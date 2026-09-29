"""The donors' CSR cache on synthetic g: the global index order, the per-position sorting, the bitwise dense
reconstruction, the threshold counts, and the module offsets. Two modules named like the model's with C = 7 and 3;
B = 2, T = 5."""

import numpy as np
import torch

from vpd_audit.donors import counts_above, dense_from_csr, module_offsets, subbatch_csr

B, T = 2, 5
MODULE_TO_C = {"h.0.attn.q_proj": 7, "h.0.mlp.c_fc": 3}


def test_module_offsets_in_sorted_order():
    assert module_offsets(MODULE_TO_C) == {"h.0.attn.q_proj": 0, "h.0.mlp.c_fc": 7}
    assert module_offsets({"b": 2, "a": 3}) == {"a": 0, "b": 3}


def test_csr_round_trip_bitwise_and_counts():
    gen = torch.Generator().manual_seed(0)
    g = {k: torch.rand((B, T, c), generator=gen) for k, c in MODULE_TO_C.items()}
    for k in g:
        g[k][g[k] < 0.5] = 0.0
    g["h.0.mlp.c_fc"][1, 3, 1] = 1e-9  # a tiny nonzero must be kept exactly
    counts, gidx, vals = subbatch_csr(g)
    n_sub = sum(MODULE_TO_C.values())
    assert counts.shape == (B * T,) and gidx.numel() == vals.numel() == int(counts.sum())
    indptr = np.zeros(B * T + 1, dtype=np.int64)
    np.cumsum(counts.numpy(), out=indptr[1:])
    indices = gidx.numpy().astype(np.uint16)
    values = vals.numpy().astype(np.float32)
    # indices sorted within each position and in the global order (q_proj first, then c_fc at offset 7)
    for p in range(B * T):
        seg = indices[indptr[p] : indptr[p + 1]]
        assert np.all(np.diff(seg.astype(int)) > 0)
    dense = dense_from_csr(indptr, indices, values, slice(0, B * T), n_sub)
    G = torch.cat([g[k].reshape(B * T, -1) for k in sorted(g)], dim=1).numpy()
    assert np.array_equal(dense, G)
    assert dense[1 * T + 3, 7 + 1] == np.float32(1e-9)
    # counts above a threshold per subcomponent (strict)
    c0 = counts_above(indices, values, n_sub, 0.0)
    assert c0.shape == (n_sub,) and c0.sum() == (G > 0).sum() and np.array_equal(c0, (G > 0).sum(0))
    c5 = counts_above(indices, values, n_sub, 0.5)
    assert np.array_equal(c5, (G > 0.5).sum(0)) and c5.sum() <= c0.sum()


def test_alive_from_cache_matches_the_dense_definition(tmp_path):
    import json

    from vpd_audit.donors import _sha, alive_from_cache

    rng = np.random.default_rng(3)
    n_pos, n_sub = 40, 10
    G = rng.random((n_pos, n_sub)).astype(np.float32)
    G[G < 0.7] = 0.0
    G[:, 3] = 0.0  # dead
    G[:, 5] = 0.0
    G[0, 5] = np.float32(1e-5)  # mean 2.5e-7 < 1e-6: dead by the threshold
    G[1, 7] = np.float32(1e-4)  # mean 2.5e-6 > 1e-6 if the rest are zero
    G[:, 7] = 0.0
    G[1, 7] = np.float32(1e-4)
    nz = G != 0
    indptr = np.zeros(n_pos + 1, dtype=np.int64)
    np.cumsum(nz.sum(1), out=indptr[1:])
    rows, cols = np.nonzero(nz)
    module_to_c = {"h.0.attn.q_proj": 6, "h.1.mlp.c_fc": 4}
    np.savez(tmp_path / "X_main.npz", indptr=indptr, indices=cols.astype(np.uint16), values=G[rows, cols])
    (tmp_path / "X_main.json").write_text(json.dumps({"n_subcomponents": n_sub, "n_positions": n_pos, "module_offsets": {"h.0.attn.q_proj": 0, "h.1.mlp.c_fc": 6}, "module_to_c": module_to_c,
                                                       "sha256": {"indptr": _sha(indptr), "indices": _sha(cols.astype(np.uint16)), "values": _sha(G[rows, cols])}, "n_sequences": 1}))
    res = alive_from_cache("X_main", tmp_path)
    expected = (G.astype(np.float64).sum(0) / n_pos) > 1e-6
    assert res["alive"]["total"] == int(expected.sum()) and res["alive"]["layer_0"] == int(expected[:6].sum()) and res["alive"]["layer_1"] == int(expected[6:].sum())
    assert not expected[3] and not expected[5] and expected[7]
    assert np.array_equal(np.load(tmp_path / "alive_X_main.npy"), expected) and res["saved_vector"]["source"] == "this computation"
    # a second call finds the saved vector and reports agreement
    res2 = alive_from_cache("X_main", tmp_path)
    assert res2["saved_vector"]["identical"] and res2["saved_vector"]["n_disagreements_with_cache"] == 0
