# PR104 execution result — stopped at Phase 0

Status: **STOPPED_INCONSISTENCY. Experiment not completed.** No E2 or E1 native process, request, forward or operator replay was started. No scientific slot was retried, removed or overwritten. This is an admission failure, not a scientific null or negative result.

## Frozen identities and admission finding

PR104 inspected head: `2511ade621d036c0d712c3d694483c79da2b4cf1`, branch `experiment/rtx-qb-confirmation-20261014`. PR98 baseline: `3235d44c26edd92db33e574094c26af8e29d2452`.

The read-only audit passed 57 of 58 checks: pinned baseline blobs, resident/run_common and all 19 inherited Python helper files, original and corrected server binaries, replay executable, all 21 numerical DLLs, six target/draft models, and recorded GPU/driver/memory/power-scheme identity. Full paths, sizes, expected/observed hashes and host samples are retained in `execution_20261014/FREEZE.json`. GPU: RTX 5070 Ti Laptop GPU; driver 616.92; memory 12,227 MiB. No native load was used to obtain this audit; loaded-module/full-offload admission was therefore not performed.

The failed check is **INHERITED_ARM_RUNTIME_ROUTING**, affecting SmolLM2/M_PQ, SmolLM2/C_PQ, Llama/M_PQ and Llama/C_PQ:

| Runtime | SHA-256 | PR98 admitted use |
|---|---|---|
| llama-server.exe | `8b7c5d9a76876dd22c596ccde18f5cb132123eb038155c1c0cf3114ca1dd2bd3` | Other arms |
| llama-server-pq-metadata4.exe | `144ffa8060f22510028ab8d03da0ba8976eca2d25a8a3e8d7ede4f94d62dd0d9` | SmolLM2/Llama PQ |

PR98 `RESOURCE_CORRECTION.json` records a PQ metadata allocation abort and its resource-only correction. Its `correction95_v02.py` selects the corrected executable **and** `NATIVE_BUILD_V02.json` for those four arms. PR104 `prepare()` copies only the original executable/build manifest, and `run_session()` instantiates unmodified `native.Resident`, which selects the original executable for every arm. Thus the proposed runtime routing does not reproduce the admitted PR98 baseline, even though the individual files are byte-correct. No new allocation abort was induced in this execution.

The user's Phase 0 rule requires stopping on any inconsistency. No corrective runtime substitution, registration or scientific start was made. `execution_20261014/FREEZE.json` is a **non-admitting Phase 0 audit freeze**, not the executable `E2_F0` registration. The deterministic exposed-panel plan is retained as `UNREGISTERED_PLAN.json`; it has never been registered or executed.

## Counts, sessions and PQ/QB comparisons

| Quantity | Planned | Started | Completed |
|---|---:|---:|---:|
| Fresh native workers | 324 | 0 | 0 |
| PQ/QB comparison requests | 864 | 0 | 0 |
| Serial reference requests | 432 | 0 | 0 |
| Excluded warmups | 324 | 0 | 0 |
| Total native requests | 1,620 | 0 | 0 |

| Session | Status | Started requests | M log contrast | C log contrast |
|---:|---|---:|---|---|
| 0 | NOT_STARTED | 0 | N/A | N/A |
| 1 | NOT_STARTED | 0 | N/A | N/A |
| 2 | NOT_STARTED | 0 | N/A | N/A |
| 3 | NOT_STARTED | 0 | N/A | N/A |
| 4 | NOT_STARTED | 0 | N/A | N/A |
| 5 | NOT_STARTED | 0 | N/A | N/A |

| Family | M geometric speed ratio | C geometric speed ratio | Qualification |
|---|---|---|---|
| Qwen | N/A | N/A | WITHHELD_PHASE0 |
| SmolLM2 | N/A | N/A | WITHHELD_PHASE0 |
| Llama | N/A | N/A | WITHHELD_PHASE0 |

The prescribed speed ratio is `T_PQ / T_QB`, so values above 1.02 indicate practical QB improvement. There are no observations to classify as improvement, weak/no practical difference, regression or reversal. No request-level bootstrap or session interval was computed. `UNSTARTED_SLOTS.csv` retains all 1,620 planned request coordinates; these are never-started slots, not missing receipts from started requests.

Scientific failures: 0 observed output mismatches, 0 observed latency anomalies, 0 missing started slots. Admission failures: 1 runtime-routing inconsistency, with four affected family/arm conditions. Unstarted planned requests: 1,620. Latency, output IDs, EOG/cap and PID fields remain empty because no request exists.

## E1 numerical table

E1 was not started because E2 did not complete. The inherited bounded matrix has 72 contexts, and its 216 operator rows are retained in `E1_NUMERICAL.csv`; all measurements are unavailable. These are NOT_STARTED, not failed captures or NOT_OBSERVED geometries.

| Families | Layers | Phases | q | Operators | Bitwise equality | Max error | ULP | First divergence |
|---|---|---|---|---|---|---|---|---|
| Qwen, SmolLM2, Llama | 0/middle/last | prefill/continuation | 1–4 | QK/softmax/AV | N/A | N/A | N/A | N/A |

q=1 remains the planned negative control. No E1 native compilation, capture adapter registration, own-path admission or replay was performed. No kernel identity or reduction-tree claim is made.

## Reproduction, archive and limitations

`phase0_audit.py` performs a read-only admission audit and never starts a native runtime. `summarize_phase0.py` recomputes the stopped result, missing planned coordinates and E1 unavailable table from preserved evidence. The original PR104 analyzer, comparator and synthetic tests remain unchanged. All 20 synthetic test methods passed on this Windows host; they are CPU checks and do not qualify E2 integration or E1 CUDA execution.

`RAW_ARCHIVE_MANIFEST.json` binds every preserved evidence member by size and SHA-256. The new raw archive was restored into a fresh directory, its members were checked against that manifest, and the CPU stopped-result analysis was rerun and compared byte-for-byte. No model weights or credentials are included. Historical evidence copied into `raw/` is clearly inherited evidence, not new PR104 scientific results.

This delivery records a stopped attempt only. It cannot establish stable independent PQ/QB benefit, generalization beyond the exposed panel, broader legal numerical geometry, speculative decoding economics, universal equivalence, same kernel or same reduction tree. Six sessions and their required spacing were never executed. Historical RTX measurements and PR102 paper results were not edited.

**Claim assessment:** this execution supplies no new support for “QB provides lower-cost local repair while preserving speculative decoding economics.” It neither confirms nor refutes that claim. A prospective amendment must first restore and freeze the inherited per-arm runtime routing; E2 and then E1 remain unexecuted. No GS-versus-QB comparison was performed.
