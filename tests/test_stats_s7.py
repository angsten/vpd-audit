"""Known-answer tests of stats_s7.py, as tests/test_stats.py does for stats.py. Fabricated eight-draw
tables of 1,024 texts with planted answers; every reading, the guard, the replicate rule, the decisive-rung rule, the
per-chain positive control, the localization statistic's independent resamples, and the shared resample."""

import numpy as np
import pytest

from vpd_audit import stats as st
from vpd_audit import stats_s7 as s7

K, N, R = 8, 1024, 2000
O_M, O_P = 0.30, 0.15  # the stated pair of overlaps; phi_ov = 0.15 / 0.85
PHI_OV = (O_M - O_P) / (1 - O_P)


def _resample(seed=("s7", "boot"), n=N, replicates=R):
    return st.Resample.make(n, replicates, seed)


def _tables(psi, *, rng_seed=0, noise=0.002, m_minus=None, shift_draws=(), shift=0.0, u_level=0.040, p_level=-0.011):
    """(e_U, e_P, e_M), each (K, N): per-text levels with a text effect the three share, U and P at curve 1's rung-2 values,
    M planted at P + phi (U - P) with phi = phi_ov + psi (1 - phi_ov). `shift_draws` moves M on the named draws by `shift`."""
    rng = np.random.default_rng(rng_seed)
    text = rng.normal(0.0, 0.01, size=N)
    e_u = u_level + text[None, :] + rng.normal(0, noise, size=(K, N))
    e_p = p_level + text[None, :] + rng.normal(0, noise, size=(K, N))
    phi = PHI_OV + psi * (1 - PHI_OV)
    e_m = (p_level + phi * (u_level - p_level)) + text[None, :] + rng.normal(0, noise, size=(K, N))
    for k in shift_draws:
        e_m[k] += shift
    return e_u, e_p, e_m


def _family(psis, **kw):
    rungs = {r: _tables(p, rng_seed=i, **kw) for i, (r, p) in enumerate(psis.items())}
    o = {r: O_M for r in rungs}
    return rungs, o, {r: O_P for r in rungs}


def test_the_pre_registered_worked_example_of_the_matched_control():
    # the worked example prints two decimals and carries the rounded values forward (0.176 as 0.18, 0.3125 as 0.31, then 0.16 for 0.165)
    assert abs(s7.overlap_closure(0.30, 0.15) - 0.18) < 1e-2
    phi = (0.005 + 0.011) / (0.0402 + 0.011)
    assert abs(phi - 0.31) < 1e-2 and abs(float(s7.psi_of(phi, s7.overlap_closure(0.30, 0.15))) - 0.16) < 1e-2
    phi = (0.030 + 0.011) / (0.0402 + 0.011)
    assert abs(phi - 0.80) < 1e-2 and abs(float(s7.psi_of(phi, s7.overlap_closure(0.30, 0.15))) - 0.76) < 1e-2
    assert float(s7.psi_of(s7.overlap_closure(0.4, 0.1), s7.overlap_closure(0.4, 0.1))) == 0.0 and float(s7.psi_of(1.0, 0.18)) == 1.0  # pure conflict is 0, pure composition 1, whatever the overlap


@pytest.mark.parametrize("psi,reading", [(0.1, "A"), (0.5, "C"), (0.9, "B")])
def test_a_planted_psi_returns_its_reading(psi, reading):
    rungs, o_m, o_p = _family({"1": psi, "2": psi})
    out = s7.closure_family(rungs, _resample(), ["1", "2"], o_m, o_p)
    assert out["reading"] == reading and out["m"] == 2
    for r in ("1", "2"):
        pr = out["per_rung"][r]
        assert abs(pr["psi"] - psi) < 0.02 and pr["psi_interval"][0] < psi < pr["psi_interval"][1] and abs(pr["phi_ov"] - PHI_OV) < 1e-12 and pr["decisive"] and pr["reading"] == reading
        assert abs(pr["rho"] - pr["M"] / pr["U"]) < 1e-12 and pr["rho_interval"][0] < pr["rho"] < pr["rho_interval"][1]
        assert len(pr["per_draw"]["M"]) == K and abs(np.mean(pr["per_draw"]["U"]) - pr["U"]) < 1e-12


def test_a_planted_m_above_u_returns_d_also_where_bs_condition_holds():
    rungs, o_m, o_p = _family({"1": 1.4, "2": 1.4})  # phi > 1: M above U, psi above 2/3, M - P positive on every draw
    out = s7.closure_family(rungs, _resample(), ["1", "2"], o_m, o_p)
    assert all(out["per_rung"][r]["conditions"] == {"A": False, "B": True, "D": True} for r in ("1", "2")) and out["reading"] == "D"
    # D takes precedence only where it holds at every decisive rung: B at both, D at one, reads B
    rungs, o_m, o_p = _family({"1": 1.4, "2": 0.9})
    out = s7.closure_family(rungs, _resample(), ["1", "2"], o_m, o_p)
    assert out["per_rung"]["1"]["conditions"]["D"] and not out["per_rung"]["2"]["conditions"]["D"] and out["reading"] == "B"


def test_reading_d_needs_the_mirror_sign_condition_six_of_eight_draws_is_not_enough():
    """D holds only if the interval of M - U lies above zero and M - U is positive on at least seven of eight
    draws. The texts-only interval of M - U is narrow beside the set-to-set noise in M, so without the draws D would fire by
    chance, and it outranks B."""
    e_u, e_p, e_m = _tables(1.4)  # M above U on every draw
    gap = float((e_m - e_u).mean())
    for k in (0, 1):
        e_m[k] -= 1.5 * gap  # two draws' M below U
    for k in range(2, 8):
        e_m[k] += 0.5 * gap  # the mean over draws held where it was
    res = s7.closure_rung(e_u, e_p, e_m, _resample(), 1, o_marginal=O_M, o_plain=O_P, raise_on_undefined=True)
    assert res["M_minus_U"]["interval"][0] > 0 and res["M_minus_U"]["n_draws_positive"] == 6 and res["M_minus_U"]["sign_condition"] is False and res["conditions"]["D"] is False
    assert res["conditions"]["B"] is True  # psi above 2/3 and M - P positive on every draw: B, not D
    assert s7.closure_family({"1": (e_u, e_p, e_m)}, _resample(), ["1"], {"1": O_M}, {"1": O_P})["reading"] == "B"
    # seven of eight is enough
    e_u, e_p, e_m = _tables(1.4)
    e_m[0] -= 1.5 * gap
    e_m[1:] += 1.5 * gap / 7
    res = s7.closure_rung(e_u, e_p, e_m, _resample(), 1, o_marginal=O_M, o_plain=O_P, raise_on_undefined=True)
    assert res["M_minus_U"]["n_draws_positive"] == 7 and res["conditions"]["D"] is True
    assert s7.closure_family({"1": (e_u, e_p, e_m)}, _resample(), ["1"], {"1": O_M}, {"1": O_P})["reading"] == "D"


def test_u_p_and_m_each_carry_an_interval_at_the_rungs_level():
    """At the family's corrected level at a decisive rung, uncorrected at the others."""
    rungs, o_m, o_p = _family({"1": 0.5, "2": 0.5, "3": 0.5})
    rs = _resample()
    out = s7.closure_family(rungs, rs, ["1", "2"], o_m, o_p, replicate_1={"1": _tables(0.5, rng_seed=9)[2]}, o_marginal_replicate_1=o_m)
    for r, m in (("1", 2), ("3", 1)):
        v = out["per_rung"][r]
        for name, e in zip(("U", "P", "M"), rungs[r]):
            want = list(st.percentile_interval(rs.means(e.mean(axis=0)), m))
            assert v[f"{name}_interval"] == want and want[0] < v[name] < want[1]
    wide, narrow = out["per_rung"]["1"]["U_interval"], list(st.percentile_interval(rs.means(rungs["1"][0].mean(axis=0)), 1))
    assert wide[0] < narrow[0] and wide[1] > narrow[1]  # corrected over two rungs: wider than the uncorrected 95 percent
    assert out["per_rung"]["1"]["replicate_1"]["M_interval"][0] < out["per_rung"]["1"]["replicate_1"]["M"] < out["per_rung"]["1"]["replicate_1"]["M_interval"][1]


def test_a_family_with_no_decisive_rung_returns_no_reading_and_its_rungs_are_descriptives():
    rungs, o_m, o_p = _family({"1": 0.1, "2": 0.1})
    out = s7.closure_family(rungs, _resample(), [], o_m, o_p)
    assert out["reading"] == "no reading" and out["m"] == 0
    assert all(pr["decisive"] is False and pr["reading"] is None and pr["m"] == 1 and pr["psi"] is not None for pr in out["per_rung"].values())
    # a mixed family: the non-decisive rung is reported at the uncorrected level and does not enter the reading
    rungs, o_m, o_p = _family({"1": 0.1, "2": 0.1, "3": 0.9})
    out = s7.closure_family(rungs, _resample(), ["1", "2"], o_m, o_p)
    assert out["reading"] == "A" and out["per_rung"]["3"]["m"] == 1 and out["per_rung"]["1"]["m"] == 2 and out["per_rung"]["3"]["reading"] is None


def test_the_sign_conditions_six_of_eight_draws_is_not_enough():
    # a planted B (psi 0.9) whose M - P is positive on only six draws: two draws' M pushed below P, the mean held by the others
    e_u, e_p, e_m = _tables(0.9)
    gap = float((e_m - e_p).mean())
    for k in (0, 1):
        e_m[k] -= 1.5 * gap
    for k in range(2, 8):
        e_m[k] += 0.5 * gap
    res = s7.closure_rung(e_u, e_p, e_m, _resample(), 1, o_marginal=O_M, o_plain=O_P, raise_on_undefined=True)
    assert res["psi_interval"][0] > s7.PSI_B and res["M_minus_P"]["n_draws_positive"] == 6 and res["conditions"]["B"] is False
    out = s7.closure_family({"1": (e_u, e_p, e_m)}, _resample(), ["1"], {"1": O_M}, {"1": O_P})
    assert out["reading"] == "C"
    # seven of eight is enough
    e_u, e_p, e_m = _tables(0.9)
    e_m[0] -= 1.5 * gap
    e_m[1:] += 1.5 * gap / 7
    assert s7.closure_family({"1": (e_u, e_p, e_m)}, _resample(), ["1"], {"1": O_M}, {"1": O_P})["reading"] == "B"
    # likewise A (psi 0.1) with U - M positive on only six draws
    e_u, e_p, e_m = _tables(0.1)
    gap = float((e_u - e_m).mean())
    for k in (0, 1):
        e_m[k] += 1.5 * gap
    for k in range(2, 8):
        e_m[k] -= 0.5 * gap
    res = s7.closure_rung(e_u, e_p, e_m, _resample(), 1, o_marginal=O_M, o_plain=O_P, raise_on_undefined=True)
    assert res["psi_interval"][1] < s7.PSI_A and res["U_minus_M"]["n_draws_positive"] == 6 and res["conditions"]["A"] is False
    assert s7.closure_family({"1": (e_u, e_p, e_m)}, _resample(), ["1"], {"1": O_M}, {"1": O_P})["reading"] == "C"


def test_the_replicate_rule_two_replicates_more_than_a_third_apart_read_c_at_that_rung():
    rungs, o_m, o_p = _family({"1": 0.1, "2": 0.1})
    rep1_far = {"1": _tables(0.6, rng_seed=5)[2], "2": _tables(0.12, rng_seed=6)[2]}
    out = s7.closure_family(rungs, _resample(), ["1", "2"], o_m, o_p, replicate_1=rep1_far, o_marginal_replicate_1=o_m)
    r1, r2 = out["per_rung"]["1"], out["per_rung"]["2"]
    assert r1["conditions"]["A"] and r1["replicate_1"]["psi_gap"] > 1 / 3 and r1["replicate_1"]["forces_C"] and r1["reading"] == "C" and r1["conditions_counted"] == {"A": False, "B": False, "D": False}
    assert r2["replicate_1"]["psi_gap"] < 1 / 3 and r2["reading"] == "A" and out["reading"] == "C"  # whatever the intervals say
    rep1_near = {"1": _tables(0.3, rng_seed=5)[2], "2": _tables(0.12, rng_seed=6)[2]}
    out = s7.closure_family(rungs, _resample(), ["1", "2"], o_m, o_p, replicate_1=rep1_near, o_marginal_replicate_1=o_m)
    assert out["per_rung"]["1"]["replicate_1"]["psi_gap"] < 1 / 3 and out["reading"] == "A"
    # replicate 1's psi uses its own overlap constant: the same M under a larger overlap is a smaller psi
    other = s7.closure_family(rungs, _resample(), ["1", "2"], o_m, o_p, replicate_1=rep1_near, o_marginal_replicate_1={"1": 0.45, "2": O_M})
    assert other["per_rung"]["1"]["replicate_1"]["psi"] < out["per_rung"]["1"]["replicate_1"]["psi"] and other["per_rung"]["1"]["replicate_1"]["phi"] == out["per_rung"]["1"]["replicate_1"]["phi"]
    with pytest.raises(AssertionError, match="its own overlap constant"):
        s7.closure_family(rungs, _resample(), ["1", "2"], o_m, o_p, replicate_1=rep1_near, o_marginal_replicate_1={"2": O_M})


def test_the_strong_form_of_a_m_negative_on_seven_of_eight_draws():
    rungs, o_m, o_p = _family({"1": 0.0, "2": 0.0}, u_level=0.040, p_level=-0.030)  # M = P + phi_ov (U - P) = -0.0176: negative on every draw
    out = s7.closure_family(rungs, _resample(), ["1", "2"], o_m, o_p, strong_form=True)
    assert out["reading"] == "A" and out["strong_form_of_A"] is True and out["per_rung"]["1"]["n_draws_M_negative"] == 8
    rungs, o_m, o_p = _family({"1": 0.1, "2": 0.1})  # curve 1's levels: M = -0.011 + 0.26 * 0.051 > 0
    out = s7.closure_family(rungs, _resample(), ["1", "2"], o_m, o_p, strong_form=True)
    assert out["reading"] == "A" and out["strong_form_of_A"] is False


def test_the_decisive_rungs_come_from_the_overlap_table_by_the_rule():
    o = {"1": 0.0917, "2": 0.2851, "2a": 0.34, "2b": 1.0 / 3.0, "3": 0.7320}
    assert s7.decisive_rungs(o, ["1", "2", "2a", "2b", "3"]) == ["1", "2", "2b"]  # at most one third: 0.34 is out, exactly a third is in
    assert s7.decisive_rungs(o, ["1", "2", "3"]) == ["1", "2"] and s7.decisive_rungs({"1": 0.5}, ["1"]) == []
    with pytest.raises(AssertionError, match="no overlap constant"):
        s7.decisive_rungs(o, ["1", "4"])


def test_the_guard_raises_on_the_whole_set_and_flags_in_a_split():
    # U and P nearly equal against their noise: the denominator's interval straddles zero
    rng = np.random.default_rng(3)
    e_p = rng.normal(0.0, 0.05, size=(K, N))
    e_u = e_p + rng.normal(0.0, 0.02, size=(K, N))
    e_u -= (e_u - e_p).mean()  # U - P is zero on the whole set
    e_m = e_p + 0.004
    rs = _resample()
    with pytest.raises(s7.ClosureUndefined, match="includes zero"):
        s7.closure_family({"1": (e_u, e_p, e_m)}, rs, ["1"], {"1": O_M}, {"1": O_P})
    # as a descriptive rung, and in a descriptive split, it never raises: undefined with its flag, the differences still reported
    out = s7.closure_family({"1": (e_u, e_p, e_m)}, rs, [], {"1": O_M}, {"1": O_P})["per_rung"]["1"]
    assert out["undefined"] is True and out["phi"] is None and out["psi"] is None and out["psi_interval"] is None
    assert abs(out["M_minus_P"]["mean"] - 0.004) < 1e-12 and out["M_minus_P"]["interval"][0] > 0 and np.isfinite(out["U_minus_M"]["interval"]).all()
    masks = {"other": np.arange(N) < 158, "prose": np.arange(N) >= 158}
    good = _tables(0.5)
    mixed = tuple(np.where(masks["other"][None, :], bad, ok) for bad, ok in zip((e_u, e_p, e_m), good))  # undefined on the 158 "other" texts only
    split = s7.closure_split({"1": mixed}, masks, {k: st.Resample.make(int(v.sum()), R, ("s7", "split", k)) for k, v in masks.items()}, {"1": 2}, {"1": O_M}, {"1": O_P})
    assert split["other"]["n"] == 158 and split["other"]["per_rung"]["1"]["undefined"] is True and split["other"]["per_rung"]["1"]["psi"] is None and "conditions" not in split["other"]["per_rung"]["1"]
    assert np.isfinite(split["other"]["per_rung"]["1"]["M_minus_P"]["interval"]).all() and np.isfinite(split["other"]["per_rung"]["1"]["U_minus_M"]["interval"]).all()
    assert split["prose"]["per_rung"]["1"]["undefined"] is False and abs(split["prose"]["per_rung"]["1"]["psi"] - 0.5) < 0.03 and split["prose"]["per_rung"]["1"]["m"] == 2
    # a denominator whose interval lies wholly below zero raises at a decisive rung as one that includes zero does (the readings assume U > P)
    below = _tables(0.5, u_level=-0.030, p_level=0.020)
    with pytest.raises(s7.ClosureUndefined, match="wholly below zero"):
        s7.closure_family({"1": below}, rs, ["1"], {"1": O_M}, {"1": O_P})
    desc = s7.closure_family({"1": below}, rs, [], {"1": O_M}, {"1": O_P})["per_rung"]["1"]  # as a descriptive it is flagged, and nothing raises
    assert desc["denominator_below_zero"] is True and desc["undefined"] is False and desc["denominator"]["interval"][1] < 0 and desc["phi"] is not None
    assert s7.closure_family({"1": good}, rs, ["1"], {"1": O_M}, {"1": O_P})["per_rung"]["1"]["denominator_below_zero"] is False


def test_the_shared_resample_is_shared():
    """phi is recomputed within each replicate from one resample of the texts. With M = U text for text, every replicate's
    phi is exactly 1 only if the numerator and the denominator see the same resampled texts; and two families given one
    Resample object see the same texts."""
    e_u, e_p, _ = _tables(0.5, noise=0.01)
    rs = _resample()
    res = s7.closure_rung(e_u, e_p, e_u.copy(), rs, 2, o_marginal=O_M, o_plain=O_P, raise_on_undefined=True)
    assert res["phi"] == 1.0 and res["phi_interval"] == [1.0, 1.0] and res["psi_interval"] == [1.0, 1.0] and res["M_minus_U"]["interval"] == [0.0, 0.0]
    # a text-level effect common to the three curves cancels in the ratio: the interval is far narrower than independent resamples would give
    e_u, e_p, e_m = _tables(0.5)
    shared = s7.closure_rung(e_u, e_p, e_m, rs, 1, o_marginal=O_M, o_plain=O_P, raise_on_undefined=True)
    other = st.Resample.make(N, R, ("s7", "another"))
    phi_indep = (other.means(e_m.mean(0)) - rs.means(e_p.mean(0))) / (rs.means(e_u.mean(0)) - rs.means(e_p.mean(0)))
    lo, hi = st.percentile_interval(phi_indep, 1)
    assert (shared["phi_interval"][1] - shared["phi_interval"][0]) < 0.2 * (hi - lo)
    with pytest.raises(AssertionError, match="the resample is of the texts"):
        s7.closure_rung(e_u[:, :100], e_p[:, :100], e_m[:, :100], rs, 1, o_marginal=O_M, o_plain=O_P, raise_on_undefined=False)


# ----------------------------------------------------------------------------- the code-leaning chain

N_POS = 256


def _chain(gaps, sizes, *, descriptive=None, seed=0, noise=0.02):
    """Erase (1, N) and control (8, N) per rung on the positive stratum, with a planted paired difference per rung."""
    rng = np.random.default_rng(seed)
    erase, control = {}, {}
    for r, gap in gaps.items():
        base = rng.normal(0.3, 0.1, size=N_POS)
        control[r] = base[None, :] + rng.normal(0, noise, size=(8, N_POS))
        erase[r] = (base + gap + rng.normal(0, noise, size=N_POS))[None, :]
    return erase, control, dict(sizes), (descriptive or {r: False for r in gaps})


def test_the_per_chain_positive_control_passes_and_fails_on_planted_chains():
    rs = st.Resample.make(N_POS, R, ("s7", "gh"))
    sizes = {"G16": 16, "G64": 64, "G256": 256, "G1007": 1007}
    ok = s7.positive_control_per_chain(*_chain({"G16": 0.01, "G64": 0.05, "G256": 0.2, "G1007": 0.6}, sizes), rs)
    assert ok["pass"] is True and ok["rungs_judged"] == ["G64", "G256", "G1007"] and ok["failing_rungs"] == [] and ok["n_control_draws"] == 8
    assert ok["per_rung"]["G16"]["judged"] is False and abs(ok["per_rung"]["G256"]["paired_difference"] - 0.2) < 0.01 and ok["per_rung"]["G256"]["interval"][0] > 0
    # a chain whose only failing rung has 16 members must pass: smaller rungs are reported, not judged
    small = s7.positive_control_per_chain(*_chain({"G16": -0.05, "G64": 0.05, "G256": 0.2, "G1007": 0.6}, sizes), rs)
    assert small["pass"] is True and small["per_rung"]["G16"]["above_zero"] is False and small["per_rung"]["G16"]["paired_difference"] < 0
    # a chain whose control equals its erase must fail: a difference of exactly zero is not above zero
    erase, control, sz, desc = _chain({"G64": 0.05, "G256": 0.2}, {"G64": 64, "G256": 256})
    control["G256"] = np.repeat(erase["G256"], 8, axis=0)
    same = s7.positive_control_per_chain(erase, control, sz, desc, rs)
    assert same["pass"] is False and same["failing_rungs"] == ["G256"] and same["per_rung"]["G256"]["interval"] == [0.0, 0.0] and same["per_rung"]["G256"]["paired_difference"] == 0.0
    # a judged rung whose interval includes zero fails; a descriptive rung is never judged; no rung of 64 members is no judgement
    weak = s7.positive_control_per_chain(*_chain({"G64": 0.0005, "G256": 0.2}, {"G64": 64, "G256": 256}, noise=0.05), rs)
    assert weak["pass"] is False and weak["failing_rungs"] == ["G64"]
    desc_fail = s7.positive_control_per_chain(*_chain({"G64": 0.05, "G1862": -0.3}, {"G64": 64, "G1862": 1862}, descriptive={"G64": False, "G1862": True}), rs)
    assert desc_fail["pass"] is True and desc_fail["per_rung"]["G1862"]["judged"] is False
    assert s7.positive_control_per_chain(*_chain({"G16": 0.3}, {"G16": 16}), rs)["pass"] is None
    erase, control, sz, desc = _chain({"G64": 0.05, "G256": 0.2}, {"G64": 64, "G256": 256})
    control["G256"] = control["G256"][:4]
    with pytest.raises(AssertionError, match="same number of draws"):  # the control has eight draws at every rung
        s7.positive_control_per_chain(erase, control, sz, desc, rs)


def test_the_localization_statistics_two_strata_are_resampled_independently():
    rng = np.random.default_rng(8)
    v = rng.normal(0.4, 0.2, size=N_POS)
    eg, er = v[None, :], np.zeros((8, N_POS))
    rs_a, rs_b = st.Resample.make(N_POS, R, ("s7", "gh")), st.Resample.make(N_POS, R, ("s7", "other"))
    out = s7.localization(eg, er, eg, er, rs_a, rs_b, 1)  # the same values on both strata: a statistic of exactly zero
    assert out["statistic"] == 0.0 and out["positive_stratum"] == out["other_stratum"]
    lo, hi = out["interval"]
    se = v.std(ddof=1) / np.sqrt(N_POS)
    assert lo < 0 < hi and 0.8 * 2 * 1.96 * np.sqrt(2) * se < hi - lo < 1.2 * 2 * 1.96 * np.sqrt(2) * se  # the width of a difference of two independent means, not the zero width one shared resample would give
    with pytest.raises(AssertionError, match="independently"):
        s7.localization(eg, er, eg, er, rs_a, rs_a, 1)
    shifted = s7.localization(eg + 0.3, er, eg, er, rs_a, rs_b, 4)
    assert abs(shifted["statistic"] - 0.3) < 1e-12 and shifted["interval"][0] > 0 and (shifted["interval"][1] - shifted["interval"][0]) > (hi - lo)  # corrected over four rungs: wider


def test_touched_surplus_from_the_per_sequence_columns_against_per_position_arrays():
    rng = np.random.default_rng(2)
    T, n = 512, 40
    kl_cell, kl_ref = rng.random((n, T)) * 0.2, rng.random((n, T)) * 0.01
    t_star = rng.integers(0, T + 1, size=n)
    t_star[:3] = (0, T, 1)
    prefix = np.arange(T)[None, :] < t_star[:, None]
    with np.errstate(invalid="ignore", divide="ignore"):
        d = np.where(t_star > 0, ((kl_cell - kl_ref) * prefix).sum(1) / np.maximum(t_star, 1), np.nan)
    excess = kl_cell.mean(1) - kl_ref.mean(1)
    want = ((kl_cell - kl_ref) * ~prefix).sum(1) / T  # the damage on positions t >= t*
    got = s7.touched_surplus(excess[None, :], d[None, :], t_star[None, :], T)[0]
    np.testing.assert_allclose(got, want, atol=1e-12)
    assert abs(got[0] - excess[0]) < 1e-15 and abs(got[1]) < 1e-12  # nothing clean: all of the damage; never touched: none of it
    r = s7.ratio_of_means(np.full((1, n), 0.2), np.full((8, n), 0.5), st.Resample.make(n, 200, ("s7", "r")))
    assert abs(r["ratio"] - 0.4) < 1e-12 and r["interval"] == [r["ratio"], r["ratio"]] or np.allclose(r["interval"], 0.4)


def _rung(d_gh, d_other, *, ctl=0.05, labels=None, loc=(0.1, 0.3), n=256, half=0.01):
    return {"n_members": n, "D_github": {"mean": d_gh, "interval": [d_gh - half, d_gh + half]}, "D_github_control": ctl, "D_other": {"mean": d_other, "interval": [d_other - half, d_other + half]},
            "d_other_labels": labels or {"0.1": "holds", "0": None}, "localization": {"interval": list(loc)}}


def test_the_readings_r1_to_r4_on_planted_chains():
    order = ["G16", "G64", "G256", "G1007"]
    passed, failed = {"pass": True, "failing_rungs": []}, {"pass": False, "failing_rungs": ["G256"]}
    sizes = dict(zip(order, (16, 64, 256, 1007)))
    # R1: a usable edit at G256: GitHub damage at least 0.5 and three times its control's, other below X, d_other holds where testable
    chain = {r: _rung(0.1, 0.01, n=sizes[r]) for r in order}
    chain["G256"] = _rung(0.9, 0.02, ctl=0.2, n=256)
    chain["G1007"] = _rung(2.0, 0.2, ctl=0.4, n=1007)
    out = s7.code_leaning_readings(chain, order, passed)
    # where R1 is named the label says, per tau_q, whether the conditional claim was testable at the rung where it fired
    assert out["label"] == "R1 at G256 (tau_q 0.1: conditional claim tested and holds, tau_q 0: conditional claim not testable at this rung)"
    assert out["R1_rungs"] == ["G256"] and out["R2"] is False and out["R3"] is False and out["R4"] is False and out["conditions_unread"] is False
    assert out["R1_conditional_claim"] == {"G256": {"0.1": s7.R1_TESTED, "0": s7.R1_NOT_TESTABLE}}
    untestable = {**chain, "G256": {**chain["G256"], "d_other_labels": {"0.1": None, "0": None}}}  # R1 can fire at a rung whose clean prefix is not testable, and the label must then say so
    assert s7.code_leaning_readings(untestable, order, passed)["label"] == "R1 at G256 (tau_q 0.1: conditional claim not testable at this rung, tau_q 0: conditional claim not testable at this rung)"
    chain["G256"]["d_other_labels"] = {"0.1": "holds", "0": "fails"}  # d_other must hold wherever it is testable
    assert s7.code_leaning_readings(chain, order, passed)["label"].startswith("otherwise")
    chain["G256"] = _rung(0.9, 0.02, ctl=0.35, n=256)  # not three times its control's
    assert s7.code_leaning_readings(chain, order, passed)["R1"] is False
    # R2: everywhere below X on other and below 0.5 on GitHub
    flat = {r: _rung(0.2, 0.01, n=sizes[r]) for r in order}
    assert s7.code_leaning_readings(flat, order, passed)["label"] == "R2"
    # R3: other is material (lower end above X) before GitHub's lower end reaches 0.5
    r3 = {r: _rung(0.2, 0.01, n=sizes[r]) for r in order}
    r3["G256"] = _rung(0.3, 0.09, n=256)
    r3["G1007"] = _rung(0.8, 0.3, n=1007)
    out = s7.code_leaning_readings(r3, order, passed)
    assert out["label"] == "R3" and out["first_rung_D_other_material"] == "G256" and out["first_rung_D_github_usable"] == "G1007"
    r3["G64"] = _rung(0.8, 0.01, ctl=0.5, n=64)  # GitHub usable first, but not three times its control's: none of R1 to R3
    assert s7.code_leaning_readings(r3, order, passed)["label"].startswith("otherwise")
    # R4 beside the others: the localization interval includes zero or is negative at every rung of at least 64 members (G16 is not read for it)
    r4 = {r: _rung(0.2, 0.01, n=sizes[r], loc=(-0.05, 0.05)) for r in order}
    r4["G16"]["localization"] = {"interval": [0.2, 0.4]}
    out = s7.code_leaning_readings(r4, order, passed)
    assert out["label"] == "R2" and out["R4"] is True and out["rungs_of_at_least_64"] == ["G64", "G256", "G1007"]
    # a chain whose own positive control fails is not read, whatever its numbers; they are kept beside
    out = s7.code_leaning_readings(flat, order, failed)
    assert out["read"] is False and out["label"].startswith("not read") and "G256" in out["label"] and out["R2"] is None
    # the computed conditions are still returned, flagged unread, for the report to print
    assert out["conditions_unread"] is True and out["conditions_computed"] == {"R1": False, "R1_rungs": [], "R1_conditional_claim": {}, "R2": True, "R3": False, "R4": False, "text": "R2"}
    chain["G256"] = _rung(0.9, 0.02, ctl=0.2, n=256)
    unread = s7.code_leaning_readings(chain, order, failed)
    assert unread["R1"] is None and unread["conditions_computed"]["R1_rungs"] == ["G256"] and unread["conditions_computed"]["text"].startswith("R1 at G256 (tau_q 0.1: conditional claim tested and holds")
    assert s7.code_leaning_readings(flat, order, {"pass": None})["label"].startswith("not read: no rung")
