"""The marginal-matched control's sampler (`sources.matched_random_source` with `weights` and
`replicate`), on synthetic inputs and, for the regression, on the committed tables of the main run.

1. `weights=None` reproduces the committed tier-2 source hashes: every plain control of `results/grid/main/tier2/{E,E_lab}`
   (601 cells) is rebuilt from committed files alone, the alive vector from `results/grid/pre_reads/main/rank_keys.parquet`
   (its hash is the cells' `control_alive_sha256`) and the per-matrix counts from the cell tables' `n_on__<module>` columns.
   The complement controls are not covered: their prose-named vector lives on the volume only.
"""

from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from vpd_audit.sources import matched_random_source, source_hash

ROOT = Path(__file__).resolve().parent.parent
TIER2 = ROOT / "results" / "grid" / "main" / "tier2"
RANK_KEYS = ROOT / "results" / "grid" / "pre_reads" / "main" / "rank_keys.parquet"
N_PLAIN_TIER2 = {"E": 379, "E_lab": 222}  # the plain controls of tier 2 on the main run, as committed


def _committed_alive_and_modules() -> tuple[np.ndarray, dict[str, int]]:
    rk = pd.read_parquet(RANK_KEYS).sort_values("index")
    assert np.array_equal(rk["index"].to_numpy(), np.arange(len(rk)))
    module_to_c = {str(k): int(v) for k, v in rk.groupby("module", sort=True)["c"].max().add(1).items()}
    return rk["alive"].to_numpy(np.bool_), module_to_c


@pytest.mark.parametrize("eval_set", ["E", "E_lab"])
def test_1_weights_none_reproduces_the_committed_tier_2_source_hashes(eval_set):
    alive, module_to_c = _committed_alive_and_modules()
    assert sum(module_to_c.values()) == alive.size == 38912 and len(module_to_c) == 24
    cells = pd.read_parquet(TIER2 / eval_set / "cells.parquet")
    plain = cells[cells.control == "plain"]
    assert len(plain) == N_PLAIN_TIER2[eval_set]
    assert set(plain.control_alive_sha256) == {source_hash(alive)}, "the committed alive vector is not the one the controls drew from"
    for _, r in plain.iterrows():
        counts = {k: int(r[f"n_on__{k}"]) for k in module_to_c}
        rho, meta = matched_random_source(counts, alive, module_to_c, family=r["family"], draw=int(r["draw"]), master_seed=0, alive_run="main")
        assert source_hash(rho) == r["source_sha256"], r["cell"]
        assert int(rho.sum()) == int(r["n_on"])
        # today's metadata, key for key: weights=None adds nothing to a source's record
        assert sorted(meta) == ["alive_run", "alive_sha256", "candidates", "draw", "family", "n_alive", "overflow", "seed_tuples"], r["cell"]


# ----------------------------------------------------------------------------- the weighted sampler on the worked example fixed in advance

from vpd_audit.masks import seed_from_tuple  # noqa: E402
from vpd_audit.sources import MARGINAL_FAMILY, key_sha256, marginal_arrival_times, marginal_rates, n_on  # noqa: E402

M1 = {"h.0.attn.q_proj": 4}  # one matrix, four candidates (the worked example fixed in advance)
USAGE = np.array([0.9, 0.3, 0.05, 0.01])
N_POOL = 524_288


class _FixedExponentials:
    """A stand-in generator whose exponential draws are the worked example's seeded E_c."""

    def __init__(self, e):
        self.e = np.asarray(e, dtype=np.float64)

    def exponential(self, size):
        assert size == self.e.size
        return self.e.copy()


def test_worked_example_rates_arrival_times_and_inclusion_probabilities():
    lam = marginal_rates(USAGE, N_POOL)
    assert lam.dtype == np.float64
    np.testing.assert_allclose(lam, [2.303, 0.357, 0.0513, 0.01005], rtol=2e-3)
    T = marginal_arrival_times(lam, _FixedExponentials([0.5, 1.2, 0.3, 2.0]))
    np.testing.assert_allclose(T, [0.217, 3.36, 5.85, 199.0], rtol=2e-3)
    assert list(np.argsort(T, kind="stable")) == [0, 1, 2, 3]  # the order is c1, c2, c3, c4
    for k, p in ((1, [0.900, 0.300, 0.050, 0.010]), (8, [1.000, 0.942, 0.337, 0.077])):
        np.testing.assert_allclose(1.0 - np.exp(-lam * k), p, atol=5e-4)  # P(T_c <= k) = 1 - (1 - u_c)^k
        np.testing.assert_allclose(1.0 - np.exp(-lam * k), 1.0 - (1.0 - USAGE) ** k, rtol=1e-12)
    assert marginal_rates(np.array([0.0, 0.5]), N_POOL)[0] == 0.0  # a never-named subcomponent is not a candidate


def test_2_marginals_inclusion_frequency_equals_p_c_of_k_with_an_unconstrained_count():
    lam = marginal_rates(USAGE, N_POOL)
    n_seeds = 20_000
    T = np.stack([marginal_arrival_times(lam, np.random.default_rng(seed_from_tuple((0, "rand", MARGINAL_FAMILY, 0, "h.0.attn.q_proj", r)))) for r in range(n_seeds)])
    for k in (1, 8):
        p = 1.0 - (1.0 - USAGE) ** k
        freq = (T <= k).mean(axis=0)  # the set of candidates arrived by "time" k, whatever its size
        se = np.sqrt(p * (1.0 - p) / n_seeds)
        assert np.all(np.abs(freq - p) <= 4.0 * se + 1e-6), (k, freq.tolist(), p.tolist(), se.tolist())
    # and the race itself: c_1 is first with probability lambda_1 / sum(lambda)
    first = (np.argmin(T, axis=1) == 0).mean()
    p1 = lam[0] / lam.sum()
    assert abs(first - p1) <= 4.0 * np.sqrt(p1 * (1 - p1) / n_seeds)


def _marginal(counts, lam, alive, M=None, **kw):
    return matched_random_source(counts, alive, M or M1, family=kw.pop("family", "union"), draw=kw.pop("draw", 0), master_seed=0, weights=lam, **kw)


def test_3_nesting_one_order_serves_every_rung():
    rng = np.random.default_rng(7)
    M2 = {"h.0.attn.q_proj": 40, "h.0.mlp.c_fc": 60}
    usage = np.where(rng.random(100) < 0.7, rng.random(100) ** 3, 0.0)
    lam = marginal_rates(usage, N_POOL)
    alive = np.ones(100, bool)
    prev = np.zeros(100, bool)
    for a, b in ((1, 2), (3, 5), (9, 17), (int((lam[:40] > 0).sum()), int((lam[40:] > 0).sum()))):
        rho, meta = _marginal({"h.0.attn.q_proj": a, "h.0.mlp.c_fc": b}, lam, alive, M2)
        assert n_on(rho, M2) == {"h.0.attn.q_proj": a, "h.0.mlp.c_fc": b, "total": a + b}
        assert np.all(prev <= rho) and np.all(rho <= (lam > 0)) and meta["overflow"] == {}
        prev = rho
    assert np.array_equal(prev, lam > 0)  # the last rung asked for every candidate
    # the set is the first n arrivals of the recorded seed, over the candidates in ascending global index
    rho, meta = _marginal({"h.0.attn.q_proj": 5}, lam, alive, M2, draw=3, replicate=2)
    seed = (0, "rand", "marginal", 3, "h.0.attn.q_proj", 2)
    assert meta["seed_tuples"] == {"h.0.attn.q_proj": list(seed)}
    cand = np.flatnonzero(lam[:40] > 0)
    T = np.random.default_rng(seed_from_tuple(seed)).exponential(size=cand.size) / lam[cand]
    assert np.array_equal(np.flatnonzero(rho), np.sort(cand[np.argsort(T, kind="stable")[:5]]))


def test_4_replicates_differ_the_same_seed_reproduces_and_the_seed_carries_no_family():
    rng = np.random.default_rng(11)
    M2 = {"h.0.attn.q_proj": 200}
    lam = marginal_rates(rng.random(200) ** 4, N_POOL)
    alive = np.ones(200, bool)
    counts = {"h.0.attn.q_proj": 30}
    r0, m0 = _marginal(counts, lam, alive, M2)
    r0_again, m0_again = _marginal(counts, lam, alive, M2, replicate=0)
    r1, m1 = _marginal(counts, lam, alive, M2, replicate=1)
    k1, _ = _marginal(counts, lam, alive, M2, draw=1)
    assert np.array_equal(r0, r0_again) and m0 == m0_again
    assert not np.array_equal(r0, r1) and not np.array_equal(r0, k1) and r0.sum() == r1.sum() == 30
    assert m0["seed_tuples"]["h.0.attn.q_proj"] == [0, "rand", "marginal", 0, "h.0.attn.q_proj", 0] and m1["seed_tuples"]["h.0.attn.q_proj"][-1] == 1
    assert m0["replicate"] == 0 and m1["replicate"] == 1 and m0["sampler"] == "marginal" and m0["weights_sha256"] == key_sha256(lam) and m0["n_candidates"] == int((lam > 0).sum())
    # the sets are the same in every family: only the recorded family differs
    se, mse = _marginal(counts, lam, alive, M2, family="soft_erase")
    assert np.array_equal(r0, se) and mse["seed_tuples"] == m0["seed_tuples"] and mse["family"] == "soft_erase"
    # and they are not the plain control's
    plain, _ = matched_random_source(counts, alive, M2, family="union", draw=0, master_seed=0)
    assert not np.array_equal(plain, r0)


def test_5_the_clip_a_candidate_named_everywhere_arrives_first_and_stays_finite():
    usage = np.array([1.0, 1e-4, 1e-4, 1e-4, 0.0])
    lam = marginal_rates(usage, N_POOL)
    assert np.all(np.isfinite(lam)) and lam[0] == -np.log1p(-(1.0 - 1.0 / (2.0 * N_POOL))) and abs(lam[0] - np.log(2.0 * N_POOL)) < 1e-9 and lam[4] == 0.0
    with np.errstate(divide="raise", invalid="raise", over="raise"):
        for r in range(200):
            T = marginal_arrival_times(lam[:4], np.random.default_rng(seed_from_tuple((0, "rand", "marginal", 0, "m", r))))
            assert np.all(np.isfinite(T)) and int(np.argmin(T)) == 0
            rho, _ = _marginal({"m": 1}, lam, np.ones(5, bool), {"m": 5}, replicate=r)
            assert np.flatnonzero(rho).tolist() == [0]
    # unclipped, the rate would be infinite
    with np.errstate(divide="ignore"):
        assert np.isinf(-np.log1p(-1.0))


def test_candidates_are_the_positive_rates_not_the_alive_vector_and_overflow_is_recorded():
    M2 = {"a": 6, "b": 4}
    usage = np.array([0.5, 0.0, 0.2, 0.0, 0.1, 0.0, 0.0, 0.3, 0.0, 0.0])
    lam = marginal_rates(usage, N_POOL)
    alive = np.array([0, 1, 1, 1, 1, 1, 1, 0, 1, 1], bool)  # entry 0 and entry 7 are named but dead by their mean
    rho, meta = _marginal({"a": 3, "b": 1}, lam, alive, M2)
    assert np.flatnonzero(rho).tolist() == [0, 2, 4, 7] and meta["overflow"] == {} and meta["n_candidates"] == 4  # a dead-but-named candidate is switched on, as the union can
    # more than the candidates: all of them, then a seeded permutation of the rest, recorded
    rho2, meta2 = _marginal({"a": 5, "b": 1}, lam, alive, M2)
    assert np.all(rho <= rho2) and n_on(rho2, M2) == {"a": 5, "b": 1, "total": 6} and meta2["overflow"] == {"a": 2}
    rho3, _ = _marginal({"a": 5, "b": 1}, lam, alive, M2)
    assert np.array_equal(rho2, rho3)


def test_refusals_candidates_with_weights_and_a_replicate_without_weights():
    alive = np.ones(4, bool)
    lam = marginal_rates(USAGE, N_POOL)
    with pytest.raises(AssertionError):
        matched_random_source({"h.0.attn.q_proj": 2}, alive, M1, family="union", draw=0, master_seed=0, weights=lam, candidates=alive)
    with pytest.raises(AssertionError):
        matched_random_source({"h.0.attn.q_proj": 2}, alive, M1, family="union", draw=0, master_seed=0, replicate=1)
    with pytest.raises(AssertionError):
        matched_random_source({"h.0.attn.q_proj": 2}, alive, M1, family="union", draw=0, master_seed=0, weights=lam.astype(np.float32))
    with pytest.raises(AssertionError):
        matched_random_source({"h.0.attn.q_proj": 2}, alive, M1, family="union", draw=0, master_seed=0, weights=np.array([1.0, np.inf, 0.0, 0.0]))
    with pytest.raises(AssertionError):
        marginal_rates(np.array([0.5, 1.5]), N_POOL)


# ----------------------------------------------------------------------------- the marginal control's label-only pre-read on a synthetic pool

from vpd_audit.constants import SEQ_LEN  # noqa: E402
from vpd_audit.pre_reads import S7_RUNGS, decisive_rungs, marginal_pre_read, per_sequence_g_sums, percentile_of, pool_usage  # noqa: E402
from vpd_audit.sources import Cache, donor_set, union_source  # noqa: E402

MODS = {"h.0.attn.q_proj": 120, "h.0.mlp.c_fc": 200}
N_SUB = 320


@pytest.fixture(scope="module")
def synthetic_pre_read():
    rng = np.random.default_rng(314)
    rate = np.where(rng.random(N_SUB) < 0.8, rng.random(N_SUB) ** 6 * 0.5, 0.0)  # heavy-tailed usage, a fifth never named

    def dense(n):
        return np.where(rng.random((n, SEQ_LEN, N_SUB)) < rate[None, None, :], rng.random((n, SEQ_LEN, N_SUB)) * 0.8 + 0.2, 0.0).astype(np.float32)

    G_pool, G_E = dense(12), dense(6)
    pool, E = Cache.from_dense(G_pool, MODS, name="pool"), Cache.from_dense(G_E, MODS, name="E")
    alive = pool_usage(pool, 0.0) > 0
    alive[:3] = False  # a few named subcomponents are dead by the saved vector: candidates, but not alive
    norms = rng.random(N_SUB) + rate * 4
    tables, summary = marginal_pre_read(pool, per_sequence_g_sums(E), alive, source_hash(alive), norms, "main", draws=3, master_seed=0, n_seeds=12, log=lambda *_: None)
    return tables, summary, pool, G_E, alive, norms


def test_pre_read_sets_are_the_runs_own_and_the_counts_match(synthetic_pre_read):
    tables, summary, pool, G_E, alive, norms = synthetic_pre_read
    comp = tables["marginal_composition"]
    per_draw = comp[comp.draw.astype(str) != "pooled"]
    usage = pool_usage(pool, 0.1)
    assert summary["n_candidates"] == int((usage > 0).sum()) and summary["n_marginal_overflows"] == 0 and summary["n_candidates_not_alive"] == int(((usage > 0) & ~alive).sum())
    for r in S7_RUNGS:
        for k in range(3):
            U = union_source(pool, donor_set("D_unif", pool.n_sequences, k, r, 0).positions, 0.1)
            rows = per_draw[(per_draw.rung == r) & (per_draw.draw.astype(int) == k)]
            u_row = rows[rows.control == "union"].iloc[0]
            assert u_row.source_sha256 == source_hash(U) and int(u_row.n) == int(U.sum())
            assert abs(u_row.mean_usage - usage[U].mean()) < 1e-12 and abs(u_row.p90_norm - np.percentile(norms[U], 90)) < 1e-12 and abs(u_row.median_norm - np.median(norms[U])) < 1e-12
            assert set(rows.n) == {int(U.sum())}  # the plain controls and the marginal control carry the union's count
            # the union's mean switched mass on E, by brute force: sigma_b = (1/T) sum_t sum_{c in U} (1 - g)
            brute = float(((1.0 - G_E[:, :, U].astype(np.float64)).sum(axis=(1, 2)) / SEQ_LEN).mean())
            assert abs(u_row.mean_sigma - brute) < 1e-9
    assert set(comp[(comp.control == "marginal") & (comp.replicate == 1)].rung) == {"1", "2"}  # replicate 1 at rungs 1 and 2 only
    assert set(comp[comp.control == "plain"].family) == {"union", "soft_erase"} and set(comp[(comp.control == "plain") & (comp.family == "soft_erase")].rung) == {"1", "2", "3"}
    pooled = comp[(comp.draw.astype(str) == "pooled") & (comp.control == "union") & (comp.rung == "1")].iloc[0]
    assert int(pooled.n) == int(per_draw[(per_draw.control == "union") & (per_draw.rung == "1")].n.sum())  # pooled: the members of the draws' sets concatenated


def test_pre_read_overlap_constants_are_ratios_of_totals_over_draws(synthetic_pre_read):
    tables, *_ = synthetic_pre_read
    per, by = tables["marginal_overlap_per_draw"], tables["marginal_overlap_by_rung"]
    assert set(zip(by.control, by.family, by.replicate)) == {("marginal", "all", 0), ("marginal", "all", 1), ("plain", "union", 0), ("plain", "soft_erase", 0)}
    for _, row in by.iterrows():
        t = per[(per.control == row.control) & (per.family == row.family) & (per.replicate == row.replicate) & (per.rung == row.rung)]
        assert len(t) == 3 == row.n_draws
        assert abs(row.overlap_mass_pooled - t.sigma_shared.sum() / t.sigma_named.sum()) < 1e-15
        assert abs(row.overlap_mass_mean_of_draw_ratios - (t.sigma_shared / t.sigma_named).mean()) < 1e-15
        assert abs(row.overlap_count_pooled - t.n_shared.sum() / t.n_named.sum()) < 1e-15
        assert 0.0 <= row.overlap_mass_pooled <= 1.0 and np.all(t.n_shared <= t.n_named) and np.all(t.sigma_shared <= t.sigma_named + 1e-12)
    pw = tables["marginal_pairwise_real_draws"]
    assert len(pw) == len(S7_RUNGS) * 3 * 2 and np.all((pw.overlap_count_of_a >= 0) & (pw.overlap_count_of_a <= 1))


def test_pre_read_gate_table_and_seed_spread(synthetic_pre_read):
    tables, summary, *_ = synthetic_pre_read
    gate, seeds = tables["marginal_gate"], tables["marginal_sampler_seeds"]
    assert len(seeds) == 12 * len(S7_RUNGS) and len(gate) == 3 * len(S7_RUNGS) and set(gate[gate.gated].rung) == {"1", "2", "2a"}
    for _, g in gate.iterrows():
        d = seeds[seeds.rung == g.rung][g.statistic].to_numpy()
        assert abs(g.seeds_mean - d.mean()) < 1e-15 and abs(g.ratio_seeds_mean_to_union - d.mean() / g.union_value) < 1e-15
        assert g.within_bounds == (g.bound_low <= g.ratio_seeds_mean_to_union <= g.bound_high)
        assert abs(g.replicate_0_percentile - percentile_of(g.replicate_0_value, d)) < 1e-12
    assert summary["gate"]["pass"] == bool(gate[gate.gated].within_bounds.all())
    assert dict(zip(gate.statistic, zip(gate.bound_low, gate.bound_high)))["mean_usage"] == (0.9, 1.1) and dict(zip(gate.statistic, zip(gate.bound_low, gate.bound_high)))["mean_norm"] == (0.95, 1.05)
    # the usage distribution: the alive set and the candidates beside it
    ud = tables["usage_distribution"]
    assert ud["set"].tolist() == ["alive", "candidates (usage > 0)"] and {"p0", "p50", "p100", "n_above_0.1", "n_above_0.5", "n_above_0.9"} <= set(ud.columns)


def test_percentile_of_and_the_decisive_rung_rule():
    assert percentile_of(2.0, np.array([1.0, 2.0, 3.0, 4.0])) == 37.5 and percentile_of(0.0, np.array([1.0, 2.0])) == 0.0 and percentile_of(9.0, np.array([1.0, 2.0])) == 100.0
    by = pd.DataFrame({"control": ["marginal"] * 5 + ["marginal", "plain"], "family": ["all"] * 6 + ["union"], "replicate": [0] * 5 + [1, 0], "rung": ["1", "2", "2a", "2b", "3", "1", "1"],
                       "overlap_mass_pooled": [0.10, 1.0 / 3.0, 0.34, 0.5, 0.2, 0.9, 0.05]})
    assert decisive_rungs(by) == ["1", "2", "3"]  # at most one third: 1/3 is in, 0.34 is out; replicate 1 and the plain rows are not read
    assert decisive_rungs(by, family="soft_erase") == ["1", "2", "3"] and decisive_rungs(by[by.rung != "3"], family="soft_erase") == ["1", "2"]
    assert decisive_rungs(by.assign(overlap_mass_pooled=0.5)) == []


def test_pre_read_real_position_sets(synthetic_pre_read):
    from vpd_audit.pre_reads import real_position_sets

    tables, summary, pool, G_E, alive, norms = synthetic_pre_read
    real = tables["marginal_real_position_sets"]
    assert len(real) == 201 and real.realized.tolist() == [True] + [False] * 200 and real.first_draw.tolist() == [3 * j for j in range(201)]  # three draws per set in this fixture
    usage = pool_usage(pool, 0.1)
    # set 0 is the realized union at rung 1; any set is the pooled statistic of its draws' rung-1 positions
    comp = tables["marginal_composition"]
    pooled = comp[(comp.draw.astype(str) == "pooled") & (comp.control == "union") & (comp.rung == "1")].iloc[0]
    assert int(real.n.iloc[0]) == int(pooled.n) and abs(real.mean_usage.iloc[0] - pooled.mean_usage) < 1e-12 and abs(real.mean_norm.iloc[0] - pooled.mean_norm) < 1e-12
    row = real.iloc[17]
    members = np.concatenate([np.flatnonzero(union_source(pool, donor_set("D_unif", pool.n_sequences, k, "1", 0).positions, 0.1)) for k in range(51, 54)])
    assert int(row.n) == members.size and abs(row.mean_usage - usage[members].mean()) < 1e-12 and abs(row.mean_norm - norms[members].mean()) < 1e-12
    assert row.positions == " ".join(str(donor_set("D_unif", pool.n_sequences, k, "1", 0).positions[0]) for k in range(51, 54))
    rp = summary["real_position_sets"]
    assert rp["n_sets"] == 200 and rp["draws_used"] == [3, 602] and rp["seed_pattern"] == [0, "posperm", "D_unif", "<draw>"]
    for stat in ("mean_usage", "mean_norm", "n"):
        d = real[~real.realized][stat].to_numpy(float)
        assert abs(rp[stat]["realized_percentile"] - percentile_of(float(real[stat].iloc[0]), d)) < 1e-12 and abs(rp[stat]["sets_mean"] - d.mean()) < 1e-12
    assert real_position_sets(pool, norms, usage, draws=3, n_sets=4).equals(real.iloc[:5].reset_index(drop=True))
