"""Results: the run manifest and the resumable per-sub-batch store of a job.

Per job: a run manifest; a per-sequence long table, one row per (cell, sequence), with the
mean, maximum, and argmax divergence, the per-sequence mask fingerprint `mask_fp`, and, for
reference cells, the cross-entropy and the target's on the same sequence; one float16
per-position array per cell; all checkpointed after every sub-batch with an atomic rename and a
"done through sub-batch i" marker whose `extra` carries the per-sub-batch and per-cell digests
and the two mask counts (the grid's cell table will hold them later). A table written before
the on-device fingerprint existed carries `mask_hash` (the SHA-256) instead of `mask_fp`; its manifest has no
`fingerprint` field. Resume reads
the marker and skips completed sub-batches; the seed tuples make a resumed sub-batch bitwise
identical to the interrupted one. Duplicate (cell, sequence) keys are rejected.
"""

from __future__ import annotations

import json
import os
import subprocess
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from vpd_audit import env
from vpd_audit.constants import SEQ_LEN

ROW_DTYPES: dict[str, Any] = {
    "cell": "string",
    "condition": "string",
    "draw": "int64",
    "seq": "int64",
    "kl_mean": "float32",
    "kl_max": "float32",
    "kl_argmax": "int64",
    "ce": "float32",
    "ce_target": "float32",
    "mask_fp": "string",  # the per-sequence fingerprint phi_b as 16 hex characters (in place of the earlier SHA-256 mask_hash)
    "delta": "string",
    "precision": "string",
    "min_gap": "float32",
    "n_below_label": "int64",
    # the grid's per-sequence columns (NaN or -1 where a cell has no such quantity)
    "n_positions_below_label": "int64",
    "n_on": "int64",
    "sigma": "float32",
    "omega": "float32",
    "t_star_0.1": "int64",
    "t_star_0": "int64",
    # the clean-prefix sum of the cell's own divergence, the conditional damage d_b
    # against the chain's rung 0, and the position-level touched count, at both tau_q; NaN / -1 off the hard-zero cells
    "kl_prefix_sum_0.1": "float32",
    "kl_prefix_sum_0": "float32",
    "d_0.1": "float32",
    "d_0": "float32",
    "n_touched_0.1": "int64",
    "n_touched_0": "int64",
}
KEY_COLUMNS = ("cell", "seq")
# the per-text columns of a tier-5 store (the plain-terms extras of every cell; the reverse
# divergence, the divergence to the other comparison model, and the padded-id mass of an external-model cell). They are cast only
# where a table has them, so every earlier store's table is what it was.
EXTRA_ROW_DTYPES: dict[str, Any] = {
    "top_changed": "float32",
    "top_changed_confident": "float32",
    "p_target_top": "float32",
    "top_is_next": "float32",
    "kl_reverse_mean": "float32",
    "kl_other_mean": "float32",
    "padded_mass_mean": "float32",
    "padded_mass_max": "float32",
}


CODE_PREFIXES = ("vpd_audit/", "tests/", "third_party/")  # untracked files here are uncommitted code
CODE_FILES = ("pyproject.toml", "uv.lock", "Makefile")


def dirty_tree_flag(root: Path = env.PROJECT_ROOT) -> str:
    """The dirty-tree flag: "1" if a tracked file is modified, or an untracked file lies
    under vpd_audit/, tests/, or third_party/, or is pyproject.toml, uv.lock, or Makefile; an untracked note elsewhere
    (the project root, results/) is not uncommitted code. "unknown" when git is unavailable (on Modal the
    launcher's value arrives as the environment variable VPD_AUDIT_DIRTY)."""
    try:
        out = subprocess.run(["git", "-C", str(root), "status", "--porcelain", "--untracked-files=all"], check=True, capture_output=True, text=True).stdout
    except Exception:
        return os.environ.get("VPD_AUDIT_DIRTY", "unknown")
    for line in out.splitlines():
        if not line.strip():
            continue
        status, path = line[:2], line[3:].strip()
        if status == "??":
            if path.startswith(CODE_PREFIXES) or path in CODE_FILES:
                return "1"
            continue
        return "1"  # a tracked file modified, added, deleted, or renamed
    return "0"


def code_commits() -> dict[str, str]:
    """Project and submodule commits from git, else from the variables the Modal image sets; plus the dirty-tree flag,
    so that a launch from uncommitted code is visible in every manifest."""
    out: dict[str, str] = {}
    for name, path, var in (("project", env.PROJECT_ROOT, "VPD_AUDIT_COMMIT"), ("submodule", env.SUBMODULE_DIR, "VPD_AUDIT_SUBMODULE_COMMIT")):
        try:
            out[name] = subprocess.run(["git", "-C", str(path), "rev-parse", "HEAD"], check=True, capture_output=True, text=True).stdout.strip()
        except Exception:
            out[name] = os.environ.get(var, "unknown")
    out["dirty"] = dirty_tree_flag()
    return out


@dataclass
class RunManifest:
    job: str
    run: str
    checkpoint_hashes: dict[str, str]
    set_name: str
    set_hash: str
    n_sequences: int
    precision: str
    g_dtype: str
    subbatch: int
    importance_chunk: int
    master_seed: int
    n_draws: int
    device: str
    gpu_name: str | None
    torch_version: str
    commits: dict[str, str]
    created_at: str = field(default_factory=lambda: time.strftime("%Y-%m-%dT%H:%M:%S%z"))
    extra: dict[str, Any] = field(default_factory=dict)
    # the on-device fingerprint's description ({version, mixer, salts, slab}) once it exists; None until
    # then. A manifest without the field (written before the fingerprint existed) is read as SHA-256, the acceptance's convention.
    fingerprint: dict[str, Any] | None = None
    # written when the job's last sub-batch completes; None while the job is running or was interrupted
    finished_at: str | None = None

    def mark_finished(self, path: Path) -> None:
        self.finished_at = time.strftime("%Y-%m-%dT%H:%M:%S%z")
        self.save(path)

    def save(self, path: Path) -> None:
        _atomic_json(path, asdict(self))

    @classmethod
    def load(cls, path: Path) -> "RunManifest":
        with open(path) as f:
            return cls(**json.load(f))


def _atomic_json(path: Path, obj: Any) -> None:
    tmp = path.with_name(path.name + ".tmp")
    with open(tmp, "w") as f:
        json.dump(obj, f, indent=2, sort_keys=True, default=_json_default)
    os.replace(tmp, path)


def _json_default(o: Any) -> Any:
    if isinstance(o, (np.integer,)):
        return int(o)
    if isinstance(o, (np.floating,)):
        return float(o)
    if isinstance(o, np.ndarray):
        return o.tolist()
    raise TypeError(f"not JSON serializable: {type(o)}")


def rows_to_frame(rows: list[dict[str, Any]]) -> pd.DataFrame:
    df = pd.DataFrame(rows)
    if len(df) == 0:
        return pd.DataFrame({c: pd.Series(dtype=t) for c, t in ROW_DTYPES.items()})
    return df.astype({c: t for c, t in {**ROW_DTYPES, **EXTRA_ROW_DTYPES}.items() if c in df.columns})


class SubbatchStore:
    """Rows and per-position arrays of one job, checkpointed per sub-batch, resumable.

    `extra_arrays`: further per-sequence arrays beside kl/, name -> (the shape after the sequence
    axis, the dtype, the fill value), written to extras/<name>.npy with the same atomic rename and restored on resume. Without
    it (every store before tier 5) nothing here changes: no extras/ folder, the same marker."""

    def __init__(self, out_dir: Path, *, n_sequences: int, cells: list[str], subbatch: int, seq_len: int = SEQ_LEN,
                 extra_arrays: dict[str, tuple[tuple[int, ...], str, Any]] | None = None):
        assert len(cells) == len(set(cells)), "cells must be distinct"
        self.out_dir = Path(out_dir)
        self.out_dir.mkdir(parents=True, exist_ok=True)
        (self.out_dir / "kl").mkdir(exist_ok=True)
        self.extra_spec: dict[str, tuple[tuple[int, ...], str, Any]] = dict(extra_arrays or {})
        self.extras: dict[str, np.ndarray] = {name: np.full((int(n_sequences),) + tuple(tail), fill, dtype=np.dtype(dt)) for name, (tail, dt, fill) in self.extra_spec.items()}
        if self.extra_spec:
            (self.out_dir / "extras").mkdir(exist_ok=True)
        self.n_sequences = int(n_sequences)
        self.cells = list(cells)
        self.subbatch = int(subbatch)
        self.seq_len = int(seq_len)
        self.arrays: dict[str, np.ndarray] = {c: np.full((self.n_sequences, self.seq_len), np.nan, dtype=np.float16) for c in self.cells}
        self.rows: list[dict[str, Any]] = []
        self.keys: set[tuple[str, int]] = set()
        self.done_through = -1
        self.extra: dict[str, Any] = {}
        # wall-clock; started_at is the first checkpoint's process start, kept across resumes
        self.process_started = time.time()
        self.started_at: str | None = None
        self.started_epoch: float | None = None
        self.sessions: list[list[str]] = []  # [start, end] per process that wrote to this store

    # paths
    @property
    def table_path(self) -> Path:
        return self.out_dir / "per_sequence.parquet"

    @property
    def marker_path(self) -> Path:
        return self.out_dir / "marker.json"

    def array_path(self, cell: str) -> Path:
        return self.out_dir / "kl" / f"{cell.replace('/', '__')}.npy"

    # sub-batches
    @property
    def n_subbatches(self) -> int:
        return (self.n_sequences + self.subbatch - 1) // self.subbatch

    def subbatch_slice(self, i: int) -> slice:
        assert 0 <= i < self.n_subbatches, i
        return slice(i * self.subbatch, min((i + 1) * self.subbatch, self.n_sequences))

    # writing
    def add_rows(self, rows: list[dict[str, Any]]) -> None:
        for r in rows:
            key = (str(r["cell"]), int(r["seq"]))
            if key in self.keys:
                raise ValueError(f"duplicate (cell, seq) key {key}")
            assert r["cell"] in self.arrays, f"unknown cell {r['cell']!r}"
            self.keys.add(key)
            self.rows.append(dict(r))

    def set_positions(self, cell: str, sl: slice, arr: np.ndarray) -> None:
        assert arr.shape == (sl.stop - sl.start, self.seq_len), (arr.shape, sl)
        self.arrays[cell][sl] = arr.astype(np.float16)

    def extra_path(self, name: str) -> Path:
        return self.out_dir / "extras" / f"{name.replace('/', '__')}.npy"

    def set_extra(self, name: str, sl: slice, arr: np.ndarray) -> None:
        """Rows `sl` of a registered extra array, already in its stored dtype (no silent cast: a wrong dtype is an error)."""
        assert name in self.extras, f"unregistered extra array {name!r}"
        tail, dt, _ = self.extra_spec[name]
        assert arr.shape == (sl.stop - sl.start,) + tuple(tail) and arr.dtype == np.dtype(dt), (name, arr.shape, arr.dtype, tail, dt)
        self.extras[name][sl] = arr

    def checkpoint(self, i: int) -> None:
        """Write the table, the arrays, and the marker, each by atomic rename; marks sub-batch i done."""
        assert i == self.done_through + 1, f"sub-batches are checkpointed in order; done through {self.done_through}, got {i}"
        df = rows_to_frame(self.rows)
        tmp = self.table_path.with_name(self.table_path.name + ".tmp")
        df.to_parquet(tmp, index=False)
        os.replace(tmp, self.table_path)
        for cell, arr in self.arrays.items():
            p = self.array_path(cell)
            tmp = p.with_name(p.name + ".tmp")
            with open(tmp, "wb") as f:
                np.save(f, arr)
            os.replace(tmp, p)
        for name, arr in self.extras.items():
            p = self.extra_path(name)
            tmp = p.with_name(p.name + ".tmp")
            with open(tmp, "wb") as f:
                np.save(f, arr)
            os.replace(tmp, p)
        now = time.time()
        if self.started_at is None:
            self.started_at = time.strftime("%Y-%m-%dT%H:%M:%S%z", time.localtime(self.process_started))
            self.started_epoch = self.process_started
        stamp = time.strftime("%Y-%m-%dT%H:%M:%S%z", time.localtime(now))
        this_start = time.strftime("%Y-%m-%dT%H:%M:%S%z", time.localtime(self.process_started))
        if self.sessions and self.sessions[-1][0] == this_start:
            self.sessions[-1][1] = stamp
        else:
            self.sessions.append([this_start, stamp])
        marker = {"done_through": i, "cells": self.cells, "n_sequences": self.n_sequences,
                  "subbatch": self.subbatch, "seq_len": self.seq_len, "n_rows": len(self.rows), "extra": self.extra,
                  "started_at": self.started_at, "finished_at": stamp, "wall_clock_s": now - (self.started_epoch or now),
                  "sessions": self.sessions}
        if self.extra_spec:  # only a store with extra arrays names them; every other marker is what it was
            marker["extra_arrays"] = {name: {"tail": list(tail), "dtype": str(np.dtype(dt))} for name, (tail, dt, _) in self.extra_spec.items()}
        _atomic_json(self.marker_path, marker)
        self.done_through = i

    # reading
    def resume(self) -> int:
        """Load a previous checkpoint of this job if there is one. Returns the last completed sub-batch."""
        if not self.marker_path.is_file():
            return -1
        with open(self.marker_path) as f:
            marker = json.load(f)
        assert marker["cells"] == self.cells, "cells differ from the checkpointed job"
        assert marker["n_sequences"] == self.n_sequences and marker["subbatch"] == self.subbatch and marker["seq_len"] == self.seq_len
        df = pd.read_parquet(self.table_path)
        assert len(df) == marker["n_rows"], (len(df), marker["n_rows"])
        self.rows = df.to_dict("records")
        self.keys = {(str(r["cell"]), int(r["seq"])) for r in self.rows}
        assert len(self.keys) == len(self.rows), "duplicate keys in the checkpointed table"
        for cell in self.cells:
            arr = np.load(self.array_path(cell))
            assert arr.shape == (self.n_sequences, self.seq_len) and arr.dtype == np.float16
            self.arrays[cell] = arr
        assert sorted(marker.get("extra_arrays", {})) == sorted(self.extra_spec), "the extra arrays differ from the checkpointed job's"
        for name, (tail, dt, _) in self.extra_spec.items():
            arr = np.load(self.extra_path(name))
            assert arr.shape == (self.n_sequences,) + tuple(tail) and arr.dtype == np.dtype(dt), (name, arr.shape, arr.dtype)
            self.extras[name] = arr
        self.extra = marker.get("extra", {})
        self.started_at = marker.get("started_at")
        if self.started_at is not None:
            self.started_epoch = time.mktime(time.strptime(self.started_at[:19], "%Y-%m-%dT%H:%M:%S"))
        self.sessions = [list(x) for x in marker.get("sessions", [])]
        self.done_through = int(marker["done_through"])
        return self.done_through

    def table(self) -> pd.DataFrame:
        return rows_to_frame(self.rows)


def load_table(out_dir: Path) -> pd.DataFrame:
    return pd.read_parquet(Path(out_dir) / "per_sequence.parquet")
