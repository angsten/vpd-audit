"""The mask checks A5 (source and mask shapes), A6 (the uniform background from its seed tuple) and A7 (the residual
follows the background), on synthetic tensors with pairwise-distinct axis sizes: B = 2, T = 5, C = 7, and a second
matrix with C = 3."""

import pytest
import torch

from vpd_audit.masks import (
    apply_binary_source,
    apply_source,
    residual_mask,
    rounded_mask,
    seed_from_tuple,
    uniform_background,
    wrap_masks,
)

B, T, C1, C2 = 2, 5, 7, 3
MODULE_TO_C = {"a.first": C1, "b.second": C2}


class FakeModel:
    module_to_c = MODULE_TO_C


def _g(C: int, seed: int = 0) -> torch.Tensor:
    gen = torch.Generator().manual_seed(seed)
    g = torch.rand((B, T, C), generator=gen)
    g[g < 0.3] = 0.0  # exact zeros like the clamp
    return g


# --------------------------------------------------------------------------- A5 shapes


def test_a5_source_and_mask_shapes():
    g1, g2 = _g(C1), _g(C2, 1)
    rho1 = torch.tensor([1, 0, 1, 0, 0, 1, 0], dtype=torch.float32)
    rho2 = torch.tensor([0, 1, 0], dtype=torch.float32)
    assert rho1.shape == (C1,) and rho2.shape == (C2,)
    m1, m2 = apply_binary_source(g1, rho1), apply_binary_source(g2, rho2)
    assert m1.shape == (B, T, C1) and m2.shape == (B, T, C2)
    # the formula, exactly
    assert torch.equal(m1, g1 + (1 - g1) * rho1)
    assert torch.equal(m2, g2 + (1 - g2) * rho2)
    # nothing goes below its label; named subcomponents are 1
    assert (m1 >= g1).all() and (m1[..., rho1.bool()] == 1).all()


def test_a5_source_of_length_T_raises():
    g1 = _g(C1)
    rho_T = torch.ones(T)  # length T = 5, not C = 7
    with pytest.raises(AssertionError):
        apply_binary_source(g1, rho_T)


def test_a5_mask_of_shape_BT_raises():
    g1 = _g(C1)
    with pytest.raises(AssertionError):
        apply_source(g1, torch.rand(B, T))  # a (B, T) source
    with pytest.raises(AssertionError):
        apply_source(g1, torch.rand(B, T, C2))  # the other matrix's C


def test_a5_wrap_requires_every_module_and_BT_residual():
    g1, g2 = _g(C1), _g(C2, 1)
    masks = {"a.first": torch.ones_like(g1), "b.second": torch.ones_like(g2)}
    infos = wrap_masks(FakeModel(), masks)
    assert set(infos) == set(MODULE_TO_C)
    with pytest.raises(AssertionError):
        wrap_masks(FakeModel(), {"a.first": torch.ones_like(g1)})  # a module omitted
    deltas_ok = {k: torch.ones(B, T) for k in MODULE_TO_C}
    weight_deltas = {"a.first": torch.zeros(4, 4), "b.second": torch.zeros(4, 4)}
    infos = wrap_masks(FakeModel(), masks, deltas_ok, weight_deltas)
    assert all(infos[k].weight_delta_and_mask is not None for k in MODULE_TO_C)
    with pytest.raises(AssertionError):
        wrap_masks(FakeModel(), masks, {"a.first": torch.ones(B, T, C1), "b.second": torch.ones(B, T)}, weight_deltas)
    with pytest.raises(AssertionError):
        wrap_masks(FakeModel(), masks, {"a.first": torch.ones(T, B), "b.second": torch.ones(B, T)}, weight_deltas)


def test_rounded_mask_uses_strict_greater():
    g = torch.tensor([[[0.0, 0.1, 0.10001, 0.5, 0.9, 1.0, 0.05]]])
    assert torch.equal(rounded_mask(g, 0.1), torch.tensor([[[0.0, 0.0, 1.0, 1.0, 1.0, 1.0, 0.0]]]))
    assert torch.equal(rounded_mask(g, 0.0), torch.tensor([[[0.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0]]]))
    assert torch.equal(rounded_mask(g, 0.5), torch.tensor([[[0.0, 0.0, 0.0, 0.0, 1.0, 1.0, 0.0]]]))


# --------------------------------------------------------------------------- A6 uniform background


def test_a6_uniform_background_from_seed_tuple():
    u1, d1 = uniform_background((0, "u", 3, 2), MODULE_TO_C, B, T, dtype=torch.float32, device="cpu")
    u2, d2 = uniform_background((0, "u", 3, 2), MODULE_TO_C, B, T, dtype=torch.float32, device="cpu")
    assert set(u1) == set(MODULE_TO_C) and u1["a.first"].shape == (B, T, C1) and u1["b.second"].shape == (B, T, C2)
    assert d1["a.first"].shape == (B, T) and d1["b.second"].shape == (B, T)
    for k in MODULE_TO_C:
        assert torch.equal(u1[k], u2[k]) and torch.equal(d1[k], d2[k])  # drawn twice: identical
    u3, d3 = uniform_background((0, "u", 4, 2), MODULE_TO_C, B, T, dtype=torch.float32, device="cpu")
    u4, _ = uniform_background((1, "u", 3, 2), MODULE_TO_C, B, T, dtype=torch.float32, device="cpu")
    assert not torch.equal(u1["a.first"], u3["a.first"]) and not torch.equal(u1["a.first"], u4["a.first"])
    assert not torch.equal(d1["a.first"], d3["a.first"])
    # the same tensor serves every rung of one draw: the tuple carries no rung
    rung0 = uniform_background((0, "u", 3, 2), MODULE_TO_C, B, T, dtype=torch.float32, device="cpu")[0]
    rung8 = uniform_background((0, "u", 3, 2), MODULE_TO_C, B, T, dtype=torch.float32, device="cpu")[0]
    assert all(torch.equal(rung0[k], rung8[k]) for k in MODULE_TO_C)
    assert seed_from_tuple((0, "u", 3, 2)) == seed_from_tuple((0, "u", 3, 2)) != seed_from_tuple((0, "u", 2, 3))
    assert all((0 <= u1[k]).all() and (u1[k] < 1).all() for k in MODULE_TO_C)


def test_a6_uniform_masks_gated_by_g():
    g1 = _g(C1)
    u, _ = uniform_background((0, "u", 0, 0), MODULE_TO_C, B, T, dtype=torch.float32, device="cpu")
    m = apply_source(g1, u["a.first"])
    assert torch.equal(m, g1 + (1 - g1) * u["a.first"])
    assert (m >= g1).all() and (m[g1 == 1] == 1).all() and torch.equal(m[g1 == 0], u["a.first"][g1 == 0])


# --------------------------------------------------------------------------- A7 the residual rule


def test_a7_residual_follows_the_background():
    g1 = _g(C1)
    u, u_delta = uniform_background((0, "u", 1, 0), MODULE_TO_C, B, T, dtype=torch.float32, device="cpu")
    # a synthetic (C + 1)-th column with g = 0 for the residual
    g_aug = torch.cat([g1, torch.zeros(B, T, 1)], dim=-1)
    for background, value, expected in (("r0", 0.0, torch.zeros(B, T)), ("r1", 1.0, torch.ones(B, T)), ("hard_zero", 1.0, torch.ones(B, T))):
        rho_aug = torch.cat([torch.zeros(C1), torch.tensor([value])])
        m_aug = apply_binary_source(g_aug, rho_aug)
        r = residual_mask(background, B, T, u_delta=None, dtype=torch.float32, device="cpu")
        assert r.shape == (B, T) and torch.equal(r, expected) and torch.equal(m_aug[..., -1], expected)
    r_aug = torch.cat([u["a.first"], u_delta["a.first"].unsqueeze(-1)], dim=-1)
    m_aug = apply_source(g_aug, r_aug)
    r = residual_mask("uniform", B, T, u_delta=u_delta["a.first"], dtype=torch.float32, device="cpu")
    assert torch.equal(r, u_delta["a.first"]) and torch.equal(m_aug[..., -1], u_delta["a.first"])
    with pytest.raises(AssertionError):
        residual_mask("uniform", B, T, u_delta=torch.rand(B, T, 1), dtype=torch.float32, device="cpu")
    with pytest.raises(AssertionError):
        residual_mask("uniform", B, T, u_delta=None, dtype=torch.float32, device="cpu")


def test_a5_wrap_rejects_transposed_and_mismatched_masks():
    g1, g2 = _g(C1), _g(C2, 1)
    good = {"a.first": torch.ones_like(g1), "b.second": torch.ones_like(g2)}
    wrap_masks(FakeModel(), good)
    with pytest.raises(AssertionError):  # (B, C, T): last axis is T, not C
        wrap_masks(FakeModel(), {"a.first": torch.ones(B, C1, T), "b.second": torch.ones_like(g2)})
    with pytest.raises(AssertionError):  # (T, B, C) for one module only: leading axes disagree
        wrap_masks(FakeModel(), {"a.first": torch.ones(T, B, C1), "b.second": torch.ones_like(g2)})
    with pytest.raises(AssertionError):  # the other matrix's C
        wrap_masks(FakeModel(), {"a.first": torch.ones(B, T, C2), "b.second": torch.ones_like(g2)})
    with pytest.raises(AssertionError):  # (C,) source handed in as a mask
        wrap_masks(FakeModel(), {"a.first": torch.ones(C1), "b.second": torch.ones_like(g2)})


# --------------------------------------------------------------------------- the wired-in forward wrapper


class TinyModel(torch.nn.Module):
    """A stand-in with the interface `masked_forward` uses: module_to_c, parameters, forward(batch, mask_infos)."""

    module_to_c = MODULE_TO_C
    V = 11

    def __init__(self):
        super().__init__()
        self.emb = torch.nn.Parameter(torch.randn(13, self.V, generator=torch.Generator().manual_seed(3)))

    def forward(self, batch, mask_infos=None):
        # the logits depend on the masks so that the wrapper's outputs are not trivially constant
        scale = sum(float(info.component_mask.float().mean()) for info in mask_infos.values())
        delta = sum(float(info.weight_delta_and_mask[1].float().mean()) for info in mask_infos.values() if info.weight_delta_and_mask is not None)
        return self.emb[batch % 13] * (1 + scale) + delta


def test_masked_forward_fingerprints_the_tensors_it_hands_to_the_forward():
    from vpd_audit.constants import SEQ_LEN
    from vpd_audit.fingerprint import fingerprint, level3_hex, mask_counts, sha256_masks
    from vpd_audit.masks import masked_forward

    model = TinyModel()
    Bt = 2
    gen = torch.Generator().manual_seed(9)
    g = {k: torch.rand((Bt, SEQ_LEN, c), generator=gen) for k, c in MODULE_TO_C.items()}
    for k in g:
        g[k][g[k] < 0.3] = 0.0
    masks = {k: torch.where(torch.rand(c, generator=gen) < 0.5, torch.tensor(1.0), g[k]) for k, c in MODULE_TO_C.items()}
    deltas = {k: torch.ones(Bt, SEQ_LEN) for k in MODULE_TO_C}
    weight_deltas = {k: torch.zeros(3, 3) for k in MODULE_TO_C}
    batch = torch.randint(0, 13, (Bt, SEQ_LEN), generator=gen)
    fr = masked_forward(model, batch, masks, g, permitted=True, precision="fp32", delta_masks=deltas, weight_deltas=weight_deltas, do_sha256=True)
    assert fr.logits.shape == (Bt, SEQ_LEN, TinyModel.V) and fr.delta_included and fr.min_gap >= 0 and fr.n_below_label == 0
    # the fingerprint is that of the mask tensors, unchanged by wrapping
    direct = fingerprint(masks, deltas)
    assert torch.equal(fr.fp.phi, direct.phi) and all(torch.equal(fr.fp.h[k], direct.h[k]) and torch.equal(fr.fp.hd[k], direct.hd[k]) for k in MODULE_TO_C)
    assert level3_hex(fr.fp, [0, 1]) == level3_hex(direct, [0, 1])
    assert fr.sha256 == sha256_masks(masks, deltas) and len(fr.sha256) == 64
    # the two counts per module
    for k in MODULE_TO_C:
        assert (fr.n_ne_g[k], fr.n_ne_one[k]) == mask_counts(masks[k], g[k])
        assert fr.n_ne_g[k] == int((masks[k] != g[k]).sum()) and fr.n_ne_one[k] == int((masks[k] != 1).sum())
    # residual excluded: no hd, no sha unless asked
    fr2 = masked_forward(model, batch, masks, g, permitted=True, precision="fp32")
    assert fr2.fp.hd is None and fr2.fp.rho == 0 and fr2.sha256 == "" and not fr2.delta_included
    assert level3_hex(fr2.fp, [0, 1])["F"] != level3_hex(fr.fp, [0, 1])["F"]
    # a direct (non-permitted) mask below its label is counted, not asserted
    below = {k: torch.zeros_like(g[k]) for k in MODULE_TO_C}
    fr3 = masked_forward(model, batch, below, g, permitted=False, precision="fp32")
    assert fr3.n_below_label > 0 and fr3.min_gap < 0
    with pytest.raises(AssertionError):
        masked_forward(model, batch, below, g, permitted=True, precision="fp32")


def test_image_copy_ignores_credentials():
    from pathlib import Path

    from vpd_audit.modal_app import _ignore_submodule

    assert all(_ignore_submodule(Path(p)) for p in (".env", "a/.env", "a/b/.env.local", ".env.production", "x/.venv/lib/site.py", "a/.git/HEAD"))
    assert not any(_ignore_submodule(Path(p)) for p in ("param_decomp/data.py", "a/environment.yaml", "a/.envrc", "README.md"))


# --------------------------------------------------------------------------- the chunked P3 check (no permitted mask below its label)

def _p3_reference(masks, g):
    """The P3 quantities computed unchunked, as masked_forward computed them before the check was chunked."""
    from vpd_audit.constants import PERMITTED_TOL

    min_gap, n_below, below_pos, ne_g, ne_one = float("inf"), 0, None, {}, {}
    for k in sorted(masks):
        gap = masks[k].float() - g[k].float()
        min_gap = min(min_gap, float(gap.min()))
        below = gap < -PERMITTED_TOL
        n_below += int(below.sum())
        any_pos = below.any(dim=-1)
        below_pos = any_pos if below_pos is None else (below_pos | any_pos)
        ne_g[k], ne_one[k] = int((masks[k] != g[k]).sum()), int((masks[k] != 1).sum())
    return min_gap, n_below, int(below_pos.sum()), ne_g, ne_one


def test_p3_check_in_slabs_is_bitwise_the_unchunked_check_and_the_negative_tests():
    """B = 11 (a full slab of 8 and a short one of 3), masks with entries equal to g, equal to 1, one entry 2e-6 below its
    label in the second slab and one 5e-7 below it in the first (inside the tolerance): min_gap, n_below_label,
    n_positions_below_label, and the two counts per module equal the unchunked computation exactly; with permitted=True
    the 2e-6 entry raises, with permitted=False it is counted once, at one position."""
    from vpd_audit.constants import PERMITTED_TOL, SEQ_LEN
    from vpd_audit.masks import P3_SLAB, masked_forward

    assert P3_SLAB == 8
    model = TinyModel()
    Bt = 11
    gen = torch.Generator().manual_seed(11)
    g = {k: torch.rand((Bt, SEQ_LEN, c), generator=gen) for k, c in MODULE_TO_C.items()}
    for k in g:
        g[k][g[k] < 0.3] = 0.0
        g[k][g[k] > 0.9] = 1.0
    masks = {k: torch.where(torch.rand(c, generator=gen) < 0.5, torch.tensor(1.0), g[k]) for k, c in MODULE_TO_C.items()}
    good = {k: v.clone() for k, v in masks.items()}
    batch = torch.randint(0, 13, (Bt, SEQ_LEN), generator=gen)
    fr = masked_forward(model, batch, good, g, permitted=True, precision="fp32")
    ref = _p3_reference(good, g)
    assert fr.min_gap == ref[0] and fr.n_below_label == ref[1] == 0 and fr.n_positions_below_label == 0
    assert fr.n_ne_g == ref[3] and fr.n_ne_one == ref[4]
    # one entry 2e-6 below its label (second slab, b = 9, t = 100), one 5e-7 below (first slab, b = 2, t = 7): only the first counts
    bad = {k: v.clone() for k, v in masks.items()}
    k0 = "a.first"
    g[k0][9, 100, 0], g[k0][2, 7, 1] = 0.5, 0.5
    bad[k0][9, 100, 0] = 0.5 - 2e-6
    bad[k0][2, 7, 1] = 0.5 - 5e-7
    assert -2e-6 < -PERMITTED_TOL < -5e-7
    with pytest.raises(AssertionError, match="P3"):
        masked_forward(model, batch, bad, g, permitted=True, precision="fp32")
    fr2 = masked_forward(model, batch, bad, g, permitted=False, precision="fp32")
    ref2 = _p3_reference(bad, g)
    assert fr2.n_below_label == 1 and fr2.n_positions_below_label == 1
    assert (fr2.min_gap, fr2.n_below_label, fr2.n_positions_below_label, fr2.n_ne_g, fr2.n_ne_one) == ref2
    assert fr2.min_gap == float((bad[k0].float() - g[k0].float()).min()) and fr2.min_gap < -PERMITTED_TOL
    # two entries below the label at the same position count as one position, two positions as two
    bad[k0][9, 100, 2] = float(g[k0][9, 100, 2]) - 3e-6 if float(g[k0][9, 100, 2]) > 0 else 0.0
    bad[k0][0, 0, 3] = float(g[k0][0, 0, 3]) - 3e-6 if float(g[k0][0, 0, 3]) > 0 else 0.0
    g[k0][9, 100, 2], g[k0][0, 0, 3] = 0.7, 0.7
    bad[k0][9, 100, 2], bad[k0][0, 0, 3] = 0.7 - 3e-6, 0.7 - 3e-6
    fr3 = masked_forward(model, batch, bad, g, permitted=False, precision="fp32")
    assert (fr3.n_below_label, fr3.n_positions_below_label) == (3, 2) and (fr3.min_gap, fr3.n_below_label, fr3.n_positions_below_label, fr3.n_ne_g, fr3.n_ne_one) == _p3_reference(bad, g)
