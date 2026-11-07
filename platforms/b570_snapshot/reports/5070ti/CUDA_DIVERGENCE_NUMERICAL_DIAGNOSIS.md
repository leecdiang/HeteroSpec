# CUDA divergence numerical diagnosis

## Background

This is a post-hoc mechanism probe of one already frozen observation. It does not modify the formal performance results, tune CUDA, or reopen the Windows benchmark.

## Frozen observation

HumanEval/106 previously diverged in 3/3 independent processes at captured index 190: baseline token 2790 versus speculative `ubatch=2` token 2629. The `ubatch=1` exact control matched the baseline in 3/3 runs.

## Method

The official b10839 server API could reproduce the divergence but omitted target probabilities for accepted draft tokens. A separate diagnostic server was therefore built from formal llama.cpp commit `0cae43063`. The only behavioral instrumentation copies the target context's pre-sampling top probabilities at each speculative batch output into the diagnostic response before the batch-index vector is cleared. The formal binary was neither overwritten nor rerun.

Build configuration: Zig 0.16.0 C/C++, Release, static diagnostic host, `GGML_BACKEND_DL=ON`, CPU/RPC build disabled, and the unchanged official b10839 CUDA backend DLLs dynamically loaded. The committed patch and its SHA-256 are recorded with the machine-readable summary.

The API applies the identical Qwen chat template with thinking disabled. Its generated-token index 65 maps to the old runner's captured index 190 because that capture included a 125-token rendered prefix. All three paths share identical generated token IDs through API index 64. Scores returned by llama.cpp are log-softmax values. They equal raw logits up to a position-wise additive constant, so candidate ordering, logit differences and top1–top2 margins are exact.

## Results

All values below were identical across three independent process runs.

| Path | Argmax | score(2790) | score(2629) | Δ = 2790−2629 | top1−top2 margin |
|---|---:|---:|---:|---:|---:|
| Baseline single-token | 2790 | −0.699409 | −0.780357 | **+0.080948** | 0.080948 |
| Speculative CUDA `ubatch=2` | 2629 | −0.799518 | −0.673060 | **−0.126457** | 0.126457 |
| Speculative CUDA `ubatch=1` | 2790 | −0.699409 | −0.780357 | **+0.080948** | 0.080948 |

The instrumentation preserved the original behavior: `ubatch=2` diverged at API index 65 / captured index 190 in 3/3 runs, while baseline and `ubatch=1` remained identical. The prefix before the evaluated position was exactly equal in all nine captures.

Thus:

```text
Δ_baseline > 0
Δ_serial   > 0
Δ_batch    < 0
```

The two candidates are near-tied and their ordering reverses only in the batched path. Top-5 records for captured indices 188–191 are in `CUDA_DIVERGENCE_LOGITS.csv`.

## Interpretation

> The fast CUDA batched path and the exact serialized path operate on the same token prefix but produce a different ordering of two near-tied logits at the first divergence position.

This directly supports a batch-shape-dependent numerical argmax flip. Together with the separate verification-cost measurement, it explains the observed constraint: fast two-token verification is available, but strict correctness forces serialization and removes its amortization advantage.

It does not identify a specific CUDA kernel, Tensor Core operation, or Q8_0 implementation as the cause.

## Limitations

- Post-hoc diagnostic on one stable divergence prompt.
- The response instrumentation may in principle perturb execution, although it reproduced the original index and token pair exactly in 3/3 runs.
- Returned scores are normalized log probabilities, not unnormalized raw logits; all reported differences and ranks are invariant to that normalization.
- No kernel-level causal attribution was attempted.
- HumanEval/129 was not rerun here because the preceding minimum-reproduction control already established it as a negative case under `ubatch=2`; the stop rule required ending after the three-path HumanEval/106 capture.
