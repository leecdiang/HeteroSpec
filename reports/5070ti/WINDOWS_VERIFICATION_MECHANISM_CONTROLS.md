# Windows exact-verification mechanism controls

## Scope

Two narrow follow-ups were run after platform closure. They validate the already observed mechanism; they do not reopen the benchmark, search for a winning configuration, or change the frozen conclusion.

## 1. Exact verification cost microbenchmark

`llama-bench` measured the same Qwen3-8B Q8_0 CUDA target with Flash Attention off. `PP2/PP1` is used as a target-forward proxy for `T_verify(2)/T_decode(1)`: the only change is whether one or two adjacent tokens are evaluated. Each cell contains 20 repetitions and reports the ratio of medians.

| Context depth | CUDA batched, `ubatch=2` | Exact serialized, `ubatch=1` |
|---:|---:|---:|
| 0 | 1.009× | 2.431× |
| 256 | 0.983× | 2.137× |

The batched path evaluates two tokens for approximately the cost of one, consistent with the M4 mechanism range reported by the companion experiment. The correctness-preserving Windows path instead costs **2.14–2.43×**. This directly quantifies the lost verification amortization: exactness forces the execution onto a near-serial path whose two-token cost is more than twice single-token decode.

This is a kernel-level proxy, not an end-to-end speculative time decomposition. It deliberately excludes draft generation, acceptance, transfer and orchestration.

## 2. CUDA divergence minimum reproduction

The original model files, llama.cpp b10839 (`0cae43063`), CUDA 12.4 build, driver 616.56, greedy seed 123, `k=2`, and `ubatch=2` were frozen. Two previously examined prompts were repeated three times.

| Prompt | Diverged | Stability | First captured divergence | Token IDs (baseline/spec) |
|---|---:|---:|---:|---:|
| HumanEval/106 | 3/3 | Same location and tokens in every repetition | index 190 | 2790 / 2629 |
| HumanEval/129 | 0/3 | Exact under this `ubatch=2` setting | — | — |

HumanEval/106 is therefore a stable minimal reproducer. The speculative run diverged at the identical captured token index and selected the identical alternative token in all three repetitions; acceptance was 95% each time. In the already completed `ubatch=1` 30-prompt control, all three HumanEval/106 pairs were exact. This supports the causal sequence:

> batched CUDA target evaluation → repeatable token divergence → exactness gate requires `ubatch=1` → verification cost rises above 2×.

The index refers to the runner's tokenized captured output, which includes a shared rendered prefix; it is intended as a deterministic reproduction coordinate, not a semantic completion-token count.

### Logit-margin limitation

This llama.cpp CLI build exposes generated token IDs and aggregate performance statistics but does not export per-step top logits/logprobs for speculative CLI execution. Consequently, the logit margin is recorded as **unavailable**, not estimated from token identity. Obtaining it would require instrumenting or changing the runtime, which is outside this minimal validation and would weaken the frozen-build reproduction.

**Subsequent evidence:** “unavailable” describes this original CLI-only control, not the final archive state. A later isolated, same-commit diagnostic build captured the target scores without modifying the formal binary and found the stable margin sign flip. `CUDA_DIVERGENCE_NUMERICAL_DIAGNOSIS.md` supersedes this limitation for the numerical mechanism claim; the measurements in this report remain unchanged.

## Conclusion

These controls strengthen rather than change the closed-platform result. Windows CUDA has an efficient batched two-token path, but that path is not lossless for the stable HumanEval/106 case. The exact fallback makes two-token target verification cost 2.14–2.43 times one-token decoding, removing the core amortization speculative decoding depends on.

Artifacts: `WINDOWS_EXACT_VERIFICATION_COST.csv`, `WINDOWS_CUDA_DIVERGENCE_MINREPRO.csv`, and the reproduction scripts under `scripts/`.
