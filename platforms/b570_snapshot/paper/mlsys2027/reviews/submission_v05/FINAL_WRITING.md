# Final independent writing review

Reviewed the revised abstract, Sections 1–10, the full separate appendix, and headline/runtime/evidence table captions as a paper before reading any other review or evidence report. No manuscript edits made. This is an independent prose audit; no Humanizer skill was used.

## Assessment

The narrative is coherent and appropriately bounded. The abstract distinguishes retrospective cases from separately frozen runtime studies, reports the stronger fixed-speculation point estimate, and disclaims an incremental control advantage. Sections 6 and 7 now connect the two measured constraints to qualification and continuation decisions without presenting a cross-platform ablation chain. Historical text-path agreement is explicitly separated from direct generated-ID equality in the framework, methods, limitations, appendix, and relevant captions. The guard is clearly one-way, request-local, fixed-width, and configuration-scoped; its timer boundary, calibration reference, decision schedule, and information restrictions are stated. No major scientific wording blocker found.

## Tiny recommended replacements

1. **Section 7, guard decision schedule — grammatical repair.**

   Original: `The selected rule first decides after \RTRounds\ completed speculative rounds, margin \RTMargin, then a decision after every later round while speculation continues.`

   Replacement: `The selected rule uses margin \RTMargin\ and first decides after \RTRounds\ completed speculative rounds, then decides after every later round while speculation continues.`

   Reason: completes the second predicate and attaches the margin unambiguously to the rule. No policy change.

2. **Appendix, Runtime Study Reproducibility — align the calibration comparator name with the main text.**

   Original: `Calibration selects the exact candidate with the lowest geometric-mean oracle regret.`

   Replacement: `Calibration selects the exact candidate with the lowest geometric-mean latency ratio to the offline oracle.`

   Reason: the manuscript otherwise defines a latency ratio and explicitly distinguishes it from a regret guarantee. Calling the same quantity “oracle regret” briefly introduces an unnecessary technical ambiguity. Preserve any historical internal field names in the evidence artifacts.

3. **Section 5, execution-path qualification — identify the recorded comparator at the point of failure.**

   Original: `The intended fast HumanEval execution nevertheless fails the frozen token-equivalence gate.`

   Replacement: `The intended fast HumanEval execution nevertheless fails the frozen text-path comparison gate.`

   Reason: the surrounding section and framework establish the historical RTX comparator; repeating its type avoids a momentary direct-ID reading of “token-equivalence.” This does not alter the reported failure or subsequent numerical reproducer.

4. **Section 4, M4 outcomes — repair an ambiguous pronoun.**

   Original: `It does not establish general M4 profitability or isolate unified memory as its cause.`

   Replacement: `These outcomes do not establish general M4 profitability or isolate unified memory as a cause of the profitable result.`

   Reason: “It” follows a sentence about profitability not being a hardware capability property, while “its cause” lacks a crisp antecedent. The replacement preserves the same causal limitation.

## Optional, lower priority

- Abstract: `correctness qualification can exclude cheap verification` could become `correctness qualification can exclude cheap verification paths`. This makes clear that an execution path is excluded, rather than verification being omitted.
- Section 5: `Exact subsets may be descriptively useful` could become `Matching subsets may be descriptively useful` in the B570 discussion, maintaining the local text-path vocabulary. The comparator is already explicit nearby, so this is optional.

## Retain as written

- The abstract’s “four ... case studies” remains understandable as four consumer systems, with separate M4 workload studies and later runtime experiments described explicitly.
- “Guard is profitable against target-only” is scoped to the held-out workload; the text does not claim that the control decision improved performance.
- “Fixed speculation has the higher aggregate speedup point estimate” correctly avoids implying a tested significant Guard–Always difference.
- The explicit exclusions of policy transfer, risk reduction, threshold optimality, persistence benefit, and a universal oracle lower bound are scientifically useful and should not be removed solely for stylistic brevity.
- The provenance exception is plainly disclosed without claiming uninterrupted validation.
