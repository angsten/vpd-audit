"""Tier 7: the merges of 2 and 4 donor tokens and the code-leaning edit on the panels. The enumeration against tiers 1 to 6 (the hashes of
tests/test_s12_labels.py, taken on the code before T2 and T4 existed), the table of cells, the launch subsets, the stores'
references and canaries, the sets held before any forward pass, the stand-in's panels and documents, and the loop on a 200-row panel with
a final partial sub-batch (the stand-in on CPU in float32; skipped when its artifacts are not in the local cache)."""

from __future__ import annotations

import dataclasses
import hashlib

import numpy as np
import pandas as pd
import pytest

from vpd_audit import cells as C
from vpd_audit import env
from vpd_audit import tier7
from vpd_audit.cells import Cell, enumerate_cells, reference_for, tier_7_cells

MAIN_LADDER = [(16, False), (64, False), (256, False), (1007, False), (1862, True)]
AS_LAUNCHED = {("D_code", 0.1): ("5a", "6a"), ("D_unif", 0.1): ("5a", "6a")}
ON_MAIN_1_TO_6 = {"main": (4516, "cd2872bffc3ef23df4a8dd0f557cee2f5ee7ec337b2efcc1865aad924ca5bc15"), "simplestories": (4512, "6ce85f13a5a02a838b25912fddc6e27ff1c63be41da33605209326830aeaeaef")}


def _sha(cells):
    return hashlib.sha256("\n".join(f"{c.tier}|{c.name}" for c in cells).encode()).hexdigest()


@pytest.mark.parametrize("run", ["main", "simplestories"])
def test_tiers_1_to_6_are_unchanged_with_tier_7_enumerated(run):
    every = enumerate_cells(runs=(run,), adaptive=AS_LAUNCHED, tier_4=True, code_leaning={run: MAIN_LADDER}, tier_5=True, tier_6=True, tier_7=True)
    base = [c for c in every if c.tier != 7]
    assert every[: len(base)] == base and all(c.tier == 7 for c in every[len(base):])
    assert (len(base), _sha(base)) == ON_MAIN_1_TO_6[run]
    assert enumerate_cells(runs=(run,), adaptive=AS_LAUNCHED, tier_4=True, code_leaning={run: MAIN_LADDER}, tier_5=True, tier_6=True) == base
    assert not any(c.tier == 7 for c in enumerate_cells(runs=("control",), tier_7=True))


def test_tier_7_is_the_table_of_cells():
    t7 = tier_7_cells("main", 8)
    merges = [c for c in t7 if c.family == "union"]
    e, e_lab = [c for c in merges if c.eval_set == "E"], [c for c in merges if c.eval_set == "E_lab"]
    panel = [c for c in t7 if c.family == "code_leaning_hard"]
    assert len(e) == 48 and len(e_lab) == 48 and len(panel) == 144 and len(t7) == 240 and len({c.name for c in t7}) == 240
    assert {(c.control, c.draw, c.rung) for c in e} == {(ctl, k, r) for ctl in ("none", "plain", "marginal") for k in range(8) for r in ("T2", "T4")}
    assert {(c.donor_pool, c.draw, c.rung) for c in e_lab} == {(p, k, r) for p in ("D_code", "D_unif", "D_prose") for k in range(8) for r in ("T2", "T4")} and all(c.control == "none" for c in e_lab)
    assert all(c.tau == 0.1 and c.background == "r0" and c.delta == "excluded" and c.descriptive and c.replicate == 0 for c in merges)
    assert all(c.donor_pool == "D_unif" for c in e)
    assert {c.eval_set for c in panel} == set(C.PANEL_EVAL_SETS["main"]) and len(C.PANEL_EVAL_SETS["main"]) == 8
    for p in C.PANEL_EVAL_SETS["main"]:
        mine = [c for c in panel if c.eval_set == p]
        assert len(mine) == 18
        assert {(c.rung, c.control, c.draw) for c in mine} == {(r, "none", 0) for r in ("G256", "G1007")} | {(r, "usage", k) for r in ("G256", "G1007") for k in range(8)}
    assert all(c.background == "ones" and c.delta == "included" and c.donor_pool == "D_code" and c.tau == 0.1 and not c.descriptive for c in panel)
    assert merges[0].name == "main/E/union/D_unif/tau0.1/r0/excl/k0/rT2" and e[-1].name == "main/E/union/D_unif/tau0.1/r0/excl/k7/rT4/ctl-marginal"
    assert panel[0].name == "main/panel_Github/code_leaning_hard/D_code/tau0.1/ones/incl/k0/rG256"
    # rung 0 of every merge is importances; of every panel edit, unmasked_delta (the loop requires it in each panel store)
    assert {reference_for(c) for c in merges} == {"importances"} and {reference_for(c) for c in panel} == {"unmasked_delta"}
    # cost: a panel pass is 200/1,024 of a pass over E
    assert panel[0].e_equivalent == pytest.approx(200 / 1024) and round(sum(c.e_equivalent for c in t7), 3) == round(48 + 24 + 144 * 200 / 1024, 3)
    counts = C.tier_counts(t7)["tier_7"]
    assert counts["cells"] == 240 and counts["by_eval_set"]["panel_ArXiv"] == 18 and counts["by_eval_set"]["E"] == 48


def test_the_stand_ins_tier_7_has_five_panels_and_its_own_sizes():
    t7 = tier_7_cells("simplestories", 2)
    panel = [c for c in t7 if c.family == "code_leaning_hard"]
    assert {c.eval_set for c in panel} == set(tier7.STAND_IN_PANELS) and {c.rung for c in panel} == {"G64", "G94"} and len(panel) == 5 * 2 * (1 + 2)


def test_the_subsets_select_tier_7_and_nothing_else():
    every = enumerate_cells(runs=("main",), adaptive=AS_LAUNCHED, tier_4=True, code_leaning={"main": MAIN_LADDER}, tier_5=True, tier_6=True, tier_7=True)
    t7 = [c for c in every if c.tier == 7]
    ms = [c for c in every if C.SUBSETS_TIER_7["merge_sizes"](c)]
    pe = [c for c in every if C.SUBSETS_TIER_7["panel_edit"](c)]
    assert set(ms) | set(pe) == set(t7) and not set(ms) & set(pe) and len(ms) == 96 and len(pe) == 144
    assert set(C.LAUNCH_SUBSETS_S12) == set(C.LAUNCH_SUBSETS_S11) | set(C.SUBSETS_TIER_7) and not set(C.SUBSETS_TIER_7) & set(C.LAUNCH_SUBSETS_S11)
    # the earlier predicates: only tier 3's `curve1_extra` (descriptive curve-1 cells) would take a tier-7 cell by itself, the E merges at 2 and
    # 4 tokens without a control or with the uniform one; a tier-3 launch filters by tier before it applies the predicate (grid.run_grid), so
    # it never does. The tier-6 subset, which is applied to the whole enumeration, takes none.
    taken = {name: [c for c in t7 if pred(c)] for name, pred in C.LAUNCH_SUBSETS_S11.items()}
    assert {n for n, v in taken.items() if v} == {"curve1_extra"} and {(c.eval_set, c.control) for c in taken["curve1_extra"]} == {("E", "none"), ("E", "plain")}
    assert not any(c.tier == 3 for c in t7) and not taken["binary_union"]
    assert not any(C.SUBSETS_TIER_7[s](c) for s in C.SUBSETS_TIER_7 for c in every if c.tier != 7)
    assert not ({"T2", "T4"} & {c.rung for c in every if c.tier != 7})


def test_the_stores_references_and_canaries():
    assert [c.name for c in tier7.reference_conditions("merge_sizes")] == ["unmasked", "importances"] and [c.name for c in tier7.reference_conditions("panel_edit")] == ["unmasked_delta"]
    can = tier7.merge_canary_cells("main")
    assert [c.name for c in can["E"]] == ["main/E/union/D_unif/tau0.1/r0/excl/k0/r2", "main/E/union/D_unif/tau0.1/r0/excl/k0/r2/ctl-plain", "main/E/union/D_unif/tau0.1/r0/excl/k0/r2/ctl-marginal"]
    assert [c.name for c in can["E_lab"]] == [f"main/E_lab/union/{p}/tau0.1/r0/excl/k0/r1" for p in ("D_code", "D_unif", "D_prose")]
    assert [c.name for c in tier7.panel_canary_cells("main")] == ["main/E_lab/code_leaning_hard/D_code/tau0.1/ones/incl/k0/rG256", "main/E_lab/code_leaning_hard/D_code/tau0.1/ones/incl/k0/rG256/ctl-usage"]
    assert [c.rung for c in tier7.panel_canary_cells("simplestories")] == ["G64", "G64"]
    # the canaries are cells of the committed enumeration, under their committed tiers
    every = {c.name: c for c in enumerate_cells(runs=("main",), adaptive=AS_LAUNCHED, tier_4=True, code_leaning={"main": MAIN_LADDER}, tier_5=True)}
    for c in can["E"] + can["E_lab"] + tier7.panel_canary_cells("main"):
        assert c.name in every and every[c.name].tier == c.tier and every[c.name].descriptive == c.descriptive, c.name
    assert tier7.committed_roots(__import__("pathlib").Path("r"), "main")[0].as_posix() == "r/grid/main" and len(tier7.committed_roots(__import__("pathlib").Path("r"), "simplestories")) == 3


class _Committed:
    roots = ("planted",)

    def __init__(self, sha):
        self.sha = sha

    def __contains__(self, n):
        return n in self.sha

    def source_sha256(self, n):
        return self.sha[n]


def test_assert_sets_holds_every_set_and_refuses_a_different_one():
    from vpd_audit.tier5 import GateFailure

    h = lambda s: hashlib.sha256(s.encode()).hexdigest()  # noqa: E731
    t7 = tier_7_cells("main", 2)
    merges = [c for c in t7 if c.family == "union"]
    panel = [c for c in t7 if c.family == "code_leaning_hard" and c.eval_set == "panel_ArXiv"]
    canaries = [c for cs in tier7.merge_canary_cells("main").values() for c in cs] + tier7.panel_canary_cells("main")
    table = pd.DataFrame([{"cell": c.name, "source_sha256": h(c.name), "matched_source_sha256": h("m" + c.name) if c.control != "none" else None} for c in merges])
    committed = {tier7.committed_twin(c): h(tier7.committed_twin(c)) for c in panel + canaries}
    records = {c.name: {"source_sha256": h(c.name), "matched_source_sha256": h("m" + c.name) if c.control != "none" else None} for c in merges}
    records.update({c.name: {"source_sha256": committed[tier7.committed_twin(c)]} for c in panel + canaries})
    n = tier7.assert_sets(merges + panel + canaries, records, _Committed(committed), table, log=lambda *_: None)
    assert n == {"merge_sets": len(merges), "merge_matched_sets": sum(c.control != "none" for c in merges), "panel_edit_sets": len(panel), "canaries": len(canaries)}
    assert tier7.committed_twin(panel[0]) == "main/E_lab/code_leaning_hard/D_code/tau0.1/ones/incl/k0/rG256" and tier7.committed_twin(merges[0]) is None
    for bad in (merges[0], merges[-1], panel[3], canaries[0]):
        with pytest.raises(GateFailure):
            tier7.assert_sets(merges + panel + canaries, {**records, bad.name: {**records[bad.name], "source_sha256": h("other")}}, _Committed(committed), table, log=lambda *_: None)
    ctl = next(c for c in merges if c.control == "marginal")
    with pytest.raises(GateFailure, match="matched set"):
        tier7.assert_sets(merges, {**records, ctl.name: {**records[ctl.name], "matched_source_sha256": h("other")}}, _Committed(committed), table, log=lambda *_: None)
    with pytest.raises(GateFailure, match="not in the label-only table"):
        tier7.assert_sets(merges, records, _Committed(committed), table.iloc[1:], log=lambda *_: None)
    with pytest.raises(GateFailure, match="in no committed store"):
        tier7.assert_sets(panel, records, _Committed({}), None, log=lambda *_: None)


def test_the_launch_runs_at_the_committed_sub_batch_size():
    from vpd_audit import env
    from vpd_audit.tier5 import CommittedTables

    committed = CommittedTables(tier7.committed_roots(env.PROJECT_ROOT / "results", "main"))
    assert tier7.assert_subbatch(64, committed, "main") == {"E": 64, "E_lab": 64}
    with pytest.raises(AssertionError, match="not the committed stores"):
        tier7.assert_subbatch(32, committed, "main")


@pytest.mark.skipif(not (env.PROJECT_ROOT / "results" / "dry_run" / "E").is_dir(), reason="the stand-in's committed stores (results/dry_run/E, dry_run_s7, dry_run_s9) are not included")
def test_the_stand_in_launch_runs_at_its_committed_sub_batch_size():
    from vpd_audit.tier5 import CommittedTables

    stand_in = CommittedTables(tier7.committed_roots(env.PROJECT_ROOT / "results", "simplestories"))
    assert tier7.assert_subbatch(64, stand_in, "simplestories") == {"E": 64, "E_lab": 64}


def test_the_stand_in_panels_and_their_documents(tmp_path):
    from vpd_audit.data import load_set, save_set

    rng = np.random.default_rng(0)
    ids = rng.integers(1, 4000, size=(1024, 512)).astype(np.int32)
    save_set(tier7.STAND_IN_SOURCE_SET, ids, np.arange(1024), {"tokenizer": "planted"}, tmp_path)
    got = tier7.prepare_stand_in_panels(tmp_path, log=lambda *_: None)
    assert set(got) == set(tier7.STAND_IN_PANELS)
    for panel, (a, b) in tier7.STAND_IN_PANELS.items():
        p_ids, p_rows, rec = load_set(tier7.stand_in_set_name(panel), tmp_path)
        assert np.array_equal(p_ids, ids[a:b]) and np.array_equal(p_rows, np.arange(a, b)) and rec["stand_in_panel_for"] == panel
    assert tier7.prepare_stand_in_panels(tmp_path, log=lambda *_: None) == got  # written once; the second call finds them equal
    save_set("panel_dry_ArXiv", ids[1:201], np.arange(1, 201), {}, tmp_path)
    with pytest.raises(AssertionError, match="is not rows 0 to 199"):
        tier7.prepare_stand_in_panels(tmp_path, log=lambda *_: None)
    assert tier7.stand_in_set_map()["panel_Github"] == "panel_dry_Github"
    docs = {p: tier7.stand_in_documents(p) for p in tier7.STAND_IN_PANELS}
    assert np.unique(docs["panel_FreeLaw"]).size == 9 and all(np.unique(docs[p]).size == 67 for p in docs if p != "panel_FreeLaw")
    assert all(np.all(np.diff(d) >= 0) and d.size == 200 for d in docs.values())


# ----------------------------------------------------------------------------- the loop on a 200-row panel (the stand-in, CPU)

RUN = "simplestories"


def _have_local_artifacts() -> bool:
    from vpd_audit import env
    from vpd_audit.artifacts import AUDIT_RUNS, decomp_checkpoint_path

    try:
        spec = AUDIT_RUNS[RUN]
        return (decomp_checkpoint_path(RUN).is_file() and (env.SETS_DIR / f"{tier7.STAND_IN_SOURCE_SET}.npz").is_file() and (env.ARTIFACTS_DIR / spec.target_run).is_dir()
                and all((env.CACHE_DIR / "donors" / f"{p}_dry_{RUN}.npz").is_file() for p in ("D_unif", "D_code", "D_prose")))
    except Exception:
        return False


@pytest.fixture(scope="module")
def panel_loop(tmp_path_factory):
    if not _have_local_artifacts():
        pytest.skip("the SimpleStories artifacts, its rows, or the stand-in's caches are not in the local cache")
    import torch

    from vpd_audit import env
    from vpd_audit.artifacts import checkpoint_hashes, load_component_model
    from vpd_audit.cells import BuiltSource, build_sources, run_cells
    from vpd_audit.code_leaning import STAND_IN_GROUP, STAND_IN_WIDE, code_leaning_sets
    from vpd_audit.data import load_set
    from vpd_audit.sources import Cache, source_hash

    torch.use_deterministic_algorithms(True, warn_only=True)
    model = load_component_model(RUN, "cpu")
    ids = load_set(tier7.STAND_IN_SOURCE_SET)[0][:200]
    caches = {f"{p}_{RUN}": Cache.load(f"{p}_dry_{RUN}") for p in ("D_unif", "D_code", "D_prose")}
    alive = np.load(env.CACHE_DIR / "donors" / f"alive_D_unif_dry_{RUN}.npy")
    cl = code_leaning_sets(caches[f"D_code_{RUN}"], caches[f"D_prose_{RUN}"], alive, group_threshold=STAND_IN_GROUP, wide_threshold=STAND_IN_WIDE)
    size = 64
    assert (size, False) in cl.ladder
    group = Cell(RUN, "code_leaning_hard", "panel_ArXiv", "D_code", 0.1, "ones", "included", 0, f"G{size}", "none", 7)
    twin = dataclasses.replace(group, control="usage")
    ref = Cell(RUN, "reference", "panel_ArXiv", None, None, "none", "included", 0, "0", "none", 1, condition="unmasked_delta")
    module_to_c = {k: model.module_to_c[k] for k in sorted(model.module_to_c)}
    sources = build_sources([group, twin], caches, {RUN: (alive, source_hash(alive))}, None, None, module_to_c, log=lambda *_: None, code_leaning={RUN: cl})
    sources[ref.name] = BuiltSource(None, {"kind": "reference"})
    root = tmp_path_factory.mktemp("tier7_loop")

    def run(cells, rows, sub, name):
        return run_cells(model, cells, ids[rows], sources, job=f"tier7_{name}", run=RUN, out_dir=root / name, precision="fp32", subbatch=sub, set_name="panel_dry_ArXiv", set_hash="", checkpoint_hashes=checkpoint_hashes(RUN),
                         importance_chunk=8, resume=True, log=lambda *_: None)

    store = run([ref, group, twin], slice(0, 200), 64, "whole")
    alone = run([ref, group, twin], slice(192, 200), 8, "tail")
    return {"root": root, "store": store, "run": run, "cells": (ref, group, twin), "sources": sources}


def test_a_200_row_panel_runs_in_sub_batches_of_64_with_a_final_partial_one(panel_loop):
    root = panel_loop["root"]
    rows = pd.read_parquet(root / "whole" / "per_sequence.parquet")
    ref, group, twin = panel_loop["cells"]
    assert panel_loop["store"].n_subbatches == 4
    for c in (ref, group, twin):
        r = rows[rows.cell == c.name].sort_values("seq")
        assert r["seq"].tolist() == list(range(200)) and np.isfinite(r["kl_mean"]).all()
    ct = pd.read_parquet(root / "whole" / "cells.parquet").set_index("cell")
    assert (ct["n_subbatches"].astype(int) == 4).all()
    # the last partial sub-batch of 8 rows gives the same divergences as those 8 rows run alone
    tail = pd.read_parquet(root / "tail" / "per_sequence.parquet")
    for c in (ref, group, twin):
        a = rows[(rows.cell == c.name) & (rows.seq >= 192)].sort_values("seq")["kl_mean"].to_numpy(np.float64)
        b = tail[tail.cell == c.name].sort_values("seq")["kl_mean"].to_numpy(np.float64)
        assert np.allclose(a, b, rtol=1e-5, atol=1e-7), c.name
    g = rows[rows.cell == group.name].sort_values("seq")
    assert (g["omega"] > 0).any() and (g["t_star_0.1"] >= 0).all()


def test_a_panel_store_without_its_rung_0_is_refused(panel_loop):
    ref, group, twin = panel_loop["cells"]
    with pytest.raises(AssertionError, match="must hold their rung 0"):
        panel_loop["run"]([group], slice(0, 8), 8, "no_ref")
