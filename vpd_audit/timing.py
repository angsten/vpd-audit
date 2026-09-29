"""Per-phase timing of one sub-batch of the reference loop.

One sub-batch of 64 of E on the main run, the 24 masked cells the acceptance runs (eight draws
of both stochastic rows), with the on-device fingerprint on (it always is) and the
acceptance run's SHA-256 off unless `do_sha256`. Phases: importances, mask building, the P3 check with
the two counts, the fingerprint (levels 1 and 2, on the device), its level-3 pull, the forward,
the divergence, the cross-entropy, the per-sequence summary. Each phase boundary synchronizes
the device so that the wall-clock is attributed to the phase that did the work. The
fingerprint phase is the one judged: about 0.05 s per cell per sub-batch expected, 0.1 s
the pre-registered trigger. The forward's time per cell per sub-batch, times the number of
sub-batches in E, is the per-cell pass-over-E cost the grid is budgeted with.
"""

from __future__ import annotations

import time
from collections import defaultdict
from contextlib import contextmanager
from pathlib import Path
from typing import Any

import numpy as np
import torch

from vpd_audit.fingerprint import FINGERPRINT_SPEC, level3_hex
from vpd_audit.importances import compute_importances
from vpd_audit.masks import masked_forward
from vpd_audit.metrics import per_position_kl, per_sequence_ce, summarize_kl
from vpd_audit.reference import CONDITIONS, build_condition_masks, cell_key


class PhaseTimer:
    def __init__(self, device: torch.device) -> None:
        self.device = device
        self.seconds: dict[str, float] = defaultdict(float)
        self.calls: dict[str, int] = defaultdict(int)

    def _sync(self) -> None:
        if self.device.type == "cuda":
            torch.cuda.synchronize(self.device)

    @contextmanager
    def phase(self, name: str):
        self._sync()
        t0 = time.perf_counter()
        try:
            yield
        finally:
            self._sync()
            self.seconds[name] += time.perf_counter() - t0
            self.calls[name] += 1


def time_subbatch(model: Any, ids: np.ndarray, *, precision: str, do_sha256: bool = False, n_draws: int = 8, master_seed: int = 0, log: Any = print) -> dict[str, Any]:
    """The per-sub-batch body of `run_references`, phase by phase, on `ids` (B, 512)."""
    device = next(model.parameters()).device
    timer = PhaseTimer(device)
    batch = torch.from_numpy(np.ascontiguousarray(ids)).long().to(device)
    timer._sync()
    t_total = time.perf_counter()
    with timer.phase("weight_deltas"):
        weight_deltas = model.calc_weight_deltas()
    with timer.phase("importances"):
        imp = compute_importances(model, batch, precision=precision)
    with timer.phase("ce"):
        per_sequence_ce(imp.target_logits, batch)
    n_cells = 0
    digests: dict[str, str] = {}  # F per cell, so a compiled and an eager timing can be compared bitwise
    for cond in CONDITIONS:
        if cond.kind == "target":
            continue
        for draw in range(n_draws) if cond.per_draw else [0]:
            n_cells += 1
            with timer.phase("mask_build"):
                masks, deltas = build_condition_masks(cond, imp.g, model.module_to_c, draw=draw, subbatch_index=0, master_seed=master_seed)
            fr = masked_forward(model, batch, masks, imp.g, permitted=cond.permitted, precision=precision, delta_masks=deltas,
                                weight_deltas=weight_deltas if deltas is not None else None, do_sha256=do_sha256, timings=timer)
            with timer.phase("fingerprint_l3"):
                digests[cell_key(cond, draw)] = level3_hex(fr.fp, np.arange(batch.shape[0]))["F"]
            with timer.phase("divergence"):
                kl = per_position_kl(imp.target_logits, fr.logits)
            with timer.phase("ce"):
                per_sequence_ce(fr.logits, batch)
            with timer.phase("summarize"):
                summarize_kl(kl)
                kl.cpu().numpy()
            del masks, deltas, fr, kl
    timer._sync()
    total = time.perf_counter() - t_total
    out = {
        "precision": precision, "do_sha256": do_sha256, "fingerprint": dict(FINGERPRINT_SPEC), "B": int(ids.shape[0]), "n_draws": n_draws, "n_cells": n_cells,
        "gpu": torch.cuda.get_device_name(device) if device.type == "cuda" else "cpu",
        "total_s": total, "phases_s": dict(timer.seconds), "phase_calls": dict(timer.calls),
        "unaccounted_s": total - sum(timer.seconds.values()),
        "forward_s_per_cell": timer.seconds["forward"] / n_cells,
        "fingerprint_s_per_cell": (timer.seconds["fingerprint"] + timer.seconds["fingerprint_l3"]) / n_cells,
        "fingerprint_trigger_s_per_cell": 0.1,
        "cells": [cell_key(c, k) for c in CONDITIONS if c.kind != "target" for k in (range(n_draws) if c.per_draw else [0])],
        "digests": digests,
    }
    log(f"[timing] do_sha256={do_sha256}, fingerprint on: total {total:.1f} s over {n_cells} cells; " + ", ".join(f"{k} {v:.2f}" for k, v in sorted(timer.seconds.items(), key=lambda kv: -kv[1])))
    del imp
    if device.type == "cuda":
        torch.cuda.empty_cache()
    return out


# ----------------------------------------------------------------------------- the grid-slice mode


def grid_slice_cells(run: str = "main") -> list:
    """One cell of each tier-1 type on E (union r = 0, union uniform, soft erase r = 1 and uniform, hard-zero Delta
    included with its t* and the conditional-damage columns), at draw 0 and rung 4, plus the reference set with one draw
    of the stochastic rows: 16 cells."""
    from vpd_audit.cells import Cell, _references

    cells = [
        Cell(run, "union", "E", "D_unif", 0.1, "r0", "excluded", 0, "4", "none", 1),
        Cell(run, "union", "E", "D_unif", 0.1, "uniform", "excluded", 0, "4", "none", 1),
        Cell(run, "soft_erase", "E", "D_unif", 0.1, "r1", "excluded", 0, "4", "none", 1),
        Cell(run, "soft_erase", "E", "D_unif", 0.1, "uniform", "excluded", 0, "4", "none", 1),
        Cell(run, "hard_zero", "E", "D_unif", 0.1, "ones", "included", 0, "4", "none", 1),
    ]
    return cells + _references(run, "E", 1, draws=1)


def time_grid_subbatch(model: Any, ids: np.ndarray, cells: list, sources: dict, *, run: str, precision: str, out_dir: Path, set_name: str, set_hash: str,
                       checkpoint_hashes: dict[str, str], importance_chunk: int = 32, log: Any = print) -> dict[str, Any]:
    """`run_cells` on one sub-batch (all of `ids`, so B = ids.shape[0]) through `cells`, phase by phase, into a fresh
    store under `out_dir`, with the peak GPU memory of the pass. The phases are those of `time_subbatch` plus
    softmax_once (the target's softmax, once per sub-batch), columns (the switched mass, over-removal, t*, and the conditional-damage columns), and
    checkpoint. Run it once with B = 64 and once with B = 1 (the short-slab shape of the donor-side rung-4 groups)."""
    import shutil

    device = next(model.parameters()).device
    timer = PhaseTimer(device)
    if out_dir.exists():
        shutil.rmtree(out_dir)
    if device.type == "cuda":
        torch.cuda.synchronize(device)
        torch.cuda.reset_peak_memory_stats(device)
    t0 = time.perf_counter()
    from vpd_audit.cells import run_cells

    store = run_cells(model, cells, ids, sources, job="timing_grid", run=run, out_dir=out_dir, precision=precision, subbatch=int(ids.shape[0]), set_name=set_name, set_hash=set_hash,
                      checkpoint_hashes=checkpoint_hashes, importance_chunk=min(importance_chunk, int(ids.shape[0])), resume=False, timings=timer, log=log)
    timer._sync()
    total = time.perf_counter() - t0
    n_cells = len(cells)
    n_forwards = sum(1 for c in cells if not (c.family == "reference" and c.condition == "target"))
    out = {
        "precision": precision, "B": int(ids.shape[0]), "n_cells": n_cells, "n_forwards": n_forwards, "cells": [c.name for c in cells],
        "gpu": torch.cuda.get_device_name(device) if device.type == "cuda" else "cpu",
        "total_s": total, "phases_s": dict(timer.seconds), "phase_calls": dict(timer.calls), "unaccounted_s": total - sum(timer.seconds.values()),
        "forward_s_per_cell": timer.seconds["forward"] / n_forwards,
        "fingerprint_s_per_cell": (timer.seconds["fingerprint"] + timer.seconds["fingerprint_l3"]) / n_forwards,
        "per_cell_s_excluding_importances": (total - timer.seconds["importances"] - timer.seconds["softmax_once"] - timer.seconds["checkpoint"]) / n_forwards,
        "max_memory_allocated_gb": torch.cuda.max_memory_allocated(device) / 1e9 if device.type == "cuda" else None,
        "n_rows": len(store.rows),
    }
    log(f"[timing-grid] B={out['B']}: total {total:.1f} s over {n_forwards} forwards; peak {out['max_memory_allocated_gb']} GB; " + ", ".join(f"{k} {v:.2f}" for k, v in sorted(timer.seconds.items(), key=lambda kv: -kv[1])))
    if device.type == "cuda":
        torch.cuda.empty_cache()
    return out


def format_grid_split(results: list[dict[str, Any]], n_subbatches_in_E: int) -> str:
    phases = ["importances", "ce", "softmax_once", "mask_build", "p3_check", "fingerprint", "fingerprint_l3", "forward", "divergence", "columns", "summarize", "checkpoint"]
    lines = ["| phase | " + " | ".join(f"{r['gpu']}, B = {r['B']}, {r['n_forwards']} forwards (s)" for r in results) + " |", "|---|" + "---|" * len(results)]
    for ph in phases:
        lines.append(f"| {ph} | " + " | ".join(f"{r['phases_s'].get(ph, 0.0):.2f}" for r in results) + " |")
    lines.append("| unaccounted | " + " | ".join(f"{r['unaccounted_s']:.2f}" for r in results) + " |")
    lines.append("| **total** | " + " | ".join(f"**{r['total_s']:.2f}**" for r in results) + " |")
    lines.append("| peak GPU memory (GB) | " + " | ".join(f"{r['max_memory_allocated_gb']:.1f}" if r["max_memory_allocated_gb"] is not None else "n/a" for r in results) + " |")
    r = results[0]
    lines.append("")
    lines.append(f"Per cell per sub-batch of {r['B']} on {r['gpu']}, excluding the importances, the softmax and the checkpoint: {r['per_cell_s_excluding_importances']:.3f} s, "
                 f"so {r['per_cell_s_excluding_importances'] * n_subbatches_in_E:.1f} s per cell-pass over E ({n_subbatches_in_E} sub-batches); forward alone "
                 f"{r['forward_s_per_cell'] * n_subbatches_in_E:.1f} s, fingerprint {r['fingerprint_s_per_cell'] * n_subbatches_in_E:.2f} s per cell-pass.")
    return "\n".join(lines)


def format_split(results: list[dict[str, Any]], n_subbatches_in_E: int) -> str:
    """A small table of the phase split, and the per-cell pass-over-E cost of the forward alone. Each column's header
    names the card the timing ran on, so a timing on another card is not read against one on the 40 GB card."""
    phases = ["importances", "weight_deltas", "mask_build", "p3_check", "fingerprint", "fingerprint_l3", "sha256", "forward", "divergence", "ce", "summarize"]
    lines = ["| phase | " + " | ".join(f"{r.get('gpu', 'card not recorded')}: sha256={'on' if r.get('do_sha256') else 'off'}, fingerprint on (s)" for r in results) + " |", "|---|" + "---|" * len(results)]
    for ph in phases:
        lines.append(f"| {ph} | " + " | ".join(f"{r['phases_s'].get(ph, 0.0):.2f}" for r in results) + " |")
    lines.append("| unaccounted | " + " | ".join(f"{r['unaccounted_s']:.2f}" for r in results) + " |")
    lines.append("| **total** | " + " | ".join(f"**{r['total_s']:.2f}**" for r in results) + " |")
    r = results[0]
    per_pass = r["forward_s_per_cell"] * n_subbatches_in_E
    lines.append("")
    lines.append(f"Forward alone: {r['forward_s_per_cell']:.3f} s per cell per sub-batch of {r['B']} on {r['gpu']}, "
                 f"so {per_pass:.1f} s per cell-pass over E ({n_subbatches_in_E} sub-batches); {r['n_cells']} cells per sub-batch.")
    lines.append(f"Fingerprint (levels 1-2 on the device plus the level-3 pull): {r['fingerprint_s_per_cell']:.3f} s per cell per sub-batch "
                 f"against the 0.1 s trigger ({'at or below' if r['fingerprint_s_per_cell'] <= 0.1 else 'ABOVE'}); "
                 f"{r['fingerprint_s_per_cell'] * n_subbatches_in_E:.2f} s per cell-pass over E.")
    return "\n".join(lines)
