# Auditing the Released VPD Decomposition: Technical Report

This report carries the detail behind the post *Do VPD's Explanations Aggregate? An Audit of the Released Decomposition*: exact definitions, every measurement with its interval, the statistics as used, the checks that make the code trustworthy, and the standing of every number. Its sections follow the post's. Every quotation of the paper is exact, and every number is cited by the committed file it comes from. A path beginning with `results/` is relative to the repository root. A bare file name is under `results/grid/analysis/main/`, or under the directory named in the nearest earlier citation of its section. The README's layout section explains how files and cells are named.

## 1. What Was Tested, and How to Read This Report

adVersarial Parameter Decomposition (VPD) [1] rewrites a model's weight matrices as sums of many rank-one *components* and trains a second network that labels every component, at every token of every input, with how much it is needed there. The paper's central property, *mechanistic faithfulness*, is that "Every subset of components that includes the causally important components is sufficient to compute the network's output on any particular input" [1]. In mask terms: any setting of the components that keeps each one at or above its label should leave the output unchanged.

The paper names two uses of the labels, "to understand or edit a given model" [1], and grounds its standard for robustness in them. The audit tests the released decomposition under masks built for those two uses:
- **aggregating** the explanations of several inputs, as one would to find the components behind a behaviour;
- **deleting** components from the model, as one would to edit it.

It uses the paper's own released checkpoint, the paper's own measure of output change, and masks the paper's definition permits wherever the question is faithfulness. Everything here concerns one decomposition of one small model. The authors' repository points to a newer, unpublished training recipe, to which none of this was applied.

**Standing.** The audit's original plan fixed its tests, their pass-or-fail rules, and their tolerances before any of its data existed. Later experiments were designed after earlier results had pointed to them. Each result carries one of four standings:
- **Registered verdict:** a pass-or-fail rule in the original plan, fixed before any of the audit's data existed, and read by analysis code committed before any result was read.
- **Registered description:** a quantity named in the original plan, with no rule attached.
- **Readings fixed before the run:** an experiment designed after earlier results had been seen, whose possible readings were written down before it ran. For most such experiments the analysis code was also committed before the run, and the sections say where.
- **Descriptive:** read by no rule.

Section 8 tabulates the standing of every number in the post.

## 2. Setup

### 2.1 The Decomposition

The target model is the paper's four-layer decoder-only transformer: residual width 768, MLP width 3,072, six attention heads, context 512 tokens, about 67 million parameters. VPD decomposes 24 of its weight matrices: the query, key, value, and output projections of attention, and the two MLP matrices, in each of the four layers. Embeddings, normalization layers, and biases are left as they are. Each matrix $W^l$ is written as a sum of rank-one components plus a *residual* $\Delta^l$, the part of the weights the components leave over:

$$
W^l = \sum_{c=1}^{C_l} \vec U^l_c\, (\vec V^l_c)^{\top} + \Delta^l .
$$

There are 38,912 components in all. A *mask* sets, at every token, one number in $[0, 1]$ per component and one for each matrix's residual. With $h$ the input to matrix $l$ at a token, the masked model computes that matrix's output as

$$
\sum_{c} m_c\, \langle h, \vec V^l_c \rangle\, \vec U^l_c \;+\; m_{\Delta}\, \Delta^l h .
$$

A mask value of 1 leaves a component's contribution unchanged, 0 removes it, and a value in between scales it. With every component and residual mask at 1, the masked model is the original model up to floating point.

### 2.2 The Labels

The decomposition's labelling network assigns every component $c$ a *label* $g_{t,c} \in [0, 1]$ at every token $t$ of a text: the lowest level to which the component can be turned down at that token without changing the output. The paper calls it the *causal importance*. The labels are computed once, from the original model on the unmasked text, and never recomputed under a mask. The labelling network reads the whole text, so a label at one token can depend on later tokens.

- A mask is **permitted** if every component's mask is at or above its label at every token: $m_{t,c} \ge g_{t,c}$. Faithfulness says every permitted mask leaves the output unchanged.
- A text's **own explanation** is the mask that sets every component to its label, $m = g$.
- A component is **labelled as needed** at a token if its label there is above 0.1, the cut-off the paper uses to filter "low-CI noise" (CI being its abbreviation for causal importance) [1]. A token's explanation, as a set, is the components it labels as needed. Where a result instead uses "label above 0", it says so.
- A component is **alive**, in the paper's sense, if its mean label over the donor texts (section 2.4) exceeds $10^{-6}$. On our donor texts 9,959 of the 38,912 are alive, against the paper's 9,972 (`results/grid/pre_reads/main/summary.json`).
- **The training masks.** The paper trains the decomposition under random masks that set each component, at every token, uniformly at random between its label and 1. These masks are the second starting point of some aggregation tests below.

On a typical token about 205 components have a label above 0 (203.4 on our recipient texts, against the paper's 205; `results/acceptance/checks.txt`, check 4).

### 2.3 Output Harm

**Output harm** is the KL divergence of the masked model's next-token distribution from the original model's, in nats:

$$
\mathrm{KL}_{t} = \sum_{v} P_t(v)\,\big[\log P_t(v) - \log Q_t(v)\big],
$$

with $P_t$ the original model's distribution at token $t$ and $Q_t$ the masked model's. It is averaged over a text's 512 tokens and then over texts. This is the direction the authors' own code computes, and the quantity their training loss sums. It needs no labels of the text: it measures how far the masked model's predictions move from the original's, not how well it predicts the true next token (section 5 translates it into terms that are easier to picture). Logits are computed in bfloat16 and the divergence in float32.

Three reference points recur:
- **the complete decomposition**, every component at 1 and the residual left out: 0.0115 nats from the original model. The residual's absence is the whole of this gap (`results/grid/analysis/main/level_cells.csv`, `mean_kl`, row `main/E/ref/unmasked`);
- **the complete model**, every component at 1 and the residual included: 0.0006 nats, which is bfloat16 rounding; in float32 it is $-1.6 \times 10^{-9}$ (`results/acceptance/conditions_main_bf16.csv` and `conditions_main_fp32.csv`, `kl_mean`, row `unmasked_delta`);
- **a text's own explanation**, every component at its label and the residual left out: 0.342 nats (row `main/E/ref/importances`).

A **rise** is a mask's output harm minus the output harm of its starting point, paired within each text. Aggregations are reported as rises over the recipient's own explanation, and deletions as rises over the complete model, with the reference named each time. Where the post gives a total, the report gives both.

### 2.4 The Texts

| Set | Name in the tables | What it is | Size |
|---|---|---|---|
| Recipient texts | `E` | rows 0 to 1,023 of the validation split of the authors' tokenized Pile, read in stream order | 1,024 texts of 512 tokens |
| General donor texts | `D_unif` | rows 1,024 to 2,047 of the same split; disjoint from the recipients | 1,024 texts; 524,288 token positions |
| Code and prose donor pools | `D_code`, `D_prose` | from the labelled Pile validation file: 512 GitHub texts (code) and 256 Pile-CC plus 256 Wikipedia texts (prose) | 262,144 positions each |
| Labelled recipient texts | `E_lab` | from the same file, disjoint documents: 256 GitHub texts and 64 each from StackExchange, ArXiv, Pile-CC (web text), and Wikipedia | 512 texts |
| Panels | `panel_<source>` | from the same file, disjoint documents again: 200 random 512-token windows per source | 200 texts per source |

The authors' validation split was carved from the Pile's training data, and their tokenized copy is shuffled at the row level, so each recipient and general donor text is treated as an independent sample.

The labelled Pile file records each document's source. Its documents were split at random, source by source, into three disjoint parts:
- **part A:** the code and prose donor pools, and the pools used to choose components for the code edit;
- **part B:** the labelled recipient texts;
- **part C:** the panels.

In parts A and B the texts are the first consecutive 512-token windows of the part's token stream, so one document can span several texts. The 256 GitHub recipients come from 69 documents, and the 64 Pile-CC, Wikipedia, StackExchange, and ArXiv recipients from 25, 33, 44, and 3 documents (`results/grid/analysis/main/s9/document_counts.csv`). Every interval on the labelled texts therefore resamples documents, not texts (section 6). The panels are random windows of part C, whose source documents are recovered from the token stream (section 4.2.5).

The data manifest records every pairwise intersection among these sets as zero (`results/data/labeled_manifest.json`). Ten of the 256 GitHub recipients share an exact 50-token window with a code donor text; the ones inspected are licence headers (`results/grid/analysis/main/s9/near_duplicate_pairs.csv`).

**Reader labels.** Each recipient and general donor text also carries a label of *code*, *prose*, *mixed*, or *other*. These labels were assigned by language-model readers following a fixed written rubric (`results/data/reader_labels/rubric.md`), each reader seeing only the rubric and the decoded text, and they were frozen before any measurement that uses them.
- **Agreement:** on 200 texts read twice by independent readers, the two labels agree exactly on 95 percent, and on every text for code against not-code.
- **Blinded check:** a sample of 256 labelled texts, read under anonymous keys so that readers could not see their source (`anon_key` in `labels_labeled_sample.tsv`), confirms the source labels. For example, 58 of 64 GitHub donor texts read as code, and the other six as *prose* or *other*.

The label files, with the counts, are under `results/data/reader_labels/` (`summary.json`, `labels_labeled_sample.tsv`).

## 3. Aggregating Explanations

### 3.1 The Claim Under Test

The paper states the property this part tests. If two inputs are explained by subsets $S_1$ and $S_2$ of the components, "a parameter vector formed by the union of both subsets $\sum_{i\in S_1 \cup S_2} \theta_i$ will still compute approximately the same output on both datapoints". It calls this "one of the central promises of ablation-based parameter decomposition". It sketches combining explanations "first into explanations of the model's behavior on narrow sub-distributions (such as bracket closing or pronoun prediction)", and it says that "It remains unclear whether our current decomposition is sufficiently adversarially robust for this purpose" [1].

**Recipients and donors.**
- A *recipient* is a text of 512 tokens on which output harm is measured: the 1,024 recipient texts of section 2.4.
- A *donor token* is one token position of a *donor text*: the 1,024 general donor texts, disjoint from the recipients, 524,288 positions in all.
- A donor token's *explanation* is the set of components it labels as needed (label above 0.1).
- For each of eight *draws*, the donor positions are put in a seeded random order, and an aggregation of $k$ donor tokens takes the first $k$. The donor sets therefore nest: the 8-token set of a draw contains its 1-token set.
- An aggregation of one *donor text* takes all 512 positions of that text.

**Tokens' worth.** An aggregation of $k$ donor tokens switches on the union of their explanations. Its size in components is the mean over the eight draws of the union's size (`results/grid/analysis/main/union_E_D_unif_tau0.1_r0_excl_ctl-none.csv`, `n_on`):

| donor tokens | 1 | 8 | 16 | 32 | 64 | one text | 64 texts | whole pool |
|---|---|---|---|---|---|---|---|---|
| components | 169 | 1,121 | 1,974 | 3,199 | 4,544 | 4,890 | 9,659 | 9,966 |

At 2 and 4 donor tokens the aggregation switches on 399 and 671 components on average (120 to 804 and 524 to 1,067 over the draws; `results/grid/pre_reads/main/s12/merge_sets.csv`). These two sizes were measured after the others, with the same donor draws: their donor tokens are the first 2 and 4 of each draw's existing order, so every draw's sets nest from 1 to 8 tokens.

Tokens share many of the components they need, so the count grows much more slowly than the number of tokens.

### 3.2 The Aggregation, in Two Forms

*The fractional form, reported throughout.* At every token of the recipient, each component keeps the recipient's own label, except that every component in the donors' union is set fully on (1). The residual is held at 0. The aggregation's start, with no donors, is the recipient's own explanation, which sits at **0.342** nats from the original model.

*The all-or-nothing form, as the paper states the property.* The recipient's own explanation is first rounded: every component with a label above 0 at a token is set to 1, and every other to 0. Then the donors' union is switched on. Its start, the rounded explanation, sits at **0.311** nats (`results/grid/analysis/main/s11/s11_absolute.csv`).

Both forms keep every mask at or above its label, so both are permitted masks, and faithfulness says neither should change the output. *Worked example*: one recipient token, five components, and a donor union that contains $c_4$.

| | $c_1$ | $c_2$ | $c_3$ | $c_4$ | $c_5$ |
|---|---|---|---|---|---|
| recipient's labels | 1.0 | 0.7 | 0.05 | 0.0 | 0.0 |
| fractional start (own labels) | 1.0 | 0.7 | 0.05 | 0.0 | 0.0 |
| fractional aggregation | 1.0 | 0.7 | 0.05 | **1.0** | 0.0 |
| all-or-nothing start (labels above 0 set to 1) | 1 | 1 | 1 | 0 | 0 |
| all-or-nothing aggregation | 1 | 1 | 1 | **1** | 0 |

**The two forms agree.** *Standing: readings fixed before the run, with the analysis code committed first; the test was designed after the main aggregation result.* The all-or-nothing form was to *fail* if its rise at 8 tokens was positive on all eight draws with an interval above zero. If it failed, outcome A held when its rise at every size lay within a factor of two of the fractional form's. The run returned **A** (`results/grid/analysis/main/s11/s11_step1.csv`, `s11_step2.csv`, `s11_verdict.csv`; text bootstrap with the draws held fixed, at level $1 - 0.05/4$):

| aggregation | all-or-nothing rise | fractional rise | all-or-nothing output harm | fractional output harm |
|---|---|---|---|---|
| 8 tokens | 0.036 [0.035, 0.037] | 0.040 | 0.347 | 0.382 |
| 16 tokens | 0.096 [0.094, 0.099] | 0.102 | 0.407 | 0.444 |
| 64 tokens | 0.483 [0.471, 0.495] | 0.458 | 0.794 | 0.799 |
| the recipient aggregated with itself (section 3.5) | 1.060 [1.034, 1.086] | 1.030 | 1.371 | 1.371 |

The two forms' rises are measured from different starts, 0.311 and 0.342, but the forms end at nearly the same output harm. All eight draws rise at every size in both forms. A variant that rounds the recipient's labels at 0.1, which is not a permitted mask, gives rises of 0.036, 0.096, and 0.475 (`s11_secondary.csv`).

### 3.3 Larger Aggregations Do More Harm: The Registered Test

*Standing: registered verdict.*

**The rule** (section 6 gives the statistics). An aggregation's rise is the mean over the eight draws and the 1,024 recipients.
- *Detected:* the rise's interval, corrected over the aggregations of its curve, lies above zero, and at least seven of the eight per-draw means are positive.
- *Material:* detected, and the interval's lower end also exceeds $X = 0.05$ nats.
- *Fails:* the curve fails if any aggregation is material.

$X$ is the size of the difference the paper reports between two of its own mask conditions: its table's importances-as-masks and rounded-at-zero rows differ by 0.05 nats of cross-entropy.

**The outcome: the curve fails** (`union_E_D_unif_tau0.1_r0_excl_ctl-none.csv`, `excess`, `interval`, `fraction_seq_above_X`; the 16- and 32-token rows from `..._ctl-none__descriptive_rungs.csv`):

| donor tokens | components | rise | interval | output harm | recipients above $X$ |
|---|---|---|---|---|---|
| 1 | 169 | +0.0038 | [+0.0033, +0.0042] | 0.346 | 0% |
| 8 | 1,121 | +0.0402 | [+0.0383, +0.0420] | 0.382 | 25.5% |
| 16 (added later; descriptive) | 1,974 | +0.102 | [+0.099, +0.104], 95% | 0.444 | 95.7% |
| 32 (added later; descriptive) | 3,199 | +0.231 | [+0.226, +0.237], 95% | 0.573 | 100% |
| 64 | 4,544 | +0.458 | [+0.444, +0.472] | 0.799 | 100% |
| one text | 4,890 | +0.488 | [+0.472, +0.504] | 0.829 | 100% |
| 64 texts | 9,659 | +0.954 | [+0.927, +0.981] | 1.295 | 100% |
| whole pool | 9,966 | +0.946 | [+0.919, +0.974] | 1.288 | 100% |

Two sizes added after the fact, descriptive, with 95% intervals (`results/grid/analysis/main/s12/s12_merge_E.csv`):

| donor tokens | components | rise | interval | output harm | draws positive |
|---|---|---|---|---|---|
| 2 | 399 | +0.0101 | [+0.0094, +0.0107], 95% | 0.352 | 8 of 8 |
| 4 | 671 | +0.0190 | [+0.0181, +0.0200], 95% | 0.361 | 8 of 8 |

They sit between the 1- and 8-token points, and the rise grows steadily with size from the first donor token on.

- The mean rise crosses $X$ at about 1,230 components, between 8 and 16 donor tokens, by log-linear interpolation (`union_E_D_unif_tau0.1_r0_excl_ctl-none__x_crossing.csv`).
- 64 tokens is the first registered aggregation the rule calls material. There the mean rise is nine times $X$, and every recipient is above $X$.
- Every one of the eight draws rises at every size.
- The curve also fails under the second registered starting point, the training masks of section 2.2, on every draw.
- The widest interval is about ±0.027 nats, so the test could resolve what it needed to.

**The paper's 20-step adversary as a reference.** *Standing: an outside number, quoted and not re-measured.* The paper reports a KL divergence of 0.8280 to the target model under adversarial masks after 20 optimization steps, "calculated across a batch of $128$ of sequence length $512$ drawn from the evaluation set" [1]. The 64-token aggregation reaches 0.799, with no search.

What the two share:
- both keep every component mask at or above its label;
- both are scored as KL divergence to the original model, averaged over positions.

What they do not share:
- **Search.** The adversary maximizes the divergence over 20 steps; an aggregation performs no search.
- **The scope of a mask.** The adversary's masks are shared across a batch, "sharing the same source for each subcomponent across the batch" [1]; an aggregation sets masks per recipient from other texts' explanations.
- **The residual.** The adversary also moves the residual's mask; the paper says the residual's sources "are treated identically to those used for the regular subcomponents, i.e. they are also adversarially optimized" [1]. Aggregations hold the residual at 0.
- **The texts.** The adversary was run on 128 of the paper's evaluation sequences. Aggregations are scored on 1,024 recipients from the same validation split, which are not shown to be the same rows.

The comparison says that an aggregation reaches the adversary's scale, not that the two measure the same thing.

**How widely the harm is spread.** *Standing: the one number that owns the word "most" was fixed before the per-position data were read; the rest are descriptive.* $S(\epsilon)$ is the share of recipient positions whose rise exceeds $\epsilon$. The rule read *on most positions* if the interval of $S(0.05)$ at 64 tokens had its lower end at 0.50 or above. It is 0.7605 [0.757, 0.764] with the draws held fixed, and 0.735 to 0.789 across the eight draws. The breakdown by size, per aggregation with draws not averaged (`results/grid/analysis/main/s9/check_d_positions.csv`):

| aggregation | positions rising > 0.05 | > 0.1 | > 0.5 | > 1 | falling > 0.05 |
|---|---|---|---|---|---|
| 1 token | 9.0% | 3.7% | 0.1% | 0.0% | 6.8% |
| 8 tokens | 29.7% | 18.3% | 1.9% | 0.4% | 15.8% |
| 16 tokens | 44.9% | 32.4% | 5.6% | 1.4% | 14.6% |
| 32 tokens | 61.1% | 49.8% | 14.4% | 5.0% | 11.0% |
| 64 tokens | 76.1% | 67.3% | 28.5% | 12.9% | 6.6% |
| one text | 68.4% | 60.0% | 28.5% | 14.6% | 6.9% |
| uniform random set, 64 tokens' worth | 36.0% | 23.8% | 2.2% | 0.3% | 22.5% |

At 64 tokens every recipient's mean rise exceeds 0.1, and 1,023 of 1,024 exceed 0.2 (`check_d_texts.csv`). A uniform random set of the same size reshuffles the output: 36% of positions up, 23% down, a net +0.04. A real aggregation pushes one way. The paper's hope that failures may "only apply to a few data points" [1] does not describe this.

### 3.4 The Two Random Comparisons, and What Each Can Separate

*Standing: the uniform comparison is a registered description. The frequency-matched comparison, its statistic, and its four readings were fixed, with its analysis code committed, before it ran.*

**Uniform random components.** In each weight matrix, as many components as the real union contains, drawn uniformly from the 9,959 alive components; eight draws, nested across sizes.

**Frequency-matched random components.** A random donor token labels component $c$ as needed with probability $u_c$, its usage over the donor tokens. A union of $k$ independent donor tokens therefore contains $c$ with probability

$$
p_c(k) = 1 - (1 - u_c)^k .
$$

The frequency-matched set keeps every component's inclusion probability $p_c(k)$ and destroys only which components appear *together*. Every one-at-a-time property of its members (weight, usage, amount of mask moved) therefore matches the real union's in expectation. It is drawn per matrix as the first $n$ arrivals of seeded exponential clocks $T_c = Z_c / \lambda_c$, with $\lambda_c = -\ln(1 - u_c)$ and $Z_c \sim \mathrm{Exp}(1)$, where $n$ is the real union's count in that matrix. Since $P(T_c \le k) = p_c(k)$, one order per draw and matrix serves every size, and the sets nest.

*Worked example.* A matrix has four candidates with usage 0.9, 0.3, 0.05, and 0.01, and seeded $Z$ of 0.5, 1.2, 0.3, and 2.0. Their rates are $\lambda = 2.30, 0.357, 0.0513, 0.0101$, so the arrival times are 0.22, 3.36, 5.85, and 199. If the real union holds two of this matrix's components, the matched set is the first two to arrive. Under the uniform draw, any two would be equally likely, which is why the uniform set is light and little used.

**Results** (`results/grid/analysis/main/fig7_marginal_control.csv`, `U`, `P`, `M`):

| donor tokens | real union | uniform random | frequency-matched |
|---|---|---|---|
| 1 | +0.0038 | −0.0021 | −0.0033 [−0.0036, −0.0031] |
| 8 | +0.0402 | −0.0110 | −0.0038 [−0.0047, −0.0029] |
| 16 | +0.102 | −0.013 | +0.025 |
| 32 | +0.231 | −0.001 | +0.137 |
| 64 | +0.458 | +0.040 | +0.377 |

Added after the fact, descriptive, 95% intervals (`s12/s12_merge_E.csv`; per draw in `s12_merge_E_per_draw.csv`):

| donor tokens | real aggregation | uniform random | frequency-matched |
|---|---|---|---|
| 2 | +0.0101 | −0.0043 | −0.0044 [−0.0048, −0.0040] |
| 4 | +0.0190 | −0.0074 | −0.0063 [−0.0068, −0.0058] |

The real aggregation exceeds the frequency-matched set on all eight draws at both sizes (by +0.015 and +0.025, `s12_merge_E_real_minus_matched.csv`), continuing the pattern of 1 and 8 tokens. At these sizes the two random sets are nearly equal.

- **The uniform comparison separates *how many* from *which*.** At 1 and 8 tokens the real union raises the harm while as many uniform random components lower it slightly; at 64 tokens (4,544 components) the union's rise is 11.5 times the uniform set's. The uniform set's small improvement is consistent with the labels being slightly low everywhere (section 4.1): raising a component the recipient uses at a fraction helps slightly. The uniform comparison cannot say whether a real union harms because of its members' kind (heavier and much more used) or because of their combination.
- **The frequency-matched comparison separates *kind* from *combination*, but only at 1 and 8 donor tokens.** The rule reads a size only if the matched set shares at most a third of the real union's moved mask, and the label-only tables settled before the run that this leaves 1 and 8 tokens. The statistic $\psi$ is the share of the real-minus-uniform gap that matching closes, beyond what shared members alone would close; the rule reads *combination* if its interval lies below 1/3 with the real union above the matched set on at least seven of eight draws. It returned **combination**: $\psi = -0.30$ and $-0.02$ (`results/grid/analysis/main/s7_marginal_closure.csv`). A second, independently seeded matched set agrees. At the sizes where the harm begins, sets matched in every one-at-a-time property do no harm in the mean.
- **What it cannot separate.** From 16 tokens on, the matched and real sets share 43% to 73% of their moved mask (`results/grid/pre_reads/main/s7/marginal_overlap_by_rung.csv`, `overlap_mass_pooled`), and the matched set loses its grip. A component used at 4% of positions enters a 64-token matched set with probability 0.9, so real combinations are completed by chance. The large-aggregation numbers are therefore descriptions: by 64 tokens a frequency-matched set, which needs no donor texts at all, does about four fifths of the real union's harm.
- The reading does not identify *what* about the combination harms. Section 3.5 bears on it.

Under the random masks the decomposition was trained with, instead of the recipient's own labels, the uniform set does almost nothing (+0.0003 and +0.0051 at 1 and 8 tokens). There the matched set does 31% and 54% of the real union's harm at 1 and 8 tokens, and 93% at 64. The rule read *combination* at 1 token and neither reading at 8, where the kind of component accounts for about two fifths of the gap ($\psi = 0.39$).

### 3.5 Similar Donors Do More Harm

*Standing: readings fixed before the run, with the analysis code committed first, for the design's outcome, the match ratio, the count-only prediction, the self-aggregation, and the ladder. The experiment was designed after the main aggregation result.*

**Design.** Three donor pools, each an *arm* of the design, are aggregated into the 512 labelled recipients, in the fractional form, with eight draws:
- **C**, code donors: 512 GitHub texts;
- **U**, general donors: the pool of the main aggregation curve (section 3.3), with the same eight draws, its sets asserted equal by hash;
- **P**, prose donors: 256 Pile-CC and 256 Wikipedia texts.

Recipients are read on the *code stratum* (256 GitHub texts from 69 documents) and the *prose stratum* (128 Pile-CC and Wikipedia texts from 58 documents). Intervals resample documents, at level $1 - 0.05/10$. The recipients' own explanations sit at 0.293 nats on code and 0.429 on prose.

**Components switched on**, from label-only tables fixed before the run (`results/grid/pre_reads/main/s9/summary.md`; per draw in `merge_sets.csv`):

| donor tokens | code donors (range over draws) | general donors | prose donors |
|---|---|---|---|
| 1 | 198 (72 to 364) | 169 | 174 |
| 8 | 975 (799 to 1,153) | 1,121 | 1,127 |
| 16 | 1,552 | 1,974 | 2,011 |
| 64 | 3,626 | 4,544 | 3,975 |
| one text | 5,156 | 4,890 | 5,699 |

From 8 to 64 tokens, code donors switch on fewer components than general donors. At 1 token and at a whole text they switch on more.

**Rises** (`results/grid/analysis/main/s9b/s9_run2_curves.csv`):

| donor tokens | C into code | U into code | P into code | C into prose | U into prose | P into prose |
|---|---|---|---|---|---|---|
| 1 | +0.019 [0.016, 0.021] | +0.007 | +0.003 | −0.002 | +0.003 | +0.009 |
| 8 | **+0.191** [0.152, 0.223] | +0.057 [0.048, 0.072] | +0.028 [0.018, 0.046] | +0.001 [−0.006, 0.009] | +0.032 | **+0.090** |
| 16 | +0.329 | **+0.128** | +0.069 | +0.025 | **+0.098** | +0.210 |
| 32 | +0.622 [0.532, 0.714] | +0.339 [0.285, 0.429] | **+0.142** [0.094, 0.225] | **+0.105** [0.081, 0.131] | +0.226 [0.202, 0.254] | +0.395 [0.361, 0.432] |
| 64 | +0.902 [0.770, 1.033] | +0.608 [0.537, 0.694] | +0.263 | +0.240 | +0.455 | +0.621 |
| one text | +0.993 | +0.635 | +0.433 | +0.477 | +0.571 | +0.808 |
| 64 texts | +1.288 | +1.276 | +1.244 | +0.851 | +0.842 | +0.857 |

Bold marks the first material size of each line that becomes material.

Added after the fact, descriptive, 95% intervals over documents (`results/grid/analysis/main/s12/s12_merge_E_lab.csv`):

| donor tokens | C into code | U into code | P into code | C into prose | U into prose | P into prose |
|---|---|---|---|---|---|---|
| 2 | +0.043 [0.039, 0.047] | +0.020 [0.013, 0.031] | +0.008 [0.006, 0.010] | −0.002 [−0.005, +0.000] | +0.009 [0.007, 0.011] | +0.016 [0.014, 0.017] |
| 4 | +0.101 [0.088, 0.113] | +0.032 [0.025, 0.043] | +0.011 [0.008, 0.016] | −0.005 [−0.008, −0.001] | +0.013 [0.010, 0.015] | +0.037 [0.034, 0.039] |

The ordering of the three pools holds at both sizes on both strata. Code donors into code recipients already exceed 0.05 nats at 4 donor tokens (about 590 components), and code donors slightly *lower* the divergence of prose recipients there.

**The outcome: same-kind donors fail first.** The rule was gated on arm U failing on the code stratum, which it does. Code donors into code recipients are material from 8 tokens, general donors from 16. The mirror holds on prose: prose donors are material from 8 tokens, general donors from 16. Code donors do nothing detectable to prose recipients at 1 or 8 tokens, while prose donors harm code recipients measurably at 8 tokens (+0.028), about a third of what they do to prose. Same-kind donors do the harm; other-kind donors do less. By 64 texts every pool has switched on nearly all it ever will, and the three arms meet.

**The match ratio.** It cancels both a pool's overall harshness and a recipient's overall fragility. With $\hat e(D \to S)$ the mean rise of pool $D$ on stratum $S$:

$$
r_{\mathrm{code}} = \frac{\hat e(C \to \mathrm{code})}{\hat e(P \to \mathrm{code})}, \qquad
r_{\mathrm{prose}} = \frac{\hat e(P \to \mathrm{prose})}{\hat e(C \to \mathrm{prose})}, \qquad
R = \sqrt{r_{\mathrm{code}}\, r_{\mathrm{prose}}} .
$$

A pool that is $h$ times as harsh everywhere multiplies one ratio by $h$ and the other by $1/h$, so it cancels in $R$. The readings: *matching helps* if $R$'s interval lies below 0.8; *closer is worse* if it lies above 1.25; *no material help* in between. $R$ was read at 8 tokens, 64 tokens, and 64 texts, and only where all four rises had intervals above zero.

*Worked example.* Suppose the rises were 0.045 (C into code), 0.060 (P into code), 0.015 (P into prose), and 0.045 (C into prose). Then $r_{\mathrm{code}} = 0.75$, $r_{\mathrm{prose}} = 0.33$, and $R = 0.50$: matching halves the harm, even though code donors are 1.5 times as harsh everywhere. The code stratum alone would have hidden that.

**Result** (`s9_run2_match_ratio.csv`):
- At 64 tokens $R = 2.98$ [2.34, 3.78], with $r_{\mathrm{code}} = 3.43$ and $r_{\mathrm{prose}} = 2.59$: *closer is worse*, on both sides.
- At 64 texts $R = 1.021$ [1.014, 1.028]: *no material help*, the saturated regime.
- At 8 tokens $R$ is withheld by the rule, because code donors' rise on prose recipients includes zero.

**The count-only prediction.** Is the extra harm just the amount switched on? For each draw of arm C, arm U's own curve predicts the rise at that draw's amount of mask moved. The curve is the rise against mask moved, interpolated log-log through its ten sizes and never extrapolated. The reading was *above* if the interval of $\log(\text{observed}/\text{predicted})$ lies above zero. At 64 tokens, observed 0.902 against predicted 0.415 gives a log ratio of 0.775 [0.528, 0.981], a factor of 2.2 (`s9_run2_count_only.csv`). The same holds when the prediction uses the count of components (0.766 [0.522, 0.969]). So the factor of 2.2 is at equal amounts switched on. Without that matching, code donors cost code recipients about 1.5 times what general donors do at 64 tokens (0.902 against 0.608).

**The self-aggregation.** The self-aggregation keeps a recipient's labels and switches on every component that any of its own 512 tokens labels as needed, about 5,550 components (`s9_run6_self_merge_rule.csv`, `s9_run6_self_against_stranger.csv`):
- It is material on all 1,024 recipients: rise +1.030 [1.005, 1.056], output harm 1.37. Every recipient is made worse, every one by more than 0.2, with a median rise of 0.95.
- *Self against stranger.* Each recipient also received other recipients' sets, by a seeded rotation under which both arms hold the identical collection of sets, so that component counts match. A recipient's own tokens cost it 0.455 [0.436, 0.475] more than a stranger's set, positive on every one of the 1,024.

**The closeness ladder.** Rises on the 512 labelled recipients, per source, with partners drawn within the recipient's own source, at level $1 - 0.05/5$ over documents (`s9_run6_ladder.csv`):

| source (documents) | a general text | another document of the same source | the same document | the recipient itself |
|---|---|---|---|---|
| GitHub (69) | +0.570 [0.516, 0.647] | +1.026 [0.913, 1.153] | +1.307 (27 texts; too few for a reading) | +1.397 [1.306, 1.512] |
| Pile-CC (25) | +0.621 | +0.761 [0.694, 0.829] | +0.925 (8; too few) | +0.845 |
| Wikipedia (33) | +0.711 | +0.891 [0.815, 0.992] | +1.021 (7; too few) | +0.978 |
| StackExchange (44) | +0.500 | +0.818 [0.726, 0.906] | +0.927 (3; too few) | +1.030 |
| ArXiv (3; no interval) | +0.426 | +0.705 | | +0.857 |

On code recipients the ladder is monotone, at about the same component count per rung (5,601, 5,250, and 5,243): the closer the donor, the worse. The other-document, same-source rung is material on all four sources, which is what the scope rule required before one may say "within one kind of text" (`s9_run6_scope.csv`).

**What this means for aggregations of related inputs.** *Standing: interpretation.* The paper's sketched route to global explanations starts from narrow sub-distributions of related inputs. On this decomposition related donors are the harshest. Code aggregated into code crosses $X$ at 8 tokens, where code donors switch on 975 components on average (799 to 1,153 over the draws), fewer than the 1,121 general donors switch on; a text's own tokens are harsher still. This is consistent with a component harming where it fires, since a code donor's components fire on code and idle on prose. That reading was not tested directly, and aggregations within a single behaviour, such as bracket closing, were not tested.

### 3.6 The Decomposition Trained Without the Adversarial Loss

*Standing: registered description, with a prediction stated in advance that this decomposition shows larger rises. The prediction holds from 8 tokens on and is reversed at 1.*

The authors also released a decomposition trained without the adversarial loss (WandB run `goodfire/spd/runs/s-05ef623e`):
- A recipient's own explanation sits at 4.69 nats from the original model, against 0.34.
- One donor token's explanation (61 components) *lowers* the divergence by 0.63.
- From 8 tokens on its aggregations harm more in the mean (at 8 tokens on five of eight draws; from 64 tokens on all eight): one donor text costs +2.68, against +0.49.

**At equal amounts of mask moved**, its rise is 6.6, 5.6, and 4.1 times the paper's decomposition's, in the three ranges where its eight draws agree in sign (1,222 to 6,498 units of mask moved). These are the quotients `mean_this` / `mean_other` in bins 2 to 4 of `results/grid/analysis/control/compare_mass_matched_curve_1.csv`, binned on the paper's decomposition's decile edges. In the range just below, 203 to 1,222 units, the quotient is fifteen, but three of the eight draws repair there, so that figure describes one set of draws. In the lowest range, the decomposition trained without the loss repairs outright ($-0.71$).

The ratio is quoted at equal mask moved, not at equal component count, because the two decompositions' donor tokens switch on different numbers of components (61 against 169 at one token). The adversarial loss buys robustness, an aggregation harm four to seven times smaller at equal mask moved, but not an aggregation that holds at any size.

## 4. Deleting Components

The aggregation sections switch components *on*. This part takes them *out*, with two operations.

- **Hard delete.** Chosen components get a mask of 0 at every token of every text. Every other component gets a mask of 1, and the residual is kept. With nothing deleted, this is the complete model, 0.0006 nats from the original (bfloat16 rounding). It is one of the edits the authors' editing code performs: given the same component set, in float32 and with the residual left out in both, their `EditableModel._edited_forward_batched` and this harness return bitwise-identical logits (section 7, item 5). The measured hard delete keeps the residual, which changes the whole-set result below by 0.003 nats. A hard delete can take a mask below its label, so it is not in general a permitted mask.
- **Soft delete.** Chosen components are turned down to the recipient's own label at each token. Every other component stays at 1, and the residual is left out. Every soft-deleted mask is permitted. With nothing turned down, this is the complete decomposition, 0.0115 nats from the original.

Hard-delete damage is reported as a rise over the complete model; add 0.0006 for output harm. Soft-delete values are reported as output harm.

| set of components | definition | size |
|---|---|---|
| used | labelled as needed at some donor token | 9,966 |
| alive (the paper's definition) | mean label over the donor tokens above $10^{-6}$ | 9,959 |
| never needed | labelled as needed at no donor token | 28,946 |
| exactly zero | label exactly 0 at every donor token | 5,336 |

Eight used components fall below the alive threshold, and one alive component is never labelled as needed (`results/grid/pre_reads/main/coverage.csv`).

**What faithfulness guarantees for a deletion.** The paper states the editing aim this way: "Ideally, the resulting model should still behave the same way for all inputs on which those subcomponents were not causally important" [1]. For a hard delete, the prediction at token $t$ of a text is covered only if no deleted component is labelled as needed at any token up to and including $t$. Attention reads earlier tokens, so one early use uncovers everything after it. The covered tokens form the text's **clean prefix**; the first token at which a deleted component is needed is the *first touched token*, $t^*$. The strict form ends the prefix at the first label above 0, instead of above 0.1.

*Worked example.* A text has six tokens, and the deleted set is $\{a, b\}$. Component $a$'s labels are 0, 0, 0.05, 0.3, 0, 0, and $b$'s are 0, 0, 0, 0, 0, 0.2. The first label above 0.1 is at token 4, so the clean prefix is tokens 1 to 3, half the text. In the strict form, the first label above 0 is at token 3, so the prefix is tokens 1 and 2. *Whole-text damage* averages over all six tokens; *conditional damage* averages over the clean prefix only.

**When conditional damage is read.** A text *contributes* to the conditional damage only if its clean prefix has at least 8 tokens ($t^* \ge 8$). The conditional damage at a deletion size is the mean over the eight draws of the mean, over contributing texts, of each text's rise over the complete model averaged over its clean prefix. A size is *testable* only if at least 64 texts contribute on average over draws and clean prefixes make up at least 5% of all positions. Both floors were fixed before any data (`vpd_audit/stats.py`). The six-token text above would not contribute, since its clean prefix has three tokens.

### 4.1 Deleting Components Never Labelled as Needed

*Standing: the chain and the level sweep are readings fixed before the run: they were designed after the whole-set number had been seen, and the possible readings of each were written down before it ran. The whole-set deletion, the exactly-zero set, and the ranked deletions are descriptive; the two orderings of the ranked deletions were fixed before they ran.*

**The chain.** Nested random subsets of the never-needed set are hard-deleted at the component counts of the aggregation curve's sizes (169, 1,121, 4,544, … components, the mean numbers that 1, 8, 64, … donor tokens label as needed), under eight random draws, each draw's subsets nested. Each size is compared with deleting as many uniformly random *alive* components, with the same count in each weight matrix. The table gives means over draws (`results/grid/analysis/main/never_named_chain.csv`, `D_mean`, `alive_control_mean`). Its intervals are those of the conditional damage, corrected over the chain's eleven sizes (`results/grid/analysis/main/never_named_hard_E_D_unif_tau0.1_ones_incl_ctl-none__tau_q0.1__all__donor_chain.csv`, `interval`). At these sizes the clean prefix covers at least 99.6% of positions, so conditional and whole-text damage agree to 0.001.

| components deleted | tokens' worth | rise over the complete model | interval of the conditional damage | deleting as many random alive components |
|---|---|---|---|---|
| 169 | 1 | 0.0060 | [0.0058, 0.0062] | 1.12 |
| 1,121 | 8 | 0.0515 | [0.0497, 0.0536] | 5.40 |
| 4,544 | 64 | 0.297 | [0.288, 0.309] | 9.56 |
| 9,659 | | 0.645 | [0.627, 0.663] | 10.46 |
| 14,473 (half) | | 0.882 | [0.861, 0.904] | |
| 21,709 | | 1.122 | [1.097, 1.146] | |
| 28,946 (all) | | 1.284 | [1.266, 1.302], 95% | 11.33 (all used components) |

Counts are means over the eight draws; at 169 the draws range from 38 to 226 (the 1-token union's size varies by draw). The random comparison varies with the draw too: 0.115 to 2.98 nats, least for the smallest draw (38 components), against 0.001 to 0.008 for as many never-needed components in the same draw (`results/grid/analysis/main/s12/hard_delete_per_draw.csv`). The correction over eleven sizes is why the interval at 1,121 components straddles 0.05; at 95% it would not.

What the table shows:
- **The labels rank correctly.** At equal count, a never-needed component costs 0.5% (at 169) to 11% (all) of what an alive one costs.
- **The absolute claim fails.** Deleting all 28,946 moves the output 1.28 nats from the complete model (1.2847 from the original).
- **The cost is diffuse.** It is near-additive up to about 10,000 components (log-log slopes 1.0 to 1.25) and saturates after (slopes 0.8 to 0.5). The first 9,659 cost 0.64 nats, and the remaining 19,287 cost 0.64 more.
- **A few members do not carry it.** The draw-to-draw spread at small sizes shows no step.

Of the four readings written down before the run (proportional, quadratic, concentrated in a few members, ranked but absolutely wrong), the last holds.

**The exactly-zero set.** The 5,336 components with label exactly 0 at every donor token were hard-deleted as a single cell (`never_named_rung_8_cells.csv`, row `.../tau0/ones/incl/ctl-none`):
- over whole texts they cost 0.326 [0.319, 0.334] nats (rise over the complete model);
- on the strict clean prefix they cost 0.313 [0.303, 0.324]. These are the tokens where every one of the 5,336 also has label exactly 0 on the recipient text, at that token and every earlier one: 30% of positions, with 903 of the 1,024 texts contributing (`results/grid/pre_reads/main/testability.csv`, row `never_named_hard/E/D_unif/tau0/...`, `tau_q0`).

No cut-off enters at any step. The labels say "exactly unused" on both the donor and the recipient texts, and the deletion still moves the output 0.31 nats, six times the 0.05-nat line used throughout this report.

**Soft delete against hard delete.** Turning the never-needed components down to their labels, instead of to 0, leaves them near 0, since on the recipient texts 28,817 of the 28,946 never exceed a label of 0.01 (`results/grid/pre_reads/main/summary.json`). The two operations then agree (`results/grid/main/verify/comparisons.md`, item 4):

| operation (never-needed set; used set at 1) | residual | output harm | from |
|---|---|---|---|
| hard delete | included | 1.2847 | rise 1.2841 (`never_named_rung_8_cells.csv`, `unconditional`) plus the complete model's 0.0006 |
| hard delete | excluded | 1.2876 | rise 1.2761 (same file) plus the complete decomposition's 0.0115 |
| soft delete | excluded | 1.2876 | `level_cells.csv`, `mean_kl`, row `s = 1.0`, never-needed at labels |

At the same residual setting, hard and soft delete agree to four decimals. The 0.003-nat gap between 1.2847 and 1.2876 is the residual's effect under this mask. On 128 texts in float32, with the residual left out in every arm, the authors' editing code and the hard delete give bitwise-identical logits, and the soft delete agrees with them to $2 \times 10^{-5}$ nats in the mean and within 0.003 on every text (`results/identities/h4_main.txt`).

**The level sweep: whether "never needed" holds depends on where the other masks sit.** Raise every *used* component together from its label $g$ toward 1, to the mask

$$
m = s + (1 - s)\,g, \qquad s \in \{0, 0.25, 0.5, 0.75, 1\},
$$

and put the never-needed set either at its labels (a soft delete) or fully on. For example, a used component with $g = 0.2$ at some token sits at $0.6$ when $s = 0.5$, and one with $g = 1$ stays at 1. Values are output harm (`results/grid/analysis/main/level_cells.csv`, `mean_kl`; the difference and its 95% interval are `footprint_labels_minus_one` and `footprint_interval`):

| used set at level $s$ | never-needed fully on | never-needed at labels (deleted) | difference the deletion makes |
|---|---|---|---|
| 0 (their labels) | 0.362 | 0.342 | $-0.020$ [$-0.021$, $-0.019$] |
| 0.25 | 0.262 | 0.262 | $+0.000$ [$-0.000$, $+0.001$] |
| 0.5 | 0.195 | 0.213 | $+0.018$ [$+0.017$, $+0.019$] |
| 0.75 | 0.126 | 0.254 | $+0.128$ [$+0.125$, $+0.131$] |
| 1 (fully on) | 0.011 | 1.288 | $+1.276$ [$+1.259$, $+1.295$] |

The last column is not a distance from the original model. It is how much deleting the never-needed set *changes* the output harm at that level. At the labels end, deleting them slightly *lowers* the harm (0.362 to 0.342). With the used set fully on, it raises the harm from 0.011 to 1.288.

Three shapes were written down before the run for the deletion's effect along this path:
- proportional to $s$: 0.32, 0.64, and 0.96 at the three middle levels;
- quadratic in $s$: 0.08, 0.32, and 0.72;
- a threshold: near zero until the used set is nearly complete.

The threshold shape holds, with an effect rising as $s^6$ to $s^8$. So a "never needed" label is not a property of the component alone: whether deleting it is harmless depends on where the other masks are set.

**No fixed contribution fits these numbers, however it is aligned.** Treat the divergence locally as a squared distance $\|e\|^2$ between output logits. Let $e(s)$ be the used set's error at level $s$ and $\delta$ a fixed contribution of the never-needed set. Then the deletion's effect is

$$
F(s) = 2\langle e(s), \delta\rangle + \|\delta\|^2 \;\ge\; \|\delta\|^2 - 2\|\delta\|\sqrt{L(s)},
$$

by the Cauchy–Schwarz inequality, where $L(s)$ is the harm with the never-needed set on. The corner value $F(1) = 1.276$ with $L(1) = 0.0115$ forces $\|\delta\|$ between 1.03 and 1.24. Then the floor at $s = 0.5$ and $0.75$, where $L = 0.195$ and $0.126$, is at least 0.15 and 0.33. The measured values are 0.018 and 0.128, eight and three times smaller. Saturation of the divergence would only raise the floor. The never-needed set's contribution itself shrinks as the used set is scaled down: it is gated.

*A descriptive aside, measured with no expectation stated:* with the never-needed set at its labels, raising the used set halfway *improves* every one of the 1,024 texts (0.342 to 0.213 in the mean; per text in `results/grid/main/tier3/E__levels/per_sequence.parquet`, against the own-explanation reference on the same texts). The labels are uniformly a little too low.

**Weight size, not the labels, grades the cost.** The never-needed set was ordered two ways and hard-deleted from the top and from the bottom of each order: by weight norm, and by how many donor tokens give a component a label above 0 (not above 0.1). The two orders are nearly independent (Spearman correlation 0.13; `results/grid/pre_reads/main/summary.json`). Each value is one deletion, a rise over the complete model, with its standard error over texts (`results/grid/analysis/main/fig6_ranked_pair.csv`, `D_mean`, `se`):

| deleted | heaviest first | lightest first | most positive labels first | fewest first |
|---|---|---|---|---|
| 201 | 0.0724 (s.e. 0.0014) | 0.0064 | 0.0109 | 0.0068 |
| 1,039 | 0.233 | 0.050 | 0.062 | 0.042 |
| 14,473 (half) | 1.174 | 0.845 | 0.923 | 0.844 |

- **Weight norm grades the cost, eleven to one at 201 components.** The cost is not concentrated in the heavy components, though: the lighter half, deleted alone, still costs 0.85 nats, against the heavier half's 1.17 and 1.28 for both.
- **The count of positive labels barely orders it:** 1.6 to one at 201, and 1.1 to one at half.

"Never needed" is therefore not a matter of a cut-off set too high.

### 4.2 Editing Out Code

*Standing: readings fixed before the run. The group's existence rule, its comparison set, and the readings of the edit were fixed, and the analysis code committed, before any damage was measured; the experiment was designed after an earlier, stricter code edit, part of the original plan, turned out too small to test. The table by source is descriptive.*

#### 4.2.1 The Code-Leaning Group

For each alive component $c$, let $u^{\mathrm{code}}_c$ and $u^{\mathrm{prose}}_c$ be the fractions of the code pool's and the prose pool's token positions that label it as needed (section 2.4; part A of the labelled file). Its **code-importance score** is

$$
s_c = \frac{u^{\mathrm{code}}_c}{u^{\mathrm{code}}_c + u^{\mathrm{prose}}_c}.
$$

The score is 0.5 for even use, 0.9 for nine to one toward code, and 1 for a component no prose position labels as needed. A component enters the group if two conditions hold:
- $s_c \ge 0.9$;
- it passes a **support floor**: $u^{\mathrm{code}}_c \ge 10^{-3}$ (at least 263 of the 262,144 code positions) in at least 8 distinct code texts, so that a rate is never read off one file.

*Worked example.* Take a component labelled as needed at 20,000 code positions across 300 texts and at 1,500 prose positions. Then $u^{\mathrm{code}} = 0.0763$, $u^{\mathrm{prose}} = 0.0057$, and $s = 0.93$, so it is in the group. A strict rule that allows no prose use at all would exclude it. A component needed at 100 code positions in two files and nowhere in prose has $s = 1$ but fails the floor.

The group has **1,007** members (`results/grid/pre_reads/main/s7/code_leaning_groups.csv`, row `G_0.9`). Its *code-firing mass*, the mean number of its members that one code position labels as needed, is 49.47. That is 24.8% of the 199.8 components a code position labels as needed on average. The strict rule's set has 270 members and 0.05% of the mass. Members are ranked by $s_c$, most code-leaning first.

*The existence rule*, fixed before any prose usage rate was computed, read *clear* if two conditions held: the group's mass is at least 10% of that total, and a null that shuffles which of the 1,024 pool texts count as code gives under a fifth of it at its 95th percentile. It read *clear*; over 200 shuffles the largest share is $1.5 \times 10^{-5}$ (`results/grid/pre_reads/main/s7/code_leaning_null.csv`). The null is weak, since any two distinguishable kinds of text would beat it, so *clear* says only that the labels separate these two pools. The evidence that the separation concerns code is the edit below.

Two caveats on the pools:
- The code pool's 512 texts come from 96 documents. Restated in documents, the floor's "8 distinct texts" changes the group by at most seven members and no conclusion.
- "Code-leaning" as built means leaning away from web text and Wikipedia prose. Anything that prose lacks and code has can enter the group, including markup and mathematical notation.

#### 4.2.2 The Comparison Set: Twins

Deleting any few hundred frequently used components harms a model, so each member of the group is paired with a **twin**: a random component from the same weight matrix with nearly the same usage. For each of eight draws, members are processed in rank order, and each takes one candidate at random from the 8 unused candidates nearest in usage rank in its own matrix. Candidates are the alive set minus every component with $s_c \ge 0.75$. A member's twin depends only on the members before it, so twin sets nest as the group's subsets do.

A gate fixed before any deletion required the twins' mean usage and mean weight norm to be within 10% of the group's from 64 members up (`results/grid/pre_reads/main/s7/code_leaning_control_by_rung.csv`):

| members | usage, twins over group | weight norm, twins over group |
|---|---|---|
| 64 | 1.03 | 1.07 |
| 256 | 1.00 | 1.05 |
| 1,007 | 1.02 | 1.02 |

#### 4.2.3 The Edit and Its Readings

The group's top 16, 64, and 256 members, and all 1,007, are hard-deleted. The labelled recipients are split into their GitHub half and their "other" half (StackExchange, ArXiv, Pile-CC, Wikipedia). Let $H$ be whole-text damage and $h$ conditional damage on the clean prefix. The bar for an edit that matters on code is 0.5 nats, and $X = 0.05$ nats is the line for harm that matters. Four readings were fixed before any deletion ran:

| reading | condition | meaning |
|---|---|---|
| R1 | at some size, $H$ on code has its interval at or above 0.5 and is at least three times its twins', while $H$ on other text has its interval below $X$ and $h$ holds where testable | a usable code edit |
| R2 | at every size, other text below $X$ and code below 0.5 | harmless but ineffective |
| R3 | other text passes $X$ at a smaller size than code reaches 0.5 | unclean |
| R4, read beside the others | the group's damage is no more specific to code than its twins' | the labels' lean carries no code-specific effect |

Damage is a rise over the complete model (`results/grid/analysis/main/s7_code_leaning_damage.csv`). Intervals are corrected over the four sizes; twins are means over eight draws.

| members deleted | code | its twins | other text | its twins |
|---|---|---|---|---|
| 16 | 0.016 [0.013, 0.019] | 0.0015 | 0.003 [0.002, 0.005] | 0.002 |
| 64 | 0.101 [0.090, 0.112] | 0.012 | 0.018 [0.014, 0.022] | 0.019 |
| 256 | 0.639 [0.576, 0.702] | 0.100 | 0.156 [0.126, 0.188] | 0.148 |
| 1,007 | 3.24 [3.03, 3.44] | 1.10 | 1.25 [1.02, 1.50] | 1.31 |

**The frozen rule's verdict is "otherwise": none of R1 to R3** (`results/grid/analysis/main/s7_code_leaning_readings.csv`).
- R1 fails because 256 members, the first size that takes half a nat from code, is also where other text first passes $X$.
- R3 misses on that tie, since it asked for a strictly smaller size.
- R4 does not hold: at every size the group's damage is more specific to code than its twins'.

The edit is read only because it reaches code: at 64, 256, and 1,007 members its damage on code exceeds its twins' by 0.089, 0.54, and 2.14 nats, each with the interval of the paired difference above zero (`s7_code_leaning_positive_control.csv`). In plain words, the labels' lean toward code carries a code-specific effect, but no size of this edit is both large enough to matter on code and harmless to the other half as a whole.

**Why faithfulness can barely be tested here** (`results/grid/analysis/main/s7_code_leaning_conditional.csv`, "other" half, cut-off 0.1):

| members deleted | contributing texts (mean over draws) | clean-prefix share of positions | conditional damage |
|---|---|---|---|
| 16 | 238 | 73% | 0.0009, *holds* |
| 64 | 179 | 39% | 0.0037, *holds* |
| 256 | 95 | 4.7% | not testable (under the 5% floor) |
| 1,007 | 0 | 0% | not testable |

A group allowed one prose use in ten is labelled as needed on nearly every non-code text within its first few tokens. So from 256 members up, faithfulness covers only a few percent of non-code tokens and says nothing about the rest: 4.7% here, and on the 200-passage panels of section 4.2.5 0.9% (StackExchange), 1.2% (ArXiv), 5.8% (Wikipedia), and 7.4% (web text), with almost none at 1,007 (`results/grid/analysis/main/s12/panel_coverage.csv`, cut-off 0.1). At 64 members the *holds* is a test of low severity. The whole-text damage there is 0.0179 with 39.4% of positions clean, so even if all of it fell on clean positions, their average could be at most $0.0179 / 0.394 = 0.045$, already under $X$. The more informative contrast at 64 members is within the text: about 0.0036 nats per clean token against about 0.027 per token after the group's first use. Clean tokens are early tokens by construction, though, and no position-matched baseline exists.

#### 4.2.4 Where the Damage Falls, by Source

*Standing: descriptive. The table was added before the run with no reading attached; the rule read the other half as one group.*

Damage at 256 and 1,007 members over whole texts, as a rise over the complete model (`results/grid/analysis/main/s7_code_leaning_damage_by_source.csv`; also `results/grid/analysis/main/s9/check_a_removed_label_by_source.csv`, `H_group`, `H_twins`):

| source (documents) | 256: edit | 256: twins | 1,007: edit | 1,007: twins |
|---|---|---|---|---|
| GitHub (69) | 0.639 | 0.100 | 3.24 | 1.10 |
| StackExchange (44) | 0.325 | 0.112 | 2.17 | 1.12 |
| ArXiv (3) | 0.250 | 0.124 | 2.47 | 1.05 |
| web text, Pile-CC (25) | 0.021 | 0.176 | 0.16 | 1.44 |
| Wikipedia (33) | 0.026 | 0.179 | 0.20 | 1.61 |

Document-level 95% intervals for the edit's damage (`results/grid/analysis/main/s12/code_edit_E_lab_document_intervals.csv`): GitHub [0.49, 0.77] and [2.66, 3.68] at 256 and 1,007 members; StackExchange [0.26, 0.40] and [1.83, 2.53]; web text [0.020, 0.022] and [0.145, 0.177]; Wikipedia [0.023, 0.032] and [0.161, 0.253]; none for ArXiv, whose 64 texts come from three papers. They are wider than intervals that resample texts would be, by up to about 2.7 times in standard error on GitHub, because texts from one document are not independent.

- **Web text and Wikipedia are spared.** Their twins cost them seven to nine times what the edit does. They are the sources the prose pool was drawn from, though from disjoint documents. So this shows that the labels carry over to held-out text of those sources, not that the group is specific to code.
- **StackExchange is hit about as hard as ArXiv.** Much of StackExchange is code: in the reading of section 2.4, done under anonymous keys, 7 of 16 sampled StackExchange texts read as code and 5 more as mixed code and prose (`results/data/reader_labels/labels_labeled_sample.tsv`). The same existence rule, run on 200-text panels of GitHub against StackExchange, reads *none* in both directions: 0.15% and 1.7% of what a position labels as needed (`results/grid/analysis/main/s9b/check_b_panels.csv`). The labels do not distinguish the two sources, so the edit reaches code wherever it appears.
- **ArXiv.** The Pile's ArXiv component is LaTeX source with Markdown structure, dense in math-mode markup: backslash commands, braces, sub- and superscripts, `&` alignment. It contains little program code; the readers of section 2.4 labelled none of 16 sampled ArXiv texts as code (13 prose, 3 other). At 256 members the label mass the edit removes on ArXiv is 1.12, against 9.05 on GitHub, 5.49 on StackExchange, and 0.03 and 0.06 on web text and Wikipedia (`check_a_removed_label_by_source.csv`, `omega_group`). **These 64 ArXiv texts come from three papers**, which is why section 4.2.5 re-measures the edit on many.

#### 4.2.5 The Edit Re-Measured on Texts From Many Documents

*Standing: readings fixed before the run, with the analysis code committed first, for ArXiv; the other seven panels are descriptive.*

Because the ArXiv figure above rests on three papers, the edit was measured again on text from many documents. Each *panel* is 200 random 512-token windows from part C of the labelled file, which is disjoint from every text the components were chosen on. Each window's source document was recovered exactly from the token stream (`results/grid/analysis/main/s12/panel_document_index.csv`), so that intervals can resample documents: the ArXiv panel's 200 passages come from 162 papers, and the other panels from 174 to 197 documents. The edit is the same: the group's 256 and 1,007 members, hard-deleted, against the eight twin draws.

**The ArXiv reading, fixed before the run.** Let $H$ be the edit's damage and $T$ the twins' (averaged over the eight draws per text), with $\rho = H / T$ recomputed inside each bootstrap replicate, and 95% intervals over documents (section 6.4):
- *keep* if at 256 members the interval of $H$ lies at or above 0.05, and the interval of $\rho$ lies above 1 at both sizes;
- *drop* if the interval of $H$ at 256 members lies entirely below 0.05;
- *soften* otherwise.

**It reads keep** (`results/grid/analysis/main/s12/s12_panels.csv`): at 256 members $H = 0.262$ [0.233, 0.292] and $\rho = 2.15$ [1.88, 2.43]; at 1,007 members $H = 2.68$ [2.42, 2.92] and $\rho = 2.48$ [2.20, 2.76]. The edit damages ArXiv text more than twice as much as deleting equally used random components does.

**Every panel** (damage as a rise over the complete model; 95% intervals over documents):

| panel (documents) | 256: $H$ | 256: $T$ | 256: $\rho$ | 1,007: $H$ | 1,007: $T$ | 1,007: $\rho$ |
|---|---|---|---|---|---|---|
| GitHub (193) | 0.666 [0.611, 0.723] | 0.076 | 8.71 [7.74, 9.75] | 3.34 [3.17, 3.51] | 0.98 | 3.42 [3.15, 3.69] |
| StackExchange (197) | 0.342 [0.308, 0.377] | 0.102 | 3.36 [2.94, 3.82] | 2.26 [2.10, 2.43] | 1.07 | 2.12 [1.94, 2.31] |
| ArXiv (162) | 0.262 [0.233, 0.292] | 0.122 | 2.15 [1.88, 2.43] | 2.68 [2.42, 2.92] | 1.08 | 2.48 [2.20, 2.76] |
| web text, Pile-CC (192) | 0.026 [0.022, 0.030] | 0.171 | 0.150 [0.128, 0.178] | 0.213 [0.175, 0.260] | 1.37 | 0.155 [0.127, 0.190] |
| Wikipedia (184) | 0.025 [0.024, 0.026] | 0.175 | 0.143 [0.137, 0.150] | 0.208 [0.184, 0.241] | 1.59 | 0.130 [0.115, 0.152] |
| DM Mathematics (174) | 0.089 [0.080, 0.100] | 0.115 | 0.78 [0.70, 0.87] | 1.13 [1.06, 1.19] | 1.20 | 0.94 [0.87, 1.01] |
| PubMed Central (186) | 0.078 [0.060, 0.098] | 0.124 | 0.63 [0.48, 0.80] | 0.89 [0.78, 1.02] | 1.33 | 0.67 [0.58, 0.77] |
| FreeLaw (174) | 0.044 [0.037, 0.051] | 0.229 | 0.19 [0.16, 0.23] | 0.33 [0.29, 0.37] | 1.80 | 0.18 [0.16, 0.21] |

**Replication.** GitHub, StackExchange, and Wikipedia on the panels fall inside the intervals of the labelled evaluation set above at both sizes. Web text comes out a quarter to a third higher on the panel (0.026 against 0.021 at 256 members, 0.213 against 0.162 at 1,007), and at 256 members the two intervals do not overlap; it is spared either way (`s12_replication.csv`). The post's code-edit figure uses the panels for every bar.

**What the edit reaches, descriptively.** Three further sources were chosen before the run to separate explanations of the ArXiv damage: mathematics without LaTeX (DM Mathematics, arithmetic and algebra problems in plain text), scientific writing with little mathematics (PubMed Central), and formal prose far from web text (FreeLaw). All three are damaged less than by the twins at 256 members, and at 1,007 members DM Mathematics' $\rho$ interval includes 1 ([0.87, 1.01]). So neither mathematics as such nor scientific register accounts for most of the ArXiv damage (DM Mathematics still takes 0.089 nats at 256 members, three and a half times web text's), which points to LaTeX markup: braces, backslashes, sub- and superscripts, and alignment characters, which prose lacks and code shares. This reading was not tested directly, for example by separating math-mode tokens from prose tokens within ArXiv passages.

**The labels understate ArXiv's dependence on the group.** On the five panels with label caches, $\omega$, the label the edit removes, orders the sources GitHub > StackExchange > ArXiv > web text > Wikipedia at both sizes, and the damage follows that order at 256 members, though web text and Wikipedia are within each other's intervals there (0.026 and 0.025). Per unit of label removed, though, the group costs ArXiv 2.6 times (256 members) and 1.6 times (1,007) what the twins cost per unit of their label, while it costs the two code sources less per unit than the twins (0.5 to 0.7; `s12_removed_label.csv`). The two prose panels also exceed 1 at 256 members (1.9 and 5.8), but on a removed label so small that the ratio moves a lot with little label; ArXiv's ratio rests on a substantial one. At 1,007 members ArXiv is damaged more than StackExchange (2.68 against 2.26) although the labels remove half as much there (15.4 against 31.0).

#### 4.2.6 Why Deleting What One Token Needs Is Not an Edit

*Standing: registered description.*

A simpler edit deletes what code tokens label as needed. It breaks the model (rises over the complete model):
- deleting the 198 components one code token needs costs 11.7 nats on the labelled recipients;
- deleting what 64 code texts need costs 11.6;
- one general donor token's 169 components cost 11.5 on the recipient texts.

For comparison, switching off every component and the residual costs 67.10 nats (`results/acceptance/conditions_main_bf16.csv`, row `zero_all`, `kl_mean`). Every token's explanation includes components that every text uses from its first token, so every text's clean prefix is empty, and faithfulness cannot even be tested for this edit (`results/grid/analysis/main/hard_zero_E_lab_D_code_tau0.1_ones_incl_ctl-none__tau_q0.1__all__donor_chain.csv`, `unconditional`, and its `testable` column).

### 4.3 Soft Deletion: A Text's Own Explanation, Used in Part

*Standing: the shape is a registered description, named before the data with no rule attached. The frequency-matched comparison and the rule that reads it were fixed, with their analysis code committed, before that comparison ran.*

**The operation.** Take the components that $k$ donor tokens label as needed, and turn them down to the recipient's own labels, token by token, with every other component fully on and the residual left out. The mask is permitted, and only the recipient's own explanation is involved: the donors choose *which* components are turned down, not the values. One token's worth is 169 components on average.

**The hump.** Values are output harm (`results/grid/analysis/main/soft_erase_E_D_unif_tau0.1_r1_excl_ctl-none.csv`, `mean_kl`, `fraction_seq_above_X`):

| turned down to own labels | output harm | recipients harmed by more than 0.05 nats |
|---|---|---|
| none (the complete decomposition) | 0.011 | |
| 169 (1 token's worth) | 0.448 | 100% |
| 1,121 (8) | 0.742 | 100% |
| 4,544 (64) | 0.476 | 100% |
| every used component (9,966) | 0.362 | 99.8% |

For reference, the recipient's own explanation (every component at its label) sits at 0.342. So turning 169 components down to their labels, with the rest on, harms the output more than using the whole explanation does. Lowering more can cost less, and no sum of non-negative per-component costs produces such a hump. The labels hold, as far as they hold, only as a joint configuration.

**The two random comparisons** (`results/grid/analysis/main/s7_marginal_closure.csv`, the soft-delete family; the committed values are rises over the complete decomposition, to which 0.0115 is added here). The uniform and frequency-matched sets are built as in section 3.4.

| tokens' worth | real set | frequency-matched | uniform random |
|---|---|---|---|
| 1 | 0.448 | 0.417 [0.404, 0.430] | 0.082 |
| 8 | 0.742 | 0.671 [0.659, 0.685] | 0.303 |
| 64 | 0.476 | 0.459 | 0.366 |

Intervals are corrected over the two sizes the rule reads. At 1 and 8 tokens' worth, the matched sets share only 9% and 29% of the real sets' moved mask, yet cost 93% and 90% of what the real sets cost. The rule fixed in advance returned **kind**, the reading opposite to *combination* in section 3.4: the hump belongs to heavy, much-used components turned down while the rest of the model is on, not to the particular sets that real explanations name. What remains specific to real sets is small: +0.031 nats at 1 token's worth (six of eight draws) and +0.070 at 8 (eight of eight).

## 5. How Big Is a Nat?

*Standing: descriptive. The list of masks, the statistics, and the comparison models were fixed before the run.*

Output harm is a divergence, and a reader needs a sense of its size. For each mask below, the run stored, at every token, the masked model's top prediction, its probability on the original model's top prediction, and its loss on the real next token (`results/grid/analysis/main/s9b/s9_plain_terms_listed_masks.csv`, set `E`). The divergences are from `s9_yardstick.csv`, `s9_yardstick_ratios.csv`, `level_cells.csv`, and `results/acceptance/conditions_main_bf16.csv`.

| state of the model | output harm (nats) | top prediction differs from the original's | among tokens where the original is confident | top prediction is the real next token | loss on the real next token |
|---|---|---|---|---|---|
| the original model | 0 | | | 48.3% | 2.72 |
| the complete model (residual included) | 0.0006 | 0.9% | 0.04% | 48.3% | 2.72 |
| the complete decomposition (residual left out) | 0.011 | 5.0% | 0.4% | 48.1% | 2.73 |
| a text's own explanation | 0.342 | 18.5% | 1.9% | 47.8% | 3.00 |
| Pythia-70M, a different model | 0.394 | 26.4% | 6.5% | 46.5% | 2.89 |
| Pythia-160M, a different model | 0.463 | 26.3% | 5.3% | 50.8% | 2.54 |
| the 64-token aggregation (mean over eight draws) | 0.799 | 37.6% | 16.9% | 39.9% | 3.49 |
| the one-text aggregation (mean over eight draws) | 0.829 | 37.6% | 17.8% | 39.5% | 3.53 |
| deleting the never-needed components | 1.285 | 53.8% | 37.1% | 30.6% | 4.01 |
| the self-aggregation | 1.371 | 54.9% | 38.8% | 30.0% | 4.09 |

"Confident" means the original model's top prediction has probability at least 0.5. The change rates leave out the 2.5% of tokens where the original's top two predictions tie exactly, since bfloat16 logits are coarse.

Pooled over these masks by the divergence at a token (`s9_plain_terms_bins.csv`), the top prediction changes at 1.2% of tokens whose divergence is under 0.05, where the masked model's mean probability on the original's top prediction is 0.85. It changes at 42% of tokens between half a nat and one, where that probability is 0.18, and at 91% of tokens over two nats, where it is 0.03. Five example tokens, chosen by a rule fixed before the run, are in `s9_examples.csv`.

**The outside yardstick.** Pythia-70M and Pythia-160M [2] share the model's tokenizer, which was asserted id by id over all 50,277 ids. The 27 padded output entries of each carry under $10^{-10}$ of the probability on average and were dropped before renormalizing (`s9_yardstick.csv`). The divergence from the original to Pythia-70M is 0.394 [0.386, 0.402] on the recipient texts. As multiples of it (`s9_yardstick_ratios.csv`):

| mask | multiple of Pythia-70M's divergence |
|---|---|
| a text's own explanation | 0.87 [0.85, 0.88] |
| the 64-token aggregation | 2.03 [2.00, 2.06] |
| the one-text aggregation | 2.11 [2.08, 2.13] |
| deleting the never-needed components | 3.26 [3.20, 3.32] |
| the self-aggregation | 3.48 [3.42, 3.55] |

Two things a reader is owed:
- **Pythia probably saw these texts.** It was trained on the full Pile [2], and the recipient texts come from the Pile, so it has probably seen most of them; the original model has not. There is no sign that this matters: each Pythia's loss gap to the original is the same on the recipient texts as on held-out labelled texts, +0.17 against +0.18 for Pythia-70M, and −0.18 against −0.17 for Pythia-160M.
- **Distance is not quality.** Pythia-160M has a lower loss than the original model, and yet in the forward divergence used throughout it sits farther from the original than Pythia-70M does, because a sharper model rules out tokens the original keeps. In the reverse divergence it is nearer (0.39 against 0.41; `s9_yardstick.csv`, `kl_model_to_target`). A masked model is the same weights partly switched off, and its loss rises with its divergence almost one for one: the 64-token aggregation sits 0.80 nats away and costs +0.77 of loss, and the self-aggregation 1.37 away at +1.37. A different model's loss does not track its divergence this way (0.39 away at +0.17; 0.46 away at −0.18).

## 6. Statistics as Used

### 6.1 What Is Measured, and Paired

Every measurement is one forward pass of the model under one mask over a fixed set of texts. For text $b$ it records $\bar K_b$, the output harm averaged over the text's 512 tokens.

Nearly every number is a *paired difference*: the same text measured under two masks, one subtracted from the other. For an aggregation with donor draw $k$ at size $j$, the rise on text $b$ is

$$
e^{(k,j)}_b = \bar K^{(k,j)}_b - \bar K^{(0)}_b ,
$$

where $\bar K^{(0)}_b$ is the text's output harm at the starting point: its own explanation for an aggregation (0.342 nats on average), the complete model for a hard delete (0.0006 with the residual included), or the complete decomposition for a soft delete (0.0115). A reported value is the mean over the eight donor draws of the mean over texts:

$$
\hat e_j = \frac{1}{8} \sum_{k=1}^{8} \frac{1}{N} \sum_{b=1}^{N} e^{(k,j)}_b .
$$

Pairing matters because texts differ from one another by tenths of a nat, while a mask moves a single text by hundredths. *Worked example*, with three texts and one draw: divergences under the own explanation of 0.30, 0.35, and 0.40, and under an aggregation of 0.31, 0.39, and 0.41, give rises of 0.01, 0.04, and 0.01, with a mean of 0.02. The spread of the rises (0.03) is far smaller than the spread of the divergences (0.10), and it is the rises that the intervals resample.

### 6.2 What Is Resampled, and What Is Held Fixed

Every interval is a bootstrap percentile interval with 10,000 replicates: the sampling units are redrawn with replacement, the statistic is recomputed on each redraw, and the interval runs between two quantiles of the recomputed values.

**The sampling unit is the text on the recipient texts and the document on the labelled texts.** The recipient texts are rows of a globally shuffled token stream, so the resample draws texts. The labelled texts are consecutive windows of a few documents per source (section 2.4), so there the resample draws *documents*, all texts of a drawn document entering together. Every mean is kept text-weighted: the resampled text total over the resampled text count. So the point estimate is the plain mean over texts, and only the interval changes. Where a stratum pools several sources (the prose recipients are web text and Wikipedia together), each source's documents are resampled among themselves and the sources are combined with their fixed text shares, so that the mix of sources is the design's in every replicate.

*Worked example.* A stratum has four texts from documents A, A, B, and C. A replicate that draws (A, A, C) holds texts A1, A2, A1, A2, and C: five texts, whose sum divided by five is the replicate's mean.

**No interval is reported for a stratum of fewer than ten documents.** Three papers cannot estimate the between-document variance, so ArXiv is a point value wherever it appears on the labelled texts.

**The eight donor draws and every random comparison set are held fixed.** An interval says how far a number would move with different texts of the same kind, for these donor draws, on this decomposition. It does not say how far it would move with different donors. Variation over donors enters in two other ways:
- a sign condition inside each pass-or-fail rule: an aggregation size counts as detected only if at least seven of the eight draws have a positive mean rise;
- where a rule compares two donor pools, a *two-level* interval that resamples the draws as well as the texts.

At the one-donor-text point of the aggregation curve, for example, the two-level interval on the rise is [0.264, 0.644] against the texts-only [0.472, 0.504] (`results/grid/analysis/main/union_E_D_unif_tau0.1_r0_excl_ctl-none.csv`, columns `two_level` and `interval`), because one of the eight donor texts names far fewer components than the others.

**Replicates are shared.** One set of redraws is made per set of texts, from a fixed seed, and used for every mask measured on those texts. A difference between two masks, or a ratio of two damages, is therefore computed replicate by replicate. Ratios are recomputed inside each replicate from the resampled sums, never as a ratio of interval ends. A replicate in which a ratio is undefined is counted, and a quantity with any undefined replicate is not read.

### 6.3 Levels: 95 Percent in the Figures, Corrected Levels in the Readings

The post's figures draw every error bar as an uncorrected 95 percent interval, recomputed from the committed per-text tables with the resamples above. The figures carry no verdict, and a reader expects an unlabelled bar to be 95 percent.

The pass-or-fail readings fixed before their data were read at *corrected* levels. An aggregation curve compares $m$ sizes with its start, and each size's interval is drawn at level $1 - 0.05/m$ (Bonferroni), so that the chance of any of the $m$ intervals missing by chance is at most 5 percent for the curve as a whole.

| reading | $m$ | level | table |
|---|---|---|---|
| the aggregation curve on the recipient texts, and its uniform random comparison | 10 | 99.5% | `results/grid/analysis/main/union_E_D_unif_tau0.1_r0_excl_ctl-none.csv`, `..._ctl-plain.csv` |
| the frequency-matched comparison at 1 and 8 tokens' worth | 2 | 97.5% | `results/grid/analysis/main/fig7_marginal_control.csv` |
| the same at 16, 32, and 64 tokens' worth (descriptive) | 1 | 95% | same file |
| the all-or-nothing aggregation form (three sizes and the self-aggregation) | 4 | 98.75% | `results/grid/analysis/main/s11/s11_step1.csv` |
| code, general, and prose donors into code and prose recipients | 10 | 99.5%, over documents | `results/grid/analysis/main/s9b/s9_run2_curves.csv` |
| the match ratio $R$ (two-level) | 3 | 98.3% | `s9_run2_match_ratio.csv` |
| the count-only prediction | 2 | 97.5% | `s9_run2_count_only.csv` |
| the self-aggregation (three text sets) | 3 | 98.3% | `s9_run6_self_merge_rule.csv` |
| the closeness ladder (five sources), over documents | 5 | 99% | `s9_run6_ladder.csv` |
| the never-needed deletion chain (eleven sizes) | 11 | 99.5% | `never_named_hard_E_D_unif_tau0.1_ones_incl_ctl-none__tau_q0.1__all__donor_chain.csv` |
| the code edit on code and on the pooled other text (four sizes) | 4 | 98.75% | `s7_code_leaning_damage.csv` |
| the soft-delete frequency-matched comparison (two sizes) | 2 | 97.5% | `s7_marginal_closure.csv` |
| every single whole-set deletion, every difference between two masks or two decompositions, the level sweep, and the by-source damages | 1 | 95% | `never_named_rung_8_cells.csv`, `level_cells.csv`, `s7_code_leaning_damage_by_source.csv`, the `compare_*.csv` tables |

The weight- and label-ranked deletions report a standard error beside each mean (`ranked_pair.csv`, `se`), not an interval. A "±" beside a single mean is always a standard error: the standard deviation over texts divided by $\sqrt{N}$.

**Monte-Carlo error.** An interval end estimated from 10,000 replicates is stable to about a fortieth of the interval's half-width. No reading in the post sits within that distance of its threshold.

### 6.4 The ArXiv Re-Measurement, and Why Its Reading Needs No Correction

The ArXiv reading of section 4.2.5 was fixed before the run:
- *keep* if the interval of $H_{256}$ lies at or above 0.05 nats, **and** the interval of $\rho$ lies above 1 at both sizes;
- *drop* if the interval of $H_{256}$ lies entirely below 0.05 nats;
- *soften* otherwise.

*Keep* is an intersection of three conditions, each tested at level 0.05. When a claim requires all of several conditions, testing each at level $\alpha$ gives an overall false-positive rate of at most $\alpha$: the claim is wrongly kept only if every test passes, which is at most as likely as any one of them passing wrongly. This is the intersection-union principle, and it is why *keep* needs no Bonferroni correction. The price is power, not size: the more conditions, the more often a true effect lands in *soften*, which is the conservative direction for the post. *Drop* is a single condition and needs no correction either. As with every ratio here, $\rho$ is read only if no bootstrap replicate leaves it undefined. If *drop* were returned, one of three further panels could stand in as the post's example of collateral damage only if it met *keep* at $1 - 0.05/3$, correcting for the three candidates.

## 7. Why the Code Can Be Trusted

A measurement that contradicts a paper's claim is only as good as the instrument that made it. This section lists the checks that stand between the released checkpoints and every number in this report, each with the failure it rules out and the committed file where it can be read. Items 1 and 2 ask whether the harness computes what the authors' code computes. Items 3 to 5 ask whether each forward pass received the intended mask, and whether the hard delete is the authors' own edit. Items 6 to 8 ask whether anything moved when the harness was later changed or relaunched. Items 9 and 10 ask whether the readings could have been shaped by the results. Item 11 says what the chain does not cover. Lines in the committed check files carry short labels (such as H2, P4, or CE-DIAG); a label is given so that the line can be found, and each item says what the check compares.

**1. The harness reproduces the paper's table.**
- **What was done.** Given the released checkpoints, the harness re-measured the paper's cross-entropy table on all 1,024 recipient texts, under each of the table's mask conditions: the original model, everything on, random masks, labels rounded at three thresholds, and the labels used as masks.
- **The comparison.** The paper's table rests on one batch of 128 texts that cannot be reconstructed, so each row is compared by its paired difference from the original model.
- **The result.** Every paired difference is within 0.006 nats of the printed value; the largest miss is 0.0057, on the rounded-at-zero row (`results/acceptance/vs_paper.csv`).
  - The mean number of labels above zero per token is 203.4, against the paper's 205.
  - The output harm with every component off is 67.10, against the paper's 67.24, inside the batch-to-batch spread (`results/acceptance/checks.txt`, checks 4 and 5).
  - All gated lines of that file pass, and their tolerances were written before any number existed.
- *Rules out:* the wrong checkpoint, a different computation of the labels, a different reading of the mask conditions, a different measure of harm.

**2. Agreement with the authors' own evaluation code.** The authors' evaluation class builds the same mask conditions its own way, and was driven exactly as their evaluation script drives it, on the same 128 texts.
- **In float32**, all 105 gated comparisons agree. The largest gap is $5.2 \times 10^{-6}$ nats, on the everything-off divergence of 67 nats; every other gap is $3.1 \times 10^{-7}$ or smaller (`results/short_runs/check6_fp32_unrounded/summary.json`).
- **In bfloat16**, the precision every run uses, the largest gap over 189 gated comparisons at matched batch shape is $3.1 \times 10^{-4}$ nats, against a tolerance of $10^{-3}$ (`results/short_runs/check6_bf16/check6_summary.json`). That gap sits in the cross-entropy rows only. It comes from their cross-entropy call rounding log-probabilities to bfloat16 before averaging, and a one-line cast removes it; the output harm agrees to about $10^{-7}$ (`results/smoke_fp/checks_main_bf16_n64.txt`, the lines labelled CE-DIAG).

Every number in this report is an output harm. *Rules out:* that our reference masks or our measure differ from the authors'.

**3. Masks whose answer is known in advance.** Each identity builds a mask through the audit's own formula and compares it with a result known independently:
- an aggregation with no donors equals the recipient's own explanation, bit for bit;
- a soft delete of nothing equals everything on;
- everything on, with the residual included, reproduces the original model over all 1,024 recipient texts, to $6.2 \times 10^{-4}$ nats in bfloat16 (that precision's noise floor) and to $-1.6 \times 10^{-9}$ in float32 (`results/acceptance/conditions_main_bf16.csv` and `conditions_main_fp32.csv`, row `unmasked_delta`);
- zeroing every mask at one token leaves every earlier token's prediction unchanged and changes that token's;
- a hard delete puts exactly 0 on the deleted set and exactly 1 elsewhere.

*Where:* `results/smoke/checks_main_bf16_n64.txt` and `results/identities/checks_main.txt`. *Rules out:* an error in the mask formula, in the treatment of the residual, or in causal ordering, at every point where the truth is known.

**4. A fingerprint of the mask each forward pass actually received.** The most dangerous silent failure in this design is a mask that is computed and never applied: every aggregation would then equal its recipient's own explanation, and the rule would read "faithfulness holds". Counting what a mask should switch on does not catch it, because the count comes from the recipe, not from the tensor the model saw. So every forward pass records an exact on-device digest of the mask tensors it receives.
- The digest gives the same equality pattern as SHA-256 over all pairs of cells, and is bitwise equal between CPU and GPU (`results/smoke_fp/checks_main_bf16_n64.txt`).
- Along every chain the digests are pairwise distinct, and each chain's start equals its reference condition's digest (`results/grid/analysis/main/report.md`, precondition P4: 62 of 62 chains).
- Every aggregation is also checked to be permitted, with no entry below its label, on every batch of the main grid and of the all-or-nothing run (`results/grid/analysis/main/report.md`, precondition P3; `results/grid/analysis/main/s11/report.md`, section 0).

*Rules out:* the unapplied mask; two cells silently receiving the same mask; an aggregation that faithfulness does not cover.

**5. The hard delete is the authors' edit, bit for bit.** The authors' library ships an editing function that zeroes chosen components at every token. Their function and our hard-delete path were given the same sets, and their logits compared, in float32 with the residual left out in both arms.
- On one text, at 6,058 and at 4 deleted components, the largest difference is exactly zero (`results/identities/checks_main.txt`, H2).
- On 128 recipient texts with all 28,946 never-needed components deleted, the logits are identical, and both arms give 1.2944 nats (`results/identities/h4_main.txt`).

The measured hard delete runs in bfloat16 and keeps the residual; keeping the residual changes the whole-set result by 0.003 nats (section 4.1). *Rules out:* that the edit tested differs from the edit in the authors' own editing code, and that the cost of deleting the never-needed set is an artefact of our mask construction.

**6. Every code path ran on a small stand-in first.** Before any cell ran on the paper's model, the whole grid ran on a small public decomposition of a small model: 1,097 cells across every family, comparison, size, and draw, with every precondition read on its output. None failed (`results/dry_run/summary.md`). The same was done before each later launch. *Rules out:* enumeration and plumbing errors reaching the paper's model. It does not show that any number on the paper's model is right; items 1 to 5 do that.

**7. Re-runs, resumes, and later changes moved nothing.**
- **After a speed-up.** One launch on the paper's model re-ran 41 cells measured before the harness was sped up. The 25 reference conditions agree on all 25,600 (cell, text) pairs, in harm and cross-entropy, and the 16 chain cells agree on all 16,384 pairs, in harm and fingerprint (`results/grid/main/verify/comparisons.md`, items 1 and 2).
- **After a resume.** A store interrupted after its second batch and resumed equals an uninterrupted one on every column (same file).
- **After a re-read.** Claims first read from an early analysis were later recomputed from the committed stores. 42 of 43 printed values agree at the printed precision; the exception is 1.2953, printed as 1.29 (`results/grid/analysis/main/s7_checks/summary.md`).

*Rules out:* that an optimization, a resume, or a re-read changed a number.

**8. A bitwise canary in every launch.**
- **Reference conditions.** Every store carries the full set of reference conditions, run in the same job, and the analysis asserts them bitwise equal across every store on the same texts before reading anything else (`results/grid/analysis/main/report.md`, section 0).
- **Conditional damage, computed twice.** The conditional damage of a delete is computed once in the loop in float32 and again from the stored per-token arrays, with a tolerance derived from the arrays' precision. The largest discrepancy is 0.76 of its bound over 383,923 checks on the recipient texts, and 0.86 over 312,116 on the labelled texts (same section).
- **Re-run cells.** Later launches re-ran cells of earlier ones as canaries:
  - 77 re-run cells over 166,912 (cell, text) pairs, bitwise equal, in the similar-donors run (`results/grid/analysis/main/s9b/report.md`, section 0);
  - five cells in the all-or-nothing run (`results/grid/analysis/main/s11/report.md`, section 0);
  - the stored per-text harms of 69 cells, reproduced from their per-token arrays to $8.5 \times 10^{-5}$ (`results/grid/analysis/main/s9/report.md`).
- **One departure.** The launch of the random-component comparisons ran from a working tree with uncommitted edits to analysis files. That launch imports none of them, its manifest records the flag (`results/grid/main/tier2/E/run_manifest.json`, `commits.dirty`), and its references equal the first launch's bitwise.

*Rules out:* drift between launches in code, checkpoint, or hardware, and an off-by-one in where a clean prefix ends. Most stores ran on A100 40 GB cards; four ran on A100 80 GB cards (`results/grid/main/tier2/E/run_manifest.json`, `tier2/E_lab/`, and `results/grid/control/tier1/E/` and `tier1/E_lab/`, field `gpu_name`), and their reference conditions agree with the others bitwise.

**9. Everything the labels alone decide was fixed before any harm was measured.**
- **For the deletions.** Several choices in reading a delete depend only on labels: which components count as never needed, where each text's clean prefix ends, and so which sizes have enough clean text to be read at all. These were computed on CPU from cached labels and committed before any deletion chain ran. The analysis asserts that the first touched tokens recorded in the loop equal the pre-computed ones on every delete cell (`results/grid/pre_reads/main/`; the pre-read line of `results/grid/analysis/main/report.md`, section 0).
- **For the comparison sets.** The frequency-matched components passed a gate on mean usage, weight norm, and mask moved before launch (`results/grid/pre_reads/main/s7/marginal_gate.csv`). The code edit's twins passed their 10 percent gate at 64, 256, and 1,007 members (`results/grid/pre_reads/main/s7/summary.md`).
- **For the aggregation sets.** Every aggregation set of the similar-donors and all-or-nothing runs was asserted by hash against a committed label-only table before any forward pass (`results/grid/pre_reads/main/s9/verification.json`; `results/grid/pre_reads/main/s11/checks.md`).

*Rules out:* deciding what to read after seeing what it says; a comparison set that differs from the real one in the property it exists to match.

**10. The analyses were frozen, with planted answers, before they saw a result.** Each reading rule is a pure function tested on fabricated data with known answers:
- a planted rise of 0.08 nats must read *fails*, 0.01 *detected but immaterial*, and none *holds*, with the first detected and first material sizes where they were planted;
- planted closures must return the comparison's readings;
- a comparison equal to its delete must give an interval of exactly zero;
- a planted all-or-nothing rise within, and outside, a factor of two of the fractional rise must return the two outcomes (outcome A, and its opposite).

These tests are in `tests/test_stats.py`, `test_analysis.py`, `test_stats_s7.py`, `test_analysis_s7.py`, `test_stats_s9.py`, `test_analysis_s9.py`, and `test_analysis_s11.py`. The code was then committed, and each analysis refuses to read a store of the paper's model unless the working tree is clean and the analysis code is the committed version. The later reports print a table of the frozen modules at the top (`s9/report.md`, `s11/report.md`); the main report records the frozen commit and the clean-tree flag.

Three limits, stated:
- at the wider of two planted noise levels, the 0.01 rise sits at the edge of detection, and the test accepts either label;
- the false-alarm test asserts only that at most a tenth of 200 null tables produce a detection;
- for the first aggregation curve, the freeze protected less than the phrase suggests: its two ends had been measured, as harness checks, before its analysis was frozen. What the freeze protected there is everything between the ends, the contrast with random components, and every deletion number.

*Rules out:* rules tuned to the result, rules that cannot fire, rules that fire on noise.

**11. What the chain does not cover.** It establishes that the harness computes what the authors' code computes, applies the masks it says it applies, and was read by rules fixed in advance. It does not establish:
- that the released checkpoints are the ones behind the paper's figures, beyond the agreement of item 1;
- that the results carry over to another seed, size, or training recipe;
- that intervals cover more than the texts they resample, since donor draws and random comparison sets are held fixed (section 6.2).

## 8. The Standing of Every Number in the Post

The standings are those of section 1:
- **Registered verdict:** a pass-or-fail rule in the original plan, fixed before any of the audit's data existed, and read by analysis code committed before any result was read.
- **Registered description:** a quantity named in the original plan, with no rule attached.
- **Readings fixed before the run:** designed after earlier results had been seen, with its possible readings written down before it ran.
- **Descriptive:** read by no rule.

Intervals are the committed ones at their corrected levels unless marked 95%; the post's figures redraw them at 95%. Paths are relative to `results/grid/analysis/main/` unless they begin with `results/`.

### 8.1 Aggregating

| post claim | value [interval] | standing | file, column |
|---|---|---|---|
| a recipient's own explanation sits 0.34 nats from the original | 0.3417 | registered description | `level_cells.csv`, `mean_kl`, row `main/E/ref/importances` |
| the complete decomposition, every component on and the residual left out | 0.0115 | registered description | same, row `main/E/ref/unmasked` |
| 1 token's worth (about 170 components): almost no effect | +0.0038 [0.0033, 0.0042]; 169 components | registered verdict: detected, not material | `union_E_D_unif_tau0.1_r0_excl_ctl-none.csv`, `excess`, `interval`, `n_on` |
| 8 tokens' worth (about 1,100) | +0.0402 [0.0383, 0.0420]; 1,121 | registered verdict: detected, not material | same |
| 16 tokens' worth: 0.1 | +0.1016 [0.0993, 0.1041], 95% | descriptive (size added after the curve was seen to cross 0.05 between 8 and 64) | `..._ctl-none__descriptive_rungs.csv` |
| 64 tokens' worth (about 4,500): +0.46, total 0.80 | +0.4575 [0.4444, 0.4722]; 4,544; total 0.7993 | registered verdict: material; the curve **fails** | `..._ctl-none.csv` |
| one whole donor text: total 0.83 | +0.4877 [0.4720, 0.5038]; total 0.8294 | registered verdict: material | same |
| harm crosses 0.05 nats at about 1,230 components | 1,227 (interpolated) | descriptive | `..._ctl-none__x_crossing.csv` |
| uniform random components do almost no harm | −0.0021, −0.0110 at 1 and 8 tokens' worth; +0.0397 at 64 | registered description | `union_E_D_unif_tau0.1_r0_excl_ctl-plain.csv`, `excess` |
| frequency-matched components do much less harm at small aggregations: the harm depends on which components come together | −0.0033 [−0.0036, −0.0031] and −0.0038 [−0.0047, −0.0029] against +0.0038 and +0.0402; reading *combination* | readings fixed before the run; a second, independently seeded set agrees | `fig7_marginal_control.csv`; `s7_marginal_closure.csv` |
| at large aggregations, frequency-matched components approach real donors, with 43% to 73% overlap | +0.025, +0.137, +0.377 at 16, 32, 64 (95%); overlap 0.43, 0.59, 0.73 by mask moved | descriptive; the rule was written not to read these sizes | `fig7_marginal_control.csv`; `results/grid/pre_reads/main/s7/marginal_overlap_by_rung.csv`, `overlap_mass_pooled` |
| 0.80 against the paper's 20-step adversary at 0.83 | 0.7993; 0.8280 quoted | descriptive; the paper's value is quoted, not re-measured | `s9/figures/fig1_merge_curve.csv`; the paper [1] |
| about twice as far as Pythia-70M | 2.03 [2.00, 2.06] | descriptive; the comparison model fixed before the run | `s9b/s9_yardstick_ratios.csv` |
| about three quarters of token positions rise by more than 0.05 at 64 tokens' worth | 0.7605 [0.757, 0.764]; 0.735 to 0.789 across draws | readings fixed before the run: the one number owning the words *on most positions* | `s9/check_d_positions.csv`; the interval and the range across draws in `s9/summary.json` |
| every one of the 1,024 recipients rises by more than 0.1 at 64 tokens' worth | 1,024 of 1,024; 1,023 above 0.2 | descriptive | `s9/check_d_texts.csv` |
| the all-or-nothing form: 0.036, 0.096, 0.48 against 0.040, 0.10, 0.46 | rises above their own starts (0.311 and 0.342); every size within a factor of two | readings fixed before the run: outcome A | `s11/s11_step1.csv`, `s11_step2.csv`, `s11_verdict.csv`, `s11_absolute.csv`; the fractional start, 0.342, in `level_cells.csv` |
| 2 and 4 tokens' worth: +0.010 and +0.019 (399 and 671 components) | +0.0101 [0.0094, 0.0107]; +0.0190 [0.0181, 0.0200] (95%) | descriptive, added after the fact, with predictions dated before the run | `s12/s12_merge_E.csv` |

### 8.2 Similar Donors

| post claim | value [interval] | standing | file, column |
|---|---|---|---|
| own explanation of code recipients 0.29, of prose recipients 0.43 | 0.2926; 0.4286 | registered description | `results/grid/main_s9/tier5/E_lab__same_domain/per_sequence.parquet`, the reference cell, by source |
| code donors into code recipients: material from 8 tokens' worth; general donors from 16 | +0.191 [0.152, 0.223] at 8; general +0.057 at 8, +0.128 at 16 | readings fixed before the run: same-kind donors first | `s9b/s9_run2_curves.csv`, `s9_run2_verdict.csv` |
| code donors barely touch prose recipients through 8 tokens' worth; prose donors harm code recipients measurably | +0.001 [−0.006, 0.009]; +0.028 [0.018, 0.046] | readings fixed before the run (the mirror strata of the same run) | `s9_run2_curves.csv` |
| closer is worse | $R$ = 2.98 [2.34, 3.78] at 64 tokens' worth | readings fixed before the run: *closer is worse* | `s9_run2_match_ratio.csv` |
| code donors cost code recipients 2.2 times what the general donors' curve predicts at the same amount switched on | observed 0.902 against predicted 0.415; log ratio 0.775 [0.528, 0.981] | readings fixed before the run: *above the prediction* | `s9_run2_count_only.csv` |
| code donors switch on fewer components than general donors at 8 to 64 tokens' worth | 975 against 1,121 at 8; 3,626 against 4,544 at 64 | label-only, fixed before the run | `results/grid/pre_reads/main/s9/summary.md` |
| the self-aggregation takes the model from 0.34 to 1.37; every text worse | rise 1.030 [1.005, 1.056]; total 1.371 | readings fixed before the run: material | `s9_run6_self_merge_rule.csv` |
| every text worse than under a stranger's aggregation | +0.455 [0.436, 0.475]; all 1,024 | readings fixed before the run | `s9_run6_self_against_stranger.csv` |
| the ladder on code: 0.57, 1.03, 1.40, at about the same component count | 0.570, 1.026, 1.397; 5,601, 5,250, 5,243 components | readings fixed before the run; the scope rule allows "within one kind of text" | `s9_run6_ladder.csv`, `s9_run6_scope.csv` |
| 2 and 4 tokens' worth; code into code already +0.10 at 4 tokens | e.g. C into code +0.043 and +0.101 [0.088, 0.113] (95%, over documents) | descriptive, added after the fact | `s12/s12_merge_E_lab.csv` |

### 8.3 Deleting

| post claim | value [interval] | standing | file, column |
|---|---|---|---|
| 9,966 of 38,912 components ever needed above 0.1 on the donor texts; 28,946 never; 5,336 exactly zero; about 10,000 alive | 9,966; 28,946; 5,336; 9,959 | label-only counts | `results/grid/pre_reads/main/summary.json`; `union_..._ctl-none.csv`, `n_on` at the whole pool |
| deleting 169 never-needed components costs 0.006; 169 random alive components 1.12 | 0.0060 [0.0058, 0.0062]; 1.120, and 0.11 to 3.0 over the draws (descriptive) | readings fixed before the run | `never_named_chain.csv`; the chain's `donor_chain.csv`; `s12/hard_delete_per_draw.csv` |
| 1,121 deleted: 0.05; 4,544: 0.30 | 0.0515 [0.0497, 0.0536]; 0.2974 [0.2875, 0.3085] | readings fixed before the run | same |
| all 28,946 deleted: 1.28 | rise 1.2841, output harm 1.2847; conditional damage 1.2830 [1.2655, 1.3016] (95%) | descriptive: first seen as the whole-pool end of the aggregation curve, during harness checks | `never_named_rung_8_cells.csv`, `unconditional`, `interval_0.1`; the output harm, 1.2847, in `results/grid/main/verify/comparisons.md`, item 4 |
| turning them down to their labels instead costs within 0.003 of the same | 1.2876 against 1.2847; identical at the same residual setting | descriptive; identity check | `level_cells.csv`; `results/grid/main/verify/comparisons.md`, item 4; `results/identities/h4_main.txt` |
| the 5,336 exactly-zero components cost 0.31 where their labels are exactly zero | 0.3131 [0.3032, 0.3237] (95%); 0.3262 over whole texts | descriptive | `never_named_rung_8_cells.csv`, `d_hat_0`, `interval_0` |
| with the used components at their labels, deleting the never-needed changes the output by 0.02; halfway 0.02; three quarters 0.13; fully on 1.28 | −0.0198, +0.0181, +0.1278, +1.2761 (95%); output harms 0.362→0.342, 0.195→0.213, 0.126→0.254, 0.011→1.288 | readings fixed before the run: *threshold* | `level_cells.csv`, `footprint_labels_minus_one`, `footprint_interval`, `mean_kl` |
| the 201 heaviest never-needed components cost 0.072, the 201 lightest 0.006; graded, not concentrated | 0.0724 (s.e. 0.0014) against 0.0064; lighter half 0.845, heavier half 1.174 | descriptive; the two orderings fixed before the run | `fig6_ranked_pair.csv`; `ranked_pair_top_minus_bottom.csv` |
| deleting what one code token needs breaks the model: over 11 nats | 11.68 at 198 components | registered description | `hard_zero_E_lab_D_code_tau0.1_ones_incl_ctl-none__tau_q0.1__all__donor_chain.csv`, `unconditional` |
| 1,007 code-leaning components, a quarter of what a code token needs | 1,007; share 0.248; the shuffle null far below its bar | readings fixed before the run: the existence rule reads *clear* | `results/grid/pre_reads/main/s7/code_leaning_groups.csv`, `code_leaning_null.csv` |
| on the labelled texts, deleting the 256 most code-leaning costs code 0.64, the twins 0.10; all 1,007: 3.24 against 1.10 (the post quotes the panels: 0.67 and 3.34) | 0.639 [0.576, 0.702]; 0.100; 3.24 [3.03, 3.44]; 1.10 | readings fixed before the run; the rule returned none of R1 to R3 | `s7_code_leaning_damage.csv`, `s7_code_leaning_readings.csv` |
| the edit exceeds its twins on code at every size read | +0.089, +0.54, +2.14 at 64, 256, 1,007 | readings fixed before the run | `s7_code_leaning_positive_control.csv` |
| web text and Wikipedia about 0.03 at 256 and 0.21 at 1,007; the twins hurt them six to eight times more | 0.026, 0.025, 0.213, 0.208; twins 0.171, 0.175, 1.371, 1.593 | descriptive (panels) | `s12/s12_panels.csv` |
| StackExchange 0.34 and 2.26 | 0.342, 2.262 | descriptive (panels) | `s12/s12_panels.csv` |
| much of StackExchange is code | 7 of 16 sampled texts read as code, 5 as mixed | descriptive (reader labels) | `results/data/reader_labels/labels_labeled_sample.tsv` |
| the labels cannot tell GitHub code from StackExchange | leaning share 0.15% and 1.7%, *none* both ways | readings fixed before the run | `s9b/check_b_panels.csv` |
| ArXiv: 0.26 and 2.68, more than twice the twins | on 200 passages from 162 papers: 0.262 [0.233, 0.292], $\rho$ 2.15 [1.88, 2.43]; 2.68 [2.42, 2.92], $\rho$ 2.48 [2.20, 2.76]; reads *keep* (the three-paper values 0.250 and 2.47 agree) | readings fixed before the run (section 6.4) | `s12/s12_panels.csv`; the three-paper values in `s7_code_leaning_damage_by_source.csv` |
| the post's code-edit bars and their twins | panel values, table in section 4.2.5 | descriptive (a replication, except ArXiv) | `s12/s12_panels.csv`; `results/post/code_edit_panels.csv` |
| plain-text math, biomedical papers, and legal text are hurt no more than by the twins; LaTeX markup the likely route | $\rho$ 0.78, 0.63, 0.19 at 256 members | descriptive; the three sources chosen before the run to separate the explanations | `s12/s12_panels.csv` |
| about 1–7% of non-code tokens covered at 256; almost none at 1,007 | 0.009–0.074 on the panels (0.047 on the labelled texts) | label-only | `s12/panel_coverage.csv`; `s7_code_leaning_conditional.csv` |
| soft-deleting one token's worth costs 0.45; eight tokens' worth 0.74; all used components 0.36 | 0.448, 0.742, 0.362 | registered description | `soft_erase_E_D_unif_tau0.1_r1_excl_ctl-none.csv`, `mean_kl` |
| every one of the 1,024 texts harmed by the soft delete | 100% above 0.05 at 1 and 8 tokens' worth | descriptive | same, `fraction_seq_above_X` |
| frequency-matched soft delete 0.42; uniform 0.08 | 0.417 [0.404, 0.430]; 0.082 | readings fixed before the run: reading *kind* | `s7_marginal_closure.csv` |

### 8.4 How Big Is a Nat

| post claim | value | standing | file, column |
|---|---|---|---|
| top prediction changes: 19, 38, 54, 26 percent | 0.185, 0.376, 0.538, 0.264 (exact ties excluded, 2.5% of tokens) | descriptive; the masks and statistics fixed before the run | `s9b/s9_plain_terms_listed_masks.csv`, `change_rate` |
| top prediction is the real next token: 48, 48, 40, 31, 47 percent | 0.483, 0.478, 0.399, 0.306, 0.465 | descriptive | same, `top_is_next` |
| among confident tokens: 2, 17, 37 percent | 0.019, 0.169, 0.371 | descriptive | same, `change_rate_confident` |
| Pythia-70M at 0.39; the 64-token aggregation about twice that, the deletion more than three times | 0.394; 2.03, 3.26 | descriptive | `s9b/s9_yardstick.csv`, `s9_yardstick_ratios.csv` |

### 8.5 The Decomposition Trained Without the Adversarial Loss

| post claim | value | standing | file, column |
|---|---|---|---|
| four to seven times the aggregation harm at the same amount of mask switched on, where aggregations do harm | 6.6, 5.6, 4.1 in the three ranges where its draws agree in sign | registered description, with the direction predicted in advance | `results/grid/analysis/control/compare_mass_matched_curve_1.csv`, `mean_this` / `mean_other`, bins 2 to 4 |

## 9. Limitations

- **One released decomposition of one small model.** Every number concerns the decomposition released with the paper, of a four-layer, 67M-parameter model, with the authors' decomposition trained without the adversarial loss as the only comparison. Nothing here was applied to other seeds, sizes, or the authors' newer training recipe.
- **The combination reading covers only small aggregations.** The frequency-matched comparison can tell kind from combination only at 1 and 8 tokens' worth, where the harm is still under 0.05 nats. It does not separate the causes of the material harm at larger aggregations (section 3.4).
- **The 0.05-nat line is borrowed.** It is the size of a difference the paper reports between two of its mask conditions. Where the aggregation curve crosses it, and which sizes the registered test calls material, depend on that choice. That the harm rises steadily from the first donor token and reaches the scale of the paper's own adversary by 64 tokens' worth does not.
- **The code-leaning group's existence rule has a weak null.** Any two distinguishable kinds of text would beat it. That the group concerns code rests on the edit itself (section 4.2).
- **Donors are random tokens and texts, not trimmed per-behaviour sets.** The paper's worked examples build small explanations for one prompt and one predicted token; the aggregations here use every component a donor token needs, drawn from general, code, or prose text. Aggregations within a single behaviour, such as bracket closing, were not tested. At about 170 components, the size of one token's explanation, the harm is small.
- **Output harm measures change, not capability.** A KL divergence says how differently the model predicts, not what it can no longer do. Section 5 translates it into prediction changes and loss, but no capability benchmark was run.
- **Intervals hold the donor draws fixed.** They describe uncertainty over texts, for these eight draws; the pass-or-fail rules add a sign condition over draws, and some comparisons report a two-level interval (section 6.2).
- **The freeze protected the interior of the first aggregation curve, not its ends,** which had been measured as harness checks before its analysis was committed (section 7, item 10).
- **The adversary comparison is an outside number.** The paper's 20-step adversary was not re-run here; its value is quoted.
- **Some labels of texts were assigned by language-model readers,** following a fixed rubric with measured agreement (section 2.4). They enter only descriptive statements.
- **The labelled texts come from a limited number of documents.** Intervals on them resample documents, and ArXiv's three papers carry no interval, which is why the code edit was re-measured on panels of many documents (section 4.2.5).
- **The editing guarantee is untested where it could fail.** For the code edit, faithfulness covers about 1% to 7% of non-code tokens at 256 components and almost none at 1,007, and where it was read, on the labelled texts at 16 and 64 components, the test could hardly have failed (section 4.2.3).

## References

[1] L. Bushnaq, D. Braun, O. Clive-Griffin, B. Bussmann, N. Hu, M. Ivanitskiy, L. Linsefors, and L. Sharkey. Interpreting Language Model Parameters (adVersarial Parameter Decomposition). Goodfire, May 2026. https://www.goodfire.ai/research/interpreting-lm-parameters

[2] S. Biderman, H. Schoelkopf, Q. Anthony, H. Bradley, K. O'Brien, E. Hallahan, M. A. Khan, S. Purohit, U. S. Prashanth, E. Raff, A. Skowron, L. Sutawika, and O. van der Wal. Pythia: A Suite for Analyzing Large Language Models Across Training and Scaling. ICML 2023. arXiv:2304.01373.

[3] Goodfire. `param-decomp`: Parameter Decomposition library. https://github.com/goodfire-ai/param-decomp, tag `vpd-paper`, commit `74146b5`.
