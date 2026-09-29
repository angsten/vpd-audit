"""Cache root and the environment variables that must be set before `param_decomp`,
`datasets`, or `huggingface_hub` are imported.

`VPD_AUDIT_CACHE_DIR` is the root of the cache: `/cache` on Modal (the image sets the
variable to the volume mount) and `<project>/.cache` locally. Beneath it: `artifacts/`,
`sets/`, `results/`, `out/`, `hf/`. `PARAM_DECOMP_OUT_DIR` points at `<cache>/out`
because importing `param_decomp` otherwise creates `~/param_decomp_out` at import time;
`HF_HOME` points at `<cache>/hf`.
"""

from __future__ import annotations

import os
from pathlib import Path

PROJECT_ROOT: Path = Path(__file__).resolve().parent.parent
SUBMODULE_DIR: Path = PROJECT_ROOT / "third_party" / "param-decomp"

CACHE_DIR: Path = Path(os.environ.get("VPD_AUDIT_CACHE_DIR", PROJECT_ROOT / ".cache")).resolve()
ARTIFACTS_DIR: Path = CACHE_DIR / "artifacts"
SETS_DIR: Path = CACHE_DIR / "sets"
RESULTS_DIR: Path = CACHE_DIR / "results"
OUT_DIR: Path = CACHE_DIR / "out"
HF_DIR: Path = CACHE_DIR / "hf"

os.environ.setdefault("PARAM_DECOMP_OUT_DIR", str(OUT_DIR))
os.environ.setdefault("HF_HOME", str(HF_DIR))

for _d in (ARTIFACTS_DIR, SETS_DIR, RESULTS_DIR, OUT_DIR, HF_DIR):
    _d.mkdir(parents=True, exist_ok=True)


def describe() -> dict[str, str]:
    return {
        "VPD_AUDIT_CACHE_DIR": str(CACHE_DIR),
        "PARAM_DECOMP_OUT_DIR": os.environ["PARAM_DECOMP_OUT_DIR"],
        "HF_HOME": os.environ["HF_HOME"],
    }


def input_path(p: str | os.PathLike) -> str:
    """An input's path as an output file records it: relative to the project root, with forward slashes, never absolute. (A file
    the command writes itself is recorded by its name, relative to the output directory.)"""
    return Path(os.path.relpath(Path(p).resolve(), PROJECT_ROOT)).as_posix()


def assert_no_absolute_path(obj: object, where: str) -> None:
    """Refuses to record an absolute path: every string or path in `obj` (walked through dicts, lists, and tuples) must be relative,
    so that an output file is the same wherever the command ran."""

    def walk(x: object, at: str) -> None:
        if isinstance(x, dict):
            for k, v in x.items():
                walk(v, f"{at}/{k}")
        elif isinstance(x, (list, tuple)):
            for i, v in enumerate(x):
                walk(v, f"{at}[{i}]")
        elif isinstance(x, (str, os.PathLike)):
            assert not os.path.isabs(os.fspath(x)), f"{where}: an absolute path would be recorded at {at or '/'}: {os.fspath(x)}"

    walk(obj, "")
