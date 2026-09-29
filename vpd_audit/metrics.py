"""Per-position divergence and per-sequence cross-entropy, matching the authors.

Divergence: `F.kl_div(log_q, p, reduction="none").sum(-1)` on float32 log-softmaxes, direction
KL(P_target || Q_masked), zero where P = 0, exactly as `recon_loss_kl` in
`param_decomp/models/batch_and_loss_fns.py` computes before it sums; run in sub-chunks of 8
sequences. Its mean over all T positions equals the authors' scalar `calc_kl_divergence_lm`.

Cross-entropy: the average over positions 0 to T - 2 of -log Q(x_{t+1}), the last position
dropped, as `CEandKLLosses._calc_ce_and_kl_losses` does by flattening, shifting by one, and
ignoring each sequence's first label; the batch mean of our per-sequence values equals theirs.
"""

from __future__ import annotations

import torch
import torch.nn.functional as F
from torch import Tensor

from vpd_audit.constants import KL_CHUNK


def per_position_kl(target_logits: Tensor, masked_logits: Tensor, *, chunk: int = KL_CHUNK) -> Tensor:
    """KL(P_target || Q_masked) per position, shape (B, T), float32."""
    assert target_logits.shape == masked_logits.shape, (tuple(target_logits.shape), tuple(masked_logits.shape))
    assert target_logits.ndim == 3
    out = []
    for s in range(0, target_logits.shape[0], chunk):
        p = torch.softmax(target_logits[s : s + chunk].float(), dim=-1)  # P
        log_q = torch.log_softmax(masked_logits[s : s + chunk].float(), dim=-1)  # log Q
        out.append(F.kl_div(log_q, p, reduction="none").sum(dim=-1))  # P * (log P - log Q), 0 where P = 0
        del p, log_q
    kl = torch.cat(out, dim=0)
    assert kl.shape == target_logits.shape[:2] and kl.dtype == torch.float32
    return kl


def target_softmax_chunks(target_logits: Tensor, *, chunk: int = KL_CHUNK) -> list[Tensor]:
    """The target's softmax P per chunk of `chunk` sequences, exactly the call `per_position_kl` makes per chunk:
    computed once per sub-batch and handed to `per_position_kl_from_probs` for every cell, so the
    target logits can be freed. Not one softmax over all rows, which would change the kernel's batch shape."""
    assert target_logits.ndim == 3
    return [torch.softmax(target_logits[s : s + chunk].float(), dim=-1) for s in range(0, target_logits.shape[0], chunk)]


def per_position_kl_from_probs(target_probs: list[Tensor], masked_logits: Tensor, *, chunk: int = KL_CHUNK) -> Tensor:
    """`per_position_kl` with the target's softmax chunks precomputed by `target_softmax_chunks` at the same `chunk`: the
    `F.kl_div(log_q, p)` call and its inputs are identical, so the result is bitwise `per_position_kl`'s."""
    assert masked_logits.ndim == 3
    B = masked_logits.shape[0]
    starts = list(range(0, B, chunk))
    assert len(target_probs) == len(starts), f"{len(target_probs)} softmax chunks for {len(starts)} chunks of {chunk} over B = {B}"
    out = []
    for p, s in zip(target_probs, starts):
        assert p.shape == (min(chunk, B - s),) + tuple(masked_logits.shape[1:]) and p.dtype == torch.float32, (tuple(p.shape), tuple(masked_logits.shape))
        log_q = torch.log_softmax(masked_logits[s : s + chunk].float(), dim=-1)  # log Q
        out.append(F.kl_div(log_q, p, reduction="none").sum(dim=-1))  # P * (log P - log Q), 0 where P = 0
        del log_q
    kl = torch.cat(out, dim=0)
    assert kl.shape == masked_logits.shape[:2] and kl.dtype == torch.float32
    return kl


def per_sequence_ce(logits: Tensor, ids: Tensor, *, chunk: int = KL_CHUNK) -> Tensor:
    """Cross-entropy per sequence: mean over t = 0..T-2 of -log Q_t(x_{t+1}); shape (B,), float32."""
    assert logits.ndim == 3 and ids.shape == logits.shape[:2], (tuple(logits.shape), tuple(ids.shape))
    ids = ids.to(logits.device).long()
    out = []
    for s in range(0, logits.shape[0], chunk):
        log_q = torch.log_softmax(logits[s : s + chunk].float(), dim=-1)  # (b, T, V)
        labels = ids[s : s + chunk, 1:].unsqueeze(-1)  # (b, T-1, 1)
        nll = -log_q[:, :-1].gather(-1, labels).squeeze(-1)  # (b, T-1)
        out.append(nll.mean(dim=-1))
        del log_q, nll
    ce = torch.cat(out, dim=0)
    assert ce.shape == (logits.shape[0],) and ce.dtype == torch.float32
    return ce


def summarize_kl(kl: Tensor) -> tuple[Tensor, Tensor, Tensor]:
    """Per-sequence mean, maximum, and argmax over positions of a (B, T) divergence tensor."""
    assert kl.ndim == 2
    mx, arg = kl.max(dim=-1)
    return kl.mean(dim=-1), mx, arg
