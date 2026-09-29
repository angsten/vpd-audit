# Pre-reads for the control run: label-only numbers from the caches and the sources

## 1. Dead against never named (38912 subcomponents; alive by the saved vector 6355, dead 32557; dead recomputed from the cache 32557, disagreements 0)

| tau | named | never named | dead & never named | dead & named | alive & never named | alive & named |
|---|---|---|---|---|---|---|
| 0 | 32456 | 6456 | 6456 | 26101 | 0 | 6355 |
| 0.1 | 6361 | 32551 | 32548 | 9 | 3 | 6352 |
| 0.5 | 6325 | 32587 | 32557 | 0 | 30 | 6325 |

## 2. The never-named set (tau = 0.1) and the strict set (tau = 0) on the five caches

### never_named_tau0.1: 32551 members

| cache | tau_q | median t* | q1 / q3 | fraction = T | fraction >= 8 | clean-prefix fraction | mean touched positions |
|---|---|---|---|---|---|---|---|
| D_code | 0 | 1 | 0 / 2 | 0.000 | 0.018 | 0.003 | 192.1 |
| D_code | 0.01 | 512 | 512 / 512 | 0.926 | 0.979 | 0.948 | 0.1 |
| D_code | 0.1 | 512 | 512 / 512 | 0.996 | 0.996 | 0.996 | 0.0 |
| D_prose | 0 | 0 | 0 / 2 | 0.000 | 0.023 | 0.003 | 179.7 |
| D_prose | 0.01 | 512 | 512 / 512 | 0.936 | 0.992 | 0.959 | 0.1 |
| D_prose | 0.1 | 512 | 512 / 512 | 0.996 | 1.000 | 0.999 | 0.0 |
| D_unif | 0 | 1 | 0 / 2 | 0.000 | 0.016 | 0.003 | 180.7 |
| D_unif | 0.01 | 512 | 512 / 512 | 0.915 | 0.989 | 0.945 | 0.1 |
| D_unif | 0.1 | 512 | 512 / 512 | 1.000 | 1.000 | 1.000 | 0.0 |
| E | 0 | 1 | 0 / 2 | 0.000 | 0.017 | 0.003 | 178.9 |
| E | 0.01 | 512 | 512 / 512 | 0.909 | 0.990 | 0.941 | 0.2 |
| E | 0.1 | 512 | 512 / 512 | 0.985 | 0.999 | 0.989 | 0.1 |
| E_lab | 0 | 0 | 0 / 2 | 0.000 | 0.008 | 0.002 | 190.8 |
| E_lab | 0.01 | 512 | 512 / 512 | 0.918 | 0.992 | 0.948 | 0.1 |
| E_lab | 0.1 | 512 | 512 / 512 | 0.994 | 1.000 | 0.997 | 0.0 |

| cache | members with any g > 0 | median positions with g > 0 | max g <= 0.01 | 0.01 < max g <= 0.1 | max g > 0.1 | largest max g | labels in the set per position: mean / max / fraction of positions with any |
|---|---|---|---|---|---|---|---|
| D_code | 21823 of 32551 | 2 | 32526 | 24 | 1 | 0.1827 | 0.61 / 35 / 0.375 |
| D_prose | 22048 of 32551 | 2 | 32539 | 11 | 1 | 0.4484 | 0.52 / 25 / 0.351 |
| D_unif | 26095 of 32551 | 5 | 32522 | 29 | 0 | 0.0913 | 0.53 / 41 / 0.353 |
| E | 25948 of 32551 | 5 | 32455 | 43 | 53 | 1.0000 | 0.52 / 55 / 0.349 |
| E_lab | 23225 of 32551 | 2 | 32530 | 20 | 1 | 0.4035 | 0.58 / 32 / 0.373 |

### strict_tau0: 6456 members

| cache | tau_q | median t* | q1 / q3 | fraction = T | fraction >= 8 | clean-prefix fraction | mean touched positions |
|---|---|---|---|---|---|---|---|
| D_code | 0 | 58 | 22 / 153 | 0.057 | 0.930 | 0.236 | 4.1 |
| D_code | 0.01 | 512 | 512 / 512 | 1.000 | 1.000 | 1.000 | 0.0 |
| D_code | 0.1 | 512 | 512 / 512 | 1.000 | 1.000 | 1.000 | 0.0 |
| D_prose | 0 | 119 | 45 / 256 | 0.066 | 0.965 | 0.336 | 2.9 |
| D_prose | 0.01 | 512 | 512 / 512 | 1.000 | 1.000 | 1.000 | 0.0 |
| D_prose | 0.1 | 512 | 512 / 512 | 1.000 | 1.000 | 1.000 | 0.0 |
| D_unif | 0 | 512 | 512 / 512 | 1.000 | 1.000 | 1.000 | 0.0 |
| D_unif | 0.01 | 512 | 512 / 512 | 1.000 | 1.000 | 1.000 | 0.0 |
| D_unif | 0.1 | 512 | 512 / 512 | 1.000 | 1.000 | 1.000 | 0.0 |
| E | 0 | 118 | 45 / 253 | 0.087 | 0.945 | 0.329 | 3.1 |
| E | 0.01 | 512 | 512 / 512 | 0.997 | 1.000 | 0.998 | 0.0 |
| E | 0.1 | 512 | 512 / 512 | 0.998 | 1.000 | 0.999 | 0.0 |
| E_lab | 0 | 84 | 32 / 216 | 0.043 | 0.924 | 0.278 | 3.8 |
| E_lab | 0.01 | 512 | 512 / 512 | 1.000 | 1.000 | 1.000 | 0.0 |
| E_lab | 0.1 | 512 | 512 / 512 | 1.000 | 1.000 | 1.000 | 0.0 |

| cache | members with any g > 0 | median positions with g > 0 | max g <= 0.01 | 0.01 < max g <= 0.1 | max g > 0.1 | largest max g | labels in the set per position: mean / max / fraction of positions with any |
|---|---|---|---|---|---|---|---|
| D_code | 1151 of 6456 | 0 | 6456 | 0 | 0 | 0.0043 | 0.01 / 3 / 0.008 |
| D_prose | 969 of 6456 | 0 | 6456 | 0 | 0 | 0.0039 | 0.01 / 3 / 0.006 |
| D_unif | 0 of 6456 | 0 | 6456 | 0 | 0 | 0.0000 | 0.00 / 0 / 0.000 |
| E | 1778 of 6456 | 0 | 6451 | 4 | 1 | 0.8998 | 0.01 / 6 / 0.006 |
| E_lab | 1169 of 6456 | 0 | 6456 | 0 | 0 | 0.0043 | 0.01 / 3 / 0.007 |

## 3. Union against its plain control at tau = 0.1: the fraction of the union set the control also names (mean over draws), beside n_on / |alive|

| rung | n_on | overlap fraction | expected n_on / alive |
|---|---|---|---|
| 1 | 61 | 0.016 | 0.010 |
| 2 | 392 | 0.085 | 0.062 |
| 2a | 670 | 0.137 | 0.105 |
| 2b | 1135 | 0.224 | 0.179 |
| 3 | 1792 | 0.328 | 0.282 |
| 4 | 2484 | 0.414 | 0.391 |
| 5 | 4394 | 0.709 | 0.691 |
| 6 | 5516 | 0.875 | 0.868 |
| 7 | 6053 | 0.954 | 0.952 |
| 8 | 6361 | 0.998 | 1.001 |
Per matrix in overlap_union_vs_control.csv.

## 4. E2's coverage: the fraction of alive subcomponents the union names (mean over draws; per layer in coverage.csv)

| tau | rung 1 | rung 2 | rung 2a | rung 2b | rung 3 | rung 4 | rung 5 | rung 6 | rung 7 | rung 8 |
|---|---|---|---|---|---|---|---|---|---|---|
| 0 | 0.010 | 0.068 |  |  | 0.307 | 0.438 | 0.760 | 0.935 | 0.991 | 1.000 |
| 0.1 | 0.010 | 0.062 | 0.105 | 0.179 | 0.282 | 0.391 | 0.691 | 0.868 | 0.952 | 1.000 |
| 0.5 | 0.007 | 0.045 |  |  | 0.220 | 0.324 | 0.622 | 0.826 | 0.931 | 0.995 |
Overlap between draws at rung 7 (tau = 0.1): pairwise Jaccard mean 0.957 (min 0.941, max 0.969, 28 pairs); intersection of all draws 5680, union 6335.

## 5. The union's n_on at tau = 0 (draw/rung): k0/r1: 90, k0/r2: 493, k0/r3: 2046, k0/r4: 4120, k0/r5: 5927, k0/r6: 9748, k0/r7: 16642, k0/r8: 32456, k1/r1: 81, k1/r2: 459, k1/r3: 1923, k1/r4: 2499, k1/r5: 5575, k1/r6: 9242, k1/r7: 16237, k2/r1: 84, k2/r2: 400, k2/r3: 2026, k2/r4: 3436, k2/r5: 6103, k2/r6: 9468, k2/r7: 16407, k3/r1: 60, k3/r2: 661, k3/r3: 2065, k3/r4: 634, k3/r5: 5583, k3/r6: 9221, k3/r7: 16456, k4/r1: 104, k4/r2: 426, k4/r3: 1795, k4/r4: 3220, k4/r5: 6304, k4/r6: 9758, k4/r7: 16563, k5/r1: 52, k5/r2: 320, k5/r3: 2102, k5/r4: 3748, k5/r5: 5923, k5/r6: 9445, k5/r7: 16240, k6/r1: 14, k6/r2: 349, k6/r3: 1949, k6/r4: 3371, k6/r5: 5657, k6/r6: 9428, k6/r7: 16237, k7/r1: 39, k7/r2: 389, k7/r3: 1951, k7/r4: 3099, k7/r5: 5275, k7/r6: 9127, k7/r7: 16160
Never-named set at tau = 0.1: 32551; the strict never-named set at tau = 0: 6456.

## 6. Testability of the hard-zero chains (1182 cells, 910 distinct erased sets, 22 chains; per-sequence t* in t_star.parquet, 849408 rows; the full table in testability.csv)

Rungs meeting the readability floor at tau_q = 0.1 on the whole set (at least 64 contributing on average over draws, clean-prefix fraction at least 0.05):

| chain | testable rungs |
|---|---|
| code_specific_hard/E/D_code/tau0.1/ones/incl/ctl-none | 1, 2, 3, 4, 5, 6, 7, 8, S4, S16, S64 |
| code_specific_hard/E_lab/D_code/tau0.1/ones/excl/ctl-none | 1, 2, 3, 4, 5, 6, 7, 8, S4, S16, S64 |
| code_specific_hard/E_lab/D_code/tau0.1/ones/incl/ctl-complement | 1, 2, 3, 4, 5, 6, 7, 8, S4, S16, S64 |
| code_specific_hard/E_lab/D_code/tau0.1/ones/incl/ctl-none | 1, 2, 3, 4, 5, 6, 7, 8, S4, S16, S64 |
| code_specific_hard/E_lab/D_code/tau0.1/ones/incl/ctl-plain | 1, 2, 3, 4, S4 |
| code_specific_hard/E_lab/D_code/tau0.5/ones/incl/ctl-complement | 1, 2, 3, 4, 5, 6, 7, 8, S4, S16, S64 |
| code_specific_hard/E_lab/D_code/tau0.5/ones/incl/ctl-none | 1, 2, 3, 4, 5, 6, 7, 8, S4, S16, S64 |
| code_specific_hard/E_lab/D_code/tau0.5/ones/incl/ctl-plain | 1, 2, 3 |
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
| never_named_hard/E/D_unif/tau0.1/ones/incl/ctl-none | 1, 2, 3, 4, 5, 6, 7, B50, B75, 8 |
| never_named_hard/E/D_unif/tau0/ones/incl/ctl-none | 8 |

Clean-prefix fraction and contributing count at tau_q = 0.1 (mean over draws), whole set, per chain and rung:

| chain | rung | mean contributing | mean clean-prefix fraction | fraction never touched | floor met |
|---|---|---|---|---|---|
| code_specific_hard/E/D_code/tau0.1/ones/incl/ctl-none | 1 | 1024.0 | 1.000 | 1.000 | True |
| code_specific_hard/E/D_code/tau0.1/ones/incl/ctl-none | 2 | 1022.5 | 0.976 | 0.963 | True |
| code_specific_hard/E/D_code/tau0.1/ones/incl/ctl-none | 3 | 1011.9 | 0.890 | 0.841 | True |
| code_specific_hard/E/D_code/tau0.1/ones/incl/ctl-none | 4 | 1001.9 | 0.868 | 0.812 | True |
| code_specific_hard/E/D_code/tau0.1/ones/incl/ctl-none | 5 | 949.8 | 0.701 | 0.599 | True |
| code_specific_hard/E/D_code/tau0.1/ones/incl/ctl-none | 6 | 870.9 | 0.500 | 0.380 | True |
| code_specific_hard/E/D_code/tau0.1/ones/incl/ctl-none | 7 | 842.9 | 0.452 | 0.333 | True |
| code_specific_hard/E/D_code/tau0.1/ones/incl/ctl-none | 8 | 819.0 | 0.432 | 0.314 | True |
| code_specific_hard/E/D_code/tau0.1/ones/incl/ctl-none | S4 | 1010.0 | 0.860 | 0.800 | True |
| code_specific_hard/E/D_code/tau0.1/ones/incl/ctl-none | S16 | 958.0 | 0.751 | 0.678 | True |
| code_specific_hard/E/D_code/tau0.1/ones/incl/ctl-none | S64 | 877.0 | 0.481 | 0.356 | True |
| code_specific_hard/E_lab/D_code/tau0.1/ones/excl/ctl-none | 1 | 512.0 | 1.000 | 1.000 | True |
| code_specific_hard/E_lab/D_code/tau0.1/ones/excl/ctl-none | 2 | 510.2 | 0.928 | 0.901 | True |
| code_specific_hard/E_lab/D_code/tau0.1/ones/excl/ctl-none | 3 | 499.9 | 0.714 | 0.628 | True |
| code_specific_hard/E_lab/D_code/tau0.1/ones/excl/ctl-none | 4 | 491.2 | 0.696 | 0.608 | True |
| code_specific_hard/E_lab/D_code/tau0.1/ones/excl/ctl-none | 5 | 457.1 | 0.505 | 0.406 | True |
| code_specific_hard/E_lab/D_code/tau0.1/ones/excl/ctl-none | 6 | 414.6 | 0.406 | 0.322 | True |
| code_specific_hard/E_lab/D_code/tau0.1/ones/excl/ctl-none | 7 | 398.9 | 0.367 | 0.288 | True |
| code_specific_hard/E_lab/D_code/tau0.1/ones/excl/ctl-none | 8 | 391.0 | 0.360 | 0.283 | True |
| code_specific_hard/E_lab/D_code/tau0.1/ones/excl/ctl-none | S4 | 487.0 | 0.596 | 0.506 | True |
| code_specific_hard/E_lab/D_code/tau0.1/ones/excl/ctl-none | S16 | 442.0 | 0.531 | 0.459 | True |
| code_specific_hard/E_lab/D_code/tau0.1/ones/excl/ctl-none | S64 | 413.0 | 0.386 | 0.297 | True |
| code_specific_hard/E_lab/D_code/tau0.1/ones/incl/ctl-complement | 1 | 512.0 | 1.000 | 1.000 | True |
| code_specific_hard/E_lab/D_code/tau0.1/ones/incl/ctl-complement | 2 | 511.1 | 0.963 | 0.948 | True |
| code_specific_hard/E_lab/D_code/tau0.1/ones/incl/ctl-complement | 3 | 508.2 | 0.912 | 0.873 | True |
| code_specific_hard/E_lab/D_code/tau0.1/ones/incl/ctl-complement | 4 | 508.8 | 0.936 | 0.899 | True |
| code_specific_hard/E_lab/D_code/tau0.1/ones/incl/ctl-complement | 5 | 495.2 | 0.695 | 0.570 | True |
| code_specific_hard/E_lab/D_code/tau0.1/ones/incl/ctl-complement | 6 | 477.0 | 0.551 | 0.420 | True |
| code_specific_hard/E_lab/D_code/tau0.1/ones/incl/ctl-complement | 7 | 457.5 | 0.490 | 0.374 | True |
| code_specific_hard/E_lab/D_code/tau0.1/ones/incl/ctl-complement | 8 | 416.0 | 0.391 | 0.305 | True |
| code_specific_hard/E_lab/D_code/tau0.1/ones/incl/ctl-complement | S4 | 504.0 | 0.832 | 0.732 | True |
| code_specific_hard/E_lab/D_code/tau0.1/ones/incl/ctl-complement | S16 | 495.0 | 0.700 | 0.553 | True |
| code_specific_hard/E_lab/D_code/tau0.1/ones/incl/ctl-complement | S64 | 472.0 | 0.510 | 0.379 | True |
| code_specific_hard/E_lab/D_code/tau0.1/ones/incl/ctl-none | 1 | 512.0 | 1.000 | 1.000 | True |
| code_specific_hard/E_lab/D_code/tau0.1/ones/incl/ctl-none | 2 | 510.2 | 0.928 | 0.901 | True |
| code_specific_hard/E_lab/D_code/tau0.1/ones/incl/ctl-none | 3 | 499.9 | 0.714 | 0.628 | True |
| code_specific_hard/E_lab/D_code/tau0.1/ones/incl/ctl-none | 4 | 491.2 | 0.696 | 0.608 | True |
| code_specific_hard/E_lab/D_code/tau0.1/ones/incl/ctl-none | 5 | 457.1 | 0.505 | 0.406 | True |
| code_specific_hard/E_lab/D_code/tau0.1/ones/incl/ctl-none | 6 | 414.6 | 0.406 | 0.322 | True |
| code_specific_hard/E_lab/D_code/tau0.1/ones/incl/ctl-none | 7 | 398.9 | 0.367 | 0.288 | True |
| code_specific_hard/E_lab/D_code/tau0.1/ones/incl/ctl-none | 8 | 391.0 | 0.360 | 0.283 | True |
| code_specific_hard/E_lab/D_code/tau0.1/ones/incl/ctl-none | S4 | 487.0 | 0.596 | 0.506 | True |
| code_specific_hard/E_lab/D_code/tau0.1/ones/incl/ctl-none | S16 | 442.0 | 0.531 | 0.459 | True |
| code_specific_hard/E_lab/D_code/tau0.1/ones/incl/ctl-none | S64 | 413.0 | 0.386 | 0.297 | True |
| code_specific_hard/E_lab/D_code/tau0.1/ones/incl/ctl-plain | 1 | 512.0 | 1.000 | 1.000 | True |
| code_specific_hard/E_lab/D_code/tau0.1/ones/incl/ctl-plain | 2 | 451.8 | 0.872 | 0.869 | True |
| code_specific_hard/E_lab/D_code/tau0.1/ones/incl/ctl-plain | 3 | 412.9 | 0.512 | 0.430 | True |
| code_specific_hard/E_lab/D_code/tau0.1/ones/incl/ctl-plain | 4 | 412.4 | 0.316 | 0.213 | True |
| code_specific_hard/E_lab/D_code/tau0.1/ones/incl/ctl-plain | 5 | 99.4 | 0.012 | 0.000 | False |
| code_specific_hard/E_lab/D_code/tau0.1/ones/incl/ctl-plain | 6 | 2.2 | 0.000 | 0.000 | False |
| code_specific_hard/E_lab/D_code/tau0.1/ones/incl/ctl-plain | 7 | 0.0 | 0.000 | 0.000 | False |
| code_specific_hard/E_lab/D_code/tau0.1/ones/incl/ctl-plain | 8 | 0.0 | 0.000 | 0.000 | False |
| code_specific_hard/E_lab/D_code/tau0.1/ones/incl/ctl-plain | S4 | 489.0 | 0.515 | 0.336 | True |
| code_specific_hard/E_lab/D_code/tau0.1/ones/incl/ctl-plain | S16 | 298.0 | 0.037 | 0.000 | False |
| code_specific_hard/E_lab/D_code/tau0.1/ones/incl/ctl-plain | S64 | 0.0 | 0.000 | 0.000 | False |
| code_specific_hard/E_lab/D_code/tau0.5/ones/incl/ctl-complement | 1 | 512.0 | 1.000 | 1.000 | True |
| code_specific_hard/E_lab/D_code/tau0.5/ones/incl/ctl-complement | 2 | 508.9 | 0.968 | 0.955 | True |
| code_specific_hard/E_lab/D_code/tau0.5/ones/incl/ctl-complement | 3 | 488.5 | 0.759 | 0.673 | True |
| code_specific_hard/E_lab/D_code/tau0.5/ones/incl/ctl-complement | 4 | 479.0 | 0.695 | 0.600 | True |
| code_specific_hard/E_lab/D_code/tau0.5/ones/incl/ctl-complement | 5 | 417.5 | 0.405 | 0.292 | True |
| code_specific_hard/E_lab/D_code/tau0.5/ones/incl/ctl-complement | 6 | 357.5 | 0.294 | 0.206 | True |
| code_specific_hard/E_lab/D_code/tau0.5/ones/incl/ctl-complement | 7 | 307.5 | 0.240 | 0.168 | True |
| code_specific_hard/E_lab/D_code/tau0.5/ones/incl/ctl-complement | 8 | 238.0 | 0.178 | 0.111 | True |
| code_specific_hard/E_lab/D_code/tau0.5/ones/incl/ctl-complement | S4 | 499.0 | 0.853 | 0.762 | True |
| code_specific_hard/E_lab/D_code/tau0.5/ones/incl/ctl-complement | S16 | 475.0 | 0.646 | 0.508 | True |
| code_specific_hard/E_lab/D_code/tau0.5/ones/incl/ctl-complement | S64 | 374.0 | 0.304 | 0.213 | True |
| code_specific_hard/E_lab/D_code/tau0.5/ones/incl/ctl-none | 1 | 512.0 | 1.000 | 1.000 | True |
| code_specific_hard/E_lab/D_code/tau0.5/ones/incl/ctl-none | 2 | 481.4 | 0.783 | 0.721 | True |
| code_specific_hard/E_lab/D_code/tau0.5/ones/incl/ctl-none | 3 | 387.5 | 0.436 | 0.356 | True |
| code_specific_hard/E_lab/D_code/tau0.5/ones/incl/ctl-none | 4 | 345.9 | 0.360 | 0.281 | True |
| code_specific_hard/E_lab/D_code/tau0.5/ones/incl/ctl-none | 5 | 280.5 | 0.270 | 0.205 | True |
| code_specific_hard/E_lab/D_code/tau0.5/ones/incl/ctl-none | 6 | 243.1 | 0.216 | 0.156 | True |
| code_specific_hard/E_lab/D_code/tau0.5/ones/incl/ctl-none | 7 | 220.8 | 0.189 | 0.129 | True |
| code_specific_hard/E_lab/D_code/tau0.5/ones/incl/ctl-none | 8 | 206.0 | 0.153 | 0.090 | True |
| code_specific_hard/E_lab/D_code/tau0.5/ones/incl/ctl-none | S4 | 394.0 | 0.466 | 0.381 | True |
| code_specific_hard/E_lab/D_code/tau0.5/ones/incl/ctl-none | S16 | 324.0 | 0.330 | 0.262 | True |
| code_specific_hard/E_lab/D_code/tau0.5/ones/incl/ctl-none | S64 | 275.0 | 0.251 | 0.189 | True |
| code_specific_hard/E_lab/D_code/tau0.5/ones/incl/ctl-plain | 1 | 512.0 | 1.000 | 1.000 | True |
| code_specific_hard/E_lab/D_code/tau0.5/ones/incl/ctl-plain | 2 | 495.4 | 0.766 | 0.681 | True |
| code_specific_hard/E_lab/D_code/tau0.5/ones/incl/ctl-plain | 3 | 287.8 | 0.093 | 0.028 | True |
| code_specific_hard/E_lab/D_code/tau0.5/ones/incl/ctl-plain | 4 | 85.4 | 0.009 | 0.000 | False |
| code_specific_hard/E_lab/D_code/tau0.5/ones/incl/ctl-plain | 5 | 14.9 | 0.001 | 0.000 | False |
| code_specific_hard/E_lab/D_code/tau0.5/ones/incl/ctl-plain | 6 | 0.1 | 0.000 | 0.000 | False |
| code_specific_hard/E_lab/D_code/tau0.5/ones/incl/ctl-plain | 7 | 0.0 | 0.000 | 0.000 | False |
| code_specific_hard/E_lab/D_code/tau0.5/ones/incl/ctl-plain | 8 | 0.0 | 0.000 | 0.000 | False |
| code_specific_hard/E_lab/D_code/tau0.5/ones/incl/ctl-plain | S4 | 0.0 | 0.000 | 0.000 | False |
| code_specific_hard/E_lab/D_code/tau0.5/ones/incl/ctl-plain | S16 | 0.0 | 0.000 | 0.000 | False |
| code_specific_hard/E_lab/D_code/tau0.5/ones/incl/ctl-plain | S64 | 0.0 | 0.000 | 0.000 | False |
| hard_zero/E/D_code/tau0.1/ones/incl/ctl-none | 1 | 0.0 | 0.000 | 0.000 | False |
| hard_zero/E/D_code/tau0.1/ones/incl/ctl-none | 2 | 0.0 | 0.000 | 0.000 | False |
| hard_zero/E/D_code/tau0.1/ones/incl/ctl-none | 3 | 0.0 | 0.000 | 0.000 | False |
| hard_zero/E/D_code/tau0.1/ones/incl/ctl-none | 4 | 0.0 | 0.000 | 0.000 | False |
| hard_zero/E/D_code/tau0.1/ones/incl/ctl-none | 5 | 0.0 | 0.000 | 0.000 | False |
| hard_zero/E/D_code/tau0.1/ones/incl/ctl-none | 6 | 0.0 | 0.000 | 0.000 | False |
| hard_zero/E/D_code/tau0.1/ones/incl/ctl-none | 7 | 0.0 | 0.000 | 0.000 | False |
| hard_zero/E/D_code/tau0.1/ones/incl/ctl-none | 8 | 0.0 | 0.000 | 0.000 | False |
| hard_zero/E/D_unif/tau0.1/ones/excl/ctl-none | 1 | 0.0 | 0.000 | 0.000 | False |
| hard_zero/E/D_unif/tau0.1/ones/excl/ctl-none | 2 | 0.0 | 0.000 | 0.000 | False |
| hard_zero/E/D_unif/tau0.1/ones/excl/ctl-none | 3 | 0.0 | 0.000 | 0.000 | False |
| hard_zero/E/D_unif/tau0.1/ones/excl/ctl-none | 4 | 0.0 | 0.000 | 0.000 | False |
| hard_zero/E/D_unif/tau0.1/ones/excl/ctl-none | 5 | 0.0 | 0.000 | 0.000 | False |
| hard_zero/E/D_unif/tau0.1/ones/excl/ctl-none | 6 | 0.0 | 0.000 | 0.000 | False |
| hard_zero/E/D_unif/tau0.1/ones/excl/ctl-none | 7 | 0.0 | 0.000 | 0.000 | False |
| hard_zero/E/D_unif/tau0.1/ones/excl/ctl-none | 8 | 0.0 | 0.000 | 0.000 | False |
| hard_zero/E/D_unif/tau0.1/ones/incl/ctl-none | 1 | 0.0 | 0.000 | 0.000 | False |
| hard_zero/E/D_unif/tau0.1/ones/incl/ctl-none | 2 | 0.0 | 0.000 | 0.000 | False |
| hard_zero/E/D_unif/tau0.1/ones/incl/ctl-none | 3 | 0.0 | 0.000 | 0.000 | False |
| hard_zero/E/D_unif/tau0.1/ones/incl/ctl-none | 4 | 0.0 | 0.000 | 0.000 | False |
| hard_zero/E/D_unif/tau0.1/ones/incl/ctl-none | 5 | 0.0 | 0.000 | 0.000 | False |
| hard_zero/E/D_unif/tau0.1/ones/incl/ctl-none | 6 | 0.0 | 0.000 | 0.000 | False |
| hard_zero/E/D_unif/tau0.1/ones/incl/ctl-none | 7 | 0.0 | 0.000 | 0.000 | False |
| hard_zero/E/D_unif/tau0.1/ones/incl/ctl-none | 8 | 0.0 | 0.000 | 0.000 | False |
| hard_zero/E/D_unif/tau0.1/ones/incl/ctl-plain | 1 | 0.0 | 0.000 | 0.000 | False |
| hard_zero/E/D_unif/tau0.1/ones/incl/ctl-plain | 2 | 0.0 | 0.000 | 0.000 | False |
| hard_zero/E/D_unif/tau0.1/ones/incl/ctl-plain | 3 | 0.0 | 0.000 | 0.000 | False |
| hard_zero/E/D_unif/tau0.1/ones/incl/ctl-plain | 4 | 0.0 | 0.000 | 0.000 | False |
| hard_zero/E/D_unif/tau0.1/ones/incl/ctl-plain | 5 | 0.0 | 0.000 | 0.000 | False |
| hard_zero/E/D_unif/tau0.1/ones/incl/ctl-plain | 6 | 0.0 | 0.000 | 0.000 | False |
| hard_zero/E/D_unif/tau0.1/ones/incl/ctl-plain | 7 | 0.0 | 0.000 | 0.000 | False |
| hard_zero/E/D_unif/tau0.1/ones/incl/ctl-plain | 8 | 0.0 | 0.000 | 0.000 | False |
| hard_zero/E/D_unif/tau0.5/ones/incl/ctl-none | 1 | 0.1 | 0.000 | 0.000 | False |
| hard_zero/E/D_unif/tau0.5/ones/incl/ctl-none | 2 | 0.0 | 0.000 | 0.000 | False |
| hard_zero/E/D_unif/tau0.5/ones/incl/ctl-none | 3 | 0.0 | 0.000 | 0.000 | False |
| hard_zero/E/D_unif/tau0.5/ones/incl/ctl-none | 4 | 0.0 | 0.000 | 0.000 | False |
| hard_zero/E/D_unif/tau0.5/ones/incl/ctl-none | 5 | 0.0 | 0.000 | 0.000 | False |
| hard_zero/E/D_unif/tau0.5/ones/incl/ctl-none | 6 | 0.0 | 0.000 | 0.000 | False |
| hard_zero/E/D_unif/tau0.5/ones/incl/ctl-none | 7 | 0.0 | 0.000 | 0.000 | False |
| hard_zero/E/D_unif/tau0.5/ones/incl/ctl-none | 8 | 0.0 | 0.000 | 0.000 | False |
| hard_zero/E/D_unif/tau0.5/ones/incl/ctl-plain | 1 | 2.0 | 0.001 | 0.000 | False |
| hard_zero/E/D_unif/tau0.5/ones/incl/ctl-plain | 2 | 0.0 | 0.000 | 0.000 | False |
| hard_zero/E/D_unif/tau0.5/ones/incl/ctl-plain | 3 | 0.0 | 0.000 | 0.000 | False |
| hard_zero/E/D_unif/tau0.5/ones/incl/ctl-plain | 4 | 0.0 | 0.000 | 0.000 | False |
| hard_zero/E/D_unif/tau0.5/ones/incl/ctl-plain | 5 | 0.0 | 0.000 | 0.000 | False |
| hard_zero/E/D_unif/tau0.5/ones/incl/ctl-plain | 6 | 0.0 | 0.000 | 0.000 | False |
| hard_zero/E/D_unif/tau0.5/ones/incl/ctl-plain | 7 | 0.0 | 0.000 | 0.000 | False |
| hard_zero/E/D_unif/tau0.5/ones/incl/ctl-plain | 8 | 0.0 | 0.000 | 0.000 | False |
| hard_zero/E_lab/D_code/tau0.1/ones/excl/ctl-none | 1 | 0.0 | 0.000 | 0.000 | False |
| hard_zero/E_lab/D_code/tau0.1/ones/excl/ctl-none | 2 | 0.0 | 0.000 | 0.000 | False |
| hard_zero/E_lab/D_code/tau0.1/ones/excl/ctl-none | 3 | 0.0 | 0.000 | 0.000 | False |
| hard_zero/E_lab/D_code/tau0.1/ones/excl/ctl-none | 4 | 0.0 | 0.000 | 0.000 | False |
| hard_zero/E_lab/D_code/tau0.1/ones/excl/ctl-none | 5 | 0.0 | 0.000 | 0.000 | False |
| hard_zero/E_lab/D_code/tau0.1/ones/excl/ctl-none | 6 | 0.0 | 0.000 | 0.000 | False |
| hard_zero/E_lab/D_code/tau0.1/ones/excl/ctl-none | 7 | 0.0 | 0.000 | 0.000 | False |
| hard_zero/E_lab/D_code/tau0.1/ones/excl/ctl-none | 8 | 0.0 | 0.000 | 0.000 | False |
| hard_zero/E_lab/D_code/tau0.1/ones/incl/ctl-none | 1 | 0.0 | 0.000 | 0.000 | False |
| hard_zero/E_lab/D_code/tau0.1/ones/incl/ctl-none | 2 | 0.0 | 0.000 | 0.000 | False |
| hard_zero/E_lab/D_code/tau0.1/ones/incl/ctl-none | 3 | 0.0 | 0.000 | 0.000 | False |
| hard_zero/E_lab/D_code/tau0.1/ones/incl/ctl-none | 4 | 0.0 | 0.000 | 0.000 | False |
| hard_zero/E_lab/D_code/tau0.1/ones/incl/ctl-none | 5 | 0.0 | 0.000 | 0.000 | False |
| hard_zero/E_lab/D_code/tau0.1/ones/incl/ctl-none | 6 | 0.0 | 0.000 | 0.000 | False |
| hard_zero/E_lab/D_code/tau0.1/ones/incl/ctl-none | 7 | 0.0 | 0.000 | 0.000 | False |
| hard_zero/E_lab/D_code/tau0.1/ones/incl/ctl-none | 8 | 0.0 | 0.000 | 0.000 | False |
| hard_zero/E_lab/D_code/tau0.1/ones/incl/ctl-plain | 1 | 33.6 | 0.003 | 0.000 | False |
| hard_zero/E_lab/D_code/tau0.1/ones/incl/ctl-plain | 2 | 0.0 | 0.000 | 0.000 | False |
| hard_zero/E_lab/D_code/tau0.1/ones/incl/ctl-plain | 3 | 0.0 | 0.000 | 0.000 | False |
| hard_zero/E_lab/D_code/tau0.1/ones/incl/ctl-plain | 4 | 0.0 | 0.000 | 0.000 | False |
| hard_zero/E_lab/D_code/tau0.1/ones/incl/ctl-plain | 5 | 0.0 | 0.000 | 0.000 | False |
| hard_zero/E_lab/D_code/tau0.1/ones/incl/ctl-plain | 6 | 0.0 | 0.000 | 0.000 | False |
| hard_zero/E_lab/D_code/tau0.1/ones/incl/ctl-plain | 7 | 0.0 | 0.000 | 0.000 | False |
| hard_zero/E_lab/D_code/tau0.1/ones/incl/ctl-plain | 8 | 0.0 | 0.000 | 0.000 | False |
| hard_zero/E_lab/D_code/tau0.5/ones/incl/ctl-none | 1 | 0.0 | 0.000 | 0.000 | False |
| hard_zero/E_lab/D_code/tau0.5/ones/incl/ctl-none | 2 | 0.0 | 0.000 | 0.000 | False |
| hard_zero/E_lab/D_code/tau0.5/ones/incl/ctl-none | 3 | 0.0 | 0.000 | 0.000 | False |
| hard_zero/E_lab/D_code/tau0.5/ones/incl/ctl-none | 4 | 0.0 | 0.000 | 0.000 | False |
| hard_zero/E_lab/D_code/tau0.5/ones/incl/ctl-none | 5 | 0.0 | 0.000 | 0.000 | False |
| hard_zero/E_lab/D_code/tau0.5/ones/incl/ctl-none | 6 | 0.0 | 0.000 | 0.000 | False |
| hard_zero/E_lab/D_code/tau0.5/ones/incl/ctl-none | 7 | 0.0 | 0.000 | 0.000 | False |
| hard_zero/E_lab/D_code/tau0.5/ones/incl/ctl-none | 8 | 0.0 | 0.000 | 0.000 | False |
| hard_zero/E_lab/D_code/tau0.5/ones/incl/ctl-plain | 1 | 41.4 | 0.004 | 0.000 | False |
| hard_zero/E_lab/D_code/tau0.5/ones/incl/ctl-plain | 2 | 0.0 | 0.000 | 0.000 | False |
| hard_zero/E_lab/D_code/tau0.5/ones/incl/ctl-plain | 3 | 0.0 | 0.000 | 0.000 | False |
| hard_zero/E_lab/D_code/tau0.5/ones/incl/ctl-plain | 4 | 0.0 | 0.000 | 0.000 | False |
| hard_zero/E_lab/D_code/tau0.5/ones/incl/ctl-plain | 5 | 0.0 | 0.000 | 0.000 | False |
| hard_zero/E_lab/D_code/tau0.5/ones/incl/ctl-plain | 6 | 0.0 | 0.000 | 0.000 | False |
| hard_zero/E_lab/D_code/tau0.5/ones/incl/ctl-plain | 7 | 0.0 | 0.000 | 0.000 | False |
| hard_zero/E_lab/D_code/tau0.5/ones/incl/ctl-plain | 8 | 0.0 | 0.000 | 0.000 | False |
| never_named_hard/E/D_unif/tau0.1/ones/excl/ctl-none | 8 | 1023.0 | 0.989 | 0.985 | True |
| never_named_hard/E/D_unif/tau0.1/ones/incl/ctl-none | 1 | 1024.0 | 1.000 | 1.000 | True |
| never_named_hard/E/D_unif/tau0.1/ones/incl/ctl-none | 2 | 1024.0 | 1.000 | 0.999 | True |
| never_named_hard/E/D_unif/tau0.1/ones/incl/ctl-none | 3 | 1023.9 | 0.998 | 0.997 | True |
| never_named_hard/E/D_unif/tau0.1/ones/incl/ctl-none | 4 | 1023.9 | 0.998 | 0.997 | True |
| never_named_hard/E/D_unif/tau0.1/ones/incl/ctl-none | 5 | 1023.8 | 0.997 | 0.996 | True |
| never_named_hard/E/D_unif/tau0.1/ones/incl/ctl-none | 6 | 1023.8 | 0.997 | 0.995 | True |
| never_named_hard/E/D_unif/tau0.1/ones/incl/ctl-none | 7 | 1023.8 | 0.996 | 0.995 | True |
| never_named_hard/E/D_unif/tau0.1/ones/incl/ctl-none | B50 | 1023.4 | 0.993 | 0.991 | True |
| never_named_hard/E/D_unif/tau0.1/ones/incl/ctl-none | B75 | 1023.2 | 0.991 | 0.988 | True |
| never_named_hard/E/D_unif/tau0.1/ones/incl/ctl-none | 8 | 1023.0 | 0.989 | 0.985 | True |
| never_named_hard/E/D_unif/tau0/ones/incl/ctl-none | 8 | 1024.0 | 0.999 | 0.998 | True |

## 7. Switched mass under the non-uniform backgrounds (float64 from the caches; tables sigma_E.parquet, sigma_E_lab.parquet, sigma_donors.parquet)

- E: {'bytes': 13118254, 'n_cells': 1313, 'n_sequences': 1024}
- E_lab: {'bytes': 5337946, 'n_cells': 1104, 'n_sequences': 512}
- donors: {'n_cells': 16, 'rows': 520}
The union (tau = 0.1, r = 0) pooled over rungs 1 to 7 with 5a and 6a and all draws: 57344 points from 56 cells; deciles (0 to 100 by 10): 10.30, 68.32, 345.97, 547.15, 1815.97, 2652.92, 4194.32, 4650.02, 5456.53, 5978.49, 6092.51
Its plain control: 57344 points; fraction above the union's top edge 0.000, below its bottom edge 0.000.
Per-rung mean sigma, union then control: 1: 53.40 / 60.10; 2: 374.54 / 388.42; 3: 1755.81 / 1775.72; 4: 2447.97 / 2463.62; 5: 4348.73 / 4359.82; 6: 5468.56 / 5474.06; 7: 6005.52 / 6007.61

## 8. Matched-random controls' overflow into the dead set: 47 of 1196 control cells overflow, 132032 entries in all; by module: {'h.0.attn.k_proj': 2041, 'h.0.attn.o_proj': 3096, 'h.0.attn.q_proj': 1913, 'h.0.attn.v_proj': 2131, 'h.0.mlp.c_fc': 13337, 'h.0.mlp.down_proj': 11254, 'h.1.attn.k_proj': 2229, 'h.1.attn.o_proj': 4933, 'h.1.attn.q_proj': 1932, 'h.1.attn.v_proj': 3192, 'h.1.mlp.c_fc': 11217, 'h.1.mlp.down_proj': 10350, 'h.2.attn.k_proj': 2366, 'h.2.attn.o_proj': 4509, 'h.2.attn.q_proj': 2372, 'h.2.attn.v_proj': 2116, 'h.2.mlp.c_fc': 10266, 'h.2.mlp.down_proj': 10163, 'h.3.attn.k_proj': 2126, 'h.3.attn.o_proj': 3752, 'h.3.attn.q_proj': 2011, 'h.3.attn.v_proj': 3002, 'h.3.mlp.c_fc': 10376, 'h.3.mlp.down_proj': 11348} (per cell in control_overflow.csv)

## 9. Not available: no identities chain store for this run
