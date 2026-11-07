# LLM42_DVR_GGML_W32 mapping

Source: Microsoft `llm-42` revision `143cb7075d96b756edc3ef44e6f752cb4fcc90e2`, specifically `python/sglang/srt/llm42/llm42_worker.py`, `llm42_info.py`, README, and the author's v2 paper (https://arxiv.org/html/2601.17768v2). Exact read-file hashes are delivered with the final source receipt.

This is an external-method adaptation to a single-request Q8_0 GGML/CUDA stack. It is not the original SGLang/H100 system, grouped dynamic serving, or a reproduction of its published speeds. Window32 and one verification request are the present study's fixed choices.

| Method operation | This implementation |
|---|---|
| Fast decode | Same target model, shared immutable weights, private UB4 context. Ordinary greedy selection with the actual model's runtime suppression set. No small drafter or offline output tape. |
| Consistent initial state | Independent verifier context with UB32 prefill, FA off, one sequence. Its own first pending token is committed; equality to UB1 ordinary R is separately measured. |
| Verify | Pending token plus at most31 fast proposals. All32 causal query slots and logits are actually evaluated in the UB32 context. Short tails use valid dummy ID32. Actual shapes are checked in engineering. |
| Correction/bonus | Compare each proposal with the previous input row's verifier prediction. Keep the accepted prefix and first correction. All-accepted blocks may commit the final real row's bonus. Cap and first native runtime EOG stop committed output. |
| Rollback | Remove verifier KV from the first unprocessed/corrected pending position onward, including all padding and rejected future inputs. Optimistic fast KV is discarded before the next window. |
| KV replacement | Paid sequence-state export/import copies the verifier's retained prefix to the fast context. Full state byte equality, source preservation and positions are checked in engineering; selected raw state objects are archived. |
| Request reset | Clear both sequence memories and reset the stateless greedy/suppression sampler at every request. There is no cross-request prompt/result cache. |
| Endpoint | Complete native committed IDs through first EOG, including it, or cap128. No text retokenization or cropping. Pending EOG/cap1 endpoints need no further verification window. Synthetic forced-pending-EOG tests exercise this endpoint branch without claiming a natural ordinary decision. |

The source implementation pads groups of requests and maintains SGLang allocator/page-table resources. Here dummy rows are later causal positions of one sequence. Their KV/logits are never committed. Padding32 versus33 control fixtures test earlier real-row decisions; source code and actual call shapes provide the mapping evidence. Grouped scheduling, multi-request batching, cross-device behavior and global bitwise determinism are outside this adaptation.

All online fast decode, fixed32 verify, padding, KV export/import, rollback, sampling, synchronization and response construction are paid inside the common resident HTTP client boundary. Model load, teardown, synthetic warmup, engineering graph observation and diagnostic state-file writes are separated. Formal E disables graph callbacks and all synthetic fixture controls. E's custom generation timer has a different boundary from the old server's `predicted_ms`; **E generation comparisons are null**. Full client request latency is the shared primary boundary.

Engineering and reference-contract gates are independent. A valid, repeat-stable adaptation that differs from ordinary R is `COMPLETE_CONTRACT_MISMATCH`, with qualified speedup null. It does not establish an error in the original LLM-42 paper or system.

Six explicitly synthetic verified-EOG decision fixtures inject a terminal runtime EOG at proposal indices0/15/30, after an actual32-query decode. They preserve the unmodified native proposals and predictions separately; preceding comparator decisions are synthetically aligned to reach the intended endpoint branch. They test the shared commit/rollback/termination logic, not natural model choices or a consistent continuation after such an injection. Formal processes reject these controls and omit engineering token-decision traces and byte-roundtrip checks; minimum block counts and KV owner metadata remain in their response.
