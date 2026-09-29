"""The tier-4 reading rules as code (the marginal-matched control and the code-leaning chain), on arrays, with no file
reading and no divergence printed: `analysis.py` loads the tables, builds the arrays, and writes the report. `vpd_audit/stats.py`
is frozen and is imported, never changed in behaviour: the sequence bootstrap (`Resample`), the percentile interval, the sign condition, and
the hard-zero rung are its.

Conventions as in stats.py. An excess matrix e has shape (K, N): K draws, N texts, e[k, b] the cell's divergence minus its
rung 0's, paired on the text, the draw, and (under the uniform background) the same u^(k). A family's curves share one
`Resample` of the texts, so every ratio and difference below is recomputed within a replicate from the same resampled texts.

The marginal-matched control. Per rung j: U_j, P_j, M_j, the excess of the named sets, the plain control, and the
marginal control; the gap closure phi_j = (M_j - P_j) / (U_j - P_j); the closure overlap alone would produce,
phi_ov_j = (o_M - o_P) / (1 - o_P), from the label-only overlap constants; and the primary statistic
psi_j = (phi_j - phi_ov_j) / (1 - phi_ov_j), 0 under pure conflict and 1 under pure composition. Intervals: phi recomputed
within each replicate of the shared resample, draws held fixed, mapped to psi by the fixed constants, percentile at level
1 - alpha / m with m the number of decisive rungs of the family.

The code-leaning chain. One erase cell per rung against eight control draws, on two disjoint strata that are
never averaged; the per-chain positive control; the three further statistics; the readings R1 to R4.
"""

from __future__ import annotations

from typing import Any

import numpy as np

from vpd_audit import stats as st
from vpd_audit.constants import SEQ_LEN

DECISIVE_MAX_OVERLAP = 1.0 / 3.0  # a rung is decisive if the marginal control (replicate 0) shares at most a third of the named set's switched mass
PSI_A = 1.0 / 3.0  # reading A: the interval of psi lies below
PSI_B = 2.0 / 3.0  # reading B: the interval of psi lies above
REPLICATE_MAX_GAP = 1.0 / 3.0  # the replicate rule: the width of the band between the two cut-offs
POSITIVE_CONTROL_MIN_MEMBERS = 64  # a sub-rung or ranked chain's positive control is judged at every rung of at least 64 members
D_GITHUB_USABLE = 0.5  # R1, R2, R3: nats
R1_RATIO = 3.0  # R1: the erase's GitHub damage is at least three times its control's
X = st.X_MATERIAL


class ClosureUndefined(ValueError):
    """The closure's guard: on the whole evaluation set at a decisive rung the corrected interval
    of U - P includes zero, or lies wholly below it (the readings assume U > P)."""


# ----------------------------------------------------------------------------- the decisive rungs and the overlap constants


def decisive_rungs(overlap_marginal: dict[str, float], rungs: list[str]) -> list[str]:
    """The rungs, in the order given, whose pooled switched-mass overlap between the marginal control (replicate 0) and the
    named set is at most one third. The constants come from the committed label-only table, never typed by hand."""
    out = []
    for r in rungs:
        assert r in overlap_marginal and np.isfinite(overlap_marginal[r]), f"no overlap constant for rung {r}"
        if float(overlap_marginal[r]) <= DECISIVE_MAX_OVERLAP:
            out.append(r)
    return out


def overlap_closure(o_marginal: float, o_plain: float) -> float:
    """phi_ov = (o_M - o_P) / (1 - o_P): the closure that shared members alone produce under pure conflict."""
    assert 0.0 <= o_plain < 1.0 and 0.0 <= o_marginal <= 1.0, (o_marginal, o_plain)
    return (o_marginal - o_plain) / (1.0 - o_plain)


def psi_of(phi: Any, phi_ov: float) -> Any:
    """psi = (phi - phi_ov) / (1 - phi_ov), elementwise."""
    assert phi_ov < 1.0, phi_ov
    return (np.asarray(phi, dtype=np.float64) - phi_ov) / (1.0 - phi_ov)


# ----------------------------------------------------------------------------- one rung of a family


def _interval(stats: np.ndarray, m: int) -> list[float]:
    lo, hi = st.percentile_interval(stats, m)
    return [lo, hi]


def _difference(a: np.ndarray, b: np.ndarray, resample: st.Resample, m: int) -> dict[str, Any]:
    """a - b for two (K, N) excess matrices: the mean, its interval at level 1 - alpha / m from the shared resample, the
    per-draw means, and how many of them are positive."""
    d = np.asarray(a, np.float64) - np.asarray(b, np.float64)
    per_draw = d.mean(axis=1)
    ok, n_pos, k = st.sign_condition(per_draw, 0.0)
    return {"mean": float(d.mean(axis=0).mean()), "interval": _interval(resample.means(d.mean(axis=0)), m), "per_draw": per_draw.tolist(), "n_draws_positive": n_pos, "n_draws": k, "sign_condition": bool(ok)}


def closure_rung(e_u: np.ndarray, e_p: np.ndarray, e_m: np.ndarray, resample: st.Resample, m: int, *, o_marginal: float, o_plain: float, raise_on_undefined: bool) -> dict[str, Any]:
    """One rung: U, P, M, each with its own interval; phi, phi_ov, psi, and rho = M / U with their intervals; the differences
    M - P, U - M, and M - U with theirs and their draw-level sign counts; the per-draw table; the rung's reading conditions.
    The guard: if the interval of the denominator U - P includes zero, or lies wholly below it (the readings
    assume U > P), a decisive rung on the whole set raises (`raise_on_undefined`). Anywhere else an interval that includes
    zero returns phi, psi, and their intervals as None with `undefined` set, one wholly below zero is flagged
    (`denominator_below_zero`), and the differences are reported all the same."""
    e_u, e_p, e_m = (np.asarray(x, dtype=np.float64) for x in (e_u, e_p, e_m))
    assert e_u.ndim == 2 and e_u.shape == e_p.shape == e_m.shape, (e_u.shape, e_p.shape, e_m.shape)
    assert e_u.shape[1] == resample.n, "the resample is of the texts these matrices hold"
    K = e_u.shape[0]
    u_seq, p_seq, m_seq = e_u.mean(axis=0), e_p.mean(axis=0), e_m.mean(axis=0)
    U, P, M = float(u_seq.mean()), float(p_seq.mean()), float(m_seq.mean())
    Ur, Pr, Mr = resample.means(u_seq), resample.means(p_seq), resample.means(m_seq)  # one resample: the three curves move together
    den = Ur - Pr
    den_interval = _interval(den, m)
    undefined = bool(not (den_interval[0] > 0.0 or den_interval[1] < 0.0))
    below_zero = bool(den_interval[1] < 0.0)
    if (undefined or below_zero) and raise_on_undefined:
        raise ClosureUndefined(f"the interval of U - P {'includes zero' if undefined else 'lies wholly below zero (the readings assume U > P)'}: {U - P:+.6f} [{den_interval[0]:+.6f}, {den_interval[1]:+.6f}] at m = {m}")
    phi_ov = overlap_closure(o_marginal, o_plain)
    out: dict[str, Any] = {"U": U, "P": P, "M": M, "U_interval": _interval(Ur, m), "P_interval": _interval(Pr, m), "M_interval": _interval(Mr, m),  # each at the rung's level
                           "n_draws": K, "n_texts": int(e_u.shape[1]), "m": m, "o_marginal": float(o_marginal), "o_plain": float(o_plain), "phi_ov": float(phi_ov),
                           "denominator": {"mean": U - P, "interval": den_interval}, "undefined": undefined, "denominator_below_zero": below_zero,
                           "per_draw": {"U": e_u.mean(axis=1).tolist(), "P": e_p.mean(axis=1).tolist(), "M": e_m.mean(axis=1).tolist()},
                           "M_minus_P": _difference(e_m, e_p, resample, m), "U_minus_M": _difference(e_u, e_m, resample, m), "M_minus_U": _difference(e_m, e_u, resample, m),
                           "n_draws_M_negative": int((e_m.mean(axis=1) < 0).sum())}
    if undefined:
        out.update({"phi": None, "phi_interval": None, "psi": None, "psi_interval": None})
    else:
        with np.errstate(divide="ignore", invalid="ignore"):
            phi_r = np.where(den != 0, (Mr - Pr) / np.where(den != 0, den, 1.0), np.nan)
        phi = (M - P) / (U - P)
        out.update({"phi": float(phi), "phi_interval": _interval(phi_r, m), "psi": float(psi_of(phi, phi_ov)), "psi_interval": _interval(psi_of(phi_r, phi_ov), m),
                    "n_replicates_with_zero_denominator": int((den == 0).sum())})
    with np.errstate(divide="ignore", invalid="ignore"):
        rho_r = np.where(Ur != 0, Mr / np.where(Ur != 0, Ur, 1.0), np.nan)
    out.update({"rho": float(M / U) if U != 0 else float("nan"), "rho_interval": _interval(rho_r, m)})
    psi_iv = out["psi_interval"]
    # D carries the mirror sign condition: the texts-only interval of M - U is narrow beside the set-to-set noise in M,
    # so without the draws D would fire by chance, and it outranks B
    out["conditions"] = {"A": bool(psi_iv is not None and psi_iv[1] < PSI_A and out["U_minus_M"]["sign_condition"]), "B": bool(psi_iv is not None and psi_iv[0] > PSI_B and out["M_minus_P"]["sign_condition"]),
                         "D": bool(out["M_minus_U"]["interval"][0] > 0.0 and out["M_minus_U"]["sign_condition"])}
    return out


def rung_reading(conditions: dict[str, bool], *, forced_c: bool = False) -> str:
    """A rung's own reading. D takes precedence where B holds too; the replicate rule forces C whatever the intervals say."""
    if forced_c:
        return "C"
    if conditions["D"]:
        return "D"
    if conditions["A"]:
        return "A"
    if conditions["B"]:
        return "B"
    return "C"


def closure_family(rungs: dict[str, tuple[np.ndarray, np.ndarray, np.ndarray]], resample: st.Resample, decisive: list[str], o_marginal: dict[str, float], o_plain: dict[str, float], *,
                   replicate_1: dict[str, np.ndarray] | None = None, o_marginal_replicate_1: dict[str, float] | None = None, strong_form: bool = False) -> dict[str, Any]:
    """A family of the marginal-matched control: `rungs` maps each rung to its (e_U, e_P, e_M) with M the marginal control's replicate 0.
    The decisive rungs are read at level 1 - alpha / m, m their number, with the guard raising; the others are descriptives
    at the uncorrected level with the guard flagging. The replicate rule (the primary family): at a rung that replicate 1
    also ran, if the two replicates' point values of psi differ by more than a third, the rung reads C. The family's reading
    is a condition at every decisive rung: D where D holds at each (it takes precedence over B), else A, else B, else C; a
    family with no decisive rung returns no reading."""
    assert all(r in rungs for r in decisive), (decisive, list(rungs))
    m = len(decisive)
    per_rung: dict[str, Any] = {}
    for r, (e_u, e_p, e_m) in rungs.items():
        is_dec = r in decisive
        res = closure_rung(e_u, e_p, e_m, resample, m if is_dec else 1, o_marginal=o_marginal[r], o_plain=o_plain[r], raise_on_undefined=is_dec)
        res["decisive"] = is_dec
        rep = None
        if replicate_1 is not None and r in replicate_1:
            assert o_marginal_replicate_1 is not None and r in o_marginal_replicate_1, f"replicate 1 has its own overlap constant at rung {r}"
            r1 = closure_rung(e_u, e_p, replicate_1[r], resample, m if is_dec else 1, o_marginal=o_marginal_replicate_1[r], o_plain=o_plain[r], raise_on_undefined=False)
            gap = abs(res["psi"] - r1["psi"]) if (res["psi"] is not None and r1["psi"] is not None) else None
            rep = {"M": r1["M"], "M_interval": r1["M_interval"], "phi": r1["phi"], "psi": r1["psi"], "psi_interval": r1["psi_interval"], "o_marginal": r1["o_marginal"], "phi_ov": r1["phi_ov"], "per_draw_M": r1["per_draw"]["M"],
                   "psi_gap": gap, "forces_C": bool(gap is not None and gap > REPLICATE_MAX_GAP)}
        res["replicate_1"] = rep
        forced = bool(rep and rep["forces_C"])
        # the conditions a family's reading counts at this rung: none of them where the replicate rule forces C
        res["conditions_counted"] = {k: bool(v and not forced) for k, v in res["conditions"].items()} if is_dec else None
        res["reading"] = rung_reading(res["conditions"], forced_c=forced) if is_dec else None
        per_rung[r] = res
    if not decisive:
        reading = "no reading"  # "at every decisive rung" would hold vacuously for every reading
    else:  # each reading is a condition at every decisive rung; D before B where both hold; anything else is C
        reading = next((x for x in ("D", "A", "B") if all(per_rung[r]["conditions_counted"][x] for r in decisive)), "C")
    out = {"m": m, "decisive": list(decisive), "per_rung": per_rung, "reading": reading}
    if strong_form:  # reported if reading A holds on the primary family: M negative on at least K - 1 of K draws at every decisive rung, so the sign reversal survives matching
        out["strong_form_of_A"] = bool(reading == "A" and all(per_rung[r]["n_draws_M_negative"] >= (per_rung[r]["n_draws"] - 1 if per_rung[r]["n_draws"] > 1 else per_rung[r]["n_draws"]) for r in decisive))
    return out


def closure_split(rungs: dict[str, tuple[np.ndarray, np.ndarray, np.ndarray]], masks: dict[str, np.ndarray], resamples: dict[str, st.Resample], levels: dict[str, int],
                  o_marginal: dict[str, float], o_plain: dict[str, float]) -> dict[str, Any]:
    """A descriptive split (by reader label): per label and rung the same statistics on the label's texts with the label's own
    resample, at the rung's level on the whole set; it never raises, and carries no reading."""
    out: dict[str, Any] = {}
    for lab, mask in masks.items():
        out[lab] = {"n": int(mask.sum()), "per_rung": {}}
        for r, (e_u, e_p, e_m) in rungs.items():
            res = closure_rung(e_u[:, mask], e_p[:, mask], e_m[:, mask], resamples[lab], levels[r], o_marginal=o_marginal[r], o_plain=o_plain[r], raise_on_undefined=False)
            res.pop("conditions")
            out[lab]["per_rung"][r] = res
    return out


# ----------------------------------------------------------------------------- the code-leaning chain


def mean_interval(e: np.ndarray, resample: st.Resample, m: int) -> dict[str, Any]:
    """The mean over draws and texts of a (K, N) matrix with its interval at level 1 - alpha / m from the stratum's resample."""
    e = np.asarray(e, dtype=np.float64)
    assert e.ndim == 2 and e.shape[1] == resample.n
    seq = e.mean(axis=0)
    return {"mean": float(seq.mean()), "interval": _interval(resample.means(seq), m), "n_draws": int(e.shape[0]), "n_texts": int(e.shape[1])}


def positive_control_per_chain(erase: dict[str, np.ndarray], control: dict[str, np.ndarray], sizes: dict[str, int], descriptive: dict[str, bool], resample: st.Resample,
                               *, min_members: int = POSITIVE_CONTROL_MIN_MEMBERS) -> dict[str, Any]:
    """The per-chain rule, adopted before the code-leaning chain ran (earlier chains keep their frozen verdicts), for a
    sub-rung or ranked chain: on the positive stratum, at every rung
    the rule reads that has at least 64 members, the paired erase-minus-control unconditional damage, as a mean over the
    control's draws, has its uncorrected 95 percent sequence-bootstrap interval above zero. Smaller rungs and descriptive
    rungs are reported with their paired differences and not judged. `erase[r]` is (1, N) and `control[r]` (K, N), on the
    positive stratum's texts; the control has the same number of draws at every rung."""
    per_rung: dict[str, Any] = {}
    n_draws = {int(np.asarray(control[r]).shape[0]) for r in erase}
    assert len(n_draws) == 1, f"the control has the same number of draws at every rung: {sorted(n_draws)}"
    for r, e in erase.items():
        e, c = np.asarray(e, np.float64), np.asarray(control[r], np.float64)
        assert e.shape[0] == 1 and e.shape[1] == c.shape[1] == resample.n, (e.shape, c.shape, resample.n)
        d = (e - c).mean(axis=0)  # the mean over the control's draws of the paired difference; exactly zero, draw by draw, where a control equals its erase
        lo, hi = st.percentile_interval(resample.means(d), 1)
        judged = bool((not descriptive[r]) and sizes[r] >= min_members)
        per_rung[r] = {"n_members": int(sizes[r]), "descriptive": bool(descriptive[r]), "judged": judged, "paired_difference": float(d.mean()), "interval": [lo, hi], "above_zero": bool(lo > 0.0),
                       "per_draw": (e - c).mean(axis=1).tolist()}
    judged_rungs = [r for r, v in per_rung.items() if v["judged"]]
    failing = [r for r in judged_rungs if not per_rung[r]["above_zero"]]
    return {"per_rung": per_rung, "rungs_judged": judged_rungs, "failing_rungs": failing, "n_control_draws": n_draws.pop(), "pass": (not failing) if judged_rungs else None}


def localization(erase_pos: np.ndarray, control_pos: np.ndarray, erase_other: np.ndarray, control_other: np.ndarray, resample_pos: st.Resample, resample_other: st.Resample, m: int) -> dict[str, Any]:
    """(D_G - D_R) on the positive stratum minus (D_G - D_R) on the other: two disjoint strata, so the interval comes from
    independent resamples of the two, the pairing on texts kept within each (as `stats.unpaired_difference` pairs), at
    level 1 - alpha / m."""
    assert np.asarray(erase_pos).shape[0] == 1 and np.asarray(erase_other).shape[0] == 1, "one erase cell per rung, against the control's draws"
    a = (np.asarray(erase_pos, np.float64) - np.asarray(control_pos, np.float64)).mean(axis=0)  # paired on the text, draw by draw, then the mean over draws
    b = (np.asarray(erase_other, np.float64) - np.asarray(control_other, np.float64)).mean(axis=0)
    assert a.size == resample_pos.n and b.size == resample_other.n and resample_pos.replicates == resample_other.replicates
    assert resample_pos.seed_tuple != resample_other.seed_tuple or resample_pos.seed_tuple == ("explicit",), "the two strata are resampled independently: their seeds differ"
    stats = resample_pos.means(a) - resample_other.means(b)
    return {"statistic": float(a.mean() - b.mean()), "interval": _interval(stats, m), "positive_stratum": float(a.mean()), "other_stratum": float(b.mean()), "n_pos": int(a.size), "n_other": int(b.size)}


def touched_surplus(excess: np.ndarray, d: np.ndarray, t_star: np.ndarray, T: int = SEQ_LEN) -> np.ndarray:
    """Per draw and text, the unconditional damage that falls outside the clean prefix: (1 / T) sum over t >= t* of the cell's
    per-position divergence minus the reference's. From the per-sequence columns: the whole sum is T times the excess, and
    the prefix's is t* times the conditional damage d (d is NaN and the prefix empty where t* = 0), so the
    surplus is excess - (t* / T) d."""
    excess, d, t = np.asarray(excess, np.float64), np.asarray(d, np.float64), np.asarray(t_star, np.int64)
    assert excess.shape == d.shape == t.shape
    assert not np.isnan(d[t > 0]).any(), "the conditional damage is defined wherever the clean prefix is not empty"
    return excess - (t / float(T)) * np.where(t > 0, np.nan_to_num(d, nan=0.0), 0.0)


def ratio_of_means(num: np.ndarray, den: np.ndarray, resample: st.Resample, m: int = 1) -> dict[str, Any]:
    """mean(num) / mean(den) over draws and texts ((K, N) each), recomputed within each replicate of the shared resample."""
    a, b = np.asarray(num, np.float64).mean(axis=0), np.asarray(den, np.float64).mean(axis=0)
    ar, br = resample.means(a), resample.means(b)
    with np.errstate(divide="ignore", invalid="ignore"):
        r = np.where(br != 0, ar / np.where(br != 0, br, 1.0), np.nan)
    return {"ratio": float(a.mean() / b.mean()) if b.mean() != 0 else float("nan"), "interval": _interval(r, m), "numerator": float(a.mean()), "denominator": float(b.mean())}


R1_TESTED = "conditional claim tested and holds"
R1_NOT_TESTABLE = "conditional claim not testable at this rung"


def code_leaning_readings(per_rung: dict[str, dict[str, Any]], rungs_in_order: list[str], positive_control: dict[str, Any], *, min_members: int = POSITIVE_CONTROL_MIN_MEMBERS) -> dict[str, Any]:
    """R1 to R4 on the rungs within the group (the non-descriptive rungs, in chain order). Each rung carries `n_members`,
    `D_github` and `D_other` ({mean, interval}, the intervals at the chain's corrected level), `D_github_control` (the mean),
    `d_other_labels` ({tau_q: the hard-zero rule's label on the other stratum, or None where not testable}), and
    `localization` ({interval}). A chain whose own positive control does not pass is not read; its computed conditions are
    still returned and printed, flagged unread. R1 to R3 are reported as the conditions that hold; the rules order none
    above another, so where more than one holds all are named. Where R1 is named the label says, per tau_q, whether the
    conditional claim was testable at the rung where it fired: R1 can fire at a rung whose
    clean prefix is not testable. R4 is read beside the others, never instead: the labels' code-leaning shows no
    code-specific effect at these sizes."""
    rungs = list(rungs_in_order)
    assert all(r in per_rung for r in rungs)
    r1_at = [r for r in rungs if per_rung[r]["D_github"]["interval"][0] >= D_GITHUB_USABLE and per_rung[r]["D_github"]["mean"] >= R1_RATIO * per_rung[r]["D_github_control"]
             and per_rung[r]["D_other"]["interval"][1] < X and all(lab == "holds" for lab in per_rung[r]["d_other_labels"].values() if lab is not None)]
    r1_detail = {r: {tq: (R1_TESTED if lab == "holds" else R1_NOT_TESTABLE) for tq, lab in per_rung[r]["d_other_labels"].items()} for r in r1_at}
    r2 = bool(rungs) and all(per_rung[r]["D_other"]["interval"][1] < X and per_rung[r]["D_github"]["interval"][1] < D_GITHUB_USABLE for r in rungs)
    first_other = next((i for i, r in enumerate(rungs) if per_rung[r]["D_other"]["interval"][0] > X), None)
    first_github = next((i for i, r in enumerate(rungs) if per_rung[r]["D_github"]["interval"][0] >= D_GITHUB_USABLE), None)
    r3 = bool(first_other is not None and (first_github is None or first_other < first_github))
    big = [r for r in rungs if per_rung[r]["n_members"] >= min_members]
    r4 = bool(all(per_rung[r]["localization"]["interval"][0] <= 0.0 for r in big)) if big else None
    r1_text = "R1 at " + "; ".join(f"{r} ({', '.join(f'tau_q {tq}: {txt}' for tq, txt in r1_detail[r].items())})" for r in r1_at) if r1_at else ""
    holds = [text for text, ok in ((r1_text, bool(r1_at)), ("R2", r2), ("R3", r3)) if ok]
    conditions_text = " and ".join(holds) if holds else "otherwise (none of R1 to R3): reported as measured, rung by rung"
    read = positive_control.get("pass") is True
    label = conditions_text if read else \
        ("not read: the chain's positive control fails at rungs " + ", ".join(positive_control.get("failing_rungs", [])) if positive_control.get("pass") is False else "not read: no rung of at least 64 members judges the positive control")
    conditions = {"R1": bool(r1_at), "R1_rungs": r1_at, "R1_conditional_claim": r1_detail, "R2": r2, "R3": r3, "R4": r4, "text": conditions_text}
    return {"read": bool(read), "label": label, "R1": bool(r1_at) if read else None, "R1_rungs": r1_at if read else None, "R1_conditional_claim": r1_detail if read else None, "R2": r2 if read else None,
            "R3": r3 if read else None, "R4": r4 if read else None, "first_rung_D_other_material": rungs[first_other] if first_other is not None else None,
            "first_rung_D_github_usable": rungs[first_github] if first_github is not None else None, "rungs_read": rungs, "rungs_of_at_least_64": big,
            "conditions_computed": conditions, "conditions_unread": not read}
