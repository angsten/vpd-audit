# The code-leaning edit on the panels, and the merges of 2 and 4 donor tokens (main)

**ArXiv reads keep**: ArXiv is damaged, more than by deleting as many equally used random components.

Every interval is a 95 percent percentile bootstrap (10000 replicates) unless it says otherwise. On a panel the bootstrap resamples its documents, every row of a drawn document entering together, means in ratio form, one document draw per replicate shared by H, T, and rho at both sizes, the twins' draws held fixed. H is the edit's damage (the mean over rows of a row's divergence from the original model, minus the rung-0 reference's); T the usage-matched twins' (the mean over the draws per row first); rho = H / T. X = 0.05 nats.

Keep requires every one of its three intervals to clear its bar (H at the smaller size at or above X, rho above 1 at both sizes): an intersection-union test, whose error rate is at most the per-interval 5 percent, so no correction across the three is applied.

## 0. What was asserted before anything was read

- The guard: commit c57fc2b543b4, dirty flag 0, freeze c57fc2b (HEAD or its ancestor: True), enforced: True. The nine frozen modules against main (c57fc2b543b4): all equal; this analysis's modules at the freeze: vpd_audit/analysis_s12.py equal, vpd_audit/stats_s12.py equal (s12_frozen_modules.csv).
- The stores: 11 under results/grid/main_s12/tier7, each complete and exactly the launch's cells (s12_stores.csv); the launch summaries: {'merge_sizes': {'cells_run': 106, 'gpu': 'NVIDIA A100-SXM4-40GB', 'P3': True, 'sets_asserted_at_launch': True, 'two_paths': True}, 'panel_edit': {'cells_run': 155, 'gpu': 'NVIDIA A100-SXM4-40GB', 'P3': True, 'sets_asserted_at_launch': True, 'two_paths': True}}.
- The canaries: 13 cells bitwise equal to their committed per-text divergences (s12_canary.csv).
- Every set held again to the label-only table and its committed twin: {'merge_sets': 96, 'merge_matched_sets': 32, 'panel_edit_sets': 144, 'canaries': 8}.
- The importances of every committed store the 1- and 8-token points are read from equal the tier-7 store's bitwise: ['results/grid/main/tier1/E', 'results/grid/main/tier2/E', 'results/grid/main/tier4/E__marginal', 'results/grid/main_s9/tier5/E_lab__same_domain'].

## 1. ArXiv (decisive), at 256 and 1007 members

| size | n_documents | H | H_interval_lo | H_interval_hi | T | T_interval_lo | T_interval_hi | rho | rho_interval_lo | rho_interval_hi | rho_nonfinite_share |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 256 | 162 | 0.2618 | 0.2327 | 0.2918 | 0.1217 | 0.1180 | 0.1257 | 2.1507 | 1.8833 | 2.4286 | 0.0000 |
| 1007 | 162 | 2.6750 | 2.4177 | 2.9224 | 1.0776 | 1.0512 | 1.1059 | 2.4823 | 2.2037 | 2.7603 | 0.0000 |

Reading: **keep** (the interval of H at the smaller size starts at or above 0.05 and rho lies above 1 at both sizes); rho above 1 at 256, above 1 at 1007. The post may then say: ArXiv is damaged, more than by deleting as many equally used random components.

## 2. The candidates to stand in for ArXiv (this applies only if ArXiv reads drop)

Each of DM Mathematics, PubMed Central, and FreeLaw may serve as the caveat's example only if it meets the keep condition with every interval at 1 - 0.05/3 (about 98.3 percent), correcting for the three candidates.

| source | size | n_documents | H | H_interval_lo | H_interval_hi | rho | rho_interval_lo | rho_interval_hi | rho_nonfinite_share | reading |
|---|---|---|---|---|---|---|---|---|---|---|
| DM Mathematics | 256 | 174 | 0.0894 | 0.0776 | 0.1019 | 0.7807 | 0.6855 | 0.8836 | 0.0000 | soften |
| DM Mathematics | 1007 | 174 | 1.1263 | 1.0413 | 1.2068 | 0.9412 | 0.8547 | 1.0235 | 0.0000 | soften |
| PubMed Central | 256 | 186 | 0.0782 | 0.0568 | 0.1030 | 0.6314 | 0.4496 | 0.8486 | 0.0000 | soften |
| PubMed Central | 1007 | 186 | 0.8891 | 0.7553 | 1.0483 | 0.6668 | 0.5602 | 0.7983 | 0.0000 | soften |
| FreeLaw | 256 | 174 | 0.0436 | 0.0362 | 0.0529 | 0.1903 | 0.1571 | 0.2345 | 0.0000 | soften |
| FreeLaw | 1007 | 174 | 0.3300 | 0.2870 | 0.3793 | 0.1831 | 0.1601 | 0.2108 | 0.0000 | soften |

Candidates meeting keep at that level: none.

## 3. Every panel (descriptive: the same numbers and the same rule, read by nothing)

| source | size | n_documents | H | H_interval_lo | H_interval_hi | T | rho | rho_interval_lo | rho_interval_hi | rho_nonfinite_share | reading | rho_side |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| GitHub | 256 | 193 | 0.6661 | 0.6110 | 0.7227 | 0.0764 | 8.7137 | 7.7410 | 9.7495 | 0.0000 | keep | above 1 |
| GitHub | 1007 | 193 | 3.3424 | 3.1699 | 3.5144 | 0.9774 | 3.4198 | 3.1544 | 3.6950 | 0.0000 | keep | above 1 |
| StackExchange | 256 | 197 | 0.3416 | 0.3078 | 0.3772 | 0.1016 | 3.3612 | 2.9446 | 3.8189 | 0.0000 | keep | above 1 |
| StackExchange | 1007 | 197 | 2.2618 | 2.1016 | 2.4283 | 1.0676 | 2.1187 | 1.9422 | 2.3057 | 0.0000 | keep | above 1 |
| ArXiv | 256 | 162 | 0.2618 | 0.2327 | 0.2918 | 0.1217 | 2.1507 | 1.8833 | 2.4286 | 0.0000 | keep | above 1 |
| ArXiv | 1007 | 162 | 2.6750 | 2.4177 | 2.9224 | 1.0776 | 2.4823 | 2.2037 | 2.7603 | 0.0000 | keep | above 1 |
| Pile-CC | 256 | 192 | 0.0256 | 0.0222 | 0.0301 | 0.1709 | 0.1500 | 0.1284 | 0.1784 | 0.0000 | drop | below 1 |
| Pile-CC | 1007 | 192 | 0.2129 | 0.1749 | 0.2599 | 1.3714 | 0.1553 | 0.1271 | 0.1905 | 0.0000 | drop | below 1 |
| Wikipedia | 256 | 184 | 0.0251 | 0.0242 | 0.0260 | 0.1752 | 0.1431 | 0.1373 | 0.1496 | 0.0000 | drop | below 1 |
| Wikipedia | 1007 | 184 | 0.2077 | 0.1836 | 0.2412 | 1.5931 | 0.1304 | 0.1154 | 0.1523 | 0.0000 | drop | below 1 |
| DM Mathematics | 256 | 174 | 0.0894 | 0.0798 | 0.0996 | 0.1145 | 0.7807 | 0.7008 | 0.8657 | 0.0000 | soften | below 1 |
| DM Mathematics | 1007 | 174 | 1.1263 | 1.0575 | 1.1928 | 1.1967 | 0.9412 | 0.8709 | 1.0111 | 0.0000 | soften | neither |
| PubMed Central | 256 | 186 | 0.0782 | 0.0605 | 0.0979 | 0.1239 | 0.6314 | 0.4805 | 0.8033 | 0.0000 | soften | below 1 |
| PubMed Central | 1007 | 186 | 0.8891 | 0.7764 | 1.0193 | 1.3335 | 0.6668 | 0.5753 | 0.7724 | 0.0000 | soften | below 1 |
| FreeLaw | 256 | 174 | 0.0436 | 0.0372 | 0.0513 | 0.2292 | 0.1903 | 0.1620 | 0.2256 | 0.0000 | soften | below 1 |
| FreeLaw | 1007 | 174 | 0.3300 | 0.2943 | 0.3704 | 1.8020 | 0.1831 | 0.1636 | 0.2057 | 0.0000 | soften | below 1 |

## 4. A replication: each panel's H beside the committed E_lab value on the same source

The E_lab intervals resample E_lab's documents of that source (seed (master, "boot_docs", "E_lab", source)); the E_lab values equal the committed by-source damages exactly.

| source | size | panel_H | panel_H_interval_lo | panel_H_interval_hi | panel_documents | E_lab_H | E_lab_H_interval_lo | E_lab_H_interval_hi | E_lab_documents |
|---|---|---|---|---|---|---|---|---|---|
| Github | 256 | 0.6661 | 0.6110 | 0.7227 | 193 | 0.6390 | 0.4920 | 0.7697 | 69 |
| StackExchange | 256 | 0.3416 | 0.3078 | 0.3772 | 197 | 0.3251 | 0.2558 | 0.3970 | 44 |
| Pile-CC | 256 | 0.0256 | 0.0222 | 0.0301 | 192 | 0.0206 | 0.0196 | 0.0222 | 25 |
| Wikipedia (en) | 256 | 0.0251 | 0.0242 | 0.0260 | 184 | 0.0263 | 0.0229 | 0.0316 | 33 |
| Github | 1007 | 3.3424 | 3.1699 | 3.5144 | 193 | 3.2391 | 2.6598 | 3.6843 | 69 |
| StackExchange | 1007 | 2.2618 | 2.1016 | 2.4283 | 197 | 2.1746 | 1.8316 | 2.5326 | 44 |
| Pile-CC | 1007 | 0.2129 | 0.1749 | 0.2599 | 192 | 0.1616 | 0.1448 | 0.1771 | 25 |
| Wikipedia (en) | 1007 | 0.2077 | 0.1836 | 0.2412 | 184 | 0.1978 | 0.1615 | 0.2526 | 33 |

## 5. The damage per unit of removed label, beside rho (descriptive)

| panel | size | omega_group | omega_twins | H_per_omega_group | T_per_omega_twins | rho | rho_interval_lo | rho_interval_hi |
|---|---|---|---|---|---|---|---|---|
| panel_Github | 256 | 9.7921 | 0.7908 | 0.0680 | 0.0967 | 8.7137 | 7.7410 | 9.7495 |
| panel_StackExchange | 256 | 5.7138 | 1.1033 | 0.0598 | 0.0921 | 3.3612 | 2.9446 | 3.8189 |
| panel_ArXiv | 256 | 1.3863 | 1.6896 | 0.1889 | 0.0720 | 2.1507 | 1.8833 | 2.4286 |
| panel_Pile_CC | 256 | 0.1603 | 2.0540 | 0.1599 | 0.0832 | 0.1500 | 0.1284 | 0.1784 |
| panel_Wikipedia__en_ | 256 | 0.0575 | 2.3324 | 0.4361 | 0.0751 | 0.1431 | 0.1373 | 0.1496 |
| panel_Github | 1007 | 43.0250 | 6.4308 | 0.0777 | 0.1520 | 3.4198 | 3.1544 | 3.6950 |
| panel_StackExchange | 1007 | 31.0223 | 7.8589 | 0.0729 | 0.1358 | 2.1187 | 1.9422 | 2.3057 |
| panel_ArXiv | 1007 | 15.4455 | 10.0171 | 0.1732 | 0.1076 | 2.4823 | 2.2037 | 2.7603 |
| panel_Pile_CC | 1007 | 2.1108 | 12.4501 | 0.1009 | 0.1101 | 0.1553 | 0.1271 | 0.1905 |
| panel_Wikipedia__en_ | 1007 | 1.2403 | 13.9799 | 0.1675 | 0.1140 | 0.1304 | 0.1154 | 0.1523 |

- 256 members: by the group's omega GitHub > StackExchange > ArXiv > Pile-CC > Wikipedia; by H GitHub > StackExchange > ArXiv > Pile-CC > Wikipedia; the same order: yes.
- 1007 members: by the group's omega GitHub > StackExchange > ArXiv > Pile-CC > Wikipedia; by H GitHub > ArXiv > StackExchange > Pile-CC > Wikipedia; the same order: no.

| size | pair | omega_first | omega_second | H_first | H_second | higher_by_omega | higher_by_H | same_order |
|---|---|---|---|---|---|---|---|---|
| 256 | StackExchange / ArXiv | 5.7138 | 1.3863 | 0.3416 | 0.2618 | StackExchange | StackExchange | yes |
| 256 | Pile-CC / Wikipedia | 0.1603 | 0.0575 | 0.0256 | 0.0251 | Pile-CC | Pile-CC | yes |
| 1007 | StackExchange / ArXiv | 31.0223 | 15.4455 | 2.2618 | 2.6750 | StackExchange | ArXiv | no |
| 1007 | Pile-CC / Wikipedia | 2.1108 | 1.2403 | 0.2129 | 0.2077 | Pile-CC | Pile-CC | yes |

## 6. The merge points at 1, 2, 4, and 8 donor tokens (descriptive)

On E, the rise over the text's own explanation per line; 1 and 8 tokens from the committed stores, 2 and 4 from tier 7:

| line | tokens | rise | interval_lo | interval_hi | divergence | n_draws_positive | n_draws |
|---|---|---|---|---|---|---|---|
| real merge | 1 | 0.0038 | 0.0034 | 0.0041 | 0.3455 | 8 | 8 |
| real merge | 2 | 0.0101 | 0.0094 | 0.0107 | 0.3518 | 8 | 8 |
| real merge | 4 | 0.0190 | 0.0181 | 0.0200 | 0.3608 | 8 | 8 |
| real merge | 8 | 0.0402 | 0.0389 | 0.0415 | 0.3819 | 8 | 8 |
| frequency-matched | 1 | -0.0033 | -0.0036 | -0.0031 | 0.3384 | 0 | 8 |
| frequency-matched | 2 | -0.0044 | -0.0048 | -0.0040 | 0.3373 | 0 | 8 |
| frequency-matched | 4 | -0.0063 | -0.0068 | -0.0058 | 0.3355 | 1 | 8 |
| frequency-matched | 8 | -0.0038 | -0.0046 | -0.0030 | 0.3379 | 2 | 8 |
| uniform random | 1 | -0.0021 | -0.0022 | -0.0020 | 0.3397 | 0 | 8 |
| uniform random | 2 | -0.0043 | -0.0045 | -0.0041 | 0.3374 | 0 | 8 |
| uniform random | 4 | -0.0074 | -0.0078 | -0.0071 | 0.3343 | 0 | 8 |
| uniform random | 8 | -0.0110 | -0.0116 | -0.0104 | 0.3307 | 0 | 8 |

The real merge minus the frequency-matched control, paired per text and draw:

| tokens | real_minus_matched | interval_lo | interval_hi | n_draws_positive | n_draws |
|---|---|---|---|---|---|
| 1 | 0.0071 | 0.0068 | 0.0074 | 8 | 8 |
| 2 | 0.0145 | 0.0140 | 0.0150 | 8 | 8 |
| 4 | 0.0253 | 0.0247 | 0.0260 | 8 | 8 |
| 8 | 0.0440 | 0.0431 | 0.0449 | 8 | 8 |

Per draw (the mean over the texts of E):

| tokens | rung | draw | real_merge | frequency_matched | real_minus_matched | uniform_random |
|---|---|---|---|---|---|---|
| 1 | 1 | 0 | 0.0066 | -0.0053 | 0.0119 | -0.0016 |
| 1 | 1 | 1 | 0.0017 | -0.0044 | 0.0061 | -0.0038 |
| 1 | 1 | 2 | 0.0047 | -0.0033 | 0.0081 | -0.0017 |
| 1 | 1 | 3 | 0.0044 | -0.0043 | 0.0087 | -0.0025 |
| 1 | 1 | 4 | 0.0055 | -0.0045 | 0.0101 | -0.0026 |
| 1 | 1 | 5 | 0.0028 | -0.0026 | 0.0054 | -0.0015 |
| 1 | 1 | 6 | 0.0016 | -0.0009 | 0.0025 | -0.0008 |
| 1 | 1 | 7 | 0.0028 | -0.0014 | 0.0041 | -0.0021 |
| 2 | T2 | 0 | 0.0150 | -0.0075 | 0.0225 | -0.0034 |
| 2 | T2 | 1 | 0.0084 | -0.0062 | 0.0146 | -0.0055 |
| 2 | T2 | 2 | 0.0104 | -0.0057 | 0.0161 | -0.0030 |
| 2 | T2 | 3 | 0.0248 | -0.0001 | 0.0249 | -0.0062 |
| 2 | T2 | 4 | 0.0105 | -0.0056 | 0.0160 | -0.0075 |
| 2 | T2 | 5 | 0.0048 | -0.0045 | 0.0093 | -0.0032 |
| 2 | T2 | 6 | 0.0015 | -0.0025 | 0.0041 | -0.0016 |
| 2 | T2 | 7 | 0.0053 | -0.0032 | 0.0085 | -0.0040 |
| 4 | T4 | 0 | 0.0193 | -0.0093 | 0.0286 | -0.0074 |
| 4 | T4 | 1 | 0.0128 | -0.0081 | 0.0209 | -0.0077 |
| 4 | T4 | 2 | 0.0158 | -0.0076 | 0.0234 | -0.0055 |
| 4 | T4 | 3 | 0.0334 | 0.0002 | 0.0332 | -0.0085 |
| 4 | T4 | 4 | 0.0254 | -0.0055 | 0.0310 | -0.0098 |
| 4 | T4 | 5 | 0.0162 | -0.0054 | 0.0216 | -0.0056 |
| 4 | T4 | 6 | 0.0184 | -0.0075 | 0.0259 | -0.0072 |
| 4 | T4 | 7 | 0.0110 | -0.0069 | 0.0178 | -0.0077 |
| 8 | 2 | 0 | 0.0385 | -0.0056 | 0.0441 | -0.0115 |
| 8 | 2 | 1 | 0.0414 | 0.0023 | 0.0391 | -0.0102 |
| 8 | 2 | 2 | 0.0308 | -0.0088 | 0.0396 | -0.0099 |
| 8 | 2 | 3 | 0.0677 | 0.0070 | 0.0607 | -0.0122 |
| 8 | 2 | 4 | 0.0446 | -0.0026 | 0.0473 | -0.0125 |
| 8 | 2 | 5 | 0.0348 | -0.0076 | 0.0424 | -0.0090 |
| 8 | 2 | 6 | 0.0328 | -0.0078 | 0.0406 | -0.0116 |
| 8 | 2 | 7 | 0.0308 | -0.0074 | 0.0381 | -0.0114 |

On E_lab, each pool on the code texts and on the prose texts (the stratified document bootstrap):

| stratum | donors | tokens | rise | interval_lo | interval_hi | divergence | n_documents | n_draws_positive |
|---|---|---|---|---|---|---|---|---|
| code texts | code donors | 1 | 0.0185 | 0.0165 | 0.0206 | 0.3111 | 69 | 8 |
| code texts | code donors | 2 | 0.0427 | 0.0388 | 0.0468 | 0.3354 | 69 | 8 |
| code texts | code donors | 4 | 0.1011 | 0.0879 | 0.1131 | 0.3937 | 69 | 8 |
| code texts | code donors | 8 | 0.1911 | 0.1640 | 0.2153 | 0.4837 | 69 | 8 |
| code texts | general donors | 1 | 0.0071 | 0.0063 | 0.0080 | 0.2998 | 69 | 5 |
| code texts | general donors | 2 | 0.0198 | 0.0128 | 0.0308 | 0.3124 | 69 | 7 |
| code texts | general donors | 4 | 0.0319 | 0.0246 | 0.0433 | 0.3245 | 69 | 8 |
| code texts | general donors | 8 | 0.0568 | 0.0494 | 0.0668 | 0.3494 | 69 | 8 |
| code texts | prose donors | 1 | 0.0032 | 0.0018 | 0.0050 | 0.2959 | 69 | 4 |
| code texts | prose donors | 2 | 0.0078 | 0.0060 | 0.0101 | 0.3005 | 69 | 6 |
| code texts | prose donors | 4 | 0.0112 | 0.0079 | 0.0156 | 0.3039 | 69 | 8 |
| code texts | prose donors | 8 | 0.0280 | 0.0196 | 0.0401 | 0.3207 | 69 | 8 |
| prose texts | code donors | 1 | -0.0018 | -0.0033 | -0.0002 | 0.4268 | 58 | 3 |
| prose texts | code donors | 2 | -0.0023 | -0.0047 | 0.0003 | 0.4263 | 58 | 3 |
| prose texts | code donors | 4 | -0.0046 | -0.0079 | -0.0012 | 0.4241 | 58 | 2 |
| prose texts | code donors | 8 | 0.0013 | -0.0040 | 0.0067 | 0.4299 | 58 | 5 |
| prose texts | general donors | 1 | 0.0034 | 0.0019 | 0.0047 | 0.4320 | 58 | 7 |
| prose texts | general donors | 2 | 0.0089 | 0.0068 | 0.0111 | 0.4376 | 58 | 5 |
| prose texts | general donors | 4 | 0.0127 | 0.0101 | 0.0153 | 0.4413 | 58 | 6 |
| prose texts | general donors | 8 | 0.0324 | 0.0289 | 0.0360 | 0.4611 | 58 | 8 |
| prose texts | prose donors | 1 | 0.0087 | 0.0074 | 0.0099 | 0.4374 | 58 | 7 |
| prose texts | prose donors | 2 | 0.0156 | 0.0141 | 0.0172 | 0.4443 | 58 | 7 |
| prose texts | prose donors | 4 | 0.0366 | 0.0342 | 0.0391 | 0.4653 | 58 | 8 |
| prose texts | prose donors | 8 | 0.0901 | 0.0855 | 0.0950 | 0.5188 | 58 | 8 |

