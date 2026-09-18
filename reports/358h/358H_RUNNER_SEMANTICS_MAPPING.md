# 358H heterogeneous runner semantics mapping

## Authority

- llama.cpp commit: `0cae43063cf15170e91a2ff4d034da0ecef4a1b2` (build 10839)
- Primary reference: `examples/speculative-simple/speculative-simple.cpp`
- Draft implementation reference: `common/speculative.cpp`, `COMMON_SPECULATIVE_TYPE_DRAFT_SIMPLE`
- This mapping precedes all heterogeneous-runner model generation.

## Frozen requirement to pinned implementation

| Frozen requirement | Pinned source behavior | Bridge rule |
|---|---|---|
| Greedy target sampling | Target sampler is created at `speculative-simple.cpp:113-115`; `common_sampler_sample_and_accept_n` consumes target logits in order at lines 251-258. | Select the maximum target logit deterministically at each checked position. |
| Autoregressive draft | `common_speculative_draft` receives `n_past`, `id_last`, and the committed target prompt at lines 187-196. `draft-simple` advances its own context in `common/speculative.cpp`. | OpenVINO produces up to two greedy tokens from the exact committed prompt and output history. |
| k=2 proposal cap | The implementation-specific `n_max` limits the draft; the outer loop additionally caps it by remaining context/output budget at lines 180-190. | Propose `min(2, remaining_output_tokens - 1)`; when only one output remains, decode target-only. |
| Serialized target verification | Target batch is `[id_last, draft0, draft1, ...]` with logits requested at every position at lines 221-233. | Obtain the target greedy token before d1, after d1, and after d2 in order. No approximate or probability-threshold verification. |
| Ordered prefix acceptance | Lines 251-258 continue through available logits only while target sampling agrees with the next draft token. | Stop at the first mismatch; later proposal tokens can never be accepted. |
| Correction token | The returned `ids` is asserted non-empty at line 262. On mismatch, its final element is the target-sampled token at the first disagreeing position. | Commit the accepted draft prefix followed by exactly one target correction token. |
| Bonus token | When every draft token agrees, sampling continues once beyond the draft because the target batch includes logits after the final draft token (lines 225-258). | If d1 and d2 both match, commit d1, d2, and the target greedy bonus token. |
| Target rollback | Before verification the implementation checkpoints target state (lines 198-203). Partial acceptance restores/removes speculative KV at lines 264-289; contexts supporting partial removal use sequence removal. | Remove rejected candidate positions from target KV, then decode the correction token; full acceptance keeps both candidate positions and decodes the bonus token. |
| Draft synchronization | Draft state is checkpointed/reset before verification at lines 176-213 and notified through `common_speculative_accept` at line 292. | Qualification runner uses the frozen, permitted replay strategy: every proposal reconstructs draft state from the exact committed prefix. No hidden persistent divergent state exists. |
| Committed history | Lines 294-308 count accepted draft tokens plus the final target token and append them in order. | Per-round committed output is `[accepted draft prefix, correction-or-bonus]`; `C` is its length (1, 2, or 3 for k=2). |
| Output cap | Remaining-budget clamp occurs at lines 180-185; `n_predict` advances by the complete returned `ids` at line 298. | Never commit beyond 128 generated tokens; reduce proposal width near the boundary. |
| Accounting | `n_drafted += n_draft`, `n_accept += ids.size()-1`, `n_predict += ids.size()` at lines 294-298. | Proposed tokens count every generated candidate; accepted draft tokens exclude the correction/bonus; committed progress includes it. |
| Reset | Target and speculative contexts are initialized from the prompt before the loop at lines 126-150. | Clear target KV and replay the prompt for every observation; OpenVINO generation calls are independent full-prefix reconstructions. |

## State strategy selected

- Target: persistent llama.cpp low-level context on explicit `Vulkan0`, with KV removal for rejected candidate suffixes.
- OpenVINO CPU: full committed-prefix replay for every proposal.
- OpenVINO NPU: full committed-prefix replay for every proposal using the already-qualified NPU LLMPipeline configuration and cache.
- Replay is scientifically neutral for token semantics. Its time is part of `draft_time` and therefore inside future primary end-to-end latency; it is never subtracted as setup.

## Required assertions

After every round, the orchestrator records and asserts:

1. target KV maximum position equals `len(prompt_tokens) + len(committed_output) - 1`;
2. target logical history equals orchestrator history;
3. OpenVINO replay input equals prompt tokens plus orchestrator history;
4. committed output is exactly accepted draft prefix plus one correction/bonus token;
5. proposed, accepted and per-round C counters reconcile.

Any violation aborts qualification and forbids formal Phase-3 measurement.

