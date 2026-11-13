# Data included for figure and table reconstruction

This directory contains public numerical evidence copied from immutable source
versions. No model weights, captured tensors, KV payloads, company credentials,
or private absolute paths are included.

## Representation and limits

- `closeout/` supplies public timing rows, plans and original statistical results
  for the Q8 application/factorial panels and the S3/natural service panels.
  Root identity, arm, and repeated session or round are retained.
- `pr218/PER_ROOT.csv` is an independent published check of the S3 root ratios.
- `pr222/` preserves the earlier author package's public numerical inputs.
  Some are original timing rows, some are complete root-level sums, and others
  are source-report projections. Their own `scope`/`input_level` fields identify
  that representation. For example, B570 supplies all 108 scalar timings but
  does not reconstruct complete native traces; equal-work q8 supplies 32
  origin/path aggregate times representing 128 operations, not 128 individual
  event samples. Historical geometry uses reported ratios without a new CI.
- `pr230/`, `pr234/`, and `pr237/` retain the extracted RTX operator timing rows.
  Their independent unit is one captured input, measured in separate sessions;
  repeated blocks are not independent workload samples.
- `derived/` is output from `scripts/build_figures.py`, not an original source.
  It contains the four natural paired comparisons and all fifteen fixed
  application contrasts with exact timing/interval source references.

The 47 baseline source files are byte-preserving copies with SHA-256 checks. Git blob
identities are retained for the 24 paper-source inputs. The exact URLs and
versions are in `../generated/figure_source_downloads.json`; per-figure subsets
also appear in `../generated/figure_manifest.json`.

The package reconstructs the published statistics and figures. It does not
provide the unavailable or separately held native full-vector/KV captures and
does not claim a fresh numerical qualification of the models. Authors must
confirm the broader research data-availability statement before submission.

## Revision 2 additions

The 47 baseline input files remain byte-identical to the #243 review commit. Five additional public fixed-version records are stored under `v2/`: the S3 phase account, the natural-history reconciliation, the source-derived local-cost report, modern-U compiler resources, and the original live-width arm analysis. Their full commit, Git blob, SHA-256 and direct URL are in `../generated/figure_sources_v2.json`; the original source manifest remains in `../generated/figure_source_downloads.json`.

The history report contains short public token/text excerpts explaining the canonical-history transition. It does not contain the full conversation corpus. Original native tensor archives, company-restricted records, model weights and pruned temporary data are not added. New derived summaries in `generated/` are CPU explanations, not new experimental measurements.
