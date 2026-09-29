"""The analysis of the grid: loads the stores, asserts what the registered rules assert, builds every chain's arrays,
applies the rules of `stats.py`, and writes the report in the pre-registered read order with every table as CSV and
every figure as PNG with its data beside it. CPU only.

Blindness, mechanically: a store whose manifest names the run `main` or `control` is refused unless `frozen` is
given and equals the current commit of the working tree. Nothing here prints a per-cell divergence; the values go into
report.md and the CSVs under the output directory, which nobody opens before the freeze.
"""

from __future__ import annotations

import json
import math
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from vpd_audit import env
from vpd_audit import stats as st
from vpd_audit.cells import HARD_ZERO_FAMILIES, Cell, reference_for
from vpd_audit.constants import SEQ_LEN
from vpd_audit.grid import _chain_key, cell_permitted
from vpd_audit.results import code_commits
from vpd_audit.sources import SUB_RUNGS
from vpd_audit.two_paths import CELL_FIELDS, _cell_from_row

CELL_COLUMNS = list(CELL_FIELDS)
PAPER_RUNS = ("main", "control")
STRATUM_GITHUB = "Github"
# the level cells and the ranked never-named pair carry no verdict; no rule of stats.py is applied to them (they have
# descriptive tables of their own). They are loaded, chained, and checked (P3, P4, the pre-reads' t*, the two-path
# recompute) like any other cell.
DESCRIPTIVE_FAMILIES = ("level", "never_named_ranked")


# ----------------------------------------------------------------------------- stores and the grid


@dataclass
class Store:
    dir: Path
    name: str
    run: str
    eval_set: str
    cells: pd.DataFrame
    rows: pd.DataFrame
    manifest: dict[str, Any]
    marker: dict[str, Any]


@dataclass
class SetData:
    eval_set: str
    n_sequences: int
    set_hash: str
    rows: pd.DataFrame  # one row per (cell, seq), references deduplicated after the assert
    cells: pd.DataFrame  # one row per cell (cells.parquet columns), indexed by cell
    cell_objects: dict[str, Cell]
    stores: list[Store]
    _wide: dict[str, pd.DataFrame] = field(default_factory=dict)

    def wide(self, column: str) -> pd.DataFrame:
        if column not in self._wide:
            self._wide[column] = self.rows.pivot(index="cell", columns="seq", values=column).sort_index(axis=1)
        return self._wide[column]

    def vector(self, cell: str, column: str) -> np.ndarray:
        return self.wide(column).loc[cell].to_numpy()


@dataclass
class Grid:
    run: str
    root: Path
    sets: dict[str, SetData]
    stores: list[Store]
    reference_assert: dict[str, Any]


def discover_stores(root: Path) -> list[Store]:
    root = Path(root)
    out = []
    for p in sorted(root.rglob("cells.parquet")):
        d = p.parent
        if not (d / "per_sequence.parquet").is_file() or not (d / "run_manifest.json").is_file():
            continue
        if "analysis" in d.parts or "pre_reads" in d.parts or d.name.endswith("_resume") or any(p.startswith("verify") for p in d.parts):
            continue  # the verification store repeats tier 1's cell names: it is the canary's input, never a store of the grid
        cells = pd.read_parquet(p)
        rows = pd.read_parquet(d / "per_sequence.parquet")
        with open(d / "run_manifest.json") as f:
            manifest = json.load(f)
        marker = json.load(open(d / "marker.json")) if (d / "marker.json").is_file() else {}
        eval_sets = sorted(cells["eval_set"].unique())
        assert len(eval_sets) == 1, (d, eval_sets)
        runs = sorted(cells["run"].unique())
        assert len(runs) == 1, (d, runs)
        out.append(Store(dir=d, name=str(d.relative_to(root)), run=runs[0], eval_set=eval_sets[0], cells=cells, rows=rows, manifest=manifest, marker=marker))
    return out


def check_blindness(stores: list[Store], frozen: str | None) -> dict[str, Any]:
    paper = [s for s in stores if s.run in PAPER_RUNS or s.manifest.get("run") in PAPER_RUNS]
    commit = code_commits()
    if paper:
        assert frozen is not None, "stores of the paper's model: give --frozen <hash>, the commit the analysis code was frozen at"
        assert commit["project"].startswith(frozen) and len(frozen) >= 7, f"--frozen {frozen} is not the current commit {commit['project'][:12]}"
        assert commit["dirty"] == "0", "stores of the paper's model: the working tree must be clean (the dirty flag is 1)"
    return {"paper_model_stores": len(paper), "frozen": frozen, "commit": commit}


def _assert_references_bitwise(stores: list[Store]) -> dict[str, Any]:
    """Every store of a set carries the full reference set; they must agree bitwise on kl_mean, ce, mask_fp."""
    ref_rows = [s.rows[s.rows["cell"].str.contains("/ref/")].set_index(["cell", "seq"]).sort_index() for s in stores]
    base = ref_rows[0]
    checks = []
    for s, r in zip(stores[1:], ref_rows[1:]):
        common = base.index.intersection(r.index)
        eq = {"kl_mean": bool(np.array_equal(base.loc[common, "kl_mean"].to_numpy(np.float32), r.loc[common, "kl_mean"].to_numpy(np.float32))),
              "ce": bool(np.array_equal(base.loc[common, "ce"].to_numpy(np.float32), r.loc[common, "ce"].to_numpy(np.float32), equal_nan=True)),
              "mask_fp": bool((base.loc[common, "mask_fp"].fillna("").to_numpy() == r.loc[common, "mask_fp"].fillna("").to_numpy()).all())}
        checks.append({"store": s.name, "against": stores[0].name, "n_pairs": int(len(common)), "n_pairs_expected": int(len(base)), **eq, "pass": all(eq.values()) and len(common) == len(base) == len(r)})
    assert all(c["pass"] for c in checks), f"the references differ between stores of the same set: {[c for c in checks if not c['pass']]}"
    return {"n_stores": len(stores), "n_reference_cells": int(base.reset_index()["cell"].nunique()), "checks": checks}


def _assert_canaries_bitwise(stores: list[Store], run: str) -> tuple[dict[str, Any], dict[str, set[str]]]:
    """A tier-4 store reruns curve 1's union and its plain control at rung 2, draw 0, under their
    own names. They are the only cells a second store of a set may repeat; each must equal its first occurrence bitwise on
    kl_mean and mask_fp per sequence and on the source hash and the applied-mask digest, and the repeat is then dropped.
    Returns the record and, per store name, the cell names to drop from it."""
    from vpd_audit.cells import marginal_canaries

    allowed = {c.name for c in marginal_canaries(run)}
    first: dict[str, Store] = {}
    checks, drop = [], {}
    for s_ in stores:
        for name in s_.cells["cell"]:
            if "/ref/" in name:
                continue
            if name not in first:
                first[name] = s_
                continue
            assert name in allowed, f"cells present in more than one store of {s_.eval_set}: {name} (in {first[name].name} and {s_.name}); only the canaries of tier 4 may repeat"
            a, b = first[name].rows[first[name].rows["cell"] == name].sort_values("seq"), s_.rows[s_.rows["cell"] == name].sort_values("seq")
            ca, cb = first[name].cells.set_index("cell").loc[name], s_.cells.set_index("cell").loc[name]
            eq = {"kl_mean": bool(np.array_equal(a["kl_mean"].to_numpy(np.float32), b["kl_mean"].to_numpy(np.float32))), "mask_fp": bool((a["mask_fp"].fillna("").to_numpy() == b["mask_fp"].fillna("").to_numpy()).all()),
                  "sigma": bool(np.array_equal(a["sigma"].to_numpy(np.float32), b["sigma"].to_numpy(np.float32), equal_nan=True)), "source_sha256": bool(ca["source_sha256"] == cb["source_sha256"]),
                  "mask_fp_cell": bool(ca["mask_fp_cell"] == cb["mask_fp_cell"])}
            checks.append({"cell": name, "store": s_.name, "against": first[name].name, "n_sequences": int(len(b)), **eq, "pass": all(eq.values()) and len(a) == len(b)})
            drop.setdefault(s_.name, set()).add(name)
    assert all(c["pass"] for c in checks), f"a canary differs from its first run: {[c for c in checks if not c['pass']]}"
    return {"n_canaries": len(checks), "checks": checks}, drop


def load_grid(root: Path, *, frozen: str | None = None, only_sets: tuple[str, ...] | None = None, extra_roots: tuple[Path, ...] = ()) -> Grid:
    """`extra_roots`: further roots whose stores join this grid's sets, after the root's own. The stand-in's tier-4
    dry run lives in a root of its own (results/dry_run_s7) beside results/dry_run; the paper's tier 4 is under the run's root."""
    stores = discover_stores(root)
    for extra in extra_roots:
        more = discover_stores(extra)
        for s_ in more:
            s_.name = f"{Path(extra).name}/{s_.name}"
        stores += more
    assert stores, f"no stores under {root}"
    check_blindness(stores, frozen)
    runs = sorted({s.run for s in stores})
    assert len(runs) == 1, runs
    sets: dict[str, SetData] = {}
    ref_assert: dict[str, Any] = {}
    # E and E_lab are joined across stores (tiers); every donor-side store is a set of its own (its own donor sequences)
    groups: dict[str, list[Store]] = {}
    for s in stores:
        groups.setdefault(s.name if s.eval_set == "donors" else s.eval_set, []).append(s)
    for key in sorted(groups):
        ss = groups[key]
        eval_set = ss[0].eval_set
        if only_sets is not None and eval_set not in only_sets:
            continue
        ref_assert[key] = _assert_references_bitwise(ss) if len(ss) > 1 else {"n_stores": 1, "checks": []}
        canaries, drop = _assert_canaries_bitwise(ss, runs[0]) if len(ss) > 1 else ({"n_canaries": 0, "checks": []}, {})
        if canaries["n_canaries"]:  # tier 4: recorded only where a store repeats a canary, so that every earlier context is what it was
            ref_assert[key]["canaries"] = canaries
        rows = pd.concat([ss[0].rows] + [s.rows[~s.rows["cell"].str.contains("/ref/") & ~s.rows["cell"].isin(drop.get(s.name, ()))] for s in ss[1:]], ignore_index=True)
        cells = pd.concat([ss[0].cells] + [s.cells[~s.cells["cell"].str.contains("/ref/") & ~s.cells["cell"].isin(drop.get(s.name, ()))] for s in ss[1:]], ignore_index=True)
        dup = cells["cell"][cells["cell"].duplicated()].tolist()
        assert not dup, f"cells present in more than one store of {eval_set}: {dup[:5]}"
        n_seq = int(rows["seq"].max()) + 1
        assert rows.groupby("cell")["seq"].count().eq(n_seq).all(), "every cell must hold every sequence of its set"
        objects = {r["cell"]: _cell_from_row(r) for _, r in cells.iterrows()}
        sets[key] = SetData(eval_set, n_seq, ss[0].manifest.get("set_hash", ""), rows, cells.set_index("cell"), objects, ss)
    return Grid(run=runs[0], root=Path(root), sets=sets, stores=stores, reference_assert=ref_assert)


def restrict_tiers(grid: Grid, tiers: tuple[int, ...]) -> Grid:
    """The grid with only the cells of the given tiers (the references kept): for `--tiers` on a store that mixes tiers
    (the dry run), and for reading tier 1 alone with the controls absent."""
    sets = {}
    for key, sd in grid.sets.items():
        keep = [c for c, o in sd.cell_objects.items() if o.tier in tiers or o.family == "reference"]
        rows = sd.rows[sd.rows["cell"].isin(keep)].reset_index(drop=True)
        cells = sd.cells.loc[[c for c in sd.cells.index if c in keep]]
        sets[key] = SetData(sd.eval_set, sd.n_sequences, sd.set_hash, rows, cells, {c: sd.cell_objects[c] for c in keep}, sd.stores)
    return Grid(run=grid.run, root=grid.root, sets=sets, stores=grid.stores, reference_assert=grid.reference_assert)


# ----------------------------------------------------------------------------- the canary against the verification store


def assert_verify_canary(grid: Grid, verify_dir: Path) -> dict[str, Any]:
    """The cells of the verification store that the grid repeats: equality only, never a value."""
    if not (Path(verify_dir) / "per_sequence.parquet").is_file():
        return {"available": False}
    v = pd.read_parquet(Path(verify_dir) / "per_sequence.parquet")
    v = v[~v["cell"].str.contains("/ref/")].set_index(["cell", "seq"]).sort_index()
    out = {"available": True, "cells": {}}
    for eval_set, sd in grid.sets.items():
        g = sd.rows.set_index(["cell", "seq"]).sort_index()
        common_cells = sorted(set(v.index.get_level_values(0)) & set(sd.cells.index))
        for c in common_cells:
            a, b = v.loc[c, "kl_mean"].to_numpy(np.float32), g.loc[c, "kl_mean"].to_numpy(np.float32)
            out["cells"][c] = bool(a.shape == b.shape and np.array_equal(a, b))
    out["n_cells"] = len(out["cells"])
    out["pass"] = all(out["cells"].values())
    assert out["pass"], f"the verification store's cells differ from the grid's on kl_mean: {[c for c, ok in out['cells'].items() if not ok]}"
    return out


# ----------------------------------------------------------------------------- the pre-reads


@dataclass
class PreReads:
    dir: Path
    testability: pd.DataFrame
    overlap: pd.DataFrame
    summary: dict[str, Any]
    t_star: pd.DataFrame
    sigma: dict[str, pd.DataFrame]


def load_pre_reads(pre_dir: Path) -> PreReads | None:
    d = Path(pre_dir)
    if not (d / "summary.json").is_file():
        return None
    t = pd.read_parquet(d / "t_star.parquet")
    t["cell"] = t["cell"].astype(str)
    sigma = {s: pd.read_parquet(d / f"sigma_{s}.parquet") for s in ("E", "E_lab") if (d / f"sigma_{s}.parquet").is_file()}
    return PreReads(d, pd.read_csv(d / "testability.csv", dtype={"rung": str}), pd.read_csv(d / "overlap_union_vs_control.csv", dtype={"rung": str}), json.load(open(d / "summary.json")), t, sigma)


def assert_pre_reads(grid: Grid, pre: PreReads) -> dict[str, Any]:
    """The loop's t_star columns equal the pre-reads' bitwise for every hard-zero cell present; the loop's sigma equals the
    pre-reads' to a relative 1e-5 with an absolute floor of 1e-6 for every cell under a non-uniform background."""
    out: dict[str, Any] = {"t_star": {}, "sigma": {}}
    for eval_set, sd in grid.sets.items():
        hz = [c for c, o in sd.cell_objects.items() if o.is_hard_zero]
        rows = sd.rows[sd.rows["cell"].isin(hz)]
        merged = rows.merge(pre.t_star, on=["cell", "seq"], suffixes=("_loop", "_pre"))
        assert len(merged) == len(rows), f"{eval_set}: the pre-reads hold t* for {merged['cell'].nunique()} of the {len(hz)} hard-zero cells"
        eq = {col: bool(np.array_equal(merged[f"{col}_loop"].to_numpy(np.int64), merged[f"{col}_pre"].to_numpy(np.int64))) for col in ("t_star_0.1", "t_star_0", "n_touched_0.1", "n_touched_0")}
        out["t_star"][eval_set] = {"n_cells": len(hz), "n_rows": int(len(merged)), **eq}
        assert all(eq.values()), f"{eval_set}: the loop's t* columns differ from the pre-reads': {eq}"
        if eval_set in pre.sigma:
            wide = pre.sigma[eval_set].set_index("seq")
            nonuni = [c for c, o in sd.cell_objects.items() if o.background != "uniform" and o.family != "reference" and o.donor_side_reference is None and c in wide.columns]
            worst, n = 0.0, 0
            for c in nonuni:
                loop = sd.vector(c, "sigma").astype(np.float64)
                ref = wide[c].to_numpy(np.float64)
                tol = 1e-5 * np.abs(ref) + 1e-6
                worst = max(worst, float((np.abs(loop - ref) / tol).max()))
                n += 1
            out["sigma"][eval_set] = {"n_cells": n, "max_ratio_to_tolerance": worst, "pass": worst <= 1.0}
            assert worst <= 1.0, f"{eval_set}: the loop's sigma differs from the pre-reads' beyond 1e-5 relative (ratio {worst:.3f})"
    return out


# ----------------------------------------------------------------------------- strata and labels


def load_strata(grid: Grid) -> dict[str, Any]:
    out: dict[str, Any] = {}
    if "E_lab" in grid.sets:
        sd = grid.sets["E_lab"]
        if grid.run in PAPER_RUNS:
            with open(env.PROJECT_ROOT / "results" / "data" / "labeled_manifest.json") as f:
                m = json.load(f)["sets"]["E_lab"]
            strata = list(m["strata"])
            assert m["sha256_ids"] == sd.set_hash, "E_lab's strata file does not match the store's set hash"
            positive = STRATUM_GITHUB
        else:
            p = env.SETS_DIR / f"{sd.stores[0].manifest.get('set_name', 'E_lab_dry')}.strata.json"
            with open(p) as f:
                strata = list(json.load(f)["strata"])
            positive = "dialogue"
        assert len(strata) == sd.n_sequences
        arr = np.asarray(strata)
        out["E_lab"] = {"labels": strata, "positive": positive, "groups": {"all": np.ones(len(arr), bool), positive: arr == positive, "other": arr != positive, **{s: arr == s for s in sorted(set(strata)) if s != positive}}}
    if "E" in grid.sets and grid.run in PAPER_RUNS:
        p = env.PROJECT_ROOT / "results" / "data" / "reader_labels" / "labels_first_pass.tsv"
        if p.is_file():
            df = pd.read_csv(p, sep="\t")
            df = df[df["set"] == "E"].sort_values("seq")
            if len(df) == grid.sets["E"].n_sequences:
                arr = df["label"].to_numpy()
                out["E_reader"] = {"labels": arr.tolist(), "groups": {lab: arr == lab for lab in sorted(set(arr))}}
    return out


# ----------------------------------------------------------------------------- chains and matrices


@dataclass
class Chain:
    key: tuple
    family: str
    eval_set: str
    pool: str | None
    tau: float | None
    background: str
    delta: str
    control: str
    draw_if_uniform: int
    rungs: dict[str, list[Cell]]  # rung -> cells sorted by draw
    rank_key: str | None = None  # the ranked pair's ordering key and end, part of the chain (and of the pre-reads' chain key)
    rank_end: str | None = None

    @property
    def label(self) -> str:
        k = f"/k{self.draw_if_uniform}" if self.draw_if_uniform >= 0 else ""
        rank = f"/{self.rank_key}-{self.rank_end}" if self.rank_key else ""
        return f"{self.family}/{self.eval_set}/{self.pool}/tau{self.tau:g}/{self.background}/{self.delta[:4]}{k}/ctl-{self.control}{rank}"

    def rung_order(self) -> list[str]:
        return st.sort_rungs(list(self.rungs))


def build_chains(sd: SetData, *, descriptive: bool = False) -> dict[tuple, Chain]:
    """The chains of a set. Cells flagged `descriptive` (the position rungs 2a and 2b, outside the
    pre-registered comparison count) are left out unless `descriptive` is asked for, so that no rung reaches the frozen
    rules of stats.py that the count did not register; the filter is here, by the flag, never by rung name in stats.py."""
    chains: dict[tuple, Chain] = {}
    for name, c in sd.cell_objects.items():
        if c.family == "reference" or c.eval_set == "donors" or c.donor_side_reference is not None:
            continue
        if bool(c.descriptive) != descriptive:
            continue
        key = _chain_key(c)
        if key not in chains:
            chains[key] = Chain(key, c.family, c.eval_set, c.donor_pool, c.tau, c.background, c.delta, c.control, c.draw if c.background == "uniform" else -1, {}, c.rank_key, c.rank_end)
        chains[key].rungs.setdefault(c.rung, []).append(c)
    for ch in chains.values():
        for r in ch.rungs:
            ch.rungs[r].sort(key=lambda x: x.draw)
    return chains


def ref_cell_name(c: Cell) -> str:
    return f"{c.run}/{c.eval_set}/ref/{reference_for(c)}"


def matrix(sd: SetData, cells: list[Cell], column: str) -> np.ndarray:
    return np.stack([sd.vector(c.name, column) for c in cells], axis=0)


def excess_matrix(sd: SetData, cells: list[Cell]) -> np.ndarray:
    """(K, N): the cell's kl_mean minus its rung-0 reference's, paired on the sequence and (under uniform) the draw."""
    return np.stack([sd.vector(c.name, "kl_mean").astype(np.float64) - sd.vector(ref_cell_name(c), "kl_mean").astype(np.float64) for c in cells], axis=0)


# ----------------------------------------------------------------------------- the two-path recompute


def two_path_recompute(sd: SetData) -> dict[str, Any]:
    """d_b recomputed from the loop's kl_prefix_sum column and the reference's float16 array, against the d column.
    Only the reference is rounded here (the cell's prefix sum is the loop's float32 value), so the bound has one float16
    term, plus the float32 rounding of the loop's two sums (the pairwise sum of up to T terms, bounded by
    2^-24 (log2 T + 1) times the prefix sum's magnitude) and of the division, and the floor, times 1 + 2^-10."""
    out: dict[str, Any] = {"n_cells": 0, "n_checks": 0, "n_nan_checks": 0, "max_ratio": 0.0, "max_ratio_at": None, "n_over": 0, "n_nonfinite": 0, "n_nan_mismatch": 0, "missing_arrays": []}
    arrays: dict[str, np.ndarray] = {}
    for name, c in sd.cell_objects.items():
        if not c.is_hard_zero:
            continue
        ref = ref_cell_name(c)
        store = next(s for s in sd.stores if name in set(s.cells["cell"]))
        p = store.dir / "kl" / f"{ref.replace('/', '__')}.npy"
        if ref not in arrays:
            if not p.is_file():
                out["missing_arrays"].append(str(p))
                continue
            arrays[ref] = np.load(p).astype(np.float64)
        R = arrays[ref]
        cs = np.cumsum(R, axis=1)
        mx = np.maximum.accumulate(R, axis=1)
        out["n_cells"] += 1
        for tag in ("0.1", "0"):
            t = sd.vector(name, f"t_star_{tag}").astype(np.int64)
            d = sd.vector(name, f"d_{tag}").astype(np.float64)
            ps = sd.vector(name, f"kl_prefix_sum_{tag}").astype(np.float64)
            nan_ok = np.isnan(d) == (t == 0)
            out["n_nan_mismatch"] += int((~nan_ok).sum())
            out["n_nan_checks"] += int((t == 0).sum())
            pos = np.flatnonzero(t > 0)
            if pos.size == 0:
                continue
            j = t[pos] - 1
            d_re = (ps[pos] - cs[pos, j]) / t[pos]
            # the float32 term bounds the loop's two sums through the sum of absolute differences, |S| plus the reference's summed prefix
            bound = (2.0 ** -11 * mx[pos, j] + 2.0 ** -24 * (math.log2(SEQ_LEN) + 1) * (np.abs(ps[pos]) + cs[pos, j]) / t[pos] + 2.0 ** -22 * np.abs(d[pos]) + 1e-6) * (1 + 2.0 ** -10)
            with np.errstate(invalid="ignore", divide="ignore"):
                ratio = np.abs(d[pos] - d_re) / bound
            finite = np.isfinite(ratio)
            out["n_checks"] += int(pos.size)
            out["n_nonfinite"] += int((~finite).sum())
            out["n_over"] += int(((~finite) | (ratio > 1)).sum())
            if finite.any():
                k = int(np.argmax(np.where(finite, ratio, -1)))
                if ratio[k] > out["max_ratio"]:
                    out["max_ratio"] = float(ratio[k])
                    out["max_ratio_at"] = {"cell": name, "seq": int(pos[k]), "tau_q": tag, "t_star": int(t[pos[k]])}
    out["pass"] = bool(out["n_over"] == 0 and out["n_nonfinite"] == 0 and out["n_nan_mismatch"] == 0 and not out["missing_arrays"])
    return out


# ----------------------------------------------------------------------------- the preconditions


def preconditions(grid: Grid, chains_by_set: dict[str, dict[tuple, Chain]], hard_zero_results: dict[str, Any], strata: dict[str, Any],
                  descriptive_chains: dict[str, dict[tuple, Chain]] | None = None) -> dict[str, Any]:
    p1, p2, p4 = [], [], []
    p4_desc: list[dict[str, Any]] = []
    for eval_set, sd in grid.sets.items():
        means = sd.rows.groupby("cell")["kl_mean"].mean()
        # the descriptive chains (rungs 2a, 2b and their control) are digest-checked like every other cell
        both = [(ch, False) for ch in chains_by_set[eval_set].values()] + [(ch, True) for ch in (descriptive_chains or {}).get(eval_set, {}).values()]
        for ch, is_desc in both:
            cells = [c for cs in ch.rungs.values() for c in cs]
            c0 = cells[0]
            refn = ref_cell_name(c0)
            if ch.family == "union" and ch.control == "none" and refn in means.index and not is_desc:
                for c8 in ch.rungs.get("8", []):
                    d = float(means[c8.name] - means[refn])
                    p1.append({"chain": ch.label, "rung_0": float(means[refn]), "rung_8": float(means[c8.name]), "difference": d, "pass": abs(d) > 0.01})
                    unm, imp = f"{c0.run}/{eval_set}/ref/{'unmasked' if c0.delta == 'excluded' else 'unmasked_delta'}", f"{c0.run}/{eval_set}/ref/importances"
                    p2.append({"chain": ch.label, "rung_8": float(means[c8.name]), "unmasked": float(means[unm]) if unm in means.index else None, "importances": float(means[imp]) if imp in means.index else None})
            # P4: digests equal iff sources equal (with the exception on equal switched mass), non-empty rungs distinct from rung 0, empty ones equal
            ct = sd.cells
            digests = {c.name: ct.loc[c.name, "mask_fp_cell"] for c in cells}
            srcs = {c.name: ct.loc[c.name, "source_sha256"] for c in cells}
            n_ons = {c.name: int(ct.loc[c.name, "n_on"]) for c in cells}
            ref_digest = ct.loc[refn, "mask_fp_cell"] if refn in ct.index else None
            defects = 0
            for i, a in enumerate(cells):
                for b in cells[i + 1 :]:
                    same_src, same_dig = srcs[a.name] == srcs[b.name], digests[a.name] == digests[b.name]
                    if same_dig != same_src:
                        sa, sb = sd.vector(a.name, "sigma"), sd.vector(b.name, "sigma")
                        if (not same_dig) or not np.array_equal(sa, sb, equal_nan=True):
                            defects += 1
            non_empty = [c.name for c in cells if n_ons[c.name] > 0]
            distinct = ref_digest is None or all(digests[n] != ref_digest for n in non_empty)
            empty_eq = ref_digest is None or all(digests[c.name] == ref_digest for c in cells if n_ons[c.name] == 0)
            (p4_desc if is_desc else p4).append({"chain": ch.label + (" (descriptive rungs)" if is_desc else ""), "n_cells": len(cells), "defects": defects, "non_empty_distinct_from_rung_0": bool(distinct), "empty_equal_rung_0": bool(empty_eq), "pass": bool(defects == 0 and distinct and empty_eq)})
    p3_perm, p3_bad, hz8 = 0, 0, {}
    for eval_set, sd in grid.sets.items():
        for name, c in sd.cell_objects.items():
            if c.eval_set == "donors":
                continue
            below = sd.cells.loc[name, "n_below_label_total"]
            if cell_permitted(c):
                p3_perm += 1
                p3_bad += int(pd.notna(below) and below > 0)
            if c.is_hard_zero and c.rung == "8":
                hz8[name] = int(below) if pd.notna(below) else 0
    p3 = {"permitted_cells": p3_perm, "permitted_cells_with_entries_below_label": p3_bad, "hard_zero_rung_8_counts": hz8, "pass": p3_bad == 0 and all(v > 0 for v in hz8.values())}
    p5 = {k: {"applies": True, "pass": v["positive_control"]["pass"], "n_rungs_judged": v["positive_control"]["n_rungs_judged"], "kind": v["positive_control"]["kind"], "control_not_run": v["positive_control"].get("control_not_run", False)}
          for k, v in hard_zero_results.items() if v.get("positive_control") and v["positive_control"].get("applies")}  # applies: the P5 line prints the word
    return {"P1": {"chains": p1, "n_pass": sum(x["pass"] for x in p1), "n": len(p1)}, "P2": p2, "P3": p3, "P4": {"chains": p4, "n_pass": sum(x["pass"] for x in p4), "n": len(p4),
                                                                                                                   "descriptive_chains": p4_desc, "n_pass_descriptive": sum(x["pass"] for x in p4_desc), "n_descriptive": len(p4_desc)}, "P5": p5}


# ----------------------------------------------------------------------------- the analysis


def assert_chain_completeness(grid: Grid, chains_by_set: dict[str, dict[tuple, Chain]], descriptive_by_set: dict[str, dict[tuple, Chain]]) -> dict[str, Any]:
    """Every non-reference, non-donor-side cell of every store lands in exactly one chain set: the rule chains (the
    descriptive families among them, which the rules skip by name), or the descriptive-rung chains; none missing, none
    twice (a silent drop like the NaN-as-descriptive one cannot pass again)."""
    out: dict[str, Any] = {}
    for key, sd in grid.sets.items():
        eligible = {n for n, c in sd.cell_objects.items() if c.family != "reference" and c.eval_set != "donors" and c.donor_side_reference is None}
        seen: dict[str, int] = {}
        kinds = {"rule": 0, "descriptive_family": 0, "descriptive_rung": 0}
        for ch in chains_by_set.get(key, {}).values():
            for cs in ch.rungs.values():
                for c in cs:
                    seen[c.name] = seen.get(c.name, 0) + 1
                    kinds["descriptive_family" if c.family in DESCRIPTIVE_FAMILIES else "rule"] += 1
        for ch in descriptive_by_set.get(key, {}).values():
            for cs in ch.rungs.values():
                for c in cs:
                    seen[c.name] = seen.get(c.name, 0) + 1
                    kinds["descriptive_rung"] += 1
        missing, extra, twice = sorted(eligible - set(seen)), sorted(set(seen) - eligible), sorted(n for n, k in seen.items() if k > 1)
        assert not missing and not extra and not twice, f"{key}: cells not in exactly one chain set: missing {missing[:5]} ({len(missing)}), not eligible {extra[:5]}, more than once {twice[:5]}"
        out[key] = {"n_cells": len(eligible), **kinds, "pass": True}
    return out


def _resample_for(grid: Grid, eval_set: str, mask: np.ndarray | None, replicates: int, master_seed: int, cache: dict) -> st.Resample:
    import hashlib

    key = (eval_set, None if mask is None else mask.tobytes())
    if key not in cache:
        n = grid.sets[eval_set].n_sequences if mask is None else int(mask.sum())
        # the stratum's seed from a content hash of its mask (not Python's per-process-salted hash)
        seed = (master_seed, "boot", eval_set) if mask is None else (master_seed, "boot", eval_set, hashlib.sha256(mask.tobytes()).hexdigest()[:16])
        cache[key] = st.Resample.make(n, replicates, seed)
    return cache[key]


def analyze_union_chains(grid: Grid, chains: dict[tuple, Chain], resamples: dict, replicates: int, master_seed: int, labels: dict[str, Any],
                         descriptive: dict[tuple, Chain] | None = None) -> dict[str, Any]:
    """Every union chain (the rule), the soft erases and the rounded-own-g union (descriptive, same machinery).
    `descriptive`: the chains of the descriptive rungs 2a and 2b, read with uncorrected intervals beside their
    chain's table, m untouched, and added to the paired union-minus-control line; never handed to the curve's rule."""
    out: dict[str, Any] = {}
    for key, ch in chains.items():
        if ch.family not in ("union", "soft_erase", "rounded_own_g", "code_specific_soft"):
            continue
        sd = grid.sets[ch.eval_set]
        rs = _resample_for(grid, ch.eval_set, None, replicates, master_seed, resamples)
        rung_e = {r: excess_matrix(sd, cs) for r, cs in ch.rungs.items()}
        res = st.union_curve(rung_e, "union", rs)
        for r in res["rungs"]:
            res["per_rung"][r]["n_on"] = float(np.mean([sd.cells.loc[c.name, "n_on"] for c in ch.rungs[r]]))
            res["per_rung"][r]["mean_sigma"] = float(np.nanmean(matrix(sd, ch.rungs[r], "sigma")))
            res["per_rung"][r]["mean_kl"] = float(matrix(sd, ch.rungs[r], "kl_mean").mean())
            res["per_rung"][r]["two_level_interval"] = st.two_level_interval(rung_e[r], rs, res["m"], (master_seed, "boot2", ch.eval_set, r))
        res["rung_0_mean"] = float(np.mean([sd.vector(ref_cell_name(c), "kl_mean").mean() for c in ch.rungs[res["rungs"][0]]]))
        res["descriptive_only"] = ch.family != "union"
        # curve 1 split by the reader labels on E, with intervals from each label's own resample
        if ch.family == "union" and ch.eval_set == "E" and ch.control == "none":
            if "E_reader" in labels:
                by_label = {}
                for lab, mask in labels["E_reader"]["groups"].items():
                    rs_g = _resample_for(grid, "E", mask, replicates, master_seed, resamples)
                    by_label[lab] = {r: {**{k: v for k, v in st.union_rung(rung_e[r][:, mask], rs_g, res["m"]).items() if k in ("e_hat", "interval", "half_width", "detected", "material")}, "n": int(mask.sum())} for r in res["rungs"]}
                res["by_reader_label"] = by_label
            else:
                res["by_reader_label"] = "reader labels not available"
        out[ch.label] = {"chain": ch, "result": res, "rung_excess": rung_e}
    # the paired union-minus-control differences at rungs 1 to 4 and 5a, and rungs 3 against 4
    for lab, entry in list(out.items()):
        ch = entry["chain"]
        if ch.family != "union" or ch.control != "none":
            continue
        ctl_key = tuple(list(ch.key[:-1]) + ["plain"])
        ctl = next((e for e in out.values() if e["chain"].key == ctl_key), None)
        rs = _resample_for(grid, ch.eval_set, None, replicates, master_seed, resamples)
        if ctl is None:
            entry["result"]["paired_vs_control"] = "control not yet run"
        else:
            entry["result"]["paired_vs_control"] = {r: st.paired_difference(entry["rung_excess"][r], ctl["rung_excess"][r], rs) for r in ("1", "2", "3", "4", "5a") if r in entry["rung_excess"] and r in ctl["rung_excess"]}
        if "3" in entry["rung_excess"] and "4" in entry["rung_excess"]:
            entry["result"]["rung_3_vs_4"] = st.paired_difference(entry["rung_excess"]["4"], entry["rung_excess"]["3"], rs)
        # the paired union-minus-control difference by reader label at rungs 1 to 4 and 5a, each label with its own
        # resample at the uncorrected level, the control's per-label excess (uncorrected) beside it
        if ctl is not None and ch.eval_set == "E" and "E_reader" in labels:
            by_label: dict[str, Any] = {}
            for lab_, mask in labels["E_reader"]["groups"].items():
                rs_g = _resample_for(grid, "E", mask, replicates, master_seed, resamples)
                by_label[lab_] = {}
                for r in ("1", "2", "3", "4", "5a"):
                    if r in entry["rung_excess"] and r in ctl["rung_excess"] and entry["rung_excess"][r].shape == ctl["rung_excess"][r].shape:
                        cu = st.union_rung(ctl["rung_excess"][r][:, mask], rs_g, 1)
                        by_label[lab_][r] = {**st.paired_difference(entry["rung_excess"][r][:, mask], ctl["rung_excess"][r][:, mask], rs_g), "n": int(mask.sum()),
                                             "control_excess": cu["e_hat"], "control_interval": cu["interval"], "control_half_width": cu["half_width"]}
            entry["result"]["paired_vs_control_by_reader_label"] = by_label
    # the descriptive rungs 2a and 2b beside their chain, uncorrected (m = 1), the paired line extended, and
    # curve 1's crossing of X as the bracket between the last position rung below X and the first above with the log-linear
    # interpolated point inside it and the per-draw crossings beside, never as a single number
    for dch in (descriptive or {}).values():
        entry = out.get(dch.label)
        if entry is None or dch.family != "union":
            continue
        sd = grid.sets[dch.eval_set]
        rs = _resample_for(grid, dch.eval_set, None, replicates, master_seed, resamples)
        drungs: dict[str, Any] = {}
        entry["descriptive_excess"] = {}
        for r in st.sort_rungs(list(dch.rungs)):
            cs = dch.rungs[r]
            em = excess_matrix(sd, cs)
            entry["descriptive_excess"][r] = em
            u = st.union_rung(em, rs, 1)
            drungs[r] = {"e_hat": u["e_hat"], "interval": u["interval"], "half_width": u["half_width"], "per_draw": u["per_draw"], "n_draws": u["n_draws"], "n_draws_positive": u["n_draws_positive"],
                         "fraction_sequences_above_X": u["fraction_sequences_above_X"], "n_on": float(np.mean([sd.cells.loc[c.name, "n_on"] for c in cs])), "n_on_per_draw": [int(sd.cells.loc[c.name, "n_on"]) for c in cs],
                         "mean_sigma": float(np.nanmean(matrix(sd, cs, "sigma"))), "mean_kl": float(matrix(sd, cs, "kl_mean").mean())}
        entry["result"]["descriptive_rungs"] = drungs
    for lab, entry in out.items():
        ch = entry["chain"]
        if ch.family != "union" or ch.control != "none" or "descriptive_rungs" not in entry["result"]:
            continue
        ctl = next((e for e in out.values() if e["chain"].key == tuple(list(ch.key[:-1]) + ["plain"])), None)
        pv = entry["result"].get("paired_vs_control")
        if ctl is not None and isinstance(pv, dict) and "descriptive_excess" in ctl:
            rs = _resample_for(grid, ch.eval_set, None, replicates, master_seed, resamples)
            for r, em in entry["descriptive_excess"].items():
                if r in ctl["descriptive_excess"] and ctl["descriptive_excess"][r].shape == em.shape:
                    pv[r] = st.paired_difference(em, ctl["descriptive_excess"][r], rs)
            entry["result"]["paired_vs_control"] = {r: pv[r] for r in st.sort_rungs(list(pv))}
        # the crossing of X along the position run (rungs 1, 2, 2a, 2b, 3): per curve and per draw
        res = entry["result"]
        pos = [r for r in st.sort_rungs(list(res["per_rung"]) + list(res["descriptive_rungs"])) if st.donor_count_order(r)[0] == 0]
        e_of = {r: (res["per_rung"][r]["e_hat"] if r in res["per_rung"] else res["descriptive_rungs"][r]["e_hat"]) for r in pos}
        n_of = {r: (res["per_rung"][r]["n_on"] if r in res["per_rung"] else res["descriptive_rungs"][r]["n_on"]) for r in pos}
        per_draw_e = {r: (res["per_rung"][r]["per_draw"] if r in res["per_rung"] else res["descriptive_rungs"][r]["per_draw"]) for r in pos}
        per_draw_n = {r: [int(grid.sets[ch.eval_set].cells.loc[c.name, "n_on"]) for c in ch.rungs.get(r, [])] for r in pos}
        for dch in (descriptive or {}).values():
            if dch.label == lab:
                for r in dch.rungs:
                    per_draw_n[r] = [int(grid.sets[ch.eval_set].cells.loc[c.name, "n_on"]) for c in dch.rungs[r]]
        res["x_crossing"] = _x_crossing(pos, e_of, n_of, per_draw_e, per_draw_n)
    return out


def _bracket(rungs: list[str], e: dict[str, float], n: dict[str, float], x: float) -> dict[str, Any]:
    """The first pair of consecutive rungs with e below x then at or above it, and the log-linear interpolated n at x."""
    for a, b in zip(rungs, rungs[1:]):
        if e[a] < x <= e[b] and n[a] > 0 and n[b] > 0 and e[b] > e[a]:
            f = (x - e[a]) / (e[b] - e[a])
            return {"bracket": [a, b], "n_low": n[a], "n_high": n[b], "e_low": e[a], "e_high": e[b], "interpolated_n": float(np.exp(np.log(n[a]) + f * (np.log(n[b]) - np.log(n[a]))))}
    if not rungs:
        return {"bracket": None, "note": "no position rungs"}
    if e[rungs[0]] >= x:
        return {"bracket": None, "note": f"at or above X from rung {rungs[0]} (n_on {n[rungs[0]]:.0f}, excess {e[rungs[0]]:+.4f}) on"}
    if all(e[r] < x for r in rungs):
        return {"bracket": None, "note": f"below X through rung {rungs[-1]} (n_on {n[rungs[-1]]:.0f}, excess {e[rungs[-1]]:+.4f})"}
    return {"bracket": None, "note": "no monotone crossing of X within the position run"}


def _x_crossing(pos: list[str], e_of: dict[str, float], n_of: dict[str, float], per_draw_e: dict[str, list[float]], per_draw_n: dict[str, list[int]], x: float = st.X_MATERIAL) -> dict[str, Any]:
    out: dict[str, Any] = {"x": x, "position_rungs": pos, "e_hat": {r: e_of[r] for r in pos}, "n_on": {r: n_of[r] for r in pos}, **_bracket(pos, e_of, n_of, x), "per_draw": []}
    K = min((len(per_draw_e[r]) for r in pos), default=0)
    for k in range(K):
        ek = {r: float(per_draw_e[r][k]) for r in pos}
        nk = {r: float(per_draw_n[r][k]) if len(per_draw_n.get(r, [])) > k else n_of[r] for r in pos}
        out["per_draw"].append({"draw": k, **_bracket(pos, ek, nk, x)})
    return out


def analyze_hard_zero_chains(grid: Grid, chains: dict[tuple, Chain], strata: dict[str, Any], pre: PreReads | None, resamples: dict, replicates: int, master_seed: int) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for key, ch in chains.items():
        if ch.family not in HARD_ZERO_FAMILIES or ch.family in DESCRIPTIVE_FAMILIES:
            continue
        sd = grid.sets[ch.eval_set]
        entry: dict[str, Any] = {"chain": ch, "by_tau_q": {}, "unconditional": {}}
        # strata: E_lab's pre-registered strata, E whole; the sub-rung chain and the donor chain are separate
        groups = {"all": np.ones(sd.n_sequences, bool)}
        if ch.eval_set == "E_lab" and "E_lab" in strata:
            groups = dict(strata["E_lab"]["groups"])
        donor_rungs = {r: cs for r, cs in ch.rungs.items() if r not in SUB_RUNGS}
        sub_rungs = {r: cs for r, cs in ch.rungs.items() if r in SUB_RUNGS}
        for tag in ("0.1", "0"):
            entry["by_tau_q"][tag] = {}
            for gname, mask in groups.items():
                rs = _resample_for(grid, ch.eval_set, None if gname == "all" else mask, replicates, master_seed, resamples)
                per_group: dict[str, Any] = {}
                for part, rungs in (("donor_chain", donor_rungs), ("sub_rung_chain", sub_rungs)):
                    if not rungs or not st.compared_rungs(list(rungs), ch.family):
                        continue  # a chain of rung 8 alone (the never-named family's Delta-excluded and strict cells) is read under the one-cell rule below
                    rung_d = {r: matrix(sd, cs, f"d_{tag}")[:, mask] for r, cs in rungs.items()}
                    rung_t = {r: matrix(sd, cs, f"t_star_{tag}")[:, mask] for r, cs in rungs.items()}
                    res = st.hard_zero_chain(rung_d, rung_t, ch.family, rs)
                    for r in res["rungs"]:
                        res["per_rung"][r]["n_off"] = float(np.mean([sd.cells.loc[c.name, "n_on"] for c in rungs[r]]))
                    per_group[part] = res
                entry["by_tau_q"][tag][gname] = per_group
        # every rung-8 cell of the never-named family under the one-cell rule: testability, d_hat, interval, label at
        # both tau_q, m = 1, the sign condition dropped, not counted in the donor chain's m
        if ch.family == "never_named_hard" and "8" in ch.rungs:
            rs = _resample_for(grid, ch.eval_set, None, replicates, master_seed, resamples)
            one: dict[str, Any] = {"n_erased": float(np.mean([sd.cells.loc[c.name, "n_on"] for c in ch.rungs["8"]]))}
            for tag in ("0.1", "0"):
                d, t = matrix(sd, ch.rungs["8"], f"d_{tag}"), matrix(sd, ch.rungs["8"], f"t_star_{tag}")
                read = st.readability(t)
                res = st.hard_zero_rung(d, t, rs, 1, one_cell=True) if read["floor_met"] else None
                one[tag] = {"readability": read, "testable": read["floor_met"], "result": res, "label": res["label"] if res else "not testable with these donors"}
            one["unconditional"] = float(excess_matrix(sd, ch.rungs["8"]).mean())
            entry["one_cell_rung_8"] = one
        # the unconditional damage per rung and group (the naive edit's cost) and the positive control
        for gname, mask in groups.items():
            entry["unconditional"][gname] = {r: float(excess_matrix(sd, cs)[:, mask].mean()) for r, cs in ch.rungs.items()}
        entry["positive_control"] = {"applies": False}
        if ch.control == "none" and ch.tau in (0.1, 0.5) and ch.delta == "included" and ch.family != "never_named_hard":  # tau = 0.5: the code-specific chain at that tau, read with its own positive control
            if ch.eval_set == "E_lab" and "E_lab" in strata:
                ctl_name = "complement" if ch.family == "code_specific_hard" else "plain"
                ctl = next((c2 for c2 in chains.values() if c2.key == tuple(list(ch.key[:-1]) + [ctl_name])), None)
                gh = strata["E_lab"]["groups"][strata["E_lab"]["positive"]]
                if ctl is not None:
                    er = {r: excess_matrix(sd, cs)[:, gh] for r, cs in ch.rungs.items()}
                    co = {r: excess_matrix(sd, cs)[:, gh] for r, cs in ctl.rungs.items()}
                    entry["positive_control"] = {"applies": True, "kind": f"erase exceeds its {ctl_name} control on {strata['E_lab']['positive']}", **st.positive_control_paired(er, co, ch.rung_order())}
                else:
                    entry["positive_control"] = {"applies": True, "kind": f"erase exceeds its {ctl_name} control on {strata['E_lab']['positive']}", "pass": None, "n_rungs_judged": 0, "control_not_run": True}  # recorded deviation: not judged, not failed
            elif ch.eval_set == "E" and ch.pool == "D_unif":
                dmg = {r: excess_matrix(sd, cs) for r, cs in ch.rungs.items()}
                entry["positive_control"] = {"applies": True, "kind": "unconditional damage on E material at rung 4 and beyond", **st.positive_control_material(dmg, ch.rung_order())}
        # the floor against the pre-reads' testability table (judged once; must agree); every (tau_q, stratum, rung) checked must
        # match exactly one row of the table, else the assert would be vacuous
        if pre is not None:
            t = pre.testability
            mism, n_checked, n_matched = [], 0, 0
            for tag in ("0.1", "0"):
                for gname in groups:
                    for part, res in entry["by_tau_q"][tag][gname].items():
                        for r in res["rungs"]:
                            n_checked += 1
                            rows_ = t[(t.chain == ch.label.replace(f"/k{ch.draw_if_uniform}", "")) & (t.rung == r) & (t.tau_q == f"tau_q{float(tag):g}") & (t.stratum == gname)]
                            if len(rows_) == 1:
                                n_matched += 1
                                if bool(rows_.iloc[0]["floor_met"]) != res["per_rung"][r]["testable"]:
                                    mism.append((tag, gname, part, r))
            entry["floor_matches_pre_reads"] = not mism and n_matched == n_checked
            entry["floor_rows_checked"], entry["floor_rows_matched"] = n_checked, n_matched
            assert n_matched == n_checked, f"{ch.label}: {n_matched} of {n_checked} (tau_q, stratum, rung) combinations found in the pre-reads' testability table"
            assert not mism, f"{ch.label}: the readability floor judged on the tables differs from the pre-reads' at {mism[:5]}"
        out[ch.label] = entry
    return out


def analyze_descriptives(grid: Grid, union_res: dict[str, Any], hz_res: dict[str, Any], chains_by_set: dict[str, dict[tuple, Chain]], pre: PreReads | None, resamples: dict, replicates: int, master_seed: int,
                         strata: dict[str, Any] | None = None) -> dict[str, Any]:
    strata = strata or {}
    out: dict[str, Any] = {}
    # mass-matched deciles and the slope, per union configuration (curves 1 and 2) with the control binned by the same edges
    deciles = {}
    for lab, entry in union_res.items():
        ch = entry["chain"]
        if ch.family != "union" or ch.control != "none" or ch.eval_set != "E":
            continue
        sd = grid.sets["E"]
        rs = _resample_for(grid, "E", None, replicates, master_seed, resamples)
        pooled_rungs = [r for r in entry["result"]["rungs"] if r != "8"]

        def points(e: dict[str, Any]) -> dict[str, np.ndarray]:
            ex, sg, sq = [], [], []
            for r in pooled_rungs:
                if r not in e["rung_excess"]:
                    continue
                em = e["rung_excess"][r]
                sm = matrix(sd, e["chain"].rungs[r], "sigma")
                K, N = em.shape
                ex.append(em.ravel()); sg.append(sm.ravel()); sq.append(np.tile(np.arange(N), K))
            return {"excess": np.concatenate(ex), "sigma": np.concatenate(sg), "seq": np.concatenate(sq)}

        pu = points(entry)
        edges = st.decile_edges(pu["sigma"]) if ch.background == "uniform" or pre is None else np.asarray(pre.summary["item7_switched_mass"]["union_tau0.1_r0_pooled"]["deciles_0_to_100"]) if (ch.tau == 0.1 and ch.background == "r0") else st.decile_edges(pu["sigma"])
        ctl = next((e for e in union_res.values() if e["chain"].key == tuple(list(ch.key[:-1]) + ["plain"])), None)
        item: dict[str, Any] = {"edges": edges.tolist(), "edges_source": "pre-reads" if (ch.tau == 0.1 and ch.background == "r0" and pre is not None) else "the loop's sigma column", "n_points_union": int(pu["excess"].size)}
        rung_mean_e = {r: entry["result"]["per_rung"][r]["e_hat"] for r in pooled_rungs}
        rung_mean_s = {r: entry["result"]["per_rung"][r]["mean_sigma"] for r in pooled_rungs}
        item["slope_union"] = st.ols_slope(pu["sigma"], pu["excess"], pu["seq"], rs)
        bu = st.assign_bins(pu["sigma"], edges)  # the union's own decile means, drawn by fig3 with or without the control (recorded deviation)
        item["union_bins"] = [{"bin": b, "edge_low": float(edges[b]) if b < 10 else float(edges[10]), "edge_high": float(edges[b + 1]) if b < 10 else float("inf"), "n_sequences": int(np.unique(pu["seq"][bu == b]).size),
                               "mean_excess": float(pu["excess"][bu == b].mean()) if np.unique(pu["seq"][bu == b]).size >= 64 else float("nan")} for b in range(11)]
        item["difference_quotients_union"] = st.difference_quotients(rung_mean_e, rung_mean_s, pooled_rungs)
        if ctl is not None:
            pc = points(ctl)
            item["bins"] = st.binned_difference(pu, pc, edges, rs)
            item["slope_control"] = st.ols_slope(pc["sigma"], pc["excess"], pc["seq"], rs)
        else:
            item["bins"] = "control not yet run"
        deciles[lab] = item
    out["deciles"] = deciles
    # the donor-side pass: every donor-side store is its own set
    donor = {}
    for sd in grid.sets.values():
        if sd.eval_set != "donors":
            continue
        for name, c in sd.cell_objects.items():
            if c.donor_side_reference is None:
                rounded = f"{name}/donorref-rounded"
                imp = f"{name}/donorref-importances"
                if rounded in sd.cell_objects:
                    donor[name] = {"excess_over_rounded": st.mean_se(sd.vector(name, "kl_mean").astype(np.float64) - sd.vector(rounded, "kl_mean").astype(np.float64)),
                                   "excess_over_importances": st.mean_se(sd.vector(name, "kl_mean").astype(np.float64) - sd.vector(imp, "kl_mean").astype(np.float64)) if imp in sd.cell_objects else None}
    out["donor_side"] = donor
    # E8 (hard-zero at least soft-erase damage on the same sequences), the Delta gaps, the two-by-two, the never-named chain
    e8 = []
    soft_of = {"hard_zero": "soft_erase", "code_specific_hard": "code_specific_soft"}  # E8 completed with the code-specific pair
    for lab, hz in hz_res.items():
        ch = hz["chain"]
        if ch.family not in soft_of:
            continue
        candidates = [e for e in union_res.values() if e["chain"].family == soft_of[ch.family] and e["chain"].eval_set == ch.eval_set and e["chain"].pool == ch.pool and e["chain"].tau == ch.tau and e["chain"].background == "r1" and e["chain"].control == ch.control]
        # recorded deviation: the same Delta setting when present, else the other, each family's excess over its own rung 0
        soft = next((e for e in candidates if e["chain"].delta == ch.delta), None) or (candidates[0] if candidates else None)
        if soft is None:
            continue
        sd = grid.sets[ch.eval_set]
        for r, cs in ch.rungs.items():
            if r in soft["chain"].rungs and len(soft["chain"].rungs[r]) == len(cs):
                hzd = excess_matrix(sd, cs)
                sfd = soft["rung_excess"][r]
                e8.append({"chain": lab, "rung": r, "soft_erase_chain": soft["chain"].label, "delta_settings": "same" if soft["chain"].delta == ch.delta else "differ (each excess over its own rung 0)",
                           "fraction_sequences_hard_zero_at_least_soft": float((hzd >= sfd).mean()), "mean_hard_zero": float(hzd.mean()), "mean_soft": float(sfd.mean())})
    out["E8"] = e8
    gaps = []
    for eval_set, chains in chains_by_set.items():
        sd = grid.sets[eval_set]
        for ch in chains.values():
            if ch.delta != "excluded":
                continue
            twin = next((c2 for c2 in chains.values() if c2.key[:6] == ch.key[:6] and c2.delta == "included" and c2.key[7:] == ch.key[7:]), None)
            if twin is None:
                continue
            for r in ch.rung_order():
                if r in twin.rungs and len(twin.rungs[r]) == len(ch.rungs[r]):
                    gaps.append({"chain": ch.label, "rung": r, "delta_gap_mean": float((matrix(sd, twin.rungs[r], "kl_mean") - matrix(sd, ch.rungs[r], "kl_mean")).mean())})
    out["delta_gaps"] = gaps
    # the two-by-two on E: unmasked, importances, the fourth cell (and its twin), curve 1's rung 8, curve 2's rung 8 per draw
    if "E" in grid.sets:
        sd = grid.sets["E"]
        run = grid.run
        two = {}
        for label, name in (("unmasked", f"{run}/E/ref/unmasked"), ("importances", f"{run}/E/ref/importances"), ("fourth_cell", f"{run}/E/soft_erase/D_unif/tau0.1/r1/excl/k0/r8"),
                            ("fourth_cell_delta_included", f"{run}/E/soft_erase/D_unif/tau0.1/r1/incl/k0/r8"), ("curve_1_rung_8", f"{run}/E/union/D_unif/tau0.1/r0/excl/k0/r8")):
            if name in sd.cell_objects:
                two[label] = st.mean_se(sd.vector(name, "kl_mean"))
                if label.startswith("fourth_cell"):  # the paired differences with standard errors, as the verification run printed them
                    f = sd.vector(name, "kl_mean").astype(np.float64)
                    two[label]["paired_minus_importances"] = st.mean_se(f - sd.vector(f"{run}/E/ref/importances", "kl_mean").astype(np.float64))
                    two[label]["paired_minus_unmasked"] = st.mean_se(f - sd.vector(f"{run}/E/ref/unmasked", "kl_mean").astype(np.float64))
        c2 = [f"{run}/E/union/D_unif/tau0.1/uniform/excl/k{k}/r8" for k in range(8)]
        c2 = [n for n in c2 if n in sd.cell_objects]
        if c2:
            two["curve_2_rung_8"] = st.mean_se(np.concatenate([sd.vector(n, "kl_mean") for n in c2]))
            two["curve_2_rung_8_per_draw"] = [float(sd.vector(n, "kl_mean").mean()) for n in c2]
            two["stochastic_rung_0_per_draw"] = [float(sd.vector(f"{run}/E/ref/stochastic/k{k}", "kl_mean").mean()) for k in range(len(c2)) if f"{run}/E/ref/stochastic/k{k}" in sd.cell_objects]
        out["two_by_two"] = two
        # the never-named chain: D(n) against n, the prediction lines, the draw spread, the ratio to the alive control
        nn = {lab: hz for lab, hz in hz_res.items() if hz["chain"].family == "never_named_hard" and hz["chain"].delta == "included" and hz["chain"].tau == 0.1}
        if nn:
            lab, hz = next(iter(nn.items()))
            ch = hz["chain"]
            whole = f"{run}/E/never_named_hard/D_unif/tau0.1/ones/incl/k0/r8"
            D8 = float(excess_matrix(sd, sd.cell_objects[whole] and [sd.cell_objects[whole]]).mean()) if whole in sd.cell_objects else float("nan")
            n_whole = int(sd.cells.loc[whole, "n_on"]) if whole in sd.cell_objects else 0
            ctl_chain = next((c2 for c2 in chains_by_set["E"].values() if c2.family == "hard_zero" and c2.pool == "D_unif" and c2.tau == 0.1 and c2.delta == "included" and c2.control == "plain"), None)
            rows_ = []
            for r in ch.rung_order():
                cs = ch.rungs[r]
                em = excess_matrix(sd, cs)
                n = float(np.mean([sd.cells.loc[c.name, "n_on"] for c in cs]))
                row = {"rung": r, "n_erased": n, "n_per_draw": [int(sd.cells.loc[c.name, "n_on"]) for c in cs], "D_mean": float(em.mean()), "D_per_draw": em.mean(axis=1).tolist(),  # n per draw
                       "draw_spread_sd": float(em.mean(axis=1).std(ddof=1)) if em.shape[0] > 1 else float("nan"), "linear_prediction": 1.29 * n / 28946, "quadratic_prediction": 1.29 * (n / 28946) ** 2}
                if ctl_chain is not None and r in ctl_chain.rungs and len(ctl_chain.rungs[r]) == len(cs):
                    cm = excess_matrix(sd, ctl_chain.rungs[r])
                    row["alive_control_mean"] = float(cm.mean())
                    row["ratio_to_alive_control"] = float(em.mean() / cm.mean()) if cm.mean() else float("nan")
                rows_.append(row)
            strict = f"{run}/E/never_named_hard/D_unif/tau0/ones/incl/k0/r8"
            out["never_named"] = {"chain": lab, "rungs": rows_, "whole_set": {"n": n_whole, "D": D8}, "strict": st.mean_se(sd.vector(strict, "kl_mean").astype(np.float64) - sd.vector(f"{run}/E/ref/unmasked_delta", "kl_mean").astype(np.float64)) if strict in sd.cell_objects else None,
                                  "control_present": ctl_chain is not None}
        # ---- the level cells beside their four corners, with the soft-erase curve's points at their own switched fraction
        out["level"] = _level_table(grid, union_res, resamples, replicates, master_seed)
        # ---- the ranked never-named pair: D(n) against n beside the random chain's, top minus bottom paired per key
        out["ranked"] = _ranked_table(grid, chains_by_set, out.get("never_named"), pre, resamples, replicates, master_seed)
        # ---- the tau = 0 union: the control's dead-set overflow per rung, and the reference lines (the strict cell, the never-named rung 8)
        out["tau0_union"] = _tau0_union_extras(grid, union_res, pre)
    # ---- the erased set against its control per rung, from the pre-reads' control_overlap.csv, for every hard-zero chain with a control
    out["control_overlap"] = _control_overlap_by_rung(hz_res, pre)
    # the domain comparisons on E_lab: (1) and (2) the erase against its own control per stratum, paired
    # on the sequence with the stratum's resample and an interval; (3) within other at rung 7, StackExchange and ArXiv against
    # Pile-CC and Wikipedia, unpaired with two resamples; the conditional damage beside where sequences contribute
    dom, dom3 = [], []
    if "E_lab" in grid.sets and "E_lab" in strata:
        sd = grid.sets["E_lab"]
        groups = strata["E_lab"]["groups"]
        labels = np.asarray(strata["E_lab"]["labels"])
        for hz in hz_res.values():
            ch = hz["chain"]
            if ch.eval_set != "E_lab" or ch.control != "none":
                continue
            ctl_name = "complement" if ch.family == "code_specific_hard" else "plain"
            ctl = next((c2 for c2 in chains_by_set["E_lab"].values() if c2.key == tuple(list(ch.key[:-1]) + [ctl_name])), None)
            for r in ch.rung_order():
                er = excess_matrix(sd, ch.rungs[r])
                co = excess_matrix(sd, ctl.rungs[r]) if (ctl is not None and r in ctl.rungs and len(ctl.rungs[r]) == len(ch.rungs[r])) else None
                d01 = matrix(sd, ch.rungs[r], "d_0.1")
                t01 = matrix(sd, ch.rungs[r], "t_star_0.1")
                for gname, mask in groups.items():
                    if gname == "all":
                        continue
                    row: dict[str, Any] = {"chain": ch.label, "rung": r, "stratum": gname, "n": int(mask.sum()), "erase_unconditional": float(er[:, mask].mean())}
                    if co is not None:
                        rs_g = _resample_for(grid, "E_lab", mask, replicates, master_seed, resamples)
                        pdiff = st.paired_difference(er[:, mask], co[:, mask], rs_g)
                        row.update({"control_unconditional": float(co[:, mask].mean()), "paired_erase_minus_control": pdiff["mean"], "interval": _interval(pdiff["interval"])})
                    else:
                        row["paired_erase_minus_control"] = "control not yet run"
                    contrib = (t01[:, mask] >= st.CONTRIBUTING_MIN_T_STAR) & np.isfinite(d01[:, mask])
                    row["conditional_d_0.1"] = float(np.nanmean([d01[:, mask][k, contrib[k]].mean() for k in range(d01.shape[0]) if contrib[k].any()])) if contrib.any() else float("nan")
                    row["n_contributing_mean"] = float(contrib.sum(axis=1).mean())
                    dom.append(row)
            # comparison 3 at rung 7 (the paper's sources; not available on the stand-in)
            a_mask, b_mask = np.isin(labels, ["StackExchange", "ArXiv"]), np.isin(labels, ["Pile-CC", "Wikipedia (en)"])
            if "7" in ch.rungs and a_mask.any() and b_mask.any():
                er7 = excess_matrix(sd, ch.rungs["7"])
                ra, rb = _resample_for(grid, "E_lab", a_mask, replicates, master_seed, resamples), _resample_for(grid, "E_lab", b_mask, replicates, master_seed, resamples)
                ud = st.unpaired_difference(er7[:, a_mask], er7[:, b_mask], ra, rb)
                d7, t7 = matrix(sd, ch.rungs["7"], "d_0.1"), matrix(sd, ch.rungs["7"], "t_star_0.1")
                cond = {}
                for name, m in (("StackExchange+ArXiv", a_mask), ("Pile-CC+Wikipedia", b_mask)):
                    c = (t7[:, m] >= st.CONTRIBUTING_MIN_T_STAR) & np.isfinite(d7[:, m])
                    cond[name] = float(np.nanmean([d7[:, m][k, c[k]].mean() for k in range(d7.shape[0]) if c[k].any()])) if c.any() else float("nan")
                dom3.append({"chain": ch.label, "rung": "7", "n_a": int(a_mask.sum()), "n_b": int(b_mask.sum()), "unconditional_a_minus_b": ud["mean"], "interval": _interval(ud["interval"]),
                             "conditional_d_0.1_a": cond["StackExchange+ArXiv"], "conditional_d_0.1_b": cond["Pile-CC+Wikipedia"]})
    out["domain"] = dom
    out["domain_3"] = dom3 if dom3 else "not available (the paper's sources are not in these strata)"
    # curve 2's rung 8 against curve 1's per sequence, paired: the ratio's distribution
    if "E" in grid.sets and "two_by_two" in out:
        sd = grid.sets["E"]
        run = grid.run
        c1 = f"{run}/E/union/D_unif/tau0.1/r0/excl/k0/r8"
        c2 = [f"{run}/E/union/D_unif/tau0.1/uniform/excl/k{k}/r8" for k in range(8) if f"{run}/E/union/D_unif/tau0.1/uniform/excl/k{k}/r8" in sd.cell_objects]
        if c1 in sd.cell_objects and c2:
            k1 = sd.vector(c1, "kl_mean").astype(np.float64)
            k2 = np.mean([sd.vector(n, "kl_mean").astype(np.float64) for n in c2], axis=0)
            with np.errstate(divide="ignore", invalid="ignore"):
                ratio = np.where(k1 > 0, k2 / k1, np.nan)
            q = np.nanpercentile(ratio, [0, 10, 25, 50, 75, 90, 100])
            out["two_by_two"]["curve2_over_curve1_rung_8_per_sequence"] = {"n": int(np.isfinite(ratio).sum()), "quantiles_0_10_25_50_75_90_100": q.tolist(), "mean": float(np.nanmean(ratio)),
                                                                            "fraction_below_0.5": float(np.nanmean(ratio < 0.5)), "fraction_above_0.9": float(np.nanmean(ratio > 0.9))}
    return out


# ----------------------------------------------------------------------------- the descriptive tables of the sensitivity tier


LEVEL_S = (0.0, 0.25, 0.5, 0.75, 1.0)


def _level_cell_name(run: str, s: float, at: str) -> str:
    """The cell at level s with the never-named set at its labels (background r0) or at 1 (r1); the corners are existing cells."""
    if s == 0.0:
        return f"{run}/E/ref/importances" if at == "labels" else f"{run}/E/soft_erase/D_unif/tau0.1/r1/excl/k0/r8"
    if s == 1.0:
        return f"{run}/E/union/D_unif/tau0.1/r0/excl/k0/r8" if at == "labels" else f"{run}/E/ref/unmasked"
    return f"{run}/E/level/D_unif/tau0.1/{'r0' if at == 'labels' else 'r1'}/excl/k0/r8/s{s:g}"


def _level_table(grid: Grid, union_res: dict[str, Any], resamples: dict, replicates: int, master_seed: int) -> dict[str, Any] | None:
    sd = grid.sets["E"]
    run = grid.run
    names = {(s, at): _level_cell_name(run, s, at) for s in LEVEL_S for at in ("labels", "one")}
    if not any(n in sd.cell_objects for (s, at), n in names.items() if 0 < s < 1):
        return None
    rs = _resample_for(grid, "E", None, replicates, master_seed, resamples)
    ref = {"labels": f"{run}/E/ref/importances", "one": f"{run}/E/ref/unmasked"}
    rows = []
    for s in LEVEL_S:
        for at in ("labels", "one"):
            n = names[(s, at)]
            if n not in sd.cell_objects:
                continue
            kl = sd.vector(n, "kl_mean").astype(np.float64)
            sig = sd.vector(n, "sigma").astype(np.float64)
            row: dict[str, Any] = {"s": s, "never_named_at": at, "cell": n, "corner": s in (0.0, 1.0), "mean_kl": float(kl.mean()), "se": st.mean_se(kl)["se"], "mean_sigma": float(np.nanmean(sig)) if np.isfinite(sig).any() else float("nan"),
                                   "excess_over_path_rung_0": float((kl - sd.vector(ref[at], "kl_mean").astype(np.float64)).mean()), "path_rung_0": ref[at].split("/")[-1]}
            other = names[(s, "one" if at == "labels" else "labels")]
            if at == "labels" and other in sd.cell_objects:
                fp = st.paired_difference(kl[None, :], sd.vector(other, "kl_mean").astype(np.float64)[None, :], rs)
                row.update({"footprint_labels_minus_one": fp["mean"], "footprint_interval": fp["interval"]})
            rows.append(row)
    # the soft-erase curve (r1, tau 0.1, E) at its own switched fraction: rung j's sigma over rung 8's, placed at s = 1 - fraction on the at-1 path
    soft = union_res.get("soft_erase/E/D_unif/tau0.1/r1/excl/ctl-none")
    soft_pts = []
    if soft is not None and "8" in soft["result"]["per_rung"]:
        s8 = soft["result"]["per_rung"]["8"]["mean_sigma"]
        for r in soft["result"]["rungs"]:
            pr = soft["result"]["per_rung"][r]
            frac = pr["mean_sigma"] / s8 if s8 else float("nan")
            soft_pts.append({"rung": r, "switched_fraction": frac, "s_equivalent": 1.0 - frac, "mean_kl": pr["mean_kl"], "n_on": pr["n_on"]})
    return {"rows": rows, "soft_erase_points": soft_pts, "n_interior_cells": sum(1 for r in rows if not r["corner"])}


def _ranked_table(grid: Grid, chains_by_set: dict[str, dict[tuple, Chain]], never_named: dict[str, Any] | None, pre: PreReads | None, resamples: dict, replicates: int, master_seed: int) -> dict[str, Any] | None:
    sd = grid.sets["E"]
    ranked = {ch.label: ch for ch in chains_by_set.get("E", {}).values() if ch.family == "never_named_ranked"}
    if not ranked:
        return None
    rs = _resample_for(grid, "E", None, replicates, master_seed, resamples)
    rand = {r["rung"]: r for r in (never_named or {}).get("rungs", [])}
    rows, excess = [], {}
    for lab, ch in ranked.items():
        for r in ch.rung_order():
            cs = ch.rungs[r]
            em = excess_matrix(sd, cs)
            excess[(ch.rank_key, ch.rank_end, r)] = em
            n = float(np.mean([sd.cells.loc[c.name, "n_on"] for c in cs]))
            row = {"key": ch.rank_key, "end": ch.rank_end, "rung": r, "n_erased": n, "D_mean": float(em.mean()), "se": st.mean_se(em.mean(axis=0))["se"], "linear_prediction": 1.29 * n / 28946, "quadratic_prediction": 1.29 * (n / 28946) ** 2,
                   "random_chain_D_mean": rand.get(r, {}).get("D_mean", float("nan")), "random_chain_draw_spread_sd": rand.get(r, {}).get("draw_spread_sd", float("nan")), "random_chain_n_erased": rand.get(r, {}).get("n_erased", float("nan")),
                   # draw 0 beside the mean over draws: the ranked chains are sized to draw 0's counts, and the mean's sizes differ from rung 4 on
                   "random_chain_D_draw_0": (rand[r]["D_per_draw"][0] if r in rand and rand[r].get("D_per_draw") else float("nan")), "random_chain_n_draw_0": (rand[r]["n_per_draw"][0] if r in rand and rand[r].get("n_per_draw") else float("nan"))}
            rows.append(row)
    diffs = []
    for key in ("weight_norm", "positive_count"):
        for r in st.sort_rungs(sorted({rr for (k, e, rr) in excess if k == key})):
            if (key, "top", r) in excess and (key, "bottom", r) in excess:
                pdiff = st.paired_difference(excess[(key, "top", r)], excess[(key, "bottom", r)], rs)
                diffs.append({"key": key, "rung": r, "n_erased": next(x["n_erased"] for x in rows if x["key"] == key and x["end"] == "top" and x["rung"] == r), "top_minus_bottom": pdiff["mean"], "interval": pdiff["interval"], "half_width": pdiff["half_width"]})
    whole = (never_named or {}).get("whole_set")
    corr = (pre.summary.get("item10_rank_keys") if pre is not None else None) or None
    return {"rows": rows, "top_minus_bottom": diffs, "whole_set": whole, "rank_correlation": corr}


def _tau0_union_extras(grid: Grid, union_res: dict[str, Any], pre: PreReads | None) -> dict[str, Any] | None:
    sd = grid.sets["E"]
    run = grid.run
    lab = "union/E/D_unif/tau0/r0/excl/ctl-none"
    if lab not in union_res:
        return None
    out: dict[str, Any] = {"chain": lab, "control_chain": lab.replace("ctl-none", "ctl-plain")}
    # the plain control's overflow into the dead set per rung (mean over draws of the summed per-module overflow), from the pre-reads
    ctl = union_res.get(out["control_chain"])
    overflow = None
    if ctl is not None and pre is not None and (pre.dir / "control_overflow.csv").is_file():
        ov = pd.read_csv(pre.dir / "control_overflow.csv", dtype={"rung": str})
        names = {c.name for cs in ctl["chain"].rungs.values() for c in cs}
        sel = ov[ov["cell"].isin(names)]
        per_cell = sel.groupby(["rung", "draw"])["overflow"].sum()
        overflow = {}
        for r in ctl["chain"].rung_order():
            vals = [float(per_cell.get((r, c.draw), 0.0)) for c in ctl["chain"].rungs[r]]
            overflow[r] = {"mean_overflow": float(np.mean(vals)), "per_draw": vals, "n_on": ctl["result"]["per_rung"][r]["n_on"] if r in ctl["result"]["per_rung"] else float("nan")}
    out["control_overflow_by_rung"] = overflow
    # the reference lines: rung 8 of this chain is the complement of the strict set, so the strict cell and the never-named rung 8 are its natural companions
    lines = []
    for name, what in ((f"{run}/E/never_named_hard/D_unif/tau0/ones/incl/k0/r8", "strict cell: the strict set (g = 0 at every pool position) erased, Delta included"),
                       (f"{run}/E/never_named_hard/D_unif/tau0.1/ones/incl/k0/r8", "never-named rung 8: the never-named set at tau = 0.1 erased, Delta included"),
                       (f"{run}/E/never_named_hard/D_unif/tau0.1/ones/excl/k0/r8", "never-named rung 8, Delta excluded"),
                       (f"{run}/E/union/D_unif/tau0/r0/excl/k0/r8", "this chain's rung 8: everything the pool labels above 0 pinned at 1, the strict set at its labels, Delta excluded"),
                       (f"{run}/E/ref/unmasked", "unmasked"), (f"{run}/E/ref/unmasked_delta", "unmasked, Delta included"), (f"{run}/E/ref/importances", "importances-as-masks (this chain's rung 0)")):
        if name in sd.cell_objects:
            kl = sd.vector(name, "kl_mean").astype(np.float64)
            lines.append({"line": what, "cell": name, "n_on": int(sd.cells.loc[name, "n_on"]), "mean_kl": float(kl.mean()), "se": st.mean_se(kl)["se"],
                          "excess_over_unmasked": float((kl - sd.vector(f"{run}/E/ref/unmasked", "kl_mean").astype(np.float64)).mean()) if f"{run}/E/ref/unmasked" in sd.cell_objects else float("nan")})
    out["reference_lines"] = lines
    return out


def _control_overlap_by_rung(hz_res: dict[str, Any], pre: PreReads | None) -> dict[str, Any] | None:
    if pre is None or not (pre.dir / "control_overlap.csv").is_file():
        return None
    ov = pd.read_csv(pre.dir / "control_overlap.csv", dtype={"rung": str})
    out: dict[str, Any] = {}
    for lab, hz in hz_res.items():
        ch = hz["chain"]
        if ch.control != "none":
            continue
        ctl_name = "complement" if ch.family == "code_specific_hard" else "plain"
        sel = ov[(ov["family"] == ch.family) & (ov["eval_set"] == ch.eval_set) & (ov["pool"] == ch.pool) & (ov["tau"] == ch.tau) & (ov["delta"] == ch.delta) & (ov["control"] == ctl_name)]
        if not len(sel):
            continue
        rows = []
        for r in ch.rung_order():
            g = sel[sel["rung"] == r]
            if not len(g):
                continue
            rows.append({"rung": r, "n_draws": int(len(g)), "n_named": float(g["n_named"].mean()), "n_control": float(g["n_control"].mean()), "overlap": float(g["overlap"].mean()), "fraction_of_named": float(g["fraction_of_named"].mean()),
                         "control_pool_size": int(g["control_pool_size"].iloc[0]), "named_in_control_pool": float(g["named_in_control_pool"].mean()), "control_overflow": float(g["control_overflow"].mean())})
        out[lab] = {"control": ctl_name, "rows": rows}
    return out


# ----------------------------------------------------------------------------- E1 to E9


def sanity_checks(grid: Grid, union_res: dict[str, Any], hz_res: dict[str, Any], chains_by_set: dict[str, dict[tuple, Chain]]) -> list[dict[str, Any]]:
    checks = []
    run = grid.run
    if "E" in grid.sets:
        sd = grid.sets["E"]
        c1 = union_res.get(f"union/E/D_unif/tau0.1/r0/excl/ctl-none")
        if c1:
            r = c1["result"]
            imp = float(sd.vector(f"{run}/E/ref/importances", "kl_mean").mean())
            unm = float(sd.vector(f"{run}/E/ref/unmasked", "kl_mean").mean())
            checks.append({"id": "E1", "pass": abs(r["rung_0_mean"] - imp) < 1e-6, "note": f"rung 0 equals importances-as-masks ({abs(r['rung_0_mean'] - imp):.1e}); rung 8 {r['per_rung']['8']['mean_kl']:.4f} against unmasked {unm:.4f} and the start {imp:.4f}: "
                           + ("below the start" if r["per_rung"]["8"]["mean_kl"] < imp else "above the start (the rule's own rung-8 comparison, not a bug)")})
        # E2 / E4: coverage monotone within each nested run (n_on non-decreasing)
        mono_bad = []
        for lab, e in union_res.items():
            ch = e["chain"]
            if ch.family != "union":
                continue
            for run_ in st.nested_runs(e["result"]["rungs"]):
                ns = [e["result"]["per_rung"][r]["n_on"] for r in run_]
                if any(b < a for a, b in zip(ns, ns[1:])):
                    mono_bad.append((lab, run_))
        checks.append({"id": "E2/E4", "pass": not mono_bad, "note": f"n_on non-decreasing within every nested run of every union chain; violations {mono_bad[:3] or 'none'}"})
        soft = union_res.get("soft_erase/E/D_unif/tau0.1/r1/excl/ctl-none")
        if soft:
            r = soft["result"]
            checks.append({"id": "E3", "pass": abs(r["rung_0_mean"] - float(sd.vector(f"{run}/E/ref/unmasked", "kl_mean").mean())) < 1e-6, "note": f"soft-erase rung 0 equals unmasked; rung 8 {r['per_rung']['8']['mean_kl']:.4f} against importances-as-masks {float(sd.vector(f'{run}/E/ref/importances', 'kl_mean').mean()):.4f}"})
    nan_cells = sum(int(sdd.rows["kl_mean"].isna().sum()) for sdd in grid.sets.values())
    checks.append({"id": "E6", "pass": nan_cells == 0, "note": f"no NaN kl_mean anywhere ({nan_cells} found); the sequence bootstrap widths are in the tables"})
    e9_bad, e9_skipped = [], []
    for lab, hz in hz_res.items():
        for tag in ("0.1", "0"):
            res = hz["by_tau_q"][tag].get("all", {}).get("donor_chain")
            if not res:
                continue
            for run_ in st.nested_runs(res["rungs"]):
                for a, b in zip(run_, run_[1:]):
                    pa, pb = res["per_rung"][a], res["per_rung"][b]
                    if pb["n_off"] < pa["n_off"]:  # the sets are nested only where the erased count does not fall (the stand-in's never-named shortfall breaks it; the paper's model cannot)
                        e9_skipped.append((lab, tag, a, b))
                        continue
                    if pb["readability"]["mean_clean_prefix_fraction"] > pa["readability"]["mean_clean_prefix_fraction"] + 1e-12:
                        e9_bad.append((lab, tag, a, b))
    checks.append({"id": "E9", "pass": not e9_bad, "note": f"clean-prefix fractions non-increasing within each nested run of every hard-zero chain at both tau_q; violations {e9_bad[:3] or 'none'}; "
                                                          f"pairs not nested by count (skipped) {len(e9_skipped)}{': ' + str(e9_skipped[:2]) if e9_skipped else ''}"})
    return checks


# ----------------------------------------------------------------------------- the control run against the main run

COMPARISON_CURVES = (("curve 1", "union/E/D_unif/tau0.1/r0/excl/ctl-none", "union"), ("curve 2 (draw 0)", "union/E/D_unif/tau0.1/uniform/excl/k0/ctl-none", "union"),
                     ("curve 3", "hard_zero/E_lab/D_code/tau0.1/ones/incl/ctl-none", "hz"), ("curve 4", "code_specific_hard/E_lab/D_code/tau0.1/ones/incl/ctl-none", "hz"))


def _union_points(sd: SetData, chain: Chain, rungs: list[str]) -> dict[str, np.ndarray]:
    ex, sg, sq = [], [], []
    for r in rungs:
        if r == "8" or r not in chain.rungs:
            continue
        em = excess_matrix(sd, chain.rungs[r])
        sm = matrix(sd, chain.rungs[r], "sigma")
        K, N = em.shape
        ex.append(em.ravel()); sg.append(sm.ravel()); sq.append(np.tile(np.arange(N), K))
    return {"excess": np.concatenate(ex), "sigma": np.concatenate(sg), "seq": np.concatenate(sq)}


def compare_with_other_run(grid: Grid, ctx: dict[str, Any], other_root: Path, *, frozen: str | None, tiers: tuple[int, ...] | None, other_pre_dir: Path | None,
                           resamples: dict, replicates: int, master_seed: int, log: Any = print) -> dict[str, Any]:
    """This run (the control) against the other run's tier stores (the main run's), loaded through load_grid with the same
    blindness gate; the set hashes must agree, since both runs score the same sequences. Rung by rung on curves 1 to 4 at
    the intersection of the two rung lists (each run keeps its own; the rungs one run alone has are listed), the paired
    per-sequence difference this minus other on the same sequence and draw with the shared sequence resample; and at
    matched switched mass, the other run's decile edges (curve 1's from its pre-reads, curve 2's from its loop sigma)
    applied to this run's union cells, per bin the two means and their difference with the shared resample."""
    from vpd_audit import analysis_s7

    other = load_grid(other_root, frozen=frozen)
    if tiers is not None:
        other = restrict_tiers(other, tuple(t for t in tiers if t != analysis_s7.TIER_4))
    elif analysis_s7.has_tier_4(other):  # the other run's tier 4 is no part of this comparison
        other = restrict_tiers(other, (1, 2, 3))
    out: dict[str, Any] = {"other_root": env.input_path(other_root), "other_run": other.run, "available": True, "rung_by_rung": {}, "mass_matched": {}, "sets": {}}
    for key, sd in grid.sets.items():
        if key in other.sets:
            od = other.sets[key]
            assert sd.set_hash == od.set_hash and sd.n_sequences == od.n_sequences, f"{key}: the two runs do not score the same set ({sd.set_hash[:12]} against {od.set_hash[:12]})"
            out["sets"][key] = {"set_hash": sd.set_hash, "n_sequences": sd.n_sequences}
    other_chains = {s: build_chains(od) for s, od in other.sets.items()}
    other_pre = load_pre_reads(other_pre_dir) if other_pre_dir else None
    for title, lab, kind in COMPARISON_CURVES:
        eval_set = lab.split("/")[1]
        if eval_set not in grid.sets or eval_set not in other.sets:
            out["rung_by_rung"][title] = {"available": False, "reason": f"set {eval_set} absent in one run"}
            continue
        sd, od = grid.sets[eval_set], other.sets[eval_set]
        this_chain = next((c for c in build_chains(sd).values() if c.label == lab), None)
        other_chain = next((c for c in other_chains[eval_set].values() if c.label == lab), None)
        if this_chain is None or other_chain is None:
            out["rung_by_rung"][title] = {"available": False, "reason": f"chain absent in {'this' if this_chain is None else 'the other'} run"}
            continue
        rs = _resample_for(grid, eval_set, None, replicates, master_seed, resamples)
        this_rungs, other_rungs = this_chain.rung_order(), other_chain.rung_order()
        shared = [r for r in this_rungs if r in other_chain.rungs]
        rows = []
        for r in shared:
            a, b = excess_matrix(sd, this_chain.rungs[r]), excess_matrix(od, other_chain.rungs[r])
            if a.shape != b.shape:
                rows.append({"rung": r, "note": f"draw counts differ ({a.shape[0]} against {b.shape[0]})"})
                continue
            pdiff = st.paired_difference(a, b, rs)
            row = {"rung": r, "n_on_this": float(np.mean([sd.cells.loc[c.name, "n_on"] for c in this_chain.rungs[r]])), "n_on_other": float(np.mean([od.cells.loc[c.name, "n_on"] for c in other_chain.rungs[r]])),
                   "excess_this": float(a.mean()), "excess_other": float(b.mean()), "paired_difference": pdiff["mean"], "interval": pdiff["interval"], "half_width": pdiff["half_width"]}
            if kind == "hz":
                for who, sdd, ch in (("this", sd, this_chain), ("other", od, other_chain)):
                    d = matrix(sdd, ch.rungs[r], "d_0.1")
                    t = matrix(sdd, ch.rungs[r], "t_star_0.1")
                    read = st.readability(t)
                    row[f"testable_{who}"] = read["floor_met"]
                    res = st.hard_zero_rung(d, t, rs, max(1, len([x for x in ch.rung_order() if x not in SUB_RUNGS and x != "8"]))) if read["floor_met"] else None
                    row[f"d_hat_{who}"] = res["d_hat"] if res else float("nan")
                    row[f"d_interval_{who}"] = res["interval"] if res else [float("nan"), float("nan")]
            rows.append(row)
        out["rung_by_rung"][title] = {"available": True, "rows": rows, "rungs_only_in_this_run": [r for r in this_rungs if r not in other_chain.rungs], "rungs_only_in_other_run": [r for r in other_rungs if r not in this_chain.rungs],
                                      "paired_on": "the same sequence and draw, this minus other, the shared sequence resample, 95 percent uncorrected"}
    for title, lab, kind in COMPARISON_CURVES[:2]:
        eval_set = "E"
        if eval_set not in grid.sets or eval_set not in other.sets:
            out["mass_matched"][title] = {"available": False}
            continue
        sd, od = grid.sets[eval_set], other.sets[eval_set]
        this_chain = next((c for c in build_chains(sd).values() if c.label == lab), None)
        other_chain = next((c for c in other_chains[eval_set].values() if c.label == lab), None)
        if this_chain is None or other_chain is None:
            out["mass_matched"][title] = {"available": False}
            continue
        pooled_other = [r for r in other_chain.rung_order() if r != "8"]
        pooled_this = [r for r in this_chain.rung_order() if r != "8"]
        po = _union_points(od, other_chain, pooled_other)
        pt = _union_points(sd, this_chain, pooled_this)
        if lab.startswith("union/E/D_unif/tau0.1/r0") and other_pre is not None:
            edges = np.asarray(other_pre.summary["item7_switched_mass"]["union_tau0.1_r0_pooled"]["deciles_0_to_100"], dtype=np.float64)
            src = "the other run's pre-reads"
        else:
            edges = st.decile_edges(po["sigma"])
            src = "the other run's loop sigma"
        rs = _resample_for(grid, eval_set, None, replicates, master_seed, resamples)
        bt, bo = st.assign_bins(pt["sigma"], edges), st.assign_bins(po["sigma"], edges)
        n = rs.n
        rows = []
        for i in range(11):
            st_, so = bt == i, bo == i
            nt, no = np.unique(pt["seq"][st_]).size, np.unique(po["seq"][so]).size
            row: dict[str, Any] = {"bin": i, "overflow": i == 10, "edge_low": float(edges[i]) if i < 10 else float(edges[10]), "edge_high": float(edges[i + 1]) if i < 10 else float("inf"),
                                   "n_sequences_this": int(nt), "n_sequences_other": int(no), "populated": bool(nt >= 64 and no >= 64),
                                   "mean_this": float(pt["excess"][st_].mean()) if nt >= 64 else float("nan"), "mean_other": float(po["excess"][so].mean()) if no >= 64 else float("nan")}
            if row["populated"]:
                num_t = np.bincount(pt["seq"][st_], weights=pt["excess"][st_], minlength=n); cnt_t = np.bincount(pt["seq"][st_], minlength=n).astype(np.float64)
                num_o = np.bincount(po["seq"][so], weights=po["excess"][so], minlength=n); cnt_o = np.bincount(po["seq"][so], minlength=n).astype(np.float64)
                lo, hi = st.percentile_interval(rs.ratios(num_t, cnt_t) - rs.ratios(num_o, cnt_o), 1)
                row.update({"difference": row["mean_this"] - row["mean_other"], "interval": [lo, hi]})
            rows.append(row)
        out["mass_matched"][title] = {"available": True, "edges": edges.tolist(), "edges_source": src, "rows": rows}
    log(f"[analyze] compared with {other.run} at {other_root}: " + ", ".join(f"{t}: {'ok' if v.get('available') else v.get('reason', 'n/a')}" for t, v in out["rung_by_rung"].items()))
    return out


def _append_comparison(L: list[str], out_dir: Path, cmp: dict[str, Any]) -> None:
    L.append(f"## 8. This run against the {cmp.get('other_run', 'other')} run's stores ({cmp['other_root']}): this minus other, paired on the sequence and the draw")
    if not cmp.get("available"):
        L.append("Not available.")
        L.append("")
        return
    L.append("Sets scored in common (hashes asserted equal): " + ", ".join(f"{k} ({v['n_sequences']})" for k, v in cmp["sets"].items()))
    for title, item in cmp["rung_by_rung"].items():
        if not item.get("available"):
            L.append(f"- {title}: {item['reason']}")
            continue
        df = pd.DataFrame(item["rows"])
        for col in ("interval", "d_interval_this", "d_interval_other"):
            if col in df.columns:
                df[col] = df[col].apply(lambda v: _interval(v) if isinstance(v, list) else v)
        df.to_csv(out_dir / f"compare_{title.replace(' ', '_').replace('(', '').replace(')', '')}.csv", index=False)
        L.append(f"### {title}: rungs only in this run {item['rungs_only_in_this_run'] or 'none'}, only in the other {item['rungs_only_in_other_run'] or 'none'}")
        L.append(_md(df))
        L.append("")
    for title, item in cmp["mass_matched"].items():
        if not item.get("available"):
            L.append(f"- {title}, mass-matched: not available")
            continue
        df = pd.DataFrame(item["rows"])
        if "interval" in df.columns:
            df["interval"] = df["interval"].apply(lambda v: _interval(v) if isinstance(v, list) else v)
        df.to_csv(out_dir / f"compare_mass_matched_{title.replace(' ', '_').replace('(', '').replace(')', '')}.csv", index=False)
        L.append(f"### {title} at matched switched mass, edges from {item['edges_source']} applied to both runs' union cells")
        L.append(_md(df))
        L.append("")


# ----------------------------------------------------------------------------- the report


def _md(df: pd.DataFrame, floatfmt: str = "{:.4f}") -> str:
    if df is None or len(df) == 0:
        return "(empty)"
    cols = list(df.columns)
    lines = ["| " + " | ".join(str(c) for c in cols) + " |", "|" + "---|" * len(cols)]
    for _, row in df.iterrows():
        vals = []
        for c in cols:
            v = row[c]
            if isinstance(v, (float, np.floating)):
                vals.append("" if (isinstance(v, float) and math.isnan(v)) else floatfmt.format(v))
            elif isinstance(v, (list, tuple)):
                vals.append("[" + ", ".join(floatfmt.format(x) if isinstance(x, (float, np.floating)) else str(x) for x in v) + "]")
            else:
                vals.append(str(v))
        lines.append("| " + " | ".join(vals) + " |")
    return "\n".join(lines)


def _pc_word(pc: dict[str, Any]) -> str:
    """A positive control's word: pass, FAIL, or not judged (control not run); recorded deviation."""
    if not pc.get("applies"):
        return "n/a"
    if pc.get("control_not_run") or pc.get("pass") is None:
        return "not judged (control not run)"
    return "pass" if pc["pass"] else "FAIL"


def _verdict_read(pc: dict[str, Any]) -> bool | None:
    """Whether a curve's verdict is read: True, False (its positive control failed), or None (not judged: the control has not run)."""
    if not pc.get("applies"):
        return True
    if pc.get("control_not_run") or pc.get("pass") is None:
        return None
    return bool(pc["pass"])


def _interval_sci(iv: list[float]) -> str:
    return f"[{iv[0]:+.3e}, {iv[1]:+.3e}]" if iv and all(isinstance(x, float) and math.isfinite(x) for x in iv) else "n/a"


def _interval(iv: list[float]) -> str:
    return f"[{iv[0]:+.4f}, {iv[1]:+.4f}]" if iv and all(isinstance(x, float) and math.isfinite(x) for x in iv) else "n/a"


def write_report(out_dir: Path, grid: Grid, ctx: dict[str, Any]) -> Path:
    out_dir.mkdir(parents=True, exist_ok=True)
    L: list[str] = [f"# Analysis of the grid, run {grid.run} (the pre-registered read order)", "",
                    f"Stores: {', '.join(s.name for s in grid.stores)}; sets {', '.join(f'{k} ({v.n_sequences} sequences, {len(v.cells)} cells)' for k, v in grid.sets.items())}; "
                    f"replicates {ctx['replicates']}; seed (master {ctx['master_seed']}, boot, set); commit {ctx['blindness']['commit']['project'][:12]} (dirty {ctx['blindness']['commit']['dirty']}).", ""]
    L.append("## 0. Asserts")
    L.append(f"- References bitwise across stores per set: {ctx['grid_reference_assert']}")
    L.append(f"- Verification-store canary (equality only): {ctx['verify_canary']}")
    L.append(f"- Pre-reads: {ctx['pre_reads_assert']}")
    L.append(f"- Two-path recompute from kl_prefix_sum and the reference arrays: " + "; ".join(f"{s}: {v['n_cells']} cells, {v['n_checks']} checks, max ratio {v['max_ratio']:.4f}, {'pass' if v['pass'] else 'FAIL'}" for s, v in ctx["two_path"].items()))
    if ctx.get("chain_completeness"):
        L.append("- Every non-reference, non-donor-side cell in exactly one chain set (rule, descriptive family, descriptive rung): " + "; ".join(f"{k}: {v['n_cells']} ({v['rule']}, {v['descriptive_family']}, {v['descriptive_rung']})" for k, v in ctx["chain_completeness"].items() if v["n_cells"]))
    L.append("")
    pre = ctx["preconditions"]
    L.append("## 1. Preconditions and the sanity checks")
    L.append(f"P1 ({pre['P1']['n_pass']}/{pre['P1']['n']}): " + "; ".join(f"{x['chain']}: rung 0 {x['rung_0']:.4f}, rung 8 {x['rung_8']:.4f} -> {'pass' if x['pass'] else 'FAIL'}" for x in pre["P1"]["chains"]))
    L.append("P2: " + "; ".join(f"{x['chain']}: rung 8 {x['rung_8']:.4f} vs unmasked {x['unmasked']:.4f} / importances {x['importances']:.4f}" if x["unmasked"] is not None and x["importances"] is not None
                                else f"{x['chain']}: rung 8 {x['rung_8']:.4f} (a reference row absent)" for x in pre["P2"]))
    L.append(f"P3: permitted cells below their label {pre['P3']['permitted_cells_with_entries_below_label']} of {pre['P3']['permitted_cells']}; hard-zero rung-8 counts positive {all(v > 0 for v in pre['P3']['hard_zero_rung_8_counts'].values())} -> {'pass' if pre['P3']['pass'] else 'FAIL'}")
    L.append(f"P4: {pre['P4']['n_pass']}/{pre['P4']['n']} chains" + ("" if pre["P4"]["n_pass"] == pre["P4"]["n"] else "; failing: " + ", ".join(x["chain"] for x in pre["P4"]["chains"] if not x["pass"]))
             + (f"; descriptive rungs (2a, 2b): {pre['P4']['n_pass_descriptive']}/{pre['P4']['n_descriptive']} chains" + ("" if pre["P4"]["n_pass_descriptive"] == pre["P4"]["n_descriptive"] else "; failing: " + ", ".join(x["chain"] for x in pre["P4"]["descriptive_chains"] if not x["pass"])) if pre["P4"].get("n_descriptive") else ""))
    L.append("P5 (positive controls, by the registered rule): " + ("; ".join(f"{k}: {_pc_word(v)} ({v['n_rungs_judged']} rungs; {v['kind']})" for k, v in pre["P5"].items()) or "no curve applies"))
    L.append("")
    L.append(_md(pd.DataFrame(ctx["sanity"])[["id", "pass", "note"]]))
    L.append("")

    overlap_by_rung = ctx.get("overlap_by_rung", {})
    overlap_other = ctx.get("overlap_by_union_chain", {})

    def overlap_of(entry: dict[str, Any], rung: str) -> float:
        ch = entry["chain"]
        if ch.family == "union" and ch.eval_set == "E" and ch.pool == "D_unif" and ch.tau == 0.1:
            return overlap_by_rung.get(rung, float("nan"))  # the pre-reads' overlap table (control_overlap.csv); both backgrounds: the sets do not depend on it (recorded deviation)
        # the other union chains (tau = 0 and 0.5): the same fraction from the pre-reads' control_overlap.csv
        return overlap_other.get((ch.eval_set, ch.pool, ch.tau, ch.delta), {}).get(rung, float("nan")) if ch.family == "union" else float("nan")

    def union_table(entry: dict[str, Any]) -> pd.DataFrame:
        r = entry["result"]
        rows = []
        for rung in r["rungs"]:
            p = r["per_rung"][rung]
            rows.append({"rung": rung, "n_on": p["n_on"], "mean_sigma": p["mean_sigma"], "overlap": overlap_of(entry, rung), "mean_kl": p["mean_kl"], "excess": p["e_hat"], "interval": _interval(p["interval"]),
                         "half_width": p["half_width"], "two_level": _interval(p["two_level_interval"]), "draws_positive": f"{p['n_draws_positive']}/{p['n_draws']}", "fraction_seq_above_X": p["fraction_sequences_above_X"],
                         "detected": p["detected"], "material": p["material"], "repair": p["repair"], "differs_at_m_8": p["at_m_8"]["differs"]})
        return pd.DataFrame(rows)

    def union_section(title: str, lab: str) -> None:
        entry = ctx["union"].get(lab)
        L.append(f"## {title}")
        if entry is None:
            L.append("Not in these stores.")
            L.append("")
            return
        r = entry["result"]
        L.append(f"Chain `{lab}`; rung 0 mean {r['rung_0_mean']:.4f}; m = {r['m']} rungs compared; **label: {r['label']}** (at m = 8: {r['label_at_m_8']}{', differs' if r['label_differs_at_m_8'] else ''}); "
                 f"j_det = {r['j_det']}, j_mat = {r['j_mat']}, first repair rung = {r['first_repair']}; per draw: " + ", ".join(f"{k}: det {v['j_det']}, mat {v['j_mat']}" for k, v in r["per_draw"].items()))
        L.append("")
        df = union_table(entry)
        df.to_csv(out_dir / f"{lab.replace('/', '_')}.csv", index=False)
        L.append(_md(df))
        if r.get("descriptive_rungs"):  # the descriptive rungs 2a, 2b beside the table, uncorrected 95 percent intervals, m unchanged
            rows_d = [{"rung": rg + " (descriptive)", "n_on": v["n_on"], "mean_sigma": v["mean_sigma"], "mean_kl": v["mean_kl"], "excess": v["e_hat"], "interval_uncorrected": _interval(v["interval"]), "half_width": v["half_width"],
                       "draws_positive": f"{v['n_draws_positive']}/{v['n_draws']}", "fraction_seq_above_X": v["fraction_sequences_above_X"], "n_on_per_draw": v["n_on_per_draw"]} for rg, v in r["descriptive_rungs"].items()]
            df_d = pd.DataFrame(rows_d)
            df_d.to_csv(out_dir / f"{lab.replace('/', '_')}__descriptive_rungs.csv", index=False)
            L.append("")
            L.append(f"Descriptive rungs outside the comparison count (m stays {r['m']}; uncorrected 95 percent intervals):")
            L.append(_md(df_d.drop(columns=["n_on_per_draw"])))
        pv = r.get("paired_vs_control")
        if isinstance(pv, dict):
            L.append("")
            L.append("Paired union minus control on the same sequence, draw, and rung (95 percent uncorrected), with the pre-reads' overlap of the two sets: "
                     + "; ".join(f"rung {k}: {v['mean']:+.4f} {_interval(v['interval'])} (overlap {overlap_of(entry, k):.3f})" for k, v in pv.items()))
        elif pv:
            L.append("")
            L.append(f"Paired union minus control: {pv}.")
        if "rung_3_vs_4" in r:
            v = r["rung_3_vs_4"]
            L.append(f"Rung 4 minus rung 3 at nearly the same count (diffuse against concentrated), paired: {v['mean']:+.4f} {_interval(v['interval'])}.")
        if r.get("x_crossing"):  # the crossing of X as a bracket, never a single number
            xc = r["x_crossing"]
            if xc.get("bracket"):
                per = "; ".join(f"draw {d['draw']}: " + (f"{d['bracket'][0]} ({d['n_low']:.0f}) to {d['bracket'][1]} ({d['n_high']:.0f}), log-linear {d['interpolated_n']:.0f}" if d.get("bracket") else d.get("note", "none")) for d in xc["per_draw"])
                L.append(f"Crossing of X = {xc['x']} along the position run {xc['position_rungs']}: between rung {xc['bracket'][0]} (n_on {xc['n_low']:.0f}, excess {xc['e_low']:+.4f}) and rung {xc['bracket'][1]} (n_on {xc['n_high']:.0f}, excess {xc['e_high']:+.4f}); "
                         f"the log-linear interpolated point inside the bracket sits at n_on about {xc['interpolated_n']:.0f}. Per draw: {per}.")
            else:
                L.append(f"Crossing of X = {xc['x']} along the position run {xc['position_rungs']}: {xc.get('note')}.")
            pd.DataFrame([{"draw": "curve", **{k: v for k, v in xc.items() if k not in ("per_draw", "position_rungs", "e_hat", "n_on")}}] + [{k: v for k, v in d.items()} for d in xc["per_draw"]]).to_csv(out_dir / f"{lab.replace('/', '_')}__x_crossing.csv", index=False)
        if "4" in r["per_rung"]:
            L.append(f"Rung 4 (one donor sequence): excess {r['per_rung']['4']['e_hat']:+.4f} {_interval(r['per_rung']['4']['interval'])}, fraction of sequences with excess above X {r['per_rung']['4']['fraction_sequences_above_X']:.3f}.")
        if "by_reader_label" in r:
            if isinstance(r["by_reader_label"], str):
                L.append(f"Per-rung excess by reader label on E: {r['by_reader_label']}.")
            else:
                L.append("Per-rung excess by reader label on E (each label's own resample, the curve's m):")
                rows = []
                for lab_, d in r["by_reader_label"].items():
                    for rg, v in d.items():
                        rows.append({"label": lab_, "n": v["n"], "rung": rg, "excess": v["e_hat"], "interval": _interval(v["interval"]), "half_width": v["half_width"], "detected": v["detected"], "material": v["material"]})
                df_l = pd.DataFrame(rows)
                df_l.to_csv(out_dir / f"{lab.replace('/', '_')}__by_reader_label.csv", index=False)
                L.append(_md(df_l))
        if isinstance(r.get("paired_vs_control_by_reader_label"), dict) and r["paired_vs_control_by_reader_label"]:
            rows = []
            for lab_, d in r["paired_vs_control_by_reader_label"].items():
                for rg, v in d.items():
                    rows.append({"label": lab_, "n": v["n"], "rung": rg, "union_minus_control": v["mean"], "interval_uncorrected": _interval(v["interval"]), "half_width": v["half_width"],
                                 "control_excess": v["control_excess"], "control_interval_uncorrected": _interval(v["control_interval"])})
            if rows:
                df_c = pd.DataFrame(rows)
                df_c.to_csv(out_dir / f"{lab.replace('/', '_')}__by_reader_label_vs_control.csv", index=False)
                L.append("")
                L.append("Paired union minus control by reader label at rungs 1 to 4 and 5a (each label's own resample, uncorrected 95 percent), the control's per-label excess beside:")
                L.append(_md(df_c))
        L.append("")

    union_section("2. Curve 1: the union under r = 0, tau = 0.1, Delta excluded, on E", "union/E/D_unif/tau0.1/r0/excl/ctl-none")
    union_section("2b. Its plain control", "union/E/D_unif/tau0.1/r0/excl/ctl-plain")
    L.append("## 3. The mass-matched deciles and the slope")
    for lab, item in ctx["descriptives"]["deciles"].items():
        L.append(f"`{lab}`: edges from {item['edges_source']}: " + ", ".join(f"{e:.1f}" for e in item["edges"]) + f"; union slope {item['slope_union']['slope']:.3e} {_interval_sci(item['slope_union']['slope_interval'])} (intercept {item['slope_union']['intercept']:+.4f} {_interval(item['slope_union']['intercept_interval'])})"
                 + (f"; control slope {item['slope_control']['slope']:.3e} {_interval_sci(item['slope_control']['slope_interval'])}" if "slope_control" in item else ""))
        if isinstance(item["bins"], list):
            df = pd.DataFrame([{k: (v if k != "interval" else _interval(v)) for k, v in b.items()} for b in item["bins"]])
            for col in ("union_mean_excess", "control_mean_excess", "difference", "interval"):  # present even when no bin is populated, so the CSV's schema is fixed
                if col not in df.columns:
                    df[col] = np.nan
            df.to_csv(out_dir / f"deciles_{lab.replace('/', '_')}.csv", index=False)
            L.append(_md(df))
        else:
            L.append(str(item["bins"]))
        L.append("Local slopes (difference quotients): " + "; ".join(f"{q['from']}->{q['to']}: {q['quotient']:.3e}" for q in item["difference_quotients_union"]))
        L.append("")
    for k in range(8):
        pass
    union_section("4. Curve 2: the union under the uniform background (draw 0 shown; every draw in the CSVs)", "union/E/D_unif/tau0.1/uniform/excl/k0/ctl-none")
    for k in range(1, 8):
        lab = f"union/E/D_unif/tau0.1/uniform/excl/k{k}/ctl-none"
        if lab in ctx["union"]:
            union_table(ctx["union"][lab]).to_csv(out_dir / f"{lab.replace('/', '_')}.csv", index=False)
            r = ctx["union"][lab]["result"]
            L.append(f"- draw {k}: label {r['label']}, j_det {r['j_det']}, j_mat {r['j_mat']}, rung 8 {r['per_rung']['8']['mean_kl']:.4f} (rung 0 {r['rung_0_mean']:.4f})")
    two = ctx["descriptives"].get("two_by_two", {})
    if two:
        L.append("")
        L.append("The two-by-two completed (means over E with sequence standard errors): " + "; ".join(f"{k}: {v['mean']:.4f} (se {v['se']:.4f})" for k, v in two.items() if isinstance(v, dict) and "mean" in v and "se" in v)
                 + (f"; curve 2 rung 8 per draw {[round(x, 4) for x in two['curve_2_rung_8_per_draw']]} against stochastic rung 0 per draw {[round(x, 4) for x in two.get('stochastic_rung_0_per_draw', [])]}" if "curve_2_rung_8_per_draw" in two else ""))
        for k in ("fourth_cell", "fourth_cell_delta_included"):
            if k in two and "paired_minus_importances" in two[k]:
                a, b = two[k]["paired_minus_importances"], two[k]["paired_minus_unmasked"]
                L.append(f"{k}, paired per sequence: minus importances-as-masks {a['mean']:+.4f} (se {a['se']:.4f}); minus unmasked {b['mean']:+.4f} (se {b['se']:.4f}).")
        if "curve2_over_curve1_rung_8_per_sequence" in two:
            q = two["curve2_over_curve1_rung_8_per_sequence"]
            L.append(f"Curve 2's rung 8 over curve 1's per sequence (paired; the mean over draws of curve 2 divided by curve 1): quantiles 0/10/25/50/75/90/100 = {[round(x, 3) for x in q['quantiles_0_10_25_50_75_90_100']]}, mean {q['mean']:.3f}, "
                     f"fraction below 0.5 {q['fraction_below_0.5']:.3f}, above 0.9 {q['fraction_above_0.9']:.3f} (n {q['n']}): whether saturation is uniform across sequences or a mixture.")
    L.append("")
    L.append("## 5. The hard-zero chains: testability, positive controls, budgets (both tau_q)")
    # the one-table summary first, then curves 3, 4, 5, then their controls and the mirrors

    def hz_stratum(hz: dict[str, Any]) -> str:
        return "other" if "other" in hz["by_tau_q"]["0.1"] else "all"

    summary_rows = []
    for lab, hz in ctx["hard_zero"].items():
        pc = hz["positive_control"]
        stratum = hz_stratum(hz)
        for part in ("donor_chain", "sub_rung_chain"):
            res01, res0 = hz["by_tau_q"]["0.1"][stratum].get(part), hz["by_tau_q"]["0"][stratum].get(part)
            if not res01:
                continue
            testable = [r for r in res01["rungs"] if res01["per_rung"][r]["testable"]]
            summary_rows.append({"chain": lab, "part": part, "stratum": stratum, "positive_control": _pc_word(pc), "verdict_read": _verdict_read(pc),
                                 "testable_rungs_at_0.1": ", ".join(testable) or "none", "budget_at_0.1": res01["budget"]["budget_rung"], "budget_at_0": res0["budget"]["budget_rung"] if res0 else None})
        if "one_cell_rung_8" in hz:
            one = hz["one_cell_rung_8"]
            summary_rows.append({"chain": lab, "part": "rung 8 alone (one-cell rule)", "stratum": "all", "positive_control": "n/a", "verdict_read": True, "testable_rungs_at_0.1": "8" if one["0.1"]["testable"] else "none",
                                 "budget_at_0.1": one["0.1"]["label"], "budget_at_0": one["0"]["label"]})
    df_s = pd.DataFrame(summary_rows)
    df_s.to_csv(out_dir / "hard_zero_summary.csv", index=False)
    L.append(_md(df_s))
    L.append("")
    first = ["hard_zero/E_lab/D_code/tau0.1/ones/incl/ctl-none", "code_specific_hard/E_lab/D_code/tau0.1/ones/incl/ctl-none", "hard_zero/E/D_unif/tau0.1/ones/incl/ctl-none"]
    ordered = [lab for lab in first if lab in ctx["hard_zero"]] + [lab for lab in ctx["hard_zero"] if lab not in first]
    for lab in ordered:
        hz = ctx["hard_zero"][lab]
        pc = hz["positive_control"]
        L.append(f"### `{lab}`" + (" (curve 3)" if lab == first[0] else " (curve 4)" if lab == first[1] else " (curve 5)" if lab == first[2] else ""))
        L.append(f"Positive control: " + (f"{pc['kind']}: {_pc_word(pc)} ({pc['n_rungs_judged']} rungs judged)" if pc.get("applies") else "does not apply")
                 + (f"; readability floor equals the pre-reads' table: {hz.get('floor_matches_pre_reads')} ({hz.get('floor_rows_matched')} of {hz.get('floor_rows_checked')} rows matched)" if "floor_matches_pre_reads" in hz else ""))
        ov = (ctx["descriptives"].get("control_overlap") or {}).get(lab)
        if ov:  # how nearly the erased set and its control are the same population
            L.append(f"The erased set against its {ov['control']} control per rung (mean over draws; the control's pool is {'the alive set' if ov['control'] == 'plain' else 'alive minus prose-named at this tau'}): "
                     + "; ".join(f"rung {x['rung']}: overlap {x['overlap']:.0f} of {x['n_named']:.0f} erased ({x['fraction_of_named']:.3f}; control {x['n_control']:.0f} from a pool of {x['control_pool_size']}, of which {x['named_in_control_pool']:.0f} are the erased set's own"
                                 + (f", overflow {x['control_overflow']:.0f}" if x["control_overflow"] else "") + ")" for x in ov["rows"]))
            pd.DataFrame(ov["rows"]).to_csv(out_dir / f"{lab.replace('/', '_')}__control_overlap.csv", index=False)
        if "one_cell_rung_8" in hz:
            one = hz["one_cell_rung_8"]
            L.append(f"Rung 8 alone under the one-cell rule (m = 1, not counted in the donor chain's m), {one['n_erased']:.0f} erased: "
                     + "; ".join(f"tau_q = {tag}: {'testable' if one[tag]['testable'] else 'not testable'}, " + (f"d_hat {one[tag]['result']['d_hat']:+.4f} {_interval(one[tag]['result']['interval'])}, {one[tag]['label']}" if one[tag]["result"] else one[tag]["label"]) for tag in ("0.1", "0"))
                     + f"; unconditional {one['unconditional']:.4f}")
        for tag in ("0.1", "0"):
            for gname, parts in hz["by_tau_q"][tag].items():
                for part, res in parts.items():
                    rows = []
                    for r in res["rungs"]:
                        p = res["per_rung"][r]
                        rd = p["readability"]
                        row = {"rung": r, "n_off": p["n_off"], "mean_contributing": rd["mean_n_contributing"], "clean_prefix_fraction": rd["mean_clean_prefix_fraction"], "testable": p["testable"], "label": None,
                               "d_hat": None, "interval": None, "half_width": None, "draws_above_X": None, "unconditional": hz["unconditional"][gname][r]}
                        if p["result"]:
                            q = p["result"]
                            row.update({"label": q["label"], "d_hat": q["d_hat"], "interval": _interval(q["interval"]), "half_width": q["half_width"], "draws_above_X": f"{q['n_draws_above_X']}/{q['n_draws']}"})
                        else:
                            row["label"] = "not testable with these donors"
                        rows.append(row)
                    df = pd.DataFrame(rows)
                    df.to_csv(out_dir / f"{lab.replace('/', '_')}__tau_q{tag}__{gname}__{part}.csv", index=False)
                    verdict = ("no verdict read (positive control failed)" if _verdict_read(pc) is False else f"budget rung {res['budget']['budget_rung']}" + (" (positive control not judged: control not run)" if _verdict_read(pc) is None else ""))
                    L.append(f"tau_q = {tag}, stratum {gname}, {part} (m = {res['m']}): {verdict}")
                    L.append(_md(df))
                    L.append("")
    L.append("## 6. The labels of curves 1 to 5")
    for title, lab, kind in (("Curve 1", "union/E/D_unif/tau0.1/r0/excl/ctl-none", "union"), ("Curve 2 (draw 0; all draws above)", "union/E/D_unif/tau0.1/uniform/excl/k0/ctl-none", "union"),
                             ("Curve 3", "hard_zero/E_lab/D_code/tau0.1/ones/incl/ctl-none", "hz"), ("Curve 4", "code_specific_hard/E_lab/D_code/tau0.1/ones/incl/ctl-none", "hz"), ("Curve 5", "hard_zero/E/D_unif/tau0.1/ones/incl/ctl-none", "hz")):
        if kind == "union" and lab in ctx["union"]:
            r = ctx["union"][lab]["result"]
            L.append(f"- {title}: **{r['label']}** (j_det {r['j_det']}, j_mat {r['j_mat']}; half-widths from {min(p['half_width'] for p in r['per_rung'].values()):.4f} to {max(p['half_width'] for p in r['per_rung'].values()):.4f})")
        elif kind == "hz" and lab in ctx["hard_zero"]:
            hz = ctx["hard_zero"][lab]
            stratum = "other" if "other" in hz["by_tau_q"]["0.1"] else "all"
            parts = hz["by_tau_q"]["0.1"][stratum]
            pc = hz["positive_control"]
            b = "; ".join(f"{part}: budget rung {res['budget']['budget_rung']}, labels {res['budget']['labels']}" for part, res in parts.items())
            strict = "; ".join(f"{part}: budget rung {res['budget']['budget_rung']}" for part, res in hz["by_tau_q"]["0"][stratum].items())
            L.append(f"- {title} on {stratum}: positive control {_pc_word(pc) if pc.get('applies') else 'n/a'}; at tau_q = 0.1: {b}; at tau_q = 0: {strict}")
        else:
            L.append(f"- {title}: not in these stores")
    L.append("")
    L.append("## 7. Everything else")
    d = ctx["descriptives"]
    if d.get("never_named"):
        nn = d["never_named"]
        L.append(f"### The never-named chain (`{nn['chain']}`), D(n) against n with the linear and quadratic lines; whole set n = {nn['whole_set']['n']}, D = {nn['whole_set']['D']:.4f}; alive control present: {nn['control_present']}")
        df = pd.DataFrame(nn["rungs"])
        df.to_csv(out_dir / "never_named_chain.csv", index=False)
        df_p = df.drop(columns=["D_per_draw"])
        df_p["n_per_draw"] = df_p["n_per_draw"].map(lambda v: " ".join(str(int(x)) for x in v))  # the erased count per draw, matched to the union's per-draw n_on
        L.append(_md(df_p))
        L.append("")
        L.append("The family's rung-8 cells under the one-cell rule (the whole set with Delta included and excluded, the strict cell at tau = 0), the conditional figure at both tau_q:")
        rows8 = []
        for lab8, hz8 in ctx["hard_zero"].items():
            if hz8["chain"].family == "never_named_hard" and "one_cell_rung_8" in hz8:
                one = hz8["one_cell_rung_8"]
                row = {"cell": lab8, "n_erased": one["n_erased"], "unconditional": one["unconditional"]}
                for tag in ("0.1", "0"):
                    row[f"testable_{tag}"] = one[tag]["testable"]
                    row[f"d_hat_{tag}"] = one[tag]["result"]["d_hat"] if one[tag]["result"] else float("nan")
                    row[f"interval_{tag}"] = _interval(one[tag]["result"]["interval"]) if one[tag]["result"] else ""
                    row[f"label_{tag}"] = one[tag]["label"]
                rows8.append(row)
        df8 = pd.DataFrame(rows8)
        df8.to_csv(out_dir / "never_named_rung_8_cells.csv", index=False)
        L.append(_md(df8))
        L.append("")
    # ---- the tau = 0 union, the level cells, the ranked pair
    if "union/E/D_unif/tau0.5/r0/excl/ctl-none" in ctx["union"]:  # curve 1 at tau = 0.5 with its plain control, its section and CSVs like every other union chain
        L.append("### Curve 1 at tau = 0.5 and its plain control, read as any union chain")
        union_section("The union under r = 0, tau = 0.5, Delta excluded, on E", "union/E/D_unif/tau0.5/r0/excl/ctl-none")
        union_section("Its plain control", "union/E/D_unif/tau0.5/r0/excl/ctl-plain")
    t0u = d.get("tau0_union")
    if t0u:
        L.append("### The tau = 0 union and its plain control, read as any union chain")
        union_section("The tau = 0 union under r = 0 on E", t0u["chain"])
        union_section("Its plain control", t0u["control_chain"])
        if t0u.get("control_overflow_by_rung"):
            L.append("The control's overflow into the dead set per rung (the matched count exceeds the alive set from rung 5; mean over draws of the summed per-module overflow, from the pre-reads): "
                     + "; ".join(f"rung {r}: {v['mean_overflow']:.0f} of n_on {v['n_on']:.0f}" for r, v in t0u["control_overflow_by_rung"].items()))
            pd.DataFrame([{"rung": r, **{k: v2 for k, v2 in v.items() if k != "per_draw"}, "per_draw": " ".join(f"{x:.0f}" for x in v["per_draw"])} for r, v in t0u["control_overflow_by_rung"].items()]).to_csv(out_dir / "tau0_union_control_overflow.csv", index=False)
        if t0u.get("reference_lines"):
            L.append("")
            L.append("Reference lines beside the chain (its rung 8 is the complement of the strict set: everything the pool labels above 0 pinned at 1, the strict 5,336 at their labels):")
            df_r = pd.DataFrame(t0u["reference_lines"])
            df_r.to_csv(out_dir / "tau0_union_reference_lines.csv", index=False)
            L.append(_md(df_r))
        L.append("")
    lv = d.get("level")
    if lv:
        L.append("### The level cells: the alive set at s + (1 - s) g, the never-named set at its labels or at 1, beside their four corners")
        df_l = pd.DataFrame(lv["rows"])
        df_l["footprint_interval"] = df_l["footprint_interval"].map(lambda v: _interval(v) if isinstance(v, list) else "")
        df_l.to_csv(out_dir / "level_cells.csv", index=False)
        L.append(_md(df_l.drop(columns=["cell"])))
        L.append("")
        L.append("The footprint is L(s, labels) - L(s, 1), paired per sequence with the shared resample (uncorrected 95 percent). The soft-erase chain's points at their own switched fraction (s = 1 - sigma_j / sigma_8), drawn on fig5:")
        df_s = pd.DataFrame(lv["soft_erase_points"])
        df_s.to_csv(out_dir / "level_cells_soft_erase_points.csv", index=False)
        L.append(_md(df_s))
        L.append("")
    rk = d.get("ranked")
    if rk:
        L.append("### The ranked never-named pair: D(n) against n beside the random chain's, both keys, both ends")
        if rk.get("rank_correlation"):
            rc = rk["rank_correlation"]
            L.append(f"Rank correlation (Spearman, average ranks for ties) between the weight norm and the positive-label count over the never-named set (n = {rc['n_never_named']}, of which {rc['never_named_with_positive_count_zero']} have count zero): "
                     f"{rc['spearman_weight_norm_vs_positive_count_over_never_named']:.3f} (over all subcomponents {rc['spearman_over_all']:.3f}), from the pre-reads' rank_keys.parquet.")
        df_k = pd.DataFrame(rk["rows"])
        df_k.to_csv(out_dir / "ranked_pair.csv", index=False)
        L.append(_md(df_k))
        L.append("")
        L.append("Top-n minus bottom-n at the same n, paired per sequence (uncorrected 95 percent):")
        df_t = pd.DataFrame(rk["top_minus_bottom"])
        if len(df_t):
            df_t["interval"] = df_t["interval"].map(_interval)
        df_t.to_csv(out_dir / "ranked_pair_top_minus_bottom.csv", index=False)
        L.append(_md(df_t))
        L.append("")
    L.append("### Delta gaps per rung (included minus excluded, mean over draws and sequences)")
    if d["delta_gaps"]:
        df = pd.DataFrame(d["delta_gaps"]); df.to_csv(out_dir / "delta_gaps.csv", index=False)
        L.append(_md(df))
    L.append("")
    L.append("### E8: hard-zero damage at least soft-erase damage on the same sequences")
    if d["E8"]:
        df = pd.DataFrame(d["E8"]); df.to_csv(out_dir / "E8.csv", index=False)
        L.append(_md(df))
    L.append("")
    L.append("### The donor-side pass (excess over the rounded reference on the donor sequences)")
    L.append("; ".join(f"{k.split('/', 2)[-1]}: {v['excess_over_rounded']['mean']:+.4f} (se {v['excess_over_rounded']['se']:.4f})" for k, v in d["donor_side"].items()) or "none")
    L.append("")
    L.append("### The domain comparisons per stratum: the erase against its own control, paired on the sequence with the stratum's resample; never averaged over strata")
    if d["domain"]:
        df = pd.DataFrame(d["domain"]); df.to_csv(out_dir / "domain.csv", index=False)
        L.append(_md(df))
    L.append("")
    L.append("Comparison 3, within other at rung 7: StackExchange and ArXiv against Pile-CC and Wikipedia, unpaired, with the conditional damage beside:")
    if isinstance(d.get("domain_3"), list):
        df = pd.DataFrame(d["domain_3"]); df.to_csv(out_dir / "domain_3.csv", index=False)
        L.append(_md(df))
    else:
        L.append(str(d.get("domain_3")))
    L.append("")
    L.append("### Soft erases and the rounded-own-g union (descriptive, the union machinery)")
    for lab, entry in ctx["union"].items():
        if entry["result"]["descriptive_only"]:
            union_table(entry).to_csv(out_dir / f"{lab.replace('/', '_')}.csv", index=False)
            r = entry["result"]
            L.append(f"- `{lab}`: rung 0 {r['rung_0_mean']:.4f}; excess per rung " + ", ".join(f"{rg} {r['per_rung'][rg]['e_hat']:+.4f}" for rg in r["rungs"]))
    L.append("")
    if ctx.get("comparison") is not None:
        env.assert_no_absolute_path(ctx["comparison"], "report.md, the comparison with the other run")
        _append_comparison(L, out_dir, ctx["comparison"])
    path = out_dir / "report.md"
    with open(path, "w") as f:
        f.write("\n".join(L) + "\n")
    return path


# ----------------------------------------------------------------------------- the command


def analyze(root: Path, out_dir: Path, *, frozen: str | None = None, pre_reads_dir: Path | None = None, verify_dir: Path | None = None, replicates: int = st.N_REPLICATES,
            master_seed: int = 0, tiers: tuple[int, ...] | None = None, compare_with: Path | None = None, compare_pre_reads_dir: Path | None = None, log: Any = print,
            extra_roots: tuple[Path, ...] = ()) -> dict[str, Any]:
    from vpd_audit import analysis_s7

    t0 = time.time()
    grid_all = load_grid(root, frozen=frozen, extra_roots=tuple(extra_roots))
    # tier 4 is read by analysis_s7 under its own rules and never reaches the chains below, so every table of
    # tiers 1 to 3 comes out as it did; without a tier-4 cell and without --tiers the grid is the loaded one, as before
    grid = grid_all
    if tiers is not None:
        grid = restrict_tiers(grid_all, tuple(t for t in tiers if t != analysis_s7.TIER_4))
    elif analysis_s7.has_tier_4(grid_all):
        grid = restrict_tiers(grid_all, (1, 2, 3))
    log(f"[analyze] {grid.run}: {len(grid.stores)} stores, sets {list(grid.sets)}; references bitwise across stores: pass")
    ctx: dict[str, Any] = {"replicates": replicates, "master_seed": master_seed, "blindness": check_blindness(grid.stores, frozen), "grid_reference_assert": {k: {"n_stores": v["n_stores"], "pass": all(c["pass"] for c in v["checks"])} for k, v in grid.reference_assert.items()}}
    ctx["verify_canary"] = assert_verify_canary(grid, verify_dir) if verify_dir else {"available": False}
    pre = load_pre_reads(pre_reads_dir) if pre_reads_dir else None
    ctx["pre_reads_assert"] = assert_pre_reads(grid, pre) if pre else {"available": False}
    log(f"[analyze] pre-reads assert: {ctx['pre_reads_assert']}")
    ctx["two_path"] = {s: two_path_recompute(sd) for s, sd in grid.sets.items() if sd.eval_set != "donors"}
    assert all(v["pass"] for v in ctx["two_path"].values()), f"the two-path recompute failed: {ctx['two_path']}"
    log("[analyze] two-path recompute: pass")
    strata = load_strata(grid)
    chains_by_set = {s: build_chains(sd) for s, sd in grid.sets.items()}
    descriptive_by_set = {s: build_chains(sd, descriptive=True) for s, sd in grid.sets.items()}  # rungs 2a, 2b, outside the rules
    ctx["chain_completeness"] = assert_chain_completeness(grid, chains_by_set, descriptive_by_set)
    log(f"[analyze] chain completeness: " + "; ".join(f"{k}: {v['n_cells']} cells ({v['rule']} rule, {v['descriptive_family']} descriptive family, {v['descriptive_rung']} descriptive rung)" for k, v in ctx["chain_completeness"].items() if v["n_cells"]))
    resamples: dict = {}
    union_all: dict[str, Any] = {}
    hz_all: dict[str, Any] = {}
    for s in grid.sets:
        union_all.update(analyze_union_chains(grid, chains_by_set[s], resamples, replicates, master_seed, strata, descriptive=descriptive_by_set[s]))
        hz_all.update(analyze_hard_zero_chains(grid, chains_by_set[s], strata, pre, resamples, replicates, master_seed))
    ctx["union"], ctx["hard_zero"] = union_all, hz_all
    ctx["preconditions"] = preconditions(grid, chains_by_set, hz_all, strata, descriptive_chains=descriptive_by_set)
    ctx["descriptives"] = analyze_descriptives(grid, union_all, hz_all, chains_by_set, pre, resamples, replicates, master_seed, strata)
    ctx["sanity"] = sanity_checks(grid, union_all, hz_all, chains_by_set)
    ctx["overlap_by_rung"] = pre.overlap.groupby("rung")["fraction_total"].mean().to_dict() if pre is not None else {}  # the pre-reads' measured union-against-control overlap
    ctx["overlap_by_union_chain"] = {}
    if pre is not None and (pre.dir / "control_overlap.csv").is_file():
        ov = pd.read_csv(pre.dir / "control_overlap.csv", dtype={"rung": str})
        ov = ov[(ov["family"] == "union") & (ov["control"] == "plain")]
        for (es, pool, tau, delta), g in ov.groupby(["eval_set", "pool", "tau", "delta"]):
            ctx["overlap_by_union_chain"][(es, pool, float(tau), delta)] = g.groupby("rung")["fraction_of_named"].mean().to_dict()
    ctx["comparison"] = (compare_with_other_run(grid, ctx, Path(compare_with), frozen=frozen, tiers=tiers, other_pre_dir=compare_pre_reads_dir, resamples=resamples, replicates=replicates,
                                                master_seed=master_seed, log=log) if compare_with is not None else None)
    path = write_report(out_dir, grid, ctx)
    # the report's section 9 (analysis_s7), appended after the earlier sections, its tables beside theirs
    ctx["s7"] = analysis_s7.analyze_s7(grid_all, grid, pre_reads_dir, strata, resamples, replicates, master_seed, out_dir, log=log)
    with open(path, "a") as f:
        f.write("\n".join(ctx["s7"]["report_lines"]) + "\n")
    try:
        from vpd_audit.figures import draw_all

        ctx["figures"] = draw_all(out_dir, ctx, grid)
    except Exception as e:  # noqa: BLE001
        ctx["figures"] = {"error": f"{type(e).__name__}: {e}"}
        log(f"[analyze] figures failed: {ctx['figures']['error']}")
    summary = {"run": grid.run, "seconds": time.time() - t0, "report": path.name, "n_union_chains": len(union_all), "n_hard_zero_chains": len(hz_all),
               "preconditions": {"P1": (ctx["preconditions"]["P1"]["n_pass"], ctx["preconditions"]["P1"]["n"]), "P3": ctx["preconditions"]["P3"]["pass"], "P4": (ctx["preconditions"]["P4"]["n_pass"], ctx["preconditions"]["P4"]["n"]),
                                 "P5": {k: v["pass"] for k, v in ctx["preconditions"]["P5"].items()}},
               "labels": {lab: e["result"]["label"] for lab, e in union_all.items() if e["chain"].family == "union" and e["chain"].control == "none"}, "sanity": [(c["id"], c["pass"]) for c in ctx["sanity"]],
               "two_path": {s: (v["n_cells"], v["max_ratio"], v["pass"]) for s, v in ctx["two_path"].items()}, "figures": ctx["figures"],
               "comparison": ({t: v.get("available") for t, v in ctx["comparison"]["rung_by_rung"].items()} if ctx["comparison"] else None), "s7": analysis_s7.summary_of(ctx["s7"])}
    env.assert_no_absolute_path(summary, "summary.json")
    with open(out_dir / "summary.json", "w") as f:
        json.dump(summary, f, indent=2, default=str)
    log(f"[analyze] report written to {path} in {summary['seconds']:.0f} s")
    return summary
