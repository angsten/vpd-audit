"""The weight norm ||U_c|| ||V_c|| per subcomponent from a model's components, in the global index."""

from __future__ import annotations

import math

import numpy as np
import torch

from vpd_audit.weight_norms import exact_row_norms, weight_norms


class _Comp:
    def __init__(self, U: torch.Tensor, V: torch.Tensor):
        self.U, self.V = U, V


class _Model:
    def __init__(self):
        torch.manual_seed(0)
        self.module_to_c = {"h.1.mlp.c_fc": 3, "h.0.attn.q_proj": 2}  # unsorted on purpose
        self.components = {"h-0-attn-q_proj": _Comp(torch.randn(2, 5), torch.randn(4, 2)), "h.1.mlp.c_fc": _Comp(torch.randn(3, 5), torch.randn(4, 3))}


def test_weight_norms_are_row_norms_of_U_times_column_norms_of_V_in_global_order():
    m = _Model()
    norms, meta = weight_norms(m)
    assert norms.shape == (5,) and norms.dtype == np.float64 and meta["n_sub"] == 5
    a, b = m.components["h-0-attn-q_proj"], m.components["h.1.mlp.c_fc"]
    torch_norms = np.concatenate([(a.U.double().norm(dim=1) * a.V.double().norm(dim=0)).numpy(), (b.U.double().norm(dim=1) * b.V.double().norm(dim=0)).numpy()])  # sorted module order: h.0 then h.1
    assert np.allclose(norms, torch_norms, rtol=1e-14, atol=0)
    for c in range(2):  # the exact definition: the correctly rounded sum of squares, then sqrt, then the product
        u, v = a.U[c].double().numpy(), a.V[:, c].double().numpy()
        assert norms[c] == math.sqrt(math.fsum((u * u).tolist())) * math.sqrt(math.fsum((v * v).tolist()))
    assert meta["sha256"] == weight_norms(m)[1]["sha256"] and set(meta["per_module"]) == set(m.module_to_c)
    # the exact row norms do not depend on the summation order the caller might have used
    A = np.array([[1e16, 1.0, -1e16, 1.0], [3.0, 4.0, 0.0, 0.0]])
    assert np.array_equal(exact_row_norms(A), [math.sqrt(2e32 + 2.0), 5.0]) and exact_row_norms(A)[0] == math.sqrt(math.fsum([1e32, 1.0, 1e32, 1.0]))
