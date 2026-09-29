"""The tier-5 switches on the real loop: the SimpleStories stand-in on CPU in float32, with the local artifacts and dry sets.

The tier-5 switches change no value of any cell that existed before them: the same cells run with and without `tier5` give
the same tables and per-position arrays bitwise (only `ce`, which tier 5 asks for on every cell, and the new columns differ).
The self-merge's sets from a label cache equal the on-device (g > 0.1).any(dim=1) on every sub-batch, and a wrong set stops the
run; the per-text cells' rows carry per-text counts and switched mass; the extras' per-position arrays are consistent with the
per-text columns; a canary that does not match stops the run before the sub-batch is marked done; and a job interrupted and
resumed gives the uninterrupted run's tables and extra arrays bitwise. Skipped when the artifacts are not in the local cache."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
import pytest
import torch

from vpd_audit import env, tier5
from vpd_audit.cells import Cell, build_sources, per_position_listed, run_cells
from vpd_audit.reference import CONDITION_BY_NAME
from vpd_audit.sources import Cache, source_hash

RUN, SET, POOL = "simplestories", "E_dry", "D_unif_dry"
N_SEQ, SUBBATCH = 24, 8


def _have_local_artifacts() -> bool:
    from vpd_audit.artifacts import AUDIT_RUNS, decomp_checkpoint_path

    try:
        spec = AUDIT_RUNS[RUN]
        return decomp_checkpoint_path(RUN).is_file() and (env.SETS_DIR / f"{SET}.npz").is_file() and (env.CACHE_DIR / "donors" / f"{POOL}_{RUN}.npz").is_file() \
            and (env.CACHE_DIR / "donors" / f"D_prose_dry_{RUN}.npz").is_file() and (env.ARTIFACTS_DIR / spec.target_run).is_dir()
    except Exception:
        return False


def _ref(cond: str) -> Cell:
    return Cell(RUN, "reference", "E", None, None, "none", CONDITION_BY_NAME[cond].delta, 0, "0", "none", 1, condition=cond)


REFS = [_ref("target"), _ref("unmasked"), _ref("unmasked_delta"), _ref("importances"), _ref("rounded_0.1")]
OLD_CELLS = [  # cell types that existed before tier 5, the kinds the plain_terms subset re-runs
    Cell(RUN, "union", "E", "D_unif", 0.1, "r0", "excluded", 0, "3", "none", 1),
    Cell(RUN, "union", "E", "D_unif", 0.1, "r0", "excluded", 0, "4", "none", 1),
    Cell(RUN, "union", "E", "D_unif", 0.1, "r0", "excluded", 0, "2a", "none", 3, descriptive=True),
    Cell(RUN, "union", "E", "D_unif", 0.1, "r0", "excluded", 0, "3", "plain", 2),
    Cell(RUN, "soft_erase", "E", "D_unif", 0.1, "r1", "excluded", 0, "4", "none", 1),
    Cell(RUN, "never_named_hard", "E", "D_unif", 0.1, "ones", "included", 0, "8", "none", 3),
]
NEW_CELLS = [
    Cell(RUN, "self_union", "E", "E", 0.1, "r0", "excluded", 0, "4", "none", 5),
    Cell(RUN, "partner_union", "E", "E", 0.1, "r0", "excluded", 0, "4", "none", 5, shift=1, arm="within"),
    Cell(RUN, "partner_union", "E", "E", 0.1, "r0", "excluded", 0, "4", "none", 5, shift=0, arm="within"),  # shift 0: the self-merge again, by another path
    Cell(RUN, "partner_union", "E", "D_unif", 0.1, "r0", "excluded", 0, "4", "none", 5, shift=2, arm="general"),
    Cell(RUN, "union", "E", "D_prose", 0.1, "r0", "excluded", 1, "3", "none", 5),  # D_prose as a donor pool of the union family
]


@pytest.fixture(scope="module")
def loop_inputs(tmp_path_factory):
    if not _have_local_artifacts():
        pytest.skip("the SimpleStories artifacts, E_dry, or the stand-in's caches are not in the local cache")
    from vpd_audit.artifacts import checkpoint_hashes, load_component_model
    from vpd_audit.data import load_set
    from vpd_audit.donors import build_cache
    from vpd_audit.s9_pre_reads import own_named

    torch.use_deterministic_algorithms(True, warn_only=True)
    model = load_component_model(RUN, "cpu")
    ids, _, rec = load_set(SET)
    ids = ids[:N_SEQ]
    caches = {f"D_unif_{RUN}": Cache.load(f"{POOL}_{RUN}"), f"D_prose_{RUN}": Cache.load(f"D_prose_dry_{RUN}")}
    alive_vec = np.load(env.CACHE_DIR / "donors" / f"alive_{POOL}_{RUN}.npy")
    # the evaluation set's own label cache, built as the loop will compute g: the same rows, sub-batch, chunk, and precision
    cache_dir = tmp_path_factory.mktemp("eval_cache")
    build_cache(model, ids, run=RUN, set_name="E_first24", set_hash="", checkpoint_hashes={}, precision="fp32", subbatch=SUBBATCH, chunk=SUBBATCH, out_dir=cache_dir, log=lambda *_: None)
    own = {"E": own_named(Cache.load(f"E_first24_{RUN}", cache_dir)), "D_unif": own_named(caches[f"D_unif_{RUN}"])}
    module_to_c = {k: model.module_to_c[k] for k in sorted(model.module_to_c)}
    return {"model": model, "ids": ids, "set_hash": rec["sha256_ids"], "caches": caches, "alive": {RUN: (alive_vec, source_hash(alive_vec))}, "module_to_c": module_to_c, "hashes": checkpoint_hashes(RUN),
            "inputs": tier5.Tier5Inputs(own=own)}


def _run(inputs, cells, out_dir: Path, *, store_run=None, ce_for_all=False, crash_after=None, t5_inputs=None):
    sources = build_sources(cells, inputs["caches"], inputs["alive"], None, None, inputs["module_to_c"], log=lambda *_: None, tier5_inputs={RUN: t5_inputs or inputs["inputs"]})

    def on_subbatch(i: int) -> None:
        if crash_after is not None and i == crash_after:
            raise RuntimeError(f"interrupted after sub-batch {i + 1}")

    return run_cells(inputs["model"], cells, inputs["ids"], sources, job="tier5_loop_test", run=RUN, out_dir=out_dir, precision="fp32", subbatch=SUBBATCH, set_name=SET, set_hash=inputs["set_hash"],
                     checkpoint_hashes=inputs["hashes"], importance_chunk=SUBBATCH, resume=True, on_subbatch=on_subbatch, log=lambda *_: None, ce_for_all=ce_for_all, tier5=store_run)


def _store_run(checker=None, positions=True):
    return tier5.StoreRun(listed=per_position_listed, example_positions=tier5.example_positions(N_SEQ) if positions else None, checker=checker)


OLD_COLUMNS = ["cell", "condition", "draw", "seq", "kl_mean", "kl_max", "kl_argmax", "ce_target", "mask_fp", "delta", "precision", "min_gap", "n_below_label", "n_positions_below_label", "n_on", "sigma", "omega", "t_star_0.1", "t_star_0",
               "kl_prefix_sum_0.1", "kl_prefix_sum_0", "d_0.1", "d_0", "n_touched_0.1", "n_touched_0"]


@pytest.fixture(scope="module")
def stores(loop_inputs, tmp_path_factory):
    root = tmp_path_factory.mktemp("tier5_loop")
    _run(loop_inputs, REFS + OLD_CELLS, root / "before")  # as every store ran before tier 5
    _run(loop_inputs, REFS + OLD_CELLS + NEW_CELLS, root / "tier5", store_run=_store_run(), ce_for_all=True)
    return root


def test_the_tier_5_switches_change_no_value_of_a_cell_that_existed_before(stores):
    before = pd.read_parquet(stores / "before" / "per_sequence.parquet").sort_values(["cell", "seq"]).reset_index(drop=True)
    after = pd.read_parquet(stores / "tier5" / "per_sequence.parquet")
    after = after[after["cell"].isin(set(before["cell"]))].sort_values(["cell", "seq"]).reset_index(drop=True)
    assert list(before.columns) == OLD_COLUMNS[:7] + ["ce"] + OLD_COLUMNS[7:] and len(before) == len(after) == (len(REFS) + len(OLD_CELLS)) * N_SEQ
    pd.testing.assert_frame_equal(before[OLD_COLUMNS], after[OLD_COLUMNS], check_exact=True)
    is_ref = before["cell"].str.contains("/ref/")
    assert np.array_equal(before.loc[is_ref, "ce"].to_numpy(), after.loc[is_ref, "ce"].to_numpy()) and before.loc[~is_ref, "ce"].isna().all() and after["ce"].notna().all()  # ce for every cell of a tier-5 store
    for c in REFS + OLD_CELLS:
        f = f"{c.name.replace('/', '__')}.npy"
        assert np.array_equal(np.load(stores / "before" / "kl" / f), np.load(stores / "tier5" / "kl" / f), equal_nan=True)
    cb, ca = pd.read_parquet(stores / "before" / "cells.parquet").set_index("cell"), pd.read_parquet(stores / "tier5" / "cells.parquet").set_index("cell")
    for col in ("source_sha256", "mask_fp_cell", "mask_fp_modules", "n_ne_g_modules", "n_ne_one_modules", "n_below_label_total", "n_on", "n_subbatches"):
        assert cb[col].fillna("-").to_dict() == ca.loc[cb.index, col].fillna("-").to_dict(), col
    assert not (stores / "before" / "extras").exists() and "tier5" not in json.loads((stores / "before" / "run_manifest.json").read_text())["extra"]
    assert set(after.columns) - set(before.columns) == {"top_changed", "top_changed_confident", "p_target_top", "top_is_next"}


def test_the_per_text_cells_on_the_real_loop(stores, loop_inputs):
    rows = pd.read_parquet(stores / "tier5" / "per_sequence.parquet")
    by = {c.name: rows[rows["cell"] == c.name].sort_values("seq").reset_index(drop=True) for c in REFS + OLD_CELLS + NEW_CELLS}
    own = loop_inputs["inputs"].own
    self_rows, shift1, shift0, general = (by[c.name] for c in NEW_CELLS[:4])  # NEW_CELLS lists shift 1 before shift 0
    assert np.array_equal(self_rows["n_on"].to_numpy(), own["E"].sum(axis=1)) and self_rows["n_on"].nunique() > 1  # the count is per text
    # shift 0 is the self-merge by the partner path: the same masks (fingerprints), the same numbers
    for col in ("kl_mean", "kl_max", "mask_fp", "sigma", "n_on", "top_changed", "p_target_top"):
        assert np.array_equal(self_rows[col].to_numpy(), shift0[col].to_numpy()), col
    partner = tier5.partner_assignment("E", "within", 1, N_SEQ)
    assert np.array_equal(shift1["n_on"].to_numpy(), own["E"].sum(axis=1)[partner]) and not np.array_equal(shift1["mask_fp"].to_numpy(), self_rows["mask_fp"].to_numpy())
    assert np.array_equal(general["n_on"].to_numpy(), own["D_unif"].sum(axis=1)[tier5.partner_assignment("E", "general", 2, N_SEQ, n_pool=own["D_unif"].shape[0])])
    # a union: never below the label, the switched mass positive, and the divergence not the own-labels reference's
    ct = pd.read_parquet(stores / "tier5" / "cells.parquet").set_index("cell")
    for c in NEW_CELLS:
        assert int(ct.loc[c.name, "n_below_label_total"]) == 0 and (by[c.name]["sigma"] > 0).all() and (by[c.name]["min_gap"] >= 0).all()
        assert not np.array_equal(by[c.name]["kl_mean"].to_numpy(), by[REFS[3].name]["kl_mean"].to_numpy())
    assert int(ct.loc[NEW_CELLS[0].name, "n_on"]) == int(round(own["E"].sum(axis=1).mean())) and int(ct.loc[NEW_CELLS[1].name, "shift"]) == 1 and ct.loc[NEW_CELLS[3].name, "arm"] == "general"
    # the self-merge of a text is the one-text merge of that text into itself: the batch-shared union cell built from text 3's own set gives text 3 the same divergence and the same mask
    from vpd_audit.cells import BuiltSource

    one = Cell(RUN, "union", "E", "D_unif", 0.1, "r0", "excluded", 7, "4", "none", 1)
    src = {one.name: BuiltSource(own["E"][3].copy(), {"n_on": {"total": int(own["E"][3].sum())}, "source_sha256": source_hash(own["E"][3])}), **{r.name: BuiltSource(None, {"kind": "reference"}) for r in REFS[:1]}}
    out = stores / "one_text"
    run_cells(loop_inputs["model"], [REFS[0], one], loop_inputs["ids"], src, job="one_text", run=RUN, out_dir=out, precision="fp32", subbatch=SUBBATCH, set_name=SET, set_hash=loop_inputs["set_hash"],
              checkpoint_hashes=loop_inputs["hashes"], importance_chunk=SUBBATCH, log=lambda *_: None)
    got = pd.read_parquet(out / "per_sequence.parquet")
    got = got[(got["cell"] == one.name) & (got["seq"] == 3)].iloc[0]
    assert got["kl_mean"] == self_rows.loc[3, "kl_mean"] and got["mask_fp"] == self_rows.loc[3, "mask_fp"] and got["sigma"] == self_rows.loc[3, "sigma"]


def test_the_extras_arrays_agree_with_the_per_text_columns(stores):
    rows = pd.read_parquet(stores / "tier5" / "per_sequence.parquet")
    ex = stores / "tier5" / "extras"
    t_top, t_p, t_tie = np.load(ex / "target__top.npy"), np.load(ex / "target__top_p.npy"), np.load(ex / "target__tie.npy")
    assert (t_top.dtype, t_p.dtype, t_tie.dtype) == (np.uint16, np.float32, np.bool_) and t_top.shape == t_p.shape == t_tie.shape == (N_SEQ, 512) and (t_top != 65535).all() and np.isfinite(t_p).all()
    listed = [c for c in REFS + OLD_CELLS + NEW_CELLS if _store_run().listed(c)]
    # the per-position list: the three references, every re-run kind, the self-merge on E; not the target, the rounded reference, the partners, or a prose-donor arm
    assert {c.name for c in listed} == {c.name for c in REFS[1:4] + OLD_CELLS + NEW_CELLS[:1]}
    assert sorted(p.name for p in ex.glob("*__nll.npy")) == sorted(f"{c.name.replace('/', '__')}__nll.npy" for c in listed)
    ids = np.load(env.SETS_DIR / f"{SET}.npz")["ids"][:N_SEQ]
    conf = t_p >= 0.5
    for c in listed:
        stem = c.name.replace("/", "__")
        top, p, nll = np.load(ex / f"{stem}__top.npy"), np.load(ex / f"{stem}__p_target_top.npy"), np.load(ex / f"{stem}__nll.npy")
        assert (top.dtype, p.dtype, nll.dtype, nll.shape) == (np.uint16, np.float16, np.float16, (N_SEQ, 511))
        r = rows[rows["cell"] == c.name].sort_values("seq")
        changed = top != t_top
        assert np.array_equal(r["top_changed"].to_numpy(), changed.mean(axis=1).astype(np.float32))  # the P(a) >= 0.5 mask from the stored float32 array is the device's
        want_conf = np.where(conf.sum(axis=1) > 0, (changed & conf).sum(axis=1) / np.maximum(conf.sum(axis=1), 1), np.nan).astype(np.float32)
        assert np.allclose(r["top_changed_confident"].to_numpy(), want_conf, rtol=1e-6, equal_nan=True)
        assert np.array_equal(r["top_is_next"].to_numpy(), (top[:, :-1] == ids[:, 1:]).mean(axis=1).astype(np.float32))
        assert np.allclose(r["p_target_top"].to_numpy(), p.astype(np.float64).mean(axis=1), atol=2e-4) and np.allclose(r["ce"].to_numpy(), nll.astype(np.float64).mean(axis=1), rtol=2e-3)  # float16 storage
        ids5, p5 = np.load(ex / f"{stem}__top5_ids.npy"), np.load(ex / f"{stem}__top5_p.npy")
        pos = tier5.example_positions(N_SEQ)
        assert ids5.shape == p5.shape == (N_SEQ, 2, 5) and np.array_equal(ids5[:, :, 0], np.take_along_axis(top, pos, axis=1)) and (np.diff(p5, axis=-1) <= 0).all()
    # the target's own row: nothing changes, and its probability is its own; the unmasked model is nearly the target
    tgt = rows[rows["cell"] == REFS[0].name].sort_values("seq")
    assert (tgt["top_changed"] == 0).all() and np.allclose(tgt["p_target_top"].to_numpy(), t_p.mean(axis=1), rtol=1e-6)
    assert np.array_equal(np.load(ex / "target__top5_ids.npy")[:, :, 0], np.take_along_axis(t_top, tier5.example_positions(N_SEQ), axis=1))
    unm = rows[rows["cell"] == REFS[1].name]
    merge = rows[rows["cell"] == OLD_CELLS[1].name]
    assert unm["top_changed"].mean() < merge["top_changed"].mean() and unm["p_target_top"].mean() > merge["p_target_top"].mean()


def test_a_wrong_self_merge_set_and_a_failed_canary_stop_the_run(loop_inputs, tmp_path):
    wrong = loop_inputs["inputs"].own["E"].copy()
    wrong[9, np.flatnonzero(~wrong[9])[0]] = True  # one piece text 9 does not name
    bad = tier5.Tier5Inputs(own={**loop_inputs["inputs"].own, "E": wrong})
    with pytest.raises(tier5.GateFailure, match="differ from the on-device"):
        _run(loop_inputs, REFS[:1] + NEW_CELLS[:1], tmp_path / "wrong", store_run=_store_run(positions=False), ce_for_all=True, t5_inputs=bad)
    assert json.loads((tmp_path / "wrong" / "marker.json").read_text())["done_through"] == 0  # text 9 is in the second sub-batch: the first was good, the second is not marked done
    # the canary: the committed values are this store's own from an earlier run; one ulp off on one text of the third sub-batch stops it there
    first = _run(loop_inputs, REFS[:4] + OLD_CELLS[:1], tmp_path / "first")
    table = first.table()
    want = {c.name: np.array(table[table["cell"] == c.name].sort_values("seq")["kl_mean"], dtype=np.float32, copy=True) for c in REFS[:4] + OLD_CELLS[:1]}
    ok = tier5.SubbatchChecker(store="ok", canary={k: v.copy() for k, v in want.items()}, log=lambda *_: None)
    store = _run(loop_inputs, REFS[:4] + OLD_CELLS[:1], tmp_path / "second", store_run=_store_run(checker=ok, positions=False), ce_for_all=True)
    assert ok.n_subbatches == 3 and ok.n_compared == 5 * N_SEQ and ok.finish(store.rows)["canary_pass"]
    want[OLD_CELLS[0].name][20] = np.nextafter(want[OLD_CELLS[0].name][20], np.float32(9))
    off = tier5.SubbatchChecker(store="off", canary=want, log=lambda *_: None)
    with pytest.raises(tier5.GateFailure, match="canary fails"):
        _run(loop_inputs, REFS[:4] + OLD_CELLS[:1], tmp_path / "third", store_run=_store_run(checker=off, positions=False), ce_for_all=True)
    assert json.loads((tmp_path / "third" / "marker.json").read_text())["done_through"] == 1  # the failing sub-batch is not marked done


def test_an_interrupted_tier_5_store_resumes_bitwise_with_its_extra_arrays(stores, loop_inputs, tmp_path):
    cells = REFS + OLD_CELLS + NEW_CELLS
    with pytest.raises(RuntimeError, match="interrupted after sub-batch 2"):
        _run(loop_inputs, cells, tmp_path / "partial", store_run=_store_run(), ce_for_all=True, crash_after=1)
    store = _run(loop_inputs, cells, tmp_path / "partial", store_run=_store_run(), ce_for_all=True)
    assert store.done_through == 2 and len(store.sessions) == 2
    full, res = pd.read_parquet(stores / "tier5" / "per_sequence.parquet"), pd.read_parquet(tmp_path / "partial" / "per_sequence.parquet")
    pd.testing.assert_frame_equal(full.sort_values(["cell", "seq"]).reset_index(drop=True), res.sort_values(["cell", "seq"]).reset_index(drop=True), check_exact=True)
    for sub in ("kl", "extras"):
        a, b = sorted((stores / "tier5" / sub).glob("*.npy")), sorted((tmp_path / "partial" / sub).glob("*.npy"))
        assert [p.name for p in a] == [p.name for p in b] and all(np.array_equal(np.load(x), np.load(y), equal_nan=True) for x, y in zip(a, b))
    pd.testing.assert_frame_equal(pd.read_parquet(stores / "tier5" / "cells.parquet"), pd.read_parquet(tmp_path / "partial" / "cells.parquet"), check_exact=True)
