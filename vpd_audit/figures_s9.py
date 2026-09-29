"""The figures for the forum post: presentation only, outside the freeze. Each figure
reads committed tables and nothing else (no store, no array, no pull), writes a PNG at 2x and the CSV of every number it draws
beside it, and labels everything in words a reader outside the project knows. Sources, all under results/:

- Figure 1: the merge curve on E. grid/analysis/main/union_E_D_unif_tau0.1_r0_excl_ctl-none.csv and ..._ctl-plain.csv (rungs 1
  to 4: mean_kl, half_width, fraction_seq_above_X), their __descriptive_rungs.csv twins (16 and 32 tokens), level_cells.csv (the
  two reference lines), acceptance/conditions_main_bf16.csv (the size of E for the axis label).
- Figure 2: the ruler. grid/analysis/main/s9b/s9_yardstick_ratios.csv (own labels, the two merges, the self-merge, the
  never-named removal, Pythia-70M), s9_yardstick.csv (Pythia-160M), level_cells.csv (the full model), acceptance/
  conditions_main_bf16.csv (the training-time random masks and everything off), the registered line X, and the paper's attack
  values, which are quoted from its table and reproduced by nobody here (PAPER_ATTACK_KL).
- Figure 4: the code-leaning edit. grid/analysis/main/fig8_code_leaning.csv, s7_code_leaning_conditional.csv (the guarantee's
  coverage), s7_code_leaning_damage.csv and s7_code_leaning_damage_by_source.csv (the damage by source at 256 pieces).
- Figure 5: the matched random sets. grid/analysis/main/fig7_marginal_control.csv (U, P, M, M_replicate_1), 1 to 64 tokens.
- Figure 6: the examples of predictions shifting. grid/analysis/main/s9b/s9_examples.csv, the five rows shown by rule.
- Figure 7: run 2 in two panels. s9b/s9_run2_curves.csv (strata G and P), s9_run2_controls.csv (the same-size random sets).
- Figure 8: the closeness ladder on the code texts. s9b/s9_run6_ladder.csv (source:Github), s9_run6_self_merge_rule.csv (E).

One style across the seven (Okabe-Ito colours, which are safe for colour-blind readers). Every number on a figure comes from a
table through this module's CSV, and every CSV row names its source table and row; nothing is typed by hand except the paper's
quoted values, which say so on the figure. `_save` refuses a figure whose text uses a project word (rung, tau, r0, X, n_on)."""

from __future__ import annotations

import ast
import math
import re
import textwrap
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from vpd_audit import env
from vpd_audit import stats as st
from vpd_audit import stats_s7 as s7
from vpd_audit.constants import SEQ_LEN
from vpd_audit.sources import RUNG_SCHEDULE

ANALYSIS_DIR: Path = env.PROJECT_ROOT / "results" / "grid" / "analysis" / "main"
S9B_DIR: Path = ANALYSIS_DIR / "s9b"
ACCEPTANCE_DIR: Path = env.PROJECT_ROOT / "results" / "acceptance"
OUT_DIR: Path = ANALYSIS_DIR / "s9" / "figures"
DPI = 200  # 2x: matplotlib's figure inch is 100 pixels at 1x

# The paper's table `tab:vpd-pgd-ce` ("KL divergence to target model" under
# adversarial masking, steps 20, 40, 80, 160): quoted, and reproduced by nobody here. The only numbers in this module that are
# typed rather than read from a table of ours; the figure labels them "as reported, not reproduced by us".
PAPER_ATTACK_KL: dict[int, float] = {20: 0.8280, 40: 1.3539, 80: 3.8381, 160: 25.2560}
PAPER_KIND = "as reported by the paper, not reproduced by us"
MEASURED_KIND = "measured by us"
REGISTERED_KIND = "the line fixed in advance"

# Okabe-Ito
BLUE, ORANGE, GREEN, VERMILLION, SKY, PURPLE, YELLOW, BLACK, GRAY = "#0072B2", "#E69F00", "#009E73", "#D55E00", "#56B4E9", "#CC79A7", "#F0E442", "#000000", "#7F7F7F"
STYLE = {"font.size": 9, "axes.titlesize": 10, "axes.labelsize": 9, "legend.fontsize": 8, "xtick.labelsize": 8, "ytick.labelsize": 8, "axes.spines.top": False,
         "axes.spines.right": False, "legend.frameon": False, "figure.dpi": 100, "savefig.dpi": DPI, "axes.titlelocation": "left", "axes.titleweight": "bold"}

SOURCE_WORDS = {"Github": "code (GitHub)", "Pile-CC": "web text (Pile-CC)", "Wikipedia (en)": "Wikipedia", "StackExchange": "StackExchange", "ArXiv": "ArXiv"}
TOKEN_RUNGS = ("1", "2", "2a", "2b", "3")  # 1, 8, 16, 32, 64 donor tokens, through RUNG_SCHEDULE
WHOLE_TEXT_RUNG = "4"
# Words a reader outside the project does not know; `_save` refuses a figure whose text carries one as a whole word.
BANNED_WORDS = re.compile(r"\b(rung|rungs|tau|r0|n_on|X)\b")


def _plt():
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    return plt


def _esc(s: Any) -> str:
    """Text from a table, made safe for matplotlib: a dollar sign would open mathtext."""
    return str(s).replace("$", r"\$")


def _show_token(t: str) -> str:
    """A token as the figure shows it: in quotes, with newlines and tabs written out, nothing else changed."""
    return "'" + str(t).replace("\n", "\\n").replace("\t", "\\t") + "'"


def _interval(s: Any) -> tuple[float, float]:
    """'[+0.5762, +0.7016]' -> (0.5762, 0.7016), the tables' four-decimal interval strings."""
    m = re.fullmatch(r"\s*\[\s*([-+]?[0-9.]+(?:e[-+]?\d+)?)\s*,\s*([-+]?[0-9.]+(?:e[-+]?\d+)?)\s*\]\s*", str(s))
    assert m, f"not an interval: {s!r}"
    return float(m.group(1)), float(m.group(2))


_TOP5 = re.compile(r"""('(?:[^'\\]|\\.)*'|"(?:[^"\\]|\\.)*")\s+([0-9]+\.[0-9]+)""")


def parse_top5(s: str) -> list[tuple[str, float]]:
    """The examples table's 'top5: ...' cells, written as `{token!r} {p:.3f}` joined by '; ': back to (token, probability)."""
    out = [(ast.literal_eval(lit), float(p)) for lit, p in _TOP5.findall(s)]
    assert len(out) == 5, f"expected five entries in {s!r}, parsed {len(out)}"
    return out


def _percent(fraction: float) -> str:
    v = 100.0 * fraction
    return f"{v:.0f}%" if v >= 10 or v == 0 else f"{v:.1f}%"


def _n_texts_of_E(cond: pd.DataFrame) -> int:
    """The size of E from the acceptance table (its n_seq column, equal on every row), for the axis labels' 'mean over N texts'."""
    n = cond["n_seq"].astype(int)
    assert n.nunique() == 1, n.unique()
    return int(n.iloc[0])


def figure_words(fig: Any) -> list[str]:
    """Every string of text on a figure: titles, labels, ticks, legends, annotations."""
    import matplotlib.text

    return [t.get_text() for t in fig.findobj(matplotlib.text.Text) if t.get_text()]


def check_words(fig: Any) -> None:
    bad = [w for w in figure_words(fig) if BANNED_WORDS.search(w)]
    assert not bad, f"project words on the figure: {bad}"


def _save(fig: Any, out_dir: Path, name: str, df: pd.DataFrame) -> dict[str, Any]:
    check_words(fig)
    out_dir.mkdir(parents=True, exist_ok=True)
    png, csv = out_dir / f"{name}.png", out_dir / f"{name}.csv"
    w, h = (float(v) for v in fig.get_size_inches())
    fig.savefig(png, dpi=DPI)
    _plt().close(fig)
    df.to_csv(csv, index=False)
    return {"png": png.name, "csv": csv.name, "rows": int(len(df)), "size_inches": [w, h], "dpi": DPI}


# ----------------------------------------------------------------------------- figure 1: the merge curve


def figure_1_merge_curve(out_dir: Path, analysis_dir: Path = ANALYSIS_DIR, acceptance_dir: Path = ACCEPTANCE_DIR) -> dict[str, Any]:
    """Total divergence against tokens merged (1, 8, 16, 32, 64) and then one whole text as a visibly different kind of donor;
    real explanations against random sets of the same size; reference lines at the full model and the text's own explanation;
    a strip beneath with the share of texts over the line for both curves."""
    plt = _plt()
    stem = "union_E_D_unif_tau0.1_r0_excl"
    curves = {"real explanations": ("ctl-none", BLUE, "o"), "random sets of the same size": ("ctl-plain", ORANGE, "s")}
    level = pd.read_csv(analysis_dir / "level_cells.csv")
    n_texts = _n_texts_of_E(pd.read_csv(acceptance_dir / "conditions_main_bf16.csv"))
    refs = {"the full model, nothing removed": "main/E/ref/unmasked", "the text's own explanation": "main/E/ref/importances"}
    ref_values = {}
    for words, cell in refs.items():
        sel = level[level["cell"] == cell]
        assert len(sel) == 1 and bool(sel["corner"].iloc[0]), cell
        ref_values[words] = float(sel["mean_kl"].iloc[0])
    rows = []
    for words, (ctl, _, _) in curves.items():
        main = pd.read_csv(analysis_dir / f"{stem}_{ctl}.csv", dtype={"rung": str}).set_index("rung")
        desc = pd.read_csv(analysis_dir / f"{stem}_{ctl}__descriptive_rungs.csv", dtype={"rung": str}).set_index("rung")
        for rung in TOKEN_RUNGS + (WHOLE_TEXT_RUNG,):
            unit, count = RUNG_SCHEDULE[rung]
            if rung in main.index:
                r, table, row = main.loc[rung], f"{stem}_{ctl}.csv", rung
            else:
                row = f"{rung} (descriptive)"
                r, table = desc.loc[row], f"{stem}_{ctl}__descriptive_rungs.csv"
            whole = unit == "sequence"
            assert whole or unit == "position"
            rows.append({"series": words, "donor": "one whole text" if whole else f"{count} tokens", "tokens_merged": SEQ_LEN * count if whole else count, "divergence": float(r["mean_kl"]),
                         "rise_over_own_explanation": float(r["excess"]), "interval_half_width": float(r["half_width"]), "share_of_texts_over_the_line": float(r["fraction_seq_above_X"]),
                         "pieces_switched_on_mean": float(r["n_on"]), "source_table": table, "source_row": row})
    for words, v in ref_values.items():
        rows.append({"series": f"reference: {words}", "donor": "none", "tokens_merged": 0, "divergence": v, "rise_over_own_explanation": np.nan, "interval_half_width": np.nan,
                     "share_of_texts_over_the_line": np.nan, "pieces_switched_on_mean": np.nan, "source_table": "level_cells.csv", "source_row": refs[words]})
    df = pd.DataFrame(rows)

    xs = {rung: i for i, rung in enumerate(TOKEN_RUNGS)}
    xs[WHOLE_TEXT_RUNG] = len(TOKEN_RUNGS) + 0.9
    x_of = {(words, RUNG_SCHEDULE[r][1] * (SEQ_LEN if RUNG_SCHEDULE[r][0] == "sequence" else 1)): xs[r] for r in TOKEN_RUNGS + (WHOLE_TEXT_RUNG,) for words in curves}
    with plt.rc_context(STYLE):
        fig, (ax, strip) = plt.subplots(2, 1, figsize=(8.0, 6.4), sharex=True, gridspec_kw={"height_ratios": (3.2, 1.0)})
        ax.axvspan(len(TOKEN_RUNGS) - 0.45, xs[WHOLE_TEXT_RUNG] + 0.6, color="0.93", zorder=0)
        ax.text(xs[WHOLE_TEXT_RUNG], 0.03, f"a different kind of donor:\none whole other text\n(all {SEQ_LEN} tokens)", ha="center", va="bottom", fontsize=7.5, color="0.35", transform=ax.get_xaxis_transform())
        for words, (_, color, marker) in curves.items():
            sub = df[df["series"] == words]
            tok = sub[sub["donor"] != "one whole text"]
            whole = sub[sub["donor"] == "one whole text"]
            x_tok = [x_of[(words, int(t))] for t in tok["tokens_merged"]]
            ax.errorbar(x_tok, tok["divergence"], yerr=tok["interval_half_width"], fmt=marker + "-", color=color, ms=5, capsize=3, label=words)
            x_whole = [x_of[(words, int(t))] for t in whole["tokens_merged"]]
            ax.errorbar(x_whole, whole["divergence"], yerr=whole["interval_half_width"], fmt="D", color=color, ms=7, mfc="white", mew=1.6, capsize=3, ls="none")
            ax.plot([x_tok[-1], x_whole[0]], [tok["divergence"].iloc[-1], whole["divergence"].iloc[0]], ls=":", color=color, lw=1)
            for x, t, y in zip(x_tok + x_whole, list(tok["tokens_merged"]) + list(whole["tokens_merged"]), list(tok["divergence"]) + list(whole["divergence"])):
                if int(t) == 64 or (int(t) == SEQ_LEN and words.startswith("real")):
                    ax.annotate(f"{y:.2f}", (x, y), textcoords="offset points", xytext=(0, 7 if words.startswith("real") else -13), ha="center", fontsize=8, color=color)
                elif int(t) == SEQ_LEN:  # the random whole-text point: to the right, clear of the reference line's label
                    ax.annotate(f"{y:.2f}", (x, y), textcoords="offset points", xytext=(9, -3), ha="left", fontsize=8, color=color)
        for (words, v), ls, x, ha in zip(ref_values.items(), ("-.", ":"), (-0.4, xs[WHOLE_TEXT_RUNG] + 0.6), ("left", "right")):
            ax.axhline(v, color=BLACK, lw=0.8, ls=ls)
            ax.text(x, v, f"{words} ({v:.3f})", fontsize=7.5, va="bottom", ha=ha)
        ax.set_ylabel(f"divergence from the original model\n(nats, mean over {n_texts:,} texts)")
        ax.set_title("Merging what other tokens need into a text's own explanation")
        ax.legend(loc="upper left", bbox_to_anchor=(0.0, 0.93))
        ax.set_ylim(bottom=0)
        width = 0.36
        for j, (words, (_, color, _)) in enumerate(curves.items()):
            sub = df[df["series"] == words]
            x = np.array([x_of[(words, int(t))] for t in sub["tokens_merged"]]) + (j - 0.5) * width
            share = 100.0 * sub["share_of_texts_over_the_line"].to_numpy(float)
            strip.bar(x, share, width=width, color=color, label=words)
            for xi, v in zip(x, share):
                strip.text(xi, v + 2, f"{v:.0f}" if v >= 10 or v == 0 else f"{v:.1f}", ha="center", va="bottom", fontsize=7, color=color)
        strip.set_ylim(0, 118)
        strip.set_ylabel("texts over the line (%)")
        strip.set_xticks([xs[r] for r in TOKEN_RUNGS + (WHOLE_TEXT_RUNG,)])
        strip.set_xticklabels([str(RUNG_SCHEDULE[r][1]) for r in TOKEN_RUNGS] + ["one whole\ntext"])
        strip.set_xlabel("tokens whose explanations were merged in (random positions of other texts)")
        fig.text(0.01, 0.005, f"over the line: more than {st.X_MATERIAL:g} nats above the text's own explanation, the line fixed before the data. Error bars: bootstrap intervals over texts.", fontsize=7, color="0.35")
        fig.tight_layout(rect=(0, 0.02, 1, 1))
        return _save(fig, out_dir, "fig1_merge_curve", df)


# ----------------------------------------------------------------------------- figure 2: the ruler


def _multiple_of_perplexity(k: float) -> str:
    """e^k as a tick label of the second scale: 'x1.35' up to ten thousand, then a power of ten."""
    v = math.exp(k)
    return f"x{v:.3g}" if v < 1e4 else r"$\times 10^{%d}$" % round(math.log10(v))


def figure_2_ruler(out_dir: Path, analysis_dir: Path = ANALYSIS_DIR, s9_dir: Path = S9B_DIR, acceptance_dir: Path = ACCEPTANCE_DIR) -> dict[str, Any]:
    """A horizontal log ruler of the landmarks, each labelled on its own row so that no two labels collide (the smallest value on
    the top row, each label to the right of its stem, so no label crosses another's stem); a second scale in e^k; Pythia-70M and
    Pythia-160M as measured landmarks; the paper's attack values below the ruler as hollow markers, labelled as reported and not
    reproduced."""
    plt = _plt()
    ratios = pd.read_csv(s9_dir / "s9_yardstick_ratios.csv").set_index("quantity")
    yard = pd.read_csv(s9_dir / "s9_yardstick.csv").set_index(["model", "set"])
    level = pd.read_csv(analysis_dir / "level_cells.csv").set_index("cell")
    cond = pd.read_csv(acceptance_dir / "conditions_main_bf16.csv").set_index("condition")
    n_texts = _n_texts_of_E(cond.reset_index())
    assert (ratios["comparison_model"] == "pythia-70m").all()
    # the tables agree where they overlap: the text's own explanation, and the comparison model's divergence
    assert np.isclose(float(ratios.loc["own labels", "divergence_on_E"]), float(level.loc["main/E/ref/importances", "mean_kl"]))
    assert np.isclose(float(ratios.loc["own labels", "divergence_to_the_primary_comparison_model"]), float(yard.loc[("pythia-70m", "E"), "kl_target_to_model"]))
    ours = [  # (words, value, kind, source table, source row, source column)
        ("the full model, nothing removed", float(level.loc["main/E/ref/unmasked", "mean_kl"]), MEASURED_KIND, "level_cells.csv", "main/E/ref/unmasked", "mean_kl"),
        ("the line fixed in advance (the tolerance)", float(st.X_MATERIAL), REGISTERED_KIND, "stats.py", "X_MATERIAL", ""),
        ("the random masks the labels were trained under", float(cond.loc["stochastic", "kl_mean"]), MEASURED_KIND, "acceptance/conditions_main_bf16.csv", "stochastic", "kl_mean"),
        ("the text's own explanation", float(ratios.loc["own labels", "divergence_on_E"]), MEASURED_KIND, "s9_yardstick_ratios.csv", "own labels", "divergence_on_E"),
        ("a different model, Pythia-70M", float(ratios.loc["own labels", "divergence_to_the_primary_comparison_model"]), MEASURED_KIND, "s9_yardstick_ratios.csv", "own labels", "divergence_to_the_primary_comparison_model"),
        ("a different model, Pythia-160M", float(yard.loc[("pythia-160m", "E"), "kl_target_to_model"]), MEASURED_KIND, "s9_yardstick.csv", "pythia-160m, E", "kl_target_to_model"),
        ("64 other tokens' explanations merged in", float(ratios.loc["the 64-token merge", "divergence_on_E"]), MEASURED_KIND, "s9_yardstick_ratios.csv", "the 64-token merge", "divergence_on_E"),
        ("one whole other text merged in", float(ratios.loc["the one-text merge", "divergence_on_E"]), MEASURED_KIND, "s9_yardstick_ratios.csv", "the one-text merge", "divergence_on_E"),
        ("the never-named pieces removed from the full model", float(ratios.loc["the never-named removal", "divergence_on_E"]), MEASURED_KIND, "s9_yardstick_ratios.csv", "the never-named removal", "divergence_on_E"),
        (f"every piece the text's own {SEQ_LEN} tokens name, fully on (the self-merge)", float(ratios.loc["the self-merge", "divergence_on_E"]), MEASURED_KIND, "s9_yardstick_ratios.csv", "the self-merge", "divergence_on_E"),
        ("everything off (every piece removed)", float(cond.loc["zero_all", "kl_mean"]), MEASURED_KIND, "acceptance/conditions_main_bf16.csv", "zero_all", "kl_mean"),
    ]
    rows = [{"landmark": w, "value": v, "kind": k, "source_table": t, "source_row": r, "source_column": c} for w, v, k, t, r, c in ours]
    for steps, v in PAPER_ATTACK_KL.items():
        rows.append({"landmark": f"the paper's optimized attack, {steps} steps", "value": v, "kind": PAPER_KIND, "source_table": "the paper's table tab:vpd-pgd-ce", "source_row": str(steps), "source_column": "KL divergence to target model"})
    df = pd.DataFrame(rows)
    df["multiple_of_perplexity_e_to_the_k"] = np.exp(df["value"])

    with plt.rc_context(STYLE):
        fig, ax = plt.subplots(figsize=(12.0, 7.2))
        lo, hi = 0.006, 1000.0
        ax.set_xscale("log")
        ax.set_xlim(lo, hi)
        mine = df[df["kind"] != PAPER_KIND].sort_values("value").reset_index(drop=True)
        n = len(mine)
        ax.set_ylim(-1.0 - 0.8 * len(PAPER_ATTACK_KL), n + 0.8)
        ax.axhline(0, color=BLACK, lw=1.4, zorder=1)
        for i, r in mine.iterrows():
            v, row = float(r["value"]), n - i  # the smallest value on the top row
            registered = r["kind"] == REGISTERED_KIND
            ax.plot([v, v], [0, row], color="0.75", lw=0.6, zorder=1)
            ax.plot([v], [0], marker="|" if registered else "o", color=GRAY if registered else BLUE, ms=16 if registered else 9, mew=1.8, zorder=3, ls="none")
            ax.text(v * 1.07, row, f"{_esc(r['landmark'])}: {v:.3g} nats", ha="left", va="center", fontsize=8, color=GRAY if registered else BLACK, zorder=4)
        paper = df[df["kind"] == PAPER_KIND].sort_values("value", ascending=False).reset_index(drop=True)
        for i, r in paper.iterrows():  # mirrored below the ruler: the largest value on the row nearest it, each label to the right of its stem
            v, row = float(r["value"]), -1.0 - 0.8 * i
            ax.plot([v, v], [0, row], color="0.75", lw=0.6, zorder=1)
            ax.plot([v], [row], marker="o", ms=9, mfc="white", mec=VERMILLION, mew=1.6, ls="none", zorder=3)
            ax.text(v * 1.07, row, f"the paper's optimized attack, {r['source_row']} steps: {v:.3g} nats, as reported", ha="left", va="center", fontsize=8, color=VERMILLION, zorder=4)
        handles = [plt.Line2D([], [], marker="o", color=BLUE, ls="none", ms=8, label=f"measured by us: mean divergence over {n_texts:,} texts"),
                   plt.Line2D([], [], marker="|", color=GRAY, ls="none", ms=12, mew=1.8, label=f"the line fixed in advance ({st.X_MATERIAL:g} nats)"),
                   plt.Line2D([], [], marker="o", mfc="white", mec=VERMILLION, mew=1.6, ls="none", ms=8, label="quoted from the paper, not reproduced by us")]
        ax.legend(handles=handles, loc="lower left", fontsize=7.5)
        ax.set_yticks([])
        ax.spines["left"].set_visible(False)
        ax.set_xlabel("divergence from the original model (nats, log scale)")
        ticks = [0.01, 0.03, 0.1, 0.3, 1, 3, 10, 30, 100]
        ax.set_xticks(ticks)
        ax.set_xticklabels([f"{t:g}" for t in ticks])
        ax.xaxis.set_minor_formatter(plt.NullFormatter())
        top = ax.twiny()
        top.set_xscale("log")
        top.set_xlim(ax.get_xlim())
        top.set_xticks(ticks)
        top.set_xticklabels([_multiple_of_perplexity(t) for t in ticks])
        top.set_xticks([], minor=True)
        top.spines["right"].set_visible(False)
        top.spines["left"].set_visible(False)
        top.set_xlabel("the same, as a multiple of the original model's perplexity on its own next-token choices (e to the k)")
        fig.suptitle("How big is a nat here? Where the numbers sit between identical and destroyed", x=0.01, ha="left", fontweight="bold", fontsize=10)
        fig.text(0.01, 0.005, "The paper's attack values come from one batch of 128 texts, the batch the attack was fit on, and its masks also move the residual, which our merges hold at zero; we quote them and did not run them.", fontsize=7, color="0.35")
        fig.tight_layout(rect=(0, 0.02, 1, 0.96))
        return _save(fig, out_dir, "fig2_ruler", df)


# ----------------------------------------------------------------------------- figure 4: the code-leaning edit


EDIT_SIZES = ("G16", "G64", "G256", "G1007")  # the four sizes named for the figure; G1862 is descriptive and not drawn
BY_SOURCE_SIZE = "G256"
BY_SOURCE_ORDER = ("Github", "StackExchange", "ArXiv", "Pile-CC", "Wikipedia (en)")


def _plain_log_ticks(axis: Any, ticks: list[float]) -> None:
    axis.set_ticks(ticks)
    axis.set_ticklabels([f"{t:g}" for t in ticks])
    axis.set_minor_formatter(_plt().NullFormatter())


def figure_4_code_edit(out_dir: Path, analysis_dir: Path = ANALYSIS_DIR) -> dict[str, Any]:
    """Left: damage on code against damage on other text as the edit grows, the edit against its twins, the corner a usable edit
    would need to reach shaded and empty, each point annotated with its size and the guarantee's coverage. Right: the damage by
    source at 256 pieces, the edit as bars and its twins as hollow markers."""
    plt = _plt()
    fig8 = pd.read_csv(analysis_dir / "fig8_code_leaning.csv").set_index("rung")
    cond = pd.read_csv(analysis_dir / "s7_code_leaning_conditional.csv")
    dmg = pd.read_csv(analysis_dir / "s7_code_leaning_damage.csv").set_index("rung")
    by_src = pd.read_csv(analysis_dir / "s7_code_leaning_damage_by_source.csv")
    rows = []
    for rung in EDIT_SIZES:
        r = fig8.loc[rung]
        assert not bool(r["descriptive"]), rung
        c = cond[(cond["rung"] == rung) & (cond["stratum"] == "other") & (cond["set"] == "group") & (cond["tau_q"].astype(str) == "0.1")]
        assert len(c) == 1, (rung, len(c))
        rows.append({"panel": "trade-off", "source_table": "fig8_code_leaning.csv; coverage: s7_code_leaning_conditional.csv (other, group, cut-off 0.1)", "source_row": rung, "n_pieces": int(r["n_members"]), "source": "", "damage_on_code": float(r["D_github"]), "damage_on_code_lo": float(r["D_github_low"]), "damage_on_code_hi": float(r["D_github_high"]),
                     "damage_on_other_text": float(r["D_other"]), "damage_on_other_text_lo": float(r["D_other_low"]), "damage_on_other_text_hi": float(r["D_other_high"]),
                     "twins_damage_on_code": float(r["D_github_control"]), "twins_damage_on_other_text": float(r["D_other_control"]), "guarantee_covers_share_of_other_text": float(c["mean_clean_prefix_fraction"].iloc[0]),
                     "damage": np.nan, "damage_lo": np.nan, "damage_hi": np.nan, "twins_damage": np.nan, "twins_damage_lo": np.nan, "twins_damage_hi": np.nan})
    r = dmg.loc[BY_SOURCE_SIZE]
    assert not bool(r["descriptive"]) and np.isclose(float(r["D_github"]), float(fig8.loc[BY_SOURCE_SIZE, "D_github"])) and np.isclose(float(r["D_github_control"]), float(fig8.loc[BY_SOURCE_SIZE, "D_github_control"]))
    lo, hi = _interval(r["D_github_interval"])
    sel = by_src[(by_src["rung"] == BY_SOURCE_SIZE)]
    assert set(sel["source"]) == set(BY_SOURCE_ORDER) - {"Github"} and len(sel) == 8, sel
    for source in BY_SOURCE_ORDER:
        if source == "Github":  # the code texts' row is the damage table's; its twins carry no interval in any committed table
            rows.append({"panel": "by source", "source_table": "s7_code_leaning_damage.csv", "source_row": BY_SOURCE_SIZE, "n_pieces": int(r["n_members"]), "source": SOURCE_WORDS[source], "damage": float(r["D_github"]), "damage_lo": lo, "damage_hi": hi,
                         "twins_damage": float(r["D_github_control"]), "twins_damage_lo": np.nan, "twins_damage_hi": np.nan})
            continue
        g = sel[(sel["source"] == source) & (sel["set"] == "group")]
        t = sel[(sel["source"] == source) & (sel["set"] == "control")]
        assert len(g) == 1 and len(t) == 1 and int(g["n_draws"].iloc[0]) == 1 and int(g["n_members"].iloc[0]) == int(r["n_members"]), source
        glo, ghi = _interval(g["interval_95"].iloc[0])
        tlo, thi = _interval(t["interval_95"].iloc[0])
        rows.append({"panel": "by source", "source_table": "s7_code_leaning_damage_by_source.csv", "source_row": f"{BY_SOURCE_SIZE} | {source}", "n_pieces": int(g["n_members"].iloc[0]), "source": SOURCE_WORDS[source], "damage": float(g["D"].iloc[0]), "damage_lo": glo, "damage_hi": ghi,
                     "twins_damage": float(t["D"].iloc[0]), "twins_damage_lo": tlo, "twins_damage_hi": thi})
    df = pd.DataFrame(rows)

    with plt.rc_context(STYLE):
        fig, (a, b) = plt.subplots(1, 2, figsize=(12.0, 5.2), gridspec_kw={"width_ratios": (1.35, 1.0)})
        t = df[df["panel"] == "trade-off"]
        x, y = t["damage_on_other_text"].to_numpy(float), t["damage_on_code"].to_numpy(float)
        a.set_xscale("log")
        a.set_yscale("log")
        xlim, ylim = (1e-3, 30.0), (5e-3, 8.0)
        a.fill_between([xlim[0], s7.X], s7.D_GITHUB_USABLE, ylim[1], color=GREEN, alpha=0.12, hatch="//", edgecolor=GREEN, lw=0, zorder=0)
        a.text(xlim[0] * 1.25, ylim[1] * 0.75, f"where a usable edit would land:\nat least {s7.D_GITHUB_USABLE:g} on code, under {s7.X:g} elsewhere\n(empty)", fontsize=7.5, color=GREEN, va="top", ha="left")
        a.axvline(s7.X, color=GRAY, lw=0.7, ls=":")
        a.axhline(s7.D_GITHUB_USABLE, color=GRAY, lw=0.7, ls=":")
        a.errorbar(x, y, xerr=[x - t["damage_on_other_text_lo"], t["damage_on_other_text_hi"] - x], yerr=[y - t["damage_on_code_lo"], t["damage_on_code_hi"] - y], fmt="o-", color=BLUE, ms=6, capsize=3, label="the code-leaning edit")
        a.plot(t["twins_damage_on_other_text"], t["twins_damage_on_code"], "s--", color=ORANGE, ms=6, label="its twins: random pieces used as often (mean over draws)")
        for _, r in t.iterrows():
            a.annotate(f"{int(r['n_pieces']):,} pieces\nguarantee covers {_percent(r['guarantee_covers_share_of_other_text'])} of other text", (r["damage_on_other_text"], r["damage_on_code"]), textcoords="offset points", xytext=(9, -4), fontsize=7.5, color=BLUE)
        a.set_xlim(*xlim)
        a.set_ylim(*ylim)
        _plain_log_ticks(a.xaxis, [0.001, 0.01, 0.1, 1, 10])
        _plain_log_ticks(a.yaxis, [0.01, 0.1, 1])
        a.set_xlabel("damage on other text (nats, log scale)")
        a.set_ylabel("damage on code (nats, log scale)")
        a.set_title("Removing the code-leaning pieces: what it costs on code and elsewhere")
        a.legend(loc="lower right")
        s = df[df["panel"] == "by source"].reset_index(drop=True)
        pos = np.arange(len(s))
        b.bar(pos, s["damage"], color=[BLUE if src.startswith("code") else SKY for src in s["source"]], width=0.62, label="the code-leaning edit")
        b.errorbar(pos, s["damage"], yerr=[s["damage"] - s["damage_lo"], s["damage_hi"] - s["damage"]], fmt="none", ecolor=BLACK, capsize=3, lw=0.8)
        has = s["twins_damage_lo"].notna()
        b.errorbar(pos[has], s.loc[has, "twins_damage"], yerr=[s.loc[has, "twins_damage"] - s.loc[has, "twins_damage_lo"], s.loc[has, "twins_damage_hi"] - s.loc[has, "twins_damage"]], fmt="none", ecolor=ORANGE, capsize=3, lw=0.8)
        b.plot(pos, s["twins_damage"], "s", mfc="white", mec=ORANGE, mew=1.6, ms=7, ls="none", label="its twins: random pieces used as often (mean over draws)")
        for p, v in zip(pos, s["damage"]):
            b.text(p, v * 1.25, f"{v:.3g}", ha="center", va="bottom", fontsize=8)
        b.set_yscale("log")
        b.set_ylim(0.01, 1.2)
        _plain_log_ticks(b.yaxis, [0.01, 0.02, 0.05, 0.1, 0.2, 0.5, 1])
        b.set_xticks(pos)
        b.set_xticklabels([_esc(v) for v in s["source"]], rotation=20, ha="right")
        b.axhline(s7.D_GITHUB_USABLE, color=GRAY, lw=0.7, ls=":")
        b.axhline(s7.X, color=GRAY, lw=0.7, ls=":")
        b.text(len(s) - 0.5, s7.D_GITHUB_USABLE, f"{s7.D_GITHUB_USABLE:g}: effective on code", fontsize=7, color=GRAY, ha="right", va="bottom")
        b.text(len(s) - 0.5, s7.X, f"{s7.X:g}: the line fixed in advance", fontsize=7, color=GRAY, ha="right", va="bottom")
        b.set_ylabel(f"damage at {int(s['n_pieces'].iloc[0]):,} pieces (nats, log scale)")
        b.set_title(f"The same edit at {int(s['n_pieces'].iloc[0]):,} pieces, by kind of text")
        b.legend(loc="upper right", fontsize=7.5)
        fig.text(0.01, 0.005, "damage: divergence of the edited full model from the original, mean over the texts of each kind. Error bars: bootstrap intervals over texts (none in any table for the twins on code).", fontsize=7, color="0.35")
        fig.tight_layout(rect=(0, 0.02, 1, 1))
        return _save(fig, out_dir, "fig4_code_edit", df)


# ----------------------------------------------------------------------------- figure 5: the matched random sets


FIG5_SERIES = (("U", "real_explanations", "other texts' explanations merged in", "o-", BLUE), ("M", "matched_random", "random sets of the same kinds of piece, without the real combinations", "^-", GREEN),
               ("P", "random_same_size", "random sets of the same size", "s--", ORANGE))
FIG5_SECOND_DRAW = ("M_replicate_1", "matched_random_second_draw")


def figure_5_matched_sets(out_dir: Path, analysis_dir: Path = ANALYSIS_DIR) -> dict[str, Any]:
    """The matched control's left panel extended to 64 tokens: U, P, M, and M's second draw, from fig7_marginal_control.csv."""
    plt = _plt()
    src = pd.read_csv(analysis_dir / "fig7_marginal_control.csv", dtype={"rung": str})
    assert list(src["rung"]) == list(TOKEN_RUNGS), list(src["rung"])
    assert (src["donor_positions"].to_numpy() == np.array([RUNG_SCHEDULE[r][1] for r in src["rung"]])).all()
    df = pd.DataFrame({"tokens_merged": src["donor_positions"].astype(int), "pieces_switched_on_mean": src["n_on"].astype(float)})
    for col, plain, *_ in FIG5_SERIES + (FIG5_SECOND_DRAW,):
        for suffix in ("", "_low", "_high"):
            df[plain + suffix.replace("_low", "_lo").replace("_high", "_hi")] = src[col + suffix].astype(float)
    df["source_table"] = "fig7_marginal_control.csv"
    df["source_row"] = src["rung"]
    with plt.rc_context(STYLE):
        fig, ax = plt.subplots(figsize=(6.4, 4.4))
        x = df["tokens_merged"].to_numpy(float)
        for _, plain, words, fmt, color in FIG5_SERIES:
            y = df[plain].to_numpy(float)
            ax.errorbar(x, y, yerr=[y - df[f"{plain}_lo"].to_numpy(float), df[f"{plain}_hi"].to_numpy(float) - y], fmt=fmt, color=color, ms=5, capsize=3, label=words)
        second = FIG5_SECOND_DRAW[1]
        rep = df[df[second].notna()]
        if len(rep):
            y = rep[second].to_numpy(float)
            ax.errorbar(rep["tokens_merged"].to_numpy(float) * 1.12, y, yerr=[y - rep[f"{second}_lo"].to_numpy(float), rep[f"{second}_hi"].to_numpy(float) - y], fmt="v", color=GREEN, mfc="white", capsize=3, label="a second draw of the matched sets")
        ax.axhline(0.0, color=BLACK, lw=0.7)
        ax.axhline(st.X_MATERIAL, color=GRAY, lw=0.7, ls=":")
        ax.text(x.min(), st.X_MATERIAL, f"{st.X_MATERIAL:g} nats: the line fixed in advance", fontsize=7, va="bottom", ha="left", color=GRAY)
        ax.set_xscale("log", base=2)
        ax.set_xticks(x)
        ax.set_xticklabels([str(int(v)) for v in x])
        ax.xaxis.set_minor_formatter(plt.NullFormatter())
        ax.set_xlabel("tokens whose explanations were merged in")
        ax.set_ylabel("change in divergence from the text's own explanation (nats)")
        ax.set_title("At small merges, sets built from the same kinds of piece do no harm")
        ax.legend(loc="upper left")
        fig.tight_layout()
        return _save(fig, out_dir, "fig5_matched_random_sets", df)


# ----------------------------------------------------------------------------- figure 6: the examples


EXAMPLE_MODELS = {"merge": (("the original model", "top5: the original model"), ("the text's own explanation", "top5: own labels"), ("one whole other text merged in", "top5: the merge of general donors, 1 text")),
                  "never_named": (("the original model", "top5: the original model"), ("the full model, every piece on", "top5: the full decomposed model with the residual"), ("the never-named pieces removed", "top5: the removal of the never-named pieces"))}
EXAMPLE_WHAT = {"merge": "one whole other text merged in", "never_named": "the never-named pieces removed"}
EXAMPLE_COLORS = (GRAY, BLUE, VERMILLION)


def figure_6_examples(out_dir: Path, s9_dir: Path = S9B_DIR) -> dict[str, Any]:
    """For each of the five positions chosen by rule: the five most likely next tokens and their probabilities under the original
    model, the text's own explanation, and the merge (for the never-named example: the full model and the removal), the
    position's divergence in the legend, and the 48 tokens of context above."""
    plt = _plt()
    ex = pd.read_csv(s9_dir / "s9_examples.csv")
    shown = ex[ex["shown"]].reset_index(drop=True)
    assert len(shown) == 5 and (shown["rank_by_nearness"] == 0).all()
    rows, panels = [], []
    for k, r in shown.iterrows():
        models = EXAMPLE_MODELS[r["example_of"]]
        tops = {words: parse_top5(r[col]) for words, col in models}
        order: list[str] = []
        for words, _ in models:
            for tok, _ in tops[words]:
                if tok not in order:
                    order.append(tok)
        for words, col in models:
            for rank, (tok, p) in enumerate(tops[words]):
                rows.append({"example": k + 1, "example_of": r["example_of"], "percentile": float(r["percentile"]), "text": int(r["seq"]), "position": int(r["position"]), "divergence_at_position": float(r["kl_at_position"]),
                             "real_next_token": r["real_next_token"], "model": words, "rank": rank + 1, "token": tok, "probability": p, "source_table": "s9_examples.csv", "source_column": col})
        panels.append((k + 1, r, models, tops, order))
    df = pd.DataFrame(rows)

    with plt.rc_context(STYLE):
        fig, axes = plt.subplots(5, 1, figsize=(11.0, 17.0))
        width = 0.27
        for ax, (k, r, models, tops, order) in zip(axes, panels):
            pos = {tok: i for i, tok in enumerate(order)}
            for j, ((words, _), color) in enumerate(zip(models, EXAMPLE_COLORS)):
                xs = [pos[tok] + (j - 1) * width for tok, _ in tops[words]]
                ax.bar(xs, [p for _, p in tops[words]], width=width, color=color, label=words)
            ax.set_xticks(range(len(order)))
            ax.set_xticklabels([_esc(_show_token(t)) for t in order], rotation=30, ha="right", fontsize=8, family="monospace")
            ax.set_ylim(0, 1.0)
            ax.set_ylabel("probability of the next token")
            head = (f"Example {k} of {len(panels)}: the {r['percentile']:g}th-percentile position of the per-position divergence under {EXAMPLE_WHAT[r['example_of']]}\n"
                    f"text {int(r['seq'])}, position {int(r['position'])}; real next token {_esc(_show_token(r['real_next_token']))}; the 48 tokens before it:")
            ctx = "\n".join(textwrap.wrap(_esc(str(r["context"]).replace("\n", "\\n").replace("\t", "\\t")), width=150))
            ax.set_title(head + "\n" + ctx, fontsize=7.6, family="monospace", weight="normal", loc="left")
            ax.legend(title=f"divergence at this position: {r['kl_at_position']:.3f} nats", loc="upper right", title_fontsize=8)
        fig.text(0.01, 0.003, "a missing bar: the token is not among that model's five most likely there. Context: the 48 tokens before the prediction, newlines and tabs written out. The positions were chosen by a rule fixed in advance; nobody picked one.", fontsize=7, color="0.35")
        fig.tight_layout(rect=(0, 0.01, 1, 1), h_pad=1.6)
        return _save(fig, out_dir, "fig6_prediction_examples", df)


# ----------------------------------------------------------------------------- figure 7: run 2 in two panels


RUN2_ARMS = (("C", "code donors", VERMILLION, "o"), ("U", "general donors", BLUE, "s"), ("P", "prose donors", GREEN, "^"))
RUN2_STRATA = (("G", "the code texts"), ("P", "the prose texts"))


def figure_7_within_one_kind(out_dir: Path, s9_dir: Path = S9B_DIR) -> dict[str, Any]:
    """Run 2 in two panels, the code texts and the prose texts, each with the three donor arms, the same-size random sets where
    they exist, the 0.05 line, and the own-labels line."""
    plt = _plt()
    curves = pd.read_csv(s9_dir / "s9_run2_curves.csv", dtype={"size": str})
    controls = pd.read_csv(s9_dir / "s9_run2_controls.csv", dtype={"size": str})
    sizes = list(dict.fromkeys(curves["size"]))
    rows = []
    for stratum, stratum_words in RUN2_STRATA:
        for arm, arm_words, _, _ in RUN2_ARMS:
            sub = curves[(curves["stratum"] == stratum) & (curves["arm"] == arm)]
            assert list(sub["size"]) == sizes, (stratum, arm)
            assert sub["flag"].isna().all(), "a pooled flag on a single-source stratum"
            for _, r in sub.iterrows():
                rows.append({"texts": stratum_words, "stratum": stratum, "donors": arm_words, "arm": arm, "series": "real explanations", "merged_in": r["size_words"], "n_texts": int(r["n_texts"]), "n_documents": int(r["n_documents"]),
                             "n_draws": int(r["n_draws"]), "rise": float(r["rise"]), "interval_lo": float(r["interval_documents_lo"]), "interval_hi": float(r["interval_documents_hi"]), "detected": bool(r["detected"]), "material": bool(r["material"]),
                             "pieces_switched_on_mean": float(r["n_on_mean"]), "source_table": "s9_run2_curves.csv", "source_row": r["size"]})
            ctl = controls[(controls["stratum"] == stratum) & (controls["arm"] == arm)]
            for _, c in ctl.iterrows():
                real = sub[sub["size"] == c["size"]]
                assert len(real) == 1 and np.isclose(float(real["rise"].iloc[0]), float(c["real"])), "the control row's arm value is the curve's"
                rows.append({"texts": stratum_words, "stratum": stratum, "donors": arm_words, "arm": arm, "series": "random sets of the same size", "merged_in": c["size_words"], "n_texts": int(real["n_texts"].iloc[0]),
                             "n_documents": int(real["n_documents"].iloc[0]), "n_draws": int(c["n_draws"]), "rise": float(c["random"]), "interval_lo": np.nan, "interval_hi": np.nan, "detected": np.nan, "material": np.nan,
                             "pieces_switched_on_mean": float(c["n_on_random"]), "source_table": "s9_run2_controls.csv", "source_row": c["size"]})
    df = pd.DataFrame(rows)
    xs = {}
    x = 0.0
    for i, s in enumerate(sizes):
        unit = RUNG_SCHEDULE[s][0]
        if i and unit != RUNG_SCHEDULE[sizes[i - 1]][0]:
            x += 0.7
        xs[s] = x
        x += 1.0
    words = dict(zip(curves["size"], curves["size_words"]))

    with plt.rc_context(STYLE):
        fig, axes = plt.subplots(1, 2, figsize=(12.5, 5.0), sharey=True)
        for ax, (stratum, stratum_words) in zip(axes, RUN2_STRATA):
            for arm, arm_words, color, marker in RUN2_ARMS:
                real = df[(df["stratum"] == stratum) & (df["arm"] == arm) & (df["series"] == "real explanations")]
                xr = [xs[s] for s in real["source_row"]]
                y = real["rise"].to_numpy(float)
                ax.errorbar(xr, y, yerr=[y - real["interval_lo"].to_numpy(float), real["interval_hi"].to_numpy(float) - y], fmt=marker + "-", color=color, ms=5, capsize=2.5, label=f"{arm_words}: their explanations merged in")
                rnd = df[(df["stratum"] == stratum) & (df["arm"] == arm) & (df["series"] == "random sets of the same size")]
                if len(rnd):
                    ax.plot([xs[s] for s in rnd["source_row"]], rnd["rise"], marker=marker, mfc="white", mec=color, color=color, ls="--", lw=0.9, ms=5, label=f"random sets of the same size as the {arm_words}' sets")
            ax.axhline(0.0, color=BLACK, lw=0.8, label="the text's own explanation (no rise)")
            ax.axhline(st.X_MATERIAL, color=GRAY, lw=0.8, ls=":", label=f"the line fixed in advance ({st.X_MATERIAL:g} nats)")
            for a, b in zip(sizes, sizes[1:]):
                if RUNG_SCHEDULE[a][0] != RUNG_SCHEDULE[b][0]:
                    ax.axvline((xs[a] + xs[b]) / 2, color="0.85", lw=0.8)
            n_texts, n_docs = df[(df["stratum"] == stratum)][["n_texts", "n_documents"]].iloc[0]
            ax.set_title(f"{stratum_words} ({int(n_texts)} texts of {int(n_docs)} documents)")
            ax.set_xticks([xs[s] for s in sizes])
            ax.set_xticklabels([words[s].replace("the whole pool", "the whole\ndonor pool") for s in sizes], rotation=35, ha="right")
            ax.set_xlabel("what was merged in")
        axes[0].set_ylabel("rise in divergence over the text's own explanation\n(nats, mean over texts; intervals over documents)")
        axes[1].legend(loc="upper left", fontsize=7.2)
        fig.suptitle("Merging within one kind of text: code, general, and prose donors on the code texts and on the prose texts", x=0.01, ha="left", fontweight="bold", fontsize=10)
        fig.text(0.01, 0.005, "what was merged in: the explanations of so many donor tokens (random positions of the donor pool), then of so many whole donor texts, then of the whole donor pool. Dashed, hollow: random sets of as many pieces.", fontsize=7, color="0.35")
        fig.tight_layout(rect=(0, 0.02, 1, 0.97))
        return _save(fig, out_dir, "fig7_within_one_kind", df)


# ----------------------------------------------------------------------------- figure 8: the closeness ladder


LADDER_RUNGS = (("a general partner", "a general text\n(from the general pool)"), ("a partner from the same source, another document", "another code file"), ("the text itself", "the text itself"))
LADDER_STRATUM = "source:Github"


def figure_8_closeness_ladder(out_dir: Path, s9_dir: Path = S9B_DIR) -> dict[str, Any]:
    """The closeness ladder on the code texts as a bar chart with its intervals, and the self-merge on all texts of E beside it,
    with its total divergence and the text's own explanation's beside the rise."""
    plt = _plt()
    ladder = pd.read_csv(s9_dir / "s9_run6_ladder.csv")
    rule = pd.read_csv(s9_dir / "s9_run6_self_merge_rule.csv").set_index("set")
    rows = []
    for rung, words in LADDER_RUNGS:
        r = ladder[(ladder["stratum"] == LADDER_STRATUM) & (ladder["rung"] == rung)]
        assert len(r) == 1 and r["standing"].iloc[0] == "material" and float(r["nonfinite_share"].iloc[0]) == 0.0, rung
        r = r.iloc[0]
        rows.append({"group": "the code texts", "donor": words.replace("\n", " "), "n_texts": int(r["n_texts"]), "n_documents": int(r["n_documents"]), "rise": float(r["mean_rise"]), "interval_lo": float(r["interval_lo"]), "interval_hi": float(r["interval_hi"]),
                     "standing": r["standing"], "pieces_switched_on_mean": float(r["mean_count"]), "own_explanation_divergence": np.nan, "total_divergence": np.nan, "source_table": "s9_run6_ladder.csv", "source_row": f"{LADDER_STRATUM} | {rung}"})
    e = rule.loc["E"]
    assert bool(e["material"]) and np.isclose(float(e["own_labels_kl"]) + float(e["rise"]), float(e["self_merge_kl"]))
    rows.append({"group": "all texts", "donor": "the text itself", "n_texts": int(e["n_texts"]), "n_documents": np.nan, "rise": float(e["rise"]), "interval_lo": float(e["interval_lo"]), "interval_hi": float(e["interval_hi"]),
                 "standing": "material", "pieces_switched_on_mean": float(e["n_on_mean"]), "own_explanation_divergence": float(e["own_labels_kl"]), "total_divergence": float(e["self_merge_kl"]), "source_table": "s9_run6_self_merge_rule.csv", "source_row": "E"})
    df = pd.DataFrame(rows)
    code, everyone = df[df["group"] == "the code texts"], df[df["group"] == "all texts"].iloc[0]

    with plt.rc_context(STYLE):
        fig, ax = plt.subplots(figsize=(6.8, 4.8))
        pos = np.array([0.0, 1.0, 2.0, 3.4])
        colors = [BLUE] * len(code) + [SKY]
        ax.bar(pos, df["rise"], width=0.66, color=colors)
        ax.errorbar(pos, df["rise"], yerr=[df["rise"] - df["interval_lo"], df["interval_hi"] - df["rise"]], fmt="none", ecolor=BLACK, capsize=4, lw=0.9)
        top = float(df["interval_hi"].max())
        for p, (_, r) in zip(pos, df.iterrows()):
            ax.text(p, r["interval_hi"] + 0.02 * top, f"{r['rise']:.2f}", ha="center", va="bottom", fontsize=8.5)
            ax.text(p, 0.02 * top, f"{int(r['n_texts']):,} texts", ha="center", va="bottom", fontsize=7, color="white")
        ax.text(pos[-1], everyone["rise"] * 0.5, f"{everyone['own_explanation_divergence']:.2f} under the\ntext's own\nexplanation,\n{everyone['total_divergence']:.2f} in total", ha="center", va="center", fontsize=7, color="white")
        ax.axvline((pos[-2] + pos[-1]) / 2, color="0.85", lw=0.8)
        ax.set_xticks(pos)
        ax.set_xticklabels([_esc(w) for _, w in LADDER_RUNGS] + [f"the text itself,\non all {int(everyone['n_texts']):,} texts"], fontsize=8)
        ax.set_ylabel("rise in divergence over the text's own explanation\n(nats, mean over texts)")
        ax.set_xlabel("whose explanation was merged into the text's own")
        ax.set_title("The closer the donor, the worse the merge: the code texts")
        ax.set_ylim(0, top * 1.14)
        ax.text(pos[:-1].mean(), top * 1.08, f"the code texts ({int(code['n_texts'].iloc[0])} texts, {int(code['n_documents'].iloc[0])} documents)", ha="center", fontsize=8, color=BLUE)
        ax.text(pos[-1], top * 1.08, f"beside: all {int(everyone['n_texts']):,} texts", ha="center", fontsize=8, color=BLUE)
        fig.text(0.01, 0.005, f"Error bars: bootstrap intervals over documents (over texts for the {int(everyone['n_texts']):,}). Every bar's interval lies above the line fixed in advance ({st.X_MATERIAL:g} nats).", fontsize=7, color="0.35")
        fig.tight_layout(rect=(0, 0.02, 1, 1))
        return _save(fig, out_dir, "fig8_closeness_ladder", df)


# ----------------------------------------------------------------------------- all


def draw_s9(out_dir: Path = OUT_DIR, analysis_dir: Path = ANALYSIS_DIR, s9_dir: Path = S9B_DIR, acceptance_dir: Path = ACCEPTANCE_DIR) -> dict[str, Any]:
    out_dir = Path(out_dir)
    return {"fig1": figure_1_merge_curve(out_dir, analysis_dir, acceptance_dir), "fig2": figure_2_ruler(out_dir, analysis_dir, s9_dir, acceptance_dir), "fig4": figure_4_code_edit(out_dir, analysis_dir),
            "fig5": figure_5_matched_sets(out_dir, analysis_dir), "fig6": figure_6_examples(out_dir, s9_dir), "fig7": figure_7_within_one_kind(out_dir, s9_dir), "fig8": figure_8_closeness_ladder(out_dir, s9_dir)}
