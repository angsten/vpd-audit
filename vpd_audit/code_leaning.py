"""The code-leaning group, its chain, and its usage-matched control, from the caches alone. One implementation serves the label-only pre-read (`pre_reads.code_leaning_pre_read`) and the
cells (`cells.build_sources`), so the sets a pre-read judged are the sets a launch erases; the launch asserts their hashes.

The group. Over the alive set, from the code pool and the prose pool at the naming threshold 0.1: u_code and u_prose, the
fraction of each pool's positions whose label exceeds the threshold; rows_code, the number of distinct rows (documents) of
the code pool with such a position; the selectivity s = u_code / (u_code + u_prose); the support floor u_code >= 1e-3 and
rows_code >= 8. G_s is the floor-passing members with selectivity at least s; the group is G_0.9, fixed before any prose
usage rate was computed; G_0.75 is the wide set the descriptive rungs run down to and the control excludes.

The chain. G_0.75 ordered by s descending, ties by u_code descending, then the seeded tie permutation of
`sources.ranked_order`; G_0.9 is a prefix of it. The rungs are prefixes (`sources.code_leaning_ladder`).

The control (which replaced an earlier design by usage bins). Candidates: the alive set minus G_0.75. Within
each matrix every alive subcomponent, group members included, is ranked by its usage on the neutral pool D_unif ascending,
ties by the seeded tie permutation. For control draw k the members are processed in chain order; each takes one candidate,
uniformly at random, from the W = 8 nearest not yet used candidates of its own matrix by rank distance, ties in distance by
the tie permutation, the choice seeded by (master, "rand", "code_leaning_hard", draw, the member's global index). A rung's
control is the twins of that rung's members: a member's pick depends only on the members before it in chain order, so the
prefixes nest, and no candidate is used twice within a draw. A matrix with no unused candidate left gives no twin: the
shortfall is recorded, never filled from another matrix.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np

from vpd_audit.constants import SEQ_LEN
from vpd_audit.masks import seed_from_tuple
from vpd_audit.sources import CODE_LEANING_FAMILY, Cache, code_leaning_ladder, code_leaning_order, module_offsets, ranked_tie_seed, source_hash

CL_TAU = 0.1
CL_THRESHOLDS: tuple[float, ...] = (0.75, 0.9, 0.95, 0.99)
CL_GROUP = 0.9  # the group is G_0.9, fixed before any prose usage rate was computed
CL_WIDE = 0.75  # the descriptive rungs run down to here, and the control excludes G_0.75
CL_FLOOR_USAGE = 1e-3
CL_FLOOR_ROWS = 8
CL_WINDOW = 8  # a member's twin is one of the W nearest unused candidates of its matrix by usage rank
# The stand-in (SimpleStories, "dialogue" against "narration") has no member of G_0.9 and the existence rule returns none, so
# its dry run would never build a code-leaning cell. Its pre-read and its dry run are therefore given a forced group: lower
# thresholds and a chain built whatever the rule returns. These numbers carry no
# meaning; they were chosen from the stand-in's selectivity distribution so that the ladder has non-descriptive and
# descriptive rungs. The paper's runs always use CL_GROUP and CL_WIDE with no forcing.
STAND_IN_GROUP = 0.65
STAND_IN_WIDE = 0.55


def pool_usage_above(cache: Cache, tau: float) -> np.ndarray:
    """Per subcomponent, the fraction of the pool's positions at which its label exceeds tau (strict, float32, as the union
    source compares); (n_sub,) float64. The same arithmetic as `pre_reads.pool_usage`, which the cells cannot import."""
    idx = cache.indices.astype(np.int64)[cache.values > np.float32(tau)]
    return np.bincount(idx, minlength=cache.n_sub).astype(np.float64) / float(cache.n_positions)


def per_document_counts(cache: Cache, tau: float, columns: np.ndarray | None = None) -> np.ndarray:
    """(n_documents, n_columns) int32: per document (row of the pool) and subcomponent, the number of the document's positions
    at which the label exceeds tau (strict, float32 as the union source compares). Rows are the honest sample size."""
    N = cache.n_sequences
    assert cache.n_positions == N * SEQ_LEN
    n_cols = cache.n_sub if columns is None else int(columns.size)
    out = np.zeros((N, n_cols), dtype=np.int32)
    for b in range(N):
        e0, e1 = int(cache.indptr[b * SEQ_LEN]), int(cache.indptr[(b + 1) * SEQ_LEN])
        sel = cache.values[e0:e1] > np.float32(tau)
        cnt = np.bincount(cache.indices[e0:e1][sel].astype(np.int64), minlength=cache.n_sub)
        out[b] = cnt if columns is None else cnt[columns]
    return out


def leaning_table(n_a: np.ndarray, rows_a: np.ndarray, n_b: np.ndarray, n_pos_a: int, n_pos_b: int) -> dict[str, np.ndarray]:
    """Usage toward pool a and away from pool b, per subcomponent, from position and row counts: u_a, u_b, the selectivity
    s = u_a / (u_a + u_b) (NaN where neither pool names the subcomponent), and the support floor u_a >= 1e-3 and rows_a >= 8."""
    u_a, u_b = n_a.astype(np.float64) / float(n_pos_a), n_b.astype(np.float64) / float(n_pos_b)
    with np.errstate(divide="ignore", invalid="ignore"):
        s = np.where(u_a + u_b > 0, u_a / (u_a + u_b), np.nan)
    return {"u_a": u_a, "u_b": u_b, "selectivity": s, "floor": (u_a >= CL_FLOOR_USAGE) & (rows_a >= CL_FLOOR_ROWS)}


def leaning_group(t: dict[str, np.ndarray], threshold: float) -> np.ndarray:
    with np.errstate(invalid="ignore"):
        return t["floor"] & (t["selectivity"] >= threshold)


@dataclass
class CodeLeaningSets:
    """The group's label-only quantities over the alive set (arrays of length n_alive unless said otherwise) and its chain."""

    alive_idx: np.ndarray  # (n_alive,) global indices
    c_code: np.ndarray  # (rows_code, n_alive) int32 per-document counts
    c_prose: np.ndarray
    n_code: np.ndarray
    n_prose: np.ndarray
    rows_code: np.ndarray
    rows_prose: np.ndarray
    toward_code: dict[str, np.ndarray]
    toward_prose: dict[str, np.ndarray]
    group: np.ndarray  # bool over alive_idx: G at `group_threshold`
    wide: np.ndarray  # bool over alive_idx: G at `wide_threshold`
    group_threshold: float
    wide_threshold: float
    order: np.ndarray  # the chain: global indices of the wide set, pure to leaky; the group is its first n_group entries
    ladder: list[tuple[int, bool]]  # (rung size, descriptive)
    wide_full: np.ndarray  # (n_sub,) bool
    selectivity_full: np.ndarray  # (n_sub,) float64, 0 where undefined or not alive
    u_code_full: np.ndarray  # (n_sub,) float64

    @property
    def n_group(self) -> int:
        return int(self.group.sum())

    @property
    def n_wide(self) -> int:
        return int(self.wide.sum())

    def named(self, size: int) -> np.ndarray:
        """The rung of `size` members: the first `size` entries of the chain, as an (n_sub,) boolean source."""
        assert 0 < size <= self.order.size
        rho = np.zeros(self.wide_full.shape[0], dtype=np.bool_)
        rho[self.order[:size]] = True
        return rho


def code_leaning_sets(code: Cache, prose: Cache, alive: np.ndarray, *, group_threshold: float = CL_GROUP, wide_threshold: float = CL_WIDE, master_seed: int = 0) -> CodeLeaningSets:
    """The group and its chain from the two domain caches and the alive vector. The thresholds are the ones fixed in advance (0.9 and 0.75) on
    the paper's model; the stand-in, whose labels lean toward neither of its pools, is given lower ones so that its dry run
    exercises the cells (recorded wherever it is done)."""
    assert code.n_sub == prose.n_sub == alive.shape[0] and code.offsets == prose.offsets and alive.dtype == np.bool_
    assert 0.5 < wide_threshold <= group_threshold <= 1.0, (wide_threshold, group_threshold)
    n_sub = code.n_sub
    alive_idx = np.flatnonzero(alive)
    c_code, c_prose = per_document_counts(code, CL_TAU, alive_idx), per_document_counts(prose, CL_TAU, alive_idx)
    n_code, n_prose = c_code.sum(axis=0, dtype=np.int64), c_prose.sum(axis=0, dtype=np.int64)
    for cache, n in ((code, n_code), (prose, n_prose)):  # the per-document counts add up to the pool's usage
        assert np.array_equal(n.astype(np.float64) / cache.n_positions, pool_usage_above(cache, CL_TAU)[alive_idx])
    rows_code, rows_prose = (c_code > 0).sum(axis=0), (c_prose > 0).sum(axis=0)
    toward_code = leaning_table(n_code, rows_code, n_prose, code.n_positions, prose.n_positions)
    toward_prose = leaning_table(n_prose, rows_prose, n_code, prose.n_positions, code.n_positions)
    group, wide = leaning_group(toward_code, group_threshold), leaning_group(toward_code, wide_threshold)
    assert np.all(group <= wide)
    wide_full, s_full, u_full = np.zeros(n_sub, bool), np.zeros(n_sub), np.zeros(n_sub)
    wide_full[alive_idx[wide]] = True
    s_full[alive_idx] = np.where(np.isfinite(toward_code["selectivity"]), toward_code["selectivity"], 0.0)
    u_full[alive_idx] = toward_code["u_a"]
    order = code_leaning_order(wide_full, s_full, u_full, master_seed=master_seed)
    n_group = int(group.sum())
    assert order.size == int(wide.sum()) and set(order[:n_group].tolist()) == set(alive_idx[group].tolist()), "the group is the first |G| members of the chain's order"
    return CodeLeaningSets(alive_idx=alive_idx, c_code=c_code, c_prose=c_prose, n_code=n_code, n_prose=n_prose, rows_code=rows_code, rows_prose=rows_prose, toward_code=toward_code,
                           toward_prose=toward_prose, group=group, wide=wide, group_threshold=float(group_threshold), wide_threshold=float(wide_threshold), order=order,
                           ladder=code_leaning_ladder(n_group, int(wide.sum())), wide_full=wide_full, selectivity_full=s_full, u_code_full=u_full)


def usage_ranks(usage: np.ndarray, alive: np.ndarray, module_to_c: dict[str, int], *, master_seed: int = 0, offsets: dict[str, int] | None = None) -> tuple[np.ndarray, np.ndarray]:
    """Per matrix, the rank (from 0) of every alive subcomponent, group members included, by usage ascending, ties by the
    seeded tie permutation of `sources.ranked_order`; (n_sub,) int64, -1 off the alive set. Also returns that permutation
    (a rank per global index), which breaks ties in rank distance too."""
    assert alive.dtype == np.bool_ and usage.shape == alive.shape
    off = offsets if offsets is not None else module_offsets(module_to_c)
    tie = np.random.default_rng(seed_from_tuple(ranked_tie_seed(master_seed))).permutation(alive.shape[0])
    rank = np.full(alive.shape[0], -1, dtype=np.int64)
    for k in sorted(module_to_c):
        idx = off[k] + np.flatnonzero(alive[off[k] : off[k] + module_to_c[k]])
        order = idx[np.lexsort((tie[idx], usage[idx].astype(np.float64)))]  # ascending usage, then the tie permutation
        rank[order] = np.arange(order.size, dtype=np.int64)
    return rank, tie


def usage_twins(order: np.ndarray, excluded: np.ndarray, alive: np.ndarray, usage: np.ndarray, module_to_c: dict[str, int], *, draw: int, master_seed: int = 0, window: int = CL_WINDOW,
                family: str = CODE_LEANING_FAMILY, offsets: dict[str, int] | None = None) -> tuple[np.ndarray, dict[str, Any]]:
    """For control draw `draw`, the twin of every member of the chain `order` (global indices, in chain
    order), as an int64 array of global indices, -1 where the member's matrix had no unused candidate left. See the module
    docstring for the construction. The twins of a prefix of `order` are the prefix of the twins."""
    assert excluded.dtype == np.bool_ and alive.dtype == np.bool_ and excluded.shape == alive.shape == usage.shape and window >= 1
    order = np.asarray(order, dtype=np.int64)
    assert np.unique(order).size == order.size and np.all(alive[order]) and np.all(excluded[order]), "the chain's members are distinct, alive, and inside the excluded set"
    off = offsets if offsets is not None else module_offsets(module_to_c)
    rank, tie = usage_ranks(usage, alive, module_to_c, master_seed=master_seed, offsets=off)
    keys = sorted(module_to_c)
    starts = np.array([off[k] for k in keys], dtype=np.int64)
    pool = alive & ~excluded
    cand = {k: off[k] + np.flatnonzero(pool[off[k] : off[k] + module_to_c[k]]) for k in keys}
    cand_rank = {k: rank[v] for k, v in cand.items()}
    cand_tie = {k: tie[v] for k, v in cand.items()}
    unused = {k: np.ones(v.size, dtype=np.bool_) for k, v in cand.items()}
    twins = np.full(order.size, -1, dtype=np.int64)
    shortfall: dict[str, int] = {}
    for i, m in enumerate(order.tolist()):
        k = keys[int(np.searchsorted(starts, m, side="right")) - 1]
        free = np.flatnonzero(unused[k])
        if free.size == 0:
            shortfall[k] = shortfall.get(k, 0) + 1
            continue
        dist = np.abs(cand_rank[k][free] - rank[m])
        nearest = free[np.lexsort((cand_tie[k][free], dist))[:window]]  # by rank distance, ties by the tie permutation
        j = int(np.random.default_rng(seed_from_tuple((master_seed, "rand", family, int(draw), int(m)))).integers(0, nearest.size))
        unused[k][nearest[j]] = False
        twins[i] = cand[k][nearest[j]]
    got = twins[twins >= 0]
    assert np.unique(got).size == got.size and not excluded[got].any() and np.all(alive[got]), "a twin is an unused alive candidate outside the excluded set"
    meta = {"family": family, "draw": int(draw), "sampler": "usage_nearest", "window": int(window), "candidates": "alive minus the excluded set (G_0.75)", "n_candidates": int(pool.sum()),
            "excluded_sha256": source_hash(excluded), "seed_pattern": [master_seed, "rand", family, int(draw), "<member's global index>"], "tie_seed_tuple": list(ranked_tie_seed(master_seed)),
            "n_members": int(order.size), "n_twins": int(got.size), "shortfall": shortfall}
    return twins, meta


def twins_source(twins: np.ndarray, size: int, n_sub: int) -> np.ndarray:
    """The control of the rung of `size` members: the twins of the chain's first `size` members, as an (n_sub,) boolean source."""
    rho = np.zeros(n_sub, dtype=np.bool_)
    t = twins[:size]
    rho[t[t >= 0]] = True
    return rho
