# Recovery content review

Date: 11 November 2026. This is an independent assistant reading of the recovered author-review draft, not an external journal review or an editorial recommendation. The author authorized this manuscript reconstruction and review. No manuscript source was changed by this reviewer, and no model or GPU experiment was run.

## Scope and method

The reviewer read the complete abstract, seven main sections, preamble, manuscript root, standalone supplement and bibliography in `source/`. The review used the recovered, pinned scientific-critical-thinking 1.5, peer-review 2.4, scientific-writing 2.3 and Humanizer 4.0.0 skill texts. It checked scientific interpretation and terminology, and independently calculated selected numerical claims from the supplied data. The existing review reports were contextual records, not substitutes for reading the manuscript or checking its arithmetic.

The principal question is consistent across the draft: how to organize known-query work in parallel while preserving an established quantized deployment's target vectors and active state. The manuscript distinguishes physical-extent groups, native arithmetic groups, cut placement and logical state ownership. It evaluates numerical qualification before component effects and complete application costs.

## Assessment

No scientific inconsistency blocking delivery for author review was found in the recovered text. One small terminology edit is recommended below. This finding does not certify all-input equivalence, independently reproduce GPU measurements, or predict journal acceptance.

### Mechanism and construction

- The CUDA extent experiment correctly holds consumer query width at one and exchanges the physical probability/value range. It does not relabel this as an experimentally profiled q4 attention reduction change. The two directions of crop/pad replay and the distinct vector/token divergence indices, 29 and 81, agree with the pinned primary report.
- The CUDA Q8 account correctly distinguishes four versus two MMVQ reduction warps from the Vulkan F32-versus-Q8_1 activation-path change. The same CUDA row quantizer at q4/q8 is not treated as proof that all hidden quantizer bytes were independently captured.
- The Vulkan `p021` specialization is assigned to QK, with AV range/stride/dispatch requirements described separately. This matches the primary report's observed 4,519/8,192 QK-element differences and subsequent repair.
- The producer experiment is stated as a joint change of serialized KV and the initial full vector. Its two-input consumer-endpoint result is not promoted to a KV-only causal intervention or a full numerical-equivalence result.
- The reference's producer semantics are distinguished from a candidate's physical prefill grouping. The runtime plans from phase/operator/cache descriptors before execution, avoiding a circular definition based on observing whether the candidate succeeded.
- The extent equation is restricted to the guarded dense, nonwrapping append profile. Its example produces extents [768,768,768,1024] for head 765 and [768,1024,1024,1024] for head 767 with padding 256. The run-length ceiling formula is correct for contiguous equal-key runs under the specified width bound.
- The composition paragraph states its per-group and state-ownership premises explicitly. Finite qualification results test the implemented premises; the paragraph does not claim a floating-point theorem for all inputs.

### Performance interpretation

- The 0.80%-1.64% Q8 packing increment uses the stronger backend-loop4 control. It remains separate from the 11.52%-25.54% complete speculative-application reductions.
- Local-cut effects are reported at fixed projection mode. The two packed-path intervals include one, and the text says so. The natural boundary rate explains available opportunities without converting a count into a latency estimate.
- Mixed-Q4 full-service results retain their graph-level scalar-loop comparator. The stronger backend-internal loop contributes completed operator evidence only at this draft's stated cutoff.
- The matched-history A5000 B2 experiment is identified as one exposed input with four process clusters per cell, including mixed process-level directions. It is not substituted for a live-request improvement.
- The equal-work q8/q4-pair comparison and live k7/k3 comparison use distinct workloads and estimands. Their opposing directions are explained through additional target rows and draft proposals.
- Negative results remain visible: 32B speculative requests and the B570 resident pilot favor ordinary generation; short Llama worker workloads do not preserve the resident-time ranking; historical wide crossing cells can favor Whole.

## Independent calculations

These calculations read the supplied numeric files directly and did not invoke the manuscript's figure, table or validation scripts. Application and factorial calculations used the recorded totals; they did not reconstruct the unavailable underlying captures or newly estimate inherited intervals.

| Quantity | Independently calculated result | Manuscript rounding |
|---|---:|---:|
| Qwen3-8B application reduction versus fastest fixed M | 17.2078047944% | 17.21% |
| Qwen3-14B application reduction versus fastest fixed M | 25.5391955368% | 25.54% |
| Llama-8B application reduction versus fastest fixed M | 11.5220800047% | 11.52% |
| 8B packing, Whole / Local | 1.6352477316% / 1.5560110274% | 1.64% / 1.56% |
| 14B packing, Whole / Local | 0.9870309215% / 0.7959007142% | 0.99% / 0.80% |
| 8B local cuts, loop4 / packed | 0.2087320385% / 0.1283462194% | 0.21% / 0.13% |
| 14B local cuts, loop4 / packed | 0.3043071244% / 0.1118590176% | 0.30% / 0.11% |
| Natural affected-cycle frequency, 20/2,224 | 0.8992805755% | 0.899% |
| 14B native-worker reduction | 10.2614510195% | 10.26% |
| Accepted / inspected proposals, k3 / k7 | 87.4669020300% / 87.9323597233% | 87.47% / 87.93% |
| Accepted / all proposed, k3 / k7 | 75.4185692542% / 56.9437531110% | 75.42% / 56.94% |
| Increase in verification rows, 18,368/14,016 - 1 | 31.0502283105% | 31.05% |
| Strong-loop operator C/B equal-cell geometric ratio | 0.8528258434 | 0.8528 |
| Strong-loop operator B/G equal-cell geometric ratio | 0.6390412656 | 0.6390 |

The B2 check independently consumed all 128 operation observations, accounting for 64 warm and 64 measured operations. For each of 16 workers it divided the sum of two measured q8 times by the sum of two measured q4-pair times, then formed the four process-cluster geometric means. The results were:

| Projection / prefix | Recalculated geometric ratio | Processes above one |
|---|---:|---:|
| loop4 / 248 | 0.9904445372731789 | 2 of 4 |
| loop4 / 252 | 0.9780650783484270 | 1 of 4 |
| packed / 248 | 0.9369889121771803 | 1 of 4 |
| packed / 252 | 0.9475656348625566 | 0 of 4 |

All 16 recalculated process ratios match the recorded values within 1e-14. All checked manuscript rounded values agree.

## Small terminology revision

The first use of KV, Q/K/V, QK, AV and RoPE could be expanded for TPDS readers. There is no existing explicit expansion to duplicate. The following edits leave the scientific meaning unchanged:

1. In `abstract.tex`, expand the first physical KV range to “physical key-value (KV) range.” The abstract has a separate definition from the main text.
2. In `sections/01_introduction.tex`, expand the first KV state to “key-value (KV) state.”
3. In `sections/02_reference.tex`, expand the first visible operand list to query (Q), key (K), value (V), and query-key (QK) products. Define the native AV operator as attention-value aggregation. Figure 1's caption precedes this definition and can also expand AV once.
4. In `sections/02_reference.tex`, expand the first RoPE use to “rotary position embedding (RoPE).”

MMVQ already has an explicit expansion and needs no additional definition. The root writer is responsible for applying any edits and rechecking the resulting pages.

## Primary mechanism sources opened in this pass

The following fixed repository files were fetched and read in full during this review:

- [CUDA physical-range intervention](https://github.com/leecdiang/HeteroSpec/blob/701079f265c0ff8fd05d43fbc2d8d5054a711e1b/platforms/rtx_reference_snapshot/benchmarks/rtx_llama_repair_v1/host_execution/RESULTS.md), blob `0a6623ee6f03f89ff86d60a293cce3c6b3ab68e7`.
- [CUDA operator-frontier results](https://github.com/leecdiang/HeteroSpec/blob/371223b696bb805030c29f04e39eb17b57fb2ebb/benchmarks/rtx_operator_frontier_v1/execution/RESULTS.md), blob `002b5847a69744887fc53d9a1f2144101f05c17b`.
- [Vulkan reference-compatible parallel execution](https://github.com/leecdiang/HeteroSpec/blob/8ca17478c292275b3515a91b51d0e791a8fae256/benchmarks/b570_parallel_v1/RESULTS.md).
- [Vulkan producer/consumer boundary](https://github.com/leecdiang/HeteroSpec/blob/701079f265c0ff8fd05d43fbc2d8d5054a711e1b/benchmarks/b570_producer_consumer_boundary_v1/RESULT.md).

This pass did not repeat the bibliography identity check, rerun native qualification, reconstruct application confidence intervals, or assess the latest remote experimental progress. Those checks belong to the existing evidence record and the parallel recovery work. The scientific assessment above concerns the recovered draft and its explicit evidence cutoff.

## Resolution of the clarity edit

The lead writer applied the first-use definitions of KV, Q/K/V, QK, AV and RoPE. The exact patch is in `RECOVERY_CLARITY_EDITS.diff`. The main paper recompiles to 10 pages without LaTeX warnings, and the five-page supplement remains byte-identical. Only main pages 1–2 change in the render; both received the final targeted visual check.
