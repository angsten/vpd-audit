"""The small-model mode's check against the authors' logged scores (`vpd_audit/logged_scores.py`): the pass and fail logic on
planted batch values, and the stop it puts in front of every load of the small-model mode. No model files."""

from __future__ import annotations

from vpd_audit import env  # noqa: F401  (first: sets PARAM_DECOMP_OUT_DIR and HF_HOME)

import math

import numpy as np
import pytest

from vpd_audit import logged_scores as ls

LOGGED = ls.LOGGED_SCORES["simplestories"]


def _planted(shift: dict[str, float] | None = None, spread: float = 1e-3, n_b: int = 4) -> dict[str, np.ndarray]:
    """Batch values centred on the logged values (plus `shift`), with a small symmetric spread."""
    z = np.linspace(-1, 1, n_b)
    out = {}
    for q, v in LOGGED.items():
        scale = spread if q.startswith("kl") else spread * 100
        out[q] = v + (shift or {}).get(q, 0.0) + scale * z
    out["kl_unmasked"] = np.full(n_b, 0.0016) + 1e-5 * z
    return out


def test_the_logged_values_are_the_runs_final_evaluation():
    assert LOGGED == {"kl_ci_masked": 0.39056103229522704, "kl_unmasked": 0.0015728561207652091, "l0_layer_0": 15.076059341430664,
                      "l0_layer_1": 32.30177307128906, "l0_total": 47.377830505371094}
    assert set(ls.LOGGED_SCORES) == {"simplestories"}  # the 67M runs have none here
    assert ls.EVAL_BATCH == 128 and ls.LOGGED_N_BATCHES == 5


def test_the_check_passes_on_values_at_the_logged_scores():
    res = ls.compare(_planted(), LOGGED)
    assert res["passed"] and res["failed"] == []
    rows = {r["quantity"]: r for r in res["rows"]}
    r = rows["kl_ci_masked"]
    se = r["s_b"] * math.sqrt(1 / 5 + 1 / 4)
    assert r["se"] == pytest.approx(se) and r["tolerance"] == pytest.approx(min(0.025, max(3 * se, 0.005)))
    t = rows["l0_total"]
    assert t["tolerance"] == pytest.approx(min(0.10 * 47.377830505371094, max(3 * t["se"], 0.02 * 47.377830505371094)))
    assert rows["kl_unmasked"]["tolerance"] == 0.005


def test_the_check_fails_on_each_kind_of_miss():
    assert ls.compare(_planted({"kl_ci_masked": 0.03}), LOGGED)["failed"] == ["kl_ci_masked"]  # beyond the 0.025 ceiling
    assert ls.compare(_planted({"kl_ci_masked": 0.004}), LOGGED)["passed"]  # within the 0.005 floor
    assert ls.compare(_planted({"l0_total": 0.05 * 47.378}), LOGGED)["failed"] == ["l0_total"]  # 5% off with a tight spread
    assert ls.compare(_planted({"l0_layer_0": -0.015 * 15.076}), LOGGED)["passed"]  # 1.5% off: within the 2% floor
    bad = _planted()
    bad["kl_unmasked"] = np.full(4, 0.006)
    assert ls.compare(bad, LOGGED)["failed"] == ["kl_unmasked"]  # above the 0.005 bound
    coarse = _planted()
    coarse["kl_ci_masked"] = LOGGED["kl_ci_masked"] + np.array([-0.05, -0.01, 0.01, 0.05])  # 3 SE above the ceiling
    res = ls.compare(coarse, LOGGED)
    row = next(r for r in res["rows"] if r["quantity"] == "kl_ci_masked")
    assert row["too_coarse"] and not row["passed"] and res["failed"] == ["kl_ci_masked"]


def test_the_rendered_table_states_the_verdict():
    res = ls.compare(_planted({"kl_ci_masked": 0.03}), LOGGED)
    res.update({"run": "simplestories", "decomp_run": "s-eab2ace8", "split": "x/test", "n_rows": 512, "n_batches": 4, "batch": 128, "label_fix_applied": True})
    text = ls.render(res)
    assert "verdict: FAILS (kl_ci_masked)" in text and "| kl_ci_masked | 0.39056 |" in text


def test_a_failed_check_stops_the_caller_and_a_pass_is_kept_for_the_process(monkeypatch):
    monkeypatch.setattr(ls, "_PASSED_IN_PROCESS", set())
    calls: list[str] = []

    def fake_check(model, run, **kw):
        calls.append(run)
        res = ls.compare(_planted({"kl_ci_masked": 0.2}) if model == "unfixed" else _planted(), LOGGED)
        res.update({"run": run, "decomp_run": "s-eab2ace8", "split": "x/test", "n_rows": 512, "n_batches": 4, "batch": 128, "label_fix_applied": model != "unfixed"})
        return res

    monkeypatch.setattr(ls, "check_logged_scores", fake_check)
    log = lambda *a: None  # noqa: E731
    with pytest.raises(ls.LoggedScoresMismatch):
        ls.require_logged_scores("unfixed", "simplestories", log=log)
    assert ls.require_logged_scores("fixed", "simplestories", log=log)["passed"]
    assert ls.require_logged_scores("fixed", "simplestories", log=log) is None  # passed once in this process: not run again
    assert ls.require_logged_scores("anything", "main", log=log) is None and ls.require_logged_scores("anything", "control", log=log) is None
    assert calls == ["simplestories", "simplestories"]
