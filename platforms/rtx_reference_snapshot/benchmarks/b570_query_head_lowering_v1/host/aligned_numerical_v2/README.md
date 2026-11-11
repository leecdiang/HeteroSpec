# Repaired-layout operator numerical panel: CPU preparation complete

Review base: `74d8bee4fd738c67e2f08169beb5164bac5efe98`.
Run identity: `b570-aligned-numerical-v2-20261015-01`.
**No GPU host, device query, support query or numerical graph has been started for this panel.**

The seven alignment diagnostics are closed at their recorded result. This directory
prepares a separate finite operator panel; it does not reopen their assertions or
reuse those graphs as repetitions. The original S1 remains **2 attempts / 5.109
owned seconds / 159 unstarted**. The independent diagnostic remains **7 attempts /
13.172 owned seconds / 5 successful graphs / 2 predeclared negative failures**.
Their files, F0s and accounting are bound read-only in the new F0.

## Implemented and tested

`host.cpp` and `fixture.hpp` implement one real GGML parser, builder and descriptor
serializer for the support census, numerical host and separate metadata-only CPU
executable. Both executables were compiled offline with the existing numerical
DLLs. The CPU executable alone was launched during preparation. Its actual wire
parsing produced **240 descriptors from all 161 formal requests**: 80 census
descriptions plus 160 numerical descriptions. Every census graph and its two
execution descriptions match exactly. All 80 graphs match the reviewed repaired
fixture's operations, source links, dimensions, strides and offsets.

The latest fresh suite passed **25/25 CPU methods** in 10.625 seconds (test receipt
`preparation/CPU_TESTS_03.json`). It covers all 80 independent Q/GQA/KV/mask address
mappings, all 80 complete four-stage layout restorations using labeled CPU
vectors, exact serializer bytes, q1 graph identity, analytic scalar FP64 GQA and
causal-mask checks, incorrect ownership/mask binding, truncated/nonfinite output,
mutated slab bytes, masked probabilities, module/resource records, incomplete
attempt accounting and approval rejection before launch. Synthetic analyzer test
files are explicitly marked CPU fixtures; they are not GPU evidence.

`reference.py` separately decodes each original stored input and freezes all four
scalar FP64 reference vectors. It imports no candidate graph or packing helper.
`analyzer.py` restores actual full QK, softmax, AV and final arrays to logical
query/head/element order, checks input and slab bytes, and separately reports
absolute/relative/ULP errors and the first divergence stage. A test with two
identical incorrect outputs still exposes the independent FP64 error. Ordinary
FP64 rounding differences have no numerical PASS cutoff.

`controller.py`, `native_audit.py` and `reconstruct.py` retain actual PID plus OS
creation FILETIME, loaded-module hashes before work and at close, resource samples,
complete supports_op, all root/view bounds and device ownership, actual executable
bindings, before/after inputs and all stage bytes. Missing lifecycle/output stays
missing; a started but incomplete slot is not counted as unstarted or filled with
zeros. No CPU numerical backend or hidden fallback is admitted.

Four prospective CPU preparation/build/test records and their source snapshots
are retained. A freezer import failure before F0 creation is also retained in
`preparation/FREEZE_FAILURE_00.json`; its sibling-module resolution fix has a new
regression test. None of these are scientific GPU attempts.

## Source and layout differences

The only storage repairs relative to original S1 are Q0 independent storage for
every representation and independent per-query PQ mask slabs for q>1. Logical
Q/K/V/mask bytes, Q shape/stride, original 32-row mask storage, K/V shape/stride,
F32/F16 types, precisions, scales, causal/dyadic generator, K63/257 and arithmetic
operations remain fixed. The old Q+32 layout remains a historical failure and
boundary case in the old directories. No historical layout is reclassified.

The existing real QH_C CONT, QH_D mask REPEAT, REPEAT4 KV REPEAT, concatenation and
output restoration are preserved through the unchanged `native/query_head.h`.
All q1 labels use the same original common graph at Q0. PQ q>1 retains its
otherwise disconnected original mask views as metadata; only actual executing
bindings impose descriptor-alignment conditions.

The new host adds prospective input/physical-layout/module/binding/stage logging
and the census adapter. The new controller serializes independent process starts
and stops on structural/control/resource failures. `BUILD_INPUTS.json` freezes
pinned headers/JSON tree/import library/compiler/linker/CMake identities and
rechecks the previously reviewed numerical backend source hashes. The frozen
backend/DLLs were neither modified nor rebuilt. Driver and environment identity
remain the previous diagnostic's identities; current dynamic alignment is unknown.

PQ's incremental CPU copy, API upload, logical bytes and allocator rounding are
reported separately for each actual run. Under the frozen required interface
condition of 64 bytes, the planned increments per PQ graph are:

| q | K63 logical/copy/upload bytes each | K63 rounded bytes | K257 logical/copy/upload bytes each | K257 rounded bytes |
|---|---:|---:|---:|---:|
| 1 | 0 | 0 | 0 | 0 |
| 2 | 504 | 512 | 2056 | 2176 |
| 3 | 756 | 768 | 3084 | 3264 |
| 4 | 1008 | 1024 | 4112 | 4352 |

These are planned byte counts, not measured traffic/residency. The full panel
adds 46,080 bytes each of logical PQ slab storage summed across runs, CPU copy and
API upload; planned rounded allocation sums to 48,384 bytes. Original mask storage
remains in addition. Every charged host must read the actual interface value and
abort if it differs from the frozen condition; 64 is not a universal assumption.

## Exact proposed panel and stopping rules

The 16 already exposed synthetic inputs are exactly those in `host/S1_INPUTS.json`:
q1..4, K63/257, H8 with Hkv8/Hkv2. They are not unseen or natural actor inputs.
`PLAN.json` and all 161 actual `wires/*.wire` fix the execution order:

1. One separately charged support-only census of all 80 repaired graphs, with no
   graph compute. Every executing node must be supported; QH_C remains the fixed
   primary candidate and is not selected from census/output/time results.
2. All 40 q1 hosts, using original input-manifest order, then repeat0 modes
   MQ/PQ/QH_C/QH_D/REPEAT4 followed by repeat1 in the same order.
3. All 120 q>1 hosts in the same fixed original-input and representation order.

Each graph host has exactly one graph invocation. Every repeat is a fresh process.
The ceiling is **161 new host attempts / 160 graph calls / 3,600 cumulative owned
seconds / 180 seconds per host / 2 GiB**. Storage includes all v2 preparation,
build and output-root bytes plus one raw export reserve. Additional monitoring
conditions: sampled worker RSS <=8 GiB, available host RAM >=8 GiB, free disk >=4
GiB, nominal sample interval 100 ms and maximum actual gap 1,000 ms; GPU free
memory >=512 MiB at declared in-host checkpoints. No continuous residency claim.
Zero models, extra probes, warmups, scientific retries or expected-crash slots.

Stop later slots on any assertion/crash, unsupported graph, wrong device or
actual binding, input mutation, nonfinite output, q1 common-path difference,
same-implementation independent-repeat bit difference, identity drift or
resource/observer violation. All four stages participate in q1/repeat controls.
q>1 valid finite differences remain fully recorded without changing inputs,
implementation, tolerance or coordinate inventory. All ten mode pairs per
input/repeat are reported. An incomplete panel names all invalid/unstarted slots
and cannot claim a full-domain result. Full strict rules are frozen in `RULES.md`.

## Frozen identity and pending author confirmation

New F0: `F0.json`

SHA256: `332c5d5d309a97f5073b7fd3d8228a5ef46ade7b87315632165251fe89b7786c`

It binds the new source, binaries, original numerical DLLs, driver/environment,
16 input identities, exact serializer/wires, 160-graph plan, separate census,
independent analyzer/reference bytes, CPU admission record and historical files.
`BINARIES.zip` preserves the exact new CPU metadata and numerical host binaries;
the original numerical DLL identities are retained as dependencies.

The sole numerical-panel entry, **not invoked during this preparation**, is:

```powershell
& 'C:/Users/DIANG/AppData/Local/Programs/Python/Python312/python.exe' 'C:/hs/b570-query-head-lowering/benchmarks/b570_query_head_lowering_v1/host/aligned_numerical_v2/run_panel.py' --author-approved-f0-sha 332c5d5d309a97f5073b7fd3d8228a5ef46ade7b87315632165251fe89b7786c
```

This entry requires explicit human approval of this exact F0 SHA, rejects an
existing run directory, rehashes frozen identities, and inventories OS processes
without querying a GPU before starting the one charged census host. Preparation
does not authorize execution. Actual support, bindings, independent GPU repeats,
all-stage GPU/FP64 errors and cross-mode results remain unknown.

S2/S3 and performance experiments remain closed. Owned time includes setup,
queries, upload, readback and logs and yields no speed claim. Any natural-actor
layout/mask review and full-request pilot requires a later separate review and
approval. PR112 stays Draft; no RTX, paper, main, release or automation change.
