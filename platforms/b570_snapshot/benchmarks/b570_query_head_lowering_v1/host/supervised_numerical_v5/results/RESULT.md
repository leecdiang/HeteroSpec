# v5 actual result: HOLD before native spawn

The exact approved PowerShell entry ran once from reviewed commit `4ea4d0a6777f330ca4be5eb74875dc1ba23f3af1`, run_id `b570-supervised-numerical-v5-20261016-01`, F0 SHA256 `ff596ea94e80a80d004bdb6c9236d0494687a597149baa0c03a77f75e507db44`. It returned exit1 under the frozen stop rule. No repair, retry, resumed slot, extra GPU probe or further experiment followed. Keep PR112 Draft. This occupied registration cannot be reused.

## Actual execution and missing coordinates

|Stage|Planned registrations|Admitted|Failed registration|Unattempted registrations|Experimental hosts|Graph calls|
|---|---:|---:|---:|---:|---:|---:|
|80-description support census|1|0|1 before spawn|0|0|0|
|A q1|8|0|0|8|0|0|
|B q2|10|0|0|10|0|0|
|C q3|10|0|0|10|0|0|
|D q4|40|0|0|40|0|0|

One registration attempt is not one experimental host. All69 native hosts are unstarted. All68 numerical registrations remain unattempted. Exact coordinates are enumerated in SUMMARY.json. Registered experimental monitor/auditor processes are0/138. PowerShell launcher PID42164, numerical controller PID46008 and post-controller CPU log-audit PID26076 are distinct roles; the controller exited1. Two storage-watch threads were created inside the controller, not two extra processes. OS-inventory helpers, preparation/build/test processes and independent CPU delivery tools are separately scoped, not a claim about the whole-machine process count.

Census index0, slot `eac04272f57ddf18426927f91618cc1aa06f41e2cbd637bc72e05e003e63184a`, stopped with:

```
storage watch failure: sealed storage changed: C:\hs\b570-query-head-lowering\benchmarks\b570_query_head_lowering_v1\host\supervised_numerical_v5\results
```

The frozen `supervise()` constructs Lease before its first STATE, REQUEST/JOB and native Popen. The census folder contains only WATCH_1.jsonl. There is no STATE/SPAWN, native lifecycle, monitor/auditor, support census, graph binding, input snapshot or vector file. Zero native hosts and graph calls follow from this control flow and the actual file inventory, not from substituting zero-filled outputs. Actual device alignment, support, bindings, GPU-memory checkpoints, native lifetime and native post-exit audit durations are absent/UNKNOWN, not measured zeros.

## What the launch evidence establishes

The frozen launcher used the new fixed external directory outside both protected roots. No outer stdout/stderr file redirection was added. The stdout file is empty; stderr contains the155-byte stop message. Both capture readers reached EOF, actual pipe capacities were8,192bytes each, and CLOSED.json has error=null, controller_exit_code=1, status=FAILED. External logs and all five closed files were fully certified and archived by the post-controller tool. External logging did not overflow. Actual external originals occupy20,473bytes; the full32MiB maximum including export remains charged.

Nevertheless the source/results watcher rejected a sealed-directory notification while Lease was being initialized. The raw failing notification action, writer and event timestamp were not saved. It is not established that external logs wrote there, nor is a particular file operation uniquely identified. The two separate author/preflight receipts in source/results were completed before the frozen launcher began; all subsequent result publication was after controller exit. Their actual paths and timing boundary are disclosed in LAUNCH_CONTEXT.json. No runtime delivery writer was deliberately launched. This does not identify or excuse the unknown notification. No assertion that the environment is now reliable, or that the CPU fixtures covered every production filesystem effect, follows from prior39-test qualification. Status remains HOLD.

## Separate clocks, supervision and storage

- Frozen numerical-controller engineering2.812s; through closeout2.828s.
- Whole PowerShell script-entry through completed log certification5,797,583,100ns (5.7975831s). Capture/close scope5,233,810,100ns. Post-controller CPU log audit0.562s. External command-runner wall6.3500285s is a separate scope, not substituted for the frozen engineering interval.
- No native process existed, so native lifetime/post-exit audit and runtime resource/directory gap qualification are N/A. No measured graph latency or speed is reported.
- OUT prelaunch watcher produced13 pulses, max read47,000,000ns and max effective interval94,000,000ns. HERE produced no completed pulse journal before rejecting the sealed change. This is not evidence that an overall runtime1s monitoring qualification passed, nor an observed1s gap failure. Strict1,000,000,000ns is unchanged.
- Prelaunch CPU identity/inventory2.157s verified1,091 bindings, all69 wires and unchanged old raw history. Both run directories were absent, SID matched, and OS inventory reported no conflicting compute task. Available RAM18,478,952,448bytes and disk free156,820,873,216bytes were prelaunch OS facts, not runtime samples or device queries. Authorization was recorded when handled at actual UTC, without inventing an earlier receipt timestamp.
- Post-stop independent frozen reconstruction0.640s and additional CPU evidence/binding certification1.469s are separately charged delivery tools. They started no experiment, graph or device query.
- Publication snapshot including all new preparation/build/CPU-test/run/result files, fixed32MiB external/export reserve, full raw-run export reserve1,253,717bytes and remaining1MiB delivery allowance totals264,250,852bytes, below1,073,741,824. Later small documentation/remote metadata consumes that remaining allowance. PUBLICATION_BUDGET.json records the snapshot and definitions. No evidence was deleted and no prior-run budget remainder was used.

## Numerical and independent reconstruction outcome

q1 controls0/8; repeats0/34 available and34 missing; mode comparisons0/124 available and124 missing; descriptive v3 q2 anchors0/10 available and10 missing. The frozen CPU analyzer explicitly enumerates every slot/pair and retains null relationships. Its legacy output filename V4_RECONSTRUCTION.json is preserved exactly; its run_id is v5 and its contents contain only this run's states. INDEPENDENT_RECONSTRUCTION.json is an authenticated publication of that fresh CPU result.

All40 q4 coordinates are unstarted. PQ/QH_C/QH_D/REPEAT4 equality, MQ AV-first divergence, cross-run trends, full QK/softmax/AV/final errors and first differing indices are UNKNOWN in v5. No new independent FP64-to-GPU errors or scientific counterexamples exist. Bound FP64 references remain unchanged; there is no new GPU vector to compare. This is not numerical PASS or a refutation of the old v3 counterexamples. Nonfinite counts and actual PQ copy/upload/storage costs are also missing; they are not measured zero. Existing mandatory PQ/CONT/REPEAT costs and all rules remain frozen, and no old output supplies a missing v5 sample.

## Complete evidence and immutable history

RAW_EVIDENCE.zip contains all17 registered evidence members /317,865 uncompressed bytes: the complete7-file run including explicitly labeled post-stop CPU reconstruction; all5 external originals;2 actual author/prelaunch receipts; and3 post-controller log-certification artifacts. The archive is55,147bytes, SHA256 `21fa6886f34f59d82d384677288bc159ff130ffd4ca956362350cf8f4e4db425`. All members were independently decompressed and rehashed against RAW_MANIFEST.json. Remote authentication is reported in the PR after the actual push/readback; this source does not preclaim it.

Frozen F0/source/launcher DLL/native/DLL/backend/input/wire/reference/analyzer and historical bindings all rehash unchanged.694 old v2 raw files,4,995 v3 raw files and7 v4 raw files remain authenticated. Only new v5 results are added. S1 remains2 attempts/5.109s/159 unstarted; diagnostics7/13.172s/5 success/2 declared negatives; v2 remains37started/36admitted/1invalid/124unstarted/36calls/41.327s; v3 remains117started/116admitted/1invalid/44unstarted; v4 remains one failed registration/zero native hosts or calls/68 numerical unattempted/3.156s.

No AV-only, natural decoder/actor, S2/S3, performance/profile, RTL or other GPU task follows. RTX, paper, main, release and automation are untouched. This result stops at evidence delivery; any future repair or new registration requires a separate instruction and any new GPU run requires a new reviewed exact-F0 authorization.
