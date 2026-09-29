"""The heuristic code filter and its calibration against the labeled file's source label.

Three jobs: a fallback for the domain sets if the labeled file cannot be loaded; the code fraction of D_unif; and
the stratification of E into code-like and prose-like rows. Calibrated as Github against every other set, the only
label there is; the write-up carries two readings, the raw filter-positive fraction ("code-like text by the filter")
and the corrected estimate ("Github-source share").

The text a row is scored on: the 512 ids split at every end-of-text id, each segment decoded with
`skip_special_tokens=False, clean_up_tokenization_spaces=False`, the segments joined with one newline (so the
literal's `<`, `>`, `|` stay out of the punctuation count); per row `n_eot` and `straddles = n_eot > 0`.

Features, with P the ten characters { } ; = ( ) [ ] < >: f_p = N_P / N_nw (N_nw non-whitespace characters by
`str.isspace`), f_i = N_ind / N_line (N_line non-empty lines, split on "\\n" with one trailing "\\r" stripped, a line
non-empty if it has a non-whitespace character; N_ind the non-empty lines beginning with two spaces or a tab). Each
fraction is 0 when its denominator is; a single leading space is not indentation; other Unicode whitespace at a
line start is not.

Rule: code-like if f_p >= a and f_i >= b; prose-like if f_p < a and f_i < b; unassigned otherwise. Thresholds chosen
on the fit halves by Youden's J = TPR - FPR over the grid a in {0.005, ..., 0.150} (30), b in {0.05, ..., 0.95} (19);
ties to the lower FPR, then the larger a, then the larger b; a pair on the grid's boundary widens the grid in that
direction and both grids are recorded (nothing is frozen until the pair is interior). Reported on the report halves
with Wilson 95 percent intervals: TPR, FPR, L, S, U1, U0, J on both halves; the per-set panel; twenty random rows
from each confusion cell; the filter on E_lab as a held-out test. Floors: thresholds frozen and E stratified only
if J on the report halves >= 0.5; the stratified comparison read only if the code-like stratum's PPV at the
estimated prevalence >= 0.5 and each stratum has >= 64 rows (recorded as flags). The code fraction of D_unif:
q with its Wilson interval, the Rogan-Gladen pi = (q - FPR) / (TPR - FPR) clipped to [0, 1], 5,000 bootstrap
replicates with seed (master, "boot", "codefilter") resampling the 1,024 rows of D_unif and the two report halves;
PPV and prose purity at pi; the labeled file's Github token share w as an independent prediction.
"""

from __future__ import annotations

import csv
import hashlib
import json
import math
import time
from pathlib import Path
from typing import Any

import numpy as np

from vpd_audit import env
from vpd_audit.data import load_set
from vpd_audit.masks import seed_from_tuple

PUNCT = frozenset("{};=()[]<>")
GRID_A = [round(0.005 * i, 3) for i in range(1, 31)]  # 0.005 .. 0.150
GRID_B = [round(0.05 * i, 2) for i in range(1, 20)]  # 0.05 .. 0.95
FALLBACK = {"a": 0.03, "b": 0.30}
J_FLOOR = 0.5
PPV_FLOOR = 0.5
STRATUM_MIN_ROWS = 64
N_BOOT = 5000
N_EXAMPLES = 20
Z95 = 1.959963984540054


# ----------------------------------------------------------------------------- the text and the features


def row_text(ids: np.ndarray, tokenizer: Any, eos: int) -> tuple[str, int]:
    ids = [int(x) for x in ids]
    segments: list[list[int]] = [[]]
    n_eot = 0
    for t in ids:
        if t == eos:
            n_eot += 1
            segments.append([])
        else:
            segments[-1].append(t)
    text = "\n".join(tokenizer.decode(seg, skip_special_tokens=False, clean_up_tokenization_spaces=False) if seg else "" for seg in segments)
    return text, n_eot


def features(text: str) -> tuple[float, float]:
    n_p = sum(1 for c in text if c in PUNCT)
    n_nw = sum(1 for c in text if not c.isspace())
    f_p = n_p / n_nw if n_nw else 0.0
    n_line = 0
    n_ind = 0
    for line in text.split("\n"):
        if line.endswith("\r"):
            line = line[:-1]
        if not any(not c.isspace() for c in line):
            continue
        n_line += 1
        if line.startswith("  ") or line.startswith("\t"):
            n_ind += 1
    f_i = n_ind / n_line if n_line else 0.0
    return f_p, f_i


def classify(f_p: float, f_i: float, a: float, b: float) -> str:
    if f_p >= a and f_i >= b:
        return "code"
    if f_p < a and f_i < b:
        return "prose"
    return "unassigned"


def score_rows(ids: np.ndarray, tokenizer: Any, eos: int) -> dict[str, np.ndarray]:
    fp, fi, ne, texts = [], [], [], []
    for r in range(ids.shape[0]):
        text, n_eot = row_text(ids[r], tokenizer, eos)
        a_, b_ = features(text)
        fp.append(a_)
        fi.append(b_)
        ne.append(n_eot)
        texts.append(text)
    return {"f_p": np.asarray(fp), "f_i": np.asarray(fi), "n_eot": np.asarray(ne), "texts": texts}


# ----------------------------------------------------------------------------- statistics


def wilson(k: int, n: int, z: float = Z95) -> dict[str, float]:
    if n == 0:
        return {"p": float("nan"), "lo": float("nan"), "hi": float("nan"), "k": k, "n": n}
    p = k / n
    denom = 1 + z * z / n
    centre = (p + z * z / (2 * n)) / denom
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / denom
    return {"p": p, "lo": centre - half, "hi": centre + half, "k": k, "n": n}


def rates(fp: np.ndarray, fi: np.ndarray, a: float, b: float) -> dict[str, float]:
    code = (fp >= a) & (fi >= b)
    prose = (fp < a) & (fi < b)
    return {"code": float(code.mean()), "prose": float(prose.mean()), "unassigned": float(1 - code.mean() - prose.mean()), "n": int(fp.size)}


def choose_thresholds(gh: tuple[np.ndarray, np.ndarray], other: tuple[np.ndarray, np.ndarray], grid_a: list[float], grid_b: list[float]) -> dict[str, Any]:
    """The pair maximizing J = TPR - FPR on the fit halves; ties to the lower FPR, then the larger a, then the larger b."""
    best: tuple[float, float, float, float] | None = None  # (J, -FPR, a, b)
    table = []
    for a in grid_a:
        for b in grid_b:
            tpr = float(((gh[0] >= a) & (gh[1] >= b)).mean())
            fpr = float(((other[0] >= a) & (other[1] >= b)).mean())
            j = tpr - fpr
            table.append({"a": a, "b": b, "TPR": tpr, "FPR": fpr, "J": j})
            key = (j, -fpr, a, b)
            if best is None or key > best:
                best = key
    assert best is not None
    j, neg_fpr, a, b = best
    on_edge = {"a_low": a == min(grid_a), "a_high": a == max(grid_a), "b_low": b == min(grid_b), "b_high": b == max(grid_b)}
    return {"a": a, "b": b, "J_fit": j, "TPR_fit": j - neg_fpr, "FPR_fit": -neg_fpr, "grid_a": [min(grid_a), max(grid_a), len(grid_a)], "grid_b": [min(grid_b), max(grid_b), len(grid_b)],
            "on_boundary": any(on_edge.values()), "boundary": on_edge, "table": table}


def choose_with_edge_rule(gh, other, *, max_widenings: int = 12) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    """The grid-edge rule: a pair on the boundary widens the grid in that direction and reruns; every grid is recorded.
    Upward, ten more steps of a (0.005) or up to b = 1.0; downward, the step halves toward the natural edge at 0, which
    is added last. A pair still on a boundary after the widenings is recorded as such (a natural edge at 0 or 1 cannot be
    widened past) and is not frozen."""
    grid_a, grid_b = list(GRID_A), list(GRID_B)
    history = []
    res: dict[str, Any] = {}
    for _ in range(max_widenings + 1):
        res = choose_thresholds(gh, other, grid_a, grid_b)
        history.append({k: v for k, v in res.items() if k != "table"})
        if not res["on_boundary"]:
            res["natural_edge"] = False
            return res, history
        e = res["boundary"]
        step_a, step_b = 0.005, 0.05
        widened = False
        if e["a_high"]:
            grid_a += [float(round(max(grid_a) + step_a * i, 4)) for i in range(1, 11)]
            widened = True
        if e["a_low"] and min(grid_a) > 0.0:
            lo = min(grid_a)
            new_lo = 0.0 if lo <= 0.0005 else float(round(lo / 2, 6))
            grid_a = [new_lo] + grid_a
            widened = True
        if e["b_high"] and max(grid_b) < 1.0:
            grid_b += [float(round(min(1.0, max(grid_b) + step_b * i), 3)) for i in range(1, 3)]
            widened = True
        if e["b_low"] and min(grid_b) > 0.0:
            lo = min(grid_b)
            new_lo = 0.0 if lo <= 0.005 else float(round(lo / 2, 4))
            grid_b = [new_lo] + grid_b
            widened = True
        grid_a, grid_b = sorted(set(float(x) for x in grid_a)), sorted(set(float(x) for x in grid_b))
        if not widened:
            break
    res["natural_edge"] = bool((res["boundary"]["a_low"] and res["a"] == 0.0) or (res["boundary"]["b_low"] and res["b"] == 0.0)
                               or (res["boundary"]["b_high"] and res["b"] >= 1.0))
    return res, history


def rogan_gladen(q: float, tpr: float, fpr: float) -> float:
    if tpr - fpr <= 0:
        return float("nan")
    return min(1.0, max(0.0, (q - fpr) / (tpr - fpr)))


def ppv(pi: float, tpr: float, fpr: float) -> float:
    d = pi * tpr + (1 - pi) * fpr
    return pi * tpr / d if d > 0 else float("nan")


def prose_purity(pi: float, s: float, l: float) -> float:
    d = (1 - pi) * s + pi * l
    return (1 - pi) * s / d if d > 0 else float("nan")


# ----------------------------------------------------------------------------- the calibration


def _json_default(o: Any) -> Any:
    if isinstance(o, (np.integer,)):
        return int(o)
    if isinstance(o, (np.floating,)):
        return float(o)
    if isinstance(o, (np.bool_,)):
        return bool(o)
    if isinstance(o, np.ndarray):
        return o.tolist()
    raise TypeError(f"not JSON serializable: {type(o)}")


def _sha_rows(ids: np.ndarray) -> str:
    return hashlib.sha256(np.ascontiguousarray(ids, dtype=np.int32).tobytes()).hexdigest()


def calibrate(*, sets_dir: Path = env.SETS_DIR, out_dir: Path, master_seed: int = 0, acceptance_dir: Path | None = None, log: Any = print) -> dict[str, Any]:
    """The calibration end to end on the saved sets: the thresholds, the report-half rates, the panel, the examples, E_lab
    as a held-out test, the strata of E and D_unif, and the corrected code fraction of D_unif."""
    from transformers import AutoTokenizer

    from vpd_audit.data import LABELED_TOKENIZER

    t0 = time.time()
    out_dir.mkdir(parents=True, exist_ok=True)
    tok = AutoTokenizer.from_pretrained(LABELED_TOKENIZER)
    eos = int(tok.eos_token_id)
    assert tok.encode("<|endoftext|>", add_special_tokens=False) == [eos]
    with open(sets_dir / "labeled_manifest.json") as f:
        labeled_manifest = json.load(f)
    gh_ids, _, gh_rec = load_set("calib_github", sets_dir)
    ot_ids, _, ot_rec = load_set("calib_other", sets_dir)
    with open(sets_dir / "calib_other.labels.json") as f:
        ot_labels = json.load(f)["labels"]
    assert gh_ids.shape[0] == ot_ids.shape[0] == 2000
    half = gh_ids.shape[0] // 2
    log(f"[codefilter] scoring {gh_ids.shape[0]} Github and {ot_ids.shape[0]} other calibration rows")
    gh, ot = score_rows(gh_ids, tok, eos), score_rows(ot_ids, tok, eos)
    fit_gh = (gh["f_p"][:half], gh["f_i"][:half])
    fit_ot = (ot["f_p"][:half], ot["f_i"][:half])
    rep_gh = (gh["f_p"][half:], gh["f_i"][half:])
    rep_ot = (ot["f_p"][half:], ot["f_i"][half:])
    chosen, history = choose_with_edge_rule(fit_gh, fit_ot)
    a, b = chosen["a"], chosen["b"]
    log(f"[codefilter] thresholds a={a}, b={b} (J on the fit halves {chosen['J_fit']:.3f}; {len(history)} grid(s); interior={not chosen['on_boundary']})")
    # the report halves
    r_gh, r_ot = rates(*rep_gh, a, b), rates(*rep_ot, a, b)
    n = half
    report = {"TPR": wilson(round(r_gh["code"] * n), n), "FPR": wilson(round(r_ot["code"] * n), n), "L_github_prose_like": wilson(round(r_gh["prose"] * n), n),
              "S_other_prose_like": wilson(round(r_ot["prose"] * n), n), "U1_github_unassigned": wilson(round(r_gh["unassigned"] * n), n), "U0_other_unassigned": wilson(round(r_ot["unassigned"] * n), n)}
    j_report = r_gh["code"] - r_ot["code"]
    fit_rates_gh, fit_rates_ot = rates(*fit_gh, a, b), rates(*fit_ot, a, b)
    j_fit = fit_rates_gh["code"] - fit_rates_ot["code"]
    # the per-set panel, never used to choose
    panel: dict[str, Any] = {}
    for name, meta in labeled_manifest["sets"].items():
        if not name.startswith("panel_"):
            continue
        ids, _, _ = load_set(name, sets_dir)
        sc = score_rows(ids, tok, eos)
        panel[meta["label"]] = {**rates(sc["f_p"], sc["f_i"], a, b), "f_p_median": float(np.median(sc["f_p"])), "f_i_median": float(np.median(sc["f_i"]))}
    # the examples: twenty random rows from each confusion cell of the report halves
    rng = np.random.default_rng(seed_from_tuple((master_seed, "examples", "codefilter")))
    cells = {"Github -> prose-like": [half + i for i in range(half) if classify(rep_gh[0][i], rep_gh[1][i], a, b) == "prose"],
             "Github -> unassigned": [half + i for i in range(half) if classify(rep_gh[0][i], rep_gh[1][i], a, b) == "unassigned"],
             "non-Github -> code-like": [half + i for i in range(half) if classify(rep_ot[0][i], rep_ot[1][i], a, b) == "code"],
             "non-Github -> unassigned": [half + i for i in range(half) if classify(rep_ot[0][i], rep_ot[1][i], a, b) == "unassigned"]}
    with open(out_dir / "examples.txt", "w") as f:
        f.write(f"# Twenty random rows from each confusion cell of the report halves, thresholds a={a}, b={b}; decoded text, truncated to 1,500 characters\n\n")
        for cell, idx in cells.items():
            pick = rng.choice(idx, size=min(N_EXAMPLES, len(idx)), replace=False) if idx else []
            f.write(f"## {cell}: {len(idx)} rows in the cell; {len(pick)} shown\n\n")
            for i in pick:
                src = gh if cell.startswith("Github") else ot
                lab = "Github" if cell.startswith("Github") else ot_labels[i]
                f.write(f"--- row {i} ({lab}); f_p={src['f_p'][i]:.4f}, f_i={src['f_i'][i]:.3f}, n_eot={src['n_eot'][i]}\n{src['texts'][i][:1500]}\n\n")
    # E_lab, held out: the confusion matrix per source set
    elab_ids, _, _ = load_set("E_lab", sets_dir)
    with open(sets_dir / "E_lab.strata.json") as f:
        elab_strata = json.load(f)["strata"]
    sc = score_rows(elab_ids, tok, eos)
    elab: dict[str, dict[str, int]] = {}
    for i, s in enumerate(elab_strata):
        elab.setdefault(s, {"code": 0, "prose": 0, "unassigned": 0})[classify(sc["f_p"][i], sc["f_i"][i], a, b)] += 1
    # the floors
    frozen = j_report >= J_FLOOR and not chosen["on_boundary"]
    log(f"[codefilter] chosen pair on a boundary: {chosen['on_boundary']} (natural edge: {chosen.get('natural_edge')}); grids tried: {len(history)}; "
        f"J on the fit halves per grid: {[round(h['J_fit'], 4) for h in history]}; a per grid: {[h['a'] for h in history]}")
    calibration = {
        "calibrated": True, "a": a, "b": b, "frozen": bool(frozen), "frozen_rule": f"J on the report halves >= {J_FLOOR} and the pair interior to its grid",
        "grid": {"a": "0.005 to 0.150 by 0.005 (30)", "b": "0.05 to 0.95 by 0.05 (19)", "objective": "Youden's J = TPR - FPR on the fit halves",
                 "tie_break": "lower FPR, then larger a, then larger b", "edge_rule": "a pair on the boundary widens the grid in that direction and reruns; every grid recorded", "history": history},
        "seeds": {"docs": "(master, 'docs', label)", "calib_github": "(master, 'calib', 'Github')", "calib_other": "(master, 'calib', 'other')", "panel": "(master, 'calib', label)",
                  "examples": "(master, 'examples', 'codefilter')", "bootstrap": "(master, 'boot', 'codefilter')", "master_seed": master_seed},
        "rows": {"calib_github_sha256": gh_rec["sha256_ids"], "calib_other_sha256": ot_rec["sha256_ids"], "fit_github_sha256": _sha_rows(gh_ids[:half]), "report_github_sha256": _sha_rows(gh_ids[half:]),
                 "fit_other_sha256": _sha_rows(ot_ids[:half]), "report_other_sha256": _sha_rows(ot_ids[half:]), "n_per_half": half,
                 "deviation": "1,000 rows per class were pre-registered; 2,000 used so that thresholds are chosen on one half and every rate reported on the other"},
        "fit_halves": {"TPR": fit_rates_gh["code"], "FPR": fit_rates_ot["code"], "J": j_fit},
        "report_halves": {**report, "J": j_report, "J_optimism_fit_minus_report": j_fit - j_report},
        "per_set_panel": panel,
        "E_lab_confusion_per_source": elab,
        "file": labeled_manifest["file"], "tokenizer": {"name": LABELED_TOKENIZER, "eos_token_id": eos},
        "features": {"f_p": "count of { } ; = ( ) [ ] < > over non-whitespace characters (str.isspace); the denominator refines the pre-registered 'fraction of characters'",
                     "f_i": "non-empty lines beginning with two spaces or a tab over non-empty lines (split on newline, one trailing carriage return stripped)"},
        "token_share_w": labeled_manifest["token_share"]["w"],
        "commits": None, "prepared_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
    }
    from vpd_audit.results import code_commits

    calibration["commits"] = code_commits()
    cal_path = out_dir / "calibration.json"
    with open(cal_path, "w") as f:
        json.dump(calibration, f, indent=2, sort_keys=True, default=_json_default)
    cal_sha = hashlib.sha256(cal_path.read_bytes()).hexdigest()
    with open(out_dir / "per_set.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["set", "n_rows", "code_like", "prose_like", "unassigned", "f_p_median", "f_i_median"])
        for lab, v in sorted(panel.items()):
            w.writerow([lab, v["n"], f"{v['code']:.4f}", f"{v['prose']:.4f}", f"{v['unassigned']:.4f}", f"{v['f_p_median']:.5f}", f"{v['f_i_median']:.4f}"])
    log(f"[codefilter] report halves: TPR {report['TPR']['p']:.3f} FPR {report['FPR']['p']:.3f} J {j_report:.3f} (fit {j_fit:.3f}); L {report['L_github_prose_like']['p']:.3f} S {report['S_other_prose_like']['p']:.3f} "
        f"U1 {report['U1_github_unassigned']['p']:.3f} U0 {report['U0_other_unassigned']['p']:.3f}; frozen={frozen}")
    # the strata of E and D_unif, and the corrected code fraction
    target_ce = None
    if acceptance_dir is not None and (Path(acceptance_dir) / "main_bf16" / "per_sequence.parquet").is_file():
        import pandas as pd

        acc = pd.read_parquet(Path(acceptance_dir) / "main_bf16" / "per_sequence.parquet")
        target_ce = acc[acc.condition == "target"].set_index("seq")["ce"].astype(float)
    strata_summary: dict[str, Any] = {}
    q_rows = None
    for set_name in ("E", "D_unif"):
        ids, _, rec = load_set(set_name, sets_dir)
        sc = score_rows(ids, tok, eos)
        strata = [classify(sc["f_p"][i], sc["f_i"][i], a, b) for i in range(ids.shape[0])]
        with open(out_dir / f"strata_{set_name}.csv", "w", newline="") as f:
            f.write(f"# calibration_sha256={cal_sha} set_sha256={rec['sha256_ids']} a={a} b={b}\n")
            w = csv.writer(f)
            w.writerow(["seq", "f_p", "f_i", "stratum", "n_eot", "straddles"])
            for i in range(ids.shape[0]):
                w.writerow([i, f"{sc['f_p'][i]:.6f}", f"{sc['f_i'][i]:.4f}", strata[i], int(sc["n_eot"][i]), int(sc["n_eot"][i] > 0)])
        summ: dict[str, Any] = {}
        for s in ("code", "prose", "unassigned"):
            idx = [i for i, x in enumerate(strata) if x == s]
            entry: dict[str, Any] = {"n_rows": len(idx), "straddling_fraction": float(np.mean([sc["n_eot"][i] > 0 for i in idx])) if idx else None}
            if set_name == "E" and target_ce is not None and idx:
                ce = target_ce.loc[idx].to_numpy()
                entry.update({"target_ce_mean": float(ce.mean()), "target_ce_std": float(ce.std(ddof=1)) if len(ce) > 1 else None})
            summ[s] = entry
        strata_summary[set_name] = summ
        if set_name == "D_unif":
            q_rows = np.asarray([s == "code" for s in strata])
    assert q_rows is not None
    k = int(q_rows.sum())
    n_d = int(q_rows.size)
    q = k / n_d
    tpr, fpr = report["TPR"]["p"], report["FPR"]["p"]
    pi = rogan_gladen(q, tpr, fpr)
    rng = np.random.default_rng(seed_from_tuple((master_seed, "boot", "codefilter")))
    gh_code = ((rep_gh[0] >= a) & (rep_gh[1] >= b)).astype(float)
    ot_code = ((rep_ot[0] >= a) & (rep_ot[1] >= b)).astype(float)
    boots = []
    for _ in range(N_BOOT):
        qb = q_rows[rng.integers(0, n_d, n_d)].mean()
        tb = gh_code[rng.integers(0, half, half)].mean()
        fb = ot_code[rng.integers(0, half, half)].mean()
        boots.append([qb, tb, fb, rogan_gladen(qb, tb, fb)])
    boots_arr = np.asarray(boots, dtype=float)
    pis = boots_arr[:, 3]
    pis = pis[np.isfinite(pis)]
    s_rate, l_rate = report["S_other_prose_like"]["p"], report["L_github_prose_like"]["p"]
    code_fraction = {"q_code_like_rows": wilson(k, n_d), "TPR": tpr, "FPR": fpr, "pi_rogan_gladen": pi,
                     "pi_bootstrap": {"n": N_BOOT, "n_finite": int(pis.size), "p2.5": float(np.percentile(pis, 2.5)) if pis.size else None, "p97.5": float(np.percentile(pis, 97.5)) if pis.size else None,
                                      "seed": "(master, 'boot', 'codefilter')", "resampled": "the 1,024 rows of D_unif, the 1,000 Github report rows, the 1,000 non-Github report rows, independently"},
                     "PPV_at_pi": ppv(pi, tpr, fpr), "prose_purity_at_pi": prose_purity(pi, s_rate, l_rate), "S": s_rate, "L": l_rate,
                     "w_Github_token_share": labeled_manifest["token_share"]["w"].get("Github"), "calibration_sha256": cal_sha,
                     "readings": {"raw": "code-like text by the filter", "corrected": "Github-source share"},
                     "floors": {"J_report": j_report, "J_floor": J_FLOOR, "frozen_and_E_stratified": bool(frozen),
                                "PPV_floor": PPV_FLOOR, "stratum_min_rows": STRATUM_MIN_ROWS,
                                "stratified_comparison_readable": bool(frozen and ppv(pi, tpr, fpr) >= PPV_FLOOR and strata_summary["E"]["code"]["n_rows"] >= STRATUM_MIN_ROWS and strata_summary["E"]["prose"]["n_rows"] >= STRATUM_MIN_ROWS)},
                     "strata": strata_summary}
    with open(out_dir / "code_fraction_D_unif.json", "w") as f:
        json.dump(code_fraction, f, indent=2, sort_keys=True, default=_json_default)
    log(f"[codefilter] D_unif: q = {q:.4f} ({k}/{n_d}), pi = {pi:.4f} [{code_fraction['pi_bootstrap']['p2.5']}, {code_fraction['pi_bootstrap']['p97.5']}], PPV {code_fraction['PPV_at_pi']:.3f}, "
        f"prose purity {code_fraction['prose_purity_at_pi']:.3f}, w_Github {code_fraction['w_Github_token_share']}; E strata {{{', '.join(f'{s}: {v['n_rows']}' for s, v in strata_summary['E'].items())}}}; {time.time() - t0:.0f} s")
    return {"calibration": calibration, "code_fraction": code_fraction, "calibration_sha256": cal_sha}
