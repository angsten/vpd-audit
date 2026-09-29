"""The tier-6 cells on the real loop: the SimpleStories stand-in on CPU in float32, with the local artifacts and dry sets.

With an empty donor set the primary form gives the rounded_0 reference's divergence and mask fingerprint bitwise, and the secondary the
rounded_0.1 reference's (identity M6e, on the loop). The flag the loop hands to `masked_forward`, which switches its P3 assertion on, is
`grid.cell_permitted` for every cell: on for the primary form, its look-alike control and its self-merge, off for the secondary form. The
secondary self-merge of a text is the hard removal of everything the text never names above 0.1 (its mask is the text's named set at every
position), and the primary self-merge of a text is the batch-shared primary form with that text's set: same divergence, same fingerprint.
The tier-5 self-merge gives the same rows beside the new cells as alone, and a wrong self-merge set still stops the run when the text's
own labels are rounded. Skipped when the artifacts are not in the local cache."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest
import torch

from vpd_audit import cells as cells_mod
from vpd_audit import env, tier5
from vpd_audit.cells import BuiltSource, Cell, build_sources, run_cells
from vpd_audit.grid import cell_permitted
from vpd_audit.reference import CONDITION_BY_NAME
from vpd_audit.sources import ROUNDED0_FAMILY, Cache, source_hash

RUN, SET, POOL = "simplestories", "E_dry", "D_unif_dry"
N_SEQ, SUBBATCH = 24, 8


def _have_local_artifacts() -> bool:
    from vpd_audit.artifacts import AUDIT_RUNS, decomp_checkpoint_path

    try:
        spec = AUDIT_RUNS[RUN]
        return decomp_checkpoint_path(RUN).is_file() and (env.SETS_DIR / f"{SET}.npz").is_file() and (env.CACHE_DIR / "donors" / f"{POOL}_{RUN}.npz").is_file() and (env.ARTIFACTS_DIR / spec.target_run).is_dir()
    except Exception:
        return False


def _ref(cond: str) -> Cell:
    return Cell(RUN, "reference", "E", None, None, "none", CONDITION_BY_NAME[cond].delta, 0, "0", "none", 1, condition=cond)


REFS = [_ref("importances"), _ref("rounded_0"), _ref("rounded_0.1"), _ref("unmasked")]
PRIMARY = [Cell(RUN, ROUNDED0_FAMILY, "E", "D_unif", 0.1, "r0", "excluded", 0, r, "none", 6) for r in ("2", "3")]
CONTROL = [Cell(RUN, ROUNDED0_FAMILY, "E", "D_unif", 0.1, "r0", "excluded", 0, "2", "marginal", 6)]
SECONDARY = [Cell(RUN, "rounded_own_g", "E", "D_unif", 0.1, "r0", "excluded", 0, "2", "none", 3), Cell(RUN, "rounded_own_g", "E", "D_unif", 0.1, "r0", "excluded", 0, "2a", "none", 6)]
SELF_OLD = Cell(RUN, "self_union", "E", "E", 0.1, "r0", "excluded", 0, "4", "none", 5)
SELF_0 = Cell(RUN, "self_union", "E", "E", 0.1, "r0", "excluded", 0, "4", "none", 6, own_round=0.0)
SELF_01 = Cell(RUN, "self_union", "E", "E", 0.1, "r0", "excluded", 0, "4", "none", 6, own_round=0.1)
CANARY = Cell(RUN, "union", "E", "D_unif", 0.1, "r0", "excluded", 0, "2", "none", 1)
BUILT = PRIMARY + CONTROL + SECONDARY + [SELF_OLD, SELF_0, SELF_01, CANARY]
# hand-made sources, under names of their own: the empty set in both forms (M6e), and text 3's own set through the batch-shared paths
EMPTY_P = Cell(RUN, ROUNDED0_FAMILY, "E", "D_unif", 0.1, "r0", "excluded", 7, "2", "none", 6)
EMPTY_S = Cell(RUN, "rounded_own_g", "E", "D_unif", 0.1, "r0", "excluded", 7, "2", "none", 6)
TEXT = 3
P_TEXT = Cell(RUN, ROUNDED0_FAMILY, "E", "D_unif", 0.1, "r0", "excluded", 6, "4", "none", 6)  # text 3's own set, batch-shared, rounded at 0
HZ_TEXT = Cell(RUN, "hard_zero", "E", "D_unif", 0.1, "ones", "excluded", 6, "4", "none", 3)  # everything text 3 never names above 0.1, removed
HANDMADE = [EMPTY_P, EMPTY_S, P_TEXT, HZ_TEXT]


@pytest.fixture(scope="module")
def loop_inputs(tmp_path_factory):
    if not _have_local_artifacts():
        pytest.skip("the SimpleStories artifacts, E_dry, or the stand-in's D_unif cache are not in the local cache")
    from vpd_audit.artifacts import checkpoint_hashes, load_component_model
    from vpd_audit.data import load_set
    from vpd_audit.donors import build_cache
    from vpd_audit.s9_pre_reads import own_named

    torch.use_deterministic_algorithms(True, warn_only=True)
    model = load_component_model(RUN, "cpu")
    ids, _, rec = load_set(SET)
    ids = ids[:N_SEQ]
    caches = {f"D_unif_{RUN}": Cache.load(f"{POOL}_{RUN}")}
    alive_vec = np.load(env.CACHE_DIR / "donors" / f"alive_{POOL}_{RUN}.npy")
    cache_dir = tmp_path_factory.mktemp("eval_cache")  # E's own label cache, built as the loop computes g: the same rows, sub-batch, chunk, precision
    build_cache(model, ids, run=RUN, set_name="E_first24", set_hash="", checkpoint_hashes={}, precision="fp32", subbatch=SUBBATCH, chunk=SUBBATCH, out_dir=cache_dir, log=lambda *_: None)
    own = own_named(Cache.load(f"E_first24_{RUN}", cache_dir))
    module_to_c = {k: model.module_to_c[k] for k in sorted(model.module_to_c)}
    inputs = tier5.Tier5Inputs(own={"E": own})
    sources = build_sources(BUILT, caches, {RUN: (alive_vec, source_hash(alive_vec))}, None, None, module_to_c, log=lambda *_: None, tier5_inputs={RUN: inputs})
    n_sub = sum(module_to_c.values())
    empty = np.zeros(n_sub, dtype=bool)
    rec0 = lambda rho: {"n_on": {"total": int(rho.sum())}, "source_sha256": source_hash(rho)}  # noqa: E731
    sources.update({EMPTY_P.name: BuiltSource(empty.copy(), rec0(empty)), EMPTY_S.name: BuiltSource(empty.copy(), rec0(empty)),
                    P_TEXT.name: BuiltSource(own[TEXT].copy(), rec0(own[TEXT])), HZ_TEXT.name: BuiltSource(~own[TEXT], rec0(~own[TEXT]))})
    sources.update({r.name: BuiltSource(None, {"kind": "reference"}) for r in REFS})
    return {"model": model, "ids": ids, "set_hash": rec["sha256_ids"], "sources": sources, "own": own, "inputs": inputs, "hashes": checkpoint_hashes(RUN), "caches": caches,
            "alive": {RUN: (alive_vec, source_hash(alive_vec))}, "module_to_c": module_to_c}


def _run(inputs, cells, out_dir, sources=None):
    return run_cells(inputs["model"], cells, inputs["ids"], sources or inputs["sources"], job="tier6_loop_test", run=RUN, out_dir=out_dir, precision="fp32", subbatch=SUBBATCH, set_name=SET,
                     set_hash=inputs["set_hash"], checkpoint_hashes=inputs["hashes"], importance_chunk=SUBBATCH, resume=True, log=lambda *_: None)


@pytest.fixture(scope="module")
def store(loop_inputs, tmp_path_factory):
    """The store, run once with a spy on masked_forward that records the flag each call is handed."""
    root = tmp_path_factory.mktemp("tier6_loop")
    calls: list[bool] = []
    real = cells_mod.masked_forward

    def spy(*a, **kw):
        calls.append(bool(kw["permitted"]))
        return real(*a, **kw)

    mp = pytest.MonkeyPatch()
    mp.setattr(cells_mod, "masked_forward", spy)
    try:
        cells = REFS + BUILT + HANDMADE
        _run(loop_inputs, cells, root / "store")
    finally:
        mp.undo()
    _run(loop_inputs, REFS + [SELF_OLD], root / "alone")
    rows = pd.read_parquet(root / "store" / "per_sequence.parquet")
    by = {c.name: rows[rows["cell"] == c.name].sort_values("seq").reset_index(drop=True) for c in cells}
    return {"root": root, "by": by, "calls": calls, "cells": cells}


def test_an_empty_donor_set_gives_the_rounded_references_on_the_loop(store):
    by = store["by"]
    for cell, ref in ((EMPTY_P, "rounded_0"), (EMPTY_S, "rounded_0.1")):
        r = by[f"{RUN}/E/ref/{ref}"]
        for col in ("kl_mean", "kl_max", "kl_argmax", "mask_fp"):
            assert np.array_equal(by[cell.name][col].to_numpy(), r[col].to_numpy()), (cell.name, col)
    assert not np.array_equal(by[f"{RUN}/E/ref/rounded_0"]["mask_fp"].to_numpy(), by[f"{RUN}/E/ref/rounded_0.1"]["mask_fp"].to_numpy())  # the two starts differ on the stand-in


def test_the_loop_asserts_p3_on_every_cell_of_the_primary_form_and_on_no_cell_of_the_secondary(store):
    """run_cells puts the references first and keeps the rest in order; every non-target cell is one masked forward per sub-batch."""
    cells = store["cells"]
    order = sorted(cells, key=lambda c: 0 if c.family == "reference" else 1)
    n_sub = N_SEQ // SUBBATCH
    assert len(store["calls"]) == n_sub * len(order)
    flags = {c.name: [store["calls"][i * len(order) + j] for i in range(n_sub)] for j, c in enumerate(order)}
    assert all(len(set(v)) == 1 for v in flags.values())
    flag = {n: v[0] for n, v in flags.items()}
    assert all(flag[c.name] == cell_permitted(c) for c in cells if c is not HZ_TEXT), {c.name: (flag[c.name], cell_permitted(c)) for c in cells if flag[c.name] != cell_permitted(c)}
    assert all(flag[c.name] for c in PRIMARY + CONTROL + [SELF_0, EMPTY_P, P_TEXT]) and not any(flag[c.name] for c in SECONDARY + [SELF_01, EMPTY_S])
    ct = pd.read_parquet(store["root"] / "store" / "cells.parquet").set_index("cell")
    by = store["by"]
    for c in PRIMARY + CONTROL + [SELF_0]:
        assert int(ct.loc[c.name, "n_below_label_total"]) == 0 and (by[c.name]["min_gap"] >= 0).all() and (by[c.name]["n_below_label"] == 0).all()
    for c in SECONDARY + [SELF_01]:
        assert int(ct.loc[c.name, "n_below_label_total"]) > 0  # rounding at 0.1 drops the labels in (0, 0.1], as it must
    # every rung of a form differs from its own start; each form starts where its reference is
    for c, ref in [(c, "rounded_0") for c in PRIMARY + CONTROL + [SELF_0]] + [(c, "rounded_0.1") for c in SECONDARY + [SELF_01]]:
        assert cells_mod.reference_for(c) == ref and not np.array_equal(by[c.name]["mask_fp"].to_numpy(), by[f"{RUN}/E/ref/{ref}"]["mask_fp"].to_numpy())


def test_the_binary_self_merges_of_a_text_are_the_batch_shared_masks_of_its_set(store, loop_inputs):
    by, own = store["by"], loop_inputs["own"]
    for per_text, shared in ((SELF_01, HZ_TEXT), (SELF_0, P_TEXT)):
        a, b = by[per_text.name].loc[TEXT], by[shared.name].loc[TEXT]
        assert a["kl_mean"] == b["kl_mean"] and a["kl_max"] == b["kl_max"] and a["mask_fp"] == b["mask_fp"], (per_text.name, shared.name)
    for c in (SELF_0, SELF_01, SELF_OLD):
        assert np.array_equal(by[c.name]["n_on"].to_numpy(), own.sum(axis=1)) and by[c.name]["n_on"].nunique() > 1
    # three forms of the self-merge, three different masks
    fps = [by[c.name]["mask_fp"].to_numpy() for c in (SELF_OLD, SELF_0, SELF_01)]
    assert not np.array_equal(fps[0], fps[1]) and not np.array_equal(fps[1], fps[2]) and not np.array_equal(fps[0], fps[2])


def test_the_tier_5_self_merge_is_unchanged_beside_the_new_cells(store):
    alone = pd.read_parquet(store["root"] / "alone" / "per_sequence.parquet")
    alone = alone[alone["cell"] == SELF_OLD.name].sort_values("seq").reset_index(drop=True)
    beside = store["by"][SELF_OLD.name]
    for col in ("kl_mean", "kl_max", "kl_argmax", "mask_fp", "sigma", "n_on", "min_gap", "n_below_label"):
        assert np.array_equal(alone[col].to_numpy(), beside[col].to_numpy()), col
    ca = pd.read_parquet(store["root"] / "alone" / "cells.parquet").set_index("cell").loc[SELF_OLD.name]
    cb = pd.read_parquet(store["root"] / "store" / "cells.parquet").set_index("cell").loc[SELF_OLD.name]
    for col in ("source_sha256", "mask_fp_cell", "mask_fp_modules", "n_ne_g_modules", "n_ne_one_modules", "n_below_label_total"):
        assert ca[col] == cb[col], col
    assert pd.isna(cb["own_round"]) and cb.name == "simplestories/E/self_union/E/tau0.1/r0/excl/k0/r4"


def test_a_wrong_self_merge_set_stops_the_binary_self_merge_too(loop_inputs, tmp_path):
    wrong = loop_inputs["own"].copy()
    wrong[9, np.flatnonzero(~wrong[9])[0]] = True  # one piece text 9 does not name
    bad = tier5.Tier5Inputs(own={"E": wrong})
    for c in (SELF_0, SELF_01):
        src = build_sources([c], loop_inputs["caches"], loop_inputs["alive"], None, None, loop_inputs["module_to_c"], log=lambda *_: None, tier5_inputs={RUN: bad})
        src[REFS[0].name] = BuiltSource(None, {"kind": "reference"})
        with pytest.raises(tier5.GateFailure, match="differ from the on-device"):
            _run(loop_inputs, [REFS[0], c], tmp_path / f"wrong_{c.own_round:g}", sources=src)
