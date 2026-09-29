"""The launch harness: the adaptive rule across launches, the pre-reads' CSR arithmetic against the loop's
dense functions, the verification launch's cell list and comparisons on a synthetic store, and the resume
comparison. No model."""

from __future__ import annotations

import json
from dataclasses import asdict

import numpy as np
import pandas as pd
import pytest
import torch

from vpd_audit.constants import SEQ_LEN
from vpd_audit.sources import Cache, rho_tensors

M2 = {"h.0.attn.q_proj": 6, "h.1.mlp.c_fc": 10}
N_SUB = 16


def _dense(n_seq: int, seed: int) -> np.ndarray:
    rng = np.random.default_rng(seed)
    G = rng.random((n_seq * SEQ_LEN, N_SUB), dtype=np.float32)
    G[G < 0.85] = 0.0  # sparse, exact zeros
    G[G >= 0.85] = (G[G >= 0.85] - 0.85) / 0.15  # in (0, 1)
    G[rng.random(G.shape) < 0.02] = 0.005  # a few small labels below 0.01
    G[0, :] = 0.0  # a clean first position on the first sequence
    return G.astype(np.float32)


def test_adaptive_rule_written_then_asserted(tmp_path):
    from vpd_audit.grid import assert_or_write_adaptive_rule

    rule = {"n_on": {"D_unif|tau0.1": {"1": {0: 201, 1: 199}, "8": {0: 9966}}}, "rule": {"D_unif|tau0.1": {"insert_5a_6a": True, "ratio": 0.92}}, "insert": {"D_unif|tau0.1": ["5a", "6a"]}}
    p = tmp_path / "grid" / "main" / "adaptive_rule.json"
    assert assert_or_write_adaptive_rule(rule, p, log=lambda *_: None) == "written" and p.is_file()
    assert assert_or_write_adaptive_rule(rule, p, log=lambda *_: None) == "asserted"
    changed = json.loads(json.dumps(rule))
    changed["n_on"]["D_unif|tau0.1"]["1"]["0"] = 202
    with pytest.raises(AssertionError, match="differs"):
        assert_or_write_adaptive_rule(changed, p, log=lambda *_: None)


def test_csr_first_touched_and_sigma_match_the_dense_loop_functions():
    from vpd_audit.masks import first_touched, switched_mass
    from vpd_audit.pre_reads import first_touched_from_cache, labels_in_set_per_position, per_sequence_g_sums, per_subcomponent_counts_and_max, sigma_from_sums

    n_seq = 3
    G = _dense(n_seq, 5)
    cache = Cache.from_dense(G, M2)
    g_dense = {k: torch.from_numpy(G.reshape(n_seq, SEQ_LEN, N_SUB)[..., cache.offsets[k] : cache.offsets[k] + M2[k]].copy()) for k in M2}
    rng = np.random.default_rng(1)
    for trial in range(5):
        S = rng.random(N_SUB) < 0.4
        if trial == 4:
            S[:] = False
        ft = first_touched_from_cache(cache, S, (0.0, 0.01, 0.1))
        rt = rho_tensors(S, M2, torch.float32, "cpu", cache.offsets)
        for tq in (0.0, 0.01, 0.1):
            t_dense, n_dense = first_touched(g_dense, rt, tq)
            assert np.array_equal(ft[tq][0], t_dense.numpy()) and np.array_equal(ft[tq][1], n_dense.numpy()), (trial, tq)
        # the switched mass of the union (r0), the soft erase (r1), and a hard-zero cell's soft-erase sigma all equal |rho| - sum g / T
        sums = per_sequence_g_sums(cache)
        sig = sigma_from_sums(sums, S[:, None])[:, 0]
        for fam, bg in (("union", "r0"), ("soft_erase", "r1")):
            dense = switched_mass(g_dense, rt, family=fam, background=bg).numpy().astype(np.float64)
            assert np.allclose(sig, dense, rtol=1e-5, atol=1e-5), (trial, fam)
        per_pos = labels_in_set_per_position(cache, S)
        assert per_pos.shape == (n_seq * SEQ_LEN,) and np.array_equal(per_pos, ((G > 0) & S[None, :]).sum(axis=1))
    counts, mx = per_subcomponent_counts_and_max(cache)
    assert np.array_equal(counts, (G > 0).sum(axis=0)) and np.array_equal(mx, G.max(axis=0))
    assert ft[0.0][0][0] >= 1  # the first position of sequence 0 is clean by construction
    # sequences whose erased set is never used sit at T with no touched position
    empty = first_touched_from_cache(cache, np.zeros(N_SUB, bool), (0.0,))
    assert (empty[0.0][0] == SEQ_LEN).all() and (empty[0.0][1] == 0).all()


def test_pre_read_inputs_and_the_paper_names():
    from vpd_audit.pre_reads import paper_inputs

    inp = paper_inputs("control")
    assert inp.cache_tag == "control" and inp.set_map == {"E": "E", "E_lab": "E_lab"} and inp.pool_map["D_prose"] == "D_prose" and inp.chains_dir is None and inp.positive_stratum == "Github"


def test_verify_cells_are_the_45_registered_and_match_the_identities_names():
    from vpd_audit.verify import verify_cells

    cells = verify_cells("main")
    names = [c.name for c in cells]
    assert len(names) == len(set(names)) == 45
    assert sum(1 for c in cells if c.family == "reference") == 25
    chains = pd.read_parquet("results/identities/chains_main/cells.parquet")["cell"].tolist()
    assert all(n in names for n in chains if "/ref/" not in n) and len([n for n in chains if "/ref/" not in n]) == 16
    assert "main/E/soft_erase/D_unif/tau0.1/r1/excl/k0/r8" in names and "main/E/soft_erase/D_unif/tau0.1/r1/incl/k0/r8" in names
    assert "main/E/never_named_hard/D_unif/tau0.1/ones/incl/k0/r8" in names and "main/E/never_named_hard/D_unif/tau0.1/ones/excl/k0/r8" in names
    assert all(c.eval_set == "E" and c.run == "main" for c in cells)


def _synthetic_verify_store(tmp_path, n_seq=200, perturb: str | None = None):
    from vpd_audit.verify import verify_cells

    rng = np.random.default_rng(7)
    cells = verify_cells("main")
    d = tmp_path / "verify"
    (d / "kl").mkdir(parents=True)
    rows, per_cell = [], {}
    for c in cells:
        base = 0.0 if c.condition == "target" else float(rng.random() * 2)
        kl = (rng.random((n_seq, SEQ_LEN), dtype=np.float32) * base).astype(np.float32)
        per_cell[c.name] = kl
        np.save(d / "kl" / f"{c.name.replace('/', '__')}.npy", kl.astype(np.float16))
        for b in range(n_seq):
            row = {"cell": c.name, "seq": b, "kl_mean": float(kl[b].mean()), "ce": float(rng.random()) if c.family == "reference" else float("nan")}
            for tag in ("0.1", "0"):
                if c.is_hard_zero:
                    t = int(rng.integers(0, SEQ_LEN + 1))
                    row[f"t_star_{tag}"] = t
                    row[f"d_{tag}"] = float("nan") if t == 0 else float((kl[b, :t] - 0.0).mean())
                else:
                    row[f"t_star_{tag}"], row[f"d_{tag}"] = -1, float("nan")
            rows.append(row)
    df = pd.DataFrame(rows)
    ct = pd.DataFrame([{**asdict(c), "cell": c.name, "mask_fp_cell": f"{abs(hash(c.name)) % (1 << 64):016x}", "n_on": 28946 if c.family == "never_named_hard" else 0} for c in cells])
    # the earlier runs: the acceptance table (unprefixed names, kl_mean and ce) and the chains store (kl_mean per cell, mask_fp_cell)
    acc = df[df.cell.str.contains("/ref/")].copy()
    acc["cell"] = acc["cell"].str[len("main/E/ref/"):]
    chain_names = [c.name for c in cells if c.family in ("union", "hard_zero")]
    ch = df[df.cell.isin(chain_names + ["main/E/ref/unmasked", "main/E/ref/importances"])].copy()
    if perturb == "acceptance":
        acc.loc[acc.index[5], "kl_mean"] = np.float32(acc.loc[acc.index[5], "kl_mean"]) + np.float32(1e-6)
    if perturb == "chain_digest":
        ct.loc[ct.cell == chain_names[3], "mask_fp_cell"] = "0" * 16
    (d.parent / "acc").mkdir(exist_ok=True)
    (d.parent / "chains").mkdir(exist_ok=True)
    acc.to_parquet(d.parent / "acc" / "per_sequence.parquet", index=False)
    ch.to_parquet(d.parent / "chains" / "per_sequence.parquet", index=False)
    ct_chain = pd.DataFrame([{"cell": c, "mask_fp_cell": f"{abs(hash(c)) % (1 << 64):016x}"} for c in chain_names])
    ct_chain.to_parquet(d.parent / "chains" / "cells.parquet", index=False)
    # the reference table's unmasked/importances are the ones the store carries (no perturbation there)
    nn = df[df.cell == "main/E/never_named_hard/D_unif/tau0.1/ones/excl/k0/r8"]
    h4 = {"mean_kl": {"b_our_hard_zero_complement": float(nn[nn.seq < 128]["kl_mean"].mean()) + 0.004}}
    (d.parent / "h4.json").write_text(json.dumps(h4))
    df.to_parquet(d / "per_sequence.parquet", index=False)
    ct.to_parquet(d / "cells.parquet", index=False)
    return d


def test_verify_comparisons_pass_on_a_consistent_store_and_catch_a_perturbation(tmp_path):
    from vpd_audit.verify import compare_with_earlier_runs, format_comparisons

    d = _synthetic_verify_store(tmp_path / "ok")
    c = compare_with_earlier_runs(d, d.parent / "acc" / "per_sequence.parquet", d.parent / "chains", d.parent / "h4.json")
    assert c["references_vs_acceptance"]["pass"] and c["references_vs_acceptance"]["n_pairs"] == 25 * 200
    assert c["chains_vs_identities"]["pass"] and c["chains_vs_identities"]["n_cells"] == 16
    assert c["never_named_rung_8"]["within_tolerance"] and abs(c["never_named_rung_8"]["difference"] + 0.004) < 1e-6
    assert set(c["fourth_cell"]) == {"unmasked", "importances", "F_excluded", "F_included"} and c["fourth_cell"]["F_excluded"]["paired_F_minus_unmasked"]["n"] == 200
    text = format_comparisons(c, None, None)
    assert "-> pass" in text and "equality only" in text
    d2 = _synthetic_verify_store(tmp_path / "bad_acc", perturb="acceptance")
    c2 = compare_with_earlier_runs(d2, d2.parent / "acc" / "per_sequence.parquet", d2.parent / "chains", d2.parent / "h4.json")
    assert not c2["references_vs_acceptance"]["pass"] and not c2["references_vs_acceptance"]["kl_mean_equal"] and c2["references_vs_acceptance"]["ce_equal"]
    d3 = _synthetic_verify_store(tmp_path / "bad_fp", perturb="chain_digest")
    c3 = compare_with_earlier_runs(d3, d3.parent / "acc" / "per_sequence.parquet", d3.parent / "chains", d3.parent / "h4.json")
    assert not c3["chains_vs_identities"]["mask_fp_cell_equal"] and c3["chains_vs_identities"]["kl_mean_equal"]


def test_verify_store_comparison_is_bitwise(tmp_path):
    import shutil

    from vpd_audit.verify import compare_stores_bitwise

    a = _synthetic_verify_store(tmp_path / "a", n_seq=20)
    b = tmp_path / "b" / "verify"
    shutil.copytree(a, b)
    r = compare_stores_bitwise(a, b)
    assert r["pass"] and r["rows"] == 45 * 20 and r["n_arrays"] == 45
    arr_path = next((b / "kl").glob("*.npy"))
    arr = np.load(arr_path)
    arr[0, 0] = np.float16(float(arr[0, 0]) + 0.5)
    np.save(arr_path, arr)
    r2 = compare_stores_bitwise(a, b)
    assert not r2["arrays_equal"] and r2["rows_equal"] and not r2["pass"]


def test_modal_list_parsing():
    from vpd_audit.modal_app import _parse_list

    assert _parse_list("1") == ("1",) and _parse_list("2, 3") == ("2", "3") and _parse_list("") == () and _parse_list("E,E_lab") == ("E", "E_lab")


def test_control_overlap_rows_and_spearman():
    """Every controlled cell's set against the set it matches, with the sizes and the
    control's pool (alive for a plain control, alive minus prose-named at the cell's tau for a complement control), on
    synthetic sources; and Spearman's rank correlation with average ranks for ties."""
    from vpd_audit.cells import BuiltSource, Cell
    from vpd_audit.pre_reads import control_overlap_rows, spearman

    n = 20
    alive = np.zeros(n, bool); alive[:16] = True
    prose = np.zeros(n, bool); prose[:6] = True
    A = np.zeros(n, bool); A[6:10] = True  # the erased set: alive, not prose-named
    C_plain = np.zeros(n, bool); C_plain[8:12] = True  # a plain control overlapping A on two members
    C_comp = np.zeros(n, bool); C_comp[7:11] = True  # a complement control overlapping A on three
    base = Cell("main", "code_specific_hard", "E_lab", "D_code", 0.1, "ones", "included", 0, "4", "none", 1)
    plain = Cell("main", "code_specific_hard", "E_lab", "D_code", 0.1, "ones", "included", 0, "4", "plain", 2)
    comp = Cell("main", "code_specific_hard", "E_lab", "D_code", 0.1, "ones", "included", 0, "4", "complement", 2)
    orphan = Cell("main", "hard_zero", "E", "D_unif", 0.1, "ones", "included", 0, "4", "plain", 2)  # no matched cell among the cells
    ref = Cell("main", "reference", "E_lab", None, None, "none", "excluded", 0, "0", "none", 1, condition="unmasked")
    sources = {base.name: BuiltSource(A, {}), plain.name: BuiltSource(C_plain, {"control": {"overflow": {"m": 1}}}), comp.name: BuiltSource(C_comp, {"control": {"overflow": {}}}),
               orphan.name: BuiltSource(C_plain, {}), ref.name: BuiltSource(None, {"kind": "reference"})}
    rows = control_overlap_rows([base, plain, comp, orphan, ref], sources, alive, {0.1: prose})
    assert [r["control"] for r in rows] == ["plain", "complement"]
    p, c = rows
    assert p["n_named"] == 4 and p["n_control"] == 4 and p["overlap"] == 2 and p["fraction_of_named"] == 0.5 and p["control_pool_size"] == 16 and p["named_in_control_pool"] == 4 and p["control_overflow"] == 1
    assert c["overlap"] == 3 and c["fraction_of_named"] == 0.75 and c["control_pool_size"] == 10 and c["named_in_control_pool"] == 4 and c["control_overflow"] == 0
    assert p["cell"] == plain.name and p["rung"] == "4" and p["tau"] == 0.1
    x = np.arange(10, dtype=float)
    assert spearman(x, x) == pytest.approx(1.0) and spearman(x, -x) == pytest.approx(-1.0)
    assert spearman(x, np.zeros(10)) != spearman(x, np.zeros(10))  # nan on a constant key
    ties = np.array([0, 0, 0, 1, 1, 2, 3, 4, 5, 6], float)
    assert spearman(x, ties) == pytest.approx(pd.Series(x).corr(pd.Series(ties), method="spearman"))


def test_set_composition_rows_and_pool_usage():
    """On synthetic sources, per draw and as a mean over draws for curve 1's union and its
    plain control at the small rungs, the mean and median weight norm and the mean pool usage of the named set, with the
    alive set as the baseline; pool usage is the fraction of positions with g > 0.1 per subcomponent."""
    from vpd_audit.cells import BuiltSource, Cell
    from vpd_audit.pre_reads import SET_COMPOSITION_RUNGS, pool_usage, set_composition_rows
    from vpd_audit.sources import Cache

    G = np.zeros((2 * 512, 6), dtype=np.float32)
    G[:100, 0] = 0.5; G[:50, 1] = 0.05; G[:10, 1] = 0.2; G[:1024, 2] = 0.11
    cache = Cache.from_dense(G, {"h.0.attn.q_proj": 3, "h.0.mlp.c_fc": 3}, name="D_unif_main")
    usage = pool_usage(cache, 0.1)
    assert np.allclose(usage, [100 / 1024, 10 / 1024, 1.0, 0, 0, 0])
    norms = np.array([1.0, 2.0, 3.0, 4.0, 5.0, 6.0])
    alive = np.array([True, True, True, True, False, False])

    def cell(rung, draw, control):
        return Cell("main", "union", "E", "D_unif", 0.1, "r0", "excluded", draw, rung, control, 1 if control == "none" else 2, descriptive=rung in ("2a", "2b"))

    def rho(idx):
        v = np.zeros(6, bool); v[list(idx)] = True; return v

    cells = [cell("1", 0, "none"), cell("1", 1, "none"), cell("2a", 0, "none"), cell("1", 0, "plain"), cell("1", 1, "plain"), cell("8", 0, "none")]
    sources = {cells[0].name: BuiltSource(rho([0]), {}), cells[1].name: BuiltSource(rho([0, 2]), {}), cells[2].name: BuiltSource(rho([1, 2]), {}),
               cells[3].name: BuiltSource(rho([3]), {}), cells[4].name: BuiltSource(rho([1]), {}), cells[5].name: BuiltSource(rho([0, 1, 2, 3]), {})}
    rows = set_composition_rows(cells, sources, norms, usage, alive)
    by = {(r["family"], r["rung"], r["draw"]): r for r in rows}
    assert SET_COMPOSITION_RUNGS == ("1", "2", "2a", "2b", "3", "4") and ("union", "8", 0) not in by  # rung 8 is not a small rung
    assert by[("union", "1", 0)]["mean_norm"] == 1.0 and by[("union", "1", 1)]["mean_norm"] == 2.0 and by[("union", "1", 1)]["median_norm"] == 2.0 and by[("union", "1", 1)]["mean_usage"] == pytest.approx((100 / 1024 + 1.0) / 2)
    assert by[("union", "1", "mean")]["mean_norm"] == 1.5 and by[("union", "1", "mean")]["n_on"] == 1.5
    assert by[("union", "2a", 0)]["mean_norm"] == 2.5 and by[("union", "2a", "mean")]["median_norm"] == 2.5
    assert by[("control", "1", "mean")]["mean_norm"] == 3.0 and by[("control", "1", 0)]["mean_usage"] == 0.0
    base = by[("alive (baseline)", "", "")]
    assert base["n_on"] == 4 and base["mean_norm"] == 2.5 and base["median_norm"] == 2.5 and base["mean_usage"] == pytest.approx((100 / 1024 + 10 / 1024 + 1.0) / 4)
