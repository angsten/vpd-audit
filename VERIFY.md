# Verifying This Repository

## What This History Can and Cannot Show

**What this history can and cannot show.** This repository's history was condensed into two commits for publication: the code, data, and texts, then the outputs regenerated from them. It shows that the committed code reproduces every committed number from the committed stores. It cannot, by itself, show the order in which the rules, the analysis code, and the measurements were written. The report states that order (section 7, items 9 and 10), and it rests on the working history, which is not published.

## The Clean-Up, and Why It Changes No Number

After the analyses ran, the code's comments, docstrings, and some message strings were edited to remove references to internal working documents. The result files that carry such text were then written again from the edited code: the analyses and figures were re-run from the committed data, and the launch summaries of the GPU stores were rebuilt from their stores by `vpd-audit resummarize`.

For every Python file, the syntax tree with its docstrings removed is the tree of the code that produced the results, except for these listed changes:

1. **Message and report strings.** Citations of internal documents were removed from log lines, assert messages, help texts, and report lines. The numbers and fields in them are unchanged.
2. **Names.** A few identifiers, dictionary keys, and test names that referred to internal documents were renamed, and one results directory was renamed to `s9b`. Every reader of a renamed key was renamed with it, and the committed files that carry a renamed key were edited to match.
3. **Recorded paths.** The analyses record the paths of their outputs relative to their output directory, and of their inputs relative to the repository root, so an output file is the same wherever it was written. They assert that no recorded path is absolute.
4. **A new command.** `vpd-audit resummarize` rebuilds a finished launch's summary from its stores: the preconditions P1 to P5 are recomputed from the stores and must equal the launch's, and only the text is rebuilt from the current code. It uses `grid.launch_title` and an optional `strata` argument of `grid.preconditions`.
5. **The recorded harness modules.** `RECORDED_AT` and `RECORDED_MODULES` in `vpd_audit/s9_checks.py` name this repository's commit and its blobs.
6. **Four tests dropped.** Four tests of the small stand-in's dry run were dropped with their fixtures, since the stand-in's stores are not included.

**Every change to a frozen analysis module beyond comments, docstrings, and message strings:**
- the path writers of item 3, in `analysis.py`, `analysis_s9.py`, `figures.py`, and `figures_s9.py`;
- in `stats.py`, the constant of the correction count, now `REGISTERED_CORRECTION` (a rename; its value, 8, is unchanged);
- in `figures_s9.py`, the constant of the `s9b` directory, now `S9B_DIR`, and that directory's name;
- in `analysis_s9.py`, one output key of the stranger consistency check, now `committed_value_on_the_papers_run`;
- in `analysis_s11.py`, the constant of the comparators' table, now `REGISTERED_COMPARATORS`, and its output key, now `registered_table`.

Re-running the analyses from the committed data reproduces the committed tables.

## The Digest Table

One row per module of `vpd_audit/`:
- **Blob recorded when the analyses ran:** the git blob of the module as the analyses' own reports recorded it before the clean-up. The reports in this repository were regenerated from this repository's code, so they now record the public blobs.
- **Public blob:** `git hash-object` of the module in this repository.
- **SHA-256 of the normalised syntax tree:** parse the file with Python 3.13's `ast.parse`; remove every statement that is a lone string constant (docstrings included) from every statement list, putting `pass` in a body left empty; take `ast.dump(tree, annotate_fields=True, include_attributes=False)`; hash its UTF-8 bytes with SHA-256. The first 16 hexadecimal digits are shown.
- **Tree as before the clean-up:** "yes" where the normalised tree equals that of the code that produced the results, "listed changes" where it differs only by the changes listed above, "new file" for `resummarize.py`.

| Module | Blob recorded when the analyses ran | Public blob | SHA-256 of the normalised syntax tree | Tree as before the clean-up |
|---|---|---|---|---|
| `__init__.py` | not recorded | `10ac82232620` | `3f6a1f648ea5f05a` | yes |
| `acceptance.py` | not recorded | `7eb114f68b56` | `92288dfa9c9c7108` | yes |
| `analysis.py` | `3e68657f037e` | `3a1d9a38168e` | `d6ba41ba0f1158a4` | listed changes |
| `analysis_s11.py` | `78eedb35cd72` | `38efee525f14` | `ce5b0e833cf5fee6` | listed changes |
| `analysis_s12.py` | not recorded | `ba9b5036bccf` | `fb22891e3bbaac55` | listed changes |
| `analysis_s7.py` | `c465798b797b` | `e64f29c7a9f0` | `f3c7401142c48c94` | listed changes |
| `analysis_s9.py` | `52512efbccf4` | `75566fd14e23` | `6a9d26d3fab91d24` | listed changes |
| `artifacts.py` | not recorded | `1f65cb5ea95f` | `70cdd0313d2f38f5` | yes |
| `cells.py` | `2413aa558750`, `777c246aadf6` | `3adca95be884` | `cebd09f50e498b4d` | listed changes |
| `cli.py` | not recorded | `7ced327f2dd9` | `85b2778decdc9596` | listed changes |
| `code_leaning.py` | `087b16d2280f` | `1e6c637a871f` | `655d4f1ba1680550` | yes |
| `codefilter.py` | not recorded | `b99359c1feb7` | `18e349a7c3641de8` | listed changes |
| `constants.py` | not recorded | `56cd4bf70fbe` | `932bd98809616a4b` | yes |
| `data.py` | not recorded | `c8cf87f0977a` | `ce2d697afce9fe91` | listed changes |
| `donors.py` | not recorded | `b6aee296c34e` | `061c4a5b4a4105f5` | yes |
| `dry_sets.py` | not recorded | `24789241e819` | `816f6722e8b383c4` | yes |
| `env.py` | not recorded | `28cdf6859d23` | `3064dcf4eef4054a` | listed changes |
| `external_models.py` | not recorded | `92ff29fd76f2` | `0dfceb5a2b76be43` | yes |
| `figures.py` | `40a3bad3b53d` | `217421d76651` | `33c4533df297e38f` | listed changes |
| `figures_post.py` | not recorded | `97e9a969575c` | `a98725ab5161a378` | listed changes |
| `figures_s7.py` | `251a6c478959` | `b1d5eab36864` | `2274a9c9b8c058f8` | yes |
| `figures_s9.py` | `ed28ff7bfe09` | `7a8a3b812544` | `9052cecb9e2a6116` | listed changes |
| `fingerprint.py` | not recorded | `a62e516ac8e0` | `ec685b9da164841c` | yes |
| `grid.py` | `0cc5f8eab632`, `507f55f013b5` | `3186e4405db1` | `245c97c7f09b2948` | listed changes |
| `h4.py` | not recorded | `c9a586787e99` | `58164664fe73dcc9` | listed changes |
| `identities.py` | not recorded | `7d643426601a` | `595abef68eabcf9e` | yes |
| `importances.py` | not recorded | `0c64dbc23a41` | `5419bad7d8dec358` | listed changes |
| `level_check.py` | not recorded | `c2e8ad5d1d64` | `46fe9ea764c2beb9` | yes |
| `masks.py` | `6fda9d806b09` | `9e332b8d142e` | `a7f78f9485efbf56` | yes |
| `metrics.py` | not recorded | `94f3ef64a4eb` | `5d94fbbc4aea50ec` | yes |
| `modal_app.py` | not recorded | `410958e586eb` | `796d198072e30229` | listed changes |
| `plain_terms.py` | not recorded | `612980baeca7` | `c39ac6abc87e260c` | yes |
| `post_tables.py` | not recorded | `546f8a467afd` | `bf36ff2d1c4e07c9` | yes |
| `pre_reads.py` | `7d8b9f23e719` | `879ad795fc63` | `23d8d3b385043b9b` | listed changes |
| `reference.py` | not recorded | `b377f5bf7b12` | `e7ea09931bd4c340` | yes |
| `residual_matrix.py` | not recorded | `fb9188cd9d96` | `7797df3defa3a7de` | listed changes |
| `residual_rank.py` | not recorded | `d18348e39861` | `44b649b5512a1fe1` | listed changes |
| `results.py` | not recorded | `84073f93737a` | `f252648035d2997c` | yes |
| `resummarize.py` | not recorded | `3f4a4e5ec0d6` | `b79db1d08a6c52fb` | new file |
| `roundtrip.py` | not recorded | `30874e9564de` | `d92bf8f36950ea7a` | yes |
| `s12_labels.py` | not recorded | `e99d524ccdcb` | `c4909c1a8546518e` | listed changes |
| `s7_checks.py` | not recorded | `3d1682e085ef` | `d755c4c02983dab4` | listed changes |
| `s9_checks.py` | not recorded | `aa68bd049779` | `8dd01c1075e49ea9` | listed changes |
| `s9_panels.py` | not recorded | `29142ad0e499` | `b54172197de72e0a` | listed changes |
| `s9_pre_reads.py` | not recorded | `bd25cf5ea188` | `b7e2f8095588728c` | listed changes |
| `short_runs.py` | not recorded | `5ce21607a6d3` | `a27469328e208f26` | listed changes |
| `smoke.py` | not recorded | `872cb35f65a8` | `5817674b04d1ddcc` | listed changes |
| `sources.py` | `87e4262eec50`, `ebec8683e876` | `bd7256908f36` | `50f8313389c804c2` | yes |
| `stats.py` | `a00812ba43cf` | `5c6e1afc019a` | `db8214266ee0841a` | listed changes |
| `stats_s12.py` | not recorded | `eab36824e48d` | `71b73cba681a71fd` | yes |
| `stats_s7.py` | `8986ed426430` | `849ae0a462f6` | `16753fff1162ca56` | yes |
| `stats_s9.py` | `5f72136d898e` | `eb16c45c6a65` | `b48cb1475ff08e2d` | yes |
| `tier5.py` | `bb53d5464e3b` | `3fd44ccb4f83` | `fca439cfbe32df28` | listed changes |
| `tier6.py` | `5983639d882d` | `b8d61a43f0d9` | `0db5ac25c6fc206e` | listed changes |
| `tier7.py` | not recorded | `e52674bc86df` | `157f1fde87dca599` | yes |
| `timing.py` | not recorded | `9ec935cae227` | `cc422f658af029e4` | yes |
| `two_paths.py` | `5086fca70073` | `f4b2b9fe01a1` | `b8d6e8a1ac180d6d` | yes |
| `verify.py` | not recorded | `f6f4f52d0814` | `a58f4d76b0e3e5c8` | listed changes |
| `weight_norms.py` | not recorded | `a4c509e8ddd5` | `1d85e572e8a7ad4e` | yes |

Where two blobs were recorded for a module, the module was extended between two analyses. Every blob recorded for a frozen analysis module is the blob of the code the clean-up started from.
