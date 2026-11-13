# Mechanism repair, then independent confirmation

## Question
Can a uniform producer/operator rule remove the two 14B shared-reference failures while preserving useful query parallelism and full-request benefit? The test is not whether a new paragraph can explain the failure. Development may iterate; final confirmation cannot be tuned after seeing its outcomes.

Frozen reference: original PR156 Qwen3-14B Q8_0, original 0.6B Q8_0 draft, original 21 numerical DLLs, target weight offload24, threads24, context1024, F16 KV, non-flash, greedy cap128/native EOG. Target hash `a0dfe649137410b7d82f06a209240508e218f32f5b6fd81b69d6932160cfcd9d`. PR156 remains a closed 40-request negative experiment; none of its bytes or claims is rewritten. New study: `rtx_reference_repair_v1`.

## Competing explanations and informative interventions

1. **Producer state:** compare native bulk prefill, one-token API prefill within the existing UB4 context, and actual UB1-reference prefill with complete sequence-state and initial-logit handoff. P1 is not assumed equivalent to UB1 R. Also send candidate-produced state to a reference consumer. Own-path import/export must pass first.
2. **Numerical path:** with known matched logical prefixes, observe selected normalization, projection, RoPE, attention, residual/FFN and output tensors. Record actual scheduler assignment and source descriptors. Equal token prefixes do not imply identical internal operands. Use controlled replacement or fixed-operand replay before asserting the first causal operator.
3. **Repair locality:** apply row lowering only to an evidence-supported dense operator family across all layers/inputs. The implementation keeps the old single-column call and forwards caller precision. It does not prove same kernel selection/accumulation on every backend. Check actual output and placement. Norm/elementwise or fused paths may require a different general repair; document that change rather than forcing the supplied hypothesis.
4. **Transaction/state:** the native proposal/acceptance/correction/bonus/trim code is inherited. Check pending ownership, initial logits, effective KV and positions. Fix a real common transaction defect if discovered, in a new version, with regression and an unchanged original R.

## Development/confirmation split

Development uses all four PR156 pilot inputs, including both failed math cases and both passing code controls. They are already exposed and may be inspected repeatedly within a shared finite budget. Do not fit per-input thresholds, output positions, model-name exceptions or cached answers. Diagnostic positions/layer filters are allowed for localization; they must not control candidate semantics.

First development pass: baseline 40; R own-path state restore sham8; P1 32; RSEED32; reverse BSEED→reference8 = **120 requests**. The baseline may reproduce the old failures; this is expected and does not cancel repair work. R_NEW must still preserve the original reference. Check import format and observer effects before interpreting a cross.

Up to152 additional development requests (272 total) support focused tracing, family-rule candidates, controls and engineering recovery. The agent chooses these adaptively on the exposed development set and records its reasoning. This is not a preregistered performance-confirmation estimate, and no development speed winner may select the final rule. If more development is genuinely necessary, report the concrete unresolved mechanism and propose an additional budget before native execution; do not reset this ledger.

The twelve PR155 prospective natural inputs remain unopened at the output level. Preserve their source and formatted tokens. They cross code/math with128–384/512–768 lengths,3 per stratum. Freeze one general implementation, producer policy and row family set before their first output. Each input runs original R, rebuilt R_NEW, M_PQ, M_QB, C_PQ, C_QB in metadata/full-logit versus clean mode: **144 requests**. Each original R pair must agree; new-core R must match old R in complete decision vectors and sequence state; all candidate endpoints must match old R. Candidate PQ/QB internal equality is reported separately. The whole panel qualifies or fails; no successful-subset performance claim.

If confirmation finds another counterexample, keep it and the panel becomes development data. Repair may continue, but a new independent confirmation panel requires prospective exposure exclusion and a new version. Maximum two confirmation panels (**288 requests**) in this study. No claim of universal correctness follows from either finite panel alone; accompany the empirical result with a defensible numerical/state argument for the stated supported domain.

## Original-model regression

After14B confirmation, use four original Qwen3-8B regression inputs, exact original model/tokenizer/DLLs and PR151 reference. The repair worker and structural policy are identical; only authenticated model geometry/placement binding differs. Six arms ×4inputs×heavy/clean = **48 requests**, with a64-request regression ceiling including bounded recovery. This detects breaking the original domain; it is not a new blind performance panel or evidence for all three old families. Wider regression can be proposed separately if a change touches a shared path outside the supported dense Qwen cohort.

## Timing after both gates

Four sessions ×12inputs×6 labels (R,M_PQ,M_QB,C_PQ_A,C_PQ_B,C_QB) ×one warmup+measurement = **576 requests**. Every worker has a fixed layout/policy, one input and one warmup/measurement pair;288 model-worker starts. The six-arm rotation is balanced over12inputs per session; four sessions are not a complete six-period Latin square per input. No concurrent model workers. All output checks and all blocks remain, including regressions.

The paid interval includes reset, actual prefill, any UB1 producer execution, state/logit export/import/readback, draft, verification, required synchronization, state updates and result assembly. Model loading and context provisioning are separately charged. Observer tensor capture and audit file output are outside clean samples. RSEED's copies/readback are real measured work even when expensive; do not turn them into precomputed reference lookup or hide their cost.

Primary local ratio: C_QB / mean(C_PQ_A,C_PQ_B). Equal input/session log weights. Engineering benefit requires more than max(2%,largest absolute per-input A/A imbalance) and QB faster in every session aggregate. Separately report M_QB/C_QB, M_PQ/dual-C_PQ, C_QB/R, M_QB/R and M_QB/M_PQ. These distinguish behavior reference, draft opportunity cost and representation increment. No artificial population CI, request bootstrap, outlier pruning or significance-driven extension. Failing to recover useful performance is not a reason to relax reference equality.

## Resources and safety

New maximum **1,200 model requests**:272development+288confirmation+64regression+576timing. Original40 remain separately identified; failed and reserved interrupted requests are charged. Shared ledger across epochs/builds prevents resets. No time-of-day deadline; actual finite worker timeout, cumulative owned time, RAM/VRAM/disk reserve, payload and cleanup budgets are filled on the host before execution. Stop native work for unknown ownership, asset drift, exhausted reservation or failed cleanup. Compiler/helper lifetimes are recorded in build/host receipts, not misrepresented as complete model-work accounting.

A source or auditor bug may be repaired with a documented successor epoch and fresh identifiers. Existing raw should be reaudited without a forward when possible. A changed scientific rule after confirmation exposure cannot reuse that panel as unseen.

## Outcomes and paper treatment

- **Correct and useful:** mechanism-supported fixed rule, untouched confirmation, old-model regression, and fully charged cost gain.
- **Correct but not useful:** reference restored, costs do not improve; continue engineering only within explicit development scope, report the trade-off.
- **Still counterexample:** retain new failures and specific unresolved mechanism; do not pretend the original broad guarantee was established.
- **Engineering block:** preserve inability and actual coverage; no invented numerical conclusion.

Original failures never disappear from history. No automatic paper rewrite, merge, arXiv submission, Strata/MoE branch, precision change, new reference, empirical-margin-only fallback or full-reference re-execution hidden outside timing. A full serial path is a correctness/cost control, not an optimization success.
