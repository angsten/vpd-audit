"""The post's descriptive tables (post_tables.py): the per-draw hard delete held to the committed never-named table, the coverage
arithmetic held to the committed E_lab table (every row, exactly) before it is trusted on the panels, and the code edit on E_lab the same
file the code-edit figure writes beside its E_lab variant."""

from __future__ import annotations

import json

import numpy as np
import pandas as pd
import pytest

from vpd_audit import env
from vpd_audit import post_tables as P
from vpd_audit.cells import TAU_PRIMARY, Cell

RESULTS = env.PROJECT_ROOT / "results"
TABLES = RESULTS / "grid" / "analysis" / "main"
CODE_LEANING = RESULTS / "grid" / "main" / "tier4" / "E_lab__code_leaning"
TIER7 = RESULTS / "grid" / "main_s12" / "tier7"


def _cl(eval_set: str, draw: int, rung: str, control: str, tier: int) -> str:
    return Cell("main", "code_leaning_hard", eval_set, "D_code", TAU_PRIMARY, "ones", "included", draw, rung, control, tier).name


def test_the_hard_delete_per_draw_reproduces_the_committed_means_and_counts():
    table, checks = P.hard_delete_per_draw(RESULTS)  # asserts the reference, the counts, and the two means against the committed table
    assert list(table["draw"]) == list(range(8)) and checks["n_texts"] == 1024 and checks["reference"] == "main/E/ref/unmasked_delta"
    assert list(table["random_alive_n_components"]) == [201, 222, 226, 143, 212, 154, 38, 156] == list(table["never_needed_n_components"])
    assert table["random_alive_rise"].mean() == pytest.approx(1.120206958873041, abs=1e-15)  # equal draws of equal size: the mean of the draws' means
    assert (table["never_needed_rise"] < table["random_alive_rise"]).all() and (table["never_needed_rise"] > 0).all()
    assert table["random_alive_cell"].iloc[0] == "main/E/hard_zero/D_unif/tau0.1/ones/incl/k0/r1/ctl-plain"
    assert table["never_needed_cell"].iloc[7] == "main/E/never_named_hard/D_unif/tau0.1/ones/incl/k7/r1"


def test_the_hard_delete_refuses_a_committed_mean_it_does_not_reproduce(tmp_path):
    root = tmp_path / "results"
    (root / "grid").mkdir(parents=True)
    (root / "grid" / "main").symlink_to(RESULTS / "grid" / "main", target_is_directory=True)
    (root / "grid" / "analysis" / "main").mkdir(parents=True)
    t = pd.read_csv(TABLES / "fig4_never_named.csv", dtype={"rung": str})
    t.loc[t.rung == "1", "alive_control_mean"] = 1.12
    t.to_csv(root / "grid" / "analysis" / "main" / "fig4_never_named.csv", index=False)
    with pytest.raises(AssertionError, match="1.12"):
        P.hard_delete_per_draw(root)


def test_the_coverage_arithmetic_reproduces_every_row_of_the_committed_e_lab_table():
    committed = pd.read_csv(TABLES / "s7_code_leaning_conditional.csv", float_precision="round_trip", dtype={"tau_q": str})
    idx = pd.read_csv(TABLES / "s9" / "document_index.csv")
    src = idx[idx["set"] == "E_lab"].sort_values("row")["source"].to_numpy()
    masks = {"github": src == "Github", "other": src != "Github"}
    for r in committed.itertuples():
        names = [_cl("E_lab", 0, r.rung, "none", 4)] if r.set == "group" else [_cl("E_lab", k, r.rung, "usage", 4) for k in range(8)]
        got = P.coverage(CODE_LEANING, names, r.tau_q, masks[r.stratum])
        assert got["mean_n_contributing"] == r.mean_n_contributing and got["mean_clean_prefix_fraction"] == r.mean_clean_prefix_fraction, (r.rung, r.stratum, r.set, r.tau_q, got)
    assert len(committed) == 40


def test_the_canary_stores_first_touched_positions_are_the_committed_ones():
    for tq in P.TAU_QS:
        a = P.t_star_matrix(TIER7 / "E_lab__panel_edit", [_cl("E_lab", 0, "G256", "none", 7)], tq)
        b = P.t_star_matrix(CODE_LEANING, [_cl("E_lab", 0, "G256", "none", 4)], tq)
        assert np.array_equal(a, b), tq


def test_the_panel_coverage_table_and_its_orderings():
    cov = P.panel_coverage(RESULTS)
    assert len(cov) == 4 * 2 * 2 and set(cov["n_texts"]) == {200} and set(cov["set"]) == {"group"}
    assert ((cov["mean_clean_prefix_fraction"] >= 0) & (cov["mean_clean_prefix_fraction"] <= 1)).all() and (cov["mean_n_contributing"] <= 200).all()
    for source, panel in P.COVERAGE_PANELS.items():
        store = TIER7 / f"{panel}__panel_edit"
        t = {(n, tq): P.t_star_matrix(store, [_cl(panel, 0, f"G{n}", "none", 7)], tq)[0] for n in P.EDIT_SIZES for tq in P.TAU_QS}
        for tq in P.TAU_QS:
            assert (t[(1007, tq)] <= t[(256, tq)]).all(), (source, tq)  # the larger set holds the smaller: touched no later
        for n in P.EDIT_SIZES:
            assert (t[(n, "0")] <= t[(n, "0.1")]).all(), (source, n)  # a label above 0.1 is above 0


def test_the_code_edit_on_e_lab_is_the_figures_own_csv(tmp_path):
    from vpd_audit import figures_post as F

    P.code_edit_e_lab(RESULTS).to_csv(tmp_path / "table.csv", index=False, lineterminator="\n")
    F.code_edit_figures(F.paper_inputs(with_tier7=False), tmp_path, ("lab",))
    assert (tmp_path / "table.csv").read_bytes() == (tmp_path / "code_edit.csv").read_bytes()
    t = pd.read_csv(tmp_path / "table.csv")
    assert list(t.columns) == ["source", "size", "set", "damage", "lo", "hi", "n_rows", "n_documents", "level"] and len(t) == 10 and t["lo"].isna().sum() == 2  # ArXiv: 3 documents


def test_the_command_writes_the_three_tables_and_the_manifest(tmp_path):
    out = P.post_tables(tmp_path / "s12", RESULTS, log=lambda *_: None)
    files = sorted(p.name for p in (tmp_path / "s12").iterdir())
    assert files == sorted([P.HARD_DELETE_FILE, P.COVERAGE_FILE, P.CODE_EDIT_E_LAB_FILE, P.MANIFEST_FILE])
    man = json.loads((tmp_path / "s12" / P.MANIFEST_FILE).read_text())
    assert man["hard_delete"]["random_alive_mean"] == man["hard_delete"]["random_alive_mean_committed"] and man["files"] == [P.HARD_DELETE_FILE, P.COVERAGE_FILE, P.CODE_EDIT_E_LAB_FILE]
    assert len(out["coverage"]) == 16 and len(out["hard_delete"]) == 8 and len(out["code_edit_e_lab"]) == 10
