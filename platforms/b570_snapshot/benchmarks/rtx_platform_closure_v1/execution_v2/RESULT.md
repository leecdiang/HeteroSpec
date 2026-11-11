# RTX platform closure: completed finite-panel result

**E0 repaired, E1 passed, E2 completed: NO_ESTABLISHED_PRACTICAL_LAYOUT_BENEFIT.**

Primary QB / dual-PQ service ratio **0.98928383**, a **1.072%** reduction. Largest input-aggregate A/A imbalance **5.208%**; engineering threshold **5.208%**. QB / target-only ratio **0.58232511** (REPAYS_ON_PANEL).

| Fixed exposed input | Output | QB / dual-PQ | QB / target-only |
|---|---|---:|---:|
| MBPP/413 | 34/EOG | 0.988025 | 0.608126 |
| GSM8K/test/120 | 128/CAP | 1.004279 | 0.578678 |
| GSM8K/test/322 | 128/CAP | 0.963695 | 0.610027 |
| GSM8K/test/443 | 128/CAP | 1.001663 | 0.535651 |

## Reference and scope

PR136 was audited at65b938c19b9856c6c37af6c1d224989c22cd469f. The original E0 stop is preserved under e0_20261020. Following the user’s explicit repair instruction, a new prospective request driver/reference identity was frozen at351415f112c695f6bc84ae718b323c7b59d3990d before the first model process. This is a prospective service study using the same model/tokenizer/output bytes and21 original numerical DLLs, not an assertion that PR104 contained complete logits or that its resident timer had the new service window.

Four independently generated R/PQ k1 references preserve the old R endpoints;1,106 complete float32 vocabulary vectors are sealed at18f8ef3a7a7cd61846d3deca4a7f62f9f0d9f9ee before independent E1. E1 produced1,794 vectors, all compared byte-for-byte against the matching new R or PQ reference, including discarded target verification rows. R/PQ/QB endpoints match, and speculative cycle/pending/proposal/accept/reject/correction/bonus/KV-bound traces match. All36 target layers show actual caller rows2, physical attention q2 for QB and serial q1 for PQ, GQA32/8, observed key extents/dtypes/strides/masks and RTX placement. Operator tensor readbacks were not requested because that would split the CUDA graph. Visible key counts are derived from registered causal positions; physical mask extents/strides are observed.

Qualification was sealed at913407f7 before clean timing. E2 contains4 independent native processes,64 measured requests and64 separately charged warmups, one per input/arm/process. Every output and cycle/state check passes. All16 paired blocks, both identical PQ controls and all session signs remain visible. No failed native process, scientific retry, outlier removal or post-hoc input selection occurred.

The primary timer covers fresh target/draft context and graph reservation through prefills, generation, greedy decisions, output/state handling, synchronization and teardown. Both model weights remain resident for R; model loading is separate. R retains historical target ubatch1; speculative target uses ubatch4 and draft ubatch1. This measures the frozen execution policy, not an optimized production-serving ceiling. Timing has no node observer, full-vector file writes or correctness comparisons inside service. Host decode phase intervals are not mutually exclusive GPU critical-path shares.

## Decision

The preregistered2%/A/A/every-session engineering screen is applied without significance or equivalence claims. A practical complete-service layout advantage is not established on this fixed panel.
The A/A imbalance exceeds the2% practical margin. The small layout point estimate is noise-limited and unresolved; two session aggregates favor PQ. This is not proof of equivalence, no true layout effect, or a precisely measured1.07% gain. No outlier removal or follow-up precision hunt repairs that uncertainty.
E3 disposition is recorded separately; no additional profiler, counter sweep, hardware/RTL/actor study or favorable-number search was run. No physical bottleneck or accelerator claim follows.

## Accounting and archive

New scope UUID `03e27959-0838-4829-8ccb-48e53cb902c6`:12 native processes /148 total requests, native parent lifetime 446.746733s; separately recorded model loading 44.690935s. All12 processes exited normally and cleanup returned. Native GPU-active duration and hardware kernel count are unmeasured. The original preparation DLL-staging failure and five successful compiler/archive/link invocations remain documented; compiler lifetime was not captured before that staging error. Historical RTX ledgers and their separate units/caps are preserved; no B570 allowance was transferred.

`ALL_SLOTS.csv` preserves148 successful requests and24 conditional E3 positions not started. `COST_TABLE.json`, native receipts, the full raw SHA256 manifest, compact compressed results, state traces and immutable local archive descriptors accompany this result. The complete local ZIP contains raw vectors, executable, original numerical DLLs and frozen sources; model weights are identified by hash and remain at their retained paths rather than duplicated. All ZIP members are reopened and checked against their raw hashes. Raw archive availability is local, not an external authenticated raw download or independent audit.

The finite panel uses four previously exposed inputs, one model pair, one RTX machine/date and k1; no unseen-input, cross-device, universal-equality or energy claim is made. Old PR104 layout values retain their original scope. The paper handoff distinguishes layout benefit from speculative economics and includes all negative/weak observations; no paper reconstruction has begun.
