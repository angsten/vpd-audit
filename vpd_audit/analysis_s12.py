"""The reading of tier 7: the code-leaning edit on the panels, and the merge points at 2 and 4 donor tokens. CPU only, read-only.

It loads the tier-7 stores (`results/grid/<run>_s12/tier7/`: the merge stores on E and E_lab, one store per panel, and the panel edit's
canary store on E_lab), asserts what must hold before anything is read, and writes `report.md` with one CSV per table
(`results/grid/analysis/<run>/s12/`).

**Before anything is read.** The guard: for a store of the paper's model the working tree must be clean, `--freeze` must name the freeze
commit, this module's and stats_s12.py's blobs on disk must be their blobs at HEAD and at the freeze, and each of the nine frozen modules
must be its blob on `main` (printed, module by module). Then every store: complete, every cell holding every text once, exactly the
launch's cells, no failure recorded in the launch summaries; each panel store run on its saved panel (by ids hash). **The canaries**: the
merge stores' references and their re-run committed cells, and the panel edit's canary store (its reference, the smaller edit, and its
draw-0 twin), reproduce their committed per-text divergences bitwise. Every set is held again to the label-only table and to its committed
twin (`tier7.assert_sets`, on the stores' own cell tables).

**The panels.** For each panel and edit size: H, T, rho with their document-bootstrap intervals (stats_s12), and the reading. The decisive
panel is ArXiv: keep, drop, or soften by `stats_s12.reading` at 95 percent. Three candidates (DM Mathematics, PubMed Central, FreeLaw) are
read by the same rule at 1 - 0.05/3, printed under a heading that says it applies only if ArXiv reads drop. Every other panel is described
with the same numbers and the same rule, read by nothing. Beside them: for GitHub, StackExchange, Pile-CC, and Wikipedia, the panel's H next
to the committed E_lab value with its document-level interval (a replication; the E_lab values are asserted equal to the committed
by-source damages); for the panels with label caches, the damage per unit of removed label (H/omega for the group, T/omega for the twins)
beside rho, and the panels' order by omega against their order by H, overall and for the pairs StackExchange/ArXiv and Pile-CC/Wikipedia.

**The merge points.** On E, the real merge, the frequency-matched control, and the uniform control at 1, 2, 4, and 8 donor tokens (1 and 8
from the committed stores, 2 and 4 from the tier-7 store): the rise over the text's own explanation, its 95 percent interval from the text
bootstrap of E (seed (master, "boot", "E"), shared by the three lines, the draws held fixed), the per-draw means, and the real merge minus the
matched control per draw and paired. On E_lab, the three donor pools on the code texts and on the prose texts, with the stratified document
bootstrap of `stats_s9.stratified_document_resample` (seed (master, "boot_docs", "E_lab", source)) at 95 percent. Descriptions, read by no rule.

    uv run vpd-audit analyze-s12 --run main --freeze <the freeze commit>
    uv run vpd-audit analyze-s12 --dry
"""

from __future__ import annotations

import json
import os
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable

import numpy as np
import pandas as pd

from vpd_audit import env
from vpd_audit import stats as st
from vpd_audit import stats_s9 as s9
from vpd_audit import stats_s12 as s12
from vpd_audit.cells import PANEL_EDIT_SIZES, PANEL_EVAL_SETS, TAU_PRIMARY, Cell, _references, code_leaning_rung, tier_7_cells

FROZEN_MODULES: tuple[str, ...] = ("stats.py", "stats_s7.py", "stats_s9.py", "analysis.py", "analysis_s7.py", "analysis_s9.py", "figures.py", "figures_s7.py", "figures_s9.py")
THIS_MODULES: tuple[str, ...] = ("analysis_s12.py", "stats_s12.py")
RECORDED_MODULES: tuple[str, ...] = ("cells.py", "grid.py", "sources.py", "masks.py", "code_leaning.py", "tier5.py", "tier7.py", "two_paths.py", "s9_checks.py", "s12_labels.py")
PAPER_RUNS: tuple[str, ...] = ("main", "control")
MERGE_RUNGS: tuple[str, ...] = ("1", "T2", "T4", "2")
TOKENS: dict[str, int] = {"1": 1, "T2": 2, "T4": 4, "2": 8}
COMMITTED_MERGE_RUNGS: tuple[str, ...] = ("1", "2")
LINES: dict[str, str] = {"real merge": "none", "frequency-matched": "marginal", "uniform random": "plain"}
COMMITTED_TIER: dict[str, int] = {"none": 1, "plain": 2, "marginal": 4}
ARMS: dict[str, str] = {"code donors": "D_code", "general donors": "D_unif", "prose donors": "D_prose"}
DECISIVE = "panel_ArXiv"
CANDIDATES: tuple[str, ...] = ("panel_DM_Mathematics", "panel_PubMed_Central", "panel_FreeLaw")
REPLICATION: dict[str, str] = {"panel_Github": "Github", "panel_StackExchange": "StackExchange", "panel_Pile_CC": "Pile-CC", "panel_Wikipedia__en_": "Wikipedia (en)"}
ORDER_PAIRS: tuple[tuple[str, str], ...] = (("panel_StackExchange", "panel_ArXiv"), ("panel_Pile_CC", "panel_Wikipedia__en_"))
PANEL_WORDS: dict[str, str] = {"panel_Github": "GitHub", "panel_StackExchange": "StackExchange", "panel_ArXiv": "ArXiv", "panel_Pile_CC": "Pile-CC", "panel_Wikipedia__en_": "Wikipedia",
                               "panel_DM_Mathematics": "DM Mathematics", "panel_PubMed_Central": "PubMed Central", "panel_FreeLaw": "FreeLaw"}
POST_WORDS: dict[str | None, str] = {s12.KEEP: "ArXiv is damaged, more than by deleting as many equally used random components",
                                     s12.DROP: "the claim of notable collateral damage on ArXiv is unsupported, whatever rho is",
                                     s12.SOFTEN: "ArXiv is not spared the way web text and Wikipedia are",
                                     None: "no reading (fewer than ten documents)"}
X = s12.X


# ----------------------------------------------------------------------------- what the reading is run on


@dataclass
class Spec:
    run: str
    store_root: Path  # the tier-7 root
    out_dir: Path
    committed_roots: tuple[Path, ...]
    merge_table: Path  # the label-only table of the 2- and 4-token sets
    panels: tuple[str, ...]
    edit_sizes: tuple[int, int]
    panel_documents: Callable[[str], np.ndarray]  # a panel's document per row, in row order
    e_lab_sources: list[str]  # E_lab's source per row
    e_lab_documents: np.ndarray  # E_lab's document codes per row, distinct across sources
    code_sources: tuple[str, ...]
    prose_sources: tuple[str, ...]
    omega_table: Path | None = None  # the removed label on the panels with label caches
    panel_set_hashes: dict[str, str] | None = None  # each panel's ids hash from the committed manifests
    by_source_damage: Path | None = None  # s7_code_leaning_damage_by_source.csv, for the replication's equality
    github_damage: Path | None = None  # s7_code_leaning_damage.csv
    n_e: int | None = None  # the paper's sizes, asserted
    n_draws: int | None = None
    notes: dict[str, Any] = field(default_factory=dict)


def _panel_index_documents(index_csv: Path) -> Callable[[str], np.ndarray]:
    index = pd.read_csv(index_csv)

    def docs(panel: str) -> np.ndarray:
        g = index[index["panel"] == panel].sort_values("row")
        assert len(g) and g["row"].tolist() == list(range(len(g))), f"{panel}: the document index does not hold every row once"
        return g["majority_document"].to_numpy(np.int64)

    return docs


def paper_spec(results_root: Path | None = None, run: str = "main") -> Spec:
    """The paper's model: the committed document indexes (the panels' in analysis/<run>/s12/, E_lab's in analysis/<run>/s9/), the label-only
    table of the merge sets and the removed label (pre_reads/<run>/s12/), the committed manifests' panel hashes, and the committed by-source damages."""
    from vpd_audit import s9_checks
    from vpd_audit import tier7 as t7m

    r = Path(results_root or env.PROJECT_ROOT / "results")
    idx = pd.read_csv(r / "grid" / "analysis" / run / "s9" / "document_index.csv")
    el = idx[idx["set"] == "E_lab"].sort_values("row").reset_index(drop=True)
    labeled = json.loads((r / "data" / "labeled_manifest.json").read_text())["sets"]
    cached = json.loads((r / "grid" / "analysis" / run / "s9b" / "panel_manifest.json").read_text())["panels"]
    hashes = {p: (labeled.get(p, {}).get("sha256_ids") or cached.get(p, {}).get("set_sha256_ids")) for p in PANEL_EVAL_SETS[run]}
    return Spec(run=run, store_root=r / "grid" / t7m.root_name(run) / "tier7", out_dir=r / "grid" / "analysis" / run / "s12", committed_roots=t7m.committed_roots(r, run),
                merge_table=r / "grid" / "pre_reads" / run / "s12" / t7m.MERGE_TABLE, panels=PANEL_EVAL_SETS[run], edit_sizes=PANEL_EDIT_SIZES[run],  # type: ignore[arg-type]
                panel_documents=_panel_index_documents(r / "grid" / "analysis" / run / "s12" / "panel_document_index.csv"), e_lab_sources=[str(s) for s in el["source"]],
                e_lab_documents=s9_checks.document_codes(idx, "E_lab", 0, len(el)), code_sources=("Github",), prose_sources=("Pile-CC", "Wikipedia (en)"),
                omega_table=r / "grid" / "pre_reads" / run / "s12" / "removed_label_panels.csv", panel_set_hashes=hashes,
                by_source_damage=r / "grid" / "analysis" / run / "s7_code_leaning_damage_by_source.csv", github_damage=r / "grid" / "analysis" / run / "s7_code_leaning_damage.csv", n_e=1024, n_draws=8)


def stand_in_spec(results_root: Path | None = None, sets_dir: Path | None = None) -> Spec:
    """The stand-in: its tier-7 dry run, its committed dry-run stores, its label-only table, the stand-in panels' synthetic documents, and
    E_lab_dry's strata with synthetic documents of three rows (`analysis_s9.STAND_IN_DOCUMENT_ROWS`). No label caches of the panels, so no omega."""
    from vpd_audit import s9_checks
    from vpd_audit import tier7 as t7m
    from vpd_audit.analysis_s9 import STAND_IN_DOCUMENT_ROWS

    r = Path(results_root or env.PROJECT_ROOT / "results")
    inp = s9_checks.S9Inputs(run="simplestories", set_map={"E": "E_dry", "E_lab": "E_lab_dry"}, pool_map={"D_unif": "D_unif_dry", "D_code": "D_code_dry", "D_prose": "D_prose_dry"}, pairs=(), regression=None,
                             synthetic_document_rows=STAND_IN_DOCUMENT_ROWS)
    idx = s9_checks.inputs_document_index(inp)
    el = idx[idx["set"] == "E_lab"].sort_values("row").reset_index(drop=True)
    return Spec(run="simplestories", store_root=r / "dry_run_s12" / "tier7", out_dir=r / "dry_run_s12" / "analysis", committed_roots=t7m.committed_roots(r, "simplestories"),
                merge_table=r / "dry_run_s12" / "pre_reads" / "s12" / t7m.MERGE_TABLE, panels=PANEL_EVAL_SETS["simplestories"], edit_sizes=PANEL_EDIT_SIZES["simplestories"],  # type: ignore[arg-type]
                panel_documents=t7m.stand_in_documents, e_lab_sources=[str(s) for s in el["source"]], e_lab_documents=s9_checks.document_codes(idx, "E_lab", 0, len(el)),
                code_sources=("dialogue",), prose_sources=("narration",), notes={"stand_in": True})


# ----------------------------------------------------------------------------- the guard


def _git(*args: str) -> str:
    return subprocess.run(["git", "-C", str(env.PROJECT_ROOT), *args], check=True, capture_output=True, text=True).stdout.strip()


def _blob(rev: str | None, module: str) -> str | None:
    if rev is None:
        return None
    try:
        return _git("rev-parse", f"{rev}:vpd_audit/{module}")
    except subprocess.CalledProcessError:
        return None


def freeze_guard(freeze: str | None, *, enforce: bool, against: str = "main", log: Any = None) -> dict[str, Any]:
    """The nine frozen modules' blobs on disk, at HEAD, and on `main` (each must be main's); this module's and stats_s12.py's on disk, at
    HEAD, and at the freeze (all equal); the modules they rely on, recorded against the freeze. Every blob is printed through `log` before
    anything is asserted. `enforce` (a store of the paper's model): a clean tree, a freeze that is HEAD or an ancestor of it, and every
    equality above, or the analysis refuses to run."""
    from vpd_audit.results import code_commits

    commit = code_commits()
    frozen = []
    for m in FROZEN_MODULES:
        row = {"module": f"vpd_audit/{m}", "blob_on_disk": _git("hash-object", f"vpd_audit/{m}"), "blob_at_head": _blob("HEAD", m), f"blob_on_{against}": _blob(against, m)}
        row["equal"] = bool(row["blob_on_disk"] == row["blob_at_head"] == row[f"blob_on_{against}"])
        frozen.append(row)
    own = []
    for m in THIS_MODULES:
        row = {"module": f"vpd_audit/{m}", "blob_on_disk": _git("hash-object", f"vpd_audit/{m}"), "blob_at_head": _blob("HEAD", m), "blob_at_freeze": _blob(freeze, m)}
        row["equal"] = bool(row["blob_on_disk"] == row["blob_at_head"] == row["blob_at_freeze"])
        own.append(row)
    recorded = [{"module": f"vpd_audit/{m}", "blob_on_disk": _git("hash-object", f"vpd_audit/{m}"), "blob_at_head": _blob("HEAD", m), "blob_at_freeze": _blob(freeze, m)} for m in RECORDED_MODULES]
    for r in recorded:
        r["unchanged_since_the_freeze"] = bool(r["blob_on_disk"] == r["blob_at_head"] == r["blob_at_freeze"])
    ancestor = None
    if freeze:
        ancestor = subprocess.run(["git", "-C", str(env.PROJECT_ROOT), "merge-base", "--is-ancestor", freeze, "HEAD"], capture_output=True).returncode == 0
    out = {"enforced": enforce, "freeze": freeze, "commit": commit, "against": against, "against_commit": _git("rev-parse", against), "frozen_modules": frozen, "this_modules": own,
           "recorded_modules": recorded, "freeze_is_head_or_its_ancestor": ancestor, "frozen_modules_pass": all(r["equal"] for r in frozen)}
    if log is not None:
        log(f"[analyze s12] guard: commit {commit.get('project', '?')[:12]}, dirty flag {commit.get('dirty')}, freeze {freeze} (HEAD or its ancestor: {ancestor}), enforced: {enforce}")
        for r in frozen:
            log(f"[analyze s12]   {r['module']}: on disk {r['blob_on_disk'][:12]}, at HEAD {str(r['blob_at_head'])[:12]}, on {against} {str(r[f'blob_on_{against}'])[:12]} -> {'equal' if r['equal'] else 'DIFFERENT'}")
        for r in own:
            log(f"[analyze s12]   {r['module']}: on disk {r['blob_on_disk'][:12]}, at HEAD {str(r['blob_at_head'])[:12]}, at the freeze {str(r['blob_at_freeze'])[:12]} -> {'equal' if r['equal'] else 'DIFFERENT'}")
    if enforce:
        assert commit["dirty"] == "0", "the analysis refuses to run on a dirty tree (a tracked file modified, or uncommitted code)"
        assert freeze is not None and len(freeze) >= 7, "a store of the paper's model: give --freeze <the freeze commit>"
        assert ancestor, f"the freeze {freeze} is not HEAD or an ancestor of it"
        assert out["frozen_modules_pass"], f"a frozen module is not main's blob: {[r['module'] for r in frozen if not r['equal']]}"
        assert all(r["equal"] for r in own), f"a module of this analysis is not the freeze's blob: {[r['module'] for r in own if not r['equal']]}"
    return out


# ----------------------------------------------------------------------------- the stores


@dataclass
class Store:
    dir: Path
    run: str
    eval_set: str
    cells: pd.DataFrame
    rows: pd.DataFrame
    manifest: dict[str, Any]
    marker: dict[str, Any]
    objects: dict[str, Cell]
    kl: pd.DataFrame  # cell x seq, float32

    @property
    def n(self) -> int:
        return int(self.manifest["n_sequences"])

    @property
    def n_draws(self) -> int:
        return int(self.manifest["n_draws"])

    def vector(self, name: str) -> np.ndarray:
        assert name in self.kl.index, f"{self.dir.name}: no cell {name!r}"
        return self.kl.loc[name].to_numpy(np.float32)


def _rel(p: Any) -> str:
    a = Path(p).resolve()
    return os.path.relpath(a, env.PROJECT_ROOT) if env.PROJECT_ROOT in a.parents else str(p)


def load_store(store_dir: Path) -> Store:
    from vpd_audit.two_paths import _cell_from_row

    d = Path(store_dir)
    for needed in ("cells.parquet", "per_sequence.parquet", "run_manifest.json", "marker.json"):
        assert (d / needed).is_file(), f"{d}: a store without {needed}"
    assert not (d / "error.txt").is_file(), f"{d}: the launch recorded a failure of this store (error.txt)"
    cells, rows = pd.read_parquet(d / "cells.parquet"), pd.read_parquet(d / "per_sequence.parquet")
    manifest, marker = json.loads((d / "run_manifest.json").read_text()), json.loads((d / "marker.json").read_text())
    runs, sets = sorted(cells["run"].unique()), sorted(cells["eval_set"].unique())
    assert len(runs) == 1 and len(sets) == 1 and manifest.get("run") == runs[0], (d, runs, sets, manifest.get("run"))
    assert not cells["cell"].duplicated().any(), f"{d}: a cell appears twice in the cell table"
    objects = {r["cell"]: _cell_from_row(r) for _, r in cells.iterrows()}
    assert all(o.name == name for name, o in objects.items()), f"{d}: a cell rebuilt from its row does not carry its own name"
    kl = rows.pivot(index="cell", columns="seq", values="kl_mean").sort_index(axis=1)
    return Store(dir=d, run=runs[0], eval_set=sets[0], cells=cells.set_index("cell", drop=False), rows=rows, manifest=manifest, marker=marker, objects=objects, kl=kl)


def expected_stores(run: str, draws: int) -> dict[str, list[Cell]]:
    """The cells each tier-7 store holds: the launch's cells, the subset's references, and the canaries."""
    from vpd_audit import tier7 as t7m

    t7 = tier_7_cells(run, draws)

    def refs(eval_set: str, subset: str) -> list[Cell]:
        return _references(run, eval_set, 1, conditions=t7m.reference_conditions(subset), draws=draws)

    can = t7m.merge_canary_cells(run)
    out = {"E__merge_sizes": [c for c in t7 if c.eval_set == "E"] + refs("E", "merge_sizes") + can["E"],
           "E_lab__merge_sizes": [c for c in t7 if c.eval_set == "E_lab"] + refs("E_lab", "merge_sizes") + can["E_lab"],
           t7m.PANEL_CANARY_GROUP: t7m.panel_canary_cells(run) + refs("E_lab", "panel_edit")}
    for p in PANEL_EVAL_SETS.get(run, ()):
        out[f"{p}__panel_edit"] = [c for c in t7 if c.eval_set == p] + refs(p, "panel_edit")
    return out


def assert_complete(s: Store, want: list[Cell]) -> dict[str, Any]:
    """Every sub-batch done, the manifest finished, exactly the expected cells, each holding every text once with a finite divergence."""
    n_sub = (s.n + int(s.marker["subbatch"]) - 1) // int(s.marker["subbatch"])
    assert int(s.marker["done_through"]) == n_sub - 1 and int(s.marker["n_sequences"]) == s.n, f"{s.dir.name}: not complete (done through sub-batch {s.marker['done_through']} of {n_sub})"
    assert s.manifest.get("finished_at"), f"{s.dir.name}: the run manifest was never marked finished"
    assert set(s.rows["cell"].unique()) == set(s.cells.index) == set(s.marker["cells"]), f"{s.dir.name}: the rows, the cell table, and the marker do not hold the same cells"
    counts = s.rows.groupby("cell")["seq"].agg(["count", "nunique", "min", "max"])
    assert (counts["count"] == s.n).all() and (counts["nunique"] == s.n).all() and (counts["min"] == 0).all() and (counts["max"] == s.n - 1).all(), f"{s.dir.name}: a cell does not hold every text exactly once"
    assert np.array_equal(s.kl.columns.to_numpy(), np.arange(s.n)) and np.isfinite(s.kl.to_numpy(np.float64)).all(), f"{s.dir.name}: a per-text divergence that is missing or not finite"
    by = {c.name: c for c in want}
    assert set(s.objects) == set(by), f"{s.dir.name}: not the launch's cells: missing {sorted(set(by) - set(s.objects))[:4]}, extra {sorted(set(s.objects) - set(by))[:4]}"
    assert all(s.objects[n] == c for n, c in by.items()), f"{s.dir.name}: a cell's coordinates are not the launch's: {[n for n, c in by.items() if s.objects[n] != c][:4]}"
    assert (s.cells["n_subbatches"].astype(int) == n_sub).all(), f"{s.dir.name}: a cell's marker did not sum every sub-batch"
    return {"store": _rel(s.dir), "n_cells": int(len(s.cells)), "n_texts": s.n, "n_draws": s.n_draws, "n_subbatches": n_sub, "commit": s.manifest.get("commits", {}).get("project"),
            "dirty": s.manifest.get("commits", {}).get("dirty"), "gpu": s.manifest.get("gpu_name"), "precision": s.manifest.get("precision"), "subbatch": int(s.marker["subbatch"]), "set_hash": s.manifest.get("set_hash")}


def assert_summaries(root: Path) -> dict[str, Any]:
    """The two launch summaries beside the stores: no cell failed, every store run whole."""
    out = {}
    for subset in ("merge_sizes", "panel_edit"):
        p = Path(root) / f"summary__{subset}.json"
        assert p.is_file(), f"no launch summary at {p}"
        summ = json.loads(p.read_text())
        assert int(summ["cells_failed"]) == 0 and not summ["failures"], f"the {subset} launch recorded failures: {summ['failures']}"
        assert all(g.get("ok") is True for g in summ["groups"].values()), f"the {subset} launch did not run every store whole"
        t7s = summ.get("tier_7", {}).get("sets", {})
        out[subset] = {"cells_run": int(summ["cells_run"]), "gpu": summ.get("gpu"), "P3": summ.get("preconditions", {}).get("P3", {}).get("pass"), "sets_asserted_at_launch": bool(t7s.get("asserted")),
                       "two_paths": (summ.get("d_b_two_paths") or {}).get("pass")}
    return out


def load_tier7(spec: Spec) -> tuple[dict[str, Store], dict[str, Any]]:
    """Every tier-7 store of the run, complete and exactly the launch's cells."""
    from vpd_audit import tier7 as t7m

    stores: dict[str, Store] = {}
    records: dict[str, Any] = {}
    for d in sorted(Path(spec.store_root).glob("*/cells.parquet")):
        s = load_store(d.parent)
        assert s.run == spec.run, f"{d.parent}: a store of run {s.run!r}, not {spec.run!r}"
        stores[d.parent.name] = s
    assert stores, f"no tier-7 store under {spec.store_root}"
    draws = max(s.n_draws for s in stores.values())
    for name, s in stores.items():  # the panel edit's canary store holds draw 0 only; every other store holds every draw
        assert name == t7m.PANEL_CANARY_GROUP or s.n_draws == draws, f"{name}: {s.n_draws} draws, the other stores {draws}"
    want = expected_stores(spec.run, draws)
    assert set(stores) == set(want), f"the tier-7 root holds {sorted(stores)}, the launch {sorted(want)}"
    for name, s in stores.items():
        records[name] = assert_complete(s, want[name])
        if spec.panel_set_hashes and s.eval_set in spec.panel_set_hashes:
            assert s.manifest.get("set_hash") == spec.panel_set_hashes[s.eval_set], f"{name}: run on a set with ids hash {s.manifest.get('set_hash')}, not the saved panel's {spec.panel_set_hashes[s.eval_set]}"
    if spec.n_e is not None:
        assert stores["E__merge_sizes"].n == spec.n_e and draws == spec.n_draws, (stores["E__merge_sizes"].n, draws)
    return stores, records


def assert_canaries(stores: dict[str, Store], committed: Any, run: str, log: Any = print) -> list[dict[str, Any]]:
    """The merge stores' references and re-run committed cells, and the panel edit's canary store, bitwise against the committed stores."""
    from vpd_audit import tier7 as t7m

    names: dict[str, list[str]] = {"E__merge_sizes": [f"{run}/E/ref/{r}" for r in t7m.REFERENCE_NAMES["merge_sizes"]] + [c.name for c in t7m.merge_canary_cells(run)["E"]],
                                   "E_lab__merge_sizes": [f"{run}/E_lab/ref/{r}" for r in t7m.REFERENCE_NAMES["merge_sizes"]] + [c.name for c in t7m.merge_canary_cells(run)["E_lab"]],
                                   t7m.PANEL_CANARY_GROUP: [f"{run}/E_lab/ref/unmasked_delta"] + [c.name for c in t7m.panel_canary_cells(run)]}
    rows = []
    for store, ns in names.items():
        for name in ns:
            assert name in committed, f"THE CANARY CANNOT BE CHECKED: {name} is in no committed store"
            a, b = stores[store].vector(name), committed.kl_mean(name)
            equal = bool(a.shape == b.shape and np.array_equal(a, b))
            assert equal, f"THE CANARY FAILS: {name} in {store} does not reproduce its committed per-text kl_mean bitwise ({int((a != b).sum()) if a.shape == b.shape else 'shape'} texts differ)"
            rows.append({"store": store, "cell": name, "committed_store": _rel(committed.where[name]), "n_texts": int(a.size), "bitwise_equal": equal})
    log(f"[analyze s12] canary pass: {len(rows)} cells bitwise equal to the committed stores over {sum(r['n_texts'] for r in rows)} (cell, text) pairs")
    return rows


def assert_sets_again(stores: dict[str, Store], committed: Any, merge_table: Path, log: Any = print) -> dict[str, Any]:
    """Every set of every store, from its own cell table, against the label-only table and its committed twin (the launch's check, made
    again on what ran)."""
    from vpd_audit import tier7 as t7m

    cells, records = [], {}
    for s in stores.values():
        for n in s.cells.index:
            c = s.objects[n]
            cells.append(c)
            records[n] = {"source_sha256": s.cells.loc[n, "source_sha256"], "matched_source_sha256": s.cells.loc[n, "matched_source_sha256"]}
    table = pd.read_csv(merge_table, dtype={"rung": str})
    return t7m.assert_sets(cells, records, committed, table, log=log)


# ----------------------------------------------------------------------------- the panels


def panel_damage(s: Store, run: str, panel: str, size: int, draws: int) -> tuple[np.ndarray, np.ndarray]:
    """h (N,): the group's per-row damage against the store's rung 0 (unmasked_delta), as `analysis.excess_matrix` pairs it; t (N,): the
    twins' per-row damage, the mean over the draws first."""
    ref = s.vector(f"{run}/{panel}/ref/unmasked_delta").astype(np.float64)
    base = Cell(run, "code_leaning_hard", panel, "D_code", TAU_PRIMARY, "ones", "included", 0, code_leaning_rung(size), "none", 7)
    h = s.vector(base.name).astype(np.float64) - ref
    twins = np.stack([s.vector(Cell(run, "code_leaning_hard", panel, "D_code", TAU_PRIMARY, "ones", "included", k, code_leaning_rung(size), "usage", 7).name).astype(np.float64) - ref for k in range(draws)])
    return h, twins.mean(axis=0)


def panel_table(spec: Spec, stores: dict[str, Store], replicates: int, master_seed: int) -> dict[str, Any]:
    """Per panel and size: the statistics at 95 percent, and for the candidates at 1 - 0.05/3; the readings."""
    out: dict[str, Any] = {"stats": {}, "stats_candidates": {}, "readings": {}, "readings_candidates": {}, "documents": {}}
    small, large = spec.edit_sizes
    for p in spec.panels:
        s = stores[f"{p}__panel_edit"]
        docs = np.asarray(spec.panel_documents(p))
        assert docs.shape == (s.n,), f"{p}: {docs.shape} documents for {s.n} rows"
        n_docs = int(np.unique(docs).size)
        rs = s12.document_resample(docs, replicates, (master_seed, "boot_docs", "s12_panel", p)) if n_docs >= s9.MIN_DOCUMENTS else None
        out["documents"][p] = n_docs
        out["stats"][p], out["stats_candidates"][p] = {}, {}
        for size in spec.edit_sizes:
            h, t = panel_damage(s, spec.run, p, size, s.n_draws)
            out["stats"][p][size] = s12.edit_statistics(h, t, rs, n_docs, m=s12.M_PANEL)
            out["stats_candidates"][p][size] = s12.edit_statistics(h, t, rs, n_docs, m=s12.M_CANDIDATES)
        out["readings"][p] = s12.reading(out["stats"][p][small], out["stats"][p][large])
        out["readings_candidates"][p] = s12.reading(out["stats_candidates"][p][small], out["stats_candidates"][p][large])
    return out


def replication(spec: Spec, committed: Any, pt: dict[str, Any], replicates: int, master_seed: int) -> list[dict[str, Any]] | None:
    """For the panels of GitHub, StackExchange, Pile-CC, and Wikipedia: the panel's H beside the committed E_lab value on the same source, each
    with its document-level interval (on E_lab the source's own document resample, seed (master, "boot_docs", "E_lab", source)). The E_lab
    values are asserted equal to the committed by-source damages. None where the run has no such panel or no committed tables."""
    from vpd_audit.s9_checks import document_resample

    if spec.by_source_damage is None or not any(p in spec.panels for p in REPLICATION):
        return None
    run = spec.run
    by = pd.read_csv(spec.by_source_damage, float_precision="round_trip")
    gh = pd.read_csv(spec.github_damage, float_precision="round_trip").set_index("rung") if spec.github_damage else None
    src = np.asarray(spec.e_lab_sources)
    rows = []
    for size in spec.edit_sizes:
        rung = code_leaning_rung(size)
        g_name = Cell(run, "code_leaning_hard", "E_lab", "D_code", TAU_PRIMARY, "ones", "included", 0, rung, "none", 4).name
        ref_name = f"{run}/E_lab/ref/unmasked_delta"
        d = committed.where[g_name]
        ref = _committed_store_kl(d, ref_name)
        h_all = committed.kl_mean(g_name).astype(np.float64) - ref.astype(np.float64)
        tw = []
        k = 0
        while True:
            n = Cell(run, "code_leaning_hard", "E_lab", "D_code", TAU_PRIMARY, "ones", "included", k, rung, "usage", 4).name
            if n not in committed:
                break
            assert committed.where[n] == d, f"{n}: not in the group's store"
            tw.append(committed.kl_mean(n).astype(np.float64) - ref.astype(np.float64))
            k += 1
        t_all = np.stack(tw).mean(axis=0)
        for p, source in REPLICATION.items():
            if p not in spec.panels:
                continue
            mask = src == source
            docs = spec.e_lab_documents[mask]
            n_docs = int(np.unique(docs).size)
            rs = document_resample(docs, replicates, (master_seed, "boot_docs", "E_lab", source)) if n_docs >= s9.MIN_DOCUMENTS else None
            e = s12.edit_statistics(h_all[mask], t_all[mask], rs, n_docs, m=s12.M_PANEL)
            if source == "Github":
                want_h, want_t = (float(gh.loc[rung, "D_github"]), float(gh.loc[rung, "D_github_control"])) if gh is not None else (None, None)
            else:
                r = by[(by["rung"] == rung) & (by["source"] == source)].set_index("set")
                want_h, want_t = float(r.loc["group", "D"]), float(r.loc["control", "D"])
            h_ = float(h_all[mask].mean())
            t_ = float(np.stack(tw)[:, mask].mean(axis=0).mean())  # the committed tables' order of operations: per text over draws, then over texts
            assert want_h is None or (h_ == want_h and t_ == want_t), f"{source}, {size} members: the E_lab damages ({h_}, {t_}) are not the committed by-source damages ({want_h}, {want_t})"
            ps = pt["stats"][p][size]
            rows.append({"panel": p, "source": source, "size": size, "panel_H": ps["H"], **_lohi("panel_H_interval", ps["H_interval"]), "panel_documents": ps["n_documents"],
                         "E_lab_H": e["H"], **_lohi("E_lab_H_interval", e["H_interval"]), "E_lab_rows": int(mask.sum()), "E_lab_documents": n_docs, "E_lab_equal_to_committed": want_h is not None,
                         "panel_rho": ps["rho"], "E_lab_rho": e["rho"]})
    return rows


def _committed_store_kl(store: Path, name: str) -> np.ndarray:
    r = pd.read_parquet(Path(store) / "per_sequence.parquet", columns=["cell", "seq", "kl_mean"])
    r = r[r["cell"] == name].sort_values("seq")
    assert len(r) and np.array_equal(r["seq"].to_numpy(), np.arange(len(r))), f"{store}: {name} does not hold every text once"
    return r["kl_mean"].to_numpy(np.float32)


def removed_label(spec: Spec, pt: dict[str, Any]) -> dict[str, Any] | None:
    """For the panels with label caches: H/omega for the group and T/omega for the twins beside rho, and the order of the panels by the
    group's omega against their order by H, overall and for the two pairs. None where no omega table exists."""
    if spec.omega_table is None or not Path(spec.omega_table).is_file():
        return None
    om = pd.read_csv(spec.omega_table)
    rows, orders, pairs = [], {}, []
    for size in spec.edit_sizes:
        sub = om[om["size"] == size].set_index("panel")
        have = [p for p in spec.panels if p in sub.index]
        for p in have:
            ps = pt["stats"][p][size]
            og, ot = float(sub.loc[p, "omega_group"]), float(sub.loc[p, "omega_twins"])
            rows.append({"panel": p, "size": size, "omega_group": og, "omega_twins": ot, "H": ps["H"], "T": ps["T"], "H_per_omega_group": ps["H"] / og if og > 0 else float("nan"),
                         "T_per_omega_twins": ps["T"] / ot if ot > 0 else float("nan"), "rho": ps["rho"], **_lohi("rho_interval", ps["rho_interval"])})
        by_omega = sorted(have, key=lambda p: -float(sub.loc[p, "omega_group"]))
        by_h = sorted(have, key=lambda p: -pt["stats"][p][size]["H"])
        orders[size] = {"by_omega_group": by_omega, "by_H": by_h, "same": by_omega == by_h}
        for a, b in ORDER_PAIRS:
            if a in have and b in have:
                oa, ob = float(sub.loc[a, "omega_group"]), float(sub.loc[b, "omega_group"])
                ha, hb = pt["stats"][a][size]["H"], pt["stats"][b][size]["H"]
                pairs.append({"size": size, "pair": f"{PANEL_WORDS[a]} / {PANEL_WORDS[b]}", "omega_first": oa, "omega_second": ob, "H_first": ha, "H_second": hb,
                              "higher_by_omega": PANEL_WORDS[a] if oa > ob else PANEL_WORDS[b], "higher_by_H": PANEL_WORDS[a] if ha > hb else PANEL_WORDS[b], "same_order": (oa > ob) == (ha > hb)})
    return {"rows": rows, "orders": orders, "pairs": pairs}


# ----------------------------------------------------------------------------- the merge points


def merge_points(spec: Spec, stores: dict[str, Store], committed: Any, replicates: int, master_seed: int) -> dict[str, Any]:
    """The rises over the text's own explanation at 1, 2, 4, 8 donor tokens: on E per line (the text bootstrap), on E_lab per arm and stratum
    (the stratified document bootstrap), all at 95 percent, the draws held fixed; per-draw means; the real merge minus the matched control."""
    run = spec.run
    E, EL = stores["E__merge_sizes"], stores["E_lab__merge_sizes"]
    draws = E.n_draws
    imp_e7, imp_l7 = E.vector(f"{run}/E/ref/importances"), EL.vector(f"{run}/E_lab/ref/importances")
    checked: dict[str, bool] = {}

    def committed_rise(name: str, eval_set: str, first: np.ndarray) -> np.ndarray:
        assert name in committed, f"{name}: in no committed store"
        d = committed.where[name]
        imp = _committed_store_kl(d, f"{run}/{eval_set}/ref/importances")
        if str(d) not in checked:
            assert np.array_equal(imp, first), f"{d}: its importances are not the tier-7 store's bitwise"
            checked[str(d)] = True
        return committed.kl_mean(name).astype(np.float64) - imp.astype(np.float64)

    def rise(eval_set: str, pool: str, control: str, rung: str) -> np.ndarray:
        out = []
        for k in range(draws):
            if rung in COMMITTED_MERGE_RUNGS:
                tier = COMMITTED_TIER[control] if eval_set == "E" else 5
                c = Cell(run, "union", eval_set, pool, TAU_PRIMARY, "r0", "excluded", k, rung, control, tier)
                out.append(committed_rise(c.name, eval_set, imp_e7 if eval_set == "E" else imp_l7))
            else:
                c = Cell(run, "union", eval_set, pool, TAU_PRIMARY, "r0", "excluded", k, rung, control, 7, descriptive=True)
                s = E if eval_set == "E" else EL
                out.append(s.vector(c.name).astype(np.float64) - (imp_e7 if eval_set == "E" else imp_l7).astype(np.float64))
        return np.stack(out)

    rs_e = st.Resample.make(E.n, replicates, (master_seed, "boot", "E"))
    e_rows, draw_rows, diff_rows = [], [], []
    rises = {line: {r: rise("E", "D_unif", ctl, r) for r in MERGE_RUNGS} for line, ctl in LINES.items()}
    base_e = float(imp_e7.astype(np.float64).mean())
    for line, by_r in rises.items():
        for r in MERGE_RUNGS:
            u = st.union_rung(by_r[r], rs_e, 1)
            e_rows.append({"line": line, "tokens": TOKENS[r], "rung": r, "rise": u["e_hat"], **_lohi("interval", u["interval"]), "own_explanation": base_e, "divergence": u["e_hat"] + base_e,
                           "n_draws_positive": u["n_draws_positive"], "n_draws": u["n_draws"], "measured_in": "tier 7" if r not in COMMITTED_MERGE_RUNGS else "committed"})
    for r in MERGE_RUNGS:
        real, matched, uni = rises["real merge"][r], rises["frequency-matched"][r], rises["uniform random"][r]
        pdiff = st.paired_difference(real, matched, rs_e)
        per = real.mean(axis=1) - matched.mean(axis=1)
        diff_rows.append({"tokens": TOKENS[r], "rung": r, "real_minus_matched": pdiff["mean"], **_lohi("interval", pdiff["interval"]), "n_draws_positive": int((per > 0).sum()), "n_draws": int(per.size)})
        for k in range(draws):
            draw_rows.append({"tokens": TOKENS[r], "rung": r, "draw": k, "real_merge": float(real[k].mean()), "frequency_matched": float(matched[k].mean()), "real_minus_matched": float(per[k]),
                              "uniform_random": float(uni[k].mean())})
    # E_lab: each pool on the code texts and on the prose texts
    src = np.asarray(spec.e_lab_sources)
    docs = np.asarray(spec.e_lab_documents)
    lab_rows = []
    for stratum, members in (("code texts", spec.code_sources), ("prose texts", spec.prose_sources)):
        mask = np.isin(src, members)
        n_docs = int(np.unique(docs[mask]).size)
        rs = s9.stratified_document_resample(docs[mask], src[mask], replicates, lambda s: (master_seed, "boot_docs", "E_lab", s))
        base = float(imp_l7.astype(np.float64)[mask].mean())
        for arm, pool in ARMS.items():
            for r in MERGE_RUNGS:
                u = s9.union_rung_s9(rise("E_lab", pool, "none", r)[:, mask], rs, 1, n_documents=n_docs)
                lab_rows.append({"stratum": stratum, "donors": arm, "pool": pool, "tokens": TOKENS[r], "rung": r, "rise": u["e_hat"], **_lohi("interval", u["interval"]), "own_explanation": base,
                                 "divergence": u["e_hat"] + base, "n_documents": n_docs, "n_texts": int(mask.sum()), "n_draws_positive": u["n_draws_positive"], "n_draws": u["n_draws"]})
    return {"E": e_rows, "E_per_draw": draw_rows, "E_real_minus_matched": diff_rows, "E_lab": lab_rows, "importances_stores_checked": sorted(_rel(k) for k in checked)}


# ----------------------------------------------------------------------------- the outputs


def _lohi(prefix: str, iv: Any) -> dict[str, float]:
    ok = isinstance(iv, (list, tuple)) and len(iv) == 2 and all(x is not None for x in iv)
    return {f"{prefix}_lo": float(iv[0]) if ok else float("nan"), f"{prefix}_hi": float(iv[1]) if ok else float("nan")}


def _fmt(v: Any, nd: int = 4) -> str:
    if v is None:
        return ""
    if isinstance(v, (bool, np.bool_)):
        return "yes" if v else "no"
    if isinstance(v, (float, np.floating)):
        return "" if np.isnan(v) else f"{v:.{nd}f}"
    return str(v)


def _md(df: pd.DataFrame, nd: int = 4) -> str:
    cols = list(df.columns)
    L = ["| " + " | ".join(cols) + " |", "|" + "---|" * len(cols)]
    for row in df.astype(object).itertuples(index=False):  # object rows: an integer column stays an integer beside a float one
        L.append("| " + " | ".join(_fmt(v, nd) for v in row) + " |")
    return "\n".join(L)


def _iv(lo: float, hi: float) -> str:
    return "" if (np.isnan(lo) or np.isnan(hi)) else f"[{lo:.4f}, {hi:.4f}]"


def panel_rows(spec: Spec, pt: dict[str, Any], key: str = "stats", reading_key: str = "readings") -> list[dict[str, Any]]:
    rows = []
    for p in spec.panels:
        rd = pt[reading_key][p]
        for size in spec.edit_sizes:
            v = pt[key][p][size]
            rows.append({"panel": p, "source": PANEL_WORDS.get(p, p), "size": size, "level": f"1 - 0.05/{v['m']}", "n_rows": v["n_rows"], "n_documents": v["n_documents"], "H": v["H"], **_lohi("H_interval", v["H_interval"]),
                         "T": v["T"], **_lohi("T_interval", v["T_interval"]), "rho": v["rho"], **_lohi("rho_interval", v["rho_interval"]), "rho_nonfinite_share": v["rho_nonfinite_share"],
                         "reading": rd["word"], "rho_side": rd["rho_sides"]["small" if size == spec.edit_sizes[0] else "large"]})
    return rows


def write_outputs(out_dir: Path, ctx: dict[str, Any]) -> Path:
    """report.md and one CSV per table (s12_*.csv), and nothing that depends on the time or the machine."""
    out_dir.mkdir(parents=True, exist_ok=True)
    spec: Spec = ctx["spec"]
    pt = ctx["panels"]
    small, large = spec.edit_sizes
    tables: dict[str, pd.DataFrame] = {"s12_panels": pd.DataFrame(panel_rows(spec, pt)),
                                       "s12_panel_candidates": pd.DataFrame([r for r in panel_rows(spec, pt, "stats_candidates", "readings_candidates") if r["panel"] in CANDIDATES]),
                                       "s12_merge_E": pd.DataFrame(ctx["merge"]["E"]), "s12_merge_E_per_draw": pd.DataFrame(ctx["merge"]["E_per_draw"]),
                                       "s12_merge_E_real_minus_matched": pd.DataFrame(ctx["merge"]["E_real_minus_matched"]), "s12_merge_E_lab": pd.DataFrame(ctx["merge"]["E_lab"]),
                                       "s12_canary": pd.DataFrame(ctx["checks"]["canary"]), "s12_stores": pd.DataFrame(list(ctx["checks"]["stores"].values())),
                                       "s12_frozen_modules": pd.DataFrame(ctx["guard"]["frozen_modules"] + ctx["guard"]["this_modules"] + ctx["guard"]["recorded_modules"])}
    if ctx.get("replication"):
        tables["s12_replication"] = pd.DataFrame(ctx["replication"])
    if ctx.get("removed_label"):
        tables["s12_removed_label"] = pd.DataFrame(ctx["removed_label"]["rows"])
        tables["s12_removed_label_pairs"] = pd.DataFrame(ctx["removed_label"]["pairs"])
    for name, df in tables.items():
        df.to_csv(out_dir / f"{name}.csv", index=False, lineterminator="\n")
    g, ch = ctx["guard"], ctx["checks"]
    arx = pt["readings"].get(DECISIVE)
    T = tables["s12_panels"]
    L = [f"# The code-leaning edit on the panels, and the merges of 2 and 4 donor tokens ({spec.run})", ""]
    if arx is not None:
        L += [f"**ArXiv reads {arx['word']}**: {POST_WORDS[arx['word']]}." + (f" rho lies {arx['rho_sides']['small']} at {small} members and {arx['rho_sides']['large']} at {large}." if arx["word"] == s12.SOFTEN else ""), ""]
    L += [f"Every interval is a 95 percent percentile bootstrap ({ctx['replicates']} replicates) unless it says otherwise. On a panel the bootstrap resamples its documents, every row of a drawn document "
          "entering together, means in ratio form, one document draw per replicate shared by H, T, and rho at both sizes, the twins' draws held fixed. H is the edit's damage (the mean over rows of a "
          f"row's divergence from the original model, minus the rung-0 reference's); T the usage-matched twins' (the mean over the draws per row first); rho = H / T. X = {X:g} nats.", "",
          "Keep requires every one of its three intervals to clear its bar (H at the smaller size at or above X, rho above 1 at both sizes): an intersection-union test, whose error rate is at most "
          "the per-interval 5 percent, so no correction across the three is applied.", "",
          "## 0. What was asserted before anything was read", "",
          f"- The guard: commit {g['commit'].get('project', '?')[:12]}, dirty flag {g['commit'].get('dirty')}, freeze {g['freeze']} (HEAD or its ancestor: {g['freeze_is_head_or_its_ancestor']}), enforced: {g['enforced']}. "
          f"The nine frozen modules against {g['against']} ({g['against_commit'][:12]}): {'all equal' if g['frozen_modules_pass'] else 'NOT all equal'}; this analysis's modules at the freeze: "
          + ", ".join(f"{r['module']} {'equal' if r['equal'] else 'DIFFERENT'}" for r in g["this_modules"]) + " (s12_frozen_modules.csv).",
          f"- The stores: {len(ch['stores'])} under {_rel(spec.store_root)}, each complete and exactly the launch's cells (s12_stores.csv)"
          + (f"; the launch summaries: {ch['summaries']}" if ch.get("summaries") else "") + ".",
          f"- The canaries: {len(ch['canary'])} cells bitwise equal to their committed per-text divergences (s12_canary.csv).",
          f"- Every set held again to the label-only table and its committed twin: {ch['sets']}.",
          f"- The importances of every committed store the 1- and 8-token points are read from equal the tier-7 store's bitwise: {ctx['merge']['importances_stores_checked']}.", "",
          f"## 1. ArXiv (decisive), at {small} and {large} members", ""]
    cols = ["size", "n_documents", "H", "H_interval_lo", "H_interval_hi", "T", "T_interval_lo", "T_interval_hi", "rho", "rho_interval_lo", "rho_interval_hi", "rho_nonfinite_share"]
    if DECISIVE in spec.panels:
        L += [_md(T[T.panel == DECISIVE][cols]), "", f"Reading: **{arx['word']}** ({arx['reason']}); rho {arx['rho_sides']['small']} at {small}, {arx['rho_sides']['large']} at {large}. "
              f"The post may then say: {POST_WORDS[arx['word']]}.", ""]
    else:
        L += ["No ArXiv panel on this run.", ""]
    TC = tables["s12_panel_candidates"]
    L += ["## 2. The candidates to stand in for ArXiv (this applies only if ArXiv reads drop)", "",
          "Each of DM Mathematics, PubMed Central, and FreeLaw may serve as the caveat's example only if it meets the keep condition with every interval at 1 - 0.05/3 (about 98.3 percent), correcting for the three candidates.", ""]
    if len(TC):
        L += [_md(TC[["source", "size", "n_documents", "H", "H_interval_lo", "H_interval_hi", "rho", "rho_interval_lo", "rho_interval_hi", "rho_nonfinite_share", "reading"]]), "",
              "Candidates meeting keep at that level: " + (", ".join(PANEL_WORDS[p] for p in CANDIDATES if p in pt["readings_candidates"] and pt["readings_candidates"][p]["word"] == s12.KEEP) or "none") + ".", ""]
    else:
        L += ["No candidate panel on this run.", ""]
    L += ["## 3. Every panel (descriptive: the same numbers and the same rule, read by nothing)", "",
          _md(T[["source", "size", "n_documents", "H", "H_interval_lo", "H_interval_hi", "T", "rho", "rho_interval_lo", "rho_interval_hi", "rho_nonfinite_share", "reading", "rho_side"]]), ""]
    if ctx.get("replication"):
        L += ["## 4. A replication: each panel's H beside the committed E_lab value on the same source", "",
              "The E_lab intervals resample E_lab's documents of that source (seed (master, \"boot_docs\", \"E_lab\", source)); the E_lab values equal the committed by-source damages exactly.", "",
              _md(tables["s12_replication"][["source", "size", "panel_H", "panel_H_interval_lo", "panel_H_interval_hi", "panel_documents", "E_lab_H", "E_lab_H_interval_lo", "E_lab_H_interval_hi", "E_lab_documents"]]), ""]
    else:
        L += ["## 4. A replication against E_lab: not available on this run.", ""]
    if ctx.get("removed_label"):
        rl = ctx["removed_label"]
        L += ["## 5. The damage per unit of removed label, beside rho (descriptive)", "",
              _md(tables["s12_removed_label"][["panel", "size", "omega_group", "omega_twins", "H_per_omega_group", "T_per_omega_twins", "rho", "rho_interval_lo", "rho_interval_hi"]]), ""]
        for size, o in rl["orders"].items():
            L.append(f"- {size} members: by the group's omega {' > '.join(PANEL_WORDS[p] for p in o['by_omega_group'])}; by H {' > '.join(PANEL_WORDS[p] for p in o['by_H'])}; the same order: {'yes' if o['same'] else 'no'}.")
        L += ["", _md(tables["s12_removed_label_pairs"]), ""]
    else:
        L += ["## 5. The damage per unit of removed label: not available on this run (no label caches of its panels).", ""]
    L += ["## 6. The merge points at 1, 2, 4, and 8 donor tokens (descriptive)", "",
          "On E, the rise over the text's own explanation per line; 1 and 8 tokens from the committed stores, 2 and 4 from tier 7:", "",
          _md(tables["s12_merge_E"][["line", "tokens", "rise", "interval_lo", "interval_hi", "divergence", "n_draws_positive", "n_draws"]]), "",
          "The real merge minus the frequency-matched control, paired per text and draw:", "", _md(tables["s12_merge_E_real_minus_matched"][["tokens", "real_minus_matched", "interval_lo", "interval_hi", "n_draws_positive", "n_draws"]]), "",
          "Per draw (the mean over the texts of E):", "", _md(tables["s12_merge_E_per_draw"]), "",
          "On E_lab, each pool on the code texts and on the prose texts (the stratified document bootstrap):", "",
          _md(tables["s12_merge_E_lab"][["stratum", "donors", "tokens", "rise", "interval_lo", "interval_hi", "divergence", "n_documents", "n_draws_positive"]]), ""]
    path = out_dir / "report.md"
    path.write_text("\n".join(L) + "\n")
    return path


def _jsonable(o: Any) -> Any:
    if isinstance(o, dict):
        return {str(k): _jsonable(v) for k, v in o.items()}
    if isinstance(o, (list, tuple)):
        return [_jsonable(x) for x in o]
    if isinstance(o, np.bool_):
        return bool(o)
    if isinstance(o, np.integer):
        return int(o)
    if isinstance(o, np.floating):
        return float(o)
    return o


def analyze_s12(spec: Spec, *, freeze: str | None = None, replicates: int = st.N_REPLICATES, master_seed: int = 0, log: Any = print) -> dict[str, Any]:
    """The whole reading. The guard runs before any file of a store is opened."""
    from vpd_audit.tier5 import CommittedTables

    paper = spec.run in PAPER_RUNS
    guard = freeze_guard(freeze, enforce=paper, log=log)
    for r in spec.committed_roots:
        a, b = Path(r).resolve(), Path(spec.store_root).resolve()
        assert a.is_dir() and a != b and a not in b.parents and b not in a.parents, f"the committed root {r} and the tier-7 root {spec.store_root} overlap, or the root is absent"
    stores, records = load_tier7(spec)
    committed = CommittedTables(tuple(Path(r) for r in spec.committed_roots))
    checks: dict[str, Any] = {"stores": records}
    checks["summaries"] = assert_summaries(spec.store_root) if (paper or (Path(spec.store_root) / "summary__merge_sizes.json").is_file()) else None
    from vpd_audit import tier7 as t7m

    want_sub = {"E": t7m.committed_subbatch(committed, spec.run, "E"), "E_lab": t7m.committed_subbatch(committed, spec.run, "E_lab")}
    for name, rec in records.items():
        es = "E" if name.startswith("E__") else "E_lab"  # the panels and the panel edit's canary at E_lab's
        assert rec["subbatch"] == want_sub[es], f"{name}: run at sub-batch {rec['subbatch']}, not the committed {es} store's {want_sub[es]}"
    checks["committed_subbatch"] = want_sub
    checks["canary"] = assert_canaries(stores, committed, spec.run, log)
    checks["sets"] = assert_sets_again(stores, committed, spec.merge_table, log)
    pt = panel_table(spec, stores, replicates, master_seed)
    ctx: dict[str, Any] = {"spec": spec, "guard": guard, "checks": checks, "panels": pt, "replicates": replicates, "master_seed": master_seed,
                           "replication": replication(spec, committed, pt, replicates, master_seed), "removed_label": removed_label(spec, pt),
                           "merge": merge_points(spec, stores, committed, replicates, master_seed)}
    path = write_outputs(Path(spec.out_dir), ctx)
    arx = pt["readings"].get(DECISIVE)
    summary = {"run": spec.run, "freeze": freeze, "commit": guard["commit"], "replicates": replicates, "master_seed": master_seed, "arxiv_reading": arx,
               "candidates_meeting_keep": [p for p in CANDIDATES if p in pt["readings_candidates"] and pt["readings_candidates"][p]["word"] == s12.KEEP],
               "readings": pt["readings"], "documents": pt["documents"], "checks": {k: v for k, v in checks.items() if k != "stores"}}
    with open(Path(spec.out_dir) / "summary.json", "w") as f:
        json.dump(_jsonable(summary), f, indent=2, sort_keys=True)
    log(f"[analyze s12] ArXiv: {arx['word'] if arx else 'no panel'}; report written to {path}")
    return summary
