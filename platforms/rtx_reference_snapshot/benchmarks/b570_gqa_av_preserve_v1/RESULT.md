# B570 GQA: preserve PQ AV arithmetic while broadcasting query batches

Parent: [PR131 `b5370cab`](https://github.com/leecdiang/HeteroSpec/commit/b5370cab7ce853d4b284e42e5515ffa50f1e8ce7). Run: 2026-10-20, fresh UUID `c2bdba94-d819-4191-b40e-21a227e0ea13`. The author explicitly authorized this targeted AV follow-up after PR131's failed attempt, carrying forward its remaining51.5894409s. The previous failure is retained unchanged.

**All six registered operator coordinates pass complete PQ/QB stage-byte equality.** This closes the tested AV discrepancy without changing the reference, tolerance or shader arithmetic. It is not model/request qualification.

## Fix

PR131 sent lifted QB's capacity-strided V through a compact copy and general matvec path, while PQ used the existing noncontiguous AV shader. At key512/q2, probabilities matched but7,160/8,192 AV floats differed.

This follow-up keeps that original nc shader for the exact registered AV domain. Its workgroup x coordinate already indexes tensor dimension3. For the scoped batch broadcast:

- V's batch stride is zero, so each query reads the same original V head.
- Probability and output batch strides retain their real values.
- Dispatch x extent follows the query batch count.
- Each output uses the same local32-lane workgroup, vector loads, dot/accumulation and shared-memory reduction as PQ. Independent query workgroups may execute concurrently; no cross-query reduction is introduced.

The helper requires F16 V/F32 probabilities, d128, Hkv8/Hq32, key256/512, capacity1024 exact V strides, q2/q4, and contiguous probabilities. Existing equal-batch calls retain their old addresses and dispatch extents; q1 does not enter the new allowance. Source-domain admission from PR131 remains unchanged. No shader was edited or recompiled:147 frozen objects were reused. No REPEAT, QH or KV replication.

CPU address checks establish equal V element bases and disjoint correct probability/output addresses across the registered domain. Actual GPU byte checks establish this panel's numerical result; the source reasoning alone is not a general floating-point proof.

## Unchanged panel and reference

The C++ test harness is byte-identical to PR131 (SHA256 `698b4d1ef3ebff952ad213f524ffc1cdb136b8307c72dfe1a163b4339c684dc7`). Same deterministic synthetic inputs, causal masks, full backing stores, strides and final output ordering. key256 follows the observed PR129 layout, key512 is derived, not a captured speculative request.

Reference remains explicit per-query PQ with QK F32 precision and inherited AV precision. In addition to same-run comparisons, all20 previously available PQ stage files were compared directly with the actual PR131 raw bytes and remained identical. The previously failed QB output is not overwritten or reclassified.

| key | q | QK bytes | softmax bytes | AV bytes | final bytes |
|---|---:|---|---|---|---|
| 256 | 1 | PASS | PASS | PASS | PASS |
| 256 | 2 | PASS | PASS | PASS | PASS |
| 256 | 4 | PASS | PASS | PASS | PASS |
| 512 | 1 | PASS | PASS | PASS | PASS |
| 512 | 2 | PASS | PASS | PASS | PASS |
| 512 | 4 | PASS | PASS | PASS | PASS |

Twelve graphs returned successfully on B570. All10 positive/negative descriptor controls passed. All full Q/K/V/mask backing-storage readbacks before/after matched. All produced stages independently passed the original FP64 tolerance in CPU reconstruction, and every PQ/QB stage has zero differing float32 elements. No performance timing was planned; parent wall time is accounting, not algorithm latency.

## Evidence and budget

PID45272, exit0, normal backend cleanup, complete stdout/stderr, no deadline kill; no lingering gqa process observed. Direct .NET launch,20s execution cap plus15s admission margin. No new Job/CPU8 guarantees are claimed.

| Accounting | Seconds |
|---|---:|
| Prior cumulative, including PR131 failure | 248.4105591 |
| New entire parent wall charge | 0.8368002 |
| Cumulative / original cap | 249.2473593 / 300 |
| Remaining | **50.7526407** |

The preregistration, launcher and181 frozen inputs were checked; the179 parent frozen inputs were also verified before this run. The build succeeds with existing upstream warnings. Patch application against the PR131 source passes. `analyze.py` rereads every returned raw stage and all backing input readbacks, independently recomputes FP64 results and verifies reference continuity. This is same-machine CPU verification, not external independent review or CI.

`RAW_EVIDENCE.zip` contains every new result file. `SOURCE_SNAPSHOT.zip` holds parent/candidate sources, graph header and unchanged shader text. The local root retains binaries, build logs and original raw. Archives are checked byte-for-byte after creation; repository files are checked by Git blob identity after upload.

## Scope and next boundary

This author-authorized follow-up satisfies the complete six-coordinate synthetic GQA operator gate. It does not establish general GQA support, arbitrary strides/types, actual speculative q>1 state, request endpoints, runtime graph-cache integration, natural KV maintenance or end-to-end speedup. The nc path's internal packing avoidance is not separately timed here.

The next scientific step is a separately frozen native request bridge using the existing speculative state protocol and explicit request reference. Its actual geometry, integration/source identity and full budget still need to be resolved before execution; this PR does not launch it. No model, actor, RTL, CPU8 framework changes, budget reset or merge occurred.
