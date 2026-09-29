"""The tier-5 cells, and the test that the enumeration of tiers 1 to 4 is what it was before tier 5 existed.

The fixture tests/data/cells_tier_4_on_main.json was taken from `enumerate_cells` before tier 5 existed: adding a tier must change
no existing cell name. Per configuration: the tier-4 cells' count, first and last names, the SHA-256 of their "tier|name" lines in
enumeration order, and the same hash over tiers 1 to 4 together. tests/test_tier4_cells.py holds tiers 1 to 3 the same way."""

import hashlib
import json
from pathlib import Path

import pytest

from vpd_audit.cells import enumerate_cells

FIXTURE_T4 = json.loads((Path(__file__).resolve().parent / "data" / "cells_tier_4_on_main.json").read_text())


def _kwargs(raw):
    kw = {}
    for k, v in raw.items():
        if k == "adaptive":
            kw[k] = {(key.split("|")[0], float(key.split("|")[1])): tuple(r) for key, r in v.items()}
        elif k == "code_leaning":
            kw[k] = {run: [(int(a), bool(b)) for a, b in ladder] for run, ladder in v.items()}
        elif isinstance(v, list):
            kw[k] = tuple(v)
        else:
            kw[k] = v
    return kw


def _sha(cells):
    return hashlib.sha256("\n".join(f"{c.tier}|{c.name}" for c in cells).encode()).hexdigest()


@pytest.mark.parametrize("tier_5", [False, True])
@pytest.mark.parametrize("config", sorted(FIXTURE_T4["configs"]))
def test_the_names_order_and_count_of_the_cells_of_tiers_1_to_4_are_what_they_are_on_main(config, tier_5):
    """With and without tier 5 enumerated: tier 5 follows last and moves nothing."""
    want = FIXTURE_T4["configs"][config]
    every = enumerate_cells(**_kwargs(want["kwargs"]), **({"tier_5": True} if tier_5 else {}))
    cells = [c for c in every if c.tier in (1, 2, 3, 4)]
    assert every[: len(cells)] == cells and all(c.tier == 5 for c in every[len(cells):]) and (len(every) > len(cells)) == tier_5
    t4 = [c for c in cells if c.tier == 4]
    assert len(t4) == want["n_cells_tier_4"] and len(cells) == want["n_cells_tiers_1_to_4"]
    assert {str(t): sum(1 for c in cells if c.tier == t) for t in (1, 2, 3, 4)} == want["per_tier"]
    assert (t4[0].name if t4 else None) == want["first_tier_4"] and (t4[-1].name if t4 else None) == want["last_tier_4"]
    assert _sha(t4) == want["sha256_of_tier_4_lines"] and _sha(cells) == want["sha256_of_tiers_1_to_4_lines"]


FIXTURE_T3 = json.loads((Path(__file__).resolve().parent / "data" / "cells_tiers_1_to_3_on_main.json").read_text())


@pytest.mark.parametrize("config", sorted(FIXTURE_T3["configs"]))
def test_tiers_1_to_3_are_what_they_are_on_main_with_tier_5_enumerated(config):
    """The tiers 1 to 3 fixture (tests/test_tier4_cells.py holds it without tier 5), now with tiers 4 and 5 enumerated after it."""
    want = FIXTURE_T3["configs"][config]
    kw = {k: v for k, v in _kwargs(want["kwargs"]).items()}
    cells = [c for c in enumerate_cells(**kw, tier_4=True, tier_5=True) if c.tier in (1, 2, 3)]
    assert len(cells) == want["n_cells"] and cells[0].name == want["first"] and cells[-1].name == want["last"]
    assert _sha(cells) == want["sha256_of_tier_and_name_lines"]


# ----------------------------------------------------------------------------- the tier-5 cells themselves

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

from vpd_audit import cells as C  # noqa: E402
from vpd_audit.cells import Cell, reference_for, tier_5_cells, tier_counts  # noqa: E402

MAIN_LADDER = [(16, False), (64, False), (256, False), (1007, False), (1862, True)]
AS_LAUNCHED = {("D_code", 0.1): ("5a", "6a"), ("D_unif", 0.1): ("5a", "6a")}
ROOT = Path(__file__).resolve().parent.parent


def _main_cells():
    return enumerate_cells(runs=("main",), adaptive=AS_LAUNCHED, tier_4=True, code_leaning={"main": MAIN_LADDER}, tier_5=True)


def test_tier_5_is_the_registered_table_and_changes_no_existing_name():
    cells = _main_cells()
    base = [c for c in cells if c.tier != 5]
    t5 = [c for c in cells if c.tier == 5]
    assert all(c.shift == 0 and c.arm is None and c.model is None for c in base) and not any("/arm-" in c.name or "/shift" in c.name or "/external/" in c.name for c in base)
    # three arms on E_lab over the ten sizes (m = 10, the pool once), none descriptive, no adaptive rung; controls for C and U at the six smallest sizes
    same = [c for c in t5 if C.SUBSETS_TIER_5["same_domain"](c)]
    assert len(same) == 3 * (9 * 8 + 1) + 2 * 6 * 8 == 315
    assert all(c.family == "union" and c.eval_set == "E_lab" and c.tau == 0.1 and c.background == "r0" and c.delta == "excluded" and not c.descriptive and not c.optional for c in same)
    for pool, has_control in (("D_code", True), ("D_unif", True), ("D_prose", False)):
        real = [c for c in same if c.donor_pool == pool and c.control == "none"]
        ctl = [c for c in same if c.donor_pool == pool and c.control == "plain"]
        assert sorted({c.rung for c in real}, key=C.rung_order) == ["1", "2", "2a", "2b", "3", "4", "5", "6", "7", "8"] and len(real) == 73
        assert [c.draw for c in real if c.rung == "8"] == [0] and all({c.draw for c in real if c.rung == r} == set(range(8)) for r in C.SAME_DOMAIN_RUNGS)
        assert (len(ctl) == 48 and {c.rung for c in ctl} == {"1", "2", "2a", "2b", "3", "4"}) if has_control else not ctl
    assert not any(c.rung in ("5a", "6a") for c in t5)
    from vpd_audit.s9_pre_reads import MERGE_POOLS, MERGE_RUNGS

    assert C.SAME_DOMAIN_RUNGS + ("8",) == MERGE_RUNGS and {p for _, p, _ in C.SAME_DOMAIN_ARMS} == set(MERGE_POOLS)  # the sets the label-only merge_sets.csv holds
    assert same[0].name == "main/E_lab/union/D_code/tau0.1/r0/excl/k0/r1" and [reference_for(c) for c in same[:1]] == ["importances"]
    # the self-merge on three sets; the partner merges, four shifts in three arms
    per_text = [c for c in t5 if C.SUBSETS_TIER_5["self_merge"](c)]
    selfs, partners = [c for c in per_text if c.family == "self_union"], [c for c in per_text if c.family == "partner_union"]
    assert [(c.eval_set, c.donor_pool) for c in selfs] == [("E", "E"), ("E_lab", "E_lab"), ("D_unif", "D_unif")] and len(partners) == 12 and len(per_text) == 15
    assert {(c.eval_set, c.arm, c.donor_pool) for c in partners} == {("E", "within", "E"), ("E_lab", "source", "E_lab"), ("E_lab", "general", "D_unif")}
    assert all({c.shift for c in partners if c.arm == a} == {1, 2, 3, 4} for a in ("within", "source", "general"))
    assert all(c.rung == "4" and c.background == "r0" and c.delta == "excluded" and c.tau == 0.1 and reference_for(c) == "importances" and not c.is_hard_zero for c in per_text)
    assert selfs[0].name == "main/E/self_union/E/tau0.1/r0/excl/k0/r4" and partners[-1].name == "main/E_lab/partner_union/D_unif/tau0.1/r0/excl/k0/r4/arm-general/shift4"
    from vpd_audit import tier5

    assert C.PARTNER_ARMS == tier5.PARTNER_ARMS and C.PARTNER_SHIFTS == tier5.PARTNER_SHIFTS
    # two comparison models on E and on E_lab, the paper's model only
    ext = [c for c in t5 if C.SUBSETS_TIER_5["plain_terms"](c)]
    assert [c.name for c in ext] == ["main/E/external/pythia-70m", "main/E/external/pythia-160m", "main/E_lab/external/pythia-70m", "main/E_lab/external/pythia-160m"]
    from vpd_audit.external_models import MODELS, PRIMARY

    assert tuple(MODELS) == C.EXTERNAL_MODEL_KEYS and PRIMARY == C.EXTERNAL_MODEL_KEYS[0]
    assert len(same) + len(per_text) + len(ext) == len(t5) == 334 and len({c.name for c in cells}) == len(cells)
    assert not any(c.family == "external" for c in tier_5_cells("simplestories", 2)) and not any(c.tier == 5 for c in enumerate_cells(runs=("control",), tier_5=True))
    counts = tier_counts(cells)
    assert counts["tier_5"]["cells"] == 334 and counts["tier_5"]["by_eval_set"] == {"E": 7, "E_lab": 326, "donors": 0, "D_unif": 1} and "tier_5" not in tier_counts(base)
    assert "D_unif" not in tier_counts(base)["tier_4"]["by_eval_set"]  # the earlier tiers' counts are what they were
    # the launch subsets sit beside ALL_SUBSETS, which tests/test_tier4_cells.py holds to SUBSETS and SUBSETS_TIER_4
    assert set(C.SUBSETS_TIER_5) == {"same_domain", "self_merge", "plain_terms"} and not set(C.SUBSETS_TIER_5) & set(C.ALL_SUBSETS) and set(C.LAUNCH_SUBSETS) == set(C.ALL_SUBSETS) | set(C.SUBSETS_TIER_5)
    assert not any(pred(c) for pred in C.SUBSETS_TIER_5.values() for c in base) and not any(pred(c) for pred in C.ALL_SUBSETS.values() for c in t5)


def test_the_plain_terms_re_runs_are_the_registered_list_under_their_committed_names():
    cells = _main_cells()
    reruns = C.plain_terms_reruns(cells, 1007)
    by = {}
    for c in reruns:
        by.setdefault((c.family, c.control), []).append(c)
    curve1 = by[("union", "none")]
    assert sorted({c.rung for c in curve1}, key=C.rung_order) == ["1", "2", "2a", "2b", "3", "4", "8"] and len(curve1) == 6 * 8 + 1 and [c.draw for c in curve1 if c.rung == "8"] == [0]
    assert {c.rung for c in by[("union", "plain")]} == {"3", "4"} and len(by[("union", "plain")]) == 16
    assert {(c.rung, c.background) for c in by[("soft_erase", "none")]} == {("4", "r1")} and {c.draw for c in by[("soft_erase", "none")]} == set(range(8))
    assert [c.name for c in by[("never_named_hard", "none")]] == ["main/E/never_named_hard/D_unif/tau0.1/ones/incl/k0/r8"]
    assert [c.name for c in by[("code_leaning_hard", "none")]] == [f"main/E_lab/code_leaning_hard/D_code/tau0.1/ones/incl/k0/rG{n}" for n in (64, 256, 1007)]
    assert len(reruns) == 77 and all(c.tier in (1, 2, 3, 4) for c in reruns) and {c.eval_set for c in reruns} == {"E", "E_lab"}
    # the stand-in's chain has its group at 94 members: 64 and the group, and no 256 (descriptive there)
    ss = enumerate_cells(runs=("simplestories",), draws=2, tier_4=True, code_leaning={"simplestories": [(16, False), (64, False), (94, False), (256, True), (456, True)]}, tier_5=True)
    assert [c.rung for c in C.plain_terms_reruns(ss, 94) if c.family == "code_leaning_hard"] == ["G64", "G94"]
    # every re-run cell is a cell of a committed store of the paper's model, under the same name and tier
    committed = pd.concat([pd.read_parquet(p, columns=["cell", "tier"]) for p in sorted((ROOT / "results" / "grid" / "main").glob("tier*/*/cells.parquet"))])
    tiers = dict(zip(committed["cell"], committed["tier"]))
    assert all(c.name in tiers and int(tiers[c.name]) == c.tier for c in reruns)


def test_the_per_position_list_is_the_registered_one():
    cells = _main_cells()
    reruns = C.plain_terms_reruns(cells, 1007)
    listed = [c for c in cells if C.per_position_listed(c, 1007)]
    refs = [c for c in listed if c.family == "reference"]
    assert {(c.eval_set, c.condition) for c in refs} == {(s, r) for s in ("E", "E_lab") for r in ("unmasked", "unmasked_delta", "importances")}
    assert set(reruns) <= set(listed) and [c.name for c in listed if c.family == "self_union"] == ["main/E/self_union/E/tau0.1/r0/excl/k0/r4"] and sum(c.family == "external" for c in listed) == 4
    arms = [c for c in listed if c.tier == 5 and c.family == "union"]
    assert {(c.donor_pool, c.rung, c.control) for c in arms} == {(p, r, "none") for p in ("D_code", "D_unif") for r in ("3", "4")} and len(arms) == 2 * 2 * 8
    assert len(listed) == 6 + 77 + 1 + 4 + 32 and not any(c.family == "partner_union" for c in listed)
    assert not C.per_position_listed(Cell("main", "reference", "D_unif", None, None, "none", "excluded", 0, "0", "none", 1, condition="importances"))


def test_a_store_written_before_the_tier_5_fields_loads_with_their_defaults():
    from dataclasses import asdict

    from vpd_audit.two_paths import _cell_from_row

    c = Cell("main", "union", "E", "D_unif", 0.1, "r0", "excluded", 3, "2", "plain", 2)
    row = {**asdict(c), "cell": c.name}
    for k in ("shift", "arm", "model"):
        row.pop(k)
    assert _cell_from_row(pd.Series(row)) == c
    p = Cell("main", "partner_union", "E_lab", "D_unif", 0.1, "r0", "excluded", 0, "4", "none", 5, shift=3, arm="general")
    back = _cell_from_row(pd.Series({**asdict(p), "cell": p.name, "shift": np.float64(3.0)}))  # a table joined with stores that lack the column reads it as a float
    assert back == p and type(back.shift) is int and back.name.endswith("/arm-general/shift3")
    x = Cell("main", "external", "E", None, None, "none", "none", 0, "0", "none", 5, model="pythia-70m")
    assert _cell_from_row(pd.Series({**asdict(x), "cell": x.name})) == x and x.e_equivalent == 1.0
