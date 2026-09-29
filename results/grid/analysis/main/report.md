# Analysis of the grid, run main (the pre-registered read order)

Stores: tier1/E, tier1/E_lab, tier2/E, tier2/E_lab, tier3/E__curve1_extra, tier3/E__editing_extra, tier3/E__levels, tier3/E__never_named, tier3/E__ranked, tier3/E__tau0_union, tier3/E_lab__editing_extra, tier3/donors_D_unif_k0_r4, tier3/donors_D_unif_k0_r7, tier3/donors_D_unif_k1_r4, tier3/donors_D_unif_k1_r7, tier3/donors_D_unif_k2_r4, tier3/donors_D_unif_k2_r7, tier3/donors_D_unif_k3_r4, tier3/donors_D_unif_k3_r7, tier3/donors_D_unif_k4_r4, tier3/donors_D_unif_k4_r7, tier3/donors_D_unif_k5_r4, tier3/donors_D_unif_k5_r7, tier3/donors_D_unif_k6_r4, tier3/donors_D_unif_k6_r7, tier3/donors_D_unif_k7_r4, tier3/donors_D_unif_k7_r7, tier4/E__marginal, tier4/E_lab__code_leaning; sets E (1024 sequences, 1284 cells), E_lab (512 sequences, 770 cells), tier3/donors_D_unif_k0_r4 (1 sequences, 3 cells), tier3/donors_D_unif_k0_r7 (64 sequences, 3 cells), tier3/donors_D_unif_k1_r4 (1 sequences, 3 cells), tier3/donors_D_unif_k1_r7 (64 sequences, 3 cells), tier3/donors_D_unif_k2_r4 (1 sequences, 3 cells), tier3/donors_D_unif_k2_r7 (64 sequences, 3 cells), tier3/donors_D_unif_k3_r4 (1 sequences, 3 cells), tier3/donors_D_unif_k3_r7 (64 sequences, 3 cells), tier3/donors_D_unif_k4_r4 (1 sequences, 3 cells), tier3/donors_D_unif_k4_r7 (64 sequences, 3 cells), tier3/donors_D_unif_k5_r4 (1 sequences, 3 cells), tier3/donors_D_unif_k5_r7 (64 sequences, 3 cells), tier3/donors_D_unif_k6_r4 (1 sequences, 3 cells), tier3/donors_D_unif_k6_r7 (64 sequences, 3 cells), tier3/donors_D_unif_k7_r4 (1 sequences, 3 cells), tier3/donors_D_unif_k7_r7 (64 sequences, 3 cells); replicates 10000; seed (master 0, boot, set); commit c57fc2b543b4 (dirty 0).

## 0. Asserts
- References bitwise across stores per set: {'E': {'n_stores': 9, 'pass': True}, 'E_lab': {'n_stores': 4, 'pass': True}, 'tier3/donors_D_unif_k0_r4': {'n_stores': 1, 'pass': True}, 'tier3/donors_D_unif_k0_r7': {'n_stores': 1, 'pass': True}, 'tier3/donors_D_unif_k1_r4': {'n_stores': 1, 'pass': True}, 'tier3/donors_D_unif_k1_r7': {'n_stores': 1, 'pass': True}, 'tier3/donors_D_unif_k2_r4': {'n_stores': 1, 'pass': True}, 'tier3/donors_D_unif_k2_r7': {'n_stores': 1, 'pass': True}, 'tier3/donors_D_unif_k3_r4': {'n_stores': 1, 'pass': True}, 'tier3/donors_D_unif_k3_r7': {'n_stores': 1, 'pass': True}, 'tier3/donors_D_unif_k4_r4': {'n_stores': 1, 'pass': True}, 'tier3/donors_D_unif_k4_r7': {'n_stores': 1, 'pass': True}, 'tier3/donors_D_unif_k5_r4': {'n_stores': 1, 'pass': True}, 'tier3/donors_D_unif_k5_r7': {'n_stores': 1, 'pass': True}, 'tier3/donors_D_unif_k6_r4': {'n_stores': 1, 'pass': True}, 'tier3/donors_D_unif_k6_r7': {'n_stores': 1, 'pass': True}, 'tier3/donors_D_unif_k7_r4': {'n_stores': 1, 'pass': True}, 'tier3/donors_D_unif_k7_r7': {'n_stores': 1, 'pass': True}}
- Verification-store canary (equality only): {'available': True, 'cells': {'main/E/hard_zero/D_unif/tau0.1/ones/incl/k0/r1': True, 'main/E/hard_zero/D_unif/tau0.1/ones/incl/k0/r2': True, 'main/E/hard_zero/D_unif/tau0.1/ones/incl/k0/r3': True, 'main/E/hard_zero/D_unif/tau0.1/ones/incl/k0/r4': True, 'main/E/hard_zero/D_unif/tau0.1/ones/incl/k0/r5': True, 'main/E/hard_zero/D_unif/tau0.1/ones/incl/k0/r6': True, 'main/E/hard_zero/D_unif/tau0.1/ones/incl/k0/r7': True, 'main/E/hard_zero/D_unif/tau0.1/ones/incl/k0/r8': True, 'main/E/never_named_hard/D_unif/tau0.1/ones/excl/k0/r8': True, 'main/E/never_named_hard/D_unif/tau0.1/ones/incl/k0/r8': True, 'main/E/soft_erase/D_unif/tau0.1/r1/excl/k0/r8': True, 'main/E/union/D_unif/tau0.1/r0/excl/k0/r1': True, 'main/E/union/D_unif/tau0.1/r0/excl/k0/r2': True, 'main/E/union/D_unif/tau0.1/r0/excl/k0/r3': True, 'main/E/union/D_unif/tau0.1/r0/excl/k0/r4': True, 'main/E/union/D_unif/tau0.1/r0/excl/k0/r5': True, 'main/E/union/D_unif/tau0.1/r0/excl/k0/r6': True, 'main/E/union/D_unif/tau0.1/r0/excl/k0/r7': True, 'main/E/union/D_unif/tau0.1/r0/excl/k0/r8': True}, 'n_cells': 19, 'pass': True}
- Pre-reads: {'t_star': {'E': {'n_cells': 349, 'n_rows': 357376, 't_star_0.1': True, 't_star_0': True, 'n_touched_0.1': True, 'n_touched_0': True}, 'E_lab': {'n_cells': 526, 'n_rows': 269312, 't_star_0.1': True, 't_star_0': True, 'n_touched_0.1': True, 'n_touched_0': True}, 'tier3/donors_D_unif_k0_r4': {'n_cells': 0, 'n_rows': 0, 't_star_0.1': True, 't_star_0': True, 'n_touched_0.1': True, 'n_touched_0': True}, 'tier3/donors_D_unif_k0_r7': {'n_cells': 0, 'n_rows': 0, 't_star_0.1': True, 't_star_0': True, 'n_touched_0.1': True, 'n_touched_0': True}, 'tier3/donors_D_unif_k1_r4': {'n_cells': 0, 'n_rows': 0, 't_star_0.1': True, 't_star_0': True, 'n_touched_0.1': True, 'n_touched_0': True}, 'tier3/donors_D_unif_k1_r7': {'n_cells': 0, 'n_rows': 0, 't_star_0.1': True, 't_star_0': True, 'n_touched_0.1': True, 'n_touched_0': True}, 'tier3/donors_D_unif_k2_r4': {'n_cells': 0, 'n_rows': 0, 't_star_0.1': True, 't_star_0': True, 'n_touched_0.1': True, 'n_touched_0': True}, 'tier3/donors_D_unif_k2_r7': {'n_cells': 0, 'n_rows': 0, 't_star_0.1': True, 't_star_0': True, 'n_touched_0.1': True, 'n_touched_0': True}, 'tier3/donors_D_unif_k3_r4': {'n_cells': 0, 'n_rows': 0, 't_star_0.1': True, 't_star_0': True, 'n_touched_0.1': True, 'n_touched_0': True}, 'tier3/donors_D_unif_k3_r7': {'n_cells': 0, 'n_rows': 0, 't_star_0.1': True, 't_star_0': True, 'n_touched_0.1': True, 'n_touched_0': True}, 'tier3/donors_D_unif_k4_r4': {'n_cells': 0, 'n_rows': 0, 't_star_0.1': True, 't_star_0': True, 'n_touched_0.1': True, 'n_touched_0': True}, 'tier3/donors_D_unif_k4_r7': {'n_cells': 0, 'n_rows': 0, 't_star_0.1': True, 't_star_0': True, 'n_touched_0.1': True, 'n_touched_0': True}, 'tier3/donors_D_unif_k5_r4': {'n_cells': 0, 'n_rows': 0, 't_star_0.1': True, 't_star_0': True, 'n_touched_0.1': True, 'n_touched_0': True}, 'tier3/donors_D_unif_k5_r7': {'n_cells': 0, 'n_rows': 0, 't_star_0.1': True, 't_star_0': True, 'n_touched_0.1': True, 'n_touched_0': True}, 'tier3/donors_D_unif_k6_r4': {'n_cells': 0, 'n_rows': 0, 't_star_0.1': True, 't_star_0': True, 'n_touched_0.1': True, 'n_touched_0': True}, 'tier3/donors_D_unif_k6_r7': {'n_cells': 0, 'n_rows': 0, 't_star_0.1': True, 't_star_0': True, 'n_touched_0.1': True, 'n_touched_0': True}, 'tier3/donors_D_unif_k7_r4': {'n_cells': 0, 'n_rows': 0, 't_star_0.1': True, 't_star_0': True, 'n_touched_0.1': True, 'n_touched_0': True}, 'tier3/donors_D_unif_k7_r7': {'n_cells': 0, 'n_rows': 0, 't_star_0.1': True, 't_star_0': True, 'n_touched_0.1': True, 'n_touched_0': True}}, 'sigma': {'E': {'n_cells': 939, 'max_ratio_to_tolerance': 0.027889977409959674, 'pass': True}, 'E_lab': {'n_cells': 745, 'max_ratio_to_tolerance': 0.029841058036305716, 'pass': True}}}
- Two-path recompute from kl_prefix_sum and the reference arrays: E: 349 cells, 383923 checks, max ratio 0.7584, pass; E_lab: 526 cells, 312116 checks, max ratio 0.8561, pass
- Every non-reference, non-donor-side cell in exactly one chain set (rule, descriptive family, descriptive rung): E: 1259 (1185, 42, 32); E_lab: 745 (745, 0, 0)

## 1. Preconditions and the sanity checks
P1 (10/11): union/E/D_unif/tau0.1/r0/excl/ctl-none: rung 0 0.3417, rung 8 1.2876 -> pass; union/E/D_unif/tau0.1/uniform/excl/k0/ctl-none: rung 0 0.2151, rung 8 0.8650 -> pass; union/E/D_unif/tau0.1/uniform/excl/k1/ctl-none: rung 0 0.2151, rung 8 0.8650 -> pass; union/E/D_unif/tau0.1/uniform/excl/k2/ctl-none: rung 0 0.2151, rung 8 0.8652 -> pass; union/E/D_unif/tau0.1/uniform/excl/k3/ctl-none: rung 0 0.2152, rung 8 0.8651 -> pass; union/E/D_unif/tau0.1/uniform/excl/k4/ctl-none: rung 0 0.2151, rung 8 0.8649 -> pass; union/E/D_unif/tau0.1/uniform/excl/k5/ctl-none: rung 0 0.2151, rung 8 0.8650 -> pass; union/E/D_unif/tau0.1/uniform/excl/k6/ctl-none: rung 0 0.2152, rung 8 0.8651 -> pass; union/E/D_unif/tau0.1/uniform/excl/k7/ctl-none: rung 0 0.2151, rung 8 0.8650 -> pass; union/E/D_unif/tau0.5/r0/excl/ctl-none: rung 0 0.3417, rung 8 1.2892 -> pass; union/E/D_unif/tau0/r0/excl/ctl-none: rung 0 0.3417, rung 8 0.3419 -> FAIL
P2: union/E/D_unif/tau0.1/r0/excl/ctl-none: rung 8 1.2876 vs unmasked 0.0115 / importances 0.3417; union/E/D_unif/tau0.1/uniform/excl/k0/ctl-none: rung 8 0.8650 vs unmasked 0.0115 / importances 0.3417; union/E/D_unif/tau0.1/uniform/excl/k1/ctl-none: rung 8 0.8650 vs unmasked 0.0115 / importances 0.3417; union/E/D_unif/tau0.1/uniform/excl/k2/ctl-none: rung 8 0.8652 vs unmasked 0.0115 / importances 0.3417; union/E/D_unif/tau0.1/uniform/excl/k3/ctl-none: rung 8 0.8651 vs unmasked 0.0115 / importances 0.3417; union/E/D_unif/tau0.1/uniform/excl/k4/ctl-none: rung 8 0.8649 vs unmasked 0.0115 / importances 0.3417; union/E/D_unif/tau0.1/uniform/excl/k5/ctl-none: rung 8 0.8650 vs unmasked 0.0115 / importances 0.3417; union/E/D_unif/tau0.1/uniform/excl/k6/ctl-none: rung 8 0.8651 vs unmasked 0.0115 / importances 0.3417; union/E/D_unif/tau0.1/uniform/excl/k7/ctl-none: rung 8 0.8650 vs unmasked 0.0115 / importances 0.3417; union/E/D_unif/tau0.5/r0/excl/ctl-none: rung 8 1.2892 vs unmasked 0.0115 / importances 0.3417; union/E/D_unif/tau0/r0/excl/ctl-none: rung 8 0.3419 vs unmasked 0.0115 / importances 0.3417
P3: permitted cells below their label 0 of 1169; hard-zero rung-8 counts positive True -> pass
P4: 62/62 chains; descriptive rungs (2a, 2b): 2/2 chains
P5 (positive controls, by the registered rule): hard_zero/E/D_unif/tau0.1/ones/incl/ctl-none: pass (7 rungs; unconditional damage on E material at rung 4 and beyond); hard_zero/E_lab/D_code/tau0.1/ones/incl/ctl-none: FAIL (7 rungs; erase exceeds its plain control on Github); code_specific_hard/E_lab/D_code/tau0.1/ones/incl/ctl-none: FAIL (10 rungs; erase exceeds its complement control on Github); code_specific_hard/E_lab/D_code/tau0.5/ones/incl/ctl-none: pass (10 rungs; erase exceeds its complement control on Github)

| id | pass | note |
|---|---|---|
| E1 | True | rung 0 equals importances-as-masks (0.0e+00); rung 8 1.2876 against unmasked 0.0115 and the start 0.3417: above the start (the rule's own rung-8 comparison, not a bug) |
| E2/E4 | True | n_on non-decreasing within every nested run of every union chain; violations none |
| E3 | True | soft-erase rung 0 equals unmasked; rung 8 0.3615 against importances-as-masks 0.3417 |
| E6 | True | no NaN kl_mean anywhere (0 found); the sequence bootstrap widths are in the tables |
| E9 | True | clean-prefix fractions non-increasing within each nested run of every hard-zero chain at both tau_q; violations none; pairs not nested by count (skipped) 0 |

## 2. Curve 1: the union under r = 0, tau = 0.1, Delta excluded, on E
Chain `union/E/D_unif/tau0.1/r0/excl/ctl-none`; rung 0 mean 0.3417; m = 10 rungs compared; **label: fails** (at m = 8: fails); j_det = 1, j_mat = 3, first repair rung = None; per draw: k0: det 1, mat 3, k1: det 1, mat 3, k2: det 1, mat 3, k3: det 1, mat 2, k4: det 1, mat 3, k5: det 1, mat 3, k6: det 1, mat 3, k7: det 1, mat 3

| rung | n_on | mean_sigma | overlap | mean_kl | excess | interval | half_width | two_level | draws_positive | fraction_seq_above_X | detected | material | repair | differs_at_m_8 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 169.0000 | 149.4218 | 0.0261 | 0.3455 | 0.0038 | [+0.0033, +0.0042] | 0.0005 | [+0.0021, +0.0056] | 8/8 | 0.0000 | True | False | False | False |
| 2 | 1120.6250 | 1064.4031 | 0.1487 | 0.3819 | 0.0402 | [+0.0383, +0.0420] | 0.0018 | [+0.0318, +0.0537] | 8/8 | 0.2549 | True | False | False | False |
| 3 | 4543.6250 | 4414.2329 | 0.5363 | 0.7993 | 0.4575 | [+0.4444, +0.4722] | 0.0139 | [+0.4224, +0.4932] | 8/8 | 1.0000 | True | True | False | False |
| 4 | 4890.2500 | 4771.0303 | 0.5340 | 0.8294 | 0.4877 | [+0.4720, +0.5038] | 0.0159 | [+0.2644, +0.6436] | 8/8 | 1.0000 | True | True | False | False |
| 5a | 6501.3750 | 6360.5298 | 0.6985 | 1.0569 | 0.7152 | [+0.6946, +0.7369] | 0.0211 | [+0.6348, +0.8033] | 8/8 | 1.0000 | True | True | False | False |
| 5 | 7711.0000 | 7563.5215 | 0.8055 | 1.1933 | 0.8516 | [+0.8294, +0.8755] | 0.0230 | [+0.8031, +0.9029] | 8/8 | 1.0000 | True | True | False | False |
| 6a | 8489.5000 | 8339.5098 | 0.8729 | 1.2659 | 0.9242 | [+0.9000, +0.9504] | 0.0252 | [+0.8881, +0.9576] | 8/8 | 1.0000 | True | True | False | False |
| 6 | 9060.0000 | 8909.0762 | 0.9205 | 1.2944 | 0.9527 | [+0.9268, +0.9798] | 0.0265 | [+0.9255, +0.9824] | 8/8 | 1.0000 | True | True | False | False |
| 7 | 9659.2500 | 9508.0664 | 0.9724 | 1.2953 | 0.9536 | [+0.9269, +0.9813] | 0.0272 | [+0.9271, +0.9817] | 8/8 | 1.0000 | True | True | False | False |
| 8 | 9966.0000 | 9814.8027 | 0.9993 | 1.2876 | 0.9458 | [+0.9193, +0.9738] | 0.0273 | [+0.9193, +0.9738] | 1/1 | 1.0000 | True | True | False | False |

Descriptive rungs outside the comparison count (m stays 10; uncorrected 95 percent intervals):
| rung | n_on | mean_sigma | mean_kl | excess | interval_uncorrected | half_width | draws_positive | fraction_seq_above_X |
|---|---|---|---|---|---|---|---|---|
| 2a (descriptive) | 1973.7500 | 1892.7473 | 0.4433 | 0.1016 | [+0.0993, +0.1041] | 0.0024 | 8/8 | 0.9570 |
| 2b (descriptive) | 3198.5000 | 3090.8113 | 0.5729 | 0.2312 | [+0.2258, +0.2370] | 0.0056 | 8/8 | 1.0000 |

Paired union minus control on the same sequence, draw, and rung (95 percent uncorrected), with the pre-reads' overlap of the two sets: rung 1: +0.0058 [+0.0055, +0.0062] (overlap 0.026); rung 2: +0.0512 [+0.0502, +0.0523] (overlap 0.149); rung 2a: +0.1141 [+0.1122, +0.1163] (overlap 0.251); rung 2b: +0.2325 [+0.2280, +0.2375] (overlap 0.392); rung 3: +0.4178 [+0.4100, +0.4259] (overlap 0.536); rung 4: +0.4305 [+0.4201, +0.4412] (overlap 0.534); rung 5a: +0.5587 [+0.5459, +0.5715] (overlap 0.698)
Rung 4 minus rung 3 at nearly the same count (diffuse against concentrated), paired: +0.0302 [+0.0232, +0.0368].
Crossing of X = 0.05 along the position run ['1', '2', '2a', '2b', '3']: between rung 2 (n_on 1121, excess +0.0402) and rung 2a (n_on 1974, excess +0.1016); the log-linear interpolated point inside the bracket sits at n_on about 1227. Per draw: draw 0: 2 (1039) to 2a (2166), log-linear 1149; draw 1: 2 (1287) to 2a (1819), log-linear 1382; draw 2: 2 (1066) to 2a (2059), log-linear 1273; draw 3: 1 (143) to 2 (1530), log-linear 788; draw 4: 2 (1201) to 2a (2166), log-linear 1263; draw 5: 2 (891) to 2a (1767), log-linear 1063; draw 6: 2 (950) to 2a (1749), log-linear 1156; draw 7: 2 (1001) to 2a (1968), log-linear 1234.
Rung 4 (one donor sequence): excess +0.4877 [+0.4720, +0.5038], fraction of sequences with excess above X 1.000.
Per-rung excess by reader label on E (each label's own resample, the curve's m):
| label | n | rung | excess | interval | half_width | detected | material |
|---|---|---|---|---|---|---|---|
| code | 120 | 1 | 0.0079 | [+0.0064, +0.0096] | 0.0016 | False | False |
| code | 120 | 2 | 0.0583 | [+0.0517, +0.0664] | 0.0073 | True | True |
| code | 120 | 3 | 0.6017 | [+0.5568, +0.6513] | 0.0472 | True | True |
| code | 120 | 4 | 0.6513 | [+0.6104, +0.6959] | 0.0427 | True | True |
| code | 120 | 5a | 0.8918 | [+0.8321, +0.9574] | 0.0626 | True | True |
| code | 120 | 5 | 1.0570 | [+0.9882, +1.1314] | 0.0716 | True | True |
| code | 120 | 6a | 1.2314 | [+1.1505, +1.3168] | 0.0831 | True | True |
| code | 120 | 6 | 1.2855 | [+1.1996, +1.3763] | 0.0883 | True | True |
| code | 120 | 7 | 1.2869 | [+1.2011, +1.3794] | 0.0891 | True | True |
| code | 120 | 8 | 1.2782 | [+1.1928, +1.3701] | 0.0886 | True | True |
| mixed | 27 | 1 | 0.0060 | [+0.0039, +0.0079] | 0.0020 | False | False |
| mixed | 27 | 2 | 0.0435 | [+0.0367, +0.0506] | 0.0069 | True | False |
| mixed | 27 | 3 | 0.4865 | [+0.4384, +0.5404] | 0.0510 | True | True |
| mixed | 27 | 4 | 0.5613 | [+0.5167, +0.6091] | 0.0462 | True | True |
| mixed | 27 | 5a | 0.7900 | [+0.7268, +0.8579] | 0.0655 | True | True |
| mixed | 27 | 5 | 0.9331 | [+0.8618, +1.0077] | 0.0730 | True | True |
| mixed | 27 | 6a | 1.0378 | [+0.9549, +1.1224] | 0.0838 | True | True |
| mixed | 27 | 6 | 1.0660 | [+0.9796, +1.1575] | 0.0890 | True | True |
| mixed | 27 | 7 | 1.0624 | [+0.9777, +1.1543] | 0.0883 | True | True |
| mixed | 27 | 8 | 1.0547 | [+0.9694, +1.1466] | 0.0886 | True | True |
| other | 158 | 1 | 0.0001 | [-0.0010, +0.0015] | 0.0013 | False | False |
| other | 158 | 2 | 0.0419 | [+0.0368, +0.0473] | 0.0052 | True | False |
| other | 158 | 3 | 0.4730 | [+0.4248, +0.5292] | 0.0522 | True | True |
| other | 158 | 4 | 0.3870 | [+0.3240, +0.4537] | 0.0648 | True | True |
| other | 158 | 5a | 0.6074 | [+0.5230, +0.6972] | 0.0871 | True | True |
| other | 158 | 5 | 0.8005 | [+0.7134, +0.8973] | 0.0919 | True | True |
| other | 158 | 6a | 0.9891 | [+0.9064, +1.0853] | 0.0894 | True | True |
| other | 158 | 6 | 1.1076 | [+1.0251, +1.2037] | 0.0893 | True | True |
| other | 158 | 7 | 1.1639 | [+1.0819, +1.2596] | 0.0888 | True | True |
| other | 158 | 8 | 1.1611 | [+1.0785, +1.2576] | 0.0895 | True | True |
| prose | 719 | 1 | 0.0038 | [+0.0033, +0.0043] | 0.0005 | True | False |
| prose | 719 | 2 | 0.0366 | [+0.0350, +0.0384] | 0.0017 | True | False |
| prose | 719 | 3 | 0.4290 | [+0.4176, +0.4405] | 0.0115 | True | True |
| prose | 719 | 4 | 0.4798 | [+0.4666, +0.4925] | 0.0129 | True | True |
| prose | 719 | 5a | 0.7066 | [+0.6890, +0.7243] | 0.0176 | True | True |
| prose | 719 | 5 | 0.8255 | [+0.8047, +0.8470] | 0.0212 | True | True |
| prose | 719 | 6a | 0.8544 | [+0.8330, +0.8765] | 0.0217 | True | True |
| prose | 719 | 6 | 0.8588 | [+0.8372, +0.8808] | 0.0218 | True | True |
| prose | 719 | 7 | 0.8477 | [+0.8262, +0.8697] | 0.0217 | True | True |
| prose | 719 | 8 | 0.8390 | [+0.8176, +0.8608] | 0.0216 | True | True |

Paired union minus control by reader label at rungs 1 to 4 and 5a (each label's own resample, uncorrected 95 percent), the control's per-label excess beside:
| label | n | rung | union_minus_control | interval_uncorrected | half_width | control_excess | control_interval_uncorrected |
|---|---|---|---|---|---|---|---|
| code | 120 | 1 | 0.0091 | [+0.0081, +0.0102] | 0.0011 | -0.0012 | [-0.0015, -0.0010] |
| code | 120 | 2 | 0.0628 | [+0.0582, +0.0680] | 0.0049 | -0.0045 | [-0.0055, -0.0034] |
| code | 120 | 3 | 0.5267 | [+0.4968, +0.5582] | 0.0307 | 0.0750 | [+0.0701, +0.0802] |
| code | 120 | 4 | 0.5674 | [+0.5401, +0.5957] | 0.0278 | 0.0838 | [+0.0791, +0.0886] |
| code | 120 | 5a | 0.6826 | [+0.6466, +0.7198] | 0.0366 | 0.2092 | [+0.1989, +0.2203] |
| mixed | 27 | 1 | 0.0087 | [+0.0074, +0.0099] | 0.0013 | -0.0027 | [-0.0031, -0.0023] |
| mixed | 27 | 2 | 0.0554 | [+0.0516, +0.0590] | 0.0037 | -0.0118 | [-0.0138, -0.0098] |
| mixed | 27 | 3 | 0.4445 | [+0.4150, +0.4745] | 0.0297 | 0.0420 | [+0.0342, +0.0515] |
| mixed | 27 | 4 | 0.5021 | [+0.4737, +0.5321] | 0.0292 | 0.0592 | [+0.0520, +0.0677] |
| mixed | 27 | 5a | 0.6275 | [+0.5913, +0.6658] | 0.0373 | 0.1624 | [+0.1487, +0.1786] |
| other | 158 | 1 | 0.0004 | [-0.0006, +0.0014] | 0.0010 | -0.0002 | [-0.0006, +0.0002] |
| other | 158 | 2 | 0.0424 | [+0.0388, +0.0461] | 0.0036 | -0.0005 | [-0.0021, +0.0011] |
| other | 158 | 3 | 0.3854 | [+0.3565, +0.4165] | 0.0300 | 0.0876 | [+0.0774, +0.0986] |
| other | 158 | 4 | 0.2926 | [+0.2517, +0.3356] | 0.0419 | 0.0944 | [+0.0857, +0.1036] |
| other | 158 | 5a | 0.3827 | [+0.3328, +0.4360] | 0.0516 | 0.2247 | [+0.2071, +0.2437] |
| prose | 719 | 1 | 0.0064 | [+0.0061, +0.0067] | 0.0003 | -0.0026 | [-0.0027, -0.0025] |
| prose | 719 | 2 | 0.0511 | [+0.0502, +0.0519] | 0.0009 | -0.0144 | [-0.0150, -0.0139] |
| prose | 719 | 3 | 0.4058 | [+0.3990, +0.4125] | 0.0067 | 0.0232 | [+0.0211, +0.0252] |
| prose | 719 | 4 | 0.4352 | [+0.4262, +0.4440] | 0.0089 | 0.0445 | [+0.0426, +0.0464] |
| prose | 719 | 5a | 0.5741 | [+0.5631, +0.5851] | 0.0110 | 0.1325 | [+0.1290, +0.1360] |

## 2b. Its plain control
Chain `union/E/D_unif/tau0.1/r0/excl/ctl-plain`; rung 0 mean 0.3417; m = 10 rungs compared; **label: fails** (at m = 8: fails); j_det = 3, j_mat = 4, first repair rung = 1; per draw: k0: det 3, mat 4, k1: det 3, mat 5a, k2: det 3, mat 5a, k3: det 3, mat 5a, k4: det 3, mat 5a, k5: det 3, mat 4, k6: det 3, mat 4, k7: det 3, mat 4

| rung | n_on | mean_sigma | overlap | mean_kl | excess | interval | half_width | two_level | draws_positive | fraction_seq_above_X | detected | material | repair | differs_at_m_8 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 169.0000 | 165.9057 | 0.0261 | 0.3397 | -0.0021 | [-0.0022, -0.0019] | 0.0002 | [-0.0030, -0.0013] | 0/8 | 0.0000 | False | False | True | False |
| 2 | 1120.6250 | 1099.6158 | 0.1487 | 0.3307 | -0.0110 | [-0.0119, -0.0102] | 0.0008 | [-0.0124, -0.0096] | 0/8 | 0.0000 | False | False | True | False |
| 3 | 4543.6250 | 4463.8711 | 0.5363 | 0.3814 | 0.0397 | [+0.0358, +0.0439] | 0.0041 | [+0.0297, +0.0485] | 8/8 | 0.3740 | True | False | False | False |
| 4 | 4890.2500 | 4808.7080 | 0.5340 | 0.3989 | 0.0572 | [+0.0539, +0.0607] | 0.0034 | [+0.0149, +0.1133] | 7/8 | 0.5352 | True | True | False | False |
| 5a | 6501.3750 | 6393.8550 | 0.6985 | 0.4982 | 0.1565 | [+0.1503, +0.1634] | 0.0065 | [+0.1011, +0.2241] | 8/8 | 0.9883 | True | True | False | False |
| 5 | 7711.0000 | 7586.0557 | 0.8055 | 0.6639 | 0.3222 | [+0.3112, +0.3342] | 0.0115 | [+0.2662, +0.3871] | 8/8 | 1.0000 | True | True | False | False |
| 6a | 8489.5000 | 8353.4668 | 0.8729 | 0.8500 | 0.5082 | [+0.4920, +0.5265] | 0.0173 | [+0.4469, +0.5573] | 8/8 | 1.0000 | True | True | False | False |
| 6 | 9060.0000 | 8917.4688 | 0.9205 | 1.0150 | 0.6732 | [+0.6524, +0.6961] | 0.0218 | [+0.6285, +0.7229] | 8/8 | 1.0000 | True | True | False | False |
| 7 | 9659.2500 | 9510.6230 | 0.9724 | 1.2023 | 0.8606 | [+0.8358, +0.8874] | 0.0258 | [+0.8168, +0.9015] | 8/8 | 1.0000 | True | True | False | False |
| 8 | 9966.0000 | 9814.8027 | 0.9993 | 1.2876 | 0.9459 | [+0.9193, +0.9738] | 0.0273 | [+0.9193, +0.9738] | 1/1 | 1.0000 | True | True | False | False |

Descriptive rungs outside the comparison count (m stays 10; uncorrected 95 percent intervals):
| rung | n_on | mean_sigma | mean_kl | excess | interval_uncorrected | half_width | draws_positive | fraction_seq_above_X |
|---|---|---|---|---|---|---|---|---|
| 2a (descriptive) | 1973.7500 | 1937.4500 | 0.3292 | -0.0125 | [-0.0135, -0.0115] | 0.0010 | 0/8 | 0.0039 |
| 2b (descriptive) | 3198.5000 | 3141.0071 | 0.3403 | -0.0014 | [-0.0030, +0.0003] | 0.0016 | 2/8 | 0.0176 |
Rung 4 (one donor sequence): excess +0.0572 [+0.0539, +0.0607], fraction of sequences with excess above X 0.535.

## 3. The mass-matched deciles and the slope
`union/E/D_unif/tau0.1/r0/excl/ctl-none`: edges from pre-reads: 23.1, 202.8, 1221.7, 4396.4, 5304.6, 6498.0, 7512.9, 8218.7, 8791.4, 9421.1, 9708.9; union slope 1.116e-04 [+1.095e-04, +1.137e-04] (intercept -0.0348 [-0.0378, -0.0319]); control slope 8.189e-05 [+8.019e-05, +8.368e-05]
| bin | overflow | edge_low | edge_high | n_points_union | n_points_control | n_sequences_union | n_sequences_control | populated | union_mean_excess | control_mean_excess | difference | interval |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 0 | False | 23.1357 | 202.8046 | 7372 | 5120 | 1024 | 1024 | True | 0.0042 | -0.0017 | 0.0059 | [+0.0056, +0.0063] |
| 1 | False | 202.8046 | 1221.7465 | 7373 | 9216 | 1024 | 1024 | True | 0.0331 | -0.0082 | 0.0414 | [+0.0403, +0.0425] |
| 2 | False | 1221.7465 | 4396.4055 | 7373 | 6043 | 1024 | 1024 | True | 0.2979 | 0.0082 | 0.2897 | [+0.2826, +0.2971] |
| 3 | False | 4396.4055 | 5304.6058 | 7372 | 8308 | 1024 | 1024 | True | 0.4920 | 0.0410 | 0.4511 | [+0.4418, +0.4607] |
| 4 | False | 5304.6058 | 6498.0445 | 7373 | 7578 | 1024 | 1024 | True | 0.6492 | 0.0988 | 0.5504 | [+0.5376, +0.5632] |
| 5 | False | 6498.0445 | 7512.8537 | 7373 | 7789 | 1024 | 1024 | True | 0.7846 | 0.2228 | 0.5618 | [+0.5476, +0.5761] |
| 6 | False | 7512.8537 | 8218.7061 | 7372 | 7149 | 1024 | 1024 | True | 0.9001 | 0.3880 | 0.5121 | [+0.5017, +0.5227] |
| 7 | False | 8218.7061 | 8791.3866 | 7373 | 7448 | 1024 | 1024 | True | 0.9341 | 0.5476 | 0.3865 | [+0.3796, +0.3936] |
| 8 | False | 8791.3866 | 9421.1109 | 7373 | 7468 | 1024 | 1024 | True | 0.9641 | 0.7103 | 0.2538 | [+0.2498, +0.2579] |
| 9 | False | 9421.1109 | 9708.9387 | 7372 | 7607 | 1024 | 1024 | True | 0.9255 | 0.8398 | 0.0857 | [+0.0839, +0.0875] |
| 10 | True | 9708.9387 | inf | 1 | 2 | 1 | 2 | False |  |  |  |  |
Local slopes (difference quotients): 1->2: 3.978e-05; 2->3: 1.246e-04; 3->4: 8.451e-05; 4->5a: 1.432e-04; 5a->5: 1.134e-04; 5->6a: 9.352e-05; 6a->6: 4.999e-05; 6->7: 1.544e-06

`union/E/D_unif/tau0.1/uniform/excl/k0/ctl-none`: edges from the loop's sigma column: 79.4, 93.1, 493.6, 2185.9, 3311.1, 3678.8, 4007.2, 4250.2, 4519.4, 4811.1, 4855.5; union slope 1.521e-04 [+1.486e-04, +1.557e-04] (intercept +0.0156 [+0.0126, +0.0183]); control slope 1.295e-04 [+1.267e-04, +1.324e-04]
| bin | overflow | edge_low | edge_high | n_points_union | n_points_control | n_sequences_union | n_sequences_control | populated | union_mean_excess | control_mean_excess | difference | interval |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 0 | False | 79.3522 | 93.1002 | 922 | 0 | 922 | 0 | False | 0.0107 |  |  |  |
| 1 | False | 93.1002 | 493.6082 | 921 | 1024 | 904 | 1024 | True | 0.0477 | 0.0003 | 0.0474 | [+0.0458, +0.0490] |
| 2 | False | 493.6082 | 2185.9388 | 922 | 1024 | 897 | 1024 | True | 0.3275 | 0.0037 | 0.3238 | [+0.3114, +0.3360] |
| 3 | False | 2185.9388 | 3311.1470 | 921 | 1050 | 902 | 1024 | True | 0.5535 | 0.0876 | 0.4659 | [+0.4508, +0.4814] |
| 4 | False | 3311.1470 | 3678.7576 | 922 | 1041 | 915 | 1024 | True | 0.6174 | 0.2332 | 0.3842 | [+0.3712, +0.3977] |
| 5 | False | 3678.7576 | 4007.1804 | 921 | 1035 | 921 | 1024 | True | 0.6370 | 0.3281 | 0.3089 | [+0.2990, +0.3190] |
| 6 | False | 4007.1804 | 4250.2256 | 922 | 1050 | 922 | 1024 | True | 0.6623 | 0.4199 | 0.2424 | [+0.2338, +0.2510] |
| 7 | False | 4250.2256 | 4519.4385 | 921 | 1052 | 921 | 1024 | True | 0.6567 | 0.4966 | 0.1601 | [+0.1532, +0.1670] |
| 8 | False | 4519.4385 | 4811.1101 | 922 | 1011 | 922 | 1010 | True | 0.6463 | 0.5666 | 0.0796 | [+0.0741, +0.0847] |
| 9 | False | 4811.1101 | 4855.5332 | 922 | 928 | 922 | 928 | True | 0.6206 | 0.6076 | 0.0130 | [+0.0115, +0.0145] |
| 10 | True | 4855.5332 | inf | 0 | 1 | 0 | 1 | False |  |  |  |  |
Local slopes (difference quotients): 1->2: 9.786e-05; 2->3: 1.927e-04; 3->4: 1.854e-04; 4->5a: 1.496e-04; 5a->5: 6.878e-05; 5->6a: 2.045e-06; 6a->6: 6.556e-06; 6->7: -3.091e-05

`union/E/D_unif/tau0.1/uniform/excl/k1/ctl-none`: edges from the loop's sigma column: 92.2, 104.2, 616.2, 2034.6, 2170.2, 3232.0, 3825.2, 4178.8, 4364.4, 4704.0, 4749.8; union slope 1.565e-04 [+1.532e-04, +1.598e-04] (intercept +0.0181 [+0.0156, +0.0206]); control slope 1.273e-04 [+1.243e-04, +1.304e-04]
| bin | overflow | edge_low | edge_high | n_points_union | n_points_control | n_sequences_union | n_sequences_control | populated | union_mean_excess | control_mean_excess | difference | interval |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 0 | False | 92.1614 | 104.2381 | 922 | 0 | 922 | 0 | False | 0.0078 |  |  |  |
| 1 | False | 104.2381 | 616.1554 | 921 | 1024 | 909 | 1024 | True | 0.0553 | 0.0007 | 0.0546 | [+0.0528, +0.0564] |
| 2 | False | 616.1554 | 2034.6420 | 922 | 1027 | 880 | 1024 | True | 0.3466 | 0.0076 | 0.3390 | [+0.3229, +0.3559] |
| 3 | False | 2034.6420 | 2170.1582 | 921 | 1021 | 900 | 1021 | True | 0.3649 | 0.0584 | 0.3065 | [+0.2957, +0.3179] |
| 4 | False | 2170.1582 | 3231.9663 | 922 | 1038 | 908 | 1024 | True | 0.5483 | 0.0928 | 0.4555 | [+0.4393, +0.4720] |
| 5 | False | 3231.9663 | 3825.2224 | 921 | 1048 | 915 | 1024 | True | 0.6342 | 0.2304 | 0.4039 | [+0.3927, +0.4151] |
| 6 | False | 3825.2224 | 4178.8069 | 922 | 1047 | 921 | 1024 | True | 0.6631 | 0.3701 | 0.2931 | [+0.2852, +0.3008] |
| 7 | False | 4178.8069 | 4364.3779 | 921 | 1022 | 921 | 1021 | True | 0.6682 | 0.4506 | 0.2176 | [+0.2116, +0.2239] |
| 8 | False | 4364.3779 | 4703.9817 | 922 | 1035 | 922 | 1024 | True | 0.6566 | 0.5022 | 0.1544 | [+0.1491, +0.1596] |
| 9 | False | 4703.9817 | 4749.8198 | 922 | 953 | 922 | 953 | True | 0.6234 | 0.5584 | 0.0650 | [+0.0620, +0.0677] |
| 10 | True | 4749.8198 | inf | 0 | 1 | 0 | 1 | False |  |  |  |  |
Local slopes (difference quotients): 1->2: 9.355e-05; 2->3: 2.180e-04; 3->4: 1.847e-04; 4->5a: 2.098e-04; 5a->5: 6.905e-05; 5->6a: 3.071e-05; 6a->6: -5.552e-06; 6->7: -3.886e-05

`union/E/D_unif/tau0.1/uniform/excl/k2/ctl-none`: edges from the loop's sigma column: 93.9, 105.1, 510.0, 2257.7, 2558.5, 3260.8, 3935.9, 4288.3, 4471.2, 4726.4, 4771.3; union slope 1.492e-04 [+1.459e-04, +1.527e-04] (intercept +0.0194 [+0.0161, +0.0225]); control slope 1.275e-04 [+1.246e-04, +1.305e-04]
| bin | overflow | edge_low | edge_high | n_points_union | n_points_control | n_sequences_union | n_sequences_control | populated | union_mean_excess | control_mean_excess | difference | interval |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 0 | False | 93.9404 | 105.0779 | 922 | 0 | 922 | 0 | False | 0.0085 |  |  |  |
| 1 | False | 105.0779 | 510.0085 | 921 | 1024 | 918 | 1024 | True | 0.0463 | 0.0005 | 0.0458 | [+0.0443, +0.0473] |
| 2 | False | 510.0085 | 2257.7382 | 922 | 1025 | 832 | 1024 | True | 0.3756 | 0.0047 | 0.3710 | [+0.3581, +0.3838] |
| 3 | False | 2257.7382 | 2558.5432 | 921 | 1025 | 907 | 1024 | True | 0.4548 | 0.0970 | 0.3578 | [+0.3465, +0.3701] |
| 4 | False | 2558.5432 | 3260.7600 | 922 | 1038 | 920 | 1024 | True | 0.4973 | 0.1072 | 0.3901 | [+0.3766, +0.4042] |
| 5 | False | 3260.7600 | 3935.9221 | 921 | 1053 | 905 | 1024 | True | 0.5814 | 0.2242 | 0.3572 | [+0.3454, +0.3695] |
| 6 | False | 3935.9221 | 4288.3394 | 922 | 1078 | 920 | 1024 | True | 0.6325 | 0.3883 | 0.2441 | [+0.2358, +0.2529] |
| 7 | False | 4288.3394 | 4471.2017 | 921 | 1018 | 921 | 1018 | True | 0.6559 | 0.4878 | 0.1681 | [+0.1626, +0.1737] |
| 8 | False | 4471.2017 | 4726.3652 | 922 | 1001 | 922 | 1001 | True | 0.6481 | 0.5337 | 0.1144 | [+0.1086, +0.1203] |
| 9 | False | 4726.3652 | 4771.2573 | 922 | 953 | 922 | 953 | True | 0.6245 | 0.5721 | 0.0524 | [+0.0484, +0.0557] |
| 10 | True | 4771.2573 | inf | 0 | 1 | 0 | 1 | False |  |  |  |  |
Local slopes (difference quotients): 1->2: 9.152e-05; 2->3: 2.250e-04; 3->4: -3.411e-05; 4->5a: 1.638e-04; 5a->5: 1.201e-04; 5->6a: 1.057e-04; 6a->6: 1.206e-05; 6->7: -1.684e-05

`union/E/D_unif/tau0.1/uniform/excl/k3/ctl-none`: edges from the loop's sigma column: 57.7, 65.5, 663.3, 736.0, 2197.2, 2767.9, 3803.3, 4086.1, 4399.4, 4703.2, 4749.1; union slope 1.568e-04 [+1.535e-04, +1.604e-04] (intercept -0.0027 [-0.0049, -0.0004]); control slope 1.231e-04 [+1.203e-04, +1.261e-04]
| bin | overflow | edge_low | edge_high | n_points_union | n_points_control | n_sequences_union | n_sequences_control | populated | union_mean_excess | control_mean_excess | difference | interval |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 0 | False | 57.7341 | 65.4719 | 922 | 0 | 922 | 0 | False | 0.0062 |  |  |  |
| 1 | False | 65.4719 | 663.2516 | 921 | 1024 | 847 | 1024 | True | 0.0353 | 0.0002 | 0.0350 | [+0.0331, +0.0371] |
| 2 | False | 663.2516 | 735.9885 | 922 | 1024 | 876 | 1024 | True | 0.0722 | 0.0031 | 0.0691 | [+0.0654, +0.0733] |
| 3 | False | 735.9885 | 2197.1689 | 921 | 1024 | 897 | 1024 | True | 0.3485 | 0.0074 | 0.3411 | [+0.3245, +0.3583] |
| 4 | False | 2197.1689 | 2767.8572 | 922 | 1026 | 919 | 1024 | True | 0.4958 | 0.0881 | 0.4077 | [+0.3964, +0.4191] |
| 5 | False | 2767.8572 | 3803.3113 | 921 | 1056 | 912 | 1024 | True | 0.5716 | 0.1476 | 0.4240 | [+0.4107, +0.4377] |
| 6 | False | 3803.3113 | 4086.0950 | 922 | 1037 | 922 | 1024 | True | 0.6231 | 0.3238 | 0.2993 | [+0.2900, +0.3089] |
| 7 | False | 4086.0950 | 4399.4243 | 921 | 1059 | 921 | 1024 | True | 0.6263 | 0.4038 | 0.2225 | [+0.2148, +0.2305] |
| 8 | False | 4399.4243 | 4703.1731 | 922 | 1013 | 922 | 1013 | True | 0.6529 | 0.5289 | 0.1239 | [+0.1189, +0.1287] |
| 9 | False | 4703.1731 | 4749.0522 | 922 | 950 | 922 | 950 | True | 0.6258 | 0.5671 | 0.0586 | [+0.0544, +0.0623] |
| 10 | True | 4749.0522 | inf | 0 | 3 | 0 | 3 | False |  |  |  |  |
Local slopes (difference quotients): 1->2: 1.018e-04; 2->3: 2.485e-04; 3->4: 2.619e-04; 4->5a: 2.270e-04; 5a->5: 1.081e-04; 5->6a: 1.944e-05; 6a->6: 1.148e-04; 6->7: -2.301e-05

`union/E/D_unif/tau0.1/uniform/excl/k4/ctl-none`: edges from the loop's sigma column: 81.6, 99.2, 578.2, 2060.0, 2432.1, 2841.9, 3761.0, 4112.0, 4451.4, 4765.7, 4810.2; union slope 1.531e-04 [+1.498e-04, +1.566e-04] (intercept +0.0140 [+0.0110, +0.0171]); control slope 1.322e-04 [+1.291e-04, +1.354e-04]
| bin | overflow | edge_low | edge_high | n_points_union | n_points_control | n_sequences_union | n_sequences_control | populated | union_mean_excess | control_mean_excess | difference | interval |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 0 | False | 81.5884 | 99.1843 | 922 | 0 | 922 | 0 | False | 0.0052 |  |  |  |
| 1 | False | 99.1843 | 578.1752 | 921 | 1024 | 913 | 1024 | True | 0.0498 | 0.0004 | 0.0494 | [+0.0467, +0.0522] |
| 2 | False | 578.1752 | 2060.0056 | 922 | 1024 | 858 | 1024 | True | 0.3356 | 0.0070 | 0.3286 | [+0.3158, +0.3417] |
| 3 | False | 2060.0056 | 2432.0962 | 921 | 1030 | 898 | 1024 | True | 0.4279 | 0.0760 | 0.3519 | [+0.3385, +0.3661] |
| 4 | False | 2432.0962 | 2841.8519 | 922 | 1030 | 917 | 1024 | True | 0.4523 | 0.0903 | 0.3620 | [+0.3464, +0.3783] |
| 5 | False | 2841.8519 | 3760.9927 | 921 | 1055 | 919 | 1024 | True | 0.5481 | 0.1562 | 0.3920 | [+0.3774, +0.4073] |
| 6 | False | 3760.9927 | 4111.9961 | 922 | 1048 | 915 | 1024 | True | 0.6606 | 0.3474 | 0.3131 | [+0.3055, +0.3211] |
| 7 | False | 4111.9961 | 4451.4058 | 921 | 1047 | 921 | 1024 | True | 0.6604 | 0.4529 | 0.2076 | [+0.2016, +0.2135] |
| 8 | False | 4451.4058 | 4765.6738 | 922 | 1017 | 922 | 1014 | True | 0.6480 | 0.5364 | 0.1116 | [+0.1063, +0.1167] |
| 9 | False | 4765.6738 | 4810.2256 | 922 | 939 | 922 | 939 | True | 0.6238 | 0.6019 | 0.0219 | [+0.0192, +0.0245] |
| 10 | True | 4810.2256 | inf | 0 | 2 | 0 | 2 | False |  |  |  |  |
Local slopes (difference quotients): 1->2: 9.238e-05; 2->3: 2.271e-04; 3->4: 4.083e-05; 4->5a: 1.953e-04; 5a->5: 1.889e-04; 5->6a: 4.104e-05; 6a->6: -1.564e-05; 6->7: -2.031e-05

`union/E/D_unif/tau0.1/uniform/excl/k5/ctl-none`: edges from the loop's sigma column: 60.6, 70.0, 423.5, 2303.2, 2743.7, 3172.9, 3661.3, 4233.5, 4508.8, 4709.3, 4755.8; union slope 1.492e-04 [+1.459e-04, +1.527e-04] (intercept +0.0312 [+0.0276, +0.0347]); control slope 1.291e-04 [+1.261e-04, +1.322e-04]
| bin | overflow | edge_low | edge_high | n_points_union | n_points_control | n_sequences_union | n_sequences_control | populated | union_mean_excess | control_mean_excess | difference | interval |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 0 | False | 60.5756 | 70.0268 | 922 | 0 | 922 | 0 | False | 0.0072 |  |  |  |
| 1 | False | 70.0268 | 423.4513 | 921 | 1024 | 919 | 1024 | True | 0.0465 | 0.0003 | 0.0462 | [+0.0445, +0.0479] |
| 2 | False | 423.4513 | 2303.1855 | 922 | 1032 | 836 | 1024 | True | 0.3859 | 0.0058 | 0.3800 | [+0.3667, +0.3933] |
| 3 | False | 2303.1855 | 2743.6997 | 921 | 1026 | 898 | 1024 | True | 0.5033 | 0.0936 | 0.4098 | [+0.3992, +0.4206] |
| 4 | False | 2743.6997 | 3172.9176 | 922 | 1027 | 919 | 1024 | True | 0.5230 | 0.1297 | 0.3932 | [+0.3805, +0.4063] |
| 5 | False | 3172.9176 | 3661.2588 | 921 | 1044 | 920 | 1024 | True | 0.5661 | 0.2006 | 0.3655 | [+0.3542, +0.3767] |
| 6 | False | 3661.2588 | 4233.5098 | 922 | 1088 | 895 | 1024 | True | 0.6237 | 0.3274 | 0.2963 | [+0.2873, +0.3054] |
| 7 | False | 4233.5098 | 4508.8042 | 921 | 1044 | 921 | 1024 | True | 0.6592 | 0.4987 | 0.1605 | [+0.1551, +0.1658] |
| 8 | False | 4508.8042 | 4709.3384 | 922 | 979 | 922 | 979 | True | 0.6562 | 0.5707 | 0.0856 | [+0.0800, +0.0915] |
| 9 | False | 4709.3384 | 4755.7593 | 922 | 951 | 922 | 951 | True | 0.6253 | 0.5897 | 0.0357 | [+0.0309, +0.0396] |
| 10 | True | 4755.7593 | inf | 0 | 1 | 0 | 1 | False |  |  |  |  |
Local slopes (difference quotients): 1->2: 1.071e-04; 2->3: 2.155e-04; 3->4: 9.375e-05; 4->5a: 1.318e-04; 5a->5: 1.041e-04; 5->6a: 1.165e-04; 6a->6: 1.931e-05; 6->7: -5.102e-05

`union/E/D_unif/tau0.1/uniform/excl/k6/ctl-none`: edges from the loop's sigma column: 11.6, 14.9, 451.9, 2268.4, 2708.9, 3105.4, 3650.8, 4062.9, 4388.8, 4760.6, 4804.4; union slope 1.514e-04 [+1.481e-04, +1.547e-04] (intercept +0.0226 [+0.0192, +0.0259]); control slope 1.240e-04 [+1.213e-04, +1.270e-04]
| bin | overflow | edge_low | edge_high | n_points_union | n_points_control | n_sequences_union | n_sequences_control | populated | union_mean_excess | control_mean_excess | difference | interval |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 0 | False | 11.6245 | 14.9203 | 922 | 0 | 922 | 0 | False | 0.0007 |  |  |  |
| 1 | False | 14.9203 | 451.8847 | 921 | 1024 | 862 | 1024 | True | 0.0394 | -0.0001 | 0.0394 | [+0.0383, +0.0406] |
| 2 | False | 451.8847 | 2268.3521 | 922 | 1030 | 885 | 1024 | True | 0.3716 | 0.0056 | 0.3660 | [+0.3518, +0.3806] |
| 3 | False | 2268.3521 | 2708.8521 | 921 | 1028 | 893 | 1024 | True | 0.4623 | 0.0922 | 0.3701 | [+0.3601, +0.3802] |
| 4 | False | 2708.8521 | 3105.4166 | 922 | 1028 | 895 | 1024 | True | 0.5138 | 0.1246 | 0.3892 | [+0.3760, +0.4024] |
| 5 | False | 3105.4166 | 3650.7617 | 921 | 1040 | 915 | 1024 | True | 0.5714 | 0.2001 | 0.3713 | [+0.3601, +0.3827] |
| 6 | False | 3650.7617 | 4062.8584 | 922 | 1053 | 919 | 1024 | True | 0.6188 | 0.3158 | 0.3030 | [+0.2937, +0.3123] |
| 7 | False | 4062.8584 | 4388.7744 | 921 | 1038 | 921 | 1024 | True | 0.6555 | 0.4390 | 0.2165 | [+0.2095, +0.2237] |
| 8 | False | 4388.7744 | 4760.6282 | 922 | 1024 | 922 | 1019 | True | 0.6476 | 0.5286 | 0.1190 | [+0.1131, +0.1249] |
| 9 | False | 4760.6282 | 4804.4136 | 922 | 949 | 922 | 949 | True | 0.6227 | 0.5957 | 0.0270 | [+0.0227, +0.0305] |
| 10 | True | 4804.4136 | inf | 0 | 2 | 0 | 2 | False |  |  |  |  |
Local slopes (difference quotients): 1->2: 8.678e-05; 2->3: 2.107e-04; 3->4: 8.411e-05; 4->5a: 2.449e-04; 5a->5: 9.392e-05; 5->6a: 1.023e-04; 6a->6: 4.406e-05; 6->7: -1.736e-05

`union/E/D_unif/tau0.1/uniform/excl/k7/ctl-none`: edges from the loop's sigma column: 62.1, 71.0, 477.7, 2235.6, 2646.2, 3372.2, 3584.2, 4109.9, 4480.1, 4767.0, 4811.6; union slope 1.516e-04 [+1.483e-04, +1.550e-04] (intercept +0.0220 [+0.0193, +0.0245]); control slope 1.248e-04 [+1.220e-04, +1.277e-04]
| bin | overflow | edge_low | edge_high | n_points_union | n_points_control | n_sequences_union | n_sequences_control | populated | union_mean_excess | control_mean_excess | difference | interval |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 0 | False | 62.0918 | 71.0284 | 922 | 0 | 922 | 0 | False | 0.0056 |  |  |  |
| 1 | False | 71.0284 | 477.7080 | 921 | 1024 | 909 | 1024 | True | 0.0380 | 0.0002 | 0.0378 | [+0.0364, +0.0393] |
| 2 | False | 477.7080 | 2235.5909 | 922 | 1025 | 886 | 1024 | True | 0.3658 | 0.0043 | 0.3615 | [+0.3465, +0.3770] |
| 3 | False | 2235.5909 | 2646.1768 | 921 | 1029 | 887 | 1024 | True | 0.4801 | 0.0876 | 0.3926 | [+0.3837, +0.4017] |
| 4 | False | 2646.1768 | 3372.2040 | 922 | 1038 | 906 | 1024 | True | 0.5301 | 0.1169 | 0.4132 | [+0.3998, +0.4271] |
| 5 | False | 3372.2040 | 3584.1887 | 921 | 1029 | 921 | 1024 | True | 0.5831 | 0.2279 | 0.3552 | [+0.3438, +0.3667] |
| 6 | False | 3584.1887 | 4109.9011 | 922 | 1066 | 911 | 1024 | True | 0.6133 | 0.2825 | 0.3308 | [+0.3198, +0.3423] |
| 7 | False | 4109.9011 | 4480.0684 | 921 | 1067 | 920 | 1024 | True | 0.6612 | 0.4456 | 0.2156 | [+0.2083, +0.2228] |
| 8 | False | 4480.0684 | 4766.9902 | 922 | 998 | 922 | 998 | True | 0.6581 | 0.5433 | 0.1148 | [+0.1095, +0.1201] |
| 9 | False | 4766.9902 | 4811.5640 | 922 | 938 | 922 | 938 | True | 0.6231 | 0.5995 | 0.0236 | [+0.0204, +0.0264] |
| 10 | True | 4811.5640 | inf | 0 | 2 | 0 | 2 | False |  |  |  |  |
Local slopes (difference quotients): 1->2: 8.281e-05; 2->3: 2.210e-04; 3->4: 9.767e-05; 4->5a: 1.393e-04; 5a->5: 1.172e-04; 5->6a: 1.431e-04; 6a->6: 1.130e-05; 6->7: -5.470e-05

`union/E/D_unif/tau0.5/r0/excl/ctl-none`: edges from the loop's sigma column: 22.5, 162.5, 977.2, 3845.4, 4834.4, 6005.8, 7055.6, 7834.2, 8525.2, 9287.7, 9485.9; union slope 1.134e-04 [+1.114e-04, +1.156e-04] (intercept -0.0421 [-0.0449, -0.0393]); control slope 7.598e-05 [+7.438e-05, +7.766e-05]
| bin | overflow | edge_low | edge_high | n_points_union | n_points_control | n_sequences_union | n_sequences_control | populated | union_mean_excess | control_mean_excess | difference | interval |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 0 | False | 22.4580 | 162.4650 | 7373 | 6108 | 1024 | 1024 | True | 0.0037 | -0.0014 | 0.0051 | [+0.0048, +0.0054] |
| 1 | False | 162.4650 | 977.2053 | 7373 | 8228 | 1024 | 1024 | True | 0.0232 | -0.0079 | 0.0311 | [+0.0302, +0.0319] |
| 2 | False | 977.2053 | 3845.4285 | 7373 | 5172 | 1024 | 1024 | True | 0.2327 | -0.0026 | 0.2353 | [+0.2294, +0.2416] |
| 3 | False | 3845.4285 | 4834.3883 | 7372 | 9166 | 1024 | 1024 | True | 0.4096 | 0.0175 | 0.3922 | [+0.3821, +0.4024] |
| 4 | False | 4834.3883 | 6005.8494 | 7373 | 8135 | 1024 | 1024 | True | 0.5515 | 0.0615 | 0.4900 | [+0.4770, +0.5029] |
| 5 | False | 6005.8494 | 7055.5714 | 7373 | 7236 | 1024 | 1024 | True | 0.7467 | 0.1689 | 0.5778 | [+0.5636, +0.5921] |
| 6 | False | 7055.5714 | 7834.2406 | 7372 | 7185 | 1024 | 1024 | True | 0.8497 | 0.2865 | 0.5632 | [+0.5518, +0.5747] |
| 7 | False | 7834.2406 | 8525.2025 | 7373 | 7344 | 1024 | 1024 | True | 0.9250 | 0.4646 | 0.4604 | [+0.4515, +0.4696] |
| 8 | False | 8525.2025 | 9287.7453 | 7373 | 7454 | 1024 | 1024 | True | 0.9593 | 0.6286 | 0.3308 | [+0.3246, +0.3370] |
| 9 | False | 9287.7453 | 9485.9404 | 7373 | 7697 | 1024 | 1024 | True | 0.9277 | 0.7942 | 0.1336 | [+0.1311, +0.1360] |
| 10 | True | 9485.9404 | inf | 0 | 3 | 0 | 3 | False |  |  |  |  |
Local slopes (difference quotients): 1->2: 3.343e-05; 2->3: 1.064e-04; 3->4: 2.023e-04; 4->5a: 1.418e-04; 5a->5: 1.197e-04; 5->6a: 1.107e-04; 6a->6: 6.022e-05; 6->7: 1.890e-05

`union/E/D_unif/tau0/r0/excl/ctl-none`: edges from the loop's sigma column: 23.1, 207.3, 1066.2, 1595.9, 4673.9, 5776.2, 8614.7, 9146.1, 12301.0, 18509.5, 18954.9; union slope 4.536e-05 [+4.430e-05, +4.645e-05] (intercept +0.1716 [+0.1673, +0.1758]); control slope 5.260e-05 [+5.146e-05, +5.381e-05]
| bin | overflow | edge_low | edge_high | n_points_union | n_points_control | n_sequences_union | n_sequences_control | populated | union_mean_excess | control_mean_excess | difference | interval |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 0 | False | 23.1357 | 207.3223 | 5735 | 4096 | 1024 | 1024 | True | 0.0056 | -0.0018 | 0.0074 | [+0.0070, +0.0079] |
| 1 | False | 207.3223 | 1066.2255 | 5734 | 6201 | 1024 | 1024 | True | 0.0226 | -0.0053 | 0.0279 | [+0.0269, +0.0289] |
| 2 | False | 1066.2255 | 1595.8669 | 5734 | 6087 | 1024 | 1024 | True | 0.0476 | -0.0119 | 0.0595 | [+0.0581, +0.0610] |
| 3 | False | 1595.8669 | 4673.8807 | 5735 | 5918 | 1024 | 1024 | True | 0.4586 | 0.0295 | 0.4291 | [+0.4182, +0.4405] |
| 4 | False | 4673.8807 | 5776.2407 | 5734 | 6370 | 1024 | 1024 | True | 0.4975 | 0.0588 | 0.4387 | [+0.4296, +0.4481] |
| 5 | False | 5776.2407 | 8614.7361 | 5734 | 5444 | 1024 | 1024 | True | 0.6995 | 0.2361 | 0.4634 | [+0.4517, +0.4750] |
| 6 | False | 8614.7361 | 9146.0620 | 5735 | 5806 | 1024 | 1024 | True | 0.8715 | 0.6080 | 0.2635 | [+0.2557, +0.2710] |
| 7 | False | 9146.0620 | 12300.9840 | 5734 | 5953 | 1024 | 1024 | True | 0.8836 | 0.8620 | 0.0216 | [+0.0190, +0.0242] |
| 8 | False | 12300.9840 | 18509.5465 | 5734 | 5735 | 1024 | 1024 | True | 0.8213 | 0.8275 | -0.0062 | [-0.0072, -0.0052] |
| 9 | False | 18509.5465 | 18954.9375 | 5735 | 5734 | 1024 | 1024 | True | 0.7064 | 0.7102 | -0.0038 | [-0.0044, -0.0032] |
| 10 | True | 18954.9375 | inf | 0 | 0 | 0 | 0 | False |  |  |  |  |
Local slopes (difference quotients): 1->2: 4.079e-05; 2->3: 1.274e-04; 3->4: 2.552e-05; 4->5: 9.970e-05; 5->6: 9.475e-06; 6->7: -2.590e-05

## 4. Curve 2: the union under the uniform background (draw 0 shown; every draw in the CSVs)
Chain `union/E/D_unif/tau0.1/uniform/excl/k0/ctl-none`; rung 0 mean 0.2151; m = 10 rungs compared; **label: fails** (at m = 8: fails); j_det = 1, j_mat = 3, first repair rung = None; per draw: k0: det 1, mat 3

| rung | n_on | mean_sigma | overlap | mean_kl | excess | interval | half_width | two_level | draws_positive | fraction_seq_above_X | detected | material | repair | differs_at_m_8 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 201.0000 | 88.7910 | 0.0261 | 0.2248 | 0.0097 | [+0.0087, +0.0107] | 0.0010 | [+0.0087, +0.0107] | 1/1 | 0.0254 | True | False | False | False |
| 2 | 1039.0000 | 491.3366 | 0.1487 | 0.2642 | 0.0491 | [+0.0472, +0.0510] | 0.0019 | [+0.0472, +0.0510] | 1/1 | 0.4004 | True | False | False | False |
| 3 | 4494.0000 | 2183.2070 | 0.5363 | 0.5902 | 0.3751 | [+0.3650, +0.3858] | 0.0104 | [+0.3650, +0.3858] | 1/1 | 1.0000 | True | True | False | False |
| 4 | 6764.0000 | 3310.8684 | 0.5340 | 0.7993 | 0.5842 | [+0.5655, +0.6043] | 0.0194 | [+0.5655, +0.6043] | 1/1 | 1.0000 | True | True | False | False |
| 5a | 7508.0000 | 3680.3098 | 0.6985 | 0.8545 | 0.6394 | [+0.6203, +0.6601] | 0.0199 | [+0.6203, +0.6601] | 1/1 | 1.0000 | True | True | False | False |
| 5 | 8170.0000 | 4010.5034 | 0.8055 | 0.8772 | 0.6621 | [+0.6423, +0.6826] | 0.0202 | [+0.6423, +0.6826] | 1/1 | 1.0000 | True | True | False | False |
| 6a | 8660.0000 | 4255.1470 | 0.8729 | 0.8777 | 0.6626 | [+0.6426, +0.6839] | 0.0206 | [+0.6426, +0.6839] | 1/1 | 1.0000 | True | True | False | False |
| 6 | 9203.0000 | 4526.1113 | 0.9205 | 0.8795 | 0.6644 | [+0.6438, +0.6861] | 0.0212 | [+0.6438, +0.6861] | 1/1 | 1.0000 | True | True | False | False |
| 7 | 9794.0000 | 4821.4473 | 0.9724 | 0.8704 | 0.6553 | [+0.6346, +0.6775] | 0.0214 | [+0.6346, +0.6775] | 1/1 | 1.0000 | True | True | False | False |
| 8 | 9966.0000 | 4907.4331 | 0.9993 | 0.8650 | 0.6499 | [+0.6293, +0.6720] | 0.0214 | [+0.6293, +0.6720] | 1/1 | 1.0000 | True | True | False | False |

Paired union minus control on the same sequence, draw, and rung (95 percent uncorrected), with the pre-reads' overlap of the two sets: rung 1: +0.0093 [+0.0087, +0.0100] (overlap 0.026); rung 2: +0.0454 [+0.0440, +0.0467] (overlap 0.149); rung 3: +0.2960 [+0.2894, +0.3025] (overlap 0.536); rung 4: +0.3597 [+0.3489, +0.3706] (overlap 0.534); rung 5a: +0.3211 [+0.3120, +0.3303] (overlap 0.698)
Rung 4 minus rung 3 at nearly the same count (diffuse against concentrated), paired: +0.2091 [+0.1994, +0.2188].
Rung 4 (one donor sequence): excess +0.5842 [+0.5655, +0.6043], fraction of sequences with excess above X 1.000.
Per-rung excess by reader label on E (each label's own resample, the curve's m):
| label | n | rung | excess | interval | half_width | detected | material |
|---|---|---|---|---|---|---|---|
| code | 120 | 1 | 0.0008 | [+0.0002, +0.0014] | 0.0006 | True | False |
| code | 120 | 2 | 0.0553 | [+0.0482, +0.0633] | 0.0075 | True | False |
| code | 120 | 3 | 0.4327 | [+0.3910, +0.4790] | 0.0440 | True | True |
| code | 120 | 4 | 0.9060 | [+0.8352, +0.9786] | 0.0717 | True | True |
| code | 120 | 5a | 0.9358 | [+0.8621, +1.0135] | 0.0757 | True | True |
| code | 120 | 5 | 0.9281 | [+0.8544, +1.0065] | 0.0761 | True | True |
| code | 120 | 6a | 0.9285 | [+0.8544, +1.0085] | 0.0770 | True | True |
| code | 120 | 6 | 0.9230 | [+0.8493, +1.0018] | 0.0763 | True | True |
| code | 120 | 7 | 0.9068 | [+0.8328, +0.9868] | 0.0770 | True | True |
| code | 120 | 8 | 0.9000 | [+0.8261, +0.9803] | 0.0771 | True | True |
| mixed | 27 | 1 | 0.0048 | [+0.0036, +0.0061] | 0.0013 | True | False |
| mixed | 27 | 2 | 0.0590 | [+0.0502, +0.0688] | 0.0093 | True | True |
| mixed | 27 | 3 | 0.4015 | [+0.3626, +0.4390] | 0.0382 | True | True |
| mixed | 27 | 4 | 0.7672 | [+0.7009, +0.8364] | 0.0677 | True | True |
| mixed | 27 | 5a | 0.7853 | [+0.7186, +0.8538] | 0.0676 | True | True |
| mixed | 27 | 5 | 0.7781 | [+0.7105, +0.8482] | 0.0688 | True | True |
| mixed | 27 | 6a | 0.7740 | [+0.7055, +0.8448] | 0.0697 | True | True |
| mixed | 27 | 6 | 0.7641 | [+0.6933, +0.8367] | 0.0717 | True | True |
| mixed | 27 | 7 | 0.7481 | [+0.6791, +0.8192] | 0.0701 | True | True |
| mixed | 27 | 8 | 0.7427 | [+0.6742, +0.8136] | 0.0697 | True | True |
| other | 158 | 1 | 0.0019 | [+0.0011, +0.0030] | 0.0009 | True | False |
| other | 158 | 2 | 0.0314 | [+0.0273, +0.0358] | 0.0043 | True | False |
| other | 158 | 3 | 0.3141 | [+0.2844, +0.3511] | 0.0333 | True | True |
| other | 158 | 4 | 0.4934 | [+0.4311, +0.5608] | 0.0649 | True | True |
| other | 158 | 5a | 0.5759 | [+0.5118, +0.6474] | 0.0678 | True | True |
| other | 158 | 5 | 0.7344 | [+0.6669, +0.8066] | 0.0698 | True | True |
| other | 158 | 6a | 0.7567 | [+0.6878, +0.8312] | 0.0717 | True | True |
| other | 158 | 6 | 0.8038 | [+0.7367, +0.8811] | 0.0722 | True | True |
| other | 158 | 7 | 0.8167 | [+0.7519, +0.8934] | 0.0707 | True | True |
| other | 158 | 8 | 0.8121 | [+0.7476, +0.8887] | 0.0705 | True | True |
| prose | 719 | 1 | 0.0131 | [+0.0118, +0.0143] | 0.0013 | True | False |
| prose | 719 | 2 | 0.0515 | [+0.0495, +0.0536] | 0.0020 | True | False |
| prose | 719 | 3 | 0.3778 | [+0.3684, +0.3877] | 0.0097 | True | True |
| prose | 719 | 4 | 0.5435 | [+0.5289, +0.5574] | 0.0142 | True | True |
| prose | 719 | 5a | 0.5984 | [+0.5821, +0.6145] | 0.0162 | True | True |
| prose | 719 | 5 | 0.5975 | [+0.5812, +0.6136] | 0.0162 | True | True |
| prose | 719 | 6a | 0.5934 | [+0.5771, +0.6097] | 0.0163 | True | True |
| prose | 719 | 6 | 0.5869 | [+0.5713, +0.6026] | 0.0157 | True | True |
| prose | 719 | 7 | 0.5743 | [+0.5591, +0.5898] | 0.0153 | True | True |
| prose | 719 | 8 | 0.5690 | [+0.5539, +0.5845] | 0.0153 | True | True |

Paired union minus control by reader label at rungs 1 to 4 and 5a (each label's own resample, uncorrected 95 percent), the control's per-label excess beside:
| label | n | rung | union_minus_control | interval_uncorrected | half_width | control_excess | control_interval_uncorrected |
|---|---|---|---|---|---|---|---|
| code | 120 | 1 | 0.0008 | [+0.0003, +0.0012] | 0.0004 | 0.0000 | [-0.0002, +0.0002] |
| code | 120 | 2 | 0.0519 | [+0.0468, +0.0572] | 0.0052 | 0.0034 | [+0.0028, +0.0040] |
| code | 120 | 3 | 0.3426 | [+0.3175, +0.3694] | 0.0260 | 0.0902 | [+0.0839, +0.0970] |
| code | 120 | 4 | 0.6197 | [+0.5831, +0.6571] | 0.0370 | 0.2863 | [+0.2689, +0.3054] |
| code | 120 | 5a | 0.5066 | [+0.4769, +0.5362] | 0.0296 | 0.4293 | [+0.4030, +0.4578] |
| mixed | 27 | 1 | 0.0047 | [+0.0038, +0.0055] | 0.0008 | 0.0002 | [-0.0001, +0.0004] |
| mixed | 27 | 2 | 0.0557 | [+0.0495, +0.0623] | 0.0064 | 0.0033 | [+0.0025, +0.0041] |
| mixed | 27 | 3 | 0.3180 | [+0.2940, +0.3414] | 0.0237 | 0.0835 | [+0.0785, +0.0888] |
| mixed | 27 | 4 | 0.5135 | [+0.4793, +0.5477] | 0.0342 | 0.2537 | [+0.2378, +0.2704] |
| mixed | 27 | 5a | 0.4236 | [+0.3974, +0.4499] | 0.0263 | 0.3617 | [+0.3374, +0.3872] |
| other | 158 | 1 | 0.0010 | [+0.0004, +0.0018] | 0.0007 | 0.0008 | [+0.0006, +0.0011] |
| other | 158 | 2 | 0.0242 | [+0.0209, +0.0275] | 0.0033 | 0.0072 | [+0.0062, +0.0083] |
| other | 158 | 3 | 0.2214 | [+0.2008, +0.2454] | 0.0223 | 0.0927 | [+0.0862, +0.0998] |
| other | 158 | 4 | 0.2336 | [+0.2005, +0.2682] | 0.0339 | 0.2598 | [+0.2445, +0.2777] |
| other | 158 | 5a | 0.1947 | [+0.1655, +0.2249] | 0.0297 | 0.3812 | [+0.3582, +0.4080] |
| prose | 719 | 1 | 0.0128 | [+0.0119, +0.0136] | 0.0009 | 0.0003 | [+0.0002, +0.0004] |
| prose | 719 | 2 | 0.0486 | [+0.0472, +0.0500] | 0.0014 | 0.0030 | [+0.0028, +0.0032] |
| prose | 719 | 3 | 0.3037 | [+0.2979, +0.3096] | 0.0058 | 0.0741 | [+0.0729, +0.0754] |
| prose | 719 | 4 | 0.3382 | [+0.3302, +0.3460] | 0.0079 | 0.2053 | [+0.2018, +0.2088] |
| prose | 719 | 5a | 0.3141 | [+0.3065, +0.3215] | 0.0075 | 0.2843 | [+0.2791, +0.2895] |

- draw 1: label fails, j_det 1, j_mat 2, rung 8 0.8650 (rung 0 0.2151)
- draw 2: label fails, j_det 1, j_mat 3, rung 8 0.8652 (rung 0 0.2151)
- draw 3: label fails, j_det 1, j_mat 2, rung 8 0.8651 (rung 0 0.2152)
- draw 4: label fails, j_det 1, j_mat 3, rung 8 0.8649 (rung 0 0.2151)
- draw 5: label fails, j_det 1, j_mat 3, rung 8 0.8650 (rung 0 0.2151)
- draw 6: label fails, j_det 1, j_mat 3, rung 8 0.8651 (rung 0 0.2152)
- draw 7: label fails, j_det 1, j_mat 3, rung 8 0.8650 (rung 0 0.2151)

The two-by-two completed (means over E with sequence standard errors): unmasked: 0.0115 (se 0.0001); importances: 0.3417 (se 0.0032); fourth_cell: 0.3615 (se 0.0032); curve_1_rung_8: 1.2876 (se 0.0093); curve_2_rung_8: 0.8650 (se 0.0027); curve 2 rung 8 per draw [0.865, 0.865, 0.8652, 0.8651, 0.8649, 0.865, 0.8651, 0.865] against stochastic rung 0 per draw [0.2151, 0.2151, 0.2151, 0.2152, 0.2151, 0.2151, 0.2152, 0.2151]
fourth_cell, paired per sequence: minus importances-as-masks +0.0198 (se 0.0004); minus unmasked +0.3501 (se 0.0032).
Curve 2's rung 8 over curve 1's per sequence (paired; the mean over draws of curve 2 divided by curve 1): quantiles 0/10/25/50/75/90/100 = [0.46, 0.62, 0.64, 0.662, 0.689, 0.724, 0.927], mean 0.667, fraction below 0.5 0.001, above 0.9 0.001 (n 1024): whether saturation is uniform across sequences or a mixture.

## 5. The hard-zero chains: testability, positive controls, budgets (both tau_q)
| chain | part | stratum | positive_control | verdict_read | testable_rungs_at_0.1 | budget_at_0.1 | budget_at_0 |
|---|---|---|---|---|---|---|---|
| hard_zero/E/D_unif/tau0.1/ones/incl/ctl-none | donor_chain | all | pass | True | none |  |  |
| hard_zero/E/D_unif/tau0.1/ones/incl/ctl-plain | donor_chain | all | n/a | True | none |  |  |
| code_specific_hard/E/D_code/tau0.1/ones/incl/ctl-none | donor_chain | all | n/a | True | 1, 2, 3, 4, 5a, 5, 6a, 6, 7 | 7 | 7 |
| code_specific_hard/E/D_code/tau0.1/ones/incl/ctl-none | sub_rung_chain | all | n/a | True | S4, S16, S64 | S64 | S64 |
| never_named_hard/E/D_unif/tau0.1/ones/incl/ctl-none | donor_chain | all | n/a | True | 1, 2, 3, 4, 5a, 5, 6a, 6, 7, B50, B75 | 1 | 2 |
| never_named_hard/E/D_unif/tau0.1/ones/incl/ctl-none | rung 8 alone (one-cell rule) | all | n/a | True | 8 | fails | not testable with these donors |
| never_named_hard/E/D_unif/tau0.1/ones/excl/ctl-none | rung 8 alone (one-cell rule) | all | n/a | True | 8 | fails | not testable with these donors |
| never_named_hard/E/D_unif/tau0/ones/incl/ctl-none | rung 8 alone (one-cell rule) | all | n/a | True | 8 | fails | fails |
| hard_zero/E_lab/D_code/tau0.1/ones/incl/ctl-none | donor_chain | other | FAIL | False | none |  |  |
| code_specific_hard/E_lab/D_code/tau0.1/ones/incl/ctl-none | donor_chain | other | FAIL | False | 1, 2, 3, 4, 5a, 5, 6a, 6, 7 | 7 | 7 |
| code_specific_hard/E_lab/D_code/tau0.1/ones/incl/ctl-none | sub_rung_chain | other | FAIL | False | S4, S16, S64 | S64 | S64 |
| hard_zero/E_lab/D_code/tau0.1/ones/incl/ctl-plain | donor_chain | other | n/a | True | none |  |  |
| code_specific_hard/E_lab/D_code/tau0.1/ones/incl/ctl-complement | donor_chain | other | n/a | True | 1, 2, 3, 4, 5a, 5, 6a, 6, 7 | 7 | 7 |
| code_specific_hard/E_lab/D_code/tau0.1/ones/incl/ctl-complement | sub_rung_chain | other | n/a | True | S4, S16, S64 | S64 | S64 |
| code_specific_hard/E_lab/D_code/tau0.1/ones/incl/ctl-plain | donor_chain | other | n/a | True | 1, 2, 3 | 3 | 3 |
| code_specific_hard/E_lab/D_code/tau0.1/ones/incl/ctl-plain | sub_rung_chain | other | n/a | True | none |  |  |
| code_specific_hard/E_lab/D_code/tau0.5/ones/incl/ctl-none | donor_chain | other | pass | True | 1, 2, 3, 4, 5a, 5, 6a, 6, 7 | 7 | 6a |
| code_specific_hard/E_lab/D_code/tau0.5/ones/incl/ctl-none | sub_rung_chain | other | pass | True | S4, S16, S64 | S64 | S64 |
| code_specific_hard/E_lab/D_code/tau0.5/ones/incl/ctl-complement | donor_chain | other | n/a | True | 1, 2, 3, 4, 5a, 5, 6a, 6, 7 | 7 | 6a |
| code_specific_hard/E_lab/D_code/tau0.5/ones/incl/ctl-complement | sub_rung_chain | other | n/a | True | S4, S16, S64 | S64 | S64 |

### `hard_zero/E_lab/D_code/tau0.1/ones/incl/ctl-none` (curve 3)
Positive control: erase exceeds its plain control on Github: FAIL (7 rungs judged); readability floor equals the pre-reads' table: True (126 of 126 rows matched)
The erased set against its plain control per rung (mean over draws; the control's pool is the alive set): rung 1: overlap 8 of 198 erased (0.039; control 198 from a pool of 9959, of which 198 are the erased set's own); rung 2: overlap 134 of 975 erased (0.135; control 975 from a pool of 9959, of which 975 are the erased set's own); rung 3: overlap 1552 of 3626 erased (0.426; control 3626 from a pool of 9959, of which 3626 are the erased set's own); rung 4: overlap 2974 of 5156 erased (0.564; control 5156 from a pool of 9959, of which 5156 are the erased set's own); rung 5a: overlap 4040 of 6109 erased (0.659; control 6109 from a pool of 9959, of which 6109 are the erased set's own); rung 5: overlap 5679 of 7324 erased (0.773; control 7324 from a pool of 9959, of which 7324 are the erased set's own); rung 6a: overlap 6876 of 8146 erased (0.844; control 8146 from a pool of 9959, of which 8146 are the erased set's own); rung 6: overlap 7666 of 8650 erased (0.886; control 8650 from a pool of 9959, of which 8650 are the erased set's own); rung 7: overlap 8619 of 9223 erased (0.934; control 9223 from a pool of 9959, of which 9223 are the erased set's own); rung 8: overlap 9327 of 9624 erased (0.969; control 9624 from a pool of 9959, of which 9624 are the erased set's own)
tau_q = 0.1, stratum all, donor_chain (m = 9): no verdict read (positive control failed)
| rung | n_off | mean_contributing | clean_prefix_fraction | testable | label | d_hat | interval | half_width | draws_above_X | unconditional |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 197.8750 | 0.0000 | 0.0000 | False | not testable with these donors | None | None | None | None | 11.6786 |
| 2 | 975.0000 | 0.0000 | 0.0000 | False | not testable with these donors | None | None | None | None | 12.5123 |
| 3 | 3626.3750 | 0.0000 | 0.0000 | False | not testable with these donors | None | None | None | None | 11.5381 |
| 4 | 5156.3750 | 0.0000 | 0.0000 | False | not testable with these donors | None | None | None | None | 11.3994 |
| 5a | 6108.8750 | 0.0000 | 0.0000 | False | not testable with these donors | None | None | None | None | 11.4018 |
| 5 | 7324.5000 | 0.0000 | 0.0000 | False | not testable with these donors | None | None | None | None | 11.4045 |
| 6a | 8146.3750 | 0.0000 | 0.0000 | False | not testable with these donors | None | None | None | None | 11.4765 |
| 6 | 8649.7500 | 0.0000 | 0.0000 | False | not testable with these donors | None | None | None | None | 11.5729 |
| 7 | 9223.2500 | 0.0000 | 0.0000 | False | not testable with these donors | None | None | None | None | 11.6047 |

tau_q = 0.1, stratum Github, donor_chain (m = 9): no verdict read (positive control failed)
| rung | n_off | mean_contributing | clean_prefix_fraction | testable | label | d_hat | interval | half_width | draws_above_X | unconditional |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 197.8750 | 0.0000 | 0.0000 | False | not testable with these donors | None | None | None | None | 12.1597 |
| 2 | 975.0000 | 0.0000 | 0.0000 | False | not testable with these donors | None | None | None | None | 13.4082 |
| 3 | 3626.3750 | 0.0000 | 0.0000 | False | not testable with these donors | None | None | None | None | 11.9384 |
| 4 | 5156.3750 | 0.0000 | 0.0000 | False | not testable with these donors | None | None | None | None | 12.0472 |
| 5a | 6108.8750 | 0.0000 | 0.0000 | False | not testable with these donors | None | None | None | None | 12.0663 |
| 5 | 7324.5000 | 0.0000 | 0.0000 | False | not testable with these donors | None | None | None | None | 12.0058 |
| 6a | 8146.3750 | 0.0000 | 0.0000 | False | not testable with these donors | None | None | None | None | 12.0263 |
| 6 | 8649.7500 | 0.0000 | 0.0000 | False | not testable with these donors | None | None | None | None | 12.1124 |
| 7 | 9223.2500 | 0.0000 | 0.0000 | False | not testable with these donors | None | None | None | None | 12.1797 |

tau_q = 0.1, stratum other, donor_chain (m = 9): no verdict read (positive control failed)
| rung | n_off | mean_contributing | clean_prefix_fraction | testable | label | d_hat | interval | half_width | draws_above_X | unconditional |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 197.8750 | 0.0000 | 0.0000 | False | not testable with these donors | None | None | None | None | 11.1976 |
| 2 | 975.0000 | 0.0000 | 0.0000 | False | not testable with these donors | None | None | None | None | 11.6165 |
| 3 | 3626.3750 | 0.0000 | 0.0000 | False | not testable with these donors | None | None | None | None | 11.1378 |
| 4 | 5156.3750 | 0.0000 | 0.0000 | False | not testable with these donors | None | None | None | None | 10.7515 |
| 5a | 6108.8750 | 0.0000 | 0.0000 | False | not testable with these donors | None | None | None | None | 10.7373 |
| 5 | 7324.5000 | 0.0000 | 0.0000 | False | not testable with these donors | None | None | None | None | 10.8032 |
| 6a | 8146.3750 | 0.0000 | 0.0000 | False | not testable with these donors | None | None | None | None | 10.9266 |
| 6 | 8649.7500 | 0.0000 | 0.0000 | False | not testable with these donors | None | None | None | None | 11.0333 |
| 7 | 9223.2500 | 0.0000 | 0.0000 | False | not testable with these donors | None | None | None | None | 11.0298 |

tau_q = 0.1, stratum ArXiv, donor_chain (m = 9): no verdict read (positive control failed)
| rung | n_off | mean_contributing | clean_prefix_fraction | testable | label | d_hat | interval | half_width | draws_above_X | unconditional |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 197.8750 | 0.0000 | 0.0000 | False | not testable with these donors | None | None | None | None | 11.8995 |
| 2 | 975.0000 | 0.0000 | 0.0000 | False | not testable with these donors | None | None | None | None | 12.6151 |
| 3 | 3626.3750 | 0.0000 | 0.0000 | False | not testable with these donors | None | None | None | None | 11.7374 |
| 4 | 5156.3750 | 0.0000 | 0.0000 | False | not testable with these donors | None | None | None | None | 11.5087 |
| 5a | 6108.8750 | 0.0000 | 0.0000 | False | not testable with these donors | None | None | None | None | 11.4172 |
| 5 | 7324.5000 | 0.0000 | 0.0000 | False | not testable with these donors | None | None | None | None | 11.3724 |
| 6a | 8146.3750 | 0.0000 | 0.0000 | False | not testable with these donors | None | None | None | None | 11.4951 |
| 6 | 8649.7500 | 0.0000 | 0.0000 | False | not testable with these donors | None | None | None | None | 11.6281 |
| 7 | 9223.2500 | 0.0000 | 0.0000 | False | not testable with these donors | None | None | None | None | 11.6910 |

tau_q = 0.1, stratum Pile-CC, donor_chain (m = 9): no verdict read (positive control failed)
| rung | n_off | mean_contributing | clean_prefix_fraction | testable | label | d_hat | interval | half_width | draws_above_X | unconditional |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 197.8750 | 0.0000 | 0.0000 | False | not testable with these donors | None | None | None | None | 10.4798 |
| 2 | 975.0000 | 0.0000 | 0.0000 | False | not testable with these donors | None | None | None | None | 10.4132 |
| 3 | 3626.3750 | 0.0000 | 0.0000 | False | not testable with these donors | None | None | None | None | 10.5197 |
| 4 | 5156.3750 | 0.0000 | 0.0000 | False | not testable with these donors | None | None | None | None | 9.9455 |
| 5a | 6108.8750 | 0.0000 | 0.0000 | False | not testable with these donors | None | None | None | None | 9.9188 |
| 5 | 7324.5000 | 0.0000 | 0.0000 | False | not testable with these donors | None | None | None | None | 10.0852 |
| 6a | 8146.3750 | 0.0000 | 0.0000 | False | not testable with these donors | None | None | None | None | 10.2565 |
| 6 | 8649.7500 | 0.0000 | 0.0000 | False | not testable with these donors | None | None | None | None | 10.3779 |
| 7 | 9223.2500 | 0.0000 | 0.0000 | False | not testable with these donors | None | None | None | None | 10.3307 |

tau_q = 0.1, stratum StackExchange, donor_chain (m = 9): no verdict read (positive control failed)
| rung | n_off | mean_contributing | clean_prefix_fraction | testable | label | d_hat | interval | half_width | draws_above_X | unconditional |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 197.8750 | 0.0000 | 0.0000 | False | not testable with these donors | None | None | None | None | 11.8051 |
| 2 | 975.0000 | 0.0000 | 0.0000 | False | not testable with these donors | None | None | None | None | 12.6031 |
| 3 | 3626.3750 | 0.0000 | 0.0000 | False | not testable with these donors | None | None | None | None | 11.5620 |
| 4 | 5156.3750 | 0.0000 | 0.0000 | False | not testable with these donors | None | None | None | None | 11.2849 |
| 5a | 6108.8750 | 0.0000 | 0.0000 | False | not testable with these donors | None | None | None | None | 11.2437 |
| 5 | 7324.5000 | 0.0000 | 0.0000 | False | not testable with these donors | None | None | None | None | 11.2275 |
| 6a | 8146.3750 | 0.0000 | 0.0000 | False | not testable with these donors | None | None | None | None | 11.2801 |
| 6 | 8649.7500 | 0.0000 | 0.0000 | False | not testable with these donors | None | None | None | None | 11.3498 |
| 7 | 9223.2500 | 0.0000 | 0.0000 | False | not testable with these donors | None | None | None | None | 11.3590 |

tau_q = 0.1, stratum Wikipedia (en), donor_chain (m = 9): no verdict read (positive control failed)
| rung | n_off | mean_contributing | clean_prefix_fraction | testable | label | d_hat | interval | half_width | draws_above_X | unconditional |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 197.8750 | 0.0000 | 0.0000 | False | not testable with these donors | None | None | None | None | 10.6059 |
| 2 | 975.0000 | 0.0000 | 0.0000 | False | not testable with these donors | None | None | None | None | 10.8345 |
| 3 | 3626.3750 | 0.0000 | 0.0000 | False | not testable with these donors | None | None | None | None | 10.7321 |
| 4 | 5156.3750 | 0.0000 | 0.0000 | False | not testable with these donors | None | None | None | None | 10.2671 |
| 5a | 6108.8750 | 0.0000 | 0.0000 | False | not testable with these donors | None | None | None | None | 10.3697 |
| 5 | 7324.5000 | 0.0000 | 0.0000 | False | not testable with these donors | None | None | None | None | 10.5277 |
| 6a | 8146.3750 | 0.0000 | 0.0000 | False | not testable with these donors | None | None | None | None | 10.6746 |
| 6 | 8649.7500 | 0.0000 | 0.0000 | False | not testable with these donors | None | None | None | None | 10.7775 |
| 7 | 9223.2500 | 0.0000 | 0.0000 | False | not testable with these donors | None | None | None | None | 10.7385 |

tau_q = 0, stratum all, donor_chain (m = 9): no verdict read (positive control failed)
| rung | n_off | mean_contributing | clean_prefix_fraction | testable | label | d_hat | interval | half_width | draws_above_X | unconditional |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 197.8750 | 0.0000 | 0.0000 | False | not testable with these donors | None | None | None | None | 11.6786 |
| 2 | 975.0000 | 0.0000 | 0.0000 | False | not testable with these donors | None | None | None | None | 12.5123 |
| 3 | 3626.3750 | 0.0000 | 0.0000 | False | not testable with these donors | None | None | None | None | 11.5381 |
| 4 | 5156.3750 | 0.0000 | 0.0000 | False | not testable with these donors | None | None | None | None | 11.3994 |
| 5a | 6108.8750 | 0.0000 | 0.0000 | False | not testable with these donors | None | None | None | None | 11.4018 |
| 5 | 7324.5000 | 0.0000 | 0.0000 | False | not testable with these donors | None | None | None | None | 11.4045 |
| 6a | 8146.3750 | 0.0000 | 0.0000 | False | not testable with these donors | None | None | None | None | 11.4765 |
| 6 | 8649.7500 | 0.0000 | 0.0000 | False | not testable with these donors | None | None | None | None | 11.5729 |
| 7 | 9223.2500 | 0.0000 | 0.0000 | False | not testable with these donors | None | None | None | None | 11.6047 |

tau_q = 0, stratum Github, donor_chain (m = 9): no verdict read (positive control failed)
| rung | n_off | mean_contributing | clean_prefix_fraction | testable | label | d_hat | interval | half_width | draws_above_X | unconditional |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 197.8750 | 0.0000 | 0.0000 | False | not testable with these donors | None | None | None | None | 12.1597 |
| 2 | 975.0000 | 0.0000 | 0.0000 | False | not testable with these donors | None | None | None | None | 13.4082 |
| 3 | 3626.3750 | 0.0000 | 0.0000 | False | not testable with these donors | None | None | None | None | 11.9384 |
| 4 | 5156.3750 | 0.0000 | 0.0000 | False | not testable with these donors | None | None | None | None | 12.0472 |
| 5a | 6108.8750 | 0.0000 | 0.0000 | False | not testable with these donors | None | None | None | None | 12.0663 |
| 5 | 7324.5000 | 0.0000 | 0.0000 | False | not testable with these donors | None | None | None | None | 12.0058 |
| 6a | 8146.3750 | 0.0000 | 0.0000 | False | not testable with these donors | None | None | None | None | 12.0263 |
| 6 | 8649.7500 | 0.0000 | 0.0000 | False | not testable with these donors | None | None | None | None | 12.1124 |
| 7 | 9223.2500 | 0.0000 | 0.0000 | False | not testable with these donors | None | None | None | None | 12.1797 |

tau_q = 0, stratum other, donor_chain (m = 9): no verdict read (positive control failed)
| rung | n_off | mean_contributing | clean_prefix_fraction | testable | label | d_hat | interval | half_width | draws_above_X | unconditional |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 197.8750 | 0.0000 | 0.0000 | False | not testable with these donors | None | None | None | None | 11.1976 |
| 2 | 975.0000 | 0.0000 | 0.0000 | False | not testable with these donors | None | None | None | None | 11.6165 |
| 3 | 3626.3750 | 0.0000 | 0.0000 | False | not testable with these donors | None | None | None | None | 11.1378 |
| 4 | 5156.3750 | 0.0000 | 0.0000 | False | not testable with these donors | None | None | None | None | 10.7515 |
| 5a | 6108.8750 | 0.0000 | 0.0000 | False | not testable with these donors | None | None | None | None | 10.7373 |
| 5 | 7324.5000 | 0.0000 | 0.0000 | False | not testable with these donors | None | None | None | None | 10.8032 |
| 6a | 8146.3750 | 0.0000 | 0.0000 | False | not testable with these donors | None | None | None | None | 10.9266 |
| 6 | 8649.7500 | 0.0000 | 0.0000 | False | not testable with these donors | None | None | None | None | 11.0333 |
| 7 | 9223.2500 | 0.0000 | 0.0000 | False | not testable with these donors | None | None | None | None | 11.0298 |

tau_q = 0, stratum ArXiv, donor_chain (m = 9): no verdict read (positive control failed)
| rung | n_off | mean_contributing | clean_prefix_fraction | testable | label | d_hat | interval | half_width | draws_above_X | unconditional |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 197.8750 | 0.0000 | 0.0000 | False | not testable with these donors | None | None | None | None | 11.8995 |
| 2 | 975.0000 | 0.0000 | 0.0000 | False | not testable with these donors | None | None | None | None | 12.6151 |
| 3 | 3626.3750 | 0.0000 | 0.0000 | False | not testable with these donors | None | None | None | None | 11.7374 |
| 4 | 5156.3750 | 0.0000 | 0.0000 | False | not testable with these donors | None | None | None | None | 11.5087 |
| 5a | 6108.8750 | 0.0000 | 0.0000 | False | not testable with these donors | None | None | None | None | 11.4172 |
| 5 | 7324.5000 | 0.0000 | 0.0000 | False | not testable with these donors | None | None | None | None | 11.3724 |
| 6a | 8146.3750 | 0.0000 | 0.0000 | False | not testable with these donors | None | None | None | None | 11.4951 |
| 6 | 8649.7500 | 0.0000 | 0.0000 | False | not testable with these donors | None | None | None | None | 11.6281 |
| 7 | 9223.2500 | 0.0000 | 0.0000 | False | not testable with these donors | None | None | None | None | 11.6910 |

tau_q = 0, stratum Pile-CC, donor_chain (m = 9): no verdict read (positive control failed)
| rung | n_off | mean_contributing | clean_prefix_fraction | testable | label | d_hat | interval | half_width | draws_above_X | unconditional |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 197.8750 | 0.0000 | 0.0000 | False | not testable with these donors | None | None | None | None | 10.4798 |
| 2 | 975.0000 | 0.0000 | 0.0000 | False | not testable with these donors | None | None | None | None | 10.4132 |
| 3 | 3626.3750 | 0.0000 | 0.0000 | False | not testable with these donors | None | None | None | None | 10.5197 |
| 4 | 5156.3750 | 0.0000 | 0.0000 | False | not testable with these donors | None | None | None | None | 9.9455 |
| 5a | 6108.8750 | 0.0000 | 0.0000 | False | not testable with these donors | None | None | None | None | 9.9188 |
| 5 | 7324.5000 | 0.0000 | 0.0000 | False | not testable with these donors | None | None | None | None | 10.0852 |
| 6a | 8146.3750 | 0.0000 | 0.0000 | False | not testable with these donors | None | None | None | None | 10.2565 |
| 6 | 8649.7500 | 0.0000 | 0.0000 | False | not testable with these donors | None | None | None | None | 10.3779 |
| 7 | 9223.2500 | 0.0000 | 0.0000 | False | not testable with these donors | None | None | None | None | 10.3307 |

tau_q = 0, stratum StackExchange, donor_chain (m = 9): no verdict read (positive control failed)
| rung | n_off | mean_contributing | clean_prefix_fraction | testable | label | d_hat | interval | half_width | draws_above_X | unconditional |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 197.8750 | 0.0000 | 0.0000 | False | not testable with these donors | None | None | None | None | 11.8051 |
| 2 | 975.0000 | 0.0000 | 0.0000 | False | not testable with these donors | None | None | None | None | 12.6031 |
| 3 | 3626.3750 | 0.0000 | 0.0000 | False | not testable with these donors | None | None | None | None | 11.5620 |
| 4 | 5156.3750 | 0.0000 | 0.0000 | False | not testable with these donors | None | None | None | None | 11.2849 |
| 5a | 6108.8750 | 0.0000 | 0.0000 | False | not testable with these donors | None | None | None | None | 11.2437 |
| 5 | 7324.5000 | 0.0000 | 0.0000 | False | not testable with these donors | None | None | None | None | 11.2275 |
| 6a | 8146.3750 | 0.0000 | 0.0000 | False | not testable with these donors | None | None | None | None | 11.2801 |
| 6 | 8649.7500 | 0.0000 | 0.0000 | False | not testable with these donors | None | None | None | None | 11.3498 |
| 7 | 9223.2500 | 0.0000 | 0.0000 | False | not testable with these donors | None | None | None | None | 11.3590 |

tau_q = 0, stratum Wikipedia (en), donor_chain (m = 9): no verdict read (positive control failed)
| rung | n_off | mean_contributing | clean_prefix_fraction | testable | label | d_hat | interval | half_width | draws_above_X | unconditional |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 197.8750 | 0.0000 | 0.0000 | False | not testable with these donors | None | None | None | None | 10.6059 |
| 2 | 975.0000 | 0.0000 | 0.0000 | False | not testable with these donors | None | None | None | None | 10.8345 |
| 3 | 3626.3750 | 0.0000 | 0.0000 | False | not testable with these donors | None | None | None | None | 10.7321 |
| 4 | 5156.3750 | 0.0000 | 0.0000 | False | not testable with these donors | None | None | None | None | 10.2671 |
| 5a | 6108.8750 | 0.0000 | 0.0000 | False | not testable with these donors | None | None | None | None | 10.3697 |
| 5 | 7324.5000 | 0.0000 | 0.0000 | False | not testable with these donors | None | None | None | None | 10.5277 |
| 6a | 8146.3750 | 0.0000 | 0.0000 | False | not testable with these donors | None | None | None | None | 10.6746 |
| 6 | 8649.7500 | 0.0000 | 0.0000 | False | not testable with these donors | None | None | None | None | 10.7775 |
| 7 | 9223.2500 | 0.0000 | 0.0000 | False | not testable with these donors | None | None | None | None | 10.7385 |

### `code_specific_hard/E_lab/D_code/tau0.1/ones/incl/ctl-none` (curve 4)
Positive control: erase exceeds its complement control on Github: FAIL (10 rungs judged); readability floor equals the pre-reads' table: True (168 of 168 rows matched)
The erased set against its complement control per rung (mean over draws; the control's pool is alive minus prose-named at this tau): rung 1: overlap 0 of 0 erased (0.000; control 0 from a pool of 450, of which 0 are the erased set's own); rung 2: overlap 0 of 1 erased (0.167; control 1 from a pool of 450, of which 1 are the erased set's own); rung 3: overlap 1 of 5 erased (0.295; control 5 from a pool of 450, of which 5 are the erased set's own); rung 4: overlap 3 of 9 erased (0.325; control 9 from a pool of 450, of which 9 are the erased set's own); rung 5a: overlap 4 of 14 erased (0.309; control 14 from a pool of 450, of which 14 are the erased set's own); rung 5: overlap 8 of 30 erased (0.274; control 30 from a pool of 450, of which 30 are the erased set's own); rung 6a: overlap 13 of 46 erased (0.271; control 46 from a pool of 450, of which 46 are the erased set's own); rung 6: overlap 19 of 64 erased (0.292; control 64 from a pool of 450, of which 64 are the erased set's own); rung 7: overlap 44 of 109 erased (0.365; control 109 from a pool of 450, of which 109 are the erased set's own); rung 8: overlap 199 of 270 erased (0.737; control 270 from a pool of 450, of which 270 are the erased set's own); rung S4: overlap 0 of 4 erased (0.000; control 4 from a pool of 450, of which 4 are the erased set's own); rung S16: overlap 3 of 16 erased (0.188; control 16 from a pool of 450, of which 16 are the erased set's own); rung S64: overlap 20 of 64 erased (0.312; control 64 from a pool of 450, of which 64 are the erased set's own)
tau_q = 0.1, stratum all, donor_chain (m = 9): no verdict read (positive control failed)
| rung | n_off | mean_contributing | clean_prefix_fraction | testable | label | d_hat | interval | half_width | draws_above_X | unconditional |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 0.1250 | 510.0000 | 0.9659 | True | holds | 0.0000 | [+0.0000, +0.0000] | 0.0000 | 0/8 | 0.0001 |
| 2 | 1.2500 | 497.1250 | 0.8371 | True | holds | 0.0001 | [+0.0001, +0.0002] | 0.0000 | 0/8 | 0.0009 |
| 3 | 5.1250 | 457.5000 | 0.5489 | True | holds | 0.0006 | [+0.0005, +0.0007] | 0.0001 | 0/8 | 0.0040 |
| 4 | 8.6250 | 433.6250 | 0.5055 | True | holds | 0.0010 | [+0.0009, +0.0012] | 0.0001 | 0/8 | 0.0055 |
| 5a | 14.3750 | 412.6250 | 0.4693 | True | holds | 0.0015 | [+0.0013, +0.0018] | 0.0002 | 0/8 | 0.0076 |
| 5 | 30.2500 | 389.0000 | 0.4279 | True | holds | 0.0028 | [+0.0025, +0.0031] | 0.0003 | 0/8 | 0.0100 |
| 6a | 45.7500 | 369.1250 | 0.3781 | True | holds | 0.0042 | [+0.0037, +0.0047] | 0.0005 | 0/8 | 0.0125 |
| 6 | 63.6250 | 358.7500 | 0.3635 | True | holds | 0.0057 | [+0.0051, +0.0065] | 0.0007 | 0/8 | 0.0145 |
| 7 | 108.6250 | 347.5000 | 0.3473 | True | holds | 0.0095 | [+0.0084, +0.0109] | 0.0013 | 0/8 | 0.0187 |

tau_q = 0.1, stratum all, sub_rung_chain (m = 3): no verdict read (positive control failed)
| rung | n_off | mean_contributing | clean_prefix_fraction | testable | label | d_hat | interval | half_width | draws_above_X | unconditional |
|---|---|---|---|---|---|---|---|---|---|---|
| S4 | 4.0000 | 454.0000 | 0.5198 | True | holds | 0.0005 | [+0.0004, +0.0007] | 0.0001 | 0/1 | 0.0015 |
| S16 | 16.0000 | 394.0000 | 0.4391 | True | holds | 0.0015 | [+0.0014, +0.0018] | 0.0002 | 0/1 | 0.0096 |
| S64 | 64.0000 | 357.0000 | 0.3641 | True | holds | 0.0061 | [+0.0055, +0.0069] | 0.0007 | 0/1 | 0.0151 |

tau_q = 0.1, stratum Github, donor_chain (m = 9): no verdict read (positive control failed)
| rung | n_off | mean_contributing | clean_prefix_fraction | testable | label | d_hat | interval | half_width | draws_above_X | unconditional |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 0.1250 | 254.5000 | 0.9411 | True | holds | 0.0000 | [+0.0000, +0.0000] | 0.0000 | 0/8 | 0.0001 |
| 2 | 1.2500 | 243.0000 | 0.7312 | True | holds | 0.0002 | [+0.0002, +0.0003] | 0.0000 | 0/8 | 0.0014 |
| 3 | 5.1250 | 210.2500 | 0.2623 | True | holds | 0.0010 | [+0.0008, +0.0012] | 0.0002 | 0/8 | 0.0066 |
| 4 | 8.6250 | 190.6250 | 0.2019 | True | holds | 0.0016 | [+0.0013, +0.0019] | 0.0003 | 0/8 | 0.0091 |
| 5a | 14.3750 | 173.5000 | 0.1671 | True | holds | 0.0024 | [+0.0020, +0.0029] | 0.0004 | 0/8 | 0.0125 |
| 5 | 30.2500 | 158.0000 | 0.1493 | True | holds | 0.0043 | [+0.0036, +0.0050] | 0.0007 | 0/8 | 0.0159 |
| 6a | 45.7500 | 147.6250 | 0.1401 | True | holds | 0.0062 | [+0.0053, +0.0073] | 0.0010 | 0/8 | 0.0193 |
| 6 | 63.6250 | 141.7500 | 0.1344 | True | holds | 0.0083 | [+0.0071, +0.0099] | 0.0014 | 0/8 | 0.0219 |
| 7 | 108.6250 | 135.3750 | 0.1298 | True | holds | 0.0137 | [+0.0114, +0.0170] | 0.0028 | 0/8 | 0.0271 |

tau_q = 0.1, stratum Github, sub_rung_chain (m = 3): no verdict read (positive control failed)
| rung | n_off | mean_contributing | clean_prefix_fraction | testable | label | d_hat | interval | half_width | draws_above_X | unconditional |
|---|---|---|---|---|---|---|---|---|---|---|
| S4 | 4.0000 | 205.0000 | 0.1989 | True | holds | 0.0009 | [+0.0007, +0.0012] | 0.0003 | 0/1 | 0.0026 |
| S16 | 16.0000 | 156.0000 | 0.1462 | True | holds | 0.0026 | [+0.0022, +0.0031] | 0.0004 | 0/1 | 0.0159 |
| S64 | 64.0000 | 138.0000 | 0.1327 | True | holds | 0.0092 | [+0.0079, +0.0108] | 0.0015 | 0/1 | 0.0230 |

tau_q = 0.1, stratum other, donor_chain (m = 9): no verdict read (positive control failed)
| rung | n_off | mean_contributing | clean_prefix_fraction | testable | label | d_hat | interval | half_width | draws_above_X | unconditional |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 0.1250 | 255.5000 | 0.9907 | True | holds | 0.0000 | [+0.0000, +0.0000] | 0.0000 | 0/8 | 0.0000 |
| 2 | 1.2500 | 254.1250 | 0.9431 | True | holds | 0.0001 | [+0.0001, +0.0001] | 0.0000 | 0/8 | 0.0003 |
| 3 | 5.1250 | 247.2500 | 0.8356 | True | holds | 0.0003 | [+0.0003, +0.0004] | 0.0001 | 0/8 | 0.0014 |
| 4 | 8.6250 | 243.0000 | 0.8091 | True | holds | 0.0006 | [+0.0005, +0.0007] | 0.0001 | 0/8 | 0.0020 |
| 5a | 14.3750 | 239.1250 | 0.7714 | True | holds | 0.0009 | [+0.0008, +0.0010] | 0.0001 | 0/8 | 0.0027 |
| 5 | 30.2500 | 231.0000 | 0.7064 | True | holds | 0.0018 | [+0.0016, +0.0020] | 0.0002 | 0/8 | 0.0041 |
| 6a | 45.7500 | 221.5000 | 0.6161 | True | holds | 0.0028 | [+0.0026, +0.0032] | 0.0003 | 0/8 | 0.0057 |
| 6 | 63.6250 | 217.0000 | 0.5926 | True | holds | 0.0040 | [+0.0036, +0.0045] | 0.0004 | 0/8 | 0.0071 |
| 7 | 108.6250 | 212.1250 | 0.5648 | True | holds | 0.0068 | [+0.0062, +0.0075] | 0.0007 | 0/8 | 0.0103 |

tau_q = 0.1, stratum other, sub_rung_chain (m = 3): no verdict read (positive control failed)
| rung | n_off | mean_contributing | clean_prefix_fraction | testable | label | d_hat | interval | half_width | draws_above_X | unconditional |
|---|---|---|---|---|---|---|---|---|---|---|
| S4 | 4.0000 | 249.0000 | 0.8407 | True | holds | 0.0002 | [+0.0002, +0.0003] | 0.0001 | 0/1 | 0.0004 |
| S16 | 16.0000 | 238.0000 | 0.7320 | True | holds | 0.0009 | [+0.0008, +0.0010] | 0.0001 | 0/1 | 0.0034 |
| S64 | 64.0000 | 219.0000 | 0.5955 | True | holds | 0.0042 | [+0.0038, +0.0048] | 0.0005 | 0/1 | 0.0072 |

tau_q = 0.1, stratum ArXiv, donor_chain (m = 9): no verdict read (positive control failed)
| rung | n_off | mean_contributing | clean_prefix_fraction | testable | label | d_hat | interval | half_width | draws_above_X | unconditional |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 0.1250 | 63.6250 | 0.9942 | False | not testable with these donors | None | None | None | None | 0.0000 |
| 2 | 1.2500 | 63.6250 | 0.9878 | False | not testable with these donors | None | None | None | None | 0.0000 |
| 3 | 5.1250 | 62.6250 | 0.9558 | False | not testable with these donors | None | None | None | None | 0.0002 |
| 4 | 8.6250 | 61.1250 | 0.8657 | False | not testable with these donors | None | None | None | None | 0.0005 |
| 5a | 14.3750 | 59.5000 | 0.7970 | False | not testable with these donors | None | None | None | None | 0.0007 |
| 5 | 30.2500 | 55.2500 | 0.6368 | False | not testable with these donors | None | None | None | None | 0.0019 |
| 6a | 45.7500 | 47.5000 | 0.3313 | False | not testable with these donors | None | None | None | None | 0.0036 |
| 6 | 63.6250 | 44.5000 | 0.2713 | False | not testable with these donors | None | None | None | None | 0.0051 |
| 7 | 108.6250 | 42.7500 | 0.2286 | False | not testable with these donors | None | None | None | None | 0.0084 |

tau_q = 0.1, stratum ArXiv, sub_rung_chain (m = 3): no verdict read (positive control failed)
| rung | n_off | mean_contributing | clean_prefix_fraction | testable | label | d_hat | interval | half_width | draws_above_X | unconditional |
|---|---|---|---|---|---|---|---|---|---|---|
| S4 | 4.0000 | 64.0000 | 0.9868 | True | holds | 0.0002 | [+0.0001, +0.0002] | 0.0000 | 0/1 | 0.0002 |
| S16 | 16.0000 | 61.0000 | 0.6790 | False | not testable with these donors |  |  |  |  | 0.0007 |
| S64 | 64.0000 | 45.0000 | 0.2746 | False | not testable with these donors |  |  |  |  | 0.0051 |

tau_q = 0.1, stratum Pile-CC, donor_chain (m = 9): no verdict read (positive control failed)
| rung | n_off | mean_contributing | clean_prefix_fraction | testable | label | d_hat | interval | half_width | draws_above_X | unconditional |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 0.1250 | 64.0000 | 1.0000 | True | holds | 0.0000 | [+0.0000, +0.0000] | 0.0000 | 0/8 | 0.0000 |
| 2 | 1.2500 | 64.0000 | 1.0000 | True | holds | 0.0000 | [+0.0000, +0.0000] | 0.0000 | 0/8 | 0.0000 |
| 3 | 5.1250 | 64.0000 | 0.9985 | True | holds | 0.0002 | [+0.0002, +0.0002] | 0.0000 | 0/8 | 0.0002 |
| 4 | 8.6250 | 63.8750 | 0.9907 | False | not testable with these donors |  |  |  |  | 0.0004 |
| 5a | 14.3750 | 63.8750 | 0.9846 | False | not testable with these donors |  |  |  |  | 0.0007 |
| 5 | 30.2500 | 63.5000 | 0.9750 | False | not testable with these donors |  |  |  |  | 0.0015 |
| 6a | 45.7500 | 63.3750 | 0.9679 | False | not testable with these donors |  |  |  |  | 0.0024 |
| 6 | 63.6250 | 63.1250 | 0.9564 | False | not testable with these donors |  |  |  |  | 0.0035 |
| 7 | 108.6250 | 62.3750 | 0.9336 | False | not testable with these donors |  |  |  |  | 0.0061 |

tau_q = 0.1, stratum Pile-CC, sub_rung_chain (m = 3): no verdict read (positive control failed)
| rung | n_off | mean_contributing | clean_prefix_fraction | testable | label | d_hat | interval | half_width | draws_above_X | unconditional |
|---|---|---|---|---|---|---|---|---|---|---|
| S4 | 4.0000 | 64.0000 | 1.0000 | True | holds | 0.0001 | [+0.0001, +0.0001] | 0.0000 | 0/1 | 0.0001 |
| S16 | 16.0000 | 64.0000 | 0.9805 | True | holds | 0.0007 | [+0.0006, +0.0007] | 0.0000 | 0/1 | 0.0007 |
| S64 | 64.0000 | 63.0000 | 0.9460 | False | not testable with these donors |  |  |  |  | 0.0036 |

tau_q = 0.1, stratum StackExchange, donor_chain (m = 9): no verdict read (positive control failed)
| rung | n_off | mean_contributing | clean_prefix_fraction | testable | label | d_hat | interval | half_width | draws_above_X | unconditional |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 0.1250 | 63.8750 | 0.9692 | False | not testable with these donors | None | None | None | None | 0.0000 |
| 2 | 1.2500 | 62.5000 | 0.7859 | False | not testable with these donors | None | None | None | None | 0.0011 |
| 3 | 5.1250 | 56.6250 | 0.3932 | False | not testable with these donors | None | None | None | None | 0.0050 |
| 4 | 8.6250 | 54.2500 | 0.3934 | False | not testable with these donors | None | None | None | None | 0.0064 |
| 5a | 14.3750 | 52.0000 | 0.3220 | False | not testable with these donors | None | None | None | None | 0.0087 |
| 5 | 30.2500 | 48.6250 | 0.2425 | False | not testable with these donors | None | None | None | None | 0.0112 |
| 6a | 45.7500 | 47.0000 | 0.2022 | False | not testable with these donors | None | None | None | None | 0.0138 |
| 6 | 63.6250 | 45.7500 | 0.1825 | False | not testable with these donors | None | None | None | None | 0.0157 |
| 7 | 108.6250 | 44.1250 | 0.1557 | False | not testable with these donors | None | None | None | None | 0.0196 |

tau_q = 0.1, stratum StackExchange, sub_rung_chain (m = 3): no verdict read (positive control failed)
| rung | n_off | mean_contributing | clean_prefix_fraction | testable | label | d_hat | interval | half_width | draws_above_X | unconditional |
|---|---|---|---|---|---|---|---|---|---|---|
| S4 | 4.0000 | 57.0000 | 0.3794 | False | not testable with these donors | None | None | None | None | 0.0013 |
| S16 | 16.0000 | 49.0000 | 0.3016 | False | not testable with these donors | None | None | None | None | 0.0113 |
| S64 | 64.0000 | 47.0000 | 0.1946 | False | not testable with these donors | None | None | None | None | 0.0160 |

tau_q = 0.1, stratum Wikipedia (en), donor_chain (m = 9): no verdict read (positive control failed)
| rung | n_off | mean_contributing | clean_prefix_fraction | testable | label | d_hat | interval | half_width | draws_above_X | unconditional |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 0.1250 | 64.0000 | 0.9994 | True | holds | 0.0000 | [+0.0000, +0.0000] | 0.0000 | 0/8 | 0.0000 |
| 2 | 1.2500 | 64.0000 | 0.9986 | True | holds | 0.0001 | [+0.0001, +0.0001] | 0.0000 | 0/8 | 0.0001 |
| 3 | 5.1250 | 64.0000 | 0.9948 | True | holds | 0.0003 | [+0.0003, +0.0003] | 0.0000 | 0/8 | 0.0003 |
| 4 | 8.6250 | 63.7500 | 0.9866 | False | not testable with these donors |  |  |  |  | 0.0005 |
| 5a | 14.3750 | 63.7500 | 0.9822 | False | not testable with these donors |  |  |  |  | 0.0009 |
| 5 | 30.2500 | 63.6250 | 0.9715 | False | not testable with these donors |  |  |  |  | 0.0018 |
| 6a | 45.7500 | 63.6250 | 0.9630 | False | not testable with these donors |  |  |  |  | 0.0030 |
| 6 | 63.6250 | 63.6250 | 0.9604 | False | not testable with these donors |  |  |  |  | 0.0042 |
| 7 | 108.6250 | 62.8750 | 0.9413 | False | not testable with these donors |  |  |  |  | 0.0073 |

tau_q = 0.1, stratum Wikipedia (en), sub_rung_chain (m = 3): no verdict read (positive control failed)
| rung | n_off | mean_contributing | clean_prefix_fraction | testable | label | d_hat | interval | half_width | draws_above_X | unconditional |
|---|---|---|---|---|---|---|---|---|---|---|
| S4 | 4.0000 | 64.0000 | 0.9967 | True | holds | 0.0002 | [+0.0002, +0.0002] | 0.0000 | 0/1 | 0.0002 |
| S16 | 16.0000 | 64.0000 | 0.9667 | True | holds | 0.0008 | [+0.0008, +0.0009] | 0.0001 | 0/1 | 0.0009 |
| S64 | 64.0000 | 64.0000 | 0.9667 | True | holds | 0.0042 | [+0.0040, +0.0044] | 0.0002 | 0/1 | 0.0043 |

tau_q = 0, stratum all, donor_chain (m = 9): no verdict read (positive control failed)
| rung | n_off | mean_contributing | clean_prefix_fraction | testable | label | d_hat | interval | half_width | draws_above_X | unconditional |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 0.1250 | 509.5000 | 0.9611 | True | holds | 0.0000 | [+0.0000, +0.0000] | 0.0000 | 0/8 | 0.0001 |
| 2 | 1.2500 | 494.5000 | 0.8161 | True | holds | 0.0001 | [+0.0001, +0.0001] | 0.0000 | 0/8 | 0.0009 |
| 3 | 5.1250 | 447.6250 | 0.4885 | True | holds | 0.0006 | [+0.0005, +0.0007] | 0.0001 | 0/8 | 0.0040 |
| 4 | 8.6250 | 415.1250 | 0.4151 | True | holds | 0.0010 | [+0.0008, +0.0011] | 0.0001 | 0/8 | 0.0055 |
| 5a | 14.3750 | 384.6250 | 0.3450 | True | holds | 0.0014 | [+0.0013, +0.0016] | 0.0002 | 0/8 | 0.0076 |
| 5 | 30.2500 | 350.2500 | 0.2605 | True | holds | 0.0027 | [+0.0024, +0.0030] | 0.0003 | 0/8 | 0.0100 |
| 6a | 45.7500 | 327.0000 | 0.1972 | True | holds | 0.0040 | [+0.0036, +0.0044] | 0.0004 | 0/8 | 0.0125 |
| 6 | 63.6250 | 310.0000 | 0.1622 | True | holds | 0.0054 | [+0.0049, +0.0060] | 0.0006 | 0/8 | 0.0145 |
| 7 | 108.6250 | 283.0000 | 0.1129 | True | holds | 0.0089 | [+0.0080, +0.0100] | 0.0010 | 0/8 | 0.0187 |

tau_q = 0, stratum all, sub_rung_chain (m = 3): no verdict read (positive control failed)
| rung | n_off | mean_contributing | clean_prefix_fraction | testable | label | d_hat | interval | half_width | draws_above_X | unconditional |
|---|---|---|---|---|---|---|---|---|---|---|
| S4 | 4.0000 | 445.0000 | 0.4706 | True | holds | 0.0005 | [+0.0004, +0.0006] | 0.0001 | 0/1 | 0.0015 |
| S16 | 16.0000 | 366.0000 | 0.3097 | True | holds | 0.0014 | [+0.0012, +0.0016] | 0.0002 | 0/1 | 0.0096 |
| S64 | 64.0000 | 311.0000 | 0.1617 | True | holds | 0.0059 | [+0.0053, +0.0066] | 0.0006 | 0/1 | 0.0151 |

tau_q = 0, stratum Github, donor_chain (m = 9): no verdict read (positive control failed)
| rung | n_off | mean_contributing | clean_prefix_fraction | testable | label | d_hat | interval | half_width | draws_above_X | unconditional |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 0.1250 | 254.2500 | 0.9361 | True | holds | 0.0000 | [+0.0000, +0.0000] | 0.0000 | 0/8 | 0.0001 |
| 2 | 1.2500 | 241.1250 | 0.7142 | True | holds | 0.0002 | [+0.0002, +0.0002] | 0.0000 | 0/8 | 0.0014 |
| 3 | 5.1250 | 203.2500 | 0.2322 | True | holds | 0.0009 | [+0.0008, +0.0011] | 0.0002 | 0/8 | 0.0066 |
| 4 | 8.6250 | 177.0000 | 0.1641 | True | holds | 0.0015 | [+0.0013, +0.0018] | 0.0003 | 0/8 | 0.0091 |
| 5a | 14.3750 | 154.0000 | 0.1253 | True | holds | 0.0023 | [+0.0019, +0.0028] | 0.0004 | 0/8 | 0.0125 |
| 5 | 30.2500 | 131.2500 | 0.0935 | True | holds | 0.0041 | [+0.0034, +0.0050] | 0.0008 | 0/8 | 0.0159 |
| 6a | 45.7500 | 119.0000 | 0.0712 | True | holds | 0.0059 | [+0.0050, +0.0070] | 0.0010 | 0/8 | 0.0193 |
| 6 | 63.6250 | 109.5000 | 0.0577 | True | holds | 0.0079 | [+0.0066, +0.0094] | 0.0014 | 0/8 | 0.0219 |
| 7 | 108.6250 | 94.8750 | 0.0393 | False | not testable with these donors |  |  |  |  | 0.0271 |

tau_q = 0, stratum Github, sub_rung_chain (m = 3): no verdict read (positive control failed)
| rung | n_off | mean_contributing | clean_prefix_fraction | testable | label | d_hat | interval | half_width | draws_above_X | unconditional |
|---|---|---|---|---|---|---|---|---|---|---|
| S4 | 4.0000 | 199.0000 | 0.1809 | True | holds | 0.0008 | [+0.0006, +0.0010] | 0.0002 | 0/1 | 0.0026 |
| S16 | 16.0000 | 136.0000 | 0.1067 | True | holds | 0.0024 | [+0.0020, +0.0028] | 0.0004 | 0/1 | 0.0159 |
| S64 | 64.0000 | 109.0000 | 0.0569 | True | holds | 0.0088 | [+0.0075, +0.0105] | 0.0015 | 0/1 | 0.0230 |

tau_q = 0, stratum other, donor_chain (m = 9): no verdict read (positive control failed)
| rung | n_off | mean_contributing | clean_prefix_fraction | testable | label | d_hat | interval | half_width | draws_above_X | unconditional |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 0.1250 | 255.2500 | 0.9862 | True | holds | 0.0000 | [+0.0000, +0.0000] | 0.0000 | 0/8 | 0.0000 |
| 2 | 1.2500 | 253.3750 | 0.9180 | True | holds | 0.0001 | [+0.0001, +0.0001] | 0.0000 | 0/8 | 0.0003 |
| 3 | 5.1250 | 244.3750 | 0.7449 | True | holds | 0.0003 | [+0.0003, +0.0004] | 0.0000 | 0/8 | 0.0014 |
| 4 | 8.6250 | 238.1250 | 0.6662 | True | holds | 0.0006 | [+0.0005, +0.0006] | 0.0001 | 0/8 | 0.0020 |
| 5a | 14.3750 | 230.6250 | 0.5648 | True | holds | 0.0009 | [+0.0008, +0.0009] | 0.0001 | 0/8 | 0.0027 |
| 5 | 30.2500 | 219.0000 | 0.4274 | True | holds | 0.0018 | [+0.0017, +0.0019] | 0.0001 | 0/8 | 0.0041 |
| 6a | 45.7500 | 208.0000 | 0.3232 | True | holds | 0.0028 | [+0.0026, +0.0031] | 0.0002 | 0/8 | 0.0057 |
| 6 | 63.6250 | 200.5000 | 0.2667 | True | holds | 0.0040 | [+0.0037, +0.0044] | 0.0003 | 0/8 | 0.0071 |
| 7 | 108.6250 | 188.1250 | 0.1864 | True | holds | 0.0069 | [+0.0063, +0.0076] | 0.0006 | 0/8 | 0.0103 |

tau_q = 0, stratum other, sub_rung_chain (m = 3): no verdict read (positive control failed)
| rung | n_off | mean_contributing | clean_prefix_fraction | testable | label | d_hat | interval | half_width | draws_above_X | unconditional |
|---|---|---|---|---|---|---|---|---|---|---|
| S4 | 4.0000 | 246.0000 | 0.7603 | True | holds | 0.0002 | [+0.0002, +0.0003] | 0.0001 | 0/1 | 0.0004 |
| S16 | 16.0000 | 230.0000 | 0.5127 | True | holds | 0.0008 | [+0.0008, +0.0009] | 0.0001 | 0/1 | 0.0034 |
| S64 | 64.0000 | 202.0000 | 0.2665 | True | holds | 0.0043 | [+0.0040, +0.0047] | 0.0004 | 0/1 | 0.0072 |

tau_q = 0, stratum ArXiv, donor_chain (m = 9): no verdict read (positive control failed)
| rung | n_off | mean_contributing | clean_prefix_fraction | testable | label | d_hat | interval | half_width | draws_above_X | unconditional |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 0.1250 | 63.3750 | 0.9876 | False | not testable with these donors | None | None | None | None | 0.0000 |
| 2 | 1.2500 | 63.2500 | 0.9635 | False | not testable with these donors | None | None | None | None | 0.0000 |
| 3 | 5.1250 | 61.1250 | 0.8476 | False | not testable with these donors | None | None | None | None | 0.0002 |
| 4 | 8.6250 | 59.2500 | 0.7229 | False | not testable with these donors | None | None | None | None | 0.0005 |
| 5a | 14.3750 | 55.7500 | 0.5848 | False | not testable with these donors | None | None | None | None | 0.0007 |
| 5 | 30.2500 | 50.2500 | 0.4025 | False | not testable with these donors | None | None | None | None | 0.0019 |
| 6a | 45.7500 | 42.2500 | 0.2196 | False | not testable with these donors | None | None | None | None | 0.0036 |
| 6 | 63.6250 | 38.7500 | 0.1601 | False | not testable with these donors | None | None | None | None | 0.0051 |
| 7 | 108.6250 | 35.0000 | 0.0919 | False | not testable with these donors | None | None | None | None | 0.0084 |

tau_q = 0, stratum ArXiv, sub_rung_chain (m = 3): no verdict read (positive control failed)
| rung | n_off | mean_contributing | clean_prefix_fraction | testable | label | d_hat | interval | half_width | draws_above_X | unconditional |
|---|---|---|---|---|---|---|---|---|---|---|
| S4 | 4.0000 | 63.0000 | 0.9364 | False | not testable with these donors | None | None | None | None | 0.0002 |
| S16 | 16.0000 | 57.0000 | 0.4588 | False | not testable with these donors | None | None | None | None | 0.0007 |
| S64 | 64.0000 | 39.0000 | 0.1481 | False | not testable with these donors | None | None | None | None | 0.0051 |

tau_q = 0, stratum Pile-CC, donor_chain (m = 9): no verdict read (positive control failed)
| rung | n_off | mean_contributing | clean_prefix_fraction | testable | label | d_hat | interval | half_width | draws_above_X | unconditional |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 0.1250 | 64.0000 | 0.9992 | True | holds | 0.0000 | [+0.0000, +0.0000] | 0.0000 | 0/8 | 0.0000 |
| 2 | 1.2500 | 63.7500 | 0.9648 | False | not testable with these donors |  |  |  |  | 0.0000 |
| 3 | 5.1250 | 63.5000 | 0.8784 | False | not testable with these donors |  |  |  |  | 0.0002 |
| 4 | 8.6250 | 62.8750 | 0.8002 | False | not testable with these donors |  |  |  |  | 0.0004 |
| 5a | 14.3750 | 62.1250 | 0.6973 | False | not testable with these donors |  |  |  |  | 0.0007 |
| 5 | 30.2500 | 60.8750 | 0.5521 | False | not testable with these donors |  |  |  |  | 0.0015 |
| 6a | 45.7500 | 60.0000 | 0.4534 | False | not testable with these donors |  |  |  |  | 0.0024 |
| 6 | 63.6250 | 59.0000 | 0.3840 | False | not testable with these donors |  |  |  |  | 0.0035 |
| 7 | 108.6250 | 56.6250 | 0.2944 | False | not testable with these donors |  |  |  |  | 0.0061 |

tau_q = 0, stratum Pile-CC, sub_rung_chain (m = 3): no verdict read (positive control failed)
| rung | n_off | mean_contributing | clean_prefix_fraction | testable | label | d_hat | interval | half_width | draws_above_X | unconditional |
|---|---|---|---|---|---|---|---|---|---|---|
| S4 | 4.0000 | 63.0000 | 0.8711 | False | not testable with these donors | None | None | None | None | 0.0001 |
| S16 | 16.0000 | 63.0000 | 0.6498 | False | not testable with these donors | None | None | None | None | 0.0007 |
| S64 | 64.0000 | 59.0000 | 0.3645 | False | not testable with these donors | None | None | None | None | 0.0036 |

tau_q = 0, stratum StackExchange, donor_chain (m = 9): no verdict read (positive control failed)
| rung | n_off | mean_contributing | clean_prefix_fraction | testable | label | d_hat | interval | half_width | draws_above_X | unconditional |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 0.1250 | 63.8750 | 0.9605 | False | not testable with these donors | None | None | None | None | 0.0000 |
| 2 | 1.2500 | 62.3750 | 0.7610 | False | not testable with these donors | None | None | None | None | 0.0011 |
| 3 | 5.1250 | 55.7500 | 0.3321 | False | not testable with these donors | None | None | None | None | 0.0050 |
| 4 | 8.6250 | 52.2500 | 0.3011 | False | not testable with these donors | None | None | None | None | 0.0064 |
| 5a | 14.3750 | 49.0000 | 0.2178 | False | not testable with these donors | None | None | None | None | 0.0087 |
| 5 | 30.2500 | 44.3750 | 0.1415 | False | not testable with these donors | None | None | None | None | 0.0112 |
| 6a | 45.7500 | 42.2500 | 0.1100 | False | not testable with these donors | None | None | None | None | 0.0138 |
| 6 | 63.6250 | 39.6250 | 0.0947 | False | not testable with these donors | None | None | None | None | 0.0157 |
| 7 | 108.6250 | 35.2500 | 0.0665 | False | not testable with these donors | None | None | None | None | 0.0196 |

tau_q = 0, stratum StackExchange, sub_rung_chain (m = 3): no verdict read (positive control failed)
| rung | n_off | mean_contributing | clean_prefix_fraction | testable | label | d_hat | interval | half_width | draws_above_X | unconditional |
|---|---|---|---|---|---|---|---|---|---|---|
| S4 | 4.0000 | 56.0000 | 0.2928 | False | not testable with these donors | None | None | None | None | 0.0013 |
| S16 | 16.0000 | 46.0000 | 0.1966 | False | not testable with these donors | None | None | None | None | 0.0113 |
| S64 | 64.0000 | 40.0000 | 0.1044 | False | not testable with these donors | None | None | None | None | 0.0160 |

tau_q = 0, stratum Wikipedia (en), donor_chain (m = 9): no verdict read (positive control failed)
| rung | n_off | mean_contributing | clean_prefix_fraction | testable | label | d_hat | interval | half_width | draws_above_X | unconditional |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 0.1250 | 64.0000 | 0.9974 | True | holds | 0.0000 | [+0.0000, +0.0000] | 0.0000 | 0/8 | 0.0000 |
| 2 | 1.2500 | 64.0000 | 0.9827 | True | holds | 0.0001 | [+0.0001, +0.0001] | 0.0000 | 0/8 | 0.0001 |
| 3 | 5.1250 | 64.0000 | 0.9213 | True | holds | 0.0003 | [+0.0003, +0.0003] | 0.0000 | 0/8 | 0.0003 |
| 4 | 8.6250 | 63.7500 | 0.8406 | False | not testable with these donors |  |  |  |  | 0.0005 |
| 5a | 14.3750 | 63.7500 | 0.7592 | False | not testable with these donors |  |  |  |  | 0.0009 |
| 5 | 30.2500 | 63.5000 | 0.6136 | False | not testable with these donors |  |  |  |  | 0.0018 |
| 6a | 45.7500 | 63.5000 | 0.5099 | False | not testable with these donors |  |  |  |  | 0.0030 |
| 6 | 63.6250 | 63.1250 | 0.4282 | False | not testable with these donors |  |  |  |  | 0.0042 |
| 7 | 108.6250 | 61.2500 | 0.2929 | False | not testable with these donors |  |  |  |  | 0.0073 |

tau_q = 0, stratum Wikipedia (en), sub_rung_chain (m = 3): no verdict read (positive control failed)
| rung | n_off | mean_contributing | clean_prefix_fraction | testable | label | d_hat | interval | half_width | draws_above_X | unconditional |
|---|---|---|---|---|---|---|---|---|---|---|
| S4 | 4.0000 | 64.0000 | 0.9409 | True | holds | 0.0002 | [+0.0002, +0.0002] | 0.0000 | 0/1 | 0.0002 |
| S16 | 16.0000 | 64.0000 | 0.7457 | True | holds | 0.0009 | [+0.0008, +0.0010] | 0.0001 | 0/1 | 0.0009 |
| S64 | 64.0000 | 64.0000 | 0.4491 | True | holds | 0.0049 | [+0.0043, +0.0057] | 0.0007 | 0/1 | 0.0043 |

### `hard_zero/E/D_unif/tau0.1/ones/incl/ctl-none` (curve 5)
Positive control: unconditional damage on E material at rung 4 and beyond: pass (7 rungs judged); readability floor equals the pre-reads' table: True (18 of 18 rows matched)
The erased set against its plain control per rung (mean over draws; the control's pool is the alive set): rung 1: overlap 6 of 169 erased (0.035; control 169 from a pool of 9959, of which 169 are the erased set's own); rung 2: overlap 169 of 1121 erased (0.147; control 1121 from a pool of 9959, of which 1121 are the erased set's own); rung 3: overlap 2429 of 4544 erased (0.534; control 4544 from a pool of 9959, of which 4544 are the erased set's own); rung 4: overlap 2838 of 4890 erased (0.534; control 4890 from a pool of 9959, of which 4890 are the erased set's own); rung 5a: overlap 4555 of 6501 erased (0.696; control 6501 from a pool of 9959, of which 6501 are the erased set's own); rung 5: overlap 6200 of 7711 erased (0.803; control 7711 from a pool of 9959, of which 7711 are the erased set's own); rung 6a: overlap 7406 of 8490 erased (0.872; control 8490 from a pool of 9959, of which 8490 are the erased set's own); rung 6: overlap 8338 of 9060 erased (0.920; control 9060 from a pool of 9959, of which 9060 are the erased set's own); rung 7: overlap 9388 of 9659 erased (0.972; control 9659 from a pool of 9959, of which 9659 are the erased set's own); rung 8: overlap 9958 of 9966 erased (0.999; control 9966 from a pool of 9959, of which 9958 are the erased set's own, overflow 7)
tau_q = 0.1, stratum all, donor_chain (m = 9): budget rung None
| rung | n_off | mean_contributing | clean_prefix_fraction | testable | label | d_hat | interval | half_width | draws_above_X | unconditional |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 169.0000 | 0.0000 | 0.0000 | False | not testable with these donors | None | None | None | None | 11.5378 |
| 2 | 1120.6250 | 0.0000 | 0.0000 | False | not testable with these donors | None | None | None | None | 12.3670 |
| 3 | 4543.6250 | 0.0000 | 0.0000 | False | not testable with these donors | None | None | None | None | 11.4629 |
| 4 | 4890.2500 | 0.0000 | 0.0000 | False | not testable with these donors | None | None | None | None | 11.0800 |
| 5a | 6501.3750 | 0.0000 | 0.0000 | False | not testable with these donors | None | None | None | None | 11.0008 |
| 5 | 7711.0000 | 0.0000 | 0.0000 | False | not testable with these donors | None | None | None | None | 11.0004 |
| 6a | 8489.5000 | 0.0000 | 0.0000 | False | not testable with these donors | None | None | None | None | 11.1825 |
| 6 | 9060.0000 | 0.0000 | 0.0000 | False | not testable with these donors | None | None | None | None | 11.2475 |
| 7 | 9659.2500 | 0.0000 | 0.0000 | False | not testable with these donors | None | None | None | None | 11.2893 |

tau_q = 0, stratum all, donor_chain (m = 9): budget rung None
| rung | n_off | mean_contributing | clean_prefix_fraction | testable | label | d_hat | interval | half_width | draws_above_X | unconditional |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 169.0000 | 0.0000 | 0.0000 | False | not testable with these donors | None | None | None | None | 11.5378 |
| 2 | 1120.6250 | 0.0000 | 0.0000 | False | not testable with these donors | None | None | None | None | 12.3670 |
| 3 | 4543.6250 | 0.0000 | 0.0000 | False | not testable with these donors | None | None | None | None | 11.4629 |
| 4 | 4890.2500 | 0.0000 | 0.0000 | False | not testable with these donors | None | None | None | None | 11.0800 |
| 5a | 6501.3750 | 0.0000 | 0.0000 | False | not testable with these donors | None | None | None | None | 11.0008 |
| 5 | 7711.0000 | 0.0000 | 0.0000 | False | not testable with these donors | None | None | None | None | 11.0004 |
| 6a | 8489.5000 | 0.0000 | 0.0000 | False | not testable with these donors | None | None | None | None | 11.1825 |
| 6 | 9060.0000 | 0.0000 | 0.0000 | False | not testable with these donors | None | None | None | None | 11.2475 |
| 7 | 9659.2500 | 0.0000 | 0.0000 | False | not testable with these donors | None | None | None | None | 11.2893 |

### `hard_zero/E/D_unif/tau0.1/ones/incl/ctl-plain`
Positive control: does not apply; readability floor equals the pre-reads' table: True (18 of 18 rows matched)
tau_q = 0.1, stratum all, donor_chain (m = 9): budget rung None
| rung | n_off | mean_contributing | clean_prefix_fraction | testable | label | d_hat | interval | half_width | draws_above_X | unconditional |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 169.0000 | 0.1250 | 0.0000 | False | not testable with these donors | None | None | None | None | 1.1202 |
| 2 | 1120.6250 | 0.0000 | 0.0000 | False | not testable with these donors | None | None | None | None | 5.3968 |
| 3 | 4543.6250 | 0.0000 | 0.0000 | False | not testable with these donors | None | None | None | None | 9.5600 |
| 4 | 4890.2500 | 0.0000 | 0.0000 | False | not testable with these donors | None | None | None | None | 8.9393 |
| 5a | 6501.3750 | 0.0000 | 0.0000 | False | not testable with these donors | None | None | None | None | 10.7056 |
| 5 | 7711.0000 | 0.0000 | 0.0000 | False | not testable with these donors | None | None | None | None | 10.0903 |
| 6a | 8489.5000 | 0.0000 | 0.0000 | False | not testable with these donors | None | None | None | None | 10.3834 |
| 6 | 9060.0000 | 0.0000 | 0.0000 | False | not testable with these donors | None | None | None | None | 10.8391 |
| 7 | 9659.2500 | 0.0000 | 0.0000 | False | not testable with these donors | None | None | None | None | 10.4650 |

tau_q = 0, stratum all, donor_chain (m = 9): budget rung None
| rung | n_off | mean_contributing | clean_prefix_fraction | testable | label | d_hat | interval | half_width | draws_above_X | unconditional |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 169.0000 | 0.0000 | 0.0000 | False | not testable with these donors | None | None | None | None | 1.1202 |
| 2 | 1120.6250 | 0.0000 | 0.0000 | False | not testable with these donors | None | None | None | None | 5.3968 |
| 3 | 4543.6250 | 0.0000 | 0.0000 | False | not testable with these donors | None | None | None | None | 9.5600 |
| 4 | 4890.2500 | 0.0000 | 0.0000 | False | not testable with these donors | None | None | None | None | 8.9393 |
| 5a | 6501.3750 | 0.0000 | 0.0000 | False | not testable with these donors | None | None | None | None | 10.7056 |
| 5 | 7711.0000 | 0.0000 | 0.0000 | False | not testable with these donors | None | None | None | None | 10.0903 |
| 6a | 8489.5000 | 0.0000 | 0.0000 | False | not testable with these donors | None | None | None | None | 10.3834 |
| 6 | 9060.0000 | 0.0000 | 0.0000 | False | not testable with these donors | None | None | None | None | 10.8391 |
| 7 | 9659.2500 | 0.0000 | 0.0000 | False | not testable with these donors | None | None | None | None | 10.4650 |

### `code_specific_hard/E/D_code/tau0.1/ones/incl/ctl-none`
Positive control: does not apply; readability floor equals the pre-reads' table: True (24 of 24 rows matched)
tau_q = 0.1, stratum all, donor_chain (m = 9): budget rung 7
| rung | n_off | mean_contributing | clean_prefix_fraction | testable | label | d_hat | interval | half_width | draws_above_X | unconditional |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 0.1250 | 1022.1250 | 0.9916 | True | holds | 0.0000 | [+0.0000, +0.0000] | 0.0000 | 0/8 | 0.0000 |
| 2 | 1.2500 | 1015.2500 | 0.9387 | True | holds | 0.0001 | [+0.0001, +0.0001] | 0.0000 | 0/8 | 0.0003 |
| 3 | 5.1250 | 990.6250 | 0.8142 | True | holds | 0.0004 | [+0.0003, +0.0004] | 0.0000 | 0/8 | 0.0015 |
| 4 | 8.6250 | 978.1250 | 0.7813 | True | holds | 0.0006 | [+0.0006, +0.0007] | 0.0000 | 0/8 | 0.0021 |
| 5a | 14.3750 | 957.8750 | 0.7352 | True | holds | 0.0010 | [+0.0009, +0.0010] | 0.0001 | 0/8 | 0.0030 |
| 5 | 30.2500 | 923.8750 | 0.6247 | True | holds | 0.0019 | [+0.0018, +0.0021] | 0.0001 | 0/8 | 0.0046 |
| 6a | 45.7500 | 894.3750 | 0.5393 | True | holds | 0.0031 | [+0.0029, +0.0033] | 0.0002 | 0/8 | 0.0062 |
| 6 | 63.6250 | 874.0000 | 0.4912 | True | holds | 0.0044 | [+0.0041, +0.0047] | 0.0003 | 0/8 | 0.0077 |
| 7 | 108.6250 | 851.8750 | 0.4496 | True | holds | 0.0074 | [+0.0070, +0.0078] | 0.0004 | 0/8 | 0.0113 |

tau_q = 0.1, stratum all, sub_rung_chain (m = 3): budget rung S64
| rung | n_off | mean_contributing | clean_prefix_fraction | testable | label | d_hat | interval | half_width | draws_above_X | unconditional |
|---|---|---|---|---|---|---|---|---|---|---|
| S4 | 4.0000 | 995.0000 | 0.8132 | True | holds | 0.0002 | [+0.0002, +0.0003] | 0.0000 | 0/1 | 0.0006 |
| S16 | 16.0000 | 943.0000 | 0.6700 | True | holds | 0.0010 | [+0.0009, +0.0011] | 0.0001 | 0/1 | 0.0036 |
| S64 | 64.0000 | 877.0000 | 0.4875 | True | holds | 0.0046 | [+0.0044, +0.0049] | 0.0003 | 0/1 | 0.0080 |

tau_q = 0, stratum all, donor_chain (m = 9): budget rung 7
| rung | n_off | mean_contributing | clean_prefix_fraction | testable | label | d_hat | interval | half_width | draws_above_X | unconditional |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 0.1250 | 1021.7500 | 0.9892 | True | holds | 0.0000 | [+0.0000, +0.0000] | 0.0000 | 0/8 | 0.0000 |
| 2 | 1.2500 | 1012.3750 | 0.9173 | True | holds | 0.0001 | [+0.0001, +0.0001] | 0.0000 | 0/8 | 0.0003 |
| 3 | 5.1250 | 978.5000 | 0.7356 | True | holds | 0.0003 | [+0.0003, +0.0004] | 0.0000 | 0/8 | 0.0015 |
| 4 | 8.6250 | 954.2500 | 0.6551 | True | holds | 0.0006 | [+0.0006, +0.0006] | 0.0000 | 0/8 | 0.0021 |
| 5a | 14.3750 | 922.0000 | 0.5551 | True | holds | 0.0009 | [+0.0009, +0.0010] | 0.0001 | 0/8 | 0.0030 |
| 5 | 30.2500 | 866.8750 | 0.3872 | True | holds | 0.0019 | [+0.0018, +0.0021] | 0.0001 | 0/8 | 0.0046 |
| 6a | 45.7500 | 818.2500 | 0.2780 | True | holds | 0.0031 | [+0.0029, +0.0033] | 0.0002 | 0/8 | 0.0062 |
| 6 | 63.6250 | 776.3750 | 0.2146 | True | holds | 0.0043 | [+0.0041, +0.0046] | 0.0003 | 0/8 | 0.0077 |
| 7 | 108.6250 | 710.7500 | 0.1492 | True | holds | 0.0074 | [+0.0070, +0.0078] | 0.0004 | 0/8 | 0.0113 |

tau_q = 0, stratum all, sub_rung_chain (m = 3): budget rung S64
| rung | n_off | mean_contributing | clean_prefix_fraction | testable | label | d_hat | interval | half_width | draws_above_X | unconditional |
|---|---|---|---|---|---|---|---|---|---|---|
| S4 | 4.0000 | 984.0000 | 0.7561 | True | holds | 0.0002 | [+0.0002, +0.0002] | 0.0000 | 0/1 | 0.0006 |
| S16 | 16.0000 | 900.0000 | 0.4670 | True | holds | 0.0010 | [+0.0009, +0.0010] | 0.0001 | 0/1 | 0.0036 |
| S64 | 64.0000 | 775.0000 | 0.2113 | True | holds | 0.0046 | [+0.0043, +0.0048] | 0.0002 | 0/1 | 0.0080 |

### `never_named_hard/E/D_unif/tau0.1/ones/incl/ctl-none`
Positive control: does not apply; readability floor equals the pre-reads' table: True (22 of 22 rows matched)
Rung 8 alone under the one-cell rule (m = 1, not counted in the donor chain's m), 28946 erased: tau_q = 0.1: testable, d_hat +1.2830 [+1.2655, +1.3016], fails; tau_q = 0: not testable, not testable with these donors; unconditional 1.2841
tau_q = 0.1, stratum all, donor_chain (m = 11): budget rung 1
| rung | n_off | mean_contributing | clean_prefix_fraction | testable | label | d_hat | interval | half_width | draws_above_X | unconditional |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 169.0000 | 1023.8750 | 0.9999 | True | holds | 0.0060 | [+0.0058, +0.0062] | 0.0002 | 0/8 | 0.0060 |
| 2 | 1120.6250 | 1023.0000 | 0.9990 | True | indeterminate | 0.0515 | [+0.0497, +0.0536] | 0.0019 | 3/8 | 0.0515 |
| 3 | 4543.6250 | 1022.2500 | 0.9981 | True | fails | 0.2974 | [+0.2875, +0.3085] | 0.0105 | 8/8 | 0.2974 |
| 4 | 4890.2500 | 1022.1250 | 0.9979 | True | fails | 0.3242 | [+0.3141, +0.3357] | 0.0108 | 8/8 | 0.3242 |
| 5a | 6501.3750 | 1021.8750 | 0.9976 | True | fails | 0.4394 | [+0.4264, +0.4541] | 0.0139 | 8/8 | 0.4396 |
| 5 | 7711.0000 | 1021.6250 | 0.9975 | True | fails | 0.5226 | [+0.5080, +0.5389] | 0.0155 | 8/8 | 0.5228 |
| 6a | 8489.5000 | 1021.6250 | 0.9975 | True | fails | 0.5729 | [+0.5574, +0.5903] | 0.0164 | 8/8 | 0.5732 |
| 6 | 9060.0000 | 1021.5000 | 0.9974 | True | fails | 0.6081 | [+0.5920, +0.6263] | 0.0171 | 8/8 | 0.6086 |
| 7 | 9659.2500 | 1021.5000 | 0.9972 | True | fails | 0.6442 | [+0.6274, +0.6629] | 0.0177 | 8/8 | 0.6446 |
| B50 | 14473.0000 | 1021.2500 | 0.9971 | True | fails | 0.8814 | [+0.8610, +0.9041] | 0.0216 | 8/8 | 0.8821 |
| B75 | 21709.0000 | 1020.5000 | 0.9963 | True | fails | 1.1207 | [+1.0974, +1.1464] | 0.0245 | 8/8 | 1.1217 |

tau_q = 0, stratum all, donor_chain (m = 11): budget rung 2
| rung | n_off | mean_contributing | clean_prefix_fraction | testable | label | d_hat | interval | half_width | draws_above_X | unconditional |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 169.0000 | 976.6250 | 0.5600 | True | holds | 0.0060 | [+0.0058, +0.0062] | 0.0002 | 0/8 | 0.0060 |
| 2 | 1120.6250 | 761.2500 | 0.0976 | True | holds | 0.0473 | [+0.0454, +0.0496] | 0.0021 | 3/8 | 0.0515 |
| 3 | 4543.6250 | 368.5000 | 0.0170 | False | not testable with these donors |  |  |  |  | 0.2974 |
| 4 | 4890.2500 | 367.6250 | 0.0221 | False | not testable with these donors |  |  |  |  | 0.3242 |
| 5a | 6501.3750 | 260.7500 | 0.0116 | False | not testable with these donors |  |  |  |  | 0.4396 |
| 5 | 7711.0000 | 212.1250 | 0.0094 | False | not testable with these donors |  |  |  |  | 0.5228 |
| 6a | 8489.5000 | 181.1250 | 0.0083 | False | not testable with these donors |  |  |  |  | 0.5732 |
| 6 | 9060.0000 | 163.5000 | 0.0076 | False | not testable with these donors |  |  |  |  | 0.6086 |
| 7 | 9659.2500 | 150.0000 | 0.0071 | False | not testable with these donors |  |  |  |  | 0.6446 |
| B50 | 14473.0000 | 72.0000 | 0.0045 | False | not testable with these donors |  |  |  |  | 0.8821 |
| B75 | 21709.0000 | 23.8750 | 0.0027 | False | not testable with these donors |  |  |  |  | 1.1217 |

### `never_named_hard/E/D_unif/tau0.1/ones/excl/ctl-none`
Positive control: does not apply; readability floor equals the pre-reads' table: True (0 of 0 rows matched)
Rung 8 alone under the one-cell rule (m = 1, not counted in the donor chain's m), 28946 erased: tau_q = 0.1: testable, d_hat +1.2751 [+1.2576, +1.2935], fails; tau_q = 0: not testable, not testable with these donors; unconditional 1.2761
### `never_named_hard/E/D_unif/tau0/ones/incl/ctl-none`
Positive control: does not apply; readability floor equals the pre-reads' table: True (0 of 0 rows matched)
Rung 8 alone under the one-cell rule (m = 1, not counted in the donor chain's m), 5336 erased: tau_q = 0.1: testable, d_hat +0.3262 [+0.3187, +0.3343], fails; tau_q = 0: testable, d_hat +0.3131 [+0.3032, +0.3237], fails; unconditional 0.3262
### `hard_zero/E_lab/D_code/tau0.1/ones/incl/ctl-plain`
Positive control: does not apply; readability floor equals the pre-reads' table: True (126 of 126 rows matched)
tau_q = 0.1, stratum all, donor_chain (m = 9): budget rung None
| rung | n_off | mean_contributing | clean_prefix_fraction | testable | label | d_hat | interval | half_width | draws_above_X | unconditional |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 197.8750 | 0.0000 | 0.0000 | False | not testable with these donors | None | None | None | None | 1.2072 |
| 2 | 975.0000 | 0.0000 | 0.0000 | False | not testable with these donors | None | None | None | None | 5.6047 |
| 3 | 3626.3750 | 0.0000 | 0.0000 | False | not testable with these donors | None | None | None | None | 9.1254 |
| 4 | 5156.3750 | 0.0000 | 0.0000 | False | not testable with these donors | None | None | None | None | 10.2470 |
| 5a | 6108.8750 | 0.0000 | 0.0000 | False | not testable with these donors | None | None | None | None | 10.9350 |
| 5 | 7324.5000 | 0.0000 | 0.0000 | False | not testable with these donors | None | None | None | None | 10.9381 |
| 6a | 8146.3750 | 0.0000 | 0.0000 | False | not testable with these donors | None | None | None | None | 11.0713 |
| 6 | 8649.7500 | 0.0000 | 0.0000 | False | not testable with these donors | None | None | None | None | 11.0749 |
| 7 | 9223.2500 | 0.0000 | 0.0000 | False | not testable with these donors | None | None | None | None | 11.0930 |

tau_q = 0.1, stratum Github, donor_chain (m = 9): budget rung None
| rung | n_off | mean_contributing | clean_prefix_fraction | testable | label | d_hat | interval | half_width | draws_above_X | unconditional |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 197.8750 | 0.0000 | 0.0000 | False | not testable with these donors | None | None | None | None | 1.2952 |
| 2 | 975.0000 | 0.0000 | 0.0000 | False | not testable with these donors | None | None | None | None | 6.0747 |
| 3 | 3626.3750 | 0.0000 | 0.0000 | False | not testable with these donors | None | None | None | None | 9.8377 |
| 4 | 5156.3750 | 0.0000 | 0.0000 | False | not testable with these donors | None | None | None | None | 10.8234 |
| 5a | 6108.8750 | 0.0000 | 0.0000 | False | not testable with these donors | None | None | None | None | 11.5642 |
| 5 | 7324.5000 | 0.0000 | 0.0000 | False | not testable with these donors | None | None | None | None | 11.5273 |
| 6a | 8146.3750 | 0.0000 | 0.0000 | False | not testable with these donors | None | None | None | None | 11.6445 |
| 6 | 8649.7500 | 0.0000 | 0.0000 | False | not testable with these donors | None | None | None | None | 11.6264 |
| 7 | 9223.2500 | 0.0000 | 0.0000 | False | not testable with these donors | None | None | None | None | 11.6547 |

tau_q = 0.1, stratum other, donor_chain (m = 9): budget rung None
| rung | n_off | mean_contributing | clean_prefix_fraction | testable | label | d_hat | interval | half_width | draws_above_X | unconditional |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 197.8750 | 0.0000 | 0.0000 | False | not testable with these donors | None | None | None | None | 1.1192 |
| 2 | 975.0000 | 0.0000 | 0.0000 | False | not testable with these donors | None | None | None | None | 5.1346 |
| 3 | 3626.3750 | 0.0000 | 0.0000 | False | not testable with these donors | None | None | None | None | 8.4130 |
| 4 | 5156.3750 | 0.0000 | 0.0000 | False | not testable with these donors | None | None | None | None | 9.6706 |
| 5a | 6108.8750 | 0.0000 | 0.0000 | False | not testable with these donors | None | None | None | None | 10.3059 |
| 5 | 7324.5000 | 0.0000 | 0.0000 | False | not testable with these donors | None | None | None | None | 10.3490 |
| 6a | 8146.3750 | 0.0000 | 0.0000 | False | not testable with these donors | None | None | None | None | 10.4982 |
| 6 | 8649.7500 | 0.0000 | 0.0000 | False | not testable with these donors | None | None | None | None | 10.5235 |
| 7 | 9223.2500 | 0.0000 | 0.0000 | False | not testable with these donors | None | None | None | None | 10.5312 |

tau_q = 0.1, stratum ArXiv, donor_chain (m = 9): budget rung None
| rung | n_off | mean_contributing | clean_prefix_fraction | testable | label | d_hat | interval | half_width | draws_above_X | unconditional |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 197.8750 | 0.0000 | 0.0000 | False | not testable with these donors | None | None | None | None | 1.1376 |
| 2 | 975.0000 | 0.0000 | 0.0000 | False | not testable with these donors | None | None | None | None | 5.2918 |
| 3 | 3626.3750 | 0.0000 | 0.0000 | False | not testable with these donors | None | None | None | None | 8.8548 |
| 4 | 5156.3750 | 0.0000 | 0.0000 | False | not testable with these donors | None | None | None | None | 10.0075 |
| 5a | 6108.8750 | 0.0000 | 0.0000 | False | not testable with these donors | None | None | None | None | 10.6700 |
| 5 | 7324.5000 | 0.0000 | 0.0000 | False | not testable with these donors | None | None | None | None | 10.7483 |
| 6a | 8146.3750 | 0.0000 | 0.0000 | False | not testable with these donors | None | None | None | None | 10.9670 |
| 6 | 8649.7500 | 0.0000 | 0.0000 | False | not testable with these donors | None | None | None | None | 10.9935 |
| 7 | 9223.2500 | 0.0000 | 0.0000 | False | not testable with these donors | None | None | None | None | 10.9910 |

tau_q = 0.1, stratum Pile-CC, donor_chain (m = 9): budget rung None
| rung | n_off | mean_contributing | clean_prefix_fraction | testable | label | d_hat | interval | half_width | draws_above_X | unconditional |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 197.8750 | 0.0000 | 0.0000 | False | not testable with these donors | None | None | None | None | 1.0838 |
| 2 | 975.0000 | 0.0000 | 0.0000 | False | not testable with these donors | None | None | None | None | 4.6794 |
| 3 | 3626.3750 | 0.0000 | 0.0000 | False | not testable with these donors | None | None | None | None | 7.7987 |
| 4 | 5156.3750 | 0.0000 | 0.0000 | False | not testable with these donors | None | None | None | None | 9.1463 |
| 5a | 6108.8750 | 0.0000 | 0.0000 | False | not testable with these donors | None | None | None | None | 9.7171 |
| 5 | 7324.5000 | 0.0000 | 0.0000 | False | not testable with these donors | None | None | None | None | 9.7885 |
| 6a | 8146.3750 | 0.0000 | 0.0000 | False | not testable with these donors | None | None | None | None | 9.9039 |
| 6 | 8649.7500 | 0.0000 | 0.0000 | False | not testable with these donors | None | None | None | None | 9.9366 |
| 7 | 9223.2500 | 0.0000 | 0.0000 | False | not testable with these donors | None | None | None | None | 9.9442 |

tau_q = 0.1, stratum StackExchange, donor_chain (m = 9): budget rung None
| rung | n_off | mean_contributing | clean_prefix_fraction | testable | label | d_hat | interval | half_width | draws_above_X | unconditional |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 197.8750 | 0.0000 | 0.0000 | False | not testable with these donors | None | None | None | None | 1.1013 |
| 2 | 975.0000 | 0.0000 | 0.0000 | False | not testable with these donors | None | None | None | None | 5.5046 |
| 3 | 3626.3750 | 0.0000 | 0.0000 | False | not testable with these donors | None | None | None | None | 8.7935 |
| 4 | 5156.3750 | 0.0000 | 0.0000 | False | not testable with these donors | None | None | None | None | 10.0265 |
| 5a | 6108.8750 | 0.0000 | 0.0000 | False | not testable with these donors | None | None | None | None | 10.7833 |
| 5 | 7324.5000 | 0.0000 | 0.0000 | False | not testable with these donors | None | None | None | None | 10.6859 |
| 6a | 8146.3750 | 0.0000 | 0.0000 | False | not testable with these donors | None | None | None | None | 10.8480 |
| 6 | 8649.7500 | 0.0000 | 0.0000 | False | not testable with these donors | None | None | None | None | 10.8344 |
| 7 | 9223.2500 | 0.0000 | 0.0000 | False | not testable with these donors | None | None | None | None | 10.8768 |

tau_q = 0.1, stratum Wikipedia (en), donor_chain (m = 9): budget rung None
| rung | n_off | mean_contributing | clean_prefix_fraction | testable | label | d_hat | interval | half_width | draws_above_X | unconditional |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 197.8750 | 0.0000 | 0.0000 | False | not testable with these donors | None | None | None | None | 1.1540 |
| 2 | 975.0000 | 0.0000 | 0.0000 | False | not testable with these donors | None | None | None | None | 5.0626 |
| 3 | 3626.3750 | 0.0000 | 0.0000 | False | not testable with these donors | None | None | None | None | 8.2049 |
| 4 | 5156.3750 | 0.0000 | 0.0000 | False | not testable with these donors | None | None | None | None | 9.5020 |
| 5a | 6108.8750 | 0.0000 | 0.0000 | False | not testable with these donors | None | None | None | None | 10.0530 |
| 5 | 7324.5000 | 0.0000 | 0.0000 | False | not testable with these donors | None | None | None | None | 10.1734 |
| 6a | 8146.3750 | 0.0000 | 0.0000 | False | not testable with these donors | None | None | None | None | 10.2739 |
| 6 | 8649.7500 | 0.0000 | 0.0000 | False | not testable with these donors | None | None | None | None | 10.3295 |
| 7 | 9223.2500 | 0.0000 | 0.0000 | False | not testable with these donors | None | None | None | None | 10.3131 |

tau_q = 0, stratum all, donor_chain (m = 9): budget rung None
| rung | n_off | mean_contributing | clean_prefix_fraction | testable | label | d_hat | interval | half_width | draws_above_X | unconditional |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 197.8750 | 0.0000 | 0.0000 | False | not testable with these donors | None | None | None | None | 1.2072 |
| 2 | 975.0000 | 0.0000 | 0.0000 | False | not testable with these donors | None | None | None | None | 5.6047 |
| 3 | 3626.3750 | 0.0000 | 0.0000 | False | not testable with these donors | None | None | None | None | 9.1254 |
| 4 | 5156.3750 | 0.0000 | 0.0000 | False | not testable with these donors | None | None | None | None | 10.2470 |
| 5a | 6108.8750 | 0.0000 | 0.0000 | False | not testable with these donors | None | None | None | None | 10.9350 |
| 5 | 7324.5000 | 0.0000 | 0.0000 | False | not testable with these donors | None | None | None | None | 10.9381 |
| 6a | 8146.3750 | 0.0000 | 0.0000 | False | not testable with these donors | None | None | None | None | 11.0713 |
| 6 | 8649.7500 | 0.0000 | 0.0000 | False | not testable with these donors | None | None | None | None | 11.0749 |
| 7 | 9223.2500 | 0.0000 | 0.0000 | False | not testable with these donors | None | None | None | None | 11.0930 |

tau_q = 0, stratum Github, donor_chain (m = 9): budget rung None
| rung | n_off | mean_contributing | clean_prefix_fraction | testable | label | d_hat | interval | half_width | draws_above_X | unconditional |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 197.8750 | 0.0000 | 0.0000 | False | not testable with these donors | None | None | None | None | 1.2952 |
| 2 | 975.0000 | 0.0000 | 0.0000 | False | not testable with these donors | None | None | None | None | 6.0747 |
| 3 | 3626.3750 | 0.0000 | 0.0000 | False | not testable with these donors | None | None | None | None | 9.8377 |
| 4 | 5156.3750 | 0.0000 | 0.0000 | False | not testable with these donors | None | None | None | None | 10.8234 |
| 5a | 6108.8750 | 0.0000 | 0.0000 | False | not testable with these donors | None | None | None | None | 11.5642 |
| 5 | 7324.5000 | 0.0000 | 0.0000 | False | not testable with these donors | None | None | None | None | 11.5273 |
| 6a | 8146.3750 | 0.0000 | 0.0000 | False | not testable with these donors | None | None | None | None | 11.6445 |
| 6 | 8649.7500 | 0.0000 | 0.0000 | False | not testable with these donors | None | None | None | None | 11.6264 |
| 7 | 9223.2500 | 0.0000 | 0.0000 | False | not testable with these donors | None | None | None | None | 11.6547 |

tau_q = 0, stratum other, donor_chain (m = 9): budget rung None
| rung | n_off | mean_contributing | clean_prefix_fraction | testable | label | d_hat | interval | half_width | draws_above_X | unconditional |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 197.8750 | 0.0000 | 0.0000 | False | not testable with these donors | None | None | None | None | 1.1192 |
| 2 | 975.0000 | 0.0000 | 0.0000 | False | not testable with these donors | None | None | None | None | 5.1346 |
| 3 | 3626.3750 | 0.0000 | 0.0000 | False | not testable with these donors | None | None | None | None | 8.4130 |
| 4 | 5156.3750 | 0.0000 | 0.0000 | False | not testable with these donors | None | None | None | None | 9.6706 |
| 5a | 6108.8750 | 0.0000 | 0.0000 | False | not testable with these donors | None | None | None | None | 10.3059 |
| 5 | 7324.5000 | 0.0000 | 0.0000 | False | not testable with these donors | None | None | None | None | 10.3490 |
| 6a | 8146.3750 | 0.0000 | 0.0000 | False | not testable with these donors | None | None | None | None | 10.4982 |
| 6 | 8649.7500 | 0.0000 | 0.0000 | False | not testable with these donors | None | None | None | None | 10.5235 |
| 7 | 9223.2500 | 0.0000 | 0.0000 | False | not testable with these donors | None | None | None | None | 10.5312 |

tau_q = 0, stratum ArXiv, donor_chain (m = 9): budget rung None
| rung | n_off | mean_contributing | clean_prefix_fraction | testable | label | d_hat | interval | half_width | draws_above_X | unconditional |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 197.8750 | 0.0000 | 0.0000 | False | not testable with these donors | None | None | None | None | 1.1376 |
| 2 | 975.0000 | 0.0000 | 0.0000 | False | not testable with these donors | None | None | None | None | 5.2918 |
| 3 | 3626.3750 | 0.0000 | 0.0000 | False | not testable with these donors | None | None | None | None | 8.8548 |
| 4 | 5156.3750 | 0.0000 | 0.0000 | False | not testable with these donors | None | None | None | None | 10.0075 |
| 5a | 6108.8750 | 0.0000 | 0.0000 | False | not testable with these donors | None | None | None | None | 10.6700 |
| 5 | 7324.5000 | 0.0000 | 0.0000 | False | not testable with these donors | None | None | None | None | 10.7483 |
| 6a | 8146.3750 | 0.0000 | 0.0000 | False | not testable with these donors | None | None | None | None | 10.9670 |
| 6 | 8649.7500 | 0.0000 | 0.0000 | False | not testable with these donors | None | None | None | None | 10.9935 |
| 7 | 9223.2500 | 0.0000 | 0.0000 | False | not testable with these donors | None | None | None | None | 10.9910 |

tau_q = 0, stratum Pile-CC, donor_chain (m = 9): budget rung None
| rung | n_off | mean_contributing | clean_prefix_fraction | testable | label | d_hat | interval | half_width | draws_above_X | unconditional |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 197.8750 | 0.0000 | 0.0000 | False | not testable with these donors | None | None | None | None | 1.0838 |
| 2 | 975.0000 | 0.0000 | 0.0000 | False | not testable with these donors | None | None | None | None | 4.6794 |
| 3 | 3626.3750 | 0.0000 | 0.0000 | False | not testable with these donors | None | None | None | None | 7.7987 |
| 4 | 5156.3750 | 0.0000 | 0.0000 | False | not testable with these donors | None | None | None | None | 9.1463 |
| 5a | 6108.8750 | 0.0000 | 0.0000 | False | not testable with these donors | None | None | None | None | 9.7171 |
| 5 | 7324.5000 | 0.0000 | 0.0000 | False | not testable with these donors | None | None | None | None | 9.7885 |
| 6a | 8146.3750 | 0.0000 | 0.0000 | False | not testable with these donors | None | None | None | None | 9.9039 |
| 6 | 8649.7500 | 0.0000 | 0.0000 | False | not testable with these donors | None | None | None | None | 9.9366 |
| 7 | 9223.2500 | 0.0000 | 0.0000 | False | not testable with these donors | None | None | None | None | 9.9442 |

tau_q = 0, stratum StackExchange, donor_chain (m = 9): budget rung None
| rung | n_off | mean_contributing | clean_prefix_fraction | testable | label | d_hat | interval | half_width | draws_above_X | unconditional |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 197.8750 | 0.0000 | 0.0000 | False | not testable with these donors | None | None | None | None | 1.1013 |
| 2 | 975.0000 | 0.0000 | 0.0000 | False | not testable with these donors | None | None | None | None | 5.5046 |
| 3 | 3626.3750 | 0.0000 | 0.0000 | False | not testable with these donors | None | None | None | None | 8.7935 |
| 4 | 5156.3750 | 0.0000 | 0.0000 | False | not testable with these donors | None | None | None | None | 10.0265 |
| 5a | 6108.8750 | 0.0000 | 0.0000 | False | not testable with these donors | None | None | None | None | 10.7833 |
| 5 | 7324.5000 | 0.0000 | 0.0000 | False | not testable with these donors | None | None | None | None | 10.6859 |
| 6a | 8146.3750 | 0.0000 | 0.0000 | False | not testable with these donors | None | None | None | None | 10.8480 |
| 6 | 8649.7500 | 0.0000 | 0.0000 | False | not testable with these donors | None | None | None | None | 10.8344 |
| 7 | 9223.2500 | 0.0000 | 0.0000 | False | not testable with these donors | None | None | None | None | 10.8768 |

tau_q = 0, stratum Wikipedia (en), donor_chain (m = 9): budget rung None
| rung | n_off | mean_contributing | clean_prefix_fraction | testable | label | d_hat | interval | half_width | draws_above_X | unconditional |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 197.8750 | 0.0000 | 0.0000 | False | not testable with these donors | None | None | None | None | 1.1540 |
| 2 | 975.0000 | 0.0000 | 0.0000 | False | not testable with these donors | None | None | None | None | 5.0626 |
| 3 | 3626.3750 | 0.0000 | 0.0000 | False | not testable with these donors | None | None | None | None | 8.2049 |
| 4 | 5156.3750 | 0.0000 | 0.0000 | False | not testable with these donors | None | None | None | None | 9.5020 |
| 5a | 6108.8750 | 0.0000 | 0.0000 | False | not testable with these donors | None | None | None | None | 10.0530 |
| 5 | 7324.5000 | 0.0000 | 0.0000 | False | not testable with these donors | None | None | None | None | 10.1734 |
| 6a | 8146.3750 | 0.0000 | 0.0000 | False | not testable with these donors | None | None | None | None | 10.2739 |
| 6 | 8649.7500 | 0.0000 | 0.0000 | False | not testable with these donors | None | None | None | None | 10.3295 |
| 7 | 9223.2500 | 0.0000 | 0.0000 | False | not testable with these donors | None | None | None | None | 10.3131 |

### `code_specific_hard/E_lab/D_code/tau0.1/ones/incl/ctl-complement`
Positive control: does not apply; readability floor equals the pre-reads' table: True (168 of 168 rows matched)
tau_q = 0.1, stratum all, donor_chain (m = 9): budget rung 7
| rung | n_off | mean_contributing | clean_prefix_fraction | testable | label | d_hat | interval | half_width | draws_above_X | unconditional |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 0.1250 | 512.0000 | 1.0000 | True | holds | 0.0000 | [+0.0000, +0.0000] | 0.0000 | 0/8 | 0.0000 |
| 2 | 1.2500 | 502.6250 | 0.8548 | True | holds | 0.0002 | [+0.0002, +0.0002] | 0.0000 | 0/8 | 0.0012 |
| 3 | 5.1250 | 480.5000 | 0.6259 | True | holds | 0.0005 | [+0.0004, +0.0006] | 0.0001 | 0/8 | 0.0034 |
| 4 | 8.6250 | 469.5000 | 0.5877 | True | holds | 0.0008 | [+0.0007, +0.0009] | 0.0001 | 0/8 | 0.0041 |
| 5a | 14.3750 | 456.7500 | 0.5112 | True | holds | 0.0012 | [+0.0011, +0.0014] | 0.0001 | 0/8 | 0.0066 |
| 5 | 30.2500 | 429.7500 | 0.4513 | True | holds | 0.0024 | [+0.0022, +0.0026] | 0.0002 | 0/8 | 0.0082 |
| 6a | 45.7500 | 415.6250 | 0.4297 | True | holds | 0.0036 | [+0.0033, +0.0039] | 0.0003 | 0/8 | 0.0102 |
| 6 | 63.6250 | 400.5000 | 0.4084 | True | holds | 0.0050 | [+0.0046, +0.0054] | 0.0004 | 0/8 | 0.0116 |
| 7 | 108.6250 | 381.1250 | 0.3814 | True | holds | 0.0085 | [+0.0079, +0.0093] | 0.0007 | 0/8 | 0.0155 |

tau_q = 0.1, stratum all, sub_rung_chain (m = 3): budget rung S64
| rung | n_off | mean_contributing | clean_prefix_fraction | testable | label | d_hat | interval | half_width | draws_above_X | unconditional |
|---|---|---|---|---|---|---|---|---|---|---|
| S4 | 4.0000 | 483.0000 | 0.5714 | True | holds | 0.0005 | [+0.0004, +0.0006] | 0.0001 | 0/1 | 0.0046 |
| S16 | 16.0000 | 463.0000 | 0.5310 | True | holds | 0.0012 | [+0.0011, +0.0014] | 0.0001 | 0/1 | 0.0073 |
| S64 | 64.0000 | 398.0000 | 0.4087 | True | holds | 0.0055 | [+0.0051, +0.0059] | 0.0004 | 0/1 | 0.0119 |

tau_q = 0.1, stratum Github, donor_chain (m = 9): budget rung 7
| rung | n_off | mean_contributing | clean_prefix_fraction | testable | label | d_hat | interval | half_width | draws_above_X | unconditional |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 0.1250 | 256.0000 | 1.0000 | True | holds | 0.0000 | [+0.0000, +0.0000] | 0.0000 | 0/8 | 0.0000 |
| 2 | 1.2500 | 248.0000 | 0.7686 | True | holds | 0.0003 | [+0.0002, +0.0004] | 0.0001 | 0/8 | 0.0020 |
| 3 | 5.1250 | 229.7500 | 0.4136 | True | holds | 0.0008 | [+0.0007, +0.0009] | 0.0001 | 0/8 | 0.0056 |
| 4 | 8.6250 | 220.7500 | 0.3725 | True | holds | 0.0011 | [+0.0010, +0.0013] | 0.0002 | 0/8 | 0.0067 |
| 5a | 14.3750 | 210.7500 | 0.2664 | True | holds | 0.0018 | [+0.0016, +0.0020] | 0.0002 | 0/8 | 0.0107 |
| 5 | 30.2500 | 192.0000 | 0.2288 | True | holds | 0.0033 | [+0.0030, +0.0037] | 0.0003 | 0/8 | 0.0127 |
| 6a | 45.7500 | 183.5000 | 0.2128 | True | holds | 0.0049 | [+0.0044, +0.0054] | 0.0005 | 0/8 | 0.0155 |
| 6 | 63.6250 | 174.8750 | 0.2053 | True | holds | 0.0067 | [+0.0061, +0.0075] | 0.0007 | 0/8 | 0.0171 |
| 7 | 108.6250 | 161.1250 | 0.1778 | True | holds | 0.0114 | [+0.0102, +0.0128] | 0.0013 | 0/8 | 0.0218 |

tau_q = 0.1, stratum Github, sub_rung_chain (m = 3): budget rung S64
| rung | n_off | mean_contributing | clean_prefix_fraction | testable | label | d_hat | interval | half_width | draws_above_X | unconditional |
|---|---|---|---|---|---|---|---|---|---|---|
| S4 | 4.0000 | 235.0000 | 0.3711 | True | holds | 0.0008 | [+0.0006, +0.0010] | 0.0002 | 0/1 | 0.0075 |
| S16 | 16.0000 | 218.0000 | 0.3268 | True | holds | 0.0018 | [+0.0015, +0.0020] | 0.0003 | 0/1 | 0.0116 |
| S64 | 64.0000 | 180.0000 | 0.2321 | True | holds | 0.0074 | [+0.0066, +0.0081] | 0.0008 | 0/1 | 0.0171 |

tau_q = 0.1, stratum other, donor_chain (m = 9): budget rung 7
| rung | n_off | mean_contributing | clean_prefix_fraction | testable | label | d_hat | interval | half_width | draws_above_X | unconditional |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 0.1250 | 256.0000 | 1.0000 | True | holds | 0.0000 | [+0.0000, +0.0000] | 0.0000 | 0/8 | 0.0000 |
| 2 | 1.2500 | 254.6250 | 0.9410 | True | holds | 0.0001 | [+0.0001, +0.0001] | 0.0000 | 0/8 | 0.0005 |
| 3 | 5.1250 | 250.7500 | 0.8382 | True | holds | 0.0003 | [+0.0002, +0.0003] | 0.0001 | 0/8 | 0.0013 |
| 4 | 8.6250 | 248.7500 | 0.8028 | True | holds | 0.0005 | [+0.0004, +0.0005] | 0.0001 | 0/8 | 0.0015 |
| 5a | 14.3750 | 246.0000 | 0.7559 | True | holds | 0.0008 | [+0.0007, +0.0008] | 0.0001 | 0/8 | 0.0026 |
| 5 | 30.2500 | 237.7500 | 0.6739 | True | holds | 0.0016 | [+0.0015, +0.0018] | 0.0001 | 0/8 | 0.0037 |
| 6a | 45.7500 | 232.1250 | 0.6466 | True | holds | 0.0026 | [+0.0024, +0.0028] | 0.0002 | 0/8 | 0.0049 |
| 6 | 63.6250 | 225.6250 | 0.6114 | True | holds | 0.0037 | [+0.0034, +0.0040] | 0.0003 | 0/8 | 0.0061 |
| 7 | 108.6250 | 220.0000 | 0.5851 | True | holds | 0.0064 | [+0.0060, +0.0070] | 0.0005 | 0/8 | 0.0092 |

tau_q = 0.1, stratum other, sub_rung_chain (m = 3): budget rung S64
| rung | n_off | mean_contributing | clean_prefix_fraction | testable | label | d_hat | interval | half_width | draws_above_X | unconditional |
|---|---|---|---|---|---|---|---|---|---|---|
| S4 | 4.0000 | 248.0000 | 0.7717 | True | holds | 0.0002 | [+0.0002, +0.0003] | 0.0000 | 0/1 | 0.0018 |
| S16 | 16.0000 | 245.0000 | 0.7352 | True | holds | 0.0008 | [+0.0007, +0.0009] | 0.0001 | 0/1 | 0.0029 |
| S64 | 64.0000 | 218.0000 | 0.5853 | True | holds | 0.0039 | [+0.0036, +0.0042] | 0.0003 | 0/1 | 0.0068 |

tau_q = 0.1, stratum ArXiv, donor_chain (m = 9): budget rung 1
| rung | n_off | mean_contributing | clean_prefix_fraction | testable | label | d_hat | interval | half_width | draws_above_X | unconditional |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 0.1250 | 64.0000 | 1.0000 | True | holds | 0.0000 | [-0.0000, +0.0000] | 0.0000 | 0/8 | 0.0000 |
| 2 | 1.2500 | 63.6250 | 0.9253 | False | not testable with these donors |  |  |  |  | 0.0001 |
| 3 | 5.1250 | 63.3750 | 0.8658 | False | not testable with these donors |  |  |  |  | 0.0003 |
| 4 | 8.6250 | 61.8750 | 0.7001 | False | not testable with these donors |  |  |  |  | 0.0006 |
| 5a | 14.3750 | 61.0000 | 0.6237 | False | not testable with these donors |  |  |  |  | 0.0009 |
| 5 | 30.2500 | 56.7500 | 0.4239 | False | not testable with these donors |  |  |  |  | 0.0020 |
| 6a | 45.7500 | 54.3750 | 0.3665 | False | not testable with these donors |  |  |  |  | 0.0031 |
| 6 | 63.6250 | 50.3750 | 0.3085 | False | not testable with these donors |  |  |  |  | 0.0043 |
| 7 | 108.6250 | 48.5000 | 0.2655 | False | not testable with these donors |  |  |  |  | 0.0073 |

tau_q = 0.1, stratum ArXiv, sub_rung_chain (m = 3): budget rung None
| rung | n_off | mean_contributing | clean_prefix_fraction | testable | label | d_hat | interval | half_width | draws_above_X | unconditional |
|---|---|---|---|---|---|---|---|---|---|---|
| S4 | 4.0000 | 61.0000 | 0.5438 | False | not testable with these donors | None | None | None | None | 0.0006 |
| S16 | 16.0000 | 59.0000 | 0.4579 | False | not testable with these donors | None | None | None | None | 0.0014 |
| S64 | 64.0000 | 46.0000 | 0.2377 | False | not testable with these donors | None | None | None | None | 0.0066 |

tau_q = 0.1, stratum Pile-CC, donor_chain (m = 9): budget rung 2
| rung | n_off | mean_contributing | clean_prefix_fraction | testable | label | d_hat | interval | half_width | draws_above_X | unconditional |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 0.1250 | 64.0000 | 1.0000 | True | holds | 0.0000 | [-0.0000, +0.0000] | 0.0000 | 0/8 | 0.0000 |
| 2 | 1.2500 | 64.0000 | 1.0000 | True | holds | 0.0000 | [+0.0000, +0.0000] | 0.0000 | 0/8 | 0.0000 |
| 3 | 5.1250 | 63.8750 | 0.9960 | False | not testable with these donors |  |  |  |  | 0.0002 |
| 4 | 8.6250 | 63.8750 | 0.9941 | False | not testable with these donors |  |  |  |  | 0.0003 |
| 5a | 14.3750 | 63.7500 | 0.9912 | False | not testable with these donors |  |  |  |  | 0.0006 |
| 5 | 30.2500 | 63.5000 | 0.9775 | False | not testable with these donors |  |  |  |  | 0.0014 |
| 6a | 45.7500 | 63.1250 | 0.9686 | False | not testable with these donors |  |  |  |  | 0.0022 |
| 6 | 63.6250 | 63.0000 | 0.9606 | False | not testable with these donors |  |  |  |  | 0.0032 |
| 7 | 108.6250 | 62.2500 | 0.9444 | False | not testable with these donors |  |  |  |  | 0.0058 |

tau_q = 0.1, stratum Pile-CC, sub_rung_chain (m = 3): budget rung S4
| rung | n_off | mean_contributing | clean_prefix_fraction | testable | label | d_hat | interval | half_width | draws_above_X | unconditional |
|---|---|---|---|---|---|---|---|---|---|---|
| S4 | 4.0000 | 64.0000 | 1.0000 | True | holds | 0.0001 | [+0.0001, +0.0001] | 0.0000 | 0/1 | 0.0001 |
| S16 | 16.0000 | 63.0000 | 0.9768 | False | not testable with these donors |  |  |  |  | 0.0006 |
| S64 | 64.0000 | 62.0000 | 0.9612 | False | not testable with these donors |  |  |  |  | 0.0034 |

tau_q = 0.1, stratum StackExchange, donor_chain (m = 9): budget rung 1
| rung | n_off | mean_contributing | clean_prefix_fraction | testable | label | d_hat | interval | half_width | draws_above_X | unconditional |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 0.1250 | 64.0000 | 1.0000 | True | holds | 0.0000 | [+0.0000, +0.0000] | 0.0000 | 0/8 | 0.0000 |
| 2 | 1.2500 | 63.0000 | 0.8386 | False | not testable with these donors |  |  |  |  | 0.0016 |
| 3 | 5.1250 | 59.5000 | 0.4920 | False | not testable with these donors |  |  |  |  | 0.0045 |
| 4 | 8.6250 | 59.0000 | 0.5208 | False | not testable with these donors |  |  |  |  | 0.0048 |
| 5a | 14.3750 | 57.3750 | 0.4166 | False | not testable with these donors |  |  |  |  | 0.0082 |
| 5 | 30.2500 | 53.6250 | 0.3117 | False | not testable with these donors |  |  |  |  | 0.0096 |
| 6a | 45.7500 | 51.0000 | 0.2771 | False | not testable with these donors |  |  |  |  | 0.0117 |
| 6 | 63.6250 | 48.6250 | 0.2074 | False | not testable with these donors |  |  |  |  | 0.0131 |
| 7 | 108.6250 | 45.8750 | 0.1705 | False | not testable with these donors |  |  |  |  | 0.0169 |

tau_q = 0.1, stratum StackExchange, sub_rung_chain (m = 3): budget rung None
| rung | n_off | mean_contributing | clean_prefix_fraction | testable | label | d_hat | interval | half_width | draws_above_X | unconditional |
|---|---|---|---|---|---|---|---|---|---|---|
| S4 | 4.0000 | 59.0000 | 0.5431 | False | not testable with these donors | None | None | None | None | 0.0063 |
| S16 | 16.0000 | 59.0000 | 0.5059 | False | not testable with these donors | None | None | None | None | 0.0087 |
| S64 | 64.0000 | 47.0000 | 0.1764 | False | not testable with these donors | None | None | None | None | 0.0130 |

tau_q = 0.1, stratum Wikipedia (en), donor_chain (m = 9): budget rung 4
| rung | n_off | mean_contributing | clean_prefix_fraction | testable | label | d_hat | interval | half_width | draws_above_X | unconditional |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 0.1250 | 64.0000 | 1.0000 | True | holds | 0.0000 | [+0.0000, +0.0000] | 0.0000 | 0/8 | 0.0000 |
| 2 | 1.2500 | 64.0000 | 1.0000 | True | holds | 0.0001 | [+0.0001, +0.0001] | 0.0000 | 0/8 | 0.0001 |
| 3 | 5.1250 | 64.0000 | 0.9992 | True | holds | 0.0002 | [+0.0002, +0.0003] | 0.0000 | 0/8 | 0.0002 |
| 4 | 8.6250 | 64.0000 | 0.9963 | True | holds | 0.0004 | [+0.0004, +0.0004] | 0.0000 | 0/8 | 0.0004 |
| 5a | 14.3750 | 63.8750 | 0.9922 | False | not testable with these donors |  |  |  |  | 0.0007 |
| 5 | 30.2500 | 63.8750 | 0.9824 | False | not testable with these donors |  |  |  |  | 0.0017 |
| 6a | 45.7500 | 63.6250 | 0.9743 | False | not testable with these donors |  |  |  |  | 0.0027 |
| 6 | 63.6250 | 63.6250 | 0.9691 | False | not testable with these donors |  |  |  |  | 0.0038 |
| 7 | 108.6250 | 63.3750 | 0.9598 | False | not testable with these donors |  |  |  |  | 0.0068 |

tau_q = 0.1, stratum Wikipedia (en), sub_rung_chain (m = 3): budget rung S16
| rung | n_off | mean_contributing | clean_prefix_fraction | testable | label | d_hat | interval | half_width | draws_above_X | unconditional |
|---|---|---|---|---|---|---|---|---|---|---|
| S4 | 4.0000 | 64.0000 | 1.0000 | True | holds | 0.0002 | [+0.0002, +0.0002] | 0.0000 | 0/1 | 0.0002 |
| S16 | 16.0000 | 64.0000 | 1.0000 | True | holds | 0.0008 | [+0.0007, +0.0008] | 0.0001 | 0/1 | 0.0008 |
| S64 | 64.0000 | 63.0000 | 0.9660 | False | not testable with these donors |  |  |  |  | 0.0041 |

tau_q = 0, stratum all, donor_chain (m = 9): budget rung 7
| rung | n_off | mean_contributing | clean_prefix_fraction | testable | label | d_hat | interval | half_width | draws_above_X | unconditional |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 0.1250 | 512.0000 | 0.9980 | True | holds | 0.0000 | [+0.0000, +0.0000] | 0.0000 | 0/8 | 0.0000 |
| 2 | 1.2500 | 501.3750 | 0.8342 | True | holds | 0.0002 | [+0.0001, +0.0002] | 0.0000 | 0/8 | 0.0012 |
| 3 | 5.1250 | 475.3750 | 0.5568 | True | holds | 0.0005 | [+0.0004, +0.0006] | 0.0001 | 0/8 | 0.0034 |
| 4 | 8.6250 | 459.2500 | 0.4924 | True | holds | 0.0007 | [+0.0006, +0.0008] | 0.0001 | 0/8 | 0.0041 |
| 5a | 14.3750 | 442.3750 | 0.3948 | True | holds | 0.0012 | [+0.0011, +0.0013] | 0.0001 | 0/8 | 0.0066 |
| 5 | 30.2500 | 399.8750 | 0.2836 | True | holds | 0.0024 | [+0.0022, +0.0026] | 0.0002 | 0/8 | 0.0082 |
| 6a | 45.7500 | 376.6250 | 0.2252 | True | holds | 0.0036 | [+0.0033, +0.0039] | 0.0003 | 0/8 | 0.0102 |
| 6 | 63.6250 | 349.7500 | 0.1806 | True | holds | 0.0050 | [+0.0046, +0.0055] | 0.0005 | 0/8 | 0.0116 |
| 7 | 108.6250 | 310.6250 | 0.1281 | True | holds | 0.0087 | [+0.0079, +0.0095] | 0.0008 | 0/8 | 0.0155 |

tau_q = 0, stratum all, sub_rung_chain (m = 3): budget rung S64
| rung | n_off | mean_contributing | clean_prefix_fraction | testable | label | d_hat | interval | half_width | draws_above_X | unconditional |
|---|---|---|---|---|---|---|---|---|---|---|
| S4 | 4.0000 | 478.0000 | 0.5138 | True | holds | 0.0005 | [+0.0004, +0.0006] | 0.0001 | 0/1 | 0.0046 |
| S16 | 16.0000 | 448.0000 | 0.3708 | True | holds | 0.0012 | [+0.0011, +0.0013] | 0.0001 | 0/1 | 0.0073 |
| S64 | 64.0000 | 340.0000 | 0.1763 | True | holds | 0.0058 | [+0.0052, +0.0065] | 0.0006 | 0/1 | 0.0119 |

tau_q = 0, stratum Github, donor_chain (m = 9): budget rung 7
| rung | n_off | mean_contributing | clean_prefix_fraction | testable | label | d_hat | interval | half_width | draws_above_X | unconditional |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 0.1250 | 256.0000 | 0.9996 | True | holds | 0.0000 | [+0.0000, +0.0000] | 0.0000 | 0/8 | 0.0000 |
| 2 | 1.2500 | 247.2500 | 0.7512 | True | holds | 0.0003 | [+0.0002, +0.0003] | 0.0001 | 0/8 | 0.0020 |
| 3 | 5.1250 | 226.1250 | 0.3609 | True | holds | 0.0007 | [+0.0006, +0.0009] | 0.0001 | 0/8 | 0.0056 |
| 4 | 8.6250 | 213.8750 | 0.3137 | True | holds | 0.0010 | [+0.0009, +0.0012] | 0.0001 | 0/8 | 0.0067 |
| 5a | 14.3750 | 201.6250 | 0.2053 | True | holds | 0.0017 | [+0.0015, +0.0019] | 0.0002 | 0/8 | 0.0107 |
| 5 | 30.2500 | 172.2500 | 0.1393 | True | holds | 0.0033 | [+0.0030, +0.0038] | 0.0004 | 0/8 | 0.0127 |
| 6a | 45.7500 | 157.8750 | 0.1074 | True | holds | 0.0049 | [+0.0044, +0.0055] | 0.0006 | 0/8 | 0.0155 |
| 6 | 63.6250 | 142.6250 | 0.0872 | True | holds | 0.0069 | [+0.0061, +0.0079] | 0.0009 | 0/8 | 0.0171 |
| 7 | 108.6250 | 120.2500 | 0.0553 | True | holds | 0.0118 | [+0.0103, +0.0136] | 0.0016 | 0/8 | 0.0218 |

tau_q = 0, stratum Github, sub_rung_chain (m = 3): budget rung S64
| rung | n_off | mean_contributing | clean_prefix_fraction | testable | label | d_hat | interval | half_width | draws_above_X | unconditional |
|---|---|---|---|---|---|---|---|---|---|---|
| S4 | 4.0000 | 233.0000 | 0.3231 | True | holds | 0.0007 | [+0.0006, +0.0010] | 0.0002 | 0/1 | 0.0075 |
| S16 | 16.0000 | 207.0000 | 0.2217 | True | holds | 0.0017 | [+0.0014, +0.0019] | 0.0003 | 0/1 | 0.0116 |
| S64 | 64.0000 | 140.0000 | 0.0925 | True | holds | 0.0080 | [+0.0068, +0.0094] | 0.0013 | 0/1 | 0.0171 |

tau_q = 0, stratum other, donor_chain (m = 9): budget rung 7
| rung | n_off | mean_contributing | clean_prefix_fraction | testable | label | d_hat | interval | half_width | draws_above_X | unconditional |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 0.1250 | 256.0000 | 0.9965 | True | holds | 0.0000 | [-0.0000, +0.0000] | 0.0000 | 0/8 | 0.0000 |
| 2 | 1.2500 | 254.1250 | 0.9171 | True | holds | 0.0001 | [+0.0001, +0.0001] | 0.0000 | 0/8 | 0.0005 |
| 3 | 5.1250 | 249.2500 | 0.7527 | True | holds | 0.0003 | [+0.0002, +0.0003] | 0.0001 | 0/8 | 0.0013 |
| 4 | 8.6250 | 245.3750 | 0.6710 | True | holds | 0.0004 | [+0.0004, +0.0005] | 0.0000 | 0/8 | 0.0015 |
| 5a | 14.3750 | 240.7500 | 0.5843 | True | holds | 0.0008 | [+0.0007, +0.0008] | 0.0001 | 0/8 | 0.0026 |
| 5 | 30.2500 | 227.6250 | 0.4280 | True | holds | 0.0017 | [+0.0016, +0.0018] | 0.0001 | 0/8 | 0.0037 |
| 6a | 45.7500 | 218.7500 | 0.3429 | True | holds | 0.0027 | [+0.0025, +0.0029] | 0.0002 | 0/8 | 0.0049 |
| 6 | 63.6250 | 207.1250 | 0.2740 | True | holds | 0.0038 | [+0.0035, +0.0041] | 0.0003 | 0/8 | 0.0061 |
| 7 | 108.6250 | 190.3750 | 0.2008 | True | holds | 0.0067 | [+0.0061, +0.0072] | 0.0005 | 0/8 | 0.0092 |

tau_q = 0, stratum other, sub_rung_chain (m = 3): budget rung S64
| rung | n_off | mean_contributing | clean_prefix_fraction | testable | label | d_hat | interval | half_width | draws_above_X | unconditional |
|---|---|---|---|---|---|---|---|---|---|---|
| S4 | 4.0000 | 245.0000 | 0.7046 | True | holds | 0.0002 | [+0.0002, +0.0003] | 0.0000 | 0/1 | 0.0018 |
| S16 | 16.0000 | 241.0000 | 0.5199 | True | holds | 0.0008 | [+0.0007, +0.0008] | 0.0001 | 0/1 | 0.0029 |
| S64 | 64.0000 | 200.0000 | 0.2601 | True | holds | 0.0043 | [+0.0039, +0.0048] | 0.0004 | 0/1 | 0.0068 |

tau_q = 0, stratum ArXiv, donor_chain (m = 9): budget rung 1
| rung | n_off | mean_contributing | clean_prefix_fraction | testable | label | d_hat | interval | half_width | draws_above_X | unconditional |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 0.1250 | 64.0000 | 1.0000 | True | holds | 0.0000 | [-0.0000, +0.0000] | 0.0000 | 0/8 | 0.0000 |
| 2 | 1.2500 | 63.3750 | 0.8983 | False | not testable with these donors |  |  |  |  | 0.0001 |
| 3 | 5.1250 | 63.0000 | 0.7907 | False | not testable with these donors |  |  |  |  | 0.0003 |
| 4 | 8.6250 | 60.3750 | 0.5982 | False | not testable with these donors |  |  |  |  | 0.0006 |
| 5a | 14.3750 | 58.6250 | 0.4848 | False | not testable with these donors |  |  |  |  | 0.0009 |
| 5 | 30.2500 | 52.7500 | 0.2981 | False | not testable with these donors |  |  |  |  | 0.0020 |
| 6a | 45.7500 | 49.2500 | 0.2265 | False | not testable with these donors |  |  |  |  | 0.0031 |
| 6 | 63.6250 | 44.2500 | 0.1698 | False | not testable with these donors |  |  |  |  | 0.0043 |
| 7 | 108.6250 | 39.7500 | 0.1204 | False | not testable with these donors |  |  |  |  | 0.0073 |

tau_q = 0, stratum ArXiv, sub_rung_chain (m = 3): budget rung None
| rung | n_off | mean_contributing | clean_prefix_fraction | testable | label | d_hat | interval | half_width | draws_above_X | unconditional |
|---|---|---|---|---|---|---|---|---|---|---|
| S4 | 4.0000 | 59.0000 | 0.4852 | False | not testable with these donors | None | None | None | None | 0.0006 |
| S16 | 16.0000 | 57.0000 | 0.3344 | False | not testable with these donors | None | None | None | None | 0.0014 |
| S64 | 64.0000 | 43.0000 | 0.1359 | False | not testable with these donors | None | None | None | None | 0.0066 |

tau_q = 0, stratum Pile-CC, donor_chain (m = 9): budget rung 2
| rung | n_off | mean_contributing | clean_prefix_fraction | testable | label | d_hat | interval | half_width | draws_above_X | unconditional |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 0.1250 | 64.0000 | 0.9954 | True | holds | 0.0000 | [-0.0000, +0.0000] | 0.0000 | 0/8 | 0.0000 |
| 2 | 1.2500 | 64.0000 | 0.9666 | True | holds | 0.0000 | [+0.0000, +0.0000] | 0.0000 | 0/8 | 0.0000 |
| 3 | 5.1250 | 63.6250 | 0.8672 | False | not testable with these donors |  |  |  |  | 0.0002 |
| 4 | 8.6250 | 63.5000 | 0.8000 | False | not testable with these donors |  |  |  |  | 0.0003 |
| 5a | 14.3750 | 62.8750 | 0.7234 | False | not testable with these donors |  |  |  |  | 0.0006 |
| 5 | 30.2500 | 62.1250 | 0.5858 | False | not testable with these donors |  |  |  |  | 0.0014 |
| 6a | 45.7500 | 61.0000 | 0.4759 | False | not testable with these donors |  |  |  |  | 0.0022 |
| 6 | 63.6250 | 59.8750 | 0.4110 | False | not testable with these donors |  |  |  |  | 0.0032 |
| 7 | 108.6250 | 57.0000 | 0.3142 | False | not testable with these donors |  |  |  |  | 0.0058 |

tau_q = 0, stratum Pile-CC, sub_rung_chain (m = 3): budget rung S4
| rung | n_off | mean_contributing | clean_prefix_fraction | testable | label | d_hat | interval | half_width | draws_above_X | unconditional |
|---|---|---|---|---|---|---|---|---|---|---|
| S4 | 4.0000 | 64.0000 | 0.9142 | True | holds | 0.0001 | [+0.0001, +0.0001] | 0.0000 | 0/1 | 0.0001 |
| S16 | 16.0000 | 63.0000 | 0.6286 | False | not testable with these donors |  |  |  |  | 0.0006 |
| S64 | 64.0000 | 57.0000 | 0.3924 | False | not testable with these donors |  |  |  |  | 0.0034 |

tau_q = 0, stratum StackExchange, donor_chain (m = 9): budget rung 1
| rung | n_off | mean_contributing | clean_prefix_fraction | testable | label | d_hat | interval | half_width | draws_above_X | unconditional |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 0.1250 | 64.0000 | 0.9981 | True | holds | 0.0000 | [-0.0000, +0.0000] | 0.0000 | 0/8 | 0.0000 |
| 2 | 1.2500 | 62.7500 | 0.8238 | False | not testable with these donors |  |  |  |  | 0.0016 |
| 3 | 5.1250 | 58.6250 | 0.4340 | False | not testable with these donors |  |  |  |  | 0.0045 |
| 4 | 8.6250 | 57.7500 | 0.4079 | False | not testable with these donors |  |  |  |  | 0.0048 |
| 5a | 14.3750 | 55.6250 | 0.2989 | False | not testable with these donors |  |  |  |  | 0.0082 |
| 5 | 30.2500 | 50.7500 | 0.1932 | False | not testable with these donors |  |  |  |  | 0.0096 |
| 6a | 45.7500 | 47.6250 | 0.1439 | False | not testable with these donors |  |  |  |  | 0.0117 |
| 6 | 63.6250 | 44.0000 | 0.0956 | False | not testable with these donors |  |  |  |  | 0.0131 |
| 7 | 108.6250 | 38.0000 | 0.0656 | False | not testable with these donors |  |  |  |  | 0.0169 |

tau_q = 0, stratum StackExchange, sub_rung_chain (m = 3): budget rung None
| rung | n_off | mean_contributing | clean_prefix_fraction | testable | label | d_hat | interval | half_width | draws_above_X | unconditional |
|---|---|---|---|---|---|---|---|---|---|---|
| S4 | 4.0000 | 58.0000 | 0.4809 | False | not testable with these donors | None | None | None | None | 0.0063 |
| S16 | 16.0000 | 58.0000 | 0.3444 | False | not testable with these donors | None | None | None | None | 0.0087 |
| S64 | 64.0000 | 43.0000 | 0.0763 | False | not testable with these donors | None | None | None | None | 0.0130 |

tau_q = 0, stratum Wikipedia (en), donor_chain (m = 9): budget rung 3
| rung | n_off | mean_contributing | clean_prefix_fraction | testable | label | d_hat | interval | half_width | draws_above_X | unconditional |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 0.1250 | 64.0000 | 0.9924 | True | holds | 0.0000 | [+0.0000, +0.0000] | 0.0000 | 0/8 | 0.0000 |
| 2 | 1.2500 | 64.0000 | 0.9798 | True | holds | 0.0001 | [+0.0001, +0.0001] | 0.0000 | 0/8 | 0.0001 |
| 3 | 5.1250 | 64.0000 | 0.9189 | True | holds | 0.0002 | [+0.0002, +0.0003] | 0.0000 | 0/8 | 0.0002 |
| 4 | 8.6250 | 63.7500 | 0.8779 | False | not testable with these donors |  |  |  |  | 0.0004 |
| 5a | 14.3750 | 63.6250 | 0.8303 | False | not testable with these donors |  |  |  |  | 0.0007 |
| 5 | 30.2500 | 62.0000 | 0.6348 | False | not testable with these donors |  |  |  |  | 0.0017 |
| 6a | 45.7500 | 60.8750 | 0.5254 | False | not testable with these donors |  |  |  |  | 0.0027 |
| 6 | 63.6250 | 59.0000 | 0.4195 | False | not testable with these donors |  |  |  |  | 0.0038 |
| 7 | 108.6250 | 55.6250 | 0.3031 | False | not testable with these donors |  |  |  |  | 0.0068 |

tau_q = 0, stratum Wikipedia (en), sub_rung_chain (m = 3): budget rung S4
| rung | n_off | mean_contributing | clean_prefix_fraction | testable | label | d_hat | interval | half_width | draws_above_X | unconditional |
|---|---|---|---|---|---|---|---|---|---|---|
| S4 | 4.0000 | 64.0000 | 0.9380 | True | holds | 0.0002 | [+0.0002, +0.0002] | 0.0000 | 0/1 | 0.0002 |
| S16 | 16.0000 | 63.0000 | 0.7721 | False | not testable with these donors |  |  |  |  | 0.0008 |
| S64 | 64.0000 | 57.0000 | 0.4359 | False | not testable with these donors |  |  |  |  | 0.0041 |

### `code_specific_hard/E_lab/D_code/tau0.1/ones/incl/ctl-plain`
Positive control: does not apply; readability floor equals the pre-reads' table: True (168 of 168 rows matched)
tau_q = 0.1, stratum all, donor_chain (m = 9): budget rung 3
| rung | n_off | mean_contributing | clean_prefix_fraction | testable | label | d_hat | interval | half_width | draws_above_X | unconditional |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 0.1250 | 511.7500 | 0.9756 | True | holds | 0.0000 | [+0.0000, +0.0000] | 0.0000 | 0/8 | 0.0000 |
| 2 | 1.2500 | 436.2500 | 0.6796 | True | holds | 0.0003 | [+0.0003, +0.0003] | 0.0000 | 0/8 | 0.0011 |
| 3 | 5.1250 | 223.7500 | 0.0554 | True | holds | 0.0014 | [+0.0013, +0.0016] | 0.0001 | 0/8 | 0.0063 |
| 4 | 8.6250 | 172.2500 | 0.0345 | False | not testable with these donors |  |  |  |  | 0.0120 |
| 5a | 14.3750 | 88.5000 | 0.0111 | False | not testable with these donors |  |  |  |  | 0.0314 |
| 5 | 30.2500 | 2.8750 | 0.0004 | False | not testable with these donors |  |  |  |  | 0.1891 |
| 6a | 45.7500 | 0.2500 | 0.0001 | False | not testable with these donors |  |  |  |  | 0.2629 |
| 6 | 63.6250 | 0.0000 | 0.0000 | False | not testable with these donors |  |  |  |  | 0.3794 |
| 7 | 108.6250 | 0.0000 | 0.0000 | False | not testable with these donors |  |  |  |  | 0.7780 |

tau_q = 0.1, stratum all, sub_rung_chain (m = 3): budget rung None
| rung | n_off | mean_contributing | clean_prefix_fraction | testable | label | d_hat | interval | half_width | draws_above_X | unconditional |
|---|---|---|---|---|---|---|---|---|---|---|
| S4 | 4.0000 | 225.0000 | 0.0256 | False | not testable with these donors | None | None | None | None | 0.0117 |
| S16 | 16.0000 | 43.0000 | 0.0049 | False | not testable with these donors | None | None | None | None | 0.0180 |
| S64 | 64.0000 | 0.0000 | 0.0000 | False | not testable with these donors | None | None | None | None | 0.1749 |

tau_q = 0.1, stratum Github, donor_chain (m = 9): budget rung 3
| rung | n_off | mean_contributing | clean_prefix_fraction | testable | label | d_hat | interval | half_width | draws_above_X | unconditional |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 0.1250 | 255.8750 | 0.9821 | True | holds | 0.0000 | [+0.0000, +0.0000] | 0.0000 | 0/8 | 0.0000 |
| 2 | 1.2500 | 220.0000 | 0.7000 | True | holds | 0.0004 | [+0.0004, +0.0005] | 0.0001 | 0/8 | 0.0013 |
| 3 | 5.1250 | 106.1250 | 0.0544 | True | holds | 0.0018 | [+0.0015, +0.0021] | 0.0003 | 0/8 | 0.0069 |
| 4 | 8.6250 | 86.3750 | 0.0380 | False | not testable with these donors |  |  |  |  | 0.0090 |
| 5a | 14.3750 | 38.8750 | 0.0100 | False | not testable with these donors |  |  |  |  | 0.0380 |
| 5 | 30.2500 | 1.1250 | 0.0004 | False | not testable with these donors |  |  |  |  | 0.1735 |
| 6a | 45.7500 | 0.1250 | 0.0001 | False | not testable with these donors |  |  |  |  | 0.2601 |
| 6 | 63.6250 | 0.0000 | 0.0000 | False | not testable with these donors |  |  |  |  | 0.3899 |
| 7 | 108.6250 | 0.0000 | 0.0000 | False | not testable with these donors |  |  |  |  | 0.8451 |

tau_q = 0.1, stratum Github, sub_rung_chain (m = 3): budget rung None
| rung | n_off | mean_contributing | clean_prefix_fraction | testable | label | d_hat | interval | half_width | draws_above_X | unconditional |
|---|---|---|---|---|---|---|---|---|---|---|
| S4 | 4.0000 | 125.0000 | 0.0232 | False | not testable with these donors | None | None | None | None | 0.0119 |
| S16 | 16.0000 | 13.0000 | 0.0044 | False | not testable with these donors | None | None | None | None | 0.0188 |
| S64 | 64.0000 | 0.0000 | 0.0000 | False | not testable with these donors | None | None | None | None | 0.2521 |

tau_q = 0.1, stratum other, donor_chain (m = 9): budget rung 3
| rung | n_off | mean_contributing | clean_prefix_fraction | testable | label | d_hat | interval | half_width | draws_above_X | unconditional |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 0.1250 | 255.8750 | 0.9692 | True | holds | 0.0000 | [+0.0000, +0.0000] | 0.0000 | 0/8 | 0.0000 |
| 2 | 1.2500 | 216.2500 | 0.6591 | True | holds | 0.0002 | [+0.0002, +0.0003] | 0.0000 | 0/8 | 0.0010 |
| 3 | 5.1250 | 117.6250 | 0.0563 | True | holds | 0.0012 | [+0.0011, +0.0014] | 0.0001 | 0/8 | 0.0057 |
| 4 | 8.6250 | 85.8750 | 0.0310 | False | not testable with these donors |  |  |  |  | 0.0151 |
| 5a | 14.3750 | 49.6250 | 0.0121 | False | not testable with these donors |  |  |  |  | 0.0247 |
| 5 | 30.2500 | 1.7500 | 0.0004 | False | not testable with these donors |  |  |  |  | 0.2048 |
| 6a | 45.7500 | 0.1250 | 0.0001 | False | not testable with these donors |  |  |  |  | 0.2656 |
| 6 | 63.6250 | 0.0000 | 0.0000 | False | not testable with these donors |  |  |  |  | 0.3689 |
| 7 | 108.6250 | 0.0000 | 0.0000 | False | not testable with these donors |  |  |  |  | 0.7109 |

tau_q = 0.1, stratum other, sub_rung_chain (m = 3): budget rung None
| rung | n_off | mean_contributing | clean_prefix_fraction | testable | label | d_hat | interval | half_width | draws_above_X | unconditional |
|---|---|---|---|---|---|---|---|---|---|---|
| S4 | 4.0000 | 100.0000 | 0.0280 | False | not testable with these donors | None | None | None | None | 0.0114 |
| S16 | 16.0000 | 30.0000 | 0.0053 | False | not testable with these donors | None | None | None | None | 0.0173 |
| S64 | 64.0000 | 0.0000 | 0.0000 | False | not testable with these donors | None | None | None | None | 0.0978 |

tau_q = 0.1, stratum ArXiv, donor_chain (m = 9): budget rung 1
| rung | n_off | mean_contributing | clean_prefix_fraction | testable | label | d_hat | interval | half_width | draws_above_X | unconditional |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 0.1250 | 64.0000 | 0.9975 | True | holds | 0.0000 | [-0.0000, +0.0000] | 0.0000 | 0/8 | 0.0000 |
| 2 | 1.2500 | 55.6250 | 0.6668 | False | not testable with these donors |  |  |  |  | 0.0006 |
| 3 | 5.1250 | 34.2500 | 0.0916 | False | not testable with these donors |  |  |  |  | 0.0043 |
| 4 | 8.6250 | 24.2500 | 0.0510 | False | not testable with these donors |  |  |  |  | 0.0267 |
| 5a | 14.3750 | 14.2500 | 0.0184 | False | not testable with these donors |  |  |  |  | 0.0319 |
| 5 | 30.2500 | 0.7500 | 0.0005 | False | not testable with these donors |  |  |  |  | 0.1825 |
| 6a | 45.7500 | 0.0000 | 0.0001 | False | not testable with these donors |  |  |  |  | 0.2522 |
| 6 | 63.6250 | 0.0000 | 0.0000 | False | not testable with these donors |  |  |  |  | 0.3290 |
| 7 | 108.6250 | 0.0000 | 0.0000 | False | not testable with these donors |  |  |  |  | 0.6787 |

tau_q = 0.1, stratum ArXiv, sub_rung_chain (m = 3): budget rung None
| rung | n_off | mean_contributing | clean_prefix_fraction | testable | label | d_hat | interval | half_width | draws_above_X | unconditional |
|---|---|---|---|---|---|---|---|---|---|---|
| S4 | 4.0000 | 35.0000 | 0.0681 | False | not testable with these donors | None | None | None | None | 0.0098 |
| S16 | 16.0000 | 8.0000 | 0.0051 | False | not testable with these donors | None | None | None | None | 0.0201 |
| S64 | 64.0000 | 0.0000 | 0.0000 | False | not testable with these donors | None | None | None | None | 0.0867 |

tau_q = 0.1, stratum Pile-CC, donor_chain (m = 9): budget rung None
| rung | n_off | mean_contributing | clean_prefix_fraction | testable | label | d_hat | interval | half_width | draws_above_X | unconditional |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 0.1250 | 63.8750 | 0.9710 | False | not testable with these donors | None | None | None | None | 0.0000 |
| 2 | 1.2500 | 53.8750 | 0.6577 | False | not testable with these donors | None | None | None | None | 0.0007 |
| 3 | 5.1250 | 28.7500 | 0.0502 | False | not testable with these donors | None | None | None | None | 0.0060 |
| 4 | 8.6250 | 21.2500 | 0.0211 | False | not testable with these donors | None | None | None | None | 0.0107 |
| 5a | 14.3750 | 13.2500 | 0.0097 | False | not testable with these donors | None | None | None | None | 0.0164 |
| 5 | 30.2500 | 0.2500 | 0.0003 | False | not testable with these donors | None | None | None | None | 0.2180 |
| 6a | 45.7500 | 0.0000 | 0.0001 | False | not testable with these donors | None | None | None | None | 0.2659 |
| 6 | 63.6250 | 0.0000 | 0.0000 | False | not testable with these donors | None | None | None | None | 0.3707 |
| 7 | 108.6250 | 0.0000 | 0.0000 | False | not testable with these donors | None | None | None | None | 0.6815 |

tau_q = 0.1, stratum Pile-CC, sub_rung_chain (m = 3): budget rung None
| rung | n_off | mean_contributing | clean_prefix_fraction | testable | label | d_hat | interval | half_width | draws_above_X | unconditional |
|---|---|---|---|---|---|---|---|---|---|---|
| S4 | 4.0000 | 22.0000 | 0.0149 | False | not testable with these donors | None | None | None | None | 0.0124 |
| S16 | 16.0000 | 10.0000 | 0.0065 | False | not testable with these donors | None | None | None | None | 0.0162 |
| S64 | 64.0000 | 0.0000 | 0.0000 | False | not testable with these donors | None | None | None | None | 0.0798 |

tau_q = 0.1, stratum StackExchange, donor_chain (m = 9): budget rung 1
| rung | n_off | mean_contributing | clean_prefix_fraction | testable | label | d_hat | interval | half_width | draws_above_X | unconditional |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 0.1250 | 64.0000 | 0.9511 | True | holds | 0.0000 | [+0.0000, +0.0000] | 0.0000 | 0/8 | 0.0000 |
| 2 | 1.2500 | 55.3750 | 0.6681 | False | not testable with these donors |  |  |  |  | 0.0010 |
| 3 | 5.1250 | 27.5000 | 0.0363 | False | not testable with these donors |  |  |  |  | 0.0064 |
| 4 | 8.6250 | 20.3750 | 0.0249 | False | not testable with these donors |  |  |  |  | 0.0112 |
| 5a | 14.3750 | 10.6250 | 0.0090 | False | not testable with these donors |  |  |  |  | 0.0307 |
| 5 | 30.2500 | 0.5000 | 0.0004 | False | not testable with these donors |  |  |  |  | 0.1772 |
| 6a | 45.7500 | 0.0000 | 0.0001 | False | not testable with these donors |  |  |  |  | 0.2431 |
| 6 | 63.6250 | 0.0000 | 0.0000 | False | not testable with these donors |  |  |  |  | 0.3539 |
| 7 | 108.6250 | 0.0000 | 0.0000 | False | not testable with these donors |  |  |  |  | 0.7111 |

tau_q = 0.1, stratum StackExchange, sub_rung_chain (m = 3): budget rung None
| rung | n_off | mean_contributing | clean_prefix_fraction | testable | label | d_hat | interval | half_width | draws_above_X | unconditional |
|---|---|---|---|---|---|---|---|---|---|---|
| S4 | 4.0000 | 25.0000 | 0.0166 | False | not testable with these donors | None | None | None | None | 0.0131 |
| S16 | 16.0000 | 5.0000 | 0.0043 | False | not testable with these donors | None | None | None | None | 0.0188 |
| S64 | 64.0000 | 0.0000 | 0.0000 | False | not testable with these donors | None | None | None | None | 0.1712 |

tau_q = 0.1, stratum Wikipedia (en), donor_chain (m = 9): budget rung 1
| rung | n_off | mean_contributing | clean_prefix_fraction | testable | label | d_hat | interval | half_width | draws_above_X | unconditional |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 0.1250 | 64.0000 | 0.9572 | True | holds | 0.0000 | [+0.0000, +0.0000] | 0.0000 | 0/8 | 0.0000 |
| 2 | 1.2500 | 51.3750 | 0.6437 | False | not testable with these donors |  |  |  |  | 0.0016 |
| 3 | 5.1250 | 27.1250 | 0.0472 | False | not testable with these donors |  |  |  |  | 0.0061 |
| 4 | 8.6250 | 20.0000 | 0.0270 | False | not testable with these donors |  |  |  |  | 0.0116 |
| 5a | 14.3750 | 11.5000 | 0.0114 | False | not testable with these donors |  |  |  |  | 0.0198 |
| 5 | 30.2500 | 0.2500 | 0.0005 | False | not testable with these donors |  |  |  |  | 0.2414 |
| 6a | 45.7500 | 0.1250 | 0.0002 | False | not testable with these donors |  |  |  |  | 0.3013 |
| 6 | 63.6250 | 0.0000 | 0.0000 | False | not testable with these donors |  |  |  |  | 0.4219 |
| 7 | 108.6250 | 0.0000 | 0.0000 | False | not testable with these donors |  |  |  |  | 0.7725 |

tau_q = 0.1, stratum Wikipedia (en), sub_rung_chain (m = 3): budget rung None
| rung | n_off | mean_contributing | clean_prefix_fraction | testable | label | d_hat | interval | half_width | draws_above_X | unconditional |
|---|---|---|---|---|---|---|---|---|---|---|
| S4 | 4.0000 | 18.0000 | 0.0123 | False | not testable with these donors | None | None | None | None | 0.0103 |
| S16 | 16.0000 | 7.0000 | 0.0054 | False | not testable with these donors | None | None | None | None | 0.0139 |
| S64 | 64.0000 | 0.0000 | 0.0000 | False | not testable with these donors | None | None | None | None | 0.0533 |

tau_q = 0, stratum all, donor_chain (m = 9): budget rung 2
| rung | n_off | mean_contributing | clean_prefix_fraction | testable | label | d_hat | interval | half_width | draws_above_X | unconditional |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 0.1250 | 511.6250 | 0.9740 | True | holds | 0.0000 | [+0.0000, +0.0000] | 0.0000 | 0/8 | 0.0000 |
| 2 | 1.2500 | 431.7500 | 0.6715 | True | holds | 0.0003 | [+0.0003, +0.0003] | 0.0000 | 0/8 | 0.0011 |
| 3 | 5.1250 | 205.2500 | 0.0475 | False | not testable with these donors |  |  |  |  | 0.0063 |
| 4 | 8.6250 | 158.2500 | 0.0294 | False | not testable with these donors |  |  |  |  | 0.0120 |
| 5a | 14.3750 | 77.5000 | 0.0095 | False | not testable with these donors |  |  |  |  | 0.0314 |
| 5 | 30.2500 | 1.8750 | 0.0003 | False | not testable with these donors |  |  |  |  | 0.1891 |
| 6a | 45.7500 | 0.1250 | 0.0001 | False | not testable with these donors |  |  |  |  | 0.2629 |
| 6 | 63.6250 | 0.0000 | 0.0000 | False | not testable with these donors |  |  |  |  | 0.3794 |
| 7 | 108.6250 | 0.0000 | 0.0000 | False | not testable with these donors |  |  |  |  | 0.7780 |

tau_q = 0, stratum all, sub_rung_chain (m = 3): budget rung None
| rung | n_off | mean_contributing | clean_prefix_fraction | testable | label | d_hat | interval | half_width | draws_above_X | unconditional |
|---|---|---|---|---|---|---|---|---|---|---|
| S4 | 4.0000 | 205.0000 | 0.0231 | False | not testable with these donors | None | None | None | None | 0.0117 |
| S16 | 16.0000 | 27.0000 | 0.0037 | False | not testable with these donors | None | None | None | None | 0.0180 |
| S64 | 64.0000 | 0.0000 | 0.0000 | False | not testable with these donors | None | None | None | None | 0.1749 |

tau_q = 0, stratum Github, donor_chain (m = 9): budget rung 2
| rung | n_off | mean_contributing | clean_prefix_fraction | testable | label | d_hat | interval | half_width | draws_above_X | unconditional |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 0.1250 | 255.8750 | 0.9799 | True | holds | 0.0000 | [+0.0000, +0.0000] | 0.0000 | 0/8 | 0.0000 |
| 2 | 1.2500 | 217.8750 | 0.6905 | True | holds | 0.0004 | [+0.0003, +0.0004] | 0.0001 | 0/8 | 0.0013 |
| 3 | 5.1250 | 96.2500 | 0.0451 | False | not testable with these donors |  |  |  |  | 0.0069 |
| 4 | 8.6250 | 79.2500 | 0.0319 | False | not testable with these donors |  |  |  |  | 0.0090 |
| 5a | 14.3750 | 33.0000 | 0.0084 | False | not testable with these donors |  |  |  |  | 0.0380 |
| 5 | 30.2500 | 1.0000 | 0.0003 | False | not testable with these donors |  |  |  |  | 0.1735 |
| 6a | 45.7500 | 0.0000 | 0.0001 | False | not testable with these donors |  |  |  |  | 0.2601 |
| 6 | 63.6250 | 0.0000 | 0.0000 | False | not testable with these donors |  |  |  |  | 0.3899 |
| 7 | 108.6250 | 0.0000 | 0.0000 | False | not testable with these donors |  |  |  |  | 0.8451 |

tau_q = 0, stratum Github, sub_rung_chain (m = 3): budget rung None
| rung | n_off | mean_contributing | clean_prefix_fraction | testable | label | d_hat | interval | half_width | draws_above_X | unconditional |
|---|---|---|---|---|---|---|---|---|---|---|
| S4 | 4.0000 | 113.0000 | 0.0212 | False | not testable with these donors | None | None | None | None | 0.0119 |
| S16 | 16.0000 | 10.0000 | 0.0034 | False | not testable with these donors | None | None | None | None | 0.0188 |
| S64 | 64.0000 | 0.0000 | 0.0000 | False | not testable with these donors | None | None | None | None | 0.2521 |

tau_q = 0, stratum other, donor_chain (m = 9): budget rung 3
| rung | n_off | mean_contributing | clean_prefix_fraction | testable | label | d_hat | interval | half_width | draws_above_X | unconditional |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 0.1250 | 255.7500 | 0.9681 | True | holds | 0.0000 | [+0.0000, +0.0000] | 0.0000 | 0/8 | 0.0000 |
| 2 | 1.2500 | 213.8750 | 0.6525 | True | holds | 0.0002 | [+0.0002, +0.0003] | 0.0000 | 0/8 | 0.0010 |
| 3 | 5.1250 | 109.0000 | 0.0500 | True | holds | 0.0012 | [+0.0010, +0.0013] | 0.0001 | 0/8 | 0.0057 |
| 4 | 8.6250 | 79.0000 | 0.0269 | False | not testable with these donors |  |  |  |  | 0.0151 |
| 5a | 14.3750 | 44.5000 | 0.0106 | False | not testable with these donors |  |  |  |  | 0.0247 |
| 5 | 30.2500 | 0.8750 | 0.0003 | False | not testable with these donors |  |  |  |  | 0.2048 |
| 6a | 45.7500 | 0.1250 | 0.0001 | False | not testable with these donors |  |  |  |  | 0.2656 |
| 6 | 63.6250 | 0.0000 | 0.0000 | False | not testable with these donors |  |  |  |  | 0.3689 |
| 7 | 108.6250 | 0.0000 | 0.0000 | False | not testable with these donors |  |  |  |  | 0.7109 |

tau_q = 0, stratum other, sub_rung_chain (m = 3): budget rung None
| rung | n_off | mean_contributing | clean_prefix_fraction | testable | label | d_hat | interval | half_width | draws_above_X | unconditional |
|---|---|---|---|---|---|---|---|---|---|---|
| S4 | 4.0000 | 92.0000 | 0.0250 | False | not testable with these donors | None | None | None | None | 0.0114 |
| S16 | 16.0000 | 17.0000 | 0.0040 | False | not testable with these donors | None | None | None | None | 0.0173 |
| S64 | 64.0000 | 0.0000 | 0.0000 | False | not testable with these donors | None | None | None | None | 0.0978 |

tau_q = 0, stratum ArXiv, donor_chain (m = 9): budget rung 1
| rung | n_off | mean_contributing | clean_prefix_fraction | testable | label | d_hat | interval | half_width | draws_above_X | unconditional |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 0.1250 | 64.0000 | 0.9975 | True | holds | 0.0000 | [-0.0000, +0.0000] | 0.0000 | 0/8 | 0.0000 |
| 2 | 1.2500 | 54.3750 | 0.6593 | False | not testable with these donors |  |  |  |  | 0.0006 |
| 3 | 5.1250 | 31.7500 | 0.0801 | False | not testable with these donors |  |  |  |  | 0.0043 |
| 4 | 8.6250 | 22.5000 | 0.0428 | False | not testable with these donors |  |  |  |  | 0.0267 |
| 5a | 14.3750 | 12.7500 | 0.0165 | False | not testable with these donors |  |  |  |  | 0.0319 |
| 5 | 30.2500 | 0.2500 | 0.0003 | False | not testable with these donors |  |  |  |  | 0.1825 |
| 6a | 45.7500 | 0.0000 | 0.0001 | False | not testable with these donors |  |  |  |  | 0.2522 |
| 6 | 63.6250 | 0.0000 | 0.0000 | False | not testable with these donors |  |  |  |  | 0.3290 |
| 7 | 108.6250 | 0.0000 | 0.0000 | False | not testable with these donors |  |  |  |  | 0.6787 |

tau_q = 0, stratum ArXiv, sub_rung_chain (m = 3): budget rung None
| rung | n_off | mean_contributing | clean_prefix_fraction | testable | label | d_hat | interval | half_width | draws_above_X | unconditional |
|---|---|---|---|---|---|---|---|---|---|---|
| S4 | 4.0000 | 33.0000 | 0.0583 | False | not testable with these donors | None | None | None | None | 0.0098 |
| S16 | 16.0000 | 6.0000 | 0.0041 | False | not testable with these donors | None | None | None | None | 0.0201 |
| S64 | 64.0000 | 0.0000 | 0.0000 | False | not testable with these donors | None | None | None | None | 0.0867 |

tau_q = 0, stratum Pile-CC, donor_chain (m = 9): budget rung None
| rung | n_off | mean_contributing | clean_prefix_fraction | testable | label | d_hat | interval | half_width | draws_above_X | unconditional |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 0.1250 | 63.8750 | 0.9710 | False | not testable with these donors | None | None | None | None | 0.0000 |
| 2 | 1.2500 | 53.3750 | 0.6484 | False | not testable with these donors | None | None | None | None | 0.0007 |
| 3 | 5.1250 | 27.0000 | 0.0457 | False | not testable with these donors | None | None | None | None | 0.0060 |
| 4 | 8.6250 | 19.7500 | 0.0188 | False | not testable with these donors | None | None | None | None | 0.0107 |
| 5a | 14.3750 | 12.1250 | 0.0089 | False | not testable with these donors | None | None | None | None | 0.0164 |
| 5 | 30.2500 | 0.2500 | 0.0003 | False | not testable with these donors | None | None | None | None | 0.2180 |
| 6a | 45.7500 | 0.0000 | 0.0001 | False | not testable with these donors | None | None | None | None | 0.2659 |
| 6 | 63.6250 | 0.0000 | 0.0000 | False | not testable with these donors | None | None | None | None | 0.3707 |
| 7 | 108.6250 | 0.0000 | 0.0000 | False | not testable with these donors | None | None | None | None | 0.6815 |

tau_q = 0, stratum Pile-CC, sub_rung_chain (m = 3): budget rung None
| rung | n_off | mean_contributing | clean_prefix_fraction | testable | label | d_hat | interval | half_width | draws_above_X | unconditional |
|---|---|---|---|---|---|---|---|---|---|---|
| S4 | 4.0000 | 21.0000 | 0.0143 | False | not testable with these donors | None | None | None | None | 0.0124 |
| S16 | 16.0000 | 6.0000 | 0.0054 | False | not testable with these donors | None | None | None | None | 0.0162 |
| S64 | 64.0000 | 0.0000 | 0.0000 | False | not testable with these donors | None | None | None | None | 0.0798 |

tau_q = 0, stratum StackExchange, donor_chain (m = 9): budget rung None
| rung | n_off | mean_contributing | clean_prefix_fraction | testable | label | d_hat | interval | half_width | draws_above_X | unconditional |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 0.1250 | 63.8750 | 0.9477 | False | not testable with these donors | None | None | None | None | 0.0000 |
| 2 | 1.2500 | 54.8750 | 0.6600 | False | not testable with these donors | None | None | None | None | 0.0010 |
| 3 | 5.1250 | 25.1250 | 0.0323 | False | not testable with these donors | None | None | None | None | 0.0064 |
| 4 | 8.6250 | 18.6250 | 0.0223 | False | not testable with these donors | None | None | None | None | 0.0112 |
| 5a | 14.3750 | 9.5000 | 0.0076 | False | not testable with these donors | None | None | None | None | 0.0307 |
| 5 | 30.2500 | 0.1250 | 0.0002 | False | not testable with these donors | None | None | None | None | 0.1772 |
| 6a | 45.7500 | 0.0000 | 0.0001 | False | not testable with these donors | None | None | None | None | 0.2431 |
| 6 | 63.6250 | 0.0000 | 0.0000 | False | not testable with these donors | None | None | None | None | 0.3539 |
| 7 | 108.6250 | 0.0000 | 0.0000 | False | not testable with these donors | None | None | None | None | 0.7111 |

tau_q = 0, stratum StackExchange, sub_rung_chain (m = 3): budget rung None
| rung | n_off | mean_contributing | clean_prefix_fraction | testable | label | d_hat | interval | half_width | draws_above_X | unconditional |
|---|---|---|---|---|---|---|---|---|---|---|
| S4 | 4.0000 | 24.0000 | 0.0163 | False | not testable with these donors | None | None | None | None | 0.0131 |
| S16 | 16.0000 | 2.0000 | 0.0033 | False | not testable with these donors | None | None | None | None | 0.0188 |
| S64 | 64.0000 | 0.0000 | 0.0000 | False | not testable with these donors | None | None | None | None | 0.1712 |

tau_q = 0, stratum Wikipedia (en), donor_chain (m = 9): budget rung 1
| rung | n_off | mean_contributing | clean_prefix_fraction | testable | label | d_hat | interval | half_width | draws_above_X | unconditional |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 0.1250 | 64.0000 | 0.9561 | True | holds | 0.0000 | [+0.0000, +0.0000] | 0.0000 | 0/8 | 0.0000 |
| 2 | 1.2500 | 51.2500 | 0.6425 | False | not testable with these donors |  |  |  |  | 0.0016 |
| 3 | 5.1250 | 25.1250 | 0.0421 | False | not testable with these donors |  |  |  |  | 0.0061 |
| 4 | 8.6250 | 18.1250 | 0.0237 | False | not testable with these donors |  |  |  |  | 0.0116 |
| 5a | 14.3750 | 10.1250 | 0.0095 | False | not testable with these donors |  |  |  |  | 0.0198 |
| 5 | 30.2500 | 0.2500 | 0.0004 | False | not testable with these donors |  |  |  |  | 0.2414 |
| 6a | 45.7500 | 0.1250 | 0.0002 | False | not testable with these donors |  |  |  |  | 0.3013 |
| 6 | 63.6250 | 0.0000 | 0.0000 | False | not testable with these donors |  |  |  |  | 0.4219 |
| 7 | 108.6250 | 0.0000 | 0.0000 | False | not testable with these donors |  |  |  |  | 0.7725 |

tau_q = 0, stratum Wikipedia (en), sub_rung_chain (m = 3): budget rung None
| rung | n_off | mean_contributing | clean_prefix_fraction | testable | label | d_hat | interval | half_width | draws_above_X | unconditional |
|---|---|---|---|---|---|---|---|---|---|---|
| S4 | 4.0000 | 14.0000 | 0.0110 | False | not testable with these donors | None | None | None | None | 0.0103 |
| S16 | 16.0000 | 3.0000 | 0.0034 | False | not testable with these donors | None | None | None | None | 0.0139 |
| S64 | 64.0000 | 0.0000 | 0.0000 | False | not testable with these donors | None | None | None | None | 0.0533 |

### `code_specific_hard/E_lab/D_code/tau0.5/ones/incl/ctl-none`
Positive control: erase exceeds its complement control on Github: pass (10 rungs judged); readability floor equals the pre-reads' table: True (168 of 168 rows matched)
The erased set against its complement control per rung (mean over draws; the control's pool is alive minus prose-named at this tau): rung 1: overlap 0 of 0 erased (0.000; control 0 from a pool of 776, of which 0 are the erased set's own); rung 2: overlap 0 of 5 erased (0.046; control 5 from a pool of 776, of which 5 are the erased set's own); rung 3: overlap 3 of 22 erased (0.155; control 22 from a pool of 776, of which 22 are the erased set's own); rung 4: overlap 6 of 32 erased (0.153; control 32 from a pool of 776, of which 32 are the erased set's own); rung 5a: overlap 10 of 49 erased (0.176; control 49 from a pool of 776, of which 49 are the erased set's own); rung 5: overlap 21 of 88 erased (0.232; control 88 from a pool of 776, of which 88 are the erased set's own); rung 6a: overlap 39 of 128 erased (0.306; control 128 from a pool of 776, of which 128 are the erased set's own); rung 6: overlap 70 of 176 erased (0.397; control 176 from a pool of 776, of which 176 are the erased set's own); rung 7: overlap 116 of 243 erased (0.477; control 243 from a pool of 776, of which 243 are the erased set's own); rung 8: overlap 222 of 379 erased (0.586; control 379 from a pool of 776, of which 379 are the erased set's own); rung S4: overlap 0 of 4 erased (0.000; control 4 from a pool of 776, of which 4 are the erased set's own); rung S16: overlap 3 of 16 erased (0.188; control 16 from a pool of 776, of which 16 are the erased set's own); rung S64: overlap 10 of 64 erased (0.156; control 64 from a pool of 776, of which 64 are the erased set's own)
tau_q = 0.1, stratum all, donor_chain (m = 9): budget rung 7
| rung | n_off | mean_contributing | clean_prefix_fraction | testable | label | d_hat | interval | half_width | draws_above_X | unconditional |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 0.3750 | 499.6250 | 0.9092 | True | holds | 0.0000 | [+0.0000, +0.0001] | 0.0000 | 0/8 | 0.0002 |
| 2 | 4.6250 | 441.6250 | 0.5747 | True | holds | 0.0004 | [+0.0004, +0.0005] | 0.0000 | 0/8 | 0.0041 |
| 3 | 21.6250 | 331.3750 | 0.3462 | True | holds | 0.0016 | [+0.0015, +0.0017] | 0.0001 | 0/8 | 0.0133 |
| 4 | 31.8750 | 330.2500 | 0.3224 | True | holds | 0.0023 | [+0.0021, +0.0025] | 0.0002 | 0/8 | 0.0207 |
| 5a | 49.0000 | 290.5000 | 0.2642 | True | holds | 0.0034 | [+0.0031, +0.0037] | 0.0003 | 0/8 | 0.0291 |
| 5 | 87.7500 | 268.2500 | 0.2057 | True | holds | 0.0055 | [+0.0051, +0.0061] | 0.0005 | 0/8 | 0.0384 |
| 6a | 127.6250 | 251.2500 | 0.1656 | True | holds | 0.0080 | [+0.0074, +0.0087] | 0.0006 | 0/8 | 0.0501 |
| 6 | 176.3750 | 236.1250 | 0.1290 | True | holds | 0.0111 | [+0.0103, +0.0121] | 0.0009 | 0/8 | 0.0603 |
| 7 | 242.7500 | 199.7500 | 0.0916 | True | holds | 0.0152 | [+0.0139, +0.0167] | 0.0014 | 0/8 | 0.0719 |

tau_q = 0.1, stratum all, sub_rung_chain (m = 3): budget rung S64
| rung | n_off | mean_contributing | clean_prefix_fraction | testable | label | d_hat | interval | half_width | draws_above_X | unconditional |
|---|---|---|---|---|---|---|---|---|---|---|
| S4 | 4.0000 | 385.0000 | 0.4580 | True | holds | 0.0008 | [+0.0007, +0.0010] | 0.0001 | 0/1 | 0.0031 |
| S16 | 16.0000 | 325.0000 | 0.3445 | True | holds | 0.0012 | [+0.0011, +0.0014] | 0.0001 | 0/1 | 0.0141 |
| S64 | 64.0000 | 285.0000 | 0.2442 | True | holds | 0.0040 | [+0.0037, +0.0044] | 0.0003 | 0/1 | 0.0365 |

tau_q = 0.1, stratum Github, donor_chain (m = 9): budget rung 5
| rung | n_off | mean_contributing | clean_prefix_fraction | testable | label | d_hat | interval | half_width | draws_above_X | unconditional |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 0.3750 | 245.8750 | 0.8591 | True | holds | 0.0001 | [+0.0000, +0.0001] | 0.0000 | 0/8 | 0.0004 |
| 2 | 4.6250 | 200.1250 | 0.3578 | True | holds | 0.0006 | [+0.0005, +0.0007] | 0.0001 | 0/8 | 0.0063 |
| 3 | 21.6250 | 114.3750 | 0.1175 | True | holds | 0.0023 | [+0.0020, +0.0026] | 0.0003 | 0/8 | 0.0195 |
| 4 | 31.8750 | 117.0000 | 0.1088 | True | holds | 0.0032 | [+0.0029, +0.0037] | 0.0004 | 0/8 | 0.0297 |
| 5a | 49.0000 | 90.0000 | 0.0791 | True | holds | 0.0048 | [+0.0042, +0.0057] | 0.0008 | 0/8 | 0.0421 |
| 5 | 87.7500 | 79.2500 | 0.0592 | True | holds | 0.0081 | [+0.0069, +0.0095] | 0.0013 | 0/8 | 0.0513 |
| 6a | 127.6250 | 69.1250 | 0.0470 | False | not testable with these donors |  |  |  |  | 0.0636 |
| 6 | 176.3750 | 62.7500 | 0.0353 | False | not testable with these donors |  |  |  |  | 0.0703 |
| 7 | 242.7500 | 46.7500 | 0.0205 | False | not testable with these donors |  |  |  |  | 0.0802 |

tau_q = 0.1, stratum Github, sub_rung_chain (m = 3): budget rung S64
| rung | n_off | mean_contributing | clean_prefix_fraction | testable | label | d_hat | interval | half_width | draws_above_X | unconditional |
|---|---|---|---|---|---|---|---|---|---|---|
| S4 | 4.0000 | 146.0000 | 0.1414 | True | holds | 0.0014 | [+0.0011, +0.0018] | 0.0003 | 0/1 | 0.0051 |
| S16 | 16.0000 | 109.0000 | 0.1162 | True | holds | 0.0018 | [+0.0015, +0.0022] | 0.0003 | 0/1 | 0.0239 |
| S64 | 64.0000 | 85.0000 | 0.0704 | True | holds | 0.0056 | [+0.0049, +0.0064] | 0.0008 | 0/1 | 0.0508 |

tau_q = 0.1, stratum other, donor_chain (m = 9): budget rung 7
| rung | n_off | mean_contributing | clean_prefix_fraction | testable | label | d_hat | interval | half_width | draws_above_X | unconditional |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 0.3750 | 253.7500 | 0.9593 | True | holds | 0.0000 | [+0.0000, +0.0000] | 0.0000 | 0/8 | 0.0001 |
| 2 | 4.6250 | 241.5000 | 0.7916 | True | holds | 0.0003 | [+0.0003, +0.0003] | 0.0000 | 0/8 | 0.0020 |
| 3 | 21.6250 | 217.0000 | 0.5749 | True | holds | 0.0012 | [+0.0012, +0.0013] | 0.0001 | 0/8 | 0.0071 |
| 4 | 31.8750 | 213.2500 | 0.5361 | True | holds | 0.0018 | [+0.0017, +0.0019] | 0.0001 | 0/8 | 0.0117 |
| 5a | 49.0000 | 200.5000 | 0.4492 | True | holds | 0.0027 | [+0.0025, +0.0029] | 0.0002 | 0/8 | 0.0162 |
| 5 | 87.7500 | 189.0000 | 0.3521 | True | holds | 0.0045 | [+0.0042, +0.0048] | 0.0003 | 0/8 | 0.0255 |
| 6a | 127.6250 | 182.1250 | 0.2842 | True | holds | 0.0068 | [+0.0063, +0.0073] | 0.0005 | 0/8 | 0.0366 |
| 6 | 176.3750 | 173.3750 | 0.2227 | True | holds | 0.0095 | [+0.0088, +0.0104] | 0.0008 | 0/8 | 0.0502 |
| 7 | 242.7500 | 153.0000 | 0.1628 | True | holds | 0.0131 | [+0.0121, +0.0142] | 0.0011 | 0/8 | 0.0636 |

tau_q = 0.1, stratum other, sub_rung_chain (m = 3): budget rung S64
| rung | n_off | mean_contributing | clean_prefix_fraction | testable | label | d_hat | interval | half_width | draws_above_X | unconditional |
|---|---|---|---|---|---|---|---|---|---|---|
| S4 | 4.0000 | 239.0000 | 0.7746 | True | holds | 0.0005 | [+0.0004, +0.0005] | 0.0001 | 0/1 | 0.0010 |
| S16 | 16.0000 | 216.0000 | 0.5728 | True | holds | 0.0009 | [+0.0009, +0.0010] | 0.0001 | 0/1 | 0.0043 |
| S64 | 64.0000 | 200.0000 | 0.4181 | True | holds | 0.0033 | [+0.0031, +0.0036] | 0.0002 | 0/1 | 0.0222 |

tau_q = 0.1, stratum ArXiv, donor_chain (m = 9): budget rung None
| rung | n_off | mean_contributing | clean_prefix_fraction | testable | label | d_hat | interval | half_width | draws_above_X | unconditional |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 0.3750 | 63.0000 | 0.9300 | False | not testable with these donors | None | None | None | None | 0.0003 |
| 2 | 4.6250 | 57.2500 | 0.7026 | False | not testable with these donors | None | None | None | None | 0.0032 |
| 3 | 21.6250 | 46.8750 | 0.3547 | False | not testable with these donors | None | None | None | None | 0.0133 |
| 4 | 31.8750 | 43.7500 | 0.2921 | False | not testable with these donors | None | None | None | None | 0.0239 |
| 5a | 49.0000 | 37.1250 | 0.1495 | False | not testable with these donors | None | None | None | None | 0.0323 |
| 5 | 87.7500 | 32.8750 | 0.0984 | False | not testable with these donors | None | None | None | None | 0.0574 |
| 6a | 127.6250 | 31.0000 | 0.0737 | False | not testable with these donors | None | None | None | None | 0.0863 |
| 6 | 176.3750 | 25.8750 | 0.0470 | False | not testable with these donors | None | None | None | None | 0.1275 |
| 7 | 242.7500 | 21.5000 | 0.0262 | False | not testable with these donors | None | None | None | None | 0.1627 |

tau_q = 0.1, stratum ArXiv, sub_rung_chain (m = 3): budget rung None
| rung | n_off | mean_contributing | clean_prefix_fraction | testable | label | d_hat | interval | half_width | draws_above_X | unconditional |
|---|---|---|---|---|---|---|---|---|---|---|
| S4 | 4.0000 | 61.0000 | 0.8192 | False | not testable with these donors | None | None | None | None | 0.0003 |
| S16 | 16.0000 | 46.0000 | 0.2499 | False | not testable with these donors | None | None | None | None | 0.0018 |
| S64 | 64.0000 | 39.0000 | 0.1731 | False | not testable with these donors | None | None | None | None | 0.0473 |

tau_q = 0.1, stratum Pile-CC, donor_chain (m = 9): budget rung 1
| rung | n_off | mean_contributing | clean_prefix_fraction | testable | label | d_hat | interval | half_width | draws_above_X | unconditional |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 0.3750 | 64.0000 | 1.0000 | True | holds | 0.0000 | [+0.0000, +0.0000] | 0.0000 | 0/8 | 0.0000 |
| 2 | 4.6250 | 63.7500 | 0.9763 | False | not testable with these donors |  |  |  |  | 0.0002 |
| 3 | 21.6250 | 63.0000 | 0.8773 | False | not testable with these donors |  |  |  |  | 0.0011 |
| 4 | 31.8750 | 62.5000 | 0.8380 | False | not testable with these donors |  |  |  |  | 0.0016 |
| 5a | 49.0000 | 61.3750 | 0.7654 | False | not testable with these donors |  |  |  |  | 0.0025 |
| 5 | 87.7500 | 59.2500 | 0.6343 | False | not testable with these donors |  |  |  |  | 0.0041 |
| 6a | 127.6250 | 58.5000 | 0.5362 | False | not testable with these donors |  |  |  |  | 0.0063 |
| 6 | 176.3750 | 57.0000 | 0.4334 | False | not testable with these donors |  |  |  |  | 0.0087 |
| 7 | 242.7500 | 53.6250 | 0.3346 | False | not testable with these donors |  |  |  |  | 0.0125 |

tau_q = 0.1, stratum Pile-CC, sub_rung_chain (m = 3): budget rung S16
| rung | n_off | mean_contributing | clean_prefix_fraction | testable | label | d_hat | interval | half_width | draws_above_X | unconditional |
|---|---|---|---|---|---|---|---|---|---|---|
| S4 | 4.0000 | 64.0000 | 0.9811 | True | holds | 0.0003 | [+0.0003, +0.0003] | 0.0000 | 0/1 | 0.0003 |
| S16 | 16.0000 | 64.0000 | 0.9216 | True | holds | 0.0008 | [+0.0008, +0.0008] | 0.0000 | 0/1 | 0.0008 |
| S64 | 64.0000 | 60.0000 | 0.6991 | False | not testable with these donors |  |  |  |  | 0.0031 |

tau_q = 0.1, stratum StackExchange, donor_chain (m = 9): budget rung None
| rung | n_off | mean_contributing | clean_prefix_fraction | testable | label | d_hat | interval | half_width | draws_above_X | unconditional |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 0.3750 | 62.7500 | 0.9086 | False | not testable with these donors | None | None | None | None | 0.0002 |
| 2 | 4.6250 | 56.5000 | 0.5028 | False | not testable with these donors | None | None | None | None | 0.0042 |
| 3 | 21.6250 | 44.1250 | 0.1994 | False | not testable with these donors | None | None | None | None | 0.0127 |
| 4 | 31.8750 | 44.0000 | 0.2038 | False | not testable with these donors | None | None | None | None | 0.0194 |
| 5a | 49.0000 | 40.0000 | 0.1542 | False | not testable with these donors | None | None | None | None | 0.0269 |
| 5 | 87.7500 | 37.0000 | 0.1156 | False | not testable with these donors | None | None | None | None | 0.0356 |
| 6a | 127.6250 | 33.8750 | 0.0847 | False | not testable with these donors | None | None | None | None | 0.0463 |
| 6 | 176.3750 | 32.6250 | 0.0760 | False | not testable with these donors | None | None | None | None | 0.0542 |
| 7 | 242.7500 | 27.7500 | 0.0527 | False | not testable with these donors | None | None | None | None | 0.0642 |

tau_q = 0.1, stratum StackExchange, sub_rung_chain (m = 3): budget rung None
| rung | n_off | mean_contributing | clean_prefix_fraction | testable | label | d_hat | interval | half_width | draws_above_X | unconditional |
|---|---|---|---|---|---|---|---|---|---|---|
| S4 | 4.0000 | 50.0000 | 0.3141 | False | not testable with these donors | None | None | None | None | 0.0029 |
| S16 | 16.0000 | 42.0000 | 0.1940 | False | not testable with these donors | None | None | None | None | 0.0135 |
| S64 | 64.0000 | 39.0000 | 0.1293 | False | not testable with these donors | None | None | None | None | 0.0344 |

tau_q = 0.1, stratum Wikipedia (en), donor_chain (m = 9): budget rung 2
| rung | n_off | mean_contributing | clean_prefix_fraction | testable | label | d_hat | interval | half_width | draws_above_X | unconditional |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 0.3750 | 64.0000 | 0.9988 | True | holds | 0.0000 | [+0.0000, +0.0000] | 0.0000 | 0/8 | 0.0000 |
| 2 | 4.6250 | 64.0000 | 0.9845 | True | holds | 0.0003 | [+0.0003, +0.0003] | 0.0000 | 0/8 | 0.0003 |
| 3 | 21.6250 | 63.0000 | 0.8680 | False | not testable with these donors |  |  |  |  | 0.0013 |
| 4 | 31.8750 | 63.0000 | 0.8104 | False | not testable with these donors |  |  |  |  | 0.0019 |
| 5a | 49.0000 | 62.0000 | 0.7278 | False | not testable with these donors |  |  |  |  | 0.0029 |
| 5 | 87.7500 | 59.8750 | 0.5602 | False | not testable with these donors |  |  |  |  | 0.0049 |
| 6a | 127.6250 | 58.7500 | 0.4424 | False | not testable with these donors |  |  |  |  | 0.0075 |
| 6 | 176.3750 | 57.8750 | 0.3344 | False | not testable with these donors |  |  |  |  | 0.0104 |
| 7 | 242.7500 | 50.1250 | 0.2378 | False | not testable with these donors |  |  |  |  | 0.0150 |

tau_q = 0.1, stratum Wikipedia (en), sub_rung_chain (m = 3): budget rung S16
| rung | n_off | mean_contributing | clean_prefix_fraction | testable | label | d_hat | interval | half_width | draws_above_X | unconditional |
|---|---|---|---|---|---|---|---|---|---|---|
| S4 | 4.0000 | 64.0000 | 0.9838 | True | holds | 0.0004 | [+0.0004, +0.0005] | 0.0000 | 0/1 | 0.0004 |
| S16 | 16.0000 | 64.0000 | 0.9256 | True | holds | 0.0010 | [+0.0009, +0.0010] | 0.0001 | 0/1 | 0.0010 |
| S64 | 64.0000 | 62.0000 | 0.6709 | False | not testable with these donors |  |  |  |  | 0.0037 |

tau_q = 0, stratum all, donor_chain (m = 9): budget rung 5
| rung | n_off | mean_contributing | clean_prefix_fraction | testable | label | d_hat | interval | half_width | draws_above_X | unconditional |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 0.3750 | 498.5000 | 0.8985 | True | holds | 0.0000 | [+0.0000, +0.0001] | 0.0000 | 0/8 | 0.0002 |
| 2 | 4.6250 | 433.3750 | 0.5087 | True | holds | 0.0004 | [+0.0004, +0.0004] | 0.0000 | 0/8 | 0.0041 |
| 3 | 21.6250 | 312.1250 | 0.1980 | True | holds | 0.0016 | [+0.0014, +0.0017] | 0.0001 | 0/8 | 0.0133 |
| 4 | 31.8750 | 303.5000 | 0.1788 | True | holds | 0.0022 | [+0.0021, +0.0024] | 0.0002 | 0/8 | 0.0207 |
| 5a | 49.0000 | 258.5000 | 0.1102 | True | holds | 0.0033 | [+0.0030, +0.0036] | 0.0003 | 0/8 | 0.0291 |
| 5 | 87.7500 | 222.6250 | 0.0624 | True | holds | 0.0052 | [+0.0048, +0.0057] | 0.0004 | 0/8 | 0.0384 |
| 6a | 127.6250 | 198.1250 | 0.0401 | False | not testable with these donors |  |  |  |  | 0.0501 |
| 6 | 176.3750 | 173.8750 | 0.0277 | False | not testable with these donors |  |  |  |  | 0.0603 |
| 7 | 242.7500 | 122.8750 | 0.0169 | False | not testable with these donors |  |  |  |  | 0.0719 |

tau_q = 0, stratum all, sub_rung_chain (m = 3): budget rung S64
| rung | n_off | mean_contributing | clean_prefix_fraction | testable | label | d_hat | interval | half_width | draws_above_X | unconditional |
|---|---|---|---|---|---|---|---|---|---|---|
| S4 | 4.0000 | 368.0000 | 0.4020 | True | holds | 0.0008 | [+0.0006, +0.0009] | 0.0001 | 0/1 | 0.0031 |
| S16 | 16.0000 | 307.0000 | 0.2245 | True | holds | 0.0012 | [+0.0011, +0.0013] | 0.0001 | 0/1 | 0.0141 |
| S64 | 64.0000 | 254.0000 | 0.0783 | True | holds | 0.0039 | [+0.0036, +0.0043] | 0.0003 | 0/1 | 0.0365 |

tau_q = 0, stratum Github, donor_chain (m = 9): budget rung 4
| rung | n_off | mean_contributing | clean_prefix_fraction | testable | label | d_hat | interval | half_width | draws_above_X | unconditional |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 0.3750 | 245.0000 | 0.8502 | True | holds | 0.0001 | [+0.0000, +0.0001] | 0.0000 | 0/8 | 0.0004 |
| 2 | 4.6250 | 194.5000 | 0.3240 | True | holds | 0.0006 | [+0.0005, +0.0006] | 0.0001 | 0/8 | 0.0063 |
| 3 | 21.6250 | 102.8750 | 0.0736 | True | holds | 0.0022 | [+0.0019, +0.0025] | 0.0003 | 0/8 | 0.0195 |
| 4 | 31.8750 | 101.3750 | 0.0670 | True | holds | 0.0032 | [+0.0028, +0.0038] | 0.0005 | 0/8 | 0.0297 |
| 5a | 49.0000 | 73.1250 | 0.0408 | False | not testable with these donors |  |  |  |  | 0.0421 |
| 5 | 87.7500 | 55.8750 | 0.0228 | False | not testable with these donors |  |  |  |  | 0.0513 |
| 6a | 127.6250 | 44.7500 | 0.0153 | False | not testable with these donors |  |  |  |  | 0.0636 |
| 6 | 176.3750 | 37.0000 | 0.0099 | False | not testable with these donors |  |  |  |  | 0.0703 |
| 7 | 242.7500 | 20.2500 | 0.0049 | False | not testable with these donors |  |  |  |  | 0.0802 |

tau_q = 0, stratum Github, sub_rung_chain (m = 3): budget rung S16
| rung | n_off | mean_contributing | clean_prefix_fraction | testable | label | d_hat | interval | half_width | draws_above_X | unconditional |
|---|---|---|---|---|---|---|---|---|---|---|
| S4 | 4.0000 | 133.0000 | 0.1222 | True | holds | 0.0013 | [+0.0010, +0.0016] | 0.0003 | 0/1 | 0.0051 |
| S16 | 16.0000 | 97.0000 | 0.0777 | True | holds | 0.0017 | [+0.0014, +0.0020] | 0.0003 | 0/1 | 0.0239 |
| S64 | 64.0000 | 71.0000 | 0.0328 | False | not testable with these donors |  |  |  |  | 0.0508 |

tau_q = 0, stratum other, donor_chain (m = 9): budget rung 6a
| rung | n_off | mean_contributing | clean_prefix_fraction | testable | label | d_hat | interval | half_width | draws_above_X | unconditional |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 0.3750 | 253.5000 | 0.9468 | True | holds | 0.0000 | [+0.0000, +0.0000] | 0.0000 | 0/8 | 0.0001 |
| 2 | 4.6250 | 238.8750 | 0.6934 | True | holds | 0.0003 | [+0.0003, +0.0003] | 0.0000 | 0/8 | 0.0020 |
| 3 | 21.6250 | 209.2500 | 0.3225 | True | holds | 0.0012 | [+0.0011, +0.0013] | 0.0001 | 0/8 | 0.0071 |
| 4 | 31.8750 | 202.1250 | 0.2906 | True | holds | 0.0018 | [+0.0016, +0.0019] | 0.0001 | 0/8 | 0.0117 |
| 5a | 49.0000 | 185.3750 | 0.1795 | True | holds | 0.0027 | [+0.0025, +0.0029] | 0.0002 | 0/8 | 0.0162 |
| 5 | 87.7500 | 166.7500 | 0.1020 | True | holds | 0.0045 | [+0.0042, +0.0049] | 0.0004 | 0/8 | 0.0255 |
| 6a | 127.6250 | 153.3750 | 0.0649 | True | holds | 0.0071 | [+0.0064, +0.0078] | 0.0007 | 0/8 | 0.0366 |
| 6 | 176.3750 | 136.8750 | 0.0456 | False | not testable with these donors |  |  |  |  | 0.0502 |
| 7 | 242.7500 | 102.6250 | 0.0290 | False | not testable with these donors |  |  |  |  | 0.0636 |

tau_q = 0, stratum other, sub_rung_chain (m = 3): budget rung S64
| rung | n_off | mean_contributing | clean_prefix_fraction | testable | label | d_hat | interval | half_width | draws_above_X | unconditional |
|---|---|---|---|---|---|---|---|---|---|---|
| S4 | 4.0000 | 235.0000 | 0.6819 | True | holds | 0.0005 | [+0.0004, +0.0005] | 0.0001 | 0/1 | 0.0010 |
| S16 | 16.0000 | 210.0000 | 0.3713 | True | holds | 0.0009 | [+0.0008, +0.0010] | 0.0001 | 0/1 | 0.0043 |
| S64 | 64.0000 | 183.0000 | 0.1237 | True | holds | 0.0033 | [+0.0031, +0.0036] | 0.0002 | 0/1 | 0.0222 |

tau_q = 0, stratum ArXiv, donor_chain (m = 9): budget rung None
| rung | n_off | mean_contributing | clean_prefix_fraction | testable | label | d_hat | interval | half_width | draws_above_X | unconditional |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 0.3750 | 62.7500 | 0.9171 | False | not testable with these donors | None | None | None | None | 0.0003 |
| 2 | 4.6250 | 56.6250 | 0.6349 | False | not testable with these donors | None | None | None | None | 0.0032 |
| 3 | 21.6250 | 44.3750 | 0.2546 | False | not testable with these donors | None | None | None | None | 0.0133 |
| 4 | 31.8750 | 40.6250 | 0.2039 | False | not testable with these donors | None | None | None | None | 0.0239 |
| 5a | 49.0000 | 33.0000 | 0.0930 | False | not testable with these donors | None | None | None | None | 0.0323 |
| 5 | 87.7500 | 28.1250 | 0.0565 | False | not testable with these donors | None | None | None | None | 0.0574 |
| 6a | 127.6250 | 25.5000 | 0.0366 | False | not testable with these donors | None | None | None | None | 0.0863 |
| 6 | 176.3750 | 20.0000 | 0.0230 | False | not testable with these donors | None | None | None | None | 0.1275 |
| 7 | 242.7500 | 13.8750 | 0.0125 | False | not testable with these donors | None | None | None | None | 0.1627 |

tau_q = 0, stratum ArXiv, sub_rung_chain (m = 3): budget rung None
| rung | n_off | mean_contributing | clean_prefix_fraction | testable | label | d_hat | interval | half_width | draws_above_X | unconditional |
|---|---|---|---|---|---|---|---|---|---|---|
| S4 | 4.0000 | 59.0000 | 0.7590 | False | not testable with these donors | None | None | None | None | 0.0003 |
| S16 | 16.0000 | 44.0000 | 0.1762 | False | not testable with these donors | None | None | None | None | 0.0018 |
| S64 | 64.0000 | 34.0000 | 0.0883 | False | not testable with these donors | None | None | None | None | 0.0473 |

tau_q = 0, stratum Pile-CC, donor_chain (m = 9): budget rung 1
| rung | n_off | mean_contributing | clean_prefix_fraction | testable | label | d_hat | interval | half_width | draws_above_X | unconditional |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 0.3750 | 64.0000 | 0.9875 | True | holds | 0.0000 | [+0.0000, +0.0000] | 0.0000 | 0/8 | 0.0000 |
| 2 | 4.6250 | 63.0000 | 0.8473 | False | not testable with these donors |  |  |  |  | 0.0002 |
| 3 | 21.6250 | 60.6250 | 0.4509 | False | not testable with these donors |  |  |  |  | 0.0011 |
| 4 | 31.8750 | 59.1250 | 0.4167 | False | not testable with these donors |  |  |  |  | 0.0016 |
| 5a | 49.0000 | 56.0000 | 0.2664 | False | not testable with these donors |  |  |  |  | 0.0025 |
| 5 | 87.7500 | 50.8750 | 0.1494 | False | not testable with these donors |  |  |  |  | 0.0041 |
| 6a | 127.6250 | 47.0000 | 0.0965 | False | not testable with these donors |  |  |  |  | 0.0063 |
| 6 | 176.3750 | 42.0000 | 0.0688 | False | not testable with these donors |  |  |  |  | 0.0087 |
| 7 | 242.7500 | 31.7500 | 0.0451 | False | not testable with these donors |  |  |  |  | 0.0125 |

tau_q = 0, stratum Pile-CC, sub_rung_chain (m = 3): budget rung None
| rung | n_off | mean_contributing | clean_prefix_fraction | testable | label | d_hat | interval | half_width | draws_above_X | unconditional |
|---|---|---|---|---|---|---|---|---|---|---|
| S4 | 4.0000 | 63.0000 | 0.8510 | False | not testable with these donors | None | None | None | None | 0.0003 |
| S16 | 16.0000 | 62.0000 | 0.6203 | False | not testable with these donors | None | None | None | None | 0.0008 |
| S64 | 64.0000 | 54.0000 | 0.1630 | False | not testable with these donors | None | None | None | None | 0.0031 |

tau_q = 0, stratum StackExchange, donor_chain (m = 9): budget rung None
| rung | n_off | mean_contributing | clean_prefix_fraction | testable | label | d_hat | interval | half_width | draws_above_X | unconditional |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 0.3750 | 62.7500 | 0.8943 | False | not testable with these donors | None | None | None | None | 0.0002 |
| 2 | 4.6250 | 55.2500 | 0.4530 | False | not testable with these donors | None | None | None | None | 0.0042 |
| 3 | 21.6250 | 41.7500 | 0.1402 | False | not testable with these donors | None | None | None | None | 0.0127 |
| 4 | 31.8750 | 40.8750 | 0.1403 | False | not testable with these donors | None | None | None | None | 0.0194 |
| 5a | 49.0000 | 37.1250 | 0.0949 | False | not testable with these donors | None | None | None | None | 0.0269 |
| 5 | 87.7500 | 32.6250 | 0.0612 | False | not testable with these donors | None | None | None | None | 0.0356 |
| 6a | 127.6250 | 28.3750 | 0.0393 | False | not testable with these donors | None | None | None | None | 0.0463 |
| 6 | 176.3750 | 25.2500 | 0.0315 | False | not testable with these donors | None | None | None | None | 0.0542 |
| 7 | 242.7500 | 18.1250 | 0.0201 | False | not testable with these donors | None | None | None | None | 0.0642 |

tau_q = 0, stratum StackExchange, sub_rung_chain (m = 3): budget rung None
| rung | n_off | mean_contributing | clean_prefix_fraction | testable | label | d_hat | interval | half_width | draws_above_X | unconditional |
|---|---|---|---|---|---|---|---|---|---|---|
| S4 | 4.0000 | 49.0000 | 0.2839 | False | not testable with these donors | None | None | None | None | 0.0029 |
| S16 | 16.0000 | 40.0000 | 0.1573 | False | not testable with these donors | None | None | None | None | 0.0135 |
| S64 | 64.0000 | 35.0000 | 0.0635 | False | not testable with these donors | None | None | None | None | 0.0344 |

tau_q = 0, stratum Wikipedia (en), donor_chain (m = 9): budget rung 2
| rung | n_off | mean_contributing | clean_prefix_fraction | testable | label | d_hat | interval | half_width | draws_above_X | unconditional |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 0.3750 | 64.0000 | 0.9883 | True | holds | 0.0000 | [+0.0000, +0.0000] | 0.0000 | 0/8 | 0.0000 |
| 2 | 4.6250 | 64.0000 | 0.8383 | True | holds | 0.0003 | [+0.0002, +0.0003] | 0.0000 | 0/8 | 0.0003 |
| 3 | 21.6250 | 62.5000 | 0.4442 | False | not testable with these donors |  |  |  |  | 0.0013 |
| 4 | 31.8750 | 61.5000 | 0.4015 | False | not testable with these donors |  |  |  |  | 0.0019 |
| 5a | 49.0000 | 59.2500 | 0.2638 | False | not testable with these donors |  |  |  |  | 0.0029 |
| 5 | 87.7500 | 55.1250 | 0.1409 | False | not testable with these donors |  |  |  |  | 0.0049 |
| 6a | 127.6250 | 52.5000 | 0.0871 | False | not testable with these donors |  |  |  |  | 0.0075 |
| 6 | 176.3750 | 49.6250 | 0.0590 | False | not testable with these donors |  |  |  |  | 0.0104 |
| 7 | 242.7500 | 38.8750 | 0.0383 | False | not testable with these donors |  |  |  |  | 0.0150 |

tau_q = 0, stratum Wikipedia (en), sub_rung_chain (m = 3): budget rung S16
| rung | n_off | mean_contributing | clean_prefix_fraction | testable | label | d_hat | interval | half_width | draws_above_X | unconditional |
|---|---|---|---|---|---|---|---|---|---|---|
| S4 | 4.0000 | 64.0000 | 0.8336 | True | holds | 0.0004 | [+0.0004, +0.0005] | 0.0001 | 0/1 | 0.0004 |
| S16 | 16.0000 | 64.0000 | 0.5312 | True | holds | 0.0010 | [+0.0009, +0.0011] | 0.0001 | 0/1 | 0.0010 |
| S64 | 64.0000 | 60.0000 | 0.1801 | False | not testable with these donors |  |  |  |  | 0.0037 |

### `code_specific_hard/E_lab/D_code/tau0.5/ones/incl/ctl-complement`
Positive control: does not apply; readability floor equals the pre-reads' table: True (168 of 168 rows matched)
tau_q = 0.1, stratum all, donor_chain (m = 9): budget rung 7
| rung | n_off | mean_contributing | clean_prefix_fraction | testable | label | d_hat | interval | half_width | draws_above_X | unconditional |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 0.3750 | 509.8750 | 0.9535 | True | holds | 0.0000 | [+0.0000, +0.0000] | 0.0000 | 0/8 | 0.0001 |
| 2 | 4.6250 | 486.3750 | 0.7650 | True | holds | 0.0003 | [+0.0003, +0.0004] | 0.0000 | 0/8 | 0.0018 |
| 3 | 21.6250 | 420.6250 | 0.3771 | True | holds | 0.0013 | [+0.0013, +0.0014] | 0.0001 | 0/8 | 0.0057 |
| 4 | 31.8750 | 395.8750 | 0.3641 | True | holds | 0.0019 | [+0.0018, +0.0021] | 0.0001 | 0/8 | 0.0115 |
| 5a | 49.0000 | 370.3750 | 0.2943 | True | holds | 0.0030 | [+0.0028, +0.0032] | 0.0002 | 0/8 | 0.0165 |
| 5 | 87.7500 | 327.8750 | 0.2279 | True | holds | 0.0052 | [+0.0049, +0.0057] | 0.0004 | 0/8 | 0.0225 |
| 6a | 127.6250 | 294.7500 | 0.1902 | True | holds | 0.0076 | [+0.0070, +0.0082] | 0.0006 | 0/8 | 0.0304 |
| 6 | 176.3750 | 260.1250 | 0.1477 | True | holds | 0.0105 | [+0.0098, +0.0114] | 0.0008 | 0/8 | 0.0387 |
| 7 | 242.7500 | 233.7500 | 0.1193 | True | holds | 0.0148 | [+0.0137, +0.0161] | 0.0012 | 0/8 | 0.0478 |

tau_q = 0.1, stratum all, sub_rung_chain (m = 3): budget rung S64
| rung | n_off | mean_contributing | clean_prefix_fraction | testable | label | d_hat | interval | half_width | draws_above_X | unconditional |
|---|---|---|---|---|---|---|---|---|---|---|
| S4 | 4.0000 | 491.0000 | 0.7280 | True | holds | 0.0002 | [+0.0002, +0.0003] | 0.0000 | 0/1 | 0.0004 |
| S16 | 16.0000 | 437.0000 | 0.3464 | True | holds | 0.0012 | [+0.0011, +0.0013] | 0.0001 | 0/1 | 0.0038 |
| S64 | 64.0000 | 368.0000 | 0.2506 | True | holds | 0.0032 | [+0.0030, +0.0034] | 0.0002 | 0/1 | 0.0202 |

tau_q = 0.1, stratum Github, donor_chain (m = 9): budget rung 6a
| rung | n_off | mean_contributing | clean_prefix_fraction | testable | label | d_hat | interval | half_width | draws_above_X | unconditional |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 0.3750 | 255.0000 | 0.9487 | True | holds | 0.0000 | [+0.0000, +0.0000] | 0.0000 | 0/8 | 0.0000 |
| 2 | 4.6250 | 242.7500 | 0.7308 | True | holds | 0.0004 | [+0.0004, +0.0005] | 0.0001 | 0/8 | 0.0024 |
| 3 | 21.6250 | 200.8750 | 0.2106 | True | holds | 0.0017 | [+0.0015, +0.0018] | 0.0001 | 0/8 | 0.0068 |
| 4 | 31.8750 | 183.3750 | 0.2089 | True | holds | 0.0025 | [+0.0023, +0.0027] | 0.0002 | 0/8 | 0.0157 |
| 5a | 49.0000 | 163.6250 | 0.1327 | True | holds | 0.0039 | [+0.0035, +0.0043] | 0.0004 | 0/8 | 0.0225 |
| 5 | 87.7500 | 135.0000 | 0.0927 | True | holds | 0.0069 | [+0.0061, +0.0078] | 0.0009 | 0/8 | 0.0275 |
| 6a | 127.6250 | 111.5000 | 0.0672 | True | holds | 0.0100 | [+0.0089, +0.0113] | 0.0012 | 0/8 | 0.0370 |
| 6 | 176.3750 | 89.7500 | 0.0449 | False | not testable with these donors |  |  |  |  | 0.0443 |
| 7 | 242.7500 | 74.7500 | 0.0327 | False | not testable with these donors |  |  |  |  | 0.0528 |

tau_q = 0.1, stratum Github, sub_rung_chain (m = 3): budget rung S64
| rung | n_off | mean_contributing | clean_prefix_fraction | testable | label | d_hat | interval | half_width | draws_above_X | unconditional |
|---|---|---|---|---|---|---|---|---|---|---|
| S4 | 4.0000 | 249.0000 | 0.7807 | True | holds | 0.0002 | [+0.0002, +0.0003] | 0.0000 | 0/1 | 0.0004 |
| S16 | 16.0000 | 220.0000 | 0.1902 | True | holds | 0.0015 | [+0.0013, +0.0017] | 0.0002 | 0/1 | 0.0037 |
| S64 | 64.0000 | 161.0000 | 0.1025 | True | holds | 0.0040 | [+0.0036, +0.0044] | 0.0004 | 0/1 | 0.0258 |

tau_q = 0.1, stratum other, donor_chain (m = 9): budget rung 7
| rung | n_off | mean_contributing | clean_prefix_fraction | testable | label | d_hat | interval | half_width | draws_above_X | unconditional |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 0.3750 | 254.8750 | 0.9584 | True | holds | 0.0000 | [+0.0000, +0.0000] | 0.0000 | 0/8 | 0.0001 |
| 2 | 4.6250 | 243.6250 | 0.7993 | True | holds | 0.0003 | [+0.0002, +0.0003] | 0.0000 | 0/8 | 0.0012 |
| 3 | 21.6250 | 219.7500 | 0.5436 | True | holds | 0.0010 | [+0.0010, +0.0011] | 0.0001 | 0/8 | 0.0047 |
| 4 | 31.8750 | 212.5000 | 0.5194 | True | holds | 0.0015 | [+0.0014, +0.0016] | 0.0001 | 0/8 | 0.0073 |
| 5a | 49.0000 | 206.7500 | 0.4559 | True | holds | 0.0023 | [+0.0022, +0.0025] | 0.0002 | 0/8 | 0.0104 |
| 5 | 87.7500 | 192.8750 | 0.3631 | True | holds | 0.0041 | [+0.0038, +0.0044] | 0.0003 | 0/8 | 0.0175 |
| 6a | 127.6250 | 183.2500 | 0.3132 | True | holds | 0.0061 | [+0.0057, +0.0066] | 0.0005 | 0/8 | 0.0239 |
| 6 | 176.3750 | 170.3750 | 0.2505 | True | holds | 0.0086 | [+0.0080, +0.0094] | 0.0007 | 0/8 | 0.0331 |
| 7 | 242.7500 | 159.0000 | 0.2060 | True | holds | 0.0124 | [+0.0115, +0.0135] | 0.0010 | 0/8 | 0.0429 |

tau_q = 0.1, stratum other, sub_rung_chain (m = 3): budget rung S64
| rung | n_off | mean_contributing | clean_prefix_fraction | testable | label | d_hat | interval | half_width | draws_above_X | unconditional |
|---|---|---|---|---|---|---|---|---|---|---|
| S4 | 4.0000 | 242.0000 | 0.6753 | True | holds | 0.0002 | [+0.0002, +0.0003] | 0.0000 | 0/1 | 0.0004 |
| S16 | 16.0000 | 217.0000 | 0.5027 | True | holds | 0.0008 | [+0.0008, +0.0009] | 0.0001 | 0/1 | 0.0038 |
| S64 | 64.0000 | 207.0000 | 0.3988 | True | holds | 0.0026 | [+0.0025, +0.0028] | 0.0002 | 0/1 | 0.0147 |

tau_q = 0.1, stratum ArXiv, donor_chain (m = 9): budget rung None
| rung | n_off | mean_contributing | clean_prefix_fraction | testable | label | d_hat | interval | half_width | draws_above_X | unconditional |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 0.3750 | 62.8750 | 0.8789 | False | not testable with these donors | None | None | None | None | 0.0003 |
| 2 | 4.6250 | 53.5000 | 0.5147 | False | not testable with these donors | None | None | None | None | 0.0026 |
| 3 | 21.6250 | 38.2500 | 0.1536 | False | not testable with these donors | None | None | None | None | 0.0114 |
| 4 | 31.8750 | 35.3750 | 0.1138 | False | not testable with these donors | None | None | None | None | 0.0151 |
| 5a | 49.0000 | 32.6250 | 0.0865 | False | not testable with these donors | None | None | None | None | 0.0217 |
| 5 | 87.7500 | 28.5000 | 0.0567 | False | not testable with these donors | None | None | None | None | 0.0409 |
| 6a | 127.6250 | 26.1250 | 0.0454 | False | not testable with these donors | None | None | None | None | 0.0551 |
| 6 | 176.3750 | 24.1250 | 0.0326 | False | not testable with these donors | None | None | None | None | 0.0784 |
| 7 | 242.7500 | 22.8750 | 0.0296 | False | not testable with these donors | None | None | None | None | 0.0983 |

tau_q = 0.1, stratum ArXiv, sub_rung_chain (m = 3): budget rung None
| rung | n_off | mean_contributing | clean_prefix_fraction | testable | label | d_hat | interval | half_width | draws_above_X | unconditional |
|---|---|---|---|---|---|---|---|---|---|---|
| S4 | 4.0000 | 54.0000 | 0.3487 | False | not testable with these donors | None | None | None | None | 0.0005 |
| S16 | 16.0000 | 38.0000 | 0.1787 | False | not testable with these donors | None | None | None | None | 0.0106 |
| S64 | 64.0000 | 34.0000 | 0.1299 | False | not testable with these donors | None | None | None | None | 0.0337 |

tau_q = 0.1, stratum Pile-CC, donor_chain (m = 9): budget rung 2
| rung | n_off | mean_contributing | clean_prefix_fraction | testable | label | d_hat | interval | half_width | draws_above_X | unconditional |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 0.3750 | 64.0000 | 0.9981 | True | holds | 0.0000 | [+0.0000, +0.0000] | 0.0000 | 0/8 | 0.0000 |
| 2 | 4.6250 | 64.0000 | 0.9822 | True | holds | 0.0002 | [+0.0002, +0.0002] | 0.0000 | 0/8 | 0.0002 |
| 3 | 21.6250 | 63.2500 | 0.9034 | False | not testable with these donors |  |  |  |  | 0.0009 |
| 4 | 31.8750 | 62.1250 | 0.8618 | False | not testable with these donors |  |  |  |  | 0.0013 |
| 5a | 49.0000 | 62.1250 | 0.8115 | False | not testable with these donors |  |  |  |  | 0.0020 |
| 5 | 87.7500 | 59.6250 | 0.6891 | False | not testable with these donors |  |  |  |  | 0.0036 |
| 6a | 127.6250 | 58.0000 | 0.6081 | False | not testable with these donors |  |  |  |  | 0.0055 |
| 6 | 176.3750 | 55.0000 | 0.4979 | False | not testable with these donors |  |  |  |  | 0.0078 |
| 7 | 242.7500 | 52.7500 | 0.4155 | False | not testable with these donors |  |  |  |  | 0.0113 |

tau_q = 0.1, stratum Pile-CC, sub_rung_chain (m = 3): budget rung S4
| rung | n_off | mean_contributing | clean_prefix_fraction | testable | label | d_hat | interval | half_width | draws_above_X | unconditional |
|---|---|---|---|---|---|---|---|---|---|---|
| S4 | 4.0000 | 64.0000 | 0.9627 | True | holds | 0.0002 | [+0.0001, +0.0002] | 0.0000 | 0/1 | 0.0002 |
| S16 | 16.0000 | 63.0000 | 0.8748 | False | not testable with these donors |  |  |  |  | 0.0007 |
| S64 | 64.0000 | 62.0000 | 0.7075 | False | not testable with these donors |  |  |  |  | 0.0023 |

tau_q = 0.1, stratum StackExchange, donor_chain (m = 9): budget rung 1
| rung | n_off | mean_contributing | clean_prefix_fraction | testable | label | d_hat | interval | half_width | draws_above_X | unconditional |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 0.3750 | 64.0000 | 0.9569 | True | holds | 0.0000 | [+0.0000, +0.0001] | 0.0000 | 0/8 | 0.0001 |
| 2 | 4.6250 | 62.1250 | 0.7259 | False | not testable with these donors |  |  |  |  | 0.0018 |
| 3 | 21.6250 | 54.5000 | 0.2505 | False | not testable with these donors |  |  |  |  | 0.0053 |
| 4 | 31.8750 | 52.7500 | 0.2863 | False | not testable with these donors |  |  |  |  | 0.0112 |
| 5a | 49.0000 | 50.0000 | 0.1743 | False | not testable with these donors |  |  |  |  | 0.0157 |
| 5 | 87.7500 | 44.2500 | 0.1141 | False | not testable with these donors |  |  |  |  | 0.0212 |
| 6a | 127.6250 | 39.7500 | 0.0943 | False | not testable with these donors |  |  |  |  | 0.0287 |
| 6 | 176.3750 | 35.1250 | 0.0744 | False | not testable with these donors |  |  |  |  | 0.0371 |
| 7 | 242.7500 | 31.3750 | 0.0638 | False | not testable with these donors |  |  |  |  | 0.0487 |

tau_q = 0.1, stratum StackExchange, sub_rung_chain (m = 3): budget rung None
| rung | n_off | mean_contributing | clean_prefix_fraction | testable | label | d_hat | interval | half_width | draws_above_X | unconditional |
|---|---|---|---|---|---|---|---|---|---|---|
| S4 | 4.0000 | 60.0000 | 0.4227 | False | not testable with these donors | None | None | None | None | 0.0006 |
| S16 | 16.0000 | 52.0000 | 0.1365 | False | not testable with these donors | None | None | None | None | 0.0031 |
| S64 | 64.0000 | 47.0000 | 0.1089 | False | not testable with these donors | None | None | None | None | 0.0200 |

tau_q = 0.1, stratum Wikipedia (en), donor_chain (m = 9): budget rung 2
| rung | n_off | mean_contributing | clean_prefix_fraction | testable | label | d_hat | interval | half_width | draws_above_X | unconditional |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 0.3750 | 64.0000 | 0.9998 | True | holds | 0.0000 | [+0.0000, +0.0000] | 0.0000 | 0/8 | 0.0000 |
| 2 | 4.6250 | 64.0000 | 0.9744 | True | holds | 0.0002 | [+0.0002, +0.0003] | 0.0000 | 0/8 | 0.0002 |
| 3 | 21.6250 | 63.7500 | 0.8671 | False | not testable with these donors |  |  |  |  | 0.0010 |
| 4 | 31.8750 | 62.2500 | 0.8157 | False | not testable with these donors |  |  |  |  | 0.0015 |
| 5a | 49.0000 | 62.0000 | 0.7512 | False | not testable with these donors |  |  |  |  | 0.0024 |
| 5 | 87.7500 | 60.5000 | 0.5924 | False | not testable with these donors |  |  |  |  | 0.0042 |
| 6a | 127.6250 | 59.3750 | 0.5050 | False | not testable with these donors |  |  |  |  | 0.0064 |
| 6 | 176.3750 | 56.1250 | 0.3971 | False | not testable with these donors |  |  |  |  | 0.0091 |
| 7 | 242.7500 | 52.0000 | 0.3149 | False | not testable with these donors |  |  |  |  | 0.0131 |

tau_q = 0.1, stratum Wikipedia (en), sub_rung_chain (m = 3): budget rung S64
| rung | n_off | mean_contributing | clean_prefix_fraction | testable | label | d_hat | interval | half_width | draws_above_X | unconditional |
|---|---|---|---|---|---|---|---|---|---|---|
| S4 | 4.0000 | 64.0000 | 0.9669 | True | holds | 0.0002 | [+0.0002, +0.0002] | 0.0000 | 0/1 | 0.0002 |
| S16 | 16.0000 | 64.0000 | 0.8206 | True | holds | 0.0008 | [+0.0008, +0.0009] | 0.0001 | 0/1 | 0.0008 |
| S64 | 64.0000 | 64.0000 | 0.6487 | True | holds | 0.0028 | [+0.0026, +0.0031] | 0.0002 | 0/1 | 0.0028 |

tau_q = 0, stratum all, donor_chain (m = 9): budget rung 5
| rung | n_off | mean_contributing | clean_prefix_fraction | testable | label | d_hat | interval | half_width | draws_above_X | unconditional |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 0.3750 | 509.7500 | 0.9457 | True | holds | 0.0000 | [+0.0000, +0.0000] | 0.0000 | 0/8 | 0.0001 |
| 2 | 4.6250 | 480.3750 | 0.6944 | True | holds | 0.0003 | [+0.0003, +0.0004] | 0.0000 | 0/8 | 0.0018 |
| 3 | 21.6250 | 398.8750 | 0.2283 | True | holds | 0.0013 | [+0.0012, +0.0014] | 0.0001 | 0/8 | 0.0057 |
| 4 | 31.8750 | 364.6250 | 0.2042 | True | holds | 0.0019 | [+0.0017, +0.0020] | 0.0001 | 0/8 | 0.0115 |
| 5a | 49.0000 | 327.8750 | 0.1289 | True | holds | 0.0029 | [+0.0027, +0.0032] | 0.0002 | 0/8 | 0.0165 |
| 5 | 87.7500 | 269.6250 | 0.0667 | True | holds | 0.0051 | [+0.0048, +0.0056] | 0.0004 | 0/8 | 0.0225 |
| 6a | 127.6250 | 226.2500 | 0.0446 | False | not testable with these donors |  |  |  |  | 0.0304 |
| 6 | 176.3750 | 183.2500 | 0.0297 | False | not testable with these donors |  |  |  |  | 0.0387 |
| 7 | 242.7500 | 149.7500 | 0.0212 | False | not testable with these donors |  |  |  |  | 0.0478 |

tau_q = 0, stratum all, sub_rung_chain (m = 3): budget rung S64
| rung | n_off | mean_contributing | clean_prefix_fraction | testable | label | d_hat | interval | half_width | draws_above_X | unconditional |
|---|---|---|---|---|---|---|---|---|---|---|
| S4 | 4.0000 | 484.0000 | 0.6130 | True | holds | 0.0002 | [+0.0002, +0.0002] | 0.0000 | 0/1 | 0.0004 |
| S16 | 16.0000 | 420.0000 | 0.2159 | True | holds | 0.0011 | [+0.0010, +0.0012] | 0.0001 | 0/1 | 0.0038 |
| S64 | 64.0000 | 317.0000 | 0.1038 | True | holds | 0.0031 | [+0.0028, +0.0033] | 0.0002 | 0/1 | 0.0202 |

tau_q = 0, stratum Github, donor_chain (m = 9): budget rung 5a
| rung | n_off | mean_contributing | clean_prefix_fraction | testable | label | d_hat | interval | half_width | draws_above_X | unconditional |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 0.3750 | 254.8750 | 0.9423 | True | holds | 0.0000 | [+0.0000, +0.0000] | 0.0000 | 0/8 | 0.0000 |
| 2 | 4.6250 | 239.2500 | 0.6747 | True | holds | 0.0004 | [+0.0004, +0.0005] | 0.0001 | 0/8 | 0.0024 |
| 3 | 21.6250 | 187.7500 | 0.1382 | True | holds | 0.0016 | [+0.0015, +0.0017] | 0.0001 | 0/8 | 0.0068 |
| 4 | 31.8750 | 165.2500 | 0.1279 | True | holds | 0.0024 | [+0.0022, +0.0027] | 0.0003 | 0/8 | 0.0157 |
| 5a | 49.0000 | 140.3750 | 0.0685 | True | holds | 0.0038 | [+0.0035, +0.0043] | 0.0004 | 0/8 | 0.0225 |
| 5 | 87.7500 | 103.3750 | 0.0348 | False | not testable with these donors |  |  |  |  | 0.0275 |
| 6a | 127.6250 | 75.8750 | 0.0208 | False | not testable with these donors |  |  |  |  | 0.0370 |
| 6 | 176.3750 | 53.1250 | 0.0130 | False | not testable with these donors |  |  |  |  | 0.0443 |
| 7 | 242.7500 | 38.6250 | 0.0088 | False | not testable with these donors |  |  |  |  | 0.0528 |

tau_q = 0, stratum Github, sub_rung_chain (m = 3): budget rung S64
| rung | n_off | mean_contributing | clean_prefix_fraction | testable | label | d_hat | interval | half_width | draws_above_X | unconditional |
|---|---|---|---|---|---|---|---|---|---|---|
| S4 | 4.0000 | 247.0000 | 0.6610 | True | holds | 0.0002 | [+0.0002, +0.0003] | 0.0000 | 0/1 | 0.0004 |
| S16 | 16.0000 | 212.0000 | 0.1262 | True | holds | 0.0013 | [+0.0012, +0.0015] | 0.0001 | 0/1 | 0.0037 |
| S64 | 64.0000 | 134.0000 | 0.0527 | True | holds | 0.0038 | [+0.0034, +0.0042] | 0.0004 | 0/1 | 0.0258 |

tau_q = 0, stratum other, donor_chain (m = 9): budget rung 6a
| rung | n_off | mean_contributing | clean_prefix_fraction | testable | label | d_hat | interval | half_width | draws_above_X | unconditional |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 0.3750 | 254.8750 | 0.9491 | True | holds | 0.0000 | [+0.0000, +0.0000] | 0.0000 | 0/8 | 0.0001 |
| 2 | 4.6250 | 241.1250 | 0.7140 | True | holds | 0.0003 | [+0.0002, +0.0003] | 0.0000 | 0/8 | 0.0012 |
| 3 | 21.6250 | 211.1250 | 0.3184 | True | holds | 0.0010 | [+0.0009, +0.0011] | 0.0001 | 0/8 | 0.0047 |
| 4 | 31.8750 | 199.3750 | 0.2805 | True | holds | 0.0015 | [+0.0014, +0.0016] | 0.0001 | 0/8 | 0.0073 |
| 5a | 49.0000 | 187.5000 | 0.1893 | True | holds | 0.0023 | [+0.0021, +0.0025] | 0.0002 | 0/8 | 0.0104 |
| 5 | 87.7500 | 166.2500 | 0.0987 | True | holds | 0.0041 | [+0.0038, +0.0045] | 0.0003 | 0/8 | 0.0175 |
| 6a | 127.6250 | 150.3750 | 0.0684 | True | holds | 0.0060 | [+0.0056, +0.0066] | 0.0005 | 0/8 | 0.0239 |
| 6 | 176.3750 | 130.1250 | 0.0465 | False | not testable with these donors |  |  |  |  | 0.0331 |
| 7 | 242.7500 | 111.1250 | 0.0336 | False | not testable with these donors |  |  |  |  | 0.0429 |

tau_q = 0, stratum other, sub_rung_chain (m = 3): budget rung S64
| rung | n_off | mean_contributing | clean_prefix_fraction | testable | label | d_hat | interval | half_width | draws_above_X | unconditional |
|---|---|---|---|---|---|---|---|---|---|---|
| S4 | 4.0000 | 237.0000 | 0.5650 | True | holds | 0.0002 | [+0.0002, +0.0002] | 0.0000 | 0/1 | 0.0004 |
| S16 | 16.0000 | 208.0000 | 0.3056 | True | holds | 0.0008 | [+0.0008, +0.0009] | 0.0001 | 0/1 | 0.0038 |
| S64 | 64.0000 | 183.0000 | 0.1549 | True | holds | 0.0025 | [+0.0024, +0.0027] | 0.0002 | 0/1 | 0.0147 |

tau_q = 0, stratum ArXiv, donor_chain (m = 9): budget rung None
| rung | n_off | mean_contributing | clean_prefix_fraction | testable | label | d_hat | interval | half_width | draws_above_X | unconditional |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 0.3750 | 62.8750 | 0.8728 | False | not testable with these donors | None | None | None | None | 0.0003 |
| 2 | 4.6250 | 52.7500 | 0.4833 | False | not testable with these donors | None | None | None | None | 0.0026 |
| 3 | 21.6250 | 36.0000 | 0.1127 | False | not testable with these donors | None | None | None | None | 0.0114 |
| 4 | 31.8750 | 32.7500 | 0.0834 | False | not testable with these donors | None | None | None | None | 0.0151 |
| 5a | 49.0000 | 29.0000 | 0.0551 | False | not testable with these donors | None | None | None | None | 0.0217 |
| 5 | 87.7500 | 24.1250 | 0.0314 | False | not testable with these donors | None | None | None | None | 0.0409 |
| 6a | 127.6250 | 21.2500 | 0.0246 | False | not testable with these donors | None | None | None | None | 0.0551 |
| 6 | 176.3750 | 18.2500 | 0.0177 | False | not testable with these donors | None | None | None | None | 0.0784 |
| 7 | 242.7500 | 16.0000 | 0.0145 | False | not testable with these donors | None | None | None | None | 0.0983 |

tau_q = 0, stratum ArXiv, sub_rung_chain (m = 3): budget rung None
| rung | n_off | mean_contributing | clean_prefix_fraction | testable | label | d_hat | interval | half_width | draws_above_X | unconditional |
|---|---|---|---|---|---|---|---|---|---|---|
| S4 | 4.0000 | 52.0000 | 0.2999 | False | not testable with these donors | None | None | None | None | 0.0005 |
| S16 | 16.0000 | 37.0000 | 0.1275 | False | not testable with these donors | None | None | None | None | 0.0106 |
| S64 | 64.0000 | 30.0000 | 0.0685 | False | not testable with these donors | None | None | None | None | 0.0337 |

tau_q = 0, stratum Pile-CC, donor_chain (m = 9): budget rung 1
| rung | n_off | mean_contributing | clean_prefix_fraction | testable | label | d_hat | interval | half_width | draws_above_X | unconditional |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 0.3750 | 64.0000 | 0.9838 | True | holds | 0.0000 | [+0.0000, +0.0000] | 0.0000 | 0/8 | 0.0000 |
| 2 | 4.6250 | 63.5000 | 0.8629 | False | not testable with these donors |  |  |  |  | 0.0002 |
| 3 | 21.6250 | 61.2500 | 0.5259 | False | not testable with these donors |  |  |  |  | 0.0009 |
| 4 | 31.8750 | 58.7500 | 0.4401 | False | not testable with these donors |  |  |  |  | 0.0013 |
| 5a | 49.0000 | 56.7500 | 0.3187 | False | not testable with these donors |  |  |  |  | 0.0020 |
| 5 | 87.7500 | 51.6250 | 0.1676 | False | not testable with these donors |  |  |  |  | 0.0036 |
| 6a | 127.6250 | 47.2500 | 0.1171 | False | not testable with these donors |  |  |  |  | 0.0055 |
| 6 | 176.3750 | 41.6250 | 0.0827 | False | not testable with these donors |  |  |  |  | 0.0078 |
| 7 | 242.7500 | 36.2500 | 0.0599 | False | not testable with these donors |  |  |  |  | 0.0113 |

tau_q = 0, stratum Pile-CC, sub_rung_chain (m = 3): budget rung None
| rung | n_off | mean_contributing | clean_prefix_fraction | testable | label | d_hat | interval | half_width | draws_above_X | unconditional |
|---|---|---|---|---|---|---|---|---|---|---|
| S4 | 4.0000 | 63.0000 | 0.7692 | False | not testable with these donors | None | None | None | None | 0.0002 |
| S16 | 16.0000 | 60.0000 | 0.5276 | False | not testable with these donors | None | None | None | None | 0.0007 |
| S64 | 64.0000 | 55.0000 | 0.2549 | False | not testable with these donors | None | None | None | None | 0.0023 |

tau_q = 0, stratum StackExchange, donor_chain (m = 9): budget rung 1
| rung | n_off | mean_contributing | clean_prefix_fraction | testable | label | d_hat | interval | half_width | draws_above_X | unconditional |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 0.3750 | 64.0000 | 0.9505 | True | holds | 0.0000 | [+0.0000, +0.0001] | 0.0000 | 0/8 | 0.0001 |
| 2 | 4.6250 | 61.2500 | 0.6599 | False | not testable with these donors |  |  |  |  | 0.0018 |
| 3 | 21.6250 | 51.6250 | 0.1660 | False | not testable with these donors |  |  |  |  | 0.0053 |
| 4 | 31.8750 | 48.6250 | 0.1864 | False | not testable with these donors |  |  |  |  | 0.0112 |
| 5a | 49.0000 | 44.0000 | 0.1001 | False | not testable with these donors |  |  |  |  | 0.0157 |
| 5 | 87.7500 | 37.0000 | 0.0556 | False | not testable with these donors |  |  |  |  | 0.0212 |
| 6a | 127.6250 | 32.3750 | 0.0406 | False | not testable with these donors |  |  |  |  | 0.0287 |
| 6 | 176.3750 | 27.1250 | 0.0304 | False | not testable with these donors |  |  |  |  | 0.0371 |
| 7 | 242.7500 | 21.7500 | 0.0209 | False | not testable with these donors |  |  |  |  | 0.0487 |

tau_q = 0, stratum StackExchange, sub_rung_chain (m = 3): budget rung None
| rung | n_off | mean_contributing | clean_prefix_fraction | testable | label | d_hat | interval | half_width | draws_above_X | unconditional |
|---|---|---|---|---|---|---|---|---|---|---|
| S4 | 4.0000 | 59.0000 | 0.3790 | False | not testable with these donors | None | None | None | None | 0.0006 |
| S16 | 16.0000 | 49.0000 | 0.1029 | False | not testable with these donors | None | None | None | None | 0.0031 |
| S64 | 64.0000 | 39.0000 | 0.0635 | False | not testable with these donors | None | None | None | None | 0.0200 |

tau_q = 0, stratum Wikipedia (en), donor_chain (m = 9): budget rung 1
| rung | n_off | mean_contributing | clean_prefix_fraction | testable | label | d_hat | interval | half_width | draws_above_X | unconditional |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 0.3750 | 64.0000 | 0.9892 | True | holds | 0.0000 | [+0.0000, +0.0000] | 0.0000 | 0/8 | 0.0000 |
| 2 | 4.6250 | 63.6250 | 0.8499 | False | not testable with these donors |  |  |  |  | 0.0002 |
| 3 | 21.6250 | 62.2500 | 0.4688 | False | not testable with these donors |  |  |  |  | 0.0010 |
| 4 | 31.8750 | 59.2500 | 0.4119 | False | not testable with these donors |  |  |  |  | 0.0015 |
| 5a | 49.0000 | 57.7500 | 0.2831 | False | not testable with these donors |  |  |  |  | 0.0024 |
| 5 | 87.7500 | 53.5000 | 0.1401 | False | not testable with these donors |  |  |  |  | 0.0042 |
| 6a | 127.6250 | 49.5000 | 0.0915 | False | not testable with these donors |  |  |  |  | 0.0064 |
| 6 | 176.3750 | 43.1250 | 0.0552 | False | not testable with these donors |  |  |  |  | 0.0091 |
| 7 | 242.7500 | 37.1250 | 0.0392 | False | not testable with these donors |  |  |  |  | 0.0131 |

tau_q = 0, stratum Wikipedia (en), sub_rung_chain (m = 3): budget rung None
| rung | n_off | mean_contributing | clean_prefix_fraction | testable | label | d_hat | interval | half_width | draws_above_X | unconditional |
|---|---|---|---|---|---|---|---|---|---|---|
| S4 | 4.0000 | 63.0000 | 0.8119 | False | not testable with these donors | None | None | None | None | 0.0002 |
| S16 | 16.0000 | 62.0000 | 0.4644 | False | not testable with these donors | None | None | None | None | 0.0008 |
| S64 | 64.0000 | 59.0000 | 0.2328 | False | not testable with these donors | None | None | None | None | 0.0028 |

## 6. The labels of curves 1 to 5
- Curve 1: **fails** (j_det 1, j_mat 3; half-widths from 0.0005 to 0.0273)
- Curve 2 (draw 0; all draws above): **fails** (j_det 1, j_mat 3; half-widths from 0.0010 to 0.0214)
- Curve 3 on other: positive control FAIL; at tau_q = 0.1: donor_chain: budget rung None, labels {'1': 'not testable with these donors', '2': 'not testable with these donors', '3': 'not testable with these donors', '4': 'not testable with these donors', '5a': 'not testable with these donors', '5': 'not testable with these donors', '6a': 'not testable with these donors', '6': 'not testable with these donors', '7': 'not testable with these donors'}; at tau_q = 0: donor_chain: budget rung None
- Curve 4 on other: positive control FAIL; at tau_q = 0.1: donor_chain: budget rung 7, labels {'1': 'holds', '2': 'holds', '3': 'holds', '4': 'holds', '5a': 'holds', '5': 'holds', '6a': 'holds', '6': 'holds', '7': 'holds'}; sub_rung_chain: budget rung S64, labels {'S4': 'holds', 'S16': 'holds', 'S64': 'holds'}; at tau_q = 0: donor_chain: budget rung 7; sub_rung_chain: budget rung S64
- Curve 5 on all: positive control pass; at tau_q = 0.1: donor_chain: budget rung None, labels {'1': 'not testable with these donors', '2': 'not testable with these donors', '3': 'not testable with these donors', '4': 'not testable with these donors', '5a': 'not testable with these donors', '5': 'not testable with these donors', '6a': 'not testable with these donors', '6': 'not testable with these donors', '7': 'not testable with these donors'}; at tau_q = 0: donor_chain: budget rung None

## 7. Everything else
### The never-named chain (`never_named_hard/E/D_unif/tau0.1/ones/incl/ctl-none`), D(n) against n with the linear and quadratic lines; whole set n = 28946, D = 1.2841; alive control present: True
| rung | n_erased | n_per_draw | D_mean | draw_spread_sd | linear_prediction | quadratic_prediction | alive_control_mean | ratio_to_alive_control |
|---|---|---|---|---|---|---|---|---|
| 1 | 169.0000 | 201 222 226 143 212 154 38 156 | 0.0060 | 0.0023 | 0.0075 | 0.0000 | 1.1202 | 0.0053 |
| 2 | 1120.6250 | 1039 1287 1066 1530 1201 891 950 1001 | 0.0515 | 0.0133 | 0.0499 | 0.0019 | 5.3968 | 0.0095 |
| 3 | 4543.6250 | 4494 4466 4640 4523 4240 4733 4660 4593 | 0.2974 | 0.0135 | 0.2025 | 0.0318 | 9.5600 | 0.0311 |
| 4 | 4890.2500 | 6764 4171 5242 1366 4981 5621 5550 5427 | 0.3242 | 0.1161 | 0.2179 | 0.0368 | 8.9393 | 0.0363 |
| 5a | 6501.3750 | 7508 6609 6666 5677 5814 6490 6356 6891 | 0.4396 | 0.0402 | 0.2897 | 0.0651 | 10.7056 | 0.0411 |
| 5 | 7711.0000 | 8170 7805 8026 7761 7675 7475 7455 7321 | 0.5228 | 0.0195 | 0.3436 | 0.0915 | 10.0903 | 0.0518 |
| 6a | 8489.5000 | 8660 8517 8736 8331 8383 8626 8284 8379 | 0.5732 | 0.0130 | 0.3783 | 0.1110 | 10.3834 | 0.0552 |
| 6 | 9060.0000 | 9203 8893 9106 8963 9067 9182 8942 9124 | 0.6086 | 0.0085 | 0.4038 | 0.1264 | 10.8391 | 0.0561 |
| 7 | 9659.2500 | 9794 9580 9625 9579 9704 9591 9694 9707 | 0.6446 | 0.0045 | 0.4305 | 0.1436 | 10.4650 | 0.0616 |
| B50 | 14473.0000 | 14473 14473 14473 14473 14473 14473 14473 14473 | 0.8821 | 0.0032 | 0.6450 | 0.3225 |  |  |
| B75 | 21709.0000 | 21709 21709 21709 21709 21709 21709 21709 21709 | 1.1217 | 0.0017 | 0.9675 | 0.7256 |  |  |
| 8 | 28946.0000 | 28946 | 1.2841 |  | 1.2900 | 1.2900 | 11.3324 | 0.1133 |

The family's rung-8 cells under the one-cell rule (the whole set with Delta included and excluded, the strict cell at tau = 0), the conditional figure at both tau_q:
| cell | n_erased | unconditional | testable_0.1 | d_hat_0.1 | interval_0.1 | label_0.1 | testable_0 | d_hat_0 | interval_0 | label_0 |
|---|---|---|---|---|---|---|---|---|---|---|
| never_named_hard/E/D_unif/tau0.1/ones/incl/ctl-none | 28946.0000 | 1.2841 | True | 1.2830 | [+1.2655, +1.3016] | fails | False |  |  | not testable with these donors |
| never_named_hard/E/D_unif/tau0.1/ones/excl/ctl-none | 28946.0000 | 1.2761 | True | 1.2751 | [+1.2576, +1.2935] | fails | False |  |  | not testable with these donors |
| never_named_hard/E/D_unif/tau0/ones/incl/ctl-none | 5336.0000 | 0.3262 | True | 0.3262 | [+0.3187, +0.3343] | fails | True | 0.3131 | [+0.3032, +0.3237] | fails |

### Curve 1 at tau = 0.5 and its plain control, read as any union chain
## The union under r = 0, tau = 0.5, Delta excluded, on E
Chain `union/E/D_unif/tau0.5/r0/excl/ctl-none`; rung 0 mean 0.3417; m = 10 rungs compared; **label: fails** (at m = 8: fails); j_det = 1, j_mat = 3, first repair rung = None; per draw: k0: det 1, mat 3, k1: det 1, mat 3, k2: det 1, mat 3, k3: det 1, mat 3, k4: det 1, mat 3, k5: det 1, mat 3, k6: det 1, mat 3, k7: det 1, mat 3

| rung | n_on | mean_sigma | overlap | mean_kl | excess | interval | half_width | two_level | draws_positive | fraction_seq_above_X | detected | material | repair | differs_at_m_8 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 136.1250 | 118.0438 | 0.0178 | 0.3449 | 0.0031 | [+0.0027, +0.0036] | 0.0004 | [+0.0015, +0.0049] | 8/8 | 0.0000 | True | False | False | False |
| 2 | 893.5000 | 843.8892 | 0.1160 | 0.3691 | 0.0274 | [+0.0260, +0.0289] | 0.0015 | [+0.0217, +0.0349] | 8/8 | 0.0645 | True | False | False | False |
| 3 | 3976.8750 | 3855.2559 | 0.4720 | 0.6894 | 0.3477 | [+0.3376, +0.3591] | 0.0108 | [+0.3215, +0.3763] | 8/8 | 1.0000 | True | True | False | False |
| 4 | 4382.0000 | 4269.2422 | 0.4837 | 0.7732 | 0.4314 | [+0.4172, +0.4459] | 0.0144 | [+0.2255, +0.5838] | 8/8 | 0.9922 | True | True | False | False |
| 5a | 5969.5000 | 5833.1938 | 0.6481 | 0.9949 | 0.6532 | [+0.6339, +0.6730] | 0.0195 | [+0.5596, +0.7556] | 8/8 | 1.0000 | True | True | False | False |
| 5 | 7244.7500 | 7099.6396 | 0.7634 | 1.1465 | 0.8048 | [+0.7834, +0.8272] | 0.0219 | [+0.7498, +0.8679] | 8/8 | 1.0000 | True | True | False | False |
| 6a | 8120.7500 | 7971.7705 | 0.8415 | 1.2430 | 0.9013 | [+0.8787, +0.9260] | 0.0236 | [+0.8588, +0.9381] | 8/8 | 1.0000 | True | True | False | False |
| 6 | 8798.2500 | 8647.7021 | 0.8984 | 1.2837 | 0.9420 | [+0.9174, +0.9688] | 0.0257 | [+0.9136, +0.9721] | 8/8 | 1.0000 | True | True | False | False |
| 7 | 9506.5000 | 9355.3477 | 0.9587 | 1.2971 | 0.9554 | [+0.9289, +0.9832] | 0.0271 | [+0.9286, +0.9843] | 8/8 | 1.0000 | True | True | False | False |
| 8 | 9926.0000 | 9774.8027 | 0.9968 | 1.2892 | 0.9475 | [+0.9209, +0.9754] | 0.0272 | [+0.9209, +0.9754] | 1/1 | 1.0000 | True | True | False | False |

Paired union minus control on the same sequence, draw, and rung (95 percent uncorrected), with the pre-reads' overlap of the two sets: rung 1: +0.0048 [+0.0045, +0.0051] (overlap 0.018); rung 2: +0.0372 [+0.0364, +0.0381] (overlap 0.116); rung 3: +0.3299 [+0.3238, +0.3362] (overlap 0.472); rung 4: +0.3976 [+0.3879, +0.4074] (overlap 0.484); rung 5a: +0.5450 [+0.5326, +0.5574] (overlap 0.648)
Rung 4 minus rung 3 at nearly the same count (diffuse against concentrated), paired: +0.0838 [+0.0767, +0.0906].
Rung 4 (one donor sequence): excess +0.4314 [+0.4172, +0.4459], fraction of sequences with excess above X 0.992.
Per-rung excess by reader label on E (each label's own resample, the curve's m):
| label | n | rung | excess | interval | half_width | detected | material |
|---|---|---|---|---|---|---|---|
| code | 120 | 1 | 0.0072 | [+0.0057, +0.0089] | 0.0016 | True | False |
| code | 120 | 2 | 0.0425 | [+0.0368, +0.0496] | 0.0064 | True | False |
| code | 120 | 3 | 0.4596 | [+0.4241, +0.5015] | 0.0387 | True | True |
| code | 120 | 4 | 0.5870 | [+0.5508, +0.6260] | 0.0376 | True | True |
| code | 120 | 5a | 0.7957 | [+0.7423, +0.8538] | 0.0558 | True | True |
| code | 120 | 5 | 0.9460 | [+0.8831, +1.0132] | 0.0650 | True | True |
| code | 120 | 6a | 1.1791 | [+1.1020, +1.2619] | 0.0800 | True | True |
| code | 120 | 6 | 1.2815 | [+1.1957, +1.3708] | 0.0875 | True | True |
| code | 120 | 7 | 1.2911 | [+1.2049, +1.3841] | 0.0896 | True | True |
| code | 120 | 8 | 1.2794 | [+1.1938, +1.3715] | 0.0889 | True | True |
| mixed | 27 | 1 | 0.0049 | [+0.0032, +0.0065] | 0.0017 | False | False |
| mixed | 27 | 2 | 0.0295 | [+0.0244, +0.0347] | 0.0051 | True | False |
| mixed | 27 | 3 | 0.3683 | [+0.3305, +0.4139] | 0.0417 | True | True |
| mixed | 27 | 4 | 0.5006 | [+0.4620, +0.5437] | 0.0408 | True | True |
| mixed | 27 | 5a | 0.7107 | [+0.6538, +0.7730] | 0.0596 | True | True |
| mixed | 27 | 5 | 0.8584 | [+0.7930, +0.9272] | 0.0671 | True | True |
| mixed | 27 | 6a | 1.0056 | [+0.9278, +1.0853] | 0.0787 | True | True |
| mixed | 27 | 6 | 1.0656 | [+0.9792, +1.1550] | 0.0879 | True | True |
| mixed | 27 | 7 | 1.0661 | [+0.9811, +1.1574] | 0.0881 | True | True |
| mixed | 27 | 8 | 1.0557 | [+0.9705, +1.1476] | 0.0886 | True | True |
| other | 158 | 1 | 0.0005 | [-0.0006, +0.0018] | 0.0012 | False | False |
| other | 158 | 2 | 0.0300 | [+0.0261, +0.0340] | 0.0040 | True | False |
| other | 158 | 3 | 0.3603 | [+0.3253, +0.4014] | 0.0380 | True | True |
| other | 158 | 4 | 0.3353 | [+0.2793, +0.3939] | 0.0573 | True | True |
| other | 158 | 5a | 0.5286 | [+0.4502, +0.6102] | 0.0800 | True | True |
| other | 158 | 5 | 0.7092 | [+0.6276, +0.7961] | 0.0842 | True | True |
| other | 158 | 6a | 0.9007 | [+0.8249, +0.9895] | 0.0823 | True | True |
| other | 158 | 6 | 1.0355 | [+0.9573, +1.1275] | 0.0851 | True | True |
| other | 158 | 7 | 1.1530 | [+1.0728, +1.2470] | 0.0871 | True | True |
| other | 158 | 8 | 1.1626 | [+1.0798, +1.2590] | 0.0896 | True | True |
| prose | 719 | 1 | 0.0030 | [+0.0026, +0.0034] | 0.0004 | True | False |
| prose | 719 | 2 | 0.0242 | [+0.0229, +0.0256] | 0.0013 | True | False |
| prose | 719 | 3 | 0.3254 | [+0.3167, +0.3341] | 0.0087 | True | True |
| prose | 719 | 4 | 0.4240 | [+0.4121, +0.4357] | 0.0118 | True | True |
| prose | 719 | 5a | 0.6546 | [+0.6382, +0.6710] | 0.0164 | True | True |
| prose | 719 | 5 | 0.8002 | [+0.7799, +0.8208] | 0.0205 | True | True |
| prose | 719 | 6a | 0.8512 | [+0.8295, +0.8731] | 0.0218 | True | True |
| prose | 719 | 6 | 0.8602 | [+0.8387, +0.8821] | 0.0217 | True | True |
| prose | 719 | 7 | 0.8518 | [+0.8303, +0.8737] | 0.0217 | True | True |
| prose | 719 | 8 | 0.8408 | [+0.8194, +0.8627] | 0.0217 | True | True |

Paired union minus control by reader label at rungs 1 to 4 and 5a (each label's own resample, uncorrected 95 percent), the control's per-label excess beside:
| label | n | rung | union_minus_control | interval_uncorrected | half_width | control_excess | control_interval_uncorrected |
|---|---|---|---|---|---|---|---|
| code | 120 | 1 | 0.0081 | [+0.0070, +0.0091] | 0.0011 | -0.0008 | [-0.0010, -0.0006] |
| code | 120 | 2 | 0.0470 | [+0.0431, +0.0516] | 0.0043 | -0.0045 | [-0.0054, -0.0036] |
| code | 120 | 3 | 0.4134 | [+0.3890, +0.4398] | 0.0254 | 0.0462 | [+0.0424, +0.0502] |
| code | 120 | 4 | 0.5287 | [+0.5044, +0.5535] | 0.0245 | 0.0583 | [+0.0546, +0.0621] |
| code | 120 | 5a | 0.6488 | [+0.6150, +0.6835] | 0.0343 | 0.1469 | [+0.1394, +0.1547] |
| mixed | 27 | 1 | 0.0071 | [+0.0059, +0.0082] | 0.0011 | -0.0021 | [-0.0026, -0.0018] |
| mixed | 27 | 2 | 0.0400 | [+0.0371, +0.0428] | 0.0029 | -0.0105 | [-0.0121, -0.0089] |
| mixed | 27 | 3 | 0.3492 | [+0.3254, +0.3743] | 0.0245 | 0.0191 | [+0.0129, +0.0263] |
| mixed | 27 | 4 | 0.4648 | [+0.4389, +0.4926] | 0.0268 | 0.0358 | [+0.0299, +0.0426] |
| mixed | 27 | 5a | 0.5995 | [+0.5644, +0.6375] | 0.0365 | 0.1112 | [+0.1009, +0.1233] |
| other | 158 | 1 | 0.0008 | [-0.0001, +0.0017] | 0.0009 | -0.0003 | [-0.0006, -0.0001] |
| other | 158 | 2 | 0.0313 | [+0.0285, +0.0342] | 0.0028 | -0.0013 | [-0.0025, -0.0000] |
| other | 158 | 3 | 0.3037 | [+0.2823, +0.3275] | 0.0226 | 0.0566 | [+0.0489, +0.0647] |
| other | 158 | 4 | 0.2691 | [+0.2317, +0.3080] | 0.0381 | 0.0662 | [+0.0592, +0.0737] |
| other | 158 | 5a | 0.3661 | [+0.3173, +0.4177] | 0.0502 | 0.1625 | [+0.1495, +0.1765] |
| prose | 719 | 1 | 0.0051 | [+0.0048, +0.0054] | 0.0003 | -0.0021 | [-0.0022, -0.0020] |
| prose | 719 | 2 | 0.0368 | [+0.0361, +0.0375] | 0.0007 | -0.0126 | [-0.0130, -0.0121] |
| prose | 719 | 3 | 0.3210 | [+0.3158, +0.3262] | 0.0052 | 0.0045 | [+0.0028, +0.0061] |
| prose | 719 | 4 | 0.4014 | [+0.3930, +0.4097] | 0.0084 | 0.0226 | [+0.0210, +0.0242] |
| prose | 719 | 5a | 0.5650 | [+0.5542, +0.5756] | 0.0107 | 0.0896 | [+0.0869, +0.0923] |

## Its plain control
Chain `union/E/D_unif/tau0.5/r0/excl/ctl-plain`; rung 0 mean 0.3417; m = 10 rungs compared; **label: fails** (at m = 8: fails); j_det = 3, j_mat = 5a, first repair rung = 1; per draw: k0: det 3, mat 4, k1: det 3, mat 5a, k2: det 3, mat 5a, k3: det 3, mat 5, k4: det 3, mat 5, k5: det 3, mat 5a, k6: det 3, mat 5a, k7: det 3, mat 5a

| rung | n_on | mean_sigma | overlap | mean_kl | excess | interval | half_width | two_level | draws_positive | fraction_seq_above_X | detected | material | repair | differs_at_m_8 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 136.1250 | 133.5844 | 0.0178 | 0.3401 | -0.0017 | [-0.0018, -0.0015] | 0.0001 | [-0.0024, -0.0009] | 0/8 | 0.0000 | False | False | True | False |
| 2 | 893.5000 | 876.6694 | 0.1160 | 0.3319 | -0.0098 | [-0.0105, -0.0091] | 0.0007 | [-0.0109, -0.0088] | 0/8 | 0.0000 | False | False | True | False |
| 3 | 3976.8750 | 3906.5439 | 0.4720 | 0.3595 | 0.0178 | [+0.0147, +0.0211] | 0.0032 | [+0.0106, +0.0247] | 8/8 | 0.1328 | True | False | False | False |
| 4 | 4382.0000 | 4308.7627 | 0.4837 | 0.3756 | 0.0339 | [+0.0311, +0.0368] | 0.0029 | [+0.0045, +0.0763] | 7/8 | 0.2764 | True | False | False | False |
| 5a | 5969.5000 | 5870.5190 | 0.6481 | 0.4499 | 0.1081 | [+0.1033, +0.1133] | 0.0050 | [+0.0591, +0.1701] | 8/8 | 0.9033 | True | True | False | False |
| 5 | 7244.7500 | 7126.6484 | 0.7634 | 0.5791 | 0.2374 | [+0.2288, +0.2466] | 0.0089 | [+0.1903, +0.2895] | 8/8 | 1.0000 | True | True | False | False |
| 6a | 8120.7500 | 7989.9316 | 0.8415 | 0.7568 | 0.4151 | [+0.4014, +0.4302] | 0.0144 | [+0.3464, +0.4755] | 8/8 | 1.0000 | True | True | False | False |
| 6 | 8798.2500 | 8658.8379 | 0.8984 | 0.9339 | 0.5922 | [+0.5735, +0.6130] | 0.0197 | [+0.5444, +0.6522] | 8/8 | 1.0000 | True | True | False | False |
| 7 | 9506.5000 | 9359.4082 | 0.9587 | 1.1542 | 0.8125 | [+0.7884, +0.8387] | 0.0251 | [+0.7748, +0.8486] | 8/8 | 1.0000 | True | True | False | False |
| 8 | 9926.0000 | 9774.9355 | 0.9968 | 1.2840 | 0.9423 | [+0.9158, +0.9702] | 0.0272 | [+0.9158, +0.9702] | 1/1 | 1.0000 | True | True | False | False |
Rung 4 (one donor sequence): excess +0.0339 [+0.0311, +0.0368], fraction of sequences with excess above X 0.276.

### The tau = 0 union and its plain control, read as any union chain
## The tau = 0 union under r = 0 on E
Chain `union/E/D_unif/tau0/r0/excl/ctl-none`; rung 0 mean 0.3417; m = 8 rungs compared; **label: fails** (at m = 8: fails); j_det = 1, j_mat = 3, first repair rung = None; per draw: k0: det 1, mat 3, k1: det 1, mat 3, k2: det 1, mat 3, k3: det 1, mat 2, k4: det 1, mat 3, k5: det 1, mat 3, k6: det 1, mat 3, k7: det 1, mat 3

| rung | n_on | mean_sigma | overlap | mean_kl | excess | interval | half_width | two_level | draws_positive | fraction_seq_above_X | detected | material | repair | differs_at_m_8 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 180.7500 | 160.6622 | 0.0289 | 0.3459 | 0.0042 | [+0.0037, +0.0047] | 0.0005 | [+0.0023, +0.0062] | 8/8 | 0.0000 | True | False | False | False |
| 2 | 1206.5000 | 1148.1084 | 0.1590 | 0.3862 | 0.0444 | [+0.0425, +0.0464] | 0.0019 | [+0.0351, +0.0595] | 8/8 | 0.3535 | True | False | False | False |
| 3 | 4764.8750 | 4633.4092 | 0.5547 | 0.8303 | 0.4886 | [+0.4747, +0.5035] | 0.0144 | [+0.4512, +0.5256] | 8/8 | 1.0000 | True | True | False | False |
| 4 | 5417.3750 | 5295.5503 | 0.5626 | 0.8472 | 0.5055 | [+0.4895, +0.5218] | 0.0161 | [+0.2817, +0.6579] | 8/8 | 1.0000 | True | True | False | False |
| 5 | 8951.1250 | 8802.5576 | 0.8208 | 1.1968 | 0.8551 | [+0.8332, +0.8792] | 0.0230 | [+0.8093, +0.9013] | 8/8 | 1.0000 | True | True | False | False |
| 6 | 12422.2500 | 12271.1504 | 0.7767 | 1.2297 | 0.8880 | [+0.8631, +0.9144] | 0.0256 | [+0.8619, +0.9159] | 8/8 | 1.0000 | True | True | False | False |
| 7 | 18745.3750 | 18594.1797 | 0.6762 | 1.0659 | 0.7242 | [+0.7001, +0.7495] | 0.0247 | [+0.6996, +0.7505] | 8/8 | 1.0000 | True | True | False | False |
| 8 | 33576.0000 | 33424.8047 | 0.8730 | 0.3419 | 0.0002 | [-0.0138, +0.0153] | 0.0146 | [-0.0138, +0.0153] | 1/1 | 0.2842 | False | False | False | False |

Paired union minus control on the same sequence, draw, and rung (95 percent uncorrected), with the pre-reads' overlap of the two sets: rung 1: +0.0064 [+0.0060, +0.0067] (overlap 0.029); rung 2: +0.0562 [+0.0551, +0.0574] (overlap 0.159); rung 3: +0.4401 [+0.4317, +0.4487] (overlap 0.555); rung 4: +0.4160 [+0.4057, +0.4267] (overlap 0.563)
Rung 4 minus rung 3 at nearly the same count (diffuse against concentrated), paired: +0.0169 [+0.0103, +0.0231].
Rung 4 (one donor sequence): excess +0.5055 [+0.4895, +0.5218], fraction of sequences with excess above X 1.000.
Per-rung excess by reader label on E (each label's own resample, the curve's m):
| label | n | rung | excess | interval | half_width | detected | material |
|---|---|---|---|---|---|---|---|
| code | 120 | 1 | 0.0085 | [+0.0069, +0.0101] | 0.0016 | False | False |
| code | 120 | 2 | 0.0627 | [+0.0558, +0.0711] | 0.0076 | True | True |
| code | 120 | 3 | 0.6446 | [+0.5980, +0.6956] | 0.0488 | True | True |
| code | 120 | 4 | 0.6734 | [+0.6318, +0.7189] | 0.0436 | True | True |
| code | 120 | 5 | 1.0906 | [+1.0191, +1.1670] | 0.0739 | True | True |
| code | 120 | 6 | 1.2158 | [+1.1336, +1.3045] | 0.0855 | True | True |
| code | 120 | 7 | 1.0353 | [+0.9560, +1.1208] | 0.0824 | True | True |
| code | 120 | 8 | 0.1792 | [+0.1301, +0.2399] | 0.0549 | True | True |
| mixed | 27 | 1 | 0.0066 | [+0.0045, +0.0085] | 0.0020 | False | False |
| mixed | 27 | 2 | 0.0476 | [+0.0403, +0.0553] | 0.0075 | True | False |
| mixed | 27 | 3 | 0.5220 | [+0.4726, +0.5778] | 0.0526 | True | True |
| mixed | 27 | 4 | 0.5799 | [+0.5341, +0.6283] | 0.0471 | True | True |
| mixed | 27 | 5 | 0.9461 | [+0.8731, +1.0213] | 0.0741 | True | True |
| mixed | 27 | 6 | 0.9985 | [+0.9176, +1.0849] | 0.0837 | True | True |
| mixed | 27 | 7 | 0.8255 | [+0.7500, +0.9070] | 0.0785 | True | True |
| mixed | 27 | 8 | 0.0127 | [-0.0248, +0.0519] | 0.0383 | False | False |
| other | 158 | 1 | 0.0002 | [-0.0010, +0.0016] | 0.0013 | False | False |
| other | 158 | 2 | 0.0462 | [+0.0407, +0.0520] | 0.0056 | True | False |
| other | 158 | 3 | 0.5043 | [+0.4530, +0.5644] | 0.0557 | True | True |
| other | 158 | 4 | 0.4150 | [+0.3496, +0.4840] | 0.0672 | True | True |
| other | 158 | 5 | 0.8576 | [+0.7755, +0.9530] | 0.0888 | True | True |
| other | 158 | 6 | 1.0795 | [+1.0005, +1.1712] | 0.0853 | True | True |
| other | 158 | 7 | 0.9416 | [+0.8662, +1.0280] | 0.0809 | True | True |
| other | 158 | 8 | 0.1726 | [+0.1313, +0.2196] | 0.0442 | True | True |
| prose | 719 | 1 | 0.0042 | [+0.0038, +0.0047] | 0.0005 | True | False |
| prose | 719 | 2 | 0.0409 | [+0.0392, +0.0427] | 0.0018 | True | False |
| prose | 719 | 3 | 0.4578 | [+0.4462, +0.4696] | 0.0117 | True | True |
| prose | 719 | 4 | 0.4945 | [+0.4816, +0.5072] | 0.0128 | True | True |
| prose | 719 | 5 | 0.8118 | [+0.7916, +0.8323] | 0.0204 | True | True |
| prose | 719 | 6 | 0.7870 | [+0.7667, +0.8076] | 0.0204 | True | True |
| prose | 719 | 7 | 0.6206 | [+0.6020, +0.6394] | 0.0187 | True | True |
| prose | 719 | 8 | -0.0680 | [-0.0774, -0.0589] | 0.0092 | False | False |

Paired union minus control by reader label at rungs 1 to 4 and 5a (each label's own resample, uncorrected 95 percent), the control's per-label excess beside:
| label | n | rung | union_minus_control | interval_uncorrected | half_width | control_excess | control_interval_uncorrected |
|---|---|---|---|---|---|---|---|
| code | 120 | 1 | 0.0098 | [+0.0087, +0.0109] | 0.0011 | -0.0014 | [-0.0016, -0.0011] |
| code | 120 | 2 | 0.0674 | [+0.0625, +0.0729] | 0.0052 | -0.0047 | [-0.0058, -0.0035] |
| code | 120 | 3 | 0.5584 | [+0.5269, +0.5917] | 0.0324 | 0.0862 | [+0.0808, +0.0919] |
| code | 120 | 4 | 0.5554 | [+0.5286, +0.5832] | 0.0273 | 0.1180 | [+0.1119, +0.1241] |
| mixed | 27 | 1 | 0.0094 | [+0.0081, +0.0107] | 0.0013 | -0.0029 | [-0.0033, -0.0024] |
| mixed | 27 | 2 | 0.0602 | [+0.0560, +0.0643] | 0.0041 | -0.0126 | [-0.0147, -0.0104] |
| mixed | 27 | 3 | 0.4712 | [+0.4402, +0.5024] | 0.0311 | 0.0508 | [+0.0423, +0.0613] |
| mixed | 27 | 4 | 0.4887 | [+0.4605, +0.5184] | 0.0289 | 0.0912 | [+0.0824, +0.1018] |
| other | 158 | 1 | 0.0005 | [-0.0006, +0.0016] | 0.0011 | -0.0003 | [-0.0006, +0.0001] |
| other | 158 | 2 | 0.0466 | [+0.0426, +0.0507] | 0.0040 | -0.0004 | [-0.0021, +0.0013] |
| other | 158 | 3 | 0.4050 | [+0.3743, +0.4379] | 0.0318 | 0.0993 | [+0.0878, +0.1116] |
| other | 158 | 4 | 0.2839 | [+0.2424, +0.3278] | 0.0427 | 0.1311 | [+0.1205, +0.1425] |
| prose | 719 | 1 | 0.0070 | [+0.0067, +0.0073] | 0.0003 | -0.0027 | [-0.0029, -0.0026] |
| prose | 719 | 2 | 0.0563 | [+0.0554, +0.0573] | 0.0009 | -0.0154 | [-0.0160, -0.0149] |
| prose | 719 | 3 | 0.4269 | [+0.4198, +0.4340] | 0.0071 | 0.0309 | [+0.0287, +0.0331] |
| prose | 719 | 4 | 0.4191 | [+0.4103, +0.4277] | 0.0087 | 0.0754 | [+0.0731, +0.0777] |

## Its plain control
Chain `union/E/D_unif/tau0/r0/excl/ctl-plain`; rung 0 mean 0.3417; m = 8 rungs compared; **label: fails** (at m = 8: fails); j_det = 3, j_mat = 4, first repair rung = 1; per draw: k0: det 3, mat 4, k1: det 3, mat 5, k2: det 3, mat 3, k3: det 3, mat 5, k4: det 3, mat 4, k5: det 3, mat 3, k6: det 3, mat 4, k7: det 3, mat 4

| rung | n_on | mean_sigma | overlap | mean_kl | excess | interval | half_width | two_level | draws_positive | fraction_seq_above_X | detected | material | repair | differs_at_m_8 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 180.7500 | 177.4806 | 0.0289 | 0.3395 | -0.0022 | [-0.0024, -0.0020] | 0.0002 | [-0.0031, -0.0014] | 0/8 | 0.0000 | False | False | True | False |
| 2 | 1206.5000 | 1183.8247 | 0.1590 | 0.3299 | -0.0118 | [-0.0127, -0.0109] | 0.0009 | [-0.0134, -0.0103] | 0/8 | 0.0000 | False | False | True | False |
| 3 | 4764.8750 | 4681.9707 | 0.5547 | 0.3902 | 0.0485 | [+0.0444, +0.0529] | 0.0043 | [+0.0381, +0.0579] | 8/8 | 0.4531 | True | False | False | False |
| 4 | 5417.3750 | 5327.1328 | 0.5626 | 0.4311 | 0.0894 | [+0.0856, +0.0934] | 0.0039 | [+0.0297, +0.1625] | 7/8 | 0.8467 | True | True | False | False |
| 5 | 8951.1250 | 8810.7285 | 0.8208 | 0.9403 | 0.5986 | [+0.5818, +0.6172] | 0.0177 | [+0.5297, +0.6719] | 8/8 | 1.0000 | True | True | False | False |
| 6 | 12422.2500 | 12271.1982 | 0.7767 | 1.2349 | 0.8932 | [+0.8678, +0.9202] | 0.0262 | [+0.8669, +0.9203] | 8/8 | 1.0000 | True | True | False | False |
| 7 | 18745.3750 | 18594.1797 | 0.6762 | 1.0699 | 0.7282 | [+0.7041, +0.7543] | 0.0251 | [+0.7037, +0.7549] | 8/8 | 1.0000 | True | True | False | False |
| 8 | 33576.0000 | 33424.8047 | 0.8730 | 0.3442 | 0.0025 | [-0.0115, +0.0179] | 0.0147 | [-0.0115, +0.0179] | 1/1 | 0.2998 | False | False | False | False |
Rung 4 (one donor sequence): excess +0.0894 [+0.0856, +0.0934], fraction of sequences with excess above X 0.847.

The control's overflow into the dead set per rung (the matched count exceeds the alive set from rung 5; mean over draws of the summed per-module overflow, from the pre-reads): rung 1: 0 of n_on 181; rung 2: 0 of n_on 1206; rung 3: 0 of n_on 4765; rung 4: 1 of n_on 5417; rung 5: 198 of n_on 8951; rung 6: 2545 of n_on 12422; rung 7: 8786 of n_on 18745; rung 8: 23617 of n_on 33576

Reference lines beside the chain (its rung 8 is the complement of the strict set: everything the pool labels above 0 pinned at 1, the strict 5,336 at their labels):
| line | cell | n_on | mean_kl | se | excess_over_unmasked |
|---|---|---|---|---|---|
| strict cell: the strict set (g = 0 at every pool position) erased, Delta included | main/E/never_named_hard/D_unif/tau0/ones/incl/k0/r8 | 5336 | 0.3268 | 0.0040 | 0.3154 |
| never-named rung 8: the never-named set at tau = 0.1 erased, Delta included | main/E/never_named_hard/D_unif/tau0.1/ones/incl/k0/r8 | 28946 | 1.2847 | 0.0093 | 1.2732 |
| never-named rung 8, Delta excluded | main/E/never_named_hard/D_unif/tau0.1/ones/excl/k0/r8 | 28946 | 1.2876 | 0.0093 | 1.2761 |
| this chain's rung 8: everything the pool labels above 0 pinned at 1, the strict set at its labels, Delta excluded | main/E/union/D_unif/tau0/r0/excl/k0/r8 | 33576 | 0.3419 | 0.0041 | 0.3305 |
| unmasked | main/E/ref/unmasked | 0 | 0.0115 | 0.0001 | 0.0000 |
| unmasked, Delta included | main/E/ref/unmasked_delta | 0 | 0.0006 | 0.0000 | -0.0108 |
| importances-as-masks (this chain's rung 0) | main/E/ref/importances | 0 | 0.3417 | 0.0032 | 0.3303 |

### The level cells: the alive set at s + (1 - s) g, the never-named set at its labels or at 1, beside their four corners
| s | never_named_at | corner | mean_kl | se | mean_sigma | excess_over_path_rung_0 | path_rung_0 | footprint_labels_minus_one | footprint_interval |
|---|---|---|---|---|---|---|---|---|---|
| 0.0000 | labels | True | 0.3417 | 0.0032 |  | 0.0000 | importances | -0.0198 | [-0.0205, -0.0191] |
| 0.0000 | one | True | 0.3615 | 0.0032 | 9814.8030 | 0.3501 | unmasked |  |  |
| 0.2500 | labels | False | 0.2619 | 0.0025 | 2453.7007 | -0.0798 | importances | 0.0001 | [-0.0004, +0.0006] |
| 0.2500 | one | False | 0.2618 | 0.0024 | 7361.1022 | 0.2503 | unmasked |  |  |
| 0.5000 | labels | False | 0.2126 | 0.0020 | 4907.4015 | -0.1291 | importances | 0.0181 | [+0.0172, +0.0189] |
| 0.5000 | one | False | 0.1946 | 0.0017 | 4907.4015 | 0.1831 | unmasked |  |  |
| 0.7500 | labels | False | 0.2537 | 0.0022 | 7361.1022 | -0.0881 | importances | 0.1278 | [+0.1250, +0.1305] |
| 0.7500 | one | False | 0.1258 | 0.0012 | 2453.7007 | 0.1144 | unmasked |  |  |
| 1.0000 | labels | True | 1.2876 | 0.0093 | 9814.8030 | 0.9458 | importances | 1.2761 | [+1.2585, +1.2947] |
| 1.0000 | one | True | 0.0115 | 0.0001 |  | 0.0000 | unmasked |  |  |

The footprint is L(s, labels) - L(s, 1), paired per sequence with the shared resample (uncorrected 95 percent). The soft-erase chain's points at their own switched fraction (s = 1 - sigma_j / sigma_8), drawn on fig5:
| rung | switched_fraction | s_equivalent | mean_kl | n_on |
|---|---|---|---|---|
| 1 | 0.0152 | 0.9848 | 0.4477 | 169.0000 |
| 2 | 0.1084 | 0.8916 | 0.7416 | 1120.6250 |
| 3 | 0.4498 | 0.5502 | 0.4756 | 4543.6250 |
| 4 | 0.4861 | 0.5139 | 0.4600 | 4890.2500 |
| 5a | 0.6481 | 0.3519 | 0.3975 | 6501.3750 |
| 5 | 0.7706 | 0.2294 | 0.3807 | 7711.0000 |
| 6a | 0.8497 | 0.1503 | 0.3717 | 8489.5000 |
| 6 | 0.9077 | 0.0923 | 0.3673 | 9060.0000 |
| 7 | 0.9687 | 0.0313 | 0.3635 | 9659.2500 |
| 8 | 1.0000 | 0.0000 | 0.3615 | 9966.0000 |

### The ranked never-named pair: D(n) against n beside the random chain's, both keys, both ends
Rank correlation (Spearman, average ranks for ties) between the weight norm and the positive-label count over the never-named set (n = 28946, of which 5336 have count zero): 0.134 (over all subcomponents 0.448), from the pre-reads' rank_keys.parquet.
| key | end | rung | n_erased | D_mean | se | linear_prediction | quadratic_prediction | random_chain_D_mean | random_chain_draw_spread_sd | random_chain_n_erased | random_chain_D_draw_0 | random_chain_n_draw_0 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| weight_norm | top | 1 | 201.0000 | 0.0724 | 0.0014 | 0.0090 | 0.0001 | 0.0060 | 0.0023 | 169.0000 | 0.0074 | 201 |
| weight_norm | top | 2 | 1039.0000 | 0.2326 | 0.0029 | 0.0463 | 0.0017 | 0.0515 | 0.0133 | 1120.6250 | 0.0472 | 1039 |
| weight_norm | top | 3 | 4494.0000 | 0.6824 | 0.0060 | 0.2003 | 0.0311 | 0.2974 | 0.0135 | 4543.6250 | 0.2908 | 4494 |
| weight_norm | top | 4 | 6764.0000 | 0.8548 | 0.0073 | 0.3014 | 0.0704 | 0.3242 | 0.1161 | 4890.2500 | 0.4560 | 6764 |
| weight_norm | top | 5 | 8170.0000 | 0.9718 | 0.0081 | 0.3641 | 0.1028 | 0.5228 | 0.0195 | 7711.0000 | 0.5518 | 8170 |
| weight_norm | top | 6 | 9203.0000 | 1.0293 | 0.0085 | 0.4101 | 0.1304 | 0.6086 | 0.0085 | 9060.0000 | 0.6151 | 9203 |
| weight_norm | top | 7 | 9794.0000 | 1.0527 | 0.0086 | 0.4365 | 0.1477 | 0.6446 | 0.0045 | 9659.2500 | 0.6519 | 9794 |
| weight_norm | top | B50 | 14473.0000 | 1.1740 | 0.0091 | 0.6450 | 0.3225 | 0.8821 | 0.0032 | 14473.0000 | 0.8830 | 14473 |
| weight_norm | top | B75 | 21709.0000 | 1.2605 | 0.0093 | 0.9675 | 0.7256 | 1.1217 | 0.0017 | 21709.0000 | 1.1204 | 21709 |
| weight_norm | bottom | 1 | 201.0000 | 0.0064 | 0.0001 | 0.0090 | 0.0001 | 0.0060 | 0.0023 | 169.0000 | 0.0074 | 201 |
| weight_norm | bottom | 2 | 1039.0000 | 0.0501 | 0.0007 | 0.0463 | 0.0017 | 0.0515 | 0.0133 | 1120.6250 | 0.0472 | 1039 |
| weight_norm | bottom | 3 | 4494.0000 | 0.3453 | 0.0048 | 0.2003 | 0.0311 | 0.2974 | 0.0135 | 4543.6250 | 0.2908 | 4494 |
| weight_norm | bottom | 4 | 6764.0000 | 0.4895 | 0.0059 | 0.3014 | 0.0704 | 0.3242 | 0.1161 | 4890.2500 | 0.4560 | 6764 |
| weight_norm | bottom | 5 | 8170.0000 | 0.6040 | 0.0067 | 0.3641 | 0.1028 | 0.5228 | 0.0195 | 7711.0000 | 0.5518 | 8170 |
| weight_norm | bottom | 6 | 9203.0000 | 0.6425 | 0.0069 | 0.4101 | 0.1304 | 0.6086 | 0.0085 | 9060.0000 | 0.6151 | 9203 |
| weight_norm | bottom | 7 | 9794.0000 | 0.6535 | 0.0069 | 0.4365 | 0.1477 | 0.6446 | 0.0045 | 9659.2500 | 0.6519 | 9794 |
| weight_norm | bottom | B50 | 14473.0000 | 0.8450 | 0.0078 | 0.6450 | 0.3225 | 0.8821 | 0.0032 | 14473.0000 | 0.8830 | 14473 |
| weight_norm | bottom | B75 | 21709.0000 | 1.1032 | 0.0087 | 0.9675 | 0.7256 | 1.1217 | 0.0017 | 21709.0000 | 1.1204 | 21709 |
| positive_count | top | 1 | 201.0000 | 0.0109 | 0.0001 | 0.0090 | 0.0001 | 0.0060 | 0.0023 | 169.0000 | 0.0074 | 201 |
| positive_count | top | 2 | 1039.0000 | 0.0625 | 0.0008 | 0.0463 | 0.0017 | 0.0515 | 0.0133 | 1120.6250 | 0.0472 | 1039 |
| positive_count | top | 3 | 4494.0000 | 0.3527 | 0.0042 | 0.2003 | 0.0311 | 0.2974 | 0.0135 | 4543.6250 | 0.2908 | 4494 |
| positive_count | top | 4 | 6764.0000 | 0.5236 | 0.0056 | 0.3014 | 0.0704 | 0.3242 | 0.1161 | 4890.2500 | 0.4560 | 6764 |
| positive_count | top | 5 | 8170.0000 | 0.6174 | 0.0062 | 0.3641 | 0.1028 | 0.5228 | 0.0195 | 7711.0000 | 0.5518 | 8170 |
| positive_count | top | 6 | 9203.0000 | 0.6786 | 0.0066 | 0.4101 | 0.1304 | 0.6086 | 0.0085 | 9060.0000 | 0.6151 | 9203 |
| positive_count | top | 7 | 9794.0000 | 0.7117 | 0.0068 | 0.4365 | 0.1477 | 0.6446 | 0.0045 | 9659.2500 | 0.6519 | 9794 |
| positive_count | top | B50 | 14473.0000 | 0.9225 | 0.0079 | 0.6450 | 0.3225 | 0.8821 | 0.0032 | 14473.0000 | 0.8830 | 14473 |
| positive_count | top | B75 | 21709.0000 | 1.1376 | 0.0088 | 0.9675 | 0.7256 | 1.1217 | 0.0017 | 21709.0000 | 1.1204 | 21709 |
| positive_count | bottom | 1 | 201.0000 | 0.0068 | 0.0001 | 0.0090 | 0.0001 | 0.0060 | 0.0023 | 169.0000 | 0.0074 | 201 |
| positive_count | bottom | 2 | 1039.0000 | 0.0420 | 0.0006 | 0.0463 | 0.0017 | 0.0515 | 0.0133 | 1120.6250 | 0.0472 | 1039 |
| positive_count | bottom | 3 | 4494.0000 | 0.2655 | 0.0034 | 0.2003 | 0.0311 | 0.2974 | 0.0135 | 4543.6250 | 0.2908 | 4494 |
| positive_count | bottom | 4 | 6764.0000 | 0.4262 | 0.0049 | 0.3014 | 0.0704 | 0.3242 | 0.1161 | 4890.2500 | 0.4560 | 6764 |
| positive_count | bottom | 5 | 8170.0000 | 0.5195 | 0.0056 | 0.3641 | 0.1028 | 0.5228 | 0.0195 | 7711.0000 | 0.5518 | 8170 |
| positive_count | bottom | 6 | 9203.0000 | 0.5816 | 0.0060 | 0.4101 | 0.1304 | 0.6086 | 0.0085 | 9060.0000 | 0.6151 | 9203 |
| positive_count | bottom | 7 | 9794.0000 | 0.6152 | 0.0062 | 0.4365 | 0.1477 | 0.6446 | 0.0045 | 9659.2500 | 0.6519 | 9794 |
| positive_count | bottom | B50 | 14473.0000 | 0.8444 | 0.0075 | 0.6450 | 0.3225 | 0.8821 | 0.0032 | 14473.0000 | 0.8830 | 14473 |
| positive_count | bottom | B75 | 21709.0000 | 1.0923 | 0.0086 | 0.9675 | 0.7256 | 1.1217 | 0.0017 | 21709.0000 | 1.1204 | 21709 |

Top-n minus bottom-n at the same n, paired per sequence (uncorrected 95 percent):
| key | rung | n_erased | top_minus_bottom | interval | half_width |
|---|---|---|---|---|---|
| weight_norm | 1 | 201.0000 | 0.0660 | [+0.0635, +0.0688] | 0.0027 |
| weight_norm | 2 | 1039.0000 | 0.1825 | [+0.1778, +0.1875] | 0.0049 |
| weight_norm | 3 | 4494.0000 | 0.3371 | [+0.3288, +0.3455] | 0.0083 |
| weight_norm | 4 | 6764.0000 | 0.3653 | [+0.3570, +0.3737] | 0.0084 |
| weight_norm | 5 | 8170.0000 | 0.3678 | [+0.3592, +0.3766] | 0.0087 |
| weight_norm | 6 | 9203.0000 | 0.3869 | [+0.3780, +0.3962] | 0.0091 |
| weight_norm | 7 | 9794.0000 | 0.3992 | [+0.3901, +0.4086] | 0.0092 |
| weight_norm | B50 | 14473.0000 | 0.3290 | [+0.3212, +0.3369] | 0.0079 |
| weight_norm | B75 | 21709.0000 | 0.1573 | [+0.1529, +0.1615] | 0.0043 |
| positive_count | 1 | 201.0000 | 0.0041 | [+0.0040, +0.0042] | 0.0001 |
| positive_count | 2 | 1039.0000 | 0.0205 | [+0.0199, +0.0211] | 0.0006 |
| positive_count | 3 | 4494.0000 | 0.0873 | [+0.0849, +0.0897] | 0.0024 |
| positive_count | 4 | 6764.0000 | 0.0973 | [+0.0948, +0.1000] | 0.0026 |
| positive_count | 5 | 8170.0000 | 0.0980 | [+0.0953, +0.1008] | 0.0027 |
| positive_count | 6 | 9203.0000 | 0.0970 | [+0.0943, +0.0998] | 0.0027 |
| positive_count | 7 | 9794.0000 | 0.0965 | [+0.0939, +0.0993] | 0.0027 |
| positive_count | B50 | 14473.0000 | 0.0781 | [+0.0759, +0.0804] | 0.0022 |
| positive_count | B75 | 21709.0000 | 0.0454 | [+0.0440, +0.0468] | 0.0014 |

### Delta gaps per rung (included minus excluded, mean over draws and sequences)
| chain | rung | delta_gap_mean |
|---|---|---|
| never_named_hard/E/D_unif/tau0.1/ones/excl/ctl-none | 8 | -0.0029 |

### E8: hard-zero damage at least soft-erase damage on the same sequences
| chain | rung | soft_erase_chain | delta_settings | fraction_sequences_hard_zero_at_least_soft | mean_hard_zero | mean_soft |
|---|---|---|---|---|---|---|
| hard_zero/E/D_unif/tau0.1/ones/incl/ctl-none | 1 | soft_erase/E/D_unif/tau0.1/r1/excl/ctl-none | differ (each excess over its own rung 0) | 1.0000 | 11.5378 | 0.4362 |
| hard_zero/E/D_unif/tau0.1/ones/incl/ctl-none | 2 | soft_erase/E/D_unif/tau0.1/r1/excl/ctl-none | differ (each excess over its own rung 0) | 1.0000 | 12.3670 | 0.7302 |
| hard_zero/E/D_unif/tau0.1/ones/incl/ctl-none | 3 | soft_erase/E/D_unif/tau0.1/r1/excl/ctl-none | differ (each excess over its own rung 0) | 1.0000 | 11.4629 | 0.4641 |
| hard_zero/E/D_unif/tau0.1/ones/incl/ctl-none | 4 | soft_erase/E/D_unif/tau0.1/r1/excl/ctl-none | differ (each excess over its own rung 0) | 1.0000 | 11.0800 | 0.4486 |
| hard_zero/E/D_unif/tau0.1/ones/incl/ctl-none | 5 | soft_erase/E/D_unif/tau0.1/r1/excl/ctl-none | differ (each excess over its own rung 0) | 1.0000 | 11.0004 | 0.3692 |
| hard_zero/E/D_unif/tau0.1/ones/incl/ctl-none | 5a | soft_erase/E/D_unif/tau0.1/r1/excl/ctl-none | differ (each excess over its own rung 0) | 1.0000 | 11.0008 | 0.3860 |
| hard_zero/E/D_unif/tau0.1/ones/incl/ctl-none | 6 | soft_erase/E/D_unif/tau0.1/r1/excl/ctl-none | differ (each excess over its own rung 0) | 1.0000 | 11.2475 | 0.3558 |
| hard_zero/E/D_unif/tau0.1/ones/incl/ctl-none | 6a | soft_erase/E/D_unif/tau0.1/r1/excl/ctl-none | differ (each excess over its own rung 0) | 1.0000 | 11.1825 | 0.3603 |
| hard_zero/E/D_unif/tau0.1/ones/incl/ctl-none | 7 | soft_erase/E/D_unif/tau0.1/r1/excl/ctl-none | differ (each excess over its own rung 0) | 1.0000 | 11.2893 | 0.3520 |
| hard_zero/E/D_unif/tau0.1/ones/incl/ctl-none | 8 | soft_erase/E/D_unif/tau0.1/r1/excl/ctl-none | differ (each excess over its own rung 0) | 1.0000 | 11.3137 | 0.3501 |
| hard_zero/E/D_unif/tau0.1/ones/incl/ctl-plain | 1 | soft_erase/E/D_unif/tau0.1/r1/excl/ctl-plain | differ (each excess over its own rung 0) | 0.9948 | 1.1202 | 0.0702 |
| hard_zero/E/D_unif/tau0.1/ones/incl/ctl-plain | 2 | soft_erase/E/D_unif/tau0.1/r1/excl/ctl-plain | differ (each excess over its own rung 0) | 1.0000 | 5.3968 | 0.2919 |
| hard_zero/E/D_unif/tau0.1/ones/incl/ctl-plain | 3 | soft_erase/E/D_unif/tau0.1/r1/excl/ctl-plain | differ (each excess over its own rung 0) | 1.0000 | 9.5600 | 0.3543 |
| hard_zero/E/D_unif/tau0.1/ones/incl/ctl-plain | 4 | soft_erase/E/D_unif/tau0.1/r1/excl/ctl-plain | differ (each excess over its own rung 0) | 1.0000 | 8.9393 | 0.3569 |
| hard_zero/E/D_unif/tau0.1/ones/incl/ctl-plain | 5 | soft_erase/E/D_unif/tau0.1/r1/excl/ctl-plain | differ (each excess over its own rung 0) | 1.0000 | 10.0903 | 0.3427 |
| hard_zero/E/D_unif/tau0.1/ones/incl/ctl-plain | 5a | soft_erase/E/D_unif/tau0.1/r1/excl/ctl-plain | differ (each excess over its own rung 0) | 1.0000 | 10.7056 | 0.3447 |
| hard_zero/E/D_unif/tau0.1/ones/incl/ctl-plain | 6 | soft_erase/E/D_unif/tau0.1/r1/excl/ctl-plain | differ (each excess over its own rung 0) | 1.0000 | 10.8391 | 0.3475 |
| hard_zero/E/D_unif/tau0.1/ones/incl/ctl-plain | 6a | soft_erase/E/D_unif/tau0.1/r1/excl/ctl-plain | differ (each excess over its own rung 0) | 1.0000 | 10.3834 | 0.3453 |
| hard_zero/E/D_unif/tau0.1/ones/incl/ctl-plain | 7 | soft_erase/E/D_unif/tau0.1/r1/excl/ctl-plain | differ (each excess over its own rung 0) | 1.0000 | 10.4650 | 0.3495 |
| hard_zero/E/D_unif/tau0.1/ones/incl/ctl-plain | 8 | soft_erase/E/D_unif/tau0.1/r1/excl/ctl-plain | differ (each excess over its own rung 0) | 1.0000 | 11.3324 | 0.3500 |
| hard_zero/E_lab/D_code/tau0.1/ones/incl/ctl-none | 1 | soft_erase/E_lab/D_code/tau0.1/r1/excl/ctl-none | differ (each excess over its own rung 0) | 1.0000 | 11.6786 | 0.4688 |
| hard_zero/E_lab/D_code/tau0.1/ones/incl/ctl-none | 2 | soft_erase/E_lab/D_code/tau0.1/r1/excl/ctl-none | differ (each excess over its own rung 0) | 1.0000 | 12.5123 | 0.7261 |
| hard_zero/E_lab/D_code/tau0.1/ones/incl/ctl-none | 3 | soft_erase/E_lab/D_code/tau0.1/r1/excl/ctl-none | differ (each excess over its own rung 0) | 1.0000 | 11.5381 | 0.4936 |
| hard_zero/E_lab/D_code/tau0.1/ones/incl/ctl-none | 4 | soft_erase/E_lab/D_code/tau0.1/r1/excl/ctl-none | differ (each excess over its own rung 0) | 1.0000 | 11.3994 | 0.4028 |
| hard_zero/E_lab/D_code/tau0.1/ones/incl/ctl-none | 5 | soft_erase/E_lab/D_code/tau0.1/r1/excl/ctl-none | differ (each excess over its own rung 0) | 1.0000 | 11.4045 | 0.3633 |
| hard_zero/E_lab/D_code/tau0.1/ones/incl/ctl-none | 5a | soft_erase/E_lab/D_code/tau0.1/r1/excl/ctl-none | differ (each excess over its own rung 0) | 1.0000 | 11.4018 | 0.3800 |
| hard_zero/E_lab/D_code/tau0.1/ones/incl/ctl-none | 6 | soft_erase/E_lab/D_code/tau0.1/r1/excl/ctl-none | differ (each excess over its own rung 0) | 1.0000 | 11.5729 | 0.3526 |
| hard_zero/E_lab/D_code/tau0.1/ones/incl/ctl-none | 6a | soft_erase/E_lab/D_code/tau0.1/r1/excl/ctl-none | differ (each excess over its own rung 0) | 1.0000 | 11.4765 | 0.3559 |
| hard_zero/E_lab/D_code/tau0.1/ones/incl/ctl-none | 7 | soft_erase/E_lab/D_code/tau0.1/r1/excl/ctl-none | differ (each excess over its own rung 0) | 1.0000 | 11.6047 | 0.3489 |
| hard_zero/E_lab/D_code/tau0.1/ones/incl/ctl-none | 8 | soft_erase/E_lab/D_code/tau0.1/r1/excl/ctl-none | differ (each excess over its own rung 0) | 1.0000 | 11.6658 | 0.3463 |
| code_specific_hard/E_lab/D_code/tau0.1/ones/incl/ctl-none | 1 | code_specific_soft/E_lab/D_code/tau0.1/r1/excl/ctl-none | differ (each excess over its own rung 0) | 0.9478 | 0.0001 | 0.0000 |
| code_specific_hard/E_lab/D_code/tau0.1/ones/incl/ctl-none | 2 | code_specific_soft/E_lab/D_code/tau0.1/r1/excl/ctl-none | differ (each excess over its own rung 0) | 0.8000 | 0.0009 | 0.0002 |
| code_specific_hard/E_lab/D_code/tau0.1/ones/incl/ctl-none | 3 | code_specific_soft/E_lab/D_code/tau0.1/r1/excl/ctl-none | differ (each excess over its own rung 0) | 0.6436 | 0.0040 | 0.0011 |
| code_specific_hard/E_lab/D_code/tau0.1/ones/incl/ctl-none | 4 | code_specific_soft/E_lab/D_code/tau0.1/r1/excl/ctl-none | differ (each excess over its own rung 0) | 0.6787 | 0.0055 | 0.0016 |
| code_specific_hard/E_lab/D_code/tau0.1/ones/incl/ctl-none | 5 | code_specific_soft/E_lab/D_code/tau0.1/r1/excl/ctl-none | differ (each excess over its own rung 0) | 0.7012 | 0.0100 | 0.0037 |
| code_specific_hard/E_lab/D_code/tau0.1/ones/incl/ctl-none | 5a | code_specific_soft/E_lab/D_code/tau0.1/r1/excl/ctl-none | differ (each excess over its own rung 0) | 0.6926 | 0.0076 | 0.0023 |
| code_specific_hard/E_lab/D_code/tau0.1/ones/incl/ctl-none | 6 | code_specific_soft/E_lab/D_code/tau0.1/r1/excl/ctl-none | differ (each excess over its own rung 0) | 0.7632 | 0.0145 | 0.0070 |
| code_specific_hard/E_lab/D_code/tau0.1/ones/incl/ctl-none | 6a | code_specific_soft/E_lab/D_code/tau0.1/r1/excl/ctl-none | differ (each excess over its own rung 0) | 0.7271 | 0.0125 | 0.0054 |
| code_specific_hard/E_lab/D_code/tau0.1/ones/incl/ctl-none | 7 | code_specific_soft/E_lab/D_code/tau0.1/r1/excl/ctl-none | differ (each excess over its own rung 0) | 0.7458 | 0.0187 | 0.0108 |
| code_specific_hard/E_lab/D_code/tau0.1/ones/incl/ctl-none | 8 | code_specific_soft/E_lab/D_code/tau0.1/r1/excl/ctl-none | differ (each excess over its own rung 0) | 0.6250 | 0.0321 | 0.0241 |
| hard_zero/E_lab/D_code/tau0.1/ones/incl/ctl-plain | 1 | soft_erase/E_lab/D_code/tau0.1/r1/excl/ctl-plain | differ (each excess over its own rung 0) | 1.0000 | 1.2072 | 0.0932 |
| hard_zero/E_lab/D_code/tau0.1/ones/incl/ctl-plain | 2 | soft_erase/E_lab/D_code/tau0.1/r1/excl/ctl-plain | differ (each excess over its own rung 0) | 1.0000 | 5.6047 | 0.2897 |
| hard_zero/E_lab/D_code/tau0.1/ones/incl/ctl-plain | 3 | soft_erase/E_lab/D_code/tau0.1/r1/excl/ctl-plain | differ (each excess over its own rung 0) | 1.0000 | 9.1254 | 0.3767 |
| hard_zero/E_lab/D_code/tau0.1/ones/incl/ctl-plain | 4 | soft_erase/E_lab/D_code/tau0.1/r1/excl/ctl-plain | differ (each excess over its own rung 0) | 1.0000 | 10.2470 | 0.3578 |
| hard_zero/E_lab/D_code/tau0.1/ones/incl/ctl-plain | 5 | soft_erase/E_lab/D_code/tau0.1/r1/excl/ctl-plain | differ (each excess over its own rung 0) | 1.0000 | 10.9381 | 0.3408 |
| hard_zero/E_lab/D_code/tau0.1/ones/incl/ctl-plain | 5a | soft_erase/E_lab/D_code/tau0.1/r1/excl/ctl-plain | differ (each excess over its own rung 0) | 1.0000 | 10.9350 | 0.3457 |
| hard_zero/E_lab/D_code/tau0.1/ones/incl/ctl-plain | 6 | soft_erase/E_lab/D_code/tau0.1/r1/excl/ctl-plain | differ (each excess over its own rung 0) | 1.0000 | 11.0749 | 0.3404 |
| hard_zero/E_lab/D_code/tau0.1/ones/incl/ctl-plain | 6a | soft_erase/E_lab/D_code/tau0.1/r1/excl/ctl-plain | differ (each excess over its own rung 0) | 1.0000 | 11.0713 | 0.3405 |
| hard_zero/E_lab/D_code/tau0.1/ones/incl/ctl-plain | 7 | soft_erase/E_lab/D_code/tau0.1/r1/excl/ctl-plain | differ (each excess over its own rung 0) | 1.0000 | 11.0930 | 0.3426 |
| hard_zero/E_lab/D_code/tau0.1/ones/incl/ctl-plain | 8 | soft_erase/E_lab/D_code/tau0.1/r1/excl/ctl-plain | differ (each excess over its own rung 0) | 1.0000 | 11.8807 | 0.3431 |

### The donor-side pass (excess over the rounded reference on the donor sequences)
union/D_unif/tau0.1/r0/excl/k0/r4: +1.2140 (se nan); union/D_unif/tau0.1/r0/excl/k0/r7: +1.0176 (se 0.0405); union/D_unif/tau0.1/r0/excl/k1/r4: +1.2039 (se nan); union/D_unif/tau0.1/r0/excl/k1/r7: +0.9543 (se 0.0390); union/D_unif/tau0.1/r0/excl/k2/r4: +1.1014 (se nan); union/D_unif/tau0.1/r0/excl/k2/r7: +1.0302 (se 0.0399); union/D_unif/tau0.1/r0/excl/k3/r4: +0.1371 (se nan); union/D_unif/tau0.1/r0/excl/k3/r7: +0.9659 (se 0.0412); union/D_unif/tau0.1/r0/excl/k4/r4: +1.7075 (se nan); union/D_unif/tau0.1/r0/excl/k4/r7: +0.9955 (se 0.0358); union/D_unif/tau0.1/r0/excl/k5/r4: +2.2445 (se nan); union/D_unif/tau0.1/r0/excl/k5/r7: +1.0269 (se 0.0416); union/D_unif/tau0.1/r0/excl/k6/r4: +0.9305 (se nan); union/D_unif/tau0.1/r0/excl/k6/r7: +0.9780 (se 0.0385); union/D_unif/tau0.1/r0/excl/k7/r4: +0.7064 (se nan); union/D_unif/tau0.1/r0/excl/k7/r7: +0.9075 (se 0.0390)

### The domain comparisons per stratum: the erase against its own control, paired on the sequence with the stratum's resample; never averaged over strata
| chain | rung | stratum | n | erase_unconditional | control_unconditional | paired_erase_minus_control | interval | conditional_d_0.1 | n_contributing_mean |
|---|---|---|---|---|---|---|---|---|---|
| hard_zero/E_lab/D_code/tau0.1/ones/incl/ctl-none | 1 | Github | 256 | 12.1597 | 1.2952 | 10.8645 | [+10.6755, +11.0409] |  | 0.0000 |
| hard_zero/E_lab/D_code/tau0.1/ones/incl/ctl-none | 1 | other | 256 | 11.1976 | 1.1192 | 10.0784 | [+9.9789, +10.1772] |  | 0.0000 |
| hard_zero/E_lab/D_code/tau0.1/ones/incl/ctl-none | 1 | ArXiv | 64 | 11.8995 | 1.1376 | 10.7618 | [+10.6209, +10.9018] |  | 0.0000 |
| hard_zero/E_lab/D_code/tau0.1/ones/incl/ctl-none | 1 | Pile-CC | 64 | 10.4798 | 1.0838 | 9.3960 | [+9.3109, +9.4816] |  | 0.0000 |
| hard_zero/E_lab/D_code/tau0.1/ones/incl/ctl-none | 1 | StackExchange | 64 | 11.8051 | 1.1013 | 10.7038 | [+10.5656, +10.8404] |  | 0.0000 |
| hard_zero/E_lab/D_code/tau0.1/ones/incl/ctl-none | 1 | Wikipedia (en) | 64 | 10.6059 | 1.1540 | 9.4519 | [+9.3604, +9.5464] |  | 0.0000 |
| hard_zero/E_lab/D_code/tau0.1/ones/incl/ctl-none | 2 | Github | 256 | 13.4082 | 6.0747 | 7.3335 | [+7.1750, +7.4848] |  | 0.0000 |
| hard_zero/E_lab/D_code/tau0.1/ones/incl/ctl-none | 2 | other | 256 | 11.6165 | 5.1346 | 6.4819 | [+6.3699, +6.5944] |  | 0.0000 |
| hard_zero/E_lab/D_code/tau0.1/ones/incl/ctl-none | 2 | ArXiv | 64 | 12.6151 | 5.2918 | 7.3233 | [+7.1567, +7.4879] |  | 0.0000 |
| hard_zero/E_lab/D_code/tau0.1/ones/incl/ctl-none | 2 | Pile-CC | 64 | 10.4132 | 4.6794 | 5.7338 | [+5.6258, +5.8443] |  | 0.0000 |
| hard_zero/E_lab/D_code/tau0.1/ones/incl/ctl-none | 2 | StackExchange | 64 | 12.6031 | 5.5046 | 7.0986 | [+6.9404, +7.2529] |  | 0.0000 |
| hard_zero/E_lab/D_code/tau0.1/ones/incl/ctl-none | 2 | Wikipedia (en) | 64 | 10.8345 | 5.0626 | 5.7719 | [+5.6653, +5.8780] |  | 0.0000 |
| hard_zero/E_lab/D_code/tau0.1/ones/incl/ctl-none | 3 | Github | 256 | 11.9384 | 9.8377 | 2.1007 | [+1.9946, +2.2003] |  | 0.0000 |
| hard_zero/E_lab/D_code/tau0.1/ones/incl/ctl-none | 3 | other | 256 | 11.1378 | 8.4130 | 2.7248 | [+2.6791, +2.7706] |  | 0.0000 |
| hard_zero/E_lab/D_code/tau0.1/ones/incl/ctl-none | 3 | ArXiv | 64 | 11.7374 | 8.8548 | 2.8826 | [+2.7981, +2.9675] |  | 0.0000 |
| hard_zero/E_lab/D_code/tau0.1/ones/incl/ctl-none | 3 | Pile-CC | 64 | 10.5197 | 7.7987 | 2.7210 | [+2.6557, +2.7862] |  | 0.0000 |
| hard_zero/E_lab/D_code/tau0.1/ones/incl/ctl-none | 3 | StackExchange | 64 | 11.5620 | 8.7935 | 2.7684 | [+2.6467, +2.8834] |  | 0.0000 |
| hard_zero/E_lab/D_code/tau0.1/ones/incl/ctl-none | 3 | Wikipedia (en) | 64 | 10.7321 | 8.2049 | 2.5272 | [+2.4688, +2.5833] |  | 0.0000 |
| hard_zero/E_lab/D_code/tau0.1/ones/incl/ctl-none | 4 | Github | 256 | 12.0472 | 10.8234 | 1.2239 | [+1.1688, +1.2784] |  | 0.0000 |
| hard_zero/E_lab/D_code/tau0.1/ones/incl/ctl-none | 4 | other | 256 | 10.7515 | 9.6706 | 1.0810 | [+1.0317, +1.1329] |  | 0.0000 |
| hard_zero/E_lab/D_code/tau0.1/ones/incl/ctl-none | 4 | ArXiv | 64 | 11.5087 | 10.0075 | 1.5012 | [+1.4142, +1.5906] |  | 0.0000 |
| hard_zero/E_lab/D_code/tau0.1/ones/incl/ctl-none | 4 | Pile-CC | 64 | 9.9455 | 9.1463 | 0.7992 | [+0.7470, +0.8520] |  | 0.0000 |
| hard_zero/E_lab/D_code/tau0.1/ones/incl/ctl-none | 4 | StackExchange | 64 | 11.2849 | 10.0265 | 1.2584 | [+1.1830, +1.3359] |  | 0.0000 |
| hard_zero/E_lab/D_code/tau0.1/ones/incl/ctl-none | 4 | Wikipedia (en) | 64 | 10.2671 | 9.5020 | 0.7651 | [+0.7141, +0.8179] |  | 0.0000 |
| hard_zero/E_lab/D_code/tau0.1/ones/incl/ctl-none | 5a | Github | 256 | 12.0663 | 11.5642 | 0.5020 | [+0.4598, +0.5449] |  | 0.0000 |
| hard_zero/E_lab/D_code/tau0.1/ones/incl/ctl-none | 5a | other | 256 | 10.7373 | 10.3059 | 0.4315 | [+0.3881, +0.4774] |  | 0.0000 |
| hard_zero/E_lab/D_code/tau0.1/ones/incl/ctl-none | 5a | ArXiv | 64 | 11.4172 | 10.6700 | 0.7472 | [+0.6581, +0.8365] |  | 0.0000 |
| hard_zero/E_lab/D_code/tau0.1/ones/incl/ctl-none | 5a | Pile-CC | 64 | 9.9188 | 9.7171 | 0.2018 | [+0.1308, +0.2733] |  | 0.0000 |
| hard_zero/E_lab/D_code/tau0.1/ones/incl/ctl-none | 5a | StackExchange | 64 | 11.2437 | 10.7833 | 0.4604 | [+0.3780, +0.5449] |  | 0.0000 |
| hard_zero/E_lab/D_code/tau0.1/ones/incl/ctl-none | 5a | Wikipedia (en) | 64 | 10.3697 | 10.0530 | 0.3167 | [+0.2673, +0.3675] |  | 0.0000 |
| hard_zero/E_lab/D_code/tau0.1/ones/incl/ctl-none | 5 | Github | 256 | 12.0058 | 11.5273 | 0.4785 | [+0.4263, +0.5297] |  | 0.0000 |
| hard_zero/E_lab/D_code/tau0.1/ones/incl/ctl-none | 5 | other | 256 | 10.8032 | 10.3490 | 0.4542 | [+0.4094, +0.5001] |  | 0.0000 |
| hard_zero/E_lab/D_code/tau0.1/ones/incl/ctl-none | 5 | ArXiv | 64 | 11.3724 | 10.7483 | 0.6242 | [+0.5450, +0.6998] |  | 0.0000 |
| hard_zero/E_lab/D_code/tau0.1/ones/incl/ctl-none | 5 | Pile-CC | 64 | 10.0852 | 9.7885 | 0.2968 | [+0.2081, +0.3834] |  | 0.0000 |
| hard_zero/E_lab/D_code/tau0.1/ones/incl/ctl-none | 5 | StackExchange | 64 | 11.2275 | 10.6859 | 0.5416 | [+0.4447, +0.6402] |  | 0.0000 |
| hard_zero/E_lab/D_code/tau0.1/ones/incl/ctl-none | 5 | Wikipedia (en) | 64 | 10.5277 | 10.1734 | 0.3543 | [+0.2766, +0.4297] |  | 0.0000 |
| hard_zero/E_lab/D_code/tau0.1/ones/incl/ctl-none | 6a | Github | 256 | 12.0263 | 11.6445 | 0.3818 | [+0.3239, +0.4391] |  | 0.0000 |
| hard_zero/E_lab/D_code/tau0.1/ones/incl/ctl-none | 6a | other | 256 | 10.9266 | 10.4982 | 0.4284 | [+0.3856, +0.4712] |  | 0.0000 |
| hard_zero/E_lab/D_code/tau0.1/ones/incl/ctl-none | 6a | ArXiv | 64 | 11.4951 | 10.9670 | 0.5282 | [+0.4473, +0.6074] |  | 0.0000 |
| hard_zero/E_lab/D_code/tau0.1/ones/incl/ctl-none | 6a | Pile-CC | 64 | 10.2565 | 9.9039 | 0.3526 | [+0.2715, +0.4334] |  | 0.0000 |
| hard_zero/E_lab/D_code/tau0.1/ones/incl/ctl-none | 6a | StackExchange | 64 | 11.2801 | 10.8480 | 0.4321 | [+0.3240, +0.5360] |  | 0.0000 |
| hard_zero/E_lab/D_code/tau0.1/ones/incl/ctl-none | 6a | Wikipedia (en) | 64 | 10.6746 | 10.2739 | 0.4007 | [+0.3253, +0.4748] |  | 0.0000 |
| hard_zero/E_lab/D_code/tau0.1/ones/incl/ctl-none | 6 | Github | 256 | 12.1124 | 11.6264 | 0.4860 | [+0.4225, +0.5494] |  | 0.0000 |
| hard_zero/E_lab/D_code/tau0.1/ones/incl/ctl-none | 6 | other | 256 | 11.0333 | 10.5235 | 0.5098 | [+0.4695, +0.5509] |  | 0.0000 |
| hard_zero/E_lab/D_code/tau0.1/ones/incl/ctl-none | 6 | ArXiv | 64 | 11.6281 | 10.9935 | 0.6346 | [+0.5616, +0.7046] |  | 0.0000 |
| hard_zero/E_lab/D_code/tau0.1/ones/incl/ctl-none | 6 | Pile-CC | 64 | 10.3779 | 9.9366 | 0.4412 | [+0.3674, +0.5131] |  | 0.0000 |
| hard_zero/E_lab/D_code/tau0.1/ones/incl/ctl-none | 6 | StackExchange | 64 | 11.3498 | 10.8344 | 0.5154 | [+0.4081, +0.6184] |  | 0.0000 |
| hard_zero/E_lab/D_code/tau0.1/ones/incl/ctl-none | 6 | Wikipedia (en) | 64 | 10.7775 | 10.3295 | 0.4479 | [+0.3796, +0.5137] |  | 0.0000 |
| hard_zero/E_lab/D_code/tau0.1/ones/incl/ctl-none | 7 | Github | 256 | 12.1797 | 11.6547 | 0.5250 | [+0.4637, +0.5866] |  | 0.0000 |
| hard_zero/E_lab/D_code/tau0.1/ones/incl/ctl-none | 7 | other | 256 | 11.0298 | 10.5312 | 0.4985 | [+0.4585, +0.5396] |  | 0.0000 |
| hard_zero/E_lab/D_code/tau0.1/ones/incl/ctl-none | 7 | ArXiv | 64 | 11.6910 | 10.9910 | 0.7000 | [+0.6334, +0.7668] |  | 0.0000 |
| hard_zero/E_lab/D_code/tau0.1/ones/incl/ctl-none | 7 | Pile-CC | 64 | 10.3307 | 9.9442 | 0.3865 | [+0.3181, +0.4545] |  | 0.0000 |
| hard_zero/E_lab/D_code/tau0.1/ones/incl/ctl-none | 7 | StackExchange | 64 | 11.3590 | 10.8768 | 0.4822 | [+0.3794, +0.5847] |  | 0.0000 |
| hard_zero/E_lab/D_code/tau0.1/ones/incl/ctl-none | 7 | Wikipedia (en) | 64 | 10.7385 | 10.3131 | 0.4254 | [+0.3651, +0.4827] |  | 0.0000 |
| hard_zero/E_lab/D_code/tau0.1/ones/incl/ctl-none | 8 | Github | 256 | 12.2416 | 12.4386 | -0.1970 | [-0.2377, -0.1566] |  | 0.0000 |
| hard_zero/E_lab/D_code/tau0.1/ones/incl/ctl-none | 8 | other | 256 | 11.0900 | 11.3229 | -0.2330 | [-0.2648, -0.2014] |  | 0.0000 |
| hard_zero/E_lab/D_code/tau0.1/ones/incl/ctl-none | 8 | ArXiv | 64 | 11.7045 | 11.8397 | -0.1353 | [-0.1817, -0.0905] |  | 0.0000 |
| hard_zero/E_lab/D_code/tau0.1/ones/incl/ctl-none | 8 | Pile-CC | 64 | 10.3808 | 10.6663 | -0.2855 | [-0.3426, -0.2276] |  | 0.0000 |
| hard_zero/E_lab/D_code/tau0.1/ones/incl/ctl-none | 8 | StackExchange | 64 | 11.4581 | 11.7789 | -0.3209 | [-0.4017, -0.2342] |  | 0.0000 |
| hard_zero/E_lab/D_code/tau0.1/ones/incl/ctl-none | 8 | Wikipedia (en) | 64 | 10.8165 | 11.0067 | -0.1902 | [-0.2382, -0.1416] |  | 0.0000 |
| code_specific_hard/E_lab/D_code/tau0.1/ones/incl/ctl-none | 1 | Github | 256 | 0.0001 | 0.0000 | 0.0001 | [+0.0001, +0.0001] | 0.0000 | 254.5000 |
| code_specific_hard/E_lab/D_code/tau0.1/ones/incl/ctl-none | 1 | other | 256 | 0.0000 | 0.0000 | 0.0000 | [+0.0000, +0.0000] | 0.0000 | 255.5000 |
| code_specific_hard/E_lab/D_code/tau0.1/ones/incl/ctl-none | 1 | ArXiv | 64 | 0.0000 | 0.0000 | 0.0000 | [+0.0000, +0.0000] | 0.0000 | 63.6250 |
| code_specific_hard/E_lab/D_code/tau0.1/ones/incl/ctl-none | 1 | Pile-CC | 64 | 0.0000 | 0.0000 | 0.0000 | [+0.0000, +0.0000] | 0.0000 | 64.0000 |
| code_specific_hard/E_lab/D_code/tau0.1/ones/incl/ctl-none | 1 | StackExchange | 64 | 0.0000 | 0.0000 | 0.0000 | [+0.0000, +0.0001] | 0.0000 | 63.8750 |
| code_specific_hard/E_lab/D_code/tau0.1/ones/incl/ctl-none | 1 | Wikipedia (en) | 64 | 0.0000 | 0.0000 | 0.0000 | [+0.0000, +0.0000] | 0.0000 | 64.0000 |
| code_specific_hard/E_lab/D_code/tau0.1/ones/incl/ctl-none | 2 | Github | 256 | 0.0014 | 0.0020 | -0.0005 | [-0.0007, -0.0004] | 0.0002 | 243.0000 |
| code_specific_hard/E_lab/D_code/tau0.1/ones/incl/ctl-none | 2 | other | 256 | 0.0003 | 0.0005 | -0.0002 | [-0.0002, -0.0001] | 0.0001 | 254.1250 |
| code_specific_hard/E_lab/D_code/tau0.1/ones/incl/ctl-none | 2 | ArXiv | 64 | 0.0000 | 0.0001 | -0.0001 | [-0.0001, -0.0000] | 0.0000 | 63.6250 |
| code_specific_hard/E_lab/D_code/tau0.1/ones/incl/ctl-none | 2 | Pile-CC | 64 | 0.0000 | 0.0000 | -0.0000 | [-0.0000, +0.0000] | 0.0000 | 64.0000 |
| code_specific_hard/E_lab/D_code/tau0.1/ones/incl/ctl-none | 2 | StackExchange | 64 | 0.0011 | 0.0016 | -0.0006 | [-0.0008, -0.0004] | 0.0001 | 62.5000 |
| code_specific_hard/E_lab/D_code/tau0.1/ones/incl/ctl-none | 2 | Wikipedia (en) | 64 | 0.0001 | 0.0001 | -0.0000 | [-0.0000, -0.0000] | 0.0001 | 64.0000 |
| code_specific_hard/E_lab/D_code/tau0.1/ones/incl/ctl-none | 3 | Github | 256 | 0.0066 | 0.0056 | 0.0010 | [+0.0009, +0.0011] | 0.0010 | 210.2500 |
| code_specific_hard/E_lab/D_code/tau0.1/ones/incl/ctl-none | 3 | other | 256 | 0.0014 | 0.0013 | 0.0001 | [+0.0001, +0.0002] | 0.0003 | 247.2500 |
| code_specific_hard/E_lab/D_code/tau0.1/ones/incl/ctl-none | 3 | ArXiv | 64 | 0.0002 | 0.0003 | -0.0001 | [-0.0001, -0.0000] | 0.0002 | 62.6250 |
| code_specific_hard/E_lab/D_code/tau0.1/ones/incl/ctl-none | 3 | Pile-CC | 64 | 0.0002 | 0.0002 | 0.0000 | [+0.0000, +0.0000] | 0.0002 | 64.0000 |
| code_specific_hard/E_lab/D_code/tau0.1/ones/incl/ctl-none | 3 | StackExchange | 64 | 0.0050 | 0.0045 | 0.0005 | [+0.0003, +0.0007] | 0.0006 | 56.6250 |
| code_specific_hard/E_lab/D_code/tau0.1/ones/incl/ctl-none | 3 | Wikipedia (en) | 64 | 0.0003 | 0.0002 | 0.0000 | [+0.0000, +0.0000] | 0.0003 | 64.0000 |
| code_specific_hard/E_lab/D_code/tau0.1/ones/incl/ctl-none | 4 | Github | 256 | 0.0091 | 0.0067 | 0.0024 | [+0.0021, +0.0027] | 0.0016 | 190.6250 |
| code_specific_hard/E_lab/D_code/tau0.1/ones/incl/ctl-none | 4 | other | 256 | 0.0020 | 0.0015 | 0.0004 | [+0.0003, +0.0006] | 0.0006 | 243.0000 |
| code_specific_hard/E_lab/D_code/tau0.1/ones/incl/ctl-none | 4 | ArXiv | 64 | 0.0005 | 0.0006 | -0.0001 | [-0.0002, -0.0001] | 0.0004 | 61.1250 |
| code_specific_hard/E_lab/D_code/tau0.1/ones/incl/ctl-none | 4 | Pile-CC | 64 | 0.0004 | 0.0003 | 0.0001 | [+0.0001, +0.0001] | 0.0004 | 63.8750 |
| code_specific_hard/E_lab/D_code/tau0.1/ones/incl/ctl-none | 4 | StackExchange | 64 | 0.0064 | 0.0048 | 0.0016 | [+0.0011, +0.0020] | 0.0010 | 54.2500 |
| code_specific_hard/E_lab/D_code/tau0.1/ones/incl/ctl-none | 4 | Wikipedia (en) | 64 | 0.0005 | 0.0004 | 0.0001 | [+0.0001, +0.0001] | 0.0005 | 63.7500 |
| code_specific_hard/E_lab/D_code/tau0.1/ones/incl/ctl-none | 5a | Github | 256 | 0.0125 | 0.0107 | 0.0018 | [+0.0015, +0.0022] | 0.0024 | 173.5000 |
| code_specific_hard/E_lab/D_code/tau0.1/ones/incl/ctl-none | 5a | other | 256 | 0.0027 | 0.0026 | 0.0001 | [+0.0001, +0.0002] | 0.0009 | 239.1250 |
| code_specific_hard/E_lab/D_code/tau0.1/ones/incl/ctl-none | 5a | ArXiv | 64 | 0.0007 | 0.0009 | -0.0002 | [-0.0002, -0.0001] | 0.0007 | 59.5000 |
| code_specific_hard/E_lab/D_code/tau0.1/ones/incl/ctl-none | 5a | Pile-CC | 64 | 0.0007 | 0.0006 | 0.0001 | [+0.0001, +0.0001] | 0.0007 | 63.8750 |
| code_specific_hard/E_lab/D_code/tau0.1/ones/incl/ctl-none | 5a | StackExchange | 64 | 0.0087 | 0.0082 | 0.0005 | [+0.0002, +0.0008] | 0.0014 | 52.0000 |
| code_specific_hard/E_lab/D_code/tau0.1/ones/incl/ctl-none | 5a | Wikipedia (en) | 64 | 0.0009 | 0.0007 | 0.0001 | [+0.0001, +0.0002] | 0.0008 | 63.7500 |
| code_specific_hard/E_lab/D_code/tau0.1/ones/incl/ctl-none | 5 | Github | 256 | 0.0159 | 0.0127 | 0.0032 | [+0.0028, +0.0035] | 0.0043 | 158.0000 |
| code_specific_hard/E_lab/D_code/tau0.1/ones/incl/ctl-none | 5 | other | 256 | 0.0041 | 0.0037 | 0.0005 | [+0.0003, +0.0006] | 0.0018 | 231.0000 |
| code_specific_hard/E_lab/D_code/tau0.1/ones/incl/ctl-none | 5 | ArXiv | 64 | 0.0019 | 0.0020 | -0.0001 | [-0.0002, +0.0000] | 0.0015 | 55.2500 |
| code_specific_hard/E_lab/D_code/tau0.1/ones/incl/ctl-none | 5 | Pile-CC | 64 | 0.0015 | 0.0014 | 0.0001 | [+0.0001, +0.0001] | 0.0015 | 63.5000 |
| code_specific_hard/E_lab/D_code/tau0.1/ones/incl/ctl-none | 5 | StackExchange | 64 | 0.0112 | 0.0096 | 0.0016 | [+0.0011, +0.0022] | 0.0024 | 48.6250 |
| code_specific_hard/E_lab/D_code/tau0.1/ones/incl/ctl-none | 5 | Wikipedia (en) | 64 | 0.0018 | 0.0017 | 0.0002 | [+0.0001, +0.0002] | 0.0018 | 63.6250 |
| code_specific_hard/E_lab/D_code/tau0.1/ones/incl/ctl-none | 6a | Github | 256 | 0.0193 | 0.0155 | 0.0039 | [+0.0035, +0.0043] | 0.0062 | 147.6250 |
| code_specific_hard/E_lab/D_code/tau0.1/ones/incl/ctl-none | 6a | other | 256 | 0.0057 | 0.0049 | 0.0008 | [+0.0006, +0.0010] | 0.0028 | 221.5000 |
| code_specific_hard/E_lab/D_code/tau0.1/ones/incl/ctl-none | 6a | ArXiv | 64 | 0.0036 | 0.0031 | 0.0004 | [+0.0002, +0.0007] | 0.0024 | 47.5000 |
| code_specific_hard/E_lab/D_code/tau0.1/ones/incl/ctl-none | 6a | Pile-CC | 64 | 0.0024 | 0.0022 | 0.0002 | [+0.0002, +0.0003] | 0.0024 | 63.3750 |
| code_specific_hard/E_lab/D_code/tau0.1/ones/incl/ctl-none | 6a | StackExchange | 64 | 0.0138 | 0.0117 | 0.0021 | [+0.0015, +0.0027] | 0.0036 | 47.0000 |
| code_specific_hard/E_lab/D_code/tau0.1/ones/incl/ctl-none | 6a | Wikipedia (en) | 64 | 0.0030 | 0.0027 | 0.0003 | [+0.0002, +0.0004] | 0.0029 | 63.6250 |
| code_specific_hard/E_lab/D_code/tau0.1/ones/incl/ctl-none | 6 | Github | 256 | 0.0219 | 0.0171 | 0.0048 | [+0.0043, +0.0053] | 0.0083 | 141.7500 |
| code_specific_hard/E_lab/D_code/tau0.1/ones/incl/ctl-none | 6 | other | 256 | 0.0071 | 0.0061 | 0.0010 | [+0.0008, +0.0013] | 0.0040 | 217.0000 |
| code_specific_hard/E_lab/D_code/tau0.1/ones/incl/ctl-none | 6 | ArXiv | 64 | 0.0051 | 0.0043 | 0.0008 | [+0.0005, +0.0012] | 0.0034 | 44.5000 |
| code_specific_hard/E_lab/D_code/tau0.1/ones/incl/ctl-none | 6 | Pile-CC | 64 | 0.0035 | 0.0032 | 0.0003 | [+0.0002, +0.0004] | 0.0034 | 63.1250 |
| code_specific_hard/E_lab/D_code/tau0.1/ones/incl/ctl-none | 6 | StackExchange | 64 | 0.0157 | 0.0131 | 0.0026 | [+0.0019, +0.0034] | 0.0050 | 45.7500 |
| code_specific_hard/E_lab/D_code/tau0.1/ones/incl/ctl-none | 6 | Wikipedia (en) | 64 | 0.0042 | 0.0038 | 0.0004 | [+0.0003, +0.0005] | 0.0041 | 63.6250 |
| code_specific_hard/E_lab/D_code/tau0.1/ones/incl/ctl-none | 7 | Github | 256 | 0.0271 | 0.0218 | 0.0053 | [+0.0047, +0.0059] | 0.0137 | 135.3750 |
| code_specific_hard/E_lab/D_code/tau0.1/ones/incl/ctl-none | 7 | other | 256 | 0.0103 | 0.0092 | 0.0011 | [+0.0009, +0.0014] | 0.0068 | 212.1250 |
| code_specific_hard/E_lab/D_code/tau0.1/ones/incl/ctl-none | 7 | ArXiv | 64 | 0.0084 | 0.0073 | 0.0010 | [+0.0004, +0.0016] | 0.0059 | 42.7500 |
| code_specific_hard/E_lab/D_code/tau0.1/ones/incl/ctl-none | 7 | Pile-CC | 64 | 0.0061 | 0.0058 | 0.0003 | [+0.0003, +0.0004] | 0.0061 | 62.3750 |
| code_specific_hard/E_lab/D_code/tau0.1/ones/incl/ctl-none | 7 | StackExchange | 64 | 0.0196 | 0.0169 | 0.0027 | [+0.0020, +0.0035] | 0.0082 | 44.1250 |
| code_specific_hard/E_lab/D_code/tau0.1/ones/incl/ctl-none | 7 | Wikipedia (en) | 64 | 0.0073 | 0.0068 | 0.0004 | [+0.0002, +0.0006] | 0.0071 | 62.8750 |
| code_specific_hard/E_lab/D_code/tau0.1/ones/incl/ctl-none | 8 | Github | 256 | 0.0431 | 0.0392 | 0.0039 | [+0.0032, +0.0047] | 0.0290 | 128.0000 |
| code_specific_hard/E_lab/D_code/tau0.1/ones/incl/ctl-none | 8 | other | 256 | 0.0210 | 0.0211 | -0.0002 | [-0.0005, +0.0002] | 0.0158 | 206.0000 |
| code_specific_hard/E_lab/D_code/tau0.1/ones/incl/ctl-none | 8 | ArXiv | 64 | 0.0187 | 0.0189 | -0.0002 | [-0.0008, +0.0003] | 0.0132 | 40.0000 |
| code_specific_hard/E_lab/D_code/tau0.1/ones/incl/ctl-none | 8 | Pile-CC | 64 | 0.0152 | 0.0151 | 0.0001 | [-0.0002, +0.0003] | 0.0148 | 62.0000 |
| code_specific_hard/E_lab/D_code/tau0.1/ones/incl/ctl-none | 8 | StackExchange | 64 | 0.0325 | 0.0325 | -0.0000 | [-0.0010, +0.0010] | 0.0178 | 42.0000 |
| code_specific_hard/E_lab/D_code/tau0.1/ones/incl/ctl-none | 8 | Wikipedia (en) | 64 | 0.0176 | 0.0180 | -0.0004 | [-0.0007, -0.0001] | 0.0170 | 62.0000 |
| code_specific_hard/E_lab/D_code/tau0.1/ones/incl/ctl-none | S4 | Github | 256 | 0.0026 | 0.0075 | -0.0049 | [-0.0061, -0.0037] | 0.0009 | 205.0000 |
| code_specific_hard/E_lab/D_code/tau0.1/ones/incl/ctl-none | S4 | other | 256 | 0.0004 | 0.0018 | -0.0014 | [-0.0019, -0.0009] | 0.0002 | 249.0000 |
| code_specific_hard/E_lab/D_code/tau0.1/ones/incl/ctl-none | S4 | ArXiv | 64 | 0.0002 | 0.0006 | -0.0005 | [-0.0006, -0.0003] | 0.0002 | 64.0000 |
| code_specific_hard/E_lab/D_code/tau0.1/ones/incl/ctl-none | S4 | Pile-CC | 64 | 0.0001 | 0.0001 | 0.0000 | [+0.0000, +0.0000] | 0.0001 | 64.0000 |
| code_specific_hard/E_lab/D_code/tau0.1/ones/incl/ctl-none | S4 | StackExchange | 64 | 0.0013 | 0.0063 | -0.0050 | [-0.0068, -0.0033] | 0.0005 | 57.0000 |
| code_specific_hard/E_lab/D_code/tau0.1/ones/incl/ctl-none | S4 | Wikipedia (en) | 64 | 0.0002 | 0.0002 | -0.0000 | [-0.0000, -0.0000] | 0.0002 | 64.0000 |
| code_specific_hard/E_lab/D_code/tau0.1/ones/incl/ctl-none | S16 | Github | 256 | 0.0159 | 0.0116 | 0.0042 | [+0.0037, +0.0047] | 0.0026 | 156.0000 |
| code_specific_hard/E_lab/D_code/tau0.1/ones/incl/ctl-none | S16 | other | 256 | 0.0034 | 0.0029 | 0.0005 | [+0.0002, +0.0008] | 0.0009 | 238.0000 |
| code_specific_hard/E_lab/D_code/tau0.1/ones/incl/ctl-none | S16 | ArXiv | 64 | 0.0007 | 0.0014 | -0.0008 | [-0.0010, -0.0005] | 0.0007 | 61.0000 |
| code_specific_hard/E_lab/D_code/tau0.1/ones/incl/ctl-none | S16 | Pile-CC | 64 | 0.0007 | 0.0006 | 0.0000 | [+0.0000, +0.0001] | 0.0007 | 64.0000 |
| code_specific_hard/E_lab/D_code/tau0.1/ones/incl/ctl-none | S16 | StackExchange | 64 | 0.0113 | 0.0087 | 0.0025 | [+0.0017, +0.0035] | 0.0013 | 49.0000 |
| code_specific_hard/E_lab/D_code/tau0.1/ones/incl/ctl-none | S16 | Wikipedia (en) | 64 | 0.0009 | 0.0008 | 0.0001 | [+0.0000, +0.0001] | 0.0008 | 64.0000 |
| code_specific_hard/E_lab/D_code/tau0.1/ones/incl/ctl-none | S64 | Github | 256 | 0.0230 | 0.0171 | 0.0059 | [+0.0052, +0.0067] | 0.0092 | 138.0000 |
| code_specific_hard/E_lab/D_code/tau0.1/ones/incl/ctl-none | S64 | other | 256 | 0.0072 | 0.0068 | 0.0005 | [+0.0001, +0.0009] | 0.0042 | 219.0000 |
| code_specific_hard/E_lab/D_code/tau0.1/ones/incl/ctl-none | S64 | ArXiv | 64 | 0.0051 | 0.0066 | -0.0015 | [-0.0022, -0.0009] | 0.0037 | 45.0000 |
| code_specific_hard/E_lab/D_code/tau0.1/ones/incl/ctl-none | S64 | Pile-CC | 64 | 0.0036 | 0.0034 | 0.0003 | [+0.0002, +0.0003] | 0.0036 | 63.0000 |
| code_specific_hard/E_lab/D_code/tau0.1/ones/incl/ctl-none | S64 | StackExchange | 64 | 0.0160 | 0.0130 | 0.0029 | [+0.0019, +0.0041] | 0.0056 | 47.0000 |
| code_specific_hard/E_lab/D_code/tau0.1/ones/incl/ctl-none | S64 | Wikipedia (en) | 64 | 0.0043 | 0.0041 | 0.0002 | [-0.0000, +0.0003] | 0.0042 | 64.0000 |
| code_specific_hard/E_lab/D_code/tau0.5/ones/incl/ctl-none | 1 | Github | 256 | 0.0004 | 0.0000 | 0.0003 | [+0.0003, +0.0004] | 0.0001 | 245.8750 |
| code_specific_hard/E_lab/D_code/tau0.5/ones/incl/ctl-none | 1 | other | 256 | 0.0001 | 0.0001 | 0.0000 | [-0.0000, +0.0000] | 0.0000 | 253.7500 |
| code_specific_hard/E_lab/D_code/tau0.5/ones/incl/ctl-none | 1 | ArXiv | 64 | 0.0003 | 0.0003 | -0.0001 | [-0.0001, -0.0000] | 0.0001 | 63.0000 |
| code_specific_hard/E_lab/D_code/tau0.5/ones/incl/ctl-none | 1 | Pile-CC | 64 | 0.0000 | 0.0000 | 0.0000 | [+0.0000, +0.0000] | 0.0000 | 64.0000 |
| code_specific_hard/E_lab/D_code/tau0.5/ones/incl/ctl-none | 1 | StackExchange | 64 | 0.0002 | 0.0001 | 0.0001 | [+0.0000, +0.0001] | 0.0000 | 62.7500 |
| code_specific_hard/E_lab/D_code/tau0.5/ones/incl/ctl-none | 1 | Wikipedia (en) | 64 | 0.0000 | 0.0000 | 0.0000 | [-0.0000, +0.0000] | 0.0000 | 64.0000 |
| code_specific_hard/E_lab/D_code/tau0.5/ones/incl/ctl-none | 2 | Github | 256 | 0.0063 | 0.0024 | 0.0039 | [+0.0034, +0.0043] | 0.0006 | 200.1250 |
| code_specific_hard/E_lab/D_code/tau0.5/ones/incl/ctl-none | 2 | other | 256 | 0.0020 | 0.0012 | 0.0008 | [+0.0005, +0.0010] | 0.0003 | 241.5000 |
| code_specific_hard/E_lab/D_code/tau0.5/ones/incl/ctl-none | 2 | ArXiv | 64 | 0.0032 | 0.0026 | 0.0006 | [+0.0003, +0.0010] | 0.0003 | 57.2500 |
| code_specific_hard/E_lab/D_code/tau0.5/ones/incl/ctl-none | 2 | Pile-CC | 64 | 0.0002 | 0.0002 | 0.0000 | [+0.0000, +0.0000] | 0.0002 | 63.7500 |
| code_specific_hard/E_lab/D_code/tau0.5/ones/incl/ctl-none | 2 | StackExchange | 64 | 0.0042 | 0.0018 | 0.0024 | [+0.0017, +0.0032] | 0.0004 | 56.5000 |
| code_specific_hard/E_lab/D_code/tau0.5/ones/incl/ctl-none | 2 | Wikipedia (en) | 64 | 0.0003 | 0.0002 | 0.0000 | [+0.0000, +0.0000] | 0.0003 | 64.0000 |
| code_specific_hard/E_lab/D_code/tau0.5/ones/incl/ctl-none | 3 | Github | 256 | 0.0195 | 0.0068 | 0.0127 | [+0.0116, +0.0139] | 0.0023 | 114.3750 |
| code_specific_hard/E_lab/D_code/tau0.5/ones/incl/ctl-none | 3 | other | 256 | 0.0071 | 0.0047 | 0.0025 | [+0.0019, +0.0031] | 0.0012 | 217.0000 |
| code_specific_hard/E_lab/D_code/tau0.5/ones/incl/ctl-none | 3 | ArXiv | 64 | 0.0133 | 0.0114 | 0.0019 | [+0.0013, +0.0026] | 0.0011 | 46.8750 |
| code_specific_hard/E_lab/D_code/tau0.5/ones/incl/ctl-none | 3 | Pile-CC | 64 | 0.0011 | 0.0009 | 0.0002 | [+0.0002, +0.0002] | 0.0011 | 63.0000 |
| code_specific_hard/E_lab/D_code/tau0.5/ones/incl/ctl-none | 3 | StackExchange | 64 | 0.0127 | 0.0053 | 0.0074 | [+0.0055, +0.0094] | 0.0015 | 44.1250 |
| code_specific_hard/E_lab/D_code/tau0.5/ones/incl/ctl-none | 3 | Wikipedia (en) | 64 | 0.0013 | 0.0010 | 0.0003 | [+0.0003, +0.0003] | 0.0013 | 63.0000 |
| code_specific_hard/E_lab/D_code/tau0.5/ones/incl/ctl-none | 4 | Github | 256 | 0.0297 | 0.0157 | 0.0140 | [+0.0127, +0.0152] | 0.0032 | 117.0000 |
| code_specific_hard/E_lab/D_code/tau0.5/ones/incl/ctl-none | 4 | other | 256 | 0.0117 | 0.0073 | 0.0044 | [+0.0035, +0.0055] | 0.0018 | 213.2500 |
| code_specific_hard/E_lab/D_code/tau0.5/ones/incl/ctl-none | 4 | ArXiv | 64 | 0.0239 | 0.0151 | 0.0088 | [+0.0060, +0.0119] | 0.0016 | 43.7500 |
| code_specific_hard/E_lab/D_code/tau0.5/ones/incl/ctl-none | 4 | Pile-CC | 64 | 0.0016 | 0.0013 | 0.0003 | [+0.0003, +0.0004] | 0.0016 | 62.5000 |
| code_specific_hard/E_lab/D_code/tau0.5/ones/incl/ctl-none | 4 | StackExchange | 64 | 0.0194 | 0.0112 | 0.0082 | [+0.0063, +0.0103] | 0.0021 | 44.0000 |
| code_specific_hard/E_lab/D_code/tau0.5/ones/incl/ctl-none | 4 | Wikipedia (en) | 64 | 0.0019 | 0.0015 | 0.0004 | [+0.0004, +0.0004] | 0.0019 | 63.0000 |
| code_specific_hard/E_lab/D_code/tau0.5/ones/incl/ctl-none | 5a | Github | 256 | 0.0421 | 0.0225 | 0.0196 | [+0.0178, +0.0213] | 0.0048 | 90.0000 |
| code_specific_hard/E_lab/D_code/tau0.5/ones/incl/ctl-none | 5a | other | 256 | 0.0162 | 0.0104 | 0.0057 | [+0.0045, +0.0070] | 0.0027 | 200.5000 |
| code_specific_hard/E_lab/D_code/tau0.5/ones/incl/ctl-none | 5a | ArXiv | 64 | 0.0323 | 0.0217 | 0.0106 | [+0.0075, +0.0141] | 0.0024 | 37.1250 |
| code_specific_hard/E_lab/D_code/tau0.5/ones/incl/ctl-none | 5a | Pile-CC | 64 | 0.0025 | 0.0020 | 0.0005 | [+0.0004, +0.0005] | 0.0024 | 61.3750 |
| code_specific_hard/E_lab/D_code/tau0.5/ones/incl/ctl-none | 5a | StackExchange | 64 | 0.0269 | 0.0157 | 0.0113 | [+0.0086, +0.0141] | 0.0030 | 40.0000 |
| code_specific_hard/E_lab/D_code/tau0.5/ones/incl/ctl-none | 5a | Wikipedia (en) | 64 | 0.0029 | 0.0024 | 0.0006 | [+0.0005, +0.0006] | 0.0030 | 62.0000 |
| code_specific_hard/E_lab/D_code/tau0.5/ones/incl/ctl-none | 5 | Github | 256 | 0.0513 | 0.0275 | 0.0238 | [+0.0217, +0.0260] | 0.0081 | 79.2500 |
| code_specific_hard/E_lab/D_code/tau0.5/ones/incl/ctl-none | 5 | other | 256 | 0.0255 | 0.0175 | 0.0080 | [+0.0063, +0.0099] | 0.0045 | 189.0000 |
| code_specific_hard/E_lab/D_code/tau0.5/ones/incl/ctl-none | 5 | ArXiv | 64 | 0.0574 | 0.0409 | 0.0165 | [+0.0118, +0.0215] | 0.0040 | 32.8750 |
| code_specific_hard/E_lab/D_code/tau0.5/ones/incl/ctl-none | 5 | Pile-CC | 64 | 0.0041 | 0.0036 | 0.0005 | [+0.0005, +0.0006] | 0.0041 | 59.2500 |
| code_specific_hard/E_lab/D_code/tau0.5/ones/incl/ctl-none | 5 | StackExchange | 64 | 0.0356 | 0.0212 | 0.0144 | [+0.0107, +0.0184] | 0.0046 | 37.0000 |
| code_specific_hard/E_lab/D_code/tau0.5/ones/incl/ctl-none | 5 | Wikipedia (en) | 64 | 0.0049 | 0.0042 | 0.0007 | [+0.0006, +0.0008] | 0.0050 | 59.8750 |
| code_specific_hard/E_lab/D_code/tau0.5/ones/incl/ctl-none | 6a | Github | 256 | 0.0636 | 0.0370 | 0.0266 | [+0.0240, +0.0292] | 0.0113 | 69.1250 |
| code_specific_hard/E_lab/D_code/tau0.5/ones/incl/ctl-none | 6a | other | 256 | 0.0366 | 0.0239 | 0.0127 | [+0.0099, +0.0157] | 0.0068 | 182.1250 |
| code_specific_hard/E_lab/D_code/tau0.5/ones/incl/ctl-none | 6a | ArXiv | 64 | 0.0863 | 0.0551 | 0.0312 | [+0.0230, +0.0401] | 0.0061 | 31.0000 |
| code_specific_hard/E_lab/D_code/tau0.5/ones/incl/ctl-none | 6a | Pile-CC | 64 | 0.0063 | 0.0055 | 0.0008 | [+0.0007, +0.0009] | 0.0062 | 58.5000 |
| code_specific_hard/E_lab/D_code/tau0.5/ones/incl/ctl-none | 6a | StackExchange | 64 | 0.0463 | 0.0287 | 0.0176 | [+0.0131, +0.0224] | 0.0070 | 33.8750 |
| code_specific_hard/E_lab/D_code/tau0.5/ones/incl/ctl-none | 6a | Wikipedia (en) | 64 | 0.0075 | 0.0064 | 0.0011 | [+0.0010, +0.0013] | 0.0077 | 58.7500 |
| code_specific_hard/E_lab/D_code/tau0.5/ones/incl/ctl-none | 6 | Github | 256 | 0.0703 | 0.0443 | 0.0260 | [+0.0234, +0.0287] | 0.0155 | 62.7500 |
| code_specific_hard/E_lab/D_code/tau0.5/ones/incl/ctl-none | 6 | other | 256 | 0.0502 | 0.0331 | 0.0171 | [+0.0132, +0.0214] | 0.0095 | 173.3750 |
| code_specific_hard/E_lab/D_code/tau0.5/ones/incl/ctl-none | 6 | ArXiv | 64 | 0.1275 | 0.0784 | 0.0491 | [+0.0371, +0.0618] | 0.0085 | 25.8750 |
| code_specific_hard/E_lab/D_code/tau0.5/ones/incl/ctl-none | 6 | Pile-CC | 64 | 0.0087 | 0.0078 | 0.0009 | [+0.0008, +0.0010] | 0.0085 | 57.0000 |
| code_specific_hard/E_lab/D_code/tau0.5/ones/incl/ctl-none | 6 | StackExchange | 64 | 0.0542 | 0.0371 | 0.0171 | [+0.0125, +0.0221] | 0.0096 | 32.6250 |
| code_specific_hard/E_lab/D_code/tau0.5/ones/incl/ctl-none | 6 | Wikipedia (en) | 64 | 0.0104 | 0.0091 | 0.0013 | [+0.0012, +0.0015] | 0.0111 | 57.8750 |
| code_specific_hard/E_lab/D_code/tau0.5/ones/incl/ctl-none | 7 | Github | 256 | 0.0802 | 0.0528 | 0.0274 | [+0.0246, +0.0304] | 0.0220 | 46.7500 |
| code_specific_hard/E_lab/D_code/tau0.5/ones/incl/ctl-none | 7 | other | 256 | 0.0636 | 0.0429 | 0.0207 | [+0.0158, +0.0259] | 0.0131 | 153.0000 |
| code_specific_hard/E_lab/D_code/tau0.5/ones/incl/ctl-none | 7 | ArXiv | 64 | 0.1627 | 0.0983 | 0.0644 | [+0.0500, +0.0797] | 0.0108 | 21.5000 |
| code_specific_hard/E_lab/D_code/tau0.5/ones/incl/ctl-none | 7 | Pile-CC | 64 | 0.0125 | 0.0113 | 0.0012 | [+0.0010, +0.0014] | 0.0121 | 53.6250 |
| code_specific_hard/E_lab/D_code/tau0.5/ones/incl/ctl-none | 7 | StackExchange | 64 | 0.0642 | 0.0487 | 0.0154 | [+0.0101, +0.0212] | 0.0123 | 27.7500 |
| code_specific_hard/E_lab/D_code/tau0.5/ones/incl/ctl-none | 7 | Wikipedia (en) | 64 | 0.0150 | 0.0131 | 0.0019 | [+0.0017, +0.0021] | 0.0154 | 50.1250 |
| code_specific_hard/E_lab/D_code/tau0.5/ones/incl/ctl-none | 8 | Github | 256 | 0.0969 | 0.0706 | 0.0263 | [+0.0231, +0.0295] | 0.0347 | 38.0000 |
| code_specific_hard/E_lab/D_code/tau0.5/ones/incl/ctl-none | 8 | other | 256 | 0.0817 | 0.0615 | 0.0202 | [+0.0161, +0.0245] | 0.0216 | 138.0000 |
| code_specific_hard/E_lab/D_code/tau0.5/ones/incl/ctl-none | 8 | ArXiv | 64 | 0.1926 | 0.1382 | 0.0544 | [+0.0429, +0.0667] | 0.0174 | 19.0000 |
| code_specific_hard/E_lab/D_code/tau0.5/ones/incl/ctl-none | 8 | Pile-CC | 64 | 0.0210 | 0.0193 | 0.0017 | [+0.0011, +0.0022] | 0.0203 | 51.0000 |
| code_specific_hard/E_lab/D_code/tau0.5/ones/incl/ctl-none | 8 | StackExchange | 64 | 0.0877 | 0.0658 | 0.0218 | [+0.0162, +0.0280] | 0.0208 | 23.0000 |
| code_specific_hard/E_lab/D_code/tau0.5/ones/incl/ctl-none | 8 | Wikipedia (en) | 64 | 0.0254 | 0.0224 | 0.0030 | [+0.0024, +0.0036] | 0.0253 | 45.0000 |
| code_specific_hard/E_lab/D_code/tau0.5/ones/incl/ctl-none | S4 | Github | 256 | 0.0051 | 0.0004 | 0.0048 | [+0.0042, +0.0053] | 0.0014 | 146.0000 |
| code_specific_hard/E_lab/D_code/tau0.5/ones/incl/ctl-none | S4 | other | 256 | 0.0010 | 0.0004 | 0.0006 | [+0.0004, +0.0008] | 0.0005 | 239.0000 |
| code_specific_hard/E_lab/D_code/tau0.5/ones/incl/ctl-none | S4 | ArXiv | 64 | 0.0003 | 0.0005 | -0.0002 | [-0.0003, -0.0001] | 0.0003 | 61.0000 |
| code_specific_hard/E_lab/D_code/tau0.5/ones/incl/ctl-none | S4 | Pile-CC | 64 | 0.0003 | 0.0002 | 0.0001 | [+0.0001, +0.0002] | 0.0003 | 64.0000 |
| code_specific_hard/E_lab/D_code/tau0.5/ones/incl/ctl-none | S4 | StackExchange | 64 | 0.0029 | 0.0006 | 0.0023 | [+0.0016, +0.0030] | 0.0008 | 50.0000 |
| code_specific_hard/E_lab/D_code/tau0.5/ones/incl/ctl-none | S4 | Wikipedia (en) | 64 | 0.0004 | 0.0002 | 0.0002 | [+0.0002, +0.0003] | 0.0004 | 64.0000 |
| code_specific_hard/E_lab/D_code/tau0.5/ones/incl/ctl-none | S16 | Github | 256 | 0.0239 | 0.0037 | 0.0202 | [+0.0179, +0.0225] | 0.0018 | 109.0000 |
| code_specific_hard/E_lab/D_code/tau0.5/ones/incl/ctl-none | S16 | other | 256 | 0.0043 | 0.0038 | 0.0004 | [-0.0009, +0.0019] | 0.0009 | 216.0000 |
| code_specific_hard/E_lab/D_code/tau0.5/ones/incl/ctl-none | S16 | ArXiv | 64 | 0.0018 | 0.0106 | -0.0089 | [-0.0115, -0.0065] | 0.0008 | 46.0000 |
| code_specific_hard/E_lab/D_code/tau0.5/ones/incl/ctl-none | S16 | Pile-CC | 64 | 0.0008 | 0.0007 | 0.0001 | [+0.0001, +0.0002] | 0.0008 | 64.0000 |
| code_specific_hard/E_lab/D_code/tau0.5/ones/incl/ctl-none | S16 | StackExchange | 64 | 0.0135 | 0.0031 | 0.0104 | [+0.0069, +0.0142] | 0.0012 | 42.0000 |
| code_specific_hard/E_lab/D_code/tau0.5/ones/incl/ctl-none | S16 | Wikipedia (en) | 64 | 0.0010 | 0.0008 | 0.0001 | [+0.0001, +0.0002] | 0.0010 | 64.0000 |
| code_specific_hard/E_lab/D_code/tau0.5/ones/incl/ctl-none | S64 | Github | 256 | 0.0508 | 0.0258 | 0.0251 | [+0.0230, +0.0272] | 0.0056 | 85.0000 |
| code_specific_hard/E_lab/D_code/tau0.5/ones/incl/ctl-none | S64 | other | 256 | 0.0222 | 0.0147 | 0.0075 | [+0.0058, +0.0093] | 0.0033 | 200.0000 |
| code_specific_hard/E_lab/D_code/tau0.5/ones/incl/ctl-none | S64 | ArXiv | 64 | 0.0473 | 0.0337 | 0.0136 | [+0.0090, +0.0187] | 0.0028 | 39.0000 |
| code_specific_hard/E_lab/D_code/tau0.5/ones/incl/ctl-none | S64 | Pile-CC | 64 | 0.0031 | 0.0023 | 0.0008 | [+0.0007, +0.0009] | 0.0031 | 60.0000 |
| code_specific_hard/E_lab/D_code/tau0.5/ones/incl/ctl-none | S64 | StackExchange | 64 | 0.0344 | 0.0200 | 0.0145 | [+0.0107, +0.0185] | 0.0037 | 39.0000 |
| code_specific_hard/E_lab/D_code/tau0.5/ones/incl/ctl-none | S64 | Wikipedia (en) | 64 | 0.0037 | 0.0028 | 0.0009 | [+0.0008, +0.0010] | 0.0037 | 62.0000 |

Comparison 3, within other at rung 7: StackExchange and ArXiv against Pile-CC and Wikipedia, unpaired, with the conditional damage beside:
| chain | rung | n_a | n_b | unconditional_a_minus_b | interval | conditional_d_0.1_a | conditional_d_0.1_b |
|---|---|---|---|---|---|---|---|
| hard_zero/E_lab/D_code/tau0.1/ones/incl/ctl-none | 7 | 128 | 128 | 0.9904 | [+0.8286, +1.1509] |  |  |
| code_specific_hard/E_lab/D_code/tau0.1/ones/incl/ctl-none | 7 | 128 | 128 | 0.0073 | [+0.0053, +0.0095] | 0.0070 | 0.0066 |
| code_specific_hard/E_lab/D_code/tau0.5/ones/incl/ctl-none | 7 | 128 | 128 | 0.0997 | [+0.0809, +0.1200] | 0.0117 | 0.0137 |

### Soft erases and the rounded-own-g union (descriptive, the union machinery)
- `soft_erase/E/D_unif/tau0.1/r1/excl/ctl-none`: rung 0 0.0115; excess per rung 1 +0.4362, 2 +0.7302, 3 +0.4641, 4 +0.4486, 5a +0.3860, 5 +0.3692, 6a +0.3603, 6 +0.3558, 7 +0.3520, 8 +0.3501
- `soft_erase/E/D_unif/tau0.1/uniform/excl/k0/ctl-none`: rung 0 0.2151; excess per rung 1 +0.0108, 2 +0.0365, 3 +0.0884, 4 +0.0985, 5a +0.1026, 5 +0.1039, 6a +0.1046, 6 +0.1055, 7 +0.1059, 8 +0.1060
- `soft_erase/E/D_unif/tau0.1/uniform/excl/k1/ctl-none`: rung 0 0.2151; excess per rung 1 +0.0113, 2 +0.0411, 3 +0.0886, 4 +0.0744, 5a +0.0982, 5 +0.1039, 6a +0.1053, 6 +0.1056, 7 +0.1059, 8 +0.1060
- `soft_erase/E/D_unif/tau0.1/uniform/excl/k2/ctl-none`: rung 0 0.2151; excess per rung 1 +0.0095, 2 +0.0369, 3 +0.0914, 4 +0.0848, 5a +0.0976, 5 +0.1030, 6a +0.1052, 6 +0.1056, 7 +0.1059, 8 +0.1060
- `soft_erase/E/D_unif/tau0.1/uniform/excl/k3/ctl-none`: rung 0 0.2152; excess per rung 1 +0.0061, 2 +0.0383, 3 +0.0896, 4 +0.0241, 5a +0.0929, 5 +0.1024, 6a +0.1035, 6 +0.1055, 7 +0.1058, 8 +0.1059
- `soft_erase/E/D_unif/tau0.1/uniform/excl/k4/ctl-none`: rung 0 0.2151; excess per rung 1 +0.0081, 2 +0.0352, 3 +0.0873, 4 +0.0813, 5a +0.0883, 5 +0.1026, 6a +0.1051, 6 +0.1056, 7 +0.1059, 8 +0.1060
- `soft_erase/E/D_unif/tau0.1/uniform/excl/k5/ctl-none`: rung 0 0.2151; excess per rung 1 +0.0097, 2 +0.0325, 3 +0.0916, 4 +0.0914, 5a +0.0968, 5 +0.1010, 6a +0.1051, 6 +0.1057, 7 +0.1060, 8 +0.1060
- `soft_erase/E/D_unif/tau0.1/uniform/excl/k6/ctl-none`: rung 0 0.2152; excess per rung 1 +0.0017, 2 +0.0317, 3 +0.0890, 4 +0.0905, 5a +0.0971, 5 +0.1018, 6a +0.1039, 6 +0.1052, 7 +0.1059, 8 +0.1059
- `soft_erase/E/D_unif/tau0.1/uniform/excl/k7/ctl-none`: rung 0 0.2151; excess per rung 1 +0.0083, 2 +0.0336, 3 +0.0888, 4 +0.0908, 5a +0.0985, 5 +0.1006, 6a +0.1044, 6 +0.1055, 7 +0.1059, 8 +0.1059
- `soft_erase/E/D_unif/tau0.1/r1/excl/ctl-plain`: rung 0 0.0115; excess per rung 1 +0.0702, 2 +0.2919, 3 +0.3543, 4 +0.3569, 5a +0.3447, 5 +0.3427, 6a +0.3453, 6 +0.3475, 7 +0.3495, 8 +0.3500
- `soft_erase/E/D_unif/tau0.1/uniform/excl/k0/ctl-plain`: rung 0 0.2151; excess per rung 1 +0.0028, 2 +0.0177, 3 +0.0613, 4 +0.0817, 5a +0.0903, 5 +0.0950, 6a +0.0982, 6 +0.1025, 7 +0.1055, 8 +0.1060
- `soft_erase/E/D_unif/tau0.1/uniform/excl/k1/ctl-plain`: rung 0 0.2151; excess per rung 1 +0.0045, 2 +0.0216, 3 +0.0655, 4 +0.0544, 5a +0.0839, 5 +0.0933, 6a +0.0992, 6 +0.1010, 7 +0.1045, 8 +0.1060
- `soft_erase/E/D_unif/tau0.1/uniform/excl/k2/ctl-plain`: rung 0 0.2151; excess per rung 1 +0.0029, 2 +0.0182, 3 +0.0671, 4 +0.0651, 5a +0.0810, 5 +0.0936, 6a +0.0998, 6 +0.1021, 7 +0.1049, 8 +0.1060
- `soft_erase/E/D_unif/tau0.1/uniform/excl/k3/ctl-plain`: rung 0 0.2152; excess per rung 1 +0.0020, 2 +0.0223, 3 +0.0643, 4 +0.0167, 5a +0.0716, 5 +0.0904, 6a +0.0950, 6 +0.1018, 7 +0.1048, 8 +0.1058
- `soft_erase/E/D_unif/tau0.1/uniform/excl/k4/ctl-plain`: rung 0 0.2151; excess per rung 1 +0.0040, 2 +0.0221, 3 +0.0613, 4 +0.0632, 5a +0.0736, 5 +0.0933, 6a +0.0994, 6 +0.1027, 7 +0.1055, 8 +0.1060
- `soft_erase/E/D_unif/tau0.1/uniform/excl/k5/ctl-plain`: rung 0 0.2151; excess per rung 1 +0.0028, 2 +0.0136, 3 +0.0652, 4 +0.0697, 5a +0.0789, 5 +0.0882, 6a +0.0982, 6 +0.1026, 7 +0.1049, 8 +0.1060
- `soft_erase/E/D_unif/tau0.1/uniform/excl/k6/ctl-plain`: rung 0 0.2152; excess per rung 1 +0.0008, 2 +0.0149, 3 +0.0655, 4 +0.0696, 5a +0.0792, 5 +0.0894, 6a +0.0963, 6 +0.1010, 7 +0.1047, 8 +0.1059
- `soft_erase/E/D_unif/tau0.1/uniform/excl/k7/ctl-plain`: rung 0 0.2151; excess per rung 1 +0.0030, 2 +0.0190, 3 +0.0651, 4 +0.0684, 5a +0.0814, 5 +0.0863, 6a +0.0976, 6 +0.1026, 7 +0.1051, 8 +0.1059
- `soft_erase/E_lab/D_code/tau0.1/r1/excl/ctl-none`: rung 0 0.0122; excess per rung 1 +0.4688, 2 +0.7261, 3 +0.4936, 4 +0.4028, 5a +0.3800, 5 +0.3633, 6a +0.3559, 6 +0.3526, 7 +0.3489, 8 +0.3463
- `soft_erase/E_lab/D_code/tau0.1/r1/excl/ctl-plain`: rung 0 0.0122; excess per rung 1 +0.0932, 2 +0.2897, 3 +0.3767, 4 +0.3578, 5a +0.3457, 5 +0.3408, 6a +0.3405, 6 +0.3404, 7 +0.3426, 8 +0.3431
- `code_specific_soft/E_lab/D_code/tau0.1/r1/excl/ctl-none`: rung 0 0.0122; excess per rung 1 +0.0000, 2 +0.0002, 3 +0.0011, 4 +0.0016, 5a +0.0023, 5 +0.0037, 6a +0.0054, 6 +0.0070, 7 +0.0108, 8 +0.0241

## 9. Tier 4: the marginal-matched control, the code-leaning chain, and the code-specific chain on E by reader label

Every reading rule below was fixed before any tier-4 store existed; the labels are the frozen rules' output.

Canaries (curve 1's union and its plain control at rung 2, draw 0, rerun in the marginal store), bitwise against their first run on kl_mean, mask_fp, sigma, the source hash, and the applied-mask digest: E: 2 of 2 equal (union/D_unif/tau0.1/r0/excl/k0/r2 in tier4/E__marginal against tier1/E, union/D_unif/tau0.1/r0/excl/k0/r2/ctl-plain in tier4/E__marginal against tier2/E). The references of every tier-4 store are in section 0's assert with every other store's.

Two-path recompute of the conditional damage on the tier-4 hard-zero cells: E_lab: 45 cells, 8563 checks, max ratio 0.8562, pass

### 9.1 The marginal-matched control

Asserted before reading: 104 marginal cells and 104 union and plain cells equal, by source hash, the sets of the committed label-only pre-read (results/grid/pre_reads/main/s7/marginal_composition.csv); P4 on 4 tier-4 chains; the canaries and references in section 0. Overlap constants from results/grid/pre_reads/main/s7/marginal_overlap_by_rung.csv (overlap_mass_pooled); a rung is decisive at o_M at most 0.3333. One resample of E's texts serves the three curves and every rung of every family.

**The readings** (each a condition at every decisive rung; D before B; C otherwise; no reading without a decisive rung; the soft erase is read at rungs 1 and 2 only; at a decisive rung a denominator U - P whose interval includes zero or lies below it gives that family no reading, the others being read all the same; the headline takes the primary family's reading, and a primary family with no reading leaves the headline with none: it does not pass to the secondary family):

| family | role | reading | decisive_rungs | m | decisive_by_the_rule_alone | strong_form_of_A | guard_fired_at | rungs_missing |
|---|---|---|---|---|---|---|---|---|
| union_r0 | primary | A | 1, 2 | 2 | 1, 2 | False |  |  |
| union_uniform | secondary | C | 1, 2 | 2 | 1, 2 |  |  |  |
| soft_erase_r1 | third | B | 1, 2 | 2 | 1, 2 |  |  |  |

**Per rung** (s7_marginal_closure.csv carries every column; U, P, and M each with its own interval, at the family's corrected level at the decisive rungs and uncorrected at the others, which are descriptives; s7_marginal_per_draw.csv the per-draw U, P, M). Reading D needs the interval of M - U above zero and M - U positive on at least K - 1 of K draws:

| family | rung | decisive | m | U | U_interval | P | P_interval | M | M_interval | U_minus_P_interval | M_minus_P | M_minus_P_interval | U_minus_M | U_minus_M_interval | phi_ov | phi | psi | psi_interval | rho | M_minus_P_draws_positive | U_minus_M_draws_positive | M_minus_U_interval | M_minus_U_draws_positive | rung_reading | replicate_1_psi | replicate_psi_gap | replicate_rule_forces_C |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| union_r0 | 1 | True | 2 | 0.0038 | [+0.0034, +0.0041] | -0.0021 | [-0.0022, -0.0019] | -0.0033 | [-0.0036, -0.0031] | [+0.0054, +0.0062] | -0.0013 | [-0.0015, -0.0010] | 0.0071 | [+0.0068, +0.0074] | 0.0656 | -0.2185 | -0.3040 | [-0.3583, -0.2527] | -0.8866 | 1 | 8 | [-0.0074, -0.0068] | 0 | A | -0.3007 | 0.0033 | False |
| union_r0 | 2 | True | 2 | 0.0402 | [+0.0388, +0.0416] | -0.0110 | [-0.0117, -0.0104] | -0.0038 | [-0.0047, -0.0029] | [+0.0500, +0.0525] | 0.0072 | [+0.0067, +0.0078] | 0.0440 | [+0.0430, +0.0450] | 0.1562 | 0.1414 | -0.0175 | [-0.0283, -0.0067] | -0.0947 | 8 | 8 | [-0.0450, -0.0430] | 0 | A | 0.0058 | 0.0233 | False |
| union_r0 | 2a | False | 1 | 0.1016 | [+0.0993, +0.1041] | -0.0125 | [-0.0135, -0.0115] | 0.0250 | [+0.0237, +0.0264] | [+0.1122, +0.1163] | 0.0376 | [+0.0365, +0.0387] | 0.0766 | [+0.0751, +0.0782] | 0.2355 | 0.3291 | 0.1224 | [+0.1128, +0.1318] | 0.2465 | 8 | 8 | [-0.0782, -0.0751] | 0 | descriptive |  |  | None |
| union_r0 | 2b | False | 1 | 0.2312 | [+0.2258, +0.2370] | -0.0014 | [-0.0030, +0.0003] | 0.1368 | [+0.1332, +0.1405] | [+0.2280, +0.2375] | 0.1382 | [+0.1350, +0.1414] | 0.0944 | [+0.0916, +0.0975] | 0.3257 | 0.5942 | 0.3982 | [+0.3849, +0.4107] | 0.5917 | 8 | 8 | [-0.0975, -0.0916] | 0 | descriptive |  |  | None |
| union_r0 | 3 | False | 1 | 0.4575 | [+0.4481, +0.4674] | 0.0397 | [+0.0369, +0.0426] | 0.3770 | [+0.3684, +0.3861] | [+0.4100, +0.4259] | 0.3373 | [+0.3297, +0.3450] | 0.0805 | [+0.0780, +0.0831] | 0.4212 | 0.8073 | 0.6671 | [+0.6564, +0.6775] | 0.8241 | 8 | 8 | [-0.0831, -0.0780] | 0 | descriptive |  |  | None |
| union_uniform | 1 | True | 2 | 0.0059 | [+0.0056, +0.0061] | 0.0003 | [+0.0003, +0.0004] | 0.0018 | [+0.0017, +0.0019] | [+0.0053, +0.0058] | 0.0015 | [+0.0014, +0.0016] | 0.0040 | [+0.0038, +0.0042] | 0.0656 | 0.2728 | 0.2218 | [+0.2080, +0.2358] | 0.3125 | 8 | 8 | [-0.0042, -0.0038] | 0 | A |  |  | None |
| union_uniform | 2 | True | 2 | 0.0491 | [+0.0481, +0.0500] | 0.0051 | [+0.0048, +0.0053] | 0.0265 | [+0.0259, +0.0271] | [+0.0431, +0.0449] | 0.0214 | [+0.0209, +0.0220] | 0.0226 | [+0.0220, +0.0231] | 0.1562 | 0.4872 | 0.3923 | [+0.3839, +0.4008] | 0.5401 | 8 | 8 | [-0.0231, -0.0220] | 0 | C |  |  | None |
| union_uniform | 3 | False | 1 | 0.4161 | [+0.4076, +0.4250] | 0.0868 | [+0.0848, +0.0891] | 0.3850 | [+0.3767, +0.3938] | [+0.3225, +0.3364] | 0.2982 | [+0.2913, +0.3052] | 0.0311 | [+0.0297, +0.0325] | 0.4212 | 0.9055 | 0.8368 | [+0.8293, +0.8442] | 0.9252 | 8 | 8 | [-0.0325, -0.0297] | 0 | descriptive |  |  | None |
| soft_erase_r1 | 1 | True | 2 | 0.4362 | [+0.4225, +0.4511] | 0.0702 | [+0.0685, +0.0720] | 0.4051 | [+0.3923, +0.4189] | [+0.3530, +0.3802] | 0.3349 | [+0.3230, +0.3479] | 0.0311 | [+0.0288, +0.0335] | 0.0628 | 0.9150 | 0.9093 | [+0.9036, +0.9152] | 0.9287 | 8 | 6 | [-0.0335, -0.0288] | 2 | B |  |  | None |
| soft_erase_r1 | 2 | True | 2 | 0.7302 | [+0.7163, +0.7451] | 0.2919 | [+0.2870, +0.2972] | 0.6598 | [+0.6470, +0.6735] | [+0.4260, +0.4515] | 0.3679 | [+0.3565, +0.3803] | 0.0704 | [+0.0668, +0.0741] | 0.1608 | 0.8393 | 0.8086 | [+0.7994, +0.8180] | 0.9036 | 8 | 8 | [-0.0741, -0.0668] | 0 | B |  |  | None |
| soft_erase_r1 | 3 | False | 1 | 0.4641 | [+0.4577, +0.4707] | 0.3543 | [+0.3491, +0.3594] | 0.4477 | [+0.4415, +0.4540] | [+0.1070, +0.1127] | 0.0934 | [+0.0907, +0.0962] | 0.0165 | [+0.0156, +0.0174] | 0.4227 | 0.8501 | 0.7404 | [+0.7266, +0.7547] | 0.9645 | 8 | 7 | [-0.0174, -0.0156] | 1 | descriptive |  |  | None |

**Beside rung 1's reading, as stated before the launch.** Label-only: the realized marginal control's pooled usage is 0.9133 of the eight realized union sets' at rung 1 and its weight norm 0.9663; among 200 sets of eight real pool positions the realized union's usage is at the 87.5th percentile and its norm at the 89.5th. The note written before the launch: under pure composition this predicts a rung-1 psi near 0.9 and not 1, a small bias toward reading A; rung 2 is the clean test. Per draw (s7_marginal_rung_1_usage_per_draw.csv):

| control | draw | n | mean_usage | p90_usage | mean_norm | p90_norm |
|---|---|---|---|---|---|---|
| union | 0 | 201 | 0.1349 | 0.4129 | 1.7689 | 2.9764 |
| union | 1 | 222 | 0.1121 | 0.2117 | 1.6660 | 2.9742 |
| union | 2 | 226 | 0.1176 | 0.2259 | 1.6343 | 2.4666 |
| union | 3 | 143 | 0.1430 | 0.6224 | 1.7737 | 3.6110 |
| union | 4 | 212 | 0.1074 | 0.1683 | 1.6876 | 3.3650 |
| union | 5 | 154 | 0.1613 | 0.6152 | 1.9510 | 3.7743 |
| union | 6 | 38 | 0.2763 | 0.9755 | 2.9209 | 7.7732 |
| union | 7 | 156 | 0.1521 | 0.5396 | 1.9169 | 3.5706 |
| union | pooled | 1352 | 0.1338 | 0.4500 | 1.7875 | 3.4585 |
| marginal | 0 | 201 | 0.1298 | 0.3229 | 1.7245 | 3.1741 |
| marginal | 1 | 222 | 0.1009 | 0.1356 | 1.6394 | 3.1238 |
| marginal | 2 | 226 | 0.1081 | 0.1760 | 1.6050 | 2.3667 |
| marginal | 3 | 143 | 0.1339 | 0.3990 | 1.7865 | 3.5903 |
| marginal | 4 | 212 | 0.1162 | 0.2386 | 1.6974 | 3.6188 |
| marginal | 5 | 154 | 0.1362 | 0.5440 | 1.8501 | 3.6989 |
| marginal | 6 | 38 | 0.2179 | 0.9755 | 2.3293 | 5.9822 |
| marginal | 7 | 156 | 0.1233 | 0.2695 | 1.7518 | 3.1863 |
| marginal | pooled | 1352 | 0.1222 | 0.2744 | 1.7273 | 3.1973 |

**By reader label** (descriptive; each label's own resample at the rung's level; the ratio is undefined where the interval of U - P includes zero, the differences are always reported): s7_marginal_by_reader_label.csv.

For the soft erase the named cost is sublinear between rungs 1 and 2, so shared members may carry more than their linear share and push psi upward: there reading A is secure, and readings B and C are less so.

### 9.2 The code-leaning chain

Pre-read: existence rule clear; thresholds {'chain_forced': False, 'group': 0.9, 'default_thresholds': True, 'wide': 0.75}; the control's label-only gate {'failures': [], 'pass': True, 'rule': "at every non-descriptive rung of at least 64 members the control's mean usage and mean weight norm, as a mean over the draws, lie within 10 percent of the group's", 'rungs_judged': [64, 256, 1007]}. Asserted before reading: every rung and every control equal, by source hash, the pre-read's; P4 on the erase chain and its controls; the readability floor equal to the pre-read's testability table. Strata: Github and other, never averaged. Rungs read: G16, G64, G256, G1007 (m = 4); descriptive, uncorrected: G1862; 8 control draws per rung.

**The chain's own positive control** (on Github, judged at the rungs the rule reads that have at least 64 members, uncorrected 95 percent): **pass**

| rung | n_members | descriptive | judged | paired_erase_minus_control | interval_95 | above_zero |
|---|---|---|---|---|---|---|
| G16 | 16 | False | False | 0.0144 | [+0.0123, +0.0165] | True |
| G64 | 64 | False | True | 0.0894 | [+0.0806, +0.0982] | True |
| G256 | 256 | False | True | 0.5394 | [+0.4859, +0.5929] | True |
| G1007 | 1007 | False | True | 2.1359 | [+1.9331, +2.3313] | True |
| G1862 | 1862 | True | False | 2.7843 | [+2.4820, +3.0720] | True |

**Reading: otherwise (none of R1 to R3): reported as measured, rung by rung**; R4, read beside the others (the labels' code-leaning shows no code-specific effect at these sizes: the localization statistic's interval includes zero or is negative at every rung of at least 64 members): False.

Unconditional damage per stratum (the erase minus its rung 0; intervals at the chain's corrected level on the rungs read), its control, and the localization statistic (independent resamples of the two strata):

| rung | n_members | descriptive | level_m | D_github | D_github_interval | D_github_control | D_github_ratio_to_control | D_other | D_other_interval | D_other_control | localization | localization_interval |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| G16 | 16 | False | 4 | 0.0159 | [+0.0133, +0.0186] | 0.0015 | 10.6692 | 0.0034 | [+0.0022, +0.0047] | 0.0021 | 0.0131 | [+0.0102, +0.0161] |
| G64 | 64 | False | 4 | 0.1012 | [+0.0901, +0.1124] | 0.0118 | 8.5551 | 0.0179 | [+0.0137, +0.0225] | 0.0192 | 0.0907 | [+0.0781, +0.1030] |
| G256 | 256 | False | 4 | 0.6390 | [+0.5762, +0.7016] | 0.0995 | 6.4188 | 0.1555 | [+0.1255, +0.1883] | 0.1478 | 0.5317 | [+0.4540, +0.6077] |
| G1007 | 1007 | False | 4 | 3.2391 | [+3.0298, +3.4397] | 1.1031 | 2.9362 | 1.2514 | [+1.0186, +1.4985] | 1.3082 | 2.1927 | [+1.8123, +2.5577] |
| G1862 | 1862 | True | 1 | 6.8968 | [+6.6635, +7.1221] | 4.1125 | 1.6770 | 3.0193 | [+2.7462, +3.2987] | 4.1369 | 3.9019 | [+3.4683, +4.3270] |

Conditional damage on clean prefixes (the hard-zero rule, the floor judged per stratum; s7_code_leaning_conditional.csv), the group on the other stratum:

| rung | n_members | stratum | set | tau_q | mean_n_contributing | mean_clean_prefix_fraction | testable | d_hat | interval | label |
|---|---|---|---|---|---|---|---|---|---|---|
| G16 | 16 | other | group | 0.1 | 238.0000 | 0.7320 | True | 0.0009 | [+0.0008, +0.0010] | holds |
| G16 | 16 | other | group | 0 | 230.0000 | 0.5127 | True | 0.0008 | [+0.0008, +0.0009] | holds |
| G64 | 64 | other | group | 0.1 | 179.0000 | 0.3940 | True | 0.0037 | [+0.0034, +0.0039] | holds |
| G64 | 64 | other | group | 0 | 168.0000 | 0.1386 | True | 0.0037 | [+0.0034, +0.0040] | holds |
| G256 | 256 | other | group | 0.1 | 95.0000 | 0.0465 | False |  |  | not testable |
| G256 | 256 | other | group | 0 | 70.0000 | 0.0131 | False |  |  | not testable |
| G1007 | 1007 | other | group | 0.1 | 0.0000 | 0.0000 | False |  |  | not testable |
| G1007 | 1007 | other | group | 0 | 0.0000 | 0.0000 | False |  |  | not testable |
| G1862 | 1862 | other | group | 0.1 | 0.0000 | 0.0000 | False |  |  | not testable |
| G1862 | 1862 | other | group | 0 | 0.0000 | 0.0000 | False |  |  | not testable |

Editing budget on other over the rungs read: tau_q 0.1: G64; tau_q 0: G64.

The touched surplus on other, the over-removal, and the surplus per unit of over-removal, the group and its control (s7_code_leaning_touched_surplus.csv), at tau_q 0.1:

| rung | n_members | stratum | set | tau_q | touched_surplus | surplus_interval_95 | over_removal | surplus_per_over_removal | ratio_interval_95 |
|---|---|---|---|---|---|---|---|---|---|
| G16 | 16 | other | group | 0.1 | 0.0028 | [+0.0019, +0.0039] | 0.0099 | 0.2856 | [+0.2473, +0.3260] |
| G16 | 16 | other | control | 0.1 | 0.0020 | [+0.0019, +0.0021] | 0.0145 | 0.1369 | [+0.1308, +0.1432] |
| G64 | 64 | other | group | 0.1 | 0.0165 | [+0.0130, +0.0202] | 0.1432 | 0.1150 | [+0.1052, +0.1249] |
| G64 | 64 | other | control | 0.1 | 0.0192 | [+0.0184, +0.0200] | 0.1665 | 0.1153 | [+0.1123, +0.1184] |
| G256 | 256 | other | group | 0.1 | 0.1546 | [+0.1304, +0.1797] | 1.6748 | 0.0923 | [+0.0819, +0.1053] |
| G256 | 256 | other | control | 0.1 | 0.1478 | [+0.1425, +0.1530] | 1.8328 | 0.0806 | [+0.0790, +0.0823] |
| G1007 | 1007 | other | group | 0.1 | 1.2514 | [+1.0690, +1.4424] | 11.4194 | 0.1096 | [+0.0991, +0.1212] |
| G1007 | 1007 | other | control | 0.1 | 1.3082 | [+1.2714, +1.3458] | 11.3186 | 0.1156 | [+0.1138, +0.1174] |
| G1862 | 1862 | other | group | 0.1 | 3.0193 | [+2.7462, +3.2987] | 25.3111 | 0.1193 | [+0.1137, +0.1254] |
| G1862 | 1862 | other | control | 0.1 | 4.1369 | [+4.0689, +4.2053] | 27.4476 | 0.1507 | [+0.1483, +0.1532] |

Unconditional damage on each source of other, the group and its control, uncorrected 95 percent, each source's own resample (s7_code_leaning_damage_by_source.csv):

| rung | n_members | descriptive | source | n_texts | set | n_draws | D | interval_95 |
|---|---|---|---|---|---|---|---|---|
| G16 | 16 | False | ArXiv | 64 | group | 1 | 0.0007 | [+0.0006, +0.0007] |
| G16 | 16 | False | ArXiv | 64 | control | 8 | 0.0017 | [+0.0015, +0.0019] |
| G64 | 64 | False | ArXiv | 64 | group | 1 | 0.0165 | [+0.0133, +0.0199] |
| G64 | 64 | False | ArXiv | 64 | control | 8 | 0.0152 | [+0.0143, +0.0160] |
| G256 | 256 | False | ArXiv | 64 | group | 1 | 0.2501 | [+0.2000, +0.3021] |
| G256 | 256 | False | ArXiv | 64 | control | 8 | 0.1244 | [+0.1191, +0.1298] |
| G1007 | 1007 | False | ArXiv | 64 | group | 1 | 2.4717 | [+2.0214, +2.9406] |
| G1007 | 1007 | False | ArXiv | 64 | control | 8 | 1.0524 | [+1.0123, +1.0953] |
| G1862 | 1862 | True | ArXiv | 64 | group | 1 | 4.8024 | [+4.2716, +5.3320] |
| G1862 | 1862 | True | ArXiv | 64 | control | 8 | 3.6929 | [+3.5858, +3.8064] |
| G16 | 16 | False | Pile-CC | 64 | group | 1 | 0.0007 | [+0.0006, +0.0007] |
| G16 | 16 | False | Pile-CC | 64 | control | 8 | 0.0019 | [+0.0017, +0.0021] |
| G64 | 64 | False | Pile-CC | 64 | group | 1 | 0.0034 | [+0.0032, +0.0035] |
| G64 | 64 | False | Pile-CC | 64 | control | 8 | 0.0248 | [+0.0230, +0.0267] |
| G256 | 256 | False | Pile-CC | 64 | group | 1 | 0.0206 | [+0.0199, +0.0215] |
| G256 | 256 | False | Pile-CC | 64 | control | 8 | 0.1760 | [+0.1677, +0.1844] |
| G1007 | 1007 | False | Pile-CC | 64 | group | 1 | 0.1616 | [+0.1517, +0.1719] |
| G1007 | 1007 | False | Pile-CC | 64 | control | 8 | 1.4425 | [+1.4067, +1.4795] |
| G1862 | 1862 | True | Pile-CC | 64 | group | 1 | 1.1235 | [+0.9955, +1.2632] |
| G1862 | 1862 | True | Pile-CC | 64 | control | 8 | 4.2077 | [+4.1183, +4.3042] |
| G16 | 16 | False | StackExchange | 64 | group | 1 | 0.0113 | [+0.0081, +0.0146] |
| G16 | 16 | False | StackExchange | 64 | control | 8 | 0.0021 | [+0.0019, +0.0023] |
| G64 | 64 | False | StackExchange | 64 | group | 1 | 0.0476 | [+0.0373, +0.0584] |
| G64 | 64 | False | StackExchange | 64 | control | 8 | 0.0156 | [+0.0147, +0.0165] |
| G256 | 256 | False | StackExchange | 64 | group | 1 | 0.3251 | [+0.2701, +0.3820] |
| G256 | 256 | False | StackExchange | 64 | control | 8 | 0.1121 | [+0.1036, +0.1209] |
| G1007 | 1007 | False | StackExchange | 64 | group | 1 | 2.1746 | [+1.9048, +2.4565] |
| G1007 | 1007 | False | StackExchange | 64 | control | 8 | 1.1230 | [+1.0719, +1.1833] |
| G1862 | 1862 | True | StackExchange | 64 | group | 1 | 4.6494 | [+4.2180, +5.0920] |
| G1862 | 1862 | True | StackExchange | 64 | control | 8 | 3.9171 | [+3.8252, +4.0114] |
| G16 | 16 | False | Wikipedia (en) | 64 | group | 1 | 0.0009 | [+0.0008, +0.0009] |
| G16 | 16 | False | Wikipedia (en) | 64 | control | 8 | 0.0027 | [+0.0024, +0.0030] |
| G64 | 64 | False | Wikipedia (en) | 64 | group | 1 | 0.0040 | [+0.0038, +0.0043] |
| G64 | 64 | False | Wikipedia (en) | 64 | control | 8 | 0.0212 | [+0.0203, +0.0222] |
| G256 | 256 | False | Wikipedia (en) | 64 | group | 1 | 0.0263 | [+0.0234, +0.0309] |
| G256 | 256 | False | Wikipedia (en) | 64 | control | 8 | 0.1787 | [+0.1714, +0.1859] |
| G1007 | 1007 | False | Wikipedia (en) | 64 | group | 1 | 0.1978 | [+0.1659, +0.2499] |
| G1007 | 1007 | False | Wikipedia (en) | 64 | control | 8 | 1.6149 | [+1.5591, +1.6742] |
| G1862 | 1862 | True | Wikipedia (en) | 64 | group | 1 | 1.5021 | [+1.3053, +1.7291] |
| G1862 | 1862 | True | Wikipedia (en) | 64 | control | 8 | 4.7298 | [+4.6263, +4.8366] |

### 9.3 The code-specific chain on E by reader label (an analysis addition, no verdict)

`code_specific_hard/E/D_code/tau0.1/ones/incl/ctl-none`: 96 rows in s7_code_specific_hard_E_D_code_tau0.1_ones_incl_ctl-none__by_reader_label.csv; rungs 4 and 7 of the donor chain at tau_q 0.1:

| reader_label | n_texts | rung | n_off | unconditional | unconditional_interval | mean_n_contributing | testable | d_hat | d_interval | label |
|---|---|---|---|---|---|---|---|---|---|---|
| code | 120 | 4 | 8.6250 | 0.0109 | [+0.0089, +0.0131] | 95.1250 | True | 0.0015 | [+0.0013, +0.0019] | holds |
| code | 120 | 7 | 108.6250 | 0.0320 | [+0.0279, +0.0361] | 66.1250 | True | 0.0138 | [+0.0109, +0.0175] | holds |
| mixed | 27 | 4 | 8.6250 | 0.0061 | [+0.0042, +0.0084] | 25.1250 | False |  |  | not testable with these donors |
| mixed | 27 | 7 | 108.6250 | 0.0201 | [+0.0163, +0.0245] | 20.8750 | False |  |  | not testable with these donors |
| other | 158 | 4 | 8.6250 | 0.0010 | [+0.0008, +0.0011] | 151.1250 | True | 0.0007 | [+0.0006, +0.0007] | holds |
| other | 158 | 7 | 108.6250 | 0.0131 | [+0.0117, +0.0146] | 112.8750 | True | 0.0096 | [+0.0085, +0.0109] | holds |
| prose | 719 | 4 | 8.6250 | 0.0007 | [+0.0006, +0.0008] | 706.7500 | True | 0.0005 | [+0.0005, +0.0005] | holds |
| prose | 719 | 7 | 108.6250 | 0.0071 | [+0.0068, +0.0073] | 652.0000 | True | 0.0063 | [+0.0061, +0.0065] | holds |

