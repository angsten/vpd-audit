# The checks that need no GPU (main run)

Every reading rule below was fixed before any of these numbers existed.

## The freeze guard and the regression checks

`--frozen c57fc2b543b4a3a0b8587e403a66be249a85670f` is HEAD, which by itself cannot fail; its content is the table below: each of the six frozen statistics and analysis modules is, on disk and at HEAD, the blob it is on `main` (c57fc2b543b4).

| module | blob_on_disk | blob_at_head | blob_on_main | equal |
|---|---|---|---|---|
| vpd_audit/stats.py | 5c6e1afc019aba09688e5954e282298e9d2eaaf7 | 5c6e1afc019aba09688e5954e282298e9d2eaaf7 | 5c6e1afc019aba09688e5954e282298e9d2eaaf7 | True |
| vpd_audit/stats_s7.py | 849ae0a462f63e732e3aa2e5bf5a0197e8fdecb7 | 849ae0a462f63e732e3aa2e5bf5a0197e8fdecb7 | 849ae0a462f63e732e3aa2e5bf5a0197e8fdecb7 | True |
| vpd_audit/analysis.py | 3a1d9a38168ef664c11cc35adba04cb208874d67 | 3a1d9a38168ef664c11cc35adba04cb208874d67 | 3a1d9a38168ef664c11cc35adba04cb208874d67 | True |
| vpd_audit/analysis_s7.py | e64f29c7a9f07ec7350fc92f8e6cce73aee19ac3 | e64f29c7a9f07ec7350fc92f8e6cce73aee19ac3 | e64f29c7a9f07ec7350fc92f8e6cce73aee19ac3 | True |
| vpd_audit/figures.py | 217421d7665134449952fb1c35368480deb826ed | 217421d7665134449952fb1c35368480deb826ed | 217421d7665134449952fb1c35368480deb826ed | True |
| vpd_audit/figures_s7.py | b1d5eab36864392080c9380b64c60c2554148fed | b1d5eab36864392080c9380b64c60c2554148fed | b1d5eab36864392080c9380b64c60c2554148fed | True |

Recorded, not asserted: the five harness modules that later stages extended additively, against their blobs at `HEAD`, the commit that produced the committed outputs. A rerun must reproduce every committed CSV byte for byte whether or not they have changed.

| module | blob_on_disk | blob_at_head | blob_at_HEAD | unchanged_since |
|---|---|---|---|---|
| vpd_audit/cells.py | 3adca95be8842d5455340395d50e3163a8b75870 | 3adca95be8842d5455340395d50e3163a8b75870 | 3adca95be8842d5455340395d50e3163a8b75870 | True |
| vpd_audit/sources.py | bd7256908f365ca070c4551f6ed5755d7bbfcc37 | bd7256908f365ca070c4551f6ed5755d7bbfcc37 | bd7256908f365ca070c4551f6ed5755d7bbfcc37 | True |
| vpd_audit/code_leaning.py | 1e6c637a871f2518d9cb40c69d462e6a2fd9b24f | 1e6c637a871f2518d9cb40c69d462e6a2fd9b24f | 1e6c637a871f2518d9cb40c69d462e6a2fd9b24f | True |
| vpd_audit/grid.py | 3186e4405db18490b1f0755dc4653ca888074efc | 3186e4405db18490b1f0755dc4653ca888074efc | 3186e4405db18490b1f0755dc4653ca888074efc | True |
| vpd_audit/pre_reads.py | 879ad795fc63174b7c6b6e847754c0a5ca1f9094 | 879ad795fc63174b7c6b6e847754c0a5ca1f9094 | 879ad795fc63174b7c6b6e847754c0a5ca1f9094 | True |

| regression check | result | detail |
|---|---|---|
| the frozen modules are main's blobs, on disk and at HEAD | pass | 6 of 6 equal; main at c57fc2b543b4, HEAD c57fc2b543b4; recorded, not asserted: 5 of 5 harness modules unchanged since HEAD |
| check (a): the by-source damages reproduce s7_code_leaning_damage_by_source.csv exactly | pass | 40 by-source values and 10 GitHub values, 0 unequal, 0 printed intervals unequal |
| check (b): 512 against 512 with the row floor reproduces the committed code-leaning group | pass | 1007 members, mass 49.47, share 0.248, null p95 and word equal to the committed summary |
| check (b): the cache half's document index is the local one | pass | SHA-256 of the index table |
| check (d): the draw-averaged shares at 0.05 reproduce fraction_seq_above_X | pass | 24 rungs compared, 0 unequal; the five values fixed in advance, at three decimals: True |
| check (d): the gate, per-position arrays against the committed kl_mean | pass | 69 cells, max difference 8.53e-05 against 0.0005 |
| check (c): the rebuilt named and matched sets are the committed stores' | pass | 32 sets equal by source hash and n_on |

## The document index

Documents are numbered per source block by the running count of end-of-text ids; a row's document is its majority document. `distinct_documents` counts majority documents, the unit of every document bootstrap and floor here; `documents_by_end_of_text_count` is the end-of-text count plus one (short documents never hold a row's majority). The saved rows are the first 512 of 513 tokens, so an end-of-text id at a row's unsaved 513th token is invisible; `expected_hidden_boundaries` is how many that is expected to be in each block.

| set | source | rows | distinct_documents | documents_by_end_of_text_count | rows_per_document_mean | rows_per_document_max | expected_hidden_boundaries |
|---|---|---|---|---|---|---|---|
| E_lab | Github | 256 | 69 | 99 | 3.71 | 25 | 0.19 |
| E_lab | Pile-CC | 64 | 25 | 38 | 2.56 | 11 | 0.07 |
| E_lab | Wikipedia (en) | 64 | 33 | 55 | 1.94 | 6 | 0.10 |
| E_lab | StackExchange | 64 | 44 | 61 | 1.45 | 6 | 0.12 |
| E_lab | ArXiv | 64 | 3 | 3 | 21.33 | 29 | 0.00 |
| D_code | Github | 512 | 96 | 130 | 5.33 | 56 | 0.25 |
| D_prose | Pile-CC | 256 | 98 | 141 | 2.61 | 36 | 0.27 |
| D_prose | Wikipedia (en) | 256 | 105 | 172 | 2.44 | 14 | 0.33 |

**Near-duplicate screen (a description; no rule reads it).** 0.0391 of the 256 GitHub rows of E_lab share at least one exact 50-token window with a row of D_code (42 row pairs, listed in `near_duplicate_pairs.csv`).

| e_lab_row | d_code_row | n_shared_windows | first_offset_e_lab | first_offset_d_code |
|---|---|---|---|---|
| 6 | 36 | 33 | 187 | 258 |
| 6 | 80 | 31 | 137 | 432 |
| 6 | 81 | 2 | 218 | 0 |
| 6 | 134 | 32 | 188 | 125 |
| 6 | 261 | 33 | 187 | 10 |
| 6 | 364 | 83 | 137 | 304 |
| 9 | 36 | 36 | 83 | 258 |
| 9 | 80 | 31 | 33 | 432 |
| 9 | 81 | 5 | 114 | 0 |
| 9 | 134 | 32 | 84 | 125 |
| 9 | 261 | 36 | 83 | 10 |
| 9 | 364 | 86 | 33 | 304 |
| 38 | 36 | 33 | 375 | 258 |
| 38 | 81 | 2 | 406 | 0 |
| 38 | 134 | 32 | 376 | 125 |
| 38 | 261 | 33 | 375 | 10 |
| 38 | 364 | 33 | 375 | 354 |
| 52 | 36 | 37 | 40 | 258 |
| 52 | 81 | 6 | 71 | 0 |
| 52 | 134 | 32 | 41 | 125 |

## Check (a): whether the code-leaning group's labels are empty on prose

Per chain size and source of E_lab: the mean removed label, the damage over whole texts (as `analysis_s7` computes it), the damage per unit of removed label (a ratio of means), and the group-to-twins ratio of that with a 95 percent interval that resamples documents within the source (10000 replicates, uncorrected; none under ten documents). The guard: the ratio is read at a size only if the intervals of the group's removed label and of the twins' damage per unit both exclude zero.

| members | source | texts | documents | group's removed label | twins' | H group | H twins | H per label, group | H per label, twins | ratio | ratio interval | group's label interval | twins' per-unit interval | guard | clean prefix, group | clean prefix, twins | contributing, group | contributing, twins |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 16 | Github | 256 | 69 | 0.06343 | 0.00505 | 0.0159 | 0.0015 | 0.2500 | 0.2945 | 0.8489 | [0.678, 1.067] | [0.04953, 0.07766] | [0.2579, 0.3374] | True | 0.1462 | 0.2955 | 156.0 | 146.2 |
| 64 | Github | 256 | 69 | 0.89897 | 0.09218 | 0.1012 | 0.0118 | 0.1126 | 0.1283 | 0.8773 | [0.716, 1.094] | [0.67797, 1.07866] | [0.1060, 0.1551] | True | 0.0506 | 0.0005 | 47.0 | 2.0 |
| 256 | Github | 256 | 69 | 9.04729 | 0.94624 | 0.6390 | 0.0995 | 0.0706 | 0.1052 | 0.6713 | [0.608, 0.756] | [7.02043, 10.65827] | [0.0938, 0.1161] | True | 0.0013 | 0.0000 | 4.0 | 0.0 |
| 1007 | Github | 256 | 69 | 41.51833 | 7.39849 | 3.2391 | 1.1031 | 0.0780 | 0.1491 | 0.5232 | [0.480, 0.566] | [34.46502, 47.08981] | [0.1384, 0.1634] | True | 0.0000 | 0.0000 | 0.0 | 0.0 |
| 1862 | Github | 256 | 69 | 72.88201 | 19.80526 | 6.8968 | 4.1125 | 0.0946 | 0.2076 | 0.4557 | [0.422, 0.495] | [64.02270, 79.80281] | [0.1897, 0.2265] | True | 0.0000 | 0.0000 | 0.0 | 0.0 |
| 16 | ArXiv | 64 | 3 | 0.00095 | 0.01341 | 0.0007 | 0.0017 | 0.7103 | 0.1281 | 5.5436 | no interval | no interval | no interval | False | 0.6790 | 0.1222 | 61.0 | 34.2 |
| 64 | ArXiv | 64 | 3 | 0.13025 | 0.16085 | 0.0165 | 0.0152 | 0.1267 | 0.0942 | 1.3441 | no interval | no interval | no interval | False | 0.1398 | 0.0000 | 33.0 | 0.0 |
| 256 | ArXiv | 64 | 3 | 1.12247 | 1.66426 | 0.2501 | 0.1244 | 0.2228 | 0.0747 | 2.9813 | no interval | no interval | no interval | False | 0.0186 | 0.0000 | 15.0 | 0.0 |
| 1007 | ArXiv | 64 | 3 | 12.83572 | 10.11044 | 2.4717 | 1.0524 | 0.1926 | 0.1041 | 1.8500 | no interval | no interval | no interval | False | 0.0000 | 0.0000 | 0.0 | 0.0 |
| 1862 | ArXiv | 64 | 3 | 33.03206 | 23.97833 | 4.8024 | 3.6929 | 0.1454 | 0.1540 | 0.9440 | no interval | no interval | no interval | False | 0.0000 | 0.0000 | 0.0 | 0.0 |
| 16 | Pile-CC | 64 | 25 | 0.00005 | 0.01479 | 0.0007 | 0.0019 | 13.9033 | 0.1289 | 107.8653 | [71.876, 178.652] | [0.00003, 0.00007] | [0.1076, 0.1557] | True | 0.9805 | 0.1065 | 64.0 | 35.5 |
| 64 | Pile-CC | 64 | 25 | 0.00101 | 0.19579 | 0.0034 | 0.0248 | 3.3332 | 0.1267 | 26.3165 | [16.749, 54.553] | [0.00049, 0.00164] | [0.1160, 0.1369] | True | 0.7065 | 0.0002 | 59.0 | 0.4 |
| 256 | Pile-CC | 64 | 25 | 0.02940 | 2.09424 | 0.0206 | 0.1760 | 0.7018 | 0.0840 | 8.3519 | [6.766, 12.309] | [0.01917, 0.03824] | [0.0779, 0.0903] | True | 0.0895 | 0.0000 | 39.0 | 0.0 |
| 1007 | Pile-CC | 64 | 25 | 1.08336 | 12.71416 | 0.1616 | 1.4425 | 0.1491 | 0.1135 | 1.3145 | [1.041, 1.874] | [0.70217, 1.44484] | [0.1090, 0.1179] | True | 0.0000 | 0.0000 | 0.0 | 0.0 |
| 1862 | Pile-CC | 64 | 25 | 6.80131 | 30.50198 | 1.1235 | 4.2077 | 0.1652 | 0.1379 | 1.1975 | [1.035, 1.441] | [4.71655, 8.84549] | [0.1339, 0.1417] | True | 0.0000 | 0.0000 | 0.0 | 0.0 |
| 16 | StackExchange | 64 | 44 | 0.03840 | 0.01073 | 0.0113 | 0.0021 | 0.2930 | 0.1937 | 1.5125 | [1.240, 1.851] | [0.02569, 0.05284] | [0.1774, 0.2112] | True | 0.3016 | 0.1471 | 49.0 | 32.4 |
| 64 | StackExchange | 64 | 44 | 0.43974 | 0.12246 | 0.0476 | 0.0156 | 0.1084 | 0.1277 | 0.8483 | [0.733, 0.978] | [0.33691, 0.54936] | [0.1211, 0.1347] | True | 0.0771 | 0.0001 | 30.0 | 0.1 |
| 256 | StackExchange | 64 | 44 | 5.48976 | 1.19998 | 0.3251 | 0.1121 | 0.0592 | 0.0934 | 0.6339 | [0.554, 0.725] | [4.44778, 6.47525] | [0.0896, 0.0977] | True | 0.0077 | 0.0000 | 8.0 | 0.0 |
| 1007 | StackExchange | 64 | 44 | 30.69295 | 8.35881 | 2.1746 | 1.1230 | 0.0709 | 0.1343 | 0.5274 | [0.485, 0.575] | [26.55872, 34.39629] | [0.1290, 0.1403] | True | 0.0000 | 0.0000 | 0.0 | 0.0 |
| 1862 | StackExchange | 64 | 44 | 53.59355 | 21.89700 | 4.6494 | 3.9171 | 0.0868 | 0.1789 | 0.4850 | [0.456, 0.520] | [47.03892, 59.18929] | [0.1704, 0.1884] | True | 0.0000 | 0.0000 | 0.0 | 0.0 |
| 16 | Wikipedia (en) | 64 | 33 | 0.00007 | 0.01916 | 0.0009 | 0.0027 | 13.0760 | 0.1390 | 94.0886 | [52.332, 232.818] | [0.00003, 0.00012] | [0.1284, 0.1513] | True | 0.9667 | 0.0929 | 64.0 | 31.1 |
| 64 | Wikipedia (en) | 64 | 33 | 0.00181 | 0.18691 | 0.0040 | 0.0212 | 2.2307 | 0.1136 | 19.6443 | [8.600, 70.385] | [0.00049, 0.00428] | [0.1081, 0.1187] | True | 0.6524 | 0.0001 | 57.0 | 0.1 |
| 256 | Wikipedia (en) | 64 | 33 | 0.05771 | 2.37259 | 0.0263 | 0.1787 | 0.4558 | 0.0753 | 6.0496 | [2.914, 19.711] | [0.01613, 0.14094] | [0.0722, 0.0785] | True | 0.0704 | 0.0000 | 33.0 | 0.0 |
| 1007 | Wikipedia (en) | 64 | 33 | 1.06556 | 14.09109 | 0.1978 | 1.6149 | 0.1857 | 0.1146 | 1.6200 | [1.304, 2.128] | [0.68579, 1.66612] | [0.1116, 0.1181] | True | 0.0000 | 0.0000 | 0.0 | 0.0 |
| 1862 | Wikipedia (en) | 64 | 33 | 7.81754 | 33.41305 | 1.5021 | 4.7298 | 0.1921 | 0.1416 | 1.3573 | [1.234, 1.498] | [6.39872, 9.48073] | [0.1384, 0.1446] | True | 0.0000 | 0.0000 | 0.0 | 0.0 |

**Reading (mark 0.2, at 64 and 256 members).**
- Pile-CC: **not met**. at 64 members the ratio is 26.316 [16.749, 54.553], guard passes; at 256 members the ratio is 8.352 [6.766, 12.309], guard passes (25 documents).
- Wikipedia (en): **not met**. at 64 members the ratio is 19.644 [8.600, 70.385], guard passes; at 256 members the ratio is 6.050 [2.914, 19.711], guard passes (33 documents).
- "The labels fire on prose without effect" is **not supported** (supported only if the mark is met on both prose sources).

## Check (b): the existence rule run prose against prose

The existence rule on matched pools of 256 rows. Two floors (usage at least 1e-3 in at least 8 distinct rows, or documents; the document floor is primary) and three nulls (the rule's row shuffle; a document shuffle, variant (a): the first D_A documents of a permutation of the pooled documents, primary; variant (b): documents until the row count is nearest 256). Verdict words come from the document nulls only; where (a) and (b) differ, both are printed and the pair is marginal.

| pair (pool A against pool B) | documents A | documents B | floor counts | null shuffles | shuffles | members of G_0.9 | firing mass F | share | null p95 | bar (F / 5) | word under this null | verdict for the floor |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| code against prose, 512 against 512 (the code-leaning group's) | 96 | 203 | rows | rows | 200 | 1007 | 49.4702 | 0.2476 | 0.0029 | 9.8940 | clear | n/a |
| Wikipedia against Pile-CC | 105 | 98 | documents | rows | 2000 | 125 | 1.1962 | 0.0058 | 0.0055 | 0.2392 | none | none |
| Wikipedia against Pile-CC | 105 | 98 | documents | documents (a) | 2000 | 125 | 1.1962 | 0.0058 | 0.2688 | 0.2392 | none | none |
| Wikipedia against Pile-CC | 105 | 98 | documents | documents (b) | 2000 | 125 | 1.1962 | 0.0058 | 0.3102 | 0.2392 | none | none |
| Wikipedia against Pile-CC | 105 | 98 | rows | rows | 2000 | 125 | 1.1962 | 0.0058 | 0.0055 | 0.2392 | none | none |
| Wikipedia against Pile-CC | 105 | 98 | rows | documents (a) | 2000 | 125 | 1.1962 | 0.0058 | 0.2755 | 0.2392 | none | none |
| Wikipedia against Pile-CC | 105 | 98 | rows | documents (b) | 2000 | 125 | 1.1962 | 0.0058 | 0.3230 | 0.2392 | none | none |
| Pile-CC against Wikipedia | 98 | 105 | documents | rows | 2000 | 90 | 1.5510 | 0.0080 | 0.0055 | 0.3102 | none | none |
| Pile-CC against Wikipedia | 98 | 105 | documents | documents (a) | 2000 | 90 | 1.5510 | 0.0080 | 0.3127 | 0.3102 | none | none |
| Pile-CC against Wikipedia | 98 | 105 | documents | documents (b) | 2000 | 90 | 1.5510 | 0.0080 | 0.3240 | 0.3102 | none | none |
| Pile-CC against Wikipedia | 98 | 105 | rows | rows | 2000 | 97 | 1.5740 | 0.0081 | 0.0055 | 0.3148 | none | none |
| Pile-CC against Wikipedia | 98 | 105 | rows | documents (a) | 2000 | 97 | 1.5740 | 0.0081 | 0.3244 | 0.3148 | none | none |
| Pile-CC against Wikipedia | 98 | 105 | rows | documents (b) | 2000 | 97 | 1.5740 | 0.0081 | 0.3375 | 0.3148 | none | none |
| code against Pile-CC | 54 | 98 | documents | rows | 200 | 1008 | 52.2704 | 0.2629 | 0.0241 | 10.4541 | clear | clear |
| code against Pile-CC | 54 | 98 | documents | documents (a) | 200 | 1008 | 52.2704 | 0.2629 | 2.2109 | 10.4541 | clear | clear |
| code against Pile-CC | 54 | 98 | documents | documents (b) | 200 | 1008 | 52.2704 | 0.2629 | 0.7211 | 10.4541 | clear | clear |
| code against Pile-CC | 54 | 98 | rows | rows | 200 | 1014 | 52.2779 | 0.2629 | 0.0252 | 10.4556 | clear | clear |
| code against Pile-CC | 54 | 98 | rows | documents (a) | 200 | 1014 | 52.2779 | 0.2629 | 2.2353 | 10.4556 | clear | clear |
| code against Pile-CC | 54 | 98 | rows | documents (b) | 200 | 1014 | 52.2779 | 0.2629 | 0.7247 | 10.4556 | clear | clear |
| Pile-CC against code | 98 | 54 | documents | rows | 200 | 1103 | 39.1592 | 0.2025 | 0.0306 | 7.8318 | clear | clear |
| Pile-CC against code | 98 | 54 | documents | documents (a) | 200 | 1103 | 39.1592 | 0.2025 | 0.6967 | 7.8318 | clear | clear |
| Pile-CC against code | 98 | 54 | documents | documents (b) | 200 | 1103 | 39.1592 | 0.2025 | 0.8158 | 7.8318 | clear | clear |
| Pile-CC against code | 98 | 54 | rows | rows | 200 | 1107 | 39.1729 | 0.2025 | 0.0309 | 7.8346 | clear | clear |
| Pile-CC against code | 98 | 54 | rows | documents (a) | 200 | 1107 | 39.1729 | 0.2025 | 0.6967 | 7.8346 | clear | clear |
| Pile-CC against code | 98 | 54 | rows | documents (b) | 200 | 1107 | 39.1729 | 0.2025 | 0.8220 | 7.8346 | clear | clear |
| code against Wikipedia | 54 | 105 | documents | rows | 200 | 1114 | 56.4532 | 0.2839 | 0.0000 | 11.2906 | clear | clear |
| code against Wikipedia | 54 | 105 | documents | documents (a) | 200 | 1114 | 56.4532 | 0.2839 | 0.4164 | 11.2906 | clear | clear |
| code against Wikipedia | 54 | 105 | documents | documents (b) | 200 | 1114 | 56.4532 | 0.2839 | 0.2565 | 11.2906 | clear | clear |
| code against Wikipedia | 54 | 105 | rows | rows | 200 | 1120 | 56.4606 | 0.2839 | 0.0000 | 11.2921 | clear | clear |
| code against Wikipedia | 54 | 105 | rows | documents (a) | 200 | 1120 | 56.4606 | 0.2839 | 0.4388 | 11.2921 | clear | clear |
| code against Wikipedia | 54 | 105 | rows | documents (b) | 200 | 1120 | 56.4606 | 0.2839 | 0.2718 | 11.2921 | clear | clear |
| Wikipedia against code | 105 | 54 | documents | rows | 200 | 857 | 40.8977 | 0.1983 | 0.0049 | 8.1795 | clear | clear |
| Wikipedia against code | 105 | 54 | documents | documents (a) | 200 | 857 | 40.8977 | 0.1983 | 0.3059 | 8.1795 | clear | clear |
| Wikipedia against code | 105 | 54 | documents | documents (b) | 200 | 857 | 40.8977 | 0.1983 | 0.2464 | 8.1795 | clear | clear |
| Wikipedia against code | 105 | 54 | rows | rows | 200 | 857 | 40.8977 | 0.1983 | 0.0049 | 8.1795 | clear | clear |
| Wikipedia against code | 105 | 54 | rows | documents (a) | 200 | 857 | 40.8977 | 0.1983 | 0.3060 | 8.1795 | clear | clear |
| Wikipedia against code | 105 | 54 | rows | documents (b) | 200 | 857 | 40.8977 | 0.1983 | 0.2577 | 8.1795 | clear | clear |

Rows superseded by a rerun at 2000 shuffles (a document null's 95th percentile within a factor of two of the bar): 12; they stay in the CSV.

**Reading.** Wikipedia against Pile-CC under the document floor: **none**; Pile-CC against Wikipedia: **none**. So: **code-leaning stands**.

## Check (d): where the merging harm falls

### Texts (from the committed tables)

| cells | rung | size | draws | mean excess | texts above 0.05 (draw-averaged) | texts above 0.1 (draw-averaged) | texts above 0.2 (draw-averaged) | (text, draw) pairs above 0.05 | (text, draw) pairs above 0.1 | (text, draw) pairs above 0.2 |
|---|---|---|---|---|---|---|---|---|---|---|
| curve 1 | 1 | 1 token | 8 | 0.0038 | 0.0000 | 0.0000 | 0.0000 | 0.0149 | 0.0011 | 0.0000 |
| curve 1 | 2 | 8 tokens | 8 | 0.0402 | 0.2549 | 0.0146 | 0.0000 | 0.2793 | 0.0682 | 0.0096 |
| curve 1 | 2a | 16 tokens | 8 | 0.1016 | 0.9570 | 0.4766 | 0.0137 | 0.8236 | 0.4158 | 0.0662 |
| curve 1 | 2b | 32 tokens | 8 | 0.2312 | 1.0000 | 0.9883 | 0.6006 | 0.9874 | 0.9385 | 0.5571 |
| curve 1 | 3 | 64 tokens | 8 | 0.4575 | 1.0000 | 1.0000 | 0.9990 | 1.0000 | 0.9961 | 0.9777 |
| curve 1 | 4 | 1 text | 8 | 0.4877 | 1.0000 | 0.9688 | 0.9199 | 0.8967 | 0.8610 | 0.7902 |
| curve 1 | 5a | 2 texts | 8 | 0.7152 | 1.0000 | 1.0000 | 0.9814 | 0.9996 | 0.9965 | 0.9714 |
| curve 1 | 5 | 4 texts | 8 | 0.8516 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 0.9976 |
| curve 1 | 6a | 8 texts | 8 | 0.9242 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 |
| curve 1 | 6 | 16 texts | 8 | 0.9527 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 |
| curve 1 | 7 | 64 texts | 8 | 0.9536 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 |
| curve 1 | 8 | the pool | 1 | 0.9458 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 |
| its same-size random control (ctl-plain) | 1 | 1 token | 8 | -0.0021 | 0.0000 | 0.0000 | 0.0000 | 0.0002 | 0.0000 | 0.0000 |
| its same-size random control (ctl-plain) | 2 | 8 tokens | 8 | -0.0110 | 0.0000 | 0.0000 | 0.0000 | 0.0005 | 0.0000 | 0.0000 |
| its same-size random control (ctl-plain) | 2a | 16 tokens | 8 | -0.0125 | 0.0039 | 0.0000 | 0.0000 | 0.0065 | 0.0005 | 0.0000 |
| its same-size random control (ctl-plain) | 2b | 32 tokens | 8 | -0.0014 | 0.0176 | 0.0107 | 0.0000 | 0.0258 | 0.0100 | 0.0007 |
| its same-size random control (ctl-plain) | 3 | 64 tokens | 8 | 0.0397 | 0.3740 | 0.0508 | 0.0156 | 0.3593 | 0.0648 | 0.0142 |
| its same-size random control (ctl-plain) | 4 | 1 text | 8 | 0.0572 | 0.5352 | 0.0791 | 0.0156 | 0.4456 | 0.1877 | 0.0435 |
| its same-size random control (ctl-plain) | 5a | 2 texts | 8 | 0.1565 | 0.9883 | 0.7920 | 0.2090 | 0.9098 | 0.6877 | 0.2556 |
| its same-size random control (ctl-plain) | 5 | 4 texts | 8 | 0.3222 | 1.0000 | 1.0000 | 0.8945 | 0.9999 | 0.9950 | 0.8270 |
| its same-size random control (ctl-plain) | 6a | 8 texts | 8 | 0.5082 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 0.9965 |
| its same-size random control (ctl-plain) | 6 | 16 texts | 8 | 0.6732 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 |
| its same-size random control (ctl-plain) | 7 | 64 texts | 8 | 0.8606 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 |
| its same-size random control (ctl-plain) | 8 | the pool | 1 | 0.9459 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 |

### Positions (from the per-position arrays)

The unit is a position under one merge. The gate passed on 69 cells (largest difference 8.53e-05 against 0.0005); the arrays and their SHA-256 are in `check_d_pull_manifest.csv`. C_10, C_1, q_50 and the worst tenth of texts are pooled over all units, with the range over the draws.

| cells | size | texts | version | mean rise | S(0.05) | S(0.1) | S(0.2) | S(0.5) | S(1) | S-(0.05) | S-(0.1) | S-(0.2) | S-(0.5) | S-(1) | positions within 0.001 of 0.05 | C_10 | C_1 | q_50 | worst tenth of texts |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| curve 1 | 1 token | all texts | per merge (draws not averaged) | 0.0038 | 0.0900 | 0.0366 | 0.0111 | 0.0012 | 0.0001 | 0.0685 | 0.0175 | 0.0028 | 0.0001 | 0.0000 | 16356 | 3.032 (2.112 to 7.283) | 0.931 (0.575 to 2.150) | 0.004 (0.001 to 0.008) | 0.787 (0.425 to 1.153) |
| curve 1 | 1 token | all texts | draw-averaged | 0.0038 | 0.0580 | 0.0138 | 0.0022 | 0.0001 | 0.0000 | 0.0368 | 0.0081 | 0.0011 | 0.0001 | 0.0000 | 2135 | 1.842 | 0.473 | 0.011 | 0.375 |
| curve 1 | 8 tokens | all texts | per merge (draws not averaged) | 0.0402 | 0.2972 | 0.1827 | 0.0848 | 0.0190 | 0.0042 | 0.1578 | 0.0654 | 0.0160 | 0.0012 | 0.0001 | 26760 | 0.967 (0.896 to 1.057) | 0.275 (0.218 to 0.329) | 0.028 (0.020 to 0.036) | 0.336 (0.237 to 0.458) |
| curve 1 | 8 tokens | all texts | draw-averaged | 0.0402 | 0.3551 | 0.1763 | 0.0505 | 0.0035 | 0.0002 | 0.0904 | 0.0345 | 0.0083 | 0.0006 | 0.0001 | 5328 | 0.592 | 0.125 | 0.076 | 0.201 |
| curve 1 | 16 tokens | all texts | per merge (draws not averaged) | 0.1016 | 0.4490 | 0.3235 | 0.1866 | 0.0561 | 0.0139 | 0.1456 | 0.0690 | 0.0197 | 0.0020 | 0.0002 | 26204 | 0.667 (0.630 to 0.717) | 0.167 (0.150 to 0.210) | 0.058 (0.048 to 0.065) | 0.240 (0.169 to 0.279) |
| curve 1 | 16 tokens | all texts | draw-averaged | 0.1016 | 0.5639 | 0.3807 | 0.1798 | 0.0287 | 0.0034 | 0.0817 | 0.0365 | 0.0104 | 0.0011 | 0.0001 | 4588 | 0.466 | 0.100 | 0.113 | 0.172 |
| curve 1 | 32 tokens | all texts | per merge (draws not averaged) | 0.2312 | 0.6108 | 0.4979 | 0.3449 | 0.1439 | 0.0504 | 0.1098 | 0.0571 | 0.0187 | 0.0024 | 0.0003 | 21628 | 0.542 (0.500 to 0.567) | 0.129 (0.114 to 0.139) | 0.086 (0.079 to 0.100) | 0.209 (0.183 to 0.236) |
| curve 1 | 32 tokens | all texts | draw-averaged | 0.2312 | 0.7192 | 0.5815 | 0.3797 | 0.1314 | 0.0356 | 0.0629 | 0.0320 | 0.0108 | 0.0016 | 0.0002 | 3001 | 0.444 | 0.097 | 0.123 | 0.183 |
| curve 1 | 64 tokens | all texts | per merge (draws not averaged) | 0.4575 | 0.7605 | 0.6725 | 0.5311 | 0.2849 | 0.1286 | 0.0656 | 0.0364 | 0.0136 | 0.0022 | 0.0004 | 15727 | 0.474 (0.450 to 0.497) | 0.103 (0.096 to 0.106) | 0.110 (0.101 to 0.121) | 0.185 (0.164 to 0.205) |
| curve 1 | 64 tokens | all texts | draw-averaged | 0.4575 | 0.8322 | 0.7422 | 0.5813 | 0.2902 | 0.1200 | 0.0405 | 0.0224 | 0.0089 | 0.0016 | 0.0003 | 1957 | 0.429 | 0.090 | 0.132 | 0.174 |
| curve 1 | 1 text | all texts | per merge (draws not averaged) | 0.4877 | 0.6836 | 0.5998 | 0.4824 | 0.2848 | 0.1457 | 0.0693 | 0.0345 | 0.0121 | 0.0020 | 0.0003 | 16363 | 0.525 (0.438 to 0.973) | 0.116 (0.087 to 0.270) | 0.091 (0.027 to 0.126) | 0.230 (0.159 to 0.359) |
| curve 1 | 1 text | all texts | draw-averaged | 0.4877 | 0.8232 | 0.7295 | 0.5766 | 0.3036 | 0.1336 | 0.0307 | 0.0165 | 0.0067 | 0.0012 | 0.0002 | 2015 | 0.441 | 0.092 | 0.126 | 0.168 |
| its same-size random control (ctl-plain) | 64 tokens | all texts | per merge (draws not averaged) | 0.0397 | 0.3595 | 0.2384 | 0.1153 | 0.0215 | 0.0027 | 0.2254 | 0.1219 | 0.0381 | 0.0037 | 0.0004 | 25817 | 1.033 (0.895 to 1.386) | 0.235 (0.197 to 0.319) | 0.030 (0.019 to 0.038) | 0.340 (0.283 to 0.408) |
| its same-size random control (ctl-plain) | 64 tokens | all texts | draw-averaged | 0.0397 | 0.3823 | 0.2317 | 0.0936 | 0.0108 | 0.0007 | 0.1834 | 0.0917 | 0.0266 | 0.0025 | 0.0002 | 4092 | 0.825 | 0.172 | 0.045 | 0.318 |
| its same-size random control (ctl-plain) | 1 text | all texts | per merge (draws not averaged) | 0.0572 | 0.3683 | 0.2530 | 0.1336 | 0.0320 | 0.0060 | 0.1884 | 0.0963 | 0.0298 | 0.0032 | 0.0003 | 24548 | 0.864 (0.521 to 2.160) | 0.210 (0.112 to 0.505) | 0.038 (0.010 to 0.093) | 0.369 (0.183 to 0.525) |
| its same-size random control (ctl-plain) | 1 text | all texts | draw-averaged | 0.0572 | 0.4356 | 0.2691 | 0.1108 | 0.0127 | 0.0008 | 0.1364 | 0.0641 | 0.0183 | 0.0018 | 0.0002 | 4456 | 0.614 | 0.126 | 0.072 | 0.230 |
| the never-named removal at its whole-set rung (residual included) | 28946 pieces | all texts | per merge (draws not averaged) | 1.2841 | 0.9723 | 0.9527 | 0.9154 | 0.7580 | 0.4650 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 451 | 0.323 (0.323 to 0.323) | 0.057 (0.057 to 0.057) | 0.201 (0.201 to 0.201) | 0.149 (0.149 to 0.149) |
| the code-leaning edit at 256 members | 256 members | the GitHub half | per merge (draws not averaged) | 0.6390 | 0.6694 | 0.5714 | 0.4694 | 0.3194 | 0.1962 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 820 | 0.536 (0.536 to 0.536) | 0.111 (0.111 to 0.111) | 0.088 (0.088 to 0.088) | 0.213 (0.213 to 0.213) |
| the code-leaning edit at 256 members | 256 members | the other half | per merge (draws not averaged) | 0.1555 | 0.2508 | 0.1650 | 0.1142 | 0.0654 | 0.0370 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 910 | 0.814 (0.814 to 0.814) | 0.303 (0.303 to 0.303) | 0.024 (0.024 to 0.024) | 0.399 (0.399 to 0.399) |

A share of the total rise is a share of the *net* total, negative positions included (as in the worked example), so it exceeds 1 where falls cancel much of the rise, as at the small merges. Draws whose own total rise is not positive have no such share and are left out of the ranges: 1 over all rows (`n_draws_total_rise_not_positive`).

The mean rise by position in the text, eight blocks of 64 positions (`check_d_by_block.csv`):

| cells | size | texts | 0 to 63 | 64 to 127 | 128 to 191 | 192 to 255 | 256 to 319 | 320 to 383 | 384 to 447 | 448 to 511 |
|---|---|---|---|---|---|---|---|---|---|---|
| curve 1 | 1 token | all texts | 0.0034 | 0.0043 | 0.0040 | 0.0041 | 0.0039 | 0.0036 | 0.0035 | 0.0034 |
| curve 1 | 8 tokens | all texts | 0.0335 | 0.0397 | 0.0404 | 0.0411 | 0.0411 | 0.0415 | 0.0414 | 0.0427 |
| curve 1 | 16 tokens | all texts | 0.0855 | 0.0980 | 0.1008 | 0.1026 | 0.1045 | 0.1057 | 0.1066 | 0.1093 |
| curve 1 | 32 tokens | all texts | 0.1972 | 0.2209 | 0.2270 | 0.2329 | 0.2363 | 0.2415 | 0.2448 | 0.2486 |
| curve 1 | 64 tokens | all texts | 0.4045 | 0.4407 | 0.4483 | 0.4590 | 0.4655 | 0.4747 | 0.4827 | 0.4848 |
| curve 1 | 1 text | all texts | 0.4466 | 0.4807 | 0.4810 | 0.4905 | 0.4919 | 0.4996 | 0.5026 | 0.5085 |
| its same-size random control (ctl-plain) | 64 tokens | all texts | 0.0341 | 0.0382 | 0.0400 | 0.0395 | 0.0407 | 0.0413 | 0.0418 | 0.0421 |
| its same-size random control (ctl-plain) | 1 text | all texts | 0.0525 | 0.0567 | 0.0577 | 0.0573 | 0.0586 | 0.0583 | 0.0586 | 0.0581 |
| the never-named removal at its whole-set rung (residual included) | 28946 pieces | all texts | 1.2287 | 1.2766 | 1.2743 | 1.2817 | 1.2868 | 1.3036 | 1.3105 | 1.3105 |
| the code-leaning edit at 256 members | 256 members | the GitHub half | 0.7137 | 0.6963 | 0.6502 | 0.6252 | 0.6153 | 0.6423 | 0.5969 | 0.5716 |
| the code-leaning edit at 256 members | 256 members | the other half | 0.1654 | 0.1577 | 0.1779 | 0.1448 | 0.1387 | 0.1537 | 0.1567 | 0.1494 |

**Reading.** S(0.05) on curve 1 at 64 tokens is 0.7605, 95 percent interval [0.7569, 0.7642] over texts (10000 replicates, draws held fixed): **on most positions**. The eight draws one by one run from 0.7346 to 0.7893, a spread the interval does not carry, since it holds the draws fixed. Concentration is reported as numbers and carries no word.

## Check (c): the donors' kind of text against the small-merge harm

| donor tokens | draw | n_on | donor positions in code texts | named set in G_0.9 | named set in the prose-leaning group | matched set in G_0.9 | matched set in the prose-leaning group | U - M, code texts | U - M, prose texts |
|---|---|---|---|---|---|---|---|---|---|
| 1 | 0 | 201 | 0 | 0.0000 | 0.0896 | 0.0547 | 0.0945 | 0.0009 | 0.0165 |
| 1 | 1 | 222 | 0 | 0.0045 | 0.2883 | 0.0991 | 0.1216 | 0.0006 | 0.0087 |
| 1 | 2 | 226 | 0 | 0.0044 | 0.0310 | 0.0752 | 0.0664 | 0.0017 | 0.0106 |
| 1 | 3 | 143 | 0 | 0.0000 | 0.0839 | 0.0629 | 0.0769 | 0.0017 | 0.0110 |
| 1 | 4 | 212 | 1 | 0.3538 | 0.0000 | 0.0660 | 0.0708 | 0.0499 | 0.0034 |
| 1 | 5 | 154 | 0 | 0.0000 | 0.1364 | 0.0584 | 0.0260 | -0.0010 | 0.0078 |
| 1 | 6 | 38 | 0 | 0.2632 | 0.0000 | 0.1053 | 0.0526 | 0.0035 | 0.0026 |
| 1 | 7 | 156 | 0 | 0.1474 | 0.0833 | 0.0641 | 0.0577 | 0.0051 | 0.0045 |
| 8 | 0 | 1039 | 1 | 0.1261 | 0.1088 | 0.0760 | 0.0799 | 0.0617 | 0.0448 |
| 8 | 1 | 1287 | 1 | 0.1080 | 0.0940 | 0.0901 | 0.0831 | 0.0338 | 0.0456 |
| 8 | 2 | 1066 | 0 | 0.0413 | 0.0966 | 0.0788 | 0.0797 | 0.0103 | 0.0509 |
| 8 | 3 | 1530 | 2 | 0.1124 | 0.0327 | 0.0797 | 0.0614 | 0.0881 | 0.0508 |
| 8 | 4 | 1201 | 1 | 0.1782 | 0.0441 | 0.1049 | 0.0908 | 0.0852 | 0.0302 |
| 8 | 5 | 891 | 1 | 0.0202 | 0.1111 | 0.0640 | 0.0584 | 0.0204 | 0.0521 |
| 8 | 6 | 950 | 3 | 0.0853 | 0.1432 | 0.0884 | 0.0737 | 0.0306 | 0.0479 |
| 8 | 7 | 1001 | 0 | 0.1678 | 0.0629 | 0.0889 | 0.0819 | 0.0828 | 0.0304 |

**Reading (eight tokens, prose texts, 8 draws).** Spearman of the named set's code-leaning share with U - M: -0.929 (bar 0.74); of n_on with the same U - M: -0.214. A domain block is **not seen**. *Not seen* carries no weight in the post: with eight draws a true correlation of 0.6 gives 0.3 or less about one time in five, so a null here is not evidence of absence, and the tier-5 same-domain merge tests the same rival on far more data. The one-token table is a description and carries no reading.
