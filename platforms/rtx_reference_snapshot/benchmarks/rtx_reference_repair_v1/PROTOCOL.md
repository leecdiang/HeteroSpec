# Mechanism-led repair protocol

## 1. Objective and protected evidence

Preserve the original Qwen3-14B Q8 target, 0.6B Q8 draft, tokenization, greedy/EOG,
cap128, context1024, F16 KV, k3 and fixed weight-offload policy from PR156. R is the
original PR156 UB1 execution, not a newly chosen candidate output. Keep the 40 failed
pilot requests, wrong historical placement interpretations and correction v2 intact.
This study is a new authorized development effort, not a technical retry of PR156.

Success has three parts: a mechanism-based fix, independent transfer/regression
checks, and complete-cost measurements. Removing two known divergences does not
by itself prove generality. Returning every request through full serial R is a
correctness control, not a performance achievement.

## 2. First implementation and scientific alternatives

### D0: canonical producer intervention

A real UB1/unscoped context prefills the exact prompt. Export complete sequence KV,
positions and final FP32 logits; restore into an empty consumer; sample the copied
logits. The token is pending and must not already be inserted in target KV. The
receiver import is round-trip checked in the diagnostic channel. R→R controls test
handoff fidelity. Native/PQ/QB producer-to-R crosses test whether the imported state
can already change subsequent reference execution.

This is not "submit q1 rows into UB4 and assume it is R". Context capacity, backend
path, output reservation and numerical operations remain observable. The producer
is destroyed per request and its full cost remains inside service_seconds. A later
persistent-context implementation is allowed only as a separately validated global
policy with reset and cache-reuse controls and a fresh cost identity.

Development matrix: four existing inputs ×12 (consumer,prefill) recipes ×heavy/off
=96 requests. Recipes are R/native, R/reference (sham), R/pq, R/qb, and the M_PQ,
M_QB,C_PQ,C_QB consumers under native and reference prefill. Every matrix cell is
retained, including expected reverse-cross failures. An observer or restoration
failure blocks interpretation, not only performance.

### D1: same-prefix localization

Inspect initial logits/boundary state first, then force an identical historical
*development* token prefix into target-only consumers and inspect the next decision.
Forced tokens are not a live repair, and all such runs are marked diagnostic and
rejected from correctness qualification and performance.

Capture l_out checkpoints before expanding to norm, Q/K/V, RoPE, QK, softmax, AV,
output projection or FFN. Source-verify names and logical row axes. Pair every heavy
trace with the same-prefix non-tensor observer control. Reject a localized claim
when observation changes endpoints, logits or final state. Multi-ubatch graphs can
have different call occurrence/row mappings; align explicitly rather than compare
unrelated buffers. The first captured mismatch is not necessarily the first global
mismatch, nor sufficient evidence of causal responsibility.

Actual backend is read from the scheduler's tensor assignment, with buffer ownership
kept separate. The API does not prove occupancy, internal kernel placement or physical
bottleneck fractions. No claim that CPU-resident weights imply CPU QK is allowed.
Post-op captures save outputs only: in-place sources may already have been overwritten.
A same-operand replay requires authentic pre-op operands and own-path reproduction.

### D2: minimal structural repair

Use a causal intervention/ablation to identify which change removes the discrepancy.
The supplied opt-in Q8 matmul primitive splits independent token columns into one-row
native products and concatenates them in order. Enable only justified operator roles,
not a task ID, prompt hash, generation position, selected answer token or logit-margin
threshold. R/q1 and inactive draft calls use the original branch.

The primitive does NOT guarantee bitwise R equivalence: reduction selection, numerical
libraries, memory representation and dispatch can still differ. Test exact same-operand
correspondence in the implicated operator and whole-model endpoints before timing.
Broader numerical repair, backend path stabilization, or a supported norm/attention
fix may be implemented if diagnosis warrants it; preserve source diffs and add tests.
Do not globally serialize all work and call it a fast implementation.

### Development freedom

Normal engineering failures can be fixed and repeated in new attempt/epoch directories.
New scientific candidates may also be developed, provided their mechanism is recorded
and old failures remain. The user has already authorized this development; do not stop
for another generic confirmation after each compiler/adapter failure. Never reset the
shared ledger or overwrite an old attempt. See ENGINEERING_POLICY.md.

## 3. Regression and freeze

The four 14B development inputs are permanently exposed. Include the original 8B
qualified control panel and previous Llama counterexample/controls using their own
pinned model/reference identities; do not substitute their references with 14B output.
The 14B runner does not automate these other model harnesses. The agent should reuse
existing runners, record exact counts and costs in the new ledger, and keep actual
cross-model support separate from 14B-only conclusions. Do not claim regression PASS
when a model or source capsule is unavailable.

Before held-out exposure, record: causal evidence, the implemented intervention,
ablations, same-operand controls where relevant, full development/control outcomes,
regression outcomes, source/EXE/DLL hashes, policy and remaining limitations. All R/native
and R/reference shams and the selected M/C-PQ/QB policies must preserve the fixed R.
The freeze command verifies native record hashes and reaudits their vectors/state.
Human scientific assessment is still required; a boolean review field is not a proof.

## 4. Confirmation panel and reference

Use the exact 12 input IDs and token arrays already selected in PR156 but never run
with the 14B model. Preserve the code/math ×short/long design. Do not replace a failed
item or alter prompts, output cap, precision or stopping rules. `prepare` matches both
panels to their fixed Git source. Prior exposure is tracked across development epochs.

First execute the ORIGINAL PR156 worker and its original 21 DLLs for 12 inputs ×heavy/off
=24 reference requests. Candidate references are not used as the ground truth. Then
run 12 inputs ×R,M_PQ,M_QB,C_PQ,C_QB ×heavy/off=120 requests with the frozen candidate.
Every required complete endpoint must agree with original R; every observer pair must
agree. Logit/state correspondence between PQ and QB is separately reported and is not
silently required where the scientific claim is only endpoint preservation.

If a held-out case fails, retain it and return to mechanism development. It is now
exposed; the same panel cannot subsequently be described as blind confirmation.
A new version can use it as regression data, but a new independent panel requires a
prospective selection record, exposure exclusion and an explicit protocol/implementation
amendment before any forward, within the remaining authorized budget. The supplied
first-pass runner intentionally will not auto-recycle the old panel until PASS.

## 5. Cost only after qualification

Six labels: R, M_PQ, M_QB, C_PQ_A, C_PQ_B, C_QB. PQ_A/PQ_B are identical implementations.
Four process sessions ×12 inputs ×6 arms=288 measured requests and288 matched warmups.
Ordering balances arm positions over the twelve inputs per session; it is not a full
six-session Latin square for every single input. There is no required three-day wait.
One model worker is active at a time. Keep power/threads/device/software and context
reset policy fixed. Record actual session timestamps and all blocks.

Primary clock: resident models; request state reset, any canonical producer context
creation, prefill, state export/import, producer destruction, draft/verification,
reconciliation, synchronization and result assembly. Model load/pool provisioning is
recorded separately. Diagnostic tensor/state writing is outside the performance path.
Do not report transfer as free because it occurs before the consumer's first token.

Report QB/mean(PQ_A,PQ_B), same-layout M/C ratios, and both candidate/R comparisons.
A practical QB layout benefit requires >max(2%, largest input-aggregate absolute A/A
imbalance) reduction and QB favored in every session mean. This finite-panel engineering
screen is not a population confidence interval. All reversals remain. A repair can
preserve reference and still be too expensive: report that outcome directly.

## 6. Resources and stop rules

New research ceiling1200 model requests:480 development/diagnosis/engineering recovery/
cross-model regression +24 original held-out references +120 candidate qualification
+576 timing/warmup. Failed or interrupted attempts remain charged; stage reservations
are conservative. No closed PR156 request or budget is rewritten. Non-generating model
loads, compilers, helpers and evidence I/O are separately recorded.

Machine safety timeouts are finite and declared before each epoch, not deadlines such
as "finish tonight". Bootstrap defaults are reviewable resource ceilings, not duration
promises. Shared GPU lock, kill-on-close Job, exit accounting, RAM/VRAM/disk reserves
and finite capture limits are enforced. An unsettled native process receipt blocks
new execution until actual cleanup/cost is established. No silent retry.

## 7. Delivery

Result PR must include all candidate versions and failures, mechanism/ablation evidence,
actual scheduler observations, native build identities, complete slot ledger, independently
recomputed endpoints/decisions/state and performance, unused slots, and a raw access
index with upload + download verification. The supplied archiver verifies local ZIP
members; remote delivery is a separate action. No paper rewrite, automatic merge or
arXiv submission is part of this experiment.
