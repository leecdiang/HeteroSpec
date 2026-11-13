# V3 targeted language review

## Scope actually read

Read the complete current main manuscript source (title/abstract, introduction, method, implementation, evaluation, results, related work, discussion, conclusion and declarations) and all three supplementary section files. Read the existing pinned humanizer-workflow record, including its limits; this is continuation of its factual-preservation editing procedure, not a claim of an AI-authorship test or fresh use of an unavailable skill. The historical mechanism evidence is being checked independently by the other reviewers; this edit did not replay native experiments or independently recalculate timing statistics.

## Files edited

- `paper/sections/08_discussion.tex`: replaced the speculative “can matter … maintenance effort” argument with what the 1.51% measurement establishes after shared activation quantization. The motivation remains a set of plausible development scenarios, with no production-demand or ROI claim. Replaced the generic cost paragraph with a measured-scope synthesis: S3 prefill versus decode, Q8 k=3 verification below multi-group packing width, and boundary opportunity/surrounding work/additional computation. Backend-transfer requirements, finite qualification, service failure boundaries, root-level uncertainty, small samples, and unmeasured hardware quantities remain.
- `paper/sections/09_conclusion.tex`: replaced “small but measurable” with the exact 1.51% target-only resident-service result and the scalar-loop control. Identified the a=1 whole-call instance and prefill concentration. Closed on the execution freedom between groups, required outputs/state, and opportunity versus added work. Kept the stated-backend-conditions qualification without repeating a universal-proof disclaimer.

No other manuscript file was changed by this reviewer. No measured data, confidence interval, citation key, model identity, source or title was altered.

## Precise suggestions for the integrating author (not applied here)

1. **Results, application subsection.** Replace the first sentence with: “The three A5000 Q8 application panels improve on all four target-only controls.” This binds the positive statement to its actual cohort; the B570 counterexample in the next paragraph remains visible. If “applications improve” seems less precise than an explicit measured object, use “In all three A5000 Q8 application panels, the complete speculative path reduces resident-service time relative to each of the four target-only controls.”

2. **Results, modern operator subsection.** Remove the two main-text sentences describing the failed earlier CPU-round-to-nearest oracle and subsequent redefinition. The supplement already preserves this chronology and its fixed source. Keep the 0.612924 ratio, interval, single-input 4096×4096/q=8 scope, 38.7% operator interpretation, and 32,766/32,768 different output patterns. Replace the last paragraph with a direct distinction, for example: “U supplies a faster extracted operator when the numerical reference can change. Full default-backend qualification and paired service timing have not been run. The legacy-compatible C and C1 candidates take 1.1264 and 1.0261 times B's complete-operator time in their separate sessions.” Details of contracts and resource limits already have an appropriate supplementary table.

3. **Main factorial caption.** Delete “Intervals spanning one are visibly retained.” It describes editorial conduct, not the experiment. The caption already identifies the estimators and intervals. If a reading aid is needed, name what a ratio below one favors after checking the final figure labels.

4. **Main physical-range caption.** Once the new Vulkan evidence paragraph states the joint extent/contiguity/dispatch repair, place that limitation there and shorten the caption to the CUDA intervention itself. Retain the one-query/768–1024 setup and full operator-output comparison; these are essential scope. Avoid repeating the same joint-intervention warning in caption and body.

5. **Supplement, historical geometry caption.** Replace “Every recorded cell and its inside control is retained” with a description of paired crossing/inside controls. Preserve the unmeasured-cell convention and descriptive statistical scope. The purpose is to explain geometry-sensitive reversals, not reassure readers that unfavorable points were kept.

6. **Supplement, modern-operator final paragraph.** Keep the failed oracle, unrun service status and source identities. Remove the final audit-style sentence about retaining faster and slower results together. The actual juxtaposition in the figure already conveys the engineering choice.

## Boundaries checked after editing

- The S3 control remains a shared-quantization backend **scalar** loop, not the Q8 loop4 control.
- The 1.51% observation remains one A5000 Qwen3-32B target-only deployment, with a=1 and whole-call cuts.
- The synthesis is explicitly about the measured experiments; it does not predict all speculative deployments.
- The conclusion does not credit draft-model gains to the construction or claim modern-backend service superiority.
- The discussion retains the distinction between backend arithmetic conditions and finite empirical qualification, root-level inference and repetitions, source-derived counts and measured hardware performance, and descriptive pilots and workload estimates.
- No production ROI, measured maintenance cost, universal bitwise theorem, or author-confirmed declaration was introduced.

## Integration checks still required

Compile and inspect the changed pages in the final CAS PDF. Verify that main-text cross-references to the new historical tables resolve, and that the shorter modern-operator text still leaves the failed-oracle history in the supplement. A final full-draft read should check that the new historical paragraphs replace repeated explanation rather than creating additional repetitions.
