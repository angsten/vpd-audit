"""The post's figures (figures_post.py): the interval canary at the committed levels on the paper's committed stores, the own
explanations computed with the E_lab assertion, the code edit's damages against the committed tables, the drawing functions on the
reference figures' own inputs, and the whole module on planted tier-7 stores (the 2- and 4-token points drawn filled like the rest, the
code edit's default variant and its two others on request, the CSVs beside the PNGs)."""

from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from vpd_audit import env
from vpd_audit import figures_post as F
from vpd_audit.cells import PANEL_EDIT_SIZES, TAU_PRIMARY, Cell, _references

RESULTS = env.PROJECT_ROOT / "results"
FIGS = RESULTS / "grid" / "analysis" / "main" / "s9" / "figures"
TABLES = RESULTS / "grid" / "analysis" / "main"


@pytest.fixture(scope="module")
def paper():
    return F.paper_inputs(with_tier7=False)


def test_the_interval_canary_reproduces_every_committed_interval_at_its_level(paper):
    out = F.interval_canary(paper)
    assert out["aggregation_curve"]["m_curve_1"] == 10 and out["aggregation_curve"]["m_curve_1_plain"] == 10  # what compared_rungs gives the committed chain
    assert len(out["aggregation_curve"]["checks"]) == 3 * 5 + 2 and {c.split()[-1] for c in out["aggregation_curve"]["checks"][:15]} == {"m1", "m2"}
    assert out["similar_donors"] == {"n_points": 2 * 3 * 6, "m": 10} and out["code_edit"]["n_bars"] == 10


def test_the_canary_catches_a_changed_level(paper, monkeypatch):
    real = F.aggregation_curve_numbers

    def one_level_off(inp, sd, cells, *, levels=None):
        if levels is not None:
            levels = {k: dict(v) for k, v in levels.items()}
            levels["marginal"]["2"] = 1
        return real(inp, sd, cells, levels=levels)

    monkeypatch.setattr(F, "aggregation_curve_numbers", one_level_off)
    with pytest.raises(AssertionError, match="M at rung 2"):
        F.interval_canary(paper)


def test_the_own_explanations_are_computed_and_held_to_the_committed_e_lab_value(paper):
    strata = F.e_lab_strata(paper)
    sd, _ = F.e_lab_data(paper)
    own = F.own_explanations(paper, sd, strata)
    assert round(own["code"], 4) == 0.2926 and round(own["prose"], 4) == 0.4286 and own["E_lab_bitwise"]
    assert strata["code"]["n_documents"] == 69 and strata["prose"]["n_documents"] == 58 and int(strata["code"]["mask"].sum()) == 256 and int(strata["prose"]["mask"].sum()) == 128
    assert F.own_explanation_e(paper) == 0.3417225123921525


def test_the_own_explanation_assertion_refuses_a_wrong_committed_value(paper, tmp_path):
    import shutil

    root = tmp_path / "results"
    (root / "grid" / "analysis" / "main" / "s9b").mkdir(parents=True)
    t = pd.read_csv(TABLES / "s9b" / "s9_run6_self_merge_rule.csv")
    t.loc[t.set == "E_lab", "own_labels_kl"] = 0.3339
    t.to_csv(root / "grid" / "analysis" / "main" / "s9b" / "s9_run6_self_merge_rule.csv", index=False)
    shutil.copytree(TABLES / "s9", root / "grid" / "analysis" / "main" / "s9")
    bad = F.Inputs("main", root, None)
    strata = F.e_lab_strata(bad)
    sd, _ = F.e_lab_data(paper)
    with pytest.raises(AssertionError, match="not the committed E_lab value"):
        F.own_explanations(bad, sd, strata)


def test_the_code_edit_on_e_lab_has_document_intervals_and_none_on_arxiv(paper):
    t = F.code_edit_lab_numbers(paper, F.e_lab_strata(paper)).set_index(["source", "size"])
    assert np.isnan(t.loc[("ArXiv", 256), "lo"]) and t.loc[("ArXiv", 256), "n_documents"] == 3
    for s in ("GitHub", "StackExchange", "Pile-CC", "Wikipedia (en)"):
        for n in (256, 1007):
            assert t.loc[(s, n), "lo"] < t.loc[(s, n), "damage"] < t.loc[(s, n), "hi"]
    assert t.loc[("GitHub", 256), "n_documents"] == 69 and t.loc[("GitHub", 256), "damage"] == 0.638953306876715


# ----------------------------------------------------------------------------- the drawing on the reference figures' own inputs


def legacy_aggregation_curve() -> tuple[list[F.Line], list[int], float]:
    """The reference top figure's inputs, as its script built them from the committed tables."""
    own = 0.3417225123921525
    tokens = [1, 8, 16, 32, 64]
    d = pd.read_csv(FIGS / "fig5_matched_random_sets.csv").set_index("tokens_merged").loc[tokens]
    f1 = pd.read_csv(FIGS / "fig1_merge_curve.csv")
    whole = {"real_explanations": f1[(f1.series == "real explanations") & (f1.tokens_merged == 512)].iloc[0],
             "random_same_size": f1[(f1.series == "random sets of the same size") & (f1.tokens_merged == 512)].iloc[0]}
    lines = []
    for col, (_, color, dark, marker, label) in zip(("real_explanations", "matched_random", "random_same_size"), F.MERGE_LINES):
        w = whole.get(col)
        lines.append(F.Line(color, dark, marker, label, d[col].to_numpy() + own, d[f"{col}_lo"].to_numpy() + own, d[f"{col}_hi"].to_numpy() + own,
                            None if w is None else (w.divergence, w.divergence - w.interval_half_width, w.divergence + w.interval_half_width)))
    return lines, tokens, own


def legacy_similar_donors() -> tuple[list[F.Panel], list[int]]:
    tokens = [1, 8, 16, 32, 64]
    d = pd.read_csv(FIGS / "fig7_within_one_kind.csv")
    d = d[d.series == "real explanations"]
    points = [f"{t} token" if t == 1 else f"{t} tokens" for t in tokens] + ["1 text"]
    panels = []
    for texts, ttl, b, tcol in (("the code texts", "Code Recipients", 0.2926, F.PURPLE), ("the prose texts", "Prose Recipients", 0.4286, F.GREEN)):
        lines = []
        for (name, color, dark, marker, label) in F.SIMILAR_LINES:
            s = d[(d.texts == texts) & (d.donors == name)].set_index("merged_in").loc[points]
            lines.append(F.Line(color, dark, marker, label, s.rise.to_numpy() + b, s.interval_lo.to_numpy() + b, s.interval_hi.to_numpy() + b))
        panels.append(F.Panel(ttl, tcol, b, lines))
    return panels, tokens


def legacy_code_edit() -> F.Bars:
    by_src = pd.read_csv(TABLES / "s7_code_leaning_damage_by_source.csv")
    overall = pd.read_csv(TABLES / "s7_code_leaning_damage.csv").set_index("rung")
    vals = {}
    for n in (256, 1007):
        rung = f"G{n}"
        row = []
        for s in F.CODE_EDIT_SOURCES:
            if s == "GitHub":
                row.append(float(overall.loc[rung, "D_github"]))
            else:
                r = by_src[(by_src.rung == rung) & (by_src.source == s)].set_index("set")
                row.append(float(r.loc["group", "D"]))
        vals[n] = row
    return F.Bars(vals)


# The reference figures, as they were drawn before the port; the aggregation schematic's as redrawn with its panel (d) titled
# "Aggregated setting" (the one change to its text since the port was proved pixel-identical).
REFERENCE = env.PROJECT_ROOT / "tests" / "data" / "post_figures"


def _pixels(path: Path) -> np.ndarray:
    from PIL import Image

    with Image.open(path) as im:
        return np.asarray(im.convert("RGBA"))


def _draw_reference(name: str, path: Path) -> Path:
    if name == "aggregation_schematic":
        return F.draw_aggregation_schematic(path)
    if name == "delete_schematic":
        return F.draw_delete_schematic(path)
    if name == "aggregation_curve":
        lines, tokens, own = legacy_aggregation_curve()
        return F.draw_aggregation_curve(lines, tokens, own, path)
    if name == "similar_donors":
        panels, tokens = legacy_similar_donors()
        return F.draw_similar_donors(panels, tokens, path)
    assert name == "code_edit", name
    return F.draw_code_edit(legacy_code_edit(), path)


@pytest.mark.parametrize("name", ["aggregation_schematic", "delete_schematic", "aggregation_curve", "similar_donors", "code_edit"])
def test_each_ported_figure_is_the_reference_one_pixel_for_pixel(name, tmp_path):
    """Drawn from the reference figure's own inputs (the committed tables it was drawn from, its token list and levels), the ported drawing
    function gives the reference image: the decoded pixel arrays are equal (not the files, whose metadata carries the library's version)."""
    got = _pixels(_draw_reference(name, tmp_path / f"{name}.png"))
    want = _pixels(REFERENCE / f"{name}.png")
    assert got.shape == want.shape, (name, got.shape, want.shape)
    diff = np.any(got != want, axis=-1)
    assert not diff.any(), f"{name}: {int(diff.sum())} pixels differ, in rows {np.flatnonzero(diff.any(axis=1))[[0, -1]].tolist()} and columns {np.flatnonzero(diff.any(axis=0))[[0, -1]].tolist()}"


# ----------------------------------------------------------------------------- the whole module on planted tier-7 stores

K = 8
U = 1.0 / 4096
PLANT_E = {"none": 30.0, "plain": -10.0, "marginal": -20.0}  # the planted rise per token at 2 and 4 tokens, in U
PLANT_PANEL = {"GitHub": 2000, "StackExchange": 1200, "ArXiv": 900, "Pile-CC": 100, "Wikipedia (en)": 120}


def _write(d: Path, cells: list[Cell], kl: dict[str, np.ndarray], n: int, run: str = "main") -> None:
    d.mkdir(parents=True, exist_ok=True)
    pd.DataFrame([{**asdict(c), "cell": c.name, "n_on": 0, "n_subbatches": 1, "source_sha256": None, "matched_source_sha256": None, "n_below_label_total": 0} for c in cells]).to_parquet(d / "cells.parquet", index=False)
    pd.concat([pd.DataFrame({"cell": c.name, "seq": np.arange(n), "kl_mean": np.asarray(kl[c.name], dtype=np.float32)}) for c in cells], ignore_index=True).to_parquet(d / "per_sequence.parquet", index=False)
    (d / "marker.json").write_text(json.dumps({"done_through": 0, "subbatch": n, "n_sequences": n, "cells": [c.name for c in cells]}))
    (d / "run_manifest.json").write_text(json.dumps({"run": run, "n_sequences": n, "n_draws": max([c.draw for c in cells]) + 1, "finished_at": "planted"}))


def _committed_imp(eval_set: str) -> np.ndarray:
    store = RESULTS / "grid" / "main" / "tier1" / eval_set
    r = pd.read_parquet(store / "per_sequence.parquet", columns=["cell", "seq", "kl_mean"])
    return r[r.cell == f"main/{eval_set}/ref/importances"].sort_values("seq")["kl_mean"].to_numpy(np.float32)


@pytest.fixture(scope="module")
def planted_tier7(tmp_path_factory):
    root = tmp_path_factory.mktemp("tier7")
    for eval_set, pools, ctls in (("E", ("D_unif",), ("none", "plain", "marginal")), ("E_lab", ("D_code", "D_unif", "D_prose"), ("none",))):
        imp = _committed_imp(eval_set)
        refs = [c for c in _references("main", eval_set, 1, draws=K) if c.condition == "importances"]
        cells, kl = list(refs), {refs[0].name: imp}
        for pool in pools:
            for ctl in ctls:
                for k in range(K):
                    for r, tok in (("T2", 2), ("T4", 4)):
                        c = Cell("main", "union", eval_set, pool, TAU_PRIMARY, "r0", "excluded", k, r, ctl, 7, descriptive=True)
                        cells.append(c)
                        per = PLANT_E[ctl] if eval_set == "E" else {"D_code": 50.0, "D_unif": 20.0, "D_prose": 10.0}[pool]
                        kl[c.name] = (imp.astype(np.float64) + per * tok * U).astype(np.float32)
        _write(root / f"{eval_set}__merge_sizes", cells, kl, imp.size)
    for source, panel in F.PANEL_OF_SOURCE.items():
        ref = next(c for c in _references("main", panel, 1, draws=K) if c.condition == "unmasked_delta")
        cells, kl = [ref], {ref.name: np.full(200, 64 * U, dtype=np.float32)}
        for n in PANEL_EDIT_SIZES["main"]:
            for ctl, draws in (("none", [0]), ("usage", range(K))):
                for k in draws:
                    c = Cell("main", "code_leaning_hard", panel, "D_code", TAU_PRIMARY, "ones", "included", k, f"G{n}", ctl, 7)
                    cells.append(c)
                    units = PLANT_PANEL[source] * (1 if n == 256 else 3) if ctl == "none" else 400
                    kl[c.name] = ((64 + units + (np.arange(200) % 5)) * U).astype(np.float32)
        _write(root / f"{panel}__panel_edit", cells, kl, 200)
    return root


def test_the_figures_on_planted_tier_7_stores(planted_tier7, tmp_path):
    inp = F.paper_inputs()
    inp.tier7_root, inp.replicates = planted_tier7, 400
    out = F.figures_post(inp, tmp_path, log=lambda *_: None)
    files = sorted(p.name for p in tmp_path.iterdir())
    assert files == ["aggregation_curve.csv", "aggregation_curve.png", "aggregation_schematic.png", "code_edit_panels.csv", "code_edit_panels.png",
                     "delete_schematic.png", "figures_manifest.json", "similar_donors.csv", "similar_donors.png"]  # by default the code edit's panels variant only
    assert json.loads((tmp_path / "figures_manifest.json").read_text())["files"] == [f for f in files if f != "figures_manifest.json"]  # listed before it is written
    (tmp_path / "variants").mkdir()
    F.code_edit_figures(inp, tmp_path / "variants", ("lab", "arxiv_panel"))
    assert sorted(p.name for p in (tmp_path / "variants").iterdir()) == ["code_edit.csv", "code_edit.png", "code_edit_arxiv_panel.csv", "code_edit_arxiv_panel.png"]
    mc = pd.read_csv(tmp_path / "aggregation_curve.csv")
    assert set(mc.marker) == {"filled"} and len(mc) == 3 * 7 + 2  # no open markers: every point filled, 2 and 4 tokens included
    real4 = mc[(mc.line == "Components Donor Tokens Need") & (mc.donor_tokens.astype(str) == "4")].iloc[0]
    assert real4.rise == pytest.approx(PLANT_E["none"] * 4 * U, abs=2e-7) and real4.lo <= real4.divergence <= real4.hi
    one = mc[(mc.line == "Components Donor Tokens Need") & (mc.donor_tokens.astype(str) == "1")].iloc[0]
    f7 = pd.read_csv(TABLES / "fig7_marginal_control.csv", float_precision="round_trip", dtype={"rung": str}).set_index("rung")
    assert one.rise == pytest.approx(float(f7.loc["1", "U"]), abs=1e-15)  # the committed point; its bar now at 95 percent
    sd = pd.read_csv(tmp_path / "similar_donors.csv")
    assert len(sd) == 2 * 3 * 8 and set(sd.marker) == {"filled"}  # no open markers
    code = sd[(sd.recipients == "Code Recipients") & (sd.donors == "Code Donors") & (sd.donor_tokens.astype(str) == "2")].iloc[0]
    assert code.rise == pytest.approx(50 * 2 * U, abs=2e-7) and round(code.own_explanation, 4) == 0.2926
    lab = pd.read_csv(tmp_path / "variants" / "code_edit.csv").set_index(["source", "size"])
    panels = pd.read_csv(tmp_path / "code_edit_panels.csv").set_index(["source", "size"])
    mixed = pd.read_csv(tmp_path / "variants" / "code_edit_arxiv_panel.csv").set_index(["source", "size"])
    assert np.isnan(lab.loc[("ArXiv", 256), "lo"]) and not np.isnan(panels.loc[("ArXiv", 256), "lo"])
    assert panels.loc[("ArXiv", 256), "damage"] == pytest.approx((900 + 2) * U, rel=1e-6) and panels.loc[("ArXiv", 256), "n_documents"] == 162
    assert mixed.loc[("ArXiv", 256), "set"] == "panel_ArXiv" and mixed.loc[("GitHub", 256), "set"] == "E_lab" and mixed.loc[("ArXiv", 1007), "damage"] == panels.loc[("ArXiv", 1007), "damage"]
    assert out["canary"]["similar_donors"]["m"] == 10


def test_the_variants_flag_and_the_refusal_without_tier_7(planted_tier7, tmp_path):
    inp = F.paper_inputs()
    inp.tier7_root, inp.replicates = planted_tier7, 200
    F.code_edit_figures(inp, tmp_path, ("lab",))
    assert sorted(p.name for p in tmp_path.iterdir()) == ["code_edit.csv", "code_edit.png"]
    with pytest.raises(AssertionError):
        F.code_edit_figures(inp, tmp_path, ("sideways",))
    with pytest.raises(AssertionError, match="tier-7 stores"):
        F.figures_post(F.paper_inputs(with_tier7=False), tmp_path, log=lambda *_: None)
