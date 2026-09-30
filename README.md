# Auditing the Released VPD Decomposition: Code, Results, and Technical Report

This repository holds the code, the committed results, and a technical report behind the post *Do VPD's Explanations Aggregate? An Audit of the Released Decomposition*. The post asks whether the causal-importance labels of the released adVersarial Parameter Decomposition (VPD) [1] can be trusted under two uses a practitioner would make of them: aggregating the explanations of several inputs, and deleting components to edit the model. Everything here concerns one decomposition, the one the paper released for its four-layer, 67M-parameter language model. The authors' repository also points to a newer, unpublished training recipe, and nothing here was applied to it.

- **`REPORT.md`** is the technical report. It gives the exact definitions, every measurement behind the post with its interval, the statistics as used, the checks that make the code trustworthy, and the standing of every number: which were read by a rule written down before the data and which are descriptive.
- **This README** says how to set up and reproduce the results, where every number and figure in the post comes from, and how the repository is laid out.

This audit was designed and directed by Thomas Angsten. Much of the code and analysis was carried out with the help of AI agents, working in scoped sessions on clearly defined tasks. The research questions, methods, and decisions were directed by the author, who is responsible for all conclusions.

## Setup and Reproduction

### Requirements

- **Python 3.13** and **[uv](https://docs.astral.sh/uv/)**. Every dependency is pinned in `uv.lock`, and `torch`, `transformers`, `datasets`, `wandb`, and `numpy` are pinned to the versions in the authors' own lockfile.
- **The authors' code**, as a git submodule at `third_party/param-decomp`, pinned to commit `74146b5` of [goodfire-ai/param-decomp](https://github.com/goodfire-ai/param-decomp) (MIT licence). Clone with submodules, then run `make bootstrap`, which checks the submodule commit and runs `uv sync`.
- **To regenerate the post's figures and the level-1 analyses below from the committed results:** a laptop CPU. No model, data, or GPU is needed.
- **To re-run measurements:** a GPU and the model files below. The measurements here were taken on NVIDIA A100 GPUs in bfloat16 autocast, with 12 GiB of host memory, through [Modal](https://modal.com) (`vpd_audit/modal_app.py`): nearly all on the 40 GB card, and four stores on the 80 GB card, as each store's `run_manifest.json` records under `gpu_name`. Their reference conditions agree bit for bit across cards at the same batch shape (64 texts per batch). Other hardware agrees to many digits but not bit for bit.

```
git clone --recurse-submodules <this repository>
cd <this repository>
make bootstrap
make test
```

### The Model and Its Decomposition

The decomposition, its target model, and a second decomposition trained without the adversarial loss are public runs in the WandB project `goodfire/spd`:

| Run | What it is | Size |
|---|---|---|
| `s-55ea3f9b` | the paper's decomposition of its four-layer, 67M-parameter model (38,912 components in 24 weight matrices) | 2.9 GB |
| `t-9d2b8f02` | the target model it decomposes | 0.3 GB |
| `s-05ef623e` | the same decomposition trained without the adversarial loss | 2.9 GB |
| `s-eab2ace8`, `gf6rbga0` | a small two-layer model and its decomposition, used only to dry-run the code | 0.15 GB |

`uv run vpd-audit fetch` downloads them once into `.cache/artifacts/` and writes a manifest of sizes and SHA-256 hashes; `vpd-audit verify-artifacts` re-checks them. The fetch needs a WandB API key (a free account's) in the environment or in a `.env` file. The key is read only by the fetch and is never printed or stored. After the fetch, loading needs no key. Set `VPD_AUDIT_CACHE_DIR` to put the cache elsewhere.

### The Data

- **Recipient texts and general donor texts.** Rows 0 to 1,023 (recipients) and 1,024 to 2,047 (general donors) of the `val` split of [`danbraunai/pile-uncopyrighted-tok-shuffled`](https://huggingface.co/datasets/danbraunai/pile-uncopyrighted-tok-shuffled), the authors' tokenized Pile, read in stream order and cut to 512 tokens as the authors' loader cuts them. Build them with `vpd-audit prepare-data`. The saved arrays are checked against SHA-256 hashes on every load.
- **Texts labelled by source.** The code and prose donors, the labelled recipients (GitHub, web text, Wikipedia, StackExchange, ArXiv), and the 200-text panels come from `val.jsonl.zst` of [`monology/pile-uncopyrighted`](https://huggingface.co/datasets/monology/pile-uncopyrighted), tokenized with the GPT-NeoX-20B tokenizer the model uses. Each source's documents are split by a seeded permutation into three disjoint parts: part A for choosing components and for donors, part B for the labelled recipients, part C for the panels. Build them with `vpd-audit prepare-data --labeled`. Their manifest, with row counts and hashes, is `results/data/labeled_manifest.json`.
- **Label caches.** Every component's label at every token of each donor pool. They are computed on the GPU, are several GB, and are not in the repository. They are needed only to rebuild the label-only tables and the component sets, which are committed.

### What Regenerates What

| Level | Needs | Commands | Writes |
|---|---|---|---|
| 1. From committed tables | this repository only | `vpd-audit figures-post`: the post's five figures, each a PNG, the three data figures each with a CSV of exactly what it plots; `vpd-audit post-tables`: three small tables the post and the report quote | `results/post/`, `results/grid/analysis/main/s12/` |
| | | `vpd-audit analyze --run main --frozen <commit>` and `--run control --compare-with main`: the registered readings of the main measurements, the frequency-matched comparison, and the code edit | `results/grid/analysis/{main,control}/` |
| | | `vpd-audit analyze-s11 --run main --freeze <commit>`: the all-or-nothing aggregation | `results/grid/analysis/main/s11/` |
| | | `vpd-audit figures-s9`: the figures behind the similar-donors and plain-terms tables | `results/grid/analysis/main/s9/figures/` |
| | | `vpd-audit analyze-s12 --run main --freeze <commit>`: the 2- and 4-token aggregations and the panels | `results/grid/analysis/main/s12/` |
| 2. Committed tables plus per-token arrays | the per-token divergence arrays of a run (not in the repository because of their size; written by the GPU runs) | `vpd-audit analyze-s9 --run main --frozen <commit>`: similar donors, the self-aggregation, the plain-terms table | `results/grid/analysis/main/s9b/` |
| | the same, plus the label caches | `vpd-audit s9-checks`: the document index, the spread of the harm over positions, the source-leaning checks | `results/grid/analysis/main/s9/` |
| 3. Label-only tables | the label caches (CPU) | the label-only commands (`vpd-audit --help`) | `results/grid/pre_reads/` |
| 4. The measurements | a GPU and the model files | `modal run vpd_audit/modal_app.py::grid --run main --tiers "1,2" [--subset <name>]` | `results/grid/<run>[_sN]/tier<t>/` |

`--frozen <commit>` (`--freeze` for `analyze-s11` and `analyze-s12`, which also accept an earlier commit the current one descends from) must name the current commit, and the working tree must be clean; the analyses refuse to read results of the paper's model otherwise. Each analysis module was committed before the measurements it reads were analysed, and, with one exception stated in the report (section 7, item 10), before they existed. This repository's history was condensed for publication. It shows that the committed code reproduces every committed number, but not, by itself, the order in which the code and the measurements were written. A level-1 run on a laptop takes minutes; the bootstrap analyses (10,000 resamples) can take up to about an hour.

**Cost of re-measuring.** One pass over the 1,024 recipient texts takes about 8 seconds on an A100. The main measurement grid is about 7,000 such passes, roughly \$16 at \$2.10 to \$2.50 per A100-hour; all measurements in the repository together come to roughly \$40.

## Where Every Number in the Post Comes From

Paths are relative to `results/grid/analysis/main/` unless they start with `results/`.

The **Command** column names the command that writes the file:

| Code | Command |
|---|---|
| FP | `figures-post` |
| PT | `post-tables` |
| A | `analyze` |
| C | `analyze --run control --compare-with main` |
| S9 | `analyze-s9` |
| C9 | `s9-checks` |
| F9 | `figures-s9` |
| S11 | `analyze-s11` |
| S12 | `analyze-s12` |
| L | a label-only table (see "What Regenerates What") |
| G | a GPU store read directly |

"Rung" is the code's name for an aggregation size:

| Rung | Size |
|---|---|
| `1` | 1 donor token |
| `T2` | 2 donor tokens |
| `T4` | 4 donor tokens |
| `2` | 8 donor tokens |
| `2a` | 16 donor tokens |
| `2b` | 32 donor tokens |
| `3` | 64 donor tokens |
| `4` | one whole donor text |
| `8` | the whole donor pool |

### The Figures

Every figure is drawn by `vpd-audit figures-post` into `results/post/` as a PNG. Each of the three data figures also has a CSV of exactly what it plots: the divergence, the rise it comes from, and 95 percent intervals.

| Post figure | File | Where its numbers come from |
|---|---|---|
| The aggregation curve (top of the post) | `results/post/aggregation_curve.png`, `.csv` | 1, 8, 16, 32, 64 tokens: `fig7_marginal_control.csv` (`U`, `P`, `M`) and the per-text stores of `results/grid/main/`; 2 and 4 tokens: `s12/s12_merge_E.csv` and `results/grid/main_s12/tier7/E__merge_sizes/`; one whole text: `union_E_D_unif_tau0.1_r0_excl_ctl-none.csv` and `ctl-plain.csv`, rung 4. Every interval is recomputed at 95 percent from the per-text stores, resampling texts with draws held fixed |
| The aggregation schematic | `results/post/aggregation_schematic.png` | an illustration |
| The deletion schematic | `results/post/delete_schematic.png` | an illustration |
| Similar donors | `results/post/similar_donors.png`, `.csv` | 1, 8 to 64 tokens and one text: `s9b/s9_run2_curves.csv` and `results/grid/main_s9/tier5/E_lab__same_domain/`; 2 and 4 tokens: `s12/s12_merge_E_lab.csv`. Intervals resample source documents (`s9/document_index.csv`). The own-explanation lines are computed from the same store |
| The code edit | `results/post/code_edit_panels.png`, `.csv` | `s12/s12_panels.csv` (`H`, `T` and their intervals, per panel and size), from `results/grid/main_s12/tier7/panel_*__panel_edit/`. Intervals resample documents (`s12/panel_document_index.csv`). Two variants are drawn with `--code-edit`: the labelled texts (`code_edit.png`; its numbers in `s12/code_edit_E_lab_document_intervals.csv`) and the labelled texts with ArXiv's bar from its panel (`code_edit_arxiv_panel.png`) |

### The Numbers in the Text

**TL;DR and the top figure's caption**

| Post | Value | File, and column or row | Command |
|---|---|---|---|
| 64 tokens' worth is about 4,500 components | 4,543.6 | `s9/figures/fig1_merge_curve.csv`, `pieces_switched_on_mean` | F9 |
| 0.80 nats at 64 tokens' worth | 0.7993 | same file, `divergence`, 64 tokens | F9 |
| 0.83 nats, the paper's 20-step adversary | 0.8280 | the paper's adversarial-attack table [1] | — |
| 1) the harm of aggregation is worse when inputs are similar | at 64 tokens: code into code +0.902 against general donors +0.608; prose into prose +0.621 against +0.455 | `s9b/s9_run2_curves.csv`, `rise`; the outcome in `s9b/s9_run2_verdict.csv` | S9 |
| 2) edits that heavily disrupt the model's predictions on code while mostly sparing the text chosen for protection | GitHub 0.666 and 3.342 against web text 0.026 and 0.213 and Wikipedia 0.025 and 0.208, at 256 and 1,007 components | `s12/s12_panels.csv`, `H` | S12 |
| 3) deleting all the components never labelled as needed moves the model 1.28 nats in KL from the original (the hard delete) | 1.2841 rise, 1.2847 absolute | `never_named_rung_8_cells.csv`, `unconditional`; `results/grid/main/verify/comparisons.md`, item 4 | A, G |
| lines would be close to zero with perfect faithfulness | 0.0115 | `level_cells.csv`, `mean_kl`, `main/E/ref/unmasked` | A |
| roughly 10,000 components counted as alive (average label above $10^{-6}$) | 9,959 | `results/grid/pre_reads/main/summary.json`, `n_alive_saved`; `vpd_audit/constants.py`, `ALIVE_THRESHOLD` | L |
| error bars: 95 percent bootstrap intervals over texts | | `results/post/aggregation_curve.csv`, `lo`, `hi`, `level` | FP |

**The schematics' captions**

| Post | Value | File, and column or row | Command |
|---|---|---|---|
| about 170, 1,100 and 4,500 components at 1, 8 and 64 tokens' worth | 169.0, 1,120.6, 4,543.6 | `s9/figures/fig5_matched_random_sets.csv`, `pieces_switched_on_mean` | F9 |
| deletions from 169 to 28,946 components | | `never_named_chain.csv`, `n_erased`, rungs 1 and 8 | A |

**Footnotes**

| Post | Value | File, and column or row | Command |
|---|---|---|---|
| 2: the all-or-nothing form raises KL above the own explanation by 0.036, 0.096 and 0.48 at 8, 16 and 64 tokens' worth, against 0.040, 0.10 and 0.46 | 0.0363, 0.0963, 0.4828; 0.0402, 0.1016, 0.4575 | `s11/s11_step2.csv`, `binary_excess`, `fractional_excess` | S11 |
| 2: at 64 tokens' worth, 0.79 against 0.80 nats from the original | 0.3114 + 0.4828 = 0.794; 0.7993 | `s11/s11_absolute.csv`, row `rounded_0`; `s9/figures/fig1_merge_curve.csv`, `divergence` | S11, F9 |

**Larger Aggregations Do More Harm**

| Post | Value | File, and column or row | Command |
|---|---|---|---|
| the own explanation, 0.34 nats | 0.3417 | `level_cells.csv`, `mean_kl`, `main/E/ref/importances` | A |
| one token: almost no effect | +0.0038 | `union_E_D_unif_tau0.1_r0_excl_ctl-none.csv`, `excess`, rung 1 | A |
| 16 tokens: 0.1 nats | +0.1016 | `union_E_D_unif_tau0.1_r0_excl_ctl-none__descriptive_rungs.csv`, `excess`, rung 2a | A |
| 64 tokens: 0.46 nats | +0.4575 | `union_E_D_unif_tau0.1_r0_excl_ctl-none.csv`, `excess`, rung 3 | A |
| 0.80 (0.34 + 0.46), both total KL divergence from the original model | 0.7993 = 0.3417 + 0.4575 | `s9/figures/fig1_merge_curve.csv`, `divergence` and `rise_over_own_explanation`, 64 tokens | F9 |
| uniform random components do almost no harm | −0.013 to +0.040 | `fig7_marginal_control.csv`, `P`; 2 and 4 tokens in `s12/s12_merge_E.csv`, line "uniform random" | A, S12 |
| frequency-matched components do much less harm at small sizes | −0.0033, −0.0038 at 1 and 8 tokens | `fig7_marginal_control.csv`, `M`; readings in `s7_marginal_readings.csv`; 2 and 4 tokens in `s12/s12_merge_E.csv`, and real minus matched in `s12_merge_E_real_minus_matched.csv` | A, S12 |
| about 75 percent overlap at 64 tokens | 0.732 | `results/grid/pre_reads/main/s7/marginal_overlap_by_rung.csv`, `overlap_mass_pooled`, rung 3 | L |
| about four fifths of the damage from usage frequency alone | 0.377 / 0.458 | `fig7_marginal_control.csv`, `M` / `U`, rung 3 | A |
| three quarters of token positions rise by more than 0.05 nats | 0.7605 | `s9/check_d_positions.csv`, `S_0.05`, curve 1, rung 3 | C9 |
| every recipient rises by more than 0.1 nats | 1.0 | `s9/check_d_texts.csv`, `share_texts_draw_averaged_above_0.1` | C9 |

**Similar Donors Do More Harm**

| Post | Value | File, and column or row | Command |
|---|---|---|---|
| own explanation 0.29 (code recipients) and 0.43 (prose) | 0.2926, 0.4286 | `s12/s12_merge_E_lab.csv`, `own_explanation`; `results/post/similar_donors.csv` | S12, FP |
| code donors barely harm prose through eight tokens' worth | +0.001 [−0.004, +0.007] at 8 tokens | `s12/s12_merge_E_lab.csv` (95 percent, documents), prose texts, code donors | S12 |
| prose donors harm code recipients much less | +0.028 on code, against +0.090 on prose, at 8 tokens | same file | S12 |
| 256 GitHub texts from 69 documents; 128 web and Wikipedia texts from 58 | | same file, `n_texts`, `n_documents` | S12 |
| code donors switch on fewer components at 2 to 64 tokens' worth | 311 against 399 at 2; 586 against 671 at 4; 975 against 1,121 at 8; 3,626 against 4,544 at 64 | `results/grid/pre_reads/main/s12/merge_sets.csv`, `n_on`; `s9/figures/fig7_within_one_kind.csv`, `pieces_switched_on_mean` | L, F9 |
| at 64 tokens' worth, 2.2 times what the general donors' curve predicts for that number of components | 0.902 observed, 0.415 predicted | `s9b/s9_run2_count_only.csv`, `observed`, `prediction`, `log_ratio`, switched mass, 64 tokens | S9 |
| self-aggregation: from 0.34 to 1.37 nats, every text harmed | rise 1.030; share 1.0 | `s9b/s9_run6_self_merge_rule.csv`, `rise`, `self_merge_kl`, `share_made_worse` | S9 |
| every text harmed more than when a different text's explanation is aggregated | 1.0 | `s9b/s9_run6_self_against_stranger.csv`, `share_of_texts_self_worse` | S9 |
| the closeness ladder: 0.57, 1.03, 1.40 at about the same count | 5,601, 5,250, 5,243 components | `s9/figures/fig8_closeness_ladder.csv`, `rise`, `pieces_switched_on_mean`; `s9b/s9_run6_ladder.csv` | F9, S9 |
| error bars: 95 percent bootstrap intervals over whole source documents | | `results/post/similar_donors.csv`, `lo`, `hi`, `level`; `s9/document_index.csv` | FP |

**Deleting Components Never Labelled as Needed**

| Post | Value | File, and column or row | Command |
|---|---|---|---|
| 9,966 of 38,912 ever labelled as needed; 28,946 never | | `union_E_D_unif_tau0.1_r0_excl_ctl-none.csv`, `n_on`, rung 8; `never_named_chain.csv`, `n_erased`, rung 8 | A |
| 169 never-needed components: 0.006 nats | 0.0060 | `never_named_chain.csv`, `D_mean`, rung 1 | A |
| the same number of random used components, in the same weight matrices: 1.12 nats, an average over eight samples of 38 to 226 components | 1.120; 38 to 226 | `never_named_chain.csv`, `alive_control_mean`, `n_per_draw`, rung 1; `s12/hard_delete_per_draw.csv` | A, PT |
| for the used components, the cost ranges from 0.11 to 3.0 nats across the samples | 0.115 to 2.98 | `s12/hard_delete_per_draw.csv`, `random_alive_rise`, from `results/grid/main/tier2/E/per_sequence.parquet` | PT |
| 1,121 deleted: 0.05; 4,544: 0.30; all: 1.28 | 0.0515, 0.297, 1.284 | `never_named_chain.csv`, `D_mean`, rungs 2, 3, 8 | A |
| turning them down only to their labels: essentially the same output damage, within 0.003 nats | 1.2876 against 1.2847 | `results/grid/main/verify/comparisons.md`, item 4; `level_cells.csv` | G, A |
| the 5,336 components labelled exactly zero: 0.31 nats, even on the recipient tokens where faithfulness guarantees no change | 0.313 [0.303, 0.324] | `never_named_rung_8_cells.csv`, row `tau0`, `d_hat_0` | A |
| used components at their labels: 0.34 deleted, 0.36 left on | 0.3417, 0.3615 | `level_cells.csv`, `mean_kl`, `s` = 0, `never_named_at` = labels / one | A |
| halfway: 0.21 against 0.19; three quarters: 0.25 against 0.13; fully on: from 0.01 to about the same 1.28 nats as the hard delete | 0.2126 / 0.1946; 0.2537 / 0.1258; 0.0115 / 1.2876 (the hard delete: 1.2847) | same file, `s` = 0.5, 0.75, 1; `results/grid/main/verify/comparisons.md`, item 4 | A, G |
| 201 heaviest: 0.072 nats; 201 lightest: 0.006 | 0.0724, 0.0064 | `fig6_ranked_pair.csv`, `D_mean`, `key` = weight_norm, `end` = top / bottom, rung 1 | A |
| lighter half 0.85, heavier half 1.17 | 0.845, 1.174 | same file, rung B50 | A |
| ranking by how often a label is above zero matters less | | same file, `key` = positive_count | A |

**Editing Out Code Behavior**

| Post | Value | File, and column or row | Command |
|---|---|---|---|
| one code token's ~200 components: over 11 nats | 197.9 components, 11.68 | `hard_zero_E_lab_D_code_tau0.1_ones_incl_ctl-none__tau_q0.1__all__donor_chain.csv`, `n_off`, `unconditional`, rung 1 | A |
| score at least 0.9, in at least 8 code texts: 1,007 components | | `results/grid/pre_reads/main/s7/code_leaning_groups.csv`, row `G_0.9`; the floors in `vpd_audit/code_leaning.py` | L |
| code, 256: 0.67; stand-ins 0.08 | 0.666 [0.611, 0.723]; 0.076 | `s12/s12_panels.csv`, `H`, `T`, `panel_Github` | S12 |
| web text and Wikipedia, 256: about 0.03; stand-ins about 0.17 | 0.026, 0.025; 0.171, 0.175 | same file, `panel_Pile_CC`, `panel_Wikipedia__en_` | S12 |
| code, 1,007: 3.34 (stand-ins 0.98) | 3.342, 0.977 | same file | S12 |
| web text and Wikipedia, 1,007: about 0.21 (stand-ins 1.37 to 1.59) | 0.213, 0.208; 1.371, 1.593 | same file | S12 |
| the stand-ins hurt prose six to eight times more | 1/ρ = 6.4 to 7.7 | same file, `rho`, the two prose panels | S12 |
| caption: stand-ins cost 0.08 to 0.18 at 256, 0.98 to 1.59 at 1,007 | | same file, `T`, all five panels | S12 |
| caption: 200 passages per kind, from 162 to 197 documents | | same file, `n_rows`, `n_documents`; `s12/panel_document_counts.csv` | S12 |
| StackExchange: 0.34 and 2.26 | 0.342, 2.262 | same file, `panel_StackExchange` | S12 |
| 7 of 16 sampled StackExchange texts code, 5 mixed | | `results/data/reader_labels/labels_labeled_sample.tsv` | — |
| footnote: StackExchange and GitHub texts look alike to the labels | 0.15 and 1.7 percent, reading *none* | `s9b/check_b_panels.csv`, pairs "code against StackExchange" and back, `share` | S9 |
| ArXiv: 0.26 and 2.68, more than twice the stand-ins' harm | 0.262 [0.233, 0.292], 2.675; ρ 2.15 [1.88, 2.43] and 2.48 [2.20, 2.76]; reading *keep* | `s12/s12_panels.csv`, `panel_ArXiv`, `H`, `rho`, `reading` | S12 |
| plain-text math problems and biomedical papers hurt no more than by the stand-ins | ρ 0.78 and 0.94 (DM Mathematics); 0.63 and 0.67 (PubMed Central) | `s12/s12_panels.csv`, `panel_DM_Mathematics`, `panel_PubMed_Central` | S12 |
| about 1 to 7 percent of non-code tokens covered by the guarantee at 256 components; none at 1,007 | 0.009, 0.012, 0.074, 0.058 (StackExchange, ArXiv, web text, Wikipedia); at 1,007, 0 except StackExchange, 0.00001 | `s12/panel_coverage.csv` (the labelled texts: `s7_code_leaning_conditional.csv`, 0.0465) | PT |

**Component Faithfulness Lacks Independence**

| Post | Value | File, and column or row | Command |
|---|---|---|---|
| one token's worth, ~170 components | 169.0 | `soft_erase_E_D_unif_tau0.1_r1_excl_ctl-none.csv`, `n_on`, rung 1 | A |
| soft deletion: 0.45, 0.74 and 0.36 nats; every text affected | 0.4477, 0.7416, 0.3615 | same file, `mean_kl`, rungs 1, 2, 8; `fraction_seq_above_X` | A |
| frequency-matched 0.42; uniform 0.08 | rise 0.405 and 0.070, plus 0.0115 | `s7_marginal_closure.csv`, the soft-deletion family, rung 1, `M`, `P`; `level_cells.csv`, `main/E/ref/unmasked` | A |

**How Big Is a Nat?**

| Post | Value | File, and column or row | Command |
|---|---|---|---|
| KL column 0.34, 0.80, 1.28, 0.39 | | `s9b/s9_yardstick_ratios.csv`, `divergence_on_E`, `divergence_to_the_primary_comparison_model` | S9 |
| top prediction changes 19, 38, 54, 26 percent; is the real next token 48, 48, 40, 31, 47 percent | | `s9b/s9_plain_terms_listed_masks.csv`, `change_rate`, `top_is_next`, `top_is_next_target` | S9 |
| on confident tokens: 2, 17 and 37 percent | | same file, `change_rate_confident` | S9 |
| twice as far; more than three times | 2.03, 3.26 | `s9b/s9_yardstick_ratios.csv`, `ratio` | S9 |

**Conclusion**

| Post | Value | File, and column or row | Command |
|---|---|---|---|
| similar inputs: harm after a few hundred components | +0.101 at 4 code tokens (585.6 components) | `s12/s12_merge_E_lab.csv`, code texts, code donors, `T4`; `results/grid/pre_reads/main/s12/merge_sets.csv`, `n_on`, D_code, `T4` | S12, L |
| other inputs: harm after about a thousand components | 1,227 | `union_E_D_unif_tau0.1_r0_excl_ctl-none__x_crossing.csv`, `interpolated_n`, row "curve" | A |
| deleting all never-needed components moves the model 1.28 nats from the original with the rest fully on, and turning them down only to their labels costs the same | 1.2847 (hard, absolute); 1.2876 (soft) | `results/grid/main/verify/comparisons.md`, item 4; `level_cells.csv`, `mean_kl`, `s` = 1, never-needed at labels | G, A |
| labels separate needed from unneeded components | 0.5 to 11 percent of the random used cost | `never_named_chain.csv`, `ratio_to_alive_control` | A |
| without the adversarial loss: four to seven times the harm at larger aggregations, at the same mask moved | 4.1, 5.6, 6.6 | `results/grid/analysis/control/compare_mass_matched_curve_1.csv`, `mean_this` / `mean_other`, bins 2 to 4 | C |
| the labels hold only as a joint configuration (also the opening of the Results) | the deletion's effect −0.020, +0.018, +0.128, +1.276 as the used components rise from their labels to fully on; the soft-deletion hump 0.45, 0.74, 0.36 | `level_cells.csv`, `footprint_labels_minus_one`; `soft_erase_E_D_unif_tau0.1_r1_excl_ctl-none.csv`, `mean_kl` | A |

The technical report (`REPORT.md`, section 8) gives the standing of each of these numbers, and which were read by a rule written down before the data.

## The Layout

### The Package, by Role

| Role | Modules |
|---|---|
| Environment, model and data | `env`, `constants`, `artifacts` (fetch and the key-free loader), `data` (the recipient, donor, labelled and panel sets), `roundtrip`, `codefilter`, `dry_sets`, `external_models` (Pythia as a comparison model) |
| Labels | `importances` (every component's label at every token), `donors` (the donor pools' label caches; the alive set) |
| Masks and the forward pass | `masks`, `metrics` (per-token KL and cross-entropy), `fingerprint` (an on-device digest of every applied mask), `reference` (the reference settings) |
| What is switched on or off | `sources` (donor positions and aggregation sizes, aggregation and deletion sets, the uniform and frequency-matched random sets), `code_leaning` (the code-leaning group and its usage-matched stand-ins), `weight_norms` |
| Cells and runs | `cells` (one masked pass over one text set at one point of the grid), `grid` (the runner), `results` (per-text stores and manifests), `tier5`, `tier6`, `tier7` (the inputs and checks of later groups of cells), `plain_terms`, `modal_app` (GPU launches), `cli` (`vpd-audit`) |
| Label-only tables | `pre_reads`, `s9_pre_reads`, `s9_panels`, `s12_labels` (including each panel passage's source document) |
| Checks of the harness | `smoke`, `acceptance`, `identities`, `verify`, `two_paths`, `level_check`, `h4`, `residual_matrix`, `residual_rank`, `short_runs`, `timing` |
| Statistics (pure functions, tested with planted answers) | `stats`, `stats_s7`, `stats_s9`, `stats_s12` |
| Analyses | `analysis`, `analysis_s7`, `analysis_s9`, `analysis_s11`, `analysis_s12`, `post_tables`, `s7_checks`, `s9_checks` |
| Figures | `figures_post` (the post's figures), and the earlier `figures`, `figures_s7`, `figures_s9` |

### What the Suffixes Mean

The audit ran in stages. Each stage added measurements through new code without changing what earlier code computes; tests hold every earlier cell's name and component set fixed. A suffix marks the stage that added a file. The numbers are labels, not counts.

| Stage | Adds |
|---|---|
| no suffix | the reproduction of the paper's reference numbers; the main grid of aggregations and deletions with uniform random comparisons |
| `s7` | the frequency-matched comparison; the code edit and its usage-matched stand-ins |
| `s9`, `s9b` | the document index of the labelled texts; the spread of the harm; similar donors; the self-aggregation; the plain-terms statistics; the comparison model; the source panels |
| `s11` | the all-or-nothing aggregation |
| `s12` | the 2- and 4-token aggregations; the code edit on the 200-passage panels, with each passage's source document |

A **tier** is a group of cells launched together:
- tier 1: the registered measurements;
- tier 2: their random comparisons;
- tier 3: sensitivity variants;
- tiers 4 to 7: the stages `s7`, `s9`, `s11`, `s12`.

### Code Names Against the Post's Terms

The post uses the paper's word, "aggregation". Some committed file names, columns, and table rows say "merge" instead, for example `s12_merge_E.csv` or the row "the 64-token merge". Both words name the same operation.

**Text sets**

| Code | Post |
|---|---|
| `E` | the 1,024 recipient texts |
| `D_unif` | the general donor texts |
| `E_lab` | the labelled recipients: 256 GitHub, and 64 each of web text, Wikipedia, StackExchange, ArXiv |
| `D_code`, `D_prose` | the code donors; the prose donors (web text and Wikipedia) |
| `panel_<Source>` | a 200-passage panel of one source |

**Operations (families)**

| Code | Post |
|---|---|
| `union` | the aggregation, with the recipient's own labels kept as they are |
| `rounded0_own_g` | the all-or-nothing aggregation |
| `self_union` | the self-aggregation |
| `partner_union` | aggregating one other whole text (the stranger, and the closeness ladder) |
| `soft_erase` | the soft delete |
| `never_named_hard` | the hard delete of never-needed components |
| `code_leaning_hard` | the code edit |

**Comparison sets**

| Code | Post |
|---|---|
| `ctl-plain` | uniform random components |
| `ctl-marginal` | frequency-matched random components |
| `ctl-usage` | the code edit's equally used stand-ins from the same weight matrices |

**Settings and sizes**

| Code | Post |
|---|---|
| `tau0.1` | a donor token needs a component if its label is above 0.1 |
| `r0` | elsewhere the recipient keeps its own labels |
| `r1`, `ones` | every other component fully on |
| `incl`, `excl` | the decomposition's small residual kept or left out |
| `k0` to `k7` | the eight random draws of donor tokens |
| rungs `1`, `T2`, `T4`, `2`, `2a`, `2b`, `3` | 1, 2, 4, 8, 16, 32, 64 donor tokens |
| rung `4` | one donor text |
| rungs `G256`, `G1007` | the code edit's 256 and 1,007 components |
| `excess`, `rise`, `H`, `D` | harm above the starting point, which each table names |

### The `results/` Tree

| Directory | Contents |
|---|---|
| `results/post/` | the post's figures, the three data figures with their CSVs, and a manifest |
| `results/grid/analysis/{main,control}/` | every analysis report (`report.md`), its tables, and `summary.json`; the stage directories `s7_checks/`, `s9/`, `s9b/`, `s11/`, `s12/`. `control/` is the decomposition trained without the adversarial loss |
| `results/grid/{main,control}/tier<t>/<set>[__<subset>]/` | the per-text stores: `per_sequence.parquet` (one row per cell and text), `cells.parquet` (each cell's coordinates, the hash of its component set, its counts), `run_manifest.json`, `marker.json`. Per-token arrays are not included, except the reference arrays the analyses read |
| `results/grid/main_s9/`, `main_s11/`, `main_s12/` | the later stages' stores, kept apart so that earlier analyses never read them |
| `results/grid/pre_reads/` | label-only tables computed from the label caches before any model run they constrain; each run is checked against them |
| `results/acceptance/` | the paper's reference numbers, reproduced |
| `results/identities/` | identity checks on the real model, including agreement with the authors' editing code |
| `results/data/` | set manifests and hashes, donor-cache manifests, and the source labels of sampled texts |
| `results/smoke/`, `results/smoke_fp/`, `results/short_runs/`, `results/dry_run/` | the harness checks the technical report cites |

## Licence and Acknowledgements

The code in this repository is released under the MIT licence (`LICENSE`). Eight lines of `vpd_audit/smoke.py` re-implement a function of the authors' `param-decomp` library (MIT, copyright Goodfire) to cross-check it; the attribution is in `NOTICE`.

| Item | Licence | How it is used here |
|---|---|---|
| [`goodfire-ai/param-decomp`](https://github.com/goodfire-ai/param-decomp) | MIT | linked as a submodule |
| the decomposition and model runs in WandB `goodfire/spd` | as published by the authors | downloaded by run id, never committed |
| [`danbraunai/pile-uncopyrighted-tok-shuffled`](https://huggingface.co/datasets/danbraunai/pile-uncopyrighted-tok-shuffled) | MIT | streamed; token ids cached locally only |
| [`monology/pile-uncopyrighted`](https://huggingface.co/datasets/monology/pile-uncopyrighted) | as stated on its card | the labelled texts; a few short decoded excerpts appear in one results table |
| [Pythia](https://github.com/EleutherAI/pythia) [2] | Apache 2.0 | downloaded at run time as a comparison model |

Thanks to the VPD authors for releasing their decomposition, code, and training runs.

## References

[1] L. Bushnaq, D. Braun, O. Clive-Griffin, B. Bussmann, N. Hu, M. Ivanitskiy, L. Linsefors, and L. Sharkey. Interpreting Language Model Parameters (adVersarial Parameter Decomposition). Goodfire, May 2026. https://www.goodfire.ai/research/interpreting-lm-parameters

[2] S. Biderman et al. Pythia: A Suite for Analyzing Large Language Models Across Training and Scaling. ICML 2023. arXiv:2304.01373.
