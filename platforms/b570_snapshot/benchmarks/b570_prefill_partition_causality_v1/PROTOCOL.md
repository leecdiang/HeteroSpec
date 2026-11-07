# B570 Prefill Partition Causality — prospective diagnostic protocol
Parent: PR97 head 5a66653bd0ce413d4eb9aef3a4501b93c138071b. Inherits audited PR92/93 evidence without rerunning formal prices, modifying old qualification or merging old PRs.

A: UB512, one full-prompt llama_decode caller; capacity1.
B: UB512, caller chunks128 + remainder; capacity1.
C: UB128, one full-prompt caller (native internally partitions); capacity1.
All: target-only Q6_K, identical native prompt IDs within task, context1024/logicalbatch512/threads10/F16 KV/FAoff/native greedy/cap128; continuation caller1 under original context UB. No new phase binding, runtime transition, speculative path or forced suffix. Context reset remains inherited same-UB bind/sync for every arm.

Critically, all prefill rows request logits=false except the final position of the complete prompt. B's intermediate submission requests ZERO outputs. KV positions are original contiguous absolute positions; pending-token commit/consume rules unchanged. Record every actual successful decode graph/row/width delta and final-only logits-request position; no kernel geometry or exclusive GPU timing inferred from caller flags.

Exposed set: historical divergent GSM1248(161 IDs), GSM831(133); historical stable >128 controls GSM1011(190), GSM1249(163), ascending ID among admitted old stable >128 tasks. Fixed prefix inputs of the SAME GSM1248 native IDs, lengths127,128,129, prospectively fixed; these are truncated synthetic prompts, not task accuracy examples. No replacement after no-trigger results.

63 whole requests =7 inputs ×3 arms ×3 independent fresh-native-worker repeats, rotated arm/task order. Repeat0 counts capture-off; repeats1/2 heavy capture-on. Exactly1 zero-forward A load probe, no warmups/retries/forks. Totalchargedunits64, native owned-process time3600s, ≥512MiB same-PID measured dedicated headroom. Preserve failed starts, stop affected scopes; never replay a charged coordinate. No API-dump/ETW trial (unneeded for this intervention and prior observer failure retained by parent).

Before first new model forward: exact models/numerical DLLs/native frontend verified; source/inputs/plan/budget/readout F0A archived, GitHub-published and actual body bytes authenticated. Whole source capsule includes native actor, controller, static assets/DLL/import libs/include files; GGUF weights are hash-bound external inputs. Correct every preparatory build/source issue BEFORE frozen forward, retain failures.

Primary comparisons per input, no pooling over exposed trajectories:
- A/B fixed-context causal intervention: full outputs, stop/EOG/cap and first differing index.
- C reference reproduction against immutable PR92 R_stock; A against R_prod; all10 old repeats must agree.
- Positive sufficient explanation on an affected case requires A!=B, B=C COMPLETE trajectories, B/C exact prefill FP32 logits and serialized sequence KV equality, repeat stability and observer guard.
- B=A but C differs: external partition insufficient; report negative.
- All other patterns are partial/unresolved and published, including no-trigger controls.
At natural output indices0,preceding first difference,and known first difference (controls0/1/47), save full FP32 logits vectors; save full source-defined sequence-KV serialization at output0; hash complete serialized memory at later cuts. Independent audit rehashes payloads and reconstructs exact top2 and KV positions/F16 tensor shapes from source-defined format. Full serialized KV is NOT full frontend/sampler/scheduler state; no donor restoration claim.

Submission boundaries necessarily include per-call scheduler/queue handling. Even with physical width agreement, this tests external Prefill partition recipe; it does NOT isolate physical kernel geometry from every internal scheduling effect. Heavy mode adds readback/sync per call; capture-off full-output guard mandatory. Exact equality and raw differences precede causal wording; no state-to-token mediation/necessity claim without a validated cross-state intervention.

All new elapsed diagnostic only; physical counters are native successful graph rows, not costs or vkCmdDispatch counts. Original R_stock qualification failures and null qualified ratios retained. Existing actual paired request fees remain PR92-only. Continuous residency UNKNOWN; MODEL_TIMING_UNAVAILABLE.

Independent stdlib audit imports no controller or native executor, validates all63 coordinates/raw native FIFO/pins/lifecycles/memory/graph conservation/EOG/pending/captures/payloads/historical claims. Synthetic malformed evidence tests, complete content-address archive, fresh local and authenticated remote byte restore with independent exact rederivation. New Draft result PR adds ONLY benchmarks/b570_prefill_partition_causality_v1, based on PR97's branch; no paper/docs/main/older-PR changes or merges.
