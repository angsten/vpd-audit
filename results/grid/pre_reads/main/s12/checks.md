# Label-only checks: the panels' documents, the 2- and 4-token merge sets, the erased sets, the removed label (main)

Label tables built on CPU at commit c57fc2b543b4 (dirty flag 0), 8 draws, master seed 0.

## The panels' document index

Every part C re-run equals the authors' `tokenize_documents` id for id, with the manifest's row and document counts; every panel row equals the rebuilt stream bitwise; every panel's `sha256_ids` equals the committed manifests' ({'panel_Github': 1, 'panel_StackExchange': 2, 'panel_ArXiv': 2, 'panel_Pile_CC': 2, 'panel_Wikipedia__en_': 2, 'panel_DM_Mathematics': 1, 'panel_PubMed_Central': 1, 'panel_FreeLaw': 1}).

| panel | rows | distinct documents | rows per document (mean, max) | rows sharing a document | part C documents |
|---|---|---|---|---|---|
| panel_Github | 200 | 193 | 1.036, 2 | 14 | 6112 |
| panel_StackExchange | 200 | 197 | 1.015, 2 | 6 | 9983 |
| panel_ArXiv | 200 | 162 | 1.235, 4 | 68 | 811 |
| panel_Pile_CC | 200 | 192 | 1.042, 3 | 14 | 17597 |
| panel_Wikipedia__en_ | 200 | 184 | 1.087, 3 | 29 | 5826 |
| panel_DM_Mathematics | 200 | 174 | 1.149, 3 | 49 | 669 |
| panel_PubMed_Central | 200 | 186 | 1.075, 2 | 28 | 1992 |
| panel_FreeLaw | 200 | 174 | 1.149, 3 | 50 | 1698 |

Per part C: straddling tokens, separator pieces, cut separators, end-of-text strings inside documents: ArXiv 0, 0, 0, 0; DM Mathematics 0, 0, 0, 0; FreeLaw 0, 0, 0, 0; Github 0, 0, 0, 0; Pile-CC 0, 6, 1, 0; PubMed Central 0, 0, 0, 0; StackExchange 0, 0, 0, 0; Wikipedia (en) 0, 14, 2, 0

## The merge sets at 2 and 4 donor tokens

- Donor positions at 1, 2, 4, 8 tokens strictly nested for every pool and draw, and the named sets nested (32 real-merge chains); the plain and marginal controls of D_unif on E nested (16 chains); each control's matched set is the real merge's; the D_unif sets on E_lab are E's at every draw and rung.
- The rebuilt sets at rungs "1" (1 token) and "2" (8 tokens) equal the committed cells' by SHA-256: 96 cells ({'results/grid/main/tier1/E': 16, 'results/grid/main/tier2/E': 16, 'results/grid/main/tier4/E__marginal': 16, 'results/grid/main_s9/tier5/E_lab__same_domain': 48}).

n_on per draw of the real merge (the number of components the donor tokens name):

| set | donors | 2 tokens (T2) | 4 tokens (T4) |
|---|---|---|---|
| E | D_unif | 350, 467, 355, 804, 540, 299, 120, 259 (mean 399.2) | 627, 665, 524, 1067, 815, 564, 554, 548 (mean 670.5) |
| E_lab | D_unif | 350, 467, 355, 804, 540, 299, 120, 259 (mean 399.2) | 627, 665, 524, 1067, 815, 564, 554, 548 (mean 670.5) |
| E_lab | D_code | 421, 167, 331, 188, 196, 462, 312, 414 (mean 311.4) | 692, 445, 585, 380, 647, 686, 654, 596 (mean 585.6) |
| E_lab | D_prose | 553, 342, 233, 252, 229, 296, 321, 353 (mean 322.4) | 795, 639, 463, 421, 411, 713, 553, 591 (mean 573.2) |

## The erased sets

- The group's sets at 256, 1007 members and their twins under 8 draws equal the committed cells' by SHA-256: 18 cells ({'results/grid/main/tier4/E_lab__code_leaning': 18}). Group 1007, wide set 1862.

## The removed label on the panels (descriptive)

omega: the sum over the erased components of their labels, averaged over a row's positions and then over the rows.

| panel | members | omega, group | omega, twins (mean of 8 draws) | twins' draws, min to max | rank by the group's omega |
|---|---|---|---|---|---|
| panel_Github | 256 | 9.7921 | 0.7908 | 0.6982 to 0.8560 | 1 |
| panel_StackExchange | 256 | 5.7138 | 1.1033 | 0.9959 to 1.2108 | 2 |
| panel_ArXiv | 256 | 1.3863 | 1.6896 | 1.2571 to 2.0894 | 3 |
| panel_Pile_CC | 256 | 0.1603 | 2.0540 | 1.8994 to 2.2445 | 4 |
| panel_Wikipedia__en_ | 256 | 0.0575 | 2.3324 | 2.0454 to 2.5842 | 5 |
| panel_Github | 1007 | 43.0250 | 6.4308 | 5.4592 to 7.4002 | 1 |
| panel_StackExchange | 1007 | 31.0223 | 7.8589 | 7.1067 to 8.6184 | 2 |
| panel_ArXiv | 1007 | 15.4455 | 10.0171 | 9.0680 to 10.6927 | 3 |
| panel_Pile_CC | 1007 | 2.1108 | 12.4501 | 11.6052 to 13.5730 | 4 |
| panel_Wikipedia__en_ | 1007 | 1.2403 | 13.9799 | 13.1133 to 15.1459 | 5 |

Order by the group's omega: 256 members: Github > StackExchange > ArXiv > Pile-CC > Wikipedia (en); 1007 members: Github > StackExchange > ArXiv > Pile-CC > Wikipedia (en)

Validation on E_lab (18 cells, the cache's omega against the loop's in the committed store, per text): largest absolute difference 7.79e-06, largest relative 2.32e-07; 5698 of 9216 texts equal in float32. Reported, not asserted.
