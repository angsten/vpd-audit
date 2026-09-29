"""The grid loop on the SimpleStories stand-in, on CPU in float32, with the local artifacts and dry sets: the references run
first and the hard-zero columns (the clean-prefix sums and the conditional damage) are filled from the held rung-0 divergence; A14 rerun on the real loop, a job interrupted after
sub-batch 2 and resumed must give the tables of an uninterrupted run bitwise, the new columns and the held reference state included; and a store with a hard-zero cell
but without its rung 0 is refused. Skipped when the artifacts or the dry sets are not in the local cache."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
import pytest
import torch

from vpd_audit import env
from vpd_audit.cells import Cell, build_sources, run_cells
from vpd_audit.reference import CONDITION_BY_NAME
from vpd_audit.sources import Cache, source_hash

RUN, SET, POOL = "simplestories", "E_dry", "D_unif_dry"
N_SEQ, SUBBATCH = 24, 8  # three sub-batches, so an interruption after the second leaves one to resume


def _have_local_artifacts() -> bool:
    from vpd_audit.artifacts import AUDIT_RUNS, decomp_checkpoint_path

    try:
        spec = AUDIT_RUNS[RUN]
        return decomp_checkpoint_path(RUN).is_file() and (env.SETS_DIR / f"{SET}.npz").is_file() and (env.CACHE_DIR / "donors" / f"{POOL}_{RUN}.npz").is_file() \
            and (env.CACHE_DIR / "donors" / f"D_code_dry_{RUN}.npz").is_file() and (env.CACHE_DIR / "donors" / f"prose_named_f_code_dry_{RUN}.json").is_file() \
            and (env.ARTIFACTS_DIR / spec.target_run).is_dir()
    except Exception:
        return False


def _ref(cond: str, k: int = 0) -> Cell:
    return Cell(RUN, "reference", "E", None, None, "none", CONDITION_BY_NAME[cond].delta, k, "0", "none", 1, condition=cond)


def _cells_with_references() -> list[Cell]:
    return [
        Cell(RUN, "hard_zero", "E", "D_unif", 0.1, "ones", "included", 0, "4", "none", 1),
        Cell(RUN, "hard_zero", "E", "D_unif", 0.1, "ones", "included", 0, "2", "none", 1),
        Cell(RUN, "hard_zero", "E", "D_unif", 0.1, "ones", "included", 0, "4", "plain", 2),
        Cell(RUN, "hard_zero", "E", "D_unif", 0.1, "ones", "excluded", 0, "4", "none", 3),
        # the stand-in's uniform-donor erases touch every sequence at position 0, so d_b is NaN on them; the
        # code-specific erase at rung 1 leaves every sequence of E_dry clean (the committed dry run), so d_b is finite there
        Cell(RUN, "code_specific_hard", "E", "D_code", 0.1, "ones", "included", 0, "1", "none", 3),
        Cell(RUN, "code_specific_hard", "E", "D_code", 0.1, "ones", "included", 0, "S4", "none", 3),
        # the never-named chain: a union-matched rung, a bridging rung, and the strict cell, all hard-zero cells
        Cell(RUN, "never_named_hard", "E", "D_unif", 0.1, "ones", "included", 1, "2", "none", 3),
        Cell(RUN, "never_named_hard", "E", "D_unif", 0.1, "ones", "included", 0, "B50", "none", 3),
        Cell(RUN, "never_named_hard", "E", "D_unif", 0.0, "ones", "included", 0, "8", "none", 3),
        Cell(RUN, "union", "E", "D_unif", 0.1, "r0", "excluded", 0, "4", "none", 1),
        Cell(RUN, "union", "E", "D_unif", 0.1, "uniform", "excluded", 0, "4", "none", 1),
        Cell(RUN, "soft_erase", "E", "D_unif", 0.1, "r1", "excluded", 0, "4", "none", 1),
        # the two rung-8 corners of the level cells, two level cells at s = 0.5, one ranked cell of each key, one descriptive rung
        Cell(RUN, "union", "E", "D_unif", 0.1, "r0", "excluded", 0, "8", "none", 1),
        Cell(RUN, "soft_erase", "E", "D_unif", 0.1, "r1", "excluded", 0, "8", "none", 1),
        Cell(RUN, "level", "E", "D_unif", 0.1, "r0", "excluded", 0, "8", "none", 3, level=0.5),
        Cell(RUN, "level", "E", "D_unif", 0.1, "r1", "excluded", 0, "8", "none", 3, level=0.5),
        Cell(RUN, "never_named_ranked", "E", "D_unif", 0.1, "ones", "included", 0, "2", "none", 3, rank_key="weight_norm", rank_end="top"),
        Cell(RUN, "never_named_ranked", "E", "D_unif", 0.1, "ones", "included", 0, "B50", "none", 3, rank_key="positive_count", rank_end="bottom"),
        Cell(RUN, "union", "E", "D_unif", 0.1, "r0", "excluded", 0, "2a", "none", 3, descriptive=True),
        _ref("target"), _ref("unmasked"), _ref("unmasked_delta"), _ref("importances"), _ref("stochastic", 0), _ref("stochastic_delta", 0),
    ]


@pytest.fixture(scope="module")
def loop_inputs():
    if not _have_local_artifacts():
        pytest.skip("the SimpleStories artifacts, E_dry, or the D_unif_dry cache are not in the local cache")
    from vpd_audit.artifacts import checkpoint_hashes, load_component_model
    from vpd_audit.data import load_set

    from vpd_audit.donors import load_prose_named_and_f_code

    torch.use_deterministic_algorithms(True, warn_only=True)
    model = load_component_model(RUN, "cpu")
    ids, _, rec = load_set(SET)
    caches = {f"D_unif_{RUN}": Cache.load(f"{POOL}_{RUN}"), f"D_code_{RUN}": Cache.load(f"D_code_dry_{RUN}")}
    alive_vec = np.load(env.CACHE_DIR / "donors" / f"alive_{POOL}_{RUN}.npy")
    prose_named, f_code, _ = load_prose_named_and_f_code(f"dry_{RUN}")
    module_to_c = {k: model.module_to_c[k] for k in sorted(model.module_to_c)}
    from vpd_audit.weight_norms import weight_norms

    return {"model": model, "ids": ids[:N_SEQ], "set_hash": rec["sha256_ids"], "caches": caches, "alive": {RUN: (alive_vec, source_hash(alive_vec))},
            "prose_named": {RUN: prose_named}, "f_code": {RUN: f_code}, "module_to_c": module_to_c, "hashes": checkpoint_hashes(RUN), "weight_norms": {RUN: weight_norms(model)[0]}}


def _run(inputs, cells, out_dir: Path, *, crash_after: int | None = None, resume: bool = True):
    sources = build_sources(cells, inputs["caches"], inputs["alive"], inputs["prose_named"], inputs["f_code"], inputs["module_to_c"], log=lambda *_: None, weight_norms=inputs["weight_norms"])

    def on_subbatch(i: int) -> None:
        if crash_after is not None and i == crash_after:
            raise RuntimeError(f"interrupted after sub-batch {i + 1}")

    return run_cells(inputs["model"], cells, inputs["ids"], sources, job="loop_test", run=RUN, out_dir=out_dir, precision="fp32", subbatch=SUBBATCH, set_name=SET,
                     set_hash=inputs["set_hash"], checkpoint_hashes=inputs["hashes"], importance_chunk=SUBBATCH, resume=resume, on_subbatch=on_subbatch, log=lambda *_: None)


def _tables(out_dir: Path) -> tuple[pd.DataFrame, pd.DataFrame, dict[str, np.ndarray]]:
    rows = pd.read_parquet(out_dir / "per_sequence.parquet").sort_values(["cell", "seq"]).reset_index(drop=True)
    ct = pd.read_parquet(out_dir / "cells.parquet").sort_values("cell").reset_index(drop=True)
    arrays = {p.stem: np.load(p) for p in sorted((out_dir / "kl").glob("*.npy"))}
    return rows, ct, arrays


def test_hard_zero_columns_from_the_held_reference(loop_inputs, tmp_path):
    cells = _cells_with_references()
    store = _run(loop_inputs, cells, tmp_path / "full")
    assert store.done_through == 2
    rows, ct, arrays = _tables(tmp_path / "full")
    by = rows.set_index(["cell", "seq"])
    hz = [c for c in cells if c.is_hard_zero]
    others = [c for c in cells if not c.is_hard_zero]
    for c in others:
        sub = rows[rows.cell == c.name]
        assert sub[["kl_prefix_sum_0.1", "kl_prefix_sum_0", "d_0.1", "d_0"]].isna().all().all() and (sub[["n_touched_0.1", "n_touched_0"]] == -1).all().all()
    T = arrays[next(iter(arrays))].shape[1]
    for c in hz:
        ref = f"{RUN}/E/ref/{'unmasked_delta' if c.delta == 'included' else 'unmasked'}"
        sub = rows[rows.cell == c.name].sort_values("seq")
        assert (sub["n_touched_0.1"] >= 0).all() and (sub["n_touched_0"] >= sub["n_touched_0.1"]).all() and (sub["t_star_0"] <= sub["t_star_0.1"]).all()
        for _, r in sub.iterrows():
            for tag in ("0.1", "0"):
                t_star = int(r[f"t_star_{tag}"])
                if t_star == 0:
                    assert np.isnan(r[f"d_{tag}"]) and r[f"kl_prefix_sum_{tag}"] == 0.0
                else:  # the authors' per-position arithmetic can sit a few 1e-8 below zero (test_metrics A8), so the sum may too
                    assert np.isfinite(r[f"d_{tag}"]) and r[f"kl_prefix_sum_{tag}"] >= -1e-4
                    if t_star == T:  # never touched: the difference of the two per-sequence means, to float32 rounding
                        assert r[f"d_{tag}"] == pytest.approx(float(r["kl_mean"]) - float(by.loc[(ref, int(r["seq"])), "kl_mean"]), abs=1e-5)
                        assert r[f"kl_prefix_sum_{tag}"] == pytest.approx(float(r["kl_mean"]) * T, rel=1e-5)
        # the position-level count never undercounts the prefix condition: t* < T implies at least one touched position
        assert ((sub["t_star_0.1"] == T) | (sub["n_touched_0.1"] >= 1)).all()
    # every cell's marker summed all three sub-batches, the references included
    assert (ct["n_subbatches"] == 3).all() and len(ct) == len(cells)
    # the code-specific cells have finite d_b on some sequences (the never-touched ones were checked above against the means)
    spec = rows[rows.cell.str.contains("/code_specific_hard/")]
    assert spec["d_0.1"].notna().any() and spec["d_0"].notna().any() and (spec.loc[spec["d_0.1"].notna(), "t_star_0.1"] > 0).all()
    # the two-path check on this store, the column path against the float16 arrays within the per-sequence bound
    from vpd_audit.two_paths import check_d_b_two_paths

    two = check_d_b_two_paths(tmp_path / "full", log=lambda *_: None)
    assert two["pass"] and two["n_cells_checked"] == len(hz) and two["max_ratio"] <= 1.0 and two["n_sequence_checks"] > 0 and two["n_nan_mismatch"] == 0


def test_a14_interrupt_after_subbatch_2_and_resume_is_bitwise(loop_inputs, tmp_path):
    cells = _cells_with_references()
    _run(loop_inputs, cells, tmp_path / "full")
    with pytest.raises(RuntimeError, match="interrupted after sub-batch 2"):
        _run(loop_inputs, cells, tmp_path / "partial", crash_after=1)
    marker = json.loads((tmp_path / "partial" / "marker.json").read_text())
    assert marker["done_through"] == 1 and not (tmp_path / "partial" / "cells.parquet").is_file()
    store = _run(loop_inputs, cells, tmp_path / "partial")  # resume: only the third sub-batch is computed
    assert store.done_through == 2 and len(store.sessions) == 2
    full_rows, full_ct, full_arr = _tables(tmp_path / "full")
    res_rows, res_ct, res_arr = _tables(tmp_path / "partial")
    pd.testing.assert_frame_equal(full_rows, res_rows, check_exact=True)
    pd.testing.assert_frame_equal(full_ct, res_ct, check_exact=True)
    assert set(full_arr) == set(res_arr) and all(np.array_equal(full_arr[k], res_arr[k], equal_nan=True) for k in full_arr)
    # the new columns are present and carry values on the hard-zero cells in both runs
    assert {"kl_prefix_sum_0.1", "kl_prefix_sum_0", "d_0.1", "d_0", "n_touched_0.1", "n_touched_0"} <= set(full_rows.columns)
    assert full_rows[full_rows.cell.str.contains("/code_specific_hard/")]["d_0.1"].notna().any()


def test_a_store_with_a_hard_zero_cell_needs_its_rung_0(loop_inputs, tmp_path):
    cells = [Cell(RUN, "hard_zero", "E", "D_unif", 0.1, "ones", "included", 0, "4", "none", 1), _ref("target"), _ref("unmasked")]  # unmasked_delta missing
    with pytest.raises(AssertionError, match="rung 0"):
        _run(loop_inputs, cells, tmp_path / "norefs")


def test_level_ranked_and_descriptive_cells_through_the_loop_and_the_corner_check(loop_inputs, tmp_path):
    """On the stand-in, CPU, float32: the level cells run as permitted cells (no entry below the
    label, no hard-zero columns) with sigma equal to s times (never-named at labels) or 1 - s times (at 1) the set's sigma
    from the union's and the soft erase's rung 8; the ranked cells carry the hard-zero columns and erase inside the
    never-named set; the descriptive rung is an ordinary union cell; and the corner check reproduces the four existing
    cells bitwise, the store's rows included."""
    from vpd_audit.level_check import level_corner_check
    from vpd_audit.sources import never_named_set, union_source

    cells = _cells_with_references()
    _run(loop_inputs, cells, tmp_path / "full")
    rows, ct, arrays = _tables(tmp_path / "full")
    ct = ct.set_index("cell")
    by = rows.set_index(["cell", "seq"]).sort_index()
    lv = [c for c in cells if c.family == "level"]
    u8, s8 = f"{RUN}/E/union/D_unif/tau0.1/r0/excl/k0/r8", f"{RUN}/E/soft_erase/D_unif/tau0.1/r1/excl/k0/r8"
    for c in lv:
        assert ct.loc[c.name, "n_below_label_total"] == 0 and ct.loc[c.name, "level"] == 0.5 and ct.loc[c.name, "n_on"] == ct.loc[u8, "n_on"] and ct.loc[c.name, "source_sha256"] != ct.loc[u8, "source_sha256"]
        sub = rows[rows.cell == c.name].sort_values("seq")
        assert sub[["d_0.1", "d_0", "kl_prefix_sum_0.1"]].isna().all().all() and (sub["t_star_0.1"] == -1).all()
        base = rows[rows.cell == (u8 if c.background == "r0" else s8)].sort_values("seq")["sigma"].to_numpy(np.float64)
        assert np.allclose(sub["sigma"].to_numpy(np.float64), 0.5 * base, rtol=1e-5, atol=1e-6)
        assert ct.loc[c.name, "mask_fp_cell"] not in (ct.loc[u8, "mask_fp_cell"], ct.loc[s8, "mask_fp_cell"])  # the interior differs from both corners
    assert ct.loc[lv[0].name, "mask_fp_cell"] != ct.loc[lv[1].name, "mask_fp_cell"]
    cache = loop_inputs["caches"][f"D_unif_{RUN}"]
    alive_set = union_source(cache, range(cache.n_positions), 0.1)
    S = never_named_set(alive_set)
    for c in [c for c in cells if c.family == "never_named_ranked"]:
        assert ct.loc[c.name, "rank_key"] == c.rank_key and ct.loc[c.name, "rank_end"] == c.rank_end and ct.loc[c.name, "n_on"] > 0
        sub = rows[rows.cell == c.name]
        assert (sub["t_star_0.1"] >= 0).all() and sub["kl_prefix_sum_0.1"].notna().all()
    desc = f"{RUN}/E/union/D_unif/tau0.1/r0/excl/k0/r2a"
    assert bool(ct.loc[desc, "descriptive"]) and ct.loc[desc, "n_on"] > 0 and not ct.loc[u8, "descriptive"]
    corner = level_corner_check(loop_inputs["model"], loop_inputs["ids"], alive_set, run=RUN, precision="fp32", subbatch=SUBBATCH, chunk=SUBBATCH, store_dir=tmp_path / "full", log=lambda *_: None)
    assert corner["pass"] and corner["n_sequences"] == SUBBATCH and len(corner["corners"]) == 4
    assert all(e["masks_bitwise"] and e["fingerprints_equal"] and e["kl_bitwise"] and e["store_rows_equal"] is True and e["n_below_label"] == 0 for e in corner["corners"])
    assert [e["existing_cell"].split("/", 2)[-1] for e in corner["corners"]] == ["ref/importances", "union/D_unif/tau0.1/r0/excl/k0/r8", "soft_erase/D_unif/tau0.1/r1/excl/k0/r8", "ref/unmasked"]
