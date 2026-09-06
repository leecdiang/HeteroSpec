# M4 Correctness Check

## Current status

**NOT RUN — requires the physical M4 MacBook Air.** No correctness claim is made from this Windows audit.

## Gate protocol

1. Freeze macOS, MLX, MLX-LM, model revisions, quantization, tokenizer/chat template, prompt token IDs, `temperature=0`, `batch=1`, output cap and EOS handling.
2. Run baseline twice on two canary prompts. The two baseline token-ID arrays must match exactly.
3. Run native speculation at fixed `k=2` on the same prompts. Compare generated token IDs, not decoded text alone.
4. On success, run all 12 existing `root_cause_12q` prompts for `k=2,4,6`; dynamic/default scheduling is a separate labeled condition.
5. Store target tokens, speculative tokens, SHA-256 hashes and the zero-based first-divergence index. Text equality is secondary.

## Decision rules

- `PASS_EXACT`: all baseline/speculative token IDs match for the condition.
- `FAIL_RUNTIME`: load, cache trim, unsupported operation or generation error.
- `FAIL_CORRECTNESS`: any token mismatch. Timing may be kept as diagnostic only and must not enter headline speedup.
- `NONDETERMINISTIC_BASELINE`: repeated baselines differ; stop before speculation.

On mismatch, rerun one prompt with identical model files, then test unquantized/smaller canary if it fits and optionally reproduce in llama.cpp. Classify the likely layer as numerical/quantization, tokenizer/template, sampling policy, cache implementation or speculative implementation. Do not relax exactness to “similar text” to obtain a performance result.

Open MLX-LM Qwen3 mismatch reports make this gate a prerequisite rather than a formality: [#1423](https://github.com/ml-explore/mlx-lm/issues/1423) and [#1470](https://github.com/ml-explore/mlx-lm/issues/1470).

