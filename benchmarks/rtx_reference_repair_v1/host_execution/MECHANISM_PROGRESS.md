# Native mechanism evidence; candidate validation still in progress

PR158 head was verified as `798ba41c09ac503faa690f134e618df96bfa2063`.
The original PR156 model, worker, references and numerical DLLs remain unchanged.
All new epochs share `D:/rtx158/research/LEDGER.jsonl`; the old40 requests remain
separate. No held-out14B output has been generated at this checkpoint.

## Retained roles=0 development

Epoch01 built and admitted successfully and completed all96 requests. Every
heavy/off endpoint and transaction control agrees. Canonical UB1 prefill restores
both mathematical M-path endpoints and the GSM120 C-path endpoint, but causes
the GSM111 C paths to depart at16. Native-prefill M paths retain the old16/82
counterexamples, and native C paths retain the82 counterexample. Reverse PQ/QB
producer-to-R transfers reproduce the mathematical failures. This is a failed
development candidate, not an authorization to expose confirmation inputs.

## Same-state localization and native operator replay

Eight paired trace/no-trace requests compare the first common seed on GSM111,
with equal serialized boundary KV and initial token. R ordinary row0 and C
verification row0 refer to the same absolute position92; other speculative
rows are not mistaken for R rows. All complete vectors, endpoints, transactions
and final states match their observer controls. M_QB matches R at all40 layer
outputs. Both C layouts first differ at the captured `l_out-10` checkpoint;
this does not establish the globally earliest internal difference.

Eight narrower requests locate equal normalized K operands followed by different
RoPE outputs: R assigns K RoPE to CPU, C to CUDA0. Q/K head normalization scaling
uses an offload preference based on row count;8 heads ×4 tokens crosses the
pinned CUDA preference threshold while8 ×1 does not. GPU assignment propagates
to the following RoPE. The actual scheduler API establishes these assignments;
CUDA_Host buffer ownership is recorded separately and is not used as proof.

Epoch02 changes only diagnostic RoPE parameter/immutable-position recording.
Four observer-controlled requests capture real operands. Eight native operator
replays, conservatively charged to the development budget, reproduce both full
own-path CPU and CUDA outputs. CPU on the captured four-row operand gives the R
first-row result; CUDA on the identical one-row operand gives the C first-row
result. All repeats agree.851/1024 float elements differ, maximum absolute
difference `2.3126602172851562e-05`. This establishes the backend-dependent RoPE
discrepancy for these operands, not an arbitrary Q8 matmul cause.

## Candidate intervention and ablation

`repair_offload.hpp` queries the original offload predicate with one-token
geometry for scoped-target Q/K head-normalization scaling. It leaves actual
tensor data, shapes, arithmetic operations, R and inactive draft paths intact.
The rule is global by operator class, with no task, token, layer-number or
margin condition. It changes the static scheduler code, not the21 numerical
DLLs. Static-library hashes supplement the original build receipts. The supplied
rowwise Q8 matmul primitive stays disabled (`rowwise_roles=0`).

Epoch03 prospectively selects native prefill, without a per-request canonical
producer. It builds and passes capacity admission. The same eight first-seed
requests pass observer controls; all40 layer outputs and final logits now match
R in M_QB/C_PQ/C_QB, and complete natural endpoints match R. The complete96-cell
development matrix subsequently completed: all48 heavy/off pairs preserve R,
with no observer discrepancies. No held-out qualification or performance claim
follows yet.

## Remaining gates and resource accounting

After development, run144 original-Qwen8B regression requests and24 pinned
Llama regression requests. The latter retain the original known counterexample
and two controls, using the metadata4 source and fresh contexts. Their references
are read from pinned historical records, never from candidate output. The derived
host driver retains the existing lock, Job, timeout, memory and shared-budget
checks; only family binding and model-specific geometry/vocabulary validation differ.
The first Qwen8B admission failed before generation because the adapter incorrectly
bound32 layers. Authenticated model metadata reports36 layers and4096 embedding
dimensions. The adapter now binds36 for Qwen and32 for Llama, with explicit coverage
tests; the failed receipt and prior source remain. New regression epochs were
prepared. Qwen8B admission and all144 requests subsequently passed against the
original references, with72 stable observer pairs.

The first Llama run failed after15 completed records while the16th heavy request
was active. The new regression integration exposed a fresh-context capture lifetime
bug: diagnostic state serialization occurred after context destruction. Windows
recorded access violation `c0000005`; all24 reserved requests remain charged. A fresh
Llama build captures state into owned bytes before teardown and writes them afterward,
outside service timing. The natural decode/acceptance loop is byte-identical. The new
capacity admission and complete24-request regression pass. All24 endpoints/native
transactions and2356 saved full-vector artifacts match original historical behavior.
The known CodeContests108 C_PQ/C_QB counterexample remains four failures against R;
it is not relabeled as reference preservation.

The mechanism record and native freeze re-audit now pass. At freeze420 requests
are conservatively charged, including8 operator replays and the entire failed
Llama24 reservation. The planned720 confirmation/timing requests bring the projected
total to1140. Held-out qualification and performance are still pending.

Before epoch03 output, finite safety ceilings were raised to21600seconds per
worker and86400seconds cumulative to accommodate the frozen long prompts and
full continuation. Prior native seconds are retained. Request ceilings remain
1200 total and480 development/diagnosis/regression. At development03 START,
228 slots are charged:116 completed model requests,8 completed operator replays,
8 completed candidate ablation requests, and96 reserved development requests.
No budget is reclaimed on failure. Confirmation still requires a justified freeze,
24 original-binary references,120 candidate qualification requests, then complete
paired timing. Initial checkout/test failures and all candidate versions remain.
