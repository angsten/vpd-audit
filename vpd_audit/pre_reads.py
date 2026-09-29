"""The pre-reads: label-only numbers from the caches and the sources, before any grid
cell on the paper's model, into results/grid/pre_reads/<run>/ with a summary.md. Nothing here needs a forward pass or
reads a divergence, except item 9, which reads the two ends of the identities' union chain.

1. The cross-tabulation of dead (mean importance over D_unif at or below 1e-6, the paper's count) against never named
   above tau, tau in {0, 0.1, 0.5}.
2. The never-named set at tau = 0.1 and the strict set at tau = 0 on each of the five caches: the distribution of t*_b
   at tau_q in {0, 0.01, 0.1}; per member, the number of positions with g > 0 and the maximum g; per position, how
   many of its nonzero labels fall in the set.
3. The union-against-control overlap per rung and draw at tau = 0.1, in total and per matrix, beside n_on / |alive|.
4. E2's coverage per layer, rung, draw, and tau; the overlap between draws at rung 7.
5. The union's n_on at every rung and draw at tau = 0; the strict set's size.
6. The testability table of every hard-zero chain: per-sequence t*_b at both tau_q stored as a table (t_star.parquet,
   which the analysis asserts the loop's columns against bitwise), the clean-prefix fraction, the contributing count
   (t* >= 8), and the readability floor of the hard-zero rule (at least 64 contributing on average over draws and a
   clean-prefix fraction of at least 0.05); per stratum on E_lab.
7. The switched mass sigma_b of every cell under a non-uniform background, at every rung and draw, in float64 from
   the caches and the switched-mass formula (one matrix product from per-sequence sums of g over the named set:
   sigma_b = |rho| - (1/T) sum_{c in rho} sum_t g_{b,t,c}), stored as tables (sigma_<set>.parquet, columns the
   cells); the deciles of the union's pooled distribution over rungs 1 to 7 with 5a and 6a; the fraction of the
   control's points above the union's top edge. Uniform-background cells are omitted (their sigma depends on the
   CUDA draw of u).
8. The matched-random controls' overflow into the dead set per matrix and rung.
9. From the identities launch's per-sequence table: the standard deviation over sequences of the rung-8 excess of
   the union chain over its rung 0 (two ends), which calibrates the standard error that was guessed in advance.

The CSR arithmetic reproduces the loop's first_touched exactly: per position the maximum of g over the set (the
cache holds the loop's float32 values), compared with tau_q in float32, the first position above it or T.
"""

from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from vpd_audit import env
from vpd_audit.cells import HARD_ZERO_FAMILIES, Cell, build_sources, enumerate_cells
from vpd_audit.constants import ALIVE_THRESHOLD, SEQ_LEN
from vpd_audit.importances import layer_of
from vpd_audit.results import code_commits
from vpd_audit.sources import Cache, key_sha256, never_named_set, positive_label_counts, rung_order, source_hash, split_by_module, union_source

POOLS = ("D_unif", "D_code", "D_prose")
TAU_QS_NEVER_NAMED = (0.0, 0.01, 0.1)
TAU_QS_LOOP = (0.1, 0.0)
FLOOR_CONTRIBUTING = 64
FLOOR_CLEAN_FRACTION = 0.05
CONTRIBUTING_MIN_T_STAR = 8


@dataclass
class PreReadInputs:
    run: str
    cache_tag: str
    set_map: dict[str, str]  # {"E": "E", "E_lab": "E_lab"}
    pool_map: dict[str, str]  # {"D_unif": "D_unif", ...}
    strata_file: str  # in env.SETS_DIR
    chains_dir: Path | None  # the identities' chains store (item 9), or None
    draws: int = 8
    master_seed: int = 0
    positive_stratum: str = "Github"
    extra: dict[str, Any] = field(default_factory=dict)


def paper_inputs(run: str, draws: int = 8) -> PreReadInputs:
    chains = env.RESULTS_DIR / "identities" / "chains_main"
    return PreReadInputs(run=run, cache_tag=run, set_map={"E": "E", "E_lab": "E_lab"}, pool_map={p: p for p in POOLS}, strata_file="E_lab.strata.json",
                         chains_dir=chains if (run == "main" and (chains / "per_sequence.parquet").is_file()) else None, draws=draws)


# ----------------------------------------------------------------------------- CSR arithmetic


def _reduceat(ufunc: Any, a: np.ndarray, indptr: np.ndarray, empty_value: Any) -> np.ndarray:
    """ufunc.reduceat over the CSR segments, with empty segments given `empty_value` (reduceat would return a[start])."""
    counts = np.diff(indptr)
    out = np.full(counts.size, empty_value, dtype=a.dtype)
    nonempty = counts > 0
    if nonempty.any():
        out[nonempty] = ufunc.reduceat(a, indptr[:-1][nonempty])
    return out


def first_touched_from_cache(cache: Cache, S: np.ndarray, tau_qs: tuple[float, ...]) -> dict[float, tuple[np.ndarray, np.ndarray]]:
    """The hard-zero rule's first touched position from the CSR cache: per position the maximum of g over the set S, then per sequence and tau_q the
    first position with max > tau_q (T if none) and the number of such positions; exactly the loop's first_touched on
    the same float32 values. Returns {tau_q: (t_star (N,), n_touched (N,))}, int64."""
    assert S.dtype == np.bool_ and S.shape == (cache.n_sub,)
    sel = S[cache.indices]
    vm = np.where(sel, cache.values, np.float32(0.0))
    best = _reduceat(np.maximum, vm, cache.indptr, np.float32(0.0)).reshape(cache.n_sequences, SEQ_LEN)
    out = {}
    for tq in tau_qs:
        touched = best > np.float32(tq)
        any_ = touched.any(axis=1)
        t_star = np.where(any_, touched.argmax(axis=1), SEQ_LEN).astype(np.int64)
        out[tq] = (t_star, touched.sum(axis=1).astype(np.int64))
    return out


def labels_in_set_per_position(cache: Cache, S: np.ndarray) -> np.ndarray:
    """Per position, how many of its nonzero labels fall in S; (P,) int64."""
    sel = S[cache.indices].astype(np.int64)
    return _reduceat(np.add, sel, cache.indptr, np.int64(0))


def per_subcomponent_counts_and_max(cache: Cache) -> tuple[np.ndarray, np.ndarray]:
    """Per subcomponent over the cache: the number of positions with g > 0 and the maximum g; (n_sub,) each."""
    idx = cache.indices.astype(np.int64)
    counts = np.bincount(idx, minlength=cache.n_sub).astype(np.int64)
    mx = np.zeros(cache.n_sub, dtype=np.float32)
    np.maximum.at(mx, idx, cache.values)
    return counts, mx


def per_sequence_g_sums(cache: Cache) -> np.ndarray:
    """(N, n_sub) float64: sum over the sequence's T positions of g per subcomponent (the per-sequence sums the switched
    mass is one matrix product away from)."""
    N = cache.n_sequences
    out = np.zeros((N, cache.n_sub), dtype=np.float64)
    idx = cache.indices.astype(np.int64)
    vals = cache.values.astype(np.float64)
    for b in range(N):
        e0, e1 = int(cache.indptr[b * SEQ_LEN]), int(cache.indptr[(b + 1) * SEQ_LEN])
        if e1 > e0:
            out[b] = np.bincount(idx[e0:e1], weights=vals[e0:e1], minlength=cache.n_sub)
    return out


def sigma_from_sums(g_sums: np.ndarray, rhos: np.ndarray, T: int = SEQ_LEN) -> np.ndarray:
    """The switched mass under a non-uniform background: sigma_b = |rho| - (1/T) sum_{c in rho} sum_t g_{b,t,c}, for the named
    set of the union (r = 0), the erased set of the soft erase (r = 1), and a hard-zero cell's soft-erase sigma; (N, K)
    float64 for K sets given as (n_sub, K) booleans."""
    assert rhos.dtype == np.bool_ and rhos.shape[0] == g_sums.shape[1]
    sizes = rhos.sum(axis=0).astype(np.float64)
    return sizes[None, :] - (g_sums @ rhos.astype(np.float64)) / float(T)


def t_star_stats(t: np.ndarray) -> dict[str, float]:
    t = np.asarray(t, dtype=np.int64)
    if t.size == 0:
        return {"n": 0}
    return {"n": int(t.size), "median": float(np.median(t)), "q1": float(np.percentile(t, 25)), "q3": float(np.percentile(t, 75)), "fraction_equal_T": float((t == SEQ_LEN).mean()),
            "fraction_at_least_8": float((t >= CONTRIBUTING_MIN_T_STAR).mean()), "n_contributing": int((t >= CONTRIBUTING_MIN_T_STAR).sum()), "clean_prefix_fraction": float((t / SEQ_LEN).mean())}


# ----------------------------------------------------------------------------- the run


def control_overlap_rows(cells: list[Cell], sources: dict[str, Any], alive: np.ndarray, prose_named: dict[float, np.ndarray]) -> list[dict[str, Any]]:
    """For every controlled cell on E or E_lab, the overlap of
    its control set with the set it matches (the same cell with control none), the two sizes, and the size of the pool the
    control drew from (the alive set for a plain control; alive minus prose-named at the cell's tau for a complement control,
    of which the code-specific erased set is a part), so that a positive control can be read against how nearly the two
    sets are the same population."""
    rows = []
    by_name = {c.name: c for c in cells}
    for c in cells:
        if c.control == "none" or c.eval_set == "donors" or c.family == "reference":
            continue
        base = c.name.replace(f"/ctl-{c.control}", "")
        if base not in by_name or sources.get(base) is None or sources[base].rho is None or sources[c.name].rho is None:
            continue
        A, C = sources[base].rho, sources[c.name].rho
        pool = alive if c.control == "plain" else (alive & ~prose_named[c.tau])
        inter = int((A & C).sum())
        rows.append({"cell": c.name, "family": c.family, "eval_set": c.eval_set, "pool": c.donor_pool, "tau": c.tau, "delta": c.delta, "control": c.control, "draw": c.draw, "rung": c.rung,
                     "n_named": int(A.sum()), "n_control": int(C.sum()), "overlap": inter, "fraction_of_named": inter / int(A.sum()) if int(A.sum()) else float("nan"),
                     "control_pool_size": int(pool.sum()), "named_in_control_pool": int((A & pool).sum()), "control_overflow": int(sum(sources[c.name].record.get("control", {}).get("overflow", {}).values()))})
    return rows


SET_COMPOSITION_RUNGS = ("1", "2", "2a", "2b", "3", "4")


def pool_usage(cache: Cache, tau: float = 0.1) -> np.ndarray:
    """Per subcomponent, the fraction of the pool's positions at which its label exceeds tau; (n_sub,) float64."""
    idx = cache.indices.astype(np.int64)[cache.values > np.float32(tau)]
    return np.bincount(idx, minlength=cache.n_sub).astype(np.float64) / float(cache.n_positions)


def set_composition_rows(cells: list[Cell], sources: dict[str, Any], norms: np.ndarray, usage: np.ndarray, alive: np.ndarray, rungs: tuple[str, ...] = SET_COMPOSITION_RUNGS) -> list[dict[str, Any]]:
    """For curve 1's union under r = 0 at tau = 0.1 and its plain
    control, at the small rungs per draw and as a mean over draws, the mean and median weight norm and the mean pool usage
    (the fraction of D_unif positions with g > 0.1) of the subcomponents each set names, with the same statistics over the
    whole alive set as a baseline: whether the union's small-rung sets are heavier or more used than the random control's."""
    def stats(sel: np.ndarray) -> dict[str, float]:
        n = int(sel.sum())
        if n == 0:
            return {"n_on": 0, "mean_norm": float("nan"), "median_norm": float("nan"), "mean_usage": float("nan")}
        return {"n_on": n, "mean_norm": float(norms[sel].mean()), "median_norm": float(np.median(norms[sel])), "mean_usage": float(usage[sel].mean())}

    rows: list[dict[str, Any]] = []
    for control, fam in (("none", "union"), ("plain", "control")):
        sel_cells = [c for c in cells if c.family == "union" and c.eval_set == "E" and c.donor_pool == "D_unif" and c.background == "r0" and c.delta == "excluded" and c.tau == 0.1 and c.control == control and c.rung in rungs]
        per_rung: dict[str, list[dict[str, float]]] = {}
        for c in sorted(sel_cells, key=lambda x: (rung_order(x.rung), x.draw)):
            st = stats(sources[c.name].rho)
            rows.append({"family": fam, "rung": c.rung, "draw": c.draw, **st})
            per_rung.setdefault(c.rung, []).append(st)
        for r, sts in per_rung.items():
            rows.append({"family": fam, "rung": r, "draw": "mean", "n_on": float(np.mean([x["n_on"] for x in sts])), "mean_norm": float(np.nanmean([x["mean_norm"] for x in sts])),
                         "median_norm": float(np.nanmean([x["median_norm"] for x in sts])), "mean_usage": float(np.nanmean([x["mean_usage"] for x in sts]))})
    rows.append({"family": "alive (baseline)", "rung": "", "draw": "", **stats(alive.astype(bool))})
    return rows


def spearman(a: np.ndarray, b: np.ndarray) -> float:
    """Spearman's rank correlation with average ranks for ties (pandas' rank), Pearson on the ranks."""
    ra, rb = pd.Series(a).rank(method="average").to_numpy(np.float64), pd.Series(b).rank(method="average").to_numpy(np.float64)
    ra, rb = ra - ra.mean(), rb - rb.mean()
    d = float(np.sqrt((ra * ra).sum() * (rb * rb).sum()))
    return float((ra * rb).sum() / d) if d > 0 else float("nan")


def _chain_key(c: Cell) -> str:
    rank = f"/{c.rank_key}-{c.rank_end}" if c.rank_key else ""  # the ranked pair's four chains
    return f"{c.family}/{c.eval_set}/{c.donor_pool}/tau{c.tau:g}/{c.background}/{c.delta[:4]}/ctl-{c.control}{rank}"


def run_pre_reads(run: str, out_dir: Path, *, draws: int = 8, inputs: PreReadInputs | None = None, log: Any = print) -> dict[str, Any]:
    from vpd_audit.donors import donors_dir, load_prose_named_and_f_code
    from vpd_audit.grid import compute_adaptive

    t_all = time.time()
    inp = inputs or paper_inputs(run, draws)
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    # ---- inputs
    caches: dict[str, Cache] = {f"{pool}_{run}": Cache.load(f"{inp.pool_map[pool]}_{run}") for pool in POOLS}
    eval_caches: dict[str, Cache] = {s: Cache.load(f"{inp.set_map[s]}_{run}") for s in ("E", "E_lab")}
    d_unif = caches[f"D_unif_{run}"]
    module_to_c = dict(d_unif.module_to_c)
    offsets = d_unif.offsets
    n_sub = d_unif.n_sub
    alive_vec = np.load(donors_dir() / f"alive_{inp.pool_map['D_unif']}_{run}.npy")
    alive = {run: (alive_vec, source_hash(alive_vec))}
    prose_named, f_code, pn_meta = load_prose_named_and_f_code(inp.cache_tag)
    with open(env.SETS_DIR / inp.strata_file) as f:
        strata = json.load(f)["strata"]
    adaptive = compute_adaptive(caches, run, inp.draws, inp.master_seed)
    adaptive_map = {(k.split("|tau")[0], float(k.split("|tau")[1])): tuple(v) for k, v in adaptive["insert"].items()}
    cells = enumerate_cells(runs=(run,), draws=inp.draws, adaptive=adaptive_map)
    # the ranked never-named pair orders the set by the weight norm ||U_c|| ||V_c|| of the run's model, so
    # the pre-reads load it on CPU when such a cell is enumerated for this run; the two keys are saved beside the tables
    norms_meta: dict[str, Any] | None = None
    norms_by_run: dict[str, np.ndarray] | None = None
    rank_keys: dict[str, str] | None = None
    if any(c.family == "never_named_ranked" for c in cells):
        from vpd_audit.artifacts import load_component_model
        from vpd_audit.weight_norms import weight_norms

        t_m = time.time()
        model = load_component_model(run, "cpu")
        norms, norms_meta = weight_norms(model)
        del model
        norms_by_run = {run: norms}
        counts_key = positive_label_counts(d_unif)
        rank_keys = {"weight_norm": norms_meta["sha256"], "positive_count": key_sha256(counts_key)}  # the launch asserts both
        log(f"[pre-reads] weight norms from the {run} model on CPU: sha256 {norms_meta['sha256'][:16]}; positive-label counts from D_unif: sha256 {rank_keys['positive_count'][:16]}; {time.time() - t_m:.0f} s")
    sources = build_sources(cells, caches, alive, {run: prose_named}, {run: f_code}, module_to_c, master_seed=inp.master_seed, log=log, weight_norms=norms_by_run)
    by_name = {c.name: c for c in cells}
    log(f"[pre-reads] {run}: {len(cells)} cells, caches " + ", ".join(f"{k} ({v.n_sequences} seqs, nnz {v.indptr[-1]})" for k, v in {**caches, **eval_caches}.items()) + f"; {time.time() - t_all:.0f} s")
    summary: dict[str, Any] = {"run": run, "draws": inp.draws, "n_cells": len(cells), "adaptive": adaptive}
    layers = sorted({layer_of(k) for k in module_to_c})
    layer_masks = {}
    for lyr in layers:
        m = np.zeros(n_sub, dtype=bool)
        for k in module_to_c:
            if layer_of(k) == lyr:
                m[offsets[k] : offsets[k] + module_to_c[k]] = True
        layer_masks[lyr] = m

    # ---- 1. dead against never named
    sum_g = np.bincount(d_unif.indices.astype(np.int64), weights=d_unif.values.astype(np.float64), minlength=n_sub)
    mean_g = sum_g / d_unif.n_positions
    dead_cache = mean_g <= ALIVE_THRESHOLD
    dead_saved = ~alive_vec
    all_positions = np.arange(d_unif.n_positions)
    unions_8 = {tau: union_source(d_unif, all_positions, tau) for tau in (0.0, 0.1, 0.5)}
    item1 = {"n_subcomponents": int(n_sub), "n_alive_saved": int(alive_vec.sum()), "n_dead_saved": int(dead_saved.sum()), "n_dead_from_cache": int(dead_cache.sum()),
             "saved_vs_cache_disagreements": int((dead_cache != dead_saved).sum()), "tables": {}}
    for tau, u8 in unions_8.items():
        never = ~u8
        item1["tables"][f"tau{tau:g}"] = {"n_named": int(u8.sum()), "n_never_named": int(never.sum()), "dead_and_never_named": int((dead_saved & never).sum()), "dead_and_named": int((dead_saved & u8).sum()),
                                          "alive_and_never_named": int((~dead_saved & never).sum()), "alive_and_named": int((~dead_saved & u8).sum())}
    summary["item1_dead_vs_never_named"] = item1

    # ---- 2. the never-named set and the strict set on the five caches
    sets2 = {"never_named_tau0.1": never_named_set(unions_8[0.1]), "strict_tau0": never_named_set(unions_8[0.0])}
    five = {**{p: caches[f"{p}_{run}"] for p in POOLS}, **eval_caches}
    item2: dict[str, Any] = {name: {"size": int(S.sum()), "sha256": source_hash(S), "caches": {}} for name, S in sets2.items()}
    per_cache_stats: dict[str, tuple[np.ndarray, np.ndarray]] = {}
    for cname, cache in five.items():
        per_cache_stats[cname] = per_subcomponent_counts_and_max(cache)
    for name, S in sets2.items():
        for cname, cache in five.items():
            ft = first_touched_from_cache(cache, S, TAU_QS_NEVER_NAMED)
            counts, mx = per_cache_stats[cname]
            per_pos = labels_in_set_per_position(cache, S)
            cs, ms = counts[S], mx[S]
            item2[name]["caches"][cname] = {
                "t_star": {f"tau_q{tq:g}": t_star_stats(ft[tq][0]) for tq in TAU_QS_NEVER_NAMED},
                "n_touched_mean": {f"tau_q{tq:g}": float(ft[tq][1].mean()) for tq in TAU_QS_NEVER_NAMED},
                "members": {"n": int(S.sum()), "with_any_positive_g": int((cs > 0).sum()), "positions_positive_median": float(np.median(cs)), "positions_positive_max": int(cs.max()) if cs.size else 0,
                            "max_g_at_most_0.01": int((ms <= 0.01).sum()), "max_g_in_0.01_to_0.1": int(((ms > 0.01) & (ms <= 0.1)).sum()), "max_g_above_0.1": int((ms > 0.1).sum()), "max_g_max": float(ms.max()) if ms.size else 0.0},
                "per_position_labels_in_set": {"mean": float(per_pos.mean()), "median": float(np.median(per_pos)), "max": int(per_pos.max()), "fraction_positions_with_any": float((per_pos > 0).mean())},
            }
        log(f"[pre-reads] item 2: {name} ({item2[name]['size']}) on the five caches; {time.time() - t_all:.0f} s")
    summary["item2_never_named_sets"] = item2
    # ---- 10: the two ranking keys of the ranked pair beside the alive and never-named flags, and their rank
    # correlation over the never-named set, so that agreement between the two top chains can be read as one fact or two
    if norms_by_run is not None:
        modules = np.empty(n_sub, dtype=object)
        within = np.zeros(n_sub, dtype=np.int64)
        for k in sorted(module_to_c):
            modules[offsets[k] : offsets[k] + module_to_c[k]] = k
            within[offsets[k] : offsets[k] + module_to_c[k]] = np.arange(module_to_c[k])
        S01 = sets2["never_named_tau0.1"]
        pd.DataFrame({"index": np.arange(n_sub, dtype=np.int64), "module": modules.astype(str), "c": within, "weight_norm": norms_by_run[run], "positive_count": counts_key,
                      "alive": alive_vec.astype(bool), "never_named_tau0.1": S01.astype(bool)}).to_parquet(out_dir / "rank_keys.parquet", index=False)
        summary["item10_rank_keys"] = {"n_never_named": int(S01.sum()), "spearman_weight_norm_vs_positive_count_over_never_named": spearman(norms_by_run[run][S01], counts_key[S01].astype(np.float64)),
                                       "never_named_with_positive_count_zero": int((counts_key[S01] == 0).sum()), "spearman_over_all": spearman(norms_by_run[run], counts_key.astype(np.float64))}

    # ---- 3, 4, 5, 8 from the sources
    def union_cells(tau: float, control: str) -> list[Cell]:
        return [c for c in cells if c.family == "union" and c.eval_set == "E" and c.donor_pool == "D_unif" and c.background == "r0" and c.delta == "excluded" and c.tau == tau and c.control == control]

    n_alive_total = int(alive_vec.sum())
    alive_by_module = {k: int(v.sum()) for k, v in split_by_module(alive_vec, module_to_c, offsets).items()}
    overlap_rows = []
    ctl_by = {(c.draw, c.rung): c for c in union_cells(0.1, "plain")}
    for c in sorted(union_cells(0.1, "none"), key=lambda x: (x.draw, rung_order(x.rung))):
        if (c.draw, c.rung) not in ctl_by:
            continue
        U, C = sources[c.name].rho, sources[ctl_by[(c.draw, c.rung)].name].rho
        n = int(U.sum())
        row = {"draw": c.draw, "rung": c.rung, "n_on": n, "overlap_total": int((U & C).sum()), "fraction_total": float((U & C).sum() / n) if n else float("nan"), "expected_total": n / n_alive_total}
        for k, (u_k, c_k) in zip(sorted(module_to_c), zip(split_by_module(U, module_to_c, offsets).values(), split_by_module(C, module_to_c, offsets).values())):
            nk = int(u_k.sum())
            row[f"fraction__{k}"] = float((u_k & c_k).sum() / nk) if nk else float("nan")
            row[f"expected__{k}"] = nk / alive_by_module[k] if alive_by_module[k] else float("nan")
        overlap_rows.append(row)
    overlap = pd.DataFrame(overlap_rows)
    overlap.to_csv(out_dir / "overlap_union_vs_control.csv", index=False)
    summary["item3_overlap"] = {"by_rung_mean_over_draws": overlap.groupby("rung")[["n_on", "fraction_total", "expected_total"]].mean().to_dict("index") if len(overlap) else {}}

    coverage_rows = []
    for tau in (0.0, 0.1, 0.5):
        for c in union_cells(tau, "none"):
            U = sources[c.name].rho
            row = {"tau": tau, "draw": c.draw, "rung": c.rung, "n_on": int(U.sum()), "n_on_alive": int((U & alive_vec).sum()), "n_on_dead": int((U & ~alive_vec).sum())}
            for lyr, m in layer_masks.items():
                row[f"coverage_layer_{lyr}"] = float((U & alive_vec & m).sum() / (alive_vec & m).sum())
            row["coverage_total"] = float((U & alive_vec).sum() / n_alive_total)
            coverage_rows.append(row)
    coverage = pd.DataFrame(coverage_rows).sort_values(["tau", "draw", "rung"], key=lambda s: s.map(rung_order) if s.name == "rung" else s)
    coverage.to_csv(out_dir / "coverage.csv", index=False)
    r7 = [sources[c.name].rho for c in sorted(union_cells(0.1, "none"), key=lambda x: x.draw) if c.rung == "7"]
    jac = [float((a & b).sum() / (a | b).sum()) for i, a in enumerate(r7) for b in r7[i + 1 :]]
    inter_all = np.logical_and.reduce(r7) if r7 else np.zeros(n_sub, bool)
    union_all = np.logical_or.reduce(r7) if r7 else np.zeros(n_sub, bool)
    summary["item4_coverage"] = {"rung_7_pairwise_jaccard": {"mean": float(np.mean(jac)) if jac else float("nan"), "min": float(np.min(jac)) if jac else float("nan"), "max": float(np.max(jac)) if jac else float("nan"), "n_pairs": len(jac)},
                                 "rung_7_intersection_of_draws": int(inter_all.sum()), "rung_7_union_of_draws": int(union_all.sum()),
                                 "coverage_total_by_tau_and_rung_mean_over_draws": {f"tau{t:g}": coverage[coverage.tau == t].groupby("rung")["coverage_total"].mean().to_dict() for t in (0.0, 0.1, 0.5)}}
    n_on_tau0 = {f"k{c.draw}/r{c.rung}": int(sources[c.name].rho.sum()) for c in union_cells(0.0, "none")}
    summary["item5_tau0"] = {"n_on_union_tau0": n_on_tau0, "strict_never_named_size": int(sets2["strict_tau0"].sum()), "never_named_tau0.1_size": int(sets2["never_named_tau0.1"].sum())}
    overflow_rows = [{"cell": c.name, "family": c.family, "eval_set": c.eval_set, "rung": c.rung, "draw": c.draw, "control": c.control, "module": k, "overflow": int(v)}
                     for c in cells if c.control != "none" for k, v in sources[c.name].record.get("control", {}).get("overflow", {}).items()]
    overflow = pd.DataFrame(overflow_rows, columns=["cell", "family", "eval_set", "rung", "draw", "control", "module", "overflow"])
    overflow.to_csv(out_dir / "control_overflow.csv", index=False)
    ov_rows = control_overlap_rows(cells, sources, alive_vec, prose_named)  # every controlled cell's set against the set it matches
    pd.DataFrame(ov_rows, columns=["cell", "family", "eval_set", "pool", "tau", "delta", "control", "draw", "rung", "n_named", "n_control", "overlap", "fraction_of_named", "control_pool_size", "named_in_control_pool", "control_overflow"]).to_csv(out_dir / "control_overlap.csv", index=False)
    summary["item11_control_overlap"] = {"n_controlled_cells": len(ov_rows)}
    summary["item8_overflow"] = {"n_control_cells": sum(1 for c in cells if c.control != "none"), "n_cells_with_overflow": int(overflow["cell"].nunique()) if len(overflow) else 0,
                                 "total_overflow_entries": int(overflow["overflow"].sum()) if len(overflow) else 0,
                                 "by_module": overflow.groupby("module")["overflow"].sum().to_dict() if len(overflow) else {}}
    log(f"[pre-reads] items 3, 4, 5, 8 from the sources; {time.time() - t_all:.0f} s")

    # ---- 6. testability: t* of every hard-zero cell on E and E_lab, per sequence, at the loop's two tau_q
    hz = [c for c in cells if c.is_hard_zero and c.eval_set in ("E", "E_lab")]
    unique: dict[tuple[str, str], list[Cell]] = {}
    for c in hz:
        unique.setdefault((c.eval_set, sources[c.name].record["source_sha256"]), []).append(c)
    t_rows: list[pd.DataFrame] = []
    cell_stats: dict[str, dict[str, Any]] = {}
    strata_arr = np.asarray(strata)
    strata_groups = {"all": None, **{s: (strata_arr == s) for s in sorted(set(strata))}, "other": strata_arr != inp.positive_stratum}
    t_done = 0
    for (eval_set, _sha), group in unique.items():
        cache = eval_caches[eval_set]
        S = sources[group[0].name].rho
        ft = first_touched_from_cache(cache, S, TAU_QS_LOOP)
        n = cache.n_sequences
        for c in group:
            df = pd.DataFrame({"cell": c.name, "seq": np.arange(n, dtype=np.int32), "t_star_0.1": ft[0.1][0].astype(np.int16), "t_star_0": ft[0.0][0].astype(np.int16),
                               "n_touched_0.1": ft[0.1][1].astype(np.int16), "n_touched_0": ft[0.0][1].astype(np.int16)})
            t_rows.append(df)
            st: dict[str, Any] = {}
            for tq in TAU_QS_LOOP:
                t = ft[tq][0]
                if eval_set == "E_lab":
                    for sname, mask in strata_groups.items():
                        st[f"tau_q{tq:g}|{sname}"] = t_star_stats(t if mask is None else t[mask])
                else:
                    st[f"tau_q{tq:g}|all"] = t_star_stats(t)
            cell_stats[c.name] = st
        t_done += 1
        if t_done % 100 == 0:
            log(f"[pre-reads] item 6: {t_done} of {len(unique)} unique erased sets; {time.time() - t_all:.0f} s")
    t_star_table = pd.concat(t_rows, ignore_index=True)
    t_star_table["cell"] = t_star_table["cell"].astype("category")
    t_star_table.to_parquet(out_dir / "t_star.parquet", index=False)
    test_rows = []
    chains: dict[str, dict[str, list[Cell]]] = {}
    for c in hz:
        chains.setdefault(_chain_key(c), {}).setdefault(c.rung, []).append(c)
    for ck, rungs in chains.items():
        for r, cs in rungs.items():
            for key in cell_stats[cs[0].name]:
                tq_label, stratum = key.split("|")
                contributing = [cell_stats[c.name][key]["n_contributing"] for c in cs]
                clean = [cell_stats[c.name][key]["clean_prefix_fraction"] for c in cs]
                test_rows.append({"chain": ck, "rung": r, "tau_q": tq_label, "stratum": stratum, "n_draws": len(cs), "n_sequences": cell_stats[cs[0].name][key]["n"],
                                  "mean_n_contributing": float(np.mean(contributing)), "min_n_contributing": int(np.min(contributing)), "mean_clean_prefix_fraction": float(np.mean(clean)),
                                  "fraction_never_touched": float(np.mean([cell_stats[c.name][key]["fraction_equal_T"] for c in cs])),
                                  "floor_met": bool(np.mean(contributing) >= FLOOR_CONTRIBUTING and np.mean(clean) >= FLOOR_CLEAN_FRACTION)})
    testability = pd.DataFrame(test_rows).sort_values(["chain", "tau_q", "stratum", "rung"], key=lambda s: s.map(rung_order) if s.name == "rung" else s)
    testability.to_csv(out_dir / "testability.csv", index=False)
    summary["item6_testability"] = {"n_hard_zero_cells": len(hz), "n_unique_erased_sets": len(unique), "n_chains": len(chains), "t_star_rows": int(len(t_star_table)),
                                    "testable_rungs_by_chain_tau_q0.1_all": {ck: sorted([r for r in rungs if any(x["floor_met"] for x in test_rows if x["chain"] == ck and x["rung"] == r and x["tau_q"] == "tau_q0.1" and x["stratum"] == "all")], key=rung_order)
                                                                             for ck, rungs in chains.items()}}
    log(f"[pre-reads] item 6: {len(hz)} hard-zero cells, {len(unique)} unique sets, {len(t_star_table)} t* rows; {time.time() - t_all:.0f} s")

    # ---- 7. the switched mass of every non-uniform cell with a source, from per-sequence sums of g
    sigma_summary: dict[str, Any] = {}
    sums = {s: per_sequence_g_sums(eval_caches[s]) for s in ("E", "E_lab")}
    sums["donors"] = per_sequence_g_sums(d_unif)
    for eval_set in ("E", "E_lab", "donors"):
        sel_cells = [c for c in cells if c.eval_set == eval_set and c.background != "uniform" and sources[c.name].rho is not None]
        if not sel_cells:
            continue
        R = np.stack([sources[c.name].rho for c in sel_cells], axis=1)
        if eval_set == "donors":
            from vpd_audit.sources import donor_set

            rows_ = []
            for c, j in zip(sel_cells, range(R.shape[1])):
                ds = donor_set(c.donor_pool, d_unif.n_sequences, c.draw, c.rung, inp.master_seed)
                seqs = np.asarray(ds.sequences, dtype=np.int64)
                sig = sigma_from_sums(sums["donors"][seqs], R[:, j : j + 1])[:, 0]
                rows_.append(pd.DataFrame({"cell": c.name, "seq": np.arange(seqs.size, dtype=np.int32), "pool_sequence": seqs.astype(np.int32), "sigma": sig}))
            long = pd.concat(rows_, ignore_index=True)
            long.to_parquet(out_dir / "sigma_donors.parquet", index=False)
            sigma_summary["donors"] = {"n_cells": len(sel_cells), "rows": int(len(long))}
            continue
        sig = sigma_from_sums(sums[eval_set], R)
        for j, c in enumerate(sel_cells):  # a level cell's named entries contribute (1 - g) |s - r_bg|: s (never-named at labels) or 1 - s (at 1) times the set's sigma
            if c.family == "level":
                assert c.level is not None
                sig[:, j] *= c.level if c.background == "r0" else 1.0 - c.level
        wide = pd.DataFrame(sig, columns=[c.name for c in sel_cells])
        wide.insert(0, "seq", np.arange(sig.shape[0], dtype=np.int32))
        wide.to_parquet(out_dir / f"sigma_{eval_set}.parquet", index=False)
        sigma_summary[eval_set] = {"n_cells": len(sel_cells), "n_sequences": int(sig.shape[0]), "bytes": int((out_dir / f"sigma_{eval_set}.parquet").stat().st_size)}
        if eval_set == "E":
            pooled_rungs = [r for r in ("1", "2", "3", "4", "5", "5a", "6", "6a", "7")]
            u_idx = [j for j, c in enumerate(sel_cells) if c.family == "union" and c.donor_pool == "D_unif" and c.background == "r0" and c.tau == 0.1 and c.control == "none" and c.rung in pooled_rungs]
            c_idx = [j for j, c in enumerate(sel_cells) if c.family == "union" and c.donor_pool == "D_unif" and c.background == "r0" and c.tau == 0.1 and c.control == "plain" and c.rung in pooled_rungs]
            pooled_u, pooled_c = sig[:, u_idx].ravel(), sig[:, c_idx].ravel()
            deciles = np.percentile(pooled_u, np.arange(0, 101, 10)).tolist()
            sigma_summary["union_tau0.1_r0_pooled"] = {"n_points": int(pooled_u.size), "n_cells": len(u_idx), "deciles_0_to_100": deciles,
                                                        "control_n_points": int(pooled_c.size), "control_fraction_above_union_top_edge": float((pooled_c > pooled_u.max()).mean()) if pooled_c.size else float("nan"),
                                                        "control_fraction_below_union_bottom_edge": float((pooled_c < pooled_u.min()).mean()) if pooled_c.size else float("nan"),
                                                        "per_rung_mean": {r: float(np.mean([sig[:, j].mean() for j in u_idx if sel_cells[j].rung == r])) for r in pooled_rungs if any(sel_cells[j].rung == r for j in u_idx)},
                                                        "control_per_rung_mean": {r: float(np.mean([sig[:, j].mean() for j in c_idx if sel_cells[j].rung == r])) for r in pooled_rungs if any(sel_cells[j].rung == r for j in c_idx)}}
    summary["item7_switched_mass"] = sigma_summary
    log(f"[pre-reads] item 7: sigma tables {list(sigma_summary)}; {time.time() - t_all:.0f} s")

    # ---- 12: the composition of curve 1's small-rung sets against its control's
    if norms_by_run is not None:
        comp = set_composition_rows(cells, sources, norms_by_run[run], pool_usage(d_unif, 0.1), alive_vec)
        pd.DataFrame(comp, columns=["family", "rung", "draw", "n_on", "mean_norm", "median_norm", "mean_usage"]).to_csv(out_dir / "set_composition.csv", index=False)
        summary["item12_set_composition"] = {"rows": [r for r in comp if r["draw"] in ("mean", "")], "rungs": list(SET_COMPOSITION_RUNGS)}
        log(f"[pre-reads] item 12: set composition of curve 1 and its control at rungs {SET_COMPOSITION_RUNGS}, {len(comp)} rows; {time.time() - t_all:.0f} s")
    # ---- 9. the rung-8 excess of the identities' union chain, per sequence (two ends)
    if inp.chains_dir is not None:
        ch = pd.read_parquet(inp.chains_dir / "per_sequence.parquet")
        k8 = ch[ch.cell == f"{run}/E/union/D_unif/tau0.1/r0/excl/k0/r8"].sort_values("seq")["kl_mean"].to_numpy(np.float64)
        k0 = ch[ch.cell == f"{run}/E/ref/importances"].sort_values("seq")["kl_mean"].to_numpy(np.float64)
        ex = k8 - k0
        summary["item9_rung8_excess"] = {"n": int(ex.size), "mean_excess": float(ex.mean()), "sd_over_sequences": float(ex.std(ddof=1)), "se_of_mean": float(ex.std(ddof=1) / np.sqrt(ex.size)),
                                         "guessed_se": 0.0016, "sd_rung_0": float(k0.std(ddof=1)), "sd_rung_8": float(k8.std(ddof=1))}
    else:
        summary["item9_rung8_excess"] = {"available": False, "reason": "no identities chain store for this run"}

    # ---- manifest and summary
    manifest = {"run": run, "draws": inp.draws, "master_seed": inp.master_seed, "commits": code_commits(), "seconds": time.time() - t_all,
                "caches": {k: {"name": v.name, "n_sequences": v.n_sequences, "nnz": int(v.indptr[-1]), "sha256": v.sha256} for k, v in {**caches, **eval_caches}.items()},
                "alive_sha256": alive[run][1], "prose_named": pn_meta, "strata_file": inp.strata_file, "adaptive": adaptive, "n_cells": len(cells),
                "weight_norms": norms_meta, "rank_keys": rank_keys, "files": sorted(p.name for p in out_dir.iterdir() if p.is_file())}
    with open(out_dir / "manifest.json", "w") as f:
        json.dump(manifest, f, indent=2, sort_keys=True, default=str)
    with open(out_dir / "summary.json", "w") as f:
        json.dump(summary, f, indent=2, sort_keys=True, default=str)
    text = format_pre_reads(summary, overlap, coverage, testability)
    with open(out_dir / "summary.md", "w") as f:
        f.write(text + "\n")
    log(text)
    log(f"[pre-reads] done in {time.time() - t_all:.0f} s -> {out_dir}")
    return {"run": run, "seconds": time.time() - t_all, "n_cells": len(cells), "t_star_rows": int(len(t_star_table)), "files": manifest["files"]}


def rerender_summary(out_dir: Path) -> str:
    """summary.md again from the saved summary.json and the CSV tables of a finished pre-reads directory (no recomputation)."""
    out_dir = Path(out_dir)
    with open(out_dir / "summary.json") as f:
        s = json.load(f)
    text = format_pre_reads(s, pd.read_csv(out_dir / "overlap_union_vs_control.csv"), pd.read_csv(out_dir / "coverage.csv"), pd.read_csv(out_dir / "testability.csv", dtype={"rung": str}))
    with open(out_dir / "summary.md", "w") as f:
        f.write(text + "\n")
    return text


def _fmt(x: Any, nd: int = 3) -> str:
    return f"{x:.{nd}f}" if isinstance(x, float) else str(x)


def format_pre_reads(s: dict[str, Any], overlap: pd.DataFrame, coverage: pd.DataFrame, testability: pd.DataFrame) -> str:
    L = [f"# Pre-reads for the {s['run']} run: label-only numbers from the caches and the sources", ""]
    i1 = s["item1_dead_vs_never_named"]
    L.append(f"## 1. Dead against never named ({i1['n_subcomponents']} subcomponents; alive by the saved vector {i1['n_alive_saved']}, dead {i1['n_dead_saved']}; dead recomputed from the cache {i1['n_dead_from_cache']}, disagreements {i1['saved_vs_cache_disagreements']})")
    L.append("")
    L.append("| tau | named | never named | dead & never named | dead & named | alive & never named | alive & named |")
    L.append("|---|---|---|---|---|---|---|")
    for tau, t in i1["tables"].items():
        L.append(f"| {tau[3:]} | {t['n_named']} | {t['n_never_named']} | {t['dead_and_never_named']} | {t['dead_and_named']} | {t['alive_and_never_named']} | {t['alive_and_named']} |")
    L.append("")
    L.append("## 2. The never-named set (tau = 0.1) and the strict set (tau = 0) on the five caches")
    for name, it in s["item2_never_named_sets"].items():
        L.append("")
        L.append(f"### {name}: {it['size']} members")
        L.append("")
        L.append("| cache | tau_q | median t* | q1 / q3 | fraction = T | fraction >= 8 | clean-prefix fraction | mean touched positions |")
        L.append("|---|---|---|---|---|---|---|---|")
        for cname, cs in it["caches"].items():
            for tq, st in cs["t_star"].items():
                L.append(f"| {cname} | {tq[5:]} | {st['median']:.0f} | {st['q1']:.0f} / {st['q3']:.0f} | {st['fraction_equal_T']:.3f} | {st['fraction_at_least_8']:.3f} | {st['clean_prefix_fraction']:.3f} | {cs['n_touched_mean'][tq]:.1f} |")
        L.append("")
        L.append("| cache | members with any g > 0 | median positions with g > 0 | max g <= 0.01 | 0.01 < max g <= 0.1 | max g > 0.1 | largest max g | labels in the set per position: mean / max / fraction of positions with any |")
        L.append("|---|---|---|---|---|---|---|---|")
        for cname, cs in it["caches"].items():
            m, p = cs["members"], cs["per_position_labels_in_set"]
            L.append(f"| {cname} | {m['with_any_positive_g']} of {m['n']} | {m['positions_positive_median']:.0f} | {m['max_g_at_most_0.01']} | {m['max_g_in_0.01_to_0.1']} | {m['max_g_above_0.1']} | {m['max_g_max']:.4f} | {p['mean']:.2f} / {p['max']} / {p['fraction_positions_with_any']:.3f} |")
    L.append("")
    L.append("## 3. Union against its plain control at tau = 0.1: the fraction of the union set the control also names (mean over draws), beside n_on / |alive|")
    L.append("")
    L.append("| rung | n_on | overlap fraction | expected n_on / alive |")
    L.append("|---|---|---|---|")
    for r, v in sorted(s["item3_overlap"]["by_rung_mean_over_draws"].items(), key=lambda kv: rung_order(kv[0])):
        L.append(f"| {r} | {v['n_on']:.0f} | {v['fraction_total']:.3f} | {v['expected_total']:.3f} |")
    L.append("Per matrix in overlap_union_vs_control.csv.")
    L.append("")
    i4 = s["item4_coverage"]
    L.append("## 4. E2's coverage: the fraction of alive subcomponents the union names (mean over draws; per layer in coverage.csv)")
    L.append("")
    all_rungs = sorted({r for by in i4["coverage_total_by_tau_and_rung_mean_over_draws"].values() for r in by}, key=rung_order)  # the adaptive rungs exist only where the rule fired
    L.append("| tau | " + " | ".join(f"rung {r}" for r in all_rungs) + " |")
    L.append("|---|" + "---|" * len(all_rungs))
    for tau, by in i4["coverage_total_by_tau_and_rung_mean_over_draws"].items():
        L.append(f"| {tau[3:]} | " + " | ".join(f"{by[r]:.3f}" if r in by else "" for r in all_rungs) + " |")
    j = i4["rung_7_pairwise_jaccard"]
    L.append(f"Overlap between draws at rung 7 (tau = 0.1): pairwise Jaccard mean {j['mean']:.3f} (min {j['min']:.3f}, max {j['max']:.3f}, {j['n_pairs']} pairs); intersection of all draws {i4['rung_7_intersection_of_draws']}, union {i4['rung_7_union_of_draws']}.")
    L.append("")
    i5 = s["item5_tau0"]
    L.append(f"## 5. The union's n_on at tau = 0 (draw/rung): " + ", ".join(f"{k}: {v}" for k, v in sorted(i5["n_on_union_tau0"].items(), key=lambda kv: (int(kv[0].split('/')[0][1:]), rung_order(kv[0].split('/r')[1])))))
    L.append(f"Never-named set at tau = 0.1: {i5['never_named_tau0.1_size']}; the strict never-named set at tau = 0: {i5['strict_never_named_size']}.")
    L.append("")
    i6 = s["item6_testability"]
    L.append(f"## 6. Testability of the hard-zero chains ({i6['n_hard_zero_cells']} cells, {i6['n_unique_erased_sets']} distinct erased sets, {i6['n_chains']} chains; per-sequence t* in t_star.parquet, {i6['t_star_rows']} rows; the full table in testability.csv)")
    L.append("")
    L.append("Rungs meeting the readability floor at tau_q = 0.1 on the whole set (at least 64 contributing on average over draws, clean-prefix fraction at least 0.05):")
    L.append("")
    L.append("| chain | testable rungs |")
    L.append("|---|---|")
    for ck, rs in sorted(i6["testable_rungs_by_chain_tau_q0.1_all"].items()):
        L.append(f"| {ck} | {', '.join(rs) if rs else 'none'} |")
    L.append("")
    L.append("Clean-prefix fraction and contributing count at tau_q = 0.1 (mean over draws), whole set, per chain and rung:")
    L.append("")
    sub = testability[(testability.tau_q == "tau_q0.1") & (testability.stratum == "all")]
    L.append("| chain | rung | mean contributing | mean clean-prefix fraction | fraction never touched | floor met |")
    L.append("|---|---|---|---|---|---|")
    for _, r in sub.iterrows():
        L.append(f"| {r['chain']} | {r['rung']} | {r['mean_n_contributing']:.1f} | {r['mean_clean_prefix_fraction']:.3f} | {r['fraction_never_touched']:.3f} | {r['floor_met']} |")
    L.append("")
    i7 = s["item7_switched_mass"]
    L.append("## 7. Switched mass under the non-uniform backgrounds (float64 from the caches; tables sigma_E.parquet, sigma_E_lab.parquet, sigma_donors.parquet)")
    L.append("")
    for k, v in i7.items():
        if k == "union_tau0.1_r0_pooled":
            L.append(f"The union (tau = 0.1, r = 0) pooled over rungs 1 to 7 with 5a and 6a and all draws: {v['n_points']} points from {v['n_cells']} cells; deciles (0 to 100 by 10): " + ", ".join(f"{d:.2f}" for d in v["deciles_0_to_100"]))
            L.append(f"Its plain control: {v['control_n_points']} points; fraction above the union's top edge {v['control_fraction_above_union_top_edge']:.3f}, below its bottom edge {v['control_fraction_below_union_bottom_edge']:.3f}.")
            L.append("Per-rung mean sigma, union then control: " + "; ".join(f"{r}: {v['per_rung_mean'][r]:.2f} / {v['control_per_rung_mean'].get(r, float('nan')):.2f}" for r in sorted(v["per_rung_mean"], key=rung_order)))
        else:
            L.append(f"- {k}: {v}")
    L.append("")
    i8 = s["item8_overflow"]
    L.append(f"## 8. Matched-random controls' overflow into the dead set: {i8['n_cells_with_overflow']} of {i8['n_control_cells']} control cells overflow, {i8['total_overflow_entries']} entries in all; by module: {i8['by_module'] or 'none'} (per cell in control_overflow.csv)")
    L.append("")
    if s.get("item12_set_composition"):
        i12 = s["item12_set_composition"]
        base = next((r for r in i12["rows"] if r["family"].startswith("alive")), None)
        L.append("## 12. The composition of curve 1's small-rung sets against its plain control's (mean over draws): the mean and median weight norm ||U_c|| ||V_c|| and the mean pool usage (the fraction of D_unif positions with g > 0.1) of the subcomponents each set names; per draw in set_composition.csv")
        L.append("")
        L.append("| rung | union n_on | union mean norm | union median norm | union mean usage | control mean norm | control median norm | control mean usage |")
        L.append("|---|---|---|---|---|---|---|---|")
        by = {(r["family"], r["rung"]): r for r in i12["rows"] if r["draw"] == "mean"}
        for rg in i12["rungs"]:
            u, c = by.get(("union", rg)), by.get(("control", rg))
            if u is None:
                continue
            L.append(f"| {rg} | {u['n_on']:.0f} | {u['mean_norm']:.4f} | {u['median_norm']:.4f} | {u['mean_usage']:.4f} | " + (f"{c['mean_norm']:.4f} | {c['median_norm']:.4f} | {c['mean_usage']:.4f} |" if c else " | | |"))
        if base:
            L.append(f"The whole alive set ({base['n_on']} subcomponents) as the baseline: mean norm {base['mean_norm']:.4f}, median norm {base['median_norm']:.4f}, mean usage {base['mean_usage']:.4f}. "
                     "A union set heavier or more used than its control's at the same count would be a rival to the conflict reading.")
        L.append("")
    i9 = s["item9_rung8_excess"]
    if i9.get("available", True):
        L.append(f"## 9. The rung-8 excess of the identities' union chain over its rung 0, per sequence (two ends): mean {i9['mean_excess']:.4f}, SD over {i9['n']} sequences {i9['sd_over_sequences']:.4f}, "
                 f"standard error of the mean {i9['se_of_mean']:.5f} against the {i9['guessed_se']} guessed in advance; SD of rung 0 {i9['sd_rung_0']:.4f}, of rung 8 {i9['sd_rung_8']:.4f}")
    else:
        L.append(f"## 9. Not available: {i9['reason']}")
    return "\n".join(L)


# ============================================================================= the tier-4 label-only pre-reads
# Label-only pre-reads for the marginal-matched control and the code-leaning group. New functions and new files under <pre_reads>/<run>/s7/ only: nothing above this line changed and
# `run_pre_reads` is not rerun, so every existing pre-reads file stays as committed.

S7_TAU = 0.1
S7_RUNGS: tuple[str, ...] = ("1", "2", "2a", "2b", "3")  # 1, 8, 16, 32, 64 donor positions
S7_GATE_RUNGS: tuple[str, ...] = ("1", "2", "2a")
S7_GATE_BOUNDS: dict[str, tuple[float, float]] = {"mean_usage": (0.9, 1.1), "mean_norm": (0.95, 1.05), "mean_sigma": (0.95, 1.05)}
S7_N_SEEDS = 200
S7_REPLICATE_1_RUNGS: tuple[str, ...] = ("1", "2")
S7_PLAIN_FAMILIES: dict[str, tuple[str, str, tuple[str, ...]]] = {"union": ("union", "r0", S7_RUNGS), "soft_erase": ("soft_erase", "r1", ("1", "2", "3"))}  # the plain control's seed carries the family
from vpd_audit import stats_s7 as _s7  # noqa: E402  (the rule itself lives in stats_s7.py, which the frozen analysis applies; one implementation)

S7_DECISIVE_MAX_OVERLAP = _s7.DECISIVE_MAX_OVERLAP


def _member_stats(norms: np.ndarray, usage: np.ndarray, members: np.ndarray) -> dict[str, float]:
    """Count, and the mean, median, and 90th percentile of the weight norm and of the usage, over `members` (global indices,
    with multiplicity when several sets are pooled)."""
    if members.size == 0:
        return {"n": 0, **{f"{s}_{v}": float("nan") for v in ("norm", "usage") for s in ("mean", "median", "p90")}}
    out: dict[str, float] = {"n": int(members.size)}
    for v, x in (("norm", norms[members]), ("usage", usage[members])):
        out[f"mean_{v}"], out[f"median_{v}"], out[f"p90_{v}"] = float(x.mean()), float(np.median(x)), float(np.percentile(x, 90))
    return out


def percentile_of(x: float, dist: np.ndarray) -> float:
    """Where x falls in `dist`, as a mid-rank percentile: 100 (#{d < x} + #{d = x} / 2) / n."""
    dist = np.asarray(dist, dtype=np.float64)
    return float(100.0 * ((dist < x).sum() + 0.5 * (dist == x).sum()) / dist.size)


def decisive_rungs(overlap_by_rung: pd.DataFrame, *, replicate: int = 0, family: str = "union") -> list[str]:
    """A rung is decisive if the switched-mass overlap between the marginal
    control (replicate 0) and the union, pooled over draws (total intersection mass over total named mass), is at most one
    third. The marginal sets are the same in every family, so the family only names the rungs the family has."""
    t = overlap_by_rung[(overlap_by_rung.control == "marginal") & (overlap_by_rung.replicate == replicate)]
    o = {str(r): float(v) for r, v in zip(t["rung"], t["overlap_mass_pooled"])}
    return _s7.decisive_rungs(o, [r for r in S7_PLAIN_FAMILIES[family][2] if r in o])


S7_N_REAL_SETS = 200


def real_position_sets(d_unif: Cache, norms: np.ndarray, usage: np.ndarray, *, draws: int = 8, n_sets: int = S7_N_REAL_SETS, master_seed: int = 0) -> pd.DataFrame:
    """`n_sets` sets of `draws` real pool positions with the donor draws' seeding pattern, beside the realized
    one. Set j holds the rung-1 donor positions of draws j * draws to j * draws + draws - 1, each the first entry of the
    position permutation seeded (master, "posperm", "D_unif", draw) as `sources.donor_set` draws it; set 0 is the realized
    union's eight draws, through the same code. Per set: the pooled count, and the per-member mean usage and weight norm over
    the sets the positions name at tau = 0.1. Real positions co-occur, which the sampler's independent seeds do not, so this is
    the yardstick for whether the realized draws are an ordinary high draw of the pool."""
    from vpd_audit.sources import donor_set

    rows = []
    for j in range(n_sets + 1):
        tot_u = tot_n = 0.0
        count, positions, counts = 0, [], []
        for k in range(j * draws, (j + 1) * draws):
            ds = donor_set("D_unif", d_unif.n_sequences, k, "1", master_seed)
            rho = union_source(d_unif, ds.positions, S7_TAU)
            tot_u += float(usage[rho].sum())
            tot_n += float(norms[rho].sum())
            count += int(rho.sum())
            positions.append(int(ds.positions[0]))
            counts.append(int(rho.sum()))
        rows.append({"set": j, "realized": j == 0, "first_draw": j * draws, "n": count, "mean_usage": tot_u / count if count else float("nan"), "mean_norm": tot_n / count if count else float("nan"),
                     "min_count": int(min(counts)), "max_count": int(max(counts)), "positions": " ".join(str(p) for p in positions)})
    return pd.DataFrame(rows)


def marginal_pre_read(d_unif: Cache, g_sums_E: np.ndarray, alive_vec: np.ndarray, alive_sha: str, norms: np.ndarray, run: str, *, draws: int = 8, master_seed: int = 0,
                      n_seeds: int = S7_N_SEEDS, log: Any = print) -> tuple[dict[str, pd.DataFrame], dict[str, Any]]:
    """The marginal control's label-only pre-read for curve 1's configuration (union on E, donors from D_unif, tau = 0.1, r0, residual excluded) at rungs
    1, 2, 2a, 2b, 3: the composition of the union, the plain control, and the marginal control; the overlap of each control
    with the union by count and by switched mass on E; the usage distribution; the sampler's spread over `n_seeds`
    label-only seeds with the gate on its bias. The union and plain sets are built by `build_sources` from the enumerated
    cells, so they are the run's own; the marginal sets by `matched_random_source` with the rates of `marginal_rates`."""
    from vpd_audit.sources import marginal_rates, matched_random_source, n_on

    t0 = time.time()
    module_to_c, offsets, n_sub = dict(d_unif.module_to_c), d_unif.offsets, d_unif.n_sub
    assert alive_vec.shape == norms.shape == (n_sub,) and g_sums_E.shape[1] == n_sub
    usage = pool_usage(d_unif, S7_TAU)
    lam = marginal_rates(usage, d_unif.n_positions)
    candidates = lam > 0
    assert np.array_equal(candidates, usage > 0)
    all_cells = enumerate_cells(runs=(run,), draws=draws)

    def pick(family: str, background: str, control: str, rungs: tuple[str, ...]) -> list[Cell]:
        return [c for c in all_cells if c.family == family and c.eval_set == "E" and c.donor_pool == "D_unif" and c.tau == S7_TAU and c.background == background
                and c.delta == "excluded" and c.control == control and c.rung in rungs]

    union_cells = pick("union", "r0", "none", S7_RUNGS)
    plain_cells = {fam: pick(f, bg, "plain", rungs) for fam, (f, bg, rungs) in S7_PLAIN_FAMILIES.items()}
    named_se = pick("soft_erase", "r1", "none", S7_PLAIN_FAMILIES["soft_erase"][2])
    assert len(union_cells) == draws * len(S7_RUNGS) and all(len(v) == draws * len(S7_PLAIN_FAMILIES[f][2]) for f, v in plain_cells.items()) and len(named_se) == draws * 3
    cells = union_cells + plain_cells["union"] + plain_cells["soft_erase"] + named_se
    sources = build_sources(cells, {f"D_unif_{run}": d_unif}, {run: (alive_vec, alive_sha)}, None, None, module_to_c, master_seed=master_seed, log=log)
    U = {(c.rung, c.draw): sources[c.name].rho for c in union_cells}
    for c in named_se:  # the soft erase's named set is the union's set at the same draw and rung: one named set serves every family
        assert np.array_equal(sources[c.name].rho, U[(c.rung, c.draw)]), c.name
    # ---- the sets: (control, family, replicate) -> {(rung, draw): (rho, cell name or "", record)}
    sets: dict[tuple[str, str, int], dict[tuple[str, int], tuple[np.ndarray, str, dict[str, Any]]]] = {("union", "union", 0): {(c.rung, c.draw): (sources[c.name].rho, c.name, sources[c.name].record) for c in union_cells}}
    for fam, cs in plain_cells.items():
        sets[("plain", fam, 0)] = {(c.rung, c.draw): (sources[c.name].rho, c.name, sources[c.name].record) for c in cs}
        for c in cs:
            assert sources[c.name].record["matched_source_sha256"] == source_hash(U[(c.rung, c.draw)]), c.name

    def marginal(rung: str, k: int, replicate: int) -> tuple[np.ndarray, dict[str, Any]]:
        rho, meta = matched_random_source(n_on(U[(rung, k)], module_to_c, offsets), alive_vec, module_to_c, family="union", draw=k, master_seed=master_seed, alive_sha256=alive_sha,
                                          alive_run=run, offsets=offsets, weights=lam, replicate=replicate)
        assert n_on(rho, module_to_c, offsets) == n_on(U[(rung, k)], module_to_c, offsets), (rung, k, replicate)  # the count is the union's, matrix by matrix
        return rho, meta

    n_overflow = 0
    for rep, rungs in ((0, S7_RUNGS), (1, S7_REPLICATE_1_RUNGS)):
        sets[("marginal", "all", rep)] = {}
        for r in rungs:
            for k in range(draws):
                rho, meta = marginal(r, k, rep)
                n_overflow += len(meta["overflow"])
                sets[("marginal", "all", rep)][(r, k)] = (rho, "", {"control": meta, "source_sha256": source_hash(rho)})
    for rep in (0, 1):  # nested along the chain, as the plain control's are
        for k in range(draws):
            rr = [r for r in S7_RUNGS if (r, k) in sets[("marginal", "all", rep)]]
            for a, b in zip(rr[:-1], rr[1:]):
                assert np.all(sets[("marginal", "all", rep)][(a, k)][0] <= sets[("marginal", "all", rep)][(b, k)][0]), (rep, k, a, b)
    # ---- switched mass on E under the labels background: sigma_b(S) = |S| - (1/T) sum_{c in S} sum_t g_{b,t,c}
    N = g_sums_E.shape[0]
    m_c = 1.0 - g_sums_E.sum(axis=0) / float(N * SEQ_LEN)  # a set's mean sigma over E's texts is the sum of m_c over its members
    cols: list[np.ndarray] = []
    col_of: dict[tuple[Any, ...], int] = {}
    for key, by in sets.items():
        for (r, k), (rho, _, _) in by.items():
            col_of[(*key, r, k)] = len(cols)
            cols.append(rho)
            if key[0] != "union":
                col_of[(*key, r, k, "shared")] = len(cols)
                cols.append(rho & U[(r, k)])
    sig = sigma_from_sums(g_sums_E, np.stack(cols, axis=1))  # (N, K) float64, the existing machinery
    sig_mean = sig.mean(axis=0)
    for j, rho in enumerate(cols):  # the two routes to a set's mean switched mass agree
        assert abs(sig_mean[j] - m_c[rho].sum()) <= 1e-9 * max(1.0, abs(sig_mean[j])), (j, sig_mean[j], m_c[rho].sum())
    # ---- 1. composition, per rung and draw and pooled over draws
    comp_rows: list[dict[str, Any]] = []
    pooled_value: dict[tuple[Any, ...], dict[str, float]] = {}
    for key, by in sets.items():
        control, fam, rep = key
        for r in sorted({r for r, _ in by}, key=rung_order):
            members, sigs = [], []
            for k in range(draws):
                rho, name, rec = by[(r, k)]
                idx = np.flatnonzero(rho)
                s_mean = float(sig_mean[col_of[(*key, r, k)]])
                comp_rows.append({"control": control, "family": fam, "replicate": rep, "rung": r, "draw": k, **_member_stats(norms, usage, idx), "mean_sigma": s_mean,
                                  "n_not_alive": int((rho & ~alive_vec).sum()), "source_sha256": rec["source_sha256"], "cell": name})
                members.append(idx)
                sigs.append(s_mean)
            allm = np.concatenate(members)
            st = _member_stats(norms, usage, allm)
            comp_rows.append({"control": control, "family": fam, "replicate": rep, "rung": r, "draw": "pooled", **st, "mean_sigma": float(np.mean(sigs)),
                              "n_not_alive": int(sum((by[(r, k)][0] & ~alive_vec).sum() for k in range(draws))), "source_sha256": "", "cell": ""})
            pooled_value[(*key, r)] = {"mean_usage": st["mean_usage"], "mean_norm": st["mean_norm"], "mean_sigma": float(np.mean(sigs)), "n": st["n"]}
    composition = pd.DataFrame(comp_rows)
    # ---- 2. overlap of each control with the union, by count and by switched mass on E
    ov_rows: list[dict[str, Any]] = []
    for key, by in sets.items():
        control, fam, rep = key
        if control == "union":
            continue
        for (r, k), (rho, name, _) in sorted(by.items(), key=lambda kv: (rung_order(kv[0][0]), kv[0][1])):
            ju, js = col_of[("union", "union", 0, r, k)], col_of[(*key, r, k, "shared")]
            with np.errstate(divide="ignore", invalid="ignore"):
                per_text = sig[:, js] / sig[:, ju]
            ov_rows.append({"control": control, "family": fam, "replicate": rep, "rung": r, "draw": k, "n_named": int(U[(r, k)].sum()), "n_control": int(rho.sum()), "n_shared": int((rho & U[(r, k)]).sum()),
                            "overlap_count": float((rho & U[(r, k)]).sum() / U[(r, k)].sum()), "sigma_named": float(sig_mean[ju]), "sigma_shared": float(sig_mean[js]),
                            "overlap_mass": float(sig_mean[js] / sig_mean[ju]), "overlap_mass_mean_over_texts": float(np.nanmean(per_text)), "n_texts_sigma_named_zero": int((sig[:, ju] == 0).sum()), "cell": name})
    overlap = pd.DataFrame(ov_rows)
    by_rows: list[dict[str, Any]] = []
    for (control, fam, rep, r), t in overlap.groupby(["control", "family", "replicate", "rung"], sort=False):
        by_rows.append({"control": control, "family": fam, "replicate": rep, "rung": r, "n_draws": len(t),
                        "overlap_mass_pooled": float(t.sigma_shared.sum() / t.sigma_named.sum()),  # the named constant: total intersection mass over total named mass
                        "overlap_mass_mean_of_draw_ratios": float(t.overlap_mass.mean()), "overlap_mass_mean_over_texts": float(t.overlap_mass_mean_over_texts.mean()),
                        "overlap_count_pooled": float(t.n_shared.sum() / t.n_named.sum()), "overlap_count_mean_of_draw_ratios": float(t.overlap_count.mean()),
                        "overlap_mass_min_draw": float(t.overlap_mass.min()), "overlap_mass_max_draw": float(t.overlap_mass.max())})
    overlap_by_rung = pd.DataFrame(by_rows).sort_values(["control", "family", "replicate", "rung"], key=lambda s: s.map(rung_order) if s.name == "rung" else s).reset_index(drop=True)
    pair_rows = [{"rung": r, "draw_a": a, "draw_b": b, "n_a": int(U[(r, a)].sum()), "n_b": int(U[(r, b)].sum()), "n_shared": int((U[(r, a)] & U[(r, b)]).sum()),
                  "overlap_count_of_a": float((U[(r, a)] & U[(r, b)]).sum() / U[(r, a)].sum()), "jaccard": float((U[(r, a)] & U[(r, b)]).sum() / (U[(r, a)] | U[(r, b)]).sum())}
                 for r in S7_RUNGS for a in range(draws) for b in range(draws) if a != b]
    pairwise = pd.DataFrame(pair_rows)
    # ---- 3. the usage distribution of the alive set (and of the sampler's candidates beside it)
    use_rows = []
    for name, sel in (("alive", alive_vec), ("candidates (usage > 0)", candidates)):
        u = usage[sel]
        use_rows.append({"set": name, "n": int(sel.sum()), **{f"p{p}": float(np.percentile(u, p)) for p in range(0, 101, 10)}, "mean": float(u.mean()), "n_above_0.1": int((u > 0.1).sum()),
                         "n_above_0.5": int((u > 0.5).sum()), "n_above_0.9": int((u > 0.9).sum()), "n_at_clip_or_above": int((u >= 1.0 - 1.0 / (2.0 * d_unif.n_positions)).sum())})
    usage_distribution = pd.DataFrame(use_rows)
    # ---- 4. the sampler's own spread over n_seeds label-only seeds, and the gate on its bias
    log(f"[pre-reads s7] marginal: sets, composition, overlap in {time.time() - t0:.0f} s; the sampler under {n_seeds} seeds")
    seed_rows: list[dict[str, Any]] = []
    for rep in range(n_seeds):
        for r in S7_RUNGS:
            tot_u = tot_n = tot_m = 0.0
            count = 0
            for k in range(draws):
                rho = sets[("marginal", "all", rep)][(r, k)][0] if (rep in (0, 1) and (r, k) in sets[("marginal", "all", rep)]) else marginal(r, k, rep)[0]
                tot_u += float(usage[rho].sum())
                tot_n += float(norms[rho].sum())
                tot_m += float(m_c[rho].sum())
                count += int(rho.sum())
            seed_rows.append({"replicate": rep, "rung": r, "n": count, "mean_usage": tot_u / count, "mean_norm": tot_n / count, "mean_sigma": tot_m / draws, "sigma_per_member": tot_m / count})
    seeds = pd.DataFrame(seed_rows)
    gate_rows: list[dict[str, Any]] = []
    for r in S7_RUNGS:
        t = seeds[seeds.rung == r]
        for stat, (lo, hi) in S7_GATE_BOUNDS.items():
            d = t[stat].to_numpy(np.float64)
            uv = pooled_value[("union", "union", 0, r)][stat]
            ratio = float(d.mean() / uv)
            rep1 = float(t[t.replicate == 1][stat].iloc[0]) if n_seeds > 1 else float("nan")
            gate_rows.append({"rung": r, "statistic": stat, "gated": r in S7_GATE_RUNGS, "union_value": uv, "plain_value": pooled_value[("plain", "union", 0, r)][stat], "seeds_mean": float(d.mean()), "seeds_sd": float(d.std(ddof=1)),
                              "seeds_min": float(d.min()), **{f"seeds_p{str(p).replace('.', '_')}": float(np.percentile(d, p)) for p in (2.5, 5, 25, 50, 75, 95, 97.5)}, "seeds_max": float(d.max()),
                              "ratio_seeds_mean_to_union": ratio, "bound_low": lo, "bound_high": hi, "within_bounds": bool(lo <= ratio <= hi), "ratio_plain_to_union": float(pooled_value[("plain", "union", 0, r)][stat] / uv),
                              "union_percentile_in_seeds": percentile_of(uv, d), "replicate_0_value": float(t[t.replicate == 0][stat].iloc[0]), "replicate_0_percentile": percentile_of(float(t[t.replicate == 0][stat].iloc[0]), d),
                              "replicate_1_value": rep1, "replicate_1_percentile": percentile_of(rep1, d) if n_seeds > 1 else float("nan")})
    gate = pd.DataFrame(gate_rows)
    for rep in (0, 1):  # the realized replicates' rows of the seed table are the composition table's pooled rows
        for r in (S7_RUNGS if rep == 0 else S7_REPLICATE_1_RUNGS):
            if rep < n_seeds:
                row = seeds[(seeds.replicate == rep) & (seeds.rung == r)].iloc[0]
                pv = pooled_value[("marginal", "all", rep, r)]
                assert abs(row["mean_usage"] - pv["mean_usage"]) <= 1e-12 * max(1.0, pv["mean_usage"]) and abs(row["mean_sigma"] - pv["mean_sigma"]) <= 1e-9 * max(1.0, pv["mean_sigma"]) and int(row["n"]) == pv["n"]
    gated = gate[gate.gated]
    # ---- the realized eight rung-1 positions among 200 sets of eight real pool positions
    real = real_position_sets(d_unif, norms, usage, draws=draws, master_seed=master_seed)
    r0 = real[real.realized].iloc[0]
    pv1 = pooled_value[("union", "union", 0, "1")]
    assert int(r0["n"]) == pv1["n"] and abs(r0["mean_usage"] - pv1["mean_usage"]) <= 1e-12 * max(1.0, pv1["mean_usage"]) and abs(r0["mean_norm"] - pv1["mean_norm"]) <= 1e-12 * max(1.0, pv1["mean_norm"]), "set 0 is the realized union at rung 1"
    others = real[~real.realized]
    real_summary = {"n_sets": int(len(others)), "draws_per_set": draws, "seed_pattern": [master_seed, "posperm", "D_unif", "<draw>"], "draws_used": [draws, int(others.first_draw.max()) + draws - 1],
                    **{stat: {"realized": float(r0[stat]), "sets_mean": float(others[stat].mean()), "sets_sd": float(others[stat].std(ddof=1)), "sets_min": float(others[stat].min()), "sets_p5": float(np.percentile(others[stat], 5)),
                              "sets_p50": float(np.percentile(others[stat], 50)), "sets_p95": float(np.percentile(others[stat], 95)), "sets_max": float(others[stat].max()),
                              "realized_percentile": percentile_of(float(r0[stat]), others[stat].to_numpy(np.float64))} for stat in ("mean_usage", "mean_norm", "n")}}
    summary = {"run": run, "real_position_sets": real_summary, "draws": draws, "n_seeds": n_seeds, "tau": S7_TAU, "rungs": list(S7_RUNGS), "n_candidates": int(candidates.sum()), "n_alive": int(alive_vec.sum()),
               "n_candidates_not_alive": int((candidates & ~alive_vec).sum()), "n_alive_not_candidates": int((alive_vec & ~candidates).sum()), "n_positions": int(d_unif.n_positions),
               "usage_sha256": key_sha256(usage), "rates_sha256": key_sha256(lam), "n_marginal_overflows": int(n_overflow),
               "gate": {"bounds": {k: list(v) for k, v in S7_GATE_BOUNDS.items()}, "rungs": list(S7_GATE_RUNGS), "pass": bool(gated.within_bounds.all()),
                        "failures": [f"rung {r} {s}: {x:.4f}" for r, s, x, ok in zip(gated.rung, gated.statistic, gated.ratio_seeds_mean_to_union, gated.within_bounds) if not ok]},
               "decisive_rule": {"max_overlap_mass_pooled": S7_DECISIVE_MAX_OVERLAP, "replicate": 0,
                                 "by_family": {"union_r0 (primary, rungs 1, 2, 2a, 2b, 3)": decisive_rungs(overlap_by_rung, family="union"),
                                               "union_uniform and soft_erase (rungs 1, 2, 3)": decisive_rungs(overlap_by_rung, family="soft_erase")}},
               "seconds": time.time() - t0}
    log(f"[pre-reads s7] marginal: done in {summary['seconds']:.0f} s; gate pass {summary['gate']['pass']}; decisive {summary['decisive_rule']['by_family']}")
    return {"marginal_composition": composition, "marginal_overlap_per_draw": overlap, "marginal_overlap_by_rung": overlap_by_rung, "marginal_pairwise_real_draws": pairwise,
            "usage_distribution": usage_distribution, "marginal_sampler_seeds": seeds, "marginal_gate": gate, "marginal_real_position_sets": real}, summary


# ----------------------------------------------------------------------------- the code-leaning group

from vpd_audit.code_leaning import (  # noqa: E402  (one implementation for the pre-read and the cells; re-exported here for the tests)
    CL_FLOOR_ROWS,
    CL_FLOOR_USAGE,
    CL_GROUP,
    CL_TAU,
    CL_THRESHOLDS,
    CL_WIDE,
    CL_WINDOW,
    code_leaning_sets,
    leaning_group,
    leaning_table,
    per_document_counts,
    twins_source,
    usage_twins,
)

CL_N_SHUFFLES = 200
CL_CLEAR_SHARE = 0.10
CL_NONE_SHARE = 0.02
CL_NULL_FRACTION = 0.2  # a clear group needs the null's 95th percentile below a fifth of M(G_0.9)
CL_HIST_BINS = 20
CL_CONTROL_TOLERANCE = 0.10
CL_CONTROL_GATE_MIN_MEMBERS = 64  # the control's gate is read at every non-descriptive rung of at least 64 members
CL_STRAY_ROWS = 10


def existence_verdict(share: float, mass: float, null_p95: float) -> str:
    """The existence rule, fixed before any prose usage rate was computed: clear if M(G_0.9) is at least 10 percent of the alive
    set's code-firing mass and the shuffle null's 95th percentile is below a fifth of M(G_0.9); none if the share is under 2
    percent; marginal otherwise."""
    if share < CL_NONE_SHARE:
        return "none"
    if share >= CL_CLEAR_SHARE and null_p95 < CL_NULL_FRACTION * mass:
        return "clear"
    return "marginal"


def shuffle_null(counts_a: np.ndarray, counts_b: np.ndarray, *, threshold: float = CL_GROUP, n_shuffles: int = CL_N_SHUFFLES, master_seed: int = 0) -> pd.DataFrame:
    """The null for the tail: pool the documents of the two pools, shuffle the code/prose label over documents
    `n_shuffles` times from one generator seeded (master, "shuffle", "code_leaning"), and recompute M(G_threshold) toward the
    pseudo-code half each time, from the per-document counts (columns: the alive set). Row -1 is the true labelling through
    the same code, the observed value."""
    from vpd_audit.masks import seed_from_tuple

    n_a, n_b = counts_a.shape[0], counts_b.shape[0]
    counts = np.concatenate([counts_a, counts_b], axis=0)
    present = counts > 0
    rng = np.random.default_rng(seed_from_tuple((master_seed, "shuffle", "code_leaning")))
    rows = []
    for i in range(-1, n_shuffles):
        perm = np.arange(n_a + n_b) if i < 0 else rng.permutation(n_a + n_b)
        a, b = perm[:n_a], perm[n_a:]
        t = leaning_table(counts[a].sum(axis=0, dtype=np.int64), present[a].sum(axis=0), counts[b].sum(axis=0, dtype=np.int64), n_a * SEQ_LEN, n_b * SEQ_LEN)
        G = leaning_group(t, threshold)
        total = float(t["u_a"].sum())
        mass = float(t["u_a"][G].sum())
        rows.append({"shuffle": i, "n_members": int(G.sum()), "mass": mass, "total_mass": total, "share": mass / total if total else float("nan"), "n_true_code_documents_in_pseudo_code": int((a < n_a).sum())})
    return pd.DataFrame(rows)


def code_leaning_pre_read(code: Cache, prose: Cache, d_unif: Cache, e_lab: Cache, strata: list[str], alive_vec: np.ndarray, alive_sha: str, norms: np.ndarray, run: str, *, draws: int = 8,
                          master_seed: int = 0, n_shuffles: int = CL_N_SHUFFLES, positive_stratum: str = "Github", group_threshold: float = CL_GROUP, wide_threshold: float = CL_WIDE,
                          force_chain: bool = False, log: Any = print) -> tuple[dict[str, pd.DataFrame], dict[str, Any]]:
    """The code-leaning group's label-only pre-read. The label-only table over the alive set; the groups G_s and their
    prose-leaning mirror images; the histogram of s weighted by u_code; the shuffle null; the existence rule; the stray-code
    diagnostic; and, if the group is clear or marginal, the chain, its usage-matched control (nearest-neighbour twins, with
    their gate), and the testability of both on E_lab's strata. `group_threshold`, `wide_threshold`, and `force_chain` are
    the ones fixed in advance (0.9, 0.75, no) on the paper's model; the stand-in, where the rule finds no group, is given lower thresholds and a forced
    chain so that its dry run exercises the cells, and the summary records it."""
    from vpd_audit.sources import usage_bins

    t0 = time.time()
    module_to_c, offsets, n_sub = dict(d_unif.module_to_c), d_unif.offsets, d_unif.n_sub
    assert code.n_sub == prose.n_sub == e_lab.n_sub == n_sub and code.offsets == prose.offsets == offsets and alive_vec.shape == norms.shape == (n_sub,)
    modules = np.empty(n_sub, dtype=object)
    within = np.zeros(n_sub, dtype=np.int64)
    for k in sorted(module_to_c):
        modules[offsets[k] : offsets[k] + module_to_c[k]] = k
        within[offsets[k] : offsets[k] + module_to_c[k]] = np.arange(module_to_c[k])
    # ---- the table, over the alive set
    sets = code_leaning_sets(code, prose, alive_vec, group_threshold=group_threshold, wide_threshold=wide_threshold, master_seed=master_seed)
    alive_idx, c_code, c_prose, n_code, n_prose, rows_code, rows_prose = sets.alive_idx, sets.c_code, sets.c_prose, sets.n_code, sets.n_prose, sets.rows_code, sets.rows_prose
    toward_code, toward_prose = sets.toward_code, sets.toward_prose
    for cache, n in ((code, n_code), (prose, n_prose)):  # the cells' usage arithmetic is the pre-reads'
        assert np.array_equal(n.astype(np.float64) / cache.n_positions, pool_usage(cache, CL_TAU)[alive_idx])
    u_code, u_prose, s = toward_code["u_a"], toward_code["u_b"], toward_code["selectivity"]
    usage_unif = pool_usage(d_unif, CL_TAU)
    bins, n_bins = usage_bins(usage_unif, alive_vec, module_to_c, offsets)
    norms_a = norms[alive_idx]
    total_code, total_prose = float(u_code.sum()), float(u_prose.sum())
    default_thresholds = (group_threshold, wide_threshold) == (CL_GROUP, CL_WIDE)
    groups: dict[str, tuple[str, np.ndarray]] = {}
    for thr in CL_THRESHOLDS:
        groups[f"G_{thr:g}"] = ("code", leaning_group(toward_code, thr))
    groups["strict code (code-named, no prose position), no floor"] = ("code", (n_code > 0) & (n_prose == 0))
    groups["strict code, floor passed"] = ("code", toward_code["floor"] & (n_prose == 0))
    for thr in CL_THRESHOLDS:
        groups[f"prose-leaning, s <= {1 - thr:.2f}"] = ("prose", leaning_group(toward_prose, thr))
    groups["strict prose (prose-named, no code position), no floor"] = ("prose", (n_prose > 0) & (n_code == 0))
    groups["strict prose, floor passed"] = ("prose", toward_prose["floor"] & (n_code == 0))
    if not default_thresholds:  # the stand-in's forced group and wide set, beside the ones fixed in advance
        groups[f"forced group, s >= {group_threshold:g}"] = ("code", sets.group)
        groups[f"forced wide set, s >= {wide_threshold:g}"] = ("code", sets.wide)
    table = pd.DataFrame({"index": alive_idx, "module": modules[alive_idx].astype(str), "c": within[alive_idx], "n_code": n_code, "n_prose": n_prose, "rows_code": rows_code, "rows_prose": rows_prose,
                          "u_code": u_code, "u_prose": u_prose, "selectivity": s, "floor_code": toward_code["floor"], "floor_prose": toward_prose["floor"], "weight_norm": norms_a,
                          "usage_unif": usage_unif[alive_idx], "usage_bin": bins[alive_idx], **{f"in_G_{thr:g}": groups[f"G_{thr:g}"][1] for thr in CL_THRESHOLDS}})
    if not default_thresholds:
        table["in_forced_group"], table["in_forced_wide"] = sets.group, sets.wide
    g_rows, gm_rows = [], []
    for name, (side, G) in groups.items():
        u, total = (u_code, total_code) if side == "code" else (u_prose, total_prose)
        g_rows.append({"group": name, "toward": side, "n_members": int(G.sum()), "firing_mass": float(u[G].sum()), "share_of_alive_firing_mass": float(u[G].sum() / total), "alive_firing_mass": total,
                       "mean_weight_norm": float(norms_a[G].mean()) if G.any() else float("nan"), "mean_usage_unif": float(usage_unif[alive_idx][G].mean()) if G.any() else float("nan"),
                       "min_selectivity": float(np.nanmin(np.where(G, s, np.nan))) if G.any() else float("nan"), "max_selectivity": float(np.nanmax(np.where(G, s, np.nan))) if G.any() else float("nan")})
        per = pd.Series(modules[alive_idx][G].astype(str)).value_counts()
        gm_rows.append({"group": name, **{k: int(per.get(k, 0)) for k in sorted(module_to_c)}, "total": int(G.sum())})
    group_table, group_per_matrix = pd.DataFrame(g_rows), pd.DataFrame(gm_rows)
    # ---- the histogram of s weighted by u_code (data; the figure is drawn from it)
    defined = np.isfinite(s)
    edges = np.arange(CL_HIST_BINS + 1, dtype=np.float64) / CL_HIST_BINS  # k / 20 correctly rounded, as a ratio of counts on an edge is
    which = np.clip(np.digitize(np.where(defined, s, 0.0), edges[1:-1], right=False), 0, CL_HIST_BINS - 1)  # [lo, hi), the last bin closed at 1
    hist = pd.DataFrame({"bin_low": edges[:-1], "bin_high": edges[1:],
                         "n_members": [int((defined & (which == j)).sum()) for j in range(CL_HIST_BINS)], "weight_u_code": [float(u_code[defined & (which == j)].sum()) for j in range(CL_HIST_BINS)],
                         "n_members_floor_passed": [int((defined & toward_code["floor"] & (which == j)).sum()) for j in range(CL_HIST_BINS)],
                         "weight_u_code_floor_passed": [float(u_code[defined & toward_code["floor"] & (which == j)].sum()) for j in range(CL_HIST_BINS)]})
    hist["share_of_alive_code_firing_mass"] = hist["weight_u_code"] / total_code
    # ---- the null for the tail, and the existence rule
    log(f"[pre-reads s7] code-leaning: the table and groups in {time.time() - t0:.0f} s; the shuffle null ({n_shuffles})")
    null = shuffle_null(c_code, c_prose, threshold=group_threshold, n_shuffles=n_shuffles, master_seed=master_seed)
    G90, G75 = sets.group, sets.wide
    mass, share = float(u_code[G90].sum()), float(u_code[G90].sum() / total_code)
    observed = null[null.shuffle == -1].iloc[0]
    assert observed["mass"] == mass and int(observed["n_members"]) == int(G90.sum()), "the null's code path returns the observed group under the true labels"
    nm = null[null.shuffle >= 0]["mass"].to_numpy(np.float64)
    null_mean, null_p95 = float(nm.mean()), float(np.percentile(nm, 95))
    verdict = existence_verdict(share, mass, null_p95)
    existence = {"group": f"G_{group_threshold:g}", "n_members": int(G90.sum()), "mass": mass, "alive_code_firing_mass": total_code, "share": share, "null_mean": null_mean, "null_p95": null_p95, "null_max": float(nm.max()),
                 "a_fifth_of_mass": CL_NULL_FRACTION * mass, "null_p95_below_a_fifth": bool(null_p95 < CL_NULL_FRACTION * mass), "share_at_least_10_percent": bool(share >= CL_CLEAR_SHARE),
                 "share_under_2_percent": bool(share < CL_NONE_SHARE), "verdict": verdict, "n_shuffles": n_shuffles, "null_mean_members": float(null[null.shuffle >= 0]["n_members"].mean())}
    # ---- the stray-code diagnostic, descriptive only: where in the prose pool the group's prose firings fall
    firing = G90 & (n_prose > 0)
    per_row = c_prose[:, firing].sum(axis=1, dtype=np.int64)
    top = np.lexsort((np.arange(per_row.size), -per_row))[:CL_STRAY_ROWS]
    tot = int(per_row.sum())
    stray_rows = pd.DataFrame({"rank": np.arange(1, top.size + 1), "prose_row": top, "firings_of_the_group": per_row[top], "share_of_the_groups_prose_firings": per_row[top] / tot if tot else np.nan,
                               "n_members_firing_in_row": (c_prose[top][:, firing] > 0).sum(axis=1)})
    cp = np.sort(c_prose[:, firing], axis=0)[::-1]  # per member, its prose firings per row, largest first
    member_share = cp[:CL_STRAY_ROWS].sum(axis=0) / np.maximum(cp.sum(axis=0), 1)
    stray_members = pd.DataFrame({"index": alive_idx[firing], "module": modules[alive_idx][firing].astype(str), "n_code": n_code[firing], "n_prose": n_prose[firing], "rows_prose": rows_prose[firing],
                                  "selectivity": s[firing], "share_of_prose_firings_in_own_top_10_rows": member_share})
    stray = {"n_members_firing_in_prose": int(firing.sum()), "n_members": int(G90.sum()), "prose_firings_of_the_group": tot, "group_share_in_its_top_10_rows": float(per_row[top].sum() / tot) if tot else float("nan"),
             "per_member_share_in_own_top_10_rows": {"mean": float(member_share.mean()), "median": float(np.median(member_share)), "q1": float(np.percentile(member_share, 25)), "q3": float(np.percentile(member_share, 75)),
                                                     "fraction_at_least_0.5": float((member_share >= 0.5).mean()), "fraction_at_least_0.9": float((member_share >= 0.9).mean())} if firing.any() else {},
             "n_prose_rows": int(prose.n_sequences), "uniform_share_of_10_rows": CL_STRAY_ROWS / prose.n_sequences}
    tables = {"code_leaning_table": table, "code_leaning_groups": group_table, "code_leaning_groups_per_matrix": group_per_matrix, "code_leaning_histogram": hist, "code_leaning_null": null,
              "code_leaning_stray_code_rows": stray_rows, "code_leaning_stray_code_members": stray_members}
    summary: dict[str, Any] = {"run": run, "tau": CL_TAU, "n_alive": int(alive_vec.sum()), "n_positions_code": int(code.n_positions), "n_positions_prose": int(prose.n_positions), "n_rows_code": int(code.n_sequences),
                               "n_rows_prose": int(prose.n_sequences), "n_alive_with_defined_selectivity": int(defined.sum()), "n_alive_floor_code": int(toward_code["floor"].sum()), "n_alive_floor_prose": int(toward_prose["floor"].sum()),
                               "existence": existence, "stray_code": stray, "usage_bins_per_matrix": n_bins,
                               "thresholds": {"group": float(group_threshold), "wide": float(wide_threshold), "default_thresholds": bool(default_thresholds), "chain_forced": bool(force_chain)}}
    log(f"[pre-reads s7] code-leaning: existence rule returns {verdict!r} (share {share:.4f}, M {mass:.4f}, null p95 {null_p95:.5f}); {time.time() - t0:.0f} s")
    if (verdict == "none" and not force_chain) or sets.n_group == 0:
        summary["seconds"] = time.time() - t0
        return tables, summary
    # ---- the chain: the wide set ordered by s descending, ties by u_code descending, then the seeded tie permutation; the group is a prefix
    order, ladder, wide_full, s_full, u_full = sets.order, sets.ladder, sets.wide_full, sets.selectivity_full, sets.u_code_full
    n90, n75 = sets.n_group, sets.n_wide
    strata_arr = np.asarray(strata)
    assert strata_arr.size == e_lab.n_sequences
    strata_groups = {"all": None, **{x: (strata_arr == x) for x in sorted(set(strata))}, "other": strata_arr != positive_stratum}
    chain_rows, ctl_rows, ctl_summary, short_rows, test_rows = [], [], [], [], []

    def testability(kind: str, size: int, descriptive: bool, sets_: list[np.ndarray]) -> None:
        per = [first_touched_from_cache(e_lab, S, TAU_QS_LOOP) for S in sets_]
        for tq in TAU_QS_LOOP:
            for sname, mask in strata_groups.items():
                sts = [t_star_stats(ft[tq][0] if mask is None else ft[tq][0][mask]) for ft in per]
                contributing, clean = [x["n_contributing"] for x in sts], [x["clean_prefix_fraction"] for x in sts]
                test_rows.append({"chain": kind, "rung_size": size, "descriptive": descriptive, "tau_q": f"tau_q{tq:g}", "stratum": sname, "n_draws": len(sts), "n_sequences": sts[0]["n"],
                                  "mean_n_contributing": float(np.mean(contributing)), "min_n_contributing": int(np.min(contributing)), "mean_clean_prefix_fraction": float(np.mean(clean)),
                                  "fraction_never_touched": float(np.mean([x["fraction_equal_T"] for x in sts])), "floor_met": bool(np.mean(contributing) >= FLOOR_CONTRIBUTING and np.mean(clean) >= FLOOR_CLEAN_FRACTION)})

    # the control: per draw, the twin of every member of the chain, once; a rung's control is its members' twins
    twins, twin_meta = {}, {}
    for k in range(draws):
        twins[k], twin_meta[k] = usage_twins(order, wide_full, alive_vec, usage_unif, module_to_c, draw=k, master_seed=master_seed, offsets=offsets)
    twin_table = pd.DataFrame([{"draw": k, "position_in_chain": i, "member": int(order[i]), "member_module": str(modules[order[i]]), "twin": int(twins[k][i]), "member_usage_unif": float(usage_unif[order[i]]),
                                "twin_usage_unif": float(usage_unif[twins[k][i]]) if twins[k][i] >= 0 else float("nan"), "member_weight_norm": float(norms[order[i]]),
                                "twin_weight_norm": float(norms[twins[k][i]]) if twins[k][i] >= 0 else float("nan")} for k in range(draws) for i in range(order.size)])
    prev = np.zeros(n_sub, bool)
    prev_ctl = [np.zeros(n_sub, bool) for _ in range(draws)]
    for size, descriptive in ladder:
        named = sets.named(size)
        assert np.all(prev <= named)
        prev = named
        members = order[:size]
        g_norm, g_usage = float(norms[members].mean()), float(usage_unif[members].mean())
        chain_rows.append({"rung_size": size, "descriptive": descriptive, "min_selectivity": float(s_full[members].min()), "code_firing_mass": float(u_full[members].sum()),
                           "share_of_alive_code_firing_mass": float(u_full[members].sum() / total_code), "mean_weight_norm": g_norm, "mean_usage_unif": g_usage,
                           "n_matrices": int(len({modules[i] for i in members})), "source_sha256": source_hash(named)})
        ctl_sets, pair_ratios, n_zero = [], [], 0
        for k in range(draws):
            rho = twins_source(twins[k], size, n_sub)
            assert np.all(prev_ctl[k] <= rho) and not (rho & wide_full).any()  # nested along the chain, outside G_0.75
            prev_ctl[k] = rho
            ctl_sets.append(rho)
            tw = twins[k][:size]
            ok = (tw >= 0) & (usage_unif[members] > 0)
            n_zero += int(((tw >= 0) & (usage_unif[members] == 0)).sum())
            ratios = usage_unif[tw[ok]] / usage_unif[members[ok]]
            pair_ratios.append(ratios)
            short = int((tw < 0).sum())
            ctl_rows.append({"rung_size": size, "descriptive": descriptive, "draw": k, "n_control": int(rho.sum()), "mean_weight_norm": float(norms[rho].mean()), "mean_usage_unif": float(usage_unif[rho].mean()),
                             "median_pair_usage_ratio": float(np.median(ratios)) if ratios.size else float("nan"), "shortfall": short, "overlap_with_group": int((rho & named).sum()), "source_sha256": source_hash(rho)})
            if short:
                per_mod = pd.Series(modules[members[tw < 0]].astype(str)).value_counts()
                short_rows += [{"rung_size": size, "draw": k, "module": str(mod), "shortfall": int(v)} for mod, v in per_mod.items()]
        these = [r for r in ctl_rows if r["rung_size"] == size]
        c_norm, c_usage = float(np.mean([r["mean_weight_norm"] for r in these])), float(np.mean([r["mean_usage_unif"] for r in these]))
        all_ratios = np.concatenate(pair_ratios) if pair_ratios else np.zeros(0)
        judged = bool((not descriptive) and size >= CL_CONTROL_GATE_MIN_MEMBERS)
        norm_off, usage_off = bool(abs(c_norm / g_norm - 1.0) > CL_CONTROL_TOLERANCE), bool(g_usage > 0 and abs(c_usage / g_usage - 1.0) > CL_CONTROL_TOLERANCE)
        ctl_summary.append({"rung_size": size, "descriptive": descriptive, "judged_by_the_gate": judged, "group_mean_weight_norm": g_norm, "control_mean_weight_norm": c_norm, "norm_ratio_control_to_group": c_norm / g_norm,
                            "group_mean_usage_unif": g_usage, "control_mean_usage_unif": c_usage, "usage_ratio_control_to_group": c_usage / g_usage if g_usage else float("nan"),
                            "median_pair_usage_ratio": float(np.median(all_ratios)) if all_ratios.size else float("nan"), "n_pairs_member_usage_zero": n_zero,
                            "norm_off_by_more_than_10_percent": norm_off, "usage_off_by_more_than_10_percent": usage_off, "gate_pass": (not (norm_off or usage_off)) if judged else None,
                            "mean_n_control": float(np.mean([r["n_control"] for r in these])), "total_shortfall": int(sum(r["shortfall"] for r in these))})
        testability("group", size, descriptive, [named])
        testability("control", size, descriptive, ctl_sets)
        log(f"[pre-reads s7] code-leaning: rung {size}{' (descriptive)' if descriptive else ''} with its {draws} controls and their testability; {time.time() - t0:.0f} s")
    tables.update({"code_leaning_chain": pd.DataFrame(chain_rows), "code_leaning_control_per_draw": pd.DataFrame(ctl_rows), "code_leaning_control_by_rung": pd.DataFrame(ctl_summary),
                   "code_leaning_control_twins": twin_table,
                   "code_leaning_control_shortfall": pd.DataFrame(short_rows, columns=["rung_size", "draw", "module", "shortfall"]),
                   "code_leaning_testability": pd.DataFrame(test_rows)})
    judged_rows = [r for r in ctl_summary if r["judged_by_the_gate"]]
    summary["chain"] = {"n_group": n90, "n_wide": n75, "ladder": [[int(a), bool(b)] for a, b in ladder], "order_sha256": key_sha256(order.astype(np.float64)),
                        "control": {"sampler": "usage_nearest", "window": CL_WINDOW, "seed_pattern": twin_meta[0]["seed_pattern"] if twin_meta else None, "n_candidates": int((alive_vec & ~wide_full).sum())},
                        "control_gate": {"rule": "at every non-descriptive rung of at least 64 members the control's mean usage and mean weight norm, as a mean over the draws, lie within 10 percent of the group's",
                                         "rungs_judged": [r["rung_size"] for r in judged_rows], "pass": bool(all(r["gate_pass"] for r in judged_rows)) if judged_rows else None,
                                         "failures": [r["rung_size"] for r in judged_rows if not r["gate_pass"]]},
                        "rungs_with_norm_off": [r["rung_size"] for r in ctl_summary if r["norm_off_by_more_than_10_percent"]], "rungs_with_usage_off": [r["rung_size"] for r in ctl_summary if r["usage_off_by_more_than_10_percent"]],
                        "rungs_with_shortfall": sorted({r["rung_size"] for r in short_rows})}
    summary["seconds"] = time.time() - t0
    return tables, summary


# ----------------------------------------------------------------------------- the runner, the summary, and the local finishing step

S7_DIR_NAME = "s7"


S7_STALE_FILES = ("code_leaning_control_overflow.csv",)  # an earlier bin-based control recorded overflow; the nearest-neighbour twins have none


def run_pre_reads_s7(run: str, out_dir: Path, *, draws: int = 8, inputs: PreReadInputs | None = None, n_seeds: int = S7_N_SEEDS, n_shuffles: int = CL_N_SHUFFLES, group_threshold: float = CL_GROUP,
                     wide_threshold: float = CL_WIDE, force_chain: bool = False, log: Any = print) -> dict[str, Any]:
    """The tier-4 label-only pre-reads, where the caches live: the marginal control's pre-read and the code-leaning table, into
    `out_dir`, which must be a directory named s7 (under <pre_reads>/<run>/): no existing pre-reads file is written. If the
    parent directory holds the run's pre-reads manifest, the alive vector's and the weight norms' hashes are asserted equal
    to it, so the sets and keys here are the ones the grid used."""
    from vpd_audit.artifacts import load_component_model
    from vpd_audit.donors import donors_dir
    from vpd_audit.weight_norms import weight_norms

    t_all = time.time()
    out_dir = Path(out_dir)
    assert out_dir.name == S7_DIR_NAME, f"the tier-4 pre-reads write into a directory named {S7_DIR_NAME!r} only, not {out_dir}"
    inp = inputs or paper_inputs(run, draws)
    out_dir.mkdir(parents=True, exist_ok=True)

    def load(name: str) -> tuple[Cache, dict[str, Any]]:
        with open(donors_dir() / f"{name}.json") as f:
            meta = json.load(f)
        return Cache.load(name), {"name": name, "set_name": meta.get("set_name"), "set_hash": meta.get("set_hash"), "n_sequences": int(meta["n_sequences"]), "nnz": int(meta["nnz"]), "sha256": meta["sha256"]}

    cache_records: dict[str, Any] = {}
    d_unif, cache_records["D_unif"] = load(f"{inp.pool_map['D_unif']}_{run}")
    alive_vec = np.load(donors_dir() / f"alive_{inp.pool_map['D_unif']}_{run}.npy")
    alive_sha = source_hash(alive_vec)
    t_m = time.time()
    model = load_component_model(run, "cpu")
    norms, norms_meta = weight_norms(model)
    del model
    log(f"[pre-reads s7] {run}: weight norms on CPU, sha256 {norms_meta['sha256'][:16]}, in {time.time() - t_m:.0f} s; alive {int(alive_vec.sum())}, sha256 {alive_sha[:16]}")
    checked: dict[str, Any] = {"pre_reads_manifest": None}
    parent_manifest = out_dir.parent / "manifest.json"
    if parent_manifest.is_file():
        with open(parent_manifest) as f:
            pm = json.load(f)
        assert pm["alive_sha256"] == alive_sha, "the alive vector is not the one the run's pre-reads used"
        assert pm["weight_norms"] is None or pm["weight_norms"]["sha256"] == norms_meta["sha256"], "the weight norms are not the ones the run's pre-reads used"
        checked = {"pre_reads_manifest": str(parent_manifest), "alive_sha256_equal": True, "weight_norms_sha256_equal": pm["weight_norms"] is not None, "pre_reads_commit": pm.get("commits", {}).get("project")}
    # ---- the marginal control (E's per-sequence sums are freed before the domain caches are loaded)
    e_cache, cache_records["E"] = load(f"{inp.set_map['E']}_{run}")
    g_sums = per_sequence_g_sums(e_cache)
    del e_cache
    tables, marginal_summary = marginal_pre_read(d_unif, g_sums, alive_vec, alive_sha, norms, run, draws=inp.draws, master_seed=inp.master_seed, n_seeds=n_seeds, log=log)
    del g_sums
    # ---- the code-leaning group
    code, cache_records["D_code"] = load(f"{inp.pool_map['D_code']}_{run}")
    prose, cache_records["D_prose"] = load(f"{inp.pool_map['D_prose']}_{run}")
    e_lab, cache_records["E_lab"] = load(f"{inp.set_map['E_lab']}_{run}")
    with open(env.SETS_DIR / inp.strata_file) as f:
        strata = json.load(f)["strata"]
    cl_tables, cl_summary = code_leaning_pre_read(code, prose, d_unif, e_lab, strata, alive_vec, alive_sha, norms, run, draws=inp.draws, master_seed=inp.master_seed, n_shuffles=n_shuffles,
                                                  positive_stratum=inp.positive_stratum, group_threshold=group_threshold, wide_threshold=wide_threshold, force_chain=force_chain, log=log)
    tables.update(cl_tables)
    for name in S7_STALE_FILES:
        if (out_dir / name).is_file():
            (out_dir / name).unlink()
    for name, df in tables.items():
        df.to_csv(out_dir / f"{name}.csv", index=False)
    summary = {"run": run, "marginal": marginal_summary, "code_leaning": cl_summary}
    with open(out_dir / "summary.json", "w") as f:
        json.dump(summary, f, indent=2, sort_keys=True, default=str)
    text = format_pre_reads_s7(summary, tables)
    with open(out_dir / "summary.md", "w") as f:
        f.write(text + "\n")
    manifest = {"run": run, "draws": inp.draws, "master_seed": inp.master_seed, "n_seeds": n_seeds, "n_shuffles": n_shuffles, "commits": code_commits(), "seconds": time.time() - t_all, "caches": cache_records,
                "alive_sha256": alive_sha, "weight_norms": {"sha256": norms_meta["sha256"], "definition": norms_meta["definition"]}, "strata_file": inp.strata_file, "positive_stratum": inp.positive_stratum,
                "checked_against": checked, "tables": {name: {"rows": int(len(df)), "columns": list(df.columns)} for name, df in tables.items()},
                "files": sorted({p.name for p in out_dir.iterdir() if p.is_file()} | {"manifest.json"})}
    with open(out_dir / "manifest.json", "w") as f:
        json.dump(manifest, f, indent=2, sort_keys=True, default=str)
    log(text)
    log(f"[pre-reads s7] done in {time.time() - t_all:.0f} s -> {out_dir}")
    return {"run": run, "seconds": time.time() - t_all, "gate_pass": marginal_summary["gate"]["pass"], "decisive": marginal_summary["decisive_rule"]["by_family"], "existence": cl_summary["existence"]["verdict"],
            "control_gate": cl_summary.get("chain", {}).get("control_gate"), "files": manifest["files"]}


def _md_table(df: pd.DataFrame, cols: list[str], fmt: dict[str, str] | None = None) -> list[str]:
    fmt = fmt or {}
    L = ["| " + " | ".join(cols) + " |", "|" + "---|" * len(cols)]
    for _, r in df.iterrows():
        L.append("| " + " | ".join((format(r[c], fmt[c]) if c in fmt and pd.notna(r[c]) else str(r[c])) for c in cols) + " |")
    return L


def format_pre_reads_s7(s: dict[str, Any], tables: dict[str, pd.DataFrame]) -> str:
    m, c = s["marginal"], s["code_leaning"]
    L = [f"# Tier-4 pre-reads for the {s['run']} run: label-only numbers, no forward pass", ""]
    L += [f"## 1. The marginal-matched control: curve 1's configuration at rungs {', '.join(m['rungs'])}, {m['draws']} draws, {m['n_seeds']} label-only seeds", "",
          f"Candidates (usage above zero at tau = {m['tau']:g} on D_unif, {m['n_positions']} positions): {m['n_candidates']}, of which {m['n_candidates_not_alive']} are not in the alive vector ({m['n_alive']}); "
          f"{m['n_alive_not_candidates']} alive subcomponents are not candidates. Overflows of the marginal sampler: {m['n_marginal_overflows']}.", ""]
    g = tables["marginal_gate"]
    L += ["### The gate on the sampler's bias (mean over seeds of the pooled statistic, over the union's pooled value)", ""]
    L += _md_table(g, ["rung", "statistic", "gated", "union_value", "plain_value", "seeds_mean", "seeds_sd", "seeds_p2_5", "seeds_p97_5", "ratio_seeds_mean_to_union", "bound_low", "bound_high", "within_bounds",
                       "union_percentile_in_seeds", "replicate_0_percentile", "replicate_1_percentile"],
                   {k: ".4f" for k in ("union_value", "plain_value", "seeds_mean", "seeds_sd", "seeds_p2_5", "seeds_p97_5", "ratio_seeds_mean_to_union")} | {k: ".1f" for k in ("union_percentile_in_seeds", "replicate_0_percentile", "replicate_1_percentile")})
    L += ["", f"Gate at rungs {', '.join(m['gate']['rungs'])}: **{'pass' if m['gate']['pass'] else 'FAIL'}**" + ("" if m["gate"]["pass"] else " (" + "; ".join(m["gate"]["failures"]) + ")"), ""]
    if m.get("real_position_sets"):
        rp = m["real_position_sets"]
        L += [f"### The realized eight rung-1 positions among {rp['n_sets']} sets of {rp['draws_per_set']} real pool positions (seeds {rp['seed_pattern']}, draws {rp['draws_used'][0]} to {rp['draws_used'][1]}; marginal_real_position_sets.csv)", "",
              "| statistic | realized | sets' mean | SD | min | p5 | p50 | p95 | max | realized percentile |", "|---|---|---|---|---|---|---|---|---|---|"]
        for stat in ("mean_usage", "mean_norm", "n"):
            v = rp[stat]
            L.append(f"| {stat} | {v['realized']:.4f} | {v['sets_mean']:.4f} | {v['sets_sd']:.4f} | {v['sets_min']:.4f} | {v['sets_p5']:.4f} | {v['sets_p50']:.4f} | {v['sets_p95']:.4f} | {v['sets_max']:.4f} | {v['realized_percentile']:.1f} |")
        L.append("")
    L += ["### Overlap of each control with the union (overlap_mass_pooled is the named constant: total intersection mass over total named mass, over the draws)", ""]
    L += _md_table(tables["marginal_overlap_by_rung"], ["control", "family", "replicate", "rung", "overlap_mass_pooled", "overlap_mass_mean_of_draw_ratios", "overlap_mass_mean_over_texts", "overlap_count_pooled",
                                                        "overlap_count_mean_of_draw_ratios", "overlap_mass_min_draw", "overlap_mass_max_draw"],
                   {k: ".4f" for k in ("overlap_mass_pooled", "overlap_mass_mean_of_draw_ratios", "overlap_mass_mean_over_texts", "overlap_count_pooled", "overlap_count_mean_of_draw_ratios", "overlap_mass_min_draw", "overlap_mass_max_draw")})
    pw = tables["marginal_pairwise_real_draws"].groupby("rung", sort=False).agg(mean=("overlap_count_of_a", "mean"), min=("overlap_count_of_a", "min"), max=("overlap_count_of_a", "max"), jaccard=("jaccard", "mean")).reset_index()
    L += ["", "Pairwise count overlap between the real draws at the same rung (shared members over the first draw's count, ordered pairs):", ""]
    L += _md_table(pw, ["rung", "mean", "min", "max", "jaccard"], {k: ".4f" for k in ("mean", "min", "max", "jaccard")})
    L += ["", f"Decisive rungs by the rule (pooled switched-mass overlap of replicate 0 at most {m['decisive_rule']['max_overlap_mass_pooled']:.4f}): " + "; ".join(f"{k}: {', '.join(v) if v else 'none'}" for k, v in m["decisive_rule"]["by_family"].items()), ""]
    comp = tables["marginal_composition"]
    L += ["### Composition, pooled over draws (per draw in marginal_composition.csv)", ""]
    L += _md_table(comp[comp.draw.astype(str) == "pooled"], ["control", "family", "replicate", "rung", "n", "mean_norm", "median_norm", "p90_norm", "mean_usage", "median_usage", "p90_usage", "mean_sigma", "n_not_alive"],
                   {k: ".4f" for k in ("mean_norm", "median_norm", "p90_norm", "mean_usage", "median_usage", "p90_usage")} | {"mean_sigma": ".2f"})
    L += ["", "### The usage distribution", ""]
    L += _md_table(tables["usage_distribution"], list(tables["usage_distribution"].columns), {f"p{p}": ".5f" for p in range(0, 101, 10)} | {"mean": ".5f"})
    e = c["existence"]
    th = c.get("thresholds", {})
    forced = "" if th.get("default_thresholds", True) and not th.get("chain_forced") else f" **The stand-in's forced configuration: group s >= {th['group']:g}, wide set s >= {th['wide']:g}, chain forced {th['chain_forced']}; not the thresholds fixed in advance.**"
    L += ["", f"## 2. The code-leaning group: tau = {c['tau']:g}, {c['n_alive']} alive subcomponents, {c['n_rows_code']} code rows and {c['n_rows_prose']} prose rows" + forced, "",
          f"Alive subcomponents with a defined selectivity: {c['n_alive_with_defined_selectivity']}; passing the floor toward code {c['n_alive_floor_code']}, toward prose {c['n_alive_floor_prose']}.", ""]
    L += _md_table(tables["code_leaning_groups"], ["group", "n_members", "firing_mass", "share_of_alive_firing_mass", "mean_weight_norm", "mean_usage_unif", "min_selectivity"],
                   {"firing_mass": ".4f", "share_of_alive_firing_mass": ".4f", "mean_weight_norm": ".4f", "mean_usage_unif": ".5f", "min_selectivity": ".4f"})
    L += ["", f"**The existence rule on {e['group']}: {e['verdict']}.** M = {e['mass']:.4f} of {e['alive_code_firing_mass']:.2f} (share {e['share']:.4f}; {e['n_members']} members); the shuffle null over {e['n_shuffles']} shuffles: "
              f"mean {e['null_mean']:.5f}, 95th percentile {e['null_p95']:.5f}, maximum {e['null_max']:.5f}, against a fifth of M = {e['a_fifth_of_mass']:.5f} (mean members under the null {e['null_mean_members']:.1f}).", ""]
    st = c["stray_code"]
    L += [f"Stray code (descriptive): {st['n_members_firing_in_prose']} of {st['n_members']} members fire in prose, {st['prose_firings_of_the_group']} firings in all; the ten prose rows where the group fires most hold "
          f"{st['group_share_in_its_top_10_rows']:.4f} of them (ten of {st['n_prose_rows']} rows at random would hold {st['uniform_share_of_10_rows']:.4f}); per member, the share in its own top ten rows: {st['per_member_share_in_own_top_10_rows']}.", ""]
    if "code_leaning_chain" in tables:
        L += ["### The chain (rungs are prefixes of G_0.75 ordered by selectivity, then code usage, then the seeded tie permutation)", ""]
        L += _md_table(tables["code_leaning_chain"], ["rung_size", "descriptive", "min_selectivity", "code_firing_mass", "share_of_alive_code_firing_mass", "mean_weight_norm", "mean_usage_unif", "n_matrices"],
                       {"min_selectivity": ".4f", "code_firing_mass": ".4f", "share_of_alive_code_firing_mass": ".4f", "mean_weight_norm": ".4f", "mean_usage_unif": ".5f"})
        cg = c["chain"]["control_gate"]
        L += ["", f"### The usage-matched control against the group (nearest-neighbour twins, W = {c['chain']['control']['window']}; mean over draws)", ""]
        L += _md_table(tables["code_leaning_control_by_rung"], ["rung_size", "descriptive", "judged_by_the_gate", "group_mean_weight_norm", "control_mean_weight_norm", "norm_ratio_control_to_group", "group_mean_usage_unif",
                                                                "control_mean_usage_unif", "usage_ratio_control_to_group", "median_pair_usage_ratio", "norm_off_by_more_than_10_percent", "usage_off_by_more_than_10_percent", "gate_pass",
                                                                "total_shortfall"],
                       {k: ".4f" for k in ("group_mean_weight_norm", "control_mean_weight_norm", "norm_ratio_control_to_group", "usage_ratio_control_to_group", "median_pair_usage_ratio")} | {"group_mean_usage_unif": ".5f", "control_mean_usage_unif": ".5f"})
        L += ["", f"The control's gate ({cg['rule']}) at rungs {cg['rungs_judged']}: **{'pass' if cg['pass'] else ('FAIL at ' + str(cg['failures']) if cg['pass'] is not None else 'no rung judged')}**"]
        t = tables["code_leaning_testability"]
        L += ["", "### Testability on E_lab (the hard-zero rule's floor: at least 64 contributing texts on average and a clean-prefix fraction of at least 0.05); every stratum in code_leaning_testability.csv", ""]
        L += _md_table(t[t.stratum.isin(["Github", "other"])], ["chain", "rung_size", "descriptive", "tau_q", "stratum", "n_draws", "n_sequences", "mean_n_contributing", "mean_clean_prefix_fraction", "fraction_never_touched", "floor_met"],
                       {"mean_n_contributing": ".1f", "mean_clean_prefix_fraction": ".4f", "fraction_never_touched": ".4f"})
    return "\n".join(L)


def finish_pre_reads_s7(s7_dir: Path, *, stores_root: Path | None, sets_dir: Path = env.SETS_DIR, prose_set: str = "D_prose", calibration: Path | None = None, log: Any = print) -> dict[str, Any]:
    """The local finishing step, from the pulled tables: (1) the histogram's figure from its CSV; (2) the stray-code rows scored by
    the frozen code filter (the prose set's ids are local; its hash is asserted equal to the cache's recorded set hash;
    thresholds from the committed calibration, which must be frozen); (3) with `stores_root` (results/grid/<run>), the
    pre-read's union and plain sets checked against the committed cell tables' source hashes, their mean switched mass
    against the committed sigma_E.parquet, and the manifest's hashes against the committed pre-reads manifest. Writes
    code_leaning_histogram.png, code_leaning_stray_code_rows_scored.csv, and verification.json; changes no other file."""
    s7_dir = Path(s7_dir)
    with open(s7_dir / "manifest.json") as f:
        manifest = json.load(f)
    out: dict[str, Any] = {"run": manifest["run"], "s7_commit": manifest["commits"]}
    # ---- (1) the figure
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    h = pd.read_csv(s7_dir / "code_leaning_histogram.csv")
    fig, ax = plt.subplots(figsize=(7.5, 4.2))
    w = (h.bin_high - h.bin_low).to_numpy()
    ax.bar(h.bin_low, h.share_of_alive_code_firing_mass, width=w, align="edge", color="#9ecae1", edgecolor="#3182bd", label="all alive subcomponents")
    ax.bar(h.bin_low, h.weight_u_code_floor_passed / h.weight_u_code.sum(), width=w, align="edge", color="none", edgecolor="#e6550d", hatch="//", label="passing the support floor")
    for x in CL_THRESHOLDS:
        ax.axvline(x, color="k", lw=0.6, ls=":")
    ax.set_xlabel("selectivity s = u_code / (u_code + u_prose)")
    ax.set_ylabel("share of the alive set's code-firing mass")
    ax.set_title(f"Code-firing mass by selectivity ({manifest['run']} run, tau = {CL_TAU:g})")
    ax.legend(frameon=False, fontsize=8)
    fig.tight_layout()
    fig.savefig(s7_dir / "code_leaning_histogram.png", dpi=150)
    plt.close(fig)
    # ---- (2) the stray-code rows under the frozen filter
    if calibration is not None:
        from transformers import AutoTokenizer

        from vpd_audit.codefilter import classify, score_rows
        from vpd_audit.data import LABELED_TOKENIZER, hash_ids, load_set

        with open(calibration) as f:
            cal = json.load(f)
        assert cal["frozen"] is True, "the code filter's thresholds are not frozen"
        ids, _, _ = load_set(prose_set, sets_dir)
        assert hash_ids(ids) == manifest["caches"]["D_prose"]["set_hash"], "the local prose set is not the set the cache was built from"
        rows = pd.read_csv(s7_dir / "code_leaning_stray_code_rows.csv")
        tok = AutoTokenizer.from_pretrained(LABELED_TOKENIZER)
        sc = score_rows(ids[rows.prose_row.to_numpy()], tok, int(tok.eos_token_id))
        rows["f_p"], rows["f_i"], rows["n_eot"] = sc["f_p"], sc["f_i"], sc["n_eot"]
        rows["filter_class"] = [classify(a, b, cal["a"], cal["b"]) for a, b in zip(sc["f_p"], sc["f_i"])]
        rows.to_csv(s7_dir / "code_leaning_stray_code_rows_scored.csv", index=False)
        out["stray_code"] = {"thresholds": {"a": cal["a"], "b": cal["b"]}, "classes": rows.filter_class.value_counts().to_dict(), "set_hash": manifest["caches"]["D_prose"]["set_hash"]}
    # ---- (3) the sets against the committed stores
    if stores_root is not None:
        stores_root = Path(stores_root)
        committed = pd.concat([pd.read_parquet(p)[["cell", "source_sha256", "n_on"]] for p in sorted(stores_root.glob("tier*/*/cells.parquet"))], ignore_index=True)
        by_cell: dict[str, set[str]] = committed.groupby("cell")["source_sha256"].agg(lambda x: set(x)).to_dict()
        comp = pd.read_csv(s7_dir / "marginal_composition.csv", dtype={"rung": str, "draw": str})
        named = comp[comp.cell.notna() & (comp.cell != "")]
        missing = [c for c in named.cell if c not in by_cell]
        mismatched = [c for c, hsh in zip(named.cell, named.source_sha256) if c in by_cell and by_cell[c] != {hsh}]
        pre_dir = stores_root.parent / "pre_reads" / stores_root.name
        sig = pd.read_parquet(pre_dir / "sigma_E.parquet")
        worst = max(abs(float(sig[c].mean()) - float(m)) / max(1.0, abs(float(m))) for c, m in zip(named.cell, named.mean_sigma) if c in sig.columns)
        with open(pre_dir / "manifest.json") as f:
            pm = json.load(f)
        out["against_committed"] = {"n_union_and_plain_cells": int(len(named)), "cells_not_in_committed_tables": missing, "source_hash_mismatches": mismatched, "n_cells_in_sigma_E": int(sum(c in sig.columns for c in named.cell)),
                                    "max_relative_difference_of_mean_sigma": worst, "alive_sha256_equal": pm["alive_sha256"] == manifest["alive_sha256"],
                                    "weight_norms_sha256_equal": pm["weight_norms"]["sha256"] == manifest["weight_norms"]["sha256"], "committed_pre_reads_commit": pm["commits"]["project"]}
        assert not missing and not mismatched and worst <= 1e-9 and out["against_committed"]["alive_sha256_equal"] and out["against_committed"]["weight_norms_sha256_equal"], out["against_committed"]
    with open(s7_dir / "verification.json", "w") as f:
        json.dump(out, f, indent=2, sort_keys=True, default=str)
    log(json.dumps(out, indent=1, default=str))
    return out
