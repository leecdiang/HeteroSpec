# Four-request supplied-history pilot — frozen design, GPU not started

Base: PR231 latest head301df2f2cb47a432c3d2afb84c69aaebb16ea3f0.
The user conditionally authorizes at most4 model requests,8192 physical input/
continuation rows and one model deployment, with no automatic retry. The old
76-request plan, STATE, references and ledgers are unchanged and not reused.

## One case, selected before new numerical observations

CASE_FROZEN.json binds the first already-frozen PR226 development episode, root
330fc1cf-53dd-4d67-8201-2782df947dd5, next user
b23c5984-720f-4e0c-907d-a0f33127c944. No offset, padding, speed or acceptance
search was performed. Its previously predicted whole-rechunk and LOCAL ordered
partitions are **identical**; this case tests lifecycle feasibility, not a
favorable LOCAL opportunity. A pass cannot establish that LOCAL is worth pursuing
on other inputs. A failure at the strict canonical bridge can stop this contract.

Source is OASST1 revision fdf72ae0827c1cda404aff25b6603abec9e3399b,
CC-BY-4.0, via the immutable PR224 saved tokenizer output SHA
23e812286a06ce6e067eb89648221b4348daeb1d3b5722aab780d09c56288350.
Existing token files are read only; no N0 census, tokenizer or vocabulary helper
is rerun. CASE_FROZEN binds exact full input IDs and source hashes.

The old logical stream has187 IDs:186 materialized, plus pending EOG151645.
Next canonical Q has216 IDs. The predicted retained prefix is88, leaving128
suffix rows. This is a prediction until actual native head/cell-map checks pass.
F is the first8 saved tokens from the next supplied assistant body on the same
preselected path, with no EOG. F is fixed **input continuation**, not generated
output or a change to the old natural response cap128. No manufactured EOS or
claim of free generation is permitted.

## Exact request/row accounting

One process, one original R numerical model object/deployment, two equally
configured independent C4096/F16 contexts (resident A and scratch B). Their
allocation/peak must be admitted before requests; no extra model load, warmup,
forward probe, recovery decode or hidden context initialization request.

| Order | Operation | Context | Physical rows |
| --- | --- | --- | ---: |
| 1 | Materialize the exact186 old IDs; register the supplied pending token without decoding it | A, initially empty |186 |
| 2 | Independently repeat the exact old materialization | B, initially empty |186 |
| 3 | Cold canonical Q: q1 prefix88, then suffix128; append fixed F8 | B, explicit reset |224 |
| 4 | Preserve actual A from request1; trim186→88, discard pending, append exact Q suffix128 and F8 | same A |136 |
| Total | No retry or fifth request | one model, two contexts |**732** |

Hard limits remain4/8192/1, not just the smaller nominal sum. Each request and
each actual decode row must be durably charged before entering the native API;
setup, partial failures and any unexpected decode count stop and remain charged.
No request may pack an extra canonical prompt/reset-rebuild into its budget.

R1/R2 must pass complete requested vectors and active-state comparison before R3.
R3 is an independent cold construction, never a restore of A's captured bytes.
Its captures must be complete and finite before R4. R4 is a resident reference
bridge, not a LOCAL/strong candidate. There is no candidate or performance panel.

## Strict captures and comparisons

Use the exact original R arithmetic, q1 order, output mask/reserve, model/template
identities and source-bound native writer. Capture every actually requested
vocabulary vector in full F32, not only argmax. Capture active F16 K/V over all
36 layers×8heads×128 dimensions, with cell/position/sequence maps, frontier,
logical/materialized IDs, pending, and caller-owned output stability.

Compare R1/R2 old state and outputs; compare A before/after trim against R1's
retained prefix bytes; compare trimmed A with R3's independently computed88-token
prefix; compare Q-complete vectors/KV and every fixed-continuation checkpoint
between R3/R4. A trimmed invalid frontier is not compared to the cold prefix's
fresh logits. After suffix decode, frontiers must align. Save first differing
coordinate/bits and stop; no tolerance change, hash-only equality, restored
oracle, argmax substitution or unexplained common reset. Trim failure is STOP
within this pilot, not an uncharged rebuild. Empty/reset checks consume no rows.

This profile repeats the **old initial state**, not the complete transition.
It therefore cannot claim full resident-reference repeatability or N1a pass.
If an independent repeat of the whole transition is required, the smallest
extension is a fifth request (another136 rows,868 total) and third context:
retain two independently built old states, run one cold oracle, then both
resident transitions. That extension is **not approved or runnable** here.
Independent-process/model-load repeatability cannot fit one deployment and is
outside either profile.

## Resource and admission state

Read-only audit:209 original bindings and all full source/dependency closures
match; the8,709,518,112-byte model has SHA408b9555…883d6. Old120 STATE/ledgers and
three lock identities match. GPU0 has another service; selected GPU1 was idle at
the recorded observation. An idle snapshot is not an exclusive window.

Existing user@ delegation already enables memory/pids. Actual newly named
systemd user services proved64MiB memory.max, swap.max0, pids.max8, same-group
parent/child startup, owned group cleanup and real kernel OOM termination.
No admin/ACL/controller-setting change was required. The first observer stopped
prematurely during deactivation; its STOP survives. The corrected bounded wait
requires terminal state, empty group and readable held pidfds. The second real
check passed. These are real kernel observations, not ordinary-file mocks.

This does **not** yet connect the PR231 native launcher to systemd admission.
Existing production denial is unchanged. A dedicated pilot entry must bind the
real unit/cgroup/lease and exact model/source/config to durable4/8192/1 counters;
it must require correct pre-exec membership before loading the model. Merely
using systemd-run around a denied ELF or submitting a PASS receipt is not such
an implementation. No native ELF has been run.

Proposed pilot limits:24GiB host domain memory, swap disabled,16 tasks, two C4096
contexts, ≥2GiB live VRAM reserve,10-minute native ceiling, and20-minute export
margin inside a specifically coordinated window. At most40 state snapshots at
head≤224 plus732 complete F32 vectors fit a2GiB raw-byte cap; metadata/logs have
64MiB each. Reserve32GiB disk for raw/archive/readback/build/failure retention,
without deleting anything. Placement/peak is not yet measured. Blocking IO or
GPU operations are not guaranteed interruptible by a host watchdog.

**Current No-Go:** exclusive start/end and shared-server coordination are not
confirmed (question pending); the bounded two-context native pilot entry is not
implemented/admitted. GPU requests/rows/deployments/contexts/forwards are all0.
No administrator change is currently indicated. Do not infer approval of5 or76
requests, run N1a/N2, reset devices, kill other tasks, merge or change the paper.
