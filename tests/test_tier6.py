"""The binary union's families, the per-text path's `own_round`, the permitted labels, tier 6's enumeration against tiers 1 to 5 as
they were before it, and the launch's assertion that every set is its committed twin's.

The hashes of tiers 1 to 5 below were taken from `enumerate_cells` before tier 6 existed: adding a tier must change no existing cell name.
Tier 6 must move no name, no order, and no count of the earlier tiers."""

from __future__ import annotations

import dataclasses
import hashlib
from dataclasses import asdict

import numpy as np
import pandas as pd
import pytest
import torch

from vpd_audit import cells as C
from vpd_audit import tier6
from vpd_audit.cells import Cell, enumerate_cells, reference_for, tier_6_cells
from vpd_audit.masks import apply_binary_source_per_text, rounded_mask
from vpd_audit.reference import CONDITION_BY_NAME, build_condition_masks
from vpd_audit.sources import OWN_ROUND_VALUES, ROUNDED0_FAMILY, family_masks, family_masks_per_text, rho_tensors

MAIN_LADDER = [(16, False), (64, False), (256, False), (1007, False), (1862, True)]
AS_LAUNCHED = {("D_code", 0.1): ("5a", "6a"), ("D_unif", 0.1): ("5a", "6a")}
# taken before tier 6 existed: tiers 1 to 5 of each run with the main ladder and the adaptive rungs as launched, and tier 5 alone
ON_MAIN = {"main": {"n": 4458, "n_tier_5": 334, "sha_1_to_5": "7deafba22d9a7794962ca6bbd5d6bd40cf2529ef8bdba331ae82837030e9ae32", "sha_5": "3fcc1fc5339c8b5352cf0e3eb730aab21a8f8051cb973c3d2f09cdef3558b47b"},
           "simplestories": {"n": 4454, "n_tier_5": 330, "sha_1_to_5": "95ec24f8e4e47f1870f6e7d2adf72e978d0d83d57e5a1da8c4f68a5dfc3eeee1", "sha_5": "7372fb9f1d2377e0a56691e75c6c4778475c1b14f231368db798a8f8067b14cf"}}
KEY = "h.0.attn.q_proj"


def _sha(cells):
    return hashlib.sha256("\n".join(f"{c.tier}|{c.name}" for c in cells).encode()).hexdigest()


def _one_token(values, dtype=torch.float32):
    return {KEY: torch.tensor(values, dtype=dtype).view(1, 1, -1)}


def _rho(values, dtype=torch.float32):
    return rho_tensors(np.array(values, dtype=bool), {KEY: len(values)}, dtype, "cpu")


# ----------------------------------------------------------------------------- the masks


@pytest.mark.parametrize("dtype", [torch.float32, torch.bfloat16])
def test_the_worked_example_for_both_binary_families(dtype):
    """g = (0.9, 0.05, 0, 0), donors name (0, 0, 1, 0): the worked example's table, row by row, and which forms are permitted."""
    g, rho = _one_token([0.9, 0.05, 0.0, 0.0], dtype), _rho([False, False, True, False], dtype)
    want = lambda v: torch.tensor(v, dtype=dtype)  # noqa: E731
    frac, _, p_frac = family_masks("union", g, rho, background="r0", delta="excluded")
    prim, d_prim, p_prim = family_masks(ROUNDED0_FAMILY, g, rho, background="r0", delta="excluded", tau=0.1)
    sec, _, p_sec = family_masks("rounded_own_g", g, rho, background="r0", delta="excluded", tau=0.1)
    assert torch.equal(frac[KEY][0, 0], torch.tensor([0.9, 0.05, 1.0, 0.0], dtype=dtype)) and p_frac
    assert torch.equal(prim[KEY][0, 0], want([1, 1, 1, 0])) and p_prim and d_prim is None
    assert torch.equal(sec[KEY][0, 0], want([1, 0, 1, 0])) and not p_sec
    assert torch.equal(rounded_mask(g[KEY], 0.0)[0, 0], want([1, 1, 0, 0])) and torch.equal(rounded_mask(g[KEY], 0.1)[0, 0], want([1, 0, 0, 0]))
    # the primary is at or above g everywhere; the secondary drops c_2 below its label; in both the donor raises only c_3
    assert bool((prim[KEY] >= g[KEY]).all()) and float((sec[KEY] - g[KEY]).min()) < 0 and bool(sec[KEY][0, 0, 1] < g[KEY][0, 0, 1])
    assert torch.equal(prim[KEY] - rounded_mask(g[KEY], 0.0), want([0, 0, 1, 0]).view(1, 1, -1)) and torch.equal(sec[KEY] - rounded_mask(g[KEY], 0.1), want([0, 0, 1, 0]).view(1, 1, -1))
    # the per-text path gives the primary's row for a text whose set is the donors' (the self-merge takes the path; one text here)
    pt, _, p_pt = family_masks_per_text("self_union", g, {KEY: rho[KEY].view(1, 1, -1)}, background="r0", delta="excluded", own_round=0.0)
    assert torch.equal(pt[KEY], prim[KEY]) and p_pt
    # rounded at 0.1 the self-merge's set must hold c_1 (labelled 0.9): the donors' set of the example is not a self-merge's set, and is refused
    with pytest.raises(AssertionError, match="not the text's named set"):
        family_masks_per_text("self_union", g, {KEY: rho[KEY].view(1, 1, -1)}, background="r0", delta="excluded", own_round=0.1)
    self_set = _rho([True, False, True, False], dtype)[KEY].view(1, 1, -1)  # holds every piece labelled above 0.1
    s01, _, p01 = family_masks_per_text("self_union", g, {KEY: self_set}, background="r0", delta="excluded", own_round=0.1)
    assert torch.equal(s01[KEY], self_set) and torch.equal(s01[KEY], family_masks("rounded_own_g", g, {KEY: self_set.view(-1)}, background="r0", delta="excluded", tau=0.1)[0][KEY]) and not p01


def _random_g(seed: int, B: int = 3, T: int = 64, M: dict[str, int] | None = None) -> tuple[dict[str, torch.Tensor], dict[str, int]]:
    """Labels with exact zeros, labels in (0, 0.1], exactly 0.1, above 0.1, and exactly 1, as the real g has."""
    M = M or {"h.0.attn.q_proj": 7, "h.0.mlp.c_fc": 11, "h.1.mlp.c_proj": 5}
    rng = np.random.default_rng(seed)
    g = {}
    for k, c in M.items():
        u = rng.random((B, T, c))
        v = np.where(u < 0.5, 0.0, np.where(u < 0.7, rng.uniform(1e-6, 0.1, u.shape), np.where(u < 0.75, 0.1, np.where(u < 0.95, rng.uniform(0.1, 1.0, u.shape), 1.0))))
        g[k] = torch.from_numpy(v.astype(np.float32))
    return g, M


@pytest.mark.parametrize("seed", [0, 1])
def test_an_empty_donor_set_gives_the_rounded_references_bitwise(seed):
    """Identity M6e for both forms (smoke.py): with no donor, the primary's masks are the rounded_0 reference's and the secondary's the
    rounded_0.1 reference's, bitwise, as the loop builds those references."""
    g, M = _random_g(seed)
    empty = rho_tensors(np.zeros(sum(M.values()), dtype=bool), M, torch.float32, "cpu")
    prim, _, _ = family_masks(ROUNDED0_FAMILY, g, empty, background="r0", delta="excluded", tau=0.1)
    sec, _, _ = family_masks("rounded_own_g", g, empty, background="r0", delta="excluded", tau=0.1)
    r0, _ = build_condition_masks(CONDITION_BY_NAME["rounded_0"], g, M, draw=0, subbatch_index=0, master_seed=0)
    r01, _ = build_condition_masks(CONDITION_BY_NAME["rounded_0.1"], g, M, draw=0, subbatch_index=0, master_seed=0)
    for k in M:
        assert prim[k].dtype == r0[k].dtype and torch.equal(prim[k], r0[k]) and torch.equal(sec[k], r01[k])
    assert CONDITION_BY_NAME["rounded_0"].permitted and not CONDITION_BY_NAME["rounded_0.1"].permitted


@pytest.mark.parametrize("seed", [0, 1])
def test_the_self_merge_in_both_binary_forms_and_unchanged_without_the_field(seed):
    """The secondary self-merge is the text's named set at every position; the primary is max(1[g > 0], rho) and at or above g; without
    own_round the per-text path is tier 5's where(rho, 1, g), bitwise, and permitted."""
    g, M = _random_g(seed)
    B = next(iter(g.values())).shape[0]
    rng = np.random.default_rng(seed + 10)
    # the self-merge's set, as the loop asserts it on the device: every piece any position of the text labels above 0.1, per text
    rho = {k: (v > 0.1).any(dim=1, keepdim=True).to(torch.float32) for k, v in g.items()}
    assert all(r.shape == (B, 1, g[k].shape[-1]) for k, r in rho.items())
    sec, d_sec, p_sec = family_masks_per_text("self_union", g, rho, background="r0", delta="excluded", own_round=0.1)
    prim, d_prim, p_prim = family_masks_per_text("self_union", g, rho, background="r0", delta="excluded", own_round=0.0)
    old, d_old, p_old = family_masks_per_text("self_union", g, rho, background="r0", delta="excluded")
    for k in g:
        assert torch.equal(sec[k], rho[k].expand_as(g[k]))
        assert torch.equal(prim[k], torch.maximum(rounded_mask(g[k], 0.0), rho[k].expand_as(g[k]))) and bool((prim[k] >= g[k]).all())
        assert torch.equal(old[k], apply_binary_source_per_text(g[k], rho[k])) and torch.equal(old[k], torch.where(rho[k].bool(), 1, g[k]))
        # the per-text primary's row b is the batch-shared primary with text b's set
        b = int(rng.integers(0, B))
        shared, _, _ = family_masks(ROUNDED0_FAMILY, {k: g[k][b : b + 1]}, {k: rho[k][b, 0]}, background="r0", delta="excluded", tau=0.1)
        assert torch.equal(prim[k][b : b + 1], shared[k])
    assert (p_prim, p_sec, p_old) == (True, False, True) and d_sec is None and d_prim is None and d_old is None
    # a set missing one piece a position labels above 0.1 is refused when rounded at 0.1
    k0 = next(iter(g))
    hit = torch.nonzero(rho[k0][0, 0] > 0)
    bad = {k: v.clone() for k, v in rho.items()}
    bad[k0][0, 0, int(hit[0])] = 0.0
    with pytest.raises(AssertionError, match="not the text's named set"):
        family_masks_per_text("self_union", g, bad, background="r0", delta="excluded", own_round=0.1)
    with pytest.raises(AssertionError, match="own_round is defined"):
        family_masks_per_text("partner_union", g, rho, background="r0", delta="excluded", own_round=0.0)
    with pytest.raises(AssertionError, match="own_round is defined"):
        family_masks_per_text("self_union", g, rho, background="r0", delta="excluded", own_round=0.5)
    assert OWN_ROUND_VALUES == (0.0, 0.1)


def test_the_primary_is_marked_permitted_and_the_secondary_is_not():
    """The mask functions' flags (which switch on the loop's P3 assertion) and grid.cell_permitted (the manifest's and P3's labels) agree."""
    from vpd_audit.grid import cell_permitted

    t6 = {(c.family, c.control, c.own_round): c for c in tier_6_cells("main", 1)}
    assert cell_permitted(t6[(ROUNDED0_FAMILY, "none", None)]) and cell_permitted(t6[(ROUNDED0_FAMILY, "marginal", None)]) and cell_permitted(t6[("self_union", "none", 0.0)])
    assert not cell_permitted(t6[("rounded_own_g", "none", None)]) and not cell_permitted(t6[("self_union", "none", 0.1)])
    assert cell_permitted(Cell("main", "self_union", "E", "E", 0.1, "r0", "excluded", 0, "4", "none", 5))  # tier 5's self-merge, as it was
    assert not cell_permitted(Cell("main", "rounded_own_g", "E", "D_unif", 0.1, "r0", "excluded", 0, "2", "none", 3))  # tier 3's, as it was
    g, M = _random_g(3)
    rho = rho_tensors(np.random.default_rng(3).random(sum(M.values())) < 0.3, M, torch.float32, "cpu")
    assert family_masks(ROUNDED0_FAMILY, g, rho, background="r0", delta="excluded", tau=0.1)[2] is True
    assert family_masks("rounded_own_g", g, rho, background="r0", delta="excluded", tau=0.1)[2] is False
    with pytest.raises(AssertionError):
        family_masks(ROUNDED0_FAMILY, g, rho, background="uniform", delta="excluded", tau=0.1)  # the one configuration fixed in advance: background r0


# ----------------------------------------------------------------------------- the cells


@pytest.mark.parametrize("run", ["main", "simplestories"])
def test_tiers_1_to_5_are_what_they_are_on_main_with_tier_6_enumerated(run):
    every = enumerate_cells(runs=(run,), adaptive=AS_LAUNCHED, tier_4=True, code_leaning={run: MAIN_LADDER}, tier_5=True, tier_6=True)
    base = [c for c in every if c.tier != 6]
    assert every[: len(base)] == base and all(c.tier == 6 for c in every[len(base):])
    assert len(base) == ON_MAIN[run]["n"] and _sha(base) == ON_MAIN[run]["sha_1_to_5"]
    t5 = [c for c in base if c.tier == 5]
    assert len(t5) == ON_MAIN[run]["n_tier_5"] and _sha(t5) == ON_MAIN[run]["sha_5"]  # the tier-5 cells' names, the self-merge's among them
    assert all(c.own_round is None and "/ownround" not in c.name for c in base)
    assert [c for c in enumerate_cells(runs=(run,), adaptive=AS_LAUNCHED, tier_4=True, code_leaning={run: MAIN_LADDER}, tier_5=True)] == base  # tier_6 off: exactly as before


def test_tier_6_is_the_registered_table():
    every = enumerate_cells(runs=("main",), adaptive=AS_LAUNCHED, tier_4=True, code_leaning={"main": MAIN_LADDER}, tier_5=True, tier_6=True)
    t6 = [c for c in every if c.tier == 6]
    assert len(t6) == 58 and len({c.name for c in every}) == len(every)
    assert all(c.eval_set == "E" and c.tau == 0.1 and c.background == "r0" and c.delta == "excluded" and c.draw in range(8) and not c.descriptive and not c.optional and c.replicate == 0 for c in t6)
    prim = [c for c in t6 if c.family == ROUNDED0_FAMILY and c.control == "none"]
    ctl = [c for c in t6 if c.family == ROUNDED0_FAMILY and c.control == "marginal"]
    sec = [c for c in t6 if c.family == "rounded_own_g"]
    selfs = [c for c in t6 if c.family == "self_union"]
    assert {(c.draw, c.rung) for c in prim} == {(k, r) for k in range(8) for r in ("2", "2a", "3")} == {(c.draw, c.rung) for c in ctl} and len(prim) == len(ctl) == 24
    assert {(c.draw, c.rung) for c in sec} == {(k, "2a") for k in range(8)} and all(c.control == "none" for c in sec)
    assert [(c.own_round, c.donor_pool, c.rung, c.draw) for c in selfs] == [(0.0, "E", "4", 0), (0.1, "E", "4", 0)]
    assert all(c.donor_pool == "D_unif" for c in prim + ctl + sec)
    assert [c.name for c in selfs] == ["main/E/self_union/E/tau0.1/r0/excl/k0/r4/ownround0", "main/E/self_union/E/tau0.1/r0/excl/k0/r4/ownround0.1"]
    assert prim[0].name == "main/E/rounded0_own_g/D_unif/tau0.1/r0/excl/k0/r2" and ctl[-1].name == "main/E/rounded0_own_g/D_unif/tau0.1/r0/excl/k7/r3/ctl-marginal"
    # each form starts from its own rounded labels; tier 5's self-merge from the text's own labels, as before
    assert {reference_for(c) for c in prim + ctl} == {"rounded_0"} and {reference_for(c) for c in sec} == {"rounded_0.1"}
    assert [reference_for(c) for c in selfs] == ["rounded_0", "rounded_0.1"] and reference_for(dataclasses.replace(selfs[0], own_round=None, tier=5)) == "importances"
    # the subset: every tier-6 cell and the secondary form's tier-3 cells at rungs 2 and 3 (never the plain control, tau 0.5, or another residual), nothing else
    chosen = [c for c in every if C.LAUNCH_SUBSETS_S11["binary_union"](c)]
    t3 = [c for c in chosen if c.tier == 3]
    assert len(chosen) == 74 and len(t3) == 16 and all(c in every for c in t3)
    assert {(c.family, c.control, c.tau, c.delta, c.draw, c.rung) for c in t3} == {("rounded_own_g", "none", 0.1, "excluded", k, r) for k in range(8) for r in ("2", "3")}
    assert all(c.tier in (3, 6) for c in chosen) and {c.tier for c in chosen} == {3, 6}
    assert tier6.launch_cells("main") == chosen
    # the dictionaries: the new one sits beside LAUNCH_SUBSETS, which keeps its contents through tier 5; no earlier predicate takes a tier-6 cell
    assert set(C.SUBSETS_TIER_6) == {"binary_union"} and not set(C.SUBSETS_TIER_6) & set(C.LAUNCH_SUBSETS) and set(C.LAUNCH_SUBSETS_S11) == set(C.LAUNCH_SUBSETS) | set(C.SUBSETS_TIER_6)
    assert set(C.LAUNCH_SUBSETS) == set(C.ALL_SUBSETS) | set(C.SUBSETS_TIER_5)
    assert not any(pred(c) for pred in C.LAUNCH_SUBSETS.values() for c in t6)
    assert not any(C.SUBSETS_TIER_6["binary_union"](c) for c in every if c.tier in (1, 2, 4, 5))
    # no tier 6 on the control run; the counts
    assert not any(c.tier == 6 for c in enumerate_cells(runs=("control",), tier_6=True))
    assert C.tier_counts(every)["tier_6"]["cells"] == 58 and C.tier_counts(every)["tier_6"]["by_eval_set"]["E"] == 58 and "tier_6" not in C.tier_counts([c for c in every if c.tier != 6])


def test_own_round_round_trips_through_a_cell_table():
    """The cell table's own_round column: a float where set, NaN where not (a table joined from stores without it), rebuilt as the field."""
    from vpd_audit.two_paths import OPTIONAL_FIELDS, _cell_from_row

    assert OPTIONAL_FIELDS[-1] == "own_round"
    selfs = [c for c in tier_6_cells("main", 1) if c.family == "self_union"]
    old = Cell("main", "self_union", "E", "E", 0.1, "r0", "excluded", 0, "4", "none", 5)
    table = pd.DataFrame([{**asdict(c), "cell": c.name} for c in selfs + [old]])
    assert table["own_round"].dtype == np.float64 and np.isnan(table["own_round"].iloc[-1])
    back = [_cell_from_row(r) for _, r in table.iterrows()]
    assert back == selfs + [old] and back[0].own_round == 0.0 and isinstance(back[1].own_round, float) and back[2].own_round is None
    assert _cell_from_row(pd.Series({k: v for k, v in asdict(old).items() if k != "own_round"} | {"cell": old.name})) == old  # a store written before the column existed


# ----------------------------------------------------------------------------- the launch's sets against their committed twins


class _Committed:
    """A stand-in for tier5.CommittedTables: name -> source hash, and the store each is read from."""

    def __init__(self, sha: dict[str, str]):
        self.cells, self.roots = {n: {"source_sha256": h} for n, h in sha.items()}, ("planted",)
        self.where = {n: f"planted/{n.split('/')[2]}" for n in sha}

    def __contains__(self, name: str) -> bool:
        return name in self.cells

    def source_sha256(self, name: str) -> str:
        return self.cells[name]["source_sha256"]


def test_every_set_of_the_launch_is_held_to_its_committed_twin():
    from vpd_audit.tier5 import GateFailure

    cells = tier6.launch_cells("main", 2) + tier6.canary_cells("main") + tier6.reference_cells("main")
    h = lambda n: hashlib.sha256(n.encode()).hexdigest()  # noqa: E731
    committed = {}
    for k in range(2):
        for r in ("2", "2a", "3"):
            u = f"main/E/union/D_unif/tau0.1/r0/excl/k{k}/r{r}"
            committed[u], committed[u + "/ctl-marginal"] = h(u), h(u + "/ctl-marginal")
    committed["main/E/self_union/E/tau0.1/r0/excl/k0/r4"] = h("self")
    records = {}
    for c in cells:
        tw = tier6.twin_name(c)
        records[c.name] = {"source_sha256": committed.get(tw) if tw else None, "matched_source_sha256": committed[dataclasses.replace(c, family="union", control="none").name] if c.control == "marginal" else None}
    got = tier6.assert_sets_are_committed(cells, records, _Committed(committed), log=lambda *_: None)
    assert got["counts"] == {"binary_named_sets": 12, "look_alike_sets": 6, "look_alike_matched_sets": 6, "self_merge_sets": 2, "canary": 1}  # 2 draws: 6 primary, 2 secondary at 16 tokens, 4 secondary from tier 3
    assert tier6.twin_name(cells[0]).startswith("main/E/union/") and tier6.twin_name(tier6.reference_cells("main")[0]) is None
    # one set off, a twin missing, a control's matched set off: each stops the launch
    k = next(c.name for c in cells if c.family == ROUNDED0_FAMILY and c.control == "none")
    with pytest.raises(GateFailure, match="is not its committed twin"):
        tier6.assert_sets_are_committed(cells, {**records, k: {**records[k], "source_sha256": h("other")}}, _Committed(committed), log=lambda *_: None)
    with pytest.raises(GateFailure, match="in no committed store"):
        tier6.assert_sets_are_committed(cells, records, _Committed({n: v for n, v in committed.items() if "self_union" not in n}), log=lambda *_: None)
    m = next(c.name for c in cells if c.control == "marginal")
    with pytest.raises(GateFailure, match="matched set"):
        tier6.assert_sets_are_committed(cells, {**records, m: {**records[m], "matched_source_sha256": h("other")}}, _Committed(committed), log=lambda *_: None)


def test_the_store_carries_four_references_and_the_canary():
    from vpd_audit.grid import Group, add_store_references

    refs = tier6.reference_cells("main")
    assert [c.condition for c in refs] == ["unmasked", "rounded_0", "rounded_0.1", "importances"] and all(c.eval_set == "E" and c.tier == 1 for c in refs)
    assert [c.name for c in tier6.canary_cells("main")] == ["main/E/union/D_unif/tau0.1/r0/excl/k0/r2"] == [C.marginal_canaries("main")[0].name]
    g = Group("E__binary_union", "E", "E", np.zeros((1, 512), dtype=np.int64), "", list(tier6.launch_cells("main")))
    added = add_store_references([g], "main", 8, eval_sets=("E",), conditions=tier6.REFERENCE_CONDITIONS)
    assert added["E__binary_union"] == [c.name for c in refs]
    assert tier6.add_store_canary([g], "main") == {"E__binary_union": ["main/E/union/D_unif/tau0.1/r0/excl/k0/r2"]} and len(g.cells) == 74 + 4 + 1
    g2 = Group("E", "E", "E", np.zeros((1, 512), dtype=np.int64), "", [])
    assert len(add_store_references([g2], "main", 8)["E"]) == len(C._references("main", "E", 1))  # without conditions: the full set, as before
