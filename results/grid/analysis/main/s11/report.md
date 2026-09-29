# Outcome: A

The binary union on main, read by the rule fixed before any store of the run existed. The primary form (own labels rounded at 0, start `rounded_0`) decides; the secondary form and the look-alike control are described beside it and no rule reads them. Every interval is a text bootstrap over the texts of E with the draws held fixed, 10000 replicates, percentile, at level 1 - 0.05/4; material means the lower end exceeds 0.05 nats.

Outcome C would mean *no drift from the original model at the sizes tested*, not that the union equation holds: the excess compares each mask with the original model, so a text's rises and falls at different positions can cancel. A *fails* carries over to the paper's equation; a *holds* does not. Donors are cut at 0.1 while the recipient is cut at 0, so the merged set is smaller than the equation's literal union at 0, an asymmetry that favours the paper.

## 0. What was asserted before anything was read

- The guard: commit c57fc2b543b4, dirty flag 0, freeze c57fc2b (HEAD or its ancestor: True), enforced: True. This module's blob on disk, at HEAD, at the freeze: 38efee525f14, 38efee525f14, 38efee525f14. The nine frozen modules against main (c57fc2b543b4): all equal (s11_frozen_modules.csv).
- The store results/grid/main_s11/tier6/E__binary_union: 79 cells, 1024 texts, 8 draws, complete; launched at commit df84096baba9 (dirty flag 0) on NVIDIA A100-SXM4-40GB, bf16. The launch summary: 79 cells run, 0 failed, P3 True.
- The canary: 5 cells (the four references and the headline union at draw 0, rung 2) bitwise equal to their committed per-text divergences. Every named set equal to its committed twin's: {'binary_named_sets': 48, 'look_alike_sets': 24, 'look_alike_matched_sets': 24, 'self_merge_sets': 2, 'canary': 1}.
- P3 on the primary form: 49 permitted cells, 0 entries below their label, smallest m - g 0; the secondary form's 25 cells are not permitted (25 with entries below their label, as rounding at 0.1 must give).
- The committed fractional comparators, recomputed: 8 tokens 0.0402, 16 tokens 0.1016, 64 tokens 0.4575, the self-merge 1.0298 (equal to the table fixed in advance, to four decimals).

## 1. Step 1: the verdict (the primary form)

| size | excess | interval_lo | interval_hi | n_draws_positive | sign_condition | detected | material |
|---|---|---|---|---|---|---|---|
| 8 tokens | +0.0363 | +0.0352 | +0.0374 | +8.0000 | yes | yes | no |
| 16 tokens | +0.0963 | +0.0942 | +0.0986 | +8.0000 | yes | yes | yes |
| 64 tokens | +0.4828 | +0.4714 | +0.4951 | +8.0000 | yes | yes | yes |
| the self-merge | +1.0598 | +1.0341 | +1.0863 |  |  |  | yes |

**Verdict: fails**.

## 2. Step 2: the size (read because step 1 says fails)

Within the band means 1/2 e_frac <= e_bin <= 2 e_frac on point estimates, against the committed fractional excesses over the text's own labels. Outcome A needs every one of 8 tokens, 16 tokens, 64 tokens, the self-merge within its band. The paired difference is per text and draw against the committed per-text fractional values; it describes and does not decide.

| size | binary_excess | fractional_excess | band_lo | band_hi | within_band | read_by_the_rule | paired_difference | paired_difference_interval_lo | paired_difference_interval_hi |
|---|---|---|---|---|---|---|---|---|---|
| 8 tokens | +0.0363 | +0.0402 | +0.0201 | +0.0803 | yes | yes | -0.0039 | -0.0047 | -0.0031 |
| 16 tokens | +0.0963 | +0.1016 | +0.0508 | +0.2032 | yes | yes | -0.0053 | -0.0065 | -0.0041 |
| 64 tokens | +0.4828 | +0.4575 | +0.2288 | +0.9151 | yes | yes | +0.0253 | +0.0238 | +0.0266 |
| the self-merge | +1.0598 | +1.0298 | +0.5149 | +2.0595 | yes | yes | +0.0300 | +0.0287 | +0.0312 |

**Outcome: A.**

## 3. Descriptions (no rule reads them)

The secondary form (own labels rounded at 0.1, start `rounded_0.1`), its excesses with the bump rule's labels and its bands against the same fractional comparators:

| size | excess_over_rounded_0.1 | interval_lo | interval_hi | n_draws_positive | detected | material | band_lo | band_hi | within_band |
|---|---|---|---|---|---|---|---|---|---|
| 8 tokens | +0.0359 | +0.0348 | +0.0370 | +8.0000 | yes | no | +0.0201 | +0.0803 | yes |
| 16 tokens | +0.0955 | +0.0932 | +0.0979 | +8.0000 | yes | yes | +0.0508 | +0.2032 | yes |
| 64 tokens | +0.4754 | +0.4639 | +0.4877 | +8.0000 | yes | yes | +0.2288 | +0.9151 | yes |
| the self-merge | +1.0542 | +1.0283 | +1.0808 |  |  | yes | +0.5149 | +2.0595 | yes |

The look-alike control (the committed tier-4 sets in the primary form's mask), its excess over `rounded_0`, and the primary form minus the control, paired per text and draw:

| size | control_excess_over_rounded_0 | control_interval_lo | control_interval_hi | primary_minus_control | primary_minus_control_interval_lo | primary_minus_control_interval_hi |
|---|---|---|---|---|---|---|
| 8 tokens | +0.0105 | +0.0098 | +0.0113 | +0.0258 | +0.0251 | +0.0265 |
| 16 tokens | +0.0473 | +0.0458 | +0.0489 | +0.0490 | +0.0477 | +0.0504 |
| 64 tokens | +0.4249 | +0.4138 | +0.4367 | +0.0579 | +0.0552 | +0.0608 |

The absolute divergences (mean over the texts of E, nats):

| mask | mean_divergence |
|---|---|
| rounded_0 (the primary's start) | +0.3114 |
| rounded_0.1 (the secondary's start) | +0.3174 |
| self-merge, own labels rounded at 0 | +1.3712 |
| self-merge, own labels rounded at 0.1 | +1.3716 |

No switched mass is printed for either binary family: `masks.switched_mass` computes the union's (1 - g) over the named entries and ignores the rounding.

