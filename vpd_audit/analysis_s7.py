"""The tier-4 analysis: builds the arrays `stats_s7.py` reads from the loaded grid, asserts what the registered rules
assert, and writes the tables, the report section, and the two figures. `analysis.analyze` calls `analyze_s7` after the
pipeline of tiers 1 to 3, which never sees a tier-4 cell: the tier-4 cells are kept out of its chains, so every table it
wrote before comes out byte for byte as it did.

What is asserted before anything is read: the marginal sets a store ran are, by source hash,
the sets the committed label-only pre-read judged (marginal_composition.csv), and so are the union and plain sets the
overlap constants were read on; the code-leaning chain's and its twins' against code_leaning_chain.csv and
code_leaning_control_per_draw.csv; the two canaries bitwise against tiers 1 and 2 (in the loader, with the references);
digests equal iff sources equal along every tier-4 chain (P4); the two-path recompute of the conditional damage; the
readability floor judged on the tables against the pre-read's testability table.

The decisive rungs are never typed: the rule is applied here to the committed marginal_overlap_by_rung.csv.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from vpd_audit import stats as st
from vpd_audit import stats_s7 as s7
from vpd_audit.cells import MARGINAL_OTHER_FAMILY_RUNGS, MARGINAL_RUNGS, TIER_4, Cell, code_leaning_size, marginal_canaries
from vpd_audit.constants import SEQ_LEN

S7_PRE_READS_SUBDIR = "s7"
SOFT_ERASE_READ_RUNGS = ("1", "2")  # at rung 3 the named-minus-plain gap is a quarter of the named cost, and a ratio there is not informative
# (key, title, family, background, rungs, the plain control's family in the overlap table, role)
FAMILIES = (
    ("union_r0", "curve 1: the union under the labels background", "union", "r0", MARGINAL_RUNGS, "union", "primary"),
    ("union_uniform", "curve 2: the union under the uniform background, the mean over draws, each draw paired on its own u^(k)", "union", "uniform", MARGINAL_OTHER_FAMILY_RUNGS, "union", "secondary"),
    ("soft_erase_r1", "the soft erase under the ones background", "soft_erase", "r1", MARGINAL_OTHER_FAMILY_RUNGS, "soft_erase", "third"),
)


NO_READING_GUARD = "no reading: the named-minus-plain gap is not positive at a decisive rung"


def family_with_the_guard_caught(data: dict[str, tuple[np.ndarray, np.ndarray, np.ndarray]], rs: Any, decisive: list[str], o_m: dict[str, float], o_p: dict[str, float], **kw: Any) -> dict[str, Any]:
    """`stats_s7.closure_family` raises where, at a decisive rung on the whole set, the interval of U - P includes
    zero or lies below it. The glue catches that per family, on the paper's runs and the stand-in alike (one path for every
    run): the family gets no reading, and its rungs are still reported, each with U, P, M and their intervals, the
    denominator's interval, and the differences M - P and U - M with theirs, at the rung's own level. No ratio is reported
    at a rung whose denominator is not positive, and no condition of A, B, or D is evaluated anywhere in the family. The
    other families and the code-leaning chain are read as they would have been."""
    try:
        return s7.closure_family(data, rs, decisive, o_m, o_p, **kw)
    except s7.ClosureUndefined as e:
        m = len(decisive)
        per_rung: dict[str, Any] = {}
        fired = []
        for r, (e_u, e_p, e_m) in data.items():
            v = s7.closure_rung(e_u, e_p, e_m, rs, m if r in decisive else 1, o_marginal=o_m[r], o_plain=o_p[r], raise_on_undefined=False)
            if v["undefined"] or v["denominator_below_zero"]:
                v.update({"phi": None, "phi_interval": None, "psi": None, "psi_interval": None})
                if r in decisive:
                    fired.append(r)
            rep = None
            if kw.get("replicate_1") and r in kw["replicate_1"]:  # replicate 1's M is still reported beside; it has no psi to compare
                r1 = s7.closure_rung(e_u, e_p, kw["replicate_1"][r], rs, m if r in decisive else 1, o_marginal=kw["o_marginal_replicate_1"][r], o_plain=o_p[r], raise_on_undefined=False)
                rep = {"M": r1["M"], "M_interval": r1["M_interval"], "phi": None, "psi": None, "psi_interval": None, "o_marginal": r1["o_marginal"], "phi_ov": r1["phi_ov"], "per_draw_M": r1["per_draw"]["M"], "psi_gap": None, "forces_C": False}
            v.update({"decisive": r in decisive, "conditions": None, "conditions_counted": None, "reading": None, "replicate_1": rep})
            per_rung[r] = v
        assert fired, "the guard raised, so it fired at a decisive rung"
        return {"m": m, "decisive": list(decisive), "per_rung": per_rung, "reading": NO_READING_GUARD, "guard": {"raised": True, "rungs": fired, "message": str(e)}}


def has_tier_4(grid: Any) -> bool:
    return any(o.tier >= TIER_4 for sd in grid.sets.values() for o in sd.cell_objects.values())


def _rel(p: Any) -> str:
    """A path as the report prints it: relative to the project root where it lies under it."""
    from vpd_audit import env

    try:
        return str(Path(p).resolve().relative_to(env.PROJECT_ROOT))
    except ValueError:
        return str(p)


def _iv(v: Any) -> str:
    from vpd_audit.analysis import _interval

    return _interval(v) if isinstance(v, list) else ("undefined" if v is None else str(v))


# ----------------------------------------------------------------------------- the label-only constants


def load_overlap_constants(s7_dir: Path) -> dict[str, Any]:
    """The committed overlap table of the label-only pre-read: o_M per replicate and rung, o_P per plain family and rung, all
    `overlap_mass_pooled` (total intersection mass over total named mass across the draws)."""
    t = pd.read_csv(Path(s7_dir) / "marginal_overlap_by_rung.csv", dtype={"rung": str})
    out: dict[str, Any] = {"marginal": {}, "plain": {}, "path": _rel(Path(s7_dir) / "marginal_overlap_by_rung.csv")}
    for rep, g in t[t.control == "marginal"].groupby("replicate"):
        out["marginal"][int(rep)] = {str(r): float(o) for r, o in zip(g.rung, g.overlap_mass_pooled)}
    for fam, g in t[t.control == "plain"].groupby("family"):
        out["plain"][str(fam)] = {str(r): float(o) for r, o in zip(g.rung, g.overlap_mass_pooled)}
    assert 0 in out["marginal"] and out["plain"], f"no marginal or plain overlap rows in {out['path']}"
    return out


def assert_sets_are_the_pre_reads(sd: Any, s7_dir: Path) -> dict[str, Any]:
    """Every marginal cell's source hash equals the hash the pre-read recorded for that rung, draw, and replicate
    (the sets built on Modal), and every union and plain cell the overlap constants were read on equals its row too."""
    comp = pd.read_csv(Path(s7_dir) / "marginal_composition.csv", dtype={"rung": str, "draw": str})
    comp = comp[comp.draw != "pooled"]
    marg = {(str(r), int(k), int(rep)): h for r, k, rep, h in zip(comp[comp.control == "marginal"].rung, comp[comp.control == "marginal"].draw, comp[comp.control == "marginal"].replicate, comp[comp.control == "marginal"].source_sha256)}
    named = {str(c): h for c, h in zip(comp[comp.control != "marginal"].cell, comp[comp.control != "marginal"].source_sha256)}
    n_m = n_n = 0
    for name, c in sd.cell_objects.items():
        got = sd.cells.loc[name, "source_sha256"]
        if c.control == "marginal":
            key = (c.rung, c.draw, c.replicate)
            assert key in marg and marg[key] == got, f"{name}: its set ({str(got)[:16]}) is not the label-only pre-read's ({marg.get(key, 'absent')[:16]}); the overlap constants were read on the pre-read's"
            n_m += 1
        elif name in named:
            assert named[name] == got, f"{name}: its set is not the one the overlap constants were read on"
            n_n += 1
    return {"n_marginal_cells": n_m, "n_union_and_plain_cells": n_n, "table": _rel(Path(s7_dir) / "marginal_composition.csv"), "pass": True}


def p4_tier_4(sd: Any, cells: list[Cell]) -> dict[str, Any]:
    """P4 along a tier-4 chain, as analysis.preconditions reads it: digests equal iff sources equal (an equal-digest pair
    with different sources a defect only if its switched mass differs too); non-empty rungs distinct from rung 0."""
    from vpd_audit.analysis import ref_cell_name

    ct = sd.cells
    refn = ref_cell_name(cells[0])
    ref_digest = ct.loc[refn, "mask_fp_cell"] if refn in ct.index else None
    defects = 0
    for i, a in enumerate(cells):
        for b in cells[i + 1 :]:
            same_src, same_dig = ct.loc[a.name, "source_sha256"] == ct.loc[b.name, "source_sha256"], ct.loc[a.name, "mask_fp_cell"] == ct.loc[b.name, "mask_fp_cell"]
            if same_dig != same_src and ((not same_dig) or not np.array_equal(sd.vector(a.name, "sigma"), sd.vector(b.name, "sigma"), equal_nan=True)):
                defects += 1
    distinct = ref_digest is None or all(ct.loc[c.name, "mask_fp_cell"] != ref_digest for c in cells if int(ct.loc[c.name, "n_on"]) > 0)
    return {"n_cells": len(cells), "defects": defects, "non_empty_distinct_from_rung_0": bool(distinct), "pass": bool(defects == 0 and distinct)}


# ----------------------------------------------------------------------------- the marginal-matched control


def _pick(sd: Any, family: str, background: str, control: str, replicate: int, rungs: tuple[str, ...]) -> dict[str, list[Cell]]:
    out: dict[str, list[Cell]] = {}
    for c in sd.cell_objects.values():
        if (c.family, c.eval_set, c.donor_pool, c.tau, c.background, c.delta, c.control, c.replicate) == (family, "E", "D_unif", 0.1, background, "excluded", control, replicate) and c.rung in rungs \
                and c.donor_side_reference is None:
            out.setdefault(c.rung, []).append(c)
    for r in out:
        out[r].sort(key=lambda x: x.draw)
    return out


def analyze_marginal(grid_all: Any, s7_dir: Path, labels: dict[str, Any], resamples: dict, replicates: int, master_seed: int, log: Any = print) -> dict[str, Any] | None:
    """The marginal-matched control on the three families. Returns None where the grid holds no marginal cell."""
    from vpd_audit.analysis import _resample_for, excess_matrix

    if "E" not in grid_all.sets or not any(c.control == "marginal" for c in grid_all.sets["E"].cell_objects.values()):
        return None
    sd = grid_all.sets["E"]
    consts = load_overlap_constants(s7_dir)
    out: dict[str, Any] = {"overlap_table": consts["path"], "sets_assert": assert_sets_are_the_pre_reads(sd, s7_dir), "families": {}, "p4": {}}
    rs = _resample_for(grid_all, "E", None, replicates, master_seed, resamples)  # one resample of E's texts for the three curves and every rung of every family
    for key, title, family, background, rungs, plain_family, role in FAMILIES:
        U, P, M = (_pick(sd, family, background, ctl, 0, rungs) for ctl in ("none", "plain", "marginal"))
        M1 = _pick(sd, family, background, "marginal", 1, rungs)
        present = [r for r in rungs if r in U and r in P and r in M and len(U[r]) == len(P[r]) == len(M[r]) and [c.draw for c in U[r]] == [c.draw for c in P[r]] == [c.draw for c in M[r]]]
        missing = [r for r in rungs if r not in present]
        if not present:
            out["families"][key] = {"title": title, "role": role, "available": False, "rungs_missing": missing}
            continue
        o_m, o_p = consts["marginal"][0], consts["plain"][plain_family]
        decisive = s7.decisive_rungs(o_m, present)
        decisive_by_rule = list(decisive)
        if family == "soft_erase":
            decisive = [r for r in decisive if r in SOFT_ERASE_READ_RUNGS]
        data = {r: (excess_matrix(sd, U[r]), excess_matrix(sd, P[r]), excess_matrix(sd, M[r])) for r in present}
        rep1 = {r: excess_matrix(sd, M1[r]) for r in present if r in M1 and len(M1[r]) == len(M[r])} if role == "primary" else {}
        res = family_with_the_guard_caught(data, rs, decisive, o_m, o_p, replicate_1=rep1 or None, o_marginal_replicate_1=consts["marginal"].get(1) if rep1 else None, strong_form=role == "primary")
        for r in present:
            res["per_rung"][r]["n_on"] = float(np.mean([sd.cells.loc[c.name, "n_on"] for c in M[r]]))
        entry: dict[str, Any] = {"title": title, "role": role, "available": True, "rungs": present, "rungs_missing": missing, "decisive_by_the_rule": decisive_by_rule, "result": res,
                                 "plain_overlap_family": plain_family, "o_marginal": {r: o_m[r] for r in present}, "o_plain": {r: o_p[r] for r in present}}
        if "E_reader" in labels:  # the split by reader label: differences always, the ratio where its denominator's interval leaves zero out
            masks = labels["E_reader"]["groups"]
            rs_l = {lab: _resample_for(grid_all, "E", mask, replicates, master_seed, resamples) for lab, mask in masks.items()}
            entry["by_reader_label"] = s7.closure_split(data, masks, rs_l, {r: res["per_rung"][r]["m"] for r in present}, o_m, o_p)
        else:
            entry["by_reader_label"] = None
        out["families"][key] = entry
        for ctl, rep, chain in (("marginal", 0, M), ("marginal", 1, M1)):
            cells = [c for r in chain for c in chain[r]]
            if cells:
                out["p4"][f"{key}/ctl-{ctl}/rep{rep}"] = p4_tier_4(sd, cells)
        log(f"[analyze s7] {key}: rungs {present}, decisive {decisive}, reading {res['reading']}")
    assert all(v["pass"] for v in out["p4"].values()), f"P4 fails on a tier-4 chain: {[k for k, v in out['p4'].items() if not v['pass']]}"
    # the two things stated before the launch beside rung 1's reading, from the committed label-only tables
    comp = pd.read_csv(Path(s7_dir) / "marginal_composition.csv", dtype={"rung": str, "draw": str})
    r1 = comp[(comp.rung == "1") & (comp.replicate == 0) & (comp.control.isin(["union", "marginal"])) & ((comp.family == "union") | (comp.control == "marginal"))]
    out["rung_1_usage_per_draw"] = r1[["control", "draw", "n", "mean_usage", "p90_usage", "mean_norm", "p90_norm"]].to_dict("records")
    pooled = {c: r1[(r1.control == c) & (r1.draw == "pooled")].iloc[0] for c in ("union", "marginal")}
    out["rung_1_matching"] = {"usage_ratio_marginal_to_union": float(pooled["marginal"].mean_usage / pooled["union"].mean_usage), "norm_ratio_marginal_to_union": float(pooled["marginal"].mean_norm / pooled["union"].mean_norm)}
    with open(Path(s7_dir) / "summary.json") as f:
        out["real_position_sets"] = json.load(f)["marginal"].get("real_position_sets")
    return out


# ----------------------------------------------------------------------------- the code-leaning chain


def analyze_code_leaning(grid_all: Any, s7_dir: Path, strata: dict[str, Any], resamples: dict, replicates: int, master_seed: int, log: Any = print) -> dict[str, Any] | None:
    """The code-leaning chain. Returns None where the grid holds no code-leaning cell."""
    from vpd_audit.analysis import _resample_for, excess_matrix, matrix

    if "E_lab" not in grid_all.sets or "E_lab" not in strata:
        return None
    sd = grid_all.sets["E_lab"]
    cl = [c for c in sd.cell_objects.values() if c.family == "code_leaning_hard"]
    if not cl:
        return None
    erase = {c.rung: c for c in cl if c.control == "none"}
    control: dict[str, list[Cell]] = {}
    for c in cl:
        if c.control == "usage":
            control.setdefault(c.rung, []).append(c)
    for r in control:
        control[r].sort(key=lambda x: x.draw)
    rungs = sorted(erase, key=code_leaning_size)
    assert set(control) == set(erase) and len({len(control[r]) for r in rungs}) == 1, "every rung has its control, with the same number of draws"
    sizes = {r: code_leaning_size(r) for r in rungs}
    desc = {r: bool(erase[r].descriptive) for r in rungs}
    read_rungs = [r for r in rungs if not desc[r]]
    m = max(len(read_rungs), 1)
    # the sets are the pre-read's, by source hash
    chain_t, ctl_t = pd.read_csv(Path(s7_dir) / "code_leaning_chain.csv"), pd.read_csv(Path(s7_dir) / "code_leaning_control_per_draw.csv")
    want_chain = {int(n): h for n, h in zip(chain_t.rung_size, chain_t.source_sha256)}
    want_ctl = {(int(n), int(k)): h for n, k, h in zip(ctl_t.rung_size, ctl_t.draw, ctl_t.source_sha256)}
    for r in rungs:
        assert sd.cells.loc[erase[r].name, "source_sha256"] == want_chain[sizes[r]] and int(sd.cells.loc[erase[r].name, "n_on"]) == sizes[r], f"{erase[r].name}: not the rung the pre-read judged"
        for c in control[r]:
            assert sd.cells.loc[c.name, "source_sha256"] == want_ctl[(sizes[r], c.draw)], f"{c.name}: not the control the pre-read judged"
    groups = strata["E_lab"]["groups"]
    pos_name = strata["E_lab"]["positive"]
    pos, other = groups[pos_name], groups["other"]
    rs = {"positive": _resample_for(grid_all, "E_lab", pos, replicates, master_seed, resamples), "other": _resample_for(grid_all, "E_lab", other, replicates, master_seed, resamples)}
    masks = {"positive": pos, "other": other}
    test_t = pd.read_csv(Path(s7_dir) / "code_leaning_testability.csv")
    out: dict[str, Any] = {"positive_stratum": pos_name, "rungs": rungs, "sizes": sizes, "descriptive": desc, "rungs_read": read_rungs, "m": m, "n_control_draws": len(control[rungs[0]]), "per_rung": {},
                           "p4": {"erase": p4_tier_4(sd, [erase[r] for r in rungs]), "control": p4_tier_4(sd, [c for r in rungs for c in control[r]])}, "floor_mismatches": []}
    assert out["p4"]["erase"]["pass"] and out["p4"]["control"]["pass"], out["p4"]
    e_g = {r: excess_matrix(sd, [erase[r]]) for r in rungs}  # (1, N): the erase's divergence minus its rung 0's (unmasked with the residual, the target itself)
    e_c = {r: excess_matrix(sd, control[r]) for r in rungs}  # (K, N)
    out["positive_control"] = s7.positive_control_per_chain({r: e_g[r][:, pos] for r in rungs}, {r: e_c[r][:, pos] for r in rungs}, sizes, desc, rs["positive"])
    for r in rungs:
        level = m if not desc[r] else 1  # the descriptive rungs below the group carry uncorrected 95 percent intervals
        row: dict[str, Any] = {"n_members": sizes[r], "descriptive": desc[r], "level_m": level}
        for sname, mask in masks.items():
            tag = "github" if sname == "positive" else "other"
            row[f"D_{tag}"] = s7.mean_interval(e_g[r][:, mask], rs[sname], level)
            ctl = s7.mean_interval(e_c[r][:, mask], rs[sname], level)
            row[f"D_{tag}_control"] = ctl["mean"]
            row[f"D_{tag}_control_interval"] = ctl["interval"]
            row[f"conditional_{tag}"] = {}
            for who, cells in (("group", [erase[r]]), ("control", control[r])):
                for tq in ("0.1", "0"):
                    d, t = matrix(sd, cells, f"d_{tq}")[:, mask], matrix(sd, cells, f"t_star_{tq}")[:, mask]
                    read = st.readability(t)
                    res = st.hard_zero_rung(d, t, rs[sname], level, one_cell=len(cells) == 1) if read["floor_met"] else None
                    row[f"conditional_{tag}"][f"{who}|{tq}"] = {"readability": read, "testable": read["floor_met"], "d_hat": res["d_hat"] if res else float("nan"), "interval": res["interval"] if res else None,
                                                                 "label": res["label"] if res else None}
                    pre = test_t[(test_t.chain == who) & (test_t.rung_size == sizes[r]) & (test_t.tau_q == f"tau_q{float(tq):g}") & (test_t.stratum == (pos_name if sname == "positive" else "other"))]
                    if len(pre) != 1 or bool(pre.iloc[0].floor_met) != read["floor_met"] or abs(float(pre.iloc[0].mean_n_contributing) - read["mean_n_contributing"]) > 1e-9:
                        out["floor_mismatches"].append((r, tag, who, tq))
            # the damage outside the clean prefix, the over-removal, and the surplus per unit of over-removal, the group and its control
            row[f"touched_{tag}"] = {}
            for who, cells, e in (("group", [erase[r]], e_g[r]), ("control", control[r], e_c[r])):
                om = matrix(sd, cells, "omega")[:, mask]
                for tq in ("0.1", "0"):
                    sp = s7.touched_surplus(e[:, mask], matrix(sd, cells, f"d_{tq}")[:, mask], matrix(sd, cells, f"t_star_{tq}")[:, mask])
                    row[f"touched_{tag}"][f"{who}|{tq}"] = {"surplus": s7.mean_interval(sp, rs[sname], 1), "over_removal": float(om.mean()), "surplus_per_over_removal": s7.ratio_of_means(sp, om, rs[sname])}
        row["D_github_ratio_to_control"] = float(row["D_github"]["mean"] / row["D_github_control"]) if row["D_github_control"] else float("nan")
        row["d_other_labels"] = {tq: row["conditional_other"][f"group|{tq}"]["label"] for tq in ("0.1", "0")}
        row["localization"] = s7.localization(e_g[r][:, pos], e_c[r][:, pos], e_g[r][:, other], e_c[r][:, other], rs["positive"], rs["other"], level)
        out["per_rung"][r] = row
    assert not out["floor_mismatches"], f"the readability floor judged on the tables differs from the pre-read's testability table at {out['floor_mismatches'][:5]}"
    # the hard-zero rule's budget on the other stratum, over the rungs within the group, per tau_q (read only if the chain's own positive control passes)
    out["budget_other"] = {tq: st.editing_budget(read_rungs, {r: out["per_rung"][r]["conditional_other"][f"group|{tq}"]["label"] or "not testable with these donors" for r in read_rungs},
                                                 {r: out["per_rung"][r]["conditional_other"][f"group|{tq}"]["testable"] for r in read_rungs}) for tq in ("0.1", "0")}
    out["readings"] = s7.code_leaning_readings(out["per_rung"], read_rungs, out["positive_control"])
    # the unconditional damage on each source of "other", the group and its control, per rung, uncorrected 95 percent, each source's own resample
    out["by_source"] = []
    for sname in sorted(k for k in groups if k not in ("all", "other", pos_name)):
        rs_s = _resample_for(grid_all, "E_lab", groups[sname], replicates, master_seed, resamples)
        for r in rungs:
            for who, e in (("group", e_g[r]), ("control", e_c[r])):
                mi = s7.mean_interval(e[:, groups[sname]], rs_s, 1)
                out["by_source"].append({"rung": r, "n_members": sizes[r], "descriptive": desc[r], "source": sname, "n_texts": int(groups[sname].sum()), "set": who, "n_draws": mi["n_draws"], "D": mi["mean"], "interval_95": mi["interval"]})
    with open(Path(s7_dir) / "summary.json") as f:
        cls = json.load(f)["code_leaning"]
    out["pre_read"] = {"existence": cls["existence"]["verdict"], "thresholds": cls.get("thresholds"), "control_gate": cls.get("chain", {}).get("control_gate")}
    log(f"[analyze s7] code-leaning: rungs {rungs}, read {read_rungs} (m = {m}), positive control {out['positive_control']['pass']}, reading {out['readings']['label']}")
    return out


# ----------------------------------------------------------------------------- the code-specific chain on E by reader label


def code_specific_on_E_by_reader_label(grid: Any, labels: dict[str, Any], resamples: dict, replicates: int, master_seed: int) -> dict[str, Any] | None:
    """The code-specific hard-zero chain on E was analysed with E as one stratum; here the same rule's
    machinery per reader label, conditional and unconditional. Per label its own resample; the conditional damage through
    `stats.hard_zero_chain` exactly as the whole set is read (its m, its floor, its one-cell rule), so a label holding every
    text reproduces the whole-set table; the unconditional damage with an uncorrected 95 percent interval. An analysis
    addition only: it reads stores that are already open and carries no verdict."""
    from vpd_audit.analysis import SUB_RUNGS, _resample_for, build_chains, excess_matrix, matrix

    if "E" not in grid.sets or "E_reader" not in labels:
        return None
    sd = grid.sets["E"]
    out: dict[str, Any] = {}
    for ch in build_chains(sd).values():
        if ch.family != "code_specific_hard" or ch.control != "none":
            continue
        parts = {"donor_chain": {r: cs for r, cs in ch.rungs.items() if r not in SUB_RUNGS}, "sub_rung_chain": {r: cs for r, cs in ch.rungs.items() if r in SUB_RUNGS}}
        rows = []
        for lab, mask in labels["E_reader"]["groups"].items():
            rs = _resample_for(grid, "E", mask, replicates, master_seed, resamples)
            for part, rungs in parts.items():
                if not rungs or not st.compared_rungs(list(rungs), ch.family):
                    continue
                for tq in ("0.1", "0"):
                    res = st.hard_zero_chain({r: matrix(sd, cs, f"d_{tq}")[:, mask] for r, cs in rungs.items()}, {r: matrix(sd, cs, f"t_star_{tq}")[:, mask] for r, cs in rungs.items()}, ch.family, rs)
                    for r in res["rungs"]:
                        pr = res["per_rung"][r]
                        un = s7.mean_interval(excess_matrix(sd, rungs[r])[:, mask], rs, 1)
                        rows.append({"chain": ch.label, "part": part, "reader_label": lab, "n_texts": int(mask.sum()), "rung": r, "n_off": float(np.mean([sd.cells.loc[c.name, "n_on"] for c in rungs[r]])), "tau_q": tq, "m": res["m"],
                                     "unconditional": un["mean"], "unconditional_interval": un["interval"], "mean_n_contributing": pr["readability"]["mean_n_contributing"],
                                     "mean_clean_prefix_fraction": pr["readability"]["mean_clean_prefix_fraction"], "testable": pr["testable"], "d_hat": pr["result"]["d_hat"] if pr["result"] else float("nan"),
                                     "d_interval": pr["result"]["interval"] if pr["result"] else None, "label": pr["result"]["label"] if pr["result"] else "not testable with these donors",
                                     "budget_rung": res["budget"]["budget_rung"]})
        out[ch.label] = rows
    return out or None


# ----------------------------------------------------------------------------- tables, the report section, the command's entry


def _closure_rows(key: str, entry: dict[str, Any]) -> list[dict[str, Any]]:
    rows = []
    for r in entry["rungs"]:
        v = entry["result"]["per_rung"][r]
        rep = v.get("replicate_1") or {}
        rows.append({"family": key, "role": entry["role"], "rung": r, "decisive": v["decisive"], "m": v["m"], "n_draws": v["n_draws"], "n_on": v.get("n_on"), "U": v["U"], "U_interval": _iv(v["U_interval"]), "P": v["P"], "P_interval": _iv(v["P_interval"]), "M": v["M"], "M_interval": _iv(v["M_interval"]),
                     "M_minus_P": v["M_minus_P"]["mean"], "M_minus_P_interval": _iv(v["M_minus_P"]["interval"]), "M_minus_P_draws_positive": v["M_minus_P"]["n_draws_positive"],
                     "U_minus_M": v["U_minus_M"]["mean"], "U_minus_M_interval": _iv(v["U_minus_M"]["interval"]), "U_minus_M_draws_positive": v["U_minus_M"]["n_draws_positive"],
                     "M_minus_U_interval": _iv(v["M_minus_U"]["interval"]), "M_minus_U_draws_positive": v["M_minus_U"]["n_draws_positive"], "M_draws_negative": v["n_draws_M_negative"], "U_minus_P": v["denominator"]["mean"],
                     "U_minus_P_interval": _iv(v["denominator"]["interval"]), "U_minus_P_below_zero": v["denominator_below_zero"],
                     "o_marginal": v["o_marginal"], "o_plain": v["o_plain"], "phi_ov": v["phi_ov"], "phi": v["phi"] if v["phi"] is not None else "undefined", "phi_interval": _iv(v["phi_interval"]),
                     "psi": v["psi"] if v["psi"] is not None else "undefined", "psi_interval": _iv(v["psi_interval"]), "rho": v["rho"], "rho_interval": _iv(v["rho_interval"]), "undefined": v["undefined"],
                     "condition_A": v["conditions"]["A"] if v["conditions"] else "", "condition_B": v["conditions"]["B"] if v["conditions"] else "", "condition_D": v["conditions"]["D"] if v["conditions"] else "",
                     "rung_reading": v["reading"] if v["reading"] is not None else ("no reading (the guard)" if entry["result"].get("guard") else "descriptive"),
                     "replicate_1_M": rep.get("M"), "replicate_1_M_interval": _iv(rep["M_interval"]) if rep else "", "replicate_1_o_marginal": rep.get("o_marginal"), "replicate_1_psi": rep.get("psi") if rep.get("psi") is not None else ("" if not rep else "undefined"),
                     "replicate_psi_gap": rep.get("psi_gap"), "replicate_rule_forces_C": rep.get("forces_C")})
    return rows


def write_s7(out_dir: Path, ctx7: dict[str, Any]) -> list[str]:
    """The CSV tables and the report section's lines."""
    from vpd_audit.analysis import _md

    out_dir = Path(out_dir)
    L: list[str] = ["## 9. Tier 4: the marginal-matched control, the code-leaning chain, and the code-specific chain on E by reader label", "",
                    "Every reading rule below was fixed before any tier-4 store existed; the labels are the frozen rules' output.", ""]
    can = ctx7.get("canaries") or {}
    if ctx7.get("tier_4_present"):
        L += ["Canaries (curve 1's union and its plain control at rung 2, draw 0, rerun in the marginal store), bitwise against their first run on kl_mean, mask_fp, sigma, the source hash, and the applied-mask digest: "
              + ("; ".join(f"{k}: {v['n_canaries']} of {v['n_canaries']} equal (" + ", ".join(f"{c['cell'].split('/', 2)[-1]} in {c['store']} against {c['against']}" for c in v["checks"]) + ")" for k, v in can.items()) or "none present in these stores")
              + ". The references of every tier-4 store are in section 0's assert with every other store's.", ""]
        if ctx7.get("two_path"):
            L += ["Two-path recompute of the conditional damage on the tier-4 hard-zero cells: " + "; ".join(f"{k}: {v['n_cells']} cells, {v['n_checks']} checks, max ratio {v['max_ratio']:.4f}, {'pass' if v['pass'] else 'FAIL'}" for k, v in ctx7["two_path"].items()), ""]
    mg = ctx7.get("marginal")
    if mg is None:
        L += ["### 9.1 The marginal-matched control: no marginal cell in these stores", ""]
    else:
        L += ["### 9.1 The marginal-matched control", "",
              f"Asserted before reading: {mg['sets_assert']['n_marginal_cells']} marginal cells and {mg['sets_assert']['n_union_and_plain_cells']} union and plain cells equal, by source hash, the sets of the committed label-only pre-read "
              f"({mg['sets_assert']['table']}); P4 on {len(mg['p4'])} tier-4 chains; the canaries and references in section 0. Overlap constants from {mg['overlap_table']} (overlap_mass_pooled); a rung is decisive at "
              f"o_M at most {s7.DECISIVE_MAX_OVERLAP:.4f}. One resample of E's texts serves the three curves and every rung of every family.", ""]
        rows, per_draw, split_rows, read_rows = [], [], [], []
        for key, entry in mg["families"].items():
            if not entry.get("available"):
                read_rows.append({"family": key, "role": entry["role"], "reading": "not available", "decisive_rungs": "", "m": "", "rungs_missing": ", ".join(entry["rungs_missing"])})
                continue
            res = entry["result"]
            rows += _closure_rows(key, entry)
            read_rows.append({"family": key, "role": entry["role"], "reading": res["reading"], "decisive_rungs": ", ".join(res["decisive"]), "m": res["m"], "decisive_by_the_rule_alone": ", ".join(entry["decisive_by_the_rule"]),
                              "strong_form_of_A": res.get("strong_form_of_A", ""), "guard_fired_at": ", ".join(res["guard"]["rungs"]) if res.get("guard") else "", "rungs_missing": ", ".join(entry["rungs_missing"])})
            for r in entry["rungs"]:
                v = res["per_rung"][r]
                for k in range(v["n_draws"]):
                    per_draw.append({"family": key, "rung": r, "draw": k, "U": v["per_draw"]["U"][k], "P": v["per_draw"]["P"][k], "M": v["per_draw"]["M"][k],
                                     "M_replicate_1": (v["replicate_1"]["per_draw_M"][k] if v.get("replicate_1") else None)})
            for lab, s in (entry.get("by_reader_label") or {}).items():
                for r, v in s["per_rung"].items():
                    split_rows.append({"family": key, "reader_label": lab, "n_texts": s["n"], "rung": r, "m": v["m"], "M_minus_P": v["M_minus_P"]["mean"], "M_minus_P_interval": _iv(v["M_minus_P"]["interval"]),
                                       "U_minus_M": v["U_minus_M"]["mean"], "U_minus_M_interval": _iv(v["U_minus_M"]["interval"]), "U_minus_P": v["denominator"]["mean"], "U_minus_P_interval": _iv(v["denominator"]["interval"]),
                                       "undefined": v["undefined"], "phi": v["phi"] if v["phi"] is not None else "undefined", "psi": v["psi"] if v["psi"] is not None else "undefined", "psi_interval": _iv(v["psi_interval"])})
        tables = {"s7_marginal_readings": pd.DataFrame(read_rows), "s7_marginal_closure": pd.DataFrame(rows), "s7_marginal_per_draw": pd.DataFrame(per_draw),
                  "s7_marginal_rung_1_usage_per_draw": pd.DataFrame(mg["rung_1_usage_per_draw"])}
        if split_rows:
            tables["s7_marginal_by_reader_label"] = pd.DataFrame(split_rows)
        for name, df in tables.items():
            df.to_csv(out_dir / f"{name}.csv", index=False)
        L += ["**The readings** (each a condition at every decisive rung; D before B; C otherwise; no reading without a decisive rung; the soft erase is read at rungs 1 and 2 only; at a decisive rung a denominator U - P whose interval "
              "includes zero or lies below it gives that family no reading, the others being read all the same; the headline takes the primary family's reading, and a primary family with no reading leaves the headline "
              "with none: it does not pass to the secondary family):", "", _md(tables["s7_marginal_readings"]), ""]
        for key, entry in mg["families"].items():
            g = entry.get("result", {}).get("guard") if entry.get("available") else None
            if g:
                L += [f"**`{key}` ({entry['role']}): {NO_READING_GUARD}** (rung {', '.join(g['rungs'])}: {g['message']}). Its U, P, M, the denominator's interval, and the differences M - P and U - M with their intervals are in the table below; "
                      "no ratio is reported where the denominator is not positive, and no condition of A, B, or D was evaluated." + (" **The headline takes no reading; it does not pass to the secondary family.**" if entry["role"] == "primary" else ""), ""]
        show = ["family", "rung", "decisive", "m", "U", "U_interval", "P", "P_interval", "M", "M_interval", "U_minus_P_interval", "M_minus_P", "M_minus_P_interval", "U_minus_M", "U_minus_M_interval", "phi_ov", "phi", "psi", "psi_interval", "rho",
                "M_minus_P_draws_positive", "U_minus_M_draws_positive", "M_minus_U_interval", "M_minus_U_draws_positive", "rung_reading", "replicate_1_psi", "replicate_psi_gap", "replicate_rule_forces_C"]
        L += ["**Per rung** (s7_marginal_closure.csv carries every column; U, P, and M each with its own interval, at the family's corrected level at the decisive rungs and uncorrected at the others, which are descriptives; "
              "s7_marginal_per_draw.csv the per-draw U, P, M). Reading D needs the interval of M - U above zero and M - U positive on at least K - 1 of K draws:", "", _md(tables["s7_marginal_closure"][show]), ""]
        rm, rp = mg["rung_1_matching"], mg.get("real_position_sets") or {}
        L += ["**Beside rung 1's reading, as stated before the launch.** Label-only: the realized marginal control's pooled usage is "
              f"{rm['usage_ratio_marginal_to_union']:.4f} of the eight realized union sets' at rung 1 and its weight norm {rm['norm_ratio_marginal_to_union']:.4f}"
              + (f"; among {rp['n_sets']} sets of eight real pool positions the realized union's usage is at the {rp['mean_usage']['realized_percentile']:.1f}th percentile and its norm at the {rp['mean_norm']['realized_percentile']:.1f}th" if rp else "")
              + ". The note written before the launch: under pure composition this predicts a rung-1 psi near 0.9 and not 1, a small bias toward reading A; rung 2 is the clean test. Per draw (s7_marginal_rung_1_usage_per_draw.csv):", "",
              _md(tables["s7_marginal_rung_1_usage_per_draw"]), ""]
        if split_rows:
            L += ["**By reader label** (descriptive; each label's own resample at the rung's level; the ratio is undefined where the interval of U - P includes zero, the differences are always reported): s7_marginal_by_reader_label.csv.", ""]
        soft = mg["families"].get("soft_erase_r1", {})
        if soft.get("available"):
            L += ["For the soft erase the named cost is sublinear between rungs 1 and 2, so shared members may carry more than their linear share and push psi upward: there reading A is secure, and readings B and C are less so.", ""]
    cl = ctx7.get("code_leaning")
    if cl is None:
        L += ["### 9.2 The code-leaning chain: no code-leaning cell in these stores", ""]
    else:
        pc = cl["positive_control"]
        L += ["### 9.2 The code-leaning chain", "",
              f"Pre-read: existence rule {cl['pre_read']['existence']}; thresholds {cl['pre_read']['thresholds']}; the control's label-only gate {cl['pre_read']['control_gate']}. Asserted before reading: every rung and every control equal, by source hash, "
              f"the pre-read's; P4 on the erase chain and its controls; the readability floor equal to the pre-read's testability table. Strata: {cl['positive_stratum']} and other, never averaged. "
              f"Rungs read: {', '.join(cl['rungs_read'])} (m = {cl['m']}); descriptive, uncorrected: {', '.join(r for r in cl['rungs'] if cl['descriptive'][r]) or 'none'}; {cl['n_control_draws']} control draws per rung.", ""]
        pcr = pd.DataFrame([{"rung": r, "n_members": v["n_members"], "descriptive": v["descriptive"], "judged": v["judged"], "paired_erase_minus_control": v["paired_difference"], "interval_95": _iv(v["interval"]),
                             "above_zero": v["above_zero"]} for r, v in pc["per_rung"].items()])
        pcr.to_csv(out_dir / "s7_code_leaning_positive_control.csv", index=False)
        L += [f"**The chain's own positive control** (on {cl['positive_stratum']}, judged at the rungs the rule reads that have at least 64 members, uncorrected 95 percent): "
              f"**{'pass' if pc['pass'] else ('FAIL at ' + ', '.join(pc['failing_rungs']) if pc['pass'] is False else 'not judged')}**", "", _md(pcr), ""]
        dmg, cond, sur = [], [], []
        for r in cl["rungs"]:
            v = cl["per_rung"][r]
            dmg.append({"rung": r, "n_members": v["n_members"], "descriptive": v["descriptive"], "level_m": v["level_m"], "D_github": v["D_github"]["mean"], "D_github_interval": _iv(v["D_github"]["interval"]),
                        "D_github_control": v["D_github_control"], "D_github_ratio_to_control": v["D_github_ratio_to_control"], "D_other": v["D_other"]["mean"], "D_other_interval": _iv(v["D_other"]["interval"]),
                        "D_other_control": v["D_other_control"], "localization": v["localization"]["statistic"], "localization_interval": _iv(v["localization"]["interval"])})
            for tag in ("github", "other"):
                for k, c in v[f"conditional_{tag}"].items():
                    who, tq = k.split("|")
                    cond.append({"rung": r, "n_members": v["n_members"], "stratum": tag, "set": who, "tau_q": tq, "mean_n_contributing": c["readability"]["mean_n_contributing"],
                                 "mean_clean_prefix_fraction": c["readability"]["mean_clean_prefix_fraction"], "testable": c["testable"], "d_hat": c["d_hat"], "interval": _iv(c["interval"]) if c["interval"] else "", "label": c["label"] or "not testable"})
                for k, t in v[f"touched_{tag}"].items():
                    who, tq = k.split("|")
                    sur.append({"rung": r, "n_members": v["n_members"], "stratum": tag, "set": who, "tau_q": tq, "touched_surplus": t["surplus"]["mean"], "surplus_interval_95": _iv(t["surplus"]["interval"]), "over_removal": t["over_removal"],
                                "surplus_per_over_removal": t["surplus_per_over_removal"]["ratio"], "ratio_interval_95": _iv(t["surplus_per_over_removal"]["interval"])})
        for name, rows_ in (("s7_code_leaning_damage", dmg), ("s7_code_leaning_conditional", cond), ("s7_code_leaning_touched_surplus", sur)):
            pd.DataFrame(rows_).to_csv(out_dir / f"{name}.csv", index=False)
        src = pd.DataFrame(cl["by_source"])
        if len(src):
            src["interval_95"] = src["interval_95"].map(_iv)
        src.to_csv(out_dir / "s7_code_leaning_damage_by_source.csv", index=False)
        rd = cl["readings"]
        cc = rd["conditions_computed"]
        pd.DataFrame([{"label": rd["label"], "read": rd["read"], "R1": rd["R1"], "R1_rungs": ", ".join(rd["R1_rungs"] or []), "R2": rd["R2"], "R3": rd["R3"], "R4_beside": rd["R4"],
                       "conditions_unread": rd["conditions_unread"], "computed_R1_rungs": ", ".join(cc["R1_rungs"]), "computed_R1_conditional_claim": json.dumps(cc["R1_conditional_claim"]), "computed_R2": cc["R2"], "computed_R3": cc["R3"],
                       "computed_R4": cc["R4"], "computed_text": cc["text"],
                       "first_rung_D_other_material": rd["first_rung_D_other_material"], "first_rung_D_github_usable": rd["first_rung_D_github_usable"], "budget_other_tau_q_0.1": cl["budget_other"]["0.1"]["budget_rung"],
                       "budget_other_tau_q_0": cl["budget_other"]["0"]["budget_rung"]}]).to_csv(out_dir / "s7_code_leaning_readings.csv", index=False)
        r4_words = "R4, read beside the others (the labels' code-leaning shows no code-specific effect at these sizes: the localization statistic's interval includes zero or is negative at every rung of at least 64 members)"
        L += [f"**Reading: {rd['label']}**" + (f"; {r4_words}: {rd['R4']}" if rd["read"] else "") + ".", ""]
        if rd["conditions_unread"]:  # the computed conditions are still printed, flagged unread
            L += [f"*Unread* (the chain's positive control did not pass; computed all the same, and not a reading): {cc['text']}; {r4_words}: {cc['R4']}.", ""]
        L += [
              "Unconditional damage per stratum (the erase minus its rung 0; intervals at the chain's corrected level on the rungs read), its control, and the localization statistic (independent resamples of the two strata):", "", _md(pd.DataFrame(dmg)), "",
              "Conditional damage on clean prefixes (the hard-zero rule, the floor judged per stratum; s7_code_leaning_conditional.csv), the group on the other stratum:", "",
              _md(pd.DataFrame([c for c in cond if c["stratum"] == "other" and c["set"] == "group"])), "",
              f"Editing budget on other over the rungs read: tau_q 0.1: {cl['budget_other']['0.1']['budget_rung']}; tau_q 0: {cl['budget_other']['0']['budget_rung']}" + ("" if rd["read"] else " (not read: the positive control)") + ".", "",
              "The touched surplus on other, the over-removal, and the surplus per unit of over-removal, the group and its control (s7_code_leaning_touched_surplus.csv), at tau_q 0.1:", "",
              _md(pd.DataFrame([c for c in sur if c["stratum"] == "other" and c["tau_q"] == "0.1"])), "",
              "Unconditional damage on each source of other, the group and its control, uncorrected 95 percent, each source's own resample (s7_code_leaning_damage_by_source.csv):", "", _md(src), ""]
    cs = ctx7.get("code_specific_by_reader_label")
    L += ["### 9.3 The code-specific chain on E by reader label (an analysis addition, no verdict)", ""]
    if not cs:
        L += ["Not available: no reader labels for this run, or no code-specific chain on E.", ""]
    else:
        for lab, rows_ in cs.items():
            df = pd.DataFrame(rows_)
            for col in ("unconditional_interval", "d_interval"):
                df[col] = df[col].map(lambda v: _iv(v) if isinstance(v, list) else "")
            df.to_csv(out_dir / f"s7_{lab.replace('/', '_')}__by_reader_label.csv", index=False)
            sub = df[(df.tau_q == "0.1") & (df.part == "donor_chain") & (df.rung.isin(["4", "7"]))]
            L += [f"`{lab}`: {len(df)} rows in s7_{lab.replace('/', '_')}__by_reader_label.csv; rungs 4 and 7 of the donor chain at tau_q 0.1:", "",
                  _md(sub[["reader_label", "n_texts", "rung", "n_off", "unconditional", "unconditional_interval", "mean_n_contributing", "testable", "d_hat", "d_interval", "label"]]), ""]
    return L


def analyze_s7(grid_all: Any, grid_base: Any, pre_reads_dir: Path | None, labels: dict[str, Any], resamples: dict, replicates: int, master_seed: int, out_dir: Path, log: Any = print) -> dict[str, Any]:
    """Called by analysis.analyze after the pipeline of tiers 1 to 3. `grid_all` holds every cell; `grid_base` is the grid that
    pipeline read (tier 4 kept out). Writes the s7_* tables and figures, returns the context with the report section's lines."""
    from vpd_audit.analysis import restrict_tiers, two_path_recompute

    ctx7: dict[str, Any] = {"tier_4_present": has_tier_4(grid_all), "canaries": {k: v["canaries"] for k, v in grid_all.reference_assert.items() if isinstance(v, dict) and v.get("canaries")}}
    s7_dir = Path(pre_reads_dir) / S7_PRE_READS_SUBDIR if pre_reads_dir is not None else None
    if ctx7["tier_4_present"]:
        assert s7_dir is not None and (s7_dir / "marginal_overlap_by_rung.csv").is_file(), f"tier-4 stores need the committed tier-4 label-only pre-read ({s7_dir})"
        t4 = restrict_tiers(grid_all, (TIER_4,))
        ctx7["two_path"] = {s: two_path_recompute(sd) for s, sd in t4.sets.items() if sd.eval_set != "donors" and any(c.is_hard_zero for c in sd.cell_objects.values())}
        assert all(v["pass"] for v in ctx7["two_path"].values()), f"the two-path recompute failed on tier 4: {ctx7['two_path']}"
        ctx7["marginal"] = analyze_marginal(grid_all, s7_dir, labels, resamples, replicates, master_seed, log)
        ctx7["code_leaning"] = analyze_code_leaning(grid_all, s7_dir, labels, resamples, replicates, master_seed, log)
    ctx7["code_specific_by_reader_label"] = code_specific_on_E_by_reader_label(grid_base, labels, resamples, replicates, master_seed)
    ctx7["report_lines"] = write_s7(out_dir, ctx7)
    try:
        from vpd_audit.figures_s7 import draw_s7

        ctx7["figures"] = draw_s7(out_dir, ctx7)
    except Exception as e:  # noqa: BLE001
        ctx7["figures"] = {"error": f"{type(e).__name__}: {e}"}
        log(f"[analyze s7] figures failed: {ctx7['figures']['error']}")
    return ctx7


def summary_of(ctx7: dict[str, Any]) -> dict[str, Any]:
    mg, cl = ctx7.get("marginal"), ctx7.get("code_leaning")
    return {"tier_4_present": ctx7["tier_4_present"],
            "marginal": {k: {"reading": v["result"]["reading"], "decisive": v["result"]["decisive"], "m": v["result"]["m"], "strong_form_of_A": v["result"].get("strong_form_of_A"),
                             "guard_fired_at": v["result"]["guard"]["rungs"] if v["result"].get("guard") else None} if v.get("available") else {"reading": "not available"}
                         for k, v in mg["families"].items()} if mg else None,
            "headline_reading": (mg["families"]["union_r0"]["result"]["reading"] if mg and mg["families"].get("union_r0", {}).get("available") else None),  # the primary family's, never another's
            "code_leaning": {"positive_control": cl["positive_control"]["pass"], "reading": cl["readings"]["label"], "R4": cl["readings"]["R4"], "rungs_read": cl["rungs_read"]} if cl else None,
            "code_specific_by_reader_label": sorted(ctx7["code_specific_by_reader_label"]) if ctx7.get("code_specific_by_reader_label") else None, "figures": ctx7.get("figures")}
