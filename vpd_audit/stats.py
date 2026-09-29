"""The pre-registered reading rules as code: statistics and labels on arrays, with no file reading and no divergence
printed. `analysis.py` loads the tables, builds the
arrays, and writes the report; `figures.py` draws.

Conventions. A chain's cells are arranged per rung as an excess matrix e of shape (K, N): K draws (one at rung 8
under r = 0), N sequences of the evaluation set, e[k, b] = K_bar^{(k, j)}_b - K_bar^{(k, 0)}_b paired on the sequence,
the draw, and (under the uniform background) the same u^{(k)}. The sequence bootstrap is one `Resample` per evaluation
set (or stratum): R index draws with replacement, kept as a count matrix W (R, N), shared across every rung, draw,
family, and chain evaluated on the same set, so that differences between families have their joint distribution. A
replicate's statistic is the mean over draws of the count-weighted mean over sequences. Percentile intervals are
two-sided at level 1 - alpha / m, m the number of rungs the curve compares (counted, never assumed), by linear
interpolation of the replicate quantiles.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import numpy as np

from vpd_audit.constants import SEQ_LEN
from vpd_audit.masks import seed_from_tuple
from vpd_audit.sources import BRIDGING_RUNGS, RUNG_SCHEDULE, SUB_RUNGS

X_MATERIAL = 0.05  # the materiality threshold X, nats per position
ALPHA = 0.05
N_REPLICATES = 10_000
FLOOR_CONTRIBUTING = 64  # the hard-zero rule's readability floor
FLOOR_CLEAN_FRACTION = 0.05
CONTRIBUTING_MIN_T_STAR = 8
REGISTERED_CORRECTION = 8  # the correction count of 8 fixed in advance, reported beside the counted one
HARD_ZERO_FAMILIES = ("hard_zero", "code_specific_hard", "never_named_hard")


# ----------------------------------------------------------------------------- rung order


def donor_count_order(rung: str) -> tuple[int, float]:
    """The chain order by donor count, never by label: the position run (1, 2, 3 at 1, 8, 64 positions), then the sequence
    run (4, 5a, 5, 6a, 6, 7 at 1, 2, 4, 8, 16, 64 sequences, then B50 and B75, then 8, the pool), then the sub-rung chain
    S4, S16, S64. Returns (run, count); sorting by it gives the plots' x order and the budgets' order."""
    r = str(rung)
    if r in SUB_RUNGS:
        return (2, float(SUB_RUNGS[r]))
    if r in BRIDGING_RUNGS:
        return (1, 1e6 * (1 + BRIDGING_RUNGS[r]))
    unit, count = RUNG_SCHEDULE[r]
    if unit == "none":
        return (-1, 0.0)
    if unit == "position":
        return (0, float(count))
    if unit == "sequence":
        return (1, float(count))
    return (1, 1e9)  # the pool


def sort_rungs(rungs: list[str] | tuple[str, ...]) -> list[str]:
    return sorted((str(r) for r in rungs), key=donor_count_order)


def nested_runs(rungs: list[str]) -> list[list[str]]:
    """The nested runs of a chain: the position run, the sequence run (with the bridging rungs and rung
    8), and the sub-rung chain, each in donor-count order; monotonicity checks are within a run."""
    out = []
    for run_idx in (0, 1, 2):
        rs = [r for r in sort_rungs(rungs) if donor_count_order(r)[0] == run_idx]
        if rs:
            out.append(rs)
    return out


def compared_rungs(rungs: list[str], family: str) -> list[str]:
    """The rungs a curve compares: every rung for a union or soft-erase curve (rung 8 included); every rung but 8 for a
    hard-zero donor chain (the hard-zero rule reads rung 8 by no rule); the sub-rungs form their own chain."""
    rs = [str(r) for r in rungs if str(r) != "0"]
    subs = [r for r in rs if r in SUB_RUNGS]
    if subs and len(subs) == len(rs):
        return sort_rungs(subs)
    assert not subs, f"a chain's rungs must be all sub-rungs or none (the sub-rung chain is its own chain): {rs}"
    donor = [r for r in rs if r not in SUB_RUNGS]
    if family in HARD_ZERO_FAMILIES:
        donor = [r for r in donor if r != "8"]
    return sort_rungs(donor)


def correction_count(rungs: list[str], family: str) -> int:
    return len(compared_rungs(rungs, family))


# ----------------------------------------------------------------------------- the sequence bootstrap


@dataclass
class Resample:
    """R index draws with replacement over N sequences, as a count matrix W (R, N) of int32; `seed_tuple` records the
    seed (master, "boot", set[, stratum]). `indices(r)` reproduces the r-th index set for the known-answer tests."""

    n: int
    replicates: int
    seed_tuple: tuple[Any, ...]
    W: np.ndarray = field(repr=False)

    @classmethod
    def make(cls, n: int, replicates: int, seed_tuple: tuple[Any, ...]) -> "Resample":
        rng = np.random.default_rng(seed_from_tuple(seed_tuple))
        W = np.zeros((replicates, n), dtype=np.int32)
        for r in range(replicates):
            idx = rng.integers(0, n, size=n)
            W[r] = np.bincount(idx, minlength=n)
        return cls(n=n, replicates=replicates, seed_tuple=tuple(seed_tuple), W=W)

    @classmethod
    def from_index_sets(cls, index_sets: list[list[int]], n: int) -> "Resample":
        W = np.zeros((len(index_sets), n), dtype=np.int32)
        for r, idx in enumerate(index_sets):
            W[r] = np.bincount(np.asarray(idx, dtype=np.int64), minlength=n)
        return cls(n=n, replicates=len(index_sets), seed_tuple=("explicit",), W=W)

    def restrict(self, mask: np.ndarray, seed_tuple: tuple[Any, ...]) -> "Resample":
        """A resample of the sequences a boolean mask selects (a stratum), drawn with its own seed."""
        return Resample.make(int(mask.sum()), self.replicates, seed_tuple)

    def means(self, v: np.ndarray) -> np.ndarray:
        """Count-weighted means over sequences: v (N,) or (M, N) -> (R,) or (R, M)."""
        v = np.asarray(v, dtype=np.float64)
        if v.ndim == 1:
            return (self.W @ v) / self.n
        return (self.W @ v.T) / self.n

    def ratios(self, num: np.ndarray, den: np.ndarray) -> np.ndarray:
        """(W @ num) / (W @ den) per replicate, NaN where the denominator is zero; num and den (N,)."""
        a = self.W @ np.asarray(num, dtype=np.float64)
        b = self.W @ np.asarray(den, dtype=np.float64)
        with np.errstate(invalid="ignore", divide="ignore"):
            return np.where(b > 0, a / np.where(b > 0, b, 1.0), np.nan)


def percentile_interval(stats: np.ndarray, m: int, alpha: float = ALPHA) -> tuple[float, float]:
    """Two-sided percentile interval at level 1 - alpha / m: the alpha / (2 m) and 1 - alpha / (2 m) quantiles, linear."""
    s = np.asarray(stats, dtype=np.float64)
    s = s[np.isfinite(s)]
    if s.size == 0:
        return (float("nan"), float("nan"))
    q = alpha / (2 * m)
    return (float(np.quantile(s, q)), float(np.quantile(s, 1 - q)))


# ----------------------------------------------------------------------------- the union rule


def sign_condition(per_draw: np.ndarray, threshold: float = 0.0) -> tuple[bool, int, int]:
    """At least K - 1 of the K per-draw means above `threshold`; dropped (True) when there is one draw."""
    k = int(per_draw.size)
    above = int((per_draw > threshold).sum())
    if k <= 1:
        return True, above, k
    return above >= k - 1, above, k


def union_rung(e: np.ndarray, resample: Resample, m: int, *, x: float = X_MATERIAL, alt_m: int = REGISTERED_CORRECTION) -> dict[str, Any]:
    """One rung of a union curve from its excess matrix e (K, N): e_hat, the per-draw means, the corrected interval (with
    its half-width), the labels detected / material / repair, and whether the labels would differ at the fixed count of 8."""
    e = np.asarray(e, dtype=np.float64)
    assert e.ndim == 2
    K, N = e.shape
    per_draw = e.mean(axis=1)
    m_seq = e.mean(axis=0)  # mean over draws per sequence
    e_hat = float(m_seq.mean())
    stats = resample.means(m_seq)
    lo, hi = percentile_interval(stats, m)
    sign_ok, n_pos, k = sign_condition(per_draw, 0.0)
    detected = bool(lo > 0 and sign_ok)
    material = bool(detected and lo > x)
    repair = bool(hi < 0)
    lo8, hi8 = percentile_interval(stats, alt_m)
    detected8 = bool(lo8 > 0 and sign_ok)
    material8 = bool(detected8 and lo8 > x)
    return {"e_hat": e_hat, "per_draw": per_draw.tolist(), "n_draws": K, "n_sequences": N, "interval": [lo, hi], "half_width": (hi - lo) / 2, "m": m,
            "sign_condition": sign_ok, "n_draws_positive": n_pos, "detected": detected, "material": material, "repair": repair,
            "fraction_sequences_above_X": float((m_seq > x).mean()), "at_m_8": {"interval": [lo8, hi8], "detected": detected8, "material": material8, "differs": (detected8, material8) != (detected, material)}}


def union_curve(rung_excess: dict[str, np.ndarray], family: str, resample: Resample, *, x: float = X_MATERIAL) -> dict[str, Any]:
    """The union rule over a curve: per-rung results in donor-count order, the curve's label, j_det, j_mat, the first repair
    rung, and the per-draw j_det and j_mat."""
    rungs = compared_rungs(list(rung_excess), family)
    m = len(rungs)
    per_rung = {r: union_rung(rung_excess[r], resample, m, x=x) for r in rungs}
    j_det = next((r for r in rungs if per_rung[r]["detected"]), None)
    j_mat = next((r for r in rungs if per_rung[r]["material"]), None)
    j_rep = next((r for r in rungs if per_rung[r]["repair"]), None)
    if any(per_rung[r]["material"] for r in rungs):
        label = "fails"
    elif not any(per_rung[r]["detected"] for r in rungs):
        label = "holds at the scale tested"
    else:
        label = "detected but immaterial"
    label8 = "fails" if any(per_rung[r]["at_m_8"]["material"] for r in rungs) else ("holds at the scale tested" if not any(per_rung[r]["at_m_8"]["detected"] for r in rungs) else "detected but immaterial")
    # per draw: the smallest rung whose single-draw interval leaves zero / passes X (no sign condition for one draw)
    per_draw: dict[str, Any] = {}
    K = max(rung_excess[r].shape[0] for r in rungs)
    for k in range(K):
        det = mat = None
        for r in rungs:
            e = rung_excess[r]
            if k >= e.shape[0]:
                continue
            lo, hi = percentile_interval(resample.means(e[k]), m)
            if det is None and lo > 0:
                det = r
            if mat is None and lo > x:
                mat = r
        per_draw[f"k{k}"] = {"j_det": det, "j_mat": mat}
    return {"rungs": rungs, "m": m, "per_rung": per_rung, "label": label, "label_at_m_8": label8, "label_differs_at_m_8": label8 != label,
            "j_det": j_det, "j_mat": j_mat, "first_repair": j_rep, "negative_at_any_rung": any(per_rung[r]["e_hat"] < 0 for r in rungs), "per_draw": per_draw}


def two_level_interval(e: np.ndarray, resample: Resample, m: int, seed_tuple: tuple[Any, ...]) -> list[float]:
    """The two-level bootstrap over sequences and draws (reported only): per replicate the draws are resampled with
    replacement as well, the sequence resample being the shared one."""
    e = np.asarray(e, dtype=np.float64)
    K = e.shape[0]
    if K <= 1:
        lo, hi = percentile_interval(resample.means(e.mean(axis=0)), m)
        return [lo, hi]
    rng = np.random.default_rng(seed_from_tuple(seed_tuple))
    draw_counts = rng.multinomial(K, np.full(K, 1.0 / K), size=resample.replicates).astype(np.float64)  # (R, K)
    per_draw_stats = resample.means(e)  # (R, K)
    stats = (draw_counts * per_draw_stats).sum(axis=1) / K
    lo, hi = percentile_interval(stats, m)
    return [lo, hi]


def paired_difference(a: np.ndarray, b: np.ndarray, resample: Resample, *, level_m: int = 1) -> dict[str, Any]:
    """The paired per-sequence difference of two families on the same sequences, draws, and rung: a - b, (K, N) each,
    mean over draws then sequences, with the shared resample at the uncorrected 95 percent level (level_m = 1)."""
    d = np.asarray(a, dtype=np.float64) - np.asarray(b, dtype=np.float64)
    m_seq = d.mean(axis=0)
    lo, hi = percentile_interval(resample.means(m_seq), level_m)
    return {"mean": float(m_seq.mean()), "interval": [lo, hi], "half_width": (hi - lo) / 2, "n_draws": int(d.shape[0]), "n_sequences": int(d.shape[1])}


def unpaired_difference(a: np.ndarray, b: np.ndarray, resample_a: Resample, resample_b: Resample) -> dict[str, Any]:
    """Mean of a minus mean of b on disjoint sequence sets (each (K, N_a) and (K, N_b)), with independent resamples of the
    two sets, uncorrected 95 percent."""
    ma, mb = np.asarray(a, dtype=np.float64).mean(axis=0), np.asarray(b, dtype=np.float64).mean(axis=0)
    stats = resample_a.means(ma) - resample_b.means(mb)
    lo, hi = percentile_interval(stats, 1)
    return {"mean": float(ma.mean() - mb.mean()), "interval": [lo, hi], "half_width": (hi - lo) / 2, "n_a": int(ma.size), "n_b": int(mb.size)}


# ----------------------------------------------------------------------------- the hard-zero rule


def readability(t_star: np.ndarray) -> dict[str, Any]:
    """The readability floor from a (K, N) matrix of first touched positions at the primary tau_q: at least 64 contributing
    sequences (t* >= 8) on average over draws and a clean-prefix fraction of at least 0.05."""
    t = np.asarray(t_star, dtype=np.int64)
    contributing = (t >= CONTRIBUTING_MIN_T_STAR).sum(axis=1)
    clean = (t / SEQ_LEN).mean(axis=1)
    mean_c, mean_clean = float(contributing.mean()), float(clean.mean())
    return {"mean_n_contributing": mean_c, "mean_clean_prefix_fraction": mean_clean, "per_draw_n_contributing": contributing.tolist(),
            "floor_met": bool(mean_c >= FLOOR_CONTRIBUTING and mean_clean >= FLOOR_CLEAN_FRACTION), "fraction_never_touched": float((t == SEQ_LEN).mean())}


def hard_zero_rung(d: np.ndarray, t_star: np.ndarray, resample: Resample, m: int, *, x: float = X_MATERIAL, one_cell: bool = False) -> dict[str, Any]:
    """One rung of a hard-zero chain: d (K, N) the conditional damage (NaN where t* = 0), t_star (K, N) at the tau_q being
    read; contributors are the sequences with t* >= 8 under that draw's set; d_hat is the mean over draws of the mean over
    contributors; per replicate and draw the contributors are the resampled rows that contribute, a draw with none is
    dropped from that replicate's mean over draws (frequency recorded); the label holds / fails / indeterminate."""
    d = np.asarray(d, dtype=np.float64)
    t = np.asarray(t_star, dtype=np.int64)
    K, N = d.shape
    c = (t >= CONTRIBUTING_MIN_T_STAR) & np.isfinite(d)
    per_draw = np.array([d[k, c[k]].mean() if c[k].any() else np.nan for k in range(K)])
    d_hat = float(np.nanmean(per_draw)) if np.isfinite(per_draw).any() else float("nan")
    stats = np.full(resample.replicates, np.nan)
    per_draw_stats = np.stack([resample.ratios(np.where(c[k], d[k], 0.0), c[k].astype(np.float64)) for k in range(K)], axis=1)  # (R, K), NaN where no contributor
    valid = np.isfinite(per_draw_stats)
    n_valid = valid.sum(axis=1)
    with np.errstate(invalid="ignore"):
        stats = np.where(n_valid > 0, np.nansum(np.where(valid, per_draw_stats, 0.0), axis=1) / np.maximum(n_valid, 1), np.nan)
    lo, hi = percentile_interval(stats, m)
    sign_ok, n_above, k = sign_condition(per_draw[np.isfinite(per_draw)], x)
    if one_cell or K == 1:
        sign_ok = True
    holds = bool(np.isfinite(hi) and hi < x)
    fails = bool(np.isfinite(lo) and lo > x and sign_ok)
    label = "holds" if holds else ("fails" if fails else "indeterminate")
    return {"d_hat": d_hat, "per_draw": per_draw.tolist(), "n_draws": K, "n_sequences": N, "n_contributing_per_draw": c.sum(axis=1).tolist(),
            "interval": [lo, hi], "half_width": (hi - lo) / 2 if np.isfinite(lo) and np.isfinite(hi) else float("nan"), "m": m,
            "replicates_with_a_draw_dropped": int((n_valid < K).sum()), "replicates_with_no_draw": int((n_valid == 0).sum()),
            "sign_condition": bool(sign_ok), "n_draws_above_X": n_above, "label": label}


def editing_budget(rungs_in_order: list[str], labels: dict[str, str], testable: dict[str, bool]) -> dict[str, Any]:
    """The largest rung, in donor-count order, such that the claim holds at every testable rung up to it; a rung that is
    not testable is skipped, never counted as a failure."""
    budget = None
    for r in rungs_in_order:
        if not testable.get(r, False):
            continue
        if labels.get(r) == "holds":
            budget = r
        else:
            break
    return {"budget_rung": budget, "rungs_in_order": rungs_in_order, "labels": {r: labels.get(r) for r in rungs_in_order}, "testable": {r: bool(testable.get(r, False)) for r in rungs_in_order}}


def hard_zero_chain(rung_d: dict[str, np.ndarray], rung_t: dict[str, np.ndarray], family: str, resample: Resample, *, x: float = X_MATERIAL,
                    floor_override: dict[str, bool] | None = None) -> dict[str, Any]:
    """The hard-zero rule over a chain at one tau_q: per rung the readability floor (judged once, on the observed data),
    the rung's result where testable, and the editing budget. `floor_override`, when given, must agree with the floor
    judged here (the pre-reads' testability table), asserted by the caller."""
    rungs = compared_rungs(list(rung_d), family)
    m = len(rungs)
    per_rung: dict[str, Any] = {}
    labels, testable = {}, {}
    for r in rungs:
        read = readability(rung_t[r])
        one_cell = rung_d[r].shape[0] == 1
        res = hard_zero_rung(rung_d[r], rung_t[r], resample, m, x=x, one_cell=one_cell) if read["floor_met"] else None
        per_rung[r] = {"readability": read, "testable": read["floor_met"], "result": res}
        testable[r] = read["floor_met"]
        labels[r] = res["label"] if res else "not testable with these donors"
    return {"rungs": rungs, "m": m, "per_rung": per_rung, "budget": editing_budget(rungs, labels, testable)}


# ----------------------------------------------------------------------------- descriptives


def decile_edges(pooled_sigma: np.ndarray) -> np.ndarray:
    """The deciles (0 to 100 by 10) of the union's pooled switched mass; bins are [edge_i, edge_{i+1}) with the last closed,
    plus an overflow bin above the top edge."""
    return np.percentile(np.asarray(pooled_sigma, dtype=np.float64), np.arange(0, 101, 10))


def assign_bins(sigma: np.ndarray, edges: np.ndarray) -> np.ndarray:
    """Bin index 0..9 for the ten decile bins, 10 for the overflow bin above the top edge, -1 below the bottom edge."""
    s = np.asarray(sigma, dtype=np.float64)
    idx = np.searchsorted(edges, s, side="right") - 1  # edges[i] <= s < edges[i+1]
    idx = np.where(s == edges[-1], 9, idx)  # the top edge closed
    idx = np.where(s > edges[-1], 10, idx)
    idx = np.where(s < edges[0], -1, idx)
    return idx.astype(np.int64)


def binned_difference(points_u: dict[str, np.ndarray], points_c: dict[str, np.ndarray], edges: np.ndarray, resample: Resample, *, min_sequences: int = 64) -> list[dict[str, Any]]:
    """Per bin, the union's mean excess minus the control's, each family's points being (excess, sigma, seq) arrays over
    sequences, draws, and rungs; a bin is compared only if both families hold at least `min_sequences` distinct sequences
    in it; the interval from the shared resample, each resampled sequence carrying all its points, 95 percent uncorrected."""
    out = []
    bu, bc = assign_bins(points_u["sigma"], edges), assign_bins(points_c["sigma"], edges)
    n = resample.n
    for b in range(11):
        su, sc = bu == b, bc == b
        nu, nc = np.unique(points_u["seq"][su]).size, np.unique(points_c["seq"][sc]).size
        row: dict[str, Any] = {"bin": b, "overflow": b == 10, "edge_low": float(edges[b]) if b < 10 else float(edges[10]), "edge_high": float(edges[b + 1]) if b < 10 else float("inf"),
                               "n_points_union": int(su.sum()), "n_points_control": int(sc.sum()), "n_sequences_union": int(nu), "n_sequences_control": int(nc),
                               "populated": bool(nu >= min_sequences and nc >= min_sequences),
                               # each family's bin mean whenever that family alone holds enough sequences (the other run's comparison reads it); the
                               # difference and its interval only where both do
                               "union_mean_excess": float(points_u["excess"][su].mean()) if nu >= min_sequences else float("nan"),
                               "control_mean_excess": float(points_c["excess"][sc].mean()) if nc >= min_sequences else float("nan")}
        if row["populated"]:
            num_u = np.bincount(points_u["seq"][su], weights=points_u["excess"][su], minlength=n)
            cnt_u = np.bincount(points_u["seq"][su], minlength=n).astype(np.float64)
            num_c = np.bincount(points_c["seq"][sc], weights=points_c["excess"][sc], minlength=n)
            cnt_c = np.bincount(points_c["seq"][sc], minlength=n).astype(np.float64)
            stats = resample.ratios(num_u, cnt_u) - resample.ratios(num_c, cnt_c)
            lo, hi = percentile_interval(stats, 1)
            row.update({"difference": float(points_u["excess"][su].mean() - points_c["excess"][sc].mean()), "interval": [lo, hi]})
        out.append(row)
    return out


def ols_slope(x: np.ndarray, y: np.ndarray, seq: np.ndarray, resample: Resample) -> dict[str, Any]:
    """Ordinary least squares y = a + s x with an intercept over pooled points, sequence-bootstrapped (each resampled sequence
    carrying its points), 95 percent uncorrected; a linear summary of a curve that need not be linear."""
    x, y, seq = np.asarray(x, np.float64), np.asarray(y, np.float64), np.asarray(seq, np.int64)
    n = resample.n
    sums = {k: np.bincount(seq, weights=v, minlength=n) for k, v in (("x", x), ("y", y), ("xy", x * y), ("xx", x * x), ("c", np.ones_like(x)))}
    W = resample.W.astype(np.float64)
    Sx, Sy, Sxy, Sxx, Sc = (W @ sums[k] for k in ("x", "y", "xy", "xx", "c"))
    with np.errstate(invalid="ignore", divide="ignore"):
        slope = (Sxy - Sx * Sy / Sc) / (Sxx - Sx * Sx / Sc)
        intercept = (Sy - slope * Sx) / Sc
    s0 = (sums["xy"].sum() - sums["x"].sum() * sums["y"].sum() / sums["c"].sum()) / (sums["xx"].sum() - sums["x"].sum() ** 2 / sums["c"].sum())
    a0 = (sums["y"].sum() - s0 * sums["x"].sum()) / sums["c"].sum()
    return {"slope": float(s0), "slope_interval": list(percentile_interval(slope, 1)), "intercept": float(a0), "intercept_interval": list(percentile_interval(intercept, 1)), "n_points": int(x.size)}


def difference_quotients(rung_mean_excess: dict[str, float], rung_mean_sigma: dict[str, float], rungs_in_order: list[str]) -> list[dict[str, Any]]:
    """Local slopes between consecutive rungs: the difference of mean excess over the difference of mean sigma."""
    out = []
    for a, b in zip(rungs_in_order, rungs_in_order[1:]):
        ds = rung_mean_sigma[b] - rung_mean_sigma[a]
        out.append({"from": a, "to": b, "d_excess": rung_mean_excess[b] - rung_mean_excess[a], "d_sigma": ds, "quotient": (rung_mean_excess[b] - rung_mean_excess[a]) / ds if ds else float("nan")})
    return out


def mean_se(v: np.ndarray) -> dict[str, float]:
    v = np.asarray(v, dtype=np.float64)
    v = v[np.isfinite(v)]
    return {"mean": float(v.mean()) if v.size else float("nan"), "se": float(v.std(ddof=1) / np.sqrt(v.size)) if v.size > 1 else float("nan"), "n": int(v.size)}


# ----------------------------------------------------------------------------- the positive control (P5)


def positive_control_paired(erase: dict[str, np.ndarray], control: dict[str, np.ndarray], rungs: list[str]) -> dict[str, Any]:
    """On the GitHub stratum: per rung j >= 4 (5a and 6a included) and every sub-rung, the mean over draws of the paired
    per-sequence difference of unconditional damage, erase minus control, must be positive; erase and control are
    (K, N_stratum) unconditional damages per rung."""
    per_rung = {}
    for r in rungs:
        if r in SUB_RUNGS or donor_count_order(r) >= donor_count_order("4"):
            if r not in erase or r not in control:
                per_rung[r] = {"available": False}
                continue
            d = (np.asarray(erase[r], np.float64) - np.asarray(control[r], np.float64)).mean(axis=1)  # per draw
            per_rung[r] = {"available": True, "mean_paired_difference": float(d.mean()), "per_draw": d.tolist(), "positive": bool(d.mean() > 0)}
    judged = [v for v in per_rung.values() if v.get("available")]
    return {"per_rung": per_rung, "n_rungs_judged": len(judged), "pass": bool(judged) and all(v["positive"] for v in judged)}


def positive_control_material(damage: dict[str, np.ndarray], rungs: list[str], *, x: float = X_MATERIAL) -> dict[str, Any]:
    """On E for the uniform-donor hard-zero: the unconditional damage is material (mean over draws and sequences above X) at
    rung 4 and beyond, 5a and 6a included."""
    per_rung = {}
    for r in rungs:
        if donor_count_order(r) >= donor_count_order("4") and r not in SUB_RUNGS:
            if r not in damage:
                per_rung[r] = {"available": False}
                continue
            mean = float(np.asarray(damage[r], np.float64).mean())
            per_rung[r] = {"available": True, "mean_damage": mean, "material": bool(mean > x)}
    judged = [v for v in per_rung.values() if v.get("available")]
    return {"per_rung": per_rung, "n_rungs_judged": len(judged), "pass": bool(judged) and all(v["material"] for v in judged)}
