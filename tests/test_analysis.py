"""The blindness gate (a store of the paper's model is refused without --frozen and with a
wrong hash, accepted with the current commit), the loader and the chains on the dry run, the control-absent path
("control not yet run"), and the tier restriction. The dry-run parts skip when results/dry_run/ is not present."""

from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from vpd_audit.analysis import analyze_descriptives, analyze_union_chains, build_chains, discover_stores, load_grid, restrict_tiers
from vpd_audit.cells import Cell
from vpd_audit.results import code_commits

ROOT = Path(__file__).resolve().parents[1]
DRY = ROOT / "results" / "dry_run"


def _paper_store(tmp_path: Path, run: str = "main") -> Path:
    d = tmp_path / "grid" / run / "tier1" / "E"
    (d / "kl").mkdir(parents=True)
    cells = [Cell(run, "reference", "E", None, None, "none", "excluded", 0, "0", "none", 1, condition="unmasked"), Cell(run, "union", "E", "D_unif", 0.1, "r0", "excluded", 0, "4", "none", 1)]
    rows = [{"cell": c.name, "seq": b, "kl_mean": 0.1, "ce": float("nan"), "mask_fp": "0" * 16, "sigma": 1.0} for c in cells for b in range(4)]
    pd.DataFrame(rows).to_parquet(d / "per_sequence.parquet", index=False)
    pd.DataFrame([{**asdict(c), "cell": c.name} for c in cells]).to_parquet(d / "cells.parquet", index=False)
    (d / "run_manifest.json").write_text(json.dumps({"run": run, "set_hash": "x"}))
    (d / "marker.json").write_text("{}")
    return tmp_path / "grid" / run


def test_blindness_gate_refuses_the_paper_model_without_the_frozen_commit(tmp_path):
    root = _paper_store(tmp_path)
    with pytest.raises(AssertionError, match="frozen"):
        load_grid(root, frozen=None)
    with pytest.raises(AssertionError, match="not the current commit"):
        load_grid(root, frozen="0000000")
    if code_commits()["dirty"] == "0":
        grid = load_grid(root, frozen=code_commits()["project"][:10])
        assert grid.run == "main" and "E" in grid.sets
    else:  # a dirty working tree is refused for the paper's runs even at the right commit
        with pytest.raises(AssertionError, match="clean"):
            load_grid(root, frozen=code_commits()["project"][:10])
    stand_in = _paper_store(tmp_path / "s", run="simplestories")
    assert load_grid(stand_in, frozen=None).run == "simplestories"


@pytest.fixture(scope="module")
def dry_grid():
    if not (DRY / "E" / "per_sequence.parquet").is_file():
        pytest.skip("results/dry_run is not present")
    return load_grid(DRY, frozen=None)


def test_loader_and_chains_on_the_dry_run(dry_grid):
    g = dry_grid
    assert g.run == "simplestories" and {"E", "E_lab"} <= set(g.sets) and len(discover_stores(DRY)) == 6
    chains = build_chains(g.sets["E"])
    c1 = next(ch for ch in chains.values() if ch.family == "union" and ch.background == "r0" and ch.tau == 0.1 and ch.control == "none" and ch.delta == "excluded")
    assert c1.rung_order() == ["1", "2", "3", "4", "5a", "5", "6a", "6", "7", "8"] and len(c1.rungs["1"]) == 2 and len(c1.rungs["8"]) == 1
    nn = next(ch for ch in chains.values() if ch.family == "never_named_hard" and ch.tau == 0.1 and ch.delta == "included")
    assert nn.rung_order() == ["1", "2", "3", "4", "5a", "5", "6a", "6", "7", "B50", "B75", "8"]
    donors = [k for k, sd in g.sets.items() if sd.eval_set == "donors"]
    assert len(donors) == 4 and all(len(build_chains(g.sets[k])) == 0 for k in donors)


def test_control_absent_prints_control_not_yet_run(dry_grid):
    g1 = restrict_tiers(dry_grid, (1,))
    assert not any(o.control != "none" for sd in g1.sets.values() for o in sd.cell_objects.values())
    assert any(o.family == "reference" for o in g1.sets["E"].cell_objects.values())
    chains = build_chains(g1.sets["E"])
    res = analyze_union_chains(g1, chains, {}, 200, 0, {})
    c1 = res["union/E/D_unif/tau0.1/r0/excl/ctl-none"]["result"]
    assert c1["paired_vs_control"] == "control not yet run" and c1["label"] in ("fails", "holds at the scale tested", "detected but immaterial")
    d = analyze_descriptives(g1, res, {}, {"E": chains}, None, {}, 200, 0)
    assert d["deciles"]["union/E/D_unif/tau0.1/r0/excl/ctl-none"]["bins"] == "control not yet run"
    # with the controls present the paired differences and the bins exist
    chains_all = build_chains(dry_grid.sets["E"])
    res_all = analyze_union_chains(dry_grid, chains_all, {}, 200, 0, {})
    pv = res_all["union/E/D_unif/tau0.1/r0/excl/ctl-none"]["result"]["paired_vs_control"]
    assert isinstance(pv, dict) and set(pv) == {"1", "2", "3", "4", "5a"} and all("interval" in v for v in pv.values())


def test_shared_resample_reaches_every_chain(dry_grid):
    from vpd_audit.analysis import _resample_for

    cache: dict = {}
    a = _resample_for(dry_grid, "E", None, 50, 0, cache)
    b = _resample_for(dry_grid, "E", None, 50, 0, cache)
    assert a is b and a.W.shape == (50, dry_grid.sets["E"].n_sequences)
    mask = np.zeros(dry_grid.sets["E_lab"].n_sequences, bool)
    mask[:10] = True
    c = _resample_for(dry_grid, "E_lab", mask, 50, 0, cache)
    assert c.n == 10 and c.W.shape == (50, 10)


def test_compare_with_the_same_run_gives_zero_differences(dry_grid, tmp_path):
    """The stand-in compared with its own stores, paired per sequence and draw with the shared resample, gives zero
    differences with [0, 0] intervals at every shared rung of every curve and in every populated mass-matched bin; and a
    rung one run alone has is listed, never compared."""
    from vpd_audit.analysis import analyze

    b = analyze(DRY, tmp_path / "b", frozen=None, pre_reads_dir=DRY / "pre_reads", verify_dir=None, replicates=200, compare_with=DRY, compare_pre_reads_dir=DRY / "pre_reads", log=lambda *_: None)
    assert b["comparison"] and all(b["comparison"].values())
    text = (tmp_path / "b" / "report.md").read_text()
    assert "## 8. This run against the simplestories run's stores" in text and "hashes asserted equal" in text
    for name in ("compare_curve_1.csv", "compare_curve_2_draw_0.csv", "compare_curve_3.csv", "compare_curve_4.csv"):
        df = pd.read_csv(tmp_path / "b" / name, dtype={"rung": str})
        assert len(df) > 0, name
        assert np.all(df["paired_difference"].to_numpy() == 0.0) and (df["interval"] == "[+0.0000, +0.0000]").all(), name
        assert np.array_equal(df["excess_this"].to_numpy(), df["excess_other"].to_numpy())
        if "d_hat_this" in df.columns:
            assert np.array_equal(df["d_hat_this"].to_numpy(), df["d_hat_other"].to_numpy(), equal_nan=True)
    for name in ("compare_mass_matched_curve_1.csv", "compare_mass_matched_curve_2_draw_0.csv"):
        df = pd.read_csv(tmp_path / "b" / name)
        pop = df[df["populated"]]
        if name.endswith("curve_1.csv"):
            assert len(pop) > 0, name  # curve 2's sigma spreads within a rung under the uniform background, so on the 64-sequence stand-in no bin holds 64 sequences
        if len(pop):
            assert np.all(pop["difference"].to_numpy() == 0.0) and (pop["interval"] == "[+0.0000, +0.0000]").all(), name
    assert "rungs only in this run none, only in the other none" in text


def test_compare_with_lists_rungs_one_run_alone_has(dry_grid, tmp_path):
    """A run without 5a and 6a (the control's rule did not fire) against one with them: the shared rungs are compared, the
    others listed."""
    import shutil

    from vpd_audit.analysis import analyze

    other = tmp_path / "other"
    shutil.copytree(DRY / "E", other / "E")
    ct = pd.read_parquet(other / "E" / "cells.parquet")
    keep = ~ct["rung"].isin(["5a", "6a"])
    ct[keep].to_parquet(other / "E" / "cells.parquet", index=False)
    rows = pd.read_parquet(other / "E" / "per_sequence.parquet")
    rows[rows["cell"].isin(set(ct[keep]["cell"]))].to_parquet(other / "E" / "per_sequence.parquet", index=False)
    b = analyze(DRY, tmp_path / "b", frozen=None, pre_reads_dir=None, verify_dir=None, replicates=100, compare_with=other, compare_pre_reads_dir=None, log=lambda *_: None)
    df = pd.read_csv(tmp_path / "b" / "compare_curve_1.csv", dtype={"rung": str})
    assert "5a" not in set(df["rung"]) and "5" in set(df["rung"]) and np.all(df["paired_difference"].to_numpy() == 0.0)
    assert "rungs only in this run ['5a', '6a'], only in the other none" in (tmp_path / "b" / "report.md").read_text()


def test_excess_matrix_pairs_on_the_sequence(tmp_path):
    """Per-sequence tables with rung 0 at a spread of 0.15 and paired noise of 0.05 through
    excess_matrix on a synthetic SetData give a half-width near 0.0015 at eight draws; an unpaired treatment of the same
    tables (the difference of two independent means) would give about 0.0018 times 10."""
    from vpd_audit.analysis import SetData, excess_matrix
    from vpd_audit.cells import Cell
    from vpd_audit.reference import CONDITION_BY_NAME
    from vpd_audit import stats as st

    rng = np.random.default_rng(4)
    N, K = 1024, 8
    k0 = rng.normal(0.34, 0.15, size=N)
    ref = Cell("main", "reference", "E", None, None, "none", "excluded", 0, "0", "none", 1, condition="importances")
    cells = [Cell("main", "union", "E", "D_unif", 0.1, "r0", "excluded", k, "4", "none", 1) for k in range(K)]
    rows = [{"cell": ref.name, "seq": b, "kl_mean": np.float32(k0[b]), "sigma": np.nan} for b in range(N)]
    for c in cells:
        for b in range(N):
            rows.append({"cell": c.name, "seq": b, "kl_mean": np.float32(k0[b] + rng.normal(0.0, 0.05)), "sigma": 1.0})
    df = pd.DataFrame(rows)
    ct = pd.DataFrame([{**asdict(c), "cell": c.name, "n_on": 100} for c in [ref] + cells]).set_index("cell")
    sd = SetData("E", N, "h", df, ct, {c.name: c for c in [ref] + cells}, [])
    e = excess_matrix(sd, cells)
    assert e.shape == (K, N)
    rs = st.Resample.make(N, 2000, (0, "boot", "E"))
    res = st.union_rung(e, rs, 10)
    assert 0.0008 < res["half_width"] < 0.0025, res["half_width"]
    unpaired_hw = 2.8 * np.sqrt(2) * 0.158 / np.sqrt(N)  # two independent means of spread 0.158 over 1,024 sequences
    assert unpaired_hw > 8 * res["half_width"]


def test_descriptive_rungs_are_filtered_before_the_frozen_rules(tmp_path):
    """Cells flagged descriptive (rungs 2a, 2b) never enter a chain that reaches stats.py, so
    compared_rungs over the chain's rungs excludes them and m stays what the pre-registered rungs give; they are read
    through build_chains(descriptive=True) instead; and a store written before the flag existed loads with it False."""
    from vpd_audit import stats as st
    from vpd_audit.analysis import SetData
    from vpd_audit.two_paths import _cell_from_row

    run = "simplestories"
    cells = [Cell(run, "union", "E", "D_unif", 0.1, "r0", "excluded", k, r, "none", 1) for k in range(2) for r in ("1", "2", "3", "4")]
    cells += [Cell(run, "union", "E", "D_unif", 0.1, "r0", "excluded", k, r, "none", 3, descriptive=True) for k in range(2) for r in ("2a", "2b")]
    cells += [Cell(run, "union", "E", "D_unif", 0.1, "r0", "excluded", 0, "8", "none", 1), Cell(run, "reference", "E", None, None, "none", "excluded", 0, "0", "none", 1, condition="importances")]
    ct = pd.DataFrame([{**asdict(c), "cell": c.name} for c in cells])
    objects = {r["cell"]: _cell_from_row(r) for _, r in ct.iterrows()}
    assert sum(o.descriptive for o in objects.values()) == 4 and all(o.level is None and o.rank_key is None for o in objects.values())
    sd = SetData("E", 4, "x", pd.DataFrame(), ct.set_index("cell"), objects, [])
    chains = build_chains(sd)
    assert len(chains) == 1
    ch = next(iter(chains.values()))
    assert set(ch.rungs) == {"1", "2", "3", "4", "8"} and st.compared_rungs(list(ch.rungs), "union") == ["1", "2", "3", "4", "8"] and st.correction_count(list(ch.rungs), "union") == 5
    desc = build_chains(sd, descriptive=True)
    assert len(desc) == 1 and set(next(iter(desc.values())).rungs) == {"2a", "2b"} and st.sort_rungs(["2b", "2a"]) == ["2a", "2b"]
    # a row without the level, descriptive and rank columns (a store written before them) loads with the defaults
    old = ct.drop(columns=["level", "descriptive", "rank_key", "rank_end"]).iloc[0]
    c0 = _cell_from_row(old)
    assert c0.descriptive is False and c0.level is None and c0.rank_key is None and c0.rank_end is None and c0.name == cells[0].name


def test_level_cells_and_ranked_pair_are_loaded_and_chained_but_reach_no_rule(dry_grid):
    """The dry run's level cells and ranked pair load with their fields, the ranked pair forms four
    chains whose labels carry the key and end (the pre-reads' chain keys), and neither family reaches the hard-zero rule;
    the descriptive rungs 2a and 2b form their own chain outside the verdict chains."""
    from vpd_audit.analysis import DESCRIPTIVE_FAMILIES, analyze_hard_zero_chains

    sd = dry_grid.sets["E"]
    lv = [o for o in sd.cell_objects.values() if o.family == "level"]
    rk = [o for o in sd.cell_objects.values() if o.family == "never_named_ranked"]
    assert len(lv) == 6 and sorted(o.level for o in lv) == [0.25, 0.25, 0.5, 0.5, 0.75, 0.75] and len(rk) == 36 and all(o.rank_key and o.rank_end for o in rk)
    chains = build_chains(sd)
    ranked = [c for c in chains.values() if c.family == "never_named_ranked"]
    assert len(ranked) == 4 and sorted(c.label for c in ranked) == sorted(f"never_named_ranked/E/D_unif/tau0.1/ones/incl/ctl-none/{k}-{e}" for k in ("weight_norm", "positive_count") for e in ("top", "bottom"))
    assert all(len(c.rungs) == 9 for c in ranked) and len([c for c in chains.values() if c.family == "level"]) == 2
    hz = analyze_hard_zero_chains(dry_grid, chains, {}, None, {}, 50, 0)
    assert not any(e["chain"].family in DESCRIPTIVE_FAMILIES for e in hz.values()) and any(e["chain"].family == "never_named_hard" for e in hz.values())
    desc = build_chains(sd, descriptive=True)
    assert {c.family for c in desc.values()} == {"union"} and all(set(c.rungs) == {"2a", "2b"} for c in desc.values()) and not any(c.rung in ("2a", "2b") for ch in chains.values() for cs in ch.rungs.values() for c in cs)


def test_descriptive_rungs_crossing_and_per_label_control_split(dry_grid):
    """On the dry run, the descriptive rungs 2a and 2b are read beside curve 1 with uncorrected
    intervals and m untouched, the paired union-minus-control line gains them, the crossing of X is a bracket or a stated
    note (never a single number), and with fabricated reader labels the per-label paired union-minus-control table exists
    at rungs 1 to 4 and 5a with the control's per-label excess beside it, each label with its own resample."""
    from vpd_audit import stats as st
    from vpd_audit.analysis import analyze_union_chains, preconditions

    sd = dry_grid.sets["E"]
    chains = build_chains(sd)
    desc = build_chains(sd, descriptive=True)
    n = sd.n_sequences
    parity = np.arange(n) % 2 == 0
    labels = {"E_reader": {"labels": ["code" if p else "prose" for p in parity], "groups": {"code": parity, "prose": ~parity}}}
    res = analyze_union_chains(dry_grid, chains, {}, 100, 0, labels, descriptive=desc)
    c1 = res["union/E/D_unif/tau0.1/r0/excl/ctl-none"]["result"]
    assert set(c1["descriptive_rungs"]) == {"2a", "2b"} and "2a" not in c1["per_rung"] and c1["m"] == st.correction_count(list(c1["per_rung"]), "union")
    d2a = c1["descriptive_rungs"]["2a"]
    assert d2a["n_draws"] == 2 and len(d2a["n_on_per_draw"]) == 2 and d2a["interval"][0] <= d2a["e_hat"] <= d2a["interval"][1] and c1["descriptive_rungs"]["2a"]["n_on"] < c1["descriptive_rungs"]["2b"]["n_on"]
    pv = c1["paired_vs_control"]
    assert {"2a", "2b"} <= set(pv) and list(pv) == st.sort_rungs(list(pv)) and all("interval" in v for v in pv.values())
    xc = c1["x_crossing"]
    assert xc["position_rungs"] == ["1", "2", "2a", "2b", "3"] and ("bracket" in xc) and len(xc["per_draw"]) == 2
    if xc["bracket"]:
        assert xc["n_low"] <= xc["interpolated_n"] <= xc["n_high"] and xc["e_low"] < st.X_MATERIAL <= xc["e_high"]
    else:
        assert xc["note"]
    by = c1["paired_vs_control_by_reader_label"]
    assert set(by) == {"code", "prose"} and set(by["code"]) == {"1", "2", "3", "4", "5a"}
    v = by["code"]["4"]
    assert v["n"] == int(parity.sum()) and "control_excess" in v and v["control_interval"][0] <= v["control_excess"] <= v["control_interval"][1] and v["interval"][0] <= v["mean"] <= v["interval"][1]
    # the per-label control excess is that label's own resample: the two labels do not share intervals
    assert by["code"]["4"]["control_excess"] != by["prose"]["4"]["control_excess"]
    # P4 over the descriptive chains too, and the P5 dict now says it applies
    hz = {}
    pre = preconditions(dry_grid, {k: build_chains(v) for k, v in dry_grid.sets.items()}, hz, {}, descriptive_chains={k: build_chains(v, descriptive=True) for k, v in dry_grid.sets.items()})
    assert pre["P4"]["n_descriptive"] == 2 and pre["P4"]["n_pass_descriptive"] == 2 and all(" (descriptive rungs)" in x["chain"] for x in pre["P4"]["descriptive_chains"])


def test_cells_joined_across_old_and_new_stores_keep_their_defaults():
    """The loader takes its defaults from dataclasses.fields(Cell): a row missing every optional column, or NaN in every
    optional column (a table joined from stores written before and after the columns existed; bool(nan) is True), loads
    with the defaults; a NaN in a field without a default raises; donor_pool and tau are None on a reference cell."""
    from vpd_audit.two_paths import CELL_FIELDS, OPTIONAL_FIELDS, _cell_from_row

    # "replicate": the tier-4 Cell field (default 0); the one edit tier 4 made to this test.
    # "shift", "arm", "model": the tier-5 fields (defaults 0, None, None); the one edit tier 5 made to it.
    # "own_round": the tier-6 field for the binary self-merge (default None); the one edit tier 6 made to it.
    assert OPTIONAL_FIELDS == ("condition", "optional", "donor_side_reference", "level", "descriptive", "rank_key", "rank_end", "replicate", "shift", "arm", "model", "own_round") and CELL_FIELDS[:4] == ("run", "family", "eval_set", "donor_pool")
    old = Cell("main", "union", "E", "D_unif", 0.1, "r0", "excluded", 0, "4", "none", 1)
    new = Cell("main", "union", "E", "D_unif", 0.1, "r0", "excluded", 0, "2a", "none", 3, descriptive=True)
    lvl = Cell("main", "level", "E", "D_unif", 0.1, "r0", "excluded", 0, "8", "none", 3, level=0.25)
    ref = Cell("main", "reference", "E", None, None, "none", "excluded", 0, "0", "none", 1, condition="unmasked")
    row_missing = pd.Series({k: v for k, v in asdict(old).items() if k not in OPTIONAL_FIELDS} | {"cell": old.name})
    assert _cell_from_row(row_missing) == old
    joined = pd.concat([pd.DataFrame([{k: v for k, v in asdict(old).items() if k not in OPTIONAL_FIELDS} | {"cell": old.name}]), pd.DataFrame([{**asdict(c), "cell": c.name} for c in (new, lvl, ref)])], ignore_index=True)
    assert all(joined[f].isna().iloc[0] for f in OPTIONAL_FIELDS) and bool(joined["descriptive"].iloc[0]) is True  # the trap
    objs = [_cell_from_row(r) for _, r in joined.iterrows()]
    assert objs[0] == old and objs[1] == new and objs[2] == lvl and objs[3] == ref and objs[3].donor_pool is None and objs[3].tau is None
    assert objs[0].descriptive is False and objs[0].level is None and objs[0].rank_key is None and objs[0].optional is False and objs[0].condition is None
    bad = pd.Series({**asdict(old), "cell": old.name, "rung": float("nan")})
    with pytest.raises(AssertionError, match="'rung' is NaN"):
        _cell_from_row(bad)
    with pytest.raises(AssertionError, match="'background' is missing"):
        _cell_from_row(pd.Series({k: v for k, v in asdict(old).items() if k != "background"}))


def test_chain_completeness_counts_every_cell_once_and_catches_a_drop(dry_grid):
    """Every non-reference, non-donor-side cell of every store lands in exactly one chain set;
    a chain set with a cell dropped, or a cell counted twice, is refused."""
    from vpd_audit.analysis import assert_chain_completeness

    chains = {k: build_chains(v) for k, v in dry_grid.sets.items()}
    desc = {k: build_chains(v, descriptive=True) for k, v in dry_grid.sets.items()}
    out = assert_chain_completeness(dry_grid, chains, desc)
    sd = dry_grid.sets["E"]
    eligible = [c for c in sd.cell_objects.values() if c.family != "reference" and c.donor_side_reference is None]
    assert out["E"]["n_cells"] == len(eligible) and out["E"]["descriptive_rung"] == 8 and out["E"]["descriptive_family"] == 42 and out["E"]["rule"] == len(eligible) - 50
    assert all(out[k]["n_cells"] == 0 for k in out if k.startswith("donors"))
    dropped = {k: dict(v) for k, v in chains.items()}
    key = next(iter(dropped["E"]))
    del dropped["E"][key]
    with pytest.raises(AssertionError, match="missing"):
        assert_chain_completeness(dry_grid, dropped, desc)
    twice = {k: dict(v) for k, v in desc.items()}
    twice["E"] = {**twice["E"], **{("dup",) + k: v for k, v in twice["E"].items()}}
    with pytest.raises(AssertionError, match="more than once"):
        assert_chain_completeness(dry_grid, chains, twice)
