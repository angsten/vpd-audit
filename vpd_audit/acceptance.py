"""The acceptance test, orchestrated: the eleven references on
all of E for the main run under bf16 autocast and again in float32, the control run under bf16
for check 8, the authors' `CEandKLLosses` (one instance per batch) at rounding thresholds 0,
0.1, and 0.5 on two batches of 64 in float32 for check 6, then the summary of the eight checks.
Outputs under `<results>/acceptance/`: the run manifests, the per-sequence tables, the
condition tables, the ours-versus-paper table, the summary of the checks, and the importance
statistics. Per-position arrays stay beside them on the volume.

Runnable on CPU in float32 with `--n 8 --jobs main_fp32 --primary main_fp32` so that the
summary code is exercised before any GPU is paid for.
"""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

import pandas as pd
import torch

from vpd_audit import env
from vpd_audit.artifacts import checkpoint_hashes, load_component_model
from vpd_audit.data import hash_ids, load_set
from vpd_audit.importances import ImportanceSums
from vpd_audit.reference import BATCH, acceptance_summary, authors_metric, condition_table, format_checks, run_references, vs_paper_table
from vpd_audit.results import code_commits, load_table

JOBS = {"main_bf16": ("main", "bf16"), "main_fp32": ("main", "fp32"), "control_bf16": ("control", "bf16"), "control_fp32": ("control", "fp32")}


def run_acceptance(
    *,
    device: str,
    subbatch: int = 64,
    n_draws: int = 8,
    master_seed: int = 0,
    n: int | None = None,
    out_root: Path | None = None,
    jobs: tuple[str, ...] = ("main_bf16", "main_fp32", "control_bf16"),
    primary: str = "main_bf16",
    fp32_job: str = "main_fp32",
    control_job: str = "control_bf16",
    check6: bool = True,
    check6_batch: int = 64,
    check6_n_batches: int = 2,
    check6_precision: str = "fp32",
    stat_batch: int = BATCH,
    on_subbatch: Any = None,
    log: Any = print,
) -> pd.DataFrame:
    """`check6_precision` is the autocast setting of the authors' class run here; fp32, the acceptance's
    setting, by default. The matched-shape bf16 comparison for check 6 is `short_runs.run_check6_matched`, not this."""
    torch.use_deterministic_algorithms(True, warn_only=True)
    out_root = out_root or (env.RESULTS_DIR / "acceptance")
    out_root.mkdir(parents=True, exist_ok=True)
    ids, _, record = load_set("E")
    if n is not None:
        ids = ids[:n]
    assert check6_batch * check6_n_batches <= ids.shape[0], "check 6 needs its batches inside the sequences run"
    set_hash = record["sha256_ids"]
    timings: dict[str, float] = {}

    for job in jobs:
        run, precision = JOBS[job]
        t0 = time.time()
        model = load_component_model(run, device)
        run_references(model, ids, job=job, run=run, out_dir=out_root / job, precision=precision, subbatch=subbatch, n_draws=n_draws,
                       master_seed=master_seed, set_name="E", set_hash=set_hash, checkpoint_hashes=checkpoint_hashes(run), resume=True,
                       on_subbatch=on_subbatch, log=log)
        df = load_table(out_root / job)
        condition_table(df, stat_batch).to_csv(out_root / f"conditions_{job}.csv", index=False)
        del model
        if device.startswith("cuda"):
            torch.cuda.empty_cache()
        timings[job] = time.time() - t0
        log(f"[acceptance] {job} in {timings[job]:.0f} s")

    theirs = None
    if check6:
        t0 = time.time()
        model = load_component_model("main", device)
        batches = [ids[i * check6_batch : (i + 1) * check6_batch] for i in range(check6_n_batches)]
        theirs = authors_metric(model, batches, (0.0, 0.1, 0.5), precision=check6_precision)
        with open(out_root / f"authors_metric_{check6_precision}.json", "w") as f:
            json.dump({"check6_batch": check6_batch, "n_batches": check6_n_batches, "precision": check6_precision, "per_threshold": theirs,
                       # provenance into the auxiliary outputs
                       "commits": code_commits(), "checkpoint_hashes": checkpoint_hashes("main"), "gpu": torch.cuda.get_device_name(0) if device.startswith("cuda") else None,
                       "torch_version": torch.__version__, "set_name": "E", "set_hash": set_hash, "set_hash_first_n": hash_ids(ids[: check6_batch * check6_n_batches])},
                      f, indent=2, sort_keys=True)
        del model
        if device.startswith("cuda"):
            torch.cuda.empty_cache()
        timings["authors_metric"] = time.time() - t0
        log(f"[acceptance] authors' metric at three thresholds on {check6_n_batches} x {check6_batch} in {timings['authors_metric']:.0f} s")

    summary = summarize(out_root, primary=primary, fp32_job=fp32_job, control_job=control_job, theirs=theirs, check6_batch=check6_batch,
                        stat_batch=stat_batch, log=log)
    with open(out_root / "timings.json", "w") as f:
        json.dump({"timings_s": timings, "device": device, "gpu": torch.cuda.get_device_name(0) if device.startswith("cuda") else None,
                   "subbatch": subbatch, "n_draws": n_draws, "n_sequences": int(ids.shape[0]), "stat_batch": stat_batch,
                   "check6_batch": check6_batch, "check6_n_batches": check6_n_batches}, f, indent=2)
    return summary


def summarize(
    out_root: Path,
    *,
    primary: str = "main_bf16",
    fp32_job: str = "main_fp32",
    control_job: str = "control_bf16",
    theirs: dict[str, list[dict[str, float]]] | None = None,
    check6_batch: int = 64,
    stat_batch: int = BATCH,
    log: Any = print,
) -> pd.DataFrame:
    """The eight checks from the tables under `out_root` (re-runnable on pulled results)."""
    out_root = Path(out_root)
    df_primary = load_table(out_root / primary)
    with open(out_root / primary / "marker.json") as f:
        sums = ImportanceSums.from_json(json.load(f)["extra"]["importance_sums"])
    df_fp32 = load_table(out_root / fp32_job) if (out_root / fp32_job / "per_sequence.parquet").is_file() else None
    df_control = load_table(out_root / control_job) if (out_root / control_job / "per_sequence.parquet").is_file() else None
    if theirs is None and (out_root / "authors_metric_fp32.json").is_file():
        with open(out_root / "authors_metric_fp32.json") as f:
            saved = json.load(f)
        theirs, check6_batch = saved["per_threshold"], int(saved["check6_batch"])
    summary = acceptance_summary(df_primary, sums, primary, df_fp32=df_fp32, fp32_label=fp32_job, theirs=theirs, check6_batch=check6_batch,
                                 df_control=df_control, batch_size=stat_batch)
    summary.to_csv(out_root / "summary.csv", index=False)
    vs_paper = vs_paper_table(df_primary, stat_batch)
    vs_paper.to_csv(out_root / "vs_paper.csv", index=False)
    with open(out_root / "importance_stats.json", "w") as f:
        json.dump({"n_positions": sums.n_positions, "mean_count_positive": sums.per_layer_mean_count(), "alive": sums.alive_counts(),
                   "count_above": sums.count_above}, f, indent=2)
    text = format_checks(summary)
    with open(out_root / "checks.txt", "w") as f:
        f.write(text + "\n")
    log(f"[acceptance] ours minus the paper ({primary}):\n" + vs_paper.to_string(index=False))
    log(text)
    gate = summary[(summary["check"].isin([1, 2, 3, 4, 5, 6])) & (summary["pass"].notna())]
    log(f"[acceptance] gate (checks 1-6): {int(gate['pass'].sum())}/{len(gate)} pass")
    return summary
