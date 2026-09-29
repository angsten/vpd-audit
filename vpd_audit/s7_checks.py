"""Two recorded claims about tier 3 that were computed from parquet stores and that the statistics check could not reach,
recomputed from the committed stores (CPU, no model, no cache).

(a) The level cell: at level s = 0.5 with the never-named set at its labels, every one of the 1,024 texts sits below its own
    importances-as-masks divergence; the median and the tenth-to-ninetieth range of the paired difference
    (results/grid/main/tier3/E__levels/per_sequence.parquet, the level cell against the importances reference of the same store).
(b) The donor side: the donor-side table's means and ranges over the eight draws at rungs 4 and 7, and the per-draw rung-4
    values (results/grid/main/tier3/donors_D_unif_k{k}_r{4,7}/), with the same union on E from tier 1's store beside them.

    uv run python -m vpd_audit.s7_checks            (writes results/grid/analysis/main/s7_checks/)

Each computed number is printed beside the claimed one and compared at the precision the claim was printed with.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from vpd_audit import env
from vpd_audit.results import code_commits

STORES = env.PROJECT_ROOT / "results" / "grid" / "main"
OUT = env.PROJECT_ROOT / "results" / "grid" / "analysis" / "main" / "s7_checks"
LEVEL_CELL = "main/E/level/D_unif/tau0.1/r0/excl/k0/r8/s0.5"
IMPORTANCES = "main/E/ref/importances"
DRAWS = 8
# the claimed values as they were first printed, with the decimals they were printed with
CLAIMED_A = {"n_texts": 1024, "n_texts_below": 1024, "median_paired_difference": (-0.138, 3), "p10_paired_difference": (-0.176, 3), "p90_paired_difference": (-0.068, 3),
             "mean_level": (0.2126, 4), "mean_importances": (0.3417, 4)}
CLAIMED_B = {("4", "union_on_donors"): {"mean": 1.47, "min": 0.29, "max": 2.48}, ("4", "donors_own_importances"): {"mean": 0.34, "min": 0.15, "max": 0.53},
             ("4", "donors_own_rounded"): {"mean": 0.31, "min": 0.16, "max": 0.48}, ("4", "same_union_on_E"): {"mean": 0.83},
             ("7", "union_on_donors"): {"mean": 1.30, "min": 1.25, "max": 1.34}, ("7", "donors_own_importances"): {"mean": 0.34, "min": 0.31, "max": 0.37},
             ("7", "donors_own_rounded"): {"mean": 0.32, "min": 0.29, "max": 0.34}, ("7", "same_union_on_E"): {"mean": 1.29}}
CLAIMED_B_RUNG4 = {"union_on_donors": [1.54, 1.38, 1.58, 0.29, 2.01, 2.48, 1.35, 1.11], "donors_own_importances": [0.36, 0.20, 0.53, 0.15, 0.34, 0.25, 0.44, 0.44]}


def _agrees(computed: float, claimed: float, decimals: int) -> bool:
    return bool(round(float(computed), decimals) == round(float(claimed), decimals))


def check_a(stores: Path = STORES) -> dict[str, Any]:
    ps = pd.read_parquet(stores / "tier3" / "E__levels" / "per_sequence.parquet", columns=["cell", "seq", "kl_mean"])
    lvl = ps[ps.cell == LEVEL_CELL].sort_values("seq")
    ref = ps[ps.cell == IMPORTANCES].sort_values("seq")
    assert len(lvl) == len(ref) and np.array_equal(lvl.seq.to_numpy(), ref.seq.to_numpy()) and lvl.seq.is_unique
    a, b = lvl.kl_mean.to_numpy(np.float64), ref.kl_mean.to_numpy(np.float64)
    d = a - b
    computed = {"n_texts": int(d.size), "n_texts_below": int((d < 0).sum()), "n_texts_equal": int((d == 0).sum()), "n_texts_above": int((d > 0).sum()), "median_paired_difference": float(np.median(d)),
                "p10_paired_difference": float(np.percentile(d, 10)), "p90_paired_difference": float(np.percentile(d, 90)), "max_paired_difference": float(d.max()), "min_paired_difference": float(d.min()),
                "mean_paired_difference": float(d.mean()), "mean_level": float(a.mean()), "mean_importances": float(b.mean())}
    rows = []
    for k, claim in CLAIMED_A.items():
        c, dec = (claim, 0) if isinstance(claim, int) else claim
        rows.append({"quantity": k, "claimed": c, "computed": computed[k], "decimals": dec, "agrees": _agrees(computed[k], c, dec)})
    return {"level_cell": LEVEL_CELL, "reference": IMPORTANCES, "store": "results/grid/main/tier3/E__levels/per_sequence.parquet", "computed": computed, "comparison": rows,
            "every_text_below": bool((d < 0).all()), "all_agree": bool(all(r["agrees"] for r in rows))}


def check_b(stores: Path = STORES) -> tuple[pd.DataFrame, pd.DataFrame, dict[str, Any]]:
    e = pd.read_parquet(stores / "tier1" / "E" / "per_sequence.parquet", columns=["cell", "kl_mean"])
    per_draw = []
    for r in ("4", "7"):
        for k in range(DRAWS):
            d = stores / "tier3" / f"donors_D_unif_k{k}_r{r}"
            ps = pd.read_parquet(d / "per_sequence.parquet", columns=["cell", "seq", "kl_mean"])
            cells = pd.read_parquet(d / "cells.parquet", columns=["cell", "n_on"])
            base = f"main/donors/union/D_unif/tau0.1/r0/excl/k{k}/r{r}"
            means = ps.groupby("cell")["kl_mean"].agg(["mean", "size"])
            assert set(means.index) == {base, f"{base}/donorref-importances", f"{base}/donorref-rounded"} and means["size"].nunique() == 1
            on_e = e[e.cell == f"main/E/union/D_unif/tau0.1/r0/excl/k{k}/r{r}"]["kl_mean"]
            assert len(on_e) == 1024
            per_draw.append({"rung": r, "draw": k, "n_donor_sequences": int(means["size"].iloc[0]), "n_on": int(cells[cells.cell == base]["n_on"].iloc[0]), "union_on_donors": float(means.loc[base, "mean"]),
                             "donors_own_importances": float(means.loc[f"{base}/donorref-importances", "mean"]), "donors_own_rounded": float(means.loc[f"{base}/donorref-rounded", "mean"]),
                             "same_union_on_E": float(on_e.mean())})
    per_draw_df = pd.DataFrame(per_draw)
    rows = []
    for (r, col), claim in CLAIMED_B.items():
        x = per_draw_df[per_draw_df.rung == r][col].to_numpy(np.float64)
        comp = {"mean": float(x.mean()), "min": float(x.min()), "max": float(x.max())}
        for stat, c in claim.items():
            rows.append({"rung": r, "column": col, "statistic": f"{stat} over draws", "claimed": c, "computed": comp[stat], "decimals": 2, "agrees": _agrees(comp[stat], c, 2)})
    for col, claims in CLAIMED_B_RUNG4.items():
        for k, c in enumerate(claims):
            x = float(per_draw_df[(per_draw_df.rung == "4") & (per_draw_df.draw == k)][col].iloc[0])
            rows.append({"rung": "4", "column": col, "statistic": f"draw {k}", "claimed": c, "computed": x, "decimals": 2, "agrees": _agrees(x, c, 2)})
    comparison = pd.DataFrame(rows)
    return per_draw_df, comparison, {"all_agree": bool(comparison.agrees.all()), "n_compared": int(len(comparison)), "n_disagree": int((~comparison.agrees).sum())}


def main(out: Path = OUT) -> int:
    out.mkdir(parents=True, exist_ok=True)
    a = check_a()
    per_draw, comparison, b = check_b()
    pd.DataFrame(a["comparison"]).to_csv(out / "check_a_levels_s0.5.csv", index=False)
    per_draw.to_csv(out / "check_b_donor_side_per_draw.csv", index=False)
    comparison.to_csv(out / "check_b_donor_side_comparison.csv", index=False)
    summary = {"commits": code_commits(), "check_a": a, "check_b": b}
    with open(out / "summary.json", "w") as f:
        json.dump(summary, f, indent=2, sort_keys=True)
    c = a["computed"]
    L = ["# Two recorded claims about tier 3 recomputed from the committed stores", "",
         f"## (a) The level cell s = 0.5 with the never-named set at its labels, against importances-as-masks, per text ({a['store']})", "",
         f"Texts below their own importances-as-masks divergence: {c['n_texts_below']} of {c['n_texts']} (equal {c['n_texts_equal']}, above {c['n_texts_above']}); the largest paired difference is {c['max_paired_difference']:+.4f}.",
         f"Paired difference (level minus importances): median {c['median_paired_difference']:+.4f}, tenth percentile {c['p10_paired_difference']:+.4f}, ninetieth {c['p90_paired_difference']:+.4f}, mean {c['mean_paired_difference']:+.4f}; "
         f"means {c['mean_level']:.4f} and {c['mean_importances']:.4f}.", "", "| quantity | claimed | computed | agrees at the printed precision |", "|---|---|---|---|"]
    L += [f"| {r['quantity']} | {r['claimed']} | {r['computed']:.6g} | {r['agrees']} |" for r in a["comparison"]]
    L += ["", "## (b) The donor-side pass (results/grid/main/tier3/donors_D_unif_k{k}_r{4,7}/; the union on E from results/grid/main/tier1/E)", "",
          "| rung | draw | donor sequences | n_on | the union on the donors | the donors' own importances-as-masks | the donors' own rounded labels | the same union on E |", "|---|---|---|---|---|---|---|---|"]
    L += [f"| {r.rung} | {r.draw} | {r.n_donor_sequences} | {r.n_on} | {r.union_on_donors:.4f} | {r.donors_own_importances:.4f} | {r.donors_own_rounded:.4f} | {r.same_union_on_E:.4f} |" for r in per_draw.itertuples()]
    L += ["", "| rung | column | statistic | claimed | computed | agrees at two decimals |", "|---|---|---|---|---|---|"]
    L += [f"| {r.rung} | {r.column} | {r.statistic} | {r.claimed} | {r.computed:.4f} | {r.agrees} |" for r in comparison.itertuples()]
    L += ["", f"(a) all agree: {a['all_agree']}; (b) {b['n_compared'] - b['n_disagree']} of {b['n_compared']} agree."]
    text = "\n".join(L)
    with open(out / "summary.md", "w") as f:
        f.write(text + "\n")
    print(text)
    return 0


if __name__ == "__main__":
    sys.exit(main())
