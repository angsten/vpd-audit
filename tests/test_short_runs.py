"""The residual short runs' summary arithmetic and shrink rule on synthetic tables: s_b, Q, Delta, the tripwire, the guard, the
labels, and the pre-registered shrink order. Six sequences, two draws, two modules (pairwise-distinct sizes)."""

import json

import numpy as np
import pandas as pd
import pytest

from vpd_audit.results import rows_to_frame
from vpd_audit.short_runs import (
    FULL_PASSES,
    PassSpec,
    apply_shrink_rule,
    decide_final_specs,
    label_run_ii,
    label_run_iii,
    project_seconds,
    residual_summary,
    summarize_residual_pass,
)

N, DRAWS = 6, 2
X, Y = 0.004, 0.003  # Cu = C0 - X ; C1 = C0 + Y


def _frame(precision: str = "fp32") -> pd.DataFrame:
    rows = []

    def add(cond, draw, seq, kl, ce, delta):
        cell = f"{cond}/k{draw}" if cond.startswith("stochastic") else cond
        rows.append({"cell": cell, "condition": cond, "draw": draw, "seq": seq, "kl_mean": kl, "kl_max": kl * 3, "kl_argmax": 7, "ce": ce,
                     "ce_target": 2.7 + 0.01 * seq, "mask_hash": "", "mask_fp": "", "delta": delta, "precision": precision, "min_gap": 0.0, "n_below_label": 0})

    for b in range(N):
        add("target", 0, b, 0.0, 2.7 + 0.01 * b, "none")
        add("unmasked", 0, b, 0.0115 + 0.001 * (b - 2.5), 2.71 + 0.01 * b, "excluded")
        add("unmasked_delta", 0, b, 0.0005, 2.7002 + 0.01 * b, "included")
        kl_imp = 0.30 + 0.01 * b
        add("importances", 0, b, kl_imp, 3.0 + 0.01 * b, "excluded")
        s_b = -0.02 + 0.001 * (b - 2.5) if b < N - 1 else 0.0  # the last sequence: identical, for the tripwire
        add("importances_delta1", 0, b, kl_imp - s_b, 3.0 + 0.01 * b - s_b, "included")
        for k in range(DRAWS):
            c0 = 0.20 + 0.01 * b + 0.001 * k
            add("stochastic", k, b, c0, 2.85 + 0.01 * b + 0.001 * k, "excluded")
            add("stochastic_delta", k, b, c0 - X, 2.85 + 0.01 * b + 0.001 * k - X, "included")
            add("stochastic_delta1", k, b, c0 + Y, 2.85 + 0.01 * b + 0.001 * k + Y, "included")
    return rows_to_frame(rows)


def _manifest(precision="fp32"):
    return {"precision": precision, "n_draws": DRAWS, "subbatch": 3, "importance_chunk": 3, "gpu_name": "test",
            "extra": {"conditions": ["target", "unmasked", "unmasked_delta", "importances", "importances_delta1", "stochastic", "stochastic_delta", "stochastic_delta1"], "do_hash": False},
            "fingerprint": None}


def _marker(ok=True):
    d = {"components_equal_stochastic_vs_stochastic_delta": 2, "components_equal_stochastic_vs_stochastic_delta1": 2 if ok else 1, "n_modules": 2,
         "residual_masks_differ_stochastic_delta_vs_delta1": True, "residual_delta1_all_ones": True}
    hook = {"guard": "shared_mask", "passed": True, "n_comparisons": 8, "draws": {"k0": d, "k1": d}}
    return {"done_through": 1, "extra": {"subbatch_hooks": {"0": hook, "1": hook}}}


def test_summary_arithmetic_fp32():
    df = _frame()
    out = summarize_residual_pass(df, _manifest(), _marker())
    # ||delta||^2 in fp32 is the unmasked mean
    assert out["delta_sq"]["value"] == pytest.approx(0.0115, abs=1e-9)
    # run (ii): s_b = KL(importances) - KL(importances_delta1)
    s_expected = np.array([-0.02 + 0.001 * (b - 2.5) for b in range(N - 1)] + [0.0])
    r2 = out["run_ii"]["kl_mean"]
    assert r2["mean"] == pytest.approx(s_expected.mean(), abs=1e-7)
    assert r2["se"] == pytest.approx(s_expected.std(ddof=1) / np.sqrt(N), abs=1e-7)
    assert r2["fraction_positive"] == pytest.approx(0.0)
    assert len(r2["batch_means_128"]) == 1 and r2["batch_means_128"][0] == pytest.approx(s_expected.mean(), abs=1e-7)
    # run (iii): Q = C0 + C1 - 2 Cu = Y + 2 X exactly, Delta = C1 - C0 = Y, for every (draw, seq)
    r3 = out["run_iii"]["kl_mean"]
    assert r3["Q"]["mean"] == pytest.approx(Y + 2 * X, abs=1e-6) and r3["Q"]["se"] == pytest.approx(0.0, abs=1e-6)
    assert r3["Delta"]["mean"] == pytest.approx(Y, abs=1e-6)
    assert out["run_iii"]["Q_over_delta_sq"] == pytest.approx((Y + 2 * X) / 0.0115, rel=1e-4)
    assert out["run_iii"]["Delta_over_delta_sq"] == pytest.approx(Y / 0.0115, rel=1e-4)
    assert r3["draws"] == [0, 1]
    # tripwire: five of six sequences differ for importances_delta1; every (draw, seq) pair for stochastic_delta1
    t = out["tripwire"]
    assert t["importances_delta1_vs_importances"]["fraction_over_tol"] == pytest.approx(5 / 6)
    assert t["stochastic_delta1_vs_stochastic"]["fraction_over_tol"] == pytest.approx(1.0) and t["stochastic_delta1_vs_stochastic"]["n_pairs"] == N * DRAWS
    assert t["both_cells_over_min_fraction"] is False  # 5/6 < 0.9
    assert out["shared_mask_guard"]["holds_on_every_subbatch"] is True and out["shared_mask_guard"]["n_comparisons_total"] == 16
    assert summarize_residual_pass(df, _manifest(), _marker(ok=False))["shared_mask_guard"]["holds_on_every_subbatch"] is False
    # the ce version of s_b has the same values here by construction
    assert out["run_ii"]["ce"]["mean"] == pytest.approx(r2["mean"], abs=1e-6)


def test_delta_sq_in_bf16_subtracts_the_rounding_floor():
    out = summarize_residual_pass(_frame("bf16"), _manifest("bf16"), _marker())
    assert out["delta_sq"]["value"] == pytest.approx(0.0115 - 0.0005, abs=1e-9)


def test_labels_follow_the_registered_rules():
    # run (ii): sign first with the 2 SE interval clear of zero, then the band
    assert label_run_ii(-0.020, 0.002) == "cancellation"
    assert label_run_ii(-0.020, 0.010) == "indeterminate"  # straddles zero
    assert label_run_ii(-0.006, 0.001) == "indeterminate"  # interval [-0.008, -0.004] straddles the band edge -0.005
    assert label_run_ii(-0.003, 0.0001) == "indeterminate"  # |mean| <= 0.005
    assert label_run_ii(+0.011, 0.001) == "orthogonal"
    assert label_run_ii(+0.042, 0.002) == "shortfall"
    assert label_run_ii(+0.025, 0.001) == "outside every band"
    assert label_run_ii(-0.050, 0.001) == "outside every band"
    # run (iii): Q-bar as a fraction of ||delta||^2
    assert label_run_iii(0.40) == "consistent" and label_run_iii(0.25) == "consistent" and label_run_iii(0.60) == "consistent"
    assert label_run_iii(0.15) == "marginal" and label_run_iii(0.70) == "marginal"
    assert label_run_iii(0.05) == "near zero" and label_run_iii(-0.05) == "near zero"
    assert label_run_iii(0.9) == "inconsistent" and label_run_iii(-0.3) == "inconsistent"


def test_shrink_rule_order_and_projection():
    probe = {p.name: p for p in FULL_PASSES}
    assert probe["residual_fp32"].n_cells == 17 and probe["residual_bf16"].n_cells == 11
    assert probe["residual_fp32"].n_subbatches == 8 and probe["residual_bf16"].n_subbatches == 16
    t = {"residual_fp32": 8.0, "residual_bf16": 2.2}
    assert project_seconds(probe, probe, t, 80.0) == pytest.approx(8 * 8 + 16 * 2.2 + 80)
    # under budget: nothing changes
    final, steps = apply_shrink_rule(probe, probe, t, 80.0, 180.0)
    assert steps == [] and {k: (v.n, v.n_draws) for k, v in final.items()} == {"residual_fp32": (256, 4), "residual_bf16": (512, 2)}
    # over by a little: the float32 pass shrinks first, and only it
    final, steps = apply_shrink_rule(probe, probe, t, 100.0, 180.0)
    assert [(s["pass"], s["field"], s["value"]) for s in steps] == [("residual_fp32", "n", 128)]
    assert final["residual_fp32"].n == 128 and final["residual_fp32"].n_draws == 4 and final["residual_bf16"].n == 512
    # over by more: then bf16 to 256, then bf16 draws to 1
    t2 = {"residual_fp32": 14.0, "residual_bf16": 5.0}
    final, steps = apply_shrink_rule(probe, probe, t2, 100.0, 180.0)
    assert [(s["pass"], s["field"], s["value"]) for s in steps] == [("residual_fp32", "n", 128), ("residual_bf16", "n", 256), ("residual_bf16", "n_draws", 1)]
    assert final["residual_bf16"].n_draws == 1 and final["residual_bf16"].n_cells == 8
    # the projection with draws shrunk scales the bf16 first-sub-batch time by 8/11 cells
    assert project_seconds(final, probe, t2, 100.0) == pytest.approx(4 * 14.0 + 8 * 5.0 * 8 / 11 + 100.0)
    # never dropped: four fp32 draws, and the probes are not mutated
    assert final["residual_fp32"].n_draws == 4 and probe["residual_fp32"].n == 256 and probe["residual_bf16"].n_draws == 2


def test_residual_summary_end_to_end(tmp_path):
    for name, precision in (("residual_fp32", "fp32"), ("residual_bf16", "bf16")):
        d = tmp_path / name
        d.mkdir()
        _frame(precision).to_parquet(d / "per_sequence.parquet", index=False)
        (d / "run_manifest.json").write_text(json.dumps(_manifest(precision)))
        (d / "marker.json").write_text(json.dumps(_marker()))
    summary, text = residual_summary(tmp_path, acceptance_dir=None)
    assert set(summary["passes"]) == {"residual_fp32", "residual_bf16"}
    assert summary["gate"]["passed"] is False  # the tripwire's 5/6 on importances_delta1
    assert "Run (ii) label" in text and "Run (iii) label" in text and summary["labels"]["residual_fp32"]["run_iii"] == label_run_iii((Y + 2 * X) / 0.0115)


def test_override_records_the_verdict_and_keeps_full_sizes():
    probe = {p.name: p for p in FULL_PASSES}
    t = {"residual_fp32": 8.0, "residual_bf16": 2.2}
    # check 6 at 226.4 s: the rule would shrink to the floor and still miss the budget
    final, rec = decide_final_specs(probe, t, 226.4, 180.0, None)
    assert rec["shrink_rule"]["verdict"] == "shrink" and len(rec["shrink_rule"]["steps"]) == 3 and rec["shrink_rule"]["budget_met_if_applied"] is False
    assert final["residual_fp32"].n == 128 and final["residual_bf16"].n_draws == 1 and rec["shrink_override"]["applied"] is False
    # an override: same verdict recorded, full sizes kept, reason recorded
    final, rec = decide_final_specs(probe, t, 226.4, 180.0, "the rule's premise failed")
    assert rec["shrink_rule"]["verdict"] == "shrink" and len(rec["shrink_rule"]["steps"]) == 3
    assert rec["shrink_override"] == {"applied": True, "reason": "the rule's premise failed", "kept": {k: {"name": v.name, "precision": v.precision, "n": v.n, "n_draws": v.n_draws} for k, v in probe.items()}}
    assert {k: (v.n, v.n_draws) for k, v in final.items()} == {"residual_fp32": (256, 4), "residual_bf16": (512, 2)} and rec["shrink_steps_applied"] == []
    assert rec["projection_final_s"] == pytest.approx(8 * 8 + 16 * 2.2 + 226.4)
    # under budget, an override reason changes nothing and is recorded as not applied
    final, rec = decide_final_specs(probe, t, 80.0, 180.0, "unused")
    assert rec["shrink_rule"]["verdict"] == "no shrink" and rec["shrink_override"]["applied"] is False and final["residual_fp32"].n == 256
