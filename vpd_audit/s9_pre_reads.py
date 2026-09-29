"""The label-only tables the tier-5 GPU run will assert against, fixed before any forward
pass, from the label caches alone (CPU, where the main run's caches live: the Modal volume).

The tier-5 run merges code donors into code texts, with general and prose donors into the same texts as contrasts, and re-measures the
self-merge (a text merged with the pieces its own 512 tokens name). Same-kind donors share pieces with each other and with the
text, so at the same donor count they name fewer pieces and move less mask. For each donor pool (D_code, D_unif, D_prose), each
draw, and each merge size (1, 8, 16, 32, 64 tokens; 1, 4, 16, 64 texts; the whole pool, once; no adaptive insertion), with the
donor schedule and seeds of `sources.donor_set` (so D_unif's draws are the headline's own): n_on in total and per matrix, the
SHA-256 of the named set, the distinct donor documents behind it (the majority documents of `s9_checks.document_index`; for D_unif, whose stream the
authors shuffled by row, distinct donor rows), the shares of the named set inside the code-leaning group G_0.9 and inside the
prose-leaning group (s <= 0.10), and on each source of E_lab the mean switched mass (`pre_reads.sigma_from_sums`)
and the mean share of the named set that the receiving text itself names at some position. For the self-merge: for every text
of E, E_lab, and D_unif, the number of pieces its own positions name above 0.1, its switched mass on itself, its named set's
SHA-256, and per set the SHA-256 of the per-text named sets taken together.

    uv run vpd-audit s9-pre-reads                  (where the caches live; on Modal: modal_app.py::s9_label_tables)
    uv run vpd-audit s9-pre-reads --finish         (locally, on the pulled directory: the checks against the committed stores)
"""

from __future__ import annotations

import hashlib
import json
import time
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from vpd_audit import env
from vpd_audit.constants import SEQ_LEN
from vpd_audit.s9_checks import S9_DIR_NAME, S9Inputs, inputs_document_index, leaning_groups_full, load_cache_checked, paper_inputs

TAU = 0.1
MERGE_POOLS = ("D_code", "D_unif", "D_prose")
MERGE_RUNGS = ("1", "2", "2a", "2b", "3", "4", "5", "6", "7", "8")  # 1, 8, 16, 32, 64 tokens; 1, 4, 16, 64 texts; the whole pool. No 5a, 6a
SELF_SETS = ("E", "E_lab", "D_unif")
ROW_IS_DOCUMENT = ("D_unif",)  # the authors shuffled that stream by row: a donor document is a donor row
COMMITTED_UNION_FAMILIES = ("union", "soft_erase", "hard_zero")  # families whose recorded source is the donors' union itself


def pre_reads_dir(run: str = "main") -> Path:
    return env.PROJECT_ROOT / "results" / "grid" / "pre_reads" / run / S9_DIR_NAME


def n_donor_documents(index: pd.DataFrame, pool: str, sequences: tuple[int, ...]) -> int:
    """The distinct donor documents behind a donor set: distinct (source, majority document) over its rows; distinct rows for D_unif."""
    if pool in ROW_IS_DOCUMENT:
        return len(set(sequences))
    g = index[(index["set"] == pool) & (index["row"].isin(list(sequences)))]
    assert len(g) == len(set(sequences)), f"{pool}: the document index holds {len(g)} of the {len(set(sequences))} donor rows"
    return int(len(set(zip(g["source"], g["majority_document"]))))


def merge_sets(pool: str, cache: Any, index: pd.DataFrame, G: np.ndarray, P: np.ndarray, *, draws: int, master_seed: int) -> tuple[list[dict[str, Any]], list[np.ndarray]]:
    """One pool's named sets over the draws and merge sizes, with their label-only columns; the whole pool is one set (draw 0)."""
    from vpd_audit.sources import RUNG_SCHEDULE, donor_set, n_on, source_hash, union_source

    rows, rhos = [], []
    for rung in MERGE_RUNGS:
        unit, count = RUNG_SCHEDULE[rung]
        for k in range(draws if unit != "pool" else 1):
            ds = donor_set(pool, cache.n_sequences, k, rung, master_seed)
            rho = union_source(cache, ds.positions, TAU)
            n = n_on(rho, cache.module_to_c, cache.offsets)
            total = n.pop("total")
            rows.append({"pool": pool, "draw": k, "rung": rung, "donor_unit": unit, "donor_count": count if count is not None else cache.n_sequences, "n_donor_positions": ds.size, "n_donor_rows": len(ds.sequences),
                         "n_donor_documents": n_donor_documents(index, pool, ds.sequences), "n_on": total, "source_sha256": source_hash(rho),
                         "share_in_code_leaning": float((rho & G).sum() / total) if total else float("nan"), "share_in_prose_leaning": float((rho & P).sum() / total) if total else float("nan"),
                         "n_in_code_leaning": int((rho & G).sum()), "n_in_prose_leaning": int((rho & P).sum()), **{f"n_on__{m}": v for m, v in n.items()}})
            rhos.append(rho)
    return rows, rhos


def own_named(cache: Any) -> np.ndarray:
    """(N, n_sub) bool: the pieces each text's own positions name above 0.1 (strict, float32, as the union source compares)."""
    from vpd_audit.code_leaning import per_document_counts

    return per_document_counts(cache, TAU) > 0


def sigma_by_source(g_sums: np.ndarray, own: np.ndarray, strata: list[str], rows: list[dict[str, Any]], rhos: list[np.ndarray]) -> pd.DataFrame:
    """Per named set and source of the receiving set: the mean switched mass sigma and the mean share of the named set that the
    receiving text itself names at some position."""
    from vpd_audit.pre_reads import sigma_from_sums

    R = np.stack(rhos, axis=1)  # (n_sub, M)
    sigma = sigma_from_sums(g_sums, R)  # (N, M)
    sizes = R.sum(axis=0).astype(np.float64)
    inter = (own.astype(np.float32) @ R.astype(np.float32)).astype(np.float64)  # counts below 2^24: exact in float32
    with np.errstate(divide="ignore", invalid="ignore"):
        share = np.where(sizes[None, :] > 0, inter / np.where(sizes > 0, sizes, 1.0)[None, :], np.nan)
    arr = np.asarray(strata)
    out = []
    for j, r in enumerate(rows):
        for s in dict.fromkeys(strata):
            m = arr == s
            out.append({"pool": r["pool"], "draw": r["draw"], "rung": r["rung"], "n_on": r["n_on"], "source": s, "n_texts": int(m.sum()), "mean_sigma": float(sigma[m, j].mean()), "mean_share_named_by_receiving_text": float(share[m, j].mean())})
    return pd.DataFrame(out)


def self_merge(name: str, g_sums: np.ndarray, own: np.ndarray, strata: list[str] | None) -> tuple[pd.DataFrame, str]:
    """Per text: the pieces its own positions name, its switched mass on itself (|rho_b| - (1/T) sum over rho_b and t of g), and its
    named set's SHA-256; per set, the SHA-256 of the (N, n_sub) boolean matrix of the per-text named sets."""
    from vpd_audit.sources import source_hash

    n = own.sum(axis=1).astype(np.int64)
    sigma = n.astype(np.float64) - np.einsum("ij,ij->i", g_sums, own.astype(np.float64)) / float(SEQ_LEN)
    df = pd.DataFrame({"set": name, "seq": np.arange(own.shape[0]), "source": strata if strata is not None else [""] * own.shape[0], "n_on": n, "sigma_self": sigma, "source_sha256": [source_hash(own[b]) for b in range(own.shape[0])]})
    return df, hashlib.sha256(np.ascontiguousarray(own, dtype=np.bool_).tobytes()).hexdigest()


def run_s9_pre_reads(run: str, out_dir: Path, *, inputs: S9Inputs | None = None, log: Any = print) -> dict[str, Any]:
    from vpd_audit.donors import donors_dir
    from vpd_audit.pre_reads import per_sequence_g_sums
    from vpd_audit.results import code_commits
    from vpd_audit.sources import source_hash

    t0 = time.time()
    out_dir = Path(out_dir)
    assert out_dir.name == S9_DIR_NAME, f"the tier-5 pre-reads write into a directory named {S9_DIR_NAME!r} only, not {out_dir}"
    inp = inputs or paper_inputs(run)
    out_dir.mkdir(parents=True, exist_ok=True)
    records: dict[str, Any] = {}
    alive_vec = np.load(donors_dir() / f"alive_{inp.pool_map['D_unif']}_{inp.run}.npy")
    index = inputs_document_index(inp)
    code, records["D_code"] = load_cache_checked(inp, "D_code")
    prose, records["D_prose"] = load_cache_checked(inp, "D_prose")
    lg = leaning_groups_full(code, prose, alive_vec, inp.master_seed)
    G, P = lg["G"], lg["P"]
    del lg
    log(f"[s9 pre-reads] {inp.run}: G_0.9 has {int(G.sum())} members, the prose-leaning group {int(P.sum())}; {time.time() - t0:.0f} s")
    rows: list[dict[str, Any]] = []
    rhos: list[np.ndarray] = []
    for pool, cache in (("D_code", code), ("D_prose", prose)):
        r_, h_ = merge_sets(pool, cache, index, G, P, draws=inp.draws, master_seed=inp.master_seed)
        rows, rhos = rows + r_, rhos + h_
    del code, prose
    d_unif, records["D_unif"] = load_cache_checked(inp, "D_unif")
    r_, h_ = merge_sets("D_unif", d_unif, index, G, P, draws=inp.draws, master_seed=inp.master_seed)
    rows, rhos = rows + r_, rhos + h_
    order = sorted(range(len(rows)), key=lambda i: (MERGE_POOLS.index(rows[i]["pool"]), MERGE_RUNGS.index(rows[i]["rung"]), rows[i]["draw"]))
    rows, rhos = [rows[i] for i in order], [rhos[i] for i in order]
    merge = pd.DataFrame(rows)
    merge.to_csv(out_dir / "merge_sets.csv", index=False)
    log(f"[s9 pre-reads] {len(merge)} named sets over {MERGE_POOLS}; {time.time() - t0:.0f} s")
    # the self-merge, one set at a time; E_lab's sums and named sets also give the merges' switched mass by source
    with open(env.SETS_DIR / inp.strata_file) as f:
        strata = [str(s) for s in json.load(f)["strata"]]
    selfs, set_hashes = [], {}
    sigma_t = None
    for key in SELF_SETS:
        cache = d_unif if key == "D_unif" else None
        if cache is None:
            cache, records[key] = load_cache_checked(inp, key)
        g_sums, own = per_sequence_g_sums(cache), own_named(cache)
        if key == "E_lab":
            assert len(strata) == cache.n_sequences
            sigma_t = sigma_by_source(g_sums, own, strata, rows, rhos)
        df, set_hashes[key] = self_merge(key, g_sums, own, strata if key == "E_lab" else None)
        selfs.append(df)
        log(f"[s9 pre-reads] self-merge on {key}: {len(df)} texts, mean n_on {df['n_on'].mean():.1f}, mean switched mass {df['sigma_self'].mean():.2f}; {time.time() - t0:.0f} s")
        del g_sums, own, cache
    assert sigma_t is not None
    sigma_t.to_csv(out_dir / "merge_sigma_by_source.csv", index=False)
    self_t = pd.concat(selfs, ignore_index=True)
    self_t.to_parquet(out_dir / "self_merge_sets.parquet", index=False)
    files = ["merge_sets.csv", "merge_sigma_by_source.csv", "self_merge_sets.parquet", "manifest.json", "summary.md"]
    manifest = {"run": inp.run, "draws": inp.draws, "master_seed": inp.master_seed, "tau": TAU, "merge_rungs": list(MERGE_RUNGS), "commits": code_commits(), "seconds": time.time() - t0, "caches": records,
                "alive_sha256": source_hash(alive_vec), "code_leaning_group": {"n_members": int(G.sum()), "sha256": source_hash(G)}, "prose_leaning_group": {"n_members": int(P.sum()), "sha256": source_hash(P)},
                "self_merge_sets_sha256": set_hashes, "synthetic_documents": inp.synthetic_document_rows, "document_index_sha256": hashlib.sha256(index.to_csv(index=False).encode()).hexdigest(),
                "tables": {"merge_sets": int(len(merge)), "merge_sigma_by_source": int(len(sigma_t)), "self_merge_sets": int(len(self_t))}, "files": files}
    with open(out_dir / "manifest.json", "w") as f:
        json.dump(manifest, f, indent=2, sort_keys=True, default=str)
    text = format_summary(manifest, merge, sigma_t, self_t)
    with open(out_dir / "summary.md", "w") as f:
        f.write(text + "\n")
    log(text)
    log(f"[s9 pre-reads] done in {time.time() - t0:.0f} s -> {out_dir}")
    return {"run": inp.run, "seconds": time.time() - t0, "n_named_sets": int(len(merge)), "self_merge_sets_sha256": set_hashes, "out_dir": str(out_dir)}


def format_summary(manifest: dict[str, Any], merge: pd.DataFrame, sigma_t: pd.DataFrame, self_t: pd.DataFrame) -> str:
    L = [f"# Label-only tables for the tier-5 run ({manifest['run']} run)", "",
         f"Named sets at tau = {TAU:g} from the donor schedule and seeds of `sources.donor_set`; G_0.9 has {manifest['code_leaning_group']['n_members']} members, the prose-leaning group {manifest['prose_leaning_group']['n_members']}.", "",
         "## The merges: means over the draws", "", "| pool | rung | donors | draws | n_on | min | max | donor documents | in G_0.9 | in the prose-leaning group |", "|---|---|---|---|---|---|---|---|---|---|"]
    for (pool, rung), g in merge.groupby(["pool", "rung"], sort=False):
        L.append(f"| {pool} | {rung} | {int(g['donor_count'].iloc[0])} {g['donor_unit'].iloc[0]} | {len(g)} | {g['n_on'].mean():.1f} | {int(g['n_on'].min())} | {int(g['n_on'].max())} | {g['n_donor_documents'].mean():.1f} | "
                 f"{g['share_in_code_leaning'].mean():.4f} | {g['share_in_prose_leaning'].mean():.4f} |")
    L += ["", "## On each source of E_lab: the mean switched mass and the mean share of the named set the receiving text itself names (means over the draws)", ""]
    sources = list(dict.fromkeys(sigma_t["source"]))
    L += ["| pool | rung | " + " | ".join(f"sigma, {s}" for s in sources) + " | " + " | ".join(f"own share, {s}" for s in sources) + " |", "|---|---|" + "---|" * (2 * len(sources))]
    for (pool, rung), g in sigma_t.groupby(["pool", "rung"], sort=False):
        m = g.groupby("source", sort=False)[["mean_sigma", "mean_share_named_by_receiving_text"]].mean()
        L.append(f"| {pool} | {rung} | " + " | ".join(f"{m.loc[s, 'mean_sigma']:.1f}" for s in sources) + " | " + " | ".join(f"{m.loc[s, 'mean_share_named_by_receiving_text']:.4f}" for s in sources) + " |")
    L += ["", "## The self-merge", "", "| set | source | texts | mean n_on | min | max | mean switched mass on itself | SHA-256 of the set's named sets |", "|---|---|---|---|---|---|---|---|"]
    for (name, source), g in self_t.groupby(["set", "source"], sort=False):
        L.append(f"| {name} | {source or 'all'} | {len(g)} | {g['n_on'].mean():.1f} | {int(g['n_on'].min())} | {int(g['n_on'].max())} | {g['sigma_self'].mean():.2f} | {manifest['self_merge_sets_sha256'][name][:16]} |")
    return "\n".join(L)


# ----------------------------------------------------------------------------- the local finishing step


def finish_s9_pre_reads(s9_dir: Path, *, stores_root: Path, log: Any = print) -> dict[str, Any]:
    """From the pulled tables, against the committed cell tables (label-only columns: source hash and n_on): (1) every named set
    that a committed cell also names (the donors' union of the same pool, draw, and rung at tau = 0.1: curve 1 for D_unif, so the
    draws are the headline's own; the code-donor chains on E_lab for D_code) equals it by hash and count; (2) the check fixed in advance:
    for the eight rows of D_unif that are the one-text donors of draws 0 to 7, the self-merge's count equals the committed n_on of
    curve 1 at one text, and its hash the committed source hash. Writes verification.json; any failure stops the command."""
    from vpd_audit.sources import donor_set

    s9_dir, stores_root = Path(s9_dir), Path(stores_root)
    with open(s9_dir / "manifest.json") as f:
        manifest = json.load(f)
    merge = pd.read_csv(s9_dir / "merge_sets.csv", dtype={"rung": str})
    self_t = pd.read_parquet(s9_dir / "self_merge_sets.parquet")
    cols = ["cell", "family", "eval_set", "donor_pool", "tau", "background", "delta", "draw", "rung", "control", "level", "donor_side_reference", "replicate", "source_sha256", "n_on"]
    # the stores of tiers 1 and 2 have no `level` or `replicate` column (added with later tiers): absent means no level, replicate 0
    committed = pd.concat([pd.read_parquet(p).reindex(columns=cols) for p in sorted(stores_root.glob("tier*/*/cells.parquet"))], ignore_index=True)
    committed["replicate"] = committed["replicate"].fillna(0)
    c = committed[committed["family"].isin(COMMITTED_UNION_FAMILIES) & (committed["control"] == "none") & (committed["tau"] == TAU) & committed["level"].isna() & committed["donor_side_reference"].isna() & (committed["replicate"] == 0)
                  & committed["eval_set"].isin(["E", "E_lab"])]
    n_compared, mismatched, per_pool = 0, [], {}
    for _, r in merge.iterrows():
        hit = c[(c["donor_pool"] == r["pool"]) & (c["rung"].astype(str) == r["rung"]) & (c["draw"] == r["draw"])]
        for _, h in hit.iterrows():
            n_compared += 1
            per_pool[r["pool"]] = per_pool.get(r["pool"], 0) + 1
            if h["source_sha256"] != r["source_sha256"] or int(h["n_on"]) != int(r["n_on"]):
                mismatched.append(h["cell"])
    curve1 = c[(c["family"] == "union") & (c["eval_set"] == "E") & (c["donor_pool"] == "D_unif") & (c["background"] == "r0") & (c["delta"] == "excluded")]
    headline = {"rungs_compared": sorted(set(curve1["rung"].astype(str)) & set(merge["rung"])), "n_cells": int(curve1[curve1["rung"].astype(str).isin(set(merge["rung"]))]["cell"].nunique())}
    one_text = []
    du = self_t[self_t["set"] == "D_unif"].set_index("seq")
    for k in range(int(manifest["draws"])):
        ds = donor_set("D_unif", int(len(du)), k, "4", int(manifest["master_seed"]))
        assert len(ds.sequences) == 1
        cell = curve1[(curve1["rung"].astype(str) == "4") & (curve1["draw"] == k)]
        assert len(cell) == 1, f"no single committed curve-1 cell at one text, draw {k}"
        cell = cell.iloc[0]
        row = du.loc[ds.sequences[0]]
        one_text.append({"draw": k, "donor_row": int(ds.sequences[0]), "self_merge_n_on": int(row["n_on"]), "committed_n_on": int(cell["n_on"]), "equal": bool(int(row["n_on"]) == int(cell["n_on"])), "hash_equal": bool(row["source_sha256"] == cell["source_sha256"])})
    out = {"run": manifest["run"], "s9_commit": manifest["commits"], "against_committed": {"n_named_sets": int(len(merge)), "n_compared_with_a_committed_cell": n_compared, "compared_per_pool": per_pool, "mismatched_cells": mismatched, "headline": headline},
           "one_text_donors": one_text, "pass": bool(n_compared > 0 and not mismatched and all(o["equal"] and o["hash_equal"] for o in one_text))}
    with open(s9_dir / "verification.json", "w") as f:
        json.dump(out, f, indent=2, sort_keys=True, default=str)
    log(f"[s9 pre-reads finish] {'pass' if not mismatched and n_compared else 'FAIL'}: {n_compared} committed cells name a set of merge_sets.csv ({per_pool}); {len(mismatched)} differ by hash or count")
    log(f"[s9 pre-reads finish] {'pass' if all(o['equal'] and o['hash_equal'] for o in one_text) else 'FAIL'}: the one-text donors' self-merge counts against curve 1 at one text: " + ", ".join(f"k{o['draw']} row {o['donor_row']}: {o['self_merge_n_on']} = {o['committed_n_on']}" for o in one_text))
    assert out["pass"], out
    return out
