"""Artifacts: the one-time fetch with the WandB key, the artifact directory and manifest,
and the key-free loader.

Layout, keyed on run id because the main and control decompositions ship under one name:

    <cache>/artifacts/
      s-55ea3f9b/   model_400000.pth  final_config.yaml          main decomposition
      s-05ef623e/   model_400000.pth  final_config.yaml          control (no adversarial loss)
      t-9d2b8f02/   final_config.yaml model_config.yaml ckpt/model_step_99999.pt   paper target
      s-eab2ace8/   model_400000.pth  final_config.yaml          SimpleStories 2-layer decomposition
      gf6rbga0/     final_config.yaml model_config.yaml [tokenizer.json] ckpt/model_step_<N>.pt
      manifest.json                                               bytes and SHA-256 of every file

The WandB key is read only inside `fetch_artifacts`, is never printed, and is never written
anywhere. Loading needs no key: both loaders take their local branches on absolute paths.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import time
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Any

from vpd_audit import env

if TYPE_CHECKING:
    from param_decomp.models.component_model import ComponentModel

WANDB_PROJECT = "goodfire/spd"
MANIFEST_NAME = "manifest.json"
DECOMP_CHECKPOINT = "model_400000.pth"
DECOMP_FILES = (DECOMP_CHECKPOINT, "final_config.yaml")
TARGET_FILES = ("final_config.yaml", "model_config.yaml")
TARGET_OPTIONAL_FILES = ("tokenizer.json",)
STEP_RE = re.compile(r"^model_step_(\d+)\.pt$")


@dataclass(frozen=True)
class WandbRunSpec:
    run_id: str
    kind: str  # "decomp" or "target"
    description: str
    approx_gb: float


RUN_SPECS: dict[str, WandbRunSpec] = {
    "s-eab2ace8": WandbRunSpec("s-eab2ace8", "decomp", "SimpleStories two-layer decomposition", 0.10),
    "gf6rbga0": WandbRunSpec("gf6rbga0", "target", "SimpleStories target model", 0.05),
    "t-9d2b8f02": WandbRunSpec("t-9d2b8f02", "target", "the paper's target model", 0.27),
    "s-55ea3f9b": WandbRunSpec("s-55ea3f9b", "decomp", "the main decomposition", 2.91),
    "s-05ef623e": WandbRunSpec("s-05ef623e", "decomp", "the control without the adversarial loss", 2.91),
}
ALL_RUN_IDS: tuple[str, ...] = tuple(RUN_SPECS)
LOCAL_RUN_IDS: tuple[str, ...] = ("s-eab2ace8", "gf6rbga0", "t-9d2b8f02", "s-55ea3f9b")


@dataclass(frozen=True)
class AuditRun:
    """One decomposition paired with its target, as the harness names them."""

    name: str
    decomp_run: str
    target_run: str
    n_matrices: int | None  # asserted after load when not None
    n_subcomponents: int | None
    target_step: int | None  # asserted when not None; else the largest step in ckpt/


AUDIT_RUNS: dict[str, AuditRun] = {
    "main": AuditRun("main", "s-55ea3f9b", "t-9d2b8f02", 24, 38_912, 99_999),
    "control": AuditRun("control", "s-05ef623e", "t-9d2b8f02", 24, 38_912, 99_999),
    "simplestories": AuditRun("simplestories", "s-eab2ace8", "gf6rbga0", None, None, None),
}


# ----------------------------------------------------------------------------- hashing


def sha256_file(path: Path, chunk_bytes: int = 1 << 23) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while True:
            block = f.read(chunk_bytes)
            if not block:
                break
            h.update(block)
    return h.hexdigest()


def _atomic_write_json(path: Path, obj: Any) -> None:
    tmp = path.with_suffix(path.suffix + ".tmp")
    with open(tmp, "w") as f:
        json.dump(obj, f, indent=2, sort_keys=True)
    os.replace(tmp, path)


def read_manifest(art_dir: Path = env.ARTIFACTS_DIR) -> dict[str, Any]:
    path = art_dir / MANIFEST_NAME
    if not path.is_file():
        raise FileNotFoundError(f"no artifact manifest at {path}; run `vpd-audit fetch` first")
    with open(path) as f:
        return json.load(f)


def _run_files_on_disk(run_dir: Path) -> list[Path]:
    return sorted(p for p in run_dir.rglob("*") if p.is_file() and not p.name.endswith(".tmp"))


def write_manifest(art_dir: Path, run_ids: list[str]) -> dict[str, Any]:
    """Hash every file of the given runs into the manifest, merging with an existing one."""
    manifest: dict[str, Any] = {"wandb_project": WANDB_PROJECT, "files": {}, "runs": {}}
    if (art_dir / MANIFEST_NAME).is_file():
        manifest = read_manifest(art_dir)
    for run_id in run_ids:
        run_dir = art_dir / run_id
        files = _run_files_on_disk(run_dir)
        assert files, f"no files under {run_dir}"
        # drop stale entries for this run, then re-hash
        manifest["files"] = {k: v for k, v in manifest["files"].items() if not k.startswith(run_id + "/")}
        rel_names = []
        for p in files:
            rel = f"{run_id}/{p.relative_to(run_dir).as_posix()}"
            manifest["files"][rel] = {"bytes": p.stat().st_size, "sha256": sha256_file(p)}
            rel_names.append(rel)
        manifest["runs"][run_id] = {
            "kind": RUN_SPECS[run_id].kind,
            "description": RUN_SPECS[run_id].description,
            "files": rel_names,
            "fetched_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        }
    _atomic_write_json(art_dir / MANIFEST_NAME, manifest)
    return manifest


def verify_manifest(art_dir: Path = env.ARTIFACTS_DIR, run_ids: list[str] | None = None) -> list[str]:
    """Recompute byte sizes and SHA-256 of every manifest file of the given runs (all if None).

    Raises on a missing file, a size mismatch, a hash mismatch, or a run absent from the manifest.
    Returns the verified relative paths.
    """
    manifest = read_manifest(art_dir)
    if run_ids is None:
        run_ids = list(manifest["runs"])
    verified: list[str] = []
    for run_id in run_ids:
        if run_id not in manifest["runs"]:
            raise RuntimeError(f"run {run_id} is not in the artifact manifest at {art_dir}")
        for rel in manifest["runs"][run_id]["files"]:
            entry = manifest["files"][rel]
            path = art_dir / rel
            if not path.is_file():
                raise RuntimeError(f"manifest file missing on disk: {path}")
            size = path.stat().st_size
            if size != entry["bytes"]:
                raise RuntimeError(f"size mismatch for {rel}: {size} on disk, {entry['bytes']} in manifest")
            digest = sha256_file(path)
            if digest != entry["sha256"]:
                raise RuntimeError(f"sha256 mismatch for {rel}: {digest} on disk, {entry['sha256']} in manifest")
            verified.append(rel)
    return verified


# ----------------------------------------------------------------------------- fetch


def _wandb_api_key() -> str:
    """The key from the environment (the Modal secret) or from <project>/.env. Never printed."""
    key = os.environ.get("WANDB_API_KEY")
    if not key:
        from dotenv import dotenv_values

        key = dotenv_values(env.PROJECT_ROOT / ".env").get("WANDB_API_KEY")
    if not key:
        raise RuntimeError("WANDB_API_KEY is neither in the environment nor in <project>/.env")
    return key


def _download(file_obj: Any, dest: Path, *, replace: bool) -> str:
    """Download one WandB file object to `dest`. Returns 'skipped' or 'downloaded'."""
    if dest.is_file() and not replace and dest.stat().st_size == int(file_obj.size):
        return "skipped"
    dest.parent.mkdir(parents=True, exist_ok=True)
    scratch = dest.parent / f"_dl_{dest.name}"
    if scratch.exists():
        shutil.rmtree(scratch)
    scratch.mkdir()
    file_obj.download(root=str(scratch), replace=True)
    downloaded = scratch / file_obj.name
    assert downloaded.is_file(), f"download of {file_obj.name} did not produce {downloaded}"
    os.replace(downloaded, dest)
    shutil.rmtree(scratch)
    return "downloaded"


def fetch_artifacts(
    run_ids: list[str] | None = None,
    art_dir: Path = env.ARTIFACTS_DIR,
    *,
    replace: bool = False,
    log: Any = print,
) -> dict[str, Any]:
    """Fetch the runs' files from goodfire/spd into the layout above and write the manifest.

    Defaults to the four runs needed locally; the control (`s-05ef623e`) is fetched when named.
    """
    import wandb

    run_ids = list(run_ids or LOCAL_RUN_IDS)
    for run_id in run_ids:
        assert run_id in RUN_SPECS, f"unknown run {run_id}; known: {ALL_RUN_IDS}"
    art_dir.mkdir(parents=True, exist_ok=True)

    api = wandb.Api(api_key=_wandb_api_key())  # the key is used here and nowhere else
    for run_id in run_ids:
        spec = RUN_SPECS[run_id]
        run_dir = art_dir / run_id
        run_dir.mkdir(parents=True, exist_ok=True)
        t0 = time.time()
        run = api.run(f"{WANDB_PROJECT}/{run_id}")
        files = {f.name: f for f in run.files()}
        log(f"[fetch] {run_id} ({spec.description}): {len(files)} files listed")
        wanted: list[tuple[Any, Path]] = []
        if spec.kind == "decomp":
            for name in DECOMP_FILES:
                assert name in files, f"{run_id}: expected file {name!r}; have {sorted(files)}"
                wanted.append((files[name], run_dir / name))
        else:
            for name in TARGET_FILES:
                assert name in files, f"{run_id}: expected file {name!r}; have {sorted(files)}"
                wanted.append((files[name], run_dir / name))
            for name in TARGET_OPTIONAL_FILES:
                if name in files:
                    wanted.append((files[name], run_dir / name))
            steps = sorted((int(m.group(1)), n) for n in files if (m := STEP_RE.match(n)))
            assert steps, f"{run_id}: no model_step_<N>.pt among {sorted(files)}"
            step, name = steps[-1]
            wanted.append((files[name], run_dir / "ckpt" / name))
            log(f"[fetch] {run_id}: largest checkpoint step {step} -> ckpt/{name}")
        for f, dest in wanted:
            status = _download(f, dest, replace=replace)
            log(f"[fetch] {run_id}: {status} {dest.relative_to(art_dir)} ({int(f.size) / 1e6:.1f} MB)")
        log(f"[fetch] {run_id}: done in {time.time() - t0:.1f} s")

    manifest = write_manifest(art_dir, run_ids)
    verify_manifest(art_dir, run_ids)
    log(f"[fetch] manifest written and verified: {art_dir / MANIFEST_NAME}")
    return manifest


# ----------------------------------------------------------------------------- load


def decomp_checkpoint_path(run: str, art_dir: Path = env.ARTIFACTS_DIR) -> Path:
    return (art_dir / AUDIT_RUNS[run].decomp_run / DECOMP_CHECKPOINT).resolve()


def target_checkpoint_path(run: str, art_dir: Path = env.ARTIFACTS_DIR) -> Path:
    spec = AUDIT_RUNS[run]
    ckpt_dir = art_dir / spec.target_run / "ckpt"
    steps = sorted((int(m.group(1)), p) for p in ckpt_dir.glob("model_step_*.pt") if (m := STEP_RE.match(p.name)))
    assert steps, f"no model_step_<N>.pt under {ckpt_dir}"
    step, path = steps[-1]
    if spec.target_step is not None:
        assert step == spec.target_step, f"{run}: target checkpoint step {step}, expected {spec.target_step}"
    return path.resolve()


def checkpoint_hashes(run: str, art_dir: Path = env.ARTIFACTS_DIR) -> dict[str, str]:
    """The manifest's SHA-256 of the decomposition and target checkpoints, for result provenance."""
    manifest = read_manifest(art_dir)
    d = decomp_checkpoint_path(run, art_dir).relative_to(art_dir.resolve()).as_posix()
    t = target_checkpoint_path(run, art_dir).relative_to(art_dir.resolve()).as_posix()
    return {"decomp": manifest["files"][d]["sha256"], "target": manifest["files"][t]["sha256"]}


def load_component_model(run: str, device: str, *, verify: bool = True) -> "ComponentModel":
    """The key-free load, with the artifact root from `env`.

    Both loaders take their local branches: `ParamDecompRunInfo.from_path` on an absolute
    checkpoint path expects `final_config.yaml` beside it; `PretrainRunInfo.from_path` on an
    absolute path expects `final_config.yaml` and `model_config.yaml` in the grandparent.
    """
    from param_decomp.models.component_model import ComponentModel, ParamDecompRunInfo

    spec = AUDIT_RUNS[run]
    art_dir = env.ARTIFACTS_DIR
    if verify:
        verify_manifest(art_dir, [spec.decomp_run, spec.target_run])
    decomp_ckpt = decomp_checkpoint_path(run, art_dir)
    target = target_checkpoint_path(run, art_dir)
    assert decomp_ckpt.is_absolute() and target.is_absolute()
    assert decomp_ckpt.is_file(), decomp_ckpt
    assert (decomp_ckpt.parent / "final_config.yaml").is_file()
    assert (target.parent.parent / "final_config.yaml").is_file()
    assert (target.parent.parent / "model_config.yaml").is_file()
    run_info = ParamDecompRunInfo.from_path(decomp_ckpt)  # local branch: no WandB call
    run_info.config = run_info.config.model_copy(
        update={"pretrained_model_name": str(target)}
    )  # frozen config: copy with the override
    model = ComponentModel.from_run_info(run_info)  # target loads by its local branch
    model = model.to(device).eval()
    if spec.n_matrices is not None:
        assert len(model.components) == spec.n_matrices, len(model.components)
        assert sum(model.module_to_c.values()) == spec.n_subcomponents, sum(model.module_to_c.values())
    assert all(not p.requires_grad for p in model.target_model.parameters())
    return model


def load_run_config(run: str, art_dir: Path = env.ARTIFACTS_DIR) -> Any:
    """The decomposition run's `final_config.yaml` as the authors' `Config` (no model load)."""
    import yaml
    from param_decomp.configs import Config

    with open(decomp_checkpoint_path(run, art_dir).parent / "final_config.yaml") as f:
        return Config(**yaml.safe_load(f))
