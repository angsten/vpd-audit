"""The metric checks A8 (the divergence's direction and per-position reduction) and A9 (the cross-entropy matches the authors')."""

import math

import einops
import torch
import torch.nn.functional as F

from vpd_audit.metrics import per_position_kl, per_sequence_ce, summarize_kl

B, T, V = 2, 5, 3


def test_a8_divergence_direction_and_reduction():
    gen = torch.Generator().manual_seed(0)
    logits = torch.randn((B, T, V), generator=gen)
    # identical logits: zero up to float32 rounding (log p is softmax(x).log(), log q is log_softmax(x),
    # which is the authors' arithmetic and why per-position values may sit a few 1e-8 below zero)
    same = per_position_kl(logits, logits)
    assert same.shape == (B, T) and torch.allclose(same, torch.zeros(B, T), atol=1e-6) and float(same.min()) > -1e-4
    # P = (0.9, 0.1, ~0), Q = (0.5, 0.5, ~0); KL(P || Q) = 0.9 ln(0.9/0.5) + 0.1 ln(0.1/0.5)
    p_logits = torch.tensor([math.log(0.9), math.log(0.1), -1e4]).expand(B, T, V).contiguous()
    q_logits = torch.tensor([math.log(0.5), math.log(0.5), -1e4]).expand(B, T, V).contiguous()
    kl = per_position_kl(p_logits, q_logits)
    forward = 0.9 * math.log(0.9 / 0.5) + 0.1 * math.log(0.1 / 0.5)  # 0.368
    reverse = 0.5 * math.log(0.5 / 0.9) + 0.5 * math.log(0.5 / 0.1)  # 0.511
    assert kl.shape == (B, T)
    assert torch.allclose(kl, torch.full((B, T), forward), atol=1e-6)
    assert abs(forward - 0.368) < 1e-3 and abs(reverse - 0.511) < 1e-3
    assert not torch.allclose(kl, torch.full((B, T), reverse), atol=1e-3)
    assert torch.isfinite(kl).all()  # the P = 0 entry contributes 0, not NaN
    # per position, not per sequence: distinct positions give distinct values
    q2 = q_logits.clone()
    q2[:, 0, :] = p_logits[:, 0, :]
    kl2 = per_position_kl(p_logits, q2)
    assert torch.allclose(kl2[:, 0], torch.zeros(B), atol=1e-6) and torch.allclose(kl2[:, 1:], torch.full((B, T - 1), forward), atol=1e-6)
    mean, mx, arg = summarize_kl(kl2)
    assert torch.allclose(mean, torch.full((B,), forward * (T - 1) / T), atol=1e-6) and torch.allclose(mx, torch.full((B,), forward), atol=1e-6)
    assert (arg >= 1).all()


def _authors_ce(logits: torch.Tensor, batch: torch.Tensor) -> float:
    """`CEandKLLosses._calc_ce_and_kl_losses` lines 101-110 at commit 74146b5, verbatim."""
    masked_batch = batch.clone()
    masked_batch[:, 0] = -100
    flat_masked_batch = masked_batch.flatten()
    flat_logits = einops.rearrange(logits, "b seq_len vocab -> (b seq_len) vocab")
    return F.cross_entropy(flat_logits[:-1], flat_masked_batch[1:], ignore_index=-100).item()


def test_a9_cross_entropy_matches_the_authors():
    gen = torch.Generator().manual_seed(1)
    for b, t, v in ((2, 5, 7), (3, 11, 13), (4, 512, 17)):
        logits = torch.randn((b, t, v), generator=gen) * 3
        ids = torch.randint(0, v, (b, t), generator=gen)
        ours = per_sequence_ce(logits, ids)
        assert ours.shape == (b,)
        assert abs(float(ours.mean()) - _authors_ce(logits, ids)) < 1e-6
        # the last position is dropped and labels are shifted by one
        by_hand = torch.stack([
            torch.stack([-torch.log_softmax(logits[i, j], -1)[ids[i, j + 1]] for j in range(t - 1)]).mean() for i in range(b)
        ])
        assert torch.allclose(ours, by_hand, atol=1e-6)


def test_kl_from_precomputed_target_softmax_is_bitwise_per_position_kl():
    """The target's softmax computed once in chunks and passed to the kl_div call gives
    bitwise the per-cell path, for B = 20 (chunks of 8, 8, 4) and for a chunk of 3; a wrong chunk count is refused."""
    from vpd_audit.metrics import per_position_kl_from_probs, target_softmax_chunks

    gen = torch.Generator().manual_seed(2)
    t = torch.randn((20, 5, 7), generator=gen) * 3
    for q in (torch.randn((20, 5, 7), generator=gen) * 3, t.clone()):
        for chunk in (8, 3, 20, 64):
            probs = target_softmax_chunks(t, chunk=chunk)
            assert len(probs) == -(-20 // chunk) and all(p.dtype == torch.float32 for p in probs)
            assert torch.equal(per_position_kl_from_probs(probs, q, chunk=chunk), per_position_kl(t, q, chunk=chunk))
    import pytest

    with pytest.raises(AssertionError, match="softmax chunks"):
        per_position_kl_from_probs(target_softmax_chunks(t, chunk=8), t, chunk=4)
