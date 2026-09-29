"""Entry points: fetch, verify-artifacts, prepare-data, smoke, acceptance, acceptance-report;
(the residual test cells) short-runs-report; (check 6 at matched shapes) check6-report; (the residual follow-up) residual-matrix-report."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from vpd_audit import env  # noqa: F401  (first: sets PARAM_DECOMP_OUT_DIR and HF_HOME)


def _device(arg: str | None) -> str:
    import torch

    if arg:
        return arg
    return "cuda" if torch.cuda.is_available() else "cpu"


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="vpd-audit")
    sub = p.add_subparsers(dest="cmd", required=True)

    f = sub.add_parser("fetch", help="one-time artifact fetch with the WandB key (from the environment or .env)")
    f.add_argument("--runs", nargs="*", default=None, help="run ids; default: the four local runs")
    f.add_argument("--all", action="store_true", help="all five runs, the control included")
    f.add_argument("--replace", action="store_true")

    v = sub.add_parser("verify-artifacts", help="recompute sizes and SHA-256 against the manifest")
    v.add_argument("--runs", nargs="*", default=None)

    pdp = sub.add_parser("prepare-data", help="E and D_unif from the stream, with hashes; --labeled: the labeled sets")
    pdp.add_argument("--labeled", action="store_true")
    pdp.add_argument("--num-proc", type=int, default=1)

    s = sub.add_parser("smoke", help="load a run, compute g on n sequences, run the references and the identities")
    s.add_argument("--run", choices=["simplestories", "main", "control"], required=True)
    s.add_argument("--n", type=int, default=8)
    s.add_argument("--precision", choices=["fp32", "bf16"], default=None, help="default: bf16 on CUDA, fp32 on CPU")
    s.add_argument("--device", default=None)
    s.add_argument("--subbatch", type=int, default=None)
    s.add_argument("--n-draws", type=int, default=2)
    s.add_argument("--master-seed", type=int, default=0)
    s.add_argument("--sizes", type=int, nargs="*", default=None, help="sub-batch sizes for M5 (default 1 4 8)")

    a = sub.add_parser("acceptance", help="the acceptance test; meant for Modal, runnable locally with --n")
    a.add_argument("--device", default=None)
    a.add_argument("--subbatch", type=int, default=64)
    a.add_argument("--n-draws", type=int, default=8)
    a.add_argument("--n", type=int, default=None)
    a.add_argument("--jobs", nargs="*", default=None)
    a.add_argument("--primary", default="main_bf16", help="the job checks 1, 3, 4, 5, 7 read (main_bf16 on Modal, main_fp32 on CPU)")
    a.add_argument("--fp32-job", default="main_fp32")
    a.add_argument("--control-job", default="control_bf16")
    a.add_argument("--no-check6", action="store_true")
    a.add_argument("--check6-batch", type=int, default=64)
    a.add_argument("--check6-n-batches", type=int, default=2)
    a.add_argument("--stat-batch", type=int, default=128, help="batch size for the spreads s and s_d (the paper's 128)")
    a.add_argument("--out", default=None)

    r = sub.add_parser("acceptance-report", help="print the eight checks from results/acceptance/")
    r.add_argument("--dir", default="results/acceptance")
    r.add_argument("--primary", default="main_bf16")
    r.add_argument("--fp32-job", default="main_fp32")
    r.add_argument("--control-job", default="control_bf16")
    r.add_argument("--stat-batch", type=int, default=128)

    sr = sub.add_parser("short-runs-report", help="summary.json and summary.md for the two residual passes from the committed tables")
    sr.add_argument("--dir", default="results/short_runs")
    sr.add_argument("--acceptance", default="results/acceptance", help="the committed acceptance tables for the reproducibility check")

    c6 = sub.add_parser("check6-report", help="the three comparisons of check 6 at matched shapes from the committed files")
    c6.add_argument("--dir", default="results/short_runs/check6_bf16")
    c6.add_argument("--acceptance", default="results/acceptance")
    c6.add_argument("--precision", default="bf16")

    pr = sub.add_parser("pre-reads", help="label-only numbers from the caches and the sources before any grid cell (CPU; the caches must be in the local cache)")
    pr.add_argument("--run", choices=["main", "control"], required=True)
    pr.add_argument("--draws", type=int, default=8)
    pr.add_argument("--out", default=None, help="default: results/grid/pre_reads/<run>/ under the cache's results directory")

    p7 = sub.add_parser("pre-reads-s7", help="the marginal control's pre-read and the code-leaning table (CPU; the caches must be in the local cache; --dry for the stand-in)")
    p7.add_argument("--run", choices=["main", "control"], default="main")
    p7.add_argument("--dry", action="store_true", help="the stand-in: run simplestories on the dry sets and caches, two draws, into results/dry_run/pre_reads/s7/")
    p7.add_argument("--draws", type=int, default=None)
    p7.add_argument("--n-seeds", type=int, default=None)
    p7.add_argument("--n-shuffles", type=int, default=None)
    p7.add_argument("--out", default=None, help="a directory named s7; default: results/grid/pre_reads/<run>/s7/ under the cache's results directory")

    p7f = sub.add_parser("pre-reads-s7-finish", help="the local finishing step on a pulled s7 directory (the histogram's figure, the stray-code rows under the frozen filter, the checks against the committed stores)")
    p7f.add_argument("--dir", required=True, help="the s7 directory, e.g. results/grid/pre_reads/main/s7")
    p7f.add_argument("--stores-root", default=None, help="results/grid/<run>: check the union and plain sets against the committed cell tables (omit for the stand-in)")
    p7f.add_argument("--calibration", default=None, help="results/data/code_filter/calibration.json: score the stray-code rows (omit for the stand-in)")

    an = sub.add_parser("analyze", help="the pre-registered reading rules on the grid's stores (CPU); refuses the paper's model without --frozen <commit>")
    an.add_argument("--run", choices=["main", "control", "simplestories"], required=True)
    an.add_argument("--tiers", type=int, nargs="*", default=None, help="tiers to read (default: every tier<t>/ directory present)")
    an.add_argument("--root", default=None, help="the stores' root (default: results/grid/<run>/, or results/dry_run/ for simplestories)")
    an.add_argument("--out", default=None, help="default: results/grid/analysis/<run>/, or results/dry_run/analysis/ for simplestories")
    an.add_argument("--frozen", default=None, help="the frozen commit hash; required for main and control")
    an.add_argument("--replicates", type=int, default=None)
    an.add_argument("--master-seed", type=int, default=0)
    an.add_argument("--extra-root", action="append", default=None, help="a further root whose stores join this run's sets (the stand-in's tier-4 dry run, results/dry_run_s7); may be given more than once")
    an.add_argument("--compare-with", default=None, help="a run name (its committed analysis under results/grid/analysis/<run>/) or a directory; "
                                                         "this run against it rung by rung at the shared rungs and at matched switched mass with its decile edges")

    a9 = sub.add_parser("analyze-s9", help="the frozen analysis of the tier-5 stores (CPU), with its own loader and the bitwise canary inside it; refuses the paper's model without --frozen <commit> from a clean tree")
    a9.add_argument("--run", choices=["main", "simplestories"], required=True)
    a9.add_argument("--root", default=None, help="the tier-5 stores' root (default: results/grid/main_s9/, or results/dry_run_s9/ for simplestories)")
    a9.add_argument("--out", default=None, help="default: results/grid/analysis/main/s9b/, or results/dry_run_s9/analysis/ for simplestories")
    a9.add_argument("--frozen", default=None, help="the frozen commit hash; required for main")
    a9.add_argument("--committed-root", action="append", default=None, help="a root of the run's committed stores, the canary's other side; may be given more than once "
                                                                              "(default: results/grid/main/, or results/dry_run/ and results/dry_run_s7/ for simplestories)")
    a9.add_argument("--no-canary", action="store_true", help="the stand-in only: read stores that did not run on the card the committed stores ran on (a local CPU run); never allowed for main")
    a9.add_argument("--synthetic-document-rows", type=int, default=None, help="the stand-in only: the size of its synthetic documents, which must be the launch's (default: analysis_s9.STAND_IN_DOCUMENT_ROWS)")
    a9.add_argument("--replicates", type=int, default=None)
    a9.add_argument("--master-seed", type=int, default=0)

    rm = sub.add_parser("residual-matrix-report", help="the residual follow-up's summary.json and summary.md from the committed tables")
    rm.add_argument("--dir", default="results/short_runs/residual_matrix_fp32")
    rm.add_argument("--short-runs", default="results/short_runs/summary.json", help="the residual test cells' summary, for the measured Q-bar")

    cu = sub.add_parser("check6-unrounded", help="the acceptance test's check 6 recomputed unrounded from the committed acceptance files (CPU; results/acceptance is read only)")
    cu.add_argument("--acceptance", default="results/acceptance")
    cu.add_argument("--out", default="results/short_runs/check6_fp32_unrounded")
    cu.add_argument("--precision", default="fp32")

    rr = sub.add_parser("residual-rank", help="a CPU measurement: singular values, the Eckart-Young floor, and the residual's energy in the components' spans, per matrix")
    rr.add_argument("--run", default="main")
    rr.add_argument("--out", default="results/short_runs/residual_rank")

    rt = sub.add_parser("round-trip", help="the tokenizer round-trip check on saved sets (CPU); E first, then the labeled sets")
    rt.add_argument("--sets", nargs="+", default=["E"])
    rt.add_argument("--out", default="results/data/round_trip.json")

    cf = sub.add_parser("code-filter", help="calibrate the code filter on the saved calibration rows, stratify E and D_unif, the corrected code fraction (CPU)")
    cf.add_argument("--sets-dir", default=None, help="default: the cache's sets directory")
    cf.add_argument("--out", default="results/data/code_filter")
    cf.add_argument("--acceptance", default="results/acceptance", help="for the target's cross-entropy per stratum of E")
    cf.add_argument("--master-seed", type=int, default=0)

    dr = sub.add_parser("dry-run", help="the grid on SimpleStories with the stand-in sets (a reduced CPU pass with --tiers; the full run is the Modal dry_run function)")
    dr.add_argument("--device", default=None)
    dr.add_argument("--precision", default=None)
    dr.add_argument("--tiers", type=int, nargs="*", default=[1, 2, 3])
    dr.add_argument("--draws", type=int, default=2)
    dr.add_argument("--subbatch", type=int, default=64)
    dr.add_argument("--chunk", type=int, default=32)
    dr.add_argument("--out", default=None)
    dr.add_argument("--groups", nargs="*", default=None, help="run these groups only (E, E_lab, donors_D_unif_k0_r4, ...)")
    dr.add_argument("--subset", default=None, help="a launch subset of cells (cells.SUBSETS) into <group>__<subset> stores")
    dr.add_argument("--corner-check", action="store_true", help="after the grid, the level cells' corner check on the E group's first sub-batch")
    dr.add_argument("--s7-pre-reads", default=None, help="with --tiers 4, the stand-in's s7 pre-read directory (pre-reads-s7 --dry) the tier-4 sets are held to; the forced group of code_leaning.py is used")
    dr.add_argument("--s9-pre-reads", default=None, help="with --tiers 5, the stand-in's label-only tables (s9-pre-reads --dry) the tier-5 sets are held to; default: results/dry_run/pre_reads/s9/ under the cache")
    dr.add_argument("--committed-roots", nargs="*", default=None, help="with --tiers 5, the roots of the stand-in's committed stores, the other side of the bitwise canary and the D_unif gate "
                                                                       "(only meaningful on the card those stores ran on; omitted on CPU, where the canary is then not checked and says so)")

    xp = sub.add_parser("s9-example-positions", help="the example positions for E (two per text, 48 <= t <= 510, seed (master, 'examples', 'E')), written as the list the launch is held to")
    xp.add_argument("--run", choices=["main"], default="main")
    xp.add_argument("--out", default=None, help="default: results/grid/pre_reads/<run>/s9b/example_positions.csv")
    xp.add_argument("--master-seed", type=int, default=0)

    s9 = sub.add_parser("s9-checks", help="the document index and the four checks (CPU). Default: the local command (the document index, checks (a) and (d), the local halves of checks (b) and (c), the report), "
                                          "which needs --frozen <HEAD> on a clean tree; --cache-half runs where the label caches live (on Modal: modal_app.py::s9_label_tables); --pull fetches check (d)'s arrays")
    s9.add_argument("--run", choices=["main"], default="main")
    s9.add_argument("--frozen", default=None, help="the current commit, as `analyze` takes it; the frozen modules' blob hashes are printed against main's beside it")
    s9.add_argument("--cache-half", action="store_true", help="check (b) and the label-only half of check (c), from the label caches (they must be in the local cache)")
    s9.add_argument("--pull", action="store_true", help="confirm check (d)'s per-position arrays are on the Modal volume and pull the absent ones into the stores' git-ignored kl/ folders")
    s9.add_argument("--dry", action="store_true", help="with --cache-half: the stand-in (run simplestories, the dry sets and caches, synthetic documents), into results/dry_run/analysis/s9/")
    s9.add_argument("--n-shuffles", type=int, default=200)
    s9.add_argument("--replicates", type=int, default=None)
    s9.add_argument("--out", default=None, help="a directory named s9")

    s9p = sub.add_parser("s9-pre-reads", help="the label-only tables for the tier-5 GPU run (CPU; the caches must be in the local cache; on Modal: modal_app.py::s9_label_tables); "
                                              "--finish: the local checks of a pulled s9 directory against the committed cell tables")
    s9p.add_argument("--run", choices=["main"], default="main")
    s9p.add_argument("--finish", action="store_true", help="on the pulled results/grid/pre_reads/<run>/s9/: the named sets and the one-text donors against the committed stores' cell tables")
    s9p.add_argument("--dry", action="store_true", help="the stand-in, into results/dry_run/pre_reads/s9/")
    s9p.add_argument("--out", default=None, help="a directory named s9")

    f9 = sub.add_parser("figures-s9", help="the post's figures from the committed tables only (CPU; no store, no array, no pull), each a PNG at 2x with its CSV beside it")
    f9.add_argument("--out", default=None, help="default: results/grid/analysis/main/s9/figures/")

    l11 = sub.add_parser("s11-label-checks", help="the label-only checks before the tier-6 launch. Default: the label tables from the caches (CPU; they must be in the local cache; "
                                                  "on Modal: modal_app.py::s11_label_tables); --finish: the pulled tables against the committed cell tables, and the label gate")
    l11.add_argument("--run", choices=["main"], default="main")
    l11.add_argument("--finish", action="store_true", help="on the pulled results/grid/pre_reads/<run>/s11/: every set against its committed twin; the label gate printed")
    l11.add_argument("--dir", default=None, help="the s11 directory (default: results/grid/pre_reads/<run>/s11/ in the project for --finish, under the cache otherwise)")

    a11 = sub.add_parser("analyze-s11", help="the frozen reading of the binary union (CPU, read-only); refuses the paper's model on a dirty tree or without --freeze <the freeze commit>")
    a11.add_argument("--run", choices=["main"], default="main")
    a11.add_argument("--freeze", default=None, help="the freeze commit; required")
    a11.add_argument("--store", default=None, help="default: results/grid/<run>_s11/tier6/E__binary_union/")
    a11.add_argument("--out", default=None, help="default: results/grid/analysis/<run>/s11/")
    a11.add_argument("--replicates", type=int, default=None)
    a11.add_argument("--master-seed", type=int, default=0)

    l12 = sub.add_parser("s12-label-checks", help="label-only checks of the 2- and 4-token merge sets, the code-leaning edit's erased sets, and the label it removes on the panels. Default: the label "
                                                  "tables from the caches (CPU; they must be in the local cache; on Modal, with the panels' document index: modal_app.py::s12_label_tables); "
                                                  "--finish: the pulled tables against the committed stores, with the document index's panels")
    l12.add_argument("--run", choices=["main"], default="main")
    l12.add_argument("--dry", action="store_true", help="the stand-in (SimpleStories): its caches and its committed dry-run stores; no document index")
    l12.add_argument("--finish", action="store_true", help="on the pulled results/grid/pre_reads/<run>/s12/ (and results/grid/analysis/<run>/s12/ for the document index): every set against its committed twin")
    l12.add_argument("--dir", default=None, help="the label tables' s12 directory (default: results/grid/pre_reads/<run>/s12/ in the project for --finish, under the cache otherwise; "
                                                  "results/dry_run_s12/pre_reads/s12/ with --dry)")
    l12.add_argument("--doc-dir", default=None, help="the document index's s12 directory for --finish (default: results/grid/analysis/<run>/s12/; none with --dry)")

    a12 = sub.add_parser("analyze-s12", help="the reading of tier 7: the code-leaning edit on the panels (ArXiv decisive) and the merge points at 2 and 4 donor tokens (CPU, read-only); "
                                             "refuses the paper's model on a dirty tree or without --freeze <the freeze commit>")
    a12.add_argument("--run", choices=["main"], default="main")
    a12.add_argument("--dry", action="store_true", help="the stand-in's dry run: results/dry_run_s12/tier7/ into results/dry_run_s12/analysis/")
    a12.add_argument("--freeze", default=None, help="the freeze commit; required on the paper's model")
    a12.add_argument("--replicates", type=int, default=None)
    a12.add_argument("--master-seed", type=int, default=0)

    fp = sub.add_parser("figures-post", help="the post's five figures from committed tables and per-text stores only (CPU; after the tier-7 launch), each a PNG with its CSV, into results/post/")
    fp.add_argument("--run", choices=["main"], default="main")
    fp.add_argument("--out", default=None, help="default: results/post/")
    fp.add_argument("--code-edit", default="panels", help="which of the code-edit figure's variants to draw, comma-separated: panels (every bar from the panels; the default), lab (E_lab), arxiv_panel (E_lab with ArXiv's bar from its panel)")
    fp.add_argument("--replicates", type=int, default=None)

    pt = sub.add_parser("post-tables", help="three descriptive tables for the post from committed stores only (CPU): the hard delete per draw, the editing guarantee's coverage on the panels, and the code edit on E_lab with document-level intervals, into results/grid/analysis/<run>/s12/")
    pt.add_argument("--run", choices=["main"], default="main")

    rs = sub.add_parser("resummarize", help="a finished launch's summary rebuilt from its stores and the current code (CPU): the preconditions recomputed and held equal to the launch's, the text rebuilt, the .md rendered again; or the verification store's comparisons.md")
    rs.add_argument("roots", nargs="+", help="a tier's root holding summary*.json and its stores (for example results/grid/main/tier1), or the verification store")
    rs.add_argument("--out", default=None, help="default: in place; with several roots, the out directory gets one subdirectory per root, by its path under results/grid/")

    args = p.parse_args(argv)

    if args.cmd == "resummarize":
        from vpd_audit import env as _env
        from vpd_audit.resummarize import resummarize_root

        for root in args.roots:
            r = Path(root).resolve()
            out = None if args.out is None else (Path(args.out) / r.relative_to(_env.PROJECT_ROOT / "results" / "grid") if len(args.roots) > 1 else Path(args.out))
            resummarize_root(r, out)
        return 0

    if args.cmd == "post-tables":
        from vpd_audit import post_tables

        post_tables.post_tables(run=args.run)
        return 0

    if args.cmd == "figures-post":
        from vpd_audit import env as _env
        from vpd_audit import figures_post
        from vpd_audit.stats import N_REPLICATES

        inp = figures_post.paper_inputs(run=args.run)
        inp.replicates = args.replicates or N_REPLICATES
        figures_post.figures_post(inp, Path(args.out) if args.out else _env.PROJECT_ROOT / "results" / "post", code_edit=tuple(v for v in args.code_edit.split(",") if v))
        return 0
    if args.cmd == "analyze-s12":
        import json as _json

        from vpd_audit import analysis_s12
        from vpd_audit.stats import N_REPLICATES

        spec = analysis_s12.stand_in_spec() if args.dry else analysis_s12.paper_spec(run=args.run)
        summary = analysis_s12.analyze_s12(spec, freeze=args.freeze, replicates=args.replicates or N_REPLICATES, master_seed=args.master_seed)
        print(_json.dumps({k: summary[k] for k in ("run", "arxiv_reading", "candidates_meeting_keep", "freeze")}, indent=1, default=str))
        return 0
    if args.cmd == "s12-label-checks":
        from vpd_audit import env as _env
        from vpd_audit import s12_labels

        inputs = s12_labels.dry_inputs() if args.dry else s12_labels.paper_inputs(args.run)
        if args.finish:
            pre = Path(args.dir) if args.dir else s12_labels.pre_reads_dir(inputs.run, _env.PROJECT_ROOT / "results", dry=args.dry)
            doc = None if args.dry else (Path(args.doc_dir) if args.doc_dir else s12_labels.analysis_dir(inputs.run, _env.PROJECT_ROOT / "results"))
            s12_labels.finish_label_checks(pre, _env.PROJECT_ROOT / "results", inputs=inputs, doc_dir=doc)
        else:
            s12_labels.label_tables(Path(args.dir) if args.dir else s12_labels.pre_reads_dir(inputs.run, _env.RESULTS_DIR, dry=args.dry), inputs=inputs)
        return 0
    if args.cmd == "s11-label-checks":
        from vpd_audit import env as _env
        from vpd_audit import tier6

        if args.finish:
            tier6.finish_label_checks(args.run, Path(args.dir) if args.dir else _env.PROJECT_ROOT / "results" / "grid" / "pre_reads" / args.run / "s11", _env.PROJECT_ROOT / "results")
        else:
            tier6.label_tables(args.run, Path(args.dir) if args.dir else _env.RESULTS_DIR / "grid" / "pre_reads" / args.run / "s11")
        return 0
    if args.cmd == "analyze-s11":
        import json as _json

        from vpd_audit import analysis_s11
        from vpd_audit import env as _env
        from vpd_audit.stats import N_REPLICATES
        from vpd_audit.tier6 import SUBSET, committed_roots, root_name

        results = _env.PROJECT_ROOT / "results"
        store = Path(args.store) if args.store else results / "grid" / root_name(args.run) / "tier6" / f"E__{SUBSET}"
        out = Path(args.out) if args.out else results / "grid" / "analysis" / args.run / "s11"
        summary = analysis_s11.analyze_s11(store, out, run=args.run, committed_roots=committed_roots(results, args.run), freeze=args.freeze, replicates=args.replicates or N_REPLICATES, master_seed=args.master_seed)
        print(_json.dumps({k: summary[k] for k in ("run", "outcome", "verdict", "reason", "freeze")}, indent=1, default=str))
        return 0

    if args.cmd == "s9-checks":
        from vpd_audit import env as _env
        from vpd_audit import s9_checks

        if args.cache_half:
            if args.dry:
                s9_checks.run_cache_half("simplestories", Path(args.out) if args.out else _env.RESULTS_DIR / "dry_run" / "analysis" / "s9", inputs=s9_checks.dry_inputs(), n_shuffles=args.n_shuffles)
            else:
                s9_checks.run_cache_half(args.run, Path(args.out) if args.out else _env.RESULTS_DIR / "grid" / "analysis" / args.run / "s9", n_shuffles=args.n_shuffles)
            return 0
        if args.pull:
            s9_checks.pull_command(args.run, frozen=args.frozen)
            return 0
        s9_checks.run_s9_checks(args.run, frozen=args.frozen, out_dir=Path(args.out) if args.out else None, replicates=args.replicates or s9_checks.REPLICATES)
        return 0
    if args.cmd == "s9-example-positions":
        import hashlib

        from vpd_audit import env as _env
        from vpd_audit import tier5
        from vpd_audit.data import load_set

        n = load_set("E")[0].shape[0]
        text = tier5.example_positions_csv(tier5.example_positions(n, master_seed=args.master_seed))
        out = Path(args.out) if args.out else _env.PROJECT_ROOT / "results" / "grid" / "pre_reads" / args.run / "s9b" / "example_positions.csv"
        out.parent.mkdir(parents=True, exist_ok=True)
        with open(out, "w", newline="") as f:
            f.write(text)
        print(f"[s9 example positions] {n} texts, {text.count(chr(10)) - 1} positions -> {out}; sha256 {hashlib.sha256(text.encode()).hexdigest()} (tier5.EXAMPLE_POSITIONS_SHA256[{args.run!r}] must be this)")
        return 0
    if args.cmd == "s9-pre-reads":
        from vpd_audit import env as _env
        from vpd_audit import s9_checks, s9_pre_reads

        if args.finish:
            s9_pre_reads.finish_s9_pre_reads(Path(args.out) if args.out else s9_pre_reads.pre_reads_dir(args.run), stores_root=_env.PROJECT_ROOT / "results" / "grid" / args.run)
        elif args.dry:
            s9_pre_reads.run_s9_pre_reads("simplestories", Path(args.out) if args.out else _env.RESULTS_DIR / "dry_run" / "pre_reads" / "s9", inputs=s9_checks.dry_inputs())
        else:
            s9_pre_reads.run_s9_pre_reads(args.run, Path(args.out) if args.out else _env.RESULTS_DIR / "grid" / "pre_reads" / args.run / "s9")
        return 0
    if args.cmd == "figures-s9":
        from vpd_audit import figures_s9

        made = figures_s9.draw_s9(Path(args.out) if args.out else figures_s9.OUT_DIR)
        for key, m in made.items():
            print(f"[figures s9] {key}: {m['png']} ({m['size_inches'][0]:g} x {m['size_inches'][1]:g} in at {m['dpi']} dpi); {m['rows']} rows in {m['csv']}")
        return 0
    if args.cmd == "fetch":
        from vpd_audit.artifacts import ALL_RUN_IDS, fetch_artifacts

        fetch_artifacts(list(ALL_RUN_IDS) if args.all else args.runs, replace=args.replace)
        return 0
    if args.cmd == "verify-artifacts":
        from vpd_audit.artifacts import verify_manifest

        for rel in verify_manifest(run_ids=args.runs):
            print(f"[verify] ok {rel}")
        return 0
    if args.cmd == "prepare-data":
        from vpd_audit.data import prepare_labeled_sets, prepare_stream_sets

        if args.labeled:
            prepare_labeled_sets(num_proc=args.num_proc, results_dir=Path("results/data"))
        else:
            prepare_stream_sets()
        return 0
    if args.cmd == "smoke":
        from vpd_audit.smoke import format_checks, run_smoke

        device = _device(args.device)
        precision = args.precision or ("bf16" if device.startswith("cuda") else "fp32")
        kwargs = {}
        if args.sizes:
            kwargs["subbatch_sizes"] = tuple(args.sizes)
        checks = run_smoke(args.run, args.n, precision=precision, device=device, subbatch=args.subbatch, n_draws=args.n_draws,
                           master_seed=args.master_seed, **kwargs)
        print(format_checks(checks))
        failed = [c for c in checks if c.passed is False]
        print(f"[smoke] {len([c for c in checks if c.passed is True])} pass, {len(failed)} fail, {len([c for c in checks if c.passed is None])} reported")
        return 1 if failed else 0
    if args.cmd == "acceptance":
        from vpd_audit.acceptance import run_acceptance

        kwargs = {}
        if args.jobs:
            kwargs["jobs"] = tuple(args.jobs)
        run_acceptance(device=_device(args.device), subbatch=args.subbatch, n_draws=args.n_draws, n=args.n, check6=not args.no_check6,
                       out_root=Path(args.out) if args.out else None, primary=args.primary, fp32_job=args.fp32_job, control_job=args.control_job,
                       check6_batch=args.check6_batch, check6_n_batches=args.check6_n_batches, stat_batch=args.stat_batch, **kwargs)
        return 0
    if args.cmd == "acceptance-report":
        from vpd_audit.acceptance import summarize

        summarize(Path(args.dir), primary=args.primary, fp32_job=args.fp32_job, control_job=args.control_job, stat_batch=args.stat_batch)
        return 0
    if args.cmd == "check6-report":
        import json

        from vpd_audit.short_runs import check6_summary

        summary, text = check6_summary(Path(args.dir), Path(args.acceptance), args.precision)
        with open(Path(args.dir) / f"checks_{args.precision}.txt", "w") as f:
            f.write(text + "\n")
        with open(Path(args.dir) / "check6_summary.json", "w") as f:
            json.dump(summary, f, indent=2, sort_keys=True)
        print(text)
        return 0
    if args.cmd == "dry-run":
        import torch

        from vpd_audit import env as _env
        from vpd_audit.artifacts import load_component_model
        from vpd_audit.grid import GridConfig, run_grid

        device = _device(args.device)
        precision = args.precision or ("bf16" if device.startswith("cuda") else "fp32")
        torch.use_deterministic_algorithms(True, warn_only=True)
        cfg = GridConfig(run="simplestories", set_map={"E": "E_dry", "E_lab": "E_lab_dry"}, pool_map={"D_unif": "D_unif_dry", "D_code": "D_code_dry", "D_prose": "D_prose_dry"},
                         cache_tag="dry_simplestories", draws=args.draws, precision=precision, subbatch=args.subbatch, chunk=args.chunk, tiers=tuple(args.tiers),
                         only_groups=tuple(args.groups) if args.groups else None, subset_name=args.subset,
                         job_title=f"The dry run of the grid{', the ' + args.subset + ' subset' if args.subset else ''}")
        if 4 in cfg.tiers or 5 in cfg.tiers:  # the stand-in's forced code-leaning group, as in its pre-read (tier 5's plain_terms subset re-runs the chain's cells)
            from vpd_audit.code_leaning import STAND_IN_GROUP, STAND_IN_WIDE

            cfg.code_leaning_group, cfg.code_leaning_wide, cfg.code_leaning_force = STAND_IN_GROUP, STAND_IN_WIDE, True
        t5_kwargs = {}
        if 5 in cfg.tiers:  # the stand-in's documents are blocks of four rows, as in s9_checks.dry_inputs; its tier 5 goes to a root of its own
            from vpd_audit.s9_checks import dry_inputs

            cfg.synthetic_document_rows = dry_inputs().synthetic_document_rows
            cfg.job_title, cfg.job_prefix = f"The dry run of tier 5, the {args.subset} subset", "dry_s9"
            t5_kwargs = dict(s9_pre_reads_dir=Path(args.s9_pre_reads) if args.s9_pre_reads else _env.RESULTS_DIR / "dry_run" / "pre_reads" / "s9",
                             committed_roots=tuple(Path(p) for p in args.committed_roots) if args.committed_roots else None, require_s9=False)
        model = load_component_model("simplestories", device)
        out_root = Path(args.out) if args.out else (_env.RESULTS_DIR / "dry_run_s9" / "tier5" if 5 in cfg.tiers else _env.RESULTS_DIR / "dry_run")
        run_grid(model, cfg, out_root, pre_reads_manifest=_env.RESULTS_DIR / "dry_run" / "pre_reads" / "manifest.json", require_pre_reads_hash=False,
                 s7_pre_reads_dir=Path(args.s7_pre_reads) if args.s7_pre_reads else _env.RESULTS_DIR / "dry_run" / "pre_reads" / "s7", **t5_kwargs)
        if args.corner_check:
            from vpd_audit.data import load_set
            from vpd_audit.level_check import level_corner_check
            from vpd_audit.sources import Cache, union_source

            d_unif = Cache.load("D_unif_dry_simplestories")
            alive_set = union_source(d_unif, range(d_unif.n_positions), 0.1)
            ids_e, _, _ = load_set("E_dry")
            store = next((d for d in (out_root / "E", out_root / f"E__{args.subset}") if (d / "per_sequence.parquet").is_file()), None)
            corner = level_corner_check(model, ids_e, alive_set, run="simplestories", precision=precision, subbatch=args.subbatch, chunk=args.chunk, store_dir=store)
            with open(out_root / "level_corner_check.json", "w") as f:
                json.dump(corner, f, indent=2, sort_keys=True, default=str)
            print(json.dumps({k: corner[k] for k in ("pass", "n_sequences", "store_dir")}, indent=1))
        return 0
    if args.cmd == "analyze":
        from vpd_audit import env as _env
        from vpd_audit.analysis import analyze
        from vpd_audit.stats import N_REPLICATES

        results = _env.PROJECT_ROOT / "results"
        dry = args.run == "simplestories"
        root = Path(args.root) if args.root else (results / "dry_run" if dry else results / "grid" / args.run)
        out = Path(args.out) if args.out else (results / "dry_run" / "analysis" if dry else results / "grid" / "analysis" / args.run)
        pre = results / "dry_run" / "pre_reads" if dry else results / "grid" / "pre_reads" / args.run
        verify = results / "grid" / "main" / "verify" if args.run == "main" else None  # the canary is the main run's; on the control it would match nothing
        if args.tiers is not None and not dry:
            # a subset of tiers: every store under the run's root is loaded (the references asserted bitwise across all of them) and the
            # cells of the other tiers dropped by analyze(tiers=...); the earlier temporary root of symlinks found nothing, since
            # Path.rglob does not follow symlinked directories
            for t in args.tiers:
                assert (root / f"tier{t}").is_dir(), f"no {root / f'tier{t}'}"
        compare = compare_pre = None
        if args.compare_with:  # a run name: its tier stores under results/grid/<run>/ and its pre-reads; or a stores root (the dry run's, for the self-comparison)
            if Path(args.compare_with).is_dir():
                compare, compare_pre = Path(args.compare_with), pre
            else:
                compare, compare_pre = results / "grid" / args.compare_with, results / "grid" / "pre_reads" / args.compare_with
        summary = analyze(root, out, frozen=args.frozen, pre_reads_dir=pre if pre.is_dir() else None, verify_dir=verify, replicates=args.replicates or N_REPLICATES, master_seed=args.master_seed,
                          tiers=tuple(args.tiers) if args.tiers is not None else None, compare_with=compare, compare_pre_reads_dir=compare_pre, extra_roots=tuple(Path(x) for x in (args.extra_root or ())))
        import json as _json

        print(_json.dumps({k: v for k, v in summary.items() if k in ("run", "seconds", "report", "preconditions", "labels", "sanity", "two_path")}, indent=1, default=str))
        return 0
    if args.cmd == "analyze-s9":
        import json as _json

        from vpd_audit import analysis_s9
        from vpd_audit import env as _env
        from vpd_audit.stats import N_REPLICATES

        results = _env.PROJECT_ROOT / "results"
        dry = args.run == "simplestories"
        assert dry or not (args.no_canary or args.synthetic_document_rows), "--no-canary and --synthetic-document-rows are for the stand-in only"
        spec = analysis_s9.stand_in_spec(args.synthetic_document_rows or analysis_s9.STAND_IN_DOCUMENT_ROWS) if dry else analysis_s9.paper_spec(args.run)
        root = Path(args.root) if args.root else (results / "dry_run_s9" if dry else results / "grid" / f"{args.run}_s9")
        out = Path(args.out) if args.out else (results / "dry_run_s9" / "analysis" if dry else results / "grid" / "analysis" / args.run / "s9b")
        committed = tuple(Path(x) for x in args.committed_root) if args.committed_root else ((results / "dry_run", results / "dry_run_s7") if dry else (results / "grid" / args.run,))
        summary = analysis_s9.analyze_s9(root, out, spec=spec, frozen=args.frozen, committed_roots=None if args.no_canary else committed, require_canary=not args.no_canary, replicates=args.replicates or N_REPLICATES,
                                         master_seed=args.master_seed)
        print(_json.dumps({k: summary[k] for k in ("run", "seconds", "report", "frozen")}, indent=1, default=str))  # gates, assertions, and the rules' words are logged above; the numbers are in the report
        return 0
    if args.cmd == "pre-reads":
        from vpd_audit import env as _env
        from vpd_audit.pre_reads import run_pre_reads

        run_pre_reads(args.run, Path(args.out) if args.out else _env.RESULTS_DIR / "grid" / "pre_reads" / args.run, draws=args.draws)
        return 0
    if args.cmd == "pre-reads-s7":
        from vpd_audit import env as _env
        from vpd_audit.pre_reads import CL_N_SHUFFLES, S7_N_SEEDS, PreReadInputs, run_pre_reads_s7

        n_seeds, n_shuffles = args.n_seeds or S7_N_SEEDS, args.n_shuffles or CL_N_SHUFFLES
        if args.dry:
            draws = args.draws or 2
            inp = PreReadInputs(run="simplestories", cache_tag="dry_simplestories", set_map={"E": "E_dry", "E_lab": "E_lab_dry"},
                                pool_map={"D_unif": "D_unif_dry", "D_code": "D_code_dry", "D_prose": "D_prose_dry"}, strata_file="E_lab_dry.strata.json", chains_dir=None, draws=draws, positive_stratum="dialogue")
            from vpd_audit.code_leaning import STAND_IN_GROUP, STAND_IN_WIDE

            run_pre_reads_s7("simplestories", Path(args.out) if args.out else _env.RESULTS_DIR / "dry_run" / "pre_reads" / "s7", draws=draws, inputs=inp, n_seeds=n_seeds, n_shuffles=n_shuffles,
                             group_threshold=STAND_IN_GROUP, wide_threshold=STAND_IN_WIDE, force_chain=True)  # the stand-in's forced group (code_leaning.py)
        else:
            run_pre_reads_s7(args.run, Path(args.out) if args.out else _env.RESULTS_DIR / "grid" / "pre_reads" / args.run / "s7", draws=args.draws or 8, n_seeds=n_seeds, n_shuffles=n_shuffles)
        return 0
    if args.cmd == "pre-reads-s7-finish":
        from vpd_audit.pre_reads import finish_pre_reads_s7

        finish_pre_reads_s7(Path(args.dir), stores_root=Path(args.stores_root) if args.stores_root else None, calibration=Path(args.calibration) if args.calibration else None)
        return 0
    if args.cmd == "code-filter":
        from vpd_audit import env as _env
        from vpd_audit.codefilter import calibrate

        calibrate(sets_dir=Path(args.sets_dir) if args.sets_dir else _env.SETS_DIR, out_dir=Path(args.out), master_seed=args.master_seed, acceptance_dir=Path(args.acceptance))
        return 0
    if args.cmd == "round-trip":
        from vpd_audit.roundtrip import run_round_trip

        out = run_round_trip(args.sets, Path(args.out))
        return 0 if all(v["passed"] for v in out["sets"].values()) else 1
    if args.cmd == "residual-rank":
        import json

        from vpd_audit.artifacts import checkpoint_hashes, load_component_model
        from vpd_audit.residual_rank import format_residual_rank, residual_rank
        from vpd_audit.results import code_commits

        res = residual_rank(load_component_model(args.run, "cpu"))
        out = Path(args.out)
        out.mkdir(parents=True, exist_ok=True)
        with open(out / "summary.json", "w") as f:
            json.dump({"run": args.run, "checkpoint_hashes": checkpoint_hashes(args.run), "commits": code_commits(), "per_matrix": res}, f, indent=2, sort_keys=True)
        text = format_residual_rank(res)
        with open(out / "summary.md", "w") as f:
            f.write(text + "\n")
        print(text)
        return 0
    if args.cmd == "check6-unrounded":
        from vpd_audit.short_runs import check6_unrounded

        _, text = check6_unrounded(Path(args.acceptance), Path(args.out), args.precision)
        print(text.split("\n\n| quantity")[0])
        return 0
    if args.cmd == "residual-matrix-report":
        import json

        from vpd_audit.residual_matrix import residual_matrix_summary

        summary, text = residual_matrix_summary(Path(args.dir), Path(args.short_runs) if args.short_runs else None)
        with open(Path(args.dir) / "summary.json", "w") as f:
            json.dump(summary, f, indent=2, sort_keys=True)
        with open(Path(args.dir) / "summary.md", "w") as f:
            f.write(text + "\n")
        print(text)
        return 0
    if args.cmd == "short-runs-report":
        import json

        from vpd_audit.short_runs import residual_summary

        summary, text = residual_summary(Path(args.dir), Path(args.acceptance) if args.acceptance else None)
        with open(Path(args.dir) / "summary.json", "w") as f:
            json.dump(summary, f, indent=2, sort_keys=True)
        with open(Path(args.dir) / "summary.md", "w") as f:
            f.write(text + "\n")
        print(text)
        return 0
    return 2


if __name__ == "__main__":
    sys.exit(main())
