# B570 JSA closeout: draft-prefill submission policy

Status: **DESIGN_ONLY / NOT_EXECUTED**. This is one bounded software-baseline study, not an extension of CPU8 or a new attention/hardware search. It closes the numerically qualified but incompletely timed submission candidate in PR135. No clock-time deadline is part of the experiment.

## One question and fixed references

Can one draft-prefill API submission reduce **complete fresh-context service cost** while retaining physical q1 and the existing reference? Source ancestry: PR134 `51febaddcf49bb18565e568cf964a6e5c78876c9`, PR135 `e44c4df04c895b55ef734ee7b0659189158f95ab`, `benchmarks/b570_draft_prefill_submission_v1/attempt2/`. Keep the old failed observer attempt, incomplete timing, thread-policy negative result and cumulative charges unchanged. Do not resume its UUID or treat new observations as completing old registered slots.

The actual source audit says: change **only draft prompt submission**, from one llama_decode and synchronization per prompt token to one prompt submission; retain configured physical ubatch1, numerical DLLs, final-token logits flag, target QB implementation, model files, context, mask, positions, KV type, output cap and threads8. Logical caller width may grow; **physical q must remain1 for draft prefill**. This is not numerical batching and not proof of fewer GPU operations.

## S0 — evidence recovery and prospective freeze

Read the actual host results and search for any previously uncommitted timing; archive it as historical rather than pretending it did not exist. Recover original four input ID sequences and the346 PR134 QB full vectors plus complete native outputs/cycles. Verify exact target/draft model/tokenizer bytes, source/build and numerical DLLs. Check the repaired observer path first, and demonstrate that observers are absent from timed requests. The archived compile/capture result is not clean timing.

Prepare one new driver identity to select BASE or SUBMIT before each fresh context, never under an existing graph cache. No other optimization is combined. Reconcile old budgets, register a new UUID and all native/host/storage/cleanup reservations. S0 does not re-open CPU8/F0. If native infrastructure is unavailable, record a block and stop; this paper closeout must not trigger another open-ended supervisor rewrite.

## Arms and inputs

Use the exact four exposed HumanEval inputs from PR134: /38, /65, /115, /127, cap64 with natural EOG. The old reference endpoints are64/CAP,53/EOG,41/EOG,64/CAP. No new-input or length-generalization claim is intended.

| Arm | Definition |
|---|---|
| R | Original target-only reference; both model weights resident |
| BASE_A | Qualified QB, draft threads8, per-token draft prefill submission |
| BASE_B | Exactly BASE_A, independently invoked identical control |
| SUBMIT | Same QB/threads8, only one draft-prefill logical submission; physical ubatch1 |

Do not include CPU1, target-prefill batching, a new shader, persistent-context service, k tuning or QH. The single independent variable must remain visible in the source diff.

## E0 calibration and E1 qualification

Reserve one existing /42 cap16 bridge prompt for a bounded source/observer control: BASE and SUBMIT, capture and counts once each (4 requests in one process). Any discrepancy stops entry; retain the failed attempt. These calibration results do not select among multiple candidate policies.

On each of the four fixed inputs run R capture/count, BASE capture/count and SUBMIT capture/count: **24 requests in four qualification processes**. Compare capture/count native endpoints and complete cycles. BASE and SUBMIT must each match every applicable original346 full target/draft vectors including rejected verification rows; compare R only to its own matching reference. Check draft PREFILL physical q1 at all observable layers/ubatches, token position/mask/key evolution, logits flags and exact KV/pending behavior. A larger logical submission is not a passing geometry check by itself.

Any reference, observer, actual-q or state mismatch stops the candidate before timing and closes the study with a named counterexample/engineering disposition. No repair after these results, no tolerance relaxation, no reference replacement, and no timing of an unqualified candidate. If a required historical raw vector cannot be recovered, leave qualification BLOCKED rather than regenerate it as historical.

## E2 complete-service panel

Four independent timing processes ×four inputs ×four arms = **64 measured requests**, plus one arm/input-matched warmup before each measurement = **64 explicit warmups**. Every warmup is checked and separately charged. Commit a balanced four-arm order and rotated input order before execution. There is one single-threaded host writer and no concurrent model process. Layout and policy are fixed before fresh context creation. A failed slot remains failed; no automatic retry or outlier deletion.

Primary clock: immediately before fresh target/draft context creation and graph reservation through prefill, generation, native sampling, state handling, synchronization and context teardown. Model loading is separate; post-request byte comparisons and raw-file output are outside the timer. No observer capture, extra GPU synchronization or new Python wrapping is inserted into a measured interval. Host work already required by the inherited driver remains charged. Request-only, draft-prefill host interval, caller count and actual physical microbatch counts are secondary diagnostics, not GPU critical-path fractions.

Primary ratio per input/session: SUBMIT / mean(BASE_A,BASE_B). Equal-weight geometric mean across all16 blocks. Practical improvement requires complete qualification, reduction greater than max(2%, largest input-aggregate absolute BASE_A/BASE_B imbalance), and SUBMIT faster in every session aggregate. Also report SUBMIT/R and dual-BASE/R separately. Do not pool with PR134/135 timings or call an API count reduction a speedup. If timing is unstable, the small effect is unresolved rather than equivalent.

## Bounded finish and safety

Maximum **156 model requests /9 model-process starts**:4 calibration +24 qualification +64 warmups +64 measurements;1+4+4 processes. Exact source/binary/model and resource reservations must be filled before the first start. CPU compiler/wrapper/auditor costs are separately accounted. Use fresh output roots; reserve cleanup and storage; check actual exit/cleanup; stop on unknown identity, drift, memory pressure or reservation exhaustion. Derive finite whole-process safety timeouts from existing observations before execution, not a time-of-day deadline or favorable interim mean.

After E2, close this branch whether positive, negative, unresolved or blocked. No profiling extension, new model, prefill-width sweep, operator microbenchmarks, CPU8, M4/358H, actor or RTL follows automatically. This test does not assert a fully optimized software ceiling, and its four exposed inputs cannot support a generalization claim.

## Required result PR

Publish original failures/qualification identities, new preregistration and source diff, every input/arm/warmup/slot, physical-q and state evidence, all raw-vector access/hashes, timing/phase CSVs, deterministic analysis, process/cleanup/resource receipts and a PAPER_ADDENDUM with the exact outcome. If no practical benefit appears, retain the original baseline and end the software-policy branch. If it improves, use it as a new separately identified software baseline and report net drafting economics; never retroactively change PR134 or the old paper's reference.
