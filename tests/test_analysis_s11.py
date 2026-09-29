"""The known-answer tests of analysis_s11.py on fabricated stores.

A fabricated tier-6 store and fabricated committed roots (tier 1 on E with the headline union at 8 and 64 tokens, tier 3's curve1_extra at
16, tier 4's look-alike sets, tier 5's self-merge) hold planted per-text divergences in units of 1/4096, so that float32 storage and every
difference are exact. Each scenario plants the primary form's excess at each size and the self-merge's, and the rule must return its
known outcome: A, B, C, the two stops of step 1, and a draw pattern with six of eight draws positive that fails the sign condition (seven
of eight passes). Then the numbers of step 2 against the planted ones, a self-merge outside its band making the outcome B, byte-identical outputs
across two runs, the loader's refusals (the canary one ulp off, a set that is not its twin's, P3, a missing cell, a failed or incomplete
store, comparators that are not the table's), and the guard's refusals (a dirty tree, no freeze, a frozen module that is not main's)."""

from __future__ import annotations

import dataclasses
import hashlib
import json
from dataclasses import asdict
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from vpd_audit import analysis_s11 as a11
from vpd_audit import stats as st
from vpd_audit import tier6
from vpd_audit.cells import Cell
from vpd_audit.sources import ROUNDED0_FAMILY

RUN, K, N, SUBBATCH, U = "synthetic", 8, 40, 8, 1.0 / 4096
REPLICATES = 400
IMP, R0, R01, UNM = 1024, 768, 832, 64  # the references, in U: 0.25, 0.1875, 0.203125, 1/64
FRAC = {"2": 164, "2a": 416, "3": 1874, "self": 4218}  # the committed fractional excesses, in U: 0.0400, 0.1016, 0.4575, 1.0298
DRAW = (-4, -3, -2, -1, 1, 2, 3, 4)  # a draw pattern in U that sums to zero
BASE = (np.arange(N) % 5) * 16  # a per-text base under every cell of a text: the texts differ, the excesses do not
WOBBLE = np.where(np.arange(N) % 2 == 0, 1, -1)  # a per-text wobble of the excess, summing to zero, so that no interval is a point
# scenario -> the primary form's excess per size, its draw pattern per size (None: DRAW), and the primary self-merge's excess, in U
SCENARIOS = {
    "A": ({"2": 164, "2a": 416, "3": 1874}, {}, 4218),
    "B": ({"2": 492, "2a": 416, "3": 1874}, {}, 4218),  # three times the fractional at 8 tokens: outside its band
    "C": ({"2": 41, "2a": 82, "3": 164}, {}, 4218),  # 0.01, 0.02, 0.04: nothing material
    "stop_self": ({"2": 164, "2a": 416, "3": 1874}, {}, 82),  # material at 64 tokens, the self-merge at 0.02
    "stop_falling": ({"2": 410, "2a": 410, "3": 164}, {}, 4218),  # material at 8 and 16, not at 64
    "six_of_eight": ({"2": 41, "2a": 82, "3": 820}, {"3": (400, 400, 400, 400, 400, 400, -1200, -1200)}, 4218),  # 0.2 on average, two draws negative
    "seven_of_eight": ({"2": 41, "2a": 82, "3": 820}, {"3": (200, 200, 200, 200, 200, 200, 200, -1400)}, 4218),  # one draw negative
    "B_self_outside": ({"2": 164, "2a": 416, "3": 1874}, {}, 3 * 4218),  # every token size in its band, the self-merge three times the fractional
}
WANT = {"A": ("A", a11.FAILS), "B": ("B", a11.FAILS), "C": ("C", a11.HOLDS), "stop_self": (a11.STOP, a11.STOP), "stop_falling": (a11.STOP, a11.STOP), "six_of_eight": ("C", a11.HOLDS),
        "seven_of_eight": ("B", a11.FAILS), "B_self_outside": ("B", a11.FAILS)}


def h(name: str) -> str:
    return hashlib.sha256(name.encode()).hexdigest()


def union(k: int, r: str, control: str = "none") -> Cell:
    return Cell(RUN, "union", "E", "D_unif", 0.1, "r0", "excluded", k, r, control, 1 if control == "none" else 4)


def ref(cond: str) -> Cell:
    return next(c for c in tier6.reference_cells(RUN) if c.condition == cond)


def write_store(d: Path, cells: list[Cell], kl: dict[str, np.ndarray], *, extra: dict[str, dict] | None = None, run: str = RUN) -> None:
    """A store as run_cells writes it, with the columns the loaders read."""
    d.mkdir(parents=True, exist_ok=True)
    extra = extra or {}
    n_sub = (N + SUBBATCH - 1) // SUBBATCH
    table = [{**asdict(c), "cell": c.name, "n_on": 0, "n_subbatches": n_sub, "source_sha256": None, "matched_source_sha256": None, "n_below_label_total": 0, **extra.get(c.name, {})} for c in cells]
    pd.DataFrame(table).to_parquet(d / "cells.parquet", index=False)
    rows = []
    for c in cells:
        below = int(extra.get(c.name, {}).get("n_below_label_total", 0))
        rows.append(pd.DataFrame({"cell": c.name, "seq": np.arange(N), "kl_mean": np.asarray(kl[c.name], dtype=np.float32), "min_gap": np.float32(-0.05 if below else 0.0), "n_below_label": np.int64(1 if below else 0)}))
    pd.concat(rows, ignore_index=True).to_parquet(d / "per_sequence.parquet", index=False)
    (d / "marker.json").write_text(json.dumps({"done_through": n_sub - 1, "subbatch": SUBBATCH, "n_sequences": N, "cells": [c.name for c in cells]}))
    (d / "run_manifest.json").write_text(json.dumps({"run": run, "n_sequences": N, "n_draws": K, "finished_at": "planted", "commits": {"project": "planted", "dirty": "0"}, "gpu_name": "planted", "precision": "bf16"}))


def values(units: np.ndarray | float) -> np.ndarray:
    return ((np.asarray(units, dtype=np.float64) + BASE) * U).astype(np.float32)


def committed_value(c: Cell) -> np.ndarray:
    """The committed per-text divergence of a headline union cell (own labels plus the fractional excess, a draw pattern, a wobble)."""
    if c.control == "marginal":
        return values(IMP + 30 + np.zeros(N))
    return values(IMP + FRAC[c.rung] + DRAW[c.draw] + WOBBLE)


def make_committed(root: Path) -> tuple[Path, Path]:
    main, s9 = root / "grid" / RUN, root / "grid" / f"{RUN}_s9"
    refs = {"importances": IMP, "rounded_0": R0, "rounded_0.1": R01, "unmasked": UNM}
    ref_cells = [ref(n) for n in refs]
    ref_kl = {ref(n).name: values(np.full(N, v)) for n, v in refs.items()}
    t1 = [union(k, r) for k in range(K) for r in ("2", "3")]
    write_store(main / "tier1" / "E", ref_cells + t1, {**ref_kl, **{c.name: committed_value(c) for c in t1}}, extra={c.name: {"source_sha256": h(c.name)} for c in t1})
    t3 = [dataclasses.replace(union(k, "2a"), tier=3, descriptive=True) for k in range(K)]
    write_store(main / "tier3" / "E__curve1_extra", [ref("importances")] + t3, {ref("importances").name: ref_kl[ref("importances").name], **{c.name: committed_value(c) for c in t3}},
                extra={c.name: {"source_sha256": h(c.name)} for c in t3})
    t4 = [union(k, r, "marginal") for k in range(K) for r in ("2", "2a", "3")]
    write_store(main / "tier4" / "E__marginal", [ref("importances")] + t4, {ref("importances").name: ref_kl[ref("importances").name], **{c.name: committed_value(c) for c in t4}},
                extra={c.name: {"source_sha256": h(c.name)} for c in t4})
    selfc = Cell(RUN, "self_union", "E", "E", 0.1, "r0", "excluded", 0, "4", "none", 5)
    write_store(s9 / "tier5" / "E__self_merge", [ref("importances"), selfc], {ref("importances").name: ref_kl[ref("importances").name], selfc.name: values(IMP + FRAC["self"] + WOBBLE)},
                extra={selfc.name: {"source_sha256": h(selfc.name)}})
    return main, s9


def make_store(d: Path, scenario: str) -> Path:
    prim, pattern, s_prim = SCENARIOS[scenario]
    cells = a11.expected_cells(RUN, K)
    kl, extra = {}, {}
    for c in cells:
        if c.family == "reference":
            kl[c.name] = values(np.full(N, {"importances": IMP, "rounded_0": R0, "rounded_0.1": R01, "unmasked": UNM}[c.condition]))
            continue
        tw = tier6.twin_name(c)
        extra[c.name] = {"source_sha256": h(tw)}
        if c.family == "union":  # the canary: its committed value
            kl[c.name] = committed_value(c)
        elif c.family == "self_union":
            start = R0 if c.own_round == 0.0 else R01
            kl[c.name] = values(start + (s_prim if c.own_round == 0.0 else 4300) + WOBBLE)
            extra[c.name]["n_below_label_total"] = 0 if c.own_round == 0.0 else 5
        elif c.control == "marginal":
            kl[c.name] = values(R0 + 20 + DRAW[c.draw] + WOBBLE)
            extra[c.name]["matched_source_sha256"] = h(dataclasses.replace(c, family="union", control="none").name)
        elif c.family == ROUNDED0_FAMILY:
            kl[c.name] = values(R0 + prim[c.rung] + pattern.get(c.rung, DRAW)[c.draw] + WOBBLE)
        else:  # the secondary form: its own excess, a planted 3/2 of the fractional
            kl[c.name] = values(R01 + (3 * FRAC[c.rung]) // 2 + DRAW[c.draw] + WOBBLE)
            extra[c.name]["n_below_label_total"] = 5
    store = d / "grid" / f"{RUN}_s11" / "tier6" / "E__binary_union"
    write_store(store, cells, kl, extra=extra)
    return store


@pytest.fixture(scope="module")
def committed(tmp_path_factory):
    return make_committed(tmp_path_factory.mktemp("committed"))


def run(store: Path, out: Path, roots, **kw):
    return a11.analyze_s11(store, out, run=RUN, committed_roots=roots, replicates=REPLICATES, log=lambda *_: None, **kw)


# ----------------------------------------------------------------------------- the rule as pure functions


def test_the_verdict_and_the_outcome_words():
    m = lambda a, b, c: {"2": a, "2a": b, "3": c}  # noqa: E731
    assert a11.verdict(m(True, True, True), True) == {"verdict": a11.FAILS, "reason": ""}
    assert a11.verdict(m(False, False, True), True)["verdict"] == a11.FAILS
    assert a11.verdict(m(False, False, False), True)["verdict"] == a11.HOLDS and a11.verdict(m(False, False, False), False)["verdict"] == a11.HOLDS
    assert a11.verdict(m(True, True, True), False) == {"verdict": a11.STOP, "reason": a11.STOP_SELF}
    assert a11.verdict(m(True, False, False), True) == {"verdict": a11.STOP, "reason": a11.STOP_FALLING} == a11.verdict(m(False, True, False), False)
    within = {"2": True, "2a": True, "3": True, "self": True}
    assert a11.outcome(a11.FAILS, within) == "A" and a11.outcome(a11.FAILS, {**within, "2": False}) == "B" and a11.outcome(a11.HOLDS, None) == "C" and a11.outcome(a11.STOP, None) == a11.STOP
    assert a11.outcome(a11.FAILS, {**within, "self": False}) == "B"  # the self-merge's band is part of outcome A's
    assert a11.BAND_SIZES == ("2", "2a", "3", "self")
    assert a11.within_band(0.02, 0.04) and a11.within_band(0.08, 0.04) and not a11.within_band(0.0199, 0.04) and not a11.within_band(0.0801, 0.04) and not a11.within_band(-0.01, 0.04)


def test_step_1_on_planted_arrays_six_of_eight_draws_positive_fails_the_sign_condition():
    rs = st.Resample.make(N, REPLICATES, (0, "boot", "E"))
    e = lambda base, pat: np.stack([(base + pat[k] + WOBBLE) * U for k in range(K)])  # noqa: E731
    six = a11.step1({"2": e(41, DRAW), "2a": e(82, DRAW), "3": e(820, SCENARIOS["six_of_eight"][1]["3"])}, (4218 + WOBBLE) * U, rs)
    r = six["per_size"]["3"]
    assert r["n_draws_positive"] == 6 and not r["sign_condition"] and r["interval"][0] > 0.05 and not r["detected"] and not r["material"] and six["verdict"] == a11.HOLDS
    seven = a11.step1({"2": e(41, DRAW), "2a": e(82, DRAW), "3": e(820, SCENARIOS["seven_of_eight"][1]["3"])}, (4218 + WOBBLE) * U, rs)
    assert seven["per_size"]["3"]["n_draws_positive"] == 7 and seven["per_size"]["3"]["material"] and seven["verdict"] == a11.FAILS
    assert six["self"]["material"] and six["self"]["m"] == a11.M == 4 and r["m"] == 4


# ----------------------------------------------------------------------------- the planted stores


@pytest.mark.parametrize("scenario", sorted(SCENARIOS))
def test_the_planted_stores_return_their_outcomes(scenario, committed, tmp_path):
    store = make_store(tmp_path, scenario)
    out = tmp_path / "out"
    s = run(store, out, committed)
    word, verdict = WANT[scenario]
    assert s["outcome"] == word and s["verdict"] == verdict
    report = (out / "report.md").read_text()
    assert report.splitlines()[0] == f"# Outcome: {word}" + (f" ({s['reason']})" if word == a11.STOP else "")
    assert a11.WORDING_C in report and a11.WORDING_ASYMMETRY in report and "switched mass" not in (out / "s11_step1.csv").read_text()
    files = {p.name for p in out.iterdir()}
    if word == a11.STOP:
        assert s["reason"] == (a11.STOP_SELF if scenario == "stop_self" else a11.STOP_FALLING) and "nothing further is read" in report
        assert files == {"report.md", "summary.json", "s11_step1.csv", "s11_verdict.csv", "s11_canary.csv", "s11_frozen_modules.csv"}
    else:
        assert {"s11_secondary.csv", "s11_control.csv", "s11_absolute.csv"} <= files and ("s11_step2.csv" in files) == (verdict == a11.FAILS)
    # the canary and the sets were asserted, and P3 on the primary form
    can = pd.read_csv(out / "s11_canary.csv")
    # named binary sets: the primary at three sizes, the secondary at 16 tokens (tier 6) and at 8 and 64 (tier 3), every draw
    assert len(can) == 5 and can["bitwise_equal"].all() and s["checks"]["canary"]["sets"] == {"binary_named_sets": 6 * K, "look_alike_sets": 3 * K, "look_alike_matched_sets": 3 * K, "self_merge_sets": 2, "canary": 1}
    assert s["checks"]["p3"]["primary_cells"] == 6 * K + 1 and s["checks"]["p3"]["primary_entries_below_label"] == 0 and s["checks"]["p3"]["secondary_cells_with_entries_below_label"] == 3 * K + 1
    assert s["checks"]["complete"]["n_cells"] == 58 + 16 + 5 and s["comparators"]["recomputed"] == pytest.approx({j: v * U for j, v in FRAC.items()}, abs=1e-12)


def test_the_numbers_of_step_2_and_the_descriptions(committed, tmp_path):
    s = run(make_store(tmp_path, "B"), tmp_path / "out", committed)
    s2 = s["step2"]
    prim = SCENARIOS["B"][0]
    for j in ("2", "2a", "3"):
        assert s2[j]["e_bin"] == pytest.approx(prim[j] * U, abs=1e-12) and s2[j]["e_frac"] == pytest.approx(FRAC[j] * U, abs=1e-12)
        assert s2[j]["difference"] == pytest.approx((prim[j] - FRAC[j]) * U, abs=1e-12) and s2[j]["band"] == pytest.approx([0.5 * FRAC[j] * U, 2 * FRAC[j] * U])
        lo, hi = s2[j]["difference_interval"]
        assert lo == pytest.approx((prim[j] - FRAC[j]) * U, abs=1e-9) and hi == pytest.approx((prim[j] - FRAC[j]) * U, abs=1e-9)  # the pairing takes the planted draws and wobbles out exactly
    assert [s2[j]["within_band"] for j in ("2", "2a", "3", "self")] == [False, True, True, True]
    t = pd.read_csv(tmp_path / "out" / "s11_step1.csv").set_index("rung")
    assert t.loc["3", "excess"] == pytest.approx(1874 * U) and bool(t.loc["3", "material"]) and t.loc["self", "excess"] == pytest.approx(4218 * U)
    sec = pd.read_csv(tmp_path / "out" / "s11_secondary.csv").set_index("rung")
    assert sec.loc["2", "excess_over_rounded_0.1"] == pytest.approx((3 * FRAC["2"] // 2) * U) and sec.loc["self", "excess_over_rounded_0.1"] == pytest.approx(4300 * U)
    ctl = pd.read_csv(tmp_path / "out" / "s11_control.csv").set_index("rung")
    assert ctl.loc["3", "control_excess_over_rounded_0"] == pytest.approx(20 * U) and ctl.loc["3", "primary_minus_control"] == pytest.approx((1874 - 20) * U)
    ab = pd.read_csv(tmp_path / "out" / "s11_absolute.csv").set_index("mask")["mean_divergence"]
    assert ab["rounded_0 (the primary's start)"] == pytest.approx((R0 + BASE.mean()) * U) and ab["self-merge, own labels rounded at 0.1"] == pytest.approx((R01 + 4300 + BASE.mean()) * U)


def test_a_self_merge_outside_its_band_makes_the_outcome_b(committed, tmp_path):
    """The self-merge's band is read by outcome A's rule, beside the three token sizes."""
    s = run(make_store(tmp_path, "B_self_outside"), tmp_path / "out", committed)
    assert s["outcome"] == "B" and s["step2"]["self"]["within_band"] is False and all(s["step2"][j]["within_band"] for j in ("2", "2a", "3"))
    assert all(s["step2"][j]["read_by_the_rule"] for j in ("2", "2a", "3", "self")) and s["band_sizes"] == ["2", "2a", "3", "self"]
    t = pd.read_csv(tmp_path / "out" / "s11_step2.csv").set_index("rung")
    assert not bool(t.loc["self", "within_band"]) and bool(t.loc["self", "read_by_the_rule"])
    assert "Outcome A needs every one of 8 tokens, 16 tokens, 64 tokens, the self-merge within its band." in (tmp_path / "out" / "report.md").read_text()


def test_two_runs_give_byte_identical_outputs(committed, tmp_path):
    store = make_store(tmp_path, "A")
    run(store, tmp_path / "one", committed)
    run(store, tmp_path / "two", committed)
    one, two = sorted(p.name for p in (tmp_path / "one").iterdir()), sorted(p.name for p in (tmp_path / "two").iterdir())
    assert one == two and all((tmp_path / "one" / f).read_bytes() == (tmp_path / "two" / f).read_bytes() for f in one)


def test_the_loader_refuses(committed, tmp_path):
    from vpd_audit.tier5 import GateFailure

    def fresh(name: str) -> Path:
        return make_store(tmp_path / name, "A")

    def edit_rows(store: Path, fn) -> None:
        r = pd.read_parquet(store / "per_sequence.parquet")
        fn(r)
        r.to_parquet(store / "per_sequence.parquet", index=False)

    def edit_cells(store: Path, fn) -> None:
        c = pd.read_parquet(store / "cells.parquet")
        fn(c)
        c.to_parquet(store / "cells.parquet", index=False)

    # the canary one ulp off on one text
    s = fresh("ulp")
    name = f"{RUN}/E/ref/rounded_0"

    def ulp(r):
        i = r.index[(r["cell"] == name) & (r["seq"] == 7)][0]
        r.loc[i, "kl_mean"] = np.nextafter(np.float32(r.loc[i, "kl_mean"]), np.float32(9))

    edit_rows(s, ulp)
    with pytest.raises(AssertionError, match="THE CANARY FAILS"):
        run(s, tmp_path / "o1", committed)
    # a binary cell whose set is not its twin's
    s = fresh("set")
    edit_cells(s, lambda c: c.__setitem__("source_sha256", c["source_sha256"].where(c["cell"] != f"{RUN}/E/rounded0_own_g/D_unif/tau0.1/r0/excl/k3/r2a", h("other"))))
    with pytest.raises(GateFailure, match="is not its committed twin"):
        run(s, tmp_path / "o2", committed)
    # P3: a cell of the primary form with an entry below its label
    s = fresh("p3")
    edit_cells(s, lambda c: c.__setitem__("n_below_label_total", c["n_below_label_total"].where(c["cell"] != f"{RUN}/E/self_union/E/tau0.1/r0/excl/k0/r4/ownround0", 1)))
    with pytest.raises(AssertionError, match="P3"):
        run(s, tmp_path / "o3", committed)
    # a missing cell
    s = fresh("missing")
    gone = f"{RUN}/E/rounded_own_g/D_unif/tau0.1/r0/excl/k5/r3"
    edit_cells(s, lambda c: c.drop(c.index[c["cell"] == gone], inplace=True))
    edit_rows(s, lambda r: r.drop(r.index[r["cell"] == gone], inplace=True))
    m = json.loads((s / "marker.json").read_text())
    (s / "marker.json").write_text(json.dumps({**m, "cells": [x for x in m["cells"] if x != gone]}))
    with pytest.raises(AssertionError, match="not the launch's cells"):
        run(s, tmp_path / "o4", committed)
    # a store with a recorded failure; an incomplete store
    s = fresh("error")
    (s / "error.txt").write_text("boom")
    with pytest.raises(AssertionError, match="error.txt"):
        run(s, tmp_path / "o5", committed)
    s = fresh("incomplete")
    m = json.loads((s / "marker.json").read_text())
    (s / "marker.json").write_text(json.dumps({**m, "done_through": 2}))
    with pytest.raises(AssertionError, match="not complete"):
        run(s, tmp_path / "o6", committed)
    # the comparators held to a table they are not
    with pytest.raises(AssertionError, match="not the table fixed in advance"):
        run(fresh("table"), tmp_path / "o7", committed, expected_comparators=a11.REGISTERED_COMPARATORS)
    assert run(fresh("table_ok"), tmp_path / "o8", committed, expected_comparators={j: round(v * U, 4) for j, v in FRAC.items()})["outcome"] == "A"
    # a committed root that is the store's own
    s = fresh("overlap")
    with pytest.raises(AssertionError, match="overlap"):
        run(s, tmp_path / "o9", (s.parent,))
    # a store of another run than the one named
    with pytest.raises(AssertionError, match="not 'simplestories'"):
        a11.analyze_s11(fresh("other_run"), tmp_path / "o10", run="simplestories", committed_roots=committed, replicates=REPLICATES, log=lambda *_: None)


def test_the_guard(monkeypatch):
    from vpd_audit import results

    g = a11.freeze_guard(None, enforce=False)
    assert [r["module"] for r in g["frozen_modules"]] == [f"vpd_audit/{m}" for m in a11.FROZEN_MODULES] and len(g["frozen_modules"]) == 9
    assert g["this_module"]["module"] == "vpd_audit/analysis_s11.py" and g["frozen_modules_pass"] and not g["enforced"]
    monkeypatch.setattr(results, "code_commits", lambda: {"project": "x", "submodule": "y", "dirty": "1"})
    lines: list[str] = []
    with pytest.raises(AssertionError, match="dirty tree"):
        a11.freeze_guard("HEAD", enforce=True, log=lines.append)
    assert [ln.split(":")[0].split()[-1] for ln in lines[1:]] == [f"vpd_audit/{m}" for m in a11.FROZEN_MODULES] + ["vpd_audit/analysis_s11.py"]  # every blob printed before the refusal
    monkeypatch.setattr(results, "code_commits", lambda: {"project": "x", "submodule": "y", "dirty": "0"})
    with pytest.raises(AssertionError, match="--freeze"):
        a11.freeze_guard(None, enforce=True)
    with pytest.raises(AssertionError, match="--freeze"):
        a11.freeze_guard("HEAD", enforce=True)  # a freeze is a commit hash of at least seven characters
    head = a11._git("rev-parse", "HEAD")
    # the paper's run: the guard stops the analysis before the store is opened (no store at this path; the guard speaks first)
    monkeypatch.setattr(results, "code_commits", lambda: {"project": "x", "submodule": "y", "dirty": "1"})
    with pytest.raises(AssertionError, match="dirty tree"):
        a11.analyze_s11(Path("/nonexistent/store"), Path("/nonexistent/out"), run="main", committed_roots=(), freeze=head, log=lambda *_: None)
    monkeypatch.setattr(results, "code_commits", lambda: {"project": "x", "submodule": "y", "dirty": "0"})
    real = a11._blob
    monkeypatch.setattr(a11, "_blob", lambda rev, m: "0" * 40 if (rev == "main" and m == "stats_s9.py") else real(rev, m))
    with pytest.raises(AssertionError, match="not main's blob"):
        a11.freeze_guard(head, enforce=True)


def test_the_store_the_analysis_expects_is_the_launchs():
    """On the main run: the tier-6 launch's selection, its four references, and its canary, name for name."""
    want = tier6.launch_cells("main") + tier6.reference_cells("main") + tier6.canary_cells("main")
    got = a11.expected_cells("main", 8)
    assert sorted(c.name for c in got) == sorted(c.name for c in want) and len(got) == 79
    assert {c.name: c for c in got} == {c.name: c for c in want}
