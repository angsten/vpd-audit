# The frozen analysis of tier 5 (main)

Every reading rule below was fixed before any tier-5 store existed; the words are the rules' output (`vpd_audit/stats_s9.py`), and nothing here goes beyond what the rules return.

## 0. What was asserted before anything was read

- Stores: D_unif__self_merge, E__plain_terms, E__self_merge, E_lab__plain_terms, E_lab__same_domain, E_lab__self_merge; each complete, every cell holding every text once. Commit c57fc2b543b4, dirty flag 0; --frozen c57fc2b543b4a3a0b8587e403a66be249a85670f.
- The bitwise canary against the committed stores: D_unif__self_merge: 0 cells over 0 (cell, text) pairs, of which 0 re-run cells; E__plain_terms: 99 cells over 101376 (cell, text) pairs, of which 74 re-run cells; E__self_merge: 25 cells over 25600 (cell, text) pairs, of which 0 re-run cells; E_lab__plain_terms: 28 cells over 14336 (cell, text) pairs, of which 3 re-run cells; E_lab__same_domain: 25 cells over 12800 (cell, text) pairs, of which 0 re-run cells; E_lab__self_merge: 25 cells over 12800 (cell, text) pairs, of which 0 re-run cells.
- The references and the target's arrays agree bitwise across the tier-5 stores of each set: D_unif: 1 stores; E: 2 stores; E_lab: 3 stores.
- Counts and the rotation (rule 3): {"E/within": {"n_shifts": 4, "partner_n_on_equals_column": true, "received_count_is_the_partners_own": true, "self_mean_count_equals_each_shift": true}, "E_lab/source": {"n_shifts": 4, "partner_n_on_equals_column": true, "received_count_is_the_partners_own": true, "self_mean_count_equals_each_shift": true, "partner_in_own_source": true, "balanced_per_source": true, "same_document_is_the_index": true, "n_same_document_pairs": 139}, "E_lab/general": {"n_shifts": 4, "partner_n_on_equals_column": true, "received_count_is_the_partners_own": true}}.
- The gate of rule 1 (the rates recomputed from the arrays, ties included, equal the stored per-text columns bit for bit): {"E__plain_terms": {"n_listed_cells_gated": 79, "pass": true}, "E__self_merge": {"n_listed_cells_gated": 4, "pass": true}, "E_lab__plain_terms": {"n_listed_cells_gated": 8, "pass": true}, "E_lab__same_domain": {"n_listed_cells_gated": 35, "pass": true}, "E_lab__self_merge": {"n_listed_cells_gated": 3, "pass": true}, "D_unif__self_merge": {"n_listed_cells_gated": 0, "pass": true}}.
- Documents of E_lab: {"E": {"texts": 1024, "documents": null}, "D_unif": {"texts": 1024, "documents": null}, "G": {"texts": 256, "documents": 69}, "P": {"texts": 128, "documents": 58}, "O": {"texts": 256, "documents": 105}, "E_lab": {"texts": 512, "documents": 174}, "source:Github": {"texts": 256, "documents": 69}, "source:Pile-CC": {"texts": 64, "documents": 25}, "source:Wikipedia (en)": {"texts": 64, "documents": 33}, "source:StackExchange": {"texts": 64, "documents": 44}, "source:ArXiv": {"texts": 64, "documents": 3}}. 10000 bootstrap replicates; master seed 0.

On E_lab the primary interval resamples documents within source; the row-level interval is printed beside it and never read. A stratum that pools several sources keeps the design's mix in every replicate: each statistic is taken per source and the sources are combined with fixed weights, their row shares, so point estimates are plain means over rows. A stratum of fewer than ten documents has a point value and no interval. A pooled interval that holds such a source is flagged in its row, and the same value on the stratum without that source is beside it (the columns `…_without_flagged_sources`).

## 1. Run 2: merging within one kind of text

**The gate and the verdict** (arms C and U on the code texts, all ten sizes compared, m = 10):

| gate_arm_U_fails_on_the_code_texts | U_label | C_label | outcome | C_first_detected | C_first_material | U_first_material | sizes_reaching_0.05 | reason | n_documents | outcome_rows_beside_not_read |
|---|---|---|---|---|---|---|---|---|---|---|
| True | fails | fails | F-same | 1 | 2 | 2a |  |  | 69 | F-same |

The two curves of the verdict (s9_run2_curves.csv holds every arm on every stratum and source):

| arm | size_words | rise | interval_documents_lo | interval_documents_hi | interval_rows_beside_lo | interval_rows_beside_hi | n_draws_positive | detected | material | n_on_mean | sigma_mean |
|---|---|---|---|---|---|---|---|---|---|---|---|
| C | 1 token | 0.0185 | 0.0155 | 0.0214 | 0.0170 | 0.0201 | 8 | True | False | 197.8750 | 168.7347 |
| C | 8 tokens | 0.1911 | 0.1518 | 0.2230 | 0.1773 | 0.2058 | 8 | True | True | 975.0000 | 893.5001 |
| C | 16 tokens | 0.3289 | 0.2684 | 0.3820 | 0.3070 | 0.3531 | 8 | True | True | 1552.3750 | 1448.3790 |
| C | 32 tokens | 0.6219 | 0.5319 | 0.7137 | 0.5860 | 0.6607 | 8 | True | True | 2610.1250 | 2478.3856 |
| C | 64 tokens | 0.9016 | 0.7698 | 1.0330 | 0.8531 | 0.9525 | 8 | True | True | 3626.3750 | 3477.2104 |
| C | 1 text | 0.9933 | 0.8405 | 1.1362 | 0.9415 | 1.0473 | 8 | True | True | 5156.3750 | 4999.6757 |
| C | 4 texts | 1.2491 | 1.1453 | 1.3874 | 1.1928 | 1.3070 | 8 | True | True | 7324.5000 | 7156.8748 |
| C | 16 texts | 1.2976 | 1.2046 | 1.4369 | 1.2372 | 1.3589 | 8 | True | True | 8649.7500 | 8480.3183 |
| C | 64 texts | 1.2877 | 1.1957 | 1.4278 | 1.2276 | 1.3493 | 8 | True | True | 9223.2500 | 9053.7063 |
| C | the whole pool | 1.2778 | 1.1855 | 1.4174 | 1.2176 | 1.3392 | 1 | True | True | 9624.0000 | 9454.4465 |
| U | 1 token | 0.0071 | 0.0060 | 0.0085 | 0.0064 | 0.0079 | 5 | False | False | 169.0000 | 150.2711 |
| U | 8 tokens | 0.0568 | 0.0475 | 0.0716 | 0.0527 | 0.0614 | 8 | True | False | 1120.6250 | 1059.4566 |
| U | 16 tokens | 0.1276 | 0.1137 | 0.1449 | 0.1216 | 0.1341 | 8 | True | True | 1973.7500 | 1884.3176 |
| U | 32 tokens | 0.3393 | 0.2846 | 0.4291 | 0.3163 | 0.3648 | 8 | True | True | 3198.5000 | 3075.6057 |
| U | 64 tokens | 0.6076 | 0.5370 | 0.6935 | 0.5738 | 0.6442 | 8 | True | True | 4543.6250 | 4399.0427 |
| U | 1 text | 0.6345 | 0.5854 | 0.7065 | 0.6065 | 0.6654 | 8 | True | True | 4890.2500 | 4755.0435 |
| U | 4 texts | 1.0441 | 0.9590 | 1.1678 | 0.9933 | 1.0997 | 8 | True | True | 7711.0000 | 7547.6871 |
| U | 16 texts | 1.2775 | 1.1869 | 1.4163 | 1.2177 | 1.3403 | 8 | True | True | 9060.0000 | 8890.6791 |
| U | 64 texts | 1.2762 | 1.1843 | 1.4159 | 1.2162 | 1.3378 | 8 | True | True | 9659.2500 | 9489.7036 |
| U | the whole pool | 1.2675 | 1.1756 | 1.4074 | 1.2079 | 1.3291 | 1 | True | True | 9966.0000 | 9796.4459 |

**The match ratio R** (two-level, on log R, level 1 - 0.05/3; read at 8 tokens, 64 tokens, and 64 texts, and only where no replicate is undefined and the two-level interval of each of the four rises, at the same level, has its lower end above zero; printed and not read at one text):

| size_words | r_code | r_prose | R | R_interval_lo | R_interval_hi | all_four_rises_above_zero | nonfinite_share | size_is_read | reading | flag_prose |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 token |  |  |  | 2.7310 | 97.0587 | False | 0.8831 | False | not read |  |
| 8 tokens | 6.8204 | 71.7634 | 22.1236 | 7.3360 | 127.8565 | False | 0.3787 | True | not read |  |
| 16 tokens | 4.7994 | 8.3278 | 6.3220 | 4.1804 | 11.4700 | True | 0.0000 | False | not read |  |
| 32 tokens | 4.3825 | 3.7606 | 4.0597 | 2.9607 | 5.4428 | True | 0.0000 | False | not read |  |
| 64 tokens | 3.4316 | 2.5874 | 2.9797 | 2.3399 | 3.7800 | True | 0.0000 | True | closer is worse |  |
| 1 text | 2.2962 | 1.6925 | 1.9714 | 1.6246 | 2.4813 | True | 0.0000 | False | not read |  |
| 4 texts | 1.4676 | 1.1552 | 1.3021 | 1.2060 | 1.4149 | True | 0.0000 | False | not read |  |
| 16 texts | 1.1056 | 1.0260 | 1.0650 | 1.0461 | 1.0871 | True | 0.0000 | False | not read |  |
| 64 texts | 1.0350 | 1.0066 | 1.0207 | 1.0141 | 1.0281 | True | 0.0000 | True | no material help |  |
| the whole pool | 1.0028 | 1.0025 | 1.0027 | 1.0017 | 1.0036 | True | 0.0000 | False | not read |  |

**Descriptions.** The contrast between code donors and general donors on the code texts (two-level; s9_run2_contrast_C_minus_U.csv), the harm per unit of mask moved from the per-text switched mass (s9_run2_per_unit.csv), each same-size random set against its own arm and no other (s9_run2_controls.csv), and the rises by source (s9_run2_curves.csv). Lambda at 64 tokens: +0.7296, interval [0.5175240175060847, 0.9172405718964913], share of undefined replicates 0.0; pooled; ArXiv contributes 3 documents; the value without it is beside: +0.6397, interval [0.43005073521679577, 0.8299862070679979].

| size_words | rise_C | rise_U | difference | difference_interval_lo | difference_interval_hi | ratio | ratio_interval_lo | ratio_interval_hi | ratio_nonfinite_share | n_on_C | n_on_U | sigma_C | sigma_U |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 token | 0.0185 | 0.0071 | 0.0114 | -0.0033 | 0.0240 | 2.5951 | 0.8146 | 60.2606 | 0.0271 | 197.8750 | 169.0000 | 168.7347 | 150.2711 |
| 8 tokens | 0.1911 | 0.0568 | 0.1343 | 0.0779 | 0.1861 | 3.3641 | 1.8781 | 6.5145 | 0.0000 | 975.0000 | 1120.6250 | 893.5001 | 1059.4566 |
| 16 tokens | 0.3289 | 0.1276 | 0.2012 | 0.1261 | 0.2805 | 2.5764 | 1.7742 | 3.8877 | 0.0000 | 1552.3750 | 1973.7500 | 1448.3790 | 1884.3176 |
| 32 tokens | 0.6219 | 0.3393 | 0.2826 | 0.1508 | 0.3867 | 1.8328 | 1.3528 | 2.3542 | 0.0000 | 2610.1250 | 3198.5000 | 2478.3856 | 3075.6057 |
| 64 tokens | 0.9016 | 0.6076 | 0.2940 | 0.1418 | 0.4164 | 1.4839 | 1.2058 | 1.7722 | 0.0000 | 3626.3750 | 4543.6250 | 3477.2104 | 4399.0427 |
| 1 text | 0.9933 | 0.6345 | 0.3589 | 0.1096 | 0.6268 | 1.5656 | 1.1269 | 2.5858 | 0.0000 | 5156.3750 | 4890.2500 | 4999.6757 | 4755.0435 |
| 4 texts | 1.2491 | 1.0441 | 0.2050 | 0.0937 | 0.3324 | 1.1963 | 1.0813 | 1.3551 | 0.0000 | 7324.5000 | 7711.0000 | 7156.8748 | 7547.6871 |
| 16 texts | 1.2976 | 1.2775 | 0.0201 | 0.0098 | 0.0299 | 1.0157 | 1.0077 | 1.0234 | 0.0000 | 8649.7500 | 9060.0000 | 8480.3183 | 8890.6791 |
| 64 texts | 1.2877 | 1.2762 | 0.0116 | 0.0093 | 0.0138 | 1.0091 | 1.0072 | 1.0109 | 0.0000 | 9223.2500 | 9659.2500 | 9053.7063 | 9489.7036 |
| the whole pool | 1.2778 | 1.2675 | 0.0103 | 0.0091 | 0.0115 | 1.0082 | 1.0070 | 1.0091 | 0.0000 | 9624.0000 | 9966.0000 | 9454.4465 | 9796.4459 |

**The count-only prediction** on the code texts (arm U's ten per-size points, made non-decreasing, log-log interpolation, each draw of arm C predicted from its own amount, no extrapolation; level 1 - 0.05/2 at 64 tokens and 64 texts; a quantity with an undefined replicate is not read):

| amount_measured_as | size_words | n_draws_predicted | observed | prediction | log_ratio | interval_lo | interval_hi | nonfinite_share | end_segment_continued_share | readable | reading |
|---|---|---|---|---|---|---|---|---|---|---|---|
| switched mass (primary) | 1 token | 4 | 0.0224 | 0.0116 | 0.6586 |  |  |  |  | False | not read |
| switched mass (primary) | 8 tokens | 8 | 0.1911 | 0.0474 | 1.3938 |  |  |  |  | False | not read |
| switched mass (primary) | 16 tokens | 8 | 0.3289 | 0.0885 | 1.3132 |  |  |  |  | False | not read |
| switched mass (primary) | 32 tokens | 8 | 0.6219 | 0.2220 | 1.0301 |  |  |  |  | False | not read |
| switched mass (primary) | 64 tokens | 8 | 0.9016 | 0.4153 | 0.7752 | 0.5275 | 0.9808 | 0.0000 | 0.0000 | True | above the prediction |
| switched mass (primary) | 1 text | 8 | 0.9933 | 0.6711 | 0.3922 |  |  |  |  | False | not read |
| switched mass (primary) | 4 texts | 8 | 1.2491 | 0.9864 | 0.2361 |  |  |  |  | False | not read |
| switched mass (primary) | 16 texts | 8 | 1.2976 | 1.2027 | 0.0759 |  |  |  |  | False | not read |
| switched mass (primary) | 64 texts | 8 | 1.2877 | 1.2737 | 0.0110 | 0.0082 | 0.0135 | 0.0000 | 0.0000 | True | above the prediction |
| switched mass (primary) | the whole pool | 1 | 1.2778 | 1.2737 | 0.0032 |  |  |  |  | False | not read |
| count of named pieces (beside) | 1 token | 5 | 0.0213 | 0.0111 | 0.6509 |  |  |  |  | False | not read |
| count of named pieces (beside) | 8 tokens | 8 | 0.1911 | 0.0488 | 1.3639 |  |  |  |  | False | not read |
| count of named pieces (beside) | 16 tokens | 8 | 0.3289 | 0.0908 | 1.2867 |  |  |  |  | False | not read |
| count of named pieces (beside) | 32 tokens | 8 | 0.6219 | 0.2263 | 1.0111 |  |  |  |  | False | not read |
| count of named pieces (beside) | 64 tokens | 8 | 0.9016 | 0.4190 | 0.7664 | 0.5216 | 0.9693 | 0.0000 | 0.0000 | True | above the prediction |
| count of named pieces (beside) | 1 text | 8 | 0.9933 | 0.6733 | 0.3889 |  |  |  |  | False | not read |
| count of named pieces (beside) | 4 texts | 8 | 1.2491 | 0.9875 | 0.2350 |  |  |  |  | False | not read |
| count of named pieces (beside) | 16 texts | 8 | 1.2976 | 1.2030 | 0.0757 |  |  |  |  | False | not read |
| count of named pieces (beside) | 64 texts | 8 | 1.2877 | 1.2737 | 0.0110 | 0.0082 | 0.0135 | 0.0000 | 0.0000 | True | above the prediction |
| count of named pieces (beside) | the whole pool | 1 | 1.2778 | 1.2737 | 0.0032 |  |  |  |  | False | not read |

`end_segment_continued_share`: of the (replicate, draw) predictions behind an interval, the share made on the continued end segment of that replicate's curve (the replicate's end points move a little; the range and the predicted draws are fixed from the full data). A note that changes no reading: the one-text knot of arm U's curve is a mean over draws whose amounts vary about fourfold on a convex curve, so it sits slightly high, which biases the 64-text reading against *above the prediction*; that is conservative.

## 2. Run 6: the self-merge and the ladder

**The rule** (level 1 - 0.05/3; material if the lower end exceeds 0.05):

| set | n_texts | n_documents | rise | interval_lo | interval_hi | material | rise_without_flagged_sources | rise_without_flagged_sources_interval_lo | rise_without_flagged_sources_interval_hi | share_made_worse | share_above_0.05 | share_above_0.1 | share_above_0.2 | percentile_50 | rise_over_rounded_labels | flag |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| E | 1024 |  | 1.0298 | 1.0047 | 1.0557 | True |  |  |  | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 0.9513 | 1.0541 |  |
| E_lab | 512 | 174.0000 | 1.1620 | 1.1088 | 1.2210 | True | 1.2056 | 1.1525 | 1.2706 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.1139 | 1.1859 | pooled; ArXiv contributes 3 documents; the value without it is beside |
| D_unif | 1024 |  | 1.0368 | 1.0121 | 1.0618 | True |  |  |  | 1.0000 | 1.0000 | 1.0000 | 0.9990 | 0.9603 | 1.0620 |  |

The post's summary may carry the self-merge: **True** (it must be material on E).

**Self against stranger on E:** self is worse than a stranger.

| self | stranger | difference | difference_interval_lo | difference_interval_hi | reading | share_of_texts_self_worse | per_unit_self | per_unit_stranger | per_unit_difference | per_unit_difference_interval_lo | per_unit_difference_interval_hi | per_unit_nonfinite_share | consistency_x_hat | consistency_curve_1_one_text_in_these_stores | consistency_committed_value_on_the_papers_run |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1.0298 | 0.5747 | 0.4550 | 0.4356 | 0.4751 | self is worse than a stranger | 1.0000 | 0.0002 | 0.0001 | 0.0001 | 0.0001 | 0.0001 | 0.0000 | 0.5747 | 0.4877 | 0.4900 |

**The ladder on E_lab** (level 1 - 0.05/5 over documents; a text's qualifying shifts are averaged first; each rung prints its own mean count; a rung with any undefined replicate, which is one that drew no qualifying text, prints its value, its counts, and its interval, and has no standing):

| stratum | rung | n_texts | n_text_shift_pairs | n_documents | mean_rise | interval_lo | interval_hi | nonfinite_share | standing | mean_count | mean_rise_without_flagged_sources | flag |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| source:Github | the text itself | 256 | 256 | 69 | 1.3966 | 1.3059 | 1.5119 | 0.0000 | material | 5243.3867 |  |  |
| source:Github | a partner from the same document | 27 | 31 | 69 | 1.3074 | 1.0505 | 1.5693 | 0.0003 |  | 4838.0370 |  |  |
| source:Github | a partner from the same source, another document | 256 | 993 | 69 | 1.0260 | 0.9135 | 1.1527 | 0.0000 | material | 5249.7321 |  |  |
| source:Github | a general partner | 256 | 1024 | 69 | 0.5699 | 0.5164 | 0.6468 | 0.0000 | material | 5600.9502 |  |  |
| source:Pile-CC | the text itself | 64 | 64 | 25 | 0.8452 | 0.7548 | 0.9356 | 0.0000 | material | 5795.9062 |  |  |
| source:Pile-CC | a partner from the same document | 8 | 8 | 25 | 0.9245 | 0.5912 | 1.1133 | 0.0033 |  | 5699.5000 |  |  |
| source:Pile-CC | a partner from the same source, another document | 64 | 248 | 25 | 0.7606 | 0.6942 | 0.8285 | 0.0000 | material | 5797.4714 |  |  |
| source:Pile-CC | a general partner | 64 | 256 | 25 | 0.6212 | 0.5430 | 0.7036 | 0.0000 | material | 5518.9648 |  |  |
| source:Wikipedia (en) | the text itself | 64 | 64 | 33 | 0.9776 | 0.8975 | 1.1016 | 0.0000 | material | 5826.6406 |  |  |
| source:Wikipedia (en) | a partner from the same document | 7 | 7 | 33 | 1.0206 | 0.7977 | 2.1817 | 0.0163 |  | 5632.4286 |  |  |
| source:Wikipedia (en) | a partner from the same source, another document | 64 | 249 | 33 | 0.8911 | 0.8146 | 0.9924 | 0.0000 | material | 5830.6576 |  |  |
| source:Wikipedia (en) | a general partner | 64 | 256 | 33 | 0.7109 | 0.6563 | 0.7856 | 0.0000 | material | 5594.0234 |  |  |
| source:StackExchange | the text itself | 64 | 64 | 44 | 1.0299 | 0.9218 | 1.1456 | 0.0000 | material | 6186.7812 |  |  |
| source:StackExchange | a partner from the same document | 3 | 3 | 44 | 0.9274 | 0.7241 | 1.3341 | 0.1250 |  | 5630.6667 |  |  |
| source:StackExchange | a partner from the same source, another document | 64 | 253 | 44 | 0.8182 | 0.7264 | 0.9064 | 0.0000 | material | 6195.5612 |  |  |
| source:StackExchange | a general partner | 64 | 256 | 44 | 0.5003 | 0.4558 | 0.5464 | 0.0000 | material | 5543.3125 |  |  |
| source:ArXiv | the text itself | 64 | 64 | 3 | 0.8568 |  |  |  |  | 5800.0312 |  |  |
| source:ArXiv | a partner from the same document | 54 | 90 | 3 | 0.7314 |  |  |  |  | 5886.8549 |  |  |
| source:ArXiv | a partner from the same source, another document | 64 | 166 | 3 | 0.7049 |  |  |  |  | 5754.7240 |  |  |
| source:ArXiv | a general partner | 64 | 256 | 3 | 0.4257 |  |  |  |  | 5559.9023 |  |  |
| O | the text itself | 256 | 256 | 105 | 0.9274 | 0.8682 | 0.9912 | 0.0000 | material | 5902.3398 | 0.9509 | pooled; ArXiv contributes 3 documents; the value without it is beside |
| O | a partner from the same document | 72 | 108 | 105 | 0.7891 | 0.6787 | 0.9441 | 0.1422 |  | 5830.6273 | 0.9623 | pooled; ArXiv contributes 3 documents; the value without it is beside |
| O | a partner from the same source, another document | 256 | 916 | 105 | 0.7937 | 0.7448 | 0.8474 | 0.0000 | material | 5894.6035 | 0.8233 | pooled; ArXiv contributes 3 documents; the value without it is beside |
| O | a general partner | 256 | 1024 | 105 | 0.5645 | 0.5347 | 0.5951 | 0.0000 | material | 5554.0508 | 0.6108 | pooled; ArXiv contributes 3 documents; the value without it is beside |

**The scope rule:** the post may say "within one kind of text": **True** (standing: material; by standing: {'material': ['Github', 'Pile-CC', 'Wikipedia (en)', 'StackExchange'], 'interval wholly under 0.05': []}; without standing: ['ArXiv']).

## 3. Runs 3 and 7: plain terms and the outside yardstick

The target's own side, per set: {"E": {"tied_share": 0.025297164916992188, "n_tied_confident_positions": 0, "confident_share": 0.4262657165527344, "p_target_top": 0.4867343300720677, "ce": 2.7212634136812994, "top_is_next": 0.4828614194266265}, "E_lab": {"tied_share": 0.019748687744140625, "n_tied_confident_positions": 0, "confident_share": 0.5108222961425781, "p_target_top": 0.5462636837619357, "ce": 2.424039479417843, "top_is_next": 0.5452008887659758}, "D_unif": {"tied_share": 0.024408340454101562, "n_tied_confident_positions": 0, "confident_share": 0.4290027618408203, "p_target_top": 0.4882006870575424, "ce": 2.7242207570088794, "top_is_next": 0.48469605769059854}}. Every all-position change rate excludes the target's tied positions; a confident-position rate is a ratio of sums over texts; no change rate is printed without its baseline.

| set | in_words | n_draws | change_rate | change_rate_baseline | change_rate_rise | change_rate_confident | change_rate_confident_baseline | p_target_top | p_target_top_baseline | p_target_top_target | ce | ce_baseline | ce_target | top_is_next | top_is_next_baseline |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| E | comparison model pythia-70m | 1 | 0.2640 |  |  | 0.0646 |  | 0.4388 |  | 0.4867 | 2.8898 |  | 2.7213 | 0.4654 |  |
| E | comparison model pythia-160m | 1 | 0.2631 |  |  | 0.0525 |  | 0.4679 |  | 0.4867 | 2.5415 |  | 2.7213 | 0.5081 |  |
| E | merge of general donors, 1 token | 8 | 0.1883 | 0.1851 | 0.0032 | 0.0187 | 0.0185 | 0.4606 | 0.4703 | 0.4867 | 3.0038 | 3.0011 | 2.7213 | 0.4777 | 0.4782 |
| E | merge of general donors, 8 tokens | 8 | 0.2095 | 0.1851 | 0.0244 | 0.0255 | 0.0185 | 0.4309 | 0.4703 | 0.4867 | 3.0360 | 3.0011 | 2.7213 | 0.4719 | 0.4782 |
| E | merge of general donors, 64 tokens | 8 | 0.3759 | 0.1851 | 0.1908 | 0.1689 | 0.0185 | 0.3028 | 0.4703 | 0.4867 | 3.4925 | 3.0011 | 2.7213 | 0.3986 | 0.4782 |
| E | merge of general donors, 1 text | 8 | 0.3758 | 0.1851 | 0.1907 | 0.1778 | 0.0185 | 0.3185 | 0.4703 | 0.4867 | 3.5299 | 3.0011 | 2.7213 | 0.3947 | 0.4782 |
| E | merge of general donors, the whole pool | 1 | 0.5386 | 0.1851 | 0.3535 | 0.3723 | 0.0185 | 0.2219 | 0.4703 | 0.4867 | 4.0142 | 3.0011 | 2.7213 | 0.3059 | 0.4782 |
| E | soft erase of what general donors name, 1 text | 8 | 0.2528 | 0.0498 | 0.2030 | 0.0618 | 0.0038 | 0.4201 | 0.4846 | 0.4867 | 3.1144 | 2.7317 | 2.7213 | 0.4560 | 0.4811 |
| E | same-size random set, beside the merge of general donors, 64 tokens | 8 | 0.2291 | 0.1851 | 0.0440 | 0.0306 | 0.0185 | 0.4095 | 0.4703 | 0.4867 | 3.0307 | 3.0011 | 2.7213 | 0.4675 | 0.4782 |
| E | same-size random set, beside the merge of general donors, 1 text | 8 | 0.2331 | 0.1851 | 0.0480 | 0.0343 | 0.0185 | 0.4080 | 0.4703 | 0.4867 | 3.0570 | 3.0011 | 2.7213 | 0.4658 | 0.4782 |
| E | removal of the never-named pieces (the whole set) | 1 | 0.5380 | 0.0091 | 0.5289 | 0.3713 | 0.0004 | 0.2211 | 0.4869 | 0.4867 | 4.0116 | 2.7214 | 2.7213 | 0.3063 | 0.4830 |
| E | merge of general donors, 16 tokens | 8 | 0.2374 | 0.1851 | 0.0523 | 0.0412 | 0.0185 | 0.3984 | 0.4703 | 0.4867 | 3.1019 | 3.0011 | 2.7213 | 0.4620 | 0.4782 |
| E | merge of general donors, 32 tokens | 8 | 0.2893 | 0.1851 | 0.1043 | 0.0820 | 0.0185 | 0.3533 | 0.4703 | 0.4867 | 3.2428 | 3.0011 | 2.7213 | 0.4402 | 0.4782 |
| E | the full decomposed model (every piece on) | 1 | 0.0498 |  |  | 0.0038 |  | 0.4846 |  | 0.4867 | 2.7317 |  | 2.7213 | 0.4811 |  |
| E | the full decomposed model with the residual | 1 | 0.0091 |  |  | 0.0004 |  | 0.4869 |  | 0.4867 | 2.7214 |  | 2.7213 | 0.4830 |  |
| E | own labels | 1 | 0.1851 |  |  | 0.0185 |  | 0.4703 |  | 0.4867 | 3.0011 |  | 2.7213 | 0.4782 |  |
| E | self-merge (the text's own named pieces) | 1 | 0.5493 | 0.1851 | 0.3642 | 0.3882 | 0.0185 | 0.2040 | 0.4703 | 0.4867 | 4.0863 | 3.0011 | 2.7213 | 0.2997 | 0.4782 |
| E_lab | comparison model pythia-70m | 1 | 0.2512 |  |  | 0.0683 |  | 0.4939 |  | 0.5463 | 2.6018 |  | 2.4240 | 0.5235 |  |
| E_lab | comparison model pythia-160m | 1 | 0.2452 |  |  | 0.0549 |  | 0.5272 |  | 0.5463 | 2.2538 |  | 2.4240 | 0.5709 |  |
| E_lab | code-leaning edit, 64 members | 1 | 0.0692 | 0.0084 | 0.0608 | 0.0298 | 0.0003 | 0.5261 | 0.5465 | 0.5463 | 2.4842 | 2.4241 | 2.4240 | 0.5322 | 0.5453 |
| E_lab | code-leaning edit, 256 members | 1 | 0.2007 | 0.0084 | 0.1922 | 0.1469 | 0.0003 | 0.4423 | 0.5465 | 0.5463 | 2.8229 | 2.4241 | 2.4240 | 0.4752 | 0.5453 |
| E_lab | code-leaning edit, 1007 members | 1 | 0.5032 | 0.0084 | 0.4948 | 0.4781 | 0.0003 | 0.2316 | 0.5465 | 0.5463 | 4.6758 | 2.4241 | 2.4240 | 0.3032 | 0.5453 |
| E_lab | the full decomposed model (every piece on) | 1 | 0.0467 |  |  | 0.0043 |  | 0.5440 |  | 0.5463 | 2.4354 |  | 2.4240 | 0.5431 |  |
| E_lab | the full decomposed model with the residual | 1 | 0.0084 |  |  | 0.0003 |  | 0.5465 |  | 0.5463 | 2.4241 |  | 2.4240 | 0.5453 |  |
| E_lab | own labels | 1 | 0.1654 |  |  | 0.0175 |  | 0.5255 |  | 0.5463 | 2.6862 |  | 2.4240 | 0.5424 |  |
| E_lab | merge of code donors, 64 tokens | 8 | 0.3713 | 0.1654 | 0.2059 | 0.2298 | 0.0175 | 0.3202 | 0.5255 | 0.5463 | 3.3273 | 2.6862 | 2.4240 | 0.4267 | 0.5424 |
| E_lab | merge of code donors, 1 text | 8 | 0.4196 | 0.1654 | 0.2543 | 0.2736 | 0.0175 | 0.3002 | 0.5255 | 0.5463 | 3.4854 | 2.6862 | 2.4240 | 0.4008 | 0.5424 |
| E_lab | merge of general donors, 64 tokens | 8 | 0.3612 | 0.1654 | 0.1958 | 0.1779 | 0.0175 | 0.3360 | 0.5255 | 0.5463 | 3.2483 | 2.6862 | 2.4240 | 0.4464 | 0.5424 |
| E_lab | merge of general donors, 1 text | 8 | 0.3641 | 0.1654 | 0.1987 | 0.1918 | 0.0175 | 0.3498 | 0.5255 | 0.5463 | 3.2935 | 2.6862 | 2.4240 | 0.4400 | 0.5424 |

The cells that keep no per-position arrays (the confident-position rate only): s9_plain_terms_other_cells.csv, 52 masks.

**By bin of per-position divergence**, pooled over the 78 listed mask cells on E (the target's tied positions excluded):

| bin | from | to | n_positions | change_rate | mean_p_target_top |
|---|---|---|---|---|---|
| 0 | -inf | 0.0500 | 4693498 | 0.0123 | 0.8491 |
| 1 | 0.0500 | 0.2000 | 7039191 | 0.0673 | 0.6706 |
| 2 | 0.2000 | 0.5000 | 13146580 | 0.1934 | 0.3541 |
| 3 | 0.5000 | 1.0000 | 10106905 | 0.4152 | 0.1834 |
| 4 | 1.0000 | 2.0000 | 3732562 | 0.6498 | 0.1053 |
| 5 | 2.0000 | inf | 1141214 | 0.9075 | 0.0330 |

**Examples, by rule** (tokenizer EleutherAI/gpt-neox-20b; 2045 of 2048 stored positions decode without a replacement character; the five nearest per percentile are in s9_examples.csv):

- *merge, percentile 10* (value 0.1387; text 313, position 181, divergence there 0.1392). Context: ' * right.M23 + left.M33 * right.M33 + left.M34 * right.M43,\n                left.M31 * right.M14 + left.M32 * right.M24 +'. Real next token: ' left'.
    - the original model: ' left' 0.957; ' right' 0.035; ' Left' 0.001; ' top' 0.001; ' bottom' 0.000
    - own labels: ' left' 0.903; ' right' 0.035; 'left' 0.008; ' Left' 0.002; ' bottom' 0.001
    - the merge of general donors, 8 tokens: ' left' 0.776; ' right' 0.050; ' Left' 0.009; 'left' 0.005; ' top' 0.004
    - the merge of general donors, 64 tokens: ' left' 0.896; ' right' 0.089; ' Left' 0.003; ' Right' 0.001; ' top' 0.001
    - the merge of general donors, 1 text: ' left' 0.775; ' right' 0.196; ' Left' 0.007; ' middle' 0.004; ' top' 0.003
- *merge, percentile 50* (value 0.7871; text 215, position 320, divergence there 0.7871). Context: '.\n\nThe role of CD4^+^ T cells during *Salmonella* infection is likely two-fold: 1) direct effector cell activity and 2) providing help for B cells and CD8^+^ T cells. Since IFN-γ is'. Real next token: ' a'.
    - the original model: ' a' 0.205; ' produced' 0.117; ' an' 0.052; ' the' 0.052; ' not' 0.043
    - own labels: ' a' 0.261; ' the' 0.085; ' an' 0.080; ' produced' 0.038; ' known' 0.019
    - the merge of general donors, 8 tokens: ' a' 0.187; ' the' 0.073; ' an' 0.057; ' produced' 0.031; ' involved' 0.027
    - the merge of general donors, 64 tokens: ' a' 0.178; ' the' 0.048; ' an' 0.040; ' required' 0.037; ' also' 0.031
    - the merge of general donors, 1 text: ' a' 0.135; ' the' 0.064; ' an' 0.047; ' not' 0.036; ' able' 0.028
- *merge, percentile 90* (value 2.3516; text 410, position 84, divergence there 2.3535). Context: '[@Adam:2015lda] (up to 14) and ATLAS\xa0[@Aad:2015lcb] (up to 280) also agreed well with the respective NLO pQCD calculations, properly scaled, at least at'. Real next token: ' central'.
    - the original model: ' the' 0.346; ' 2' 0.041; ' energies' 0.039; ' $\\' 0.027; ' $' 0.025
    - own labels: ' the' 0.242; ' $' 0.069; ' a' 0.035; ' high' 0.030; ' low' 0.029
    - the merge of general donors, 8 tokens: ' the' 0.443; ' $' 0.053; ' $\\' 0.017; ' low' 0.016; ' high' 0.013
    - the merge of general donors, 64 tokens: ' the' 0.334; ' 3' 0.040; ' a' 0.035; ' 2' 0.029; ' $' 0.022
    - the merge of general donors, 1 text: ' least' 0.689; ' most' 0.047; ' the' 0.027; ' rest' 0.013; ' a' 0.009
- *merge, percentile 99* (value 5.5195; text 598, position 496, divergence there 5.5234). Context: 'PHA_BLEND_RGBA(sR, sG, sB, A, dR, dG, dB, dA);\n\t\t\t  \tASSEMBLE_RGBA(dst, dstbpp, dst'. Real next token: 'fmt'.
    - the original model: 'fmt' 0.992; 'dst' 0.001; 'buf' 0.001; 'rgb' 0.000; 'src' 0.000
    - own labels: 'fmt' 0.997; ' fmt' 0.002; 'format' 0.000; 'derr' 0.000; 'intf' 0.000
    - the merge of general donors, 8 tokens: 'fmt' 0.908; 'format' 0.011; ' fmt' 0.005; 'label' 0.004; 'util' 0.003
    - the merge of general donors, 64 tokens: 'buf' 0.170; 'fmt' 0.133; '_' 0.103; 'b' 0.052; ')' 0.049
    - the merge of general donors, 1 text: ',' 0.461; ');' 0.132; 'b' 0.055; ')' 0.052; '_' 0.029
- *never_named, percentile 50* (value 0.9307; text 459, position 436, divergence there 0.9297). Context: ' \\Gamma_0[\\alpha_s\\ln(q^2/q_0^2)]^n,$$ where $q^2$ is the momentum scale of these processes. At zero temperature, $q_0$ is'. Real next token: ' some'.
    - the original model: ' the' 0.213; ' proportional' 0.078; ' a' 0.048; ' not' 0.033; ' small' 0.029
    - the full decomposed model with the residual: ' the' 0.213; ' proportional' 0.083; ' a' 0.048; ' not' 0.035; ' small' 0.029
    - the removal of the never-named pieces: ' the' 0.546; ' $' 0.027; ' given' 0.023; ' a' 0.023; ' $\\' 0.015

**The outside yardstick:**

| model | set | kl_target_to_model | kl_target_to_model_interval_lo | kl_target_to_model_interval_hi | kl_model_to_target | kl_this_model_from_the_other | ce_model | ce_target | top_token_agreement | top_token_agreement_own_labels | p_target_top | p_target_top_own_labels | flag |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| pythia-70m | E | 0.3939 | 0.3862 | 0.4020 | 0.4106 | 0.5199 | 2.8898 | 2.7213 | 0.7360 | 0.8149 | 0.4388 | 0.4703 |  |
| pythia-160m | E | 0.4631 | 0.4506 | 0.4767 | 0.3899 | 0.4431 | 2.5415 | 2.7213 | 0.7369 | 0.8149 | 0.4679 | 0.4703 |  |
| pythia-70m | E_lab | 0.4459 | 0.4150 | 0.4806 | 0.4476 | 0.5786 | 2.6018 | 2.4240 | 0.7488 | 0.8346 | 0.4939 | 0.5255 | pooled; ArXiv contributes 3 documents; the value without it is beside |
| pythia-160m | E_lab | 0.5217 | 0.4844 | 0.5653 | 0.4105 | 0.4751 | 2.2538 | 2.4240 | 0.7548 | 0.8346 | 0.5272 | 0.5255 | pooled; ArXiv contributes 3 documents; the value without it is beside |

**The ratios the post will quote:**

| quantity | divergence_on_E | divergence_to_the_primary_comparison_model | comparison_model | ratio | ratio_interval_lo | ratio_interval_hi | nonfinite_share |
|---|---|---|---|---|---|---|---|
| own labels | 0.3417 | 0.3939 | pythia-70m | 0.8676 | 0.8529 | 0.8819 | 0.0000 |
| the 64-token merge | 0.7993 | 0.3939 | pythia-70m | 2.0293 | 2.0013 | 2.0556 | 0.0000 |
| the one-text merge | 0.8294 | 0.3939 | pythia-70m | 2.1059 | 2.0751 | 2.1349 | 0.0000 |
| the self-merge | 1.3715 | 0.3939 | pythia-70m | 3.4822 | 3.4170 | 3.5472 | 0.0000 |
| the never-named removal | 1.2847 | 0.3939 | pythia-70m | 3.2619 | 3.2017 | 3.3224 | 0.0000 |

