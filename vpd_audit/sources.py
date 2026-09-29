"""Sources: the donor sets, the named and erased sets of every family, the matched controls, and the backgrounds.

Every source is a batch-shared vector rho in {0, 1}^38,912 in the global index (`sorted(module_to_c)` order with
`module_offsets`), split per module into (C_l,) tensors when applied. Nothing here changes the pre-registered formulas;
their worked examples are the fixtures of tests A1 to A4 and A12.

Donor sets: for pool D and draw k, the sequence permutation from (master, "seqperm", D, k) and the position
permutation of all N x 512 positions from (master, "posperm", D, k), both through `seed_from_tuple` and
`numpy.random.default_rng`. Rungs 1 to 3 take the first 1, 8, 64 positions; rungs 4 to 7 the first 1, 4, 16, 64
sequences (all 512 positions of each); rung 8 the whole pool; the adaptive rungs 5a and 6a (2 and 8 sequences) are
inserted when the median over draws of n_on at rung 6 exceeds 90 percent of its value at rung 8, computed from n_on
alone before any cell runs. Union: rho_c = max over the chosen positions of 1[g > tau], strict, from the cache; n_on
per module and its sum. Soft erase: 1 - rho_union. Hard-zero erase: the direct mask 1 - rho_union broadcast, its own
path in masks.py. Code-specific set: rho_union(J_code, tau) (1 - rho_union(D_prose, tau)) with the prose reference the
whole pool. Sub-rungs S4, S16, S64: among alive subcomponents no prose position names, the 4, 16, 64 with the largest
f_code, ties by ascending global index, nested. Rounded-own-g union: m = max(1[g > tau], rho_union), a direct mask.
Matched-random controls: per (k, l, family) one permutation of matrix l's alive set from
(master, "rand", family, k, l), the first n_on^l(k, j) entries at rung j; if n_on^l exceeds the alive count, all alive
then a permutation of the dead; for the code-specific family and the sub-rungs the candidates are alive minus
prose-named. Every control source records the SHA-256 of the alive vector it drew from (the
1,024-sequence alive set of D_unif saved beside its cache). Backgrounds: r0 and r1 are the binary paths;
uniform uses uniform_background((master, "u", k, i)) with the named set pinned, torch.where(rho, value, u), then
apply_source, as smoke.py's M6c builds it.

Two later additions, changing nothing above: the family `rounded0_own_g`, m = max(1[g > 0], rho_union) with the donors' set at the cell's
tau (permitted); and `own_round` on the per-text sibling, the self-merge with the text's own labels rounded first.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from typing import Any

import numpy as np
import torch
from torch import Tensor

from vpd_audit.constants import SEQ_LEN
from vpd_audit.masks import apply_binary_source, apply_source, residual_mask, rounded_mask, seed_from_tuple

RUNG_SCHEDULE: dict[str, tuple[str, int | None]] = {
    "0": ("none", 0), "1": ("position", 1), "2": ("position", 8), "2a": ("position", 16), "2b": ("position", 32), "3": ("position", 64),
    "4": ("sequence", 1), "5": ("sequence", 4), "5a": ("sequence", 2), "6": ("sequence", 16), "6a": ("sequence", 8), "7": ("sequence", 64), "8": ("pool", None),
    # 2 and 4 donor tokens: perm[:2] and perm[:4] of each draw's position permutation, so the position run nests 1 < T2 < T4 < 2 (8 tokens).
    # Kept out of INTERMEDIATE_RUNGS, POSITION_SUB_RUNGS, and the rung tuples that tiers 4 to 6 enumerate.
    "T2": ("position", 2), "T4": ("position", 4),
}
INTERMEDIATE_RUNGS: tuple[str, ...] = ("1", "2", "3", "4", "5", "6", "7")
SUB_RUNGS: dict[str, int] = {"S4": 4, "S16": 16, "S64": 64}
BRIDGING_RUNGS: dict[str, float] = {"B50": 0.5, "B75": 0.75}  # the never-named chain's rungs between 7 and 8, fractions of the set
# two descriptive position rungs between 2 and 3 (16 and 32 positions of the same permutation, so the
# position run stays nested 1, 2, 2a, 2b, 3); outside the pre-registered comparison count, flagged on the Cell
POSITION_SUB_RUNGS: dict[str, float] = {"2a": 0.25, "2b": 0.5}
LEVELS: tuple[float, ...] = (0.25, 0.5, 0.75)  # the level cells' s
ADAPTIVE_FRACTION = 0.90
# the chain order of the two small position rungs, between 1 and 2 at 1 + log2(tokens) / 3 (2 tokens: 1 + 1/3; 4 tokens: 1 + 2/3)
SMALL_POSITION_RUNGS: dict[str, float] = {"T2": 1.0 + 1.0 / 3.0, "T4": 1.0 + 2.0 / 3.0}


def rung_order(r: str) -> float:
    """Chain order of a rung label: 1..7 with 2a and 2b after 2, then 5a after 5 and 6a after 6 (the adaptive rungs), B50 and
    B75 after 7, 8 last; the sub-rungs S4, S16, S64 of the code-specific family (their own chain) after everything, by size.
    T2 and T4 (2 and 4 donor tokens) sit between 1 and 2."""
    if r in SMALL_POSITION_RUNGS:
        return SMALL_POSITION_RUNGS[r]
    if r in POSITION_SUB_RUNGS:
        return 2 + POSITION_SUB_RUNGS[r]
    if r in BRIDGING_RUNGS:
        return 7 + BRIDGING_RUNGS[r]
    if r in SUB_RUNGS:
        return 10 + SUB_RUNGS[r] / 100
    if r[:1] == "G" and r[1:].isdigit():  # a code-leaning rung, named by its size, its own chain after everything
        return 20 + int(r[1:]) / 1e6
    return float(r.rstrip("a")) + (0.5 if r.endswith("a") else 0.0)


def rung_key(rung: int | str) -> str:
    return str(rung)


def module_offsets(module_to_c: dict[str, int]) -> dict[str, int]:
    """The global index of subcomponent 0 of each module in sorted order (the same rule donors.py used to write the
    caches; a loaded Cache carries the offsets its JSON recorded, and the source builders read those)."""
    off, acc = {}, 0
    for k in sorted(module_to_c):
        off[k] = acc
        acc += module_to_c[k]
    return off


def split_by_module(rho: np.ndarray, module_to_c: dict[str, int], offsets: dict[str, int] | None = None) -> dict[str, np.ndarray]:
    off = offsets if offsets is not None else module_offsets(module_to_c)
    return {k: rho[off[k] : off[k] + module_to_c[k]] for k in sorted(module_to_c)}


def source_hash(rho: np.ndarray) -> str:
    return hashlib.sha256(np.ascontiguousarray(rho.astype(np.bool_)).tobytes()).hexdigest()


# ----------------------------------------------------------------------------- a small CSR container


@dataclass
class Cache:
    """One donor pool's importances as CSR over positions (donors.py writes them); `n_sub` is the global width."""

    indptr: np.ndarray
    indices: np.ndarray
    values: np.ndarray
    n_sub: int
    n_sequences: int
    module_to_c: dict[str, int]
    name: str = ""
    sha256: dict[str, str] = field(default_factory=dict)
    offsets: dict[str, int] = field(default_factory=dict)  # from the cache's JSON when loaded

    def __post_init__(self) -> None:
        if not self.offsets:
            self.offsets = module_offsets(self.module_to_c)
        assert self.offsets == module_offsets(self.module_to_c), "the cache's module offsets are not the sorted cumulative sums"
        assert sum(self.module_to_c.values()) == self.n_sub

    @property
    def n_positions(self) -> int:
        return self.indptr.size - 1

    @classmethod
    def from_dense(cls, G: np.ndarray, module_to_c: dict[str, int], name: str = "dense") -> "Cache":
        """(N, T, n_sub) or (P, n_sub) dense g -> CSR, for tests and the identities."""
        if G.ndim == 3:
            n_seq = G.shape[0]
            G = G.reshape(-1, G.shape[-1])
        else:
            n_seq = G.shape[0] // SEQ_LEN if G.shape[0] % SEQ_LEN == 0 else 1
        nz = G != 0
        counts = nz.sum(1)
        indptr = np.zeros(G.shape[0] + 1, dtype=np.int64)
        np.cumsum(counts, out=indptr[1:])
        rows, cols = np.nonzero(nz)
        return cls(indptr=indptr, indices=cols.astype(np.uint16 if G.shape[1] < 65536 else np.int64), values=G[rows, cols].astype(np.float32), n_sub=G.shape[1], n_sequences=n_seq, module_to_c=dict(module_to_c), name=name)

    @classmethod
    def load(cls, name: str, out_dir: Any = None) -> "Cache":
        from vpd_audit.donors import load_cache

        indptr, indices, values, meta = load_cache(name, out_dir)
        return cls(indptr=indptr, indices=indices, values=values, n_sub=int(meta["n_subcomponents"]), n_sequences=int(meta["n_sequences"]), module_to_c=dict(meta["module_to_c"]), name=name,
                   sha256=dict(meta["sha256"]), offsets={k: int(v) for k, v in meta["module_offsets"].items()})

    def entries_of(self, positions: np.ndarray) -> np.ndarray:
        """The indices into indices/values of every entry of the given positions (a ragged gather)."""
        positions = np.asarray(positions, dtype=np.int64)
        if positions.size == 0:
            return np.zeros(0, dtype=np.int64)
        starts, ends = self.indptr[positions], self.indptr[positions + 1]
        lengths = ends - starts
        total = int(lengths.sum())
        if total == 0:
            return np.zeros(0, dtype=np.int64)
        offsets = np.repeat(starts - np.concatenate([[0], np.cumsum(lengths)[:-1]]), lengths)
        return offsets + np.arange(total, dtype=np.int64)


# ----------------------------------------------------------------------------- donor sets


@dataclass(frozen=True)
class DonorSet:
    pool: str
    draw: int
    rung: str
    unit: str  # none | position | sequence | pool
    positions: tuple[int, ...]  # flat position ids into the pool, sorted
    sequences: tuple[int, ...]  # the pool sequences (sequence rungs and the pool), sorted
    seed_tuple: tuple[Any, ...] | None

    @property
    def size(self) -> int:
        return len(self.positions)


def donor_set(pool: str, n_sequences: int, draw: int, rung: int | str, master_seed: int) -> DonorSet:
    r = rung_key(rung)
    unit, count = RUNG_SCHEDULE[r]
    if unit == "none":
        return DonorSet(pool, draw, r, unit, (), (), None)
    if unit == "position":
        seed = (master_seed, "posperm", pool, draw)
        perm = np.random.default_rng(seed_from_tuple(seed)).permutation(n_sequences * SEQ_LEN)
        pos = np.sort(perm[:count])
        return DonorSet(pool, draw, r, unit, tuple(int(p) for p in pos), tuple(sorted({int(p) // SEQ_LEN for p in pos})), seed)
    if unit == "sequence":
        seed = (master_seed, "seqperm", pool, draw)
        perm = np.random.default_rng(seed_from_tuple(seed)).permutation(n_sequences)
        seqs = np.sort(perm[:count])
        pos = (seqs[:, None] * SEQ_LEN + np.arange(SEQ_LEN)[None, :]).reshape(-1)
        return DonorSet(pool, draw, r, unit, tuple(int(p) for p in pos), tuple(int(s) for s in seqs), seed)
    assert unit == "pool"
    return DonorSet(pool, draw, r, unit, tuple(range(n_sequences * SEQ_LEN)), tuple(range(n_sequences)), None)


# ----------------------------------------------------------------------------- the sources


def union_source(cache: Cache, positions: Any, tau: float) -> np.ndarray:
    """rho_union(J, tau)_c = max over (b', t') in J of 1[g > tau], strict; a boolean vector of length n_sub."""
    rho = np.zeros(cache.n_sub, dtype=np.bool_)
    e = cache.entries_of(np.asarray(list(positions), dtype=np.int64))
    if e.size:
        sel = e[cache.values[e] > tau]
        rho[cache.indices[sel].astype(np.int64)] = True
    return rho


def n_on(rho: np.ndarray, module_to_c: dict[str, int], offsets: dict[str, int] | None = None) -> dict[str, int]:
    out = {k: int(v.sum()) for k, v in split_by_module(rho, module_to_c, offsets).items()}
    out["total"] = int(rho.sum())
    return out


def soft_erase_source(rho_union: np.ndarray) -> np.ndarray:
    return ~rho_union


def code_specific_source(rho_code: np.ndarray, rho_prose: np.ndarray) -> np.ndarray:
    return rho_code & ~rho_prose


def sub_rung_sets(alive: np.ndarray, prose_named: np.ndarray, f_code: np.ndarray, sizes: dict[str, int] = SUB_RUNGS) -> tuple[dict[str, np.ndarray], dict[str, Any]]:
    """S4, S16, S64: among alive subcomponents that no prose position names and that some code position names
    (f_code > 0, so that every sub-rung is a subset of the rung-8 code-only set, M15), the largest f_code,
    ties by ascending global index; nested; if fewer candidates than a size, all of them and the shortfall recorded."""
    cand = np.flatnonzero(alive & ~prose_named & (f_code > 0))
    order = cand[np.lexsort((cand, -f_code[cand]))]  # primary key -f_code (descending f_code), then ascending index
    out, meta = {}, {"n_candidates": int(cand.size), "shortfall": {}}
    for name, n in sizes.items():
        take = order[:n]
        if take.size < n:
            meta["shortfall"][name] = n - int(take.size)
        rho = np.zeros(alive.shape[0], dtype=np.bool_)
        rho[take] = True
        out[name] = rho
    meta["order_first_64"] = [int(x) for x in order[:64]]
    return out, meta


MARGINAL_FAMILY = "marginal"  # the seed's third entry for the marginal-matched control (it carries no family)


def marginal_rates(usage: np.ndarray, n_positions: int) -> np.ndarray:
    """The marginal rates: lambda_c = -ln(1 - u_c) in float64, with u_c clipped at 1 - 1/(2N) (N the pool's
    positions) so that a subcomponent named at every position has a finite rate; lambda_c = 0 exactly where u_c = 0, and
    the sampler's candidates are the entries with lambda_c > 0."""
    u = np.asarray(usage, dtype=np.float64)
    assert u.ndim == 1 and n_positions > 0 and np.all(np.isfinite(u)) and np.all((u >= 0.0) & (u <= 1.0)), "a usage is a fraction of the pool's positions"
    lam = -np.log1p(-np.minimum(u, 1.0 - 1.0 / (2.0 * float(n_positions))))
    lam[u == 0.0] = 0.0  # -log1p(-0.0) is already 0.0; written out so that the candidate set never rests on a signed zero
    assert np.all(np.isfinite(lam)) and np.all(lam >= 0.0)
    return lam


def marginal_arrival_times(rates: np.ndarray, rng: Any) -> np.ndarray:
    """T_c = E_c / lambda_c with E_c ~ Exp(1) independent, drawn in float64 from `rng` over the candidates in the order given
    (ascending global index): P(T_c <= k) = 1 - exp(-lambda_c k) = 1 - (1 - u_c)^k, the probability that a union of k
    independently drawn pool positions names c."""
    rates = np.asarray(rates)
    assert rates.dtype == np.float64 and rates.ndim == 1 and np.all(np.isfinite(rates)) and np.all(rates > 0.0), "a candidate's rate must be finite and positive"
    e = np.asarray(rng.exponential(size=rates.size), dtype=np.float64)
    return e / rates


def matched_random_source(n_on_per_module: dict[str, int], alive: np.ndarray, module_to_c: dict[str, int], *, family: str, draw: int, master_seed: int,
                          candidates: np.ndarray | None = None, alive_sha256: str | None = None, alive_run: str | None = None,
                          offsets: dict[str, int] | None = None, weights: np.ndarray | None = None, replicate: int = 0) -> tuple[np.ndarray, dict[str, Any]]:
    """The matched-random control: per matrix l, the first n_on^l entries of one seeded permutation of l's alive set (or of the
    candidate set, alive minus prose-named, for the code-specific family and the sub-rungs); if n_on^l exceeds the
    candidates, all of them then a permutation of the rest. The same permutation serves every rung of the draw, so the
    controls are nested as the donor sets are. Records the alive vector's hash.

    The marginal-matched control: with `weights` (the (n_sub,) float64 vector of rates
    lambda_c of `marginal_rates`), the candidates of matrix l are its entries with lambda_c > 0 (every subcomponent some
    pool position names, *not* intersected with the alive vector, and the union's own members are not excluded), and the
    order is by arrival time T_c = E_c / lambda_c ascending, E_c ~ Exp(1) from the seed (master, "rand", "marginal", draw,
    module, replicate) over the candidates in ascending global index; the first n_on^l arrivals are taken, so one order per
    (draw, matrix, replicate) serves every rung and the sets are nested. The seed carries no family, so the sets are the same
    in every family. Overflow as above: all candidates, then a seeded permutation of the rest, recorded. With
    `weights=None` the sets and the metadata are today's bit for bit and key for key; `replicate` is defined for the
    weighted sampler only."""
    off = offsets if offsets is not None else module_offsets(module_to_c)
    if weights is None:
        assert replicate == 0, "replicate is defined for the marginal (weighted) sampler only"
        pool = alive if candidates is None else (alive & candidates)
    else:
        assert candidates is None, "the marginal sampler's candidates are the entries with a positive rate; it takes no candidate set"
        assert isinstance(replicate, (int, np.integer)) and replicate >= 0, replicate
        weights = np.asarray(weights)
        assert weights.dtype == np.float64 and weights.shape == alive.shape and np.all(np.isfinite(weights)) and np.all(weights >= 0.0), "weights: the (n_sub,) float64 rates, finite and non-negative"
        pool = weights > 0.0
    rho = np.zeros(alive.shape[0], dtype=np.bool_)
    meta: dict[str, Any] = {"family": family, "draw": draw, "alive_sha256": alive_sha256 or source_hash(alive), "alive_run": alive_run, "n_alive": int(alive.sum()),
                            "candidates": "alive" if candidates is None else "alive minus prose-named", "seed_tuples": {}, "overflow": {}}
    if weights is not None:
        meta.update({"candidates": "positive rate (usage above zero at the naming threshold), not intersected with alive", "sampler": "marginal", "replicate": int(replicate),
                     "n_candidates": int(pool.sum()), "weights_sha256": key_sha256(weights)})
    for k in sorted(module_to_c):
        n = int(n_on_per_module.get(k, 0))
        if n == 0:
            continue
        sl = slice(off[k], off[k] + module_to_c[k])
        cand_idx = np.flatnonzero(pool[sl])
        seed = (master_seed, "rand", family, draw, k) if weights is None else (master_seed, "rand", MARGINAL_FAMILY, draw, k, int(replicate))
        meta["seed_tuples"][k] = list(seed)
        rng = np.random.default_rng(seed_from_tuple(seed))
        if weights is None:
            perm = rng.permutation(cand_idx.size)
        else:  # a stable sort: a tie in T (measure zero in float64, but not impossible) goes to the smaller global index
            perm = np.argsort(marginal_arrival_times(weights[sl][cand_idx], rng), kind="stable")
        chosen = cand_idx[perm[:n]]
        if n > cand_idx.size:
            rest = np.flatnonzero(~pool[sl])
            extra = rest[rng.permutation(rest.size)[: n - cand_idx.size]]
            chosen = np.concatenate([chosen, extra])
            meta["overflow"][k] = int(n - cand_idx.size)
        rho[off[k] + chosen] = True
    return rho, meta


def never_named_set(rho_union_8: np.ndarray) -> np.ndarray:
    """The never-named set at tau, the complement of the rung-8 union at tau over the run's own
    pool: the subcomponents no position of the pool names above tau (28,946 on the main run's D_unif at tau = 0.1,
    the set H4 erased). The strict set at tau = 0 is the complement of the tau = 0 rung-8 union."""
    assert rho_union_8.dtype == np.bool_ and rho_union_8.ndim == 1
    return ~rho_union_8


def never_named_source(never_named: np.ndarray, n: int, *, draw: int, master_seed: int) -> tuple[np.ndarray, dict[str, Any]]:
    """The first n entries of one seeded permutation of the never-named set's global indices, seed (master, "rand",
    "never_named", draw): one permutation per draw serves every rung, so the erased sets are nested along the chain as
    the donor sets are, and n is the union chain's *total* count at the same draw and rung (or a fraction of the set at
    the bridging rungs), not its per-matrix counts, since q_proj and k_proj have 512 subcomponents each and their
    never-named remainder is small. If n exceeds the set (it cannot on the paper's model, where the union's counts stop
    near 10,000 against 28,946; it does on the stand-in), the whole set is taken and the shortfall recorded."""
    assert never_named.dtype == np.bool_ and never_named.ndim == 1 and n >= 0
    idx = np.flatnonzero(never_named)
    seed = (master_seed, "rand", "never_named", draw)
    perm = np.random.default_rng(seed_from_tuple(seed)).permutation(idx.size)
    take = idx[perm[: min(n, idx.size)]]
    rho = np.zeros(never_named.shape[0], dtype=np.bool_)
    rho[take] = True
    meta = {"seed_tuple": list(seed), "n_requested": int(n), "n_taken": int(take.size), "shortfall": int(max(0, n - idx.size)),
            "never_named_size": int(idx.size), "never_named_sha256": source_hash(never_named)}
    return rho, meta


def positive_label_counts(cache: Cache) -> np.ndarray:
    """Per subcomponent, the number of pool positions at which its label is positive (g > 0), from
    the CSR cache; (n_sub,) int64. The cache holds the nonzero labels, so this counts its entries above zero."""
    idx = cache.indices.astype(np.int64)[cache.values > 0]
    return np.bincount(idx, minlength=cache.n_sub).astype(np.int64)


def key_sha256(key: np.ndarray) -> str:
    return hashlib.sha256(np.ascontiguousarray(key.astype(np.float64)).tobytes()).hexdigest()


def ranked_tie_seed(master_seed: int) -> tuple[Any, ...]:
    return (master_seed, "rand", "ranked_ties")


def ranked_order(S: np.ndarray, key: np.ndarray, end: str, *, master_seed: int = 0) -> np.ndarray:
    """The members of S in one ranking, read from one end: "top" is descending key, "bottom" the same ranking reversed, so
    the prefixes of the two orders are the nested top-n and bottom-n sets, disjoint exactly while 2n <= |S| (with one
    ranking a tie cannot put a member at both ends). Ties are broken by one seeded permutation of the global index,
    seed (master, "rand", "ranked_ties"), shared by both ends and both keys: the positive-label count ties on thousands
    of members (every strict member has count zero), and a tie broken by the index itself would erase the highest-
    indexed tied members, concentrated in the last module, instead of a spread of them."""
    assert S.dtype == np.bool_ and S.ndim == 1 and key.shape == S.shape and end in ("top", "bottom"), (S.shape, key.shape, end)
    idx = np.flatnonzero(S)
    k = key[idx].astype(np.float64)
    assert np.all(np.isfinite(k)), "a ranking key must be finite on the set"
    tie = np.random.default_rng(seed_from_tuple(ranked_tie_seed(master_seed))).permutation(S.shape[0])  # a rank per global index
    top = idx[np.lexsort((tie[idx], -k))]  # primary key last in lexsort: descending key, then the permutation's rank
    return top if end == "top" else top[::-1]


def ranked_never_named_source(S: np.ndarray, key: np.ndarray, n: int, *, end: str, master_seed: int = 0) -> tuple[np.ndarray, dict[str, Any]]:
    """The first n members of `ranked_order(S, key, end)`, so that top-n and bottom-n are nested
    along the ladder and disjoint until 2n exceeds |S|; if n exceeds |S| the whole set is taken and the shortfall recorded
    (it cannot on the paper's model, where the ladder stops near 10,000 against 28,946; it does on the stand-in)."""
    order = ranked_order(S, key, end, master_seed=master_seed)
    take = order[: min(int(n), order.size)]
    rho = np.zeros(S.shape[0], dtype=np.bool_)
    rho[take] = True
    meta = {"end": end, "n_requested": int(n), "n_taken": int(take.size), "shortfall": int(max(0, n - order.size)), "never_named_size": int(order.size),
            "never_named_sha256": source_hash(S), "key_sha256": key_sha256(key), "tie_seed_tuple": list(ranked_tie_seed(master_seed)),
            "key_first": float(key[take[0]]) if take.size else None, "key_last": float(key[take[-1]]) if take.size else None}
    return rho, meta


# ----------------------------------------------------------------------------- the code-leaning chain and its usage-matched control

CODE_LEANING_FAMILY = "code_leaning_hard"
CODE_LEANING_LADDER_START = 16  # the ladder 16, 64, 256, 1,024, ... by fours
CODE_LEANING_SKIP_FRACTION = (4, 5)  # a ladder size above 80 percent of the next whole-set rung is skipped
CODE_LEANING_SKIP_ABOVE = (5, 4)  # and so is one within 25 percent above the previous whole-set rung
USAGE_BASE_BINS = 5
USAGE_BIN_MIN_ALIVE = 25  # B_l = min(5, max(1, n_l // 25)): a matrix with fewer than 50 alive subcomponents has one bin, quintiles start at 125
USAGE_TOP_SPLIT_MIN_ALIVE = 200  # from here on the top bin is split again at the matrix's 90th and 95th usage percentiles (by rank)


def code_leaning_order(members: np.ndarray, selectivity: np.ndarray, u_code: np.ndarray, *, master_seed: int = 0) -> np.ndarray:
    """The members' global indices ordered by selectivity s_c descending, ties by u_code descending, then by
    the seeded tie permutation of `ranked_order` (seed (master, "rand", "ranked_ties")). The chain's rungs are prefixes of
    this order, so they are nested and the order walks from pure to leaky."""
    assert members.dtype == np.bool_ and members.ndim == 1 and selectivity.shape == members.shape == u_code.shape
    idx = np.flatnonzero(members)
    s, u = selectivity[idx].astype(np.float64), u_code[idx].astype(np.float64)
    assert np.all(np.isfinite(s)) and np.all(np.isfinite(u)), "the ordering keys must be finite on the set"
    tie = np.random.default_rng(seed_from_tuple(ranked_tie_seed(master_seed))).permutation(members.shape[0])
    return idx[np.lexsort((tie[idx], -u, -s))]  # primary key last in lexsort


def code_leaning_ladder(n_group: int, n_wide: int) -> list[tuple[int, bool]]:
    """The chain's rung sizes as (size, descriptive). The ladder 16, 64, 256, ... strictly below
    |G_0.9|, then |G_0.9|; then the same ladder's sizes strictly between |G_0.9| and |G_0.75| as descriptive rungs, then the
    whole of G_0.75 as the last descriptive rung. A ladder size above 80 percent of the next whole-set rung is skipped, and
    so is one within 25 percent above the previous whole-set rung, so that no two rungs are near-duplicates."""
    assert 0 <= n_group <= n_wide
    num, den = CODE_LEANING_SKIP_FRACTION
    up_num, up_den = CODE_LEANING_SKIP_ABOVE
    ladder, size = [], CODE_LEANING_LADDER_START
    while size < n_wide:
        ladder.append(size)
        size *= 4
    out = [(L, False) for L in ladder if L < n_group and den * L <= num * n_group]
    if n_group > 0:
        out.append((n_group, False))
    if n_wide > n_group:
        out += [(L, True) for L in ladder if n_group < L < n_wide and den * L <= num * n_wide and up_den * L > up_num * n_group]
        out.append((n_wide, True))
    return out


def usage_bins(usage: np.ndarray, alive: np.ndarray, module_to_c: dict[str, int], offsets: dict[str, int] | None = None) -> tuple[np.ndarray, dict[str, int]]:
    """Usage bins (the control built on these bins was replaced by the nearest-neighbour twins,
    `code_leaning.usage_twins`; the bins remain as a descriptive column of the label-only table): per matrix, the bin of every
    alive subcomponent by its rank r (from 0) of usage on the neutral pool
    among *all* alive subcomponents of the matrix, ascending, ties by ascending global index: floor(B_l r / n_l) with
    B_l = min(5, max(1, n_l // 25)) base bins; where n_l >= 200 the top bin is split again at the 90th and 95th percentiles
    of rank (bins 4, 5, 6 hold ranks [0.8, 0.9), [0.9, 0.95), [0.95, 1) of n_l). Integer arithmetic throughout. Returns the
    (n_sub,) int64 bins (-1 off the alive set) and the number of bins per matrix; a larger bin is more used."""
    assert alive.dtype == np.bool_ and usage.shape == alive.shape
    off = offsets if offsets is not None else module_offsets(module_to_c)
    bins = np.full(alive.shape[0], -1, dtype=np.int64)
    n_bins: dict[str, int] = {}
    for k in sorted(module_to_c):
        idx = off[k] + np.flatnonzero(alive[off[k] : off[k] + module_to_c[k]])
        n = int(idx.size)
        if n == 0:
            n_bins[k] = 0
            continue
        order = idx[np.lexsort((idx, usage[idx].astype(np.float64)))]  # ascending usage, then ascending global index
        r = np.arange(n, dtype=np.int64)
        B = min(USAGE_BASE_BINS, max(1, n // USAGE_BIN_MIN_ALIVE))
        b = (B * r) // n
        if n >= USAGE_TOP_SPLIT_MIN_ALIVE:
            assert B == USAGE_BASE_BINS
            b = b + (10 * r >= 9 * n).astype(np.int64) + (20 * r >= 19 * n).astype(np.int64)
            B += 2
        bins[order] = b
        n_bins[k] = B
    return bins, n_bins


def level_source_hash(rho: np.ndarray, level: float, never_named_at: str) -> str:
    """A level cell's source is (the named set, the constant s on it, where the never-named set sits),
    so its hash covers all three; P4 then compares sources and digests as for any other cell."""
    h = hashlib.sha256(np.ascontiguousarray(rho.astype(np.bool_)).tobytes())
    h.update(f"|level={level:g}|never_named_at={never_named_at}".encode())
    return h.hexdigest()


def adaptive_rungs(n_on_by_rung_and_draw: dict[str, dict[int, int]], fraction: float = ADAPTIVE_FRACTION) -> tuple[bool, dict[str, Any]]:
    """The pre-registered rule from n_on alone: insert rungs 5a and 6a if the median over draws of n_on
    at rung 6 exceeds `fraction` of its value at rung 8."""
    r6 = float(np.median(list(n_on_by_rung_and_draw["6"].values())))
    r8 = float(np.median(list(n_on_by_rung_and_draw["8"].values())))
    insert = r6 > fraction * r8
    return bool(insert), {"median_n_on_rung_6": r6, "n_on_rung_8": r8, "ratio": r6 / r8 if r8 else float("nan"), "threshold": fraction, "insert_5a_6a": bool(insert)}


# ----------------------------------------------------------------------------- applying a source under a background


def rho_tensors(rho: np.ndarray, module_to_c: dict[str, int], dtype: torch.dtype, device: Any, offsets: dict[str, int] | None = None) -> dict[str, Tensor]:
    return {k: torch.from_numpy(v.astype(np.float32)).to(device=device, dtype=dtype) for k, v in split_by_module(rho, module_to_c, offsets).items()}


def level_masks(g: dict[str, Tensor], rho: dict[str, Tensor], *, level: float, background: str) -> dict[str, Tensor]:
    """The level cells' masks: the named set at s + (1 - s) g (not g + s (1 - g): equal in exact arithmetic, but in binary
    floating point the second misses 1 by an ulp for many g), the never-named set (the complement) at its labels g
    (background r0) or at 1 (background r1). The two corners s = 0 and s = 1, and the never-named-at-1 half, are formed
    with torch.where and exact constants, as the existing cells are built (importances: g; the union's rung 8:
    where(rho, 1, g); the soft erase's rung 8: where(rho, g, 1); unmasked: ones), so the corner check is bitwise. Both
    halves lie at or above g (P3 asserts it in the forward)."""
    assert background in ("r0", "r1"), background
    assert 0.0 <= level <= 1.0, level
    out: dict[str, Tensor] = {}
    for k in sorted(g):
        gk = g[k]
        sel = rho[k].bool()
        assert sel.ndim == 1 and sel.shape[0] == gk.shape[-1], (k, tuple(sel.shape), tuple(gk.shape))
        if level == 0.0:
            named = gk
        elif level == 1.0:
            named = torch.ones_like(gk)
        else:
            named = level + (1.0 - level) * gk  # in g's dtype
        rest = gk if background == "r0" else torch.ones_like(gk)
        out[k] = torch.where(sel, named, rest)
    return out


ROUNDED0_FAMILY = "rounded0_own_g"  # the binary union with the recipient's own labels rounded at 0


def family_masks(family: str, g: dict[str, Tensor], rho: dict[str, Tensor], *, background: str, delta: str, tau: float | None = None,
                 u: dict[str, Tensor] | None = None, u_delta: dict[str, Tensor] | None = None, level: float | None = None) -> tuple[dict[str, Tensor], dict[str, Tensor] | None, bool]:
    """The 24 masks (and residual masks when included) of a cell, with the residual rule; returns
    (masks, deltas, permitted). `rho` is the *named* set of the family: the union set for the union and rounded-own-g
    families, the erased set for the two erases, the alive set for the level family (with `level`)."""
    keys = sorted(g)
    first = g[keys[0]]
    B, T = first.shape[0], first.shape[1]
    dtype, device = first.dtype, first.device
    masks: dict[str, Tensor] = {}
    if family == "level":
        assert level is not None, "a level cell needs its s"
        masks = level_masks(g, rho, level=level, background=background)
        permitted = True
        res_bg = background
    elif family == "union":
        assert background in ("r0", "uniform")
        for k in keys:
            if background == "r0":
                masks[k] = apply_binary_source(g[k], rho[k])
            else:
                assert u is not None
                masks[k] = apply_source(g[k], torch.where(rho[k].bool(), torch.ones_like(u[k]), u[k]))
        permitted = True
        res_bg = "r0" if background == "r0" else "uniform"
    elif family == "soft_erase":
        assert background in ("r1", "uniform")
        for k in keys:
            if background == "r1":
                masks[k] = apply_binary_source(g[k], 1 - rho[k])
            else:
                assert u is not None
                masks[k] = apply_source(g[k], torch.where(rho[k].bool(), torch.zeros_like(u[k]), u[k]))
        permitted = True
        res_bg = "r1" if background == "r1" else "uniform"
    elif family == "hard_zero":
        assert background == "ones"
        from vpd_audit.masks import hard_zero_masks

        masks = hard_zero_masks(g, rho)
        permitted = False
        res_bg = "hard_zero"
    elif family == "rounded_own_g":
        assert background == "r0" and tau is not None
        for k in keys:
            masks[k] = torch.maximum(rounded_mask(g[k], tau), rho[k].view(1, 1, -1).expand_as(g[k]))
        permitted = False
        res_bg = "r0"
    elif family == ROUNDED0_FAMILY:
        # the recipient's own labels rounded at 0 and the donors' named set (built at the cell's tau, the
        # headline's 0.1) switched fully on, m = max(1[g > 0], rho). Since 1[g > 0] >= g, every mask is at or above g: permitted, so the
        # loop's P3 assertion runs on it. With an empty named set the mask is the rounded_0 reference's, rounded_mask(g, 0.0), bitwise.
        assert background == "r0" and tau is not None
        for k in keys:
            masks[k] = torch.maximum(rounded_mask(g[k], 0.0), rho[k].view(1, 1, -1).expand_as(g[k]))
        permitted = True
        res_bg = "r0"
    else:
        raise ValueError(family)
    if delta == "excluded":
        return masks, None, permitted
    assert delta == "included"
    deltas = {k: residual_mask(res_bg, B, T, u_delta=(u_delta[k] if (res_bg == "uniform" and u_delta is not None) else None), dtype=dtype, device=device) for k in keys}
    return masks, deltas, permitted


# ----------------------------------------------------------------------------- per-text sources

PER_TEXT_FAMILIES: tuple[str, ...] = ("self_union", "partner_union")  # a text merged with what its own positions name, or with what another text's name


def per_text_source_hash(rho_rows: np.ndarray) -> str:
    """The SHA-256 of the (N, n_sub) boolean matrix of per-text named sets, row-major: what `s9_pre_reads.self_merge` records
    per set for the self-merge, so that a launch can be held to that table."""
    assert rho_rows.ndim == 2
    return hashlib.sha256(np.ascontiguousarray(rho_rows, dtype=np.bool_).tobytes()).hexdigest()


def rho_tensors_per_text(rho_rows: np.ndarray, module_to_c: dict[str, int], dtype: torch.dtype, device: Any, offsets: dict[str, int] | None = None) -> dict[str, Tensor]:
    """(B, n_sub) booleans, one row per text of the sub-batch, split per module into (B, 1, C_l) tensors in g's dtype: row b of
    each is what `rho_tensors` gives for rho_rows[b]."""
    assert rho_rows.ndim == 2, rho_rows.shape
    off = offsets if offsets is not None else module_offsets(module_to_c)
    return {k: torch.from_numpy(np.ascontiguousarray(rho_rows[:, off[k] : off[k] + module_to_c[k]]).astype(np.float32)).to(device=device, dtype=dtype).unsqueeze(1) for k in sorted(module_to_c)}


OWN_ROUND_VALUES: tuple[float, ...] = (0.0, 0.1)  # the binary self-merge's two thresholds for the text's own labels
OWN_ROUND_PERMITTED: dict[float, bool] = {0.0: True, 0.1: False}  # 1[g > 0] >= g everywhere; 1[g > 0.1] drops the labels in (0, 0.1]


def family_masks_per_text(family: str, g: dict[str, Tensor], rho: dict[str, Tensor], *, background: str, delta: str, own_round: float | None = None) -> tuple[dict[str, Tensor], dict[str, Tensor] | None, bool]:
    """The 24 masks of a per-text union cell: text b keeps its own labels and has the pieces its row of `rho` names switched
    fully on, m = where(rho_b, 1, g). A sibling of `family_masks`, which takes one vector per cell and is left as it is; the
    per-text families exist in one configuration only, fixed in advance (background r0, the residual excluded). Row b of every mask
    equals `family_masks("union", g[b : b + 1], rho_b, background="r0", delta="excluded")`'s. Returns (masks, None, True).

    `own_round` (the self-merge only): None runs the line above exactly as before. With a threshold t
    the text's own labels are rounded at t before the merge, m = where(rho_b, 1, 1[g > t]) = max(1[g > t], rho_b). At t = 0.0 every
    mask is at or above g (permitted, so the loop's P3 assertion runs). At t = 0.1 it is not permitted, and since the self-merge's set
    holds every piece any position of the text labels above 0.1, the mask is rho_b at every position: asserted here on every call."""
    from vpd_audit.masks import apply_binary_source_per_text

    assert family in PER_TEXT_FAMILIES, family
    assert background == "r0" and delta == "excluded", f"the per-text families run under the background r0 with the residual excluded only, got {background!r}, {delta!r}"
    if own_round is None:
        return {k: apply_binary_source_per_text(g[k], rho[k]) for k in sorted(g)}, None, True
    assert family == "self_union" and own_round in OWN_ROUND_VALUES, f"own_round is defined for the self-merge at {OWN_ROUND_VALUES} only, got {family!r}, {own_round!r}"
    masks = {k: apply_binary_source_per_text(rounded_mask(g[k], own_round), rho[k]) for k in sorted(g)}
    if own_round == 0.1:
        for k, m in masks.items():
            assert torch.equal(m, rho[k].expand_as(m)), f"{k}: the self-merge with the text's own labels rounded at 0.1 is not the text's named set at every position (a piece labelled above 0.1 that the set does not hold)"
    return masks, None, OWN_ROUND_PERMITTED[own_round]


def source_record(rho: np.ndarray, module_to_c: dict[str, int], offsets: dict[str, int] | None = None) -> dict[str, Any]:
    return {"n_on": n_on(rho, module_to_c, offsets), "source_sha256": source_hash(rho)}


def dumps_seed(seed: tuple[Any, ...] | None) -> str:
    return json.dumps(list(seed)) if seed is not None else ""
