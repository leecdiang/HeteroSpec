# X — conditional placement POC, not an asynchronous multi-GPU system

## Start with real Linux costs, not an assumed second-GPU speedup

This lane is lowest priority and conditional. Run cost_gate.py on the qualified
Linux same-GPU study's actual disjoint costs. Missing phases remain null. Historical
PR195's roughly20.5% draft share and6.15% perfect-prefill-overlap opportunity are
context only; they are not A5000/Linux forecasts. Moving the drafter does not break
proposal -> target verification -> commit/rollback -> synchronization dependencies.

Do not start a two-card model run until the coordinator has allocated an explicit
pair, checked topology/current occupancy and identified a concrete memory/latency
question. CPU-only planning and token-protocol unit work can proceed independently.
No automatic follow-on if current costs already close the economic question.

## Minimal explicit implementation

Retain Qwen8B/0.6B Q8, original target GPU/R/method, C1024/F16KV/k3/noFA, ordinary
greedy output. Split actual target and draft model/context device parameters, not
just CUDA_VISIBLE_DEVICES. Target stays intact on its original GPU; the second
GPU is not tensor parallel. Each model owns its own resident KV.

For greedy independent models, exchange actual proposal/commit/correction/bonus/
trim token messages; do not transfer whole target or draft KV. Record transport
and required synchronization. That protocol is NOT a general stochastic SD or
feature-coupled drafter protocol. No cross-round overlap, learned predictor, new
cache, optimistic speculation or prefill overlap in the initial comparison.

Reuse the current single-GPU supervisor in a separate versioned two-UUID adapter;
retain both allocations/locks, inherited masks, foreign-process detection and
own-process cleanup. Do not disable protection in PR196. CPU draft additionally
needs explicitly assigned cores/NUMA and actual CPU/KQV placement; it is not an
invitation to occupy every server CPU thread. Lack of CPU allocation is a recorded
unavailable branch, not a reason to modify a frozen test panel mid-run.

## Finite qualification and pilot

Two complementary probes:
- Fixed proposal replay isolates target/transport and state bookkeeping. It is not
  free real drafting and cannot supply an end-to-end speed result.
- Live draft checks complete target vectors/state/transactions against the same
  target reference. Proposal/acceptance may change; report actual target rows and
  draft work, never attribute all differences to communication.

Cover first/later rejection, all-accept, trim, correct frontier, pending correction/
bonus, EOG/cap, reset and physical boundary. The independent CPU toy protocol in
old materials is not native GPU evidence. Use real inputs/captures after integration.

Fixed exposed pilot: four roots, three sessions, M_MATCHED/SAME_GPU/CPU_DRAFT/
SECOND_GPU =48 complete service observations +24 primers, after qualification.
If a branch is administratively unavailable, register a new reduced pilot before
outcomes, retaining the original plan as unstarted. Pilot comparisons are descriptive.
Charge model/context setup, transport and state work; no silent subtraction.

## Additional resource changes the comparator

A dedicated two-GPU result must report latency AND allocated-GPU-seconds, CPU
core-seconds, actual memory and measured power only when available. GPU-seconds
are not joules. Compare the practical two-card alternative of two independent
same-GPU workers (or two M workers) under the same request arrival/workload before
claiming throughput/resource efficiency. Same-GPU vs two-GPU latency alone is not
a fair equal-resource throughput result. Reversing target/draft card roles requires
another explicit target reference and a separately reported block.

Only a real surviving cost/capability opportunity can motivate a later formal
panel. It must retain all four strongest legal target-only combinations and both
same-GPU SIMPLE/LOCAL D4 controls; do not promote this four-arm pilot to a full
superiority claim. Any prefill-only overlap is a new prospective condition with
thread-safety/synchronization evidence, not an in-place optimization of this panel.
Initial envelope512 requests/4M rows. No automatic full asynchronous pipeline,
rental, paper edit or merge. A bounded no-benefit finding is adequate closure.
