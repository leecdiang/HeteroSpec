# S0 real-GGML result and executed S1 closeout

**S0_COMPUTE_COMPLETE / STOP_S1_REFERENCE_RUNTIME_ASSERTION.** This is a new PR112
candidate study, not a continuation or requalification of PR109/111.

After explicit author confirmation of exact F0 `8935c7cb...3a0fb7`, S1 ran on
2026-10-15. The support-only census completed; the first q1/MQ reference graph
aborted in the frozen Vulkan backend. There are **2 charged attempts, 1 complete
capability host, 1 failed graph host, 159 unstarted slots, 0 completed graphs**.
No numerical candidate result or native endpoint qualification exists. S2/S3
are not admitted. See the executed closeout below and S1_RESULT.json.

The recovered frozen GGML base/CPU DLLs actually evaluated all **432 fixtures /
2592 graphs** across MQ, PQ, QB4, QH_C, QH_D and REPEAT4. q1/q2 development216
ran at082cfa11; q3/q4 fixture outputs216 ran after the7ed152cf lock, using the
identical executable and scalar/address implementation. These latter geometries
had already appeared in delivered toy tests; no unseen-geometry or natural-input
claim is made. No numerical retry, precision change or tolerance search.

## Results

- 40 delivered Python test methods and48 descriptor-only C++ cases pass. The mock
  include path is separate from the real target's recovered ggml.h; mock output
  is not counted as GGML evaluation.
- All432 real fixtures completed: no crash, nonfinite result, exact one-hot/
  single-key assertion failure, integer-address, GQA, mask-column, input mutation
  or bit-preserving output-recovery failure. q1 executes six actual original
  nonflash chains, not a nullptr shortcut. QH_C/QH_D retain identical K/V objects.
- Full raw final vectors: PQ=QH_C in432/432, PQ=QH_D in432/432,
  QH_C=QH_D in432/432, MQ=REPEAT4 in432/432, all bitwise on this CPU backend.
  This is not an assertion about Vulkan reductions or deployed model endpoints.
- Relative to independent stored-input FP64 math, all layouts retain QK max
  absolute error0 for the predefined dyadic/one-hot data; softmax maximum
  absolute error3.729331905788502e-9 and maximum float32 ULP3; AV/final maximum
  absolute error3.0914862265095204e-5. Large ULP distances near zero are retained.
  These are distributions, not a chosen PASS tolerance. The oracle is independent
  of the candidate's packing/GQA/output helpers.
- Inputs are checked byte-for-byte before/after every graph, including Q base
  offset/padding. All stage vectors, native ne/nb/dtype/precision/source-node
  records and final vectors are retained. The raw auditor independently checks
  complete matrix/shape/mask/GQA relations and full-vector file arithmetic;
  scalar FP64 metrics come from the separate compiled logical oracle.
- 2 owned CPU worker processes,30.452 seconds conservative owned wall, sampled
  peak RSS21,286,912 bytes. CPU wall includes graph construction, scalar audits
  and raw writes; it is not a GPU/request performance benchmark. All current
  host_outputs (including actor compilation) total about325MB, below2GiB.
- During S0: new model processes/requests=0; GPU operators/forwards=0; device queries=0;
  extra probe/warmup/retry=0. Actual CPU process module inventories/hashes are
  recorded. Only explicitly staged frozen ggml-base/cpu are used by S0.

S0_RAW.zip contains12,752 new evidence files,20,304,946 bytes compressed, with
an exact SHA256 manifest and a streaming archived-byte recheck. It restores only
this finite new CPU evidence; no repeated historical restore. Old models and29
runtime/model files were streamed and matched fixed local-byte hashes, including
the original R and unchanged old F0. No claim about official conversion ancestry.

## Useful scope and costs

The reusable representation condition is: preserve r=h*q+j, contiguous GQA
groups, per-query mask r%q, actual Q packing and ordinary output restoration,
while keeping K/V fourth axes singleton and K/V objects shared. This crosses
the **specific** old fourth-axis predicate, not complete Vulkan admission.
Compact Q can be reshaped; model-permuted Q requires an actual CONT. QH_D's
mask and REPEAT4's K/V are actual REPEAT operators, not CPU-filled results.
The frozen softmax API also requires contiguous masks; wider padded-stride
contracts must not be inferred from the prototype's broad input check.

Example q2,K257,H16,Hkv4,permuted Q, actual logical materialization destinations:

| Mode | Destination bytes from CONT/REPEAT/CONCAT |
|---|---:|
| MQ |16,384|
| PQ |32,768|
| QH_C |32,768|
| QH_D |65,664|
| REPEAT4 |1,069,056|

These count logical destinations, not DRAM, peak liveness or timing. QH_C's
Q pack can consume as many destination bytes as PQ's output organization.
Fewer attention chains alone does not prove a benefit over strong PQ. Head/query
packing, target legality and batch invariance are prior ideas (DESIGN.md cites
their primary sources). Current status is an executable method candidate with
bounded CPU evidence, not verified novelty or reference-compatible speedup.

## Native and execution engineering

An actual inherited k1 actor and graph library were ported and offline-compiled.
The native adapter admits only q<=2, explicit PQ/QH_C/QH_D layouts, per-context
role/phase/layout/mask-variant/capacity identity plus upstream n_tokens reuse
checks. Target/draft ownership, pending/bonus/reconciliation and original q1
path are inherited. Its real parser uses normalized112;128 CPU wire roundtrips
cover64 planned slots x2 potential mask variants. No variant is selected yet.
The original R executable remains original; no new shadow replaces it.
The new actor's periodic receipt declares its actual100ms thread (nominal,
not a hard actual-gap guarantee); old R checkpoint semantics remain unchanged.
S2 execution/observer/raw qualification still needs the S1-selected variant and
a separate exact S2 F0. Compiling this actor is not native admission.

Failures are retained: initial native actor build missed the inherited
native_memory_budget.h. Scoped revision1 copied that byte-identical header;
the actor then built successfully. The numerical harness/candidate was never
revised or rerun. During prospective F0 completion, a CPU gate test caught
duplicate Windows/POSIX source-lock keys with an obsolete hash. Scoped metadata
repair2 canonicalized the keys, keeping both unapproved drafts and the failed
test receipt. Final7 host gate regressions pass. No numerical outputs were used
for either repair. Offline compile warnings and all build attempts are retained.

## S1 executable preparation

Before S1 approval, qh-vulkan.exe was compiled without launch. It explicitly loads only the frozen
Vulkan DLL, queries actual complete supports_op for every executable node,
waits for a parent runtime-hash gate, and uses direct Vulkan backend execution
with actual buffer-device checks. Metadata views are separated from executable
nodes. There is no scheduler/CPU fallback to disguise as Vulkan work.

The real serialized executor records exact wire/command/PID/lifecycle and
append-only attempts; bounds owned time/RSS/output/host RAM/disk; retains failed
and unstarted slots separately; gates runtime modules before support/compute;
freezes support-only selection before numerical outputs; and independently
checks GPU input-before/after bytes/SHA256, full output dimensions/finiteness,
q1 controls and repeats. Compilation/CPU tests did not establish these GPU
behaviors. The executed census, partial graph and missing evidence are separated
below. A static batch condition is not full supports_op.

Concrete approval object: **S1_F0.json**, SHA256
`8935c7cb5369ec052d074f060d9519ac51311620830819b74be5e3c49d3a0fb7`.
16 fixed operands, one charged support-only census plus at most160 graph hosts;
161 attempts/3600 cumulative owned seconds/2GiB, zero model requests and no
extra probe/warmup/retry. Operator GPU memory monitoring is explicitly
checkpoint-based; the100ms supervisor samples owned RSS/host RAM/disk/wall,
with a prospective1000ms maximum actual gap. No continuous-residency claim.
First choose QH_C from the full census, otherwise QH_D, otherwise STOP. Actual
placement, Vulkan numerical correspondence, natural decoder endpoints and useful
cost remained unknown before S1. All64 S2 requests and S3 remain unstarted.

No GPU command was run under S0. HOST_PROMPT.md explicitly says
"准备并申请 S1，不自行启动". The author's subsequent "确认" approved this exact F0;
S1 was then executed once. S2/S3 still need their own gates and approvals. No new automation, merge,
old-study restart, RTX/paper/release change, hardware simulator, invented DRAM/
cache/XMX/timestamp/arithmetic-DAG/residency/PPA result or hardware-necessity claim.

## Executed S1: support API admission did not ensure runtime admission

The immutable F0/source/input/executable/driver hashes were checked before launch
and independently rechecked after stop. Both actual owned processes identified
Intel Arc B570 / Vulkan0 and loaded the frozen base/Vulkan numerical DLLs. No
ggml-cpu numerical module was admitted. The raw parent runtime gate preceded
the capability or compute activity.

| Representation | Complete cell support queries | Executable-node predicates true | Completed numerical graphs |
|---|---:|---:|---:|
| MQ |16/16|64/64|0 (first graph failed)|
| PQ |16/16|184/184|0 (unstarted)|
| QH_C |16/16|76/76|0 (unstarted)|
| QH_D |16/16|88/88|0 (unstarted)|
| REPEAT4 |16/16|88/88|0 (unstarted)|

The complete80-cell/representation census includes actual supports_op of every
executable node, with metadata nodes retained separately. All500 executable-node
queries returned true. The frozen rule chose **QH_C** before the first numerical
attempt; this choice was not made from numerical outputs or speed. Support-field
meaning is exactly the backend API response, not successful execution.

The first graph was **MQ, q1, K63, H8/Hkv8, permuted F32 Q with32-byte base
offset, F16 K/V, causal dyadic input**. It passed the precompute supports_op
checks; its four executable node buffers belonged to Vulkan0. All four input
before-readback byte vectors match the frozen serialized source independently.
After GRAPH_START, the process exited with3221226505 (`0xc0000409`), logging:

```
ggml-vulkan.cpp:8301: GGML_ASSERT(allow_misalign || misalign_bytes == 0) failed
```

There is no GRAPH_RETURN, after-readback, stage/final F32 vector, or CLOSE for
that process. Thus buffer assignment is observed before the call, not proof of
completed Vulkan arithmetic. No QH graph was launched. The source assertion
requires descriptor alignment unless its call site allows a misaligned offset;
the exact faulting tensor/call site and device minimum alignment were not captured
and remain unknown. The32-byte Q view and K63/V row strides are retained rather
than changed to make the run pass. No shader/backend/input repair or retry.

This is a bounded runtime/reference admission failure of the frozen experiment,
**not a QH-versus-PQ numerical counterexample** and not proof that QH is
intrinsically unusable. It establishes a reusable limitation: a complete positive
supports_op census is insufficient to certify actual execution for these physical
layouts. S0's CPU correspondence does not close that gap. There is no evidence
of useful GPU cost gain, natural-decoder compatibility or transfer, so the present
study stops with this finding and does not proceed to S2/S3.

Actual S1 accounting: census0.719s + failed graph4.390s = **5.109 owned seconds**;
2/161 attempts,0/160 numerical graphs completed,159 unstarted,0 skipped as
unsupported,0 model requests/warmups/retries/extra probes. Max sampled observer
gap485ms, peak sampled worker RSS253,112,320bytes. GPU memory observations are
checkpoints only. Initialization/census/failure elapsed time is not graph latency
or end-to-end speedup; completed per-shader work remains unknown.

`S1_RAW.zip` retains every first-run wire/raw/stdout/stderr/lifecycle, the complete
census, pre-output choice, ledger, closeout and precompute input bytes:679,680 raw
bytes in47,582 compressed bytes. `S1_RAW_MANIFEST.json` and
`S1_RESTORE_RECEIPT.json` verify all archived bytes by streaming rehash.
`S1_SLOT_ACCOUNTING.json` names every completed/failed/unstarted coordinate;
`S1_SUPPORT_MATRIX.json` preserves all80 census records. `close_s1.py` reconstructs
these records without launching a worker. Prior FINAL_VALIDATION/readiness files
remain historical pre-S1 receipts; S1_RESULT.json is the current status.
