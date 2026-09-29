"""Known-answer tests of the tier-5 reading rules (vpd_audit/stats_s9.py) on planted values. Each of the
five run-2 outcomes and *no reading*; R = 0.5 and 1.0 from the worked examples fixed in advance, with readings on each side of 0.8 and
1.25; a document bootstrap wider than the row bootstrap when rows of a document are identical, and of zero width when every row
is; the self-merge rule at its boundary; the scope rule at three and at four of five sources; the count-only reading on a planted
power law (on it) and on twice that (above)."""

import numpy as np
import pytest

from vpd_audit import stats as st
from vpd_audit import stats_s9 as s9
from vpd_audit.s9_checks import doc_means, document_resample

R = 2000


def const(value, K=8, N=40):
    return np.full((K, N), float(value))


def text_resample(n, seed="t"):
    return st.Resample.make(n, R, (0, "boot", seed))


# ----------------------------------------------------------------------------- the intervals


def test_ratio_form_is_the_frozen_mean_on_texts_and_the_document_mean_on_documents():
    rng = np.random.default_rng(0)
    v, M = rng.normal(size=30), rng.normal(size=(4, 30))
    rs = text_resample(30)
    assert np.array_equal(s9.ratio_means(rs, v), rs.means(v)) and np.array_equal(s9.ratio_means(rs, M), rs.means(M))  # every replicate holds n rows
    docs = np.repeat(np.arange(10), 3)
    rd = document_resample(docs, R, (0, "boot_docs", "x"))
    assert np.array_equal(s9.ratio_means(rd, v), doc_means(rd, v)) and np.all(rd.W.sum(axis=1) == 30)  # documents of equal size: the row count is still 30 in every replicate
    unequal = document_resample(np.array([0] * 12 + [1] * 3 + list(range(2, 17))), R, (0, "boot_docs", "y"))
    assert not np.all(unequal.W.sum(axis=1) == 30) and not np.allclose(s9.ratio_means(unequal, v), unequal.means(v))  # Resample.means would divide a varying row total by the fixed n


def test_identical_rows_give_zero_width_and_identical_rows_within_documents_a_wider_interval_than_rows():
    docs = np.array([0] * 12 + [1] * 3 + list(range(2, 17)))  # documents of unequal size, so the resampled row count varies
    rd = document_resample(docs, R, (0, "boot_docs", "z"))
    same = np.full((8, 30), 0.123)
    curve = s9.union_curve_s9({"2": same, "3": same * 2}, rd, n_documents=17)
    for r in ("2", "3"):
        lo, hi = curve["per_rung"][r]["interval"]
        assert lo == pytest.approx(curve["per_rung"][r]["e_hat"], abs=1e-15) and hi - lo < 1e-15  # the test fixed in advance: all rows identical, zero width
    lo_bad, hi_bad = st.percentile_interval(rd.means(same[0]), 2)
    assert hi_bad - lo_bad > 0.01  # what the frozen form would have given: a total over a fixed n
    # rows of one document identical, documents differing: resampling documents is wider than resampling rows
    rng = np.random.default_rng(1)
    docs2 = np.repeat(np.arange(12), 10)
    per_doc = rng.normal(0.1, 0.05, size=12)
    e = np.tile(per_doc[docs2], (8, 1))
    wide = s9.union_rung_s9(e, document_resample(docs2, R, (0, "boot_docs", "w")), 1, n_documents=12)["interval"]
    narrow = s9.union_rung_s9(e, text_resample(120, "rows"), 1)["interval"]
    assert (wide[1] - wide[0]) > 2.5 * (narrow[1] - narrow[0])
    # fewer than ten documents: the point value and the count, no interval, no label
    few = s9.union_curve_s9({"3": e[:, :30]}, document_resample(docs2[:30], R, (0, "boot_docs", "f")), n_documents=3)
    assert few["label"] is None and few["per_rung"]["3"]["interval"] is None and few["per_rung"]["3"]["e_hat"] == pytest.approx(e[:, :30].mean()) and few["per_rung"]["3"]["n_documents"] == 3
    assert s9.has_interval(None) and s9.has_interval(10) and not s9.has_interval(9)


def test_the_stratified_document_resample_is_the_document_resample_within_each_source():
    docs = np.array([0, 0, 0, 1, 1, 2, 3, 3, 4, 5, 5, 5, 5])  # source a: documents 0, 1, 2 (six rows); source b: documents 3, 4, 5 (seven rows)
    src = np.array(["a"] * 6 + ["b"] * 7)
    seed = lambda s: (0, "boot_docs", "E_lab", s)  # noqa: E731
    rs = s9.stratified_document_resample(docs, src, R, seed)
    one = s9.stratified_document_resample(docs[:6], src[:6], R, seed)
    assert np.array_equal(one.W, document_resample(docs[:6], R, seed("a")).W)  # a stratum of one source is document_resample of that source, bit for bit
    assert np.array_equal(rs.W[:, :6], one.W) and np.array_equal(rs.W[:, 6:], document_resample(docs[6:], R, seed("b")).W) and rs.n == 13  # pooled: each source's block is its own resample
    assert (rs.W[:, [0, 3, 5]].sum(axis=1) == 3).all() and (rs.W[:, [6, 8, 9]].sum(axis=1) == 3).all()  # every replicate draws, in each source, as many documents as the source has
    assert np.array_equal(rs.W[:, 0], rs.W[:, 2]) and np.array_equal(rs.W[:, 9], rs.W[:, 12])  # all rows of a drawn document enter together
    flat = document_resample(docs, R, (0, "boot_docs", "flat"))
    assert not (flat.W[:, [0, 3, 5]].sum(axis=1) == 3).all()  # which one resample of the six documents does not do
    assert isinstance(rs, s9.StratifiedResample) and rs.block_names == ("a", "b") and [b.tolist() for b in rs.blocks] == [list(range(6)), list(range(6, 13))]
    # the columns follow the rows when the sources are interleaved
    mixed = s9.stratified_document_resample(np.array([0, 3, 0, 3, 1, 4]), np.array(["a", "b", "a", "b", "a", "b"]), R, seed)
    assert np.array_equal(mixed.W[:, [0, 2, 4]], document_resample(np.array([0, 0, 1]), R, seed("a")).W) and np.array_equal(mixed.W[:, [1, 3, 5]], document_resample(np.array([3, 3, 4]), R, seed("b")).W)
    with pytest.raises(AssertionError, match="spans"):
        s9.stratified_document_resample(np.array([0, 0, 1]), np.array(["a", "b", "b"]), 10, seed)


UNEQUAL_DOCS = np.array([0] * 9 + [1] + [2] * 5 + [3] * 3 + [4] * 2 + [5] * 12 + [6] * 2 + [7] + [8] * 4 + [9])  # two sources of five documents each, of very unequal size (20 rows each)
UNEQUAL_SRC = np.array(["a"] * 20 + ["b"] * 20)
SEED = lambda s: (0, "boot_docs", "E_lab", s)  # noqa: E731


def test_pooled_sources_keep_their_design_weights_in_every_replicate():
    # each source keeps its fixed row share in every replicate; the test: two sources with constant, different values give an interval of zero width
    rs = s9.stratified_document_resample(UNEQUAL_DOCS, UNEQUAL_SRC, R, SEED)
    v = np.where(UNEQUAL_SRC == "a", 0.02, 0.30)
    reps = s9.ratio_means(rs, v)
    assert np.ptp(reps) < 1e-15 and reps[0] == pytest.approx(0.16)
    out = s9.union_rung_s9(np.tile(v, (8, 1)), rs, 10, n_documents=10)
    assert out["interval"] == pytest.approx([0.16, 0.16], abs=1e-15) and out["e_hat"] == pytest.approx(0.16)
    # what pooling the resampled rows across sources gives on the same count matrix: the mix moves with the length of the documents drawn, and the interval has width
    pooled_rows = st.Resample(n=rs.n, replicates=rs.replicates, seed_tuple=("pooled",), W=rs.W)
    assert np.ptp(s9.ratio_means(pooled_rows, v)) > 0.05 and not np.all(rs.W[:, :20].sum(axis=1) == rs.W[:, 20:].sum(axis=1))
    # the point estimate is unchanged: with every row drawn once, the stratified form is the plain mean over rows, and a ratio of sums is the pooled ratio
    rng = np.random.default_rng(12)
    x, num, den = rng.normal(size=40), rng.integers(0, 50, size=40).astype(float), rng.integers(50, 500, size=40).astype(float)
    once = s9.StratifiedResample(n=40, replicates=2, seed_tuple=("once",), W=np.ones((2, 40), dtype=np.int32), blocks=rs.blocks, block_names=rs.block_names)
    assert s9.ratio_means(once, x) == pytest.approx([x.mean()] * 2, abs=1e-15) and once.ratios(num, den) == pytest.approx([num.sum() / den.sum()] * 2, abs=1e-15)
    unequal = s9.stratified_document_resample(UNEQUAL_DOCS[:31], np.array(["a"] * 20 + ["b"] * 11), R, SEED)  # sources of 20 and 11 rows: the weights are the row shares, not one half each
    assert s9.ratio_means(unequal, np.where(np.arange(31) < 20, 0.02, 0.30))[:3] == pytest.approx([(20 * 0.02 + 11 * 0.30) / 31] * 3, abs=1e-15)
    # per source it is the ratio form of document_resample of that source, combined with the fixed row shares; a matrix gives the same as its rows
    a, b = document_resample(UNEQUAL_DOCS[:20], R, SEED("a")), document_resample(UNEQUAL_DOCS[20:], R, SEED("b"))
    assert np.allclose(s9.ratio_means(rs, x), 0.5 * doc_means(a, x[:20]) + 0.5 * doc_means(b, x[20:]), rtol=0, atol=1e-15)
    M = rng.normal(size=(3, 40))
    assert np.allclose(s9.ratio_means(rs, M), np.stack([s9.ratio_means(rs, M[i]) for i in range(3)], axis=1), rtol=0, atol=1e-15)  # (a matrix product may differ from a vector product in the last place)
    # one source: document_resample's replicates, bit for bit
    single = s9.stratified_document_resample(UNEQUAL_DOCS[:20], UNEQUAL_SRC[:20], R, SEED)
    assert np.array_equal(s9.ratio_means(single, x[:20]), doc_means(a, x[:20])) and np.array_equal(single.ratios(num[:20], den[:20]), a.ratios(num[:20], den[:20]))
    with pytest.raises(AssertionError, match="never be called on a document resample"):
        rs.means(x)
    with pytest.raises(AssertionError, match="tile"):
        s9.StratifiedResample(n=40, replicates=2, seed_tuple=("bad",), W=np.ones((2, 40), dtype=np.int32), blocks=(np.arange(20),), block_names=("a",))


def test_the_draw_table_is_shared_across_the_sources_of_a_pooled_stratum_and_R_takes_the_stratified_form():
    rs = s9.stratified_document_resample(UNEQUAL_DOCS, UNEQUAL_SRC, R, SEED)
    rng = np.random.default_rng(13)
    e = rng.normal(0.1, 0.05, size=(8, 40)) + np.linspace(-0.05, 0.05, 8)[:, None]  # the draws differ, so the draw table matters
    counts = s9.draw_counts(8, R, (0, "boot_draws", "D_prose"))
    a, b = s9.stratified_document_resample(UNEQUAL_DOCS[:20], UNEQUAL_SRC[:20], R, SEED), s9.stratified_document_resample(UNEQUAL_DOCS[20:], UNEQUAL_SRC[20:], R, SEED)
    want = 0.5 * s9.rise_replicates(e[:, :20], a, counts) + 0.5 * s9.rise_replicates(e[:, 20:], b, counts)  # one table for both sources: in a replicate every source sees the same resampled draws
    assert np.allclose(s9.rise_replicates(e, rs, counts), want, rtol=0, atol=1e-15)
    other = 0.5 * s9.rise_replicates(e[:, :20], a, counts) + 0.5 * s9.rise_replicates(e[:, 20:], b, s9.draw_counts(8, R, (0, "boot_draws", "other")))
    assert not np.allclose(s9.rise_replicates(e, rs, counts), other, rtol=0, atol=1e-6)
    # E^P inside R is two sources: with constant, different rises per source, the prose stratum's replicates do not move, and neither does R
    rs_G = document_resample(np.arange(40), R, (0, "boot_docs", "G"))
    cC, cP = s9.draw_counts(8, R, (0, "boot_draws", "D_code")), s9.draw_counts(8, R, (0, "boot_draws", "D_prose"))
    e_PP, e_CP = np.tile(np.where(UNEQUAL_SRC == "a", 0.010, 0.020), (8, 1)), np.tile(np.where(UNEQUAL_SRC == "a", 0.030, 0.060), (8, 1))  # means 0.015 and 0.045: the worked example fixed in advance
    out = s9.match_ratio(const(0.045), const(0.060), e_PP, e_CP, rs_G, rs, cC, cP, n_documents_G=40, n_documents_P=10, size_is_read=True)
    assert out["R"] == pytest.approx(0.5) and out["interval"] == pytest.approx([0.5, 0.5], abs=1e-12) and out["reading"] == s9.MATCHING_HELPS
    pooled_rows = st.Resample(n=40, replicates=R, seed_tuple=("pooled",), W=rs.W)
    wide = s9.match_ratio(const(0.045), const(0.060), e_PP, e_CP, rs_G, pooled_rows, cC, cP, n_documents_G=40, n_documents_P=10, size_is_read=True)
    assert wide["rise_intervals"]["P_P"][1] - wide["rise_intervals"]["P_P"][0] > 0.002  # the form this replaces: the two rises' intervals have width from the mix alone


def test_a_ratio_of_sums_on_pooled_sources_and_a_source_with_no_qualifying_text():
    rs = s9.stratified_document_resample(UNEQUAL_DOCS, UNEQUAL_SRC, R, SEED)
    den = np.where(UNEQUAL_SRC == "a", 300.0, 30.0)  # source a has ten times the confident positions
    num = np.where(UNEQUAL_SRC == "a", 0.10, 0.50) * den  # a constant rate per source: 0.10 and 0.50
    out = s9.rate_of_sums(num, den, rs)
    assert out["rate"] == pytest.approx((0.10 * 300 + 0.50 * 30) / 330) and out["interval"] == pytest.approx([out["rate"]] * 2, abs=1e-15) and out["nonfinite_share"] == 0.0  # the weights are the sources' shares of the denominator: the pooled rate, unmoved
    rise = s9.rate_of_sums_rise(num, den, 0.5 * num, den, rs)
    assert rise["rise"] == pytest.approx(out["rate"] / 2) and rise["rise_interval"] == pytest.approx([out["rate"] / 2] * 2, abs=1e-15)
    # a ladder rung whose qualifying texts all lie in one source: the other source's share is zero and it contributes nothing, in the point value and in every replicate
    q = np.zeros((4, 40), dtype=bool)
    q[:, :20] = True
    rung = s9.ladder_rung(np.tile(np.where(UNEQUAL_SRC == "a", 0.06, 9.0), (4, 1)), q, rs, n_documents=10)
    assert rung["n_texts"] == 20 and rung["mean_rise"] == pytest.approx(0.06) and rung["interval"] == pytest.approx([0.06, 0.06]) and rung["nonfinite_share"] == 0.0 and rung["standing"] == s9.MATERIAL


def test_the_twin_is_the_frozen_union_curve_on_a_text_resample():
    rng = np.random.default_rng(2)
    rungs = {r: rng.normal(mu, 0.05, size=(1 if r == "8" else 8, 60)) for r, mu in (("1", 0.0), ("2", 0.02), ("2a", 0.03), ("2b", 0.05), ("3", 0.09), ("4", 0.1), ("5", 0.2), ("6", 0.3), ("7", 0.4), ("8", 0.5))}
    rs = text_resample(60, "twin")
    a, b = st.union_curve(rungs, "union", rs), s9.union_curve_s9(rungs, rs)
    assert a["rungs"] == b["rungs"] == ["1", "2", "2a", "2b", "3", "4", "5", "6", "7", "8"] and b["m"] == 10  # all ten sizes compared
    assert a["label"] == b["label"] and a["j_det"] == b["j_det"] and a["j_mat"] == b["j_mat"]
    for r in a["rungs"]:
        assert a["per_rung"][r]["interval"] == b["per_rung"][r]["interval"] and a["per_rung"][r]["detected"] == b["per_rung"][r]["detected"] and a["per_rung"][r]["material"] == b["per_rung"][r]["material"]
        assert a["per_rung"][r]["e_hat"] == b["per_rung"][r]["e_hat"] and a["per_rung"][r]["sign_condition"] == b["per_rung"][r]["sign_condition"]
    # the two-level twin likewise, given the same draw counts the frozen function draws from its seed
    seed = (0, "boot2", "twin")
    counts = s9.draw_counts(8, R, seed)
    assert s9.two_level_interval_s9(rungs["3"], rs, counts, 10) == st.two_level_interval(rungs["3"], rs, 10, seed)
    assert s9.two_level_interval_s9(rungs["8"], rs, counts, 10) == st.two_level_interval(rungs["8"], rs, 10, seed)  # one draw: nothing to resample
    assert np.array_equal(counts, s9.draw_counts(8, R, seed)) and (counts.sum(axis=1) == 8).all() and s9.two_level_interval_s9(rungs["3"], rs, counts, 10, n_documents=4) is None
    # the sign condition: seven of eight per-draw means positive is enough, six is not
    e = np.full((8, 40), 0.1)
    e[0] = -0.01
    assert s9.union_rung_s9(e, text_resample(40), 1)["detected"]
    e[1] = -0.01
    out = s9.union_rung_s9(e, text_resample(40), 1)
    assert out["interval"][0] > 0.05 and not out["detected"] and not out["material"] and out["n_draws_positive"] == 6


# ----------------------------------------------------------------------------- run 2: the verdict


def _curve(intervals, detected=True):
    rungs = st.sort_rungs(list(intervals))
    per = {r: {"interval": list(iv), "detected": bool(detected and iv[0] > 0), "material": bool(detected and iv[0] > 0.05)} for r, iv in intervals.items()}
    return {"rungs": rungs, "per_rung": per, "label": s9.curve_label(per, rungs), "j_mat": next((r for r in rungs if per[r]["material"]), None)}


U_FAILS = _curve({"2": (0.06, 0.09), "3": (0.3, 0.4), "4": (0.4, 0.6)})


def test_the_worked_example_and_each_run_2_outcome():
    # the worked example: [+0.010, +0.030] at 8 tokens, [+0.030, +0.080] at 64 tokens, [+0.020, +0.045] at one text, all detected
    example = {"2": (0.010, 0.030), "3": (0.030, 0.080), "4": (0.020, 0.045)}
    assert s9.run2_outcome(_curve(example), U_FAILS)["outcome"] == s9.D_UNRESOLVED  # nothing material, one interval reaches past 0.05
    assert s9.run2_outcome(_curve(example), U_FAILS)["sizes_reaching_X"] == ["3"]
    assert s9.run2_outcome(_curve({**example, "3": (0.030, 0.045)}), U_FAILS)["outcome"] == s9.D_BELOW
    f = s9.run2_outcome(_curve({**example, "3": (0.055, 0.080)}), U_FAILS)
    assert f["outcome"] == s9.F_LATER and f["C_first_material"] == "3" and f["U_first_material"] == "2"  # material within code, first at a larger size than general donors
    assert s9.run2_outcome(_curve({**example, "2": (0.055, 0.080)}), U_FAILS)["outcome"] == s9.F_SAME  # at the same size
    later_U = _curve({"2": (0.01, 0.03), "3": (0.3, 0.4), "4": (0.4, 0.6)})
    assert s9.run2_outcome(_curve({**example, "2": (0.055, 0.080)}), later_U)["outcome"] == s9.F_SAME  # or sooner
    assert s9.run2_outcome(_curve({"2": (-0.01, 0.02), "3": (-0.005, 0.03), "4": (-0.02, 0.049)}), U_FAILS)["outcome"] == s9.H  # nothing detected, every upper end under 0.05
    assert s9.run2_outcome(_curve({"2": (-0.01, 0.02), "3": (-0.005, 0.05), "4": (-0.02, 0.04)}), U_FAILS)["outcome"] == s9.D_UNRESOLVED  # an upper end at 0.05 is not under it
    # the gate: arm U must fail on the code texts, or run 2 takes no reading, whatever arm C shows
    for u in (_curve({"2": (0.01, 0.03), "3": (0.02, 0.04)}), _curve({"2": (-0.01, 0.03), "3": (-0.02, 0.04)})):
        out = s9.run2_outcome(_curve({**example, "3": (0.055, 0.080)}), u)
        assert out["outcome"] == s9.NO_READING and out["gate"] is False
    none = {"rungs": ["2"], "per_rung": {"2": {"interval": None, "detected": None, "material": None}}, "label": None, "j_mat": None}
    assert s9.run2_outcome(none, U_FAILS)["outcome"] == s9.NO_READING
    # the order is the donor count, not the label: 2a (16 tokens) lies between 2 (8) and 3 (64), and one text after every token size
    assert s9.run2_outcome(_curve({"2a": (0.06, 0.08), "4": (0.06, 0.08)}), _curve({"3": (0.06, 0.08)}))["outcome"] == s9.F_SAME
    assert s9.run2_outcome(_curve({"4": (0.06, 0.08)}), _curve({"3": (0.06, 0.08)}))["outcome"] == s9.F_LATER


def test_the_verdict_from_planted_rise_tables():
    docs = np.repeat(np.arange(20), 2)
    rd = document_resample(docs, R, (0, "boot_docs", "E_G"))
    U = s9.union_curve_s9({"2": const(0.07), "3": const(0.4), "8": const(0.9, K=1)}, rd, n_documents=20)
    assert U["label"] == s9.FAILS and U["j_mat"] == "2"
    assert s9.run2_outcome(s9.union_curve_s9({"2": const(0.01), "3": const(0.04), "8": const(0.045, K=1)}, rd, n_documents=20), U)["outcome"] == s9.D_BELOW
    assert s9.run2_outcome(s9.union_curve_s9({"2": const(0.01), "3": const(0.06), "8": const(0.2, K=1)}, rd, n_documents=20), U)["outcome"] == s9.F_LATER
    assert s9.run2_outcome(s9.union_curve_s9({"2": const(0.0), "3": const(-0.01), "8": const(0.0, K=1)}, rd, n_documents=20), U)["outcome"] == s9.H
    rng = np.random.default_rng(3)
    noisy = np.tile(np.repeat(np.where(rng.random(20) < 0.5, 0.0, 0.11), 2), (8, 1))  # about 0.055 with an interval that straddles 0.05
    out = s9.union_curve_s9({"2": const(0.01), "3": noisy}, rd, n_documents=20)
    lo, hi = out["per_rung"]["3"]["interval"]
    assert 0 < lo < 0.05 < hi and s9.run2_outcome(out, U)["outcome"] == s9.D_UNRESOLVED


# ----------------------------------------------------------------------------- run 2: the match ratio


def _ratio(e_CG, e_PG, e_PP, e_CP, size_is_read=True):
    docs = np.arange(40)
    rs_G, rs_P = document_resample(docs, R, (0, "boot_docs", "G")), document_resample(docs, R, (0, "boot_docs", "P"))
    cC, cP = s9.draw_counts(8, R, (0, "boot_draws", "D_code")), s9.draw_counts(8, R, (0, "boot_draws", "D_prose"))
    return s9.match_ratio(const(e_CG), const(e_PG), const(e_PP), const(e_CP), rs_G, rs_P, cC, cP, n_documents_G=40, n_documents_P=40, size_is_read=size_is_read)


def test_the_match_ratio_worked_examples_and_its_readings():
    out = _ratio(0.045, 0.060, 0.015, 0.045)  # the example fixed in advance
    assert out["r_code"] == pytest.approx(0.75) and out["r_prose"] == pytest.approx(1 / 3) and out["R"] == pytest.approx(0.5) and out["m"] == 3
    assert out["interval"] == pytest.approx([0.5, 0.5]) and out["nonfinite_share"] == 0.0 and out["readable"] and out["reading"] == s9.MATCHING_HELPS
    one = _ratio(0.05, 0.05, 0.02, 0.02)
    assert one["R"] == pytest.approx(1.0) and one["reading"] == s9.NO_MATERIAL_HELP
    # a pool h times as harsh everywhere cancels in R
    assert _ratio(0.045 * 3, 0.060, 0.015, 0.045 * 3)["R"] == pytest.approx(0.5)
    # each side of 0.8 and of 1.25 (planted constants give intervals of zero width)
    below, above = _ratio(0.063, 0.1, 0.1, 0.1), _ratio(0.065, 0.1, 0.1, 0.1)  # R = sqrt(0.63) = 0.794 and sqrt(0.65) = 0.806
    assert below["R"] == pytest.approx(np.sqrt(0.63)) and below["reading"] == s9.MATCHING_HELPS and above["reading"] == s9.NO_MATERIAL_HELP
    assert _ratio(0.155, 0.1, 0.1, 0.1)["reading"] == s9.NO_MATERIAL_HELP and _ratio(0.158, 0.1, 0.1, 0.1)["reading"] == s9.CLOSER_IS_WORSE  # R = 1.245 and 1.257
    assert s9.r_reading([0.70, 0.79], True) == s9.MATCHING_HELPS and s9.r_reading([0.70, 0.80], True) == s9.UNRESOLVED and s9.r_reading([0.79, 0.95], True) == s9.UNRESOLVED
    assert s9.r_reading([0.81, 0.95], True) == s9.NO_MATERIAL_HELP and s9.r_reading([0.81, 1.40], True) == s9.NO_MATERIAL_HELP and s9.r_reading([1.25, 1.40], True) == s9.NO_MATERIAL_HELP
    assert s9.r_reading([1.26, 1.40], True) == s9.CLOSER_IS_WORSE and s9.r_reading([0.5, 1.4], True) == s9.UNRESOLVED
    assert s9.r_reading([0.1, 0.2], False) == s9.NOT_READ and s9.r_reading(None, True) == s9.NOT_READ and s9.r_reading([float("nan"), 0.5], True) == s9.NOT_READ
    # at one whole text R is printed and not read
    printed = _ratio(0.045, 0.060, 0.015, 0.045, size_is_read=False)
    assert printed["R"] == pytest.approx(0.5) and printed["interval"] == pytest.approx([0.5, 0.5]) and not printed["readable"] and printed["reading"] == s9.NOT_READ
    assert s9.R_SIZES_READ == ("2", "3", "7") and s9.R_SIZE_PRINTED_NOT_READ == "4"


def test_r_is_not_read_on_a_rise_whose_interval_lies_wholly_below_zero():
    # the condition is each rise's lower end above zero, at R's own level; "excludes zero" would have let a negative rise through
    assert s9.rises_all_above_zero({"C_G": [0.01, 0.03], "P_G": [0.02, 0.05], "P_P": [0.001, 0.01], "C_P": [0.01, 0.02]})
    below = {"C_G": [0.01, 0.03], "P_G": [0.02, 0.05], "P_P": [0.001, 0.01], "C_P": [-0.03, -0.01]}
    assert all(iv[0] > 0 or iv[1] < 0 for iv in below.values()) and not s9.rises_all_above_zero(below)  # every interval excludes zero, and the condition still fails
    assert not s9.rises_all_above_zero({"C_G": [0.0, 0.03]}) and not s9.rises_all_above_zero({"C_G": [-0.01, 0.03]}) and not s9.rises_all_above_zero({"C_G": [float("nan"), 0.03]}) and not s9.rises_all_above_zero({})
    out = _ratio(0.045, 0.060, 0.015, -0.02)  # code donors *lower* the divergence of the prose texts: that rise's interval is [-0.02, -0.02]
    assert out["rise_intervals"]["C_P"] == pytest.approx([-0.02, -0.02]) and not out["all_four_rises_above_zero"] and not out["readable"] and out["reading"] == s9.NOT_READ
    docs = np.arange(40)
    rs_G, rs_P = document_resample(docs, R, (0, "boot_docs", "G")), document_resample(docs, R, (0, "boot_docs", "P"))
    counts = s9.draw_counts(8, R, (0, "boot_draws", "D_code"))
    noisy = np.tile(np.random.default_rng(9).normal(0.02, 0.05, size=40), (8, 1))
    level = s9.match_ratio(const(0.045), const(0.06), const(0.015), noisy, rs_G, rs_P, counts, counts, n_documents_G=40, n_documents_P=40, size_is_read=True)
    reps = s9.rise_replicates(noisy, rs_P, counts)
    assert level["m"] == 3 and level["rise_intervals"]["C_P"] == s9.interval(reps, 3) and level["rise_intervals"]["C_P"] != s9.interval(reps, 1)  # the four intervals are taken at R's own level, 1 - 0.05 / 3


def test_r_is_read_only_if_all_four_rises_lie_above_zero_and_no_replicate_is_undefined():
    rng = np.random.default_rng(4)
    docs = np.arange(40)
    rs_G, rs_P = document_resample(docs, R, (0, "boot_docs", "G")), document_resample(docs, R, (0, "boot_docs", "P"))
    cC, cP = s9.draw_counts(8, R, (0, "boot_draws", "D_code")), s9.draw_counts(8, R, (0, "boot_draws", "D_prose"))
    near_zero = np.tile(rng.normal(0.002, 0.02, size=40), (8, 1))  # a numerator whose interval includes zero: some replicates have a non-positive rise
    out = s9.match_ratio(near_zero, const(0.06), const(0.015), const(0.045), rs_G, rs_P, cC, cP, n_documents_G=40, n_documents_P=40, size_is_read=True)
    assert not out["all_four_rises_above_zero"] and out["nonfinite_share"] > 0 and not out["readable"] and out["reading"] == s9.NOT_READ
    few = s9.match_ratio(const(0.045), const(0.06), const(0.015), const(0.045), rs_G, rs_P, cC, cP, n_documents_G=40, n_documents_P=3, size_is_read=True)
    assert few["R"] == pytest.approx(0.5) and few["interval"] is None and few["reading"] == s9.NOT_READ
    # the draws of a pool are shared between the strata it is scored on: with C's rise differing by draw only, r_code and r_prose move together and R's interval has width
    by_draw = np.repeat(np.linspace(0.02, 0.08, 8)[:, None], 40, axis=1)
    moving = s9.match_ratio(by_draw, const(0.06), const(0.015), by_draw, rs_G, rs_P, cC, cP, n_documents_G=40, n_documents_P=40, size_is_read=True)
    assert moving["log_interval"] == pytest.approx([np.log(np.sqrt(0.015 / 0.06))] * 2, abs=1e-12)  # C's resampled mean cancels exactly between the numerator of r_code and the denominator of r_prose


# ----------------------------------------------------------------------------- run 2: the descriptions


def test_the_descriptions():
    rs = text_resample(40, "d")
    cA, cB = s9.draw_counts(8, R, (0, "boot_draws", "A")), s9.draw_counts(8, R, (0, "boot_draws", "B"))
    out = s9.pool_contrast(const(0.06), const(0.03), rs, cA, cB, n_documents=None)
    assert out["difference"] == pytest.approx(0.03) and out["ratio"] == pytest.approx(2.0) and out["difference_interval"] == pytest.approx([0.03, 0.03]) and out["ratio_interval"] == pytest.approx([2.0, 2.0])
    assert out["n_draws_a_above_b_by_index"] == 8 and out["ratio_nonfinite_share"] == 0.0 and s9.pool_contrast(const(0.06), const(0.03), rs, cA, cB, n_documents=5)["difference_interval"] is None
    # per unit of mask moved: a ratio of means from the per-text sigma column, recomputed within each replicate
    rng = np.random.default_rng(5)
    sigma = np.tile(rng.uniform(50, 150, size=40), (8, 1))
    e = 0.001 * sigma  # harm proportional to the mask moved: h is 0.001 in every replicate
    h = s9.per_unit(e, sigma, rs, cA, n_documents=None)
    assert h["h"] == pytest.approx(0.001) and h["interval"] == pytest.approx([0.001, 0.001]) and h["sigma_bar"] == pytest.approx(sigma.mean())
    assert s9.per_unit_ratio(e, sigma, 2 * e, sigma, rs, cA, cB, n_documents=None)["interval"] == pytest.approx([0.5, 0.5])
    lam = s9.lambda_contrast(const(0.03), const(0.06), const(0.04), const(0.04), rs, text_resample(40, "o"), cA, cB)
    assert lam["lambda"] == pytest.approx(np.log(0.5)) and lam["interval"] == pytest.approx([np.log(0.5)] * 2) and lam["nonfinite_share"] == 0.0
    # a control is compared with its own arm, paired by draw and resampled with it: a per-draw offset common to both cancels exactly
    offset = np.repeat(np.linspace(-0.05, 0.05, 8)[:, None], 40, axis=1)
    ctl = s9.control_against_arm(const(0.06) + offset, const(0.01) + offset, rs, cA, n_documents=None)
    assert ctl["difference"] == pytest.approx(0.05) and ctl["difference_interval"] == pytest.approx([0.05, 0.05]) and ctl["n_draws_real_above_control"] == 8
    with pytest.raises(AssertionError, match="paired"):
        s9.control_against_arm(const(0.06), const(0.01, K=4), rs, cA, n_documents=None)


# ----------------------------------------------------------------------------- run 2: the count-only prediction


def test_pooling_adjacent_violators_and_the_log_log_interpolation():
    assert s9.pav_nondecreasing(np.array([1.0, 3.0, 2.0, 4.0])).tolist() == [1.0, 2.5, 2.5, 4.0]
    assert s9.pav_nondecreasing(np.array([3.0, 2.0, 1.0])).tolist() == [2.0, 2.0, 2.0] and s9.pav_nondecreasing(np.array([1.0, 2.0, 3.0])).tolist() == [1.0, 2.0, 3.0]
    assert s9.pav_nondecreasing(np.array([1.0, 5.0, 3.0, 2.0, 6.0])).tolist() == pytest.approx([1.0, 10 / 3, 10 / 3, 10 / 3, 6.0])
    la, lr = s9.yardstick_curve(np.array([100.0, 10.0, 1000.0, 1.0]), np.array([0.2, 0.4, 0.8, -0.1]))  # unsorted; a rise that is not positive is skipped; 0.4 above 0.2 is a violation on the log rise
    assert np.allclose(la, np.log([10.0, 100.0, 1000.0])) and np.allclose(lr, [np.log(np.sqrt(0.4 * 0.2))] * 2 + [np.log(0.8)])
    ka, kr = s9.yardstick_curve(np.array([10.0, 1000.0]), np.array([0.01, 1.0]))  # a power law with exponent 1
    assert s9.predict_loglog(np.array([100.0]), ka, kr, extend=False)[0] == pytest.approx(0.1)  # linear in log-log, not in the amounts (that would give 0.1 only by accident: here 0.0918)
    pred = s9.predict_loglog(np.array([5.0, 10.0, 1000.0, 2000.0]), ka, kr, extend=False)
    assert np.isnan(pred[0]) and np.isnan(pred[3]) and pred[1] == pytest.approx(0.01) and pred[2] == pytest.approx(1.0)  # no extrapolation; the ends belong to the range
    assert s9.predict_loglog(np.array([5.0, 2000.0]), ka, kr, extend=True) == pytest.approx([0.005, 2.0])  # only inside replicates


def _power_law_case(c_factor, n_outside=0):
    rng = np.random.default_rng(6)
    sizes = ["1", "2", "2a", "2b", "3", "4", "5", "6", "7", "8"]
    amounts = [60.0, 400.0, 700.0, 1200.0, 1900.0, 2500.0, 3500.0, 4500.0, 5200.0, 5600.0]
    N, docs = 40, np.arange(40)
    law = lambda a: 1e-6 * np.asarray(a) ** 1.6  # noqa: E731
    e_U = {j: np.full((1 if j == "8" else 8, N), law(a)) for j, a in zip(sizes, amounts)}
    a_U = {j: np.full((1 if j == "8" else 8, N), a) for j, a in zip(sizes, amounts)}
    e_C, a_C = {}, {}
    for j, a in (("3", 1500.0), ("7", 4200.0)):
        per_draw = a * rng.uniform(0.8, 1.2, size=8)
        if n_outside:
            per_draw[:n_outside] = 9000.0  # beyond U's measured range: no prediction
        scatter = np.array([0.9, 1.1, 0.95, 1.05, 0.9, 1.1, 0.95, 1.05])  # around the law, so that "on it" does not hang on rounding
        a_C[j] = np.repeat(per_draw[:, None], N, axis=1)
        e_C[j] = np.repeat((c_factor * scatter * law(per_draw))[:, None], N, axis=1)
    return e_U, a_U, e_C, a_C, document_resample(docs, 400, (0, "boot_docs", "co")), s9.draw_counts(8, 400, (0, "boot_draws", "D_code"))


def test_the_count_only_reading_on_a_planted_power_law_and_on_twice_that():
    e_U, a_U, e_C, a_C, rs, counts = _power_law_case(1.0)
    on = s9.count_only(e_U, a_U, e_C, a_C, rs, counts, n_documents=40)
    assert on["m"] == 2 and not on["U_curve"]["violators_pooled"] and on["measured_range"] == pytest.approx([60.0, 5600.0]) and len(on["U_points"]) == 10
    for j in ("3", "7"):
        row = on["per_size"][j]
        assert row["n_draws_predicted"] == 8 and abs(row["log_ratio"]) < 0.05 and row["interval"][0] < 0 < row["interval"][1] and row["readable"] and row["reading"] == s9.ON_IT
    twice = s9.count_only(*_power_law_case(2.0)[:4], rs, counts, n_documents=40)
    for j in ("3", "7"):
        row = twice["per_size"][j]
        assert row["log_ratio"] == pytest.approx(np.log(2.0), abs=0.05) and row["interval"][0] > 0.5 and row["reading"] == s9.ABOVE
    half = s9.count_only(*_power_law_case(0.5)[:4], rs, counts, n_documents=40)
    assert half["per_size"]["3"]["reading"] == s9.BELOW
    # each draw is predicted from its own amount and the predictions are averaged: on a convex curve that is above the prediction at the mean amount
    row = on["per_size"]["3"]
    at_mean = 1e-6 * np.mean(row["amount_per_draw"]) ** 1.6
    assert row["prediction"] > at_mean and row["prediction"] == pytest.approx(np.mean(row["prediction_per_draw"]))
    # no extrapolation: two draws beyond U's range have no prediction, six predicted draws are fewer than seven, and the size is not read
    out = s9.count_only(*_power_law_case(1.0, n_outside=2)[:4], rs, counts, n_documents=40)
    row = out["per_size"]["3"]
    assert row["n_draws_predicted"] == 6 and np.isnan(row["prediction_per_draw"][:2]).all() and not row["readable"] and row["reading"] == s9.NOT_READ
    assert row["observed"] == pytest.approx(np.mean(row["observed_per_draw"][2:]))  # the observed rise is averaged over the predicted draws
    one = s9.count_only(*_power_law_case(1.0, n_outside=1)[:4], rs, counts, n_documents=40)["per_size"]["3"]
    assert one["n_draws_predicted"] == 7 and one["readable"]
    # a size that is not one of the two read sizes is tabulated without an interval; fewer than ten documents, no interval anywhere
    e_U, a_U, e_C, a_C, rs, counts = _power_law_case(1.0)
    e_C["2"], a_C["2"] = np.full((8, 40), 1e-6 * 300.0 ** 1.6), np.full((8, 40), 300.0)
    extra = s9.count_only(e_U, a_U, e_C, a_C, rs, counts, n_documents=40)["per_size"]["2"]
    assert extra["log_ratio"] == pytest.approx(0.0, abs=1e-9) and extra["interval"] is None and extra["reading"] == s9.NOT_READ
    assert s9.count_only(e_U, a_U, e_C, a_C, rs, counts, n_documents=9)["per_size"]["3"]["interval"] is None


def test_the_count_only_output_says_how_often_the_end_segment_was_continued():
    # with amounts that do not vary over texts a replicate's knots are the full data's, and nothing is continued
    e_U, a_U, e_C, a_C, rs, counts = _power_law_case(1.0)
    flat = s9.count_only(e_U, a_U, e_C, a_C, rs, counts, n_documents=40)
    assert all(flat["per_size"][j]["end_segment_continued_share"] == 0.0 and flat["per_size"][j]["n_replicate_draw_predictions"] == int((counts > 0).sum()) for j in ("3", "7"))
    # arm U's top knot now moves with the resampled documents (5,500 on half of them, 5,700 on the others: 5,600 in the full data), and four draws of arm C at 64 texts sit exactly on it
    a_U["8"] = np.where(np.arange(40) % 2 == 0, 5500.0, 5700.0)[None, :]
    a_C["7"][:4] = 5600.0
    e_C["2"], a_C["2"] = np.full((8, 40), 1e-6 * 300.0 ** 1.6), np.full((8, 40), 300.0)  # a size that is tabulated and not read
    out = s9.count_only(e_U, a_U, e_C, a_C, rs, counts, n_documents=40)
    row = out["per_size"]["7"]
    assert out["measured_range"][1] == pytest.approx(5600.0) and row["n_draws_predicted"] == 8  # the ends belong to the range: all eight draws have a prediction in the full data
    top = s9.ratio_means(rs, a_U["8"][0])  # the replicates' top knots
    outside = np.log(5600.0) > np.log(top)
    want_pairs, want_continued = int((counts > 0).sum()), int(((counts[:, :4] > 0) & outside[:, None]).sum())
    assert row["n_replicate_draw_predictions"] == want_pairs and row["end_segment_continued_share"] == want_continued / want_pairs and 0.1 < row["end_segment_continued_share"] < 0.4
    assert row["nonfinite_share"] == 0.0 and np.all(np.isfinite(row["interval"]))  # continued, never dropped: the fixed set of predicted draws keeps its predictions in every replicate
    assert out["per_size"]["3"]["end_segment_continued_share"] == 0.0 and "end_segment_continued_share" not in out["per_size"]["2"]  # an interior size; and only the read sizes carry it


def test_the_count_only_curve_pools_a_violation_and_skips_a_rise_that_is_not_positive():
    e_U, a_U, e_C, a_C, rs, counts = _power_law_case(1.0)
    e_U["1"] = np.full((8, 40), -0.001)  # one token: a rise that is not positive
    e_U["2b"] = e_U["2a"] * 0.9  # 32 tokens below 16 tokens
    out = s9.count_only(e_U, a_U, e_C, a_C, rs, counts, n_documents=40)
    assert out["U_curve"]["violators_pooled"] and len(out["U_curve"]["log_amount"]) == 9 and not out["U_points"][0]["used"] and out["measured_range"][0] == pytest.approx(400.0)
    iso = np.asarray(out["U_curve"]["log_rise_isotonic"])
    assert (np.diff(iso) >= 0).all() and iso[1] == iso[2]


# ----------------------------------------------------------------------------- run 6


def test_the_self_merge_rule_at_its_boundary():
    rs = text_resample(50, "self")
    assert s9.self_merge_rule(np.full(50, 0.0501), rs)["material"] and not s9.self_merge_rule(np.full(50, 0.05), rs)["material"]  # the lower end must exceed 0.05
    s = np.linspace(-0.10, 0.22, 50)  # a mean of 0.06, above 0.05, whose interval reaches below it
    out = s9.self_merge_rule(s, rs, s_against_rounded=s - 0.01)
    assert out["s_hat"] > 0.05 and out["interval"][0] < 0.05 and not out["material"] and out["m"] == 3
    assert out["share_made_worse"] == pytest.approx((s > 0).mean()) and out["share_above"]["0.1"] == pytest.approx((s > 0.1).mean()) and out["percentiles"]["50"] == pytest.approx(np.median(s))
    assert out["s_hat_against_rounded_labels"] == pytest.approx(s.mean() - 0.01) and out["share_made_worse_interval"][0] <= out["share_made_worse"] <= out["share_made_worse_interval"][1]
    wide = st.percentile_interval(rs.means(s), 3)
    assert out["interval"] == [wide[0], wide[1]]  # level 1 - 0.05 / 3
    few = s9.self_merge_rule(s, rs, n_documents=3)
    assert few["interval"] is None and few["material"] is None and few["s_hat"] == pytest.approx(s.mean())


def test_self_against_stranger():
    rs = text_resample(50, "stranger")
    rng = np.random.default_rng(8)
    x = rng.normal(0.5, 0.1, size=(4, 50))
    sig = np.full(50, 5000.0)
    worse = s9.self_against_stranger(x.mean(axis=0) + 0.2, x, rs, sigma_self=sig, sigma_shifts=np.tile(sig, (4, 1)))
    assert worse["reading"] == s9.SELF_WORSE and worse["delta_hat"] == pytest.approx(0.2) and worse["interval"] == pytest.approx([0.2, 0.2]) and worse["share_delta_positive"] == 1.0
    assert s9.self_against_stranger(x.mean(axis=0) - 0.2, x, rs, sigma_self=sig, sigma_shifts=np.tile(sig, (4, 1)))["reading"] == s9.SELF_LESS
    same = s9.self_against_stranger(x.mean(axis=0) + rng.normal(0, 0.1, size=50), x, rs, sigma_self=sig, sigma_shifts=np.tile(sig, (4, 1)))
    assert same["reading"] == s9.SELF_NO_BETTER and same["interval"][0] < 0 < same["interval"][1]
    # per unit of mask moved: the self-merge moves half the mask for the same harm, so it is twice as harmful per unit
    unit = s9.self_against_stranger(x.mean(axis=0), x, rs, sigma_self=sig / 2, sigma_shifts=np.tile(sig, (4, 1)))
    assert unit["per_unit"]["self"] == pytest.approx(2 * unit["per_unit"]["stranger"]) and unit["per_unit"]["interval"][0] > 0 and unit["per_unit"]["nonfinite_share"] == 0.0


def test_a_ladder_rung_averages_a_texts_qualifying_shifts_first():
    docs = np.repeat(np.arange(10), 2)
    rd = document_resample(docs, R, (0, "boot_docs", "ladder"))
    e = np.zeros((4, 20))
    q = np.zeros((4, 20), dtype=bool)
    e[:, 0], q[:3, 0] = [0.1, 0.2, 0.3, 9.0], True  # text 0 qualifies under three shifts: 0.2, the fourth shift's 9.0 never enters
    e[0, 1], q[0, 1] = 0.4, True  # text 1 under one
    counts = np.where(q, 4000.0, 1.0)
    out = s9.ladder_rung(e, q, rd, n_documents=10, count_shifts=counts)
    assert out["n_texts"] == 2 and out["n_text_shift_pairs"] == 4 and out["mean_rise"] == pytest.approx(0.3) and out["mean_count"] == pytest.approx(4000.0)  # (0.2 + 0.4) / 2, not (0.1 + 0.2 + 0.3 + 0.4) / 4
    assert out["nonfinite_share"] > 0  # texts 0 and 1 are one document: a replicate that does not draw it has no qualifying text; the share is printed
    # the value, the counts, and the interval are printed, the interval flagged, and the rung has no standing, although its interval lies wholly above 0.05
    assert out["interval"][0] > 0.05 and np.all(np.isfinite(out["interval"])) and out["standing"] is None and out["interval_flag"] == s9.NONFINITE_FLAG
    clean = s9.ladder_rung(np.where(q, e, 0.3), np.ones((4, 20), bool), rd, n_documents=10)  # the same rises with every text qualifying: no undefined replicate, and the standing is given
    assert clean["nonfinite_share"] == 0.0 and clean["standing"] == s9.MATERIAL and clean["interval_flag"] == ""
    full = s9.ladder_rung(np.full((4, 20), 0.06), np.ones((4, 20), bool), rd, n_documents=10)
    assert full["standing"] == s9.MATERIAL and full["interval"] == pytest.approx([0.06, 0.06]) and full["m"] == 5 and full["nonfinite_share"] == 0.0
    assert s9.ladder_rung(np.full((4, 20), 0.04), np.ones((4, 20), bool), rd, n_documents=10)["standing"] == s9.UNDER
    assert s9.ladder_rung(np.full((4, 20), 0.05), np.ones((4, 20), bool), rd, n_documents=10)["standing"] is None  # neither above nor wholly under
    assert s9.ladder_rung(np.full((4, 20), 0.06), np.ones((4, 20), bool), rd, n_documents=3)["standing"] is None  # ArXiv: no interval, no standing
    assert s9.ladder_rung(e, np.zeros((4, 20), bool), rd, n_documents=10)["n_texts"] == 0


def test_the_scope_rule_at_three_and_at_four_of_five_sources():
    m, u = s9.MATERIAL, s9.UNDER
    four = s9.scope_rule({"Github": m, "Pile-CC": m, "Wikipedia (en)": m, "StackExchange": m, "ArXiv": None})  # ArXiv has three documents: all four readable sources are needed
    assert four["within_one_kind_of_text"] and four["standing"] == m and four["sources_without_standing"] == ["ArXiv"]
    three = s9.scope_rule({"Github": m, "Pile-CC": m, "Wikipedia (en)": m, "StackExchange": u, "ArXiv": None})
    assert not three["within_one_kind_of_text"] and three["standing"] is None and three["sources_by_standing"][m] == ["Github", "Pile-CC", "Wikipedia (en)"] and three["sources_by_standing"][u] == ["StackExchange"]
    assert s9.scope_rule({"Github": u, "Pile-CC": u, "Wikipedia (en)": u, "StackExchange": u, "ArXiv": m})["standing"] == u  # four of five, with a readable fifth that differs
    assert not s9.scope_rule({"Github": m, "Pile-CC": m, "Wikipedia (en)": u, "StackExchange": u, "ArXiv": None})["within_one_kind_of_text"]
    assert not s9.scope_rule({"Github": m, "Pile-CC": m, "Wikipedia (en)": m, "StackExchange": None, "ArXiv": None})["within_one_kind_of_text"]  # a source with neither standing does not count


# ----------------------------------------------------------------------------- runs 3 and 7


def test_change_rates_exclude_the_targets_ties_and_the_confident_rate_is_a_ratio_of_sums():
    target_top = np.array([[1, 1, 2, 2], [0, 0, 0, 0]])
    top = np.array([[1, 2, 2, 0], [1, 0, 0, 0]])
    tie = np.array([[False, True, False, False], [True, False, False, False]])
    top_p = np.array([[0.9, 0.4, 0.5, 0.3], [0.45, 0.6, 0.7, 0.2]], dtype=np.float32)
    c = s9.change_rates_excluding_ties(top, target_top, tie, top_p)
    assert c["n"].tolist() == [3, 3] and c["n_changed"].tolist() == [1, 0] and c["n_tied"].tolist() == [1, 1]  # text 0's change at the tied position 1 and text 1's at the tied position 0 do not count
    assert c["n_confident"].tolist() == [2, 2] and c["n_changed_confident"].tolist() == [0, 0] and c["rate_with_ties"].tolist() == [0.5, 0.25] and c["rate_with_ties"].dtype == np.float32  # the gate's side: ties included, as the loop stored it
    # a ratio of sums over texts: a text with three confident positions must not weigh as one with three hundred
    n_conf, n_chg = np.array([3, 300]), np.array([3, 30])
    rs = st.Resample.from_index_sets([[0, 1], [0, 0], [1, 1]], 2)
    out = s9.rate_of_sums(n_chg, n_conf, rs)
    assert out["rate"] == pytest.approx(33 / 303) and out["rate"] != pytest.approx((1.0 + 0.1) / 2) and out["n_positions"] == 303
    assert np.allclose(sorted(rs.ratios(n_chg.astype(float), n_conf.astype(float))), [0.1, 33 / 303, 1.0])
    # for a cell without per-position arrays the numerator is recovered exactly as the stored rate times the count
    rate = (n_chg / n_conf).astype(np.float32)
    assert s9.confident_counts_from_columns(rate, n_conf).tolist() == [3, 30]
    assert s9.confident_counts_from_columns(np.array([np.nan, 0.25], dtype=np.float32), np.array([0, 8])).tolist() == [0, 2]  # no confident position: a NaN rate, nothing contributed
    with pytest.raises(AssertionError, match="whole number"):
        s9.confident_counts_from_columns(np.array([0.3], dtype=np.float32), np.array([5]))
    pm = s9.paired_mean(np.array([0.5, 0.7]), np.array([0.4, 0.4]), rs)
    assert pm["mean"] == pytest.approx(0.6) and pm["rise"] == pytest.approx(0.2) and pm["baseline"] == pytest.approx(0.4)
    # the paired rise of a rate over its baseline's: both ratios of sums, recomputed from the same resampled texts and subtracted
    rise = s9.rate_of_sums_rise(n_chg, n_conf, np.array([0, 15]), n_conf, rs, m=1)
    assert rise["rate"] == pytest.approx(33 / 303) and rise["baseline"] == pytest.approx(15 / 303) and rise["rise"] == pytest.approx(18 / 303) and rise["nonfinite_share"] == 0.0
    assert np.allclose(sorted(rs.ratios(n_chg.astype(float), n_conf.astype(float)) - rs.ratios(np.array([0.0, 15.0]), n_conf.astype(float))), [0.05, 18 / 303, 1.0])
    assert rise["rise_interval"][0] == pytest.approx(np.quantile([0.05, 18 / 303, 1.0], 0.025)) and rise["rise_interval"][1] == pytest.approx(np.quantile([0.05, 18 / 303, 1.0], 0.975))


def test_the_bin_table_and_the_examples_by_rule():
    kl = np.array([[0.01, 0.05, 0.19, 0.2], [0.6, 1.0, 1.99, 2.5]])
    changed = np.array([[False, False, True, False], [True, True, True, True]])
    p = np.array([[0.9, 0.8, 0.5, 0.6], [0.3, 0.2, 0.1, 0.05]])
    t = s9.bin_table(kl, changed, p)
    assert [r["n_positions"] for r in t] == [1, 2, 1, 1, 2, 1] and t[1]["change_rate"] == 0.5 and t[1]["mean_p_target_top"] == pytest.approx(0.65) and t[0]["to"] == 0.05 and t[5]["from"] == 2.0  # a bin's lower edge belongs to it
    ex = s9.bin_table(kl, changed, p, exclude=np.array([[False, False, True, False], [False] * 4]))
    assert [r["n_positions"] for r in ex] == [1, 1, 1, 1, 2, 1] and ex[1]["change_rate"] == 0.0
    # pooled over masks from the per-mask tables: the table of the concatenated arrays (an empty bin of one mask contributes nothing)
    kl2, changed2, p2 = np.array([[0.06, 0.07, 3.0, 4.0]]), np.array([[True, True, False, True]]), np.array([[0.1, 0.2, 0.3, 0.4]])
    pooled, whole = s9.pool_bin_tables([t, s9.bin_table(kl2, changed2, p2)]), s9.bin_table(np.concatenate([kl.reshape(-1), kl2.reshape(-1)]), np.concatenate([changed.reshape(-1), changed2.reshape(-1)]), np.concatenate([p.reshape(-1), p2.reshape(-1)]))
    assert [r["n_positions"] for r in pooled] == [r["n_positions"] for r in whole] == [1, 4, 1, 1, 2, 3]
    assert all(a["change_rate"] == pytest.approx(b["change_rate"]) and a["mean_p_target_top"] == pytest.approx(b["mean_p_target_top"]) for a, b in zip(pooled, whole)) and pooled[1]["change_rate"] == pytest.approx(0.75)
    # examples: the percentile is over all positions; among the eligible stored positions, the nearest divergence; ties to the lowest text, then position
    kl_all = np.arange(40, dtype=float).reshape(4, 10) / 10
    positions = np.array([[2, 7], [2, 7], [2, 7], [2, 7]])
    eligible = np.array([[True, True], [True, False], [True, True], [True, True]])
    out = s9.choose_examples(kl_all, positions, eligible, percentiles=(50.0,), n_written=3)
    assert out[0]["value"] == pytest.approx(1.95) and [(e["seq"], e["position"]) for e in out[0]["nearest"]] == [(2, 2), (1, 2), (2, 7)]  # 2.2 and 1.7 (not eligible) ... the nearest eligible are 2.2 (0.25), 1.2 (0.75), 2.7 (0.75): the tie goes to the lower text
    tied = s9.choose_examples(np.full((3, 10), 0.5), np.array([[1, 4], [1, 4], [1, 4]]), np.ones((3, 2), bool), percentiles=(10.0, 99.0), n_written=2)
    assert all([(e["seq"], e["position"]) for e in row["nearest"]] == [(0, 1), (0, 4)] for row in tied) and s9.EXAMPLE_PERCENTILES == (10.0, 50.0, 90.0, 99.0) and s9.EXAMPLES_WRITTEN == 5
    assert s9.yardstick_ratios({"own labels": 0.34, "self-merge": 1.47}, 1.7) == pytest.approx({"own labels": 0.2, "self-merge": 1.47 / 1.7})
