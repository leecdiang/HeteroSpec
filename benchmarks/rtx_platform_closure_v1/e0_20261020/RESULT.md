# RTX platform closure v1: E0 engineering stop

Protocol reviewed: PR136 at `65b938c19b9856c6c37af6c1d224989c22cd469f`. This is a separate result record based on main `ec6b97518a2f230330d79f1b0ba2ca97bc70cd6a`.

**E0 was audited and did not admit execution. No new native model, replay, build or profiler process was started. Execution preregistration was not frozen. E1 and E2 remain unstarted, and the conditional E3 is unavailable. No new performance or hardware conclusion follows.**

## Recovery findings

| Item | Finding | Evidence |
|---|---|---|
| Target/draft pair | Qwen3-8B Q8_0 / Qwen3-0.6B Q8_0 retained byte-for-byte | `RUNTIME_MODEL_DLL_AUDIT.json` |
| Native runtime | PR104 Qwen executable, 21 numerical DLLs, build manifest and driver DLL hashes all match; together with both models, 26/26 checks are KNOWN | `RUNTIME_MODEL_DLL_AUDIT.json` |
| Tokenizer | Embedded GGUF tokenizer is bound by unchanged model bytes; retained vocabulary, template and EOS/EOG metadata are preserved | `historical_evidence/PR104_MODEL_CONTRACT.json` |
| Output window | Historical cap128 is recoverable and retained as the proposed cap. No cap reduction or EOS/EOG change was made | `EXPOSED_INPUT_INVENTORY.json`, historical resident source |
| Historical request reference | Complete endpoint/count evidence and operator snapshots are recoverable, but the required full request-level target/draft raw logits reference is missing | `REFERENCE_COVERAGE.json`, `HISTORICAL_RESTORATION.json` |
| Speculative policy | PR104 C uses maximum_k=3 and target ubatch4; PR136 fixes k=1. Old k3 workload/cycle evidence is not a complete k1 reference | `historical_evidence/PR104_experiment.py`, protocol snapshot |
| Primary cost window | PR104 times the resident HTTP request, with contexts created at model-worker startup and reused. It does not supply the new fresh-context creation-to-teardown service measurement | `historical_evidence/historical_resident.py`, counter semantics |
| RTX accounting | PR104 event ledger and process receipts are preserved; PR120–123 resource summaries retain their own original units, failures and caps. No B570 budget or invented common remaining balance is used | `RTX_LEDGER_RECONCILIATION.json`, `ledgers/` |

Target model SHA256: `408b955510e196121c1c375201744783b5c9a43c7956d73fc78df54c66e883d6`. Draft model SHA256: `9465e63a22add5354d9bb4b99e90117043c7124007664907259bd16d043bb031`. Qwen executable SHA256: `8b7c5d9a76876dd22c596ccde18f5cb132123eb038155c1c0cf3114ca1dd2bd3`.

## Why E0 stops

The retained `hs_observer.h::sample` reads a logits vector to obtain top1, top2 and selected-token scores, then emits those scalars. It does not archive the complete vector. The operator capture stores selected Q/K/V/mask/QK/softmax/AV tensors, which do not replace full decision logits. The optional live checkpoint records a selected boundary and forks; it does not establish a complete historical request reference, and the authenticated PR104 E1 archive contains no `.f32` files. Clean PR104 E2 contains endpoint/workload counts without full heavy cycle traces. Member verification and schema coverage are recorded separately so archive integrity is not confused with reference sufficiency.

The new k1 qualification cannot inherit the k3 reference by relabeling it. Producing missing reference bytes or adding complete logits capture would be prospective work with a distinct reference/runtime identity and explicit qualification design. It cannot repair missing historical evidence retroactively. The current protocol's E0 rule requires this stop.

The new primary timer also needs an explicit implementation and validation before a freeze. Reinterpreting the old resident latency as fresh-context service, or mixing process startup/model loading into it without an established boundary, would change the estimand. No such substitution was made.

## Gate and slot dispositions

| Gate | Disposition |
|---|---|
| E0 | AUDIT_COMPLETED_NOT_ADMITTED / ENGINEERING_STOP_REFERENCE_BINDING |
| Preregistration freeze | NOT_FROZEN_E0_ENGINEERING_STOP |
| E1 | 12 logical qualification positions unstarted; no new q>1 observation or complete-reference PASS |
| E2 | 64 warmup and 64 measured positions unstarted; no timing ratios, A/A estimate or practical screen |
| E3 | 24 conditional clean/profile/clean positions unstarted and unavailable because E2 did not run |
| E4 | This E0 stop is archived; scientific questions remain unresolved |

`ALL_SLOTS.csv` enumerates positions, not an executable schedule. Inputs, execution order and nonzero native budget were not fabricated or frozen after a failed E0. All 12 previously exposed Qwen inputs remain in `EXPOSED_INPUT_INVENTORY.json`; none were silently removed. The study UUID is in `AUDIT_IDENTITY.json` and `PREREGISTRATION_NOT_FROZEN.json`. No execution `PREREGISTRATION.json` is issued.

## Costs, receipts and archive

New native processes, builds, model loads, qualification requests, warmups, measurements, profiles and GPU graph calls are all zero. Native owned lifetime is zero. Service ratio, GPU-active duration and speculative economics are unmeasured, not zero. Read-only review, hashing, Python, Git and GPU inventory operations are auxiliary work and are not represented as a globally complete OS-process ledger. The audit script's measured wall time covers only that script; earlier review and final packaging are outside that interval.

`PROCESS_RECEIPTS.json` states the empty native-process set and cleanup disposition; `COST_TABLE.json` preserves the separate windows. Host inventory is a point-in-time observation, not proof of continuous exclusivity. A process-name snapshot includes an unidentified `collector_service.exe`; it is not assumed to be a study or GPU process and was not touched.

`HISTORICAL_RESTORATION.json` binds the PR104 raw archives and the authenticated combined-restoration member checks. The original PR104 success/failure/cancellation/drift history and downstream RTX failures remain immutable; this study resets no historical budget. `DESIGN_SHA256.json` hashes the reviewed design snapshot and audit implementation. `EVIDENCE_SHA256.json` hashes all files in this result record except itself. The user-facing evidence ZIP and its archive SHA256 are provided separately.

## Interpretation and handoff

This result establishes recoverable runtime/model/output identities and a missing complete-reference binding. It does not reject or confirm a QB layout advantage, speculation profitability, q>1 qualification, equivalence, or a physical bottleneck. PR104's published fixed-panel values remain historical evidence with their original window and limits.

The PR136 2% plus A/A engineering screen and the target-only economics stop remain appropriate once execution is admissible. If those results later fail the practical screen or show speculation materially more costly than target-only, profiling should close without extending the search for a favorable number. Here that decision is unavailable because E2 never started. No profiling expansion, accelerator claim or paper reconstruction was started. The paper handoff is limited to this explicit evidence gap and the preserved historical scope.
