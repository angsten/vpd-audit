"""The code-leaning chain on synthetic inputs: the chain's order and ladder, the usage bins (a descriptive column since the
usage-matched twins replaced them as the control's matching), the usage-matched control by nearest-neighbour twins, and the
label-only table, null, and existence rule of pre_reads.py."""

import numpy as np
import pytest

from vpd_audit.code_leaning import twins_source, usage_ranks, usage_twins
from vpd_audit.masks import seed_from_tuple
from vpd_audit.sources import code_leaning_ladder, code_leaning_order, ranked_tie_seed, source_hash, usage_bins


def test_ladder_sizes_and_the_two_skips():
    assert code_leaning_ladder(1007, 1862) == [(16, False), (64, False), (256, False), (1007, False), (1862, True)]  # the main run's chain: 1,024 is within 25 percent above 1,007
    assert code_leaning_ladder(800, 1500) == [(16, False), (64, False), (256, False), (800, False), (1024, True), (1500, True)]  # 1,024 > 1.25 * 800: kept
    assert code_leaning_ladder(820, 1500) == [(16, False), (64, False), (256, False), (820, False), (1500, True)]  # 1,024 <= 1.25 * 820 = 1,025: skipped
    assert code_leaning_ladder(103, 464) == [(16, False), (64, False), (103, False), (256, True), (464, True)]  # the stand-in's forced group
    assert code_leaning_ladder(700, 1500) == [(16, False), (64, False), (256, False), (700, False), (1024, True), (1500, True)]
    assert code_leaning_ladder(300, 1100) == [(16, False), (64, False), (300, False), (1100, True)]  # 256 > 240 and 1,024 > 880 are skipped
    assert code_leaning_ladder(320, 1280) == [(16, False), (64, False), (256, False), (320, False), (1024, True), (1280, True)]  # exactly 80 percent is kept
    assert code_leaning_ladder(1000, 1030) == [(16, False), (64, False), (256, False), (1000, False), (1030, True)]
    assert code_leaning_ladder(500, 500) == [(16, False), (64, False), (256, False), (500, False)]  # nothing between: no descriptive rung
    assert code_leaning_ladder(10, 40) == [(10, False), (16, True), (40, True)] and code_leaning_ladder(14, 40) == [(14, False), (40, True)]  # 16 is within 25 percent above 14
    assert code_leaning_ladder(0, 0) == [] and code_leaning_ladder(0, 30) == [(16, True), (30, True)]
    sizes = [s for s, _ in code_leaning_ladder(5000, 9000)]
    assert sizes == sorted(set(sizes)) == [16, 64, 256, 1024, 5000, 9000]  # 4,096 > 4,000 skipped


def test_order_by_selectivity_then_code_usage_then_the_seeded_tie_permutation():
    n = 12
    members = np.ones(n, bool)
    members[5] = False
    s = np.array([1.0, 0.9, 1.0, 0.95, 1.0, 1.0, 0.9, 0.95, 1.0, 0.8, 1.0, 1.0])
    u = np.array([0.1, 0.5, 0.3, 0.2, 0.3, 0.9, 0.5, 0.1, 0.3, 0.7, 0.05, 0.3])
    order = code_leaning_order(members, s, u, master_seed=0)
    assert sorted(order.tolist()) == [i for i in range(n) if i != 5]
    assert np.all(np.diff(s[order]) <= 0)  # pure to leaky
    for a, b in zip(order[:-1], order[1:]):
        if s[a] == s[b]:
            assert u[a] >= u[b]
    tie = np.random.default_rng(seed_from_tuple(ranked_tie_seed(0))).permutation(n)
    tied = [i for i in order if s[i] == 1.0 and u[i] == 0.3]  # 2, 4, 8, 11 tie on both keys
    assert sorted(tied) == [2, 4, 8, 11] and tied == sorted(tied, key=lambda i: tie[i])
    assert order[0] == 2 or s[order[0]] == 1.0 and u[order[0]] == 0.3
    assert order.tolist()[-1] == 9  # the leakiest member last


def _bins_of(n_alive, usage=None, n_dead=3):
    M = {"m": n_alive + n_dead}
    alive = np.ones(n_alive + n_dead, bool)
    alive[-n_dead:] = False
    u = np.arange(n_alive + n_dead, dtype=np.float64) if usage is None else usage
    return usage_bins(u, alive, M), alive, M


@pytest.mark.parametrize("n,expected", [(15, [15]), (36, [36]), (49, [49]), (50, [25, 25]), (124, [31, 31, 31, 31]), (125, [25] * 5), (199, [40, 40, 40, 40, 39]),
                                        (200, [40, 40, 40, 40, 20, 10, 10]), (1850, [370, 370, 370, 370, 185, 93, 92])])
def test_usage_bins_base_count_and_the_top_split(n, expected):
    (bins, n_bins), alive, _ = _bins_of(n)
    assert n_bins == {"m": len(expected)} and np.bincount(bins[alive]).tolist() == expected and np.all(bins[~alive] == -1)
    assert np.all(np.diff(bins[alive]) >= 0)  # usage ascending here: a larger bin is more used


def test_usage_bins_rank_by_usage_with_ties_by_ascending_global_index():
    usage = np.concatenate([np.zeros(30), np.full(30, 0.5), np.zeros(3)])  # 60 alive, two bins of 30; ties within each half
    (bins, n_bins), alive, _ = _bins_of(60, usage=usage)
    assert n_bins == {"m": 2} and bins[:30].tolist() == [0] * 30 and bins[30:60].tolist() == [1] * 30
    usage = np.concatenate([np.full(60, 0.25), np.zeros(3)])  # all tied: the index alone decides
    (bins, _), _, _ = _bins_of(60, usage=usage)
    assert bins[:60].tolist() == [0] * 30 + [1] * 30
    # two matrices are binned separately, each over its own alive members
    M2 = {"a": 60, "b": 40}
    alive = np.ones(100, bool)
    u = np.concatenate([np.arange(60)[::-1], np.arange(40)]).astype(np.float64)
    b2, nb2 = usage_bins(u, alive, M2)
    assert nb2 == {"a": 2, "b": 1} and b2[:60].tolist() == [1] * 30 + [0] * 30 and b2[60:].tolist() == [0] * 40


def _twin_setup(seed=3):
    rng = np.random.default_rng(seed)
    M = {"a": 250, "b": 60}
    alive = np.ones(310, bool)
    alive[rng.choice(310, 20, replace=False)] = False
    usage = rng.random(310) ** 3
    wide = alive & (rng.random(310) < 0.25)  # "G_0.75"
    order = np.flatnonzero(wide)[rng.permutation(int(wide.sum()))]  # some chain order over it
    return M, alive, usage, wide, order


def _brute_force_twins(order, wide, alive, usage, M, draw, window=8):
    """The twin rule written out plainly: python loops, one member at a time."""
    n = alive.size
    tie = np.random.default_rng(seed_from_tuple(ranked_tie_seed(0))).permutation(n)
    bounds, acc = {}, 0
    for k in sorted(M):
        bounds[k] = (acc, acc + M[k])
        acc += M[k]
    rank = {}
    for k, (lo, hi) in bounds.items():
        members = sorted([i for i in range(lo, hi) if alive[i]], key=lambda i: (usage[i], tie[i]))
        rank.update({i: r for r, i in enumerate(members)})
    used, twins = set(), []
    for m in order.tolist():
        lo, hi = next(v for v in bounds.values() if v[0] <= m < v[1])
        free = [c for c in range(lo, hi) if alive[c] and not wide[c] and c not in used]
        if not free:
            twins.append(-1)
            continue
        nearest = sorted(free, key=lambda c: (abs(rank[c] - rank[m]), tie[c]))[:window]
        j = int(np.random.default_rng(seed_from_tuple((0, "rand", "code_leaning_hard", draw, int(m)))).integers(0, len(nearest)))
        used.add(nearest[j])
        twins.append(nearest[j])
    return np.asarray(twins, dtype=np.int64)


def test_usage_twins_equal_a_brute_force_reading_of_the_twin_rule_and_nest():
    M, alive, usage, wide, order = _twin_setup()
    for draw in (0, 3):
        twins, meta = usage_twins(order, wide, alive, usage, M, draw=draw, master_seed=0)
        assert np.array_equal(twins, _brute_force_twins(order, wide, alive, usage, M, draw))
        assert meta["shortfall"] == {} and meta["window"] == 8 and meta["sampler"] == "usage_nearest" and meta["seed_pattern"] == [0, "rand", "code_leaning_hard", draw, "<member's global index>"]
        assert np.unique(twins).size == twins.size and not wide[twins].any() and np.all(alive[twins])  # no candidate twice, none from G_0.75
        assert np.all((twins < 250) == (order < 250))  # a twin comes from its member's own matrix
        # a member's pick depends only on the members before it: the twins of a prefix are the prefix of the twins, so the rungs' controls nest
        for size in (1, 7, 30):
            short, _ = usage_twins(order[:size], wide, alive, usage, M, draw=draw, master_seed=0)
            assert np.array_equal(short, twins[:size])
        prev = np.zeros(alive.size, bool)
        for size in (4, 16, 40, order.size):
            rho = twins_source(twins, size, alive.size)
            assert int(rho.sum()) == size and np.all(prev <= rho)
            prev = rho
    a, _ = usage_twins(order, wide, alive, usage, M, draw=0, master_seed=0)
    b, _ = usage_twins(order, wide, alive, usage, M, draw=1, master_seed=0)
    again, _ = usage_twins(order, wide, alive, usage, M, draw=0, master_seed=0)
    assert np.array_equal(a, again) and not np.array_equal(a, b)


def test_usage_twins_stay_within_the_window_of_nearest_unused_candidates_by_rank():
    M, alive, usage, wide, order = _twin_setup(seed=9)
    rank, tie = usage_ranks(usage, alive, M, master_seed=0)
    assert np.all(rank[~alive] == -1) and sorted(rank[:250][alive[:250]].tolist()) == list(range(int(alive[:250].sum())))
    lo = np.flatnonzero(alive[:250])
    assert np.all(np.diff(usage[lo][np.argsort(rank[lo])]) >= 0)  # rank ascends with usage, group members included
    twins, _ = usage_twins(order, wide, alive, usage, M, draw=2, master_seed=0)
    used: set[int] = set()
    for m, t in zip(order.tolist(), twins.tolist()):
        sl = range(0, 250) if m < 250 else range(250, 310)
        free = [c for c in sl if alive[c] and not wide[c] and c not in used]
        eighth = sorted(abs(rank[c] - rank[m]) for c in free)[min(8, len(free)) - 1]
        assert abs(rank[t] - rank[m]) <= eighth  # within the eight nearest unused candidates
        used.add(t)
    # W = 1 is the deterministic nearest unused neighbour, the tie in distance going to the tie permutation
    one, _ = usage_twins(order, wide, alive, usage, M, draw=5, master_seed=0, window=1)
    other, _ = usage_twins(order, wide, alive, usage, M, draw=6, master_seed=0, window=1)
    assert np.array_equal(one, other)
    # the usage of a rung's twins tracks its members': the control is matched on usage, which the usage bins were not at small rungs
    ratio = usage[twins[:40]].mean() / usage[order[:40]].mean()
    assert 0.8 < ratio < 1.25, ratio


def test_usage_twins_a_matrix_with_no_unused_candidate_left_records_a_shortfall_and_is_never_filled_from_another():
    M = {"a_small": 6, "b_big": 40}
    alive = np.ones(46, bool)
    usage = np.arange(46, dtype=np.float64)
    wide = np.zeros(46, bool)
    wide[:4] = True  # four members in the small matrix, two candidates there
    wide[10:13] = True
    order = np.array([0, 10, 1, 2, 11, 3, 12])
    twins, meta = usage_twins(order, wide, alive, usage, M, draw=0, master_seed=0)
    assert sorted(twins[[0, 2]].tolist()) == [4, 5] and twins[3] == -1 and twins[5] == -1  # the first two members take the two candidates; the next two find none
    assert meta["shortfall"] == {"a_small": 2} and meta["n_twins"] == 5 and np.all(twins[[1, 4, 6]] >= 6)
    rho = twins_source(twins, 7, 46)
    assert int(rho.sum()) == 5 and int(rho[:6].sum()) == 2
    with pytest.raises(AssertionError):  # a member outside the excluded set is refused: the control would be allowed to draw it
        usage_twins(np.array([20]), wide, alive, usage, M, draw=0, master_seed=0)


# ----------------------------------------------------------------------------- the label-only table, the null, and the existence rule (pre_reads.py)

from vpd_audit.constants import SEQ_LEN  # noqa: E402
from vpd_audit.pre_reads import (  # noqa: E402
    CL_FLOOR_ROWS,
    CL_FLOOR_USAGE,
    code_leaning_pre_read,
    existence_verdict,
    leaning_group,
    leaning_table,
    per_document_counts,
    shuffle_null,
)
from vpd_audit.sources import Cache  # noqa: E402


def test_the_worked_example_of_the_group_rule():
    N = 262_144
    n_code = np.array([5_000, 20_000, 30_000, 100])
    rows_code = np.array([120, 300, 400, 2])
    n_prose = np.array([0, 1_500, 28_000, 0])
    t = leaning_table(n_code, rows_code, n_prose, N, N)
    np.testing.assert_allclose(t["selectivity"], [1.00, 0.93, 0.52, 1.00], atol=5e-3)
    assert t["floor"].tolist() == [True, True, True, False]  # c_d: 100 positions in two files do not estimate a rate
    G = leaning_group(t, 0.9)
    assert G.tolist() == [True, True, False, False]
    assert abs(t["u_a"][G].sum() - 0.095) < 5e-4  # M(G_0.9) = 5,000/262,144 + 20,000/262,144
    # the floor's two edges: 263 positions pass and 262 do not; 8 rows pass and 7 do not
    e = leaning_table(np.array([263, 262, 263]), np.array([8, 8, 7]), np.zeros(3, int), N, N)
    assert e["floor"].tolist() == [True, False, False] and 263 / N >= CL_FLOOR_USAGE > 262 / N and CL_FLOOR_ROWS == 8
    # the selectivity's edge is exact on counts: nine to one is in G_0.9, and the undefined selectivity is in no group
    z = leaning_table(np.array([9_000, 8_999, 0]), np.array([50, 50, 0]), np.array([1_000, 1_001, 0]), N, N)
    assert leaning_group(z, 0.9).tolist() == [True, False, False] and np.isnan(z["selectivity"][2])


def test_the_existence_rule_as_written():
    assert existence_verdict(0.12, 20.0, 3.9) == "clear"
    assert existence_verdict(0.12, 20.0, 4.0) == "marginal"  # the null's 95th percentile must be *below* a fifth of M
    assert existence_verdict(0.10, 20.0, 0.1) == "clear"  # at least 10 percent
    assert existence_verdict(0.0999, 20.0, 0.1) == "marginal"
    assert existence_verdict(0.02, 4.0, 0.0) == "marginal" and existence_verdict(0.0199, 4.0, 0.0) == "none"
    assert existence_verdict(0.0, 0.0, 0.0) == "none"


MODS = {"a": 300, "b": 40}
N_SUB = 340


def _dense(n_rows, rates, rng, burst=None):
    """(n_rows, T, n_sub) float32 labels: each subcomponent fires (label 0.6) at its rate, plus label 0.05 noise below tau."""
    G = np.where(rng.random((n_rows, SEQ_LEN, N_SUB)) < rates[None, None, :], 0.6, 0.0).astype(np.float32)
    G += np.where(rng.random((n_rows, SEQ_LEN, N_SUB)) < 0.02, 0.05, 0.0).astype(np.float32)
    for c, rows in (burst or {}).items():
        G[:, :, c] = 0.0
        G[rows, :, c] = 0.9
    return np.minimum(G, 1.0)


@pytest.fixture(scope="module")
def planted():
    rng = np.random.default_rng(2026)
    code_rate, prose_rate = np.zeros(N_SUB), np.zeros(N_SUB)
    code_rate[0:60], prose_rate[0:60] = 0.05, 0.0  # code only
    code_rate[60:100], prose_rate[60:100] = 0.05, 0.003  # leaning about 0.94
    code_rate[100:160], prose_rate[100:160] = 0.05, 0.012  # leaning about 0.81
    code_rate[160:240], prose_rate[160:240] = 0.04, 0.04  # shared
    code_rate[240:280], prose_rate[240:280] = 0.0, 0.05  # prose only
    code_rate[300:340], prose_rate[300:340] = 0.03, 0.03  # the second matrix: shared
    G_code = _dense(16, code_rate, rng, burst={299: [0, 1]})  # 299: many positions in two rows only, fails the floor on rows
    G_prose = _dense(16, prose_rate, rng, burst={299: []})
    G_unif = _dense(8, (code_rate + prose_rate) / 2, rng)
    G_lab = _dense(8, (code_rate + prose_rate) / 2, rng)
    G_lab[:4] = _dense(4, code_rate, rng)
    alive = np.ones(N_SUB, bool)
    alive[280:299] = False  # never fire
    caches = {k: Cache.from_dense(v, MODS, name=k) for k, v in (("code", G_code), ("prose", G_prose), ("unif", G_unif), ("lab", G_lab))}
    return caches, {"code": G_code, "prose": G_prose, "unif": G_unif, "lab": G_lab}, alive


def test_per_document_counts_against_the_dense_labels(planted):
    caches, dense, alive = planted
    got = per_document_counts(caches["code"], 0.1)
    want = (dense["code"] > np.float32(0.1)).sum(axis=1)
    assert got.dtype == np.int32 and np.array_equal(got, want)
    cols = np.flatnonzero(alive)
    assert np.array_equal(per_document_counts(caches["prose"], 0.1, cols), (dense["prose"] > np.float32(0.1)).sum(axis=1)[:, cols])


def test_shuffle_null_row_minus_one_is_the_observed_group_and_the_null_is_small_for_a_planted_group(planted):
    caches, dense, alive = planted
    cols = np.flatnonzero(alive)
    cc, cp = per_document_counts(caches["code"], 0.1, cols), per_document_counts(caches["prose"], 0.1, cols)
    null = shuffle_null(cc, cp, n_shuffles=40, master_seed=0)
    assert null.shuffle.tolist() == list(range(-1, 40))
    obs = null.iloc[0]
    t = leaning_table(cc.sum(0), (cc > 0).sum(0), cp.sum(0), 16 * SEQ_LEN, 16 * SEQ_LEN)
    assert obs["mass"] == float(t["u_a"][leaning_group(t, 0.9)].sum()) and int(obs["n_true_code_documents_in_pseudo_code"]) == 16
    shuffled = null[null.shuffle >= 0]
    assert shuffled["mass"].max() < 0.2 * obs["mass"]  # documents, not positions, carry the planted split
    assert 4 <= shuffled["n_true_code_documents_in_pseudo_code"].mean() <= 12
    assert shuffle_null(cc, cp, n_shuffles=40, master_seed=0).equals(null) and not shuffle_null(cc, cp, n_shuffles=40, master_seed=1).equals(null)


def test_code_leaning_pre_read_on_a_planted_group_against_a_brute_force_table(planted):
    caches, dense, alive = planted
    rng = np.random.default_rng(1)
    norms = rng.random(N_SUB) + 0.5
    strata = ["Github"] * 4 + ["ArXiv", "ArXiv", "Pile-CC", "Pile-CC"]
    tables, summary = code_leaning_pre_read(caches["code"], caches["prose"], caches["unif"], caches["lab"], strata, alive, source_hash(alive), norms, "main", draws=3, master_seed=0,
                                            n_shuffles=30, log=lambda *_: None)
    # ---- the table against a brute-force computation from the dense labels
    n_code, n_prose = (dense["code"] > np.float32(0.1)).sum(axis=(0, 1)), (dense["prose"] > np.float32(0.1)).sum(axis=(0, 1))
    rows_code = ((dense["code"] > np.float32(0.1)).sum(axis=1) > 0).sum(axis=0)
    T = tables["code_leaning_table"]
    idx = T["index"].to_numpy()
    assert np.array_equal(idx, np.flatnonzero(alive)) and np.array_equal(T.n_code, n_code[idx]) and np.array_equal(T.n_prose, n_prose[idx]) and np.array_equal(T.rows_code, rows_code[idx])
    u_c, u_p = n_code / (16 * SEQ_LEN), n_prose / (16 * SEQ_LEN)
    with np.errstate(invalid="ignore", divide="ignore"):
        s = u_c / (u_c + u_p)
    floor = (u_c >= 1e-3) & (rows_code >= 8)
    for thr in (0.75, 0.9, 0.95, 0.99):
        want = alive & floor & (s >= thr)
        assert np.array_equal(idx[T[f"in_G_{thr:g}"].to_numpy()], np.flatnonzero(want)), thr
        row = tables["code_leaning_groups"].set_index("group").loc[f"G_{thr:g}"]
        assert int(row.n_members) == int(want.sum()) and abs(row.firing_mass - u_c[want].sum()) < 1e-12 and abs(row.share_of_alive_firing_mass - u_c[want].sum() / u_c[alive].sum()) < 1e-12
        assert abs(row.mean_weight_norm - norms[want].mean()) < 1e-12
    G90, G75 = alive & floor & (s >= 0.9), alive & floor & (s >= 0.75)
    assert set(range(0, 100)) <= set(np.flatnonzero(G90)) and 299 not in np.flatnonzero(G75) and not (set(range(160, 280)) & set(np.flatnonzero(G75)))  # the planted structure
    gt = tables["code_leaning_groups"].set_index("group")
    assert int(gt.loc["strict code (code-named, no prose position), no floor"].n_members) == int((alive & (n_code > 0) & (n_prose == 0)).sum())
    assert int(gt.loc["strict code, floor passed"].n_members) == int((alive & floor & (n_prose == 0)).sum()) < int(gt.loc["strict code (code-named, no prose position), no floor"].n_members)  # 299 fails the floor
    assert int(gt.loc["prose-leaning, s <= 0.10"].n_members) >= 40
    pm = tables["code_leaning_groups_per_matrix"].set_index("group")
    assert int(pm.loc["G_0.9", "a"]) == int(G90[:300].sum()) and int(pm.loc["G_0.9", "b"]) == int(G90[300:].sum()) and int(pm.loc["G_0.9", "total"]) == int(G90.sum())
    # ---- the histogram carries all of the code-firing mass of the members with a defined selectivity
    H = tables["code_leaning_histogram"]
    assert abs(H.weight_u_code.sum() - u_c[alive & np.isfinite(s)].sum()) < 1e-9 and int(H.n_members.sum()) == int((alive & np.isfinite(s)).sum())
    assert abs(H[H.bin_low >= 0.9 - 1e-12].weight_u_code_floor_passed.sum() - u_c[G90].sum()) < 1e-9  # the bins from 0.9 up, floor passed, are G_0.9
    # ---- the existence rule's inputs and output
    e = summary["existence"]
    assert e["n_members"] == int(G90.sum()) and abs(e["share"] - u_c[G90].sum() / u_c[alive].sum()) < 1e-12 and e["verdict"] == existence_verdict(e["share"], e["mass"], e["null_p95"]) == "clear"
    # ---- the chain: prefixes of one order, pure to leaky; G_0.9 is a rung; the last rung is G_0.75
    C = tables["code_leaning_chain"]
    assert C.rung_size.tolist() == [a for a, _ in code_leaning_ladder(int(G90.sum()), int(G75.sum()))] and int(G90.sum()) in C.rung_size.tolist() and C.rung_size.iloc[-1] == int(G75.sum())
    assert C[~C.descriptive].rung_size.max() == int(G90.sum()) and np.all(np.diff(C.min_selectivity) <= 0) and C[~C.descriptive].min_selectivity.min() >= 0.9 and C.min_selectivity.min() >= 0.75
    assert abs(C[C.rung_size == int(G90.sum())].code_firing_mass.iloc[0] - e["mass"]) < 1e-9
    # ---- the control: three draws per rung, the rung's count unless a shortfall is recorded, never a member of G_0.75
    P = tables["code_leaning_control_per_draw"]
    assert len(P) == 3 * len(C) and np.all(P.overlap_with_group == 0)
    assert np.all(P.n_control + P.shortfall == P.rung_size)
    B = tables["code_leaning_control_by_rung"]
    assert B.rung_size.tolist() == C.rung_size.tolist() and {"norm_off_by_more_than_10_percent", "usage_off_by_more_than_10_percent", "median_pair_usage_ratio", "gate_pass", "judged_by_the_gate"} <= set(B.columns)
    assert int(tables["code_leaning_control_shortfall"].shortfall.sum()) == int(P.shortfall.sum()) and "code_leaning_control_overflow" not in tables
    assert B.judged_by_the_gate.tolist() == [bool((not d) and n >= 64) for n, d in zip(B.rung_size, B.descriptive)]  # the gate reads the non-descriptive rungs of at least 64 members
    judged = B[B.judged_by_the_gate]
    assert summary["chain"]["control_gate"]["rungs_judged"] == judged.rung_size.tolist()
    assert summary["chain"]["control_gate"]["pass"] == bool(((judged.norm_ratio_control_to_group - 1).abs() <= 0.10).all() and ((judged.usage_ratio_control_to_group - 1).abs() <= 0.10).all())
    W = tables["code_leaning_control_twins"]
    assert len(W) == 3 * int(G75.sum()) and set(W.draw) == {0, 1, 2} and W[W.twin >= 0].groupby("draw").twin.nunique().eq(W[W.twin >= 0].groupby("draw").size()).all()
    for k in range(3):  # each rung's control is its members' twins, and its hash is the per-draw table's
        w = W[W.draw == k].sort_values("position_in_chain")
        for size in C.rung_size:
            rho = np.zeros(N_SUB, bool)
            tw = w.twin.to_numpy()[:size]
            rho[tw[tw >= 0]] = True
            assert source_hash(rho) == P[(P.draw == k) & (P.rung_size == size)].source_sha256.iloc[0]
    # ---- testability on both strata (GitHub; other, with its sources beneath), both tau_q, group and control
    Tt = tables["code_leaning_testability"]
    assert set(Tt.stratum) == {"all", "Github", "other", "ArXiv", "Pile-CC"} and set(Tt.tau_q) == {"tau_q0.1", "tau_q0"} and set(Tt.chain) == {"group", "control"}
    assert len(Tt) == len(C) * 2 * 2 * 5 and set(Tt[Tt.chain == "control"].n_draws) == {3} and set(Tt[Tt.stratum == "other"].n_sequences) == {4}
    # a clean prefix is brute-forced for the first rung on the first text: the first position where any member's label exceeds tau_q
    from vpd_audit.pre_reads import first_touched_from_cache

    s_full = np.where(np.isfinite(s), s, 0.0)
    order = code_leaning_order(G75, s_full, u_c, master_seed=0)
    first = np.zeros(N_SUB, bool)
    first[order[: int(C.rung_size.iloc[0])]] = True
    t_star = first_touched_from_cache(caches["lab"], first, (0.1,))[0.1][0]
    touched = (dense["lab"][:, :, first] > np.float32(0.1)).any(axis=2)
    assert np.array_equal(t_star, np.where(touched.any(axis=1), touched.argmax(axis=1), SEQ_LEN))
    # ---- the stray-code diagnostic: the group's prose firings and their ten fullest rows
    fire = G90 & (n_prose > 0)
    per_row = (dense["prose"][:, :, fire] > np.float32(0.1)).sum(axis=(1, 2))
    R = tables["code_leaning_stray_code_rows"]
    assert summary["stray_code"]["prose_firings_of_the_group"] == int(per_row.sum()) and R.firings_of_the_group.tolist() == sorted(per_row.tolist(), reverse=True)[:10]
    assert len(tables["code_leaning_stray_code_members"]) == int(fire.sum())


def test_code_leaning_pre_read_returns_no_chain_when_the_rule_says_no_group(planted):
    caches, dense, alive = planted
    norms = np.ones(N_SUB)
    # the same pool on both sides: nothing leans, the share is zero, and no chain, control, or testability table is built
    tables, summary = code_leaning_pre_read(caches["code"], caches["code"], caches["unif"], caches["lab"], ["Github"] * 8, alive, source_hash(alive), norms, "main", draws=2, n_shuffles=5, log=lambda *_: None)
    assert summary["existence"]["verdict"] == "none" and "code_leaning_chain" not in tables and "chain" not in summary


def test_a_forced_chain_is_built_where_the_rule_says_no_group_and_the_summary_says_so():
    """The stand-in's case: the existence rule returns none, and the dry run must still exercise the
    code-leaning cells. With `force_chain` the chain, its control, and their testability are built whatever the rule returns;
    without it nothing is."""
    rng = np.random.default_rng(77)
    code_rate, prose_rate = np.full(N_SUB, 0.04), np.full(N_SUB, 0.04)
    code_rate[:3], prose_rate[:3] = 0.02, 0.0  # three code-only subcomponents among 340 shared ones: a share far under 2 percent
    caches = {k: Cache.from_dense(_dense(n, r, rng), MODS, name=k) for k, n, r in (("code", 16, code_rate), ("prose", 16, prose_rate), ("unif", 8, (code_rate + prose_rate) / 2), ("lab", 8, code_rate))}
    alive = np.ones(N_SUB, bool)
    args = (caches["code"], caches["prose"], caches["unif"], caches["lab"], ["Github"] * 4 + ["ArXiv"] * 4, alive, source_hash(alive), np.ones(N_SUB), "simplestories")
    plain_tables, plain = code_leaning_pre_read(*args, draws=2, n_shuffles=5, log=lambda *_: None)
    assert plain["existence"]["verdict"] == "none" and plain["existence"]["n_members"] == 3 and "code_leaning_chain" not in plain_tables and plain["thresholds"] == {"group": 0.9, "wide": 0.75, "default_thresholds": True, "chain_forced": False}
    tables, forced = code_leaning_pre_read(*args, draws=2, n_shuffles=5, group_threshold=0.95, wide_threshold=0.6, force_chain=True, log=lambda *_: None)
    assert forced["existence"]["verdict"] == "none" and forced["thresholds"] == {"group": 0.95, "wide": 0.6, "default_thresholds": False, "chain_forced": True}
    assert tables["code_leaning_chain"].rung_size.tolist()[0] == 3 and len(tables["code_leaning_control_per_draw"]) == 2 * len(tables["code_leaning_chain"]) and len(tables["code_leaning_testability"]) > 0
    assert {"in_forced_group", "in_forced_wide"} <= set(tables["code_leaning_table"].columns) and "in_forced_group" not in plain_tables["code_leaning_table"].columns  # the registered table is unchanged by the option
    assert any(g.startswith("forced group") for g in tables["code_leaning_groups"].group) and not any(g.startswith("forced") for g in plain_tables["code_leaning_groups"].group)
