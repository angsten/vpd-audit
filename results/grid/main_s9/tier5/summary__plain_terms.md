# Tier 5 of the grid, the plain_terms subset on main: NVIDIA A100-SXM4-40GB, bf16, sub-batch 64, 8 draws

Wall clock 1371 s; peak GPU memory 36.3 GB
Cells enumerated 131, run 131, failed 0; failed cell types: none

| tier | cells | E-equivalent passes | optional |
|---|---|---|---|
| tier_1 | 41 | 41.0 | 0 |
| tier_2 | 16 | 16.0 | 0 |
| tier_3 | 17 | 17.0 | 0 |
| tier_4 | 3 | 1.5 | 0 |
| tier_5 | 4 | 3.0 | 0 |

Adaptive rule (n_on alone, before any cell): {'D_code|tau0': {'insert_5a_6a': False, 'median_n_on_rung_6': 11996.5, 'n_on_rung_8': 28819.0, 'ratio': 0.4162705159790416, 'threshold': 0.9}, 'D_code|tau0.1': {'insert_5a_6a': True, 'median_n_on_rung_6': 8672.0, 'n_on_rung_8': 9624.0, 'ratio': 0.9010806317539485, 'threshold': 0.9}, 'D_code|tau0.5': {'insert_5a_6a': False, 'median_n_on_rung_6': 8272.0, 'n_on_rung_8': 9378.0, 'ratio': 0.8820644060567285, 'threshold': 0.9}, 'D_unif|tau0': {'insert_5a_6a': False, 'median_n_on_rung_6': 12384.0, 'n_on_rung_8': 33576.0, 'ratio': 0.3688348820586133, 'threshold': 0.9}, 'D_unif|tau0.1': {'insert_5a_6a': True, 'median_n_on_rung_6': 9086.5, 'n_on_rung_8': 9966.0, 'ratio': 0.91174994982942, 'threshold': 0.9}, 'D_unif|tau0.5': {'insert_5a_6a': False, 'median_n_on_rung_6': 8817.5, 'n_on_rung_8': 9926.0, 'ratio': 0.8883235946000403, 'threshold': 0.9}}; inserted {'D_code|tau0.1': ['5a', '6a'], 'D_unif|tau0.1': ['5a', '6a']}

| group | set | sequences | cells | ok | seconds | peak GB |
|---|---|---|---|---|---|---|
| E__plain_terms | E | 1024 | 101 | True | 1057.2 | 36.3 |
| E_lab__plain_terms | E_lab | 512 | 30 | True | 211.5 | 36.3 |

P1 (union chains, |rung 8 - rung 0| > 0.01): 1/1 (pass count only: a tier-5 launch prints no rise; the values are in the summary's JSON, read by the frozen analysis)
P3: permitted-family cells with entries below their label 0 of 113; hard-zero rung-8 counts positive: True -> pass (non-permitted cells below g, expected: 12)
P4 (digests equal iff sources equal, an equal-digest pair with different sources a defect only if its switched mass differs too; non-empty rungs distinct from rung 0, empty rungs equal to it): 5/5 chains; empty-source cells 0; equal-digest pairs excused by equal switched mass 0
P5 (positive controls, pass or fail per curve, values withheld until the analysis code is frozen): judged in the analysis under the per-chain rule
References added per store: E__plain_terms: 25, E_lab__plain_terms: 25
Tier 5, the plain_terms subset: named sets against the label-only tables: asserted {'arm_U_against_curve_1': 0, 'control_matched_sets': 16, 'per_text_cells': 0, 'per_text_rows': 0, 'union_sets': 57}; example positions: equal to the committed list; re-run cells added: {'E__plain_terms': 74, 'E_lab__plain_terms': 3}
Comparison models' pre-flight gates: pass (pythia-160m at b56d9bee3630, pythia-70m at de3e4e2d6cbb)
- E__plain_terms: canary pass: 99 cells bitwise equal to the committed stores over 101376 (cell, text) pairs
- E_lab__plain_terms: canary pass: 28 cells bitwise equal to the committed stores over 14336 (cell, text) pairs
d_b two-path check: 4 hard-zero cells, 2717 (cell, sequence, tau_q) checks with t* > 0; largest |column - recomputed| / bound 0.8044 (must be <= 1) -> pass
