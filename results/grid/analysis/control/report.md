# Analysis of the grid, run control (the pre-registered read order)

Stores: tier1/E, tier1/E_lab, tier2/E, tier2/E_lab, tier3/E__levels, tier3/E__never_named, tier3/E__tau0_union; sets E (1024 sequences, 818 cells), E_lab (512 sequences, 433 cells); replicates 10000; seed (master 0, boot, set); commit c57fc2b543b4 (dirty 0).

## 0. Asserts
- References bitwise across stores per set: {'E': {'n_stores': 5, 'pass': True}, 'E_lab': {'n_stores': 2, 'pass': True}}
- Verification-store canary (equality only): {'available': False}
- Pre-reads: {'t_star': {'E': {'n_cells': 189, 'n_rows': 193536, 't_star_0.1': True, 't_star_0': True, 'n_touched_0.1': True, 'n_touched_0': True}, 'E_lab': {'n_cells': 294, 'n_rows': 150528, 't_star_0.1': True, 't_star_0': True, 'n_touched_0.1': True, 'n_touched_0': True}}, 'sigma': {'E': {'n_cells': 537, 'max_ratio_to_tolerance': 0.03177263929900095, 'pass': True}, 'E_lab': {'n_cells': 408, 'max_ratio_to_tolerance': 0.030663172885838443, 'pass': True}}}
- Two-path recompute from kl_prefix_sum and the reference arrays: E: 189 cells, 144226 checks, max ratio 0.8666, pass; E_lab: 294 cells, 161020 checks, max ratio 0.7858, pass
- Every non-reference, non-donor-side cell in exactly one chain set (rule, descriptive family, descriptive rung): E: 793 (787, 6, 0); E_lab: 408 (408, 0, 0)

## 1. Preconditions and the sanity checks
P1 (10/10): union/E/D_unif/tau0.1/r0/excl/ctl-none: rung 0 4.6920, rung 8 7.3079 -> pass; union/E/D_unif/tau0.1/uniform/excl/k0/ctl-none: rung 0 0.2772, rung 8 2.9388 -> pass; union/E/D_unif/tau0.1/uniform/excl/k1/ctl-none: rung 0 0.2774, rung 8 2.9383 -> pass; union/E/D_unif/tau0.1/uniform/excl/k2/ctl-none: rung 0 0.2769, rung 8 2.9400 -> pass; union/E/D_unif/tau0.1/uniform/excl/k3/ctl-none: rung 0 0.2769, rung 8 2.9400 -> pass; union/E/D_unif/tau0.1/uniform/excl/k4/ctl-none: rung 0 0.2771, rung 8 2.9394 -> pass; union/E/D_unif/tau0.1/uniform/excl/k5/ctl-none: rung 0 0.2770, rung 8 2.9383 -> pass; union/E/D_unif/tau0.1/uniform/excl/k6/ctl-none: rung 0 0.2769, rung 8 2.9389 -> pass; union/E/D_unif/tau0.1/uniform/excl/k7/ctl-none: rung 0 0.2771, rung 8 2.9390 -> pass; union/E/D_unif/tau0/r0/excl/ctl-none: rung 0 4.6920, rung 8 0.5660 -> pass
P2: union/E/D_unif/tau0.1/r0/excl/ctl-none: rung 8 7.3079 vs unmasked 0.0114 / importances 4.6920; union/E/D_unif/tau0.1/uniform/excl/k0/ctl-none: rung 8 2.9388 vs unmasked 0.0114 / importances 4.6920; union/E/D_unif/tau0.1/uniform/excl/k1/ctl-none: rung 8 2.9383 vs unmasked 0.0114 / importances 4.6920; union/E/D_unif/tau0.1/uniform/excl/k2/ctl-none: rung 8 2.9400 vs unmasked 0.0114 / importances 4.6920; union/E/D_unif/tau0.1/uniform/excl/k3/ctl-none: rung 8 2.9400 vs unmasked 0.0114 / importances 4.6920; union/E/D_unif/tau0.1/uniform/excl/k4/ctl-none: rung 8 2.9394 vs unmasked 0.0114 / importances 4.6920; union/E/D_unif/tau0.1/uniform/excl/k5/ctl-none: rung 8 2.9383 vs unmasked 0.0114 / importances 4.6920; union/E/D_unif/tau0.1/uniform/excl/k6/ctl-none: rung 8 2.9389 vs unmasked 0.0114 / importances 4.6920; union/E/D_unif/tau0.1/uniform/excl/k7/ctl-none: rung 8 2.9390 vs unmasked 0.0114 / importances 4.6920; union/E/D_unif/tau0/r0/excl/ctl-none: rung 8 0.5660 vs unmasked 0.0114 / importances 4.6920
P3: permitted cells below their label 0 of 758; hard-zero rung-8 counts positive True -> pass
P4: 52/52 chains
P5 (positive controls, by the registered rule): hard_zero/E/D_unif/tau0.1/ones/incl/ctl-none: pass (5 rungs; unconditional damage on E material at rung 4 and beyond); hard_zero/E_lab/D_code/tau0.1/ones/incl/ctl-none: pass (5 rungs; erase exceeds its plain control on Github); code_specific_hard/E_lab/D_code/tau0.1/ones/incl/ctl-none: pass (8 rungs; erase exceeds its complement control on Github)

| id | pass | note |
|---|---|---|
| E1 | True | rung 0 equals importances-as-masks (0.0e+00); rung 8 7.3079 against unmasked 0.0114 and the start 4.6920: above the start (the rule's own rung-8 comparison, not a bug) |
| E2/E4 | True | n_on non-decreasing within every nested run of every union chain; violations none |
| E3 | True | soft-erase rung 0 equals unmasked; rung 8 10.0093 against importances-as-masks 4.6920 |
| E6 | True | no NaN kl_mean anywhere (0 found); the sequence bootstrap widths are in the tables |
| E9 | True | clean-prefix fractions non-increasing within each nested run of every hard-zero chain at both tau_q; violations none; pairs not nested by count (skipped) 0 |

## 2. Curve 1: the union under r = 0, tau = 0.1, Delta excluded, on E
Chain `union/E/D_unif/tau0.1/r0/excl/ctl-none`; rung 0 mean 4.6920; m = 8 rungs compared; **label: fails** (at m = 8: fails); j_det = 3, j_mat = 3, first repair rung = 1; per draw: k0: det 3, mat 3, k1: det 3, mat 3, k2: det 2, mat 2, k3: det 2, mat 2, k4: det 2, mat 2, k5: det 2, mat 2, k6: det 3, mat 3, k7: det 2, mat 3

| rung | n_on | mean_sigma | overlap | mean_kl | excess | interval | half_width | two_level | draws_positive | fraction_seq_above_X | detected | material | repair | differs_at_m_8 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 60.7500 | 53.4033 | 0.0163 | 4.0621 | -0.6298 | [-0.7031, -0.5662] | 0.0685 | [-0.8874, -0.3622] | 0/8 | 0.0371 | False | False | True | False |
| 2 | 392.5000 | 374.5391 | 0.0849 | 5.0158 | 0.3238 | [+0.2095, +0.4291] | 0.1098 | [-0.4232, +1.0310] | 5/8 | 0.7500 | False | False | False | False |
| 3 | 1792.0000 | 1755.8110 | 0.3276 | 5.3777 | 0.6857 | [+0.5618, +0.8038] | 0.1210 | [+0.4138, +1.0720] | 8/8 | 0.8193 | True | True | False | False |
| 4 | 2483.6250 | 2447.9668 | 0.4136 | 7.3694 | 2.6775 | [+2.5395, +2.8069] | 0.1337 | [+2.2286, +3.0047] | 8/8 | 0.9600 | True | True | False | False |
| 5 | 4394.3750 | 4348.7344 | 0.7093 | 7.3900 | 2.6980 | [+2.5610, +2.8272] | 0.1331 | [+2.5518, +2.8336] | 8/8 | 0.9561 | True | True | False | False |
| 6 | 5516.0000 | 5468.5635 | 0.8747 | 7.3332 | 2.6413 | [+2.5063, +2.7692] | 0.1314 | [+2.5061, +2.7699] | 8/8 | 0.9551 | True | True | False | False |
| 7 | 6053.1250 | 6005.5181 | 0.9542 | 7.3122 | 2.6203 | [+2.4850, +2.7480] | 0.1315 | [+2.4869, +2.7484] | 8/8 | 0.9541 | True | True | False | False |
| 8 | 6361.0000 | 6313.3740 | 0.9983 | 7.3079 | 2.6160 | [+2.4806, +2.7442] | 0.1318 | [+2.4806, +2.7442] | 1/1 | 0.9541 | True | True | False | False |

Paired union minus control on the same sequence, draw, and rung (95 percent uncorrected), with the pre-reads' overlap of the two sets: rung 1: -0.4056 [-0.4477, -0.3664] (overlap 0.016); rung 2: +1.2200 [+1.1855, +1.2541] (overlap 0.085); rung 3: +2.0264 [+2.0038, +2.0482] (overlap 0.328); rung 4: +3.3348 [+3.3020, +3.3683] (overlap 0.414)
Rung 4 minus rung 3 at nearly the same count (diffuse against concentrated), paired: +1.9918 [+1.9592, +2.0250].
Rung 4 (one donor sequence): excess +2.6775 [+2.5395, +2.8069], fraction of sequences with excess above X 0.960.
Per-rung excess by reader label on E (each label's own resample, the curve's m):
| label | n | rung | excess | interval | half_width | detected | material |
|---|---|---|---|---|---|---|---|
| code | 120 | 1 | -1.4272 | [-1.7742, -1.1355] | 0.3194 | False | False |
| code | 120 | 2 | -1.3083 | [-1.8093, -0.8763] | 0.4665 | False | False |
| code | 120 | 3 | -0.7510 | [-1.3187, -0.2380] | 0.5404 | False | False |
| code | 120 | 4 | 1.4648 | [+0.8344, +2.0041] | 0.5848 | True | True |
| code | 120 | 5 | 1.4712 | [+0.8402, +2.0104] | 0.5851 | True | True |
| code | 120 | 6 | 1.4010 | [+0.7733, +1.9415] | 0.5841 | True | True |
| code | 120 | 7 | 1.3796 | [+0.7532, +1.9218] | 0.5843 | True | True |
| code | 120 | 8 | 1.3792 | [+0.7521, +1.9215] | 0.5847 | True | True |
| mixed | 27 | 1 | -1.1275 | [-1.6246, -0.7588] | 0.4329 | False | False |
| mixed | 27 | 2 | -0.7483 | [-1.4464, -0.1970] | 0.6247 | False | False |
| mixed | 27 | 3 | -0.3720 | [-1.2038, +0.3009] | 0.7523 | False | False |
| mixed | 27 | 4 | 1.7538 | [+0.8898, +2.4737] | 0.7920 | True | True |
| mixed | 27 | 5 | 1.7727 | [+0.8899, +2.5026] | 0.8064 | True | True |
| mixed | 27 | 6 | 1.7251 | [+0.8500, +2.4500] | 0.8000 | True | True |
| mixed | 27 | 7 | 1.7054 | [+0.8332, +2.4300] | 0.7984 | True | True |
| mixed | 27 | 8 | 1.7067 | [+0.8359, +2.4308] | 0.7975 | True | True |
| other | 158 | 1 | -0.5718 | [-0.8410, -0.3669] | 0.2370 | False | False |
| other | 158 | 2 | 0.4668 | [+0.0488, +0.8055] | 0.3783 | False | False |
| other | 158 | 3 | 1.1336 | [+0.6551, +1.5417] | 0.4433 | True | True |
| other | 158 | 4 | 3.4765 | [+2.9345, +3.9834] | 0.5245 | True | True |
| other | 158 | 5 | 3.4571 | [+2.9151, +3.9557] | 0.5203 | True | True |
| other | 158 | 6 | 3.3189 | [+2.7894, +3.8005] | 0.5056 | True | True |
| other | 158 | 7 | 3.2982 | [+2.7670, +3.7812] | 0.5071 | True | True |
| other | 158 | 8 | 3.3074 | [+2.7759, +3.7947] | 0.5094 | True | True |
| prose | 719 | 1 | -0.4908 | [-0.5450, -0.4513] | 0.0469 | False | False |
| prose | 719 | 2 | 0.6051 | [+0.5274, +0.6705] | 0.0715 | False | False |
| prose | 719 | 3 | 0.8668 | [+0.7830, +0.9395] | 0.0782 | True | True |
| prose | 719 | 4 | 2.7390 | [+2.6417, +2.8260] | 0.0922 | True | True |
| prose | 719 | 5 | 2.7707 | [+2.6735, +2.8583] | 0.0924 | True | True |
| prose | 719 | 6 | 2.7338 | [+2.6372, +2.8208] | 0.0918 | True | True |
| prose | 719 | 7 | 2.7127 | [+2.6163, +2.7998] | 0.0918 | True | True |
| prose | 719 | 8 | 2.7046 | [+2.6082, +2.7915] | 0.0917 | True | True |

Paired union minus control by reader label at rungs 1 to 4 and 5a (each label's own resample, uncorrected 95 percent), the control's per-label excess beside:
| label | n | rung | union_minus_control | interval_uncorrected | half_width | control_excess | control_interval_uncorrected |
|---|---|---|---|---|---|---|---|
| code | 120 | 1 | -1.0021 | [-1.2106, -0.8144] | 0.1981 | -0.4251 | [-0.4699, -0.3833] |
| code | 120 | 2 | 0.6112 | [+0.4406, +0.7659] | 0.1626 | -1.9195 | [-2.1226, -1.7299] |
| code | 120 | 3 | 1.7184 | [+1.6276, +1.8081] | 0.0902 | -2.4694 | [-2.8149, -2.1483] |
| code | 120 | 4 | 3.2275 | [+3.1175, +3.3312] | 0.1069 | -1.7627 | [-2.1041, -1.4465] |
| mixed | 27 | 1 | -0.8062 | [-1.0944, -0.5664] | 0.2640 | -0.3213 | [-0.3764, -0.2719] |
| mixed | 27 | 2 | 0.6994 | [+0.5075, +0.8760] | 0.1843 | -1.4477 | [-1.7596, -1.1871] |
| mixed | 27 | 3 | 1.8346 | [+1.6943, +1.9700] | 0.1378 | -2.2066 | [-2.6834, -1.8045] |
| mixed | 27 | 4 | 3.2335 | [+3.0638, +3.4060] | 0.1711 | -1.4797 | [-1.9705, -1.0644] |
| other | 158 | 1 | -0.3757 | [-0.5312, -0.2423] | 0.1445 | -0.1961 | [-0.2263, -0.1694] |
| other | 158 | 2 | 1.3755 | [+1.2541, +1.4886] | 0.1172 | -0.9087 | [-1.0805, -0.7599] |
| other | 158 | 3 | 1.9855 | [+1.9079, +2.0615] | 0.0768 | -0.8519 | [-1.1506, -0.5860] |
| other | 158 | 4 | 3.6281 | [+3.4863, +3.7701] | 0.1419 | -0.1516 | [-0.4477, +0.1168] |
| prose | 719 | 1 | -0.2976 | [-0.3272, -0.2727] | 0.0272 | -0.1932 | [-0.2002, -0.1867] |
| prose | 719 | 2 | 1.3069 | [+1.2822, +1.3307] | 0.0242 | -0.7018 | [-0.7347, -0.6719] |
| prose | 719 | 3 | 2.0940 | [+2.0753, +2.1124] | 0.0185 | -1.2272 | [-1.2762, -1.1829] |
| prose | 719 | 4 | 3.2921 | [+3.2639, +3.3195] | 0.0278 | -0.5531 | [-0.6027, -0.5076] |

## 2b. Its plain control
Chain `union/E/D_unif/tau0.1/r0/excl/ctl-plain`; rung 0 mean 4.6920; m = 8 rungs compared; **label: fails** (at m = 8: fails); j_det = 5, j_mat = 5, first repair rung = 1; per draw: k0: det 4, mat 4, k1: det 5, mat 5, k2: det 5, mat 5, k3: det 5, mat 5, k4: det 5, mat 5, k5: det 5, mat 5, k6: det 5, mat 5, k7: det 5, mat 5

| rung | n_on | mean_sigma | overlap | mean_kl | excess | interval | half_width | two_level | draws_positive | fraction_seq_above_X | detected | material | repair | differs_at_m_8 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 60.7500 | 60.1005 | 0.0163 | 4.4677 | -0.2242 | [-0.2381, -0.2115] | 0.0133 | [-0.3706, -0.0831] | 0/8 | 0.0029 | False | False | True | False |
| 2 | 392.5000 | 388.4193 | 0.0849 | 3.7959 | -0.8961 | [-0.9660, -0.8332] | 0.0664 | [-1.1428, -0.6835] | 0/8 | 0.0029 | False | False | True | False |
| 3 | 1792.0000 | 1775.7208 | 0.3276 | 3.3513 | -1.3407 | [-1.4491, -1.2433] | 0.1029 | [-1.7016, -0.9322] | 0/8 | 0.0615 | False | False | True | False |
| 4 | 2483.6250 | 2463.6184 | 0.4136 | 4.0346 | -0.6573 | [-0.7662, -0.5574] | 0.1044 | [-1.1463, -0.0030] | 1/8 | 0.1543 | False | False | True | False |
| 5 | 4394.3750 | 4359.8154 | 0.7093 | 5.9529 | 1.2609 | [+1.1306, +1.3845] | 0.1269 | [+0.7098, +1.9324] | 8/8 | 0.8936 | True | True | False | False |
| 6 | 5516.0000 | 5474.0571 | 0.8747 | 6.6738 | 1.9818 | [+1.8361, +2.1207] | 0.1423 | [+1.6470, +2.3425] | 8/8 | 0.9277 | True | True | False | False |
| 7 | 6053.1250 | 6007.6104 | 0.9542 | 7.0803 | 2.3884 | [+2.2500, +2.5204] | 0.1352 | [+2.0717, +2.6482] | 8/8 | 0.9463 | True | True | False | False |
| 8 | 6361.0000 | 6313.3779 | 0.9983 | 7.3059 | 2.6139 | [+2.4783, +2.7422] | 0.1319 | [+2.4783, +2.7422] | 1/1 | 0.9541 | True | True | False | False |
Rung 4 (one donor sequence): excess -0.6573 [-0.7662, -0.5574], fraction of sequences with excess above X 0.154.

## 3. The mass-matched deciles and the slope
`union/E/D_unif/tau0.1/r0/excl/ctl-none`: edges from pre-reads: 10.3, 68.3, 346.0, 547.2, 1816.0, 2652.9, 4194.3, 4650.0, 5456.5, 5978.5, 6092.5; union slope 5.057e-04 [+4.979e-04, +5.138e-04] (intercept +0.0960 [+0.0273, +0.1612]); control slope 5.488e-04 [+5.354e-04, +5.626e-04]
| bin | overflow | edge_low | edge_high | n_points_union | n_points_control | n_sequences_union | n_sequences_control | populated | union_mean_excess | control_mean_excess | difference | interval |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 0 | False | 10.2987 | 68.3178 | 5734 | 4096 | 1024 | 1024 | True | -0.5862 | -0.0950 | -0.4912 | [-0.5267, -0.4579] |
| 1 | False | 68.3178 | 345.9710 | 5734 | 7168 | 1024 | 1024 | True | -0.0865 | -0.4995 | 0.4131 | [+0.3576, +0.4652] |
| 2 | False | 345.9710 | 547.1518 | 5734 | 5120 | 1024 | 1024 | True | 0.4967 | -0.9487 | 1.4454 | [+1.4098, +1.4810] |
| 3 | False | 547.1518 | 1815.9693 | 5735 | 6144 | 1024 | 1024 | True | 0.6055 | -1.2847 | 1.8902 | [+1.8610, +1.9182] |
| 4 | False | 1815.9693 | 2652.9211 | 5734 | 6144 | 1024 | 1024 | True | 1.9898 | -1.2239 | 3.2137 | [+3.1861, +3.2417] |
| 5 | False | 2652.9211 | 4194.3233 | 5734 | 5140 | 1024 | 1024 | True | 2.7088 | -0.1027 | 2.8115 | [+2.7887, +2.8346] |
| 6 | False | 4194.3233 | 4650.0180 | 5735 | 6141 | 1024 | 1024 | True | 2.7020 | 1.1470 | 1.5550 | [+1.5304, +1.5794] |
| 7 | False | 4650.0180 | 5456.5330 | 5734 | 5208 | 1024 | 1024 | True | 2.6556 | 1.8124 | 0.8432 | [+0.8187, +0.8666] |
| 8 | False | 5456.5330 | 5978.4933 | 5734 | 6097 | 1024 | 1024 | True | 2.6120 | 2.2725 | 0.3395 | [+0.3149, +0.3636] |
| 9 | False | 5978.4933 | 6092.5078 | 5734 | 6085 | 1024 | 1024 | True | 2.6409 | 2.4670 | 0.1740 | [+0.1629, +0.1845] |
| 10 | True | 6092.5078 | inf | 1 | 1 | 1 | 1 | False |  |  |  |  |
Local slopes (difference quotients): 1->2: 2.970e-03; 2->3: 2.620e-04; 3->4: 2.878e-03; 4->5: 1.081e-05; 5->6: -5.069e-05; 6->7: -3.910e-05

`union/E/D_unif/tau0.1/uniform/excl/k0/ctl-none`: edges from the loop's sigma column: 34.5, 37.3, 210.3, 907.2, 910.3, 1780.5, 2324.9, 2329.6, 2798.7, 3027.0, 3039.6; union slope 9.134e-04 [+8.991e-04, +9.284e-04] (intercept +0.4380 [+0.4276, +0.4483]); control slope 7.969e-04 [+7.817e-04, +8.130e-04]
| bin | overflow | edge_low | edge_high | n_points_union | n_points_control | n_sequences_union | n_sequences_control | populated | union_mean_excess | control_mean_excess | difference | interval |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 0 | False | 34.4957 | 37.2587 | 717 | 0 | 717 | 0 | False | 0.0853 |  |  |  |
| 1 | False | 37.2587 | 210.3335 | 717 | 1024 | 617 | 1024 | True | 0.1814 | 0.0010 | 0.1805 | [+0.1703, +0.1908] |
| 2 | False | 210.3335 | 907.1568 | 717 | 1024 | 684 | 1024 | True | 0.5464 | 0.0107 | 0.5357 | [+0.4801, +0.5919] |
| 3 | False | 907.1568 | 910.2606 | 716 | 0 | 716 | 0 | False | 1.8358 |  |  |  |
| 4 | False | 910.2606 | 1780.5480 | 717 | 1028 | 694 | 1024 | True | 2.6357 | 0.1435 | 2.4922 | [+2.4210, +2.5674] |
| 5 | False | 1780.5480 | 2324.8548 | 717 | 1038 | 717 | 1024 | True | 2.7641 | 0.6872 | 2.0768 | [+2.0328, +2.1222] |
| 6 | False | 2324.8548 | 2329.5538 | 716 | 144 | 716 | 144 | True | 2.6366 | 1.6277 | 1.0089 | [+0.9040, +1.1054] |
| 7 | False | 2329.5538 | 2798.6895 | 717 | 1046 | 717 | 1015 | True | 2.8466 | 1.4152 | 1.4315 | [+1.3932, +1.4714] |
| 8 | False | 2798.6895 | 3026.9918 | 717 | 1038 | 717 | 1015 | True | 2.7559 | 2.1993 | 0.5566 | [+0.5286, +0.5846] |
| 9 | False | 3026.9918 | 3039.5667 | 717 | 825 | 717 | 825 | True | 2.5651 | 2.3292 | 0.2359 | [+0.2173, +0.2534] |
| 10 | True | 3039.5667 | inf | 0 | 1 | 0 | 1 | False |  |  |  |  |
Local slopes (difference quotients): 1->2: 1.113e-03; 2->3: 2.276e-03; 3->4: 1.093e-03; 4->5: -7.204e-05; 5->6: -4.184e-05; 6->7: -1.984e-04

`union/E/D_unif/tau0.1/uniform/excl/k1/ctl-none`: edges from the loop's sigma column: 30.3, 32.4, 203.8, 865.0, 868.1, 1006.9, 2182.6, 2187.2, 2692.2, 2964.5, 2976.7; union slope 9.299e-04 [+9.159e-04, +9.444e-04] (intercept +0.3675 [+0.3573, +0.3779]); control slope 8.215e-04 [+8.022e-04, +8.419e-04]
| bin | overflow | edge_low | edge_high | n_points_union | n_points_control | n_sequences_union | n_sequences_control | populated | union_mean_excess | control_mean_excess | difference | interval |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 0 | False | 30.2701 | 32.4287 | 717 | 0 | 717 | 0 | False | 0.0193 |  |  |  |
| 1 | False | 32.4287 | 203.8499 | 717 | 1024 | 660 | 1024 | True | 0.1214 | 0.0008 | 0.1206 | [+0.1134, +0.1276] |
| 2 | False | 203.8499 | 865.0348 | 717 | 1024 | 684 | 1024 | True | 0.3837 | 0.0092 | 0.3745 | [+0.3356, +0.4155] |
| 3 | False | 865.0348 | 868.0713 | 716 | 0 | 716 | 0 | False | 1.0869 |  |  |  |
| 4 | False | 868.0713 | 1006.8940 | 717 | 1024 | 690 | 1024 | True | 2.3007 | 0.1566 | 2.1441 | [+2.0713, +2.2194] |
| 5 | False | 1006.8940 | 2182.6094 | 716 | 1032 | 709 | 1024 | True | 2.2546 | 0.2783 | 1.9763 | [+1.9259, +2.0306] |
| 6 | False | 2182.6094 | 2187.2035 | 717 | 29 | 717 | 29 | False | 2.5197 |  |  |  |
| 7 | False | 2187.2035 | 2692.2135 | 717 | 1063 | 717 | 1024 | True | 2.8404 | 1.7537 | 1.0867 | [+1.0486, +1.1239] |
| 8 | False | 2692.2135 | 2964.5083 | 717 | 1039 | 717 | 1022 | True | 2.7702 | 1.9904 | 0.7798 | [+0.7492, +0.8110] |
| 9 | False | 2964.5083 | 2976.7039 | 717 | 932 | 717 | 932 | True | 2.5975 | 2.0991 | 0.4984 | [+0.4689, +0.5265] |
| 10 | True | 2976.7039 | inf | 0 | 1 | 0 | 1 | False |  |  |  |  |
Local slopes (difference quotients): 1->2: 9.733e-04; 2->3: 1.421e-03; 3->4: 8.909e-03; 4->5: 2.490e-04; 5->6: 1.867e-04; 6->7: -9.425e-05

`union/E/D_unif/tau0.1/uniform/excl/k2/ctl-none`: edges from the loop's sigma column: 32.0, 34.5, 173.5, 888.0, 891.6, 1378.3, 2302.0, 2306.8, 2726.7, 2989.9, 3001.9; union slope 9.215e-04 [+9.082e-04, +9.354e-04] (intercept +0.4661 [+0.4549, +0.4776]); control slope 8.027e-04 [+7.861e-04, +8.204e-04]
| bin | overflow | edge_low | edge_high | n_points_union | n_points_control | n_sequences_union | n_sequences_control | populated | union_mean_excess | control_mean_excess | difference | interval |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 0 | False | 32.0327 | 34.5326 | 717 | 0 | 717 | 0 | False | 0.0601 |  |  |  |
| 1 | False | 34.5326 | 173.4514 | 717 | 1024 | 717 | 1024 | True | 0.1172 | 0.0008 | 0.1164 | [+0.1098, +0.1231] |
| 2 | False | 173.4514 | 888.0403 | 717 | 1024 | 639 | 1024 | True | 0.5156 | 0.0115 | 0.5041 | [+0.4431, +0.5681] |
| 3 | False | 888.0403 | 891.5844 | 716 | 0 | 716 | 0 | False | 1.6282 |  |  |  |
| 4 | False | 891.5844 | 1378.3439 | 717 | 1024 | 710 | 1024 | True | 2.5442 | 0.1761 | 2.3681 | [+2.2992, +2.4404] |
| 5 | False | 1378.3439 | 2301.9640 | 717 | 1040 | 716 | 1024 | True | 2.7436 | 0.4567 | 2.2869 | [+2.2426, +2.3317] |
| 6 | False | 2301.9640 | 2306.7933 | 716 | 131 | 716 | 131 | True | 2.6351 | 1.8618 | 0.7733 | [+0.6316, +0.9023] |
| 7 | False | 2306.7933 | 2726.7094 | 717 | 1018 | 717 | 1000 | True | 2.8665 | 1.4961 | 1.3705 | [+1.3343, +1.4082] |
| 8 | False | 2726.7094 | 2989.9370 | 717 | 1011 | 717 | 1005 | True | 2.7838 | 2.0042 | 0.7796 | [+0.7472, +0.8139] |
| 9 | False | 2989.9370 | 3001.8689 | 717 | 894 | 717 | 894 | True | 2.5865 | 2.3191 | 0.2673 | [+0.2417, +0.2914] |
| 10 | True | 3001.8689 | inf | 0 | 2 | 0 | 2 | False |  |  |  |  |
Local slopes (difference quotients): 1->2: 8.702e-04; 2->3: 2.105e-03; 3->4: 2.322e-03; 4->5: -7.413e-05; 5->6: 4.841e-05; 6->7: -1.643e-04

`union/E/D_unif/tau0.1/uniform/excl/k3/ctl-none`: edges from the loop's sigma column: 24.3, 25.8, 237.5, 270.8, 273.7, 909.6, 2190.7, 2196.1, 2703.3, 2985.0, 2998.2; union slope 5.635e-04 [+5.495e-04, +5.782e-04] (intercept +1.3013 [+1.2807, +1.3218]); control slope 7.489e-04 [+7.333e-04, +7.654e-04]
| bin | overflow | edge_low | edge_high | n_points_union | n_points_control | n_sequences_union | n_sequences_control | populated | union_mean_excess | control_mean_excess | difference | interval |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 0 | False | 24.3112 | 25.8295 | 717 | 0 | 717 | 0 | False | 0.0180 |  |  |  |
| 1 | False | 25.8295 | 237.4578 | 717 | 1024 | 523 | 1024 | True | 1.9674 | 0.0012 | 1.9662 | [+1.8605, +2.0705] |
| 2 | False | 237.4578 | 270.8311 | 717 | 1024 | 716 | 1024 | True | 3.1427 | 0.0127 | 3.1300 | [+3.0331, +3.2220] |
| 3 | False | 270.8311 | 273.6539 | 716 | 0 | 716 | 0 | False | 0.3389 |  |  |  |
| 4 | False | 273.6539 | 909.5640 | 717 | 1024 | 705 | 1024 | True | 1.9234 | 0.0183 | 1.9051 | [+1.8121, +1.9997] |
| 5 | False | 909.5640 | 2190.7347 | 717 | 1031 | 713 | 1024 | True | 2.3405 | 0.1657 | 2.1748 | [+2.1118, +2.2426] |
| 6 | False | 2190.7347 | 2196.0856 | 716 | 71 | 716 | 71 | True | 2.5710 | 1.5923 | 0.9787 | [+0.8369, +1.1120] |
| 7 | False | 2196.0856 | 2703.3021 | 717 | 1001 | 716 | 998 | True | 2.8572 | 1.1662 | 1.6910 | [+1.6563, +1.7259] |
| 8 | False | 2703.3021 | 2985.0409 | 717 | 1096 | 717 | 1024 | True | 2.7923 | 1.9026 | 0.8897 | [+0.8576, +0.9225] |
| 9 | False | 2985.0409 | 2998.2476 | 717 | 896 | 717 | 896 | True | 2.5682 | 2.2130 | 0.3552 | [+0.3301, +0.3797] |
| 10 | True | 2998.2476 | inf | 0 | 1 | 0 | 1 | False |  |  |  |  |
Local slopes (difference quotients): 1->2: 1.339e-03; 2->3: 3.097e-03; 3->4: -1.775e-03; 4->5: -4.155e-04; 5->6: 1.196e-04; 6->7: -1.435e-04

`union/E/D_unif/tau0.1/uniform/excl/k4/ctl-none`: edges from the loop's sigma column: 39.8, 43.9, 180.8, 773.8, 777.0, 1229.2, 2143.4, 2147.9, 2743.4, 3017.0, 3029.9; union slope 8.865e-04 [+8.741e-04, +8.995e-04] (intercept +0.5764 [+0.5640, +0.5896]); control slope 8.396e-04 [+8.251e-04, +8.546e-04]
| bin | overflow | edge_low | edge_high | n_points_union | n_points_control | n_sequences_union | n_sequences_control | populated | union_mean_excess | control_mean_excess | difference | interval |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 0 | False | 39.8473 | 43.9097 | 717 | 0 | 717 | 0 | False | 0.0263 |  |  |  |
| 1 | False | 43.9097 | 180.7620 | 717 | 1024 | 704 | 1024 | True | 0.1634 | 0.0023 | 0.1611 | [+0.1497, +0.1728] |
| 2 | False | 180.7620 | 773.7787 | 717 | 1024 | 697 | 1024 | True | 0.4558 | 0.0087 | 0.4471 | [+0.3955, +0.5047] |
| 3 | False | 773.7787 | 776.9990 | 716 | 0 | 716 | 0 | False | 1.5629 |  |  |  |
| 4 | False | 776.9990 | 1229.1862 | 717 | 1024 | 706 | 1024 | True | 2.7347 | 0.1106 | 2.6241 | [+2.5421, +2.7091] |
| 5 | False | 1229.1862 | 2143.3640 | 717 | 1029 | 715 | 1024 | True | 2.8458 | 0.2735 | 2.5723 | [+2.5294, +2.6174] |
| 6 | False | 2143.3640 | 2147.8848 | 716 | 57 | 716 | 57 | False | 2.6460 |  |  |  |
| 7 | False | 2147.8848 | 2743.3510 | 717 | 1141 | 717 | 1024 | True | 2.8344 | 1.2650 | 1.5693 | [+1.5294, +1.6106] |
| 8 | False | 2743.3510 | 3017.0430 | 717 | 1037 | 717 | 1012 | True | 2.7623 | 2.2504 | 0.5120 | [+0.4815, +0.5432] |
| 9 | False | 3017.0430 | 3029.8896 | 717 | 831 | 717 | 831 | True | 2.5686 | 2.3629 | 0.2057 | [+0.1872, +0.2235] |
| 10 | True | 3029.8896 | inf | 0 | 1 | 0 | 1 | False |  |  |  |  |
Local slopes (difference quotients): 1->2: 1.365e-03; 2->3: 2.315e-03; 3->4: 3.069e-03; 4->5: -1.959e-04; 5->6: -1.001e-04; 6->7: -1.292e-04

`union/E/D_unif/tau0.1/uniform/excl/k5/ctl-none`: edges from the loop's sigma column: 19.6, 21.7, 142.0, 936.9, 940.2, 1485.4, 2163.2, 2168.9, 2793.3, 2989.1, 3000.6; union slope 9.045e-04 [+8.913e-04, +9.181e-04] (intercept +0.5259 [+0.5120, +0.5403]); control slope 7.893e-04 [+7.728e-04, +8.069e-04]
| bin | overflow | edge_low | edge_high | n_points_union | n_points_control | n_sequences_union | n_sequences_control | populated | union_mean_excess | control_mean_excess | difference | interval |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 0 | False | 19.5739 | 21.6906 | 717 | 0 | 717 | 0 | False | 0.0239 |  |  |  |
| 1 | False | 21.6906 | 142.0384 | 717 | 1024 | 716 | 1024 | True | 0.0989 | 0.0009 | 0.0980 | [+0.0914, +0.1046] |
| 2 | False | 142.0384 | 936.8721 | 717 | 1024 | 634 | 1024 | True | 0.5490 | 0.0073 | 0.5417 | [+0.4681, +0.6195] |
| 3 | False | 936.8721 | 940.1701 | 716 | 0 | 716 | 0 | False | 2.1194 |  |  |  |
| 4 | False | 940.1701 | 1485.3586 | 717 | 1024 | 704 | 1024 | True | 2.5663 | 0.2004 | 2.3660 | [+2.3019, +2.4334] |
| 5 | False | 1485.3586 | 2163.2293 | 717 | 1030 | 717 | 1024 | True | 2.7291 | 0.4251 | 2.3040 | [+2.2493, +2.3595] |
| 6 | False | 2163.2293 | 2168.8997 | 716 | 65 | 716 | 65 | True | 2.5853 | 1.7090 | 0.8762 | [+0.6916, +1.0451] |
| 7 | False | 2168.8997 | 2793.2544 | 717 | 1160 | 714 | 1024 | True | 2.8403 | 1.2994 | 1.5409 | [+1.5007, +1.5822] |
| 8 | False | 2793.2544 | 2989.1259 | 717 | 998 | 717 | 993 | True | 2.7726 | 2.1741 | 0.5985 | [+0.5688, +0.6286] |
| 9 | False | 2989.1259 | 3000.6138 | 717 | 842 | 717 | 842 | True | 2.5903 | 2.2467 | 0.3436 | [+0.3227, +0.3634] |
| 10 | True | 3000.6138 | inf | 0 | 1 | 0 | 1 | False |  |  |  |  |
Local slopes (difference quotients): 1->2: 9.049e-04; 2->3: 2.597e-03; 3->4: 9.545e-04; 4->5: -5.379e-05; 5->6: 1.066e-04; 6->7: -1.291e-04

`union/E/D_unif/tau0.1/uniform/excl/k6/ctl-none`: edges from the loop's sigma column: 5.1, 5.8, 148.6, 865.0, 868.5, 1396.2, 2094.8, 2099.9, 2725.3, 3035.0, 3047.7; union slope 9.536e-04 [+9.401e-04, +9.679e-04] (intercept +0.3201 [+0.3115, +0.3293]); control slope 8.171e-04 [+8.008e-04, +8.343e-04]
| bin | overflow | edge_low | edge_high | n_points_union | n_points_control | n_sequences_union | n_sequences_control | populated | union_mean_excess | control_mean_excess | difference | interval |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 0 | False | 5.0935 | 5.7915 | 717 | 0 | 717 | 0 | False | 0.0033 |  |  |  |
| 1 | False | 5.7915 | 148.5948 | 717 | 1024 | 575 | 1024 | True | 0.0894 | 0.0001 | 0.0893 | [+0.0839, +0.0947] |
| 2 | False | 148.5948 | 864.9577 | 717 | 1024 | 679 | 1024 | True | 0.4248 | 0.0135 | 0.4113 | [+0.3606, +0.4653] |
| 3 | False | 864.9577 | 868.4907 | 716 | 0 | 716 | 0 | False | 1.3533 |  |  |  |
| 4 | False | 868.4907 | 1396.1732 | 717 | 1024 | 693 | 1024 | True | 1.9223 | 0.1397 | 1.7825 | [+1.7280, +1.8395] |
| 5 | False | 1396.1732 | 2094.8290 | 717 | 1027 | 697 | 1024 | True | 2.5288 | 0.4654 | 2.0634 | [+2.0199, +2.1091] |
| 6 | False | 2094.8290 | 2099.9218 | 716 | 114 | 716 | 114 | True | 2.6491 | 1.7232 | 0.9259 | [+0.8052, +1.0353] |
| 7 | False | 2099.9218 | 2725.2858 | 717 | 1118 | 717 | 1021 | True | 2.8848 | 1.3835 | 1.5013 | [+1.4631, +1.5407] |
| 8 | False | 2725.2858 | 3035.0131 | 717 | 1041 | 717 | 1017 | True | 2.7911 | 2.1069 | 0.6842 | [+0.6525, +0.7172] |
| 9 | False | 3035.0131 | 3047.6636 | 717 | 795 | 717 | 795 | True | 2.5544 | 2.3948 | 0.1597 | [+0.1386, +0.1791] |
| 10 | True | 3047.6636 | inf | 0 | 1 | 0 | 1 | False |  |  |  |  |
Local slopes (difference quotients): 1->2: 9.916e-04; 2->3: 1.719e-03; 3->4: 1.684e-03; 4->5: 7.001e-04; 5->6: 2.595e-05; 6->7: -2.392e-04

`union/E/D_unif/tau0.1/uniform/excl/k7/ctl-none`: edges from the loop's sigma column: 13.4, 14.7, 163.9, 862.8, 866.2, 1277.4, 1977.8, 1983.4, 2695.2, 3005.1, 3016.5; union slope 8.941e-04 [+8.820e-04, +9.068e-04] (intercept +0.4796 [+0.4647, +0.4953]); control slope 8.265e-04 [+8.104e-04, +8.432e-04]
| bin | overflow | edge_low | edge_high | n_points_union | n_points_control | n_sequences_union | n_sequences_control | populated | union_mean_excess | control_mean_excess | difference | interval |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 0 | False | 13.4495 | 14.7366 | 717 | 0 | 717 | 0 | False | 0.0191 |  |  |  |
| 1 | False | 14.7366 | 163.9013 | 717 | 1024 | 621 | 1024 | True | 0.2571 | 0.0001 | 0.2570 | [+0.2386, +0.2763] |
| 2 | False | 163.9013 | 862.7863 | 717 | 1024 | 712 | 1024 | True | 0.5689 | 0.0045 | 0.5644 | [+0.5016, +0.6331] |
| 3 | False | 862.7863 | 866.2168 | 716 | 0 | 716 | 0 | False | 1.7450 |  |  |  |
| 4 | False | 866.2168 | 1277.4469 | 717 | 1024 | 676 | 1024 | True | 1.9542 | 0.1622 | 1.7920 | [+1.7436, +1.8425] |
| 5 | False | 1277.4469 | 1977.8164 | 717 | 1029 | 703 | 1024 | True | 2.3649 | 0.3237 | 2.0411 | [+1.9860, +2.0998] |
| 6 | False | 1977.8164 | 1983.3914 | 716 | 122 | 716 | 122 | True | 2.4704 | 1.4337 | 1.0367 | [+0.9219, +1.1439] |
| 7 | False | 1983.3914 | 2695.2349 | 717 | 1044 | 714 | 1010 | True | 2.8145 | 1.1653 | 1.6492 | [+1.6090, +1.6910] |
| 8 | False | 2695.2349 | 3005.0771 | 717 | 1066 | 717 | 1021 | True | 2.8010 | 2.2058 | 0.5951 | [+0.5658, +0.6244] |
| 9 | False | 3005.0771 | 3016.5278 | 717 | 834 | 717 | 834 | True | 2.5782 | 2.2629 | 0.3153 | [+0.2996, +0.3305] |
| 10 | True | 3016.5278 | inf | 0 | 1 | 0 | 1 | False |  |  |  |  |
Local slopes (difference quotients): 1->2: 1.998e-03; 2->3: 2.107e-03; 3->4: 8.318e-04; 4->5: 5.911e-04; 5->6: 3.245e-04; 6->7: -2.173e-04

`union/E/D_unif/tau0/r0/excl/ctl-none`: edges from the loop's sigma column: 10.3, 75.3, 380.4, 642.6, 2007.2, 3253.1, 5528.8, 6254.4, 9400.2, 16190.1, 16614.5; union slope 3.079e-05 [+2.829e-05, +3.336e-05] (intercept +1.0473 [+0.9728, +1.1191]); control slope 1.200e-04 [+1.159e-04, +1.241e-04]
| bin | overflow | edge_low | edge_high | n_points_union | n_points_control | n_sequences_union | n_sequences_control | populated | union_mean_excess | control_mean_excess | difference | interval |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 0 | False | 10.2987 | 75.3231 | 5735 | 4096 | 1024 | 1024 | True | -0.5972 | -0.1063 | -0.4909 | [-0.5226, -0.4606] |
| 1 | False | 75.3231 | 380.3614 | 5734 | 6144 | 1024 | 1024 | True | -0.1007 | -0.4978 | 0.3971 | [+0.3340, +0.4561] |
| 2 | False | 380.3614 | 642.5535 | 5734 | 6144 | 1024 | 1024 | True | 0.5567 | -1.0431 | 1.5997 | [+1.5645, +1.6349] |
| 3 | False | 642.5535 | 2007.1730 | 5735 | 5235 | 1024 | 1024 | True | 0.7563 | -1.1987 | 1.9550 | [+1.9287, +1.9805] |
| 4 | False | 2007.1730 | 3253.0703 | 5734 | 7053 | 1024 | 1024 | True | 1.9652 | -0.3908 | 2.3560 | [+2.3345, +2.3773] |
| 5 | False | 3253.0703 | 5528.7848 | 5734 | 5410 | 1024 | 1024 | True | 2.6268 | 1.0315 | 1.5953 | [+1.5749, +1.6162] |
| 6 | False | 5528.7848 | 6254.3864 | 5735 | 6040 | 1024 | 1024 | True | 2.6603 | 1.9068 | 0.7535 | [+0.7348, +0.7727] |
| 7 | False | 6254.3864 | 9400.2160 | 5734 | 5757 | 1024 | 1024 | True | 2.5683 | 2.4607 | 0.1076 | [+0.1012, +0.1139] |
| 8 | False | 9400.2160 | 16190.0922 | 5734 | 5732 | 1024 | 1024 | True | 1.5175 | 1.6525 | -0.1350 | [-0.1433, -0.1263] |
| 9 | False | 16190.0922 | 16614.5078 | 5735 | 5733 | 1024 | 1024 | True | 0.1408 | 0.3775 | -0.2367 | [-0.2511, -0.2227] |
| 10 | True | 16614.5078 | inf | 0 | 0 | 0 | 0 | False |  |  |  |  |
Local slopes (difference quotients): 1->2: 2.844e-03; 2->3: 2.654e-04; 3->4: 1.758e-03; 4->5: 1.911e-05; 5->6: -2.401e-05; 6->7: -3.530e-04

## 4. Curve 2: the union under the uniform background (draw 0 shown; every draw in the CSVs)
Chain `union/E/D_unif/tau0.1/uniform/excl/k0/ctl-none`; rung 0 mean 0.2772; m = 8 rungs compared; **label: fails** (at m = 8: fails); j_det = 1, j_mat = 1, first repair rung = None; per draw: k0: det 1, mat 1

| rung | n_on | mean_sigma | overlap | mean_kl | excess | interval | half_width | two_level | draws_positive | fraction_seq_above_X | detected | material | repair | differs_at_m_8 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 83.0000 | 36.8830 | 0.0163 | 0.3453 | 0.0682 | [+0.0640, +0.0726] | 0.0043 | [+0.0640, +0.0726] | 1/1 | 0.6318 | True | True | False | False |
| 2 | 441.0000 | 210.7227 | 0.0849 | 0.5387 | 0.2616 | [+0.2543, +0.2693] | 0.0075 | [+0.2543, +0.2693] | 1/1 | 1.0000 | True | True | False | False |
| 3 | 1855.0000 | 909.2083 | 0.3276 | 2.1287 | 1.8516 | [+1.8004, +1.9045] | 0.0521 | [+1.8004, +1.9045] | 1/1 | 1.0000 | True | True | False | False |
| 4 | 3605.0000 | 1780.8005 | 0.4136 | 3.0817 | 2.8045 | [+2.7375, +2.8777] | 0.0701 | [+2.7375, +2.8777] | 1/1 | 1.0000 | True | True | False | False |
| 5 | 4700.0000 | 2326.6990 | 0.7093 | 3.0424 | 2.7652 | [+2.7047, +2.8304] | 0.0628 | [+2.7047, +2.8304] | 1/1 | 1.0000 | True | True | False | False |
| 6 | 5644.0000 | 2798.2407 | 0.8747 | 3.0226 | 2.7455 | [+2.6879, +2.8066] | 0.0593 | [+2.6879, +2.8066] | 1/1 | 1.0000 | True | True | False | False |
| 7 | 6104.0000 | 3028.1614 | 0.9542 | 2.9770 | 2.6998 | [+2.6429, +2.7611] | 0.0591 | [+2.6429, +2.7611] | 1/1 | 1.0000 | True | True | False | False |
| 8 | 6361.0000 | 3156.6619 | 0.9983 | 2.9388 | 2.6617 | [+2.6046, +2.7233] | 0.0593 | [+2.6046, +2.7233] | 1/1 | 1.0000 | True | True | False | False |

Paired union minus control on the same sequence, draw, and rung (95 percent uncorrected), with the pre-reads' overlap of the two sets: rung 1: +0.0672 [+0.0641, +0.0703] (overlap 0.016); rung 2: +0.2509 [+0.2457, +0.2563] (overlap 0.085); rung 3: +1.7137 [+1.6797, +1.7488] (overlap 0.328); rung 4: +2.1435 [+2.1091, +2.1794] (overlap 0.414)
Rung 4 minus rung 3 at nearly the same count (diffuse against concentrated), paired: +0.9529 [+0.9308, +0.9769].
Rung 4 (one donor sequence): excess +2.8045 [+2.7375, +2.8777], fraction of sequences with excess above X 1.000.
Per-rung excess by reader label on E (each label's own resample, the curve's m):
| label | n | rung | excess | interval | half_width | detected | material |
|---|---|---|---|---|---|---|---|
| code | 120 | 1 | 0.0322 | [+0.0271, +0.0383] | 0.0056 | True | False |
| code | 120 | 2 | 0.3179 | [+0.2878, +0.3513] | 0.0317 | True | True |
| code | 120 | 3 | 2.5147 | [+2.3256, +2.7138] | 0.1941 | True | True |
| code | 120 | 4 | 4.0509 | [+3.8293, +4.2904] | 0.2305 | True | True |
| code | 120 | 5 | 3.9328 | [+3.7341, +4.1506] | 0.2083 | True | True |
| code | 120 | 6 | 3.8194 | [+3.6278, +4.0228] | 0.1975 | True | True |
| code | 120 | 7 | 3.7847 | [+3.5940, +3.9848] | 0.1954 | True | True |
| code | 120 | 8 | 3.7517 | [+3.5611, +3.9521] | 0.1955 | True | True |
| mixed | 27 | 1 | 0.0521 | [+0.0445, +0.0605] | 0.0080 | True | False |
| mixed | 27 | 2 | 0.2687 | [+0.2465, +0.2911] | 0.0223 | True | True |
| mixed | 27 | 3 | 1.9339 | [+1.7588, +2.1336] | 0.1874 | True | True |
| mixed | 27 | 4 | 3.1054 | [+2.8853, +3.3432] | 0.2290 | True | True |
| mixed | 27 | 5 | 3.0053 | [+2.8006, +3.2257] | 0.2125 | True | True |
| mixed | 27 | 6 | 2.9543 | [+2.7556, +3.1741] | 0.2092 | True | True |
| mixed | 27 | 7 | 2.9168 | [+2.7203, +3.1337] | 0.2067 | True | True |
| mixed | 27 | 8 | 2.8813 | [+2.6851, +3.0978] | 0.2064 | True | True |
| other | 158 | 1 | 0.0302 | [+0.0251, +0.0361] | 0.0055 | True | False |
| other | 158 | 2 | 0.2541 | [+0.2318, +0.2797] | 0.0239 | True | True |
| other | 158 | 3 | 1.8327 | [+1.6584, +2.0244] | 0.1830 | True | True |
| other | 158 | 4 | 2.9401 | [+2.7556, +3.1427] | 0.1936 | True | True |
| other | 158 | 5 | 2.9411 | [+2.7790, +3.1187] | 0.1698 | True | True |
| other | 158 | 6 | 2.8778 | [+2.7191, +3.0472] | 0.1641 | True | True |
| other | 158 | 7 | 2.8146 | [+2.6612, +2.9793] | 0.1591 | True | True |
| other | 158 | 8 | 2.7697 | [+2.6161, +2.9354] | 0.1597 | True | True |
| prose | 719 | 1 | 0.0831 | [+0.0782, +0.0883] | 0.0050 | True | True |
| prose | 719 | 2 | 0.2535 | [+0.2468, +0.2607] | 0.0070 | True | True |
| prose | 719 | 3 | 1.7419 | [+1.7012, +1.7847] | 0.0418 | True | True |
| prose | 719 | 4 | 2.5554 | [+2.5053, +2.6090] | 0.0519 | True | True |
| prose | 719 | 5 | 2.5226 | [+2.4778, +2.5698] | 0.0460 | True | True |
| prose | 719 | 6 | 2.5293 | [+2.4861, +2.5756] | 0.0447 | True | True |
| prose | 719 | 7 | 2.4854 | [+2.4429, +2.5310] | 0.0440 | True | True |
| prose | 719 | 8 | 2.4478 | [+2.4055, +2.4929] | 0.0437 | True | True |

Paired union minus control by reader label at rungs 1 to 4 and 5a (each label's own resample, uncorrected 95 percent), the control's per-label excess beside:
| label | n | rung | union_minus_control | interval_uncorrected | half_width | control_excess | control_interval_uncorrected |
|---|---|---|---|---|---|---|---|
| code | 120 | 1 | 0.0309 | [+0.0273, +0.0350] | 0.0038 | 0.0012 | [+0.0008, +0.0017] |
| code | 120 | 2 | 0.3029 | [+0.2815, +0.3267] | 0.0226 | 0.0150 | [+0.0135, +0.0166] |
| code | 120 | 3 | 2.3237 | [+2.1940, +2.4584] | 0.1322 | 0.1910 | [+0.1767, +0.2065] |
| code | 120 | 4 | 2.9717 | [+2.8555, +3.0913] | 0.1179 | 1.0792 | [+0.9890, +1.1756] |
| mixed | 27 | 1 | 0.0517 | [+0.0462, +0.0575] | 0.0056 | 0.0004 | [-0.0005, +0.0013] |
| mixed | 27 | 2 | 0.2579 | [+0.2424, +0.2739] | 0.0157 | 0.0108 | [+0.0085, +0.0136] |
| mixed | 27 | 3 | 1.7851 | [+1.6637, +1.9158] | 0.1261 | 0.1488 | [+0.1353, +0.1643] |
| mixed | 27 | 4 | 2.3962 | [+2.2657, +2.5374] | 0.1358 | 0.7092 | [+0.6487, +0.7738] |
| other | 158 | 1 | 0.0286 | [+0.0250, +0.0324] | 0.0037 | 0.0016 | [+0.0011, +0.0022] |
| other | 158 | 2 | 0.2391 | [+0.2227, +0.2570] | 0.0171 | 0.0150 | [+0.0136, +0.0165] |
| other | 158 | 3 | 1.6744 | [+1.5550, +1.8045] | 0.1248 | 0.1584 | [+0.1471, +0.1712] |
| other | 158 | 4 | 2.1468 | [+2.0486, +2.2493] | 0.1004 | 0.7933 | [+0.7381, +0.8547] |
| prose | 719 | 1 | 0.0823 | [+0.0786, +0.0861] | 0.0037 | 0.0008 | [+0.0006, +0.0010] |
| prose | 719 | 2 | 0.2445 | [+0.2394, +0.2496] | 0.0051 | 0.0091 | [+0.0086, +0.0095] |
| prose | 719 | 3 | 1.6178 | [+1.5893, +1.6465] | 0.0286 | 0.1241 | [+0.1218, +0.1264] |
| prose | 719 | 4 | 1.9950 | [+1.9667, +2.0243] | 0.0288 | 0.5604 | [+0.5478, +0.5726] |

- draw 1: label fails, j_det 1, j_mat 2, rung 8 2.9383 (rung 0 0.2774)
- draw 2: label fails, j_det 1, j_mat 2, rung 8 2.9400 (rung 0 0.2769)
- draw 3: label fails, j_det 1, j_mat 2, rung 8 2.9400 (rung 0 0.2769)
- draw 4: label fails, j_det 1, j_mat 2, rung 8 2.9394 (rung 0 0.2771)
- draw 5: label fails, j_det 1, j_mat 2, rung 8 2.9383 (rung 0 0.2770)
- draw 6: label fails, j_det 1, j_mat 2, rung 8 2.9389 (rung 0 0.2769)
- draw 7: label fails, j_det 1, j_mat 2, rung 8 2.9390 (rung 0 0.2771)

The two-by-two completed (means over E with sequence standard errors): unmasked: 0.0114 (se 0.0002); importances: 4.6920 (se 0.0569); fourth_cell: 10.0093 (se 0.0216); curve_1_rung_8: 7.3079 (se 0.0224); curve_2_rung_8: 2.9391 (se 0.0075); curve 2 rung 8 per draw [2.9388, 2.9383, 2.94, 2.94, 2.9394, 2.9383, 2.9389, 2.939] against stochastic rung 0 per draw [0.2772, 0.2774, 0.2769, 0.2769, 0.2771, 0.277, 0.2769, 0.2771]
fourth_cell, paired per sequence: minus importances-as-masks +5.3173 (se 0.0601); minus unmasked +9.9979 (se 0.0216).
Curve 2's rung 8 over curve 1's per sequence (paired; the mean over draws of curve 2 divided by curve 1): quantiles 0/10/25/50/75/90/100 = [0.225, 0.323, 0.358, 0.395, 0.435, 0.476, 0.791], mean 0.400, fraction below 0.5 0.929, above 0.9 0.000 (n 1024): whether saturation is uniform across sequences or a mixture.

## 5. The hard-zero chains: testability, positive controls, budgets (both tau_q)
| chain | part | stratum | positive_control | verdict_read | testable_rungs_at_0.1 | budget_at_0.1 | budget_at_0 |
|---|---|---|---|---|---|---|---|
| hard_zero/E/D_unif/tau0.1/ones/incl/ctl-none | donor_chain | all | pass | True | none |  |  |
| hard_zero/E/D_unif/tau0.1/ones/incl/ctl-plain | donor_chain | all | n/a | True | none |  |  |
| never_named_hard/E/D_unif/tau0.1/ones/incl/ctl-none | donor_chain | all | n/a | True | 1, 2, 3, 4, 5, 6, 7, B50, B75 | 2 | 2 |
| never_named_hard/E/D_unif/tau0.1/ones/incl/ctl-none | rung 8 alone (one-cell rule) | all | n/a | True | 8 | fails | not testable with these donors |
| never_named_hard/E/D_unif/tau0.1/ones/excl/ctl-none | rung 8 alone (one-cell rule) | all | n/a | True | 8 | fails | not testable with these donors |
| never_named_hard/E/D_unif/tau0/ones/incl/ctl-none | rung 8 alone (one-cell rule) | all | n/a | True | 8 | fails | fails |
| hard_zero/E_lab/D_code/tau0.1/ones/incl/ctl-none | donor_chain | other | pass | True | none |  |  |
| code_specific_hard/E_lab/D_code/tau0.1/ones/incl/ctl-none | donor_chain | other | pass | True | 1, 2, 3, 4, 5, 6, 7 | 7 | 7 |
| code_specific_hard/E_lab/D_code/tau0.1/ones/incl/ctl-none | sub_rung_chain | other | pass | True | S4, S16, S64 | S64 | S64 |
| hard_zero/E_lab/D_code/tau0.1/ones/incl/ctl-plain | donor_chain | other | n/a | True | none |  |  |
| code_specific_hard/E_lab/D_code/tau0.1/ones/incl/ctl-complement | donor_chain | other | n/a | True | 1, 2, 3, 4, 5, 6, 7 | 7 | 7 |
| code_specific_hard/E_lab/D_code/tau0.1/ones/incl/ctl-complement | sub_rung_chain | other | n/a | True | S4, S16, S64 | S64 | S64 |
| code_specific_hard/E_lab/D_code/tau0.1/ones/incl/ctl-plain | donor_chain | other | n/a | True | 1, 2, 3, 4 | 4 | 4 |
| code_specific_hard/E_lab/D_code/tau0.1/ones/incl/ctl-plain | sub_rung_chain | other | n/a | True | S4 | S4 | S4 |

### `hard_zero/E_lab/D_code/tau0.1/ones/incl/ctl-none` (curve 3)
Positive control: erase exceeds its plain control on Github: pass (5 rungs judged); readability floor equals the pre-reads' table: True (98 of 98 rows matched)
The erased set against its plain control per rung (mean over draws; the control's pool is the alive set): rung 1: overlap 2 of 63 erased (0.020; control 63 from a pool of 6355, of which 63 are the erased set's own); rung 2: overlap 26 of 316 erased (0.081; control 316 from a pool of 6355, of which 316 are the erased set's own); rung 3: overlap 395 of 1445 erased (0.272; control 1445 from a pool of 6355, of which 1445 are the erased set's own); rung 4: overlap 1101 of 2508 erased (0.425; control 2508 from a pool of 6355, of which 2508 are the erased set's own); rung 5: overlap 2556 of 3972 erased (0.640; control 3972 from a pool of 6355, of which 3972 are the erased set's own); rung 6: overlap 4118 of 5081 erased (0.810; control 5081 from a pool of 6355, of which 5081 are the erased set's own); rung 7: overlap 4885 of 5550 erased (0.880; control 5550 from a pool of 6355, of which 5550 are the erased set's own); rung 8: overlap 5431 of 5864 erased (0.926; control 5864 from a pool of 6355, of which 5863 are the erased set's own)
tau_q = 0.1, stratum all, donor_chain (m = 7): budget rung None
| rung | n_off | mean_contributing | clean_prefix_fraction | testable | label | d_hat | interval | half_width | draws_above_X | unconditional |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 63.0000 | 0.0000 | 0.0000 | False | not testable with these donors | None | None | None | None | 6.0232 |
| 2 | 316.5000 | 0.0000 | 0.0000 | False | not testable with these donors | None | None | None | None | 7.3513 |
| 3 | 1444.7500 | 0.0000 | 0.0000 | False | not testable with these donors | None | None | None | None | 8.5906 |
| 4 | 2508.5000 | 0.0000 | 0.0000 | False | not testable with these donors | None | None | None | None | 9.7867 |
| 5 | 3971.6250 | 0.0000 | 0.0000 | False | not testable with these donors | None | None | None | None | 10.4386 |
| 6 | 5081.0000 | 0.0000 | 0.0000 | False | not testable with these donors | None | None | None | None | 10.9471 |
| 7 | 5550.5000 | 0.0000 | 0.0000 | False | not testable with these donors | None | None | None | None | 11.0184 |

tau_q = 0.1, stratum Github, donor_chain (m = 7): budget rung None
| rung | n_off | mean_contributing | clean_prefix_fraction | testable | label | d_hat | interval | half_width | draws_above_X | unconditional |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 63.0000 | 0.0000 | 0.0000 | False | not testable with these donors | None | None | None | None | 6.5508 |
| 2 | 316.5000 | 0.0000 | 0.0000 | False | not testable with these donors | None | None | None | None | 7.9854 |
| 3 | 1444.7500 | 0.0000 | 0.0000 | False | not testable with these donors | None | None | None | None | 8.8307 |
| 4 | 2508.5000 | 0.0000 | 0.0000 | False | not testable with these donors | None | None | None | None | 10.3561 |
| 5 | 3971.6250 | 0.0000 | 0.0000 | False | not testable with these donors | None | None | None | None | 11.1749 |
| 6 | 5081.0000 | 0.0000 | 0.0000 | False | not testable with these donors | None | None | None | None | 11.7354 |
| 7 | 5550.5000 | 0.0000 | 0.0000 | False | not testable with these donors | None | None | None | None | 11.8202 |

tau_q = 0.1, stratum other, donor_chain (m = 7): budget rung None
| rung | n_off | mean_contributing | clean_prefix_fraction | testable | label | d_hat | interval | half_width | draws_above_X | unconditional |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 63.0000 | 0.0000 | 0.0000 | False | not testable with these donors | None | None | None | None | 5.4955 |
| 2 | 316.5000 | 0.0000 | 0.0000 | False | not testable with these donors | None | None | None | None | 6.7172 |
| 3 | 1444.7500 | 0.0000 | 0.0000 | False | not testable with these donors | None | None | None | None | 8.3506 |
| 4 | 2508.5000 | 0.0000 | 0.0000 | False | not testable with these donors | None | None | None | None | 9.2173 |
| 5 | 3971.6250 | 0.0000 | 0.0000 | False | not testable with these donors | None | None | None | None | 9.7023 |
| 6 | 5081.0000 | 0.0000 | 0.0000 | False | not testable with these donors | None | None | None | None | 10.1587 |
| 7 | 5550.5000 | 0.0000 | 0.0000 | False | not testable with these donors | None | None | None | None | 10.2166 |

tau_q = 0.1, stratum ArXiv, donor_chain (m = 7): budget rung None
| rung | n_off | mean_contributing | clean_prefix_fraction | testable | label | d_hat | interval | half_width | draws_above_X | unconditional |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 63.0000 | 0.0000 | 0.0000 | False | not testable with these donors | None | None | None | None | 5.6282 |
| 2 | 316.5000 | 0.0000 | 0.0000 | False | not testable with these donors | None | None | None | None | 6.8532 |
| 3 | 1444.7500 | 0.0000 | 0.0000 | False | not testable with these donors | None | None | None | None | 8.9362 |
| 4 | 2508.5000 | 0.0000 | 0.0000 | False | not testable with these donors | None | None | None | None | 9.7921 |
| 5 | 3971.6250 | 0.0000 | 0.0000 | False | not testable with these donors | None | None | None | None | 10.3606 |
| 6 | 5081.0000 | 0.0000 | 0.0000 | False | not testable with these donors | None | None | None | None | 10.8727 |
| 7 | 5550.5000 | 0.0000 | 0.0000 | False | not testable with these donors | None | None | None | None | 11.0445 |

tau_q = 0.1, stratum Pile-CC, donor_chain (m = 7): budget rung None
| rung | n_off | mean_contributing | clean_prefix_fraction | testable | label | d_hat | interval | half_width | draws_above_X | unconditional |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 63.0000 | 0.0000 | 0.0000 | False | not testable with these donors | None | None | None | None | 4.9374 |
| 2 | 316.5000 | 0.0000 | 0.0000 | False | not testable with these donors | None | None | None | None | 6.0276 |
| 3 | 1444.7500 | 0.0000 | 0.0000 | False | not testable with these donors | None | None | None | None | 7.8852 |
| 4 | 2508.5000 | 0.0000 | 0.0000 | False | not testable with these donors | None | None | None | None | 8.5503 |
| 5 | 3971.6250 | 0.0000 | 0.0000 | False | not testable with these donors | None | None | None | None | 8.9479 |
| 6 | 5081.0000 | 0.0000 | 0.0000 | False | not testable with these donors | None | None | None | None | 9.3566 |
| 7 | 5550.5000 | 0.0000 | 0.0000 | False | not testable with these donors | None | None | None | None | 9.3504 |

tau_q = 0.1, stratum StackExchange, donor_chain (m = 7): budget rung None
| rung | n_off | mean_contributing | clean_prefix_fraction | testable | label | d_hat | interval | half_width | draws_above_X | unconditional |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 63.0000 | 0.0000 | 0.0000 | False | not testable with these donors | None | None | None | None | 5.9441 |
| 2 | 316.5000 | 0.0000 | 0.0000 | False | not testable with these donors | None | None | None | None | 7.2252 |
| 3 | 1444.7500 | 0.0000 | 0.0000 | False | not testable with these donors | None | None | None | None | 8.3684 |
| 4 | 2508.5000 | 0.0000 | 0.0000 | False | not testable with these donors | None | None | None | None | 9.6348 |
| 5 | 3971.6250 | 0.0000 | 0.0000 | False | not testable with these donors | None | None | None | None | 10.1143 |
| 6 | 5081.0000 | 0.0000 | 0.0000 | False | not testable with these donors | None | None | None | None | 10.5463 |
| 7 | 5550.5000 | 0.0000 | 0.0000 | False | not testable with these donors | None | None | None | None | 10.5770 |

tau_q = 0.1, stratum Wikipedia (en), donor_chain (m = 7): budget rung None
| rung | n_off | mean_contributing | clean_prefix_fraction | testable | label | d_hat | interval | half_width | draws_above_X | unconditional |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 63.0000 | 0.0000 | 0.0000 | False | not testable with these donors | None | None | None | None | 5.4725 |
| 2 | 316.5000 | 0.0000 | 0.0000 | False | not testable with these donors | None | None | None | None | 6.7630 |
| 3 | 1444.7500 | 0.0000 | 0.0000 | False | not testable with these donors | None | None | None | None | 8.2125 |
| 4 | 2508.5000 | 0.0000 | 0.0000 | False | not testable with these donors | None | None | None | None | 8.8920 |
| 5 | 3971.6250 | 0.0000 | 0.0000 | False | not testable with these donors | None | None | None | None | 9.3866 |
| 6 | 5081.0000 | 0.0000 | 0.0000 | False | not testable with these donors | None | None | None | None | 9.8592 |
| 7 | 5550.5000 | 0.0000 | 0.0000 | False | not testable with these donors | None | None | None | None | 9.8945 |

tau_q = 0, stratum all, donor_chain (m = 7): budget rung None
| rung | n_off | mean_contributing | clean_prefix_fraction | testable | label | d_hat | interval | half_width | draws_above_X | unconditional |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 63.0000 | 0.0000 | 0.0000 | False | not testable with these donors | None | None | None | None | 6.0232 |
| 2 | 316.5000 | 0.0000 | 0.0000 | False | not testable with these donors | None | None | None | None | 7.3513 |
| 3 | 1444.7500 | 0.0000 | 0.0000 | False | not testable with these donors | None | None | None | None | 8.5906 |
| 4 | 2508.5000 | 0.0000 | 0.0000 | False | not testable with these donors | None | None | None | None | 9.7867 |
| 5 | 3971.6250 | 0.0000 | 0.0000 | False | not testable with these donors | None | None | None | None | 10.4386 |
| 6 | 5081.0000 | 0.0000 | 0.0000 | False | not testable with these donors | None | None | None | None | 10.9471 |
| 7 | 5550.5000 | 0.0000 | 0.0000 | False | not testable with these donors | None | None | None | None | 11.0184 |

tau_q = 0, stratum Github, donor_chain (m = 7): budget rung None
| rung | n_off | mean_contributing | clean_prefix_fraction | testable | label | d_hat | interval | half_width | draws_above_X | unconditional |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 63.0000 | 0.0000 | 0.0000 | False | not testable with these donors | None | None | None | None | 6.5508 |
| 2 | 316.5000 | 0.0000 | 0.0000 | False | not testable with these donors | None | None | None | None | 7.9854 |
| 3 | 1444.7500 | 0.0000 | 0.0000 | False | not testable with these donors | None | None | None | None | 8.8307 |
| 4 | 2508.5000 | 0.0000 | 0.0000 | False | not testable with these donors | None | None | None | None | 10.3561 |
| 5 | 3971.6250 | 0.0000 | 0.0000 | False | not testable with these donors | None | None | None | None | 11.1749 |
| 6 | 5081.0000 | 0.0000 | 0.0000 | False | not testable with these donors | None | None | None | None | 11.7354 |
| 7 | 5550.5000 | 0.0000 | 0.0000 | False | not testable with these donors | None | None | None | None | 11.8202 |

tau_q = 0, stratum other, donor_chain (m = 7): budget rung None
| rung | n_off | mean_contributing | clean_prefix_fraction | testable | label | d_hat | interval | half_width | draws_above_X | unconditional |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 63.0000 | 0.0000 | 0.0000 | False | not testable with these donors | None | None | None | None | 5.4955 |
| 2 | 316.5000 | 0.0000 | 0.0000 | False | not testable with these donors | None | None | None | None | 6.7172 |
| 3 | 1444.7500 | 0.0000 | 0.0000 | False | not testable with these donors | None | None | None | None | 8.3506 |
| 4 | 2508.5000 | 0.0000 | 0.0000 | False | not testable with these donors | None | None | None | None | 9.2173 |
| 5 | 3971.6250 | 0.0000 | 0.0000 | False | not testable with these donors | None | None | None | None | 9.7023 |
| 6 | 5081.0000 | 0.0000 | 0.0000 | False | not testable with these donors | None | None | None | None | 10.1587 |
| 7 | 5550.5000 | 0.0000 | 0.0000 | False | not testable with these donors | None | None | None | None | 10.2166 |

tau_q = 0, stratum ArXiv, donor_chain (m = 7): budget rung None
| rung | n_off | mean_contributing | clean_prefix_fraction | testable | label | d_hat | interval | half_width | draws_above_X | unconditional |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 63.0000 | 0.0000 | 0.0000 | False | not testable with these donors | None | None | None | None | 5.6282 |
| 2 | 316.5000 | 0.0000 | 0.0000 | False | not testable with these donors | None | None | None | None | 6.8532 |
| 3 | 1444.7500 | 0.0000 | 0.0000 | False | not testable with these donors | None | None | None | None | 8.9362 |
| 4 | 2508.5000 | 0.0000 | 0.0000 | False | not testable with these donors | None | None | None | None | 9.7921 |
| 5 | 3971.6250 | 0.0000 | 0.0000 | False | not testable with these donors | None | None | None | None | 10.3606 |
| 6 | 5081.0000 | 0.0000 | 0.0000 | False | not testable with these donors | None | None | None | None | 10.8727 |
| 7 | 5550.5000 | 0.0000 | 0.0000 | False | not testable with these donors | None | None | None | None | 11.0445 |

tau_q = 0, stratum Pile-CC, donor_chain (m = 7): budget rung None
| rung | n_off | mean_contributing | clean_prefix_fraction | testable | label | d_hat | interval | half_width | draws_above_X | unconditional |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 63.0000 | 0.0000 | 0.0000 | False | not testable with these donors | None | None | None | None | 4.9374 |
| 2 | 316.5000 | 0.0000 | 0.0000 | False | not testable with these donors | None | None | None | None | 6.0276 |
| 3 | 1444.7500 | 0.0000 | 0.0000 | False | not testable with these donors | None | None | None | None | 7.8852 |
| 4 | 2508.5000 | 0.0000 | 0.0000 | False | not testable with these donors | None | None | None | None | 8.5503 |
| 5 | 3971.6250 | 0.0000 | 0.0000 | False | not testable with these donors | None | None | None | None | 8.9479 |
| 6 | 5081.0000 | 0.0000 | 0.0000 | False | not testable with these donors | None | None | None | None | 9.3566 |
| 7 | 5550.5000 | 0.0000 | 0.0000 | False | not testable with these donors | None | None | None | None | 9.3504 |

tau_q = 0, stratum StackExchange, donor_chain (m = 7): budget rung None
| rung | n_off | mean_contributing | clean_prefix_fraction | testable | label | d_hat | interval | half_width | draws_above_X | unconditional |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 63.0000 | 0.0000 | 0.0000 | False | not testable with these donors | None | None | None | None | 5.9441 |
| 2 | 316.5000 | 0.0000 | 0.0000 | False | not testable with these donors | None | None | None | None | 7.2252 |
| 3 | 1444.7500 | 0.0000 | 0.0000 | False | not testable with these donors | None | None | None | None | 8.3684 |
| 4 | 2508.5000 | 0.0000 | 0.0000 | False | not testable with these donors | None | None | None | None | 9.6348 |
| 5 | 3971.6250 | 0.0000 | 0.0000 | False | not testable with these donors | None | None | None | None | 10.1143 |
| 6 | 5081.0000 | 0.0000 | 0.0000 | False | not testable with these donors | None | None | None | None | 10.5463 |
| 7 | 5550.5000 | 0.0000 | 0.0000 | False | not testable with these donors | None | None | None | None | 10.5770 |

tau_q = 0, stratum Wikipedia (en), donor_chain (m = 7): budget rung None
| rung | n_off | mean_contributing | clean_prefix_fraction | testable | label | d_hat | interval | half_width | draws_above_X | unconditional |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 63.0000 | 0.0000 | 0.0000 | False | not testable with these donors | None | None | None | None | 5.4725 |
| 2 | 316.5000 | 0.0000 | 0.0000 | False | not testable with these donors | None | None | None | None | 6.7630 |
| 3 | 1444.7500 | 0.0000 | 0.0000 | False | not testable with these donors | None | None | None | None | 8.2125 |
| 4 | 2508.5000 | 0.0000 | 0.0000 | False | not testable with these donors | None | None | None | None | 8.8920 |
| 5 | 3971.6250 | 0.0000 | 0.0000 | False | not testable with these donors | None | None | None | None | 9.3866 |
| 6 | 5081.0000 | 0.0000 | 0.0000 | False | not testable with these donors | None | None | None | None | 9.8592 |
| 7 | 5550.5000 | 0.0000 | 0.0000 | False | not testable with these donors | None | None | None | None | 9.8945 |

### `code_specific_hard/E_lab/D_code/tau0.1/ones/incl/ctl-none` (curve 4)
Positive control: erase exceeds its complement control on Github: pass (8 rungs judged); readability floor equals the pre-reads' table: True (140 of 140 rows matched)
The erased set against its complement control per rung (mean over draws; the control's pool is alive minus prose-named at this tau): rung 1: overlap 0 of 0 erased (nan; control 0 from a pool of 535, of which 0 are the erased set's own); rung 2: overlap 0 of 0 erased (0.500; control 0 from a pool of 535, of which 0 are the erased set's own); rung 3: overlap 1 of 2 erased (0.244; control 2 from a pool of 535, of which 2 are the erased set's own); rung 4: overlap 0 of 6 erased (0.044; control 6 from a pool of 535, of which 6 are the erased set's own); rung 5: overlap 3 of 22 erased (0.157; control 22 from a pool of 535, of which 22 are the erased set's own); rung 6: overlap 11 of 61 erased (0.175; control 61 from a pool of 535, of which 61 are the erased set's own); rung 7: overlap 26 of 104 erased (0.244; control 104 from a pool of 535, of which 104 are the erased set's own); rung 8: overlap 77 of 201 erased (0.383; control 201 from a pool of 535, of which 200 are the erased set's own); rung S4: overlap 1 of 4 erased (0.250; control 4 from a pool of 535, of which 4 are the erased set's own); rung S16: overlap 3 of 16 erased (0.188; control 16 from a pool of 535, of which 16 are the erased set's own); rung S64: overlap 11 of 64 erased (0.172; control 64 from a pool of 535, of which 64 are the erased set's own)
tau_q = 0.1, stratum all, donor_chain (m = 7): budget rung 7
| rung | n_off | mean_contributing | clean_prefix_fraction | testable | label | d_hat | interval | half_width | draws_above_X | unconditional |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 0.0000 | 512.0000 | 1.0000 | True | holds | 0.0000 | [+0.0000, +0.0000] | 0.0000 | 0/8 | 0.0000 |
| 2 | 0.2500 | 510.2500 | 0.9280 | True | holds | 0.0001 | [+0.0001, +0.0001] | 0.0000 | 0/8 | 0.0015 |
| 3 | 2.5000 | 499.8750 | 0.7138 | True | holds | 0.0005 | [+0.0005, +0.0006] | 0.0001 | 0/8 | 0.0055 |
| 4 | 5.6250 | 491.2500 | 0.6961 | True | holds | 0.0009 | [+0.0008, +0.0010] | 0.0001 | 0/8 | 0.0060 |
| 5 | 21.7500 | 457.1250 | 0.5051 | True | holds | 0.0031 | [+0.0028, +0.0034] | 0.0003 | 0/8 | 0.0123 |
| 6 | 60.6250 | 414.6250 | 0.4056 | True | holds | 0.0072 | [+0.0066, +0.0079] | 0.0007 | 0/8 | 0.0224 |
| 7 | 104.5000 | 398.8750 | 0.3667 | True | holds | 0.0114 | [+0.0104, +0.0124] | 0.0010 | 0/8 | 0.0298 |

tau_q = 0.1, stratum all, sub_rung_chain (m = 3): budget rung S64
| rung | n_off | mean_contributing | clean_prefix_fraction | testable | label | d_hat | interval | half_width | draws_above_X | unconditional |
|---|---|---|---|---|---|---|---|---|---|---|
| S4 | 4.0000 | 487.0000 | 0.5958 | True | holds | 0.0008 | [+0.0007, +0.0009] | 0.0001 | 0/1 | 0.0074 |
| S16 | 16.0000 | 442.0000 | 0.5314 | True | holds | 0.0025 | [+0.0022, +0.0028] | 0.0003 | 0/1 | 0.0132 |
| S64 | 64.0000 | 413.0000 | 0.3856 | True | holds | 0.0077 | [+0.0071, +0.0084] | 0.0007 | 0/1 | 0.0253 |

tau_q = 0.1, stratum Github, donor_chain (m = 7): budget rung 7
| rung | n_off | mean_contributing | clean_prefix_fraction | testable | label | d_hat | interval | half_width | draws_above_X | unconditional |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 0.0000 | 256.0000 | 1.0000 | True | holds | 0.0000 | [+0.0000, +0.0000] | 0.0000 | 0/8 | 0.0000 |
| 2 | 0.2500 | 254.5000 | 0.8813 | True | holds | 0.0001 | [+0.0001, +0.0002] | 0.0000 | 0/8 | 0.0025 |
| 3 | 2.5000 | 245.1250 | 0.5205 | True | holds | 0.0009 | [+0.0007, +0.0010] | 0.0001 | 0/8 | 0.0091 |
| 4 | 5.6250 | 239.3750 | 0.5273 | True | holds | 0.0014 | [+0.0012, +0.0015] | 0.0002 | 0/8 | 0.0098 |
| 5 | 21.7500 | 210.0000 | 0.2821 | True | holds | 0.0046 | [+0.0041, +0.0051] | 0.0005 | 0/8 | 0.0193 |
| 6 | 60.6250 | 183.7500 | 0.2023 | True | holds | 0.0103 | [+0.0092, +0.0115] | 0.0012 | 0/8 | 0.0323 |
| 7 | 104.5000 | 176.5000 | 0.1601 | True | holds | 0.0157 | [+0.0140, +0.0177] | 0.0019 | 0/8 | 0.0392 |

tau_q = 0.1, stratum Github, sub_rung_chain (m = 3): budget rung S64
| rung | n_off | mean_contributing | clean_prefix_fraction | testable | label | d_hat | interval | half_width | draws_above_X | unconditional |
|---|---|---|---|---|---|---|---|---|---|---|
| S4 | 4.0000 | 234.0000 | 0.3254 | True | holds | 0.0013 | [+0.0011, +0.0015] | 0.0002 | 0/1 | 0.0123 |
| S16 | 16.0000 | 195.0000 | 0.2376 | True | holds | 0.0041 | [+0.0036, +0.0047] | 0.0005 | 0/1 | 0.0221 |
| S64 | 64.0000 | 179.0000 | 0.1663 | True | holds | 0.0111 | [+0.0099, +0.0125] | 0.0013 | 0/1 | 0.0350 |

tau_q = 0.1, stratum other, donor_chain (m = 7): budget rung 7
| rung | n_off | mean_contributing | clean_prefix_fraction | testable | label | d_hat | interval | half_width | draws_above_X | unconditional |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 0.0000 | 256.0000 | 1.0000 | True | holds | 0.0000 | [+0.0000, +0.0000] | 0.0000 | 0/8 | 0.0000 |
| 2 | 0.2500 | 255.7500 | 0.9748 | True | holds | 0.0000 | [+0.0000, +0.0001] | 0.0000 | 0/8 | 0.0006 |
| 3 | 2.5000 | 254.7500 | 0.9071 | True | holds | 0.0002 | [+0.0002, +0.0003] | 0.0001 | 0/8 | 0.0020 |
| 4 | 5.6250 | 251.8750 | 0.8648 | True | holds | 0.0005 | [+0.0005, +0.0006] | 0.0001 | 0/8 | 0.0021 |
| 5 | 21.7500 | 247.1250 | 0.7280 | True | holds | 0.0019 | [+0.0017, +0.0021] | 0.0002 | 0/8 | 0.0053 |
| 6 | 60.6250 | 230.8750 | 0.6089 | True | holds | 0.0048 | [+0.0045, +0.0052] | 0.0004 | 0/8 | 0.0124 |
| 7 | 104.5000 | 222.3750 | 0.5734 | True | holds | 0.0079 | [+0.0074, +0.0086] | 0.0006 | 0/8 | 0.0204 |

tau_q = 0.1, stratum other, sub_rung_chain (m = 3): budget rung S64
| rung | n_off | mean_contributing | clean_prefix_fraction | testable | label | d_hat | interval | half_width | draws_above_X | unconditional |
|---|---|---|---|---|---|---|---|---|---|---|
| S4 | 4.0000 | 253.0000 | 0.8661 | True | holds | 0.0004 | [+0.0003, +0.0005] | 0.0001 | 0/1 | 0.0025 |
| S16 | 16.0000 | 247.0000 | 0.8252 | True | holds | 0.0013 | [+0.0012, +0.0015] | 0.0001 | 0/1 | 0.0043 |
| S64 | 64.0000 | 234.0000 | 0.6049 | True | holds | 0.0051 | [+0.0048, +0.0055] | 0.0004 | 0/1 | 0.0157 |

tau_q = 0.1, stratum ArXiv, donor_chain (m = 7): budget rung 3
| rung | n_off | mean_contributing | clean_prefix_fraction | testable | label | d_hat | interval | half_width | draws_above_X | unconditional |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 0.0000 | 64.0000 | 1.0000 | True | holds | 0.0000 | [+0.0000, +0.0000] | 0.0000 | 0/8 | 0.0000 |
| 2 | 0.2500 | 64.0000 | 1.0000 | True | holds | 0.0000 | [+0.0000, +0.0000] | 0.0000 | 0/8 | 0.0000 |
| 3 | 2.5000 | 64.0000 | 0.9911 | True | holds | 0.0002 | [+0.0001, +0.0002] | 0.0000 | 0/8 | 0.0002 |
| 4 | 5.6250 | 62.1250 | 0.8103 | False | not testable with these donors |  |  |  |  | 0.0010 |
| 5 | 21.7500 | 61.2500 | 0.5533 | False | not testable with these donors |  |  |  |  | 0.0053 |
| 6 | 60.6250 | 50.8750 | 0.2433 | False | not testable with these donors |  |  |  |  | 0.0212 |
| 7 | 104.5000 | 45.1250 | 0.1275 | False | not testable with these donors |  |  |  |  | 0.0420 |

tau_q = 0.1, stratum ArXiv, sub_rung_chain (m = 3): budget rung S16
| rung | n_off | mean_contributing | clean_prefix_fraction | testable | label | d_hat | interval | half_width | draws_above_X | unconditional |
|---|---|---|---|---|---|---|---|---|---|---|
| S4 | 4.0000 | 64.0000 | 1.0000 | True | holds | 0.0002 | [+0.0002, +0.0002] | 0.0000 | 0/1 | 0.0002 |
| S16 | 16.0000 | 64.0000 | 0.9901 | True | holds | 0.0010 | [+0.0009, +0.0011] | 0.0001 | 0/1 | 0.0010 |
| S64 | 64.0000 | 57.0000 | 0.2253 | False | not testable with these donors |  |  |  |  | 0.0324 |

tau_q = 0.1, stratum Pile-CC, donor_chain (m = 7): budget rung 7
| rung | n_off | mean_contributing | clean_prefix_fraction | testable | label | d_hat | interval | half_width | draws_above_X | unconditional |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 0.0000 | 64.0000 | 1.0000 | True | holds | 0.0000 | [+0.0000, +0.0000] | 0.0000 | 0/8 | 0.0000 |
| 2 | 0.2500 | 64.0000 | 1.0000 | True | holds | 0.0000 | [+0.0000, +0.0000] | 0.0000 | 0/8 | 0.0000 |
| 3 | 2.5000 | 64.0000 | 1.0000 | True | holds | 0.0001 | [+0.0001, +0.0002] | 0.0000 | 0/8 | 0.0001 |
| 4 | 5.6250 | 64.0000 | 1.0000 | True | holds | 0.0004 | [+0.0004, +0.0004] | 0.0000 | 0/8 | 0.0004 |
| 5 | 21.7500 | 64.0000 | 0.9982 | True | holds | 0.0014 | [+0.0013, +0.0015] | 0.0001 | 0/8 | 0.0014 |
| 6 | 60.6250 | 64.0000 | 0.9874 | True | holds | 0.0039 | [+0.0036, +0.0041] | 0.0002 | 0/8 | 0.0039 |
| 7 | 104.5000 | 64.0000 | 0.9824 | True | holds | 0.0067 | [+0.0063, +0.0071] | 0.0004 | 0/8 | 0.0067 |

tau_q = 0.1, stratum Pile-CC, sub_rung_chain (m = 3): budget rung S64
| rung | n_off | mean_contributing | clean_prefix_fraction | testable | label | d_hat | interval | half_width | draws_above_X | unconditional |
|---|---|---|---|---|---|---|---|---|---|---|
| S4 | 4.0000 | 64.0000 | 1.0000 | True | holds | 0.0002 | [+0.0002, +0.0002] | 0.0000 | 0/1 | 0.0002 |
| S16 | 16.0000 | 64.0000 | 0.9886 | True | holds | 0.0010 | [+0.0010, +0.0011] | 0.0001 | 0/1 | 0.0010 |
| S64 | 64.0000 | 64.0000 | 0.9886 | True | holds | 0.0043 | [+0.0040, +0.0046] | 0.0003 | 0/1 | 0.0043 |

tau_q = 0.1, stratum StackExchange, donor_chain (m = 7): budget rung 1
| rung | n_off | mean_contributing | clean_prefix_fraction | testable | label | d_hat | interval | half_width | draws_above_X | unconditional |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 0.0000 | 64.0000 | 1.0000 | True | holds | 0.0000 | [+0.0000, +0.0000] | 0.0000 | 0/8 | 0.0000 |
| 2 | 0.2500 | 63.7500 | 0.9069 | False | not testable with these donors |  |  |  |  | 0.0022 |
| 3 | 2.5000 | 62.7500 | 0.6606 | False | not testable with these donors |  |  |  |  | 0.0074 |
| 4 | 5.6250 | 61.7500 | 0.6710 | False | not testable with these donors |  |  |  |  | 0.0066 |
| 5 | 21.7500 | 57.8750 | 0.3942 | False | not testable with these donors |  |  |  |  | 0.0129 |
| 6 | 60.6250 | 52.5000 | 0.2543 | False | not testable with these donors |  |  |  |  | 0.0200 |
| 7 | 104.5000 | 50.2500 | 0.2407 | False | not testable with these donors |  |  |  |  | 0.0249 |

tau_q = 0.1, stratum StackExchange, sub_rung_chain (m = 3): budget rung None
| rung | n_off | mean_contributing | clean_prefix_fraction | testable | label | d_hat | interval | half_width | draws_above_X | unconditional |
|---|---|---|---|---|---|---|---|---|---|---|
| S4 | 4.0000 | 61.0000 | 0.4955 | False | not testable with these donors | None | None | None | None | 0.0095 |
| S16 | 16.0000 | 55.0000 | 0.3530 | False | not testable with these donors | None | None | None | None | 0.0138 |
| S64 | 64.0000 | 50.0000 | 0.2482 | False | not testable with these donors | None | None | None | None | 0.0208 |

tau_q = 0.1, stratum Wikipedia (en), donor_chain (m = 7): budget rung 5
| rung | n_off | mean_contributing | clean_prefix_fraction | testable | label | d_hat | interval | half_width | draws_above_X | unconditional |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 0.0000 | 64.0000 | 1.0000 | True | holds | 0.0000 | [+0.0000, +0.0000] | 0.0000 | 0/8 | 0.0000 |
| 2 | 0.2500 | 64.0000 | 0.9922 | True | holds | 0.0000 | [+0.0000, +0.0000] | 0.0000 | 0/8 | 0.0000 |
| 3 | 2.5000 | 64.0000 | 0.9767 | True | holds | 0.0002 | [+0.0002, +0.0002] | 0.0000 | 0/8 | 0.0002 |
| 4 | 5.6250 | 64.0000 | 0.9780 | True | holds | 0.0005 | [+0.0004, +0.0006] | 0.0001 | 0/8 | 0.0004 |
| 5 | 21.7500 | 64.0000 | 0.9664 | True | holds | 0.0018 | [+0.0015, +0.0023] | 0.0004 | 0/8 | 0.0016 |
| 6 | 60.6250 | 63.5000 | 0.9508 | False | not testable with these donors |  |  |  |  | 0.0047 |
| 7 | 104.5000 | 63.0000 | 0.9430 | False | not testable with these donors |  |  |  |  | 0.0080 |

tau_q = 0.1, stratum Wikipedia (en), sub_rung_chain (m = 3): budget rung S16
| rung | n_off | mean_contributing | clean_prefix_fraction | testable | label | d_hat | interval | half_width | draws_above_X | unconditional |
|---|---|---|---|---|---|---|---|---|---|---|
| S4 | 4.0000 | 64.0000 | 0.9690 | True | holds | 0.0003 | [+0.0002, +0.0006] | 0.0002 | 0/1 | 0.0002 |
| S16 | 16.0000 | 64.0000 | 0.9690 | True | holds | 0.0013 | [+0.0011, +0.0014] | 0.0001 | 0/1 | 0.0012 |
| S64 | 64.0000 | 63.0000 | 0.9574 | False | not testable with these donors |  |  |  |  | 0.0050 |

tau_q = 0, stratum all, donor_chain (m = 7): budget rung 7
| rung | n_off | mean_contributing | clean_prefix_fraction | testable | label | d_hat | interval | half_width | draws_above_X | unconditional |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 0.0000 | 512.0000 | 1.0000 | True | holds | 0.0000 | [+0.0000, +0.0000] | 0.0000 | 0/8 | 0.0000 |
| 2 | 0.2500 | 510.2500 | 0.9179 | True | holds | 0.0001 | [+0.0001, +0.0001] | 0.0000 | 0/8 | 0.0015 |
| 3 | 2.5000 | 494.1250 | 0.6510 | True | holds | 0.0005 | [+0.0004, +0.0006] | 0.0001 | 0/8 | 0.0055 |
| 4 | 5.6250 | 479.1250 | 0.5953 | True | holds | 0.0009 | [+0.0008, +0.0010] | 0.0001 | 0/8 | 0.0060 |
| 5 | 21.7500 | 418.0000 | 0.3001 | True | holds | 0.0030 | [+0.0027, +0.0033] | 0.0003 | 0/8 | 0.0123 |
| 6 | 60.6250 | 346.6250 | 0.1394 | True | holds | 0.0072 | [+0.0066, +0.0079] | 0.0007 | 0/8 | 0.0224 |
| 7 | 104.5000 | 308.6250 | 0.0863 | True | holds | 0.0114 | [+0.0104, +0.0126] | 0.0011 | 0/8 | 0.0298 |

tau_q = 0, stratum all, sub_rung_chain (m = 3): budget rung S64
| rung | n_off | mean_contributing | clean_prefix_fraction | testable | label | d_hat | interval | half_width | draws_above_X | unconditional |
|---|---|---|---|---|---|---|---|---|---|---|
| S4 | 4.0000 | 472.0000 | 0.5245 | True | holds | 0.0008 | [+0.0006, +0.0009] | 0.0001 | 0/1 | 0.0074 |
| S16 | 16.0000 | 402.0000 | 0.3316 | True | holds | 0.0024 | [+0.0021, +0.0028] | 0.0003 | 0/1 | 0.0132 |
| S64 | 64.0000 | 341.0000 | 0.1284 | True | holds | 0.0078 | [+0.0071, +0.0085] | 0.0007 | 0/1 | 0.0253 |

tau_q = 0, stratum Github, donor_chain (m = 7): budget rung 6
| rung | n_off | mean_contributing | clean_prefix_fraction | testable | label | d_hat | interval | half_width | draws_above_X | unconditional |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 0.0000 | 256.0000 | 1.0000 | True | holds | 0.0000 | [+0.0000, +0.0000] | 0.0000 | 0/8 | 0.0000 |
| 2 | 0.2500 | 254.5000 | 0.8640 | True | holds | 0.0001 | [+0.0001, +0.0002] | 0.0000 | 0/8 | 0.0025 |
| 3 | 2.5000 | 240.5000 | 0.4442 | True | holds | 0.0008 | [+0.0007, +0.0009] | 0.0001 | 0/8 | 0.0091 |
| 4 | 5.6250 | 231.0000 | 0.4171 | True | holds | 0.0014 | [+0.0012, +0.0015] | 0.0002 | 0/8 | 0.0098 |
| 5 | 21.7500 | 183.2500 | 0.1301 | True | holds | 0.0046 | [+0.0041, +0.0051] | 0.0005 | 0/8 | 0.0193 |
| 6 | 60.6250 | 141.0000 | 0.0526 | True | holds | 0.0104 | [+0.0093, +0.0118] | 0.0012 | 0/8 | 0.0323 |
| 7 | 104.5000 | 120.6250 | 0.0315 | False | not testable with these donors |  |  |  |  | 0.0392 |

tau_q = 0, stratum Github, sub_rung_chain (m = 3): budget rung S16
| rung | n_off | mean_contributing | clean_prefix_fraction | testable | label | d_hat | interval | half_width | draws_above_X | unconditional |
|---|---|---|---|---|---|---|---|---|---|---|
| S4 | 4.0000 | 224.0000 | 0.2469 | True | holds | 0.0012 | [+0.0010, +0.0014] | 0.0002 | 0/1 | 0.0123 |
| S16 | 16.0000 | 166.0000 | 0.1016 | True | holds | 0.0040 | [+0.0035, +0.0047] | 0.0006 | 0/1 | 0.0221 |
| S64 | 64.0000 | 134.0000 | 0.0392 | False | not testable with these donors |  |  |  |  | 0.0350 |

tau_q = 0, stratum other, donor_chain (m = 7): budget rung 7
| rung | n_off | mean_contributing | clean_prefix_fraction | testable | label | d_hat | interval | half_width | draws_above_X | unconditional |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 0.0000 | 256.0000 | 1.0000 | True | holds | 0.0000 | [+0.0000, +0.0000] | 0.0000 | 0/8 | 0.0000 |
| 2 | 0.2500 | 255.7500 | 0.9718 | True | holds | 0.0000 | [+0.0000, +0.0001] | 0.0000 | 0/8 | 0.0006 |
| 3 | 2.5000 | 253.6250 | 0.8577 | True | holds | 0.0002 | [+0.0002, +0.0003] | 0.0001 | 0/8 | 0.0020 |
| 4 | 5.6250 | 248.1250 | 0.7736 | True | holds | 0.0005 | [+0.0005, +0.0006] | 0.0001 | 0/8 | 0.0021 |
| 5 | 21.7500 | 234.7500 | 0.4700 | True | holds | 0.0019 | [+0.0017, +0.0021] | 0.0002 | 0/8 | 0.0053 |
| 6 | 60.6250 | 205.6250 | 0.2263 | True | holds | 0.0050 | [+0.0046, +0.0055] | 0.0005 | 0/8 | 0.0124 |
| 7 | 104.5000 | 188.0000 | 0.1411 | True | holds | 0.0086 | [+0.0078, +0.0094] | 0.0008 | 0/8 | 0.0204 |

tau_q = 0, stratum other, sub_rung_chain (m = 3): budget rung S64
| rung | n_off | mean_contributing | clean_prefix_fraction | testable | label | d_hat | interval | half_width | draws_above_X | unconditional |
|---|---|---|---|---|---|---|---|---|---|---|
| S4 | 4.0000 | 248.0000 | 0.8022 | True | holds | 0.0003 | [+0.0003, +0.0005] | 0.0001 | 0/1 | 0.0025 |
| S16 | 16.0000 | 236.0000 | 0.5616 | True | holds | 0.0013 | [+0.0012, +0.0015] | 0.0001 | 0/1 | 0.0043 |
| S64 | 64.0000 | 207.0000 | 0.2176 | True | holds | 0.0054 | [+0.0050, +0.0059] | 0.0004 | 0/1 | 0.0157 |

tau_q = 0, stratum ArXiv, donor_chain (m = 7): budget rung 2
| rung | n_off | mean_contributing | clean_prefix_fraction | testable | label | d_hat | interval | half_width | draws_above_X | unconditional |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 0.0000 | 64.0000 | 1.0000 | True | holds | 0.0000 | [+0.0000, +0.0000] | 0.0000 | 0/8 | 0.0000 |
| 2 | 0.2500 | 64.0000 | 1.0000 | True | holds | 0.0000 | [+0.0000, +0.0000] | 0.0000 | 0/8 | 0.0000 |
| 3 | 2.5000 | 63.6250 | 0.9532 | False | not testable with these donors |  |  |  |  | 0.0002 |
| 4 | 5.6250 | 61.2500 | 0.7524 | False | not testable with these donors |  |  |  |  | 0.0010 |
| 5 | 21.7500 | 57.3750 | 0.4051 | False | not testable with these donors |  |  |  |  | 0.0053 |
| 6 | 60.6250 | 45.1250 | 0.1220 | False | not testable with these donors |  |  |  |  | 0.0212 |
| 7 | 104.5000 | 37.8750 | 0.0623 | False | not testable with these donors |  |  |  |  | 0.0420 |

tau_q = 0, stratum ArXiv, sub_rung_chain (m = 3): budget rung S4
| rung | n_off | mean_contributing | clean_prefix_fraction | testable | label | d_hat | interval | half_width | draws_above_X | unconditional |
|---|---|---|---|---|---|---|---|---|---|---|
| S4 | 4.0000 | 64.0000 | 0.9496 | True | holds | 0.0002 | [+0.0002, +0.0002] | 0.0000 | 0/1 | 0.0002 |
| S16 | 16.0000 | 61.0000 | 0.6915 | False | not testable with these donors |  |  |  |  | 0.0010 |
| S64 | 64.0000 | 51.0000 | 0.1274 | False | not testable with these donors |  |  |  |  | 0.0324 |

tau_q = 0, stratum Pile-CC, donor_chain (m = 7): budget rung 2
| rung | n_off | mean_contributing | clean_prefix_fraction | testable | label | d_hat | interval | half_width | draws_above_X | unconditional |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 0.0000 | 64.0000 | 1.0000 | True | holds | 0.0000 | [+0.0000, +0.0000] | 0.0000 | 0/8 | 0.0000 |
| 2 | 0.2500 | 64.0000 | 0.9968 | True | holds | 0.0000 | [+0.0000, +0.0000] | 0.0000 | 0/8 | 0.0000 |
| 3 | 2.5000 | 63.6250 | 0.9461 | False | not testable with these donors |  |  |  |  | 0.0001 |
| 4 | 5.6250 | 62.8750 | 0.9000 | False | not testable with these donors |  |  |  |  | 0.0004 |
| 5 | 21.7500 | 60.7500 | 0.6456 | False | not testable with these donors |  |  |  |  | 0.0014 |
| 6 | 60.6250 | 56.7500 | 0.3585 | False | not testable with these donors |  |  |  |  | 0.0039 |
| 7 | 104.5000 | 54.1250 | 0.2247 | False | not testable with these donors |  |  |  |  | 0.0067 |

tau_q = 0, stratum Pile-CC, sub_rung_chain (m = 3): budget rung None
| rung | n_off | mean_contributing | clean_prefix_fraction | testable | label | d_hat | interval | half_width | draws_above_X | unconditional |
|---|---|---|---|---|---|---|---|---|---|---|
| S4 | 4.0000 | 63.0000 | 0.9174 | False | not testable with these donors | None | None | None | None | 0.0002 |
| S16 | 16.0000 | 61.0000 | 0.7332 | False | not testable with these donors | None | None | None | None | 0.0010 |
| S64 | 64.0000 | 58.0000 | 0.3394 | False | not testable with these donors | None | None | None | None | 0.0043 |

tau_q = 0, stratum StackExchange, donor_chain (m = 7): budget rung 1
| rung | n_off | mean_contributing | clean_prefix_fraction | testable | label | d_hat | interval | half_width | draws_above_X | unconditional |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 0.0000 | 64.0000 | 1.0000 | True | holds | 0.0000 | [+0.0000, +0.0000] | 0.0000 | 0/8 | 0.0000 |
| 2 | 0.2500 | 63.7500 | 0.8995 | False | not testable with these donors |  |  |  |  | 0.0022 |
| 3 | 2.5000 | 62.6250 | 0.6200 | False | not testable with these donors |  |  |  |  | 0.0074 |
| 4 | 5.6250 | 61.1250 | 0.5938 | False | not testable with these donors |  |  |  |  | 0.0066 |
| 5 | 21.7500 | 55.7500 | 0.2835 | False | not testable with these donors |  |  |  |  | 0.0129 |
| 6 | 60.6250 | 45.5000 | 0.1230 | False | not testable with these donors |  |  |  |  | 0.0200 |
| 7 | 104.5000 | 41.5000 | 0.0877 | False | not testable with these donors |  |  |  |  | 0.0249 |

tau_q = 0, stratum StackExchange, sub_rung_chain (m = 3): budget rung None
| rung | n_off | mean_contributing | clean_prefix_fraction | testable | label | d_hat | interval | half_width | draws_above_X | unconditional |
|---|---|---|---|---|---|---|---|---|---|---|
| S4 | 4.0000 | 59.0000 | 0.4817 | False | not testable with these donors | None | None | None | None | 0.0095 |
| S16 | 16.0000 | 52.0000 | 0.2316 | False | not testable with these donors | None | None | None | None | 0.0138 |
| S64 | 64.0000 | 42.0000 | 0.1015 | False | not testable with these donors | None | None | None | None | 0.0208 |

tau_q = 0, stratum Wikipedia (en), donor_chain (m = 7): budget rung 2
| rung | n_off | mean_contributing | clean_prefix_fraction | testable | label | d_hat | interval | half_width | draws_above_X | unconditional |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 0.0000 | 64.0000 | 1.0000 | True | holds | 0.0000 | [+0.0000, +0.0000] | 0.0000 | 0/8 | 0.0000 |
| 2 | 0.2500 | 64.0000 | 0.9908 | True | holds | 0.0000 | [+0.0000, +0.0000] | 0.0000 | 0/8 | 0.0000 |
| 3 | 2.5000 | 63.7500 | 0.9116 | False | not testable with these donors |  |  |  |  | 0.0002 |
| 4 | 5.6250 | 62.8750 | 0.8481 | False | not testable with these donors |  |  |  |  | 0.0004 |
| 5 | 21.7500 | 60.8750 | 0.5460 | False | not testable with these donors |  |  |  |  | 0.0016 |
| 6 | 60.6250 | 58.2500 | 0.3019 | False | not testable with these donors |  |  |  |  | 0.0047 |
| 7 | 104.5000 | 54.5000 | 0.1898 | False | not testable with these donors |  |  |  |  | 0.0080 |

tau_q = 0, stratum Wikipedia (en), sub_rung_chain (m = 3): budget rung None
| rung | n_off | mean_contributing | clean_prefix_fraction | testable | label | d_hat | interval | half_width | draws_above_X | unconditional |
|---|---|---|---|---|---|---|---|---|---|---|
| S4 | 4.0000 | 62.0000 | 0.8601 | False | not testable with these donors | None | None | None | None | 0.0002 |
| S16 | 16.0000 | 62.0000 | 0.5899 | False | not testable with these donors | None | None | None | None | 0.0012 |
| S64 | 64.0000 | 56.0000 | 0.3021 | False | not testable with these donors | None | None | None | None | 0.0050 |

### `hard_zero/E/D_unif/tau0.1/ones/incl/ctl-none` (curve 5)
Positive control: unconditional damage on E material at rung 4 and beyond: pass (5 rungs judged); readability floor equals the pre-reads' table: True (14 of 14 rows matched)
The erased set against its plain control per rung (mean over draws; the control's pool is the alive set): rung 1: overlap 2 of 61 erased (0.036; control 61 from a pool of 6355, of which 61 are the erased set's own); rung 2: overlap 38 of 392 erased (0.094; control 392 from a pool of 6355, of which 392 are the erased set's own); rung 3: overlap 595 of 1792 erased (0.331; control 1792 from a pool of 6355, of which 1792 are the erased set's own); rung 4: overlap 1156 of 2484 erased (0.420; control 2484 from a pool of 6355, of which 2484 are the erased set's own); rung 5: overlap 3119 of 4394 erased (0.708; control 4394 from a pool of 6355, of which 4394 are the erased set's own); rung 6: overlap 4820 of 5516 erased (0.874; control 5516 from a pool of 6355, of which 5516 are the erased set's own); rung 7: overlap 5775 of 6053 erased (0.954; control 6053 from a pool of 6355, of which 6053 are the erased set's own); rung 8: overlap 6350 of 6361 erased (0.998; control 6361 from a pool of 6355, of which 6352 are the erased set's own, overflow 8)
tau_q = 0.1, stratum all, donor_chain (m = 7): budget rung None
| rung | n_off | mean_contributing | clean_prefix_fraction | testable | label | d_hat | interval | half_width | draws_above_X | unconditional |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 60.7500 | 0.0000 | 0.0000 | False | not testable with these donors | None | None | None | None | 6.3587 |
| 2 | 392.5000 | 0.0000 | 0.0000 | False | not testable with these donors | None | None | None | None | 7.7161 |
| 3 | 1792.0000 | 0.0000 | 0.0000 | False | not testable with these donors | None | None | None | None | 8.6089 |
| 4 | 2483.6250 | 0.0000 | 0.0000 | False | not testable with these donors | None | None | None | None | 9.3136 |
| 5 | 4394.3750 | 0.0000 | 0.0000 | False | not testable with these donors | None | None | None | None | 10.2618 |
| 6 | 5516.0000 | 0.0000 | 0.0000 | False | not testable with these donors | None | None | None | None | 10.3238 |
| 7 | 6053.1250 | 0.0000 | 0.0000 | False | not testable with these donors | None | None | None | None | 10.1139 |

tau_q = 0, stratum all, donor_chain (m = 7): budget rung None
| rung | n_off | mean_contributing | clean_prefix_fraction | testable | label | d_hat | interval | half_width | draws_above_X | unconditional |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 60.7500 | 0.0000 | 0.0000 | False | not testable with these donors | None | None | None | None | 6.3587 |
| 2 | 392.5000 | 0.0000 | 0.0000 | False | not testable with these donors | None | None | None | None | 7.7161 |
| 3 | 1792.0000 | 0.0000 | 0.0000 | False | not testable with these donors | None | None | None | None | 8.6089 |
| 4 | 2483.6250 | 0.0000 | 0.0000 | False | not testable with these donors | None | None | None | None | 9.3136 |
| 5 | 4394.3750 | 0.0000 | 0.0000 | False | not testable with these donors | None | None | None | None | 10.2618 |
| 6 | 5516.0000 | 0.0000 | 0.0000 | False | not testable with these donors | None | None | None | None | 10.3238 |
| 7 | 6053.1250 | 0.0000 | 0.0000 | False | not testable with these donors | None | None | None | None | 10.1139 |

### `hard_zero/E/D_unif/tau0.1/ones/incl/ctl-plain`
Positive control: does not apply; readability floor equals the pre-reads' table: True (14 of 14 rows matched)
tau_q = 0.1, stratum all, donor_chain (m = 7): budget rung None
| rung | n_off | mean_contributing | clean_prefix_fraction | testable | label | d_hat | interval | half_width | draws_above_X | unconditional |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 60.7500 | 0.0000 | 0.0001 | False | not testable with these donors | None | None | None | None | 0.6806 |
| 2 | 392.5000 | 0.0000 | 0.0000 | False | not testable with these donors | None | None | None | None | 2.8455 |
| 3 | 1792.0000 | 0.0000 | 0.0000 | False | not testable with these donors | None | None | None | None | 7.6220 |
| 4 | 2483.6250 | 0.0000 | 0.0000 | False | not testable with these donors | None | None | None | None | 7.3509 |
| 5 | 4394.3750 | 0.0000 | 0.0000 | False | not testable with these donors | None | None | None | None | 8.6992 |
| 6 | 5516.0000 | 0.0000 | 0.0000 | False | not testable with these donors | None | None | None | None | 9.8513 |
| 7 | 6053.1250 | 0.0000 | 0.0000 | False | not testable with these donors | None | None | None | None | 9.9938 |

tau_q = 0, stratum all, donor_chain (m = 7): budget rung None
| rung | n_off | mean_contributing | clean_prefix_fraction | testable | label | d_hat | interval | half_width | draws_above_X | unconditional |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 60.7500 | 0.0000 | 0.0001 | False | not testable with these donors | None | None | None | None | 0.6806 |
| 2 | 392.5000 | 0.0000 | 0.0000 | False | not testable with these donors | None | None | None | None | 2.8455 |
| 3 | 1792.0000 | 0.0000 | 0.0000 | False | not testable with these donors | None | None | None | None | 7.6220 |
| 4 | 2483.6250 | 0.0000 | 0.0000 | False | not testable with these donors | None | None | None | None | 7.3509 |
| 5 | 4394.3750 | 0.0000 | 0.0000 | False | not testable with these donors | None | None | None | None | 8.6992 |
| 6 | 5516.0000 | 0.0000 | 0.0000 | False | not testable with these donors | None | None | None | None | 9.8513 |
| 7 | 6053.1250 | 0.0000 | 0.0000 | False | not testable with these donors | None | None | None | None | 9.9938 |

### `never_named_hard/E/D_unif/tau0.1/ones/incl/ctl-none`
Positive control: does not apply; readability floor equals the pre-reads' table: True (18 of 18 rows matched)
Rung 8 alone under the one-cell rule (m = 1, not counted in the donor chain's m), 32551 erased: tau_q = 0.1: testable, d_hat +7.2861 [+7.2425, +7.3309], fails; tau_q = 0: not testable, not testable with these donors; unconditional 7.2914
tau_q = 0.1, stratum all, donor_chain (m = 9): budget rung 2
| rung | n_off | mean_contributing | clean_prefix_fraction | testable | label | d_hat | interval | half_width | draws_above_X | unconditional |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 60.7500 | 1024.0000 | 0.9999 | True | holds | 0.0024 | [+0.0023, +0.0024] | 0.0001 | 0/8 | 0.0024 |
| 2 | 392.5000 | 1024.0000 | 0.9996 | True | holds | 0.0175 | [+0.0170, +0.0181] | 0.0005 | 0/8 | 0.0175 |
| 3 | 1792.0000 | 1023.8750 | 0.9979 | True | fails | 0.1020 | [+0.0989, +0.1058] | 0.0034 | 8/8 | 0.1021 |
| 4 | 2483.6250 | 1023.8750 | 0.9977 | True | fails | 0.1603 | [+0.1555, +0.1659] | 0.0052 | 7/8 | 0.1604 |
| 5 | 4394.3750 | 1023.7500 | 0.9971 | True | fails | 0.3401 | [+0.3306, +0.3513] | 0.0104 | 8/8 | 0.3402 |
| 6 | 5516.0000 | 1023.7500 | 0.9965 | True | fails | 0.4764 | [+0.4635, +0.4913] | 0.0139 | 8/8 | 0.4766 |
| 7 | 6053.1250 | 1023.7500 | 0.9964 | True | fails | 0.5493 | [+0.5344, +0.5663] | 0.0159 | 8/8 | 0.5496 |
| B50 | 16275.0000 | 1023.3750 | 0.9927 | True | fails | 3.1656 | [+3.1080, +3.2273] | 0.0597 | 8/8 | 3.1641 |
| B75 | 24413.0000 | 1023.2500 | 0.9906 | True | fails | 5.9183 | [+5.8500, +5.9905] | 0.0702 | 8/8 | 5.9248 |

tau_q = 0, stratum all, donor_chain (m = 9): budget rung 2
| rung | n_off | mean_contributing | clean_prefix_fraction | testable | label | d_hat | interval | half_width | draws_above_X | unconditional |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 60.7500 | 1012.7500 | 0.7980 | True | holds | 0.0024 | [+0.0023, +0.0025] | 0.0001 | 0/8 | 0.0024 |
| 2 | 392.5000 | 964.6250 | 0.3299 | True | holds | 0.0179 | [+0.0173, +0.0185] | 0.0006 | 0/8 | 0.0175 |
| 3 | 1792.0000 | 767.5000 | 0.0654 | True | fails | 0.0960 | [+0.0930, +0.0993] | 0.0031 | 8/8 | 0.1021 |
| 4 | 2483.6250 | 692.5000 | 0.0704 | True | fails | 0.1433 | [+0.1386, +0.1483] | 0.0049 | 7/8 | 0.1604 |
| 5 | 4394.3750 | 512.5000 | 0.0239 | False | not testable with these donors |  |  |  |  | 0.3402 |
| 6 | 5516.0000 | 429.3750 | 0.0187 | False | not testable with these donors |  |  |  |  | 0.4766 |
| 7 | 6053.1250 | 399.5000 | 0.0171 | False | not testable with these donors |  |  |  |  | 0.5496 |
| B50 | 16275.0000 | 97.1250 | 0.0058 | False | not testable with these donors |  |  |  |  | 3.1641 |
| B75 | 24413.0000 | 36.0000 | 0.0037 | False | not testable with these donors |  |  |  |  | 5.9248 |

### `never_named_hard/E/D_unif/tau0.1/ones/excl/ctl-none`
Positive control: does not apply; readability floor equals the pre-reads' table: True (0 of 0 rows matched)
Rung 8 alone under the one-cell rule (m = 1, not counted in the donor chain's m), 32551 erased: tau_q = 0.1: testable, d_hat +7.2913 [+7.2477, +7.3361], fails; tau_q = 0: not testable, not testable with these donors; unconditional 7.2966
### `never_named_hard/E/D_unif/tau0/ones/incl/ctl-none`
Positive control: does not apply; readability floor equals the pre-reads' table: True (0 of 0 rows matched)
Rung 8 alone under the one-cell rule (m = 1, not counted in the donor chain's m), 6456 erased: tau_q = 0.1: testable, d_hat +0.5561 [+0.5442, +0.5691], fails; tau_q = 0: testable, d_hat +0.5377 [+0.5242, +0.5524], fails; unconditional 0.5563
### `hard_zero/E_lab/D_code/tau0.1/ones/incl/ctl-plain`
Positive control: does not apply; readability floor equals the pre-reads' table: True (98 of 98 rows matched)
tau_q = 0.1, stratum all, donor_chain (m = 7): budget rung None
| rung | n_off | mean_contributing | clean_prefix_fraction | testable | label | d_hat | interval | half_width | draws_above_X | unconditional |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 63.0000 | 33.6250 | 0.0033 | False | not testable with these donors | None | None | None | None | 0.7870 |
| 2 | 316.5000 | 0.0000 | 0.0000 | False | not testable with these donors | None | None | None | None | 2.7689 |
| 3 | 1444.7500 | 0.0000 | 0.0000 | False | not testable with these donors | None | None | None | None | 7.6289 |
| 4 | 2508.5000 | 0.0000 | 0.0000 | False | not testable with these donors | None | None | None | None | 8.1469 |
| 5 | 3971.6250 | 0.0000 | 0.0000 | False | not testable with these donors | None | None | None | None | 8.7546 |
| 6 | 5081.0000 | 0.0000 | 0.0000 | False | not testable with these donors | None | None | None | None | 9.1026 |
| 7 | 5550.5000 | 0.0000 | 0.0000 | False | not testable with these donors | None | None | None | None | 9.9335 |

tau_q = 0.1, stratum Github, donor_chain (m = 7): budget rung None
| rung | n_off | mean_contributing | clean_prefix_fraction | testable | label | d_hat | interval | half_width | draws_above_X | unconditional |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 63.0000 | 16.2500 | 0.0031 | False | not testable with these donors | None | None | None | None | 0.8496 |
| 2 | 316.5000 | 0.0000 | 0.0000 | False | not testable with these donors | None | None | None | None | 3.0050 |
| 3 | 1444.7500 | 0.0000 | 0.0000 | False | not testable with these donors | None | None | None | None | 8.1311 |
| 4 | 2508.5000 | 0.0000 | 0.0000 | False | not testable with these donors | None | None | None | None | 8.5912 |
| 5 | 3971.6250 | 0.0000 | 0.0000 | False | not testable with these donors | None | None | None | None | 9.3157 |
| 6 | 5081.0000 | 0.0000 | 0.0000 | False | not testable with these donors | None | None | None | None | 9.6439 |
| 7 | 5550.5000 | 0.0000 | 0.0000 | False | not testable with these donors | None | None | None | None | 10.3585 |

tau_q = 0.1, stratum other, donor_chain (m = 7): budget rung None
| rung | n_off | mean_contributing | clean_prefix_fraction | testable | label | d_hat | interval | half_width | draws_above_X | unconditional |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 63.0000 | 17.3750 | 0.0034 | False | not testable with these donors | None | None | None | None | 0.7244 |
| 2 | 316.5000 | 0.0000 | 0.0000 | False | not testable with these donors | None | None | None | None | 2.5328 |
| 3 | 1444.7500 | 0.0000 | 0.0000 | False | not testable with these donors | None | None | None | None | 7.1267 |
| 4 | 2508.5000 | 0.0000 | 0.0000 | False | not testable with these donors | None | None | None | None | 7.7025 |
| 5 | 3971.6250 | 0.0000 | 0.0000 | False | not testable with these donors | None | None | None | None | 8.1934 |
| 6 | 5081.0000 | 0.0000 | 0.0000 | False | not testable with these donors | None | None | None | None | 8.5613 |
| 7 | 5550.5000 | 0.0000 | 0.0000 | False | not testable with these donors | None | None | None | None | 9.5085 |

tau_q = 0.1, stratum ArXiv, donor_chain (m = 7): budget rung None
| rung | n_off | mean_contributing | clean_prefix_fraction | testable | label | d_hat | interval | half_width | draws_above_X | unconditional |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 63.0000 | 5.3750 | 0.0040 | False | not testable with these donors | None | None | None | None | 0.7126 |
| 2 | 316.5000 | 0.0000 | 0.0000 | False | not testable with these donors | None | None | None | None | 2.5363 |
| 3 | 1444.7500 | 0.0000 | 0.0000 | False | not testable with these donors | None | None | None | None | 7.5045 |
| 4 | 2508.5000 | 0.0000 | 0.0000 | False | not testable with these donors | None | None | None | None | 8.1548 |
| 5 | 3971.6250 | 0.0000 | 0.0000 | False | not testable with these donors | None | None | None | None | 8.7237 |
| 6 | 5081.0000 | 0.0000 | 0.0000 | False | not testable with these donors | None | None | None | None | 9.1364 |
| 7 | 5550.5000 | 0.0000 | 0.0000 | False | not testable with these donors | None | None | None | None | 10.1809 |

tau_q = 0.1, stratum Pile-CC, donor_chain (m = 7): budget rung None
| rung | n_off | mean_contributing | clean_prefix_fraction | testable | label | d_hat | interval | half_width | draws_above_X | unconditional |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 63.0000 | 4.6250 | 0.0032 | False | not testable with these donors | None | None | None | None | 0.7000 |
| 2 | 316.5000 | 0.0000 | 0.0000 | False | not testable with these donors | None | None | None | None | 2.3838 |
| 3 | 1444.7500 | 0.0000 | 0.0000 | False | not testable with these donors | None | None | None | None | 6.4789 |
| 4 | 2508.5000 | 0.0000 | 0.0000 | False | not testable with these donors | None | None | None | None | 7.1235 |
| 5 | 3971.6250 | 0.0000 | 0.0000 | False | not testable with these donors | None | None | None | None | 7.5161 |
| 6 | 5081.0000 | 0.0000 | 0.0000 | False | not testable with these donors | None | None | None | None | 7.9395 |
| 7 | 5550.5000 | 0.0000 | 0.0000 | False | not testable with these donors | None | None | None | None | 8.9087 |

tau_q = 0.1, stratum StackExchange, donor_chain (m = 7): budget rung None
| rung | n_off | mean_contributing | clean_prefix_fraction | testable | label | d_hat | interval | half_width | draws_above_X | unconditional |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 63.0000 | 4.2500 | 0.0037 | False | not testable with these donors | None | None | None | None | 0.7280 |
| 2 | 316.5000 | 0.0000 | 0.0000 | False | not testable with these donors | None | None | None | None | 2.6025 |
| 3 | 1444.7500 | 0.0000 | 0.0000 | False | not testable with these donors | None | None | None | None | 7.4769 |
| 4 | 2508.5000 | 0.0000 | 0.0000 | False | not testable with these donors | None | None | None | None | 7.9189 |
| 5 | 3971.6250 | 0.0000 | 0.0000 | False | not testable with these donors | None | None | None | None | 8.4998 |
| 6 | 5081.0000 | 0.0000 | 0.0000 | False | not testable with these donors | None | None | None | None | 8.7704 |
| 7 | 5550.5000 | 0.0000 | 0.0000 | False | not testable with these donors | None | None | None | None | 9.5250 |

tau_q = 0.1, stratum Wikipedia (en), donor_chain (m = 7): budget rung None
| rung | n_off | mean_contributing | clean_prefix_fraction | testable | label | d_hat | interval | half_width | draws_above_X | unconditional |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 63.0000 | 3.1250 | 0.0029 | False | not testable with these donors | None | None | None | None | 0.7569 |
| 2 | 316.5000 | 0.0000 | 0.0000 | False | not testable with these donors | None | None | None | None | 2.6086 |
| 3 | 1444.7500 | 0.0000 | 0.0000 | False | not testable with these donors | None | None | None | None | 7.0464 |
| 4 | 2508.5000 | 0.0000 | 0.0000 | False | not testable with these donors | None | None | None | None | 7.6129 |
| 5 | 3971.6250 | 0.0000 | 0.0000 | False | not testable with these donors | None | None | None | None | 8.0342 |
| 6 | 5081.0000 | 0.0000 | 0.0000 | False | not testable with these donors | None | None | None | None | 8.3987 |
| 7 | 5550.5000 | 0.0000 | 0.0000 | False | not testable with these donors | None | None | None | None | 9.4194 |

tau_q = 0, stratum all, donor_chain (m = 7): budget rung None
| rung | n_off | mean_contributing | clean_prefix_fraction | testable | label | d_hat | interval | half_width | draws_above_X | unconditional |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 63.0000 | 26.3750 | 0.0027 | False | not testable with these donors | None | None | None | None | 0.7870 |
| 2 | 316.5000 | 0.0000 | 0.0000 | False | not testable with these donors | None | None | None | None | 2.7689 |
| 3 | 1444.7500 | 0.0000 | 0.0000 | False | not testable with these donors | None | None | None | None | 7.6289 |
| 4 | 2508.5000 | 0.0000 | 0.0000 | False | not testable with these donors | None | None | None | None | 8.1469 |
| 5 | 3971.6250 | 0.0000 | 0.0000 | False | not testable with these donors | None | None | None | None | 8.7546 |
| 6 | 5081.0000 | 0.0000 | 0.0000 | False | not testable with these donors | None | None | None | None | 9.1026 |
| 7 | 5550.5000 | 0.0000 | 0.0000 | False | not testable with these donors | None | None | None | None | 9.9335 |

tau_q = 0, stratum Github, donor_chain (m = 7): budget rung None
| rung | n_off | mean_contributing | clean_prefix_fraction | testable | label | d_hat | interval | half_width | draws_above_X | unconditional |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 63.0000 | 12.6250 | 0.0025 | False | not testable with these donors | None | None | None | None | 0.8496 |
| 2 | 316.5000 | 0.0000 | 0.0000 | False | not testable with these donors | None | None | None | None | 3.0050 |
| 3 | 1444.7500 | 0.0000 | 0.0000 | False | not testable with these donors | None | None | None | None | 8.1311 |
| 4 | 2508.5000 | 0.0000 | 0.0000 | False | not testable with these donors | None | None | None | None | 8.5912 |
| 5 | 3971.6250 | 0.0000 | 0.0000 | False | not testable with these donors | None | None | None | None | 9.3157 |
| 6 | 5081.0000 | 0.0000 | 0.0000 | False | not testable with these donors | None | None | None | None | 9.6439 |
| 7 | 5550.5000 | 0.0000 | 0.0000 | False | not testable with these donors | None | None | None | None | 10.3585 |

tau_q = 0, stratum other, donor_chain (m = 7): budget rung None
| rung | n_off | mean_contributing | clean_prefix_fraction | testable | label | d_hat | interval | half_width | draws_above_X | unconditional |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 63.0000 | 13.7500 | 0.0029 | False | not testable with these donors | None | None | None | None | 0.7244 |
| 2 | 316.5000 | 0.0000 | 0.0000 | False | not testable with these donors | None | None | None | None | 2.5328 |
| 3 | 1444.7500 | 0.0000 | 0.0000 | False | not testable with these donors | None | None | None | None | 7.1267 |
| 4 | 2508.5000 | 0.0000 | 0.0000 | False | not testable with these donors | None | None | None | None | 7.7025 |
| 5 | 3971.6250 | 0.0000 | 0.0000 | False | not testable with these donors | None | None | None | None | 8.1934 |
| 6 | 5081.0000 | 0.0000 | 0.0000 | False | not testable with these donors | None | None | None | None | 8.5613 |
| 7 | 5550.5000 | 0.0000 | 0.0000 | False | not testable with these donors | None | None | None | None | 9.5085 |

tau_q = 0, stratum ArXiv, donor_chain (m = 7): budget rung None
| rung | n_off | mean_contributing | clean_prefix_fraction | testable | label | d_hat | interval | half_width | draws_above_X | unconditional |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 63.0000 | 4.5000 | 0.0033 | False | not testable with these donors | None | None | None | None | 0.7126 |
| 2 | 316.5000 | 0.0000 | 0.0000 | False | not testable with these donors | None | None | None | None | 2.5363 |
| 3 | 1444.7500 | 0.0000 | 0.0000 | False | not testable with these donors | None | None | None | None | 7.5045 |
| 4 | 2508.5000 | 0.0000 | 0.0000 | False | not testable with these donors | None | None | None | None | 8.1548 |
| 5 | 3971.6250 | 0.0000 | 0.0000 | False | not testable with these donors | None | None | None | None | 8.7237 |
| 6 | 5081.0000 | 0.0000 | 0.0000 | False | not testable with these donors | None | None | None | None | 9.1364 |
| 7 | 5550.5000 | 0.0000 | 0.0000 | False | not testable with these donors | None | None | None | None | 10.1809 |

tau_q = 0, stratum Pile-CC, donor_chain (m = 7): budget rung None
| rung | n_off | mean_contributing | clean_prefix_fraction | testable | label | d_hat | interval | half_width | draws_above_X | unconditional |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 63.0000 | 3.1250 | 0.0025 | False | not testable with these donors | None | None | None | None | 0.7000 |
| 2 | 316.5000 | 0.0000 | 0.0000 | False | not testable with these donors | None | None | None | None | 2.3838 |
| 3 | 1444.7500 | 0.0000 | 0.0000 | False | not testable with these donors | None | None | None | None | 6.4789 |
| 4 | 2508.5000 | 0.0000 | 0.0000 | False | not testable with these donors | None | None | None | None | 7.1235 |
| 5 | 3971.6250 | 0.0000 | 0.0000 | False | not testable with these donors | None | None | None | None | 7.5161 |
| 6 | 5081.0000 | 0.0000 | 0.0000 | False | not testable with these donors | None | None | None | None | 7.9395 |
| 7 | 5550.5000 | 0.0000 | 0.0000 | False | not testable with these donors | None | None | None | None | 8.9087 |

tau_q = 0, stratum StackExchange, donor_chain (m = 7): budget rung None
| rung | n_off | mean_contributing | clean_prefix_fraction | testable | label | d_hat | interval | half_width | draws_above_X | unconditional |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 63.0000 | 3.5000 | 0.0031 | False | not testable with these donors | None | None | None | None | 0.7280 |
| 2 | 316.5000 | 0.0000 | 0.0000 | False | not testable with these donors | None | None | None | None | 2.6025 |
| 3 | 1444.7500 | 0.0000 | 0.0000 | False | not testable with these donors | None | None | None | None | 7.4769 |
| 4 | 2508.5000 | 0.0000 | 0.0000 | False | not testable with these donors | None | None | None | None | 7.9189 |
| 5 | 3971.6250 | 0.0000 | 0.0000 | False | not testable with these donors | None | None | None | None | 8.4998 |
| 6 | 5081.0000 | 0.0000 | 0.0000 | False | not testable with these donors | None | None | None | None | 8.7704 |
| 7 | 5550.5000 | 0.0000 | 0.0000 | False | not testable with these donors | None | None | None | None | 9.5250 |

tau_q = 0, stratum Wikipedia (en), donor_chain (m = 7): budget rung None
| rung | n_off | mean_contributing | clean_prefix_fraction | testable | label | d_hat | interval | half_width | draws_above_X | unconditional |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 63.0000 | 2.6250 | 0.0026 | False | not testable with these donors | None | None | None | None | 0.7569 |
| 2 | 316.5000 | 0.0000 | 0.0000 | False | not testable with these donors | None | None | None | None | 2.6086 |
| 3 | 1444.7500 | 0.0000 | 0.0000 | False | not testable with these donors | None | None | None | None | 7.0464 |
| 4 | 2508.5000 | 0.0000 | 0.0000 | False | not testable with these donors | None | None | None | None | 7.6129 |
| 5 | 3971.6250 | 0.0000 | 0.0000 | False | not testable with these donors | None | None | None | None | 8.0342 |
| 6 | 5081.0000 | 0.0000 | 0.0000 | False | not testable with these donors | None | None | None | None | 8.3987 |
| 7 | 5550.5000 | 0.0000 | 0.0000 | False | not testable with these donors | None | None | None | None | 9.4194 |

### `code_specific_hard/E_lab/D_code/tau0.1/ones/incl/ctl-complement`
Positive control: does not apply; readability floor equals the pre-reads' table: True (140 of 140 rows matched)
tau_q = 0.1, stratum all, donor_chain (m = 7): budget rung 7
| rung | n_off | mean_contributing | clean_prefix_fraction | testable | label | d_hat | interval | half_width | draws_above_X | unconditional |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 0.0000 | 512.0000 | 1.0000 | True | holds | 0.0000 | [+0.0000, +0.0000] | 0.0000 | 0/8 | 0.0000 |
| 2 | 0.2500 | 511.1250 | 0.9631 | True | holds | 0.0000 | [+0.0000, +0.0001] | 0.0000 | 0/8 | 0.0008 |
| 3 | 2.5000 | 508.2500 | 0.9119 | True | holds | 0.0003 | [+0.0002, +0.0003] | 0.0000 | 0/8 | 0.0011 |
| 4 | 5.6250 | 508.7500 | 0.9361 | True | holds | 0.0004 | [+0.0004, +0.0005] | 0.0000 | 0/8 | 0.0006 |
| 5 | 21.7500 | 495.2500 | 0.6947 | True | holds | 0.0019 | [+0.0018, +0.0021] | 0.0001 | 0/8 | 0.0035 |
| 6 | 60.6250 | 477.0000 | 0.5510 | True | holds | 0.0051 | [+0.0049, +0.0055] | 0.0003 | 0/8 | 0.0079 |
| 7 | 104.5000 | 457.5000 | 0.4897 | True | holds | 0.0089 | [+0.0084, +0.0095] | 0.0005 | 0/8 | 0.0130 |

tau_q = 0.1, stratum all, sub_rung_chain (m = 3): budget rung S64
| rung | n_off | mean_contributing | clean_prefix_fraction | testable | label | d_hat | interval | half_width | draws_above_X | unconditional |
|---|---|---|---|---|---|---|---|---|---|---|
| S4 | 4.0000 | 504.0000 | 0.8325 | True | holds | 0.0003 | [+0.0003, +0.0004] | 0.0000 | 0/1 | 0.0009 |
| S16 | 16.0000 | 495.0000 | 0.6996 | True | holds | 0.0014 | [+0.0013, +0.0016] | 0.0001 | 0/1 | 0.0036 |
| S64 | 64.0000 | 472.0000 | 0.5096 | True | holds | 0.0054 | [+0.0051, +0.0058] | 0.0003 | 0/1 | 0.0089 |

tau_q = 0.1, stratum Github, donor_chain (m = 7): budget rung 7
| rung | n_off | mean_contributing | clean_prefix_fraction | testable | label | d_hat | interval | half_width | draws_above_X | unconditional |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 0.0000 | 256.0000 | 1.0000 | True | holds | 0.0000 | [+0.0000, +0.0000] | 0.0000 | 0/8 | 0.0000 |
| 2 | 0.2500 | 255.2500 | 0.9407 | True | holds | 0.0001 | [+0.0001, +0.0001] | 0.0000 | 0/8 | 0.0013 |
| 3 | 2.5000 | 252.6250 | 0.8611 | True | holds | 0.0004 | [+0.0003, +0.0004] | 0.0000 | 0/8 | 0.0018 |
| 4 | 5.6250 | 253.7500 | 0.9152 | True | holds | 0.0005 | [+0.0005, +0.0006] | 0.0000 | 0/8 | 0.0007 |
| 5 | 21.7500 | 243.8750 | 0.6318 | True | holds | 0.0024 | [+0.0022, +0.0026] | 0.0002 | 0/8 | 0.0044 |
| 6 | 60.6250 | 231.8750 | 0.4385 | True | holds | 0.0063 | [+0.0059, +0.0069] | 0.0005 | 0/8 | 0.0092 |
| 7 | 104.5000 | 222.0000 | 0.3539 | True | holds | 0.0109 | [+0.0101, +0.0120] | 0.0009 | 0/8 | 0.0147 |

tau_q = 0.1, stratum Github, sub_rung_chain (m = 3): budget rung S64
| rung | n_off | mean_contributing | clean_prefix_fraction | testable | label | d_hat | interval | half_width | draws_above_X | unconditional |
|---|---|---|---|---|---|---|---|---|---|---|
| S4 | 4.0000 | 249.0000 | 0.7057 | True | holds | 0.0004 | [+0.0004, +0.0005] | 0.0001 | 0/1 | 0.0016 |
| S16 | 16.0000 | 243.0000 | 0.5581 | True | holds | 0.0019 | [+0.0017, +0.0021] | 0.0002 | 0/1 | 0.0060 |
| S64 | 64.0000 | 225.0000 | 0.3551 | True | holds | 0.0067 | [+0.0061, +0.0073] | 0.0006 | 0/1 | 0.0124 |

tau_q = 0.1, stratum other, donor_chain (m = 7): budget rung 7
| rung | n_off | mean_contributing | clean_prefix_fraction | testable | label | d_hat | interval | half_width | draws_above_X | unconditional |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 0.0000 | 256.0000 | 1.0000 | True | holds | 0.0000 | [+0.0000, +0.0000] | 0.0000 | 0/8 | 0.0000 |
| 2 | 0.2500 | 255.8750 | 0.9856 | True | holds | 0.0000 | [+0.0000, +0.0000] | 0.0000 | 0/8 | 0.0003 |
| 3 | 2.5000 | 255.6250 | 0.9626 | True | holds | 0.0002 | [+0.0002, +0.0002] | 0.0000 | 0/8 | 0.0005 |
| 4 | 5.6250 | 255.0000 | 0.9570 | True | holds | 0.0003 | [+0.0003, +0.0004] | 0.0000 | 0/8 | 0.0004 |
| 5 | 21.7500 | 251.3750 | 0.7575 | True | holds | 0.0015 | [+0.0014, +0.0016] | 0.0001 | 0/8 | 0.0027 |
| 6 | 60.6250 | 245.1250 | 0.6635 | True | holds | 0.0040 | [+0.0038, +0.0043] | 0.0002 | 0/8 | 0.0066 |
| 7 | 104.5000 | 235.5000 | 0.6254 | True | holds | 0.0070 | [+0.0066, +0.0074] | 0.0004 | 0/8 | 0.0114 |

tau_q = 0.1, stratum other, sub_rung_chain (m = 3): budget rung S64
| rung | n_off | mean_contributing | clean_prefix_fraction | testable | label | d_hat | interval | half_width | draws_above_X | unconditional |
|---|---|---|---|---|---|---|---|---|---|---|
| S4 | 4.0000 | 255.0000 | 0.9592 | True | holds | 0.0002 | [+0.0002, +0.0002] | 0.0000 | 0/1 | 0.0003 |
| S16 | 16.0000 | 252.0000 | 0.8412 | True | holds | 0.0010 | [+0.0009, +0.0010] | 0.0001 | 0/1 | 0.0013 |
| S64 | 64.0000 | 247.0000 | 0.6640 | True | holds | 0.0043 | [+0.0041, +0.0046] | 0.0002 | 0/1 | 0.0054 |

tau_q = 0.1, stratum ArXiv, donor_chain (m = 7): budget rung 3
| rung | n_off | mean_contributing | clean_prefix_fraction | testable | label | d_hat | interval | half_width | draws_above_X | unconditional |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 0.0000 | 64.0000 | 1.0000 | True | holds | 0.0000 | [+0.0000, +0.0000] | 0.0000 | 0/8 | 0.0000 |
| 2 | 0.2500 | 64.0000 | 0.9929 | True | holds | 0.0000 | [+0.0000, +0.0000] | 0.0000 | 0/8 | 0.0000 |
| 3 | 2.5000 | 64.0000 | 0.9505 | True | holds | 0.0002 | [+0.0001, +0.0002] | 0.0000 | 0/8 | 0.0002 |
| 4 | 5.6250 | 63.2500 | 0.8797 | False | not testable with these donors |  |  |  |  | 0.0006 |
| 5 | 21.7500 | 61.8750 | 0.4752 | False | not testable with these donors |  |  |  |  | 0.0043 |
| 6 | 60.6250 | 59.1250 | 0.3509 | False | not testable with these donors |  |  |  |  | 0.0103 |
| 7 | 104.5000 | 51.7500 | 0.2557 | False | not testable with these donors |  |  |  |  | 0.0177 |

tau_q = 0.1, stratum ArXiv, sub_rung_chain (m = 3): budget rung S16
| rung | n_off | mean_contributing | clean_prefix_fraction | testable | label | d_hat | interval | half_width | draws_above_X | unconditional |
|---|---|---|---|---|---|---|---|---|---|---|
| S4 | 4.0000 | 64.0000 | 0.9059 | True | holds | 0.0002 | [+0.0002, +0.0003] | 0.0000 | 0/1 | 0.0003 |
| S16 | 16.0000 | 64.0000 | 0.9046 | True | holds | 0.0009 | [+0.0008, +0.0010] | 0.0001 | 0/1 | 0.0012 |
| S64 | 64.0000 | 61.0000 | 0.4169 | False | not testable with these donors |  |  |  |  | 0.0073 |

tau_q = 0.1, stratum Pile-CC, donor_chain (m = 7): budget rung 7
| rung | n_off | mean_contributing | clean_prefix_fraction | testable | label | d_hat | interval | half_width | draws_above_X | unconditional |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 0.0000 | 64.0000 | 1.0000 | True | holds | 0.0000 | [+0.0000, +0.0000] | 0.0000 | 0/8 | 0.0000 |
| 2 | 0.2500 | 64.0000 | 1.0000 | True | holds | 0.0000 | [+0.0000, +0.0000] | 0.0000 | 0/8 | 0.0000 |
| 3 | 2.5000 | 64.0000 | 1.0000 | True | holds | 0.0001 | [+0.0001, +0.0001] | 0.0000 | 0/8 | 0.0001 |
| 4 | 5.6250 | 64.0000 | 1.0000 | True | holds | 0.0003 | [+0.0003, +0.0003] | 0.0000 | 0/8 | 0.0003 |
| 5 | 21.7500 | 64.0000 | 0.9982 | True | holds | 0.0013 | [+0.0012, +0.0013] | 0.0001 | 0/8 | 0.0013 |
| 6 | 60.6250 | 64.0000 | 0.9956 | True | holds | 0.0035 | [+0.0033, +0.0036] | 0.0002 | 0/8 | 0.0035 |
| 7 | 104.5000 | 64.0000 | 0.9936 | True | holds | 0.0061 | [+0.0058, +0.0064] | 0.0003 | 0/8 | 0.0061 |

tau_q = 0.1, stratum Pile-CC, sub_rung_chain (m = 3): budget rung S64
| rung | n_off | mean_contributing | clean_prefix_fraction | testable | label | d_hat | interval | half_width | draws_above_X | unconditional |
|---|---|---|---|---|---|---|---|---|---|---|
| S4 | 4.0000 | 64.0000 | 1.0000 | True | holds | 0.0002 | [+0.0002, +0.0002] | 0.0000 | 0/1 | 0.0002 |
| S16 | 16.0000 | 64.0000 | 1.0000 | True | holds | 0.0009 | [+0.0008, +0.0009] | 0.0001 | 0/1 | 0.0009 |
| S64 | 64.0000 | 64.0000 | 0.9951 | True | holds | 0.0037 | [+0.0036, +0.0039] | 0.0002 | 0/1 | 0.0037 |

tau_q = 0.1, stratum StackExchange, donor_chain (m = 7): budget rung 1
| rung | n_off | mean_contributing | clean_prefix_fraction | testable | label | d_hat | interval | half_width | draws_above_X | unconditional |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 0.0000 | 64.0000 | 1.0000 | True | holds | 0.0000 | [+0.0000, +0.0000] | 0.0000 | 0/8 | 0.0000 |
| 2 | 0.2500 | 63.8750 | 0.9535 | False | not testable with these donors |  |  |  |  | 0.0011 |
| 3 | 2.5000 | 63.6250 | 0.9038 | False | not testable with these donors |  |  |  |  | 0.0014 |
| 4 | 5.6250 | 63.7500 | 0.9482 | False | not testable with these donors |  |  |  |  | 0.0005 |
| 5 | 21.7500 | 61.5000 | 0.5644 | False | not testable with these donors |  |  |  |  | 0.0037 |
| 6 | 60.6250 | 58.0000 | 0.3203 | False | not testable with these donors |  |  |  |  | 0.0087 |
| 7 | 104.5000 | 55.7500 | 0.2691 | False | not testable with these donors |  |  |  |  | 0.0147 |

tau_q = 0.1, stratum StackExchange, sub_rung_chain (m = 3): budget rung None
| rung | n_off | mean_contributing | clean_prefix_fraction | testable | label | d_hat | interval | half_width | draws_above_X | unconditional |
|---|---|---|---|---|---|---|---|---|---|---|
| S4 | 4.0000 | 63.0000 | 0.9310 | False | not testable with these donors | None | None | None | None | 0.0004 |
| S16 | 16.0000 | 60.0000 | 0.4602 | False | not testable with these donors | None | None | None | None | 0.0019 |
| S64 | 64.0000 | 58.0000 | 0.2546 | False | not testable with these donors | None | None | None | None | 0.0062 |

tau_q = 0.1, stratum Wikipedia (en), donor_chain (m = 7): budget rung 7
| rung | n_off | mean_contributing | clean_prefix_fraction | testable | label | d_hat | interval | half_width | draws_above_X | unconditional |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 0.0000 | 64.0000 | 1.0000 | True | holds | 0.0000 | [+0.0000, +0.0000] | 0.0000 | 0/8 | 0.0000 |
| 2 | 0.2500 | 64.0000 | 0.9961 | True | holds | 0.0000 | [+0.0000, +0.0000] | 0.0000 | 0/8 | 0.0000 |
| 3 | 2.5000 | 64.0000 | 0.9961 | True | holds | 0.0002 | [+0.0001, +0.0002] | 0.0000 | 0/8 | 0.0002 |
| 4 | 5.6250 | 64.0000 | 1.0000 | True | holds | 0.0004 | [+0.0003, +0.0004] | 0.0000 | 0/8 | 0.0004 |
| 5 | 21.7500 | 64.0000 | 0.9923 | True | holds | 0.0015 | [+0.0014, +0.0015] | 0.0001 | 0/8 | 0.0015 |
| 6 | 60.6250 | 64.0000 | 0.9872 | True | holds | 0.0040 | [+0.0038, +0.0042] | 0.0002 | 0/8 | 0.0040 |
| 7 | 104.5000 | 64.0000 | 0.9833 | True | holds | 0.0070 | [+0.0066, +0.0074] | 0.0004 | 0/8 | 0.0071 |

tau_q = 0.1, stratum Wikipedia (en), sub_rung_chain (m = 3): budget rung S64
| rung | n_off | mean_contributing | clean_prefix_fraction | testable | label | d_hat | interval | half_width | draws_above_X | unconditional |
|---|---|---|---|---|---|---|---|---|---|---|
| S4 | 4.0000 | 64.0000 | 1.0000 | True | holds | 0.0002 | [+0.0002, +0.0002] | 0.0000 | 0/1 | 0.0002 |
| S16 | 16.0000 | 64.0000 | 1.0000 | True | holds | 0.0010 | [+0.0009, +0.0010] | 0.0001 | 0/1 | 0.0010 |
| S64 | 64.0000 | 64.0000 | 0.9895 | True | holds | 0.0044 | [+0.0042, +0.0046] | 0.0002 | 0/1 | 0.0045 |

tau_q = 0, stratum all, donor_chain (m = 7): budget rung 7
| rung | n_off | mean_contributing | clean_prefix_fraction | testable | label | d_hat | interval | half_width | draws_above_X | unconditional |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 0.0000 | 512.0000 | 1.0000 | True | holds | 0.0000 | [+0.0000, +0.0000] | 0.0000 | 0/8 | 0.0000 |
| 2 | 0.2500 | 511.1250 | 0.9572 | True | holds | 0.0000 | [+0.0000, +0.0001] | 0.0000 | 0/8 | 0.0008 |
| 3 | 2.5000 | 506.2500 | 0.8658 | True | holds | 0.0003 | [+0.0002, +0.0003] | 0.0000 | 0/8 | 0.0011 |
| 4 | 5.6250 | 505.0000 | 0.8436 | True | holds | 0.0005 | [+0.0004, +0.0005] | 0.0000 | 0/8 | 0.0006 |
| 5 | 21.7500 | 475.3750 | 0.4705 | True | holds | 0.0020 | [+0.0019, +0.0021] | 0.0001 | 0/8 | 0.0035 |
| 6 | 60.6250 | 430.8750 | 0.2314 | True | holds | 0.0055 | [+0.0052, +0.0058] | 0.0003 | 0/8 | 0.0079 |
| 7 | 104.5000 | 382.6250 | 0.1375 | True | holds | 0.0096 | [+0.0090, +0.0103] | 0.0006 | 0/8 | 0.0130 |

tau_q = 0, stratum all, sub_rung_chain (m = 3): budget rung S64
| rung | n_off | mean_contributing | clean_prefix_fraction | testable | label | d_hat | interval | half_width | draws_above_X | unconditional |
|---|---|---|---|---|---|---|---|---|---|---|
| S4 | 4.0000 | 499.0000 | 0.7731 | True | holds | 0.0003 | [+0.0003, +0.0004] | 0.0000 | 0/1 | 0.0009 |
| S16 | 16.0000 | 476.0000 | 0.5125 | True | holds | 0.0015 | [+0.0014, +0.0016] | 0.0001 | 0/1 | 0.0036 |
| S64 | 64.0000 | 413.0000 | 0.1867 | True | holds | 0.0058 | [+0.0054, +0.0062] | 0.0004 | 0/1 | 0.0089 |

tau_q = 0, stratum Github, donor_chain (m = 7): budget rung 7
| rung | n_off | mean_contributing | clean_prefix_fraction | testable | label | d_hat | interval | half_width | draws_above_X | unconditional |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 0.0000 | 256.0000 | 1.0000 | True | holds | 0.0000 | [+0.0000, +0.0000] | 0.0000 | 0/8 | 0.0000 |
| 2 | 0.2500 | 255.2500 | 0.9304 | True | holds | 0.0001 | [+0.0001, +0.0001] | 0.0000 | 0/8 | 0.0013 |
| 3 | 2.5000 | 251.0000 | 0.8072 | True | holds | 0.0003 | [+0.0003, +0.0004] | 0.0000 | 0/8 | 0.0018 |
| 4 | 5.6250 | 252.1250 | 0.8136 | True | holds | 0.0006 | [+0.0005, +0.0006] | 0.0000 | 0/8 | 0.0007 |
| 5 | 21.7500 | 231.2500 | 0.3885 | True | holds | 0.0025 | [+0.0023, +0.0027] | 0.0002 | 0/8 | 0.0044 |
| 6 | 60.6250 | 203.5000 | 0.1528 | True | holds | 0.0068 | [+0.0064, +0.0074] | 0.0005 | 0/8 | 0.0092 |
| 7 | 104.5000 | 175.6250 | 0.0800 | True | holds | 0.0121 | [+0.0112, +0.0132] | 0.0010 | 0/8 | 0.0147 |

tau_q = 0, stratum Github, sub_rung_chain (m = 3): budget rung S64
| rung | n_off | mean_contributing | clean_prefix_fraction | testable | label | d_hat | interval | half_width | draws_above_X | unconditional |
|---|---|---|---|---|---|---|---|---|---|---|
| S4 | 4.0000 | 247.0000 | 0.6439 | True | holds | 0.0005 | [+0.0004, +0.0005] | 0.0001 | 0/1 | 0.0016 |
| S16 | 16.0000 | 231.0000 | 0.3756 | True | holds | 0.0020 | [+0.0018, +0.0023] | 0.0003 | 0/1 | 0.0060 |
| S64 | 64.0000 | 187.0000 | 0.1059 | True | holds | 0.0074 | [+0.0067, +0.0082] | 0.0007 | 0/1 | 0.0124 |

tau_q = 0, stratum other, donor_chain (m = 7): budget rung 7
| rung | n_off | mean_contributing | clean_prefix_fraction | testable | label | d_hat | interval | half_width | draws_above_X | unconditional |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 0.0000 | 256.0000 | 1.0000 | True | holds | 0.0000 | [+0.0000, +0.0000] | 0.0000 | 0/8 | 0.0000 |
| 2 | 0.2500 | 255.8750 | 0.9839 | True | holds | 0.0000 | [+0.0000, +0.0000] | 0.0000 | 0/8 | 0.0003 |
| 3 | 2.5000 | 255.2500 | 0.9244 | True | holds | 0.0002 | [+0.0002, +0.0002] | 0.0000 | 0/8 | 0.0005 |
| 4 | 5.6250 | 252.8750 | 0.8736 | True | holds | 0.0004 | [+0.0003, +0.0004] | 0.0000 | 0/8 | 0.0004 |
| 5 | 21.7500 | 244.1250 | 0.5524 | True | holds | 0.0015 | [+0.0014, +0.0016] | 0.0001 | 0/8 | 0.0027 |
| 6 | 60.6250 | 227.3750 | 0.3100 | True | holds | 0.0043 | [+0.0040, +0.0046] | 0.0003 | 0/8 | 0.0066 |
| 7 | 104.5000 | 207.0000 | 0.1949 | True | holds | 0.0076 | [+0.0070, +0.0083] | 0.0006 | 0/8 | 0.0114 |

tau_q = 0, stratum other, sub_rung_chain (m = 3): budget rung S64
| rung | n_off | mean_contributing | clean_prefix_fraction | testable | label | d_hat | interval | half_width | draws_above_X | unconditional |
|---|---|---|---|---|---|---|---|---|---|---|
| S4 | 4.0000 | 252.0000 | 0.9022 | True | holds | 0.0002 | [+0.0002, +0.0002] | 0.0000 | 0/1 | 0.0003 |
| S16 | 16.0000 | 245.0000 | 0.6494 | True | holds | 0.0010 | [+0.0009, +0.0011] | 0.0001 | 0/1 | 0.0013 |
| S64 | 64.0000 | 226.0000 | 0.2675 | True | holds | 0.0045 | [+0.0042, +0.0048] | 0.0003 | 0/1 | 0.0054 |

tau_q = 0, stratum ArXiv, donor_chain (m = 7): budget rung 3
| rung | n_off | mean_contributing | clean_prefix_fraction | testable | label | d_hat | interval | half_width | draws_above_X | unconditional |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 0.0000 | 64.0000 | 1.0000 | True | holds | 0.0000 | [+0.0000, +0.0000] | 0.0000 | 0/8 | 0.0000 |
| 2 | 0.2500 | 64.0000 | 0.9929 | True | holds | 0.0000 | [+0.0000, +0.0000] | 0.0000 | 0/8 | 0.0000 |
| 3 | 2.5000 | 64.0000 | 0.9199 | True | holds | 0.0002 | [+0.0001, +0.0002] | 0.0000 | 0/8 | 0.0002 |
| 4 | 5.6250 | 63.2500 | 0.8103 | False | not testable with these donors |  |  |  |  | 0.0006 |
| 5 | 21.7500 | 60.7500 | 0.3470 | False | not testable with these donors |  |  |  |  | 0.0043 |
| 6 | 60.6250 | 55.5000 | 0.2032 | False | not testable with these donors |  |  |  |  | 0.0103 |
| 7 | 104.5000 | 45.6250 | 0.1128 | False | not testable with these donors |  |  |  |  | 0.0177 |

tau_q = 0, stratum ArXiv, sub_rung_chain (m = 3): budget rung S4
| rung | n_off | mean_contributing | clean_prefix_fraction | testable | label | d_hat | interval | half_width | draws_above_X | unconditional |
|---|---|---|---|---|---|---|---|---|---|---|
| S4 | 4.0000 | 64.0000 | 0.8615 | True | holds | 0.0002 | [+0.0002, +0.0003] | 0.0000 | 0/1 | 0.0003 |
| S16 | 16.0000 | 63.0000 | 0.7207 | False | not testable with these donors |  |  |  |  | 0.0012 |
| S64 | 64.0000 | 54.0000 | 0.2016 | False | not testable with these donors |  |  |  |  | 0.0073 |

tau_q = 0, stratum Pile-CC, donor_chain (m = 7): budget rung 2
| rung | n_off | mean_contributing | clean_prefix_fraction | testable | label | d_hat | interval | half_width | draws_above_X | unconditional |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 0.0000 | 64.0000 | 1.0000 | True | holds | 0.0000 | [+0.0000, +0.0000] | 0.0000 | 0/8 | 0.0000 |
| 2 | 0.2500 | 64.0000 | 0.9982 | True | holds | 0.0000 | [+0.0000, +0.0000] | 0.0000 | 0/8 | 0.0000 |
| 3 | 2.5000 | 63.8750 | 0.9578 | False | not testable with these donors |  |  |  |  | 0.0001 |
| 4 | 5.6250 | 63.1250 | 0.9149 | False | not testable with these donors |  |  |  |  | 0.0003 |
| 5 | 21.7500 | 61.6250 | 0.7353 | False | not testable with these donors |  |  |  |  | 0.0013 |
| 6 | 60.6250 | 58.7500 | 0.4456 | False | not testable with these donors |  |  |  |  | 0.0035 |
| 7 | 104.5000 | 55.2500 | 0.2945 | False | not testable with these donors |  |  |  |  | 0.0061 |

tau_q = 0, stratum Pile-CC, sub_rung_chain (m = 3): budget rung None
| rung | n_off | mean_contributing | clean_prefix_fraction | testable | label | d_hat | interval | half_width | draws_above_X | unconditional |
|---|---|---|---|---|---|---|---|---|---|---|
| S4 | 4.0000 | 63.0000 | 0.9123 | False | not testable with these donors | None | None | None | None | 0.0002 |
| S16 | 16.0000 | 62.0000 | 0.7896 | False | not testable with these donors | None | None | None | None | 0.0009 |
| S64 | 64.0000 | 60.0000 | 0.3810 | False | not testable with these donors | None | None | None | None | 0.0037 |

tau_q = 0, stratum StackExchange, donor_chain (m = 7): budget rung 1
| rung | n_off | mean_contributing | clean_prefix_fraction | testable | label | d_hat | interval | half_width | draws_above_X | unconditional |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 0.0000 | 64.0000 | 1.0000 | True | holds | 0.0000 | [+0.0000, +0.0000] | 0.0000 | 0/8 | 0.0000 |
| 2 | 0.2500 | 63.8750 | 0.9498 | False | not testable with these donors |  |  |  |  | 0.0011 |
| 3 | 2.5000 | 63.6250 | 0.8676 | False | not testable with these donors |  |  |  |  | 0.0014 |
| 4 | 5.6250 | 63.2500 | 0.8549 | False | not testable with these donors |  |  |  |  | 0.0005 |
| 5 | 21.7500 | 59.5000 | 0.4169 | False | not testable with these donors |  |  |  |  | 0.0037 |
| 6 | 60.6250 | 52.5000 | 0.1823 | False | not testable with these donors |  |  |  |  | 0.0087 |
| 7 | 104.5000 | 48.1250 | 0.1138 | False | not testable with these donors |  |  |  |  | 0.0147 |

tau_q = 0, stratum StackExchange, sub_rung_chain (m = 3): budget rung None
| rung | n_off | mean_contributing | clean_prefix_fraction | testable | label | d_hat | interval | half_width | draws_above_X | unconditional |
|---|---|---|---|---|---|---|---|---|---|---|
| S4 | 4.0000 | 63.0000 | 0.9098 | False | not testable with these donors | None | None | None | None | 0.0004 |
| S16 | 16.0000 | 59.0000 | 0.3347 | False | not testable with these donors | None | None | None | None | 0.0019 |
| S64 | 64.0000 | 53.0000 | 0.1390 | False | not testable with these donors | None | None | None | None | 0.0062 |

tau_q = 0, stratum Wikipedia (en), donor_chain (m = 7): budget rung 2
| rung | n_off | mean_contributing | clean_prefix_fraction | testable | label | d_hat | interval | half_width | draws_above_X | unconditional |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 0.0000 | 64.0000 | 1.0000 | True | holds | 0.0000 | [+0.0000, +0.0000] | 0.0000 | 0/8 | 0.0000 |
| 2 | 0.2500 | 64.0000 | 0.9948 | True | holds | 0.0000 | [+0.0000, +0.0000] | 0.0000 | 0/8 | 0.0000 |
| 3 | 2.5000 | 63.7500 | 0.9522 | False | not testable with these donors |  |  |  |  | 0.0002 |
| 4 | 5.6250 | 63.2500 | 0.9146 | False | not testable with these donors |  |  |  |  | 0.0004 |
| 5 | 21.7500 | 62.2500 | 0.7106 | False | not testable with these donors |  |  |  |  | 0.0015 |
| 6 | 60.6250 | 60.6250 | 0.4088 | False | not testable with these donors |  |  |  |  | 0.0040 |
| 7 | 104.5000 | 58.0000 | 0.2586 | False | not testable with these donors |  |  |  |  | 0.0071 |

tau_q = 0, stratum Wikipedia (en), sub_rung_chain (m = 3): budget rung None
| rung | n_off | mean_contributing | clean_prefix_fraction | testable | label | d_hat | interval | half_width | draws_above_X | unconditional |
|---|---|---|---|---|---|---|---|---|---|---|
| S4 | 4.0000 | 62.0000 | 0.9253 | False | not testable with these donors | None | None | None | None | 0.0002 |
| S16 | 16.0000 | 61.0000 | 0.7527 | False | not testable with these donors | None | None | None | None | 0.0010 |
| S64 | 64.0000 | 59.0000 | 0.3483 | False | not testable with these donors | None | None | None | None | 0.0045 |

### `code_specific_hard/E_lab/D_code/tau0.1/ones/incl/ctl-plain`
Positive control: does not apply; readability floor equals the pre-reads' table: True (140 of 140 rows matched)
tau_q = 0.1, stratum all, donor_chain (m = 7): budget rung 4
| rung | n_off | mean_contributing | clean_prefix_fraction | testable | label | d_hat | interval | half_width | draws_above_X | unconditional |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 0.0000 | 512.0000 | 1.0000 | True | holds | 0.0000 | [+0.0000, +0.0000] | 0.0000 | 0/8 | 0.0000 |
| 2 | 0.2500 | 451.7500 | 0.8724 | True | holds | 0.0040 | [+0.0030, +0.0052] | 0.0011 | 0/8 | 0.0344 |
| 3 | 2.5000 | 412.8750 | 0.5115 | True | holds | 0.0049 | [+0.0039, +0.0062] | 0.0011 | 0/8 | 0.0391 |
| 4 | 5.6250 | 412.3750 | 0.3159 | True | holds | 0.0021 | [+0.0019, +0.0023] | 0.0002 | 0/8 | 0.0114 |
| 5 | 21.7500 | 99.3750 | 0.0117 | False | not testable with these donors |  |  |  |  | 0.0909 |
| 6 | 60.6250 | 2.2500 | 0.0002 | False | not testable with these donors |  |  |  |  | 0.2186 |
| 7 | 104.5000 | 0.0000 | 0.0001 | False | not testable with these donors |  |  |  |  | 0.3722 |

tau_q = 0.1, stratum all, sub_rung_chain (m = 3): budget rung S4
| rung | n_off | mean_contributing | clean_prefix_fraction | testable | label | d_hat | interval | half_width | draws_above_X | unconditional |
|---|---|---|---|---|---|---|---|---|---|---|
| S4 | 4.0000 | 489.0000 | 0.5151 | True | holds | 0.0006 | [+0.0006, +0.0007] | 0.0001 | 0/1 | 0.0017 |
| S16 | 16.0000 | 298.0000 | 0.0373 | False | not testable with these donors |  |  |  |  | 0.0337 |
| S64 | 64.0000 | 0.0000 | 0.0000 | False | not testable with these donors |  |  |  |  | 0.1186 |

tau_q = 0.1, stratum Github, donor_chain (m = 7): budget rung 4
| rung | n_off | mean_contributing | clean_prefix_fraction | testable | label | d_hat | interval | half_width | draws_above_X | unconditional |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 0.0000 | 256.0000 | 1.0000 | True | holds | 0.0000 | [+0.0000, +0.0000] | 0.0000 | 0/8 | 0.0000 |
| 2 | 0.2500 | 226.1250 | 0.8753 | True | holds | 0.0034 | [+0.0024, +0.0044] | 0.0010 | 0/8 | 0.0303 |
| 3 | 2.5000 | 212.5000 | 0.5249 | True | holds | 0.0043 | [+0.0033, +0.0052] | 0.0010 | 0/8 | 0.0342 |
| 4 | 5.6250 | 206.0000 | 0.3122 | True | holds | 0.0024 | [+0.0021, +0.0027] | 0.0003 | 0/8 | 0.0126 |
| 5 | 21.7500 | 48.0000 | 0.0100 | False | not testable with these donors |  |  |  |  | 0.0906 |
| 6 | 60.6250 | 0.6250 | 0.0002 | False | not testable with these donors |  |  |  |  | 0.2236 |
| 7 | 104.5000 | 0.0000 | 0.0000 | False | not testable with these donors |  |  |  |  | 0.3989 |

tau_q = 0.1, stratum Github, sub_rung_chain (m = 3): budget rung S4
| rung | n_off | mean_contributing | clean_prefix_fraction | testable | label | d_hat | interval | half_width | draws_above_X | unconditional |
|---|---|---|---|---|---|---|---|---|---|---|
| S4 | 4.0000 | 252.0000 | 0.6447 | True | holds | 0.0006 | [+0.0005, +0.0006] | 0.0001 | 0/1 | 0.0018 |
| S16 | 16.0000 | 147.0000 | 0.0315 | False | not testable with these donors |  |  |  |  | 0.0331 |
| S64 | 64.0000 | 0.0000 | 0.0000 | False | not testable with these donors |  |  |  |  | 0.1123 |

tau_q = 0.1, stratum other, donor_chain (m = 7): budget rung 4
| rung | n_off | mean_contributing | clean_prefix_fraction | testable | label | d_hat | interval | half_width | draws_above_X | unconditional |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 0.0000 | 256.0000 | 1.0000 | True | holds | 0.0000 | [+0.0000, +0.0000] | 0.0000 | 0/8 | 0.0000 |
| 2 | 0.2500 | 225.6250 | 0.8695 | True | holds | 0.0048 | [+0.0031, +0.0071] | 0.0020 | 0/8 | 0.0385 |
| 3 | 2.5000 | 200.3750 | 0.4981 | True | holds | 0.0057 | [+0.0038, +0.0083] | 0.0022 | 0/8 | 0.0439 |
| 4 | 5.6250 | 206.3750 | 0.3197 | True | holds | 0.0019 | [+0.0017, +0.0021] | 0.0002 | 0/8 | 0.0103 |
| 5 | 21.7500 | 51.3750 | 0.0134 | False | not testable with these donors |  |  |  |  | 0.0912 |
| 6 | 60.6250 | 1.6250 | 0.0003 | False | not testable with these donors |  |  |  |  | 0.2136 |
| 7 | 104.5000 | 0.0000 | 0.0001 | False | not testable with these donors |  |  |  |  | 0.3456 |

tau_q = 0.1, stratum other, sub_rung_chain (m = 3): budget rung S4
| rung | n_off | mean_contributing | clean_prefix_fraction | testable | label | d_hat | interval | half_width | draws_above_X | unconditional |
|---|---|---|---|---|---|---|---|---|---|---|
| S4 | 4.0000 | 237.0000 | 0.3854 | True | holds | 0.0007 | [+0.0006, +0.0008] | 0.0001 | 0/1 | 0.0015 |
| S16 | 16.0000 | 151.0000 | 0.0432 | False | not testable with these donors |  |  |  |  | 0.0342 |
| S64 | 64.0000 | 0.0000 | 0.0000 | False | not testable with these donors |  |  |  |  | 0.1249 |

tau_q = 0.1, stratum ArXiv, donor_chain (m = 7): budget rung 1
| rung | n_off | mean_contributing | clean_prefix_fraction | testable | label | d_hat | interval | half_width | draws_above_X | unconditional |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 0.0000 | 64.0000 | 1.0000 | True | holds | 0.0000 | [+0.0000, +0.0000] | 0.0000 | 0/8 | 0.0000 |
| 2 | 0.2500 | 57.1250 | 0.8610 | False | not testable with these donors |  |  |  |  | 0.0325 |
| 3 | 2.5000 | 51.5000 | 0.4099 | False | not testable with these donors |  |  |  |  | 0.0373 |
| 4 | 5.6250 | 52.6250 | 0.3438 | False | not testable with these donors |  |  |  |  | 0.0073 |
| 5 | 21.7500 | 14.5000 | 0.0178 | False | not testable with these donors |  |  |  |  | 0.0714 |
| 6 | 60.6250 | 0.0000 | 0.0001 | False | not testable with these donors |  |  |  |  | 0.2136 |
| 7 | 104.5000 | 0.0000 | 0.0000 | False | not testable with these donors |  |  |  |  | 0.3709 |

tau_q = 0.1, stratum ArXiv, sub_rung_chain (m = 3): budget rung S4
| rung | n_off | mean_contributing | clean_prefix_fraction | testable | label | d_hat | interval | half_width | draws_above_X | unconditional |
|---|---|---|---|---|---|---|---|---|---|---|
| S4 | 4.0000 | 64.0000 | 0.5897 | True | holds | 0.0004 | [+0.0004, +0.0005] | 0.0001 | 0/1 | 0.0005 |
| S16 | 16.0000 | 39.0000 | 0.0553 | False | not testable with these donors |  |  |  |  | 0.0266 |
| S64 | 64.0000 | 0.0000 | 0.0000 | False | not testable with these donors |  |  |  |  | 0.1356 |

tau_q = 0.1, stratum Pile-CC, donor_chain (m = 7): budget rung 1
| rung | n_off | mean_contributing | clean_prefix_fraction | testable | label | d_hat | interval | half_width | draws_above_X | unconditional |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 0.0000 | 64.0000 | 1.0000 | True | holds | 0.0000 | [+0.0000, +0.0000] | 0.0000 | 0/8 | 0.0000 |
| 2 | 0.2500 | 56.0000 | 0.8734 | False | not testable with these donors |  |  |  |  | 0.0433 |
| 3 | 2.5000 | 48.7500 | 0.5611 | False | not testable with these donors |  |  |  |  | 0.0501 |
| 4 | 5.6250 | 50.6250 | 0.3187 | False | not testable with these donors |  |  |  |  | 0.0124 |
| 5 | 21.7500 | 14.1250 | 0.0118 | False | not testable with these donors |  |  |  |  | 0.1007 |
| 6 | 60.6250 | 1.2500 | 0.0006 | False | not testable with these donors |  |  |  |  | 0.2170 |
| 7 | 104.5000 | 0.0000 | 0.0001 | False | not testable with these donors |  |  |  |  | 0.3238 |

tau_q = 0.1, stratum Pile-CC, sub_rung_chain (m = 3): budget rung None
| rung | n_off | mean_contributing | clean_prefix_fraction | testable | label | d_hat | interval | half_width | draws_above_X | unconditional |
|---|---|---|---|---|---|---|---|---|---|---|
| S4 | 4.0000 | 61.0000 | 0.4141 | False | not testable with these donors | None | None | None | None | 0.0012 |
| S16 | 16.0000 | 42.0000 | 0.0486 | False | not testable with these donors | None | None | None | None | 0.0422 |
| S64 | 64.0000 | 0.0000 | 0.0000 | False | not testable with these donors | None | None | None | None | 0.1266 |

tau_q = 0.1, stratum StackExchange, donor_chain (m = 7): budget rung 1
| rung | n_off | mean_contributing | clean_prefix_fraction | testable | label | d_hat | interval | half_width | draws_above_X | unconditional |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 0.0000 | 64.0000 | 1.0000 | True | holds | 0.0000 | [+0.0000, +0.0000] | 0.0000 | 0/8 | 0.0000 |
| 2 | 0.2500 | 56.5000 | 0.8739 | False | not testable with these donors |  |  |  |  | 0.0399 |
| 3 | 2.5000 | 52.2500 | 0.5012 | False | not testable with these donors |  |  |  |  | 0.0431 |
| 4 | 5.6250 | 51.6250 | 0.2961 | False | not testable with these donors |  |  |  |  | 0.0096 |
| 5 | 21.7500 | 10.7500 | 0.0100 | False | not testable with these donors |  |  |  |  | 0.0926 |
| 6 | 60.6250 | 0.2500 | 0.0002 | False | not testable with these donors |  |  |  |  | 0.1969 |
| 7 | 104.5000 | 0.0000 | 0.0001 | False | not testable with these donors |  |  |  |  | 0.3459 |

tau_q = 0.1, stratum StackExchange, sub_rung_chain (m = 3): budget rung None
| rung | n_off | mean_contributing | clean_prefix_fraction | testable | label | d_hat | interval | half_width | draws_above_X | unconditional |
|---|---|---|---|---|---|---|---|---|---|---|
| S4 | 4.0000 | 62.0000 | 0.3829 | False | not testable with these donors | None | None | None | None | 0.0007 |
| S16 | 16.0000 | 40.0000 | 0.0363 | False | not testable with these donors | None | None | None | None | 0.0223 |
| S64 | 64.0000 | 0.0000 | 0.0000 | False | not testable with these donors | None | None | None | None | 0.1112 |

tau_q = 0.1, stratum Wikipedia (en), donor_chain (m = 7): budget rung 1
| rung | n_off | mean_contributing | clean_prefix_fraction | testable | label | d_hat | interval | half_width | draws_above_X | unconditional |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 0.0000 | 64.0000 | 1.0000 | True | holds | 0.0000 | [+0.0000, +0.0000] | 0.0000 | 0/8 | 0.0000 |
| 2 | 0.2500 | 56.0000 | 0.8698 | False | not testable with these donors |  |  |  |  | 0.0383 |
| 3 | 2.5000 | 47.8750 | 0.5203 | False | not testable with these donors |  |  |  |  | 0.0450 |
| 4 | 5.6250 | 51.5000 | 0.3202 | False | not testable with these donors |  |  |  |  | 0.0119 |
| 5 | 21.7500 | 12.0000 | 0.0142 | False | not testable with these donors |  |  |  |  | 0.1001 |
| 6 | 60.6250 | 0.1250 | 0.0002 | False | not testable with these donors |  |  |  |  | 0.2270 |
| 7 | 104.5000 | 0.0000 | 0.0001 | False | not testable with these donors |  |  |  |  | 0.3418 |

tau_q = 0.1, stratum Wikipedia (en), sub_rung_chain (m = 3): budget rung None
| rung | n_off | mean_contributing | clean_prefix_fraction | testable | label | d_hat | interval | half_width | draws_above_X | unconditional |
|---|---|---|---|---|---|---|---|---|---|---|
| S4 | 4.0000 | 50.0000 | 0.1551 | False | not testable with these donors | None | None | None | None | 0.0036 |
| S16 | 16.0000 | 30.0000 | 0.0324 | False | not testable with these donors | None | None | None | None | 0.0457 |
| S64 | 64.0000 | 0.0000 | 0.0000 | False | not testable with these donors | None | None | None | None | 0.1264 |

tau_q = 0, stratum all, donor_chain (m = 7): budget rung 4
| rung | n_off | mean_contributing | clean_prefix_fraction | testable | label | d_hat | interval | half_width | draws_above_X | unconditional |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 0.0000 | 512.0000 | 1.0000 | True | holds | 0.0000 | [+0.0000, +0.0000] | 0.0000 | 0/8 | 0.0000 |
| 2 | 0.2500 | 450.3750 | 0.8697 | True | holds | 0.0042 | [+0.0029, +0.0059] | 0.0015 | 0/8 | 0.0344 |
| 3 | 2.5000 | 406.3750 | 0.4911 | True | holds | 0.0051 | [+0.0037, +0.0070] | 0.0016 | 0/8 | 0.0391 |
| 4 | 5.6250 | 395.6250 | 0.2848 | True | holds | 0.0020 | [+0.0018, +0.0023] | 0.0002 | 0/8 | 0.0114 |
| 5 | 21.7500 | 83.3750 | 0.0096 | False | not testable with these donors |  |  |  |  | 0.0909 |
| 6 | 60.6250 | 1.0000 | 0.0001 | False | not testable with these donors |  |  |  |  | 0.2186 |
| 7 | 104.5000 | 0.0000 | 0.0000 | False | not testable with these donors |  |  |  |  | 0.3722 |

tau_q = 0, stratum all, sub_rung_chain (m = 3): budget rung S4
| rung | n_off | mean_contributing | clean_prefix_fraction | testable | label | d_hat | interval | half_width | draws_above_X | unconditional |
|---|---|---|---|---|---|---|---|---|---|---|
| S4 | 4.0000 | 485.0000 | 0.4136 | True | holds | 0.0007 | [+0.0006, +0.0007] | 0.0001 | 0/1 | 0.0017 |
| S16 | 16.0000 | 269.0000 | 0.0299 | False | not testable with these donors |  |  |  |  | 0.0337 |
| S64 | 64.0000 | 0.0000 | 0.0000 | False | not testable with these donors |  |  |  |  | 0.1186 |

tau_q = 0, stratum Github, donor_chain (m = 7): budget rung 4
| rung | n_off | mean_contributing | clean_prefix_fraction | testable | label | d_hat | interval | half_width | draws_above_X | unconditional |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 0.0000 | 256.0000 | 1.0000 | True | holds | 0.0000 | [+0.0000, +0.0000] | 0.0000 | 0/8 | 0.0000 |
| 2 | 0.2500 | 225.2500 | 0.8724 | True | holds | 0.0033 | [+0.0018, +0.0049] | 0.0016 | 0/8 | 0.0303 |
| 3 | 2.5000 | 209.0000 | 0.5010 | True | holds | 0.0042 | [+0.0027, +0.0057] | 0.0015 | 0/8 | 0.0342 |
| 4 | 5.6250 | 195.6250 | 0.2760 | True | holds | 0.0024 | [+0.0021, +0.0027] | 0.0003 | 0/8 | 0.0126 |
| 5 | 21.7500 | 39.3750 | 0.0080 | False | not testable with these donors |  |  |  |  | 0.0906 |
| 6 | 60.6250 | 0.2500 | 0.0001 | False | not testable with these donors |  |  |  |  | 0.2236 |
| 7 | 104.5000 | 0.0000 | 0.0000 | False | not testable with these donors |  |  |  |  | 0.3989 |

tau_q = 0, stratum Github, sub_rung_chain (m = 3): budget rung S4
| rung | n_off | mean_contributing | clean_prefix_fraction | testable | label | d_hat | interval | half_width | draws_above_X | unconditional |
|---|---|---|---|---|---|---|---|---|---|---|
| S4 | 4.0000 | 250.0000 | 0.5175 | True | holds | 0.0006 | [+0.0006, +0.0007] | 0.0001 | 0/1 | 0.0018 |
| S16 | 16.0000 | 130.0000 | 0.0255 | False | not testable with these donors |  |  |  |  | 0.0331 |
| S64 | 64.0000 | 0.0000 | 0.0000 | False | not testable with these donors |  |  |  |  | 0.1123 |

tau_q = 0, stratum other, donor_chain (m = 7): budget rung 4
| rung | n_off | mean_contributing | clean_prefix_fraction | testable | label | d_hat | interval | half_width | draws_above_X | unconditional |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 0.0000 | 256.0000 | 1.0000 | True | holds | 0.0000 | [+0.0000, +0.0000] | 0.0000 | 0/8 | 0.0000 |
| 2 | 0.2500 | 225.1250 | 0.8671 | True | holds | 0.0052 | [+0.0032, +0.0082] | 0.0025 | 0/8 | 0.0385 |
| 3 | 2.5000 | 197.3750 | 0.4813 | True | holds | 0.0061 | [+0.0039, +0.0095] | 0.0028 | 0/8 | 0.0439 |
| 4 | 5.6250 | 200.0000 | 0.2936 | True | holds | 0.0018 | [+0.0016, +0.0022] | 0.0003 | 0/8 | 0.0103 |
| 5 | 21.7500 | 44.0000 | 0.0112 | False | not testable with these donors |  |  |  |  | 0.0912 |
| 6 | 60.6250 | 0.7500 | 0.0001 | False | not testable with these donors |  |  |  |  | 0.2136 |
| 7 | 104.5000 | 0.0000 | 0.0000 | False | not testable with these donors |  |  |  |  | 0.3456 |

tau_q = 0, stratum other, sub_rung_chain (m = 3): budget rung S4
| rung | n_off | mean_contributing | clean_prefix_fraction | testable | label | d_hat | interval | half_width | draws_above_X | unconditional |
|---|---|---|---|---|---|---|---|---|---|---|
| S4 | 4.0000 | 235.0000 | 0.3097 | True | holds | 0.0007 | [+0.0006, +0.0008] | 0.0001 | 0/1 | 0.0015 |
| S16 | 16.0000 | 139.0000 | 0.0343 | False | not testable with these donors |  |  |  |  | 0.0342 |
| S64 | 64.0000 | 0.0000 | 0.0000 | False | not testable with these donors |  |  |  |  | 0.1249 |

tau_q = 0, stratum ArXiv, donor_chain (m = 7): budget rung 1
| rung | n_off | mean_contributing | clean_prefix_fraction | testable | label | d_hat | interval | half_width | draws_above_X | unconditional |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 0.0000 | 64.0000 | 1.0000 | True | holds | 0.0000 | [+0.0000, +0.0000] | 0.0000 | 0/8 | 0.0000 |
| 2 | 0.2500 | 56.7500 | 0.8591 | False | not testable with these donors |  |  |  |  | 0.0325 |
| 3 | 2.5000 | 50.0000 | 0.3971 | False | not testable with these donors |  |  |  |  | 0.0373 |
| 4 | 5.6250 | 51.0000 | 0.3196 | False | not testable with these donors |  |  |  |  | 0.0073 |
| 5 | 21.7500 | 12.1250 | 0.0152 | False | not testable with these donors |  |  |  |  | 0.0714 |
| 6 | 60.6250 | 0.0000 | 0.0000 | False | not testable with these donors |  |  |  |  | 0.2136 |
| 7 | 104.5000 | 0.0000 | 0.0000 | False | not testable with these donors |  |  |  |  | 0.3709 |

tau_q = 0, stratum ArXiv, sub_rung_chain (m = 3): budget rung None
| rung | n_off | mean_contributing | clean_prefix_fraction | testable | label | d_hat | interval | half_width | draws_above_X | unconditional |
|---|---|---|---|---|---|---|---|---|---|---|
| S4 | 4.0000 | 63.0000 | 0.4694 | False | not testable with these donors | None | None | None | None | 0.0005 |
| S16 | 16.0000 | 33.0000 | 0.0432 | False | not testable with these donors | None | None | None | None | 0.0266 |
| S64 | 64.0000 | 0.0000 | 0.0000 | False | not testable with these donors | None | None | None | None | 0.1356 |

tau_q = 0, stratum Pile-CC, donor_chain (m = 7): budget rung 1
| rung | n_off | mean_contributing | clean_prefix_fraction | testable | label | d_hat | interval | half_width | draws_above_X | unconditional |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 0.0000 | 64.0000 | 1.0000 | True | holds | 0.0000 | [+0.0000, +0.0000] | 0.0000 | 0/8 | 0.0000 |
| 2 | 0.2500 | 56.0000 | 0.8722 | False | not testable with these donors |  |  |  |  | 0.0433 |
| 3 | 2.5000 | 48.3750 | 0.5479 | False | not testable with these donors |  |  |  |  | 0.0501 |
| 4 | 5.6250 | 49.5000 | 0.2992 | False | not testable with these donors |  |  |  |  | 0.0124 |
| 5 | 21.7500 | 12.1250 | 0.0096 | False | not testable with these donors |  |  |  |  | 0.1007 |
| 6 | 60.6250 | 0.6250 | 0.0003 | False | not testable with these donors |  |  |  |  | 0.2170 |
| 7 | 104.5000 | 0.0000 | 0.0001 | False | not testable with these donors |  |  |  |  | 0.3238 |

tau_q = 0, stratum Pile-CC, sub_rung_chain (m = 3): budget rung None
| rung | n_off | mean_contributing | clean_prefix_fraction | testable | label | d_hat | interval | half_width | draws_above_X | unconditional |
|---|---|---|---|---|---|---|---|---|---|---|
| S4 | 4.0000 | 61.0000 | 0.3711 | False | not testable with these donors | None | None | None | None | 0.0012 |
| S16 | 16.0000 | 42.0000 | 0.0396 | False | not testable with these donors | None | None | None | None | 0.0422 |
| S64 | 64.0000 | 0.0000 | 0.0000 | False | not testable with these donors | None | None | None | None | 0.1266 |

tau_q = 0, stratum StackExchange, donor_chain (m = 7): budget rung 1
| rung | n_off | mean_contributing | clean_prefix_fraction | testable | label | d_hat | interval | half_width | draws_above_X | unconditional |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 0.0000 | 64.0000 | 1.0000 | True | holds | 0.0000 | [+0.0000, +0.0000] | 0.0000 | 0/8 | 0.0000 |
| 2 | 0.2500 | 56.3750 | 0.8716 | False | not testable with these donors |  |  |  |  | 0.0399 |
| 3 | 2.5000 | 51.2500 | 0.4768 | False | not testable with these donors |  |  |  |  | 0.0431 |
| 4 | 5.6250 | 49.6250 | 0.2618 | False | not testable with these donors |  |  |  |  | 0.0096 |
| 5 | 21.7500 | 8.8750 | 0.0076 | False | not testable with these donors |  |  |  |  | 0.0926 |
| 6 | 60.6250 | 0.1250 | 0.0002 | False | not testable with these donors |  |  |  |  | 0.1969 |
| 7 | 104.5000 | 0.0000 | 0.0001 | False | not testable with these donors |  |  |  |  | 0.3459 |

tau_q = 0, stratum StackExchange, sub_rung_chain (m = 3): budget rung None
| rung | n_off | mean_contributing | clean_prefix_fraction | testable | label | d_hat | interval | half_width | draws_above_X | unconditional |
|---|---|---|---|---|---|---|---|---|---|---|
| S4 | 4.0000 | 62.0000 | 0.2894 | False | not testable with these donors | None | None | None | None | 0.0007 |
| S16 | 16.0000 | 35.0000 | 0.0278 | False | not testable with these donors | None | None | None | None | 0.0223 |
| S64 | 64.0000 | 0.0000 | 0.0000 | False | not testable with these donors | None | None | None | None | 0.1112 |

tau_q = 0, stratum Wikipedia (en), donor_chain (m = 7): budget rung 1
| rung | n_off | mean_contributing | clean_prefix_fraction | testable | label | d_hat | interval | half_width | draws_above_X | unconditional |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 0.0000 | 64.0000 | 1.0000 | True | holds | 0.0000 | [+0.0000, +0.0000] | 0.0000 | 0/8 | 0.0000 |
| 2 | 0.2500 | 56.0000 | 0.8655 | False | not testable with these donors |  |  |  |  | 0.0383 |
| 3 | 2.5000 | 47.7500 | 0.5035 | False | not testable with these donors |  |  |  |  | 0.0450 |
| 4 | 5.6250 | 49.8750 | 0.2937 | False | not testable with these donors |  |  |  |  | 0.0119 |
| 5 | 21.7500 | 10.8750 | 0.0125 | False | not testable with these donors |  |  |  |  | 0.1001 |
| 6 | 60.6250 | 0.0000 | 0.0001 | False | not testable with these donors |  |  |  |  | 0.2270 |
| 7 | 104.5000 | 0.0000 | 0.0000 | False | not testable with these donors |  |  |  |  | 0.3418 |

tau_q = 0, stratum Wikipedia (en), sub_rung_chain (m = 3): budget rung None
| rung | n_off | mean_contributing | clean_prefix_fraction | testable | label | d_hat | interval | half_width | draws_above_X | unconditional |
|---|---|---|---|---|---|---|---|---|---|---|
| S4 | 4.0000 | 49.0000 | 0.1089 | False | not testable with these donors | None | None | None | None | 0.0036 |
| S16 | 16.0000 | 29.0000 | 0.0269 | False | not testable with these donors | None | None | None | None | 0.0457 |
| S64 | 64.0000 | 0.0000 | 0.0000 | False | not testable with these donors | None | None | None | None | 0.1264 |

## 6. The labels of curves 1 to 5
- Curve 1: **fails** (j_det 3, j_mat 3; half-widths from 0.0685 to 0.1337)
- Curve 2 (draw 0; all draws above): **fails** (j_det 1, j_mat 1; half-widths from 0.0043 to 0.0701)
- Curve 3 on other: positive control pass; at tau_q = 0.1: donor_chain: budget rung None, labels {'1': 'not testable with these donors', '2': 'not testable with these donors', '3': 'not testable with these donors', '4': 'not testable with these donors', '5': 'not testable with these donors', '6': 'not testable with these donors', '7': 'not testable with these donors'}; at tau_q = 0: donor_chain: budget rung None
- Curve 4 on other: positive control pass; at tau_q = 0.1: donor_chain: budget rung 7, labels {'1': 'holds', '2': 'holds', '3': 'holds', '4': 'holds', '5': 'holds', '6': 'holds', '7': 'holds'}; sub_rung_chain: budget rung S64, labels {'S4': 'holds', 'S16': 'holds', 'S64': 'holds'}; at tau_q = 0: donor_chain: budget rung 7; sub_rung_chain: budget rung S64
- Curve 5 on all: positive control pass; at tau_q = 0.1: donor_chain: budget rung None, labels {'1': 'not testable with these donors', '2': 'not testable with these donors', '3': 'not testable with these donors', '4': 'not testable with these donors', '5': 'not testable with these donors', '6': 'not testable with these donors', '7': 'not testable with these donors'}; at tau_q = 0: donor_chain: budget rung None

## 7. Everything else
### The never-named chain (`never_named_hard/E/D_unif/tau0.1/ones/incl/ctl-none`), D(n) against n with the linear and quadratic lines; whole set n = 32551, D = 7.2914; alive control present: True
| rung | n_erased | n_per_draw | D_mean | draw_spread_sd | linear_prediction | quadratic_prediction | alive_control_mean | ratio_to_alive_control |
|---|---|---|---|---|---|---|---|---|
| 1 | 60.7500 | 83 71 78 58 94 51 14 37 | 0.0024 | 0.0011 | 0.0027 | 0.0000 | 0.6806 | 0.0035 |
| 2 | 392.5000 | 441 427 365 565 380 302 315 345 | 0.0175 | 0.0048 | 0.0175 | 0.0002 | 2.8455 | 0.0061 |
| 3 | 1792.0000 | 1855 1770 1817 1856 1587 1915 1770 1766 | 0.1021 | 0.0077 | 0.0799 | 0.0049 | 7.6220 | 0.0134 |
| 4 | 2483.6250 | 3605 2046 2795 489 2494 3012 2833 2595 | 0.1604 | 0.0688 | 0.1107 | 0.0095 | 7.3509 | 0.0218 |
| 5 | 4394.3750 | 4700 4415 4654 4431 4336 4376 4239 4004 | 0.3402 | 0.0329 | 0.1958 | 0.0297 | 8.6992 | 0.0391 |
| 6 | 5516.0000 | 5644 5431 5500 5453 5533 5633 5497 5437 | 0.4766 | 0.0245 | 0.2458 | 0.0468 | 9.8513 | 0.0484 |
| 7 | 6053.1250 | 6104 5979 6030 6020 6084 6028 6120 6060 | 0.5496 | 0.0284 | 0.2698 | 0.0564 | 9.9938 | 0.0550 |
| B50 | 16275.0000 | 16275 16275 16275 16275 16275 16275 16275 16275 | 3.1641 | 0.0565 | 0.7253 | 0.4078 |  |  |
| B75 | 24413.0000 | 24413 24413 24413 24413 24413 24413 24413 24413 | 5.9248 | 0.2394 | 1.0880 | 0.9176 |  |  |
| 8 | 32551.0000 | 32551 | 7.2914 |  | 1.4507 | 1.6313 | 10.0106 | 0.7284 |

The family's rung-8 cells under the one-cell rule (the whole set with Delta included and excluded, the strict cell at tau = 0), the conditional figure at both tau_q:
| cell | n_erased | unconditional | testable_0.1 | d_hat_0.1 | interval_0.1 | label_0.1 | testable_0 | d_hat_0 | interval_0 | label_0 |
|---|---|---|---|---|---|---|---|---|---|---|
| never_named_hard/E/D_unif/tau0.1/ones/incl/ctl-none | 32551.0000 | 7.2914 | True | 7.2861 | [+7.2425, +7.3309] | fails | False |  |  | not testable with these donors |
| never_named_hard/E/D_unif/tau0.1/ones/excl/ctl-none | 32551.0000 | 7.2966 | True | 7.2913 | [+7.2477, +7.3361] | fails | False |  |  | not testable with these donors |
| never_named_hard/E/D_unif/tau0/ones/incl/ctl-none | 6456.0000 | 0.5563 | True | 0.5561 | [+0.5442, +0.5691] | fails | True | 0.5377 | [+0.5242, +0.5524] | fails |

### The tau = 0 union and its plain control, read as any union chain
## The tau = 0 union under r = 0 on E
Chain `union/E/D_unif/tau0/r0/excl/ctl-none`; rung 0 mean 4.6920; m = 8 rungs compared; **label: fails** (at m = 8: fails); j_det = 3, j_mat = 3, first repair rung = 1; per draw: k0: det 3, mat 3, k1: det 3, mat 3, k2: det 2, mat 2, k3: det 2, mat 2, k4: det 2, mat 2, k5: det 2, mat 2, k6: det 3, mat 3, k7: det 3, mat 3

| rung | n_on | mean_sigma | overlap | mean_kl | excess | interval | half_width | two_level | draws_positive | fraction_seq_above_X | detected | material | repair | differs_at_m_8 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 65.5000 | 57.8929 | 0.0199 | 4.0461 | -0.6458 | [-0.7192, -0.5807] | 0.0693 | [-0.8952, -0.3741] | 0/8 | 0.0342 | False | False | True | False |
| 2 | 437.1250 | 418.5112 | 0.0890 | 5.0718 | 0.3799 | [+0.2647, +0.4857] | 0.1105 | [-0.3253, +1.0091] | 5/8 | 0.7646 | False | False | False | False |
| 3 | 1982.1250 | 1944.9861 | 0.3529 | 5.4770 | 0.7850 | [+0.6608, +0.9036] | 0.1214 | [+0.4992, +1.1535] | 8/8 | 0.8301 | True | True | False | False |
| 4 | 3015.8750 | 2979.1709 | 0.4568 | 7.2948 | 2.6029 | [+2.4635, +2.7337] | 0.1351 | [+2.1394, +2.9581] | 8/8 | 0.9521 | True | True | False | False |
| 5 | 5793.3750 | 5747.1211 | 0.7533 | 7.3477 | 2.6557 | [+2.5194, +2.7852] | 0.1329 | [+2.5154, +2.7928] | 8/8 | 0.9551 | True | True | False | False |
| 6 | 9429.6250 | 9382.0586 | 0.6659 | 7.2604 | 2.5685 | [+2.4290, +2.6997] | 0.1354 | [+2.4113, +2.7258] | 8/8 | 0.9512 | True | True | False | False |
| 7 | 16367.7500 | 16320.1250 | 0.5800 | 4.8114 | 0.1195 | [-0.0193, +0.2524] | 0.1359 | [-0.0618, +0.2942] | 5/8 | 0.6045 | False | False | False | False |
| 8 | 32456.0000 | 32408.3750 | 0.8408 | 0.5660 | -4.1259 | [-4.2836, -3.9782] | 0.1527 | [-4.2836, -3.9782] | 0/1 | 0.0000 | False | False | True | False |

Paired union minus control on the same sequence, draw, and rung (95 percent uncorrected), with the pre-reads' overlap of the two sets: rung 1: -0.4105 [-0.4526, -0.3712] (overlap 0.020); rung 2: +1.3948 [+1.3632, +1.4260] (overlap 0.089); rung 3: +1.9040 [+1.8818, +1.9258] (overlap 0.353); rung 4: +2.1136 [+2.0881, +2.1397] (overlap 0.457)
Rung 4 minus rung 3 at nearly the same count (diffuse against concentrated), paired: +1.8179 [+1.7853, +1.8508].
Rung 4 (one donor sequence): excess +2.6029 [+2.4635, +2.7337], fraction of sequences with excess above X 0.952.
Per-rung excess by reader label on E (each label's own resample, the curve's m):
| label | n | rung | excess | interval | half_width | detected | material |
|---|---|---|---|---|---|---|---|
| code | 120 | 1 | -1.4588 | [-1.8071, -1.1616] | 0.3227 | False | False |
| code | 120 | 2 | -1.2414 | [-1.7469, -0.8117] | 0.4676 | False | False |
| code | 120 | 3 | -0.6780 | [-1.2497, -0.1647] | 0.5425 | False | False |
| code | 120 | 4 | 1.3556 | [+0.7272, +1.8948] | 0.5838 | True | True |
| code | 120 | 5 | 1.4321 | [+0.8038, +1.9701] | 0.5832 | True | True |
| code | 120 | 6 | 1.2948 | [+0.6622, +1.8295] | 0.5837 | True | True |
| code | 120 | 7 | -1.4829 | [-2.0833, -0.9539] | 0.5647 | False | False |
| code | 120 | 8 | -6.1236 | [-6.8611, -5.4808] | 0.6902 | False | False |
| mixed | 27 | 1 | -1.1523 | [-1.6607, -0.7766] | 0.4421 | False | False |
| mixed | 27 | 2 | -0.7099 | [-1.4126, -0.1520] | 0.6303 | False | False |
| mixed | 27 | 3 | -0.2671 | [-1.1027, +0.4098] | 0.7562 | False | False |
| mixed | 27 | 4 | 1.6561 | [+0.7908, +2.3787] | 0.7940 | True | True |
| mixed | 27 | 5 | 1.7338 | [+0.8486, +2.4644] | 0.8079 | True | True |
| mixed | 27 | 6 | 1.6171 | [+0.7317, +2.3418] | 0.8051 | True | True |
| mixed | 27 | 7 | -1.0351 | [-1.8954, -0.3434] | 0.7760 | False | False |
| mixed | 27 | 8 | -5.1678 | [-6.1291, -4.3980] | 0.8655 | False | False |
| other | 158 | 1 | -0.5959 | [-0.8705, -0.3844] | 0.2430 | False | False |
| other | 158 | 2 | 0.6193 | [+0.1816, +0.9740] | 0.3962 | False | False |
| other | 158 | 3 | 1.2339 | [+0.7512, +1.6418] | 0.4453 | True | True |
| other | 158 | 4 | 3.4034 | [+2.8574, +3.9160] | 0.5293 | True | True |
| other | 158 | 5 | 3.4106 | [+2.8693, +3.9086] | 0.5196 | True | True |
| other | 158 | 6 | 3.3741 | [+2.8273, +3.8779] | 0.5253 | True | True |
| other | 158 | 7 | 0.9345 | [+0.3791, +1.4303] | 0.5256 | True | True |
| other | 158 | 8 | -3.6537 | [-4.2088, -3.1677] | 0.5206 | False | False |
| prose | 719 | 1 | -0.5021 | [-0.5562, -0.4617] | 0.0472 | False | False |
| prose | 719 | 2 | 0.6388 | [+0.5612, +0.7033] | 0.0710 | True | True |
| prose | 719 | 3 | 0.9700 | [+0.8857, +1.0438] | 0.0791 | True | True |
| prose | 719 | 4 | 2.6707 | [+2.5728, +2.7583] | 0.0928 | True | True |
| prose | 719 | 5 | 2.7287 | [+2.6313, +2.8167] | 0.0927 | True | True |
| prose | 719 | 6 | 2.6397 | [+2.5401, +2.7300] | 0.0950 | True | True |
| prose | 719 | 7 | 0.2512 | [+0.1569, +0.3307] | 0.0869 | True | True |
| prose | 719 | 8 | -3.8572 | [-3.9702, -3.7570] | 0.1066 | False | False |

Paired union minus control by reader label at rungs 1 to 4 and 5a (each label's own resample, uncorrected 95 percent), the control's per-label excess beside:
| label | n | rung | union_minus_control | interval_uncorrected | half_width | control_excess | control_interval_uncorrected |
|---|---|---|---|---|---|---|---|
| code | 120 | 1 | -0.9975 | [-1.2057, -0.8112] | 0.1973 | -0.4613 | [-0.5101, -0.4152] |
| code | 120 | 2 | 0.9268 | [+0.7763, +1.0638] | 0.1437 | -2.1683 | [-2.3950, -1.9565] |
| code | 120 | 3 | 1.6187 | [+1.5322, +1.7056] | 0.0867 | -2.2967 | [-2.6485, -1.9702] |
| code | 120 | 4 | 2.1282 | [+2.0272, +2.2267] | 0.0997 | -0.7726 | [-1.1192, -0.4516] |
| mixed | 27 | 1 | -0.8142 | [-1.1084, -0.5696] | 0.2694 | -0.3380 | [-0.3966, -0.2858] |
| mixed | 27 | 2 | 0.9094 | [+0.7439, +1.0658] | 0.1609 | -1.6193 | [-1.9603, -1.3339] |
| mixed | 27 | 3 | 1.8034 | [+1.6727, +1.9280] | 0.1277 | -2.0705 | [-2.5562, -1.6551] |
| mixed | 27 | 4 | 2.0511 | [+1.9153, +2.1937] | 0.1392 | -0.3950 | [-0.9200, +0.0520] |
| other | 158 | 1 | -0.3788 | [-0.5342, -0.2455] | 0.1444 | -0.2171 | [-0.2513, -0.1868] |
| other | 158 | 2 | 1.6489 | [+1.5290, +1.7629] | 0.1170 | -1.0296 | [-1.2191, -0.8646] |
| other | 158 | 3 | 1.7623 | [+1.6884, +1.8354] | 0.0735 | -0.5284 | [-0.8378, -0.2494] |
| other | 158 | 4 | 2.3023 | [+2.1973, +2.4076] | 0.1052 | 1.1011 | [+0.7747, +1.3988] |
| prose | 719 | 1 | -0.3043 | [-0.3336, -0.2792] | 0.0272 | -0.1978 | [-0.2054, -0.1908] |
| prose | 719 | 2 | 1.4353 | [+1.4123, +1.4575] | 0.0226 | -0.7965 | [-0.8327, -0.7634] |
| prose | 719 | 3 | 1.9865 | [+1.9682, +2.0047] | 0.0183 | -1.0164 | [-1.0650, -0.9714] |
| prose | 719 | 4 | 2.0721 | [+2.0495, +2.0943] | 0.0224 | 0.5986 | [+0.5421, +0.6512] |

## Its plain control
Chain `union/E/D_unif/tau0/r0/excl/ctl-plain`; rung 0 mean 4.6920; m = 8 rungs compared; **label: fails** (at m = 8: fails); j_det = 5, j_mat = 5, first repair rung = 1; per draw: k0: det 4, mat 4, k1: det 4, mat 4, k2: det 4, mat 4, k3: det 5, mat 5, k4: det 5, mat 5, k5: det 5, mat 5, k6: det 4, mat 4, k7: det 4, mat 4

| rung | n_on | mean_sigma | overlap | mean_kl | excess | interval | half_width | two_level | draws_positive | fraction_seq_above_X | detected | material | repair | differs_at_m_8 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 65.5000 | 64.7890 | 0.0199 | 4.4566 | -0.2354 | [-0.2505, -0.2215] | 0.0145 | [-0.3774, -0.0939] | 0/8 | 0.0010 | False | False | True | False |
| 2 | 437.1250 | 432.5541 | 0.0890 | 3.6770 | -1.0149 | [-1.0945, -0.9448] | 0.0748 | [-1.2526, -0.7928] | 0/8 | 0.0020 | False | False | True | False |
| 3 | 1982.1250 | 1964.4189 | 0.3529 | 3.5730 | -1.1190 | [-1.2289, -1.0175] | 0.1057 | [-1.4778, -0.7456] | 0/8 | 0.0840 | False | False | True | False |
| 4 | 3015.8750 | 2991.1953 | 0.4568 | 5.1812 | 0.4892 | [+0.3721, +0.5972] | 0.1125 | [-0.3033, +1.3021] | 6/8 | 0.7617 | False | False | False | False |
| 5 | 5793.3750 | 5749.0244 | 0.7533 | 6.5438 | 1.8518 | [+1.7141, +1.9822] | 0.1341 | [+1.4342, +2.3093] | 8/8 | 0.9258 | True | True | False | False |
| 6 | 9429.6250 | 9382.0098 | 0.6659 | 7.2785 | 2.5865 | [+2.4491, +2.7156] | 0.1333 | [+2.4411, +2.7300] | 8/8 | 0.9531 | True | True | False | False |
| 7 | 16367.7500 | 16320.1250 | 0.5800 | 5.0592 | 0.3673 | [+0.2290, +0.5025] | 0.1368 | [+0.0907, +0.6643] | 7/8 | 0.7021 | True | True | False | False |
| 8 | 32456.0000 | 32408.3750 | 0.8408 | 0.5887 | -4.1032 | [-4.2625, -3.9549] | 0.1538 | [-4.2625, -3.9549] | 0/1 | 0.0000 | False | False | True | False |
Rung 4 (one donor sequence): excess +0.4892 [+0.3721, +0.5972], fraction of sequences with excess above X 0.762.

The control's overflow into the dead set per rung (the matched count exceeds the alive set from rung 5; mean over draws of the summed per-module overflow, from the pre-reads): rung 1: 0 of n_on 66; rung 2: 0 of n_on 437; rung 3: 0 of n_on 1982; rung 4: 0 of n_on 3016; rung 5: 127 of n_on 5793; rung 6: 3081 of n_on 9430; rung 7: 10013 of n_on 16368; rung 8: 26101 of n_on 32456

Reference lines beside the chain (its rung 8 is the complement of the strict set: everything the pool labels above 0 pinned at 1, the strict 5,336 at their labels):
| line | cell | n_on | mean_kl | se | excess_over_unmasked |
|---|---|---|---|---|---|
| strict cell: the strict set (g = 0 at every pool position) erased, Delta included | control/E/never_named_hard/D_unif/tau0/ones/incl/k0/r8 | 6456 | 0.5568 | 0.0063 | 0.5454 |
| never-named rung 8: the never-named set at tau = 0.1 erased, Delta included | control/E/never_named_hard/D_unif/tau0.1/ones/incl/k0/r8 | 32551 | 7.2920 | 0.0224 | 7.2806 |
| never-named rung 8, Delta excluded | control/E/never_named_hard/D_unif/tau0.1/ones/excl/k0/r8 | 32551 | 7.3080 | 0.0224 | 7.2966 |
| this chain's rung 8: everything the pool labels above 0 pinned at 1, the strict set at its labels, Delta excluded | control/E/union/D_unif/tau0/r0/excl/k0/r8 | 32456 | 0.5660 | 0.0063 | 0.5546 |
| unmasked | control/E/ref/unmasked | 0 | 0.0114 | 0.0002 | 0.0000 |
| unmasked, Delta included | control/E/ref/unmasked_delta | 0 | 0.0006 | 0.0000 | -0.0108 |
| importances-as-masks (this chain's rung 0) | control/E/ref/importances | 0 | 4.6920 | 0.0569 | 4.6806 |

### The level cells: the alive set at s + (1 - s) g, the never-named set at its labels or at 1, beside their four corners
| s | never_named_at | corner | mean_kl | se | mean_sigma | excess_over_path_rung_0 | path_rung_0 | footprint_labels_minus_one | footprint_interval |
|---|---|---|---|---|---|---|---|---|---|
| 0.0000 | labels | True | 4.6920 | 0.0569 |  | 0.0000 | importances | -5.3173 | [-5.4312, -5.1979] |
| 0.0000 | one | True | 10.0093 | 0.0216 | 6313.3740 | 9.9979 | unmasked |  |  |
| 0.2500 | labels | False | 2.1535 | 0.0184 | 1578.3435 | -2.5385 | importances | -4.5185 | [-4.5658, -4.4719] |
| 0.2500 | one | False | 6.6719 | 0.0197 | 4735.0305 | 6.6605 | unmasked |  |  |
| 0.5000 | labels | False | 3.2113 | 0.0256 | 3156.6870 | -1.4807 | importances | -0.3738 | [-0.4157, -0.3310] |
| 0.5000 | one | False | 3.5850 | 0.0202 | 3156.6870 | 3.5737 | unmasked |  |  |
| 0.7500 | labels | False | 6.5688 | 0.0231 | 4735.0305 | 1.8768 | importances | 6.1221 | [+6.0774, +6.1681] |
| 0.7500 | one | False | 0.4467 | 0.0035 | 1578.3435 | 0.4353 | unmasked |  |  |
| 1.0000 | labels | True | 7.3079 | 0.0224 | 6313.3740 | 2.6160 | importances | 7.2965 | [+7.2529, +7.3410] |
| 1.0000 | one | True | 0.0114 | 0.0002 |  | 0.0000 | unmasked |  |  |

The footprint is L(s, labels) - L(s, 1), paired per sequence with the shared resample (uncorrected 95 percent). The soft-erase chain's points at their own switched fraction (s = 1 - sigma_j / sigma_8), drawn on fig5:
| rung | switched_fraction | s_equivalent | mean_kl | n_on |
|---|---|---|---|---|
| 1 | 0.0085 | 0.9915 | 1.2015 | 60.7500 |
| 2 | 0.0593 | 0.9407 | 4.0220 | 392.5000 |
| 3 | 0.2781 | 0.7219 | 8.2464 | 1792.0000 |
| 4 | 0.3877 | 0.6123 | 9.0270 | 2483.6250 |
| 5 | 0.6888 | 0.3112 | 9.8275 | 4394.3750 |
| 6 | 0.8662 | 0.1338 | 10.0210 | 5516.0000 |
| 7 | 0.9512 | 0.0488 | 9.9872 | 6053.1250 |
| 8 | 1.0000 | 0.0000 | 10.0093 | 6361.0000 |

### Delta gaps per rung (included minus excluded, mean over draws and sequences)
| chain | rung | delta_gap_mean |
|---|---|---|
| never_named_hard/E/D_unif/tau0.1/ones/excl/ctl-none | 8 | -0.0160 |

### E8: hard-zero damage at least soft-erase damage on the same sequences
| chain | rung | soft_erase_chain | delta_settings | fraction_sequences_hard_zero_at_least_soft | mean_hard_zero | mean_soft |
|---|---|---|---|---|---|---|
| hard_zero/E/D_unif/tau0.1/ones/incl/ctl-none | 1 | soft_erase/E/D_unif/tau0.1/r1/excl/ctl-none | differ (each excess over its own rung 0) | 1.0000 | 6.3587 | 1.1901 |
| hard_zero/E/D_unif/tau0.1/ones/incl/ctl-none | 2 | soft_erase/E/D_unif/tau0.1/r1/excl/ctl-none | differ (each excess over its own rung 0) | 0.9999 | 7.7161 | 4.0106 |
| hard_zero/E/D_unif/tau0.1/ones/incl/ctl-none | 3 | soft_erase/E/D_unif/tau0.1/r1/excl/ctl-none | differ (each excess over its own rung 0) | 0.5983 | 8.6089 | 8.2350 |
| hard_zero/E/D_unif/tau0.1/ones/incl/ctl-none | 4 | soft_erase/E/D_unif/tau0.1/r1/excl/ctl-none | differ (each excess over its own rung 0) | 0.3549 | 9.3136 | 9.0156 |
| hard_zero/E/D_unif/tau0.1/ones/incl/ctl-none | 5 | soft_erase/E/D_unif/tau0.1/r1/excl/ctl-none | differ (each excess over its own rung 0) | 0.6201 | 10.2618 | 9.8161 |
| hard_zero/E/D_unif/tau0.1/ones/incl/ctl-none | 6 | soft_erase/E/D_unif/tau0.1/r1/excl/ctl-none | differ (each excess over its own rung 0) | 0.5331 | 10.3238 | 10.0096 |
| hard_zero/E/D_unif/tau0.1/ones/incl/ctl-none | 7 | soft_erase/E/D_unif/tau0.1/r1/excl/ctl-none | differ (each excess over its own rung 0) | 0.4784 | 10.1139 | 9.9758 |
| hard_zero/E/D_unif/tau0.1/ones/incl/ctl-none | 8 | soft_erase/E/D_unif/tau0.1/r1/excl/ctl-none | differ (each excess over its own rung 0) | 0.4463 | 9.9932 | 9.9979 |
| hard_zero/E/D_unif/tau0.1/ones/incl/ctl-plain | 1 | soft_erase/E/D_unif/tau0.1/r1/excl/ctl-plain | differ (each excess over its own rung 0) | 0.9613 | 0.6806 | 0.0540 |
| hard_zero/E/D_unif/tau0.1/ones/incl/ctl-plain | 2 | soft_erase/E/D_unif/tau0.1/r1/excl/ctl-plain | differ (each excess over its own rung 0) | 0.9999 | 2.8455 | 0.3674 |
| hard_zero/E/D_unif/tau0.1/ones/incl/ctl-plain | 3 | soft_erase/E/D_unif/tau0.1/r1/excl/ctl-plain | differ (each excess over its own rung 0) | 1.0000 | 7.6220 | 2.1620 |
| hard_zero/E/D_unif/tau0.1/ones/incl/ctl-plain | 4 | soft_erase/E/D_unif/tau0.1/r1/excl/ctl-plain | differ (each excess over its own rung 0) | 0.9982 | 7.3509 | 3.9688 |
| hard_zero/E/D_unif/tau0.1/ones/incl/ctl-plain | 5 | soft_erase/E/D_unif/tau0.1/r1/excl/ctl-plain | differ (each excess over its own rung 0) | 0.5493 | 8.6992 | 8.3513 |
| hard_zero/E/D_unif/tau0.1/ones/incl/ctl-plain | 6 | soft_erase/E/D_unif/tau0.1/r1/excl/ctl-plain | differ (each excess over its own rung 0) | 0.4965 | 9.8513 | 9.6606 |
| hard_zero/E/D_unif/tau0.1/ones/incl/ctl-plain | 7 | soft_erase/E/D_unif/tau0.1/r1/excl/ctl-plain | differ (each excess over its own rung 0) | 0.4595 | 9.9938 | 10.0609 |
| hard_zero/E/D_unif/tau0.1/ones/incl/ctl-plain | 8 | soft_erase/E/D_unif/tau0.1/r1/excl/ctl-plain | differ (each excess over its own rung 0) | 0.4502 | 10.0106 | 9.9903 |
| hard_zero/E_lab/D_code/tau0.1/ones/incl/ctl-none | 1 | soft_erase/E_lab/D_code/tau0.1/r1/excl/ctl-none | differ (each excess over its own rung 0) | 1.0000 | 6.0232 | 1.2548 |
| hard_zero/E_lab/D_code/tau0.1/ones/incl/ctl-none | 2 | soft_erase/E_lab/D_code/tau0.1/r1/excl/ctl-none | differ (each excess over its own rung 0) | 0.9995 | 7.3513 | 3.9526 |
| hard_zero/E_lab/D_code/tau0.1/ones/incl/ctl-none | 3 | soft_erase/E_lab/D_code/tau0.1/r1/excl/ctl-none | differ (each excess over its own rung 0) | 0.6594 | 8.5906 | 8.0008 |
| hard_zero/E_lab/D_code/tau0.1/ones/incl/ctl-none | 4 | soft_erase/E_lab/D_code/tau0.1/r1/excl/ctl-none | differ (each excess over its own rung 0) | 0.4541 | 9.7867 | 9.7522 |
| hard_zero/E_lab/D_code/tau0.1/ones/incl/ctl-none | 5 | soft_erase/E_lab/D_code/tau0.1/r1/excl/ctl-none | differ (each excess over its own rung 0) | 0.6111 | 10.4386 | 10.0412 |
| hard_zero/E_lab/D_code/tau0.1/ones/incl/ctl-none | 6 | soft_erase/E_lab/D_code/tau0.1/r1/excl/ctl-none | differ (each excess over its own rung 0) | 0.7888 | 10.9471 | 9.9796 |
| hard_zero/E_lab/D_code/tau0.1/ones/incl/ctl-none | 7 | soft_erase/E_lab/D_code/tau0.1/r1/excl/ctl-none | differ (each excess over its own rung 0) | 0.8020 | 11.0184 | 9.9411 |
| hard_zero/E_lab/D_code/tau0.1/ones/incl/ctl-none | 8 | soft_erase/E_lab/D_code/tau0.1/r1/excl/ctl-none | differ (each excess over its own rung 0) | 0.7637 | 10.8550 | 9.8668 |
| hard_zero/E_lab/D_code/tau0.1/ones/incl/ctl-plain | 1 | soft_erase/E_lab/D_code/tau0.1/r1/excl/ctl-plain | differ (each excess over its own rung 0) | 0.9426 | 0.7870 | 0.0603 |
| hard_zero/E_lab/D_code/tau0.1/ones/incl/ctl-plain | 2 | soft_erase/E_lab/D_code/tau0.1/r1/excl/ctl-plain | differ (each excess over its own rung 0) | 1.0000 | 2.7689 | 0.4022 |
| hard_zero/E_lab/D_code/tau0.1/ones/incl/ctl-plain | 3 | soft_erase/E_lab/D_code/tau0.1/r1/excl/ctl-plain | differ (each excess over its own rung 0) | 1.0000 | 7.6289 | 2.0369 |
| hard_zero/E_lab/D_code/tau0.1/ones/incl/ctl-plain | 4 | soft_erase/E_lab/D_code/tau0.1/r1/excl/ctl-plain | differ (each excess over its own rung 0) | 0.9990 | 8.1469 | 4.2446 |
| hard_zero/E_lab/D_code/tau0.1/ones/incl/ctl-plain | 5 | soft_erase/E_lab/D_code/tau0.1/r1/excl/ctl-plain | differ (each excess over its own rung 0) | 0.8391 | 8.7546 | 7.2211 |
| hard_zero/E_lab/D_code/tau0.1/ones/incl/ctl-plain | 6 | soft_erase/E_lab/D_code/tau0.1/r1/excl/ctl-plain | differ (each excess over its own rung 0) | 0.3870 | 9.1026 | 9.3728 |
| hard_zero/E_lab/D_code/tau0.1/ones/incl/ctl-plain | 7 | soft_erase/E_lab/D_code/tau0.1/r1/excl/ctl-plain | differ (each excess over its own rung 0) | 0.4861 | 9.9335 | 9.8048 |
| hard_zero/E_lab/D_code/tau0.1/ones/incl/ctl-plain | 8 | soft_erase/E_lab/D_code/tau0.1/r1/excl/ctl-plain | differ (each excess over its own rung 0) | 0.8809 | 10.5928 | 9.6571 |

### The donor-side pass (excess over the rounded reference on the donor sequences)
none

### The domain comparisons per stratum: the erase against its own control, paired on the sequence with the stratum's resample; never averaged over strata
| chain | rung | stratum | n | erase_unconditional | control_unconditional | paired_erase_minus_control | interval | conditional_d_0.1 | n_contributing_mean |
|---|---|---|---|---|---|---|---|---|---|
| hard_zero/E_lab/D_code/tau0.1/ones/incl/ctl-none | 1 | Github | 256 | 6.5508 | 0.8496 | 5.7012 | [+5.5711, +5.8277] |  | 0.0000 |
| hard_zero/E_lab/D_code/tau0.1/ones/incl/ctl-none | 1 | other | 256 | 5.4955 | 0.7244 | 4.7712 | [+4.6987, +4.8453] |  | 0.0000 |
| hard_zero/E_lab/D_code/tau0.1/ones/incl/ctl-none | 1 | ArXiv | 64 | 5.6282 | 0.7126 | 4.9156 | [+4.7929, +5.0352] |  | 0.0000 |
| hard_zero/E_lab/D_code/tau0.1/ones/incl/ctl-none | 1 | Pile-CC | 64 | 4.9374 | 0.7000 | 4.2374 | [+4.1436, +4.3339] |  | 0.0000 |
| hard_zero/E_lab/D_code/tau0.1/ones/incl/ctl-none | 1 | StackExchange | 64 | 5.9441 | 0.7280 | 5.2161 | [+5.0632, +5.3731] |  | 0.0000 |
| hard_zero/E_lab/D_code/tau0.1/ones/incl/ctl-none | 1 | Wikipedia (en) | 64 | 5.4725 | 0.7569 | 4.7156 | [+4.6375, +4.8014] |  | 0.0000 |
| hard_zero/E_lab/D_code/tau0.1/ones/incl/ctl-none | 2 | Github | 256 | 7.9854 | 3.0050 | 4.9804 | [+4.8618, +5.0963] |  | 0.0000 |
| hard_zero/E_lab/D_code/tau0.1/ones/incl/ctl-none | 2 | other | 256 | 6.7172 | 2.5328 | 4.1844 | [+4.1111, +4.2583] |  | 0.0000 |
| hard_zero/E_lab/D_code/tau0.1/ones/incl/ctl-none | 2 | ArXiv | 64 | 6.8532 | 2.5363 | 4.3169 | [+4.2060, +4.4233] |  | 0.0000 |
| hard_zero/E_lab/D_code/tau0.1/ones/incl/ctl-none | 2 | Pile-CC | 64 | 6.0276 | 2.3838 | 3.6438 | [+3.5551, +3.7324] |  | 0.0000 |
| hard_zero/E_lab/D_code/tau0.1/ones/incl/ctl-none | 2 | StackExchange | 64 | 7.2252 | 2.6025 | 4.6226 | [+4.4612, +4.7910] |  | 0.0000 |
| hard_zero/E_lab/D_code/tau0.1/ones/incl/ctl-none | 2 | Wikipedia (en) | 64 | 6.7630 | 2.6086 | 4.1544 | [+4.0625, +4.2505] |  | 0.0000 |
| hard_zero/E_lab/D_code/tau0.1/ones/incl/ctl-none | 3 | Github | 256 | 8.8307 | 8.1311 | 0.6997 | [+0.6531, +0.7447] |  | 0.0000 |
| hard_zero/E_lab/D_code/tau0.1/ones/incl/ctl-none | 3 | other | 256 | 8.3506 | 7.1267 | 1.2239 | [+1.1670, +1.2803] |  | 0.0000 |
| hard_zero/E_lab/D_code/tau0.1/ones/incl/ctl-none | 3 | ArXiv | 64 | 8.9362 | 7.5045 | 1.4317 | [+1.3322, +1.5317] |  | 0.0000 |
| hard_zero/E_lab/D_code/tau0.1/ones/incl/ctl-none | 3 | Pile-CC | 64 | 7.8852 | 6.4789 | 1.4062 | [+1.3024, +1.5090] |  | 0.0000 |
| hard_zero/E_lab/D_code/tau0.1/ones/incl/ctl-none | 3 | StackExchange | 64 | 8.3684 | 7.4769 | 0.8915 | [+0.8059, +0.9775] |  | 0.0000 |
| hard_zero/E_lab/D_code/tau0.1/ones/incl/ctl-none | 3 | Wikipedia (en) | 64 | 8.2125 | 7.0464 | 1.1661 | [+1.0579, +1.2734] |  | 0.0000 |
| hard_zero/E_lab/D_code/tau0.1/ones/incl/ctl-none | 4 | Github | 256 | 10.3561 | 8.5912 | 1.7650 | [+1.6592, +1.8680] |  | 0.0000 |
| hard_zero/E_lab/D_code/tau0.1/ones/incl/ctl-none | 4 | other | 256 | 9.2173 | 7.7025 | 1.5148 | [+1.4642, +1.5653] |  | 0.0000 |
| hard_zero/E_lab/D_code/tau0.1/ones/incl/ctl-none | 4 | ArXiv | 64 | 9.7921 | 8.1548 | 1.6373 | [+1.5590, +1.7128] |  | 0.0000 |
| hard_zero/E_lab/D_code/tau0.1/ones/incl/ctl-none | 4 | Pile-CC | 64 | 8.5503 | 7.1235 | 1.4267 | [+1.3429, +1.5124] |  | 0.0000 |
| hard_zero/E_lab/D_code/tau0.1/ones/incl/ctl-none | 4 | StackExchange | 64 | 9.6348 | 7.9189 | 1.7159 | [+1.5924, +1.8448] |  | 0.0000 |
| hard_zero/E_lab/D_code/tau0.1/ones/incl/ctl-none | 4 | Wikipedia (en) | 64 | 8.8920 | 7.6129 | 1.2791 | [+1.2091, +1.3476] |  | 0.0000 |
| hard_zero/E_lab/D_code/tau0.1/ones/incl/ctl-none | 5 | Github | 256 | 11.1749 | 9.3157 | 1.8592 | [+1.7665, +1.9500] |  | 0.0000 |
| hard_zero/E_lab/D_code/tau0.1/ones/incl/ctl-none | 5 | other | 256 | 9.7023 | 8.1934 | 1.5089 | [+1.4652, +1.5532] |  | 0.0000 |
| hard_zero/E_lab/D_code/tau0.1/ones/incl/ctl-none | 5 | ArXiv | 64 | 10.3606 | 8.7237 | 1.6368 | [+1.5429, +1.7246] |  | 0.0000 |
| hard_zero/E_lab/D_code/tau0.1/ones/incl/ctl-none | 5 | Pile-CC | 64 | 8.9479 | 7.5161 | 1.4318 | [+1.3586, +1.5047] |  | 0.0000 |
| hard_zero/E_lab/D_code/tau0.1/ones/incl/ctl-none | 5 | StackExchange | 64 | 10.1143 | 8.4998 | 1.6145 | [+1.5075, +1.7226] |  | 0.0000 |
| hard_zero/E_lab/D_code/tau0.1/ones/incl/ctl-none | 5 | Wikipedia (en) | 64 | 9.3866 | 8.0342 | 1.3524 | [+1.3014, +1.4063] |  | 0.0000 |
| hard_zero/E_lab/D_code/tau0.1/ones/incl/ctl-none | 6 | Github | 256 | 11.7354 | 9.6439 | 2.0915 | [+2.0329, +2.1497] |  | 0.0000 |
| hard_zero/E_lab/D_code/tau0.1/ones/incl/ctl-none | 6 | other | 256 | 10.1587 | 8.5613 | 1.5974 | [+1.5513, +1.6446] |  | 0.0000 |
| hard_zero/E_lab/D_code/tau0.1/ones/incl/ctl-none | 6 | ArXiv | 64 | 10.8727 | 9.1364 | 1.7363 | [+1.6559, +1.8170] |  | 0.0000 |
| hard_zero/E_lab/D_code/tau0.1/ones/incl/ctl-none | 6 | Pile-CC | 64 | 9.3566 | 7.9395 | 1.4171 | [+1.3494, +1.4772] |  | 0.0000 |
| hard_zero/E_lab/D_code/tau0.1/ones/incl/ctl-none | 6 | StackExchange | 64 | 10.5463 | 8.7704 | 1.7759 | [+1.6670, +1.8875] |  | 0.0000 |
| hard_zero/E_lab/D_code/tau0.1/ones/incl/ctl-none | 6 | Wikipedia (en) | 64 | 9.8592 | 8.3987 | 1.4605 | [+1.3840, +1.5355] |  | 0.0000 |
| hard_zero/E_lab/D_code/tau0.1/ones/incl/ctl-none | 7 | Github | 256 | 11.8202 | 10.3585 | 1.4617 | [+1.3962, +1.5269] |  | 0.0000 |
| hard_zero/E_lab/D_code/tau0.1/ones/incl/ctl-none | 7 | other | 256 | 10.2166 | 9.5085 | 0.7081 | [+0.6531, +0.7634] |  | 0.0000 |
| hard_zero/E_lab/D_code/tau0.1/ones/incl/ctl-none | 7 | ArXiv | 64 | 11.0445 | 10.1809 | 0.8636 | [+0.7819, +0.9480] |  | 0.0000 |
| hard_zero/E_lab/D_code/tau0.1/ones/incl/ctl-none | 7 | Pile-CC | 64 | 9.3504 | 8.9087 | 0.4416 | [+0.3702, +0.5129] |  | 0.0000 |
| hard_zero/E_lab/D_code/tau0.1/ones/incl/ctl-none | 7 | StackExchange | 64 | 10.5770 | 9.5250 | 1.0520 | [+0.9311, +1.1805] |  | 0.0000 |
| hard_zero/E_lab/D_code/tau0.1/ones/incl/ctl-none | 7 | Wikipedia (en) | 64 | 9.8945 | 9.4194 | 0.4751 | [+0.4001, +0.5476] |  | 0.0000 |
| hard_zero/E_lab/D_code/tau0.1/ones/incl/ctl-none | 8 | Github | 256 | 11.6814 | 10.9930 | 0.6883 | [+0.6160, +0.7595] |  | 0.0000 |
| hard_zero/E_lab/D_code/tau0.1/ones/incl/ctl-none | 8 | other | 256 | 10.0286 | 10.1925 | -0.1639 | [-0.2265, -0.1007] |  | 0.0000 |
| hard_zero/E_lab/D_code/tau0.1/ones/incl/ctl-none | 8 | ArXiv | 64 | 10.8433 | 10.9588 | -0.1155 | [-0.2199, -0.0114] |  | 0.0000 |
| hard_zero/E_lab/D_code/tau0.1/ones/incl/ctl-none | 8 | Pile-CC | 64 | 9.1354 | 9.5832 | -0.4478 | [-0.5482, -0.3449] |  | 0.0000 |
| hard_zero/E_lab/D_code/tau0.1/ones/incl/ctl-none | 8 | StackExchange | 64 | 10.3808 | 10.1735 | 0.2073 | [+0.0774, +0.3431] |  | 0.0000 |
| hard_zero/E_lab/D_code/tau0.1/ones/incl/ctl-none | 8 | Wikipedia (en) | 64 | 9.7551 | 10.0547 | -0.2996 | [-0.4040, -0.1939] |  | 0.0000 |
| code_specific_hard/E_lab/D_code/tau0.1/ones/incl/ctl-none | 1 | Github | 256 | 0.0000 | 0.0000 | 0.0000 | [+0.0000, +0.0000] | 0.0000 | 256.0000 |
| code_specific_hard/E_lab/D_code/tau0.1/ones/incl/ctl-none | 1 | other | 256 | 0.0000 | 0.0000 | 0.0000 | [+0.0000, +0.0000] | 0.0000 | 256.0000 |
| code_specific_hard/E_lab/D_code/tau0.1/ones/incl/ctl-none | 1 | ArXiv | 64 | 0.0000 | 0.0000 | 0.0000 | [+0.0000, +0.0000] | 0.0000 | 64.0000 |
| code_specific_hard/E_lab/D_code/tau0.1/ones/incl/ctl-none | 1 | Pile-CC | 64 | 0.0000 | 0.0000 | 0.0000 | [+0.0000, +0.0000] | 0.0000 | 64.0000 |
| code_specific_hard/E_lab/D_code/tau0.1/ones/incl/ctl-none | 1 | StackExchange | 64 | 0.0000 | 0.0000 | 0.0000 | [+0.0000, +0.0000] | 0.0000 | 64.0000 |
| code_specific_hard/E_lab/D_code/tau0.1/ones/incl/ctl-none | 1 | Wikipedia (en) | 64 | 0.0000 | 0.0000 | 0.0000 | [+0.0000, +0.0000] | 0.0000 | 64.0000 |
| code_specific_hard/E_lab/D_code/tau0.1/ones/incl/ctl-none | 2 | Github | 256 | 0.0025 | 0.0013 | 0.0012 | [+0.0010, +0.0015] | 0.0001 | 254.5000 |
| code_specific_hard/E_lab/D_code/tau0.1/ones/incl/ctl-none | 2 | other | 256 | 0.0006 | 0.0003 | 0.0003 | [+0.0002, +0.0004] | 0.0000 | 255.7500 |
| code_specific_hard/E_lab/D_code/tau0.1/ones/incl/ctl-none | 2 | ArXiv | 64 | 0.0000 | 0.0000 | -0.0000 | [-0.0000, +0.0000] | 0.0000 | 64.0000 |
| code_specific_hard/E_lab/D_code/tau0.1/ones/incl/ctl-none | 2 | Pile-CC | 64 | 0.0000 | 0.0000 | -0.0000 | [-0.0000, +0.0000] | 0.0000 | 64.0000 |
| code_specific_hard/E_lab/D_code/tau0.1/ones/incl/ctl-none | 2 | StackExchange | 64 | 0.0022 | 0.0011 | 0.0011 | [+0.0007, +0.0015] | 0.0001 | 63.7500 |
| code_specific_hard/E_lab/D_code/tau0.1/ones/incl/ctl-none | 2 | Wikipedia (en) | 64 | 0.0000 | 0.0000 | -0.0000 | [-0.0000, -0.0000] | 0.0000 | 64.0000 |
| code_specific_hard/E_lab/D_code/tau0.1/ones/incl/ctl-none | 3 | Github | 256 | 0.0091 | 0.0018 | 0.0073 | [+0.0061, +0.0086] | 0.0009 | 245.1250 |
| code_specific_hard/E_lab/D_code/tau0.1/ones/incl/ctl-none | 3 | other | 256 | 0.0020 | 0.0005 | 0.0015 | [+0.0009, +0.0022] | 0.0002 | 254.7500 |
| code_specific_hard/E_lab/D_code/tau0.1/ones/incl/ctl-none | 3 | ArXiv | 64 | 0.0002 | 0.0002 | -0.0001 | [-0.0001, +0.0000] | 0.0002 | 64.0000 |
| code_specific_hard/E_lab/D_code/tau0.1/ones/incl/ctl-none | 3 | Pile-CC | 64 | 0.0001 | 0.0001 | 0.0000 | [+0.0000, +0.0000] | 0.0001 | 64.0000 |
| code_specific_hard/E_lab/D_code/tau0.1/ones/incl/ctl-none | 3 | StackExchange | 64 | 0.0074 | 0.0014 | 0.0060 | [+0.0040, +0.0082] | 0.0005 | 62.7500 |
| code_specific_hard/E_lab/D_code/tau0.1/ones/incl/ctl-none | 3 | Wikipedia (en) | 64 | 0.0002 | 0.0002 | 0.0000 | [+0.0000, +0.0000] | 0.0002 | 64.0000 |
| code_specific_hard/E_lab/D_code/tau0.1/ones/incl/ctl-none | 4 | Github | 256 | 0.0098 | 0.0007 | 0.0090 | [+0.0078, +0.0103] | 0.0014 | 239.3750 |
| code_specific_hard/E_lab/D_code/tau0.1/ones/incl/ctl-none | 4 | other | 256 | 0.0021 | 0.0004 | 0.0017 | [+0.0011, +0.0023] | 0.0005 | 251.8750 |
| code_specific_hard/E_lab/D_code/tau0.1/ones/incl/ctl-none | 4 | ArXiv | 64 | 0.0010 | 0.0006 | 0.0004 | [+0.0002, +0.0007] | 0.0004 | 62.1250 |
| code_specific_hard/E_lab/D_code/tau0.1/ones/incl/ctl-none | 4 | Pile-CC | 64 | 0.0004 | 0.0003 | 0.0001 | [+0.0001, +0.0001] | 0.0004 | 64.0000 |
| code_specific_hard/E_lab/D_code/tau0.1/ones/incl/ctl-none | 4 | StackExchange | 64 | 0.0066 | 0.0005 | 0.0062 | [+0.0043, +0.0082] | 0.0008 | 61.7500 |
| code_specific_hard/E_lab/D_code/tau0.1/ones/incl/ctl-none | 4 | Wikipedia (en) | 64 | 0.0004 | 0.0004 | 0.0001 | [+0.0001, +0.0001] | 0.0005 | 64.0000 |
| code_specific_hard/E_lab/D_code/tau0.1/ones/incl/ctl-none | 5 | Github | 256 | 0.0193 | 0.0044 | 0.0149 | [+0.0130, +0.0168] | 0.0046 | 210.0000 |
| code_specific_hard/E_lab/D_code/tau0.1/ones/incl/ctl-none | 5 | other | 256 | 0.0053 | 0.0027 | 0.0026 | [+0.0018, +0.0037] | 0.0019 | 247.1250 |
| code_specific_hard/E_lab/D_code/tau0.1/ones/incl/ctl-none | 5 | ArXiv | 64 | 0.0053 | 0.0043 | 0.0010 | [+0.0006, +0.0015] | 0.0018 | 61.2500 |
| code_specific_hard/E_lab/D_code/tau0.1/ones/incl/ctl-none | 5 | Pile-CC | 64 | 0.0014 | 0.0013 | 0.0001 | [+0.0001, +0.0002] | 0.0014 | 64.0000 |
| code_specific_hard/E_lab/D_code/tau0.1/ones/incl/ctl-none | 5 | StackExchange | 64 | 0.0129 | 0.0037 | 0.0092 | [+0.0062, +0.0126] | 0.0026 | 57.8750 |
| code_specific_hard/E_lab/D_code/tau0.1/ones/incl/ctl-none | 5 | Wikipedia (en) | 64 | 0.0016 | 0.0015 | 0.0002 | [+0.0001, +0.0002] | 0.0018 | 64.0000 |
| code_specific_hard/E_lab/D_code/tau0.1/ones/incl/ctl-none | 6 | Github | 256 | 0.0323 | 0.0092 | 0.0231 | [+0.0203, +0.0260] | 0.0103 | 183.7500 |
| code_specific_hard/E_lab/D_code/tau0.1/ones/incl/ctl-none | 6 | other | 256 | 0.0124 | 0.0066 | 0.0058 | [+0.0045, +0.0073] | 0.0048 | 230.8750 |
| code_specific_hard/E_lab/D_code/tau0.1/ones/incl/ctl-none | 6 | ArXiv | 64 | 0.0212 | 0.0103 | 0.0109 | [+0.0084, +0.0135] | 0.0047 | 50.8750 |
| code_specific_hard/E_lab/D_code/tau0.1/ones/incl/ctl-none | 6 | Pile-CC | 64 | 0.0039 | 0.0035 | 0.0004 | [+0.0004, +0.0005] | 0.0039 | 64.0000 |
| code_specific_hard/E_lab/D_code/tau0.1/ones/incl/ctl-none | 6 | StackExchange | 64 | 0.0200 | 0.0087 | 0.0113 | [+0.0071, +0.0157] | 0.0062 | 52.5000 |
| code_specific_hard/E_lab/D_code/tau0.1/ones/incl/ctl-none | 6 | Wikipedia (en) | 64 | 0.0047 | 0.0040 | 0.0007 | [+0.0005, +0.0008] | 0.0048 | 63.5000 |
| code_specific_hard/E_lab/D_code/tau0.1/ones/incl/ctl-none | 7 | Github | 256 | 0.0392 | 0.0147 | 0.0244 | [+0.0216, +0.0273] | 0.0157 | 176.5000 |
| code_specific_hard/E_lab/D_code/tau0.1/ones/incl/ctl-none | 7 | other | 256 | 0.0204 | 0.0114 | 0.0090 | [+0.0070, +0.0113] | 0.0079 | 222.3750 |
| code_specific_hard/E_lab/D_code/tau0.1/ones/incl/ctl-none | 7 | ArXiv | 64 | 0.0420 | 0.0177 | 0.0243 | [+0.0187, +0.0301] | 0.0078 | 45.1250 |
| code_specific_hard/E_lab/D_code/tau0.1/ones/incl/ctl-none | 7 | Pile-CC | 64 | 0.0067 | 0.0061 | 0.0007 | [+0.0006, +0.0008] | 0.0067 | 64.0000 |
| code_specific_hard/E_lab/D_code/tau0.1/ones/incl/ctl-none | 7 | StackExchange | 64 | 0.0249 | 0.0147 | 0.0102 | [+0.0058, +0.0149] | 0.0096 | 50.2500 |
| code_specific_hard/E_lab/D_code/tau0.1/ones/incl/ctl-none | 7 | Wikipedia (en) | 64 | 0.0080 | 0.0071 | 0.0010 | [+0.0008, +0.0012] | 0.0080 | 63.0000 |
| code_specific_hard/E_lab/D_code/tau0.1/ones/incl/ctl-none | 8 | Github | 256 | 0.0497 | 0.0290 | 0.0207 | [+0.0179, +0.0236] | 0.0252 | 174.0000 |
| code_specific_hard/E_lab/D_code/tau0.1/ones/incl/ctl-none | 8 | other | 256 | 0.0290 | 0.0228 | 0.0062 | [+0.0046, +0.0080] | 0.0145 | 217.0000 |
| code_specific_hard/E_lab/D_code/tau0.1/ones/incl/ctl-none | 8 | ArXiv | 64 | 0.0545 | 0.0415 | 0.0131 | [+0.0099, +0.0163] | 0.0131 | 40.0000 |
| code_specific_hard/E_lab/D_code/tau0.1/ones/incl/ctl-none | 8 | Pile-CC | 64 | 0.0129 | 0.0122 | 0.0006 | [+0.0004, +0.0009] | 0.0127 | 64.0000 |
| code_specific_hard/E_lab/D_code/tau0.1/ones/incl/ctl-none | 8 | StackExchange | 64 | 0.0333 | 0.0226 | 0.0106 | [+0.0056, +0.0161] | 0.0168 | 50.0000 |
| code_specific_hard/E_lab/D_code/tau0.1/ones/incl/ctl-none | 8 | Wikipedia (en) | 64 | 0.0153 | 0.0147 | 0.0006 | [+0.0003, +0.0009] | 0.0153 | 63.0000 |
| code_specific_hard/E_lab/D_code/tau0.1/ones/incl/ctl-none | S4 | Github | 256 | 0.0123 | 0.0016 | 0.0107 | [+0.0089, +0.0128] | 0.0013 | 234.0000 |
| code_specific_hard/E_lab/D_code/tau0.1/ones/incl/ctl-none | S4 | other | 256 | 0.0025 | 0.0003 | 0.0022 | [+0.0014, +0.0032] | 0.0004 | 253.0000 |
| code_specific_hard/E_lab/D_code/tau0.1/ones/incl/ctl-none | S4 | ArXiv | 64 | 0.0002 | 0.0003 | -0.0001 | [-0.0003, +0.0000] | 0.0002 | 64.0000 |
| code_specific_hard/E_lab/D_code/tau0.1/ones/incl/ctl-none | S4 | Pile-CC | 64 | 0.0002 | 0.0002 | 0.0000 | [-0.0000, +0.0000] | 0.0002 | 64.0000 |
| code_specific_hard/E_lab/D_code/tau0.1/ones/incl/ctl-none | S4 | StackExchange | 64 | 0.0095 | 0.0004 | 0.0090 | [+0.0062, +0.0121] | 0.0007 | 61.0000 |
| code_specific_hard/E_lab/D_code/tau0.1/ones/incl/ctl-none | S4 | Wikipedia (en) | 64 | 0.0002 | 0.0002 | 0.0000 | [-0.0000, +0.0000] | 0.0003 | 64.0000 |
| code_specific_hard/E_lab/D_code/tau0.1/ones/incl/ctl-none | S16 | Github | 256 | 0.0221 | 0.0060 | 0.0160 | [+0.0136, +0.0185] | 0.0041 | 195.0000 |
| code_specific_hard/E_lab/D_code/tau0.1/ones/incl/ctl-none | S16 | other | 256 | 0.0043 | 0.0013 | 0.0030 | [+0.0019, +0.0044] | 0.0013 | 247.0000 |
| code_specific_hard/E_lab/D_code/tau0.1/ones/incl/ctl-none | S16 | ArXiv | 64 | 0.0010 | 0.0012 | -0.0003 | [-0.0006, +0.0000] | 0.0010 | 64.0000 |
| code_specific_hard/E_lab/D_code/tau0.1/ones/incl/ctl-none | S16 | Pile-CC | 64 | 0.0010 | 0.0009 | 0.0002 | [+0.0001, +0.0002] | 0.0010 | 64.0000 |
| code_specific_hard/E_lab/D_code/tau0.1/ones/incl/ctl-none | S16 | StackExchange | 64 | 0.0138 | 0.0019 | 0.0119 | [+0.0078, +0.0164] | 0.0021 | 55.0000 |
| code_specific_hard/E_lab/D_code/tau0.1/ones/incl/ctl-none | S16 | Wikipedia (en) | 64 | 0.0012 | 0.0010 | 0.0002 | [+0.0002, +0.0003] | 0.0013 | 64.0000 |
| code_specific_hard/E_lab/D_code/tau0.1/ones/incl/ctl-none | S64 | Github | 256 | 0.0350 | 0.0124 | 0.0226 | [+0.0196, +0.0256] | 0.0111 | 179.0000 |
| code_specific_hard/E_lab/D_code/tau0.1/ones/incl/ctl-none | S64 | other | 256 | 0.0157 | 0.0054 | 0.0102 | [+0.0077, +0.0130] | 0.0051 | 234.0000 |
| code_specific_hard/E_lab/D_code/tau0.1/ones/incl/ctl-none | S64 | ArXiv | 64 | 0.0324 | 0.0073 | 0.0251 | [+0.0176, +0.0333] | 0.0051 | 57.0000 |
| code_specific_hard/E_lab/D_code/tau0.1/ones/incl/ctl-none | S64 | Pile-CC | 64 | 0.0043 | 0.0037 | 0.0006 | [+0.0005, +0.0008] | 0.0043 | 64.0000 |
| code_specific_hard/E_lab/D_code/tau0.1/ones/incl/ctl-none | S64 | StackExchange | 64 | 0.0208 | 0.0062 | 0.0146 | [+0.0098, +0.0196] | 0.0064 | 50.0000 |
| code_specific_hard/E_lab/D_code/tau0.1/ones/incl/ctl-none | S64 | Wikipedia (en) | 64 | 0.0050 | 0.0045 | 0.0005 | [+0.0004, +0.0007] | 0.0051 | 63.0000 |

Comparison 3, within other at rung 7: StackExchange and ArXiv against Pile-CC and Wikipedia, unpaired, with the conditional damage beside:
| chain | rung | n_a | n_b | unconditional_a_minus_b | interval | conditional_d_0.1_a | conditional_d_0.1_b |
|---|---|---|---|---|---|---|---|
| hard_zero/E_lab/D_code/tau0.1/ones/incl/ctl-none | 7 | 128 | 128 | 1.1883 | [+1.0029, +1.3746] |  |  |
| code_specific_hard/E_lab/D_code/tau0.1/ones/incl/ctl-none | 7 | 128 | 128 | 0.0260 | [+0.0209, +0.0313] | 0.0088 | 0.0073 |

### Soft erases and the rounded-own-g union (descriptive, the union machinery)
- `soft_erase/E/D_unif/tau0.1/r1/excl/ctl-none`: rung 0 0.0114; excess per rung 1 +1.1901, 2 +4.0106, 3 +8.2350, 4 +9.0156, 5 +9.8161, 6 +10.0096, 7 +9.9758, 8 +9.9979
- `soft_erase/E/D_unif/tau0.1/uniform/excl/k0/ctl-none`: rung 0 0.2772; excess per rung 1 +0.0414, 2 +0.1631, 3 +0.5642, 4 +0.9708, 5 +1.1257, 6 +1.2227, 7 +1.2327, 8 +1.2257
- `soft_erase/E/D_unif/tau0.1/uniform/excl/k1/ctl-none`: rung 0 0.2774; excess per rung 1 +0.0223, 2 +0.1292, 3 +0.5081, 4 +0.5810, 5 +1.1330, 6 +1.2198, 7 +1.2249, 8 +1.2243
- `soft_erase/E/D_unif/tau0.1/uniform/excl/k2/ctl-none`: rung 0 0.2769; excess per rung 1 +0.0459, 2 +0.1295, 3 +0.5374, 4 +0.6433, 5 +1.1064, 6 +1.2252, 7 +1.2253, 8 +1.2268
- `soft_erase/E/D_unif/tau0.1/uniform/excl/k3/ctl-none`: rung 0 0.2769; excess per rung 1 +0.0313, 2 +0.1801, 3 +0.5916, 4 +0.1041, 5 +1.0581, 6 +1.2116, 7 +1.2259, 8 +1.2262
- `soft_erase/E/D_unif/tau0.1/uniform/excl/k4/ctl-none`: rung 0 0.2771; excess per rung 1 +0.0270, 2 +0.1362, 3 +0.4583, 4 +0.7173, 5 +1.0876, 6 +1.2003, 7 +1.2098, 8 +1.2248
- `soft_erase/E/D_unif/tau0.1/uniform/excl/k5/ctl-none`: rung 0 0.2770; excess per rung 1 +0.0289, 2 +0.1272, 3 +0.5721, 4 +0.7672, 5 +1.0580, 6 +1.2265, 7 +1.2289, 8 +1.2254
- `soft_erase/E/D_unif/tau0.1/uniform/excl/k6/ctl-none`: rung 0 0.2769; excess per rung 1 +0.0050, 2 +0.1096, 3 +0.5213, 4 +0.6775, 5 +1.0326, 6 +1.2212, 7 +1.2360, 8 +1.2255
- `soft_erase/E/D_unif/tau0.1/uniform/excl/k7/ctl-none`: rung 0 0.2771; excess per rung 1 +0.0290, 2 +0.1302, 3 +0.5239, 4 +0.6489, 5 +0.9328, 6 +1.2091, 7 +1.2325, 8 +1.2253
- `soft_erase/E/D_unif/tau0.1/r1/excl/ctl-plain`: rung 0 0.0114; excess per rung 1 +0.0540, 2 +0.3674, 3 +2.1620, 4 +3.9688, 5 +8.3513, 6 +9.6606, 7 +10.0609, 8 +9.9903
- `soft_erase/E/D_unif/tau0.1/uniform/excl/k0/ctl-plain`: rung 0 0.2772; excess per rung 1 +0.0050, 2 +0.0449, 3 +0.2019, 4 +0.4730, 5 +0.7298, 6 +1.0188, 7 +1.1729, 8 +1.2239
- `soft_erase/E/D_unif/tau0.1/uniform/excl/k1/ctl-plain`: rung 0 0.2774; excess per rung 1 +0.0064, 2 +0.0406, 3 +0.1827, 4 +0.2253, 5 +0.6934, 6 +0.9193, 7 +1.1110, 8 +1.2249
- `soft_erase/E/D_unif/tau0.1/uniform/excl/k2/ctl-plain`: rung 0 0.2769; excess per rung 1 +0.0078, 2 +0.0278, 3 +0.2008, 4 +0.2980, 5 +0.7074, 6 +0.9392, 7 +1.0999, 8 +1.2271
- `soft_erase/E/D_unif/tau0.1/uniform/excl/k3/ctl-plain`: rung 0 0.2769; excess per rung 1 +0.0050, 2 +0.0560, 3 +0.2135, 4 +0.0344, 5 +0.6524, 6 +0.9013, 7 +1.1518, 8 +1.2220
- `soft_erase/E/D_unif/tau0.1/uniform/excl/k4/ctl-plain`: rung 0 0.2771; excess per rung 1 +0.0076, 2 +0.0348, 3 +0.1505, 4 +0.3411, 5 +0.7048, 6 +0.9809, 7 +1.1525, 8 +1.2232
- `soft_erase/E/D_unif/tau0.1/uniform/excl/k5/ctl-plain`: rung 0 0.2770; excess per rung 1 +0.0030, 2 +0.0275, 3 +0.2086, 4 +0.3908, 5 +0.6995, 6 +1.0544, 7 +1.1536, 8 +1.2242
- `soft_erase/E/D_unif/tau0.1/uniform/excl/k6/ctl-plain`: rung 0 0.2769; excess per rung 1 +0.0005, 2 +0.0257, 3 +0.1924, 4 +0.3549, 5 +0.5840, 6 +1.0080, 7 +1.1643, 8 +1.2253
- `soft_erase/E/D_unif/tau0.1/uniform/excl/k7/ctl-plain`: rung 0 0.2771; excess per rung 1 +0.0072, 2 +0.0283, 3 +0.1876, 4 +0.3157, 5 +0.5435, 6 +0.9550, 7 +1.1532, 8 +1.2258
- `soft_erase/E_lab/D_code/tau0.1/r1/excl/ctl-none`: rung 0 0.0123; excess per rung 1 +1.2548, 2 +3.9526, 3 +8.0008, 4 +9.7522, 5 +10.0412, 6 +9.9796, 7 +9.9411, 8 +9.8668
- `soft_erase/E_lab/D_code/tau0.1/r1/excl/ctl-plain`: rung 0 0.0123; excess per rung 1 +0.0603, 2 +0.4022, 3 +2.0369, 4 +4.2446, 5 +7.2211, 6 +9.3728, 7 +9.8048, 8 +9.6571

## 8. This run against the main run's stores (results/grid/main): this minus other, paired on the sequence and the draw
Sets scored in common (hashes asserted equal): E (1024), E_lab (512)
### curve 1: rungs only in this run none, only in the other ['5a', '6a']
| rung | n_on_this | n_on_other | excess_this | excess_other | paired_difference | interval | half_width |
|---|---|---|---|---|---|---|---|
| 1 | 60.7500 | 169.0000 | -0.6298 | 0.0038 | -0.6336 | [-0.6837, -0.5867] | 0.0485 |
| 2 | 392.5000 | 1120.6250 | 0.3238 | 0.0402 | 0.2837 | [+0.2032, +0.3602] | 0.0785 |
| 3 | 1792.0000 | 4543.6250 | 0.6857 | 0.4575 | 0.2282 | [+0.1392, +0.3141] | 0.0874 |
| 4 | 2483.6250 | 4890.2500 | 2.6775 | 0.4877 | 2.1898 | [+2.0899, +2.2879] | 0.0990 |
| 5 | 4394.3750 | 7711.0000 | 2.6980 | 0.8516 | 1.8464 | [+1.7459, +1.9445] | 0.0993 |
| 6 | 5516.0000 | 9060.0000 | 2.6413 | 0.9527 | 1.6886 | [+1.5905, +1.7837] | 0.0966 |
| 7 | 6053.1250 | 9659.2500 | 2.6203 | 0.9536 | 1.6667 | [+1.5695, +1.7612] | 0.0959 |
| 8 | 6361.0000 | 9966.0000 | 2.6160 | 0.9458 | 1.6701 | [+1.5731, +1.7645] | 0.0957 |

### curve 2 (draw 0): rungs only in this run none, only in the other ['5a', '6a']
| rung | n_on_this | n_on_other | excess_this | excess_other | paired_difference | interval | half_width |
|---|---|---|---|---|---|---|---|
| 1 | 83.0000 | 201.0000 | 0.0682 | 0.0097 | 0.0585 | [+0.0561, +0.0609] | 0.0024 |
| 2 | 441.0000 | 1039.0000 | 0.2616 | 0.0491 | 0.2125 | [+0.2078, +0.2173] | 0.0047 |
| 3 | 1855.0000 | 4494.0000 | 1.8516 | 0.3751 | 1.4765 | [+1.4435, +1.5106] | 0.0336 |
| 4 | 3605.0000 | 6764.0000 | 2.8045 | 0.5842 | 2.2204 | [+2.1798, +2.2628] | 0.0415 |
| 5 | 4700.0000 | 8170.0000 | 2.7652 | 0.6621 | 2.1030 | [+2.0659, +2.1417] | 0.0379 |
| 6 | 5644.0000 | 9203.0000 | 2.7455 | 0.6644 | 2.0810 | [+2.0466, +2.1174] | 0.0354 |
| 7 | 6104.0000 | 9794.0000 | 2.6998 | 0.6553 | 2.0446 | [+2.0103, +2.0805] | 0.0351 |
| 8 | 6361.0000 | 9966.0000 | 2.6617 | 0.6499 | 2.0118 | [+1.9775, +2.0476] | 0.0351 |

### curve 3: rungs only in this run none, only in the other ['5a', '6a']
| rung | n_on_this | n_on_other | excess_this | excess_other | paired_difference | interval | half_width | testable_this | d_hat_this | d_interval_this | testable_other | d_hat_other | d_interval_other |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 63.0000 | 197.8750 | 6.0232 | 11.6786 | -5.6554 | [-5.7130, -5.5979] | 0.0576 | False |  | n/a | False |  | n/a |
| 2 | 316.5000 | 975.0000 | 7.3513 | 12.5123 | -5.1610 | [-5.2385, -5.0808] | 0.0789 | False |  | n/a | False |  | n/a |
| 3 | 1444.7500 | 3626.3750 | 8.5906 | 11.5381 | -2.9474 | [-2.9973, -2.8986] | 0.0494 | False |  | n/a | False |  | n/a |
| 4 | 2508.5000 | 5156.3750 | 9.7867 | 11.3994 | -1.6127 | [-1.6526, -1.5735] | 0.0395 | False |  | n/a | False |  | n/a |
| 5 | 3971.6250 | 7324.5000 | 10.4386 | 11.4045 | -0.9659 | [-1.0126, -0.9201] | 0.0462 | False |  | n/a | False |  | n/a |
| 6 | 5081.0000 | 8649.7500 | 10.9471 | 11.5729 | -0.6258 | [-0.6850, -0.5677] | 0.0586 | False |  | n/a | False |  | n/a |
| 7 | 5550.5000 | 9223.2500 | 11.0184 | 11.6047 | -0.5863 | [-0.6475, -0.5270] | 0.0602 | False |  | n/a | False |  | n/a |
| 8 | 5864.0000 | 9624.0000 | 10.8550 | 11.6658 | -0.8108 | [-0.8733, -0.7504] | 0.0614 | False |  | n/a | False |  | n/a |

### curve 4: rungs only in this run none, only in the other ['5a', '6a']
| rung | n_on_this | n_on_other | excess_this | excess_other | paired_difference | interval | half_width | testable_this | d_hat_this | d_interval_this | testable_other | d_hat_other | d_interval_other |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 0.0000 | 0.1250 | 0.0000 | 0.0001 | -0.0001 | [-0.0001, -0.0001] | 0.0000 | True | 0.0000 | [+0.0000, +0.0000] | True | 0.0000 | [+0.0000, +0.0000] |
| 2 | 0.2500 | 1.2500 | 0.0015 | 0.0009 | 0.0007 | [+0.0005, +0.0008] | 0.0002 | True | 0.0001 | [+0.0001, +0.0001] | True | 0.0001 | [+0.0001, +0.0002] |
| 3 | 2.5000 | 5.1250 | 0.0055 | 0.0040 | 0.0015 | [+0.0012, +0.0019] | 0.0004 | True | 0.0005 | [+0.0005, +0.0006] | True | 0.0006 | [+0.0005, +0.0007] |
| 4 | 5.6250 | 8.6250 | 0.0060 | 0.0055 | 0.0004 | [+0.0001, +0.0008] | 0.0004 | True | 0.0009 | [+0.0008, +0.0010] | True | 0.0010 | [+0.0009, +0.0012] |
| 5 | 21.7500 | 30.2500 | 0.0123 | 0.0100 | 0.0023 | [+0.0016, +0.0030] | 0.0007 | True | 0.0031 | [+0.0028, +0.0034] | True | 0.0028 | [+0.0025, +0.0031] |
| 6 | 60.6250 | 63.6250 | 0.0224 | 0.0145 | 0.0079 | [+0.0065, +0.0093] | 0.0014 | True | 0.0072 | [+0.0066, +0.0079] | True | 0.0057 | [+0.0051, +0.0065] |
| 7 | 104.5000 | 108.6250 | 0.0298 | 0.0187 | 0.0111 | [+0.0092, +0.0131] | 0.0019 | True | 0.0114 | [+0.0104, +0.0124] | True | 0.0095 | [+0.0084, +0.0109] |
| 8 | 201.0000 | 270.0000 | 0.0394 | 0.0321 | 0.0073 | [+0.0053, +0.0094] | 0.0021 | True | 0.0193 | [+0.0178, +0.0209] | True | 0.0208 | [+0.0186, +0.0236] |
| S4 | 4.0000 | 4.0000 | 0.0074 | 0.0015 | 0.0059 | [+0.0049, +0.0070] | 0.0010 | True | 0.0008 | [+0.0007, +0.0009] | True | 0.0005 | [+0.0004, +0.0007] |
| S16 | 16.0000 | 16.0000 | 0.0132 | 0.0096 | 0.0036 | [+0.0026, +0.0047] | 0.0010 | True | 0.0025 | [+0.0022, +0.0029] | True | 0.0015 | [+0.0013, +0.0018] |
| S64 | 64.0000 | 64.0000 | 0.0253 | 0.0151 | 0.0102 | [+0.0085, +0.0121] | 0.0018 | True | 0.0077 | [+0.0070, +0.0085] | True | 0.0061 | [+0.0054, +0.0071] |

### curve 1 at matched switched mass, edges from the other run's pre-reads applied to both runs' union cells
| bin | overflow | edge_low | edge_high | n_sequences_this | n_sequences_other | populated | mean_this | mean_other | difference | interval |
|---|---|---|---|---|---|---|---|---|---|---|
| 0 | False | 23.1357 | 202.8046 | 1024 | 1024 | True | -0.7078 | 0.0042 | -0.7120 | [-0.7665, -0.6607] |
| 1 | False | 202.8046 | 1221.7465 | 1024 | 1024 | True | 0.4862 | 0.0331 | 0.4530 | [+0.3722, +0.5295] |
| 2 | False | 1221.7465 | 4396.4055 | 1024 | 1024 | True | 1.9619 | 0.2979 | 1.6640 | [+1.5716, +1.7543] |
| 3 | False | 4396.4055 | 5304.6058 | 1024 | 1024 | True | 2.7328 | 0.4920 | 2.2408 | [+2.1336, +2.3452] |
| 4 | False | 5304.6058 | 6498.0445 | 1024 | 1024 | True | 2.6308 | 0.6492 | 1.9816 | [+1.8828, +2.0785] |
| 5 | False | 6498.0445 | 7512.8537 | 0 | 1024 | False |  | 0.7846 |  |  |
| 6 | False | 7512.8537 | 8218.7061 | 0 | 1024 | False |  | 0.9001 |  |  |
| 7 | False | 8218.7061 | 8791.3866 | 0 | 1024 | False |  | 0.9341 |  |  |
| 8 | False | 8791.3866 | 9421.1109 | 0 | 1024 | False |  | 0.9641 |  |  |
| 9 | False | 9421.1109 | 9708.9387 | 0 | 1024 | False |  | 0.9255 |  |  |
| 10 | True | 9708.9387 | inf | 0 | 1 | False |  |  |  |  |

### curve 2 (draw 0) at matched switched mass, edges from the other run's loop sigma applied to both runs' union cells
| bin | overflow | edge_low | edge_high | n_sequences_this | n_sequences_other | populated | mean_this | mean_other | difference | interval |
|---|---|---|---|---|---|---|---|---|---|---|
| 0 | False | 79.3522 | 93.1002 | 0 | 922 | False |  | 0.0107 |  |  |
| 1 | False | 93.1002 | 493.6082 | 1024 | 904 | True | 0.2616 | 0.0477 | 0.2138 | [+0.2091, +0.2188] |
| 2 | False | 493.6082 | 2185.9388 | 1024 | 897 | True | 2.3280 | 0.3275 | 2.0005 | [+1.9627, +2.0399] |
| 3 | False | 2185.9388 | 3311.1470 | 1024 | 902 | True | 2.7368 | 0.5535 | 2.1833 | [+2.1482, +2.2197] |
| 4 | False | 3311.1470 | 3678.7576 | 0 | 915 | False |  | 0.6174 |  |  |
| 5 | False | 3678.7576 | 4007.1804 | 0 | 921 | False |  | 0.6370 |  |  |
| 6 | False | 4007.1804 | 4250.2256 | 0 | 922 | False |  | 0.6623 |  |  |
| 7 | False | 4250.2256 | 4519.4385 | 0 | 921 | False |  | 0.6567 |  |  |
| 8 | False | 4519.4385 | 4811.1101 | 0 | 922 | False |  | 0.6463 |  |  |
| 9 | False | 4811.1101 | 4855.5332 | 0 | 922 | False |  | 0.6206 |  |  |
| 10 | True | 4855.5332 | inf | 0 | 0 | False |  |  |  |  |

## 9. Tier 4: the marginal-matched control, the code-leaning chain, and the code-specific chain on E by reader label

Every reading rule below was fixed before any tier-4 store existed; the labels are the frozen rules' output.

### 9.1 The marginal-matched control: no marginal cell in these stores

### 9.2 The code-leaning chain: no code-leaning cell in these stores

### 9.3 The code-specific chain on E by reader label (an analysis addition, no verdict)

Not available: no reader labels for this run, or no code-specific chain on E.

