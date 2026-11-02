# Historical review and repair protocol

## 1. Actual evidence reviewed before this design

Pinned repository paths below are primary sources, not hypotheses.

| Evidence | Commit/path | What it establishes |
|---|---|---|
| PR144 first held-out counterexample | `3305b39ffcb723782acac9693e4d0213dd832152:benchmarks/rtx_jsa_closeout_v1/revision_a/RESULT.md` (Git blob `e07c95b9908797116067d58e396dbff33379c519`) | CodeContests/valid/108 has737 prompt tokens; PQ/QB both first disagree with R at output81; all cap128. Eight previous Llama cells passed; three later cells and all timing unrun. Not a737-token threshold. |
| PR151 diagnostic status | `29511ed91eb9f3d9773cfdda53e3554b0f4ad08b:benchmarks/rtx_scope_transfer_v1/sidecar_execution/diagnostic/STATUS.json` (blob `386f0008c80fc7692838db7800d46db5f653e39e`) |54 requests and5916 vectors; stable observers; P1 and P4_NATIVE M_PQ preserve R; C_PQ/C_QB fail under both. No imported common state; operator location unresolved. |
| PR151 complete diagnostic audit | same prefix `AUDIT.json` (blob `53a348ec0dc448e78a07483b158c8f6f96e43c2e`) | Full A1/A2 outcomes, controls at source indices6 and3, no numerical retries. |
| Original model/runtime binding | same prefix `EXECUTION_IDENTITY.json` (blob `c6a2a93c6d5d12d788aca373d2d201332d26bee8`) | metadata4 source; original Llama target/draft, original EXE and21 DLLs; q4/k3/F16KV/context1024/fresh-context contract. |
| PR159 historical Llama regression | `38b3d3d3929dc958e6a2a7e0bdc8abd61ff38ab1:benchmarks/rtx_reference_repair_v1/host_execution/LLAMA_HISTORICAL_BEHAVIOR.json` |24 records match old behavior;2356 captured vectors match. Known four C-path failures against R remain failures, not PASS. |
| PR159 executed Llama adapter | same commit `scripts/experiments/rtx_reference_repair_v1/diagnostics/build_llama_regression.py` (blob `ba2a267867baef1e449d7c9b9f88d0581a972920`) | Fresh-context admission and metadata4 adaptation exist; constructor/state capture ordering needs preservation. |
| PR159 use-after-free repair | same prefix `fresh_capture.py` (blob `65cacbc5a99340f3d8746cb175781f6ea85a627a`) | Snapshot while Context is live; write owned bytes after destruction. Earlier crash was instrumentation, not the scientific token counterexample. |

Development inputs in fixed source order: `CodeContests/valid/108` (source8), `CodeContests/valid/43` (source6), `GSM8K/test/496` (source3). PR151 `REQUESTS.jsonl` SHA256 is `2e52aee27acb551f3f3556a566ec5f83b123aa0d50a9c01da3666ac33a2fa4b9`.

This authoring pass read the committed historical reports/audits/source. Bulk historical vectors have not been downloaded into this container. The new **mandatory first host step** reopens the pinned raw records, verifies all5916 vectors and computes exact decision-row/logit divergence positions. No claim of new GPU or all-raw replication is made by this PR.

## 2. What follows from the history—and what does not

* A purely textual output-comparison error is not the leading explanation: full vectors and observer controls already reproduce the failure.
* Repeating P1/P4 natural recipes alone has low information value. Their result does not prove state identity, however; a same-state intervention remains useful.
* PQ/QB mutual equality does not certify R. The likely search region is their shared producer/consumer/transaction/numerical execution, but no particular operator is declared guilty.
* Do not assume Qwen's normalization/RoPE backend switch is Llama's cause. Llama has a different graph structure; actual scheduler and same-operand evidence must lead.
* Output81 is a symptom. Find the earliest comparable saved logit difference and map it through actual accepted/correction/bonus records. A common token prefix does not imply common internal state.

## 3. Development decision tree

A. Reconstruct history and recover immutable original R assets. Preserve old references and known failure. Inspect first differing decision row, whole logits, pending/KV bounds, shapes and execution identities.

B. Build an unmodified-arithmetic Llama successor with observation/lifetime changes only. No Qwen fix by default. Reproduce failure and controls in a36-request natural matrix. Compare new R to the original EXE, not only to itself. Initial mismatches are development observations.

C. At the evidence-selected cycle, checkpoint the actual natural target state. Run uninstrumented vs checkpoint-only controls first. Then run q1/q4 same-state consumers, with own q4 replay and trace/no-trace controls. Both clone orderings are available. Record conditional-row provenance; rejected suffix rows are not natural reference outputs.

D. If same-state consumers differ, narrow by layer outputs, then source-reviewed operator checkpoints and actual scheduler assignment. Capture complete inputs/parameters from producing nodes or an explicit pre-operation hook; do not label overwritten post-operation buffers as input operands. Perform own-path replay before crossed backend/kernel/shape interventions. If same-state consumers agree but natural R/C differ, inspect producer/state/reconciliation and use checked common canonical states or adjacent natural checkpoints. If the proposed diagnostic is invalid, fix its own-path/observer controls first.

E. Implement the smallest evidence-supported structural rule that repairs the mechanism while retaining parallel work. Allowed: semantic-role dispatch, geometry/stride/kernel contracts, RoPE/mask/value-range conditions, state reconciliation or graph cache identity repair. Not allowed: task/token/output-index exceptions, replacing R, hidden answer lookups, empirical margin-only guarantees, selective failures, or calling a wholly serial fallback an optimization success. If a numerical-library change is justified, integrate an explicitly bound source successor; old R libraries remain separately pinned.

F. Validate intervention on/off with identical controlled inputs, all old Llama controls, and Qwen8B/14B regression under the new shared policy. Observe actual q and backend; unchanged declarations are not evidence of unchanged execution. Natural EOG remains natural; report unobserved q rather than forcing tokens into correctness/performance data.

## 4. Development freedom and scientific separation

The author authorizes substantial mechanism work and ordinary source/build/API/observer/storage fixes. Each new candidate has immutable source, build, asset and epoch identities. No per-candidate retry cap or mandatory wall-calendar deadline is imposed. Work-credit/time/storage reservations can be extended transparently by the agent with a specific next question; the ledger and failures remain. Hardware safety and process cleanup are nonnegotiable.

Do not turn every failed candidate into a permanent stop. Do not turn unlimited development into repeated testing on the held-out panel: exposure is appended before every native launch, including failed attempts. Once a confirmation input has been observed, it may be used for development but never counted as unseen again. Original references may be recovered/read; newly run references for held-out tasks only begin after candidate freeze.

Changing the supported scientific domain (new model weights, tokenizer, precision, context/stop contract or reference definition) is a different experiment, not an engineering fix. This PR does not automatically authorize a broad model/quantization search. Interface details and the choice of causal repair are deliberately left open.

## 5. Confirmation and complete cost

Default24 fresh natural inputs: code/math × formatted length128–384/512–768 ×six. Twelve inputs (three per cell) is allowed only when fixed before outputs and documented. All prior project exposures are excluded by ID, text and token hash. No padded/repeated/truncated prompts to manufacture length strata. Keep exact original Llama template, source snapshots and licenses.

Original oracle: unchanged PR151 EXE, models and numerical DLLs; two off/heavy requests per input. Candidate: R,M_PQ,M_QB,C_PQ,C_QB ×off/heavy. Require full endpoints/EOG/stop, transactions, complete-vector greedy checks and available state/geometry evidence. Compare candidate R vectors to original R. PQ/QB internal equality is a separate finding; no new requirement that all valid speculative states must equal serial R bytes.

Timing: R,M_PQ,M_QB,C_PQ_A,C_PQ_B,C_QB; six loaded sessions; one fresh-context warmup immediately before each measured request. Default24 gives864 measured +864 warmups. With12,432+432. Same tensor/observer policy in all natural runs; captures absent during timing. Model loading separate, context creation/reset as applicable, prefill/state transfer/verification/reconciliation/synchronization/teardown all charged.

Six-period Williams orders balance every arm position and every ordered within-block adjacent-arm pair for each input. A/A relative order is3/3 per input; block boundaries and same-arm warmup carryover are recorded rather than claimed perfectly controlled. Input order is deterministic hash-ranked. No concurrent model workers, archives or profiling during timing.

Estimator: arithmetic dual-PQ mean within each block, equal-weight geometric mean of block ratios. Separate QB/PQ, target-only layout, same-layout M/C and R-normalized costs. The new screen uses improvement > max(2%, largest symmetric input-aggregate A/A imbalance) and every session favoring QB. This is a new prospective rule, not a change to PR159. All blocks and reversals retained; no population CI from treating requests as independent samples. Do not extend timing after seeing the sign or threshold.

## 6. Completion criteria

A repaired result requires an evidenced mechanism and ablation, repaired historical counterexample with no answer-specific rule, frozen unseen qualification, regressions and fully charged costs. Correct-but-slow is not an optimization success; fast-but-reference-changing is not a repair success. An unresolved branch must report the precise current blocker and executable next step, not disguise missing data as failure of all possible methods.

Deliver a separate result PR, no automatic merge or paper submission. A new result must retain PR144/151/159 failures and code, field every planned/attempted/unstarted slot, and complete upload plus fresh download/member verification. Exact experiment counts and safety costs are reports, not a claim of independent statistical replication.
