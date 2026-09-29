# Two recorded claims about tier 3 recomputed from the committed stores

## (a) The level cell s = 0.5 with the never-named set at its labels, against importances-as-masks, per text (results/grid/main/tier3/E__levels/per_sequence.parquet)

Texts below their own importances-as-masks divergence: 1024 of 1024 (equal 0, above 0); the largest paired difference is -0.0156.
Paired difference (level minus importances): median -0.1385, tenth percentile -0.1758, ninetieth -0.0683, mean -0.1291; means 0.2126 and 0.3417.

| quantity | claimed | computed | agrees at the printed precision |
|---|---|---|---|
| n_texts | 1024 | 1024 | True |
| n_texts_below | 1024 | 1024 | True |
| median_paired_difference | -0.138 | -0.138455 | True |
| p10_paired_difference | -0.176 | -0.175778 | True |
| p90_paired_difference | -0.068 | -0.0683429 | True |
| mean_level | 0.2126 | 0.212648 | True |
| mean_importances | 0.3417 | 0.341723 | True |

## (b) The donor-side pass (results/grid/main/tier3/donors_D_unif_k{k}_r{4,7}/; the union on E from results/grid/main/tier1/E)

| rung | draw | donor sequences | n_on | the union on the donors | the donors' own importances-as-masks | the donors' own rounded labels | the same union on E |
|---|---|---|---|---|---|---|---|
| 4 | 0 | 1 | 6764 | 1.5400 | 0.3552 | 0.3261 | 1.0906 |
| 4 | 1 | 1 | 4171 | 1.3768 | 0.2004 | 0.1729 | 0.7580 |
| 4 | 2 | 1 | 5242 | 1.5806 | 0.5257 | 0.4792 | 0.8481 |
| 4 | 3 | 1 | 1366 | 0.2939 | 0.1542 | 0.1568 | 0.3774 |
| 4 | 4 | 1 | 4981 | 2.0131 | 0.3378 | 0.3056 | 0.7932 |
| 4 | 5 | 1 | 5621 | 2.4795 | 0.2514 | 0.2350 | 0.9446 |
| 4 | 6 | 1 | 5550 | 1.3520 | 0.4429 | 0.4215 | 0.8936 |
| 4 | 7 | 1 | 5427 | 1.1078 | 0.4425 | 0.4013 | 0.9299 |
| 7 | 0 | 64 | 9794 | 1.3372 | 0.3432 | 0.3196 | 1.2928 |
| 7 | 1 | 64 | 9580 | 1.2732 | 0.3437 | 0.3189 | 1.2927 |
| 7 | 2 | 64 | 9625 | 1.3338 | 0.3263 | 0.3036 | 1.2964 |
| 7 | 3 | 64 | 9579 | 1.3097 | 0.3689 | 0.3438 | 1.2967 |
| 7 | 4 | 64 | 9704 | 1.3091 | 0.3385 | 0.3135 | 1.2954 |
| 7 | 5 | 64 | 9591 | 1.3156 | 0.3121 | 0.2886 | 1.2974 |
| 7 | 6 | 64 | 9694 | 1.2961 | 0.3417 | 0.3181 | 1.2954 |
| 7 | 7 | 64 | 9707 | 1.2478 | 0.3661 | 0.3403 | 1.2959 |

| rung | column | statistic | claimed | computed | agrees at two decimals |
|---|---|---|---|---|---|
| 4 | union_on_donors | mean over draws | 1.47 | 1.4680 | True |
| 4 | union_on_donors | min over draws | 0.29 | 0.2939 | True |
| 4 | union_on_donors | max over draws | 2.48 | 2.4795 | True |
| 4 | donors_own_importances | mean over draws | 0.34 | 0.3387 | True |
| 4 | donors_own_importances | min over draws | 0.15 | 0.1542 | True |
| 4 | donors_own_importances | max over draws | 0.53 | 0.5257 | True |
| 4 | donors_own_rounded | mean over draws | 0.31 | 0.3123 | True |
| 4 | donors_own_rounded | min over draws | 0.16 | 0.1568 | True |
| 4 | donors_own_rounded | max over draws | 0.48 | 0.4792 | True |
| 4 | same_union_on_E | mean over draws | 0.83 | 0.8294 | True |
| 7 | union_on_donors | mean over draws | 1.3 | 1.3028 | True |
| 7 | union_on_donors | min over draws | 1.25 | 1.2478 | True |
| 7 | union_on_donors | max over draws | 1.34 | 1.3372 | True |
| 7 | donors_own_importances | mean over draws | 0.34 | 0.3426 | True |
| 7 | donors_own_importances | min over draws | 0.31 | 0.3121 | True |
| 7 | donors_own_importances | max over draws | 0.37 | 0.3689 | True |
| 7 | donors_own_rounded | mean over draws | 0.32 | 0.3183 | True |
| 7 | donors_own_rounded | min over draws | 0.29 | 0.2886 | True |
| 7 | donors_own_rounded | max over draws | 0.34 | 0.3438 | True |
| 7 | same_union_on_E | mean over draws | 1.29 | 1.2953 | False |
| 4 | union_on_donors | draw 0 | 1.54 | 1.5400 | True |
| 4 | union_on_donors | draw 1 | 1.38 | 1.3768 | True |
| 4 | union_on_donors | draw 2 | 1.58 | 1.5806 | True |
| 4 | union_on_donors | draw 3 | 0.29 | 0.2939 | True |
| 4 | union_on_donors | draw 4 | 2.01 | 2.0131 | True |
| 4 | union_on_donors | draw 5 | 2.48 | 2.4795 | True |
| 4 | union_on_donors | draw 6 | 1.35 | 1.3520 | True |
| 4 | union_on_donors | draw 7 | 1.11 | 1.1078 | True |
| 4 | donors_own_importances | draw 0 | 0.36 | 0.3552 | True |
| 4 | donors_own_importances | draw 1 | 0.2 | 0.2004 | True |
| 4 | donors_own_importances | draw 2 | 0.53 | 0.5257 | True |
| 4 | donors_own_importances | draw 3 | 0.15 | 0.1542 | True |
| 4 | donors_own_importances | draw 4 | 0.34 | 0.3378 | True |
| 4 | donors_own_importances | draw 5 | 0.25 | 0.2514 | True |
| 4 | donors_own_importances | draw 6 | 0.44 | 0.4429 | True |
| 4 | donors_own_importances | draw 7 | 0.44 | 0.4425 | True |

(a) all agree: True; (b) 35 of 36 agree.
