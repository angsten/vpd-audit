"""The three short runs: the two residual test cells and the bf16 rerun of check 6 at matched shapes, each its own
Modal launch on the 40 GB card, and the CPU summaries that read the committed tables against the pre-registered rules.

The two residual test cells (`run_residual_tests`): two `run_references` passes into `results/short_runs/`,
`residual_fp32` (float32, the first 256 of E, 4 draws) and `residual_bf16` (bf16, the first 512 of E, 2 draws), both at
sub-batch 32 with the importance chunk 32, master seed 0, deterministic algorithms on, the model loaded once (the
launches ran with the SHA-256 off and before the on-device fingerprint existed; a rerun would carry the fingerprint).
Conditions: target, unmasked, unmasked_delta, importances, importances_delta1, stochastic, stochastic_delta,
stochastic_delta1. The shared-mask guard builds the 24 component masks of the three stochastic cells on every sub-batch
and draw before the forwards and asserts `torch.equal` on both pairs (48 comparisons), recorded in the marker. Order
and shrink rule: the bf16 rerun of check 6 runs first, then the two passes, and the rerun's measured GPU compute
enters the projection; each pass is warmed up on 8 sequences (importances plus one masked forward) before its first
sub-batch is timed; if the projection of the fp32 pass, the bf16 pass, and the check 6 rerun together exceeds 180 s,
shrink in this order: fp32 to 128 sequences, bf16 to 256, bf16 draws to 1. Never dropped: both *_delta1 cells,
unmasked in fp32, at least two fp32 draws.

`residual_summary` (the CLI `vpd-audit short-runs-report`) computes what the readings of the two residual test cells
need: ||delta||^2 per pass, run (ii) s_b = KL(importances) - KL(importances_delta1), run (iii) Q = C_0 + C_1 - 2 C_u and
Delta = C_1 - C_0, the tripwire, the guard, the reproducibility against the acceptance tables, and the outcome labels
of the pre-registered reading rules, applied mechanically; a label is not an interpretation.
"""

from __future__ import annotations

import json
import math
import shutil
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

import gc
import hashlib

import numpy as np
import pandas as pd
import torch

from vpd_audit import env
from vpd_audit.artifacts import checkpoint_hashes, load_component_model
from vpd_audit.constants import IMPORTANCE_CHUNK
from vpd_audit.data import hash_ids, load_set
from vpd_audit.importances import compute_importances, module_keys
from vpd_audit.reference import (
    CONDITION_BY_NAME,
    Condition,
    authors_dtypes,
    authors_metric,
    build_condition_masks,
    check_two_code_paths,
    evaluate_condition,
    format_checks,
    run_references,
)
from vpd_audit.results import code_commits, load_table

SHORT_RUNS_SUBBATCH = 32  # fits the 40 GB card in both precisions (the smoke ran there)
RESIDUAL_CONDITION_NAMES: tuple[str, ...] = ("target", "unmasked", "unmasked_delta", "importances", "importances_delta1",
                                             "stochastic", "stochastic_delta", "stochastic_delta1")
RESIDUAL_CONDITIONS: tuple[Condition, ...] = tuple(CONDITION_BY_NAME[n] for n in RESIDUAL_CONDITION_NAMES)
STAT_BATCH = 128  # the paper's batch: batch means are over 128-sequence blocks of E
TRIPWIRE_TOL = 1e-5
TRIPWIRE_MIN_FRACTION = 0.90

# the residual test cells' reading rules, fixed before the runs
RUN_II_BANDS: dict[str, tuple[float, float]] = {"cancellation": (-0.035, -0.005), "orthogonal": (0.005, 0.020), "shortfall": (0.030, 0.055)}
RUN_II_POINTS: dict[str, str] = {"cancellation": "about -0.02 (= 4<a,delta> + ||delta||^2 with <a,delta> = -0.0076)", "orthogonal": "+||delta||^2, about +0.011", "shortfall": "about +0.042"}
RUN_II_INDETERMINATE_ABS = 0.005
RUN_III_CONSISTENT = (0.25, 0.60)
RUN_III_MARGINAL = (0.10, 0.80)
RUN_III_NEAR_ZERO = 0.10
RUN_III_POINT = "[1/3, 1/2] ||delta||^2 (1/3 for orthogonal per-matrix residual errors, 1/2 as they align)"


# ============================================================================= the residual test cells: the job


@dataclass
class PassSpec:
    name: str
    precision: str
    n: int
    n_draws: int

    @property
    def n_subbatches(self) -> int:
        return (self.n + SHORT_RUNS_SUBBATCH - 1) // SHORT_RUNS_SUBBATCH

    @property
    def n_cells(self) -> int:
        fixed = sum(1 for c in RESIDUAL_CONDITIONS if not c.per_draw)
        return fixed + self.n_draws * sum(1 for c in RESIDUAL_CONDITIONS if c.per_draw)


FULL_PASSES: tuple[PassSpec, ...] = (PassSpec("residual_fp32", "fp32", 256, 4), PassSpec("residual_bf16", "bf16", 512, 2))
SHRINK_BUDGET_S = 180.0


def make_shared_mask_guard(model: Any, n_draws: int, master_seed: int) -> Any:
    """The hook for `run_references`: on sub-batch i, for every draw, the component masks of `stochastic`,
    `stochastic_delta`, and `stochastic_delta1` must be bitwise equal on all 24 modules (48 comparisons), asserted;
    the residual masks of the two included cells are reported (uniform scalar against ones)."""
    keys = module_keys(model)
    c0, cu, c1 = CONDITION_BY_NAME["stochastic"], CONDITION_BY_NAME["stochastic_delta"], CONDITION_BY_NAME["stochastic_delta1"]

    def hook(i: int, imp: Any) -> dict[str, Any]:
        draws: dict[str, Any] = {}
        for k in range(n_draws):
            kw = dict(draw=k, subbatch_index=i, master_seed=master_seed)
            m0, d0 = build_condition_masks(c0, imp.g, model.module_to_c, **kw)
            mu, du = build_condition_masks(cu, imp.g, model.module_to_c, **kw)
            m1, d1 = build_condition_masks(c1, imp.g, model.module_to_c, **kw)
            assert d0 is None and du is not None and d1 is not None
            eq_u = [bool(torch.equal(m0[key], mu[key])) for key in keys]
            eq_1 = [bool(torch.equal(m0[key], m1[key])) for key in keys]
            bad = [key for key, e in zip(keys, eq_u) if not e] + [key for key, e in zip(keys, eq_1) if not e]
            assert all(eq_u) and all(eq_1), f"shared-mask guard: component masks differ on sub-batch {i}, draw {k}: {bad}"
            residual_differ = all(not torch.equal(du[key], d1[key]) for key in keys)
            delta1_ones = all(bool((d1[key] == 1).all()) and d1[key].shape == du[key].shape for key in keys)
            draws[f"k{k}"] = {"components_equal_stochastic_vs_stochastic_delta": int(sum(eq_u)),
                              "components_equal_stochastic_vs_stochastic_delta1": int(sum(eq_1)), "n_modules": len(keys),
                              "residual_masks_differ_stochastic_delta_vs_delta1": residual_differ, "residual_delta1_all_ones": delta1_ones}
            del m0, mu, m1, du, d1
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
        return {"guard": "shared_mask", "passed": True, "n_comparisons": 2 * len(keys) * n_draws, "draws": draws}

    return hook


def _sync(device: str) -> None:
    if str(device).startswith("cuda"):
        torch.cuda.synchronize()


def _warm_up(model: Any, ids8: np.ndarray, precision: str, weight_deltas: dict[str, torch.Tensor], device: str, master_seed: int) -> float:
    """8 sequences: importances plus one masked forward (the importances condition), so kernel and allocator start-up
    is not charged to the first timed sub-batch. Returns its wall time."""
    batch = torch.from_numpy(np.ascontiguousarray(ids8)).long().to(device)
    _sync(device)
    t0 = time.perf_counter()
    imp = compute_importances(model, batch, precision=precision)
    res = evaluate_condition(model, CONDITION_BY_NAME["importances"], batch, imp, draw=0, subbatch_index=0, master_seed=master_seed,
                             weight_deltas=weight_deltas)
    _sync(device)
    dt = time.perf_counter() - t0
    del imp, res, batch
    if str(device).startswith("cuda"):
        torch.cuda.empty_cache()
    return dt


def project_seconds(specs: dict[str, PassSpec], probe: dict[str, PassSpec], t_first: dict[str, float], check6_compute_s: float) -> float:
    """The projection of the three runs: per pass, the first sub-batch's time times the number of sub-batches, scaled by
    the ratio of cells if the draws were shrunk since the probe (approximate: the importance phase is per sub-batch, not
    per cell); plus the check 6 rerun's measured compute."""
    total = check6_compute_s
    for name, spec in specs.items():
        total += t_first[name] * spec.n_subbatches * (spec.n_cells / probe[name].n_cells)
    return total


def apply_shrink_rule(specs: dict[str, PassSpec], probe: dict[str, PassSpec], t_first: dict[str, float], check6_compute_s: float,
                      budget_s: float = SHRINK_BUDGET_S) -> tuple[dict[str, PassSpec], list[dict[str, Any]]]:
    """The shrink rule, pre-registered: while the projection exceeds the budget, shrink in order: fp32 to the first 128
    sequences; bf16 to the first 256; bf16 draws to 1. Both *_delta1 cells, unmasked in fp32, and the four fp32 draws are
    never touched. Returns the final specs and the steps taken, each with the projection before and after."""
    specs = {k: PassSpec(**asdict(v)) for k, v in specs.items()}
    steps: list[dict[str, Any]] = []
    order = (("residual_fp32", "n", 128), ("residual_bf16", "n", 256), ("residual_bf16", "n_draws", 1))
    for name, field_name, value in order:
        before = project_seconds(specs, probe, t_first, check6_compute_s)
        if before <= budget_s:
            break
        if name not in specs or getattr(specs[name], field_name) == value:
            continue
        setattr(specs[name], field_name, value)
        after = project_seconds(specs, probe, t_first, check6_compute_s)
        steps.append({"pass": name, "field": field_name, "value": value, "projection_before_s": before, "projection_after_s": after})
    return specs, steps


def decide_final_specs(probe: dict[str, PassSpec], t_first: dict[str, float], check6_compute_s: float, budget_s: float,
                       override_reason: str | None) -> tuple[dict[str, PassSpec], dict[str, Any]]:
    """The shrink rule's verdict, and whether it is applied. The rule always runs and its steps are recorded; when
    `override_reason` is given and the rule would shrink, the full sizes are kept and the override is recorded with its
    reason (the override was used once, when the check 6 rerun's measured compute alone exceeded the 180 s budget)."""
    projection = project_seconds(probe, probe, t_first, check6_compute_s)
    rule_specs, steps = apply_shrink_rule(probe, probe, t_first, check6_compute_s, budget_s)
    record: dict[str, Any] = {
        "projection_before_shrink_s": projection, "budget_s": budget_s,
        "shrink_rule": {"verdict": "shrink" if steps else "no shrink", "steps": steps, "final_if_applied": {k: asdict(v) for k, v in rule_specs.items()},
                        "projection_if_applied_s": project_seconds(rule_specs, probe, t_first, check6_compute_s),
                        "budget_met_if_applied": project_seconds(rule_specs, probe, t_first, check6_compute_s) <= budget_s},
    }
    if steps and override_reason:
        final = {k: PassSpec(**asdict(v)) for k, v in probe.items()}
        record["shrink_override"] = {"applied": True, "reason": override_reason, "kept": {k: asdict(v) for k, v in final.items()}}
    else:
        final = rule_specs
        record["shrink_override"] = {"applied": False, "reason": override_reason or None}
    record["shrink_steps_applied"] = [] if record["shrink_override"]["applied"] else steps
    record["projection_final_s"] = project_seconds(final, probe, t_first, check6_compute_s)
    return final, record


def run_residual_tests(
    *,
    device: str,
    check6_compute_s: float,
    budget_s: float = SHRINK_BUDGET_S,
    override_shrink_reason: str | None = None,
    master_seed: int = 0,
    out_root: Path | None = None,
    passes: tuple[PassSpec, ...] = FULL_PASSES,
    run: str = "main",
    set_name: str = "E",
    log: Any = print,
) -> dict[str, Any]:
    """The residual test cells: the two passes, the guard, the warm-up and probe, the shrink rule, and `residual_plan.json`.

    `override_shrink_reason`, when given, keeps the full sizes if the rule would shrink, and records the rule's verdict
    and the override with this reason. `run` and `set_name` default to the registered job (the main decomposition on E);
    they exist so the whole job can be dry-run on the SimpleStories decomposition on a CPU before any GPU is paid for."""
    assert check6_compute_s >= 0, "the check 6 rerun's measured GPU compute (seconds) must be given; it enters the shrink-rule projection"
    torch.use_deterministic_algorithms(True, warn_only=True)
    out_root = out_root or (env.RESULTS_DIR / "short_runs")
    out_root.mkdir(parents=True, exist_ok=True)
    ids, _, record = load_set(set_name)
    set_hash = record["sha256_ids"]
    hashes = checkpoint_hashes(run)
    t_load = time.perf_counter()
    model = load_component_model(run, device)
    weight_deltas = model.calc_weight_deltas()
    _sync(device)
    t_load = time.perf_counter() - t_load
    log(f"[residual] loaded {run} on {device} in {t_load:.1f} s; check 6 rerun compute {check6_compute_s:.1f} s, budget {budget_s:.0f} s")
    plan: dict[str, Any] = {"run": run, "set_name": set_name, "set_hash": set_hash, "checkpoint_hashes": hashes,
                            "check6_compute_s": check6_compute_s, "budget_s": budget_s, "subbatch": SHORT_RUNS_SUBBATCH, "importance_chunk": IMPORTANCE_CHUNK,
                            "master_seed": master_seed, "conditions": list(RESIDUAL_CONDITION_NAMES), "model_load_s": t_load,
                            "gpu": torch.cuda.get_device_name(0) if str(device).startswith("cuda") else None, "passes": {}}
    probe_specs = {p.name: p for p in passes}
    for spec in passes:
        assert spec.n <= ids.shape[0] and spec.n % SHORT_RUNS_SUBBATCH == 0, spec
        for c in RESIDUAL_CONDITIONS:
            assert c.name in RESIDUAL_CONDITION_NAMES
    subbatch_times: dict[str, list[float]] = {p.name: [] for p in passes}
    t_first: dict[str, float] = {}
    guard_by_pass = {p.name: make_shared_mask_guard(model, p.n_draws, master_seed) for p in passes}

    def run_pass(spec: PassSpec, *, max_subbatches: int | None) -> None:
        marks: list[float] = [time.perf_counter()]

        def on_subbatch(i: int) -> None:
            _sync(device)
            now = time.perf_counter()
            subbatch_times[spec.name].append(now - marks[-1])
            marks.append(now)

        run_references(model, ids[: spec.n], job=spec.name, run=run, out_dir=out_root / spec.name, precision=spec.precision,
                       subbatch=SHORT_RUNS_SUBBATCH, n_draws=spec.n_draws, master_seed=master_seed, set_name=set_name, set_hash=set_hash,
                       checkpoint_hashes=hashes, conditions=RESIDUAL_CONDITIONS, resume=True, importance_chunk=IMPORTANCE_CHUNK,
                       on_subbatch=on_subbatch, subbatch_hook=guard_by_pass[spec.name], max_subbatches=max_subbatches, log=log)

    # 1. warm up and time the first sub-batch of each pass at its full size
    for spec in passes:
        assert not (out_root / spec.name).exists(), f"{out_root / spec.name} exists: this job starts fresh (its probe times the first sub-batch); move the earlier attempt aside first"
        t_warm = _warm_up(model, ids[:8], spec.precision, weight_deltas, device, master_seed)
        run_pass(spec, max_subbatches=1)
        t_first[spec.name] = subbatch_times[spec.name][0]
        plan["passes"][spec.name] = {"probe": asdict(spec), "warm_up_8_seqs_s": t_warm, "first_subbatch_s": t_first[spec.name]}
        log(f"[residual] {spec.name}: warm-up {t_warm:.1f} s, first sub-batch of {SHORT_RUNS_SUBBATCH} {t_first[spec.name]:.1f} s "
            f"-> {t_first[spec.name] * spec.n_subbatches:.0f} s projected for {spec.n} sequences")

    # 2. the shrink rule, and the override if one is given
    final_specs, decision = decide_final_specs(probe_specs, t_first, check6_compute_s, budget_s, override_shrink_reason)
    steps = decision["shrink_steps_applied"]
    plan.update(decision)
    plan.update({"shrink_steps": steps, "final": {k: asdict(v) for k, v in final_specs.items()}})
    log(f"[residual] projection {decision['projection_before_shrink_s']:.0f} s against {budget_s:.0f} s; rule verdict: {decision['shrink_rule']['verdict']} "
        f"{decision['shrink_rule']['steps'] or ''}; override applied: {decision['shrink_override']['applied']}"
        + (f" ({override_shrink_reason})" if decision['shrink_override']['applied'] else "") + f"; running {plan['final']}")

    # 3. finish each pass: continue the probe's store if unchanged, else restart at the shrunk size
    for spec in passes:
        final = final_specs[spec.name]
        if asdict(final) != asdict(spec):
            aside = out_root / f"{spec.name}.probe_discarded"
            log(f"[residual] {spec.name} shrunk to n={final.n}, draws={final.n_draws}: the probe's store moves to {aside.name}; restarting the pass")
            assert not aside.exists(), aside
            shutil.move(out_root / spec.name, aside)  # nothing is deleted; the probe's one sub-batch stays beside the pass
            subbatch_times[spec.name] = []
            guard_by_pass[spec.name] = make_shared_mask_guard(model, final.n_draws, master_seed)
        t0 = time.perf_counter()
        run_pass(final, max_subbatches=None)
        _sync(device)
        plan["passes"][spec.name].update({"final": asdict(final), "restarted": asdict(final) != asdict(spec), "finish_call_s": time.perf_counter() - t0,
                                          "subbatch_s": subbatch_times[spec.name], "n_subbatches": final.n_subbatches,
                                          "mean_later_subbatch_s": float(np.mean(subbatch_times[spec.name][1:])) if len(subbatch_times[spec.name]) > 1 else None})
        if str(device).startswith("cuda"):
            torch.cuda.empty_cache()
    plan["gpu_compute_s"] = {"passes": {k: float(sum(v)) for k, v in subbatch_times.items()},
                             "warm_ups": {k: plan["passes"][k]["warm_up_8_seqs_s"] for k in plan["passes"]},
                             "probes_discarded": [k for k in plan["passes"] if plan["passes"][k]["restarted"]]}
    plan["gpu_compute_s"]["total_incl_warm_ups_and_discarded_probes"] = float(sum(plan["gpu_compute_s"]["passes"].values()) + sum(plan["gpu_compute_s"]["warm_ups"].values())
                                                                              + sum(t_first[k] for k in plan["gpu_compute_s"]["probes_discarded"]))
    with open(out_root / "residual_plan.json", "w") as f:
        json.dump(plan, f, indent=2, sort_keys=True)
    log(f"[residual] GPU compute: {plan['gpu_compute_s']}")
    return {"final": plan["final"], "shrink_steps": steps, "gpu_compute_s": plan["gpu_compute_s"]}


# ============================================================================= the residual test cells: the summary


def _single(df: pd.DataFrame, cond: str, col: str) -> pd.Series:
    sub = df[df["condition"] == cond]
    assert len(sub) > 0, f"no rows for {cond!r}"
    assert sub["draw"].nunique() == 1, f"{cond!r} has several draws; use _per_draw"
    s = pd.Series(sub[col].to_numpy(dtype=np.float64), index=sub["seq"].to_numpy()).sort_index()
    assert s.index.is_unique
    return s


def _per_draw(df: pd.DataFrame, cond: str, col: str) -> pd.DataFrame:
    """Rows (draw, seq) -> value, as a DataFrame indexed by seq with one column per draw."""
    sub = df[df["condition"] == cond]
    assert len(sub) > 0, f"no rows for {cond!r}"
    wide = sub.pivot(index="seq", columns="draw", values=col).sort_index()
    assert not wide.isna().any().any(), f"{cond!r}: missing (draw, seq) cells"
    return wide.astype(np.float64)


def _mean_se(values: np.ndarray) -> dict[str, float]:
    n = int(values.size)
    mean = float(np.mean(values))
    se = float(np.std(values, ddof=1) / math.sqrt(n)) if n > 1 else float("nan")
    return {"mean": mean, "se": se, "ci_2se": [mean - 2 * se, mean + 2 * se], "n": n}


def _batch_means(s: pd.Series, batch: int = STAT_BATCH) -> list[float]:
    return [float(x) for x in s.groupby(s.index // batch).mean()]


def label_run_ii(mean: float, se: float) -> str:
    """The sign first, with the +-2 SE interval clear of zero; then the magnitude against the bands."""
    lo, hi = mean - 2 * se, mean + 2 * se
    if abs(mean) <= RUN_II_INDETERMINATE_ABS or lo <= 0.0 <= hi:
        return "indeterminate"
    for name, (a, b) in RUN_II_BANDS.items():
        if a <= mean <= b:
            return name if (a <= lo and hi <= b) else "indeterminate"
    return "outside every band"


def label_run_iii(ratio: float) -> str:
    if abs(ratio) < RUN_III_NEAR_ZERO:
        return "near zero"
    if RUN_III_CONSISTENT[0] <= ratio <= RUN_III_CONSISTENT[1]:
        return "consistent"
    if RUN_III_MARGINAL[0] <= ratio <= RUN_III_MARGINAL[1]:
        return "marginal"
    return "inconsistent"


def summarize_residual_pass(df: pd.DataFrame, manifest: dict[str, Any], marker: dict[str, Any]) -> dict[str, Any]:
    precision = manifest["precision"]
    seqs = np.sort(df["seq"].unique())
    out: dict[str, Any] = {"precision": precision, "n_sequences": int(len(seqs)), "seq_first": int(seqs[0]), "seq_last": int(seqs[-1]),
                           "n_draws": int(manifest["n_draws"]), "subbatch": int(manifest["subbatch"]), "importance_chunk": int(manifest["importance_chunk"]),
                           "gpu_name": manifest.get("gpu_name"), "conditions": manifest["extra"]["conditions"], "do_hash": manifest["extra"].get("do_hash"),
                           "fingerprint": manifest.get("fingerprint")}
    # ||delta||^2: float32 the unmasked divergence; bf16 that minus the unmasked_delta row (the rounding floor)
    unm, unm_d = _single(df, "unmasked", "kl_mean"), _single(df, "unmasked_delta", "kl_mean")
    delta_sq = float(unm.mean()) if precision == "fp32" else float(unm.mean() - unm_d.mean())
    out["delta_sq"] = {"value": delta_sq, "unmasked_kl_mean": float(unm.mean()), "unmasked_delta_kl_mean": float(unm_d.mean()),
                       "rule": "fp32: mean kl_mean(unmasked); bf16: that minus mean kl_mean(unmasked_delta)"}
    # run (ii)
    run_ii: dict[str, Any] = {}
    for col in ("kl_mean", "ce"):
        s = _single(df, "importances", col) - _single(df, "importances_delta1", col)
        st = _mean_se(s.to_numpy())
        st.update({"batch_means_128": _batch_means(s), "fraction_positive": float((s > 0).mean()),
                   "corr_with_unmasked_kl": float(np.corrcoef(s.to_numpy(), unm.loc[s.index].to_numpy())[0, 1])})
        run_ii[col] = st
    run_ii["label"] = label_run_ii(run_ii["kl_mean"]["mean"], run_ii["kl_mean"]["se"])
    run_ii["definition"] = "s_b = KL_b(importances) - KL_b(importances_delta1), positive when the residual helps; label from the kl_mean version"
    out["run_ii"] = run_ii
    # run (iii)
    run_iii: dict[str, Any] = {}
    for col in ("kl_mean", "ce"):
        c0, cu, c1 = _per_draw(df, "stochastic", col), _per_draw(df, "stochastic_delta", col), _per_draw(df, "stochastic_delta1", col)
        assert c0.index.equals(cu.index) and c0.index.equals(c1.index) and list(c0.columns) == list(cu.columns) == list(c1.columns)
        q = (c0 + c1 - 2 * cu).mean(axis=1)  # over draws within each sequence first
        d = (c1 - c0).mean(axis=1)
        entry = {"Q": _mean_se(q.to_numpy()), "Delta": _mean_se(d.to_numpy()), "Q_batch_means_128": _batch_means(q), "Delta_batch_means_128": _batch_means(d),
                 "draws": [int(k) for k in c0.columns], "C0_mean": float(c0.to_numpy().mean()), "Cu_mean": float(cu.to_numpy().mean()), "C1_mean": float(c1.to_numpy().mean())}
        run_iii[col] = entry
    q_ratio = run_iii["kl_mean"]["Q"]["mean"] / delta_sq if delta_sq != 0 else float("nan")
    d_ratio = run_iii["kl_mean"]["Delta"]["mean"] / delta_sq if delta_sq != 0 else float("nan")
    run_iii.update({"Q_over_delta_sq": q_ratio, "Delta_over_delta_sq": d_ratio, "label": label_run_iii(q_ratio),
                    "definition": "Q_kb = C0 + C1 - 2 Cu, Delta_kb = C1 - C0 with C0 = stochastic, Cu = stochastic_delta, C1 = stochastic_delta1; "
                                  "averaged over draws within each sequence, then mean and SE over sequences; ratios use this pass's ||delta||^2"})
    out["run_iii"] = run_iii
    # tripwire
    imp_diff = (_single(df, "importances_delta1", "kl_mean") - _single(df, "importances", "kl_mean")).abs()
    st_diff = (_per_draw(df, "stochastic_delta1", "kl_mean") - _per_draw(df, "stochastic", "kl_mean")).abs()
    out["tripwire"] = {"tolerance": TRIPWIRE_TOL, "min_fraction": TRIPWIRE_MIN_FRACTION,
                       "importances_delta1_vs_importances": {"fraction_over_tol": float((imp_diff > TRIPWIRE_TOL).mean()), "n": int(imp_diff.size), "max_abs_diff": float(imp_diff.max())},
                       "stochastic_delta1_vs_stochastic": {"fraction_over_tol": float((st_diff.to_numpy() > TRIPWIRE_TOL).mean()), "n_pairs": int(st_diff.size), "max_abs_diff": float(st_diff.to_numpy().max())}}
    out["tripwire"]["both_cells_over_min_fraction"] = bool(out["tripwire"]["importances_delta1_vs_importances"]["fraction_over_tol"] > TRIPWIRE_MIN_FRACTION
                                                           and out["tripwire"]["stochastic_delta1_vs_stochastic"]["fraction_over_tol"] > TRIPWIRE_MIN_FRACTION)
    # the shared-mask guard from the marker
    hooks = marker.get("extra", {}).get("subbatch_hooks", {})
    n_sub = int(marker["done_through"]) + 1
    ok = len(hooks) == n_sub and all(
        h.get("passed") is True and all(d["components_equal_stochastic_vs_stochastic_delta"] == d["n_modules"] and d["components_equal_stochastic_vs_stochastic_delta1"] == d["n_modules"]
                                         for d in h["draws"].values()) for h in hooks.values())
    out["shared_mask_guard"] = {"holds_on_every_subbatch": bool(ok), "n_subbatches": n_sub, "n_subbatches_with_record": len(hooks),
                                "residual_masks_differ_everywhere": bool(all(d["residual_masks_differ_stochastic_delta_vs_delta1"] for h in hooks.values() for d in h["draws"].values())) if hooks else None,
                                "n_comparisons_total": int(sum(h.get("n_comparisons", 0) for h in hooks.values()))}
    # P3 on the two new permitted cells
    for name in ("importances_delta1", "stochastic_delta1"):
        sub = df[df["condition"] == name]
        out.setdefault("p3", {})[name] = {"min_gap": float(sub["min_gap"].min()), "n_below_label_max": int(sub["n_below_label"].max())}
    # the plain means of every condition, for the tables
    means: dict[str, dict[str, float]] = {}
    for name in out["conditions"]:
        sub = df[df["condition"] == name]
        means[name] = {"kl_mean": float(sub["kl_mean"].mean()), "ce": float(sub["ce"].mean()), "ce_minus_target": float((sub["ce"] - sub["ce_target"]).mean()), "n_rows": int(len(sub))}
    out["condition_means"] = means
    return out


def reproducibility_against_acceptance(df: pd.DataFrame, acc_dir: Path, conditions: tuple[str, ...] = ("unmasked", "importances")) -> dict[str, Any]:
    """The fresh single-draw rows against the acceptance table of the same precision on the same sequences, per sequence."""
    if not (acc_dir / "per_sequence.parquet").is_file():
        return {"available": False, "path": str(acc_dir)}
    acc = load_table(acc_dir)
    seqs = np.sort(df["seq"].unique())
    acc = acc[acc["seq"].isin(seqs)]
    out: dict[str, Any] = {"available": True, "path": str(acc_dir), "n_sequences": int(len(seqs)), "per_condition": {}}
    for name in conditions + ("target",):
        for col in ("kl_mean", "ce", "ce_target"):
            if name == "target" and col != "ce":
                continue
            a, b = _single(df, name, col), _single(acc, name, col)
            assert a.index.equals(b.index), (name, col)
            d = (a - b).abs()
            out["per_condition"].setdefault(name, {})[col] = {"max_abs_diff": float(d.max()), "mean_abs_diff": float(d.mean()), "n_over_1e-5": int((d > 1e-5).sum()), "n_over_1e-3": int((d > 1e-3).sum())}
    return out


def residual_summary(short_runs_dir: Path, acceptance_dir: Path | None = None) -> tuple[dict[str, Any], str]:
    """Everything the readings of the residual test cells need, from the committed tables; returns (summary, markdown)."""
    short_runs_dir = Path(short_runs_dir)
    summary: dict[str, Any] = {"rules": {"run_ii_bands": RUN_II_BANDS, "run_ii_points": RUN_II_POINTS, "run_ii_indeterminate_abs": RUN_II_INDETERMINATE_ABS,
                                         "run_iii_consistent": RUN_III_CONSISTENT, "run_iii_marginal": RUN_III_MARGINAL, "run_iii_near_zero": RUN_III_NEAR_ZERO,
                                         "run_iii_point": RUN_III_POINT, "tripwire_tol": TRIPWIRE_TOL, "tripwire_min_fraction": TRIPWIRE_MIN_FRACTION,
                                         "gate": "the shared-mask guard holds on every sub-batch and the float32 tripwire exceeds 90 percent for both cells"},
                               "passes": {}}
    if (short_runs_dir / "residual_plan.json").is_file():
        with open(short_runs_dir / "residual_plan.json") as f:
            summary["residual_plan"] = json.load(f)
    for name in ("residual_fp32", "residual_bf16"):
        d = short_runs_dir / name
        if not (d / "per_sequence.parquet").is_file():
            continue
        df = load_table(d)
        with open(d / "run_manifest.json") as f:
            manifest = json.load(f)
        with open(d / "marker.json") as f:
            marker = json.load(f)
        entry = summarize_residual_pass(df, manifest, marker)
        if acceptance_dir is not None:
            entry["reproducibility"] = reproducibility_against_acceptance(df, Path(acceptance_dir) / f"main_{manifest['precision']}")
        summary["passes"][name] = entry
    fp32 = summary["passes"].get("residual_fp32")
    gated = bool(fp32 and fp32["shared_mask_guard"]["holds_on_every_subbatch"] and fp32["tripwire"]["both_cells_over_min_fraction"]
                 and all(p["shared_mask_guard"]["holds_on_every_subbatch"] for p in summary["passes"].values()))
    summary["gate"] = {"passed": gated, "guard_every_pass": {k: v["shared_mask_guard"]["holds_on_every_subbatch"] for k, v in summary["passes"].items()},
                       "tripwire_fp32": fp32["tripwire"] if fp32 else None}
    summary["labels"] = {k: {"run_ii": v["run_ii"]["label"], "run_iii": v["run_iii"]["label"]} for k, v in summary["passes"].items()}
    return summary, format_residual_summary(summary)


def _f(x: Any, nd: int = 5) -> str:
    if x is None:
        return "n/a"
    if isinstance(x, float):
        return f"{x:.{nd}f}" if math.isfinite(x) else str(x)
    return str(x)


def format_residual_summary(s: dict[str, Any]) -> str:
    L: list[str] = ["# Short runs: the two residual test cells", ""]
    L.append("Labels below are the pre-registered rules applied mechanically; a label is not an interpretation.")
    L.append("")
    g = s["gate"]
    L.append(f"**Gate** (guard on every sub-batch, float32 tripwire > 90 % on both cells): {'PASS' if g['passed'] else 'FAIL'}; guard per pass {g['guard_every_pass']}")
    L.append("")
    for name, p in s["passes"].items():
        L.append(f"## {name}: {p['precision']}, {p['n_sequences']} sequences ({p['seq_first']}..{p['seq_last']}), {p['n_draws']} draws, sub-batch {p['subbatch']}, chunk {p['importance_chunk']}, {p['gpu_name']}")
        L.append("")
        L.append("| condition | mean KL | mean CE | CE - target | rows |")
        L.append("|---|---|---|---|---|")
        for c, m in p["condition_means"].items():
            L.append(f"| {c} | {_f(m['kl_mean'], 6)} | {_f(m['ce'], 5)} | {_f(m['ce_minus_target'], 5)} | {m['n_rows']} |")
        L.append("")
        d = p["delta_sq"]
        L.append(f"||delta||^2 = {_f(d['value'], 6)} (unmasked {_f(d['unmasked_kl_mean'], 6)}, unmasked_delta {_f(d['unmasked_delta_kl_mean'], 6)}; {d['rule']})")
        L.append("")
        r2 = p["run_ii"]
        for col in ("kl_mean", "ce"):
            st = r2[col]
            L.append(f"Run (ii), {col}: s-bar = {_f(st['mean'])} +- 2 SE [{_f(st['ci_2se'][0])}, {_f(st['ci_2se'][1])}] (SE {_f(st['se'], 6)}, n {st['n']}); "
                     f"batch means {[round(x, 5) for x in st['batch_means_128']]}; fraction s_b > 0: {_f(st['fraction_positive'], 3)}; corr with KL(unmasked): {_f(st['corr_with_unmasked_kl'], 3)}")
        L.append(f"Run (ii) label (kl_mean): **{r2['label']}**  (bands: {s['rules']['run_ii_bands']}; points: {s['rules']['run_ii_points']})")
        L.append("")
        r3 = p["run_iii"]
        for col in ("kl_mean", "ce"):
            e = r3[col]
            L.append(f"Run (iii), {col}: C0 {_f(e['C0_mean'])}, Cu {_f(e['Cu_mean'])}, C1 {_f(e['C1_mean'])}; Q-bar = {_f(e['Q']['mean'], 6)} +- 2 SE [{_f(e['Q']['ci_2se'][0], 6)}, {_f(e['Q']['ci_2se'][1], 6)}], "
                     f"batch means {[round(x, 6) for x in e['Q_batch_means_128']]}; Delta-bar = {_f(e['Delta']['mean'], 6)} +- 2 SE [{_f(e['Delta']['ci_2se'][0], 6)}, {_f(e['Delta']['ci_2se'][1], 6)}], draws {e['draws']}")
        L.append(f"Run (iii): Q-bar / ||delta||^2 = {_f(r3['Q_over_delta_sq'], 4)}; Delta-bar / ||delta||^2 = {_f(r3['Delta_over_delta_sq'], 4)} (prediction {s['rules']['run_iii_point']})")
        L.append(f"Run (iii) label: **{r3['label']}**  (consistent {s['rules']['run_iii_consistent']}, marginal within {s['rules']['run_iii_marginal']}, near zero below {s['rules']['run_iii_near_zero']})")
        L.append("")
        t = p["tripwire"]
        L.append(f"Tripwire (|dKL| > {t['tolerance']:.0e}): importances_delta1 vs importances {_f(t['importances_delta1_vs_importances']['fraction_over_tol'], 4)} of {t['importances_delta1_vs_importances']['n']} sequences "
                 f"(max {t['importances_delta1_vs_importances']['max_abs_diff']:.2e}); stochastic_delta1 vs stochastic {_f(t['stochastic_delta1_vs_stochastic']['fraction_over_tol'], 4)} of {t['stochastic_delta1_vs_stochastic']['n_pairs']} (draw, seq) pairs "
                 f"(max {t['stochastic_delta1_vs_stochastic']['max_abs_diff']:.2e}); both over {t['min_fraction']:.0%}: {t['both_cells_over_min_fraction']}")
        gd = p["shared_mask_guard"]
        L.append(f"Shared-mask guard: holds on every sub-batch = {gd['holds_on_every_subbatch']} ({gd['n_subbatches_with_record']}/{gd['n_subbatches']} sub-batches recorded, {gd['n_comparisons_total']} comparisons); residual masks differ everywhere = {gd['residual_masks_differ_everywhere']}")
        L.append(f"P3 on the new cells: {p['p3']}")
        rep = p.get("reproducibility")
        if rep and rep.get("available"):
            L.append(f"Reproducibility against {rep['path']} on {rep['n_sequences']} sequences: " + "; ".join(
                f"{c} {col}: max |d| {v['max_abs_diff']:.2e}, mean {v['mean_abs_diff']:.2e}, n > 1e-5: {v['n_over_1e-5']}, n > 1e-3: {v['n_over_1e-3']}"
                for c, cols in rep["per_condition"].items() for col, v in cols.items()))
        elif rep:
            L.append(f"Reproducibility: acceptance table not found at {rep['path']}")
        L.append("")
    if "residual_plan" in s:
        rp = s["residual_plan"]
        L.append("## The job's plan (residual_plan.json)")
        L.append(f"check 6 rerun compute {rp['check6_compute_s']:.1f} s; projection before shrink {rp['projection_before_shrink_s']:.1f} s against {rp['budget_s']:.0f} s; "
                 f"rule verdict: {rp.get('shrink_rule', {}).get('verdict')} {rp.get('shrink_rule', {}).get('steps')}; override: {rp.get('shrink_override')}; "
                 f"steps applied: {rp['shrink_steps'] or 'none'}; final {rp['final']}; projection of what ran {rp.get('projection_final_s', float('nan')):.1f} s; GPU compute {rp['gpu_compute_s']}")
        for k, v in rp["passes"].items():
            L.append(f"- {k}: warm-up (8 seqs) {v['warm_up_8_seqs_s']:.1f} s; first sub-batch {v['first_subbatch_s']:.1f} s; later sub-batches mean {_f(v.get('mean_later_subbatch_s'), 1)} s; restarted {v.get('restarted')}")
        L.append("")
    return "\n".join(L)


# ============================================================================= the bf16 rerun of check 6 at matched shapes


CHECK6_CONDITION_NAMES: tuple[str, ...] = ("target", "unmasked", "rounded_0", "rounded_0.1", "importances", "rounded_0.5", "zero_all")
CHECK6_CONDITIONS: tuple[Condition, ...] = tuple(CONDITION_BY_NAME[n] for n in CHECK6_CONDITION_NAMES)
CHECK6_THRESHOLDS: tuple[float, ...] = (0.0, 0.1, 0.5)
CHECK6_TOL = 1e-3  # check 6's pre-registered tolerance
CHECK6_IDENTICAL = 1e-4  # below this the bf16 path is the authors' at matched shape


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 23), b""):
            h.update(chunk)
    return h.hexdigest()


def run_check6_matched(
    *,
    device: str,
    precision: str = "bf16",
    class_batch: int = 32,
    n_batches: int = 4,
    thresholds: tuple[float, ...] = CHECK6_THRESHOLDS,
    master_seed: int = 0,
    out_root: Path | None = None,
    acceptance_root: Path | None = None,
    run: str = "main",
    set_name: str = "E",
    log: Any = print,
) -> dict[str, Any]:
    """The check 6 rerun at matched shapes, one launch: (1) the authors' `CEandKLLosses` at `class_batch`, `n_batches` batches, the first
    class_batch * n_batches sequences of E, under `precision`, at the three rounding thresholds; tried once, and on an
    out-of-memory error rerun at half the batch and twice the batches on the same sequences (recorded); never a larger
    card. (2) Our path on the same sequences at sub-batch equal to the class's batch and the importance chunk equal to
    it, into `<out_root>/ours_sb<B>/`; the manifest records the effective chunk. Then
    `authors_metric_<precision>.json` and the three comparisons of `check6_summary` into `checks_<precision>.txt`."""
    torch.use_deterministic_algorithms(True, warn_only=True)
    out_root = out_root or (env.RESULTS_DIR / "short_runs" / f"check6_{precision}")
    acceptance_root = acceptance_root or (env.RESULTS_DIR / "acceptance")
    out_root.mkdir(parents=True, exist_ok=True)
    n_seq = class_batch * n_batches
    ids_all, _, record = load_set(set_name)
    assert n_seq <= ids_all.shape[0]
    ids = ids_all[:n_seq]
    hashes = checkpoint_hashes(run)
    t0 = time.perf_counter()
    model = load_component_model(run, device)
    _sync(device)
    t_load = time.perf_counter() - t0
    log(f"[check6] loaded {run} on {device} in {t_load:.1f} s; class at {class_batch} x {n_batches} on the first {n_seq} of {set_name}, {precision}")

    # 1. the authors' class: one attempt at class_batch; on OOM, half the batch, twice the batches

    def run_class(B: int, nb: int) -> dict[str, list[dict[str, float]]]:
        batches = [ids[j * B : (j + 1) * B] for j in range(nb)]
        assert sum(b.shape[0] for b in batches) == n_seq
        return authors_metric(model, batches, thresholds, precision=precision)

    theirs, attempts, B, nb = run_class_with_fallback(run_class, class_batch, n_batches, n_seq, device=device, log=log)
    # 2. the dtypes on the authors' side, one batch of the chosen size
    dtypes = authors_dtypes(model, ids[:B], precision=precision)
    log(f"[check6] authors' dtypes: {dtypes['distinct']}, target logits {dtypes['target_logits_dtype']}")
    # 3. ours at sub-batch B with the importance chunk B
    ours_dir = out_root / f"ours_sb{B}"
    assert not ours_dir.exists(), f"{ours_dir} exists: this job starts fresh; move the earlier attempt aside first"
    _sync(device)
    t0 = time.perf_counter()
    run_references(model, ids, job=f"check6_{precision}_ours_sb{B}", run=run, out_dir=ours_dir, precision=precision, subbatch=B, n_draws=1,
                   master_seed=master_seed, set_name=set_name, set_hash=record["sha256_ids"], checkpoint_hashes=hashes, conditions=CHECK6_CONDITIONS,
                   resume=False, importance_chunk=B, log=log)
    _sync(device)
    t_ours = time.perf_counter() - t0
    log(f"[check6] ours at sub-batch {B}, chunk {B}, in {t_ours:.1f} s")
    # 4. the JSON
    acc_path = Path(acceptance_root) / f"main_{precision}" / "per_sequence.parquet"
    info: dict[str, Any] = {
        "precision": precision, "check6_batch": B, "n_batches": nb, "attempted_batch": class_batch, "attempted_n_batches": n_batches,
        "oom_at_attempted_batch": attempts[0]["ok"] is False, "attempts": attempts, "thresholds": list(thresholds), "n_sequences": n_seq,
        "run": run, "set_name": set_name, "set_hash_full_set": record["sha256_ids"], "set_hash_first_n": hash_ids(ids),
        "subbatch_ours": B, "importance_chunk_effective": B, "master_seed": master_seed,
        "dtypes": dtypes, "commits": code_commits(), "checkpoint_hashes": hashes,
        "gpu": torch.cuda.get_device_name(0) if str(device).startswith("cuda") else None, "torch_version": torch.__version__,
        "deterministic_algorithms": torch.are_deterministic_algorithms_enabled(),
        "seconds": {"model_load": t_load, "class": attempts[-1]["seconds"], "class_failed_attempts": sum(a["seconds"] for a in attempts if not a["ok"]), "ours": t_ours},
        "acceptance_table": {"path": str(acc_path), "sha256": sha256_file(acc_path) if acc_path.is_file() else None},
        "per_threshold": theirs,
    }
    info["seconds"]["gpu_compute_total"] = info["seconds"]["class"] + info["seconds"]["class_failed_attempts"] + info["seconds"]["ours"]
    with open(out_root / f"authors_metric_{precision}.json", "w") as f:
        json.dump(info, f, indent=2, sort_keys=True)
    # 5. the comparisons
    summary, text = check6_summary(out_root, acceptance_root, precision)
    with open(out_root / f"checks_{precision}.txt", "w") as f:
        f.write(text + "\n")
    with open(out_root / "check6_summary.json", "w") as f:
        json.dump(summary, f, indent=2, sort_keys=True)
    log(text)
    return {"check6_batch": B, "n_batches": nb, "oom_at_attempted_batch": info["oom_at_attempted_batch"], "epsilon_matched": summary["matched"]["epsilon"],
            "label": summary["matched"]["label"], "gpu_compute_s": info["seconds"]["gpu_compute_total"], "seconds": info["seconds"]}


def run_class_with_fallback(run_class: Any, class_batch: int, n_batches: int, n_seq: int, *, device: str, log: Any = print,
                            ) -> tuple[Any, list[dict[str, Any]], int, int]:
    """`run_class(B, nb)` once at (class_batch, n_batches); if it raises an out-of-memory
    error, once more at (class_batch // 2, 2 * n_batches) on the same sequences; a second failure stops the job.
    Returns (result, attempts, B, nb); every attempt, its wall time, and the error message are recorded."""
    attempts: list[dict[str, Any]] = []
    B, nb = class_batch, n_batches
    while True:
        _sync(device)
        t0 = time.perf_counter()
        try:
            result = run_class(B, nb)
            _sync(device)
            attempts.append({"batch": B, "n_batches": nb, "ok": True, "seconds": time.perf_counter() - t0})
            log(f"[check6] authors' class at {B} x {nb} in {attempts[-1]['seconds']:.1f} s")
            return result, attempts, B, nb
        except torch.cuda.OutOfMemoryError as e:
            dt = time.perf_counter() - t0
            msg = str(e).splitlines()[0][:400] if str(e) else "OutOfMemoryError"
            peak = torch.cuda.max_memory_allocated() / 1e9 if str(device).startswith("cuda") and torch.cuda.is_available() else None
            attempts.append({"batch": B, "n_batches": nb, "ok": False, "seconds": dt, "error": msg, "max_memory_allocated_gb": peak})
            log(f"[check6] authors' class at {B} x {nb}: out of memory after {dt:.1f} s ({msg})")
            del e
            gc.collect()
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
            if len(attempts) >= 2:
                raise RuntimeError("the authors' class ran out of memory twice on this function; stop and ask") from None
            B, nb = B // 2, nb * 2
            assert B >= 1 and B * nb == n_seq, (B, nb, n_seq)


def _epsilon(rows: list[dict[str, Any]]) -> dict[str, Any]:
    gated = [r for r in rows if r["pass"] is not None]
    diffs = [float(r["diff"]) for r in gated]  # unrounded ours - theirs; value/target are rounded for the printout
    per_batch = [float(r["diff"]) for r in gated if ", batch " in r["item"]]
    worst = max(gated, key=lambda r: abs(float(r["diff"]))) if gated else None
    return {"epsilon": max(abs(d) for d in diffs) if diffs else float("nan"), "n_gated": len(gated), "n_pass": int(sum(bool(r["pass"]) for r in gated)),
            "worst_item": worst["item"] if worst else None, "n_positive": int(sum(d > 0 for d in diffs)), "n_negative": int(sum(d < 0 for d in diffs)),
            "n_zero": int(sum(d == 0 for d in diffs)),
            "common_sign_every_quantity_and_batch": bool(per_batch) and (all(d > 0 for d in per_batch) or all(d < 0 for d in per_batch))}


def label_check6(eps: float, common_sign: bool) -> str:
    """The check 6 rerun's rule; the common-sign clause applies only above the identical-arithmetic band: a systematic
    bias of 1e-8 would otherwise stop the grid."""
    if eps > CHECK6_TOL or (common_sign and eps > CHECK6_IDENTICAL):
        return "fail"
    if eps <= CHECK6_IDENTICAL:
        return "pass, identical arithmetic"
    return "pass, localize"


def check6_summary(out_root: Path, acceptance_root: Path, precision: str) -> tuple[dict[str, Any], str]:
    """The three comparisons of the check 6 rerun from the files under `out_root` (re-runnable on the committed copies):
    1. matched shapes, gated: the class against ours_sb<B> through `check_two_code_paths` with check6_batch = B;
    2. unmatched shapes, reported: the class against the acceptance table of the same precision (sub-batch 64) on the
       same sequences; 3. shape sensitivity, reported: ours_sb<B> against that acceptance table per sequence."""
    out_root, acceptance_root = Path(out_root), Path(acceptance_root)
    with open(out_root / f"authors_metric_{precision}.json") as f:
        info = json.load(f)
    theirs, B, n_seq = info["per_threshold"], int(info["check6_batch"]), int(info["n_sequences"])
    df_ours = load_table(out_root / f"ours_sb{B}")
    with open(out_root / f"ours_sb{B}" / "run_manifest.json") as f:
        ours_manifest = json.load(f)
    assert ours_manifest["subbatch"] == B and ours_manifest["importance_chunk"] == B, "our path must run at the class's batch and chunk"
    summary: dict[str, Any] = {"precision": precision, "check6_batch": B, "n_batches": int(info["n_batches"]), "n_sequences": n_seq,
                               "oom_at_attempted_batch": info["oom_at_attempted_batch"], "attempts": info["attempts"], "dtypes_distinct": info["dtypes"]["distinct"],
                               "target_logits_dtype": info["dtypes"]["target_logits_dtype"], "ours_manifest": {k: ours_manifest[k] for k in ("subbatch", "importance_chunk", "g_dtype", "precision", "gpu_name")},
                               "rules": {"tol": CHECK6_TOL, "identical": CHECK6_IDENTICAL, "fail": "epsilon > tol, or a common sign across every quantity and batch when epsilon > identical"}}
    L: list[str] = [f"# Check 6 in {precision} at matched shapes: the authors' CEandKLLosses at batch {B} x {info['n_batches']} against our path at sub-batch {B}, chunk {B}, on the first {n_seq} sequences of E", ""]
    L.append(f"attempts: {info['attempts']}; dtypes on the authors' side: {info['dtypes']['distinct']}, target logits {info['dtypes']['target_logits_dtype']}; ours: g {ours_manifest['g_dtype']} on {ours_manifest['gpu_name']}")
    L.append("")
    # 1. matched, gated
    rows = check_two_code_paths(df_ours, theirs, B, tol=CHECK6_TOL)
    e = _epsilon(rows)
    e["label"] = label_check6(e["epsilon"], e["common_sign_every_quantity_and_batch"])
    summary["matched"] = e
    L.append(f"## 1. Matched shapes, gated: epsilon = {e['epsilon']:.2e} over {e['n_gated']} comparisons ({e['n_pass']} pass at {CHECK6_TOL:.0e}); signs +{e['n_positive']} / -{e['n_negative']} / 0 x{e['n_zero']}; "
             f"common sign across every quantity and batch: {e['common_sign_every_quantity_and_batch']}; worst: {e['worst_item']}; label: **{e['label']}**")
    L.append("")
    L.append(format_checks(pd.DataFrame(rows)))
    L.append("")
    # 2 and 3 need the acceptance table
    acc_dir = acceptance_root / f"main_{precision}"
    acc_path = acc_dir / "per_sequence.parquet"
    if acc_path.is_file():
        sha = sha256_file(acc_path)
        same = sha == info["acceptance_table"].get("sha256")
        summary["acceptance_table"] = {"path": str(acc_path), "sha256": sha, "same_file_as_job_used": same, "job_sha256": info["acceptance_table"].get("sha256")}
        acc = load_table(acc_dir)
        acc = acc[acc["seq"] < n_seq]
        with open(acc_dir / "run_manifest.json") as f:
            acc_manifest = json.load(f)
        rows_u = check_two_code_paths(acc, theirs, B, tol=CHECK6_TOL)
        eu = _epsilon(rows_u)
        for r in rows_u:
            r["pass"] = None  # reported, not gated
        summary["unmatched"] = {**eu, "acceptance_subbatch": acc_manifest["subbatch"], "acceptance_chunk": acc_manifest["importance_chunk"], "acceptance_gpu": acc_manifest.get("gpu_name")}
        L.append(f"## 2. Unmatched shapes, reported: the class at batch {B} against the acceptance table (sub-batch {acc_manifest['subbatch']}, chunk {acc_manifest['importance_chunk']}, {acc_manifest.get('gpu_name')}) on the same sequences: "
                 f"epsilon = {eu['epsilon']:.2e} over {eu['n_gated']} comparisons; worst: {eu['worst_item']}; the acceptance file's SHA-256 {sha[:16]}... same as the job used: {same}")
        L.append("")
        L.append(format_checks(pd.DataFrame(rows_u)))
        L.append("")
        # 3. shape sensitivity per sequence
        sens: dict[str, Any] = {}
        L.append(f"## 3. Shape sensitivity, reported: ours at sub-batch {B} against the acceptance table at sub-batch {acc_manifest['subbatch']} per sequence (M5's bf16 figure with g recomputed: 1.3e-3; with g fixed: 3.6e-4)")
        L.append("")
        L.append("| condition | column | max abs diff | mean abs diff | n > 1e-4 | n > 1e-3 |")
        L.append("|---|---|---|---|---|---|")
        for name in CHECK6_CONDITION_NAMES:
            for col in ("kl_mean", "ce"):
                if name == "target" and col == "kl_mean":
                    continue
                a, b = _single(df_ours, name, col), _single(acc, name, col)
                assert a.index.equals(b.index), (name, col)
                d = (a - b).abs()
                sens[f"{name}/{col}"] = {"max_abs_diff": float(d.max()), "mean_abs_diff": float(d.mean()), "n_over_1e-4": int((d > 1e-4).sum()), "n_over_1e-3": int((d > 1e-3).sum()), "n": int(d.size)}
                L.append(f"| {name} | {col} | {d.max():.2e} | {d.mean():.2e} | {int((d > 1e-4).sum())} | {int((d > 1e-3).sum())} |")
        summary["shape_sensitivity"] = sens
        summary["shape_sensitivity_max_kl"] = max(v["max_abs_diff"] for k, v in sens.items() if k.endswith("/kl_mean"))
        L.append("")
    else:
        summary["acceptance_table"] = {"path": str(acc_path), "available": False}
        L.append(f"## 2 and 3 skipped: acceptance table not found at {acc_path}")
    return summary, "\n".join(L)


# ============================================================================= the acceptance run's check 6, unrounded


def check6_unrounded(acceptance_root: Path, out_dir: Path, precision: str = "fp32") -> tuple[dict[str, Any], str]:
    """The acceptance run's check 6 was read from values rounded to five decimals, so its
    "agreement to 1e-5" was a ceiling. Recompute it on CPU from the committed acceptance files
    (`authors_metric_<precision>.json`, `main_<precision>/per_sequence.parquet`) with the unrounded `diff` field;
    `results/acceptance/` is read, never written."""
    acceptance_root, out_dir = Path(acceptance_root), Path(out_dir)
    with open(acceptance_root / f"authors_metric_{precision}.json") as f:
        saved = json.load(f)
    theirs, B = saved["per_threshold"], int(saved["check6_batch"])
    df = load_table(acceptance_root / f"main_{precision}")
    with open(acceptance_root / f"main_{precision}" / "run_manifest.json") as f:
        manifest = json.load(f)
    rows = check_two_code_paths(df, theirs, B, tol=CHECK6_TOL)
    e = _epsilon(rows)
    e["label"] = label_check6(e["epsilon"], e["common_sign_every_quantity_and_batch"])
    gated = [r for r in rows if r["pass"] is not None]
    per_quantity: dict[str, dict[str, Any]] = {}
    for r in gated:
        q = r["item"].split(": ", 1)[1]
        per_quantity.setdefault(q, []).append(float(r["diff"]))
    per_quantity = {q: {"max_abs": max(abs(d) for d in v), "median_abs": float(np.median([abs(d) for d in v])), "mean": float(np.mean(v)),
                        "n_positive": int(sum(d > 0 for d in v)), "n_negative": int(sum(d < 0 for d in v)), "n": len(v)} for q, v in per_quantity.items()}
    summary = {"precision": precision, "check6_batch": B, "n_batches": int(saved["n_batches"]), "acceptance_manifest": {k: manifest[k] for k in ("subbatch", "importance_chunk", "gpu_name", "precision", "g_dtype")},
               "acceptance_table_sha256": sha256_file(acceptance_root / f"main_{precision}" / "per_sequence.parquet"),
               "note": "the acceptance run's printout rounded value and target to five decimals; these are the unrounded differences ours - theirs",
               **e, "per_quantity": per_quantity}
    text = (f"# The acceptance run's check 6 in {precision}, unrounded: the authors' class at batch {B} x {saved['n_batches']} against the acceptance table "
            f"(sub-batch {manifest['subbatch']}, chunk {manifest['importance_chunk']}, {manifest.get('gpu_name')}) on the first {B * int(saved['n_batches'])} sequences of E\n\n"
            f"epsilon = {e['epsilon']:.3e} over {e['n_gated']} comparisons ({e['n_pass']} pass at {CHECK6_TOL:.0e}); signs +{e['n_positive']} / -{e['n_negative']} / 0 x{e['n_zero']}; "
            f"common sign: {e['common_sign_every_quantity_and_batch']}; worst: {e['worst_item']}; label: **{e['label']}**\n\n"
            "| quantity | max abs diff | median abs diff | mean diff | signs +/- | n |\n|---|---|---|---|---|---|\n"
            + "\n".join(f"| {q} | {v['max_abs']:.2e} | {v['median_abs']:.2e} | {v['mean']:+.2e} | +{v['n_positive']}/-{v['n_negative']} | {v['n']} |" for q, v in per_quantity.items())
            + "\n\n" + format_checks(pd.DataFrame(rows)))
    out_dir.mkdir(parents=True, exist_ok=True)
    with open(out_dir / f"checks_{precision}_unrounded.txt", "w") as f:
        f.write(text + "\n")
    with open(out_dir / "summary.json", "w") as f:
        json.dump(summary, f, indent=2, sort_keys=True)
    return summary, text
