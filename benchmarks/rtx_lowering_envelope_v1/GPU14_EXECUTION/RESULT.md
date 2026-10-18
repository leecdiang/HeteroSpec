# PR113 GPU14 independent engineering regression — PASS

Executed once after the author's explicit approval of reviewed commit
`9aefd4c722ac78421994052e41412c2c0417d73b` and GPU14 F0 SHA256
`65a6a60b726572305e29f73e2d852936af9e4c87d9740cba5f95f97f738bd290`.
The actual message and current recording time are in `AUTHOR_APPROVAL.json`.
Historical F0/registration statuses were not rewritten. No implementation, checker,
input, order, tolerance, selected QH variant or execution configuration changed.

## Execution and resource accounting

New run `pr113-timer-gpu-regression-v1`, root `D:/hs113-timer-gpu14-v1`.
All 14 native hosts started, all 14 graph calls returned successfully, all 14
explicit post-compute full-device synchronizations returned successfully, and all
14 completed full-output and independent numerical/control admission. Failed: 0;
unstarted: 0. Exactly one graph call per fresh host. No retry, model request,
warmup, additional support host or alternate QH layout.

| Item | Actual | Frozen maximum |
|---|---:|---:|
| Native processes / graph attempts | 14 / 14 | 14 / 14 |
| Explicit readiness processes | 14 | 14 |
| Controllers | 1 | 1 |
| Controlled starts, unique PIDs | 29 | 29 |
| Node support API queries | 166 | 166 |
| Native child lifetime sum | 7.804875 s | Included below |
| Readiness child lifetime sum | 1.1517179 s | Included below |
| Controller wall envelope | 35.2747007 s | 900 s |
| Conservative owned bound (controller wall × 2) | 70.5494022 s | 1800 s |
| Largest slot output | 10,642,547 B | 12,582,912 B |
| Complete raw root | 87,801,730 B | 201,326,592 B |

Every readiness query admitted the original RTX 5070 Ti Laptop GPU, driver
616.92, 12,227 MiB and AC power under the frozen idle/temperature/headroom gates.
The original `GGML_CUDA_DISABLE_GRAPHS=1` setting was retained. Source-bound calls
perform one backend load and CUDA0 initialization per host; internal driver API
and kernel invocation counts remain UNKNOWN. Ordinary shell, Git, archive and
CPU-only audit processes are delivery tooling, separate from the 29 controlled
experimental starts. Their storage is included in final `ARTIFACT_ACCOUNTING.json`.
No device/native execution is performed during packaging or reconstruction.

These are engineering lifetimes including observation and I/O, **not clean timing,
kernel timing, a speed comparison or acceleration evidence**.

## Public q1 controls, before q2

| Fixed original coordinate, MQ only | Fresh processes completed | Original MQ QK/softmax/AV | Input/own-path/placement | Independent repeat |
|---|---:|---|---|---|
| Qwen layer0/prefill/q1 | 2 | Bitwise equal | PASS | Bitwise equal |
| SmolLM2 layer0/prefill/q1 | 2 | Bitwise equal | PASS | Bitwise equal |
| Llama layer0/prefill/q1 | 2 | Bitwise equal | PASS | Bitwise equal |

All six qualified controls completed before q2. This regression runs q1 MQ
controls; it does not add new q1 executions of other layouts.

## Fixed Qwen layer0/prefill/q2

All four layouts ran twice in separate processes, in frozen MQ, PQ, QB, QH_C
order. Each layout's QK, softmax, AV and ordinary output repeated bitwise.
MQ reproduces the original MQ snapshot at every stage. PQ and QB reproduce their
corresponding original PR104 stage bytes and agree bitwise with each other.
**QH_C agrees bitwise with PQ and QB** at all three stages and ordinary output.
All outputs are finite. Each ordinary output equals its own canonical AV restore.

PQ, QB and QH_C each differ from MQ with the following identical comparisons in
both repeats. The first divergent stage is **QK**; these are retained finite
empirical differences under the original numerical rules, not execution failures.

| Stage, each of PQ/QB/QH_C versus MQ | Bitwise | Different f32 words | Maximum absolute error | Maximum ULP |
|---|---|---:|---:|---:|
| QK | Different | 9,403 | 0.027706146240234375 | 9,854,240 |
| softmax | Different | 59 | 0.0000743865966796875 | 25,794 |
| AV | Different | 4,076 | 0.00007525086402893066 | 87,552 |
| Ordinary output | Different | 4,076 | 0.00007525086402893066 | 87,552 |

Complete pairwise comparisons, including MQ–PQ, MQ–QB, PQ–QB and QH_C against
each arm, are in `ANALYSIS.json` and each immutable `raw/NN/AUDIT.json`.
No tolerance or all-layout MQ-equality requirement was introduced.

## Shared-core repair on the actual CUDA path

All 14 processes verified the original absolute core path and SHA256
`b9243e8686a2b423b662e528f818a3744146d0245c2a8a42d3b4d5bf8eaa9704`.
Host ggml_init IAT targets and resolved ggml_init/time exports belong to that
same loaded ggml-base.dll. Exact core initialization returned before the explicit
CUDA plugin load. The original registry DLL path/hash and host registry IAT were
verified. All 41 CUDA plugin core IAT symbols per process resolve to the actual
exports of the same core module (574 checked entries). A separate CPU re-audit
also checks each actual address against the frozen PE export RVA and module base.

All 166 queried graph nodes report CUDA support; all 116 nonmetadata nodes pass
the frozen CUDA buffer/placement checks. No scheduler fallback is used. All 14
graph node geometries, dtypes, op parameters, source edges and output descriptions
match their frozen CPU graph records. Complete Q/K/V/mask input bytes before and
after execution equal the original snapshots. QK/softmax/AV/ordinary are retained.
Thus shared module identity and initialization work on these actual CUDA calls;
the earlier integer-division crash did not recur in this independent regression.

Post-run streaming hashes verify all 7,808 F0 pins, including all 21 numerical
DLLs, original models, driver files, source, new host and import libraries.
All reviewed tracked bytes remain unchanged. Loaded module paths and post-run
disk hashes are recorded, including injected system modules; this is not full
in-memory module attestation or proof of all possible runtime preconditions.

## Historical separation, raw and limitations

The original numerical run remains **1 started/failed, 719 unstarted, 0 confirmed
completed**, with old startup/cost/inputs/F0/binaries and raw archive unchanged.
Nine live old failed-slot files still match their sealed hashes. No new data is
written into those slots. Historical failed archive SHA256 remains
`9dcd5240662af7cc98bdca8a82316f42e062d158c7c03e50044d9238b8592c04`.

`RAW_GPU14.zip`: 23,264,913 B, SHA256
`f1dc041ad50400b3c11c874d5a94db9fba960d17ec20361df21a2871d8c3102f`,
575 members / 109,401,883 B expanded. Manifest covers every new raw slot and
controller file, actual approval, frozen execution/checker/source/host/import
artifacts, full reference snapshots and historical PQ/QB stage bytes. Original
numerical DLL/model bytes remain in their sealed read-only locations by hash.
`analyze_gpu14.py` re-runs the unchanged independent auditor without native/GPU
work. `AUTHENTICATED_RAW.json` and `FRESH_RESTORE.json`, added after the data push,
record actual remote byte verification and fresh-directory CPU reconstruction;
they are required closure evidence, not implied by local packaging alone.

This establishes bounded engineering admission for these 14 graphs. It permits
**preparing a formal numerical-v2 review**; it does not authorize that execution.
Formal v2 requires its own new run_id/F0, prior budget and later explicit human
approval. Support qualification must be reviewed for the revised host, with any
necessary remeasurement budgeted prospectively. No full-registry support transfer
is inferred from the 14 graphs.

Unresolved: untested panel coordinates/layers/phases/q values, general numerical
equivalence and accuracy relative to an independent mathematical ground truth,
complete actor linking/initialization/serializer/request and target-mask3/k3
transaction qualification, performance/copy cost, clean timing and profiling.
Kernel/reduction-tree identity remains UNKNOWN. S1 timing/profile, formal720v2,
S2/S3 and model requests stay unadmitted. No QH speed or hardware-benefit claim.
PR113 remains Draft; PR104/110, B570, papers, main, releases and automations are
unchanged. No automatic next GPU stage is launched.
