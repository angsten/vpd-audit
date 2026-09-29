"""The glue of analysis_s7.py. On the committed stand-in stores with its tier-4 dry run joined
(results/dry_run and results/dry_run_s7; skipped when absent): tier 4 never reaches the earlier pipeline of analysis.py, whose
tables come out byte for byte; the canaries; the assertions against the label-only pre-read. On a fabricated grid: the
code-leaning chain's glue with a planted R1. On the stand-in with fabricated reader labels: the readings split by reader label."""

from __future__ import annotations

import filecmp
import json
import shutil
from dataclasses import asdict
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from vpd_audit import analysis_s7
from vpd_audit import stats as st
from vpd_audit.analysis import Grid, SetData, analyze, load_grid
from vpd_audit.cells import Cell

ROOT = Path(__file__).resolve().parents[1]
DRY, DRY_S7 = ROOT / "results" / "dry_run", ROOT / "results" / "dry_run_s7"
needs_stand_in = pytest.mark.skipif(not ((DRY / "E" / "per_sequence.parquet").is_file() and (DRY_S7 / "tier4" / "E__marginal" / "per_sequence.parquet").is_file() and (DRY / "pre_reads" / "s7" / "summary.json").is_file()),
                                    reason="the stand-in's stores, its tier-4 dry run, or its tier-4 label-only pre-read are not present")


@pytest.fixture(scope="module")
def two_runs(tmp_path_factory):
    base, with_t4 = tmp_path_factory.mktemp("base"), tmp_path_factory.mktemp("t4")
    a = analyze(DRY, base, frozen=None, pre_reads_dir=DRY / "pre_reads", replicates=300, log=lambda *_: None)
    b = analyze(DRY, with_t4, frozen=None, pre_reads_dir=DRY / "pre_reads", replicates=300, log=lambda *_: None, extra_roots=(DRY_S7,))
    return base, a, with_t4, b


@needs_stand_in
def test_tier_4_never_reaches_the_earlier_pipeline_every_table_it_wrote_is_byte_identical(two_runs):
    base, a, with_t4, b = two_runs
    old, new = {p.name for p in base.iterdir()}, {p.name for p in with_t4.iterdir()}
    assert old <= new
    differ = sorted(f for f in old if not filecmp.cmp(base / f, with_t4 / f, shallow=False))
    assert differ == ["report.md", "summary.json"], differ  # the stores' list and the new section; every CSV and every figure's data as before
    assert {k: v for k, v in a.items() if k not in ("seconds", "report", "figures", "s7")} == {k: v for k, v in b.items() if k not in ("seconds", "report", "figures", "s7")}
    added = sorted(new - old)
    assert all(f.startswith(("s7_", "fig7_", "fig8_")) for f in added) and {"s7_marginal_closure.csv", "s7_marginal_readings.csv", "s7_code_leaning_damage.csv", "s7_code_leaning_positive_control.csv", "fig7_marginal_control.png",
                                                                          "fig8_code_leaning.png"} <= set(added)
    # without a tier-4 store the new section says so and the old summary gains one key
    assert a["s7"]["tier_4_present"] is False and a["s7"]["marginal"] is None and a["s7"]["code_leaning"] is None
    text = (base / "report.md").read_text()
    assert "## 9. Tier 4" in text and "no marginal cell in these stores" in text and "no code-leaning cell in these stores" in text


@needs_stand_in
def test_the_stand_ins_tier_4_is_read_under_the_rules_with_the_decisive_rungs_from_the_committed_table(two_runs):
    _, _, out, b = two_runs
    s = b["s7"]
    table = pd.read_csv(DRY / "pre_reads" / "s7" / "marginal_overlap_by_rung.csv", dtype={"rung": str})
    o = {r: v for r, v in zip(table[(table.control == "marginal") & (table.replicate == 0)].rung, table[(table.control == "marginal") & (table.replicate == 0)].overlap_mass_pooled)}
    want = [r for r in ("1", "2", "2a", "2b", "3") if o[r] <= 1 / 3]
    assert s["tier_4_present"] and s["marginal"]["union_r0"]["decisive"] == want and s["marginal"]["union_r0"]["m"] == len(want)
    assert s["marginal"]["union_uniform"]["decisive"] == [r for r in want if r in ("1", "2", "3")] and s["marginal"]["soft_erase_r1"]["decisive"] == [r for r in want if r in ("1", "2")]
    assert all(v["reading"] in ("A", "B", "C", "D", "no reading", analysis_s7.NO_READING_GUARD) for v in s["marginal"].values())
    closure = pd.read_csv(out / "s7_marginal_closure.csv", dtype={"rung": str})
    assert set(closure.family) == {"union_r0", "union_uniform", "soft_erase_r1"} and closure[closure.family == "union_r0"].rung.tolist() == ["1", "2", "2a", "2b", "3"]
    dec = closure[closure.decisive]
    assert (dec.m == dec.groupby("family").rung.transform("count")).all() and (closure[~closure.decisive].m == 1).all()
    row = closure[(closure.family == "soft_erase_r1") & (closure.rung == "1")].iloc[0]
    assert abs(row.o_marginal - o["1"]) < 1e-15 and abs(row.phi_ov - (row.o_marginal - row.o_plain) / (1 - row.o_plain)) < 1e-12 and abs(float(row.phi) - (row.M - row.P) / (row.U - row.P)) < 1e-12
    assert abs(float(row.psi) - (float(row.phi) - row.phi_ov) / (1 - row.phi_ov)) < 1e-12 and row.rung_reading in ("A", "B", "C", "D")
    per_draw = pd.read_csv(out / "s7_marginal_per_draw.csv", dtype={"rung": str})
    g = per_draw[(per_draw.family == "soft_erase_r1") & (per_draw.rung == "1")]
    assert len(g) == 2 and abs(g.U.mean() - row.U) < 1e-12 and abs(g.M.mean() - row.M) < 1e-12
    # on the stand-in itself: its primary family's named-minus-plain gap is below zero at its decisive rung, so the guard is caught there,
    # the family has no reading, its numbers are still in the table, and the other two families and the code-leaning chain are read all the same
    prim = closure[closure.family == "union_r0"]
    assert s["marginal"]["union_r0"]["reading"] == analysis_s7.NO_READING_GUARD and s["marginal"]["union_r0"]["guard_fired_at"] == ["1"] and s["headline_reading"] == analysis_s7.NO_READING_GUARD
    assert s["marginal"]["union_uniform"]["reading"] in ("A", "B", "C", "D") and s["marginal"]["soft_erase_r1"]["reading"] in ("A", "B", "C", "D") and s["code_leaning"] is not None
    r1 = prim[prim.rung == "1"].iloc[0]
    assert r1.U < r1.P and bool(r1.U_minus_P_below_zero) and r1.phi == "undefined" and r1.psi == "undefined" and r1.rung_reading == "no reading (the guard)" and pd.isna(r1.condition_D)
    assert all(x.startswith("[") for x in (r1.U_interval, r1.P_interval, r1.M_interval, r1.U_minus_P_interval, r1.M_minus_P_interval, r1.U_minus_M_interval)) and pd.notna(r1.replicate_1_M)
    # the code-leaning chain: the forced group's rungs, the chain's own positive control judged at the rungs read of at least 64 members
    cl = s["code_leaning"]
    pc = pd.read_csv(out / "s7_code_leaning_positive_control.csv")
    assert cl["rungs_read"] == [r for r, d in zip(pc.rung, pc.descriptive) if not d] and pc.judged.tolist() == [bool((not d) and n >= 64) for n, d in zip(pc.n_members, pc.descriptive)]
    assert cl["positive_control"] in (True, False) and (cl["reading"].startswith("not read") if cl["positive_control"] is False else True)
    text = (out / "report.md").read_text()
    assert "2 of 2 equal" in text and "judged at the rungs the rule reads" in text and "results/dry_run/pre_reads/s7/marginal_overlap_by_rung.csv" in text
    assert "`union_r0` (primary): no reading: the named-minus-plain gap is not positive at a decisive rung" in text and "The headline takes no reading; it does not pass to the secondary family." in text


@needs_stand_in
def test_the_loader_takes_the_canaries_bitwise_and_nothing_else_twice(tmp_path):
    grid = load_grid(DRY, frozen=None, extra_roots=(DRY_S7,))
    can = grid.reference_assert["E"]["canaries"]
    assert can["n_canaries"] == 2 and all(c["pass"] and c["against"] == "E" and c["store"] == "dry_run_s7/tier4/E__marginal" for c in can["checks"]) and "canaries" not in grid.reference_assert["E_lab"]
    assert grid.sets["E"].cells.index.is_unique and sum(o.tier == 4 for o in grid.sets["E"].cell_objects.values()) == 26
    # a canary that differs from its first run stops the load
    bad = tmp_path / "bad"
    shutil.copytree(DRY_S7 / "tier4" / "E__marginal", bad / "tier4" / "E__marginal")
    rows = pd.read_parquet(bad / "tier4" / "E__marginal" / "per_sequence.parquet")
    i = rows.index[rows.cell == "simplestories/E/union/D_unif/tau0.1/r0/excl/k0/r2"][0]
    rows.loc[i, "kl_mean"] = np.float32(rows.loc[i, "kl_mean"]) + np.float32(1e-3)
    rows.to_parquet(bad / "tier4" / "E__marginal" / "per_sequence.parquet", index=False)
    with pytest.raises(AssertionError, match="a canary differs"):
        load_grid(DRY, frozen=None, extra_roots=(bad,))
    # any other cell present in two stores is refused, as before
    twice = tmp_path / "twice"
    shutil.copytree(DRY / "E", twice / "E")
    with pytest.raises(AssertionError, match="only the canaries"):
        load_grid(DRY, frozen=None, extra_roots=(twice,), only_sets=("E",))


@needs_stand_in
def test_a_marginal_set_that_is_not_the_pre_reads_stops_the_analysis(tmp_path):
    bad = tmp_path / "bad"
    shutil.copytree(DRY_S7 / "tier4" / "E__marginal", bad / "tier4" / "E__marginal")
    ct = pd.read_parquet(bad / "tier4" / "E__marginal" / "cells.parquet")
    i = ct.index[ct.cell == "simplestories/E/union/D_unif/tau0.1/r0/excl/k1/r2/ctl-marginal"][0]
    ct.loc[i, "source_sha256"] = "0" * 64
    ct.to_parquet(bad / "tier4" / "E__marginal" / "cells.parquet", index=False)
    grid = load_grid(DRY, frozen=None, extra_roots=(bad,), only_sets=("E",))
    with pytest.raises(AssertionError, match="is not the label-only pre-read's"):
        analysis_s7.analyze_marginal(grid, DRY / "pre_reads" / "s7", {}, {}, 100, 0, log=lambda *_: None)


@needs_stand_in
def test_a_label_holding_every_text_reproduces_the_whole_set_reading():
    from vpd_audit.analysis import analyze_hard_zero_chains, build_chains, load_strata

    grid = load_grid(DRY, frozen=None, only_sets=("E",))
    n = grid.sets["E"].n_sequences
    labels = {"E_reader": {"labels": ["all"] * n, "groups": {"everything": np.ones(n, bool), "first_half": np.arange(n) < n // 2}}}
    out = analysis_s7.code_specific_on_E_by_reader_label(grid, labels, {}, 300, 0)
    assert list(out) == ["code_specific_hard/E/D_code/tau0.1/ones/incl/ctl-none"]
    df = pd.DataFrame(out["code_specific_hard/E/D_code/tau0.1/ones/incl/ctl-none"])
    whole = analyze_hard_zero_chains(grid, build_chains(grid.sets["E"]), load_strata(grid), None, {}, 300, 0)["code_specific_hard/E/D_code/tau0.1/ones/incl/ctl-none"]
    for part in ("donor_chain", "sub_rung_chain"):
        for tq in ("0.1", "0"):
            res = whole["by_tau_q"][tq]["all"][part]
            sub = df[(df.reader_label == "everything") & (df.part == part) & (df.tau_q == tq)].set_index("rung")
            assert list(sub.index) == res["rungs"] and (sub.m == res["m"]).all()
            for r in res["rungs"]:
                pr = res["per_rung"][r]
                assert bool(sub.loc[r, "testable"]) == pr["testable"] and sub.loc[r, "mean_n_contributing"] == pr["readability"]["mean_n_contributing"]
                assert (np.isnan(sub.loc[r, "d_hat"]) and pr["result"] is None) or sub.loc[r, "d_hat"] == pr["result"]["d_hat"]
                assert abs(sub.loc[r, "unconditional"] - whole["unconditional"]["all"][r]) < 1e-12
    half = df[df.reader_label == "first_half"]
    assert (half.n_texts == n // 2).all() and len(half) == len(df) // 2
    assert analysis_s7.code_specific_on_E_by_reader_label(grid, {}, {}, 300, 0) is None  # no reader labels (the stand-in): not available


# ----------------------------------------------------------------------------- the code-leaning glue on a fabricated grid with a planted R1

N_TEXTS, T = 256, 512
RUN = "simplestories"
LADDER = [(16, False), (64, False), (256, False), (512, True)]


def _fabricated(tmp_path, *, github_damage, other_damage, control_github, control_other):
    rng = np.random.default_rng(12)
    gh = np.arange(N_TEXTS) < N_TEXTS // 2
    ref = Cell(RUN, "reference", "E_lab", None, None, "none", "included", 0, "0", "none", 1, condition="unmasked_delta")
    cells, rows, ctab, chain_rows, ctl_rows, test_rows = [ref], [], [{"cell": ref.name, "source_sha256": None, "n_on": 0, "mask_fp_cell": "ref"}], [], [], []
    rows.append(pd.DataFrame({"cell": ref.name, "seq": np.arange(N_TEXTS), "kl_mean": 0.0, "sigma": np.nan, "omega": np.nan, "d_0.1": np.nan, "d_0": np.nan, "t_star_0.1": -1, "t_star_0": -1}))
    for size, desc in LADDER:
        for control, draws in (("none", [0]), ("usage", list(range(8)))):
            for k in draws:
                c = Cell(RUN, "code_leaning_hard", "E_lab", "D_code", 0.1, "ones", "included", k, f"G{size}", control, 4, descriptive=desc)
                cells.append(c)
                level_gh, level_ot = (github_damage[size], other_damage[size]) if control == "none" else (control_github[size], control_other[size])
                kl = np.where(gh, level_gh, level_ot) * (1 + 0.05 * rng.standard_normal(N_TEXTS))
                # clean prefixes: GitHub texts are touched at once; other texts are clean throughout at the small rungs and halfway at the large ones
                t_star = np.where(gh, 0, T if size <= 64 else T // 2).astype(np.int64)
                d = np.where(t_star > 0, 0.004 * (1 + 0.05 * rng.standard_normal(N_TEXTS)), np.nan)
                rows.append(pd.DataFrame({"cell": c.name, "seq": np.arange(N_TEXTS), "kl_mean": kl, "sigma": float(size), "omega": 0.01 * size * (1 + 0.1 * rng.random(N_TEXTS)), "d_0.1": d, "d_0": d,
                                          "t_star_0.1": t_star, "t_star_0": t_star}))
                h = f"{size}-{control}-{k}"
                ctab.append({"cell": c.name, "source_sha256": h, "n_on": size, "mask_fp_cell": h})
                (chain_rows if control == "none" else ctl_rows).append({"rung_size": size, "draw": k, "source_sha256": h})
        for who in ("group", "control"):
            for stratum, mask in (("Github", gh), ("other", ~gh)):
                for tq in ("tau_q0.1", "tau_q0"):
                    t = np.where(mask, np.where(gh, 0, T if size <= 64 else T // 2), -1)[mask]
                    read = st.readability(t[None, :])
                    test_rows.append({"chain": who, "rung_size": size, "tau_q": tq, "stratum": stratum, "floor_met": read["floor_met"], "mean_n_contributing": read["mean_n_contributing"]})
    all_rows = pd.concat(rows, ignore_index=True)
    sd = SetData("E_lab", N_TEXTS, "h", all_rows, pd.DataFrame(ctab).set_index("cell"), {c.name: c for c in cells}, [])
    grid = Grid(run=RUN, root=tmp_path, sets={"E_lab": sd}, stores=[], reference_assert={})
    s7_dir = tmp_path / "s7"
    s7_dir.mkdir()
    pd.DataFrame(chain_rows).to_csv(s7_dir / "code_leaning_chain.csv", index=False)
    pd.DataFrame(ctl_rows).to_csv(s7_dir / "code_leaning_control_per_draw.csv", index=False)
    pd.DataFrame(test_rows).to_csv(s7_dir / "code_leaning_testability.csv", index=False)
    (s7_dir / "summary.json").write_text(json.dumps({"code_leaning": {"existence": {"verdict": "clear"}, "thresholds": {"group": 0.9, "wide": 0.75}, "chain": {"control_gate": {"pass": True}}}}))
    arxiv = np.arange(N_TEXTS) >= 3 * N_TEXTS // 4
    strata = {"E_lab": {"labels": ["Github"] * (N_TEXTS // 2) + ["Pile-CC"] * (N_TEXTS // 4) + ["ArXiv"] * (N_TEXTS // 4), "positive": "Github",
                        "groups": {"all": np.ones(N_TEXTS, bool), "Github": gh, "other": ~gh, "ArXiv": arxiv, "Pile-CC": ~gh & ~arxiv}}}
    return grid, s7_dir, strata, gh


def test_the_code_leaning_glue_reads_a_planted_r1_and_refuses_a_chain_whose_control_fails(tmp_path):
    sizes = [16, 64, 256, 512]
    gh_dmg, ot_dmg = dict(zip(sizes, (0.01, 0.10, 0.90, 2.0))), dict(zip(sizes, (0.001, 0.01, 0.02, 0.30)))
    c_gh, c_ot = dict(zip(sizes, (0.005, 0.03, 0.20, 0.9))), dict(zip(sizes, (0.001, 0.008, 0.015, 0.25)))
    grid, s7_dir, strata, gh = _fabricated(tmp_path, github_damage=gh_dmg, other_damage=ot_dmg, control_github=c_gh, control_other=c_ot)
    out = analysis_s7.analyze_code_leaning(grid, s7_dir, strata, {}, 500, 0, log=lambda *_: None)
    assert out["rungs"] == ["G16", "G64", "G256", "G512"] and out["rungs_read"] == ["G16", "G64", "G256"] and out["m"] == 3 and out["n_control_draws"] == 8 and out["positive_stratum"] == "Github"
    assert out["positive_control"]["pass"] is True and out["positive_control"]["rungs_judged"] == ["G64", "G256"]
    v = out["per_rung"]["G256"]
    assert abs(v["D_github"]["mean"] - 0.90) < 0.02 and abs(v["D_other"]["mean"] - 0.02) < 0.002 and abs(v["D_github_control"] - 0.20) < 0.01 and v["level_m"] == 3 and out["per_rung"]["G512"]["level_m"] == 1
    assert v["D_github"]["interval"][0] < v["D_github"]["mean"] < v["D_github"]["interval"][1] and abs(v["D_github_ratio_to_control"] - 4.5) < 0.3
    assert abs(v["localization"]["statistic"] - ((0.90 - 0.20) - (0.02 - 0.015))) < 0.02 and v["localization"]["interval"][0] > 0
    # the strata are the right texts: on other the rung is testable (half of every text is a clean prefix) and the conditional damage holds; on GitHub nothing is clean
    co, cg = v["conditional_other"]["group|0.1"], v["conditional_github"]["group|0.1"]
    assert co["testable"] and co["label"] == "holds" and abs(co["d_hat"] - 0.004) < 5e-4 and co["readability"]["mean_n_contributing"] == 128 and not cg["testable"] and cg["label"] is None
    assert v["conditional_other"]["control|0.1"]["readability"]["per_draw_n_contributing"] == [128] * 8
    # the touched surplus on other: the excess minus the clean half's share of it
    ts = v["touched_other"]["group|0.1"]
    assert abs(ts["surplus"]["mean"] - (0.02 - 0.5 * 0.004)) < 0.002 and abs(ts["surplus_per_over_removal"]["ratio"] - ts["surplus"]["mean"] / ts["over_removal"]) < 1e-12
    assert abs(out["per_rung"]["G16"]["touched_other"]["group|0.1"]["surplus"]["mean"] - (0.001 - 0.004)) < 5e-4  # never touched: the whole text is its clean prefix
    rd = out["readings"]
    assert rd["read"] and rd["label"] == "R1 at G256 (tau_q 0.1: conditional claim tested and holds, tau_q 0: conditional claim tested and holds)" and rd["R1_rungs"] == ["G256"] and rd["R4"] is False
    assert out["budget_other"]["0.1"]["budget_rung"] == "G256"
    # the damage on each source of other, the group and its control, per rung, uncorrected
    src = pd.DataFrame(out["by_source"])
    assert set(src.source) == {"ArXiv", "Pile-CC"} and len(src) == 2 * 4 * 2 and set(src.n_texts) == {64} and set(src[src["set"] == "control"].n_draws) == {8}
    g = src[(src.rung == "G256") & (src["set"] == "group")]
    assert abs(g.D.mean() - v["D_other"]["mean"]) < 1e-12 and all(lo < d < hi for d, (lo, hi) in zip(g.D, g.interval_95))  # the two sources, equal in size, average to "other"
    lines = analysis_s7.write_s7(tmp_path, {"tier_4_present": True, "marginal": None, "code_leaning": out, "code_specific_by_reader_label": None, "canaries": {}})
    text = "\n".join(lines)
    assert "conditional claim tested and holds" in text and "shows no code-specific effect at these sizes" in text and "*Unread*" not in text
    assert len(pd.read_csv(tmp_path / "s7_code_leaning_damage_by_source.csv")) == 16
    # a control as damaging as the erase on GitHub at a judged rung: the chain is not read, its numbers still reported
    grid2, s7_dir2, strata2, _ = _fabricated(tmp_path / "b", github_damage=gh_dmg, other_damage=ot_dmg, control_github={**c_gh, 64: 0.10}, control_other=c_ot) if (tmp_path / "b").mkdir() is None else (None,) * 4
    out2 = analysis_s7.analyze_code_leaning(grid2, s7_dir2, strata2, {}, 500, 0, log=lambda *_: None)
    assert out2["positive_control"]["pass"] is False and out2["positive_control"]["failing_rungs"] == ["G64"] and out2["readings"]["label"].startswith("not read") and out2["readings"]["R1"] is None
    assert out2["readings"]["conditions_unread"] and out2["readings"]["conditions_computed"]["R1_rungs"] == ["G256"]
    (tmp_path / "unread").mkdir()
    text2 = "\n".join(analysis_s7.write_s7(tmp_path / "unread", {"tier_4_present": True, "marginal": None, "code_leaning": out2, "code_specific_by_reader_label": None, "canaries": {}}))
    assert "*Unread*" in text2 and "R1 at G256" in text2 and "Reading: not read" in text2  # printed, flagged unread
    rr = pd.read_csv(tmp_path / "unread" / "s7_code_leaning_readings.csv").iloc[0]
    assert bool(rr.conditions_unread) and rr.computed_R1_rungs == "G256" and pd.isna(rr.R1)
    # a rung that is not the pre-read's stops the analysis; so does a floor that is not the pre-read's
    t = pd.read_csv(s7_dir / "code_leaning_chain.csv")
    t.loc[t.rung_size == 64, "source_sha256"] = "something else"
    t.to_csv(s7_dir / "code_leaning_chain.csv", index=False)
    with pytest.raises(AssertionError, match="not the rung the pre-read judged"):
        analysis_s7.analyze_code_leaning(grid, s7_dir, strata, {}, 100, 0, log=lambda *_: None)
    tt = pd.read_csv(s7_dir2 / "code_leaning_testability.csv")
    tt.loc[(tt.chain == "group") & (tt.rung_size == 256) & (tt.stratum == "other"), "floor_met"] = False
    tt.to_csv(s7_dir2 / "code_leaning_testability.csv", index=False)
    with pytest.raises(AssertionError, match="readability floor"):
        analysis_s7.analyze_code_leaning(grid2, s7_dir2, strata2, {}, 100, 0, log=lambda *_: None)


@needs_stand_in
def test_the_marginal_families_split_by_reader_label_reports_the_differences_and_never_raises(tmp_path):
    grid = load_grid(DRY, frozen=None, extra_roots=(DRY_S7,), only_sets=("E",))
    n = grid.sets["E"].n_sequences
    rng = np.random.default_rng(5)
    lab = rng.choice(["code", "prose", "mixed", "other"], size=n)
    labels = {"E_reader": {"labels": lab.tolist(), "groups": {"everything": np.ones(n, bool), **{x: lab == x for x in sorted(set(lab))}}}}
    out = analysis_s7.analyze_marginal(grid, DRY / "pre_reads" / "s7", labels, {}, 300, 0, log=lambda *_: None)
    fam = out["families"]["union_r0"]
    split = fam["by_reader_label"]
    assert set(split) == {"everything", "code", "prose", "mixed", "other"} and sum(split[x]["n"] for x in ("code", "prose", "mixed", "other")) == n
    for r in fam["rungs"]:
        whole, every = fam["result"]["per_rung"][r], split["everything"]["per_rung"][r]
        assert abs(every["M_minus_P"]["mean"] - whole["M_minus_P"]["mean"]) < 1e-12 and abs(every["U_minus_M"]["mean"] - whole["U_minus_M"]["mean"]) < 1e-12 and every["m"] == whole["m"]
        for x in ("code", "prose", "mixed", "other"):
            v = split[x]["per_rung"][r]
            assert np.isfinite(v["M_minus_P"]["interval"]).all() and np.isfinite(v["U_minus_M"]["interval"]).all() and "conditions" not in v
            assert (v["psi"] is None) == v["undefined"]  # in a split the ratio is withheld only where its denominator's interval includes zero; one below zero is flagged
    lines = analysis_s7.write_s7(tmp_path, {"tier_4_present": True, "marginal": out, "code_leaning": None, "code_specific_by_reader_label": None, "canaries": {}})
    t = pd.read_csv(tmp_path / "s7_marginal_by_reader_label.csv", dtype={"rung": str})
    assert len(t) == 5 * (5 + 3 + 3) and set(t.reader_label) == set(split) and any("By reader label" in x for x in lines)
    assert ((t.psi == "undefined") == t.undefined).all()


def test_the_decisive_rungs_come_from_the_committed_table_through_the_glue(tmp_path):
    """A fabricated overlap table on disk, read as the analysis reads the committed one, with a rung at 0.34 out."""
    from vpd_audit import stats_s7 as s7

    rows = [{"control": "marginal", "family": "all", "replicate": 0, "rung": r, "overlap_mass_pooled": o} for r, o in (("1", 0.09), ("2", 0.2851), ("2a", 0.34), ("2b", 1.0 / 3.0), ("3", 0.73))]
    rows += [{"control": "marginal", "family": "all", "replicate": 1, "rung": r, "overlap_mass_pooled": o} for r, o in (("1", 0.5), ("2", 0.6))]  # replicate 1 never decides
    rows += [{"control": "plain", "family": f, "replicate": 0, "rung": r, "overlap_mass_pooled": 0.1} for f in ("union", "soft_erase") for r in ("1", "2", "3")]
    pd.DataFrame(rows).to_csv(tmp_path / "marginal_overlap_by_rung.csv", index=False)
    c = analysis_s7.load_overlap_constants(tmp_path)
    assert s7.decisive_rungs(c["marginal"][0], ["1", "2", "2a", "2b", "3"]) == ["1", "2", "2b"] and s7.decisive_rungs(c["marginal"][0], ["1", "2", "3"]) == ["1", "2"]
    assert c["marginal"][1] == {"1": 0.5, "2": 0.6} and set(c["plain"]) == {"union", "soft_erase"} and c["plain"]["union"]["2"] == 0.1
    from vpd_audit.pre_reads import decisive_rungs

    assert decisive_rungs(pd.DataFrame(rows).astype({"rung": str})) == ["1", "2", "2b"]  # the pre-read's report of the rule is the same function


# ----------------------------------------------------------------------------- the marginal glue on a fabricated grid: a read primary family with its replicate, and the guard caught per family

N_E, K_E = 256, 8
O_M0, O_M1, O_PL = {"1": 0.09, "2": 0.28, "2a": 0.43, "2b": 0.59, "3": 0.73}, {"1": 0.10, "2": 0.27}, {"1": 0.03, "2": 0.15, "2a": 0.25, "2b": 0.39, "3": 0.54}
FAM = {"union_r0": ("union", "r0", ("1", "2", "2a", "2b", "3")), "union_uniform": ("union", "uniform", ("1", "2", "3")), "soft_erase_r1": ("soft_erase", "r1", ("1", "2", "3"))}


def _fabricated_marginal(tmp_path, levels, psi, *, psi_replicate_1=None):
    """An in-memory E set with U, P, M planted per family: `levels[family] = (U, P)`, M = P + phi (U - P) with phi from the
    planted psi and the overlap constants; a text effect the three curves share; small per-draw noise. And the label-only
    tables the glue is held to."""
    rng = np.random.default_rng(21)
    text = rng.normal(0, 0.01, size=N_E)
    cells, rows, ctab, comp, tier = [], [], [], [], {"none": 1, "plain": 2, "marginal": 4}

    def add(c, level, h):
        cells.append(c)
        rows.append(pd.DataFrame({"cell": c.name, "seq": np.arange(N_E), "kl_mean": level + text + rng.normal(0, 0.002, size=N_E), "sigma": float(len(cells))}))
        ctab.append({"cell": c.name, "source_sha256": h, "n_on": 100, "mask_fp_cell": h + c.family + c.background})

    for ref in ["importances", "unmasked"] + [f"stochastic/k{k}" for k in range(K_E)]:
        name = f"{RUN}/E/ref/{ref}"
        rows.append(pd.DataFrame({"cell": name, "seq": np.arange(N_E), "kl_mean": 0.0, "sigma": np.nan}))
        ctab.append({"cell": name, "source_sha256": None, "n_on": 0, "mask_fp_cell": "ref-" + ref})
    for key, (family, background, rungs) in FAM.items():
        U, P = levels[key]
        for r in rungs:
            phi_ov = (O_M0[r] - O_PL[r]) / (1 - O_PL[r])
            for k in range(K_E):
                for control, level in (("none", U), ("plain", P), ("marginal", P + (phi_ov + psi[key] * (1 - phi_ov)) * (U - P))):
                    c = Cell(RUN, family, "E", "D_unif", 0.1, background, "excluded", k, r, control, tier[control])
                    h = f"{control}-{r}-{k}" + ("" if control != "plain" else f"-{family}")  # the marginal sets are the same in every family; the plain control's seed carries it
                    add(c, level, h)
                    if key == "union_r0" and control != "marginal":
                        comp.append({"control": "union" if control == "none" else "plain", "family": "union", "replicate": 0, "rung": r, "draw": str(k), "cell": c.name, "source_sha256": h, "n": 100, "mean_usage": 0.1, "p90_usage": 0.3,
                                     "mean_norm": 1.5, "p90_norm": 3.0})
                    if key == "union_r0" and control == "marginal":
                        comp.append({"control": "marginal", "family": "all", "replicate": 0, "rung": r, "draw": str(k), "cell": "", "source_sha256": h, "n": 100, "mean_usage": 0.09, "p90_usage": 0.2, "mean_norm": 1.45, "p90_norm": 2.9})
                if key == "union_r0" and r in ("1", "2"):
                    ov1 = (O_M1[r] - O_PL[r]) / (1 - O_PL[r])
                    p1 = psi["union_r0"] if psi_replicate_1 is None else psi_replicate_1
                    add(Cell(RUN, family, "E", "D_unif", 0.1, background, "excluded", k, r, "marginal", 4, replicate=1), P + (ov1 + p1 * (1 - ov1)) * (U - P), f"marginal-{r}-{k}-rep1")
                    comp.append({"control": "marginal", "family": "all", "replicate": 1, "rung": r, "draw": str(k), "cell": "", "source_sha256": f"marginal-{r}-{k}-rep1", "n": 100, "mean_usage": 0.09, "p90_usage": 0.2, "mean_norm": 1.45,
                                 "p90_norm": 2.9})
    for control in ("union", "marginal"):
        comp.append({"control": control, "family": "union" if control == "union" else "all", "replicate": 0, "rung": "1", "draw": "pooled", "cell": "", "source_sha256": "", "n": 800, "mean_usage": 0.1 if control == "union" else 0.09,
                     "p90_usage": 0.3, "mean_norm": 1.5 if control == "union" else 1.45, "p90_norm": 3.0})
    sd = SetData("E", N_E, "h", pd.concat(rows, ignore_index=True), pd.DataFrame(ctab).set_index("cell"), {c.name: c for c in cells}, [])
    grid = Grid(run=RUN, root=tmp_path, sets={"E": sd}, stores=[], reference_assert={})
    s7_dir = tmp_path / "s7"
    s7_dir.mkdir(parents=True)
    ov = [{"control": "marginal", "family": "all", "replicate": rep, "rung": r, "overlap_mass_pooled": o} for rep, d in ((0, O_M0), (1, O_M1)) for r, o in d.items()]
    ov += [{"control": "plain", "family": f, "replicate": 0, "rung": r, "overlap_mass_pooled": O_PL[r]} for f, rr in (("union", O_PL), ("soft_erase", ("1", "2", "3"))) for r in rr]
    pd.DataFrame(ov).to_csv(s7_dir / "marginal_overlap_by_rung.csv", index=False)
    pd.DataFrame(comp).to_csv(s7_dir / "marginal_composition.csv", index=False)
    (s7_dir / "summary.json").write_text(json.dumps({"marginal": {"real_position_sets": None}}))
    return grid, s7_dir


def test_the_marginal_glue_reads_planted_families_and_catches_the_guard_per_family(tmp_path):
    """The primary family planted at psi = 0.1 with a second replicate reads A; the soft erase planted at 0.9 reads
    B; the secondary family planted with U below P at its decisive rungs has its guard caught: no reading, its numbers still
    reported, the other two read as they would have been."""
    levels = {"union_r0": (0.040, -0.011), "union_uniform": (-0.020, 0.010), "soft_erase_r1": (0.436, 0.070)}
    grid, s7_dir = _fabricated_marginal(tmp_path, levels, {"union_r0": 0.1, "union_uniform": 0.5, "soft_erase_r1": 0.9})
    out = analysis_s7.analyze_marginal(grid, s7_dir, {}, {}, 500, 0, log=lambda *_: None)
    fam = out["families"]
    assert out["sets_assert"] == {"n_marginal_cells": 8 * (5 + 2 + 3 + 3), "n_union_and_plain_cells": 80, "table": out["sets_assert"]["table"], "pass": True}
    prim = fam["union_r0"]["result"]
    assert prim["decisive"] == ["1", "2"] and prim["m"] == 2 and prim["reading"] == "A" and "guard" not in prim  # decisive by the rule from the table on disk: 0.09 and 0.28 in, 0.43 out
    for r, o1 in O_M1.items():
        v = prim["per_rung"][r]
        assert abs(v["psi"] - 0.1) < 0.03 and v["o_marginal"] == O_M0[r] and v["o_plain"] == O_PL[r]
        assert v["replicate_1"]["o_marginal"] == o1 and abs(v["replicate_1"]["psi"] - 0.1) < 0.03 and v["replicate_1"]["forces_C"] is False  # replicate 1 read with its own constant
    assert prim["per_rung"]["3"]["decisive"] is False and prim["per_rung"]["3"]["m"] == 1 and prim["per_rung"]["3"]["replicate_1"] is None
    soft = fam["soft_erase_r1"]["result"]
    assert soft["reading"] == "B" and soft["decisive"] == ["1", "2"] and fam["soft_erase_r1"]["o_plain"]["1"] == O_PL["1"]
    sec = fam["union_uniform"]["result"]
    assert sec["reading"] == analysis_s7.NO_READING_GUARD and sec["guard"]["rungs"] == ["1", "2"] and "wholly below zero" in sec["guard"]["message"] and sec["decisive"] == ["1", "2"] and sec["m"] == 2
    v = sec["per_rung"]["1"]
    assert v["phi"] is None and v["psi"] is None and v["conditions"] is None and v["reading"] is None and v["denominator_below_zero"] and v["denominator"]["interval"][1] < 0 and v["m"] == 2
    assert abs(v["U"] - (-0.020)) < 0.002 and abs(v["P"] - 0.010) < 0.002 and v["U_interval"][0] < v["U"] < v["U_interval"][1] and np.isfinite(v["M_minus_P"]["interval"]).all() and np.isfinite(v["U_minus_M"]["interval"]).all()
    lines = "\n".join(analysis_s7.write_s7(tmp_path, {"tier_4_present": True, "marginal": out, "code_leaning": None, "code_specific_by_reader_label": None, "canaries": {}}))
    assert "`union_uniform` (secondary): no reading: the named-minus-plain gap is not positive at a decisive rung" in lines and "The headline takes no reading" not in lines
    t = pd.read_csv(tmp_path / "s7_marginal_readings.csv")
    assert t.set_index("family").reading.to_dict() == {"union_r0": "A", "union_uniform": analysis_s7.NO_READING_GUARD, "soft_erase_r1": "B"} and t.set_index("family").guard_fired_at.fillna("").to_dict()["union_uniform"] == "1, 2"
    c = pd.read_csv(tmp_path / "s7_marginal_closure.csv", dtype={"rung": str})
    row = c[(c.family == "union_uniform") & (c.rung == "1")].iloc[0]
    assert row.psi == "undefined" and row.rung_reading == "no reading (the guard)" and row.U_minus_P_interval.startswith("[-") and row.M_minus_P_interval.startswith("[") and row.U_minus_M_interval.startswith("[")
    summary = analysis_s7.summary_of({"tier_4_present": True, "marginal": out, "code_leaning": None})
    assert summary["headline_reading"] == "A" and summary["marginal"]["union_uniform"]["guard_fired_at"] == ["1", "2"]


def test_a_primary_family_with_no_reading_leaves_the_headline_with_none(tmp_path):
    """The headline takes the primary family's reading; where the guard fires there it takes none, and it does not
    pass to the secondary family, whatever that family reads. Two replicates a third apart are read C by the glue as by the rule."""
    levels = {"union_r0": (-0.030, 0.010), "union_uniform": (0.030, -0.005), "soft_erase_r1": (0.436, 0.070)}
    grid, s7_dir = _fabricated_marginal(tmp_path, levels, {"union_r0": 0.1, "union_uniform": 0.1, "soft_erase_r1": 0.9})
    out = analysis_s7.analyze_marginal(grid, s7_dir, {}, {}, 500, 0, log=lambda *_: None)
    assert out["families"]["union_r0"]["result"]["reading"] == analysis_s7.NO_READING_GUARD and out["families"]["union_uniform"]["result"]["reading"] == "A"
    rep = out["families"]["union_r0"]["result"]["per_rung"]["1"]["replicate_1"]
    assert rep["psi"] is None and rep["forces_C"] is False and rep["M_interval"][0] < rep["M"] < rep["M_interval"][1]  # its M is still reported beside
    lines = "\n".join(analysis_s7.write_s7(tmp_path, {"tier_4_present": True, "marginal": out, "code_leaning": None, "code_specific_by_reader_label": None, "canaries": {}}))
    assert "`union_r0` (primary): no reading" in lines and "**The headline takes no reading; it does not pass to the secondary family.**" in lines
    assert analysis_s7.summary_of({"tier_4_present": True, "marginal": out, "code_leaning": None})["headline_reading"] == analysis_s7.NO_READING_GUARD
    from vpd_audit.figures_s7 import figure_marginal

    assert figure_marginal(tmp_path, out)["left_panel_rungs"] == ["1", "2", "2a", "2b"] and (tmp_path / "fig7_marginal_control.png").is_file()
    data = pd.read_csv(tmp_path / "fig7_marginal_control.csv", dtype={"rung": str})
    assert {"U_low", "U_high", "P_low", "P_high", "M_low", "M_high", "donor_positions"} <= set(data.columns) and data.donor_positions.tolist() == [1, 8, 16, 32, 64] and data.psi.isna().all()
    # the replicate rule through the glue: a second replicate planted a third and more away reads C at that rung
    (tmp_path / "c").mkdir()
    levels = {"union_r0": (0.040, -0.011), "union_uniform": (0.030, -0.005), "soft_erase_r1": (0.436, 0.070)}
    grid, s7_dir = _fabricated_marginal(tmp_path / "c", levels, {"union_r0": 0.1, "union_uniform": 0.1, "soft_erase_r1": 0.9}, psi_replicate_1=0.6)
    res = analysis_s7.analyze_marginal(grid, s7_dir, {}, {}, 500, 0, log=lambda *_: None)["families"]["union_r0"]["result"]
    assert res["per_rung"]["1"]["conditions"]["A"] and res["per_rung"]["1"]["replicate_1"]["forces_C"] and res["per_rung"]["1"]["reading"] == "C" and res["reading"] == "C"
