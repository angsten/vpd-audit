"""The verification launch on the paper's model.

One `run_cells` pass on E, main run, bf16, sub-batch 64, with 45 cells: the full reference set (the 25 cells the
acceptance ran), the two chains of the identities launch (union r = 0 and hard-zero Delta included from D_unif at
tau = 0.1, draw 0, rungs 1 to 8), the fourth cell of the two-by-two of the alive set and the never-named set, each at its
labels or at 1 (the soft erase's rung 8 under the ones
background, Delta excluded) with its Delta-included twin, and the never-named chain's rung 8 in both Delta settings.
The comparisons: the references bitwise on kl_mean and ce against the acceptance table; the chains bitwise on kl_mean
against the identities' per-sequence table and on mask_fp_cell against its cell table (equality printed, never a
value: the intermediate rungs of these chains are the ones nobody reads); the fourth cell and its twin as means with
sequence standard errors beside the unmasked and importances-as-masks rows, and as paired per-sequence differences
against those two rows (these are ends); the never-named rung 8 with Delta excluded against H4 on the first 128
sequences, with Delta included over all of E, and the distributions of t* at both tau_q. Then the resume test
on this launch (a second store of the same cells, interrupted after sub-batch 2 and resumed, compared bitwise with the
first), and the two-path check of the conditional damage on the store.
"""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from vpd_audit.cells import Cell, _references, build_sources, run_cells
from vpd_audit.constants import SEQ_LEN
from vpd_audit.sources import INTERMEDIATE_RUNGS, Cache, source_hash

H4_TOLERANCE = 0.01


def verify_cells(run: str = "main") -> list[Cell]:
    refs = _references(run, "E", 1, draws=8)
    chains: list[Cell] = []
    for r in INTERMEDIATE_RUNGS + ("8",):
        chains.append(Cell(run, "union", "E", "D_unif", 0.1, "r0", "excluded", 0, r, "none", 1))
        chains.append(Cell(run, "hard_zero", "E", "D_unif", 0.1, "ones", "included", 0, r, "none", 1))
    fourth = [Cell(run, "soft_erase", "E", "D_unif", 0.1, "r1", "excluded", 0, "8", "none", 1), Cell(run, "soft_erase", "E", "D_unif", 0.1, "r1", "included", 0, "8", "none", 3)]
    never = [Cell(run, "never_named_hard", "E", "D_unif", 0.1, "ones", "included", 0, "8", "none", 3), Cell(run, "never_named_hard", "E", "D_unif", 0.1, "ones", "excluded", 0, "8", "none", 3)]
    cells = refs + chains + fourth + never
    assert len(cells) == 45 and len({c.name for c in cells}) == 45
    return cells


def _mean_se(x: np.ndarray) -> dict[str, float]:
    x = np.asarray(x, dtype=np.float64)
    return {"mean": float(x.mean()), "se": float(x.std(ddof=1) / np.sqrt(x.size)), "n": int(x.size)}


def _t_star_stats(t: np.ndarray) -> dict[str, float]:
    t = np.asarray(t, dtype=np.int64)
    return {"median": float(np.median(t)), "q1": float(np.percentile(t, 25)), "q3": float(np.percentile(t, 75)), "fraction_equal_T": float((t == SEQ_LEN).mean()),
            "fraction_at_least_8": float((t >= 8).mean()), "clean_prefix_fraction": float((t / SEQ_LEN).mean()), "n": int(t.size)}


def _tables(store_dir: Path) -> tuple[pd.DataFrame, pd.DataFrame, dict[str, np.ndarray]]:
    rows = pd.read_parquet(store_dir / "per_sequence.parquet").sort_values(["cell", "seq"]).reset_index(drop=True)
    ct = pd.read_parquet(store_dir / "cells.parquet").sort_values("cell").reset_index(drop=True)
    arrays = {p.stem: np.load(p) for p in sorted((store_dir / "kl").glob("*.npy"))}
    return rows, ct, arrays


def compare_stores_bitwise(a: Path, b: Path) -> dict[str, Any]:
    """Every column of the per-sequence table (sorted by cell and sequence), the cell table, and every array, equal."""
    ra, ca, aa = _tables(a)
    rb, cb, ab = _tables(b)
    cols_bad = [c for c in ra.columns if c not in rb.columns or not (ra[c].equals(rb[c]) or (ra[c].dtype.kind == "f" and np.array_equal(ra[c].to_numpy(), rb[c].to_numpy(), equal_nan=True)))]
    cells_equal = ca.equals(cb)
    arrays_equal = set(aa) == set(ab) and all(np.array_equal(aa[k], ab[k], equal_nan=True) for k in aa)
    return {"rows": int(len(ra)), "rows_equal": len(ra) == len(rb) and not cols_bad, "columns_differing": cols_bad, "cell_table_equal": bool(cells_equal),
            "arrays_equal": bool(arrays_equal), "n_arrays": len(aa), "pass": bool(len(ra) == len(rb) and not cols_bad and cells_equal and arrays_equal)}


def compare_with_earlier_runs(store_dir: Path, acceptance_table: Path, chains_dir: Path, h4_json: Path, run: str = "main") -> dict[str, Any]:
    """The comparisons 1 to 4 on a finished verify store. Prints nothing; returns equalities, counts, and the end values."""
    rows = pd.read_parquet(store_dir / "per_sequence.parquet")
    ct = pd.read_parquet(store_dir / "cells.parquet").set_index("cell")
    out: dict[str, Any] = {}
    prefix = f"{run}/E/"
    # 1. the references against the acceptance table, bitwise on kl_mean and ce per (cell, sequence)
    acc = pd.read_parquet(acceptance_table)
    ref_cells = sorted(acc["cell"].unique())
    ours = rows[rows["cell"].isin([f"{prefix}ref/{k}" for k in ref_cells])].copy()
    ours["key"] = ours["cell"].str[len(prefix) + 4:]
    a = acc.set_index(["cell", "seq"]).sort_index()
    o = ours.set_index(["key", "seq"]).sort_index()
    common = a.index.intersection(o.index)
    kl_eq = np.array_equal(a.loc[common, "kl_mean"].to_numpy(np.float32), o.loc[common, "kl_mean"].to_numpy(np.float32))
    ce_eq = np.array_equal(a.loc[common, "ce"].to_numpy(np.float32), o.loc[common, "ce"].to_numpy(np.float32), equal_nan=True)
    out["references_vs_acceptance"] = {"n_cells": len(ref_cells), "n_pairs": int(len(common)), "n_pairs_expected": int(len(a)), "kl_mean_equal": bool(kl_eq), "ce_equal": bool(ce_eq),
                                       "pass": bool(kl_eq and ce_eq and len(common) == len(a) == len(o))}
    # 2. the two chains against the identities launch: kl_mean per (cell, sequence) and mask_fp_cell per cell; equality only
    ch_rows = pd.read_parquet(chains_dir / "per_sequence.parquet")
    ch_cells = pd.read_parquet(chains_dir / "cells.parquet").set_index("cell")
    chain_names = [c for c in ch_cells.index if "/union/" in c or "/hard_zero/" in c]
    x = ch_rows[ch_rows["cell"].isin(chain_names)].set_index(["cell", "seq"]).sort_index()
    y = rows[rows["cell"].isin(chain_names)].set_index(["cell", "seq"]).sort_index()
    common2 = x.index.intersection(y.index)
    kl2 = np.array_equal(x.loc[common2, "kl_mean"].to_numpy(np.float32), y.loc[common2, "kl_mean"].to_numpy(np.float32))
    fp_eq = all(ct.loc[c, "mask_fp_cell"] == ch_cells.loc[c, "mask_fp_cell"] for c in chain_names if c in ct.index)
    out["chains_vs_identities"] = {"n_cells": len(chain_names), "n_pairs": int(len(common2)), "n_pairs_expected": int(len(x)), "kl_mean_equal": bool(kl2), "mask_fp_cell_equal": bool(fp_eq),
                                   "pass": bool(kl2 and fp_eq and len(common2) == len(x) == len(y) and all(c in ct.index for c in chain_names))}
    # 3. the fourth cell and its twin: means with sequence standard errors beside the two reference rows, and the paired differences
    def per_seq(name: str) -> np.ndarray:
        return rows[rows["cell"] == name].sort_values("seq")["kl_mean"].to_numpy(np.float64)

    unm, imp = per_seq(f"{prefix}ref/unmasked"), per_seq(f"{prefix}ref/importances")
    item3: dict[str, Any] = {"unmasked": _mean_se(unm), "importances": _mean_se(imp)}
    for label, name in (("F_excluded", f"{prefix}soft_erase/D_unif/tau0.1/r1/excl/k0/r8"), ("F_included", f"{prefix}soft_erase/D_unif/tau0.1/r1/incl/k0/r8")):
        f = per_seq(name)
        item3[label] = {"cell": name, **_mean_se(f), "paired_F_minus_importances": _mean_se(f - imp), "paired_F_minus_unmasked": _mean_se(f - unm)}
    out["fourth_cell"] = item3
    # 4. the never-named rung 8 in both Delta settings
    with open(h4_json) as f:
        h4 = json.load(f)
    h4_value = float(h4["mean_kl"]["b_our_hard_zero_complement"])
    nn_excl = rows[rows["cell"] == f"{prefix}never_named_hard/D_unif/tau0.1/ones/excl/k0/r8"].sort_values("seq")
    nn_incl = rows[rows["cell"] == f"{prefix}never_named_hard/D_unif/tau0.1/ones/incl/k0/r8"].sort_values("seq")
    first128 = nn_excl[nn_excl["seq"] < 128]["kl_mean"].to_numpy(np.float64)
    excl_128 = float(first128.mean())
    item4: dict[str, Any] = {"excluded_mean_first_128": excl_128, "h4_float32_first_128": h4_value, "difference": excl_128 - h4_value, "within_tolerance": bool(abs(excl_128 - h4_value) <= H4_TOLERANCE),
                             "excluded_mean_all_E": _mean_se(nn_excl["kl_mean"].to_numpy(np.float64)), "included_mean_all_E": _mean_se(nn_incl["kl_mean"].to_numpy(np.float64)),
                             "n_erased": int(ct.loc[f"{prefix}never_named_hard/D_unif/tau0.1/ones/incl/k0/r8", "n_on"])}
    for tag in ("0.1", "0"):
        t_inc, t_exc = nn_incl[f"t_star_{tag}"].to_numpy(np.int64), nn_excl[f"t_star_{tag}"].to_numpy(np.int64)
        item4[f"t_star_{tag}"] = {**_t_star_stats(t_inc), "same_in_both_delta_settings": bool(np.array_equal(t_inc, t_exc))}
    out["never_named_rung_8"] = item4
    return out


def format_comparisons(c: dict[str, Any], resume: dict[str, Any] | None, two_paths: dict[str, Any] | None) -> str:
    L = ["# The verification launch on the paper's model", ""]
    r = c["references_vs_acceptance"]
    L.append(f"1. References against the acceptance table: {r['n_cells']} cells, {r['n_pairs']} of {r['n_pairs_expected']} (cell, sequence) pairs; kl_mean equal {r['kl_mean_equal']}, ce equal {r['ce_equal']} -> {'pass' if r['pass'] else 'FAIL'}")
    r = c["chains_vs_identities"]
    L.append(f"2. The two chains against the identities launch: {r['n_cells']} cells, {r['n_pairs']} of {r['n_pairs_expected']} pairs; kl_mean equal {r['kl_mean_equal']}, mask_fp_cell equal {r['mask_fp_cell_equal']} -> {'pass' if r['pass'] else 'FAIL'} (equality only; no value of these chains is printed)")
    f4 = c["fourth_cell"]
    L.append("3. The fourth cell of the two-by-two (ends), mean over E with the sequence standard error:")
    L.append("| row | mean | se |")
    L.append("|---|---|---|")
    L.append(f"| unmasked | {f4['unmasked']['mean']:.4f} | {f4['unmasked']['se']:.4f} |")
    L.append(f"| importances-as-masks | {f4['importances']['mean']:.4f} | {f4['importances']['se']:.4f} |")
    for label in ("F_excluded", "F_included"):
        x = f4[label]
        L.append(f"| {label} ({x['cell'].split('/', 2)[-1]}) | {x['mean']:.4f} | {x['se']:.4f} |")
    L.append("")
    L.append("| paired difference | mean | se |")
    L.append("|---|---|---|")
    for label in ("F_excluded", "F_included"):
        x = f4[label]
        L.append(f"| {label} - importances | {x['paired_F_minus_importances']['mean']:+.4f} | {x['paired_F_minus_importances']['se']:.4f} |")
        L.append(f"| {label} - unmasked | {x['paired_F_minus_unmasked']['mean']:+.4f} | {x['paired_F_minus_unmasked']['se']:.4f} |")
    n = c["never_named_rung_8"]
    L.append("")
    L.append(f"4. The never-named chain's rung 8 ({n['n_erased']} erased): Delta excluded over the first 128 sequences {n['excluded_mean_first_128']:.4f} against H4's {n['h4_float32_first_128']:.4f} (float32), "
             f"difference {n['difference']:+.4f}, within {H4_TOLERANCE}: {n['within_tolerance']}; Delta excluded over all of E {n['excluded_mean_all_E']['mean']:.4f} (se {n['excluded_mean_all_E']['se']:.4f}); "
             f"Delta included over all of E {n['included_mean_all_E']['mean']:.4f} (se {n['included_mean_all_E']['se']:.4f})")
    for tag in ("0.1", "0"):
        t = n[f"t_star_{tag}"]
        L.append(f"   t*_b at tau_q = {tag} on E: median {t['median']:.0f}, quartiles {t['q1']:.0f} / {t['q3']:.0f}, fraction equal to T {t['fraction_equal_T']:.3f}, fraction at least 8 {t['fraction_at_least_8']:.3f}, "
                 f"clean-prefix fraction {t['clean_prefix_fraction']:.3f} (the same in both Delta settings: {t['same_in_both_delta_settings']})")
    if resume is not None:
        L.append("")
        L.append(f"Resume test on this launch: a second store of the same cells interrupted after sub-batch 2 and resumed; {resume['rows']} rows, every column equal {resume['rows_equal']}"
                 f"{' (differing: ' + ', '.join(resume['columns_differing']) + ')' if resume['columns_differing'] else ''}, cell table equal {resume['cell_table_equal']}, "
                 f"{resume['n_arrays']} arrays equal {resume['arrays_equal']} -> {'pass' if resume['pass'] else 'FAIL'}")
    if two_paths is not None:
        L.append(f"Two-path check on this store: {two_paths['n_cells_checked']} hard-zero cells, {two_paths['n_sequence_checks']} checks with t* > 0, largest ratio {two_paths['max_ratio']:.4f} "
                 f"(non-finite {two_paths.get('n_nonfinite', 0)}) -> {'pass' if two_paths['pass'] else 'FAIL'}")
    return "\n".join(L)


def run_verify(model: Any, ids: np.ndarray, *, run: str, out_dir: Path, set_hash: str, checkpoint_hashes: dict[str, str], subbatch: int = 64, precision: str = "bf16",
               resume_test: bool = True, on_subbatch: Any = None, log: Any = print) -> dict[str, Any]:
    """The 45 cells into out_dir (uninterrupted), then the resume store beside it, then the checks that need only the store."""
    from vpd_audit import env
    from vpd_audit.donors import donors_dir
    from vpd_audit.two_paths import check_d_b_two_paths

    t0 = time.time()
    cells = verify_cells(run)
    cache = Cache.load(f"D_unif_{run}")
    alive_vec = np.load(donors_dir() / f"alive_D_unif_{run}.npy")
    module_to_c = {k: model.module_to_c[k] for k in sorted(model.module_to_c)}
    sources = build_sources(cells, {f"D_unif_{run}": cache}, {run: (alive_vec, source_hash(alive_vec))}, None, None, module_to_c, log=log)
    common = dict(run=run, precision=precision, subbatch=subbatch, set_name="E", set_hash=set_hash, checkpoint_hashes=checkpoint_hashes, importance_chunk=32, log=log)
    run_cells(model, cells, ids, sources, job=f"verify_{run}", out_dir=out_dir, resume=True, on_subbatch=on_subbatch, **common)
    result: dict[str, Any] = {"n_cells": len(cells), "seconds_main_store": time.time() - t0}
    if resume_test:
        t1 = time.time()
        resume_dir = out_dir.parent / f"{out_dir.name}_resume"

        def interrupt(i: int) -> None:
            if on_subbatch is not None:
                on_subbatch(i)
            if i == 1:
                raise RuntimeError("interrupted after sub-batch 2 (the resume test)")

        try:
            run_cells(model, cells, ids, sources, job=f"verify_{run}_resume", out_dir=resume_dir, resume=True, on_subbatch=interrupt, **common)
            interrupted = False
        except RuntimeError as e:
            interrupted = "interrupted after sub-batch 2" in str(e)
        run_cells(model, cells, ids, sources, job=f"verify_{run}_resume", out_dir=resume_dir, resume=True, on_subbatch=on_subbatch, **common)
        result["resume"] = {"interrupted_after_subbatch_2": bool(interrupted), **compare_stores_bitwise(out_dir, resume_dir), "seconds": time.time() - t1}
        log(f"[verify] resume test: interrupted {interrupted}, tables equal {result['resume']['rows_equal']}, arrays equal {result['resume']['arrays_equal']} -> {'pass' if result['resume']['pass'] and interrupted else 'FAIL'}")
    result["two_paths"] = check_d_b_two_paths(out_dir, update_summary=False, log=log)
    result["comparisons"] = compare_with_earlier_runs(out_dir, env.RESULTS_DIR / "acceptance" / "main_bf16" / "per_sequence.parquet", env.RESULTS_DIR / "identities" / "chains_main",
                                                      env.RESULTS_DIR / "identities" / "h4_main.json", run=run)
    text = format_comparisons(result["comparisons"], result.get("resume"), result["two_paths"])
    with open(out_dir / "comparisons.json", "w") as f:
        json.dump(result, f, indent=2, sort_keys=True, default=str)
    with open(out_dir / "comparisons.md", "w") as f:
        f.write(text + "\n")
    log(text)
    result["seconds"] = time.time() - t0
    return result
