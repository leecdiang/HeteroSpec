# Scientific fidelity and prose review

Review method: the complete pinned Humanizer 4.0.0 skill and the actual writing-clearly-and-concisely skill plus its companion text were read before revision. See `method_sources/WRITING_SKILLS_PROVENANCE.md` for immutable sources. This report distinguishes reading from actual file changes.

## Completed edits: evaluation and results

The current `sections/04_evaluation.tex` and `sections/05_results.tex` were read in full, revised, and read in full again after editing. Copies before the edits and the exact diff are in `review/before_humanizer/` and `review/humanizer_04_05.diff`. The corresponding file hashes are in `humanizer_04_05_manifest.json`.

- Removed repeated concluding claims and scene-setting sentences that did not add evidence.
- Consolidated the meanings of D4, physical query width and Q8 weight type without losing the distinctions.
- Changed a table header from an asserted independent unit to its actual input/repetition unit, accommodating fixed structural coordinates as well as sampled roots.
- Replaced a potentially universal statement about preserving transactions with the measured statement that all comparisons pass at the qualified observation boundaries.
- Clarified that the Linux qualification covers four **target-only** cut/projection paths and two speculative paths for each family.
- Retained Bonferroni adjustment, paired-root dependence, incomplete six-arm order balance, tested-domain scope, all negative application outcomes, and intervals containing one.
- Preserved the distinction between the 32B service comparison against a graph-level loop and its subsequent operator comparison against the stronger backend-internal loop.
- Bound the A5000 B2 equal-work result to one exposed origin and four process clusters per cell, including mixed loop4 process directions.
- Synchronized the new width figure caption with its third panel's cycle, verified-row and proposal counts; phase-cost accounting remains in the prose and supplement.

Whitespace word counts, including LaTeX commands, change from 775 to 775 in evaluation and from 1,549 to 1,470 in results. Reduction was not itself a target; the revisions retain the evidence needed to interpret each result.

## Primary-source checks completed in this pass

The full Linux qualification report was read at the fixed repository revision:

<https://github.com/leecdiang/HeteroSpec/blob/701079f265c0ff8fd05d43fbc2d8d5054a711e1b/benchmarks/linux_transfer_v1/results_ampere_20261107/README.md>

It verifies 216 geometry plus 6,524 natural requested full-vector comparisons, totaling 6,740, and 4,784 active-state comparison records. Both Qwen and Smol pass four M paths and two D4 paths. These are finite recorded comparisons and do not establish a universal equivalence theorem.

The complete B2 report was read at its separate PR head:

<https://github.com/leecdiang/HeteroSpec/blob/4fe337a8ff349d547023f9dd60b8e114e5323207/benchmarks/server_expansion_v1/strong_baseline_followup_20261110/RESULTS_B2_20261110/README.md>

It records 16 fresh processes and 128 operations, half warmups and half measurements. Its four process-cluster geometric ratios are 0.990445, 0.978065, 0.936989 and 0.947566, on one exposed origin. Two warm operations per path do not establish convergence to steady state. The main text reports this as a diagnostic and does not infer live-k7 acceleration.

## Independent arithmetic verification

`CLAIM_ARITHMETIC_RECHECK.json` recomputes the numerical claims from the manuscript's existing data projections, without invoking the figure-generation code. It checks all three application reductions and absolute means, all eight direct factorial effects and interval directions, the two mixed-Q4 service reductions and 14.00% speculative excess, all four live-width ratios, both acceptance denominators, every LOCAL-packed phase difference, both Vulkan geometry ranges, and the 20/2,224 boundary frequency. All displayed rounded values agree.

This is independent arithmetic checking of existing projections. It does not rerun GPU inference or newly reconstruct the raw numerical captures. The separate figure reviewer checks the plotted mappings and source CSVs.

## Bibliography and format

All 16 bibliography entries have verified primary identities; five entries received metadata-only improvements. Official TPDS template selection and compatibility of the unmodified IEEEtran class are recorded separately in `method_sources/BIBLIOGRAPHY_VERIFICATION.md` and `method_sources/TPDS_FORMAT_VERIFICATION.md`.

## Completed full-manuscript pass

After the substantive writers released their files, the abstract, introduction, reference section, method, related work, conclusion and supplement were each read completely, revised and read again. `humanizer_remaining.diff` preserves the exact edits; `humanizer_remaining_manifest.json` records the versions at handoff. Later layout changes by the lead writer can legitimately change those hashes.

| File | Before words | After words |
|---|---:|---:|
| Abstract | 195 | 195 |
| Introduction | 705 | 568 |
| Reference/mechanism section | 1,011 | 897 |
| Method | 1,303 | 1,240 |
| Related work/discussion | 432 | 356 |
| Conclusion | 124 | 112 |
| Supplement | 3,262 | 3,120 |

These whitespace counts include LaTeX commands. Together with the evaluation/results pass, 481 words were removed from the main-paper files and 142 from the supplement. The abstract remains within the official 100–200-word requirement. No unique numerical literal was removed from the supplement, and all complete data tables remain.

The edits remove repeated framing, scene-setting and summary sentences, explain concrete operations directly, and shorten the introduction's repeated mechanism descriptions. They retain the bidirectional native extent intervention, fixed consumer query width one, the Vulkan extent/contiguity/dispatch coupling, the separate activation mechanism, CPU/CUDA RoPE placement, all eight-input producer observations, and the distinction between endpoint evidence and full numerical correspondence. They also preserve the conditional induction argument and every measured performance direction, including negative application results.

Specific clarity fixes include:

- Maximal equal-extent/arithmetic runs are formed **before** the per-call width bound is imposed. This gives the stated sum of ceiling terms; the wording no longer suggests that a run was already width-truncated.
- The Q8 packing comparison replaces successive backend invocations, without attributing removal of graph-level joining to a baseline that already moved that loop into the backend.
- The method preserves the corrected Vulkan mapping: p021 belongs to QK; AV retains the physical-range, stride and dispatch requirements.
- The execution flow table is introduced in the method, and the construction figure identifies the blocks as repeating across transformer layers.
- The 4,784 state comparison records are distinguished from the additional frontier-vector checks.
- S1/S2 operator-study stage names are distinguished from supplementary section numbers. The incomplete full-model strong-loop result is mentioned once; the completed B2 result remains fully reported.
- The supplementary B2 table uses the generated `\BTwoRows` macro requested by the build owner, avoiding a tabular-input expansion error.

The producer paragraph was additionally clarified at handoff and reread after the lead writer's edit: the **reference's producer semantics** are distinguished from a candidate's physical prefill grouping. CUDA candidates can regroup known prompt rows while preserving the UB1 producer's outputs and state. The resident Vulkan path retains its original UB128 producer calls. The composition argument starts from state matching the reference after the same logical phase history, rather than requiring the reference implementation itself to have produced that state. This clarifies the existing method and does not create a new experiment.

The lead writer's subsequent layout edits were checked: the physical-range figure is introduced and placed after the concrete introduction example; the method's execution-flow table has a text reference; the mixed-quantization passage uses a subsubsection instead of the unwanted fourth-level paragraph numbering; and the two long section titles are shortened. The main-paper and supplementary prose reviews are complete.

## Additional historical mechanism checks

The complete producer-boundary and CUDA placement reports were reread from the earlier immutable-source cache during this pass:

- <https://github.com/leecdiang/HeteroSpec/blob/701079f265c0ff8fd05d43fbc2d8d5054a711e1b/benchmarks/b570_producer_consumer_boundary_v1/RESULT.md>
- <https://github.com/leecdiang/HeteroSpec/blob/701079f265c0ff8fd05d43fbc2d8d5054a711e1b/platforms/rtx_reference_snapshot/benchmarks/rtx_reference_repair_v1/host_execution/RESULTS.md>

The producer study changes serialized KV and the initial vector jointly; its clearest two-input contrast concerns the emitted-token endpoint after a clean receiver. It does not isolate KV alone or qualify arbitrary later consumers. The placement study crosses identical normalized K operands between native CPU and CUDA RoPE executions, supporting the specific backend-placement statement. The rewrite retains these scopes without repeating a disclaimer after every paragraph.

## Handoff

All prose files are released to the lead writer for final layout, figure placement, compilation and draft-PR assembly. No GPU inference was launched, no original paper was overwritten, and no remote write was performed by this reviewer. The final PDF checks and draft-PR submission are handled by the lead writer.

## Final assembly record

The lead writer completed the final page inspection and clean-extraction builds.
See `FINAL_VALIDATION.md` for the finished validation and
`../REWRITE_EVIDENCE.json` for the delivered source/PDF hashes. The earlier
manifest hashes remain the record of the language-review handoff.
