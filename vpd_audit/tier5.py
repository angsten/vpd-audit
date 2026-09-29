"""Tier 5: what the small GPU run needs beside the cells and the loop.

The cells are enumerated in `cells.py` (`tier_5_cells`, the launch subsets `same_domain`, `self_merge`, `plain_terms`) and run by
the one loop, `cells.run_cells`. Here:

- **Per-text sources**. `self_union`: text b is merged with every piece any of its own 512 positions labels above
  0.1. `partner_union`: text b receives another text's set. Partners come from a seeded permutation omega of the partner pool,
  seed (master, "partner", eval set, arm): under shift r the partner of omega(i) is omega((i + r) mod N). Three arms: `within`
  (E, partners within E); `source` (E_lab, partners within the text's own source: one generator, each source block permuted
  separately in row order); `general` (E_lab, partners from D_unif: one generator draws first the permutation of E_lab, then
  omega' of D_unif, and the text at position i of the first takes row omega'((i + r) mod N') of the pool). The named sets come
  from the label caches through `s9_pre_reads.own_named`, the function the committed label-only table was built with; the loop asserts them equal
  to the on-device (g > 0.1).any(dim=1) on every sub-batch.
- **The label-only tables a launch is held to** (`s9_pre_reads`): every union set against `merge_sets.csv` by SHA-256 and count,
  every per-text set against `self_merge_sets.parquet` and the manifest's set-level hash, and, on the paper's model, the three
  files themselves against the SHA-256 of the committed copies.
- **The example positions**: for E, two positions per text with 48 <= t <= 510 from the seed tuple
  (master, "examples", "E"); the committed list's hash is a constant here, asserted at launch.
- **The canary and the D_unif gate**, checked after every sub-batch inside the launch: every re-run cell
  and every reference that a committed store holds must reproduce its committed per-text kl_mean bitwise; on D_unif the eight
  rows that are the one-text donors of draws 0 to 7 must reproduce the committed donor-side values within 0.01 nats. A failure
  raises `GateFailure`, which stops the launch. Equality is printed, never a value; the gate prints its eight differences.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from vpd_audit.constants import SEQ_LEN
from vpd_audit.masks import seed_from_tuple

PARTNER_SHIFTS: tuple[int, ...] = (1, 2, 3, 4)
PARTNER_ARMS: tuple[tuple[str, str, str], ...] = (("E", "within", "E"), ("E_lab", "source", "E_lab"), ("E_lab", "general", "D_unif"))  # (eval set, arm, partner pool)
SELF_TAU = 0.1
EXAMPLE_T_MIN, EXAMPLE_T_MAX, EXAMPLES_PER_TEXT = 48, 510, 2
D_UNIF_GATE_TOLERANCE = 0.01  # nats per text (the committed donor-side stores ran at batch shape (1, 512))
D_UNIF_GATE_RUNG = "4"
# the SHA-256 of the committed label-only tables of `s9_pre_reads` (results/grid/pre_reads/main/s9/, as committed before the tier-5 launch); the launch reads the volume's
# copies, which were pulled unopened into the repository, and holds them to these
S9_TABLES_SHA256: dict[str, dict[str, str]] = {"main": {"merge_sets.csv": "6adfef244c1fb1ac49a3a00676fc90202693c0755b845fb885e3206b9d86b219",
                                                       "self_merge_sets.parquet": "4373e16ff5871486a7e96055c2c15d4b1f1ea612390ce3979259f1e7061550c5",
                                                       "manifest.json": "833a72d02c5f74888021b6b9e5a0da281bbf0497486fe2500da8e08ab8db4204"}}
# the SHA-256 of the committed example positions (results/grid/pre_reads/main/s9b/example_positions.csv), per run
EXAMPLE_POSITIONS_SHA256: dict[str, str] = {"main": "35ce12316ea321157dbe78b13aa42836ffbd373400bbd926236561d6b52e889d"}  # 1,024 texts, master seed 0 (vpd-audit s9-example-positions)


class GateFailure(AssertionError):
    """A canary, a gate, or a launch-time assertion of tier 5 failed: the launch stops (grid.run_grid re-raises it)."""


# ----------------------------------------------------------------------------- partners


def rotate(omega: np.ndarray, shift: int) -> np.ndarray:
    """partner[omega[i]] = omega[(i + shift) mod N] for a permutation omega of range(N): the text omega(i) receives the set of
    omega(i + shift). A bijection, so the partner arm holds the same collection of sets as the self arm, each used once."""
    omega = np.asarray(omega, dtype=np.int64)
    n = omega.size
    assert np.array_equal(np.sort(omega), np.arange(n)), "omega must be a permutation of range(N)"
    partner = np.empty(n, dtype=np.int64)
    partner[omega] = omega[(np.arange(n) + int(shift)) % n]
    return partner


def partner_seed(master_seed: int, eval_set: str, arm: str) -> tuple[Any, ...]:
    return (master_seed, "partner", eval_set, arm)


def partner_assignment(eval_set: str, arm: str, shift: int, n_eval: int, *, n_pool: int | None = None, blocks: list[tuple[str, int, int]] | None = None, master_seed: int = 0) -> np.ndarray:
    """(n_eval,) int64: the row of the partner pool whose named set each text receives. One generator per seed tuple; the
    permutations do not depend on the shift, so the four shifts rotate one omega."""
    rng = np.random.default_rng(seed_from_tuple(partner_seed(master_seed, eval_set, arm)))
    if arm == "within":
        assert n_pool in (None, n_eval)
        return rotate(rng.permutation(n_eval), shift)
    if arm == "source":
        assert blocks is not None and n_pool in (None, n_eval), "the source arm permutes each source block of the evaluation set separately"
        assert blocks[0][1] == 0 and blocks[-1][2] == n_eval and all(a[2] == b[1] for a, b in zip(blocks[:-1], blocks[1:])), f"the blocks must tile range({n_eval}): {blocks}"
        partner = np.empty(n_eval, dtype=np.int64)
        for _, a, b in blocks:  # in row order, from the one generator
            partner[a:b] = a + rotate(rng.permutation(b - a), shift)
        return partner
    assert arm == "general" and n_pool is not None, arm
    omega_eval = rng.permutation(n_eval)  # drawn first
    omega_pool = rng.permutation(n_pool)  # then omega' of the pool
    partner = np.empty(n_eval, dtype=np.int64)
    partner[omega_eval] = omega_pool[(np.arange(n_eval) + int(shift)) % n_pool]
    return partner


@dataclass
class Tier5Inputs:
    """What the per-text sources are built from: per abstract set name (E, E_lab, D_unif) the (N, n_sub) boolean matrix of the
    pieces each text's own positions name above 0.1; E_lab's source blocks and per-row document codes (`s9_checks.document_index`)."""

    own: dict[str, np.ndarray]
    blocks: dict[str, list[tuple[str, int, int]]] = field(default_factory=dict)
    documents: dict[str, np.ndarray] = field(default_factory=dict)
    cache_records: dict[str, Any] = field(default_factory=dict)


def load_inputs(run: str, set_map: dict[str, str], pool_map: dict[str, str], caches: dict[str, Any], *, synthetic_document_rows: int | None, log: Any = print) -> Tier5Inputs:
    """The evaluation sets' label caches (E_<run>, E_lab_<run>, beside the D_unif cache the launch already holds), their own-named
    matrices through `s9_pre_reads.own_named`, and E_lab's blocks and documents through `s9_checks.document_index`."""
    from vpd_audit import s9_checks
    from vpd_audit.data import load_set
    from vpd_audit.s9_pre_reads import own_named
    from vpd_audit.sources import Cache

    own, records = {}, {}
    for key in ("E", "E_lab", "D_unif"):
        cache = caches[f"D_unif_{run}"] if key == "D_unif" else Cache.load(f"{set_map[key]}_{run}")
        own[key] = own_named(cache)
        records[key] = {"name": cache.name, "n_sequences": int(cache.n_sequences), "sha256": dict(cache.sha256)}
        log(f"[tier 5] own-named sets of {key} ({cache.name}): {own[key].shape[0]} texts, mean {own[key].sum(axis=1).mean():.1f} pieces")
        del cache
    _, _, record = load_set(set_map["E_lab"])
    strata = [str(s) for s in record["strata"]]
    blocks = s9_checks.contiguous_blocks(strata)
    inp = s9_checks.S9Inputs(run=run, set_map=dict(set_map), pool_map=dict(pool_map), pairs=(), regression=None, synthetic_document_rows=synthetic_document_rows)
    index = s9_checks.inputs_document_index(inp)
    docs = s9_checks.document_codes(index, "E_lab", 0, len(strata))
    return Tier5Inputs(own=own, blocks={"E_lab": blocks}, documents={"E_lab": docs}, cache_records=records)


def per_text_source(family: str, eval_set: str, partner_pool: str, arm: str | None, shift: int, inputs: Tier5Inputs, module_to_c: dict[str, int], offsets: dict[str, int], *, master_seed: int = 0) -> tuple[np.ndarray, dict[str, Any], dict[str, np.ndarray]]:
    """The (N, n_sub) boolean source of a per-text cell, its record, and its per-text arrays (the partner's row and the count of
    pieces each text receives): `self_union` is the evaluation set's own matrix; `partner_union` is the partner pool's matrix at
    the partners' rows. The record's n_on is the mean over texts (rounded), since a per-text cell has no single count; the per-text
    counts are in the store's rows and in partners.parquet."""
    from vpd_audit.sources import per_text_source_hash

    own_eval = inputs.own[eval_set]
    n_eval = own_eval.shape[0]
    rec: dict[str, Any] = {"kind": "per_text", "family": family, "pool": partner_pool, "tau": SELF_TAU, "donor_unit": "sequence", "donor_size": SEQ_LEN, "arm": arm, "shift": int(shift)}
    if family == "self_union":
        assert partner_pool == eval_set and arm is None and shift == 0
        rows, partner = own_eval, np.arange(n_eval, dtype=np.int64)
        rec["seed_tuple"] = ""
    else:
        assert family == "partner_union" and arm in ("within", "source", "general"), (family, arm)
        pool = inputs.own[partner_pool]
        partner = partner_assignment(eval_set, arm, shift, n_eval, n_pool=pool.shape[0], blocks=inputs.blocks.get(eval_set) if arm == "source" else None, master_seed=master_seed)
        rows = pool[partner]
        rec["seed_tuple"] = json.dumps(list(partner_seed(master_seed, eval_set, arm)))
        rec["n_texts_partnered_with_themselves"] = int((partner == np.arange(n_eval)).sum()) if partner_pool == eval_set else 0  # zero for a shift below every block's size
    n = rows.sum(axis=1).astype(np.int64)
    off = offsets
    rec.update({"partner_rows_sha256": hashlib.sha256(np.ascontiguousarray(partner, dtype=np.int64).tobytes()).hexdigest(),
                "n_on": {**{k: int(round(float(rows[:, off[k] : off[k] + module_to_c[k]].sum(axis=1).mean()))) for k in sorted(module_to_c)}, "total": int(round(float(n.mean())))},
                "n_on_is": "the mean over texts, rounded (a per-text source has no single count)", "n_on_per_text": {"min": int(n.min()), "max": int(n.max()), "mean": float(n.mean())},
                "source_sha256": per_text_source_hash(rows), "own_set_sha256": {s: per_text_source_hash(m) for s, m in inputs.own.items() if s in (eval_set, partner_pool)}})
    return rows, rec, {"partner_rows": partner, "n_on_rows": n}


def partners_table(cells: list[Any], sources: dict[str, Any], inputs: Tier5Inputs) -> pd.DataFrame:
    """Per (text, shift) of every partner cell of one store: the partner's row, the partner's n_on, the text's own n_on, and, for
    the source arm, whether the partner lies in the text's own document (the majority documents of `s9_checks.document_index`)."""
    out = []
    for c in cells:
        if c.family != "partner_union":
            continue
        aux = sources[c.name].aux
        partner, n_partner = aux["partner_rows"], aux["n_on_rows"]
        n_own = inputs.own[c.eval_set].sum(axis=1).astype(np.int64)
        docs = inputs.documents.get(c.eval_set) if c.arm == "source" else None
        same = (docs[partner] == docs) if docs is not None else np.full(partner.size, None, dtype=object)
        out.append(pd.DataFrame({"cell": c.name, "seq": np.arange(partner.size), "arm": c.arm, "shift": c.shift, "partner_pool": c.donor_pool, "partner_row": partner, "partner_n_on": n_partner, "own_n_on": n_own,
                                 "same_document": pd.array(same, dtype="boolean")}))
    return pd.concat(out, ignore_index=True) if out else pd.DataFrame()


# ----------------------------------------------------------------------------- the example positions


def example_positions(n_texts: int, *, master_seed: int = 0, eval_set: str = "E") -> np.ndarray:
    """(n_texts, 2) int64, ascending within a text: two distinct positions per text with 48 <= t <= 510, from one generator seeded
    (master, "examples", eval set), the texts in order."""
    rng = np.random.default_rng(seed_from_tuple((master_seed, "examples", eval_set)))
    candidates = np.arange(EXAMPLE_T_MIN, EXAMPLE_T_MAX + 1)
    out = np.stack([np.sort(rng.choice(candidates, size=EXAMPLES_PER_TEXT, replace=False)) for _ in range(n_texts)]).astype(np.int64)
    assert out.shape == (n_texts, EXAMPLES_PER_TEXT) and out.min() >= EXAMPLE_T_MIN and out.max() <= EXAMPLE_T_MAX and bool((out[:, 0] < out[:, 1]).all())
    return out


def example_positions_csv(positions: np.ndarray, eval_set: str = "E") -> str:
    """The committed form of the list: set, seq, k, position, one line per example, LF line ends."""
    df = pd.DataFrame({"set": eval_set, "seq": np.repeat(np.arange(positions.shape[0]), positions.shape[1]), "k": np.tile(np.arange(positions.shape[1]), positions.shape[0]), "position": positions.reshape(-1)})
    return df.to_csv(index=False, lineterminator="\n")


def assert_example_positions(positions: np.ndarray, run: str, *, required: bool, log: Any = print) -> dict[str, Any]:
    got = hashlib.sha256(example_positions_csv(positions).encode()).hexdigest()
    want = EXAMPLE_POSITIONS_SHA256.get(run)
    if want is None:
        if required:
            raise GateFailure(f"no committed example-position list is recorded for run {run!r}")
        log(f"[tier 5] example positions: {positions.shape[0]} texts, sha256 {got[:16]}; no committed list for run {run!r}, not asserted")
        return {"sha256": got, "asserted": False}
    if got != want:
        raise GateFailure(f"the example positions ({got[:16]}) are not the committed list's ({want[:16]})")
    log(f"[tier 5] example positions equal the committed list ({got[:16]}, asserted)")
    return {"sha256": got, "asserted": True}


# ----------------------------------------------------------------------------- the committed stores: the canary's and the gate's other side


class CommittedTables:
    """The committed stores under one or more roots (the run's tiers 1 to 4): cell name -> per-text kl_mean (float32, by seq) and
    the cell table's source hash. A name held by several stores (the references, the tier-4 canaries) is read from the first in
    path order; `analysis.load_grid` has already held those copies to each other bitwise."""

    SKIP_PARTS = ("analysis", "pre_reads")

    def __init__(self, roots: tuple[Path, ...]):
        self.roots = tuple(Path(r) for r in roots)
        self.where: dict[str, Path] = {}
        self.cells: dict[str, dict[str, Any]] = {}
        self._rows: dict[Path, pd.DataFrame] = {}
        for root in self.roots:
            for p in sorted(root.rglob("cells.parquet")):
                d = p.parent
                if not (d / "per_sequence.parquet").is_file() or any(part in self.SKIP_PARTS for part in d.parts) or d.name.endswith("_resume") or any(part.startswith("verify") for part in d.parts):
                    continue
                ct = pd.read_parquet(p, columns=["cell", "source_sha256", "n_on"])
                for name, sha, n in zip(ct["cell"], ct["source_sha256"], ct["n_on"]):
                    if name not in self.where:
                        self.where[name] = d
                        self.cells[name] = {"source_sha256": sha, "n_on": n}

    def __contains__(self, cell: str) -> bool:
        return cell in self.where

    def kl_mean(self, cell: str) -> np.ndarray:
        d = self.where[cell]
        if d not in self._rows:
            self._rows[d] = pd.read_parquet(d / "per_sequence.parquet", columns=["cell", "seq", "kl_mean"])
        r = self._rows[d]
        r = r[r["cell"] == cell].sort_values("seq")
        assert np.array_equal(r["seq"].to_numpy(), np.arange(len(r))), f"{cell}: the committed store {d} does not hold every sequence once"
        return r["kl_mean"].to_numpy(np.float32)

    def source_sha256(self, cell: str) -> str | None:
        return self.cells[cell]["source_sha256"]


@dataclass
class SubbatchChecker:
    """Checked after every sub-batch of one store, before its checkpoint. `canary`: cell name -> the committed per-text kl_mean the
    cell must reproduce bitwise. `gate`: for the D_unif store, (cell name, {row: the committed donor-side kl_mean}), reproduced
    within the tolerance. Records counts and the gate's differences; raises GateFailure on the first failing sub-batch."""

    store: str
    canary: dict[str, np.ndarray] = field(default_factory=dict)
    gate_cell: str | None = None
    gate_rows: dict[int, float] = field(default_factory=dict)
    gate_draws: dict[int, int] = field(default_factory=dict)
    n_compared: int = 0
    n_subbatches: int = 0
    gate_differences: dict[int, float] = field(default_factory=dict)
    log: Any = print

    def check(self, i: int, rows: list[dict[str, Any]]) -> None:
        bad: dict[str, int] = {}
        for r in rows:
            want = self.canary.get(r["cell"])
            if want is not None:
                self.n_compared += 1
                a, b = np.float32(r["kl_mean"]), want[int(r["seq"])]
                if not (a == b or (np.isnan(a) and np.isnan(b))):
                    bad[r["cell"]] = bad.get(r["cell"], 0) + 1
            if self.gate_cell is not None and r["cell"] == self.gate_cell and int(r["seq"]) in self.gate_rows:
                self.gate_differences[int(r["seq"])] = float(np.float32(r["kl_mean"])) - float(self.gate_rows[int(r["seq"])])
        self.n_subbatches += 1
        where = f"sub-batch {i}" if i >= 0 else "the whole store"
        if bad:
            raise GateFailure(f"{self.store}, {where}: the canary fails, {len(bad)} re-run cells do not reproduce their committed per-text kl_mean bitwise ({sum(bad.values())} texts): {sorted(bad)[:6]}")
        over = {s: d for s, d in self.gate_differences.items() if not abs(d) <= D_UNIF_GATE_TOLERANCE}
        if over:
            raise GateFailure(f"{self.store}, {where}: the D_unif regression gate fails on rows {sorted(over)}: differences {over} against {D_UNIF_GATE_TOLERANCE} nats")
        if self.canary:
            self.log(f"[tier 5] {self.store}, {where}: canary equal ({len(self.canary)} cells, bitwise per-text kl_mean)")

    def finish(self, all_rows: list[dict[str, Any]]) -> dict[str, Any]:
        """The whole table once more when the store is complete (a resumed launch checked only the sub-batches it ran itself);
        then the record. Raises as `check` does."""
        self.n_compared, self.gate_differences = 0, {}
        done = self.n_subbatches
        self.check(-1, all_rows)
        self.n_subbatches = done
        out = self.summary()
        if self.gate_cell is not None:
            g = out["d_unif_gate"]
            if not g["pass"]:
                raise GateFailure(f"{self.store}: the D_unif regression gate is incomplete or fails: {g}")
            self.log(f"[tier 5] {self.store}: the D_unif gate passes; differences from the committed donor-side values by draw (nats): " + ", ".join(f"k{v['draw']}: {v['difference']:+.5f}" for v in sorted(g["rows"].values(), key=lambda v: v["draw"])))
        return out

    def summary(self) -> dict[str, Any]:
        out: dict[str, Any] = {"store": self.store, "canary_cells": len(self.canary), "canary_pairs_compared": self.n_compared, "canary_pass": True, "subbatches_checked": self.n_subbatches}
        if self.gate_cell is not None:
            out["d_unif_gate"] = {"cell": self.gate_cell, "tolerance": D_UNIF_GATE_TOLERANCE, "rows": {str(s): {"draw": self.gate_draws.get(s), "committed": self.gate_rows[s], "difference": self.gate_differences.get(s)} for s in sorted(self.gate_rows)},
                                  "complete": len(self.gate_differences) == len(self.gate_rows), "pass": len(self.gate_differences) == len(self.gate_rows) and all(abs(d) <= D_UNIF_GATE_TOLERANCE for d in self.gate_differences.values())}
        return out


def build_checker(store: str, eval_set: str, cells: list[Any], sources: dict[str, Any], committed: CommittedTables | None, *, run: str, n_pool_sequences: int, draws: int, master_seed: int, rerun_names: set[str], log: Any = print) -> SubbatchChecker | None:
    """The canary of one store: every reference and every re-run cell must be in the committed stores (a missing one stops the
    launch); any other cell the committed stores happen to hold joins it. On D_unif, the gate's eight rows and committed values,
    with the self-merge's row hash held to the committed donor-side cell's source hash."""
    from vpd_audit.sources import donor_set, source_hash

    if committed is None:
        log(f"[tier 5] {store}: no committed stores given; the canary and the D_unif gate are NOT checked (a local or CPU run)")
        return None
    chk = SubbatchChecker(store=store, log=log)
    for c in cells:
        must = c.name in rerun_names or (c.family == "reference" and eval_set in ("E", "E_lab"))
        if c.name in committed:
            chk.canary[c.name] = committed.kl_mean(c.name)
            if sources[c.name].rho is not None and sources[c.name].rho.ndim == 1:
                want = committed.source_sha256(c.name)
                if want != sources[c.name].record.get("source_sha256"):
                    raise GateFailure(f"{c.name}: the re-run's set is not the committed store's by source hash")
        elif must:
            raise GateFailure(f"{c.name}: a re-run cell or reference that no committed store holds (roots {[str(r) for r in committed.roots]})")
    if eval_set == "D_unif":
        selfs = [c for c in cells if c.family == "self_union"]
        assert len(selfs) == 1, [c.name for c in selfs]
        chk.gate_cell = selfs[0].name
        rho = sources[selfs[0].name].rho
        for k in range(draws):
            ds = donor_set("D_unif", n_pool_sequences, k, D_UNIF_GATE_RUNG, master_seed)
            assert len(ds.sequences) == 1
            row = int(ds.sequences[0])
            name = f"{run}/donors/union/D_unif/tau{SELF_TAU:g}/r0/excl/k{k}/r{D_UNIF_GATE_RUNG}"
            if name not in committed:
                raise GateFailure(f"the D_unif gate: the committed donor-side cell {name} is absent")
            kl = committed.kl_mean(name)
            assert kl.shape == (1,), (name, kl.shape)
            if committed.source_sha256(name) != source_hash(rho[row]):
                raise GateFailure(f"the D_unif gate: row {row}'s own-named set is not the committed donor-side cell's set ({name})")
            chk.gate_rows[row], chk.gate_draws[row] = float(kl[0]), k
        log(f"[tier 5] {store}: the D_unif gate holds rows {sorted(chk.gate_rows)} (the one-text donors of draws 0 to {draws - 1}) to the committed donor-side stores within {D_UNIF_GATE_TOLERANCE} nats; their sets equal by hash")
    log(f"[tier 5] {store}: canary on {len(chk.canary)} cells against the committed stores (bitwise per-text kl_mean, every sub-batch)")
    return chk


# ----------------------------------------------------------------------------- the launch held to the committed label-only tables


def _sha256_file(p: Path) -> str:
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def assert_sources_match_s9_pre_reads(cells: list[Any], sources: dict[str, Any], s9_dir: Path | None, inputs: Tier5Inputs | None, *, run: str, committed: CommittedTables | None, required: bool, log: Any = print) -> dict[str, Any]:
    """Before any forward pass. Every union set of the launch (the same-domain arms and their controls' matched sets, and the
    re-run cells whose source is a donors' union at tau = 0.1) against merge_sets.csv by SHA-256 and count; arm U's sets against
    the committed curve-1 cells as well; every per-text set against self_merge_sets.parquet (per text: hash and count) and the
    manifest's set-level hash. On a run with recorded file hashes the three files must be the committed copies."""
    from vpd_audit.sources import source_hash

    if s9_dir is None or not (Path(s9_dir) / "merge_sets.csv").is_file():
        if required:
            raise GateFailure(f"no label-only tables at {s9_dir}: run s9_label_tables first")
        log(f"[tier 5] no label-only tables at {s9_dir}; the sets are not asserted")
        return {"asserted": False, "dir": str(s9_dir)}
    s9_dir = Path(s9_dir)
    files = {}
    for name, want in S9_TABLES_SHA256.get(run, {}).items():
        got = _sha256_file(s9_dir / name)
        if got != want:
            raise GateFailure(f"{s9_dir / name} ({got[:16]}) is not the committed copy ({want[:16]})")
        files[name] = got
    merge = pd.read_csv(s9_dir / "merge_sets.csv", dtype={"rung": str})
    table = {(str(p), int(k), str(r)): (str(h), int(n)) for p, k, r, h, n in zip(merge["pool"], merge["draw"], merge["rung"], merge["source_sha256"], merge["n_on"])}
    with open(s9_dir / "manifest.json") as f:
        manifest = json.load(f)
    n = {"union_sets": 0, "control_matched_sets": 0, "arm_U_against_curve_1": 0, "per_text_cells": 0, "per_text_rows": 0}
    for c in cells:
        rec = sources[c.name].record
        if c.family in ("union", "soft_erase", "hard_zero") and c.tau == SELF_TAU and c.donor_side_reference is None and c.level is None and c.control in ("none", "plain") and (c.donor_pool, c.draw, c.rung) in table:
            want_hash, want_n = table[(c.donor_pool, c.draw, c.rung)]
            named_hash = rec["source_sha256"] if c.control == "none" else rec["matched_source_sha256"]
            named_n = rec["n_on"]["total"] if c.control == "none" else rec["named_n_on"]["total"]
            if named_hash != want_hash or int(named_n) != want_n:
                raise GateFailure(f"{c.name}: the launch's named set ({named_hash[:16]}, {named_n}) is not merge_sets.csv's ({want_hash[:16]}, {want_n})")
            n["union_sets" if c.control == "none" else "control_matched_sets"] += 1
            if c.tier == 5 and c.donor_pool == "D_unif" and c.control == "none" and committed is not None:
                twin = f"{c.run}/E/union/D_unif/tau{SELF_TAU:g}/r0/excl/k{c.draw}/r{c.rung}"
                if twin not in committed or committed.source_sha256(twin) != named_hash:
                    raise GateFailure(f"{c.name}: arm U's set is not the headline's ({twin}) by source hash")
                n["arm_U_against_curve_1"] += 1
        elif c.tier == 5 and c.family == "union":
            raise GateFailure(f"{c.name}: a tier-5 union set that merge_sets.csv does not hold")
    if inputs is not None and any(c.family in ("self_union", "partner_union") for c in cells):
        per_text = pd.read_parquet(s9_dir / "self_merge_sets.parquet")
        used = sorted({s for c in cells if c.family in ("self_union", "partner_union") for s in (c.eval_set, c.donor_pool)})
        for s in used:
            own = inputs.own[s]
            t = per_text[per_text["set"] == s].sort_values("seq")
            set_hash = hashlib.sha256(np.ascontiguousarray(own, dtype=np.bool_).tobytes()).hexdigest()
            if len(t) != own.shape[0] or set_hash != manifest["self_merge_sets_sha256"][s]:
                raise GateFailure(f"the own-named sets of {s} ({set_hash[:16]}, {own.shape[0]} texts) are not self_merge_sets.parquet's ({manifest['self_merge_sets_sha256'][s][:16]}, {len(t)} texts)")
            if not np.array_equal(t["n_on"].to_numpy(np.int64), own.sum(axis=1).astype(np.int64)) or list(t["source_sha256"]) != [source_hash(own[b]) for b in range(own.shape[0])]:
                raise GateFailure(f"the own-named sets of {s} differ from self_merge_sets.parquet per text (hash or count)")
            n["per_text_rows"] += int(own.shape[0])
        n["per_text_cells"] = sum(c.family in ("self_union", "partner_union") for c in cells)
    log(f"[tier 5] the launch's sets equal the label-only tables at {s9_dir} (asserted by hash and count): {n}; files held to the committed copies: {sorted(files) or 'none recorded for this run'}")
    return {"asserted": True, "dir": str(s9_dir), "counts": n, "files_sha256": files, "s9_pre_reads_commit": manifest.get("commits")}


# ----------------------------------------------------------------------------- what the loop is handed per store


@dataclass
class StoreRun:
    """The tier-5 switches of one `run_cells` call. `listed`: which cells keep the three per-position extras; `example_positions`:
    (N, 2) int64 for a store on E (the top five at those positions, for the target and every listed cell), else None;
    `externals`: the loaded comparison models by key; `checker`: the canary and the gate."""

    listed: Any
    example_positions: np.ndarray | None = None
    externals: dict[str, Any] | None = None
    checker: SubbatchChecker | None = None
    self_tau: float = SELF_TAU
