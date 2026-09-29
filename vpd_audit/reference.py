"""The eleven reference conditions, their runner, and the eight acceptance checks (checks 1 to 8 below).

Every reference is measured on the evaluation set by the same divergence and cross-entropy
as the cells, with the residual excluded unless stated. The stochastic row comes in two
versions: residual excluded (the ladder's line) and residual included under one uniform
scalar per position and module, which is how the authors' metric builds it and the one the
acceptance test compares against the paper's 2.84.

Spreads: for the stochastic rows the gate uses the "draw k on
batch k" spread, eight values with one draw per batch, the unbiased estimate of the one-batch,
one-draw quantity the paper reports; the draw-averaged spread and the spread over all
(batch, draw) cells are reported beside it. Check 6 compares per batch of 64 with one
`CEandKLLosses` instance per batch, and on the mean over batches; the zero-all cross-entropy
derived from the authors' rounded row is reported, not gated.
"""

from __future__ import annotations

import math
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import torch
from torch import Tensor

from vpd_audit.constants import IMPORTANCE_CHUNK, SEQ_LEN
from vpd_audit.fingerprint import FINGERPRINT_SPEC, level3_hex, sum_hex
from vpd_audit.importances import ImportanceSums, Importances, autocast_context, compute_importances
from vpd_audit.masks import apply_source, masked_forward, residual_mask, rounded_mask, seed_from_tuple, uniform_background
from vpd_audit.metrics import per_position_kl, per_sequence_ce, summarize_kl
from vpd_audit.results import RunManifest, SubbatchStore, code_commits

# ----------------------------------------------------------------------------- conditions


@dataclass(frozen=True)
class Condition:
    name: str
    kind: str  # target | ones | uniform | rounded | importances | zero_all | random_illegal
    delta: str  # "excluded" | "included" | "none"
    per_draw: bool
    permitted: bool  # inside the permitted family (P3 asserted) or a direct mask
    threshold: float | None = None
    paper_ce: float | None = None
    # None keeps the residual rule by kind (`default_delta_background`); "r1" forces the
    # residual mask to 1 at every position of every matrix when delta == "included", whatever the kind.
    delta_background: str | None = None


CONDITIONS: tuple[Condition, ...] = (
    Condition("target", "target", "none", False, False, paper_ce=2.71),
    Condition("unmasked", "ones", "excluded", False, True, paper_ce=2.72),
    Condition("unmasked_delta", "ones", "included", False, True),
    Condition("stochastic", "uniform", "excluded", True, True),
    Condition("stochastic_delta", "uniform", "included", True, True, paper_ce=2.84),
    Condition("rounded_0", "rounded", "excluded", False, True, threshold=0.0, paper_ce=2.94),  # 1[g > 0] >= g: permitted
    Condition("rounded_0.1", "rounded", "excluded", False, False, threshold=0.1, paper_ce=2.95),
    Condition("importances", "importances", "excluded", False, True, paper_ce=2.99),
    Condition("rounded_0.5", "rounded", "excluded", False, False, threshold=0.5, paper_ce=3.02),
    Condition("zero_all", "zero_all", "excluded", False, False),
    Condition("random_illegal", "random_illegal", "excluded", False, False),
)
# the two residual test cells, kept beside CONDITIONS so the acceptance code is untouched.
# Each is an existing reference condition with one change: the residual mask fixed at 1 instead of the residual rule's
# background (`default_delta_background`). importances_delta1 is permitted (m - g = 0 on components; the residual's label is g = 0 under a mask
# of 1); stochastic_delta1 shares its component masks bitwise with stochastic and stochastic_delta for the same draw and
# sub-batch, since the uniform draw (and the discarded residual draw) are made exactly as for those two.
RESIDUAL_TEST_CONDITIONS: tuple[Condition, ...] = (
    Condition("importances_delta1", "importances", "included", False, True, delta_background="r1"),
    Condition("stochastic_delta1", "uniform", "included", True, True, delta_background="r1"),
)
ALL_CONDITIONS: tuple[Condition, ...] = CONDITIONS + RESIDUAL_TEST_CONDITIONS
CONDITION_BY_NAME: dict[str, Condition] = {c.name: c for c in ALL_CONDITIONS}
assert len(CONDITION_BY_NAME) == len(ALL_CONDITIONS), "condition names must be distinct"


def default_delta_background(kind: str) -> str:
    """The residual rule for every reference kind: the residual is subcomponent C_l + 1 with g = 0, so its
    mask is the background's value. `ones` (the unmasked row, the erases' end) -> r1; `uniform` (the stochastic row) ->
    the uniform scalar u^Delta drawn per module; every other kind (rounded, importances, zero_all, random_illegal, whose
    families' background is r = 0) -> r0, a residual mask of zeros."""
    if kind == "ones":
        return "r1"
    if kind == "uniform":
        return "uniform"
    return "r0"


def rounded_condition_name(threshold: float) -> str:
    """Numeric lookup of the rounded row for a threshold (0, 0.1, 0.5)."""
    for c in CONDITIONS:
        if c.kind == "rounded" and c.threshold is not None and math.isclose(c.threshold, float(threshold), abs_tol=1e-9):
            return c.name
    raise KeyError(f"no rounded condition at threshold {threshold}")


def cell_key(cond: Condition, draw: int) -> str:
    return f"{cond.name}/k{draw}" if cond.per_draw else cond.name


def cells_for(conditions: tuple[Condition, ...], n_draws: int) -> list[str]:
    out: list[str] = []
    for c in conditions:
        out.extend(cell_key(c, k) for k in (range(n_draws) if c.per_draw else [0]))
    return out


def build_condition_masks(
    cond: Condition,
    g: dict[str, Tensor],
    module_to_c: dict[str, int],
    *,
    draw: int,
    subbatch_index: int,
    master_seed: int,
) -> tuple[dict[str, Tensor], dict[str, Tensor] | None]:
    """The 24 masks (and the residual masks when included) of a reference condition.

    The residual rule is stated for every kind through `default_delta_background`, and
    `cond.delta_background == "r1"` overrides it with a residual mask of ones. For the uniform kind the
    `uniform_background` call is made exactly as before whatever the residual rule, so the residual draw is made and
    discarded when it is not used, and the component masks of a draw are bitwise identical across the residual settings.
    """
    keys = sorted(module_to_c)
    first = g[keys[0]]
    B, T = first.shape[0], first.shape[1]
    dtype, device = first.dtype, first.device
    assert cond.delta in ("excluded", "included"), cond.delta
    assert cond.delta_background in (None, "r1"), cond.delta_background
    background = cond.delta_background or default_delta_background(cond.kind)
    masks: dict[str, Tensor] = {}
    u_delta: dict[str, Tensor] | None = None
    if cond.kind == "ones":
        for k in keys:
            masks[k] = torch.ones_like(g[k])  # the authors' unmasked row: ones_like(ci)
    elif cond.kind == "uniform":
        u, u_delta = uniform_background((master_seed, "u", draw, subbatch_index), module_to_c, B, T, dtype=dtype, device=device)
        for k in keys:
            masks[k] = apply_source(g[k], u[k])
    elif cond.kind == "rounded":
        assert cond.threshold is not None
        for k in keys:
            masks[k] = rounded_mask(g[k], cond.threshold)
    elif cond.kind == "importances":
        for k in keys:
            masks[k] = g[k]
    elif cond.kind == "zero_all":
        for k in keys:
            masks[k] = torch.zeros_like(g[k])
    elif cond.kind == "random_illegal":
        gen = torch.Generator(device=device.type)
        gen.manual_seed(seed_from_tuple((master_seed, "illegal", subbatch_index)))
        for k in keys:
            masks[k] = torch.rand(g[k].shape, generator=gen, dtype=dtype, device=device)
    else:
        raise ValueError(cond.kind)
    if cond.delta == "excluded":
        return masks, None
    deltas: dict[str, Tensor] = {}
    for k in keys:
        if background == "uniform":
            assert u_delta is not None, "the uniform residual rule needs the uniform kind's residual draw"
            deltas[k] = residual_mask("uniform", B, T, u_delta=u_delta[k], dtype=dtype, device=device)
        else:
            deltas[k] = residual_mask(background, B, T, u_delta=None, dtype=dtype, device=device)
    return masks, deltas


# ----------------------------------------------------------------------------- the runner


@dataclass
class CellResult:
    kl: Tensor  # (B, T) float32
    ce: Tensor  # (B,) float32
    fp: dict[str, Any] | None  # {"F": hex, "H": {module: hex}, "Hd": {module: hex} | None, "phi": [hex per sequence]}; None for the target
    min_gap: float
    n_below_label: int
    n_ne_g: dict[str, int]  # per module, this sub-batch
    n_ne_one: dict[str, int]
    logits: Tensor | None = None


def evaluate_condition(
    model: Any,
    cond: Condition,
    batch: Tensor,
    imp: Importances,
    *,
    draw: int,
    subbatch_index: int,
    master_seed: int,
    weight_deltas: dict[str, Tensor],
    seq_index: Any = None,
    keep_logits: bool = False,
) -> CellResult:
    """One reference condition on one sub-batch: masks, forward, divergence, cross-entropy, and the level-3
    digests with the global sequence indices `seq_index` (default 0..B-1, for checks on one batch)."""
    B = batch.shape[0]
    if seq_index is None:
        seq_index = np.arange(B)
    assert len(seq_index) == B
    if cond.kind == "target":
        kl = torch.zeros(batch.shape, dtype=torch.float32, device=imp.target_logits.device)
        ce = per_sequence_ce(imp.target_logits, batch)
        return CellResult(kl=kl, ce=ce, fp=None, min_gap=0.0, n_below_label=0, n_ne_g={}, n_ne_one={}, logits=imp.target_logits if keep_logits else None)
    masks, deltas = build_condition_masks(cond, imp.g, model.module_to_c, draw=draw, subbatch_index=subbatch_index, master_seed=master_seed)
    fr = masked_forward(model, batch, masks, imp.g, permitted=cond.permitted, precision=imp.precision,
                        delta_masks=deltas, weight_deltas=weight_deltas if deltas is not None else None)
    kl = per_position_kl(imp.target_logits, fr.logits)
    ce = per_sequence_ce(fr.logits, batch)
    fp_hex = level3_hex(fr.fp, np.asarray(seq_index))
    return CellResult(kl=kl, ce=ce, fp=fp_hex, min_gap=fr.min_gap, n_below_label=fr.n_below_label, n_ne_g=fr.n_ne_g, n_ne_one=fr.n_ne_one,
                      logits=fr.logits if keep_logits else None)


def record_cell_digests(extra: dict[str, Any], cell: str, i: int, res: CellResult) -> None:
    """The per-(cell, sub-batch) fingerprint records into the marker's extra: F_i, H_i (and Hd_i), and the two counts."""
    assert res.fp is not None
    extra.setdefault("mask_fp_subbatch", {}).setdefault(cell, {})[str(i)] = res.fp["F"]
    extra.setdefault("mask_fp_modules_subbatch", {}).setdefault(cell, {})[str(i)] = {"H": res.fp["H"], "Hd": res.fp["Hd"]}
    extra.setdefault("n_ne_g", {}).setdefault(cell, {})[str(i)] = res.n_ne_g
    extra.setdefault("n_ne_one", {}).setdefault(cell, {})[str(i)] = res.n_ne_one


def summarize_cell_digests(extra: dict[str, Any]) -> None:
    """Level 4 of the fingerprint: per cell, F = sum_i F_i and H^(l) = sum_i H^(l)_i modulo 2^64, and the counts summed over
    sub-batches; recomputed from the per-sub-batch records at every checkpoint, so a resumed run gives the same values."""
    extra["mask_fp_cell"] = {cell: sum_hex(list(per_i.values())) for cell, per_i in extra.get("mask_fp_subbatch", {}).items()}
    modules: dict[str, Any] = {}
    for cell, per_i in extra.get("mask_fp_modules_subbatch", {}).items():
        recs = list(per_i.values())
        keys = list(recs[0]["H"])
        modules[cell] = {"H": {k: sum_hex([r["H"][k] for r in recs]) for k in keys},
                         "Hd": {k: sum_hex([r["Hd"][k] for r in recs]) for k in keys} if recs[0]["Hd"] is not None else None}
    extra["mask_fp_modules_cell"] = modules
    for name in ("n_ne_g", "n_ne_one"):
        extra[f"{name}_cell"] = {cell: {k: int(sum(int(r[k]) for r in per_i.values())) for k in next(iter(per_i.values()))} for cell, per_i in extra.get(name, {}).items()}
        extra[f"{name}_cell_total"] = {cell: int(sum(v.values())) for cell, v in extra[f"{name}_cell"].items()}


def run_references(
    model: Any,
    ids: np.ndarray,
    *,
    job: str,
    run: str,
    out_dir: Path,
    precision: str,
    subbatch: int,
    n_draws: int,
    master_seed: int,
    set_name: str,
    set_hash: str,
    checkpoint_hashes: dict[str, str],
    conditions: tuple[Condition, ...] = CONDITIONS,
    resume: bool = True,
    importance_chunk: int = IMPORTANCE_CHUNK,
    on_subbatch: Any = None,
    subbatch_hook: Any = None,
    max_subbatches: int | None = None,
    log: Any = print,
) -> SubbatchStore:
    """The reference conditions on `ids` (N, 512), sub-batch outer, conditions inner; resumable.

    On resume the existing run manifest must match the current run (checkpoint hashes, set
    hash, precision, master seed, draws, sub-batch, chunk); it is never overwritten.

    `subbatch_hook(i, imp)`, when given, runs after the importances of sub-batch i and before its cells;
    whatever dict it returns is recorded in the marker under `extra["subbatch_hooks"][str(i)]` (for
    the shared-mask guard). `max_subbatches` stops this call after that many sub-batches have been
    completed (the shrink-rule probe); a later call with `resume=True` continues.

    The fingerprint is always on: every row carries `mask_fp` (phi_b), and the marker's extra
    carries per cell and sub-batch `mask_fp_subbatch` (F_i), `mask_fp_modules_subbatch` (H_i, Hd_i), the two
    counts `n_ne_g` and `n_ne_one` per module, and their per-cell sums `mask_fp_cell`, `mask_fp_modules_cell`,
    `n_ne_g_cell`, `n_ne_one_cell`, recomputed at every checkpoint from the per-sub-batch records.
    """
    assert ids.ndim == 2 and ids.shape[1] == SEQ_LEN, ids.shape
    device = next(model.parameters()).device
    cells = cells_for(conditions, n_draws)
    store = SubbatchStore(out_dir, n_sequences=ids.shape[0], cells=cells, subbatch=subbatch)
    done = store.resume() if resume else -1
    manifest_path = out_dir / "run_manifest.json"
    manifest: RunManifest | None = RunManifest.load(manifest_path) if (resume and manifest_path.is_file()) else None
    if done >= 0:
        assert manifest is not None, f"checkpointed sub-batches without a run manifest at {manifest_path}"
        log(f"[{job}] resuming after sub-batch {done} of {store.n_subbatches}")
    if manifest is not None:
        expected = {"checkpoint_hashes": checkpoint_hashes, "set_hash": set_hash, "set_name": set_name, "precision": precision,
                    "master_seed": master_seed, "n_draws": n_draws, "subbatch": subbatch, "importance_chunk": importance_chunk,
                    "n_sequences": int(ids.shape[0]), "run": run}
        for key, value in expected.items():
            got = getattr(manifest, key)
            assert got == value, f"[{job}] resume: manifest {key}={got!r} differs from the current run's {value!r}"
    weight_deltas = model.calc_weight_deltas()  # once per model
    sums = ImportanceSums.from_json(store.extra["importance_sums"]) if "importance_sums" in store.extra else ImportanceSums.empty(model)
    t_job = time.time()
    n_completed_this_call = 0
    for i in range(done + 1, store.n_subbatches):
        if max_subbatches is not None and n_completed_this_call >= max_subbatches:
            log(f"[{job}] stopping after {n_completed_this_call} sub-batch(es) this call (max_subbatches={max_subbatches}); done through {store.done_through}")
            break
        t0 = time.time()
        sl = store.subbatch_slice(i)
        batch = torch.from_numpy(np.ascontiguousarray(ids[sl])).long().to(device)  # int64, the authors' loader's dtype
        imp = compute_importances(model, batch, precision=precision, chunk=importance_chunk)
        sums.update(imp.g)
        if subbatch_hook is not None:
            hook_out = subbatch_hook(i, imp)
            store.extra.setdefault("subbatch_hooks", {})[str(i)] = hook_out
        if manifest is None:
            manifest = RunManifest(
                job=job, run=run, checkpoint_hashes=checkpoint_hashes, set_name=set_name, set_hash=set_hash,
                n_sequences=int(ids.shape[0]), precision=precision, g_dtype=str(next(iter(imp.g.values())).dtype),
                subbatch=subbatch, importance_chunk=importance_chunk, master_seed=master_seed, n_draws=n_draws,
                device=str(device), gpu_name=torch.cuda.get_device_name(device) if device.type == "cuda" else None,
                torch_version=torch.__version__, commits=code_commits(),
                extra={"conditions": [c.name for c in conditions], "cells": cells,
                       "deterministic_algorithms": torch.are_deterministic_algorithms_enabled()},
                fingerprint=dict(FINGERPRINT_SPEC),  # replaces do_hash; a manifest without it is read as SHA-256
            )
            manifest.save(manifest_path)
        ce_target = per_sequence_ce(imp.target_logits, batch)
        seq_index = np.arange(sl.start, sl.stop)
        for cond in conditions:
            for draw in range(n_draws) if cond.per_draw else [0]:
                cell = cell_key(cond, draw)
                res = evaluate_condition(model, cond, batch, imp, draw=draw, subbatch_index=i, master_seed=master_seed,
                                         weight_deltas=weight_deltas, seq_index=seq_index)
                kl_mean, kl_max, kl_arg = summarize_kl(res.kl)
                phi = res.fp["phi"] if res.fp is not None else [""] * len(seq_index)
                rows = [
                    {"cell": cell, "condition": cond.name, "draw": draw, "seq": int(seq_index[b]),
                     "kl_mean": float(kl_mean[b]), "kl_max": float(kl_max[b]), "kl_argmax": int(kl_arg[b]),
                     "ce": float(res.ce[b]), "ce_target": float(ce_target[b]), "mask_fp": phi[b],
                     "delta": cond.delta, "precision": precision, "min_gap": res.min_gap, "n_below_label": res.n_below_label}
                    for b in range(len(seq_index))
                ]
                store.add_rows(rows)
                store.set_positions(cell, sl, res.kl.cpu().numpy())
                if res.fp is not None:
                    record_cell_digests(store.extra, cell, i, res)
                del res
        store.extra["importance_sums"] = sums.to_json()
        summarize_cell_digests(store.extra)
        store.checkpoint(i)
        n_completed_this_call += 1
        del imp
        if device.type == "cuda":
            torch.cuda.empty_cache()
        if on_subbatch is not None:
            on_subbatch(i)
        log(f"[{job}] sub-batch {i + 1}/{store.n_subbatches} ({sl.start}..{sl.stop - 1}) in {time.time() - t0:.1f} s")
    if manifest is not None and store.done_through == store.n_subbatches - 1:
        manifest.mark_finished(manifest_path)
    log(f"[{job}] done: {len(store.rows)} rows, {time.time() - t_job:.1f} s")
    return store


# ----------------------------------------------------------------------------- summaries


PAPER_CE_DIFF: dict[str, float] = {"unmasked": 0.01, "stochastic_delta": 0.13, "rounded_0": 0.23, "rounded_0.1": 0.24, "importances": 0.28, "rounded_0.5": 0.31}
PAPER_CE_ORDER: tuple[str, ...] = ("unmasked", "stochastic_delta", "rounded_0", "rounded_0.1", "importances", "rounded_0.5")
PAPER_TARGET_CE = 2.71
PAPER_ZERO_ALL_KL = 67.2449
PAPER_L0: dict[str, float] = {"layer_0": 44.6, "layer_1": 18.9, "layer_2": 49.5, "layer_3": 92.0, "total": 205.0}
PAPER_ALIVE: dict[str, int] = {"layer_0": 3709, "layer_1": 848, "layer_2": 1943, "layer_3": 3472, "total": 9972}
BATCH = 128  # the paper's evaluation batch; E is eight of them
SQRT_9_8 = math.sqrt(9 / 8)


def _rows(df: pd.DataFrame, condition: str, column: str) -> pd.DataFrame:
    """Rows of one condition with columns seq, draw, value (value = ce - ce_target for 'diff')."""
    sub = df[df["condition"] == condition]
    assert len(sub) > 0, f"no rows for condition {condition!r}"
    value = (sub["ce"] - sub["ce_target"]) if column == "diff" else sub[column]
    return pd.DataFrame({"seq": sub["seq"].to_numpy(), "draw": sub["draw"].to_numpy(), "value": value.to_numpy(dtype=np.float64)})


def per_sequence_values(df: pd.DataFrame, condition: str, column: str) -> pd.Series:
    """One value per sequence: the column averaged over draws where there are several."""
    r = _rows(df, condition, column)
    return r.groupby("seq")["value"].mean().sort_index()


def _std(values: list[float]) -> float:
    return float(np.std(values, ddof=1)) if len(values) > 1 else float("nan")


def spread_single(df: pd.DataFrame, condition: str, column: str, batch_size: int = BATCH) -> dict[str, Any]:
    """Overall mean and the spread s over batch means of a single-draw row."""
    v = per_sequence_values(df, condition, column)
    batches = v.groupby(v.index // batch_size).mean()
    return {"mean": float(v.mean()), "s": _std(list(batches)), "batch_means": [float(x) for x in batches], "n_batches": int(len(batches))}


def spread_stochastic(df: pd.DataFrame, condition: str, column: str, batch_size: int = BATCH) -> dict[str, dict[str, Any]]:
    """The three spreads of a per-draw row: 'diag' (draw k on batch k, the gate), 'draw_avg'
    (per-sequence mean over draws, then batch means), and 'cells' (every (batch, draw) mean)."""
    r = _rows(df, condition, column)
    r["batch"] = r["seq"] // batch_size
    draws = sorted(r["draw"].unique())
    batches = sorted(r["batch"].unique())
    cells = r.groupby(["batch", "draw"])["value"].mean()
    diag_draws = [int(draws[j % len(draws)]) for j in range(len(batches))]
    diag = [float(cells.loc[(b, d)]) for b, d in zip(batches, diag_draws)]
    per_seq = r.groupby("seq")["value"].mean()
    davg = [float(x) for x in per_seq.groupby(per_seq.index // batch_size).mean()]
    cell_values = [float(x) for x in cells]
    return {
        "diag": {"mean": float(np.mean(diag)), "s": _std(diag), "batch_means": diag, "draws": diag_draws, "n_batches": len(batches)},
        "draw_avg": {"mean": float(np.mean(davg)), "s": _std(davg), "batch_means": davg, "n_batches": len(batches)},
        "cells": {"mean": float(np.mean(cell_values)), "s": _std(cell_values), "n_cells": len(cell_values)},
    }


def condition_table(df: pd.DataFrame, batch_size: int = BATCH) -> pd.DataFrame:
    """Mean cross-entropy, paired difference, and mean divergence per condition with batch spreads."""
    rows = []
    for name in [c.name for c in ALL_CONDITIONS if c.name in set(df["condition"])]:
        ce, d, kl = spread_single(df, name, "ce", batch_size), spread_single(df, name, "diff", batch_size), spread_single(df, name, "kl_mean", batch_size)
        rows.append({"condition": name, "ce_mean": ce["mean"], "ce_s": ce["s"], "ce_diff_mean": d["mean"], "ce_diff_s": d["s"],
                     "kl_mean": kl["mean"], "kl_s": kl["s"], "kl_max_mean": float(per_sequence_values(df, name, "kl_max").mean()),
                     "n_seq": int(len(per_sequence_values(df, name, "ce"))), "paper_ce": CONDITION_BY_NAME[name].paper_ce})
    return pd.DataFrame(rows)


def vs_paper_table(df: pd.DataFrame, batch_size: int = BATCH) -> pd.DataFrame:
    """Ours minus the paper, per row: absolute cross-entropy and the paired difference from the target."""
    rows = []
    for c in CONDITIONS:
        if c.paper_ce is None or c.name not in set(df["condition"]):
            continue
        ce = spread_single(df, c.name, "ce", batch_size)
        entry = {"condition": c.name, "ce_ours": round(ce["mean"], 4), "ce_paper": c.paper_ce, "ce_ours_minus_paper": round(ce["mean"] - c.paper_ce, 4), "ce_s": round(ce["s"], 4)}
        if c.name in PAPER_CE_DIFF:
            if c.per_draw:
                sp = spread_stochastic(df, c.name, "diff", batch_size)
                d_mean, d_s = sp["diag"]["mean"], sp["diag"]["s"]
            else:
                sd = spread_single(df, c.name, "diff", batch_size)
                d_mean, d_s = sd["mean"], sd["s"]
            entry.update({"diff_ours": round(d_mean, 4), "diff_paper": PAPER_CE_DIFF[c.name], "diff_ours_minus_paper": round(d_mean - PAPER_CE_DIFF[c.name], 4), "diff_s_d": round(d_s, 4)})
        rows.append(entry)
    return pd.DataFrame(rows)


# ----------------------------------------------------------------------------- the eight checks


def _check(check: int, item: str, value: Any, target: Any, tolerance: Any, passed: bool | None, note: str = "") -> dict[str, Any]:
    return {"check": check, "item": item, "value": value, "target": target, "tolerance": tolerance, "pass": passed, "note": note}


def check_ordering(df: pd.DataFrame) -> list[dict[str, Any]]:
    """Check 1: ordering in mean cross-entropy and the coarse ordering in divergence (both stochastic versions gated)."""
    out = []
    ce = {n: float(per_sequence_values(df, n, "ce").mean()) for n in PAPER_CE_ORDER}
    ok = all(ce[a] < ce[b] for a, b in zip(PAPER_CE_ORDER[:-1], PAPER_CE_ORDER[1:]))
    out.append(_check(1, "ce ordering " + " < ".join(PAPER_CE_ORDER), {n: round(v, 4) for n, v in ce.items()}, "strict", "", ok))
    kl = {n: float(per_sequence_values(df, n, "kl_mean").mean()) for n in ("unmasked", "stochastic", "stochastic_delta", "rounded_0", "rounded_0.1", "rounded_0.5", "importances", "zero_all")}
    upper = ("rounded_0", "rounded_0.1", "rounded_0.5", "importances")
    for stoch in ("stochastic", "stochastic_delta"):
        coarse = kl["unmasked"] < kl[stoch] and all(kl[stoch] < kl[r] for r in upper) and all(kl[r] < kl["zero_all"] for r in upper)
        out.append(_check(1, f"kl coarse ordering with {stoch}: unmasked < {stoch} < rounded rows and importances < zero_all",
                          {n: round(v, 4) for n, v in kl.items()}, "coarse", "", coarse))
    out.append(_check(1, "kl fine ordering (reported, not gated)", " < ".join(sorted(kl, key=kl.get)), "", "", None))
    return out


def check_paired_differences(df: pd.DataFrame, label: str, batch_size: int = BATCH) -> list[dict[str, Any]]:
    """Check 2: paired differences from the target within max(0.03, 2 s_d sqrt(9/8)) of the paper's.

    Stochastic rows gate on the draw-k-on-batch-k spread; the other two spreads are reported.
    """
    out = []
    for name in PAPER_CE_ORDER:
        if CONDITION_BY_NAME[name].per_draw:
            sp = spread_stochastic(df, name, "diff", batch_size)
            mean, s = sp["diag"]["mean"], sp["diag"]["s"]
            note = (f"gate: draw k on batch k, draws {sp['diag']['draws']}, batch means {[round(x, 4) for x in sp['diag']['batch_means']]}, s_d={s:.4f}; "
                    f"draw-averaged: mean {sp['draw_avg']['mean']:.4f}, s_d {sp['draw_avg']['s']:.4f}; "
                    f"all {sp['cells']['n_cells']} (batch, draw) cells: mean {sp['cells']['mean']:.4f}, s {sp['cells']['s']:.4f}")
            spreads = [s, sp["draw_avg"]["s"], sp["cells"]["s"]]
            if all(not math.isnan(x) for x in spreads) and max(spreads) - min(spreads) > 0.005:
                note += "; the three spreads differ by more than 0.005"
        else:
            sd = spread_single(df, name, "diff", batch_size)
            mean, s = sd["mean"], sd["s"]
            note = f"s_d={s:.4f}; batch means {[round(x, 4) for x in sd['batch_means']]}"
        tol = max(0.03, 2 * s * SQRT_9_8) if not math.isnan(s) else 0.03
        err = abs(mean - PAPER_CE_DIFF[name])
        if tol > 0.06:
            note += "; tolerance above 0.06: the paper's table is too coarse to test at 0.03 here"
        out.append(_check(2, f"{label}: {name} ce - target", round(mean, 4), PAPER_CE_DIFF[name], round(tol, 4), err <= tol, note))
    return out


def check_absolute_target(df: pd.DataFrame, batch_size: int = BATCH) -> list[dict[str, Any]]:
    st = spread_single(df, "target", "ce", batch_size)
    tol = 2 * st["s"] * SQRT_9_8 + 0.005 if not math.isnan(st["s"]) else 0.005
    return [_check(3, "target ce", round(st["mean"], 4), PAPER_TARGET_CE, round(tol, 4), abs(st["mean"] - PAPER_TARGET_CE) <= tol,
                   f"s={st['s']:.4f}; batch means {[round(x, 4) for x in st['batch_means']]}")]


def check_importance_anchors(sums: ImportanceSums) -> list[dict[str, Any]]:
    out = []
    l0 = sums.per_layer_mean_count()
    for key, target in PAPER_L0.items():
        v = l0[key]
        out.append(_check(4, f"mean count g > 0 per position, {key}", round(v, 2), target, "10%", abs(v - target) <= 0.10 * target))
    alive = sums.alive_counts()
    for key, target in PAPER_ALIVE.items():
        v = alive[key]
        gated = key != "total"
        out.append(_check(4, f"alive count (mean g > 1e-6 over the set), {key}", v, target, "15%" if gated else "reported", abs(v - target) <= 0.15 * target if gated else None))
    order_ok = alive["layer_1"] < alive["layer_2"] < alive["layer_3"] < alive["layer_0"]
    out.append(_check(4, "alive ordering layer 1 < 2 < 3 < 0", {k: alive[k] for k in ("layer_1", "layer_2", "layer_3", "layer_0")}, "", "", order_ok))
    return out


def check_zero_all(df: pd.DataFrame, batch_size: int = BATCH) -> list[dict[str, Any]]:
    st = spread_single(df, "zero_all", "kl_mean", batch_size)
    tol = 2 * st["s"] * SQRT_9_8 if not math.isnan(st["s"]) else float("nan")
    ok = abs(st["mean"] - PAPER_ZERO_ALL_KL) <= tol if not math.isnan(tol) else None
    return [_check(5, "zero-all divergence", round(st["mean"], 4), PAPER_ZERO_ALL_KL, round(tol, 4) if not math.isnan(tol) else "n/a (one batch)", ok,
                   f"s={st['s']:.4f}; batch means {[round(x, 4) for x in st['batch_means']]}")]


def authors_metric(model: Any, batches: list[np.ndarray], thresholds: tuple[float, ...], *, precision: str = "fp32") -> dict[str, list[dict[str, float]]]:
    """The authors' `CEandKLLosses`, one instance per batch, at each rounding threshold (their code path).

    Driven exactly as their `evaluate` drives it: `model(batch, cache_type="input")`, then
    `calc_causal_importances(..., sampling="continuous", detach_inputs=False)`, then `update`.
    Returns {threshold: [compute() of batch 0, compute() of batch 1, ...]}.
    """
    from param_decomp.metrics.ce_and_kl_losses import CEandKLLosses

    device = next(model.parameters()).device
    weight_deltas = model.calc_weight_deltas()
    out: dict[str, list[dict[str, float]]] = {}
    for thr in thresholds:
        out[str(thr)] = []
        for b in batches:
            metric = CEandKLLosses(model=model, device=str(device), sampling="continuous", rounding_threshold=thr)
            batch = torch.from_numpy(np.ascontiguousarray(b)).long().to(device)  # their cross_entropy needs int64 labels
            with torch.no_grad(), autocast_context(device, precision):
                target_output = model(batch, cache_type="input")
                ci = model.calc_causal_importances(pre_weight_acts=target_output.cache, detach_inputs=False, sampling="continuous")
                metric.update(batch=batch, target_out=target_output.output, ci=ci, weight_deltas=weight_deltas)
            del target_output, ci
            out[str(thr)].append({k: float(v) for k, v in metric.compute().items()})
            if device.type == "cuda":
                torch.cuda.empty_cache()
    return out


def authors_dtypes(model: Any, batch_ids: np.ndarray, *, precision: str) -> dict[str, Any]:
    """The dtypes on the authors' side, measured on one batch under the same autocast as `authors_metric`:
    `ci.lower_leaky[k].dtype`, which is what `CEandKLLosses.update` hands to `_calc_ce_and_kl_losses` as `ci`, and the
    dtypes of the component and residual masks that `calc_stochastic_component_mask_info(causal_importances=ci,
    component_mask_sampling="continuous", router=AllLayersRouter(), weight_deltas=weight_deltas)` returns (the class's
    rounded and ones masks are `.float()` and `ones_like(ci)`, so their dtype follows ci's). Turns a reading of the
    authors' code into a measurement."""
    from param_decomp.routing import AllLayersRouter
    from param_decomp.utils.component_utils import calc_stochastic_component_mask_info

    device = next(model.parameters()).device
    weight_deltas = model.calc_weight_deltas()
    batch = torch.from_numpy(np.ascontiguousarray(batch_ids)).long().to(device)
    with torch.no_grad(), autocast_context(device, precision):
        target_output = model(batch, cache_type="input")
        ci = model.calc_causal_importances(pre_weight_acts=target_output.cache, detach_inputs=False, sampling="continuous")
        infos = calc_stochastic_component_mask_info(causal_importances=ci.lower_leaky, component_mask_sampling="continuous",
                                                    router=AllLayersRouter(), weight_deltas=weight_deltas)
    keys = sorted(ci.lower_leaky)
    out: dict[str, Any] = {
        "precision": precision, "batch": int(batch.shape[0]),
        "target_logits_dtype": str(target_output.output.dtype),
        "ci_lower_leaky_dtype": {k: str(ci.lower_leaky[k].dtype) for k in keys},
        "ci_upper_leaky_dtype": {k: str(ci.upper_leaky[k].dtype) for k in keys},
        "stochastic_component_mask_dtype": {k: str(infos[k].component_mask.dtype) for k in keys},
        "stochastic_residual_mask_dtype": {k: str(infos[k].weight_delta_and_mask[1].dtype) for k in keys},
        "stochastic_residual_mask_shape": {k: list(infos[k].weight_delta_and_mask[1].shape) for k in keys},
        "weight_delta_dtype": {k: str(weight_deltas[k].dtype) for k in keys},
    }
    out["distinct"] = {name: sorted(set(out[name].values())) for name in ("ci_lower_leaky_dtype", "stochastic_component_mask_dtype", "stochastic_residual_mask_dtype", "weight_delta_dtype")}
    del target_output, ci, infos, batch
    if device.type == "cuda":
        torch.cuda.empty_cache()
    return out


def check_two_code_paths(df_fp32: pd.DataFrame, theirs: dict[str, list[dict[str, float]]], check6_batch: int, tol: float = 1e-3) -> list[dict[str, Any]]:
    """Check 6: our six deterministic rows against the authors' metric on the same sequences, float32,
    per batch and on the mean over batches; the zero-all cross-entropy derived from their rounded row is
    reported, not gated. `value` and `target` are rounded to five decimals for the printout; the unrounded
    signed difference ours - theirs is carried in `diff` (the bf16 rerun of check 6 reads its epsilon from that)."""
    out = []

    def ours_for(seqs: range) -> dict[str, dict[str, float]]:
        sub = df_fp32[df_fp32["seq"].isin(list(seqs))]
        res: dict[str, dict[str, float]] = {}
        for name in ("unmasked", "importances", "rounded_0", "rounded_0.1", "rounded_0.5", "zero_all"):
            v_diff = per_sequence_values(sub, name, "diff")
            v_kl = per_sequence_values(sub, name, "kl_mean")
            assert len(v_diff) == len(seqs), (name, len(v_diff), len(seqs))
            res[name] = {"diff": float(v_diff.mean()), "kl": float(v_kl.mean())}
        return res

    for thr_str, per_batch in theirs.items():
        rname = rounded_condition_name(float(thr_str))
        n_batches = len(per_batch)
        ours_b = [ours_for(range(j * check6_batch, (j + 1) * check6_batch)) for j in range(n_batches)]
        pairs = [
            ("unmasked", "ce diff", "ce_difference_unmasked", "unmasked", "diff"),
            ("importances", "ce diff", "ce_difference_ci_masked", "importances", "diff"),
            (rname, "ce diff", "ce_difference_rounded_masked", rname, "diff"),
            ("unmasked", "kl", "kl_unmasked", "unmasked", "kl"),
            ("importances", "kl", "kl_ci_masked", "importances", "kl"),
            (rname, "kl", "kl_rounded_masked", rname, "kl"),
            ("zero_all", "kl", "kl_zero_masked", "zero_all", "kl"),
        ]
        for label, what, their_key, our_name, our_key in pairs:
            for j in range(n_batches):
                o, t = ours_b[j][our_name][our_key], per_batch[j][their_key]
                out.append({**_check(6, f"threshold {thr_str}, batch {j}: {label} {what}", round(o, 5), round(t, 5), tol, abs(o - t) <= tol, f"diff={o - t:+.3e}"), "diff": float(o - t)})
            o = float(np.mean([ours_b[j][our_name][our_key] for j in range(n_batches)]))
            t = float(np.mean([per_batch[j][their_key] for j in range(n_batches)]))
            out.append({**_check(6, f"threshold {thr_str}, mean over {n_batches} batches: {label} {what}", round(o, 5), round(t, 5), tol, abs(o - t) <= tol, f"diff={o - t:+.3e}"), "diff": float(o - t)})
        # derived zero-all cross-entropy difference: (ce_rounded - ce_target) / ce_unrecovered_rounded, per batch
        derived = []
        for j in range(n_batches):
            den = per_batch[j]["ce_unrecovered_rounded_masked"]
            assert den != 0, f"threshold {thr_str}, batch {j}: ce_unrecovered_rounded_masked is zero"
            d = per_batch[j]["ce_difference_rounded_masked"] / den
            derived.append(d)
            o = ours_b[j]["zero_all"]["diff"]
            out.append({**_check(6, f"threshold {thr_str}, batch {j}: zero_all ce diff (derived, not gated)", round(o, 5), round(d, 5), "", None, f"|diff|={abs(o - d):.2e}"), "diff": float(o - d)})
        o = float(np.mean([ours_b[j]["zero_all"]["diff"] for j in range(n_batches)]))
        d = float(np.mean(derived))
        out.append({**_check(6, f"threshold {thr_str}, mean over {n_batches} batches: zero_all ce diff (derived, not gated)", round(o, 5), round(d, 5), "", None, f"|diff|={abs(o - d):.2e}"), "diff": float(o - d)})
    return out


def check_stochastic_twice(df: pd.DataFrame, batch_size: int = BATCH) -> list[dict[str, Any]]:
    a = spread_stochastic(df, "stochastic_delta", "diff", batch_size)["diag"]["mean"]
    b = spread_stochastic(df, "stochastic", "diff", batch_size)["diag"]["mean"]
    ka = spread_stochastic(df, "stochastic_delta", "kl_mean", batch_size)["diag"]["mean"]
    kb = spread_stochastic(df, "stochastic", "kl_mean", batch_size)["diag"]["mean"]
    return [_check(7, "stochastic ce diff: residual included (authors') / excluded (ladder) / residual's share", (round(a, 4), round(b, 4), round(b - a, 4)), "", "", None),
            _check(7, "stochastic kl: residual included / excluded / residual's share", (round(ka, 4), round(kb, 4), round(kb - ka, 4)), "", "", None)]


def check_control(df_main: pd.DataFrame, df_control: pd.DataFrame) -> list[dict[str, Any]]:
    out = []
    for name in ("importances", "rounded_0", "rounded_0.1", "rounded_0.5"):
        m = float(per_sequence_values(df_main, name, "ce").mean())
        c = float(per_sequence_values(df_control, name, "ce").mean())
        out.append(_check(8, f"{name}: control ce > main ce", (round(c, 4), round(m, 4)), "control worse", "", c > m,
                          "identical to three decimals: same checkpoint loaded twice?" if round(c, 3) == round(m, 3) else ""))
    m = float(per_sequence_values(df_main, "unmasked", "ce").mean())
    c = float(per_sequence_values(df_control, "unmasked", "ce").mean())
    out.append(_check(8, "unmasked: control ce vs main ce (similar; reported)", (round(c, 4), round(m, 4)), "similar", "", None,
                      "identical to three decimals: same checkpoint loaded twice?" if round(c, 3) == round(m, 3) else ""))
    return out


def acceptance_summary(
    df_primary: pd.DataFrame,
    sums: ImportanceSums,
    primary_label: str,
    *,
    df_fp32: pd.DataFrame | None = None,
    fp32_label: str = "fp32",
    theirs: dict[str, list[dict[str, float]]] | None = None,
    check6_batch: int = 64,
    df_control: pd.DataFrame | None = None,
    batch_size: int = BATCH,
) -> pd.DataFrame:
    checks: list[dict[str, Any]] = []
    checks += check_ordering(df_primary)
    checks += check_paired_differences(df_primary, primary_label, batch_size)
    if df_fp32 is not None and fp32_label != primary_label:
        checks += check_paired_differences(df_fp32, fp32_label, batch_size)
    checks += check_absolute_target(df_primary, batch_size)
    checks += check_importance_anchors(sums)
    checks += check_zero_all(df_primary, batch_size)
    if df_fp32 is not None and theirs is not None:
        checks += check_two_code_paths(df_fp32, theirs, check6_batch)
    checks += check_stochastic_twice(df_primary, batch_size)
    if df_control is not None:
        checks += check_control(df_primary, df_control)
    return pd.DataFrame(checks)


def format_checks(df: pd.DataFrame) -> str:
    lines = []
    for _, r in df.iterrows():
        status = "PASS" if r["pass"] is True else ("FAIL" if r["pass"] is False else "----")
        lines.append(f"[{status}] check {r['check']}: {r['item']}: value={r['value']} target={r['target']} tol={r['tolerance']} {r['note']}".rstrip())
    return "\n".join(lines)
