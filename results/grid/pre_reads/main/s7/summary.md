# Tier-4 pre-reads for the main run: label-only numbers, no forward pass

## 1. The marginal-matched control: curve 1's configuration at rungs 1, 2, 2a, 2b, 3, 8 draws, 200 label-only seeds

Candidates (usage above zero at tau = 0.1 on D_unif, 524288 positions): 9966, of which 8 are not in the alive vector (9959); 1 alive subcomponents are not candidates. Overflows of the marginal sampler: 0.

### The gate on the sampler's bias (mean over seeds of the pooled statistic, over the union's pooled value)

| rung | statistic | gated | union_value | plain_value | seeds_mean | seeds_sd | seeds_p2_5 | seeds_p97_5 | ratio_seeds_mean_to_union | bound_low | bound_high | within_bounds | union_percentile_in_seeds | replicate_0_percentile | replicate_1_percentile |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | mean_usage | True | 0.1338 | 0.0236 | 0.1213 | 0.0025 | 0.1160 | 0.1252 | 0.9065 | 0.9 | 1.1 | True | 100.0 | 59.8 | 53.2 |
| 1 | mean_norm | True | 1.7875 | 0.9380 | 1.7232 | 0.0218 | 1.6755 | 1.7617 | 0.9640 | 0.95 | 1.05 | True | 100.0 | 55.8 | 33.8 |
| 1 | mean_sigma | True | 149.4218 | 165.9057 | 151.3290 | 0.3870 | 150.7181 | 152.1441 | 1.0128 | 0.95 | 1.05 | True | 0.0 | 37.2 | 46.2 |
| 2 | mean_usage | True | 0.0615 | 0.0241 | 0.0615 | 0.0003 | 0.0610 | 0.0620 | 0.9996 | 0.9 | 1.1 | True | 54.5 | 88.8 | 49.8 |
| 2 | mean_norm | True | 1.3557 | 0.9206 | 1.3528 | 0.0038 | 1.3455 | 1.3604 | 0.9979 | 0.95 | 1.05 | True | 76.0 | 85.2 | 4.8 |
| 2 | mean_sigma | True | 1064.4031 | 1099.6159 | 1064.5083 | 0.2434 | 1064.0436 | 1064.9639 | 1.0001 | 0.95 | 1.05 | True | 33.5 | 10.8 | 51.2 |
| 2a | mean_usage | True | 0.0511 | 0.0236 | 0.0509 | 0.0001 | 0.0506 | 0.0511 | 0.9954 | 0.9 | 1.1 | True | 97.0 | 78.8 | 55.2 |
| 2a | mean_norm | True | 1.2761 | 0.9127 | 1.2744 | 0.0020 | 1.2706 | 1.2786 | 0.9987 | 0.95 | 1.05 | True | 79.0 | 55.2 | 13.2 |
| 2a | mean_sigma | True | 1892.7473 | 1937.4500 | 1893.2130 | 0.2110 | 1892.8355 | 1893.6522 | 1.0002 | 0.95 | 1.05 | True | 1.5 | 17.8 | 40.8 |
| 2b | mean_usage | False | 0.0425 | 0.0230 | 0.0425 | 0.0001 | 0.0424 | 0.0426 | 1.0012 | 0.9 | 1.1 | True | 22.0 | 74.8 | 4.8 |
| 2b | mean_norm | False | 1.1925 | 0.9050 | 1.1963 | 0.0014 | 1.1934 | 1.1992 | 1.0032 | 0.95 | 1.05 | True | 0.5 | 52.8 | 1.2 |
| 2b | mean_sigma | False | 3090.8112 | 3141.0072 | 3090.6674 | 0.1712 | 3090.3571 | 3090.9879 | 1.0000 | 0.95 | 1.05 | True | 78.5 | 28.8 | 95.2 |
| 3 | mean_usage | False | 0.0361 | 0.0225 | 0.0362 | 0.0000 | 0.0362 | 0.0363 | 1.0030 | 0.9 | 1.1 | True | 0.0 | 10.2 | 22.2 |
| 3 | mean_norm | False | 1.1274 | 0.8990 | 1.1294 | 0.0008 | 1.1280 | 1.1309 | 1.0017 | 0.95 | 1.05 | True | 1.0 | 29.8 | 20.2 |
| 3 | mean_sigma | False | 4414.2331 | 4463.8711 | 4413.9317 | 0.1103 | 4413.7364 | 4414.1605 | 0.9999 | 0.95 | 1.05 | True | 100.0 | 84.8 | 78.2 |

Gate at rungs 1, 2, 2a: **pass**

### The realized eight rung-1 positions among 200 sets of 8 real pool positions (seeds [0, 'posperm', 'D_unif', '<draw>'], draws 8 to 1607; marginal_real_position_sets.csv)

| statistic | realized | sets' mean | SD | min | p5 | p50 | p95 | max | realized percentile |
|---|---|---|---|---|---|---|---|---|---|
| mean_usage | 0.1338 | 0.1216 | 0.0100 | 0.0975 | 0.1073 | 0.1201 | 0.1393 | 0.1546 | 87.5 |
| mean_norm | 1.7875 | 1.7043 | 0.0650 | 1.5244 | 1.6043 | 1.7003 | 1.8179 | 1.8953 | 89.5 |
| n | 1352.0000 | 1574.9900 | 246.0307 | 977.0000 | 1198.6500 | 1564.5000 | 2021.0500 | 2335.0000 | 19.5 |

### Overlap of each control with the union (overlap_mass_pooled is the named constant: total intersection mass over total named mass, over the draws)

| control | family | replicate | rung | overlap_mass_pooled | overlap_mass_mean_of_draw_ratios | overlap_mass_mean_over_texts | overlap_count_pooled | overlap_count_mean_of_draw_ratios | overlap_mass_min_draw | overlap_mass_max_draw |
|---|---|---|---|---|---|---|---|---|---|---|
| marginal | all | 0 | 1 | 0.0917 | 0.0884 | 0.0882 | 0.1472 | 0.1516 | 0.0531 | 0.1316 |
| marginal | all | 0 | 2 | 0.2851 | 0.2797 | 0.2796 | 0.3011 | 0.2961 | 0.2358 | 0.3586 |
| marginal | all | 0 | 2a | 0.4285 | 0.4263 | 0.4263 | 0.4392 | 0.4371 | 0.3869 | 0.4670 |
| marginal | all | 0 | 2b | 0.5905 | 0.5894 | 0.5894 | 0.5978 | 0.5967 | 0.5382 | 0.6146 |
| marginal | all | 0 | 3 | 0.7320 | 0.7315 | 0.7315 | 0.7369 | 0.7364 | 0.7028 | 0.7628 |
| marginal | all | 1 | 1 | 0.0961 | 0.0863 | 0.0861 | 0.1494 | 0.1480 | 0.0131 | 0.1385 |
| marginal | all | 1 | 2 | 0.2790 | 0.2733 | 0.2733 | 0.2948 | 0.2897 | 0.2302 | 0.3361 |
| plain | soft_erase | 0 | 1 | 0.0308 | 0.0271 | 0.0271 | 0.0296 | 0.0259 | 0.0000 | 0.0537 |
| plain | soft_erase | 0 | 2 | 0.1481 | 0.1442 | 0.1442 | 0.1481 | 0.1443 | 0.1088 | 0.1797 |
| plain | soft_erase | 0 | 3 | 0.5358 | 0.5354 | 0.5354 | 0.5356 | 0.5352 | 0.5019 | 0.5584 |
| plain | union | 0 | 1 | 0.0279 | 0.0276 | 0.0276 | 0.0274 | 0.0261 | 0.0079 | 0.0385 |
| plain | union | 0 | 2 | 0.1527 | 0.1489 | 0.1489 | 0.1524 | 0.1487 | 0.1129 | 0.1949 |
| plain | union | 0 | 2a | 0.2524 | 0.2508 | 0.2508 | 0.2521 | 0.2505 | 0.2148 | 0.2890 |
| plain | union | 0 | 2b | 0.3927 | 0.3917 | 0.3917 | 0.3925 | 0.3915 | 0.3639 | 0.4339 |
| plain | union | 0 | 3 | 0.5369 | 0.5364 | 0.5364 | 0.5368 | 0.5363 | 0.5064 | 0.5629 |

Pairwise count overlap between the real draws at the same rung (shared members over the first draw's count, ordered pairs):

| rung | mean | min | max | jaccard |
|---|---|---|---|---|
| 1 | 0.1382 | 0.0360 | 0.3158 | 0.0643 |
| 2 | 0.2805 | 0.1782 | 0.3826 | 0.1607 |
| 2a | 0.4284 | 0.3366 | 0.5168 | 0.2720 |
| 2b | 0.5888 | 0.5094 | 0.6665 | 0.4170 |
| 3 | 0.7322 | 0.6536 | 0.7922 | 0.5774 |

Decisive rungs by the rule (pooled switched-mass overlap of replicate 0 at most 0.3333): union_r0 (primary, rungs 1, 2, 2a, 2b, 3): 1, 2; union_uniform and soft_erase (rungs 1, 2, 3): 1, 2

### Composition, pooled over draws (per draw in marginal_composition.csv)

| control | family | replicate | rung | n | mean_norm | median_norm | p90_norm | mean_usage | median_usage | p90_usage | mean_sigma | n_not_alive |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| union | union | 0 | 1 | 1352 | 1.7875 | 1.2427 | 3.4585 | 0.1338 | 0.0475 | 0.4500 | 149.42 | 0 |
| union | union | 0 | 2 | 8965 | 1.3557 | 1.1368 | 2.1969 | 0.0615 | 0.0366 | 0.1019 | 1064.40 | 0 |
| union | union | 0 | 2a | 15790 | 1.2761 | 1.1127 | 2.0036 | 0.0511 | 0.0344 | 0.0876 | 1892.75 | 0 |
| union | union | 0 | 2b | 25588 | 1.1925 | 1.0714 | 1.7932 | 0.0425 | 0.0302 | 0.0741 | 3090.81 | 0 |
| union | union | 0 | 3 | 36349 | 1.1274 | 1.0271 | 1.6664 | 0.0361 | 0.0256 | 0.0642 | 4414.23 | 0 |
| plain | union | 0 | 1 | 1352 | 0.9380 | 0.8864 | 1.4970 | 0.0236 | 0.0122 | 0.0519 | 165.91 | 0 |
| plain | union | 0 | 2 | 8965 | 0.9206 | 0.8621 | 1.4415 | 0.0241 | 0.0138 | 0.0541 | 1099.62 | 0 |
| plain | union | 0 | 2a | 15790 | 0.9127 | 0.8536 | 1.4360 | 0.0236 | 0.0135 | 0.0531 | 1937.45 | 0 |
| plain | union | 0 | 2b | 25588 | 0.9050 | 0.8444 | 1.4261 | 0.0230 | 0.0132 | 0.0517 | 3141.01 | 0 |
| plain | union | 0 | 3 | 36349 | 0.8990 | 0.8362 | 1.4168 | 0.0225 | 0.0130 | 0.0500 | 4463.87 | 0 |
| plain | soft_erase | 0 | 1 | 1352 | 0.9354 | 0.8881 | 1.4569 | 0.0238 | 0.0121 | 0.0531 | 165.84 | 0 |
| plain | soft_erase | 0 | 2 | 8965 | 0.9110 | 0.8521 | 1.4322 | 0.0238 | 0.0133 | 0.0526 | 1099.80 | 0 |
| plain | soft_erase | 0 | 3 | 36349 | 0.8959 | 0.8305 | 1.4050 | 0.0224 | 0.0128 | 0.0496 | 4464.20 | 0 |
| marginal | all | 0 | 1 | 1352 | 1.7273 | 1.2074 | 3.1973 | 0.1222 | 0.0415 | 0.2744 | 151.16 | 0 |
| marginal | all | 0 | 2 | 8965 | 1.3570 | 1.1437 | 2.1703 | 0.0618 | 0.0376 | 0.1010 | 1064.21 | 0 |
| marginal | all | 0 | 2a | 15790 | 1.2744 | 1.1114 | 1.9694 | 0.0510 | 0.0344 | 0.0860 | 1893.03 | 0 |
| marginal | all | 0 | 2b | 25588 | 1.1963 | 1.0728 | 1.7812 | 0.0426 | 0.0304 | 0.0740 | 3090.57 | 0 |
| marginal | all | 0 | 3 | 36349 | 1.1289 | 1.0294 | 1.6662 | 0.0362 | 0.0257 | 0.0642 | 4414.05 | 0 |
| marginal | all | 1 | 1 | 1352 | 1.7168 | 1.2272 | 3.2627 | 0.1217 | 0.0440 | 0.2619 | 151.25 | 0 |
| marginal | all | 1 | 2 | 8965 | 1.3465 | 1.1358 | 2.1355 | 0.0615 | 0.0372 | 0.1000 | 1064.51 | 0 |

### The usage distribution

| set | n | p0 | p10 | p20 | p30 | p40 | p50 | p60 | p70 | p80 | p90 | p100 | mean | n_above_0.1 | n_above_0.5 | n_above_0.9 | n_at_clip_or_above |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| alive | 9959 | 0.00000 | 0.00016 | 0.00067 | 0.00199 | 0.00495 | 0.00902 | 0.01387 | 0.02037 | 0.03084 | 0.04569 | 0.99849 | 0.01937 | 157 | 20 | 6 | 0 |
| candidates (usage > 0) | 9966 | 0.00000 | 0.00015 | 0.00067 | 0.00199 | 0.00493 | 0.00901 | 0.01384 | 0.02036 | 0.03082 | 0.04568 | 0.99849 | 0.01936 | 157 | 20 | 6 | 0 |

## 2. The code-leaning group: tau = 0.1, 9959 alive subcomponents, 512 code rows and 512 prose rows

Alive subcomponents with a defined selectivity: 9779; passing the floor toward code 6749, toward prose 6869.

| group | n_members | firing_mass | share_of_alive_firing_mass | mean_weight_norm | mean_usage_unif | min_selectivity |
|---|---|---|---|---|---|---|
| G_0.75 | 1862 | 87.5485 | 0.4382 | 0.8492 | 0.01805 | 0.7501 |
| G_0.9 | 1007 | 49.4702 | 0.2476 | 0.7611 | 0.01439 | 0.9001 |
| G_0.95 | 726 | 36.9523 | 0.1849 | 0.7318 | 0.01330 | 0.9500 |
| G_0.99 | 236 | 10.0283 | 0.0502 | 0.6584 | 0.00920 | 0.9901 |
| strict code (code-named, no prose position), no floor | 270 | 0.1048 | 0.0005 | 0.4895 | 0.00017 | 1.0000 |
| strict code, floor passed | 18 | 0.0897 | 0.0004 | 0.4347 | 0.00096 | 1.0000 |
| prose-leaning, s <= 0.25 | 2691 | 91.9777 | 0.4603 | 0.9726 | 0.02248 | 0.0000 |
| prose-leaning, s <= 0.10 | 682 | 28.0283 | 0.1403 | 0.9199 | 0.01992 | 0.0000 |
| prose-leaning, s <= 0.05 | 227 | 14.2666 | 0.0714 | 0.9401 | 0.02303 | 0.0000 |
| prose-leaning, s <= 0.01 | 30 | 0.6423 | 0.0032 | 0.6616 | 0.00552 | 0.0000 |
| strict prose (prose-named, no code position), no floor | 155 | 0.0338 | 0.0002 | 0.5976 | 0.00011 | 0.0000 |
| strict prose, floor passed | 9 | 0.0218 | 0.0001 | 0.5836 | 0.00032 | 0.0000 |

**The existence rule on G_0.9: clear.** M = 49.4702 of 199.81 (share 0.2476; 1007 members); the shuffle null over 200 shuffles: mean 0.00040, 95th percentile 0.00291, maximum 0.00298, against a fifth of M = 9.89404 (mean members under the null 0.2).

Stray code (descriptive): 989 of 1007 members fire in prose, 445745 firings in all; the ten prose rows where the group fires most hold 0.1312 of them (ten of 512 rows at random would hold 0.0195); per member, the share in its own top ten rows: {'mean': 0.5114938878061186, 'median': 0.43846153846153846, 'q1': 0.3029411764705882, 'q3': 0.696969696969697, 'fraction_at_least_0.5': 0.4196157735085945, 'fraction_at_least_0.9': 0.16885743174924167}.

### The chain (rungs are prefixes of G_0.75 ordered by selectivity, then code usage, then the seeded tie permutation)

| rung_size | descriptive | min_selectivity | code_firing_mass | share_of_alive_code_firing_mass | mean_weight_norm | mean_usage_unif | n_matrices |
|---|---|---|---|---|---|---|---|
| 16 | False | 1.0000 | 0.0870 | 0.0004 | 0.4515 | 0.00101 | 7 |
| 64 | False | 0.9974 | 1.1432 | 0.0057 | 0.5348 | 0.00353 | 11 |
| 256 | False | 0.9893 | 11.2334 | 0.0562 | 0.6660 | 0.00948 | 20 |
| 1007 | False | 0.9001 | 49.4702 | 0.2476 | 0.7611 | 0.01439 | 22 |
| 1862 | True | 0.7501 | 87.5485 | 0.4382 | 0.8492 | 0.01805 | 22 |

### The usage-matched control against the group (nearest-neighbour twins, W = 8; mean over draws)

| rung_size | descriptive | judged_by_the_gate | group_mean_weight_norm | control_mean_weight_norm | norm_ratio_control_to_group | group_mean_usage_unif | control_mean_usage_unif | usage_ratio_control_to_group | median_pair_usage_ratio | norm_off_by_more_than_10_percent | usage_off_by_more_than_10_percent | gate_pass | total_shortfall |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 16 | False | False | 0.4515 | 0.4694 | 1.0396 | 0.00101 | 0.00101 | 0.9925 | 1.0023 | False | False | None | 0 |
| 64 | False | True | 0.5348 | 0.5710 | 1.0678 | 0.00353 | 0.00364 | 1.0310 | 1.0000 | False | False | True | 0 |
| 256 | False | True | 0.6660 | 0.6973 | 1.0470 | 0.00948 | 0.00951 | 1.0024 | 0.9990 | False | False | True | 0 |
| 1007 | False | True | 0.7611 | 0.7792 | 1.0238 | 0.01439 | 0.01465 | 1.0182 | 0.9993 | False | False | True | 0 |
| 1862 | True | False | 0.8492 | 0.8580 | 1.0104 | 0.01805 | 0.01891 | 1.0478 | 1.0001 | False | False | None | 0 |

The control's gate (at every non-descriptive rung of at least 64 members the control's mean usage and mean weight norm, as a mean over the draws, lie within 10 percent of the group's) at rungs [64, 256, 1007]: **pass**

### Testability on E_lab (the hard-zero rule's floor: at least 64 contributing texts on average and a clean-prefix fraction of at least 0.05); every stratum in code_leaning_testability.csv

| chain | rung_size | descriptive | tau_q | stratum | n_draws | n_sequences | mean_n_contributing | mean_clean_prefix_fraction | fraction_never_touched | floor_met |
|---|---|---|---|---|---|---|---|---|---|---|
| group | 16 | False | tau_q0.1 | Github | 1 | 256 | 156.0 | 0.1462 | 0.0742 | True |
| group | 16 | False | tau_q0.1 | other | 1 | 256 | 238.0 | 0.7320 | 0.6484 | True |
| group | 16 | False | tau_q0 | Github | 1 | 256 | 136.0 | 0.1067 | 0.0195 | True |
| group | 16 | False | tau_q0 | other | 1 | 256 | 230.0 | 0.5127 | 0.3242 | True |
| control | 16 | False | tau_q0.1 | Github | 8 | 256 | 146.2 | 0.2955 | 0.1572 | True |
| control | 16 | False | tau_q0.1 | other | 8 | 256 | 133.2 | 0.1172 | 0.0195 | True |
| control | 16 | False | tau_q0 | Github | 8 | 256 | 130.6 | 0.1864 | 0.0591 | True |
| control | 16 | False | tau_q0 | other | 8 | 256 | 123.6 | 0.0869 | 0.0068 | True |
| group | 64 | False | tau_q0.1 | Github | 1 | 256 | 47.0 | 0.0506 | 0.0156 | False |
| group | 64 | False | tau_q0.1 | other | 1 | 256 | 179.0 | 0.3940 | 0.2773 | True |
| group | 64 | False | tau_q0 | Github | 1 | 256 | 36.0 | 0.0193 | 0.0000 | False |
| group | 64 | False | tau_q0 | other | 1 | 256 | 168.0 | 0.1386 | 0.0039 | True |
| control | 64 | False | tau_q0.1 | Github | 8 | 256 | 2.0 | 0.0005 | 0.0000 | False |
| control | 64 | False | tau_q0.1 | other | 8 | 256 | 0.6 | 0.0001 | 0.0000 | False |
| control | 64 | False | tau_q0 | Github | 8 | 256 | 1.6 | 0.0003 | 0.0000 | False |
| control | 64 | False | tau_q0 | other | 8 | 256 | 0.5 | 0.0001 | 0.0000 | False |
| group | 256 | False | tau_q0.1 | Github | 1 | 256 | 4.0 | 0.0013 | 0.0000 | False |
| group | 256 | False | tau_q0.1 | other | 1 | 256 | 95.0 | 0.0465 | 0.0000 | False |
| group | 256 | False | tau_q0 | Github | 1 | 256 | 3.0 | 0.0011 | 0.0000 | False |
| group | 256 | False | tau_q0 | other | 1 | 256 | 70.0 | 0.0131 | 0.0000 | False |
| control | 256 | False | tau_q0.1 | Github | 8 | 256 | 0.0 | 0.0000 | 0.0000 | False |
| control | 256 | False | tau_q0.1 | other | 8 | 256 | 0.0 | 0.0000 | 0.0000 | False |
| control | 256 | False | tau_q0 | Github | 8 | 256 | 0.0 | 0.0000 | 0.0000 | False |
| control | 256 | False | tau_q0 | other | 8 | 256 | 0.0 | 0.0000 | 0.0000 | False |
| group | 1007 | False | tau_q0.1 | Github | 1 | 256 | 0.0 | 0.0000 | 0.0000 | False |
| group | 1007 | False | tau_q0.1 | other | 1 | 256 | 0.0 | 0.0000 | 0.0000 | False |
| group | 1007 | False | tau_q0 | Github | 1 | 256 | 0.0 | 0.0000 | 0.0000 | False |
| group | 1007 | False | tau_q0 | other | 1 | 256 | 0.0 | 0.0000 | 0.0000 | False |
| control | 1007 | False | tau_q0.1 | Github | 8 | 256 | 0.0 | 0.0000 | 0.0000 | False |
| control | 1007 | False | tau_q0.1 | other | 8 | 256 | 0.0 | 0.0000 | 0.0000 | False |
| control | 1007 | False | tau_q0 | Github | 8 | 256 | 0.0 | 0.0000 | 0.0000 | False |
| control | 1007 | False | tau_q0 | other | 8 | 256 | 0.0 | 0.0000 | 0.0000 | False |
| group | 1862 | True | tau_q0.1 | Github | 1 | 256 | 0.0 | 0.0000 | 0.0000 | False |
| group | 1862 | True | tau_q0.1 | other | 1 | 256 | 0.0 | 0.0000 | 0.0000 | False |
| group | 1862 | True | tau_q0 | Github | 1 | 256 | 0.0 | 0.0000 | 0.0000 | False |
| group | 1862 | True | tau_q0 | other | 1 | 256 | 0.0 | 0.0000 | 0.0000 | False |
| control | 1862 | True | tau_q0.1 | Github | 8 | 256 | 0.0 | 0.0000 | 0.0000 | False |
| control | 1862 | True | tau_q0.1 | other | 8 | 256 | 0.0 | 0.0000 | 0.0000 | False |
| control | 1862 | True | tau_q0 | Github | 8 | 256 | 0.0 | 0.0000 | 0.0000 | False |
| control | 1862 | True | tau_q0 | other | 8 | 256 | 0.0 | 0.0000 | 0.0000 | False |
