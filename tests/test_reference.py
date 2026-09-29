"""The mask check A7 (the residual follows the background) applied to the reference conditions: the residual
rule is stated for every kind, `delta_background="r1"` overrides it, and the two residual test
cells share their component masks bitwise with the conditions they modify. Synthetic tensors with pairwise-distinct
axis sizes: B = 2, T = 5, C = 7 and 3."""

import torch

from vpd_audit.masks import uniform_background
from vpd_audit.reference import (
    CONDITION_BY_NAME,
    CONDITIONS,
    RESIDUAL_TEST_CONDITIONS,
    Condition,
    build_condition_masks,
    cells_for,
    default_delta_background,
)

B, T, C1, C2 = 2, 5, 7, 3
MODULE_TO_C = {"a.first": C1, "b.second": C2}
SEED = (0, "u", 1, 3)  # (master, "u", draw, subbatch_index) for draw 1 on sub-batch 3


def _g() -> dict[str, torch.Tensor]:
    gen = torch.Generator().manual_seed(7)
    out = {}
    for k, c in MODULE_TO_C.items():
        g = torch.rand((B, T, c), generator=gen)
        g[g < 0.3] = 0.0
        g[g > 0.9] = 1.0
        out[k] = g
    return out


def _build(name: str, g, draw: int = 1, subbatch_index: int = 3):
    return build_condition_masks(CONDITION_BY_NAME[name], g, MODULE_TO_C, draw=draw, subbatch_index=subbatch_index, master_seed=0)


def test_default_delta_background_states_every_kind():
    kinds = {c.kind for c in CONDITIONS if c.kind != "target"}
    assert kinds == {"ones", "uniform", "rounded", "importances", "zero_all", "random_illegal"}
    assert default_delta_background("ones") == "r1"
    assert default_delta_background("uniform") == "uniform"
    for kind in ("rounded", "importances", "zero_all", "random_illegal"):
        assert default_delta_background(kind) == "r0"


def test_residual_rule_by_kind_when_included():
    g = _g()
    ones = torch.ones(B, T)
    # ones -> r1
    masks, deltas = _build("unmasked_delta", g)
    assert deltas is not None and all(torch.equal(deltas[k], ones) for k in MODULE_TO_C)
    assert all(torch.equal(masks[k], torch.ones_like(g[k])) for k in MODULE_TO_C)
    # uniform -> the uniform scalar of the same seed tuple, per module
    _, u_delta = uniform_background(SEED, MODULE_TO_C, B, T, dtype=torch.float32, device="cpu")
    masks, deltas = _build("stochastic_delta", g)
    assert deltas is not None and all(torch.equal(deltas[k], u_delta[k]) for k in MODULE_TO_C)
    assert all(deltas[k].shape == (B, T) for k in MODULE_TO_C)
    # every other kind -> r0 (a hypothetical included rounded row)
    rounded_incl = Condition("rounded_0.1_delta", "rounded", "included", False, False, threshold=0.1)
    masks, deltas = build_condition_masks(rounded_incl, g, MODULE_TO_C, draw=0, subbatch_index=0, master_seed=0)
    assert deltas is not None and all(torch.equal(deltas[k], torch.zeros(B, T)) for k in MODULE_TO_C)
    # excluded -> no residual masks, whatever the kind
    for name in ("unmasked", "stochastic", "rounded_0.1", "importances", "zero_all", "random_illegal"):
        _, deltas = _build(name, g)
        assert deltas is None, name


def test_delta_background_r1_forces_ones_and_shares_component_masks():
    g = _g()
    ones = torch.ones(B, T)
    # importances_delta1: masks bitwise g, residual ones, permitted
    cond = CONDITION_BY_NAME["importances_delta1"]
    assert cond.kind == "importances" and cond.delta == "included" and cond.delta_background == "r1" and cond.permitted and not cond.per_draw
    masks, deltas = _build("importances_delta1", g)
    assert all(torch.equal(masks[k], g[k]) for k in MODULE_TO_C)
    assert deltas is not None and all(torch.equal(deltas[k], ones) for k in MODULE_TO_C)
    m_imp, d_imp = _build("importances", g)
    assert d_imp is None and all(torch.equal(masks[k], m_imp[k]) for k in MODULE_TO_C)
    # stochastic_delta1: residual ones; component masks bitwise those of stochastic and stochastic_delta, same draw and sub-batch
    cond = CONDITION_BY_NAME["stochastic_delta1"]
    assert cond.kind == "uniform" and cond.delta == "included" and cond.delta_background == "r1" and cond.permitted and cond.per_draw
    m1, d1 = _build("stochastic_delta1", g)
    m0, d0 = _build("stochastic", g)
    mu, du = _build("stochastic_delta", g)
    assert d0 is None and du is not None and d1 is not None
    for k in MODULE_TO_C:
        assert torch.equal(m1[k], m0[k]) and torch.equal(m1[k], mu[k])
        assert torch.equal(d1[k], ones) and not torch.equal(du[k], ones)
    # a different draw or sub-batch changes the component masks (the seed tuple carries both)
    m_other, _ = _build("stochastic_delta1", g, draw=0, subbatch_index=3)
    assert not all(torch.equal(m_other[k], m1[k]) for k in MODULE_TO_C)
    m_other, _ = _build("stochastic_delta1", g, draw=1, subbatch_index=2)
    assert not all(torch.equal(m_other[k], m1[k]) for k in MODULE_TO_C)


def test_residual_test_conditions_are_beside_not_inside_conditions():
    names = [c.name for c in CONDITIONS]
    assert "importances_delta1" not in names and "stochastic_delta1" not in names
    assert [c.name for c in RESIDUAL_TEST_CONDITIONS] == ["importances_delta1", "stochastic_delta1"]
    assert cells_for(RESIDUAL_TEST_CONDITIONS, 2) == ["importances_delta1", "stochastic_delta1/k0", "stochastic_delta1/k1"]
    # every condition of the acceptance keeps the default residual rule (delta_background None)
    assert all(c.delta_background is None for c in CONDITIONS)
