# Local query representation portability: bounded CPU follow-up

**CLOSE_B570_PORT_WITH_REUSABLE_FINDINGS.** No semantic fix or new GPU request.
The output is reusable validation infrastructure and a concrete frozen-backend
capability finding. It is not a new inference algorithm or validated routing method.

Analysis is stacked on PR109 `039a24bf61374042e0dc9f3a3619ea40b218a5ad`;
original execution code `bb803c94f23af0e5ab4e250c52f74e0b60621a66` and PR108
design `8d7b85d8aac6e546ca23e1f8a6ad353ea7ed2e02` remain unchanged. Both remote
Draft heads matched these pins at the start. Original F0 SHA256 remains
`29cf422ef631edfa45ba55b56947926e1977070b8957dbc362e4e5581401d6e8`.
Original **49 process/request attempts, 48 complete, 1 interrupted, 31 unstarted,
8110 native callers, R sampling violation and 14 endpoint counterexamples**
remain NO-GO. Nothing resumes P1/P2/P3, PR105 or RTX work.

## What is now answered

`endpoints.py` independently reads raw stdout RESULT events, request wire,
identity and lifecycle bytes, checks the existing CAS manifest and reconstructs
all 48 full endpoints. The interrupted slot has no invented endpoint.
[Endpoint classes](ENDPOINT_RELATIONS.md) distinguish full IDs/EOG/length/
terminal/stop equality from equal match counts or equal first differences.
M_B_QB equals C_B_PQ on all four complete endpoints; M_R_QB equals C_R_PQ
on all four; C_B_MQ equals C_B_QB on all four. Other same-producer pairs can
differ. These are CAP128 observations, not operand/KV identity proofs.
M_R_QB is q1/common-path evidence; C_R_PQ 4/4 is not full qualification.

The frozen build identity from `b570_partition_intervention_v1/BUILD_IDENTITY.json`
(SHA256 `5113198de3e0be1228185c922d48caa9b39d8f58ad573f185666c8d0735f70da`)
pins source bytes and the same inherited numerical DLL hashes. Seven core
ggml header/CPU/Vulkan source files match. This binds local bytes; it does not
claim a reproducible binary rebuild or certified upstream ancestry. Three
shader bodies exist locally but lack individual frozen manifest binding and
are explicitly SOURCE_UNAVAILABLE for interpreting this numerical DLL.

The decisive source property is `ggml-vulkan.cpp:18976`:
`ggml_backend_vk_device_supports_op` rejects MUL_MAT when source batch3 differs.
In original q2 QB, K/V batch3=1 while Q/probabilities batch3=2, so **both QK
and AV fail this frozen Vulkan support predicate**. This is independent of
the tested key extents and Q storage. PQ/MQ retain matching source batch3.
The specialized permuted matvec also requires one column and both source
batch3=1 plus stride/device limits. The general vector branch is different:
it can handle batched vectors; do not turn the special-case restriction into
a universal matvec claim. Actual native assignment, copies and GPU dispatch
remain UNKNOWN. Source rejection predicts fallback through a compliant
scheduler, not the measured placement or root cause of old endpoint differences.

## H1-H4, kept separate

| Hypothesis | Result and limit |
|---|---|
| H1 semantic/state mapping bug | No address, broadcast, mask-column or output mapping failure found in the bounded synthetic CPU matrix; structured exact expectations hold. GQA uses contiguous head groups, verified against frozen CPU indexing. Source cache guards and a pure per-context model reject q1/q2 topology reuse and cross-phase/layout identity changes. This does not exclude native asynchronous lifetime, actual binder or unseen-shape bugs. No fix candidate. |
| H2 different numerical/backend path | Concrete source-level capability difference established: original QB q2 fails Vulkan MUL_MAT support. MQ/PQ have distinct reachable matrix/vector paths under reviewed operands. This supports a backend-path concern, without establishing observed native placement, reduction differences or endpoint causality. No H2 conclusion is inferred merely from absence of H1 failures. |
| H3 execution costs | PQ has two attention chains/cont outputs and concat; QB can cross backend capability boundaries. Optional V transpose/cont and binder synchronizations are source-visible costs. Actual fallback transfers, timings, bottlenecks and total economics are unmeasured. Old request walls remain descriptive, with no qualified speedup. |
| H4 natural state/transaction trajectory | Still unresolved. Full-endpoint relations are now precise, but candidate diagnostic/operand/KV snapshots are absent. Same producer, early token prefix, or final endpoint cannot certify intermediate state identity. No state-distance estimate. |

## CPU evidence and failures

Input rules were committed at `b69a9cd3` before any new fixture ran.
Development ran at `f14ee719`; rules were locked at `7044ad1b` before the first
holdout. The exact same compiled executable and numerical/address source
hashes were used for both groups. First holdout results are retained.

- 72 geometries: q1/q2; K127/128/129/255/256/257; heads (8,8)/(8,1)/(32,8);
  compact Q or model-style permuted Q with 32-byte legal base offset; D=128.
- 432 synthetic fixtures: 144 development, 288 holdout; three nonempty masks
  and two fixed data patterns. 1296 CPU graph computes, including 648 executed
  common-original q1 graphs and 648 q2 MQ/PQ/QB graphs. PQ contains two
  attention chains per q2 graph. These are not real prompts or model requests.
- No crash, exact-address/structured assertion failure, or nonfinite output.
  Coordinate comparisons cover 1,546,739,712 logical address assertions; this
  is a coverage count, not CPU instructions, shader count or arithmetic DAG.
- Four independent symbolic negatives detect query-offset reuse, modulo GQA,
  reused mask column and output recombination errors. They mutate exported
  descriptors/rules, not the numerical DLL. Four initial illegal-input
  rejections and 14 final checker rejection cases are excluded from coverage.
- General FP64 comparisons retain abs/relative/float32 ULP distributions at
  QK, softmax, AV, permute and final output. Across all layouts: QK max abs=0
  for these dyadic inputs; softmax max abs=5.36080310351017e-9, max ULP=4;
  AV/final max abs=5.513250481611193e-5. Large ULP distances near zero/sign
  crossings are retained, not discarded. No general tolerance is selected.
- Structured one-hot QK and single-valid-key softmax/AV/final expectations
  are strict exact checks (216 structured fixtures; 72 single-key structured
  fixtures). Input values are compared after storage conversion. Dyadic Q
  values are F16-representable; exact QK here does not establish generic F32
  input/reduction invariance. Frozen CPU paths may convert F32 operands to
  F16 vector-dot format; the oracle retains the original stored values.

`CPU_RESULT.json`, `COVERAGE.csv`, immutable DEV/HOLDOUT per-fixture summaries,
receipts and failure witnesses support these statements. No large numerical
arrays are committed. Two CPU harness processes took 8.813 seconds of measured
runner wall time including process startup; the total engineering task also
includes analysis/compilation and is not a performance benchmark.

There were zero numerical-harness/frozen-implementation revisions and no
compile failures (one successful isolated compile, two bounded integer-narrowing
warnings retained in BUILD_00). Two evidence-scoped infrastructure revisions:
(1) static checker gained explicit K/V/mask buffer, backend-version and role/
phase preconditions; (2) cache model gained separate target/draft contexts,
two abstract-model cache hits and two q-width reuse rejections. The earlier
conservative single-state toy result is preserved. Neither revision reran
attention fixtures or claims independent holdout validation for its new code.

Actual loaded modules are recorded for the Python analyses and CPU harness
at entry/explicit load and around each fixture. Only frozen ggml-base and
explicitly loaded ggml-cpu are staged; the harness links no llama/ggml backend
discovery library and calls no device/queue API. No GPU/model module appears.
New model processes=0, requests=0, GPU forwards/operators=0, probe=0, warmup=0,
retry=0. No background job or future execution is registered.

## One bounded engineering output

`conditions.py` checks declared logical shape, Q and K/V strides/bounds, mask,
GQA, phase/role, state provenance, implementation and backend version. It
separates static legality, synthetic CPU evidence, source GPU support, actual
backend observation, full-request qualification and cost eligibility. It does
not consume output IDs, first differences, margins or latencies; it chooses no
runtime arm, brand rule or midrequest switch. Unknown backend versions remain
unknown. The checker is validation infrastructure, not an observed coverage or
cost improvement over static-QB, always-PQ or always-R.

Potential value: avoid mistaking mathematically legal QB for supported GPU
execution and avoid invalid experiments. A method claim would still need
unseen-input/shape results showing useful reference-compatible coverage or
lower total cost against all three baselines, with actual assignment/state
evidence. This round establishes none of that.

The role-specific `monitor.py` reviews actual timestamps and sampling points:
8 original-R receipts are checkpoints, 40 new-worker receipts are periodic.
New-worker source starts a 100ms thread but its legacy requested field reports
null in counts/5 in heavy mode; those fields do not describe the actual thread.
Changing that field to null,5 or100 cannot make old checkpoint receipts satisfy
the old universal periodic claim. The first R receipt blocks the candidate
stage. Future example limits (nominal100ms/max-gap250ms/loss1000ms) are explicit,
prospective and unapproved; nominal100 is not a hard actual interval bound.
No old F0/receipt/executable is edited or retroqualified.

[No GPU request](NO_GPU_REQUEST.md) explains why the proposed 24/32-start
numerical comparison lacks a supported original-QB arm. A capability failure
or fallback would not be counted as a GPU numerical counterexample.
[Hardware handoff](HARDWARE_HANDOFF.md) gives the compact representation/backend
table, strong PQ comparison, source/unknown boundaries and prior batch-invariance
context. No hardware necessity, proprietary arithmetic, RTL, simulator or PPA
claim is made. Stop this B570 investigation here; reuse the tools and finding.
