"""The residual follow-up (with its pre-registered readings): the cell list, the component
and residual mask builders, and the summary's algebra and labels on a Euclidean fixture where delta = sum_l delta_l
exactly and the footprints follow from the same vectors. Synthetic modules named like the model's, two layers, three
types, pairwise-distinct sizes B = 2, T = 5, C in {7, 3, 11, 13, 4, 6}."""

import json

import numpy as np
import pytest
import torch

from vpd_audit.residual_matrix import (
    COMPONENT_KINDS,
    Cell,
    Footprint,
    component_masks,
    default_cells,
    label_reading_1,
    label_reading_3,
    residual_masks,
    residual_matrix_summary,
)
from vpd_audit.results import rows_to_frame

B, T = 2, 5
MODULE_TO_C = {"h.0.attn.q_proj": 7, "h.0.attn.o_proj": 3, "h.0.mlp.down_proj": 11, "h.1.attn.q_proj": 13, "h.1.attn.o_proj": 4, "h.1.mlp.down_proj": 6}
KEYS = sorted(MODULE_TO_C)


def _g():
    gen = torch.Generator().manual_seed(0)
    g = {k: torch.rand((B, T, c), generator=gen) for k, c in MODULE_TO_C.items()}
    for k in g:
        g[k][g[k] < 0.3] = 0.0
    return g


def test_default_cells_structure():
    cells, fps = default_cells(KEYS)
    n = len(KEYS)
    assert len(cells) == (2 + 2 * n) + 1 + 2 * len(COMPONENT_KINDS) + (1 + n) + 2 * 2  # A, E, B, C, D (two layers)
    assert len(fps) == len(COMPONENT_KINDS) + n + 2
    names = [c.name for c in cells]
    by = {c.name: c for c in cells}
    assert by["A/all"].residual_on == frozenset(KEYS) and by["A/none"].residual_on == frozenset() and by["A/all"].components == "ones"
    assert by[f"A/all_but/{KEYS[0]}"].residual_on == frozenset(KEYS[1:]) and by[f"A/only/{KEYS[0]}"].residual_on == frozenset([KEYS[0]])
    assert by["E/half"].residual_value == 0.5 and by["E/half"].residual_on == frozenset(KEYS) and by["E/half"].components == "ones"
    assert by["B/zero_all/on"].permitted is False and by["B/rounded_0.1/off"].permitted is False and by["B/importances/on"].permitted is True
    assert by["C/off"].components == "importances" and by["C/off"].residual_on == frozenset() and by[f"C/only/{KEYS[3]}/on"].residual_on == frozenset([KEYS[3]])
    assert by["D/L1/on"].components == "hybrid/L1" and by["D/L0/off"].residual_on == frozenset()
    # every footprint's partners exist, share their component kind, and the off partner comes first
    for f in fps:
        assert by[f.on].components == by[f.off].components and names.index(f.off) < names.index(f.on)
        assert by[f.on].residual_on and not by[f.off].residual_on
    assert {f.name for f in fps} >= {"B/ones/footprint", "B/zero_all/footprint", f"C/only/{KEYS[0]}/footprint", "D/L0/footprint", "D/L1/footprint"}
    # cells sharing component masks are adjacent (one rebuild per kind per sub-batch)
    kinds = [c.components for c in cells]
    assert len([i for i in range(1, len(kinds)) if kinds[i] != kinds[i - 1]]) == len(set(kinds)) - 1


def test_component_and_residual_masks():
    g = _g()
    ones = component_masks("ones", g, MODULE_TO_C, subbatch_index=0, master_seed=0)
    assert all(torch.equal(ones[k], torch.ones_like(g[k])) for k in KEYS)
    imp = component_masks("importances", g, MODULE_TO_C, subbatch_index=0, master_seed=0)
    assert all(imp[k] is g[k] or torch.equal(imp[k], g[k]) for k in KEYS)
    zero = component_masks("zero_all", g, MODULE_TO_C, subbatch_index=0, master_seed=0)
    assert all(torch.equal(zero[k], torch.zeros_like(g[k])) for k in KEYS)
    rnd = component_masks("rounded_0.1", g, MODULE_TO_C, subbatch_index=0, master_seed=0)
    assert all(torch.equal(rnd[k], (g[k] > 0.1).float()) for k in KEYS)
    st = component_masks("stochastic/k0", g, MODULE_TO_C, subbatch_index=3, master_seed=0)
    from vpd_audit.reference import CONDITION_BY_NAME, build_condition_masks

    ref, _ = build_condition_masks(CONDITION_BY_NAME["stochastic"], g, MODULE_TO_C, draw=0, subbatch_index=3, master_seed=0)
    assert all(torch.equal(st[k], ref[k]) for k in KEYS)
    hyb = component_masks("hybrid/L1", g, MODULE_TO_C, subbatch_index=0, master_seed=0)
    for k in KEYS:
        assert torch.equal(hyb[k], g[k] if k.startswith("h.1.") else torch.ones_like(g[k]))
    with pytest.raises(AssertionError):
        component_masks("hybrid/L7", g, MODULE_TO_C, subbatch_index=0, master_seed=0)
    d = residual_masks(g, frozenset([KEYS[1]]), 1.0)
    assert torch.equal(d[KEYS[1]], torch.ones(B, T)) and all(torch.equal(d[k], torch.zeros(B, T)) for k in KEYS if k != KEYS[1])
    h = residual_masks(g, frozenset(KEYS), 0.5)
    assert all(torch.equal(h[k], torch.full((B, T), 0.5)) for k in KEYS) and h[KEYS[0]].dtype == torch.float32


def test_labels():
    assert label_reading_1(0.7).startswith("additive")
    assert label_reading_1(0.03).startswith("gating")
    assert label_reading_1(0.3).startswith("partial")
    ratios_h2 = {k: (0.9 if k == "h.1.mlp.down_proj" else 0.05) for k in KEYS}
    assert label_reading_3(ratios_h2, [], KEYS).startswith("H2")
    ratios_h3 = {k: (0.8 if k in ("h.0.attn.q_proj",) else 0.05) for k in KEYS}  # layer 0's inputs near 1, layer 1's down_proj small
    assert label_reading_3(ratios_h3, [], KEYS).startswith("H3")
    assert label_reading_3({k: 0.4 for k in KEYS}, [], KEYS).startswith("mixed")


def test_summary_on_a_euclidean_fixture(tmp_path):
    """Target output 0. Residual vectors r_l. Component-mask error a_m per kind (0 for ones). A cell's error is
    a_m + sum over the residuals that are OFF of r_l (scaled by 1 - value); its KL vs target is ||error||^2; a
    footprint is ||error_on - error_off||^2 = ||sum over the residuals that differ||^2 (here independent of a_m)."""
    rng = np.random.default_rng(2)
    r = {k: rng.normal(size=4) for k in KEYS}
    a = {"ones": np.zeros(4), "importances": rng.normal(size=4) * 3, "stochastic/k0": rng.normal(size=4) * 2, "rounded_0.1": rng.normal(size=4) * 3, "zero_all": rng.normal(size=4) * 9,
         "hybrid/L0": rng.normal(size=4), "hybrid/L1": rng.normal(size=4)}
    cells, fps = default_cells(KEYS)

    def err(c: Cell) -> np.ndarray:
        return a[c.components] + sum((1.0 - (c.residual_value if k in c.residual_on else 0.0)) * r[k] for k in KEYS)

    by = {c.name: c for c in cells}
    n_seq = 4
    rows = []
    fp_cells = {}
    for c in cells:
        cost = float(np.sum(err(c) ** 2))
        fp_cells[c.name] = cost
        for b in range(n_seq):
            rows.append({"cell": c.name, "condition": c.components, "draw": 0, "seq": b, "kl_mean": cost, "kl_max": cost, "kl_argmax": 0, "ce": 1.0, "ce_target": 1.0,
                         "mask_fp": "", "delta": "included", "precision": "fp32", "min_gap": 0.0, "n_below_label": 0})
    for f in fps:
        cost = float(np.sum((err(by[f.on]) - err(by[f.off])) ** 2))
        for b in range(n_seq):
            rows.append({"cell": f.name, "condition": "footprint", "draw": 0, "seq": b, "kl_mean": cost, "kl_max": cost, "kl_argmax": 0, "ce": float("nan"), "ce_target": 1.0,
                         "mask_fp": "", "delta": "on_vs_off", "precision": "fp32", "min_gap": float("nan"), "n_below_label": 0})
    d = tmp_path / "rm"
    d.mkdir()
    rows_to_frame(rows).to_parquet(d / "per_sequence.parquet", index=False)
    (d / "run_manifest.json").write_text(json.dumps({"precision": "fp32", "subbatch": 2, "importance_chunk": 2, "gpu_name": "test",
                                                     "extra": {"cell_specs": {c.name: {"components": c.components, "residual_on": sorted(c.residual_on), "residual_value": c.residual_value, "permitted": c.permitted} for c in cells},
                                                               "footprints": {f.name: {"on": f.on, "off": f.off} for f in fps}}}))
    specs_seen: dict[tuple, int] = {}
    digest = {}
    for c in cells:  # the same masks under two names get the same digest, as the fingerprint would give
        key = (c.components, tuple(sorted(c.residual_on)), c.residual_value)
        digest[c.name] = f"{specs_seen.setdefault(key, len(specs_seen)):016x}"
    (d / "marker.json").write_text(json.dumps({"extra": {"mask_fp_cell": digest,
                                                          "mask_fp_modules_cell": {c.name: {"H": {k: "0" * 16 for k in KEYS}, "Hd": None} for c in cells},
                                                          "footprint_logit_diffs": {f.name: {"0": {"max": 0.5, "mean": 0.1}, "1": {"max": 0.7, "mean": 0.3}} for f in fps}}}))
    S, text = residual_matrix_summary(d, None)
    assert S["digests"]["equal_within_each_spec"] and S["digests"]["distinct_across_specs"] and S["digests"]["n_distinct_mask_specs"] == len(cells) - 3
    assert set(S["digests"]["duplicate_specs"]) == {"A/all = B/ones/on", "A/none = B/ones/off", "B/importances/off = C/off"}
    delta = sum(r.values())
    delta_sq = float(np.sum(delta ** 2))
    D = float(sum(np.sum(v ** 2) for v in r.values()))
    A = S["set_A"]
    assert A["delta_sq"]["mean"] == pytest.approx(delta_sq, rel=1e-6) and A["all_residuals_on"]["mean"] == 0.0
    assert A["D"]["sum_of_means"] == pytest.approx(D, rel=1e-6) and A["loophole_D_over_3_delta_sq"] == (D > 3 * delta_sq)
    for k in KEYS:
        assert A["per_module"][k]["cross_delta_delta_l"] == pytest.approx(float(np.dot(delta, r[k])), rel=1e-5, abs=1e-6)
    assert abs(A["cross_terms"]["consistency_relative"]) < 1e-5
    # every footprint in this fixture equals ||delta||^2 (all residuals differ between on and off), so every fraction is 1 and reading 1 says additive
    Bs = S["set_B"]
    assert Bs["sanity"]["passed"] and all(v == pytest.approx(1.0, rel=1e-5) for v in Bs["fraction_of_all_ones_footprint"].values())
    assert Bs["reading_1"]["label"].startswith("additive") and Bs["reading_4"]["passed"] == (delta_sq > 1e-2)
    # set C: footprint_l = ||r_l||^2 = ||delta_l||^2 exactly here, so every ratio is 1 (or excluded)
    C = S["set_C"]
    for k, v in C["per_module"].items():
        if not v["excluded"]:
            assert v["ratio"] == pytest.approx(1.0, rel=1e-5)
    assert set(C["excluded_delta_l_sq_below_1e-4"]) == {k for k in KEYS if float(np.sum(r[k] ** 2)) < 1e-4}
    # set D and E
    assert all(v["fraction_of_all_ones_footprint"] == pytest.approx(1.0, rel=1e-5) for k, v in S["set_D"].items() if k != "note")
    assert S["set_E"]["kl_vs_target"]["mean"] == pytest.approx(0.25 * delta_sq, rel=1e-6) and S["set_E"]["ratio_to_prediction"] == pytest.approx(1.0, rel=1e-5)
    assert "Reading 3" in text
    ph = S["set_C"]["post_hoc_precision_table"]
    assert ph["label"].startswith("post hoc") and set(ph["rows"]) == set(KEYS) and "post hoc" in text
    for k, v in ph["rows"].items():  # constant values across sequences: zero SE, so every module with nonzero terms is included at ratio 1
        assert v["included"] == (v["footprint_imp"] > 0 and v["delta_l_sq"] > 0)
        if v["included"]:
            assert v["ratio"] == pytest.approx(1.0, rel=1e-5)
    assert S["footprint_logit_diffs"]["B/zero_all/footprint"] == {"max": 0.7, "mean": pytest.approx(0.2)}
    assert S["set_B"]["reading_4"]["evidence"].startswith("the residual IS added")
