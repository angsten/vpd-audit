"""Masks: the mask formula, the backgrounds, and the forward wrapper that checks (P3) and fingerprints (P4) every mask.

The mask formula m = g + (1 - g) r. For a binary batch-shared source rho of shape (C_l,) it is
computed as `torch.where(rho.bool(), 1, g)`, which equals the formula exactly; for a full
(B, T, C_l) source such as the uniform background it is the formula in g's dtype, which is what
the authors' stochastic-mask code does. The uniform background is regenerated from its seed
tuple (master, "u", k, i), module by module in sorted order, rather than stored. The residual
follows one rule: it is subcomponent C_l + 1 with g = 0, so its mask is the background's
value. Masks are wrapped with `make_mask_infos(masks)` for "Delta excluded" or with
`weight_deltas_and_masks` for "Delta included"; every decomposed module must be present in
every call, because a module omitted from the mask dictionary silently runs the target's
weights (`component_model.py` line 396). The forward wrapper asserts the shape (B, 512, C_l)
of every mask, asserts min(m - g) >= -1e-6 for permitted families (P3), counts the entries with
m != g and m != 1 per module, accepts a direct mask for the rounded, zero-all, and
random-illegal references, and fingerprints the mask tensors it hands to the forward (P4:
the on-device fingerprint of `fingerprint.py` in place of the earlier SHA-256, which stays
available as `sha256_masks` behind `do_sha256`, a flag no grid run sets).
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from typing import Any

import torch
from torch import Tensor

from vpd_audit.constants import PERMITTED_TOL, SEQ_LEN
from vpd_audit.fingerprint import Fingerprint, fingerprint, sha256_masks
from vpd_audit.importances import autocast_context

BACKGROUNDS = ("r0", "r1", "uniform", "hard_zero")
P3_SLAB = 8  # the P3 check and the two counts run in slabs of 8 sequences along B, as the fingerprint does


# ----------------------------------------------------------------------------- seeds


def seed_from_tuple(seed_tuple: tuple[Any, ...]) -> int:
    """A 63-bit seed from a tuple of ints and strings, stable across processes."""
    for x in seed_tuple:
        assert isinstance(x, (int, str)), f"seed tuples hold ints and strings only, got {type(x)}"
    digest = hashlib.sha256(repr(tuple(seed_tuple)).encode()).digest()
    return int.from_bytes(digest[:8], "little") & ((1 << 63) - 1)


def uniform_background(
    seed_tuple: tuple[Any, ...],
    module_to_c: dict[str, int],
    B: int,
    T: int,
    *,
    dtype: torch.dtype,
    device: torch.device | str,
) -> tuple[dict[str, Tensor], dict[str, Tensor]]:
    """u ~ U(0, 1) per (b, t, c) and one scalar per position for the residual, per module,
    drawn in sorted module order from one generator seeded by `seed_tuple`.

    The residual draw is always made (and discarded when Delta is excluded) so that the
    component masks of a draw are identical whether or not the residual is included.
    """
    gen = torch.Generator(device=torch.device(device).type)
    gen.manual_seed(seed_from_tuple(seed_tuple))
    u: dict[str, Tensor] = {}
    u_delta: dict[str, Tensor] = {}
    for k in sorted(module_to_c):
        u[k] = torch.rand((B, T, module_to_c[k]), generator=gen, dtype=dtype, device=device)
        u_delta[k] = torch.rand((B, T), generator=gen, dtype=dtype, device=device)
    return u, u_delta


# ----------------------------------------------------------------------------- the formula


def apply_binary_source(g: Tensor, rho: Tensor) -> Tensor:
    """m = g + (1 - g) rho for a batch-shared binary source rho of shape (C,), as where(rho, 1, g)."""
    assert g.ndim == 3, f"g must be (B, T, C), got {tuple(g.shape)}"
    assert rho.ndim == 1 and rho.shape[0] == g.shape[-1], (
        f"a batch-shared source must have shape (C,) = ({g.shape[-1]},), got {tuple(rho.shape)}"
    )
    assert bool(((rho == 0) | (rho == 1)).all()), "a binary source holds only 0 and 1"
    return torch.where(rho.bool(), 1, g)


def apply_binary_source_per_text(g: Tensor, rho: Tensor) -> Tensor:
    """m = g + (1 - g) rho for a *per-text* binary source, one row per text, shape (B, 1, C), as
    where(rho, 1, g): row b is `apply_binary_source(g[b : b + 1], rho[b, 0])` exactly (where() is elementwise). A sibling of
    `apply_binary_source`, whose assert on a one-dimensional batch-shared source is left as it is."""
    assert g.ndim == 3, f"g must be (B, T, C), got {tuple(g.shape)}"
    assert rho.ndim == 3 and rho.shape == (g.shape[0], 1, g.shape[-1]), (
        f"a per-text source must have shape (B, 1, C) = ({g.shape[0]}, 1, {g.shape[-1]}), got {tuple(rho.shape)}"
    )
    assert bool(((rho == 0) | (rho == 1)).all()), "a binary source holds only 0 and 1"
    return torch.where(rho.bool(), 1, g)


def apply_source(g: Tensor, r: Tensor) -> Tensor:
    """m = g + (1 - g) r in g's dtype for a full source r of g's shape (the uniform background)."""
    assert g.ndim == 3, f"g must be (B, T, C), got {tuple(g.shape)}"
    assert r.shape == g.shape, f"a full source must have g's shape {tuple(g.shape)}, got {tuple(r.shape)}"
    assert r.dtype == g.dtype, (r.dtype, g.dtype)
    return g + (1 - g) * r


def rounded_mask(g: Tensor, threshold: float) -> Tensor:
    """The paper's rounded mask 1[g > threshold], in g's dtype (a direct mask, not a source)."""
    assert g.ndim == 3
    return (g > threshold).to(g.dtype)


def residual_mask(background: str, B: int, T: int, *, u_delta: Tensor | None, dtype: torch.dtype, device: torch.device | str) -> Tensor:
    """m^Delta of shape exactly (B, T) when the residual is included."""
    assert background in BACKGROUNDS, background
    if background == "r0":
        return torch.zeros((B, T), dtype=dtype, device=device)
    if background in ("r1", "hard_zero"):
        return torch.ones((B, T), dtype=dtype, device=device)
    assert u_delta is not None, "the uniform background needs its residual draw"
    assert u_delta.shape == (B, T), f"residual mask must be (B, T) = ({B}, {T}), got {tuple(u_delta.shape)}"
    return u_delta


# ----------------------------------------------------------------------------- wrapping


def wrap_masks(
    model: Any,
    masks: dict[str, Tensor],
    delta_masks: dict[str, Tensor] | None = None,
    weight_deltas: dict[str, Tensor] | None = None,
) -> dict[str, Any]:
    """`make_mask_infos(masks)` (Delta excluded) or with `weight_deltas_and_masks` (Delta included).

    Every decomposed module must be present; a delta mask must have shape exactly (B, T).
    """
    from param_decomp.models.components import make_mask_infos

    keys = set(model.module_to_c)
    assert set(masks) == keys, f"every decomposed module needs a mask; missing {sorted(keys - set(masks))}, extra {sorted(set(masks) - keys)}"
    first = sorted(masks)[0]
    lead = tuple(masks[first].shape[:-1])
    for k in sorted(masks):
        m = masks[k]
        assert m.ndim == 3, f"{k}: mask must be (B, T, C_l), got {tuple(m.shape)}"
        assert m.shape[-1] == model.module_to_c[k], f"{k}: mask's last axis must be C_l = {model.module_to_c[k]}, got {tuple(m.shape)}"
        assert tuple(m.shape[:-1]) == lead, f"{k}: leading axes {tuple(m.shape[:-1])} differ from {first}'s {lead}"
    if delta_masks is None:
        return make_mask_infos(masks)
    assert weight_deltas is not None, "Delta included needs weight_deltas = model.calc_weight_deltas()"
    assert set(delta_masks) == keys and set(weight_deltas) == keys
    for k in masks:
        assert delta_masks[k].shape == tuple(masks[k].shape[:2]), (
            f"{k}: residual mask must be (B, T) = {tuple(masks[k].shape[:2])}, got {tuple(delta_masks[k].shape)}"
        )
    return make_mask_infos(masks, weight_deltas_and_masks={k: (weight_deltas[k], delta_masks[k]) for k in masks})


# ----------------------------------------------------------------------------- the forward wrapper


@dataclass
class ForwardResult:
    logits: Tensor  # (B, T, V)
    fp: Fingerprint  # P4: levels 1 and 2 of the applied masks, on the device
    delta_included: bool
    min_gap: float  # min over all entries of m - g
    n_below_label: int  # entries with m < g - PERMITTED_TOL (zero for permitted families)
    n_ne_g: dict[str, int]  # per module: entries with m != g
    n_ne_one: dict[str, int]  # per module: entries with m != 1
    sha256: str = ""  # the earlier SHA-256, only when do_sha256 (the smoke's G2 and unit test T3)
    n_positions_below_label: int = 0  # P3 for hard-zero cells: positions with at least one entry below its label


def masked_forward(
    model: Any,
    batch: Tensor,
    masks: dict[str, Tensor],
    g: dict[str, Tensor],
    *,
    permitted: bool,
    precision: str,
    delta_masks: dict[str, Tensor] | None = None,
    weight_deltas: dict[str, Tensor] | None = None,
    do_sha256: bool = False,
    timings: Any | None = None,
) -> ForwardResult:
    """One masked forward. Asserts shapes, P3 for permitted families, counts m != g and m != 1 per module, and
    fingerprints the mask tensors handed to the forward (`make_mask_infos` neither copies nor casts them, so the
    tensors inside the mask infos are the tensors fingerprinted).

    `timings`, when given, is an object with a `phase(name)` context manager (see `timing.py`); the P3 check
    with the counts, the fingerprint, the optional SHA-256, and the forward are then timed as phases. It changes
    nothing else.
    """
    import contextlib

    phase = timings.phase if timings is not None else (lambda name: contextlib.nullcontext())
    assert batch.ndim == 2 and batch.shape[1] == SEQ_LEN, f"batch must be (B, {SEQ_LEN}), got {tuple(batch.shape)}"
    B = batch.shape[0]
    keys = sorted(model.module_to_c)
    assert set(masks) == set(keys), f"masks must cover every module: missing {sorted(set(keys) - set(masks))}"
    assert set(g) == set(keys)
    with phase("p3_check"):
        # The check runs in slabs of P3_SLAB sequences along B, as the fingerprint does, so the
        # temporaries are P3_SLAB / B of what one module's (B, T, C) gap cost; four of the five reductions come from the
        # slab's gap = m - g (gap != 0 equals m != g exactly for finite floats), the fifth from m != 1 on the same slab.
        # Every output is bitwise the unchunked one: a minimum is order-independent and the counts are integer sums. The
        # accumulators live on the device and are pulled twice per cell (the minimum, then the counts) instead of once
        # per reduction per module.
        dev = masks[keys[0]].device
        min_gap_t = torch.full((), float("inf"), dtype=torch.float32, device=dev)
        n_below_t = torch.zeros((), dtype=torch.int64, device=dev)
        ne_g_t = {k: torch.zeros((), dtype=torch.int64, device=dev) for k in keys}
        ne_one_t = {k: torch.zeros((), dtype=torch.int64, device=dev) for k in keys}
        below_pos: Tensor | None = torch.zeros((B, SEQ_LEN), dtype=torch.bool, device=dev) if not permitted else None
        for k in keys:
            m = masks[k]
            assert m.shape == (B, SEQ_LEN, model.module_to_c[k]), (
                f"{k}: mask must be (B, {SEQ_LEN}, C_l) = ({B}, {SEQ_LEN}, {model.module_to_c[k]}), got {tuple(m.shape)}"
            )
            assert g[k].shape == m.shape, (k, tuple(g[k].shape), tuple(m.shape))
            gk = g[k]
            for s in range(0, B, P3_SLAB):
                ms = m[s : s + P3_SLAB]
                gap = ms.float() - gk[s : s + P3_SLAB].float()
                min_gap_t = torch.minimum(min_gap_t, gap.min())
                below = gap < -PERMITTED_TOL
                n_below_t += below.sum()
                if below_pos is not None:
                    below_pos[s : s + P3_SLAB] |= below.any(dim=-1)
                ne_g_t[k] += (gap != 0).sum()
                ne_one_t[k] += (ms != 1).sum()
                del gap, below, ms
        min_gap = float(min_gap_t)
        counts = torch.stack([n_below_t, *(ne_g_t[k] for k in keys), *(ne_one_t[k] for k in keys), below_pos.sum() if below_pos is not None else n_below_t.new_zeros(())]).cpu().tolist()
        n_below = int(counts[0])
        n_ne_g: dict[str, int] = {k: int(v) for k, v in zip(keys, counts[1 : 1 + len(keys)])}
        n_ne_one: dict[str, int] = {k: int(v) for k, v in zip(keys, counts[1 + len(keys) : 1 + 2 * len(keys)])}
        n_positions_below = int(counts[-1]) if below_pos is not None else 0
        del min_gap_t, n_below_t, ne_g_t, ne_one_t
        if permitted:
            assert min_gap >= -PERMITTED_TOL, f"P3: a permitted mask lies below its label by {-min_gap:.3e}"
    infos = wrap_masks(model, masks, delta_masks, weight_deltas)
    applied = {k: infos[k].component_mask for k in keys}
    applied_delta = {k: infos[k].weight_delta_and_mask[1] for k in keys} if delta_masks is not None else None
    with phase("fingerprint"):
        fp = fingerprint(applied, applied_delta)
    sha = ""
    if do_sha256:
        with phase("sha256"):
            sha = sha256_masks(applied, applied_delta)
    with phase("forward"):
        device = next(model.parameters()).device
        with torch.no_grad(), autocast_context(device, precision):
            logits = model(batch.to(device), mask_infos=infos)
    assert isinstance(logits, Tensor) and logits.shape[:2] == (B, SEQ_LEN), tuple(logits.shape)
    return ForwardResult(logits=logits, fp=fp, delta_included=delta_masks is not None, min_gap=min_gap, n_below_label=n_below,
                         n_ne_g=n_ne_g, n_ne_one=n_ne_one, sha256=sha, n_positions_below_label=n_positions_below)


# ----------------------------------------------------------------------------- the hard-zero path, the switched mass, the first touched position


def hard_zero_masks(g: dict[str, Tensor], rho_erase: dict[str, Tensor]) -> dict[str, Tensor]:
    """The direct mask m = 1 - rho broadcast to (B, T, C_l), bypassing the source formula; erased
    subcomponents at 0 at every position whatever their g. The forward wrapper counts m < g for these cells instead of
    asserting (P3), through permitted=False."""
    out = {}
    for k in sorted(g):
        r = rho_erase[k]
        assert r.ndim == 1 and r.shape[0] == g[k].shape[-1], (k, tuple(r.shape), tuple(g[k].shape))
        assert bool(((r == 0) | (r == 1)).all())
        m = (1 - r).to(g[k].dtype).view(1, 1, -1).expand_as(g[k]).contiguous()
        out[k] = m
    return out


def switched_mass(g: dict[str, Tensor], rho: dict[str, Tensor], *, family: str, background: str, u: dict[str, Tensor] | None = None, level: float | None = None) -> Tensor:
    """The switched mass sigma_b = (1/T) sum_t sum_l sum_c (1 - g) |r - r_bg| with r the cell's source and r_bg the value
    the background gives an un-named subcomponent. For the union the named set has r = 1, for the erases r = 0; under
    the two primary backgrounds this reduces to (1/T) sum over the named entries of (1 - g); under the uniform
    background the named entries contribute (1 - g) |named_value - u| and the rest nothing. For a hard-zero cell the
    switched mass of the soft erase with the same set is reported (background r1). For a level cell
    the named set has r = s and the background r0 (never-named at its labels) gives r_bg = 0, r1 (at 1) gives
    r_bg = 1, so the named entries contribute (1 - g) |s - r_bg|: s or 1 - s times the set's union sigma. Returns (B,) float32."""
    keys = sorted(g)
    B, T = g[keys[0]].shape[:2]
    total = torch.zeros(B, dtype=torch.float32, device=g[keys[0]].device)
    if family == "level":
        assert level is not None and background in ("r0", "r1"), (level, background)
        named_value = float(level)
    else:
        named_value = 1.0 if family in ("union", "rounded_own_g") else 0.0
    for k in keys:
        named = rho[k].bool().view(1, 1, -1)
        one_minus_g = (1 - g[k].float())
        if family == "level":
            contrib = one_minus_g * named * abs(named_value - (0.0 if background == "r0" else 1.0))
        elif background in ("r0", "r1", "ones"):
            contrib = one_minus_g * named  # |named_value - bg| = 1 for both primary backgrounds
        else:
            assert background == "uniform" and u is not None
            contrib = one_minus_g * named * (named_value - u[k].float()).abs()
        total += contrib.sum(dim=(1, 2))
    return total / T


def switched_mass_per_text(g: dict[str, Tensor], rho: dict[str, Tensor]) -> Tensor:
    """`switched_mass` for a per-text union under the background r0, the only configuration the
    per-text families run in: sigma_b = (1/T) sum_t sum_l sum over the pieces text b's source names of (1 - g). `rho[k]` has
    shape (B, 1, C_l). The arithmetic is `switched_mass`'s primary-background branch with the named set broadcast per text
    instead of per cell, so with every row equal it returns that function's values. Returns (B,) float32."""
    keys = sorted(g)
    B, T = g[keys[0]].shape[:2]
    total = torch.zeros(B, dtype=torch.float32, device=g[keys[0]].device)
    for k in keys:
        assert rho[k].ndim == 3 and rho[k].shape == (B, 1, g[k].shape[-1]), (k, tuple(rho[k].shape), tuple(g[k].shape))
        named = rho[k].bool()
        one_minus_g = (1 - g[k].float())
        contrib = one_minus_g * named
        total += contrib.sum(dim=(1, 2))
    return total / T


def over_removal(g: dict[str, Tensor], rho_erase: dict[str, Tensor]) -> Tensor:
    """The over-removal omega_b = (1/T) sum_t sum_{(l, c) in S} g, the mask a hard-zero cell removed below the label."""
    keys = sorted(g)
    B, T = g[keys[0]].shape[:2]
    total = torch.zeros(B, dtype=torch.float32, device=g[keys[0]].device)
    for k in keys:
        total += (g[k].float() * rho_erase[k].bool().view(1, 1, -1)).sum(dim=(1, 2))
    return total / T


def first_touched(g: dict[str, Tensor], rho_erase: dict[str, Tensor], tau_q: float) -> tuple[Tensor, Tensor]:
    """The first touched position t*_b = min{t : max over (l, c) in S of g > tau_q}, T if none; and the
    number of positions with max over S of g > tau_q, the position-level condition the pre-registered rules report as a looser third
    fraction. Returns (t_star, n_touched), both (B,) int64."""
    keys = sorted(g)
    B, T = g[keys[0]].shape[:2]
    best = torch.zeros((B, T), dtype=torch.float32, device=g[keys[0]].device)
    for k in keys:
        sel = rho_erase[k].bool()
        if bool(sel.any()):
            best = torch.maximum(best, g[k][..., sel].float().amax(dim=-1))
    touched = best > tau_q
    t_star = torch.where(touched.any(dim=1), touched.float().argmax(dim=1), torch.full((B,), T, device=best.device))
    return t_star.to(torch.int64), touched.sum(dim=1).to(torch.int64)
