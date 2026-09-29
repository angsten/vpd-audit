# The label-only checks before launch (main)

Label tables built on CPU at commit c0d6f5852deb (dirty flag 0), 8 draws, master seed 0.

- Every set of the launch equals its committed twin's by SHA-256, and every look-alike control's matched set is the committed union set of its draw and rung: {'binary_named_sets': 48, 'look_alike_sets': 24, 'look_alike_matched_sets': 24, 'self_merge_sets': 2, 'canary': 1} (75 rows of sets.csv).

The label gate (printed, not asserted):

- rounded_0 reference, mean divergence on E (committed store results/grid/main/tier1/E): 0.3114 nats
- labels above zero per position of E, from its label cache (the pieces rounded_0 switches on): 203.4 (expected about 203); stored per position 203.4; stored labels not above zero 0; above 0.1 per position 189.8
- rounded_0.1 reference, mean divergence on E: 0.3174 nats (expected about 0.317)
- rounded_0 cross-entropy from results/acceptance/vs_paper.csv: 2.9570 (expected 2.957; the paper's 2.94)
