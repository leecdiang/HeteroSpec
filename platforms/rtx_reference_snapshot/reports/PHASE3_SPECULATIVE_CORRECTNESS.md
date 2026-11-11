# Phase 3 Minimal Heterogeneous Speculative-Decoding Correctness

## Result

**PASS — CPU draft and RTX target were executed in one native Windows process, and every tested speculative output exactly matched the pure RTX greedy reference.**

This is a correctness prototype. Its recompute implementation intentionally favors transparency over performance and its timings must not be reported as production speculative-decoding speedups.

## Runtime configuration

- Draft: Qwen3-0.6B symmetric INT4 OpenVINO IR
- Draft device: explicitly `CPU`
- Target: Qwen3-8B bitsandbytes NF4, BF16 compute, double quantization
- Target device: explicitly `cuda:0`, NVIDIA GeForce RTX 5070 Ti Laptop GPU
- Target attention: PyTorch SDPA explicitly forced to cuDNN
- Prompt: deterministic 64-token sequence
- Decoding: greedy
- Candidate sizes tested: `k = 1, 2, 4, 8`
- Final output: 8 tokens for the first k=1 canary; 16 tokens for k=2/4/8
- Execution: native Windows, single Python process, OpenVINO CPU plus PyTorch CUDA

OpenVINO 2026.3.1 and OpenVINO GenAI 2026.3.1.0 were added to `.venv-target` to support the combined process. The updated environment is frozen in `env/target-pip-freeze.txt`.

## Algorithm checked

1. OpenVINO CPU proposes up to `k` tokens from the current prefix.
2. RTX evaluates the current prefix plus the proposed block in one causal forward pass.
3. Draft tokens are accepted only while they equal the RTX greedy token at the corresponding position.
4. At the first mismatch, the RTX token is appended and all remaining draft candidates are discarded.
5. If the entire block is accepted, one RTX bonus token is appended.
6. The resulting sequence is compared against an independently generated pure RTX greedy reference.

The prototype recomputes the full target prefix each round and does not yet implement KV-cache commit/rollback.

## Results

| k | Exact target match | Rounds | Offered | Accepted | Acceptance | Mismatch rounds | Bonus rounds | Prototype time (s) | Peak CUDA allocation (GiB) |
|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | PASS | 5 | 5 | 4 | 80.0% | 1 | 3 | 1.130 | 5.699 |
| 2 | PASS | 6 | 12 | 10 | 83.3% | 1 | 5 | 1.120 | 5.701 |
| 4 | PASS | 4 | 16 | 13 | 81.3% | 1 | 2 | 1.213 | 5.701 |
| 8 | PASS | 2 | 16 | 14 | 87.5% | 1 | 1 | 0.791 | 5.701 |

For k=2, k=4, and k=8, the pure-target reference SHA-256 was:

`b6928e2dce604be83d9716c9540c3cbffc23c17b8adb070c7597720603a9b3b4`

The corresponding speculative output produced the same hash in every case. The shorter k=1 canary also matched its independent eight-token reference exactly.

## Interpretation and limitations

- Both rejection/correction and all-accepted/bonus paths were exercised, rather than passing only an all-accepted trivial case.
- Target verification, not cross-device draft equality, determines correctness.
- The apparent prototype timing advantage over the reference is not a formal speedup: the reference deliberately performs one full-prefix target forward pass per token, while the prototype verifies blocks. Neither path uses an optimized reusable KV cache.
- Only one deterministic prompt and short output lengths have been checked. Broader prompts, repetition, EOS handling, long contexts, target caching, and telemetry are still required before any performance claim.
- The earlier long-context crash boundary remains protected by explicit cuDNN SDPA; peak allocation here stayed near 5.7 GiB.

## Decision

The heterogeneous runtime and greedy speculative acceptance logic are qualified for an expanded correctness suite. The next implementation step is to test multiple fixed prompts and repetitions, then add target KV-cache commit/rollback with exact-output regression checks before formal timing.

## Evidence

- Harness: `scripts\phase3_speculative_correctness.py`
- Results: `logs\phase3-spec-correctness-k{1|2|4|8}-canary-20260905.json`
- Updated environment: `env\target-pip-freeze.txt`
