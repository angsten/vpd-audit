# Tier 1 of the grid on main: NVIDIA A100-SXM4-40GB, bf16, sub-batch 64, 8 draws

Wall clock 4195 s; peak GPU memory 31.6 GB
Cells enumerated 651, run 651, failed 0; failed cell types: none

| tier | cells | E-equivalent passes | optional |
|---|---|---|---|
| tier_1 | 651 | 527.5 | 0 |
| tier_2 | 0 | 0 | 0 |
| tier_3 | 0 | 0 | 0 |

Adaptive rule (n_on alone, before any cell): {'D_code|tau0': {'insert_5a_6a': False, 'median_n_on_rung_6': 11996.5, 'n_on_rung_8': 28819.0, 'ratio': 0.4162705159790416, 'threshold': 0.9}, 'D_code|tau0.1': {'insert_5a_6a': True, 'median_n_on_rung_6': 8672.0, 'n_on_rung_8': 9624.0, 'ratio': 0.9010806317539485, 'threshold': 0.9}, 'D_code|tau0.5': {'insert_5a_6a': False, 'median_n_on_rung_6': 8272.0, 'n_on_rung_8': 9378.0, 'ratio': 0.8820644060567285, 'threshold': 0.9}, 'D_unif|tau0': {'insert_5a_6a': False, 'median_n_on_rung_6': 12384.0, 'n_on_rung_8': 33576.0, 'ratio': 0.3688348820586133, 'threshold': 0.9}, 'D_unif|tau0.1': {'insert_5a_6a': True, 'median_n_on_rung_6': 9086.5, 'n_on_rung_8': 9966.0, 'ratio': 0.91174994982942, 'threshold': 0.9}, 'D_unif|tau0.5': {'insert_5a_6a': False, 'median_n_on_rung_6': 8817.5, 'n_on_rung_8': 9926.0, 'ratio': 0.8883235946000403, 'threshold': 0.9}}; inserted {'D_code|tau0.1': ['5a', '6a'], 'D_unif|tau0.1': ['5a', '6a']}

| group | set | sequences | cells | ok | seconds | peak GB |
|---|---|---|---|---|---|---|
| E | E | 1024 | 404 | True | 3199.9 | 31.6 |
| E_lab | E_lab | 512 | 247 | True | 965.1 | 26.5 |

P1 (union chains, |rung 8 - rung 0| > 0.01): 9/9
- main/E/union/D_unif/tau0.1/r0/excl: rung 0 0.3417, rung 8 1.2876, difference +0.9458 -> pass
- main/E/union/D_unif/tau0.1/uniform/excl/k0: rung 0 0.2151, rung 8 0.8650, difference +0.6499 -> pass
- main/E/union/D_unif/tau0.1/uniform/excl/k1: rung 0 0.2151, rung 8 0.8650, difference +0.6499 -> pass
- main/E/union/D_unif/tau0.1/uniform/excl/k2: rung 0 0.2151, rung 8 0.8652, difference +0.6501 -> pass
- main/E/union/D_unif/tau0.1/uniform/excl/k3: rung 0 0.2152, rung 8 0.8651, difference +0.6499 -> pass
- main/E/union/D_unif/tau0.1/uniform/excl/k4: rung 0 0.2151, rung 8 0.8649, difference +0.6498 -> pass
- main/E/union/D_unif/tau0.1/uniform/excl/k5: rung 0 0.2151, rung 8 0.8650, difference +0.6500 -> pass
- main/E/union/D_unif/tau0.1/uniform/excl/k6: rung 0 0.2152, rung 8 0.8651, difference +0.6499 -> pass
- main/E/union/D_unif/tau0.1/uniform/excl/k7: rung 0 0.2151, rung 8 0.8650, difference +0.6499 -> pass
P2 (reported): rung 8 against unmasked and importances: union/D_unif/tau0.1/r0/excl/k0/r8: 1.2876 vs 0.011456812731921673 / 0.3417225182056427; union/D_unif/tau0.1/uniform/excl/k0/r8: 0.8650 vs 0.011456812731921673 / 0.3417225182056427; union/D_unif/tau0.1/uniform/excl/k1/r8: 0.8650 vs 0.011456812731921673 / 0.3417225182056427; union/D_unif/tau0.1/uniform/excl/k2/r8: 0.8652 vs 0.011456812731921673 / 0.3417225182056427; union/D_unif/tau0.1/uniform/excl/k3/r8: 0.8651 vs 0.011456812731921673 / 0.3417225182056427; union/D_unif/tau0.1/uniform/excl/k4/r8: 0.8649 vs 0.011456812731921673 / 0.3417225182056427 ...
P3: permitted-family cells with entries below their label 0 of 419; hard-zero rung-8 counts positive: True -> pass (non-permitted cells below g, expected: 219)
P4 (digests equal iff sources equal, an equal-digest pair with different sources a defect only if its switched mass differs too; non-empty rungs distinct from rung 0, empty rungs equal to it): 22/22 chains; empty-source cells 11; equal-digest pairs excused by equal switched mass 0
P5 (positive controls, pass or fail per curve, values withheld until the analysis code is frozen): hard_zero/E/D_unif: pass
d_b two-path check: 222 hard-zero cells, 71734 (cell, sequence, tau_q) checks with t* > 0; largest |column - recomputed| / bound 0.8484 (must be <= 1) -> pass
