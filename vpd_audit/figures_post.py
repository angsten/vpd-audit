"""The post's five figures, each a PNG in results/post/ beside a CSV of exactly the numbers it plots. It reads committed tables and
per-text stores only and never runs the model.

- `aggregation_schematic` and `delete_schematic`: the two schematics, of the aggregation and of the edit (a toy example, no data).
- `aggregation_curve`: the divergence from the original model on E against the number of donor tokens aggregated, for the components the
  donor tokens need, the frequency-matched random components, and uniform random components, with the whole donor text past an axis break.
- `similar_donors`: the same on E_lab's code texts and prose texts, for code, general, and prose donors.
- `code_edit_panels` (the default): the damage of deleting the code-leaning group (256 components and the whole group of 1,007) by kind of
  input text, every bar from the random 200-row panels. Two other variants are drawn on request (`--code-edit`): `code_edit` (on E_lab) and
  `code_edit_arxiv_panel` (E_lab, with the ArXiv bar from its panel, hatched and marked as measured on a different set of texts).

**The drawing** is ported unchanged from the reference designs; each drawing function takes its numbers as arguments, and a feature the
reference designs lack appears only when its input is given (the error bars of the code edit, the hatched bar; open markers, which the
post's figures do not use: every point is drawn filled). Given the reference figures' own inputs, each function redraws the reference figure
pixel for pixel (a test holds this).

**The numbers** are computed from the committed per-text stores through the functions that produced the committed tables:
`analysis.excess_matrix` (a cell's per-text divergence minus its rung-0 reference's), `stats.union_rung` with the text bootstrap of E
(seed (master, "boot", "E"), one resample shared by every line, the draws held fixed), `stats_s9.union_rung_s9` with the stratified document
bootstrap of E_lab (seed (master, "boot_docs", "E_lab", source)), `s9_checks.document_resample` for the code edit by source, and
`stats_s12.edit_statistics` for the panels. Every error bar is an uncorrected 95 percent percentile interval (lo and hi, not a half-width) of
the rise above the recipient's own explanation, drawn around the rise plus that explanation. At the committed levels the same resamples
reproduce the committed intervals (`interval_canary`), and the points equal the committed values. The own explanations of the code and the
prose texts are computed from E_lab's importances, and their row-weighted mean with the other sources must be the committed E_lab value.

    uv run vpd-audit figures-post [--code-edit panels]    # any of lab,panels,arxiv_panel; panels by default
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from vpd_audit import env

# The post's palette (Okabe-Ito): blue = real merge / general donors, orange = uniform random, vermillion = frequency-matched random,
# purple = code, green = prose; the code edit's sky blue and soft red.
BLUE, BLUE_DARK = "#0072B2", "#003B66"
ORANGE, ORANGE_DARK = "#E69F00", "#8A5A00"
PURPLE, PURPLE_DARK = "#CC79A7", "#7A3D66"
VERMILLION, VERMILLION_DARK = "#D55E00", "#7F3800"
GREEN, GREEN_DARK = "#009E73", "#005C43"
INK, MUTED, SPINE = "#1a1a1a", "#6b6b6b", "#3a3a3a"
SKY, SOFT_RED = "#56B4E9", "#E57373"
RC = {"font.size": 11, "font.family": "DejaVu Sans"}
RC_CODE_EDIT = {**RC, "hatch.linewidth": 0.8}

TOKENS: list[int] = [1, 2, 4, 8, 16, 32, 64]
LATER_TOKENS: tuple[int, ...] = ()  # none: the post draws every point filled (2 and 4 tokens were measured later, the same way on the same donor draws)
X_BREAK, X_WHOLE = 7.0, 8.0
# The paper's own adversary after 20 PGD steps: KL 0.8280 to the target model, on the authors' batch of 128 evaluation sequences of length
# 512 (the paper's PGD table).
ADVERSARY_20 = 0.8280
OUT_NAMES: dict[str, str] = {"aggregation_schematic": "aggregation_schematic", "delete_schematic": "delete_schematic", "aggregation_curve": "aggregation_curve",
                             "similar_donors": "similar_donors", "code_edit": "code_edit", "code_edit_panels": "code_edit_panels", "code_edit_arxiv_panel": "code_edit_arxiv_panel"}
CODE_EDIT_VARIANTS: dict[str, str] = {"lab": "code_edit", "panels": "code_edit_panels", "arxiv_panel": "code_edit_arxiv_panel"}
CODE_EDIT_DEFAULT: tuple[str, ...] = ("panels",)  # the post's code-edit figure; the other variants on request


def _plt():
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    return plt


# ============================================================================= the schematics (no data)

# ---- the aggregation schematic: one toy example, drawn step by step with two chosen donor tokens
MS_INK = INK
OWN = "#7a7a7a"  # on because the recipient needs it here
OFF = "#f0f0f0"
CW = 1.7  # cell width, so whole words fit above each column
COMPONENTS = ["Sentence Start", '"Capital of" Pattern', "Paris Fact", "Sky Fact", "Chemistry Fact"]
RECIPIENT_TOKENS = ["The", "capital", "of", "France"]
DONOR_TOKENS = ["The", "sky", "is", "blue"]
RECIPIENT = np.array([[0.9, 0, 0, 0], [0, 0.8, 0.6, 0], [0, 0, 0, 1.0], [0, 0, 0, 0], [0, 0, 0, 0]])
DONOR = np.array([[0.8, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0], [0, 0.7, 1.0, 0.4], [0, 0, 0, 0]])
NR, NC = RECIPIENT.shape
W = NC * CW


def donor_needs(chosen=None):
    cols = range(NC) if chosen is None else chosen
    return (DONOR[:, list(cols)] > 0.1).any(axis=1)


def merged(chosen=None):
    own = RECIPIENT > 0
    need = donor_needs(chosen)[:, None]
    return own, need & ~own, own | need  # own-need cells, donor-added cells, all on


def grey(v):
    lo, hi = np.array([0.86, 0.86, 0.86]), np.array([0.22, 0.22, 0.22])
    return tuple(lo + (hi - lo) * v)


def cell_y(i, y0):
    return y0 + NR - 1 - i


def tokens_row(ax, tokens, x0, y0, dim=None, box=None):
    from matplotlib.patches import Rectangle

    for j, tok in enumerate(tokens):
        faded = dim is not None and j in dim
        ax.text(x0 + (j + 0.5) * CW, y0 + NR + 0.15, tok, ha="center", va="bottom", fontsize=11,
                color="#b0b0b0" if faded else INK, fontweight="bold")
    if box:
        j0, j1 = min(box), max(box)
        ax.add_patch(Rectangle((x0 + j0 * CW + 0.05, y0 + NR + 0.05), (j1 - j0 + 1) * CW - 0.1, 0.75,
                               fill=False, edgecolor=BLUE, linewidth=1.6))


def row_names(ax, x0, y0, header=False, components=None):
    for i, comp in enumerate(components or COMPONENTS):
        ax.text(x0 - 0.2, cell_y(i, y0) + 0.5, comp, ha="right", va="center", fontsize=10.5, color=INK)
    if header:
        ax.text(x0 - 0.2, y0 + NR + 0.15, "Components ↓", ha="right", va="bottom", fontsize=9, color="#a6a6a6",
                style="italic")


def title(ax, text, x_centre, y0, colour=INK, size=11.5, dy=1.0):
    ax.text(x_centre, y0 + NR + dy, text, ha="center", va="bottom", fontsize=size, color=colour)


def heat(ax, values, tokens, x0, y0, dim=None, box=None):
    from matplotlib.patches import Rectangle

    for i in range(NR):
        for j in range(NC):
            v = values[i, j]
            faded = dim is not None and j in dim
            fc = "white" if v == 0 else grey(v)
            ax.add_patch(Rectangle((x0 + j * CW, cell_y(i, y0)), CW, 1, facecolor=fc, edgecolor="white",
                                   linewidth=2, alpha=0.35 if faded else 1.0))
            txt = "0" if v == 0 else f"{v:.1f}"
            tc = "#c8c8c8" if faded else (MUTED if v == 0 else ("white" if v >= 0.5 else INK))
            ax.text(x0 + (j + 0.5) * CW, cell_y(i, y0) + 0.5, txt, ha="center", va="center", fontsize=10, color=tc)
    tokens_row(ax, tokens, x0, y0, dim=dim, box=box)


def pooled(ax, needs, x0, y0, header, hsize=9.5):
    from matplotlib.patches import Rectangle

    for i in range(NR):
        fc = BLUE if needs[i] else OFF
        ax.add_patch(Rectangle((x0, cell_y(i, y0)), CW, 1, facecolor=fc, edgecolor="white", linewidth=2))
        ax.text(x0 + CW / 2, cell_y(i, y0) + 0.5, "yes" if needs[i] else "no", ha="center", va="center",
                fontsize=10, color="white" if needs[i] else MUTED)
    ax.text(x0 + CW / 2, y0 + NR + 0.15, header, ha="center", va="bottom", fontsize=hsize, color=INK,
            linespacing=1.1)


def merged_grid(ax, x0, y0, chosen=None, letters=False):
    from matplotlib.patches import Rectangle

    own, added, _ = merged(chosen)
    for i in range(NR):
        for j in range(NC):
            if own[i, j]:
                fc, txt, tc = OWN, ("R" if letters else "on"), "white"
            elif added[i, j]:
                fc, txt, tc = BLUE, ("D" if letters else "on"), "white"
            else:
                fc, txt, tc = OFF, ("" if letters else "off"), MUTED
            ax.add_patch(Rectangle((x0 + j * CW, cell_y(i, y0)), CW, 1, facecolor=fc, edgecolor="white", linewidth=2))
            ax.text(x0 + (j + 0.5) * CW, cell_y(i, y0) + 0.5, txt, ha="center", va="center", fontsize=10,
                    color=tc, fontweight="bold" if letters else "normal")
    tokens_row(ax, RECIPIENT_TOKENS, x0, y0)


def legend(ax, x, y, letters=False):
    from matplotlib.patches import Rectangle

    items = [(OWN, ("R: " if letters else "") + "on, because the recipient needs it here"),
             (BLUE, ("D: " if letters else "") + "on everywhere, because a donor token needs it"),
             (OFF, "off")]
    for k, (fc, lab) in enumerate(items):
        ax.add_patch(Rectangle((x, y - 0.6 * k), 0.42, 0.42, facecolor=fc, edgecolor=SPINE, linewidth=0.6))
        ax.text(x + 0.6, y - 0.6 * k + 0.21, lab, va="center", fontsize=9.5, color=INK)


def arrow(ax, a, b, colour=MUTED, lw=1.4, style="-|>", rad=0.0):
    from matplotlib.patches import FancyArrowPatch

    ax.add_patch(FancyArrowPatch(a, b, arrowstyle=style, mutation_scale=14, color=colour, linewidth=lw,
                                 connectionstyle=f"arc3,rad={rad}"))


def save(fig, ax, path, xlim, ylim):
    ax.set_xlim(*xlim)
    ax.set_ylim(*ylim)
    ax.set_aspect("equal")
    ax.axis("off")
    fig.savefig(path, facecolor="white", bbox_inches="tight", dpi=200)
    _plt().close(fig)


def draw_aggregation_schematic(path: Path) -> Path:
    """The aggregation, step by step, with two chosen donor tokens."""
    plt = _plt()
    with plt.rc_context(RC):
        chosen = [0, 1]
        fig, ax = plt.subplots(figsize=(12.5, 8.8))
        top = NR + 3.8
        rx = W + 2.8
        heat(ax, DONOR, DONOR_TOKENS, 0, top, dim=[2, 3], box=chosen)
        row_names(ax, 0, top, header=True)
        title(ax, "(a) Donor's labels - two tokens chosen", W / 2, top, dy=1.1, size=11.2)
        bx = rx + W / 2 - CW / 2
        pooled(ax, donor_needs(chosen), bx, top, "(b) Needed by any\nchosen token?", hsize=11.2)
        arrow(ax, (W + 0.2, top + 2.5), (bx - 0.2, top + 2.5))
        ax.text((W + bx) / 2, top + 2.95, "label > 0.1?", ha="center", va="center", fontsize=9.5, color=MUTED)
        heat(ax, RECIPIENT, RECIPIENT_TOKENS, 0, 0)
        row_names(ax, 0, 0, header=True)
        title(ax, "(c) Recipient's labels", W / 2, 0, size=11.2)
        merged_grid(ax, rx, 0, chosen=chosen)
        title(ax, "(d) Aggregated setting", rx + W / 2, 0, size=11.2)
        arrow(ax, (W + 0.2, 2.5), (rx - 0.2, 2.5))
        ax.text((W + rx) / 2, 2.95, "label > 0?", ha="center", va="center", fontsize=9.5, color=MUTED)
        for j in range(NC):
            arrow(ax, (bx + CW / 2, top - 0.1), (rx + (j + 0.5) * CW, NR + 2.35), colour=BLUE, lw=1.0)
        ax.text(rx + 1.5, top - 0.35, "Copied to every\nrecipient token", ha="right", va="center", fontsize=9.5,
                color=BLUE)
        legend(ax, rx, -0.6)
        ax.text(W / 2 - 1.5, -1.3, "Run the model on \"The capital of France\" with (d),\nmeasure the KL divergence from the "
                "original at each token.\nIf mechanistically faithful, divergence near zero expected.", ha="center", va="center", fontsize=10, color=INK,
                bbox=dict(boxstyle="square,pad=0.6", facecolor="#f0f0f0", edgecolor=INK, linewidth=1.0))
        save(fig, ax, path, (-3.6, rx + W + 0.3), (-2.4, top + NR + 2.2))
    return Path(path)


# ---- the delete schematic: the hard and the soft delete on one toy example, in the aggregation schematic's visual language
DARK_ORANGE = "#E57373"  # deleted: a soft red (the name kept from the reference code)
PINK = "#CC79A7"  # turned down to its label (soft delete)
HEAD = 11.2  # the panel headings' size
DS_TOKENS = ["Add", "baking", "soda", "so"]
DS_LABELS = np.array([[0.9, 0, 0, 0],
                      [0, 0, 0, 0],
                      [0, 0, 0, 0],
                      [0, 0, 0, 0],
                      [0, 0, 0.4, 0.2]])
DELETE = np.array([False, False, False, False, True])  # Chemistry Fact
FIRST_USE = int(np.argmax((DS_LABELS[DELETE] > 0.1).any(axis=0)))  # first token where a deleted label > 0.1
TOP = NR + 4.2  # y of the top row of grids
DX = W + 2.8  # x of the right-hand bottom grid


def setting(ax, x0, y0, mode, soft_colour=PINK, all_orange=False, outline_below=False):
    from matplotlib.patches import Rectangle

    for i in range(NR):
        for j in range(NC):
            g = DS_LABELS[i, j]
            if not DELETE[i]:
                fc, txt, tc = OWN, "on", "white"
            elif all_orange:
                fc, txt, tc = DARK_ORANGE, ("0" if mode == "hard" or g == 0 else f"{g:.1f}"), "white"
            elif mode == "hard":
                fc, txt, tc = (DARK_ORANGE, "0", "white") if g > 0 else (OFF, "0", MUTED)
            else:
                fc, txt, tc = (soft_colour, f"{g:.1f}", "white") if g > 0 else (OFF, "0", MUTED)
            ax.add_patch(Rectangle((x0 + j * CW, cell_y(i, y0)), CW, 1, facecolor=fc, edgecolor="white", linewidth=2))
            ax.text(x0 + (j + 0.5) * CW, cell_y(i, y0) + 0.5, txt, ha="center", va="center", fontsize=10, color=tc)
    for j, tok in enumerate(DS_TOKENS):
        ax.text(x0 + (j + 0.5) * CW, y0 + NR + 0.15, tok, ha="center", va="bottom", fontsize=11, color=INK,
                fontweight="bold")


def base(ax, a_title="(a) Recipient's labels", c_title="(c) Hard delete", d_title="(d) Soft delete",
         soft_colour=PINK, all_orange=False):
    heat(ax, DS_LABELS, DS_TOKENS, 0, TOP)
    row_names(ax, 0, TOP, header=True)
    title(ax, a_title, W / 2, TOP, size=HEAD)
    setting(ax, 0, 0, "hard", all_orange=all_orange)
    row_names(ax, 0, 0, header=True)
    title(ax, c_title, W / 2, 0, size=HEAD)
    setting(ax, DX, 0, "soft", soft_colour=soft_colour, all_orange=all_orange)
    title(ax, d_title, DX + W / 2, 0, size=HEAD)


def ticks(ax, x0, n_cov, label=True):
    if label:
        ax.text(x0 - 0.2, -0.45, "Guaranteed unchanged?", ha="right", va="center", fontsize=9.5, color=MUTED,
                style="italic")
    for j in range(NC):
        ok = j < n_cov
        ax.text(x0 + (j + 0.5) * CW, -0.45, "✓" if ok else "✗", ha="center", va="center", fontsize=14,
                color=GREEN if ok else DARK_ORANGE, fontweight="bold")


def legend_items(ax, x, y, items):
    from matplotlib.patches import Rectangle

    for k, (fc, lab) in enumerate(items):
        ax.add_patch(Rectangle((x, y - 0.6 * k), 0.42, 0.42, facecolor=fc, edgecolor=SPINE, linewidth=0.6))
        ax.text(x + 0.6, y - 0.6 * k + 0.21, lab, va="center", fontsize=9.5, color=INK)


def footer(ax, x, y, text):
    ax.text(x, y, text, ha="center", va="center", fontsize=10, color=INK,
            bbox=dict(boxstyle="square,pad=0.6", facecolor="#f0f0f0", edgecolor=INK, linewidth=1.0))


def draw_delete_schematic(path: Path) -> Path:
    """The hard delete (the authors' edit) and the soft delete (the check), with the tokens the promise covers."""
    plt = _plt()
    from matplotlib.patches import Rectangle

    with plt.rc_context(RC):
        fig, ax = plt.subplots(figsize=(12.5, 9.6))
        base(ax, a_title="(a) Text's labels", c_title="(b) Hard delete - the authors' edit",
             d_title="(c) Soft delete - our check")
        ax.add_patch(Rectangle((-0.02, cell_y(4, TOP) - 0.02), W + 0.04, 1.04, fill=False, edgecolor=DARK_ORANGE,
                               linewidth=2.2))
        ax.text(W + 0.25, cell_y(4, TOP) + 0.5, "Chosen\nto delete", ha="left", va="center", fontsize=9.5,
                color=DARK_ORANGE)
        ax.text(W + 0.25, cell_y(4, TOP) - 0.3, "(chosen once, for every text)", ha="left", va="center", fontsize=8.5,
                color=MUTED)
        arrow(ax, (W / 2, TOP - 0.15), (W / 2, NR + 1.95))
        ax.text(W / 2 + 0.2, TOP - 1.0, "chosen → 0", ha="left", va="center", fontsize=9.5, color=MUTED)
        arrow(ax, (W * 0.7, TOP - 0.15), (DX + W / 2, NR + 1.95), rad=0.08)
        ax.text(DX + 0.9, TOP - 1.45, "chosen → own label", ha="left", va="center", fontsize=9.5, color=MUTED)
        ticks(ax, 0, FIRST_USE)
        ticks(ax, DX, NC, label=False)
        legend_items(ax, DX, -1.5, [(OWN, "on: every other component, fully on"),
                                    (DARK_ORANGE, "off, below its label"),
                                    (PINK, "at its label"),
                                    (OFF, "0, and its label is 0 here")])
        footer(ax, W / 2 - 0.4, -2.6, 'Run the model on "Add baking soda so" with (b) or (c),\nmeasure the KL divergence '
                                      'from the original at each token.\nIf mechanistically faithful, divergence near zero '
                                      'expected\nat every token marked ✓.')
        save(fig, ax, path, (-3.6, DX + W + 0.3), (-4.2, TOP + NR + 2.0))
    return Path(path)


# ============================================================================= the data figures' drawing


LAYOUT_PIXEL_RATIO = 2


def tight_layout_at_pixel_ratio(fig) -> None:
    """`fig.tight_layout()` computed at twice the figure's dpi, then the dpi restored before saving. The reference figures were drawn by the
    macOS backend on a high-density display, which lays a figure out at a device pixel ratio of 2 and saves it at the figure's own dpi; the
    text extents, and so the axes' positions, differ by about two pixels from a layout at 1. Laying out at the same ratio under Agg gives
    the reference images pixel for pixel on any machine (the pixel test holds this)."""
    dpi = fig.dpi
    fig.set_dpi(dpi * LAYOUT_PIXEL_RATIO)
    fig.tight_layout()
    fig.set_dpi(dpi)


def style_axes(ax):
    for side in ("left", "bottom", "top", "right"):
        ax.spines[side].set_color(SPINE)
        ax.spines[side].set_linewidth(1.1)
    ax.tick_params(colors=INK, direction="in", length=5, width=1.1)


def axis_break(ax):
    import matplotlib.transforms as mtransforms

    blend = mtransforms.blended_transform_factory(ax.transData, ax.transAxes)
    for y0 in (0, 1):
        ax.plot([X_BREAK - 0.12, X_BREAK + 0.12], [y0, y0], color="white", linewidth=3,
                transform=blend, clip_on=False, zorder=6)
        for dx in (-0.12, 0.12):
            ax.plot([X_BREAK + dx - 0.06, X_BREAK + dx + 0.06], [y0 - 0.02, y0 + 0.02],
                    color=SPINE, linewidth=1.1, transform=blend, clip_on=False, zorder=7)


def curve(ax, x, y, lo, hi, color, dark, marker):
    ax.plot(x, y, color=color, linewidth=2, marker=marker, markersize=6.5,
            markeredgewidth=0, zorder=3)
    if lo is not None:
        yerr = np.vstack([np.asarray(y) - np.asarray(lo), np.asarray(hi) - np.asarray(y)])
        ax.errorbar(x, y, yerr=yerr, fmt="none", ecolor=dark, elinewidth=1.2,
                    capsize=2.5, capthick=1.2, zorder=2)


def open_markers(ax, x, y, color, marker):
    """Points measured later: the same marker, open, in the line's colour, over the filled one."""
    if len(x):
        ax.plot(x, y, linestyle="none", marker=marker, markersize=6.5, markerfacecolor="white", markeredgecolor=color, markeredgewidth=1.4, zorder=4)


def handle(color, marker):
    from matplotlib.lines import Line2D

    return Line2D([], [], color=color, linewidth=2, marker=marker, markersize=6.5,
                  markeredgewidth=0)


@dataclass
class Line:
    """One line of a curve figure: the divergence plotted at each number of donor tokens (in `tokens` order), its interval's ends (None: no
    bars), and optionally the whole donor text's point past the break; `later` lists the numbers of tokens drawn with open markers."""

    color: str
    dark: str
    marker: str
    label: str
    y: np.ndarray
    lo: np.ndarray | None = None
    hi: np.ndarray | None = None
    whole: tuple[float, float, float] | None = None  # (y, lo, hi)
    later: tuple[int, ...] = ()


def draw_aggregation_curve(lines: list[Line], tokens: list[int], own_explanation: float, path: Path, *, adversary: float = ADVERSARY_20) -> Path:
    """The top figure: divergence on E against donor tokens, the whole donor text past the break, the paper's 20-step adversary and the
    recipient's own explanation as reference lines."""
    plt = _plt()
    with plt.rc_context(RC):
        x_tok = np.log2(tokens)
        fig, ax = plt.subplots(figsize=(7.2, 4.4), dpi=200)
        ax.axhline(adversary, color=MUTED, linewidth=1.0, linestyle=(0, (5, 3)), zorder=1)
        ax.text(-0.15, adversary - 0.015, "Paper's 20-Step Adversary", color=MUTED, fontsize=9,
                va="top", ha="left")
        ax.axhline(own_explanation, color=MUTED, linewidth=1.0, linestyle=(0, (1, 2)), zorder=1)
        ax.text(8.55, own_explanation - 0.012, "Recipient's Own Explanation", color=MUTED,
                fontsize=9, va="top", ha="right")
        for ln in lines:
            curve(ax, x_tok, ln.y, ln.lo, ln.hi, ln.color, ln.dark, ln.marker)  # all lines solid
            if ln.whole is not None:
                w_y, w_lo, w_hi = ln.whole
                curve(ax, [X_WHOLE], [w_y], [w_lo], [w_hi], ln.color, ln.dark, ln.marker)
            sel = [i for i, t in enumerate(tokens) if t in ln.later]
            if sel:
                open_markers(ax, x_tok[sel], np.asarray(ln.y)[sel], ln.color, ln.marker)
        ax.set_xlim(-0.4, 8.6)
        ax.set_ylim(0, 0.9)
        ax.set_xticks(list(x_tok) + [X_WHOLE])
        ax.set_xticklabels([str(t) for t in tokens] + ["Whole Donor\nText"])
        ax.set_xlabel("Donor Tokens", color=INK)
        ax.set_ylabel("KL from Original Model (nats)", color=INK)
        style_axes(ax)
        axis_break(ax)
        leg = ax.legend([handle(ln.color, ln.marker) for ln in lines], [ln.label for ln in lines],
                        loc="lower right", bbox_to_anchor=(1.0, 0.02), frameon=False, handlelength=2.2, fontsize=10)
        for t in leg.get_texts():
            t.set_color(INK)
        tight_layout_at_pixel_ratio(fig)
        fig.savefig(path, facecolor="white")
        plt.close(fig)
    return Path(path)


@dataclass
class Panel:
    """One panel of the similar-donors figure: its title and colour, the recipients' own explanation, and one line per kind of donor
    whose `y`, `lo`, `hi` hold the token points followed by the whole donor text's."""

    title: str
    title_color: str
    base: float
    lines: list[Line]


def draw_similar_donors(panels: list[Panel], tokens: list[int], path: Path) -> Path:
    """The similar-donors figure: code recipients and prose recipients side by side, three kinds of donors each."""
    plt = _plt()
    with plt.rc_context(RC):
        xs = list(np.log2(tokens)) + [X_WHOLE]
        n = len(tokens)
        fig, axes = plt.subplots(1, 2, figsize=(10.0, 4.3), dpi=200, sharey=True)
        for ax, pnl in zip(axes, panels):
            ax.axhline(pnl.base, color=MUTED, linewidth=1.0, linestyle=(0, (1, 2)), zorder=1)
            ax.text(6.25, pnl.base - 0.02, "Recipient's Own Explanation", color=MUTED, fontsize=9,
                    va="top", ha="right")
            for ln in pnl.lines:
                y, lo, hi = np.asarray(ln.y), np.asarray(ln.lo), np.asarray(ln.hi)
                curve(ax, xs[:n], y[:n], lo[:n], hi[:n], ln.color, ln.dark, ln.marker)
                curve(ax, xs[n:], y[n:], lo[n:], hi[n:], ln.color, ln.dark, ln.marker)
                sel = [i for i, t in enumerate(tokens) if t in ln.later]
                if sel:
                    open_markers(ax, np.asarray(xs)[sel], y[sel], ln.color, ln.marker)
            ax.set_xlim(-0.4, 8.6)
            ax.set_xticks(xs)
            ax.set_xticklabels([str(t) for t in tokens] + ["Whole Donor\nText"])
            ax.set_xlabel("Donor Tokens", color=INK)
            ax.text(0.03, 0.96, pnl.title, transform=ax.transAxes, color=INK, fontsize=11,
                    fontweight="bold", va="top")
            style_axes(ax)
            axis_break(ax)
        axes[0].set_ylabel("KL from Original Model (nats)", color=INK)
        for ax in axes:
            ax.set_ylim(0, 1.5)
        leg = axes[0].legend([handle(ln.color, ln.marker) for ln in panels[0].lines], [ln.label for ln in panels[0].lines],
                             loc="upper left", bbox_to_anchor=(0.0, 0.88), frameon=False,
                             handlelength=2.2, fontsize=10)
        for t in leg.get_texts():
            t.set_color(INK)
        tight_layout_at_pixel_ratio(fig)
        fig.savefig(path, facecolor="white")
        plt.close(fig)
    return Path(path)


CODE_EDIT_SOURCES: list[str] = ["GitHub", "StackExchange", "ArXiv", "Pile-CC", "Wikipedia (en)"]
CODE_EDIT_LABELS: list[str] = ["Code\n(GitHub)", "StackExchange", "ArXiv", "Web Text\n(Pile-CC)", "Wikipedia"]
CODE_EDIT_SERIES: list[tuple[int, str, str]] = [(256, SKY, "256 Code-Specific Components Deleted"), (1007, SOFT_RED, "All 1,007 Code-Specific Components Deleted")]


@dataclass
class Bars:
    """The code-edit figure's bars: per edit size, per source (CODE_EDIT_SOURCES order), the damage, and optionally its interval's ends
    (NaN where the bar has none); `hatched` lists the sources whose bars are measured on another set of texts, with the legend's words."""

    values: dict[int, list[float]]
    lo: dict[int, list[float]] | None = None
    hi: dict[int, list[float]] | None = None
    hatched: tuple[str, ...] = ()
    hatched_label: str = ""


def draw_code_edit(bars: Bars, path: Path) -> Path:
    """Two bars per kind of text (256 and all 1,007 code-leaning components deleted)."""
    plt = _plt()
    from matplotlib.patches import Patch

    with plt.rc_context(RC_CODE_EDIT):
        x = np.arange(len(CODE_EDIT_SOURCES))
        w, gap = 0.34, 0.02
        fig, ax = plt.subplots(figsize=(7.2, 4.4), dpi=200)
        handles, names = [], []
        top = 0.0
        for i, (size, color, label) in enumerate(CODE_EDIT_SERIES):
            offset = (i - 0.5) * (w + gap)
            y = bars.values[size]
            ax.bar(x + offset, y, width=w, color=color, edgecolor=INK, linewidth=0.9, zorder=3)
            handles.append(Patch(facecolor=color, edgecolor=INK, linewidth=0.9))
            names.append(label)
            top = max(top, float(np.nanmax(y)))
            if bars.hatched:
                idx = [CODE_EDIT_SOURCES.index(s) for s in bars.hatched]
                ax.bar(x[idx] + offset, np.asarray(y)[idx], width=w, facecolor="none", edgecolor=INK, hatch="//", linewidth=0.9, zorder=4)
            if bars.lo is not None:
                lo, hi = np.asarray(bars.lo[size], dtype=float), np.asarray(bars.hi[size], dtype=float)
                has = np.isfinite(lo) & np.isfinite(hi)
                if has.any():
                    yy = np.asarray(y, dtype=float)[has]
                    ax.errorbar((x + offset)[has], yy, yerr=np.vstack([yy - lo[has], hi[has] - yy]), fmt="none", ecolor=INK, elinewidth=1.2, capsize=2.5, capthick=1.2, zorder=5)
                    top = max(top, float(np.max(hi[has])))
        if bars.hatched:
            handles.append(Patch(facecolor="white", edgecolor=INK, hatch="//", linewidth=0.9))
            names.append(bars.hatched_label)
        ax.set_xticks(x)
        ax.set_xticklabels(CODE_EDIT_LABELS)
        ax.set_xlim(-0.6, len(CODE_EDIT_SOURCES) - 0.4)
        ax.set_ylim(0, max(3.6, float(np.ceil(top * 10.0) / 10.0 + 0.1)) if top > 3.6 else 3.6)  # the reference 3.6 unless a bar or a bar's interval would not fit
        ax.set_ylabel("KL from Original Model (nats)", color=INK)
        ax.set_xlabel("Kind of Input Text", color=INK)
        style_axes(ax)
        ax.tick_params(axis="x", length=0)
        leg = ax.legend(handles, names, loc="upper right", frameon=False, fontsize=9.5)
        for t in leg.get_texts():
            t.set_color(INK)
        tight_layout_at_pixel_ratio(fig)
        fig.savefig(path, facecolor="white")
        plt.close(fig)
    return Path(path)


# ============================================================================= the numbers


@dataclass
class Inputs:
    """Where the numbers come from: the committed stores and tables of a run, and (after its launch) its tier-7 stores."""

    run: str
    results_root: Path
    tier7_root: Path | None
    master_seed: int = 0
    replicates: int = 10_000
    notes: dict[str, Any] = field(default_factory=dict)

    @property
    def grid(self) -> Path:
        return self.results_root / "grid" / self.run

    @property
    def analysis(self) -> Path:
        return self.results_root / "grid" / "analysis" / self.run


def paper_inputs(results_root: Path | None = None, run: str = "main", *, with_tier7: bool = True) -> Inputs:
    from vpd_audit import tier7 as t7m

    r = Path(results_root or env.PROJECT_ROOT / "results")
    return Inputs(run=run, results_root=r, tier7_root=(r / "grid" / t7m.root_name(run) / "tier7") if with_tier7 else None)


def _rows(store: Path, names: list[str]) -> pd.DataFrame:
    r = pd.read_parquet(Path(store) / "per_sequence.parquet", columns=["cell", "seq", "kl_mean"])
    r = r[r["cell"].isin(names)]
    missing = set(names) - set(r["cell"])
    assert not missing, f"{store}: no rows for {sorted(missing)[:4]}"
    return r


def set_data(eval_set: str, parts: list[tuple[Path, list[str]]], reference: str) -> Any:
    """An `analysis.SetData` over the given cells of the given stores, for `analysis.excess_matrix`. Each store must carry the rung-0
    reference with the same per-text values bitwise (the first store's is kept)."""
    from vpd_audit.analysis import SetData

    frames, ref_vals = [], None
    for store, names in parts:
        r = _rows(store, sorted(set(names) | {reference}))
        ref = r[r["cell"] == reference].sort_values("seq")["kl_mean"].to_numpy(np.float32)
        if ref_vals is None:
            ref_vals = ref
            frames.append(r)
        else:
            assert np.array_equal(ref, ref_vals), f"{store}: its {reference} is not the first store's bitwise"
            frames.append(r[r["cell"] != reference])
    rows = pd.concat(frames, ignore_index=True)
    dup = rows.groupby("cell")["seq"].count()
    n = int(rows["seq"].max()) + 1
    assert (dup == n).all(), f"a cell held twice or not whole: {dup[dup != n].index.tolist()[:4]}"
    cells = pd.DataFrame(index=sorted(rows["cell"].unique()))
    return SetData(eval_set, n, "", rows, cells, {}, [])


def _union(run: str, eval_set: str, pool: str, k: int, rung: str, control: str = "none", tier: int = 1, descriptive: bool = False) -> Any:
    from vpd_audit.cells import TAU_PRIMARY, Cell

    return Cell(run, "union", eval_set, pool, TAU_PRIMARY, "r0", "excluded", k, rung, control, tier, descriptive=descriptive)


def committed_curve1_chain(inp: Inputs, control: str) -> tuple[list[str], int]:
    """Curve 1's rungs (the real merge on E, or its uniform control) in the committed cell table, the registered ones only (not the
    descriptive), and the m that `stats.compared_rungs` gives them."""
    from vpd_audit import stats as st

    tier, store = (1, inp.grid / "tier1" / "E") if control == "none" else (2, inp.grid / "tier2" / "E")
    ct = pd.read_parquet(store / "cells.parquet")
    descriptive = ct["descriptive"].fillna(False).astype(bool) if "descriptive" in ct.columns else pd.Series(False, index=ct.index)  # a table written before the flag existed has none
    sel = ct[(ct.family == "union") & (ct.eval_set == "E") & (ct.donor_pool == "D_unif") & (ct.tau == 0.1) & (ct.background == "r0") & (ct.delta == "excluded") & (ct.control == control) & (~descriptive)]
    rungs = sorted(set(sel["rung"].astype(str)))
    return rungs, len(st.compared_rungs(rungs, "union"))


E_MERGE_RUNGS: dict[str, tuple[str, ...]] = {"none": ("1", "2", "2a", "2b", "3", "4"), "plain": ("1", "2", "2a", "2b", "3", "4"), "marginal": ("1", "2", "2a", "2b", "3")}
RUNG_TOKENS: dict[str, int] = {"1": 1, "T2": 2, "T4": 4, "2": 8, "2a": 16, "2b": 32, "3": 64, "4": 512}
LATER_RUNGS: tuple[str, ...] = ("T2", "T4")


def _draws(inp: Inputs) -> int:
    return 8 if inp.run == "main" else 2


def e_data(inp: Inputs) -> tuple[Any, dict[str, dict[str, list[Any]]]]:
    """E's SetData over curve 1 (the real merge and the uniform control at 1 to 64 tokens and the whole donor text), the frequency-matched
    control (1 to 64 tokens), and, with the tier-7 stores, all three at 2 and 4 tokens; and the cells per line and rung."""
    run, K = inp.run, _draws(inp)
    cells: dict[str, dict[str, list[Any]]] = {ctl: {} for ctl in ("none", "plain", "marginal")}
    where: dict[Path, list[str]] = {}
    for ctl, rungs in E_MERGE_RUNGS.items():
        for r in rungs:
            if ctl == "marginal":
                tier, store = 4, inp.grid / "tier4" / "E__marginal"
            elif r in ("2a", "2b"):
                tier, store = 3, inp.grid / "tier3" / "E__curve1_extra"
            else:
                tier, store = (1, inp.grid / "tier1" / "E") if ctl == "none" else (2, inp.grid / "tier2" / "E")
            cs = [_union(run, "E", "D_unif", k, r, ctl, tier, descriptive=r in ("2a", "2b")) for k in range(K)]
            cells[ctl][r] = cs
            where.setdefault(store, []).extend(c.name for c in cs)
    if inp.tier7_root is not None:
        for ctl in cells:
            for r in LATER_RUNGS:
                cs = [_union(run, "E", "D_unif", k, r, ctl, 7, descriptive=True) for k in range(K)]
                cells[ctl][r] = cs
                where.setdefault(inp.tier7_root / "E__merge_sizes", []).extend(c.name for c in cs)
    parts = [(inp.grid / "tier1" / "E", where.pop(inp.grid / "tier1" / "E"))] + list(where.items())
    return set_data("E", parts, f"{run}/E/ref/importances"), cells


def e_lab_strata(inp: Inputs) -> dict[str, Any]:
    """E_lab's code texts (GitHub) and prose texts (Pile-CC and Wikipedia): masks, documents (the committed document index), and the
    stratified document resample per stratum."""
    from vpd_audit import s9_checks
    from vpd_audit import stats_s9 as s9

    idx = pd.read_csv(inp.analysis / "s9" / "document_index.csv")
    el = idx[idx["set"] == "E_lab"].sort_values("row").reset_index(drop=True)
    src = el["source"].to_numpy()
    docs = s9_checks.document_codes(idx, "E_lab", 0, len(el))
    out = {"sources": src, "documents": docs}
    for key, members in (("code", ("Github",)), ("prose", ("Pile-CC", "Wikipedia (en)"))):
        mask = np.isin(src, members)
        out[key] = {"mask": mask, "n_documents": int(np.unique(docs[mask]).size),
                    "resample": s9.stratified_document_resample(docs[mask], src[mask], inp.replicates, lambda s: (inp.master_seed, "boot_docs", "E_lab", s))}
    return out


E_LAB_ARM_RUNGS: tuple[str, ...] = ("1", "2", "2a", "2b", "3", "4")
ARM_POOLS: dict[str, str] = {"code donors": "D_code", "general donors": "D_unif", "prose donors": "D_prose"}


def e_lab_data(inp: Inputs) -> tuple[Any, dict[str, dict[str, list[Any]]]]:
    """E_lab's SetData over the three arms at 1 to 64 tokens and one text (the committed same-domain store), and with the tier-7 stores at 2
    and 4 tokens."""
    run, K = inp.run, _draws(inp)
    store = inp.results_root / "grid" / f"{run}_s9" / "tier5" / "E_lab__same_domain"
    cells: dict[str, dict[str, list[Any]]] = {}
    names5, names7 = [], []
    for arm, pool in ARM_POOLS.items():
        cells[arm] = {r: [_union(run, "E_lab", pool, k, r, "none", 5) for k in range(K)] for r in E_LAB_ARM_RUNGS}
        names5 += [c.name for cs in cells[arm].values() for c in cs]
        if inp.tier7_root is not None:
            for r in LATER_RUNGS:
                cells[arm][r] = [_union(run, "E_lab", pool, k, r, "none", 7, descriptive=True) for k in range(K)]
                names7 += [c.name for c in cells[arm][r]]
    parts = [(store, names5)] + ([(inp.tier7_root / "E_lab__merge_sizes", names7)] if names7 else [])
    return set_data("E_lab", parts, f"{run}/E_lab/ref/importances"), cells


def own_explanation_e(inp: Inputs) -> float:
    """E's own explanation, the importances reference's mean divergence, read from its committed table (fig1_merge_curve.csv)."""
    f1 = pd.read_csv(inp.analysis / "s9" / "figures" / "fig1_merge_curve.csv", float_precision="round_trip")
    return float(f1[f1.series == "reference: the text's own explanation"].iloc[0]["divergence"])


def own_explanations(inp: Inputs, sd_lab: Any, strata: dict[str, Any]) -> dict[str, float]:
    """The recipients' own explanations on E_lab: the mean of its importances over the code texts and over the prose texts, computed; and
    over all of E_lab (its five sources, each row once), which must be the committed E_lab value (s9_run6_self_merge_rule.csv,
    own_labels_kl) to within 1e-12."""
    imp = sd_lab.vector(f"{inp.run}/E_lab/ref/importances", "kl_mean").astype(np.float64)
    assert imp.size == len(strata["sources"]), (imp.size, len(strata["sources"]))
    whole = float(imp.mean())
    committed = pd.read_csv(inp.analysis / "s9b" / "s9_run6_self_merge_rule.csv", float_precision="round_trip").set_index("set")
    want = float(committed.loc["E_lab", "own_labels_kl"])
    assert abs(whole - want) <= 1e-12, f"the row-weighted mean of E_lab's importances over its five sources {whole!r} is not the committed E_lab value {want!r}"
    return {"code": float(imp[strata["code"]["mask"]].mean()), "prose": float(imp[strata["prose"]["mask"]].mean()), "E_lab": whole, "E_lab_committed": want, "E_lab_bitwise": whole == want}


def aggregation_curve_numbers(inp: Inputs, sd: Any, cells: dict[str, dict[str, list[Any]]], *, levels: dict[str, dict[str, int]] | None = None) -> pd.DataFrame:
    """Per line and rung: the rise over the own explanation (`analysis.excess_matrix`, `stats.union_rung` with the text bootstrap of E) and its
    interval at level 1 - 0.05/m, m = 1 unless `levels` gives it per line and rung; the per-text mean divergence; the plotted divergence."""
    from vpd_audit import stats as st
    from vpd_audit.analysis import excess_matrix, matrix

    rs = st.Resample.make(sd.n_sequences, inp.replicates, (inp.master_seed, "boot", "E"))
    rows = []
    for ctl, by_r in cells.items():
        for r, cs in by_r.items():
            m = (levels or {}).get(ctl, {}).get(r, 1)
            e = excess_matrix(sd, cs)
            u = st.union_rung(e, rs, m)
            rows.append({"control": ctl, "rung": r, "tokens": RUNG_TOKENS[r], "m": m, "rise": u["e_hat"], "rise_lo": u["interval"][0], "rise_hi": u["interval"][1], "half_width": u["half_width"],
                         "mean_kl": float(matrix(sd, cs, "kl_mean").mean()), "n_draws": u["n_draws"], "later": r in LATER_RUNGS})
    return pd.DataFrame(rows)


def similar_donors_numbers(inp: Inputs, sd: Any, cells: dict[str, dict[str, list[Any]]], strata: dict[str, Any], *, m: int = 1) -> pd.DataFrame:
    """Per stratum, arm, and rung: the rise over the stratum's own explanation (`stats_s9.union_rung_s9` with the stratified document
    bootstrap) and its interval at level 1 - 0.05/m."""
    from vpd_audit import stats_s9 as s9
    from vpd_audit.analysis import excess_matrix

    rows = []
    for key in ("code", "prose"):
        S = strata[key]
        for arm, by_r in cells.items():
            for r, cs in by_r.items():
                u = s9.union_rung_s9(excess_matrix(sd, cs)[:, S["mask"]], S["resample"], m, n_documents=S["n_documents"])
                rows.append({"texts": key, "donors": arm, "rung": r, "tokens": RUNG_TOKENS[r], "m": m, "rise": u["e_hat"], "rise_lo": u["interval"][0], "rise_hi": u["interval"][1],
                             "n_documents": S["n_documents"], "later": r in LATER_RUNGS})
    return pd.DataFrame(rows)


CODE_LEANING_SOURCES: dict[str, str] = {"GitHub": "Github", "StackExchange": "StackExchange", "ArXiv": "ArXiv", "Pile-CC": "Pile-CC", "Wikipedia (en)": "Wikipedia (en)"}
PANEL_OF_SOURCE: dict[str, str] = {"GitHub": "panel_Github", "StackExchange": "panel_StackExchange", "ArXiv": "panel_ArXiv", "Pile-CC": "panel_Pile_CC", "Wikipedia (en)": "panel_Wikipedia__en_"}
EDIT_SIZES: tuple[int, int] = (256, 1007)


def code_edit_lab_numbers(inp: Inputs, strata: dict[str, Any]) -> pd.DataFrame:
    """Per source of E_lab and edit size: the group's damage (`analysis.excess_matrix` against unmasked_delta, the committed code-leaning
    store) with its document-level 95 percent interval (the source's own document resample, seed (master, "boot_docs", "E_lab", source);
    none below ten documents). The damages must equal the committed by-source tables."""
    from vpd_audit.analysis import excess_matrix
    from vpd_audit.cells import TAU_PRIMARY, Cell
    from vpd_audit.s9_checks import doc_means, document_resample, interval_or_none

    run = inp.run
    store = inp.grid / "tier4" / "E_lab__code_leaning"
    group = {n: Cell(run, "code_leaning_hard", "E_lab", "D_code", TAU_PRIMARY, "ones", "included", 0, f"G{n}", "none", 4) for n in EDIT_SIZES}
    sd = set_data("E_lab", [(store, [c.name for c in group.values()])], f"{run}/E_lab/ref/unmasked_delta")
    by = pd.read_csv(inp.analysis / "s7_code_leaning_damage_by_source.csv", float_precision="round_trip")
    gh = pd.read_csv(inp.analysis / "s7_code_leaning_damage.csv", float_precision="round_trip").set_index("rung")
    src, docs = strata["sources"], strata["documents"]
    rows = []
    for n, c in group.items():
        e = excess_matrix(sd, [c])[0]
        for label, source in CODE_LEANING_SOURCES.items():
            mask = src == source
            d = docs[mask]
            n_docs = int(np.unique(d).size)
            value = float(e[mask].mean())
            want = float(gh.loc[f"G{n}", "D_github"]) if source == "Github" else float(by[(by.rung == f"G{n}") & (by.source == source) & (by.set == "group")].iloc[0]["D"])
            assert value == want, f"{source}, {n} members: the damage {value!r} is not the committed {want!r}"
            iv = interval_or_none(doc_means(document_resample(d, inp.replicates, (inp.master_seed, "boot_docs", "E_lab", source)), e[mask]), n_docs) if n_docs >= 10 else None
            rows.append({"source": label, "size": n, "set": "E_lab", "damage": value, "lo": iv[0] if iv else float("nan"), "hi": iv[1] if iv else float("nan"), "n_rows": int(mask.sum()), "n_documents": n_docs})
    return pd.DataFrame(rows)


def code_edit_panel_numbers(inp: Inputs) -> pd.DataFrame:
    """Per panel of the five sources and edit size: the group's damage on the panel with its 95 percent document-bootstrap interval, exactly
    as analysis_s12 computes them (the same functions, documents, and seed)."""
    from vpd_audit import analysis_s12 as a12
    from vpd_audit import stats_s12 as s12

    assert inp.tier7_root is not None, "the panel variants need the tier-7 stores"
    docs_of = a12._panel_index_documents(inp.analysis / "s12" / "panel_document_index.csv")
    rows = []
    for label, panel in PANEL_OF_SOURCE.items():
        s = a12.load_store(inp.tier7_root / f"{panel}__panel_edit")
        docs = docs_of(panel)
        n_docs = int(np.unique(docs).size)
        rs = s12.document_resample(docs, inp.replicates, (inp.master_seed, "boot_docs", "s12_panel", panel))
        for n in EDIT_SIZES:
            h, t = a12.panel_damage(s, inp.run, panel, n, s.n_draws)
            v = s12.edit_statistics(h, t, rs, n_docs)
            iv = v["H_interval"] or [float("nan"), float("nan")]
            rows.append({"source": label, "size": n, "set": panel, "damage": v["H"], "lo": iv[0], "hi": iv[1], "n_rows": v["n_rows"], "n_documents": n_docs})
    return pd.DataFrame(rows)


# ----------------------------------------------------------------------------- the canary at the committed levels


def interval_canary(inp: Inputs) -> dict[str, Any]:
    """The points and the intervals through the functions and resamples of the figures, at the committed levels, against the committed
    tables: the merges' U, P, M of the matched-control comparison and their intervals at each rung's level_m (fig7_marginal_control.csv, full precision); curve 1's
    whole-text points at the m `stats.compared_rungs` gives the committed chain (the union tables' half-widths at full precision, their
    printed intervals to their digits); the similar-donors points at the run's m (s9_run2_curves.csv, full precision); the code edit's
    damages (asserted in `code_edit_lab_numbers`). Raises AssertionError on the first difference. Needs no tier-7 store. Always at the
    committed tables' own replicate count, whatever the figures are drawn with."""
    from vpd_audit.stats import N_REPLICATES

    base = Inputs(inp.run, inp.results_root, None, inp.master_seed, N_REPLICATES)
    out: dict[str, Any] = {}
    sd, cells = e_data(base)
    f7 = pd.read_csv(inp.analysis / "fig7_marginal_control.csv", float_precision="round_trip", dtype={"rung": str}).set_index("rung")
    levels = {ctl: {r: int(f7.loc[r, "level_m"]) for r in f7.index} for ctl in ("none", "plain", "marginal")}
    m_real, m_plain = committed_curve1_chain(base, "none")[1], committed_curve1_chain(base, "plain")[1]
    levels["none"]["4"], levels["plain"]["4"] = m_real, m_plain
    t = aggregation_curve_numbers(base, sd, cells, levels=levels).set_index(["control", "rung"])
    checks = []
    for col, ctl in (("U", "none"), ("P", "plain"), ("M", "marginal")):
        for r in f7.index:
            got = t.loc[(ctl, r)]
            want = (float(f7.loc[r, col]), float(f7.loc[r, f"{col}_low"]), float(f7.loc[r, f"{col}_high"]))
            assert (got.rise, got.rise_lo, got.rise_hi) == want, f"{col} at rung {r} (m {got.m}): {(got.rise, got.rise_lo, got.rise_hi)} against the committed {want}"
            checks.append(f"{col} r{r} m{got.m}")
    for ctl, name in (("none", "union_E_D_unif_tau0.1_r0_excl_ctl-none.csv"), ("plain", "union_E_D_unif_tau0.1_r0_excl_ctl-plain.csv")):
        u = pd.read_csv(inp.analysis / name, float_precision="round_trip", dtype={"rung": str}).set_index("rung")
        got = t.loc[(ctl, "4")]
        assert got.rise == float(u.loc["4", "excess"]) and got.half_width == float(u.loc["4", "half_width"]) and got.mean_kl == float(u.loc["4", "mean_kl"]), f"curve 1 ({ctl}), the whole text at m {got.m}: {got.rise}, {got.half_width}, {got.mean_kl} against {u.loc['4', ['excess', 'half_width', 'mean_kl']].tolist()}"
        assert f"[{got.rise_lo:+.4f}, {got.rise_hi:+.4f}]" == u.loc["4", "interval"], f"curve 1 ({ctl}), the whole text: the printed interval {u.loc['4', 'interval']}"
        checks.append(f"curve 1 {ctl} whole text m{got.m}")
    out["aggregation_curve"] = {"checks": checks, "m_curve_1": m_real, "m_curve_1_plain": m_plain}
    strata = e_lab_strata(base)
    sd_lab, cells_lab = e_lab_data(base)
    r2 = pd.read_csv(inp.analysis / "s9b" / "s9_run2_curves.csv", float_precision="round_trip", dtype={"size": str})
    ms = sorted(set(r2[r2.stratum.isin(["G", "P"])]["m"].astype(int)))
    rungs_committed = sorted(set(r2[(r2.stratum == "G") & (r2.arm == "C")]["size"]))
    from vpd_audit import stats as st

    m_run = len(st.compared_rungs(rungs_committed, "union"))
    assert ms == [m_run], f"the committed run's m {ms} is not what compared_rungs gives its sizes ({m_run})"
    t2 = similar_donors_numbers(base, sd_lab, cells_lab, strata, m=m_run)
    arm_of = {"code donors": "C", "general donors": "U", "prose donors": "P"}
    st_of = {"code": "G", "prose": "P"}
    checks2 = 0
    for _, row in t2.iterrows():
        w = r2[(r2.arm == arm_of[row.donors]) & (r2.stratum == st_of[row.texts]) & (r2["size"] == row.rung)]
        assert len(w) == 1, (row.donors, row.texts, row.rung)
        w = w.iloc[0]
        assert (row.rise, row.rise_lo, row.rise_hi) == (float(w.rise), float(w.interval_documents_lo), float(w.interval_documents_hi)), f"{row.donors} on the {row.texts} texts at {row.rung}: {(row.rise, row.rise_lo, row.rise_hi)} against {(w.rise, w.interval_documents_lo, w.interval_documents_hi)}"
        checks2 += 1
    out["similar_donors"] = {"n_points": checks2, "m": m_run}
    out["code_edit"] = {"n_bars": int(len(code_edit_lab_numbers(base, strata)))}
    return out


# ----------------------------------------------------------------------------- the figures


MERGE_LINES: list[tuple[str, str, str, str, str]] = [("none", BLUE, BLUE_DARK, "o", "Components Donor Tokens Need"),
                                                     ("marginal", VERMILLION, VERMILLION_DARK, "D", "Frequency-Matched Random Components"),
                                                     ("plain", ORANGE, ORANGE_DARK, "s", "Uniform Random Components")]
SIMILAR_LINES: list[tuple[str, str, str, str, str]] = [("code donors", PURPLE, PURPLE_DARK, "^", "Code Donors"), ("general donors", BLUE, BLUE_DARK, "o", "General Donors"),
                                                       ("prose donors", GREEN, GREEN_DARK, "s", "Prose Donors")]


def aggregation_curve_figure(inp: Inputs, out_dir: Path) -> dict[str, Any]:
    sd, cells = e_data(inp)
    t = aggregation_curve_numbers(inp, sd, cells)
    own = own_explanation_e(inp)
    imp_mean = float(sd.vector(f"{inp.run}/E/ref/importances", "kl_mean").astype(np.float64).mean())
    assert abs(imp_mean - own) <= 1e-12, f"E's own explanation in the committed table {own!r} is not its importances' mean {imp_mean!r}"
    tokens = [x for x in TOKENS if x not in LATER_TOKENS or inp.tier7_root is not None]
    lines, rows = [], []
    for ctl, color, dark, marker, label in MERGE_LINES:
        sub = t[t.control == ctl].set_index("tokens")
        y, lo, hi = (np.array([sub.loc[x, "rise"] + own for x in tokens]), np.array([sub.loc[x, "rise_lo"] + own for x in tokens]), np.array([sub.loc[x, "rise_hi"] + own for x in tokens]))
        whole = None
        if 512 in sub.index:
            w = sub.loc[512]
            whole = (float(w.mean_kl), float(w.rise_lo + own), float(w.rise_hi + own))
        lines.append(Line(color, dark, marker, label, y, lo, hi, whole, tuple(x for x in LATER_TOKENS if x in tokens)))
        for i, x in enumerate(tokens):
            rows.append({"line": label, "donor_tokens": x, "divergence": y[i], "lo": lo[i], "hi": hi[i], "rise": sub.loc[x, "rise"], "rise_lo": sub.loc[x, "rise_lo"], "rise_hi": sub.loc[x, "rise_hi"],
                         "own_explanation": own, "level": "95 percent", "marker": "open" if x in LATER_TOKENS else "filled"})
        if whole is not None:
            rows.append({"line": label, "donor_tokens": "whole donor text", "divergence": whole[0], "lo": whole[1], "hi": whole[2], "rise": sub.loc[512, "rise"], "rise_lo": sub.loc[512, "rise_lo"],
                         "rise_hi": sub.loc[512, "rise_hi"], "own_explanation": own, "level": "95 percent", "marker": "filled"})
    path = draw_aggregation_curve(lines, tokens, own, Path(out_dir) / f"{OUT_NAMES['aggregation_curve']}.png")
    pd.DataFrame(rows).to_csv(path.with_suffix(".csv"), index=False, lineterminator="\n")
    return {"png": path, "rows": len(rows)}


def similar_donors_figure(inp: Inputs, out_dir: Path) -> dict[str, Any]:
    strata = e_lab_strata(inp)
    sd, cells = e_lab_data(inp)
    own = own_explanations(inp, sd, strata)
    t = similar_donors_numbers(inp, sd, cells, strata)
    tokens = [x for x in TOKENS if x not in LATER_TOKENS or inp.tier7_root is not None]
    panels, rows = [], []
    for key, ttl, tcol in (("code", "Code Recipients", PURPLE), ("prose", "Prose Recipients", GREEN)):
        b = own[key]
        lines = []
        for arm, color, dark, marker, label in SIMILAR_LINES:
            sub = t[(t.texts == key) & (t.donors == arm)].set_index("tokens")
            pts = tokens + [512]
            y = np.array([sub.loc[x, "rise"] + b for x in pts])
            lo, hi = np.array([sub.loc[x, "rise_lo"] + b for x in pts]), np.array([sub.loc[x, "rise_hi"] + b for x in pts])
            lines.append(Line(color, dark, marker, label, y, lo, hi, None, tuple(x for x in LATER_TOKENS if x in tokens)))
            for i, x in enumerate(pts):
                rows.append({"recipients": ttl, "donors": label, "donor_tokens": "whole donor text" if x == 512 else x, "divergence": y[i], "lo": lo[i], "hi": hi[i], "rise": sub.loc[x, "rise"],
                             "rise_lo": sub.loc[x, "rise_lo"], "rise_hi": sub.loc[x, "rise_hi"], "own_explanation": b, "level": "95 percent", "marker": "open" if x in LATER_TOKENS else "filled"})
        panels.append(Panel(ttl, tcol, b, lines))
    path = draw_similar_donors(panels, tokens, Path(out_dir) / f"{OUT_NAMES['similar_donors']}.png")
    pd.DataFrame(rows).to_csv(path.with_suffix(".csv"), index=False, lineterminator="\n")
    return {"png": path, "rows": len(rows), "own_explanations": own}


def _bars(table: pd.DataFrame) -> Bars:
    vals, lo, hi = {}, {}, {}
    for n in EDIT_SIZES:
        sub = table[table["size"] == n].set_index("source")
        vals[n] = [float(sub.loc[s, "damage"]) for s in CODE_EDIT_SOURCES]
        lo[n] = [float(sub.loc[s, "lo"]) for s in CODE_EDIT_SOURCES]
        hi[n] = [float(sub.loc[s, "hi"]) for s in CODE_EDIT_SOURCES]
    return Bars(vals, lo, hi)


def code_edit_figures(inp: Inputs, out_dir: Path, variants: tuple[str, ...] = CODE_EDIT_DEFAULT) -> dict[str, Any]:
    """The code edit's variants, from the tier-7 stores where they need them: every bar from the panels (the default), on E_lab
    (document-level bars; none on ArXiv, three documents), and on E_lab with ArXiv's bar from its panel."""
    assert set(variants) <= set(CODE_EDIT_VARIANTS), variants
    strata = e_lab_strata(inp)
    lab = code_edit_lab_numbers(inp, strata)
    panels = code_edit_panel_numbers(inp) if any(v != "lab" for v in variants) else None
    out = {}
    for v in variants:
        name = CODE_EDIT_VARIANTS[v]
        if v == "lab":
            table = lab
            bars = _bars(table)
        elif v == "panels":
            table = panels
            bars = _bars(table)
        else:
            table = pd.concat([lab[lab.source != "ArXiv"], panels[panels.source == "ArXiv"]], ignore_index=True)
            n_docs = int(panels[panels.source == "ArXiv"]["n_documents"].iloc[0])
            n_rows = int(panels[panels.source == "ArXiv"]["n_rows"].iloc[0])
            bars = _bars(table)
            bars.hatched = ("ArXiv",)
            bars.hatched_label = f"ArXiv: {n_rows} Passages from {n_docs} Papers (Another Text Set)"
        path = draw_code_edit(bars, Path(out_dir) / f"{name}.png")
        table.assign(level="95 percent, documents").to_csv(path.with_suffix(".csv"), index=False, lineterminator="\n")
        out[v] = {"png": path}
    return out


def schematics(out_dir: Path) -> dict[str, Any]:
    return {"aggregation_schematic": draw_aggregation_schematic(Path(out_dir) / f"{OUT_NAMES['aggregation_schematic']}.png"),
            "delete_schematic": draw_delete_schematic(Path(out_dir) / f"{OUT_NAMES['delete_schematic']}.png")}


def figures_post(inp: Inputs, out_dir: Path, *, code_edit: tuple[str, ...] = CODE_EDIT_DEFAULT, log: Any = print) -> dict[str, Any]:
    """Every figure of the post into `out_dir`, after the interval canary; refuses without the tier-7 stores."""
    assert inp.tier7_root is not None and Path(inp.tier7_root).is_dir(), f"the post's figures need the tier-7 stores at {inp.tier7_root}"
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    canary = interval_canary(inp)
    log(f"[figures post] interval canary pass: {canary}")
    out = {"canary": canary, **schematics(out_dir), "aggregation_curve": aggregation_curve_figure(inp, out_dir), "similar_donors": similar_donors_figure(inp, out_dir),
           "code_edit": code_edit_figures(inp, out_dir, code_edit)}
    manifest = {"inputs": {"run": inp.run, "results_root": os.path.relpath(inp.results_root, env.PROJECT_ROOT) if env.PROJECT_ROOT in Path(inp.results_root).resolve().parents else str(inp.results_root),
                           "replicates": inp.replicates, "master_seed": inp.master_seed}, "canary": canary, "files": sorted(p.name for p in out_dir.iterdir())}
    (out_dir / "figures_manifest.json").write_text(json.dumps(manifest, indent=2, sort_keys=True, default=str))
    log(f"[figures post] wrote {manifest['files']} -> {out_dir}")
    return out
