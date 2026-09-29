"""The analysis figures, drawn from the analysis context: PNGs with their data beside them as
CSV. 1. Aggregation: n_on on a log axis with rung labels, the mean divergence with corrected intervals, the control
dashed, the reference lines labelled, the pre-reads' overlap annotated at each rung, an excess panel, one figure per
background. 2. Editing: n_off against d_hat with intervals for the hard-zero verdict chains and their controls in one
panel with X drawn, the unconditional damage in a second panel, the clean-prefix fraction on a third; non-testable
rungs hollow. 3. Switched mass: decile means of the excess for the union and its control with the slope lines, curves 1
and 2 at full size and every other configuration in a second file. 4. The never-named chain: D(n) against n on log
axes with the two prediction lines, the alive control, the draw spread, the strict cell as a point at its own n, and
a ratio panel."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from vpd_audit import stats as st


def _plt():
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    return plt


def _marker(rung: str) -> str:
    return "o" if st.donor_count_order(rung)[0] == 0 else ("s" if st.donor_count_order(rung)[0] == 1 else "^")


def figure_aggregation(out_dir: Path, ctx: dict[str, Any], grid: Any, background: str) -> dict[str, Any] | None:
    plt = _plt()
    k = "/k0" if background == "uniform" else ""
    lab = f"union/E/D_unif/tau0.1/{background}/excl{k}/ctl-none"
    if lab not in ctx["union"]:
        return None
    entry = ctx["union"][lab]
    ctl = ctx["union"].get(f"union/E/D_unif/tau0.1/{background}/excl{k}/ctl-plain")
    sd = grid.sets["E"]
    run = grid.run
    overlap = ctx.get("overlap_by_rung", {}) if background == "r0" else {}
    refs = {}
    for name, key in (("unmasked", f"{run}/E/ref/unmasked"), ("importances-as-masks", f"{run}/E/ref/importances"), ("rounded 0.1", f"{run}/E/ref/rounded_0.1")):
        if key in sd.cell_objects:
            refs[name] = float(sd.vector(key, "kl_mean").mean())
    stoch = [f"{run}/E/ref/stochastic/k{i}" for i in range(8) if f"{run}/E/ref/stochastic/k{i}" in sd.cell_objects]
    if stoch:
        refs["stochastic (mean over draws)"] = float(np.mean([sd.vector(n, "kl_mean").mean() for n in stoch]))
    fig, axes = plt.subplots(2, 1, figsize=(10, 10), sharex=True)
    rows = []
    for e, style, name, color in ((entry, "-", "union", "C0"), (ctl, "--", "matched-random control", "C1")):
        if e is None:
            continue
        r = e["result"]
        xs = [r["per_rung"][rg]["n_on"] for rg in r["rungs"]]
        ys = [r["per_rung"][rg]["mean_kl"] for rg in r["rungs"]]
        ex = [r["per_rung"][rg]["e_hat"] for rg in r["rungs"]]
        hw = [r["per_rung"][rg]["half_width"] for rg in r["rungs"]]
        axes[0].errorbar(xs, ys, yerr=hw, fmt=style, color=color, label=name, capsize=3)
        axes[1].errorbar(xs, ex, yerr=hw, fmt=style, color=color, label=name, capsize=3)
        for rg, x, y in zip(r["rungs"], xs, ys):
            axes[0].plot([x], [y], marker=_marker(rg), color=color)
            if name == "union":
                text = rg + (f"\n{overlap[rg]:.2f}" if rg in overlap else "")
                axes[0].annotate(text, (x, y), textcoords="offset points", xytext=(4, 4), fontsize=7)
        for rg, x, y, ee, h in zip(r["rungs"], xs, ys, ex, hw):
            rows.append({"family": name, "rung": rg, "n_on": x, "mean_kl": y, "excess": ee, "half_width": h, "overlap": overlap.get(rg, float("nan"))})
    ref_styles = {"unmasked": (":", "gray"), "importances-as-masks": ("-.", "gray"), "rounded 0.1": ((0, (1, 1)), "black"), "stochastic (mean over draws)": ((0, (3, 1, 1, 1)), "black")}
    for name, v in refs.items():
        ls, color = ref_styles.get(name, (":", "gray"))
        axes[0].axhline(v, ls=ls, lw=1, color=color, label=f"{name} ({v:.3f})")
    axes[1].axhline(0, color="black", lw=0.8)
    axes[1].axhline(st.X_MATERIAL, color="red", lw=0.8, ls=":", label="X = 0.05")
    axes[0].set_xscale("log"); axes[0].set_ylabel("mean divergence (nats)"); axes[1].set_ylabel("excess over rung 0 (nats)"); axes[1].set_xlabel("n_on (mean over draws)")
    axes[0].set_title(f"Aggregation: the union under {background}, tau = 0.1, run {run}", fontsize=11)
    axes[0].legend(fontsize=7, loc="best"); axes[1].legend(fontsize=7)
    fig.text(0.5, 0.005, "circles: position rungs; squares: sequence rungs; the number under a union rung label is the pre-reads' union-against-control overlap", ha="center", fontsize=8)
    fig.tight_layout(rect=(0, 0.02, 1, 1))
    p = out_dir / f"fig1_aggregation_{background}.png"
    fig.savefig(p, dpi=120)
    plt.close(fig)
    pd.DataFrame(rows).to_csv(p.with_suffix(".csv"), index=False)
    return {"png": p.name, "rows": len(rows)}


def figure_editing(out_dir: Path, ctx: dict[str, Any]) -> dict[str, Any] | None:
    plt = _plt()
    wanted = [("hard_zero/E_lab/D_code/tau0.1/ones/incl/ctl-none", "other", "curve 3"), ("code_specific_hard/E_lab/D_code/tau0.1/ones/incl/ctl-none", "other", "curve 4"),
              ("hard_zero/E/D_unif/tau0.1/ones/incl/ctl-none", "all", "curve 5"), ("hard_zero/E_lab/D_code/tau0.1/ones/incl/ctl-plain", "other", "curve 3 control"),
              ("code_specific_hard/E_lab/D_code/tau0.1/ones/incl/ctl-complement", "other", "curve 4 control"), ("hard_zero/E/D_unif/tau0.1/ones/incl/ctl-plain", "all", "curve 5 control")]
    present = [(lab, g, t) for lab, g, t in wanted if lab in ctx["hard_zero"]]
    if not present:
        return None
    fig, axes = plt.subplots(3, 1, figsize=(10, 12), sharex=True)
    rows = []
    for i, (lab, g, title) in enumerate(present):
        hz = ctx["hard_zero"][lab]
        stratum = g if g in hz["by_tau_q"]["0.1"] else "all"
        for part, res in hz["by_tau_q"]["0.1"][stratum].items():
            xs, ys, hw, clean, testable, unc = [], [], [], [], [], []
            for r in res["rungs"]:
                p = res["per_rung"][r]
                xs.append(p["n_off"]); testable.append(p["testable"]); clean.append(p["readability"]["mean_clean_prefix_fraction"]); unc.append(hz["unconditional"][stratum][r])
                ys.append(p["result"]["d_hat"] if p["result"] else np.nan); hw.append(p["result"]["half_width"] if p["result"] else 0.0)
                rows.append({"chain": title, "part": part, "rung": r, "n_off": xs[-1], "d_hat": ys[-1], "half_width": hw[-1], "clean_prefix_fraction": clean[-1], "testable": testable[-1], "unconditional": unc[-1]})
            color = f"C{i}"
            ls = "-" if "control" not in title else "--"
            label = f"{title} ({part}, {stratum})"
            axes[0].errorbar(xs, ys, yerr=hw, fmt=ls, color=color, capsize=3, label=label)
            for x, y, t in zip(xs, ys, testable):
                axes[0].plot([x], [y], marker="o", mfc=color if t else "white", mec=color)
            axes[1].plot(xs, unc, ls=ls, marker=".", color=color, label=label)
            axes[2].plot(xs, clean, ls=ls, marker=".", color=color, label=label)
    axes[0].axhline(st.X_MATERIAL, color="red", lw=0.8, ls=":", label="X = 0.05")
    axes[0].set_ylabel("conditional damage d_hat at tau_q = 0.1 (nats)"); axes[0].set_title("Editing: the hard-zero verdict chains and their controls (hollow: not testable with these donors)")
    axes[1].set_ylabel("unconditional damage (nats)"); axes[1].set_yscale("symlog", linthresh=0.05)
    axes[2].set_ylabel("clean-prefix fraction at tau_q = 0.1"); axes[2].set_xlabel("n_off (mean over draws)"); axes[2].set_xscale("log")
    axes[0].legend(fontsize=7)
    fig.tight_layout()
    p = out_dir / "fig2_editing.png"
    fig.savefig(p, dpi=120)
    plt.close(fig)
    pd.DataFrame(rows).to_csv(p.with_suffix(".csv"), index=False)
    return {"png": p.name, "rows": len(rows)}


def _switched_mass_panel(ax: Any, lab: str, item: dict[str, Any], rows: list[dict[str, Any]]) -> None:
    # the union's own decile means always, the control's when it is present (recorded deviation)
    series = [("union", "C0", [(((b["edge_low"] + b["edge_high"]) / 2 if b["bin"] < 10 else b["edge_low"] * 1.05), b["mean_excess"]) for b in item.get("union_bins", []) if np.isfinite(b["mean_excess"])])]
    if isinstance(item["bins"], list):
        series.append(("control", "C1", [(((b["edge_low"] + b["edge_high"]) / 2 if b["bin"] < 10 else b["edge_low"] * 1.05), b["control_mean_excess"]) for b in item["bins"] if np.isfinite(b.get("control_mean_excess", float("nan")))]))
    for fam, color, pts in series:
        if pts:
            xs, ys = zip(*pts)
            ax.plot(xs, ys, marker="o", color=color, label=f"{fam} (decile means)")
            for x, y in pts:
                rows.append({"chain": lab, "family": fam, "sigma_mid": x, "mean_excess": y})
    s = item["slope_union"]
    xx = np.linspace(item["edges"][0], item["edges"][-1], 50)
    ax.plot(xx, s["intercept"] + s["slope"] * xx, color="C0", ls=":", label=f"union slope {s['slope']:.2e}")
    if "slope_control" in item:
        sc = item["slope_control"]
        ax.plot(xx, sc["intercept"] + sc["slope"] * xx, color="C1", ls=":", label=f"control slope {sc['slope']:.2e}")
    ax.set_title(lab, fontsize=8); ax.set_xlabel("switched mass sigma_b"); ax.set_ylabel("excess (nats)"); ax.legend(fontsize=7)


def figure_switched_mass(out_dir: Path, ctx: dict[str, Any]) -> dict[str, Any] | None:
    plt = _plt()
    dec = ctx["descriptives"].get("deciles", {})
    if not dec:
        return None
    main_labs = [lab for lab in ("union/E/D_unif/tau0.1/r0/excl/ctl-none", "union/E/D_unif/tau0.1/uniform/excl/k0/ctl-none") if lab in dec]
    rest = [lab for lab in dec if lab not in main_labs]
    rows: list[dict[str, Any]] = []
    out = {}
    if main_labs:
        fig, axes = plt.subplots(1, len(main_labs), figsize=(7 * len(main_labs), 5.5), squeeze=False)
        for ax, lab in zip(axes[0], main_labs):
            _switched_mass_panel(ax, lab, dec[lab], rows)
        fig.suptitle("Switched mass: curves 1 and 2, decile means of the excess with the slope lines")
        fig.tight_layout()
        p = out_dir / "fig3_switched_mass.png"
        fig.savefig(p, dpi=120)
        plt.close(fig)
        out["png"] = p.name
    if rest:
        ncol = 3
        nrow = (len(rest) + ncol - 1) // ncol
        fig, axes = plt.subplots(nrow, ncol, figsize=(6 * ncol, 4.5 * nrow), squeeze=False)
        for ax, lab in zip(axes.ravel(), rest):
            _switched_mass_panel(ax, lab, dec[lab], rows)
        for ax in axes.ravel()[len(rest):]:
            ax.axis("off")
        fig.suptitle("Switched mass: the other union configurations")
        fig.tight_layout()
        p2 = out_dir / "fig3b_switched_mass_other.png"
        fig.savefig(p2, dpi=110)
        plt.close(fig)
        out["png_other"] = p2.name
    pd.DataFrame(rows).to_csv(out_dir / "fig3_switched_mass.csv", index=False)
    out["rows"] = len(rows)
    return out


def figure_never_named(out_dir: Path, ctx: dict[str, Any]) -> dict[str, Any] | None:
    plt = _plt()
    nn = ctx["descriptives"].get("never_named")
    if not nn:
        return None
    df = pd.DataFrame(nn["rungs"])
    fig, axes = plt.subplots(2, 1, figsize=(9, 9), sharex=True)
    ax = axes[0]
    ax.errorbar(df["n_erased"], df["D_mean"], yerr=df["draw_spread_sd"].fillna(0), fmt="o-", color="C0", capsize=3, label="never-named chain (draw spread as bars)")
    ax.plot(df["n_erased"], df["linear_prediction"], ls="--", color="gray", label="linear 1.29 n / 28946")
    ax.plot(df["n_erased"], df["quadratic_prediction"], ls=":", color="gray", label="quadratic 1.29 (n / 28946)^2")
    if "alive_control_mean" in df.columns:
        ax.plot(df["n_erased"], df["alive_control_mean"], "s--", color="C1", label="alive control at matched count")
    if nn["whole_set"]["n"]:
        ax.plot([nn["whole_set"]["n"]], [nn["whole_set"]["D"]], marker="*", color="C0", ms=12, ls="none", label="whole set")
    strict = next((hz["one_cell_rung_8"] for hz in ctx["hard_zero"].values() if hz["chain"].family == "never_named_hard" and hz["chain"].tau == 0.0 and "one_cell_rung_8" in hz), None)
    if strict is not None:
        ax.plot([strict["n_erased"]], [strict["unconditional"]], marker="D", color="C2", ms=8, ls="none", label=f"strict cell (tau = 0), n = {strict['n_erased']:.0f}")
    ax.set_xscale("log"); ax.set_yscale("log"); ax.set_ylabel("mean damage D(n) (nats), log"); ax.set_title("The never-named chain"); ax.legend(fontsize=7)
    ax2 = axes[1]
    if "ratio_to_alive_control" in df.columns:
        ax2.plot(df["n_erased"], df["ratio_to_alive_control"], "o-", color="C3", label="D(n) / alive control at matched count")
    with np.errstate(divide="ignore", invalid="ignore"):
        ax2.plot(df["n_erased"], df["D_mean"] / df["linear_prediction"], "s--", color="gray", label="D(n) / linear prediction")
    ax2.axhline(1.0, color="black", lw=0.8)
    ax2.set_xscale("log"); ax2.set_xlabel("n erased"); ax2.set_ylabel("ratio"); ax2.legend(fontsize=7)
    fig.tight_layout()
    p = out_dir / "fig4_never_named.png"
    fig.savefig(p, dpi=120)
    plt.close(fig)
    df.drop(columns=["D_per_draw"]).to_csv(p.with_suffix(".csv"), index=False)
    return {"png": p.name, "rows": len(df)}


def figure_level(out_dir: Path, ctx: dict[str, Any]) -> dict[str, Any] | None:
    """The level cells: the mean divergence against s along the two straight paths (the never-named set at its
    labels and at 1), the corners as the existing cells, the soft-erase curve's points at their own switched fraction."""
    plt = _plt()
    lv = ctx["descriptives"].get("level")
    if not lv:
        return None
    df = pd.DataFrame(lv["rows"])
    fig, ax = plt.subplots(figsize=(8, 5.5))
    for at, color, name in (("labels", "C0", "never-named set at its labels (importances -> union rung 8)"), ("one", "C1", "never-named set at 1 (soft-erase rung 8 -> unmasked)")):
        sub = df[df["never_named_at"] == at].sort_values("s")
        ax.errorbar(sub["s"], sub["mean_kl"], yerr=sub["se"], fmt="o-", color=color, capsize=3, label=name)
        for _, r in sub.iterrows():
            if r["corner"]:
                ax.plot([r["s"]], [r["mean_kl"]], marker="s", ms=9, mfc="white", mec=color)
    pts = pd.DataFrame(lv["soft_erase_points"])
    if len(pts):
        ax.plot(pts["s_equivalent"], pts["mean_kl"], marker="^", ls="none", color="C2", label="soft-erase chain at its own switched fraction (s = 1 - sigma_j / sigma_8)")
        for _, r in pts.iterrows():
            ax.annotate(str(r["rung"]), (r["s_equivalent"], r["mean_kl"]), textcoords="offset points", xytext=(3, 3), fontsize=7)
    ax.set_xlabel("level s of the alive set: m = s + (1 - s) g"); ax.set_ylabel("mean divergence (nats)"); ax.set_title("The level cells and their corners (squares)"); ax.legend(fontsize=7)
    fig.tight_layout()
    p = out_dir / "fig5_level_cells.png"
    fig.savefig(p, dpi=120)
    plt.close(fig)
    df.to_csv(p.with_suffix(".csv"), index=False)
    return {"png": p.name, "rows": len(df)}


def figure_ranked(out_dir: Path, ctx: dict[str, Any]) -> dict[str, Any] | None:
    """The ranked never-named pair: the ranked pair's D(n) against n beside the random chain's, with the draw spread of the
    random chain and the two prediction lines, both keys, both ends."""
    plt = _plt()
    rk = ctx["descriptives"].get("ranked")
    nn = ctx["descriptives"].get("never_named")
    if not rk:
        return None
    df = pd.DataFrame(rk["rows"])
    fig, ax = plt.subplots(figsize=(9, 6))
    styles = {("weight_norm", "top"): ("C0", "-", "o"), ("weight_norm", "bottom"): ("C0", "--", "o"), ("positive_count", "top"): ("C3", "-", "^"), ("positive_count", "bottom"): ("C3", "--", "^")}
    for (key, end), (color, ls, mk) in styles.items():
        sub = df[(df["key"] == key) & (df["end"] == end)].sort_values("n_erased")
        if len(sub):
            ax.errorbar(sub["n_erased"], sub["D_mean"], yerr=sub["se"], fmt=mk + ls, color=color, capsize=2, label=f"{key}, {end}-n")
    if nn:
        rd = pd.DataFrame(nn["rungs"])
        ax.errorbar(rd["n_erased"], rd["D_mean"], yerr=rd["draw_spread_sd"].fillna(0), fmt="s:", color="gray", capsize=3, label="random chain (draw spread as bars)")
        ax.plot(rd["n_erased"], rd["linear_prediction"], ls="--", color="lightgray", label="linear 1.29 n / 28946")
        ax.plot(rd["n_erased"], rd["quadratic_prediction"], ls=":", color="lightgray", label="quadratic 1.29 (n / 28946)^2")
        if nn["whole_set"]["n"]:
            ax.plot([nn["whole_set"]["n"]], [nn["whole_set"]["D"]], marker="*", color="gray", ms=12, ls="none", label="whole set")
    ax.set_xscale("log"); ax.set_yscale("log"); ax.set_xlabel("n erased"); ax.set_ylabel("mean damage D(n) (nats), log"); ax.set_title("The ranked never-named pair beside the random chain"); ax.legend(fontsize=7)
    fig.tight_layout()
    p = out_dir / "fig6_ranked_pair.png"
    fig.savefig(p, dpi=120)
    plt.close(fig)
    df.to_csv(p.with_suffix(".csv"), index=False)
    return {"png": p.name, "rows": len(df)}


def draw_all(out_dir: Path, ctx: dict[str, Any], grid: Any) -> dict[str, Any]:
    out = {}
    for bg in ("r0", "uniform"):
        out[f"aggregation_{bg}"] = figure_aggregation(out_dir, ctx, grid, bg)
    out["editing"] = figure_editing(out_dir, ctx)
    out["switched_mass"] = figure_switched_mass(out_dir, ctx)
    out["never_named"] = figure_never_named(out_dir, ctx)
    out["level"] = figure_level(out_dir, ctx)
    out["ranked"] = figure_ranked(out_dir, ctx)
    return out
