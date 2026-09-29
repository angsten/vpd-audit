"""`vpd-audit resummarize`: a finished launch's summary rebuilt from its stores and the current code.

A launch writes `summary.json` and `summary.md` (or `summary__<subset>.*`) beside its stores. The preconditions P1 to P5 in it were
computed from those stores; they are computed again here, from the same stores, and every number, flag, and label of them must equal
the launch's. The launch's other records exist only in its summary (the card, the wall clock, the groups' results, the checkpoint and
set hashes, the cell counts) and are carried over as they are. The text the code writes into a summary is rebuilt from the current
code: the title (`grid.launch_title`), the P4 rule string, the labels of the cell counts (`cells.tier_counts`), and the keys the code
has renamed since the launch (`KEY_RENAMES`). The `.md` is then rendered from the rebuilt JSON (`grid.format_summary`), as the launch
rendered it. Nothing is written if the rebuilt summary differs from the committed one in anything but that text.

Two changes of format since the earliest launches are allowed for in the comparison, not in the output: a chain's key in P4 gained the
ranked pair's two fields (both None for every other chain), and P5 gained `per_chain_rule_families` (empty unless the launch held the
code-leaning chain). The rebuilt summary keeps the launch's own format.

The verification store's `comparisons.md` is rendered again from its `comparisons.json` (`verify.format_comparisons`).

    uv run vpd-audit resummarize results/grid/main/tier1 [more roots] [--out DIR]
"""

from __future__ import annotations

import dataclasses
import json
import math
import re
from pathlib import Path
from typing import Any

import pandas as pd

from vpd_audit import env
from vpd_audit import grid
from vpd_audit.cells import Cell, tier_counts

_INT_FIELDS = {"draw", "tier", "replicate", "shift"}
_BOOL_FIELDS = {"optional", "descriptive"}
_FLOAT_FIELDS = {"tau", "level", "own_round"}
_UNRANKED_CHAIN_KEY = re.compile(r", None, None, ('[^']*')\)$")
KEY_RENAMES: dict[str, str] = {"the_plans": "default_thresholds"}  # a key of the code-leaning thresholds, renamed in pre_reads.py


def _renamed(obj: Any) -> Any:
    """`obj` with every dictionary key of KEY_RENAMES renamed, at any depth; nothing else changes."""
    if isinstance(obj, dict):
        return {KEY_RENAMES.get(k, k): _renamed(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_renamed(v) for v in obj]
    return obj


def _field(name: str, v: Any) -> Any:
    if v is None or (isinstance(v, float) and math.isnan(v)):
        return None
    if name in _INT_FIELDS:
        return int(v)
    if name in _BOOL_FIELDS:
        return bool(v)
    if name in _FLOAT_FIELDS:
        return float(v)
    return v.item() if hasattr(v, "item") else v


def store_cells(store: Path) -> list[Cell]:
    """The cells of a finished store, rebuilt from its cell table; each rebuilt cell's name must be the name the table holds."""
    ct = pd.read_parquet(Path(store) / "cells.parquet")
    fields = [f.name for f in dataclasses.fields(Cell) if f.name in ct.columns]
    out = []
    for _, r in ct.iterrows():
        c = Cell(**{f: _field(f, r[f]) for f in fields})
        assert c.name == r["cell"], f"{store}: the cell table's row {r['cell']} rebuilds as {c.name}"
        out.append(c)
    return out


@dataclasses.dataclass
class _Group:
    name: str
    result: dict[str, Any]


def _config(config: dict[str, Any]) -> grid.GridConfig:
    known = {f.name for f in dataclasses.fields(grid.GridConfig)}
    unknown = set(config) - known
    assert not unknown, f"the summary's config has fields GridConfig does not: {sorted(unknown)}"
    return grid.GridConfig(**{k: (tuple(v) if isinstance(v, list) else v) for k, v in config.items()})


def _dump(obj: Any) -> str:
    return json.dumps(obj, indent=2, sort_keys=True, default=str)


def _comparable(pre: dict[str, Any], *, launch_format: dict[str, Any]) -> dict[str, Any]:
    """The preconditions as mappings keyed by chain or curve, in the launch's format (see the module docstring), without the P4 rule."""
    p = json.loads(_dump(pre))
    if p.get("available"):
        for chain in p["P4"]["chains"]:
            chain["chain"] = _UNRANKED_CHAIN_KEY.sub(r", \1)", chain["chain"])
        p["P4"] = {**p["P4"], "chains": {c["chain"]: c for c in p["P4"]["chains"]}}
        p["P4"].pop("rule", None)
        p["P1"] = {**p["P1"], "chains": {c["chain"]: c for c in p["P1"]["chains"]}}
        p["P2"] = {"reported": {c["chain"]: c for c in p["P2"]["reported"]}}
        p["P5"] = {**p["P5"], "as_far_as_it_applies": {c["curve"]: c for c in p["P5"]["as_far_as_it_applies"]}}
        if "per_chain_rule_families" not in launch_format.get("P5", {}):
            assert p["P5"].pop("per_chain_rule_families", []) == [], "a family judged by the per-chain rule in a launch whose summary has no such key"
    return p


def _differences(a: Any, b: Any, path: str = "") -> list[str]:
    if isinstance(a, dict) and isinstance(b, dict):
        out = []
        for k in sorted(set(a) | set(b), key=str):
            if k not in a or k not in b:
                out.append(f"{path}/{k}: only in the {'committed' if k in a else 'rebuilt'} summary")
            else:
                out += _differences(a[k], b[k], f"{path}/{k}")
        return out
    if isinstance(a, list) and isinstance(b, list):
        if len(a) != len(b):
            return [f"{path}: {len(a)} entries -> {len(b)}"]
        return [d for i, (u, v) in enumerate(zip(a, b)) for d in _differences(u, v, f"{path}[{i}]")]
    return [] if a == b else [f"{path}: {str(a)[:100]!r} -> {str(b)[:100]!r}"]


def rebuild_summary(root: Path, stem: str, committed: dict[str, Any], *, strata: list[str] | None) -> tuple[dict[str, Any], list[str]]:
    """The rebuilt summary of the launch whose summary is `committed`, and the paths of the text it rebuilt."""
    cfg = _config(committed["config"])
    assert len(cfg.tiers) == 1 and str(cfg.job_prefix).startswith("grid_"), f"{root}/{stem}: not a launch of one tier of the grid ({cfg.tiers}, {cfg.job_prefix})"
    groups = [_Group(name, {"ok": bool(g.get("ok"))}) for name, g in committed["groups"].items()]
    cells = [c for g in groups if g.result["ok"] for c in store_cells(root / g.name)]
    pre = grid.preconditions(root, cells, groups, cfg, log=lambda *_: None, strata=strata)
    got, want = _comparable(pre, launch_format=committed["preconditions"]), _comparable(committed["preconditions"], launch_format=committed["preconditions"])
    diff = _differences(want, got)
    assert not diff, f"{root}/{stem}: the preconditions recomputed from the stores differ from the launch's: {diff[:6]}"
    new = _renamed(json.loads(_dump(committed)))
    rebuilt = ["/... (renamed keys)"] if _dump(new) != _dump(committed) else []
    title = grid.launch_title(cfg.tiers[0], cfg.subset_name)
    if new["config"].get("job_title") != title:
        new["config"]["job_title"] = title
        rebuilt.append("/config/job_title")
    if new["preconditions"].get("available") and new["preconditions"]["P4"].get("rule") != pre["P4"]["rule"]:
        new["preconditions"]["P4"]["rule"] = pre["P4"]["rule"]
        rebuilt.append("/preconditions/P4/rule")
    labels = {k: v for k, v in tier_counts([])["total"].items() if isinstance(v, str)}
    total = new["cell_counts"]["total"]
    old_labels = {k: v for k, v in total.items() if isinstance(v, str)}
    if old_labels != labels:
        new["cell_counts"]["total"] = {**{k: v for k, v in total.items() if not isinstance(v, str)}, **labels}
        rebuilt.append("/cell_counts/total (its text)")
    return new, rebuilt


def _check_only_text_changed(committed: dict[str, Any], new: dict[str, Any], where: str) -> None:
    """Every number and flag of the rebuilt summary equals the committed one's; only strings may differ, and only where rebuilt."""
    def walk(a: Any, b: Any, path: str) -> None:
        if isinstance(a, dict) and isinstance(b, dict):
            num_a = {k: v for k, v in a.items() if not isinstance(v, str)}
            num_b = {k: v for k, v in b.items() if not isinstance(v, str)}
            assert set(num_a) == set(num_b), f"{where}{path}: keys {sorted(set(num_a) ^ set(num_b))}"
            for k in num_a:
                walk(num_a[k], num_b[k], f"{path}/{k}")
        elif isinstance(a, list) and isinstance(b, list):
            assert len(a) == len(b), f"{where}{path}: {len(a)} entries -> {len(b)}"
            for i, (u, v) in enumerate(zip(a, b)):
                if not (isinstance(u, str) and isinstance(v, str)):
                    walk(u, v, f"{path}[{i}]")
        else:
            assert type(a) is type(b) and a == b, f"{where}{path}: {a!r} -> {b!r}"

    walk(committed, new, "")


def resummarize_root(root: Path, out_dir: Path | None = None, *, log: Any = print) -> dict[str, Any]:
    """Every launch summary directly under `root` (a tier's root), rebuilt into `out_dir` (default: `root`), or, for the verification
    store, its comparisons.md rendered again."""
    root = Path(root)
    out_dir = Path(out_dir) if out_dir is not None else root
    out_dir.mkdir(parents=True, exist_ok=True)
    done: dict[str, Any] = {}
    if (root / "comparisons.json").is_file():
        from vpd_audit.verify import format_comparisons

        r = json.loads((root / "comparisons.json").read_text())
        (out_dir / "comparisons.md").write_text(format_comparisons(r["comparisons"], r.get("resume"), r["two_paths"]) + "\n")
        done["comparisons"] = {"rendered": "comparisons.md"}
        log(f"[resummarize] {env.input_path(root)}: comparisons.md rendered from comparisons.json")
        return done
    manifest = json.loads((env.PROJECT_ROOT / "results" / "data" / "labeled_manifest.json").read_text())
    strata = manifest["sets"]["E_lab"]["strata"]
    stems = sorted(p.stem for p in root.glob("summary*.json"))
    assert stems, f"{root}: no launch summary"
    for stem in stems:
        text = (root / f"{stem}.json").read_text()
        committed = json.loads(text)
        assert _dump(committed) == text, f"{root}/{stem}.json: not in the launch's JSON format (indent 2, sorted keys)"
        new, rebuilt = rebuild_summary(root, stem, committed, strata=strata)
        _check_only_text_changed(_renamed(committed), new, f"{root}/{stem}")
        (out_dir / f"{stem}.json").write_text(_dump(new))
        (out_dir / f"{stem}.md").write_text(grid.format_summary(new) + "\n")
        done[stem] = {"rebuilt": rebuilt}
        log(f"[resummarize] {env.input_path(root)}/{stem}: preconditions equal to the launch's; rebuilt {rebuilt or 'nothing'}")
    return done
