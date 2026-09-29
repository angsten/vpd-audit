"""The two-path check of the conditional damage.

`run_cells` computes d_b(tau_q) = (1/t*) sum_{t < t*} [KL_cell - KL_ref] in float32 from the float32 per-position
divergences it holds (cells.conditional_damage) and stores it as the columns d_0.1 and d_0. This check recomputes it a
second way, from the float16 per-position arrays on disk (kl/<cell>.npy and the reference's), using the stored t_star
columns, and compares. The two paths share nothing but t*, so an off-by-one in the prefix (t < t* against t <= t*) in
either would show, which a single path cannot catch.

Tolerance, per sequence, read off the arrays themselves: a float16 value carries a 10-bit fraction, so rounding to
nearest moves it by at most half its spacing, at most 2^-11 relative (values below 6e-5 are subnormal with an absolute
error below 3e-8, covered by the floor). A prefix mean of rounded values therefore errs by at most 2^-11 times the mean
of the true values, at most 2^-11 times their maximum, once for the cell and once for the reference:

    bound_b = 2^-11 (max_{t < t*} KL_cell + max_{t < t*} KL_ref) + 1e-6,

the floor covering the float32 arithmetic of the column path. The check reports the largest ratio of discrepancy to
bound over every hard-zero cell and sequence (it must be at most 1), the number of cells and (cell, sequence, tau_q)
checks, and that d is NaN exactly where t* = 0. On the stand-in, whose positions sit at 4 to 16 nats, a fixed tolerance
would fail spuriously, which is why the bound is computed rather than fixed; on the paper's model the hard-zero rung 8
sits at tens of nats with a float16 spacing of 0.03 to 0.06. Nothing here prints or returns a divergence value: only
ratios, counts, and names.
"""

from __future__ import annotations

import dataclasses

import json
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from vpd_audit.cells import HARD_ZERO_FAMILIES, Cell, reference_for

FLOAT16_HALF_SPACING_REL = 2.0 ** -11
ABS_FLOOR = 1e-6
# the maxima in the bound are read from the rounded arrays, so the bound undershoots the one
# on the true values by a factor 1 - 2^-11; the factor below restores it with margin, so that a ratio above 1 on the
# paper's model is a defect to chase, never rounding.
BOUND_SAFETY = 1.0 + 2.0 ** -10
CELL_FIELDS = tuple(f.name for f in dataclasses.fields(Cell))
# the fields with a default in the dataclass (condition, optional, donor_side_reference, level, descriptive, rank_key, rank_end, replicate): a
# store written before one existed, or a table joined from such a store (NaN), loads it as the default; every other field must be
# present and not NaN, except donor_pool and tau, which are None on a reference cell by construction
_FIELD_DEFAULTS = {f.name: f.default for f in dataclasses.fields(Cell) if f.default is not dataclasses.MISSING}
OPTIONAL_FIELDS = tuple(_FIELD_DEFAULTS)
_NULLABLE_REQUIRED = ("donor_pool", "tau")


def _is_null(v: Any) -> bool:
    return v is None or (isinstance(v, float) and np.isnan(v))


def _cell_from_row(row: pd.Series) -> Cell:
    kw: dict[str, Any] = {}
    for f in dataclasses.fields(Cell):
        name = f.name
        missing = name not in row.index
        v = None if missing else row[name]
        if name in _FIELD_DEFAULTS:
            if missing or _is_null(v):
                kw[name] = _FIELD_DEFAULTS[name]
                continue
        elif name in _NULLABLE_REQUIRED:
            assert not missing, f"cells table without the column {name!r}"
            if _is_null(v):
                kw[name] = None
                continue
        else:
            assert not missing and not _is_null(v), f"cell {row.get('cell', '?')!r}: the field {name!r} is {'missing' if missing else 'NaN'} and has no default"
        if name == "tau" or name == "level" or name == "own_round":  # own_round: NaN in a joined table is its default, above
            v = float(v)
        elif name in ("draw", "tier", "replicate", "shift"):  # shift: a table joined with stores that lack the column reads it as a float
            v = int(v)
        elif name in ("optional", "descriptive"):
            v = bool(v)
        elif isinstance(v, (np.generic,)):
            v = v.item()
        kw[name] = v
    return Cell(**kw)


def _array(store: Path, cell: str, cache: dict[str, np.ndarray]) -> np.ndarray:
    if cell not in cache:
        p = store / "kl" / f"{cell.replace('/', '__')}.npy"
        arr = np.load(p)
        assert arr.dtype == np.float16, (cell, arr.dtype)
        cache[cell] = arr.astype(np.float64)
    return cache[cell]


def check_store(store: Path) -> dict[str, Any]:
    """The check on one run_cells store directory; returns ratios, counts, and names only."""
    store = Path(store)
    ct = pd.read_parquet(store / "cells.parquet")
    rows = pd.read_parquet(store / "per_sequence.parquet")
    hz = ct[ct["family"].isin(HARD_ZERO_FAMILIES)]
    out: dict[str, Any] = {"n_cells_checked": 0, "n_sequence_checks": 0, "n_nan_checks": 0, "n_over_bound": 0, "n_nonfinite": 0, "n_nan_mismatch": 0, "max_ratio": 0.0,
                           "max_ratio_at": None, "nonfinite_at": None, "missing_columns": [], "missing_reference": []}
    needed = {"t_star_0.1", "t_star_0", "d_0.1", "d_0"}
    if not needed <= set(rows.columns):
        out["missing_columns"] = sorted(needed - set(rows.columns))
        return out
    arrays: dict[str, np.ndarray] = {}
    for _, crow in hz.iterrows():
        c = _cell_from_row(crow)
        ref = reference_for(c)
        ref_name = f"{c.run}/{c.eval_set}/ref/{ref}"
        if ref_name not in set(ct["cell"]):
            out["missing_reference"].append(c.name)
            continue
        A = _array(store, c.name, arrays)
        R = _array(store, ref_name, arrays)
        sub = rows[rows["cell"] == c.name].sort_values("seq")
        seqs = sub["seq"].to_numpy(dtype=np.int64)
        assert seqs.size and A.shape[0] > seqs.max(), (c.name, A.shape, seqs.max())
        diff_cs = np.cumsum(A[seqs] - R[seqs], axis=1)  # (n, T): sum over t <= j
        max_a = np.maximum.accumulate(A[seqs], axis=1)
        max_r = np.maximum.accumulate(R[seqs], axis=1)
        out["n_cells_checked"] += 1
        for tag in ("0.1", "0"):
            t_star = sub[f"t_star_{tag}"].to_numpy(dtype=np.int64)
            d_col = sub[f"d_{tag}"].to_numpy(dtype=np.float64)
            nan_ok = np.isnan(d_col) == (t_star == 0)
            out["n_nan_mismatch"] += int((~nan_ok).sum())
            out["n_nan_checks"] += int((t_star == 0).sum())
            pos = np.flatnonzero(t_star > 0)
            if pos.size == 0:
                continue
            j = t_star[pos] - 1  # the last prefix position
            d_re = diff_cs[pos, j] / t_star[pos]
            bound = (FLOAT16_HALF_SPACING_REL * (max_a[pos, j] + max_r[pos, j]) + ABS_FLOOR) * BOUND_SAFETY
            with np.errstate(invalid="ignore", divide="ignore"):
                ratio = np.abs(d_col[pos] - d_re) / bound
            # a NaN or inf anywhere (an array, a column, a bound) gives a non-finite ratio, which a
            # plain `ratio > 1` and the maximum both let pass; a non-finite ratio counts as over the bound
            finite = np.isfinite(ratio)
            out["n_sequence_checks"] += int(pos.size)
            out["n_nonfinite"] += int((~finite).sum())
            out["n_over_bound"] += int(((~finite) | (ratio > 1.0)).sum())
            if not finite.all() and out["nonfinite_at"] is None:
                k = int(np.flatnonzero(~finite)[0])
                out["nonfinite_at"] = {"cell": c.name, "seq": int(seqs[pos[k]]), "tau_q": tag, "t_star": int(t_star[pos[k]])}
            if finite.any():
                k = int(np.argmax(np.where(finite, ratio, -1.0)))
                if float(ratio[k]) > out["max_ratio"]:
                    out["max_ratio"] = float(ratio[k])
                    out["max_ratio_at"] = {"cell": c.name, "seq": int(seqs[pos[k]]), "tau_q": tag, "t_star": int(t_star[pos[k]])}
    out["pass"] = bool(out["n_over_bound"] == 0 and out["n_nonfinite"] == 0 and out["n_nan_mismatch"] == 0 and not out["missing_reference"] and out["n_cells_checked"] == len(hz))
    return out


def check_d_b_two_paths(out_dir: Path, *, update_summary: bool = True, log: Any = print, summary_stem: str = "summary", only_stores: list[str] | None = None) -> dict[str, Any]:
    """The check over every store under `out_dir` (a grid's group directories, or `out_dir` itself when it is a store),
    combined; written into out_dir/<summary_stem>.json under "d_b_two_paths" and appended to <summary_stem>.md when they
    exist. `only_stores` restricts the check to the named group directories: a subset launch
    into tier 3 checks its own stores, not every earlier subset's beside them."""
    out_dir = Path(out_dir)
    stores = [out_dir] if (out_dir / "cells.parquet").is_file() else sorted(p.parent for p in out_dir.glob("*/cells.parquet"))
    if only_stores is not None:
        stores = [s for s in stores if s.name in only_stores]
    combined: dict[str, Any] = {"n_cells_checked": 0, "n_sequence_checks": 0, "n_nan_checks": 0, "n_over_bound": 0, "n_nonfinite": 0, "n_nan_mismatch": 0, "max_ratio": 0.0,
                                "max_ratio_at": None, "stores": {},
                                "bound": "(2^-11 (max_{t<t*} KL_cell + max_{t<t*} KL_ref) + 1e-6) (1 + 2^-10) per sequence, the maxima from the float16 arrays; a non-finite ratio counts as over"}
    for s in stores:
        r = check_store(s)
        combined["stores"][s.name] = r
        for k in ("n_cells_checked", "n_sequence_checks", "n_nan_checks", "n_over_bound", "n_nonfinite", "n_nan_mismatch"):
            combined[k] += r[k]
        if r["max_ratio"] > combined["max_ratio"]:
            combined["max_ratio"] = r["max_ratio"]
            combined["max_ratio_at"] = {"store": s.name, **(r["max_ratio_at"] or {})}
    combined["pass"] = bool(stores) and all(r.get("pass", False) for r in combined["stores"].values())
    log(f"[two-paths] {combined['n_cells_checked']} hard-zero cells over {len(stores)} stores, {combined['n_sequence_checks']} (cell, sequence, tau_q) checks with t* > 0 and "
        f"{combined['n_nan_checks']} with t* = 0; largest |column - recomputed| / bound = {combined['max_ratio']:.4f} (must be <= 1); over the bound {combined['n_over_bound']} "
        f"(non-finite {combined['n_nonfinite']}), NaN mismatches {combined['n_nan_mismatch']} -> {'pass' if combined['pass'] else 'FAIL'}")
    if update_summary and (out_dir / f"{summary_stem}.json").is_file():
        with open(out_dir / f"{summary_stem}.json") as f:
            summary = json.load(f)
        summary["d_b_two_paths"] = combined
        with open(out_dir / f"{summary_stem}.json", "w") as f:
            json.dump(summary, f, indent=2, sort_keys=True, default=str)
        if (out_dir / f"{summary_stem}.md").is_file():
            from vpd_audit.grid import format_summary

            with open(out_dir / f"{summary_stem}.md", "w") as f:
                f.write(format_summary(summary) + "\n")
    return combined
