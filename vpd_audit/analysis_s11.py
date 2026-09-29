"""The reading of the binary union, fixed before any store of the run existed. CPU only, read-only.

It loads the one tier-6 store (`results/grid/<run>_s11/tier6/E__binary_union/`), asserts what the rule fixed in advance asserts, builds the excess
matrices, applies the rule, and writes `report.md` and one CSV per table (`results/grid/analysis/<run>/s11/`). The statistics are the
frozen functions: the registered bump rule `stats.union_rung` (the interval of the mean over draws and texts from the text bootstrap
`stats.Resample`, seed (master, "boot", "E"); detected if the interval lies above zero and at least seven of the eight per-draw means are
positive; material if in addition its lower end exceeds 0.05), `stats_s9.self_merge_rule` (no draws, so no sign condition), and
`stats.paired_difference`. Every interval is at level 1 - 0.05/4 (three sizes plus the self-merge).

**Before anything is read.** The guard: for a store of the paper's model the working tree must be clean, `--freeze` must name the
freeze commit, this module's blob on disk must be its blob at HEAD and at the freeze, and each of the nine frozen modules must be its
blob on `main` (printed, module by module). Then the store: complete, every cell holding every text once, exactly the launch's cells
(the tier-6 cells, the secondary form's tier-3 cells, the four references, the canary), no failure recorded; **the canary**: the four
references and the headline union at draw 0, rung 2 reproduce their committed per-text divergences bitwise; every named set is its
committed twin's (`tier6.assert_sets_are_committed`, on the store's own cell table); P3 held on every cell of the primary form (the
cells are permitted, so the loop asserted m >= g, and no entry lies below its label). The committed fractional comparators are
recomputed from the committed stores and, on the paper's run, must be the table fixed in advance, to four decimals.

**The rule.** Step 1, the verdict, on the primary form (`rounded0_own_g`, own labels rounded at 0, start `rounded_0`) at 8,
16, 64 tokens and on the primary self-merge: *fails* if material at 64 tokens; two cases stop the reading (material at 64 but the
self-merge not material; material at 8 or 16 but not at 64), and a stop is reported with its reason and nothing read further. Step 2,
read only if Step 1 says fails: each size within the band 1/2 e_frac <= e_bin <= 2 e_frac on point estimates, with the paired
difference beside it (per text and draw against the committed per-text fractional values), which describes and does not decide.
Outcomes: **A** fails and every size within the band; **B** fails and some size outside; **C** not material at any size. Outcome A's
band is `BAND_SIZES`: the three token sizes *and* the self-merge (step 2 asks whether the post's quoted
numbers survive, and the self-merge's is one of them); "size" in step 1 and in outcome C keeps its narrow sense, the three token sizes.
Descriptions, never read by a rule: the absolute divergences of both starts and both
self-merges, the secondary form's excesses and bands, the look-alike control's excess and the primary minus the control. No switched
mass is printed for either binary family (`masks.switched_mass` ignores the rounding).

    uv run vpd-audit analyze-s11 --run main --freeze <the freeze commit>
"""

from __future__ import annotations

import json
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from vpd_audit import env
from vpd_audit import stats as st
from vpd_audit import stats_s9 as s9
from vpd_audit.cells import BINARY_EXISTING_RUNGS, BINARY_RUNGS, OWN_ROUND_PRIMARY, OWN_ROUND_SECONDARY, TAU_PRIMARY, Cell, tier_6_cells
from vpd_audit.constants import PERMITTED_TOL
from vpd_audit.sources import ROUNDED0_FAMILY

FROZEN_MODULES: tuple[str, ...] = ("stats.py", "stats_s7.py", "stats_s9.py", "analysis.py", "analysis_s7.py", "analysis_s9.py", "figures.py", "figures_s7.py", "figures_s9.py")
RECORDED_MODULES: tuple[str, ...] = ("cells.py", "grid.py", "sources.py", "masks.py", "tier5.py", "tier6.py", "two_paths.py")  # what this module imports or the store was made by: blobs printed against the freeze, not asserted
THIS_MODULE = "analysis_s11.py"
PAPER_RUNS: tuple[str, ...] = ("main", "control")
STORE_NAME = "E__binary_union"
X = st.X_MATERIAL  # 0.05 nats
M = 4  # three sizes plus the self-merge
SIZES: tuple[str, ...] = BINARY_RUNGS  # "2", "2a", "3": 8, 16, 64 tokens
SELF = "self"
BAND_SIZES: tuple[str, ...] = SIZES + (SELF,)  # what outcome A requires within the band: the three token sizes and the self-merge
BAND_LO, BAND_HI = 0.5, 2.0
SIZE_WORDS: dict[str, str] = {"2": "8 tokens", "2a": "16 tokens", "3": "64 tokens", SELF: "the self-merge"}
REGISTERED_COMPARATORS: dict[str, float] = {"2": 0.0402, "2a": 0.1016, "3": 0.4575, SELF: 1.0298}  # the table fixed in advance, the committed fractional excesses over own labels
N_TEXTS_E, N_DRAWS = 1024, 8
FAILS, HOLDS, STOP = "fails", "holds at the sizes tested", "stop"
STOP_SELF = "the primary form is material at 64 tokens but the self-merge is not"
STOP_FALLING = "the primary form is material at 8 or 16 tokens but not at 64, which would take a curve that falls as more is merged"
REFERENCES: tuple[str, ...] = ("importances", "rounded_0", "rounded_0.1", "unmasked")
WORDING_C = ("Outcome C would mean *no drift from the original model at the sizes tested*, not that the union equation holds: the excess compares each mask with the original model, "
             "so a text's rises and falls at different positions can cancel. A *fails* carries over to the paper's equation; a *holds* does not.")
WORDING_ASYMMETRY = ("Donors are cut at 0.1 while the recipient is cut at 0, so the merged set is smaller than the equation's literal union at 0, an asymmetry that favours the paper.")


# ----------------------------------------------------------------------------- the rule, as pure functions


def step1(e_bin: dict[str, np.ndarray], s_bin: np.ndarray, resample: st.Resample, *, m: int = M, x: float = X) -> dict[str, Any]:
    """Step 1 on the primary form: the bump rule at each size on its (K, N) excess matrix, the self-merge rule on its (N,) excess, and the
    verdict with the two stops."""
    assert set(e_bin) == set(SIZES), sorted(e_bin)
    per_size = {j: st.union_rung(e_bin[j], resample, m, x=x) for j in SIZES}
    self_rule = s9.self_merge_rule(s_bin, resample, m=m, x=x)
    material = {j: bool(per_size[j]["material"]) for j in SIZES}
    return {"per_size": per_size, "self": self_rule, **verdict(material, bool(self_rule["material"]))}


def verdict(material: dict[str, bool], self_material: bool) -> dict[str, Any]:
    """Step 1: fails if material at 64 tokens; otherwise holds at the sizes tested; the two stops first."""
    if material["3"] and not self_material:
        return {"verdict": STOP, "reason": STOP_SELF}
    if not material["3"] and (material["2"] or material["2a"]):
        return {"verdict": STOP, "reason": STOP_FALLING}
    return {"verdict": FAILS if material["3"] else HOLDS, "reason": ""}


def within_band(e_bin_hat: float, e_frac_hat: float, lo: float = BAND_LO, hi: float = BAND_HI) -> bool:
    """Step 2, on point estimates: 1/2 e_frac <= e_bin <= 2 e_frac."""
    return bool(lo * e_frac_hat <= e_bin_hat <= hi * e_frac_hat)


def outcome(verdict_word: str, within: dict[str, bool] | None, band_sizes: tuple[str, ...] = BAND_SIZES) -> str:
    """A: fails, and every size within the band; B: fails, and some size outside; C: not material at any size; a stop has no outcome word."""
    if verdict_word == STOP:
        return STOP
    if verdict_word == HOLDS:
        return "C"
    assert verdict_word == FAILS and within is not None, verdict_word
    return "A" if all(within[j] for j in band_sizes) else "B"


# ----------------------------------------------------------------------------- the guard


def _git(*args: str) -> str:
    return subprocess.run(["git", "-C", str(env.PROJECT_ROOT), *args], check=True, capture_output=True, text=True).stdout.strip()


def _blob(rev: str, module: str) -> str | None:
    try:
        return _git("rev-parse", f"{rev}:vpd_audit/{module}")
    except subprocess.CalledProcessError:
        return None


def freeze_guard(freeze: str | None, *, enforce: bool, against: str = "main", log: Any = None) -> dict[str, Any]:
    """The frozen modules' blobs on disk, at HEAD, and on `main` (each must be main's); this module's on disk, at HEAD, and at the freeze
    (all three equal); the modules it relies on, recorded against the freeze. Every blob is printed through `log` before anything is
    asserted. `enforce` (a store of the paper's model): a clean tree, a freeze that is HEAD or an ancestor of it, and every equality
    above, or the analysis refuses to run."""
    from vpd_audit.results import code_commits

    commit = code_commits()
    frozen = []
    for m in FROZEN_MODULES:
        row = {"module": f"vpd_audit/{m}", "blob_on_disk": _git("hash-object", f"vpd_audit/{m}"), "blob_at_head": _blob("HEAD", m), f"blob_on_{against}": _blob(against, m)}
        row["equal"] = bool(row["blob_on_disk"] == row["blob_at_head"] == row[f"blob_on_{against}"])
        frozen.append(row)
    own = {"module": f"vpd_audit/{THIS_MODULE}", "blob_on_disk": _git("hash-object", f"vpd_audit/{THIS_MODULE}"), "blob_at_head": _blob("HEAD", THIS_MODULE), "blob_at_freeze": _blob(freeze, THIS_MODULE) if freeze else None}
    own["equal"] = bool(own["blob_on_disk"] == own["blob_at_head"] == own["blob_at_freeze"])
    recorded = [{"module": f"vpd_audit/{m}", "blob_on_disk": _git("hash-object", f"vpd_audit/{m}"), "blob_at_head": _blob("HEAD", m), "blob_at_freeze": _blob(freeze, m) if freeze else None} for m in RECORDED_MODULES]
    for r in recorded:
        r["unchanged_since_the_freeze"] = bool(r["blob_on_disk"] == r["blob_at_head"] == r["blob_at_freeze"])
    freeze_is_ancestor = None
    if freeze:
        freeze_is_ancestor = subprocess.run(["git", "-C", str(env.PROJECT_ROOT), "merge-base", "--is-ancestor", freeze, "HEAD"], capture_output=True).returncode == 0
    out = {"enforced": enforce, "freeze": freeze, "commit": commit, "against": against, "against_commit": _git("rev-parse", against), "frozen_modules": frozen,
           "this_module": own, "recorded_modules": recorded, "freeze_is_head_or_its_ancestor": freeze_is_ancestor, "frozen_modules_pass": all(r["equal"] for r in frozen)}
    if log is not None:
        log(f"[analyze s11] guard: commit {commit.get('project', '?')[:12]}, dirty flag {commit.get('dirty')}, freeze {freeze} (HEAD or its ancestor: {freeze_is_ancestor}), enforced: {enforce}")
        for r in frozen:
            log(f"[analyze s11]   {r['module']}: on disk {r['blob_on_disk'][:12]}, at HEAD {str(r['blob_at_head'])[:12]}, on {against} {str(r[f'blob_on_{against}'])[:12]} -> {'equal' if r['equal'] else 'DIFFERENT'}")
        log(f"[analyze s11]   {own['module']}: on disk {own['blob_on_disk'][:12]}, at HEAD {str(own['blob_at_head'])[:12]}, at the freeze {str(own['blob_at_freeze'])[:12]} -> {'equal' if own['equal'] else 'DIFFERENT'}")
    if enforce:
        assert commit["dirty"] == "0", "the analysis refuses to run on a dirty tree (a tracked file modified, or uncommitted code)"
        assert freeze is not None and len(freeze) >= 7, "a store of the paper's model: give --freeze <the freeze commit>"
        assert freeze_is_ancestor, f"the freeze {freeze} is not HEAD or an ancestor of it"
        assert out["frozen_modules_pass"], f"a frozen module is not main's blob: {[r['module'] for r in frozen if not r['equal']]}"
        assert own["equal"], f"{own['module']} is not the freeze's blob (on disk {own['blob_on_disk']}, at HEAD {own['blob_at_head']}, at the freeze {own['blob_at_freeze']})"
    return out


# ----------------------------------------------------------------------------- the store


@dataclass
class Store:
    dir: Path
    run: str
    cells: pd.DataFrame  # the cell table, indexed by cell
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
        """The per-text kl_mean of a cell, float32 as stored, in text order."""
        assert name in self.kl.index, f"{self.dir.name}: no cell {name!r}"
        return self.kl.loc[name].to_numpy(np.float32)


def expected_cells(run: str, draws: int) -> list[Cell]:
    """The cells a tier-6 store holds: the tier-6 cells, the secondary form's tier-3 cells (rungs 2 and 3, every draw), the four references,
    and the canary. `tests/test_analysis_s11.py` holds this to the launch's own selection on the main run."""
    from vpd_audit.tier6 import canary_cells, reference_cells

    t3 = [Cell(run, "rounded_own_g", "E", "D_unif", TAU_PRIMARY, "r0", "excluded", k, r, "none", 3) for k in range(draws) for r in BINARY_EXISTING_RUNGS]
    return tier_6_cells(run, draws) + t3 + reference_cells(run) + canary_cells(run)


def load_store(store_dir: Path) -> Store:
    from vpd_audit.two_paths import _cell_from_row

    d = Path(store_dir)
    for needed in ("cells.parquet", "per_sequence.parquet", "run_manifest.json", "marker.json"):
        assert (d / needed).is_file(), f"{d}: a store without {needed}"
    assert not (d / "error.txt").is_file(), f"{d}: the launch recorded a failure of this store (error.txt)"
    cells, rows = pd.read_parquet(d / "cells.parquet"), pd.read_parquet(d / "per_sequence.parquet")
    manifest, marker = json.loads((d / "run_manifest.json").read_text()), json.loads((d / "marker.json").read_text())
    runs, sets = sorted(cells["run"].unique()), sorted(cells["eval_set"].unique())
    assert len(runs) == 1 and sets == ["E"] and manifest.get("run") == runs[0], (d, runs, sets, manifest.get("run"))
    assert not cells["cell"].duplicated().any(), f"{d}: a cell appears twice in the cell table"
    objects = {r["cell"]: _cell_from_row(r) for _, r in cells.iterrows()}
    assert all(o.name == name for name, o in objects.items()), f"{d}: a cell rebuilt from its row does not carry its own name"
    kl = rows.pivot(index="cell", columns="seq", values="kl_mean").sort_index(axis=1)
    return Store(dir=d, run=runs[0], cells=cells.set_index("cell", drop=False), rows=rows, manifest=manifest, marker=marker, objects=objects, kl=kl)


def assert_complete(s: Store) -> dict[str, Any]:
    """Every sub-batch done, the manifest finished, exactly the expected cells, each holding every text once with a finite divergence."""
    n_sub = (s.n + int(s.marker["subbatch"]) - 1) // int(s.marker["subbatch"])
    assert int(s.marker["done_through"]) == n_sub - 1 and int(s.marker["n_sequences"]) == s.n, f"{s.dir.name}: not complete (done through sub-batch {s.marker['done_through']} of {n_sub})"
    assert s.manifest.get("finished_at"), f"{s.dir.name}: the run manifest was never marked finished"
    assert set(s.rows["cell"].unique()) == set(s.cells.index) == set(s.marker["cells"]), f"{s.dir.name}: the rows, the cell table, and the marker do not hold the same cells"
    counts = s.rows.groupby("cell")["seq"].agg(["count", "nunique", "min", "max"])
    assert (counts["count"] == s.n).all() and (counts["nunique"] == s.n).all() and (counts["min"] == 0).all() and (counts["max"] == s.n - 1).all(), f"{s.dir.name}: a cell does not hold every text exactly once"
    assert np.array_equal(s.kl.columns.to_numpy(), np.arange(s.n)) and np.isfinite(s.kl.to_numpy(np.float64)).all(), f"{s.dir.name}: a per-text divergence that is missing or not finite"
    want = {c.name: c for c in expected_cells(s.run, s.n_draws)}
    assert set(s.objects) == set(want), f"{s.dir.name}: not the launch's cells: missing {sorted(set(want) - set(s.objects))[:4]}, extra {sorted(set(s.objects) - set(want))[:4]}"
    assert all(s.objects[n] == c for n, c in want.items()), f"{s.dir.name}: a cell's coordinates are not the launch's: {[n for n, c in want.items() if s.objects[n] != c][:4]}"
    assert (s.cells["n_subbatches"].astype(int) == n_sub).all(), f"{s.dir.name}: a cell's marker did not sum every sub-batch"
    return {"store": _rel(s.dir), "n_cells": int(len(s.cells)), "n_texts": s.n, "n_draws": s.n_draws, "n_subbatches": n_sub, "commit": s.manifest.get("commits", {}).get("project"),
            "dirty": s.manifest.get("commits", {}).get("dirty"), "gpu": s.manifest.get("gpu_name"), "precision": s.manifest.get("precision")}


def pick(s: Store, family: str, control: str, rung: str) -> list[Cell]:
    """One form's cells at one size, every draw, in draw order (by predicate on the rebuilt cells, never by a typed name)."""
    cs = sorted((c for c in s.objects.values() if c.family == family and c.control == control and c.rung == rung and c.eval_set == "E" and c.donor_pool == "D_unif"
                 and c.tau == TAU_PRIMARY and c.background == "r0" and c.delta == "excluded"), key=lambda c: c.draw)
    assert [c.draw for c in cs] == list(range(s.n_draws)), f"{family}/{control} at rung {rung}: draws {[c.draw for c in cs]}"
    return cs


def self_cell(s: Store, own_round: float) -> Cell:
    cs = [c for c in s.objects.values() if c.family == "self_union" and c.own_round == own_round]
    assert len(cs) == 1, f"the self-merge rounded at {own_round:g}: {len(cs)} cells"
    return cs[0]


def ref_name(s: Store, condition: str) -> str:
    return f"{s.run}/E/ref/{condition}"


def _rel(p: Any) -> str:
    """A path as written into the outputs: relative to the project where it lies inside it, so that the outputs do not depend on the machine."""
    import os

    a = Path(p).resolve()
    return os.path.relpath(a, env.PROJECT_ROOT) if env.PROJECT_ROOT in a.parents else str(p)


def assert_canary_and_sets(s: Store, committed: Any, log: Any = print) -> dict[str, Any]:
    """The canary: the four references and the headline union at draw 0, rung 2 reproduce their committed per-text divergences bitwise.
    Then every named set of the store's cell table is its committed twin's (the check the launch made, made again on what ran)."""
    from vpd_audit.tier6 import assert_sets_are_committed, canary_cells

    names = [ref_name(s, r) for r in REFERENCES] + [c.name for c in canary_cells(s.run)]
    rows = []
    for name in names:
        assert name in committed, f"THE CANARY CANNOT BE CHECKED: {name} is in no committed store"
        a, b = s.vector(name), committed.kl_mean(name)
        equal = bool(a.shape == b.shape and np.array_equal(a, b))
        assert equal, f"THE CANARY FAILS: {name} does not reproduce its committed per-text kl_mean bitwise ({int((a != b).sum()) if a.shape == b.shape else 'shape'} texts differ)"
        rows.append({"cell": name, "committed_store": _rel(committed.where[name]), "n_texts": int(a.size), "bitwise_equal": equal})
    log(f"[analyze s11] canary pass: {len(rows)} cells bitwise equal to the committed stores over {sum(r['n_texts'] for r in rows)} (cell, text) pairs")
    order = [s.objects[n] for n in s.cells.index]
    records = {n: {"source_sha256": s.cells.loc[n, "source_sha256"], "matched_source_sha256": s.cells.loc[n, "matched_source_sha256"]} for n in s.cells.index}
    sets = assert_sets_are_committed(order, records, committed, log=log)
    return {"canary": rows, "sets": sets["counts"]}


def assert_p3(s: Store) -> dict[str, Any]:
    """Every cell of the primary form (its union cells, its look-alike control, its self-merge) is permitted, so the loop asserted m >= g on
    every sub-batch, and none has an entry below its label; the secondary form's cells are not permitted (their counts are recorded)."""
    from vpd_audit.grid import cell_permitted

    primary = [c for c in s.objects.values() if c.family == ROUNDED0_FAMILY or (c.family == "self_union" and c.own_round == OWN_ROUND_PRIMARY)]
    secondary = [c for c in s.objects.values() if c.family == "rounded_own_g" or (c.family == "self_union" and c.own_round == OWN_ROUND_SECONDARY)]
    assert len(primary) == 2 * len(SIZES) * s.n_draws + 1 and len(secondary) == len(SIZES) * s.n_draws + 1, (len(primary), len(secondary))
    assert all(cell_permitted(c) for c in primary) and not any(cell_permitted(c) for c in secondary), "the permitted labels are not the ones fixed in advance"
    below = s.cells.loc[[c.name for c in primary], "n_below_label_total"].astype(np.int64)
    r = s.rows[s.rows["cell"].isin([c.name for c in primary])]
    assert int(below.sum()) == 0 and int(r["n_below_label"].sum()) == 0 and float(r["min_gap"].min()) >= -PERMITTED_TOL, "P3: a cell of the primary form has an entry below its label"
    return {"primary_cells": len(primary), "primary_entries_below_label": int(below.sum()), "primary_min_gap": float(r["min_gap"].min()),
            "secondary_cells": len(secondary), "secondary_cells_with_entries_below_label": int((s.cells.loc[[c.name for c in secondary], "n_below_label_total"].astype(np.int64) > 0).sum())}


def assert_summary(s: Store) -> dict[str, Any]:
    """The launch's summary beside the store (summary__binary_union.json): no cell failed, and this store among its groups."""
    p = s.dir.parent / "summary__binary_union.json"
    assert p.is_file(), f"no launch summary at {p}"
    summ = json.loads(p.read_text())
    assert int(summ["cells_failed"]) == 0 and not summ["failures"], f"the launch recorded failures: {summ['failures']}"
    assert summ["groups"][s.dir.name]["ok"] is True and int(summ["groups"][s.dir.name]["n_cells"]) == len(s.cells), "the launch summary does not record this store as run whole"
    return {"cells_run": int(summ["cells_run"]), "cells_failed": int(summ["cells_failed"]), "gpu": summ.get("gpu"), "P3": summ.get("preconditions", {}).get("P3", {}).get("pass")}


# ----------------------------------------------------------------------------- the arrays


def committed_store_kl(store: Path, name: str, cache: dict[str, pd.DataFrame] | None = None) -> np.ndarray:
    """A cell's per-text divergence, float32 as stored, from one given committed store; `cache` (one call's own) keeps each table read once."""
    cache = {} if cache is None else cache
    key = str(Path(store).resolve())
    if key not in cache:
        cache[key] = pd.read_parquet(Path(store) / "per_sequence.parquet", columns=["cell", "seq", "kl_mean"])
    r = cache[key]
    r = r[r["cell"] == name].sort_values("seq")
    assert len(r) and np.array_equal(r["seq"].to_numpy(), np.arange(len(r))), f"{store}: {name} does not hold every text once"
    return r["kl_mean"].to_numpy(np.float32)


def fractional(committed: Any, run: str, n_draws: int, n: int) -> dict[str, np.ndarray]:
    """The committed fractional excesses over the text's own labels, per text and draw: the headline union at 8, 16, 64 tokens (K, N) and
    the self-merge (N,), each against the importances of its own committed store (held equal to the first store's, bitwise)."""
    imp_name = f"{run}/E/ref/importances"
    imp = committed.kl_mean(imp_name)
    out: dict[str, np.ndarray] = {}
    checked: set[str] = set()
    cache: dict[str, pd.DataFrame] = {}
    for j in SIZES:
        rows = []
        for k in range(n_draws):
            name = f"{run}/E/union/D_unif/tau{TAU_PRIMARY:g}/r0/excl/k{k}/r{j}"
            assert name in committed, f"the committed comparator {name} is in no committed store"
            own_imp = committed_store_kl(committed.where[name], imp_name, cache)
            if str(committed.where[name]) not in checked:
                assert np.array_equal(own_imp, imp), f"{committed.where[name]}: its importances are not the first committed store's bitwise"
                checked.add(str(committed.where[name]))
            rows.append(committed.kl_mean(name).astype(np.float64) - own_imp.astype(np.float64))
        out[j] = np.stack(rows, axis=0)
    self_name = f"{run}/E/self_union/E/tau{TAU_PRIMARY:g}/r0/excl/k0/r4"
    assert self_name in committed, f"the committed self-merge {self_name} is in no committed store"
    own_imp = committed_store_kl(committed.where[self_name], imp_name, cache)
    assert np.array_equal(own_imp, imp), f"{committed.where[self_name]}: its importances are not the first committed store's bitwise"
    out[SELF] = committed.kl_mean(self_name).astype(np.float64) - own_imp.astype(np.float64)
    assert all(v.shape[-1] == n for v in out.values()), {k: v.shape for k, v in out.items()}
    return out


def excesses(s: Store) -> dict[str, Any]:
    """(K, N) excess matrices over each form's own start, and the (N,) self-merge excesses."""
    kl = lambda name: s.vector(name).astype(np.float64)  # noqa: E731
    r0, r01 = kl(ref_name(s, "rounded_0")), kl(ref_name(s, "rounded_0.1"))
    return {"primary": {j: np.stack([kl(c.name) - r0 for c in pick(s, ROUNDED0_FAMILY, "none", j)]) for j in SIZES},
            "control": {j: np.stack([kl(c.name) - r0 for c in pick(s, ROUNDED0_FAMILY, "marginal", j)]) for j in SIZES},
            "secondary": {j: np.stack([kl(c.name) - r01 for c in pick(s, "rounded_own_g", "none", j)]) for j in SIZES},
            "self_primary": kl(self_cell(s, OWN_ROUND_PRIMARY).name) - r0, "self_secondary": kl(self_cell(s, OWN_ROUND_SECONDARY).name) - r01,
            "absolute": {"rounded_0 (the primary's start)": float(r0.mean()), "rounded_0.1 (the secondary's start)": float(r01.mean()),
                         "self-merge, own labels rounded at 0": float(kl(self_cell(s, OWN_ROUND_PRIMARY).name).mean()), "self-merge, own labels rounded at 0.1": float(kl(self_cell(s, OWN_ROUND_SECONDARY).name).mean())}}


# ----------------------------------------------------------------------------- the reading


def step2(e_bin: dict[str, np.ndarray], s_bin: np.ndarray, frac: dict[str, np.ndarray], resample: st.Resample, *, m: int = M) -> dict[str, Any]:
    """Step 2 (read only if step 1 says fails): each size and the self-merge against its band on point estimates, and the paired difference
    per text and draw against the committed per-text fractional values, with its interval (describes, does not decide)."""
    out: dict[str, Any] = {}
    for j in SIZES + (SELF,):
        b = e_bin[j] if j != SELF else s_bin[None, :]
        f = frac[j] if j != SELF else frac[SELF][None, :]
        assert b.shape == f.shape, (j, b.shape, f.shape)
        e_b, e_f = float(b.mean(axis=0).mean()), float(f.mean(axis=0).mean())
        d = st.paired_difference(b, f, resample, level_m=m)
        out[j] = {"e_bin": e_b, "e_frac": e_f, "band": [BAND_LO * e_f, BAND_HI * e_f], "within_band": within_band(e_b, e_f), "difference": d["mean"], "difference_interval": d["interval"], "read_by_the_rule": j in BAND_SIZES}
    return out


def descriptions(ex: dict[str, Any], frac: dict[str, np.ndarray], resample: st.Resample, *, m: int = M) -> dict[str, Any]:
    """Printed beside the rule and read by none: the secondary form's excesses (with their bump-rule labels) and bands; the look-alike
    control's excess and the primary minus the control, paired per text and draw; the absolute divergences."""
    sec, ctl = {}, {}
    for j in SIZES:
        r = st.union_rung(ex["secondary"][j], resample, m)
        e_f = float(frac[j].mean())
        sec[j] = {"excess": r["e_hat"], "interval": r["interval"], "n_draws_positive": r["n_draws_positive"], "detected": r["detected"], "material": r["material"], "band": [BAND_LO * e_f, BAND_HI * e_f], "within_band": within_band(r["e_hat"], e_f)}
        c = st.union_rung(ex["control"][j], resample, m)
        d = st.paired_difference(ex["primary"][j], ex["control"][j], resample, level_m=m)
        ctl[j] = {"control_excess": c["e_hat"], "control_interval": c["interval"], "primary_minus_control": d["mean"], "primary_minus_control_interval": d["interval"]}
    rs = s9.self_merge_rule(ex["self_secondary"], resample, m=m)
    e_f = float(frac[SELF].mean())
    sec[SELF] = {"excess": rs["s_hat"], "interval": rs["interval"], "n_draws_positive": None, "detected": None, "material": rs["material"], "band": [BAND_LO * e_f, BAND_HI * e_f], "within_band": within_band(rs["s_hat"], e_f)}
    return {"secondary": sec, "control": ctl, "absolute": ex["absolute"]}


def assert_comparators(frac: dict[str, np.ndarray], expected: dict[str, float] | None) -> dict[str, Any]:
    """The committed fractional excesses, recomputed; on the paper's run they must be the table fixed in advance, to four decimals."""
    got = {j: float(frac[j].mean()) for j in SIZES + (SELF,)}
    if expected is not None:
        bad = {j: (got[j], expected[j]) for j in expected if not abs(got[j] - expected[j]) <= 5e-5 + 1e-12}
        assert not bad, f"the committed fractional comparators are not the table fixed in advance, to four decimals: {bad}"
    return {"recomputed": got, "registered_table": expected}


# ----------------------------------------------------------------------------- the outputs


def _fmt(v: Any) -> str:
    if v is None:
        return ""
    if isinstance(v, (bool, np.bool_)):
        return "yes" if v else "no"
    if isinstance(v, (float, np.floating)):
        return "" if np.isnan(v) else f"{v:+.4f}"
    if isinstance(v, (list, tuple)):
        return "[" + ", ".join(_fmt(x) for x in v) + "]"
    return str(v)


def _md(df: pd.DataFrame) -> str:
    cols = list(df.columns)
    L = ["| " + " | ".join(cols) + " |", "|" + "---|" * len(cols)]
    for _, row in df.iterrows():
        L.append("| " + " | ".join(_fmt(row[c]) for c in cols) + " |")
    return "\n".join(L)


def _lohi(prefix: str, iv: Any) -> dict[str, float]:
    ok = isinstance(iv, (list, tuple)) and len(iv) == 2 and all(x is not None for x in iv)
    return {f"{prefix}_lo": float(iv[0]) if ok else float("nan"), f"{prefix}_hi": float(iv[1]) if ok else float("nan")}


def write_outputs(out_dir: Path, ctx: dict[str, Any]) -> Path:
    """report.md and one CSV per table; nothing in them depends on the time or the machine, so two runs give the same bytes."""
    out_dir.mkdir(parents=True, exist_ok=True)
    s1 = ctx["step1"]
    step1_rows = [{"size": SIZE_WORDS[j], "rung": j, "excess": v["e_hat"], **_lohi("interval", v["interval"]), "per_draw_means": v["per_draw"], "n_draws_positive": v["n_draws_positive"], "n_draws": v["n_draws"],
                   "sign_condition": v["sign_condition"], "detected": v["detected"], "material": v["material"]} for j, v in s1["per_size"].items()]
    step1_rows.append({"size": SIZE_WORDS[SELF], "rung": SELF, "excess": s1["self"]["s_hat"], **_lohi("interval", s1["self"]["interval"]), "per_draw_means": None, "n_draws_positive": None, "n_draws": None,
                       "sign_condition": None, "detected": None, "material": s1["self"]["material"]})
    tables: dict[str, pd.DataFrame] = {"s11_step1": pd.DataFrame(step1_rows),
                                       "s11_verdict": pd.DataFrame([{"outcome": ctx["outcome"], "verdict": s1["verdict"], "reason": s1["reason"], "band_sizes": ", ".join(SIZE_WORDS[j] for j in BAND_SIZES)}]),
                                       "s11_canary": pd.DataFrame(ctx["checks"]["canary"]["canary"]),
                                       "s11_frozen_modules": pd.DataFrame(ctx["guard"]["frozen_modules"] + [ctx["guard"]["this_module"]] + ctx["guard"]["recorded_modules"])}
    if ctx.get("step2"):
        tables["s11_step2"] = pd.DataFrame([{"size": SIZE_WORDS[j], "rung": j, "binary_excess": v["e_bin"], "fractional_excess": v["e_frac"], **_lohi("band", v["band"]), "within_band": v["within_band"], "read_by_the_rule": v["read_by_the_rule"],
                                              "paired_difference": v["difference"], **_lohi("paired_difference_interval", v["difference_interval"])} for j, v in ctx["step2"].items()])
    if ctx.get("descriptions"):
        de = ctx["descriptions"]
        tables["s11_secondary"] = pd.DataFrame([{"size": SIZE_WORDS[j], "rung": j, "excess_over_rounded_0.1": v["excess"], **_lohi("interval", v["interval"]), "n_draws_positive": v["n_draws_positive"], "detected": v["detected"],
                                                  "material": v["material"], **_lohi("band", v["band"]), "within_band": v["within_band"]} for j, v in de["secondary"].items()])
        tables["s11_control"] = pd.DataFrame([{"size": SIZE_WORDS[j], "rung": j, "control_excess_over_rounded_0": v["control_excess"], **_lohi("control_interval", v["control_interval"]),
                                                "primary_minus_control": v["primary_minus_control"], **_lohi("primary_minus_control_interval", v["primary_minus_control_interval"])} for j, v in de["control"].items()])
        tables["s11_absolute"] = pd.DataFrame([{"mask": k, "mean_divergence": v} for k, v in de["absolute"].items()])
    for name, df in tables.items():
        df.to_csv(out_dir / f"{name}.csv", index=False, lineterminator="\n")
    T, g, ch = tables, ctx["guard"], ctx["checks"]
    word = ctx["outcome"]
    L = [f"# Outcome: {word}" + (f" ({s1['reason']})" if word == STOP else ""), "",
         f"The binary union on {ctx['run']}, read by the rule fixed before any store of the run existed. The primary form (own labels rounded at 0, start `rounded_0`) decides; "
         "the secondary form and the look-alike control are described beside it and no rule reads them. Every interval is a text bootstrap over the texts of E with the draws held fixed, "
         f"{ctx['replicates']} replicates, percentile, at level 1 - 0.05/{M}; material means the lower end exceeds {X:g} nats.", "",
         f"{WORDING_C} {WORDING_ASYMMETRY}", "",
         "## 0. What was asserted before anything was read", "",
         f"- The guard: commit {g['commit'].get('project', '?')[:12]}, dirty flag {g['commit'].get('dirty')}, freeze {g['freeze']} (HEAD or its ancestor: {g['freeze_is_head_or_its_ancestor']}), enforced: {g['enforced']}. "
         f"This module's blob on disk, at HEAD, at the freeze: {g['this_module']['blob_on_disk'][:12]}, {str(g['this_module']['blob_at_head'])[:12]}, {str(g['this_module']['blob_at_freeze'])[:12]}. "
         f"The nine frozen modules against {g['against']} ({g['against_commit'][:12]}): {'all equal' if g['frozen_modules_pass'] else 'NOT all equal'} (s11_frozen_modules.csv).",
         f"- The store {ch['complete']['store']}: {ch['complete']['n_cells']} cells, {ch['complete']['n_texts']} texts, {ch['complete']['n_draws']} draws, complete; launched at commit {str(ch['complete']['commit'])[:12]} (dirty flag {ch['complete']['dirty']}) on {ch['complete']['gpu']}, {ch['complete']['precision']}."
         + (f" The launch summary: {ch['summary']['cells_run']} cells run, {ch['summary']['cells_failed']} failed, P3 {ch['summary']['P3']}." if ch.get("summary") else ""),
         f"- The canary: {len(ch['canary']['canary'])} cells (the four references and the headline union at draw 0, rung 2) bitwise equal to their committed per-text divergences. Every named set equal to its committed twin's: {ch['canary']['sets']}.",
         f"- P3 on the primary form: {ch['p3']['primary_cells']} permitted cells, {ch['p3']['primary_entries_below_label']} entries below their label, smallest m - g {ch['p3']['primary_min_gap']:.3g}; the secondary form's {ch['p3']['secondary_cells']} cells are not permitted ({ch['p3']['secondary_cells_with_entries_below_label']} with entries below their label, as rounding at 0.1 must give).",
         "- The committed fractional comparators, recomputed: " + ", ".join(f"{SIZE_WORDS[j]} {v:.4f}" for j, v in ctx["comparators"]["recomputed"].items()) + (" (equal to the table fixed in advance, to four decimals)." if ctx["comparators"]["registered_table"] else " (no table to hold them to on this run)."), "",
         "## 1. Step 1: the verdict (the primary form)", "",
         _md(T["s11_step1"][["size", "excess", "interval_lo", "interval_hi", "n_draws_positive", "sign_condition", "detected", "material"]]), "",
         f"**Verdict: {s1['verdict']}**" + (f" ({s1['reason']})" if s1["reason"] else "") + ".", ""]
    if word == STOP:
        L += ["The reading stops here (step 1): nothing further is read.", ""]
    else:
        if ctx.get("step2"):
            L += ["## 2. Step 2: the size (read because step 1 says fails)", "",
                  f"Within the band means 1/2 e_frac <= e_bin <= 2 e_frac on point estimates, against the committed fractional excesses over the text's own labels. Outcome A needs every one of {', '.join(SIZE_WORDS[j] for j in BAND_SIZES)} within its band. "
                  "The paired difference is per text and draw against the committed per-text fractional values; it describes and does not decide.", "",
                  _md(T["s11_step2"][["size", "binary_excess", "fractional_excess", "band_lo", "band_hi", "within_band", "read_by_the_rule", "paired_difference", "paired_difference_interval_lo", "paired_difference_interval_hi"]]), ""]
        else:
            L += ["## 2. Step 2: not read (step 1 does not say fails)", ""]
        L += [f"**Outcome: {word}.**", "", "## 3. Descriptions (no rule reads them)", "",
              "The secondary form (own labels rounded at 0.1, start `rounded_0.1`), its excesses with the bump rule's labels and its bands against the same fractional comparators:", "",
              _md(T["s11_secondary"][["size", "excess_over_rounded_0.1", "interval_lo", "interval_hi", "n_draws_positive", "detected", "material", "band_lo", "band_hi", "within_band"]]), "",
              "The look-alike control (the committed tier-4 sets in the primary form's mask), its excess over `rounded_0`, and the primary form minus the control, paired per text and draw:", "",
              _md(T["s11_control"][["size", "control_excess_over_rounded_0", "control_interval_lo", "control_interval_hi", "primary_minus_control", "primary_minus_control_interval_lo", "primary_minus_control_interval_hi"]]), "",
              "The absolute divergences (mean over the texts of E, nats):", "", _md(T["s11_absolute"]), "",
              "No switched mass is printed for either binary family: `masks.switched_mass` computes the union's (1 - g) over the named entries and ignores the rounding.", ""]
    path = out_dir / "report.md"
    path.write_text("\n".join(L) + "\n")
    return path


def _jsonable(o: Any) -> Any:
    if isinstance(o, dict):
        return {str(k): _jsonable(v) for k, v in o.items()}
    if isinstance(o, (list, tuple)):
        return [_jsonable(x) for x in o]
    if isinstance(o, (np.bool_,)):
        return bool(o)
    if isinstance(o, (np.integer,)):
        return int(o)
    if isinstance(o, (np.floating,)):
        return float(o)
    return o


def analyze_s11(store_dir: Path, out_dir: Path, *, run: str, committed_roots: tuple[Path, ...], freeze: str | None = None, replicates: int = st.N_REPLICATES, master_seed: int = 0,
                expected_comparators: dict[str, float] | None = None, log: Any = print) -> dict[str, Any]:
    """The whole reading. The guard runs before any file of the store is opened; the store must then be of `run`. `expected_comparators`:
    the table fixed in advance (REGISTERED_COMPARATORS) on the paper's run, whatever is passed; None elsewhere unless given. The tests hand in planted
    stores and roots under a run that is not the paper's."""
    from vpd_audit.tier5 import CommittedTables

    paper = run in PAPER_RUNS
    guard = freeze_guard(freeze, enforce=paper, log=log)  # prints every blob, then refuses if it must
    store = load_store(Path(store_dir))
    assert store.run == run, f"the store is of run {store.run!r}, not {run!r}"
    if paper:
        assert store.n == N_TEXTS_E and store.n_draws == N_DRAWS, (store.n, store.n_draws)
        expected_comparators = REGISTERED_COMPARATORS
    for r in committed_roots:
        a, b = Path(r).resolve(), Path(store_dir).resolve()
        assert a.is_dir() and a != b and a not in b.parents and b not in a.parents, f"the committed root {r} and the store {store_dir} overlap, or the root is absent"
    committed = CommittedTables(tuple(Path(r) for r in committed_roots))
    checks: dict[str, Any] = {"complete": assert_complete(store)}
    checks["summary"] = assert_summary(store) if paper else (assert_summary(store) if (store.dir.parent / "summary__binary_union.json").is_file() else None)
    checks["canary"] = assert_canary_and_sets(store, committed, log)
    checks["p3"] = assert_p3(store)
    frac = fractional(committed, store.run, store.n_draws, store.n)
    comparators = assert_comparators(frac, expected_comparators)
    ex = excesses(store)
    rs = st.Resample.make(store.n, replicates, (master_seed, "boot", "E"))
    s1 = step1(ex["primary"], ex["self_primary"], rs)
    log(f"[analyze s11] step 1: {s1['verdict']}" + (f" ({s1['reason']})" if s1["reason"] else ""))
    ctx: dict[str, Any] = {"run": store.run, "replicates": replicates, "master_seed": master_seed, "guard": guard, "checks": checks, "comparators": comparators, "step1": s1}
    if s1["verdict"] == STOP:
        ctx["outcome"] = STOP
    else:
        ctx["step2"] = step2(ex["primary"], ex["self_primary"], frac, rs) if s1["verdict"] == FAILS else None
        ctx["outcome"] = outcome(s1["verdict"], {j: v["within_band"] for j, v in ctx["step2"].items()} if ctx["step2"] else None)
        ctx["descriptions"] = descriptions(ex, frac, rs)
    path = write_outputs(Path(out_dir), ctx)
    summary = {"run": store.run, "outcome": ctx["outcome"], "verdict": s1["verdict"], "reason": s1["reason"], "freeze": freeze, "commit": guard["commit"], "replicates": replicates, "master_seed": master_seed,
               "band_sizes": list(BAND_SIZES), "step1": {j: {k: v[k] for k in ("e_hat", "interval", "n_draws_positive", "detected", "material")} for j, v in s1["per_size"].items()},
               "self": {k: s1["self"][k] for k in ("s_hat", "interval", "material")}, "step2": ctx.get("step2"), "comparators": comparators, "checks": checks}
    with open(Path(out_dir) / "summary.json", "w") as f:
        json.dump(_jsonable(summary), f, indent=2, sort_keys=True)
    log(f"[analyze s11] outcome {ctx['outcome']}; report written to {path}")
    return summary
