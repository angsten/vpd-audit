"""The grid runner: the marker's sub-batch count is checked when the cell table is written, every store on E or E_lab gains the full
reference set, P5 is printed as pass or fail per curve only, a launch with ranked cells is held to the pre-reads' rank keys, and subset
launches keep their own summaries."""

import numpy as np
import pytest


def test_cell_table_checks_the_marker_subbatch_count(tmp_path):
    from vpd_audit.cells import BuiltSource, Cell, _record_lean, write_cell_table

    keys = ["h.0.attn.q_proj"]
    c = Cell("main", "union", "E", "D_unif", 0.1, "r0", "excluded", 0, "4", "none", 1)
    t = Cell("main", "reference", "E", None, None, "none", "excluded", 0, "0", "none", 1, condition="target")
    extra: dict = {}
    fp = {"F": "0000000000000001", "H": {k: "0000000000000001" for k in keys}, "Hd": None, "phi": ["a"]}
    _record_lean(extra, c.name, 0, fp, {k: 1 for k in keys}, {k: 1 for k in keys}, 0, 0)
    sources = {c.name: BuiltSource(None, {"n_on": {"total": 1}}), t.name: BuiltSource(None, {"kind": "reference"})}
    df = write_cell_table(tmp_path, [c, t], sources, extra, keys, n_subbatches=1)  # one sub-batch summed, the store has one: fine; the target takes the store's count
    assert df.set_index("cell").loc[t.name, "n_subbatches"] == 1 and df.set_index("cell").loc[c.name, "n_subbatches"] == 1
    with pytest.raises(AssertionError, match="sub-batches"):
        write_cell_table(tmp_path, [c, t], sources, extra, keys, n_subbatches=2)  # the store has two, the marker summed one


# --------------------------------------------------------------------------- every store carries its references; P5 prints pass or fail only


def test_every_store_on_E_or_E_lab_gains_the_full_reference_set():
    from vpd_audit.cells import Cell, _references, enumerate_cells
    from vpd_audit.grid import Group, add_store_references

    draws = 3
    cells = [c for c in enumerate_cells(runs=("main",), draws=draws) if c.tier == 2]  # a tier-2 launch: no reference cells at all
    assert not any(c.family == "reference" for c in cells)
    groups = [Group("E", "E", "E", np.zeros((4, 512)), "h", [c for c in cells if c.eval_set == "E"]),
              Group("E_lab", "E_lab", "E_lab", np.zeros((4, 512)), "h", [c for c in cells if c.eval_set == "E_lab"]),
              Group("donors_D_unif_k0_r4", "donors", "D_unif[3]", np.zeros((1, 512)), "h", [Cell("main", "union", "donors", "D_unif", 0.1, "r0", "excluded", 0, "4", "none", 3)])]
    n_before = {g.name: len(g.cells) for g in groups}
    added = add_store_references(groups, "main", draws)
    expect = {s: [c.name for c in _references("main", s, 1, draws=draws)] for s in ("E", "E_lab")}
    assert added == {"E": expect["E"], "E_lab": expect["E_lab"]} and len(expect["E"]) == 9 + 2 * draws
    for g in groups[:2]:
        names = [c.name for c in g.cells]
        assert len(names) == len(set(names)) == n_before[g.name] + 9 + 2 * draws
        assert all(c.family == "reference" and c.tier == 1 and c.eval_set == g.eval_set for c in g.cells[n_before[g.name]:])
        assert {c.condition for c in g.cells if c.family == "reference"} >= {"unmasked", "unmasked_delta", "importances", "target"}
    assert len(groups[2].cells) == 1 and "donors_D_unif_k0_r4" not in added
    # idempotent: a store that already holds its references (tier 1 in the launch) gains nothing
    again = add_store_references(groups, "main", draws)
    assert again == {"E": [], "E_lab": []} and all(len(g.cells) == n_before[g.name] + 9 + 2 * draws for g in groups[:2])


def test_p5_is_printed_as_pass_or_fail_per_curve_and_no_value_leaks():
    from vpd_audit.grid import format_summary, p5_pass_fail

    p5 = {"as_far_as_it_applies": [
        {"curve": "hard_zero/D_code/k0/r4", "curve_key": "hard_zero/E_lab/D_code", "stratum": "github", "erase": 0.4321, "control": 0.1234, "erase_exceeds_control": True},
        {"curve": "hard_zero/D_code/k0/r5", "curve_key": "hard_zero/E_lab/D_code", "stratum": "github", "erase": 0.0567, "control": 0.0891, "erase_exceeds_control": False},
        {"curve": "hard_zero/D_unif/k0/r4", "curve_key": "hard_zero/E/D_unif", "stratum": "E", "damage": 0.7777, "material": True},
    ], "n_positive": 2, "n": 3, "per_curve": {"hard_zero/E_lab/D_code": {"pass": False, "n_cells": 2}, "hard_zero/E/D_unif": {"pass": True, "n_cells": 1}}}
    assert p5_pass_fail(p5) == "hard_zero/E/D_unif: pass; hard_zero/E_lab/D_code: FAIL"
    assert p5_pass_fail({"per_curve": {}}) == "no curve applies"
    s = {"config": {"run": "main", "precision": "bf16", "subbatch": 64, "draws": 8, "job_title": "Tier 1"}, "gpu": "card", "wall_clock_s": 1.0, "max_memory_allocated_gb": 2.0,
         "cells_enumerated": 3, "cells_run": 3, "cells_failed": 0, "failed_cell_types": [], "cell_counts": {}, "adaptive": {"rule": {}, "insert": {}}, "groups": {}, "failures": [],
         "preconditions": {"available": True, "P1": {"n_pass": 1, "n": 1, "chains": [{"chain": "u", "rung_0": 0.3, "rung_8": 1.2, "difference": 0.9, "pass": True}]},
                           "P2": {"reported": []}, "P3": {"permitted_cells_with_entries_below_label": 0, "permitted_cells": 5, "hard_zero_rung_8_counts": {"a": 3}, "pass": True, "non_permitted_cells_with_entries_below_label": 1},
                           "P4": {"n_pass": 1, "n": 1, "n_empty_source_cells": 0, "n_inconsistent_pairs_not_defects": 0}, "P5": p5}}
    text = format_summary(s)
    assert text.startswith("# Tier 1 on main:") and "hard_zero/E/D_unif: pass" in text and "hard_zero/E_lab/D_code: FAIL" in text
    for leak in ("0.4321", "0.1234", "0.0567", "0.0891", "0.7777", "2/3", "n_positive"):
        assert leak not in text, leak


def test_a_launch_with_ranked_cells_must_match_the_pre_reads_rank_key_hashes(tmp_path):
    """A launch holding ranked never-named cells asserts that the SHA-256 of each ranking key it uses (the weight norms,
    the positive-label counts) equals the run's pre-reads manifest's; a mismatch of either stops; a missing hash stops when required (the paper's
    launches) and is recorded otherwise (the dry run); a launch without ranked cells is not judged."""
    import json

    from vpd_audit.cells import Cell
    from vpd_audit.grid import assert_rank_keys_match_pre_reads

    ranked = [Cell("main", "never_named_ranked", "E", "D_unif", 0.1, "ones", "included", 0, "1", "none", 3, rank_key=k, rank_end="top") for k in ("weight_norm", "positive_count")]
    plain = [Cell("main", "union", "E", "D_unif", 0.1, "r0", "excluded", 0, "1", "none", 1)]
    launch = {"weight_norm": "a" * 64, "positive_count": "c" * 64}
    m = tmp_path / "manifest.json"
    m.write_text(json.dumps({"rank_keys": {"weight_norm": "a" * 64, "positive_count": "c" * 64}}))
    ok = assert_rank_keys_match_pre_reads(launch, ranked, m, required=True, log=lambda *_: None)
    assert ok["asserted"] and ok["pre_reads"] == ok["launch"] == launch and ok["n_ranked_cells"] == 2
    m.write_text(json.dumps({"rank_keys": {"weight_norm": "a" * 64, "positive_count": "d" * 64}}))
    with pytest.raises(AssertionError, match="positive_count key .* ranking judged is not the ranking erased"):
        assert_rank_keys_match_pre_reads(launch, ranked, m, required=True, log=lambda *_: None)
    m.write_text(json.dumps({"rank_keys": {"weight_norm": "b" * 64, "positive_count": "c" * 64}}))
    with pytest.raises(AssertionError, match="weight_norm key"):
        assert_rank_keys_match_pre_reads(launch, ranked, m, required=True, log=lambda *_: None)
    with pytest.raises(AssertionError, match="no pre-reads hash"):
        assert_rank_keys_match_pre_reads(launch, ranked, tmp_path / "absent.json", required=True, log=lambda *_: None)
    m.write_text(json.dumps({"rank_keys": None, "weight_norms": None}))  # a pre-reads run that had no ranked cells (the control) records no hash
    with pytest.raises(AssertionError, match="no pre-reads hash"):
        assert_rank_keys_match_pre_reads(launch, ranked, m, required=True, log=lambda *_: None)
    m.write_text(json.dumps({"rank_keys": {"weight_norm": "a" * 64}}))  # only the keys the launch uses are needed
    assert assert_rank_keys_match_pre_reads(launch, ranked[:1], m, required=True, log=lambda *_: None)["asserted"]
    soft = assert_rank_keys_match_pre_reads(launch, ranked, tmp_path / "absent.json", required=False, log=lambda *_: None)
    assert soft["applies"] and not soft["asserted"]
    assert assert_rank_keys_match_pre_reads(launch, plain, tmp_path / "absent.json", required=True, log=lambda *_: None) == {"applies": False, "n_ranked_cells": 0}




def test_subset_launches_keep_their_own_summaries_and_two_path_checks(tmp_path):
    """A subset launch into a tier's root writes summary__<subset>.{json,md}; the two-path check can
    be restricted to the launch's own stores and writes into that summary."""
    import json

    from vpd_audit.grid import summary_stem
    from vpd_audit.two_paths import check_d_b_two_paths

    assert summary_stem(None) == "summary" and summary_stem("levels") == "summary__levels"
    root = tmp_path / "tier3"
    for name in ("E__never_named", "E__levels"):
        (root / name).mkdir(parents=True)
        (root / name / "cells.parquet").write_bytes(b"")  # discovered by name only; only_stores keeps check_store away from the other
    (root / "summary__levels.json").write_text(json.dumps({"x": 1}))
    (root / "summary.json").write_text(json.dumps({"y": 2}))
    import vpd_audit.two_paths as tp

    seen = []
    orig = tp.check_store
    tp.check_store = lambda s: (seen.append(s.name), {"n_cells_checked": 0, "n_sequence_checks": 0, "n_nan_checks": 0, "n_over_bound": 0, "n_nonfinite": 0, "n_nan_mismatch": 0, "max_ratio": 0.0, "max_ratio_at": None, "pass": True})[1]
    try:
        two = check_d_b_two_paths(root, log=lambda *_: None, summary_stem="summary__levels", only_stores=["E__levels"])
    finally:
        tp.check_store = orig
    assert seen == ["E__levels"] and two["pass"]
    assert "d_b_two_paths" in json.loads((root / "summary__levels.json").read_text()) and json.loads((root / "summary.json").read_text()) == {"y": 2}
