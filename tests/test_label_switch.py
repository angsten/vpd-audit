"""The label fix for decompositions trained before the label network rescaled its inputs (`vpd_audit/label_switch.py`), on a
small randomly initialised label network, with no model files; and the loader, which applies it to the small-model mode only."""

from __future__ import annotations

from vpd_audit import env  # noqa: F401  (first: sets PARAM_DECOMP_OUT_DIR and HF_HOME)

import dataclasses
from types import SimpleNamespace

import pytest
import torch
import torch.nn.functional as F
from torch import nn

from vpd_audit.artifacts import AUDIT_RUNS
from vpd_audit.label_switch import (_forward_without_input_rescaling, apply_label_switch, is_switched, label_function, patch_label_function_instance,
                                    switch_record)


class TinyTarget(nn.Module):
    """Two linear maps on (B, T, 6) inputs; the decomposed modules are `a` and `b`."""

    def __init__(self) -> None:
        super().__init__()
        self.a = nn.Linear(6, 8, bias=False)
        self.b = nn.Linear(8, 6, bias=False)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.b(torch.relu(self.a(x)))


def tiny_model(seed: int = 0, fn_type: str = "global_shared_transformer"):
    from param_decomp.configs import AttnConfig, GlobalCiConfig, GlobalSharedTransformerCiConfig, LayerwiseCiConfig
    from param_decomp.models.batch_and_loss_fns import make_run_batch
    from param_decomp.models.component_model import ComponentModel
    from param_decomp.utils.module_utils import ModulePathInfo

    torch.manual_seed(seed)
    target = TinyTarget()
    target.requires_grad_(False)
    if fn_type == "global_shared_transformer":
        ci = GlobalCiConfig(fn_type="global_shared_transformer",
                            simple_transformer_ci_cfg=GlobalSharedTransformerCiConfig(d_model=8, n_blocks=2, mlp_hidden_dim=[16], attn_config=AttnConfig(n_heads=2, max_len=32)))
    elif fn_type == "global_shared_mlp":
        ci = GlobalCiConfig(fn_type="global_shared_mlp", hidden_dims=[16])
    else:
        ci = LayerwiseCiConfig(fn_type="vector_mlp", hidden_dims=[16])
    model = ComponentModel(target_model=target, run_batch=make_run_batch(None), module_path_info=[ModulePathInfo("a", 5), ModulePathInfo("b", 4)],
                           ci_config=ci, sigmoid_type="leaky_hard")
    return model.eval()


def _inputs(seed: int = 1) -> dict[str, torch.Tensor]:
    """Inputs of the two decomposed modules, far from unit RMS so that the rescaling matters."""
    g = torch.Generator().manual_seed(seed)
    return {"a": 3.0 * torch.randn(2, 7, 6, generator=g) + 0.5, "b": 0.2 * torch.randn(2, 7, 8, generator=g)}


def _reference_without_rescaling(ci_fn, acts: dict[str, torch.Tensor]) -> dict[str, torch.Tensor]:
    """Written out here, independently of the fix: the forward on the raw inputs."""
    x = ci_fn._input_projector(torch.cat([acts[n] for n in ci_fn.layer_order], dim=-1))
    for block in ci_fn._blocks:
        x = block(x)
    out = ci_fn._output_head(x)
    return dict(zip(ci_fn.layer_order, torch.split(out, ci_fn.split_sizes, dim=-1)))


def _reference_with_rescaling(ci_fn, acts: dict[str, torch.Tensor]) -> dict[str, torch.Tensor]:
    return _reference_without_rescaling(ci_fn, {k: F.rms_norm(v, (v.shape[-1],)) for k, v in acts.items()})


def test_only_the_small_model_mode_is_flagged():
    assert AUDIT_RUNS["simplestories"].trained_before_ci_input_rescaling is True
    assert AUDIT_RUNS["main"].trained_before_ci_input_rescaling is False
    assert AUDIT_RUNS["control"].trained_before_ci_input_rescaling is False
    assert {r for r, s in AUDIT_RUNS.items() if s.trained_before_ci_input_rescaling} == {"simplestories"}


def test_the_fixed_forward_equals_the_forward_without_rescaling():
    model = tiny_model()
    ci = label_function(model)
    acts = _inputs()
    with torch.no_grad():
        before = ci(acts)
        apply_label_switch(model, "simplestories")
        after = ci(acts)
        ref = _reference_without_rescaling(ci, acts)
        ref_rescaled = _reference_with_rescaling(ci, acts)
    for k in acts:
        assert torch.equal(after[k], ref[k]), k
        assert torch.equal(before[k], ref_rescaled[k]), k  # the pinned forward rescales
        assert not torch.allclose(after[k], before[k]), k


def test_labels_through_the_model_follow_the_fix():
    model = tiny_model()
    ci = label_function(model)
    acts = _inputs(2)
    with torch.no_grad():
        apply_label_switch(model, "simplestories")
        out = model.calc_causal_importances(acts, sampling="continuous")
        ref = _reference_without_rescaling(ci, acts)
    for k in acts:
        assert torch.equal(out.pre_sigmoid[k], ref[k])
        assert torch.equal(out.lower_leaky[k], ref[k].clamp(0, 1))


def test_the_fix_leaves_every_parameter_unchanged():
    model = tiny_model()
    before = {k: v.clone() for k, v in model.state_dict().items()}
    ids = {k: id(p) for k, p in model.named_parameters()}
    apply_label_switch(model, "simplestories")
    after = model.state_dict()
    assert set(before) == set(after) and all(torch.equal(before[k], after[k]) for k in before)
    assert ids == {k: id(p) for k, p in model.named_parameters()}


def test_the_fix_patches_the_instance_not_the_class():
    from param_decomp.models.components import GlobalSharedTransformerCiFn

    class_forward = GlobalSharedTransformerCiFn.forward
    m1, m2 = tiny_model(0), tiny_model(0)
    acts = _inputs(3)
    apply_label_switch(m1, "simplestories")
    assert GlobalSharedTransformerCiFn.forward is class_forward
    ci2 = label_function(m2)
    assert "forward" not in vars(ci2) and not is_switched(m2)
    with torch.no_grad():
        out1, out2 = label_function(m1)(acts), ci2(acts)
        ref2 = _reference_with_rescaling(ci2, acts)
        out3 = label_function(tiny_model(0))(acts)  # a model built after the patch
    for k in acts:
        assert torch.equal(out2[k], ref2[k]) and torch.equal(out3[k], out2[k])
        assert not torch.allclose(out1[k], out2[k])


def test_the_fix_refuses_the_67m_runs_and_other_label_networks():
    for run in ("main", "control"):
        with pytest.raises(ValueError):
            apply_label_switch(tiny_model(), run)
    with pytest.raises(TypeError):
        apply_label_switch(tiny_model(0, "global_shared_mlp"), "simplestories")
    with pytest.raises(TypeError):
        apply_label_switch(tiny_model(0, "layerwise"), "simplestories")
    with pytest.raises(TypeError):
        patch_label_function_instance(torch.nn.Linear(2, 2))


def test_the_fix_refuses_a_second_application_and_records_itself():
    model = tiny_model()
    assert switch_record(model)["switch_applied"] is False
    rec = apply_label_switch(model, "simplestories")
    assert rec["switch_applied"] is True and rec["decomp_run"] == "s-eab2ace8" and "rms_norm" in rec["deviation"]
    assert vars(label_function(model))["forward"].__func__ is _forward_without_input_rescaling
    with pytest.raises(RuntimeError):
        apply_label_switch(model, "simplestories")


def test_the_loader_fixes_and_checks_the_small_model_mode_only(tmp_path, monkeypatch):
    """`load_component_model` with the authors' loaders replaced by a tiny model: the small-model mode comes back fixed and
    checked against its logged scores; the main and control runs come back unpatched and unchecked."""
    import param_decomp.models.component_model as cm

    from vpd_audit import artifacts, logged_scores

    ckpt = tmp_path / "decomp" / "model_400000.pth"
    ckpt.parent.mkdir()
    ckpt.write_bytes(b"")
    (ckpt.parent / "final_config.yaml").write_text("")
    tgt = tmp_path / "target" / "ckpt" / "model_step_1.pt"
    tgt.parent.mkdir(parents=True)
    tgt.write_bytes(b"")
    for f in ("final_config.yaml", "model_config.yaml"):
        (tgt.parent.parent / f).write_text("")
    monkeypatch.setattr(artifacts, "decomp_checkpoint_path", lambda run, art_dir=None: ckpt)
    monkeypatch.setattr(artifacts, "target_checkpoint_path", lambda run, art_dir=None: tgt)
    def fake_info(p):
        return SimpleNamespace(config=SimpleNamespace(model_copy=lambda update: SimpleNamespace()))

    monkeypatch.setattr(cm.ParamDecompRunInfo, "from_path", staticmethod(fake_info))
    monkeypatch.setattr(cm.ComponentModel, "from_run_info", classmethod(lambda cls, info: tiny_model(0)))
    # the 67M specs' shape assertions are for the real models; keep every other field, the flag included
    for r in ("main", "control"):
        monkeypatch.setitem(artifacts.AUDIT_RUNS, r, dataclasses.replace(artifacts.AUDIT_RUNS[r], n_matrices=None, n_subcomponents=None))
    checked: list[str] = []
    monkeypatch.setattr(logged_scores, "require_logged_scores", lambda model, run, **kw: checked.append(run))
    for r in ("main", "control"):
        m = artifacts.load_component_model(r, "cpu", verify=False)
        assert not is_switched(m) and "forward" not in vars(label_function(m))
    assert checked == []
    m = artifacts.load_component_model("simplestories", "cpu", verify=False)
    assert is_switched(m) and checked == ["simplestories"]
    m = artifacts.load_component_model("simplestories", "cpu", verify=False, check_logged_scores=False)
    assert is_switched(m) and checked == ["simplestories"]
