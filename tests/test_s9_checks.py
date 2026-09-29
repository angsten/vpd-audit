"""The checks that need no GPU, on synthetic inputs: the document index (its worked example), the document-level bootstrap, the
position statistics (their worked example), the three-way readings of checks (a), (d), and (c) at their boundaries, and the
existence rule's null with its two parameters."""

import numpy as np
import pandas as pd
import pytest

from vpd_audit import s9_checks as s9
from vpd_audit import stats as st
from vpd_audit.constants import SEQ_LEN

# ----------------------------------------------------------------------------- the document index


def _example_block():
    """The worked example: four rows of 512 tokens with a single end-of-text id, at token 100 of row 1."""
    block = np.full((4, SEQ_LEN), 7, dtype=np.int32)
    block[1, 100] = s9.EOT_ID
    return block


def test_document_index_worked_example():
    di = s9.block_document_index(_example_block())
    assert di["majority"].tolist() == [0, 1, 1, 1]  # row 1 holds 100 tokens of document 0 and 411 of document 1
    assert di["first"].tolist() == [0, 0, 1, 1]
    assert di["n_eot"].tolist() == [0, 1, 0, 0]


def test_document_index_ties_go_to_the_earlier_document_and_short_documents_never_hold_a_majority():
    block = np.full((2, SEQ_LEN), 7, dtype=np.int32)
    block[0, 255] = s9.EOT_ID  # 255 tokens of document 0, the id, 256 of document 1: document 1 holds the majority
    di = s9.block_document_index(block)
    assert di["majority"].tolist() == [1, 1]
    tie = np.full((1, 513), 7, dtype=np.int32)
    tie[0, 256] = s9.EOT_ID  # 256 tokens each side of the id: a tie, to the earlier document
    assert s9.block_document_index(tie)["majority"].tolist() == [0]
    short = np.full((1, SEQ_LEN), 7, dtype=np.int32)
    short[0, [200, 210, 220]] = s9.EOT_ID  # documents 1 and 2 are nine tokens each
    di = s9.block_document_index(short)
    assert di["majority"].tolist() == [3] and di["n_eot"].tolist() == [3]  # 200, 9, 9, and 291 tokens
    first = np.full((2, SEQ_LEN), 7, dtype=np.int32)
    first[1, 0] = s9.EOT_ID  # a row that starts with the id: the id closes document 0, the row's tokens are document 1's
    di = s9.block_document_index(first)
    assert di["first"].tolist() == [0, 0] and di["majority"].tolist() == [0, 1]


def test_blocks_restart_and_counts():
    assert s9.contiguous_blocks(["a", "a", "b", "b", "b", "c"]) == [("a", 0, 2), ("b", 2, 5), ("c", 5, 6)]
    with pytest.raises(AssertionError):
        s9.contiguous_blocks(["a", "b", "a"])
    rows = []
    for source, block in (("x", _example_block()), ("y", _example_block())):
        di = s9.block_document_index(block)
        rows += [{"set": "S", "row": len(rows) + i, "source": source, "majority_document": int(di["majority"][i]), "first_token_document": int(di["first"][i]), "n_end_of_text": int(di["n_eot"][i])} for i in range(4)]
    index = pd.DataFrame(rows)
    counts = s9.document_counts(index)
    assert counts["distinct_documents"].tolist() == [2, 2] and counts["documents_by_end_of_text_count"].tolist() == [2, 2]
    assert counts["rows_per_document_max"].tolist() == [3, 3] and counts["rows_per_document_mean"].tolist() == [2.0, 2.0]
    assert counts["expected_hidden_boundaries"].tolist() == [1 * 3 / (SEQ_LEN * 4)] * 2  # one id seen in 4 * 512 saved tokens; three unsaved tokens between the rows
    codes = s9.document_codes(index, "S", 0, 8)
    assert codes.tolist() == [0, 1, 1, 1, 2, 3, 3, 3]  # the second block's documents 0 and 1 are other documents than the first's
    assert s9.document_codes(index, "S", 2, 6).tolist() == [0, 0, 1, 2]


def test_near_duplicate_screen_finds_a_planted_window():
    rng = np.random.default_rng(0)
    a, b = rng.integers(1, 50000, size=(3, 120)).astype(np.int32), rng.integers(1, 50000, size=(4, 120)).astype(np.int32)
    b[2, 30:80] = a[1, 10:60]  # one exact 50-token window
    share, pairs = s9.near_duplicate_screen(a, b, window=50)
    assert share == 1 / 3 and pairs.to_dict("records") == [{"a_row": 1, "b_row": 2, "n_shared_windows": 1, "first_offset_a": 10, "first_offset_b": 30}]
    b[2, 30:81] = a[1, 10:61]  # 51 shared tokens are two windows
    assert s9.near_duplicate_screen(a, b, window=50)[1]["n_shared_windows"].tolist() == [2]
    assert s9.near_duplicate_screen(a, rng.integers(1, 50000, size=(4, 120)).astype(np.int32), window=50)[0] == 0.0


# ----------------------------------------------------------------------------- the document bootstrap


def test_document_resample_moves_a_documents_rows_together_and_the_mean_stays_row_weighted():
    docs = np.array([0, 0, 0, 1, 2, 2])
    rs = s9.document_resample(docs, 500, (0, "test"))
    assert rs.W.shape == (500, 6)
    assert np.array_equal(rs.W[:, 0], rs.W[:, 1]) and np.array_equal(rs.W[:, 0], rs.W[:, 2]) and np.array_equal(rs.W[:, 4], rs.W[:, 5])
    per_doc = rs.W[:, [0, 3, 4]]
    assert np.all(per_doc.sum(axis=1) == 3)  # as many document draws as there are documents
    v = np.array([1.0, 2.0, 3.0, 10.0, -1.0, -3.0])
    want = (rs.W @ v) / rs.W.sum(axis=1)  # the resampled row total over the resampled row count
    assert np.allclose(s9.doc_means(rs, v), want) and not np.allclose(want, rs.means(v))  # Resample.means divides by n and is not the row-weighted mean here


def test_document_bootstrap_is_wider_than_the_row_bootstrap_when_a_documents_rows_are_identical():
    rng = np.random.default_rng(1)
    n_docs, per = 40, 5
    docs = np.repeat(np.arange(n_docs), per)
    v = np.repeat(rng.normal(size=n_docs), per)  # the planted set: rows of one document are identical
    doc_rs = s9.document_resample(docs, 4000, (0, "planted", "docs"))
    row_rs = st.Resample.make(v.size, 4000, (0, "planted", "rows"))
    d_lo, d_hi = s9.interval_or_none(s9.doc_means(doc_rs, v), n_docs)
    r_lo, r_hi = st.percentile_interval(row_rs.means(v), 1)
    assert d_lo < v.mean() < d_hi
    assert (d_hi - d_lo) > 1.8 * (r_hi - r_lo)  # about sqrt(5) = 2.2 times as wide


def test_no_interval_under_ten_documents():
    assert s9.interval_or_none(np.arange(100.0), 9) is None
    assert s9.interval_or_none(np.arange(101.0), 10) == [2.5, 97.5]


# ----------------------------------------------------------------------------- check (a)


def _ps(lo, hi, guard=True):
    return {"ratio_interval": None if lo is None else [lo, hi], "guard": guard}


def test_check_a_reading_at_its_boundaries():
    assert s9.check_a_source_reading({64: _ps(0.05, 0.19), 256: _ps(0.01, 0.1999)}) == s9.MET
    assert s9.check_a_source_reading({64: _ps(0.05, 0.19), 256: _ps(0.01, 0.2)}) == s9.UNDECIDED  # the upper end must be below 0.2, not at it
    assert s9.check_a_source_reading({64: _ps(0.21, 0.9), 256: _ps(0.2001, 0.5)}) == s9.NOT_MET
    assert s9.check_a_source_reading({64: _ps(0.21, 0.9), 256: _ps(0.2, 0.5)}) == s9.UNDECIDED  # the lower end must be above 0.2, not at it
    assert s9.check_a_source_reading({64: _ps(0.05, 0.19), 256: _ps(0.21, 0.5)}) == s9.UNDECIDED  # met at one size, not met at the other
    assert s9.check_a_source_reading({64: _ps(0.1, 0.3), 256: _ps(0.05, 0.1)}) == s9.UNDECIDED  # straddles at one size
    assert s9.check_a_source_reading({64: _ps(0.05, 0.19, guard=False), 256: _ps(0.01, 0.1)}) == s9.UNDECIDED  # the guard fails at one size: not read
    assert s9.check_a_source_reading({64: _ps(None, None), 256: _ps(0.01, 0.1)}) == s9.UNDECIDED  # no interval (fewer than ten documents)
    assert s9.check_a_supported({"Pile-CC": s9.MET, "Wikipedia (en)": s9.MET}) is True
    assert s9.check_a_supported({"Pile-CC": s9.MET, "Wikipedia (en)": s9.UNDECIDED}) is False
    assert s9.check_a_supported({"Pile-CC": s9.NOT_MET, "Wikipedia (en)": s9.MET}) is False


def test_per_unit_ratio_is_a_ratio_of_means_recomputed_within_each_replicate():
    e_g, om_g = np.array([0.2, 0.0, 0.1, 0.1]), np.array([0.02, 0.0, 0.01, 0.01])  # 0.1 / 0.01 = 10 per unit
    e_t, om_t = np.array([0.4, 0.4, 0.2, 0.2]), np.array([0.01, 0.02, 0.005, 0.005])  # 0.3 / 0.01 = 30 per unit
    v = s9.per_unit_ratio(e_g, om_g, e_t, om_t, None, 50)
    assert v["H_per_omega_group"] == pytest.approx(10.0) and v["H_per_omega_twins"] == pytest.approx(30.0) and v["ratio_group_to_twins"] == pytest.approx(1 / 3)
    assert v["ratio_interval"] is None and v["guard"] is False  # no resample, no interval, no reading
    W = np.array([[1, 1, 1, 1], [2, 0, 1, 1], [0, 4, 0, 0]], dtype=np.int32)  # the third replicate draws only the text where the group removed nothing
    rs = st.Resample(n=4, replicates=3, seed_tuple=("explicit",), W=W)
    v = s9.per_unit_ratio(e_g, om_g, e_t, om_t, rs, 50)
    rep1 = ((2 * 0.2 + 0.1 + 0.1) / (2 * 0.02 + 0.01 + 0.01)) / ((2 * 0.4 + 0.2 + 0.2) / (2 * 0.01 + 0.005 + 0.005))
    assert v["n_replicates_undefined"] == 1  # a zero denominator is dropped and counted
    assert v["ratio_interval"] == pytest.approx(list(st.percentile_interval(np.array([1 / 3, rep1]), 1)))
    assert v["omega_group_interval"][0] == pytest.approx(np.quantile([0.01, 0.015, 0.0], 0.025)) and v["guard"] is True  # both intervals lie above zero
    W0 = np.array([[0, 4, 0, 0]] * 3 + [[1, 1, 1, 1]], dtype=np.int32)  # in most replicates the group removed nothing: its label's interval starts at zero
    v0 = s9.per_unit_ratio(e_g, om_g, e_t, om_t, st.Resample(n=4, replicates=4, seed_tuple=("explicit",), W=W0), 50)
    assert v0["omega_group_interval"][0] == 0.0 and v0["guard"] is False and v0["n_replicates_undefined"] == 3
    assert s9.per_unit_ratio(e_g, om_g, e_t, om_t, rs, 9)["ratio_interval"] is None  # fewer than ten documents
    assert s9.excludes_zero([0.001, 0.2]) and s9.excludes_zero([-0.3, -0.1]) and not s9.excludes_zero([0.0, 0.2]) and not s9.excludes_zero([-0.1, 0.1]) and not s9.excludes_zero(None)


# ----------------------------------------------------------------------------- check (b)


def _pools(seed=0, n_a=16, n_b=16, n_cols=30, rows_per_doc=(4, 2)):
    rng = np.random.default_rng(seed)
    ca = rng.poisson(1.0, size=(n_a, n_cols)).astype(np.int32)
    cb = rng.poisson(1.0, size=(n_b, n_cols)).astype(np.int32)
    ca[:, :5] += rng.poisson(6.0, size=(n_a, 5)).astype(np.int32)  # five columns lean toward pool a
    cb[:, :5] = 0
    return ca, cb, np.arange(n_a) // rows_per_doc[0], np.arange(n_b) // rows_per_doc[1]


def test_s9_null_at_rows_rows_is_the_existing_shuffle_null_bit_for_bit():
    from vpd_audit.pre_reads import shuffle_null

    ca, cb, da, db = _pools()
    for seed in (0, 3):
        ref = shuffle_null(ca, cb, n_shuffles=25, master_seed=seed)
        got = s9.s9_null(ca, cb, da, db, shuffle="rows", floor="rows", n_shuffles=25, seed_tuple=(seed, "shuffle", s9.ROW_NULL_SEED))
        cols = ["shuffle", "n_members", "mass", "total_mass", "share"]
        assert got[cols].equals(ref[cols])
        assert (got["n_rows_pseudo_a"] == 16).all()


def test_the_document_floor_counts_documents():
    n_cols = 4
    ca, cb = np.zeros((16, n_cols), dtype=np.int32), np.zeros((16, n_cols), dtype=np.int32)
    ca[0:8, 0] = 5  # column 0: eight rows of pool a, all of two documents (four rows each): passes the row floor, fails the document floor
    ca[0:16:2, 1] = 5  # column 1: eight rows of pool a in eight documents: passes both
    cb[:, 2] = 5
    da, db = np.arange(16) // 4, np.arange(16) // 4
    da8 = np.arange(16) // 2
    obs = lambda floor, docs: s9.s9_null(ca, cb, docs, db, shuffle="rows", floor=floor, n_shuffles=0, seed_tuple=(0, "t")).iloc[0]  # noqa: E731
    assert int(obs("rows", da)["n_members"]) == 2  # 40 positions of 8,192 is above 1e-3, in eight rows
    assert int(obs("documents", da)["n_members"]) == 0  # column 0 in two documents, column 1 in four
    assert int(obs("documents", da8)["n_members"]) == 1  # with two-row documents column 1 is in eight documents, column 0 in four
    for shuffle in ("rows", "documents"):
        for variant in ("a", "b"):
            t = s9.s9_null(ca, cb, da8, db, shuffle=shuffle, floor="documents", variant=variant, n_shuffles=0, seed_tuple=(0, "t"))
            assert int(t.iloc[0]["n_members"]) == 1  # row -1 is the true labelling whatever is shuffled


def test_a_document_shuffle_moves_whole_documents_and_variant_b_holds_the_row_count():
    ca, cb, da, db = _pools(rows_per_doc=(2, 1))  # pool a: 8 documents of 2 rows; pool b: 16 documents of 1 row
    a = s9.s9_null(ca, cb, da, db, shuffle="documents", floor="documents", variant="a", n_shuffles=60, seed_tuple=(0, "shuffle", s9.DOC_NULL_SEED, "t"))
    b = s9.s9_null(ca, cb, da, db, shuffle="documents", floor="documents", variant="b", n_shuffles=60, seed_tuple=(0, "shuffle", s9.DOC_NULL_SEED, "t"))
    assert a.iloc[0].to_dict() == b.iloc[0].to_dict() and a.iloc[0]["n_rows_pseudo_a"] == 16 and a.iloc[0]["n_documents_pseudo_a"] == 8  # the true labelling, under both
    assert a.iloc[0]["n_members"] == 5 and a.iloc[0]["mass"] > 0  # the five planted columns, each in all eight documents of pool a
    na = a[a["shuffle"] >= 0]
    assert (na["n_documents_pseudo_a"] == 8).all() and set(na["n_rows_pseudo_a"]) <= set(range(8, 17)) and na["n_rows_pseudo_a"].nunique() > 1  # eight documents of 1 or 2 rows each
    nb = b[b["shuffle"] >= 0]
    assert set(nb["n_rows_pseudo_a"]) <= {15, 16} and nb["n_documents_pseudo_a"].nunique() > 1  # the row count nearest 16 (15 and 17 tie: the fewer documents); the document count floats
    assert na["mass"].median() < a.iloc[0]["mass"] and nb["mass"].median() < a.iloc[0]["mass"]  # a shuffled labelling loses the planted lean
    four = s9.s9_null(ca, cb, np.arange(16) // 4, db, shuffle="documents", floor="documents", n_shuffles=0, seed_tuple=(0, "t"))
    assert four.iloc[0]["n_members"] == 0  # a pool of four documents can never meet a floor of eight documents
    ca2, cb2, da2, db2 = _pools(rows_per_doc=(2, 2))
    a2 = s9.s9_null(ca2, cb2, da2, db2, shuffle="documents", floor="rows", variant="a", n_shuffles=20, seed_tuple=(0, "x"))
    b2 = s9.s9_null(ca2, cb2, da2, db2, shuffle="documents", floor="rows", variant="b", n_shuffles=20, seed_tuple=(0, "x"))
    assert a2.equals(b2)  # documents of equal size: the two variants are the same null


def test_rerun_rule_and_the_two_variants_word():
    assert s9.needs_rerun(1.0, 10.0) is True and s9.needs_rerun(4.0, 10.0) is True and s9.needs_rerun(2.0, 10.0) is True  # the bar is 2.0: within [1.0, 4.0]
    assert s9.needs_rerun(0.999, 10.0) is False and s9.needs_rerun(4.001, 10.0) is False
    assert s9.needs_rerun(0.0, 0.0) is False  # no group, no bar
    assert s9.combine_variants("clear", "clear") == "clear" and s9.combine_variants("none", "none") == "none"
    assert s9.combine_variants("clear", "marginal") == "marginal" and s9.combine_variants("clear", "none") == "marginal"


def test_existence_pair_reports_four_combinations_and_words_from_the_document_nulls():
    ca, cb, da, db = _pools(n_a=32, n_b=32, rows_per_doc=(2, 2))
    spec = s9.PairSpec("a against b", "a_vs_b", ("A", 0, 32), ("B", 0, 32))
    rows = s9.existence_pair(spec, ca, cb, da, db, n_shuffles=20, log=lambda *_: None)
    final = [r for r in rows if not r["superseded_by_rerun"]]
    assert sorted((r["floor_counts"], r["null_shuffles"], r["null_variant"]) for r in final) == sorted((f, s, v) for f in ("documents", "rows") for s, v in (("rows", "-"), ("documents", "a"), ("documents", "b")))
    for floor in ("documents", "rows"):
        fr = [r for r in final if r["floor_counts"] == floor]
        words = {r["null_variant"]: r["word_under_this_null"] for r in fr if r["null_shuffles"] == "documents"}
        assert {r["verdict_for_floor"] for r in fr} == {s9.combine_variants(words["a"], words["b"])}
        assert len({(r["n_members"], r["firing_mass_F"], r["share"]) for r in fr}) == 1  # the observed group does not depend on the null
    assert all(r["primary_floor"] == (r["floor_counts"] == "documents") for r in rows)
    reg = s9.existence_pair(spec, ca, cb, da, db, n_shuffles=20, only_rows_rows=True, log=lambda *_: None)
    assert len(reg) == 1 and reg[0]["verdict_for_floor"] is None and (reg[0]["floor_counts"], reg[0]["null_shuffles"]) == ("rows", "rows")


def test_check_b_reading():
    def table(w1, w2):
        return pd.DataFrame([{"floor_counts": f, "superseded_by_rerun": False, "slug": s, "verdict_for_floor": w if f == "documents" else "clear"}
                             for f in ("documents", "rows") for s, w in (("wikipedia_vs_pile_cc", w1), ("pile_cc_vs_wikipedia", w2), ("code_vs_pile_cc", "clear"))])

    assert s9.check_b_reading(table("clear", "none"))["reading"] == "source-leaning"  # clear in either direction
    assert s9.check_b_reading(table("none", "clear"))["reading"] == "source-leaning"
    assert s9.check_b_reading(table("marginal", "none"))["reading"] == "code-leaning stands"  # the row floor's words are not read
    assert s9.check_b_reading(table("none", "none"))["reading"] == "code-leaning stands"


# ----------------------------------------------------------------------------- check (d)

EXAMPLE = np.array([2.0, 1.0, 0.5, 0.3, 0.2, 0.12, 0.08, 0.06, 0.02, -0.08])  # the worked example, total 4.2


def test_position_statistics_worked_example():
    s = s9.position_statistics(EXAMPLE[None, :])
    assert s["S_0.05"] == 8 / 10 and s["S_minus_0.05"] == 1 / 10
    assert s["C_10"] == pytest.approx(2.0 / 4.2) and round(s["C_10"], 2) == 0.48
    assert s["q_50"] == 0.2  # the two worst positions carry 3.0 >= 2.1
    assert s["total_rise"] == pytest.approx(4.2) and s["S_1"] == 1 / 10 and s["S_0.5"] == 2 / 10 and s["S_minus_0.1"] == 0.0
    assert s["n_within_0.001_of_0.05"] == 0.0
    assert s9.position_statistics(np.array([[0.0495, 0.0505, 0.0511, 0.2]]))["n_within_0.001_of_0.05"] == 2.0


def test_shares_are_means_of_per_text_shares_and_the_worst_tenth_of_texts():
    d = np.zeros((2, 10, 4))  # two draws, ten texts, four positions
    d[0, 0] = 1.0
    d[1, 3, :2] = 1.0
    s = s9.position_statistics(d)
    assert s["S_0.05"] == pytest.approx((1.0 + 0.5) / 20)
    assert s["worst_tenth_of_texts"] == pytest.approx((4.0 + 2.0) / 6.0)  # the worst two of the twenty (draw, text) units carry everything
    assert s9.carried_by_worst(np.array([3.0, 1.0, 0.0, 0.0]), 0.25) == 0.75 and s9.smallest_share_carrying_half(np.array([1.0, 1.0, 1.0, 1.0])) == 0.5
    assert np.isnan(s9.carried_by_worst(np.array([-1.0, 0.5]), 0.5)) and np.isnan(s9.smallest_share_carrying_half(np.zeros(4)))  # no positive total, no share of it


def test_the_range_over_draws_leaves_out_a_draw_with_no_positive_total():
    per_draw = [s9.position_statistics(EXAMPLE[None, :]), s9.position_statistics(-EXAMPLE[None, :]), s9.position_statistics(2 * EXAMPLE[None, ::-1])]
    assert np.isnan(per_draw[1]["C_10"]) and not per_draw[1]["total_rise"] > 0  # a draw that lowers the divergence in total has no share of a rise
    lo, hi = s9.range_over_draws(per_draw, "C_10")
    assert lo == pytest.approx(2.0 / 4.2) and hi == pytest.approx(2.0 / 4.2)  # the two draws with a positive total; doubling and reversing change no share
    assert all(np.isnan(x) for x in s9.range_over_draws([per_draw[1]], "C_10")) and all(np.isnan(x) for x in s9.range_over_draws([], "q_50"))


def test_positions_word_at_its_boundaries():
    assert s9.positions_word([0.50, 0.60]) == s9.MOST  # the lower end is at least 0.50
    assert s9.positions_word([0.4999, 0.60]) == s9.BETWEEN
    assert s9.positions_word([0.02, 0.10]) == s9.FEW  # the upper end is at most 0.10
    assert s9.positions_word([0.02, 0.1001]) == s9.BETWEEN
    assert s9.positions_word([0.2, 0.3]) == s9.BETWEEN


def test_merge_labels_say_tokens_and_texts():
    assert s9.merge_label(1, "position") == "1 token" and s9.merge_label(64, "position") == "64 tokens" and s9.merge_label(1.0, "sequence") == "1 text" and s9.merge_label(8, "sequence") == "8 texts"
    assert s9.merge_label(256, "members") == "256 members" and s9.merge_label(28946, "set") == "28946 pieces"


def test_rung_sizes_come_from_the_schedule():
    assert s9.rung_size("5a") == ("sequence", 2) and s9.rung_size("6a") == ("sequence", 8) and s9.rung_size("2a") == ("position", 16) and s9.rung_size("2b") == ("position", 32)
    assert s9.rung_size("3") == ("position", 64) and s9.rung_size("4") == ("sequence", 1) and s9.rung_size("8") == ("pool", None)


# ----------------------------------------------------------------------------- check (c)


def test_check_c_reading_at_its_boundaries():
    assert s9.check_c_reading(0.74, 0.5) == s9.SUGGESTIVE  # at least 0.74 and above the count's
    assert s9.check_c_reading(0.7399, 0.5) == s9.NOT_SEEN
    assert s9.check_c_reading(0.9, 0.9) == s9.NOT_SEEN  # it must exceed the correlation with n_on, not equal it
    assert s9.check_c_reading(0.8, 0.95) == s9.NOT_SEEN
    assert s9.check_c_reading(0.8, -0.2) == s9.SUGGESTIVE
    assert s9.check_c_reading(float("nan"), 0.1) == s9.NOT_SEEN and s9.check_c_reading(0.9, float("nan")) == s9.NOT_SEEN


def test_the_guard_holds_the_six_analysis_modules_and_records_the_five_harness_modules():
    """The six statistics and analysis modules stay held to main's blobs; the five harness modules are recorded with their blobs as
    committed, never asserted, since later stages extended them additively."""
    assert set(s9.FROZEN_MODULES) == {"stats.py", "stats_s7.py", "analysis.py", "analysis_s7.py", "figures.py", "figures_s7.py"}
    assert set(s9.RECORDED_MODULES) == {"cells.py", "sources.py", "code_leaning.py", "grid.py", "pre_reads.py"} and not set(s9.RECORDED_MODULES) & set(s9.FROZEN_MODULES)
    assert s9.RECORDED_AT == "HEAD" and all(len(b) == 40 and int(b, 16) >= 0 for b in s9.RECORDED_MODULES.values())
    blobs = s9.frozen_blobs("main")  # the constants are checked against git inside; a changed harness module never fails the guard
    assert [r["module"] for r in blobs["modules"]] == [f"vpd_audit/{m}" for m in s9.FROZEN_MODULES] and blobs["pass"] == all(r["equal"] for r in blobs["modules"])
    assert [r["module"] for r in blobs["recorded"]] == [f"vpd_audit/{m}" for m in s9.RECORDED_MODULES]
    assert all(r[f"blob_at_{s9.RECORDED_AT}"] == s9.RECORDED_MODULES[r["module"].split("/")[1]] for r in blobs["recorded"])
