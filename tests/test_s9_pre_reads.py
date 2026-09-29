"""The label-only tables for the tier-5 run, on synthetic caches: the named sets of the merges with their label-only columns, the switched mass
and the receiving text's own share by source, the self-merge, and the local finishing step against committed cell tables."""

import json

import numpy as np
import pandas as pd
import pytest

from vpd_audit import s9_pre_reads as f9
from vpd_audit.constants import SEQ_LEN
from vpd_audit.sources import RUNG_SCHEDULE, Cache, donor_set, source_hash, union_source

M = {"a": 5, "b": 7}
N_SUB = 12


def _cache(n_seq=8, seed=0):
    rng = np.random.default_rng(seed)
    G = np.where(rng.random((n_seq, SEQ_LEN, N_SUB)) < 0.02, rng.random((n_seq, SEQ_LEN, N_SUB)), 0.0).astype(np.float32)
    return Cache.from_dense(G, M, name="t"), G


def _index(pool, n_rows, per_doc):
    return pd.DataFrame({"set": pool, "row": np.arange(n_rows), "source": "src", "majority_document": np.arange(n_rows) // per_doc, "first_token_document": np.arange(n_rows) // per_doc, "n_end_of_text": 0})


def test_the_merge_sizes_are_the_registered_ones_with_no_adaptive_rung():
    assert [RUNG_SCHEDULE[r] for r in f9.MERGE_RUNGS] == [("position", 1), ("position", 8), ("position", 16), ("position", 32), ("position", 64), ("sequence", 1), ("sequence", 4), ("sequence", 16), ("sequence", 64), ("pool", None)]
    assert "5a" not in f9.MERGE_RUNGS and "6a" not in f9.MERGE_RUNGS


def test_merge_sets_are_the_donor_schedules_unions_with_their_label_only_columns():
    cache, _ = _cache()
    G, P = np.zeros(N_SUB, bool), np.zeros(N_SUB, bool)
    G[[0, 1, 2]], P[[10, 11]] = True, True
    rows, rhos = f9.merge_sets("D_code", cache, _index("D_code", 8, 4), G, P, draws=3, master_seed=0)
    assert len(rows) == len(rhos) == 9 * 3 + 1  # nine sizes over three draws, and the whole pool once
    assert [r["draw"] for r in rows if r["rung"] == "8"] == [0]
    for r, rho in zip(rows, rhos):
        ds = donor_set("D_code", 8, r["draw"], r["rung"], 0)
        want = union_source(cache, ds.positions, 0.1)
        assert np.array_equal(rho, want) and r["source_sha256"] == source_hash(want) and r["n_on"] == int(want.sum()) == r["n_on__a"] + r["n_on__b"]
        assert r["n_on__a"] == int(want[:5].sum()) and r["n_donor_positions"] == len(ds.positions) and r["n_donor_rows"] == len(ds.sequences)
        assert r["n_donor_documents"] == len({s // 4 for s in ds.sequences})  # part A's documents: four rows each
        if r["n_on"]:
            assert r["share_in_code_leaning"] == want[:3].sum() / want.sum() and r["share_in_prose_leaning"] == want[10:].sum() / want.sum()
    whole = rows[-1]
    assert whole["rung"] == "8" and whole["n_donor_rows"] == 8 and whole["n_donor_documents"] == 2 and whole["donor_count"] == 8
    rows_u, _ = f9.merge_sets("D_unif", cache, _index("D_code", 8, 4), G, P, draws=2, master_seed=0)
    assert all(r["n_donor_documents"] == r["n_donor_rows"] for r in rows_u)  # the stream was shuffled by row: a donor document is a donor row


def _known():
    """Two texts, three pieces: text 0 carries piece 0 at 0.5 everywhere and piece 1 at 0.05 (below the naming threshold);
    text 1 carries piece 1 at 0.2 at its first 256 positions."""
    Gd = np.zeros((2, SEQ_LEN, N_SUB), dtype=np.float32)
    Gd[0, :, 0], Gd[0, :, 1], Gd[1, :256, 1] = 0.5, 0.05, 0.2
    return Cache.from_dense(Gd, M, name="known")


def test_sigma_and_the_receiving_texts_own_share_known_answers():
    from vpd_audit.pre_reads import per_sequence_g_sums

    cache = _known()
    g_sums, own = per_sequence_g_sums(cache), f9.own_named(cache)
    assert own[0].tolist()[:3] == [True, False, False] and own[1].tolist()[:3] == [False, True, False]
    rho = np.zeros(N_SUB, bool)
    rho[[0, 1]] = True
    t = f9.sigma_by_source(g_sums, own, ["x", "y"], [{"pool": "D_code", "draw": 0, "rung": "1", "n_on": 2}], [rho])
    x, y = t[t.source == "x"].iloc[0], t[t.source == "y"].iloc[0]
    assert x["mean_sigma"] == pytest.approx(2 - 0.5 - 0.05) and y["mean_sigma"] == pytest.approx(2 - 0.2 * 256 / SEQ_LEN)  # |rho| minus the mean label over the named pieces
    assert x["mean_share_named_by_receiving_text"] == 0.5 and y["mean_share_named_by_receiving_text"] == 0.5 and x["n_texts"] == 1


def test_self_merge_known_answers():
    from vpd_audit.pre_reads import per_sequence_g_sums

    cache = _known()
    own = f9.own_named(cache)
    df, set_hash = f9.self_merge("E", per_sequence_g_sums(cache), own, None)
    assert df["n_on"].tolist() == [1, 1]  # piece 1 at 0.05 on text 0 is not named
    assert df["sigma_self"].tolist() == pytest.approx([1 - 0.5, 1 - 0.2 * 256 / SEQ_LEN])
    assert df["source_sha256"].tolist() == [source_hash(own[0]), source_hash(own[1])] and len(set_hash) == 64
    assert f9.self_merge("E", per_sequence_g_sums(cache), own[::-1].copy(), None)[1] != set_hash  # the set's hash covers the texts in order
    assert source_hash(own[0]) == source_hash(union_source(cache, range(SEQ_LEN), 0.1))  # a text's own named set is the union over its 512 positions


def _write_finish_fixture(tmp_path, *, break_hash=False, break_count=False):
    cache, _ = _cache(n_seq=8, seed=1)
    G = P = np.zeros(N_SUB, bool)
    rows, rhos = f9.merge_sets("D_unif", cache, _index("D_unif", 8, 1), G, P, draws=2, master_seed=0)
    s9_dir, stores = tmp_path / "s9", tmp_path / "stores" / "tier1" / "E"
    s9_dir.mkdir(parents=True)
    stores.mkdir(parents=True)
    pd.DataFrame(rows).to_csv(s9_dir / "merge_sets.csv", index=False)
    from vpd_audit.pre_reads import per_sequence_g_sums

    own = f9.own_named(cache)
    df, _ = f9.self_merge("D_unif", per_sequence_g_sums(cache), own, None)
    if break_count:
        df.loc[df.seq == donor_set("D_unif", 8, 1, "4", 0).sequences[0], "n_on"] += 1
    df.to_parquet(s9_dir / "self_merge_sets.parquet", index=False)
    with open(s9_dir / "manifest.json", "w") as f:
        json.dump({"run": "t", "draws": 2, "master_seed": 0, "commits": {}}, f)
    cells = [{"cell": f"t/E/union/D_unif/tau0.1/r0/excl/k{r['draw']}/r{r['rung']}", "family": "union", "eval_set": "E", "donor_pool": "D_unif", "tau": 0.1, "background": "r0", "delta": "excluded", "draw": r["draw"], "rung": r["rung"],
              "control": "none", "donor_side_reference": None, "source_sha256": ("0" * 64 if break_hash and (r["rung"], r["draw"]) == ("2", 1) else r["source_sha256"]), "n_on": r["n_on"]} for r in rows if r["rung"] in ("1", "2", "4", "8")]
    pd.DataFrame(cells).to_parquet(stores / "cells.parquet", index=False)  # like the committed tier-1 stores: no `level` and no `replicate` column
    return s9_dir, tmp_path / "stores"


def test_finish_passes_against_matching_cell_tables_and_stops_on_a_mismatch(tmp_path):
    s9_dir, stores = _write_finish_fixture(tmp_path / "ok")
    out = f9.finish_s9_pre_reads(s9_dir, stores_root=stores, log=lambda *_: None)
    assert out["pass"] and out["against_committed"]["n_compared_with_a_committed_cell"] == 3 * 2 + 1 and out["against_committed"]["mismatched_cells"] == []
    assert [o["equal"] and o["hash_equal"] for o in out["one_text_donors"]] == [True, True] and (s9_dir / "verification.json").is_file()
    s9_dir, stores = _write_finish_fixture(tmp_path / "hash", break_hash=True)
    with pytest.raises(AssertionError):
        f9.finish_s9_pre_reads(s9_dir, stores_root=stores, log=lambda *_: None)
    s9_dir, stores = _write_finish_fixture(tmp_path / "count", break_count=True)
    with pytest.raises(AssertionError):
        f9.finish_s9_pre_reads(s9_dir, stores_root=stores, log=lambda *_: None)
