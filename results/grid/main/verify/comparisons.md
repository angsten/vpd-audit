# The verification launch on the paper's model

1. References against the acceptance table: 25 cells, 25600 of 25600 (cell, sequence) pairs; kl_mean equal True, ce equal True -> pass
2. The two chains against the identities launch: 16 cells, 16384 of 16384 pairs; kl_mean equal True, mask_fp_cell equal True -> pass (equality only; no value of these chains is printed)
3. The fourth cell of the two-by-two (ends), mean over E with the sequence standard error:
| row | mean | se |
|---|---|---|
| unmasked | 0.0115 | 0.0001 |
| importances-as-masks | 0.3417 | 0.0032 |
| F_excluded (soft_erase/D_unif/tau0.1/r1/excl/k0/r8) | 0.3615 | 0.0032 |
| F_included (soft_erase/D_unif/tau0.1/r1/incl/k0/r8) | 0.3615 | 0.0032 |

| paired difference | mean | se |
|---|---|---|
| F_excluded - importances | +0.0198 | 0.0004 |
| F_excluded - unmasked | +0.3501 | 0.0032 |
| F_included - importances | +0.0198 | 0.0004 |
| F_included - unmasked | +0.3500 | 0.0032 |

4. The never-named chain's rung 8 (28946 erased): Delta excluded over the first 128 sequences 1.2944 against H4's 1.2944 (float32), difference +0.0000, within 0.01: True; Delta excluded over all of E 1.2876 (se 0.0093); Delta included over all of E 1.2847 (se 0.0093)
   t*_b at tau_q = 0.1 on E: median 512, quartiles 512 / 512, fraction equal to T 0.995, fraction at least 8 0.996, clean-prefix fraction 0.996 (the same in both Delta settings: True)
   t*_b at tau_q = 0 on E: median 1, quartiles 0 / 1, fraction equal to T 0.000, fraction at least 8 0.011, clean-prefix fraction 0.002 (the same in both Delta settings: True)

Resume test on this launch: a second store of the same cells interrupted after sub-batch 2 and resumed; 46080 rows, every column equal True, cell table equal True, 45 arrays equal True -> pass
Two-path check on this store: 10 hard-zero cells, 3094 checks with t* > 0, largest ratio 0.9411 (non-finite 0) -> pass
