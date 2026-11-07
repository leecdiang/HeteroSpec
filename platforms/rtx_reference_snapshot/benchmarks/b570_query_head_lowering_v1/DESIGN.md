# Design: preserve logical queries, choose an implementable representation

## 1. Candidate, not a renamed invariant theorem

PR111 established a version-specific necessary condition: its Vulkan MUL_MAT requires matching fourth extents. Original QB uses K/V fourth extent1 and query/probability extentq. The source rejects q2; actual fallback/dispatch/cost remains unobserved. MQ/PQ passing this one test is not a full-support certificate.

The new candidate keeps that axis singleton. Let H be query heads, Hkv KV heads, g=H/Hkv, and j in [0,q). Define r=hq+j. Then:

`Q'[d,0,r,0] = Q[d,j,h,0]`, with `Q'.shape=[d,1,Hq,1]`.

The native contiguous-group head broadcast maps r to:

`floor(r/(q*g)) = floor(h/g)`.

Thus each logical query still receives its original KV head. Neither model heads nor weights are changed. K/V remain the same objects `[d,n,Hkv,1]` and `[n,dv,Hkv,1]`, sharing over expanded computational heads. This algebra does not prove any specific backend implements the needed broadcast correctly or preserves its floating-point path.

## 2. Q packing, mask and output are part of the method

A compact Q with d-fast, then j, then h storage can be reshaped. A model-style permuted Q generally cannot: `ggml_cont` explicitly creates that order and its cost is included. No fabricated strides or zero-copy claim for a noncontiguous input. Base offsets and owner-buffer bounds must be checked by the real harness.

Two mask realizations are predeclared, not improvised after output inspection:

- **QH_C**: view `[n,1,q,1]`, using mask-head modulo so column `r mod q` is original query j. It relies on actual support for this head-broadcast behavior.
- **QH_D**: repeat that view to `[n,1,Hq,1]`, materializing the exact mask for every computational head. Charge the REPEAT, storage and transfer. Do not use materialized mask without counting it.

Each row must retain its original allowed keys and positions. All-masked rows outside the inherited contract are rejected, not assigned invented zeros. ALiBi/head-dependent bias, sinks, softcap, FlashAttention, MLA, multiple sequences and non-contiguous K/V outside the inherited admission are excluded. In particular, computational-head renumbering could change a head-dependent positional bias; this prototype does not claim support for it.

AV is `[dv,1,Hq,1]`. Restore `[dv,q,H,1]`, permute to `[dv,H,q,1]`, then make the ordinary output `[dv*H,q]`. This step must be tested, not inferred from equal element counts. QK retains the old explicit F32 precision flag; AV retains the inherited setting. No shader, dtype, mask value or sampling change.

## 3. Explicit controls

| Label | Purpose |
|---|---|
| MQ | Mathematical/native reference graph; not necessarily same finite precision as PQ |
| PQ | Strong local baseline, with shared KV, legal graph reuse and ordinary output recovery |
| QB4 | Original fourth-axis view. CPU/source control only where Vulkan admission rejects it; never time unsupported work as qualified GPU execution |
| QH_C | Primary compact-mask candidate |
| QH_D | Predeclared dense-mask fallback/ablation |
| REPEAT4 | Original QB with actual K/V fourth-axis repetition; transparent materialization baseline, not the only baseline |

For q1 all labels must execute the same original attention chain. A nullptr/delegation return is not an executed result. The real harness must reconstruct original QK/softmax/AV and output.

At S1, `choose_from_capabilities` examines the complete pre-output census. Choose QH_C if fully supported for all predeclared descriptors; else QH_D if fully supported; else stop. Support checks cannot read timings, tokens, numerical mismatches or labels. The selected choice and all raw support events are frozen before the first numerical graph. Both mask variants may still appear in the predeclared operator table; unsupported ones are marked SKIPPED, not replaced.

That selector is not a numerical acceptance oracle: S1 and then full requests still test it. No per-task winner selection or mid-request fallback is permitted.

## 4. Why this is not automatically novel

MLIR's Dialect Conversion already models target legality and operation rewriting. FlashAttention's pack-GQA implementation folds query-head grouping into sequence work; shape/head packing is not new as a concept. Thinking Machines' batch-invariant kernels already constrain reductions/split boundaries. These are strong conceptual neighbors.

The intended question is narrower and testable: **Can an alternative local lowering preserve a given quantized deployment reference while crossing an observed backend-capability boundary, without the structural cost of explicit PQ or replicated KV?** The output must include actual qualification, added rearrangement/storage, full cost, and new-condition results. A dimension fix or condition checker alone is validation infrastructure/porting, not a new inference algorithm.

Primary sources checked for positioning (not exhaustive priority or external performance reproduction):

- https://mlir.llvm.org/docs/DialectConversion/ — legal/dynamic/illegal conversion targets.
- https://github.com/Dao-AILab/flash-attention/blob/main/hopper/pack_gqa.h and `flash_attn/cute/pack_gqa.py` — related head/query organization, not a same-contract performance baseline.
- https://thinkingmachines.ai/blog/defeating-nondeterminism-in-llm-inference/ — batch-invariant numerical execution.
- Fixed project sources and exact SHAs are in SOURCE_LOCK.json.

## 5. Structural costs, not made-up bandwidth

For one transformed operation, compact-mask QH may allocate Q packing `4*d*H*q` bytes if required; QH_D additionally allocates `4*n*Hq` mask bytes. REPEAT4 writes full repeated K/V destinations `2*n*Hkv*(d+dv)*q`, not merely `(q-1)` copies if repeat materializes a new q-wide tensor. The allocator can also retain original tensors.

These are logical destination sizes. They are not measured DRAM bytes, cache misses, or peak memory. Output recovery, graph metadata, workspace and actual liveness must be measured in the real implementation. PQ may already share K/V effectively: no baseline that deliberately reloads it from external memory for every query. No speed claim from graph count, and no assumption that head folding keeps an identical selected matvec or reduction tree.

## 6. State and architecture interface

Natural phases reuse the same declared producer recipes as the independent pilot: original R stays original, while candidate reference128/bulk512 prefill uses MQ. Target and draft have separate schedules. All requests start from prompts; no donor files or future suffix. q1 continuation equivalence does not qualify q2 verification; same endpoints do not prove same internal operands or acceptance trace.

Export only actual: logical q, Q/K/V/mask shape/stride and source hashes, operator support observations, selected backend handles for executable nodes, copies/graph events if observed, paid timer and committed-token work. Request-level histograms do not become ordered traces. DRAM/cache/XMX/kernel-completion/DAG/continuous residency remain null unless separately measured.

This supplies competing software mappings and realistic constraints to PR110/hardware research. It does not implement another simulator or RTL core. A new-architecture arithmetic reference is distinct from the old RTX/Vulkan reference. Software-first is a valid exit; hardware necessity cannot be inferred from rejection by one software version.
