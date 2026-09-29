"""The stand-in sets and filter for the SimpleStories decomposition, used first by the identities on
that model and then by the dry run of the grid.

Rows are taken in order from the split the run's config names (`prepare_simplestories_rows`): E_dry rows 0 to 63;
D_unif_dry rows 64 to 191 (128, so that rung 7's 64 sequences are a proper subset of rung 8); calibration rows 192
to 319; the domain pools from row 320 on until filled, D_code_dry the first 128 "dialogue" rows and D_prose_dry the
first 64 "narration" rows; E_lab_dry after the pools, 32 dialogue and 32 narration rows with strata. The stand-in
filter runs through the same rule shape as the heuristic code filter with a different feature pair and pseudo-label: the fraction of
characters that are `"` and the fraction of sentences ending in `?` or `!`; the pseudo-label "dialogue" is a `"`
fraction above the median of the 128 calibration rows. The label is a function of the first feature, so the
calibration finds J about 1 near the median; that circularity is harmless, since the dry run exercises code paths
and learns nothing about the decomposition. If a range yields fewer rows than a set needs, it is extended and the
extension recorded.
"""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

import numpy as np

from vpd_audit import env
from vpd_audit.data import hash_ids, load_set, prepare_simplestories_rows, save_set

RANGES = {"E_dry": (0, 64), "D_unif_dry": (64, 192), "calib_dry": (192, 320)}
POOL_START = 320
SIZES = {"D_code_dry": 128, "D_prose_dry": 64, "E_lab_dry_each": 32}


def stand_in_features(text: str) -> tuple[float, float]:
    n = len(text)
    f_quote = text.count('"') / n if n else 0.0
    sentences = [s for s in text.replace("!", ".!").replace("?", ".?").split(".") if s.strip()]
    ends = sum(1 for s in sentences if s.strip().endswith(("?", "!")))
    f_qe = ends / len(sentences) if sentences else 0.0
    return f_quote, f_qe


def prepare_dry_sets(*, master_seed: int = 0, sets_dir: Path = env.SETS_DIR, n_rows: int = 1024, log: Any = print) -> dict[str, Any]:
    from transformers import AutoTokenizer

    from vpd_audit.artifacts import load_run_config

    t0 = time.time()
    cfg = load_run_config("simplestories")
    ids = prepare_simplestories_rows(n_rows, cfg, sets_dir, log=log)
    tok = AutoTokenizer.from_pretrained(cfg.tokenizer_name)
    eos = tok.eos_token_id
    manifest: dict[str, Any] = {"tokenizer": cfg.tokenizer_name, "n_rows_available": int(ids.shape[0]), "ranges": dict(RANGES), "pool_start": POOL_START, "sets": {}, "extensions": {}}
    meta = {"source": f"simplestories rows in order ({cfg.task_config.dataset_name}/{cfg.task_config.eval_data_split})", "tokenizer": cfg.tokenizer_name, "bos_added": False, "master_seed": master_seed}

    def save(name: str, rows: np.ndarray, idx: np.ndarray, **extra: Any) -> None:
        save_set(name, rows, idx, {**meta, **extra}, sets_dir)
        manifest["sets"][name] = {"rows": int(rows.shape[0]), "sha256_ids": hash_ids(rows), "row_indices": [int(idx[0]), int(idx[-1])], **{k: v for k, v in extra.items() if k != "strata"}}

    for name, (a, b) in RANGES.items():
        if name == "calib_dry":
            continue
        save(name, ids[a:b], np.arange(a, b))
    # the stand-in filter: the pseudo-label from the calibration rows' median quote fraction
    a, b = RANGES["calib_dry"]
    texts = [tok.decode([t for t in row if t != eos], skip_special_tokens=False, clean_up_tokenization_spaces=False) for row in ids[a:b]]
    feats = np.asarray([stand_in_features(t) for t in texts])
    median_quote = float(np.median(feats[:, 0]))
    save("calib_dry", ids[a:b], np.arange(a, b), features=feats.tolist(), median_quote=median_quote, pseudo_label="dialogue if the quote fraction exceeds the median")
    manifest["stand_in_filter"] = {"features": ["fraction of characters that are a double quote", "fraction of sentences ending in ? or !"], "pseudo_label": "dialogue := quote fraction > median of the 128 calibration rows", "median_quote": median_quote}
    # the domain pools from row 320 on, until filled; E_lab_dry after them
    code_rows, prose_rows, code_idx, prose_idx = [], [], [], []
    r = POOL_START
    while (len(code_rows) < SIZES["D_code_dry"] or len(prose_rows) < SIZES["D_prose_dry"]) and r < ids.shape[0]:
        text = tok.decode([t for t in ids[r] if t != eos], skip_special_tokens=False, clean_up_tokenization_spaces=False)
        q, _ = stand_in_features(text)
        if q > median_quote and len(code_rows) < SIZES["D_code_dry"]:
            code_rows.append(ids[r])
            code_idx.append(r)
        elif q <= median_quote and len(prose_rows) < SIZES["D_prose_dry"]:
            prose_rows.append(ids[r])
            prose_idx.append(r)
        r += 1
    assert len(code_rows) == SIZES["D_code_dry"] and len(prose_rows) == SIZES["D_prose_dry"], (len(code_rows), len(prose_rows), r)
    manifest["extensions"]["pools_end_row"] = r
    save("D_code_dry", np.stack(code_rows), np.asarray(code_idx), pseudo_label="dialogue")
    save("D_prose_dry", np.stack(prose_rows), np.asarray(prose_idx), pseudo_label="narration")
    lab_rows, lab_idx, strata = [], [], []
    n_d = n_n = 0
    while (n_d < SIZES["E_lab_dry_each"] or n_n < SIZES["E_lab_dry_each"]) and r < ids.shape[0]:
        text = tok.decode([t for t in ids[r] if t != eos], skip_special_tokens=False, clean_up_tokenization_spaces=False)
        q, _ = stand_in_features(text)
        if q > median_quote and n_d < SIZES["E_lab_dry_each"]:
            lab_rows.append(ids[r]); lab_idx.append(r); strata.append("dialogue"); n_d += 1
        elif q <= median_quote and n_n < SIZES["E_lab_dry_each"]:
            lab_rows.append(ids[r]); lab_idx.append(r); strata.append("narration"); n_n += 1
        r += 1
    assert n_d == n_n == SIZES["E_lab_dry_each"], (n_d, n_n, r)
    manifest["extensions"]["e_lab_end_row"] = r
    order = np.argsort([0 if s == "dialogue" else 1 for s in strata], kind="stable")
    lab = np.stack(lab_rows)[order]
    strata_sorted = [strata[i] for i in order]
    save("E_lab_dry", lab, np.asarray(lab_idx)[order], strata=strata_sorted)
    with open(sets_dir / "E_lab_dry.strata.json", "w") as f:
        json.dump({"strata": strata_sorted, "sha256_ids": hash_ids(lab)}, f)
    # disjointness
    from vpd_audit.data import assert_pairwise_disjoint

    manifest["pairwise_intersections"] = assert_pairwise_disjoint({n: load_set(n, sets_dir)[0] for n in ("E_dry", "D_unif_dry", "calib_dry", "D_code_dry", "D_prose_dry", "E_lab_dry")})
    manifest["seconds"] = time.time() - t0
    with open(sets_dir / "dry_manifest.json", "w") as f:
        json.dump(manifest, f, indent=2, sort_keys=True)
    sizes = ", ".join(f"{k}: {v['rows']}" for k, v in manifest["sets"].items())
    log(f"[dry-sets] {sizes}; pools end at row {manifest['extensions']['pools_end_row']}, E_lab at {manifest['extensions']['e_lab_end_row']}; {time.time() - t0:.0f} s")
    return manifest
