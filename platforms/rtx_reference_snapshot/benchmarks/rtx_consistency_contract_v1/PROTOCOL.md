# HeteroSpec continuation-state study v1

This study extends the current manuscript's RTX intervention, not a new generic speculative-decoding survey. Main e87291d and draft plan #57 are the evidence basis. #58 supplies an engineering motivation: global serialization can preserve some outputs but loses speed, and ordinary batched implementations do not preserve all deployment references. References from these different configurations are not interchangeable.

The next causal question is whether the native N0/N1 difference comes from the current target verification call, the state entering that call, or both. A positive diagnosis is useful for acceleration only if it subsequently permits a smaller consistency constraint while retaining efficient batching. No performance or new-method claim follows from these forks alone. The fixed-reference selector NO-GO in #56 remains valid.

## Frozen diagnostic contract

Reuse the original RTX target-continuation intervention: Qwen3-8B/0.6B Q8_0, b10839 pinned source, unchanged released CUDA backend, FA off, ctx4096, target/draft prefill UB2, draft UB2, k2, threads24, greedy seed123, original prompt and inclusive EOG/cap128 contract. N0 target continuation is UB2; N1 is UB1 after the original first-pending handoff. Do not replace this with #58's FA-on/UB512 service contract.

Tasks /15,/25,/18,/31 are exposed diagnostic cases. Historical native traces contain naturally aligned calls at generated counts13,4,4,4 respectively. These counts are fixed before new execution. /15 and /25 use the last historically aligned round start preceding known output divergence; controls use the last aligned count no greater than4. If the new native trajectory does not naturally reach that exact count/input contract, report UNSUPPORTED, without trimming or teacher forcing.

Immediately before target verification, after the previous native suffix cleanup and after the next proposal inputs are available, record the full committed generated prefix, actual pending ID, complete logical retained prefix, positions/sequence IDs/logits mask, cache position bounds, full serialized context state, current unused pending-logit bytes, and post-accept sampler clone contract. Logits left from a previous rejected suffix are not assumed to be pending-token probabilities and are not consumed by this verification call. Serialized state is not pure KV.

## Qualification and bounded execution

Engineering cap12 complete trajectories: /15 and /25 in each N0/N1 condition, each with the old qualified frontend, the new capture frontend, and the new frontend with a same-context state restore sham. Require complete IDs/endpoints equal across each triplet, source bytes and existing logits unchanged after capture, state/position roundtrip equality, and sampler clone chain/seed/history equality. Any failure stops dependent causal interpretation.

Pre-formal source audit correction: `llama_context::state_write_data` writes architecture and memory, not logits. Fresh destination contexts cannot be required to expose the previous logits before their first decode. The saved old logits are unused diagnostic witnesses and remain unchanged in the source; forks start with the carried pending ID and exact cache, then compute their own logits. This correction changes only the previously unexecuted fork branch. The 12 capture/sham trajectories ran under ba789982; retain their frontend separately, and bind the corrected frontend to its new commit and all formal trajectories. No failed model execution motivated this correction.

Formal cap24 complete donor trajectories: four tasks x two conditions x three fresh-process repetitions. At the frozen boundary, each actual donor is forked into target contexts UB2 and UB1, sequentially sharing the same resident target model and unchanged CUDA DLLs. Each fork restores the donor's exact state, clones its actual native common sampler, and runs the exact captured verification tokens/positions/masks. This gives at most48 fork units. The source context and sampler remain unchanged and continue their full original native trajectory after both forks. Same-path fork decisions must equal the naturally reached native decisions. Fork work is additional paid diagnostic work, not speed evidence.

Each fork records all raw verification logits and actual greedy acceptance/correction/bonus IDs; rows after first rejection are marked unreachable. It then removes inconsistent suffix state and continues scalar UB1 for at most32 additional IDs, stopping at EOG/cap. This short target-only continuation is auxiliary, not a full native speculative reproduction. The UB1 continuation context is initialized from the post-verification fork state with a sampler clone; its own exact roundtrip must pass.

Cross-donor comparisons require identical full committed/logical prefixes, pending ID, positions, sampler chain/seed/history and verification inputs. Native donors must reproduce their complete original arrays or explicitly report drift; no outcome-based exclusions. Full serialized state hash differences alone cannot establish KV differences. Context capacity is not actual graph occupancy; retain graph metadata.

## Decision after this study

Current-call effect alone motivates testing a local numerical/verification constraint. Donor-state effect requires preserving or repairing earlier state construction. Both require both constraints. No decision difference at this checkpoint does not establish absence throughout the trajectory. If the result only repeats known shape/cache sensitivity, retain it as evidence and do not claim novelty. Progress to an optimization only with a concrete non-task-specific recipe, original fixed-reference qualification and measured total cost including checks, state movement and fallback. Do not use recorded proposals, known divergence positions, or reference answers as free online inputs.

The unrelated controlled scalar/teacher-forced probe prepared earlier is NOT_EXECUTED and is not a native-state donor for this study. Manuscript files and historical assets remain unchanged; this is a private HeteroSpec research frontend, with no upstream submission.
