"""The tier-5 reading rules as pure functions (no store, no file), pinned by known-answer tests
(tests/test_stats_s9.py). Every rule here was fixed before any tier-5 number existed; the glue is analysis_s9.py.

**Intervals.** A *rise matrix* e is (K, N): draw by text, the text's mean divergence under a merge minus its mean divergence
under its own labels. On E the resample is `stats.Resample.make` over texts; on a stratum of E_lab it is
`s9_checks.document_resample` (all rows of a drawn document enter together). Every replicate statistic here is in *ratio form*,
the resampled row total over the resampled row count (`ratio_means`), so point estimates stay plain means over rows and a ratio
recomputes all of its sums within each replicate. For a text resample the row count is n in every replicate, so the ratio form
is the frozen `Resample.means` exactly. The frozen `stats.union_curve` and `stats.two_level_interval` divide by a fixed n and
cannot take a document resample: `union_curve_s9` and `two_level_interval_s9` are their twins. No interval for a stratum of
fewer than ten documents. A contrast between donor pools is two-level: draws are resampled as well, independently per pool
(`draw_counts`, one (R, K) multinomial table per pool, reused on every stratum and size the pool is scored on); documents are
resampled independently per stratum. Wherever a logarithm or a ratio is bootstrapped the share of non-finite replicates is
returned, and the quantity is not read if that share is above zero.

**Run 2.** `run2_outcome` (the gate and the verdict), `match_ratio` (r_code, r_prose, R, its two-level interval on log R at
level 1 - 0.05/3, and the reading), the descriptions, and `count_only` (arm U's ten per-size points made non-decreasing by pooling
adjacent violators on the log rise, log-log interpolation, each C draw predicted from its own amount, no extrapolation).
**Run 6.** `self_merge_rule`, `self_against_stranger`, `ladder_rung`, `scope_rule`.
**Runs 3 and 7.** The change rates with the target's tied positions excluded, the confident-position rate as a ratio of
sums over texts, the bin table, and the examples chosen by rule.

A same-size random control is compared only with its own arm, paired by draw and resampled
with it (`control_against_arm`); nothing here takes both arms' controls.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np

from vpd_audit import stats as st
from vpd_audit.masks import seed_from_tuple

X = st.X_MATERIAL  # 0.05 nats
ALPHA = st.ALPHA
MIN_DOCUMENTS = 10
FAILS, HOLDS, IMMATERIAL = "fails", "holds at the scale tested", "detected but immaterial"
NO_READING, F_SAME, F_LATER, D_BELOW, H, D_UNRESOLVED = "no reading", "F-same", "F-later", "D-below", "H", "D-unresolved"
R_SIZES_READ: tuple[str, ...] = ("2", "3", "7")  # 8 tokens, 64 tokens, 64 texts
R_SIZE_PRINTED_NOT_READ = "4"  # one whole text
R_M = 3
R_HELPS_BELOW, R_WORSE_ABOVE = 0.8, 1.25
MATCHING_HELPS, CLOSER_IS_WORSE, NO_MATERIAL_HELP, UNRESOLVED, NOT_READ = "matching helps", "closer is worse", "no material help", "unresolved at this size", "not read"
COUNT_ONLY_SIZES: tuple[str, ...] = ("3", "7")  # 64 tokens and 64 texts
COUNT_ONLY_MIN_DRAWS = 7
ABOVE, BELOW, ON_IT = "above the prediction", "below the prediction", "on it"
SELF_M = 3  # three sets
LADDER_M = 5
SELF_WORSE, SELF_LESS, SELF_NO_BETTER = "self is worse than a stranger", "self does less harm than a stranger", "self is no better than a stranger"
MATERIAL, UNDER = "material", "interval wholly under 0.05"
NONFINITE_FLAG = "some replicates drew no qualifying text: the interval is over the others, and the rung has no standing"
DIVERGENCE_BINS: tuple[float, ...] = (0.05, 0.2, 0.5, 1.0, 2.0)  # under 0.05, 0.05 to 0.2, 0.2 to 0.5, 0.5 to 1, 1 to 2, over 2
EXAMPLE_PERCENTILES: tuple[float, ...] = (10.0, 50.0, 90.0, 99.0)
EXAMPLES_WRITTEN = 5


# ----------------------------------------------------------------------------- replicates in ratio form


@dataclass
class StratifiedResample(st.Resample):
    """A document resample of a stratum of the labelled set that knows its sources. Sources are
    fixed by design, so the mix of sources must not vary between replicates: each source's documents are resampled among
    themselves, a statistic is taken in ratio form *per source*, and the sources are combined with **fixed design weights**. For
    a mean the weight is the source's row share in the full data, so the point estimate is the plain mean over rows, unchanged.
    (Pooling the resampled rows across sources would up-weight a source whenever its long documents are drawn.) `blocks` holds
    each source's row indices; they tile range(n). With one source this is `s9_checks.document_resample`, replicate for replicate.

    For a ratio of sums over texts (`ratios`: a change rate over positions, a ladder rung's mean over its qualifying texts) the
    same rule in the only form that leaves the point estimate unchanged: per source the ratio of resampled sums, combined with
    each source's share of the full data's denominator. With a denominator of ones that is the row share. A source whose share
    is zero contributes nothing; a replicate in which a source with a positive share draws a zero denominator is non-finite.
    `means`, which divides a varying row total by the fixed n, is refused."""

    blocks: tuple[np.ndarray, ...] = ()
    block_names: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        assert self.blocks and len(self.blocks) == len(self.block_names), "a stratified resample names its sources"
        rows = np.concatenate([np.asarray(b, dtype=np.int64) for b in self.blocks])
        assert np.array_equal(np.sort(rows), np.arange(self.n)) and self.W.shape == (self.replicates, self.n), "the sources' rows must tile the stratum"

    def means(self, v: np.ndarray) -> np.ndarray:
        raise AssertionError("Resample.means divides by the fixed n and must never be called on a document resample: use stats_s9.ratio_means")

    def ratios(self, num: np.ndarray, den: np.ndarray) -> np.ndarray:
        num, den = np.asarray(num, dtype=np.float64), np.asarray(den, dtype=np.float64)
        assert num.shape == den.shape == (self.n,) and np.all(den >= 0), "a ratio of sums over the stratum's texts, with a denominator that is a count"
        total = float(den.sum())
        if not total > 0:
            return np.full(self.replicates, np.nan)
        out = np.zeros(self.replicates, dtype=np.float64)
        for rows in self.blocks:
            share = float(den[rows].sum()) / total  # the fixed design weight: from the full data, never from a replicate
            if share == 0.0:
                continue
            a, b = self.W[:, rows] @ num[rows], self.W[:, rows] @ den[rows]
            with np.errstate(invalid="ignore", divide="ignore"):
                out = out + share * np.where(b > 0, a / np.where(b > 0, b, 1.0), np.nan)
        return out


def ratio_means(resample: st.Resample, v: np.ndarray) -> np.ndarray:
    """Row-weighted means per replicate, the resampled row total over the resampled row count: v (N,) -> (R,), v (M, N) -> (R, M).
    For a text resample the count is n in every replicate and this is `Resample.means`; for a document resample it is
    `s9_checks.doc_means`. On a `StratifiedResample` the ratio form is taken per source and the sources are combined with their
    fixed row shares, so the mix of sources is the design's in every replicate."""
    v = np.asarray(v, dtype=np.float64)
    assert v.shape[-1] == resample.n, (v.shape, resample.n)
    if isinstance(resample, StratifiedResample):
        out: Any = 0.0
        for rows in resample.blocks:
            Wb = resample.W[:, rows]
            den = Wb.sum(axis=1).astype(np.float64)
            assert np.all(den > 0), "a replicate with no row of a source"
            num = Wb @ (v[rows] if v.ndim == 1 else v[:, rows].T)
            out = out + (len(rows) / resample.n) * (num / (den if v.ndim == 1 else den[:, None]))
        return out
    den = resample.W.sum(axis=1).astype(np.float64)
    assert np.all(den > 0), "a replicate with no row"
    num = resample.W @ (v if v.ndim == 1 else v.T)
    return num / (den if v.ndim == 1 else den[:, None])


def interval(stats: np.ndarray, m: int) -> list[float]:
    lo, hi = st.percentile_interval(stats, m)
    return [lo, hi]


def nonfinite_share(stats: np.ndarray) -> float:
    s = np.asarray(stats, dtype=np.float64)
    return float((~np.isfinite(s)).mean()) if s.size else float("nan")


def draw_counts(n_draws: int, replicates: int, seed_tuple: tuple[Any, ...]) -> np.ndarray:
    """(R, K) float64: per replicate, how often each of a donor pool's K draws is drawn in K draws with replacement. One table per
    pool, seed (master, "boot_draws", pool), reused on every stratum and size the pool is scored on."""
    rng = np.random.default_rng(seed_from_tuple(seed_tuple))
    return rng.multinomial(n_draws, np.full(n_draws, 1.0 / n_draws), size=replicates).astype(np.float64)


def rise_replicates(e: np.ndarray, resample: st.Resample, counts: np.ndarray | None = None) -> np.ndarray:
    """(R,) replicates of the mean rise over draws and texts. With `counts` (R, K) the draws are resampled too (two-level); a
    size with one draw (the whole pool) has no draw to resample. Every replicate is in ratio form."""
    e = np.asarray(e, dtype=np.float64)
    assert e.ndim == 2 and e.shape[1] == resample.n, (e.shape, resample.n)
    per_draw = ratio_means(resample, e)  # (R, K)
    K = e.shape[0]
    if counts is None or K == 1:
        return per_draw.mean(axis=1)
    assert counts.shape == (resample.replicates, K), (counts.shape, (resample.replicates, K))
    return (counts * per_draw).sum(axis=1) / K


def has_interval(n_documents: int | None) -> bool:
    """No interval is reported for a stratum of fewer than ten documents; None means the unit is the text (E, D_unif)."""
    return n_documents is None or n_documents >= MIN_DOCUMENTS


def stratified_document_resample(doc_ids: np.ndarray, source_ids: np.ndarray, replicates: int, seed_for_source: Any) -> StratifiedResample:
    """The document bootstrap of a stratum of the labelled set, one source or several pooled (E^P, E^O, the whole of E_lab):
    documents are resampled *within source*, each source's documents among themselves with that source's own
    seed (`seed_for_source(source)`, the seed `s9_checks.document_resample` takes for the source alone), the count matrices side
    by side in row order, and the sources' rows kept, so that every statistic on it is per source with fixed design weights
    (`StratifiedResample`). A stratum of one source is `s9_checks.document_resample` of that source exactly. `doc_ids` must be distinct
    across sources (`s9_checks.document_codes`); a document that spans two sources is an error. Every replicate draws, in each
    source, as many documents as the source has."""
    from vpd_audit.s9_checks import document_resample

    doc_ids, source_ids = np.asarray(doc_ids), np.asarray(source_ids)
    assert doc_ids.shape == source_ids.shape and doc_ids.ndim == 1 and doc_ids.size > 0
    sources = list(dict.fromkeys(source_ids.tolist()))  # in order of first appearance
    for d in np.unique(doc_ids):
        assert len(set(source_ids[doc_ids == d].tolist())) == 1, f"document {d} spans more than one source: the document codes must be distinct per source"
    W = np.zeros((replicates, doc_ids.size), dtype=np.int32)
    blocks = []
    for s in sources:
        rows = np.flatnonzero(source_ids == s)
        W[:, rows] = document_resample(doc_ids[rows], replicates, tuple(seed_for_source(s))).W
        blocks.append(rows)
    return StratifiedResample(n=int(doc_ids.size), replicates=replicates, seed_tuple=("stratified",) + tuple(tuple(seed_for_source(s)) for s in sources), W=np.ascontiguousarray(W),
                              blocks=tuple(blocks), block_names=tuple(str(s) for s in sources))


# ----------------------------------------------------------------------------- the twins of stats.union_curve and stats.two_level_interval


def union_rung_s9(e: np.ndarray, resample: st.Resample, m: int, *, n_documents: int | None = None, x: float = X) -> dict[str, Any]:
    """`stats.union_rung` with its replicates in ratio form: e_hat, the per-draw means, the interval at level 1 - 0.05 / m, the sign
    condition (at least K - 1 of K per-draw means positive; dropped for one draw), detected, material, repair. Below ten
    documents: the point value and the document count, no interval, no label."""
    e = np.asarray(e, dtype=np.float64)
    assert e.ndim == 2
    per_draw = e.mean(axis=1)
    m_text = e.mean(axis=0)
    out: dict[str, Any] = {"e_hat": float(m_text.mean()), "per_draw": per_draw.tolist(), "n_draws": int(e.shape[0]), "n_texts": int(e.shape[1]), "n_documents": n_documents, "m": m}
    sign_ok, n_pos, _ = st.sign_condition(per_draw, 0.0)
    out.update({"sign_condition": sign_ok, "n_draws_positive": n_pos})
    if not has_interval(n_documents):
        out.update({"interval": None, "detected": None, "material": None, "repair": None})
        return out
    lo, hi = interval(ratio_means(resample, m_text), m)
    detected = bool(lo > 0 and sign_ok)
    out.update({"interval": [lo, hi], "detected": detected, "material": bool(detected and lo > x), "repair": bool(hi < 0)})
    return out


def curve_label(per_rung: dict[str, dict[str, Any]], rungs: list[str]) -> str | None:
    if any(per_rung[r]["detected"] is None for r in rungs):
        return None
    if any(per_rung[r]["material"] for r in rungs):
        return FAILS
    return HOLDS if not any(per_rung[r]["detected"] for r in rungs) else IMMATERIAL


def union_curve_s9(rung_excess: dict[str, np.ndarray], resample: st.Resample, *, n_documents: int | None = None, x: float = X) -> dict[str, Any]:
    """The same registered rule as `stats.union_curve`, over a curve, every given size compared (m is their number), in donor-count order:
    the label, the first detected and the first material size."""
    rungs = st.compared_rungs(list(rung_excess), "union")
    m = len(rungs)
    per_rung = {r: union_rung_s9(rung_excess[r], resample, m, n_documents=n_documents, x=x) for r in rungs}
    label = curve_label(per_rung, rungs)
    return {"rungs": rungs, "m": m, "per_rung": per_rung, "label": label, "j_det": next((r for r in rungs if per_rung[r]["detected"]), None),
            "j_mat": next((r for r in rungs if per_rung[r]["material"]), None), "n_documents": n_documents}


def two_level_interval_s9(e: np.ndarray, resample: st.Resample, counts: np.ndarray | None, m: int, *, n_documents: int | None = None) -> list[float] | None:
    if not has_interval(n_documents):
        return None
    return interval(rise_replicates(e, resample, counts), m)


# ----------------------------------------------------------------------------- the gate and the verdict


def run2_outcome(C: dict[str, Any], U: dict[str, Any], *, x: float = X) -> dict[str, Any]:
    """The verdict, by the rule fixed before the run, from the two curves on the code texts (`union_curve_s9` results, or hand-made ones with the same keys).
    Gate: arm U must fail, or run 2 takes no reading."""
    order = {r: i for i, r in enumerate(st.sort_rungs(list(dict.fromkeys(list(C["rungs"]) + list(U["rungs"])))))}
    if U["label"] != FAILS:
        return {"outcome": NO_READING, "gate": False, "reason": f"arm U on the code texts is {U['label']!r}, not {FAILS!r}"}
    if C["label"] is None:
        return {"outcome": NO_READING, "gate": True, "reason": "arm C has no interval (fewer than ten documents)"}
    if C["label"] == FAILS:
        same = order[C["j_mat"]] <= order[U["j_mat"]]
        return {"outcome": F_SAME if same else F_LATER, "gate": True, "C_first_material": C["j_mat"], "U_first_material": U["j_mat"]}
    if all(C["per_rung"][r]["interval"][1] < x for r in C["rungs"]):
        return {"outcome": H if C["label"] == HOLDS else D_BELOW, "gate": True}
    return {"outcome": D_UNRESOLVED, "gate": True, "sizes_reaching_X": [r for r in C["rungs"] if not C["per_rung"][r]["interval"][1] < x]}


# ----------------------------------------------------------------------------- the match ratio


def match_ratio_point(e_code_on_code: float, e_prose_on_code: float, e_prose_on_prose: float, e_code_on_prose: float) -> dict[str, float]:
    """r_code = e(C -> E^G) / e(P -> E^G); r_prose = e(P -> E^P) / e(C -> E^P); R = sqrt(r_code r_prose). NaN where a rise is not
    positive (R lives on the log scale)."""
    vals = np.asarray([e_code_on_code, e_prose_on_code, e_prose_on_prose, e_code_on_prose], dtype=np.float64)
    if not np.all(vals > 0):
        return {"r_code": float("nan"), "r_prose": float("nan"), "R": float("nan")}
    r_code, r_prose = vals[0] / vals[1], vals[2] / vals[3]
    return {"r_code": float(r_code), "r_prose": float(r_prose), "R": float(np.sqrt(r_code * r_prose))}


def r_reading(r_interval: list[float] | None, readable: bool) -> str:
    """Per size: matching helps if the interval lies below 0.8; closer is worse if it lies above 1.25; no material help if it lies
    above 0.8 and is not wholly above 1.25; otherwise unresolved at this size."""
    if not readable or r_interval is None or not np.all(np.isfinite(r_interval)):
        return NOT_READ
    lo, hi = r_interval
    if hi < R_HELPS_BELOW:
        return MATCHING_HELPS
    if lo > R_WORSE_ABOVE:
        return CLOSER_IS_WORSE
    if lo > R_HELPS_BELOW:
        return NO_MATERIAL_HELP
    return UNRESOLVED


def rises_all_above_zero(rise_intervals: dict[str, list[float]]) -> bool:
    """R's readability condition on the four rises: every interval's lower end above zero. An interval wholly below zero does
    not pass (it excludes zero, and a negative harm has no place in a ratio of harms), nor does a non-finite one."""
    return bool(rise_intervals) and all(bool(np.isfinite(iv[0]) and iv[0] > 0) for iv in rise_intervals.values())


def match_ratio(e_CG: np.ndarray, e_PG: np.ndarray, e_PP: np.ndarray, e_CP: np.ndarray, rs_G: st.Resample, rs_P: st.Resample, counts_C: np.ndarray, counts_P: np.ndarray, *,
                n_documents_G: int | None, n_documents_P: int | None, size_is_read: bool, m: int = R_M) -> dict[str, Any]:
    """R at one size with its two-level interval on log R: the code and prose strata resampled independently, the C and P draws
    resampled independently per pool and shared between the strata. R is read only if the size is one of the three read sizes,
    no replicate is non-finite, and the two-level interval of each of the four rises, at R's own level 1 - 0.05 / 3, has its
    lower end above zero (R is a ratio of harms, so a rise whose interval lies wholly *below* zero
    excludes zero and still must not be read)."""
    point = match_ratio_point(*(float(np.asarray(e, dtype=np.float64).mean(axis=0).mean()) for e in (e_CG, e_PG, e_PP, e_CP)))
    ok = has_interval(n_documents_G) and has_interval(n_documents_P)
    out: dict[str, Any] = {**point, "m": m, "n_documents": [n_documents_G, n_documents_P]}
    if not ok:
        return {**out, "interval": None, "rise_intervals": None, "nonfinite_share": None, "readable": False, "reading": NOT_READ}
    reps = {"C_G": rise_replicates(e_CG, rs_G, counts_C), "P_G": rise_replicates(e_PG, rs_G, counts_P), "P_P": rise_replicates(e_PP, rs_P, counts_P), "C_P": rise_replicates(e_CP, rs_P, counts_C)}
    with np.errstate(divide="ignore", invalid="ignore"):
        log_r = 0.5 * (np.log(reps["C_G"]) - np.log(reps["P_G"]) + np.log(reps["P_P"]) - np.log(reps["C_P"]))
    share = nonfinite_share(log_r)
    lo, hi = interval(log_r, m)
    rises = {k: interval(v, m) for k, v in reps.items()}
    all_above_zero = rises_all_above_zero(rises)
    readable = bool(size_is_read and share == 0.0 and all_above_zero and np.isfinite(point["R"]))
    r_iv = [float(np.exp(lo)), float(np.exp(hi))]
    return {**out, "interval": r_iv, "log_interval": [lo, hi], "rise_intervals": rises, "all_four_rises_above_zero": bool(all_above_zero), "nonfinite_share": share, "size_is_read": bool(size_is_read),
            "readable": readable, "reading": r_reading(r_iv, readable)}


# ----------------------------------------------------------------------------- the descriptions


def pool_contrast(e_a: np.ndarray, e_b: np.ndarray, resample: st.Resample, counts_a: np.ndarray | None, counts_b: np.ndarray | None, *, n_documents: int | None, m: int = 1) -> dict[str, Any]:
    """Two donor pools on the same texts: the difference of the mean rises and their ratio, two-level (each pool's draws resampled
    on its own; the texts or documents shared). The count of draws with a > b pairs the pools' draws by index: a sign check only."""
    ea, eb = np.asarray(e_a, dtype=np.float64), np.asarray(e_b, dtype=np.float64)
    a, b = float(ea.mean(axis=0).mean()), float(eb.mean(axis=0).mean())
    out: dict[str, Any] = {"a": a, "b": b, "difference": a - b, "ratio": a / b if b > 0 and a > 0 else float("nan"),
                           "n_draws_a_above_b_by_index": int((ea.mean(axis=1) > eb.mean(axis=1)).sum()) if ea.shape[0] == eb.shape[0] else None, "n_draws": [int(ea.shape[0]), int(eb.shape[0])]}
    if not has_interval(n_documents):
        return {**out, "difference_interval": None, "ratio_interval": None, "ratio_nonfinite_share": None}
    ra, rb = rise_replicates(ea, resample, counts_a), rise_replicates(eb, resample, counts_b)
    with np.errstate(divide="ignore", invalid="ignore"):
        log_ratio = np.log(ra) - np.log(rb)
    lo, hi = interval(log_ratio, m)
    return {**out, "difference_interval": interval(ra - rb, m), "ratio_interval": [float(np.exp(lo)), float(np.exp(hi))], "ratio_nonfinite_share": nonfinite_share(log_ratio)}


def per_unit_replicates(e: np.ndarray, sigma: np.ndarray, resample: st.Resample, counts: np.ndarray | None) -> np.ndarray:
    """Harm per unit of mask moved, h = e_hat / sigma_bar, a ratio of means recomputed within each replicate from the per-text
    `sigma` column (never n_on). e and sigma are (K, N)."""
    num, den = rise_replicates(e, resample, counts), rise_replicates(sigma, resample, counts)
    with np.errstate(divide="ignore", invalid="ignore"):
        return np.where(den > 0, num / np.where(den > 0, den, 1.0), np.nan)


def per_unit(e: np.ndarray, sigma: np.ndarray, resample: st.Resample, counts: np.ndarray | None, *, n_documents: int | None, m: int = 1) -> dict[str, Any]:
    e, sigma = np.asarray(e, dtype=np.float64), np.asarray(sigma, dtype=np.float64)
    s_bar = float(sigma.mean(axis=0).mean())
    out = {"e_hat": float(e.mean(axis=0).mean()), "sigma_bar": s_bar, "h": float(e.mean(axis=0).mean() / s_bar) if s_bar > 0 else float("nan")}
    if not has_interval(n_documents):
        return {**out, "interval": None, "nonfinite_share": None}
    reps = per_unit_replicates(e, sigma, resample, counts)
    return {**out, "interval": interval(reps, m), "nonfinite_share": nonfinite_share(reps)}


def per_unit_ratio(e_a: np.ndarray, sigma_a: np.ndarray, e_b: np.ndarray, sigma_b: np.ndarray, resample: st.Resample, counts_a: np.ndarray | None, counts_b: np.ndarray | None, *, n_documents: int | None, m: int = 1) -> dict[str, Any]:
    """h^a / h^b on the same texts, two-level."""
    ha, hb = per_unit(e_a, sigma_a, resample, counts_a, n_documents=None)["h"], per_unit(e_b, sigma_b, resample, counts_b, n_documents=None)["h"]
    out = {"h_a": ha, "h_b": hb, "ratio": ha / hb if hb > 0 and ha > 0 else float("nan")}
    if not has_interval(n_documents):
        return {**out, "interval": None, "nonfinite_share": None}
    with np.errstate(divide="ignore", invalid="ignore"):
        log_ratio = np.log(per_unit_replicates(e_a, sigma_a, resample, counts_a)) - np.log(per_unit_replicates(e_b, sigma_b, resample, counts_b))
    lo, hi = interval(log_ratio, m)
    return {**out, "interval": [float(np.exp(lo)), float(np.exp(hi))], "nonfinite_share": nonfinite_share(log_ratio)}


def lambda_contrast(e_CG: np.ndarray, e_UG: np.ndarray, e_CO: np.ndarray, e_UO: np.ndarray, rs_G: st.Resample, rs_O: st.Resample, counts_C: np.ndarray, counts_U: np.ndarray, *, m: int = 1) -> dict[str, Any]:
    """Lambda = log[e(C -> E^G) / e(U -> E^G)] - log[e(C -> E^O) / e(U -> E^O)]: whether code donors are relatively gentler on code
    texts than on the other texts. Two-level; the two strata resampled independently, each pool's draws shared between them."""
    pts = [float(np.asarray(e, dtype=np.float64).mean(axis=0).mean()) for e in (e_CG, e_UG, e_CO, e_UO)]
    point = float(np.log(pts[0] / pts[1]) - np.log(pts[2] / pts[3])) if all(p > 0 for p in pts) else float("nan")
    with np.errstate(divide="ignore", invalid="ignore"):
        reps = (np.log(rise_replicates(e_CG, rs_G, counts_C)) - np.log(rise_replicates(e_UG, rs_G, counts_U))) - (np.log(rise_replicates(e_CO, rs_O, counts_C)) - np.log(rise_replicates(e_UO, rs_O, counts_U)))
    return {"lambda": point, "interval": interval(reps, m), "nonfinite_share": nonfinite_share(reps)}


def control_against_arm(e_real: np.ndarray, e_control: np.ndarray, resample: st.Resample, counts: np.ndarray | None, *, n_documents: int | None, m: int = 1) -> dict[str, Any]:
    """A same-size random control against its own arm, and only its own: paired by draw (control
    draw k is matched to real draw k's counts per matrix) and resampled together with it, the same draw counts for both."""
    er, ec = np.asarray(e_real, dtype=np.float64), np.asarray(e_control, dtype=np.float64)
    assert er.shape == ec.shape, "a control is paired with its arm draw by draw"
    d = er - ec
    out = {"real": float(er.mean(axis=0).mean()), "control": float(ec.mean(axis=0).mean()), "difference": float(d.mean(axis=0).mean()), "n_draws_real_above_control": int((d.mean(axis=1) > 0).sum()), "n_draws": int(d.shape[0])}
    return {**out, "difference_interval": interval(rise_replicates(d, resample, counts), m) if has_interval(n_documents) else None}


# ----------------------------------------------------------------------------- the count-only prediction


def pav_nondecreasing(y: np.ndarray) -> np.ndarray:
    """The isotonic (non-decreasing) least-squares fit with equal weights, by pooling adjacent violators."""
    y = np.asarray(y, dtype=np.float64)
    vals: list[float] = []
    sizes: list[int] = []
    for v in y:
        vals.append(float(v))
        sizes.append(1)
        while len(vals) > 1 and vals[-2] > vals[-1]:
            n = sizes[-2] + sizes[-1]
            vals[-2:] = [(vals[-2] * sizes[-2] + vals[-1] * sizes[-1]) / n]
            sizes[-2:] = [n]
    return np.repeat(vals, sizes)


def yardstick_points(amounts: np.ndarray, rises: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Arm U's per-size points on the log-log scale: points with a rise that is not positive are skipped; sorted by amount; points
    of equal amount are one point (the mean log rise). Returns (log amounts, log rises)."""
    a, r = np.asarray(amounts, dtype=np.float64), np.asarray(rises, dtype=np.float64)
    keep = (r > 0) & (a > 0) & np.isfinite(r) & np.isfinite(a)
    a, r = a[keep], r[keep]
    order = np.argsort(a, kind="stable")
    la, lr = np.log(a[order]), np.log(r[order])
    ua, inv = np.unique(la, return_inverse=True)
    return ua, np.bincount(inv, weights=lr) / np.bincount(inv)


def yardstick_curve(amounts: np.ndarray, rises: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """`yardstick_points` with the log rises made non-decreasing in the amount by pooling adjacent violators: the knots of the
    log-log interpolation."""
    ua, lr = yardstick_points(amounts, rises)
    return ua, pav_nondecreasing(lr)


def predict_loglog(amount: np.ndarray, knots_log_a: np.ndarray, knots_log_r: np.ndarray, *, extend: bool) -> np.ndarray:
    """The predicted rise at each amount: linear in log-log between the knots. Outside the knots' range: NaN (no extrapolation)
    unless `extend`, which continues the end segments (used only inside bootstrap replicates, for draws whose amount lies within
    the measured range of the full data: a replicate's rebuilt curve moves its end points a little)."""
    x = np.log(np.asarray(amount, dtype=np.float64))
    if knots_log_a.size < 2:
        return np.full(x.shape, np.nan)
    y = np.interp(x, knots_log_a, knots_log_r)
    lo, hi = x < knots_log_a[0], x > knots_log_a[-1]
    if extend:
        s0 = (knots_log_r[1] - knots_log_r[0]) / (knots_log_a[1] - knots_log_a[0])
        s1 = (knots_log_r[-1] - knots_log_r[-2]) / (knots_log_a[-1] - knots_log_a[-2])
        y = np.where(lo, knots_log_r[0] + s0 * (x - knots_log_a[0]), np.where(hi, knots_log_r[-1] + s1 * (x - knots_log_a[-1]), y))
    else:
        y = np.where(lo | hi, np.nan, y)
    return np.exp(y)


def count_only_word(log_interval: list[float] | None, readable: bool) -> str:
    if not readable or log_interval is None or not np.all(np.isfinite(log_interval)):
        return NOT_READ
    return ABOVE if log_interval[0] > 0 else (BELOW if log_interval[1] < 0 else ON_IT)


def count_only(e_U: dict[str, np.ndarray], amount_U: dict[str, np.ndarray], e_C: dict[str, np.ndarray], amount_C: dict[str, np.ndarray], resample: st.Resample, counts_C: np.ndarray, *,
               sizes_read: tuple[str, ...] = COUNT_ONLY_SIZES, n_documents: int | None = None, m: int | None = None) -> dict[str, Any]:
    """Does arm C harm the code texts only through how much it switches on? Per size j, e_*[j] is the (K, N) rise matrix on the
    code texts and amount_*[j] the (K, N) per-text amount switched on (the `sigma` column, the primary measure; or the named
    count, constant over texts). Arm U's curve is its per-size points (mean amount, mean rise). Each C draw is predicted from its
    own mean amount and the predictions are averaged (the curve is convex); a draw outside U's measured range has no prediction,
    and the observed rise is averaged over the predicted draws. Reported: log(observed / prediction) per size, with a two-level
    interval at the read sizes (level 1 - 0.05 / their number) for a size with at least seven predicted draws. Within each
    replicate U's curve is rebuilt from all of U's draws on the resampled documents (U's draws are not resampled: they define
    the yardstick) and C's draws are resampled among the predicted ones; U's measured range and the set of predicted draws are
    fixed once from the full data. A replicate's rebuilt curve moves its end points a little, so a draw that had a prediction in
    the full data may fall just outside it; there the end segment is continued in log-log. `end_segment_continued_share`, at each
    read size: of the (replicate, draw) predictions that enter a replicate's statistic (a predicted draw that the replicate's draw
    resample holds at least once, each counted once), the share whose amount lay outside that replicate's knots."""
    m = m if m is not None else len(sizes_read)
    sizes = st.sort_rungs(list(e_U))
    assert set(amount_U) == set(e_U) and set(e_C) == set(amount_C)
    pts_a = np.asarray([float(np.asarray(amount_U[j], dtype=np.float64).mean()) for j in sizes])
    pts_r = np.asarray([float(np.asarray(e_U[j], dtype=np.float64).mean()) for j in sizes])
    knots_a, knots_r = yardstick_curve(pts_a, pts_r)
    raw_r = yardstick_points(pts_a, pts_r)[1]
    out: dict[str, Any] = {"U_points": [{"size": j, "amount": float(a), "rise": float(r), "used": bool(r > 0 and a > 0)} for j, a, r in zip(sizes, pts_a, pts_r)],
                           "U_curve": {"log_amount": knots_a.tolist(), "log_rise": raw_r.tolist(), "log_rise_isotonic": knots_r.tolist(), "violators_pooled": bool(not np.array_equal(raw_r, knots_r))},
                           "measured_range": [float(np.exp(knots_a[0])), float(np.exp(knots_a[-1]))] if knots_a.size else None, "m": m, "per_size": {}}
    # the replicate curves, once: U's per-size amounts and rises on the resampled documents, all of U's draws
    rep_a = np.stack([rise_replicates(amount_U[j], resample, None) for j in sizes], axis=1)  # (R, J)
    rep_r = np.stack([rise_replicates(e_U[j], resample, None) for j in sizes], axis=1)
    for j in st.sort_rungs(list(e_C)):
        eC, aC = np.asarray(e_C[j], dtype=np.float64), np.asarray(amount_C[j], dtype=np.float64)
        K = eC.shape[0]
        a_k, obs_k = aC.mean(axis=1), eC.mean(axis=1)
        pred_k = predict_loglog(a_k, knots_a, knots_r, extend=False)
        has = np.isfinite(pred_k)
        n_pred = int(has.sum())
        row: dict[str, Any] = {"n_draws": K, "n_draws_predicted": n_pred, "amount_per_draw": a_k.tolist(), "prediction_per_draw": pred_k.tolist(), "observed_per_draw": obs_k.tolist()}
        if n_pred == 0:
            out["per_size"][j] = {**row, "prediction": None, "observed": None, "log_ratio": None, "interval": None, "nonfinite_share": None, "readable": False, "reading": NOT_READ}
            continue
        prediction, observed = float(pred_k[has].mean()), float(obs_k[has].mean())
        log_ratio = float(np.log(observed / prediction)) if observed > 0 and prediction > 0 else float("nan")
        row.update({"prediction": prediction, "observed": observed, "log_ratio": log_ratio})
        read_here = j in sizes_read
        if not read_here or not has_interval(n_documents):
            out["per_size"][j] = {**row, "interval": None, "nonfinite_share": None, "readable": False, "reading": NOT_READ}
            continue
        rep_ak, rep_ok = ratio_means(resample, aC), ratio_means(resample, eC)  # (R, K) each
        w = (counts_C if K > 1 else np.ones((resample.replicates, 1))) * has[None, :]  # C's draws resampled among the predicted ones
        stats = np.full(resample.replicates, np.nan)
        n_pairs = n_continued = 0  # how much of the interval rests on the continued end segment
        for r in range(resample.replicates):
            if w[r].sum() <= 0:
                continue
            ka, kr = yardstick_curve(rep_a[r], rep_r[r])
            p = predict_loglog(rep_ak[r][has], ka, kr, extend=True)
            wr = w[r][has]
            pr, ob = float((wr * p).sum() / wr.sum()), float((wr * rep_ok[r][has]).sum() / wr.sum())
            stats[r] = np.log(ob / pr) if ob > 0 and pr > 0 and np.isfinite(pr) else np.nan
            if ka.size >= 2:
                x = np.log(rep_ak[r][has])
                n_pairs += int((wr > 0).sum())
                n_continued += int((((x < ka[0]) | (x > ka[-1])) & (wr > 0)).sum())
        share = nonfinite_share(stats)
        iv = interval(stats, m)
        readable = bool(n_pred >= COUNT_ONLY_MIN_DRAWS and share == 0.0 and np.isfinite(log_ratio))
        out["per_size"][j] = {**row, "interval": iv, "nonfinite_share": share, "readable": readable, "reading": count_only_word(iv, readable),
                              "end_segment_continued_share": float(n_continued / n_pairs) if n_pairs else float("nan"), "n_replicate_draw_predictions": n_pairs}
    return out


# ----------------------------------------------------------------------------- the self-merge and the ladder


def self_merge_rule(s: np.ndarray, resample: st.Resample, *, n_documents: int | None = None, m: int = SELF_M, x: float = X, s_against_rounded: np.ndarray | None = None) -> dict[str, Any]:
    """s_b is text b's rise under the self-merge. Material if the lower end of the interval of s_hat at level 1 - 0.05 / m exceeds
    0.05 (no draws, so no sign condition). Beside it: the share of texts made worse with its interval, the shares above 0.05, 0.1,
    0.2, five percentiles, and the rise over the text's rounded-labels reference as a second baseline."""
    s = np.asarray(s, dtype=np.float64)
    out: dict[str, Any] = {"s_hat": float(s.mean()), "n_texts": int(s.size), "n_documents": n_documents, "m": m, "share_made_worse": float((s > 0).mean()),
                           "share_above": {str(t): float((s > t).mean()) for t in (0.05, 0.1, 0.2)}, "percentiles": {str(p): float(np.percentile(s, p)) for p in (5, 25, 50, 75, 95)}}
    if s_against_rounded is not None:
        out["s_hat_against_rounded_labels"] = float(np.asarray(s_against_rounded, dtype=np.float64).mean())
    if not has_interval(n_documents):
        return {**out, "interval": None, "material": None, "share_made_worse_interval": None}
    iv = interval(ratio_means(resample, s), m)
    out.update({"interval": iv, "material": bool(iv[0] > x), "share_made_worse_interval": interval(ratio_means(resample, (s > 0).astype(np.float64)), m)})
    if s_against_rounded is not None:
        out["s_hat_against_rounded_labels_interval"] = interval(ratio_means(resample, np.asarray(s_against_rounded, dtype=np.float64)), m)
    return out


def self_against_stranger(s: np.ndarray, x_shifts: np.ndarray, resample: st.Resample, *, sigma_self: np.ndarray, sigma_shifts: np.ndarray) -> dict[str, Any]:
    """On E: x_b is the mean over the shifts of text b's rise under a partner's set; delta_b = s_b - x_b, 95 percent interval. And
    the same contrast per unit of mask moved, s_hat / sigma_self - x_hat / sigma_stranger, each a ratio of means recomputed
    within each replicate from the per-text sigma column."""
    s, xs = np.asarray(s, dtype=np.float64), np.asarray(x_shifts, dtype=np.float64)
    assert xs.ndim == 2 and xs.shape[1] == s.size
    x_text = xs.mean(axis=0)
    delta = s - x_text
    iv = interval(ratio_means(resample, delta), 1)
    word = SELF_WORSE if iv[0] > 0 else (SELF_LESS if iv[1] < 0 else SELF_NO_BETTER)
    sig_s, sig_x = np.asarray(sigma_self, dtype=np.float64), np.asarray(sigma_shifts, dtype=np.float64).mean(axis=0)
    rs, rx, rss, rsx = (ratio_means(resample, v) for v in (s, x_text, sig_s, sig_x))
    with np.errstate(divide="ignore", invalid="ignore"):
        per_unit_reps = rs / rss - rx / rsx
    return {"s_hat": float(s.mean()), "x_hat": float(x_text.mean()), "delta_hat": float(delta.mean()), "interval": iv, "reading": word, "share_delta_positive": float((delta > 0).mean()),
            "per_unit": {"self": float(s.mean() / sig_s.mean()), "stranger": float(x_text.mean() / sig_x.mean()), "difference": float(s.mean() / sig_s.mean() - x_text.mean() / sig_x.mean()),
                         "interval": interval(per_unit_reps, 1), "nonfinite_share": nonfinite_share(per_unit_reps)}}


def ladder_rung(rise_shifts: np.ndarray, qualifies: np.ndarray, resample: st.Resample, *, n_documents: int | None, m: int = LADDER_M, x: float = X, count_shifts: np.ndarray | None = None) -> dict[str, Any]:
    """One rung of the closeness ladder on one source: `rise_shifts` (S, N) is each text's rise under each shift's partner,
    `qualifies` (S, N) says which (shift, text) pairs belong to the rung (the partner in the text's document; in another
    document of its source; any general partner). A text's qualifying shifts are averaged first, then the texts that have at
    least one; both counts are reported. The interval resamples documents, in ratio form over the qualifying texts. Standing:
    material (lower end above 0.05), wholly under 0.05 (upper end strictly below it), or neither; and none at all where any
    replicate is non-finite (the interval is then printed with a flag). `count_shifts` (S, N): the named count each text receives,
    so that the rung prints its own mean count (these rungs are not balanced as the rotation is)."""
    e, q = np.asarray(rise_shifts, dtype=np.float64), np.asarray(qualifies, dtype=bool)
    assert e.shape == q.shape and e.ndim == 2
    n_q = q.sum(axis=0)
    has = n_q > 0
    per_text = np.where(has, np.where(q, e, 0.0).sum(axis=0) / np.maximum(n_q, 1), 0.0)
    out: dict[str, Any] = {"n_texts": int(has.sum()), "n_text_shift_pairs": int(q.sum()), "n_documents": n_documents, "m": m, "mean_rise": float(per_text[has].mean()) if has.any() else float("nan")}
    if count_shifts is not None:
        c = np.asarray(count_shifts, dtype=np.float64)
        per_text_c = np.where(has, np.where(q, c, 0.0).sum(axis=0) / np.maximum(n_q, 1), 0.0)
        out["mean_count"] = float(per_text_c[has].mean()) if has.any() else float("nan")
    if not has_interval(n_documents) or not has.any():
        return {**out, "interval": None, "standing": None, "nonfinite_share": None, "interval_flag": ""}
    reps = resample.ratios(per_text, has.astype(np.float64))  # NaN for a replicate that drew no qualifying text
    iv = interval(reps, m)
    share = nonfinite_share(reps)
    # a rung with any non-finite replicate prints its value, its counts, and its flagged interval, and
    # gets no standing (`percentile_interval` silently drops such replicates); the same rule as for R and the count-only prediction
    standing = None if share > 0 else (MATERIAL if iv[0] > x else (UNDER if iv[1] < x else None))
    return {**out, "interval": iv, "standing": standing, "nonfinite_share": share, "interval_flag": NONFINITE_FLAG if share > 0 else ""}


def scope_rule(standing_by_source: dict[str, str | None], *, needed: int = 4) -> dict[str, Any]:
    """The post may say "within one kind of text" only if the same-source, other-document partner's rise has the same standing
    (material, or interval wholly under 0.05) on at least four of the five sources; otherwise it names the sources. A source with
    fewer than ten documents has no interval and so no standing: with one such source, all four readable ones are needed."""
    counts = {w: [s for s, v in standing_by_source.items() if v == w] for w in (MATERIAL, UNDER)}
    best = max(counts, key=lambda w: len(counts[w]))
    ok = len(counts[best]) >= needed
    return {"within_one_kind_of_text": bool(ok), "standing": best if ok else None, "sources_by_standing": counts, "sources_without_standing": [s for s, v in standing_by_source.items() if v not in (MATERIAL, UNDER)], "needed": needed}


# ----------------------------------------------------------------------------- the plain-terms tables


def change_rates_excluding_ties(top: np.ndarray, target_top: np.ndarray, target_tie: np.ndarray, target_top_p: np.ndarray, *, confident: float = 0.5) -> dict[str, np.ndarray]:
    """Per text, from the per-position arrays of a listed cell: the numbers of positions that enter and that
    changed, with the target's tied positions excluded, for all positions and for the confident ones (P(a) >= 0.5); and the same
    with ties included, which must reproduce the stored per-text columns (the gate)."""
    changed, tie, conf = np.asarray(top) != np.asarray(target_top), np.asarray(target_tie, dtype=bool), np.asarray(target_top_p) >= confident
    return {"n": (~tie).sum(axis=1), "n_changed": (changed & ~tie).sum(axis=1), "n_confident": (conf & ~tie).sum(axis=1), "n_changed_confident": (changed & conf & ~tie).sum(axis=1),
            "n_tied": tie.sum(axis=1), "rate_with_ties": changed.mean(axis=1).astype(np.float32), "n_confident_with_ties": conf.sum(axis=1), "n_changed_confident_with_ties": (changed & conf).sum(axis=1)}


def rate_of_sums(numerator: np.ndarray, denominator: np.ndarray, resample: st.Resample, *, m: int = 1) -> dict[str, Any]:
    """A rate as a ratio of sums over texts (a text with three positions must not weigh as one with three hundred), with its
    text-bootstrap interval, every sum recomputed within each replicate."""
    num, den = np.asarray(numerator, dtype=np.float64), np.asarray(denominator, dtype=np.float64)
    reps = resample.ratios(num, den)
    return {"rate": float(num.sum() / den.sum()) if den.sum() > 0 else float("nan"), "interval": interval(reps, m), "nonfinite_share": nonfinite_share(reps), "n_positions": float(den.sum())}


def rate_of_sums_rise(numerator: np.ndarray, denominator: np.ndarray, base_numerator: np.ndarray, base_denominator: np.ndarray, resample: st.Resample, *, m: int = 1) -> dict[str, Any]:
    """The paired rise of a rate over its baseline's on the same texts, both as ratios of sums over texts: within each replicate
    the two rates are recomputed from the same resampled texts and subtracted. No change rate is printed without its baseline."""
    num, den = np.asarray(numerator, dtype=np.float64), np.asarray(denominator, dtype=np.float64)
    num0, den0 = np.asarray(base_numerator, dtype=np.float64), np.asarray(base_denominator, dtype=np.float64)
    assert num.shape == den.shape == num0.shape == den0.shape == (resample.n,), (num.shape, den.shape, num0.shape, den0.shape, resample.n)
    reps = resample.ratios(num, den) - resample.ratios(num0, den0)
    rate, base = (float(num.sum() / den.sum()) if den.sum() > 0 else float("nan")), (float(num0.sum() / den0.sum()) if den0.sum() > 0 else float("nan"))
    return {"rate": rate, "baseline": base, "rise": rate - base, "rise_interval": interval(reps, m), "nonfinite_share": nonfinite_share(reps)}


def confident_counts_from_columns(rate_confident: np.ndarray, n_confident: np.ndarray) -> np.ndarray:
    """For a cell that keeps no per-position arrays: the number of changed confident positions per text, recovered exactly as the
    stored per-text rate times the text's count of confident positions (from the stored target__top_p); a text with no confident
    position has a NaN rate and contributes nothing."""
    rate, n = np.asarray(rate_confident, dtype=np.float64), np.asarray(n_confident, dtype=np.int64)
    k = np.where(n > 0, np.rint(np.where(n > 0, rate, 0.0) * n), 0.0)
    assert np.all(np.abs(np.where(n > 0, rate * n, 0.0) - k) < 1e-3 * np.maximum(n, 1)), "a stored rate times its count must be a whole number of positions (to float32 rounding)"
    return k.astype(np.int64)


def paired_mean(v: np.ndarray, baseline: np.ndarray | None, resample: st.Resample, *, m: int = 1) -> dict[str, Any]:
    """A per-text column's mean with its text-bootstrap interval and, with a baseline on the same texts, the paired rise over it."""
    v = np.asarray(v, dtype=np.float64)
    out = {"mean": float(v.mean()), "interval": interval(ratio_means(resample, v), m)}
    if baseline is not None:
        d = v - np.asarray(baseline, dtype=np.float64)
        out.update({"baseline": float(np.asarray(baseline, dtype=np.float64).mean()), "rise": float(d.mean()), "rise_interval": interval(ratio_means(resample, d), m)})
    return out


def bin_table(kl: np.ndarray, changed: np.ndarray, p_target_top: np.ndarray, *, exclude: np.ndarray | None = None, edges: tuple[float, ...] = DIVERGENCE_BINS) -> list[dict[str, Any]]:
    """Change rate and probability retained by bin of per-position divergence (under 0.05, 0.05 to 0.2, 0.2 to 0.5, 0.5 to 1, 1 to
    2, over 2); positions flagged in `exclude` (the target's ties) are left out. A bin's lower edge belongs to it."""
    k, c, p = np.asarray(kl, dtype=np.float64).reshape(-1), np.asarray(changed, dtype=bool).reshape(-1), np.asarray(p_target_top, dtype=np.float64).reshape(-1)
    keep = np.isfinite(k) if exclude is None else (np.isfinite(k) & ~np.asarray(exclude, dtype=bool).reshape(-1))
    idx = np.digitize(k, np.asarray(edges), right=False)
    bounds = [float("-inf")] + list(edges) + [float("inf")]
    return [{"bin": i, "from": bounds[i], "to": bounds[i + 1], "n_positions": int((keep & (idx == i)).sum()),
             "change_rate": float(c[keep & (idx == i)].mean()) if (keep & (idx == i)).any() else float("nan"), "mean_p_target_top": float(p[keep & (idx == i)].mean()) if (keep & (idx == i)).any() else float("nan")} for i in range(len(edges) + 1)]


def pool_bin_tables(tables: list[list[dict[str, Any]]]) -> list[dict[str, Any]]:
    """`bin_table` over several masks pooled, from the per-mask tables (the pooled arrays of the paper's run would be some forty
    million positions): per bin the positions add, and the change rate and the mean probability are the position-weighted means,
    which is what `bin_table` of the concatenated arrays gives."""
    assert tables and all(len(t) == len(tables[0]) and [(r["from"], r["to"]) for r in t] == [(r["from"], r["to"]) for r in tables[0]] for t in tables), "the tables must share their bins"
    out = []
    for i, first in enumerate(tables[0]):
        n = np.asarray([t[i]["n_positions"] for t in tables], dtype=np.float64)
        rate = np.asarray([t[i]["change_rate"] if t[i]["n_positions"] else 0.0 for t in tables], dtype=np.float64)
        p = np.asarray([t[i]["mean_p_target_top"] if t[i]["n_positions"] else 0.0 for t in tables], dtype=np.float64)
        tot = float(n.sum())
        out.append({"bin": first["bin"], "from": first["from"], "to": first["to"], "n_positions": int(tot), "change_rate": float((n * rate).sum() / tot) if tot else float("nan"),
                    "mean_p_target_top": float((n * p).sum() / tot) if tot else float("nan")})
    return out


def choose_examples(kl_all: np.ndarray, positions: np.ndarray, eligible: np.ndarray, *, percentiles: tuple[float, ...] = EXAMPLE_PERCENTILES, n_written: int = EXAMPLES_WRITTEN) -> list[dict[str, Any]]:
    """Examples by rule, never by eye. `kl_all` (N, T) is the chosen mask's per-position divergence; its percentiles are taken over
    all positions. `positions` (N, P) are the stored example positions and `eligible` (N, P) the content-blind filter (the 48
    context tokens decode without replacement characters). For each percentile: among the eligible stored positions, the one
    whose divergence is nearest the percentile's value (ties to the lowest text index, then position) is shown, and the
    `n_written` nearest are written out."""
    kl_all, positions, eligible = np.asarray(kl_all, dtype=np.float64), np.asarray(positions, dtype=np.int64), np.asarray(eligible, dtype=bool)
    at = np.take_along_axis(kl_all, positions, axis=1)
    seq = np.broadcast_to(np.arange(positions.shape[0])[:, None], positions.shape)
    cand = np.flatnonzero(eligible.reshape(-1) & np.isfinite(at.reshape(-1)))
    out = []
    for q in percentiles:
        target = float(np.percentile(kl_all[np.isfinite(kl_all)], q))
        d = np.abs(at.reshape(-1)[cand] - target)
        order = cand[np.lexsort((positions.reshape(-1)[cand], seq.reshape(-1)[cand], d))][:n_written]
        out.append({"percentile": q, "value": target, "nearest": [{"seq": int(seq.reshape(-1)[i]), "position": int(positions.reshape(-1)[i]), "kl": float(at.reshape(-1)[i])} for i in order]})
    return out


def yardstick_ratios(absolute: dict[str, float], to_comparison_model: float) -> dict[str, float]:
    """The ratios the post will quote: the absolute divergence on E of own labels, of the 64-token merge, of the one-text merge, of
    the self-merge, and of the never-named removal, each divided by the divergence to the primary comparison model."""
    assert to_comparison_model > 0
    return {k: float(v) / float(to_comparison_model) for k, v in absolute.items()}
