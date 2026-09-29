"""The source panels: the panel set `panel_Github`, the proximity flag, the reading, and the existence rule run
unchanged on panel pairs with every row its own document (synthetic caches)."""

import json

import numpy as np
import pandas as pd
import pytest

from vpd_audit import s9_panels as sp
from vpd_audit.constants import SEQ_LEN
from vpd_audit.data import load_set, save_set
from vpd_audit.sources import Cache

MODS = {"a": 40, "b": 20}
N_SUB = 60


def test_panel_github_is_the_first_200_rows_of_calib_github(tmp_path):
    rng = np.random.default_rng(0)
    ids = rng.integers(0, 50277, size=(260, SEQ_LEN)).astype(np.int32)
    draw = rng.permutation(5000)[:260]  # calib_github's row indices are a seeded draw, not sorted
    save_set("calib_github", ids, draw, {"label": "Github", "part": "C", "draw": "without replacement", "tokenizer": "EleutherAI/gpt-neox-20b", "master_seed": 0}, tmp_path)
    out = sp.prepare_panel_github(tmp_path, log=lambda *_: None)
    got, rows, rec = load_set("panel_Github", tmp_path)
    assert out["written"] and np.array_equal(got, ids[:200]) and np.array_equal(rows, draw[:200]) and rec["label"] == "Github" and rec["taken_from"] == "calib_github" and rec["shape"] == [200, SEQ_LEN]
    again = sp.prepare_panel_github(tmp_path, log=lambda *_: None)  # written once; a second call checks it and writes nothing
    assert not again["written"] and again["sha256_ids"] == out["sha256_ids"]
    save_set("panel_Github", ids[1:201], draw[1:201], {"label": "Github"}, tmp_path)
    with pytest.raises(AssertionError, match="not the first 200 rows"):
        sp.prepare_panel_github(tmp_path, log=lambda *_: None)


def test_the_proximity_flag():
    rows = np.array([100, 5, 101, 140, 4000, 129, 6])
    near = sp.proximity_pairs(rows, 29)
    assert sorted(zip(near["row_index_a"], near["row_index_b"])) == sorted([(100, 101), (100, 129), (101, 129), (5, 6), (140, 129)]) and (near["distance"] <= 29).all() and (near["row_a"] < near["row_b"]).all()
    assert int((near["distance"] == 1).sum()) == 2 and len(sp.proximity_pairs(rows, 0)) == 0 and len(sp.proximity_pairs(rows, 10_000)) == 21
    assert sp.PROXIMITY_ROWS == {"ArXiv": 29, "Pile-CC": 36, "Wikipedia (en)": 14, "StackExchange": 6, "Github": 56}
    counts = pd.read_csv(sp.env.PROJECT_ROOT / "results" / "grid" / "analysis" / "main" / "s9" / "document_counts.csv")  # the committed document-count table
    assert counts.groupby("source")["rows_per_document_max"].max().to_dict() == sp.PROXIMITY_ROWS


def test_the_reading_is_on_arxiv_against_wikipedia_in_either_direction():
    def table(words):
        return pd.DataFrame([{"slug": s, "floor_counts": f, "superseded_by_rerun": False, "verdict_for_floor": w if f == "documents" else "clear"} for s, w in words.items() for f in ("documents", "rows")])

    base = {"arxiv_vs_wikipedia": "none", "wikipedia_vs_arxiv": "marginal", "code_vs_arxiv": "clear", "wikipedia_vs_pile_cc": "clear"}
    r = sp.panels_reading(table(base))
    assert not r["source_leaning"] and r["reading"] == sp.NOT_CLEAR  # code pairs and the other prose pair do not enter, nor does the row floor
    for flip in ("arxiv_vs_wikipedia", "wikipedia_vs_arxiv"):
        r = sp.panels_reading(table({**base, flip: "clear"}))
        assert r["source_leaning"] and r["reading"] == sp.SOURCE_LEANING and r["words"][flip] == "clear"
    with pytest.raises(AssertionError):
        sp.panels_reading(table({"arxiv_vs_wikipedia": "none"}))


def test_the_pairs_are_the_registered_ones():
    names = {(a, b) for a, b in sp.PAIRS} | {(b, a) for a, b in sp.PAIRS}
    assert len(names) == 12 and ("ArXiv", "Wikipedia (en)") in names and ("Pile-CC", "Wikipedia (en)") in names
    assert {b for a, b in names if a == "Github"} == {"ArXiv", "Wikipedia (en)", "Pile-CC", "StackExchange"}  # code against each, both directions
    assert set(sp.PANELS) == {"ArXiv", "Wikipedia (en)", "Pile-CC", "StackExchange", "Github"} and sp.PANELS["Github"] == "panel_Github" and sp.PANEL_ROWS == 200


def test_the_existence_rule_runs_unchanged_on_panel_pairs_with_every_row_its_own_document(tmp_path):
    rng = np.random.default_rng(3)
    lean = {"ArXiv": slice(0, 12), "Wikipedia (en)": slice(12, 14), "Pile-CC": slice(12, 14), "StackExchange": slice(14, 16), "Github": slice(16, 40)}  # ArXiv and code have pieces of their own; the two prose panels share theirs
    caches, rows = {}, {}
    for source, own in lean.items():
        rate = np.full(N_SUB, 0.01)
        rate[own] = 0.2
        rate[50:] = 0.0
        caches[source] = Cache.from_dense(np.where(rng.random((24, SEQ_LEN, N_SUB)) < rate[None, None, :], 0.6, 0.0).astype(np.float32), MODS, name=source)
        rows[source] = np.sort(rng.choice(3000, size=24, replace=False))
    alive = np.ones(N_SUB, bool)
    alive[50:] = False
    out = sp.run_panel_checks("synthetic", tmp_path / sp.S9B_DIR_NAME, n_shuffles=20, caches=caches, alive=alive, row_indices=rows, proximity=sp.PROXIMITY_ROWS, log=lambda *_: None)
    table = pd.read_csv(tmp_path / sp.S9B_DIR_NAME / "check_b_panels.csv")
    assert table["slug"].nunique() == 12 and set(table["floor_counts"]) == {"documents", "rows"} and (table["rows_a"] == 24).all() and (table["documents_a"] == 24).all()  # a row is a document
    doc = table[(table["floor_counts"] == "documents") & (~table["superseded_by_rerun"]) & (table["null_shuffles"] == "documents") & (table["null_variant"] == "a")].set_index("slug")
    row_floor = table[(table["floor_counts"] == "rows") & (~table["superseded_by_rerun"]) & (table["null_shuffles"] == "documents") & (table["null_variant"] == "a")].set_index("slug")
    assert (doc["n_members"] == row_floor.loc[doc.index, "n_members"]).all() and np.allclose(doc["firing_mass_F"], row_floor.loc[doc.index, "firing_mass_F"])  # the two floors count the same thing here
    assert doc.loc["arxiv_vs_wikipedia", "verdict_for_floor"] == "clear" and doc.loc["code_vs_pile_cc", "verdict_for_floor"] == "clear" and doc.loc["wikipedia_vs_pile_cc", "verdict_for_floor"] == "none"
    assert out["reading"]["source_leaning"] and out["reading"]["words"]["arxiv_vs_wikipedia"] == "clear"
    manifest = json.loads((tmp_path / sp.S9B_DIR_NAME / "panel_manifest.json").read_text())
    assert manifest["each_row_its_own_document"] and manifest["reading"]["source_leaning"] and {p["source"] for p in manifest["proximity"]} == set(sp.PANELS)
    prox = pd.read_csv(tmp_path / sp.S9B_DIR_NAME / "panel_row_proximity.csv")
    summ = pd.read_csv(tmp_path / sp.S9B_DIR_NAME / "panel_row_proximity_summary.csv").set_index("source")
    assert all(int(summ.loc[s, "n_pairs_within"]) == int((prox["source"] == s).sum()) for s in sp.PANELS) and (prox["distance"] <= prox["source"].map(sp.PROXIMITY_ROWS)).all()
    with pytest.raises(AssertionError, match="s9b"):
        sp.run_panel_checks("synthetic", tmp_path / "elsewhere", caches=caches, alive=alive, row_indices=rows, proximity=sp.PROXIMITY_ROWS, log=lambda *_: None)
