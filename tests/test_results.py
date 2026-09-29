"""The results check A14: the results schema round-trips, duplicate keys
are rejected, and resume skips completed sub-batches and reproduces an interrupted one bitwise."""

import numpy as np
import pandas as pd
import pytest

from vpd_audit.results import SubbatchStore, rows_to_frame

N_SEQ, SEQ_LEN, SUBBATCH = 5, 7, 2
CELLS = ["alpha", "beta/k0", "beta/k1"]


def _rows_and_arrays(i: int, sl: slice, seed: int = 0):
    """A deterministic stand-in for a sub-batch's computation, keyed by (seed, sub-batch)."""
    rng = np.random.default_rng([seed, i])
    rows, arrays = [], {}
    for cell in CELLS:
        arr = rng.random((sl.stop - sl.start, SEQ_LEN), dtype=np.float32)
        arrays[cell] = arr
        for j, seq in enumerate(range(sl.start, sl.stop)):
            rows.append({"cell": cell, "condition": cell.split("/")[0], "draw": int(cell[-1]) if "/" in cell else 0, "seq": seq,
                         "kl_mean": float(arr[j].mean()), "kl_max": float(arr[j].max()), "kl_argmax": int(arr[j].argmax()),
                         "ce": float(rng.random()), "ce_target": float(rng.random()), "mask_fp": f"{seed:04x}{i:04x}{abs(hash(cell)) % (1 << 32):08x}", "delta": "excluded",
                         "precision": "fp32", "min_gap": 0.0, "n_below_label": 0})
    return rows, arrays


def _run(out_dir, crash_after: int | None = None) -> tuple[SubbatchStore, list[int]]:
    store = SubbatchStore(out_dir, n_sequences=N_SEQ, cells=CELLS, subbatch=SUBBATCH, seq_len=SEQ_LEN)
    done = store.resume()
    computed = []
    for i in range(done + 1, store.n_subbatches):
        sl = store.subbatch_slice(i)
        rows, arrays = _rows_and_arrays(i, sl)
        store.add_rows(rows)
        for cell, arr in arrays.items():
            store.set_positions(cell, sl, arr)
        store.extra["seen"] = store.extra.get("seen", 0) + 1
        store.checkpoint(i)
        computed.append(i)
        if crash_after is not None and i == crash_after:
            break
    return store, computed


def test_a14_round_trip(tmp_path):
    store, computed = _run(tmp_path / "a")
    assert computed == [0, 1, 2] and store.n_subbatches == 3
    again = SubbatchStore(tmp_path / "a", n_sequences=N_SEQ, cells=CELLS, subbatch=SUBBATCH, seq_len=SEQ_LEN)
    assert again.resume() == 2
    assert again.table().equals(store.table())
    for cell in CELLS:
        assert np.array_equal(again.arrays[cell], store.arrays[cell], equal_nan=True)
        assert again.arrays[cell].dtype == np.float16 and not np.isnan(again.arrays[cell]).any()
    df = again.table()
    assert len(df) == len(CELLS) * N_SEQ and df["kl_mean"].dtype == np.float32 and df["seq"].dtype == np.int64
    assert again.extra["seen"] == 3


def test_a14_duplicate_keys_rejected(tmp_path):
    store = SubbatchStore(tmp_path / "d", n_sequences=N_SEQ, cells=CELLS, subbatch=SUBBATCH, seq_len=SEQ_LEN)
    rows, _ = _rows_and_arrays(0, slice(0, 2))
    store.add_rows(rows)
    with pytest.raises(ValueError, match="duplicate"):
        store.add_rows(rows[:1])
    with pytest.raises(AssertionError):
        store.add_rows([{**rows[0], "cell": "unknown", "seq": 99}])
    with pytest.raises(AssertionError):
        store.checkpoint(1)  # out of order


def test_a14_resume_skips_completed_and_reproduces_bitwise(tmp_path):
    full, _ = _run(tmp_path / "full")
    partial, computed = _run(tmp_path / "partial", crash_after=1)
    assert computed == [0, 1]
    resumed, computed2 = _run(tmp_path / "partial")
    assert computed2 == [2]  # completed sub-batches skipped
    assert resumed.table().equals(full.table())
    for cell in CELLS:
        assert np.array_equal(resumed.arrays[cell], full.arrays[cell], equal_nan=True)
    assert resumed.extra["seen"] == 3
    # a stale temporary file from an interrupted rename never replaces a checkpointed file
    (tmp_path / "partial" / "per_sequence.parquet.tmp").write_bytes(b"garbage")
    again = SubbatchStore(tmp_path / "partial", n_sequences=N_SEQ, cells=CELLS, subbatch=SUBBATCH, seq_len=SEQ_LEN)
    assert again.resume() == 2 and again.table().equals(full.table())


def test_rows_to_frame_empty_has_schema():
    df = rows_to_frame([])
    assert isinstance(df, pd.DataFrame) and "kl_mean" in df.columns and len(df) == 0


# --------------------------------------------------------------------------- provenance


def test_marker_wall_clock_and_resume_keep_started_at(tmp_path):
    import json
    import time

    store, _ = _run(tmp_path / "wc", crash_after=1)
    m1 = json.loads((tmp_path / "wc" / "marker.json").read_text())
    assert m1["started_at"] and m1["finished_at"] and m1["wall_clock_s"] >= 0 and len(m1["sessions"]) == 1
    time.sleep(1.1)
    _run(tmp_path / "wc")  # resume: started_at is kept, finished_at moves, a second session is recorded
    m2 = json.loads((tmp_path / "wc" / "marker.json").read_text())
    assert m2["started_at"] == m1["started_at"] and m2["finished_at"] >= m1["finished_at"] and m2["wall_clock_s"] >= 1.0 and len(m2["sessions"]) == 2


def test_code_commits_carry_the_dirty_flag_and_manifest_finished_at(tmp_path):
    from vpd_audit.results import RunManifest, code_commits, dirty_tree_flag

    c = code_commits()
    assert set(c) >= {"project", "submodule", "dirty"} and c["dirty"] in ("0", "1", "unknown")
    assert dirty_tree_flag() == c["dirty"]
    m = RunManifest(job="j", run="main", checkpoint_hashes={}, set_name="E", set_hash="x", n_sequences=1, precision="fp32", g_dtype="torch.float32",
                    subbatch=1, importance_chunk=1, master_seed=0, n_draws=1, device="cpu", gpu_name=None, torch_version="t", commits=c)
    assert m.finished_at is None
    m.save(tmp_path / "m.json")
    assert RunManifest.load(tmp_path / "m.json").finished_at is None
    m.mark_finished(tmp_path / "m.json")
    assert RunManifest.load(tmp_path / "m.json").finished_at is not None
