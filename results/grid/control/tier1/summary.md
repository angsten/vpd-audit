# Tier 1 of the grid on control: NVIDIA A100 80GB PCIe, bf16, sub-batch 64, 8 draws

Wall clock 3108 s; peak GPU memory 31.6 GB
Cells enumerated 523, run 523, failed 0; failed cell types: none

| tier | cells | E-equivalent passes | optional |
|---|---|---|---|
| tier_1 | 523 | 423.5 | 0 |
| tier_2 | 0 | 0 | 0 |
| tier_3 | 0 | 0 | 0 |

Adaptive rule (n_on alone, before any cell): {'D_code|tau0': {'insert_5a_6a': False, 'median_n_on_rung_6': 9307.5, 'n_on_rung_8': 28178.0, 'ratio': 0.33031088082901555, 'threshold': 0.9}, 'D_code|tau0.1': {'insert_5a_6a': False, 'median_n_on_rung_6': 5066.0, 'n_on_rung_8': 5864.0, 'ratio': 0.8639154160982264, 'threshold': 0.9}, 'D_code|tau0.5': {'insert_5a_6a': False, 'median_n_on_rung_6': 4614.0, 'n_on_rung_8': 5612.0, 'ratio': 0.8221667854597291, 'threshold': 0.9}, 'D_unif|tau0': {'insert_5a_6a': False, 'median_n_on_rung_6': 9436.5, 'n_on_rung_8': 32456.0, 'ratio': 0.2907474735025881, 'threshold': 0.9}, 'D_unif|tau0.1': {'insert_5a_6a': False, 'median_n_on_rung_6': 5498.5, 'n_on_rung_8': 6361.0, 'ratio': 0.8644081119320861, 'threshold': 0.9}, 'D_unif|tau0.5': {'insert_5a_6a': False, 'median_n_on_rung_6': 5227.0, 'n_on_rung_8': 6325.0, 'ratio': 0.8264031620553359, 'threshold': 0.9}}; inserted none

| group | set | sequences | cells | ok | seconds | peak GB |
|---|---|---|---|---|---|---|
| E | E | 1024 | 324 | True | 2359.1 | 31.6 |
| E_lab | E_lab | 512 | 199 | True | 731.4 | 26.5 |

P1 (union chains, |rung 8 - rung 0| > 0.01): 9/9
- control/E/union/D_unif/tau0.1/r0/excl: rung 0 4.6920, rung 8 7.3079, difference +2.6160 -> pass
- control/E/union/D_unif/tau0.1/uniform/excl/k0: rung 0 0.2772, rung 8 2.9388, difference +2.6617 -> pass
- control/E/union/D_unif/tau0.1/uniform/excl/k1: rung 0 0.2774, rung 8 2.9383, difference +2.6609 -> pass
- control/E/union/D_unif/tau0.1/uniform/excl/k2: rung 0 0.2769, rung 8 2.9400, difference +2.6631 -> pass
- control/E/union/D_unif/tau0.1/uniform/excl/k3: rung 0 0.2769, rung 8 2.9400, difference +2.6631 -> pass
- control/E/union/D_unif/tau0.1/uniform/excl/k4: rung 0 0.2771, rung 8 2.9394, difference +2.6623 -> pass
- control/E/union/D_unif/tau0.1/uniform/excl/k5: rung 0 0.2770, rung 8 2.9383, difference +2.6613 -> pass
- control/E/union/D_unif/tau0.1/uniform/excl/k6: rung 0 0.2769, rung 8 2.9389, difference +2.6620 -> pass
- control/E/union/D_unif/tau0.1/uniform/excl/k7: rung 0 0.2771, rung 8 2.9390, difference +2.6620 -> pass
P2 (reported): rung 8 against unmasked and importances: union/D_unif/tau0.1/r0/excl/k0/r8: 7.3079 vs 0.01138682384043932 / 4.6919684410095215; union/D_unif/tau0.1/uniform/excl/k0/r8: 2.9388 vs 0.01138682384043932 / 4.6919684410095215; union/D_unif/tau0.1/uniform/excl/k1/r8: 2.9383 vs 0.01138682384043932 / 4.6919684410095215; union/D_unif/tau0.1/uniform/excl/k2/r8: 2.9400 vs 0.01138682384043932 / 4.6919684410095215; union/D_unif/tau0.1/uniform/excl/k3/r8: 2.9400 vs 0.01138682384043932 / 4.6919684410095215; union/D_unif/tau0.1/uniform/excl/k4/r8: 2.9394 vs 0.01138682384043932 / 4.6919684410095215 ...
P3: permitted-family cells with entries below their label 0 of 339; hard-zero rung-8 counts positive: True -> pass (non-permitted cells below g, expected: 167)
P4 (digests equal iff sources equal, an equal-digest pair with different sources a defect only if its switched mass differs too; non-empty rungs distinct from rung 0, empty rungs equal to it): 22/22 chains; empty-source cells 15; equal-digest pairs excused by equal switched mass 0
P5 (positive controls, pass or fail per curve, values withheld until the analysis code is frozen): hard_zero/E/D_unif: pass
d_b two-path check: 174 hard-zero cells, 59328 (cell, sequence, tau_q) checks with t* > 0; largest |column - recomputed| / bound 0.7934 (must be <= 1) -> pass
