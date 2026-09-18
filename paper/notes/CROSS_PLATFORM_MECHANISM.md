# Cross-Platform Mechanism

## Joint result

The completed studies show both a correctness-constrained verification boundary and a state-interface boundary. M4/Metal has a profitable exact `k=2` region for the frozen code workload; Windows/CUDA exposes a cheap batched target-forward path that fails token equality, while its exact fallback serializes verification. On 358H, CPU and NPU paths remain exact, but repeated committed-prefix reconstruction makes the realized draft subsystem too expensive—especially on NPU. High acceptance and favorable isolated device throughput therefore coexist with opposite end-to-end outcomes.

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

### Windows / Core Ultra X7 358H, Vulkan target + OpenVINO draft

1. CPU and NPU paths used the same frozen Qwen3-0.6B OpenVINO draft semantics and the same explicit Vulkan0 Qwen3-8B target.
2. Both paths passed the frozen Stage-A gate (18/18 exact) and the full HumanEval30 comparison (90/90 exact per device).
3. Acceptance remained high at 75.31% on CPU and 75.13% on NPU, with mean committed work near 2.46 tokens per speculative round.
4. Nevertheless, post-prefill decode speedup was 0.734x [0.693, 0.771] for CPU and 0.352x [0.333, 0.369] for NPU; neither was faster on any of 30 prompts.
5. CPU time was dominated by target verification (87.34%). NPU time was dominated by the synchronous full-prefix replay-plus-proposal call (58.35%). Residual Python/orchestration time was about 0.02–0.04%, so host bookkeeping is not the primary explanation.
6. The NPU result does not show that the NPU lacks compute. It shows that isolated draft throughput cannot survive an adapter that reconstructs model state for every speculative proposal round.

Mechanism: exact device binding and high acceptance are still insufficient when the runtime boundary cannot retain/reuse draft state. The relevant draft term is the realized stateful subsystem cost, not vendor TOPS or isolated steady-state generation throughput.

## Correctness-constrained comparison

| Link | M4 outcome | Windows outcome |
|---|---|---|
| Cheap two-token target batch exists | Yes, `V_2` 1.022--1.076 | Yes, `V_2` 0.983--1.009 |
| Cheap path passes frozen exactness gate | Yes for tested llama.cpp/Metal cells | No on stable HumanEval/106 case |
| Cheapest tested exact path | Still near-one verification | Serialized `ubatch=1`, `V_2^exact` 2.137--2.431 |
| High-acceptance HumanEval workload | 90.1%, 1.387x | >91%, 0.404x CPU-to-RTX / 0.650x RTX-to-RTX |
| Bounded conclusion | Profitable code-conditioned exact regime | Correctness-blocked primary; exact controls decisively negative |

358H supplies a complementary exact-but-unprofitable case: unlike CUDA/B570 correctness blocking, both draft placements pass token equality, yet CPU remains verification-bound and NPU becomes state-reconstruction-bound. It therefore separates *correctness admissibility* from *runtime state efficiency*.

## Claims safe for publication

- Verification amortization must be defined after correctness filtering.
- Acceptance is not a platform-independent predictor of profitability.
- Transfer overhead is material on Windows but not sufficient to explain the result.
- M4 profitability is workload-conditioned; the representative 24Q study remains negative.
- The cross-platform contrast changes multiple factors and cannot be attributed solely to unified memory, Metal, CUDA, OpenVINO, NPU hardware, or GPU architecture.
- Isolated accelerator throughput is not a valid proxy for speculative draft cost when the end-to-end adapter reconstructs the committed prefix.
- 358H is an exact negative result under the qualified implementation, not evidence that all NPU speculative decoding designs must be unprofitable.

## Preregistration deviation

The M4 HumanEval preregistration required a corrected synthetic ceiling after the primary and `p_min` conditions: conditional probabilities 0.6/0.7/0.8/0.9/0.95/1.0 mapped to unconditional llama.cpp rates `p,p^2`, five repetitions per level and baseline, 128 output tokens, and order seed 20260911. No tracked run artifact matches that design.

The existing `work/m4/llama_synthetic_crossover.json` and its mechanism report predate the preregistration and use different probabilities, rate mapping, repetition count, output length, and seed. They remain valid only as an earlier diagnostic. The corrected ceiling is recorded as **not completed / no repository evidence found**. This consolidation does not run it, infer its break-even threshold, or claim compliance with the preregistered stop-rule sequence.
