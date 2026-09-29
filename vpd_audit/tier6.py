"""Tier 6: what the binary-union launch needs beside the cells and the loop.

The cells are enumerated in `cells.py` (`tier_6_cells`; the launch subset `binary_union` of `LAUNCH_SUBSETS_S11`, which also selects the
secondary form's two tier-3 cells per draw by predicate) and run by the one loop, `cells.run_cells`, without the tier-5 extras. Here:

- **The store's references and canary**: the references importances, rounded_0 (the primary form's start),
  rounded_0.1 (the secondary's), and unmasked; and one committed headline cell, the fractional union at draw 0, rung 2, under its
  committed tier-1 name. The analysis holds all five bitwise to their committed per-text divergences.
- **The own-named sets of E** for the two binary self-merges: `s9_pre_reads.own_named` on E's label cache (the self-merge's set is the
  one tier 5 built; the rounding is in the mask).
- **The sets held to the committed stores**: every binary cell's named set is the headline union cell's at the same
  draw and rung (tier 1 for 8 and 64 tokens, tier 3's curve1_extra for 16); every look-alike control's set is tier 4's; each binary
  self-merge's set is tier 5's self-merge's. The label-only pre-launch check runs it on the committed stores in git; the launch runs
  it again on the volume's copies before any forward pass.
- **The label-only tables** (on Modal CPU, where the caches live: `modal_app.py::s11_label_tables`) and their local finish, which also
  prints the label gate: the rounded_0 reference's mean divergence on E, the mean number of labels above zero per position of E (the
  pieces rounded_0 switches on), the rounded_0.1 reference's mean divergence, and rounded_0's cross-entropy from the acceptance tables.

    uv run modal run --detach vpd_audit/modal_app.py::s11_label_tables
    uv run modal volume get vpd-audit-cache /results/grid/pre_reads/main/s11 results/grid/pre_reads/main/
    uv run vpd-audit s11-label-checks --finish
"""

from __future__ import annotations

import dataclasses
import hashlib
import json
import os
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from vpd_audit.cells import K_DRAWS, LAUNCH_SUBSETS_S11, TAU_PRIMARY, Cell, enumerate_cells
from vpd_audit.reference import CONDITIONS
from vpd_audit.sources import ROUNDED0_FAMILY

SUBSET = "binary_union"
REFERENCE_NAMES: tuple[str, ...] = ("importances", "rounded_0", "rounded_0.1", "unmasked")
REFERENCE_CONDITIONS = tuple(c for c in CONDITIONS if c.name in REFERENCE_NAMES)  # in reference.CONDITIONS order
assert {c.name for c in REFERENCE_CONDITIONS} == set(REFERENCE_NAMES)
LABELS_FILE, SETS_FILE, MANIFEST_FILE = "labels_E.json", "sets.csv", "manifest.json"
CHECKS_MD, CHECKS_JSON = "checks.md", "checks.json"
LABEL_GATE_EXPECTED = {"labels_above_0_per_position": 203.0, "rounded_0.1_kl": 0.317, "rounded_0_ce": 2.957}  # printed beside, never asserted


def root_name(run: str) -> str:
    """The stores' root beside the run's: results/grid/<run>_s11/, which no frozen loader walks."""
    return f"{run}_s11"


def committed_roots(results_root: Path, run: str) -> tuple[Path, Path]:
    """The committed stores a launch's sets and its canary are held to: the run's tiers 1 to 4, then tier 5 (the self-merge).
    `tier5.CommittedTables` reads a name from the first store that holds it, in this order."""
    return (Path(results_root) / "grid" / run, Path(results_root) / "grid" / f"{run}_s9")


def canary_cells(run: str) -> list[Cell]:
    """The headline's fractional union at draw 0, rung 2, under its committed tier-1 name (the first of the two tier-4 canaries)."""
    return [Cell(run, "union", "E", "D_unif", TAU_PRIMARY, "r0", "excluded", 0, "2", "none", 1)]


def add_store_canary(groups: list[Any], run: str) -> dict[str, list[str]]:
    """The canary joins every tier-6 store on E under its committed name, as the references do (cell names carry no tier and
    `enumerate_cells` asserts that names are unique, so it is never enumerated a second time). Returns the names added per group."""
    added: dict[str, list[str]] = {}
    for g in groups:
        if g.eval_set != "E":
            continue
        have = {c.name for c in g.cells}
        new = [c for c in canary_cells(run) if c.name not in have]
        g.cells.extend(new)
        added[g.name] = [c.name for c in new]
    return added


def reference_cells(run: str) -> list[Cell]:
    from vpd_audit.cells import _references

    return _references(run, "E", 1, conditions=REFERENCE_CONDITIONS)


def launch_cells(run: str, draws: int = K_DRAWS, adaptive: dict[tuple[str, float], tuple[str, ...]] | None = None) -> list[Cell]:
    """The subset's cells as the launch selects them from the whole enumeration (tiers 1 to 6, so that every name is checked unique
    against every tier), in enumeration order; without the references and the canary, which the launch adds per store."""
    every = enumerate_cells(runs=(run,), draws=draws, adaptive=adaptive, tier_4=True, tier_5=True, tier_6=True)
    return [c for c in every if LAUNCH_SUBSETS_S11[SUBSET](c)]


def twin_name(c: Cell) -> str | None:
    """The committed cell whose named set a cell of the launch must carry: for a binary cell, the fractional union at the same draw and
    rung (with the same control: the look-alike sets carry no family); for a binary self-merge, the fractional self-merge; the canary is
    its own twin. None for a reference, which has no set."""
    if c.family == "reference":
        return None
    if c.family in (ROUNDED0_FAMILY, "rounded_own_g"):
        assert c.eval_set == "E" and c.donor_pool == "D_unif" and c.tau == TAU_PRIMARY and c.control in ("none", "marginal") and c.replicate == 0, c.name
        return dataclasses.replace(c, family="union").name
    if c.family == "self_union":
        assert c.own_round is not None, c.name
        return dataclasses.replace(c, own_round=None).name
    assert c.family == "union" and c.control == "none", c.name
    return c.name


def load_inputs(run: str, set_map: dict[str, str], *, cache_dir: Path | None = None, log: Any = print) -> Any:
    """The own-named sets of E from its label cache, through `s9_pre_reads.own_named` (the function the tier-5 launch and its label-only table used)."""
    from vpd_audit.s9_pre_reads import own_named
    from vpd_audit.sources import Cache
    from vpd_audit.tier5 import Tier5Inputs

    cache = Cache.load(f"{set_map['E']}_{run}", cache_dir)
    own = own_named(cache)
    log(f"[tier 6] own-named sets of E ({cache.name}): {own.shape[0]} texts, mean {own.sum(axis=1).mean():.1f} pieces")
    return Tier5Inputs(own={"E": own}, cache_records={"E": {"name": cache.name, "n_sequences": int(cache.n_sequences), "sha256": dict(cache.sha256)}})


def assert_sets_are_committed(cells: list[Cell], records: dict[str, dict[str, Any]], committed: Any, *, log: Any = print) -> dict[str, Any]:
    """Every cell with a twin (`twin_name`) carries the twin's committed named set, by SHA-256; and a look-alike control's matched set
    (the set whose per-matrix counts it copies) is the committed union set of its draw and rung. `records` maps a launch cell to its
    source record (`source_sha256`, and `matched_source_sha256` for a control); `committed` is a `tier5.CommittedTables` over the
    committed roots. A twin absent from every committed store, or a different hash, raises `tier5.GateFailure`. Returns the counts by
    kind and the store each twin was read from."""
    from vpd_audit.tier5 import GateFailure

    def committed_hash(name: str) -> str:
        if name not in committed:
            raise GateFailure(f"{name}: a committed twin that is in no committed store ({[str(r) for r in committed.roots]})")
        return committed.source_sha256(name)

    n = {"binary_named_sets": 0, "look_alike_sets": 0, "look_alike_matched_sets": 0, "self_merge_sets": 0, "canary": 0}
    where: dict[str, str] = {}
    for c in cells:
        tw = twin_name(c)
        if tw is None:
            continue
        want, got = committed_hash(tw), records[c.name].get("source_sha256")
        if not (isinstance(want, str) and want == got):
            raise GateFailure(f"{c.name}: its set ({str(got)[:16]}) is not its committed twin's {tw} ({str(want)[:16]}, in {committed.where[tw]})")
        kind = "canary" if c.family == "union" else ("self_merge_sets" if c.family == "self_union" else ("look_alike_sets" if c.control == "marginal" else "binary_named_sets"))
        n[kind] += 1
        where[c.name] = str(committed.where[tw])
        if c.control == "marginal":
            named = dataclasses.replace(c, family="union", control="none").name
            if committed_hash(named) != records[c.name].get("matched_source_sha256"):
                raise GateFailure(f"{c.name}: its matched set is not the committed union set of its draw and rung ({named})")
            n["look_alike_matched_sets"] += 1
    log(f"[tier 6] the launch's sets equal their committed twins' by SHA-256: {n}")
    return {"counts": n, "twin_store": where}


# ----------------------------------------------------------------------------- the label-only tables (Modal CPU) and their local finish


def label_counts(cache: Any) -> dict[str, Any]:
    """From a label cache, which holds every nonzero label: per position the number of labels above zero (the pieces the rounded_0
    mask switches on), above 0.1, and the number stored; their means over positions, and the sign of the smallest label."""
    indptr, values = np.asarray(cache.indptr, dtype=np.int64), np.asarray(cache.values)
    n_pos = int(indptr.size - 1)

    def per_position(sel: np.ndarray) -> np.ndarray:
        cs = np.zeros(sel.size + 1, dtype=np.int64)
        np.cumsum(sel, out=cs[1:])
        return cs[indptr[1:]] - cs[indptr[:-1]]

    above0, above01 = per_position(values > 0), per_position(values > 0.1)
    stored = np.diff(indptr)
    return {"cache": cache.name, "n_positions": n_pos, "n_sequences": int(cache.n_sequences), "values_dtype": str(values.dtype), "cache_sha256": dict(cache.sha256),
            "mean_labels_above_0_per_position": float(above0.mean()), "mean_labels_above_0.1_per_position": float(above01.mean()), "mean_labels_stored_per_position": float(stored.mean()),
            "max_labels_above_0_at_a_position": int(above0.max()), "n_stored_labels_not_above_0": int((values <= 0).sum()), "min_label": float(values.min()) if values.size else float("nan")}


def label_tables(run: str, out_dir: Path, *, set_map: dict[str, str] | None = None, pool_map: dict[str, str] | None = None, draws: int = K_DRAWS, master_seed: int = 0, cache_dir: Path | None = None,
                 log: Any = print) -> dict[str, Any]:
    """The label-only pre-launch check, the part that needs the label caches, on CPU where they live. Builds the named set of every cell of the launch
    (and of the canary) from the caches exactly as the launch will (`cells.build_sources`, the same D_unif cache, alive vector, marginal
    rates, and E's own-named sets) and writes sets.csv; from E's label cache writes labels_E.json (`label_counts`). No store is read and no
    existing file is written. The local finish (`finish_label_checks`) holds sets.csv to the committed cell tables."""
    from vpd_audit.cells import build_sources
    from vpd_audit.donors import donors_dir
    from vpd_audit.results import code_commits
    from vpd_audit.sources import Cache, source_hash

    set_map = set_map or {"E": "E"}
    pool_map = pool_map or {"D_unif": "D_unif"}
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    d_unif = Cache.load(f"{pool_map['D_unif']}_{run}", cache_dir)
    alive_vec = np.load((cache_dir or donors_dir()) / f"alive_{pool_map['D_unif']}_{run}.npy")
    inputs = load_inputs(run, set_map, cache_dir=cache_dir, log=log)
    cells = launch_cells(run, draws) + canary_cells(run)
    sources = build_sources(cells, {f"D_unif_{run}": d_unif}, {run: (alive_vec, source_hash(alive_vec))}, None, None, dict(d_unif.module_to_c), master_seed=master_seed, log=log,
                            tier5_inputs={run: inputs})
    rows = []
    for c in cells:
        rec = sources[c.name].record
        rows.append({"cell": c.name, "tier": c.tier, "family": c.family, "control": c.control, "draw": c.draw, "rung": c.rung, "own_round": c.own_round, "twin": twin_name(c),
                     "source_sha256": rec["source_sha256"], "matched_source_sha256": rec.get("matched_source_sha256"), "n_on": int(rec["n_on"]["total"]), "named_n_on": int(rec.get("named_n_on", rec["n_on"])["total"])})
    table = pd.DataFrame(rows)
    table.to_csv(out_dir / SETS_FILE, index=False, lineterminator="\n")
    e_cache = Cache.load(f"{set_map['E']}_{run}", cache_dir)
    labels = label_counts(e_cache)
    with open(out_dir / LABELS_FILE, "w") as f:
        json.dump(labels, f, indent=2, sort_keys=True)
    manifest = {"run": run, "draws": draws, "master_seed": master_seed, "n_cells": len(cells), "commits": code_commits(), "caches": {"D_unif": {"name": d_unif.name, "sha256": dict(d_unif.sha256)}, "E": inputs.cache_records["E"]},
                "alive_sha256": source_hash(alive_vec), "sets_csv_sha256": hashlib.sha256((out_dir / SETS_FILE).read_bytes()).hexdigest()}
    with open(out_dir / MANIFEST_FILE, "w") as f:
        json.dump(manifest, f, indent=2, sort_keys=True)
    log(f"[s11 label tables] {len(cells)} sets -> {out_dir / SETS_FILE}; E: {labels['mean_labels_above_0_per_position']:.1f} labels above zero per position (the pieces rounded_0 switches on) -> {out_dir / LABELS_FILE}")
    return {"n_cells": len(cells), "labels": labels, "manifest": manifest}


def _mean_kl(store: Path, cell: str) -> float:
    r = pd.read_parquet(Path(store) / "per_sequence.parquet", columns=["cell", "seq", "kl_mean"])
    r = r[r["cell"] == cell].sort_values("seq")
    assert len(r) and np.array_equal(r["seq"].to_numpy(), np.arange(len(r))), f"{store}: {cell} does not hold every sequence once"
    return float(r["kl_mean"].to_numpy(np.float32).astype(np.float64).mean())


def finish_label_checks(run: str, s11_dir: Path, results_root: Path, *, log: Any = print) -> dict[str, Any]:
    """The label-only pre-launch check, locally, on the pulled label-only tables and the committed stores in git: every set of sets.csv against its
    committed twin (`assert_sets_are_committed`, which raises on the first difference), then the label gate, printed with the expected
    values beside it and never asserted. Writes checks.json and checks.md into the s11 directory (new files)."""
    from vpd_audit.tier5 import CommittedTables

    s11_dir, results_root = Path(s11_dir), Path(results_root)
    table = pd.read_csv(s11_dir / SETS_FILE, dtype={"rung": str})
    with open(s11_dir / LABELS_FILE) as f:
        labels = json.load(f)
    with open(s11_dir / MANIFEST_FILE) as f:
        manifest = json.load(f)
    assert hashlib.sha256((s11_dir / SETS_FILE).read_bytes()).hexdigest() == manifest["sets_csv_sha256"], "sets.csv is not the file its manifest recorded"
    want = {c.name for c in launch_cells(run, int(manifest["draws"])) + canary_cells(run)}
    assert set(table["cell"]) == want and not table["cell"].duplicated().any(), "sets.csv does not hold exactly the launch's cells and the canary"
    committed = CommittedTables(committed_roots(results_root, run))
    by_name = {c.name: c for c in launch_cells(run, int(manifest["draws"])) + canary_cells(run)}
    order = [by_name[n] for n in table["cell"]]
    records = {r["cell"]: {"source_sha256": r["source_sha256"], "matched_source_sha256": r["matched_source_sha256"]} for _, r in table.iterrows()}
    sets = assert_sets_are_committed(order, records, committed, log=log)
    e_store = committed.where[f"{run}/E/ref/rounded_0"]
    acc = pd.read_csv(results_root / "acceptance" / "vs_paper.csv").set_index("condition")
    gate = {"rounded_0_kl_on_E": _mean_kl(e_store, f"{run}/E/ref/rounded_0"), "rounded_0_kl_store": os.path.relpath(e_store, results_root.parent),
            "labels_above_0_per_position": labels["mean_labels_above_0_per_position"], "labels_above_0.1_per_position": labels["mean_labels_above_0.1_per_position"],
            "labels_stored_per_position": labels["mean_labels_stored_per_position"], "stored_labels_not_above_0": labels["n_stored_labels_not_above_0"],
            "rounded_0.1_kl_on_E": _mean_kl(e_store, f"{run}/E/ref/rounded_0.1"), "rounded_0_ce": float(acc.loc["rounded_0", "ce_ours"]), "rounded_0_ce_paper": float(acc.loc["rounded_0", "ce_paper"]),
            "expected": dict(LABEL_GATE_EXPECTED)}
    out = {"run": run, "label_tables_commit": manifest["commits"], "n_sets": int(len(table)), "sets": sets["counts"], "label_gate": gate}
    with open(s11_dir / CHECKS_JSON, "w") as f:
        json.dump(out, f, indent=2, sort_keys=True)
    L = [f"# The label-only checks before launch ({run})", "",
         f"Label tables built on CPU at commit {manifest['commits'].get('project', '?')[:12]} (dirty flag {manifest['commits'].get('dirty')}), {manifest['draws']} draws, master seed {manifest['master_seed']}.", "",
         f"- Every set of the launch equals its committed twin's by SHA-256, and every look-alike control's matched set is the committed union set of its draw and rung: {sets['counts']} ({len(table)} rows of sets.csv).", "",
         "The label gate (printed, not asserted):", "",
         f"- rounded_0 reference, mean divergence on E (committed store {gate['rounded_0_kl_store']}): {gate['rounded_0_kl_on_E']:.4f} nats",
         f"- labels above zero per position of E, from its label cache (the pieces rounded_0 switches on): {gate['labels_above_0_per_position']:.1f} (expected about {LABEL_GATE_EXPECTED['labels_above_0_per_position']:.0f}); "
         f"stored per position {gate['labels_stored_per_position']:.1f}; stored labels not above zero {gate['stored_labels_not_above_0']}; above 0.1 per position {gate['labels_above_0.1_per_position']:.1f}",
         f"- rounded_0.1 reference, mean divergence on E: {gate['rounded_0.1_kl_on_E']:.4f} nats (expected about {LABEL_GATE_EXPECTED['rounded_0.1_kl']})",
         f"- rounded_0 cross-entropy from results/acceptance/vs_paper.csv: {gate['rounded_0_ce']:.4f} (expected {LABEL_GATE_EXPECTED['rounded_0_ce']}; the paper's {gate['rounded_0_ce_paper']})", ""]
    (s11_dir / CHECKS_MD).write_text("\n".join(L))
    log("\n".join(L))
    return out
