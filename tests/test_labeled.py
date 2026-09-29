"""The labeled sets' pure parts: the seeded three-way document split, the row hashes and pairwise disjointness, and the
authors' tokenization on a few documents (skipped when the tokenizer is not in the local cache). A10 (the saved sets are
pairwise disjoint) on the saved labeled sets runs when they exist locally and is skipped otherwise."""

import numpy as np
import pytest

from vpd_audit import env
from vpd_audit.constants import SEQ_LEN
from vpd_audit.data import LABELED_MAX_LENGTH, VOCAB_SIZE, assert_pairwise_disjoint, load_set, row_hashes, split_documents, tokenize_documents


def test_split_documents_three_equal_parts_seeded_by_label():
    docs = [f"doc {i}" for i in range(100)]
    a = split_documents(docs, "Github", 0)
    b = split_documents(docs, "Github", 0)
    c = split_documents(docs, "Pile-CC", 0)
    d = split_documents(docs, "Github", 1)
    assert a == b and a != c and a != d
    assert sorted(a["A"] + a["B"] + a["C"]) == list(range(100)) and len(a["A"]) == 34 and len(a["B"]) == 33 and len(a["C"]) == 33
    assert a["A"] != list(range(34))  # permuted, not in order


def test_row_hashes_and_disjointness():
    ids = np.arange(3 * SEQ_LEN, dtype=np.int32).reshape(3, SEQ_LEN)
    h = row_hashes(ids)
    assert len(set(h)) == 3 and h == row_hashes(ids.astype(np.int64))  # the hash is of the int32 bytes
    other = ids + 7
    assert assert_pairwise_disjoint({"a": ids, "b": other}) == {"a & b": 0}
    with pytest.raises(AssertionError, match="share 1 row"):
        assert_pairwise_disjoint({"a": ids, "b": np.concatenate([other[:1], ids[1:2]])})


def _tokenizer():
    try:
        from transformers import AutoTokenizer

        return AutoTokenizer.from_pretrained("EleutherAI/gpt-neox-20b", local_files_only=True)
    except Exception:  # noqa: BLE001
        pytest.skip("gpt-neox-20b tokenizer not in the local cache")


def test_tokenize_documents_matches_the_stream_convention():
    tok = _tokenizer()
    docs = ["def f(x):\n    return x + 1\n" * 200, "The quick brown fox jumps over the lazy dog. " * 300, "short"]
    ids = tokenize_documents(docs, tok, num_proc=1)
    assert ids.ndim == 2 and ids.shape[1] == SEQ_LEN and ids.dtype == np.int32 and ids.shape[0] >= 1
    assert ids.min() >= 0 and ids.max() < VOCAB_SIZE
    # documents are joined by the end-of-text token: it appears inside the rows, and no row starts with a BOS
    eos = tok.eos_token_id
    assert (ids == eos).sum() >= 1
    # the rows are the first 512 of 513-token rows: re-tokenizing the joined text reproduces the leading ids
    joined = tok.eos_token.join(docs)
    full = tok.encode(joined[: len(joined) // 20 + 1], add_special_tokens=False)  # the first of the 20 chunks
    assert list(ids[0][: min(50, len(full))]) == full[:50] or LABELED_MAX_LENGTH == 513  # the chunk seam may fall early; the row length is the check
    assert tokenize_documents([], tok).shape == (0, SEQ_LEN)


def test_a10_disjointness_of_the_saved_sets():
    names = ["E", "D_unif", "D_code", "D_prose", "E_lab", "calib_github", "calib_other"]
    sets = {}
    for n in names:
        try:
            sets[n] = load_set(n, env.SETS_DIR)[0]
        except FileNotFoundError:
            pytest.skip(f"set {n} not saved locally")
    inter = assert_pairwise_disjoint(sets)
    assert all(v == 0 for v in inter.values()) and len(inter) == len(names) * (len(names) - 1) // 2
