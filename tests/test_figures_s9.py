"""The figures read only committed tables, and every number in each figure's CSV equals the value in
its source table (a second, independent reading of the tables here, by the row and column each CSV row names); the PNGs are
at 2x; the guard against project words on a figure works; the parsers of the tables' strings round-trip."""

from __future__ import annotations

import math

import numpy as np
import pandas as pd
import pytest

from vpd_audit import figures_s9 as f9
from vpd_audit import stats as st
from vpd_audit.constants import SEQ_LEN
from vpd_audit.sources import RUNG_SCHEDULE

A = f9.ANALYSIS_DIR
S9 = f9.S9B_DIR
ACC = f9.ACCEPTANCE_DIR


def same(a: float, b: float) -> bool:
    if isinstance(a, float) and math.isnan(a):
        return isinstance(b, float) and math.isnan(b)
    return math.isclose(float(a), float(b), rel_tol=1e-12, abs_tol=1e-15)


def test_parse_top5_and_interval():
    s = "' left' 0.957; ' right' 0.035; ' Left' 0.001; ' top' 0.001; ' bottom' 0.000"
    assert f9.parse_top5(s) == [(" left", 0.957), (" right", 0.035), (" Left", 0.001), (" top", 0.001), (" bottom", 0.0)]
    assert f9.parse_top5("'\\n' 0.500; '\"' 0.200; \"it's\" 0.100; ' $\\\\' 0.050; 'x' 0.010")[:4] == [("\n", 0.5), ('"', 0.2), ("it's", 0.1), (" $\\", 0.05)]
    with pytest.raises(AssertionError):
        f9.parse_top5("' a' 0.5; ' b' 0.4")
    assert f9._interval("[+0.5762, +0.7016]") == (0.5762, 0.7016) and f9._interval("[-0.0030, +0.0003]") == (-0.003, 0.0003)
    # every top-5 cell of the committed examples table parses to five entries with probabilities in [0, 1], non-increasing
    ex = pd.read_csv(S9 / "s9_examples.csv")
    n = 0
    for col in [c for c in ex.columns if c.startswith("top5: ")]:
        for s in ex[col].dropna():
            ps = [p for _, p in f9.parse_top5(s)]
            assert all(0.0 <= p <= 1.0 for p in ps) and ps == sorted(ps, reverse=True), (col, s)
            n += 1
    assert n == 20 * 5 + 5 * 3  # the 20 merge rows hold the original, own labels, and three merges; the 5 never-named rows the original, the full model, and the removal


def test_check_words_refuses_project_words():
    plt = f9._plt()
    for text, ok in (("the line fixed in advance", True), ("x1.35 and 1,024 texts", True), ("rung 3", False), ("at rungs 2 and 3", False), ("tau 0.1", False), ("background r0", False), ("the line X", False), ("n_on per draw", False), ("StackExchange", True)):
        fig, ax = plt.subplots()
        ax.set_title(text)
        if ok:
            f9.check_words(fig)
        else:
            with pytest.raises(AssertionError):
                f9.check_words(fig)
        plt.close(fig)
    # the guard sees legends and tick labels too
    fig, ax = plt.subplots()
    ax.plot([0, 1], label="rung 1")
    ax.legend()
    with pytest.raises(AssertionError):
        f9.check_words(fig)
    plt.close(fig)


@pytest.fixture(scope="module")
def drawn(tmp_path_factory):
    out = tmp_path_factory.mktemp("figures_s9")
    return out, f9.draw_s9(out)


def _csv(drawn, key: str, **read_kw) -> pd.DataFrame:
    return pd.read_csv(drawn[0] / drawn[1][key]["csv"], **read_kw)


def test_pngs_at_2x(drawn):
    from PIL import Image

    out, made = drawn
    assert set(made) == {"fig1", "fig2", "fig4", "fig5", "fig6", "fig7", "fig8"}
    for key, m in made.items():
        w, h = m["size_inches"]
        with Image.open(out / m["png"]) as im:
            assert im.size == (round(w * f9.DPI), round(h * f9.DPI)), (key, im.size)
        assert m["dpi"] == 200 and (out / f"{key.replace('fig', 'fig')}").parent == out


def test_figure_1_equals_its_tables(drawn):
    df = _csv(drawn, "fig1", dtype={"source_row": str})
    assert len(df) == 14 and set(df["series"]) == {"real explanations", "random sets of the same size", "reference: the full model, nothing removed", "reference: the text's own explanation"}
    level = pd.read_csv(A / "level_cells.csv").set_index("cell")
    for _, r in df.iterrows():
        if r["source_table"] == "level_cells.csv":
            assert same(r["divergence"], level.loc[r["source_row"], "mean_kl"]) and r["donor"] == "none"
            continue
        src = pd.read_csv(A / r["source_table"], dtype={"rung": str}).set_index("rung").loc[r["source_row"]]
        assert same(r["divergence"], src["mean_kl"]) and same(r["rise_over_own_explanation"], src["excess"]) and same(r["interval_half_width"], src["half_width"])
        assert same(r["share_of_texts_over_the_line"], src["fraction_seq_above_X"]) and same(r["pieces_switched_on_mean"], src["n_on"])
        rung = r["source_row"].split(" ")[0]
        unit, count = RUNG_SCHEDULE[rung]
        assert (r["donor"], int(r["tokens_merged"])) == (("one whole text", SEQ_LEN) if unit == "sequence" else (f"{count} tokens", count))
        assert ("descriptive" in r["source_row"]) == (rung in ("2a", "2b"))
    real = df[df["series"] == "real explanations"].sort_values("tokens_merged")
    assert list(real["tokens_merged"]) == [1, 8, 16, 32, 64, SEQ_LEN]
    # the strip's own numbers, as a sanity check of what the table holds
    assert [round(100 * v) for v in real["share_of_texts_over_the_line"]] == [0, 25, 96, 100, 100, 100]


def test_figure_2_equals_its_tables(drawn):
    df = _csv(drawn, "fig2", dtype={"source_row": str})
    ratios = pd.read_csv(S9 / "s9_yardstick_ratios.csv").set_index("quantity")
    yard = pd.read_csv(S9 / "s9_yardstick.csv").set_index(["model", "set"])
    level = pd.read_csv(A / "level_cells.csv").set_index("cell")
    cond = pd.read_csv(ACC / "conditions_main_bf16.csv").set_index("condition")
    for _, r in df.iterrows():
        t, row, col, v = r["source_table"], r["source_row"], r["source_column"], float(r["value"])
        assert same(r["multiple_of_perplexity_e_to_the_k"], math.exp(v))
        if t == "the paper's table tab:vpd-pgd-ce":
            assert r["kind"] == f9.PAPER_KIND and same(v, f9.PAPER_ATTACK_KL[int(row)])
        elif t == "stats.py":
            assert r["kind"] == f9.REGISTERED_KIND and same(v, st.X_MATERIAL)
        else:
            assert r["kind"] == f9.MEASURED_KIND
            if t == "level_cells.csv":
                assert same(v, level.loc[row, col])
            elif t == "acceptance/conditions_main_bf16.csv":
                assert same(v, cond.loc[row, col])
            elif t == "s9_yardstick_ratios.csv":
                assert same(v, ratios.loc[row, col])
            else:
                assert t == "s9_yardstick.csv"
                model, s = row.split(", ")
                assert same(v, yard.loc[(model, s), col])
    assert df["kind"].value_counts().to_dict() == {f9.MEASURED_KIND: 10, f9.REGISTERED_KIND: 1, f9.PAPER_KIND: 4}
    assert set(df["source_table"]) == {"level_cells.csv", "stats.py", "acceptance/conditions_main_bf16.csv", "s9_yardstick_ratios.csv", "s9_yardstick.csv", "the paper's table tab:vpd-pgd-ce"}
    # the paper's four values as the paper's table prints them (tab:vpd-pgd-ce)
    assert f9.PAPER_ATTACK_KL == {20: 0.8280, 40: 1.3539, 80: 3.8381, 160: 25.2560}


def test_figure_4_equals_its_tables(drawn):
    df = _csv(drawn, "fig4")
    fig8 = pd.read_csv(A / "fig8_code_leaning.csv").set_index("rung")
    cond = pd.read_csv(A / "s7_code_leaning_conditional.csv")
    dmg = pd.read_csv(A / "s7_code_leaning_damage.csv").set_index("rung")
    by_src = pd.read_csv(A / "s7_code_leaning_damage_by_source.csv")
    t = df[df["panel"] == "trade-off"]
    assert list(t["source_row"]) == ["G16", "G64", "G256", "G1007"]
    for _, r in t.iterrows():
        s = fig8.loc[r["source_row"]]
        assert int(r["n_pieces"]) == int(s["n_members"]) and not bool(s["descriptive"])
        for a, b in (("damage_on_code", "D_github"), ("damage_on_code_lo", "D_github_low"), ("damage_on_code_hi", "D_github_high"), ("damage_on_other_text", "D_other"), ("damage_on_other_text_lo", "D_other_low"),
                     ("damage_on_other_text_hi", "D_other_high"), ("twins_damage_on_code", "D_github_control"), ("twins_damage_on_other_text", "D_other_control")):
            assert same(r[a], s[b]), (r["source_row"], a)
        c = cond[(cond["rung"] == r["source_row"]) & (cond["stratum"] == "other") & (cond["set"] == "group") & (cond["tau_q"].astype(str) == "0.1")]
        assert len(c) == 1 and same(r["guarantee_covers_share_of_other_text"], c["mean_clean_prefix_fraction"].iloc[0])
    assert [round(100 * v) for v in t["guarantee_covers_share_of_other_text"]] == [73, 39, 5, 0]  # 73, 39, under 5, and 0 percent
    b = df[df["panel"] == "by source"]
    assert list(b["source"]) == ["code (GitHub)", "StackExchange", "ArXiv", "web text (Pile-CC)", "Wikipedia"] and b["source_row"].str.startswith("G256").all() and (b["n_pieces"] == 256).all()
    words_to_source = {v: k for k, v in f9.SOURCE_WORDS.items()}
    for _, r in b.iterrows():
        source = words_to_source[r["source"]]
        if source == "Github":
            assert r["source_table"] == "s7_code_leaning_damage.csv" and r["source_row"] == "G256"
            s = dmg.loc["G256"]
            lo, hi = f9._interval(s["D_github_interval"])
            assert same(r["damage"], s["D_github"]) and same(r["damage_lo"], lo) and same(r["damage_hi"], hi) and same(r["twins_damage"], s["D_github_control"])
            assert math.isnan(r["twins_damage_lo"]) and math.isnan(r["twins_damage_hi"])
            continue
        assert r["source_table"] == "s7_code_leaning_damage_by_source.csv" and r["source_row"] == f"G256 | {source}"
        g = by_src[(by_src["rung"] == "G256") & (by_src["source"] == source) & (by_src["set"] == "group")].iloc[0]
        c = by_src[(by_src["rung"] == "G256") & (by_src["source"] == source) & (by_src["set"] == "control")].iloc[0]
        assert same(r["damage"], g["D"]) and (r["damage_lo"], r["damage_hi"]) == f9._interval(g["interval_95"])
        assert same(r["twins_damage"], c["D"]) and (r["twins_damage_lo"], r["twins_damage_hi"]) == f9._interval(c["interval_95"])
    assert [round(v, 2) for v in b["damage"]] == [0.64, 0.33, 0.25, 0.02, 0.03]  # code, StackExchange, ArXiv, web text, Wikipedia
    assert [round(v, 2) for v in b["twins_damage"].iloc[3:]] == [0.18, 0.18]  # the twins on the two prose sources


def test_figure_5_equals_its_table(drawn):
    df = _csv(drawn, "fig5", dtype={"source_row": str})
    src = pd.read_csv(A / "fig7_marginal_control.csv", dtype={"rung": str})
    assert list(df["source_row"]) == list(src["rung"]) == ["1", "2", "2a", "2b", "3"] and list(df["tokens_merged"]) == list(src["donor_positions"]) == [1, 8, 16, 32, 64]
    for col, plain in (("U", "real_explanations"), ("P", "random_same_size"), ("M", "matched_random"), ("M_replicate_1", "matched_random_second_draw")):
        for a, b in ((col, plain), (col + "_low", plain + "_lo"), (col + "_high", plain + "_hi")):
            assert all(same(x, y) for x, y in zip(df[b], src[a])), (a, b)
    assert all(same(x, y) for x, y in zip(df["pieces_switched_on_mean"], src["n_on"]))


def test_figure_6_equals_its_table(drawn):
    df = _csv(drawn, "fig6")
    ex = pd.read_csv(S9 / "s9_examples.csv")
    shown = ex[ex["shown"]].reset_index(drop=True)
    assert len(df) == 5 * 3 * 5 and sorted(df["example"].unique()) == [1, 2, 3, 4, 5]
    for _, r in df.iterrows():
        s = shown.iloc[int(r["example"]) - 1]
        assert s["example_of"] == r["example_of"] and same(s["percentile"], r["percentile"]) and int(s["seq"]) == int(r["text"]) and int(s["position"]) == int(r["position"])
        assert same(r["divergence_at_position"], s["kl_at_position"]) and r["real_next_token"] == s["real_next_token"]
        tok, p = f9.parse_top5(s[r["source_column"]])[int(r["rank"]) - 1]
        assert r["token"] == tok and same(r["probability"], p), (r["example"], r["model"], r["rank"])
    assert set(df[df["example_of"] == "merge"]["source_column"]) == {"top5: the original model", "top5: own labels", "top5: the merge of general donors, 1 text"}
    assert set(df[df["example_of"] == "never_named"]["source_column"]) == {"top5: the original model", "top5: the full decomposed model with the residual", "top5: the removal of the never-named pieces"}
    # the examples' mask is curve 1 at one whole text, draw 0, fixed in advance
    assert (ex[ex["example_of"] == "merge"]["mask"] == "main/E/union/D_unif/tau0.1/r0/excl/k0/r4").all()


def test_figure_7_equals_its_tables(drawn):
    df = _csv(drawn, "fig7", dtype={"source_row": str})
    curves = pd.read_csv(S9 / "s9_run2_curves.csv", dtype={"size": str})
    controls = pd.read_csv(S9 / "s9_run2_controls.csv", dtype={"size": str})
    assert set(df["stratum"]) == {"G", "P"} and set(df["arm"]) == {"C", "U", "P"}
    real, rnd = df[df["series"] == "real explanations"], df[df["series"] == "random sets of the same size"]
    assert len(real) == 2 * 3 * 10 and len(rnd) == 2 * 2 * 6 and set(rnd["arm"]) == {"C", "U"}
    for _, r in real.iterrows():
        s = curves[(curves["stratum"] == r["stratum"]) & (curves["arm"] == r["arm"]) & (curves["size"] == r["source_row"])]
        assert len(s) == 1
        s = s.iloc[0]
        assert same(r["rise"], s["rise"]) and same(r["interval_lo"], s["interval_documents_lo"]) and same(r["interval_hi"], s["interval_documents_hi"]) and same(r["pieces_switched_on_mean"], s["n_on_mean"])
        assert (int(r["n_texts"]), int(r["n_documents"]), int(r["n_draws"])) == (int(s["n_texts"]), int(s["n_documents"]), int(s["n_draws"])) and r["merged_in"] == s["size_words"]
        assert bool(r["detected"]) == bool(s["detected"]) and bool(r["material"]) == bool(s["material"]) and pd.isna(s["flag"])
    for _, r in rnd.iterrows():
        c = controls[(controls["stratum"] == r["stratum"]) & (controls["arm"] == r["arm"]) & (controls["size"] == r["source_row"])]
        assert len(c) == 1
        c = c.iloc[0]
        assert same(r["rise"], c["random"]) and same(r["pieces_switched_on_mean"], c["n_on_random"]) and int(r["n_draws"]) == int(c["n_draws"]) and r["merged_in"] == c["size_words"]
        assert math.isnan(r["interval_lo"]) and math.isnan(r["interval_hi"])
    g = real[(real["stratum"] == "G")]
    assert (g["n_texts"] == 256).all() and (g["n_documents"] == 69).all() and (real[real["stratum"] == "P"]["n_texts"] == 128).all()


def test_figure_8_equals_its_tables(drawn):
    df = _csv(drawn, "fig8")
    ladder = pd.read_csv(S9 / "s9_run6_ladder.csv")
    rule = pd.read_csv(S9 / "s9_run6_self_merge_rule.csv").set_index("set")
    assert len(df) == 4 and list(df["group"]) == ["the code texts"] * 3 + ["all texts"]
    for _, r in df[df["group"] == "the code texts"].iterrows():
        stratum, rung = r["source_row"].split(" | ")
        s = ladder[(ladder["stratum"] == stratum) & (ladder["rung"] == rung)]
        assert stratum == "source:Github" and len(s) == 1
        s = s.iloc[0]
        assert same(r["rise"], s["mean_rise"]) and same(r["interval_lo"], s["interval_lo"]) and same(r["interval_hi"], s["interval_hi"]) and same(r["pieces_switched_on_mean"], s["mean_count"])
        assert int(r["n_texts"]) == int(s["n_texts"]) and int(r["n_documents"]) == int(s["n_documents"]) and r["standing"] == s["standing"] == "material"
    e, r = rule.loc["E"], df.iloc[3]
    assert same(r["rise"], e["rise"]) and same(r["interval_lo"], e["interval_lo"]) and same(r["interval_hi"], e["interval_hi"]) and int(r["n_texts"]) == int(e["n_texts"]) == 1024
    assert same(r["own_explanation_divergence"], e["own_labels_kl"]) and same(r["total_divergence"], e["self_merge_kl"]) and same(r["pieces_switched_on_mean"], e["n_on_mean"]) and bool(e["material"])
    assert [round(v, 2) for v in df["rise"]] == [0.57, 1.03, 1.40, 1.03] and round(float(r["total_divergence"]), 2) == 1.37


def test_every_csv_row_names_its_source(drawn):
    for key, m in drawn[1].items():
        df = pd.read_csv(drawn[0] / m["csv"])
        assert "source_table" in df.columns and df["source_table"].notna().all(), key
        assert ("source_row" in df.columns and df["source_row"].notna().all()) or ("source_column" in df.columns and df["source_column"].notna().all()), key
        assert not any(f9.BANNED_WORDS.search(c) for c in df.columns), (key, list(df.columns))
