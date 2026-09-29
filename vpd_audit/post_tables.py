"""Three descriptive tables for the post, from committed stores only (CPU, read-only, no model and no label cache).

- **The hard delete of random alive components, per draw** (`hard_delete_per_draw.csv`): for each draw of rung 1 on E, the count of
  components deleted and the rise over the rung-0 reference `unmasked_delta` (`analysis.excess_matrix`, the mean over E's texts), for the
  random-alive control of the hard delete (`hard_zero/D_unif/tau0.1/ones/incl/k<k>/r1/ctl-plain`, tier 2) and beside it the deletion of as
  many never-needed components (`never_named_hard/D_unif/tau0.1/ones/incl/k<k>/r1`, tier 3). The counts and the means over the draws are
  held to the committed never-named table (`fig4_never_named.csv`, rung 1), the means exactly.
- **The editing guarantee's coverage on the panels** (`panel_coverage.csv`): for the code-leaning group at 256 and 1,007 members on the
  non-code panels with label caches (StackExchange, ArXiv, Pile-CC, Wikipedia), at the qualifying thresholds tau_q = 0.1 and 0, the
  clean-prefix share of positions and the count of contributing texts, `stats.readability` on the loop's first touched positions (the
  store's `t_star_<tau_q>` column): the definitions of the committed E_lab table (`s7_code_leaning_conditional.csv`), which
  `analysis_s7` computed the same way from the committed code-leaning store. A contributing text has t* >= 8; the clean-prefix share is
  the mean over texts of t*/512.
- **The code edit on E_lab with document-level intervals** (`code_edit_E_lab_document_intervals.csv`): the code-edit figure's E_lab
  numbers, `figures_post.code_edit_lab_numbers` (the damages held to the committed tables, 95 percent intervals over each source's
  documents, none below ten documents), in the columns of that figure's CSV.

All write into `results/grid/analysis/<run>/s12/` with a manifest of the code commit and the checks.

    uv run vpd-audit post-tables
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from vpd_audit import env

HARD_DELETE_FILE = "hard_delete_per_draw.csv"
COVERAGE_FILE = "panel_coverage.csv"
CODE_EDIT_E_LAB_FILE = "code_edit_E_lab_document_intervals.csv"
MANIFEST_FILE = "post_tables_manifest.json"
HARD_DELETE_RUNG = "1"
DRAWS = 8
TAU_QS: tuple[str, ...] = ("0.1", "0")
EDIT_SIZES: tuple[int, int] = (256, 1007)
COVERAGE_PANELS: dict[str, str] = {"StackExchange": "panel_StackExchange", "ArXiv": "panel_ArXiv", "Pile-CC": "panel_Pile_CC", "Wikipedia (en)": "panel_Wikipedia__en_"}


def _cell(run: str, family: str, eval_set: str, pool: str, draw: int, rung: str, control: str, tier: int) -> Any:
    from vpd_audit.cells import TAU_PRIMARY, Cell

    return Cell(run, family, eval_set, pool, TAU_PRIMARY, "ones", "included", draw, rung, control, tier)


def _n_on(store: Path, names: list[str]) -> list[int]:
    ct = pd.read_parquet(Path(store) / "cells.parquet", columns=["cell", "n_on"]).set_index("cell")
    missing = [n for n in names if n not in ct.index]
    assert not missing, f"{store}: no cell {missing[:2]}"
    return [int(ct.loc[n, "n_on"]) for n in names]


# ============================================================================= the hard delete per draw


def hard_delete_per_draw(results_root: Path, run: str = "main") -> tuple[pd.DataFrame, dict[str, Any]]:
    """Per draw at rung 1 on E: the random-alive hard delete and the never-needed deletion, each with its count of components and its
    rise over `unmasked_delta`. Asserts that the reference is `unmasked_delta`, that both stores carry it bitwise, and that the counts and
    the means over the draws are the committed never-named table's (the means exactly)."""
    from vpd_audit.analysis import excess_matrix, ref_cell_name
    from vpd_audit.figures_post import set_data

    grid = Path(results_root) / "grid" / run
    alive_store, never_store = grid / "tier2" / "E", grid / "tier3" / "E__never_named"
    alive = [_cell(run, "hard_zero", "E", "D_unif", k, HARD_DELETE_RUNG, "plain", 2) for k in range(DRAWS)]
    never = [_cell(run, "never_named_hard", "E", "D_unif", k, HARD_DELETE_RUNG, "none", 3) for k in range(DRAWS)]
    reference = f"{run}/E/ref/unmasked_delta"
    assert {ref_cell_name(c) for c in alive + never} == {reference}, "the rung-0 reference of both deletions is unmasked_delta"
    sd = set_data("E", [(alive_store, [c.name for c in alive]), (never_store, [c.name for c in never])], reference)
    e_alive, e_never = excess_matrix(sd, alive), excess_matrix(sd, never)  # (K, N)
    n_alive, n_never = _n_on(alive_store, [c.name for c in alive]), _n_on(never_store, [c.name for c in never])
    table = pd.DataFrame({"draw": np.arange(DRAWS), "random_alive_n_components": n_alive, "random_alive_rise": e_alive.mean(axis=1),
                          "never_needed_n_components": n_never, "never_needed_rise": e_never.mean(axis=1),
                          "random_alive_cell": [c.name for c in alive], "never_needed_cell": [c.name for c in never]})
    committed_path = Path(results_root) / "grid" / "analysis" / run / "fig4_never_named.csv"
    committed = pd.read_csv(committed_path, float_precision="round_trip", dtype={"rung": str}).set_index("rung").loc[HARD_DELETE_RUNG]
    want_n = json.loads(committed["n_per_draw"])
    checks = {"reference": reference, "n_texts": int(e_alive.shape[1]),
              "random_alive_mean": float(e_alive.mean()), "random_alive_mean_committed": float(committed["alive_control_mean"]),
              "never_needed_mean": float(e_never.mean()), "never_needed_mean_committed": float(committed["D_mean"]),
              "n_per_draw_committed": want_n, "committed_table": str(committed_path.relative_to(Path(results_root).parent)) if Path(results_root).parent in committed_path.parents else str(committed_path)}
    assert n_alive == want_n and n_never == want_n, f"the counts per draw {n_alive}, {n_never} are not the committed {want_n}"
    assert checks["random_alive_mean"] == checks["random_alive_mean_committed"], (checks["random_alive_mean"], checks["random_alive_mean_committed"])
    assert checks["never_needed_mean"] == checks["never_needed_mean_committed"], (checks["never_needed_mean"], checks["never_needed_mean_committed"])
    return table, checks


# ============================================================================= the guarantee's coverage


def t_star_matrix(store: Path, names: list[str], tau_q: str) -> np.ndarray:
    """(K, N): the store's first touched positions at `tau_q` for the given cells, rows in the order of `names`, texts in order."""
    col = f"t_star_{tau_q}"
    r = pd.read_parquet(Path(store) / "per_sequence.parquet", columns=["cell", "seq", col])
    out = []
    for n in names:
        g = r[r["cell"] == n].sort_values("seq")
        assert len(g) and np.array_equal(g["seq"].to_numpy(), np.arange(len(g))), f"{store}: {n} does not hold every text once"
        out.append(g[col].to_numpy(np.int64))
    assert len({v.size for v in out}) == 1, f"{store}: the cells hold different numbers of texts"
    return np.stack(out)


def coverage(store: Path, names: list[str], tau_q: str, mask: np.ndarray | None = None) -> dict[str, Any]:
    """`stats.readability` on the cells' first touched positions at `tau_q` (the texts in `mask` if given): the mean over the cells (draws)
    of the count of texts with t* >= 8 and of the mean over texts of t*/T."""
    from vpd_audit import stats as st

    t = t_star_matrix(store, names, tau_q)
    if mask is not None:
        assert mask.dtype == np.bool_ and mask.shape == (t.shape[1],), (mask.dtype, mask.shape, t.shape)
        t = t[:, mask]
    read = st.readability(t)
    return {"n_texts": int(t.shape[1]), "n_draws": int(t.shape[0]), "mean_n_contributing": read["mean_n_contributing"], "mean_clean_prefix_fraction": read["mean_clean_prefix_fraction"]}


def panel_coverage(results_root: Path, run: str = "main") -> pd.DataFrame:
    """Per panel of `COVERAGE_PANELS`, edit size, and tau_q: the group's coverage on the whole panel, from its tier-7 store."""
    from vpd_audit import tier7 as t7m
    from vpd_audit.cells import code_leaning_rung

    root = Path(results_root) / "grid" / t7m.root_name(run) / "tier7"
    rows = []
    for source, panel in COVERAGE_PANELS.items():
        store = root / f"{panel}__panel_edit"
        for n in EDIT_SIZES:
            cell = _cell(run, "code_leaning_hard", panel, "D_code", 0, code_leaning_rung(n), "none", 7).name
            for tq in TAU_QS:
                c = coverage(store, [cell], tq)
                rows.append({"source": source, "panel": panel, "n_members": n, "set": "group", "tau_q": tq, "n_texts": c["n_texts"], "mean_n_contributing": c["mean_n_contributing"],
                             "mean_clean_prefix_fraction": c["mean_clean_prefix_fraction"], "cell": cell})
    return pd.DataFrame(rows)


def code_edit_e_lab(results_root: Path, run: str = "main") -> pd.DataFrame:
    """The code edit on E_lab by source and edit size, with its document-level 95 percent intervals: exactly the rows and columns the
    code-edit figure's E_lab variant writes beside its PNG."""
    from vpd_audit import figures_post as F

    inp = F.paper_inputs(results_root, run, with_tier7=False)
    return F.code_edit_lab_numbers(inp, F.e_lab_strata(inp)).assign(level="95 percent, documents")


# ============================================================================= the command


def post_tables(out_dir: Path | None = None, results_root: Path | None = None, run: str = "main", *, log: Any = print) -> dict[str, Any]:
    from vpd_audit.results import code_commits

    root = Path(results_root or env.PROJECT_ROOT / "results")
    out = Path(out_dir or root / "grid" / "analysis" / run / "s12")
    out.mkdir(parents=True, exist_ok=True)
    hd, hd_checks = hard_delete_per_draw(root, run)
    hd.to_csv(out / HARD_DELETE_FILE, index=False, lineterminator="\n")
    log(f"[post tables] hard delete at rung 1: random alive {hd_checks['random_alive_mean']:.4f} on average (per draw {hd.random_alive_rise.min():.4f} to {hd.random_alive_rise.max():.4f}); "
        f"never needed {hd_checks['never_needed_mean']:.6f}; the committed means reproduced exactly")
    cov = panel_coverage(root, run)
    cov.to_csv(out / COVERAGE_FILE, index=False, lineterminator="\n")
    log("[post tables] coverage: " + "; ".join(f"{r.source} {r.n_members} tau_q {r.tau_q}: clean prefix {r.mean_clean_prefix_fraction:.4f}, contributing {r.mean_n_contributing:.0f}" for r in cov.itertuples()))
    ce = code_edit_e_lab(root, run)
    ce.to_csv(out / CODE_EDIT_E_LAB_FILE, index=False, lineterminator="\n")
    log(f"[post tables] the code edit on E_lab: {len(ce)} bars, document intervals on {int(ce['lo'].notna().sum())}")
    manifest = {"run": run, "commits": code_commits(), "hard_delete": hd_checks, "coverage": {"panels": COVERAGE_PANELS, "edit_sizes": list(EDIT_SIZES), "tau_qs": list(TAU_QS)},
                "files": [HARD_DELETE_FILE, COVERAGE_FILE, CODE_EDIT_E_LAB_FILE]}
    (out / MANIFEST_FILE).write_text(json.dumps(manifest, indent=2, sort_keys=True, default=str))
    return {"hard_delete": hd, "coverage": cov, "code_edit_e_lab": ce, "checks": hd_checks, "out_dir": out}
