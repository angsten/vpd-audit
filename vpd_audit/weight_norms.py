"""The weight norm ||U_c|| ||V_c|| of every subcomponent, from the loaded model, in the global index.

For each decomposed matrix W_l with the components' read directions V (d_in x C_l) and write directions U (C_l x d_out),
as `residual_rank.components_by_name` reads them, subcomponent c's norm is the Euclidean norm of U's row c times the
Euclidean norm of V's column c, in float64; the vector is laid out in `sorted(module_to_c)` order with `module_offsets`,
like every source. Its SHA-256 goes into every ranked source record and the pre-reads manifest, so a launch and the
pre-reads that cover it can be shown to have used the same ordering. The norms are computed so that the vector is the
same bytes on any device and machine: the squares in float64 (one IEEE rounding each), their sum by `math.fsum` (the
correctly rounded sum, independent of any reduction order), the square root and the product one rounding each. A torch
reduction on the card and on a CPU gave two hashes for the stand-in's model; this path gives one.
"""

from __future__ import annotations

import hashlib
import math
from typing import Any

import numpy as np

from vpd_audit.sources import module_offsets


def exact_row_norms(A: np.ndarray) -> np.ndarray:
    """(n, d) float64 -> (n,): sqrt of the correctly rounded sum of the squares of each row."""
    A = np.ascontiguousarray(A, dtype=np.float64)
    return np.array([math.sqrt(math.fsum((a * a).tolist())) for a in A], dtype=np.float64)


def weight_norms(model: Any) -> tuple[np.ndarray, dict[str, Any]]:
    from vpd_audit.residual_rank import components_by_name

    comps = components_by_name(model)
    module_to_c = {k: int(v) for k, v in model.module_to_c.items()}
    offsets = module_offsets(module_to_c)
    n_sub = sum(module_to_c.values())
    out = np.zeros(n_sub, dtype=np.float64)
    per_module: dict[str, dict[str, float]] = {}
    for k in sorted(module_to_c):
        U, V = comps[k].U.detach().double().cpu().numpy(), comps[k].V.detach().double().cpu().numpy()
        C = module_to_c[k]
        assert U.shape[0] == C and V.shape[1] == C, (k, tuple(U.shape), tuple(V.shape), C)
        norms = exact_row_norms(U) * exact_row_norms(V.T)
        out[offsets[k] : offsets[k] + C] = norms
        per_module[k] = {"min": float(norms.min()), "median": float(np.median(norms)), "max": float(norms.max())}
    assert np.all(np.isfinite(out))
    meta = {"sha256": hashlib.sha256(np.ascontiguousarray(out).tobytes()).hexdigest(), "n_sub": int(n_sub), "per_module": per_module,
            "definition": "||U_c|| ||V_c|| in float64 from the components' write and read directions (residual_rank.components_by_name), global index order; "
                          "squares in float64, sums by math.fsum (correctly rounded), so the bytes are device- and machine-independent"}
    return out, meta
