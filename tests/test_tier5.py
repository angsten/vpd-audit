"""The per-text mask path against a loop over single texts; the rotation example; partner_union
with shift 0 equal to self_union; the extras on a hand-made three-token vocabulary (top-token change, probability retained,
next-token loss, the tie flag); the external-model path with a tiny fake model whose padded ids carry known mass; the
slice-and-renormalize step. And the pieces around them: the partner arms, the example positions, the store's extra arrays, the
canary and the D_unif gate, and the launch held to the label-only tables of s9_pre_reads.py."""

import hashlib
import json
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pandas as pd
import pytest
import torch

from vpd_audit import external_models as xm
from vpd_audit import plain_terms as pt
from vpd_audit import tier5
from vpd_audit.cells import Cell, build_sources
from vpd_audit.constants import SEQ_LEN
from vpd_audit.masks import apply_binary_source, apply_binary_source_per_text, switched_mass, switched_mass_per_text
from vpd_audit.results import SubbatchStore
from vpd_audit.sources import Cache, family_masks, family_masks_per_text, per_text_source_hash, rho_tensors, rho_tensors_per_text, source_hash

ROOT = Path(__file__).resolve().parent.parent
MODS = {"a": 7, "b": 5}
N_SUB = 12

# ----------------------------------------------------------------------------- the per-text mask path


def _g_and_rows(B=4, T=6, seed=0):
    rng = np.random.default_rng(seed)
    g = {k: torch.from_numpy(rng.random((B, T, c)).astype(np.float32)) for k, c in MODS.items()}
    g["a"][0, :, 0] = 1.0  # a label of exactly 1 and one of exactly 0 stay what they are under where()
    g["b"][1, :, 1] = 0.0
    rows = rng.random((B, N_SUB)) < 0.4
    rows[2] = False  # a text whose source names nothing keeps its own labels
    return g, rows


def test_the_per_text_mask_path_equals_a_loop_over_single_texts():
    g, rows = _g_and_rows()
    rho = rho_tensors_per_text(rows, MODS, torch.float32, "cpu")
    assert {k: tuple(v.shape) for k, v in rho.items()} == {"a": (4, 1, 7), "b": (4, 1, 5)}
    masks, deltas, permitted = family_masks_per_text("self_union", g, rho, background="r0", delta="excluded")
    assert deltas is None and permitted is True
    sigma = switched_mass_per_text(g, rho)
    for b in range(rows.shape[0]):
        one = rho_tensors(rows[b], MODS, torch.float32, "cpu")
        want, _, _ = family_masks("union", {k: v[b : b + 1] for k, v in g.items()}, one, background="r0", delta="excluded")  # today's path, one text at a time
        for k in MODS:
            assert torch.equal(masks[k][b : b + 1], want[k]) and torch.equal(rho[k][b, 0], one[k])
            assert torch.equal(masks[k][b : b + 1], apply_binary_source(g[k][b : b + 1], one[k]))
        s_one = switched_mass({k: v[b : b + 1] for k, v in g.items()}, one, family="union", background="r0")
        assert torch.allclose(sigma[b : b + 1], s_one, rtol=1e-6, atol=0)
    assert torch.equal(masks["a"][2], g["a"][2]) and torch.equal(masks["b"][2], g["b"][2]) and float(sigma[2]) == 0.0
    assert all(bool((masks[k] >= g[k]).all()) for k in MODS)  # a union never lies below the label
    # with every row the same set, the per-text path is the batch-shared path, bitwise, the switched mass included
    same = np.tile(rows[0], (4, 1))
    rho_same, shared = rho_tensors_per_text(same, MODS, torch.float32, "cpu"), rho_tensors(rows[0], MODS, torch.float32, "cpu")
    m_same, _, _ = family_masks_per_text("partner_union", g, rho_same, background="r0", delta="excluded")
    m_shared, _, _ = family_masks("union", g, shared, background="r0", delta="excluded")
    assert all(torch.equal(m_same[k], m_shared[k]) for k in MODS)
    assert torch.equal(switched_mass_per_text(g, rho_same), switched_mass(g, shared, family="union", background="r0"))


def test_the_per_text_path_is_a_sibling_and_the_batch_shared_asserts_stand():
    g, rows = _g_and_rows()
    rho = rho_tensors_per_text(rows, MODS, torch.float32, "cpu")
    with pytest.raises(AssertionError, match="batch-shared source"):
        apply_binary_source(g["a"], rho["a"])  # the one-dimensional assert is not loosened
    with pytest.raises(AssertionError, match="per-text source"):
        apply_binary_source_per_text(g["a"], rho["a"][0, 0])
    with pytest.raises(AssertionError, match="per-text source"):
        apply_binary_source_per_text(g["a"], rho["a"][:2])
    with pytest.raises(AssertionError, match="binary"):
        apply_binary_source_per_text(g["a"], rho["a"] * 0.5)
    with pytest.raises(AssertionError):
        family_masks_per_text("union", g, rho, background="r0", delta="excluded")  # the batch-shared families keep their own path
    with pytest.raises(AssertionError, match="r0"):
        family_masks_per_text("self_union", g, rho, background="uniform", delta="excluded")
    with pytest.raises(AssertionError, match="r0"):
        family_masks_per_text("self_union", g, rho, background="r0", delta="included")


# ----------------------------------------------------------------------------- partners


def test_the_rotation_worked_example():
    """Four texts, omega = (3, 1, 4, 2), shift 1: text 3 receives text 1's set, 1 receives 4's, 4 receives 2's, 2 receives 3's."""
    omega = np.array([3, 1, 4, 2]) - 1
    partner = tier5.rotate(omega, 1) + 1
    assert {t: int(partner[t - 1]) for t in (3, 1, 4, 2)} == {3: 1, 1: 4, 4: 2, 2: 3}
    # the self arm and the partner arm hold the identical collection of sets, each used once
    for shift in (0, 1, 2, 3, 4, 5):
        assert sorted(tier5.rotate(omega, shift).tolist()) == [0, 1, 2, 3]
    assert tier5.rotate(omega, 0).tolist() == [0, 1, 2, 3] and tier5.rotate(omega, 4).tolist() == [0, 1, 2, 3]
    with pytest.raises(AssertionError, match="permutation"):
        tier5.rotate(np.array([0, 0, 1, 2]), 1)


def test_the_three_partner_arms():
    blocks = [("Github", 0, 16), ("Pile-CC", 16, 24), ("ArXiv", 24, 32)]
    n = 32
    for shift in (1, 2, 3, 4):
        w = tier5.partner_assignment("E", "within", shift, n)
        assert sorted(w.tolist()) == list(range(n)) and not np.any(w == np.arange(n))
        s = tier5.partner_assignment("E_lab", "source", shift, n, blocks=blocks)
        assert sorted(s.tolist()) == list(range(n)) and not np.any(s == np.arange(n))
        assert all(a <= s[i] < b for _, a, b in blocks for i in range(a, b))  # a partner within the text's own source
        gen = tier5.partner_assignment("E_lab", "general", shift, n, n_pool=80)
        assert len(set(gen.tolist())) == n and gen.min() >= 0 and gen.max() < 80  # distinct rows of the pool
    # one omega per arm: the shifts rotate it (shift r is shift 1 applied r times), and the arms and evaluation sets have their own seeds
    w1, w2 = tier5.partner_assignment("E", "within", 1, n), tier5.partner_assignment("E", "within", 2, n)
    assert np.array_equal(w2, w1[w1])
    s1, s3 = tier5.partner_assignment("E_lab", "source", 1, n, blocks=blocks), tier5.partner_assignment("E_lab", "source", 3, n, blocks=blocks)
    assert np.array_equal(s3, s1[s1[s1]])
    assert not np.array_equal(w1, tier5.partner_assignment("E_lab", "within", 1, n)) and not np.array_equal(w1, tier5.partner_assignment("E", "within", 1, n, master_seed=1))
    assert np.array_equal(w1, tier5.partner_assignment("E", "within", 1, n))
    assert tier5.partner_seed(0, "E_lab", "source") == (0, "partner", "E_lab", "source")
    # the general arm: the text at position i of the permutation of the evaluation set takes row omega'(i + r) of the pool's
    rng = np.random.default_rng(tier5.seed_from_tuple((0, "partner", "E_lab", "general")))
    omega_eval, omega_pool = rng.permutation(n), rng.permutation(80)
    gen2 = tier5.partner_assignment("E_lab", "general", 2, n, n_pool=80)
    assert all(gen2[omega_eval[i]] == omega_pool[i + 2] for i in range(n))
    with pytest.raises(AssertionError, match="tile"):
        tier5.partner_assignment("E_lab", "source", 1, n, blocks=[("Github", 0, 16), ("ArXiv", 20, 32)])


def _synthetic_inputs(seed=5, n_e=10, n_lab=8, n_pool=12):
    rng = np.random.default_rng(seed)
    dense = {k: np.where(rng.random((n, SEQ_LEN, N_SUB)) < 0.002, 0.6, 0.0).astype(np.float32) for k, n in (("E", n_e), ("E_lab", n_lab), ("D_unif", n_pool))}
    caches = {k: Cache.from_dense(v, MODS, name=k) for k, v in dense.items()}
    from vpd_audit.s9_pre_reads import own_named

    own = {k: own_named(c) for k, c in caches.items()}
    inputs = tier5.Tier5Inputs(own=own, blocks={"E_lab": [("Github", 0, 5), ("ArXiv", 5, 8)]}, documents={"E_lab": np.array([0, 0, 1, 1, 2, 3, 3, 4])})
    return caches, dense, inputs


def test_partner_union_with_shift_0_is_self_union_and_the_sources_are_the_label_caches():
    caches, dense, inputs = _synthetic_inputs()
    cells = [Cell("main", "self_union", s, s, 0.1, "r0", "excluded", 0, "4", "none", 5) for s in ("E", "E_lab", "D_unif")]
    cells += [Cell("main", "partner_union", "E", "E", 0.1, "r0", "excluded", 0, "4", "none", 5, shift=0, arm="within"), Cell("main", "partner_union", "E_lab", "E_lab", 0.1, "r0", "excluded", 0, "4", "none", 5, shift=0, arm="source"),
              Cell("main", "partner_union", "E", "E", 0.1, "r0", "excluded", 0, "4", "none", 5, shift=2, arm="within"), Cell("main", "partner_union", "E_lab", "E_lab", 0.1, "r0", "excluded", 0, "4", "none", 5, shift=1, arm="source"),
              Cell("main", "partner_union", "E_lab", "D_unif", 0.1, "r0", "excluded", 0, "4", "none", 5, shift=1, arm="general")]
    run_caches = {"D_unif_main": caches["D_unif"]}
    src = build_sources(cells, run_caches, {"main": (np.ones(N_SUB, bool), "x")}, None, None, MODS, log=lambda *_: None, tier5_inputs={"main": inputs})
    by = {c.name: src[c.name] for c in cells}
    for s, c in zip(("E", "E_lab", "D_unif"), cells[:3]):
        want = (dense[s] > 0.1).any(axis=1)  # every piece any of the text's own positions labels above 0.1
        assert np.array_equal(by[c.name].rho, want) and by[c.name].record["source_sha256"] == per_text_source_hash(want)
        assert by[c.name].record["kind"] == "per_text" and np.array_equal(by[c.name].aux["n_on_rows"], want.sum(axis=1)) and np.array_equal(by[c.name].aux["partner_rows"], np.arange(want.shape[0]))
    assert np.array_equal(by[cells[3].name].rho, by[cells[0].name].rho) and by[cells[3].name].record["source_sha256"] == by[cells[0].name].record["source_sha256"]  # shift 0, within
    assert np.array_equal(by[cells[4].name].rho, by[cells[1].name].rho)  # shift 0, source
    assert by[cells[3].name].record["n_texts_partnered_with_themselves"] == 10 and by[cells[5].name].record["n_texts_partnered_with_themselves"] == 0
    # a shifted partner arm holds the self arm's sets, each once, at the partners' rows
    p = by[cells[5].name]
    assert np.array_equal(p.rho, by[cells[0].name].rho[p.aux["partner_rows"]]) and sorted(p.aux["partner_rows"].tolist()) == list(range(10))
    assert sorted(map(source_hash, p.rho)) == sorted(map(source_hash, by[cells[0].name].rho)) and int(p.rho.sum()) == int(by[cells[0].name].rho.sum())
    gen = by[cells[7].name]
    assert np.array_equal(gen.rho, by[cells[2].name].rho[gen.aux["partner_rows"]]) and gen.record["n_on"]["total"] == int(round(gen.aux["n_on_rows"].mean()))
    assert json.loads(gen.record["seed_tuple"]) == [0, "partner", "E_lab", "general"] and all(not isinstance(v, np.ndarray) for v in gen.record.values())  # the record goes into a JSON manifest
    # the partners table: per (text, shift) the partner's row and count, and for the source arm whether the partner shares the text's document
    table = tier5.partners_table(cells, src, inputs)
    assert set(table["cell"]) == {c.name for c in cells if c.family == "partner_union"} and len(table) == 10 + 8 + 10 + 8 + 8
    srow = table[(table["arm"] == "source") & (table["shift"] == 1)].sort_values("seq")
    docs = inputs.documents["E_lab"]
    assert srow["same_document"].tolist() == (docs[srow["partner_row"].to_numpy()] == docs).tolist() and table[table["arm"] == "general"]["same_document"].isna().all()
    assert np.array_equal(srow["partner_n_on"].to_numpy(), inputs.own["E_lab"].sum(axis=1)[srow["partner_row"].to_numpy()]) and np.array_equal(srow["own_n_on"].to_numpy(), inputs.own["E_lab"].sum(axis=1))
    with pytest.raises(AssertionError, match="own-named sets"):
        build_sources(cells[:1], run_caches, {"main": (np.ones(N_SUB, bool), "x")}, None, None, MODS, log=lambda *_: None)


# ----------------------------------------------------------------------------- the extras on a three-token vocabulary


def _three_token_case():
    """Two texts, four positions, a vocabulary of three. Target logits (float32 here; bf16 on the card) and one cell's logits."""
    L = np.log
    target = torch.tensor([[[L(0.7), L(0.2), L(0.1)], [L(0.4), L(0.4), L(0.2)], [L(0.1), L(0.3), L(0.6)], [L(0.25), L(0.5), L(0.25)]],
                           [[L(0.2), L(0.2), L(0.6)], [L(0.45), L(0.35), L(0.2)], [L(0.3), L(0.3), L(0.4)], [L(0.9), L(0.05), L(0.05)]]], dtype=torch.float32)
    cell = torch.tensor([[[L(0.5), L(0.3), L(0.2)], [L(0.3), L(0.5), L(0.2)], [L(0.2), L(0.5), L(0.3)], [L(0.1), L(0.8), L(0.1)]],
                         [[L(0.6), L(0.2), L(0.2)], [L(0.5), L(0.3), L(0.2)], [L(0.2), L(0.2), L(0.6)], [L(0.3), L(0.6), L(0.1)]]], dtype=torch.float32)
    ids = torch.tensor([[0, 1, 2, 1], [2, 0, 0, 1]])
    return target, cell, ids


def test_the_extras_on_a_three_token_vocabulary():
    target_logits, cell_logits, ids = _three_token_case()
    probs = [torch.softmax(target_logits[s : s + 1].float(), dim=-1) for s in range(2)]  # chunks of one text, as target_softmax_chunks cuts them
    t = pt.target_top(probs)
    assert t["top"].tolist() == [[0, 0, 2, 1], [2, 0, 2, 0]]  # text 0, position 1 ties 0.4 with 0.4: the first index
    assert t["tie"].tolist() == [[False, True, False, False], [False, False, False, False]]  # the top two exactly equal (equal logits give equal probabilities)
    assert torch.allclose(t["top_p"], torch.tensor([[0.7, 0.4, 0.6, 0.5], [0.6, 0.45, 0.4, 0.9]]), atol=1e-6) and t["top_p"].dtype == torch.float32
    assert t["confident"].tolist() == [[True, False, True, True], [True, False, False, True]]  # P(a) >= 0.5, the boundary included
    ex = pt.cell_extras(t["top"], cell_logits, ids, chunk=1)
    assert ex["top"].tolist() == [[0, 1, 1, 1], [0, 0, 2, 1]]
    assert torch.allclose(ex["p_target_top"], torch.tensor([[0.5, 0.3, 0.3, 0.8], [0.2, 0.5, 0.6, 0.3]]), atol=1e-6)  # the cell's probability on the *target's* top token
    assert torch.allclose(ex["nll"], -torch.log(torch.tensor([[0.3, 0.2, 0.5], [0.6, 0.5, 0.2]])), atol=1e-6) and ex["nll"].shape == (2, 3)  # -log Q_t(x_{t+1}), positions 0 to T - 2
    cols = pt.summarize_extras(ex, t, ids)
    assert all(v.dtype == torch.float32 and v.shape == (2,) for v in cols.values()) and set(cols) == set(pt.EXTRA_COLUMNS)
    assert cols["top_changed"].tolist() == [0.5, 0.5]  # text 0: positions 1 and 2; text 1: positions 0 and 3
    assert torch.allclose(cols["top_changed_confident"], torch.tensor([1 / 3, 1.0]))  # among positions with P(a) >= 0.5: text 0 has three (one changed), text 1 two (both changed)
    assert torch.allclose(cols["p_target_top"], torch.tensor([(0.5 + 0.3 + 0.3 + 0.8) / 4, (0.2 + 0.5 + 0.6 + 0.3) / 4]), atol=1e-6)
    # the cell's top at t against the real token at t + 1, positions 0 to T - 2: text 0 has tops (0, 1, 1) against next tokens (1, 2, 1), one hit; text 1 has (0, 0, 2) against (0, 0, 1), two
    assert torch.allclose(cols["top_is_next"], torch.tensor([1 / 3, 2 / 3]))
    # the chunking changes nothing, and the target against itself changes nothing and keeps its own probability
    ex2 = pt.cell_extras(t["top"], cell_logits, ids, chunk=2)
    assert all(torch.equal(ex[k], ex2[k]) for k in ex)
    own = pt.summarize_extras(pt.cell_extras(t["top"], target_logits, ids, chunk=1), t, ids)
    assert own["top_changed"].tolist() == [0.0, 0.0] and own["top_changed_confident"].tolist() == [0.0, 0.0] and torch.allclose(own["p_target_top"], t["top_p"].mean(dim=1), atol=1e-6)
    as_cell = pt.summarize_extras(pt.target_as_cell(t), t, ids)
    assert as_cell["top_changed"].tolist() == [0.0, 0.0] and torch.equal(as_cell["p_target_top"], t["top_p"].mean(dim=1)) and torch.equal(as_cell["top_is_next"], own["top_is_next"])
    # a text with no confident position has no confident share
    flat = [torch.full((1, 4, 3), 1 / 3)]
    tf = pt.target_top(flat)
    assert tf["tie"].all() and not tf["confident"].any() and torch.isnan(pt.summarize_extras(pt.cell_extras(tf["top"], cell_logits[:1], ids[:1]), tf, ids[:1])["top_changed_confident"]).all()
    # stored dtypes, and the top five (here three) at fixed positions
    st = pt.storage(ex)
    assert (st["top"].dtype, st["p_target_top"].dtype, st["nll"].dtype) == (np.uint16, np.float16, np.float16)
    pos = torch.tensor([[1, 3], [0, 2]])
    ids_k, p_k = pt.top_k_at(cell_logits, pos, probs=False, k=3)
    assert ids_k[0, 1].tolist() == [1, 0, 2] or ids_k[0, 1].tolist() == [1, 2, 0]  # 0.8, then the two at 0.1
    assert torch.allclose(p_k[1, 0], torch.tensor([0.6, 0.2, 0.2]), atol=1e-6) and ids_k[1, 0, 0] == 0 and torch.allclose(p_k.sum(dim=-1), torch.ones(2, 2), atol=1e-6)
    ids_t, p_t = pt.top_k_at(probs, pos, probs=True, k=3)
    assert ids_t[0, 1].tolist()[0] == 1 and torch.allclose(p_t[1, 1], torch.tensor([0.4, 0.3, 0.3]), atol=1e-6)


def test_bf16_logits_tie_where_float32_logits_do_not():
    """Why the tie flag exists: two logits 0.03 apart at magnitude 12 are one bf16 value (spacing 1/16 there)."""
    x = torch.tensor([[[12.00, 12.03, 3.0]]])
    assert not pt.target_top([torch.softmax(x.float(), dim=-1)])["tie"].any()
    assert pt.target_top([torch.softmax(x.to(torch.bfloat16).float(), dim=-1)])["tie"].all()


def test_the_stores_extra_arrays_checkpoint_and_resume(tmp_path):
    lx = pt.LoopExtras(["c/listed", "c/unlisted"], ["c/listed", "c/absent"], example_positions=np.array([[1, 3], [0, 2], [1, 2]]), seq_len=4)
    spec = lx.spec()
    assert lx.listed == ["c/listed"] and set(spec) == {"target__top", "target__top_p", "target__tie", "target__top5_ids", "target__top5_p", "c/listed__top", "c/listed__p_target_top", "c/listed__nll", "c/listed__top5_ids", "c/listed__top5_p"}
    assert spec["c/listed__nll"][0] == (3,) and spec["target__top_p"][1] == "float32" and spec["c/listed__top5_ids"][0] == (2, 5)
    store = SubbatchStore(tmp_path / "s", n_sequences=3, cells=["c/listed", "c/unlisted"], subbatch=2, seq_len=4, extra_arrays={k: v for k, v in spec.items() if "top5" not in k})
    target_logits, cell_logits, ids = _three_token_case()
    probs = [torch.softmax(target_logits[s : s + 1].float(), dim=-1) for s in range(2)]
    lx.positions = None
    lx.start_subbatch(store, slice(0, 2), probs)
    cols = lx.cell(store, "c/listed", slice(0, 2), cell_logits, ids)
    cols_unlisted = lx.cell(store, "c/unlisted", slice(0, 2), cell_logits, ids)
    assert set(cols) == set(pt.EXTRA_COLUMNS) and all(np.array_equal(cols[k], cols_unlisted[k], equal_nan=True) for k in cols) and cols["top_changed"].dtype == np.float32
    for c in ("c/listed", "c/unlisted"):
        store.add_rows([{"cell": c, "seq": b, "kl_mean": 0.0, **{k: float(v[b]) for k, v in cols.items()}} for b in range(2)])
        store.set_positions(c, slice(0, 2), np.zeros((2, 4), np.float32))
    store.checkpoint(0)
    assert sorted(p.name for p in (tmp_path / "s" / "extras").glob("*.npy")) == sorted(f"{k.replace('/', '__')}.npy" for k in store.extra_spec)
    saved = np.load(tmp_path / "s" / "extras" / "c__listed__top.npy")
    assert saved.dtype == np.uint16 and saved[:2].tolist() == [[0, 1, 1, 1], [0, 0, 2, 1]] and saved[2].tolist() == [pt.TOKEN_FILL] * 4  # the third text is not run yet
    assert np.load(tmp_path / "s" / "extras" / "target__tie.npy")[:2].tolist() == [[False, True, False, False], [False] * 4]
    again = SubbatchStore(tmp_path / "s", n_sequences=3, cells=["c/listed", "c/unlisted"], subbatch=2, seq_len=4, extra_arrays={k: v for k, v in spec.items() if "top5" not in k})
    assert again.resume() == 0 and all(np.array_equal(again.extras[k], store.extras[k], equal_nan=True) for k in store.extras)
    assert again.table()["top_changed"].dtype == np.float32 and json.loads((tmp_path / "s" / "marker.json").read_text())["extra_arrays"]["c/listed__nll"] == {"tail": [3], "dtype": "float16"}
    with pytest.raises(AssertionError, match="extra arrays differ"):
        SubbatchStore(tmp_path / "s", n_sequences=3, cells=["c/listed", "c/unlisted"], subbatch=2, seq_len=4).resume()
    with pytest.raises(AssertionError):
        store.set_extra("c/listed__top", slice(0, 2), np.zeros((2, 4), np.int64))  # no silent cast
    # a store without extra arrays is what it was: no folder, no marker key
    plain = SubbatchStore(tmp_path / "p", n_sequences=2, cells=["c"], subbatch=2, seq_len=4)
    plain.add_rows([{"cell": "c", "seq": b, "kl_mean": 0.0} for b in range(2)])
    plain.set_positions("c", slice(0, 2), np.zeros((2, 4), np.float32))
    plain.checkpoint(0)
    assert not (tmp_path / "p" / "extras").exists() and "extra_arrays" not in json.loads((tmp_path / "p" / "marker.json").read_text())


# ----------------------------------------------------------------------------- the external-model path


class _FakeLM:
    """A tiny fake comparison model: a vocabulary of 3 padded to 5, whose two padded ids carry a known share of the softmax."""

    def __init__(self, table: torch.Tensor):
        self.table = table  # (n_ids, 5) logits by the current token id

    def __call__(self, input_ids):
        return SimpleNamespace(logits=self.table[input_ids])


def _fake_table(padded_mass: float, seed: int = 0) -> torch.Tensor:
    g = torch.Generator().manual_seed(seed)
    real = torch.softmax(torch.randn(3, 3, generator=g), dim=-1) * (1 - padded_mass)
    pad = torch.full((3, 2), padded_mass / 2)
    return torch.log(torch.cat([real, pad], dim=-1))


def test_the_external_model_path_with_a_fake_model_whose_padded_ids_carry_known_mass():
    ext = xm.ExternalModel("fake", _FakeLM(_fake_table(0.2)))
    batch = torch.tensor([[0, 1, 2, 1], [2, 2, 0, 1], [1, 0, 0, 2]])
    sliced, padded = xm.forward_sliced(ext, batch, vocab=3, chunk=2)
    assert sliced.shape == (3, 4, 3) and sliced.dtype == torch.float32 and sliced.is_contiguous() and ext.facts["logits_last_dim"] == 5
    assert torch.allclose(padded, torch.full((3, 4), 0.2), atol=1e-6)  # the full softmax's mass on ids 3 and above, at every position
    # the slice-and-renormalize step: a log-softmax over the first three ids alone is the real ids' distribution given a real id
    full = torch.softmax(_fake_table(0.2)[batch], dim=-1)
    want = full[..., :3] / full[..., :3].sum(dim=-1, keepdim=True)
    assert torch.allclose(torch.softmax(sliced, dim=-1), want, atol=1e-6) and torch.allclose(torch.softmax(sliced, dim=-1).sum(dim=-1), torch.ones(3, 4), atol=1e-6)
    # no padded ids, no mass; a model in another dtype or with too few ids is refused
    none = xm.ExternalModel("exact", _FakeLM(_fake_table(0.2)[:, :3]))
    assert float(xm.forward_sliced(none, batch, vocab=3)[1].abs().max()) == 0.0
    with pytest.raises(AssertionError):
        xm.forward_sliced(xm.ExternalModel("half", _FakeLM(_fake_table(0.2).half())), batch, vocab=3)
    with pytest.raises(AssertionError):
        xm.forward_sliced(xm.ExternalModel("short", _FakeLM(_fake_table(0.2)[:, :2])), batch, vocab=3)
    # through the same divergence function as a mask's logits, both directions, and between two comparison models
    from vpd_audit.metrics import per_position_kl, target_softmax_chunks

    target_logits = torch.randn(3, 4, 3, generator=torch.Generator().manual_seed(3))
    probs = target_softmax_chunks(target_logits)
    exts = {"fake": ext, "other": xm.ExternalModel("other", _FakeLM(_fake_table(0.1, seed=7)))}
    state: dict = {}
    q = xm.external_cell_quantities("fake", state, exts, probs, target_logits, batch, vocab=3)
    assert set(state) == {"fake", "other"} and torch.equal(q["logits"], sliced)
    assert torch.equal(q["kl"], per_position_kl(target_logits, sliced))  # bitwise the divergence every mask's logits get
    assert torch.allclose(q["kl_reverse"], per_position_kl(sliced, target_logits), atol=1e-6) and not torch.allclose(q["kl"], q["kl_reverse"])  # KL(Q || P), the other direction
    other = xm.external_cell_quantities("other", state, exts, probs, target_logits, batch, vocab=3)
    assert torch.allclose(q["kl_other"], per_position_kl(sliced, other["logits"]), atol=1e-6) and torch.allclose(other["kl_other"], per_position_kl(other["logits"], sliced), atol=1e-6)
    assert torch.allclose(other["padded_mass"], torch.full((3, 4), 0.1), atol=1e-6)
    alone = xm.external_cell_quantities("fake", {}, {"fake": ext}, probs, target_logits, batch, vocab=3)
    assert torch.isnan(alone["kl_other"]).all()


def test_the_preallocated_output_is_the_concatenated_one_bit_for_bit():
    """`forward_sliced` fills one preallocated tensor chunk by chunk instead of ending in torch.cat
    (which held the chunks and the result together); the same tensor, with and without padded ids, at a batch that is and is not
    a multiple of the chunk."""
    g = torch.Generator().manual_seed(11)
    for table in (torch.randn(3, 5, generator=g), torch.randn(3, 3, generator=g)):
        for B, chunk in ((8, 4), (7, 3), (2, 8)):
            batch = torch.randint(0, 3, (B, 6), generator=g)
            ext = xm.ExternalModel("fake", _FakeLM(table))
            new, old = xm.forward_sliced(ext, batch, vocab=3, chunk=chunk), xm.forward_sliced_by_concatenation(ext, batch, vocab=3, chunk=chunk)
            assert torch.equal(new[0], old[0]) and torch.equal(new[1], old[1]) and new[0].dtype == old[0].dtype == torch.float32 and new[0].is_contiguous()
            assert new[0].shape == (B, 6, 3) and new[1].shape == (B, 6)


def test_the_outside_yardsticks_gates_at_their_boundaries():
    def numbers(ce70, ce160, mass=1e-6, ce_other70=3.4, ce_other160=3.1):
        return {"pythia-70m": {"E": {"ce": ce70, "padded_mass_mean": mass, "padded_mass_max": 1e-3}, "E_lab_other": {"ce": ce_other70, "padded_mass_mean": mass, "padded_mass_max": 1e-3}},
                "pythia-160m": {"E": {"ce": ce160, "padded_mass_mean": 1e-9, "padded_mass_max": 1e-3}, "E_lab_other": {"ce": ce_other160, "padded_mass_mean": 1e-9, "padded_mass_max": 1e-3}}}

    order = ("pythia-70m", "pythia-160m")
    assert xm.gate_verdicts(numbers(3.5, 3.2), reference_set="E_lab_other", order=order)["pass"]
    assert xm.gate_verdicts(numbers(3.5, 3.2, mass=1e-4), reference_set="E_lab_other", order=order)["pass"]  # the mean may equal 1e-4; it may not exceed it
    assert not xm.gate_verdicts(numbers(3.5, 3.2, mass=1.0001e-4), reference_set="E_lab_other", order=order)["pass"]
    assert not xm.gate_verdicts(numbers(3.2, 3.2), reference_set="E_lab_other", order=order)["pass"]  # the larger model must be strictly below the smaller on every set
    assert not xm.gate_verdicts(numbers(3.5, 3.2, ce_other70=4.01), reference_set="E_lab_other", order=order)["pass"]  # the range is read on E^O, for each model
    assert not xm.gate_verdicts(numbers(3.5, 3.2, ce_other70=2.5, ce_other160=1.99), reference_set="E_lab_other", order=order)["pass"]
    assert xm.gate_verdicts(numbers(4.5, 4.2, ce_other70=4.0, ce_other160=2.0), reference_set="E_lab_other", order=order)["pass"]  # the range is not read on E; its ends are inside
    assert xm.VOCAB == 50277 and xm.REVISION == "step143000" and xm.MODELS["pythia-70m"] == "EleutherAI/pythia-70m" and xm.MODELS["pythia-160m"] == "EleutherAI/pythia-160m"


def test_the_tokenizer_assertions():
    class Tok:
        def __init__(self, vocab, eos=0):
            self.v, self.eos_token_id = dict(vocab), eos

        def __len__(self):
            return len(self.v)

        def get_vocab(self):
            return dict(self.v)

        def convert_ids_to_tokens(self, ids):
            inv = {i: t for t, i in self.v.items()}
            return [inv[i] for i in ids]

    v = {"<eot>": 0, "a": 1, "b": 2}
    assert xm.tokenizer_facts(Tok(v), Tok(v), vocab=3)["vocab_equal"]
    with pytest.raises(AssertionError, match="ids"):
        xm.tokenizer_facts(Tok({**v, "c": 3}), Tok(v), vocab=3)
    with pytest.raises(AssertionError, match="get_vocab"):
        xm.tokenizer_facts(Tok({"<eot>": 0, "a": 2, "b": 1}), Tok(v), vocab=3)
    with pytest.raises(AssertionError, match="end-of-text"):
        xm.tokenizer_facts(Tok(v, eos=1), Tok(v, eos=1), vocab=3)


# ----------------------------------------------------------------------------- the example positions, the canary, the gate


def test_the_example_positions_are_the_committed_list():
    pos = tier5.example_positions(1024)
    assert pos.shape == (1024, 2) and pos.min() == 48 and pos.max() == 510 and (pos[:, 0] < pos[:, 1]).all() and np.array_equal(pos, tier5.example_positions(1024))
    assert not np.array_equal(pos, tier5.example_positions(1024, master_seed=1)) and np.array_equal(pos[:64], tier5.example_positions(64))  # one generator, the texts in order
    committed = ROOT / "results" / "grid" / "pre_reads" / "main" / "s9b" / "example_positions.csv"
    text = tier5.example_positions_csv(pos)
    assert committed.read_bytes() == text.encode() and hashlib.sha256(committed.read_bytes()).hexdigest() == tier5.EXAMPLE_POSITIONS_SHA256["main"]
    assert tier5.assert_example_positions(pos, "main", required=True, log=lambda *_: None)["asserted"]
    with pytest.raises(tier5.GateFailure, match="committed list"):
        tier5.assert_example_positions(pos[::-1].copy(), "main", required=True, log=lambda *_: None)
    assert not tier5.assert_example_positions(pos[:64], "simplestories", required=False, log=lambda *_: None)["asserted"]
    with pytest.raises(tier5.GateFailure):
        tier5.assert_example_positions(pos[:64], "simplestories", required=True, log=lambda *_: None)


def test_the_committed_label_only_tables_are_the_ones_the_launch_is_held_to():
    d = ROOT / "results" / "grid" / "pre_reads" / "main" / "s9"
    assert {n: hashlib.sha256((d / n).read_bytes()).hexdigest() for n in tier5.S9_TABLES_SHA256["main"]} == tier5.S9_TABLES_SHA256["main"]


def test_the_canary_is_bitwise_and_the_d_unif_gate_is_within_a_hundredth():
    a = np.float32(0.4575)
    chk = tier5.SubbatchChecker(store="E__plain_terms", canary={"c1": np.array([a, np.float32(1.5)], dtype=np.float32)}, log=lambda *_: None)
    chk.check(0, [{"cell": "c1", "seq": 0, "kl_mean": float(a)}, {"cell": "other", "seq": 0, "kl_mean": 9.0}])
    assert chk.n_compared == 1
    with pytest.raises(tier5.GateFailure, match="canary fails"):
        chk.check(1, [{"cell": "c1", "seq": 1, "kl_mean": float(np.nextafter(np.float32(1.5), np.float32(2)))}])  # one ulp is a failure
    gate = tier5.SubbatchChecker(store="D_unif__self_merge", gate_cell="self", gate_rows={3: 1.54, 7: 0.29}, gate_draws={3: 0, 7: 3}, log=lambda *_: None)
    gate.check(0, [{"cell": "self", "seq": 3, "kl_mean": 1.5495}, {"cell": "self", "seq": 4, "kl_mean": 5.0}, {"cell": "ref", "seq": 3, "kl_mean": 0.0}])
    assert gate.gate_differences == {3: pytest.approx(0.0095, abs=1e-6)} and not gate.summary()["d_unif_gate"]["complete"]
    with pytest.raises(tier5.GateFailure, match="incomplete"):
        gate.finish([{"cell": "self", "seq": 3, "kl_mean": 1.5495}])
    out = gate.finish([{"cell": "self", "seq": 3, "kl_mean": 1.5495}, {"cell": "self", "seq": 7, "kl_mean": 0.2805}])
    assert out["d_unif_gate"]["pass"] and out["d_unif_gate"]["rows"]["7"]["draw"] == 3 and out["d_unif_gate"]["rows"]["7"]["difference"] == pytest.approx(-0.0095, abs=1e-6)
    with pytest.raises(tier5.GateFailure, match="regression gate fails"):
        gate.check(2, [{"cell": "self", "seq": 7, "kl_mean": 0.3005}])  # 0.0105 off


def test_the_committed_tables_hold_the_gates_eight_rows_and_every_re_run_cell():
    """Against the committed stores of the paper's model: the D_unif gate's other side is the eight values fixed in advance, and the canary
    finds every re-run cell and every reference."""
    from vpd_audit.cells import enumerate_cells, plain_terms_reruns
    from vpd_audit.sources import donor_set

    committed = tier5.CommittedTables((ROOT / "results" / "grid" / "main",))
    values = [round(float(committed.kl_mean(f"main/donors/union/D_unif/tau0.1/r0/excl/k{k}/r4")[0]), 2) for k in range(8)]
    assert values == [1.54, 1.38, 1.58, 0.29, 2.01, 2.48, 1.35, 1.11]
    assert [donor_set("D_unif", 1024, k, "4", 0).sequences[0] for k in range(8)] == [237, 771, 72, 677, 148, 267, 822, 81]
    cells = enumerate_cells(runs=("main",), adaptive={("D_code", 0.1): ("5a", "6a"), ("D_unif", 0.1): ("5a", "6a")}, tier_4=True, code_leaning={"main": [(16, False), (64, False), (256, False), (1007, False), (1862, True)]})
    for c in plain_terms_reruns(cells, 1007) + [c for c in cells if c.family == "reference" and c.tier == 1]:
        assert c.name in committed and committed.kl_mean(c.name).shape == ((1024,) if c.eval_set == "E" else (512,)) and committed.kl_mean(c.name).dtype == np.float32
    assert "main/E/self_union/E/tau0.1/r0/excl/k0/r4" not in committed


def test_the_launch_is_held_to_the_label_only_tables(tmp_path):
    """On synthetic caches: the tables as s9_pre_reads.py writes them; a launch whose sets are those passes, and any other set stops it."""
    from vpd_audit.s9_pre_reads import merge_sets, own_named, self_merge
    from vpd_audit.pre_reads import per_sequence_g_sums

    caches, dense, inputs = _synthetic_inputs(n_e=6, n_lab=8, n_pool=12)
    rng = np.random.default_rng(1)
    caches["D_code"] = Cache.from_dense(np.where(rng.random((9, SEQ_LEN, N_SUB)) < 0.002, 0.6, 0.0).astype(np.float32), MODS, name="D_code")
    index = pd.DataFrame([{"set": p, "row": i, "source": "s", "majority_document": i} for p in ("D_code", "D_prose") for i in range(9)])
    none = np.zeros(N_SUB, bool)
    rows = []
    for pool in ("D_code", "D_unif"):
        rows += merge_sets(pool, caches[pool], index, none, none, draws=2, master_seed=0)[0]
    d = tmp_path / "s9"
    d.mkdir()
    pd.DataFrame(rows).to_csv(d / "merge_sets.csv", index=False)
    selfs, hashes = [], {}
    for s in ("E", "E_lab", "D_unif"):
        df, hashes[s] = self_merge(s, per_sequence_g_sums(caches[s]), own_named(caches[s]), None)
        selfs.append(df)
    pd.concat(selfs).to_parquet(d / "self_merge_sets.parquet", index=False)
    (d / "manifest.json").write_text(json.dumps({"self_merge_sets_sha256": hashes, "commits": {}}))
    cells = [Cell("main", "union", "E_lab", "D_code", 0.1, "r0", "excluded", k, r, ctl, 5) for k in (0, 1) for r in ("1", "3", "4") for ctl in ("none", "plain")]
    cells += [Cell("main", "union", "E_lab", "D_unif", 0.1, "r0", "excluded", 0, "8", "none", 5), Cell("main", "self_union", "E", "E", 0.1, "r0", "excluded", 0, "4", "none", 5),
              Cell("main", "partner_union", "E_lab", "D_unif", 0.1, "r0", "excluded", 0, "4", "none", 5, shift=1, arm="general")]
    run_caches = {"D_unif_main": caches["D_unif"], "D_code_main": caches["D_code"]}
    alive = np.ones(N_SUB, bool)
    src = build_sources(cells, run_caches, {"main": (alive, source_hash(alive))}, None, None, MODS, log=lambda *_: None, tier5_inputs={"main": inputs})
    out = tier5.assert_sources_match_s9_pre_reads(cells, src, d, inputs, run="synthetic", committed=None, required=True, log=lambda *_: None)
    assert out["asserted"] and out["counts"]["union_sets"] == 7 and out["counts"]["control_matched_sets"] == 6 and out["counts"]["per_text_cells"] == 2 and out["counts"]["per_text_rows"] == 6 + 8 + 12
    # a changed union set, a set the table does not hold, and a changed per-text set each stop the launch
    src[cells[0].name].record["source_sha256"] = "0" * 64
    with pytest.raises(tier5.GateFailure, match="merge_sets.csv"):
        tier5.assert_sources_match_s9_pre_reads(cells, src, d, inputs, run="synthetic", committed=None, required=True, log=lambda *_: None)
    extra = [Cell("main", "union", "E_lab", "D_prose", 0.1, "r0", "excluded", 0, "1", "none", 5)]
    with pytest.raises(tier5.GateFailure, match="does not hold"):
        tier5.assert_sources_match_s9_pre_reads(extra, {extra[0].name: src[cells[2].name]}, d, inputs, run="synthetic", committed=None, required=True, log=lambda *_: None)
    flipped = tier5.Tier5Inputs(own={**inputs.own, "E": ~inputs.own["E"]}, blocks=inputs.blocks, documents=inputs.documents)
    with pytest.raises(tier5.GateFailure, match="own-named sets of E"):
        tier5.assert_sources_match_s9_pre_reads(cells[-2:], src, d, flipped, run="synthetic", committed=None, required=True, log=lambda *_: None)
    with pytest.raises(tier5.GateFailure, match="no label-only tables"):
        tier5.assert_sources_match_s9_pre_reads(cells, src, tmp_path / "absent", inputs, run="synthetic", committed=None, required=True, log=lambda *_: None)
    assert not tier5.assert_sources_match_s9_pre_reads(cells, src, tmp_path / "absent", inputs, run="synthetic", committed=None, required=False, log=lambda *_: None)["asserted"]
    # on the paper's model the three files must be the committed copies themselves
    with pytest.raises(tier5.GateFailure, match="not the committed copy"):
        tier5.assert_sources_match_s9_pre_reads(cells, src, d, inputs, run="main", committed=None, required=True, log=lambda *_: None)
