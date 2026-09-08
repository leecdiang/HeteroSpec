# Cross-Platform Mechanism

## Joint result

The completed studies show a correctness-constrained verification boundary. M4/Metal has a profitable exact `k=2` region for the frozen code workload; Windows/CUDA has a similarly cheap batched target-forward path, but that path fails token equality on a stable case, and the exact fallback serializes verification. High acceptance therefore coexists with opposite performance outcomes.

## Evidence chain

### M4 / llama.cpp Metal

1. The llama.cpp correctness gate was exact for the tested `k=2/4/6` cells.
2. At `k=2`, synchronized target verification measured 1.022--1.076 single-token decodes across tested prefix lengths. Width four and six rose to approximately 1.53--1.63 and 2.28--2.32 respectively.
3. Keeping an idle draft resident added only 0.65% to the bounded target-only control, arguing against residency alone as the main loss.
4. The frozen representative Spec-Bench 24Q confirmation was negative: 0.842x, 72/72 exact, and worse package energy. The higher-acceptance tertile reduced the loss but remained below one.
5. The separately preregistered HumanEval 30Q study was positive: fixed `k=2` 1.387x [1.351, 1.422], 30/30 faster, 90/90 exact, 90.1% acceptance, and 1.798 accepted draft tokens/round. The result establishes workload dependence, not general profitability.

Mechanism: cheap exact width-two verification plus tight state reuse creates the opportunity; structured, high-predictability code completions supply enough committed work to realize it. Unified memory is compatible with this chain but is not isolated from Metal kernels, scheduling, and implementation behavior.

### Windows / llama.cpp CUDA

1. The matched HumanEval batched replication failed the hard exactness gate on HumanEval/106 for both CPU-draft and RTX-draft placement.
2. The failure repeated at the same captured index and token pair in 3/3 processes. Baseline and exact `ubatch=1` selected token 2790; `ubatch=2` selected 2629.
3. At the shared prefix, the score difference `score(2790) - score(2629)` changed from +0.080948 in baseline/serialized execution to -0.126457 in batched execution. This is direct evidence of a batch-shape-dependent numerical argmax flip, not identification of a particular kernel.
4. Batched `ubatch=2` has `V_2` approximately 0.983--1.009, so cheap verification exists physically. It is not admissible for the formal result because it diverges.
5. Exact `ubatch=1` raises `V_2^exact` to 2.137--2.431. Under that path, CPU-to-RTX and RTX-to-RTX HumanEval controls reached only 0.404x and 0.650x despite acceptance above 91% and 90/90 exact pairs each.
6. Same-GPU placement recovers part of the loss, proving CPU-to-CUDA transfer/synchronization matters, but remaining below one proves it is not the sole explanation. Earlier custom/native controls likewise show that KV/state reuse and runtime integration materially change cost.

Mechanism: the backend exposes a fast batched route, but strict greedy equivalence forces the tested configuration onto a near-serial target-verification route. Draft cost and orchestration then add to a verification term already exceeding two baseline steps.

## Correctness-constrained comparison

| Link | M4 outcome | Windows outcome |
|---|---|---|
| Cheap two-token target batch exists | Yes, `V_2` 1.022--1.076 | Yes, `V_2` 0.983--1.009 |
| Cheap path passes frozen exactness gate | Yes for tested llama.cpp/Metal cells | No on stable HumanEval/106 case |
| Cheapest tested exact path | Still near-one verification | Serialized `ubatch=1`, `V_2^exact` 2.137--2.431 |
| High-acceptance HumanEval workload | 90.1%, 1.387x | >91%, 0.404x CPU-to-RTX / 0.650x RTX-to-RTX |
| Bounded conclusion | Profitable code-conditioned exact regime | Correctness-blocked primary; exact controls decisively negative |

## Claims safe for publication

- Verification amortization must be defined after correctness filtering.
- Acceptance is not a platform-independent predictor of profitability.
- Transfer overhead is material on Windows but not sufficient to explain the result.
- M4 profitability is workload-conditioned; the representative 24Q study remains negative.
- The cross-platform contrast changes multiple factors and cannot be attributed solely to unified memory, Metal, CUDA, or GPU architecture.

## Preregistration deviation

The M4 HumanEval preregistration required a corrected synthetic ceiling after the primary and `p_min` conditions: conditional probabilities 0.6/0.7/0.8/0.9/0.95/1.0 mapped to unconditional llama.cpp rates `p,p^2`, five repetitions per level and baseline, 128 output tokens, and order seed 20260911. No tracked run artifact matches that design.

The existing `work/m4/llama_synthetic_crossover.json` and its mechanism report predate the preregistration and use different probabilities, rate mapping, repetition count, output length, and seed. They remain valid only as an earlier diagnostic. The corrected ceiling is recorded as **not completed / no repository evidence found**. This consolidation does not run it, infer its break-even threshold, or claim compliance with the preregistered stop-rule sequence.
