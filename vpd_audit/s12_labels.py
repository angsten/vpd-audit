"""Label-only checks for the 2- and 4-token merge sizes, the code-leaning edit's erased sets, the label that edit removes on the
panels, and the document index of the panels. CPU only; no forward pass.

The panels' document index. A panel row is a 512-token window of its source's part-C token stream, and one document spans many
rows. The stream is rebuilt exactly as `data.prepare_labeled_sets` built it (the seeded document permutation of
`data.split_documents`, then the authors' `tokenize_and_concatenate`), with the document of every token tracked: the authors'
procedure is re-run batch by batch (the `Dataset.map` batch of 1,000 documents joined with the end-of-text string, cut into 20
character chunks, each chunk tokenized, the batch's tokens cut into 513-token rows and its tail dropped), and each token's
character offset in the batch's joined text gives its document. Asserted before any row is used: the re-run's ids equal
`data.tokenize_documents` (the authors' function) over the whole part, the part's row and document counts equal the manifest's,
and every panel row equals the stored row bitwise (per-row SHA-256), the panel's `sha256_ids` the manifest's. A row's document is
the one holding most of its saved 512 tokens, end-of-text ids not counted, ties to the earlier (the majority rule of
`s9_checks.block_document_index`). A token whose characters fall in two documents' spans (possible only where a chunk boundary
cuts the end-of-text string) is counted and reported; so is a token made of pieces of a cut end-of-text string.

The merge sets at 1, 2, 4, and 8 donor tokens (rungs "1", "T2", "T4", "2"), from the caches through `cells.build_sources`: for every
pool and draw the donor positions nest; the named sets nest; the plain and marginal controls of D_unif on E nest; the D_unif sets on
E_lab are E's; n_on per draw is printed. The sets at rungs "1" and "2" are held to the committed cells by hash in the local finish.

The erased sets: the code-leaning group's sets at two sizes (256 and 1,007 members on the paper's model) and their usage-matched
twins under every draw, rebuilt through `code_leaning.code_leaning_sets` and `cells.build_sources` as `grid.run_grid` builds them,
held to the committed cells of results/grid/main/tier4/E_lab__code_leaning/ by hash in the local finish.

The removed label, omega, on the panels whose label caches exist: (1/T) times the sum over a row's positions and the erased
components of their labels (the definition of `masks.over_removal`, the loop's per-text `omega` column for a hard-zero cell), then
the mean over rows; for the twins, the mean over the draws. As a validation, the same arithmetic on E_lab's label cache for the
committed cells, compared in the finish with the omega the loop wrote into the committed store (reported, not asserted).

    uv run modal run --detach vpd_audit/modal_app.py::s12_label_tables --dry        (the stand-in: the label tables only)
    uv run modal volume get vpd-audit-cache /results/dry_run_s12/pre_reads/s12 results/dry_run_s12/pre_reads/
    uv run vpd-audit s12-label-checks --finish --dry
    uv run modal run --detach vpd_audit/modal_app.py::s12_label_tables              (the paper's model: the label tables and the document index)
    uv run modal volume get vpd-audit-cache /results/grid/analysis/main/s12 results/grid/analysis/main/
    uv run modal volume get vpd-audit-cache /results/grid/pre_reads/main/s12 results/grid/pre_reads/main/
    uv run vpd-audit s12-label-checks --finish
"""

from __future__ import annotations

import hashlib
import json
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from vpd_audit import env
from vpd_audit.constants import SEQ_LEN

OUT_DIR_NAME = "s12"  # the name of every output directory written here
# the eight panels: source label -> saved set; `panel_Github` is the first 200 rows of `calib_github` (s9_panels.py)
PANEL_SOURCES: dict[str, str] = {"Github": "panel_Github", "StackExchange": "panel_StackExchange", "ArXiv": "panel_ArXiv", "Pile-CC": "panel_Pile_CC", "Wikipedia (en)": "panel_Wikipedia__en_",
                                 "DM Mathematics": "panel_DM_Mathematics", "PubMed Central": "panel_PubMed_Central", "FreeLaw": "panel_FreeLaw"}
CACHED_PANELS: tuple[str, ...] = ("Github", "StackExchange", "ArXiv", "Pile-CC", "Wikipedia (en)")  # the panels whose label caches exist
PANEL_GITHUB_FROM = "calib_github"
PANEL_ROWS = 200
MAP_BATCH_SIZE = 1000  # `datasets.Dataset.map`'s default batch, which `tokenize_and_concatenate`'s map takes (num_proc 1)
N_CHUNKS = 20  # `tokenize_and_concatenate`'s character chunks per batch
EOT_ID = 0  # the end-of-text id of EleutherAI/gpt-neox-20b (the labelled manifest's eos_token_id)
MERGE_RUNGS: tuple[str, ...] = ("1", "T2", "T4", "2")  # 1, 2, 4, 8 donor tokens (sources.RUNG_SCHEDULE)
NEW_RUNGS: tuple[str, ...] = ("T2", "T4")
COMMITTED_RUNGS: tuple[str, ...] = ("1", "2")
POOLS: tuple[str, ...] = ("D_unif", "D_code", "D_prose")
E_CONTROLS: tuple[str, ...] = ("none", "plain", "marginal")  # the real merge and its two controls on E, donors from D_unif
LAUNCH_TIER = 7  # the tier the new cells are enumerated in; a cell's tier is not part of its name and does not enter its source
COMMITTED_TIER = {("E", "none"): 1, ("E", "plain"): 2, ("E", "marginal"): 4, ("E_lab", "none"): 5}
EDIT_SIZES: tuple[int, int] = (256, 1007)
MERGE_SETS_FILE, MERGE_NESTING_FILE, ERASED_SETS_FILE = "merge_sets.csv", "merge_nesting.csv", "erased_sets.csv"
OMEGA_FILE, OMEGA_TEXTS_FILE, OMEGA_E_LAB_FILE, MANIFEST_FILE = "removed_label_panels.csv", "removed_label_panels_per_text.csv", "removed_label_E_lab_from_cache.csv", "manifest.json"
CHECKS_MD, CHECKS_JSON = "checks.md", "checks.json"
DOC_INDEX_FILE, DOC_COUNTS_FILE, DOC_MANIFEST_FILE = "panel_document_index.csv", "panel_document_counts.csv", "panel_document_manifest.json"


class LabelCheckFailure(AssertionError):
    """A label-only check failed: the step stops, and nothing downstream reads its tables."""


def panel_set_name(label: str) -> str:
    """`data.prepare_labeled_sets`' rule for a part-C panel's set name."""
    return "panel_" + "".join(ch if ch.isalnum() else "_" for ch in label)


assert all(PANEL_SOURCES[s] == panel_set_name(s) for s in PANEL_SOURCES)


def analysis_dir(run: str = "main", root: Path | None = None) -> Path:
    return Path(root or env.PROJECT_ROOT / "results") / "grid" / "analysis" / run / OUT_DIR_NAME


def pre_reads_dir(run: str = "main", root: Path | None = None, *, dry: bool = False) -> Path:
    if dry:
        return Path(root or env.PROJECT_ROOT / "results") / "dry_run_s12" / "pre_reads" / OUT_DIR_NAME
    return Path(root or env.PROJECT_ROOT / "results") / "grid" / "pre_reads" / run / OUT_DIR_NAME


def _sha_file(p: Path) -> str:
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


# ============================================================================= the panels' exact document index


def assign_documents(doc_starts: np.ndarray, tok_start: np.ndarray, tok_end: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Per token, the document (index into `doc_starts`, the ascending character starts of the batch's documents in its joined text)
    whose span holds the token's first character; a document's span runs to the next document's start, so it holds the end-of-text
    string that closes it (an end-of-text id carries the document it closes, as in `s9_checks.block_document_index`). Also a mask of the tokens whose last
    character lies in another document's span (a token of an empty character span is judged by its start)."""
    doc_starts, tok_start, tok_end = (np.asarray(x, dtype=np.int64) for x in (doc_starts, tok_start, tok_end))
    assert doc_starts.ndim == 1 and doc_starts.size and doc_starts[0] == 0 and np.all(np.diff(doc_starts) > 0), "document starts: ascending from 0"
    first = np.searchsorted(doc_starts, tok_start, side="right") - 1
    last = np.searchsorted(doc_starts, np.maximum(tok_end - 1, tok_start), side="right") - 1
    return first, last != first


def tokenize_with_documents(texts: list[str], tokenizer: Any, *, batch_size: int = MAP_BATCH_SIZE, num_chunks: int = N_CHUNKS, max_length: int | None = None) -> dict[str, Any]:
    """The authors' `tokenize_and_concatenate(..., add_bos_token=False, to_lower=False)` over a `Dataset` of `texts`, re-run batch by
    batch with each token's document. Returns (n_rows, max_length) arrays: `ids`, `doc` (the index into `texts`), `straddle` (a token
    whose characters fall in two documents' spans) and `separator_piece` (a token, not an end-of-text id, lying wholly inside an
    end-of-text string: a piece of one a chunk boundary cut); the rows each batch kept (`batch_rows`); and the counts of those tokens,
    of the cut end-of-text strings, and of end-of-text strings inside the documents' own text. `max_length` defaults to the labelled
    sets' 513. The caller asserts the ids against the authors' function (`data.tokenize_documents`)."""
    from vpd_audit.data import LABELED_MAX_LENGTH

    max_length = LABELED_MAX_LENGTH if max_length is None else max_length
    eos = tokenizer.eos_token
    assert isinstance(eos, str) and eos
    backend = tokenizer.backend_tokenizer
    ids_rows, doc_rows, straddle_rows, piece_rows = [], [], [], []
    n_cut_separators = n_literal_in_text = 0
    for b0 in range(0, len(texts), batch_size):
        batch = texts[b0 : b0 + batch_size]
        full = eos.join(batch)
        assert len(full) > 0, "an empty batch text"
        lens = np.fromiter((len(t) for t in batch), dtype=np.int64, count=len(batch))
        starts = np.concatenate([[0], np.cumsum(lens + len(eos))[:-1]]).astype(np.int64)
        ends = starts + lens  # the separator after document j is [ends[j], ends[j] + len(eos))
        n_literal_in_text += int(sum(t.count(eos) for t in batch))
        chunk_length = (len(full) - 1) // num_chunks + 1
        ids_parts, s_parts, e_parts = [], [], []
        for i in range(num_chunks):
            c0 = i * chunk_length
            chunk = full[c0 : c0 + chunk_length]
            if 0 < c0 < len(full):
                j = int(np.searchsorted(starts, c0, side="right") - 1)
                if ends[j] < c0 < ends[j] + len(eos):
                    n_cut_separators += 1
            enc = backend.encode(chunk, add_special_tokens=False)
            ids_parts.append(np.asarray(enc.ids, dtype=np.int64))
            off = np.asarray(enc.offsets, dtype=np.int64).reshape(-1, 2)
            s_parts.append(c0 + off[:, 0])
            e_parts.append(c0 + off[:, 1])
        ids = np.concatenate(ids_parts)
        tok_s, tok_e = np.concatenate(s_parts), np.concatenate(e_parts)
        doc, straddle = assign_documents(starts, tok_s, tok_e)
        in_sep = (tok_s >= ends[doc]) & (tok_e <= ends[doc] + len(eos)) & (ids != EOT_ID) & (tok_e > tok_s)
        n = ids.size // max_length
        keep = n * max_length
        ids_rows.append(ids[:keep].reshape(n, max_length))
        doc_rows.append((doc[:keep] + b0).reshape(n, max_length))
        straddle_rows.append(straddle[:keep].reshape(n, max_length))
        piece_rows.append(in_sep[:keep].reshape(n, max_length))

    def cat(parts: list[np.ndarray], dtype: Any) -> np.ndarray:
        return np.concatenate(parts) if parts else np.zeros((0, max_length), dtype=dtype)

    straddle_all, piece_all = cat(straddle_rows, np.bool_), cat(piece_rows, np.bool_)
    return {"ids": cat(ids_rows, np.int64), "doc": cat(doc_rows, np.int64), "straddle": straddle_all, "separator_piece": piece_all, "batch_rows": [int(r.shape[0]) for r in ids_rows],
            "n_straddling_tokens": int(straddle_all.sum()),
            "n_separator_piece_tokens": int(piece_all.sum()), "n_cut_separators": n_cut_separators, "n_end_of_text_literals_in_documents": n_literal_in_text}


def row_documents(ids_rows: np.ndarray, doc_rows: np.ndarray, eot: int = EOT_ID) -> pd.DataFrame:
    """Per row (the saved tokens only): the majority document, the one holding most of the row's tokens other than end-of-text ids,
    ties to the earlier (lower-numbered) document, and the document of the row's first token if the row holds nothing else; the number
    of documents the row's other tokens touch; the row's end-of-text ids."""
    ids_rows, doc_rows = np.asarray(ids_rows), np.asarray(doc_rows)
    assert ids_rows.shape == doc_rows.shape and ids_rows.ndim == 2
    out = []
    for i in range(ids_rows.shape[0]):
        keep = ids_rows[i] != eot
        d = doc_rows[i][keep]
        if d.size == 0:
            out.append({"majority_document": int(doc_rows[i, 0]), "documents_touched": 0, "n_end_of_text": int((~keep).sum())})
            continue
        v, c = np.unique(d, return_counts=True)  # ascending; argmax takes the first maximum, so a tie goes to the earlier document
        out.append({"majority_document": int(v[int(np.argmax(c))]), "documents_touched": int(v.size), "n_end_of_text": int((~keep).sum())})
    return pd.DataFrame(out)


def check_panel_rows(stream_ids: np.ndarray, panel_ids: np.ndarray, file_rows: np.ndarray, name: str) -> dict[str, Any]:
    """Every panel row equals the re-derived stream row (its first 512 ids) bitwise and by SHA-256; raises LabelCheckFailure otherwise."""
    from vpd_audit.data import row_hashes

    file_rows = np.asarray(file_rows, dtype=np.int64)
    if panel_ids.shape[0] != file_rows.size or panel_ids.shape[1] != SEQ_LEN:
        raise LabelCheckFailure(f"{name}: {panel_ids.shape} ids against {file_rows.size} row indices")
    if file_rows.min(initial=0) < 0 or file_rows.max(initial=0) >= stream_ids.shape[0]:
        raise LabelCheckFailure(f"{name}: a row index outside the rebuilt stream's {stream_ids.shape[0]} rows")
    derived = np.ascontiguousarray(stream_ids[file_rows, :SEQ_LEN], dtype=np.int32)
    want, got = row_hashes(np.ascontiguousarray(panel_ids, dtype=np.int32)), row_hashes(derived)
    bad = [i for i, (a, b) in enumerate(zip(want, got)) if a != b]
    if bad or not np.array_equal(derived, np.asarray(panel_ids, dtype=np.int32)):
        raise LabelCheckFailure(f"{name}: {len(bad)} of {file_rows.size} rows differ from the rebuilt stream (first rows {bad[:5]})")
    return {"rows": int(file_rows.size), "rows_equal": True, "row_hashes_sha256": hashlib.sha256("".join(got).encode()).hexdigest()}


def part_c_texts(docs: dict[str, list[str]], label: str, master_seed: int) -> list[str]:
    """A source's part C, in the seeded permutation's order (`data.split_documents`)."""
    from vpd_audit.data import split_documents

    parts = split_documents(docs[label], label, master_seed)
    return [docs[label][i] for i in parts["C"]]


def load_panel(label: str, sets_dir: Path | None = None) -> tuple[np.ndarray, np.ndarray, dict[str, Any]]:
    """A panel's saved ids, row indices into its source's part-C stream, and record (`load_set` verifies the record's hashes).
    `panel_Github` must be the first 200 rows of `calib_github`, row indices included."""
    from vpd_audit.data import load_set

    sd = Path(sets_dir) if sets_dir else env.SETS_DIR
    ids, rows, rec = load_set(PANEL_SOURCES[label], sd)
    if label == "Github":
        c_ids, c_rows, _ = load_set(PANEL_GITHUB_FROM, sd)
        if not (np.array_equal(ids, c_ids[:PANEL_ROWS]) and np.array_equal(rows, c_rows[:PANEL_ROWS])):
            raise LabelCheckFailure(f"panel_Github is not the first {PANEL_ROWS} rows of {PANEL_GITHUB_FROM}")
    elif rec.get("label") != label or rec.get("part") != "C":
        raise LabelCheckFailure(f"{PANEL_SOURCES[label]}: its record names {rec.get('label')!r}, part {rec.get('part')!r}")
    return ids, rows, rec


def panel_document_index(out_dir: Path, *, sets_dir: Path | None = None, labels: tuple[str, ...] = tuple(PANEL_SOURCES), master_seed: int = 0, docs: dict[str, list[str]] | None = None,
                         tokenizer: Any = None, manifest: dict[str, Any] | None = None, log: Any = print) -> dict[str, Any]:
    """The panels' document index, where the labelled file and the sets live. `docs`, `tokenizer`, and `manifest` are for tests; by default the labelled file
    (its SHA-256 asserted against the manifest), the manifest's tokenizer, and sets/labeled_manifest.json. Writes the index, the
    per-panel counts, and a manifest into `out_dir`; raises LabelCheckFailure on the first failed assertion, before any file is written."""
    from vpd_audit.data import LABELED_MAX_LENGTH, LABELED_TOKENIZER, labeled_file_path, read_labeled_documents, tokenize_documents
    from vpd_audit.results import code_commits

    t0 = time.time()
    out_dir = Path(out_dir)
    assert out_dir.name == OUT_DIR_NAME, f"the document index writes into a directory named {OUT_DIR_NAME!r} only, not {out_dir}"
    sd = Path(sets_dir) if sets_dir else env.SETS_DIR
    if manifest is None:
        with open(sd / "labeled_manifest.json") as f:
            manifest = json.load(f)
    file_record: dict[str, Any] = {}
    if docs is None:
        from vpd_audit.artifacts import sha256_file

        path = labeled_file_path()
        sha = sha256_file(path)
        if sha != manifest["file"]["sha256"]:
            raise LabelCheckFailure(f"the labelled file's SHA-256 {sha} is not the manifest's {manifest['file']['sha256']}")
        file_record = {"path": str(path), "sha256": sha, "bytes": int(path.stat().st_size)}
        docs = read_labeled_documents(path, log=log)
    if tokenizer is None:
        from transformers import AutoTokenizer

        assert manifest["tokenizer"] == LABELED_TOKENIZER, manifest["tokenizer"]
        tokenizer = AutoTokenizer.from_pretrained(LABELED_TOKENIZER)
    if tokenizer.eos_token_id != EOT_ID or int(manifest["eos_token_id"]) != EOT_ID:
        raise LabelCheckFailure(f"the end-of-text id is {tokenizer.eos_token_id} (manifest {manifest['eos_token_id']}), not {EOT_ID}")
    if int(manifest["master_seed"]) != master_seed or int(manifest["max_length"]) != LABELED_MAX_LENGTH:
        raise LabelCheckFailure(f"the manifest's master seed {manifest['master_seed']} and row length {manifest['max_length']} are not {master_seed} and {LABELED_MAX_LENGTH}")
    index_rows, counts_rows, parts, panels = [], [], {}, {}
    for label in labels:
        t1 = time.time()
        texts = part_c_texts(docs, label, master_seed)
        want = manifest["parts"][f"{label}/C"]
        chars = int(sum(len(t) for t in texts))
        if len(texts) != int(want["n_docs"]) or chars != int(want["chars"]):
            raise LabelCheckFailure(f"{label}/C: {len(texts)} documents and {chars} characters, the manifest {want['n_docs']} and {want['chars']}")
        mine = tokenize_with_documents(texts, tokenizer)
        ref = tokenize_documents(texts, tokenizer, num_proc=1)
        if mine["ids"].shape[0] != ref.shape[0] or ref.shape[0] != int(want["rows"]) or not np.array_equal(mine["ids"][:, :SEQ_LEN], ref.astype(np.int64)):
            raise LabelCheckFailure(f"{label}/C: the re-run's {mine['ids'].shape[0]} rows are not the authors' tokenize_documents' {ref.shape[0]} (manifest {want['rows']}) id for id")
        parts[label] = {"n_docs": len(texts), "chars": chars, "rows": int(ref.shape[0]), "rows_equal_to_tokenize_documents": True,
                        **{k: int(mine[k]) for k in ("n_straddling_tokens", "n_separator_piece_tokens", "n_cut_separators", "n_end_of_text_literals_in_documents")}, "seconds": time.time() - t1}
        ids, rows, rec = load_panel(label, sd)
        sha_manifest = manifest["sets"].get(PANEL_SOURCES[label], {}).get("sha256_ids")  # panel_Github is not in the labelled manifest; the finish holds it to the committed panel manifest
        if sha_manifest is None and label != "Github":
            raise LabelCheckFailure(f"{PANEL_SOURCES[label]} is not in the labelled manifest")
        if sha_manifest is not None and rec["sha256_ids"] != sha_manifest:
            raise LabelCheckFailure(f"{PANEL_SOURCES[label]}: its record's sha256_ids {rec['sha256_ids']} is not the manifest's {sha_manifest}")
        chk = check_panel_rows(mine["ids"], ids, rows, PANEL_SOURCES[label])
        rd = row_documents(mine["ids"][rows, :SEQ_LEN], mine["doc"][rows, :SEQ_LEN])
        doc_rows = mine["doc"][rows, :SEQ_LEN]
        n_straddle_rows, n_piece_rows = int(mine["straddle"][rows, :SEQ_LEN].sum()), int(mine["separator_piece"][rows, :SEQ_LEN].sum())
        for i, r in enumerate(rows):
            index_rows.append({"panel": PANEL_SOURCES[label], "source": label, "row": i, "file_row_index": int(r), **rd.iloc[i].to_dict()})
        per_doc = rd.groupby("majority_document").size()
        counts_rows.append({"panel": PANEL_SOURCES[label], "source": label, "rows": int(len(rows)), "distinct_documents": int(per_doc.size), "rows_per_document_mean": float(per_doc.mean()),
                            "rows_per_document_max": int(per_doc.max()), "rows_sharing_a_document": int(per_doc[per_doc > 1].sum()), "documents_touched_mean": float(rd["documents_touched"].mean()),
                            "part_C_documents": len(texts), "part_C_rows": int(ref.shape[0]), "straddling_tokens_in_rows": n_straddle_rows, "separator_piece_tokens_in_rows": n_piece_rows})
        panels[PANEL_SOURCES[label]] = {"source": label, "sha256_ids": rec["sha256_ids"], "sha256_ids_manifest": sha_manifest, **chk, "distinct_documents": int(per_doc.size),
                                        "first_document_in_rows": int(doc_rows.min()), "last_document_in_rows": int(doc_rows.max())}
        log(f"[panel documents] {label}/C: {len(texts)} documents -> {ref.shape[0]} rows, equal to tokenize_documents; {PANEL_SOURCES[label]}: {len(rows)} rows equal bitwise, "
            f"{per_doc.size} distinct documents; straddling tokens in the part {mine['n_straddling_tokens']} ({n_straddle_rows} in the panel's rows), separator pieces {mine['n_separator_piece_tokens']} "
            f"({n_piece_rows} in the panel's rows); {time.time() - t1:.0f} s")
        del mine, ref
    index = pd.DataFrame(index_rows, columns=["panel", "source", "row", "file_row_index", "majority_document", "documents_touched", "n_end_of_text"])
    counts = pd.DataFrame(counts_rows)
    out_dir.mkdir(parents=True, exist_ok=True)
    index.to_csv(out_dir / DOC_INDEX_FILE, index=False, lineterminator="\n")
    counts.to_csv(out_dir / DOC_COUNTS_FILE, index=False, lineterminator="\n")
    rec_out = {"commits": code_commits(), "master_seed": master_seed, "file": file_record, "tokenizer": getattr(tokenizer, "name_or_path", None), "eos_token_id": EOT_ID,
               "procedure": {"map_batch_size": MAP_BATCH_SIZE, "chunks_per_batch": N_CHUNKS, "row_length": int(manifest["max_length"]), "saved_tokens_per_row": SEQ_LEN,
                             "majority": "over the saved 512 tokens, end-of-text ids not counted, ties to the earlier document"},
               "parts": parts, "panels": panels, "seconds": time.time() - t0,
               "files": {DOC_INDEX_FILE: _sha_file(out_dir / DOC_INDEX_FILE), DOC_COUNTS_FILE: _sha_file(out_dir / DOC_COUNTS_FILE)}}
    with open(out_dir / DOC_MANIFEST_FILE, "w") as f:
        json.dump(rec_out, f, indent=2, sort_keys=True, default=str)
    log(f"[panel documents] done in {time.time() - t0:.0f} s -> {out_dir}")
    return {"index": index, "counts": counts, "manifest": rec_out}


AGREEMENT_FILE, AGREEMENT_MANIFEST_FILE = "panel_document_agreement.csv", "panel_document_agreement.json"


def batch_agreement(ids: np.ndarray, doc: np.ndarray, separator_piece: np.ndarray, straddle: np.ndarray, first_document: int, eot: int = EOT_ID) -> dict[str, Any]:
    """One batch's kept tokens (its rows, flattened in order): the offset rule's documents against the end-of-text count, the rule of
    `s9_checks.block_document_index` (a token's document is the number of end-of-text ids before it in the batch, counted from the
    batch's first document). The lag, offset document minus counted document, starts at 0; a cut end-of-text string hides one id, so
    the lag steps up by one at the first token after the cut string's pieces; an end-of-text string inside a document's own text adds
    an id, so it steps down. Returns the counts, the step positions, and whether every step up sits right after a run of cut-string
    pieces (or a token straddling the boundary) and every such run is followed by one."""
    ids, doc = np.asarray(ids).reshape(-1), np.asarray(doc).reshape(-1)
    piece, strad = np.asarray(separator_piece, dtype=bool).reshape(-1), np.asarray(straddle, dtype=bool).reshape(-1)
    assert ids.shape == doc.shape == piece.shape == strad.shape
    is_eot = ids == eot
    counted = np.cumsum(is_eot) - is_eot
    lag = (doc - int(first_document)) - counted
    d = np.diff(lag)
    up, down = np.flatnonzero(d > 0) + 1, np.flatnonzero(d < 0) + 1
    runs = np.flatnonzero(piece & ~np.concatenate([[False], piece[:-1]]))  # the first token of each run of cut-string pieces
    run_ends = np.flatnonzero(piece & ~np.concatenate([piece[1:], [False]]))  # the last token of each run
    at_cut = [bool(p > 0 and (piece[p - 1] or strad[p - 1])) for p in up]
    up_set = set(up.tolist())
    followed = [bool((e + 1) in up_set or (e + 2 < lag.size and strad[e + 1] and (e + 2) in up_set)) for e in run_ends]
    return {"n_tokens": int(lag.size), "n_tokens_agreeing": int((lag == 0).sum()), "lag_first": int(lag[0]) if lag.size else 0, "lag_last": int(lag[-1]) if lag.size else 0,
            "n_steps_up": int(up.size), "n_steps_down": int(down.size), "steps_up_of_size_one": bool(np.all(d[d > 0] == 1)), "n_cut_string_runs": int(runs.size),
            "n_steps_up_after_a_cut_string": int(sum(at_cut)), "n_cut_string_runs_followed_by_a_step": int(sum(followed)), "step_positions": [int(p) for p in up],
            "differ_only_at_cut_strings": bool(lag.size == 0 or (lag[0] == 0 and down.size == 0 and all(at_cut) and all(followed) and np.all(d[d > 0] == 1)))}


def panel_document_agreement(out_dir: Path, *, sets_dir: Path | None = None, labels: tuple[str, ...] = tuple(PANEL_SOURCES), master_seed: int = 0, docs: dict[str, list[str]] | None = None,
                             tokenizer: Any = None, manifest: dict[str, Any] | None = None, log: Any = print) -> dict[str, Any]:
    """Per source and per batch of 1,000 documents of its part C: how often the offset rule's document agrees with the end-of-text
    count (`batch_agreement`). Each batch is re-run alone (`tokenize_with_documents` on its 1,000 documents is that batch of the whole
    part), the batches' rows are asserted to be the part's row count, and every panel row is asserted bitwise against them, so the
    stream counted is the one the document index was built on. Writes panel_document_agreement.csv and its manifest into `out_dir`
    (new files beside the document index, which is not touched)."""
    from vpd_audit.data import LABELED_MAX_LENGTH, LABELED_TOKENIZER, labeled_file_path, read_labeled_documents
    from vpd_audit.results import code_commits

    t0 = time.time()
    out_dir = Path(out_dir)
    assert out_dir.name == OUT_DIR_NAME, f"the agreement table writes into a directory named {OUT_DIR_NAME!r} only, not {out_dir}"
    sd = Path(sets_dir) if sets_dir else env.SETS_DIR
    if manifest is None:
        with open(sd / "labeled_manifest.json") as f:
            manifest = json.load(f)
    file_record: dict[str, Any] = {}
    if docs is None:
        from vpd_audit.artifacts import sha256_file

        path = labeled_file_path()
        sha = sha256_file(path)
        if sha != manifest["file"]["sha256"]:
            raise LabelCheckFailure(f"the labelled file's SHA-256 {sha} is not the manifest's {manifest['file']['sha256']}")
        file_record = {"sha256": sha, "bytes": int(path.stat().st_size)}
        docs = read_labeled_documents(path, log=log)
    if tokenizer is None:
        from transformers import AutoTokenizer

        tokenizer = AutoTokenizer.from_pretrained(LABELED_TOKENIZER)
    if tokenizer.eos_token_id != EOT_ID or int(manifest["max_length"]) != LABELED_MAX_LENGTH:
        raise LabelCheckFailure("the end-of-text id or the row length is not the labelled sets'")
    rows, per_source = [], {}
    for label in labels:
        texts = part_c_texts(docs, label, master_seed)
        stream = []
        for b, b0 in enumerate(range(0, len(texts), MAP_BATCH_SIZE)):
            got = tokenize_with_documents(texts[b0 : b0 + MAP_BATCH_SIZE], tokenizer)
            stream.append(got["ids"])
            a = batch_agreement(got["ids"], got["doc"], got["separator_piece"], got["straddle"], 0)
            rows.append({"source": label, "batch": b, "first_document": b0, "n_documents": len(texts[b0 : b0 + MAP_BATCH_SIZE]), "n_rows": int(got["ids"].shape[0]),
                         "n_cut_strings_in_the_batch": int(got["n_cut_separators"]), "n_end_of_text_strings_in_documents": int(got["n_end_of_text_literals_in_documents"]),
                         **{k: v for k, v in a.items() if k != "step_positions"}, "step_positions": ";".join(str(p) for p in a["step_positions"])})
        ids = np.concatenate(stream) if stream else np.zeros((0, LABELED_MAX_LENGTH), dtype=np.int64)
        if ids.shape[0] != int(manifest["parts"][f"{label}/C"]["rows"]):
            raise LabelCheckFailure(f"{label}/C: the batches give {ids.shape[0]} rows, the manifest {manifest['parts'][f'{label}/C']['rows']}")
        p_ids, p_rows, _ = load_panel(label, sd)
        check_panel_rows(ids, p_ids, p_rows, PANEL_SOURCES[label])
        mine = [r for r in rows if r["source"] == label]
        per_source[label] = {"batches": len(mine), "n_tokens": sum(r["n_tokens"] for r in mine), "n_tokens_agreeing": sum(r["n_tokens_agreeing"] for r in mine),
                             "n_cut_strings_in_kept_tokens": sum(r["n_cut_string_runs"] for r in mine), "n_steps_up": sum(r["n_steps_up"] for r in mine), "n_steps_down": sum(r["n_steps_down"] for r in mine),
                             "differ_only_at_cut_strings": all(r["differ_only_at_cut_strings"] for r in mine)}
        log(f"[document agreement] {label}/C: {per_source[label]}; {time.time() - t0:.0f} s")
    table = pd.DataFrame(rows)
    out_dir.mkdir(parents=True, exist_ok=True)
    table.to_csv(out_dir / AGREEMENT_FILE, index=False, lineterminator="\n")
    rec = {"commits": code_commits(), "master_seed": master_seed, "file": file_record, "per_source": per_source, "seconds": time.time() - t0,
           "rule": "lag = offset document - end-of-text count within each batch of 1,000 documents; it may step up only right after a cut end-of-text string",
           "files": {AGREEMENT_FILE: _sha_file(out_dir / AGREEMENT_FILE)}}
    with open(out_dir / AGREEMENT_MANIFEST_FILE, "w") as f:
        json.dump(rec, f, indent=2, sort_keys=True, default=str)
    return {"table": table, "per_source": per_source}


# ============================================================================= the label tables (where the caches live)


@dataclass(frozen=True)
class LabelInputs:
    run: str  # a cache is named <set>_<run>
    pool_sets: dict[str, str]  # pool -> the set its cache was built on
    panel_caches: dict[str, str]  # source -> the set of a panel label cache (the removed label)
    e_lab: str  # the set of E_lab's label cache (the removed label's validation)
    draws: int
    edit_sizes: tuple[int, ...]
    group_threshold: float
    wide_threshold: float
    committed_roots: tuple[str, ...]  # relative to the project's results/
    master_seed: int = 0


def paper_inputs(run: str = "main") -> LabelInputs:
    from vpd_audit.code_leaning import CL_GROUP, CL_WIDE

    assert run == "main", run
    return LabelInputs(run=run, pool_sets={p: p for p in POOLS}, panel_caches={s: PANEL_SOURCES[s] for s in CACHED_PANELS}, e_lab="E_lab", draws=8, edit_sizes=EDIT_SIZES,
                     group_threshold=CL_GROUP, wide_threshold=CL_WIDE, committed_roots=("grid/main", "grid/main_s9"))


def dry_inputs(draws: int = 2) -> LabelInputs:
    """The stand-in: its dry sets and caches, the forced code-leaning thresholds `code_leaning.STAND_IN_GROUP` and `STAND_IN_WIDE`
    (the committed dry-run ladder is 16, 64, 94 = the group, then 256 and 456 descriptive), 64 members and the whole group for the two
    edit sizes, and E_lab_dry's cache standing in for a panel. Its committed stores are the stand-in's dry runs under results/dry_run,
    results/dry_run_s7, and results/dry_run_s9. Exercises the code paths; carries no meaning."""
    from vpd_audit.code_leaning import STAND_IN_GROUP, STAND_IN_WIDE

    return LabelInputs(run="simplestories", pool_sets={p: f"{p}_dry" for p in POOLS}, panel_caches={"stand-in panel (E_lab_dry)": "E_lab_dry"}, e_lab="E_lab_dry", draws=draws, edit_sizes=(64, 94),
                     group_threshold=STAND_IN_GROUP, wide_threshold=STAND_IN_WIDE, committed_roots=("dry_run", "dry_run_s7", "dry_run_s9"))


def merge_cells(run: str, draws: int) -> list[Any]:
    """The merge-size cells: the real merge on E with donors from D_unif and its plain and marginal (replicate 0) controls, and the real merge
    on E_lab from each pool, at 1, 2, 4, and 8 donor tokens, every draw; the configuration of the committed cells (tau 0.1, background
    r0, the residual excluded). At rungs "1" and "2" these are the committed cells' names."""
    from vpd_audit.cells import TAU_PRIMARY, Cell

    cells = []
    for ctl in E_CONTROLS:
        for k in range(draws):
            for r in MERGE_RUNGS:
                cells.append(Cell(run, "union", "E", "D_unif", TAU_PRIMARY, "r0", "excluded", k, r, ctl, COMMITTED_TIER[("E", ctl)] if r in COMMITTED_RUNGS else LAUNCH_TIER, descriptive=r in NEW_RUNGS))
    for pool in POOLS:
        for k in range(draws):
            for r in MERGE_RUNGS:
                cells.append(Cell(run, "union", "E_lab", pool, TAU_PRIMARY, "r0", "excluded", k, r, "none", COMMITTED_TIER[("E_lab", "none")] if r in COMMITTED_RUNGS else LAUNCH_TIER, descriptive=r in NEW_RUNGS))
    return cells


def chain_nested(sets: list[np.ndarray]) -> bool:
    """True if every set lies inside the next."""
    return all(not np.any(a & ~b) for a, b in zip(sets[:-1], sets[1:]))


def merge_tables(inp: LabelInputs, caches: dict[str, Any], alive_vec: np.ndarray, module_to_c: dict[str, int], *, log: Any = print) -> tuple[pd.DataFrame, pd.DataFrame, list[str]]:
    """The merge-size checks from the caches: per pool and draw, the donor positions at 1, 2, 4, 8 tokens strictly nested with those
    sizes; per chain (set, pool, control, draw), the sets nested; each control's matched set and count the real merge's; the D_unif sets
    on E_lab equal E's. Returns the per-cell table, the per-chain nesting table, and the list of failures (empty if every check holds);
    the hashes at rungs "1" and "2" are held to the committed cells in the finish."""
    from vpd_audit.cells import build_sources
    from vpd_audit.sources import RUNG_SCHEDULE, donor_set, source_hash

    cells = merge_cells(inp.run, inp.draws)
    built = build_sources(cells, caches, {inp.run: (alive_vec, source_hash(alive_vec))}, None, None, module_to_c, master_seed=inp.master_seed, log=log)
    by = {(c.eval_set, c.donor_pool, c.control, c.draw, c.rung): c for c in cells}
    failures: list[str] = []
    rows = []
    for c in cells:
        rec = built[c.name].record
        ds = donor_set(c.donor_pool, caches[f"{c.donor_pool}_{inp.run}"].n_sequences, c.draw, c.rung, inp.master_seed)
        rows.append({"cell": c.name, "eval_set": c.eval_set, "pool": c.donor_pool, "control": c.control, "draw": c.draw, "rung": c.rung, "donor_tokens": int(RUNG_SCHEDULE[c.rung][1]),
                     "committed_rung": c.rung in COMMITTED_RUNGS, "n_on": int(rec["n_on"]["total"]), "named_n_on": int(rec["named_n_on"]["total"]), "source_sha256": rec["source_sha256"],
                     "matched_source_sha256": rec.get("matched_source_sha256"), "donor_positions": ";".join(str(p) for p in ds.positions)})
        if c.control != "none":
            named = by[(c.eval_set, c.donor_pool, "none", c.draw, c.rung)]
            if rec.get("matched_source_sha256") != built[named.name].record["source_sha256"] or int(rec["n_on"]["total"]) != int(built[named.name].record["n_on"]["total"]):
                failures.append(f"{c.name}: its matched set or its count is not the real merge's at the same draw and rung")
    table = pd.DataFrame(rows)
    nest_rows = []
    chains = sorted({(c.eval_set, c.donor_pool, c.control, c.draw) for c in cells})
    for es, pool, ctl, k in chains:
        chain = [by[(es, pool, ctl, k, r)] for r in MERGE_RUNGS]
        sets = [built[c.name].rho for c in chain]
        pos = [set(donor_set(pool, caches[f"{pool}_{inp.run}"].n_sequences, k, r, inp.master_seed).positions) for r in MERGE_RUNGS]
        pos_ok = all(a < b for a, b in zip(pos[:-1], pos[1:])) and [len(p) for p in pos] == [int(RUNG_SCHEDULE[r][1]) for r in MERGE_RUNGS]
        sets_ok = chain_nested(sets)
        n = [int(s.sum()) for s in sets]
        nest_rows.append({"eval_set": es, "pool": pool, "control": ctl, "draw": k, "positions_nested": bool(pos_ok), "sets_nested": bool(sets_ok), **{f"n_on_r{r}": v for r, v in zip(MERGE_RUNGS, n)}})
        if not pos_ok:
            failures.append(f"{es} {pool} {ctl} draw {k}: the donor positions at 1, 2, 4, 8 tokens are not strictly nested with sizes 1, 2, 4, 8")
        if not sets_ok:
            failures.append(f"{es} {pool} {ctl} draw {k}: the sets at 1, 2, 4, 8 tokens are not nested (n_on {n})")
    nesting = pd.DataFrame(nest_rows)
    # the D_unif sets on E_lab (arm U) are E's real-merge sets, draw for draw and rung for rung
    for k in range(inp.draws):
        for r in MERGE_RUNGS:
            a, b = built[by[("E_lab", "D_unif", "none", k, r)].name].record["source_sha256"], built[by[("E", "D_unif", "none", k, r)].name].record["source_sha256"]
            if a != b:
                failures.append(f"arm U on E_lab, draw {k}, rung {r}: its set is not E's real-merge set")
    return table, nesting, failures


def erased_sets(inp: LabelInputs, caches: dict[str, Any], alive_vec: np.ndarray, module_to_c: dict[str, int], *, log: Any = print) -> tuple[pd.DataFrame, dict[str, np.ndarray], dict[str, Any]]:
    """The erased sets: the code-leaning group's sets at the edit sizes and their twins under every draw, through `code_leaning_sets` and
    `build_sources` as `grid.run_grid` builds them. Returns the table, the sets by cell name, and the group's record."""
    from vpd_audit.cells import TAU_PRIMARY, TIER_4, Cell, build_sources, code_leaning_rung
    from vpd_audit.code_leaning import code_leaning_sets
    from vpd_audit.sources import source_hash

    run = inp.run
    cl = code_leaning_sets(caches[f"D_code_{run}"], caches[f"D_prose_{run}"], alive_vec, group_threshold=inp.group_threshold, wide_threshold=inp.wide_threshold, master_seed=inp.master_seed)
    ladder = {int(a): bool(b) for a, b in cl.ladder}
    missing = [n for n in inp.edit_sizes if n not in ladder]
    if missing:
        raise LabelCheckFailure(f"edit sizes {missing} are not on the run's code-leaning ladder {cl.ladder}")
    cells = [Cell(run, "code_leaning_hard", "E_lab", "D_code", TAU_PRIMARY, "ones", "included", 0, code_leaning_rung(n), "none", TIER_4, descriptive=ladder[n]) for n in inp.edit_sizes]
    cells += [Cell(run, "code_leaning_hard", "E_lab", "D_code", TAU_PRIMARY, "ones", "included", k, code_leaning_rung(n), "usage", TIER_4, descriptive=ladder[n]) for n in inp.edit_sizes for k in range(inp.draws)]
    built = build_sources(cells, caches, {run: (alive_vec, source_hash(alive_vec))}, None, None, module_to_c, master_seed=inp.master_seed, log=log, code_leaning={run: cl})
    rows, sets = [], {}
    for c in cells:
        rec = built[c.name].record
        sets[c.name] = built[c.name].rho
        rows.append({"cell": c.name, "size": int(rec["donor_size"]), "control": c.control, "draw": c.draw, "descriptive": bool(c.descriptive), "n_on": int(rec["n_on"]["total"]),
                     "source_sha256": rec["source_sha256"], "matched_source_sha256": rec.get("matched_source_sha256"), "shortfall": int(rec.get("control", {}).get("shortfall_at_this_rung", 0))})
    group = {"n_group": cl.n_group, "n_wide": cl.n_wide, "ladder": [[int(a), bool(b)] for a, b in cl.ladder], "group_threshold": cl.group_threshold, "wide_threshold": cl.wide_threshold}
    log(f"[erased sets] code-leaning group {cl.n_group} at s >= {cl.group_threshold:g}, wide set {cl.n_wide}; {len(cells)} erased sets built")
    return pd.DataFrame(rows), sets, group


def removed_label_per_text(cache: Any, rho: np.ndarray) -> np.ndarray:
    """omega per text: (1/T) times the sum over the text's positions and the components of `rho` of their labels, from the label cache
    (every nonzero label; float32 values summed in float64). The definition of `masks.over_removal`, the loop's per-text `omega` column."""
    rho = np.asarray(rho)
    assert rho.dtype == np.bool_ and rho.shape == (cache.n_sub,), (rho.dtype, rho.shape)
    N = int(cache.n_sequences)
    assert cache.n_positions == N * SEQ_LEN, (cache.n_positions, N)
    sel = rho[np.asarray(cache.indices, dtype=np.int64)]
    counts = np.diff(np.asarray(cache.indptr, dtype=np.int64))
    row_of_entry = np.repeat(np.repeat(np.arange(N, dtype=np.int64), SEQ_LEN), counts)
    per_row = np.bincount(row_of_entry[sel], weights=np.asarray(cache.values)[sel].astype(np.float64), minlength=N)
    return per_row / float(SEQ_LEN)


def removed_label_tables(inp: LabelInputs, sets: dict[str, np.ndarray], erased: pd.DataFrame, cache_dir: Path | None = None, sets_dir: Path | None = None, *, log: Any = print) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, dict[str, Any]]:
    """The removed label on the panels whose label caches exist, and the same arithmetic on E_lab's cache for the committed cells (the validation).
    Returns the per-panel table, the per-text panel values, E_lab's per-text values, and the caches' records."""
    from vpd_audit.data import load_set
    from vpd_audit.donors import donors_dir
    from vpd_audit.sources import Cache

    def load_checked(set_name: str) -> tuple[Any, dict[str, Any]]:
        name = f"{set_name}_{inp.run}"
        with open(Path(cache_dir or donors_dir()) / f"{name}.json") as f:
            meta = json.load(f)
        _, _, rec = load_set(set_name, Path(sets_dir) if sets_dir else env.SETS_DIR)
        if meta.get("set_hash") != rec["sha256_ids"]:
            raise LabelCheckFailure(f"cache {name}: built on a set with ids hash {meta.get('set_hash')}, not the saved {set_name}'s {rec['sha256_ids']}")
        cache = Cache.load(name, cache_dir)
        if cache.n_sequences != int(rec["shape"][0]):
            raise LabelCheckFailure(f"cache {name}: {cache.n_sequences} sequences, the set {rec['shape'][0]}")
        return cache, {"name": name, "set_sha256_ids": rec["sha256_ids"], "n_sequences": int(cache.n_sequences), "sha256": dict(cache.sha256)}

    group_cell = {int(r["size"]): r["cell"] for _, r in erased.iterrows() if r["control"] == "none"}
    twin_cells = {n: [r["cell"] for _, r in erased[(erased["size"] == n) & (erased["control"] == "usage")].sort_values("draw").iterrows()] for n in inp.edit_sizes}
    assert all(len(v) == inp.draws for v in twin_cells.values()), {n: len(v) for n, v in twin_cells.items()}
    records: dict[str, Any] = {}
    rows, text_rows = [], []
    for source, set_name in inp.panel_caches.items():
        cache, records[set_name] = load_checked(set_name)
        for n in inp.edit_sizes:
            om_g = removed_label_per_text(cache, sets[group_cell[n]])
            om_t = np.stack([removed_label_per_text(cache, sets[c]) for c in twin_cells[n]])  # (draws, N)
            om_t_text = om_t.mean(axis=0)
            rows.append({"panel": set_name, "source": source, "size": n, "n_rows": int(cache.n_sequences), "omega_group": float(om_g.mean()), "omega_twins": float(om_t_text.mean()),
                         "omega_twins_draw_min": float(om_t.mean(axis=1).min()), "omega_twins_draw_max": float(om_t.mean(axis=1).max()), "group_cell": group_cell[n], "n_twin_draws": int(om_t.shape[0])})
            for i in range(cache.n_sequences):
                text_rows.append({"panel": set_name, "source": source, "size": n, "row": i, "omega_group": float(om_g[i]), "omega_twins": float(om_t_text[i])})
        log(f"[removed label] {set_name}: " + "; ".join(f"{r['size']} members: group {r['omega_group']:.4f}, twins {r['omega_twins']:.4f}" for r in rows if r["panel"] == set_name))
        del cache
    table = pd.DataFrame(rows)
    table["rank_by_omega_group"] = table.groupby("size")["omega_group"].rank(ascending=False, method="min").astype(int)
    e_cache, records[inp.e_lab] = load_checked(inp.e_lab)
    e_rows = []
    for _, r in erased.iterrows():
        om = removed_label_per_text(e_cache, sets[r["cell"]])
        for i in range(e_cache.n_sequences):
            e_rows.append({"cell": r["cell"], "size": int(r["size"]), "control": r["control"], "draw": int(r["draw"]), "seq": i, "omega_from_cache": float(om[i])})
    return table, pd.DataFrame(text_rows), pd.DataFrame(e_rows), records


def label_tables(out_dir: Path, *, inputs: LabelInputs | None = None, cache_dir: Path | None = None, sets_dir: Path | None = None, log: Any = print) -> dict[str, Any]:
    """The merge sets, the erased sets, and the removed label where the caches live: the tables and a manifest into `out_dir` (a new
    directory named s12). A failed merge-set check is written into the manifest and raised after the tables are written, so that the
    evidence is kept; nothing is read from a store."""
    from vpd_audit.donors import donors_dir
    from vpd_audit.results import code_commits
    from vpd_audit.sources import Cache, source_hash

    t0 = time.time()
    inp = inputs or paper_inputs()
    out_dir = Path(out_dir)
    assert out_dir.name == OUT_DIR_NAME, f"the label tables write into a directory named {OUT_DIR_NAME!r} only, not {out_dir}"
    out_dir.mkdir(parents=True, exist_ok=True)
    caches = {f"{p}_{inp.run}": Cache.load(f"{inp.pool_sets[p]}_{inp.run}", cache_dir) for p in POOLS}
    alive_vec = np.load(Path(cache_dir or donors_dir()) / f"alive_{inp.pool_sets['D_unif']}_{inp.run}.npy")
    module_to_c = dict(caches[f"D_unif_{inp.run}"].module_to_c)
    log(f"[label tables] {inp.run}: caches {[c.name for c in caches.values()]} loaded, alive {int(alive_vec.sum())}; {time.time() - t0:.0f} s")
    merge, nesting, failures = merge_tables(inp, caches, alive_vec, module_to_c, log=log)
    merge.to_csv(out_dir / MERGE_SETS_FILE, index=False, lineterminator="\n")
    nesting.to_csv(out_dir / MERGE_NESTING_FILE, index=False, lineterminator="\n")
    new = merge[merge["rung"].isin(NEW_RUNGS) & (merge["control"] == "none")]
    for (es, pool), g in new.groupby(["eval_set", "pool"], sort=False):
        log(f"[merge sets] n_on on {es}, donors {pool}: " + "; ".join(f"{r} ({int(g[g.rung == r].donor_tokens.iloc[0])} tokens): " + ", ".join(str(v) for v in g[g.rung == r].sort_values("draw").n_on) for r in NEW_RUNGS))
    erased, sets, group = erased_sets(inp, caches, alive_vec, module_to_c, log=log)
    erased.to_csv(out_dir / ERASED_SETS_FILE, index=False, lineterminator="\n")
    del caches
    omega, omega_texts, omega_e_lab, cache_records = removed_label_tables(inp, sets, erased, cache_dir, sets_dir, log=log)
    omega.to_csv(out_dir / OMEGA_FILE, index=False, lineterminator="\n")
    omega_texts.to_csv(out_dir / OMEGA_TEXTS_FILE, index=False, lineterminator="\n")
    omega_e_lab.to_csv(out_dir / OMEGA_E_LAB_FILE, index=False, lineterminator="\n")
    files = [MERGE_SETS_FILE, MERGE_NESTING_FILE, ERASED_SETS_FILE, OMEGA_FILE, OMEGA_TEXTS_FILE, OMEGA_E_LAB_FILE]
    manifest = {"run": inp.run, "inputs": {k: (list(v) if isinstance(v, tuple) else v) for k, v in inp.__dict__.items()}, "commits": code_commits(), "seconds": time.time() - t0,
                "pool_caches": {p: f"{inp.pool_sets[p]}_{inp.run}" for p in POOLS}, "alive_sha256": source_hash(alive_vec), "n_alive": int(alive_vec.sum()), "code_leaning": group,
                "label_caches": cache_records, "failures": failures, "files": {f: _sha_file(out_dir / f) for f in files}}
    with open(out_dir / MANIFEST_FILE, "w") as f:
        json.dump(manifest, f, indent=2, sort_keys=True, default=str)
    if failures:
        raise LabelCheckFailure(f"merge sets: {len(failures)} check(s) failed: {failures[:5]}")
    log(f"[label tables] done in {time.time() - t0:.0f} s -> {out_dir}")
    return {"run": inp.run, "n_merge_cells": int(len(merge)), "n_erased_sets": int(len(erased)), "omega": omega, "failures": failures, "out_dir": str(out_dir)}


# ============================================================================= the local finish: hashes against the committed stores


def committed_tables(inp: LabelInputs, results_root: Path) -> Any:
    from vpd_audit.tier5 import CommittedTables

    return CommittedTables(tuple(Path(results_root) / r for r in inp.committed_roots))


def hold_to_committed(table: pd.DataFrame, committed: Any, what: str, relative_to: Path | None = None) -> dict[str, Any]:
    """Every row's `source_sha256` equals the committed cell's of the same name; raises LabelCheckFailure on the first missing or different one.
    Returns the count and the stores the names were read from (paths relative to `relative_to` when given)."""
    import os

    where: dict[str, int] = {}
    for _, r in table.iterrows():
        if r["cell"] not in committed:
            raise LabelCheckFailure(f"{what}: {r['cell']} is in no committed store ({[str(x) for x in committed.roots]})")
        want = committed.source_sha256(r["cell"])
        if not (isinstance(want, str) and want == r["source_sha256"]):
            raise LabelCheckFailure(f"{what}: {r['cell']}'s set ({str(r['source_sha256'])[:16]}) is not the committed one ({str(want)[:16]}, in {committed.where[r['cell']]})")
        key = str(committed.where[r["cell"]]) if relative_to is None else os.path.relpath(committed.where[r["cell"]], relative_to)
        where[key] = where.get(key, 0) + 1
    return {"n_equal": int(len(table)), "stores": where}


def e_lab_omega_validation(omega_e_lab: pd.DataFrame, committed: Any) -> pd.DataFrame:
    """Per cell: the omega the loop wrote into the committed store against the cache's, per text (reported, not asserted)."""
    rows = []
    for cell, g in omega_e_lab.groupby("cell", sort=False):
        d = committed.where[cell]
        ps = pd.read_parquet(Path(d) / "per_sequence.parquet", columns=["cell", "seq", "omega"])
        ps = ps[ps["cell"] == cell].sort_values("seq")
        g = g.sort_values("seq")
        if not np.array_equal(ps["seq"].to_numpy(), g["seq"].to_numpy()):
            raise LabelCheckFailure(f"{cell}: the committed store's texts are not the cache's")
        store = ps["omega"].to_numpy(np.float64)
        cache = g["omega_from_cache"].to_numpy(np.float64)
        diff = np.abs(store - cache)
        with np.errstate(divide="ignore", invalid="ignore"):
            rel = np.where(np.abs(store) > 0, diff / np.abs(store), np.where(diff > 0, np.inf, 0.0))
        rows.append({"cell": cell, "size": int(g["size"].iloc[0]), "control": g["control"].iloc[0], "draw": int(g["draw"].iloc[0]), "n_texts": int(len(g)), "mean_store": float(store.mean()),
                     "mean_cache": float(cache.mean()), "max_abs_difference": float(diff.max()), "max_relative_difference": float(rel.max()), "n_texts_bitwise_equal_in_float32": int((store.astype(np.float32) == cache.astype(np.float32)).sum())})
    return pd.DataFrame(rows)


def finish_label_checks(pre_dir: Path, results_root: Path, *, inputs: LabelInputs | None = None, doc_dir: Path | None = None, log: Any = print) -> dict[str, Any]:
    """The local finish on the pulled directories and the committed stores in git: the document index's panels against the committed
    manifests (with `doc_dir`, the paper's run only), the merge sets and the erased sets against the committed cells by hash
    (LabelCheckFailure on the first difference), the removed label's table with the panels' order by the group's omega, and E_lab's
    omega validation. Writes checks.json and checks.md into `pre_dir`."""
    inp = inputs or paper_inputs()
    pre_dir, results_root = Path(pre_dir), Path(results_root)
    with open(pre_dir / MANIFEST_FILE) as f:
        manifest = json.load(f)
    for name, sha in manifest["files"].items():
        if _sha_file(pre_dir / name) != sha:
            raise LabelCheckFailure(f"{name} is not the file its manifest recorded")
    if manifest["failures"]:
        raise LabelCheckFailure(f"the label tables recorded failures: {manifest['failures']}")
    if manifest["run"] != inp.run:
        raise LabelCheckFailure(f"the tables are of run {manifest['run']!r}, not {inp.run!r}")
    out: dict[str, Any] = {"run": inp.run, "label_tables_commits": manifest["commits"]}
    L = [f"# Label-only checks: the panels' documents, the 2- and 4-token merge sets, the erased sets, the removed label ({inp.run})", "",
         f"Label tables built on CPU at commit {manifest['commits'].get('project', '?')[:12]} (dirty flag {manifest['commits'].get('dirty')}), {inp.draws} draws, master seed {inp.master_seed}.", ""]
    # ---- the panels' document index
    if doc_dir is not None:
        doc_dir = Path(doc_dir)
        with open(doc_dir / DOC_MANIFEST_FILE) as f:
            dman = json.load(f)
        for name, sha in dman["files"].items():
            if _sha_file(doc_dir / name) != sha:
                raise LabelCheckFailure(f"{name} is not the file its manifest recorded")
        with open(results_root / "data" / "labeled_manifest.json") as f:
            labeled = json.load(f)
        with open(results_root / "grid" / "analysis" / inp.run / "s9b" / "panel_manifest.json") as f:
            cached_panels = json.load(f)["panels"]  # the record of the panels whose label caches exist
        held = {}
        for label, panel in PANEL_SOURCES.items():
            got = dman["panels"][panel]
            if not got["rows_equal"]:
                raise LabelCheckFailure(f"{panel}: its rows were not all equal to the rebuilt stream")
            want = [w for w in (labeled["sets"].get(panel, {}).get("sha256_ids"), cached_panels.get(panel, {}).get("set_sha256_ids")) if w is not None]
            if not want or any(w != got["sha256_ids"] for w in want):
                raise LabelCheckFailure(f"{panel}: sha256_ids {got['sha256_ids']} against the committed {want}")
            held[panel] = len(want)
        if not all(p["rows_equal_to_tokenize_documents"] for p in dman["parts"].values()):
            raise LabelCheckFailure("a part C's re-run is not the authors' tokenize_documents")
        counts = pd.read_csv(doc_dir / DOC_COUNTS_FILE)
        out["document_index"] = {"panels_held_to_committed_manifests": held, "counts": counts.to_dict("records"), "parts": dman["parts"], "file_sha256": dman["file"].get("sha256")}
        L += ["## The panels' document index", "",
              "Every part C re-run equals the authors' `tokenize_documents` id for id, with the manifest's row and document counts; every panel row equals the rebuilt stream bitwise; "
              f"every panel's `sha256_ids` equals the committed manifests' ({held}).", "",
              "| panel | rows | distinct documents | rows per document (mean, max) | rows sharing a document | part C documents |", "|---|---|---|---|---|---|"]
        L += [f"| {r['panel']} | {r['rows']} | {r['distinct_documents']} | {r['rows_per_document_mean']:.3f}, {r['rows_per_document_max']} | {r['rows_sharing_a_document']} | {r['part_C_documents']} |" for r in counts.to_dict("records")]
        L += ["", "Per part C: straddling tokens, separator pieces, cut separators, end-of-text strings inside documents: " + "; ".join(
            f"{k} {v['n_straddling_tokens']}, {v['n_separator_piece_tokens']}, {v['n_cut_separators']}, {v['n_end_of_text_literals_in_documents']}" for k, v in dman["parts"].items()), ""]
    # ---- the merge sets
    committed = committed_tables(inp, results_root)
    merge = pd.read_csv(pre_dir / MERGE_SETS_FILE, dtype={"rung": str})
    nesting = pd.read_csv(pre_dir / MERGE_NESTING_FILE)
    want_cells = {c.name for c in merge_cells(inp.run, inp.draws)}
    if set(merge["cell"]) != want_cells or merge["cell"].duplicated().any():
        raise LabelCheckFailure(f"{MERGE_SETS_FILE} does not hold exactly the merge-size cells")
    if not (nesting["positions_nested"].all() and nesting["sets_nested"].all()):
        raise LabelCheckFailure("a merge-size chain is not nested")
    held_merge = hold_to_committed(merge[merge["committed_rung"]], committed, "merge sets", relative_to=results_root.parent)
    new = merge[merge["rung"].isin(NEW_RUNGS)]
    n_on = new[new["control"] == "none"].groupby(["eval_set", "pool", "rung"])["n_on"].agg(["mean", "min", "max"]).reset_index()
    per_draw = {f"{es} {pool} {r}": [int(v) for v in g.sort_values("draw")["n_on"]] for (es, pool, r), g in new[new["control"] == "none"].groupby(["eval_set", "pool", "rung"])}
    out["merge_sets"] = {"held": held_merge, "n_chains": int(len(nesting)), "n_on_per_draw": per_draw, "n_on_summary": n_on.to_dict("records")}
    L += ["## The merge sets at 2 and 4 donor tokens", "",
          f"- Donor positions at 1, 2, 4, 8 tokens strictly nested for every pool and draw, and the named sets nested ({int((nesting['control'] == 'none').sum())} real-merge chains); "
          f"the plain and marginal controls of D_unif on E nested ({int((nesting['control'] != 'none').sum())} chains); each control's matched set is the real merge's; the D_unif sets on E_lab are E's at every draw and rung.",
          f"- The rebuilt sets at rungs \"1\" (1 token) and \"2\" (8 tokens) equal the committed cells' by SHA-256: {held_merge['n_equal']} cells ({held_merge['stores']}).", "",
          "n_on per draw of the real merge (the number of components the donor tokens name):", "", "| set | donors | 2 tokens (T2) | 4 tokens (T4) |", "|---|---|---|---|"]
    for es, pool in [("E", "D_unif")] + [("E_lab", p) for p in POOLS]:
        a, b = per_draw[f"{es} {pool} T2"], per_draw[f"{es} {pool} T4"]
        L.append(f"| {es} | {pool} | {', '.join(map(str, a))} (mean {np.mean(a):.1f}) | {', '.join(map(str, b))} (mean {np.mean(b):.1f}) |")
    L.append("")
    # ---- the erased sets
    erased = pd.read_csv(pre_dir / ERASED_SETS_FILE)
    held_erased = hold_to_committed(erased, committed, "erased sets", relative_to=results_root.parent)
    out["erased_sets"] = {"held": held_erased, "code_leaning": manifest["code_leaning"]}
    L += ["## The erased sets", "", f"- The group's sets at {', '.join(str(n) for n in inp.edit_sizes)} members and their twins under {inp.draws} draws equal the committed cells' by SHA-256: "
          f"{held_erased['n_equal']} cells ({held_erased['stores']}). Group {manifest['code_leaning']['n_group']}, wide set {manifest['code_leaning']['n_wide']}.", ""]
    # ---- the removed label
    omega = pd.read_csv(pre_dir / OMEGA_FILE)
    omega_e = pd.read_csv(pre_dir / OMEGA_E_LAB_FILE)
    if set(omega_e["cell"]) != set(erased["cell"]):
        raise LabelCheckFailure(f"{OMEGA_E_LAB_FILE} does not hold every erased set")
    val = e_lab_omega_validation(omega_e, committed)
    val.to_csv(pre_dir / "removed_label_E_lab_validation.csv", index=False, lineterminator="\n")
    order = {int(n): list(g.sort_values("omega_group", ascending=False)["source"]) for n, g in omega.groupby("size")}
    v = {"max_abs_difference": float(val["max_abs_difference"].max()), "max_relative_difference": float(val["max_relative_difference"].max()),
         "n_texts_bitwise_equal_in_float32": int(val["n_texts_bitwise_equal_in_float32"].sum()), "n_texts": int(val["n_texts"].sum())}
    out["removed_label"] = {"table": omega.to_dict("records"), "order_by_omega_group": order, "e_lab_validation": v}
    L += ["## The removed label on the panels (descriptive)", "",
          "omega: the sum over the erased components of their labels, averaged over a row's positions and then over the rows.", "",
          f"| panel | members | omega, group | omega, twins (mean of {inp.draws} draws) | twins' draws, min to max | rank by the group's omega |", "|---|---|---|---|---|---|"]
    L += [f"| {r['panel']} | {r['size']} | {r['omega_group']:.4f} | {r['omega_twins']:.4f} | {r['omega_twins_draw_min']:.4f} to {r['omega_twins_draw_max']:.4f} | {r['rank_by_omega_group']} |" for r in omega.sort_values(["size", "rank_by_omega_group"]).to_dict("records")]
    L += ["", "Order by the group's omega: " + "; ".join(f"{n} members: {' > '.join(o)}" for n, o in order.items()), "",
          f"Validation on E_lab ({len(val)} cells, the cache's omega against the loop's in the committed store, per text): largest absolute difference {v['max_abs_difference']:.3g}, "
          f"largest relative {v['max_relative_difference']:.3g}; {v['n_texts_bitwise_equal_in_float32']} of {v['n_texts']} texts equal in float32. Reported, not asserted.", ""]
    with open(pre_dir / CHECKS_JSON, "w") as f:
        json.dump(out, f, indent=2, sort_keys=True, default=str)
    (pre_dir / CHECKS_MD).write_text("\n".join(L))
    log("\n".join(L))
    return out
