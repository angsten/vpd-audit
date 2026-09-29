"""Check (b)'s second pair, on random 200-row panels.

`s9_checks` ran the existence rule on matched pools of the labelled donor sets, whose rows are consecutive
windows of a few documents; its ArXiv rows were three papers, so ArXiv against Wikipedia was left for here. The panels
(`panel_ArXiv`, `panel_Wikipedia__en_`, `panel_Pile_CC`, `panel_StackExchange`, and a new `panel_Github`, the first 200 rows of
`calib_github`, which is already a seeded random draw) are random rows of each source's part C. Their label caches are built on
the GPU by the existing `eval_caches`; then, on CPU where the caches live, `s9_checks.existence_pair` is run unchanged on the pairs
at 200 rows against 200: ArXiv against Wikipedia, Wikipedia against Pile-CC, and code against each of the four, both directions.

The panels are random rows of a stream that was not saved, so the document index (`s9_checks.document_index`) does not exist for them: each row is its
own document (the document floor and the document nulls then count rows). Pairs of rows of one panel whose `row_indices` are close
enough to be one document are flagged: within the largest rows-per-document measured for the source (`PROXIMITY_ROWS`,
recomputed from the document index and asserted), with the count at distance 1 beside it. A flag only; no rule reads it.

**Reading, fixed in advance:** if ArXiv against Wikipedia reads *clear* in either direction, the post says that the rule separates
mathematical text from encyclopedia prose as it separates code, and "code-leaning" is one instance of source-leaning; the evidence
that the code group concerns code is then the earlier code edit on the labelled texts alone.

    uv run modal run --detach vpd_audit/modal_app.py::s9_panels --step prepare
    uv run modal run --detach vpd_audit/modal_app.py::eval_caches --runs main --sets panel_ArXiv,panel_Wikipedia__en_,panel_Pile_CC,panel_StackExchange,panel_Github
    uv run modal run --detach vpd_audit/modal_app.py::s9_panels --step check
"""

from __future__ import annotations

import hashlib
import json
import time
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from vpd_audit import env

PANEL_ROWS = 200
PANELS: dict[str, str] = {"ArXiv": "panel_ArXiv", "Wikipedia (en)": "panel_Wikipedia__en_", "Pile-CC": "panel_Pile_CC", "StackExchange": "panel_StackExchange", "Github": "panel_Github"}
PANEL_GITHUB_FROM = "calib_github"
SLUGS: dict[str, str] = {"ArXiv": "arxiv", "Wikipedia (en)": "wikipedia", "Pile-CC": "pile_cc", "StackExchange": "stackexchange", "Github": "code"}
WORDS: dict[str, str] = {"ArXiv": "ArXiv", "Wikipedia (en)": "Wikipedia", "Pile-CC": "Pile-CC", "StackExchange": "StackExchange", "Github": "code"}
# (pool A, pool B), each run in both directions
PAIRS: tuple[tuple[str, str], ...] = (("ArXiv", "Wikipedia (en)"), ("Wikipedia (en)", "Pile-CC"), ("Github", "ArXiv"), ("Github", "Wikipedia (en)"), ("Github", "Pile-CC"), ("Github", "StackExchange"))
READING_PAIR = ("ArXiv", "Wikipedia (en)")
# the largest rows-per-document measured for each source, over E_lab, D_code, and D_prose (results/grid/analysis/main/s9/document_counts.csv)
PROXIMITY_ROWS: dict[str, int] = {"ArXiv": 29, "Pile-CC": 36, "Wikipedia (en)": 14, "StackExchange": 6, "Github": 56}
S9B_DIR_NAME = "s9b"
SOURCE_LEANING = "source-leaning: the rule separates mathematical text from encyclopedia prose as it separates code; \"code-leaning\" is one instance, and the evidence that the code group concerns code is the earlier code edit on the labelled texts alone"
NOT_CLEAR = "ArXiv against Wikipedia does not read clear in either direction"


def prepare_panel_github(sets_dir: Path | None = None, *, log: Any = print) -> dict[str, Any]:
    """`panel_Github`: the first 200 rows of `calib_github` with their row indices. Written once; if it exists it must be this."""
    from vpd_audit.data import hash_ids, load_set, save_set

    sets_dir = Path(sets_dir) if sets_dir else env.SETS_DIR
    ids, row_idx, rec = load_set(PANEL_GITHUB_FROM, sets_dir)
    take_ids, take_rows = ids[:PANEL_ROWS], row_idx[:PANEL_ROWS]
    name = PANELS["Github"]
    if (sets_dir / f"{name}.npz").is_file():
        have_ids, have_rows, have = load_set(name, sets_dir)
        assert np.array_equal(have_ids, take_ids) and np.array_equal(have_rows, take_rows), f"{name} exists and is not the first {PANEL_ROWS} rows of {PANEL_GITHUB_FROM}"
        log(f"[s9 panels] {name} exists and equals the first {PANEL_ROWS} rows of {PANEL_GITHUB_FROM} ({have['sha256_ids'][:16]})")
        return {"name": name, "written": False, "sha256_ids": have["sha256_ids"]}
    meta = {k: rec[k] for k in ("source", "file_sha256", "tokenizer", "max_length", "bos_added", "master_seed", "label", "part") if k in rec}
    meta.update({"draw": f"the first {PANEL_ROWS} rows of {PANEL_GITHUB_FROM} ({rec.get('draw')}), in the draw's order", "taken_from": PANEL_GITHUB_FROM, "taken_from_sha256_ids": rec["sha256_ids"],
                 "prepared_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"), "prepared_by": "s9_panels.prepare_panel_github"})
    save_set(name, take_ids, take_rows, meta, sets_dir)
    log(f"[s9 panels] wrote {name}: {take_ids.shape[0]} rows, ids sha256 {hash_ids(take_ids)[:16]}")
    return {"name": name, "written": True, "sha256_ids": hash_ids(take_ids)}


def proximity_pairs(row_indices: np.ndarray, within: int) -> pd.DataFrame:
    """The pairs (i < j) of one panel's rows whose row indices in the source's tokenized part differ by at most `within`."""
    r = np.asarray(row_indices, dtype=np.int64)
    d = np.abs(r[:, None] - r[None, :])
    i, j = np.nonzero(np.triu(d <= within, k=1))
    return pd.DataFrame({"row_a": i, "row_b": j, "row_index_a": r[i], "row_index_b": r[j], "distance": d[i, j]})


def panels_reading(table: pd.DataFrame) -> dict[str, Any]:
    """The reading fixed before the run, from the primary rows (the document floor; with every row its own document, the row floor's numbers):
    *clear* for ArXiv against Wikipedia in either direction is source-leaning."""
    a, b = SLUGS[READING_PAIR[0]], SLUGS[READING_PAIR[1]]
    t = table[(table["floor_counts"] == "documents") & (~table["superseded_by_rerun"]) & (table["slug"].isin([f"{a}_vs_{b}", f"{b}_vs_{a}"]))]
    words = {s: str(g["verdict_for_floor"].iloc[0]) for s, g in t.groupby("slug")}
    assert set(words) == {f"{a}_vs_{b}", f"{b}_vs_{a}"}, words
    return {"words": words, "reading": SOURCE_LEANING if "clear" in words.values() else NOT_CLEAR, "source_leaning": bool("clear" in words.values())}


def measured_proximity() -> dict[str, int]:
    """The largest rows-per-document per source from the document index (`s9_checks.document_index`), recomputed from the saved sets."""
    from vpd_audit.s9_checks import DOC_SETS, document_counts, document_index

    counts = document_counts(document_index(DOC_SETS))
    return {str(s): int(v) for s, v in counts.groupby("source")["rows_per_document_max"].max().items()}


def run_panel_checks(run: str, out_dir: Path, *, n_shuffles: int = 200, master_seed: int = 0, caches: dict[str, Any] | None = None, alive: np.ndarray | None = None, row_indices: dict[str, np.ndarray] | None = None,
                     proximity: dict[str, int] | None = None, log: Any = print) -> dict[str, Any]:
    """Where the panel caches live (CPU). `caches`, `alive`, `row_indices`, and `proximity` are for tests; by default the panel
    caches `<panel>_<run>`, the run's alive vector, the saved sets' row indices, and the measured rows-per-document (`measured_proximity`)."""
    from vpd_audit.code_leaning import CL_TAU, per_document_counts
    from vpd_audit.data import load_set
    from vpd_audit.donors import donors_dir
    from vpd_audit.results import code_commits
    from vpd_audit.s9_checks import PairSpec, existence_pair
    from vpd_audit.sources import Cache, source_hash

    t0 = time.time()
    out_dir = Path(out_dir)
    assert out_dir.name == S9B_DIR_NAME, f"the panel checks write into a directory named {S9B_DIR_NAME!r} only, not {out_dir}"
    out_dir.mkdir(parents=True, exist_ok=True)
    if alive is None:
        alive = np.load(donors_dir() / f"alive_D_unif_{run}.npy")
    if proximity is None:
        proximity = measured_proximity()
        assert {k: proximity.get(k) for k in PROXIMITY_ROWS} == PROXIMITY_ROWS, f"the measured rows-per-document maxima {proximity} are not the recorded {PROXIMITY_ROWS}"
    alive_idx = np.flatnonzero(alive)
    counts, records, prox_rows, prox_summary = {}, {}, [], []
    for source, panel in PANELS.items():
        if caches is None:
            cache = Cache.load(f"{panel}_{run}")
            _, rows, rec = load_set(panel)
            assert cache.n_sequences == PANEL_ROWS == rec["shape"][0], (panel, cache.n_sequences, rec["shape"])
            records[panel] = {"cache_sha256": dict(cache.sha256), "set_sha256_ids": rec["sha256_ids"], "n_rows": int(cache.n_sequences)}
        else:
            cache, rows = caches[source], row_indices[source]  # type: ignore[index]
        counts[source] = per_document_counts(cache, CL_TAU, alive_idx)
        pp = proximity_pairs(rows, int(proximity[source]))
        pp.insert(0, "source", source)
        pp.insert(0, "panel", panel)
        prox_rows.append(pp)
        prox_summary.append({"panel": panel, "source": source, "rows": int(len(rows)), "within_rows": int(proximity[source]), "n_pairs_within": int(len(pp)), "n_pairs_at_distance_1": int((pp["distance"] == 1).sum()),
                             "n_rows_in_a_flagged_pair": int(len(set(pp["row_a"]) | set(pp["row_b"])))})
        del cache
    table_rows: list[dict[str, Any]] = []
    for a, b in PAIRS:
        for x, y in ((a, b), (b, a)):
            spec = PairSpec(f"{WORDS[x]} against {WORDS[y]} (panels, {PANEL_ROWS} rows each)", f"{SLUGS[x]}_vs_{SLUGS[y]}", (PANELS[x], 0, counts[x].shape[0]), (PANELS[y], 0, counts[y].shape[0]))
            docs_x, docs_y = np.arange(counts[x].shape[0], dtype=np.int64), np.arange(counts[y].shape[0], dtype=np.int64)  # every row its own document
            got = existence_pair(spec, counts[x], counts[y], docs_x, docs_y, master_seed=master_seed, n_shuffles=n_shuffles, log=log)
            table_rows += got
            first = next(r for r in got if r["floor_counts"] == "documents" and not r["superseded_by_rerun"])
            log(f"[s9 panels] {spec.name}: {first['n_members']} members, share {first['share']:.4f} -> {first['verdict_for_floor']}; {time.time() - t0:.0f} s")
    table = pd.DataFrame(table_rows)
    table.to_csv(out_dir / "check_b_panels.csv", index=False)
    prox = pd.concat(prox_rows, ignore_index=True)
    prox.to_csv(out_dir / "panel_row_proximity.csv", index=False)
    pd.DataFrame(prox_summary).to_csv(out_dir / "panel_row_proximity_summary.csv", index=False)
    reading = panels_reading(table)
    manifest = {"run": run, "commits": code_commits(), "seconds": time.time() - t0, "n_shuffles": n_shuffles, "master_seed": master_seed, "panels": records, "alive_sha256": source_hash(alive), "n_alive": int(alive.sum()),
                "each_row_its_own_document": True, "proximity_rows": {k: int(v) for k, v in proximity.items() if k in PANELS}, "proximity": prox_summary, "reading": reading,
                "table_sha256": hashlib.sha256((out_dir / "check_b_panels.csv").read_bytes()).hexdigest(), "files": ["check_b_panels.csv", "panel_row_proximity.csv", "panel_row_proximity_summary.csv", "panel_manifest.json"]}
    with open(out_dir / "panel_manifest.json", "w") as f:
        json.dump(manifest, f, indent=2, sort_keys=True, default=str)
    log(f"[s9 panels] reading: {reading['words']} -> {reading['reading']}; done in {time.time() - t0:.0f} s -> {out_dir}")
    return {"run": run, "reading": reading, "n_rows": int(len(table)), "proximity": prox_summary, "out_dir": str(out_dir)}
