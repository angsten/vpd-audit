"""The Modal app.

One image: Debian slim with Python 3.13, our `pyproject.toml`, `uv.lock`, and the submodule
copied in, dependencies installed from the lockfile with `uv sync --frozen` into the image's
interpreter (the submodule as the editable path dependency it is locally), and `vpd_audit`
mounted at run time; the environment variables of `env` point at `/cache`. One volume mounted at
`/cache` holding `artifacts/`, `sets/`, `results/`, `out/`, `hf/`. One secret holding the WandB
key, created with the Modal CLI from `.env` (`modal secret create vpd-audit-wandb --from-dotenv
.env`) and attached only to `fetch_artifacts`.

    uv run modal run --detach vpd_audit/modal_app.py::fetch_artifacts
    uv run modal run --detach vpd_audit/modal_app.py::prepare_data
    uv run modal run --detach vpd_audit/modal_app.py::smoke
    uv run modal run --detach vpd_audit/modal_app.py::acceptance
    uv run modal run --detach vpd_audit/modal_app.py::check6 --precision bf16          (check 6 at matched shapes, first)
    uv run modal run --detach vpd_audit/modal_app.py::residual_tests --check6-compute-s S   (the residual test cells, with the check6 launch's compute)
    uv run modal run --detach vpd_audit/modal_app.py::residual_matrix                  (the residual follow-up)
    uv run modal run --detach vpd_audit/modal_app.py::prepare_data --labeled           (the labeled sets)
    uv run modal run --detach vpd_audit/modal_app.py::donor_caches                     (the donor caches)
    uv run modal run --detach vpd_audit/modal_app.py::identities                       (the identities, with the control's D_prose cache and alive set first)
    uv run modal run --detach vpd_audit/modal_app.py::dry_run                          (the dry run of the grid)
    uv run modal run --detach vpd_audit/modal_app.py::h4                               (the H4 cross-check)
"""

from __future__ import annotations

import os
import subprocess
from pathlib import Path

import modal

PROJECT_ROOT = Path(__file__).resolve().parent.parent
REMOTE_ROOT = "/root"  # pyproject.toml, uv.lock, third_party/ at build; vpd_audit/ mounted at run time
CACHE = "/cache"
VOLUME_NAME = "vpd-audit-cache"
SECRET_NAME = "vpd-audit-wandb"
# every GPU function runs on the 40 GB A100, a single string, with 12 GiB of
# host memory; no fallback list, no 80 GB card. The CPU functions keep their settings.
GPU = "A100-40GB"
GPU_MEMORY_MIB = 12288


def _local_commits() -> dict[str, str]:
    """The commits and the dirty-tree flag at launch, into the image's environment (a launch from a dirty
    tree is allowed but visible in every manifest; only modified tracked files and untracked code count)."""
    if not modal.is_local():
        return {"VPD_AUDIT_COMMIT": os.environ.get("VPD_AUDIT_COMMIT", "unknown"), "VPD_AUDIT_SUBMODULE_COMMIT": os.environ.get("VPD_AUDIT_SUBMODULE_COMMIT", "unknown"),
                "VPD_AUDIT_DIRTY": os.environ.get("VPD_AUDIT_DIRTY", "unknown")}
    out = {}
    for var, path in (("VPD_AUDIT_COMMIT", PROJECT_ROOT), ("VPD_AUDIT_SUBMODULE_COMMIT", PROJECT_ROOT / "third_party" / "param-decomp")):
        try:
            out[var] = subprocess.run(["git", "-C", str(path), "rev-parse", "HEAD"], check=True, capture_output=True, text=True).stdout.strip()
        except Exception:
            out[var] = "unknown"
    from vpd_audit.results import dirty_tree_flag

    out["VPD_AUDIT_DIRTY"] = dirty_tree_flag(PROJECT_ROOT)
    return out


def _ignore_submodule(p: Path) -> bool:
    """Skip the submodule's git link, caches, papers, and any credentials file when copying it into the image
    (`.env`, `.env.*`, and `.venv` at any depth, since the authors' own instructions invite a credentials file there)."""
    parts = set(p.parts)
    if parts & {".git", "__pycache__", ".ruff_cache", ".pytest_cache", "param_decomp.egg-info", "papers", "node_modules", "logs", ".venv"}:  # logs/: the authors' logger writes there on import
        return True
    return any(part == ".env" or part.startswith(".env.") for part in p.parts)


image = (
    modal.Image.debian_slim(python_version="3.13")
    .apt_install("git")
    .pip_install("uv==0.11.26")
    .add_local_file(PROJECT_ROOT / "pyproject.toml", f"{REMOTE_ROOT}/pyproject.toml", copy=True)
    .add_local_file(PROJECT_ROOT / "uv.lock", f"{REMOTE_ROOT}/uv.lock", copy=True)
    .add_local_dir(PROJECT_ROOT / "third_party" / "param-decomp", f"{REMOTE_ROOT}/third_party/param-decomp", copy=True, ignore=_ignore_submodule)
    .workdir(REMOTE_ROOT)
    # The root project is not installed (it is mounted at run time); the editable path dependency on the submodule is.
    .run_commands("UV_PROJECT_ENVIRONMENT=/usr/local uv sync --frozen --no-dev --no-install-project --compile-bytecode --no-progress")
    .env({
        "VPD_AUDIT_CACHE_DIR": CACHE,
        "PARAM_DECOMP_OUT_DIR": f"{CACHE}/out",
        "HF_HOME": f"{CACHE}/hf",
        "CUBLAS_WORKSPACE_CONFIG": ":4096:8",  # deterministic cuBLAS for torch.use_deterministic_algorithms
        "PYTORCH_CUDA_ALLOC_CONF": "expandable_segments:True",  # less fragmentation on the 24 GB card
        "PYTHONUNBUFFERED": "1",
        **_local_commits(),
    })
    .add_local_python_source("vpd_audit")
)

app = modal.App("vpd-audit", image=image)
volume = modal.Volume.from_name(VOLUME_NAME, create_if_missing=True)


def _log(msg: str) -> None:
    print(msg, flush=True)


@app.function(volumes={CACHE: volume}, secrets=[modal.Secret.from_name(SECRET_NAME)], timeout=2 * 3600, cpu=2, memory=4096)
def fetch_artifacts(replace: bool = False) -> dict:
    """All five runs into /cache/artifacts with the manifest (CPU, the WandB secret; the key is never printed)."""
    from vpd_audit.artifacts import ALL_RUN_IDS, fetch_artifacts as _fetch

    manifest = _fetch(list(ALL_RUN_IDS), replace=replace, log=_log)
    volume.commit()
    return {"runs": sorted(manifest["runs"]), "n_files": len(manifest["files"])}


@app.function(volumes={CACHE: volume}, timeout=3 * 3600, cpu=2, memory=16384)
def prepare_data(labeled: bool = False) -> dict:
    """E and D_unif into /cache/sets (CPU); with `--labeled`, the labeled sets, the calibration rows of
    the code filter, sets/labeled_manifest.json, and the round-trip check on E and every labeled set, with the JSON outputs
    also under /cache/results/data/. 16 GiB for the labeled file.

        uv run modal run --detach vpd_audit/modal_app.py::prepare_data --labeled
    """
    from vpd_audit import env
    from vpd_audit.data import load_set, prepare_labeled_sets, prepare_stream_sets

    if not labeled:
        out = prepare_stream_sets(log=_log)
        volume.commit()
        return {name: load_set(name)[2]["sha256_ids"] for name in out}
    from vpd_audit.roundtrip import run_round_trip

    results_dir = env.RESULTS_DIR / "data"
    manifest = prepare_labeled_sets(results_dir=results_dir, log=_log)
    volume.commit()
    names = ["E", "D_code", "D_prose", "E_lab_github", "E_lab_other", "E_lab", "calib_github", "calib_other"] + sorted(n for n in manifest["sets"] if n.startswith("panel_"))
    rt = run_round_trip(names, results_dir / "round_trip.json", log=_log)
    volume.commit()
    return {"sets": {n: manifest["sets"][n]["rows"] for n in manifest["sets"]}, "round_trip_pass": {n: v["passed"] for n, v in rt["sets"].items()}}


@app.function(volumes={CACHE: volume}, gpu=GPU, timeout=3 * 3600, memory=GPU_MEMORY_MIB)
def smoke(n: int = 64, subbatch: int = 32, n_draws: int = 2, run: str = "main", precision: str = "bf16") -> dict:
    """M1 to M6, M12, and M13 on n sequences of E, sub-batch 32, in bf16 autocast (M13 runs the float32 pass),
    with the fingerprint on and the references extended by the two residual test conditions, plus G1, G2, G3, G3b and
    the cross-entropy diagnostic of the matched-shape check 6 rerun's "localize" row, into /cache/results/smoke_fp/."""
    import torch

    from vpd_audit.smoke import format_checks, run_smoke

    _log(f"[modal] smoke on {torch.cuda.get_device_name(0)}; torch {torch.__version__}")
    checks = run_smoke(run, n, precision=precision, device="cuda", subbatch=subbatch, n_draws=n_draws, subbatch_sizes=(1, 16, 32), log=_log)
    text = format_checks(checks)
    _log(text)
    out_dir = Path(CACHE) / "results" / "smoke_fp"  # results/smoke/ from the earlier smoke, before the fingerprint existed, stays untouched
    out_dir.mkdir(parents=True, exist_ok=True)
    with open(out_dir / f"checks_{run}_{precision}_n{n}.txt", "w") as f:
        f.write(text + "\n")
    volume.commit()
    n_fail = len([c for c in checks if c.passed is False])
    _log(f"[modal] smoke: {len([c for c in checks if c.passed is True])} pass, {n_fail} fail, {len([c for c in checks if c.passed is None])} reported")
    return {"n_fail": n_fail, "n_pass": len([c for c in checks if c.passed is True])}


@app.function(volumes={CACHE: volume}, gpu=GPU, timeout=8 * 3600, memory=GPU_MEMORY_MIB)
def acceptance(subbatch: int = 64, n_draws: int = 8, check6_batch: int = 64, check6_n_batches: int = 2) -> dict:
    """The acceptance test on all of E: main in bf16 and float32, the control in bf16, the authors' metric, the eight checks."""
    import torch

    from vpd_audit.acceptance import run_acceptance

    _log(f"[modal] acceptance on {torch.cuda.get_device_name(0)}; torch {torch.__version__}")

    def commit_every_fourth(i: int) -> None:
        if i % 4 == 3:
            volume.commit()

    summary = run_acceptance(device="cuda", subbatch=subbatch, n_draws=n_draws, check6_batch=check6_batch, check6_n_batches=check6_n_batches,
                             on_subbatch=commit_every_fourth, log=_log)
    volume.commit()
    gate = summary[(summary["check"].isin([1, 2, 3, 4, 5, 6])) & (summary["pass"].notna())]
    return {"gate_pass": int(gate["pass"].sum()), "gate_total": int(len(gate))}


@app.function(volumes={CACHE: volume}, gpu=GPU, timeout=3600, memory=GPU_MEMORY_MIB)
def timing(subbatch: int = 64, n_draws: int = 8, compile_fingerprint: bool = False) -> dict:
    """One sub-batch of 64 of E on the main run in bf16, phase-timed, on the 40 GB card, with the
    fingerprint on (it always is) and the SHA-256 off, into timing_main_bf16_sb<B>_fp.json. The fingerprint phase is
    what is judged (0.05 s per cell expected, 0.1 s the trigger); the total is reported beside the earlier 8.6 s but not
    judged, since this card's memory bandwidth is lower than the 80 GB card's. The card Modal placed the run on is
    recorded in the table's header and in the JSON, never refused: a timing on another
    card is read as that card's, not against one on the 40 GB card.

    With `--compile-fingerprint`, the same sub-batch is timed a second time with the
    fingerprint's slab function under torch.compile (warmed up first so compilation is not charged), the compiled path
    asserted live through its call counter, and every cell's digest asserted equal to the eager run's; the two tables
    are written side by side into timing_main_bf16_sb<B>_fp_compile.json. The gate for keeping it is a gain of at
    least 0.3 s per cell-pass over E on the fingerprint phase, read off the JSON, plus the dry run's digests.

        uv run modal run --detach vpd_audit/modal_app.py::timing --compile-fingerprint
    """
    import json

    import torch

    from vpd_audit.artifacts import checkpoint_hashes, load_component_model
    from vpd_audit.data import load_set
    from vpd_audit.results import code_commits
    from vpd_audit.timing import format_split, time_subbatch

    torch.use_deterministic_algorithms(True, warn_only=True)
    gpu_name = torch.cuda.get_device_name(0)
    _log(f"[modal] timing on {gpu_name}; torch {torch.__version__}")
    # Modal has been seen to place an "A100-40GB" request on an 80 GB card (an earlier smoke run).
    # Like every GPU function here, this one records the card and continues; the table header states it.
    if "40GB" not in gpu_name:
        _log(f"[modal] timing: Modal placed this run on {gpu_name!r}, not a 40 GB A100; recorded, continuing")
    model = load_component_model("main", "cuda")
    ids, _, record = load_set("E")
    sub = ids[:subbatch]
    # warm-up: one importance computation and one forward, so kernel and allocator start-up is not charged to a phase
    time_subbatch(model, sub[:8], precision="bf16", do_sha256=False, n_draws=1, log=_log)
    results = [time_subbatch(model, sub, precision="bf16", do_sha256=False, n_draws=n_draws, log=_log)]
    n_sub = (ids.shape[0] + subbatch - 1) // subbatch
    compile_info: dict = {}
    if compile_fingerprint:
        from vpd_audit.fingerprint import COMPILE, enable_compile, expected_slab_calls

        enable_compile(True)
        t0 = __import__("time").time()
        time_subbatch(model, sub[:8], precision="bf16", do_sha256=False, n_draws=1, log=_log)  # compiles the six module shapes at the full slab
        time_subbatch(model, sub[:1], precision="bf16", do_sha256=False, n_draws=1, log=_log)  # and the short slab (B = 1 groups)
        compile_info["warmup_s"] = __import__("time").time() - t0
        compile_info["compiles_after_warmup"] = COMPILE["compiles"]
        enable_compile(True)  # resets the counters, keeps the compiled function
        r_c = time_subbatch(model, sub, precision="bf16", do_sha256=False, n_draws=n_draws, log=_log)
        expected = expected_slab_calls(int(sub.shape[0]), len(model.module_to_c), r_c["n_cells"])
        compile_info.update({"calls": COMPILE["calls"], "expected_calls": expected, "live": COMPILE["calls"] == expected, "recompiles_during_timing": COMPILE["compiles"],
                             "digests_equal_eager": r_c["digests"] == results[0]["digests"], "n_cells": r_c["n_cells"],
                             "fingerprint_s_per_cell_eager": results[0]["fingerprint_s_per_cell"], "fingerprint_s_per_cell_compiled": r_c["fingerprint_s_per_cell"],
                             "gain_s_per_pass_over_E": (results[0]["fingerprint_s_per_cell"] - r_c["fingerprint_s_per_cell"]) * n_sub, "gate_s_per_pass": 0.3})
        compile_info["keep"] = bool(compile_info["live"] and compile_info["digests_equal_eager"] and compile_info["gain_s_per_pass_over_E"] >= 0.3)
        r_c["compiled_fingerprint"] = True
        results.append(r_c)
        enable_compile(False)
        _log(f"[modal] timing: compiled slab live {compile_info['live']} ({compile_info['calls']} of {expected} slab calls), digests equal eager {compile_info['digests_equal_eager']}, "
             f"fingerprint {compile_info['fingerprint_s_per_cell_eager']:.3f} -> {compile_info['fingerprint_s_per_cell_compiled']:.3f} s per cell per sub-batch, "
             f"gain {compile_info['gain_s_per_pass_over_E']:.2f} s per cell-pass over E against the 0.3 s gate -> keep: {compile_info['keep']}")
    text = format_split(results, n_sub)
    _log(text)
    out_dir = Path(CACHE) / "results" / "timing"
    out_dir.mkdir(parents=True, exist_ok=True)
    name = f"timing_main_bf16_sb{subbatch}_fp{'_compile' if compile_fingerprint else ''}.json"
    with open(out_dir / name, "w") as f:
        json.dump({"results": results, "n_subbatches_in_E": n_sub, "table": text, "gpu": gpu_name, "on_40gb_card": "40GB" in gpu_name, "torch_version": torch.__version__,
                   "commits": code_commits(), "checkpoint_hashes": checkpoint_hashes("main"), "set_name": "E", "set_hash": record["sha256_ids"],
                   "n_sequences_timed": int(sub.shape[0]), "max_memory_allocated_gb": torch.cuda.max_memory_allocated() / 1e9, "compile": compile_info}, f, indent=2)
    volume.commit()
    return {"total_s": results[0]["total_s"], "fingerprint_s_per_cell": results[0]["fingerprint_s_per_cell"], "max_memory_allocated_gb": torch.cuda.max_memory_allocated() / 1e9,
            "compile": {k: v for k, v in compile_info.items() if k in ("live", "digests_equal_eager", "gain_s_per_pass_over_E", "keep")}}


@app.function(volumes={CACHE: volume}, gpu=GPU, timeout=3600, memory=GPU_MEMORY_MIB)
def timing_grid(subbatch: int = 64, run: str = "main", compile_fingerprint: bool = False) -> dict:
    """The grid-slice timing: one sub-batch of `subbatch` of E on `run` in bf16
    through one cell of each tier-1 type and the references (`timing.grid_slice_cells`, 16 cells), phases and the peak
    GPU memory recorded with the card named, after a warm-up on 8 sequences; then the same cells on one sequence, the
    short-slab shape of the donor-side rung-4 groups. With `--compile-fingerprint` the fingerprint's slab runs under
    torch.compile (only if the gate of `timing --compile-fingerprint` was passed). Into /cache/results/timing/timing_grid_<run>_bf16_sb<B>.json.

        uv run modal run --detach vpd_audit/modal_app.py::timing_grid
    """
    import json
    import shutil

    import numpy as np
    import torch

    from vpd_audit import env
    from vpd_audit.artifacts import checkpoint_hashes, load_component_model
    from vpd_audit.cells import build_sources
    from vpd_audit.data import load_set
    from vpd_audit.donors import donors_dir
    from vpd_audit.results import code_commits
    from vpd_audit.sources import Cache, source_hash
    from vpd_audit.timing import format_grid_split, grid_slice_cells, time_grid_subbatch

    torch.use_deterministic_algorithms(True, warn_only=True)
    gpu_name = torch.cuda.get_device_name(0)
    _log(f"[modal] timing_grid on {gpu_name}; torch {torch.__version__}")
    if "40GB" not in gpu_name:
        _log(f"[modal] timing_grid: Modal placed this run on {gpu_name!r}, not a 40 GB A100; recorded, continuing")
    if compile_fingerprint:
        from vpd_audit.fingerprint import enable_compile

        enable_compile(True)
    model = load_component_model(run, "cuda")
    ids, _, record = load_set("E")
    cache = Cache.load(f"D_unif_{run}")
    alive_vec = np.load(donors_dir() / f"alive_D_unif_{run}.npy")
    module_to_c = {k: model.module_to_c[k] for k in sorted(model.module_to_c)}
    cells = grid_slice_cells(run)
    sources = build_sources(cells, {f"D_unif_{run}": cache}, {run: (alive_vec, source_hash(alive_vec))}, None, None, module_to_c, log=_log)
    hashes = checkpoint_hashes(run)
    # the timing stores are scratch and hold rung-4 rows of the paper's model, so they go to the
    # container's local /tmp, never to the volume, and a job that dies before its cleanup leaves nothing there
    import tempfile

    scratch = Path(tempfile.mkdtemp(prefix="timing_grid_"))
    assert not str(scratch).startswith(CACHE)
    common = dict(run=run, precision="bf16", set_name="E", set_hash=record["sha256_ids"], checkpoint_hashes=hashes, log=_log)
    time_grid_subbatch(model, ids[:8], cells, sources, out_dir=scratch / "warmup", **common)  # warm-up: kernels, the allocator, and any compilation
    results = [time_grid_subbatch(model, ids[:subbatch], cells, sources, out_dir=scratch / f"b{subbatch}", **common),
               time_grid_subbatch(model, ids[:1], cells, sources, out_dir=scratch / "b1", **common)]
    n_sub = (ids.shape[0] + subbatch - 1) // subbatch
    text = format_grid_split(results, n_sub)
    _log(text)
    out_dir = env.RESULTS_DIR / "timing"
    out_dir.mkdir(parents=True, exist_ok=True)
    with open(out_dir / f"timing_grid_{run}_bf16_sb{subbatch}{'_compile' if compile_fingerprint else ''}.json", "w") as f:
        json.dump({"results": results, "n_subbatches_in_E": n_sub, "table": text, "gpu": gpu_name, "on_40gb_card": "40GB" in gpu_name, "torch_version": torch.__version__,
                   "compile_fingerprint": compile_fingerprint, "commits": code_commits(), "checkpoint_hashes": hashes, "set_name": "E", "set_hash": record["sha256_ids"]}, f, indent=2)
    shutil.rmtree(scratch, ignore_errors=True)  # the timing stores are scratch on local disk, never results
    volume.commit()
    return {"gpu": gpu_name, "total_s_b64": results[0]["total_s"], "per_cell_pass_over_E_s": results[0]["per_cell_s_excluding_importances"] * n_sub,
            "max_memory_allocated_gb": results[0]["max_memory_allocated_gb"], "one_sequence_total_s": results[1]["total_s"]}


# ----------------------------------------------------------------------------- the grid on the paper's model


def _commit_every_fourth(i: int) -> None:
    if i % 4 == 3:
        volume.commit()


def _parse_list(s: str) -> tuple[str, ...]:
    return tuple(x.strip() for x in s.split(",") if x.strip())


@app.function(volumes={CACHE: volume}, gpu=GPU, timeout=4 * 3600, memory=GPU_MEMORY_MIB)
def grid(run: str = "main", tiers: str = "1", groups: str = "", draws: int = 8, subbatch: int = 64, subset: str = "") -> dict:
    """The grid on the paper's model, one tier (or several, comma-separated) of one run, on the 40 GB
    card with 12 GiB of host memory, bf16, chunk 32, resume always, no renaming: /cache/results/grid/<run>/tier<t>/<group>/,
    one store per group per tier. The adaptive rule is computed from the run's caches over `draws` draws and written to
    results/grid/<run>/adaptive_rule.json on the first launch; every later launch recomputes it and asserts equality. The
    volume is committed every four sub-batches and at the end. Every store on E or E_lab carries the full reference set.
    After the groups, the two-path check of the conditional damage. The summary
    printed is format_summary with the P5 rule. `groups` filters ("E,E_lab"). Modal's CLI takes strings, hence the
    comma-separated tiers and groups.

        uv run modal run --detach vpd_audit/modal_app.py::grid --run main --tiers 1
        uv run modal run --detach vpd_audit/modal_app.py::grid --run main --tiers 3 --subset never_named

    `subset`: a named subset of cells (cells.SUBSETS) into separately named stores
    (<group>__<subset>), each carrying the references: never_named, levels, ranked, curve1_extra, tau0_union, editing_extra,
    donor_side.

    Tier 4, on the main run only, by subset: `marginal` (the marginal-matched control, with its two
    canaries) and `code_leaning` (the chain and its usage-matched twins, enumerated only if the existence rule of the run's
    s7 pre-read allows it). Every tier-4 set is asserted equal, by source hash, to the set that pre-read judged,
    before any forward pass.

        uv run modal run --detach vpd_audit/modal_app.py::grid --run main --tiers 4 --subset marginal
        uv run modal run --detach vpd_audit/modal_app.py::grid --run main --tiers 4 --subset code_leaning

    Tier 5, on the main run only, by subset, `plain_terms` first: `plain_terms` (the re-runs of committed
    cells with the plain-terms extras, and the two comparison models after their pre-flight gates), `same_domain`, `self_merge`.
    Its stores go to a root of their own, /cache/results/grid/<run>_s9/tier5/<group>__<subset>/, which `analysis.load_grid` never
    walks (the re-runs repeat committed cell names). Before any forward pass every named set is asserted against the s9
    label-only tables and the example positions against the committed list; after every sub-batch the re-run cells and the
    references are held bitwise to the committed stores, and the D_unif rows to the donor-side stores within 0.01 nats; a
    failure stops the launch. It prints gates and assertions only.

        uv run modal run --detach vpd_audit/modal_app.py::grid --run main --tiers 5 --subset plain_terms
        uv run modal run --detach vpd_audit/modal_app.py::grid --run main --tiers 5 --subset same_domain
        uv run modal run --detach vpd_audit/modal_app.py::grid --run main --tiers 5 --subset self_merge

    Tier 6, on the main run only, its one subset: `binary_union` (the binary
    union in two forms, the primary's look-alike control, the self-merge in both binary forms, four references and one canary) into
    /cache/results/grid/<run>_s11/tier6/E__binary_union/. Before any forward pass every named set is held to its committed twin (tiers 1
    to 4 and tier 5) and the self-merge's sets to the s9 label-only tables; a failure stops the launch. It prints gates and assertions only.

        uv run modal run --detach vpd_audit/modal_app.py::grid --run main --tiers 6 --subset binary_union

    Tier 7, on the main run only, by subset, `merge_sizes` first: `merge_sizes` (the merges of 2 and 4 donor tokens on E with both controls
    and on E_lab from three pools, with their canaries) and `panel_edit` (the code-leaning edit on the eight panels, and its canary on E_lab),
    into /cache/results/grid/<run>_s12/tier7/. Before any forward pass every 2- and 4-token set is held to the label-only table and every
    panel edit's set and every canary's to its committed twin; a failure stops the launch. It prints gates and assertions only.

        uv run modal run --detach vpd_audit/modal_app.py::grid --run main --tiers 7 --subset merge_sizes
        uv run modal run --detach vpd_audit/modal_app.py::grid --run main --tiers 7 --subset panel_edit
    """
    import torch

    from vpd_audit import env
    from vpd_audit.artifacts import load_component_model
    from vpd_audit.cells import LAUNCH_SUBSETS_S12, PANEL_EVAL_SETS, SUBSETS_TIER_4, SUBSETS_TIER_5, SUBSETS_TIER_6, SUBSETS_TIER_7
    from vpd_audit.grid import GridConfig, launch_title, run_grid, summary_stem
    from vpd_audit.two_paths import check_d_b_two_paths

    tiers_t = tuple(int(t) for t in _parse_list(tiers))
    groups_t = _parse_list(groups) or None
    assert run in ("main", "control") and tiers_t and all(t in (1, 2, 3, 4, 5, 6, 7) for t in tiers_t), (run, tiers_t)
    assert not subset or subset in LAUNCH_SUBSETS_S12, f"unknown subset {subset!r}; known: {sorted(LAUNCH_SUBSETS_S12)}"
    if 4 in tiers_t:  # tier 4 runs on the main run only, one named subset per launch, alone
        assert run == "main" and tiers_t == (4,) and subset in SUBSETS_TIER_4, f"tier 4 is launched alone, on the main run, as one of {sorted(SUBSETS_TIER_4)}: got run {run!r}, tiers {tiers_t}, subset {subset!r}"
    if 5 in tiers_t:  # tier 5 likewise
        assert run == "main" and tiers_t == (5,) and subset in SUBSETS_TIER_5, f"tier 5 is launched alone, on the main run, as one of {sorted(SUBSETS_TIER_5)}: got run {run!r}, tiers {tiers_t}, subset {subset!r}"
    if 6 in tiers_t:  # tier 6 likewise
        assert run == "main" and tiers_t == (6,) and subset in SUBSETS_TIER_6, f"tier 6 is launched alone, on the main run, as one of {sorted(SUBSETS_TIER_6)}: got run {run!r}, tiers {tiers_t}, subset {subset!r}"
    if 7 in tiers_t:  # tier 7 likewise
        assert run == "main" and tiers_t == (7,) and subset in SUBSETS_TIER_7, f"tier 7 is launched alone, on the main run, as one of {sorted(SUBSETS_TIER_7)}: got run {run!r}, tiers {tiers_t}, subset {subset!r}"
    torch.use_deterministic_algorithms(True, warn_only=True)
    gpu_name = torch.cuda.get_device_name(0)
    _log(f"[modal] grid {run} tiers {tiers_t} groups {groups_t or 'all'} on {gpu_name}; torch {torch.__version__}")
    if "40GB" not in gpu_name:
        _log(f"[modal] grid: Modal placed this run on {gpu_name!r}, not a 40 GB A100; recorded, continuing")
    # the references were bitwise equal between the 40 GB and the 80 GB A100 and on no other card; a tier-4
    # launch placed elsewhere is stopped before it costs anything and relaunched, and no assertion of the analysis is ever relaxed
    assert 4 not in tiers_t or "A100" in gpu_name, f"tier 4 was placed on {gpu_name!r}, not an A100: relaunch"
    assert 5 not in tiers_t or "A100" in gpu_name, f"tier 5 was placed on {gpu_name!r}, not an A100: relaunch (its canary is bitwise against stores run on an A100)"
    assert 6 not in tiers_t or "A100" in gpu_name, f"tier 6 was placed on {gpu_name!r}, not an A100: relaunch (its canary is bitwise against stores run on an A100)"
    assert 7 not in tiers_t or "A100" in gpu_name, f"tier 7 was placed on {gpu_name!r}, not an A100: relaunch (its canaries are bitwise against stores run on an A100)"
    model = load_component_model(run, "cuda")
    out: dict = {"gpu": gpu_name, "tiers": {}}
    for tier in tiers_t:
        set_map = {"E": "E", "E_lab": "E_lab", **({p: p for p in PANEL_EVAL_SETS[run]} if tier == 7 else {})}  # tier 7: the panels are evaluation sets under their saved names
        cfg = GridConfig(run=run, set_map=set_map, pool_map={"D_unif": "D_unif", "D_code": "D_code", "D_prose": "D_prose"}, cache_tag=run, draws=draws,
                         precision="bf16", subbatch=subbatch, chunk=32, tiers=(tier,), strata_file="E_lab.strata.json", positive_stratum="Github", only_groups=groups_t,
                         job_title=launch_title(tier, subset or None), job_prefix=f"grid_{run}_t{tier}",
                         subset_name=subset or None)
        # tier 5's root is its own, beside the run's, so that analysis.load_grid never walks it; tier 6's likewise
        out_root = env.RESULTS_DIR / "grid" / run / f"tier{tier}" if tier not in (5, 6, 7) else (env.RESULTS_DIR / "grid" / f"{run}_s9" / "tier5" if tier == 5 else (env.RESULTS_DIR / "grid" / f"{run}_s11" / "tier6" if tier == 6 else env.RESULTS_DIR / "grid" / f"{run}_s12" / "tier7"))
        t5_kwargs = dict(s9_pre_reads_dir=env.RESULTS_DIR / "grid" / "pre_reads" / run / "s9", committed_roots=(env.RESULTS_DIR / "grid" / run,), require_s9=True) if tier == 5 else {}
        if tier == 6:  # the sets' twins in tiers 1 to 4 and in tier 5 (the self-merge); the self-merge's sets against the s9 label-only tables
            from vpd_audit.tier6 import committed_roots as s11_committed_roots

            t5_kwargs = dict(s9_pre_reads_dir=env.RESULTS_DIR / "grid" / "pre_reads" / run / "s9", committed_roots=s11_committed_roots(env.RESULTS_DIR, run), require_s11=True)
        if tier == 7:  # the canaries' and the panel edit's twins in tiers 1 to 5; the 2- and 4-token sets against the label-only table
            from vpd_audit.tier7 import committed_roots as s12_committed_roots

            t5_kwargs = dict(committed_roots=s12_committed_roots(env.RESULTS_DIR, run), merge_sets_dir=env.RESULTS_DIR / "grid" / "pre_reads" / run / "s12", require_s12=True)
        summary = run_grid(model, cfg, out_root, adaptive_rule_path=env.RESULTS_DIR / "grid" / run / "adaptive_rule.json", on_subbatch=_commit_every_fourth, log=_log,
                           pre_reads_manifest=env.RESULTS_DIR / "grid" / "pre_reads" / run / "manifest.json", require_pre_reads_hash=True,  # the ranking judged is the ranking erased
                           s7_pre_reads_dir=env.RESULTS_DIR / "grid" / "pre_reads" / run / "s7", **t5_kwargs)  # the tier-4 sets judged are the sets run
        volume.commit()
        # a subset launch checks and records its own stores (summary__<subset>.*), not every earlier subset's beside them
        two = check_d_b_two_paths(out_root, log=_log, summary_stem=summary_stem(subset or None), only_stores=list(summary["groups"]) if subset else None)
        volume.commit()
        out["tiers"][tier] = {"wall_clock_s": summary["wall_clock_s"], "max_memory_allocated_gb": summary["max_memory_allocated_gb"], "cells_run": summary["cells_run"], "cells_failed": summary["cells_failed"],
                              "failed_cell_types": summary["failed_cell_types"], "adaptive_rule_status": summary["adaptive_rule_status"],
                              "d_b_two_paths": {k: two[k] for k in ("n_cells_checked", "n_sequence_checks", "max_ratio", "n_over_bound", "n_nonfinite", "pass")}}
    return out


@app.function(volumes={CACHE: volume}, gpu=GPU, timeout=3600, memory=GPU_MEMORY_MIB)
def eval_caches(subbatch: int = 64, runs: str = "main,control", sets: str = "E,E_lab") -> dict:
    """Sparse caches of g on E and on E_lab for both runs, built with build_cache exactly as the donor
    caches were (bf16, sub-batch 64, chunk 32), into /cache/donors/<set>_<run>.{npz,json}, the JSON copied under
    /cache/results/data/donors/. They are read on CPU by the pre-reads and by the analysis; the loop never reads them. With
    `--runs simplestories --sets E_dry,E_lab_dry` the stand-in's, for the dry run of the analysis (its t* assert
    needs caches built on the card the dry run ran on).

        uv run modal run --detach vpd_audit/modal_app.py::eval_caches
    """
    import shutil

    import torch

    from vpd_audit import env
    from vpd_audit.artifacts import checkpoint_hashes, load_component_model
    from vpd_audit.data import load_set
    from vpd_audit.donors import build_cache, donors_dir

    torch.use_deterministic_algorithms(True, warn_only=True)
    gpu_name = torch.cuda.get_device_name(0)
    _log(f"[modal] eval_caches on {gpu_name}; torch {torch.__version__}")
    results_dir = env.RESULTS_DIR / "data" / "donors"
    results_dir.mkdir(parents=True, exist_ok=True)
    out: dict = {"gpu": gpu_name, "caches": {}}
    for run in _parse_list(runs):
        model = load_component_model(run, "cuda")
        hashes = checkpoint_hashes(run)
        for set_name in _parse_list(sets):
            ids, _, record = load_set(set_name)
            meta = build_cache(model, ids, run=run, set_name=set_name, set_hash=record["sha256_ids"], checkpoint_hashes=hashes, precision="bf16", subbatch=subbatch, log=_log)
            shutil.copy(donors_dir() / f"{set_name}_{run}.json", results_dir / f"{set_name}_{run}.json")
            out["caches"][f"{set_name}_{run}"] = {"nnz": meta["nnz"], "mean_nnz_per_position": round(meta["mean_nnz_per_position"], 2), "sha256": meta["sha256"], "bytes": meta["bytes"]}
            volume.commit()
        del model
        torch.cuda.empty_cache()
    _log(f"[modal] eval_caches: {out}")
    return out


@app.function(volumes={CACHE: volume}, gpu=GPU, timeout=2 * 3600, memory=GPU_MEMORY_MIB)
def verify(subbatch: int = 64, resume_test: bool = True) -> dict:
    """The verification launch on the paper's model (verify.py): 45 cells on E, main run, bf16,
    sub-batch 64, into /cache/results/grid/main/verify/ (and the resume store beside it); the comparisons against the
    acceptance and identities tables, the fourth cell, the never-named rung 8, the resume test, and the two-path check,
    into comparisons.{json,md}. Prints equality only for the chains.

        uv run modal run --detach vpd_audit/modal_app.py::verify
    """
    import torch

    from vpd_audit import env
    from vpd_audit.artifacts import checkpoint_hashes, load_component_model
    from vpd_audit.data import load_set
    from vpd_audit.verify import run_verify

    torch.use_deterministic_algorithms(True, warn_only=True)
    gpu_name = torch.cuda.get_device_name(0)
    _log(f"[modal] verify on {gpu_name}; torch {torch.__version__}")
    if "40GB" not in gpu_name:
        _log(f"[modal] verify: Modal placed this run on {gpu_name!r}, not a 40 GB A100; recorded, continuing")
    model = load_component_model("main", "cuda")
    ids, _, record = load_set("E")
    out_dir = env.RESULTS_DIR / "grid" / "main" / "verify"
    result = run_verify(model, ids, run="main", out_dir=out_dir, set_hash=record["sha256_ids"], checkpoint_hashes=checkpoint_hashes("main"), subbatch=subbatch, resume_test=resume_test,
                        on_subbatch=_commit_every_fourth, log=_log)
    volume.commit()
    c = result["comparisons"]
    return {"gpu": gpu_name, "seconds": result["seconds"], "references_pass": c["references_vs_acceptance"]["pass"], "chains_pass": c["chains_vs_identities"]["pass"],
            "resume_pass": result.get("resume", {}).get("pass"), "two_paths_pass": result["two_paths"]["pass"], "two_paths_max_ratio": result["two_paths"]["max_ratio"],
            "max_memory_allocated_gb": torch.cuda.max_memory_allocated() / 1e9}


@app.function(volumes={CACHE: volume}, timeout=4 * 3600, cpu=4, memory=16384)
def pre_reads(run: str = "main", draws: int = 8, dry: bool = False) -> dict:
    """The pre-reads on CPU from the caches and the sources (pre_reads.py), into
    /cache/results/grid/pre_reads/<run>/ with summary.md, the t* and sigma tables, and the manifest. With `--dry`, the
    stand-in's (run simplestories, the dry sets and caches, two draws) into /cache/results/dry_run/pre_reads/, for
    the dry run of the analysis.

        uv run modal run --detach vpd_audit/modal_app.py::pre_reads --run main
    """
    from vpd_audit import env
    from vpd_audit.pre_reads import PreReadInputs, run_pre_reads

    if dry:
        inp = PreReadInputs(run="simplestories", cache_tag="dry_simplestories", set_map={"E": "E_dry", "E_lab": "E_lab_dry"},
                            pool_map={"D_unif": "D_unif_dry", "D_code": "D_code_dry", "D_prose": "D_prose_dry"}, strata_file="E_lab_dry.strata.json", chains_dir=None,
                            draws=draws, positive_stratum="dialogue")
        out = run_pre_reads("simplestories", env.RESULTS_DIR / "dry_run" / "pre_reads", draws=draws, inputs=inp, log=_log)
    else:
        out = run_pre_reads(run, env.RESULTS_DIR / "grid" / "pre_reads" / run, draws=draws, log=_log)
    volume.commit()
    return out


@app.function(volumes={CACHE: volume}, timeout=2 * 3600, cpu=4, memory=16384)
def pre_reads_s7(run: str = "main", draws: int = 8, n_seeds: int = 200, n_shuffles: int = 200, dry: bool = False) -> dict:
    """The marginal control's label-only pre-read and the code-leaning
    table on CPU where the caches live, into /cache/results/grid/pre_reads/<run>/s7/ only; the run's
    existing pre-reads files are read (the manifest's hashes are asserted) and never written. With `--dry`, the stand-in's
    into /cache/results/dry_run/pre_reads/s7/.

        uv run modal run --detach vpd_audit/modal_app.py::pre_reads_s7 --run main
    """
    from vpd_audit import env
    from vpd_audit.pre_reads import PreReadInputs, run_pre_reads_s7

    if dry:
        inp = PreReadInputs(run="simplestories", cache_tag="dry_simplestories", set_map={"E": "E_dry", "E_lab": "E_lab_dry"},
                            pool_map={"D_unif": "D_unif_dry", "D_code": "D_code_dry", "D_prose": "D_prose_dry"}, strata_file="E_lab_dry.strata.json", chains_dir=None,
                            draws=draws, positive_stratum="dialogue")
        from vpd_audit.code_leaning import STAND_IN_GROUP, STAND_IN_WIDE

        out = run_pre_reads_s7("simplestories", env.RESULTS_DIR / "dry_run" / "pre_reads" / "s7", draws=draws, inputs=inp, n_seeds=n_seeds, n_shuffles=n_shuffles,
                               group_threshold=STAND_IN_GROUP, wide_threshold=STAND_IN_WIDE, force_chain=True, log=_log)  # the stand-in's forced group (code_leaning.py)
    else:
        out = run_pre_reads_s7(run, env.RESULTS_DIR / "grid" / "pre_reads" / run / "s7", draws=draws, n_seeds=n_seeds, n_shuffles=n_shuffles, log=_log)
    volume.commit()
    return out


@app.function(volumes={CACHE: volume}, timeout=2 * 3600, cpu=4, memory=16384)
def s9_label_tables(run: str = "main", parts: str = "checks,pre_reads", n_shuffles: int = 200) -> dict:
    """The s9 checks and tables that need the main run's label caches, on CPU where they live: check (b) and the label-only half
    of check (c) (s9_checks.run_cache_half) into /cache/results/grid/analysis/<run>/s9/, and the label-only tables for the tier-5 run (s9_pre_reads.run_s9_pre_reads)
    into /cache/results/grid/pre_reads/<run>/s9/. Both directories are new; no existing file is written. The tables are pulled
    with `modal volume get` and committed; the local `s9-checks` and `s9-pre-reads --finish` check them against the committed
    stores.

        uv run modal run --detach vpd_audit/modal_app.py::s9_label_tables
    """
    from vpd_audit import env
    from vpd_audit.s9_checks import run_cache_half
    from vpd_audit.s9_pre_reads import run_s9_pre_reads

    out: dict = {}
    wanted = _parse_list(parts)
    assert wanted and set(wanted) <= {"checks", "pre_reads"}, wanted
    if "checks" in wanted:
        out["checks"] = run_cache_half(run, env.RESULTS_DIR / "grid" / "analysis" / run / "s9", n_shuffles=n_shuffles, log=_log)
        volume.commit()
    if "pre_reads" in wanted:
        out["pre_reads"] = run_s9_pre_reads(run, env.RESULTS_DIR / "grid" / "pre_reads" / run / "s9", log=_log)
        volume.commit()
    return out


@app.function(volumes={CACHE: volume}, timeout=3600, cpu=4, memory=16384)
def s11_label_tables(run: str = "main") -> dict:
    """The tier-6 label-only checks, the part that needs the label caches, on CPU where they live: every named set of the tier-6 launch
    (and of its canary) built from the caches exactly as the launch builds them, and the labels above zero per position of E, into
    /cache/results/grid/pre_reads/<run>/s11/, a new directory. No store is read and no existing file is written. Pulled with `modal volume
    get`; the local `vpd-audit s11-label-checks --finish` holds the sets to the committed cell tables and prints the label gate.

        uv run modal run --detach vpd_audit/modal_app.py::s11_label_tables
    """
    from vpd_audit import env
    from vpd_audit.tier6 import label_tables

    assert run == "main", run
    out = label_tables(run, env.RESULTS_DIR / "grid" / "pre_reads" / run / "s11", log=_log)
    volume.commit()
    return {"n_cells": out["n_cells"], "labels": out["labels"]}


@app.function(volumes={CACHE: volume}, timeout=2 * 3600, cpu=4, memory=16384)
def s12_label_tables(run: str = "main", parts: str = "", dry: bool = False) -> dict:
    """The label-only checks of s12_labels.py, on CPU where the caches, the sets, and the labelled file live. `labels`: the merge sets at
    2 and 4 donor tokens, the code-leaning edit's erased sets, and the label it removes on the panels, into
    /cache/results/grid/pre_reads/<run>/s12/; `documents`: the panels' document index (every panel row asserted bitwise against the
    rebuilt part-C stream) into /cache/results/grid/analysis/<run>/s12/. Both directories are new; no store is read and no existing file
    is written. By default both parts on the paper's run; with `--dry` the stand-in's label tables only (the stand-in has no labelled
    file), into /cache/results/dry_run_s12/pre_reads/s12/. Pulled with `modal volume get`; the local `vpd-audit s12-label-checks
    --finish` holds the sets to the committed stores.

        uv run modal run --detach vpd_audit/modal_app.py::s12_label_tables --dry
        uv run modal run --detach vpd_audit/modal_app.py::s12_label_tables
        uv run modal run --detach vpd_audit/modal_app.py::s12_label_tables --parts agreement   (the per-batch agreement of the two document rules)
    """
    from vpd_audit import env
    from vpd_audit.s12_labels import analysis_dir, dry_inputs, label_tables, paper_inputs, panel_document_index, pre_reads_dir

    wanted = _parse_list(parts) or (("labels",) if dry else ("labels", "documents"))
    assert set(wanted) <= {"labels", "documents", "agreement"}, wanted
    assert not (dry and ("documents" in wanted or "agreement" in wanted)), "the document index has no stand-in: the stand-in has no labelled file"
    out: dict = {}
    if "agreement" in wanted:  # only when asked for: the offset rule against the end-of-text count per batch, a new file beside the document index
        from vpd_audit.s12_labels import panel_document_agreement

        got = panel_document_agreement(analysis_dir(run, env.RESULTS_DIR), log=_log)
        out["agreement"] = got["per_source"]
        volume.commit()
    if "labels" in wanted:
        inputs = dry_inputs() if dry else paper_inputs(run)
        got = label_tables(pre_reads_dir(inputs.run, env.RESULTS_DIR, dry=dry), inputs=inputs, log=_log)
        out["labels"] = {k: v for k, v in got.items() if k != "omega"}
        volume.commit()
    if "documents" in wanted:
        got = panel_document_index(analysis_dir(run, env.RESULTS_DIR), log=_log)
        out["documents"] = got["counts"].to_dict("records")
        volume.commit()
    return out


@app.function(volumes={CACHE: volume}, timeout=2 * 3600, cpu=4, memory=16384)
def s9_panels(step: str = "check", run: str = "main", n_shuffles: int = 200) -> dict:
    """Check (b)'s second pair, on random 200-row panels, on CPU where the sets and caches live. `--step prepare` writes the set `panel_Github` (the
    first 200 rows of `calib_github`) into /cache/sets/; the five panels' label caches are then built on the GPU by the existing
    `eval_caches`; `--step check` runs check (b)'s existence rule (`s9_checks.existence_pair`) on the panel pairs (s9_panels.run_panel_checks) into
    /cache/results/grid/analysis/<run>/s9b/, a new directory. No existing file is written.

        uv run modal run --detach vpd_audit/modal_app.py::s9_panels --step prepare
        uv run modal run --detach vpd_audit/modal_app.py::eval_caches --runs main --sets panel_ArXiv,panel_Wikipedia__en_,panel_Pile_CC,panel_StackExchange,panel_Github
        uv run modal run --detach vpd_audit/modal_app.py::s9_panels --step check
    """
    from vpd_audit import env
    from vpd_audit.s9_panels import S9B_DIR_NAME, prepare_panel_github, run_panel_checks

    assert step in ("prepare", "check"), step
    if step == "prepare":
        out = prepare_panel_github(log=_log)
    else:
        out = run_panel_checks(run, env.RESULTS_DIR / "grid" / "analysis" / run / S9B_DIR_NAME, n_shuffles=n_shuffles, log=_log)
    volume.commit()
    return out


@app.function(volumes={CACHE: volume}, gpu=GPU, timeout=3600, memory=GPU_MEMORY_MIB)
def residual_tests(check6_compute_s: float, budget_s: float = 180.0, override_shrink_reason: str = "") -> dict:
    """The two residual test cells on the main run, master seed 0, deterministic algorithms
    on, the model loaded once; two run_references passes into /cache/results/short_runs/ (residual_fp32: float32, the
    first 256 of E, 4 draws; residual_bf16: bf16, the first 512 of E, 2 draws), both at sub-batch 32 with the importance
    chunk 32, with the shared-mask guard on every sub-batch and draw. `check6_compute_s` is the measured GPU compute of the
    check6 launch that ran first; it enters the pre-registered shrink rule's projection against `budget_s`. A non-empty
    `override_shrink_reason` keeps the full sizes when the rule would shrink and records the rule's verdict and the
    override with that reason in residual_plan.json (added after the check6 launch alone exceeded the budget).

        uv run modal run --detach vpd_audit/modal_app.py::residual_tests --check6-compute-s <seconds> [--override-shrink-reason "..."]
    """
    import torch

    from vpd_audit.short_runs import run_residual_tests

    _log(f"[modal] residual_tests on {torch.cuda.get_device_name(0)}; torch {torch.__version__}")
    out = run_residual_tests(device="cuda", check6_compute_s=check6_compute_s, budget_s=budget_s, override_shrink_reason=override_shrink_reason or None, log=_log)
    volume.commit()
    return out


@app.function(volumes={CACHE: volume}, gpu=GPU, timeout=3600, memory=GPU_MEMORY_MIB)
def residual_matrix(n: int = 128, subbatch: int = 32, precision: str = "fp32") -> dict:
    """The residual follow-up of the residual test cells' near-zero row (cells and readings
    fixed before the run, in `residual_matrix`): sets A to E, 94 cells and 33
    footprints, on the first n sequences of E in float32 at sub-batch 32, chunk 32, deterministic algorithms on, the
    fingerprint on, the model loaded once, into /cache/results/short_runs/residual_matrix_<precision>/ with its
    summary. No card guard; the placed card is in the manifest as always.

        uv run modal run --detach vpd_audit/modal_app.py::residual_matrix
    """
    import json

    import torch

    from vpd_audit import env
    from vpd_audit.artifacts import checkpoint_hashes, load_component_model
    from vpd_audit.data import load_set
    from vpd_audit.residual_matrix import residual_matrix_summary, run_residual_matrix

    _log(f"[modal] residual_matrix on {torch.cuda.get_device_name(0)}; torch {torch.__version__}")
    model = load_component_model("main", "cuda")
    ids, _, record = load_set("E")
    out_dir = env.RESULTS_DIR / "short_runs" / f"residual_matrix_{precision}"
    run_residual_matrix(model, ids[:n], job=f"residual_matrix_{precision}", run="main", out_dir=out_dir, precision=precision, subbatch=subbatch,
                        set_name="E", set_hash=record["sha256_ids"], checkpoint_hashes=checkpoint_hashes("main"), log=_log)
    summary, text = residual_matrix_summary(out_dir, env.RESULTS_DIR / "short_runs" / "summary.json")
    with open(out_dir / "summary.json", "w") as f:
        json.dump(summary, f, indent=2, sort_keys=True)
    with open(out_dir / "summary.md", "w") as f:
        f.write(text + "\n")
    _log(text)
    _log(f"[modal] residual_matrix: peak GPU memory {torch.cuda.max_memory_allocated() / 1e9:.1f} GB")
    volume.commit()
    return {"labels": summary["labels"], "D_over_delta_sq": summary["set_A"]["D"]["ratio_to_delta_sq"], "max_memory_allocated_gb": torch.cuda.max_memory_allocated() / 1e9}


@app.function(volumes={CACHE: volume}, gpu=GPU, timeout=3600, memory=GPU_MEMORY_MIB)
def donor_caches(subbatch: int = 64) -> dict:
    """On the 40 GB card, bf16, sub-batch 64, chunk 32: the sparse donor caches of D_unif, D_code, D_prose on
    the main run (with the alive set of D_unif against the number of sequences) and of D_unif, D_code on the control
    run, into /cache/donors/; the prose-named set and f_code at tau in {0, 0.1, 0.5}; the plausible-range check
    (the target's cross-entropy on every labeled set) into /cache/results/data/labeled_ce.json; alive_vs_n.json; the
    autocast cross-entropy diagnostic on one batch of 16 of E; the cache metadata copied
    under /cache/results/data/donors/. No card guard; the placed card is in every JSON.

        uv run modal run --detach vpd_audit/modal_app.py::donor_caches
    """
    import json
    import shutil

    import torch

    from vpd_audit import env
    from vpd_audit.artifacts import checkpoint_hashes, load_component_model
    from vpd_audit.data import load_set
    from vpd_audit.donors import ALIVE_CHECKPOINTS, build_cache, ce_autocast_diagnostic, donors_dir, labeled_ce, prose_named_and_f_code

    torch.use_deterministic_algorithms(True, warn_only=True)
    gpu_name = torch.cuda.get_device_name(0)
    _log(f"[modal] donor_caches on {gpu_name}; torch {torch.__version__}")
    results_dir = env.RESULTS_DIR / "data"
    results_dir.mkdir(parents=True, exist_ok=True)
    (results_dir / "donors").mkdir(exist_ok=True)
    sets = {name: load_set(name) for name in ("D_unif", "D_code", "D_prose", "E_lab", "E_lab_github", "E_lab_other", "E")}
    metas: dict[str, dict] = {}
    out: dict = {"gpu": gpu_name}
    for run, pools in (("main", ("D_unif", "D_code", "D_prose")), ("control", ("D_unif", "D_code"))):
        model = load_component_model(run, "cuda")
        for pool in pools:
            ids, _, record = sets[pool]
            meta = build_cache(model, ids, run=run, set_name=pool, set_hash=record["sha256_ids"], checkpoint_hashes=checkpoint_hashes(run), precision="bf16", subbatch=subbatch,
                               alive_checkpoints=ALIVE_CHECKPOINTS if (pool == "D_unif" and run == "main") else None, log=_log)
            metas[f"{pool}_{run}"] = meta
            shutil.copy(donors_dir() / f"{pool}_{run}.json", results_dir / "donors" / f"{pool}_{run}.json")
            volume.commit()
        if run == "main":
            ce = labeled_ce(model, {n: sets[n][0] for n in ("D_code", "D_prose", "E_lab_github", "E_lab_other", "E_lab", "E")}, precision="bf16", subbatch=subbatch, log=_log)
            with open(results_dir / "labeled_ce.json", "w") as f:
                json.dump({"gpu": gpu_name, "run": run, "precision": "bf16", "checkpoint_hashes": checkpoint_hashes(run), "sets": ce,
                           "set_hashes": {n: sets[n][2]["sha256_ids"] for n in ce}, "rule": "mean between 1 and 5 nats and no row above 8 on every labeled set; recorded, not asserted; E beside them for reference"}, f, indent=2, sort_keys=True)
            diag = ce_autocast_diagnostic(model, sets["E"][0][:16], precision="bf16")
            diag.update({"gpu": gpu_name, "torch_version": torch.__version__, "set": "E, the first 16 sequences"})
            with open(results_dir / "ce_autocast_diagnostic.json", "w") as f:
                json.dump(diag, f, indent=2, sort_keys=True)
            _log(f"[donors] CE diagnostic: cross_entropy under autocast == nll(log_softmax bf16 -> float) bitwise: {diag['bitwise_cross_entropy_equals_bf16_log_softmax_path']}; "
                 f"== fp32 log_softmax path: {diag['bitwise_cross_entropy_equals_fp32_log_softmax_path']}; |d| to float64: {diag['abs_diff_to_ref']}")
            out["ce_diagnostic"] = {k: diag[k] for k in ("bitwise_cross_entropy_equals_bf16_log_softmax_path", "bitwise_cross_entropy_equals_fp32_log_softmax_path", "abs_diff_to_ref")}
            out["labeled_ce"] = {n: (round(v["mean"], 3), round(v["max"], 3), v["mean_in_range"] and v["no_row_above_8"]) for n, v in ce.items()}
        del model
        torch.cuda.empty_cache()
    pn = prose_named_and_f_code("D_prose_main", "D_code_main", log=_log)
    shutil.copy(donors_dir() / "prose_named_f_code_main.json", results_dir / "donors" / "prose_named_f_code_main.json")
    alive = metas["D_unif_main"]["alive"]
    with open(results_dir / "alive_vs_n.json", "w") as f:
        json.dump({"gpu": gpu_name, "run": "main", "set": "D_unif", "threshold": alive["threshold"], "by_n_sequences": alive["by_n_sequences"], "n_alive_1024": alive["n_alive"],
                   "alive_file": alive["file"], "alive_sha256": alive["sha256"], "paper_alive": {"layer_0": 3709, "layer_1": 848, "layer_2": 1943, "layer_3": 3472, "total": 9972},
                   "acceptance_run_on_E": {"64": 9393, "1024": 9947}}, f, indent=2, sort_keys=True)
    volume.commit()
    out.update({"caches": {k: (v["nnz"], round(v["mean_nnz_per_position"], 1)) for k, v in metas.items()}, "alive_by_n": {k: v["alive"]["total"] for k, v in alive["by_n_sequences"].items()},
                "prose_named": pn["n_prose_named"], "max_memory_allocated_gb": torch.cuda.max_memory_allocated() / 1e9})
    _log(f"[modal] donor_caches: {out}")
    return out


@app.function(volumes={CACHE: volume}, gpu=GPU, timeout=3600, memory=GPU_MEMORY_MIB)
def identities(subbatch: int = 64) -> dict:
    """The identities on the paper's model, 40 GB card, bf16, sub-batch 64, chunk 32, the fingerprint on: M7, M8, M9,
    M10b, M11, M14, M15, M16, H1, H2, H3 (M10a asserted throughout), with the two chains over all of E, into
    /cache/results/identities/. First, two additions: the D_prose_control cache
    (the same format and checks as the others) and the control run's alive set from its D_unif cache on CPU, saved
    beside the main run's with its hash, plus the prose-named set and f_code of the control run, and the main run's
    alive set recomputed from its cache as a consistency check. No card guard; the placed card is recorded.

        uv run modal run --detach vpd_audit/modal_app.py::identities
    """
    import json
    import shutil

    import torch

    from vpd_audit import env
    from vpd_audit.artifacts import checkpoint_hashes, load_component_model
    from vpd_audit.data import load_set
    from vpd_audit.donors import alive_from_cache, build_cache, donors_dir, prose_named_and_f_code
    from vpd_audit.identities import IdentityInputs, run_identities

    torch.use_deterministic_algorithms(True, warn_only=True)
    gpu_name = torch.cuda.get_device_name(0)
    _log(f"[modal] identities on {gpu_name}; torch {torch.__version__}")
    results = env.RESULTS_DIR / "identities"
    results.mkdir(parents=True, exist_ok=True)
    (env.RESULTS_DIR / "data" / "donors").mkdir(parents=True, exist_ok=True)
    out: dict = {"gpu": gpu_name}
    # ---- the control run's D_prose cache
    if not (donors_dir() / "D_prose_control.json").is_file():
        model_c = load_component_model("control", "cuda")
        ids, _, record = load_set("D_prose")
        meta = build_cache(model_c, ids, run="control", set_name="D_prose", set_hash=record["sha256_ids"], checkpoint_hashes=checkpoint_hashes("control"), precision="bf16", subbatch=subbatch, log=_log)
        out["D_prose_control"] = (meta["nnz"], round(meta["mean_nnz_per_position"], 1))
        del model_c
        torch.cuda.empty_cache()
        shutil.copy(donors_dir() / "D_prose_control.json", env.RESULTS_DIR / "data" / "donors" / "D_prose_control.json")
        volume.commit()
    # ---- the alive sets from the caches, the control's saved beside the main's; the prose-named set and f_code of the control
    alive_control = alive_from_cache("D_unif_control")
    alive_main_check = alive_from_cache("D_unif_main", save=False)
    pn_control = prose_named_and_f_code("D_prose_control", "D_code_control", log=_log)
    shutil.copy(donors_dir() / "prose_named_f_code_control.json", env.RESULTS_DIR / "data" / "donors" / "prose_named_f_code_control.json")
    with open(env.RESULTS_DIR / "data" / "alive_control.json", "w") as f:
        json.dump({"control": alive_control, "main_recomputed_from_cache": alive_main_check, "gpu": gpu_name}, f, indent=2, sort_keys=True)
    out["alive"] = {"control": alive_control["alive"], "main_from_cache": alive_main_check["alive"], "main_saved_vs_cache_disagreements": alive_main_check.get("saved_vector", {}).get("n_disagreements_with_cache")}
    _log(f"[identities] alive sets: control {alive_control['alive']}, main from cache {alive_main_check['alive']} (disagreements with the saved vector: {out['alive']['main_saved_vs_cache_disagreements']}); control prose-named {pn_control['n_prose_named']}")
    volume.commit()
    # ---- the identities on the main run
    inputs = IdentityInputs(run="main", cache_tag="main", eval_set="E", pool_unif="D_unif", pool_code="D_code", pool_prose="D_prose", e_lab_other="E_lab_other", precision="bf16", subbatch=subbatch, chunk=32)
    checks = run_identities(inputs, device="cuda", out_dir=results, log=_log)
    volume.commit()
    out.update({"n_pass": len([c for c in checks if c.passed is True]), "n_fail": len([c for c in checks if c.passed is False]), "n_reported": len([c for c in checks if c.passed is None]),
                "max_memory_allocated_gb": torch.cuda.max_memory_allocated() / 1e9})
    _log(f"[modal] identities: {out}")
    return out


@app.function(volumes={CACHE: volume}, gpu=GPU, timeout=3 * 3600, memory=GPU_MEMORY_MIB)
def dry_run(draws: int = 2, subbatch: int = 64, fresh: bool = True, compile_fingerprint: bool = False) -> dict:
    """The whole grid on the SimpleStories decomposition with two draws, both backgrounds, both
    thresholds, both residual settings, every rung and sub-rung, the controls, the donor-side pass, and the references,
    on the 40 GB card in bf16, into /cache/results/dry_run/. The stand-in sets (`dry_sets`) and caches are rebuilt on the volume
    first (they were built locally); the adaptive rule is computed over both draws before any cell; the peak GPU
    memory is recorded per group. Its purpose is to exercise every code path, not to learn anything about the
    decomposition. After the grid, the two-path check of the conditional damage; with
    `--compile-fingerprint` the fingerprint's slab runs compiled (the digest gate of `timing --compile-fingerprint`), recorded in the summary.

        uv run modal run --detach vpd_audit/modal_app.py::dry_run
    """
    import json

    import torch

    if compile_fingerprint:
        from vpd_audit.fingerprint import enable_compile

        enable_compile(True)

    from vpd_audit import env
    from vpd_audit.artifacts import checkpoint_hashes, load_component_model
    from vpd_audit.data import load_set
    from vpd_audit.donors import alive_from_cache, build_cache, donors_dir, prose_named_and_f_code
    from vpd_audit.dry_sets import prepare_dry_sets
    from vpd_audit.grid import GridConfig, run_grid

    torch.use_deterministic_algorithms(True, warn_only=True)
    gpu_name = torch.cuda.get_device_name(0)
    _log(f"[modal] dry_run on {gpu_name}; torch {torch.__version__}")
    if not (env.SETS_DIR / "dry_manifest.json").is_file():
        prepare_dry_sets(log=_log)
        volume.commit()
    model = load_component_model("simplestories", "cuda")
    hashes = checkpoint_hashes("simplestories")
    for pool in ("D_unif_dry", "D_code_dry", "D_prose_dry"):
        if not (donors_dir() / f"{pool}_simplestories.json").is_file():
            ids, _, record = load_set(pool)
            build_cache(model, ids, run="simplestories", set_name=pool, set_hash=record["sha256_ids"], checkpoint_hashes=hashes, precision="bf16", subbatch=subbatch,
                        alive_checkpoints=(64, 128) if pool == "D_unif_dry" else None, log=_log)
    if not (donors_dir() / "alive_D_unif_dry_simplestories.npy").is_file():
        alive_from_cache("D_unif_dry_simplestories")
    if not (donors_dir() / "prose_named_f_code_dry_simplestories.json").is_file():
        prose_named_and_f_code("D_prose_dry_simplestories", "D_code_dry_simplestories", log=_log)
    volume.commit()
    cfg = GridConfig(run="simplestories", set_map={"E": "E_dry", "E_lab": "E_lab_dry"}, pool_map={"D_unif": "D_unif_dry", "D_code": "D_code_dry", "D_prose": "D_prose_dry"},
                     cache_tag="dry_simplestories", draws=draws, precision="bf16", subbatch=subbatch, chunk=32)
    out_root = env.RESULTS_DIR / "dry_run"
    if fresh and out_root.exists():
        # an earlier attempt is moved aside (renamed, never deleted) so that the new one runs whole and its wall clock is the grid's;
        # the stand-in's pre-reads and analysis stay in place (a launch with ranked cells asserts its
        # weight-norm hash against the pre-reads manifest, so the pre-reads must exist before the grid, as on the paper's runs)
        n = 1
        while (out_root.parent / f"dry_run.attempt{n}").exists():
            n += 1
        aside = out_root.parent / f"dry_run.attempt{n}"
        aside.mkdir()
        kept = ("pre_reads", "analysis")
        for child in sorted(out_root.iterdir()):
            if child.name not in kept:
                child.rename(aside / child.name)
        _log(f"[modal] moved the earlier results/dry_run aside to results/dry_run.attempt{n} ({', '.join(k for k in kept if (out_root / k).exists()) or 'nothing'} kept in place)")
    summary = run_grid(model, cfg, out_root, log=_log, pre_reads_manifest=env.RESULTS_DIR / "dry_run" / "pre_reads" / "manifest.json", require_pre_reads_hash=False)
    volume.commit()
    # the conditional damage recomputed from the float16 arrays and compared with the columns
    from vpd_audit.two_paths import check_d_b_two_paths

    two = check_d_b_two_paths(out_root, log=_log)
    # the level cells' corner check on the E group's first sub-batch, against the store's rows
    from vpd_audit.level_check import level_corner_check
    from vpd_audit.sources import Cache, union_source

    d_unif = Cache.load("D_unif_dry_simplestories")
    alive_set = union_source(d_unif, range(d_unif.n_positions), 0.1)
    ids_e, _, _ = load_set("E_dry")
    corner = level_corner_check(model, ids_e, alive_set, run="simplestories", precision="bf16", subbatch=subbatch, chunk=32, store_dir=out_root / "E", log=_log)
    with open(out_root / "summary.json") as f:
        s_ = json.load(f)
    s_["level_corner_check"] = corner
    with open(out_root / "summary.json", "w") as f:
        json.dump(s_, f, indent=2, sort_keys=True, default=str)
    compile_info: dict = {"enabled": compile_fingerprint}
    if compile_fingerprint:
        from vpd_audit.fingerprint import COMPILE

        compile_info.update({"calls": COMPILE["calls"], "compiles": COMPILE["compiles"], "live": COMPILE["calls"] > 0})
        with open(out_root / "summary.json") as f:
            s = json.load(f)
        s["compile_fingerprint"] = compile_info
        with open(out_root / "summary.json", "w") as f:
            json.dump(s, f, indent=2, sort_keys=True, default=str)
        _log(f"[modal] dry_run: compiled fingerprint slab, {COMPILE['calls']} compiled slab calls, {COMPILE['compiles']} compilations")
    volume.commit()
    return {"gpu": gpu_name, "wall_clock_s": summary["wall_clock_s"], "max_memory_allocated_gb": summary["max_memory_allocated_gb"], "cells_run": summary["cells_run"], "cells_failed": summary["cells_failed"],
            "failed_cell_types": summary["failed_cell_types"], "preconditions": {k: (v.get("n_pass"), v.get("n")) if isinstance(v, dict) and "n_pass" in v else None for k, v in summary["preconditions"].items()},
            "d_b_two_paths": {k: two[k] for k in ("n_cells_checked", "n_sequence_checks", "max_ratio", "n_over_bound", "pass")}, "compile_fingerprint": compile_info,
            "level_corner_check": {"pass": corner["pass"], "n_sequences": corner["n_sequences"]}}


@app.function(volumes={CACHE: volume}, gpu=GPU, timeout=3600, memory=GPU_MEMORY_MIB)
def dry_run_s7(draws: int = 2, subbatch: int = 64) -> dict:
    """The dry run of tier 4 on the SimpleStories stand-in, two draws, on the 40 GB card in bf16, as
    tier 4's two launch subsets (`marginal` with its canaries, `code_leaning`), into /cache/results/dry_run_s7/tier4/, a
    root of its own: the stand-in's existing stores under /cache/results/dry_run/ are read (the adaptive rule is asserted
    against theirs) and never written. The stand-in's existence rule finds no code-leaning group, so its chain is the forced
    one of code_leaning.STAND_IN_GROUP and STAND_IN_WIDE, as in its s7 pre-read, which must exist
    (`pre_reads_s7 --dry`): every tier-4 set is asserted equal to the set that pre-read judged. After each subset, the
    two-path check of the conditional damage on its stores.

        uv run modal run --detach vpd_audit/modal_app.py::dry_run_s7
    """
    import torch

    from vpd_audit import env
    from vpd_audit.artifacts import load_component_model
    from vpd_audit.code_leaning import STAND_IN_GROUP, STAND_IN_WIDE
    from vpd_audit.grid import GridConfig, run_grid, summary_stem
    from vpd_audit.two_paths import check_d_b_two_paths

    torch.use_deterministic_algorithms(True, warn_only=True)
    gpu_name = torch.cuda.get_device_name(0)
    _log(f"[modal] dry_run_s7 on {gpu_name}; torch {torch.__version__}")
    model = load_component_model("simplestories", "cuda")
    out_root = env.RESULTS_DIR / "dry_run_s7" / "tier4"
    out: dict = {"gpu": gpu_name, "subsets": {}}
    for subset in ("marginal", "code_leaning"):
        cfg = GridConfig(run="simplestories", set_map={"E": "E_dry", "E_lab": "E_lab_dry"}, pool_map={"D_unif": "D_unif_dry", "D_code": "D_code_dry", "D_prose": "D_prose_dry"},
                         cache_tag="dry_simplestories", draws=draws, precision="bf16", subbatch=subbatch, chunk=32, tiers=(4,), subset_name=subset, job_prefix="dry_s7",
                         job_title=f"The dry run of tier 4, the {subset} subset", code_leaning_group=STAND_IN_GROUP, code_leaning_wide=STAND_IN_WIDE, code_leaning_force=True)
        summary = run_grid(model, cfg, out_root, adaptive_rule_path=env.RESULTS_DIR / "dry_run" / "adaptive_rule.json", on_subbatch=_commit_every_fourth, log=_log,
                           pre_reads_manifest=env.RESULTS_DIR / "dry_run" / "pre_reads" / "manifest.json", require_pre_reads_hash=False, s7_pre_reads_dir=env.RESULTS_DIR / "dry_run" / "pre_reads" / "s7")
        volume.commit()
        two = check_d_b_two_paths(out_root, log=_log, summary_stem=summary_stem(subset), only_stores=list(summary["groups"]))
        volume.commit()
        out["subsets"][subset] = {"wall_clock_s": summary["wall_clock_s"], "cells_run": summary["cells_run"], "cells_failed": summary["cells_failed"], "failed_cell_types": summary["failed_cell_types"],
                                  "tier_4_vs_s7_pre_reads": summary["tier_4_vs_s7_pre_reads"], "d_b_two_paths": {k: two[k] for k in ("n_cells_checked", "n_sequence_checks", "max_ratio", "pass")}}
    return out


@app.function(volumes={CACHE: volume}, gpu=GPU, timeout=3600, memory=GPU_MEMORY_MIB)
def dry_run_s12(draws: int = 2, subbatch: int = 64, fresh: bool = True) -> dict:
    """The dry run of tier 7 on the SimpleStories stand-in, two draws, on the 40 GB card in bf16, as its two launch subsets in their launch
    order (`merge_sizes`, then `panel_edit`), into /cache/results/dry_run_s12/tier7/, a root of its own. First the stand-in's panels
    (`tier7.prepare_stand_in_panels`: disjoint 200-row slices of its rows, written once). The stand-in's committed stores under
    /cache/results/dry_run, dry_run_s7, and dry_run_s9 are read and never written: they hold the canaries' and the panel edit's twins, and
    its label-only table of the merge sets (/cache/results/dry_run_s12/pre_reads/s12/merge_sets.csv) holds the 2- and 4-token sets; every
    set is held to them before any forward pass. Its code-leaning chain is the forced one of its code-leaning pre-read (results/dry_run/pre_reads/s7). With `fresh`, an
    earlier attempt's stores are moved aside (renamed, never deleted). After each subset, the two-path check of the conditional damage.

        uv run modal run --detach vpd_audit/modal_app.py::dry_run_s12
    """
    import torch

    from vpd_audit import env
    from vpd_audit.artifacts import load_component_model
    from vpd_audit.code_leaning import STAND_IN_GROUP, STAND_IN_WIDE
    from vpd_audit.grid import GridConfig, run_grid, summary_stem
    from vpd_audit.tier7 import committed_roots, prepare_stand_in_panels, stand_in_set_map
    from vpd_audit.two_paths import check_d_b_two_paths

    torch.use_deterministic_algorithms(True, warn_only=True)
    gpu_name = torch.cuda.get_device_name(0)
    _log(f"[modal] dry_run_s12 on {gpu_name}; torch {torch.__version__}")
    assert "A100" in gpu_name, f"dry_run_s12 was placed on {gpu_name!r}, not an A100: relaunch (its canaries are bitwise against stores run on an A100)"
    roots = committed_roots(env.RESULTS_DIR, "simplestories")
    for r in roots:
        assert r.is_dir(), f"the stand-in's committed stores are not on the volume at {r}"
    panels = prepare_stand_in_panels(log=_log)
    volume.commit()
    out_root = env.RESULTS_DIR / "dry_run_s12" / "tier7"
    if fresh and out_root.exists():
        n = 1
        while (out_root.parent / f"tier7.attempt{n}").exists():
            n += 1
        out_root.rename(out_root.parent / f"tier7.attempt{n}")
        _log(f"[modal] moved the earlier results/dry_run_s12/tier7 aside to tier7.attempt{n}")
    model = load_component_model("simplestories", "cuda")
    out: dict = {"gpu": gpu_name, "stand_in_panels": panels, "subsets": {}}
    for subset in ("merge_sizes", "panel_edit"):
        cfg = GridConfig(run="simplestories", set_map={"E": "E_dry", "E_lab": "E_lab_dry", **stand_in_set_map()}, pool_map={"D_unif": "D_unif_dry", "D_code": "D_code_dry", "D_prose": "D_prose_dry"},
                         cache_tag="dry_simplestories", draws=draws, precision="bf16", subbatch=subbatch, chunk=32, tiers=(7,), subset_name=subset, job_prefix="dry_s12",
                         job_title=f"The dry run of tier 7, the {subset} subset", code_leaning_group=STAND_IN_GROUP, code_leaning_wide=STAND_IN_WIDE, code_leaning_force=True)
        summary = run_grid(model, cfg, out_root, adaptive_rule_path=env.RESULTS_DIR / "dry_run" / "adaptive_rule.json", on_subbatch=_commit_every_fourth, log=_log,
                           pre_reads_manifest=env.RESULTS_DIR / "dry_run" / "pre_reads" / "manifest.json", require_pre_reads_hash=False, s7_pre_reads_dir=env.RESULTS_DIR / "dry_run" / "pre_reads" / "s7",
                           committed_roots=roots, merge_sets_dir=env.RESULTS_DIR / "dry_run_s12" / "pre_reads" / "s12", require_s12=True)
        volume.commit()
        two = check_d_b_two_paths(out_root, log=_log, summary_stem=summary_stem(subset), only_stores=list(summary["groups"]))
        volume.commit()
        out["subsets"][subset] = {"wall_clock_s": summary["wall_clock_s"], "cells_run": summary["cells_run"], "cells_failed": summary["cells_failed"], "failed_cell_types": summary["failed_cell_types"],
                                  "tier_7": summary.get("tier_7"), "d_b_two_paths": {k: two[k] for k in ("n_cells_checked", "n_sequence_checks", "max_ratio", "pass")}}
    return out


@app.function(volumes={CACHE: volume}, gpu=GPU, timeout=3600, memory=GPU_MEMORY_MIB)
def dry_run_s9(draws: int = 2, subbatch: int = 64, document_rows: int = 3, fresh: bool = True) -> dict:
    """The dry run of tier 5 on the SimpleStories stand-in, two draws, on the 40 GB card in bf16, as
    tier 5's three launch subsets in their launch order (`plain_terms` first, then `same_domain`, `self_merge`), into
    /cache/results/dry_run_s9/tier5/, a root of its own: the stand-in's existing stores under /cache/results/dry_run/ and
    /cache/results/dry_run_s7/ are read and never written. They are the other side of the bitwise canary and of the D_unif gate
    (`committed_roots`), so this run is also the test of the canary on the A100 before any paid pass of the paper's model: every
    reference and every re-run cell must reproduce its committed per-text kl_mean bitwise on every sub-batch, or the run stops.

    First, on CPU in the same container, the stand-in's s9 label-only tables (`s9_pre_reads.run_s9_pre_reads`, a few
    seconds) into /cache/results/dry_run/pre_reads/s9/, a directory of their own, from the volume's bf16 caches: every tier-5 set
    is asserted against them by hash before any forward pass. The stand-in's documents are blocks of `document_rows` rows
    (analysis_s9.STAND_IN_DOCUMENT_ROWS: three, so that each of its two sources of 32 rows has at least ten documents, of unequal
    size, and the analysis' document intervals exist); the same value goes to the pre-read, the launch, and the analysis. Its
    code-leaning chain is the forced one of its s7 pre-read, which must exist (`pre_reads_s7 --dry`). With `fresh`, an
    earlier attempt's stores are moved aside (renamed, never deleted). After each subset, the two-path check of the conditional
    damage on its stores. The stand-in has another tokenizer, so no comparison model runs (the fake-model test in tests/test_tier5.py covers them).

        uv run modal run --detach vpd_audit/modal_app.py::dry_run_s9
    """
    import dataclasses

    import torch

    from vpd_audit import env
    from vpd_audit.artifacts import load_component_model
    from vpd_audit.code_leaning import STAND_IN_GROUP, STAND_IN_WIDE
    from vpd_audit.grid import GridConfig, run_grid, summary_stem
    from vpd_audit.s9_checks import dry_inputs
    from vpd_audit.s9_pre_reads import run_s9_pre_reads
    from vpd_audit.two_paths import check_d_b_two_paths

    torch.use_deterministic_algorithms(True, warn_only=True)
    gpu_name = torch.cuda.get_device_name(0)
    _log(f"[modal] dry_run_s9 on {gpu_name}; torch {torch.__version__}")
    assert "A100" in gpu_name, f"dry_run_s9 was placed on {gpu_name!r}, not an A100: relaunch (its canary is bitwise against stores run on an A100)"
    committed_roots = (env.RESULTS_DIR / "dry_run", env.RESULTS_DIR / "dry_run_s7")
    for r in committed_roots:
        assert r.is_dir(), f"the stand-in's committed stores are not on the volume at {r}"
    s9_dir = env.RESULTS_DIR / "dry_run" / "pre_reads" / "s9"
    pre = run_s9_pre_reads("simplestories", s9_dir, inputs=dataclasses.replace(dry_inputs(draws=draws), synthetic_document_rows=document_rows), log=_log)
    volume.commit()
    out_root = env.RESULTS_DIR / "dry_run_s9" / "tier5"
    if fresh and out_root.exists():
        n = 1
        while (out_root.parent / f"tier5.attempt{n}").exists():
            n += 1
        out_root.rename(out_root.parent / f"tier5.attempt{n}")
        _log(f"[modal] moved the earlier results/dry_run_s9/tier5 aside to tier5.attempt{n}")
    model = load_component_model("simplestories", "cuda")
    out: dict = {"gpu": gpu_name, "document_rows": document_rows, "s9_pre_reads": {k: pre[k] for k in ("seconds",) if k in pre}, "subsets": {}}
    for subset in ("plain_terms", "same_domain", "self_merge"):
        cfg = GridConfig(run="simplestories", set_map={"E": "E_dry", "E_lab": "E_lab_dry"}, pool_map={"D_unif": "D_unif_dry", "D_code": "D_code_dry", "D_prose": "D_prose_dry"},
                         cache_tag="dry_simplestories", draws=draws, precision="bf16", subbatch=subbatch, chunk=32, tiers=(5,), subset_name=subset, job_prefix="dry_s9",
                         job_title=f"The dry run of tier 5, the {subset} subset", code_leaning_group=STAND_IN_GROUP, code_leaning_wide=STAND_IN_WIDE, code_leaning_force=True,
                         synthetic_document_rows=document_rows)
        summary = run_grid(model, cfg, out_root, adaptive_rule_path=env.RESULTS_DIR / "dry_run" / "adaptive_rule.json", on_subbatch=_commit_every_fourth, log=_log,
                           pre_reads_manifest=env.RESULTS_DIR / "dry_run" / "pre_reads" / "manifest.json", require_pre_reads_hash=False, s7_pre_reads_dir=env.RESULTS_DIR / "dry_run" / "pre_reads" / "s7",
                           s9_pre_reads_dir=s9_dir, committed_roots=committed_roots, require_s9=False)
        volume.commit()
        assert summary["cells_failed"] == 0, f"{subset}: {summary['failures']}"
        checks = summary["tier_5"]["checks"]
        assert all(v is not None and v["canary_pass"] for v in checks.values()), f"{subset}: a store ran without its canary: {checks}"  # a failed canary has already stopped the run (GateFailure)
        two = check_d_b_two_paths(out_root, log=_log, summary_stem=summary_stem(subset), only_stores=list(summary["groups"]))
        volume.commit()
        out["subsets"][subset] = {"wall_clock_s": summary["wall_clock_s"], "max_memory_allocated_gb": summary["max_memory_allocated_gb"], "cells_run": summary["cells_run"], "cells_failed": summary["cells_failed"],
                                  "tier_5_vs_s9_pre_reads": summary["tier_5_vs_s9_pre_reads"].get("counts"), "canary": {k: {x: v[x] for x in ("canary_cells", "canary_pairs_compared", "canary_pass")} for k, v in checks.items()},
                                  "d_unif_gate": {k: v["d_unif_gate"] for k, v in checks.items() if "d_unif_gate" in v}, "d_b_two_paths": {k: two[k] for k in ("n_cells_checked", "n_sequence_checks", "max_ratio", "pass")}}
    return out


@app.function(volumes={CACHE: volume}, gpu=GPU, timeout=3600, memory=GPU_MEMORY_MIB)
def h4(n_sequences: int = 128) -> dict:
    """The cross-check cell H4: the first 128 sequences of E, the main run, float32, the
    residual excluded, one sequence at a time: (a) the authors' edit forward with every subcomponent no position of
    D_unif names above tau = 0.1 set to 0, (b) our hard-zero mask of that set, (c) our union rung-8 cell; the readings
    are stated in vpd_audit/h4.py before the run. Into /cache/results/identities/h4_main.{json,txt}. The card is recorded.

        uv run modal run --detach vpd_audit/modal_app.py::h4
    """
    import torch

    from vpd_audit import env
    from vpd_audit.h4 import run_h4

    gpu_name = torch.cuda.get_device_name(0)
    _log(f"[modal] h4 on {gpu_name}; torch {torch.__version__}")
    out = run_h4(run="main", eval_set="E", pool="D_unif", n_sequences=n_sequences, tau=0.1, device="cuda", out_dir=env.RESULTS_DIR / "identities", precision="fp32", log=_log)
    volume.commit()
    return {"gpu": gpu_name, "mean_kl": out["mean_kl"], "max_abs_logit_diff_a_b": out["max_abs_logit_diff_a_b"]["max_over_sequences"], "kl_c_minus_b_mean": out["kl_c_minus_b"]["mean"],
            "reading": out["reading"], "seconds": out["seconds"], "max_memory_allocated_gb": torch.cuda.max_memory_allocated() / 1e9}


@app.function(volumes={CACHE: volume}, gpu=GPU, timeout=3600, memory=GPU_MEMORY_MIB)
def check6(precision: str = "bf16", check6_batch: int = 32, check6_n_batches: int = 4) -> dict:
    """Check 6 at matched shapes, its own launch. The authors' CEandKLLosses (one instance per batch,
    driven exactly as their `evaluate` drives it) at `check6_batch` x `check6_n_batches` on the first
    check6_batch * check6_n_batches sequences of E under `precision` at thresholds 0, 0.1, 0.5, tried once; on an
    out-of-memory error, half the batch and twice the batches on the same sequences (recorded), never a larger card.
    Then our path on the same sequences at sub-batch and importance chunk equal to the class's batch, and the three
    comparisons into /cache/results/short_runs/check6_<precision>/ (authors_metric_<precision>.json, checks_<precision>.txt).

        uv run modal run --detach vpd_audit/modal_app.py::check6 --precision bf16 --check6-batch 32 --check6-n-batches 4
    """
    import torch

    from vpd_audit.short_runs import run_check6_matched

    _log(f"[modal] check6 ({precision}) on {torch.cuda.get_device_name(0)}; torch {torch.__version__}")
    out = run_check6_matched(device="cuda", precision=precision, class_batch=check6_batch, n_batches=check6_n_batches, log=_log)
    volume.commit()
    return out
