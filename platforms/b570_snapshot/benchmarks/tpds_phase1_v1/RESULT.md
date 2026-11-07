# B570 phase-one review-v2 result

The current resident phase interface is qualified at C1024 and C4096 on the original Arc B570 host, using the inherited PR169/191 Vulkan F32/p021 implementation. This is an extension/qualification of that interface, not first-ever project support for 4K. All twelve registered coordinates and all three controls are retained.

Branch origin: PR193 actual head `eed20261b5820ea4f778fb5a1012cb07e98dfea4`; execution source `d240c5b63ae78299fe6abee74878c7530e9922b7`. The host audit found no earlier phase1 freeze or started phase1 ledger. Prior studies and original R were not changed. The independent result branch adopts review-v2.

## Fixed append results

Each value is the mean of the three predeclared measured appends in milliseconds. Every measurement has an immediate same-arm warmup and a separately restored valid seq0 KV prefix. The complete three timings, warmups, order and receipts are in `evidence/B570_FORMAL_RECORDS.json` and the raw archive. L/S below one favors LOCAL. No coordinate or slow arm is excluded.

| Capacity / q / relation | Scalar R ms | SIMPLE ms | LOCAL ms | LOCAL / SIMPLE |
|---|---:|---:|---:|---:|
| C1024-q2-crossing | 19.145 | 18.128 | 14.074 | 0.776350 |
| C1024-q2-inside | 16.913 | 11.773 | 11.830 | 1.004813 |
| C1024-q32-crossing | 267.435 | 133.421 | 73.803 | 0.553161 |
| C1024-q32-inside | 256.577 | 66.875 | 67.296 | 1.006290 |
| C1024-q4-crossing | 35.974 | 23.605 | 16.753 | 0.709708 |
| C1024-q4-inside | 32.269 | 13.973 | 14.340 | 1.026265 |
| C4096-q2-crossing | 23.535 | 22.050 | 17.564 | 0.796568 |
| C4096-q2-inside | 20.495 | 14.872 | 15.428 | 1.037408 |
| C4096-q32-crossing | 325.146 | 184.786 | 125.338 | 0.678289 |
| C4096-q32-inside | 316.295 | 115.998 | 117.850 | 1.015969 |
| C4096-q4-crossing | 43.972 | 29.599 | 22.363 | 0.755524 |
| C4096-q4-inside | 40.824 | 19.588 | 19.673 | 1.004339 |

LOCAL is faster than SIMPLE at the six declared crossing coordinates and slightly slower at all six inside coordinates. This selected structural matrix supplies neither natural crossing frequency nor a population interval/global service-speed average. It does not reopen Smol/k1 profitability. No extra timing round or sample was added.

## Reference, capacity and numerical scope

C1024 retains the unchanged original forced-R binary and its original Vulkan backend/reserve. C4096 has a separate deployment reference defined before any candidate output. Both preserve whole-prompt outer512/physical UB128 producer arithmetic and original output masks/reserve, followed by scalar reference continuation. Both capacities keep identical matched idle Smol135M residency. There is no target-only fallback or Qwen migration in this study.

The deterministic licensed tape is the first lexicographic existing path with at least 3,104 tokens: `3ddbd1c3-6d84-42c6-8b2c-0545e3e699af`. No padding, timing, candidate output or acceptance rate selected the tape. Prefix/append coordinates are C1024/B768 and C4096/B3072, q2/q4/q32, heads B−q and B−1. These are known-token diagnostics.

Both actual contexts report the requested n_ctx. C4096 target F16 KV is 805,306,368 bytes (768 MiB); actual backend/scheduler allocations and signed budget values are retained for every qualification. The signed GPU floor remains 128 MiB. At the C4096 q32 crossing restored qualification, the observed target scheduler allocation is 79,696,416 bytes for R and 31,982,624 bytes for S/L. These are actual allocations, not a peak-memory estimate.

The original scalar R keeps n_outputs_max=512/per-sequence1 and an observed 196,640-byte output buffer. Candidates declare max4/per-sequence4, with observed 786,464-byte buffers, sufficient for q2/q4 requested full rows. q32 requests/copies exactly **one last row**. The old reserve32/all-output probe is not used. R generates the individually required rows without expanding its reserve.

The read-only audit rechecks 700 complete 49,152-element vocabulary vectors and 156 serialized active-state equalities, plus the independently repeated references and original C1024 bridge. Producer initial frontier, required post-append vectors, full active KV and resulting frontier match. Restored known-query inputs restore seq0 KV; their suffix IDs are fixed and do not sample an imported initial-logits buffer. Ordinary generation uses the original producer's live frontier. Eighteen finite ordinary controls verify reset repetition, natural EOG at the already exposed 116-token case, cap1 and the correctly positioned unmaterialized terminal ID at both capacities.

## Physical work and clean observer

Native successful process_ubatch observations verify the actual physical head and occupied rows. At each crossing, R occupies q singleton target micrographs, SIMPLE occupies widths 1 and q−1, and LOCAL occupies one width-q target micrograph. Inside the boundary, S/L each occupy one width-q graph. The LOCAL attention cuts preserve the corresponding two extent groups while compatible outer work remains wide. Raw HS_CACHE/HS_ATTENTION/TP_DISPATCH events retain masks, extents, grouping and selected F32/p021 dispatch. A graph or dispatch-selection event is not presented as a count of every executed GPU kernel. Successful graph reuse is recorded; the restore path retains its legal phase capacity, rather than forcing a redundant UB128 reserve.

Clean append has no observer callback, heavy capture, state export/import or reference replay. Real counters cover the adapter begin/decode/end/finish chain. All four counts are zero in each formal slot; an intentionally dirty diagnostic executes actual export/import/replay/capture and produces one in each counter. Heavy qualification and physical tracing are separate charged requests.

The append clock starts immediately before resident phase binding with the query batch already assembled. It includes native reserve/planning, actual graph work/reuse, execution, required synchronization and requested output ownership copies. Caller batch assembly/release is in broader native/process envelopes and has no separate subclock. Prefix/import/reset is outside append and separately recorded. `service_ms` ends at receipt assembly; it is not claimed as complete per-request response latency. Owned-worker wall includes response write/close and termination. Unmeasured complete per-request latency and fine-grained plan/mask/concat/extraction/device-kernel clocks remain null. Nothing is inferred by subtracting inclusive clocks.

## Builds, versions and costs

Before formal timing, the freeze binds 374 actual compiler translation units, five exact link commands, 2155 input files, MSVC-produced transitive dependencies, original reports, generated/config/response files, link objects/static libraries, tools/environment and an observed union of 89 runtime module paths. All formal workers match their qualified actual module set. The final source also compiles in a fresh directory and passes independent native four-row/active-KV bridges at both capacities. Original common/ggml ABI libraries are explicit inherited dependencies, not claimed newly rebuilt shaders. See `SOURCE_AND_BUILD.json` and `REPRODUCE_B570.md`.

The first development candidate mistakenly loaded the original Vulkan backend instead of the admitted F32/p021 backend. Its C1024 q2-inside output differed in all 49,152 entries (maximum absolute difference 0.36418724). The failed runtime, all twelve native requests and their costs remain in native01. Native02 repairs runtime assembly and the redundant restore-phase reserve, then fully requalifies before its single formal freeze. No failed result is relabelled successful. Two CPU-only dependency-import failures (newline-separated response arguments and /implib output-option parsing) are retained; they occurred before the successful freeze and launched no models.

The immutable new ledger reserves **387 logical requests / 178176 decoded-row upper bounds / 0 operator replays** against 1,024 / 2,500,000. This includes references, failed qualification, all warmups, controls and clean-build bridges. All 137 workers have verified Job cleanup and zero active descendants. Native charged wall is 941.313s; owned-worker wall is 1002.175s. These overlap and are not added.

Across all 216 formal slots: append measurement total 7.708686s, warmup append total 9.088370s, preparation 236.428622s, including 235.877949s import/read and 0.549144s reset. These are study-accounting totals, not a natural-workload speed estimate. The broader native service-until-receipt-assembly envelope is 253.234648s. Every phase reports present/measured/expected coverage; missing subdivisions and initial unmetered CPU preparation remain null. Idle draft setup is charged in process provisioning; draft decode is explicitly NOT_EXECUTED.

Recorded build/configure command envelopes total 415.798s. Inclusive driver costs, failed CPU preparation, archive/storage and readback costs remain separate and are not added to nested native service. Original 900s worker /180s progress, 16 GiB Job, 20 GiB disk, 2 GiB RAM and signed 128 MiB GPU reserve floors remain.

## Delivery and limits

The dedicated release carries raw records, both development versions, all timings/controls/costs, complete build manifests, runtime binaries and source inputs. Flat KV originals remain on the host; the delivered token recipes reconstruct their exact original serialized bytes and save duplicate storage. The final delivery receipt records authenticated fresh download, archive verification and model-free reconstruction. No external-reader or external-device replication is claimed.

The C4096 branch is admitted and completed. The scientific scope remains dense seq0 F16 Smol, noFA, fixed known appends on this B570/runtime. There is no new shader/cache algorithm, natural service-profit confirmation, RTX/arXiv change, model download, rental, merge or erasure of old k1/Qwen failures.
