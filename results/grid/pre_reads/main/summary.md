# Pre-reads for the main run: label-only numbers from the caches and the sources

## 1. Dead against never named (38912 subcomponents; alive by the saved vector 9959, dead 28953; dead recomputed from the cache 28953, disagreements 0)

| tau | named | never named | dead & never named | dead & named | alive & never named | alive & named |
|---|---|---|---|---|---|---|
| 0 | 33576 | 5336 | 5336 | 23617 | 0 | 9959 |
| 0.1 | 9966 | 28946 | 28945 | 8 | 1 | 9958 |
| 0.5 | 9926 | 28986 | 28953 | 0 | 33 | 9926 |

## 2. The never-named set (tau = 0.1) and the strict set (tau = 0) on the five caches

### never_named_tau0.1: 28946 members

| cache | tau_q | median t* | q1 / q3 | fraction = T | fraction >= 8 | clean-prefix fraction | mean touched positions |
|---|---|---|---|---|---|---|---|
| D_code | 0 | 0 | 0 / 1 | 0.000 | 0.004 | 0.002 | 160.0 |
| D_code | 0.01 | 512 | 512 / 512 | 0.914 | 0.963 | 0.935 | 0.1 |
| D_code | 0.1 | 512 | 512 / 512 | 1.000 | 1.000 | 1.000 | 0.0 |
| D_prose | 0 | 1 | 0 / 1 | 0.000 | 0.012 | 0.002 | 176.0 |
| D_prose | 0.01 | 512 | 512 / 512 | 0.896 | 0.945 | 0.923 | 0.1 |
| D_prose | 0.1 | 512 | 512 / 512 | 0.998 | 0.998 | 0.998 | 0.0 |
| D_unif | 0 | 0 | 0 / 1 | 0.000 | 0.009 | 0.002 | 167.5 |
| D_unif | 0.01 | 512 | 512 / 512 | 0.886 | 0.951 | 0.913 | 0.1 |
| D_unif | 0.1 | 512 | 512 / 512 | 1.000 | 1.000 | 1.000 | 0.0 |
| E | 0 | 1 | 0 / 1 | 0.000 | 0.011 | 0.002 | 164.1 |
| E | 0.01 | 512 | 512 / 512 | 0.878 | 0.936 | 0.902 | 0.2 |
| E | 0.1 | 512 | 512 / 512 | 0.995 | 0.996 | 0.996 | 0.0 |
| E_lab | 0 | 0 | 0 / 1 | 0.000 | 0.010 | 0.002 | 171.4 |
| E_lab | 0.01 | 512 | 512 / 512 | 0.912 | 0.961 | 0.929 | 0.1 |
| E_lab | 0.1 | 512 | 512 / 512 | 1.000 | 1.000 | 1.000 | 0.0 |

| cache | members with any g > 0 | median positions with g > 0 | max g <= 0.01 | 0.01 < max g <= 0.1 | max g > 0.1 | largest max g | labels in the set per position: mean / max / fraction of positions with any |
|---|---|---|---|---|---|---|---|
| D_code | 18859 of 28946 | 2 | 28914 | 32 | 0 | 0.0724 | 0.45 / 16 / 0.312 |
| D_prose | 20456 of 28946 | 2 | 28881 | 63 | 2 | 0.1420 | 0.49 / 74 / 0.344 |
| D_unif | 23610 of 28946 | 5 | 28880 | 66 | 0 | 0.0956 | 0.47 / 50 / 0.327 |
| E | 23589 of 28946 | 5 | 28817 | 113 | 16 | 0.9584 | 0.46 / 173 / 0.320 |
| E_lab | 20797 of 28946 | 2 | 28915 | 31 | 0 | 0.0783 | 0.48 / 32 / 0.335 |

### strict_tau0: 5336 members

| cache | tau_q | median t* | q1 / q3 | fraction = T | fraction >= 8 | clean-prefix fraction | mean touched positions |
|---|---|---|---|---|---|---|---|
| D_code | 0 | 71 | 18 / 190 | 0.092 | 0.859 | 0.268 | 3.4 |
| D_code | 0.01 | 512 | 512 / 512 | 0.996 | 1.000 | 0.998 | 0.0 |
| D_code | 0.1 | 512 | 512 / 512 | 1.000 | 1.000 | 1.000 | 0.0 |
| D_prose | 0 | 116 | 39 / 246 | 0.062 | 0.898 | 0.316 | 3.0 |
| D_prose | 0.01 | 512 | 512 / 512 | 1.000 | 1.000 | 1.000 | 0.0 |
| D_prose | 0.1 | 512 | 512 / 512 | 1.000 | 1.000 | 1.000 | 0.0 |
| D_unif | 0 | 512 | 512 / 512 | 1.000 | 1.000 | 1.000 | 0.0 |
| D_unif | 0.01 | 512 | 512 / 512 | 1.000 | 1.000 | 1.000 | 0.0 |
| D_unif | 0.1 | 512 | 512 / 512 | 1.000 | 1.000 | 1.000 | 0.0 |
| E | 0 | 92 | 26 / 247 | 0.090 | 0.882 | 0.305 | 2.9 |
| E | 0.01 | 512 | 512 / 512 | 0.999 | 1.000 | 0.999 | 0.0 |
| E | 0.1 | 512 | 512 / 512 | 1.000 | 1.000 | 1.000 | 0.0 |
| E_lab | 0 | 70 | 21 / 180 | 0.053 | 0.867 | 0.250 | 3.5 |
| E_lab | 0.01 | 512 | 512 / 512 | 1.000 | 1.000 | 1.000 | 0.0 |
| E_lab | 0.1 | 512 | 512 / 512 | 1.000 | 1.000 | 1.000 | 0.0 |

| cache | members with any g > 0 | median positions with g > 0 | max g <= 0.01 | 0.01 < max g <= 0.1 | max g > 0.1 | largest max g | labels in the set per position: mean / max / fraction of positions with any |
|---|---|---|---|---|---|---|---|
| D_code | 924 of 5336 | 0 | 5335 | 1 | 0 | 0.0468 | 0.01 / 3 / 0.007 |
| D_prose | 976 of 5336 | 0 | 5336 | 0 | 0 | 0.0054 | 0.01 / 2 / 0.006 |
| D_unif | 0 of 5336 | 0 | 5336 | 0 | 0 | 0.0000 | 0.00 / 0 / 0.000 |
| E | 1667 of 5336 | 0 | 5335 | 1 | 0 | 0.0297 | 0.01 / 6 / 0.006 |
| E_lab | 1067 of 5336 | 0 | 5336 | 0 | 0 | 0.0062 | 0.01 / 3 / 0.007 |

## 3. Union against its plain control at tau = 0.1: the fraction of the union set the control also names (mean over draws), beside n_on / |alive|

| rung | n_on | overlap fraction | expected n_on / alive |
|---|---|---|---|
| 1 | 169 | 0.026 | 0.017 |
| 2 | 1121 | 0.149 | 0.113 |
| 2a | 1974 | 0.251 | 0.198 |
| 2b | 3198 | 0.392 | 0.321 |
| 3 | 4544 | 0.536 | 0.456 |
| 4 | 4890 | 0.534 | 0.491 |
| 5 | 7711 | 0.805 | 0.774 |
| 5a | 6501 | 0.698 | 0.653 |
| 6 | 9060 | 0.921 | 0.910 |
| 6a | 8490 | 0.873 | 0.852 |
| 7 | 9659 | 0.972 | 0.970 |
| 8 | 9966 | 0.999 | 1.001 |
Per matrix in overlap_union_vs_control.csv.

## 4. E2's coverage: the fraction of alive subcomponents the union names (mean over draws; per layer in coverage.csv)

| tau | rung 1 | rung 2 | rung 2a | rung 2b | rung 3 | rung 4 | rung 5 | rung 5a | rung 6 | rung 6a | rung 7 | rung 8 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 0 | 0.018 | 0.121 |  |  | 0.476 | 0.525 | 0.819 |  | 0.947 |  | 0.993 | 1.000 |
| 0.1 | 0.017 | 0.113 | 0.198 | 0.321 | 0.456 | 0.491 | 0.774 | 0.653 | 0.910 | 0.852 | 0.970 | 1.000 |
| 0.5 | 0.014 | 0.090 |  |  | 0.399 | 0.440 | 0.727 | 0.599 | 0.883 | 0.815 | 0.955 | 0.997 |
Overlap between draws at rung 7 (tau = 0.1): pairwise Jaccard mean 0.968 (min 0.956, max 0.979, 28 pairs); intersection of all draws 9212, union 9950.

## 5. The union's n_on at tau = 0 (draw/rung): k0/r1: 216, k0/r2: 1132, k0/r3: 4733, k0/r4: 7307, k0/r5: 9303, k0/r6: 12743, k0/r7: 19040, k0/r8: 33576, k1/r1: 233, k1/r2: 1381, k1/r3: 4689, k1/r4: 4581, k1/r5: 8860, k1/r6: 12228, k1/r7: 18666, k2/r1: 246, k2/r2: 1145, k2/r3: 4887, k2/r4: 5805, k2/r5: 9279, k2/r6: 12565, k2/r7: 18627, k3/r1: 149, k3/r2: 1653, k3/r3: 4747, k3/r4: 1595, k3/r5: 8943, k3/r6: 12478, k3/r7: 18961, k4/r1: 227, k4/r2: 1292, k4/r3: 4454, k4/r4: 5625, k4/r5: 8953, k4/r6: 12288, k4/r7: 18696, k5/r1: 163, k5/r2: 946, k5/r3: 4950, k5/r4: 6269, k5/r5: 8908, k5/r6: 12442, k5/r7: 18533, k6/r1: 38, k6/r2: 1011, k6/r3: 4849, k6/r4: 6156, k6/r5: 8761, k6/r6: 12308, k6/r7: 18740, k7/r1: 174, k7/r2: 1092, k7/r3: 4810, k7/r4: 6001, k7/r5: 8602, k7/r6: 12326, k7/r7: 18700
Never-named set at tau = 0.1: 28946; the strict never-named set at tau = 0: 5336.

## 6. Testability of the hard-zero chains (1538 cells, 1246 distinct erased sets, 26 chains; per-sequence t* in t_star.parquet, 1115648 rows; the full table in testability.csv)

Rungs meeting the readability floor at tau_q = 0.1 on the whole set (at least 64 contributing on average over draws, clean-prefix fraction at least 0.05):

| chain | testable rungs |
|---|---|
| code_specific_hard/E/D_code/tau0.1/ones/incl/ctl-none | 1, 2, 3, 4, 5, 5a, 6, 6a, 7, 8, S4, S16, S64 |
| code_specific_hard/E_lab/D_code/tau0.1/ones/excl/ctl-none | 1, 2, 3, 4, 5, 5a, 6, 6a, 7, 8, S4, S16, S64 |
| code_specific_hard/E_lab/D_code/tau0.1/ones/incl/ctl-complement | 1, 2, 3, 4, 5, 5a, 6, 6a, 7, 8, S4, S16, S64 |
| code_specific_hard/E_lab/D_code/tau0.1/ones/incl/ctl-none | 1, 2, 3, 4, 5, 5a, 6, 6a, 7, 8, S4, S16, S64 |
| code_specific_hard/E_lab/D_code/tau0.1/ones/incl/ctl-plain | 1, 2, 3 |
| code_specific_hard/E_lab/D_code/tau0.5/ones/incl/ctl-complement | 1, 2, 3, 4, 5, 5a, 6, 6a, 7, 8, S4, S16, S64 |
| code_specific_hard/E_lab/D_code/tau0.5/ones/incl/ctl-none | 1, 2, 3, 4, 5, 5a, 6, 6a, 7, 8, S4, S16, S64 |
| code_specific_hard/E_lab/D_code/tau0.5/ones/incl/ctl-plain | 1, 2 |
| hard_zero/E/D_code/tau0.1/ones/incl/ctl-none | none |
| hard_zero/E/D_unif/tau0.1/ones/excl/ctl-none | none |
| hard_zero/E/D_unif/tau0.1/ones/incl/ctl-none | none |
| hard_zero/E/D_unif/tau0.1/ones/incl/ctl-plain | none |
| hard_zero/E/D_unif/tau0.5/ones/incl/ctl-none | none |
| hard_zero/E/D_unif/tau0.5/ones/incl/ctl-plain | none |
| hard_zero/E_lab/D_code/tau0.1/ones/excl/ctl-none | none |
| hard_zero/E_lab/D_code/tau0.1/ones/incl/ctl-none | none |
| hard_zero/E_lab/D_code/tau0.1/ones/incl/ctl-plain | none |
| hard_zero/E_lab/D_code/tau0.5/ones/incl/ctl-none | none |
| hard_zero/E_lab/D_code/tau0.5/ones/incl/ctl-plain | none |
| never_named_hard/E/D_unif/tau0.1/ones/excl/ctl-none | 8 |
| never_named_hard/E/D_unif/tau0.1/ones/incl/ctl-none | 1, 2, 3, 4, 5, 5a, 6, 6a, 7, B50, B75, 8 |
| never_named_hard/E/D_unif/tau0/ones/incl/ctl-none | 8 |
| never_named_ranked/E/D_unif/tau0.1/ones/incl/ctl-none/positive_count-bottom | 1, 2, 3, 4, 5, 6, 7, B50, B75 |
| never_named_ranked/E/D_unif/tau0.1/ones/incl/ctl-none/positive_count-top | 1, 2, 3, 4, 5, 6, 7, B50, B75 |
| never_named_ranked/E/D_unif/tau0.1/ones/incl/ctl-none/weight_norm-bottom | 1, 2, 3, 4, 5, 6, 7, B50, B75 |
| never_named_ranked/E/D_unif/tau0.1/ones/incl/ctl-none/weight_norm-top | 1, 2, 3, 4, 5, 6, 7, B50, B75 |

Clean-prefix fraction and contributing count at tau_q = 0.1 (mean over draws), whole set, per chain and rung:

| chain | rung | mean contributing | mean clean-prefix fraction | fraction never touched | floor met |
|---|---|---|---|---|---|
| code_specific_hard/E/D_code/tau0.1/ones/incl/ctl-none | 1 | 1022.1 | 0.992 | 0.988 | True |
| code_specific_hard/E/D_code/tau0.1/ones/incl/ctl-none | 2 | 1015.2 | 0.939 | 0.916 | True |
| code_specific_hard/E/D_code/tau0.1/ones/incl/ctl-none | 3 | 990.6 | 0.814 | 0.749 | True |
| code_specific_hard/E/D_code/tau0.1/ones/incl/ctl-none | 4 | 978.1 | 0.781 | 0.714 | True |
| code_specific_hard/E/D_code/tau0.1/ones/incl/ctl-none | 5 | 923.9 | 0.625 | 0.527 | True |
| code_specific_hard/E/D_code/tau0.1/ones/incl/ctl-none | 5a | 957.9 | 0.735 | 0.657 | True |
| code_specific_hard/E/D_code/tau0.1/ones/incl/ctl-none | 6 | 874.0 | 0.491 | 0.381 | True |
| code_specific_hard/E/D_code/tau0.1/ones/incl/ctl-none | 6a | 894.4 | 0.539 | 0.430 | True |
| code_specific_hard/E/D_code/tau0.1/ones/incl/ctl-none | 7 | 851.9 | 0.450 | 0.338 | True |
| code_specific_hard/E/D_code/tau0.1/ones/incl/ctl-none | 8 | 802.0 | 0.390 | 0.274 | True |
| code_specific_hard/E/D_code/tau0.1/ones/incl/ctl-none | S4 | 995.0 | 0.813 | 0.755 | True |
| code_specific_hard/E/D_code/tau0.1/ones/incl/ctl-none | S16 | 943.0 | 0.670 | 0.568 | True |
| code_specific_hard/E/D_code/tau0.1/ones/incl/ctl-none | S64 | 877.0 | 0.488 | 0.379 | True |
| code_specific_hard/E_lab/D_code/tau0.1/ones/excl/ctl-none | 1 | 510.0 | 0.966 | 0.954 | True |
| code_specific_hard/E_lab/D_code/tau0.1/ones/excl/ctl-none | 2 | 497.1 | 0.837 | 0.796 | True |
| code_specific_hard/E_lab/D_code/tau0.1/ones/excl/ctl-none | 3 | 457.5 | 0.549 | 0.469 | True |
| code_specific_hard/E_lab/D_code/tau0.1/ones/excl/ctl-none | 4 | 433.6 | 0.505 | 0.428 | True |
| code_specific_hard/E_lab/D_code/tau0.1/ones/excl/ctl-none | 5 | 389.0 | 0.428 | 0.352 | True |
| code_specific_hard/E_lab/D_code/tau0.1/ones/excl/ctl-none | 5a | 412.6 | 0.469 | 0.395 | True |
| code_specific_hard/E_lab/D_code/tau0.1/ones/excl/ctl-none | 6 | 358.8 | 0.364 | 0.287 | True |
| code_specific_hard/E_lab/D_code/tau0.1/ones/excl/ctl-none | 6a | 369.1 | 0.378 | 0.300 | True |
| code_specific_hard/E_lab/D_code/tau0.1/ones/excl/ctl-none | 7 | 347.5 | 0.347 | 0.274 | True |
| code_specific_hard/E_lab/D_code/tau0.1/ones/excl/ctl-none | 8 | 334.0 | 0.327 | 0.262 | True |
| code_specific_hard/E_lab/D_code/tau0.1/ones/excl/ctl-none | S4 | 454.0 | 0.520 | 0.457 | True |
| code_specific_hard/E_lab/D_code/tau0.1/ones/excl/ctl-none | S16 | 394.0 | 0.439 | 0.361 | True |
| code_specific_hard/E_lab/D_code/tau0.1/ones/excl/ctl-none | S64 | 357.0 | 0.364 | 0.289 | True |
| code_specific_hard/E_lab/D_code/tau0.1/ones/incl/ctl-complement | 1 | 512.0 | 1.000 | 1.000 | True |
| code_specific_hard/E_lab/D_code/tau0.1/ones/incl/ctl-complement | 2 | 502.6 | 0.855 | 0.820 | True |
| code_specific_hard/E_lab/D_code/tau0.1/ones/incl/ctl-complement | 3 | 480.5 | 0.626 | 0.531 | True |
| code_specific_hard/E_lab/D_code/tau0.1/ones/incl/ctl-complement | 4 | 469.5 | 0.588 | 0.499 | True |
| code_specific_hard/E_lab/D_code/tau0.1/ones/incl/ctl-complement | 5 | 429.8 | 0.451 | 0.357 | True |
| code_specific_hard/E_lab/D_code/tau0.1/ones/incl/ctl-complement | 5a | 456.8 | 0.511 | 0.418 | True |
| code_specific_hard/E_lab/D_code/tau0.1/ones/incl/ctl-complement | 6 | 400.5 | 0.408 | 0.318 | True |
| code_specific_hard/E_lab/D_code/tau0.1/ones/incl/ctl-complement | 6a | 415.6 | 0.430 | 0.337 | True |
| code_specific_hard/E_lab/D_code/tau0.1/ones/incl/ctl-complement | 7 | 381.1 | 0.381 | 0.301 | True |
| code_specific_hard/E_lab/D_code/tau0.1/ones/incl/ctl-complement | 8 | 356.0 | 0.341 | 0.270 | True |
| code_specific_hard/E_lab/D_code/tau0.1/ones/incl/ctl-complement | S4 | 483.0 | 0.571 | 0.449 | True |
| code_specific_hard/E_lab/D_code/tau0.1/ones/incl/ctl-complement | S16 | 463.0 | 0.531 | 0.428 | True |
| code_specific_hard/E_lab/D_code/tau0.1/ones/incl/ctl-complement | S64 | 398.0 | 0.409 | 0.320 | True |
| code_specific_hard/E_lab/D_code/tau0.1/ones/incl/ctl-none | 1 | 510.0 | 0.966 | 0.954 | True |
| code_specific_hard/E_lab/D_code/tau0.1/ones/incl/ctl-none | 2 | 497.1 | 0.837 | 0.796 | True |
| code_specific_hard/E_lab/D_code/tau0.1/ones/incl/ctl-none | 3 | 457.5 | 0.549 | 0.469 | True |
| code_specific_hard/E_lab/D_code/tau0.1/ones/incl/ctl-none | 4 | 433.6 | 0.505 | 0.428 | True |
| code_specific_hard/E_lab/D_code/tau0.1/ones/incl/ctl-none | 5 | 389.0 | 0.428 | 0.352 | True |
| code_specific_hard/E_lab/D_code/tau0.1/ones/incl/ctl-none | 5a | 412.6 | 0.469 | 0.395 | True |
| code_specific_hard/E_lab/D_code/tau0.1/ones/incl/ctl-none | 6 | 358.8 | 0.364 | 0.287 | True |
| code_specific_hard/E_lab/D_code/tau0.1/ones/incl/ctl-none | 6a | 369.1 | 0.378 | 0.300 | True |
| code_specific_hard/E_lab/D_code/tau0.1/ones/incl/ctl-none | 7 | 347.5 | 0.347 | 0.274 | True |
| code_specific_hard/E_lab/D_code/tau0.1/ones/incl/ctl-none | 8 | 334.0 | 0.327 | 0.262 | True |
| code_specific_hard/E_lab/D_code/tau0.1/ones/incl/ctl-none | S4 | 454.0 | 0.520 | 0.457 | True |
| code_specific_hard/E_lab/D_code/tau0.1/ones/incl/ctl-none | S16 | 394.0 | 0.439 | 0.361 | True |
| code_specific_hard/E_lab/D_code/tau0.1/ones/incl/ctl-none | S64 | 357.0 | 0.364 | 0.289 | True |
| code_specific_hard/E_lab/D_code/tau0.1/ones/incl/ctl-plain | 1 | 511.8 | 0.976 | 0.957 | True |
| code_specific_hard/E_lab/D_code/tau0.1/ones/incl/ctl-plain | 2 | 436.2 | 0.680 | 0.640 | True |
| code_specific_hard/E_lab/D_code/tau0.1/ones/incl/ctl-plain | 3 | 223.8 | 0.055 | 0.009 | True |
| code_specific_hard/E_lab/D_code/tau0.1/ones/incl/ctl-plain | 4 | 172.2 | 0.035 | 0.002 | False |
| code_specific_hard/E_lab/D_code/tau0.1/ones/incl/ctl-plain | 5 | 2.9 | 0.000 | 0.000 | False |
| code_specific_hard/E_lab/D_code/tau0.1/ones/incl/ctl-plain | 5a | 88.5 | 0.011 | 0.000 | False |
| code_specific_hard/E_lab/D_code/tau0.1/ones/incl/ctl-plain | 6 | 0.0 | 0.000 | 0.000 | False |
| code_specific_hard/E_lab/D_code/tau0.1/ones/incl/ctl-plain | 6a | 0.2 | 0.000 | 0.000 | False |
| code_specific_hard/E_lab/D_code/tau0.1/ones/incl/ctl-plain | 7 | 0.0 | 0.000 | 0.000 | False |
| code_specific_hard/E_lab/D_code/tau0.1/ones/incl/ctl-plain | 8 | 0.0 | 0.000 | 0.000 | False |
| code_specific_hard/E_lab/D_code/tau0.1/ones/incl/ctl-plain | S4 | 225.0 | 0.026 | 0.000 | False |
| code_specific_hard/E_lab/D_code/tau0.1/ones/incl/ctl-plain | S16 | 43.0 | 0.005 | 0.000 | False |
| code_specific_hard/E_lab/D_code/tau0.1/ones/incl/ctl-plain | S64 | 0.0 | 0.000 | 0.000 | False |
| code_specific_hard/E_lab/D_code/tau0.5/ones/incl/ctl-complement | 1 | 509.9 | 0.954 | 0.934 | True |
| code_specific_hard/E_lab/D_code/tau0.5/ones/incl/ctl-complement | 2 | 486.4 | 0.765 | 0.696 | True |
| code_specific_hard/E_lab/D_code/tau0.5/ones/incl/ctl-complement | 3 | 420.6 | 0.377 | 0.257 | True |
| code_specific_hard/E_lab/D_code/tau0.5/ones/incl/ctl-complement | 4 | 395.9 | 0.364 | 0.245 | True |
| code_specific_hard/E_lab/D_code/tau0.5/ones/incl/ctl-complement | 5 | 327.9 | 0.228 | 0.120 | True |
| code_specific_hard/E_lab/D_code/tau0.5/ones/incl/ctl-complement | 5a | 370.4 | 0.294 | 0.180 | True |
| code_specific_hard/E_lab/D_code/tau0.5/ones/incl/ctl-complement | 6 | 260.1 | 0.148 | 0.054 | True |
| code_specific_hard/E_lab/D_code/tau0.5/ones/incl/ctl-complement | 6a | 294.8 | 0.190 | 0.085 | True |
| code_specific_hard/E_lab/D_code/tau0.5/ones/incl/ctl-complement | 7 | 233.8 | 0.119 | 0.035 | True |
| code_specific_hard/E_lab/D_code/tau0.5/ones/incl/ctl-complement | 8 | 192.0 | 0.090 | 0.018 | True |
| code_specific_hard/E_lab/D_code/tau0.5/ones/incl/ctl-complement | S4 | 491.0 | 0.728 | 0.602 | True |
| code_specific_hard/E_lab/D_code/tau0.5/ones/incl/ctl-complement | S16 | 437.0 | 0.346 | 0.209 | True |
| code_specific_hard/E_lab/D_code/tau0.5/ones/incl/ctl-complement | S64 | 368.0 | 0.251 | 0.117 | True |
| code_specific_hard/E_lab/D_code/tau0.5/ones/incl/ctl-none | 1 | 499.6 | 0.909 | 0.886 | True |
| code_specific_hard/E_lab/D_code/tau0.5/ones/incl/ctl-none | 2 | 441.6 | 0.575 | 0.500 | True |
| code_specific_hard/E_lab/D_code/tau0.5/ones/incl/ctl-none | 3 | 331.4 | 0.346 | 0.258 | True |
| code_specific_hard/E_lab/D_code/tau0.5/ones/incl/ctl-none | 4 | 330.2 | 0.322 | 0.232 | True |
| code_specific_hard/E_lab/D_code/tau0.5/ones/incl/ctl-none | 5 | 268.2 | 0.206 | 0.108 | True |
| code_specific_hard/E_lab/D_code/tau0.5/ones/incl/ctl-none | 5a | 290.5 | 0.264 | 0.172 | True |
| code_specific_hard/E_lab/D_code/tau0.5/ones/incl/ctl-none | 6 | 236.1 | 0.129 | 0.037 | True |
| code_specific_hard/E_lab/D_code/tau0.5/ones/incl/ctl-none | 6a | 251.2 | 0.166 | 0.068 | True |
| code_specific_hard/E_lab/D_code/tau0.5/ones/incl/ctl-none | 7 | 199.8 | 0.092 | 0.014 | True |
| code_specific_hard/E_lab/D_code/tau0.5/ones/incl/ctl-none | 8 | 176.0 | 0.078 | 0.012 | True |
| code_specific_hard/E_lab/D_code/tau0.5/ones/incl/ctl-none | S4 | 385.0 | 0.458 | 0.385 | True |
| code_specific_hard/E_lab/D_code/tau0.5/ones/incl/ctl-none | S16 | 325.0 | 0.344 | 0.262 | True |
| code_specific_hard/E_lab/D_code/tau0.5/ones/incl/ctl-none | S64 | 285.0 | 0.244 | 0.148 | True |
| code_specific_hard/E_lab/D_code/tau0.5/ones/incl/ctl-plain | 1 | 509.8 | 0.924 | 0.880 | True |
| code_specific_hard/E_lab/D_code/tau0.5/ones/incl/ctl-plain | 2 | 279.6 | 0.276 | 0.214 | True |
| code_specific_hard/E_lab/D_code/tau0.5/ones/incl/ctl-plain | 3 | 32.4 | 0.004 | 0.000 | False |
| code_specific_hard/E_lab/D_code/tau0.5/ones/incl/ctl-plain | 4 | 19.9 | 0.002 | 0.000 | False |
| code_specific_hard/E_lab/D_code/tau0.5/ones/incl/ctl-plain | 5 | 0.0 | 0.000 | 0.000 | False |
| code_specific_hard/E_lab/D_code/tau0.5/ones/incl/ctl-plain | 5a | 1.5 | 0.000 | 0.000 | False |
| code_specific_hard/E_lab/D_code/tau0.5/ones/incl/ctl-plain | 6 | 0.0 | 0.000 | 0.000 | False |
| code_specific_hard/E_lab/D_code/tau0.5/ones/incl/ctl-plain | 6a | 0.0 | 0.000 | 0.000 | False |
| code_specific_hard/E_lab/D_code/tau0.5/ones/incl/ctl-plain | 7 | 0.0 | 0.000 | 0.000 | False |
| code_specific_hard/E_lab/D_code/tau0.5/ones/incl/ctl-plain | 8 | 0.0 | 0.000 | 0.000 | False |
| code_specific_hard/E_lab/D_code/tau0.5/ones/incl/ctl-plain | S4 | 213.0 | 0.035 | 0.008 | False |
| code_specific_hard/E_lab/D_code/tau0.5/ones/incl/ctl-plain | S16 | 83.0 | 0.009 | 0.000 | False |
| code_specific_hard/E_lab/D_code/tau0.5/ones/incl/ctl-plain | S64 | 0.0 | 0.001 | 0.000 | False |
| hard_zero/E/D_code/tau0.1/ones/incl/ctl-none | 1 | 0.0 | 0.000 | 0.000 | False |
| hard_zero/E/D_code/tau0.1/ones/incl/ctl-none | 2 | 0.0 | 0.000 | 0.000 | False |
| hard_zero/E/D_code/tau0.1/ones/incl/ctl-none | 3 | 0.0 | 0.000 | 0.000 | False |
| hard_zero/E/D_code/tau0.1/ones/incl/ctl-none | 4 | 0.0 | 0.000 | 0.000 | False |
| hard_zero/E/D_code/tau0.1/ones/incl/ctl-none | 5 | 0.0 | 0.000 | 0.000 | False |
| hard_zero/E/D_code/tau0.1/ones/incl/ctl-none | 5a | 0.0 | 0.000 | 0.000 | False |
| hard_zero/E/D_code/tau0.1/ones/incl/ctl-none | 6 | 0.0 | 0.000 | 0.000 | False |
| hard_zero/E/D_code/tau0.1/ones/incl/ctl-none | 6a | 0.0 | 0.000 | 0.000 | False |
| hard_zero/E/D_code/tau0.1/ones/incl/ctl-none | 7 | 0.0 | 0.000 | 0.000 | False |
| hard_zero/E/D_code/tau0.1/ones/incl/ctl-none | 8 | 0.0 | 0.000 | 0.000 | False |
| hard_zero/E/D_unif/tau0.1/ones/excl/ctl-none | 1 | 0.0 | 0.000 | 0.000 | False |
| hard_zero/E/D_unif/tau0.1/ones/excl/ctl-none | 2 | 0.0 | 0.000 | 0.000 | False |
| hard_zero/E/D_unif/tau0.1/ones/excl/ctl-none | 3 | 0.0 | 0.000 | 0.000 | False |
| hard_zero/E/D_unif/tau0.1/ones/excl/ctl-none | 4 | 0.0 | 0.000 | 0.000 | False |
| hard_zero/E/D_unif/tau0.1/ones/excl/ctl-none | 5 | 0.0 | 0.000 | 0.000 | False |
| hard_zero/E/D_unif/tau0.1/ones/excl/ctl-none | 5a | 0.0 | 0.000 | 0.000 | False |
| hard_zero/E/D_unif/tau0.1/ones/excl/ctl-none | 6 | 0.0 | 0.000 | 0.000 | False |
| hard_zero/E/D_unif/tau0.1/ones/excl/ctl-none | 6a | 0.0 | 0.000 | 0.000 | False |
| hard_zero/E/D_unif/tau0.1/ones/excl/ctl-none | 7 | 0.0 | 0.000 | 0.000 | False |
| hard_zero/E/D_unif/tau0.1/ones/excl/ctl-none | 8 | 0.0 | 0.000 | 0.000 | False |
| hard_zero/E/D_unif/tau0.1/ones/incl/ctl-none | 1 | 0.0 | 0.000 | 0.000 | False |
| hard_zero/E/D_unif/tau0.1/ones/incl/ctl-none | 2 | 0.0 | 0.000 | 0.000 | False |
| hard_zero/E/D_unif/tau0.1/ones/incl/ctl-none | 3 | 0.0 | 0.000 | 0.000 | False |
| hard_zero/E/D_unif/tau0.1/ones/incl/ctl-none | 4 | 0.0 | 0.000 | 0.000 | False |
| hard_zero/E/D_unif/tau0.1/ones/incl/ctl-none | 5 | 0.0 | 0.000 | 0.000 | False |
| hard_zero/E/D_unif/tau0.1/ones/incl/ctl-none | 5a | 0.0 | 0.000 | 0.000 | False |
| hard_zero/E/D_unif/tau0.1/ones/incl/ctl-none | 6 | 0.0 | 0.000 | 0.000 | False |
| hard_zero/E/D_unif/tau0.1/ones/incl/ctl-none | 6a | 0.0 | 0.000 | 0.000 | False |
| hard_zero/E/D_unif/tau0.1/ones/incl/ctl-none | 7 | 0.0 | 0.000 | 0.000 | False |
| hard_zero/E/D_unif/tau0.1/ones/incl/ctl-none | 8 | 0.0 | 0.000 | 0.000 | False |
| hard_zero/E/D_unif/tau0.1/ones/incl/ctl-plain | 1 | 0.1 | 0.000 | 0.000 | False |
| hard_zero/E/D_unif/tau0.1/ones/incl/ctl-plain | 2 | 0.0 | 0.000 | 0.000 | False |
| hard_zero/E/D_unif/tau0.1/ones/incl/ctl-plain | 3 | 0.0 | 0.000 | 0.000 | False |
| hard_zero/E/D_unif/tau0.1/ones/incl/ctl-plain | 4 | 0.0 | 0.000 | 0.000 | False |
| hard_zero/E/D_unif/tau0.1/ones/incl/ctl-plain | 5 | 0.0 | 0.000 | 0.000 | False |
| hard_zero/E/D_unif/tau0.1/ones/incl/ctl-plain | 5a | 0.0 | 0.000 | 0.000 | False |
| hard_zero/E/D_unif/tau0.1/ones/incl/ctl-plain | 6 | 0.0 | 0.000 | 0.000 | False |
| hard_zero/E/D_unif/tau0.1/ones/incl/ctl-plain | 6a | 0.0 | 0.000 | 0.000 | False |
| hard_zero/E/D_unif/tau0.1/ones/incl/ctl-plain | 7 | 0.0 | 0.000 | 0.000 | False |
| hard_zero/E/D_unif/tau0.1/ones/incl/ctl-plain | 8 | 0.0 | 0.000 | 0.000 | False |
| hard_zero/E/D_unif/tau0.5/ones/incl/ctl-none | 1 | 0.0 | 0.000 | 0.000 | False |
| hard_zero/E/D_unif/tau0.5/ones/incl/ctl-none | 2 | 0.0 | 0.000 | 0.000 | False |
| hard_zero/E/D_unif/tau0.5/ones/incl/ctl-none | 3 | 0.0 | 0.000 | 0.000 | False |
| hard_zero/E/D_unif/tau0.5/ones/incl/ctl-none | 4 | 0.0 | 0.000 | 0.000 | False |
| hard_zero/E/D_unif/tau0.5/ones/incl/ctl-none | 5 | 0.0 | 0.000 | 0.000 | False |
| hard_zero/E/D_unif/tau0.5/ones/incl/ctl-none | 5a | 0.0 | 0.000 | 0.000 | False |
| hard_zero/E/D_unif/tau0.5/ones/incl/ctl-none | 6 | 0.0 | 0.000 | 0.000 | False |
| hard_zero/E/D_unif/tau0.5/ones/incl/ctl-none | 6a | 0.0 | 0.000 | 0.000 | False |
| hard_zero/E/D_unif/tau0.5/ones/incl/ctl-none | 7 | 0.0 | 0.000 | 0.000 | False |
| hard_zero/E/D_unif/tau0.5/ones/incl/ctl-none | 8 | 0.0 | 0.000 | 0.000 | False |
| hard_zero/E/D_unif/tau0.5/ones/incl/ctl-plain | 1 | 0.1 | 0.000 | 0.000 | False |
| hard_zero/E/D_unif/tau0.5/ones/incl/ctl-plain | 2 | 0.0 | 0.000 | 0.000 | False |
| hard_zero/E/D_unif/tau0.5/ones/incl/ctl-plain | 3 | 0.0 | 0.000 | 0.000 | False |
| hard_zero/E/D_unif/tau0.5/ones/incl/ctl-plain | 4 | 0.0 | 0.000 | 0.000 | False |
| hard_zero/E/D_unif/tau0.5/ones/incl/ctl-plain | 5 | 0.0 | 0.000 | 0.000 | False |
| hard_zero/E/D_unif/tau0.5/ones/incl/ctl-plain | 5a | 0.0 | 0.000 | 0.000 | False |
| hard_zero/E/D_unif/tau0.5/ones/incl/ctl-plain | 6 | 0.0 | 0.000 | 0.000 | False |
| hard_zero/E/D_unif/tau0.5/ones/incl/ctl-plain | 6a | 0.0 | 0.000 | 0.000 | False |
| hard_zero/E/D_unif/tau0.5/ones/incl/ctl-plain | 7 | 0.0 | 0.000 | 0.000 | False |
| hard_zero/E/D_unif/tau0.5/ones/incl/ctl-plain | 8 | 0.0 | 0.000 | 0.000 | False |
| hard_zero/E_lab/D_code/tau0.1/ones/excl/ctl-none | 1 | 0.0 | 0.000 | 0.000 | False |
| hard_zero/E_lab/D_code/tau0.1/ones/excl/ctl-none | 2 | 0.0 | 0.000 | 0.000 | False |
| hard_zero/E_lab/D_code/tau0.1/ones/excl/ctl-none | 3 | 0.0 | 0.000 | 0.000 | False |
| hard_zero/E_lab/D_code/tau0.1/ones/excl/ctl-none | 4 | 0.0 | 0.000 | 0.000 | False |
| hard_zero/E_lab/D_code/tau0.1/ones/excl/ctl-none | 5 | 0.0 | 0.000 | 0.000 | False |
| hard_zero/E_lab/D_code/tau0.1/ones/excl/ctl-none | 5a | 0.0 | 0.000 | 0.000 | False |
| hard_zero/E_lab/D_code/tau0.1/ones/excl/ctl-none | 6 | 0.0 | 0.000 | 0.000 | False |
| hard_zero/E_lab/D_code/tau0.1/ones/excl/ctl-none | 6a | 0.0 | 0.000 | 0.000 | False |
| hard_zero/E_lab/D_code/tau0.1/ones/excl/ctl-none | 7 | 0.0 | 0.000 | 0.000 | False |
| hard_zero/E_lab/D_code/tau0.1/ones/excl/ctl-none | 8 | 0.0 | 0.000 | 0.000 | False |
| hard_zero/E_lab/D_code/tau0.1/ones/incl/ctl-none | 1 | 0.0 | 0.000 | 0.000 | False |
| hard_zero/E_lab/D_code/tau0.1/ones/incl/ctl-none | 2 | 0.0 | 0.000 | 0.000 | False |
| hard_zero/E_lab/D_code/tau0.1/ones/incl/ctl-none | 3 | 0.0 | 0.000 | 0.000 | False |
| hard_zero/E_lab/D_code/tau0.1/ones/incl/ctl-none | 4 | 0.0 | 0.000 | 0.000 | False |
| hard_zero/E_lab/D_code/tau0.1/ones/incl/ctl-none | 5 | 0.0 | 0.000 | 0.000 | False |
| hard_zero/E_lab/D_code/tau0.1/ones/incl/ctl-none | 5a | 0.0 | 0.000 | 0.000 | False |
| hard_zero/E_lab/D_code/tau0.1/ones/incl/ctl-none | 6 | 0.0 | 0.000 | 0.000 | False |
| hard_zero/E_lab/D_code/tau0.1/ones/incl/ctl-none | 6a | 0.0 | 0.000 | 0.000 | False |
| hard_zero/E_lab/D_code/tau0.1/ones/incl/ctl-none | 7 | 0.0 | 0.000 | 0.000 | False |
| hard_zero/E_lab/D_code/tau0.1/ones/incl/ctl-none | 8 | 0.0 | 0.000 | 0.000 | False |
| hard_zero/E_lab/D_code/tau0.1/ones/incl/ctl-plain | 1 | 0.0 | 0.000 | 0.000 | False |
| hard_zero/E_lab/D_code/tau0.1/ones/incl/ctl-plain | 2 | 0.0 | 0.000 | 0.000 | False |
| hard_zero/E_lab/D_code/tau0.1/ones/incl/ctl-plain | 3 | 0.0 | 0.000 | 0.000 | False |
| hard_zero/E_lab/D_code/tau0.1/ones/incl/ctl-plain | 4 | 0.0 | 0.000 | 0.000 | False |
| hard_zero/E_lab/D_code/tau0.1/ones/incl/ctl-plain | 5 | 0.0 | 0.000 | 0.000 | False |
| hard_zero/E_lab/D_code/tau0.1/ones/incl/ctl-plain | 5a | 0.0 | 0.000 | 0.000 | False |
| hard_zero/E_lab/D_code/tau0.1/ones/incl/ctl-plain | 6 | 0.0 | 0.000 | 0.000 | False |
| hard_zero/E_lab/D_code/tau0.1/ones/incl/ctl-plain | 6a | 0.0 | 0.000 | 0.000 | False |
| hard_zero/E_lab/D_code/tau0.1/ones/incl/ctl-plain | 7 | 0.0 | 0.000 | 0.000 | False |
| hard_zero/E_lab/D_code/tau0.1/ones/incl/ctl-plain | 8 | 0.0 | 0.000 | 0.000 | False |
| hard_zero/E_lab/D_code/tau0.5/ones/incl/ctl-none | 1 | 0.0 | 0.000 | 0.000 | False |
| hard_zero/E_lab/D_code/tau0.5/ones/incl/ctl-none | 2 | 0.0 | 0.000 | 0.000 | False |
| hard_zero/E_lab/D_code/tau0.5/ones/incl/ctl-none | 3 | 0.0 | 0.000 | 0.000 | False |
| hard_zero/E_lab/D_code/tau0.5/ones/incl/ctl-none | 4 | 0.0 | 0.000 | 0.000 | False |
| hard_zero/E_lab/D_code/tau0.5/ones/incl/ctl-none | 5 | 0.0 | 0.000 | 0.000 | False |
| hard_zero/E_lab/D_code/tau0.5/ones/incl/ctl-none | 5a | 0.0 | 0.000 | 0.000 | False |
| hard_zero/E_lab/D_code/tau0.5/ones/incl/ctl-none | 6 | 0.0 | 0.000 | 0.000 | False |
| hard_zero/E_lab/D_code/tau0.5/ones/incl/ctl-none | 6a | 0.0 | 0.000 | 0.000 | False |
| hard_zero/E_lab/D_code/tau0.5/ones/incl/ctl-none | 7 | 0.0 | 0.000 | 0.000 | False |
| hard_zero/E_lab/D_code/tau0.5/ones/incl/ctl-none | 8 | 0.0 | 0.000 | 0.000 | False |
| hard_zero/E_lab/D_code/tau0.5/ones/incl/ctl-plain | 1 | 0.0 | 0.000 | 0.000 | False |
| hard_zero/E_lab/D_code/tau0.5/ones/incl/ctl-plain | 2 | 0.0 | 0.000 | 0.000 | False |
| hard_zero/E_lab/D_code/tau0.5/ones/incl/ctl-plain | 3 | 0.0 | 0.000 | 0.000 | False |
| hard_zero/E_lab/D_code/tau0.5/ones/incl/ctl-plain | 4 | 0.0 | 0.000 | 0.000 | False |
| hard_zero/E_lab/D_code/tau0.5/ones/incl/ctl-plain | 5 | 0.0 | 0.000 | 0.000 | False |
| hard_zero/E_lab/D_code/tau0.5/ones/incl/ctl-plain | 5a | 0.0 | 0.000 | 0.000 | False |
| hard_zero/E_lab/D_code/tau0.5/ones/incl/ctl-plain | 6 | 0.0 | 0.000 | 0.000 | False |
| hard_zero/E_lab/D_code/tau0.5/ones/incl/ctl-plain | 6a | 0.0 | 0.000 | 0.000 | False |
| hard_zero/E_lab/D_code/tau0.5/ones/incl/ctl-plain | 7 | 0.0 | 0.000 | 0.000 | False |
| hard_zero/E_lab/D_code/tau0.5/ones/incl/ctl-plain | 8 | 0.0 | 0.000 | 0.000 | False |
| never_named_hard/E/D_unif/tau0.1/ones/excl/ctl-none | 8 | 1020.0 | 0.996 | 0.995 | True |
| never_named_hard/E/D_unif/tau0.1/ones/incl/ctl-none | 1 | 1023.9 | 1.000 | 1.000 | True |
| never_named_hard/E/D_unif/tau0.1/ones/incl/ctl-none | 2 | 1023.0 | 0.999 | 0.999 | True |
| never_named_hard/E/D_unif/tau0.1/ones/incl/ctl-none | 3 | 1022.2 | 0.998 | 0.998 | True |
| never_named_hard/E/D_unif/tau0.1/ones/incl/ctl-none | 4 | 1022.1 | 0.998 | 0.998 | True |
| never_named_hard/E/D_unif/tau0.1/ones/incl/ctl-none | 5 | 1021.6 | 0.997 | 0.997 | True |
| never_named_hard/E/D_unif/tau0.1/ones/incl/ctl-none | 5a | 1021.9 | 0.998 | 0.997 | True |
| never_named_hard/E/D_unif/tau0.1/ones/incl/ctl-none | 6 | 1021.5 | 0.997 | 0.997 | True |
| never_named_hard/E/D_unif/tau0.1/ones/incl/ctl-none | 6a | 1021.6 | 0.997 | 0.997 | True |
| never_named_hard/E/D_unif/tau0.1/ones/incl/ctl-none | 7 | 1021.5 | 0.997 | 0.997 | True |
| never_named_hard/E/D_unif/tau0.1/ones/incl/ctl-none | B50 | 1021.2 | 0.997 | 0.996 | True |
| never_named_hard/E/D_unif/tau0.1/ones/incl/ctl-none | B75 | 1020.5 | 0.996 | 0.995 | True |
| never_named_hard/E/D_unif/tau0.1/ones/incl/ctl-none | 8 | 1020.0 | 0.996 | 0.995 | True |
| never_named_hard/E/D_unif/tau0/ones/incl/ctl-none | 8 | 1024.0 | 1.000 | 1.000 | True |
| never_named_ranked/E/D_unif/tau0.1/ones/incl/ctl-none/positive_count-bottom | 1 | 1024.0 | 1.000 | 1.000 | True |
| never_named_ranked/E/D_unif/tau0.1/ones/incl/ctl-none/positive_count-bottom | 2 | 1024.0 | 1.000 | 1.000 | True |
| never_named_ranked/E/D_unif/tau0.1/ones/incl/ctl-none/positive_count-bottom | 3 | 1024.0 | 1.000 | 1.000 | True |
| never_named_ranked/E/D_unif/tau0.1/ones/incl/ctl-none/positive_count-bottom | 4 | 1024.0 | 1.000 | 1.000 | True |
| never_named_ranked/E/D_unif/tau0.1/ones/incl/ctl-none/positive_count-bottom | 5 | 1024.0 | 1.000 | 1.000 | True |
| never_named_ranked/E/D_unif/tau0.1/ones/incl/ctl-none/positive_count-bottom | 6 | 1024.0 | 1.000 | 1.000 | True |
| never_named_ranked/E/D_unif/tau0.1/ones/incl/ctl-none/positive_count-bottom | 7 | 1024.0 | 1.000 | 1.000 | True |
| never_named_ranked/E/D_unif/tau0.1/ones/incl/ctl-none/positive_count-bottom | B50 | 1024.0 | 1.000 | 1.000 | True |
| never_named_ranked/E/D_unif/tau0.1/ones/incl/ctl-none/positive_count-bottom | B75 | 1022.0 | 0.998 | 0.998 | True |
| never_named_ranked/E/D_unif/tau0.1/ones/incl/ctl-none/positive_count-top | 1 | 1024.0 | 1.000 | 1.000 | True |
| never_named_ranked/E/D_unif/tau0.1/ones/incl/ctl-none/positive_count-top | 2 | 1023.0 | 0.999 | 0.998 | True |
| never_named_ranked/E/D_unif/tau0.1/ones/incl/ctl-none/positive_count-top | 3 | 1021.0 | 0.997 | 0.996 | True |
| never_named_ranked/E/D_unif/tau0.1/ones/incl/ctl-none/positive_count-top | 4 | 1020.0 | 0.996 | 0.995 | True |
| never_named_ranked/E/D_unif/tau0.1/ones/incl/ctl-none/positive_count-top | 5 | 1020.0 | 0.996 | 0.995 | True |
| never_named_ranked/E/D_unif/tau0.1/ones/incl/ctl-none/positive_count-top | 6 | 1020.0 | 0.996 | 0.995 | True |
| never_named_ranked/E/D_unif/tau0.1/ones/incl/ctl-none/positive_count-top | 7 | 1020.0 | 0.996 | 0.995 | True |
| never_named_ranked/E/D_unif/tau0.1/ones/incl/ctl-none/positive_count-top | B50 | 1020.0 | 0.996 | 0.995 | True |
| never_named_ranked/E/D_unif/tau0.1/ones/incl/ctl-none/positive_count-top | B75 | 1020.0 | 0.996 | 0.995 | True |
| never_named_ranked/E/D_unif/tau0.1/ones/incl/ctl-none/weight_norm-bottom | 1 | 1023.0 | 0.999 | 0.999 | True |
| never_named_ranked/E/D_unif/tau0.1/ones/incl/ctl-none/weight_norm-bottom | 2 | 1023.0 | 0.999 | 0.999 | True |
| never_named_ranked/E/D_unif/tau0.1/ones/incl/ctl-none/weight_norm-bottom | 3 | 1022.0 | 0.998 | 0.997 | True |
| never_named_ranked/E/D_unif/tau0.1/ones/incl/ctl-none/weight_norm-bottom | 4 | 1022.0 | 0.998 | 0.997 | True |
| never_named_ranked/E/D_unif/tau0.1/ones/incl/ctl-none/weight_norm-bottom | 5 | 1022.0 | 0.998 | 0.997 | True |
| never_named_ranked/E/D_unif/tau0.1/ones/incl/ctl-none/weight_norm-bottom | 6 | 1022.0 | 0.998 | 0.997 | True |
| never_named_ranked/E/D_unif/tau0.1/ones/incl/ctl-none/weight_norm-bottom | 7 | 1022.0 | 0.998 | 0.997 | True |
| never_named_ranked/E/D_unif/tau0.1/ones/incl/ctl-none/weight_norm-bottom | B50 | 1022.0 | 0.998 | 0.997 | True |
| never_named_ranked/E/D_unif/tau0.1/ones/incl/ctl-none/weight_norm-bottom | B75 | 1020.0 | 0.996 | 0.995 | True |
| never_named_ranked/E/D_unif/tau0.1/ones/incl/ctl-none/weight_norm-top | 1 | 1024.0 | 1.000 | 1.000 | True |
| never_named_ranked/E/D_unif/tau0.1/ones/incl/ctl-none/weight_norm-top | 2 | 1023.0 | 0.999 | 0.999 | True |
| never_named_ranked/E/D_unif/tau0.1/ones/incl/ctl-none/weight_norm-top | 3 | 1023.0 | 0.999 | 0.999 | True |
| never_named_ranked/E/D_unif/tau0.1/ones/incl/ctl-none/weight_norm-top | 4 | 1023.0 | 0.999 | 0.999 | True |
| never_named_ranked/E/D_unif/tau0.1/ones/incl/ctl-none/weight_norm-top | 5 | 1021.0 | 0.997 | 0.997 | True |
| never_named_ranked/E/D_unif/tau0.1/ones/incl/ctl-none/weight_norm-top | 6 | 1021.0 | 0.997 | 0.997 | True |
| never_named_ranked/E/D_unif/tau0.1/ones/incl/ctl-none/weight_norm-top | 7 | 1021.0 | 0.997 | 0.997 | True |
| never_named_ranked/E/D_unif/tau0.1/ones/incl/ctl-none/weight_norm-top | B50 | 1021.0 | 0.997 | 0.997 | True |
| never_named_ranked/E/D_unif/tau0.1/ones/incl/ctl-none/weight_norm-top | B75 | 1021.0 | 0.997 | 0.997 | True |

## 7. Switched mass under the non-uniform backgrounds (float64 from the caches; tables sigma_E.parquet, sigma_E_lab.parquet, sigma_donors.parquet)

- E: {'bytes': 16696218, 'n_cells': 1669, 'n_sequences': 1024}
- E_lab: {'bytes': 7183795, 'n_cells': 1408, 'n_sequences': 512}
- donors: {'n_cells': 16, 'rows': 520}
The union (tau = 0.1, r = 0) pooled over rungs 1 to 7 with 5a and 6a and all draws: 73728 points from 72 cells; deciles (0 to 100 by 10): 23.14, 202.80, 1221.75, 4396.41, 5304.61, 6498.04, 7512.85, 8218.71, 8791.39, 9421.11, 9708.94
Its plain control: 73728 points; fraction above the union's top edge 0.000, below its bottom edge 0.000.
Per-rung mean sigma, union then control: 1: 149.42 / 165.91; 2: 1064.40 / 1099.62; 3: 4414.23 / 4463.87; 4: 4771.03 / 4808.71; 5: 7563.52 / 7586.06; 5a: 6360.53 / 6393.86; 6: 8909.08 / 8917.47; 6a: 8339.51 / 8353.47; 7: 9508.07 / 9510.62

## 8. Matched-random controls' overflow into the dead set: 47 of 1500 control cells overflow, 116004 entries in all; by module: {'h.0.attn.k_proj': 1537, 'h.0.attn.o_proj': 1738, 'h.0.attn.q_proj': 1310, 'h.0.attn.v_proj': 1467, 'h.0.mlp.c_fc': 7022, 'h.0.mlp.down_proj': 8413, 'h.1.attn.k_proj': 2018, 'h.1.attn.o_proj': 5072, 'h.1.attn.q_proj': 1811, 'h.1.attn.v_proj': 3756, 'h.1.mlp.c_fc': 10114, 'h.1.mlp.down_proj': 10491, 'h.2.attn.k_proj': 2065, 'h.2.attn.o_proj': 2974, 'h.2.attn.q_proj': 2321, 'h.2.attn.v_proj': 2368, 'h.2.mlp.c_fc': 11720, 'h.2.mlp.down_proj': 12292, 'h.3.attn.k_proj': 2211, 'h.3.attn.o_proj': 4445, 'h.3.attn.q_proj': 2298, 'h.3.attn.v_proj': 4057, 'h.3.mlp.c_fc': 8651, 'h.3.mlp.down_proj': 5853} (per cell in control_overflow.csv)

## 12. The composition of curve 1's small-rung sets against its plain control's (mean over draws): the mean and median weight norm ||U_c|| ||V_c|| and the mean pool usage (the fraction of D_unif positions with g > 0.1) of the subcomponents each set names; per draw in set_composition.csv

| rung | union n_on | union mean norm | union median norm | union mean usage | control mean norm | control median norm | control mean usage |
|---|---|---|---|---|---|---|---|
| 1 | 169 | 1.9149 | 1.2825 | 0.1506 | 0.9350 | 0.8763 | 0.0229 |
| 2 | 1121 | 1.3634 | 1.1409 | 0.0624 | 0.9216 | 0.8629 | 0.0241 |
| 2a | 1974 | 1.2771 | 1.1132 | 0.0512 | 0.9130 | 0.8542 | 0.0236 |
| 2b | 3198 | 1.1929 | 1.0726 | 0.0425 | 0.9052 | 0.8441 | 0.0231 |
| 3 | 4544 | 1.1276 | 1.0269 | 0.0361 | 0.8991 | 0.8361 | 0.0225 |
| 4 | 4890 | 1.0704 | 0.9709 | 0.0322 | 0.8876 | 0.8145 | 0.0214 |
The whole alive set (9959 subcomponents) as the baseline: mean norm 0.8602, median norm 0.7689, mean usage 0.0194. A union set heavier or more used than its control's at the same count would be a rival to the conflict reading.

## 9. The rung-8 excess of the identities' union chain over its rung 0, per sequence (two ends): mean 0.9458, SD over 1024 sequences 0.3141, standard error of the mean 0.00982 against the 0.0016 guessed in advance; SD of rung 0 0.1019, of rung 8 0.2974
