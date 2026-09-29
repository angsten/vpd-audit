"""The outside yardstick: the divergence between the original model and a different small model
with the same tokenizer, on the same texts. Two *external-model cells* on E and on E_lab: EleutherAI/pythia-70m (primary) and
EleutherAI/pythia-160m, both at revision step143000, loaded in float32, eval mode, no autocast, fed the 512 token ids as they are
(no beginning-of-sequence token). Their logits are sliced to the first 50,277 ids and passed through the same divergence function
(`metrics.per_position_kl_from_probs`) and the same extras (`plain_terms.cell_extras`) as a mask's logits, with the sub-batch's
own target softmax chunks, so P is bitwise the target of every other number of the store.

Asserted in code and recorded in the manifest (`external_models.json`); nothing is taken from a web page:

1. len(tokenizer) == 50277 for the comparison model's tokenizer and for ours (EleutherAI/gpt-neox-20b, roundtrip.py); equal
   get_vocab() dictionaries; equal convert_ids_to_tokens(range(50277)); end-of-text id 0 for both.
2. The comparison model's config.vocab_size and the last dimension of its logits (recorded); at every position the probability
   its full softmax puts on ids 50,277 and above, mean and maximum recorded; stop if the mean exceeds 1e-4. Then the slice, and
   every later log-softmax is over the 50,277.
3. max_position_embeddings >= 512.
4. The resolved commit hash of the revision and the SHA-256 of the weights file (the file the model is loaded from).
5. The plausibility gate: on E^O (the non-GitHub texts of E_lab) each model's cross-entropy lies in [2.0, 4.0], and the larger
   model's is below the smaller's on every set. Otherwise stop.

The pre-flight (`preflight`) runs these before any masked forward of a launch that holds an external-model cell.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import numpy as np
import torch
import torch.nn.functional as F
from torch import Tensor

from vpd_audit.constants import KL_CHUNK, SEQ_LEN

VOCAB = 50277  # roundtrip.VOCAB_SIZE: the ids of EleutherAI/gpt-neox-20b, and the last dimension of the target's logits
REVISION = "step143000"
MODELS: dict[str, str] = {"pythia-70m": "EleutherAI/pythia-70m", "pythia-160m": "EleutherAI/pythia-160m"}  # in ascending size; the first is primary
PRIMARY = "pythia-70m"
PADDED_MASS_MAX_MEAN = 1e-4
CE_RANGE = (2.0, 4.0)
WEIGHTS_FILE = "model.safetensors"
SNAPSHOT_PATTERNS = ("config.json", WEIGHTS_FILE, "tokenizer.json", "tokenizer_config.json", "special_tokens_map.json")


@dataclass
class ExternalModel:
    key: str
    model: Any  # a callable: model(input_ids=(b, T) int64) -> an object with .logits of shape (b, T, >= VOCAB), float32
    facts: dict[str, Any] = field(default_factory=dict)


def tokenizer_facts(theirs: Any, ours: Any, vocab: int = VOCAB) -> dict[str, Any]:
    """Assertion 1, on two loaded tokenizers."""
    ids = list(range(vocab))
    facts = {"len_theirs": len(theirs), "len_ours": len(ours), "vocab_equal": bool(theirs.get_vocab() == ours.get_vocab()),
             "ids_to_tokens_equal": bool(theirs.convert_ids_to_tokens(ids) == ours.convert_ids_to_tokens(ids)), "eos_theirs": theirs.eos_token_id, "eos_ours": ours.eos_token_id}
    assert facts["len_theirs"] == vocab and facts["len_ours"] == vocab, f"the tokenizers hold {facts['len_theirs']} and {facts['len_ours']} ids, not {vocab}"
    assert facts["vocab_equal"], "the two tokenizers' get_vocab() dictionaries differ"
    assert facts["ids_to_tokens_equal"], f"convert_ids_to_tokens(range({vocab})) differs between the two tokenizers"
    assert facts["eos_theirs"] == 0 and facts["eos_ours"] == 0, f"end-of-text ids {facts['eos_theirs']} and {facts['eos_ours']}, not 0"
    return facts


def load_external(key: str, device: str | torch.device, *, revision: str = REVISION, log: Any = print) -> ExternalModel:
    """One comparison model from a pinned snapshot: assertions 1, 3, 4 and the config half of 2. The model is loaded from the
    snapshot directory with safetensors only, so the weights file hashed is the file loaded."""
    from huggingface_hub import snapshot_download
    from transformers import AutoConfig, AutoModelForCausalLM, AutoTokenizer

    from vpd_audit.artifacts import sha256_file
    from vpd_audit.roundtrip import load_tokenizer

    repo = MODELS[key]
    snap = Path(snapshot_download(repo, revision=revision, allow_patterns=list(SNAPSHOT_PATTERNS)))
    commit = snap.name
    assert len(commit) == 40 and int(commit, 16) >= 0, f"{repo}@{revision}: the snapshot directory {snap} does not name a commit"
    weights = snap / WEIGHTS_FILE
    assert weights.is_file(), f"{repo}@{revision}: no {WEIGHTS_FILE} in the snapshot"
    facts: dict[str, Any] = {"repo": repo, "revision": revision, "resolved_commit": commit, "weights_file": WEIGHTS_FILE, "weights_sha256": sha256_file(weights), "weights_bytes": weights.stat().st_size}
    facts["tokenizer"] = tokenizer_facts(AutoTokenizer.from_pretrained(snap), load_tokenizer())
    cfg = AutoConfig.from_pretrained(snap)
    facts.update({"config_vocab_size": int(cfg.vocab_size), "max_position_embeddings": int(cfg.max_position_embeddings), "config_dtype": str(getattr(cfg, "dtype", None) or getattr(cfg, "torch_dtype", None))})
    assert cfg.max_position_embeddings >= SEQ_LEN, f"{repo}: max_position_embeddings {cfg.max_position_embeddings} < {SEQ_LEN}"
    assert cfg.vocab_size >= VOCAB, f"{repo}: config.vocab_size {cfg.vocab_size} < {VOCAB}"
    model = AutoModelForCausalLM.from_pretrained(snap, dtype=torch.float32, use_safetensors=True).to(device).eval()
    dtypes = sorted({str(p.dtype) for p in model.parameters()})
    assert dtypes == ["torch.float32"], f"{repo}: parameters in {dtypes}, not float32"
    facts.update({"class": type(model).__name__, "parameter_dtype": "torch.float32", "n_parameters": int(sum(p.numel() for p in model.parameters())), "eval_mode": not model.training,
                  "torch_version": torch.__version__, "transformers_version": __import__("transformers").__version__})
    log(f"[external] {key}: {repo}@{revision} -> {commit[:12]}, {WEIGHTS_FILE} sha256 {facts['weights_sha256'][:16]}, config.vocab_size {cfg.vocab_size}, max positions {cfg.max_position_embeddings}, "
        f"{facts['n_parameters']} parameters in float32; tokenizer: {VOCAB} ids, vocabulary and id-to-token maps equal to ours, end-of-text id 0")
    return ExternalModel(key, model, facts)


def forward_sliced(ext: ExternalModel, batch: Tensor, *, vocab: int = VOCAB, chunk: int = KL_CHUNK) -> tuple[Tensor, Tensor]:
    """The comparison model's logits on `batch` (B, T) ids, fed as they are, in float32 with no autocast, in chunks of `chunk`
    sequences. Returns (the logits sliced to the first `vocab` ids, (B, T, vocab) float32, contiguous; the probability the full
    softmax puts on ids `vocab` and above, (B, T) float32). The last dimension of the full logits is recorded in `ext.facts`."""
    assert batch.ndim == 2 and batch.dtype == torch.int64, (tuple(batch.shape), batch.dtype)
    # the output is allocated once and filled chunk by chunk. A list of chunks ending in torch.cat holds the
    # chunks and the concatenation together, a second 6.6 GB at sub-batch 64 on the paper's vocabulary while the other model's
    # logits are alive. The values are the same tensor bit for bit (a copy either way; tests/test_tier5.py).
    B, T = batch.shape
    sliced = torch.empty((B, T, vocab), dtype=torch.float32, device=batch.device)
    padded = torch.empty((B, T), dtype=torch.float32, device=batch.device)
    with torch.no_grad(), torch.autocast(device_type=batch.device.type, enabled=False):
        for s in range(0, B, chunk):
            logits = ext.model(input_ids=batch[s : s + chunk]).logits
            assert logits.dtype == torch.float32 and logits.ndim == 3 and logits.shape[:2] == batch[s : s + chunk].shape and logits.shape[-1] >= vocab, (logits.dtype, tuple(logits.shape))
            last = int(logits.shape[-1])
            assert ext.facts.setdefault("logits_last_dim", last) == last
            padded[s : s + chunk] = torch.softmax(logits, dim=-1)[..., vocab:].sum(dim=-1) if last > vocab else 0.0
            sliced[s : s + chunk] = logits[..., :vocab]
            del logits
    return sliced, padded


def forward_sliced_by_concatenation(ext: ExternalModel, batch: Tensor, *, vocab: int = VOCAB, chunk: int = KL_CHUNK) -> tuple[Tensor, Tensor]:
    """`forward_sliced` as it was first written (a list of chunks, then torch.cat), kept only so that a test can hold the
    preallocated path to it bit for bit. Not used by the loop."""
    sliced, padded = [], []
    with torch.no_grad(), torch.autocast(device_type=batch.device.type, enabled=False):
        for s in range(0, batch.shape[0], chunk):
            logits = ext.model(input_ids=batch[s : s + chunk]).logits
            padded.append(torch.softmax(logits, dim=-1)[..., vocab:].sum(dim=-1) if logits.shape[-1] > vocab else torch.zeros(logits.shape[:2], dtype=torch.float32, device=logits.device))
            sliced.append(logits[..., :vocab].contiguous())
    return torch.cat(sliced, dim=0), torch.cat(padded, dim=0)


def reverse_kl(target_logits: Tensor, ext_logits: Tensor, *, chunk: int = KL_CHUNK) -> Tensor:
    """KL(Q_external || P_target) per position, (B, T) float32: the direction opposite to every other divergence of the store,
    from float32 log-softmaxes of the target's logits and of the sliced external logits, in chunks."""
    assert target_logits.shape == ext_logits.shape, (tuple(target_logits.shape), tuple(ext_logits.shape))
    out = []
    for s in range(0, ext_logits.shape[0], chunk):
        log_p = torch.log_softmax(target_logits[s : s + chunk].float(), dim=-1)
        q = torch.softmax(ext_logits[s : s + chunk].float(), dim=-1)
        out.append(F.kl_div(log_p, q, reduction="none").sum(dim=-1))  # Q (log Q - log P), 0 where Q = 0
        del log_p, q
    return torch.cat(out, dim=0)


def kl_between(a_logits: Tensor, b_logits: Tensor, *, chunk: int = KL_CHUNK) -> Tensor:
    """KL(Q_a || Q_b) per position between two external models' sliced logits, (B, T) float32."""
    assert a_logits.shape == b_logits.shape
    out = []
    for s in range(0, a_logits.shape[0], chunk):
        q_a = torch.softmax(a_logits[s : s + chunk].float(), dim=-1)
        log_b = torch.log_softmax(b_logits[s : s + chunk].float(), dim=-1)
        out.append(F.kl_div(log_b, q_a, reduction="none").sum(dim=-1))
        del q_a, log_b
    return torch.cat(out, dim=0)


def external_cell_quantities(key: str, state: dict[str, tuple[Tensor, Tensor]], externals: dict[str, ExternalModel], target_probs: list[Tensor], target_logits: Tensor, batch: Tensor, *, vocab: int = VOCAB) -> dict[str, Tensor]:
    """One external-model cell on one sub-batch, inside `cells.run_cells`. `state` holds, for the sub-batch, every comparison
    model's (sliced logits, padded-id mass), computed on first use (the divergence between the models needs them together) and
    cleared by the loop after the last external cell. Returns the sliced logits, the forward divergence KL(P || Q) through the
    same function as every mask's, the reverse divergence KL(Q || P), the divergence to the other comparison model KL(Q || Q')
    (NaN with one model), and the padded-id mass, all per position."""
    from vpd_audit.metrics import per_position_kl_from_probs

    if not state:
        for k, ext in externals.items():
            state[k] = forward_sliced(ext, batch, vocab=vocab)
    logits, padded = state[key]
    assert logits.shape == target_logits.shape and logits.shape[-1] == vocab, f"the sliced logits {tuple(logits.shape)} must have the target's shape {tuple(target_logits.shape)} with {vocab} ids"
    others = [k for k in state if k != key]
    assert len(others) <= 1, f"the divergence to the other comparison model is defined for two models, got {sorted(state)}"
    kl_other = kl_between(logits, state[others[0]][0]) if others else torch.full(logits.shape[:2], float("nan"), dtype=torch.float32, device=logits.device)
    return {"logits": logits, "kl": per_position_kl_from_probs(target_probs, logits), "kl_reverse": reverse_kl(target_logits, logits), "kl_other": kl_other, "padded_mass": padded}


def gate_verdicts(per_model: dict[str, dict[str, dict[str, float]]], *, reference_set: str, order: tuple[str, ...]) -> dict[str, Any]:
    """The gates of assertions 2 and 5 from per-model, per-set numbers ({model: {set: {"ce": mean cross-entropy, "padded_mass_mean":
    ..., "padded_mass_max": ...}}}): the padded-id mass's mean at most 1e-4 on every set; each model's cross-entropy on the
    reference set (E^O) within [2.0, 4.0]; and along `order` (ascending size) the cross-entropy strictly falling on every set."""
    padded = {m: {s: bool(v["padded_mass_mean"] <= PADDED_MASS_MAX_MEAN) for s, v in sets.items()} for m, sets in per_model.items()}
    in_range = {m: bool(CE_RANGE[0] <= sets[reference_set]["ce"] <= CE_RANGE[1]) for m, sets in per_model.items()}
    set_names = list(next(iter(per_model.values())))
    ordered = {s: bool(all(per_model[b][s]["ce"] < per_model[a][s]["ce"] for a, b in zip(order[:-1], order[1:]))) for s in set_names}
    ok = all(all(v.values()) for v in padded.values()) and all(in_range.values()) and all(ordered.values())
    return {"padded_mass_mean_at_most_1e-4": padded, "ce_on_reference_set_in_range": in_range, "larger_model_below_smaller_on_every_set": ordered, "reference_set": reference_set, "ce_range": list(CE_RANGE), "pass": bool(ok)}


def preflight(externals: dict[str, ExternalModel], sets: dict[str, np.ndarray], *, reference_rows: tuple[str, np.ndarray], device: str | torch.device, subbatch: int = 64, log: Any = print) -> dict[str, Any]:
    """Before any masked forward: every comparison model over every evaluation set, its cross-entropy per text (over the sliced,
    renormalized 50,277 ids, as `metrics.per_sequence_ce` takes it) and the padded-id mass per position; then the gates.
    `reference_rows` is (the name of the set that holds E^O, the row indices of E^O in it). Raises `tier5.GateFailure`."""
    from vpd_audit.metrics import per_sequence_ce
    from vpd_audit.tier5 import GateFailure

    t0 = time.time()
    ref_set, ref_rows = reference_rows
    ref_name = f"{ref_set}_other"
    per_model: dict[str, dict[str, dict[str, float]]] = {}
    for key, ext in externals.items():
        per_model[key] = {}
        for name, ids in sets.items():
            ces, mass_sum, mass_max, n_pos = [], 0.0, 0.0, 0
            for s in range(0, ids.shape[0], subbatch):
                batch = torch.from_numpy(np.ascontiguousarray(ids[s : s + subbatch])).long().to(device)
                logits, padded = forward_sliced(ext, batch)
                ces.append(per_sequence_ce(logits, batch).double().cpu().numpy())
                mass_sum += float(padded.double().sum())
                mass_max = max(mass_max, float(padded.max()))
                n_pos += int(padded.numel())
                del logits, padded
            ce = np.concatenate(ces)
            per_model[key][name] = {"ce": float(ce.mean()), "padded_mass_mean": mass_sum / n_pos, "padded_mass_max": mass_max, "n_texts": int(ids.shape[0])}
            if name == ref_set:
                per_model[key][ref_name] = {"ce": float(ce[ref_rows].mean()), "padded_mass_mean": per_model[key][name]["padded_mass_mean"], "padded_mass_max": mass_max, "n_texts": int(len(ref_rows))}
    order = tuple(k for k in MODELS if k in externals)
    verdicts = gate_verdicts(per_model, reference_set=ref_name, order=order)
    out = {"models": {k: e.facts for k, e in externals.items()}, "per_model_per_set": per_model, "gates": verdicts, "seconds": time.time() - t0, "vocab": VOCAB, "primary": PRIMARY}
    for key in externals:
        log(f"[external] pre-flight {key}: " + "; ".join(f"{s}: cross-entropy {v['ce']:.4f}, padded-id mass mean {v['padded_mass_mean']:.3e}, max {v['padded_mass_max']:.3e}" for s, v in per_model[key].items()))
    log(f"[external] gates: padded-id mass {'pass' if all(all(v.values()) for v in verdicts['padded_mass_mean_at_most_1e-4'].values()) else 'FAIL'}; cross-entropy on {ref_name} in {list(CE_RANGE)}: "
        f"{'pass' if all(verdicts['ce_on_reference_set_in_range'].values()) else 'FAIL'}; the larger model below the smaller on every set: {'pass' if all(verdicts['larger_model_below_smaller_on_every_set'].values()) else 'FAIL'}")
    if not verdicts["pass"]:
        raise GateFailure(f"the outside yardstick's gates failed: {verdicts}")
    return out
