"""The tier-5 analysis: loads the tier-5 stores, asserts what must hold before anything is read, builds the arrays `stats_s9.py`
reads, applies its rules, and writes the tables and the report. CPU only. Every reading rule is a pure function of `stats_s9.py`, fixed before any tier-5 number existed; this
module holds no rule, only bookkeeping, and it prefers an assert that stops the analysis to a default that lets it continue.
Three rules fixed before the run are encoded here: (1) per-text counts exclude the target's tied positions; (2) a same-size
control is compared with its own arm only, paired by draw; (3) `n_on` is read from the per-text column, never from the cell
table's rounded mean.

**The loader is its own**: tier 5 lives in a root that the frozen `analysis.load_grid` never walks
(`results/grid/main_s9/tier5/<group>__<subset>/`; the stand-in's under `results/dry_run_s9/tier5/`), because its `plain_terms`
stores re-run committed cells under their committed names. Before anything is read: the six stores are present and complete;
the blindness guard of `analysis.check_blindness` (a store of the paper's model needs `--frozen` equal to HEAD on a clean tree);
**the bitwise canary**: every reference on E and E_lab and every re-run cell of every tier-5 store must equal its committed
per-text kl_mean (through `tier5.CommittedTables`), and the references and the target's arrays must agree bitwise across the
tier-5 stores of one set. Cells are rebuilt from rows through `two_paths._cell_from_row`. Counts come from the per-text `n_on`
column, never from the cell table's rounded mean (rule 3).

**Intervals.** On E and on D_unif the text bootstrap of `stats.py`, one resample per set, seed (master, "boot", set). On
E_lab the primary bootstrap resamples documents within source (`stats_s9.stratified_document_resample`; per source the seed is
the one `s9_checks.document_resample` takes, (master, "boot_docs", "E_lab", source), so a stratum of one source is that resample exactly), and the row-level
interval is printed beside it (seeded as `analysis._resample_for` seeds a stratum). A pooled stratum (E^P inside R, E^O, the whole
set) keeps the design's mix of sources in every replicate: every statistic is taken per source in
ratio form and the sources are combined with fixed weights, their row shares (`stats_s9.StratifiedResample`), so point estimates
are the plain means over rows. No interval, of either kind, for a stratum of fewer than ten documents; a pooled stratum that holds
such a source (ArXiv) is flagged, and every value on it has beside it the same value on the stratum without that source. Draws
are resampled per donor pool from one table per pool, seed (master, "boot_draws", pool), shared by every stratum, source, and size
the pool is scored on.

**What is read.** Run 2: the gate, the verdict, R at every size (read at 8 tokens, 64 tokens, 64 texts; printed at one
text), the descriptions, the count-only prediction twice (switched mass primary, the count beside). Run 6: the self-merge
rule on three sets, self against stranger on E, the ladder per source, the scope rule. Runs 3 and 7: the plain-terms
tables under rule 1 with its gate, the bin table, the examples chosen by rule, the yardstick table and the five ratios.

    uv run vpd-audit analyze-s9 --run main --frozen <the freeze>
    uv run vpd-audit analyze-s9 --run simplestories
"""

from __future__ import annotations

import dataclasses
import hashlib
import json
import subprocess
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable

import numpy as np
import pandas as pd

from vpd_audit import env
from vpd_audit import stats as st
from vpd_audit import stats_s9 as s9
from vpd_audit.cells import PARTNER_SHIFTS, SAME_DOMAIN_ARMS, SAME_DOMAIN_CONTROL_RUNGS, SAME_DOMAIN_RUNGS, TIER_5, Cell, reference_for
from vpd_audit.constants import SEQ_LEN

REQUIRED_STORES: tuple[str, ...] = ("E_lab__same_domain", "E__self_merge", "E_lab__self_merge", "D_unif__self_merge", "E__plain_terms", "E_lab__plain_terms")
PAPER_RUNS = ("main", "control")
KL_ARRAY_TOLERANCE = 5e-4  # the gate of `s9_checks` (GATE_TOLERANCE) on a float16 per-position array against its float32 per-text mean, here absolute plus relative
TOP_IS_NEXT_TOLERANCE = 2e-6  # a float32 mean over 511 positions: the device may multiply by 1 / 511 where numpy divides
TOP5_MISMATCH_MAX = 0.01
CONTEXT_TOKENS = 48
REPLACEMENT = chr(0xFFFD)  # U+FFFD, the replacement character a decoder writes for bytes that are not text (written as a code point so that no editor can alter it)
CURVE_1_ONE_TEXT_COMMITTED = 0.49  # the printed consistency check, fixed in advance, for the stranger's rise on E
STAND_IN_DOCUMENT_ROWS = 3  # the stand-in's synthetic documents: blocks of three rows give each of its two sources of 32 rows eleven or twelve documents of unequal size


@dataclass(frozen=True)
class RunSpec:
    """What differs between the paper's run and the stand-in: the saved sets, which sources of E_lab are the code texts (E^G) and
    the prose texts (E^P), the documents, the tokenizer, and whether the comparison models ran."""

    run: str
    set_map: dict[str, str]
    pool_map: dict[str, str]
    code_sources: tuple[str, ...]
    prose_sources: tuple[str, ...]
    synthetic_document_rows: int | None
    tokenizer: str | None  # None: the saved E names it in its record
    has_external: bool


def paper_spec(run: str = "main") -> RunSpec:
    from vpd_audit.roundtrip import TOKENIZER_NAME

    return RunSpec(run=run, set_map={"E": "E", "E_lab": "E_lab", "D_unif": "D_unif"}, pool_map={p: p for p in ("D_unif", "D_code", "D_prose")}, code_sources=("Github",),
                   prose_sources=("Pile-CC", "Wikipedia (en)"), synthetic_document_rows=None, tokenizer=TOKENIZER_NAME, has_external=True)


def stand_in_spec(document_rows: int = STAND_IN_DOCUMENT_ROWS) -> RunSpec:
    return RunSpec(run="simplestories", set_map={"E": "E_dry", "E_lab": "E_lab_dry", "D_unif": "D_unif_dry"}, pool_map={"D_unif": "D_unif_dry", "D_code": "D_code_dry", "D_prose": "D_prose_dry"},
                   code_sources=("dialogue",), prose_sources=("narration",), synthetic_document_rows=int(document_rows), tokenizer=None, has_external=False)


# ----------------------------------------------------------------------------- the stores


@dataclass
class Store5:
    dir: Path
    name: str
    subset: str
    eval_set: str
    run: str
    cells: pd.DataFrame  # indexed by cell
    rows: pd.DataFrame
    manifest: dict[str, Any]
    marker: dict[str, Any]
    objects: dict[str, Cell]
    partners: pd.DataFrame | None
    _wide: dict[str, pd.DataFrame] = field(default_factory=dict)

    @property
    def n(self) -> int:
        return int(self.manifest["n_sequences"])

    @property
    def n_draws(self) -> int:
        return int(self.manifest["n_draws"])

    @property
    def listed(self) -> list[str]:
        return list(self.manifest["extra"]["tier5"]["per_position_listed_cells"])

    def vector(self, cell: str, column: str) -> np.ndarray:
        if column not in self._wide:
            w = self.rows.pivot(index="cell", columns="seq", values=column).sort_index(axis=1)
            assert np.array_equal(w.columns.to_numpy(), np.arange(self.n)), f"{self.name}: the sequences of column {column!r} are not 0..{self.n - 1}"
            self._wide[column] = w
        assert cell in self._wide[column].index, f"{self.name}: no cell {cell!r}"
        return self._wide[column].loc[cell].to_numpy()

    def matrix(self, cells: list[Cell], column: str) -> np.ndarray:
        return np.stack([self.vector(c.name, column) for c in cells], axis=0).astype(np.float64)

    def ref(self, condition: str) -> str:
        return f"{self.run}/{self.eval_set}/ref/{condition}"

    def rise(self, cells: list[Cell]) -> np.ndarray:
        """(K, N) float64: each cell's per-text mean divergence minus its own rung 0's in this store (own labels for a merge, the
        full model for a removal: `cells.reference_for`)."""
        out = []
        for c in cells:
            r = reference_for(c)
            assert r is not None, f"{c.name}: no rung 0"
            out.append(self.vector(c.name, "kl_mean").astype(np.float64) - self.vector(self.ref(r), "kl_mean").astype(np.float64))
        return np.stack(out, axis=0)

    def _load(self, folder: str, stem: str, shape: tuple[int, ...], dtype: str) -> np.ndarray:
        p = self.dir / folder / f"{stem.replace('/', '__')}.npy"
        assert p.is_file(), f"{self.name}: the array {p.name} is not here (the per-position arrays are not in git: pull {self.dir / folder} from the volume)"
        a = np.load(p)
        assert a.shape == shape and a.dtype == np.dtype(dtype), (p.name, a.shape, a.dtype, shape, dtype)
        return a

    def kl_array(self, cell: str) -> np.ndarray:
        """(N, T) float64 from the store's float16 array, held to the cell's per-text kl_mean (the gate of `s9_checks`)."""
        a = self._load("kl", cell, (self.n, SEQ_LEN), "float16").astype(np.float64)
        assert np.isfinite(a).all(), f"{self.name}: {cell}: a per-position divergence that is not finite"
        want = self.vector(cell, "kl_mean").astype(np.float64)
        worst = float(np.max(np.abs(a.mean(axis=1) - want) / (KL_ARRAY_TOLERANCE * (1.0 + np.abs(want)))))
        assert worst <= 1.0, f"{self.name}: {cell}: the per-position array's means are not the table's kl_mean (ratio to tolerance {worst:.2f})"
        return a

    def extra(self, stem: str, tail: tuple[int, ...], dtype: str) -> np.ndarray:
        return self._load("extras", stem, (self.n,) + tuple(tail), dtype)

    def target_arrays(self) -> dict[str, np.ndarray]:
        return {"top": self.extra("target__top", (SEQ_LEN,), "uint16"), "top_p": self.extra("target__top_p", (SEQ_LEN,), "float32"), "tie": self.extra("target__tie", (SEQ_LEN,), "bool")}


def discover(root: Path) -> list[Store5]:
    from vpd_audit.two_paths import _cell_from_row

    root = Path(root)
    out = []
    for p in sorted(root.rglob("cells.parquet")):
        d = p.parent
        rel = d.relative_to(root).parts
        if "analysis" in rel or "pre_reads" in rel or d.name.endswith("_resume"):
            continue
        for needed in ("per_sequence.parquet", "run_manifest.json", "marker.json"):
            assert (d / needed).is_file(), f"{d}: a store without {needed}"
        assert not (d / "error.txt").is_file(), f"{d}: the launch recorded a failure of this store (error.txt)"
        cells, rows = pd.read_parquet(p), pd.read_parquet(d / "per_sequence.parquet")
        with open(d / "run_manifest.json") as f:
            manifest = json.load(f)
        with open(d / "marker.json") as f:
            marker = json.load(f)
        runs, sets = sorted(cells["run"].unique()), sorted(cells["eval_set"].unique())
        assert len(runs) == 1 and len(sets) == 1 and manifest.get("run") == runs[0], (d, runs, sets, manifest.get("run"))
        assert "__" in d.name and d.name.split("__", 1)[0] == sets[0], f"{d}: a tier-5 store is named <evaluation set>__<subset>"
        assert not cells["cell"].duplicated().any(), f"{d}: a cell appears twice in the cell table"
        partners = pd.read_parquet(d / "partners.parquet") if (d / "partners.parquet").is_file() else None
        out.append(Store5(dir=d, name=d.name, subset=d.name.split("__", 1)[1], eval_set=sets[0], run=runs[0], cells=cells.set_index("cell", drop=False), rows=rows, manifest=manifest, marker=marker,
                          objects={r["cell"]: _cell_from_row(r) for _, r in cells.iterrows()}, partners=partners))
    return out


def assert_complete(s: Store5) -> dict[str, Any]:
    """Every sub-batch done, every cell of the cell table in the rows with every sequence once, and nothing else."""
    n_sub = (s.n + int(s.marker["subbatch"]) - 1) // int(s.marker["subbatch"])
    assert int(s.marker["done_through"]) == n_sub - 1 and int(s.marker["n_sequences"]) == s.n, f"{s.name}: not complete (done through sub-batch {s.marker['done_through']} of {n_sub})"
    assert s.manifest.get("finished_at"), f"{s.name}: the run manifest was never marked finished"
    assert set(s.rows["cell"].unique()) == set(s.cells.index) == set(s.marker["cells"]), f"{s.name}: the rows, the cell table, and the marker do not hold the same cells"
    counts = s.rows.groupby("cell")["seq"].agg(["count", "nunique", "min", "max"])
    assert (counts["count"] == s.n).all() and (counts["nunique"] == s.n).all() and (counts["min"] == 0).all() and (counts["max"] == s.n - 1).all(), f"{s.name}: a cell does not hold every sequence exactly once"
    assert all(o.name == name and o.run == s.run and o.eval_set == s.eval_set for name, o in s.objects.items()), f"{s.name}: a cell rebuilt from its row does not carry its own name"
    assert np.isfinite(s.rows["kl_mean"].to_numpy(np.float64)).all(), f"{s.name}: a per-text kl_mean that is not finite"
    assert s.manifest["extra"]["tier5"]["extra_columns"] is True and all(c in s.rows.columns for c in ("top_changed", "top_changed_confident", "p_target_top", "top_is_next", "ce")), f"{s.name}: not a tier-5 store (no plain-terms columns)"
    assert set(s.listed) <= set(s.cells.index)
    return {"store": s.name, "n_cells": int(len(s.cells)), "n_sequences": s.n, "n_subbatches": n_sub, "n_listed": len(s.listed), "commit": s.manifest.get("commits", {}).get("project"), "dirty": s.manifest.get("commits", {}).get("dirty"),
            "gpu": s.manifest.get("gpu_name"), "precision": s.manifest.get("precision")}


def is_rerun(c: Cell) -> bool:
    """A cell of a tier-5 store that an earlier tier enumerated: run here again under its committed name."""
    return c.family != "reference" and c.tier != TIER_5


def assert_canary(stores: list[Store5], committed_roots: tuple[Path, ...] | None, root: Path, *, required: bool, log: Any = print) -> dict[str, Any]:
    """The bitwise canary, inside the loader. Every reference on E and E_lab and every re-run cell must be held by a committed
    store and equal it on the per-text kl_mean, bit for bit; any other name the committed stores hold joins the comparison. Then
    the tier-5 stores of one set among themselves: the references on kl_mean, ce, mask_fp, and the four plain-terms columns, and
    the target's three arrays. Equality is recorded, never a value."""
    from vpd_audit.tier5 import CommittedTables

    out: dict[str, Any] = {"committed_roots": [env.input_path(r) for r in (committed_roots or ())], "stores": {}, "across_stores": {}}
    if not committed_roots:
        assert not required, "stores of the paper's model: the committed stores (the canary's other side) must be given"
        log("[analyze s9] NO committed roots given: the canary against the committed stores is NOT checked (a local stand-in run only)")
        out["checked"] = False
    else:
        for r in committed_roots:
            a, b = Path(r).resolve(), Path(root).resolve()
            assert a.is_dir(), f"no committed root {r}"
            assert a != b and a not in b.parents and b not in a.parents, f"the committed root {r} and the tier-5 root {root} overlap: a store would be compared with itself"
        committed = CommittedTables(tuple(Path(r) for r in committed_roots))
        assert committed.where, f"no committed store under {committed_roots}"
        for s in stores:
            n_cells = n_pairs = 0
            for name, c in s.objects.items():
                must = is_rerun(c) or (c.family == "reference" and s.eval_set in ("E", "E_lab"))
                if name not in committed:
                    assert not must, f"{s.name}: {name} is a reference or a re-run cell that no committed store holds ({[str(r) for r in committed_roots]})"
                    continue
                a, b = s.vector(name, "kl_mean").astype(np.float32), committed.kl_mean(name)
                assert a.shape == b.shape and np.array_equal(a, b, equal_nan=True), f"THE CANARY FAILS: {s.name}: {name} does not reproduce its committed per-text kl_mean bitwise ({int((a != b).sum()) if a.shape == b.shape else 'shape'} texts differ)"
                if is_rerun(c):
                    assert committed.source_sha256(name) == s.cells.loc[name, "source_sha256"], f"{s.name}: {name}: the re-run's set is not the committed store's by source hash"
                n_cells, n_pairs = n_cells + 1, n_pairs + int(a.size)
            out["stores"][s.name] = {"cells_bitwise_equal": n_cells, "pairs_compared": n_pairs, "n_reruns": sum(is_rerun(c) for c in s.objects.values()), "pass": True}
            log(f"[analyze s9] canary pass: {s.name}: {n_cells} cells bitwise equal to the committed stores over {n_pairs} (cell, text) pairs")
        out["checked"] = True
    by_set: dict[str, list[Store5]] = {}
    for s in stores:
        by_set.setdefault(s.eval_set, []).append(s)
    for eval_set, ss in by_set.items():
        base, n_refs = ss[0], 0
        refs = sorted(n for n, c in base.objects.items() if c.family == "reference")
        for other in ss[1:]:
            assert sorted(n for n, c in other.objects.items() if c.family == "reference") == refs, f"{other.name} and {base.name} do not carry the same references"
            for name in refs:
                for col in ("kl_mean", "ce", "top_changed", "top_changed_confident", "p_target_top", "top_is_next"):
                    assert np.array_equal(base.vector(name, col).astype(np.float32), other.vector(name, col).astype(np.float32), equal_nan=True), f"{name}: column {col} differs between {base.name} and {other.name}"
                assert (pd.Series(base.vector(name, "mask_fp")).fillna("").to_numpy() == pd.Series(other.vector(name, "mask_fp")).fillna("").to_numpy()).all(), f"{name}: mask_fp differs between {base.name} and {other.name}"
                n_refs += 1
            ta, tb = base.target_arrays(), other.target_arrays()
            assert all(np.array_equal(ta[k], tb[k]) for k in ta), f"the target's arrays differ between {base.name} and {other.name}"
        out["across_stores"][eval_set] = {"stores": [s.name for s in ss], "reference_comparisons": n_refs, "pass": True}
    return out


@dataclass
class Tier5:
    run: str
    root: Path
    stores: dict[str, Store5]
    completeness: dict[str, Any]
    blindness: dict[str, Any]
    canary: dict[str, Any]


def load_tier5(root: Path, *, frozen: str | None, committed_roots: tuple[Path, ...] | None, require_canary: bool, log: Any = print) -> Tier5:
    from vpd_audit.analysis import check_blindness

    found = discover(root)
    assert found, f"no tier-5 store under {root}"
    blind = check_blindness(found, frozen)  # a store of the paper's model: --frozen equal to HEAD, on a clean tree
    runs = sorted({s.run for s in found})
    assert len(runs) == 1, runs
    names = sorted(s.name for s in found)
    assert names == sorted(REQUIRED_STORES), f"the tier-5 stores under {root} are {names}; the analysis reads exactly {sorted(REQUIRED_STORES)}"
    paper = runs[0] in PAPER_RUNS
    assert not paper or require_canary, "stores of the paper's model are never read without the canary"
    complete = {s.name: assert_complete(s) for s in found}
    draws = {s.n_draws for s in found}
    assert len(draws) == 1, f"the stores were launched with different numbers of draws: {draws}"
    canary = assert_canary(found, committed_roots, Path(root), required=require_canary, log=log)
    return Tier5(run=runs[0], root=Path(root), stores={s.name: s for s in found}, completeness=complete, blindness=blind, canary=canary)


# ----------------------------------------------------------------------------- strata, documents, resamples


@dataclass
class Stratum:
    """Texts that are read together; `mask` selects them among the rows of their evaluation set. `n_documents` None: the unit is
    the text (E, D_unif) and `primary` is the text bootstrap. On E_lab `primary` is a `stats_s9.StratifiedResample`: documents
    resampled within source, every statistic per source, the sources combined with fixed design weights;
    `rows` is the row-level resample printed beside it. `without_thin`: for a pooled stratum that holds a source of
    fewer than ten documents (ArXiv), the same stratum without such sources, whose values are printed beside the flagged ones."""

    key: str
    eval_set: str
    sources: tuple[str, ...]
    mask: np.ndarray
    n_documents: int | None
    documents_by_source: dict[str, int]
    primary: st.Resample
    rows: st.Resample | None
    without_thin: "Stratum | None" = None

    @property
    def n_texts(self) -> int:
        return int(self.mask.sum())

    @property
    def thin_sources(self) -> list[str]:
        return [s for s, n in self.documents_by_source.items() if n < s9.MIN_DOCUMENTS]

    @property
    def flag(self) -> str:
        """The flag, fixed in advance, on a pooled interval: a source of fewer than ten documents is resampled among its few documents."""
        if len(self.sources) > 1 and self.thin_sources:
            return "pooled; " + ", ".join(f"{s} contributes {self.documents_by_source[s]} documents" for s in self.thin_sources) + ("; the value without " + ("it" if len(self.thin_sources) == 1 else "them") + " is beside" if self.without_thin is not None else "")
        return ""


def text_stratum(eval_set: str, n: int, replicates: int, master_seed: int) -> Stratum:
    return Stratum(key=eval_set, eval_set=eval_set, sources=(), mask=np.ones(n, dtype=bool), n_documents=None, documents_by_source={}, primary=st.Resample.make(n, replicates, (master_seed, "boot", eval_set)), rows=None)


def row_resample(eval_set: str, mask: np.ndarray, replicates: int, master_seed: int) -> st.Resample:
    """The row-level resample of a stratum, seeded as `analysis._resample_for` seeds it (a content hash of the mask)."""
    if bool(mask.all()):
        return st.Resample.make(int(mask.size), replicates, (master_seed, "boot", eval_set))
    return st.Resample.make(int(mask.sum()), replicates, (master_seed, "boot", eval_set, hashlib.sha256(mask.tobytes()).hexdigest()[:16]))


@dataclass
class Inputs:
    """What the analysis reads beside the stores, all of it label-side: the source and the document code of every row of E_lab,
    the token ids of the three evaluation sets, and the tokenizer's decoder (for the examples). `load_inputs` takes them from the
    saved sets, held to the stores by ids hash; the tests hand in planted ones."""

    sources: list[str]
    documents: np.ndarray
    ids: dict[str, np.ndarray]
    decode: Callable[[list[int]], str]
    tokenizer_name: str
    record: dict[str, Any] = field(default_factory=dict)


def load_inputs(spec: RunSpec, t5: Tier5) -> Inputs:
    """E_lab's sources are the saved set's own strata and its documents the document index of `s9_checks` (on the stand-in, blocks of
    `synthetic_document_rows` rows), as `tier5.load_inputs` builds them for the launch. Every saved set is its stores' set by ids
    hash; on the paper's run the index is the committed table (document_index.csv)."""
    from transformers import AutoTokenizer

    from vpd_audit import s9_checks
    from vpd_audit.data import load_set

    ids: dict[str, np.ndarray] = {}
    records: dict[str, Any] = {}
    for key in ("E", "E_lab", "D_unif"):
        ids[key], _, records[key] = load_set(spec.set_map[key])
        for s in t5.stores.values():
            if s.eval_set == key:
                assert s.manifest["set_hash"] == records[key]["sha256_ids"] and ids[key].shape == (s.n, SEQ_LEN), f"{s.name}: its set is not the saved {spec.set_map[key]} (ids hash)"
    sources = [str(x) for x in records["E_lab"]["strata"]]
    assert len(sources) == ids["E_lab"].shape[0]
    inp = s9_checks.S9Inputs(run=spec.run, set_map={k: v for k, v in spec.set_map.items() if k != "D_unif"}, pool_map=dict(spec.pool_map), pairs=(), regression=None, synthetic_document_rows=spec.synthetic_document_rows)
    index = s9_checks.inputs_document_index(inp)
    el = index[index["set"] == "E_lab"].sort_values("row").reset_index(drop=True)
    assert len(el) == len(sources) and list(el["source"]) == sources, "the document index's sources are not E_lab's strata, row for row"
    rec: dict[str, Any] = {"sets": {k: {"name": spec.set_map[k], "sha256_ids": records[k]["sha256_ids"]} for k in ids}, "synthetic_document_rows": spec.synthetic_document_rows}
    if spec.synthetic_document_rows is None:
        committed = pd.read_csv(s9_checks.analysis_dir(spec.run) / "document_index.csv")
        committed = committed[committed["set"] == "E_lab"].sort_values("row").reset_index(drop=True)
        assert len(committed) == len(el) and all(list(committed[c]) == list(el[c]) for c in ("row", "source", "majority_document")), "the document index rebuilt from the saved set is not the committed document_index.csv"
        rec["equal_to_committed_index"] = True
    name = spec.tokenizer or records["E"].get("tokenizer")
    assert name, f"no tokenizer is recorded for {spec.set_map['E']}"
    tok = AutoTokenizer.from_pretrained(name)
    return Inputs(sources=sources, documents=s9_checks.document_codes(index, "E_lab", 0, len(sources)), ids=ids, decode=lambda x: tok.decode([int(t) for t in x], skip_special_tokens=False, clean_up_tokenization_spaces=False),
                  tokenizer_name=str(name), record=rec)


def build_strata(inp: Inputs, spec: RunSpec, t5: Tier5, replicates: int, master_seed: int) -> tuple[dict[str, Stratum], dict[str, Any]]:
    """E and D_unif whole (texts); on E_lab: every source, E^G (the code texts), E^P (the prose texts), E^O (every text that is
    not code), and the whole set."""
    from vpd_audit.s9_checks import contiguous_blocks

    sources, docs, rec = list(inp.sources), np.asarray(inp.documents), dict(inp.record)
    assert len(sources) == docs.size == t5.stores["E_lab__same_domain"].n, "one source and one document per row of E_lab"
    contiguous_blocks(sources)  # every source is one block (asserted there), as the launch's source arm takes it
    src = np.asarray(sources)
    order = list(dict.fromkeys(sources))
    assert set(spec.code_sources) <= set(order) and set(spec.prose_sources) <= set(order) and not set(spec.code_sources) & set(spec.prose_sources), (order, spec.code_sources, spec.prose_sources)
    other = tuple(s for s in order if s not in spec.code_sources)

    def lab(key: str, members: tuple[str, ...], *, with_remainder: bool = True) -> Stratum:
        mask = np.isin(src, members)
        assert mask.any(), key
        by_source = {s: int(np.unique(docs[src == s]).size) for s in order if s in members}
        primary = s9.stratified_document_resample(docs[mask], src[mask], replicates, lambda s: (master_seed, "boot_docs", "E_lab", s))
        assert primary.block_names == tuple(s for s in order if s in members) and [len(b) for b in primary.blocks] == [int((src == s).sum()) for s in primary.block_names]
        S = Stratum(key=key, eval_set="E_lab", sources=tuple(s for s in order if s in members), mask=mask, n_documents=int(np.unique(docs[mask]).size), documents_by_source=by_source, primary=primary,
                    rows=row_resample("E_lab", mask, replicates, master_seed))
        kept = tuple(s for s in S.sources if s not in S.thin_sources)
        if with_remainder and len(S.sources) > 1 and S.thin_sources and kept:  # a flagged pooled stratum: the same without its thin sources, printed beside
            S.without_thin = lab(f"{key} without {', '.join(S.thin_sources)}", kept, with_remainder=False)
        return S

    strata = {"E": text_stratum("E", t5.stores["E__self_merge"].n, replicates, master_seed), "D_unif": text_stratum("D_unif", t5.stores["D_unif__self_merge"].n, replicates, master_seed)}
    assert t5.stores["E__plain_terms"].n == strata["E"].n_texts
    strata.update({"G": lab("G", spec.code_sources), "P": lab("P", spec.prose_sources), "O": lab("O", other), "E_lab": lab("E_lab", tuple(order))})
    for s in order:
        strata[f"source:{s}"] = lab(f"source:{s}", (s,))
    assert strata["G"].n_texts + strata["O"].n_texts == len(sources) and sum(strata[f"source:{s}"].n_documents for s in order) == strata["E_lab"].n_documents
    rec.update({"sources": order, "code_sources": list(spec.code_sources), "prose_sources": list(spec.prose_sources), "documents": {k: {"n_texts": v.n_texts, "n_documents": v.n_documents, "by_source": v.documents_by_source, "flag": v.flag} for k, v in strata.items()}})
    return strata, rec


def beside(S: Stratum, fn: Callable[[Stratum, st.Resample, int | None], dict[str, Any]]) -> dict[str, Any]:
    """`fn(stratum, resample, n_documents)`, which slices its data by the stratum it is handed (`stratum.mask`, over the rows of
    the evaluation set), under the stratum's primary bootstrap. On E_lab also under the row-level resample, whose result goes
    beside it under `rows_beside` (never read); neither interval exists for a stratum of fewer than ten documents. And for a
    flagged pooled stratum the whole of it again on the stratum without its thin sources, under `without_flagged` (a pooled
    interval that includes ArXiv stays flagged, with the value without ArXiv beside it)."""
    out = dict(fn(S, S.primary, S.n_documents))
    out["rows_beside"] = fn(S, S.rows, None) if (S.rows is not None and s9.has_interval(S.n_documents)) else None
    W = S.without_thin
    out["without_flagged"] = dict(fn(W, W.primary, W.n_documents)) if W is not None else None
    return out


def _lohi(prefix: str, iv: Any) -> dict[str, float]:
    ok = isinstance(iv, (list, tuple)) and len(iv) == 2 and all(x is not None for x in iv)
    return {f"{prefix}_lo": float(iv[0]) if ok else float("nan"), f"{prefix}_hi": float(iv[1]) if ok else float("nan")}


def _without(v: dict[str, Any], value_key: str, interval_key: str, name: str = "value") -> dict[str, Any]:
    """The columns that stand beside a flagged pooled value: the same quantity on the stratum without its thin sources, with its
    interval. Empty (NaN) where the stratum is not flagged."""
    w = v.get("without_flagged")
    return {f"{name}_without_flagged_sources": (w[value_key] if w is not None else float("nan")), **_lohi(f"{name}_without_flagged_sources_interval", w[interval_key] if w is not None else None)}


def size_words(rung: str) -> str:
    from vpd_audit.s9_checks import merge_label, rung_size

    unit, n = rung_size(rung)
    return "the whole pool" if unit == "pool" else merge_label(n, unit)


# ----------------------------------------------------------------------------- run 2


def draw_tables(n_draws: int, replicates: int, master_seed: int) -> dict[str, np.ndarray]:
    """One draw table per donor pool, seed (master, "boot_draws", pool): draws are resampled independently per pool. Asserted at
    construction: every replicate of every table holds `n_draws` draws, and the three tables are
    pairwise different, since one seed for every pool would pair independent pools by draw index in every two-level contrast."""
    pools = [pool for _, pool, _ in SAME_DOMAIN_ARMS]
    assert len(set(pools)) == len(pools) == 3, pools
    tables = {pool: s9.draw_counts(n_draws, replicates, (master_seed, "boot_draws", pool)) for pool in pools}
    for pool, t in tables.items():
        assert t.shape == (replicates, n_draws) and np.all(t.sum(axis=1) == n_draws) and np.all(t >= 0), f"the draw table of {pool}: a replicate does not hold {n_draws} draws"
    if n_draws > 1:
        for i, a in enumerate(pools):
            for b in pools[i + 1 :]:
                assert not np.array_equal(tables[a], tables[b]), f"the draw tables of {a} and {b} are the same table: draws are resampled independently per donor pool"
    return tables


def arm_data(store: Store5, pool: str, control: str) -> dict[str, Any]:
    """One donor arm of the same-domain store (or its same-size random control): per size the cells in draw order, the (K, N) rise
    over own labels, the per-text switched mass, and the per-text count. Every size must hold draws 0..K-1 (the pool: draw 0)."""
    cells = [c for c in store.objects.values() if c.tier == TIER_5 and c.family == "union" and c.donor_pool == pool and c.control == control]
    assert cells and all(c.tau == 0.1 and c.background == "r0" and c.delta == "excluded" and c.eval_set == "E_lab" and not c.descriptive for c in cells), (pool, control)
    by_rung: dict[str, list[Cell]] = {}
    for c in cells:
        by_rung.setdefault(c.rung, []).append(c)
    want = tuple(SAME_DOMAIN_RUNGS) + ("8",) if control == "none" else tuple(SAME_DOMAIN_CONTROL_RUNGS)
    assert sorted(by_rung) == sorted(want), f"arm {pool}/{control}: sizes {sorted(by_rung)}, expected {sorted(want)}"
    out: dict[str, Any] = {"pool": pool, "control": control, "cells": {}, "e": {}, "sigma": {}, "n_on": {}}
    for r in st.sort_rungs(list(by_rung)):
        cs = sorted(by_rung[r], key=lambda c: c.draw)
        assert [c.draw for c in cs] == ([0] if r == "8" else list(range(store.n_draws))), f"arm {pool}/{control}, size {r}: draws {[c.draw for c in cs]}"
        n_on, sigma = store.matrix(cs, "n_on"), store.matrix(cs, "sigma")
        assert (n_on == n_on[:, :1]).all() and [int(x) for x in n_on[:, 0]] == [int(store.cells.loc[c.name, "n_on"]) for c in cs], f"arm {pool}/{control}, size {r}: a union cell's per-text count is its set's count on every text"
        assert np.isfinite(sigma).all() and (sigma >= 0).all(), f"arm {pool}/{control}, size {r}: a switched mass that is not finite"
        out["cells"][r], out["e"][r], out["sigma"][r], out["n_on"][r] = cs, store.rise(cs), sigma, n_on
    return out


def analyze_run2(t5: Tier5, strata: dict[str, Stratum], counts: dict[str, np.ndarray], log: Any = print) -> dict[str, Any]:
    store = t5.stores["E_lab__same_domain"]
    arms = {arm: arm_data(store, pool, "none") for arm, pool, _ in SAME_DOMAIN_ARMS}
    controls = {arm: arm_data(store, pool, "plain") for arm, pool, has in SAME_DOMAIN_ARMS if has}
    assert sorted(arms) == ["C", "P", "U"] and sorted(controls) == ["C", "U"]
    pool_of = {arm: pool for arm, pool, _ in SAME_DOMAIN_ARMS}
    sizes = st.sort_rungs(list(arms["C"]["e"]))
    assert len(sizes) == 10 and all(st.sort_rungs(list(a["e"])) == sizes for a in arms.values())
    G, P, O = strata["G"], strata["P"], strata["O"]
    read_strata = [G, P, O] + [v for k, v in strata.items() if k.startswith("source:")]

    def e(arm: str, r: str, S: Stratum, key: str = "e", data: dict[str, Any] | None = None) -> np.ndarray:
        return (data or arms)[arm][key][r][:, S.mask]

    def cnt(arm: str) -> np.ndarray:
        return counts[pool_of[arm]]

    def curve(arm: str, S: Stratum) -> dict[str, Any]:
        return beside(S, lambda T, rs, nd: s9.union_curve_s9({r: e(arm, r, T) for r in sizes}, rs, n_documents=nd))

    out: dict[str, Any] = {"sizes": sizes, "size_words": {r: size_words(r) for r in sizes}, "n_draws": store.n_draws}
    # the gate and the verdict: arms C and U on the code texts, m = 10, the document bootstrap
    C, U = curve("C", G), curve("U", G)
    assert C["m"] == U["m"] == 10 and C["rungs"] == U["rungs"] == sizes
    out["verdict"] = {**s9.run2_outcome(C, U), "C_label": C["label"], "U_label": U["label"], "C_first_detected": C["j_det"], "C_first_material": C["j_mat"], "U_first_material": U["j_mat"], "n_documents": G.n_documents,
                      "rows_beside": ({**s9.run2_outcome(C["rows_beside"], U["rows_beside"]), "C_label": C["rows_beside"]["label"], "U_label": U["rows_beside"]["label"]} if C["rows_beside"] else None)}
    log(f"[analyze s9] run 2: gate (arm U fails on the code texts): {out['verdict']['gate']}; outcome: {out['verdict']['outcome']}")
    # every arm on every stratum, per size (the verdict's two curves are the first two; the rest are descriptions)
    rows = []
    for arm in ("C", "U", "P"):
        for S in read_strata:
            cv = C if (arm, S.key) == ("C", "G") else (U if (arm, S.key) == ("U", "G") else curve(arm, S))
            for r in sizes:
                v, vr = cv["per_rung"][r], (cv["rows_beside"]["per_rung"][r] if cv["rows_beside"] else None)
                vw = {"without_flagged": cv["without_flagged"]["per_rung"][r] if cv["without_flagged"] else None}
                two = s9.two_level_interval_s9(e(arm, r, S), S.primary, cnt(arm), cv["m"], n_documents=S.n_documents)
                rows.append({"arm": arm, "pool": pool_of[arm], "stratum": S.key, "role": "verdict" if (arm in ("C", "U") and S.key == "G") else "description", "size": r, "size_words": size_words(r), "m": cv["m"], "n_draws": v["n_draws"],
                             "n_texts": v["n_texts"], "n_documents": S.n_documents, "flag": S.flag, "rise": v["e_hat"], **_lohi("interval_documents", v["interval"]), **_lohi("interval_rows_beside", vr["interval"] if vr else None),
                             **_lohi("interval_two_level", two), **_without(vw, "e_hat", "interval", "rise"), "n_draws_positive": v["n_draws_positive"], "sign_condition": v["sign_condition"], "detected": v["detected"],
                             "material": v["material"], "n_on_mean": float(arms[arm]["n_on"][r].mean()), "sigma_mean": float(e(arm, r, S, "sigma").mean())})
    out["curves"] = rows
    # the match ratio R at every size; read at 8 tokens, 64 tokens, 64 texts; printed and not read at one text
    ratio_rows = []
    Gw, Pw = G.without_thin or G, P.without_thin or P  # the prose stratum pools two sources: its documents are resampled within source, with fixed weights
    for r in sizes:
        def mr(TG: Stratum, TP: Stratum, rs_G: st.Resample, rs_P: st.Resample, nd_G: int | None, nd_P: int | None) -> dict[str, Any]:
            return s9.match_ratio(e("C", r, TG), e("P", r, TG), e("P", r, TP), e("C", r, TP), rs_G, rs_P, cnt("C"), cnt("P"), n_documents_G=nd_G, n_documents_P=nd_P, size_is_read=r in s9.R_SIZES_READ)
        v = mr(G, P, G.primary, P.primary, G.n_documents, P.n_documents)
        vr = mr(G, P, G.rows, P.rows, None, None) if v["interval"] is not None else None  # type: ignore[arg-type]
        vw = {"without_flagged": mr(Gw, Pw, Gw.primary, Pw.primary, Gw.n_documents, Pw.n_documents) if (G.without_thin or P.without_thin) else None}
        ri = v.get("rise_intervals") or {}
        ratio_rows.append({"size": r, "size_words": size_words(r), "r_code": v["r_code"], "r_prose": v["r_prose"], "R": v["R"], "m": v["m"], **_lohi("R_interval", v["interval"]), **_lohi("R_interval_rows_beside", vr["interval"] if vr else None),
                           **_without(vw, "R", "interval", "R"),
                           **{k2: v2 for k, iv in (("C_on_code", ri.get("C_G")), ("P_on_code", ri.get("P_G")), ("P_on_prose", ri.get("P_P")), ("C_on_prose", ri.get("C_P"))) for k2, v2 in _lohi(f"rise_{k}", iv).items()},
                           "all_four_rises_above_zero": v.get("all_four_rises_above_zero"), "nonfinite_share": v["nonfinite_share"], "size_is_read": r in s9.R_SIZES_READ, "printed_not_read": r == s9.R_SIZE_PRINTED_NOT_READ,
                           "readable": v["readable"], "reading": v["reading"], "n_documents_code": G.n_documents, "n_documents_prose": P.n_documents, "flag_prose": P.flag})
    out["match_ratio"] = ratio_rows
    log("[analyze s9] run 2: R: " + "; ".join(f"{x['size_words']}: {x['reading']}" for x in ratio_rows if x["size_is_read"]))
    # the descriptions
    contrast, per_unit, ctl_rows = [], [], []
    for r in sizes:
        v = beside(G, lambda T, rs, nd: s9.pool_contrast(e("C", r, T), e("U", r, T), rs, cnt("C"), cnt("U"), n_documents=nd))
        contrast.append({"stratum": "G", "size": r, "size_words": size_words(r), "rise_C": v["a"], "rise_U": v["b"], "difference": v["difference"], **_lohi("difference_interval", v["difference_interval"]), "ratio": v["ratio"],
                         **_lohi("ratio_interval", v["ratio_interval"]), "ratio_nonfinite_share": v["ratio_nonfinite_share"], **_lohi("difference_interval_rows_beside", v["rows_beside"]["difference_interval"] if v["rows_beside"] else None),
                         "n_draws_C_above_U_by_index": v["n_draws_a_above_b_by_index"], "n_on_C": float(arms["C"]["n_on"][r].mean()), "n_on_U": float(arms["U"]["n_on"][r].mean()), "sigma_C": float(e("C", r, G, "sigma").mean()),
                         "sigma_U": float(e("U", r, G, "sigma").mean())})
        for S in (G, P, O):
            for arm in ("C", "U", "P"):
                h = beside(S, lambda T, rs, nd: s9.per_unit(e(arm, r, T), e(arm, r, T, "sigma"), rs, cnt(arm), n_documents=nd))
                per_unit.append({"quantity": f"h_{arm}", "stratum": S.key, "size": r, "size_words": size_words(r), "rise": h["e_hat"], "sigma_mean": h["sigma_bar"], "value": h["h"], **_lohi("interval", h["interval"]),
                                 "nonfinite_share": h["nonfinite_share"], **_without(h, "h", "interval"), **_lohi("interval_rows_beside", h["rows_beside"]["interval"] if h["rows_beside"] else None), "n_on_mean": float(arms[arm]["n_on"][r].mean()), "flag": S.flag})
            hr = beside(S, lambda T, rs, nd: s9.per_unit_ratio(e("C", r, T), e("C", r, T, "sigma"), e("U", r, T), e("U", r, T, "sigma"), rs, cnt("C"), cnt("U"), n_documents=nd))
            per_unit.append({"quantity": "h_C / h_U", "stratum": S.key, "size": r, "size_words": size_words(r), "rise": float("nan"), "sigma_mean": float("nan"), "value": hr["ratio"], **_lohi("interval", hr["interval"]),
                             "nonfinite_share": hr["nonfinite_share"], **_without(hr, "ratio", "interval"), **_lohi("interval_rows_beside", hr["rows_beside"]["interval"] if hr["rows_beside"] else None), "n_on_mean": float("nan"), "flag": S.flag})
    for arm in ("C", "U"):  # a control is compared with its own arm only, paired by draw, its draws resampled with its arm's (rule 2)
        for r in st.sort_rungs(list(controls[arm]["e"])):
            for S in (G, P, O):
                v = beside(S, lambda T, rs, nd: s9.control_against_arm(e(arm, r, T), e(arm, r, T, data=controls), rs, cnt(arm), n_documents=nd))
                ctl_rows.append({"arm": arm, "stratum": S.key, "size": r, "size_words": size_words(r), "real": v["real"], "random": v["control"], "difference": v["difference"], **_lohi("difference_interval", v["difference_interval"]),
                                 **_without(v, "difference", "difference_interval", "difference"),
                                 **_lohi("difference_interval_rows_beside", v["rows_beside"]["difference_interval"] if v["rows_beside"] else None), "n_draws_real_above_random": v["n_draws_real_above_control"], "n_draws": v["n_draws"],
                                 "n_on_real": float(arms[arm]["n_on"][r].mean()), "n_on_random": float(controls[arm]["n_on"][r].mean()), "sigma_real": float(e(arm, r, S, "sigma").mean()), "sigma_random": float(e(arm, r, S, "sigma", controls).mean()), "flag": S.flag})
    out["contrast_C_minus_U"], out["per_unit"], out["controls"] = contrast, per_unit, ctl_rows
    def lam_on(TG: Stratum, TO: Stratum, rs_G: st.Resample, rs_O: st.Resample) -> dict[str, Any]:
        return s9.lambda_contrast(e("C", "3", TG), e("U", "3", TG), e("C", "3", TO), e("U", "3", TO), rs_G, rs_O, cnt("C"), cnt("U"))

    lam_ok = s9.has_interval(G.n_documents) and s9.has_interval(O.n_documents)
    lam = lam_on(G, O, G.primary, O.primary)
    lam_rows = lam_on(G, O, G.rows, O.rows) if lam_ok else None  # type: ignore[arg-type]
    Ow = O.without_thin
    lam_w = lam_on(G, Ow, G.primary, Ow.primary) if Ow is not None else None
    out["lambda"] = {"size": "3", "size_words": size_words("3"), "lambda": lam["lambda"], "interval": lam["interval"] if lam_ok else None, "nonfinite_share": lam["nonfinite_share"] if lam_ok else None,
                     "interval_rows_beside": lam_rows["interval"] if lam_rows else None, "flag": O.flag, "lambda_without_flagged_sources": lam_w["lambda"] if lam_w else None,
                     "interval_without_flagged_sources": lam_w["interval"] if (lam_w and s9.has_interval(G.n_documents) and s9.has_interval(Ow.n_documents)) else None}
    # the count-only prediction on the code texts, twice: the switched mass (primary; it owns the word) and the count
    out["count_only"] = {}
    for amount, key in (("switched mass (primary)", "sigma"), ("count of named pieces (beside)", "n_on")):
        v = beside(G, lambda T, rs, nd: s9.count_only({r: e("U", r, T) for r in sizes}, {r: e("U", r, T, key) for r in sizes}, {r: e("C", r, T) for r in sizes}, {r: e("C", r, T, key) for r in sizes}, rs, cnt("C"), n_documents=nd))
        out["count_only"][key] = {"amount": amount, **v}
    log("[analyze s9] run 2: count-only (switched mass): " + "; ".join(f"{size_words(j)}: {out['count_only']['sigma']['per_size'][j]['reading']}" for j in s9.COUNT_ONLY_SIZES))
    return out


# ----------------------------------------------------------------------------- run 6


def _one(cells: list[Cell], what: str) -> Cell:
    assert len(cells) == 1, f"{what}: {len(cells)} cells, expected one"
    return cells[0]


def self_cell(store: Store5) -> Cell:
    return _one([c for c in store.objects.values() if c.family == "self_union"], f"{store.name}: the self-merge")


def curve_1_cells(store: Store5, rung: str) -> list[Cell]:
    """Curve 1 of the headline (general donors merged into E, tau = 0.1, background r0, residual excluded) at one size, re-run in
    the plain_terms store under its committed names: every draw, in draw order."""
    from vpd_audit.s9_checks import is_curve_1

    cs = sorted((c for c in store.objects.values() if is_curve_1(c, "none") and c.tier != TIER_5 and c.rung == rung), key=lambda c: c.draw)
    assert [c.draw for c in cs] == ([0] if rung == "8" else list(range(store.n_draws))), f"{store.name}: curve 1 at size {rung}: draws {[c.draw for c in cs]}"
    return cs


def partner_cells(store: Store5, arm: str) -> list[Cell]:
    cs = sorted((c for c in store.objects.values() if c.family == "partner_union" and c.arm == arm), key=lambda c: c.shift)
    assert [c.shift for c in cs] == list(PARTNER_SHIFTS), f"{store.name}: arm {arm}: shifts {[c.shift for c in cs]}"
    return cs


def partner_table(store: Store5, cells: list[Cell]) -> dict[str, np.ndarray]:
    """partners.parquet of the arm as (shifts, N) arrays, every shift holding every text once, in text order."""
    assert store.partners is not None, f"{store.name}: no partners.parquet"
    out: dict[str, list[np.ndarray]] = {"partner_row": [], "partner_n_on": [], "own_n_on": [], "same_document": []}
    for c in cells:
        t = store.partners[store.partners["cell"] == c.name].sort_values("seq")
        assert np.array_equal(t["seq"].to_numpy(), np.arange(store.n)) and (t["arm"] == c.arm).all() and (t["shift"] == c.shift).all() and (t["partner_pool"] == c.donor_pool).all(), f"{c.name}: partners.parquet does not hold every text once"
        for k in ("partner_row", "partner_n_on", "own_n_on"):
            out[k].append(t[k].to_numpy(np.int64))
        sd = t["same_document"]
        assert sd.isna().all() if c.arm != "source" else sd.notna().all(), f"{c.name}: same_document is recorded for the source arm and for no other"
        out["same_document"].append(sd.fillna(False).to_numpy(bool))
    return {k: np.stack(v, axis=0) for k, v in out.items()}


def assert_counts_and_rotation(t5: Tier5, inp: Inputs) -> dict[str, Any]:
    """Rule 3, on the real tables. `partner_n_on` equals the partner cell's per-text `n_on` column; the count a text
    receives is the partner's own self-merge count (a join of partners.parquet against the self-merge rows, across stores for the
    general arm); the self arm's mean count equals each within-set and each within-source shift's mean exactly (and block by
    block on E_lab), which checks the rotation; a source-arm partner lies in the text's own source, is never the text itself, and
    `same_document` is the document index's."""
    src, doc = np.asarray(inp.sources), np.asarray(inp.documents)
    out: dict[str, Any] = {}
    own = {s: t5.stores[f"{s}__self_merge"].vector(self_cell(t5.stores[f"{s}__self_merge"]).name, "n_on").astype(np.int64) for s in ("E", "E_lab", "D_unif")}
    for eval_set, arm, pool in (("E", "within", "E"), ("E_lab", "source", "E_lab"), ("E_lab", "general", "D_unif")):
        store = t5.stores[f"{eval_set}__self_merge"]
        cs = partner_cells(store, arm)
        assert all(c.donor_pool == pool for c in cs)
        pt = partner_table(store, cs)
        col = np.stack([store.vector(c.name, "n_on").astype(np.int64) for c in cs], axis=0)
        assert np.array_equal(pt["partner_n_on"], col), f"{eval_set}/{arm}: partners.parquet's partner_n_on is not the per-text n_on column"
        assert np.array_equal(pt["own_n_on"], np.tile(own[eval_set], (len(cs), 1))), f"{eval_set}/{arm}: partners.parquet's own_n_on is not the self-merge's per-text n_on"
        assert pt["partner_row"].min() >= 0 and pt["partner_row"].max() < own[pool].size and np.array_equal(pt["partner_n_on"], own[pool][pt["partner_row"]]), f"{eval_set}/{arm}: a text's received count is not its partner's own count in {pool}"
        rec: dict[str, Any] = {"n_shifts": len(cs), "partner_n_on_equals_column": True, "received_count_is_the_partners_own": True}
        if arm in ("within", "source"):
            assert (pt["partner_row"] != np.arange(store.n)[None, :]).all(), f"{eval_set}/{arm}: a text is its own partner"
            assert all(np.array_equal(np.sort(p), np.arange(store.n)) for p in pt["partner_row"]), f"{eval_set}/{arm}: a shift is not a bijection of the set"
            assert all(int(col[i].sum()) == int(own[eval_set].sum()) for i in range(len(cs))), f"{eval_set}/{arm}: the self arm's mean count is not each shift's mean exactly"
            rec["self_mean_count_equals_each_shift"] = True
        if arm == "source":
            assert (src[pt["partner_row"]] == src[None, :]).all(), "a source-arm partner lies outside the text's own source"
            for s in dict.fromkeys(src.tolist()):
                assert all(int(col[i][src == s].sum()) == int(own["E_lab"][src == s].sum()) for i in range(len(cs))), f"source arm, {s}: the block's count is not balanced"
            assert np.array_equal(pt["same_document"], doc[pt["partner_row"]] == doc[None, :]), "partners.parquet's same_document is not the document index's (another document size at launch?)"
            rec.update({"partner_in_own_source": True, "balanced_per_source": True, "same_document_is_the_index": True, "n_same_document_pairs": int(pt["same_document"].sum())})
        out[f"{eval_set}/{arm}"] = rec
    return out


def analyze_run6(t5: Tier5, strata: dict[str, Stratum], inp: Inputs, log: Any = print) -> dict[str, Any]:
    out: dict[str, Any] = {"asserts": assert_counts_and_rotation(t5, inp)}
    log(f"[analyze s9] run 6: counts and rotation asserted on {len(out['asserts'])} partner arms (rule 3)")
    # the rule on three sets: documents on E_lab, texts on E and D_unif
    rise, against_rounded = {}, {}
    out["rule"] = {}
    for key in ("E", "E_lab", "D_unif"):
        store = t5.stores[f"{key}__self_merge"]
        c = self_cell(store)
        rise[key] = store.rise([c])[0]
        against_rounded[key] = store.vector(c.name, "kl_mean").astype(np.float64) - store.vector(store.ref("rounded_0.1"), "kl_mean").astype(np.float64)
        S = strata[key]
        v = beside(S, lambda T, rs, nd: s9.self_merge_rule(rise[key][T.mask], rs, n_documents=nd, s_against_rounded=against_rounded[key][T.mask]))
        out["rule"][key] = {**v, "flag": S.flag, "n_on_mean": float(store.vector(c.name, "n_on").mean()), "sigma_mean": float(store.vector(c.name, "sigma").astype(np.float64).mean()),
                            "own_labels_kl": float(store.vector(store.ref("importances"), "kl_mean").astype(np.float64).mean()), "self_merge_kl": float(store.vector(c.name, "kl_mean").astype(np.float64).mean())}
    out["summary_may_carry_the_self_merge"] = bool(out["rule"]["E"]["material"])
    log(f"[analyze s9] run 6: the self-merge is material on E: {out['rule']['E']['material']}")
    # self against stranger on E
    sE = t5.stores["E__self_merge"]
    within = partner_cells(sE, "within")
    x = sE.rise(within)
    out["stranger"] = s9.self_against_stranger(rise["E"], x, strata["E"].primary, sigma_self=sE.vector(self_cell(sE).name, "sigma").astype(np.float64), sigma_shifts=sE.matrix(within, "sigma"))
    pt = t5.stores["E__plain_terms"]
    out["stranger"]["consistency"] = {"x_hat": out["stranger"]["x_hat"], "curve_1_one_text_in_these_stores": float(pt.rise(curve_1_cells(pt, "4")).mean(axis=0).mean()), "committed_value_on_the_papers_run": CURVE_1_ONE_TEXT_COMMITTED}
    log(f"[analyze s9] run 6: self against stranger on E: {out['stranger']['reading']}")
    # the ladder on E_lab, per source, and pooled on E^O (flagged)
    sL = t5.stores["E_lab__self_merge"]
    src_cells, gen_cells = partner_cells(sL, "source"), partner_cells(sL, "general")
    e_src, e_gen = sL.rise(src_cells), sL.rise(gen_cells)
    same = partner_table(sL, src_cells)["same_document"]
    n_src, n_gen, n_self = sL.matrix(src_cells, "n_on"), sL.matrix(gen_cells, "n_on"), sL.vector(self_cell(sL).name, "n_on").astype(np.float64)
    ladder, standing = [], {}
    for key in [k for k in strata if k.startswith("source:")] + ["O"]:
        S = strata[key]
        # each rung over all of E_lab, (shifts, N); a stratum takes its own columns
        rungs = (("the text itself", rise["E_lab"][None, :], np.ones((1, sL.n), bool), n_self[None, :]), ("a partner from the same document", e_src, same, n_src),
                 ("a partner from the same source, another document", e_src, ~same, n_src), ("a general partner", e_gen, np.ones_like(same), n_gen))
        for name, ee, q, cc in rungs:
            v = beside(S, lambda T, rs, nd: s9.ladder_rung(ee[:, T.mask], q[:, T.mask], rs, n_documents=nd, count_shifts=cc[:, T.mask]))
            ladder.append({"stratum": key, "rung": name, "n_texts": v["n_texts"], "n_text_shift_pairs": v["n_text_shift_pairs"], "n_documents": S.n_documents, "m": v["m"], "mean_rise": v["mean_rise"], **_lohi("interval", v["interval"]),
                           **_without(v, "mean_rise", "interval", "mean_rise"),
                           "nonfinite_share": v["nonfinite_share"], "interval_flag": v["interval_flag"], "standing": v["standing"], **_lohi("interval_rows_beside", v["rows_beside"]["interval"] if v["rows_beside"] else None),
                           "mean_count": v.get("mean_count"), "flag": S.flag})
            if key.startswith("source:") and name == "a partner from the same source, another document":
                standing[key.split(":", 1)[1]] = v["standing"]
    out["ladder"] = ladder
    assert t5.run not in PAPER_RUNS or len(standing) == 5, f"the scope rule is written for the five sources of E_lab, not {sorted(standing)}"
    out["scope"] = s9.scope_rule(standing)  # four of the sources, as the rule fixed before the run has it (the stand-in has two sources, so its answer is always that the sources are named)
    out["scope"]["n_sources"] = len(standing)
    log(f"[analyze s9] run 6: the scope rule: within one kind of text: {out['scope']['within_one_kind_of_text']}")
    return out


# ----------------------------------------------------------------------------- runs 3 and 7


def mask_words(c: Cell) -> str:
    if c.family == "reference":
        return {"unmasked": "the full decomposed model (every piece on)", "unmasked_delta": "the full decomposed model with the residual", "importances": "own labels"}.get(str(c.condition), str(c.condition))
    if c.family == "external":
        return f"comparison model {c.model}"
    if c.family == "self_union":
        return "self-merge (the text's own named pieces)"
    if c.family == "partner_union":
        return f"partner's set, arm {c.arm}, shift {c.shift}"
    if c.family == "union":
        donors = {"D_unif": "general", "D_code": "code", "D_prose": "prose"}.get(str(c.donor_pool), str(c.donor_pool))
        return (f"same-size random set, beside the merge of {donors} donors" if c.control == "plain" else f"merge of {donors} donors") + f", {size_words(c.rung)}"
    if c.family == "soft_erase":
        return f"soft erase of what general donors name, {size_words(c.rung)}"
    if c.family == "never_named_hard":
        return "removal of the never-named pieces (the whole set)"
    if c.family == "code_leaning_hard":
        return f"code-leaning edit, {c.rung[1:]} members"
    return c.family


def group_key(c: Cell) -> str:
    """The cells of one mask differ by draw only."""
    return dataclasses.replace(c, draw=0).name


def mask_groups(store: Store5, names: list[str]) -> dict[str, list[Cell]]:
    groups: dict[str, list[Cell]] = {}
    for n in names:
        groups.setdefault(group_key(store.objects[n]), []).append(store.objects[n])
    for cs in groups.values():
        cs.sort(key=lambda c: c.draw)
    return groups


def baseline_name(store: Store5, c: Cell) -> str | None:
    """Own labels for a merge; the full model for a removal (`cells.reference_for`). A reference has none: it is a baseline."""
    if c.family in ("reference", "external"):
        return None
    r = reference_for(c)
    assert r in ("importances", "unmasked", "unmasked_delta"), (c.name, r)
    return store.ref(r)


def per_text_counts(store: Store5, cell: str, target: dict[str, np.ndarray], ids: np.ndarray) -> dict[str, np.ndarray]:
    """A listed cell's per-text counts with the target's tied positions excluded (rule 1), after the gates: the
    all-position rate and the confident-position rate recomputed from the arrays, ties included, equal the stored per-text
    columns bit for bit; the share of positions whose top token is the real next token, recomputed with the saved ids, equals its
    column (which also holds the saved ids to the launch's); the stored probability on the target's top token averages to its
    column."""
    top = store.extra(f"{cell}__top", (SEQ_LEN,), "uint16")
    c = s9.change_rates_excluding_ties(top, target["top"], target["tie"], target["top_p"])
    assert np.array_equal(c["rate_with_ties"], store.vector(cell, "top_changed").astype(np.float32)), f"THE GATE FAILS: {store.name}: {cell}: the all-position change rate recomputed from the arrays is not the stored column"
    n_c, k_c = c["n_confident_with_ties"], c["n_changed_confident_with_ties"]
    with np.errstate(invalid="ignore", divide="ignore"):
        conf = np.where(n_c > 0, k_c.astype(np.float32) / np.maximum(n_c, 1).astype(np.float32), np.float32("nan")).astype(np.float32)
    assert np.array_equal(conf, store.vector(cell, "top_changed_confident").astype(np.float32), equal_nan=True), f"THE GATE FAILS: {store.name}: {cell}: the confident-position rate recomputed from the arrays is not the stored column"
    assert np.array_equal(s9.confident_counts_from_columns(store.vector(cell, "top_changed_confident"), n_c), k_c), f"{store.name}: {cell}: rate times count does not recover the changed confident positions"
    is_next = (top[:, :-1].astype(np.int64) == ids[:, 1:].astype(np.int64)).mean(axis=1)
    assert np.max(np.abs(is_next - store.vector(cell, "top_is_next").astype(np.float64))) <= TOP_IS_NEXT_TOLERANCE, f"{store.name}: {cell}: top_is_next recomputed with the saved ids is not the stored column (are these the launch's ids?)"
    p = store.extra(f"{cell}__p_target_top", (SEQ_LEN,), "float16").astype(np.float64)
    assert np.max(np.abs(p.mean(axis=1) - store.vector(cell, "p_target_top").astype(np.float64))) <= 1e-3, f"{store.name}: {cell}: the stored probability on the target's top token does not average to its column"
    return {**c, "changed": top != target["top"], "p_target_top_positions": p}


def _sum(cs: list[dict[str, np.ndarray]], key: str) -> np.ndarray:
    return np.sum([c[key] for c in cs], axis=0).astype(np.float64)


def rate_block(S: Stratum, tag: str, num: np.ndarray, den: np.ndarray, base: tuple[np.ndarray, np.ndarray] | None) -> dict[str, Any]:
    """A rate as a ratio of sums over texts with its interval and, with a baseline on the same texts, its paired rise; on E_lab the
    row-level intervals beside. The share of undefined replicates is printed with each."""
    assert num.shape == den.shape == S.mask.shape and bool(S.mask.all()), "the plain-terms tables are read on a whole evaluation set"
    own = beside(S, lambda T, rs, nd: s9.rate_of_sums(num[T.mask], den[T.mask], rs))
    out = {tag: own["rate"], **_lohi(f"{tag}_interval", own["interval"]), **_lohi(f"{tag}_interval_rows_beside", own["rows_beside"]["interval"] if own["rows_beside"] else None), f"{tag}_nonfinite_share": own["nonfinite_share"],
           **_without(own, "rate", "interval", tag)}
    if base is not None:
        rise = beside(S, lambda T, rs, nd: s9.rate_of_sums_rise(num[T.mask], den[T.mask], base[0][T.mask], base[1][T.mask], rs))
        assert rise["rate"] == own["rate"]
        out.update({f"{tag}_baseline": rise["baseline"], f"{tag}_rise": rise["rise"], **_lohi(f"{tag}_rise_interval", rise["rise_interval"]), **_without(rise, "rise", "rise_interval", f"{tag}_rise"),
                    **_lohi(f"{tag}_rise_interval_rows_beside", rise["rows_beside"]["rise_interval"] if rise["rows_beside"] else None), f"{tag}_rise_nonfinite_share": rise["nonfinite_share"]})
    return out


def mean_block(S: Stratum, tag: str, v: np.ndarray, base: np.ndarray | None) -> dict[str, Any]:
    """A per-text column's mean with its interval and its paired rise over the baseline's column."""
    assert v.shape == S.mask.shape and bool(S.mask.all()), "the plain-terms tables are read on a whole evaluation set"
    m = beside(S, lambda T, rs, nd: s9.paired_mean(v[T.mask], base[T.mask] if base is not None else None, rs))
    out = {tag: m["mean"], **_lohi(f"{tag}_interval", m["interval"]), **_lohi(f"{tag}_interval_rows_beside", m["rows_beside"]["interval"] if m["rows_beside"] else None), **_without(m, "mean", "interval", tag)}
    if base is not None:
        out.update({f"{tag}_baseline": m["baseline"], f"{tag}_rise": m["rise"], **_lohi(f"{tag}_rise_interval", m["rise_interval"]), **_without(m, "rise", "rise_interval", f"{tag}_rise"), **_lohi(f"{tag}_rise_interval_rows_beside", m["rows_beside"]["rise_interval"] if m["rows_beside"] else None)})
    return out


def plain_terms_tables(t5: Tier5, inp: Inputs, strata: dict[str, Stratum], log: Any = print) -> dict[str, Any]:
    """For every listed mask: the change rate against the target with the target's ties excluded, the same among confident
    positions as a ratio of sums, the probability on the target's top token, the real-text loss, the share of positions whose top
    token is the real next token; each with its interval and its paired rise over its baseline. For the other cells, which keep
    no arrays, the confident-position rate only. The bin table, pooled over the listed masks on E."""
    listed_rows, unlisted_rows, bin_tables, gates = [], [], [], {}
    target_rec: dict[str, Any] = {}
    seen_groups: set[str] = set()
    for sname in ("E__plain_terms", "E__self_merge", "E_lab__plain_terms", "E_lab__same_domain", "E_lab__self_merge", "D_unif__self_merge"):
        store = t5.stores[sname]
        S = strata[store.eval_set]
        assert s9.has_interval(S.n_documents), f"{store.eval_set}: a whole evaluation set of {S.n_documents} documents has no interval; the plain-terms tables are not written for that"
        ids = inp.ids[store.eval_set]
        assert ids.shape == (store.n, SEQ_LEN), (sname, ids.shape)
        target = store.target_arrays()
        conf_all = (target["top_p"] >= 0.5)
        n_conf_with_ties = conf_all.sum(axis=1)
        tcell = store.ref("target")
        target_rec[store.eval_set] = {"tied_share": float(target["tie"].mean()), "n_tied_confident_positions": int((target["tie"] & conf_all).sum()), "confident_share": float(conf_all.mean()),
                                      "p_target_top": float(store.vector(tcell, "p_target_top").astype(np.float64).mean()), "ce": float(store.vector(tcell, "ce").astype(np.float64).mean()),
                                      "top_is_next": float(store.vector(tcell, "top_is_next").astype(np.float64).mean())}
        counts_of: dict[str, dict[str, np.ndarray]] = {}
        listed = [n for n in store.listed]
        for n in listed:
            counts_of[n] = per_text_counts(store, n, target, ids)
        gates[sname] = {"n_listed_cells_gated": len(listed), "pass": True}

        def columns(cs: list[Cell], col: str) -> np.ndarray:
            v = store.matrix(cs, col)
            assert np.isfinite(v).all(), f"{sname}: column {col} of {cs[0].name} is not finite"
            return v.mean(axis=0)

        for key, cs in mask_groups(store, [n for n in store.cells.index if store.objects[n].family != "reference" or n in listed]).items():
            c0 = cs[0]
            if c0.family == "reference" and c0.condition == "target":
                continue
            if key in seen_groups:  # the three listed references are in every store of a set, and bitwise equal across them: once
                assert c0.family == "reference", f"{key}: a mask that is not a reference appears in two tier-5 stores"
                continue
            seen_groups.add(key)
            base = baseline_name(store, c0)
            is_listed = all(c.name in counts_of for c in cs)
            assert is_listed or not any(c.name in counts_of for c in cs), f"{key}: some draws of this mask keep arrays and some do not"
            row: dict[str, Any] = {"store": sname, "set": store.eval_set, "mask": key, "in_words": mask_words(c0), "n_draws": len(cs), "baseline": base or "", "n_documents": S.n_documents, "flag": S.flag}
            if is_listed:
                # from the per-position arrays, the target's tied positions excluded from numerator and denominator alike (rule 1)
                got = [counts_of[c.name] for c in cs]
                assert base is None or base in counts_of, f"{key}: its baseline {base} keeps no arrays in {sname}"
                for tag, num, den in (("change_rate", "n_changed", "n"), ("change_rate_confident", "n_changed_confident", "n_confident")):
                    row.update(rate_block(S, tag, _sum(got, num), _sum(got, den), (counts_of[base][num].astype(np.float64), counts_of[base][den].astype(np.float64)) if base else None))
                row["tied_share_excluded"] = target_rec[store.eval_set]["tied_share"]
                if c0.family != "external" and store.eval_set == "E":  # the bin table pools the listed masks on E; a comparison model is not a mask
                    for c in cs:
                        bin_tables.append(s9.bin_table(store.kl_array(c.name), counts_of[c.name]["changed"], counts_of[c.name]["p_target_top_positions"], exclude=target["tie"]))
            else:
                # no arrays: the confident-position rate only, its numerator recovered exactly as the stored rate times the text's count of confident positions
                k = np.sum([s9.confident_counts_from_columns(store.vector(c.name, "top_changed_confident"), n_conf_with_ties) for c in cs], axis=0).astype(np.float64)
                kb = s9.confident_counts_from_columns(store.vector(base, "top_changed_confident"), n_conf_with_ties).astype(np.float64) if base else None
                row.update(rate_block(S, "change_rate_confident", k, (len(cs) * n_conf_with_ties).astype(np.float64), (kb, n_conf_with_ties.astype(np.float64)) if base else None))
                row["ties_among_confident_positions_not_excluded"] = target_rec[store.eval_set]["n_tied_confident_positions"]
            for col in ("p_target_top", "ce", "top_is_next"):
                row.update(mean_block(S, col, columns(cs, col), store.vector(base, col).astype(np.float64) if base else None))
                row[f"{col}_target"] = target_rec[store.eval_set][col]
            (listed_rows if is_listed else unlisted_rows).append(row)
    assert bin_tables, "no listed mask on E"
    log(f"[analyze s9] runs 3 and 7: the gate of rule 1 passes on {sum(g['n_listed_cells_gated'] for g in gates.values())} listed cells (all-position and confident rates equal the stored columns bit for bit)")
    return {"listed": listed_rows, "unlisted": unlisted_rows, "bins": s9.pool_bin_tables(bin_tables), "n_masks_in_bins": len(bin_tables), "target": target_rec, "gates": gates}


def examples_by_rule(t5: Tier5, inp: Inputs, master_seed: int, log: Any = print) -> dict[str, Any]:
    """The examples chosen by rule. Mask: curve 1 at one whole text, draw 0, on E; the 10th, 50th, 90th, 99th percentiles of its
    per-position divergence over all positions; among the stored example positions whose 48 context tokens decode without a
    replacement character, the nearest (ties to the lowest text, then position) is shown and the five nearest written out, with
    the top five under the target, own labels, and the merge at 8 tokens, 64 tokens, and one text. One further example for the
    never-named removal at its median. Nobody picks an example after seeing it."""
    from vpd_audit import tier5 as t5m

    store = t5.stores["E__plain_terms"]
    ids = inp.ids["E"]
    assert ids.shape == (store.n, SEQ_LEN)
    positions = t5m.example_positions(store.n, master_seed=master_seed)
    rec = t5m.assert_example_positions(positions, t5.run, required=t5.run in PAPER_RUNS, log=log)
    assert store.manifest["extra"]["tier5"]["example_positions"] == list(positions.shape) and store.manifest["master_seed"] == master_seed, "the example positions are the launch's only under the launch's master seed"
    tok_name = inp.tokenizer_name

    def dec(x: Any) -> str:
        return inp.decode([int(t) for t in np.atleast_1d(x)])

    P = positions.shape[1]
    eligible = np.zeros(positions.shape, dtype=bool)
    context: dict[tuple[int, int], str] = {}
    for b in range(store.n):
        for p in range(P):
            t = int(positions[b, p])
            assert CONTEXT_TOKENS - 1 <= t <= SEQ_LEN - 2
            context[(b, p)] = dec(ids[b, t - CONTEXT_TOKENS + 1 : t + 1])
            eligible[b, p] = REPLACEMENT not in context[(b, p)]
    target = store.target_arrays()

    def top5(stem: str) -> tuple[np.ndarray, np.ndarray]:
        i5, p5 = store.extra(f"{stem}__top5_ids", (P, 5), "uint16"), store.extra(f"{stem}__top5_p", (P, 5), "float32")
        assert np.isfinite(p5).all() and (np.diff(p5, axis=-1) <= 0).all(), f"{stem}: the top five are not in descending probability"
        top_at = np.take_along_axis(target["top"] if stem == "target" else store.extra(f"{stem}__top", (SEQ_LEN,), "uint16"), positions, axis=1)
        clear = p5[..., 0] > p5[..., 1]
        mismatch = float((i5[..., 0] != top_at)[clear].mean()) if clear.any() else 0.0
        assert mismatch <= TOP5_MISMATCH_MAX, f"{stem}: the first of the stored top five is not the stored top token at the example positions ({mismatch:.3f} of them): the positions do not line up"
        return i5, p5

    run = t5.run
    merge = {r: curve_1_cells(store, r)[0].name for r in ("2", "3", "4")}  # draw 0 of curve 1 at 8 tokens, 64 tokens, and one whole text
    assert all(store.objects[n].draw == 0 for n in merge.values())
    never = _one([c for c in store.objects.values() if c.family == "never_named_hard"], "the never-named removal").name
    shown_for = {"merge": (merge["4"], s9.EXAMPLE_PERCENTILES, [("the original model", "target"), ("own labels", store.ref("importances"))] + [(f"the merge of general donors, {size_words(r)}", merge[r]) for r in ("2", "3", "4")]),
                 "never_named": (never, (50.0,), [("the original model", "target"), ("the full decomposed model with the residual", store.ref("unmasked_delta")), ("the removal of the never-named pieces", never)])}
    out: dict[str, Any] = {"tokenizer": tok_name, "positions": rec, "n_eligible": int(eligible.sum()), "n_positions": int(eligible.size), "rows": [], "blocks": []}
    for kind, (mask_cell, percentiles, shown) in shown_for.items():
        assert mask_cell in store.listed, f"{mask_cell} keeps no arrays in {store.name}"
        kl = store.kl_array(mask_cell)
        tops = {label: top5(stem) for label, stem in shown}
        for pick in s9.choose_examples(kl, positions, eligible, percentiles=percentiles):
            for rank, ex in enumerate(pick["nearest"]):
                b, t = ex["seq"], ex["position"]
                p = int(np.flatnonzero(positions[b] == t)[0])
                row = {"example_of": kind, "mask": mask_cell, "percentile": pick["percentile"], "percentile_value": pick["value"], "rank_by_nearness": rank, "shown": rank == 0, "seq": b, "position": t, "kl_at_position": ex["kl"],
                       "context": context[(b, p)], "real_next_token": dec(ids[b, t + 1])}
                for label, (i5, p5) in tops.items():
                    row[f"top5: {label}"] = "; ".join(f"{dec(i5[b, p, j])!r} {p5[b, p, j]:.3f}" for j in range(5))
                out["rows"].append(row)
    return out


def yardstick(t5: Tier5, spec: RunSpec, strata: dict[str, Stratum], plain: dict[str, Any], log: Any = print) -> dict[str, Any]:
    """Per comparison model and set: both directions of the divergence, both models' cross-entropy, top-token agreement (ties
    excluded), the probability on the target's top token, and the divergence between the two comparison models. And the five
    ratios the post will quote, each an absolute divergence on E over the divergence to the primary comparison model."""
    from vpd_audit.cells import EXTERNAL_MODEL_KEYS

    ext = {s.name: sorted((c for c in s.objects.values() if c.family == "external"), key=lambda c: list(EXTERNAL_MODEL_KEYS).index(c.model)) for s in t5.stores.values()}  # the primary model first
    if not spec.has_external:
        assert not any(ext.values()), "external-model cells in a run that should have none"
        return {"available": False, "reason": "the stand-in has another tokenizer: no comparison model ran (the fake-model test of tests/test_tier5.py and tests/test_analysis_s9.py cover this path)"}
    assert all(not v for k, v in ext.items() if k not in ("E__plain_terms", "E_lab__plain_terms")), "a comparison model outside the plain_terms stores"
    rows = []
    for sname in ("E__plain_terms", "E_lab__plain_terms"):
        store = t5.stores[sname]
        S = strata[store.eval_set]
        assert [c.model for c in ext[sname]] == list(EXTERNAL_MODEL_KEYS), f"{sname}: comparison models {[c.model for c in ext[sname]]}"
        lab = next(r for r in plain["listed"] if r["set"] == store.eval_set and r["mask"] == group_key(store.objects[store.ref("importances")]))
        for c in ext[sname]:
            assert (store.vector(c.name, "precision") == "fp32").all()
            prow = next(r for r in plain["listed"] if r["mask"] == group_key(c))
            row: dict[str, Any] = {"model": c.model, "set": store.eval_set, "n_documents": S.n_documents, "flag": S.flag}
            for tag, col in (("kl_target_to_model", "kl_mean"), ("kl_model_to_target", "kl_reverse_mean"), ("kl_this_model_from_the_other", "kl_other_mean"), ("ce_model", "ce"), ("ce_target", "ce_target"), ("padded_mass_mean", "padded_mass_mean")):
                vec = store.vector(c.name, col).astype(np.float64)
                assert np.isfinite(vec).all(), f"{c.name}: column {col} is not finite"
                row.update(mean_block(S, tag, vec, None))
            row.update({"top_token_agreement": 1.0 - prow["change_rate"], "top_token_agreement_interval_lo": 1.0 - prow["change_rate_interval_hi"], "top_token_agreement_interval_hi": 1.0 - prow["change_rate_interval_lo"],
                        "top_token_agreement_own_labels": 1.0 - lab["change_rate"], "tied_share_excluded": prow["tied_share_excluded"], "p_target_top": prow["p_target_top"], "p_target_top_own_labels": lab["p_target_top"], "p_target_top_target": prow["p_target_top_target"]})
            rows.append(row)
    # the five ratios on E, over the divergence to the primary comparison model
    pt, sm, rsE = t5.stores["E__plain_terms"], t5.stores["E__self_merge"], strata["E"].primary
    primary = _one([c for c in ext["E__plain_terms"] if c.model == EXTERNAL_MODEL_KEYS[0]], "the primary comparison model on E")
    den = pt.vector(primary.name, "kl_mean").astype(np.float64)

    def curve1(r: str) -> np.ndarray:
        return pt.matrix(curve_1_cells(pt, r), "kl_mean").mean(axis=0)

    absolute = {"own labels": pt.vector(pt.ref("importances"), "kl_mean").astype(np.float64), "the 64-token merge": curve1("3"), "the one-text merge": curve1("4"), "the self-merge": sm.vector(self_cell(sm).name, "kl_mean").astype(np.float64),
                "the never-named removal": pt.vector(_one([c for c in pt.objects.values() if c.family == "never_named_hard"], "the never-named removal").name, "kl_mean").astype(np.float64)}
    points = s9.yardstick_ratios({k: float(v.mean()) for k, v in absolute.items()}, float(den.mean()))
    ratios = []
    for k, v in absolute.items():
        r = s9.rate_of_sums(v, den, rsE)
        assert abs(r["rate"] - points[k]) <= 1e-12 * max(1.0, abs(points[k]))
        ratios.append({"quantity": k, "divergence_on_E": float(v.mean()), "divergence_to_the_primary_comparison_model": float(den.mean()), "comparison_model": primary.model, "ratio": points[k], **_lohi("ratio_interval", r["interval"]), "nonfinite_share": r["nonfinite_share"]})
    return {"available": True, "table": rows, "ratios": ratios}


# ----------------------------------------------------------------------------- the report and the command


def _jsonable(o: Any) -> Any:
    if isinstance(o, dict):
        return {str(k): _jsonable(v) for k, v in o.items()}
    if isinstance(o, (list, tuple)):
        return [_jsonable(v) for v in o]
    if isinstance(o, np.ndarray):
        return o.tolist()
    if isinstance(o, (np.floating, np.integer, np.bool_)):
        return o.item()
    if isinstance(o, float) and not np.isfinite(o):
        return None
    return o if isinstance(o, (str, int, float, bool, type(None))) else str(o)


def count_only_rows(co: dict[str, Any]) -> list[dict[str, Any]]:
    rows = []
    for key, v in co.items():
        for j, r in v["per_size"].items():
            rb = (v["rows_beside"] or {}).get("per_size", {}).get(j) if v.get("rows_beside") else None
            rows.append({"amount_measured_as": v["amount"], "size": j, "size_words": size_words(j), "n_draws": r["n_draws"], "n_draws_predicted": r["n_draws_predicted"], "observed": r["observed"], "prediction": r["prediction"], "log_ratio": r["log_ratio"],
                         "m": v["m"], **_lohi("interval", r["interval"]), "nonfinite_share": r["nonfinite_share"], "end_segment_continued_share": r.get("end_segment_continued_share"), "readable": r["readable"], "reading": r["reading"], **_lohi("interval_rows_beside", rb["interval"] if rb else None),
                         "U_measured_range_lo": (v["measured_range"] or [None, None])[0], "U_measured_range_hi": (v["measured_range"] or [None, None])[1], "U_violators_pooled": v["U_curve"]["violators_pooled"]})
    return rows


def write_outputs(out_dir: Path, ctx: dict[str, Any]) -> Path:
    from vpd_audit.analysis import _md as _md_rows

    def _md(df: pd.DataFrame) -> str:
        d = df.copy()
        for c in d.columns:  # a count beside a float would be printed as a float (iterrows gives a row one dtype)
            if pd.api.types.is_integer_dtype(d[c]) or pd.api.types.is_bool_dtype(d[c]):
                d[c] = d[c].astype(str)
        return _md_rows(d)

    out_dir.mkdir(parents=True, exist_ok=True)
    r2, r6, pl, ex, ys = ctx["run2"], ctx["run6"], ctx["plain_terms"], ctx["examples"], ctx["yardstick"]
    rule_rows = [{"set": k, "n_texts": v["n_texts"], "n_documents": v["n_documents"], "m": v["m"], "rise": v["s_hat"], **_lohi("interval", v["interval"]), **_lohi("interval_rows_beside", v["rows_beside"]["interval"] if v["rows_beside"] else None),
                  **_without(v, "s_hat", "interval", "rise"), "material": v["material"], "material_without_flagged_sources": (v["without_flagged"] or {}).get("material"), "share_made_worse": v["share_made_worse"], **_lohi("share_made_worse_interval", v["share_made_worse_interval"]), **{f"share_above_{t}": x for t, x in v["share_above"].items()},
                  **{f"percentile_{p}": x for p, x in v["percentiles"].items()}, "rise_over_rounded_labels": v["s_hat_against_rounded_labels"], **_lohi("rise_over_rounded_labels_interval", v.get("s_hat_against_rounded_labels_interval")),
                  "own_labels_kl": v["own_labels_kl"], "self_merge_kl": v["self_merge_kl"], "n_on_mean": v["n_on_mean"], "sigma_mean": v["sigma_mean"], "flag": v["flag"]} for k, v in r6["rule"].items()]
    stg = r6["stranger"]
    stranger_rows = [{"self": stg["s_hat"], "stranger": stg["x_hat"], "difference": stg["delta_hat"], **_lohi("difference_interval", stg["interval"]), "reading": stg["reading"], "share_of_texts_self_worse": stg["share_delta_positive"],
                      "per_unit_self": stg["per_unit"]["self"], "per_unit_stranger": stg["per_unit"]["stranger"], "per_unit_difference": stg["per_unit"]["difference"], **_lohi("per_unit_difference_interval", stg["per_unit"]["interval"]),
                      "per_unit_nonfinite_share": stg["per_unit"]["nonfinite_share"], **{f"consistency_{k}": v for k, v in stg["consistency"].items()}}]
    vd = r2["verdict"]
    verdict_rows = [{"gate_arm_U_fails_on_the_code_texts": vd["gate"], "U_label": vd["U_label"], "C_label": vd["C_label"], "outcome": vd["outcome"], "C_first_detected": vd["C_first_detected"], "C_first_material": vd["C_first_material"], "U_first_material": vd["U_first_material"],
                     "sizes_reaching_0.05": ", ".join(vd.get("sizes_reaching_X", [])), "reason": vd.get("reason", ""), "n_documents": vd["n_documents"], "outcome_rows_beside_not_read": (vd["rows_beside"] or {}).get("outcome")}]
    co = r2["count_only"]
    u_points = [{"amount_measured_as": v["amount"], **p, "size_words": size_words(p["size"])} for v in co.values() for p in v["U_points"]]  # p holds the point's own amount, rise, and whether it is used
    tables: dict[str, pd.DataFrame] = {
        "s9_run2_verdict": pd.DataFrame(verdict_rows), "s9_run2_curves": pd.DataFrame(r2["curves"]), "s9_run2_match_ratio": pd.DataFrame(r2["match_ratio"]), "s9_run2_contrast_C_minus_U": pd.DataFrame(r2["contrast_C_minus_U"]),
        "s9_run2_per_unit": pd.DataFrame(r2["per_unit"]), "s9_run2_lambda": pd.DataFrame([{k: v for k, v in {**r2["lambda"], **_lohi("interval", r2["lambda"]["interval"]), **_lohi("interval_rows_beside", r2["lambda"]["interval_rows_beside"]),
                                                                           **_lohi("interval_without_flagged_sources", r2["lambda"]["interval_without_flagged_sources"])}.items()
                                         if k not in ("interval", "interval_rows_beside", "interval_without_flagged_sources")}]),
        "s9_run2_controls": pd.DataFrame(r2["controls"]), "s9_run2_count_only": pd.DataFrame(count_only_rows(co)), "s9_run2_count_only_U_points": pd.DataFrame(u_points),
        "s9_run6_self_merge_rule": pd.DataFrame(rule_rows), "s9_run6_self_against_stranger": pd.DataFrame(stranger_rows), "s9_run6_ladder": pd.DataFrame(r6["ladder"]),
        "s9_run6_scope": pd.DataFrame([{"within_one_kind_of_text": r6["scope"]["within_one_kind_of_text"], "standing": r6["scope"]["standing"], "needed": r6["scope"]["needed"], "n_sources": r6["scope"]["n_sources"],
                                        **{f"sources_{k}": ", ".join(v) for k, v in r6["scope"]["sources_by_standing"].items()}, "sources_without_standing": ", ".join(r6["scope"]["sources_without_standing"])}]),
        "s9_plain_terms_listed_masks": pd.DataFrame(pl["listed"]), "s9_plain_terms_other_cells": pd.DataFrame(pl["unlisted"]), "s9_plain_terms_bins": pd.DataFrame(pl["bins"]), "s9_examples": pd.DataFrame(ex["rows"])}
    if ys["available"]:
        tables["s9_yardstick"], tables["s9_yardstick_ratios"] = pd.DataFrame(ys["table"]), pd.DataFrame(ys["ratios"])
    for name, df in tables.items():
        df.to_csv(out_dir / f"{name}.csv", index=False)
    T = tables
    can = ctx["tier5"]["canary"]
    lam = r2["lambda"]
    lam_beside = "" if not lam["flag"] else f"; {lam['flag']}" + (f": {lam['lambda_without_flagged_sources']:+.4f}, interval {lam['interval_without_flagged_sources']}" if lam["lambda_without_flagged_sources"] is not None else "")
    L = [f"# The frozen analysis of tier 5 ({ctx['run']})", "",
         "Every reading rule below was fixed before any tier-5 store existed; the words are the rules' output (`vpd_audit/stats_s9.py`), and nothing here goes beyond what the rules return.", "",
         "## 0. What was asserted before anything was read", "",
         f"- Stores: {', '.join(sorted(ctx['tier5']['completeness']))}; each complete, every cell holding every text once. Commit {ctx['commit']['project'][:12]}, dirty flag {ctx['commit']['dirty']}; --frozen {ctx['frozen']}.",
         "- The bitwise canary against the committed stores: " + ("; ".join(f"{k}: {v['cells_bitwise_equal']} cells over {v['pairs_compared']} (cell, text) pairs, of which {v['n_reruns']} re-run cells" for k, v in can["stores"].items()) if can.get("checked") else "NOT CHECKED (no committed roots were given)") + ".",
         "- The references and the target's arrays agree bitwise across the tier-5 stores of each set: " + "; ".join(f"{k}: {len(v['stores'])} stores" for k, v in can["across_stores"].items()) + ".",
         f"- Counts and the rotation (rule 3): {json.dumps(_jsonable(r6['asserts']))}.",
         f"- The gate of rule 1 (the rates recomputed from the arrays, ties included, equal the stored per-text columns bit for bit): {json.dumps(_jsonable(pl['gates']))}.",
         f"- Documents of E_lab: {json.dumps(_jsonable({k: {'texts': v['n_texts'], 'documents': v['n_documents']} for k, v in ctx['documents']['documents'].items()}))}. {ctx['replicates']} bootstrap replicates; master seed {ctx['master_seed']}.", "",
         "On E_lab the primary interval resamples documents within source; the row-level interval is printed beside it and never read. A stratum that pools several sources keeps the design's mix in every replicate: each statistic is taken per source "
         "and the sources are combined with fixed weights, their row shares, so point estimates are plain means over rows. A stratum of fewer than ten documents has a point value and no interval. A pooled interval that holds such a source is flagged in its row, "
         "and the same value on the stratum without that source is beside it (the columns `…_without_flagged_sources`).", "",
         "## 1. Run 2: merging within one kind of text", "", "**The gate and the verdict** (arms C and U on the code texts, all ten sizes compared, m = 10):", "", _md(T["s9_run2_verdict"]), "",
         "The two curves of the verdict (s9_run2_curves.csv holds every arm on every stratum and source):", "",
         _md(T["s9_run2_curves"][T["s9_run2_curves"].role == "verdict"][["arm", "size_words", "rise", "interval_documents_lo", "interval_documents_hi", "interval_rows_beside_lo", "interval_rows_beside_hi", "n_draws_positive", "detected", "material", "n_on_mean", "sigma_mean"]]), "",
         "**The match ratio R** (two-level, on log R, level 1 - 0.05/3; read at 8 tokens, 64 tokens, and 64 texts, and only where no replicate is undefined and the two-level interval of each of the four rises, at the same level, has its lower end above zero; printed and not read at one text):", "",
         _md(T["s9_run2_match_ratio"][["size_words", "r_code", "r_prose", "R", "R_interval_lo", "R_interval_hi", "all_four_rises_above_zero", "nonfinite_share", "size_is_read", "reading", "flag_prose"]]), "",
         "**Descriptions.** The contrast between code donors and general donors on the code texts (two-level; s9_run2_contrast_C_minus_U.csv), the harm per unit of mask moved from the per-text switched mass (s9_run2_per_unit.csv), each same-size random set against its own arm and no other (s9_run2_controls.csv), and the rises by source (s9_run2_curves.csv). "
         f"Lambda at 64 tokens: {r2['lambda']['lambda']:+.4f}, interval {r2['lambda']['interval']}, share of undefined replicates {r2['lambda']['nonfinite_share']}{lam_beside}.", "",
         _md(T["s9_run2_contrast_C_minus_U"][["size_words", "rise_C", "rise_U", "difference", "difference_interval_lo", "difference_interval_hi", "ratio", "ratio_interval_lo", "ratio_interval_hi", "ratio_nonfinite_share", "n_on_C", "n_on_U", "sigma_C", "sigma_U"]]), "",
         "**The count-only prediction** on the code texts (arm U's ten per-size points, made non-decreasing, log-log interpolation, each draw of arm C predicted from its own amount, no extrapolation; level 1 - 0.05/2 at 64 tokens and 64 texts; a quantity with an undefined replicate is not read):", "",
         _md(T["s9_run2_count_only"][["amount_measured_as", "size_words", "n_draws_predicted", "observed", "prediction", "log_ratio", "interval_lo", "interval_hi", "nonfinite_share", "end_segment_continued_share", "readable", "reading"]]), "",
         "`end_segment_continued_share`: of the (replicate, draw) predictions behind an interval, the share made on the continued end segment of that replicate's curve (the replicate's end points move a little; the range and the predicted draws are fixed from the full data). "
         "A note that changes no reading: the one-text knot of arm U's curve is a mean over draws whose amounts vary about fourfold on a convex curve, so it sits slightly high, which biases the 64-text reading against *above the prediction*; that is conservative.", "",
         "## 2. Run 6: the self-merge and the ladder", "", "**The rule** (level 1 - 0.05/3; material if the lower end exceeds 0.05):", "",
         _md(T["s9_run6_self_merge_rule"][["set", "n_texts", "n_documents", "rise", "interval_lo", "interval_hi", "material", "rise_without_flagged_sources", "rise_without_flagged_sources_interval_lo", "rise_without_flagged_sources_interval_hi", "share_made_worse", "share_above_0.05", "share_above_0.1", "share_above_0.2", "percentile_50", "rise_over_rounded_labels", "flag"]]), "",
         f"The post's summary may carry the self-merge: **{r6['summary_may_carry_the_self_merge']}** (it must be material on E).", "", "**Self against stranger on E:** " + stg["reading"] + ".", "", _md(T["s9_run6_self_against_stranger"]), "",
         "**The ladder on E_lab** (level 1 - 0.05/5 over documents; a text's qualifying shifts are averaged first; each rung prints its own mean count; a rung with any undefined replicate, which is one that drew no qualifying text, "
         "prints its value, its counts, and its interval, and has no standing):", "",
         _md(T["s9_run6_ladder"][["stratum", "rung", "n_texts", "n_text_shift_pairs", "n_documents", "mean_rise", "interval_lo", "interval_hi", "nonfinite_share", "standing", "mean_count", "mean_rise_without_flagged_sources", "flag"]]), "",
         f"**The scope rule:** the post may say \"within one kind of text\": **{r6['scope']['within_one_kind_of_text']}** (standing: {r6['scope']['standing']}; by standing: {r6['scope']['sources_by_standing']}; without standing: {r6['scope']['sources_without_standing']}).", "",
         "## 3. Runs 3 and 7: plain terms and the outside yardstick", "",
         "The target's own side, per set: " + json.dumps(_jsonable(pl["target"])) + ". Every all-position change rate excludes the target's tied positions; a confident-position rate is a ratio of sums over texts; no change rate is printed without its baseline.", "",
         _md(T["s9_plain_terms_listed_masks"][["set", "in_words", "n_draws", "change_rate", "change_rate_baseline", "change_rate_rise", "change_rate_confident", "change_rate_confident_baseline", "p_target_top", "p_target_top_baseline", "p_target_top_target", "ce", "ce_baseline", "ce_target", "top_is_next", "top_is_next_baseline"]]), "",
         f"The cells that keep no per-position arrays (the confident-position rate only): s9_plain_terms_other_cells.csv, {len(T['s9_plain_terms_other_cells'])} masks.", "",
         f"**By bin of per-position divergence**, pooled over the {pl['n_masks_in_bins']} listed mask cells on E (the target's tied positions excluded):", "", _md(T["s9_plain_terms_bins"]), "",
         f"**Examples, by rule** (tokenizer {ex['tokenizer']}; {ex['n_eligible']} of {ex['n_positions']} stored positions decode without a replacement character; the five nearest per percentile are in s9_examples.csv):", ""]
    for _, row in T["s9_examples"][T["s9_examples"].shown].iterrows():
        L += [f"- *{row['example_of']}, percentile {row['percentile']:g}* (value {row['percentile_value']:.4f}; text {row['seq']}, position {row['position']}, divergence there {row['kl_at_position']:.4f}). Context: {row['context']!r}. Real next token: {row['real_next_token']!r}."]
        L += [f"    - {c[6:]}: {row[c]}" for c in T["s9_examples"].columns if c.startswith("top5: ") and isinstance(row[c], str)]
    L += [""]
    if ys["available"]:
        L += ["**The outside yardstick:**", "", _md(T["s9_yardstick"][["model", "set", "kl_target_to_model", "kl_target_to_model_interval_lo", "kl_target_to_model_interval_hi", "kl_model_to_target", "kl_this_model_from_the_other", "ce_model", "ce_target",
                                                                              "top_token_agreement", "top_token_agreement_own_labels", "p_target_top", "p_target_top_own_labels", "flag"]]), "", "**The ratios the post will quote:**", "", _md(T["s9_yardstick_ratios"]), ""]
    else:
        L += [f"**The outside yardstick:** not available: {ys['reason']}.", ""]
    path = out_dir / "report.md"
    path.write_text("\n".join(L) + "\n")
    return path


def module_blobs() -> dict[str, Any]:
    def git(*args: str) -> str:
        return subprocess.run(["git", "-C", str(env.PROJECT_ROOT), *args], check=True, capture_output=True, text=True).stdout.strip()

    return {m: {"on_disk": git("hash-object", f"vpd_audit/{m}"), "at_head": git("rev-parse", f"HEAD:vpd_audit/{m}")} for m in ("stats_s9.py", "analysis_s9.py")}


def analyze_s9(root: Path, out_dir: Path, *, spec: RunSpec, frozen: str | None = None, committed_roots: tuple[Path, ...] | None = None, require_canary: bool = True, replicates: int = st.N_REPLICATES,
               master_seed: int = 0, inputs: Inputs | None = None, log: Any = print) -> dict[str, Any]:
    """`inputs`: the label-side inputs; None loads them from the saved sets (`load_inputs`), which is the only way the command
    runs. The tests hand in planted ones, never for a store of the paper's model."""
    from vpd_audit.results import code_commits

    t0 = time.time()
    t5 = load_tier5(Path(root), frozen=frozen, committed_roots=committed_roots, require_canary=require_canary, log=log)
    assert t5.run == spec.run, f"the stores are of run {t5.run!r}, the specification of {spec.run!r}"
    ctx: dict[str, Any] = {"run": t5.run, "root": str(root), "frozen": frozen, "commit": code_commits(), "replicates": replicates, "master_seed": master_seed,
                           "tier5": {"completeness": t5.completeness, "blindness": t5.blindness, "canary": t5.canary}}
    if t5.run in PAPER_RUNS:  # the content of the freeze guard, as the s9-checks command prints it: the six frozen statistics and analysis modules are main's blobs
        from vpd_audit.s9_checks import frozen_blobs

        ctx["frozen_modules"] = frozen_blobs()
        assert ctx["frozen_modules"]["pass"], "a frozen analysis module is not main's blob"
        blobs = module_blobs()
        assert all(v["on_disk"] == v["at_head"] for v in blobs.values()), blobs
        ctx["s9_module_blobs"] = blobs
    assert inputs is None or t5.run not in PAPER_RUNS, "the paper's stores are read with the saved sets, never with handed-in inputs"
    inp = inputs if inputs is not None else load_inputs(spec, t5)
    strata, docs = build_strata(inp, spec, t5, replicates, master_seed)
    ctx["documents"] = docs
    n_draws = t5.stores["E_lab__same_domain"].n_draws
    counts = draw_tables(n_draws, replicates, master_seed)
    ctx["run2"] = analyze_run2(t5, strata, counts, log)
    ctx["run6"] = analyze_run6(t5, strata, inp, log)
    ctx["plain_terms"] = plain_terms_tables(t5, inp, strata, log)
    ctx["examples"] = examples_by_rule(t5, inp, master_seed, log)
    ctx["yardstick"] = yardstick(t5, spec, strata, ctx["plain_terms"], log)
    path = write_outputs(Path(out_dir), ctx)
    summary = {"run": t5.run, "seconds": time.time() - t0, "report": path.name, "frozen": frozen, "commit": ctx["commit"], "replicates": replicates, "master_seed": master_seed, "canary": ctx["tier5"]["canary"],
               "completeness": ctx["tier5"]["completeness"], "documents": ctx["documents"], "s9_module_blobs": ctx.get("s9_module_blobs"),
               "run2": {"verdict": ctx["run2"]["verdict"], "R": {x["size"]: {"R": x["R"], "interval": [x["R_interval_lo"], x["R_interval_hi"]], "reading": x["reading"]} for x in ctx["run2"]["match_ratio"]}, "lambda": ctx["run2"]["lambda"],
                        "count_only": {k: {j: {"log_ratio": r["log_ratio"], "interval": r["interval"], "reading": r["reading"], "n_draws_predicted": r["n_draws_predicted"]} for j, r in v["per_size"].items()} for k, v in ctx["run2"]["count_only"].items()}},
               "run6": {"rule": {k: {"rise": v["s_hat"], "interval": v["interval"], "material": v["material"]} for k, v in ctx["run6"]["rule"].items()}, "summary_may_carry_the_self_merge": ctx["run6"]["summary_may_carry_the_self_merge"],
                        "stranger": {k: ctx["run6"]["stranger"][k] for k in ("s_hat", "x_hat", "delta_hat", "interval", "reading", "consistency")}, "scope": ctx["run6"]["scope"], "asserts": ctx["run6"]["asserts"]},
               "plain_terms": {"gates": ctx["plain_terms"]["gates"], "target": ctx["plain_terms"]["target"], "n_listed_masks": len(ctx["plain_terms"]["listed"]), "n_other_masks": len(ctx["plain_terms"]["unlisted"])},
               "examples": {k: ctx["examples"][k] for k in ("tokenizer", "positions", "n_eligible", "n_positions")}, "yardstick": {"available": ctx["yardstick"]["available"], "ratios": ctx["yardstick"].get("ratios")}}
    env.assert_no_absolute_path(summary, "summary.json")
    with open(Path(out_dir) / "summary.json", "w") as f:
        json.dump(_jsonable(summary), f, indent=2)
    log(f"[analyze s9] report written to {path} in {summary['seconds']:.0f} s")
    return summary
