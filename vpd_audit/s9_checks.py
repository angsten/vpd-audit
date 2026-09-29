"""The checks that need no GPU: a document index and four checks, (a) to (d).

The document index of E_lab, D_code, and D_prose. `prepare_labeled_sets` takes the first n rows of a tokenized part, and
the authors' `tokenize_and_concatenate` joins a part's documents with end-of-text ids and cuts the stream into rows in order, so
the rows of a labelled set are consecutive windows of its first few documents. Documents are numbered per source block by the
running count of end-of-text ids (id 0); a row's *document* is its majority document, the one holding most of its tokens (ties
to the earlier; the end-of-text ids themselves are not counted, as in the worked example, 100 + 411 tokens around one id). The
saved rows are the first 512 of 513 tokens, so one stream token in 513 is not in the saved set and an end-of-text id there is
invisible: the expected number of boundaries hidden that way is printed per block. The document bootstrap (`document_resample`)
draws documents with replacement within a source, all rows of a drawn document together, and every mean stays row-weighted: the
resampled row total over the resampled row count (`doc_means`, through `Resample.ratios`). `Resample.means` divides by the
fixed n and must never be called on a document resample. No interval for a stratum of fewer than ten documents.

Check (a). The code-leaning group's damage per unit of removed label against its twins', by source of E_lab, from the
committed tier-4 store, with the damage computed by `analysis.excess_matrix` and `stats_s7.mean_interval` as
`analysis_s7.analyze_code_leaning` computes the by-source damage; the group-to-twins ratio with a document-bootstrap interval.

Check (b). The existence rule (`code_leaning.leaning_table`, `leaning_group`, `pre_reads.existence_verdict`,
unchanged) on matched pools of 256 rows, with the support floor counted in rows and in documents, and one null function
(`s9_null`) with two parameters, what is shuffled and what the floor counts, asserted to reproduce `pre_reads.shuffle_null` bit
for bit at (rows, rows). Runs where the main run's label caches live (the Modal volume).

Check (d). Where the merging harm falls: over texts from the committed tables, over positions from the float16
per-position arrays pulled from the Modal volume into the stores' git-ignored kl/ folders.

Check (c). The donors' kind of text against the small-merge harm: a label-only half where the caches live (the named
and matched sets, rebuilt through `cells.build_sources`, and their shares inside the code-leaning and prose-leaning groups),
and a local half (the reader labels and U - M from the committed stores).

    uv run vpd-audit s9-checks --cache-half            (where the caches live; on Modal: modal_app.py::s9_label_tables)
    uv run vpd-audit s9-checks --pull                  (the per-position arrays of check (d), from the volume)
    uv run vpd-audit s9-checks --frozen <HEAD>         (the document index, checks (a) and (d), the local halves of (b) and (c), and the report)

Every reading rule here was fixed before any of these numbers existed.
"""

from __future__ import annotations

import hashlib
import json
import subprocess
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from vpd_audit import env
from vpd_audit import stats as st
from vpd_audit.constants import SEQ_LEN
from vpd_audit.masks import seed_from_tuple

EOT_ID = 0  # the end-of-text id of EleutherAI/gpt-neox-20b (sets/labeled_manifest.json records eos_token_id 0)
RAW_ROW_LEN = SEQ_LEN + 1  # a tokenized row has 513 ids; the saved row is its first 512
DOC_SETS = ("E_lab", "D_code", "D_prose")
MIN_DOCUMENTS_FOR_INTERVAL = 10
NEAR_DUP_WINDOW = 50
REPLICATES = st.N_REPLICATES  # 10,000
VOLUME_NAME = "vpd-audit-cache"
S9_DIR_NAME = "s9"
# The six statistics and analysis modules stay held to `main`'s blobs beside --frozen. The five harness modules below, which later
# stages extended additively, are recorded, not asserted: their blobs as committed (RECORDED_AT), beside their blobs on disk and at
# HEAD, so that a reader sees whether a rerun used the code the committed outputs came from. A rerun from a clean tree must still
# reproduce every committed CSV byte for byte.
FROZEN_MODULES = ("stats.py", "stats_s7.py", "analysis.py", "analysis_s7.py", "figures.py", "figures_s7.py")
RECORDED_AT = "HEAD"
RECORDED_MODULES = {"cells.py": "3adca95be8842d5455340395d50e3163a8b75870", "sources.py": "bd7256908f365ca070c4551f6ed5755d7bbfcc37", "code_leaning.py": "1e6c637a871f2518d9cb40c69d462e6a2fd9b24f",
                    "grid.py": "3186e4405db18490b1f0755dc4653ca888074efc", "pre_reads.py": "879ad795fc63174b7c6b6e847754c0a5ca1f9094"}


def analysis_dir(run: str = "main") -> Path:
    return env.PROJECT_ROOT / "results" / "grid" / "analysis" / run / S9_DIR_NAME


# ============================================================================= the document index


def block_document_index(block: np.ndarray, eot: int = EOT_ID) -> dict[str, np.ndarray]:
    """One source block, (n_rows, T) ids in tokenization order. A token's document is the number of end-of-text ids before it in
    the block; an end-of-text id carries the number of the document it closes and is not counted toward a majority. Returns per
    row the majority document (ties to the earlier document), the document of the row's first token, and the number of
    end-of-text ids inside the row."""
    block = np.asarray(block)
    assert block.ndim == 2
    n, T = block.shape
    is_eot = block.reshape(-1) == eot
    doc = (np.cumsum(is_eot) - is_eot).reshape(n, T)
    is_eot = is_eot.reshape(n, T)
    majority = np.empty(n, dtype=np.int64)
    for r in range(n):
        d = doc[r][~is_eot[r]]
        if d.size == 0:
            majority[r] = doc[r, 0]
            continue
        v, c = np.unique(d, return_counts=True)  # ascending, and argmax returns the first maximum: ties go to the earlier document
        majority[r] = v[int(np.argmax(c))]
    return {"majority": majority, "first": doc[:, 0].astype(np.int64), "n_eot": is_eot.sum(axis=1).astype(np.int64)}


def set_sources(name: str, record: dict[str, Any], n_rows: int) -> list[str]:
    """The source of every row of a labelled set, from the set's own record: `strata` (E_lab, D_prose) or `label` (D_code)."""
    if "strata" in record:
        src = [str(s) for s in record["strata"]]
    else:
        assert "label" in record, f"set {name!r}: its record names neither strata nor a label"
        src = [str(record["label"])] * n_rows
    assert len(src) == n_rows, (name, len(src), n_rows)
    return src


def contiguous_blocks(sources: list[str]) -> list[tuple[str, int, int]]:
    """(source, start, stop) of each run of equal sources; every source must form exactly one run (a block)."""
    out: list[tuple[str, int, int]] = []
    start = 0
    for i in range(1, len(sources) + 1):
        if i == len(sources) or sources[i] != sources[start]:
            out.append((sources[start], start, i))
            start = i
    assert len({s for s, _, _ in out}) == len(out), f"a source appears in more than one block: {[s for s, _, _ in out]}"
    return out


def document_index(sets: tuple[str, ...] = DOC_SETS, sets_dir: Path | None = None) -> pd.DataFrame:
    """The document index table: set, row, source, majority document, first-token document, end-of-text count; documents restart at 0 in
    each source block."""
    from vpd_audit.data import load_set

    rows = []
    for name in sets:
        ids, _, record = load_set(name, sets_dir or env.SETS_DIR)
        src = set_sources(name, record, ids.shape[0])
        for source, a, b in contiguous_blocks(src):
            di = block_document_index(ids[a:b])
            for i in range(b - a):
                rows.append({"set": name, "row": a + i, "source": source, "majority_document": int(di["majority"][i]), "first_token_document": int(di["first"][i]), "n_end_of_text": int(di["n_eot"][i])})
    return pd.DataFrame(rows)


def document_counts(index: pd.DataFrame) -> pd.DataFrame:
    """Per set and source: rows, distinct (majority) documents, the documents by end-of-text count plus one, rows per document,
    and the expected number of boundaries hidden by the unsaved 513th token of each row: of the block's n - 1 unsaved tokens
    between its rows, each is an end-of-text id at the rate seen in the saved ones."""
    out = []
    for (name, source), g in index.groupby(["set", "source"], sort=False):
        per_doc = g.groupby("majority_document").size()
        n_rows, n_eot = int(len(g)), int(g["n_end_of_text"].sum())
        out.append({"set": name, "source": source, "rows": n_rows, "distinct_documents": int(per_doc.size), "documents_by_end_of_text_count": n_eot + 1,
                    "rows_per_document_mean": float(per_doc.mean()), "rows_per_document_max": int(per_doc.max()), "n_end_of_text": n_eot,
                    "expected_hidden_boundaries": float(n_eot * (n_rows - 1) / (SEQ_LEN * n_rows))})
    return pd.DataFrame(out)


def document_codes(index: pd.DataFrame, name: str, lo: int, hi: int) -> np.ndarray:
    """Rows lo..hi-1 of a set as integer document codes, distinct per (source, majority document), in row order."""
    g = index[(index["set"] == name) & (index["row"] >= lo) & (index["row"] < hi)].sort_values("row")
    assert len(g) == hi - lo, f"{name}: the document index holds {len(g)} of rows {lo}..{hi - 1}"
    keys = list(zip(g["source"], g["majority_document"]))
    codes: dict[tuple[str, int], int] = {}
    return np.asarray([codes.setdefault(k, len(codes)) for k in keys], dtype=np.int64)


def near_duplicate_screen(a_ids: np.ndarray, b_ids: np.ndarray, window: int = NEAR_DUP_WINDOW) -> tuple[float, pd.DataFrame]:
    """The share of the rows of `a_ids` that share at least one exact `window`-token window with any row of `b_ids`, and the
    pairs (a row, b row, the number of a's windows found in b's row, the first such window's offset in each). A description."""
    from numpy.lib.stride_tricks import sliding_window_view

    a_ids, b_ids = np.ascontiguousarray(a_ids, dtype=np.int32), np.ascontiguousarray(b_ids, dtype=np.int32)
    seen: dict[bytes, dict[int, int]] = {}
    for r, row in enumerate(sliding_window_view(b_ids, window, axis=1)):
        for off, w in enumerate(row):
            seen.setdefault(w.tobytes(), {}).setdefault(r, off)
    pairs: dict[tuple[int, int], list[int]] = {}
    for r, row in enumerate(sliding_window_view(a_ids, window, axis=1)):
        for off, w in enumerate(row):
            hit = seen.get(w.tobytes())
            if hit:
                for br, boff in hit.items():
                    p = pairs.setdefault((r, br), [0, off, boff])
                    p[0] += 1
    df = pd.DataFrame([{"a_row": a, "b_row": b, "n_shared_windows": v[0], "first_offset_a": v[1], "first_offset_b": v[2]} for (a, b), v in sorted(pairs.items())],
                      columns=["a_row", "b_row", "n_shared_windows", "first_offset_a", "first_offset_b"])
    share = float(df["a_row"].nunique() / a_ids.shape[0]) if a_ids.shape[0] else float("nan")
    return share, df


# ----------------------------------------------------------------------------- the document bootstrap


def document_resample(doc_ids: np.ndarray, replicates: int, seed_tuple: tuple[Any, ...]) -> st.Resample:
    """Documents drawn with replacement (as many draws as there are documents), all rows of a drawn document entering together: a
    row's count is its document's. Use `doc_means` and `Resample.ratios` on it, never `Resample.means`, which divides by n."""
    doc_ids = np.asarray(doc_ids)
    docs, inv = np.unique(doc_ids, return_inverse=True)
    D = int(docs.size)
    rng = np.random.default_rng(seed_from_tuple(seed_tuple))
    Wd = np.zeros((replicates, D), dtype=np.int32)
    for r in range(replicates):
        Wd[r] = np.bincount(rng.integers(0, D, size=D), minlength=D)
    return st.Resample(n=int(doc_ids.size), replicates=replicates, seed_tuple=tuple(seed_tuple), W=np.ascontiguousarray(Wd[:, inv]))


def doc_means(resample: st.Resample, v: np.ndarray) -> np.ndarray:
    """The row-weighted mean per replicate: the resampled row total over the resampled row count."""
    return resample.ratios(np.asarray(v, dtype=np.float64), np.ones(resample.n, dtype=np.float64))


def interval_or_none(stats: np.ndarray, n_documents: int) -> list[float] | None:
    """The uncorrected 95 percent percentile interval, or None for a stratum of fewer than ten documents."""
    if n_documents < MIN_DOCUMENTS_FOR_INTERVAL:
        return None
    lo, hi = st.percentile_interval(stats, 1)
    return [lo, hi]


# ============================================================================= the freeze guard's content


def frozen_blobs(against: str = "main") -> dict[str, Any]:
    """`load_grid` holds the paper's stores to --frozen equal to HEAD on a clean tree, which by itself can never fail; its content
    is here: each of the six frozen statistics and analysis modules (FROZEN_MODULES) must be, on disk and at HEAD, the blob it is
    on `main` (`pass` rests on these alone). The five harness modules of RECORDED_MODULES are recorded beside them, never asserted:
    their blobs on disk and at HEAD against their blobs at RECORDED_AT, the commit that produced the committed outputs.
    The constants are checked against git where that commit is reachable."""
    def git(*args: str) -> str:
        return subprocess.run(["git", "-C", str(env.PROJECT_ROOT), *args], check=True, capture_output=True, text=True).stdout.strip()

    rows = []
    for m in FROZEN_MODULES:
        rel = f"vpd_audit/{m}"
        rows.append({"module": rel, "blob_on_disk": git("hash-object", rel), "blob_at_head": git("rev-parse", f"HEAD:{rel}"), f"blob_on_{against}": git("rev-parse", f"{against}:{rel}")})
    for r in rows:
        r["equal"] = bool(r["blob_on_disk"] == r["blob_at_head"] == r[f"blob_on_{against}"])
    recorded = []
    for m, blob in RECORDED_MODULES.items():
        rel = f"vpd_audit/{m}"
        try:
            in_git = git("rev-parse", f"{RECORDED_AT}:{rel}")
        except subprocess.CalledProcessError:
            in_git = None  # the commit is not reachable here (a shallow copy); the constant stands
        assert in_git in (None, blob), f"{rel}: the recorded blob {blob[:12]} is not the blob at {RECORDED_AT} ({in_git})"
        on_disk, at_head = git("hash-object", rel), git("rev-parse", f"HEAD:{rel}")
        recorded.append({"module": rel, "blob_on_disk": on_disk, "blob_at_head": at_head, f"blob_at_{RECORDED_AT}": blob, "unchanged_since": bool(on_disk == at_head == blob)})
    return {"against": against, "against_commit": git("rev-parse", against), "head": git("rev-parse", "HEAD"), "modules": rows, "pass": bool(all(r["equal"] for r in rows)),
            "recorded_at": RECORDED_AT, "recorded": recorded}


# ============================================================================= check (a)

CHECK_A_MARK = 0.2  # the mark: the group's damage per unit of label removed is under a fifth of its twins'
CHECK_A_SIZES = (64, 256)
CHECK_A_SOURCES = ("Pile-CC", "Wikipedia (en)")
MET, NOT_MET, UNDECIDED = "met", "not met", "undecided on that source"


def check_a_source_reading(per_size: dict[int, dict[str, Any]], mark: float = CHECK_A_MARK) -> str:
    """The reading fixed before the run on one prose source: per size, `ratio_interval` ([lo, hi] or None) and `guard` (the interval of the
    group's removed label and the interval of the twins' damage per unit of label both exclude zero). Met if the upper end is
    below the mark at every size; not met if the lower end is above it at every size; otherwise undecided. A size whose guard
    fails, or which has no interval, is not read, and the source is undecided."""
    if any((not v["guard"]) or v["ratio_interval"] is None or not np.all(np.isfinite(v["ratio_interval"])) for v in per_size.values()):
        return UNDECIDED
    if all(v["ratio_interval"][1] < mark for v in per_size.values()):
        return MET
    if all(v["ratio_interval"][0] > mark for v in per_size.values()):
        return NOT_MET
    return UNDECIDED


def check_a_supported(readings: dict[str, str]) -> bool:
    """"The labels fire on prose without effect" is supported only if the mark is met on both prose sources."""
    return bool(readings) and all(v == MET for v in readings.values())


def per_unit_ratio(e_g: np.ndarray, om_g: np.ndarray, e_t: np.ndarray, om_t: np.ndarray, resample: st.Resample | None, n_documents: int) -> dict[str, Any]:
    """Per text of one source: the group's damage and removed label, and the twins' (each the mean over the draws). Point values:
    the mean removed labels, the damages per unit of removed label (ratios of means), and the group-to-twins ratio of those. With
    a document resample: the intervals of the group's removed label, of the twins' damage per unit, and of the ratio, every sum
    recomputed within each replicate; a replicate whose ratio is undefined (a zero denominator) is dropped and counted."""
    e_g, om_g, e_t, om_t = (np.asarray(x, dtype=np.float64) for x in (e_g, om_g, e_t, om_t))
    with np.errstate(divide="ignore", invalid="ignore"):
        pu_g = float(e_g.mean() / om_g.mean()) if om_g.mean() > 0 else float("nan")
        pu_t = float(e_t.mean() / om_t.mean()) if om_t.mean() > 0 else float("nan")
        ratio = pu_g / pu_t if np.isfinite(pu_g) and np.isfinite(pu_t) and pu_t != 0 else float("nan")
    out: dict[str, Any] = {"omega_group": float(om_g.mean()), "omega_twins": float(om_t.mean()), "H_group": float(e_g.mean()), "H_twins": float(e_t.mean()), "H_per_omega_group": pu_g, "H_per_omega_twins": pu_t,
                           "ratio_group_to_twins": float(ratio), "omega_group_interval": None, "H_per_omega_twins_interval": None, "ratio_interval": None, "n_replicates_undefined": None, "guard": False}
    if resample is None or n_documents < MIN_DOCUMENTS_FOR_INTERVAL:
        return out
    W = resample.W.astype(np.float64)
    a, b, c, d = W @ e_g, W @ om_g, W @ e_t, W @ om_t
    with np.errstate(divide="ignore", invalid="ignore"):
        pu_t_rep = np.where(d > 0, c / np.where(d > 0, d, 1.0), np.nan)
        ok = (b > 0) & (d > 0) & (c != 0)
        rep = np.where(ok, (a / np.where(b > 0, b, 1.0)) / np.where(ok, pu_t_rep, 1.0), np.nan)
    out["omega_group_interval"] = interval_or_none(doc_means(resample, om_g), n_documents)
    out["H_per_omega_twins_interval"] = interval_or_none(pu_t_rep, n_documents)
    out["ratio_interval"] = interval_or_none(rep, n_documents)
    out["n_replicates_undefined"] = int((~np.isfinite(rep)).sum())
    out["guard"] = bool(excludes_zero(out["omega_group_interval"]) and excludes_zero(out["H_per_omega_twins_interval"]))
    return out


def excludes_zero(interval: list[float] | None) -> bool:
    return bool(interval is not None and np.all(np.isfinite(interval)) and (interval[0] > 0 or interval[1] < 0))


def check_a(grid: Any, strata: dict[str, Any], index: pd.DataFrame, resamples: dict, *, replicates: int = REPLICATES, master_seed: int = 0, log: Any = print) -> dict[str, Any]:
    """Check (a) from the committed tier-4 store, through the loaded grid: per chain size and source of E_lab."""
    from vpd_audit import stats_s7 as s7
    from vpd_audit.analysis import _resample_for, excess_matrix, matrix
    from vpd_audit.analysis_s7 import _iv
    from vpd_audit.cells import code_leaning_size
    from vpd_audit.stats import CONTRIBUTING_MIN_T_STAR

    sd = grid.sets["E_lab"]
    cl = [c for c in sd.cell_objects.values() if c.family == "code_leaning_hard"]
    erase = {c.rung: c for c in cl if c.control == "none"}
    control: dict[str, list[Any]] = {}
    for c in cl:
        if c.control == "usage":
            control.setdefault(c.rung, []).append(c)
    for r in control:
        control[r].sort(key=lambda x: x.draw)
    rungs = sorted(erase, key=code_leaning_size)
    assert rungs and set(control) == set(erase) and len({len(control[r]) for r in rungs}) == 1, "every rung has its control, with the same number of draws"
    groups, positive = strata["E_lab"]["groups"], strata["E_lab"]["positive"]
    sources = [positive] + sorted(k for k in groups if k not in ("all", "other", positive))
    el = index[index["set"] == "E_lab"].sort_values("row")
    assert len(el) == sd.n_sequences and list(el["source"]) == list(strata["E_lab"]["labels"]), "the document index's sources are the store's strata, row for row"
    docs_all = el["majority_document"].to_numpy(np.int64)
    rows, doc_rs = [], {}
    for sname in sources:
        mask = groups[sname]
        docs = docs_all[mask]
        n_docs = int(np.unique(docs).size)
        doc_rs[sname] = document_resample(docs, replicates, (master_seed, "boot_docs", "E_lab", sname)) if n_docs >= MIN_DOCUMENTS_FOR_INTERVAL else None
        rs_rows = _resample_for(grid, "E_lab", mask, replicates, master_seed, resamples)  # the row resample analysis_s7 used, for its committed interval
        for r in rungs:
            e_g, e_c = excess_matrix(sd, [erase[r]])[:, mask], excess_matrix(sd, control[r])[:, mask]
            om_g, om_c = matrix(sd, [erase[r]], "omega")[:, mask].astype(np.float64), matrix(sd, control[r], "omega")[:, mask].astype(np.float64)
            t_g, t_c = matrix(sd, [erase[r]], "t_star_0.1")[:, mask], matrix(sd, control[r], "t_star_0.1")[:, mask]
            mi_g, mi_c = s7.mean_interval(e_g, rs_rows, 1), s7.mean_interval(e_c, rs_rows, 1)  # exactly analysis_s7's by-source damage
            v = per_unit_ratio(e_g[0], om_g[0], e_c.mean(axis=0), om_c.mean(axis=0), doc_rs[sname], n_docs)
            assert v["H_group"] == mi_g["mean"] and v["H_twins"] == mi_c["mean"], "the ratio's damages are analysis_s7's by-source damages"
            row = {"rung": r, "n_members": code_leaning_size(r), "descriptive": bool(erase[r].descriptive), "source": sname, "n_texts": int(mask.sum()), "n_documents": n_docs, "n_twin_draws": int(e_c.shape[0]),
                   **{k: v[k] for k in ("omega_group", "omega_twins", "H_group", "H_twins", "H_per_omega_group", "H_per_omega_twins", "ratio_group_to_twins")}}
            for key, col in (("omega_group_interval", "omega_group"), ("H_per_omega_twins_interval", "H_per_omega_twins"), ("ratio_interval", "ratio")):
                row[f"{col}_lo"], row[f"{col}_hi"] = (v[key] if v[key] is not None else (float("nan"), float("nan")))
            row.update({"n_replicates_undefined": v["n_replicates_undefined"], "guard_both_exclude_zero": v["guard"], "H_group_row_interval_s7": _iv(mi_g["interval"]), "H_twins_row_interval_s7": _iv(mi_c["interval"]),
                        "clean_prefix_fraction_group": float((t_g / SEQ_LEN).mean()), "clean_prefix_fraction_twins": float((t_c / SEQ_LEN).mean()),
                        "n_contributing_group": float((t_g >= CONTRIBUTING_MIN_T_STAR).sum(axis=1).mean()), "n_contributing_twins": float((t_c >= CONTRIBUTING_MIN_T_STAR).sum(axis=1).mean())})
            rows.append(row)
    table = pd.DataFrame(rows)
    # the regression check: the by-source damages against the committed tables, exactly
    reg = check_a_regression(table, grid.root.parent / "analysis" / grid.run)
    # the reading, fixed in advance
    readings, detail = {}, {}
    for sname in CHECK_A_SOURCES:
        per_size = {}
        for n in CHECK_A_SIZES:
            t = table[(table.source == sname) & (table.n_members == n)]
            assert len(t) == 1, f"no single row for {sname} at {n} members"
            t = t.iloc[0]
            iv = [float(t.ratio_lo), float(t.ratio_hi)]
            per_size[n] = {"ratio": float(t.ratio_group_to_twins), "ratio_interval": iv if np.all(np.isfinite(iv)) else None, "guard": bool(t.guard_both_exclude_zero), "n_documents": int(t.n_documents)}
        readings[sname] = check_a_source_reading(per_size)
        detail[sname] = per_size
    out = {"table": table, "regression": reg, "readings": readings, "detail": detail, "supported": check_a_supported(readings), "sources": sources, "rungs": rungs}
    log(f"[s9 check a] readings {readings}; 'the labels fire on prose without effect' supported: {out['supported']}; regression pass: {reg['pass']}")
    return out


def check_a_regression(table: pd.DataFrame, analysis_root: Path) -> dict[str, Any]:
    """The by-source damages reproduce s7_code_leaning_damage_by_source.csv exactly (value and printed interval); GitHub's, which
    that table does not hold, reproduce D_github of s7_code_leaning_damage.csv."""
    by = pd.read_csv(analysis_root / "s7_code_leaning_damage_by_source.csv", float_precision="round_trip")
    checks = []
    for _, r in by.iterrows():
        t = table[(table.rung == r["rung"]) & (table.source == r["source"])]
        assert len(t) == 1, (r["rung"], r["source"])
        t = t.iloc[0]
        got, got_iv = (t.H_group, t.H_group_row_interval_s7) if r["set"] == "group" else (t.H_twins, t.H_twins_row_interval_s7)
        checks.append({"rung": r["rung"], "source": r["source"], "set": r["set"], "committed": float(r["D"]), "computed": float(got), "equal": bool(float(got) == float(r["D"])), "interval_equal": bool(str(got_iv) == str(r["interval_95"]))})
    dmg = pd.read_csv(analysis_root / "s7_code_leaning_damage.csv", float_precision="round_trip")
    gh = []
    if {"rung", "D_github", "D_github_control"} <= set(dmg.columns):
        for _, r in dmg.iterrows():
            t = table[(table.rung == r["rung"]) & (table.source == "Github")]
            if len(t) == 1:
                for who, col, got in (("group", "D_github", t.iloc[0].H_group), ("control", "D_github_control", t.iloc[0].H_twins)):
                    gh.append({"rung": r["rung"], "source": "Github", "set": who, "committed": float(r[col]), "computed": float(got), "equal": bool(float(got) == float(r[col])), "interval_equal": None})
    allc = checks + gh
    return {"n_by_source": len(checks), "n_github": len(gh), "n_unequal": int(sum(not c["equal"] for c in allc)), "n_interval_unequal": int(sum(c["interval_equal"] is False for c in allc)),
            "max_abs_difference": float(max((abs(c["committed"] - c["computed"]) for c in allc), default=float("nan"))), "github_checked": bool(gh),
            "pass": bool(allc and all(c["equal"] for c in allc) and all(c["interval_equal"] is not False for c in allc)), "checks": allc}


# ============================================================================= check (b)

ROW_NULL_SEED = "code_leaning"  # pre_reads.shuffle_null's: (master, "shuffle", "code_leaning")
DOC_NULL_SEED = "s9_documents"  # (master, "shuffle", "s9_documents", pair)
N_SHUFFLES_RERUN = 2000
RERUN_FACTOR = 2.0


@dataclass(frozen=True)
class PairSpec:
    name: str
    slug: str
    a: tuple[str, int, int]  # (pool, first row, stop row)
    b: tuple[str, int, int]


PAIRS_MAIN: tuple[PairSpec, ...] = (
    PairSpec("Wikipedia against Pile-CC", "wikipedia_vs_pile_cc", ("D_prose", 256, 512), ("D_prose", 0, 256)),
    PairSpec("Pile-CC against Wikipedia", "pile_cc_vs_wikipedia", ("D_prose", 0, 256), ("D_prose", 256, 512)),
    PairSpec("code against Pile-CC", "code_vs_pile_cc", ("D_code", 0, 256), ("D_prose", 0, 256)),
    PairSpec("Pile-CC against code", "pile_cc_vs_code", ("D_prose", 0, 256), ("D_code", 0, 256)),
    PairSpec("code against Wikipedia", "code_vs_wikipedia", ("D_code", 0, 256), ("D_prose", 256, 512)),
    PairSpec("Wikipedia against code", "wikipedia_vs_code", ("D_prose", 256, 512), ("D_code", 0, 256)),
)
REGRESSION_MAIN = PairSpec("code against prose, 512 against 512 (the code-leaning group's)", "code_vs_prose_512", ("D_code", 0, 512), ("D_prose", 0, 512))
REGRESSION_EXPECTED = {"n_members": 1007, "mass_2dp": 49.47, "share_3dp": 0.248}  # the values fixed in advance


def _distinct_documents_present(present_rows: np.ndarray, docs: np.ndarray) -> np.ndarray:
    """Per column, the number of distinct documents among the given rows with a True entry; present_rows (n, C) bool."""
    order = np.argsort(docs, kind="stable")
    d = docs[order]
    starts = np.flatnonzero(np.concatenate([[True], d[1:] != d[:-1]]))
    per_doc = np.add.reduceat(present_rows[order].astype(np.int32), starts, axis=0)
    return (per_doc > 0).sum(axis=0)


def s9_null(counts_a: np.ndarray, counts_b: np.ndarray, docs_a: np.ndarray, docs_b: np.ndarray, *, shuffle: str, floor: str, variant: str = "a", threshold: float | None = None,
            n_shuffles: int = 200, seed_tuple: tuple[Any, ...]) -> pd.DataFrame:
    """The existence rule's null with two parameters: what is shuffled ("rows" or "documents") and what the support
    floor counts ("rows" or "documents"). counts_* are per-row counts of naming positions (rows, columns: the alive set);
    docs_* each pool's per-row document codes. Shuffling rows is `pre_reads.shuffle_null`'s permutation of the pooled rows,
    pseudo-pool A its first n_a; at (rows, rows) under that function's seed the table is that function's, bit for bit. Shuffling
    documents permutes the pooled documents, all rows of a document moving together: variant "a" takes the first D_A of the
    permutation (D_A pool A's true number of documents), variant "b" takes documents in permuted order until the row count is
    nearest pool A's (ties to the fewer). Usage rates are per position of the pseudo-pool actually formed. Row -1 is the true
    labelling through the same code. The rule's own `leaning_table` and `leaning_group` do the rest, unchanged."""
    from vpd_audit.code_leaning import CL_GROUP, leaning_group, leaning_table

    assert shuffle in ("rows", "documents") and floor in ("rows", "documents") and variant in ("a", "b")
    threshold = CL_GROUP if threshold is None else threshold
    n_a, n_b = counts_a.shape[0], counts_b.shape[0]
    assert docs_a.shape == (n_a,) and docs_b.shape == (n_b,)
    counts = np.concatenate([counts_a, counts_b], axis=0)
    present = counts > 0
    da = np.unique(docs_a, return_inverse=True)[1]
    db = np.unique(docs_b, return_inverse=True)[1]
    D_A = int(da.max()) + 1
    docs = np.concatenate([da, db + D_A])  # pooled document codes: pool A's first, then pool B's
    D = int(docs.max()) + 1
    rng = np.random.default_rng(seed_from_tuple(seed_tuple))
    if shuffle == "documents":
        counts_u = np.zeros((D, counts.shape[1]), dtype=np.int64)
        np.add.at(counts_u, docs, counts)
        rows_present_u = np.zeros((D, counts.shape[1]), dtype=np.int64)
        np.add.at(rows_present_u, docs, present)
        n_rows_u = np.bincount(docs, minlength=D)
    rows = []
    for i in range(-1, n_shuffles):
        if shuffle == "rows":
            perm = np.arange(n_a + n_b) if i < 0 else rng.permutation(n_a + n_b)
            a, b = perm[:n_a], perm[n_a:]
            floor_a = present[a].sum(axis=0) if floor == "rows" else _distinct_documents_present(present[a], docs[a])
            t = leaning_table(counts[a].sum(axis=0, dtype=np.int64), floor_a, counts[b].sum(axis=0, dtype=np.int64), n_a * SEQ_LEN, n_b * SEQ_LEN)
            n_rows_pa, n_docs_pa = n_a, int(np.unique(docs[a]).size)
        else:
            perm = np.arange(D) if i < 0 else rng.permutation(D)
            if variant == "a":
                cut = D_A
            else:
                cum = np.cumsum(n_rows_u[perm])
                cut = int(np.argmin(np.abs(cum - n_a))) + 1  # argmin returns the first minimum: ties to the fewer documents
            cut = min(max(cut, 1), D - 1)
            a, b = perm[:cut], perm[cut:]
            n_rows_pa, n_docs_pa = int(n_rows_u[a].sum()), int(cut)
            floor_a = rows_present_u[a].sum(axis=0) if floor == "rows" else (counts_u[a] > 0).sum(axis=0)
            t = leaning_table(counts_u[a].sum(axis=0, dtype=np.int64), floor_a, counts_u[b].sum(axis=0, dtype=np.int64), n_rows_pa * SEQ_LEN, (n_a + n_b - n_rows_pa) * SEQ_LEN)
        G = leaning_group(t, threshold)
        total, mass = float(t["u_a"].sum()), float(t["u_a"][G].sum())
        rows.append({"shuffle": i, "n_members": int(G.sum()), "mass": mass, "total_mass": total, "share": mass / total if total else float("nan"), "n_rows_pseudo_a": n_rows_pa, "n_documents_pseudo_a": n_docs_pa})
    return pd.DataFrame(rows)


def needs_rerun(null_p95: float, mass: float, factor: float = RERUN_FACTOR) -> bool:
    """The rerun condition: the null's 95th percentile lies within a factor of two of the bar (a fifth of the group's mass)."""
    from vpd_audit.pre_reads import CL_NULL_FRACTION

    bar = CL_NULL_FRACTION * mass
    return bool(bar > 0 and bar / factor <= null_p95 <= bar * factor)


def combine_variants(word_a: str, word_b: str) -> str:
    """If the two document nulls give different words, both are printed and the pair is treated as marginal."""
    return word_a if word_a == word_b else "marginal"


def existence_pair(spec: PairSpec, counts_a: np.ndarray, counts_b: np.ndarray, docs_a: np.ndarray, docs_b: np.ndarray, *, master_seed: int = 0, n_shuffles: int = 200, only_rows_rows: bool = False,
                   log: Any = print) -> list[dict[str, Any]]:
    """One pair under both floors and the three nulls (rows; documents, variants a and b). Verdict words come from the document
    nulls only; the row null is printed beside them. If a document null's 95th percentile lies within a factor of two of the
    bar, every null of the pair is rerun with 2,000 shuffles and both runs are kept; the verdict is the larger run's."""
    from vpd_audit.pre_reads import CL_NULL_FRACTION, existence_verdict, shuffle_null

    row_seed, doc_seed = (master_seed, "shuffle", ROW_NULL_SEED), (master_seed, "shuffle", DOC_NULL_SEED, spec.slug)
    ref = shuffle_null(counts_a, counts_b, n_shuffles=n_shuffles, master_seed=master_seed)
    combos = [("rows", "rows", "-")] if only_rows_rows else [(f, s, v) for f in ("documents", "rows") for s, v in (("rows", "-"), ("documents", "a"), ("documents", "b"))]

    def run(n: int) -> list[dict[str, Any]]:
        out = []
        for floor, shuffle, variant in combos:
            t = s9_null(counts_a, counts_b, docs_a, docs_b, shuffle=shuffle, floor=floor, variant="a" if variant == "-" else variant, n_shuffles=n, seed_tuple=row_seed if shuffle == "rows" else doc_seed)
            if (floor, shuffle) == ("rows", "rows") and n == n_shuffles:
                cols = ["shuffle", "n_members", "mass", "total_mass", "share"]
                assert t[cols].equals(ref[cols]), f"{spec.name}: s9_null at (rows, rows) is not pre_reads.shuffle_null bit for bit"
            obs, nm = t[t["shuffle"] == -1].iloc[0], t[t["shuffle"] >= 0]
            mass, share, p95 = float(obs["mass"]), float(obs["share"]), float(np.percentile(nm["mass"].to_numpy(np.float64), 95))
            out.append({"pair": spec.name, "slug": spec.slug, "pool_a": f"{spec.a[0]}[{spec.a[1]}:{spec.a[2]}]", "pool_b": f"{spec.b[0]}[{spec.b[1]}:{spec.b[2]}]", "rows_a": int(counts_a.shape[0]), "rows_b": int(counts_b.shape[0]),
                        "documents_a": int(np.unique(docs_a).size), "documents_b": int(np.unique(docs_b).size), "floor_counts": floor, "primary_floor": floor == "documents", "null_shuffles": shuffle, "null_variant": variant,
                        "n_shuffles": n, "n_members": int(obs["n_members"]), "firing_mass_F": mass, "total_mass": float(obs["total_mass"]), "share": share, "null_mean": float(nm["mass"].mean()), "null_p95": p95,
                        "null_max": float(nm["mass"].max()), "null_mean_members": float(nm["n_members"].mean()), "null_mean_rows_pseudo_a": float(nm["n_rows_pseudo_a"].mean()), "null_mean_documents_pseudo_a": float(nm["n_documents_pseudo_a"].mean()),
                        "bar_a_fifth_of_F": CL_NULL_FRACTION * mass, "within_factor_two_of_bar": needs_rerun(p95, mass), "word_under_this_null": existence_verdict(share, mass, p95)})
        return out

    rows = run(n_shuffles)
    rerun = any(r["within_factor_two_of_bar"] for r in rows if r["null_shuffles"] == "documents")
    if rerun and n_shuffles < N_SHUFFLES_RERUN:
        log(f"[s9 check b] {spec.name}: a document null's 95th percentile is within a factor of two of the bar; rerun with {N_SHUFFLES_RERUN} shuffles")
        for r in rows:
            r["superseded_by_rerun"] = True
        rows += run(N_SHUFFLES_RERUN)
    for r in rows:
        r.setdefault("superseded_by_rerun", False)
    final = [r for r in rows if not r["superseded_by_rerun"]]
    for floor in {r["floor_counts"] for r in rows}:
        words = {r["null_variant"]: r["word_under_this_null"] for r in final if r["floor_counts"] == floor and r["null_shuffles"] == "documents"}
        verdict = combine_variants(words["a"], words["b"]) if words else None
        for r in rows:
            if r["floor_counts"] == floor:
                r["verdict_for_floor"] = verdict
                r["document_null_words_a_b"] = f"{words['a']} / {words['b']}" if words else None
    return rows


def check_b_reading(table: pd.DataFrame) -> dict[str, Any]:
    """The reading fixed before the run: if Wikipedia against Pile-CC reads clear in either direction under the document floor, "source-leaning",
    with code as one instance; if none or marginal in both directions, "code-leaning" stands."""
    t = table[(table["floor_counts"] == "documents") & (~table["superseded_by_rerun"]) & (table["slug"].isin(["wikipedia_vs_pile_cc", "pile_cc_vs_wikipedia"]))]
    words = {s: str(g["verdict_for_floor"].iloc[0]) for s, g in t.groupby("slug")}
    assert set(words) == {"wikipedia_vs_pile_cc", "pile_cc_vs_wikipedia"}, words
    return {"words": words, "reading": "source-leaning" if "clear" in words.values() else "code-leaning stands"}


# ----------------------------------------------------------------------------- the cache half: check (b) and the label-only half of check (c)


@dataclass
class S9Inputs:
    run: str  # a cache is named <set>_<run>, as pre_reads.run_pre_reads_s7 names it
    set_map: dict[str, str]
    pool_map: dict[str, str]
    pairs: tuple[PairSpec, ...]
    regression: PairSpec | None
    strata_file: str = "E_lab.strata.json"
    synthetic_document_rows: int | None = None  # the stand-in only: its pools are filtered rows, so documents are blocks of this many rows
    draws: int = 8
    master_seed: int = 0
    extra: dict[str, Any] = field(default_factory=dict)


def paper_inputs(run: str = "main") -> S9Inputs:
    return S9Inputs(run=run, set_map={"E": "E", "E_lab": "E_lab"}, pool_map={p: p for p in ("D_unif", "D_code", "D_prose")}, pairs=PAIRS_MAIN, regression=REGRESSION_MAIN)


def dry_inputs(draws: int = 2) -> S9Inputs:
    """The stand-in (SimpleStories, the dry sets and caches): exercises the code paths and carries no meaning."""
    pairs = (PairSpec("narration against dialogue (stand-in)", "dry_narration_vs_dialogue", ("D_prose", 0, 32), ("D_code", 0, 32)), PairSpec("dialogue against narration (stand-in)", "dry_dialogue_vs_narration", ("D_code", 0, 32), ("D_prose", 0, 32)))
    return S9Inputs(run="simplestories", set_map={"E": "E_dry", "E_lab": "E_lab_dry"}, pool_map={"D_unif": "D_unif_dry", "D_code": "D_code_dry", "D_prose": "D_prose_dry"}, pairs=pairs, regression=None,
                    strata_file="E_lab_dry.strata.json", synthetic_document_rows=4, draws=draws)


def load_cache_checked(inp: S9Inputs, key: str) -> tuple[Any, dict[str, Any]]:
    """A label cache with its record, the set it was built on asserted to be the saved set (by ids hash)."""
    from vpd_audit.data import load_set
    from vpd_audit.donors import donors_dir
    from vpd_audit.sources import Cache

    set_name = {**inp.set_map, **inp.pool_map}[key]
    name = f"{set_name}_{inp.run}"
    with open(donors_dir() / f"{name}.json") as f:
        meta = json.load(f)
    _, _, record = load_set(set_name)
    assert meta.get("set_hash") in (None, record["sha256_ids"]), f"cache {name}: built on a set with another ids hash than the saved {set_name}"
    return Cache.load(name), {"name": name, "set_name": set_name, "set_hash": meta.get("set_hash"), "n_sequences": int(meta["n_sequences"]), "nnz": int(meta["nnz"]), "sha256": meta["sha256"]}


def inputs_document_index(inp: S9Inputs) -> pd.DataFrame:
    """The document index where the caches live: `document_index` on the paper's sets; blocks of rows on the stand-in."""
    from vpd_audit.data import load_set

    if inp.synthetic_document_rows is None:
        return document_index(DOC_SETS)
    rows = []
    for key in ("E_lab", "D_code", "D_prose"):
        name = {**inp.set_map, **inp.pool_map}[key]
        ids, _, record = load_set(name)
        src = [str(s) for s in record["strata"]] if "strata" in record else [key] * ids.shape[0]
        for i in range(ids.shape[0]):
            rows.append({"set": key, "row": i, "source": src[i], "majority_document": i // inp.synthetic_document_rows, "first_token_document": i // inp.synthetic_document_rows, "n_end_of_text": 0})
    return pd.DataFrame(rows)


def leaning_groups_full(code: Any, prose: Any, alive_vec: np.ndarray, master_seed: int = 0) -> dict[str, Any]:
    """The code-leaning group G_0.9 and the prose-leaning group (s <= 0.10), both from code_leaning.py on the whole pools with
    its own floor, as (n_sub,) booleans; and the per-row counts over the alive set that check (b) slices."""
    from vpd_audit.code_leaning import CL_GROUP, code_leaning_sets, leaning_group

    sets = code_leaning_sets(code, prose, alive_vec, master_seed=master_seed)
    G, P = np.zeros(code.n_sub, dtype=np.bool_), np.zeros(code.n_sub, dtype=np.bool_)
    G[sets.alive_idx[sets.group]] = True
    P[sets.alive_idx[leaning_group(sets.toward_prose, CL_GROUP)]] = True
    assert not (G & P).any()
    return {"sets": sets, "G": G, "P": P}


def named_sets_table(inp: S9Inputs, d_unif: Any, alive_vec: np.ndarray, alive_sha: str, G: np.ndarray, P: np.ndarray, rungs: tuple[str, ...] = ("1", "2")) -> pd.DataFrame:
    """The label-only half of check (c): per rung (one and eight donor tokens) and draw, the named set of curve 1 and its matched
    (marginal) set, both built by `cells.build_sources` as the launches built them, with n_on, the donor positions, the hashes,
    and the shares of each set inside G_0.9 and inside the prose-leaning group."""
    from vpd_audit.cells import TAU_PRIMARY, TIER_4, Cell, build_sources
    from vpd_audit.sources import RUNG_SCHEDULE, donor_set

    cells = [Cell(inp.run, "union", "E", "D_unif", TAU_PRIMARY, "r0", "excluded", k, r, ctl, TIER_4 if ctl == "marginal" else 1) for r in rungs for k in range(inp.draws) for ctl in ("none", "marginal")]
    built = build_sources(cells, {f"D_unif_{inp.run}": d_unif}, {inp.run: (alive_vec, alive_sha)}, None, None, dict(d_unif.module_to_c), master_seed=inp.master_seed, log=lambda *_: None)
    by = {(c.rung, c.draw, c.control): c for c in cells}
    rows = []
    for r in rungs:
        for k in range(inp.draws):
            named, matched = built[by[(r, k, "none")].name], built[by[(r, k, "marginal")].name]
            ds = donor_set("D_unif", d_unif.n_sequences, k, r, inp.master_seed)
            n, m = int(named.rho.sum()), int(matched.rho.sum())
            assert n == m == named.record["n_on"]["total"] and matched.record["matched_source_sha256"] == named.record["source_sha256"]
            rows.append({"rung": r, "donor_tokens": int(RUNG_SCHEDULE[r][1]), "draw": k, "cell": by[(r, k, "none")].name, "matched_cell": by[(r, k, "marginal")].name, "n_on": n,
                         "donor_positions": ";".join(str(p) for p in ds.positions), "donor_rows": ";".join(str(p // SEQ_LEN) for p in ds.positions),
                         "source_sha256": named.record["source_sha256"], "matched_source_sha256": matched.record["source_sha256"], "n_code_leaning_group": int(G.sum()), "n_prose_leaning_group": int(P.sum()),
                         "share_named_in_code_leaning": float((named.rho & G).sum() / n) if n else float("nan"), "share_named_in_prose_leaning": float((named.rho & P).sum() / n) if n else float("nan"),
                         "share_matched_in_code_leaning": float((matched.rho & G).sum() / m) if m else float("nan"), "share_matched_in_prose_leaning": float((matched.rho & P).sum() / m) if m else float("nan")})
    return pd.DataFrame(rows)


def run_cache_half(run: str, out_dir: Path, *, inputs: S9Inputs | None = None, n_shuffles: int = 200, log: Any = print) -> dict[str, Any]:
    """Where the caches live: check (b)'s table and the label-only half of check (c), into a directory named s9, with a manifest."""
    from vpd_audit.donors import donors_dir
    from vpd_audit.results import code_commits
    from vpd_audit.sources import source_hash

    t0 = time.time()
    out_dir = Path(out_dir)
    assert out_dir.name == S9_DIR_NAME, f"the s9 checks write into a directory named {S9_DIR_NAME!r} only, not {out_dir}"
    inp = inputs or paper_inputs(run)
    out_dir.mkdir(parents=True, exist_ok=True)
    records: dict[str, Any] = {}
    code, records["D_code"] = load_cache_checked(inp, "D_code")
    prose, records["D_prose"] = load_cache_checked(inp, "D_prose")
    alive_vec = np.load(donors_dir() / f"alive_{inp.pool_map['D_unif']}_{inp.run}.npy")
    alive_sha = source_hash(alive_vec)
    index = inputs_document_index(inp)
    lg = leaning_groups_full(code, prose, alive_vec, inp.master_seed)
    sets = lg["sets"]
    log(f"[s9 cache half] {inp.run}: alive {int(alive_vec.sum())}; G_0.9 has {int(lg['G'].sum())} members, the prose-leaning group {int(lg['P'].sum())}; {time.time() - t0:.0f} s")
    counts = {"D_code": sets.c_code, "D_prose": sets.c_prose}  # per-row counts over the alive set, from code_leaning.per_document_counts at CL_TAU
    rows: list[dict[str, Any]] = []
    regression: dict[str, Any] | None = None
    specs = ([(inp.regression, True)] if inp.regression else []) + [(p, False) for p in inp.pairs]
    for spec, is_reg in specs:
        (pa, a0, a1), (pb, b0, b1) = spec.a, spec.b
        ca, cb = counts[pa][a0:a1], counts[pb][b0:b1]
        da, db = document_codes(index, pa, a0, a1), document_codes(index, pb, b0, b1)
        assert pa != pb or a1 <= b0 or b1 <= a0, f"{spec.name}: the two pools overlap"
        got = existence_pair(spec, ca, cb, da, db, master_seed=inp.master_seed, n_shuffles=n_shuffles, only_rows_rows=is_reg, log=log)
        for r in got:
            r["regression_pair"] = is_reg
        rows += got
        first = got[0]
        log(f"[s9 check b] {spec.name}: {first['documents_a']} against {first['documents_b']} documents; " + "; ".join(
            f"floor {r['floor_counts']}, null {r['null_shuffles']}{'' if r['null_variant'] == '-' else ' (' + r['null_variant'] + ')'}: {r['n_members']} members, share {r['share']:.4f}, p95 {r['null_p95']:.4g} -> {r['word_under_this_null']}"
            for r in got if not r["superseded_by_rerun"]) + f"; {time.time() - t0:.0f} s")
        if is_reg:
            r = got[0]
            regression = {"n_members": r["n_members"], "mass": r["firing_mass_F"], "share": r["share"], "null_p95": r["null_p95"], "word": r["word_under_this_null"], "expected": REGRESSION_EXPECTED,
                          "pass": bool(r["n_members"] == REGRESSION_EXPECTED["n_members"] and round(r["firing_mass_F"], 2) == REGRESSION_EXPECTED["mass_2dp"] and round(r["share"], 3) == REGRESSION_EXPECTED["share_3dp"])}
            assert regression["pass"], f"check (b)'s regression check fails: {regression}"
            assert r["n_members"] == sets.n_group, "the 512-against-512 group is code_leaning_sets' group"
            log(f"[s9 check b] regression check pass: {r['n_members']} members, mass {r['firing_mass_F']:.2f}, share {r['share']:.3f}")
    table = pd.DataFrame(rows)
    table.to_csv(out_dir / "check_b_existence_prose_vs_prose.csv", index=False)
    del code, prose
    d_unif, records["D_unif"] = load_cache_checked(inp, "D_unif")
    named = named_sets_table(inp, d_unif, alive_vec, alive_sha, lg["G"], lg["P"])
    named.to_csv(out_dir / "check_c_named_sets.csv", index=False)
    idx_counts = document_counts(index)
    manifest = {"run": inp.run, "commits": code_commits(), "seconds": time.time() - t0, "caches": records, "alive_sha256": alive_sha, "n_alive": int(alive_vec.sum()), "n_shuffles": n_shuffles,
                "n_shuffles_rerun": N_SHUFFLES_RERUN, "seeds": {"row_null": [inp.master_seed, "shuffle", ROW_NULL_SEED], "document_null": [inp.master_seed, "shuffle", DOC_NULL_SEED, "<pair slug>"]},
                "code_leaning_group": {"n_members": int(lg["G"].sum()), "sha256": source_hash(lg["G"])}, "prose_leaning_group": {"n_members": int(lg["P"].sum()), "sha256": source_hash(lg["P"])},
                "regression": regression, "synthetic_documents": inp.synthetic_document_rows, "document_counts": idx_counts.to_dict("records"),
                "document_index_sha256": hashlib.sha256(index.to_csv(index=False).encode()).hexdigest(), "files": ["check_b_existence_prose_vs_prose.csv", "check_c_named_sets.csv", "cache_half_manifest.json"]}
    with open(out_dir / "cache_half_manifest.json", "w") as f:
        json.dump(manifest, f, indent=2, sort_keys=True, default=str)
    log(f"[s9 cache half] done in {time.time() - t0:.0f} s -> {out_dir}")
    return {"run": inp.run, "seconds": time.time() - t0, "regression": regression, "n_rows_check_b": int(len(table)), "n_rows_named_sets": int(len(named)), "out_dir": str(out_dir)}


# ============================================================================= check (d)

X_TEXTS = (0.05, 0.1, 0.2)
X_POSITIONS = (0.05, 0.1, 0.2, 0.5, 1.0)
NEAR_X, NEAR_X_WIDTH = 0.05, 0.001
N_BLOCKS = 8
GATE_TOLERANCE = 5e-4
POSITION_RUNGS = ("1", "2", "2a", "2b", "3", "4")  # curve 1 at 1, 8, 16, 32, 64 tokens and one text
CONTROL_RUNGS = ("3", "4")  # its same-size random control at 64 tokens and one text
WORD_RUNG = "3"  # one number owns the word: S(0.05) on curve 1 at 64 tokens
MOST, FEW, BETWEEN = "on most positions", "on few positions", "between"
NEVER_NAMED_CELL = "{run}/E/never_named_hard/D_unif/tau0.1/ones/incl/k0/r8"
CODE_LEANING_CELL = "{run}/E_lab/code_leaning_hard/D_code/tau0.1/ones/incl/k0/rG256"


def is_curve_1(c: Any, control: str) -> bool:
    return bool(c.family == "union" and c.eval_set == "E" and c.donor_pool == "D_unif" and c.tau == 0.1 and c.background == "r0" and c.delta == "excluded" and c.control == control
                and c.donor_side_reference is None and c.level is None and c.replicate == 0)


def rung_size(rung: str) -> tuple[str, int | None]:
    """A rung's unit and size through RUNG_SCHEDULE, never by hand (5a is 2 texts and 6a is 8)."""
    from vpd_audit.sources import RUNG_SCHEDULE

    return RUNG_SCHEDULE[str(rung)]


def check_d_texts(grid: Any) -> tuple[pd.DataFrame, dict[str, Any]]:
    """Over texts: for curve 1 and its same-size random control at every stored size, the share of texts whose excess over the
    own-labels reference, averaged over the draws, exceeds 0.05, 0.1, 0.2, and the same share over (text, draw) pairs."""
    from vpd_audit.analysis import excess_matrix

    sd = grid.sets["E"]
    rows = []
    for control in ("none", "plain"):
        by: dict[str, list[Any]] = {}
        for c in sd.cell_objects.values():
            if is_curve_1(c, control):
                by.setdefault(c.rung, []).append(c)
        for r in st.sort_rungs(list(by)):
            cells = sorted(by[r], key=lambda x: x.draw)
            e = excess_matrix(sd, cells)
            unit, size = rung_size(r)
            row = {"curve": "curve 1" if control == "none" else "its same-size random control (ctl-plain)", "control": control, "rung": r, "unit": unit, "size": size, "n_draws": int(e.shape[0]), "n_texts": int(e.shape[1]),
                   "descriptive": bool(cells[0].descriptive), "mean_excess": float(e.mean())}
            for x in X_TEXTS:
                row[f"share_texts_draw_averaged_above_{x:g}"] = float((e.mean(axis=0) > x).mean())
                row[f"share_text_draw_pairs_above_{x:g}"] = float((e > x).mean())
            rows.append(row)
    table = pd.DataFrame(rows)
    return table, check_d_texts_regression(table, grid.root.parent / "analysis" / grid.run)


def check_d_texts_regression(table: pd.DataFrame, analysis_root: Path) -> dict[str, Any]:
    """At 0.05 the draw-averaged shares reproduce the committed fraction_seq_above_X column, exactly."""
    checks = []
    for control in ("none", "plain"):
        for suffix in ("", "__descriptive_rungs"):
            p = analysis_root / f"union_E_D_unif_tau0.1_r0_excl_ctl-{control}{suffix}.csv"
            if not p.is_file():
                continue
            t = pd.read_csv(p, dtype={"rung": str}, float_precision="round_trip")
            if "fraction_seq_above_X" not in t.columns:
                continue
            for _, r in t.iterrows():
                rung = str(r["rung"]).split(" ")[0]
                got = table[(table.control == control) & (table.rung == rung)]
                assert len(got) == 1, (control, rung)
                v = float(got.iloc[0]["share_texts_draw_averaged_above_0.05"])
                checks.append({"control": control, "rung": rung, "committed": float(r["fraction_seq_above_X"]), "computed": v, "equal": bool(v == float(r["fraction_seq_above_X"]))})
    named = {("none", "1"): 0.0, ("none", "2"): 0.255, ("none", "3"): 1.0, ("none", "2a"): 0.957, ("none", "2b"): 1.0}  # the five values fixed in advance
    registered = [{"control": k[0], "rung": k[1], "registered": v, "computed": next((c["computed"] for c in checks if (c["control"], c["rung"]) == k), None)} for k, v in named.items()]
    for p_ in registered:
        p_["equal_at_3dp"] = bool(p_["computed"] is not None and round(p_["computed"], 3) == p_["registered"])
    return {"n": len(checks), "n_unequal": int(sum(not c["equal"] for c in checks)), "registered_values": registered, "pass": bool(checks and all(c["equal"] for c in checks) and all(p_["equal_at_3dp"] for p_ in registered)), "checks": checks}


def _n_top(share: float, n: int) -> int:
    return max(1, int(np.floor(share * n + 1e-9)))


def carried_by_worst(values: np.ndarray, share: float) -> float:
    """The share of the total carried by the worst `share` of the units (the largest values); NaN where the total is not positive."""
    v = np.asarray(values, dtype=np.float64).reshape(-1)
    total = float(v.sum())
    if not total > 0:
        return float("nan")
    k = _n_top(share, v.size)
    return float(np.partition(v, v.size - k)[v.size - k:].sum() / total)


def smallest_share_carrying_half(values: np.ndarray) -> float:
    """q50: the smallest share of the units that carries half of the total; NaN where the total is not positive."""
    v = np.sort(np.asarray(values, dtype=np.float64).reshape(-1))[::-1]
    total = float(v.sum())
    if not total > 0:
        return float("nan")
    m = int(np.searchsorted(np.cumsum(v), total / 2.0, side="left")) + 1
    return float(m / v.size)


def position_statistics(delta: np.ndarray) -> dict[str, float]:
    """The position statistics on an array of rises whose last axis is the position and whose last-but-one is the text: S(x) and
    S^-(x) as means of per-text shares, the count near 0.05, C_10, C_1, q_50 over all units, and the worst tenth of texts."""
    d = np.asarray(delta, dtype=np.float64)
    out: dict[str, float] = {"n_units": float(d.size), "mean_rise": float(d.mean()), "total_rise": float(d.sum())}
    for x in X_POSITIONS:
        out[f"S_{x:g}"] = float((d > x).mean(axis=-1).mean())
        out[f"S_minus_{x:g}"] = float((d < -x).mean(axis=-1).mean())
    out["n_within_0.001_of_0.05"] = float((np.abs(d - NEAR_X) < NEAR_X_WIDTH).sum())
    out["C_10"], out["C_1"], out["q_50"] = carried_by_worst(d, 0.10), carried_by_worst(d, 0.01), smallest_share_carrying_half(d)
    out["worst_tenth_of_texts"] = carried_by_worst(d.sum(axis=-1), 0.10)
    return out


def range_over_draws(per_draw: list[dict[str, float]], key: str) -> tuple[float, float]:
    """The least and greatest per-draw value of a statistic, over the draws where it is defined (a draw whose total rise is not
    positive has no share of it); (NaN, NaN) where no draw has one."""
    vals = [p[key] for p in per_draw if np.isfinite(p[key])]
    return (float(np.min(vals)), float(np.max(vals))) if vals else (float("nan"), float("nan"))


def positions_word(interval: list[float]) -> str:
    """The word fixed before the run for S(0.05) on curve 1 at 64 tokens: on most positions if the interval's lower end is at least 0.50; on few
    positions if its upper end is at most 0.10; between otherwise."""
    lo, hi = interval
    if lo >= 0.50:
        return MOST
    if hi <= 0.10:
        return FEW
    return BETWEEN


def kl_path(store_dir: Path, cell: str) -> Path:
    return Path(store_dir) / "kl" / f"{cell.replace('/', '__')}.npy"


def _store_of(sd: Any, cell: str, prefer: str | None = None) -> Any:
    holders = [s for s in sd.stores if (s.cells["cell"] == cell).any()]
    assert holders, f"no store holds {cell}"
    if prefer:
        for s in holders:
            if s.name == prefer:
                return s
    return holders[0]


def needed_arrays(grid: Any) -> list[dict[str, Any]]:
    """The cells of the position statistics with the store that holds each, from the loaded grid: curve 1 at rungs 1, 2, 2a, 2b, 3, 4 (every
    draw), its plain control at rungs 3 and 4, the own-labels reference on E, the never-named removal at its whole-set rung
    (residual included) and the code-leaning edit at 256 members, each with its stored reference."""
    from vpd_audit.analysis import ref_cell_name

    out: list[dict[str, Any]] = []
    sd_e, sd_l = grid.sets["E"], grid.sets["E_lab"]

    def add(sd: Any, cell: str, group: str, prefer: str | None = None) -> None:
        s = _store_of(sd, cell, prefer)
        out.append({"group": group, "cell": cell, "store": s.name, "path": kl_path(s.dir, cell), "remote": f"/results/grid/{grid.run}/{s.name}/kl/{cell.replace('/', '__')}.npy", "eval_set": sd.eval_set})

    curve = sorted((c for c in sd_e.cell_objects.values() if is_curve_1(c, "none") and c.rung in POSITION_RUNGS), key=lambda c: (st.donor_count_order(c.rung), c.draw))
    ctl = sorted((c for c in sd_e.cell_objects.values() if is_curve_1(c, "plain") and c.rung in CONTROL_RUNGS), key=lambda c: (st.donor_count_order(c.rung), c.draw))
    for c in curve:
        add(sd_e, c.name, f"curve 1|{c.rung}")
    for c in ctl:
        add(sd_e, c.name, f"control|{c.rung}")
    ref = ref_cell_name(curve[0])
    assert all(ref_cell_name(c) == ref for c in curve + ctl)
    add(sd_e, ref, "reference|own labels", prefer=_store_of(sd_e, curve[0].name).name)
    nn = NEVER_NAMED_CELL.format(run=grid.run)
    add(sd_e, nn, "never-named|8")
    add(sd_e, ref_cell_name(sd_e.cell_objects[nn]), "reference|never-named", prefer=_store_of(sd_e, nn).name)
    cl = CODE_LEANING_CELL.format(run=grid.run)
    add(sd_l, cl, "code-leaning|G256")
    add(sd_l, ref_cell_name(sd_l.cell_objects[cl]), "reference|code-leaning", prefer=_store_of(sd_l, cl).name)
    return out


def _modal(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run(["modal", *args], capture_output=True, text=True)


def confirm_on_volume(needed: list[dict[str, Any]], log: Any = print) -> list[str]:
    """The first step of the position statistics: every array not already local must be on the volume. Returns the missing ones."""
    missing: list[str] = []
    remote = [n for n in needed if not n["path"].is_file()]
    for d in sorted({str(Path(n["remote"]).parent) for n in remote}):
        res = _modal("volume", "ls", VOLUME_NAME, d)
        assert res.returncode == 0, f"modal volume ls {d} failed: {res.stderr[-500:]}"
        have = {Path(line.strip()).name for line in res.stdout.splitlines() if line.strip().endswith(".npy")}
        missing += [n["remote"] for n in remote if str(Path(n["remote"]).parent) == d and Path(n["remote"]).name not in have]
        log(f"[s9 pull] {d}: {len(have)} arrays on the volume")
    return missing


def pull_arrays(needed: list[dict[str, Any]], log: Any = print) -> dict[str, Any]:
    """Confirm, then pull each absent array with the documented `modal volume get` into its store's git-ignored kl/ folder."""
    missing = confirm_on_volume(needed, log)
    if missing:
        raise RuntimeError("arrays missing from the volume (nothing was pulled):\n" + "\n".join(missing))
    pulled = 0
    for n in needed:
        if n["path"].is_file():
            continue
        n["path"].parent.mkdir(parents=True, exist_ok=True)
        res = _modal("volume", "get", VOLUME_NAME, n["remote"], str(n["path"]))
        assert res.returncode == 0 and n["path"].is_file(), f"modal volume get {n['remote']} failed: {res.stderr[-500:]}"
        pulled += 1
    log(f"[s9 pull] {pulled} arrays pulled, {len(needed) - pulled} already local")
    return {"pulled": pulled, "already_local": len(needed) - pulled}


def load_array_gated(sd: Any, item: dict[str, Any]) -> tuple[np.ndarray, dict[str, Any]]:
    """One (N, T) float16 array in float64, with its manifest row and the gate: the per-text mean over positions, taken in float64,
    matches the committed float32 kl_mean of that text within 5e-4."""
    p = item["path"]
    assert p.is_file(), f"{p} is absent: run `uv run vpd-audit s9-checks --pull`"
    raw = np.load(p)
    assert raw.dtype == np.float16 and raw.shape == (sd.n_sequences, SEQ_LEN), (p, raw.dtype, raw.shape)
    a = raw.astype(np.float64)
    assert np.isfinite(a).all(), f"{p}: a non-finite divergence"
    diff = float(np.abs(a.mean(axis=1) - sd.vector(item["cell"], "kl_mean").astype(np.float64)).max())
    tracked = subprocess.run(["git", "-C", str(env.PROJECT_ROOT), "ls-files", "--error-unmatch", str(p)], capture_output=True).returncode == 0
    rec = {"group": item["group"], "cell": item["cell"], "file": str(p.resolve().relative_to(env.PROJECT_ROOT)), "volume_path": item["remote"], "committed_in_git": tracked, "bytes": int(p.stat().st_size),
           "sha256": hashlib.sha256(p.read_bytes()).hexdigest(), "shape": "x".join(str(s) for s in raw.shape), "dtype": str(raw.dtype), "gate_max_abs_difference": diff, "gate_pass": bool(diff <= GATE_TOLERANCE)}
    return a, rec


def check_d_positions(grid: Any, strata: dict[str, Any], resamples: dict, *, replicates: int = REPLICATES, master_seed: int = 0, log: Any = print) -> dict[str, Any]:
    """The position statistics from the pulled arrays; `strata` is `analysis.load_strata(grid)`, for the code-leaning edit's two halves."""
    from vpd_audit.analysis import _resample_for

    needed = needed_arrays(grid)
    sd_e, sd_l = grid.sets["E"], grid.sets["E_lab"]
    manifest, arrays = [], {}
    for item in needed:
        arrays[item["cell"]], rec = load_array_gated(sd_e if item["eval_set"] == "E" else sd_l, item)
        manifest.append(rec)
    manifest_t = pd.DataFrame(manifest)
    gate = {"n_cells": int(len(manifest_t)), "max_abs_difference": float(manifest_t["gate_max_abs_difference"].max()), "tolerance": GATE_TOLERANCE, "pass": bool(manifest_t["gate_pass"].all())}
    if not gate["pass"]:
        raise AssertionError(f"check (d)'s gate fails: {manifest_t[~manifest_t['gate_pass']][['cell', 'gate_max_abs_difference']].to_dict('records')}")
    by_group: dict[str, list[str]] = {}
    for item in needed:
        by_group.setdefault(item["group"], []).append(item["cell"])
    ref_of = {"curve 1": by_group["reference|own labels"][0], "control": by_group["reference|own labels"][0], "never-named": by_group["reference|never-named"][0], "code-leaning": by_group["reference|code-leaning"][0]}
    rows, blocks = [], []
    word: dict[str, Any] = {}

    def emit(label: str, family: str, rung: str, unit: str, size: Any, delta: np.ndarray, baseline: str, subset: str = "all texts") -> None:
        K = delta.shape[0]
        per_draw = [position_statistics(delta[k]) for k in range(K)]
        for version, arr in (("per merge (draws not averaged)", delta), ("draw-averaged", delta.mean(axis=0, keepdims=True))):
            if version == "draw-averaged" and K == 1:
                continue
            s = position_statistics(arr)
            row = {"cells": label, "family": family, "rung": rung, "unit": unit, "size": size, "texts": subset, "baseline": baseline, "version": version, "n_draws": K, "n_texts": int(delta.shape[1]), **s}
            # the range over the draws, over the draws where the share is defined: a draw whose total rise is not positive has none, and is counted
            for key in ("C_10", "C_1", "q_50", "worst_tenth_of_texts"):
                row[f"{key}_min_over_draws"], row[f"{key}_max_over_draws"] = range_over_draws(per_draw if version.startswith("per merge") else [], key)
            row["n_draws_total_rise_not_positive"] = int(sum(not p["total_rise"] > 0 for p in per_draw)) if version.startswith("per merge") else 0
            rows.append(row)
        bm = delta.reshape(K, delta.shape[1], N_BLOCKS, SEQ_LEN // N_BLOCKS).mean(axis=(0, 1, 3))
        for j in range(N_BLOCKS):
            blocks.append({"cells": label, "family": family, "rung": rung, "unit": unit, "size": size, "texts": subset, "block": j, "first_position": j * (SEQ_LEN // N_BLOCKS), "last_position": (j + 1) * (SEQ_LEN // N_BLOCKS) - 1, "mean_rise": float(bm[j])})

    for fam, rungs, label in (("curve 1", POSITION_RUNGS, "curve 1"), ("control", CONTROL_RUNGS, "its same-size random control (ctl-plain)")):
        for r in rungs:
            cells = by_group[f"{fam}|{r}"]
            delta = np.stack([arrays[c] for c in cells]) - arrays[ref_of[fam]][None]
            unit, size = rung_size(r)
            emit(label, fam, r, unit, size, delta, "the own-labels reference (importances)")
            if fam == "curve 1" and r == WORD_RUNG:
                per_text = (delta > X_POSITIONS[0]).mean(axis=2).mean(axis=0)  # draws held fixed: per text, the mean over the draws of its share of positions
                rs = _resample_for(grid, "E", None, replicates, master_seed, resamples)
                lo, hi = st.percentile_interval(rs.means(per_text), 1)
                word = {"statistic": "S(0.05) on curve 1 at 64 tokens", "value": float(per_text.mean()), "interval_95": [lo, hi], "replicates": replicates, "bootstrap": "texts of E (the grid's own resample), draws held fixed", "word": positions_word([lo, hi]),
                        "per_draw": [float((delta[k] > X_POSITIONS[0]).mean()) for k in range(delta.shape[0])]}
    nn = by_group["never-named|8"][0]
    emit("the never-named removal at its whole-set rung (residual included)", "never-named", "8", "set", int(sd_e.cells.loc[nn, "n_on"]), (arrays[nn] - arrays[ref_of["never-named"]])[None], "the full model (unmasked_delta)")
    cl = by_group["code-leaning|G256"][0]
    d_cl = (arrays[cl] - arrays[ref_of["code-leaning"]])[None]
    strata_l = strata["E_lab"]
    for subset, mask in (("the GitHub half", strata_l["groups"][strata_l["positive"]]), ("the other half", strata_l["groups"]["other"])):
        emit("the code-leaning edit at 256 members", "code-leaning", "G256", "members", 256, d_cl[:, mask], "the full model (unmasked_delta)", subset)
    assert word, "curve 1 at 64 tokens was not among the cells"
    log(f"[s9 check d] gate pass on {gate['n_cells']} cells (max {gate['max_abs_difference']:.2e}); S(0.05) at 64 tokens {word['value']:.4f} {word['interval_95']} -> {word['word']}")
    return {"positions": pd.DataFrame(rows), "by_block": pd.DataFrame(blocks), "manifest": manifest_t, "gate": gate, "word": word}


# ============================================================================= check (c), the local half

SPEARMAN_BAR = 0.74
SUGGESTIVE, NOT_SEEN = "suggestive", "not seen"
NOT_SEEN_SENTENCE = ("*Not seen* carries no weight in the post: with eight draws a true correlation of 0.6 gives 0.3 or less about one time in five, so a null here is not evidence of absence, and the tier-5 same-domain merge "
                     "tests the same rival on far more data.")


def check_c_reading(rho_share: float, rho_count: float, bar: float = SPEARMAN_BAR) -> str:
    """Suggestive of a domain block if the Spearman correlation of the named set's code-leaning share with U - M is at least 0.74
    and exceeds the correlation of the same U - M with n_on; otherwise not seen."""
    if not (np.isfinite(rho_share) and np.isfinite(rho_count)):
        return NOT_SEEN
    return SUGGESTIVE if (rho_share >= bar and rho_share > rho_count) else NOT_SEEN


def check_c(grid: Any, named: pd.DataFrame, labels_path: Path, log: Any = print) -> dict[str, Any]:
    """Per rung (one and eight tokens) and draw: the label-only columns of the cache half, asserted by hash and count against the
    committed cell tables; the draw's donor positions in texts the readers labelled code; and U - M on the code and the prose
    texts of E from the committed tier-1 union store and the tier-4 marginal store."""
    from vpd_audit.analysis import excess_matrix
    from vpd_audit.pre_reads import spearman

    sd = grid.sets["E"]
    lab = pd.read_csv(labels_path, sep="\t")
    e_lab = lab[lab["set"] == "E"].sort_values("seq")["label"].to_numpy()
    d_lab = lab[lab["set"] == "D_unif"].sort_values("seq")["label"].to_numpy()
    assert e_lab.size == sd.n_sequences and d_lab.size > 0
    rows, asserted = [], 0
    for _, r in named.iterrows():
        cu, cm = sd.cell_objects[r["cell"]], sd.cell_objects[r["matched_cell"]]
        assert cm.control == "marginal" and cm.replicate == 0 and cu.control == "none"
        for cell, sha in ((r["cell"], r["source_sha256"]), (r["matched_cell"], r["matched_source_sha256"])):
            assert sd.cells.loc[cell, "source_sha256"] == sha and int(sd.cells.loc[cell, "n_on"]) == int(r["n_on"]), f"{cell}: the rebuilt set is not the one the committed store ran"
            asserted += 1
        diff = (excess_matrix(sd, [cu]) - excess_matrix(sd, [cm]))[0]
        donor_rows = [int(x) for x in str(r["donor_rows"]).split(";")]
        rows.append({**{k: r[k] for k in ("rung", "donor_tokens", "draw", "n_on", "share_named_in_code_leaning", "share_named_in_prose_leaning", "share_matched_in_code_leaning", "share_matched_in_prose_leaning")},
                     "n_donor_positions": len(donor_rows), "n_donor_positions_in_code_texts": int(sum(d_lab[x] == "code" for x in donor_rows)), "U_minus_M_code_texts": float(diff[e_lab == "code"].mean()),
                     "U_minus_M_prose_texts": float(diff[e_lab == "prose"].mean()), "U_minus_M_all_texts": float(diff.mean()), "n_code_texts": int((e_lab == "code").sum()), "n_prose_texts": int((e_lab == "prose").sum())})
    table = pd.DataFrame(rows)
    t8 = table[table["donor_tokens"] == 8].sort_values("draw")
    assert len(t8) >= 3, "eight donor tokens: too few draws for a rank correlation"
    rho_share = spearman(t8["share_named_in_code_leaning"].to_numpy(np.float64), t8["U_minus_M_prose_texts"].to_numpy(np.float64))
    rho_count = spearman(t8["n_on"].to_numpy(np.float64), t8["U_minus_M_prose_texts"].to_numpy(np.float64))
    out = {"table": table, "n_sets_asserted": asserted, "spearman_share_vs_U_minus_M_prose": rho_share, "spearman_n_on_vs_U_minus_M_prose": rho_count, "bar": SPEARMAN_BAR, "n_draws": int(len(t8)),
           "reading": check_c_reading(rho_share, rho_count), "sentence": NOT_SEEN_SENTENCE,
           "spearman_matched_share_vs_U_minus_M_prose": spearman(t8["share_matched_in_code_leaning"].to_numpy(np.float64), t8["U_minus_M_prose_texts"].to_numpy(np.float64))}
    log(f"[s9 check c] {asserted} sets equal the committed stores' by hash; at eight tokens on prose texts: Spearman(share, U - M) = {rho_share:+.3f}, Spearman(n_on, U - M) = {rho_count:+.3f} -> {out['reading']}")
    return out


# ============================================================================= the local command


def _pulled(out_dir: Path, name: str) -> Path:
    p = out_dir / name
    assert p.is_file(), f"{p} is absent: run the cache half on Modal (modal_app.py::s9_label_tables) and pull /results/grid/analysis/<run>/s9/ from the volume"
    return p


def check_b_local(out_dir: Path, index: pd.DataFrame, s7_dir: Path) -> dict[str, Any]:
    """The pulled check (b) table against what is committed and local: the regression row against the committed code-leaning
    pre-reads' summary.json (`s7_dir`), exactly; the document counts the cache half saw against the local document index; then the reading."""
    table = pd.read_csv(_pulled(out_dir, "check_b_existence_prose_vs_prose.csv"), float_precision="round_trip")
    with open(_pulled(out_dir, "cache_half_manifest.json")) as f:
        manifest = json.load(f)
    with open(s7_dir / "summary.json") as f:
        ex = json.load(f)["code_leaning"]["existence"]
    reg = table[table["regression_pair"]]
    assert len(reg) == 1
    reg = reg.iloc[0]
    regression = {"n_members": int(reg.n_members), "mass": float(reg.firing_mass_F), "share": float(reg.share), "null_p95": float(reg.null_p95), "word": str(reg.word_under_this_null), "committed": {k: ex[k] for k in ("n_members", "mass", "share", "null_p95", "verdict")},
                  "pass": bool(int(reg.n_members) == ex["n_members"] and float(reg.firing_mass_F) == ex["mass"] and float(reg.share) == ex["share"] and float(reg.null_p95) == ex["null_p95"] and str(reg.word_under_this_null) == ex["verdict"]
                               and int(reg.n_members) == REGRESSION_EXPECTED["n_members"] and round(float(reg.firing_mass_F), 2) == REGRESSION_EXPECTED["mass_2dp"] and round(float(reg.share), 3) == REGRESSION_EXPECTED["share_3dp"])}
    same_index = bool(manifest["document_index_sha256"] == hashlib.sha256(index.to_csv(index=False).encode()).hexdigest())
    return {"table": table, "regression": regression, "document_index_equal_to_the_cache_halfs": same_index, "reading": check_b_reading(table[~table["regression_pair"]]), "manifest": manifest}


def run_s9_checks(run: str = "main", *, frozen: str | None = None, out_dir: Path | None = None, replicates: int = REPLICATES, master_seed: int = 0, log: Any = print) -> dict[str, Any]:
    """The document index, checks (a) and (d), the local halves of checks (b) and (c), and the report. Any failed regression check or gate stops the command."""
    from vpd_audit.analysis import load_grid, load_strata
    from vpd_audit.data import load_set
    from vpd_audit.results import code_commits

    t0 = time.time()
    out = Path(out_dir) if out_dir else analysis_dir(run)
    out.mkdir(parents=True, exist_ok=True)
    results = env.PROJECT_ROOT / "results"
    checks: list[dict[str, Any]] = []

    def record(name: str, ok: bool, detail: str) -> None:
        checks.append({"check": name, "pass": bool(ok), "detail": detail})
        log(f"[s9 checks] {'pass' if ok else 'FAIL'}: {name} ({detail})")
        if not ok:
            raise AssertionError(f"regression check failed: {name} ({detail})")

    blobs = frozen_blobs("main")
    record("the frozen modules are main's blobs, on disk and at HEAD", blobs["pass"], f"{sum(r['equal'] for r in blobs['modules'])} of {len(blobs['modules'])} equal; main at {blobs['against_commit'][:12]}, HEAD {blobs['head'][:12]}; "
           f"recorded, not asserted: {sum(r['unchanged_since'] for r in blobs['recorded'])} of {len(blobs['recorded'])} harness modules unchanged since {blobs['recorded_at']}")
    # ---- the document index
    index = document_index(DOC_SETS)
    counts = document_counts(index)
    index.to_csv(out / "document_index.csv", index=False)
    counts.to_csv(out / "document_counts.csv", index=False)
    e_lab_ids, d_code_ids = load_set("E_lab")[0], load_set("D_code")[0]
    gh = index[(index["set"] == "E_lab") & (index["source"] == "Github")]["row"].to_numpy()
    dup_share, dup_pairs = near_duplicate_screen(e_lab_ids[gh], d_code_ids)
    dup_pairs = dup_pairs.rename(columns={"a_row": "e_lab_row", "b_row": "d_code_row", "first_offset_a": "first_offset_e_lab", "first_offset_b": "first_offset_d_code"})
    dup_pairs["e_lab_row"] = gh[dup_pairs["e_lab_row"].to_numpy(np.int64)] if len(dup_pairs) else dup_pairs["e_lab_row"]
    dup_pairs.to_csv(out / "near_duplicate_pairs.csv", index=False)
    log(f"[s9 document index] {len(index)} rows indexed; near-duplicate screen: {dup_share:.4f} of E_lab's {gh.size} GitHub rows share a {NEAR_DUP_WINDOW}-token window with D_code ({len(dup_pairs)} pairs)")
    # ---- the grid (the paper's stores: --frozen equal to HEAD on a clean tree)
    grid = load_grid(results / "grid" / run, frozen=frozen, only_sets=("E", "E_lab"))
    strata = load_strata(grid)
    resamples: dict = {}
    # ---- check (a)
    a = check_a(grid, strata, index, resamples, replicates=replicates, master_seed=master_seed, log=log)
    a["table"].to_csv(out / "check_a_removed_label_by_source.csv", index=False)
    record("check (a): the by-source damages reproduce s7_code_leaning_damage_by_source.csv exactly", a["regression"]["pass"],
           f"{a['regression']['n_by_source']} by-source values and {a['regression']['n_github']} GitHub values, {a['regression']['n_unequal']} unequal, {a['regression']['n_interval_unequal']} printed intervals unequal")
    # ---- check (b), local half
    b = check_b_local(out, index, results / "grid" / "pre_reads" / run / "s7")
    record("check (b): 512 against 512 with the row floor reproduces the committed code-leaning group", b["regression"]["pass"], f"{b['regression']['n_members']} members, mass {b['regression']['mass']:.2f}, share {b['regression']['share']:.3f}, null p95 and word equal to the committed summary")
    record("check (b): the cache half's document index is the local one", b["document_index_equal_to_the_cache_halfs"], "SHA-256 of the index table")
    # ---- check (d)
    texts, texts_reg = check_d_texts(grid)
    texts.to_csv(out / "check_d_texts.csv", index=False)
    record("check (d): the draw-averaged shares at 0.05 reproduce fraction_seq_above_X", texts_reg["pass"], f"{texts_reg['n']} rungs compared, {texts_reg['n_unequal']} unequal; the five values fixed in advance, at three decimals: {all(p['equal_at_3dp'] for p in texts_reg['registered_values'])}")
    d = check_d_positions(grid, strata, resamples, replicates=replicates, master_seed=master_seed, log=log)
    d["positions"].to_csv(out / "check_d_positions.csv", index=False)
    d["by_block"].to_csv(out / "check_d_by_block.csv", index=False)
    d["manifest"].to_csv(out / "check_d_pull_manifest.csv", index=False)
    record("check (d): the gate, per-position arrays against the committed kl_mean", d["gate"]["pass"], f"{d['gate']['n_cells']} cells, max difference {d['gate']['max_abs_difference']:.2e} against {GATE_TOLERANCE:g}")
    # ---- check (c), local half
    named = pd.read_csv(_pulled(out, "check_c_named_sets.csv"), dtype={"rung": str})
    c = check_c(grid, named, results / "data" / "reader_labels" / "labels_first_pass.tsv", log=log)
    c["table"].to_csv(out / "check_c_per_draw.csv", index=False)
    record("check (c): the rebuilt named and matched sets are the committed stores'", c["n_sets_asserted"] == 2 * len(named), f"{c['n_sets_asserted']} sets equal by source hash and n_on")
    ctx = {"run": run, "frozen": frozen, "commits": code_commits(), "blobs": blobs, "checks": checks, "counts": counts, "near_duplicates": {"share": dup_share, "n_pairs": int(len(dup_pairs)), "n_rows": int(gh.size), "pairs": dup_pairs},
           "a": a, "b": b, "texts": texts, "d": d, "c": c, "replicates": replicates}
    text = format_report(ctx)
    with open(out / "report.md", "w") as f:
        f.write(text + "\n")
    summary = {"run": run, "frozen": frozen, "commits": ctx["commits"], "replicates": replicates, "master_seed": master_seed, "frozen_modules": blobs, "regression_checks": checks,
               "documents": {"near_duplicate_share": dup_share, "near_duplicate_pairs": int(len(dup_pairs)), "document_counts": counts.to_dict("records")},
               "check_a": {"readings": a["readings"], "detail": a["detail"], "supported": a["supported"], "regression": {k: v for k, v in a["regression"].items() if k != "checks"}},
               "check_b": {"reading": b["reading"], "regression": b["regression"], "cache_half_commits": b["manifest"].get("commits")},
               "check_d": {"word": d["word"], "gate": d["gate"], "texts_regression": {k: v for k, v in texts_reg.items() if k != "checks"}},
               "check_c": {k: v for k, v in c.items() if k != "table"}}
    with open(out / "summary.json", "w") as f:
        json.dump(summary, f, indent=2, sort_keys=True, default=str)
    log(text)
    log(f"[s9 checks] {len(checks)} regression checks pass; done in {time.time() - t0:.0f} s -> {out}")
    return summary


def pull_command(run: str = "main", *, frozen: str | None = None, log: Any = print) -> dict[str, Any]:
    from vpd_audit.analysis import load_grid

    grid = load_grid(env.PROJECT_ROOT / "results" / "grid" / run, frozen=frozen, only_sets=("E", "E_lab"))
    return pull_arrays(needed_arrays(grid), log)


# ----------------------------------------------------------------------------- the report


def _f(x: Any, nd: int = 4) -> str:
    if x is None or (isinstance(x, float) and not np.isfinite(x)):
        return "n/a"
    return f"{x:.{nd}f}" if isinstance(x, (float, np.floating)) else str(x)


def _ivs(lo: Any, hi: Any, nd: int = 4) -> str:
    return "no interval" if lo is None or not (np.isfinite(lo) and np.isfinite(hi)) else f"[{lo:.{nd}f}, {hi:.{nd}f}]"


def merge_label(size: Any, unit: str) -> str:
    """A merge's size in words: donor tokens (RUNG_SCHEDULE's positions), donor texts (its sequences), or the members of an erased set."""
    word = {"position": "token", "sequence": "text", "set": "piece", "members": "member"}.get(str(unit), str(unit))
    return f"{int(size)} {word}{'' if int(size) == 1 else 's'}"


def _table(df: pd.DataFrame, cols: list[str], heads: list[str] | None = None, nd: int = 4) -> list[str]:
    heads = heads or cols
    L = ["| " + " | ".join(heads) + " |", "|" + "---|" * len(cols)]
    for _, r in df.iterrows():
        L.append("| " + " | ".join(_f(r[c], nd) if isinstance(r[c], (float, np.floating)) else str(r[c]) for c in cols) + " |")
    return L


def format_report(ctx: dict[str, Any]) -> str:
    a, b, d, c = ctx["a"], ctx["b"], ctx["d"], ctx["c"]
    L = [f"# The checks that need no GPU ({ctx['run']} run)", "",
         "Every reading rule below was fixed before any of these numbers existed.", "",
         "## The freeze guard and the regression checks", "",
         f"`--frozen {ctx['frozen']}` is HEAD, which by itself cannot fail; its content is the table below: each of the six frozen statistics and analysis modules is, on disk and at HEAD, the blob it is on `main` ({ctx['blobs']['against_commit'][:12]}).", ""]
    L += _table(pd.DataFrame(ctx["blobs"]["modules"]), ["module", "blob_on_disk", "blob_at_head", "blob_on_main", "equal"])
    if ctx["blobs"].get("recorded"):
        at = ctx["blobs"]["recorded_at"]
        L += ["", f"Recorded, not asserted: the five harness modules that later stages extended additively, against their blobs at `{at}`, the commit that produced the committed outputs. "
              "A rerun must reproduce every committed CSV byte for byte whether or not they have changed.", ""]
        L += _table(pd.DataFrame(ctx["blobs"]["recorded"]), ["module", "blob_on_disk", "blob_at_head", f"blob_at_{at}", "unchanged_since"])
    L += ["", "| regression check | result | detail |", "|---|---|---|"] + [f"| {k['check']} | {'pass' if k['pass'] else 'FAIL'} | {k['detail']} |" for k in ctx["checks"]]
    # ---- the document index
    nd_ = ctx["near_duplicates"]
    L += ["", "## The document index", "",
          "Documents are numbered per source block by the running count of end-of-text ids; a row's document is its majority document. `distinct_documents` counts majority documents, the unit of every document bootstrap and floor here; "
          "`documents_by_end_of_text_count` is the end-of-text count plus one (short documents never hold a row's majority). The saved rows are the first 512 of 513 tokens, so an end-of-text id at a row's unsaved 513th token is invisible; "
          "`expected_hidden_boundaries` is how many that is expected to be in each block.", ""]
    L += _table(ctx["counts"], ["set", "source", "rows", "distinct_documents", "documents_by_end_of_text_count", "rows_per_document_mean", "rows_per_document_max", "expected_hidden_boundaries"], nd=2)
    L += ["", f"**Near-duplicate screen (a description; no rule reads it).** {nd_['share']:.4f} of the {nd_['n_rows']} GitHub rows of E_lab share at least one exact {NEAR_DUP_WINDOW}-token window with a row of D_code "
          f"({nd_['n_pairs']} row pairs, listed in `near_duplicate_pairs.csv`)."]
    if nd_["n_pairs"]:
        L += [""] + _table(nd_["pairs"].head(20), list(nd_["pairs"].columns))
    # ---- check (a)
    L += ["", "## Check (a): whether the code-leaning group's labels are empty on prose", "",
          "Per chain size and source of E_lab: the mean removed label, the damage over whole texts (as `analysis_s7` computes it), the damage per unit of removed label (a ratio of means), and the group-to-twins ratio of that with a "
          f"95 percent interval that resamples documents within the source ({ctx['replicates']} replicates, uncorrected; none under ten documents). The guard: the ratio is read at a size only if the intervals of the group's removed label and of the twins' damage per unit both exclude zero.", ""]
    t = a["table"].copy()
    t["ratio interval"] = [_ivs(lo, hi, 3) for lo, hi in zip(t["ratio_lo"], t["ratio_hi"])]
    t["group's label interval"] = [_ivs(lo, hi, 5) for lo, hi in zip(t["omega_group_lo"], t["omega_group_hi"])]
    t["twins' per-unit interval"] = [_ivs(lo, hi, 4) for lo, hi in zip(t["H_per_omega_twins_lo"], t["H_per_omega_twins_hi"])]
    for col in ("omega_group", "omega_twins"):  # the group's removed label on prose is of order 1e-5 to 1e-3: five decimals, not four
        t[col] = [f"{x:.5f}" for x in t[col]]
    for col in ("n_contributing_group", "n_contributing_twins"):
        t[col] = [f"{x:.1f}" for x in t[col]]
    L += _table(t, ["n_members", "source", "n_texts", "n_documents", "omega_group", "omega_twins", "H_group", "H_twins", "H_per_omega_group", "H_per_omega_twins", "ratio_group_to_twins", "ratio interval", "group's label interval", "twins' per-unit interval",
                    "guard_both_exclude_zero", "clean_prefix_fraction_group", "clean_prefix_fraction_twins", "n_contributing_group", "n_contributing_twins"],
                ["members", "source", "texts", "documents", "group's removed label", "twins'", "H group", "H twins", "H per label, group", "H per label, twins", "ratio", "ratio interval", "group's label interval", "twins' per-unit interval", "guard",
                 "clean prefix, group", "clean prefix, twins", "contributing, group", "contributing, twins"])
    L += ["", f"**Reading (mark {CHECK_A_MARK:g}, at {CHECK_A_SIZES[0]} and {CHECK_A_SIZES[1]} members).**"]
    for sname, word in a["readings"].items():
        det = a["detail"][sname]
        L.append(f"- {sname}: **{word}**. " + "; ".join(f"at {n} members the ratio is {_f(v['ratio'], 3)} {_ivs(*(v['ratio_interval'] or (None, None)), nd=3)}, guard {'passes' if v['guard'] else 'fails'}" for n, v in det.items()) + f" ({det[CHECK_A_SIZES[0]]['n_documents']} documents).")
    L.append(f"- \"The labels fire on prose without effect\" is **{'supported' if a['supported'] else 'not supported'}** (supported only if the mark is met on both prose sources).")
    # ---- check (b)
    L += ["", "## Check (b): the existence rule run prose against prose", "",
          "The existence rule on matched pools of 256 rows. Two floors (usage at least 1e-3 in at least 8 distinct rows, or documents; the document floor is primary) and three nulls (the rule's row shuffle; a document shuffle, variant (a): the first D_A documents of a "
          "permutation of the pooled documents, primary; variant (b): documents until the row count is nearest 256). Verdict words come from the document nulls only; where (a) and (b) differ, both are printed and the pair is marginal.", ""]
    bt = b["table"][~b["table"]["superseded_by_rerun"]].copy()
    bt["null"] = [s if v == "-" else f"{s} ({v})" for s, v in zip(bt["null_shuffles"], bt["null_variant"])]
    L += _table(bt, ["pair", "documents_a", "documents_b", "floor_counts", "null", "n_shuffles", "n_members", "firing_mass_F", "share", "null_p95", "bar_a_fifth_of_F", "word_under_this_null", "verdict_for_floor"],
                ["pair (pool A against pool B)", "documents A", "documents B", "floor counts", "null shuffles", "shuffles", "members of G_0.9", "firing mass F", "share", "null p95", "bar (F / 5)", "word under this null", "verdict for the floor"])
    n_rerun = int(b["table"]["superseded_by_rerun"].sum())
    L += ["", f"Rows superseded by a rerun at {N_SHUFFLES_RERUN} shuffles (a document null's 95th percentile within a factor of two of the bar): {n_rerun}; they stay in the CSV.",
          "", f"**Reading.** Wikipedia against Pile-CC under the document floor: **{b['reading']['words']['wikipedia_vs_pile_cc']}**; Pile-CC against Wikipedia: **{b['reading']['words']['pile_cc_vs_wikipedia']}**. So: **{b['reading']['reading']}**."]
    # ---- check (d)
    L += ["", "## Check (d): where the merging harm falls", "", "### Texts (from the committed tables)", ""]
    tt = ctx["texts"].copy()
    tt["size"] = ["the pool" if not np.isfinite(s) else merge_label(s, u) for s, u in zip(tt["size"].astype(float), tt["unit"])]
    L += _table(tt, ["curve", "rung", "size", "n_draws", "mean_excess"] + [f"share_texts_draw_averaged_above_{x:g}" for x in X_TEXTS] + [f"share_text_draw_pairs_above_{x:g}" for x in X_TEXTS],
                ["cells", "rung", "size", "draws", "mean excess"] + [f"texts above {x:g} (draw-averaged)" for x in X_TEXTS] + [f"(text, draw) pairs above {x:g}" for x in X_TEXTS])
    L += ["", "### Positions (from the per-position arrays)", "",
          f"The unit is a position under one merge. The gate passed on {d['gate']['n_cells']} cells (largest difference {d['gate']['max_abs_difference']:.2e} against {GATE_TOLERANCE:g}); the arrays and their SHA-256 are in `check_d_pull_manifest.csv`. "
          "C_10, C_1, q_50 and the worst tenth of texts are pooled over all units, with the range over the draws.", ""]
    pt = d["positions"].copy()
    for key in ("C_10", "C_1", "q_50", "worst_tenth_of_texts"):
        pt[key + " (range)"] = [f"{_f(v, 3)} ({_f(lo, 3)} to {_f(hi, 3)})" if np.isfinite(lo) else _f(v, 3) for v, lo, hi in zip(pt[key], pt[f"{key}_min_over_draws"], pt[f"{key}_max_over_draws"])]
    pt["merge"] = [merge_label(s, u) for s, u in zip(pt["size"], pt["unit"])]
    pt["n_within_0.001_of_0.05"] = [str(int(x)) for x in pt["n_within_0.001_of_0.05"]]
    L += _table(pt, ["cells", "merge", "texts", "version", "mean_rise"] + [f"S_{x:g}" for x in X_POSITIONS] + [f"S_minus_{x:g}" for x in X_POSITIONS] + ["n_within_0.001_of_0.05", "C_10 (range)", "C_1 (range)", "q_50 (range)", "worst_tenth_of_texts (range)"],
                ["cells", "size", "texts", "version", "mean rise"] + [f"S({x:g})" for x in X_POSITIONS] + [f"S-({x:g})" for x in X_POSITIONS] + ["positions within 0.001 of 0.05", "C_10", "C_1", "q_50", "worst tenth of texts"])
    n_np = int(d["positions"]["n_draws_total_rise_not_positive"].sum())
    L += ["", f"A share of the total rise is a share of the *net* total, negative positions included (as in the worked example), so it exceeds 1 where falls cancel much of the rise, as at the small merges. "
          f"Draws whose own total rise is not positive have no such share and are left out of the ranges: {n_np} over all rows (`n_draws_total_rise_not_positive`).",
          "", "The mean rise by position in the text, eight blocks of 64 positions (`check_d_by_block.csv`):", ""]
    bb = d["by_block"].copy()
    bb["merge"] = [merge_label(s, u) for s, u in zip(bb["size"], bb["unit"])]
    bb = bb.pivot_table(index=["cells", "merge", "texts"], columns="block", values="mean_rise", sort=False).reset_index()
    bb.columns = [str(x) for x in bb.columns]
    L += _table(bb, list(bb.columns), ["cells", "size", "texts"] + [f"{j * 64} to {j * 64 + 63}" for j in range(N_BLOCKS)])
    w = d["word"]
    L += ["", f"**Reading.** S(0.05) on curve 1 at 64 tokens is {w['value']:.4f}, 95 percent interval {_ivs(*w['interval_95'])} over texts ({w['replicates']} replicates, draws held fixed): **{w['word']}**. "
          f"The eight draws one by one run from {min(w['per_draw']):.4f} to {max(w['per_draw']):.4f}, a spread the interval does not carry, since it holds the draws fixed. Concentration is reported as numbers and carries no word."]
    # ---- check (c)
    L += ["", "## Check (c): the donors' kind of text against the small-merge harm", ""]
    L += _table(c["table"], ["donor_tokens", "draw", "n_on", "n_donor_positions_in_code_texts", "share_named_in_code_leaning", "share_named_in_prose_leaning", "share_matched_in_code_leaning", "share_matched_in_prose_leaning", "U_minus_M_code_texts", "U_minus_M_prose_texts"],
                ["donor tokens", "draw", "n_on", "donor positions in code texts", "named set in G_0.9", "named set in the prose-leaning group", "matched set in G_0.9", "matched set in the prose-leaning group", "U - M, code texts", "U - M, prose texts"])
    L += ["", f"**Reading (eight tokens, prose texts, {c['n_draws']} draws).** Spearman of the named set's code-leaning share with U - M: {c['spearman_share_vs_U_minus_M_prose']:+.3f} (bar {SPEARMAN_BAR}); of n_on with the same U - M: {c['spearman_n_on_vs_U_minus_M_prose']:+.3f}. "
          f"A domain block is **{c['reading']}**. {NOT_SEEN_SENTENCE} The one-token table is a description and carries no reading."]
    return "\n".join(L)
