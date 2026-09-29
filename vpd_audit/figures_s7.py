"""The two tier-4 figures, drawn from the analysis context of analysis_s7.py, each with its data
beside it as CSV. 7: the marginal control beside curve 1 and its plain control at the small rungs, with psi and its interval
per rung. 8: the code-leaning trade-off, the damage on GitHub against the damage on other text per rung, the chain and its
usage-matched control."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from vpd_audit import stats_s7 as s7


def _plt():
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    return plt


DONOR_POSITIONS = {"1": 1, "2": 8, "2a": 16, "2b": 32, "3": 64}  # sources.RUNG_SCHEDULE's position run
LEFT_PANEL_RUNGS = ("1", "2", "2a", "2b")  # 1 to 32 donor positions; 64 belongs to the right panel


def figure_marginal(out_dir: Path, mg: dict[str, Any]) -> dict[str, Any] | None:
    """The marginal-control figure. Left: the change in divergence against the donor positions merged in, 1 to 32, on a linear axis, the
    three kinds of set with their intervals, a line at zero and a line at X. Right: the share of the gap the matched sets
    close beyond what shared members give, per number of donor positions, 64 included. Plain words for an outside reader."""
    fam = mg["families"].get("union_r0")
    if not fam or not fam.get("available"):
        return None
    plt = _plt()
    res = fam["result"]
    rows = []
    for r in fam["rungs"]:
        v = res["per_rung"][r]
        rep = v.get("replicate_1") or {}
        rows.append({"rung": r, "donor_positions": DONOR_POSITIONS[r], "n_on": v.get("n_on"), "decisive": v["decisive"], "level_m": v["m"], "U": v["U"], "U_low": v["U_interval"][0], "U_high": v["U_interval"][1],
                     "P": v["P"], "P_low": v["P_interval"][0], "P_high": v["P_interval"][1], "M": v["M"], "M_low": v["M_interval"][0], "M_high": v["M_interval"][1], "M_replicate_1": rep.get("M"),
                     "M_replicate_1_low": rep["M_interval"][0] if rep else None, "M_replicate_1_high": rep["M_interval"][1] if rep else None, "psi": v["psi"],
                     "psi_low": v["psi_interval"][0] if v["psi_interval"] else None, "psi_high": v["psi_interval"][1] if v["psi_interval"] else None, "psi_replicate_1": rep.get("psi"), "reading_of_the_family": res["reading"]})
    df = pd.DataFrame(rows)
    df.to_csv(out_dir / "fig7_marginal_control.csv", index=False)
    fig, (a, b) = plt.subplots(1, 2, figsize=(12.5, 5.6))
    left = df[df["rung"].isin(LEFT_PANEL_RUNGS)]
    x = left["donor_positions"].to_numpy(float)
    for col, lab, fmt, color in (("U", "other inputs' explanations merged in", "o-", "C0"), ("M", "random sets matched to them subcomponent by subcomponent", "^-", "C2"), ("P", "random sets of the same size", "s--", "C1")):
        y = left[col].to_numpy(float)
        a.errorbar(x, y, yerr=[y - left[f"{col}_low"].to_numpy(float), left[f"{col}_high"].to_numpy(float) - y], fmt=fmt, color=color, ms=5, capsize=3, label=lab)
    second = left[left["M_replicate_1"].notna()]
    if len(second):
        y = second["M_replicate_1"].to_numpy(float)
        a.errorbar(second["donor_positions"].to_numpy(float) + 0.6, y, yerr=[y - second["M_replicate_1_low"].to_numpy(float), second["M_replicate_1_high"].to_numpy(float) - y], fmt="v", color="C2", mfc="none", capsize=3,
                   label="a second draw of the matched random sets")
    a.axhline(0.0, color="k", lw=0.7)
    a.axhline(s7.X, color="k", lw=0.7, ls=":")
    a.annotate(f"{s7.X:g} nats", (x.max(), s7.X), fontsize=7, va="bottom", ha="right")
    a.set_xticks(sorted(set(x.tolist())))
    a.set_xlabel("donor positions merged in")
    a.set_ylabel("change in divergence from the text's own explanation (nats)", fontsize=9)
    a.legend(frameon=False, fontsize=8)
    ok = df["psi"].notna()
    xr = df["donor_positions"].to_numpy(float)
    for dec, mfc in ((True, "C3"), (False, "none")):
        sel = (ok & (df["decisive"] == dec)).to_numpy()
        if sel.any():
            y = df.loc[sel, "psi"].to_numpy(float)
            b.errorbar(xr[sel], y, yerr=[y - df.loc[sel, "psi_low"].to_numpy(float), df.loc[sel, "psi_high"].to_numpy(float) - y], fmt="o", color="C3", mfc=mfc, capsize=3,
                       label="where the matched sets share at most a third of the merged explanations" if dec else "where they share more (shown for completeness)")
    if df["psi_replicate_1"].notna().any():
        sel = df["psi_replicate_1"].notna().to_numpy()
        b.plot(xr[sel], df.loc[sel, "psi_replicate_1"].to_numpy(float), "v", color="C2", mfc="none", label="a second draw of the matched random sets")
    for y in (0.0, s7.PSI_A, s7.PSI_B, 1.0):
        b.axhline(y, color="k", lw=0.7, ls=":" if 0 < y < 1 else "-")
    b.set_xscale("log", base=2)
    b.set_xticks(sorted(set(xr.tolist())))
    b.set_xticklabels([str(int(v)) for v in sorted(set(xr.tolist()))])
    b.set_xlabel("donor positions merged in")
    b.set_ylabel("share of the gap the matched sets close,\nbeyond shared members\n(0: the harm needs real combinations;\n1: matched random sets do as much harm)", fontsize=8)
    if b.get_legend_handles_labels()[0]:
        b.legend(frameon=False, fontsize=7)
    else:  # a family whose named-minus-plain gap is not positive at a decisive rung has no share to show
        b.text(0.5, 0.5, "no share to show: merging other inputs' explanations\ndoes not cost more than random sets of the same size here", transform=b.transAxes, ha="center", va="center", fontsize=8)
    fig.tight_layout()
    fig.savefig(out_dir / "fig7_marginal_control.png", dpi=150)
    plt.close(fig)
    return {"file": "fig7_marginal_control.png", "rungs": list(df["rung"]), "left_panel_rungs": list(left["rung"])}


def figure_code_leaning(out_dir: Path, cl: dict[str, Any]) -> dict[str, Any]:
    plt = _plt()
    rows = [{"rung": r, "n_members": v["n_members"], "descriptive": v["descriptive"], "D_github": v["D_github"]["mean"], "D_github_low": v["D_github"]["interval"][0], "D_github_high": v["D_github"]["interval"][1],
             "D_other": v["D_other"]["mean"], "D_other_low": v["D_other"]["interval"][0], "D_other_high": v["D_other"]["interval"][1], "D_github_control": v["D_github_control"], "D_other_control": v["D_other_control"]}
            for r, v in cl["per_rung"].items()]
    df = pd.DataFrame(rows)
    df.to_csv(out_dir / "fig8_code_leaning.csv", index=False)
    fig, ax = plt.subplots(figsize=(6.4, 4.6))
    eps = 1e-4  # the axes are logarithmic; a damage at or below zero is drawn at eps
    gx, gy = np.maximum(df["D_other"].to_numpy(float), eps), np.maximum(df["D_github"].to_numpy(float), eps)
    ax.errorbar(gx, gy, xerr=[np.maximum(gx - np.maximum(df["D_other_low"], eps), 0), np.maximum(np.maximum(df["D_other_high"], eps) - gx, 0)],
                yerr=[np.maximum(gy - np.maximum(df["D_github_low"], eps), 0), np.maximum(np.maximum(df["D_github_high"], eps) - gy, 0)], fmt="o-", color="C0", capsize=2, label="the code-leaning chain")
    ax.plot(np.maximum(df["D_other_control"], eps), np.maximum(df["D_github_control"], eps), "s--", color="0.5", label="usage-matched control (mean over draws)")
    for _, r in df.iterrows():
        ax.annotate(f"{int(r['n_members'])}{'*' if r['descriptive'] else ''}", (max(r["D_other"], eps), max(r["D_github"], eps)), fontsize=7, xytext=(3, 3), textcoords="offset points")
    ax.axvline(s7.X, color="k", lw=0.6, ls=":")
    ax.axhline(s7.D_GITHUB_USABLE, color="k", lw=0.6, ls=":")
    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.set_xlabel(f"unconditional damage on other text (nats); dotted: X = {s7.X}")
    ax.set_ylabel(f"unconditional damage on {cl['positive_stratum']} (nats); dotted: {s7.D_GITHUB_USABLE}")
    ax.set_title("The code-leaning trade-off per rung (members; * descriptive)\nreading: " + cl["readings"]["label"][:100], fontsize=8)
    ax.legend(frameon=False, fontsize=8)
    fig.tight_layout()
    fig.savefig(out_dir / "fig8_code_leaning.png", dpi=150)
    plt.close(fig)
    return {"file": "fig8_code_leaning.png", "rungs": list(df["rung"])}


def draw_s7(out_dir: Path, ctx7: dict[str, Any]) -> dict[str, Any]:
    out: dict[str, Any] = {}
    if ctx7.get("marginal"):
        out["marginal"] = figure_marginal(Path(out_dir), ctx7["marginal"])
    if ctx7.get("code_leaning"):
        out["code_leaning"] = figure_code_leaning(Path(out_dir), ctx7["code_leaning"])
    return out
