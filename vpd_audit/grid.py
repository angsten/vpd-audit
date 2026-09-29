"""The grid runner: the loop over the tiers, and the dry run on SimpleStories.

`run_grid` loads the caches and the alive vector of the run (keyed by run, with its hash), computes the adaptive rule
from n_on alone over every draw before any cell runs (per pool at the primary threshold; the
tau = 0.5 chains mirror the tau = 0.1 chains cell for cell, so they carry the same inserted rungs), enumerates the
cells, builds every source once, groups the cells by evaluation set (E, E_lab, and for the donor-side pass the donor
sequences of each union draw and rung), runs each group through `run_cells` with the peak GPU memory recorded and
a failure caught, logged, and listed rather than aborting the rest, and then reads the launch preconditions P1 to P5
(`preconditions`) off the tables as far as they apply. The concrete set and pool names come from `GridConfig` (the dry run
maps E to E_dry, D_unif to D_unif_dry, and so on); the cells keep the abstract coordinates.
"""

from __future__ import annotations

import json
import time
import traceback
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import torch

from vpd_audit import env
from vpd_audit.cells import ALL_SUBSETS, SUBSETS, TIER_4, BuiltSource, Cell, build_sources, code_leaning_rung, enumerate_cells, marginal_canaries, reference_for, run_cells, tier_counts
from vpd_audit.cells import LAUNCH_SUBSETS, SUBSETS_TIER_5, TIER_5, TIER_5_RUNS, per_position_listed, plain_terms_reruns  # tier 5
from vpd_audit.importances import module_keys
from vpd_audit.reference import cell_key, CONDITION_BY_NAME
from vpd_audit.sources import INTERMEDIATE_RUNGS, SUB_RUNGS, Cache, adaptive_rungs, donor_set, key_sha256, n_on, positive_label_counts, source_hash, union_source
from vpd_audit.cells import LAUNCH_SUBSETS_S11, SUBSETS_TIER_6, TIER_6, TIER_6_RUNS  # tier 6
from vpd_audit.sources import OWN_ROUND_PERMITTED, ROUNDED0_FAMILY  # tier 6
from vpd_audit.cells import LAUNCH_SUBSETS_S12, SUBSETS_TIER_7, TIER_7, TIER_7_RUNS  # tier 7: the merge sizes and the panel edit

POOLS = ("D_unif", "D_code", "D_prose")
TAUS = (0.0, 0.1, 0.5)
P1_MIN_DIFF = 0.01


@dataclass
class GridConfig:
    run: str  # the decomposition and the Cell.run label: simplestories | main | control
    set_map: dict[str, str]  # {"E": "E_dry", "E_lab": "E_lab_dry"}
    pool_map: dict[str, str]  # {"D_unif": "D_unif_dry", "D_code": "D_code_dry", "D_prose": "D_prose_dry"}
    cache_tag: str  # the prose-named and f_code files' tag
    draws: int = 2
    precision: str = "bf16"
    subbatch: int = 64
    chunk: int = 32
    include_optional: bool = True
    tiers: tuple[int, ...] = (1, 2, 3)
    master_seed: int = 0
    strata_file: str | None = "E_lab_dry.strata.json"  # the strata of the labeled evaluation set, for P5
    positive_stratum: str = "dialogue"  # the stand-in for the GitHub stratum
    only_groups: tuple[str, ...] | None = None  # run these groups only (a debugging filter; None runs every group)
    job_title: str = "The dry run of the grid"  # the summary's header
    job_prefix: str = "dry"  # run_cells job names: <prefix>_<group> (a grid launch: grid_<run>_t<tier>_<group>)
    # a subset of families into separately named stores (<group>__<subset>), each carrying the references;
    # `subset_name` names a predicate of cells.SUBSETS (levels, ranked, curve1_extra, tau0_union, editing_extra,
    # donor_side, never_named); `families` is the older family filter, still honoured when given
    families: tuple[str, ...] | None = None
    subset_name: str | None = None
    # the code-leaning group's thresholds (0.9 and 0.75 on the paper's model, fixed in advance) and whether the
    # chain is built whatever the existence rule returned; only the stand-in's dry run changes them (code_leaning.STAND_IN_*)
    code_leaning_group: float = 0.9
    code_leaning_wide: float = 0.75
    code_leaning_force: bool = False
    # tier 5: the stand-in's pools are filtered rows, so its documents are blocks of this many rows, as
    # in s9_checks.dry_inputs; None on the paper's model, whose documents come from s9_checks.document_index
    synthetic_document_rows: int | None = None


@dataclass
class Group:
    name: str
    eval_set: str  # the abstract set
    set_name: str  # the concrete set
    ids: np.ndarray
    set_hash: str
    cells: list[Cell]
    note: str = ""
    result: dict[str, Any] = field(default_factory=dict)


def compute_adaptive(caches: dict[str, Cache], run: str, draws: int, master_seed: int, taus: tuple[float, ...] = TAUS) -> dict[str, Any]:
    """n_on at every rung and draw for both donor pools and every threshold, and the rule per (pool, tau)."""
    out: dict[str, Any] = {"n_on": {}, "rule": {}, "insert": {}}
    for pool in ("D_unif", "D_code"):
        cache = caches[f"{pool}_{run}"]
        for tau in taus:
            per_rung: dict[str, dict[int, int]] = {}
            for r in INTERMEDIATE_RUNGS + ("8",):
                for k in range(draws if r != "8" else 1):
                    ds = donor_set(pool, cache.n_sequences, k, r, master_seed)
                    per_rung.setdefault(r, {})[k] = int(union_source(cache, ds.positions, tau).sum())
            insert, meta = adaptive_rungs(per_rung)
            out["n_on"][f"{pool}|tau{tau:g}"] = per_rung
            out["rule"][f"{pool}|tau{tau:g}"] = meta
            if insert:
                out["insert"][f"{pool}|tau{tau:g}"] = ["5a", "6a"]
    return out


def group_cells(cells: list[Cell], cfg: GridConfig, sets: dict[str, tuple[np.ndarray, str]], caches: dict[str, Cache]) -> list[Group]:
    groups: dict[str, Group] = {}
    for c in cells:
        if c.eval_set == "donors":
            pool_ids, pool_hash = sets[cfg.pool_map[c.donor_pool]]  # type: ignore[index]
            ds = donor_set(c.donor_pool, caches[f"{c.donor_pool}_{c.run}"].n_sequences, c.draw, c.rung, cfg.master_seed)  # type: ignore[arg-type]
            key = f"donors_{c.donor_pool}_k{c.draw}_r{c.rung}"
            if key not in groups:
                ids = pool_ids[list(ds.sequences)]
                groups[key] = Group(key, "donors", f"{cfg.pool_map[c.donor_pool]}[{','.join(str(s) for s in ds.sequences[:8])}{',...' if len(ds.sequences) > 8 else ''}]", ids, pool_hash, [],  # type: ignore[index]
                                    note=f"the donor sequences of draw {c.draw}, rung {c.rung}: {len(ds.sequences)} sequences of {cfg.pool_map[c.donor_pool]}")
            groups[key].cells.append(c)
        else:
            key = c.eval_set if cfg.subset_name is None else f"{c.eval_set}__{cfg.subset_name}"
            if key not in groups:
                ids, h = sets[cfg.set_map[c.eval_set]]
                groups[key] = Group(key, c.eval_set, cfg.set_map[c.eval_set], ids, h, [], note=f"the {cfg.subset_name} subset" if cfg.subset_name else "")
            groups[key].cells.append(c)
    return list(groups.values())


def add_store_references(groups: list[Group], run: str, draws: int, eval_sets: tuple[str, ...] = ("E", "E_lab"), conditions: tuple[Any, ...] | None = None) -> dict[str, list[str]]:
    """Every store on E or E_lab carries that set's full reference set (`_references` for the run
    and set), so that a launch of tier 2 or 3 alone has its rung 0 for P1, P4, and the conditional-damage columns, and
    the references are re-run per launch as a bitwise canary. The cell names are unchanged (the tier is not in the name),
    so they are added per store here rather than in `enumerate_cells`, whose uniqueness assertion would fire. Returns
    the names added per group; nothing is added where the group already holds the reference. `eval_sets`:
    a tier-5 launch passes D_unif as well, an evaluation set of the self-merge with its own full reference set.
    `conditions`: a subset of `reference.CONDITIONS` in their order; None is the full set, as before."""
    from vpd_audit.cells import _references

    added: dict[str, list[str]] = {}
    for g in groups:
        if g.eval_set not in eval_sets:
            continue
        have = {c.name for c in g.cells}
        refs = [c for c in _references(run, g.eval_set, 1, draws=draws, **({"conditions": tuple(conditions)} if conditions is not None else {})) if c.name not in have]
        g.cells.extend(refs)
        added[g.name] = [c.name for c in refs]
    return added


def assert_or_write_adaptive_rule(adaptive: dict[str, Any], path: Path, *, log: Any = print) -> str:
    """The adaptive rule is computed from the run's caches on the first launch and written to
    `path`; every later launch recomputes it and asserts equality (after a JSON round trip, since JSON keys are strings),
    so a changed cache is noticed. Returns "written" or "asserted"."""
    fresh = json.loads(json.dumps(adaptive, sort_keys=True, default=str))
    if path.is_file():
        with open(path) as f:
            prior = json.load(f)
        assert prior == fresh, f"the adaptive rule recomputed from the caches differs from the one at {path} (a changed cache?)"
        log(f"[grid] adaptive rule equals the one at {path} (asserted)")
        return "asserted"
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as f:
        json.dump(adaptive, f, indent=2, sort_keys=True, default=str)
    return "written"


def assert_rank_keys_match_pre_reads(launch_hashes: dict[str, str], cells: list[Cell], manifest_path: Path | None, *, required: bool, log: Any = print) -> dict[str, Any]:
    """When a launch holds a ranked
    never-named cell, the SHA-256 of each ranking key it ranks by (the weight norms from the loaded model, the positive-
    label counts from the cache) must equal the one the run's pre-reads recorded in their manifest under `rank_keys`, so
    that the ranking the testability table was judged on is the ranking the cells erase. `required` makes a missing
    manifest or hash a stop (the paper's launches); the dry run tolerates its absence and says so."""
    ranked = [c for c in cells if c.family == "never_named_ranked"]
    if not ranked:
        return {"applies": False, "n_ranked_cells": 0}
    pre: dict[str, str] = {}
    if manifest_path is not None and Path(manifest_path).is_file():
        with open(manifest_path) as f:
            pre = dict(json.load(f).get("rank_keys") or {})
    needed = sorted({c.rank_key for c in ranked if c.rank_key})
    missing = [k for k in needed if not pre.get(k)]
    if missing:
        assert not required, f"{len(ranked)} ranked never-named cells in the launch, but no pre-reads hash for {missing} at {manifest_path}: rerun the pre-reads for this run first"
        log(f"[grid] rank keys: {len(ranked)} ranked cells, no pre-reads manifest hash for {missing} at {manifest_path}; not asserted")
        return {"applies": True, "n_ranked_cells": len(ranked), "pre_reads_manifest": str(manifest_path), "pre_reads": pre, "launch": launch_hashes, "asserted": False}
    for k in needed:
        assert pre[k] == launch_hashes[k], f"the launch's {k} key ({launch_hashes[k][:16]}) differs from the pre-reads' ({pre[k][:16]}) at {manifest_path}: the ranking judged is not the ranking erased"
    log(f"[grid] rank keys {needed} equal the pre-reads' at {manifest_path} (asserted: " + ", ".join(f"{k} {pre[k][:16]}" for k in needed) + ")")
    return {"applies": True, "n_ranked_cells": len(ranked), "pre_reads_manifest": str(manifest_path), "pre_reads": {k: pre[k] for k in needed}, "launch": {k: launch_hashes[k] for k in needed}, "asserted": True}


def add_store_canaries(groups: list[Group], run: str, subset_name: str | None) -> dict[str, list[str]]:
    """The marginal subset's store on E reruns curve 1's union and its plain control at rung 2,
    draw 0, under their own names (tiers 1 and 2), for the analysis to assert bitwise against tiers 1 and 2. Added per store,
    as the references are. Returns the names added per group."""
    added: dict[str, list[str]] = {}
    if subset_name != "marginal":
        return added
    for g in groups:
        if g.eval_set != "E":
            continue
        have = {c.name for c in g.cells}
        new = [c for c in marginal_canaries(run) if c.name not in have]
        g.cells.extend(new)
        added[g.name] = [c.name for c in new]
    return added


def add_store_reruns(groups: list[Group], reruns: list[Cell], cfg: GridConfig, sets: dict[str, tuple[np.ndarray, str]]) -> dict[str, list[str]]:
    """The re-run cells of the `plain_terms` subset join its stores under their committed names and
    seeds (cell names carry no tier and `enumerate_cells` asserts that names are unique, so they are never enumerated a second
    time), as the references and the marginal subset's canaries do. A store is created where the subset enumerates no cell of its own
    (the stand-in, which has no external-model cell). Returns the names added per group."""
    added: dict[str, list[str]] = {}
    by_name = {g.name: g for g in groups}
    for c in reruns:
        key = f"{c.eval_set}__{cfg.subset_name}"
        if key not in by_name:
            ids, h = sets[cfg.set_map[c.eval_set]]
            by_name[key] = Group(key, c.eval_set, cfg.set_map[c.eval_set], ids, h, [], note=f"the {cfg.subset_name} subset")
            groups.append(by_name[key])
        g = by_name[key]
        assert g.eval_set == c.eval_set and c.name not in {x.name for x in g.cells}, c.name
        g.cells.append(c)
        added.setdefault(key, []).append(c.name)
    return added


def read_s7_pre_reads(s7_dir: Path | None) -> dict[str, Any] | None:
    """The label-only pre-read (pre_reads.run_pre_reads_s7) that a tier-4 launch is held to: the existence rule's
    verdict and the chain's ladder, and the source hash of every set the pre-read judged."""
    if s7_dir is None or not (Path(s7_dir) / "summary.json").is_file():
        return None
    d = Path(s7_dir)
    with open(d / "summary.json") as f:
        summary = json.load(f)
    cl = summary["code_leaning"]
    out: dict[str, Any] = {"dir": str(d), "verdict": cl["existence"]["verdict"], "thresholds": cl.get("thresholds"), "ladder": [(int(a), bool(b)) for a, b in cl.get("chain", {}).get("ladder", [])],
                           "control_gate": cl.get("chain", {}).get("control_gate"), "rates_sha256": summary["marginal"]["rates_sha256"]}
    comp = pd.read_csv(d / "marginal_composition.csv", dtype={"rung": str, "draw": str})
    comp = comp[(comp.control == "marginal") & (comp.draw != "pooled")]
    out["marginal"] = {(str(r), int(k), int(rep)): h for r, k, rep, h in zip(comp.rung, comp.draw, comp.replicate, comp.source_sha256)}
    if (d / "code_leaning_chain.csv").is_file():
        ch = pd.read_csv(d / "code_leaning_chain.csv")
        out["chain"] = {int(n): h for n, h in zip(ch.rung_size, ch.source_sha256)}
        ct = pd.read_csv(d / "code_leaning_control_per_draw.csv")
        out["control"] = {(int(n), int(k)): h for n, k, h in zip(ct.rung_size, ct.draw, ct.source_sha256)}
    return out


def code_leaning_ladder_for_launch(pre: dict[str, Any] | None, cfg: GridConfig) -> list[tuple[int, bool]] | None:
    """At launch, the code-leaning chain is enumerated only if the pre-read's existence rule returned clear
    or marginal (or, on the stand-in, the chain was forced there and is forced here), and only under the thresholds the
    pre-read used; otherwise no code-leaning cell exists and a launch of that subset stops for want of cells."""
    if pre is None or not pre.get("ladder"):
        return None
    th = pre.get("thresholds") or {}
    assert abs(th.get("group", -1) - cfg.code_leaning_group) < 1e-12 and abs(th.get("wide", -1) - cfg.code_leaning_wide) < 1e-12, f"the pre-read's thresholds {th} are not the launch's ({cfg.code_leaning_group}, {cfg.code_leaning_wide})"
    if pre["verdict"] in ("clear", "marginal") or (cfg.code_leaning_force and th.get("chain_forced")):
        return list(pre["ladder"])
    return None


def assert_sources_match_s7_pre_reads(cells: list[Cell], sources: dict[str, BuiltSource], pre: dict[str, Any] | None, *, log: Any = print) -> dict[str, Any]:
    """Every tier-4 set a launch is about to run must be the set the label-only pre-read judged, by
    source hash: the marginal control's against marginal_composition.csv (the sets built on Modal), the code-leaning chain's
    and its twins' against code_leaning_chain.csv and code_leaning_control_per_draw.csv. The overlap constants, the gate, the
    testability, and the control's gate were all read on those sets."""
    t4 = [c for c in cells if c.tier == TIER_4]
    if not t4:
        return {"applies": False, "n_tier_4_cells": 0}
    assert pre is not None, f"{len(t4)} tier-4 cells in the launch, but no tier-4 label-only pre-read to hold them to: run pre_reads_s7 for this run first"
    n = {"marginal": 0, "chain": 0, "control": 0}
    for c in t4:
        got = sources[c.name].record["source_sha256"]
        if c.control == "marginal":
            key = (c.rung, c.draw, c.replicate)
            assert key in pre["marginal"], f"{c.name}: the pre-read holds no marginal set at rung {c.rung}, draw {c.draw}, replicate {c.replicate}"
            assert pre["marginal"][key] == got, f"{c.name}: the launch's marginal set ({got[:16]}) is not the pre-read's ({pre['marginal'][key][:16]}); the overlap constants were read on the pre-read's"
            n["marginal"] += 1
        elif c.family == "code_leaning_hard":
            size = int(c.rung[1:])
            want = pre["chain"][size] if c.control == "none" else pre["control"][(size, c.draw)]
            assert want == got, f"{c.name}: the launch's set ({got[:16]}) is not the pre-read's ({want[:16]}); the testability and the control's gate were read on the pre-read's"
            n["chain" if c.control == "none" else "control"] += 1
        else:
            raise AssertionError(f"{c.name}: a tier-4 cell the pre-read does not cover")
    log(f"[grid] tier 4: {n['marginal']} marginal sets, {n['chain']} code-leaning rungs and {n['control']} of their controls equal the label-only pre-read's at {pre['dir']} (asserted by source hash)")
    return {"applies": True, "n_tier_4_cells": len(t4), "asserted": n, "pre_reads_dir": pre["dir"], "verdict": pre["verdict"], "thresholds": pre.get("thresholds"), "control_gate": pre.get("control_gate")}


def _prepare_tier_5(model: Any, cfg: GridConfig, groups: list[Group], sources: dict[str, BuiltSource], sets: dict[str, tuple[np.ndarray, str]], caches: dict[str, Cache], t5_inputs: Any,
                    committed: Any, reruns: list[Cell], group_size: int | None, out_root: Path, *, require_s9: bool, log: Any = print) -> tuple[dict[str, Any], dict[str, Any]]:
    """Before any forward pass of a tier-5 launch: partners.parquet per store with a partner cell; the
    example positions for E, held to the committed list; the comparison models loaded and their pre-flight gates run
    (external_models.json); and one `tier5.StoreRun` per store with its canary and, on D_unif, its gate. Returns the per-store
    runs and the launch's record of all this. Any failure here is a `tier5.GateFailure` or an assertion: the launch stops."""
    from vpd_audit import tier5 as t5m

    device = next(model.parameters()).device
    record: dict[str, Any] = {"subset": cfg.subset_name, "partners": {}, "external_models": None}
    for g in groups:
        if any(c.family == "partner_union" for c in g.cells):
            table = t5m.partners_table(g.cells, sources, t5_inputs)
            (out_root / g.name).mkdir(parents=True, exist_ok=True)
            table.to_parquet(out_root / g.name / "partners.parquet", index=False)
            record["partners"][g.name] = {"rows": int(len(table)), "n_same_document_pairs": int(table["same_document"].fillna(False).sum())}
    n_e = sets[cfg.set_map["E"]][0].shape[0]
    positions = t5m.example_positions(n_e, master_seed=cfg.master_seed)
    record["example_positions"] = t5m.assert_example_positions(positions, cfg.run, required=require_s9, log=log)
    externals = None
    if any(c.family == "external" for g in groups for c in g.cells):
        from vpd_audit import external_models as xm

        keys_needed = sorted({c.model for g in groups for c in g.cells if c.family == "external"}, key=list(xm.MODELS).index)
        externals = {k: xm.load_external(k, device, log=log) for k in keys_needed}
        with open(env.SETS_DIR / cfg.strata_file) as f:  # type: ignore[operator]
            strata = json.load(f)["strata"]
        other = np.flatnonzero(np.asarray([s != cfg.positive_stratum for s in strata]))
        pre = xm.preflight(externals, {s: sets[cfg.set_map[s]][0] for s in ("E", "E_lab")}, reference_rows=("E_lab", other), device=device, subbatch=cfg.subbatch, log=log)
        with open(out_root / "external_models.json", "w") as f:
            json.dump(pre, f, indent=2, sort_keys=True, default=str)
        record["external_models"] = {"file": "external_models.json", "gates_pass": pre["gates"]["pass"], "models": {k: {x: v[x] for x in ("repo", "revision", "resolved_commit", "weights_sha256")} for k, v in pre["models"].items()}}
    rerun_names = {c.name for c in reruns}
    runs: dict[str, Any] = {}
    for g in groups:
        checker = t5m.build_checker(g.name, g.eval_set, g.cells, sources, committed, run=cfg.run, n_pool_sequences=caches[f"D_unif_{cfg.run}"].n_sequences, draws=cfg.draws, master_seed=cfg.master_seed,
                                    rerun_names=rerun_names, log=log)
        if require_s9 and checker is None:
            raise t5m.GateFailure(f"{g.name}: no canary could be built")
        runs[g.name] = t5m.StoreRun(listed=lambda c, _n=group_size: per_position_listed(c, _n), example_positions=positions if g.eval_set == "E" else None, externals=externals, checker=checker)
    record["per_position_listed_cells"] = {g.name: sum(1 for c in g.cells if per_position_listed(c, group_size)) for g in groups}
    return runs, record


def run_grid(model: Any, cfg: GridConfig, out_root: Path, *, adaptive_rule_path: Path | None = None, on_subbatch: Any = None, log: Any = print,
             pre_reads_manifest: Path | None = None, require_pre_reads_hash: bool = False, s7_pre_reads_dir: Path | None = None,
             s9_pre_reads_dir: Path | None = None, committed_roots: tuple[Path, ...] | None = None, require_s9: bool = False, require_s11: bool = False,
             merge_sets_dir: Path | None = None, require_s12: bool = False) -> dict[str, Any]:
    """`adaptive_rule_path`: where the rule lives across launches (default: out_root/adaptive_rule.json, the dry
    run's layout); `on_subbatch(i)` is passed to every run_cells (the grid function commits the volume through it);
    `pre_reads_manifest` is the run's pre-reads manifest, whose weight-norm hash a launch with ranked cells
    must match (`require_pre_reads_hash` makes its absence a stop); `s7_pre_reads_dir` is the run's label-only
    tier-4 pre-read, which a launch of tier 4 needs: the code-leaning ladder and the existence rule's verdict come from it,
    and every tier-4 set is asserted equal to the set it judged.

    Tier 5 (launched alone, one subset per launch, into a root of its own that `analysis.load_grid` never
    walks): `s9_pre_reads_dir` holds the label-only tables, against which every named set is asserted by hash before any
    forward pass; `committed_roots` are the roots of the run's committed stores (tiers 1 to 4), the other side of the bitwise
    canary and of the D_unif gate, both checked after every sub-batch; `require_s9` (the paper's model) makes the absence of
    either, or of a committed example-position list, a stop. A tier-5 launch passes `ce_for_all` and the plain-terms extras to
    the loop, carries the full reference set on D_unif as well, and prints gates and assertions only, never a rise.

    Tier 6 (launched alone as its subset `binary_union`, into a root of its own): the subset selects the tier-6 cells
    and, by predicate, the secondary form's two tier-3 cells per draw from the whole enumeration. Before any forward pass every named set,
    and the canary's, is held to its committed twin in `committed_roots` (`tier6.assert_sets_are_committed`), and the self-merge's sets
    to the label-only tables in `s9_pre_reads_dir`; `require_s11` (the paper's model) makes the absence of either a stop. The store carries four
    references and the canary; no tier-5 extra, no in-loop canary (the analysis holds the canary bitwise); it prints
    gates and assertions only.

    Tier 7 (launched alone as one of its subsets, `merge_sizes` or `panel_edit`, into a root of its own): before any forward pass every
    2- and 4-token set is held to the label-only table in `merge_sets_dir`, every panel edit's set to its committed E_lab twin, and every
    canary's set to its committed self (`tier7.assert_sets`, over `committed_roots`); `require_s12` (the paper's model) makes the absence
    of either a stop. The merge stores carry `importances` and `unmasked` and their canaries; each panel store carries `unmasked_delta`;
    the panel edit's canary runs in a store of its own on E_lab. It prints gates and assertions only."""
    from vpd_audit import tier6 as t6m
    from vpd_audit.artifacts import checkpoint_hashes
    from vpd_audit.data import load_set
    from vpd_audit.donors import donors_dir, load_prose_named_and_f_code

    t_all = time.time()
    device = next(model.parameters()).device
    keys = module_keys(model)
    module_to_c = {k: model.module_to_c[k] for k in keys}
    out_root.mkdir(parents=True, exist_ok=True)
    caches = {f"{pool}_{cfg.run}": Cache.load(f"{cfg.pool_map[pool]}_{cfg.run}") for pool in POOLS}
    alive_vec = np.load(donors_dir() / f"alive_{cfg.pool_map['D_unif']}_{cfg.run}.npy")
    alive = {cfg.run: (alive_vec, source_hash(alive_vec))}
    prose_named, f_code, pn_meta = load_prose_named_and_f_code(cfg.cache_tag)
    sets: dict[str, tuple[np.ndarray, str]] = {}
    for name in set(cfg.set_map.values()) | set(cfg.pool_map.values()):
        ids, _, rec = load_set(name)
        sets[name] = (ids, rec["sha256_ids"])
    hashes = checkpoint_hashes(cfg.run)
    log(f"[grid] {cfg.run}: sets {{{', '.join(f'{k}: {v[0].shape[0]}' for k, v in sets.items())}}}, alive {int(alive_vec.sum())}, {cfg.precision}, sub-batch {cfg.subbatch}, draws {cfg.draws}")
    # 1. the adaptive rule, from n_on alone, before any cell
    adaptive = compute_adaptive(caches, cfg.run, cfg.draws, cfg.master_seed)
    adaptive_map = {(k.split("|tau")[0], float(k.split("|tau")[1])): tuple(v) for k, v in adaptive["insert"].items()}
    adaptive_status = assert_or_write_adaptive_rule(adaptive, adaptive_rule_path or (out_root / "adaptive_rule.json"), log=log)
    log(f"[grid] adaptive rule ({adaptive_status}): {adaptive['rule']}; inserted: {adaptive['insert'] or 'none'}")
    # 2. the cells and their sources
    t5 = TIER_5 in cfg.tiers
    if t5:  # tier 5 is launched alone, as one of its subsets, on the paper's model or the stand-in
        assert cfg.tiers == (TIER_5,) and cfg.subset_name in SUBSETS_TIER_5 and cfg.run in TIER_5_RUNS and cfg.families is None, f"tier 5 is launched alone, as one of {sorted(SUBSETS_TIER_5)}, on one of {TIER_5_RUNS}: got {cfg.tiers}, {cfg.subset_name!r}, {cfg.run!r}"
        cfg.set_map = {**cfg.set_map, "D_unif": cfg.pool_map["D_unif"]}  # D_unif is an evaluation set of the self-merge (its ids are loaded above, as a pool)
    t6 = TIER_6 in cfg.tiers
    if t6:  # tier 6 is launched alone, as its one subset, on the paper's model or the stand-in
        assert cfg.tiers == (TIER_6,) and cfg.subset_name in SUBSETS_TIER_6 and cfg.run in TIER_6_RUNS and cfg.families is None, f"tier 6 is launched alone, as one of {sorted(SUBSETS_TIER_6)}, on one of {TIER_6_RUNS}: got {cfg.tiers}, {cfg.subset_name!r}, {cfg.run!r}"
    assert (cfg.subset_name in SUBSETS_TIER_6) == t6 or cfg.subset_name is None, f"the subset {cfg.subset_name!r} is a tier-6 subset, launched with --tiers 6 alone"
    t7 = TIER_7 in cfg.tiers
    if t7:  # tier 7 is launched alone, as one of its subsets, on the paper's model or the stand-in
        assert cfg.tiers == (TIER_7,) and cfg.subset_name in SUBSETS_TIER_7 and cfg.run in TIER_7_RUNS and cfg.families is None, f"tier 7 is launched alone, as one of {sorted(SUBSETS_TIER_7)}, on one of {TIER_7_RUNS}: got {cfg.tiers}, {cfg.subset_name!r}, {cfg.run!r}"
    assert (cfg.subset_name in SUBSETS_TIER_7) == t7 or cfg.subset_name is None, f"the subset {cfg.subset_name!r} is a tier-7 subset, launched with --tiers 7 alone"
    plain_terms = t5 and cfg.subset_name == "plain_terms"  # its re-runs include the code-leaning edit, so it needs the chain as a tier-4 launch does
    needs_chain = TIER_4 in cfg.tiers or plain_terms or (t7 and cfg.subset_name == "panel_edit")  # tier 7: the panel edit erases the chain's sets
    s7_pre = read_s7_pre_reads(s7_pre_reads_dir) if needs_chain else None
    cl_ladder = code_leaning_ladder_for_launch(s7_pre, cfg) if needs_chain else None
    cl_sets = None
    if cl_ladder:
        from vpd_audit.code_leaning import code_leaning_sets

        cl_sets = code_leaning_sets(caches[f"D_code_{cfg.run}"], caches[f"D_prose_{cfg.run}"], alive_vec, group_threshold=cfg.code_leaning_group, wide_threshold=cfg.code_leaning_wide, master_seed=cfg.master_seed)
        assert cl_sets.ladder == cl_ladder, f"the ladder recomputed from the caches {cl_sets.ladder} is not the pre-read's {cl_ladder} (a changed cache?)"
        log(f"[grid] code-leaning chain (existence rule: {s7_pre['verdict']}{', forced' if cfg.code_leaning_force else ''}): group {cl_sets.n_group} at s >= {cfg.code_leaning_group:g}, wide set {cl_sets.n_wide} at s >= {cfg.code_leaning_wide:g}, rungs {[code_leaning_rung(a) for a, _ in cl_ladder]}")
    # a tier-6 launch enumerates every tier (the tier-4 chain aside), so that its names are checked unique against all of them
    all_cells = enumerate_cells(runs=(cfg.run,), draws=cfg.draws, include_optional=cfg.include_optional, adaptive=adaptive_map, tier_4=needs_chain or t6 or t7,
                                code_leaning={cfg.run: cl_ladder} if cl_ladder else None, tier_5=t5 or t6 or t7, tier_6=t6 or t7, tier_7=t7)
    # the tier-6 subset also selects the secondary form's two tier-3 cells per draw, by predicate, from the whole enumeration
    cells = [c for c in all_cells if c.tier in cfg.tiers] if not t6 else list(all_cells)
    if cfg.families is not None:
        cells = [c for c in cells if c.family in cfg.families]
        assert cells, f"no cells of families {cfg.families} in tiers {cfg.tiers}"
    # the plain_terms subset's re-run cells, taken from the enumeration under their committed names;
    # they join their stores below (add_store_reruns) and are built, asserted, and run with the launch's own cells
    reruns: list[Cell] = plain_terms_reruns(all_cells, cl_sets.n_group if cl_sets is not None else None) if plain_terms else []
    if cfg.subset_name is not None:
        assert cfg.subset_name in LAUNCH_SUBSETS_S12, f"unknown subset {cfg.subset_name!r}; known: {sorted(LAUNCH_SUBSETS_S12)}"  # LAUNCH_SUBSETS_S11 and the two tier-7 subsets
        cells = [c for c in cells if LAUNCH_SUBSETS_S12[cfg.subset_name](c)]
        assert cells or reruns, f"no cells of the subset {cfg.subset_name!r} in tiers {cfg.tiers}"
    assert not t6 or cfg.subset_name is not None, "tier 6 is launched as its subset"
    counts = tier_counts(cells + reruns)
    # the ranked never-named pair orders the set by the weight norm of the loaded model
    from vpd_audit.weight_norms import weight_norms

    norms, norms_meta = weight_norms(model)
    log(f"[grid] weight norms ||U_c|| ||V_c|| from the loaded model: {norms.size} subcomponents, sha256 {norms_meta['sha256'][:16]}")
    rank_key_hashes = {"weight_norm": norms_meta["sha256"], "positive_count": key_sha256(positive_label_counts(caches[f"D_unif_{cfg.run}"]))}
    norms_check = assert_rank_keys_match_pre_reads(rank_key_hashes, cells, pre_reads_manifest, required=require_pre_reads_hash, log=log)
    t5_inputs = None
    if t5 and any(c.family in ("self_union", "partner_union") for c in cells):
        from vpd_audit import tier5 as t5m

        t5_inputs = t5m.load_inputs(cfg.run, cfg.set_map, cfg.pool_map, caches, synthetic_document_rows=cfg.synthetic_document_rows, log=log)
    if t6 and any(c.family in ("self_union", "partner_union") for c in cells):  # the self-merge on E needs E's own-named sets only
        t5_inputs = t6m.load_inputs(cfg.run, cfg.set_map, log=log)
    sources = build_sources(cells + reruns, caches, alive, {cfg.run: prose_named}, {cfg.run: f_code}, module_to_c, master_seed=cfg.master_seed, log=log, weight_norms={cfg.run: norms},
                            code_leaning={cfg.run: cl_sets} if cl_sets is not None else None, tier5_inputs={cfg.run: t5_inputs} if t5_inputs is not None else None)
    s7_check = assert_sources_match_s7_pre_reads(cells + reruns, sources, s7_pre, log=log)  # before any forward pass
    s9_check: dict[str, Any] = {"applies": False}
    committed = None
    if t5:  # every named set against the label-only tables, before any forward pass
        from vpd_audit import tier5 as t5m

        committed = t5m.CommittedTables(tuple(committed_roots)) if committed_roots else None
        if require_s9 and committed is None:
            raise t5m.GateFailure("a tier-5 launch of the paper's model needs the committed stores (the canary's and the gate's other side)")
        s9_check = {"applies": True, **t5m.assert_sources_match_s9_pre_reads(cells + reruns, sources, s9_pre_reads_dir, t5_inputs, run=cfg.run, committed=committed, required=require_s9, log=log)}
    s11_check: dict[str, Any] = {"applies": False}
    if t6:  # before any forward pass: every set of the launch and of its canary against its committed twin; the self-merge's sets against the label-only tables
        from vpd_audit import tier5 as t5m

        canary = t6m.canary_cells(cfg.run)
        sources.update(build_sources(canary, caches, alive, None, None, module_to_c, master_seed=cfg.master_seed, log=log))
        committed6 = t5m.CommittedTables(tuple(committed_roots)) if committed_roots else None
        if require_s11 and committed6 is None:
            raise t5m.GateFailure("a tier-6 launch of the paper's model needs the committed stores (the sets' twins, the canary's other side)")
        if committed6 is not None:
            s11_check = {"applies": True, "asserted": True, **t6m.assert_sets_are_committed(cells + canary, {c.name: sources[c.name].record for c in cells + canary}, committed6, log=log)}
        else:
            log("[tier 6] no committed stores given: the sets are NOT held to their committed twins (a local run)")
            s11_check = {"applies": True, "asserted": False}
        s11_check["self_merge_vs_s9_pre_reads"] = t5m.assert_sources_match_s9_pre_reads(cells + canary, sources, s9_pre_reads_dir, t5_inputs, run=cfg.run, committed=committed6, required=require_s11, log=log)
    s12_check: dict[str, Any] = {"applies": False}
    t7_canaries: dict[str, list[Cell]] = {}
    if t7:  # before any forward pass: the 2- and 4-token sets against the label-only table, the panel edit's sets and the canaries' against their committed twins
        from vpd_audit import tier5 as t5m
        from vpd_audit import tier7 as t7m

        t7_canaries = dict(t7m.merge_canary_cells(cfg.run)) if cfg.subset_name == "merge_sizes" else {t7m.PANEL_CANARY_GROUP: t7m.panel_canary_cells(cfg.run)}
        canary7 = [c for cs in t7_canaries.values() for c in cs]
        sources.update(build_sources(canary7, caches, alive, None, None, module_to_c, master_seed=cfg.master_seed, log=log, code_leaning={cfg.run: cl_sets} if cl_sets is not None else None))
        committed7 = t5m.CommittedTables(tuple(committed_roots)) if committed_roots else None
        table_path = Path(merge_sets_dir) / t7m.MERGE_TABLE if merge_sets_dir is not None else None
        merge_table = pd.read_csv(table_path, dtype={"rung": str}) if (table_path is not None and table_path.is_file()) else None
        needs_table = cfg.subset_name == "merge_sizes"
        if require_s12 and (committed7 is None or (needs_table and merge_table is None)):
            raise t5m.GateFailure(f"a tier-7 launch of the paper's model needs the committed stores{' and the label-only table of the merge sets at ' + str(table_path) if needs_table else ''}")
        if committed7 is not None and (merge_table is not None or not needs_table):
            s12_check = {"applies": True, "asserted": True, "counts": t7m.assert_sets(cells + canary7, {c.name: sources[c.name].record for c in cells + canary7}, committed7, merge_table, log=log),
                         "committed_subbatch": t7m.assert_subbatch(cfg.subbatch, committed7, cfg.run)}
        else:
            log("[tier 7] no committed stores, or no label-only table: the sets are NOT held to their twins (a local run)")
            s12_check = {"applies": True, "asserted": False}
    groups = group_cells(cells, cfg, sets, caches)
    if t7:  # the canaries join the merge stores; the panel edit's canary gets a store of its own on E_lab
        by_group = {g.name: g for g in groups}
        for key, cs in t7_canaries.items():
            gname = key if key == t7m.PANEL_CANARY_GROUP else f"{key}__{cfg.subset_name}"
            if gname not in by_group:
                ids, h = sets[cfg.set_map[cs[0].eval_set]]
                by_group[gname] = Group(gname, cs[0].eval_set, cfg.set_map[cs[0].eval_set], ids, h, [], note="the panel edit's canary: the committed smaller edit and its draw-0 twin")
                groups.append(by_group[gname])
            have = {c.name for c in by_group[gname].cells}
            by_group[gname].cells.extend([c for c in cs if c.name not in have])
    reruns_added = add_store_reruns(groups, reruns, cfg, sets) if reruns else {}
    if cfg.only_groups is not None:
        unknown = set(cfg.only_groups) - {g.name for g in groups}
        assert not unknown, f"unknown groups {sorted(unknown)}; the groups are {[g.name for g in groups]}"
        groups = [g for g in groups if g.name in cfg.only_groups]
    # every store on E or E_lab carries the set's full reference set (no-op when tier 1 is in the launch);
    # a tier-5 store on D_unif carries its own full reference set as well
    # a tier-6 store carries four references only (importances, rounded_0, rounded_0.1, unmasked)
    # tier 7: the merge stores carry importances and unmasked, each panel store (and the panel edit's canary store) unmasked_delta, nothing more
    if t7:
        references_added = add_store_references(groups, cfg.run, cfg.draws, eval_sets=("E", "E_lab") + tuple(g.eval_set for g in groups if g.eval_set.startswith("panel_")),
                                                conditions=t7m.reference_conditions(cfg.subset_name))
    else:
        references_added = add_store_references(groups, cfg.run, cfg.draws, eval_sets=("E", "E_lab", "D_unif") if t5 else ("E", "E_lab"), conditions=t6m.REFERENCE_CONDITIONS if t6 else None)
    for name in {n for names in references_added.values() for n in names}:
        sources[name] = BuiltSource(None, {"kind": "reference"})
    canaries_added = add_store_canaries(groups, cfg.run, cfg.subset_name)
    if any(canaries_added.values()):
        sources.update(build_sources(marginal_canaries(cfg.run), caches, alive, None, None, module_to_c, master_seed=cfg.master_seed, log=log))
        log("[grid] canaries added per store (curve 1's union and its plain control at rung 2, draw 0): " + ", ".join(f"{k}: {len(v)}" for k, v in canaries_added.items() if v))
    if t6:  # the headline's fractional union at draw 0, rung 2, under its committed name (its source was built and held above)
        canaries_added = t6m.add_store_canary(groups, cfg.run)
        log("[grid] the tier-6 canary added per store (the headline union at rung 2, draw 0): " + ", ".join(f"{k}: {v}" for k, v in canaries_added.items() if v))
    cells = [c for g in groups for c in g.cells]
    if any(references_added.values()):
        log("[grid] references added per store: " + ", ".join(f"{k}: {len(v)}" for k, v in references_added.items() if v))
    log(f"[grid] {len(cells)} cells in {len(groups)} groups: " + ", ".join(f"{g.name} ({len(g.cells)} cells, {g.ids.shape[0]} seqs)" for g in groups))
    # what a tier-5 store is run with, all of it fixed before any forward pass: the partner tables, the
    # example positions held to the committed list, the comparison models' pre-flight gates, and each store's canary and gate
    t5_runs: dict[str, Any] = {}
    t5_summary: dict[str, Any] = {}
    if t5:
        t5_runs, t5_summary = _prepare_tier_5(model, cfg, groups, sources, sets, caches, t5_inputs, committed, reruns, cl_sets.n_group if cl_sets is not None else None, out_root, require_s9=require_s9, log=log)
        if reruns_added:
            log("[grid] re-run cells added per store under their committed names: " + ", ".join(f"{k}: {len(v)}" for k, v in reruns_added.items()))
    # 3. run every group, catching failures
    failures: list[dict[str, Any]] = []
    peak = 0.0
    for g in groups:
        if device.type == "cuda":
            torch.cuda.reset_peak_memory_stats()
        t0 = time.time()
        gdir = out_root / g.name
        try:
            store = run_cells(model, g.cells, g.ids, sources, job=f"{cfg.job_prefix}_{g.name}", run=cfg.run, out_dir=gdir, precision=cfg.precision, subbatch=min(cfg.subbatch, g.ids.shape[0]),
                              set_name=g.set_name, set_hash=g.set_hash, checkpoint_hashes=hashes, master_seed=cfg.master_seed, importance_chunk=cfg.chunk, resume=True,
                              on_subbatch=on_subbatch, log=log, ce_for_all=t5, tier5=t5_runs.get(g.name))
            g.result = {"ok": True, "seconds": time.time() - t0, "n_cells": len(g.cells), "n_rows": len(store.rows), "n_subbatches": store.n_subbatches}
            if t5 and t5_runs[g.name].checker is not None:
                g.result["tier_5_checks"] = t5_runs[g.name].checker.finish(store.rows)  # the whole table once more (a resumed launch checked only its own sub-batches)
        except Exception as e:  # noqa: BLE001
            from vpd_audit.tier5 import GateFailure

            if isinstance(e, GateFailure):  # a failed canary, gate, or launch-time assertion of tier 5 stops the launch; it is not one group's failure
                log(f"[grid] group {g.name}: STOP: {e}")
                raise
            g.result = {"ok": False, "seconds": time.time() - t0, "n_cells": len(g.cells), "error": f"{type(e).__name__}: {e}", "traceback": traceback.format_exc()[-3000:],
                        "families": sorted({c.family for c in g.cells})}
            failures.append({"group": g.name, **{k: v for k, v in g.result.items() if k != "traceback"}})
            gdir.mkdir(parents=True, exist_ok=True)
            with open(gdir / "error.txt", "w") as f:
                f.write(traceback.format_exc())
            log(f"[grid] group {g.name} FAILED: {type(e).__name__}: {e}")
        if device.type == "cuda":
            g.result["max_memory_allocated_gb"] = torch.cuda.max_memory_allocated() / 1e9
            peak = max(peak, g.result["max_memory_allocated_gb"])
            torch.cuda.empty_cache()
        log(f"[grid] group {g.name}: {g.result.get('ok')} in {g.result['seconds']:.1f} s" + (f", peak {g.result['max_memory_allocated_gb']:.1f} GB" if device.type == "cuda" else ""))
    # 4. the preconditions and the summary
    pre = preconditions(out_root, cells, groups, cfg, log=log)
    summary = {"config": {**asdict(cfg)}, "gpu": torch.cuda.get_device_name(device) if device.type == "cuda" else None, "torch_version": torch.__version__,
               "wall_clock_s": time.time() - t_all, "max_memory_allocated_gb": peak if device.type == "cuda" else None,
               "cell_counts": counts, "cells_enumerated": len(cells), "references_added_per_store": references_added, "cells_run": sum(g.result.get("n_cells", 0) for g in groups if g.result.get("ok")),
               "cells_failed": sum(g.result.get("n_cells", 0) for g in groups if not g.result.get("ok")), "failed_cell_types": sorted({fam for g in groups if not g.result.get("ok") for fam in g.result.get("families", [])}),
               "groups": {g.name: {"set": g.set_name, "n_sequences": int(g.ids.shape[0]), "note": g.note, **{k: v for k, v in g.result.items() if k != "traceback"}} for g in groups},
               "failures": failures, "adaptive": adaptive, "adaptive_rule_status": adaptive_status, "preconditions": pre, "alive_sha256": alive[cfg.run][1], "prose_named_files": pn_meta.get("files"),
               "checkpoint_hashes": hashes, "set_hashes": {k: v[1] for k, v in sets.items()}, "weight_norms": norms_meta, "rank_keys": rank_key_hashes, "rank_keys_vs_pre_reads": norms_check,
               "tier_4_vs_s7_pre_reads": s7_check, "canaries_added_per_store": canaries_added}
    if t5:  # only a tier-5 summary carries these keys
        summary.update({"tier_5_vs_s9_pre_reads": s9_check, "reruns_added_per_store": reruns_added, "tier_5": {**t5_summary, "checks": {g.name: g.result.get("tier_5_checks") for g in groups}}})
    if t6:  # only a tier-6 summary carries this key
        summary["tier_6"] = {"subset": cfg.subset_name, "sets_vs_committed": s11_check, "references": [c.name for c in t6m.reference_cells(cfg.run)], "canary": [c.name for c in t6m.canary_cells(cfg.run)],
                             "n_cells_selected_from_tier_3": sum(1 for c in cells if c.tier == 3)}
    if t7:  # only a tier-7 summary carries this key
        summary["tier_7"] = {"subset": cfg.subset_name, "sets": s12_check, "references": [c.name for c in cells if c.family == "reference"], "canaries": {k: [c.name for c in v] for k, v in t7_canaries.items()}}
    stem = summary_stem(cfg.subset_name)
    with open(out_root / f"{stem}.json", "w") as f:
        json.dump(summary, f, indent=2, sort_keys=True, default=str)
    with open(out_root / f"{stem}.md", "w") as f:
        f.write(format_summary(summary) + "\n")
    log(format_summary(summary))
    return summary


def summary_stem(subset_name: str | None) -> str:
    """A subset launch into a tier's root writes summary__<subset>.{json,md}, so several subsets of
    one tier keep their own launch records beside their stores (the earlier never-named subset launch wrote summary.*)."""
    return f"summary__{subset_name}" if subset_name else "summary"


def launch_title(tier: int, subset_name: str | None) -> str:
    """The header of a launch's summary on the paper's model (`GridConfig.job_title`), from its tier and subset; `vpd-audit resummarize`
    rebuilds a committed summary's title with it."""
    return f"Tier {tier} of the grid" + (f", the {subset_name} subset" if subset_name else "")


# ----------------------------------------------------------------------------- the preconditions from the tables


def cell_permitted(c: Cell) -> bool:
    """Whether the cell's masks are labelled m >= g (P3 asserted in masked_forward): the union and the two erases on any
    background, the importances reference of the donor-side pass, and the permitted reference conditions. Hard zero,
    rounded own g and the rounded references lie below g by construction (family_masks, rounded_mask, Condition.permitted)."""
    if c.family == "reference":
        return bool(CONDITION_BY_NAME[c.condition].permitted)  # type: ignore[index]
    if c.donor_side_reference is not None:
        return c.donor_side_reference == "importances"
    if c.family == "self_union" and c.own_round is not None:  # the binary self-merge, permitted when rounded at 0 only
        return OWN_ROUND_PERMITTED[c.own_round]
    if c.family == ROUNDED0_FAMILY:  # 1[g > 0] >= g, so every mask is at or above g
        return True
    return c.family in ("union", "soft_erase", "code_specific_soft", "level", "self_union", "partner_union")  # level: both halves at or above g; the per-text unions are unions


def _chain_key(c: Cell) -> tuple:
    # the control stays last (the analysis forms a chain's control key by replacing it); the ranked pair's key and end sit before it
    return (c.run, c.family, c.eval_set, c.donor_pool, c.tau, c.background, c.delta, c.draw if c.background == "uniform" else -1, c.rank_key, c.rank_end, c.control)


_reference_for = reference_for  # moved to cells.py: the loop needs it for the hard-zero rung 0


def preconditions(out_root: Path, cells: list[Cell], groups: list[Group], cfg: GridConfig, *, log: Any = print, strata: list[str] | None = None) -> dict[str, Any]:
    """P1 to P5 from the finished stores under `out_root`. `strata` (the labelled recipients' source per text) is read from the set's
    strata file in the cache unless given; `vpd-audit resummarize` gives it from the committed labelled-set manifest."""
    from vpd_audit.results import load_table

    rows = []
    cell_tables = []
    for g in groups:
        if not g.result.get("ok"):
            continue
        df = load_table(out_root / g.name)
        df["group"] = g.name
        rows.append(df)
        ct = pd.read_parquet(out_root / g.name / "cells.parquet")
        ct["group"] = g.name
        cell_tables.append(ct)
    if not rows:
        return {"available": False}
    df = pd.concat(rows, ignore_index=True)
    ct = pd.concat(cell_tables, ignore_index=True).set_index("cell")
    means = df.groupby("cell")["kl_mean"].mean()
    sigma_by_cell = {name: grp.sort_values("seq")["sigma"].to_numpy() for name, grp in df.groupby("cell")}  # the switched mass per sequence, for P4's exception
    by_name = {c.name: c for c in cells}

    def ref_name(c: Cell, cond: str) -> str:
        return f"{c.run}/{c.eval_set}/ref/{cond}"

    # chains: union / soft erase / hard-zero / rounded-own-g / code-specific, per (family, set, pool, tau, background, delta, draw-if-uniform, control)
    chains: dict[tuple, list[Cell]] = {}
    for c in cells:
        if c.family == "reference" or c.eval_set == "donors" or c.donor_side_reference or c.family == "external":  # external: no mask, so no chain
            continue
        # the binary self-merges share the fractional one's set and not its mask, so each is its own chain with its own
        # rung 0 here (an extension of the key for those cells only; _chain_key, which the frozen analysis.py imports, is unchanged)
        chains.setdefault(_chain_key(c) + ((("own_round", c.own_round),) if c.own_round is not None else ()), []).append(c)
    p1, p2, p4 = [], [], []
    for key, cs in chains.items():
        c0 = cs[0]
        ref = _reference_for(c0)
        refn = ref_name(c0, ref) if ref else None
        rung8 = [c for c in cs if c.rung == "8"]
        # P1 and P2 for the union chains (every draw's rung 8 under the uniform background, the one rung 8 otherwise)
        if c0.family == "union" and c0.control == "none" and refn in means.index:
            for c8 in rung8:
                if c8.name in means.index:
                    d = float(means[c8.name] - means[refn])
                    p1.append({"chain": c8.name.rsplit("/k", 1)[0] if c0.background != "uniform" else c8.name.rsplit("/r8", 1)[0], "rung_0": float(means[refn]), "rung_8": float(means[c8.name]), "difference": d, "pass": abs(d) > P1_MIN_DIFF})
                    unm = ref_name(c0, "unmasked" if c0.delta == "excluded" else "unmasked_delta")
                    imp = ref_name(c0, "importances")
                    p2.append({"chain": c8.name, "rung_8": float(means[c8.name]), "unmasked": float(means[unm]) if unm in means.index else None, "importances": float(means[imp]) if imp in means.index else None})
        # P4: the applied-mask digests along the chain (the sub-rungs included) are pairwise distinct wherever the sources
        # differ and equal wherever the sources are identical, with one exception: two sources that differ only in
        # subcomponents whose g is exactly 1 at every position of the set give identical masks under the union and the
        # soft erase, so a pair whose digests agree while its sources differ is a defect only if the switched mass
        # differs too. Rung 0 is the reference cell itself (_reference_for; rounded own g's is the rounded reference),
        # whose digest every non-empty rung must differ from and every empty rung must equal.
        present = [c for c in cs if c.name in ct.index]
        digests = {c.name: ct.loc[c.name, "mask_fp_cell"] for c in present}
        srcs = {c.name: ct.loc[c.name, "source_sha256"] for c in present}
        n_ons = {c.name: int(ct.loc[c.name, "n_on"]) for c in present}
        ref_digest = ct.loc[refn, "mask_fp_cell"] if (refn and refn in ct.index) else None
        inconsistent = []
        for a in present:
            for b in present:
                if a.name < b.name:
                    same_src, same_dig = srcs[a.name] == srcs[b.name], digests[a.name] == digests[b.name]
                    if same_dig != same_src:
                        sa, sb = sigma_by_cell.get(a.name), sigma_by_cell.get(b.name)
                        sigma_equal = sa is not None and sb is not None and sa.shape == sb.shape and bool(np.array_equal(sa, sb, equal_nan=True))
                        defect = (not same_dig) or (not sigma_equal)  # one source, two digests: always a defect; two sources, one digest: a defect only if the switched mass differs too
                        inconsistent.append({"a": a.name, "b": b.name, "sources_equal": bool(same_src), "digests_equal": bool(same_dig), "switched_mass_equal": bool(sigma_equal), "defect": bool(defect)})
        consistent = not any(x["defect"] for x in inconsistent)
        non_empty = [c.name for c in present if n_ons[c.name] > 0]
        distinct_from_ref = ref_digest is None or all(digests[n] != ref_digest for n in non_empty)
        empty_equal_ref = ref_digest is None or all(digests[c.name] == ref_digest for c in present if n_ons[c.name] == 0)
        p4.append({"chain": str(key), "n_cells": len(present), "n_empty_source_cells": len(present) - len(non_empty), "digests_equal_iff_sources_equal": bool(consistent),
                   "inconsistent_pairs": inconsistent, "n_inconsistent_pairs_not_defects": sum(1 for x in inconsistent if not x["defect"]),
                   "non_empty_rungs_distinct_from_rung_0": bool(distinct_from_ref), "empty_rungs_equal_rung_0": bool(empty_equal_ref),
                   "pass": bool(consistent and distinct_from_ref and empty_equal_ref), "rung_0_reference": ref, "rung_0_digest": ref_digest})
    # P3: no cell of a permitted family (masks labelled m >= g: the union, the two erases, the importances references) has
    # an entry below its label; the hard-zero rung-8 count is positive. The non-permitted families (hard zero, rounded
    # own g, the rounded references) lie below g by construction; their counts are reported, not judged.
    permitted_cells = [c.name for c in cells if c.name in ct.index and cell_permitted(c)]
    permitted_bad = int((ct.loc[permitted_cells, "n_below_label_total"].fillna(0) > 0).sum())
    not_permitted_below = int((ct.loc[[c.name for c in cells if c.name in ct.index and not cell_permitted(c)], "n_below_label_total"].fillna(0) > 0).sum())
    hz8 = {c.name: int(ct.loc[c.name, "n_below_label_total"]) for c in cells if c.is_hard_zero and c.rung == "8" and c.name in ct.index}
    p3 = {"permitted_cells": len(permitted_cells), "permitted_cells_with_entries_below_label": permitted_bad, "non_permitted_cells_with_entries_below_label": not_permitted_below,
          "hard_zero_rung_8_counts": hz8, "pass": permitted_bad == 0 and all(v > 0 for v in hz8.values())}
    # P5: the positive control of each hard-zero verdict curve, as far as it applies
    p5 = []
    if strata is None and cfg.strata_file and (env.SETS_DIR / cfg.strata_file).is_file():
        with open(env.SETS_DIR / cfg.strata_file) as f:
            strata = json.load(f)["strata"]
    for c in cells:
        if not c.is_hard_zero or c.control != "none" or c.rung in ("0",) or c.tau != 0.1 or c.delta != "included":
            continue
        if c.family in ("never_named_hard", "never_named_ranked"):  # post hoc and descriptive, no verdict curve, so no positive control
            continue
        if c.family == "code_leaning_hard":  # judged in the analysis under the per-chain rule; no launch prints a verdict the analysis would not
            continue
        if c.eval_set == "E_lab" and strata is not None:
            ctl_control = "complement" if c.family == "code_specific_hard" else "plain"
            ctl = Cell(c.run, c.family, c.eval_set, c.donor_pool, c.tau, c.background, c.delta, c.draw, c.rung, ctl_control, 2)
            if c.name in means.index and ctl.name in means.index and (c.rung in SUB_RUNGS or c.rung not in ("1", "2", "3")):
                sel = df[df.cell.isin([c.name, ctl.name])]
                pos = [i for i, s in enumerate(strata) if s == cfg.positive_stratum]
                dmg = sel[sel.seq.isin(pos)].groupby("cell")["kl_mean"].mean()
                p5.append({"curve": f"{c.family}/{c.donor_pool}/k{c.draw}/r{c.rung}", "curve_key": f"{c.family}/{c.eval_set}/{c.donor_pool}", "stratum": cfg.positive_stratum,
                           "erase": float(dmg.get(c.name, np.nan)), "control": float(dmg.get(ctl.name, np.nan)), "erase_exceeds_control": bool(dmg.get(c.name, 0) > dmg.get(ctl.name, 0))})
        elif c.eval_set == "E" and c.donor_pool == "D_unif" and c.rung in ("4", "5", "6", "7", "8") and c.name in means.index:
            p5.append({"curve": f"{c.family}/{c.donor_pool}/k{c.draw}/r{c.rung}", "curve_key": f"{c.family}/{c.eval_set}/{c.donor_pool}", "stratum": "E",
                       "damage": float(means[c.name]), "material": bool(means[c.name] > 0.05)})
    # P5 is printed as pass or fail per curve only (the positive control passes if every
    # rung j >= 4, and every sub-rung, passes); the per-cell numbers above stay in summary.json, which nobody opens before
    # the analysis code is frozen
    p5_curves: dict[str, dict[str, Any]] = {}
    for x in p5:
        ok = bool(x.get("erase_exceeds_control", x.get("material", False)))
        cur = p5_curves.setdefault(x["curve_key"], {"pass": True, "n_cells": 0})
        cur["pass"] = cur["pass"] and ok
        cur["n_cells"] += 1
    out = {"available": True, "P1": {"rule": f"|rung 8 - rung 0| > {P1_MIN_DIFF} for every union chain", "chains": p1, "n_pass": sum(x["pass"] for x in p1), "n": len(p1)},
           "P2": {"reported": p2}, "P3": p3, "P4": {"chains": p4, "n_pass": sum(x["pass"] for x in p4), "n": len(p4), "n_empty_source_cells": sum(x["n_empty_source_cells"] for x in p4),
                                                   "n_inconsistent_pairs_not_defects": sum(x["n_inconsistent_pairs_not_defects"] for x in p4),
                                                   "rule": "digests equal iff sources equal, except that two sources differing only in subcomponents whose g is exactly 1 at every position of the set "
                                                           "give identical masks under the union and the soft erase: a pair with equal digests and different sources is a defect only if the switched "
                                                           "mass differs too; every non-empty rung distinct from rung 0 (the reference cell, the rounded reference for rounded own g); "
                                                           "every empty rung equal to it"},
           "P5": {"as_far_as_it_applies": p5, "n_positive": sum(bool(x.get("erase_exceeds_control", x.get("material", False))) for x in p5), "n": len(p5), "per_curve": p5_curves,
                  "per_chain_rule_families": sorted({c.family for c in cells if c.family == "code_leaning_hard"})}}
    log(f"[grid] preconditions: P1 {out['P1']['n_pass']}/{out['P1']['n']}; P3 {p3['pass']}; P4 {out['P4']['n_pass']}/{out['P4']['n']}; P5 {p5_pass_fail(out['P5'])}")
    return out


def p5_pass_fail(p5: dict[str, Any]) -> str:
    """P5 as pass or fail per curve, nothing else of it."""
    curves = p5.get("per_curve", {})
    per_chain = "judged in the analysis under the per-chain rule" if p5.get("per_chain_rule_families") else ""  # for the code-leaning family
    if not curves:
        return per_chain or "no curve applies"
    return "; ".join(f"{k}: {'pass' if v['pass'] else 'FAIL'}" for k, v in sorted(curves.items())) + (f"; {', '.join(p5['per_chain_rule_families'])}: {per_chain}" if per_chain else "")


def format_summary(s: dict[str, Any]) -> str:
    L = [f"# {s['config'].get('job_title', 'The dry run of the grid')} on {s['config']['run']}: {s['gpu']}, {s['config']['precision']}, sub-batch {s['config']['subbatch']}, {s['config']['draws']} draws", ""]
    L.append(f"Wall clock {s['wall_clock_s']:.0f} s; peak GPU memory {s['max_memory_allocated_gb']:.1f} GB" if s["max_memory_allocated_gb"] is not None else f"Wall clock {s['wall_clock_s']:.0f} s (CPU)")
    L.append(f"Cells enumerated {s['cells_enumerated']}, run {s['cells_run']}, failed {s['cells_failed']}; failed cell types: {s['failed_cell_types'] or 'none'}")
    L.append("")
    L.append("| tier | cells | E-equivalent passes | optional |")
    L.append("|---|---|---|---|")
    quiet = TIER_5 in tuple(s["config"].get("tiers", ())) or TIER_6 in tuple(s["config"].get("tiers", ())) or TIER_7 in tuple(s["config"].get("tiers", ()))  # a tier-5 launch prints gates and assertions only, never a rise; tier 6 likewise; tier 7 likewise
    for t in ("tier_1", "tier_2", "tier_3", "tier_4", "tier_5", "tier_6", "tier_7"):
        if t in s["cell_counts"]:
            v = s["cell_counts"][t]
            L.append(f"| {t} | {v['cells']} | {v['E_equivalent_passes']} | {v['optional_cells']} |")
    L.append("")
    L.append(f"Adaptive rule (n_on alone, before any cell): {s['adaptive']['rule']}; inserted {s['adaptive']['insert'] or 'none'}")
    L.append("")
    L.append("| group | set | sequences | cells | ok | seconds | peak GB |")
    L.append("|---|---|---|---|---|---|---|")
    for name, g in s["groups"].items():
        L.append(f"| {name} | {g['set']} | {g['n_sequences']} | {g.get('n_cells')} | {g.get('ok')} | {g.get('seconds', 0):.1f} | {g.get('max_memory_allocated_gb', float('nan')):.1f} |")
    L.append("")
    pre = s["preconditions"]
    if pre.get("available"):
        L.append(f"P1 (union chains, |rung 8 - rung 0| > 0.01): {pre['P1']['n_pass']}/{pre['P1']['n']}" + (" (pass count only: a tier-5 launch prints no rise; the values are in the summary's JSON, read by the frozen analysis)" if quiet else ""))
        for x in ([] if quiet else pre["P1"]["chains"]):
            L.append(f"- {x['chain']}: rung 0 {x['rung_0']:.4f}, rung 8 {x['rung_8']:.4f}, difference {x['difference']:+.4f} -> {'pass' if x['pass'] else 'FAIL'}")
        if not quiet:
            L.append(f"P2 (reported): rung 8 against unmasked and importances: " + "; ".join(f"{x['chain'].split('/', 2)[-1]}: {x['rung_8']:.4f} vs {x['unmasked']} / {x['importances']}" for x in pre["P2"]["reported"][:6]) + (" ..." if len(pre["P2"]["reported"]) > 6 else ""))
        L.append(f"P3: permitted-family cells with entries below their label {pre['P3']['permitted_cells_with_entries_below_label']} of {pre['P3']['permitted_cells']}; hard-zero rung-8 counts positive: {all(v > 0 for v in pre['P3']['hard_zero_rung_8_counts'].values())} -> {'pass' if pre['P3']['pass'] else 'FAIL'} (non-permitted cells below g, expected: {pre['P3']['non_permitted_cells_with_entries_below_label']})")
        L.append(f"P4 (digests equal iff sources equal, an equal-digest pair with different sources a defect only if its switched mass differs too; non-empty rungs distinct from rung 0, empty rungs equal to it): "
                 f"{pre['P4']['n_pass']}/{pre['P4']['n']} chains; empty-source cells {pre['P4']['n_empty_source_cells']}; equal-digest pairs excused by equal switched mass {pre['P4']['n_inconsistent_pairs_not_defects']}")
        L.append(f"P5 (positive controls, pass or fail per curve, values withheld until the analysis code is frozen): {p5_pass_fail(pre['P5'])}")
    if s.get("references_added_per_store") and any(s["references_added_per_store"].values()):
        L.append("References added per store: " + ", ".join(f"{k}: {len(v)}" for k, v in s["references_added_per_store"].items() if v))
    if s.get("tier_5"):  # the launch's gates and assertions, equality and counts only (the D_unif gate gives its eight differences, as fixed in advance)
        t5s, v9 = s["tier_5"], s.get("tier_5_vs_s9_pre_reads", {})
        L.append(f"Tier 5, the {t5s.get('subset')} subset: named sets against the label-only tables: {'asserted ' + str(v9.get('counts')) if v9.get('asserted') else 'NOT asserted'}; "
                 f"example positions: {'equal to the committed list' if t5s.get('example_positions', {}).get('asserted') else 'not asserted'}; re-run cells added: {({k: len(v) for k, v in s.get('reruns_added_per_store', {}).items()}) or 'none'}")
        if t5s.get("external_models"):
            L.append(f"Comparison models' pre-flight gates: {'pass' if t5s['external_models']['gates_pass'] else 'FAIL'} ({', '.join(f'{k} at {v['resolved_commit'][:12]}' for k, v in t5s['external_models']['models'].items())})")
        for name, chk in (t5s.get("checks") or {}).items():
            if chk is None:
                L.append(f"- {name}: canary and gate NOT checked (no committed stores given, or the store failed)")
                continue
            line = f"- {name}: canary {'pass' if chk['canary_pass'] else 'FAIL'}: {chk['canary_cells']} cells bitwise equal to the committed stores over {chk['canary_pairs_compared']} (cell, text) pairs"
            if chk.get("d_unif_gate"):
                gate = chk["d_unif_gate"]
                line += f"; D_unif gate {'pass' if gate['pass'] else 'FAIL'} within {gate['tolerance']} nats: " + ", ".join(f"k{v['draw']}: {v['difference']:+.5f}" for v in sorted(gate["rows"].values(), key=lambda v: v["draw"]) if v["difference"] is not None)
            L.append(line)
    if s.get("tier_6"):  # the launch's assertions, equality and counts only
        t6s = s["tier_6"]
        chk = t6s.get("sets_vs_committed", {})
        L.append(f"Tier 6, the {t6s.get('subset')} subset: sets against their committed twins: {'asserted ' + str(chk.get('counts')) if chk.get('asserted') else 'NOT asserted'}; "
                 f"the self-merge's sets against the label-only tables: {'asserted' if (chk.get('self_merge_vs_s9_pre_reads') or {}).get('asserted') else 'NOT asserted'}; "
                 f"{t6s.get('n_cells_selected_from_tier_3')} cells selected from tier 3; references {len(t6s.get('references', []))}; canary {t6s.get('canary')}")
    if s.get("tier_7"):  # the launch's assertions, equality and counts only
        t7s = s["tier_7"]
        chk = t7s.get("sets", {})
        L.append(f"Tier 7, the {t7s.get('subset')} subset: sets against the label-only table and their committed twins: {'asserted ' + str(chk.get('counts')) if chk.get('asserted') else 'NOT asserted'}; "
                 f"canaries {sum(len(v) for v in t7s.get('canaries', {}).values())} ({', '.join(t7s.get('canaries', {}))})")
    if s.get("d_b_two_paths"):
        d = s["d_b_two_paths"]
        L.append(f"d_b two-path check: {d['n_cells_checked']} hard-zero cells, {d['n_sequence_checks']} (cell, sequence, tau_q) checks with t* > 0; "
                 f"largest |column - recomputed| / bound {d['max_ratio']:.4f} (must be <= 1) -> {'pass' if d['pass'] else 'FAIL'}")
    if s["failures"]:
        L.append("")
        L.append("Failures:")
        for fl in s["failures"]:
            L.append(f"- {fl['group']}: {fl['error']} (families {fl.get('families')})")
    return "\n".join(L)
