"""`vpd-audit resummarize` on a committed launch: the preconditions recomputed from the stores equal the launch's, only the text is
rebuilt, a second rebuild changes nothing, and a summary whose numbers disagree with its stores is refused."""

from __future__ import annotations

import json
import shutil
from pathlib import Path

import pytest

from vpd_audit import env, grid
from vpd_audit.resummarize import resummarize_root

ROOT = env.PROJECT_ROOT / "results" / "grid" / "main_s11" / "tier6"
STEM = "summary__binary_union"


def _copy_root(tmp: Path) -> Path:
    root = tmp / "tier6"
    root.mkdir()
    shutil.copy(ROOT / f"{STEM}.json", root)
    shutil.copy(ROOT / f"{STEM}.md", root)
    (root / "E__binary_union").symlink_to(ROOT / "E__binary_union", target_is_directory=True)
    return root


def test_the_rebuilt_summary_keeps_every_number_and_a_second_rebuild_changes_nothing(tmp_path):
    root = _copy_root(tmp_path)
    resummarize_root(root, tmp_path / "once", log=lambda *_: None)
    once = json.loads((tmp_path / "once" / f"{STEM}.json").read_text())
    assert once["config"]["job_title"] == grid.launch_title(6, "binary_union") and once["preconditions"]["P4"]["n_pass"] == once["preconditions"]["P4"]["n"] == 6
    assert (tmp_path / "once" / f"{STEM}.md").read_text() == grid.format_summary(once) + "\n"
    (tmp_path / "second").mkdir()
    again = _copy_root(tmp_path / "second")
    shutil.copy(tmp_path / "once" / f"{STEM}.json", again / f"{STEM}.json")
    resummarize_root(again, tmp_path / "twice", log=lambda *_: None)
    assert (tmp_path / "twice" / f"{STEM}.json").read_bytes() == (tmp_path / "once" / f"{STEM}.json").read_bytes()


def test_a_summary_whose_numbers_disagree_with_its_stores_is_refused(tmp_path):
    root = _copy_root(tmp_path)
    s = json.loads((root / f"{STEM}.json").read_text())
    s["preconditions"]["P3"]["permitted_cells"] += 1
    (root / f"{STEM}.json").write_text(json.dumps(s, indent=2, sort_keys=True, default=str))
    with pytest.raises(AssertionError, match="differ from the launch's"):
        resummarize_root(root, tmp_path / "out", log=lambda *_: None)
    assert not (tmp_path / "out" / f"{STEM}.json").exists()
