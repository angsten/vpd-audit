"""A CPU measurement: is the residual the rank deficit of the components and nothing else?

For each of the 24 decomposed matrices W_l (d_out x d_in), with the components' read directions V (d_in x C_l) and
write directions U (C_l x d_out) so that their weight is (V U)^T and Delta_l = W_l - (V U)^T:
- the singular values sigma_i of W_l, descending;
- the Eckart-Young floor sum_{i > C_l} sigma_i^2: the smallest ||W_l - R||_F^2 any matrix R of rank C_l can reach,
  which is nonzero only where C_l < rank(W_l), that is for the 768 x 768 query and key matrices with C_l = 512;
- ||Delta_l||_F^2 measured, and its ratio to the floor: 1 means the components reach the optimal rank-C_l
  approximation and the residual is exactly the deficit; above 1, the residual carries more than the deficit;
- the fraction of Delta_l's Frobenius energy inside the column span of the write directions (P_U Delta), inside the row
  span of the read directions (Delta P_V), inside both, and outside both (an orthogonal decomposition in the Frobenius
  norm); where C_l >= d these spans are the whole space and the fractions are trivially 1;
- ||W_l||_F, and ||Delta_l||_F / ||W_l||_F.
Seconds on CPU; no forward pass. Output results/short_runs/residual_rank/summary.{json,md}.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import torch
from torch import Tensor

from vpd_audit.importances import layer_of, module_keys

RANK_REL_TOL = 1e-6  # numerical rank: singular values above this fraction of the largest


def _orthonormal_basis(A: Tensor) -> tuple[Tensor, int]:
    """An orthonormal basis (columns) of the column span of A (n x m), with its numerical rank."""
    Uo, So, _ = torch.linalg.svd(A, full_matrices=False)
    r = int((So > So.max() * RANK_REL_TOL).sum()) if So.numel() else 0
    return Uo[:, :r], r


def rank_measurement(W: Tensor, U: Tensor, V: Tensor) -> dict[str, Any]:
    """The measurement for one matrix: W (d_out, d_in), U (C, d_out), V (d_in, C); float64 throughout."""
    W, U, V = W.detach().double(), U.detach().double(), V.detach().double()
    d_out, d_in = W.shape
    C = U.shape[0]
    assert U.shape == (C, d_out) and V.shape == (d_in, C), (tuple(U.shape), tuple(V.shape), tuple(W.shape))
    Wc = (V @ U).T  # the components' weight, (d_out, d_in)
    Delta = W - Wc
    sig = torch.linalg.svdvals(W)  # descending
    floor = float(sig[C:].square().sum()) if C < sig.numel() else 0.0
    delta_sq = float(Delta.square().sum())
    QU, rank_U = _orthonormal_basis(U.T)  # span of the write directions in R^{d_out}
    QV, rank_V = _orthonormal_basis(V)  # span of the read directions in R^{d_in}
    PU_D = QU @ (QU.T @ Delta)
    D_PV = (Delta @ QV) @ QV.T
    PU_D_PV = (QU @ (QU.T @ Delta @ QV)) @ QV.T
    frac_U = float(PU_D.square().sum()) / delta_sq
    frac_V = float(D_PV.square().sum()) / delta_sq
    frac_both = float(PU_D_PV.square().sum()) / delta_sq
    rank_Wc = int((torch.linalg.svdvals(Wc) > torch.linalg.svdvals(Wc).max() * RANK_REL_TOL).sum())
    return {
        "d_out": d_out, "d_in": d_in, "C": C, "min_dim": min(d_out, d_in),
        "W_fro": float(W.norm()), "delta_fro": float(Delta.norm()), "delta_fro_sq": delta_sq, "delta_rel": float(Delta.norm() / W.norm()),
        "sigma_1": float(sig[0]), "sigma_C": float(sig[C - 1]) if C <= sig.numel() else None, "sigma_C_plus_1": float(sig[C]) if C < sig.numel() else None, "sigma_min": float(sig[-1]),
        "eckart_young_floor": floor, "delta_sq_over_floor": (delta_sq / floor) if floor > 0 else None,
        "frac_in_U_colspan": frac_U, "frac_in_V_rowspan": frac_V, "frac_in_both": frac_both, "frac_outside_both": 1.0 - frac_U - frac_V + frac_both,
        "rank_U_span": rank_U, "rank_V_span": rank_V, "rank_components_weight": rank_Wc,
        "singular_values": [float(x) for x in sig],
    }


def components_by_name(model: Any) -> dict[str, Any]:
    """The components keyed by the decomposed module's name (the authors' container may store dots as dashes)."""
    out = {}
    for name, comp in model.components.items():
        key = name if name in model.module_to_c else name.replace("-", ".")
        assert key in model.module_to_c, (name, key)
        out[key] = comp
    assert set(out) == set(model.module_to_c), (sorted(out), sorted(model.module_to_c))
    return out


def residual_rank(model: Any) -> dict[str, dict[str, Any]]:
    comps = components_by_name(model)
    out: dict[str, dict[str, Any]] = {}
    for k in module_keys(model):
        c = comps[k]
        m = rank_measurement(model.target_weight(k), c.U, c.V)
        m.update({"layer": layer_of(k), "type": k.split(".")[-1]})
        out[k] = m
    return out


COLUMN_SENTENCES: dict[str, str] = {
    "shape, C_l": "the matrix's (d_out x d_in) and its number of subcomponents; a sum of C_l rank-one terms cannot exceed rank C_l, so only where C_l < min(d_out, d_in) is there a rank deficit (the 768 x 768 query and key matrices with C_l = 512)",
    "||W_l||_F": "the size of the weight matrix, the scale the residual is measured against",
    "||Delta_l||_F / ||W_l||_F": "the residual's relative size",
    "sigma_{C_l+1}": "the first singular value of W_l that C_l rank-one terms cannot reach (blank where C_l covers the rank)",
    "floor": "the Eckart-Young floor sum_{i > C_l} sigma_i^2: the smallest ||W_l - R||_F^2 any rank-C_l matrix R can reach; zero where there is no deficit",
    "||Delta_l||_F^2": "the residual's measured Frobenius energy",
    "||Delta||^2 / floor": "1 means the components are the optimal rank-C_l approximation and the residual is exactly the deficit; above 1 the residual carries more than the deficit; undefined where the floor is zero",
    "in U span": "the fraction of Delta_l's energy inside the column span of the components' write directions: 1 means the residual writes only into directions the components already write to; trivially 1 where the write directions span the whole output space",
    "in V span": "the same for the row span of the read directions: the fraction of the residual that reads from directions the components read",
    "in both": "inside both spans at once",
    "outside both": "the residual's energy in directions the components neither read nor write, the part no re-weighting of existing subcomponents could absorb",
    "rank U, rank V": "the numerical ranks of the two spans (at 1e-6 of the largest singular value); equal to C_l where the directions are independent, to d where they fill the space",
}


def format_residual_rank(res: dict[str, dict[str, Any]]) -> str:
    L = ["# The residual against the components' rank: CPU, the main decomposition", ""]
    L.append("| module | layer | type | shape, C_l | ||W_l||_F | ||Delta_l||_F / ||W_l||_F | sigma_{C_l+1} | floor | ||Delta_l||_F^2 | ||Delta||^2 / floor | in U span | in V span | in both | outside both | rank U, rank V |")
    L.append("|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|")
    for k, m in res.items():
        s_c1 = "" if m["sigma_C_plus_1"] is None else f"{m['sigma_C_plus_1']:.4f}"
        over = "" if m["delta_sq_over_floor"] is None else f"{m['delta_sq_over_floor']:.3f}"
        L.append(f"| {k} | {m['layer']} | {m['type']} | {m['d_out']}x{m['d_in']}, {m['C']} | {m['W_fro']:.2f} | {m['delta_rel']:.4f} | {s_c1} | "
                 f"{m['eckart_young_floor']:.4f} | {m['delta_fro_sq']:.4f} | {over} | "
                 f"{m['frac_in_U_colspan']:.4f} | {m['frac_in_V_rowspan']:.4f} | {m['frac_in_both']:.4f} | {m['frac_outside_both']:.4f} | {m['rank_U_span']}, {m['rank_V_span']} |")
    L.append("")
    L.append("## What each column means")
    for col, sentence in COLUMN_SENTENCES.items():
        L.append(f"- **{col}**: {sentence}.")
    L.append("")
    qk = [m for m in res.values() if m["delta_sq_over_floor"] is not None]
    if qk:
        L.append(f"Where the floor is nonzero ({len(qk)} matrices): ||Delta||^2 / floor ranges from {min(m['delta_sq_over_floor'] for m in qk):.3f} to {max(m['delta_sq_over_floor'] for m in qk):.3f}; "
                 f"the residual's energy outside both spans ranges from {min(m['frac_outside_both'] for m in qk):.3f} to {max(m['frac_outside_both'] for m in qk):.3f}.")
    rest = [m for m in res.values() if m["delta_sq_over_floor"] is None]
    if rest:
        L.append(f"Where the floor is zero ({len(rest)} matrices): ||Delta_l||_F / ||W_l||_F ranges from {min(m['delta_rel'] for m in rest):.4f} to {max(m['delta_rel'] for m in rest):.4f}.")
    return "\n".join(L)
