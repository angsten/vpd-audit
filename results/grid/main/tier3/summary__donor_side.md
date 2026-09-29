# Tier 3 of the grid, the donor_side subset on main: NVIDIA A100-SXM4-40GB, bf16, sub-batch 64, 8 draws

Wall clock 48 s; peak GPU memory 26.5 GB
Cells enumerated 48, run 48, failed 0; failed cell types: none

| tier | cells | E-equivalent passes | optional |
|---|---|---|---|
| tier_1 | 0 | 0 | 0 |
| tier_2 | 0 | 0 | 0 |
| tier_3 | 48 | 1.5 | 0 |

Adaptive rule (n_on alone, before any cell): {'D_code|tau0': {'insert_5a_6a': False, 'median_n_on_rung_6': 11996.5, 'n_on_rung_8': 28819.0, 'ratio': 0.4162705159790416, 'threshold': 0.9}, 'D_code|tau0.1': {'insert_5a_6a': True, 'median_n_on_rung_6': 8672.0, 'n_on_rung_8': 9624.0, 'ratio': 0.9010806317539485, 'threshold': 0.9}, 'D_code|tau0.5': {'insert_5a_6a': False, 'median_n_on_rung_6': 8272.0, 'n_on_rung_8': 9378.0, 'ratio': 0.8820644060567285, 'threshold': 0.9}, 'D_unif|tau0': {'insert_5a_6a': False, 'median_n_on_rung_6': 12384.0, 'n_on_rung_8': 33576.0, 'ratio': 0.3688348820586133, 'threshold': 0.9}, 'D_unif|tau0.1': {'insert_5a_6a': True, 'median_n_on_rung_6': 9086.5, 'n_on_rung_8': 9966.0, 'ratio': 0.91174994982942, 'threshold': 0.9}, 'D_unif|tau0.5': {'insert_5a_6a': False, 'median_n_on_rung_6': 8817.5, 'n_on_rung_8': 9926.0, 'ratio': 0.8883235946000403, 'threshold': 0.9}}; inserted {'D_code|tau0.1': ['5a', '6a'], 'D_unif|tau0.1': ['5a', '6a']}

| group | set | sequences | cells | ok | seconds | peak GB |
|---|---|---|---|---|---|---|
| donors_D_unif_k0_r4 | D_unif[237] | 1 | 3 | True | 1.2 | 4.5 |
| donors_D_unif_k0_r7 | D_unif[9,17,19,24,58,60,65,83,...] | 64 | 3 | True | 2.6 | 26.5 |
| donors_D_unif_k1_r4 | D_unif[771] | 1 | 3 | True | 0.4 | 4.5 |
| donors_D_unif_k1_r7 | D_unif[12,14,38,45,63,72,100,153,...] | 64 | 3 | True | 2.4 | 26.5 |
| donors_D_unif_k2_r4 | D_unif[72] | 1 | 3 | True | 0.4 | 4.5 |
| donors_D_unif_k2_r7 | D_unif[1,7,9,14,59,72,82,87,...] | 64 | 3 | True | 2.5 | 26.5 |
| donors_D_unif_k3_r4 | D_unif[677] | 1 | 3 | True | 0.4 | 4.5 |
| donors_D_unif_k3_r7 | D_unif[1,2,22,33,51,64,72,103,...] | 64 | 3 | True | 2.5 | 26.5 |
| donors_D_unif_k4_r4 | D_unif[148] | 1 | 3 | True | 0.5 | 4.5 |
| donors_D_unif_k4_r7 | D_unif[2,18,35,89,104,116,148,163,...] | 64 | 3 | True | 2.5 | 26.5 |
| donors_D_unif_k5_r4 | D_unif[267] | 1 | 3 | True | 0.5 | 4.5 |
| donors_D_unif_k5_r7 | D_unif[11,12,15,47,49,54,70,81,...] | 64 | 3 | True | 2.7 | 26.5 |
| donors_D_unif_k6_r4 | D_unif[822] | 1 | 3 | True | 0.4 | 4.5 |
| donors_D_unif_k6_r7 | D_unif[1,12,16,19,29,33,55,77,...] | 64 | 3 | True | 2.9 | 26.5 |
| donors_D_unif_k7_r4 | D_unif[81] | 1 | 3 | True | 0.4 | 4.5 |
| donors_D_unif_k7_r7 | D_unif[1,29,33,36,60,71,75,78,...] | 64 | 3 | True | 2.4 | 26.5 |

P1 (union chains, |rung 8 - rung 0| > 0.01): 0/0
P2 (reported): rung 8 against unmasked and importances: 
P3: permitted-family cells with entries below their label 0 of 32; hard-zero rung-8 counts positive: True -> pass (non-permitted cells below g, expected: 16)
P4 (digests equal iff sources equal, an equal-digest pair with different sources a defect only if its switched mass differs too; non-empty rungs distinct from rung 0, empty rungs equal to it): 0/0 chains; empty-source cells 0; equal-digest pairs excused by equal switched mass 0
P5 (positive controls, pass or fail per curve, values withheld until the analysis code is frozen): no curve applies
d_b two-path check: 0 hard-zero cells, 0 (cell, sequence, tau_q) checks with t* > 0; largest |column - recomputed| / bound 0.0000 (must be <= 1) -> pass
