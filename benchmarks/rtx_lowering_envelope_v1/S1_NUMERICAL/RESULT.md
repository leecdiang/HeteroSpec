# PR113 numerical substage: terminal native initialization failure

The author approved the exact720 predeclared full-tensor numerical slots,720 graph computations, zero warmups/model requests/timing hosts. The existing frozen executor was invoked once without changing source, binary, task, order, QH selection, budget or input. **This execution stopped on its first native slot; the panel did not complete.** No failed coordinate was retried or replaced.

|Layout|Planned hosts|Started|Completed|Failed|Not started after protocol stop|
|---|---:|---:|---:|---:|---:|
|MQ|144|1|0|1|143|
|PQ|144|0|0|0|144|
|QB|144|0|0|0|144|
|QH_C|144|0|0|0|144|
|QH_D|144|0|0|0|144|
|Total|720|1|0|1|719|

`ANALYSIS.json` retains all720 original coordinates individually. The719 unstarted coordinates are NOT_STARTED_PROTOCOL_STOP, not unexplained missing slots, unsupported graphs, failed numerics or successful omissions. The fixed selected QH_C is unchanged and has not executed. Earlier S1A's all-node support result is retained as a support predicate; it did not certify this runtime's ability to compute.

## Actual failure and accounting

Slot `S1/numeric/000/MQ/0`: Qwen layer0/prefill/q1, first MQ own-path repeat. Controller PID6448, native PID9628. Controller began2026-10-15T12:07:15.429946Z, elapsed18.977621078s, exit1. Native before-start epoch1792066051.2364936, lifetime3.129477500s, exit3221225620 / `0xc0000094`. The native graph-start marker exists with index0/warmup=false; no successful native RECORD, stage tensor bytes, ordinary output, or completed-interval receipt exists. Charge **one started graph computation**, with zero confirmed completed graph evaluations; actual kernel execution/count is unknown. Warmups0, model requests0, scientific retries0. Do not call this a zero-compute attempt or a numerical mismatch.

The single new readiness observation passed the unchanged policy: RTX5070 Ti Laptop, driver616.92,total12227MiB,used119MiB,util0%,43C,AC1; query0.055967200s. All7528 file identities were checked by the frozen controller before the start, and separately passed the retained post-stop disk-hash verification. Disk identity does not supply a missing GPU-input postcheck. The source control flow reached the graph-start marker after its allocation and pre-input checks; without a successful complete native record, executed operator/stream placement, post-input invariance and full loaded-module SHA qualification remain unqualified.

Cumulative S1 so far:2 native hosts including the earlier census,1 charged graph start,0 confirmed completed numerical graphs,0 warmups/model requests. Sum of native owned intervals4.737028100s against the unchanged7200s S1 ceiling. Whole controller wall envelopes are reported separately (16.399829388s census plus18.977621078s numeric); neither is kernel time, clean graph cost or speed evidence. The OS-created crash dump is charged to S1 derived storage. All raw, failures and unknown states are retained; original S0/PR104/PR110 budgets/data are not reused or rewritten.

## Offline diagnosis, without another native start

Windows Application Error/WER events for PID9628 and the existing OS crash dump independently identify `ggml-base.dll+0x1cf7`, exception `0xc0000094`. PE exports place this in **ggml_time_us+0x37**. Raw exception/context bytes show RIP at that instruction, **RCX=0**, and x64 `IDIV RCX`. The recorded64-byte fault-code context matches the frozen on-disk DLL exactly. Its preceding load reads the DLL timer-frequency global at RVA0xc0358; the original crash memory value is **zero**. The DLL's SHA matches F0. This confirms an uninitialized Windows timer divisor at the trap, rather than an observed QH numerical failure.

Build.ninja links the new host against static ggml-base.a, while the fixed numerical CUDA plugin loads the inherited ggml-base.dll. In the frozen source, ggml_init initializes the static core's Windows timer; the standalone host does not explicitly initialize the separate DLL's timer. This separate-state linkage explains why CPU integration and support predicates could pass while first graph compute faults. It is a source/linkage diagnosis, **not a tested repair** or a proof that timer initialization is the only remaining integration issue. No source/binary/library was patched, compiled or launched after the failure.

The complete original124,357,314-byte process dump and69,386-byte WER report remain locally read-only at paths/hashes in CRASH_RETAINED_ARTIFACTS.json. Full process memory can contain private environment data, so it is not published to Git. The archive contains the bounded raw exception/thread-context/code/timer-frequency capsule, full relevant native Windows events, module metadata and reproducible offline parsers. No arbitrary heap, environment or unrelated event is exported. This limitation is explicit; fresh remote CPU auditing verifies the archived capsule and all scientific raw, without claiming to reconstruct the entire privately retained dump.

## Qualification and next gate

|Evidence|State|
|---|---|
|Complete finite-registry CUDA support|Prior S1A PASS, unchanged|
|Numerical MQ own-path / PQ-QB controls / q1 / repeatability|NOT_OBSERVED; first baseline failed before output|
|QK,softmax,AV bitwise/max error/ULP/first divergence|Unavailable; no stage bytes, no substituted zero/error table|
|QH numerical behavior or advantage|NOT_EXECUTED|
|Full request endpoints / target-mask3/k3 economics|NOT_EXECUTED|
|Valid timing / profiling / hardware gain|NOT_QUALIFIED; profile remains unavailable|

The protocol states that illegal indexing, nonfinite violation, q1 mismatch, failed inherited own-path, wrong device/placement or mutation stops progression; the frozen executor also stops on a failed native host. This is a native infrastructure failure at the first required control. **The current numerical execution is terminal.** No remaining slots, timing/profiling or S2/S3 are authorized to proceed through this failure; no scientific retry is permitted. Any separate engineering correction and prospective protocol amendment must preserve this failed record, define how the invalidated run is treated, freeze exact new identities/budgets, and obtain author authorization before a new GPU start. This is not evidence against MQ/PQ/QB/QH mathematics or evidence of hardware need.

All new records remain under the PR113 isolated directory/branch. PR104/110, main, PR102/paper, B570, releases and automations are unchanged. PR113 remains Draft. Final raw authentication, fresh CPU reconstruction and local delivery receipts supplement this result after sealing.

## Authenticated failure delivery completed

Data commit `c4a53af368d7c0f63c77d3ed86fc00a6308a8625` was pushed before authentication. RAW_NUMERICAL_STOP.zip:724,193 bytes, SHA256 `9dcd5240662af7cc98bdca8a82316f42e062d158c7c03e50044d9238b8592c04`,47 members. Actual authenticated remote bytes of archive, manifest, full analysis, all720 slot rows and both reconstruction scripts matched local committed bytes. This substage had no transport failure; the earlier S1A transport failure remains retained separately.

A fresh directory verified every archive member, reconstructed exception code/RIP/IDIV-RCX/zero divisor and frequency from the bounded raw capsule, and regenerated full analysis plus720-row CSV byte-for-byte. It launched no new native/GPU host, graph compute, model request or device query. AUTHENTICATED_RAW.json/FRESH_RESTORE.json record that scope and the explicit limitation that the complete original private process dump/WER remain local by hash. User delivery hashes and complete current S1 derived-byte accounting, including that OS dump/report, are in DELIVERY.json. The failure is preserved as a terminal result, not completion of the numerical panel.
