# M4 Correctness Check

## Result

**BASELINE = PASS**

**SPECULATIVE = PASS**

**EXACT MATCH = PASS**

The bounded MLX-LM 0.31.3 test used Spec-Bench root-cause ID 395 (21 prompt tokens), Qwen3-8B 4-bit target, Qwen3-0.6B 4-bit draft, greedy decoding, batch 1, 64 output tokens and fixed `k=4`. Both weight files were SHA-256 checked against their Hugging Face linked ETags before loading.

| Field | Baseline | Native speculative |
|---|---:|---:|
| Output tokens | 64 | 64 |
| Token SHA-256 | `93d056ae...a5da0ae` | `93d056ae...a5da0ae` |
| First divergent token | N/A | None |
| TTFT | 335.63 ms | 378.82 ms |
| Completion | 4,040.75 ms | 3,115.37 ms |
| End-to-end output rate | 15.84 tok/s | 20.54 tok/s |
| MLX generation rate | 17.46 tok/s | 23.42 tok/s |
| Accepted draft output tokens | 0 | 37 / 64 (57.81%) |
| MLX peak allocator | 4.402 GiB | 4.742 GiB |

The same exact-match result was observed in the preceding cold/compile canary. The warm canary is about 1.30x faster end-to-end, but this is one prompt and **not a formal speedup claim**. Swap grew during the paired process, so the configured memory gate prevents expansion to additional `k` values or 12Q in this session.

A separate target-only medium canary used frozen ID 291 (400 prompt tokens). It completed 64 tokens at 17.11 MLX generation tok/s, with 2,562.80 ms TTFT, 6,331.80 ms completion and 4.718 GiB MLX peak allocation.

Raw token arrays and full metrics remain in ignored local files under `work/m4/`; benchmark content and raw runs are not committed.
