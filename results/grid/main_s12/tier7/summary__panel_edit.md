# Tier 7 of the grid, the panel_edit subset on main: NVIDIA A100-SXM4-40GB, bf16, sub-batch 64, 8 draws

Wall clock 339 s; peak GPU memory 26.5 GB
Cells enumerated 155, run 155, failed 0; failed cell types: none

| tier | cells | E-equivalent passes | optional |
|---|---|---|---|
| tier_1 | 0 | 0 | 0 |
| tier_2 | 0 | 0 | 0 |
| tier_3 | 0 | 0 | 0 |
| tier_7 | 144 | 28.1 | 0 |

Adaptive rule (n_on alone, before any cell): {'D_code|tau0': {'insert_5a_6a': False, 'median_n_on_rung_6': 11996.5, 'n_on_rung_8': 28819.0, 'ratio': 0.4162705159790416, 'threshold': 0.9}, 'D_code|tau0.1': {'insert_5a_6a': True, 'median_n_on_rung_6': 8672.0, 'n_on_rung_8': 9624.0, 'ratio': 0.9010806317539485, 'threshold': 0.9}, 'D_code|tau0.5': {'insert_5a_6a': False, 'median_n_on_rung_6': 8272.0, 'n_on_rung_8': 9378.0, 'ratio': 0.8820644060567285, 'threshold': 0.9}, 'D_unif|tau0': {'insert_5a_6a': False, 'median_n_on_rung_6': 12384.0, 'n_on_rung_8': 33576.0, 'ratio': 0.3688348820586133, 'threshold': 0.9}, 'D_unif|tau0.1': {'insert_5a_6a': True, 'median_n_on_rung_6': 9086.5, 'n_on_rung_8': 9966.0, 'ratio': 0.91174994982942, 'threshold': 0.9}, 'D_unif|tau0.5': {'insert_5a_6a': False, 'median_n_on_rung_6': 8817.5, 'n_on_rung_8': 9926.0, 'ratio': 0.8883235946000403, 'threshold': 0.9}}; inserted {'D_code|tau0.1': ['5a', '6a'], 'D_unif|tau0.1': ['5a', '6a']}

| group | set | sequences | cells | ok | seconds | peak GB |
|---|---|---|---|---|---|---|
| E_lab__panel_edit | E_lab | 512 | 3 | True | 24.3 | 26.5 |
| panel_ArXiv__panel_edit | panel_ArXiv | 200 | 19 | True | 35.5 | 26.5 |
| panel_DM_Mathematics__panel_edit | panel_DM_Mathematics | 200 | 19 | True | 35.2 | 26.5 |
| panel_FreeLaw__panel_edit | panel_FreeLaw | 200 | 19 | True | 36.3 | 26.5 |
| panel_Github__panel_edit | panel_Github | 200 | 19 | True | 36.6 | 26.5 |
| panel_Pile_CC__panel_edit | panel_Pile_CC | 200 | 19 | True | 39.0 | 26.5 |
| panel_PubMed_Central__panel_edit | panel_PubMed_Central | 200 | 19 | True | 35.5 | 26.5 |
| panel_StackExchange__panel_edit | panel_StackExchange | 200 | 19 | True | 35.3 | 26.5 |
| panel_Wikipedia__en___panel_edit | panel_Wikipedia__en_ | 200 | 19 | True | 35.4 | 26.5 |

P1 (union chains, |rung 8 - rung 0| > 0.01): 0/0 (pass count only: a tier-5 launch prints no rise; the values are in the summary's JSON, read by the frozen analysis)
P3: permitted-family cells with entries below their label 0 of 9; hard-zero rung-8 counts positive: True -> pass (non-permitted cells below g, expected: 146)
P4 (digests equal iff sources equal, an equal-digest pair with different sources a defect only if its switched mass differs too; non-empty rungs distinct from rung 0, empty rungs equal to it): 18/18 chains; empty-source cells 0; equal-digest pairs excused by equal switched mass 0
P5 (positive controls, pass or fail per curve, values withheld until the analysis code is frozen): judged in the analysis under the per-chain rule
References added per store: E_lab__panel_edit: 1, panel_ArXiv__panel_edit: 1, panel_DM_Mathematics__panel_edit: 1, panel_FreeLaw__panel_edit: 1, panel_Github__panel_edit: 1, panel_Pile_CC__panel_edit: 1, panel_PubMed_Central__panel_edit: 1, panel_StackExchange__panel_edit: 1, panel_Wikipedia__en___panel_edit: 1
Tier 7, the panel_edit subset: sets against the label-only table and their committed twins: asserted {'canaries': 2, 'merge_matched_sets': 0, 'merge_sets': 0, 'panel_edit_sets': 144}; canaries 2 (E_lab__panel_edit)
d_b two-path check: 146 hard-zero cells, 2196 (cell, sequence, tau_q) checks with t* > 0; largest |column - recomputed| / bound 0.7892 (must be <= 1) -> pass
