# Tier 7 of the grid, the merge_sizes subset on main: NVIDIA A100-SXM4-40GB, bf16, sub-batch 64, 8 draws

Wall clock 660 s; peak GPU memory 26.5 GB
Cells enumerated 106, run 106, failed 0; failed cell types: none

| tier | cells | E-equivalent passes | optional |
|---|---|---|---|
| tier_1 | 0 | 0 | 0 |
| tier_2 | 0 | 0 | 0 |
| tier_3 | 0 | 0 | 0 |
| tier_7 | 96 | 72.0 | 0 |

Adaptive rule (n_on alone, before any cell): {'D_code|tau0': {'insert_5a_6a': False, 'median_n_on_rung_6': 11996.5, 'n_on_rung_8': 28819.0, 'ratio': 0.4162705159790416, 'threshold': 0.9}, 'D_code|tau0.1': {'insert_5a_6a': True, 'median_n_on_rung_6': 8672.0, 'n_on_rung_8': 9624.0, 'ratio': 0.9010806317539485, 'threshold': 0.9}, 'D_code|tau0.5': {'insert_5a_6a': False, 'median_n_on_rung_6': 8272.0, 'n_on_rung_8': 9378.0, 'ratio': 0.8820644060567285, 'threshold': 0.9}, 'D_unif|tau0': {'insert_5a_6a': False, 'median_n_on_rung_6': 12384.0, 'n_on_rung_8': 33576.0, 'ratio': 0.3688348820586133, 'threshold': 0.9}, 'D_unif|tau0.1': {'insert_5a_6a': True, 'median_n_on_rung_6': 9086.5, 'n_on_rung_8': 9966.0, 'ratio': 0.91174994982942, 'threshold': 0.9}, 'D_unif|tau0.5': {'insert_5a_6a': False, 'median_n_on_rung_6': 8817.5, 'n_on_rung_8': 9926.0, 'ratio': 0.8883235946000403, 'threshold': 0.9}}; inserted {'D_code|tau0.1': ['5a', '6a'], 'D_unif|tau0.1': ['5a', '6a']}

| group | set | sequences | cells | ok | seconds | peak GB |
|---|---|---|---|---|---|---|
| E__merge_sizes | E | 1024 | 53 | True | 414.9 | 26.5 |
| E_lab__merge_sizes | E_lab | 512 | 53 | True | 206.4 | 26.5 |

P1 (union chains, |rung 8 - rung 0| > 0.01): 0/0 (pass count only: a tier-5 launch prints no rise; the values are in the summary's JSON, read by the frozen analysis)
P3: permitted-family cells with entries below their label 0 of 106; hard-zero rung-8 counts positive: True -> pass (non-permitted cells below g, expected: 0)
P4 (digests equal iff sources equal, an equal-digest pair with different sources a defect only if its switched mass differs too; non-empty rungs distinct from rung 0, empty rungs equal to it): 6/6 chains; empty-source cells 0; equal-digest pairs excused by equal switched mass 0
P5 (positive controls, pass or fail per curve, values withheld until the analysis code is frozen): no curve applies
References added per store: E__merge_sizes: 2, E_lab__merge_sizes: 2
Tier 7, the merge_sizes subset: sets against the label-only table and their committed twins: asserted {'canaries': 6, 'merge_matched_sets': 32, 'merge_sets': 96, 'panel_edit_sets': 0}; canaries 6 (E, E_lab)
d_b two-path check: 0 hard-zero cells, 0 (cell, sequence, tau_q) checks with t* > 0; largest |column - recomputed| / bound 0.0000 (must be <= 1) -> pass
