"""The source checks on the worked examples: A1 (the union, soft erase and hard zero at tau = 0.5), A2 (strict thresholds,
the named sets nested as tau falls), A3 (nested donor sets), A4 (the empty donor set), A11 (the matched random controls),
A12 (the derived sources) and A13 (the first touched position), plus the switched mass and over-removal and the donor-set
schedule. One matrix with four subcomponents, two positions, as in the running example; where a second module is needed its
size differs."""

import numpy as np
import pytest
import torch

from vpd_audit.masks import first_touched, hard_zero_masks, over_removal, switched_mass
from vpd_audit.sources import (
    RUNG_SCHEDULE,
    Cache,
    adaptive_rungs,
    code_specific_source,
    donor_set,
    family_masks,
    matched_random_source,
    n_on,
    rho_tensors,
    soft_erase_source,
    source_hash,
    sub_rung_sets,
    union_source,
)

M = {"h.0.attn.q_proj": 4}  # the running example's one matrix
# the running sequence: g at t = 0 and t = 1
G_SEQ = torch.tensor([[[1.0, 0.7, 0.0, 0.0], [0.2, 0.0, 0.9, 0.0]]])  # (B=1, T=2, C=4)
# the two donor positions of the running example
DONORS = np.array([[0.0, 0.9, 0.8, 0.1], [0.3, 0.0, 0.05, 0.0]], dtype=np.float32)


def _cache(rows: np.ndarray) -> Cache:
    return Cache.from_dense(rows.reshape(rows.shape[0], -1), M)


def _rho_t(rho):
    return rho_tensors(rho, M, torch.float32, "cpu")


def test_a1_worked_example_at_tau_half():
    cache = _cache(DONORS)
    rho = union_source(cache, [0, 1], 0.5)
    assert rho.tolist() == [False, True, True, False]
    assert n_on(rho, M) == {"h.0.attn.q_proj": 2, "total": 2}
    masks, deltas, permitted = family_masks("union", {"h.0.attn.q_proj": G_SEQ}, _rho_t(rho), background="r0", delta="excluded")
    assert torch.equal(masks["h.0.attn.q_proj"][0, 0], torch.tensor([1.0, 1.0, 1.0, 0.0])) and deltas is None and permitted
    erase = soft_erase_source(rho)
    assert erase.tolist() == [True, False, False, True]
    masks, _, _ = family_masks("soft_erase", {"h.0.attn.q_proj": G_SEQ}, _rho_t(rho), background="r1", delta="excluded")
    assert torch.equal(masks["h.0.attn.q_proj"][0, 0], torch.tensor([1.0, 0.7, 0.0, 1.0]))
    hz = hard_zero_masks({"h.0.attn.q_proj": G_SEQ}, _rho_t(rho))
    assert torch.equal(hz["h.0.attn.q_proj"][0], torch.tensor([[1.0, 0.0, 0.0, 1.0], [1.0, 0.0, 0.0, 1.0]]))
    # the table's second position under the union at tau = 0.5: c1 stays at 0.2
    assert torch.equal(family_masks("union", {"h.0.attn.q_proj": G_SEQ}, _rho_t(rho), background="r0", delta="excluded")[0]["h.0.attn.q_proj"][0, 1], torch.tensor([0.2, 1.0, 1.0, 0.0]))


def test_a2_thresholds_strict_and_nested_as_tau_falls():
    cache = _cache(DONORS)
    r01 = union_source(cache, [0, 1], 0.1)
    r0 = union_source(cache, [0, 1], 0.0)
    r05 = union_source(cache, [0, 1], 0.5)
    assert r01.tolist() == [True, True, True, False]  # 0.1 > 0.1 is false: c4 not named
    assert r0.tolist() == [True, True, True, True]
    assert np.all(r05 <= r01) and np.all(r01 <= r0)
    # the current input's own g is never binarized: at tau = 0.1 the union mask at t = 1 lifts c1 from 0.2 to 1
    masks, _, _ = family_masks("union", {"h.0.attn.q_proj": G_SEQ}, _rho_t(r01), background="r0", delta="excluded")
    assert torch.equal(masks["h.0.attn.q_proj"][0, 1], torch.tensor([1.0, 1.0, 1.0, 0.0]))


def test_a3_nesting_of_donor_sets():
    cache = _cache(DONORS)
    r1 = union_source(cache, [0], 0.1)  # J1 = {d1}
    r2 = union_source(cache, [0, 1], 0.1)  # J2 = {d1, d2}
    assert np.all(r1 <= r2) and r1.tolist() == [False, True, True, False]
    g = {"h.0.attn.q_proj": G_SEQ}
    u1 = family_masks("union", g, _rho_t(r1), background="r0", delta="excluded")[0]["h.0.attn.q_proj"]
    u2 = family_masks("union", g, _rho_t(r2), background="r0", delta="excluded")[0]["h.0.attn.q_proj"]
    e1 = family_masks("soft_erase", g, _rho_t(r1), background="r1", delta="excluded")[0]["h.0.attn.q_proj"]
    e2 = family_masks("soft_erase", g, _rho_t(r2), background="r1", delta="excluded")[0]["h.0.attn.q_proj"]
    assert bool((u1 <= u2).all()) and bool((e1 >= e2).all())


def test_a4_empty_donor_set():
    cache = _cache(DONORS)
    rho = union_source(cache, [], 0.1)
    assert not rho.any()
    g = {"h.0.attn.q_proj": G_SEQ}
    assert torch.equal(family_masks("union", g, _rho_t(rho), background="r0", delta="excluded")[0]["h.0.attn.q_proj"], G_SEQ)
    assert torch.equal(family_masks("soft_erase", g, _rho_t(rho), background="r1", delta="excluded")[0]["h.0.attn.q_proj"], torch.ones_like(G_SEQ))
    assert torch.equal(hard_zero_masks(g, _rho_t(rho))["h.0.attn.q_proj"], torch.ones_like(G_SEQ))
    # the default residual rule through family_masks
    for fam, bg, expect in (("union", "r0", 0.0), ("soft_erase", "r1", 1.0), ("hard_zero", "ones", 1.0)):
        _, deltas, _ = family_masks(fam, g, _rho_t(rho), background=bg, delta="included")
        assert deltas is not None and torch.equal(deltas["h.0.attn.q_proj"], torch.full((1, 2), expect))


def test_switched_mass_and_over_removal():
    g = {"h.0.attn.q_proj": G_SEQ}
    union = _rho_t(np.array([False, True, True, False]))
    control = _rho_t(np.array([False, True, False, True]))
    assert switched_mass(g, union, family="union", background="r0")[0] == pytest.approx(1.2)  # (1.3 + 1.1) / 2
    assert switched_mass(g, control, family="union", background="r0")[0] == pytest.approx(1.65)  # (1.3 + 2.0) / 2
    assert over_removal(g, union)[0] == pytest.approx(0.8)  # (0.7 + 0.9) / 2
    # under the uniform background the named entries contribute (1 - g) |1 - u|
    u = {"h.0.attn.q_proj": torch.tensor([[[0.3, 0.6, 0.1, 0.8], [0.5, 0.2, 0.9, 0.4]]])}
    expect = ((1 - 0.7) * 0.4 + (1 - 0.0) * 0.9 + (1 - 0.0) * 0.8 + (1 - 0.9) * 0.1) / 2
    assert switched_mass(g, union, family="union", background="uniform", u=u)[0] == pytest.approx(expect)


def test_a13_first_touched_position():
    # one sequence of six positions, one matrix with three subcomponents c1, c2, c3; erased set S = {c2, c3}
    g = torch.zeros(1, 6, 3)
    g[0, :, 1] = torch.tensor([0.0, 0.05, 0.0, 0.4, 0.0, 0.0])
    g[0, :, 2] = torch.tensor([0.0, 0.0, 0.0, 0.0, 0.9, 0.0])
    S = {"m": torch.tensor([0.0, 1.0, 1.0])}
    assert first_touched({"m": g}, S, 0.1)[0].tolist() == [3]
    assert first_touched({"m": g}, S, 0.0)[0].tolist() == [1]
    assert first_touched({"m": g}, {"m": torch.tensor([1.0, 0.0, 0.0])}, 0.0)[0].tolist() == [6]  # never used -> T
    # the position-level count, positions 3 and 4 at tau_q = 0.1 and positions 1, 3, 4 at tau_q = 0
    assert first_touched({"m": g}, S, 0.1)[1].tolist() == [2] and first_touched({"m": g}, S, 0.0)[1].tolist() == [3]
    assert first_touched({"m": g}, {"m": torch.tensor([1.0, 0.0, 0.0])}, 0.0)[1].tolist() == [0]


def test_a15_conditional_damage():
    """On the six-position example, d_b = 0.02 at tau_q = 0.1 (t* = 3) and 0.01 at tau_q = 0 (t* = 1);
    NaN for a sequence touched at t = 0; the difference of the two per-sequence means when t* = T; the prefix sum is the
    cell's own divergence over t < t*, zero when t* = 0; and the prefix is strict (t < t*, not t <= t*)."""
    from vpd_audit.cells import conditional_damage

    kl_ref = torch.tensor([[0.10, 0.20, 0.10, 0.30, 0.20, 0.10]])
    diff = torch.tensor([[0.01, 0.02, 0.03, 0.30, 0.80, 0.05]])
    kl = kl_ref + diff
    prefix_sum, d = conditional_damage(torch.cat([kl] * 4), torch.cat([kl_ref] * 4), torch.tensor([3, 1, 0, 6]))
    assert d[0].item() == pytest.approx(0.02, abs=1e-6) and d[1].item() == pytest.approx(0.01, abs=1e-6)
    assert torch.isnan(d[2]) and prefix_sum[2].item() == 0.0
    assert d[3].item() == pytest.approx(float(kl.mean() - kl_ref.mean()), abs=1e-6)
    assert prefix_sum[0].item() == pytest.approx(float(kl[0, :3].sum()), abs=1e-6) and prefix_sum[1].item() == pytest.approx(float(kl[0, 0]), abs=1e-6)
    assert prefix_sum[3].item() == pytest.approx(float(kl.sum()), abs=1e-6)
    # t <= t* would give (0.01 + 0.02 + 0.03 + 0.30) / 4 = 0.09 at t* = 3: the strict prefix is what the rule states
    assert d[0].item() != pytest.approx(0.09, abs=1e-3)
    assert prefix_sum.dtype == torch.float32 and d.dtype == torch.float32


def test_a12_derived_sources():
    assert code_specific_source(np.array([1, 1, 1, 0], bool), np.array([1, 0, 0, 1], bool)).tolist() == [False, True, True, False]
    alive = np.ones(4, bool)
    prose_named = np.array([1, 0, 1, 0], bool)
    f_code = np.array([0.6, 0.5, 0.4, 0.1])
    sets, meta = sub_rung_sets(alive, prose_named, f_code, sizes={"S1": 1, "S2": 2, "S3": 3})
    assert sets["S1"].tolist() == [False, True, False, False] and sets["S2"].tolist() == [False, True, False, True]
    assert sets["S3"].tolist() == [False, True, False, True] and meta["shortfall"] == {"S3": 1} and meta["n_candidates"] == 2
    again, _ = sub_rung_sets(alive, prose_named, f_code, sizes={"S1": 1, "S2": 2})
    assert all(np.array_equal(sets[k], again[k]) for k in again)  # identical across two builds
    # ties by ascending index
    sets2, _ = sub_rung_sets(np.ones(4, bool), np.zeros(4, bool), np.array([0.5, 0.5, 0.5, 0.9]), sizes={"S2": 2})
    assert sets2["S2"].tolist() == [True, False, False, True]
    # a subcomponent no code position names (f_code = 0) is never a candidate, so every sub-rung lies inside the rung-8 code-only set (M15)
    sets3, meta3 = sub_rung_sets(np.ones(4, bool), np.zeros(4, bool), np.array([0.0, 0.3, 0.0, 0.2]), sizes={"S3": 3})
    assert sets3["S3"].tolist() == [False, True, False, True] and meta3["shortfall"] == {"S3": 1} and meta3["n_candidates"] == 2
    # rounded-own-g union at t = 1, tau = 0.5, with rho_union = (0, 1, 1, 0): (0, 1, 1, 0) against the fractional (0.2, 1, 1, 0)
    g = {"h.0.attn.q_proj": G_SEQ}
    rho = _rho_t(np.array([False, True, True, False]))
    masks, _, permitted = family_masks("rounded_own_g", g, rho, background="r0", delta="excluded", tau=0.5)
    assert torch.equal(masks["h.0.attn.q_proj"][0, 1], torch.tensor([0.0, 1.0, 1.0, 0.0])) and not permitted
    assert torch.equal(family_masks("union", g, rho, background="r0", delta="excluded")[0]["h.0.attn.q_proj"][0, 1], torch.tensor([0.2, 1.0, 1.0, 0.0]))


def test_a11_matched_random_controls():
    M2 = {"h.0.attn.q_proj": 7, "h.0.mlp.c_fc": 3}
    alive = np.array([1, 1, 0, 1, 1, 1, 0, 1, 1, 0], bool)  # 5 alive in the first matrix, 2 in the second
    counts = {"h.0.attn.q_proj": 3, "h.0.mlp.c_fc": 1}
    rho, meta = matched_random_source(counts, alive, M2, family="union", draw=0, master_seed=0, alive_run="main")
    assert n_on(rho, M2) == {**counts, "total": 4} and np.all(rho <= alive)
    assert meta["alive_sha256"] == source_hash(alive) and meta["alive_run"] == "main" and meta["n_alive"] == 7 and meta["overflow"] == {}
    # nested along the chain: a larger count at a later rung extends the same permutation
    rho2, _ = matched_random_source({"h.0.attn.q_proj": 4, "h.0.mlp.c_fc": 2}, alive, M2, family="union", draw=0, master_seed=0)
    assert np.all(rho <= rho2)
    # the same seeds give the same set; a different draw is a different permutation: its recorded seed tuples differ in every matrix
    rho_k1, meta_k1 = matched_random_source(counts, alive, M2, family="union", draw=1, master_seed=0)
    rho_again, meta_again = matched_random_source(counts, alive, M2, family="union", draw=0, master_seed=0)
    assert np.array_equal(rho, rho_again) and meta_again["seed_tuples"] == meta["seed_tuples"]
    assert all(meta_k1["seed_tuples"][k] != meta["seed_tuples"][k] for k in M2) and meta_k1["seed_tuples"]["h.0.attn.q_proj"] == [0, "rand", "union", 1, "h.0.attn.q_proj"]
    # more than the alive count: all alive then the dead, recorded
    rho3, meta3 = matched_random_source({"h.0.attn.q_proj": 6, "h.0.mlp.c_fc": 3}, alive, M2, family="union", draw=0, master_seed=0)
    assert n_on(rho3, M2)["total"] == 9 and meta3["overflow"] == {"h.0.attn.q_proj": 1, "h.0.mlp.c_fc": 1} and np.all(alive <= rho3)
    # the complement-drawn control: inside alive minus prose-named
    prose = np.array([1, 0, 0, 0, 0, 0, 0, 1, 0, 0], bool)
    rho4, meta4 = matched_random_source({"h.0.attn.q_proj": 2, "h.0.mlp.c_fc": 1}, alive, M2, family="code_specific", draw=0, master_seed=0, candidates=~prose)
    assert np.all(rho4 <= (alive & ~prose)) and meta4["candidates"] == "alive minus prose-named"


def test_donor_set_schedule_and_seeds():
    n = 20
    for r, (unit, count) in RUNG_SCHEDULE.items():
        d = donor_set("D_unif", n, 0, r, 0)
        assert d.unit == unit
        if unit == "position":
            assert d.size == count and all(0 <= p < n * 512 for p in d.positions)
        elif unit == "sequence":
            assert d.size == min(count, n) * 512 and len(d.sequences) == min(count, n)  # a pool of 20 cannot supply 64
        elif unit == "pool":
            assert d.size == n * 512 and len(d.sequences) == n
        else:
            assert d.size == 0
    # nested sequence rungs within a draw, from one permutation
    s4, s5, s6, s7 = (set(donor_set("D_unif", n, 3, r, 0).sequences) for r in ("4", "5", "6", "7"))
    assert s4 <= s5 <= s6 <= s7 and len(s7) == n  # the pool has 20 sequences, so rung 7 takes all
    p1, p2, p3 = (set(donor_set("D_unif", n, 3, r, 0).positions) for r in ("1", "2", "3"))
    assert p1 <= p2 <= p3
    assert donor_set("D_unif", n, 0, "4", 0) == donor_set("D_unif", n, 0, 4, 0)  # the same seed, the same set
    assert donor_set("D_unif", n, 0, "3", 0).positions != donor_set("D_unif", n, 1, "3", 0).positions  # two draws: two permutations (64 of 10,240 positions)
    assert donor_set("D_unif", n, 0, "4", 0).seed_tuple == (0, "seqperm", "D_unif", 0) and donor_set("D_unif", n, 2, "2", 0).seed_tuple == (0, "posperm", "D_unif", 2)
    insert, meta = adaptive_rungs({"6": {0: 95, 1: 92}, "8": {0: 100}})
    assert insert and meta["ratio"] == pytest.approx(0.935)
    assert not adaptive_rungs({"6": {0: 80, 1: 85}, "8": {0: 100}})[0]


def test_a16_never_named_chain_on_a_synthetic_cache():
    """On a synthetic pool (4 sequences, two matrices of 30 and 50), S is the complement of the rung-8
    union at tau; every rung's erased set is inside S and disjoint from that rung's union set; its size is the union's total
    at the same draw and rung; the sets are nested along the chain (1 to 3; 4 to 8 with the bridging rungs); the strict set
    at tau = 0 is inside the set at tau = 0.1; the per-matrix counts sum to the total; a shortfall is recorded when the set
    is exhausted; and the rung-8 cell with Delta excluded erases the same set as the included one."""
    from vpd_audit.cells import Cell, build_sources, enumerate_cells
    from vpd_audit.sources import BRIDGING_RUNGS, never_named_set, never_named_source

    M2 = {"h.0.attn.q_proj": 30, "h.0.mlp.c_fc": 50}
    N = 4
    rng = np.random.default_rng(0)
    G = np.zeros((N * 512, 80), dtype=np.float32)
    for c in list(range(10)) + list(range(40, 50)):  # named above 0.1 somewhere: 20 subcomponents
        pos = rng.choice(N * 512, size=int(rng.integers(1, 40)), replace=False)
        G[pos, c] = rng.uniform(0.11, 1.0, size=pos.size)
    for c in range(10, 15):  # named only in (0, 0.1]: 5 more at tau = 0
        pos = rng.choice(N * 512, size=20, replace=False)
        G[pos, c] = rng.uniform(0.01, 0.1, size=pos.size)
    cache = Cache.from_dense(G, M2, name="D_unif_main")
    caches = {"D_unif_main": cache}
    alive = np.ones(80, dtype=bool)
    cells = [c for c in enumerate_cells(runs=("main",), draws=2, extra_rungs=("5a", "6a")) if c.family == "never_named_hard"]
    assert len(cells) == 9 * 2 + 2 * 2 + 3
    src = build_sources(cells, caches, {"main": (alive, source_hash(alive))}, None, None, M2, log=lambda *_: None)
    S01 = never_named_set(union_source(cache, range(cache.n_positions), 0.1))
    S0 = never_named_set(union_source(cache, range(cache.n_positions), 0.0))
    assert int(S01.sum()) == 60 and int(S0.sum()) == 55 and np.all(S0 <= S01)
    by = {c.name: (c, src[c.name]) for c in cells}
    chain = ["1", "2", "3", "4", "5a", "5", "6a", "6", "7", "B50", "B75", "8"]
    for k in range(2):
        sets = {}
        for r in chain:
            c, s = by[f"main/E/never_named_hard/D_unif/tau0.1/ones/incl/k{0 if r == '8' else k}/r{r}"]
            rho = s.rho
            sets[r] = rho
            assert np.all(rho <= S01) and s.record["never_named"]["size"] == 60 and s.record["never_named"]["sha256"] == source_hash(S01)
            assert sum(v for kk, v in s.record["n_on"].items() if kk != "total") == s.record["n_on"]["total"] == int(rho.sum())
            if r in BRIDGING_RUNGS:
                assert int(rho.sum()) == int(np.floor(BRIDGING_RUNGS[r] * 60)) and s.record["donor_unit"] == "bridge"
            elif r == "8":
                assert int(rho.sum()) == 60 and np.array_equal(rho, S01)
            else:
                union = union_source(cache, donor_set("D_unif", N, k, r, 0).positions, 0.1)
                assert int(rho.sum()) == int(union.sum()) == s.record["matched_union_n_on"]["total"] and not np.any(rho & union)
                assert s.record["never_named_draw"]["shortfall"] == 0 and s.record["never_named_draw"]["seed_tuple"] == [0, "rand", "never_named", k]
        for run_ in (("1", "2", "3"), ("4", "5a", "5", "6a", "6", "7", "B50", "B75", "8")):
            for a, b in zip(run_, run_[1:]):
                assert np.all(sets[a] <= sets[b]), (k, a, b)
    # two draws are two permutations: the bridging sets differ, the rung-8 set is the same whole set
    assert not np.array_equal(by["main/E/never_named_hard/D_unif/tau0.1/ones/incl/k0/rB50"][1].rho, by["main/E/never_named_hard/D_unif/tau0.1/ones/incl/k1/rB50"][1].rho)
    # the Delta-excluded rung 8 erases the same set; the strict cell is the tau = 0 complement, inside the tau = 0.1 set
    excl = by["main/E/never_named_hard/D_unif/tau0.1/ones/excl/k0/r8"][1]
    strict = by["main/E/never_named_hard/D_unif/tau0/ones/incl/k0/r8"][1]
    assert excl.record["source_sha256"] == by["main/E/never_named_hard/D_unif/tau0.1/ones/incl/k0/r8"][1].record["source_sha256"]
    assert np.array_equal(strict.rho, S0) and np.all(strict.rho <= S01) and strict.record["never_named"]["tau"] == 0.0
    # exhaustion: the whole set and the shortfall recorded
    rho_x, meta_x = never_named_source(S01, 1000, draw=0, master_seed=0)
    assert int(rho_x.sum()) == 60 and meta_x["shortfall"] == 940 and meta_x["n_taken"] == 60 and meta_x["never_named_size"] == 60


# ----------------------------------------------------------------------------- the level cells, the ranked never-named pair, and the descriptive position rungs


def _synthetic_pool(seed: int = 0):
    """A synthetic D_unif pool of 4 sequences over two matrices (30 and 50): 20 subcomponents named above 0.1, 5 more only
    in (0, 0.1], the rest never named (the fixture of test_a16, shared by the ranked-pair test)."""
    M2 = {"h.0.attn.q_proj": 30, "h.0.mlp.c_fc": 50}
    N = 4
    rng = np.random.default_rng(seed)
    G = np.zeros((N * 512, 80), dtype=np.float32)
    for c in list(range(10)) + list(range(40, 50)):
        pos = rng.choice(N * 512, size=int(rng.integers(1, 40)), replace=False)
        G[pos, c] = rng.uniform(0.11, 1.0, size=pos.size)
    for c in range(10, 15):
        pos = rng.choice(N * 512, size=20, replace=False)
        G[pos, c] = rng.uniform(0.01, 0.1, size=pos.size)
    return M2, N, Cache.from_dense(G, M2, name="D_unif_main")


def test_level_masks_interior_formula_and_the_four_corners_bitwise():
    """On synthetic tensors, in float32 and bfloat16, the named set sits at s + (1 - s) g (checked at
    s = 0.5 entry by entry against that expression, and s + (1 - s) g >= g everywhere for the three levels, the P3
    condition), the never-named set at g (r0) or at 1 (r1); and the corners built through the level path reproduce the
    existing constructions bitwise: importances (g), the union's rung 8 (where(rho, 1, g)), the soft erase's rung 8
    (where(rho, g, 1)), unmasked (ones)."""
    from vpd_audit.masks import apply_binary_source
    from vpd_audit.sources import LEVELS, family_masks, level_masks

    torch.manual_seed(0)
    M2 = {"h.0.attn.q_proj": 6, "h.0.mlp.c_fc": 10}
    for dtype in (torch.float32, torch.bfloat16):
        g = {k: torch.rand(2, 4, c).to(dtype) for k, c in M2.items()}
        g["h.0.mlp.c_fc"][0, 0, :3] = 1.0  # exact ones and zeros, and values a few ulps below 1
        g["h.0.mlp.c_fc"][0, 1, :3] = 0.0
        g["h.0.attn.q_proj"][1, 2, :2] = torch.nextafter(torch.ones(2, dtype=dtype), torch.zeros(2, dtype=dtype))
        rho = {k: (torch.arange(c) % 2 == 0).to(dtype) for k, c in M2.items()}
        for s in LEVELS:
            for bg in ("r0", "r1"):
                m, deltas, permitted = family_masks("level", g, rho, background=bg, delta="excluded", level=s)
                assert deltas is None and permitted
                for k in M2:
                    named = rho[k].bool()
                    assert m[k].dtype == dtype and bool((m[k].float() >= g[k].float()).all()), (dtype, s, bg, k)  # P3: both halves at or above g
                    rest = g[k] if bg == "r0" else torch.ones_like(g[k])
                    assert torch.equal(m[k][..., ~named], rest[..., ~named])
                    if s == 0.5:
                        expect = s + (1.0 - s) * g[k]
                        assert torch.equal(m[k][..., named], expect[..., named])
                        assert bool((m[k][..., named] > g[k][..., named]).any())
        corners = {(0.0, "r0"): {k: g[k] for k in M2}, (1.0, "r0"): {k: apply_binary_source(g[k], rho[k]) for k in M2},
                   (0.0, "r1"): {k: apply_binary_source(g[k], 1 - rho[k]) for k in M2}, (1.0, "r1"): {k: torch.ones_like(g[k]) for k in M2}}
        for (s, bg), expect in corners.items():
            m = level_masks(g, rho, level=s, background=bg)
            assert all(torch.equal(m[k], expect[k]) and m[k].dtype == expect[k].dtype for k in M2), (dtype, s, bg)
    # the Delta-included path keeps the residual rule of the background
    m, deltas, _ = family_masks("level", g, rho, background="r1", delta="included", level=0.25)
    assert deltas is not None and all(bool((deltas[k] == 1).all()) for k in M2)


def test_switched_mass_of_a_level_cell_scales_the_union_sigma_of_its_set():
    """Sigma of a level cell is |s - r_bg| times the set's sigma under a primary background: s times
    it with the never-named set at its labels, 1 - s times it with the never-named set at 1."""
    from vpd_audit.masks import switched_mass

    torch.manual_seed(1)
    M2 = {"h.0.attn.q_proj": 6, "h.0.mlp.c_fc": 10}
    g = {k: torch.rand(3, 4, c) for k, c in M2.items()}
    rho = {k: (torch.arange(c) % 3 == 0).float() for k, c in M2.items()}
    base = switched_mass(g, rho, family="union", background="r0")
    for s in (0.25, 0.5, 0.75):
        at_labels = switched_mass(g, rho, family="level", background="r0", level=s)
        at_one = switched_mass(g, rho, family="level", background="r1", level=s)
        assert torch.allclose(at_labels, s * base, rtol=1e-6, atol=1e-7) and torch.allclose(at_one, (1 - s) * base, rtol=1e-6, atol=1e-7)
    assert torch.equal(switched_mass(g, rho, family="level", background="r0", level=1.0), base)
    assert bool((switched_mass(g, rho, family="level", background="r1", level=1.0) == 0).all())


def test_ranked_never_named_pair_on_a_synthetic_cache():
    """On the synthetic pool, the four ranked chains erase the never-named set at tau = 0.1 by
    the weight norm and by the positive-label count, top-n and bottom-n: every erased set is inside S; nested along the
    ladder; sized to it (the union's draw-0 total at rungs 1 to 7, floor(0.5 |S|) and floor(0.75 |S|), the shortfall
    recorded where the ladder exceeds |S| on the stand-in); top and bottom disjoint until they meet (2n <= |S|); the
    whole-set source's hash equal to the never-named chain's rung 8; ties by ascending global index; the key's hash and
    the ladder's provenance in the record."""
    from vpd_audit.cells import RANKED_RUNGS, build_sources, enumerate_cells
    from vpd_audit.sources import BRIDGING_RUNGS, never_named_set, positive_label_counts, ranked_never_named_source, ranked_order

    M2, N, cache = _synthetic_pool()
    caches = {"D_unif_main": cache}
    alive = np.ones(80, dtype=bool)
    rng = np.random.default_rng(3)
    norms = rng.uniform(0.1, 5.0, size=80)
    cells = [c for c in enumerate_cells(runs=("main",), draws=2) if c.family in ("never_named_ranked", "never_named_hard")]
    ranked = [c for c in cells if c.family == "never_named_ranked"]
    assert len(ranked) == 4 * 9 and {c.rung for c in ranked} == set(RANKED_RUNGS) and all(c.draw == 0 and c.is_hard_zero and c.delta == "included" and c.background == "ones" for c in ranked)
    with pytest.raises(AssertionError, match="weight norms"):
        build_sources(ranked, caches, {"main": (alive, source_hash(alive))}, None, None, M2, log=lambda *_: None)
    src = build_sources(cells, caches, {"main": (alive, source_hash(alive))}, None, None, M2, log=lambda *_: None, weight_norms={"main": norms})
    S = never_named_set(union_source(cache, range(cache.n_positions), 0.1))
    n_S = int(S.sum())
    assert n_S == 60
    counts = positive_label_counts(cache)
    assert counts.shape == (80,) and int((counts[S] > 0).sum()) == 5  # the five named only in (0, 0.1] are positive somewhere
    keys = {"weight_norm": norms, "positive_count": counts.astype(np.float64)}
    for key_name, key in keys.items():
        sets = {}
        for end in ("top", "bottom"):
            chain = {}
            for r in RANKED_RUNGS:
                c = next(x for x in ranked if x.rank_key == key_name and x.rank_end == end and x.rung == r)
                s = src[c.name]
                rho = s.rho
                assert np.all(rho <= S) and s.record["never_named"]["sha256"] == source_hash(S) and s.record["rank"]["key"] == key_name and s.record["rank"]["end"] == end
                if r in BRIDGING_RUNGS:
                    n = int(np.floor(BRIDGING_RUNGS[r] * n_S))
                    assert s.record["donor_unit"] == "bridge"
                else:
                    n = int(union_source(cache, donor_set("D_unif", N, 0, r, 0).positions, 0.1).sum())
                    assert s.record["matched_union_n_on"]["total"] == n and s.record["matched_union_draw"] == 0
                assert s.record["rank"]["n_requested"] == n and int(rho.sum()) == min(n, n_S) == s.record["rank"]["n_taken"] and s.record["rank"]["shortfall"] == max(0, n - n_S)
                assert s.record["n_on"]["total"] == int(rho.sum()) and s.record["source_sha256"] == source_hash(rho)
                # the first n of the order: the largest (top) or smallest (bottom) keys within S
                order = ranked_order(S, key, end)
                assert np.array_equal(np.flatnonzero(rho), np.sort(order[: min(n, n_S)]))
                if 0 < n < n_S:
                    inside, outside = key[rho], key[S & ~rho]
                    assert (inside.min() >= outside.max()) if end == "top" else (inside.max() <= outside.min())
                chain[r] = rho
            for a, b in zip(RANKED_RUNGS, RANKED_RUNGS[1:]):
                assert np.all(chain[a] <= chain[b]), (key_name, end, a, b)
            sets[end] = chain
        for r in RANKED_RUNGS:
            n = int(sets["top"][r].sum())
            if 2 * n <= n_S:
                assert not np.any(sets["top"][r] & sets["bottom"][r]), (key_name, r)
            else:
                assert np.any(sets["top"][r] & sets["bottom"][r])  # met
        # the whole set, from either end, is the never-named chain's rung 8
        rung8 = src["main/E/never_named_hard/D_unif/tau0.1/ones/incl/k0/r8"].record["source_sha256"]
        for end in ("top", "bottom"):
            whole, meta = ranked_never_named_source(S, key, n_S, end=end)
            assert source_hash(whole) == rung8 and meta["shortfall"] == 0 and meta["n_taken"] == n_S
        whole_x, meta_x = ranked_never_named_source(S, key, 1000, end="top")
        assert source_hash(whole_x) == rung8 and meta_x["shortfall"] == 940
    # one ranking read from both ends, ties by one seeded permutation of the index: a constant key gives
    # that permutation's order restricted to S at the top and its reverse at the bottom, never the index order
    from vpd_audit.masks import seed_from_tuple
    from vpd_audit.sources import ranked_tie_seed

    tie_key = np.zeros(80)
    perm = np.random.default_rng(seed_from_tuple(ranked_tie_seed(0))).permutation(80)
    expect_top = np.flatnonzero(S)[np.argsort(perm[np.flatnonzero(S)], kind="stable")]
    assert np.array_equal(ranked_order(S, tie_key, "top"), expect_top) and np.array_equal(ranked_order(S, tie_key, "bottom"), expect_top[::-1])
    assert not np.array_equal(ranked_order(S, tie_key, "top"), np.flatnonzero(S)) and ranked_tie_seed(0) == (0, "rand", "ranked_ties")
    assert np.array_equal(ranked_order(S, norms, "bottom"), ranked_order(S, norms, "top")[::-1])
    assert not np.array_equal(ranked_order(S, tie_key, "top", master_seed=1), ranked_order(S, tie_key, "top", master_seed=0))
    # the bottom-by-count sets at the ladder's sizes are drawn across modules: the 55 strict members (count 0) span both matrices,
    # and the tied prefix must not be the highest-indexed members of the last one
    strict = S & (counts == 0)
    assert int(strict.sum()) == 55 and strict[:30].any() and strict[30:].any()
    for c in [x for x in ranked if x.rank_key == "positive_count" and x.rank_end == "bottom" and x.rung in ("1", "2", "3")]:
        rho = src[c.name].rho
        n = int(rho.sum())
        assert np.all(rho <= strict) or n > int(strict.sum()), c.name  # a bottom-by-count prefix inside the strict set while it fits
        if n >= 4:
            assert rho[:30].any() and rho[30:].any(), (c.name, n, np.flatnonzero(rho))
            assert not np.array_equal(np.flatnonzero(rho), np.flatnonzero(strict)[-n:]), c.name
    assert src[next(x.name for x in ranked if x.rank_key == "positive_count")].record["rank"]["tie_seed_tuple"] == [0, "rand", "ranked_ties"]
    # the key's hash is recorded and differs between the two keys
    h = {k: src[next(x.name for x in ranked if x.rank_key == k)].record["rank"]["key_sha256"] for k in keys}
    assert h["weight_norm"] != h["positive_count"]


def test_position_rungs_2a_and_2b_are_nested_in_the_position_run():
    """Rungs 2a (16 positions) and 2b (32) come from the same permutation as 1, 2, 3, so the position run
    is nested 1 < 2 < 2a < 2b < 3 with sizes 1, 8, 16, 32, 64; their chain order sits between 2 and 3."""
    from vpd_audit.sources import POSITION_SUB_RUNGS, RUNG_SCHEDULE, rung_order

    assert RUNG_SCHEDULE["2a"] == ("position", 16) and RUNG_SCHEDULE["2b"] == ("position", 32) and set(POSITION_SUB_RUNGS) == {"2a", "2b"}
    for k in range(3):
        ds = {r: set(donor_set("D_unif", 64, k, r, 0).positions) for r in ("1", "2", "2a", "2b", "3")}
        assert [len(ds[r]) for r in ("1", "2", "2a", "2b", "3")] == [1, 8, 16, 32, 64]
        assert ds["1"] <= ds["2"] <= ds["2a"] <= ds["2b"] <= ds["3"]
    assert rung_order("2") < rung_order("2a") < rung_order("2b") < rung_order("3")
    assert sorted(["3", "2b", "1", "2a", "2", "5a", "B50", "8"], key=rung_order) == ["1", "2", "2a", "2b", "3", "5a", "B50", "8"]
