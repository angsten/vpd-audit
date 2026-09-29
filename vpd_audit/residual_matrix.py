"""The follow-up of the two residual test cells' "near zero" row (`short_runs.py`), with the cells and the readings
fixed before the run (section "Readings" below).

One launch, float32, the first 128 sequences of E, sub-batch 32, chunk 32, deterministic algorithms on, the
fingerprint on, the model loaded once, into results/short_runs/residual_matrix_fp32/. Every cell is deterministic:
component masks of one of six kinds, and a residual mask pattern (a value, 1 or 0.5, on a set of modules, 0
elsewhere), always through the residual-included forward path (`make_mask_infos` with a weight delta and mask for
every module), so that a pattern of zeros is the residual-excluded model computed through the included path.

Sets. A (50): component masks all ones; residual all, none, and for every matrix l "all_but/l" (cost ||delta_l||^2
to second order) and "only/l" (||delta - delta_l||^2); from them D = sum_l ||delta_l||^2 and
<delta, delta_l> = (||delta||^2 + ||delta_l||^2 - ||delta - delta_l||^2) / 2. B (10): footprints under the all-ones,
importances-as-masks, stochastic draw 0 (seed tuple (0, "u", 0, i) as in the reference job), rounded-0.1, and
zero-all component masks, residual all on against all off. C (24 + the shared partner): component masks
importances-as-masks, residual "only/l" against all off, for every l. D (8): for each layer L, component masks
importances on layer L's six modules and ones elsewhere, residual all on against all off. E (1): component masks
all ones, every residual mask at 0.5 (the quadratic model at the target predicts 1/4 ||delta||^2).

A *footprint* is the per-position divergence between two masked models that share their component masks and
differ in their residual masks, KL(P = residual on || Q = residual off), computed with `per_position_kl(on_logits,
off_logits)` from the partner's logits kept within the sub-batch (3.3 GB at sub-batch 32 in float32). The direction
is fixed as written. Every cell, footprint partners included, also records its divergence against the target.
Footprint rows carry condition "footprint", no cross-entropy, no fingerprint (a footprint is not a mask).

Readings, applied mechanically by `residual_matrix_summary` and labelled (a label is not an interpretation):
1. the footprint under the importances mask as a fraction of the all-ones footprint (which must reproduce
   ||delta||^2 to 1e-4): >= 0.5 additive premise holds (then H1 is tested by D > 3 ||delta||^2); <= 0.1 gating;
   between: partial gating;
2. D / ||delta||^2, expected between 0.7 and 1.5; near 3 rescues H1 only if reading 1 came out >= 0.5;
3. set C's ratios footprint_l(imp) / ||delta_l||^2 by module type and layer, modules with ||delta_l||^2 < 1e-4
   excluded and listed: H2 (downstream gating) if near 1 only for layer 3's down_proj (perhaps o_proj) and small
   elsewhere; H3 (upstream gating) if near 1 for layer 0's q, k, v, c_fc and small for layer 3's down_proj; else
   mixed. "Near 1" and "small" are not numbers in the readings as written; this module uses >= 0.5 and <= 0.2 and says so;
4. the zero-all footprint (the H4 control) must exceed 1e-2; if near zero, stop and read the residual path again.
"""

from __future__ import annotations

import json
import math
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import torch
from torch import Tensor

from vpd_audit.constants import IMPORTANCE_CHUNK, SEQ_LEN
from vpd_audit.fingerprint import FINGERPRINT_SPEC, level3_hex
from vpd_audit.importances import Importances, compute_importances, layer_of, module_keys
from vpd_audit.masks import masked_forward, rounded_mask
from vpd_audit.metrics import per_position_kl, per_sequence_ce, summarize_kl
from vpd_audit.reference import CONDITION_BY_NAME, build_condition_masks, record_cell_digests, summarize_cell_digests
from vpd_audit.results import RunManifest, SubbatchStore, code_commits, load_table

FOOTPRINT_CONDITION = "footprint"
COMPONENT_KINDS: tuple[str, ...] = ("ones", "importances", "stochastic/k0", "rounded_0.1", "zero_all")  # plus "hybrid/L<n>"
NOT_PERMITTED_KINDS = ("rounded_0.1", "zero_all")  # direct masks that may lie below g (as in the reference conditions)
SANITY_TOL = 1e-4
READING_1_ADDITIVE = 0.5
READING_1_GATING = 0.1
READING_2_EXPECTED = (0.7, 1.5)
READING_3_NEAR_ONE = 0.5  # this module's number for reading 3's "near 1"
READING_3_SMALL = 0.2  # and for "small"
READING_3_MIN_DELTA_L_SQ = 1e-4
READING_4_FLOOR = 1e-2
LOOPHOLE_FACTOR = 3.0
POST_HOC_REL_SE = 0.10  # the post-hoc precision table: both terms with relative SE at or below this


@dataclass(frozen=True)
class Cell:
    name: str
    components: str  # one of COMPONENT_KINDS or "hybrid/L<n>"
    residual_on: frozenset[str]  # modules whose residual mask is `residual_value`; every other module's is 0
    residual_value: float = 1.0
    permitted: bool = True


@dataclass(frozen=True)
class Footprint:
    name: str
    on: str  # the cell whose logits are P
    off: str  # the cell whose logits are Q


def module_type(key: str) -> str:
    return key.split(".")[-1]


def default_cells(keys: list[str]) -> tuple[list[Cell], list[Footprint]]:
    """The five sets, in the order they run (cells sharing component masks are adjacent; a footprint's `off`
    partner precedes its `on` cells)."""
    keys = sorted(keys)
    layers = sorted({layer_of(k) for k in keys})
    every = frozenset(keys)
    cells: list[Cell] = []
    fps: list[Footprint] = []
    # A: all ones, the residual patterns
    cells += [Cell("A/all", "ones", every), Cell("A/none", "ones", frozenset())]
    cells += [Cell(f"A/all_but/{k}", "ones", frozenset(kk for kk in keys if kk != k)) for k in keys]
    cells += [Cell(f"A/only/{k}", "ones", frozenset([k])) for k in keys]
    # E: all ones, every residual at 0.5 (shares the ones component masks)
    cells.append(Cell("E/half", "ones", every, residual_value=0.5))
    # B: footprints under five component masks
    for kind in COMPONENT_KINDS:
        p = kind not in NOT_PERMITTED_KINDS
        cells += [Cell(f"B/{kind}/off", kind, frozenset(), permitted=p), Cell(f"B/{kind}/on", kind, every, permitted=p)]
        fps.append(Footprint(f"B/{kind}/footprint", on=f"B/{kind}/on", off=f"B/{kind}/off"))
        if kind == "importances":
            # C: per-module footprints under the importances mask, against the shared partner
            cells.append(Cell("C/off", "importances", frozenset()))
            for k in keys:
                cells.append(Cell(f"C/only/{k}/on", "importances", frozenset([k])))
                fps.append(Footprint(f"C/only/{k}/footprint", on=f"C/only/{k}/on", off="C/off"))
    # D: the hybrids, per layer
    for L in layers:
        kind = f"hybrid/L{L}"
        cells += [Cell(f"D/L{L}/off", kind, frozenset()), Cell(f"D/L{L}/on", kind, every)]
        fps.append(Footprint(f"D/L{L}/footprint", on=f"D/L{L}/on", off=f"D/L{L}/off"))
    names = [c.name for c in cells] + [f.name for f in fps]
    assert len(set(names)) == len(names)
    return cells, fps


def component_masks(kind: str, g: dict[str, Tensor], module_to_c: dict[str, int], *, subbatch_index: int, master_seed: int) -> dict[str, Tensor]:
    keys = sorted(g)
    if kind == "ones":
        return {k: torch.ones_like(g[k]) for k in keys}
    if kind == "importances":
        return {k: g[k] for k in keys}
    if kind == "stochastic/k0":
        masks, _ = build_condition_masks(CONDITION_BY_NAME["stochastic"], g, module_to_c, draw=0, subbatch_index=subbatch_index, master_seed=master_seed)
        return masks
    if kind == "rounded_0.1":
        return {k: rounded_mask(g[k], 0.1) for k in keys}
    if kind == "zero_all":
        return {k: torch.zeros_like(g[k]) for k in keys}
    if kind.startswith("hybrid/L"):
        L = int(kind[len("hybrid/L") :])
        assert any(layer_of(k) == L for k in keys), kind
        return {k: (g[k] if layer_of(k) == L else torch.ones_like(g[k])) for k in keys}
    raise ValueError(kind)


def residual_masks(g: dict[str, Tensor], on: frozenset[str], value: float = 1.0) -> dict[str, Tensor]:
    """(B, T) residual masks: `value` on `on`, 0 elsewhere, in g's dtype and device; every module present."""
    keys = sorted(g)
    assert on <= set(keys), sorted(on - set(keys))
    first = g[keys[0]]
    B, T = first.shape[0], first.shape[1]
    return {k: torch.full((B, T), value if k in on else 0.0, dtype=first.dtype, device=first.device) for k in keys}


def run_residual_matrix(
    model: Any,
    ids: np.ndarray,
    *,
    job: str,
    run: str,
    out_dir: Path,
    precision: str,
    subbatch: int,
    set_name: str,
    set_hash: str,
    checkpoint_hashes: dict[str, str],
    cells: list[Cell] | None = None,
    footprints: list[Footprint] | None = None,
    master_seed: int = 0,
    importance_chunk: int = IMPORTANCE_CHUNK,
    log: Any = print,
) -> SubbatchStore:
    """The cells and footprints on `ids` (N, 512), sub-batch outer, cells inner; the same store, rows, marker digests,
    and manifest as `run_references`. Component masks are rebuilt when the kind changes; a footprint partner's logits
    are kept until every footprint that needs them is computed."""
    assert ids.ndim == 2 and ids.shape[1] == SEQ_LEN, ids.shape
    torch.use_deterministic_algorithms(True, warn_only=True)
    device = next(model.parameters()).device
    keys = module_keys(model)
    if cells is None or footprints is None:
        cells, footprints = default_cells(keys)
    by_name = {c.name: c for c in cells}
    for f in footprints:
        assert f.on in by_name and f.off in by_name and by_name[f.on].components == by_name[f.off].components, f
    partner_uses: dict[str, int] = {}
    for f in footprints:
        partner_uses[f.on] = partner_uses.get(f.on, 0) + 1
        partner_uses[f.off] = partner_uses.get(f.off, 0) + 1
    all_cells = [c.name for c in cells] + [f.name for f in footprints]
    assert not out_dir.exists(), f"{out_dir} exists: this job starts fresh; move the earlier attempt aside first"
    store = SubbatchStore(out_dir, n_sequences=ids.shape[0], cells=all_cells, subbatch=subbatch)
    weight_deltas = model.calc_weight_deltas()
    # ||Delta_l||_F / ||W_l||_F per module: how much of each weight matrix the components leave to the residual
    rel_norm = {k: float((weight_deltas[k].detach().norm() / model.target_weight(k).detach().norm()).item()) for k in keys}
    manifest: RunManifest | None = None
    t_job = time.time()
    for i in range(store.n_subbatches):
        t0 = time.time()
        sl = store.subbatch_slice(i)
        batch = torch.from_numpy(np.ascontiguousarray(ids[sl])).long().to(device)
        imp: Importances = compute_importances(model, batch, precision=precision, chunk=importance_chunk)
        if manifest is None:
            manifest = RunManifest(
                job=job, run=run, checkpoint_hashes=checkpoint_hashes, set_name=set_name, set_hash=set_hash,
                n_sequences=int(ids.shape[0]), precision=precision, g_dtype=str(next(iter(imp.g.values())).dtype),
                subbatch=subbatch, importance_chunk=importance_chunk, master_seed=master_seed, n_draws=1,
                device=str(device), gpu_name=torch.cuda.get_device_name(device) if device.type == "cuda" else None,
                torch_version=torch.__version__, commits=code_commits(),
                extra={"conditions": sorted({c.components for c in cells}) + [FOOTPRINT_CONDITION], "cells": all_cells,
                       "cell_specs": {c.name: {"components": c.components, "residual_on": sorted(c.residual_on), "residual_value": c.residual_value, "permitted": c.permitted} for c in cells},
                       "footprints": {f.name: {"on": f.on, "off": f.off, "direction": "KL(P = on || Q = off) per position"} for f in footprints},
                       "residual_path": "included for every cell (make_mask_infos with a weight delta and mask for every module)",
                       "weight_delta_relative_norm": rel_norm,
                       "deterministic_algorithms": torch.are_deterministic_algorithms_enabled()},
                fingerprint=dict(FINGERPRINT_SPEC),
            )
            manifest.save(out_dir / "run_manifest.json")
        ce_target = per_sequence_ce(imp.target_logits, batch)
        seq_index = np.arange(sl.start, sl.stop)
        kept: dict[str, Tensor] = {}
        uses_left = dict(partner_uses)
        pending = list(footprints)
        current_kind: str | None = None
        comp: dict[str, Tensor] | None = None
        for c in cells:
            if c.components != current_kind:
                del comp
                comp = component_masks(c.components, imp.g, model.module_to_c, subbatch_index=i, master_seed=master_seed)
                current_kind = c.components
            deltas = residual_masks(imp.g, c.residual_on, c.residual_value)
            fr = masked_forward(model, batch, comp, imp.g, permitted=c.permitted, precision=precision, delta_masks=deltas, weight_deltas=weight_deltas)
            kl = per_position_kl(imp.target_logits, fr.logits)
            ce = per_sequence_ce(fr.logits, batch)
            fp_hex = level3_hex(fr.fp, seq_index)
            _write_rows(store, c.name, c.components, "included", seq_index, kl, ce, ce_target, fp_hex["phi"], precision, fr.min_gap, fr.n_below_label, sl)

            class _Res:  # what record_cell_digests reads
                fp = fp_hex
                n_ne_g = fr.n_ne_g
                n_ne_one = fr.n_ne_one

            record_cell_digests(store.extra, c.name, i, _Res())  # type: ignore[arg-type]
            if uses_left.get(c.name, 0) > 0:
                kept[c.name] = fr.logits
            del fr, kl, ce, deltas
            # every footprint whose two partners are now in hand
            for f in list(pending):
                if f.on in kept and f.off in kept:
                    kl_fp = per_position_kl(kept[f.on], kept[f.off])  # KL(P = on || Q = off)
                    _write_rows(store, f.name, FOOTPRINT_CONDITION, "on_vs_off", seq_index, kl_fp, None, ce_target, [""] * len(seq_index), precision, float("nan"), 0, sl)
                    diff = (kept[f.on].float() - kept[f.off].float()).abs()  # was the residual added at all? (H4: a residual scaled by the component level would give 0)
                    store.extra.setdefault("footprint_logit_diffs", {}).setdefault(f.name, {})[str(i)] = {"max": float(diff.max()), "mean": float(diff.mean())}
                    del diff
                    pending.remove(f)
                    for partner in (f.on, f.off):
                        uses_left[partner] -= 1
                        if uses_left[partner] == 0:
                            del kept[partner]
                    del kl_fp
        assert not pending and not kept, (pending, list(kept))
        summarize_cell_digests(store.extra)
        store.checkpoint(i)
        del imp, comp
        if device.type == "cuda":
            torch.cuda.empty_cache()
        log(f"[{job}] sub-batch {i + 1}/{store.n_subbatches} ({sl.start}..{sl.stop - 1}), {len(cells)} cells + {len(footprints)} footprints, in {time.time() - t0:.1f} s")
    if manifest is not None:
        manifest.mark_finished(out_dir / "run_manifest.json")
    log(f"[{job}] done: {len(store.rows)} rows, {time.time() - t_job:.1f} s")
    return store


def _write_rows(store: SubbatchStore, cell: str, condition: str, delta: str, seq_index: np.ndarray, kl: Tensor, ce: Tensor | None, ce_target: Tensor,
                phi: list[str], precision: str, min_gap: float, n_below: int, sl: slice) -> None:
    kl_mean, kl_max, kl_arg = summarize_kl(kl)
    rows = [
        {"cell": cell, "condition": condition, "draw": 0, "seq": int(seq_index[b]),
         "kl_mean": float(kl_mean[b]), "kl_max": float(kl_max[b]), "kl_argmax": int(kl_arg[b]),
         "ce": float(ce[b]) if ce is not None else float("nan"), "ce_target": float(ce_target[b]), "mask_fp": phi[b],
         "delta": delta, "precision": precision, "min_gap": min_gap, "n_below_label": n_below}
        for b in range(len(seq_index))
    ]
    store.add_rows(rows)
    store.set_positions(cell, sl, kl.cpu().numpy())


# ----------------------------------------------------------------------------- the summary


def _mean_se(v: np.ndarray) -> tuple[float, float]:
    return float(v.mean()), (float(v.std(ddof=1) / math.sqrt(v.size)) if v.size > 1 else float("nan"))


def label_reading_1(fraction: float) -> str:
    if fraction >= READING_1_ADDITIVE:
        return "additive premise holds (>= 0.5): H1 tested by reading 2"
    if fraction <= READING_1_GATING:
        return "gating (<= 0.1): the additive model and the cancellation reading retired; H2 against H3 by set C"
    return "partial gating (between 0.1 and 0.5): report both, no reading fixed in advance"


def label_reading_2(ratio: float, reading_1_fraction: float) -> str:
    inside = READING_2_EXPECTED[0] <= ratio <= READING_2_EXPECTED[1]
    loophole = ratio > LOOPHOLE_FACTOR
    s = f"D / ||delta||^2 = {ratio:.3f}: {'inside' if inside else 'outside'} the expected [0.7, 1.5]; loophole D > 3 ||delta||^2: {loophole}"
    if loophole:
        s += "; rescues H1 only because reading 1 came out >= 0.5" if reading_1_fraction >= READING_1_ADDITIVE else "; does NOT rescue H1 (reading 1 below 0.5)"
    return s


def label_reading_3(ratios: dict[str, float], excluded: list[str], keys: list[str]) -> str:
    layers = sorted({layer_of(k) for k in keys})
    first, last = layers[0], layers[-1]

    def r(k: str) -> float | None:
        return ratios.get(k)

    last_down = [k for k in keys if layer_of(k) == last and module_type(k) == "down_proj"]
    first_inputs = [k for k in keys if layer_of(k) == first and module_type(k) in ("q_proj", "k_proj", "v_proj", "c_fc")]
    others = [k for k in ratios if k not in last_down]
    ld = [r(k) for k in last_down if r(k) is not None]
    fi = [r(k) for k in first_inputs if r(k) is not None]
    h2 = bool(ld) and all(v >= READING_3_NEAR_ONE for v in ld) and all(ratios[k] <= READING_3_SMALL for k in others)
    h3 = bool(fi) and all(v >= READING_3_NEAR_ONE for v in fi) and all(v <= READING_3_SMALL for v in ld)
    if h2 and not h3:
        lab = f"H2, downstream gating: layer {last} down_proj ratio(s) {[round(v, 3) for v in ld]} >= {READING_3_NEAR_ONE}, every other ratio <= {READING_3_SMALL}"
    elif h3 and not h2:
        lab = f"H3, upstream gating: layer {first} q, k, v, c_fc ratios {[round(v, 3) for v in fi]} >= {READING_3_NEAR_ONE}, layer {last} down_proj {[round(v, 3) for v in ld]} <= {READING_3_SMALL}"
    else:
        lab = f"mixed / report the table: layer {last} down_proj {[round(v, 3) for v in ld]}, layer {first} q, k, v, c_fc {[round(v, 3) for v in fi]}"
    return lab + f" (near 1 := >= {READING_3_NEAR_ONE}, small := <= {READING_3_SMALL}, this module's numbers; {len(excluded)} module(s) excluded for ||delta_l||^2 < {READING_3_MIN_DELTA_L_SQ:.0e})"


def residual_matrix_summary(out_dir: Path, short_runs_summary: Path | None = None) -> tuple[dict[str, Any], str]:
    out_dir = Path(out_dir)
    df = load_table(out_dir)
    with open(out_dir / "run_manifest.json") as f:
        manifest = json.load(f)
    with open(out_dir / "marker.json") as f:
        marker = json.load(f)
    specs = manifest["extra"]["cell_specs"]
    keys = sorted({k for s in specs.values() for k in s["residual_on"]})
    wide = df.pivot(index="seq", columns="cell", values="kl_mean").sort_index().astype(np.float64)
    assert not wide.isna().any().any()
    n = int(len(wide))

    def ms(cell: str) -> dict[str, float]:
        m, se = _mean_se(wide[cell].to_numpy())
        return {"mean": m, "se": se}

    rel_norm: dict[str, float] = manifest["extra"].get("weight_delta_relative_norm", {})
    ld_raw: dict[str, dict[str, dict[str, float]]] = marker.get("extra", {}).get("footprint_logit_diffs", {})
    logit_diffs = {name: {"max": max(v["max"] for v in per_i.values()), "mean": float(np.mean([v["mean"] for v in per_i.values()]))} for name, per_i in ld_raw.items()}
    S: dict[str, Any] = {"n_sequences": n, "precision": manifest["precision"], "subbatch": manifest["subbatch"], "importance_chunk": manifest["importance_chunk"],
                         "gpu_name": manifest.get("gpu_name"), "n_cells": len(specs), "n_footprints": len(manifest["extra"]["footprints"]),
                         "kl_vs_target_means": {c: ms(c) for c in wide.columns}, "footprint_logit_diffs": logit_diffs, "weight_delta_relative_norm": rel_norm}
    # ---- set A
    delta_sq = ms("A/none")
    all_on = ms("A/all")
    per_module: dict[str, dict[str, float]] = {}
    D = 0.0
    cross_sum = 0.0
    for k in keys:
        but, only = ms(f"A/all_but/{k}"), ms(f"A/only/{k}")
        cross = 0.5 * (delta_sq["mean"] + but["mean"] - only["mean"])
        per_module[k] = {"layer": layer_of(k), "type": module_type(k), "delta_l_sq": but["mean"], "delta_l_sq_se": but["se"], "delta_minus_delta_l_sq": only["mean"],
                         "delta_minus_delta_l_sq_se": only["se"], "cross_delta_delta_l": cross, "share_of_delta_sq": cross / delta_sq["mean"],
                         "weight_delta_relative_norm": rel_norm.get(k)}
        D += but["mean"]
        cross_sum += cross
    D_b = sum(wide[f"A/all_but/{k}"].to_numpy() for k in keys)
    ratio_b = D_b / wide["A/none"].to_numpy()
    q_pred = 0.5 * delta_sq["mean"] - D / 6.0
    S["set_A"] = {"delta_sq": delta_sq, "all_residuals_on": {**all_on, "expected": "about 0 (M6d)"},
                  "D": {"sum_of_means": D, "ratio_to_delta_sq": D / delta_sq["mean"], "ratio_per_sequence_mean": float(ratio_b.mean()),
                        "ratio_per_sequence_min_max": [float(ratio_b.min()), float(ratio_b.max())], "se_of_sequence_sum": _mean_se(D_b)[1]},
                  "loophole_D_over_3_delta_sq": bool(D > LOOPHOLE_FACTOR * delta_sq["mean"]),
                  "cross_terms": {"sum_over_l": cross_sum, "consistency_relative": (cross_sum - delta_sq["mean"]) / delta_sq["mean"],
                                  "note": "sum_l <delta, delta_l> = ||delta||^2 if delta = sum_l delta_l and the divergence is locally a squared norm"},
                  "off_diagonal_gram_sum": delta_sq["mean"] - D, "Q_predicted_from_D": {"value": q_pred, "ratio_to_delta_sq": q_pred / delta_sq["mean"], "formula": "||delta||^2 / 2 - D / 6"},
                  "per_module": per_module,
                  "by_type": {t: sum(v["delta_l_sq"] for v in per_module.values() if v["type"] == t) for t in sorted({v["type"] for v in per_module.values()})},
                  "by_layer": {str(L): sum(v["delta_l_sq"] for v in per_module.values() if v["layer"] == L) for L in sorted({v["layer"] for v in per_module.values()})}}
    if short_runs_summary is not None and Path(short_runs_summary).is_file():
        with open(short_runs_summary) as f:
            sr = json.load(f)
        p = sr["passes"].get("residual_fp32")
        if p:
            q_meas = p["run_iii"]["kl_mean"]["Q"]["mean"]
            S["set_A"]["Q_measured_fp32"] = {"value": q_meas, "ratio_to_delta_sq": p["run_iii"]["Q_over_delta_sq"], "delta_sq_of_that_pass": p["delta_sq"]["value"], "predicted_minus_measured": q_pred - q_meas}
    # ---- set B: footprints, the sanity check, reading 1 and 4
    fp = {kind: ms(f"B/{kind}/footprint") for kind in COMPONENT_KINDS}
    ones_fp = fp["ones"]["mean"]
    sanity_diff = abs(ones_fp - delta_sq["mean"])
    frac = {kind: fp[kind]["mean"] / ones_fp for kind in COMPONENT_KINDS}
    S["set_B"] = {"footprints": fp, "fraction_of_all_ones_footprint": frac,
                  "sanity": {"all_ones_footprint": ones_fp, "delta_sq_from_A_none": delta_sq["mean"], "abs_diff": sanity_diff, "tolerance": SANITY_TOL, "passed": bool(sanity_diff <= SANITY_TOL)},
                  "partners_vs_target": {kind: {"on": ms(f"B/{kind}/on"), "off": ms(f"B/{kind}/off")} for kind in COMPONENT_KINDS},
                  "reading_1": {"fraction_importances": frac["importances"], "label": label_reading_1(frac["importances"]), "expected": "0.01 to 0.05 (about 3e-4 nats), and the same order under the stochastic and rounded masks",
                                "fraction_stochastic": frac["stochastic/k0"], "fraction_rounded_0.1": frac["rounded_0.1"]},
                  "reading_4": {"zero_all_footprint": fp["zero_all"]["mean"], "floor": READING_4_FLOOR, "passed": bool(fp["zero_all"]["mean"] > READING_4_FLOOR),
                                "label": "H4 control passes: the residual is added to the output under the zero-all mask" if fp["zero_all"]["mean"] > READING_4_FLOOR else "STOP: the zero-all footprint is near zero; read the residual path in the code again before anything else",
                                "zero_all_logit_diff": logit_diffs.get("B/zero_all/footprint"),
                                "evidence": ("the residual IS added under zero-all: the on and off logits differ (max |d| above); a residual scaled by the component mask level would give exactly 0"
                                             if logit_diffs.get("B/zero_all/footprint", {}).get("max", 0.0) > 0 else "no logit difference recorded")}}
    S["set_A"]["reading_2"] = {"ratio": D / delta_sq["mean"], "label": label_reading_2(D / delta_sq["mean"], frac["importances"])}
    # ---- set C: per-module footprints under the importances mask, ratios to ||delta_l||^2
    c_fp = {k: ms(f"C/only/{k}/footprint") for k in keys}
    excluded = [k for k in keys if per_module[k]["delta_l_sq"] < READING_3_MIN_DELTA_L_SQ]
    ratios = {k: c_fp[k]["mean"] / per_module[k]["delta_l_sq"] for k in keys if k not in excluded}
    table = {k: {"layer": layer_of(k), "type": module_type(k), "footprint_imp": c_fp[k]["mean"], "footprint_imp_se": c_fp[k]["se"], "delta_l_sq": per_module[k]["delta_l_sq"],
                 "ratio": ratios.get(k), "excluded": k in excluded, "on_vs_target": ms(f"C/only/{k}/on")["mean"]} for k in keys}
    types = sorted({module_type(k) for k in keys})
    layers = sorted({layer_of(k) for k in keys})
    grid = {t: {str(L): next((round(ratios[k], 4) for k in ratios if module_type(k) == t and layer_of(k) == L), None) for L in layers} for t in types}
    # post hoc, precision-based: every module whose two terms both have a relative standard
    # error at or below 10 percent, with the standard errors shown; beside the pre-registered table, not in place of it
    post: dict[str, dict[str, Any]] = {}
    for k in keys:
        f_m, f_se = c_fp[k]["mean"], c_fp[k]["se"]
        d_m, d_se = per_module[k]["delta_l_sq"], per_module[k]["delta_l_sq_se"]
        rel_f = f_se / f_m if f_m > 0 else float("inf")
        rel_d = d_se / d_m if d_m > 0 else float("inf")
        inc = rel_f <= POST_HOC_REL_SE and rel_d <= POST_HOC_REL_SE
        post[k] = {"layer": layer_of(k), "type": module_type(k), "footprint_imp": f_m, "footprint_imp_se": f_se, "footprint_rel_se": rel_f,
                   "delta_l_sq": d_m, "delta_l_sq_se": d_se, "delta_l_sq_rel_se": rel_d, "included": inc, "ratio": (f_m / d_m) if inc else None,
                   "excluded_by_the_preregistered_rule": k in excluded}
    S["set_C"] = {"off_vs_target": ms("C/off"), "per_module": table, "ratio_grid_type_by_layer": grid, "excluded_delta_l_sq_below_1e-4": excluded,
                  "sum_of_footprints": float(sum(v["mean"] for v in c_fp.values())), "footprint_importances_from_B": fp["importances"]["mean"],
                  "reading_3": {"label": label_reading_3(ratios, excluded, keys)},
                  "post_hoc_precision_table": {"label": "post hoc, precision-based; the pre-registered rule excluded modules below 1e-4",
                                               "criterion": f"both terms with relative standard error <= {POST_HOC_REL_SE:.0%}", "rows": post,
                                               "n_included": int(sum(v["included"] for v in post.values()))}}
    # ---- set D: hybrids per layer
    d_layers = sorted({int(nm.split("/")[1][1:]) for nm in specs if nm.startswith("D/L")})
    S["set_D"] = {str(L): {"footprint": ms(f"D/L{L}/footprint"), "fraction_of_all_ones_footprint": ms(f"D/L{L}/footprint")["mean"] / ones_fp,
                           "on_vs_target": ms(f"D/L{L}/on"), "off_vs_target": ms(f"D/L{L}/off")} for L in d_layers}
    S["set_D"]["note"] = "component masks importances on layer L's modules and ones elsewhere; the footprint is the residual's effect when only layer L is masked"
    # ---- set E
    half = ms("E/half")
    S["set_E"] = {"kl_vs_target": half, "prediction_quarter_delta_sq": 0.25 * delta_sq["mean"], "ratio_to_prediction": half["mean"] / (0.25 * delta_sq["mean"]),
                  "note": "every residual mask at 0.5 with all components on; the quadratic model at the target predicts (1 - 0.5)^2 ||delta||^2"}
    # ---- digests: the cell list names the same masks twice by construction (B/ones/off is A/none, B/ones/on is A/all,
    # C/off is B/importances/off), so digests must be equal within a mask spec and distinct across specs
    mfc = marker["extra"]["mask_fp_cell"]
    groups: dict[tuple[Any, ...], list[str]] = {}
    for c in mfc:
        sp = specs[c]
        groups.setdefault((sp["components"], tuple(sp["residual_on"]), sp["residual_value"]), []).append(c)
    within = {tuple(cs): len({mfc[c] for c in cs}) == 1 for cs in groups.values() if len(cs) > 1}
    across = len({mfc[cs[0]] for cs in groups.values()}) == len(groups)
    S["digests"] = {"n_cells_with_digest": len(mfc), "n_distinct_mask_specs": len(groups), "equal_within_each_spec": all(within.values()),
                    "duplicate_specs": {" = ".join(cs): ok for cs, ok in within.items()}, "distinct_across_specs": across,
                    "A_component_digests_all_equal": len({json.dumps(marker["extra"]["mask_fp_modules_cell"][c]["H"], sort_keys=True) for c in mfc if c.startswith("A/")}) == 1}
    S["labels"] = {"reading_1": S["set_B"]["reading_1"]["label"], "reading_2": S["set_A"]["reading_2"]["label"], "reading_3": S["set_C"]["reading_3"]["label"], "reading_4": S["set_B"]["reading_4"]["label"],
                   "sanity_all_ones_footprint": "pass" if S["set_B"]["sanity"]["passed"] else "FAIL"}
    return S, format_residual_matrix_summary(S)


def _f(x: float | None, nd: int = 6) -> str:
    return "n/a" if x is None or (isinstance(x, float) and not math.isfinite(x)) else f"{x:.{nd}f}"


def format_residual_matrix_summary(S: dict[str, Any]) -> str:
    A, B, C, D, E = S["set_A"], S["set_B"], S["set_C"], S["set_D"], S["set_E"]
    L: list[str] = [f"# The residual follow-up (the residual test cells' near-zero row; the pre-registered readings): {S['precision']}, {S['n_sequences']} sequences, sub-batch {S['subbatch']}, chunk {S['importance_chunk']}, {S['gpu_name']}; {S['n_cells']} cells and {S['n_footprints']} footprints", ""]
    L.append("Labels are the pre-registered readings applied mechanically; a label is not an interpretation.")
    L.append("")
    L.append("## Labels")
    for k, v in S["labels"].items():
        L.append(f"- {k}: **{v}**")
    L.append("")
    L.append("## Set A: the per-matrix residual costs with every component on")
    L.append(f"||delta||^2 (A/none) = {_f(A['delta_sq']['mean'])} +- SE {_f(A['delta_sq']['se'])}; all residuals on (A/all) = {A['all_residuals_on']['mean']:.2e} (expected about 0)")
    L.append(f"D = sum_l ||delta_l||^2 = {_f(A['D']['sum_of_means'])}; D / ||delta||^2 = {A['D']['ratio_to_delta_sq']:.3f} (per sequence: mean {A['D']['ratio_per_sequence_mean']:.3f}, range {A['D']['ratio_per_sequence_min_max'][0]:.3f} to {A['D']['ratio_per_sequence_min_max'][1]:.3f}); "
             f"loophole D > 3 ||delta||^2: {A['loophole_D_over_3_delta_sq']}")
    L.append(f"sum_l <delta, delta_l> against ||delta||^2: relative deviation {A['cross_terms']['consistency_relative']:+.4f}; off-diagonal Gram sum ||delta||^2 - D = {A['off_diagonal_gram_sum']:+.6f}")
    q = A["Q_predicted_from_D"]
    line = f"Q predicted from D = {_f(q['value'])} = {q['ratio_to_delta_sq']:.3f} ||delta||^2"
    if "Q_measured_fp32" in A:
        m = A["Q_measured_fp32"]
        line += f"; measured Q-bar (residual_fp32) {_f(m['value'])} = {m['ratio_to_delta_sq']:.4f} of that pass's ||delta||^2 {_f(m['delta_sq_of_that_pass'])}; predicted - measured {m['predicted_minus_measured']:+.6f}"
    L.append(line)
    L.append(f"||delta_l||^2 by type: { {t: round(v, 6) for t, v in A['by_type'].items()} }; by layer: { {k: round(v, 6) for k, v in A['by_layer'].items()} }")
    L.append("")
    L.append("| module | layer | type | ||delta_l||^2 | ||delta - delta_l||^2 | <delta, delta_l> | share | ||Delta_l||_F / ||W_l||_F |")
    L.append("|---|---|---|---|---|---|---|---|")
    for k, v in A["per_module"].items():
        rn = v.get("weight_delta_relative_norm")
        L.append(f"| {k} | {v['layer']} | {v['type']} | {_f(v['delta_l_sq'])} +- {_f(v['delta_l_sq_se'])} | {_f(v['delta_minus_delta_l_sq'])} | {v['cross_delta_delta_l']:+.6f} | {v['share_of_delta_sq']:+.3f} | {_f(rn, 4) if rn is not None else 'n/a'} |")
    L.append("")
    L.append("## Set B: the residual's footprint under five component masks (KL(on || off), per position, mean over sequences)")
    s = B["sanity"]
    L.append(f"Sanity: all-ones footprint {_f(s['all_ones_footprint'])} against ||delta||^2 {_f(s['delta_sq_from_A_none'])}: |diff| {s['abs_diff']:.2e} (tolerance {s['tolerance']:.0e}) -> {'pass' if s['passed'] else 'FAIL'}")
    L.append("")
    L.append("| component masks | footprint | +- SE | fraction of the all-ones footprint | on vs target | off vs target | max / mean |logits_on - logits_off| |")
    L.append("|---|---|---|---|---|---|---|")
    for kind in COMPONENT_KINDS:
        p = B["partners_vs_target"][kind]
        ld = S["footprint_logit_diffs"].get(f"B/{kind}/footprint")
        lds = f"{ld['max']:.2e} / {ld['mean']:.2e}" if ld else "n/a"
        L.append(f"| {kind} | {_f(B['footprints'][kind]['mean'])} | {_f(B['footprints'][kind]['se'])} | {B['fraction_of_all_ones_footprint'][kind]:.4f} | {_f(p['on']['mean'])} | {_f(p['off']['mean'])} | {lds} |")
    L.append("")
    L.append(f"Reading 1 (importances footprint / all-ones footprint = {B['reading_1']['fraction_importances']:.4f}; stochastic {B['reading_1']['fraction_stochastic']:.4f}, rounded-0.1 {B['reading_1']['fraction_rounded_0.1']:.4f}; expected {B['reading_1']['expected']}): **{B['reading_1']['label']}**")
    L.append(f"Reading 2: **{A['reading_2']['label']}**")
    L.append(f"Reading 4 (zero-all footprint {B['reading_4']['zero_all_footprint']:.3e} against the {B['reading_4']['floor']:.0e} floor): **{B['reading_4']['label']}**; "
             f"logit difference under zero-all: {B['reading_4']['zero_all_logit_diff']}; {B['reading_4']['evidence']}")
    L.append("")
    L.append("## Set C: per-module footprints under the importances mask, against ||delta_l||^2 from set A")
    L.append(f"C/off (importances, residual off) vs target = {_f(C['off_vs_target']['mean'])}; sum of the 24 per-module footprints {_f(C['sum_of_footprints'])} against the all-on importances footprint of set B {_f(C['footprint_importances_from_B'])}")
    L.append(f"Excluded (||delta_l||^2 < 1e-4): {C['excluded_delta_l_sq_below_1e-4'] or 'none'}")
    L.append("")
    L.append("| module | layer | type | footprint_l(imp) | +- SE | ||delta_l||^2 | ratio | only-l-on vs target |")
    L.append("|---|---|---|---|---|---|---|---|")
    for k, v in C["per_module"].items():
        ratio = "excluded" if v["excluded"] else f"{v['ratio']:.3f}"
        L.append(f"| {k} | {v['layer']} | {v['type']} | {_f(v['footprint_imp'])} | {_f(v['footprint_imp_se'])} | {_f(v['delta_l_sq'])} | {ratio} | {_f(v['on_vs_target'])} |")
    L.append("")
    L.append("Ratio grid, type by layer (None = excluded):")
    layers = sorted({str(v["layer"]) for v in C["per_module"].values()}, key=int)
    L.append("| type | " + " | ".join(f"layer {l}" for l in layers) + " |")
    L.append("|---|" + "---|" * len(layers))
    for t, row in C["ratio_grid_type_by_layer"].items():
        L.append(f"| {t} | " + " | ".join(str(row[l]) for l in layers) + " |")
    L.append("")
    L.append(f"Reading 3: **{C['reading_3']['label']}**")
    L.append("")
    ph = C["post_hoc_precision_table"]
    L.append(f"### {ph['label']} ({ph['criterion']}; {ph['n_included']} of {len(ph['rows'])} modules included)")
    L.append("")
    L.append("| module | layer | type | footprint_l(imp) +- SE (rel) | ||delta_l||^2 +- SE (rel) | ratio | pre-registered rule |")
    L.append("|---|---|---|---|---|---|---|")
    for k, v in ph["rows"].items():
        ratio = f"{v['ratio']:.4f}" if v["included"] else "not included"
        L.append(f"| {k} | {v['layer']} | {v['type']} | {v['footprint_imp']:.2e} +- {v['footprint_imp_se']:.1e} ({v['footprint_rel_se']:.0%}) | "
                 f"{v['delta_l_sq']:.2e} +- {v['delta_l_sq_se']:.1e} ({v['delta_l_sq_rel_se']:.0%}) | {ratio} | {'excluded' if v['excluded_by_the_preregistered_rule'] else 'kept'} |")
    L.append("")
    L.append("## Set D: the hybrids (importances on one layer, ones elsewhere), residual all on against all off")
    L.append("| layer | footprint | +- SE | fraction of the all-ones footprint | on vs target | off vs target |")
    L.append("|---|---|---|---|---|---|")
    for Lk, v in D.items():
        if Lk == "note":
            continue
        L.append(f"| {Lk} | {_f(v['footprint']['mean'])} | {_f(v['footprint']['se'])} | {v['fraction_of_all_ones_footprint']:.4f} | {_f(v['on_vs_target']['mean'])} | {_f(v['off_vs_target']['mean'])} |")
    L.append("")
    L.append(f"## Set E: every residual mask at 0.5 with all components on: KL vs target {_f(E['kl_vs_target']['mean'])} +- {_f(E['kl_vs_target']['se'])} against the prediction 1/4 ||delta||^2 = {_f(E['prediction_quarter_delta_sq'])}: ratio {E['ratio_to_prediction']:.3f}")
    L.append("")
    dg = S["digests"]
    L.append(f"Digests: {dg['n_cells_with_digest']} cells, {dg['n_distinct_mask_specs']} distinct mask specs; equal within each duplicated spec = {dg['equal_within_each_spec']} {dg['duplicate_specs']}; "
             f"distinct across specs = {dg['distinct_across_specs']}; set A's component digests all equal = {dg['A_component_digests_all_equal']}")
    return "\n".join(L)
