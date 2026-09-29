"""The importance tensor g for a sub-batch.

Fixed everywhere: chunks of exactly 32 sequences, `torch.no_grad`, bf16 autocast on CUDA or
float32 with autocast off on CPU, `model(batch, cache_type="input")` for the target logits and
the clean inputs of all decomposed matrices, then
`model.calc_causal_importances(cache, sampling="continuous", detach_inputs=False)`, keeping
only `lower_leaky` (that is g) and dropping the other two fields at once. Per-matrix arrays
are kept in `sorted(model.module_to_c)` order. g is never computed from a masked forward.
"""

from __future__ import annotations

import contextlib
import re
from dataclasses import dataclass
from typing import Any

import torch
from torch import Tensor

from vpd_audit.constants import IMPORTANCE_CHUNK, SEQ_LEN

Precision = str  # "fp32" or "bf16"
_LAYER_RE = re.compile(r"^h\.(\d+)\.")


def module_keys(model: Any) -> list[str]:
    return sorted(model.module_to_c)


def layer_of(key: str) -> int:
    m = _LAYER_RE.match(key)
    assert m, f"module key {key!r} does not name a layer"
    return int(m.group(1))


def autocast_context(device: torch.device | str, precision: Precision):
    """bf16 autocast on CUDA (the authors' `bf16_autocast`); nothing on CPU / in float32."""
    dev = torch.device(device)
    if precision == "bf16":
        assert dev.type == "cuda", "bf16 autocast is used only on CUDA; CPU runs in float32"
        return torch.autocast(device_type="cuda", dtype=torch.bfloat16, enabled=True)
    assert precision == "fp32", precision
    return contextlib.nullcontext()


@dataclass
class Importances:
    g: dict[str, Tensor]  # sorted module keys; each (B, T, C_l), in [0, 1]
    target_logits: Tensor  # (B, T, V); bf16 under autocast, float32 otherwise
    chunk: int
    precision: Precision


def compute_importances(model: Any, batch: Tensor, *, precision: Precision, chunk: int = IMPORTANCE_CHUNK) -> Importances:
    """g and the target logits for `batch` of shape (B, 512), computed in chunks of `chunk`."""
    assert batch.ndim == 2 and batch.shape[1] == SEQ_LEN, f"batch must be (B, {SEQ_LEN}), got {tuple(batch.shape)}"
    B = batch.shape[0]
    assert B <= chunk or B % chunk == 0, f"B={B} must be at most or a multiple of the chunk {chunk}"
    device = next(model.parameters()).device
    keys = module_keys(model)
    g_parts: dict[str, list[Tensor]] = {k: [] for k in keys}
    logits_parts: list[Tensor] = []
    with torch.no_grad(), autocast_context(device, precision):
        for s in range(0, B, chunk):
            sub = batch[s : s + chunk].to(device)
            out = model(sub, cache_type="input")  # clean forward: target logits + inputs of all matrices
            assert set(out.cache) == set(model.module_to_c), "cache must hold every decomposed module's input"
            ci = model.calc_causal_importances(out.cache, sampling="continuous", detach_inputs=False)
            lower = ci.lower_leaky
            del ci  # drop upper_leaky and pre_sigmoid at once
            assert set(lower) == set(model.module_to_c)
            for k in keys:
                t = lower[k]
                assert t.shape == (sub.shape[0], SEQ_LEN, model.module_to_c[k]), (k, tuple(t.shape))
                g_parts[k].append(t)
            logits_parts.append(out.output)
            del out, lower
    g = {k: torch.cat(g_parts[k], dim=0) for k in keys}
    logits = torch.cat(logits_parts, dim=0)
    assert logits.shape[:2] == (B, SEQ_LEN), tuple(logits.shape)
    for k in keys:
        assert g[k].shape[0] == B
        assert float(g[k].min()) >= 0.0 and float(g[k].max()) <= 1.0, f"g out of [0, 1] for {k}"
    return Importances(g=g, target_logits=logits, chunk=chunk, precision=precision)


# ----------------------------------------------------------------------------- statistics


@dataclass
class ImportanceSums:
    """Accumulated over sub-batches: counts of g > threshold per module and sums of g per subcomponent."""

    n_positions: int
    count_positive: dict[str, int]  # entries with g > 0, per module
    count_above: dict[str, dict[str, int]]  # threshold -> module -> entries with g > threshold
    sum_g: dict[str, Tensor]  # per module, (C_l,) float64 sum of g over (b, t)

    @classmethod
    def empty(cls, model: Any, thresholds: tuple[float, ...] = (0.0, 0.1, 0.5)) -> "ImportanceSums":
        keys = module_keys(model)
        return cls(
            n_positions=0,
            count_positive={k: 0 for k in keys},
            count_above={str(t): {k: 0 for k in keys} for t in thresholds},
            sum_g={k: torch.zeros(model.module_to_c[k], dtype=torch.float64) for k in keys},
        )

    def update(self, g: dict[str, Tensor]) -> None:
        first = next(iter(g.values()))
        self.n_positions += first.shape[0] * first.shape[1]
        for k, t in g.items():
            self.count_positive[k] += int((t > 0).sum())
            for thr in self.count_above:
                self.count_above[thr][k] += int((t > float(thr)).sum())
            self.sum_g[k] += t.sum(dim=(0, 1), dtype=torch.float64).cpu()  # upcast before the sum, not after

    def per_layer_mean_count(self) -> dict[str, float]:
        """Mean count of g > 0 per position, per layer and in total (the paper's L0)."""
        out: dict[str, float] = {}
        for k, c in self.count_positive.items():
            key = f"layer_{layer_of(k)}"
            out[key] = out.get(key, 0.0) + c / self.n_positions
        out["total"] = sum(v for kk, v in out.items() if kk.startswith("layer_"))
        return out

    def alive_counts(self, threshold: float = 1e-6) -> dict[str, int]:
        """Subcomponents whose mean g over the positions seen exceeds `threshold`, per layer and total."""
        out: dict[str, int] = {}
        for k, s in self.sum_g.items():
            key = f"layer_{layer_of(k)}"
            out[key] = out.get(key, 0) + int(((s / self.n_positions) > threshold).sum())
        out["total"] = sum(v for kk, v in out.items() if kk.startswith("layer_"))
        return out

    def to_json(self) -> dict[str, Any]:
        return {
            "n_positions": self.n_positions,
            "count_positive": self.count_positive,
            "count_above": self.count_above,
            "sum_g": {k: v.tolist() for k, v in self.sum_g.items()},
        }

    @classmethod
    def from_json(cls, d: dict[str, Any]) -> "ImportanceSums":
        return cls(
            n_positions=int(d["n_positions"]),
            count_positive={k: int(v) for k, v in d["count_positive"].items()},
            count_above={t: {k: int(v) for k, v in m.items()} for t, m in d["count_above"].items()},
            sum_g={k: torch.tensor(v, dtype=torch.float64) for k, v in d["sum_g"].items()},
        )
