"""The tier-4 cells, and the test that the enumeration of tiers 1 to 3 is what it was before tier 4 existed. The fixture
tests/data/cells_tiers_1_to_3_on_main.json was taken from `enumerate_cells` before tier 4 existed: adding a tier must change no
existing cell name. Per configuration: the count, the count per tier, and the SHA-256 of the "tier|name" lines in enumeration order."""

import hashlib
import json
from pathlib import Path

import pytest

from vpd_audit.cells import enumerate_cells

FIXTURE = json.loads((Path(__file__).resolve().parent / "data" / "cells_tiers_1_to_3_on_main.json").read_text())


def _kwargs(raw):
    kw = {}
    for k, v in raw.items():
        if k == "adaptive":
            kw[k] = {(key.split("|")[0], float(key.split("|")[1])): tuple(r) for key, r in v.items()}
        elif isinstance(v, list):
            kw[k] = tuple(v)
        else:
            kw[k] = v
    return kw


@pytest.mark.parametrize("config", sorted(FIXTURE["configs"]))
def test_the_names_order_and_count_of_the_cells_of_tiers_1_to_3_are_what_they_are_on_main(config):
    want = FIXTURE["configs"][config]
    cells = [c for c in enumerate_cells(**_kwargs(want["kwargs"])) if c.tier in (1, 2, 3)]
    assert len(cells) == want["n_cells"] and {str(t): sum(1 for c in cells if c.tier == t) for t in (1, 2, 3)} == want["per_tier"]
    assert cells[0].name == want["first"] and cells[-1].name == want["last"]
    assert hashlib.sha256("\n".join(f"{c.tier}|{c.name}" for c in cells).encode()).hexdigest() == want["sha256_of_tier_and_name_lines"]


# ----------------------------------------------------------------------------- the tier-4 cells themselves

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

from vpd_audit.cells import ALL_SUBSETS, SUBSETS, SUBSETS_TIER_4, Cell, build_sources, code_leaning_rung, code_leaning_size, marginal_canaries, reference_for, tier_4_cells, tier_counts  # noqa: E402
from vpd_audit.constants import SEQ_LEN  # noqa: E402
from vpd_audit.sources import Cache, source_hash  # noqa: E402

LADDER = [(16, False), (64, False), (256, False), (1007, False), (1862, True)]


def test_tier_4_is_the_registered_table_and_changes_no_existing_name():
    base = enumerate_cells(runs=("main",))
    cells = enumerate_cells(runs=("main",), tier_4=True, code_leaning={"main": LADDER})
    assert [c.name for c in cells[: len(base)]] == [c.name for c in base] and all(c.tier == 4 for c in cells[len(base):])  # tier 4 follows; tiers 1 to 3 are the same cells in the same order
    assert all(c.replicate == 0 for c in base) and not any("/rep" in c.name for c in base)  # the new field defaults to 0 and leaves every existing name as it is
    t4 = cells[len(base):]
    m = [c for c in t4 if ALL_SUBSETS["marginal"](c)]
    curve1 = [c for c in m if c.family == "union" and c.background == "r0" and c.replicate == 0]
    rep1 = [c for c in m if c.replicate == 1]
    soft = [c for c in m if c.family == "soft_erase"]
    curve2 = [c for c in m if c.family == "union" and c.background == "uniform"]
    assert (len(curve1), len(rep1), len(soft), len(curve2), len(m)) == (40, 16, 24, 24, 104) and len(m) + len(marginal_canaries("main")) == 106  # the registered count, the two canaries included
    assert {c.rung for c in curve1} == {"1", "2", "2a", "2b", "3"} and {c.rung for c in rep1} == {"1", "2"} and {c.rung for c in soft} == {c.rung for c in curve2} == {"1", "2", "3"}
    assert all(c.eval_set == "E" and c.donor_pool == "D_unif" and c.tau == 0.1 and c.delta == "excluded" and c.control == "marginal" for c in m) and {c.background for c in soft} == {"r1"}
    assert {c.draw for c in curve1} == set(range(8)) and all(c.family == "union" and c.background == "r0" for c in rep1)
    assert curve1[0].name == "main/E/union/D_unif/tau0.1/r0/excl/k0/r1/ctl-marginal" and rep1[0].name == "main/E/union/D_unif/tau0.1/r0/excl/k0/r1/ctl-marginal/rep1"
    assert [reference_for(c) for c in (curve1[0], soft[0], curve2[3])] == ["importances", "unmasked", f"stochastic/k{curve2[3].draw}"]  # each family's own rung 0; curve 2's draw under its own u^(k)
    cl = [c for c in t4 if ALL_SUBSETS["code_leaning"](c)]
    assert len(cl) == 5 * (1 + 8) and len(m) + len(cl) == len(t4)
    assert all(c.family == "code_leaning_hard" and c.eval_set == "E_lab" and c.tau == 0.1 and c.background == "ones" and c.delta == "included" and c.is_hard_zero and c.erase_family and reference_for(c) == "unmasked_delta" for c in cl)
    assert [c.rung for c in cl if c.control == "none"] == ["G16", "G64", "G256", "G1007", "G1862"] and {c.control for c in cl} == {"none", "usage"}
    assert [c.descriptive for c in cl if c.control == "none"] == [False, False, False, False, True] and sum(c.control == "usage" and c.rung == "G64" for c in cl) == 8
    assert code_leaning_size(code_leaning_rung(1007)) == 1007 and cl[-1].name == "main/E_lab/code_leaning_hard/D_code/tau0.1/ones/incl/k7/rG1862/ctl-usage"
    # no tier 4 on the control run; none without a ladder for the chain; the counts
    assert not any(c.tier == 4 for c in enumerate_cells(runs=("control",), tier_4=True, code_leaning={"control": LADDER}))
    assert sum(c.tier == 4 for c in enumerate_cells(runs=("main",), tier_4=True)) == 104 and tier_4_cells("simplestories", 2, [(16, False)])[-1].run == "simplestories"
    counts = tier_counts(cells)
    assert counts["tier_4"]["cells"] == 149 and counts["tier_4"]["by_eval_set"] == {"E": 104, "E_lab": 45, "donors": 0} and "tier_4" not in tier_counts(base)
    # the two launch subsets sit beside SUBSETS, which a test in tests/test_cells.py holds to tier 3
    assert set(SUBSETS_TIER_4) == {"marginal", "code_leaning"} and not (set(SUBSETS_TIER_4) & set(SUBSETS)) and set(ALL_SUBSETS) == set(SUBSETS) | set(SUBSETS_TIER_4)
    assert not any(pred(c) for pred in SUBSETS_TIER_4.values() for c in base) and not any(pred(c) for pred in SUBSETS.values() for c in t4)


def test_a_store_written_before_the_replicate_field_loads_with_replicate_zero():
    from dataclasses import asdict

    from vpd_audit.two_paths import _cell_from_row

    c = Cell("main", "union", "E", "D_unif", 0.1, "r0", "excluded", 3, "2", "plain", 2)
    row = {**asdict(c), "cell": c.name}
    row.pop("replicate")
    assert _cell_from_row(pd.Series(row)) == c
    m = Cell("main", "union", "E", "D_unif", 0.1, "r0", "excluded", 3, "2", "marginal", 4, replicate=1)
    back = _cell_from_row(pd.Series({**asdict(m), "cell": m.name, "replicate": np.int64(1)}))
    assert back == m and type(back.replicate) is int and back.name.endswith("/ctl-marginal/rep1")


MODS = {"a": 300, "b": 40}
N_SUB = 340


@pytest.fixture(scope="module")
def synthetic():
    rng = np.random.default_rng(99)
    code_rate, prose_rate = np.zeros(N_SUB), np.zeros(N_SUB)
    code_rate[0:80], prose_rate[0:80] = 0.05, 0.002
    code_rate[80:160], prose_rate[80:160] = 0.05, 0.012
    code_rate[160:280], prose_rate[160:280] = 0.04, 0.04
    code_rate[300:340], prose_rate[300:340] = 0.03, 0.03

    def dense(n, rate):
        return np.where(rng.random((n, SEQ_LEN, N_SUB)) < rate[None, None, :], 0.6, 0.0).astype(np.float32)

    G = {"D_code": dense(16, code_rate), "D_prose": dense(16, prose_rate), "D_unif": dense(12, (code_rate + prose_rate) / 2), "E": dense(6, (code_rate + prose_rate) / 2), "E_lab": dense(8, code_rate)}
    caches = {k: Cache.from_dense(v, MODS, name=k) for k, v in G.items()}
    alive = np.ones(N_SUB, bool)
    alive[280:300] = False
    return caches, alive


def test_build_sources_gives_the_sets_the_label_only_pre_read_judged(synthetic):
    """One implementation serves the pre-read and the cells: on a synthetic run, every tier-4 source's hash is the hash the
    pre-read's tables carry, which is what the launch asserts on the paper's model (grid.assert_sources_match_s7_pre_reads)."""
    from vpd_audit.code_leaning import code_leaning_sets
    from vpd_audit.grid import assert_sources_match_s7_pre_reads
    from vpd_audit.pre_reads import code_leaning_pre_read, marginal_pre_read, per_sequence_g_sums

    caches, alive = synthetic
    sha, norms, draws = source_hash(alive), np.ones(N_SUB), 3
    mt, _ = marginal_pre_read(caches["D_unif"], per_sequence_g_sums(caches["E"]), alive, sha, norms, "main", draws=draws, n_seeds=2, log=lambda *_: None)
    ct, cs = code_leaning_pre_read(caches["D_code"], caches["D_prose"], caches["D_unif"], caches["E_lab"], ["Github"] * 4 + ["ArXiv"] * 4, alive, sha, norms, "main", draws=draws, n_shuffles=3, log=lambda *_: None)
    assert cs["existence"]["verdict"] == "clear"
    sets = code_leaning_sets(caches["D_code"], caches["D_prose"], alive)
    assert [list(x) for x in sets.ladder] == cs["chain"]["ladder"]
    cells = [c for c in enumerate_cells(runs=("main",), draws=draws, tier_4=True, code_leaning={"main": sets.ladder}) if c.tier == 4]
    run_caches = {f"{k}_main": v for k, v in caches.items() if k.startswith("D_")}
    sources = build_sources(cells, run_caches, {"main": (alive, sha)}, None, None, MODS, log=lambda *_: None, code_leaning={"main": sets})
    comp = mt["marginal_composition"]
    comp = comp[(comp.control == "marginal") & (comp.draw.astype(str) != "pooled")]
    pre = {"dir": "synthetic", "verdict": "clear", "marginal": {(str(r), int(k), int(rep)): h for r, k, rep, h in zip(comp.rung, comp.draw, comp.replicate, comp.source_sha256)},
           "chain": {int(n): h for n, h in zip(ct["code_leaning_chain"].rung_size, ct["code_leaning_chain"].source_sha256)},
           "control": {(int(n), int(k)): h for n, k, h in zip(ct["code_leaning_control_per_draw"].rung_size, ct["code_leaning_control_per_draw"].draw, ct["code_leaning_control_per_draw"].source_sha256)}}
    out = assert_sources_match_s7_pre_reads(cells, sources, pre, log=lambda *_: None)
    n_rungs = len(sets.ladder)
    assert out["asserted"] == {"marginal": draws * (5 + 2 + 3 + 3), "chain": n_rungs, "control": n_rungs * draws}
    # the marginal sets are the same in all three families; the soft erase's and curve 2's are curve 1's at the same rung, draw, and replicate
    by = {c.name: c for c in cells}
    for c in cells:
        if c.control == "marginal" and (c.family != "union" or c.background != "r0"):
            twin = next(d for d in cells if d.control == "marginal" and d.family == "union" and d.background == "r0" and (d.rung, d.draw, d.replicate) == (c.rung, c.draw, 0))
            assert sources[c.name].record["source_sha256"] == sources[twin.name].record["source_sha256"] and by[c.name].replicate == 0
    rec = sources["main/E/union/D_unif/tau0.1/r0/excl/k1/r2/ctl-marginal/rep1"].record
    assert rec["control"]["sampler"] == "marginal" and rec["control"]["replicate"] == 1 and rec["control"]["seed_tuples"]["a"] == [0, "rand", "marginal", 1, "a", 1] and rec["n_on"] == rec["named_n_on"]
    u = sources["main/E_lab/code_leaning_hard/D_code/tau0.1/ones/incl/k2/rG64/ctl-usage"].record
    assert u["control"]["sampler"] == "usage_nearest" and u["control"]["alive_sha256"] == sha and u["matched_source_sha256"] == sources["main/E_lab/code_leaning_hard/D_code/tau0.1/ones/incl/k0/rG64"].record["source_sha256"]
    assert u["n_on"]["total"] == 64 and u["code_leaning"]["n_group"] == sets.n_group
    # a launch whose set is not the pre-read's stops before any forward pass; so does a tier-4 launch with no pre-read at all
    bad = {**pre, "marginal": {**pre["marginal"], ("2", 0, 0): "0" * 64}}
    with pytest.raises(AssertionError, match="is not the pre-read's"):
        assert_sources_match_s7_pre_reads(cells, sources, bad, log=lambda *_: None)
    with pytest.raises(AssertionError, match="no tier-4 label-only pre-read"):
        assert_sources_match_s7_pre_reads(cells, sources, None, log=lambda *_: None)
    assert assert_sources_match_s7_pre_reads([c for c in enumerate_cells(runs=("main",), draws=1) if c.tier == 1][:3], {}, None) == {"applies": False, "n_tier_4_cells": 0}


def test_the_launch_reads_the_ladder_and_the_verdict_from_the_pre_read(tmp_path, synthetic):
    from vpd_audit.grid import GridConfig, code_leaning_ladder_for_launch, read_s7_pre_reads

    cfg = GridConfig(run="main", set_map={}, pool_map={}, cache_tag="main", tiers=(4,))
    pre = {"verdict": "clear", "thresholds": {"group": 0.9, "wide": 0.75, "default_thresholds": True, "chain_forced": False}, "ladder": LADDER}
    assert code_leaning_ladder_for_launch(pre, cfg) == LADDER and code_leaning_ladder_for_launch({**pre, "verdict": "marginal"}, cfg) == LADDER
    assert code_leaning_ladder_for_launch({**pre, "verdict": "none"}, cfg) is None and code_leaning_ladder_for_launch(None, cfg) is None  # no group: no erase is run
    forced = {**pre, "verdict": "none", "thresholds": {"group": 0.65, "wide": 0.55, "default_thresholds": False, "chain_forced": True}}
    stand_in = GridConfig(run="simplestories", set_map={}, pool_map={}, cache_tag="x", tiers=(4,), code_leaning_group=0.65, code_leaning_wide=0.55, code_leaning_force=True)
    assert code_leaning_ladder_for_launch(forced, stand_in) == LADDER
    with pytest.raises(AssertionError, match="thresholds"):  # the paper's launch never takes the stand-in's forced thresholds, nor the reverse
        code_leaning_ladder_for_launch(forced, cfg)
    assert read_s7_pre_reads(tmp_path) is None and read_s7_pre_reads(None) is None


def test_the_marginal_store_gains_its_two_canaries_and_the_code_leaning_launch_prints_no_verdict():
    from vpd_audit.grid import Group, add_store_canaries, p5_pass_fail

    cells = [c for c in enumerate_cells(runs=("main",), draws=2, tier_4=True, code_leaning={"main": LADDER}) if c.tier == 4]
    g = Group("E__marginal", "E", "E", np.zeros((4, 512)), "h", [c for c in cells if ALL_SUBSETS["marginal"](c)])
    lab = Group("E_lab__code_leaning", "E_lab", "E_lab", np.zeros((4, 512)), "h", [c for c in cells if ALL_SUBSETS["code_leaning"](c)])
    n = len(g.cells)
    added = add_store_canaries([g, lab], "main", "marginal")
    assert added == {"E__marginal": ["main/E/union/D_unif/tau0.1/r0/excl/k0/r2", "main/E/union/D_unif/tau0.1/r0/excl/k0/r2/ctl-plain"]} and len(g.cells) == n + 2 and [c.tier for c in g.cells[-2:]] == [1, 2]
    assert add_store_canaries([g, lab], "main", "marginal") == {"E__marginal": []} and add_store_canaries([lab], "main", "code_leaning") == {}
    # for the new family the launch prints this and nothing else; beside an old curve it is appended
    assert p5_pass_fail({"per_curve": {}, "per_chain_rule_families": ["code_leaning_hard"]}) == "judged in the analysis under the per-chain rule"
    assert p5_pass_fail({"per_curve": {"hard_zero/E/D_unif": {"pass": True, "n_cells": 1}}, "per_chain_rule_families": []}) == "hard_zero/E/D_unif: pass"
    assert p5_pass_fail({"per_curve": {}}) == "no curve applies"
