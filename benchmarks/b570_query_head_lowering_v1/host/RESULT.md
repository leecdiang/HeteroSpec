# S0 real-GGML result and S1 admission request

**S0_COMPUTE_COMPLETE / S1_AWAITING_AUTHOR_APPROVAL.** This is a new PR112
candidate study, not a continuation or requalification of PR109/111.

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
- New model processes/requests=0; GPU operators/forwards=0; device queries=0;
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

## S1 is concrete but not started

qh-vulkan.exe is compiled, not launched. It explicitly loads only the frozen
Vulkan DLL, queries actual complete supports_op for every executable node,
waits for a parent runtime-hash gate, and uses direct Vulkan backend execution
with actual buffer-device checks. Metadata views are separated from executable
nodes. There is no scheduler/CPU fallback to disguise as Vulkan work.

The real serialized executor records exact wire/command/PID/lifecycle and
append-only attempts; bounds owned time/RSS/output/host RAM/disk; retains failed
and unstarted slots separately; gates runtime modules before support/compute;
freezes support-only selection before numerical outputs; and independently
checks GPU input-before/after bytes/SHA256, full output dimensions/finiteness,
q1 controls and repeats. These GPU behaviors remain **UNEXECUTED**, not validated
by CPU tests. A compile or a static batch condition is not full supports_op.

Concrete approval object: **S1_F0.json**, SHA256
`8935c7cb5369ec052d074f060d9519ac51311620830819b74be5e3c49d3a0fb7`.
16 fixed operands, one charged support-only census plus at most160 graph hosts;
161 attempts/3600 cumulative owned seconds/2GiB, zero model requests and no
extra probe/warmup/retry. Operator GPU memory monitoring is explicitly
checkpoint-based; the100ms supervisor samples owned RSS/host RAM/disk/wall,
with a prospective1000ms maximum actual gap. No continuous-residency claim.
First choose QH_C from the full census, otherwise QH_D, otherwise STOP. Actual
placement, Vulkan numerical correspondence, natural decoder endpoints and useful
cost remain unknown. All161 S1 slots, all64 S2 requests and S3 are unstarted.

No GPU command was run under S0. HOST_PROMPT.md explicitly says
"准备并申请 S1，不自行启动". Await author confirmation of this exact F0;
S2/S3 each still need their own gates and approvals. No new automation, merge,
old-study restart, RTX/paper/release change, hardware simulator, invented DRAM/
cache/XMX/timestamp/arithmetic-DAG/residency/PPA result or hardware-necessity claim.
