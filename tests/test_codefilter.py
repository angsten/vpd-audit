"""The code filter on hand-made text, the rule on the registered worked examples, Wilson, the threshold choice and its
tie-breaks on a separable sample, Rogan-Gladen and the two purities on the registered worked numbers."""

import numpy as np
import pytest

from vpd_audit.codefilter import GRID_A, GRID_B, choose_thresholds, choose_with_edge_rule, classify, features, ppv, prose_purity, rogan_gladen, wilson


def test_features_on_hand_made_text():
    code = "def f(x):\n    return {x: [1, 2]};\n\tif (a <= b) { y = 3; }\n"
    f_p, f_i = features(code)
    n_nw = sum(1 for c in code if not c.isspace())
    assert f_p == pytest.approx(sum(1 for c in code if c in "{};=()[]<>") / n_nw)
    assert f_i == pytest.approx(2 / 3)  # three non-empty lines, two indented (four spaces; a tab)
    prose = "The quick brown fox.\n\n Jumps over the lazy dog.\r\n"
    f_p, f_i = features(prose)
    assert f_p == 0.0 and f_i == 0.0  # a single leading space is not indentation; the empty line does not count; the trailing CR is stripped
    assert features("") == (0.0, 0.0) and features("\n\n  \n") == (0.0, 0.0)
    # a form feed is not a line separator; a non-breaking space at a line start is not indentation
    assert features("a\x0cb\n  c")[1] == 0.0
    assert features("  x\n  y")[1] == 1.0


def test_rule_on_the_worked_examples():
    a, b = 0.03, 0.30
    assert classify(0.062, 0.71, a, b) == "code"  # a Python module
    assert classify(0.006, 0.00, a, b) == "prose"  # a Wikipedia article
    assert classify(0.048, 0.04, a, b) == "unassigned"  # LaTeX source
    assert classify(0.004, 0.90, a, b) == "unassigned"  # an indented poem
    assert classify(a, b, a, b) == "code"  # the thresholds themselves are code-like (>=)


def test_wilson():
    w = wilson(80, 100)
    assert w["p"] == 0.8 and 0.70 < w["lo"] < 0.72 and 0.86 < w["hi"] < 0.88
    assert wilson(0, 10)["lo"] == 0.0 and wilson(10, 10)["hi"] == pytest.approx(1.0)


def test_choose_thresholds_and_tie_breaks():
    rng = np.random.default_rng(0)
    gh = (rng.uniform(0.05, 0.12, 400), rng.uniform(0.5, 0.9, 400))  # code-like
    ot = (rng.uniform(0.0, 0.02, 400), rng.uniform(0.0, 0.2, 400))  # prose-like
    res = choose_thresholds(gh, ot, GRID_A, GRID_B)
    assert res["J_fit"] == pytest.approx(1.0) and res["TPR_fit"] == 1.0 and res["FPR_fit"] == 0.0
    # every pair with a in [0.025, 0.05] and b in [0.25, 0.5] separates perfectly: the tie-break takes the largest a, then the largest b
    assert res["a"] == 0.05 and res["b"] == 0.5 and not res["on_boundary"]
    res2, history = choose_with_edge_rule(gh, ot)
    assert res2["a"] == 0.05 and len(history) == 1
    # a sample whose best pair sits at the grid's top edge widens the grid
    gh_hi = (rng.uniform(0.2, 0.4, 300), rng.uniform(0.5, 0.9, 300))
    ot_hi = (rng.uniform(0.0, 0.16, 300), rng.uniform(0.0, 0.2, 300))
    res3, history3 = choose_with_edge_rule(gh_hi, ot_hi)
    assert len(history3) >= 2 and history3[0]["on_boundary"] and res3["a"] > 0.15 and not res3["on_boundary"]
    # a sample separated by indentation alone drives a to the natural edge at 0, which is recorded, not frozen
    gh_ind = (rng.uniform(0.0, 0.01, 300), rng.uniform(0.5, 0.9, 300))
    ot_ind = (rng.uniform(0.0, 0.01, 300), rng.uniform(0.0, 0.2, 300))
    res4, history4 = choose_with_edge_rule(gh_ind, ot_ind)
    assert res4["on_boundary"] and res4["a"] == 0.0 and res4["natural_edge"] and len(history4) >= 3


def test_rogan_gladen_and_the_purities_on_the_worked_example():
    assert rogan_gladen(0.115, 0.80, 0.04) == pytest.approx(0.075 / 0.76)
    assert rogan_gladen(0.01, 0.80, 0.04) == 0.0 and rogan_gladen(0.9, 0.80, 0.04) == 1.0  # clipped
    pi = 0.099
    assert ppv(pi, 0.80, 0.04) == pytest.approx(0.69, abs=0.01)
    assert prose_purity(pi, 0.90, 0.10) == pytest.approx(0.99, abs=0.005)
