"""The known-answer tests of stats_s12.py and analysis_s12.py: the panel readings on the worked example (keep, soften, drop), a panel of
nine documents with no interval, a document resample in which the rows of one document always enter together, the statistics against a
by-hand computation, the whole analysis on planted tier-7 stores and committed roots (the stand-in's run, so that its five panels and edit
sizes apply) with its refusals, the replication and the removed label on the committed E_lab store and the committed label-only table
of removed labels of the paper's model, and the guard."""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, replace
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from vpd_audit import analysis_s12 as A
from vpd_audit import stats_s12 as S
from vpd_audit import tier7
from vpd_audit.cells import Cell, _references, tier_7_cells

X = S.X


def _stats(h_iv, rho_iv, readable=True):
    return {"H_interval": h_iv, "rho_interval": rho_iv, "rho_readable": readable}


# ----------------------------------------------------------------------------- the rule on the worked example


def test_the_worked_example_reads_keep_soften_and_drop():
    keep = S.reading(_stats([0.12, 0.25], [1.2, 1.9]), _stats([0.12, 0.25], [1.6, 2.5]))
    assert keep["word"] == S.KEEP and keep["rho_sides"] == {"small": S.ABOVE, "large": S.ABOVE}
    # only rho at the larger size changed to 1.1 [0.9, 1.3]: soften, rho above 1 at the smaller size and neither at the larger
    soft = S.reading(_stats([0.12, 0.25], [1.2, 1.9]), _stats([0.12, 0.25], [0.9, 1.3]))
    assert soft["word"] == S.SOFTEN and soft["rho_sides"] == {"small": S.ABOVE, "large": S.NEITHER}
    # H 0.12 [0.08, 0.16] with rho 0.6 [0.4, 0.8]: soften, not drop, since the damage clears X; rho lies below 1
    soft2 = S.reading(_stats([0.08, 0.16], [0.4, 0.8]), _stats([0.08, 0.16], [0.6, 0.9]))
    assert soft2["word"] == S.SOFTEN and soft2["rho_sides"]["small"] == S.BELOW
    # H 0.03 [0.02, 0.04]: drop, whatever rho is
    for rho in ([1.2, 1.9], [0.4, 0.8], [0.9, 1.3]):
        assert S.reading(_stats([0.02, 0.04], rho), _stats([0.5, 0.9], rho))["word"] == S.DROP
    # the bars exactly: the lower end at X keeps; an upper end at X does not drop
    assert S.reading(_stats([X, 0.2], [1.01, 2.0]), _stats([X, 0.2], [1.01, 2.0]))["word"] == S.KEEP
    assert S.reading(_stats([0.01, X], [0.5, 0.9]), _stats([0.01, X], [0.5, 0.9]))["word"] == S.SOFTEN
    # rho's interval exactly at 1 is not above 1
    assert S.reading(_stats([0.1, 0.2], [1.0, 2.0]), _stats([0.1, 0.2], [1.5, 2.0]))["word"] == S.SOFTEN
    # a rho with a non-finite replicate is not read, so it cannot keep
    unread = S.reading(_stats([0.12, 0.25], [1.2, 1.9], readable=False), _stats([0.12, 0.25], [1.6, 2.5]))
    assert unread["word"] == S.SOFTEN and unread["rho_sides"]["small"] == S.NOT_READ


def test_a_panel_of_nine_documents_has_no_interval_and_no_reading():
    h, t = np.linspace(0.1, 0.2, 18), np.linspace(0.05, 0.06, 18)
    docs = np.arange(18) // 2  # nine documents
    rs = S.document_resample(docs, 100, (0, "boot_docs", "s12_panel", "p"))
    st9 = S.edit_statistics(h, t, rs, 9)
    assert st9["H_interval"] is None and st9["rho_interval"] is None and st9["H"] == pytest.approx(h.mean()) and st9["rho"] == pytest.approx(h.mean() / t.mean())
    assert S.reading(st9, st9)["word"] is None
    docs10 = np.arange(20) // 2
    st10 = S.edit_statistics(np.linspace(0.1, 0.2, 20), np.linspace(0.05, 0.06, 20), S.document_resample(docs10, 100, (0, "x")), 10)
    assert st10["H_interval"] is not None and st10["rho_readable"]


def test_the_rows_of_a_document_always_enter_together():
    docs = np.array([0, 0, 1, 2, 2, 2, 3, 4, 4, 5, 6, 7, 8, 9, 9, 10])
    rs = S.document_resample(docs, 500, (0, "boot_docs", "s12_panel", "panel_ArXiv"))
    W = rs.W
    for d in np.unique(docs):
        cols = np.flatnonzero(docs == d)
        assert all(np.array_equal(W[:, cols[0]], W[:, c]) for c in cols[1:])
    assert np.all(W[:, np.unique(docs, return_index=True)[1]].sum(axis=1) == np.unique(docs).size)  # as many document draws as documents
    assert np.array_equal(S.document_resample(docs, 500, (0, "boot_docs", "s12_panel", "panel_ArXiv")).W, W)  # the seed fixes it


def test_edit_statistics_against_a_computation_by_hand():
    rng = np.random.default_rng(4)
    docs = np.repeat(np.arange(12), 3)
    h, t = rng.uniform(0.1, 0.4, 36), rng.uniform(0.05, 0.1, 36)
    rs = S.document_resample(docs, 300, (0, "x"))
    got = S.edit_statistics(h, t, rs, 12)
    W = rs.W.astype(np.float64)
    Hr, Tr = (W @ h) / W.sum(axis=1), (W @ t) / W.sum(axis=1)
    q = lambda v, m: [float(np.quantile(v, 0.05 / (2 * m))), float(np.quantile(v, 1 - 0.05 / (2 * m)))]  # noqa: E731
    assert got["H_interval"] == q(Hr, 1) and got["T_interval"] == q(Tr, 1) and got["rho_interval"] == q(Hr / Tr, 1) and got["rho_nonfinite_share"] == 0.0
    got3 = S.edit_statistics(h, t, rs, 12, m=3)
    assert got3["rho_interval"] == q(Hr / Tr, 3) and got3["H"] == got["H"]


# ----------------------------------------------------------------------------- the whole analysis on planted stores (the stand-in's run)

RUN, K, N_E, N_L, N_P, SUB = "simplestories", 2, 16, 12, 200, 64
U = 1.0 / 4096
SOURCES = ["dialogue"] * 6 + ["narration"] * 6
E_LAB_DOCS = np.array([0, 0, 1, 1, 2, 2, 3, 3, 4, 4, 5, 5])
# per panel: the group's per-row damage and the twins', in units of U, so that float32 storage and every difference are exact
PLANT = {"panel_ArXiv": (800, 200), "panel_Github": (800, 700), "panel_StackExchange": (40, 200), "panel_DM_Mathematics": (800, 200), "panel_FreeLaw": (800, 200)}
REF_DELTA, IMP, UNM = 64, 1024, 96


def h(s: str) -> str:
    return hashlib.sha256(s.encode()).hexdigest()


def _write(d: Path, cells: list[Cell], kl: dict[str, np.ndarray], n: int, *, sets: dict[str, dict] | None = None, set_hash: str = "planted", sub: int = SUB) -> None:
    d.mkdir(parents=True, exist_ok=True)
    sets = sets or {}
    n_sub = (n + sub - 1) // sub
    pd.DataFrame([{**asdict(c), "cell": c.name, "n_on": 0, "n_subbatches": n_sub, "source_sha256": sets.get(c.name, {}).get("s"), "matched_source_sha256": sets.get(c.name, {}).get("m"),
                   "n_below_label_total": 0} for c in cells]).to_parquet(d / "cells.parquet", index=False)
    pd.concat([pd.DataFrame({"cell": c.name, "seq": np.arange(n), "kl_mean": np.asarray(kl[c.name], dtype=np.float32)}) for c in cells], ignore_index=True).to_parquet(d / "per_sequence.parquet", index=False)
    (d / "marker.json").write_text(json.dumps({"done_through": n_sub - 1, "subbatch": sub, "n_sequences": n, "cells": [c.name for c in cells]}))
    draws = max([c.draw for c in cells] + [0]) + 1
    (d / "run_manifest.json").write_text(json.dumps({"run": RUN, "n_sequences": n, "n_draws": draws, "finished_at": "planted", "commits": {"project": "planted", "dirty": "0"}, "gpu_name": "planted",
                                                     "precision": "bf16", "set_hash": set_hash, "subbatch": sub}))


def _v(units, n: int) -> np.ndarray:
    return (np.broadcast_to(np.asarray(units, dtype=np.float64), (n,)) * U).astype(np.float32)


def _wobble(n: int) -> np.ndarray:
    return (np.arange(n) % 4) * 4  # a per-row wobble, so that no interval is a point


def _refs(eval_set: str, subset: str) -> list[Cell]:
    return _references(RUN, eval_set, 1, conditions=tier7.reference_conditions(subset), draws=K)


def _merge_value(eval_set: str, pool: str, ctl: str, k: int, rung: str) -> float:
    tokens = {"1": 1, "T2": 2, "T4": 4, "2": 8}[rung]
    return IMP + 10 * tokens + {"none": 3, "plain": 1, "marginal": 2}[ctl] * (k + 1) + {"D_code": 5, "D_unif": 0, "D_prose": 7}[pool]


def planted_world(tmp: Path, *, spoil: str | None = None) -> A.Spec:
    committed = tmp / "committed"
    n_of = {"E": N_E, "E_lab": N_L}
    # committed: E (references, the real merge and the uniform control at 1 and 8 tokens), the marginal control, E_lab's same-domain arms, and the code-leaning store
    ref_kl = lambda cells, n: {c.name: _v({"importances": IMP, "unmasked": UNM, "unmasked_delta": REF_DELTA}[c.condition] + _wobble(n), n) for c in cells}  # noqa: E731
    e_refs = _references(RUN, "E", 1, conditions=tier7.reference_conditions("merge_sizes"), draws=K)
    e_cells = [Cell(RUN, "union", "E", "D_unif", 0.1, "r0", "excluded", k, r, ctl, 1 if ctl == "none" else 2) for ctl in ("none", "plain") for k in range(K) for r in ("1", "2")]
    _write(committed / "dry_run" / "E", e_refs + e_cells, {**ref_kl(e_refs, N_E), **{c.name: _v(_merge_value("E", "D_unif", c.control, c.draw, c.rung) + _wobble(N_E), N_E) for c in e_cells}}, N_E,
           sets={c.name: {"s": h(c.name)} for c in e_cells})
    m_cells = [Cell(RUN, "union", "E", "D_unif", 0.1, "r0", "excluded", k, r, "marginal", 4) for k in range(K) for r in ("1", "2")]
    _write(committed / "dry_run_s7" / "tier4" / "E__marginal", e_refs[1:] + m_cells, {**ref_kl(e_refs[1:], N_E), **{c.name: _v(_merge_value("E", "D_unif", "marginal", c.draw, c.rung) + _wobble(N_E), N_E) for c in m_cells}},
           N_E, sets={c.name: {"s": h(c.name)} for c in m_cells})
    l_refs = _references(RUN, "E_lab", 1, conditions=tier7.reference_conditions("merge_sizes") + tier7.reference_conditions("panel_edit"), draws=K)
    l_cells = [Cell(RUN, "union", "E_lab", p, 0.1, "r0", "excluded", k, r, "none", 5) for p in ("D_code", "D_unif", "D_prose") for k in range(K) for r in ("1", "2")]
    _write(committed / "dry_run_s9" / "tier5" / "E_lab__same_domain", l_refs + l_cells, {**ref_kl(l_refs, N_L), **{c.name: _v(_merge_value("E_lab", c.donor_pool, "none", c.draw, c.rung) + _wobble(N_L), N_L) for c in l_cells}},
           N_L, sets={c.name: {"s": h(c.name)} for c in l_cells})
    size = 64
    cl = [Cell(RUN, "code_leaning_hard", "E_lab", "D_code", 0.1, "ones", "included", 0, f"G{s}", "none", 4) for s in (64, 94)]
    cl += [Cell(RUN, "code_leaning_hard", "E_lab", "D_code", 0.1, "ones", "included", k, f"G{s}", "usage", 4) for s in (64, 94) for k in range(K)]
    d_refs = [c for c in l_refs if c.condition == "unmasked_delta"]
    _write(committed / "dry_run_s7" / "tier4" / "E_lab__code_leaning", d_refs + cl, {**ref_kl(d_refs, N_L), **{c.name: _v(REF_DELTA + 300 + _wobble(N_L), N_L) for c in cl}}, N_L,
           sets={c.name: {"s": h(c.name)} for c in cl})
    # the tier-7 stores, as the launch writes them
    root = tmp / "tier7"
    want = A.expected_stores(RUN, K)
    table = []
    for name, cells in want.items():
        es = cells[0].eval_set
        n = N_P if es.startswith("panel_") else n_of[es]
        kl, sets = {}, {}
        for c in cells:
            if c.family == "reference":
                base = {"importances": IMP, "unmasked": UNM, "unmasked_delta": REF_DELTA}[c.condition]
                kl[c.name] = _v(base + _wobble(n), n)
            elif c.tier != 7:  # a canary: its committed value
                kl[c.name] = _v((REF_DELTA + 300 if c.family == "code_leaning_hard" else _merge_value(es, c.donor_pool, c.control, c.draw, c.rung)) + _wobble(n), n)
                sets[c.name] = {"s": h(c.name)}
            elif c.family == "union":
                kl[c.name] = _v(_merge_value(es, c.donor_pool, c.control, c.draw, c.rung) + _wobble(n), n)
                sets[c.name] = {"s": h(c.name), "m": h("m" + c.name) if c.control != "none" else None}
                table.append({"cell": c.name, "rung": c.rung, "source_sha256": h(c.name), "matched_source_sha256": h("m" + c.name) if c.control != "none" else None})
            else:  # a panel edit: the planted damage over the store's rung 0, the group and the twins
                g, tw = PLANT[es]
                units = (g if c.control == "none" else tw) * (1 if c.rung == f"G{size}" else 2)
                kl[c.name] = _v(REF_DELTA + units + _wobble(n) + (np.arange(n) % 7), n)
                sets[c.name] = {"s": h(tier7.committed_twin(c))}
        if spoil == "canary" and name == "E__merge_sizes":
            nm = tier7.merge_canary_cells(RUN)["E"][0].name
            kl[nm] = kl[nm].copy()
            kl[nm][3] = np.nextafter(kl[nm][3], np.float32(1))
        if spoil == "set" and name == "panel_ArXiv__panel_edit":
            c0 = next(c for c in cells if c.tier == 7)
            sets[c0.name] = {"s": h("another set")}
        if spoil == "missing" and name == "panel_Github__panel_edit":
            cells = cells[:-1]
        _write(root / name, cells, kl, n, sets=sets, sub=32 if (spoil == "subbatch" and name == "panel_FreeLaw__panel_edit") else SUB)
    for subset in ("merge_sizes", "panel_edit"):
        (root / f"summary__{subset}.json").write_text(json.dumps({"cells_failed": 0, "failures": [], "cells_run": 1, "groups": {"x": {"ok": True}}, "gpu": "planted", "tier_7": {"sets": {"asserted": True}}}))
    pd.DataFrame(table).to_csv(tmp / "merge_sets.csv", index=False)
    return A.Spec(run=RUN, store_root=root, out_dir=tmp / "out", committed_roots=(committed / "dry_run", committed / "dry_run_s7", committed / "dry_run_s9"), merge_table=tmp / "merge_sets.csv",
                  panels=tuple(PLANT), edit_sizes=(64, 94), panel_documents=tier7.stand_in_documents, e_lab_sources=SOURCES, e_lab_documents=E_LAB_DOCS,
                  code_sources=("dialogue",), prose_sources=("narration",))


def test_the_whole_analysis_on_planted_stores(tmp_path):
    spec = planted_world(tmp_path)
    s = A.analyze_s12(spec, replicates=300, log=lambda *_: None)
    r = s["readings"]
    # ArXiv: damage 800/4096 = 0.195 at 64 members against twins 0.049: keep. GitHub: rho near 1.14 with a wobble: soften or keep by its
    # interval; StackExchange: damage 40/4096 = 0.0098, below X: drop. FreeLaw: nine documents, no reading.
    assert s["arxiv_reading"]["word"] == S.KEEP and r["panel_StackExchange"]["word"] == S.DROP and r["panel_FreeLaw"]["word"] is None
    assert r["panel_DM_Mathematics"]["word"] == S.KEEP and s["candidates_meeting_keep"] == ["panel_DM_Mathematics"]
    t = pd.read_csv(spec.out_dir / "s12_panels.csv")
    arx = t[(t.panel == "panel_ArXiv") & (t["size"] == 64)].iloc[0]
    rows = np.arange(N_P)
    hh = (800 + (rows % 7)) * U
    tt = (200 + (rows % 7)) * U
    assert arx.H == pytest.approx(hh.mean(), rel=1e-6) and arx["T"] == pytest.approx(tt.mean(), rel=1e-6) and arx.rho_nonfinite_share == 0.0
    # the merge points: the planted rises over the own explanation, 10 per token plus the line's draw pattern
    m = pd.read_csv(spec.out_dir / "s12_merge_E.csv")
    real2 = m[(m.line == "real merge") & (m.tokens == 2)].iloc[0]
    assert real2.rise == pytest.approx((20 + 3 * 1.5) * U, rel=1e-6) and real2.interval_lo <= real2.rise <= real2.interval_hi
    d = pd.read_csv(spec.out_dir / "s12_merge_E_per_draw.csv")
    row = d[(d.tokens == 4) & (d.draw == 1)].iloc[0]
    assert row.real_minus_matched == pytest.approx((3 * 2 - 2 * 2) * U, rel=1e-6)
    lab = pd.read_csv(spec.out_dir / "s12_merge_E_lab.csv")
    assert set(lab.stratum) == {"code texts", "prose texts"} and len(lab) == 2 * 3 * 4
    assert (spec.out_dir / "report.md").is_file() and "ArXiv reads keep" in (spec.out_dir / "report.md").read_text()
    # two runs, the same bytes
    first = {p.name: p.read_bytes() for p in spec.out_dir.iterdir()}
    A.analyze_s12(spec, replicates=300, log=lambda *_: None)
    assert {p.name: p.read_bytes() for p in spec.out_dir.iterdir()} == first


@pytest.mark.parametrize("spoil,match", [("canary", "THE CANARY FAILS"), ("set", "is not its committed twin's"), ("missing", "not the launch's cells"), ("subbatch", "run at sub-batch 32")])
def test_the_analysis_refuses(tmp_path, spoil, match):
    from vpd_audit.tier5 import GateFailure

    spec = planted_world(tmp_path, spoil=spoil)
    with pytest.raises((AssertionError, GateFailure), match=match):
        A.analyze_s12(spec, replicates=50, log=lambda *_: None)


def test_the_stores_the_analysis_expects_are_the_launchs():
    from vpd_audit import cells as C

    for run, draws in (("main", 8), ("simplestories", 2)):
        want = A.expected_stores(run, draws)
        t7 = [c for c in tier_7_cells(run, draws)]
        held = [c for cs in want.values() for c in cs if c.tier == 7]
        assert sorted(c.name for c in held) == sorted(c.name for c in t7)
        assert len(want) == 3 + len(C.PANEL_EVAL_SETS[run])
        assert {c.condition for c in want[f"{C.PANEL_EVAL_SETS[run][0]}__panel_edit"] if c.family == "reference"} == {"unmasked_delta"}
        assert {c.condition for c in want["E__merge_sizes"] if c.family == "reference"} == {"importances", "unmasked"}


# ----------------------------------------------------------------------------- the paper's committed data, before any tier-7 store


def _paper_pt(spec: A.Spec) -> dict:
    return {"stats": {p: {n: {"H": 0.2 + i / 100, "T": 0.1, "rho": 2.0, "H_interval": [0.1, 0.3], "rho_interval": [1.5, 2.5], "n_documents": 150} for n in spec.edit_sizes} for i, p in enumerate(spec.panels)}}


def test_the_replication_holds_to_the_committed_by_source_damages():
    spec = A.paper_spec()
    from vpd_audit.tier5 import CommittedTables

    rows = A.replication(spec, CommittedTables(spec.committed_roots), _paper_pt(spec), 200, 0)
    by = pd.read_csv(spec.by_source_damage, float_precision="round_trip")
    assert len(rows) == 4 * 2 and all(r["E_lab_equal_to_committed"] for r in rows)
    arx_free = {(r["source"], r["size"]): r for r in rows}
    assert arx_free[("StackExchange", 256)]["E_lab_H"] == float(by[(by.rung == "G256") & (by.source == "StackExchange") & (by.set == "group")].iloc[0]["D"])
    assert arx_free[("Github", 256)]["E_lab_documents"] == 69 and arx_free[("Pile-CC", 1007)]["E_lab_documents"] == 25
    assert all(r["E_lab_H_interval_lo"] < r["E_lab_H"] < r["E_lab_H_interval_hi"] for r in rows)


def test_the_removed_label_orders_on_the_committed_table():
    spec = A.paper_spec()
    rl = A.removed_label(spec, _paper_pt(spec))
    om = pd.read_csv(spec.omega_table)
    assert len(rl["rows"]) == 5 * 2 and len(rl["pairs"]) == 2 * 2
    assert rl["orders"][256]["by_omega_group"] == ["panel_Github", "panel_StackExchange", "panel_ArXiv", "panel_Pile_CC", "panel_Wikipedia__en_"]
    r = next(x for x in rl["rows"] if x["panel"] == "panel_ArXiv" and x["size"] == 256)
    assert r["H_per_omega_group"] == pytest.approx(r["H"] / float(om[(om.panel == "panel_ArXiv") & (om["size"] == 256)].iloc[0].omega_group))
    assert {p["pair"] for p in rl["pairs"]} == {"StackExchange / ArXiv", "Pile-CC / Wikipedia"}
    assert A.removed_label(replace(spec, omega_table=None), _paper_pt(spec)) is None


def test_the_paper_spec_points_at_the_committed_inputs():
    spec = A.paper_spec()
    assert spec.run == "main" and spec.edit_sizes == (256, 1007) and len(spec.panels) == 8 and spec.store_root.as_posix().endswith("results/grid/main_s12/tier7")
    assert spec.panel_documents("panel_ArXiv").shape == (200,) and np.unique(spec.panel_documents("panel_ArXiv")).size == 162
    assert len(spec.e_lab_sources) == 512 and np.unique(spec.e_lab_documents).size == 174
    assert set(spec.panel_set_hashes) == set(spec.panels) and all(spec.panel_set_hashes.values())


def test_the_guard(monkeypatch):
    from vpd_audit import results

    g = A.freeze_guard(None, enforce=False)
    assert [r["module"] for r in g["frozen_modules"]] == [f"vpd_audit/{m}" for m in A.FROZEN_MODULES] and len(g["frozen_modules"]) == 9 and g["frozen_modules_pass"]
    assert [r["module"] for r in g["this_modules"]] == ["vpd_audit/analysis_s12.py", "vpd_audit/stats_s12.py"]
    monkeypatch.setattr(results, "code_commits", lambda: {"project": "x", "submodule": "y", "dirty": "1"})
    lines: list[str] = []
    with pytest.raises(AssertionError, match="dirty tree"):
        A.freeze_guard("HEAD", enforce=True, log=lines.append)
    assert len(lines) == 1 + 9 + 2  # every blob printed before the refusal
    monkeypatch.setattr(results, "code_commits", lambda: {"project": "x", "submodule": "y", "dirty": "0"})
    with pytest.raises(AssertionError, match="--freeze"):
        A.freeze_guard(None, enforce=True)
    head = A._git("rev-parse", "HEAD")
    real = A._blob
    monkeypatch.setattr(A, "_blob", lambda rev, m: "0" * 40 if (rev == "main" and m == "stats.py") else real(rev, m))
    with pytest.raises(AssertionError, match="not main's blob"):
        A.freeze_guard(head, enforce=True)
    monkeypatch.setattr(A, "_blob", lambda rev, m: "1" * 40 if m == "stats_s12.py" else ("0" * 40 if m == "analysis_s12.py" else real(rev, m)))
    monkeypatch.setattr(A, "_git", lambda *a: "0" * 40 if (a[0] == "hash-object" and a[1].endswith("analysis_s12.py")) else (real_git(*a)))
    with pytest.raises(AssertionError, match="not the freeze's blob"):
        A.freeze_guard(head, enforce=True)


real_git = A._git
