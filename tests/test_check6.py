"""Check 6 on stand-ins: the one out-of-memory fallback fixed in advance for the authors' class, and the epsilon and label
of the matched-shape comparison."""

import pytest
import torch

from vpd_audit.short_runs import CHECK6_IDENTICAL, CHECK6_TOL, _epsilon, label_check6, run_class_with_fallback


def test_fallback_halves_the_batch_once_and_stops_at_the_second_oom():
    calls = []

    def ok_first(B, nb):
        calls.append((B, nb))
        return {"0.0": [{"x": 1.0}] * nb}

    res, attempts, B, nb = run_class_with_fallback(ok_first, 32, 4, 128, device="cpu", log=lambda *_: None)
    assert (B, nb) == (32, 4) and calls == [(32, 4)] and [a["ok"] for a in attempts] == [True]

    calls.clear()

    def oom_once(B, nb):
        calls.append((B, nb))
        if len(calls) == 1:
            raise torch.cuda.OutOfMemoryError("CUDA out of memory. Tried to allocate 3.14 GiB")
        return {"0.0": [{"x": 1.0}] * nb}

    res, attempts, B, nb = run_class_with_fallback(oom_once, 32, 4, 128, device="cpu", log=lambda *_: None)
    assert (B, nb) == (16, 8) and calls == [(32, 4), (16, 8)]
    assert [a["ok"] for a in attempts] == [False, True] and attempts[0]["batch"] == 32 and "out of memory" in attempts[0]["error"]
    assert len(res["0.0"]) == 8

    def oom_always(B, nb):
        raise torch.cuda.OutOfMemoryError("CUDA out of memory")

    with pytest.raises(RuntimeError, match="twice"):
        run_class_with_fallback(oom_always, 32, 4, 128, device="cpu", log=lambda *_: None)

    def other_error(B, nb):
        raise ValueError("not an OOM")

    with pytest.raises(ValueError):  # only out-of-memory errors are caught
        run_class_with_fallback(other_error, 32, 4, 128, device="cpu", log=lambda *_: None)


def _row(item, value, target, gated=True):
    return {"check": 6, "item": item, "value": round(value, 5), "target": round(target, 5), "tolerance": CHECK6_TOL,
            "pass": (abs(value - target) <= CHECK6_TOL) if gated else None, "note": "", "diff": value - target}


def test_epsilon_and_label():
    rows = [_row("threshold 0.0, batch 0: unmasked kl", 0.010141, 0.010140), _row("threshold 0.0, batch 1: unmasked kl", 0.0120, 0.0120),
            _row("threshold 0.0, mean over 2 batches: unmasked kl", 0.0110705, 0.011070), _row("threshold 0.0, batch 0: zero_all ce diff (derived, not gated)", 5.0, 4.0, gated=False)]
    e = _epsilon(rows)
    assert e["n_gated"] == 3 and e["epsilon"] == pytest.approx(1e-6, rel=1e-3) and e["n_positive"] == 2 and e["n_zero"] == 1
    assert e["common_sign_every_quantity_and_batch"] is False  # one per-batch difference is exactly zero
    assert label_check6(e["epsilon"], e["common_sign_every_quantity_and_batch"]) == "pass, identical arithmetic"
    rows2 = [_row(f"threshold 0.1, batch {j}: importances kl", 0.35 + 2e-5, 0.35) for j in range(4)]
    e2 = _epsilon(rows2)
    assert e2["common_sign_every_quantity_and_batch"] is True
    # a common sign fails only above the identical-arithmetic band: a 1e-8 systematic bias must not stop the grid
    assert label_check6(e2["epsilon"], True) == "pass, identical arithmetic"
    assert label_check6(1e-8, True) == "pass, identical arithmetic"
    assert label_check6(5e-4, True) == "fail" and label_check6(5e-4, False) == "pass, localize"
    assert label_check6(CHECK6_IDENTICAL, False) == "pass, identical arithmetic"
    assert label_check6(5e-4, False) == "pass, localize"
    assert label_check6(CHECK6_TOL + 1e-9, False) == "fail"
