"""The tokenizer round-trip check, CPU.

For each row of a saved set: the first and last *word-initial* tokens (a token whose decoded string begins with a
space or a newline); the span from the first to the token before the last; decode with
`skip_special_tokens=False, clean_up_tokenization_spaces=False`; re-encode with `encode(text,
add_special_tokens=False)`; compare. Rows with fewer than two word-initial tokens have no span and are skipped and
counted (must be below 1 percent). At least 97 percent of rows must match exactly; every differing row is listed
with its first differing position. Also asserted: `encode("<|endoftext|>", add_special_tokens=False) ==
[eos_token_id]`, and that the tokenizer is the one the model's configs name (the configs give the tokenizer and the
vocabulary size, 50,277, not the id itself; the id is read from the tokenizer and checked below the vocabulary).
Run on E before any labeled row is built, then on every labeled set; output results/data/round_trip.json.
"""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

import numpy as np

from vpd_audit import env
from vpd_audit.constants import SEQ_LEN
from vpd_audit.data import load_set

TOKENIZER_NAME = "EleutherAI/gpt-neox-20b"
EOT_LITERAL = "<|endoftext|>"
MATCH_MIN = 0.97
NO_SPAN_MAX = 0.01
VOCAB_SIZE = 50277


def load_tokenizer(name: str = TOKENIZER_NAME) -> Any:
    from transformers import AutoTokenizer

    return AutoTokenizer.from_pretrained(name)


def tokenizer_facts(tokenizer: Any) -> dict[str, Any]:
    """The end-of-text facts the round-trip check asserts, plus the configs' agreement on the tokenizer's name."""
    from vpd_audit.artifacts import load_run_config

    eos = tokenizer.eos_token_id
    enc = tokenizer.encode(EOT_LITERAL, add_special_tokens=False)
    assert enc == [eos], f"encode({EOT_LITERAL!r}) = {enc}, eos_token_id = {eos}"
    assert eos is not None and 0 <= eos < VOCAB_SIZE, eos
    assert tokenizer.decode([eos], skip_special_tokens=False, clean_up_tokenization_spaces=False) == EOT_LITERAL
    facts: dict[str, Any] = {"tokenizer": tokenizer.name_or_path, "eos_token_id": int(eos), "eos_token": tokenizer.eos_token, "bos_token_id": tokenizer.bos_token_id,
                             "encode_eot_literal": enc, "vocab_size_model": VOCAB_SIZE, "len_tokenizer": len(tokenizer)}
    try:
        cfg = load_run_config("main")
        facts["decomposition_config_tokenizer_name"] = cfg.tokenizer_name
        assert cfg.tokenizer_name == TOKENIZER_NAME, cfg.tokenizer_name
    except FileNotFoundError:
        facts["decomposition_config_tokenizer_name"] = None
    return facts


def word_initial_table(tokenizer: Any, vocab_size: int = VOCAB_SIZE) -> np.ndarray:
    """word_initial[id]: the token's decoded string begins with a space or a newline."""
    table = np.zeros(vocab_size, dtype=bool)
    for i in range(vocab_size):
        s = tokenizer.decode([i], skip_special_tokens=False, clean_up_tokenization_spaces=False)
        table[i] = s.startswith((" ", "\n"))
    return table


def round_trip_rows(ids: np.ndarray, tokenizer: Any, table: np.ndarray, *, max_listed: int = 50) -> dict[str, Any]:
    assert ids.ndim == 2 and ids.shape[1] == SEQ_LEN
    n = ids.shape[0]
    n_match = 0
    no_span: list[int] = []
    differing: list[dict[str, Any]] = []
    span_lengths: list[int] = []
    for r in range(n):
        row = ids[r]
        wi = np.flatnonzero(table[row])
        if wi.size < 2:
            no_span.append(r)
            continue
        a, b = int(wi[0]), int(wi[-1])  # from the first word-initial token to the token before the last
        span = row[a:b].tolist()
        span_lengths.append(len(span))
        text = tokenizer.decode(span, skip_special_tokens=False, clean_up_tokenization_spaces=False)
        back = tokenizer.encode(text, add_special_tokens=False)
        if back == span:
            n_match += 1
        else:
            first = next((i for i in range(min(len(back), len(span))) if back[i] != span[i]), min(len(back), len(span)))
            if len(differing) < max_listed:
                differing.append({"row": r, "span_start": a, "span_len": len(span), "reencoded_len": len(back), "first_differing_position_in_span": first,
                                  "first_differing_position_in_row": a + first, "original": span[max(0, first - 3) : first + 4], "reencoded": back[max(0, first - 3) : first + 4],
                                  "n_eot_in_span": int(sum(1 for t in span if t == tokenizer.eos_token_id))})
    n_spanned = n - len(no_span)
    n_diff = n_spanned - n_match
    frac_match = n_match / n_spanned if n_spanned else float("nan")
    return {"n_rows": n, "n_no_span": len(no_span), "fraction_no_span": len(no_span) / n, "no_span_rows": no_span[:max_listed],
            "n_spanned": n_spanned, "n_match": n_match, "n_differ": n_diff, "fraction_match": frac_match,
            "passed": bool(frac_match >= MATCH_MIN and len(no_span) / n < NO_SPAN_MAX), "match_min": MATCH_MIN, "no_span_max": NO_SPAN_MAX,
            "span_len_mean": float(np.mean(span_lengths)) if span_lengths else None, "differing_rows": differing,
            "fraction_rows_starting_with_eot": float((ids[:, 0] == tokenizer.eos_token_id).mean()),
            "eot_per_row_mean": float((ids == tokenizer.eos_token_id).sum(1).mean())}


def run_round_trip(set_names: list[str], out_path: Path | None = None, *, sets_dir: Path = env.SETS_DIR, log: Any = print) -> dict[str, Any]:
    t0 = time.time()
    tokenizer = load_tokenizer()
    facts = tokenizer_facts(tokenizer)
    table = word_initial_table(tokenizer)
    log(f"[round-trip] tokenizer {facts['tokenizer']}: eos {facts['eos_token_id']} ({facts['eos_token']!r}), encode({EOT_LITERAL}) = {facts['encode_eot_literal']}, "
        f"word-initial tokens in the vocabulary: {int(table.sum())} of {table.size}; table in {time.time() - t0:.0f} s")
    out: dict[str, Any] = {"tokenizer_facts": facts, "n_word_initial_tokens_in_vocab": int(table.sum()), "sets": {}}
    if out_path is not None and out_path.is_file():
        with open(out_path) as f:
            previous = json.load(f)
        out["sets"] = previous.get("sets", {})  # earlier sets (E first, then the labeled ones) stay
    for name in set_names:
        ids, _, record = load_set(name, sets_dir)
        t1 = time.time()
        res = round_trip_rows(ids, tokenizer, table)
        res.update({"set_hash": record["sha256_ids"], "seconds": time.time() - t1, "checked_at": time.strftime("%Y-%m-%dT%H:%M:%S%z")})
        out["sets"][name] = res
        log(f"[round-trip] {name}: {res['n_match']}/{res['n_spanned']} exact ({res['fraction_match']:.4f}; >= {MATCH_MIN}), no span {res['n_no_span']} ({res['fraction_no_span']:.4f}; < {NO_SPAN_MAX}), "
            f"rows starting with EOT {res['fraction_rows_starting_with_eot']:.4f}, EOT per row {res['eot_per_row_mean']:.2f} -> {'pass' if res['passed'] else 'FAIL'}")
        for d in res["differing_rows"]:
            log(f"[round-trip]   row {d['row']}: first differing position in row {d['first_differing_position_in_row']} (span {d['span_start']}+{d['first_differing_position_in_span']}), "
                f"original {d['original']} -> re-encoded {d['reencoded']}; EOT in span {d['n_eot_in_span']}")
    if out_path is not None:
        out_path.parent.mkdir(parents=True, exist_ok=True)
        with open(out_path, "w") as f:
            json.dump(out, f, indent=2, sort_keys=True)
    return out
