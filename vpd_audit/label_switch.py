"""The label fix for decompositions trained before the label network rescaled its inputs.

At the authors' commit 28f6436 (5 February 2026), `GlobalSharedTransformerCiFn.forward` passes the raw inputs of the
decomposed matrices to its input projector. At the commit this repository pins, 74146b5 (16 May 2026), the same `forward`
first applies `F.rms_norm` to each input (`third_party/param-decomp/param_decomp/models/components.py`, in
`GlobalSharedTransformerCiFn.forward`). The parameters keep their names and shapes, so a checkpoint trained before the
rescaling existed loads into the pinned class without error, and then computes its labels from inputs it was never trained
on.

`apply_label_switch(model, run)` replaces `forward` on the one `GlobalSharedTransformerCiFn` instance inside `model` with
`_forward_without_input_rescaling` below: the pinned `forward` with the `F.rms_norm` call removed and nothing else changed.
The class, the weights, the transformer blocks, the sigmoids and the output split are untouched, and the pinned library is
not edited. It refuses a run whose `AuditRun.trained_before_ci_input_rescaling` is not set, and any label network that is
not exactly a `GlobalSharedTransformerCiFn`. `artifacts.load_component_model` applies it exactly for the runs with that
field set, which is the small-model mode (`simplestories`, decomposition `s-eab2ace8`, trained at 28f6436) only; the 67M
runs (`main`, `control`) were trained at 85c6b70, which already has the rescaling, and load unchanged.

The fix was verified outside this repository by bitwise agreement of the labels and of the own-label masked logits with the
authors' complete February code path at 28f6436, and by reproducing the run's logged scores (`logged_scores.py`).
"""

from __future__ import annotations

import types
from typing import Any

import torch
from torch import Tensor

PINNED_COMMIT = "74146b555f3eb3cd2bc639c3789fd3b7a099094a"
TRAINING_COMMIT_BEFORE_RESCALING = "28f64360e674c518f5ac6f49c7abaaa507aba7ef"  # where s-eab2ace8 was trained (its W&B run record)
SWITCH_NAME = "label_network_inputs_without_rescaling"
_INSTANCE_MARK = "_vpd_audit_label_switch"  # set on the patched label-network instance
_MODEL_MARK = "_vpd_audit_label_switch_run"  # set on the ComponentModel whose label network was patched

DEVIATION_TEXT = (
    "Deviation from the pinned code: the label network's forward on this one model instance omits the F.rms_norm that "
    "param_decomp/models/components.py (GlobalSharedTransformerCiFn.forward, commit 74146b5) applies to each input of the "
    "decomposed matrices before the input projector, as the authors' code did at commit 28f6436, where this decomposition "
    "was trained. Only that instance's forward is replaced; the class, the weights, the blocks, the sigmoids and the output "
    "split are unchanged, and no pinned file is edited."
)


def _forward_without_input_rescaling(self: Any, input_acts: dict[str, Tensor]) -> dict[str, Tensor]:
    """The pinned `GlobalSharedTransformerCiFn.forward` (74146b5) with `F.rms_norm(input_acts[name], ...)` replaced by
    `input_acts[name]`, which is the first line of the same forward at 28f6436. Every other line is the pinned line
    unchanged."""
    inputs_list = [input_acts[name] for name in self.layer_order]
    concatenated = torch.cat(inputs_list, dim=-1)
    projected: Tensor = self._input_projector(concatenated)

    added_seq_dim = False
    if projected.ndim < 3:
        projected = projected.unsqueeze(-2)
        added_seq_dim = True

    x = projected
    for block in self._blocks:
        x = block(x)

    output = self._output_head(x)

    if added_seq_dim:
        output = output.squeeze(-2)

    split_outputs = torch.split(output, self.split_sizes, dim=-1)
    outputs = {name: split_outputs[i] for i, name in enumerate(self.layer_order)}

    return outputs


def label_function(model: Any) -> Any:
    """The global label network inside a loaded `ComponentModel` (`model.ci_fn._global_ci_fn`)."""
    from param_decomp.models.components import GlobalCiFnWrapper

    wrapper = getattr(model, "ci_fn", None)
    if not isinstance(wrapper, GlobalCiFnWrapper):
        raise TypeError(f"the model's label-network wrapper is {type(wrapper).__name__}, not GlobalCiFnWrapper")
    return wrapper._global_ci_fn


def patch_label_function_instance(ci_fn: Any) -> None:
    """Replace `forward` on this one instance. Refuses any type other than exactly `GlobalSharedTransformerCiFn`, and an
    instance that is already patched or already carries an instance-level `forward`."""
    from param_decomp.models.components import GlobalSharedTransformerCiFn

    if type(ci_fn) is not GlobalSharedTransformerCiFn:
        raise TypeError(f"the label fix applies only to GlobalSharedTransformerCiFn, got {type(ci_fn).__module__}.{type(ci_fn).__qualname__}")
    if getattr(ci_fn, _INSTANCE_MARK, False):
        raise RuntimeError("the label fix is already applied to this instance")
    if "forward" in vars(ci_fn):
        raise RuntimeError("this label-network instance already has an instance-level forward; refusing to replace it")
    # the class's forward must still be the pinned one (with the rescaling), or the fix would be stale
    assert "rms_norm" in GlobalSharedTransformerCiFn.forward.__code__.co_names, "the pinned forward no longer calls rms_norm"
    ci_fn.forward = types.MethodType(_forward_without_input_rescaling, ci_fn)
    object.__setattr__(ci_fn, _INSTANCE_MARK, True)


def apply_label_switch(model: Any, run: str) -> dict[str, Any]:
    """Make `model`'s label network compute what the authors' code computed when the run was trained. Patches the one
    instance inside `model`, never the class. Raises for a run whose `trained_before_ci_input_rescaling` is not set.
    Returns the record of the fix."""
    from vpd_audit.artifacts import AUDIT_RUNS

    spec = AUDIT_RUNS[run]
    if not spec.trained_before_ci_input_rescaling:
        raise ValueError(f"run {run!r} ({spec.decomp_run}) was not trained before the label network rescaled its inputs; it needs no fix")
    if getattr(model, _MODEL_MARK, None) is not None:
        raise RuntimeError(f"the label fix is already applied to this model (run {getattr(model, _MODEL_MARK)})")
    patch_label_function_instance(label_function(model))
    object.__setattr__(model, _MODEL_MARK, run)
    return switch_record(model)


def is_switched(model: Any) -> bool:
    """True if `model`'s label network carries the fix (both marks set and the instance forward in place)."""
    if getattr(model, _MODEL_MARK, None) is None:
        return False
    ci_fn = label_function(model)
    fwd = vars(ci_fn).get("forward")
    return bool(getattr(ci_fn, _INSTANCE_MARK, False)) and fwd is not None and getattr(fwd, "__func__", None) is _forward_without_input_rescaling


def switch_record(model: Any) -> dict[str, Any]:
    """Whether the fix was applied to `model`, and the deviation it makes from the pinned code."""
    if not is_switched(model):
        return {"switch_applied": False, "name": SWITCH_NAME}
    from vpd_audit.artifacts import AUDIT_RUNS

    run = getattr(model, _MODEL_MARK)
    return {"switch_applied": True, "name": SWITCH_NAME, "run": run, "decomp_run": AUDIT_RUNS[run].decomp_run, "pinned_commit": PINNED_COMMIT,
            "training_commit": TRAINING_COMMIT_BEFORE_RESCALING, "deviation": DEVIATION_TEXT}
