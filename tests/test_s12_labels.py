"""The two small position rungs (T2, T4: 2 and 4 donor tokens) and the label-only checks of s12_labels.py: the panels' document
index, the merge sets, the erased sets, the removed label, and the local finish.

The enumeration hashes below were taken on vpd_audit/ as it was before the 2- and 4-token rungs (T2, T4) existed:
adding them to `sources.RUNG_SCHEDULE` must move no name, no order, and no count of tiers 1 to 6 on any run. The tokenizer tests
need gpt-neox-20b in the local cache and are skipped without it."""

from __future__ import annotations

import dataclasses
import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd
import pytest
import torch

from vpd_audit import cells as C
from vpd_audit import s12_labels as S
from vpd_audit.constants import SEQ_LEN
from vpd_audit.masks import over_removal, seed_from_tuple
from vpd_audit.sources import POSITION_SUB_RUNGS, RUNG_SCHEDULE, INTERMEDIATE_RUNGS, SMALL_POSITION_RUNGS, Cache, donor_set, module_offsets, rung_order

MAIN_LADDER = [(16, False), (64, False), (256, False), (1007, False), (1862, True)]
AS_LAUNCHED = {("D_code", 0.1): ("5a", "6a"), ("D_unif", 0.1): ("5a", "6a")}
# tiers 1 to 6 on the code before the 2- and 4-token rungs existed: (number of cells, SHA-256 of the "tier|name" lines)
ON_MAIN = {"main": (4516, "cd2872bffc3ef23df4a8dd0f557cee2f5ee7ec337b2efcc1865aad924ca5bc15"), "simplestories": (4512, "6ce85f13a5a02a838b25912fddc6e27ff1c63be41da33605209326830aeaeaef"),
           "control": (3939, "065e54ee7be3af8a9a3a7b4574593567d337c66fd675a867fdb6945526234f8d")}
M2C = {"h.0.attn.q_proj": 16, "h.0.mlp.c_fc": 24}  # 40 subcomponents; offsets 0 and 16


def _sha(cells):
    return hashlib.sha256("\n".join(f"{c.tier}|{c.name}" for c in cells).encode()).hexdigest()


# ============================================================================= the two rungs


@pytest.mark.parametrize("run", ["main", "simplestories", "control"])
def test_tiers_1_to_6_enumerate_as_before_the_small_rungs(run):
    kw = {"code_leaning": {run: MAIN_LADDER}} if run != "control" else {}
    every = C.enumerate_cells(runs=(run,), adaptive=AS_LAUNCHED, tier_4=True, tier_5=True, tier_6=True, **kw)
    assert (len(every), _sha(every)) == ON_MAIN[run]
    assert not any(c.rung in S.NEW_RUNGS for c in every)


def test_the_small_rungs_are_the_first_2_and_4_positions_of_each_draws_permutation():
    assert RUNG_SCHEDULE["T2"] == ("position", 2) and RUNG_SCHEDULE["T4"] == ("position", 4)
    for pool, n in (("D_unif", 1024), ("D_code", 512), ("D_prose", 512)):
        for k in range(8):
            perm = np.random.default_rng(seed_from_tuple((0, "posperm", pool, k))).permutation(n * SEQ_LEN)
            ds = {r: donor_set(pool, n, k, r, 0) for r in ("1", "T2", "T4", "2", "2a", "2b", "3")}
            assert ds["T2"].positions == tuple(int(p) for p in np.sort(perm[:2])) and ds["T4"].positions == tuple(int(p) for p in np.sort(perm[:4]))
            assert ds["T2"].seed_tuple == ds["1"].seed_tuple == (0, "posperm", pool, k) and ds["T2"].unit == "position"
            sets = [set(ds[r].positions) for r in ("1", "T2", "T4", "2", "2a", "2b", "3")]
            assert [len(s) for s in sets] == [1, 2, 4, 8, 16, 32, 64] and all(a < b for a, b in zip(sets[:-1], sets[1:]))


def test_the_small_rungs_sit_between_1_and_2_in_every_order():
    from vpd_audit.stats import donor_count_order, sort_rungs

    assert rung_order("T2") == pytest.approx(1 + 1 / 3) and rung_order("T4") == pytest.approx(1 + 2 / 3) and set(SMALL_POSITION_RUNGS) == {"T2", "T4"}
    assert rung_order("1") < rung_order("T2") < rung_order("T4") < rung_order("2") < rung_order("2a")
    assert sorted(["2", "T4", "3", "1", "2a", "T2", "5a", "8"], key=rung_order) == ["1", "T2", "T4", "2", "2a", "3", "5a", "8"]
    assert donor_count_order("T2") == (0, 2.0) and donor_count_order("T4") == (0, 4.0)
    assert sort_rungs(["2", "T4", "1", "T2", "4"]) == ["1", "T2", "T4", "2", "4"]
    for r in ("0", "1", "2", "2a", "2b", "3", "4", "5", "5a", "6", "6a", "7", "8", "B50", "S4", "G256"):  # every other label keeps its order
        assert rung_order(r) not in (1 + 1 / 3, 1 + 2 / 3)


def test_the_small_rungs_are_in_no_enumerated_tuple():
    from vpd_audit import figures_s9

    tuples = {"INTERMEDIATE_RUNGS": INTERMEDIATE_RUNGS, "POSITION_SUB_RUNGS": tuple(POSITION_SUB_RUNGS), "MARGINAL_RUNGS": C.MARGINAL_RUNGS, "MARGINAL_REPLICATE_1_RUNGS": C.MARGINAL_REPLICATE_1_RUNGS,
              "MARGINAL_OTHER_FAMILY_RUNGS": C.MARGINAL_OTHER_FAMILY_RUNGS, "SAME_DOMAIN_RUNGS": C.SAME_DOMAIN_RUNGS, "SAME_DOMAIN_CONTROL_RUNGS": C.SAME_DOMAIN_CONTROL_RUNGS,
              "BINARY_RUNGS": C.BINARY_RUNGS, "BINARY_EXISTING_RUNGS": C.BINARY_EXISTING_RUNGS, "RANKED_RUNGS": C.RANKED_RUNGS, "PLAIN_TERMS_CURVE_1_RUNGS": C.PLAIN_TERMS_CURVE_1_RUNGS,
              "PLAIN_TERMS_CONTROL_RUNGS": C.PLAIN_TERMS_CONTROL_RUNGS, "LISTED_ARM_RUNGS": C.LISTED_ARM_RUNGS, "figures_s9.TOKEN_RUNGS": figures_s9.TOKEN_RUNGS}
    for name, t in tuples.items():
        assert not set(t) & {"T2", "T4"}, name
    assert INTERMEDIATE_RUNGS == ("1", "2", "3", "4", "5", "6", "7") and set(POSITION_SUB_RUNGS) == {"2a", "2b"}


# ============================================================================= the panels' document index


def _tokenizer():
    try:
        from transformers import AutoTokenizer

        return AutoTokenizer.from_pretrained("EleutherAI/gpt-neox-20b", local_files_only=True)
    except Exception:  # noqa: BLE001
        pytest.skip("gpt-neox-20b tokenizer not in the local cache")


WORDS = ["the", "code", "def", "return", "x", "=", "{", "}", "\\frac{a}{b}", "$", "é", "中文", "naïve", "😀", "\n", "\n\n", "  ", "Ω", "données", "_id", "::", "->"]


def _corpus(n_docs: int, seed: int, lo: int = 5, hi: int = 400) -> list[str]:
    rng = np.random.default_rng(seed)
    return [" ".join(rng.choice(WORDS, size=int(rng.integers(lo, hi)))) for _ in range(n_docs)]


def _eot_count_documents(ids_flat: np.ndarray) -> np.ndarray:
    """The end-of-text count inside one batch (`s9_checks.block_document_index`'s rule): a token's document is the number of end-of-text
    ids before it (an end-of-text id carries the document it closes)."""
    is_eot = ids_flat == S.EOT_ID
    return np.cumsum(is_eot) - is_eot


def test_assign_documents_by_first_character_and_the_straddle_mask():
    starts = np.array([0, 10, 25])
    s = np.array([0, 8, 10, 24, 30, 9])
    e = np.array([3, 12, 10, 26, 31, 10])
    doc, straddle = S.assign_documents(starts, s, e)
    assert doc.tolist() == [0, 0, 1, 1, 2, 0] and straddle.tolist() == [False, True, False, True, False, False]
    with pytest.raises(AssertionError):
        S.assign_documents(np.array([1, 5]), s, e)


def test_the_rerun_is_the_authors_tokenization_and_its_documents_are_the_end_of_text_count_in_one_batch():
    from vpd_audit.data import tokenize_documents

    tok = _tokenizer()
    texts = _corpus(300, 0)
    assert not any(tok.eos_token in t for t in texts)
    got = S.tokenize_with_documents(texts, tok)
    ref = tokenize_documents(texts, tok, num_proc=1)
    assert got["ids"].shape == (ref.shape[0], 513) and np.array_equal(got["ids"][:, :SEQ_LEN], ref.astype(np.int64))
    assert got["batch_rows"] == [ref.shape[0]] and got["n_cut_separators"] == 0 and got["n_straddling_tokens"] == 0 and got["n_separator_piece_tokens"] == 0
    flat_ids, flat_doc = got["ids"].reshape(-1), got["doc"].reshape(-1)
    assert np.array_equal(flat_doc, _eot_count_documents(flat_ids))  # with no cut separator and no literal, the two rules agree token for token
    assert flat_doc.min() == 0 and flat_doc.max() <= 299 and np.all(np.diff(flat_doc) >= 0)


def test_batches_of_1000_documents_start_their_own_document_count_and_drop_their_tails():
    from vpd_audit.data import tokenize_documents

    tok = _tokenizer()
    texts = _corpus(2300, 1, lo=5, hi=60)
    got = S.tokenize_with_documents(texts, tok)
    ref = tokenize_documents(texts, tok, num_proc=1)
    assert np.array_equal(got["ids"][:, :SEQ_LEN], ref.astype(np.int64)) and len(got["batch_rows"]) == 3 and sum(got["batch_rows"]) == ref.shape[0]
    b = np.cumsum([0] + got["batch_rows"])
    for i, first_doc in enumerate((0, 1000, 2000)):
        block = got["doc"][b[i] : b[i + 1]].reshape(-1)
        assert block[0] == first_doc and block.max() < first_doc + 1000 and np.all(np.diff(block) >= 0)
        # within a batch the offsets and the end-of-text count differ only by the separators a chunk boundary cut (each hides one id)
        lag = (block - first_doc) - _eot_count_documents(got["ids"][b[i] : b[i + 1]].reshape(-1))
        assert lag.min() == 0 and np.all(np.diff(lag) >= 0) and lag.max() <= got["n_cut_separators"]
    # the end-of-text count over the whole stream runs behind: no end-of-text id joins two batches, and each batch's tail is dropped
    assert _eot_count_documents(got["ids"].reshape(-1))[-1] < got["doc"].reshape(-1)[-1]


def test_a_chunk_boundary_that_cuts_the_end_of_text_string():
    from vpd_audit.data import tokenize_documents

    tok = _tokenizer()
    texts = ["b" * 100, " x" * 988 + "y"]  # joined length 2,090: 20 chunks of 105 characters, and the separator sits at [100, 113)
    got = S.tokenize_with_documents(texts, tok)
    assert np.array_equal(got["ids"][:, :SEQ_LEN], tokenize_documents(texts, tok, num_proc=1).astype(np.int64)) and got["ids"].shape[0] >= 1
    assert got["n_cut_separators"] == 1 and got["n_separator_piece_tokens"] >= 2 and not (got["ids"] == S.EOT_ID).any()  # no end-of-text id: counting ids would miss the boundary
    doc, piece = got["doc"][0], got["separator_piece"][0]
    assert doc[0] == 0 and doc[-1] == 1 and np.all(doc[piece] == 0) and np.all(np.diff(doc) >= 0) and piece.sum() == got["n_separator_piece_tokens"]
    assert (doc == 1).sum() > 400 and S.row_documents(got["ids"][:1, :SEQ_LEN], got["doc"][:1, :SEQ_LEN])["majority_document"].tolist() == [1]


def test_an_end_of_text_string_inside_a_document_stays_in_that_document():
    tok = _tokenizer()
    texts = ["alpha beta <|endoftext|> gamma " * 60, "delta " * 700]
    got = S.tokenize_with_documents(texts, tok)
    assert got["n_end_of_text_literals_in_documents"] == 60
    flat_ids, flat_doc = got["ids"].reshape(-1), got["doc"].reshape(-1)
    assert set(np.unique(flat_doc).tolist()) == {0, 1} and np.all(np.diff(flat_doc) >= 0)
    first_of_1 = int(np.argmax(flat_doc == 1))
    # the end-of-text ids inside document 0 open no document (a chunk boundary may cut one of the sixty strings, or the separator)
    assert (flat_ids[:first_of_1] == S.EOT_ID).sum() >= 58 and tok.decode(flat_ids[first_of_1 : first_of_1 + 2].tolist()).strip().startswith("delta")
    # the counted rule steps down at every end-of-text id inside document 0: the two rules disagree there, as they should
    a = S.batch_agreement(got["ids"], got["doc"], got["separator_piece"], got["straddle"], 0)
    assert a["n_steps_down"] >= 58 and not a["differ_only_at_cut_strings"]


@pytest.mark.parametrize("where", ["separator start", "document start"])
def test_a_chunk_boundary_exactly_at_a_separator_or_a_document_start_cuts_nothing(where):
    """The 20 chunks are 105 characters long. With a first document of 105 characters the second chunk starts exactly where the
    end-of-text string starts; with one of 92 it starts exactly where the second document starts (the string ends at 105). Either way
    the string is whole in one chunk: one end-of-text id, no piece, no cut, and the offset rule agrees with the end-of-text count."""
    from vpd_audit.data import tokenize_documents

    tok = _tokenizer()
    texts = ["b" * 105, " x" * 985 + "y"] if where == "separator start" else ["b" * 92, " x" * 988 + "y"]
    joined = tok.eos_token.join(texts)
    chunk = (len(joined) - 1) // 20 + 1
    assert chunk == 105
    assert (joined[105 : 105 + len(tok.eos_token)] if where == "separator start" else joined[92:105]) == tok.eos_token
    got = S.tokenize_with_documents(texts, tok)
    assert np.array_equal(got["ids"][:, :SEQ_LEN], tokenize_documents(texts, tok, num_proc=1).astype(np.int64))
    assert got["n_cut_separators"] == 0 and got["n_separator_piece_tokens"] == 0 and got["n_straddling_tokens"] == 0
    flat_ids, flat_doc = got["ids"].reshape(-1), got["doc"].reshape(-1)
    assert (flat_ids == S.EOT_ID).sum() == 1 and np.array_equal(flat_doc, _eot_count_documents(flat_ids))
    first_of_1 = int(np.argmax(flat_doc == 1))
    assert flat_ids[first_of_1 - 1] == S.EOT_ID and flat_doc[first_of_1 - 1] == 0  # the end-of-text id closes document 0
    a = S.batch_agreement(got["ids"], got["doc"], got["separator_piece"], got["straddle"], 0)
    assert a["n_tokens_agreeing"] == a["n_tokens"] and a["n_steps_up"] == 0 and a["differ_only_at_cut_strings"]


def test_the_cut_string_is_the_only_disagreement_of_the_two_rules():
    tok = _tokenizer()
    got = S.tokenize_with_documents(["b" * 100, " x" * 988 + "y"], tok)
    a = S.batch_agreement(got["ids"], got["doc"], got["separator_piece"], got["straddle"], 0)
    assert a["n_steps_up"] == 1 and a["n_cut_string_runs"] == 1 and a["n_steps_up_after_a_cut_string"] == 1 and a["n_cut_string_runs_followed_by_a_step"] == 1
    assert a["differ_only_at_cut_strings"] and a["n_tokens_agreeing"] == a["step_positions"][0]


def test_batch_agreement_on_planted_tokens():
    E = S.EOT_ID
    #          doc 0      | cut pieces (doc 0) | doc 1       | eot | doc 2
    ids = np.array([5, 6, 7, 8, 9, 5, 6, E, 7, 8])
    doc = np.array([0, 0, 0, 0, 1, 1, 1, 1, 2, 2])
    piece = np.array([0, 0, 1, 1, 0, 0, 0, 0, 0, 0], bool)
    a = S.batch_agreement(ids, doc, piece, np.zeros(10, bool), 0)
    assert a["n_steps_up"] == 1 and a["step_positions"] == [4] and a["differ_only_at_cut_strings"] and a["n_tokens_agreeing"] == 4
    # a step with no cut string before it is a disagreement the rule does not allow
    a2 = S.batch_agreement(ids, doc, np.zeros(10, bool), np.zeros(10, bool), 0)
    assert not a2["differ_only_at_cut_strings"] and a2["n_steps_up_after_a_cut_string"] == 0
    # a straddling token right after the pieces carries the step one token later
    doc3 = np.array([0, 0, 0, 0, 0, 1, 1, 1, 2, 2])
    a3 = S.batch_agreement(ids, doc3, piece, np.array([0, 0, 0, 0, 1, 0, 0, 0, 0, 0], bool), 0)
    assert a3["step_positions"] == [5] and a3["differ_only_at_cut_strings"]


def test_panel_document_agreement_on_a_planted_file(tmp_path):
    tok = _tokenizer()
    docs = {"ArXiv": _corpus(90, 5, lo=150, hi=600)}
    man, _ = _manifest_for(docs, ("ArXiv",), tok, tmp_path / "sets", np.random.default_rng(0))
    out = S.panel_document_agreement(tmp_path / "s12", sets_dir=tmp_path / "sets", labels=("ArXiv",), docs=docs, tokenizer=tok, manifest=man, log=lambda *_: None)
    t = pd.read_csv(tmp_path / "s12" / S.AGREEMENT_FILE)
    assert len(t) == 1 and t["n_documents"].tolist() == [30] and out["per_source"]["ArXiv"]["differ_only_at_cut_strings"]
    assert out["per_source"]["ArXiv"]["n_tokens"] == man["parts"]["ArXiv/C"]["rows"] * 513
    man2 = json.loads(json.dumps(man))
    man2["parts"]["ArXiv/C"]["rows"] += 1
    with pytest.raises(S.LabelCheckFailure, match="the batches give"):
        S.panel_document_agreement(tmp_path / "x" / "s12", sets_dir=tmp_path / "sets", labels=("ArXiv",), docs=docs, tokenizer=tok, manifest=man2, log=lambda *_: None)


def test_row_documents_majority_without_end_of_text_ties_to_the_earlier():
    E = S.EOT_ID
    ids = np.array([[5, 5, 5, 5, 5, 5], [5, 5, 5, E, E, 5], [5, E, 5, 5, 5, 5], [E, E, E, E, E, E]])
    doc = np.array([[3, 3, 3, 4, 4, 4], [3, 3, 3, 3, 4, 4], [3, 3, 4, 4, 4, 4], [7, 7, 8, 8, 8, 8]])
    rd = S.row_documents(ids, doc)
    assert rd["majority_document"].tolist() == [3, 3, 4, 7]  # a tie goes to 3; row 1's end-of-text ids are not counted (3 of 3 against 1); an all end-of-text row takes its first token's
    assert rd["documents_touched"].tolist() == [2, 2, 2, 0] and rd["n_end_of_text"].tolist() == [0, 2, 1, 6]


def test_check_panel_rows_holds_every_row_bitwise():
    rng = np.random.default_rng(3)
    stream = rng.integers(1, 50000, size=(40, 513))
    rows = np.array([2, 7, 30])
    panel = stream[rows, :SEQ_LEN].astype(np.int32)
    assert S.check_panel_rows(stream, panel, rows, "p")["rows_equal"]
    bad = panel.copy()
    bad[1, 17] += 1
    with pytest.raises(S.LabelCheckFailure, match="1 of 3 rows differ"):
        S.check_panel_rows(stream, bad, rows, "p")
    with pytest.raises(S.LabelCheckFailure, match="outside"):
        S.check_panel_rows(stream, panel, np.array([2, 7, 40]), "p")


def _manifest_for(docs: dict[str, list[str]], labels: tuple[str, ...], tok, sets_dir: Path, rng) -> tuple[dict, dict]:
    from vpd_audit.data import hash_ids, save_set, tokenize_documents

    man = {"tokenizer": "EleutherAI/gpt-neox-20b", "eos_token_id": 0, "master_seed": 0, "max_length": 513, "parts": {}, "sets": {}}
    streams = {}
    for label in labels:
        texts = S.part_c_texts(docs, label, 0)
        ids = tokenize_documents(texts, tok, num_proc=1)
        streams[label] = ids
        man["parts"][f"{label}/C"] = {"n_docs": len(texts), "chars": int(sum(len(t) for t in texts)), "rows": int(ids.shape[0])}
        pick = np.sort(rng.choice(ids.shape[0], size=6, replace=False))
        save_set(S.PANEL_SOURCES[label], ids[pick], pick, {"label": label, "part": "C"}, sets_dir)
        man["sets"][S.PANEL_SOURCES[label]] = {"sha256_ids": hash_ids(ids[pick])}
    return man, streams


def test_panel_document_index_on_a_planted_file(tmp_path):
    from vpd_audit.data import load_set, save_set

    tok = _tokenizer()
    docs = {"ArXiv": _corpus(90, 5, lo=150, hi=600), "FreeLaw": _corpus(60, 6, lo=300, hi=900), "Other": ["unused"] * 4}
    sets_dir = tmp_path / "sets"
    man, streams = _manifest_for(docs, ("ArXiv", "FreeLaw"), tok, sets_dir, np.random.default_rng(0))
    got = S.panel_document_index(tmp_path / "s12", sets_dir=sets_dir, labels=("ArXiv", "FreeLaw"), docs=docs, tokenizer=tok, manifest=man, log=lambda *_: None)
    idx = pd.read_csv(tmp_path / "s12" / S.DOC_INDEX_FILE)
    assert list(idx.columns) == ["panel", "source", "row", "file_row_index", "majority_document", "documents_touched", "n_end_of_text"] and len(idx) == 12
    for label in ("ArXiv", "FreeLaw"):
        _, rows, _ = load_set(S.PANEL_SOURCES[label], sets_dir)
        g = idx[idx.source == label].sort_values("row")
        assert g["file_row_index"].tolist() == rows.tolist()
        # the part is one batch (under 1,000 documents): where no chunk boundary cut a separator, the end-of-text count over the 513-token
        # stream gives every token's document, and so the majority, independently of the offsets
        rerun = S.tokenize_with_documents(S.part_c_texts(docs, label, 0), tok)
        assert np.array_equal(rerun["ids"][:, :SEQ_LEN], streams[label].astype(np.int64))
        assert rerun["n_cut_separators"] == 0, "the planted corpus was chosen with no cut separator"
        eot_docs = _eot_count_documents(rerun["ids"].reshape(-1)).reshape(rerun["ids"].shape)
        want = S.row_documents(streams[label][rows], eot_docs[rows, :SEQ_LEN])
        assert g["majority_document"].tolist() == want["majority_document"].tolist() and g["documents_touched"].tolist() == want["documents_touched"].tolist()
    counts = pd.read_csv(tmp_path / "s12" / S.DOC_COUNTS_FILE)
    assert counts["distinct_documents"].tolist() == [idx[idx.source == s]["majority_document"].nunique() for s in ("ArXiv", "FreeLaw")]
    with open(tmp_path / "s12" / S.DOC_MANIFEST_FILE) as f:
        dman = json.load(f)
    assert all(p["rows_equal"] for p in dman["panels"].values()) and all(p["rows_equal_to_tokenize_documents"] for p in dman["parts"].values())
    # a stored row that is not the stream's stops the document index before any file is written
    ids, rows, _ = load_set("panel_ArXiv", sets_dir)
    ids = ids.copy()
    ids[2, 100] = (ids[2, 100] + 1) % 50000
    save_set("panel_ArXiv", ids, rows, {"label": "ArXiv", "part": "C"}, sets_dir)
    with pytest.raises(S.LabelCheckFailure, match="the panel's|record's sha256_ids"):
        S.panel_document_index(tmp_path / "other" / "s12", sets_dir=sets_dir, labels=("ArXiv",), docs=docs, tokenizer=tok, manifest=man, log=lambda *_: None)
    man2 = json.loads(json.dumps(man))
    man2["sets"]["panel_ArXiv"]["sha256_ids"] = load_set("panel_ArXiv", sets_dir)[2]["sha256_ids"]  # the manifest agrees with the changed set: the row check must catch it
    with pytest.raises(S.LabelCheckFailure, match="1 of 6 rows differ"):
        S.panel_document_index(tmp_path / "other" / "s12", sets_dir=sets_dir, labels=("ArXiv",), docs=docs, tokenizer=tok, manifest=man2, log=lambda *_: None)
    man3 = json.loads(json.dumps(man))
    man3["parts"]["FreeLaw/C"]["rows"] += 1
    with pytest.raises(S.LabelCheckFailure, match="FreeLaw/C"):
        S.panel_document_index(tmp_path / "other" / "s12", sets_dir=sets_dir, labels=("FreeLaw",), docs=docs, tokenizer=tok, manifest=man3, log=lambda *_: None)
    assert not (tmp_path / "other").exists()


def test_panel_github_must_be_the_first_200_rows_of_calib_github(tmp_path):
    from vpd_audit.data import save_set

    rng = np.random.default_rng(1)
    calib = rng.integers(1, 50000, size=(210, SEQ_LEN)).astype(np.int32)
    rows = rng.choice(5000, size=210, replace=False)
    save_set("calib_github", calib, rows, {"label": "Github", "part": "C"}, tmp_path)
    save_set("panel_Github", calib[:200], rows[:200], {"label": "Github", "part": "C"}, tmp_path)
    ids, got_rows, _ = S.load_panel("Github", tmp_path)
    assert np.array_equal(got_rows, rows[:200])
    save_set("panel_Github", calib[1:201], rows[1:201], {"label": "Github", "part": "C"}, tmp_path)
    with pytest.raises(S.LabelCheckFailure, match="first 200 rows"):
        S.load_panel("Github", tmp_path)


# ============================================================================= the label tables on planted caches, and the finish


def _save_cache(cache_dir: Path, name: str, G: np.ndarray, set_hash: str) -> Cache:
    c = Cache.from_dense(G.astype(np.float32), M2C, name)
    cache_dir.mkdir(parents=True, exist_ok=True)
    np.savez(cache_dir / f"{name}.npz", indptr=c.indptr, indices=c.indices, values=c.values)
    sha = {k: hashlib.sha256(np.ascontiguousarray(getattr(c, k)).tobytes()).hexdigest() for k in ("indptr", "indices", "values")}
    meta = {"n_subcomponents": c.n_sub, "n_sequences": c.n_sequences, "module_to_c": M2C, "module_offsets": module_offsets(M2C), "sha256": sha, "set_hash": set_hash}
    (cache_dir / f"{name}.json").write_text(json.dumps(meta))
    return Cache.load(name, cache_dir)


def _dense(rng, n_seq: int, density: float, high: list[int] | None = None, high_rate: float = 0.0, low_only: bool = False) -> np.ndarray:
    G = np.where(rng.random((n_seq, SEQ_LEN, 40)) < density, rng.uniform(0.001, 0.05 if low_only else 1.0, size=(n_seq, SEQ_LEN, 40)), 0.0)
    if high:
        on = rng.random((n_seq, SEQ_LEN, len(high))) < high_rate
        G[..., high] = np.where(on, 0.9, G[..., high])
    return G


@pytest.fixture()
def planted(tmp_path):
    """Planted caches in the donors format: D_unif (6 texts), D_code (10) whose components 16..23 are labelled 0.9 on a tenth of the
    positions and no other label above 0.05, D_prose (10) that never labels 16..23 above 0.05; so the code-leaning group and the wide
    set are those eight, and the ladder is [(8, False)]. E_lab (3 texts) and one panel (2 texts) for the removed label."""
    from vpd_audit.data import hash_ids, save_set

    rng = np.random.default_rng(11)
    cache_dir, sets_dir = tmp_path / "donors", tmp_path / "sets"
    run = "t"
    G = {"D_unif": _dense(rng, 6, 0.3), "D_code": _dense(rng, 10, 0.3, high=list(range(16, 24)), high_rate=0.1, low_only=True)}
    Gp = _dense(rng, 10, 0.3)
    Gp[..., 16:24] = np.minimum(Gp[..., 16:24], 0.05)
    G["D_prose"] = Gp
    G["E_lab"], G["panel_X"] = _dense(rng, 3, 0.3), _dense(rng, 2, 0.3)
    for name, g in G.items():
        ids = rng.integers(1, 50000, size=(g.shape[0], SEQ_LEN)).astype(np.int32)
        save_set(name, ids, np.arange(g.shape[0]), {}, sets_dir)
        _save_cache(cache_dir, f"{name}_{run}", g, hash_ids(ids))
    alive = np.ones(40, dtype=np.bool_)
    np.save(cache_dir / f"alive_D_unif_{run}.npy", alive)
    inp = S.LabelInputs(run=run, pool_sets={p: p for p in S.POOLS}, panel_caches={"X": "panel_X"}, e_lab="E_lab", draws=3, edit_sizes=(8,), group_threshold=0.9, wide_threshold=0.75,
                      committed_roots=("stores",))
    return {"inp": inp, "cache_dir": cache_dir, "sets_dir": sets_dir, "root": tmp_path / "results", "G": G}


def test_removed_label_per_text_is_over_removal():
    rng = np.random.default_rng(2)
    G = _dense(rng, 3, 0.4)
    c = Cache.from_dense(G.astype(np.float32), M2C, "g")
    rho = rng.random(40) < 0.3
    got = S.removed_label_per_text(c, rho)
    off = module_offsets(M2C)
    g_t = {k: torch.from_numpy(G[..., off[k] : off[k] + M2C[k]].astype(np.float32)) for k in sorted(M2C)}
    r_t = {k: torch.from_numpy(rho[off[k] : off[k] + M2C[k]]) for k in sorted(M2C)}
    want = over_removal(g_t, r_t).numpy()
    assert got.shape == (3,) and np.allclose(got, want, rtol=1e-6, atol=0)
    assert np.allclose(got, (G.astype(np.float32).astype(np.float64)[..., rho]).sum(axis=(1, 2)) / SEQ_LEN, rtol=1e-12)


def test_merge_tables_nest_and_hold_arm_u_to_e(planted):
    inp, cd = planted["inp"], planted["cache_dir"]
    caches = {f"{p}_{inp.run}": Cache.load(f"{p}_{inp.run}", cd) for p in S.POOLS}
    table, nesting, failures = S.merge_tables(inp, caches, np.load(cd / f"alive_D_unif_{inp.run}.npy"), M2C, log=lambda *_: None)
    assert failures == [] and len(table) == (3 + 3) * 3 * 4 and len(nesting) == 6 * 3
    assert nesting["positions_nested"].all() and nesting["sets_nested"].all()
    real = table[(table.control == "none") & (table.eval_set == "E")].sort_values(["draw", "rung"], key=lambda s: s.map(rung_order) if s.name == "rung" else s)
    for _, g in real.groupby("draw"):
        assert g["donor_tokens"].tolist() == [1, 2, 4, 8] and g["n_on"].is_monotonic_increasing
    assert set(table[table.committed_rung]["rung"]) == {"1", "2"} and set(table[~table.committed_rung]["rung"]) == {"T2", "T4"}
    assert not S.chain_nested([np.array([1, 0, 1], bool), np.array([1, 1, 0], bool)]) and S.chain_nested([np.array([0, 0, 1], bool), np.array([1, 0, 1], bool)])
    # the cells at rungs 1 and 2 carry the committed names; the new ones carry T2 and T4
    assert "t/E/union/D_unif/tau0.1/r0/excl/k0/r1" in set(table.cell) and "t/E/union/D_unif/tau0.1/r0/excl/k2/rT4/ctl-marginal" in set(table.cell)
    assert "t/E_lab/union/D_prose/tau0.1/r0/excl/k1/rT2" in set(table.cell)


def _plant_committed(root: Path, pre: Path, cache_dir: Path, run: str) -> None:
    """A committed store holding every committed-rung merge cell and every erased set with the tables' own hashes, and the loop's
    omega for the erased cells (the cache's, rounded to float32)."""
    merge = pd.read_csv(pre / S.MERGE_SETS_FILE, dtype={"rung": str})
    erased = pd.read_csv(pre / S.ERASED_SETS_FILE)
    om = pd.read_csv(pre / S.OMEGA_E_LAB_FILE)
    ct = pd.concat([merge[merge.committed_rung][["cell", "source_sha256", "n_on"]], erased[["cell", "source_sha256", "n_on"]]], ignore_index=True)
    d = root / "stores" / "fake"
    d.mkdir(parents=True)
    ct.to_parquet(d / "cells.parquet")
    ps = pd.DataFrame({"cell": om["cell"], "seq": om["seq"], "kl_mean": np.float32(0.1), "omega": om["omega_from_cache"].astype(np.float32)})
    ps.to_parquet(d / "per_sequence.parquet")


def _plant_document_index(root: Path, doc_dir: Path, run: str) -> None:
    doc_dir.mkdir(parents=True)
    pd.DataFrame([{"panel": p, "source": s, "rows": 200, "distinct_documents": 150, "rows_per_document_mean": 1.3, "rows_per_document_max": 4, "rows_sharing_a_document": 70, "part_C_documents": 900}
                  for s, p in S.PANEL_SOURCES.items()]).to_csv(doc_dir / S.DOC_COUNTS_FILE, index=False)
    pd.DataFrame({"panel": ["panel_ArXiv"], "row": [0]}).to_csv(doc_dir / S.DOC_INDEX_FILE, index=False)
    parts = {s: {"rows_equal_to_tokenize_documents": True, "n_straddling_tokens": 0, "n_separator_piece_tokens": 0, "n_cut_separators": 0, "n_end_of_text_literals_in_documents": 0} for s in S.PANEL_SOURCES}
    dman = {"panels": {p: {"rows_equal": True, "sha256_ids": f"h_{p}"} for p in S.PANEL_SOURCES.values()}, "parts": parts, "file": {"sha256": "f"},
            "files": {f: hashlib.sha256((doc_dir / f).read_bytes()).hexdigest() for f in (S.DOC_COUNTS_FILE, S.DOC_INDEX_FILE)}}
    (doc_dir / S.DOC_MANIFEST_FILE).write_text(json.dumps(dman))
    (root / "data").mkdir(parents=True)
    (root / "data" / "labeled_manifest.json").write_text(json.dumps({"sets": {p: {"sha256_ids": f"h_{p}"} for s, p in S.PANEL_SOURCES.items() if s != "Github"}}))
    s9 = root / "grid" / "analysis" / run / "s9b"
    s9.mkdir(parents=True)
    (s9 / "panel_manifest.json").write_text(json.dumps({"panels": {S.PANEL_SOURCES[s]: {"set_sha256_ids": f"h_{S.PANEL_SOURCES[s]}"} for s in S.CACHED_PANELS}}))


def test_label_tables_and_the_finish_on_planted_caches(planted):
    inp, cd, sd, root = planted["inp"], planted["cache_dir"], planted["sets_dir"], planted["root"]
    pre = root / "pre" / "s12"
    got = S.label_tables(pre, inputs=inp, cache_dir=cd, sets_dir=sd, log=lambda *_: None)
    assert got["failures"] == [] and got["n_erased_sets"] == 1 + 3
    erased = pd.read_csv(pre / S.ERASED_SETS_FILE)
    assert erased["size"].tolist() == [8] * 4 and erased["n_on"].tolist() == [8] * 4 and erased["shortfall"].tolist() == [0] * 4
    group = erased[erased.control == "none"].iloc[0]
    # the removed label: the group is components 16..23, so the panel's omega is the mean over its texts of their labels there, over 512
    omega = pd.read_csv(pre / S.OMEGA_FILE)
    Gx = planted["G"]["panel_X"].astype(np.float32).astype(np.float64)
    assert omega.loc[0, "omega_group"] == pytest.approx(Gx[..., 16:24].sum(axis=(1, 2)).mean() / SEQ_LEN, rel=1e-12) and omega.loc[0, "n_twin_draws"] == 3
    assert group["cell"] == "t/E_lab/code_leaning_hard/D_code/tau0.1/ones/incl/k0/rG8"
    # the finish passes against a committed store holding the same hashes, with a planted document-index record
    _plant_committed(root, pre, cd, inp.run)
    _plant_document_index(root, root / "grid" / "analysis" / inp.run / "s12", inp.run)
    out = S.finish_label_checks(pre, root, inputs=inp, doc_dir=root / "grid" / "analysis" / inp.run / "s12", log=lambda *_: None)
    assert out["merge_sets"]["held"]["n_equal"] == (3 + 3) * 3 * 2 and out["erased_sets"]["held"]["n_equal"] == 4
    assert out["merge_sets"]["held"]["stores"] == {"results/stores/fake": 36} and out["erased_sets"]["held"]["stores"] == {"results/stores/fake": 4}  # relative to the project
    val = out["removed_label"]["e_lab_validation"]
    assert val["max_relative_difference"] < 1e-6 and val["n_texts_bitwise_equal_in_float32"] == 4 * 3
    held = out["document_index"]["panels_held_to_committed_manifests"]
    assert set(held) == set(S.PANEL_SOURCES.values()) and held["panel_ArXiv"] == 2 and held["panel_Github"] == 1 and held["panel_FreeLaw"] == 1
    assert (pre / S.CHECKS_MD).is_file() and (pre / S.CHECKS_JSON).is_file()
    # one committed hash changed: the finish stops at that cell
    ct = pd.read_parquet(root / "stores" / "fake" / "cells.parquet")
    ct.loc[ct.cell == group["cell"], "source_sha256"] = "0" * 64
    ct.to_parquet(root / "stores" / "fake" / "cells.parquet")
    with pytest.raises(S.LabelCheckFailure, match="erased sets: .*rG8's set"):
        S.finish_label_checks(pre, root, inputs=inp, log=lambda *_: None)
    # a panel's committed sha256_ids that is not the pulled one stops the document-index part
    (root / "data" / "labeled_manifest.json").write_text(json.dumps({"sets": {"panel_ArXiv": {"sha256_ids": "other"}}}))
    with pytest.raises(S.LabelCheckFailure, match="panel_ArXiv"):
        S.finish_label_checks(pre, root, inputs=inp, doc_dir=root / "grid" / "analysis" / inp.run / "s12", log=lambda *_: None)
    # a pulled table that is not the file its manifest recorded
    (pre / S.MERGE_SETS_FILE).write_text((pre / S.MERGE_SETS_FILE).read_text() + "\n")
    with pytest.raises(S.LabelCheckFailure, match="not the file its manifest recorded"):
        S.finish_label_checks(pre, root, inputs=inp, log=lambda *_: None)


def test_hold_to_committed_refuses_a_missing_or_different_set():
    class _Committed:
        roots = ("planted",)

        def __init__(self, sha):
            self.sha, self.where = sha, {n: "store" for n in sha}

        def __contains__(self, n):
            return n in self.sha

        def source_sha256(self, n):
            return self.sha[n]

    t = pd.DataFrame({"cell": ["a", "b"], "source_sha256": ["1", "2"]})
    assert S.hold_to_committed(t, _Committed({"a": "1", "b": "2"}), "x") == {"n_equal": 2, "stores": {"store": 2}}
    with pytest.raises(S.LabelCheckFailure, match="b's set"):
        S.hold_to_committed(t, _Committed({"a": "1", "b": "3"}), "x")
    with pytest.raises(S.LabelCheckFailure, match="in no committed store"):
        S.hold_to_committed(t, _Committed({"a": "1"}), "x")


def test_the_inputs_name_the_committed_stores_and_the_panels():
    p, d = S.paper_inputs(), S.dry_inputs()
    assert p.draws == 8 and p.edit_sizes == (256, 1007) and p.committed_roots == ("grid/main", "grid/main_s9") and list(p.panel_caches.values()) == [S.PANEL_SOURCES[s] for s in S.CACHED_PANELS]
    assert d.run == "simplestories" and d.draws == 2 and d.edit_sizes == (64, 94) and d.pool_sets == {"D_unif": "D_unif_dry", "D_code": "D_code_dry", "D_prose": "D_prose_dry"}
    assert S.PANEL_SOURCES["Wikipedia (en)"] == "panel_Wikipedia__en_" and len(S.PANEL_SOURCES) == 8
    cells = S.merge_cells("main", 8)
    assert len(cells) == (3 + 3) * 8 * 4 and len({c.name for c in cells}) == len(cells)
    assert {c.name for c in cells if c.rung in S.COMMITTED_RUNGS} <= {c.name for c in C.enumerate_cells(runs=("main",), adaptive=AS_LAUNCHED, tier_4=True, code_leaning={"main": MAIN_LADDER}, tier_5=True)}
    assert all(c.descriptive for c in cells if c.rung in S.NEW_RUNGS) and not any(c.descriptive for c in cells if c.rung in S.COMMITTED_RUNGS)
    assert dataclasses.replace(cells[0], tier=1).name == cells[0].name
