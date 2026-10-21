# Paper-ready evidence addendum: B570 finite request panel

Use with PR130's reference-preserving QB method and backend/cost chapters. Do not replace existing RTX request benefits.

## Candidate English paragraph

We further evaluated the Vulkan port in a prospectively fixed four-input Qwen3 request panel, using a 64-token output cap and natural end-of-generation termination. A target-only q1 reference, serial-query attention (PQ), and query-to-batch attention (QB) produced identical complete native endpoints. PQ and QB additionally matched all saved full logits vectors byte for byte and agreed on the complete speculative state traces. The observed verification graphs used q=2 and physical key extents256/512 with32 query heads and8 KV heads. We then measured64 requests in four independent process sessions, with16 separately reported warmup requests and identical-implementation PQ controls. The equal-input geometric-mean QB/dual-PQ service ratio was 0.995144; the QB/target-only ratio was 2.619763. The registered practical-benefit screen returned NO_ESTABLISHED_PRACTICAL_PANEL_BENEFIT. These results establish reference-preserving migration for this finite panel, while keeping semantic admission distinct from measured request benefit.

Registered phase timing further shows a7.33% descriptive reduction in target-verification wall duration, from1.009s to0.935s on average. However, draft prefill and decode together require12.367s per QB request under the frozen serial-prefill policy. The local verification improvement therefore does not establish useful request acceleration, and the current draft execution policy fails to repay its cost. These phase measurements describe software execution intervals rather than physical GPU bottlenecks.

## Required accompanying limitations

Four previously exposed inputs, one model pair, one machine/date, k=1 and one bounded reference policy. Token-by-token prefill; shared loaded models; service window includes fresh context lifetime but excludes shared model loading. No population confidence interval, equivalence claim, serving-wide qualification or hardware mechanism attribution. Complete raw vectors remain at the original machine; compact metadata and hashes are in this repository.

## Figure/table data

Use TIMING_TABLE.csv for per-input/per-process paired ratios and ANALYSIS.json for full service/request/stage rows, including warmups. All16 paired blocks must remain visible. A/A controls and target-only economics should accompany the QB/PQ panel; do not publish a headline speedup alone.
