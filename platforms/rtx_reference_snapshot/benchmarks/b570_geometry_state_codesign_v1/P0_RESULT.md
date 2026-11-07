# PR108 native integration P0 — completed, awaiting exact P1 authorization

Design: 8d7b85d8aac6e546ca23e1f8a6ad353ea7ed2e02. Execution branch: experiment/b570-geometry-native-p0-20261015.
F0_EXECUTION.json SHA256: 29cf422ef631edfa45ba55b56947926e1977070b8957dbc362e4e5581401d6e8.

P0 has produced compiled native code and actual serialized launch objects. It has not executed a model. Author confirmation of this exact F0 and its 80-start budget is required before P1. P2/P3 remain separately unauthorized. Original fixed design files and old CPU_TESTS.log are unchanged.

## Work completed and source restoration

- Fresh full PR97 CAS restoration: archive SHA256 816b802f915373c861e754bba448048705ce790ee8a230e114fef8197079a530; 8,358 logical files / 7,883 objects rehashed. Includes original PR92 R executable, runtime, generic k1 transaction, old raw and source. Original R executable SHA256 e53fa3992504bfffa4b8dec40191e4640d34ff2b0975b2ed427491484c351275.
- PR101 worker independently matches fixed Git blob c45b45b26d998bbbcfe20a115c319041b8e167a8. Its natural final-only prefill policy is ported into independent per-context producer ownership. Its target-only guard is not removed or used to enable speculation.
- Isolated source changes implement local attention PQ/QB using existing ggml operators, independent target/draft phase binding, ub4 continuation, cache invalidation on role/phase/layout/geometry/capacity, actual VERIFY all-output positions, bounded diagnostic state/initial-logits evidence, and the inherited k1 acceptance/correction/bonus/rollback transaction. q1 remains the common upstream attention path.
- Original R uses the unchanged original executable/DLLs and original timer/caller. R_SHADOW uses the rebuilt ordinary/capacity1 path only. Four GGML numerical backend DLLs are byte-identical across roles; no shader, reduction kernel, model, sampler or precision change. The graph/llama DLL and actor are intentionally rebuilt and separately pinned.
- Both GGUF bodies, frozen driver dependencies and import libraries were freshly hashed. Target Q6_K: 33981adf6bae52c503fb5c24f72539010632f7ed290a56c1315a8cd50adca587. Draft Q4_K_M: 6f85a640a97cf2bf5b8e764087b1e83da0fdb51d7c9fab7d0fece9385611df83. Driver remains32.0.101.9034 with original body hashes. Template hash e10ca381b1ccc5cf9db52e371f3b6651576caee0a630b452e2816b2d404d4b65; inherited double BOS is retained.

## Actual CPU/build evidence

- MSVC x64 Release build succeeded. Detailed compiler/cache/dependency and binary hashes are in p0/BUILD_MANIFEST.json and p0/RUNTIME.json. Retained inherited compiler warnings are visible in complete build logs.
- Required fixed suite ran on this Windows host:70/70. Final combined suite:104/104, including34 new integration/raw rejection tests. These cover real serializer routing, immutable send bytes/no second lookup, binary/model swaps, effective_k0 versus native argv1, stage gates, load-failure accounting, source phase/cache guards, forged/truncated raw, wrong memory PID, contaminated counts and wrong capacity.
- Actual C++ metadata and terminal/rollback checks:49. Actual synthetic CPU arithmetic:40,960 element comparisons across query layouts/GQA/masks, max absolute difference8.76584e-6. This verifies CPU shape/storage behavior within tolerance; it is not bitwise stability, a B570 run or native qualification.
- Windows module enumeration, same-PID RAM sampling and actual CPU-helper GetProcessTimes/exit handling were exercised without a model/GPU. CPU-helper time is distinct from owned model seconds.
- Independent audit reconstructed1,200 historical PR92 raw records and passed20,400 checks. Historical controls/counterexamples remain historical; none qualifies a new slot.
- Exact source derivation reproduced byte-for-byte. New2,103,277-byte source/binary capsule was independently restored and all members rehashed. It excludes weights and credentials; old runtime/backend restore remains bound to the fixed PR97 CAS.

## Real serializer and executor

p0/PLAN_P1.json and p0/WIRES_P1.json bind all80 slots to normalized input, actual wire text/hash, binary role/hash, argv and recipe. No-draft effective_k0 maps to required native argv1. The validated immutable bytes are the bytes sent; no send-time registry lookup. All geometry fields here are declarations/code checks; actual GPU geometry remains NOT_OBSERVED.

run_p1.py requires an external author-confirmation receipt naming the exact F0 hash/budget, plus authenticated remote readback. It durably appends PROCESS_ATTEMPT before Popen, separately records requests and forward events, checks previous controls, stops on infrastructure/observer failure and retains valid treatment counterexamples. It refuses a previously attempted ledger rather than automatically resuming/replaying slots. Cleanup targets only its owned process object. Actual loaded module paths/hashes and Windows creation/exit timestamps are retained.

Safety thresholds are frozen:7200 cumulative charged owned seconds;300s per process;4GiB new run output; disk free≥10GiB; available RAM≥2GiB; owned working set≤12GiB; same-PID dedicated B570 signed headroom≥512MiB. Host and native safety samples are100ms plus checkpoints; neither proves continuous residency. Counts do not enable GPU timestamps/API dump/heavy readback or observation sync. Necessary phase-management synchronization and safety lifecycle costs stay in the measured native request window, including the safety sampler stop/join. Diagnostic captures are finite and listed in F0.

The adapter calls the independent raw auditor; the latter reads exact native stdout, actual wire, identity/lifecycle, raw counters, memory samples, ordered diagnostic trace, full initial FP32 payload and both handoff sequence byte arrays. It does not trust an executor-generated qualification boolean. VERIFY multirow requires phase-bound ordered native records and full output-position mapping, never a total histogram.

## Execution and scientific status

New model process attempts0; model request starts0; GPU forward starts0; operator starts0; owned model time0s; new scientific native output0bytes. All80 P1 coordinates are unstarted in p0/UNSTARTED_P1.json; no scientific failed slot or retry exists. Preparation/build/restoration artifacts occupy about1.06GB locally and are separate from future P1 run output. One scoped integration round is used; no second scientific port/search round has been consumed.

No new R, R_SHADOW or candidate endpoint has been observed, so all new complete-output qualifications are NOT_CHECKED. No genuine new multirow VERIFY witness exists. Request cost, regressions, panel qualification and all time-gated performance aggregates are WITHHELD. CPU checks do not fill these gaps. Old PR105 failed1 process/request,127 decodes,12.438s and167 unstarted slots are untouched; no restart or automation was made.

Producer adds independently owned natural prefill partition selection. Consumer adds local PQ/QB attention representation while preserving outer multirow caller intent. The combination adds phase/cache/state-ownership safeguards. Their numerical compatibility, actual VERIFY widths, complete-request cost and independent-input scope remain unmeasured. No unseen P2 panel is claimed; EXPOSURE_NOT_ESTABLISHED.

## Hardware first-stage judgment

HOLD_MISSING_EVIDENCE. H-L: new phase/cache logic may add graph/synchronization cost; completed GPU timing is absent. H-M: graph views share KV ownership syntactically; DRAM/cache traffic is absent. H-A: CPU layout differences and unknown GPU reduction DAG prevent an arithmetic-preserving hardware conclusion; same-resource strong software alternatives remain to compare. H-S: producer and handoff evidence paths exist, but no new natural model-state observation exists. Each explanation needs the already-planned source-bound P1 output/work/state evidence before any stronger claim. Dispatches, array concurrency, tensor operand metadata, XMX use, kernel times, residency, DRAM, cache, area and power remain UNKNOWN/null. No hardware model, RTL or PPA was implemented.

The next authorized boundary is author review of the remotely authenticated F0. P1 can establish control qualification and physical leverage; it does not authorize P2/P3 or imply hardware GO.
