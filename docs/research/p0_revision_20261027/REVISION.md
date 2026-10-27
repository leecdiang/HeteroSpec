# P0 manuscript revision and independent review

Date: 2026-10-27. Baseline: PR145 at `85b3f2d6e43ea7d19fb4b0f6827cbd7f492f6fdb`.

The author authorized three P0 changes, independent post-change review, and separate RTX and B570 experiment PRs. This checkpoint completes the manuscript changes. It adds retrospective analyses of existing records; it adds no model executions, timing observations, independent hosts, or new input coverage.

## What changed and why

1. **E2 now directly reports local drafting economics.** The unchanged 1,620-row request source yields 864 local-arm measurements and 216 complete family/input/session quartets. Equal-input and equal-session log contrasts give QB draft ratios `T_M/T_C` of 1.083666 for Qwen3, 0.596931 for SmolLM2, and 1.105048 for Llama. All six sessions retain each family's direction under both PQ and QB. New pointwise t5 intervals and layout-by-draft contrasts are explicitly retrospective and exploratory. E2 uses the same exposed panel and contains no GS arm, so it does not independently replicate the complete scope-by-draft interaction. The registered PQ/QB bootstrap analysis remains unchanged.
2. **The original seven-arm cost comparison gains an authenticated work audit.** The audit reopens 2,058 original records, including 2,016 formal requests and 42 warmups. The formal requests form 288 matched seven-arm audit groups. Within target-only and speculative paths, all 576 GS/PQ/QB triples agree on the 33 recorded logical/decision/histogram fields. PQ/QB also agree on all 50 workload fields; GS intentionally changes physical graph work. Endpoints agree with the matched R records. The published projection, source bindings, reconstruction script, original counter headers and build mapping make these statements inspectable. Matching is retrospective: the actual campaign used 42 arm workers with 48 formal slots each, not 288 adjacent randomized seven-arm executions.
3. **The narrative leads with identified interventions and uses joint policy selection.** The named GS/PQ/QB experiment now leads the results. Historical M3/C3 qualification moves to Supplement S2 with its identity limits intact. E2 local draft decisions precede QB's incremental benefit. The selection rule compares observed complete-request cost over qualified repair/layout/draft combinations under a fixed service contract; it does not assume separable effects or a globally optimal greedy sequence. Reference conditions are centralized, while the Llama transfer counterexample, SmolLM2 draft cost and k1 failures remain visible.

The manuscript's contribution remains runtime/graph integration and the measured relationship between repair scope and draft profitability. This revision strengthens evidence and interpretation without adding a new attention algorithm or a universal reference-preservation claim. Complete-request savings are not an operator-time decomposition or a decode-only measurement.

## Independent review and response

Two independent task-level reviewers, neither of whom wrote the revised prose or the new analysis code, evaluated the revision. The statistical reviewer independently recomputed E2 estimates and intervals and reopened the original seven-arm records. The argument reviewer compared baseline and revised claims, read the actual campaign plan, and assessed the value and identifiability of proposed platform experiments. Across these reviews, six review/writing skills were applied; the reports explain their use.

Both conclude that the revision is substantively stronger within its stated scope and can update PR145. Neither found an unresolved blocking or major mandatory issue. They are internal AI-agent reviews with separated author/reviewer responsibilities, not external human peer review or an acceptance decision.

See [the statistical review](INDEPENDENT_STATS_REVIEW.md), [the argument review](INDEPENDENT_ARGUMENT_REVIEW.md), and [the itemized response](REVIEW_RESPONSE.md). All mandatory wording findings were corrected and read back. The statistical reviewer also checked the final caption-only generator change and refreshed its final source snapshot.

## Reproducible artifact

- [Final 28-page PDF](HeteroSpec_P0_20261027.pdf), including the 39-entry regenerated bibliography and supplement.
- [Final QA record](QA_FINAL.json): successful build, 543 data checks, 53 analysis/mutation tests, and all 28 rendered pages inspected.
- [Source preservation manifest](SOURCE_PRESERVATION.json): all 189 baseline files authenticated; no deletions; all 128 original ancillary files other than the edited checker preserved byte-for-byte.
- `paper/arxiv_v4_candidate/scripts/generate_e2_draft_profitability.py --check` verifies the new E2 outputs.
- `paper/arxiv_v4_candidate/scripts/generate_seven_arm_work_audit.py --check` verifies the compact audit; optional `--raw-root` and `--parts-dir` paths verify original records/selected archive parts.

The three downloaded archive parts were authenticated individually. The entire nine-part archive was not downloaded or rehashed in this task. The compact projection and part verification must not be described as a new whole-archive download. The independently reviewed audit documents this custody boundary.

The source build is `python3 -B scripts/build.py` from `paper/arxiv_v4_candidate`, with a TeX installation providing `elsarticle`. The final build in this workspace used the official elsarticle class as an external TeX dependency. Build logs retained here are the actual final outputs, not predictions of a future build.

## Separate next experiments

The RTX work package tests GS/PQ/QB by draft on/off on the fixed PR144 Qwen/Smol transfer panels over three actual dates, with nearby arm blocks; bounded Llama diagnostics are separate from formal timing. The B570 work package tests producer-conditioned Qwen consumer behavior with consumer-specific restoration controls and a 152-request default budget. Each receives its own experiment PR stacked on its platform's existing material-delivery branch.

These experiment PRs contain protocol, CPU planning/validation tools and explicit native implementation handoff. Their new GPU results are **NOT_RUN**. Native worker changes, compilation and qualification are host-side prerequisites and are not claimed as completed by this manuscript revision.
