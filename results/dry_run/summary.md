# The dry run of the grid on simplestories: NVIDIA A100-SXM4-40GB, bf16, sub-batch 64, 2 draws

Wall clock 142 s; peak GPU memory 4.6 GB
Cells enumerated 1097, run 1097, failed 0; failed cell types: none

| tier | cells | E-equivalent passes | optional |
|---|---|---|---|
| tier_1 | 183 | 146.5 | 0 |
| tier_2 | 179 | 138.0 | 0 |
| tier_3 | 735 | 603.4 | 19 |

Adaptive rule (n_on alone, before any cell): {'D_code|tau0': {'insert_5a_6a': True, 'median_n_on_rung_6': 6552.5, 'n_on_rung_8': 6771.0, 'ratio': 0.9677300251070743, 'threshold': 0.9}, 'D_code|tau0.1': {'insert_5a_6a': True, 'median_n_on_rung_6': 4520.5, 'n_on_rung_8': 4996.0, 'ratio': 0.9048238590872698, 'threshold': 0.9}, 'D_code|tau0.5': {'insert_5a_6a': True, 'median_n_on_rung_6': 3153.0, 'n_on_rung_8': 3168.0, 'ratio': 0.9952651515151515, 'threshold': 0.9}, 'D_unif|tau0': {'insert_5a_6a': True, 'median_n_on_rung_6': 6548.5, 'n_on_rung_8': 6772.0, 'ratio': 0.9669964559952746, 'threshold': 0.9}, 'D_unif|tau0.1': {'insert_5a_6a': True, 'median_n_on_rung_6': 4495.0, 'n_on_rung_8': 4993.0, 'ratio': 0.9002603645103144, 'threshold': 0.9}, 'D_unif|tau0.5': {'insert_5a_6a': True, 'median_n_on_rung_6': 3151.0, 'n_on_rung_8': 3166.0, 'ratio': 0.9952621604548326, 'threshold': 0.9}}; inserted {'D_code|tau0': ['5a', '6a'], 'D_code|tau0.1': ['5a', '6a'], 'D_code|tau0.5': ['5a', '6a'], 'D_unif|tau0': ['5a', '6a'], 'D_unif|tau0.1': ['5a', '6a'], 'D_unif|tau0.5': ['5a', '6a']}

| group | set | sequences | cells | ok | seconds | peak GB |
|---|---|---|---|---|---|---|
| E | E_dry | 64 | 690 | True | 67.1 | 4.6 |
| E_lab | E_lab_dry | 64 | 395 | True | 38.4 | 3.7 |
| donors_D_unif_k0_r4 | D_unif_dry[94] | 1 | 3 | True | 0.3 | 0.2 |
| donors_D_unif_k0_r7 | D_unif_dry[1,3,7,9,13,14,16,17,...] | 64 | 3 | True | 0.6 | 3.7 |
| donors_D_unif_k1_r4 | D_unif_dry[83] | 1 | 3 | True | 0.2 | 0.2 |
| donors_D_unif_k1_r7 | D_unif_dry[0,4,11,12,13,14,15,16,...] | 64 | 3 | True | 0.8 | 3.7 |

P1 (union chains, |rung 8 - rung 0| > 0.01): 9/9
- simplestories/E/union/D_unif/tau0.1/r0/excl: rung 0 7.2443, rung 8 0.3075, difference -6.9368 -> pass
- simplestories/E/union/D_unif/tau0.1/uniform/excl/k0: rung 0 2.5901, rung 8 0.1156, difference -2.4745 -> pass
- simplestories/E/union/D_unif/tau0.1/uniform/excl/k1: rung 0 2.5866, rung 8 0.1155, difference -2.4711 -> pass
- simplestories/E/union/D_unif/tau0.5/r0/excl: rung 0 7.2443, rung 8 0.5796, difference -6.6647 -> pass
- simplestories/E/union/D_unif/tau0.5/uniform/excl/k0: rung 0 2.5901, rung 8 0.2446, difference -2.3455 -> pass
- simplestories/E/union/D_unif/tau0.5/uniform/excl/k1: rung 0 2.5866, rung 8 0.2449, difference -2.3416 -> pass
- simplestories/E/union/D_unif/tau0.1/uniform/incl/k0: rung 0 2.5837, rung 8 0.1144, difference -2.4693 -> pass
- simplestories/E/union/D_unif/tau0.1/uniform/incl/k1: rung 0 2.5798, rung 8 0.1143, difference -2.4655 -> pass
- simplestories/E/union/D_unif/tau0/r0/excl: rung 0 7.2443, rung 8 0.0381, difference -7.2062 -> pass
P2 (reported): rung 8 against unmasked and importances: union/D_unif/tau0.1/r0/excl/k0/r8: 0.3075 vs 0.002615726552903652 / 7.2443037033081055; union/D_unif/tau0.1/uniform/excl/k0/r8: 0.1156 vs 0.002615726552903652 / 7.2443037033081055; union/D_unif/tau0.1/uniform/excl/k1/r8: 0.1155 vs 0.002615726552903652 / 7.2443037033081055; union/D_unif/tau0.5/r0/excl/k0/r8: 0.5796 vs 0.002615726552903652 / 7.2443037033081055; union/D_unif/tau0.5/uniform/excl/k0/r8: 0.2446 vs 0.002615726552903652 / 7.2443037033081055; union/D_unif/tau0.5/uniform/excl/k1/r8: 0.2449 vs 0.002615726552903652 / 7.2443037033081055 ...
P3: permitted-family cells with entries below their label 0 of 599; hard-zero rung-8 counts positive: True -> pass (non-permitted cells below g, expected: 441)
P4 (digests equal iff sources equal, an equal-digest pair with different sources a defect only if its switched mass differs too; non-empty rungs distinct from rung 0, empty rungs equal to it): 69/69 chains; empty-source cells 60; equal-digest pairs excused by equal switched mass 0
P5 (positive controls, pass or fail per curve, values withheld until the analysis code is frozen): code_specific_hard/E_lab/D_code: FAIL; hard_zero/E/D_unif: pass; hard_zero/E_lab/D_code: pass
d_b two-path check: 446 hard-zero cells, 21666 (cell, sequence, tau_q) checks with t* > 0; largest |column - recomputed| / bound 0.8854 (must be <= 1) -> pass
