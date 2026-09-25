# Targeted runtime literature check — 2026-09-25

Primary sources checked:
- TurboSpec v3: https://arxiv.org/abs/2406.14066v3 — execution profiling and feedback-based adjustment of intra-request speculation for serving goodput. Added to the manuscript as the direct control-system comparator; all 13 authors retained.
- Runtime-Controlled Evaluation of Speculative Decoding Methods: https://www.mdpi.com/2079-9292/15/14/3179 — existing citation retained; full direct retrieval failed, but indexed primary publisher text confirms complete drafting/verification cost and committed-work accounting. No new detailed claim relies on inaccessible full text.
- LLM-42 v2: https://arxiv.org/abs/2601.17768v2 — existing deterministic/verified-speculation positioning retained.
- DuoDecoding: https://arxiv.org/abs/2503.00784 — existing heterogeneous-placement positioning retained.
- AdaptiveSD: https://arxiv.org/abs/2607.03876 — freshness search surfaced additional runtime-adaptive work; full HTML unavailable. No detailed comparison or citation expansion inferred from the title alone.

Search scope was runtime cost/adaptive speculation and fallback, not a systematic literature review. Existing 13 bibliography entries remain byte-identical; TurboSpec is an appended entry. No firstness claim is made for qualification, cost accounting, state reuse, adaptive speculation, or heterogeneous execution. The paper does not compare its one-request M4 guard experimentally against TurboSpec or any serving controller.
