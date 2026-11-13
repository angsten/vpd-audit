"""The small-model mode's check against the authors' logged scores.

The small-model mode (`simplestories`, decomposition `s-eab2ace8`) once computed its labels wrongly without any check
noticing: the decomposition was trained before the authors' label network rescaled its inputs (see `label_switch.py`).
This check measures, on rows of the run's own test split, three things the authors logged at the end of training and
compares each with its logged value:

- the distance with every component at its own label: the KL divergence of the masked model's next-token distribution
  from the target model's (target first), averaged over positions (`eval/ce_kl/kl_ci_masked`);
- the distance with every component fully on (`eval/ce_kl/kl_unmasked`);
- the number of components per token whose label is above 0, in layer 0, in layer 1 and in total (`eval/l0/0.0_layer_0`,
  `eval/l0/0.0_layer_1`, `eval/l0/0.0_total`).

The labels are `lower_leaky` of the label network's continuous output from a clean forward (`importances.compute_importances`,
float32); the masked forwards use the labels, or ones, as masks with no weight deltas, as the authors' evaluation does.

**Batches and tolerance.** The authors logged the mean of 5 evaluation batches of 128 rows. The check cuts its rows into
batches of 128 in order and reads each quantity as the mean of its batch values, with s_b their standard deviation and
n_b their number:

    SE = s_b * sqrt(1/5 + 1/n_b),    tolerance = min(ceiling, max(3 SE, floor)),

and a quantity passes if |ours - logged| <= tolerance. The floors and ceilings are 0.005 and 0.025 nats for the own-label
distance, and 2% and 10% of the logged value for the three counts. The fully-on distance passes if it is at most 0.005
nats. A quantity whose 3 SE exceeds its ceiling cannot be resolved with this many rows and fails the check (run it with
more batches). The check passes if every quantity passes.

The rows are the first rows of the test split, built by `data.prepare_simplestories_rows`, whose tokenizer call appends one
end-of-text token per chunk more than the call the decomposition was trained with (see the README). The check passes
with them, which is part of what it shows.
"""

from __future__ import annotations

import math
import time
from dataclasses import asdict, dataclass
from typing import Any

import numpy as np

from vpd_audit.constants import SEQ_LEN

# The authors' logged values: run s-eab2ace8 in the public W&B project goodfire/spd, the final evaluation at step
# 400,000, keys eval/ce_kl/kl_ci_masked, eval/ce_kl/kl_unmasked, eval/l0/0.0_layer_0, eval/l0/0.0_layer_1 and
# eval/l0/0.0_total, copied unchanged (rounded: 0.39056, 0.00157, 15.076, 32.302, 47.378).
LOGGED_SCORES: dict[str, dict[str, float]] = {
    "simplestories": {
        "kl_ci_masked": 0.39056103229522704,
        "kl_unmasked": 0.0015728561207652091,
        "l0_layer_0": 15.076059341430664,
        "l0_layer_1": 32.30177307128906,
        "l0_total": 47.377830505371094,
    },
}
LOGGED_KEYS: dict[str, str] = {"kl_ci_masked": "eval/ce_kl/kl_ci_masked", "kl_unmasked": "eval/ce_kl/kl_unmasked", "l0_layer_0": "eval/l0/0.0_layer_0",
                               "l0_layer_1": "eval/l0/0.0_layer_1", "l0_total": "eval/l0/0.0_total"}
EVAL_BATCH = 128  # the authors' evaluation batch size
LOGGED_N_BATCHES = 5  # the authors' number of evaluation batches
DEFAULT_N_BATCHES = 4  # 512 rows: a few minutes on a CPU
SUB_BATCH = 32
LABEL_THRESHOLD = 0.0  # the counts' threshold, as logged (eval/l0/0.0_*)


@dataclass(frozen=True)
class Rule:
    kind: str  # "stat": tolerance from SE between a floor and a ceiling; "bound": passes if ours <= floor
    floor: tuple[str, float]  # ("abs", nats) or ("rel", fraction of the logged value)
    ceiling: tuple[str, float] | None


RULES: dict[str, Rule] = {
    "kl_ci_masked": Rule("stat", ("abs", 0.005), ("abs", 0.025)),
    "kl_unmasked": Rule("bound", ("abs", 0.005), None),
    "l0_layer_0": Rule("stat", ("rel", 0.02), ("rel", 0.10)),
    "l0_layer_1": Rule("stat", ("rel", 0.02), ("rel", 0.10)),
    "l0_total": Rule("stat", ("rel", 0.02), ("rel", 0.10)),
}


class LoggedScoresMismatch(RuntimeError):
    """The small-model mode does not reproduce the authors' logged scores: its labels cannot be trusted."""


# ----------------------------------------------------------------------------- measurement


def measure_batches(model: Any, ids: np.ndarray, *, batch: int = EVAL_BATCH, sub_batch: int = SUB_BATCH, log: Any = print) -> dict[str, np.ndarray]:
    """Per batch of `batch` rows of `ids` (N, 512), in order: the own-label and fully-on distances (means over the batch's
    positions) and the per-layer counts of labels above 0 per position."""
    import torch
    from param_decomp.models.components import make_mask_infos

    from vpd_audit.importances import compute_importances
    from vpd_audit.metrics import per_position_kl

    assert ids.ndim == 2 and ids.shape[1] == SEQ_LEN, ids.shape
    N = ids.shape[0]
    assert N % batch == 0 and N // batch >= 2 and batch % sub_batch == 0, (N, batch, sub_batch)
    for name, p in model.named_parameters():
        assert p.dtype == torch.float32, (name, p.dtype)
    device = next(model.parameters()).device
    keys = sorted(model.module_to_c)
    layer_of = {k: k.split(".")[1] for k in keys}
    assert all(k.startswith("h.") for k in keys), keys
    layers = sorted(set(layer_of.values()))
    kl_ci, kl_on = np.zeros(N), np.zeros(N)
    counts = {layer: np.zeros(N, np.int64) for layer in layers}
    t0 = time.time()
    with torch.no_grad():
        for s in range(0, N, sub_batch):
            b = torch.from_numpy(np.ascontiguousarray(ids[s : s + sub_batch])).long().to(device)
            imp = compute_importances(model, b, precision="fp32", chunk=sub_batch)
            g, target = imp.g, imp.target_logits
            for k in keys:
                counts[layer_of[k]][s : s + sub_batch] += (g[k] > LABEL_THRESHOLD).sum(dim=(1, 2)).cpu().numpy()
            logits = model(b, mask_infos=make_mask_infos(g))
            kl_ci[s : s + sub_batch] = per_position_kl(target, logits).double().mean(dim=-1).cpu().numpy()
            logits = model(b, mask_infos=make_mask_infos({k: torch.ones_like(v) for k, v in g.items()}))
            kl_on[s : s + sub_batch] = per_position_kl(target, logits).double().mean(dim=-1).cpu().numpy()
            del imp, g, target, logits
            if (s // sub_batch) % 4 == 3:
                log(f"[logged scores] {s + sub_batch}/{N} rows ({time.time() - t0:.0f} s)")
    n_b = N // batch

    def bmean(x: np.ndarray) -> np.ndarray:
        return x.reshape(n_b, batch).mean(axis=1)

    out = {"kl_ci_masked": bmean(kl_ci), "kl_unmasked": bmean(kl_on)}
    positions = batch * SEQ_LEN
    total = np.zeros(n_b)
    for layer in layers:
        v = counts[layer].reshape(n_b, batch).sum(axis=1) / positions
        out[f"l0_layer_{layer}"] = v
        total = total + v
    out["l0_total"] = total
    return out


# ----------------------------------------------------------------------------- comparison (pure)


def _amount(spec: tuple[str, float], logged: float) -> float:
    kind, x = spec
    if kind == "abs":
        return float(x)
    assert kind == "rel", kind
    return float(x * abs(logged))


@dataclass
class Row:
    quantity: str
    logged_key: str
    logged: float
    ours: float
    diff: float  # ours - logged
    s_b: float
    n_b: int
    se: float
    three_se: float
    tolerance: float  # for a bound: the bound
    too_coarse: bool  # 3 SE above the ceiling: not resolved with these rows
    passed: bool


def evaluate(quantity: str, values: np.ndarray, logged: float) -> Row:
    """One quantity's batch values against its logged value, by its rule."""
    rule = RULES[quantity]
    v = np.asarray(values, dtype=np.float64)
    n_b = int(v.size)
    assert n_b >= 2, n_b
    ours, s_b = float(v.mean()), float(v.std(ddof=1))
    se = s_b * math.sqrt(1.0 / LOGGED_N_BATCHES + 1.0 / n_b)
    floor = _amount(rule.floor, logged)
    if rule.kind == "bound":
        return Row(quantity, LOGGED_KEYS[quantity], logged, ours, ours - logged, s_b, n_b, se, 3 * se, floor, False, bool(ours <= floor))
    assert rule.kind == "stat" and rule.ceiling is not None
    ceiling = _amount(rule.ceiling, logged)
    tol = min(ceiling, max(3.0 * se, floor))
    too_coarse = bool(3.0 * se > ceiling)
    return Row(quantity, LOGGED_KEYS[quantity], logged, ours, ours - logged, s_b, n_b, se, 3 * se, tol, too_coarse, bool(abs(ours - logged) <= tol and not too_coarse))


def compare(batch_values: dict[str, np.ndarray], logged: dict[str, float]) -> dict[str, Any]:
    """Every quantity's row, and the verdict: passes if every quantity passes."""
    assert set(batch_values) >= set(RULES) and set(logged) == set(RULES), (sorted(batch_values), sorted(logged))
    rows = [evaluate(q, batch_values[q], logged[q]) for q in RULES]
    failed = [r.quantity for r in rows if not r.passed]
    return {"passed": not failed, "failed": failed, "rows": [asdict(r) for r in rows]}


def render(result: dict[str, Any]) -> str:
    lines = [f"logged-score check, run {result['run']} ({result['decomp_run']}), {result['n_rows']} rows of {result['split']} in {result['n_batches']} batches of "
             f"{result['batch']}, label fix applied: {result['label_fix_applied']}",
             "| quantity | logged | ours | ours - logged | s_b | 3 SE | tolerance | passed |", "|---|---|---|---|---|---|---|---|"]
    for r in result["rows"]:
        tol = f"<= {r['tolerance']:.4g}" if RULES[r["quantity"]].kind == "bound" else f"{r['tolerance']:.4g}" + (" (too coarse)" if r["too_coarse"] else "")
        lines.append(f"| {r['quantity']} | {r['logged']:.5g} | {r['ours']:.5g} | {r['diff']:+.4g} | {r['s_b']:.3g} | {r['three_se']:.3g} | {tol} | {'yes' if r['passed'] else 'NO'} |")
    lines.append("verdict: " + ("passes" if result["passed"] else f"FAILS ({', '.join(result['failed'])})"))
    return "\n".join(lines)


# ----------------------------------------------------------------------------- the check


def check_logged_scores(model: Any, run: str, *, n_batches: int = DEFAULT_N_BATCHES, log: Any = print) -> dict[str, Any]:
    """Measure the logged quantities with `model` on the first `n_batches` x 128 rows of the run's test split and compare."""
    from vpd_audit.artifacts import AUDIT_RUNS, load_run_config
    from vpd_audit.data import prepare_simplestories_rows
    from vpd_audit.label_switch import is_switched

    assert run in LOGGED_SCORES, f"no logged scores are kept for run {run!r}"
    cfg = load_run_config(run)
    ids = prepare_simplestories_rows(n_batches * EVAL_BATCH, cfg, log=log)
    t0 = time.time()
    values = measure_batches(model, ids, log=log)
    out = compare(values, LOGGED_SCORES[run])
    out.update({"run": run, "decomp_run": AUDIT_RUNS[run].decomp_run, "split": f"{cfg.task_config.dataset_name}/{cfg.task_config.eval_data_split}",
                "n_rows": int(ids.shape[0]), "n_batches": n_batches, "batch": EVAL_BATCH, "label_fix_applied": is_switched(model),
                "device": str(next(model.parameters()).device), "seconds": time.time() - t0, "batch_values": {k: [float(x) for x in v] for k, v in values.items()}})
    return out


_PASSED_IN_PROCESS: set[str] = set()


def require_logged_scores(model: Any, run: str, *, n_batches: int = DEFAULT_N_BATCHES, log: Any = print) -> dict[str, Any] | None:
    """Run the check once per process for a run with logged scores, and stop the caller if it fails. A no-op for any other
    run (the 67M runs) and after the check has passed in this process."""
    if run not in LOGGED_SCORES or run in _PASSED_IN_PROCESS:
        return None
    res = check_logged_scores(model, run, n_batches=n_batches, log=log)
    log(render(res))
    if not res["passed"]:
        raise LoggedScoresMismatch(f"run {run}: the loaded model does not reproduce the authors' logged scores ({', '.join(res['failed'])}); "
                                   f"its labels cannot be trusted. See `vpd-audit check-logged-scores --run {run}`.")
    _PASSED_IN_PROCESS.add(run)
    return res
