# Actual phase and retained-state recipes
All numerical model/GGML/Vulkan DLL bytes are inherited unchanged from pinned PR92. New code is a diagnostic frontend, linked to the same private phase-binding ABI. Sampler remains the same owned native greedy sampler; template and exact target-native prompt IDs are inherited once. Logical batch512 / context1024 / threads10 / F16 KV / FAoff / k1 / cap128 are fixed.

| Actual calling phase | O128 / R_stock | O512 / R_prod | B128 (whole recipe) | B512 / M_match | C512 / C_k1 |
|---|---|---|---|---|---|
| Context initialization | prefill UB128, capacity1 | prefill UB512, capacity1 | prefill UB128, capacity4 | prefill UB512, capacity4 | target prefill UB512/capacity4; draft UB1/capacity1 |
| Workspace preflight | no phase transition | no phase transition | same target bind1 then bind128 | same target bind1 then bind512 | same target bind1 then bind512 |
| Request reset | target synchronize, clear complete KV, greedy reset, bind original UB | same | same | same | same target plus independently owned draft synchronize/KV/sampler reset |
| Prefill | actual tokens split into successful occupied micrographs at UB128 | UB512 | UB128 | UB512 | target UB512; draft UB1 |
| After prefill | no new bind | no new bind | same context bind1 | same context bind1 | same target context bind1 |
| First output | sample actual last prefill row, commit native ID; not decoded yet | same | same | same | same target sample |
| Continuation | caller1 / actual occupied width1, UB flag128 | caller1 / occupied width1, UB flag512 | caller1 / occupied width1, UB1 | caller1 / occupied width1, UB1 | caller2 seed+proposal / two occupied width1 target graphs; draft catchup1 plus proposal1 |
| Output reservation | 1 | 1 | 4 | 4 | target4/draft1 |
| KV/pending position | prefix IDs committed in frontend, last output pending until next decode; native logical KV checked | same | same | same | target verify may transiently contain uncommitted proposal; trim to naturally accepted prefix; draft trimmed/caught up |
| Binding semantics | reset helper synchronizes even at same UB | same | reset/postprefill helpers synchronize; changed UB sets sched_need_reserve and sched_reserve | same | same target plus draft reset helper |
| End/reset ownership | all caller queues, contexts and samplers owned by same native PID; final direct synchronize included | same | same | same | two owned contexts, no model or sampler crossing |
| Placement | actual native weight map and stderr Vulkan0 KV checked before admission; checkpoint budgets not continuous residency | same | same | same | same for both models |

The inherited binding implementation first calls synchronize(). If UB changes, it sets n_ubatch and re-reserves the scheduler. It does not clone contexts, restore sampler history or prove continuous residency. Same UB binding-noop shams check native full-context and sequence-KV byte equality within one actual context; they do not validate donor-state forks.

Physical graph counters increment only after successful process_ubatch/graph computation. They bind actual occupied query rows and graph counts, not GPU kernel completion time. P2 records each real decode's graph deltas; one owned worker additionally attempts SDK Vulkan API dispatch metadata. API calls/graph-node names cannot certify per-stage GPU wall.

Diagnostic boundaries capture native top1/top2 values, full FP32 logits hash, exact natural output prefix, consumed input row/positions, complete serialized-context hash and sequence-KV serialization hash. Hashes are measured in process; large state payloads are not saved, so offline analysis does not redo byte comparisons from vector payloads. Serialization includes source-defined fields; it is not a complete frontend/sampler/scheduler fork.

Factorial: PHASE_FACTOR_NOT_ISOLATABLE. The target-only continuation C factor clamps to one occupied row on every path; reservation/binding differs across existing recipes. Four explicitly named whole recipes are used. Causal prefill-only and donor-state claims remain UNRESOLVED. Separate comparisons of full suffix reproducibility will be reported without upgrading this gate.
