# B570 real speculative q2 request: integration and exact-reference bridge

Parent: PR132 `7e98e288b4137c998604a0809c7e956474967de1`. Private runtime candidate; no upstream repository modified.

**Real speculative q2 verification is integrated and qualified for this exposed 16-token request.** Target Qwen3-8B Q8_0 and draft Qwen3-0.6B Q8_0 actually generated proposals, performed target verification, accepted/corrected outputs and trimmed both KV states. This is not replaying synthetic graph inputs or substituting an actor.

## Integration and reference

PR132 fixes the Vulkan AV kernel dispatch but does not modify the model graph builder. This study rebuilds `llama-graph.cpp` with the existing graph helper, links184 other frozen llama objects and uses the exact PR132 Vulkan DLL. For the registered target GQA32/8, d128, q2/q4, key256/512 domain, PQ builds serial query attention and QB lifts the query batch. No FlashAttention, soft-cap, bias, sinks, MLA or KV-repeat substitution is introduced.

Layout is fixed before each fresh context is created. Contexts are used sequentially; no graph is reused across an arm switch. This environment-variable control is a private single-threaded study interface, not a production context-safe API. Draft's q1 computation and all target q1 calls retain the original graph. Physical graph reservation outside the scoped domain does not count as observed q2 execution.

The request state loop is a direct bounded implementation of the existing native protocol: committed seed, one natural draft proposal, target verification of seed+proposal, greedy prefix acceptance, correction or bonus, then trim both contexts to base+1+accepted. Sampling is deterministic ascending-ID argmax. Both vocabularies' token text and EOG classification are checked before speculative execution. Existing model files are pinned in MODEL_IDENTITY.json.

The same exposed HumanEval/42 input has124 prompt IDs. Prefill is submitted token by token with last-prompt logits only; target verification uses actual batch2 in an ubatch4 context. This is an explicit scope choice, not a claim to reproduce the historical512-token prefill policy or128-token qualification.

Reference checks, in order:

1. Fresh target-only q1 reference reproduces all16 previous PR129 complete logits vectors and native IDs/EOG values exactly.
2. PQ and QB each reproduce the complete16-token native endpoint: IDs, EOG flags, length, terminal ID and CAP stop.
3. Every PQ/QB saved full logits vector matches:21 target vectors (initial plus20 verification rows) and10 draft proposal vectors, **31 pairs** total, including verification rows later discarded by rejection.
4. The complete10-cycle state traces agree, including proposals, decisions, accepted counts, positions and post-trim KV maxima.

## Observed geometry and work

All36 target layers produce QB QK tensors `[256,1,32,2]` with original K `[128,256,8,1]`. This establishes actual q2, physical key256, Hq/Hkv32/8 on B570; configuration capacity1024 is not physical key1024. PQ uses two single-query chains. Callback metadata is collected only during target verification and never requests extra per-node evaluation or readback.

Each speculative arm performs10 verification cycles,6 accepted proposals and4 rejections, ending at16 tokens/CAP. A final cap can prevent committing a bonus; the uncommitted output row is still preserved for exact comparison. EOG stopping, other k values, new prompts, longer output windows and arbitrary GQA are not qualified by this request.

## Timing boundary and preserved budget

This qualification process saves raw logits and metadata. Its request durations are **diagnostic**, not clean costs and not an algorithm speedup measurement.

The initial planned clean pair was skipped because the predeclared internal time-reserve gate triggered after qualification. Status `BRIDGE_QUALIFIED_NO_TIMING` is successful qualification with no clean cost result, not a timing failure.

- PID15736, exit0, complete capture, normal cleanup, no watchdog kill.
- New entire-parent charge36.4329496s.
- Preserved prior249.2473593s gives285.6803089/300s; old remaining14.3196911s.
- Outer deadline38s; internal35s checks are cooperative between operations, not a hard asynchronous deadline.

The author subsequently explicitly requested continuation beyond the old balance barrier. The separately preregistered cost study in `b570_spec_request_cost_v1` uses new accounting and preserves this historical ledger unchanged.

## Evidence and verification

CPU reconstruction reread all16 q1 and31 PQ/QB full-logit comparisons, endpoint and state equality, and observed geometry for36 layers. All219 frozen inputs bind the private runtime, models, historical reference and executable. CPU preparation failures (text encoding and a missing nested object during link) were repaired before GPU execution and their logs retained.

Full78 raw logits files remain at the original local root and in a local full-raw archive. The GitHub compact archive carries every produced JSON record, geometry, trace and raw-file SHA256/size manifest; it does not claim full raw logits are hosted in GitHub or externally certified. No actor, RTL, CPU8 expansion or merge occurred.
