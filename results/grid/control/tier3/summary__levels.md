# Tier 3 of the grid, the levels subset on control: NVIDIA A100-SXM4-40GB, bf16, sub-batch 64, 8 draws

Wall clock 271 s; peak GPU memory 26.5 GB
Cells enumerated 31, run 31, failed 0; failed cell types: none

| tier | cells | E-equivalent passes | optional |
|---|---|---|---|
| tier_1 | 0 | 0 | 0 |
| tier_2 | 0 | 0 | 0 |
| tier_3 | 6 | 6.0 | 0 |

Adaptive rule (n_on alone, before any cell): {'D_code|tau0': {'insert_5a_6a': False, 'median_n_on_rung_6': 9307.5, 'n_on_rung_8': 28178.0, 'ratio': 0.33031088082901555, 'threshold': 0.9}, 'D_code|tau0.1': {'insert_5a_6a': False, 'median_n_on_rung_6': 5066.0, 'n_on_rung_8': 5864.0, 'ratio': 0.8639154160982264, 'threshold': 0.9}, 'D_code|tau0.5': {'insert_5a_6a': False, 'median_n_on_rung_6': 4614.0, 'n_on_rung_8': 5612.0, 'ratio': 0.8221667854597291, 'threshold': 0.9}, 'D_unif|tau0': {'insert_5a_6a': False, 'median_n_on_rung_6': 9436.5, 'n_on_rung_8': 32456.0, 'ratio': 0.2907474735025881, 'threshold': 0.9}, 'D_unif|tau0.1': {'insert_5a_6a': False, 'median_n_on_rung_6': 5498.5, 'n_on_rung_8': 6361.0, 'ratio': 0.8644081119320861, 'threshold': 0.9}, 'D_unif|tau0.5': {'insert_5a_6a': False, 'median_n_on_rung_6': 5227.0, 'n_on_rung_8': 6325.0, 'ratio': 0.8264031620553359, 'threshold': 0.9}}; inserted none

| group | set | sequences | cells | ok | seconds | peak GB |
|---|---|---|---|---|---|---|
| E__levels | E | 1024 | 31 | True | 257.3 | 26.5 |

P1 (union chains, |rung 8 - rung 0| > 0.01): 0/0
P2 (reported): rung 8 against unmasked and importances: 
P3: permitted-family cells with entries below their label 0 of 26; hard-zero rung-8 counts positive: True -> pass (non-permitted cells below g, expected: 4)
P4 (digests equal iff sources equal, an equal-digest pair with different sources a defect only if its switched mass differs too; non-empty rungs distinct from rung 0, empty rungs equal to it): 2/2 chains; empty-source cells 0; equal-digest pairs excused by equal switched mass 0
P5 (positive controls, pass or fail per curve, values withheld until the analysis code is frozen): no curve applies
References added per store: E__levels: 25
d_b two-path check: 0 hard-zero cells, 0 (cell, sequence, tau_q) checks with t* > 0; largest |column - recomputed| / bound 0.0000 (must be <= 1) -> pass
