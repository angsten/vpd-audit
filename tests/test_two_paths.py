"""The two-path check of the conditional damage on a synthetic store. The column path (float32,
cells.conditional_damage) and the array path (float16 arrays on disk) agree within the per-sequence float16 bound on a
store whose positions sit at up to 20 nats (the stand-in's regime); NaN exactly where t* = 0; and a t <= t* off-by-one
planted in the columns is caught, as is a wrong reference."""

from dataclasses import asdict

import numpy as np
import pandas as pd
import pytest
import torch

from vpd_audit.cells import Cell, conditional_damage
from vpd_audit.reference import CONDITION_BY_NAME
from vpd_audit.two_paths import check_d_b_two_paths, check_store

T, N = 512, 40


def _store(tmp_path, *, off_by_one: bool = False, wrong_ref: bool = False):
    rng = np.random.default_rng(3)
    cells = [Cell("main", "hard_zero", "E", "D_unif", 0.1, "ones", "included", 0, "4", "none", 1),
             Cell("main", "hard_zero", "E", "D_unif", 0.1, "ones", "excluded", 0, "4", "none", 3),
             Cell("main", "never_named_hard", "E", "D_unif", 0.1, "ones", "included", 1, "B50", "none", 3),
             Cell("main", "union", "E", "D_unif", 0.1, "r0", "excluded", 0, "4", "none", 1)]
    refs = [Cell("main", "reference", "E", None, None, "none", CONDITION_BY_NAME[n].delta, 0, "0", "none", 1, condition=n) for n in ("target", "unmasked", "unmasked_delta")]
    d = tmp_path / "E"
    (d / "kl").mkdir(parents=True)
    kl = {}
    for c in cells + refs:
        scale = 1e-3 if c.family == "reference" else 20.0
        arr = (rng.random((N, T), dtype=np.float32) * scale).astype(np.float32)
        if c.family == "reference" and c.condition == "target":
            arr[:] = 0.0
        kl[c.name] = arr
        np.save(d / "kl" / f"{c.name.replace('/', '__')}.npy", arr.astype(np.float16))
    rows = []
    for c in cells + refs:
        for b in range(N):
            row = {"cell": c.name, "seq": b, "kl_mean": float(kl[c.name][b].mean())}
            for tag in ("0.1", "0"):
                row[f"t_star_{tag}"] = -1
                row[f"d_{tag}"] = float("nan")
            rows.append(row)
    df = pd.DataFrame(rows)
    for c in cells:
        if not c.is_hard_zero:
            continue
        ref = "unmasked_delta" if c.delta == "included" else "unmasked"
        if wrong_ref:
            ref = "unmasked" if ref == "unmasked_delta" else "unmasked_delta"
        r_arr = torch.from_numpy(kl[f"main/E/ref/{ref}"])
        for tag, t_star in (("0.1", rng.integers(0, T + 1, size=N)), ("0", rng.integers(0, 12, size=N))):
            t_star = t_star.astype(np.int64)
            t_star[:3] = [0, 1, T]  # touched at 0 (NaN), a one-position prefix, never touched
            t_used = np.minimum(t_star + 1, T) if off_by_one else t_star
            _, dd = conditional_damage(torch.from_numpy(kl[c.name]), r_arr, torch.from_numpy(t_used))
            dd = dd.numpy()
            if off_by_one:
                dd[t_star == 0] = np.nan  # keep the NaN rule so only the prefix is wrong
            sel = df["cell"] == c.name
            df.loc[sel, f"t_star_{tag}"] = t_star
            df.loc[sel, f"d_{tag}"] = dd
    df.to_parquet(d / "per_sequence.parquet", index=False)
    pd.DataFrame([{**asdict(c), "cell": c.name} for c in cells + refs]).to_parquet(d / "cells.parquet", index=False)
    return d


def test_two_paths_agree_within_the_float16_bound_and_nan_where_t_star_is_zero(tmp_path):
    d = _store(tmp_path)
    r = check_store(d)
    assert r["pass"] and r["n_cells_checked"] == 3 and r["max_ratio"] <= 1.0 and r["n_over_bound"] == 0 and r["n_nan_mismatch"] == 0
    assert r["n_sequence_checks"] + r["n_nan_checks"] == 3 * 2 * N and r["n_nan_checks"] >= 3 * 2 and r["max_ratio_at"]["cell"].startswith("main/E/")
    # the combined check over a grid directory and its summary
    (tmp_path / "summary.json").write_text('{"config": {"run": "main"}}')
    out = check_d_b_two_paths(tmp_path, log=lambda *_: None)
    assert out["pass"] and out["n_cells_checked"] == 3 and set(out["stores"]) == {"E"}
    import json

    assert json.loads((tmp_path / "summary.json").read_text())["d_b_two_paths"]["max_ratio"] == out["max_ratio"]


def test_two_paths_catch_an_off_by_one_prefix_and_a_wrong_reference(tmp_path):
    r = check_store(_store(tmp_path / "a", off_by_one=True))
    assert not r["pass"] and r["n_over_bound"] > 0 and r["max_ratio"] > 1.0
    r2 = check_store(_store(tmp_path / "b", wrong_ref=True))
    assert not r2["pass"] and r2["n_over_bound"] > 0


def test_two_paths_report_missing_columns_rather_than_fail(tmp_path):
    d = _store(tmp_path)
    df = pd.read_parquet(d / "per_sequence.parquet").drop(columns=["d_0"])
    df.to_parquet(d / "per_sequence.parquet", index=False)
    r = check_store(d)
    assert r["missing_columns"] == ["d_0"] and r["n_cells_checked"] == 0 and not r.get("pass", False)
