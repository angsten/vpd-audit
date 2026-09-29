"""The rank measurement on synthetic matrices: with the components equal to the top-C singular triplets of W the
residual is exactly the Eckart-Young deficit and lies outside both spans; with an arbitrary rank-C factorization it
exceeds the floor. Shapes 6 x 5 with C = 3 (a deficit) and 6 x 5 with C = 5 (no deficit)."""

import pytest
import torch

from vpd_audit.residual_rank import rank_measurement

torch.manual_seed(0)


def test_optimal_components_leave_exactly_the_deficit():
    d_out, d_in, C = 6, 5, 3
    W = torch.randn(d_out, d_in, dtype=torch.float64)
    Ql, S, Qr = torch.linalg.svd(W, full_matrices=False)  # W = Ql diag(S) Qr
    V = (Qr[:C].T * S[:C])  # (d_in, C): read directions scaled by the singular values
    U = Ql[:, :C].T  # (C, d_out): write directions
    m = rank_measurement(W, U, V)
    floor = float(S[C:].square().sum())
    assert m["eckart_young_floor"] == pytest.approx(floor) and m["delta_fro_sq"] == pytest.approx(floor, rel=1e-9)
    assert m["delta_sq_over_floor"] == pytest.approx(1.0, rel=1e-9)
    assert m["frac_in_U_colspan"] == pytest.approx(0.0, abs=1e-12) and m["frac_in_V_rowspan"] == pytest.approx(0.0, abs=1e-12)
    assert m["frac_in_both"] == pytest.approx(0.0, abs=1e-12) and m["frac_outside_both"] == pytest.approx(1.0, rel=1e-9)
    assert m["rank_U_span"] == C and m["rank_V_span"] == C and m["rank_components_weight"] == C
    assert m["sigma_C_plus_1"] == pytest.approx(float(S[C])) and m["W_fro"] == pytest.approx(float(W.norm()))
    assert len(m["singular_values"]) == min(d_out, d_in) and m["singular_values"] == sorted(m["singular_values"], reverse=True)


def test_arbitrary_components_exceed_the_floor_and_the_decomposition_is_orthogonal():
    d_out, d_in, C = 6, 5, 3
    W = torch.randn(d_out, d_in, dtype=torch.float64)
    U = torch.randn(C, d_out, dtype=torch.float64)
    V = torch.randn(d_in, C, dtype=torch.float64)
    m = rank_measurement(W, U, V)
    assert m["delta_sq_over_floor"] > 1.0
    for key in ("frac_in_U_colspan", "frac_in_V_rowspan", "frac_in_both", "frac_outside_both"):
        assert 0.0 <= m[key] <= 1.0 + 1e-12
    assert m["frac_in_both"] <= min(m["frac_in_U_colspan"], m["frac_in_V_rowspan"]) + 1e-12
    # the four-way split PΔQ, PΔ(1-Q), (1-P)ΔQ, (1-P)Δ(1-Q) is orthogonal in the Frobenius norm, so the pieces sum to 1
    assert m["frac_in_U_colspan"] + m["frac_in_V_rowspan"] - m["frac_in_both"] + m["frac_outside_both"] == pytest.approx(1.0, rel=1e-9)


def test_no_deficit_when_C_covers_the_rank():
    d_out, d_in, C = 6, 5, 5
    W = torch.randn(d_out, d_in, dtype=torch.float64)
    U = torch.randn(C, d_out, dtype=torch.float64)
    V = torch.randn(d_in, C, dtype=torch.float64)
    m = rank_measurement(W, U, V)
    assert m["eckart_young_floor"] == 0.0 and m["delta_sq_over_floor"] is None and m["sigma_C_plus_1"] is None
    assert m["rank_V_span"] == 5 and m["frac_in_V_rowspan"] == pytest.approx(1.0, rel=1e-9)  # the read directions fill R^5
