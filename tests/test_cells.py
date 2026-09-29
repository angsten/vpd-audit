"""The enumeration of the grid's first three tiers (its invariants and counts), the lean marker record, and the cell
table (the results-schema check A14, extended). No model: the loop itself runs on SimpleStories in
tests/test_loop_simplestories.py."""

import json

import pytest

from vpd_audit.cells import Cell, _record_lean, enumerate_cells, tier_counts, write_cell_table
from vpd_audit.sources import INTERMEDIATE_RUNGS, SUB_RUNGS


def test_enumeration_invariants():
    cells = enumerate_cells()
    names = [c.name for c in cells]
    assert len(names) == len(set(names))
    by = {c.name: c for c in cells}
    # rungs 1-7 under eight draws; rung 8 once under a primary background and per draw under a uniform one
    u_r0 = [c for c in cells if c.run == "main" and c.family == "union" and c.eval_set == "E" and c.background == "r0" and c.tau == 0.1 and c.control == "none" and c.tier == 1]
    assert sorted({c.rung for c in u_r0}) == sorted(INTERMEDIATE_RUNGS + ("8",)) and len([c for c in u_r0 if c.rung == "8"]) == 1 and len([c for c in u_r0 if c.rung == "1"]) == 8
    u_un = [c for c in cells if c.run == "main" and c.family == "union" and c.eval_set == "E" and c.background == "uniform" and c.tau == 0.1 and c.control == "none" and c.tier == 1]
    assert len([c for c in u_un if c.rung == "8"]) == 8
    # rung 0 appears as the reference conditions, once per set and run, the stochastic ones per draw
    refs = [c for c in cells if c.family == "reference" and c.run == "main" and c.eval_set == "E"]
    assert len(refs) == 9 + 2 * 8 and all(c.rung == "0" for c in refs)
    # the sub-rungs once, for the code-specific hard-zero on E_lab (and its two controls)
    subs = [c for c in cells if c.rung in SUB_RUNGS and c.tier == 1 and c.run == "main"]
    assert len(subs) == 3 and all(c.family == "code_specific_hard" and c.eval_set == "E_lab" and c.draw == 0 for c in subs)
    ctl_subs = [c for c in cells if c.rung in SUB_RUNGS and c.tier == 2 and c.run == "main"]
    assert {c.control for c in ctl_subs} == {"plain", "complement"} and len(ctl_subs) == 6
    # every tier-1 family has a control in tier 2 with the same coordinates
    t1 = [c for c in cells if c.tier == 1 and c.family != "reference"]
    for c in t1:
        assert any(d.tier == 2 and d.control != "none" and (d.run, d.family, d.eval_set, d.donor_pool, d.tau, d.background, d.delta, d.draw, d.rung) == (c.run, c.family, c.eval_set, c.donor_pool, c.tau, c.background, c.delta, c.draw, c.rung) for d in cells)
    # tau = 0.5 for everything in tiers 1 and 2 that is not a reference
    t12 = [c for c in cells if c.tier in (1, 2) and c.family != "reference"]
    for c in t12:
        assert Cell(c.run, c.family, c.eval_set, c.donor_pool, 0.5, c.background, c.delta, c.draw, c.rung, c.control, 3, optional=c.optional).name in by
    # the non-primary residual settings once, the tau = 0 union, the rounded-own-g union and its control, the donor-side pass, the domain families on E
    assert by["main/E/union/D_unif/tau0.1/uniform/incl/k0/r1"].tier == 3 and "main/E/union/D_unif/tau0.1/r0/incl/k0/r1" not in by  # union r0 included is the same cell as excluded
    assert by["main/E/hard_zero/D_unif/tau0.1/ones/excl/k0/r1"].tier == 3 and by["main/E/union/D_unif/tau0/r0/excl/k3/r5"].tier == 3
    # the tau = 0 union has its matched-random control in tier 3; the residual variants keep no controls
    assert by["main/E/union/D_unif/tau0/r0/excl/k3/r5/ctl-plain"].tier == 3 and by["main/E/union/D_unif/tau0/r0/excl/k0/r8/ctl-plain"].tier == 3
    assert "main/E/union/D_unif/tau0.1/uniform/incl/k0/r1/ctl-plain" not in by and "main/E/soft_erase/D_unif/tau0.1/r1/incl/k0/r1/ctl-plain" not in by
    assert by["main/E/rounded_own_g/D_unif/tau0.1/r0/excl/k0/r8"].tier == 3 and by["main/E/rounded_own_g/D_unif/tau0.1/r0/excl/k0/r8/ctl-plain"].tier == 3
    donors = [c for c in cells if c.eval_set == "donors"]
    assert len(donors) == 2 * 8 * 2 * 3 and {c.rung for c in donors} == {"4", "7"} and {c.donor_side_reference for c in donors} == {None, "importances", "rounded"}
    assert by["main/E/code_specific_hard/D_code/tau0.1/ones/incl/k0/rS4"].tier == 3 and by["main/E_lab/code_specific_soft/D_code/tau0.1/r1/excl/k0/r1"].tier == 3
    assert all(c.optional for c in cells if c.family == "soft_erase" and c.eval_set == "E_lab" and c.donor_pool == "D_unif")
    # the adaptive rungs enter every chain when asked for
    with_adaptive = enumerate_cells(extra_rungs=("5a", "6a"))
    assert len([c for c in with_adaptive if c.rung == "5a"]) > 0 and len(with_adaptive) > len(cells)
    counts = tier_counts(cells)
    assert counts["total"]["cells"] == len(cells) and counts["tier_1"]["cells"] + counts["tier_2"]["cells"] + counts["tier_3"]["cells"] == len(cells)
    assert counts["tier_1"]["E_equivalent_passes"] == pytest.approx(2 * (57 + 64 + 57 + 57 + 64 + 25) + 2 * 0.5 * (57 + 57 + 60 + 25))


def test_lean_marker_and_cell_table(tmp_path):
    from vpd_audit.cells import BuiltSource

    keys = ["h.0.attn.q_proj", "h.0.mlp.c_fc"]
    c = Cell("main", "union", "E", "D_unif", 0.1, "r0", "excluded", 0, "4", "none", 1)
    extra: dict = {}
    fp1 = {"F": "0000000000000005", "H": {k: "0000000000000001" for k in keys}, "Hd": None, "phi": ["a", "b"]}
    fp2 = {"F": "ffffffffffffffff", "H": {k: "0000000000000002" for k in keys}, "Hd": None, "phi": ["c", "d"]}
    _record_lean(extra, c.name, 0, fp1, {k: 3 for k in keys}, {k: 1 for k in keys}, 0, 0)
    _record_lean(extra, c.name, 1, fp2, {k: 4 for k in keys}, {k: 2 for k in keys}, 5, 2)
    s = extra["cell_sums"][c.name]
    assert extra["mask_fp_subbatch"][c.name] == {"0": "0000000000000005", "1": "ffffffffffffffff"}
    assert s["F"] == "0000000000000004"  # 5 + (2^64 - 1) mod 2^64 = 4
    assert s["H"][keys[0]] == "0000000000000003" and s["n_ne_g"][keys[0]] == 7 and s["n_ne_one"][keys[1]] == 3 and s["n_below_label"] == 5 and s["n_positions_below_label"] == 2 and s["n_subbatches"] == 2
    assert "mask_fp_modules_subbatch" not in extra  # only F_i per sub-batch, running sums otherwise
    sources = {c.name: BuiltSource(None, {"n_on": {keys[0]: 3, keys[1]: 1, "total": 4}, "source_sha256": "abc", "seed_tuple": json.dumps([0, "seqperm", "D_unif", 0]),
                                          "control": {"alive_sha256": "def", "alive_run": "main"}, "donor_unit": "sequence", "donor_size": 512})}
    df = write_cell_table(tmp_path, [c], sources, extra, keys)
    assert (tmp_path / "cells.parquet").is_file() and len(df) == 1
    row = df.iloc[0]
    assert row["cell"] == c.name and row["n_on"] == 4 and row[f"n_on__{keys[0]}"] == 3 and row["mask_fp_cell"] == "0000000000000004"
    assert json.loads(row["mask_fp_modules"])["H"][keys[1]] == "0000000000000003" and row["n_ne_g_total"] == 14 and row["control_alive_sha256"] == "def" and row["tier"] == 1
    assert row["e_equivalent"] == 1.0 and row["source_sha256"] == "abc"


def test_cell_permitted_follows_the_families():
    """P3's permitted set in the grid's reading: the union and the erases (m >= g by construction), the importances
    reference of the donor-side pass, and the permitted reference conditions; hard zero, rounded own g and the rounded
    donor-side reference lie below g and are not judged."""
    from vpd_audit.grid import cell_permitted
    from vpd_audit.reference import CONDITION_BY_NAME

    mk = lambda fam, **kw: Cell("main", fam, "E", "D_unif", 0.1, kw.pop("background", "r0"), "excluded", 0, "4", "none", 1, **kw)  # noqa: E731
    assert cell_permitted(mk("union")) and cell_permitted(mk("soft_erase", background="r1")) and cell_permitted(mk("code_specific_soft", background="r1"))
    assert not cell_permitted(mk("hard_zero", background="ones")) and not cell_permitted(mk("code_specific_hard", background="ones")) and not cell_permitted(mk("rounded_own_g"))
    assert not cell_permitted(mk("never_named_hard", background="ones"))
    donors = [c for c in enumerate_cells(draws=1, runs=("main",)) if c.eval_set == "donors" and c.rung == "4"]
    assert sorted(str(c.donor_side_reference) for c in donors) == ["None", "importances", "rounded"]
    assert {c.donor_side_reference: cell_permitted(c) for c in donors} == {None: True, "importances": True, "rounded": False}
    refs = [c for c in enumerate_cells(draws=1) if c.family == "reference" and c.eval_set == "E"]
    assert refs and all(cell_permitted(c) == CONDITION_BY_NAME[c.condition].permitted for c in refs)


def test_build_sources_keys_prose_named_by_run():
    """Two runs whose prose-named sets differ: each run's code-specific cell is built from its own set, and a run
    without a prose-named set is refused."""
    import numpy as np

    from vpd_audit.cells import build_sources
    from vpd_audit.constants import SEQ_LEN
    from vpd_audit.sources import Cache, code_specific_source, source_hash

    M = {"h.0.attn.q_proj": 4}
    G = np.zeros((SEQ_LEN, 4), dtype=np.float32)
    G[0, :3] = 0.9  # the whole pool (rung 8) names subcomponents 0, 1, 2 above tau = 0.1; 3 is never named
    caches = {"D_code_main": Cache.from_dense(G, M, name="D_code_main"), "D_code_control": Cache.from_dense(G, M, name="D_code_control")}
    alive = {r: (np.array([1, 1, 1, 0], bool), "sha") for r in ("main", "control")}
    prose = {"main": {0.1: np.array([0, 1, 0, 0], bool)}, "control": {0.1: np.array([1, 0, 0, 0], bool)}}
    fc = {r: {0.1: np.array([0.5, 0.5, 0.5, 0.0])} for r in ("main", "control")}
    cells = [Cell(r, "code_specific_hard", "E_lab", "D_code", 0.1, "ones", "included", 0, "8", "none", 1) for r in ("main", "control")]
    out = build_sources(cells, caches, alive, prose, fc, M, log=lambda *_: None)
    rho_u = np.array([1, 1, 1, 0], bool)
    for c in cells:
        expect = code_specific_source(rho_u, prose[c.run][0.1])
        assert np.array_equal(out[c.name].rho, expect) and out[c.name].record["prose_named_run"] == c.run and out[c.name].record["prose_named_sha256"] == source_hash(prose[c.run][0.1])
    assert not np.array_equal(out[cells[0].name].rho, out[cells[1].name].rho) and out[cells[0].name].record["source_sha256"] != out[cells[1].name].record["source_sha256"]
    with pytest.raises(AssertionError, match="prose-named set of run 'control'"):
        build_sources(cells, caches, alive, {"main": prose["main"]}, {"main": fc["main"]}, M, log=lambda *_: None)


def test_enumeration_of_the_never_named_chain_and_tier_counts():
    """The never-named erase chain is listed first in tier 3 for each run, on E from D_unif under ones
    with Delta included: rungs 1 to 7 (and 5a, 6a when inserted) under eight draws, B50 and B75 per draw, rung 8 once, plus
    the Delta-excluded rung 8 and the strict tau = 0 cell; a hard-zero family in every respect; the tier counts."""
    from vpd_audit.grid import cell_permitted

    cells = enumerate_cells()
    by = {c.name: c for c in cells}
    for run in ("main", "control"):
        nn = [c for c in cells if c.family == "never_named_hard" and c.run == run]
        assert next(c for c in cells if c.run == run and c.tier == 3).family == "never_named_hard"
        assert all(c.tier == 3 and c.eval_set == "E" and c.donor_pool == "D_unif" and c.background == "ones" and c.control == "none" for c in nn)
        assert all(c.is_hard_zero and c.erase_family and not cell_permitted(c) for c in nn)
        assert len([c for c in nn if c.rung == "B50"]) == 8 and len([c for c in nn if c.rung == "B75"]) == 8 and len([c for c in nn if c.rung == "1"]) == 8
        assert sorted(c.name for c in nn if c.rung == "8") == [f"{run}/E/never_named_hard/D_unif/tau0.1/ones/excl/k0/r8", f"{run}/E/never_named_hard/D_unif/tau0.1/ones/incl/k0/r8",
                                                                f"{run}/E/never_named_hard/D_unif/tau0/ones/incl/k0/r8"]
        assert len(nn) == 7 * 8 + 2 * 8 + 3
        assert not any(c.tau == 0.5 for c in nn)  # no tau = 0.5 mirror: the chain is tier 3 itself
    with_adaptive = [c for c in enumerate_cells(extra_rungs=("5a", "6a"), runs=("main",)) if c.family == "never_named_hard"]
    assert len(with_adaptive) == 9 * 8 + 2 * 8 + 3 == 91
    order = [c.rung for c in with_adaptive if c.draw == 0 and c.delta == "included" and c.tau == 0.1]
    assert order == ["1", "2", "3", "4", "5", "5a", "6", "6a", "7", "B50", "B75", "8"]
    counts = tier_counts(cells)
    assert counts["tier_3"]["cells"] >= 2 * 75 and by["main/E/never_named_hard/D_unif/tau0.1/ones/incl/k3/rB75"].e_equivalent == 1.0


def test_enumeration_of_the_level_cells_the_ranked_pair_the_descriptive_rungs_and_the_subsets():
    """Six level cells per run (the alive set at s in {0.25, 0.5, 0.75}, the never-named set at its
    labels and at 1; tier 3, E, D_unif, tau 0.1, Delta excluded, no draws, permitted, rung 0 the importances reference or
    unmasked); the ranked never-named pair on the main run only (four chains of nine rungs, hard-zero, ones, Delta
    included); rungs 2a and 2b of curve 1 and its plain control per draw, flagged descriptive; the never-named chain still
    first in tier 3; every launch subset under 600 cells per store on the main run."""
    from vpd_audit.cells import FAMILY_MASK_KIND, RANKED_RUNGS, SUBSETS, reference_for
    from vpd_audit.grid import cell_permitted

    cells = enumerate_cells()
    by = {c.name: c for c in cells}
    assert len(by) == len(cells)
    for run in ("main", "control"):
        assert next(c for c in cells if c.run == run and c.tier == 3).family == "never_named_hard"
        lv = [c for c in cells if c.run == run and c.family == "level"]
        assert sorted(c.name for c in lv) == sorted(f"{run}/E/level/D_unif/tau0.1/{bg}/excl/k0/r8/s{s:g}" for bg in ("r0", "r1") for s in (0.25, 0.5, 0.75))
        assert all(c.tier == 3 and c.eval_set == "E" and c.donor_pool == "D_unif" and c.tau == 0.1 and c.delta == "excluded" and c.draw == 0 and c.rung == "8" and c.control == "none" for c in lv)
        assert all(cell_permitted(c) and not c.is_hard_zero and not c.erase_family and not c.descriptive and c.e_equivalent == 1.0 for c in lv)
        assert {reference_for(c) for c in lv if c.background == "r0"} == {"importances"} and {reference_for(c) for c in lv if c.background == "r1"} == {"unmasked"}
        ds = [c for c in cells if c.run == run and c.descriptive]
        assert len(ds) == 2 * 8 * 2 and {c.rung for c in ds} == {"2a", "2b"} and {c.control for c in ds} == {"none", "plain"} and {c.draw for c in ds} == set(range(8))
        assert all(c.family == "union" and c.eval_set == "E" and c.donor_pool == "D_unif" and c.tau == 0.1 and c.background == "r0" and c.delta == "excluded" and c.tier == 3 for c in ds)
        assert f"{run}/E/union/D_unif/tau0.1/r0/excl/k3/r2b/ctl-plain" in by
        assert not any(c.descriptive for c in cells if c.run == run and c.rung not in ("2a", "2b"))
    rk = [c for c in cells if c.family == "never_named_ranked"]
    assert {c.run for c in rk} == {"main"} and len(rk) == 4 * 9
    assert all(c.is_hard_zero and c.erase_family and not cell_permitted(c) and c.eval_set == "E" and c.donor_pool == "D_unif" and c.tau == 0.1 and c.background == "ones" and c.delta == "included"
               and c.draw == 0 and c.control == "none" and c.tier == 3 and reference_for(c) == "unmasked_delta" for c in rk)
    assert FAMILY_MASK_KIND["never_named_ranked"] == "hard_zero" and RANKED_RUNGS == ("1", "2", "3", "4", "5", "6", "7", "B50", "B75")
    for key in ("weight_norm", "positive_count"):
        for end in ("top", "bottom"):
            chain = [c for c in rk if c.rank_key == key and c.rank_end == end]
            assert [c.rung for c in chain] == list(RANKED_RUNGS) and chain[0].name == f"main/E/never_named_ranked/D_unif/tau0.1/ones/incl/k0/r1/{key}-{end}"
    # the launch subsets, on the main run's tier 3
    t3 = [c for c in cells if c.tier == 3 and c.run == "main"]
    sizes = {}
    for name, pred in SUBSETS.items():
        sel = [c for c in t3 if pred(c)]
        by_set: dict[str, int] = {}
        for c in sel:
            by_set[c.eval_set] = by_set.get(c.eval_set, 0) + 1
        assert sel and max(by_set.values()) < 600, (name, by_set)
        sizes[name] = by_set
    assert sizes["levels"] == {"E": 6} and sizes["ranked"] == {"E": 36} and sizes["never_named"] == {"E": 75} and sizes["donor_side"] == {"donors": 48}
    assert sizes["curve1_extra"] == {"E": 32 + 2 * 57} and sizes["tau0_union"] == {"E": 2 * 57} and sizes["editing_extra"] == {"E_lab": 60 + 60 + 57, "E": 60}
    c1x = [c for c in t3 if SUBSETS["curve1_extra"](c)]
    assert all(c.descriptive or c.tau == 0.5 for c in c1x) and sum(c.descriptive for c in c1x) == 32
    ed = [c for c in t3 if SUBSETS["editing_extra"](c)]
    assert {(c.family, c.eval_set, c.tau) for c in ed} == {("code_specific_hard", "E_lab", 0.5), ("code_specific_hard", "E", 0.1), ("code_specific_soft", "E_lab", 0.1)}
    assert {c.control for c in ed if c.eval_set == "E_lab" and c.family == "code_specific_hard"} == {"none", "complement"}
    # no subset takes a cell from the cut list: the tau = 0.5 mirrors other than curve 1 and the code-specific hard zero, the residual variants, the rounded-own-g union, the plain code families on E
    taken = [c for c in t3 if any(p(c) for p in SUBSETS.values())]
    assert not any(c.family == "rounded_own_g" or (c.family in ("hard_zero", "soft_erase") and c.donor_pool == "D_code" and c.eval_set == "E") or (c.family == "soft_erase" and c.tau == 0.5) for c in taken)
    assert not any(c.delta == "included" and c.family in ("union", "soft_erase") for c in taken)
    # the control run has no ranked cells and its subsets skip them; with two draws the descriptive rungs are 8 per run
    assert [c for c in enumerate_cells(runs=("control",)) if SUBSETS["ranked"](c)] == []
    assert len([c for c in enumerate_cells(runs=("main",), draws=2) if c.descriptive]) == 8
