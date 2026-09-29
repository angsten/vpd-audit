"""Tier 7: what the launches of the 2- and 4-token merges and of the code-leaning edit on the panels need beside the cells and the loop.

The cells are enumerated in `cells.py` (`tier_7_cells`; the launch subsets `merge_sizes` and `panel_edit` of `SUBSETS_TIER_7`) and run by
the one loop, `cells.run_cells`. Here:

- **The references** each store carries, and nothing more: `importances` (rung 0 of every merge) and `unmasked` on the merge stores;
  `unmasked_delta` (rung 0 of the hard delete, which the loop requires) on the panel stores.
- **The canaries**, re-run under their committed names and tiers (a cell's tier is not in its name, and `enumerate_cells` asserts unique
  names, so they are added per store and never enumerated): on E, the real merge at draw 0, 8 tokens, with its uniform and its
  frequency-matched control; on E_lab, the tier-5 merge at draw 0, 1 token, from each of the three pools; and a store of their own on E_lab,
  `E_lab__panel_edit`, with the code-leaning group's smaller edit and its draw-0 twin. The references of the merge stores are canaries too.
  The analysis holds every canary to its committed per-text divergence bitwise.
- **The sets held before any forward pass** (`assert_sets`): every 2- and 4-token set equals the label-only table's (`merge_sets.csv`, built
  from the caches on CPU before the launch); every panel edit's erased set equals the committed E_lab cell of the same size, draw, and
  control (the sets do not depend on the text they are applied to); every canary's set equals its committed self.
- **The stand-in's panels** for its dry run: disjoint 200-row slices of `simplestories_smoke_1024`, saved under their own names, with
  synthetic documents of three rows (nine documents on the FreeLaw stand-in, so that the path without an interval runs).
"""

from __future__ import annotations

import dataclasses
import time
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from vpd_audit.cells import PANEL_EDIT_SIZES, PANEL_EVAL_SETS, PANEL_ROWS, TAU_PRIMARY, TIER_4, TIER_7, Cell, code_leaning_rung
from vpd_audit.reference import CONDITIONS

SUBSETS: tuple[str, ...] = ("merge_sizes", "panel_edit")
REFERENCE_NAMES: dict[str, tuple[str, ...]] = {"merge_sizes": ("importances", "unmasked"), "panel_edit": ("unmasked_delta",)}
PANEL_CANARY_GROUP = "E_lab__panel_edit"
MERGE_TABLE = "merge_sets.csv"  # the label-only table of the 2- and 4-token sets (s12_labels.label_tables)
STAND_IN_SOURCE_SET = "simplestories_smoke_1024"
STAND_IN_PANELS: dict[str, tuple[int, int]] = {"panel_ArXiv": (0, 200), "panel_Github": (200, 400), "panel_StackExchange": (400, 600), "panel_DM_Mathematics": (600, 800), "panel_FreeLaw": (800, 1000)}
STAND_IN_DOCUMENT_ROWS: dict[str, int] = {"panel_FreeLaw": 23}  # 200 rows in blocks of 23: nine documents; every other stand-in panel: blocks of 3
STAND_IN_DEFAULT_DOCUMENT_ROWS = 3
assert set(STAND_IN_PANELS) == set(PANEL_EVAL_SETS["simplestories"])


def reference_conditions(subset: str) -> tuple[Any, ...]:
    """The subset's references, in `reference.CONDITIONS` order."""
    out = tuple(c for c in CONDITIONS if c.name in REFERENCE_NAMES[subset])
    assert {c.name for c in out} == set(REFERENCE_NAMES[subset]), subset
    return out


def root_name(run: str) -> str:
    """The stores' root beside the run's (results/grid/<run>_s12/), which no frozen loader walks."""
    return f"{run}_s12"


def committed_roots(results_root: Path, run: str) -> tuple[Path, ...]:
    """The committed stores the canaries and the panel edit's sets are held to: the paper's tiers 1 to 4 and the tier-5 stores; the
    stand-in's dry runs."""
    r = Path(results_root)
    if run == "simplestories":
        return (r / "dry_run", r / "dry_run_s7", r / "dry_run_s9")
    return (r / "grid" / run, r / "grid" / f"{run}_s9")


def merge_canary_cells(run: str) -> dict[str, list[Cell]]:
    """Per evaluation set, the merge stores' canaries under their committed names and tiers."""
    e = [Cell(run, "union", "E", "D_unif", TAU_PRIMARY, "r0", "excluded", 0, "2", ctl, tier) for ctl, tier in (("none", 1), ("plain", 2), ("marginal", TIER_4))]
    e_lab = [Cell(run, "union", "E_lab", pool, TAU_PRIMARY, "r0", "excluded", 0, "1", "none", 5) for pool in ("D_code", "D_unif", "D_prose")]
    return {"E": e, "E_lab": e_lab}


def panel_canary_cells(run: str) -> list[Cell]:
    """The panel edit's canary on E_lab: the smaller edit size's group cell and its draw-0 twin, under their committed tier-4 names."""
    size = PANEL_EDIT_SIZES[run][0]
    return [Cell(run, "code_leaning_hard", "E_lab", "D_code", TAU_PRIMARY, "ones", "included", 0, code_leaning_rung(size), ctl, TIER_4) for ctl in ("none", "usage")]


def canary_names(run: str) -> list[str]:
    return [c.name for cs in merge_canary_cells(run).values() for c in cs] + [c.name for c in panel_canary_cells(run)]


def committed_twin(c: Cell) -> str | None:
    """The committed cell whose set a launch cell must carry: a panel edit's is the E_lab cell of the same size, draw, and control; a
    canary is its own twin; a 2- or 4-token merge has none (it is held to the label-only table); a reference has no set."""
    if c.family == "reference":
        return None
    if c.tier == TIER_7 and c.family == "code_leaning_hard":
        return dataclasses.replace(c, eval_set="E_lab", tier=TIER_4).name
    if c.tier == TIER_7:
        return None
    return c.name


def assert_sets(cells: list[Cell], records: dict[str, dict[str, Any]], committed: Any, merge_table: pd.DataFrame | None, *, log: Any = print) -> dict[str, Any]:
    """Before any forward pass: every 2- and 4-token set (and a control's matched set) equals the label-only table's by SHA-256; every panel
    edit's erased set equals its committed E_lab twin's; every canary's set equals its committed self. `merge_table` None is allowed only
    where no merge cell is among `cells`. Raises `tier5.GateFailure` on the first difference."""
    from vpd_audit.tier5 import GateFailure

    table = None if merge_table is None else merge_table.set_index("cell")
    n = {"merge_sets": 0, "merge_matched_sets": 0, "panel_edit_sets": 0, "canaries": 0}
    for c in cells:
        if c.family == "reference":
            continue
        got = records[c.name].get("source_sha256")
        if c.tier == TIER_7 and c.family == "union":
            if table is None or c.name not in table.index:
                raise GateFailure(f"{c.name}: not in the label-only table of the merge sets")
            if table.loc[c.name, "source_sha256"] != got:
                raise GateFailure(f"{c.name}: its set ({str(got)[:16]}) is not the label-only table's ({str(table.loc[c.name, 'source_sha256'])[:16]})")
            n["merge_sets"] += 1
            if c.control != "none":
                want = table.loc[c.name, "matched_source_sha256"]
                if want != records[c.name].get("matched_source_sha256"):
                    raise GateFailure(f"{c.name}: its matched set is not the label-only table's")
                n["merge_matched_sets"] += 1
            continue
        tw = committed_twin(c)
        assert tw is not None, c.name
        if tw not in committed:
            raise GateFailure(f"{c.name}: its committed twin {tw} is in no committed store ({[str(r) for r in committed.roots]})")
        if committed.source_sha256(tw) != got:
            raise GateFailure(f"{c.name}: its set ({str(got)[:16]}) is not its committed twin's {tw} ({str(committed.source_sha256(tw))[:16]})")
        n["panel_edit_sets" if c.tier == TIER_7 else "canaries"] += 1
    log(f"[tier 7] the launch's sets equal the label-only table's and their committed twins' by SHA-256: {n}")
    return n


def committed_subbatch(committed: Any, run: str, eval_set: str) -> int:
    """The sub-batch size of the committed store that holds the evaluation set's importances reference (read from its run manifest)."""
    import json

    name = f"{run}/{eval_set}/ref/importances"
    assert name in committed, f"{name} is in no committed store"
    manifest = json.loads((Path(committed.where[name]) / "run_manifest.json").read_text())
    return int(manifest["subbatch"])


def assert_subbatch(subbatch: int, committed: Any, run: str) -> dict[str, int]:
    """Every tier-7 store runs at its evaluation set's committed sub-batch size: E's for the merge store on E, E_lab's for the merge store on
    E_lab, for the panel edit's canary, and for the panels (which have no store of their own). One launch runs at one size, so the two must
    agree with it."""
    got = {"E": committed_subbatch(committed, run, "E"), "E_lab": committed_subbatch(committed, run, "E_lab")}
    assert all(v == int(subbatch) for v in got.values()), f"the launch's sub-batch {subbatch} is not the committed stores' {got}"
    return got


# ----------------------------------------------------------------------------- the stand-in's panels


def stand_in_set_name(panel: str) -> str:
    """The stand-in's saved set for a panel's evaluation-set name: panel_ArXiv -> panel_dry_ArXiv."""
    assert panel.startswith("panel_"), panel
    return "panel_dry_" + panel[len("panel_"):]


def stand_in_set_map() -> dict[str, str]:
    return {p: stand_in_set_name(p) for p in STAND_IN_PANELS}


def prepare_stand_in_panels(sets_dir: Path | None = None, *, log: Any = print) -> dict[str, str]:
    """The stand-in's panels, written once: disjoint 200-row slices of the stand-in's rows; if a panel exists it must be its slice.
    Returns each panel's ids hash."""
    from vpd_audit import env
    from vpd_audit.data import hash_ids, load_set, save_set

    sd = Path(sets_dir) if sets_dir else env.SETS_DIR
    ids, rows, rec = load_set(STAND_IN_SOURCE_SET, sd)
    out: dict[str, str] = {}
    for panel, (a, b) in STAND_IN_PANELS.items():
        name = stand_in_set_name(panel)
        take, take_rows = ids[a:b], rows[a:b]
        assert take.shape[0] == PANEL_ROWS, (panel, take.shape)
        if (sd / f"{name}.npz").is_file():
            have, have_rows, have_rec = load_set(name, sd)
            assert np.array_equal(have, take) and np.array_equal(have_rows, take_rows), f"{name} exists and is not rows {a} to {b - 1} of {STAND_IN_SOURCE_SET}"
            out[panel] = have_rec["sha256_ids"]
            continue
        save_set(name, take, take_rows, {"source": STAND_IN_SOURCE_SET, "taken": f"rows {a} to {b - 1}", "taken_from_sha256_ids": rec["sha256_ids"], "tokenizer": rec.get("tokenizer"),
                                         "prepared_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"), "stand_in_panel_for": panel}, sd)
        out[panel] = hash_ids(take)
        log(f"[tier 7] wrote the stand-in panel {name}: rows {a} to {b - 1} of {STAND_IN_SOURCE_SET}")
    return out


def stand_in_documents(panel: str, n_rows: int = PANEL_ROWS) -> np.ndarray:
    """A stand-in panel's synthetic documents: consecutive blocks of rows."""
    return np.arange(n_rows, dtype=np.int64) // int(STAND_IN_DOCUMENT_ROWS.get(panel, STAND_IN_DEFAULT_DOCUMENT_ROWS))
