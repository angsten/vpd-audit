"""The glue of analysis_s9.py on a fabricated tier-5 root with planted answers. The stand-in cannot
exercise the reading paths of run 2 (on SimpleStories every merge *lowers* the divergence, so the gate fails, R is undefined, and
the count-only curve has no positive point), and it has no comparison model. Here every rise, count, change pattern, and partner is
planted, in units of 1/4096 so that float32 storage is exact, and each join or stratum that could go wrong silently has a known
answer: the verdict and its gate, R = 0.5 from the worked example fixed in advance, the count-only reading, the controls (each with its own
arm), Lambda, the self-merge rule, self against stranger, the ladder and the scope rule, the three rules analysis_s9.py encodes, the bin
table, the examples, the yardstick and its ratios. What is planted differs across everything that could be confused: by arm, size,
source (every source its own rise in every arm), draw (each arm and each control its own pattern over the draws, so that every interval that resamples draws is held exactly to a direct computation with the pool's own table, and a
crossed table, a shifted control, reversed or unshared draws are each shown to fail it), document (of unequal size: each source
keeps its row share in every replicate), the two full-model references and the target, and the comparison models' values per set. Then the loader's refusals: the canary one ulp off, a missing or incomplete store, a store
of the paper's model without --frozen, a tampered partners table, a tampered column (the gate), the wrong token ids.

On the committed stand-in stores, when present (results/dry_run_s9): the whole command with the canary against the committed
stand-in stores."""

from __future__ import annotations

import dataclasses
import json
import shutil
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from vpd_audit import analysis_s9 as a9
from vpd_audit import stats as st
from vpd_audit import stats_s9 as s9
from vpd_audit import tier5
from vpd_audit.cells import Cell, _references, per_position_listed, tier_5_cells
from vpd_audit.constants import SEQ_LEN
from vpd_audit.s9_checks import contiguous_blocks, document_resample

ROOT = Path(__file__).resolve().parents[1]
RUN, K, T, U = "synthetic", 8, SEQ_LEN, 1.0 / 4096
REPLICATES = 300
# (source, rows, the rows of each of its documents): 12, 10, 10, 10, and 3 documents, of unequal size, so that a resample's row count varies and a pooled stratum's mix of sources would move if rows were pooled across sources
SOURCES = (("code", 24, (5, 1, 1, 3, 1, 2, 1, 4, 1, 2, 1, 2)), ("prose_a", 20, (4, 1, 1, 3, 1, 2, 1, 4, 1, 2)), ("prose_b", 20, (1, 1, 6, 1, 1, 2, 3, 1, 2, 2)), ("forum", 20, (3, 1, 2, 2, 4, 1, 1, 2, 3, 1)), ("papers", 9, (5, 3, 1)))
assert all(sum(sizes) == n for _, n, sizes in SOURCES)
N = {"E": 40, "E_lab": sum(n for _, n, _ in SOURCES), "D_unif": 50}
ROWS = {s: n for s, n, _ in SOURCES}
F = {"1": 1, "2": 4, "2a": 5, "2b": 6, "3": 7, "4": 8, "5": 8, "6": 9, "7": 10, "8": 10}  # a rise is (BASE[pool][source] * F[size] + DRAW[pool][draw]) / 4096
SIGMA = {"1": 100, "2": 400, "2a": 500, "2b": 600, "3": 700, "4": 800, "5": 850, "6": 900, "7": 1000, "8": 1100}  # the same in every arm: a draw of arm C sits on a knot of arm U's curve
# every source has its own rise in every arm, so that a stratum built from the wrong source, or weighted otherwise than by rows, shows. Over the two prose sources (20 rows each) the
# means are 18, 40, and 6, the worked example of R, fixed in advance, with 18 and 24 on the code texts: r_code = 18 / 24, r_prose = 6 / 18, R = 0.5
BASE = {"D_code": {"code": 18, "prose_a": 17, "prose_b": 19, "forum": 9, "papers": 12}, "D_unif": {"code": 60, "prose_a": 38, "prose_b": 42, "forum": 39, "papers": 43},
        "D_prose": {"code": 24, "prose_a": 5, "prose_b": 7, "forum": 8, "papers": 10}}
# the draws are not inert. Each arm and each control has its own pattern over the eight draws (each sums to zero, so every mean over draws is BASE * F), and an interval that
# resamples draws is asserted exactly against a direct computation with the pool's own table: a crossed table, a control paired with another draw, draws out of order, or no draw resampling all fail it
DRAW = {"D_code": (-7, -5, -3, -1, 1, 3, 5, 7), "D_unif": (-4, -3, -2, -1, 1, 2, 3, 4), "D_prose": (3, 2, 1, 0, 0, -1, -2, -3)}
CONTROL_BASE, CONTROL_DRAW = 2, {"D_code": (1, -1, 1, -1, 1, -1, 1, -1), "D_unif": (-1, -1, 1, 1, -1, -1, 1, 1)}
assert all(sum(v) == 0 for v in (*DRAW.values(), *CONTROL_DRAW.values()))
OWN_LABELS, ROUNDED, UNMASKED, UNMASKED_DELTA = 0.25, 0.1875, 1.0 / 64, 1.0 / 128  # the full model with the residual is not the target, so a removal read against the wrong one of the two shows
SELF = {"E": 256, "D_unif": 0, "code": 256, "prose_a": 300, "prose_b": 320, "forum": 280, "papers": 260}  # the self-merge's rise, in 1/4096 (0.05 is 204.8)
STRANGER, SAME_DOCUMENT, OTHER_DOCUMENT, GENERAL, CURVE_1 = 2048, 100, 250, 300, {"1": 16, "2": 160, "2a": 400, "2b": 900, "3": 1800, "4": 2000, "8": 2400}
# the comparison models' values differ between the two sets, so the ratios' denominator taken from the wrong store shows
PYTHIA = {"E": {"pythia-70m": {"kl": 2.0, "reverse": 2.5, "other": 0.5, "ce": 3.25}, "pythia-160m": {"kl": 1.5, "reverse": 1.75, "other": 0.375, "ce": 3.0}},
          "E_lab": {"pythia-70m": {"kl": 2.25, "reverse": 2.75, "other": 0.625, "ce": 3.5}, "pythia-160m": {"kl": 1.75, "reverse": 2.0, "other": 0.4375, "ce": 3.125}}}


def base_mean(pool: str, sources: tuple[str, ...]) -> float:
    """The row-weighted mean of a pool's planted base over a stratum's sources."""
    return sum(ROWS[s] * BASE[pool][s] for s in sources) / sum(ROWS[s] for s in sources)


PROSE, OTHER, OTHER_NO_PAPERS = ("prose_a", "prose_b"), ("prose_a", "prose_b", "forum", "papers"), ("prose_a", "prose_b", "forum")
assert (base_mean("D_code", PROSE), base_mean("D_unif", PROSE), base_mean("D_prose", PROSE)) == (18, 40, 6)
SPEC = a9.RunSpec(run=RUN, set_map={}, pool_map={}, code_sources=("code",), prose_sources=("prose_a", "prose_b"), synthetic_document_rows=None, tokenizer=None, has_external=True)


def lab_sources() -> tuple[list[str], np.ndarray]:
    src, docs, d = [], [], 0
    for s, _, sizes in SOURCES:
        for size in sizes:
            src += [s] * size
            docs += [d] * size
            d += 1
    return src, np.asarray(docs, dtype=np.int64)


def make_inputs() -> a9.Inputs:
    rng = np.random.default_rng(11)
    ids = {k: rng.integers(1, 100, size=(n, T)).astype(np.int32) for k, n in N.items()}
    ids["E"][0] = 0  # id 0 decodes to the replacement character: no example may come from text 0
    src, docs = lab_sources()
    return a9.Inputs(sources=src, documents=docs, ids=ids, decode=lambda x: " ".join(a9.REPLACEMENT if int(t) == 0 else f"w{int(t)}" for t in x), tokenizer_name="planted", record={})


def target_side(n: int, seed: int) -> dict[str, np.ndarray]:
    """The target's arrays: texts with 256 confident positions alternate with texts of 16 (so that a ratio of sums is not a mean of
    rates); the first two positions of every text are tied."""
    rng = np.random.default_rng(seed)
    cb = np.where(np.arange(n) % 2 == 0, 256, 16)
    top_p = np.full((n, T), 0.25, dtype=np.float32)
    for b in range(n):
        top_p[b, T - cb[b]:] = 0.75
    tie = np.zeros((n, T), dtype=bool)
    tie[:, :2] = True
    return {"top": rng.integers(1, 100, size=(n, T)).astype(np.uint16), "top_p": top_p, "tie": tie, "cb": cb}


def changed_positions(target: dict[str, np.ndarray], m: int, mc: int) -> np.ndarray:
    """A cell changes the first m positions of every text (the two tied ones among them) and the first mc of its confident block."""
    n = target["top"].shape[0]
    ch = np.zeros((n, T), dtype=bool)
    ch[:, :m] = True
    for b in range(n):
        s = T - int(target["cb"][b])
        ch[b, s : s + min(mc, int(target["cb"][b]))] = True
    return ch


def change_pattern(c: Cell) -> tuple[int, int, float, float]:
    """(m, mc, the probability left on the target's top token, the loss) of a cell."""
    if c.family == "reference":
        return {"target": (0, 0, 0.625, 2.5), "unmasked": (4, 0, 0.5, 2.5625), "unmasked_delta": (6, 1, 0.5625, 2.53125), "importances": (100, 8, 0.5, 3.0)}.get(str(c.condition), (50, 4, 0.5, 3.0))
    if c.family == "external":
        return (200, 100, 0.25, PYTHIA[c.eval_set][str(c.model)]["ce"])  # m stays below 256 everywhere, so that the two changed blocks never overlap
    if c.family == "never_named_hard":
        return (150, 10, 0.375, 3.25)
    if c.family == "code_leaning_hard":
        return (20, 2, 0.5, 2.75)
    if c.family == "self_union":
        return (180, 16, 0.375, 3.25)
    i = list(F).index(c.rung) if c.rung in F else 5
    return (110 + 10 * i + c.draw, 9 + i, 0.25, 3.5)  # the draws of one mask differ: a mask's rate pools them


def per_document_wobble(docs: np.ndarray) -> np.ndarray:
    return np.where(docs % 2 == 0, 40, -40)


def planted_kl(c: Cell, src: list[str], docs: np.ndarray) -> np.ndarray:
    """The per-text mean divergence of a cell, float32-exact."""
    n = N[c.eval_set]
    if c.family == "reference":
        return np.full(n, {"target": 0.0, "unmasked": UNMASKED, "unmasked_delta": UNMASKED_DELTA, "importances": OWN_LABELS, "rounded_0.1": ROUNDED}.get(str(c.condition), 0.5))
    if c.family == "external":
        return np.full(n, PYTHIA[c.eval_set][str(c.model)]["kl"])
    if c.family == "never_named_hard":
        return np.full(n, UNMASKED_DELTA + 1024 * U)  # a removal with the residual included: over the full model with the residual
    if c.family == "code_leaning_hard":
        return np.full(n, UNMASKED_DELTA + 512 * U)
    if c.family == "soft_erase":
        return np.full(n, UNMASKED + 3000 * U)
    if c.family == "self_union":
        if c.eval_set != "E_lab":
            return np.full(n, OWN_LABELS + SELF[c.eval_set] * U)
        return OWN_LABELS + (np.asarray([SELF[s] for s in src]) + per_document_wobble(docs)) * U  # constant within a document, differing between documents
    if c.family == "partner_union":
        raise AssertionError("planted with its partners")
    assert c.family == "union"
    if c.eval_set == "E":  # curve 1 and its same-size random control, re-run on E
        return np.full(n, OWN_LABELS + (CURVE_1[c.rung] if c.control == "none" else 64) * U)
    pool = str(c.donor_pool)
    by_draw = (DRAW[pool] if c.control == "none" else CONTROL_DRAW[pool])[c.draw] if c.rung != "8" else 0  # the whole pool is one cell: no draws
    rise = np.asarray([(BASE[pool][s] if c.control == "none" else CONTROL_BASE) * F[c.rung] + by_draw for s in src], dtype=np.float64)
    if pool == "D_code" and c.control == "none" and c.rung == "1":  # the sign condition: six of eight per-draw means positive on the code texts, the mean unchanged
        rise = np.where(np.asarray(src) == "code", -6.0 if c.draw < 2 else 26.0, rise)
    return OWN_LABELS + rise * U


def build_root(root: Path, run: str = RUN, other_document_forum: int = OTHER_DOCUMENT) -> a9.Inputs:
    inp = make_inputs()
    src, docs = inp.sources, inp.documents
    blocks = contiguous_blocks(src)
    own = {"E": 3000 + 7 * np.arange(N["E"]), "E_lab": 4000 + 3 * np.arange(N["E_lab"]), "D_unif": 5000 + 11 * np.arange(N["D_unif"])}
    targets = {k: target_side(n, seed) for seed, (k, n) in enumerate(N.items())}
    positions = tier5.example_positions(N["E"], master_seed=0)
    t5 = [c for c in tier_5_cells(run, K) if c.family != "external"]
    ext = {s: [Cell(run, "external", s, None, None, "none", "none", 0, "0", "none", 5, model=m) for m in PYTHIA[s]] for s in ("E", "E_lab")}
    curve1 = [Cell(run, "union", "E", "D_unif", 0.1, "r0", "excluded", k, r, "none", 3 if r in ("2a", "2b") else 1, descriptive=r in ("2a", "2b")) for r in ("1", "2", "2a", "2b", "3", "4") for k in range(K)]
    curve1 += [Cell(run, "union", "E", "D_unif", 0.1, "r0", "excluded", 0, "8", "none", 1)] + [Cell(run, "union", "E", "D_unif", 0.1, "r0", "excluded", k, r, "plain", 2) for r in ("3", "4") for k in range(K)]
    curve1 += [Cell(run, "soft_erase", "E", "D_unif", 0.1, "r1", "excluded", k, "4", "none", 1) for k in range(K)] + [Cell(run, "never_named_hard", "E", "D_unif", 0.1, "ones", "included", 0, "8", "none", 3)]
    leaning = [Cell(run, "code_leaning_hard", "E_lab", "D_code", 0.1, "ones", "included", 0, "G64", "none", 4)]
    stores = {"E_lab__same_domain": [c for c in t5 if c.family == "union"], "E__self_merge": [c for c in t5 if c.eval_set == "E" and c.family != "union"], "E_lab__self_merge": [c for c in t5 if c.eval_set == "E_lab" and c.family != "union"],
              "D_unif__self_merge": [c for c in t5 if c.eval_set == "D_unif"], "E__plain_terms": curve1 + ext["E"], "E_lab__plain_terms": leaning + ext["E_lab"]}
    for name, cells in stores.items():
        eval_set = name.split("__")[0]
        n, target, ids = N[eval_set], targets[eval_set], inp.ids[eval_set]
        cells = cells + _references(run, eval_set, 1, draws=K)
        d = root / "tier5" / name
        (d / "kl").mkdir(parents=True)
        (d / "extras").mkdir()
        frames, partner_frames, listed = [], [], []
        for c in cells:
            m, mc, p, ce = change_pattern(c)
            n_on, sigma = np.zeros(n, dtype=np.int64), np.full(n, np.nan)
            if c.family == "partner_union":
                partner = tier5.partner_assignment(eval_set, str(c.arm), c.shift, n, n_pool=N[str(c.donor_pool)], blocks=blocks if c.arm == "source" else None)
                same = (docs[partner] == docs) if c.arm == "source" else None
                if c.arm == "within":
                    rise = np.full(n, float(STRANGER))
                elif c.arm == "source":
                    rise = np.where(same, SAME_DOCUMENT, np.where(np.asarray(src) == "forum", other_document_forum, OTHER_DOCUMENT)).astype(np.float64)
                else:
                    rise = np.full(n, float(GENERAL))
                kl, n_on = OWN_LABELS + rise * U, own[str(c.donor_pool)][partner]
                sigma = n_on * 0.5
                partner_frames.append(pd.DataFrame({"cell": c.name, "seq": np.arange(n), "arm": c.arm, "shift": c.shift, "partner_pool": c.donor_pool, "partner_row": partner, "partner_n_on": n_on, "own_n_on": own[eval_set],
                                                    "same_document": pd.array(same if same is not None else np.full(n, None, dtype=object), dtype="boolean")}))
            else:
                kl = planted_kl(c, src, docs)
                if c.family == "self_union":
                    n_on, sigma = own[eval_set], own[eval_set] * 0.5
                elif c.family == "union":
                    n_on, sigma = np.full(n, 2 * SIGMA[c.rung]), np.full(n, float(SIGMA[c.rung]))
            changed = changed_positions(target, m, mc)
            top = np.where(changed, (target["top"].astype(np.int64) + 1) % 100, target["top"]).astype(np.uint16)
            conf = target["top_p"] >= 0.5
            frame = pd.DataFrame({"cell": c.name, "seq": np.arange(n), "kl_mean": kl.astype(np.float32), "ce": np.float32(ce), "ce_target": np.float32(2.5), "mask_fp": "00", "precision": "fp32" if c.family == "external" else "bf16",
                                  "n_on": n_on.astype(np.int64), "sigma": sigma.astype(np.float32), "top_changed": changed.mean(axis=1).astype(np.float32),
                                  "top_changed_confident": ((changed & conf).sum(axis=1).astype(np.float32) / conf.sum(axis=1).astype(np.float32)).astype(np.float32), "p_target_top": np.float32(p),
                                  "top_is_next": (top[:, :-1].astype(np.int64) == ids[:, 1:]).mean(axis=1).astype(np.float32)})
            if c.family == "external":
                frame["kl_reverse_mean"], frame["kl_other_mean"], frame["padded_mass_mean"] = np.float32(PYTHIA[eval_set][str(c.model)]["reverse"]), np.float32(PYTHIA[eval_set][str(c.model)]["other"]), np.float32(1e-6)
            frames.append(frame)
            if per_position_listed(c):
                listed.append(c.name)
                stem = c.name.replace("/", "__")
                spread = 2.0 * ((np.arange(T) % 64) + 0.5) / 64.0  # mean one over the positions: the per-position divergence varies and still averages to the text's
                np.save(d / "kl" / f"{stem}.npy", (kl[:, None] * spread[None, :]).astype(np.float16))
                np.save(d / "extras" / f"{stem}__top.npy", top)
                np.save(d / "extras" / f"{stem}__p_target_top.npy", np.full((n, T), p, dtype=np.float16))
                if eval_set == "E":
                    at = np.take_along_axis(top, positions, axis=1).astype(np.int64)
                    np.save(d / "extras" / f"{stem}__top5_ids.npy", ((at[..., None] + np.arange(5)) % 100).astype(np.uint16))
                    np.save(d / "extras" / f"{stem}__top5_p.npy", np.broadcast_to(np.asarray([0.5, 0.2, 0.1, 0.05, 0.01], dtype=np.float32), (n, 2, 5)).copy())
        for k in ("top", "top_p", "tie"):
            np.save(d / "extras" / f"target__{k}.npy", target[k])
        if eval_set == "E":
            at = np.take_along_axis(target["top"], positions, axis=1).astype(np.int64)
            np.save(d / "extras" / "target__top5_ids.npy", ((at[..., None] + np.arange(5)) % 100).astype(np.uint16))
            np.save(d / "extras" / "target__top5_p.npy", np.broadcast_to(np.asarray([0.5, 0.2, 0.1, 0.05, 0.01], dtype=np.float32), (n, 2, 5)).copy())
        table = pd.DataFrame([{**dataclasses.asdict(c), "cell": c.name, "source_sha256": f"sha-{c.name}", "n_on": 0 if c.family not in ("union",) else 2 * SIGMA[c.rung]} for c in cells])
        table.to_parquet(d / "cells.parquet", index=False)
        pd.concat(frames, ignore_index=True).to_parquet(d / "per_sequence.parquet", index=False)
        if partner_frames:
            pd.concat(partner_frames, ignore_index=True).to_parquet(d / "partners.parquet", index=False)
        with open(d / "run_manifest.json", "w") as f:
            json.dump({"run": run, "n_sequences": n, "n_draws": K, "set_hash": f"hash-{eval_set}", "finished_at": "now", "master_seed": 0, "commits": {"project": "0" * 40, "dirty": "0"}, "gpu_name": None, "precision": "bf16",
                       "extra": {"tier5": {"per_position_listed_cells": listed, "extra_columns": True, "example_positions": [n, 2] if eval_set == "E" else None}}}, f)
        with open(d / "marker.json", "w") as f:
            json.dump({"done_through": 0, "subbatch": n, "n_sequences": n, "cells": [c.name for c in cells]}, f)
    return inp


def build_committed(root: Path, t5_root: Path) -> None:
    """The committed stores, the canary's other side: every reference on E and E_lab and every re-run cell, with the same values."""
    for name, eval_set in (("E__plain_terms", "E"), ("E_lab__plain_terms", "E_lab")):
        cells, rows = pd.read_parquet(t5_root / "tier5" / name / "cells.parquet"), pd.read_parquet(t5_root / "tier5" / name / "per_sequence.parquet")
        keep = cells[cells["tier"] != 5]["cell"]
        d = root / "tier1" / eval_set
        d.mkdir(parents=True)
        cells[cells["cell"].isin(keep)][["cell", "source_sha256", "n_on"]].to_parquet(d / "cells.parquet", index=False)
        rows[rows["cell"].isin(keep)][["cell", "seq", "kl_mean"]].to_parquet(d / "per_sequence.parquet", index=False)


@pytest.fixture(scope="module")
def planted(tmp_path_factory):
    root, committed, out = tmp_path_factory.mktemp("s9_root"), tmp_path_factory.mktemp("s9_committed"), tmp_path_factory.mktemp("s9_out")
    inp = build_root(root)
    build_committed(committed, root)
    summary = a9.analyze_s9(root, out, spec=SPEC, committed_roots=(committed,), require_canary=True, replicates=REPLICATES, inputs=inp, log=lambda *_: None)
    return {"root": root, "committed": committed, "out": out, "inputs": inp, "summary": summary}


def table(planted, name: str) -> pd.DataFrame:
    return pd.read_csv(planted["out"] / f"{name}.csv", dtype={"size": str})


def offsets(pool: str, pattern: tuple[int, ...] | None = None, table_of: str | None = None) -> np.ndarray:
    """(R,) per replicate, the mean planted draw offset of a pool under the resampled draws of its own table (or, to show that a crossed table would be seen, of `table_of`'s). A planted rise is
    constant over the texts of a source and the sources keep fixed weights, so the documents move nothing: a two-level replicate of an arm's mean rise is (base * F + offsets) / 4096, exactly."""
    counts = s9.draw_counts(K, REPLICATES, (0, "boot_draws", table_of or pool))
    return counts @ np.asarray(pattern if pattern is not None else DRAW[pool], dtype=np.float64) / K


def one(df: pd.DataFrame, **where) -> pd.Series:
    for k, v in where.items():
        df = df[df[k] == v]
    assert len(df) == 1, (where, len(df))
    return df.iloc[0]


# ----------------------------------------------------------------------------- run 2


def test_the_gate_the_verdict_and_the_curves(planted):
    v = one(table(planted, "s9_run2_verdict"))
    assert bool(v.gate_arm_U_fails_on_the_code_texts) and v.U_label == s9.FAILS and v.U_first_material == 2 and v.C_label == s9.IMMATERIAL and v.outcome == s9.D_BELOW and v.n_documents == 12 and v.outcome_rows_beside_not_read == s9.D_BELOW
    assert v.C_first_detected == 2 and pd.isna(v.C_first_material)  # arm C: not detected at one token (the sign condition), detected from eight tokens on, material nowhere
    curves = table(planted, "s9_run2_curves")
    assert len(curves) == 3 * 8 * 10 and set(curves[curves.role == "verdict"].arm) == {"C", "U"} and set(curves[curves.role == "verdict"].stratum) == {"G"} and (curves.m == 10).all()  # three arms, eight strata and sources, ten sizes
    c3 = one(curves, arm="C", stratum="G", size="3")
    assert c3.rise == pytest.approx(18 * 7 * U, abs=1e-12) and c3.interval_documents_lo == pytest.approx(c3.rise) and c3.interval_documents_hi == pytest.approx(c3.rise) and bool(c3.detected) and not bool(c3.material)
    assert c3.n_on_mean == 1400 and c3.sigma_mean == 700 and c3.size_words == "64 tokens" and c3.n_texts == 24 and c3.n_documents == 12 and c3.n_draws == 8
    c1 = one(curves, arm="C", stratum="G", size="1")  # the sign condition reaches the glue: the mean is positive, six of eight per-draw means are, and the size is not detected
    assert c1.rise == pytest.approx(18 * U, abs=1e-12) and c1.n_draws_positive == 6 and not bool(c1.sign_condition) and not bool(c1.detected) and c1.interval_two_level_hi > c1.interval_two_level_lo
    u2, u1 = one(curves, arm="U", stratum="G", size="2"), one(curves, arm="U", stratum="G", size="1")
    assert bool(u2.material) and u2.rise == pytest.approx(240 * U) and bool(u1.detected) and not bool(u1.material)
    # a stratum is its own texts: the prose texts (row-weighted over two sources that differ), each source by itself, the pooled other texts, and a source of three documents, which has a point value and no interval of any kind
    assert one(curves, arm="P", stratum="P", size="7").rise == pytest.approx(6 * 10 * U) and one(curves, arm="P", stratum="P", size="7").n_texts == 40
    for arm, pool in (("C", "D_code"), ("U", "D_unif"), ("P", "D_prose")):
        for s, n, _ in SOURCES:
            row = one(curves, arm=arm, stratum=f"source:{s}", size="3")
            assert row.rise == pytest.approx(BASE[pool][s] * 7 * U, abs=1e-12) and row.n_texts == n  # every source has its own planted rise in every arm: a stratum built from another source shows
    o = one(curves, arm="C", stratum="O", size="3")
    assert o.rise == pytest.approx(base_mean("D_code", OTHER) * 7 * U) and o.rise != pytest.approx(np.mean([BASE["D_code"][s] for s in OTHER]) * 7 * U) and o.n_documents == 33 and "papers contributes 3 documents" in o.flag  # weighted by rows, not by sources
    thin = one(curves, arm="P", stratum="source:papers", size="3")
    assert thin.rise == pytest.approx(10 * 7 * U) and thin.n_documents == 3 and np.isnan(thin.interval_documents_lo) and np.isnan(thin.interval_rows_beside_lo) and np.isnan(thin.interval_two_level_lo) and pd.isna(thin.detected)
    assert one(curves, arm="U", stratum="G", size="8").n_draws == 1  # the whole pool, once


def test_the_two_level_intervals_use_each_pools_own_draw_table(planted):
    # the planted draws differ, by a pattern of each arm's own, and an interval that resamples draws is held exactly to a direct computation with the pool's own table
    curves = table(planted, "s9_run2_curves")
    for arm, pool, stratum, sources, size in (("P", "D_prose", "P", PROSE, "7"), ("C", "D_code", "G", ("code",), "3"), ("U", "D_unif", "O", OTHER, "4"), ("C", "D_code", "source:forum", ("forum",), "2")):
        row = one(curves, arm=arm, stratum=stratum, size=size)
        want = s9.interval((base_mean(pool, sources) * F[size] + offsets(pool)) * U, 10)
        assert [row.interval_two_level_lo, row.interval_two_level_hi] == pytest.approx(want, abs=1e-12) and want[1] - want[0] > 1e-4
        for other in set(DRAW) - {pool}:  # another pool's table gives other replicates, so a crossed table fails the comparison
            crossed = s9.interval((base_mean(pool, sources) * F[size] + offsets(pool, table_of=other)) * U, 10)
            assert [row.interval_two_level_lo, row.interval_two_level_hi] != pytest.approx(crossed, abs=1e-9)
        reversed_draws = s9.interval((base_mean(pool, sources) * F[size] + offsets(pool, DRAW[pool][::-1])) * U, 10)
        assert [row.interval_two_level_lo, row.interval_two_level_hi] != pytest.approx(reversed_draws, abs=1e-9)  # and so do draws taken in another order
        assert row.interval_documents_hi - row.interval_documents_lo < 1e-12  # the interval of the same registered rule as `stats.union_curve` holds the draws fixed: no width here, so the two-level width above is the draws'
    whole_pool = one(curves, arm="U", stratum="G", size="8")
    assert whole_pool.interval_two_level_hi - whole_pool.interval_two_level_lo < 1e-12  # one cell: no draw to resample


def test_a_pooled_stratum_keeps_the_design_mix_and_prints_the_value_without_its_thin_source(planted):
    # each source keeps its fixed row share in every replicate, through the glue. On the other texts arm C's rise is a different constant on each of the four sources, and the documents are of unequal size:
    # per source with fixed row shares the replicates cannot move; with the resampled rows pooled across sources they do (the row-level interval beside shows that the values differ)
    curves = table(planted, "s9_run2_curves")
    o = one(curves, arm="C", stratum="O", size="3")
    assert o.interval_documents_hi - o.interval_documents_lo < 1e-12 and o.interval_documents_lo == pytest.approx(o.rise, abs=1e-12) and o.interval_rows_beside_hi - o.interval_rows_beside_lo > 1e-4
    assert "papers contributes 3 documents; the value without it is beside" in o.flag
    assert o.rise_without_flagged_sources == pytest.approx(base_mean("D_code", OTHER_NO_PAPERS) * 7 * U) and o.rise_without_flagged_sources_interval_lo == pytest.approx(o.rise_without_flagged_sources, abs=1e-12)
    assert o.rise_without_flagged_sources != pytest.approx(o.rise, abs=1e-6)
    assert np.isnan(one(curves, arm="C", stratum="G", size="3").rise_without_flagged_sources) and np.isnan(one(curves, arm="C", stratum="P", size="3").rise_without_flagged_sources)  # not flagged: nothing beside
    inp = planted["inputs"]
    src, docs = np.asarray(inp.sources), inp.documents
    rule = one(table(planted, "s9_run6_self_merge_rule"), set="E_lab")
    keep = src != "papers"
    want = ((np.asarray([SELF[s] for s in src]) + per_document_wobble(docs)) * U)[keep]
    assert rule.rise_without_flagged_sources == pytest.approx(want.mean()) and bool(rule.material_without_flagged_sources) and rule.rise_without_flagged_sources_interval_lo < want.mean() < rule.rise_without_flagged_sources_interval_hi
    # the whole set's interval is the per-source replicates combined with the row shares, exactly
    t5 = a9.load_tier5(planted["root"], frozen=None, committed_roots=None, require_canary=False, log=lambda *_: None)
    strata, _ = a9.build_strata(inp, SPEC, t5, REPLICATES, 0)
    s_all = (np.asarray([SELF[s] for s in src]) + per_document_wobble(docs)) * U
    direct = sum((src == s).sum() / 93 * s9.ratio_means(strata[f"source:{s}"].primary, s_all[src == s]) for s, _, _ in SOURCES)
    assert [rule.interval_lo, rule.interval_hi] == pytest.approx(s9.interval(direct, 3), abs=1e-12)
    lad = table(planted, "s9_run6_ladder")
    assert one(lad, stratum="O", rung="a general partner").mean_rise_without_flagged_sources == pytest.approx(GENERAL * U) and np.isnan(one(lad, stratum="source:forum", rung="a general partner").mean_rise_without_flagged_sources)
    lam = one(table(planted, "s9_run2_lambda"))
    want_lam = np.log(18 / 60) - np.log(base_mean("D_code", OTHER_NO_PAPERS) / base_mean("D_unif", OTHER_NO_PAPERS))
    assert lam.lambda_without_flagged_sources == pytest.approx(want_lam) and lam.interval_without_flagged_sources_lo < want_lam < lam.interval_without_flagged_sources_hi
    pt = one(table(planted, "s9_plain_terms_listed_masks"), set="E_lab", in_words="own labels")
    conf = np.where(np.arange(93) % 2 == 0, 256, 16)[keep]
    assert pt.change_rate_without_flagged_sources == pytest.approx((100 - 2 + 8) / 510) and pt.change_rate_confident_without_flagged_sources == pytest.approx(8 * keep.sum() / conf.sum()) and pt.change_rate_confident != pytest.approx(pt.change_rate_confident_without_flagged_sources)
    assert np.isnan(one(table(planted, "s9_plain_terms_listed_masks"), set="E", in_words="own labels").change_rate_without_flagged_sources)


def test_the_match_ratio_is_the_worked_example_at_every_size(planted):
    r = table(planted, "s9_run2_match_ratio")
    assert list(r["size"]) == ["1", "2", "2a", "2b", "3", "4", "5", "6", "7", "8"] and np.allclose(r.r_code, 0.75) and np.allclose(r.r_prose, 1 / 3) and np.allclose(r.R, 0.5)
    read = r[r.size_is_read]
    assert list(read["size"]) == ["2", "3", "7"] and (read.reading == s9.MATCHING_HELPS).all() and (read.nonfinite_share == 0).all() and read.all_four_rises_above_zero.all()
    assert (r[~r.size_is_read].reading == s9.NOT_READ).all() and bool(one(r, size="4").printed_not_read) and np.isfinite(one(r, size="4").R_interval_lo)  # one whole text: printed with its interval, not read
    # the interval, exactly: arm C's draws on the code texts and on the prose texts are one resample of one table, arm P's likewise with its own; the two prose sources differ and keep their fixed weights,
    # so the documents move nothing, and log R = (log C_G - log P_G + log P_P - log C_P) / 2 is known in every replicate from the two tables alone
    aC, aP = offsets("D_code"), offsets("D_prose")
    for size in ("2", "3", "4", "7"):
        f, row = F[size], one(r, size=size)
        log_r = 0.5 * (np.log(18 * f + aC) - np.log(24 * f + aP) + np.log(6 * f + aP) - np.log(18 * f + aC))
        assert [row.R_interval_lo, row.R_interval_hi] == pytest.approx(np.exp(s9.interval(log_r, 3)), abs=1e-12) and row.R_interval_lo < 0.5 < row.R_interval_hi
        wrong = 0.5 * (np.log(6 * f + offsets("D_prose", table_of="D_code")) - np.log(24 * f + offsets("D_prose", table_of="D_code")))  # arm P resampled with arm C's table
        assert [row.R_interval_lo, row.R_interval_hi] != pytest.approx(np.exp(s9.interval(wrong, 3)), abs=1e-9)
        unshared = 0.5 * (np.log(18 * f + aC) - np.log(24 * f + aP) + np.log(6 * f + aP) - np.log(18 * f + offsets("D_code", table_of="D_unif")))  # a pool's draws not shared between the two strata
        assert [row.R_interval_lo, row.R_interval_hi] != pytest.approx(np.exp(s9.interval(unshared, 3)), abs=1e-9)
        assert [row.rise_P_on_prose_lo, row.rise_P_on_prose_hi] == pytest.approx(s9.interval((6 * f + aP) * U, 3), abs=1e-12) and [row.rise_C_on_prose_lo, row.rise_C_on_prose_hi] == pytest.approx(s9.interval((18 * f + aC) * U, 3), abs=1e-12)
    tok1 = one(r, size="1")  # at one token arm C's planted draws on the code texts are the sign-condition case (-6, -6, 26, ...): R is still 0.5 and its interval is wider
    assert tok1.R == pytest.approx(0.5) and tok1.R_interval_hi - tok1.R_interval_lo > one(r, size="2").R_interval_hi - one(r, size="2").R_interval_lo


def test_the_descriptions_each_control_with_its_own_arm(planted):
    aC, aU = offsets("D_code"), offsets("D_unif")
    d = one(table(planted, "s9_run2_contrast_C_minus_U"), size="3")
    assert d.difference == pytest.approx((18 - 60) * 7 * U) and d.ratio == pytest.approx(0.3) and d.ratio_nonfinite_share == 0 and d.n_draws_C_above_U_by_index == 0 and d.sigma_C == 700
    # two pools on the same texts, each pool's draws resampled with its own table: exactly
    assert [d.difference_interval_lo, d.difference_interval_hi] == pytest.approx(s9.interval(((126 + aC) - (420 + aU)) * U, 1), abs=1e-12)
    assert [d.ratio_interval_lo, d.ratio_interval_hi] == pytest.approx(np.exp(s9.interval(np.log(126 + aC) - np.log(420 + aU), 1)), abs=1e-12)
    assert [d.difference_interval_lo, d.difference_interval_hi] != pytest.approx(s9.interval(((126 + aC) - (420 + offsets("D_unif", table_of="D_code"))) * U, 1), abs=1e-9)  # paired by index through one table: seen
    h = table(planted, "s9_run2_per_unit")
    assert one(h, quantity="h_C", stratum="G", size="3").value == pytest.approx(18 * 7 * U / 700) and one(h, quantity="h_C / h_U", stratum="G", size="3").value == pytest.approx(0.3)
    hp, hr = one(h, quantity="h_P", stratum="P", size="7"), one(h, quantity="h_C / h_U", stratum="P", size="7")
    assert hp.value == pytest.approx(6 * 10 * U / 1000) and [hp.interval_lo, hp.interval_hi] == pytest.approx(s9.interval((60 + offsets("D_prose")) * U / 1000, 1), abs=1e-15)
    assert hr.value == pytest.approx(18 / 40) and [hr.interval_lo, hr.interval_hi] == pytest.approx(np.exp(s9.interval(np.log(180 + aC) - np.log(400 + aU), 1)), abs=1e-12)
    ctl = table(planted, "s9_run2_controls")
    assert set(ctl.arm) == {"C", "U"} and sorted(set(ctl["size"])) == sorted(["1", "2", "2a", "2b", "3", "4"]) and len(ctl) == 2 * 6 * 3  # arm P has no control; nothing holds two controls
    c = one(ctl, arm="C", stratum="G", size="3")
    assert c.real == pytest.approx(18 * 7 * U) and c.random == pytest.approx(2 * 7 * U) and c.difference == pytest.approx(16 * 7 * U) and c.n_draws_real_above_random == 8
    # a control is paired with its own arm draw by draw and resampled with its arm's table: exactly; a control paired with another draw of its arm, or resampled with the other arm's table, is seen
    pair = np.asarray(DRAW["D_code"]) - np.asarray(CONTROL_DRAW["D_code"])
    assert [c.difference_interval_lo, c.difference_interval_hi] == pytest.approx(s9.interval((16 * 7 + offsets("D_code", tuple(pair))) * U, 1), abs=1e-12)
    shifted = np.asarray(DRAW["D_code"]) - np.roll(np.asarray(CONTROL_DRAW["D_code"]), 1)
    assert [c.difference_interval_lo, c.difference_interval_hi] != pytest.approx(s9.interval((16 * 7 + offsets("D_code", tuple(shifted))) * U, 1), abs=1e-9)
    assert [c.difference_interval_lo, c.difference_interval_hi] != pytest.approx(s9.interval((16 * 7 + offsets("D_code", tuple(pair), table_of="D_unif")) * U, 1), abs=1e-9)
    cu = one(ctl, arm="U", stratum="P", size="4")
    pair_u = np.asarray(DRAW["D_unif"]) - np.asarray(CONTROL_DRAW["D_unif"])
    assert cu.difference == pytest.approx((40 - 2) * 8 * U) and [cu.difference_interval_lo, cu.difference_interval_hi] == pytest.approx(s9.interval(((40 - 2) * 8 + offsets("D_unif", tuple(pair_u))) * U, 1), abs=1e-12)
    lam = one(table(planted, "s9_run2_lambda"))
    c_o, u_o = base_mean("D_code", OTHER) * 7, base_mean("D_unif", OTHER) * 7
    assert lam["lambda"] == pytest.approx(np.log(18 / 60) - np.log(c_o / u_o)) and lam.nonfinite_share == 0 and "papers" in lam.flag
    assert [lam.interval_lo, lam.interval_hi] == pytest.approx(s9.interval((np.log(126 + aC) - np.log(420 + aU)) - (np.log(c_o + aC) - np.log(u_o + aU)), 1), abs=1e-12)  # each pool's draws shared between the two strata


def test_the_count_only_prediction_sits_on_arm_Us_knots(planted):
    co = table(planted, "s9_run2_count_only")
    assert len(co) == 20 and set(co.amount_measured_as) == {"switched mass (primary)", "count of named pieces (beside)"}
    for amount in set(co.amount_measured_as):
        for size in ("3", "7"):
            row = one(co, amount_measured_as=amount, size=size)  # every draw of arm C has arm U's amount at the same size, so its prediction is arm U's rise there
            assert row.n_draws_predicted == 8 and row.prediction == pytest.approx(60 * F[size] * U) and row.observed == pytest.approx(18 * F[size] * U) and row.log_ratio == pytest.approx(np.log(0.3))
            assert row.interval_hi < 0 and bool(row.readable) and row.reading == s9.BELOW and row.m == 2 and not bool(row.U_violators_pooled)
            # exactly: arm U's curve is rebuilt from all of its draws (their offsets sum to zero, so its knots do not move) and arm C's draws are resampled with arm C's table
            assert [row.interval_lo, row.interval_hi] == pytest.approx(s9.interval(np.log((18 * F[size] + offsets("D_code")) / (60 * F[size])), 2), abs=1e-9)
            assert [row.interval_lo, row.interval_hi] != pytest.approx(s9.interval(np.log((18 * F[size] + offsets("D_code", table_of="D_unif")) / (60 * F[size])), 2), abs=1e-6)
            assert row.end_segment_continued_share == 0.0  # the planted amounts do not vary over texts, so a replicate's knots are the full data's
        assert one(co, amount_measured_as=amount, size="2").reading == s9.NOT_READ and np.isnan(one(co, amount_measured_as=amount, size="2").interval_lo)  # tabulated, not one of the two read sizes
        assert np.isnan(one(co, amount_measured_as=amount, size="2").end_segment_continued_share)
    pts = table(planted, "s9_run2_count_only_U_points")
    assert len(pts) == 20 and one(pts, amount_measured_as="switched mass (primary)", size="3").amount == 700 and one(pts, amount_measured_as="count of named pieces (beside)", size="3").amount == 1400
    assert np.allclose(sorted(pts[pts.amount_measured_as == "count of named pieces (beside)"]["rise"]), sorted(60 * f * U for f in F.values())) and pts.used.all()  # arm U on the code texts, not on all of E_lab


# ----------------------------------------------------------------------------- run 6


def test_the_self_merge_rule_on_three_sets_and_the_document_interval(planted):
    rule = table(planted, "s9_run6_self_merge_rule")
    e, lab, d = one(rule, set="E"), one(rule, set="E_lab"), one(rule, set="D_unif")
    assert e.rise == pytest.approx(256 * U) and bool(e.material) and e.m == 3 and e.share_made_worse == 1.0 and e["share_above_0.05"] == 1.0 and e["share_above_0.1"] == 0.0 and e.rise_over_rounded_labels == pytest.approx(OWN_LABELS - ROUNDED + 256 * U)
    assert d.rise == 0 and not bool(d.material) and d.share_made_worse == 0.0 and planted["summary"]["run6"]["summary_may_carry_the_self_merge"] is True
    src, docs = np.asarray(planted["inputs"].sources), planted["inputs"].documents
    want = (np.asarray([SELF[s] for s in src]) + per_document_wobble(docs)) * U
    assert lab.rise == pytest.approx(want.mean()) and lab.n_texts == 93 and lab.n_documents == 45 and "papers contributes 3 documents" in lab.flag and bool(lab.material)
    # the rows of a document are identical and documents differ: the document interval is wider than the row interval beside it
    assert (lab.interval_hi - lab.interval_lo) > 1.2 * (lab.interval_rows_beside_hi - lab.interval_rows_beside_lo) > 0
    assert e.n_on_mean == pytest.approx((3000 + 7 * np.arange(40)).mean()) and lab.own_labels_kl == pytest.approx(OWN_LABELS)


def test_self_against_stranger_and_its_printed_consistency_check(planted):
    s = one(table(planted, "s9_run6_self_against_stranger"))
    assert s.self == pytest.approx(256 * U) and s.stranger == pytest.approx(0.5) and s.difference == pytest.approx(256 * U - 0.5) and s.reading == s9.SELF_LESS and s.share_of_texts_self_worse == 0.0
    assert s.consistency_curve_1_one_text_in_these_stores == pytest.approx(CURVE_1["4"] * U) and s.consistency_committed_value_on_the_papers_run == 0.49 and s.consistency_x_hat == pytest.approx(0.5)
    own = 3000 + 7 * np.arange(40)
    assert s.per_unit_self == pytest.approx(256 * U / (own * 0.5).mean()) and s.per_unit_stranger == pytest.approx(0.5 / (own * 0.5).mean())  # the rotation: a stranger's set has the self arm's mean count exactly


def test_the_ladder_and_the_scope_rule(planted, tmp_path):
    lad = table(planted, "s9_run6_ladder")
    inp = planted["inputs"]
    src, docs = np.asarray(inp.sources), inp.documents
    blocks = contiguous_blocks(inp.sources)
    same = np.stack([docs[tier5.partner_assignment("E_lab", "source", r, 93, n_pool=93, blocks=blocks)] == docs for r in (1, 2, 3, 4)])
    for s, n, per in SOURCES:
        m = src == s
        it, sd, od, gen = (one(lad, stratum=f"source:{s}", rung=r) for r in ("the text itself", "a partner from the same document", "a partner from the same source, another document", "a general partner"))
        assert it.n_texts == n and it.mean_rise == pytest.approx(((SELF[s] + per_document_wobble(docs[m])) * U).mean()) and it.mean_count == pytest.approx((4000 + 3 * np.arange(93))[m].mean())
        assert sd.n_text_shift_pairs == int(same[:, m].sum()) and sd.n_texts == int(same[:, m].any(axis=0).sum()) and od.n_text_shift_pairs == 4 * n - sd.n_text_shift_pairs and gen.n_text_shift_pairs == 4 * n
        assert od.mean_rise == pytest.approx(OTHER_DOCUMENT * U) and gen.mean_rise == pytest.approx(GENERAL * U) and (sd.n_texts == 0 or sd.mean_rise == pytest.approx(SAME_DOCUMENT * U)) and od.m == 5
        assert od.standing == (s9.MATERIAL if s != "papers" else None) or (s == "papers" and pd.isna(od.standing))  # three documents: no interval, no standing
    # a rung with an undefined replicate keeps its printed interval, flagged, and has no standing; here that is every same-document rung (few texts, in few documents)
    flagged = lad[lad.nonfinite_share > 0]
    assert len(flagged) >= 3 and (flagged.rung == "a partner from the same document").all() and flagged.standing.isna().all() and (flagged.interval_flag == s9.NONFINITE_FLAG).all()
    assert np.isfinite(flagged.interval_lo).all() and (flagged.interval_hi < 0.05).all()  # planted at 100 / 4096 = 0.024: each would have read "wholly under 0.05"
    assert lad[lad.nonfinite_share == 0].interval_flag.isna().all()
    pooled = one(lad, stratum="O", rung="a general partner")
    assert pooled.n_texts == 69 and "papers contributes 3 documents" in pooled.flag and pooled.standing == s9.MATERIAL
    scope = planted["summary"]["run6"]["scope"]
    assert scope["within_one_kind_of_text"] is True and scope["standing"] == s9.MATERIAL and scope["sources_without_standing"] == ["papers"] and scope["needed"] == 4  # ArXiv's analogue is unreadable: all four readable sources are needed, and agree
    # one readable source with the other standing, and the post names the sources
    root = tmp_path / "root"
    inp2 = build_root(root, other_document_forum=SAME_DOCUMENT)
    out = a9.analyze_s9(root, tmp_path / "out", spec=SPEC, committed_roots=None, require_canary=False, replicates=100, inputs=inp2, log=lambda *_: None)
    sc = out["run6"]["scope"]
    assert sc["within_one_kind_of_text"] is False and sc["standing"] is None and sc["sources_by_standing"][s9.UNDER] == ["forum"] and sorted(sc["sources_by_standing"][s9.MATERIAL]) == ["code", "prose_a", "prose_b"]


def test_rule_3_is_asserted_on_the_tables(planted, tmp_path):
    rec = planted["summary"]["run6"]["asserts"]
    assert set(rec) == {"E/within", "E_lab/source", "E_lab/general"} and rec["E_lab/source"]["balanced_per_source"] and rec["E_lab/source"]["same_document_is_the_index"] and rec["E/within"]["self_mean_count_equals_each_shift"]
    for column, change, message in (("partner_n_on", lambda v: v + 1, "partner_n_on"), ("same_document", lambda v: ~v, "same_document"), ("partner_row", lambda v: (v + 1) % 93, "received count")):
        root = tmp_path / f"tampered_{column}"
        shutil.copytree(planted["root"], root)
        p = root / "tier5" / "E_lab__self_merge" / "partners.parquet"
        t = pd.read_parquet(p)
        sel = t["arm"] == "source"
        t.loc[sel, column] = change(t.loc[sel, column])
        t.to_parquet(p, index=False)
        with pytest.raises(AssertionError, match=message):
            a9.analyze_s9(root, tmp_path / f"out_{column}", spec=SPEC, committed_roots=None, require_canary=False, replicates=50, inputs=planted["inputs"], log=lambda *_: None)


# ----------------------------------------------------------------------------- runs 3 and 7


def test_the_plain_terms_table_excludes_ties_and_pools_a_masks_draws(planted):
    t = table(planted, "s9_plain_terms_listed_masks")
    own = one(t, set="E", in_words="own labels")
    assert own.change_rate == pytest.approx((100 - 2 + 8) / 510) and own.tied_share_excluded == pytest.approx(2 / 512) and pd.isna(own.change_rate_baseline) and own.n_draws == 1  # the two tied positions leave numerator and denominator
    assert own.change_rate_confident == pytest.approx(8 * 40 / (20 * 256 + 20 * 16)) and own.change_rate_confident != pytest.approx((8 / 256 + 8 / 16) / 2)  # a ratio of sums over texts, not a mean of per-text rates
    merge = one(t, set="E", in_words="merge of general donors, 1 text")  # eight draws, m = 160 + k, mc = 14
    assert merge.n_draws == 8 and merge.change_rate == pytest.approx((160 + 3.5 - 2 + 14) / 510) and merge.change_rate_baseline == pytest.approx(own.change_rate) and merge.change_rate_rise == pytest.approx(merge.change_rate - own.change_rate)
    assert merge.change_rate_rise_interval_lo == pytest.approx(merge.change_rate_rise) and merge.change_rate_confident == pytest.approx(14 * 40 / 5440) and merge.p_target_top == 0.25 and merge.p_target_top_baseline == 0.5 and merge.p_target_top_target == 0.625
    assert merge.ce == 3.5 and merge.ce_rise == 0.5 and merge.ce_target == 2.5 and merge.baseline.endswith("/ref/importances")
    removal = one(t, set="E", in_words="removal of the never-named pieces (the whole set)")
    # a removal's baseline is the full model, and which full model: the one with the residual for a removal that includes it, which is planted apart from the target and from the full model without it
    assert removal.baseline.endswith("/ref/unmasked_delta") and removal.change_rate == pytest.approx((150 - 2 + 10) / 510) and removal.change_rate_baseline == pytest.approx((6 - 2 + 1) / 510)
    assert removal.ce_baseline == 2.53125 and removal.p_target_top_baseline == 0.5625 and removal.ce_rise == pytest.approx(3.25 - 2.53125) and removal.change_rate_confident_baseline == pytest.approx(1 * 40 / 5440)
    erase = one(t, set="E", in_words="soft erase of what general donors name, 1 text")  # the residual excluded: over the full model without it
    assert erase.baseline.endswith("/ref/unmasked") and erase.change_rate_baseline == pytest.approx((4 - 2) / 510) and erase.ce_baseline == 2.5625 and erase.p_target_top_baseline == 0.5 and erase.change_rate_confident_baseline == 0
    edit = one(t, set="E_lab", in_words="code-leaning edit, 64 members")
    assert edit.baseline.endswith("/ref/unmasked_delta") and edit.ce_baseline == 2.53125 and edit.change_rate_baseline == pytest.approx(5 / 510)
    with_residual = one(t, set="E", in_words="the full decomposed model with the residual")
    assert with_residual.change_rate == pytest.approx(5 / 510) and with_residual.ce == 2.53125 and with_residual.ce_target == 2.5 and pd.isna(with_residual.change_rate_baseline)
    lab = one(t, set="E_lab", in_words="merge of code donors, 64 tokens")
    assert lab.n_documents == 45 and "papers" in lab.flag and np.isfinite(lab.change_rate_interval_rows_beside_lo) and lab.change_rate_baseline == pytest.approx((100 - 2 + 8) / 510)
    assert len(t[t.in_words == "own labels"]) == 2 and len(t[t.in_words.str.startswith("comparison model")]) == 4  # a reference that every store of a set carries is printed once
    # the cells that keep no arrays: the confident-position rate only, its numerator recovered as rate times count
    other = table(planted, "s9_plain_terms_other_cells")
    assert "change_rate" not in other.columns and len(other) + len(t) == len(set(other["mask"]) | set(t["mask"]))
    row = one(other, set="E_lab", in_words="merge of prose donors, 64 tokens")  # m = 150 + k, mc = 13
    n_conf = np.where(np.arange(93) % 2 == 0, 256, 16).sum()
    assert row.n_draws == 8 and row.change_rate_confident == pytest.approx(13 * 93 / n_conf) and row.change_rate_confident_baseline == pytest.approx(8 * 93 / n_conf) and row.ties_among_confident_positions_not_excluded == 0
    assert planted["summary"]["plain_terms"]["gates"]["E__plain_terms"]["n_listed_cells_gated"] == 6 * 8 + 1 + 2 * 8 + 8 + 1 + 2 + 3


def test_the_bin_table_pools_the_listed_masks_on_E_and_no_comparison_model(planted):
    bins = table(planted, "s9_plain_terms_bins")
    n_cells = (6 * 8 + 1 + 2 * 8 + 8 + 1) + 3 + 1  # the re-runs, the three listed references, the self-merge; not the two comparison models
    assert planted["summary"]["plain_terms"]["n_listed_masks"] and bins.n_positions.sum() == n_cells * 40 * (512 - 2) and list(bins["from"])[1:] == [0.05, 0.2, 0.5, 1.0, 2.0]
    assert bins.iloc[0].n_positions >= 2 * 40 * 510 and 0 <= bins.iloc[0].change_rate < bins.iloc[3].change_rate  # the full model's two references change least and diverge least


def test_the_examples_are_chosen_by_rule_from_eligible_positions(planted):
    ex = table(planted, "s9_examples")
    inp = planted["inputs"]
    assert planted["summary"]["examples"]["n_eligible"] == 78 and planted["summary"]["examples"]["n_positions"] == 80 and (ex.seq != 0).all()  # text 0 decodes to replacement characters
    assert sorted(set(ex[ex.example_of == "merge"].percentile)) == [10.0, 50.0, 90.0, 99.0] and list(ex[ex.example_of == "never_named"].percentile.unique()) == [50.0] and len(ex) == 5 * 5 and ex.shown.sum() == 5
    assert (ex[ex.example_of == "merge"]["mask"] == f"{RUN}/E/union/D_unif/tau0.1/r0/excl/k0/r4").all()
    positions = tier5.example_positions(40)
    kl = np.load(planted["root"] / "tier5" / "E__plain_terms" / "kl" / f"{RUN}__E__union__D_unif__tau0.1__r0__excl__k0__r4.npy").astype(np.float64)
    top = np.load(planted["root"] / "tier5" / "E__plain_terms" / "extras" / f"{RUN}__E__union__D_unif__tau0.1__r0__excl__k0__r3__top.npy")
    for _, row in ex[ex.example_of == "merge"].iterrows():
        b, t = int(row.seq), int(row.position)
        assert t in positions[b] and row.kl_at_position == pytest.approx(kl[b, t]) and row.percentile_value == pytest.approx(np.percentile(kl, row.percentile))
        assert row.context == inp.decode(inp.ids["E"][b, t - 47 : t + 1]) and len(row.context.split(" ")) == 48 and row.real_next_token == inp.decode([inp.ids["E"][b, t + 1]])
        assert row["top5: the merge of general donors, 64 tokens"].startswith(f"'w{int(top[b, t])}' 0.500") or int(top[b, t]) == 0  # the top five are the right cell's, at the right position
    shown = ex[(ex.example_of == "merge") & ex.shown]
    eligible_at = np.asarray([[kl[b, t] for t in positions[b]] for b in range(1, 40)]).reshape(-1)
    for _, row in shown.iterrows():
        assert abs(row.kl_at_position - row.percentile_value) == pytest.approx(np.min(np.abs(eligible_at - row.percentile_value)))  # the nearest eligible stored position
    assert "top5: the full decomposed model with the residual" in ex.columns and ex[ex.example_of == "never_named"]["top5: own labels"].isna().all()


def test_the_yardstick_and_the_ratios_the_post_will_quote(planted):
    y = table(planted, "s9_yardstick")
    assert len(y) == 4 and set(y.model) == set(PYTHIA["E"]) and set(y.set) == {"E", "E_lab"}
    row = one(y, model="pythia-70m", set="E")
    assert row.kl_target_to_model == 2.0 and row.kl_model_to_target == 2.5 and row.kl_this_model_from_the_other == 0.5 and row.ce_model == 3.25 and row.ce_target == 2.5
    rate = (200 - 2 + (20 * 100 + 20 * 16) / 40) / 510  # 100 changed confident positions where a text has 256, all 16 where it has 16
    assert row.top_token_agreement == pytest.approx(1 - rate) and row.top_token_agreement_own_labels == pytest.approx(1 - 106 / 510) and row.p_target_top == 0.25 and row.p_target_top_own_labels == 0.5
    assert np.isfinite(one(y, model="pythia-160m", set="E_lab").kl_target_to_model_interval_rows_beside_lo) and "papers" in one(y, model="pythia-160m", set="E_lab").flag
    for eval_set, models in PYTHIA.items():  # the comparison models' values differ between the two sets and between the two models: each row is its own store's and its own model's
        for model, v in models.items():
            got = one(y, model=model, set=eval_set)
            assert (got.kl_target_to_model, got.kl_model_to_target, got.kl_this_model_from_the_other, got.ce_model) == (v["kl"], v["reverse"], v["other"], v["ce"])
    r = table(planted, "s9_yardstick_ratios")
    want = {"own labels": OWN_LABELS, "the 64-token merge": OWN_LABELS + CURVE_1["3"] * U, "the one-text merge": OWN_LABELS + CURVE_1["4"] * U, "the self-merge": OWN_LABELS + 256 * U, "the never-named removal": UNMASKED_DELTA + 1024 * U}
    assert list(r.quantity) == list(want) and (r.comparison_model == "pythia-70m").all() and (r.divergence_to_the_primary_comparison_model == 2.0).all()  # the primary model on E: 2.0, not E_lab's 2.25 nor the other model's 1.5
    for k, v in want.items():
        assert one(r, quantity=k).ratio == pytest.approx(v / 2.0) and one(r, quantity=k).ratio_interval_lo == pytest.approx(v / 2.0) and one(r, quantity=k).nonfinite_share == 0


def test_the_gate_of_rule_1_and_the_token_ids(planted, tmp_path):
    root = tmp_path / "column"
    shutil.copytree(planted["root"], root)
    p = root / "tier5" / "E__plain_terms" / "per_sequence.parquet"
    t = pd.read_parquet(p)
    i = t.index[(t["cell"] == f"{RUN}/E/never_named_hard/D_unif/tau0.1/ones/incl/k0/r8") & (t["seq"] == 3)][0]
    t.loc[i, "top_changed"] = np.nextafter(np.float32(t.loc[i, "top_changed"]), np.float32(1))  # one text of one listed cell, one ulp
    t.to_parquet(p, index=False)
    with pytest.raises(AssertionError, match="THE GATE FAILS.*never_named"):
        a9.analyze_s9(root, tmp_path / "o1", spec=SPEC, committed_roots=None, require_canary=False, replicates=50, inputs=planted["inputs"], log=lambda *_: None)
    wrong = dataclasses.replace(planted["inputs"], ids={**planted["inputs"].ids, "E": np.roll(planted["inputs"].ids["E"], 1, axis=0)})  # the right set, its rows out of order
    with pytest.raises(AssertionError, match="are these the launch's ids"):
        a9.analyze_s9(planted["root"], tmp_path / "o2", spec=SPEC, committed_roots=None, require_canary=False, replicates=50, inputs=wrong, log=lambda *_: None)


# ----------------------------------------------------------------------------- the loader


def test_the_canary_inside_the_loader(planted, tmp_path):
    can = planted["summary"]["canary"]
    assert can["checked"] and can["stores"]["E__plain_terms"]["n_reruns"] == 6 * 8 + 1 + 2 * 8 + 8 + 1 and can["stores"]["E__plain_terms"]["cells_bitwise_equal"] == can["stores"]["E__plain_terms"]["n_reruns"] + 25
    assert can["stores"]["E_lab__same_domain"]["cells_bitwise_equal"] == 25 and can["stores"]["D_unif__self_merge"]["cells_bitwise_equal"] == 0 and can["across_stores"]["E_lab"]["stores"] == ["E_lab__plain_terms", "E_lab__same_domain", "E_lab__self_merge"]
    load = lambda root, committed: a9.load_tier5(root, frozen=None, committed_roots=(committed,), require_canary=True, log=lambda *_: None)  # noqa: E731
    # one text of one re-run cell one ulp off
    committed = tmp_path / "ulp"
    shutil.copytree(planted["committed"], committed)
    p = committed / "tier1" / "E" / "per_sequence.parquet"
    t = pd.read_parquet(p)
    i = t.index[(t["cell"] == f"{RUN}/E/union/D_unif/tau0.1/r0/excl/k5/r3") & (t["seq"] == 17)][0]
    t.loc[i, "kl_mean"] = np.nextafter(np.float32(t.loc[i, "kl_mean"]), np.float32(9))
    t.to_parquet(p, index=False)
    with pytest.raises(AssertionError, match="THE CANARY FAILS.*k5/r3"):
        load(planted["root"], committed)
    # a re-run cell that no committed store holds
    missing = tmp_path / "missing"
    shutil.copytree(planted["committed"], missing)
    for f in ("cells.parquet", "per_sequence.parquet"):
        t = pd.read_parquet(missing / "tier1" / "E" / f)
        t[~t["cell"].str.contains("never_named")].to_parquet(missing / "tier1" / "E" / f, index=False)
    with pytest.raises(AssertionError, match="no committed store holds"):
        load(planted["root"], missing)
    with pytest.raises(AssertionError, match="overlap"):
        load(planted["root"], planted["root"] / "tier5")
    with pytest.raises(AssertionError, match="must be given"):
        a9.load_tier5(planted["root"], frozen=None, committed_roots=None, require_canary=True, log=lambda *_: None)
    # a reference that differs between two tier-5 stores of one set
    root = tmp_path / "refs"
    shutil.copytree(planted["root"], root)
    p = root / "tier5" / "E_lab__self_merge" / "per_sequence.parquet"
    t = pd.read_parquet(p)
    i = t.index[(t["cell"] == f"{RUN}/E_lab/ref/rounded_0.5") & (t["seq"] == 0)][0]
    t.loc[i, "kl_mean"] = np.float32(0.75)
    t.to_parquet(p, index=False)
    with pytest.raises(AssertionError, match="differs between"):
        a9.load_tier5(root, frozen=None, committed_roots=None, require_canary=False, log=lambda *_: None)


def test_the_loader_refuses_what_is_missing_incomplete_or_blind(planted, tmp_path):
    quiet = dict(frozen=None, committed_roots=None, require_canary=False, log=lambda *_: None)
    root = tmp_path / "missing_store"
    shutil.copytree(planted["root"], root)
    shutil.rmtree(root / "tier5" / "D_unif__self_merge")
    with pytest.raises(AssertionError, match="reads exactly"):
        a9.load_tier5(root, **quiet)
    root = tmp_path / "incomplete"
    shutil.copytree(planted["root"], root)
    p = root / "tier5" / "E__self_merge" / "marker.json"
    marker = json.loads(p.read_text())
    p.write_text(json.dumps({**marker, "subbatch": 16}))  # three sub-batches, one done
    with pytest.raises(AssertionError, match="not complete"):
        a9.load_tier5(root, **quiet)
    root = tmp_path / "short"
    shutil.copytree(planted["root"], root)
    p = root / "tier5" / "E__self_merge" / "per_sequence.parquet"
    t = pd.read_parquet(p)
    t.iloc[:-1].to_parquet(p, index=False)
    with pytest.raises(AssertionError, match="every sequence exactly once"):
        a9.load_tier5(root, **quiet)
    (tmp_path / "failed").mkdir()
    shutil.copytree(planted["root"] / "tier5", tmp_path / "failed" / "tier5")
    (tmp_path / "failed" / "tier5" / "E__self_merge" / "error.txt").write_text("out of memory")
    with pytest.raises(AssertionError, match="recorded a failure"):
        a9.load_tier5(tmp_path / "failed", **quiet)
    # a store of the paper's model: never without --frozen, never without the canary, never with handed-in inputs
    main = tmp_path / "main"
    build_root(main, run="main")
    with pytest.raises(AssertionError, match="--frozen"):
        a9.load_tier5(main, **quiet)
    with pytest.raises(AssertionError, match="--frozen"):
        a9.load_tier5(main, frozen="0000000", committed_roots=None, require_canary=False, log=lambda *_: None)


def test_the_strata_and_their_resamples(planted):
    t5 = a9.load_tier5(planted["root"], frozen=None, committed_roots=None, require_canary=False, log=lambda *_: None)
    strata, rec = a9.build_strata(planted["inputs"], SPEC, t5, 50, 0)
    src, docs = np.asarray(planted["inputs"].sources), planted["inputs"].documents
    assert set(strata) == {"E", "D_unif", "G", "P", "O", "E_lab"} | {f"source:{s}" for s, _, _ in SOURCES} and strata["G"].sources == ("code",) and strata["P"].sources == ("prose_a", "prose_b") and strata["O"].n_texts == 69
    assert np.array_equal(strata["G"].primary.W, document_resample(docs[src == "code"], 50, (0, "boot_docs", "E_lab", "code")).W)  # a stratum of one source is document_resample of that source
    assert np.array_equal(strata["P"].primary.W[:, :20], strata["source:prose_a"].primary.W) and np.array_equal(strata["O"].primary.W[:, 20:40], strata["source:prose_b"].primary.W)  # a pooled stratum resamples within source
    assert np.array_equal(strata["E"].primary.W, st.Resample.make(40, 50, (0, "boot", "E")).W) and strata["E"].rows is None and strata["E"].n_documents is None
    from vpd_audit.analysis import _resample_for

    class _Grid:
        sets = {"E_lab": type("S", (), {"n_sequences": 93})()}

    assert np.array_equal(strata["P"].rows.W, _resample_for(_Grid(), "E_lab", strata["P"].mask, 50, 0, {}).W) and np.array_equal(strata["E_lab"].rows.W, _resample_for(_Grid(), "E_lab", None, 50, 0, {}).W)
    assert strata["source:papers"].n_documents == 3 and strata["O"].thin_sources == ["papers"] and strata["G"].flag == "" and rec["documents"]["P"]["n_documents"] == 20
    with pytest.raises(AssertionError, match="more than one block"):
        a9.build_strata(dataclasses.replace(planted["inputs"], sources=planted["inputs"].sources[::-1][:1] + planted["inputs"].sources[1:]), SPEC, t5, 10, 0)


def test_the_three_pools_draw_tables_are_asserted_pairwise_different(monkeypatch):
    tables = a9.draw_tables(8, 50, 0)
    assert list(tables) == ["D_code", "D_unif", "D_prose"] and all(np.array_equal(t, s9.draw_counts(8, 50, (0, "boot_draws", pool))) and (t.sum(axis=1) == 8).all() for pool, t in tables.items())
    assert not np.array_equal(a9.draw_tables(8, 50, 1)["D_code"], tables["D_code"])
    one_seed = s9.draw_counts
    monkeypatch.setattr(s9, "draw_counts", lambda n, r, seed: one_seed(n, r, (0, "boot_draws")))  # the realistic bug: one seed for every pool
    with pytest.raises(AssertionError, match="are the same table"):
        a9.draw_tables(8, 50, 0)
    monkeypatch.setattr(s9, "draw_counts", lambda n, r, seed: one_seed(n, r, seed) + (np.arange(n) == 0))
    with pytest.raises(AssertionError, match="does not hold 8 draws"):
        a9.draw_tables(8, 50, 0)


# ----------------------------------------------------------------------------- the committed stand-in stores

DRY_S9 = ROOT / "results" / "dry_run_s9"
needs_stand_in = pytest.mark.skipif(not all((DRY_S9 / "tier5" / s / "extras" / "target__top.npy").is_file() for s in a9.REQUIRED_STORES) or not (ROOT / "results" / "dry_run" / "E" / "per_sequence.parquet").is_file(),
                                    reason="the stand-in's tier-5 stores with their per-position arrays (git-ignored; pulled from the volume) are not present")


@needs_stand_in
def test_the_stand_in_runs_whole_with_the_canary(tmp_path):
    with open(DRY_S9 / "tier5" / "summary__self_merge.json") as f:
        rows = json.load(f)["config"]["synthetic_document_rows"]
    out = a9.analyze_s9(DRY_S9, tmp_path, spec=a9.stand_in_spec(rows), committed_roots=(ROOT / "results" / "dry_run", ROOT / "results" / "dry_run_s7"), require_canary=True, replicates=200, log=lambda *_: None)
    assert out["canary"]["checked"] and all(v["pass"] for v in out["canary"]["stores"].values()) and out["run2"]["verdict"]["outcome"] in (s9.NO_READING, s9.F_SAME, s9.F_LATER, s9.D_BELOW, s9.H, s9.D_UNRESOLVED)
    assert (tmp_path / "report.md").is_file() and not out["yardstick"]["available"] and all(g["pass"] for g in out["plain_terms"]["gates"].values())
