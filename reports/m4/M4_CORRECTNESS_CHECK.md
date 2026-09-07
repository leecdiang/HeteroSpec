# M4 Correctness Check

## Result

**BASELINE = PASS**

**SPECULATIVE = PASS**

**EXACT MATCH = FAIL ON FROZEN QUESTION 469**

The earlier question-395 canary remains a valid local pass, but it did not
generalize to the frozen 12-question set. After rebooting to zero swap, the M2
runner stopped after the first question block as required by the exact-token
gate.

| Frozen question 469 condition | Output rate | Accepted draft outputs | First divergence | Exact |
|---|---:|---:|---:|---|
| Baseline | 16.85 tok/s | 0 / 64 | reference | Yes |
| `k=2` | 31.61 tok/s | 41 / 64 | index 24 | **No** |
| `k=4` | 26.21 tok/s | 47 / 64 | index 24 | **No** |
| `k=6` | 25.16 tok/s | 51 / 64 | index 24 | **No** |

All three speculative conditions produced the same 64-token sequence, while
the baseline produced another deterministic sequence. A separate fresh-process
`k=2` rerun reproduced the divergence at index 24. The common prefix ends after
"total cost of the items John made."; baseline next selected token `14374`
(`###`) while the batched speculative verification selected token `16` (`1`).

At that shared-prefix step, the sequential baseline target log-probabilities
were approximately -0.75 for `###` and -1.00 for `1`. Under the speculative
batched target call both values were represented as -1.00, and greedy argmax
selected the lower token ID. This is evidence of a deterministic near-tie
flip caused by the quantized/BF16 target's different computation shape. It is
not evidence of stochastic sampling or draft-only token commitment.

**Formal interpretation:** runtime execution passes, but native MLX-LM
speculation with this 4-bit target fails HeteroSpec's strict exact-token gate.
The apparent speedups on question 469 are invalid for promotion.

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

The same question-395 exact-match result was observed in the preceding
cold/compile canary. The warm canary was about 1.30x faster end-to-end, but it
was one prompt and is superseded as a qualification result by the frozen
question-469 failure above.

A separate target-only medium canary used frozen ID 291 (400 prompt tokens). It completed 64 tokens at 17.11 MLX generation tok/s, with 2,562.80 ms TTFT, 6,331.80 ms completion and 4.718 GiB MLX peak allocation.

Raw token arrays and full metrics are archived under `work/m4/`; the archive
commit preserves the original files without rewriting their embedded local
paths.

## Precision rescue and independent-runtime control

An 8-bit MLX target did not rescue strict equivalence. Two fresh-process
checks reproduced deterministic divergence: question 395 first diverged at
output index 54, and question 469 first diverged at output index 60. The
original 4-bit question-469 index-24 flip disappeared, but exactness still
failed at a later position.

The independent `llama.cpp` 0.4.0 Metal control used official Qwen Q8_0 GGUF
artifacts for both the 8B target and 0.6B draft. It passed both frozen questions
at every tested draft depth:

| Runtime / target | `k` | Q395 | Q469 | Gate |
|---|---:|---|---|---|
| llama.cpp Metal / Q8_0 | 2 | Exact | Exact | PASS |
| llama.cpp Metal / Q8_0 | 4 | Exact | Exact | PASS |
| llama.cpp Metal / Q8_0 | 6 | Exact | Exact | PASS |

The runner compares canonical token sequences produced by the tokenizer
embedded in the target GGUF over the isolated completion text. CLI banners,
prompt echo and timing lines are excluded. This establishes that strict greedy
equivalence is achievable on the same Apple GPU and narrows the observed
failure to MLX's speculative/batched-verification numerical path or its
interaction with target quantization. It does not yet qualify 12Q performance.
