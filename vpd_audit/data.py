"""The stream sets E and D_unif and the eight SimpleStories sequences for the smoke.

Rows 0 to 2047 of the `val` split of `danbraunai/pile-uncopyrighted-tok-shuffled`, read in
stream order without the authors' buffered shuffle. Every raw row must have exactly 513 ids;
each is truncated to its first 512 as `param_decomp/data.py` lines 227 to 233 do, and the
saved row is asserted elementwise equal to the raw row's first 512 ids. Rows 0 to 1023 are E,
rows 1024 to 2047 are D_unif. Each set is saved as an int32 array with its row indices and a
SHA-256 hash, which the loader verifies. No beginning-of-sequence token is added anywhere.
"""

from __future__ import annotations

import hashlib
import json
import time
from pathlib import Path
from typing import Any

import numpy as np

from vpd_audit import env
from vpd_audit.constants import RAW_ROW_LEN, SEQ_LEN

STREAM_DATASET = "danbraunai/pile-uncopyrighted-tok-shuffled"
STREAM_SPLIT = "val"
STREAM_COLUMN = "input_ids"
STREAM_SETS: dict[str, tuple[int, int]] = {"E": (0, 1024), "D_unif": (1024, 2048)}
N_STREAM_ROWS = 2048


def hash_ids(ids: np.ndarray) -> str:
    """SHA-256 of the C-contiguous int32 bytes of a (N, T) id array."""
    arr = np.ascontiguousarray(ids, dtype=np.int32)
    return hashlib.sha256(arr.tobytes()).hexdigest()


def truncate_row(raw: np.ndarray, n_ctx: int = SEQ_LEN) -> np.ndarray:
    """`x[col][:n_ctx]`, as the authors' loader truncates a tokenized row."""
    return raw[:n_ctx]


def _set_paths(name: str, sets_dir: Path) -> tuple[Path, Path]:
    return sets_dir / f"{name}.npz", sets_dir / f"{name}.json"


def save_set(name: str, ids: np.ndarray, row_indices: np.ndarray, meta: dict[str, Any], sets_dir: Path) -> Path:
    assert ids.ndim == 2 and ids.shape[1] == SEQ_LEN, ids.shape
    assert row_indices.shape == (ids.shape[0],)
    ids = np.ascontiguousarray(ids, dtype=np.int32)
    row_indices = np.ascontiguousarray(row_indices, dtype=np.int64)
    npz, js = _set_paths(name, sets_dir)
    sets_dir.mkdir(parents=True, exist_ok=True)
    tmp = npz.with_suffix(".npz.tmp")
    with open(tmp, "wb") as f:
        np.savez(f, ids=ids, row_indices=row_indices)
    tmp.replace(npz)
    record = {
        "name": name,
        "shape": list(ids.shape),
        "dtype": "int32",
        "sha256_ids": hash_ids(ids),
        "sha256_row_indices": hashlib.sha256(row_indices.tobytes()).hexdigest(),
        "row_indices_first": int(row_indices[0]),
        "row_indices_last": int(row_indices[-1]),
        **meta,
    }
    with open(js, "w") as f:
        json.dump(record, f, indent=2, sort_keys=True)
    return npz


def load_set(name: str, sets_dir: Path = env.SETS_DIR) -> tuple[np.ndarray, np.ndarray, dict[str, Any]]:
    """Load a saved set, verifying its hashes. Returns (ids, row_indices, record)."""
    npz, js = _set_paths(name, sets_dir)
    if not npz.is_file() or not js.is_file():
        raise FileNotFoundError(f"set {name!r} not found under {sets_dir}; run `vpd-audit prepare-data`")
    with open(js) as f:
        record = json.load(f)
    with np.load(npz) as z:
        ids = np.ascontiguousarray(z["ids"], dtype=np.int32)
        row_indices = np.ascontiguousarray(z["row_indices"], dtype=np.int64)
    assert list(ids.shape) == record["shape"], (ids.shape, record["shape"])
    assert ids.shape[1] == SEQ_LEN
    digest = hash_ids(ids)
    if digest != record["sha256_ids"]:
        raise RuntimeError(f"set {name!r}: ids hash {digest} != recorded {record['sha256_ids']}")
    rdigest = hashlib.sha256(row_indices.tobytes()).hexdigest()
    if rdigest != record["sha256_row_indices"]:
        raise RuntimeError(f"set {name!r}: row-index hash mismatch")
    return ids, row_indices, record


def prepare_stream_sets(sets_dir: Path = env.SETS_DIR, *, log: Any = print) -> dict[str, Path]:
    """Read rows 0 to 2047 of the `val` stream in order and save E and D_unif."""
    from datasets import load_dataset

    t0 = time.time()
    ds = load_dataset(STREAM_DATASET, split=STREAM_SPLIT, streaming=True)
    rows = np.empty((N_STREAM_ROWS, SEQ_LEN), dtype=np.int32)
    it = iter(ds)
    for i in range(N_STREAM_ROWS):
        row = next(it)
        raw = np.asarray(row[STREAM_COLUMN])
        assert raw.ndim == 1 and raw.shape[0] == RAW_ROW_LEN, f"row {i}: raw row has shape {raw.shape}, expected ({RAW_ROW_LEN},)"
        saved = truncate_row(raw)
        assert saved.shape == (SEQ_LEN,), f"row {i}: truncated row has shape {saved.shape}"
        assert np.array_equal(saved, raw[:SEQ_LEN]), f"row {i}: saved row differs from the raw row's first {SEQ_LEN} ids"
        assert raw.min() >= 0, f"row {i}: negative id"
        rows[i] = saved
        if (i + 1) % 512 == 0:
            log(f"[prepare-data] {i + 1}/{N_STREAM_ROWS} rows read ({time.time() - t0:.1f} s)")
    out: dict[str, Path] = {}
    meta = {"dataset": STREAM_DATASET, "split": STREAM_SPLIT, "column": STREAM_COLUMN, "raw_row_len": RAW_ROW_LEN,
            "order": "stream order, no shuffle", "bos_added": False, "prepared_at": time.strftime("%Y-%m-%dT%H:%M:%S%z")}
    for name, (a, b) in STREAM_SETS.items():
        out[name] = save_set(name, rows[a:b], np.arange(a, b), meta, sets_dir)
        ids, row_indices, record = load_set(name, sets_dir)  # verifies the hashes on the way back
        assert np.array_equal(ids, rows[a:b]) and row_indices[0] == a and row_indices[-1] == b - 1
        log(f"[prepare-data] {name}: rows {a}..{b - 1}, shape {ids.shape}, sha256 {record['sha256_ids'][:16]}... -> {out[name]}")
    log(f"[prepare-data] done in {time.time() - t0:.1f} s")
    return out


# ----------------------------------------------------------------------------- SimpleStories


SIMPLESTORIES_SET = "simplestories_smoke"


def prepare_simplestories_rows(n: int, run_config: Any, sets_dir: Path = env.SETS_DIR, *, log: Any = print) -> np.ndarray:
    """The first `n` rows of 512 tokens that the authors' tokenization produces from the
    dataset the SimpleStories run's `final_config.yaml` names, taken in order for the smoke.

    Uses the authors' `tokenize_and_concatenate` with the run's tokenizer, `add_bos_token=False`,
    and the same `to_lower` rule as their loader. That function's `to_lower` only rewrites the
    lowercased end-of-text literal; it does not lowercase the text (the dataset is lowercase).
    """
    from datasets import load_dataset
    from transformers import AutoTokenizer

    from param_decomp.data import tokenize_and_concatenate

    tc = run_config.task_config
    name = f"{SIMPLESTORIES_SET}_{n}"
    try:
        ids, _, record = load_set(name, sets_dir)
        if record.get("dataset") == tc.dataset_name and record.get("tokenizer") == run_config.tokenizer_name:
            return ids
    except FileNotFoundError:
        pass
    assert tc.max_seq_len == SEQ_LEN, tc.max_seq_len
    tokenizer = AutoTokenizer.from_pretrained(run_config.tokenizer_name)
    ds = load_dataset(tc.dataset_name, split=tc.eval_data_split, streaming=True)
    to_lower = "SimpleStories" in tc.dataset_name
    tok = tokenize_and_concatenate(ds, tokenizer, column_name=tc.column_name, max_length=tc.max_seq_len,
                                   add_bos_token=False, to_lower=to_lower)
    rows = []
    for ex in tok:
        r = np.asarray(ex["input_ids"])
        assert r.shape == (SEQ_LEN,), r.shape
        rows.append(r)
        if len(rows) == n:
            break
    ids = np.stack(rows).astype(np.int32)
    meta = {"dataset": tc.dataset_name, "split": tc.eval_data_split, "column": tc.column_name,
            "tokenizer": run_config.tokenizer_name, "to_lower": to_lower, "bos_added": False, "order": "first rows in order",
            "prepared_at": time.strftime("%Y-%m-%dT%H:%M:%S%z")}
    save_set(name, ids, np.arange(n), meta, sets_dir)
    log(f"[simplestories] saved {n} rows from {tc.dataset_name}/{tc.eval_data_split} with {run_config.tokenizer_name}")
    return ids


# ----------------------------------------------------------------------------- the labeled sets

LABELED_REPO = "monology/pile-uncopyrighted"
LABELED_FILE = "val.jsonl.zst"
LABELED_TOKENIZER = "EleutherAI/gpt-neox-20b"
LABELED_MAX_LENGTH = 513  # the stream's row length; truncated to the first 512 as the stream's rows are
VOCAB_SIZE = 50277
DONOR_LABELS = ("Github", "Pile-CC", "Wikipedia (en)")  # part A donors, part B evaluation
OTHER_LABELS = ("Pile-CC", "Wikipedia (en)", "StackExchange", "ArXiv")  # 64 rows each from part B
FALLBACK_LABEL = "PubMed Abstracts"
LABELED_SET_SIZES = {"D_code": 512, "D_prose_each": 256, "E_lab_github": 256, "E_lab_other_each": 64}
CALIB_N = 2000  # per class, fit half then report half (1,000 pre-registered, recorded deviation)
PANEL_N = 200


def labeled_file_path() -> Path:
    from huggingface_hub import hf_hub_download

    return Path(hf_hub_download(repo_id=LABELED_REPO, filename=LABELED_FILE, repo_type="dataset"))


def read_labeled_documents(path: Path, *, log: Any = print) -> dict[str, list[str]]:
    """Stream the zstd-compressed JSONL line by line; documents grouped by `meta.pile_set_name`."""
    import io

    import zstandard

    docs: dict[str, list[str]] = {}
    t0 = time.time()
    n = 0
    with open(path, "rb") as fh:
        reader = io.TextIOWrapper(zstandard.ZstdDecompressor().stream_reader(fh), encoding="utf-8")
        for line in reader:
            if not line.strip():
                continue
            rec = json.loads(line)
            docs.setdefault(rec["meta"]["pile_set_name"], []).append(rec["text"])
            n += 1
            if n % 50000 == 0:
                log(f"[labeled] {n} documents read ({time.time() - t0:.0f} s)")
    log(f"[labeled] {n} documents, {len(docs)} labels, in {time.time() - t0:.0f} s")
    return docs


def split_documents(docs: list[str], label: str, master_seed: int) -> dict[str, list[int]]:
    """The seeded permutation of a label's documents, split into three equal parts by document count, in order:
    A (donor), B (evaluation), C (calibration). Seed tuple (master, "docs", label)."""
    from vpd_audit.masks import seed_from_tuple

    rng = np.random.default_rng(seed_from_tuple((master_seed, "docs", label)))
    perm = rng.permutation(len(docs))
    a, b, c = np.array_split(perm, 3)
    return {"A": a.tolist(), "B": b.tolist(), "C": c.tolist()}


def tokenize_documents(texts: list[str], tokenizer: Any, *, num_proc: int = 1) -> np.ndarray:
    """The authors' `tokenize_and_concatenate` (513-token rows, no BOS, the map's default batch of 1,000 documents,
    20 chunks per batch), then each row truncated to its first 512 ids with the stream's raw-row assertion."""
    from datasets import Dataset

    from param_decomp.data import tokenize_and_concatenate

    if not texts:
        return np.zeros((0, SEQ_LEN), dtype=np.int32)
    ds = Dataset.from_dict({"text": texts})
    tok = tokenize_and_concatenate(ds, tokenizer, column_name="text", max_length=LABELED_MAX_LENGTH, add_bos_token=False, num_proc=num_proc, to_lower=False)
    rows = []
    for ex in tok:
        raw = np.asarray(ex["input_ids"])
        assert raw.ndim == 1 and raw.shape[0] == LABELED_MAX_LENGTH, raw.shape
        saved = truncate_row(raw)
        assert saved.shape == (SEQ_LEN,) and np.array_equal(saved, raw[:SEQ_LEN])
        rows.append(saved)
    out = np.stack(rows).astype(np.int32) if rows else np.zeros((0, SEQ_LEN), dtype=np.int32)
    assert out.min(initial=0) >= 0 and out.max(initial=0) < VOCAB_SIZE, "an id at or above the vocabulary size"
    return out


def row_hashes(ids: np.ndarray) -> list[str]:
    return [hashlib.sha256(np.ascontiguousarray(r, dtype=np.int32).tobytes()).hexdigest() for r in ids]


def assert_pairwise_disjoint(sets: dict[str, np.ndarray]) -> dict[str, int]:
    """Pairwise disjointness of the sets on per-row SHA-256; returns the sizes of the pairwise intersections (all 0)."""
    hashes = {name: set(row_hashes(ids)) for name, ids in sets.items()}
    out: dict[str, int] = {}
    names = sorted(hashes)
    for i, a in enumerate(names):
        for b in names[i + 1 :]:
            n = len(hashes[a] & hashes[b])
            out[f"{a} & {b}"] = n
            assert n == 0, f"{a} and {b} share {n} row(s)"
    return out


def prepare_labeled_sets(sets_dir: Path = env.SETS_DIR, *, master_seed: int = 0, num_proc: int = 1, results_dir: Path | None = None, log: Any = print) -> dict[str, Any]:
    """The labeled sets, the calibration rows of the code filter, and sets/labeled_manifest.json."""
    from transformers import AutoTokenizer

    from vpd_audit.artifacts import sha256_file
    from vpd_audit.masks import seed_from_tuple

    t0 = time.time()
    path = labeled_file_path()
    file_sha, file_size = sha256_file(path), path.stat().st_size
    log(f"[labeled] {LABELED_REPO}/{LABELED_FILE}: {file_size} bytes, sha256 {file_sha[:16]}...")
    docs = read_labeled_documents(path, log=log)
    labels = sorted(docs)
    manifest: dict[str, Any] = {"file": {"repo": LABELED_REPO, "name": LABELED_FILE, "sha256": file_sha, "bytes": file_size}, "tokenizer": LABELED_TOKENIZER,
                                "max_length": LABELED_MAX_LENGTH, "master_seed": master_seed, "labels": labels,
                                "documents": {lab: {"n_docs": len(docs[lab]), "chars": int(sum(len(t) for t in docs[lab]))} for lab in labels},
                                "split": "seeded permutation (master, 'docs', label) into three equal parts by document count: A donor, B evaluation, C calibration (a recorded deviation from the pre-registered halves)",
                                "parts": {}, "sets": {}, "prepared_at": time.strftime("%Y-%m-%dT%H:%M:%S%z")}
    for lab in DONOR_LABELS + (FALLBACK_LABEL,) + tuple(OTHER_LABELS):
        assert lab in docs, f"label {lab!r} not in the file; labels: {labels}"
    tokenizer = AutoTokenizer.from_pretrained(LABELED_TOKENIZER)
    eos = tokenizer.eos_token_id
    assert tokenizer.encode("<|endoftext|>", add_special_tokens=False) == [eos] and eos < VOCAB_SIZE
    manifest["eos_token_id"] = int(eos)
    parts = {lab: split_documents(docs[lab], lab, master_seed) for lab in labels}
    needed = {(lab, "A") for lab in DONOR_LABELS} | {(lab, "B") for lab in set(DONOR_LABELS) | set(OTHER_LABELS) | {FALLBACK_LABEL}} | {(lab, "C") for lab in labels}
    tokens: dict[tuple[str, str], np.ndarray] = {}
    for lab, part in sorted(needed):
        texts = [docs[lab][i] for i in parts[lab][part]]
        t1 = time.time()
        ids = tokenize_documents(texts, tokenizer, num_proc=num_proc)
        tokens[(lab, part)] = ids
        chars = int(sum(len(t) for t in texts))
        manifest["parts"][f"{lab}/{part}"] = {"n_docs": len(texts), "chars": chars, "rows": int(ids.shape[0]), "tokens_in_rows": int(ids.shape[0] * LABELED_MAX_LENGTH),
                                              "tokens_per_char": (ids.shape[0] * LABELED_MAX_LENGTH / chars) if chars else None,
                                              "fraction_rows_starting_with_eot": float((ids[:, 0] == eos).mean()) if ids.shape[0] else None, "seconds": time.time() - t1}
        log(f"[labeled] {lab}/{part}: {len(texts)} docs, {chars} chars -> {ids.shape[0]} rows in {time.time() - t1:.0f} s")
    meta_base = {"source": f"{LABELED_REPO}/{LABELED_FILE}", "file_sha256": file_sha, "tokenizer": LABELED_TOKENIZER, "max_length": LABELED_MAX_LENGTH,
                 "bos_added": False, "master_seed": master_seed, "prepared_at": manifest["prepared_at"]}

    def take(lab: str, part: str, n: int, start: int = 0) -> tuple[np.ndarray, np.ndarray]:
        ids = tokens[(lab, part)]
        assert ids.shape[0] >= start + n, f"{lab}/{part} has {ids.shape[0]} rows, need {start + n}"
        return ids[start : start + n], np.arange(start, start + n)

    built: dict[str, np.ndarray] = {}

    def save(name: str, ids: np.ndarray, row_idx: np.ndarray, **meta: Any) -> None:
        save_set(name, ids, row_idx, {**meta_base, **meta}, sets_dir)
        built[name] = ids
        manifest["sets"][name] = {"rows": int(ids.shape[0]), "sha256_ids": hash_ids(ids), "fraction_rows_starting_with_eot": float((ids[:, 0] == eos).mean()), **meta}

    # the domain sets, rows in tokenization order
    ids, ri = take("Github", "A", LABELED_SET_SIZES["D_code"])
    save("D_code", ids, ri, label="Github", part="A", taken=f"first {LABELED_SET_SIZES['D_code']} rows of part A")
    p1, r1 = take("Pile-CC", "A", LABELED_SET_SIZES["D_prose_each"])
    p2, r2 = take("Wikipedia (en)", "A", LABELED_SET_SIZES["D_prose_each"])
    save("D_prose", np.concatenate([p1, p2]), np.concatenate([r1, r2]), labels=["Pile-CC", "Wikipedia (en)"], part="A", taken="first 256 rows of each label's part A",
         strata=["Pile-CC"] * len(r1) + ["Wikipedia (en)"] * len(r2))
    ids, ri = take("Github", "B", LABELED_SET_SIZES["E_lab_github"])
    save("E_lab_github", ids, ri, label="Github", part="B", taken=f"first {LABELED_SET_SIZES['E_lab_github']} rows of part B")
    other_ids, other_ri, other_strata, fills = [], [], [], {}
    for lab in OTHER_LABELS:
        avail = tokens[(lab, "B")].shape[0]
        n = min(LABELED_SET_SIZES["E_lab_other_each"], avail)
        ids, ri = take(lab, "B", n)
        other_ids.append(ids)
        other_ri.append(ri)
        other_strata += [lab] * n
        if n < LABELED_SET_SIZES["E_lab_other_each"]:
            fills[lab] = LABELED_SET_SIZES["E_lab_other_each"] - n
    fill_start = 0
    for lab, short in fills.items():
        ids, ri = take(FALLBACK_LABEL, "B", short, fill_start)
        fill_start += short
        other_ids.append(ids)
        other_ri.append(ri)
        other_strata += [f"{FALLBACK_LABEL} (fill for {lab})"] * short
        log(f"[labeled] {lab} part B short by {short}; filled from {FALLBACK_LABEL} part B")
    save("E_lab_other", np.concatenate(other_ids), np.concatenate(other_ri), labels=list(OTHER_LABELS), part="B", fills=fills, strata=other_strata)
    e_lab_ids = np.concatenate([built["E_lab_github"], built["E_lab_other"]])
    e_lab_strata = ["Github"] * built["E_lab_github"].shape[0] + other_strata
    save("E_lab", e_lab_ids, np.arange(e_lab_ids.shape[0]), composition="E_lab_github then E_lab_other", strata=e_lab_strata)
    with open(sets_dir / "E_lab.strata.json", "w") as f:
        json.dump({"strata": e_lab_strata, "sha256_ids": hash_ids(e_lab_ids)}, f, indent=2)
    assert e_lab_ids.shape[0] == 512, e_lab_ids.shape

    # the calibration rows of the code filter, from part C
    gh_c = tokens[("Github", "C")]
    rng = np.random.default_rng(seed_from_tuple((master_seed, "calib", "Github")))
    draw = rng.choice(gh_c.shape[0], size=CALIB_N, replace=False)
    save("calib_github", gh_c[draw], draw, label="Github", part="C", draw="without replacement, seed (master, 'calib', 'Github'); fit = first 1000 of the draw, report = last 1000",
         fit_rows=list(range(CALIB_N // 2)), report_rows=list(range(CALIB_N // 2, CALIB_N)))
    pooled = [(lab, i) for lab in labels if lab != "Github" for i in range(tokens[(lab, "C")].shape[0])]
    rng = np.random.default_rng(seed_from_tuple((master_seed, "calib", "other")))
    draw = rng.choice(len(pooled), size=CALIB_N, replace=False)
    other_rows = np.stack([tokens[(pooled[j][0], "C")][pooled[j][1]] for j in draw])
    other_labels = [pooled[j][0] for j in draw]
    save("calib_other", other_rows, draw, part="C", draw="uniform without replacement over the pooled part-C rows of every non-Github label, seed (master, 'calib', 'other')",
         labels_per_row=other_labels, fit_rows=list(range(CALIB_N // 2)), report_rows=list(range(CALIB_N // 2, CALIB_N)))
    with open(sets_dir / "calib_other.labels.json", "w") as f:
        json.dump({"labels": other_labels, "sha256_ids": hash_ids(other_rows)}, f)
    drawn = {(pooled[j][0], pooled[j][1]) for j in draw}
    panels: dict[str, int] = {}
    for lab in labels:
        if lab == "Github":
            continue
        cand = [i for i in range(tokens[(lab, "C")].shape[0]) if (lab, i) not in drawn]
        rng = np.random.default_rng(seed_from_tuple((master_seed, "calib", lab)))
        pick = np.sort(rng.choice(len(cand), size=min(PANEL_N, len(cand)), replace=False)) if cand else np.zeros(0, dtype=np.int64)
        idx = np.asarray([cand[j] for j in pick], dtype=np.int64)
        if idx.size == 0:
            panels[lab] = 0
            continue
        name = "panel_" + "".join(ch if ch.isalnum() else "_" for ch in lab)
        save(name, tokens[(lab, "C")][idx], idx, label=lab, part="C", draw="up to 200 part-C rows not already drawn for calib_other, seed (master, 'calib', label)")
        panels[lab] = int(idx.size)
    manifest["panels"] = panels
    # the token-share census from part C: each label's tokens per character, and its share of the file's tokens
    tpc = {lab: manifest["parts"][f"{lab}/C"]["tokens_per_char"] for lab in labels}
    est_tokens = {lab: (manifest["documents"][lab]["chars"] * tpc[lab]) if tpc[lab] else 0.0 for lab in labels}
    total = sum(est_tokens.values())
    manifest["token_share"] = {"tokens_per_char_part_C": tpc, "estimated_tokens": est_tokens, "w": {lab: (v / total if total else None) for lab, v in est_tokens.items()}}
    # the assertions
    E_ids, _, _ = load_set("E", sets_dir)
    D_unif_ids, _, _ = load_set("D_unif", sets_dir)
    check = {"E": E_ids, "D_unif": D_unif_ids, **{k: v for k, v in built.items() if k not in ("E_lab_github", "E_lab_other")}}
    manifest["pairwise_intersections"] = assert_pairwise_disjoint(check)
    for name, ids in built.items():
        assert ids.max() < VOCAB_SIZE and ids.min() >= 0
    manifest["seconds"] = time.time() - t0
    with open(sets_dir / "labeled_manifest.json", "w") as f:
        json.dump(manifest, f, indent=2, sort_keys=True, default=lambda o: o.tolist() if isinstance(o, np.ndarray) else str(o))
    if results_dir is not None:
        results_dir.mkdir(parents=True, exist_ok=True)
        with open(results_dir / "labeled_manifest.json", "w") as f:
            json.dump(manifest, f, indent=2, sort_keys=True, default=lambda o: o.tolist() if isinstance(o, np.ndarray) else str(o))
    log(f"[labeled] done in {time.time() - t0:.0f} s: sets {sorted(built)}; E_lab starts with EOT in {manifest['sets']['E_lab']['fraction_rows_starting_with_eot']:.4f} of rows")
    return manifest
