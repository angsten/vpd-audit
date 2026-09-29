"""The pre-registered reading rules as code, on known answers. The registered four-sequence, two-draw worked
example; the correction count and the rung order; fabricated eight-draw, 1,024-sequence union tables at both spreads
(paired noise 0.05 and 0.3) with a planted material bump, a planted immaterial bump, and a null; a null-calibration
test at the 0.3 spread; the readability floor at its boundaries; a fabricated hard-zero chain with a known budget and a
planted positive-control failure; the decile bins; the shared resample."""

from __future__ import annotations

import numpy as np
import pytest

from vpd_audit import stats as st
from vpd_audit.constants import SEQ_LEN

RUNGS_10 = ["1", "2", "3", "4", "5", "5a", "6", "6a", "7", "8"]
RUNGS_8 = ["1", "2", "3", "4", "5", "6", "7", "8"]


# --------------------------------------------------------------------------- the registered worked example


def test_the_worked_example_of_four_sequences_two_draws():
    k0 = np.array([0.30, 0.25, 0.40, 0.35])
    d1 = np.array([0.33, 0.27, 0.41, 0.36])
    d2 = np.array([0.31, 0.24, 0.42, 0.37])
    e = np.stack([d1 - k0, d2 - k0])
    assert e.mean(axis=1).tolist() == pytest.approx([0.0175, 0.0100])
    assert float(e.mean()) == pytest.approx(0.01375)
    rs = st.Resample.from_index_sets([[0, 0, 2, 3], [1, 1, 1, 3]], n=4)
    reps = rs.means(e.mean(axis=0))
    assert reps.tolist() == pytest.approx([0.0175, 0.0075])
    # with an interval of [0.006, 0.019] the bump is detected and not material
    res = st.union_rung(e, st.Resample.make(4, 2000, (0, "boot", "test")), m=1)
    assert res["per_draw"] == pytest.approx([0.0175, 0.0100]) and res["n_draws_positive"] == 2 and res["sign_condition"]
    assert res["detected"] and not res["material"] and res["e_hat"] == pytest.approx(0.01375)


# --------------------------------------------------------------------------- the correction count and the rung order


def test_correction_count_and_rung_order():
    assert st.correction_count(RUNGS_10, "union") == 10 and st.correction_count(RUNGS_8, "union") == 8
    assert st.correction_count(RUNGS_10, "hard_zero") == 9 and st.correction_count(RUNGS_8, "hard_zero") == 7
    assert st.correction_count(["S4", "S16", "S64"], "code_specific_hard") == 3
    assert st.correction_count(["1", "2", "3", "4", "5", "5a", "6", "6a", "7", "B50", "B75", "8"], "never_named_hard") == 11
    assert st.sort_rungs(["8", "7", "6a", "6", "5", "5a", "4", "3", "2", "1"]) == ["1", "2", "3", "4", "5a", "5", "6a", "6", "7", "8"]
    assert st.sort_rungs(["8", "B75", "B50", "7"]) == ["7", "B50", "B75", "8"]
    assert st.sort_rungs(["S64", "S4", "S16"]) == ["S4", "S16", "S64"]
    assert st.donor_count_order("5a") < st.donor_count_order("5") and st.donor_count_order("6a") < st.donor_count_order("6") and st.donor_count_order("3") < st.donor_count_order("4")
    assert st.nested_runs(RUNGS_10) == [["1", "2", "3"], ["4", "5a", "5", "6a", "6", "7", "8"]]
    assert st.nested_runs(["1", "S4", "S16", "8"]) == [["1"], ["8"], ["S4", "S16"]]


# --------------------------------------------------------------------------- fabricated union tables


def fabricate_union(seed: int, *, n_seq: int = 1024, n_draws: int = 8, rungs: list[str] = RUNGS_10, rung0_sd: float = 0.15, paired_sd: float = 0.05, bump: float = 0.0, bump_rung: str | None = None,
                    rung8_one_draw: bool = True) -> dict[str, np.ndarray]:
    """The registered example's magnitudes: rung 0 per sequence N(0.34, rung0_sd), paired noise N(0, paired_sd) per (draw, rung, sequence),
    a bump added at one rung; rung 8 with one draw under r = 0."""
    rng = np.random.default_rng(seed)
    out = {}
    for r in rungs:
        K = 1 if (r == "8" and rung8_one_draw) else n_draws
        e = rng.normal(0.0, paired_sd, size=(K, n_seq))
        if bump_rung is not None and r == bump_rung:
            e += bump
        out[r] = e
    return out


@pytest.mark.parametrize("paired_sd", [0.05, 0.3])
def test_planted_bumps_at_both_spreads(paired_sd):
    rs = st.Resample.make(1024, 2000, (0, "boot", f"fab{paired_sd}"))
    material = st.union_curve(fabricate_union(1, paired_sd=paired_sd, bump=0.08, bump_rung="4"), "union", rs)
    null = st.union_curve(fabricate_union(3, paired_sd=paired_sd), "union", rs)
    assert material["label"] == "fails" and material["j_mat"] == "4" and material["j_det"] == "4" and material["m"] == 10
    assert null["label"] == "holds at the scale tested" and null["j_det"] is None and null["j_mat"] is None
    if paired_sd == 0.05:
        immaterial = st.union_curve(fabricate_union(2, paired_sd=paired_sd, bump=0.01, bump_rung="6"), "union", rs)
        assert immaterial["label"] == "detected but immaterial" and immaterial["j_det"] == "6" and immaterial["j_mat"] is None
        hw = immaterial["per_rung"]["6"]["half_width"]
        assert 0.0008 < hw < 0.004  # near 0.0015: the paired design detects 0.01 where an unpaired one, at a spread of 0.15, would not
    else:
        # at a spread of 0.3 per point and eight independent draws the half-width is near 0.3 / sqrt(8 * 1024) * 2.8 = 0.0093 (0.028 at
        # one draw, rung 8), so a 0.01 bump sits at the edge of detection: "detected but immaterial" now spans "too noisy to call"
        immaterial = st.union_curve(fabricate_union(2, paired_sd=paired_sd, bump=0.01, bump_rung="6"), "union", rs)
        hw = immaterial["per_rung"]["6"]["half_width"]
        assert 0.007 < hw < 0.014 and immaterial["label"] in ("holds at the scale tested", "detected but immaterial")
        one_draw = st.union_rung(fabricate_union(2, paired_sd=paired_sd)["8"], rs, m=10)
        assert 0.02 < one_draw["half_width"] < 0.04  # the one-draw rung: near 0.028
    # every label is printed with its half-width; the m = 8 alternative is reported and does not change these labels
    assert all("half_width" in p for p in material["per_rung"].values()) and not material["label_differs_at_m_8"]


def test_null_calibration_at_the_0_3_spread():
    """200 null tables at 4,000 replicates each: the fraction with a detection at any rung must not exceed 0.10 (the corrected
    level is 0.05). Planted bumps cannot catch an interval that is too narrow; this can."""
    rs = st.Resample.make(1024, 4000, (0, "boot", "null-calibration"))
    detections = 0
    for i in range(200):
        res = st.union_curve(fabricate_union(1000 + i, paired_sd=0.3), "union", rs)
        detections += int(res["j_det"] is not None)
    assert detections / 200 <= 0.10, detections


def test_replicate_function_and_shared_resample():
    rs = st.Resample.make(10, 50, (0, "boot", "E"))
    assert rs.W.shape == (50, 10) and (rs.W.sum(axis=1) == 10).all()
    # the same index set reaches every family in a replicate: two vectors resampled with the same W
    a, b = np.arange(10, dtype=float), np.arange(10, dtype=float) ** 2
    ma, mb = rs.means(a), rs.means(b)
    assert np.allclose(rs.means(a + b), ma + mb)
    again = st.Resample.make(10, 50, (0, "boot", "E"))
    assert np.array_equal(rs.W, again.W) and not np.array_equal(rs.W, st.Resample.make(10, 50, (0, "boot", "E_lab")).W)


# --------------------------------------------------------------------------- the readability floor and the hard-zero rule


def test_readability_floor_at_its_boundaries():
    K, N = 8, 1024

    def t_with(n_contributing: int, clean_fraction: float) -> np.ndarray:
        t = np.zeros((K, N), dtype=np.int64)
        t[:, :n_contributing] = SEQ_LEN  # contributing sequences never touched
        # set the clean-prefix fraction exactly through one more sequence's t* (positions are integers, so aim within 1/(N T))
        total_needed = clean_fraction * N * SEQ_LEN
        remaining = total_needed - n_contributing * SEQ_LEN
        if remaining > 0:
            t[:, n_contributing] = min(SEQ_LEN, int(round(remaining)))
        return t

    r64 = st.readability(t_with(64, 0.0))
    r63 = st.readability(t_with(63, 0.0))
    assert r64["mean_n_contributing"] == 64 and r64["mean_clean_prefix_fraction"] == pytest.approx(64 / 1024) and r64["floor_met"]
    assert r63["mean_n_contributing"] == 63 and not r63["floor_met"]
    # the clean-prefix boundary: 70 contributors (above 64) whose prefixes set the fraction, every other sequence touched at
    # position 7 (below 8, so not contributing): 0.049 against 0.05
    t = np.zeros((K, N), dtype=np.int64)
    t[:, 70:] = 7
    t[:, :70] = 272  # (70 * 272 + 954 * 7) / (1024 * 512) = 0.04905
    r = st.readability(t)
    assert 0.049 <= r["mean_clean_prefix_fraction"] < 0.05 and r["mean_n_contributing"] == 70 and not r["floor_met"]
    t[:, :70] = 283  # 0.05052
    r2 = st.readability(t)
    assert r2["mean_clean_prefix_fraction"] >= 0.05 and r2["mean_n_contributing"] == 70 and r2["floor_met"]


def fabricate_hard_zero(seed: int, per_rung_d: dict[str, float], testable: dict[str, bool], *, n_seq: int = 256, n_draws: int = 8, noise: float = 0.02) -> tuple[dict, dict]:
    rng = np.random.default_rng(seed)
    d, t = {}, {}
    for r, level in per_rung_d.items():
        tt = np.full((n_draws, n_seq), SEQ_LEN, dtype=np.int64)
        if not testable[r]:
            tt[:, :] = 3  # every sequence touched before position 8: nothing contributes
        dd = rng.normal(level, noise, size=(n_draws, n_seq))
        dd[tt == 0] = np.nan
        d[r], t[r] = dd, tt
    return d, t


def test_hard_zero_chain_budget_and_labels():
    rungs = ["1", "2", "3", "4", "5", "5a", "6", "6a", "7", "8"]
    levels = {"1": 0.0, "2": 0.005, "3": 0.01, "4": 0.02, "5a": 0.03, "5": 0.03, "6a": 0.07, "6": 0.09, "7": 0.2, "8": 0.5}
    testable = {r: True for r in rungs}
    testable["7"] = False
    d, t = fabricate_hard_zero(5, levels, testable)
    rs = st.Resample.make(256, 2000, (0, "boot", "hz"))
    res = st.hard_zero_chain(d, t, "hard_zero", rs)
    assert res["rungs"] == ["1", "2", "3", "4", "5a", "5", "6a", "6", "7"] and res["m"] == 9  # rung 8 not compared
    labels = {r: res["per_rung"][r]["result"]["label"] if res["per_rung"][r]["result"] else "not testable" for r in res["rungs"]}
    assert labels["5"] == "holds" and labels["6a"] == "fails" and labels["6"] == "fails" and labels["7"] == "not testable"
    assert res["budget"]["budget_rung"] == "5" and not res["per_rung"]["7"]["testable"]
    assert res["per_rung"]["6"]["result"]["n_draws_above_X"] == 8 and res["per_rung"]["6"]["result"]["sign_condition"]
    # a rung between: interval straddling X is indeterminate
    d2, t2 = fabricate_hard_zero(6, {"1": 0.05}, {"1": True}, noise=0.5)
    r2 = st.hard_zero_rung(d2["1"], t2["1"], rs, 1)
    assert r2["label"] == "indeterminate"


def test_positive_control_rules_and_a_planted_failure():
    rungs = ["1", "2", "3", "4", "5", "5a", "6", "6a", "7", "8", "S4", "S16", "S64"]
    rng = np.random.default_rng(9)
    erase = {r: rng.normal(0.3, 0.05, size=(8, 256)) for r in rungs}
    control = {r: rng.normal(0.2, 0.05, size=(8, 256)) for r in rungs}
    pc = st.positive_control_paired(erase, control, rungs)
    assert pc["pass"] and sorted(pc["per_rung"]) == ["4", "5", "5a", "6", "6a", "7", "8", "S16", "S4", "S64"]
    control["6a"] = erase["6a"] + 0.01  # the control exceeds the erase at 6a: the curve's positive control fails
    pc2 = st.positive_control_paired(erase, control, rungs)
    assert not pc2["pass"] and not pc2["per_rung"]["6a"]["positive"] and pc2["per_rung"]["6"]["positive"]
    dmg = {r: rng.normal(0.3, 0.05, size=(8, 1024)) for r in rungs if r not in ("S4", "S16", "S64")}
    assert st.positive_control_material(dmg, list(dmg))["pass"]
    dmg["5a"] = rng.normal(0.02, 0.01, size=(8, 1024))
    assert not st.positive_control_material(dmg, list(dmg))["pass"]


# --------------------------------------------------------------------------- the deciles and the slope


def test_decile_bins_with_overflow_and_an_unpopulated_bin():
    rng = np.random.default_rng(11)
    n = 200
    sig_u = rng.uniform(0, 100, size=3000)
    seq_u = rng.integers(0, n, size=3000)
    exc_u = 0.001 * sig_u + rng.normal(0, 0.01, size=3000)
    edges = st.decile_edges(sig_u)
    assert edges.shape == (11,) and edges[0] == sig_u.min() and edges[-1] == sig_u.max()
    b = st.assign_bins(np.array([edges[0], edges[-1], edges[-1] + 1, edges[0] - 1, (edges[3] + edges[4]) / 2]), edges)
    assert b.tolist() == [0, 9, 10, -1, 3]
    sig_c = rng.uniform(50, 130, size=3000)  # the control moves more mass: points above the top edge, none in the low bins
    seq_c = rng.integers(0, n, size=3000)
    exc_c = 0.001 * sig_c + 0.02 + rng.normal(0, 0.01, size=3000)
    rs = st.Resample.make(n, 500, (0, "boot", "dec"))
    bins = st.binned_difference({"excess": exc_u, "sigma": sig_u, "seq": seq_u}, {"excess": exc_c, "sigma": sig_c, "seq": seq_c}, edges, rs)
    assert len(bins) == 11 and bins[10]["overflow"] and bins[10]["n_points_control"] > 0 and bins[10]["n_points_union"] == 0 and not bins[10]["populated"]
    assert not bins[0]["populated"] and bins[8]["populated"] and bins[8]["difference"] < 0 and bins[8]["interval"][1] < 0
    s = st.ols_slope(sig_u, exc_u, seq_u, rs)
    assert abs(s["slope"] - 0.001) < 0.0002 and s["slope_interval"][0] < 0.001 < s["slope_interval"][1] and abs(s["intercept"]) < 0.01


def test_paired_and_unpaired_differences_and_two_level():
    rng = np.random.default_rng(2)
    a = rng.normal(0.1, 0.05, size=(8, 300))
    b = a - 0.02 + rng.normal(0, 0.01, size=(8, 300))
    rs = st.Resample.make(300, 1000, (0, "boot", "pd"))
    p = st.paired_difference(a, b, rs)
    assert abs(p["mean"] - 0.02) < 0.003 and p["interval"][0] > 0.01
    ra, rb = st.Resample.make(150, 1000, (0, "boot", "a")), st.Resample.make(150, 1000, (0, "boot", "b"))
    u = st.unpaired_difference(a[:, :150], b[:, 150:], ra, rb)
    assert abs(u["mean"] - 0.02) < 0.01
    lo, hi = st.two_level_interval(a - 0.1, rs, 10, (0, "boot2"))
    assert lo < 0 < hi


def test_compared_rungs_refuses_a_mixed_list():
    """The sub-rungs are their own chain; a list mixing them with donor rungs is refused, not silently split."""
    with pytest.raises(AssertionError, match="sub-rungs or none"):
        st.compared_rungs(["1", "2", "S4"], "code_specific_hard")
    assert st.compared_rungs(["S4", "S16", "S64"], "code_specific_hard") == ["S4", "S16", "S64"]
    assert st.compared_rungs(["0", "1", "8"], "union") == ["1", "8"]


def test_donor_count_order_places_2a_and_2b_between_2_and_3_without_a_change_here():
    """The frozen rung order sorts by the schedule's counts, so the descriptive rungs 2a (16 positions)
    and 2b (32) fall between 2 (8) and 3 (64) in the position run with no change to stats.py."""
    assert st.donor_count_order("2") < st.donor_count_order("2a") < st.donor_count_order("2b") < st.donor_count_order("3")
    assert st.donor_count_order("2a")[0] == st.donor_count_order("2b")[0] == 0
    assert st.sort_rungs(["3", "2b", "1", "2a", "2"]) == ["1", "2", "2a", "2b", "3"]
    assert st.nested_runs(["1", "2", "2a", "2b", "3", "4", "8"]) == [["1", "2", "2a", "2b", "3"], ["4", "8"]]
