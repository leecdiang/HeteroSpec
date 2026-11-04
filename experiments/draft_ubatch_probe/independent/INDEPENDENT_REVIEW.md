# Independent review: draft physical microbatch candidate

Verdict: acceptable as a local, unpublished source candidate and bounded CPU protocol fixture after the corrections below. This review does not qualify the Windows worker, CUDA execution, the frozen PR151 target route, a production fast path, or a speedup.

## Source and binding review

The final isolated intervention keeps draft output reservations at one and changes only its physical microbatch parameter to 1, 2, or 4. Both fresh and resident draft constructors pass the new parameter. The target constructor call sites and request accept/reject/correction/bonus/trim algorithm are unchanged. The shared Context assignment is changed, but retains the old effective target value; this is a source inspection, not a Windows execution result.

An independent inverse of every listed edit restores the entire exact frozen source for all three arms. The generated source file hashes match the manifest's actual bytes. Slot, plan, family binding, actual context width, and the distinct study identifier bind the width. Unsupported widths and changed source bytes fail closed. The final CLI also rejects CRLF-normalized copies rather than recording a misleading original byte hash.

Draft prompt prefill can use wider internal microbatches. DRAFT_SYNC and each PROPOSE remain singleton calls. Wider draft execution can change draft state, proposals, acceptance, target histories, allocation, and total work. No target numerical qualification or end-to-end performance claim follows from leaving the target source algorithm unchanged.

## Concrete problems found and corrected

1. The first intervention also changed draft output capacity. The final version separates physical width from the original output reservation of one.
2. A deliberately invalid fixture that terminated every request after the first output passed all 75 historical cases, with zero speculative cycles. Its endpoint oracle used actual output length. The final fixture independently asserts expected length, non-vacuous cycles, and the forced first-cycle branch. The same early-stop mutation now exits with the expected length error.
3. A deliberately invalid fixture that discarded all generated committed KV after producing the endpoint passed all 75 historical cases and 114 cycles when its reference state followed the same mutable history. The final fixture derives the committed prefix independently from output tokens and the terminal accepted/correction/bonus branch, checks the actual frontier, and uses that independent prefix for state and continuation comparisons. A mutation inserted after the frontier assertions is now rejected with serialized-state mismatches in 57 of 75 cases.
4. The original CLI used text newline normalization, accepting a CRLF file whose raw SHA256 differed from the claimed pin. The final CLI preserves input bytes and writes output bytes, and the negative check rejects the CRLF file before creating an output directory.

The two invalid native fixtures are retained under historical/. They demonstrate old validation gaps, not a defect discovered in the production acceptance arithmetic. They must never be treated as valid implementations.

## Independently reproduced evidence

Using the unmodified candidate CPU libraries, the final native fixture passed 75 distinct cases and 114 speculative cycles on each of four separately identified synthetic models: original F32, original Q8, norm-strengthened F32, and its Q8 derivative. Each run reported 367917 low-level checks, mostly individual finite-logit assertions. That count is not a count of independent scenarios. Repeated runs do not multiply the case coverage.

The fixture checks full target verification vectors, endpoint IDs and expected length, nonterminal pending tokens, independently derived committed-sequence serialization, continuation, and target/draft reset. Target physical ubatch is one, with output reservation four to retain the four verification rows. This is not the scoped target ubatch-four route. Target and draft use the same synthetic model within each run. The stop condition is a synthetic output-index predicate, not tokenizer EOG classification. Only the test executable is UBSan-instrumented; the linked runtime libraries are not.

Model sensitivity is a material limitation. For six prefixes ending in token 1, the original Q8 fixture returned identical 128-element logit vectors for every prefix. Original F32 differences were only about 4.4e-9 to 9.3e-9. The independently verified stress F32 model changes exactly five norm-weight ranges to one, leaving every other byte unchanged; both stress models show nonzero differences in four of the five non-reference prefix probes. Stress Q8 reaches about 6.66e-4 and F32 about 1.16e-4 maximum absolute difference.

That improvement is not comprehensive fault sensitivity. For both original and stress Q8, the committed-state-loss mutation still passed every continuation-logit comparison; it was rejected by serialized-state comparison. The continuation check is therefore not independently adequate for that corruption. Sequence serialization also excludes inactive padding and other hidden backend state.

## Remaining qualifications

No Windows worker compilation, actual two-model pairing, GPU numerical comparison, performance experiment, native EOG classification, exhaustive context-length/model coverage, decode-failure recovery, free-padding equality, or asynchronous lease/transaction proof was performed. Future CUDA arms must preserve the frozen target contract against the actual forced prefixes and retained state they generate. A mismatch must reject qualification. These local CPU results do not authorize an optimized target path.

Exact reviewed source, model, library, and artifact hashes are in SUMMARY.json and SHA256SUMS. The original and stress results are kept distinct.
