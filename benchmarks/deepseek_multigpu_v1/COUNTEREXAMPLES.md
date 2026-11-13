# Prior art and counterexample requirements

## Review conclusion

The current deliverable is a feasibility/design PR with a CPU planning utility. It does **not** establish a novel accelerator or a representative end-to-end improvement. The following checks are intended to disprove weak versions of the hypothesis before expensive confirmation.

## Existing systems that the method must exceed

| Source | Existing capability | Consequence for the proposed contribution |
|---|---|---|
| [vLLM adaptive verification](https://github.com/vllm-project/vllm/blob/75be5c3919b6a82fa1885c0d0a2250adba477413/docs/features/speculative_decoding/adaptive_verification.md) | Per-position survival estimates, global verification budget, startup shape-cost profiling and online acceptance calibration for eligible proposers | Confidence, batch size, measured hardware cost and variable horizon are not by themselves new. Use the strongest eligible native policy. |
| [SGLang adaptive parameters](https://github.com/sgl-project/sglang/blob/219b7e7a688363bac9ef09eacf80e44eef9efe4b/python/sglang/srt/speculative/adaptive_spec_params.py) | Observed acceptance, batch-size tiers and hysteresis | Its built-in EAGLE/EAGLE3, top-k=1 restrictions and exclusions for attention data parallelism, multilayer EAGLE and two-batch overlap are eligibility conditions, not absence of adaptation. |
| [DeepInfer deployment explanation](https://github.com/deepseek-ai/DeepInfer/blob/a679bb86ce36e883a98a97733492b686e5b9a08e/doc/inference_deployment_qa.md) | Profiled throughput, confidence-based prefix selection and asynchronous recomputation | Dynamic verification is already a production feature; its gains are workload-dependent. |
| [TurboSpec](https://arxiv.org/abs/2406.14066v3) | Hardware-profiled, closed-loop goodput optimization for speculative inference | Compare concrete observables, actions and objective, not just the label “cost-aware controller.” |
| [vLLM batch invariance](https://github.com/vllm-project/vllm/blob/75be5c3919b6a82fa1885c0d0a2250adba477413/docs/features/batch_invariance.md) | Native arithmetic intended to remain invariant across batch size/order | A legal grouping schema is not a new numerical guarantee or acceleration algorithm by itself. Native compatible batching is an essential control. |

The potentially different part is a decision over **numerically legal groups, actual page/state geometry and distributed critical-path cost**, combined with a verified lowering. This remains unproven. Native measured step cost may already capture much of topology cost. Before claiming novelty, specify the exact missing transformation, show a native trace where it matters, and compare action spaces, cost models, state constraints, supported proposers and runner restrictions. If it is already implemented upstream, reuse it and narrow or abandon the claimed contribution.

## A direct negative counterexample

The pinned DeepInfer explanation reports the following estimated throughput changes for dynamic verification versus fixed length 5:

| Concurrency | Estimated throughput change |
|---:|---:|
| 16 | −1.5% |
| 32 | +1.6% |
| 48 | +3.6% |
| 60 | +5.4% |
| 72 | +6.7% |

This is its EP64/DP64 deployment example, not an A5000 measurement, not request-latency evidence and not a prediction for this PR. EP means expert parallelism and DP means data parallelism. It directly cautions against claiming universal >5% gains from adaptation: low concurrency can be worse while high concurrency improves.

## Tests that can invalidate the candidate

1. **No added useful parallelism.** A short verification block is already batched by the native engine. Regrouping it can leave the same padded tile underfilled; TP shrinks output-channel work further. Require an actual reduction in launches, data movement or critical-path work versus the native batched path, without increasing proposal length. Generic tile tuning belongs in both arms.
2. **Communication dominates.** On PCIe TP4/8, mandatory per-layer collectives may dominate. An ordered fallback can be slower and consume more memory than stock NCCL. Test message-size curves, empty-rank participation, topology and peak temporary storage. A memory formula and a CUDA routing proposal are not a working collective.
3. **Equal lengths but different visible state.** Two queries can have equal length while seeing different pages, masks, positions, shared-prefix ownership or sliding-window contents. Test page boundaries, causal/tree masks, head ownership, rollback and stale epochs. A graph key omitting these can be wrong; one including every changing physical address can have no reuse.
4. **Metadata work is already hidden.** Native graphs and asynchronous scheduling may overlap the CPU work that a new cache eliminates. Sorting, hashing, device barriers and shape proliferation can instead add exposed latency. Split immutable schema plans from refreshed device descriptors; record refresh cost, hit rate, recapture count and barriers. Count only critical-path savings, not overlapped work twice.
5. **N-gram has no useful match.** Native no-match behavior still produces ordinary rejectable draft positions in the inspected implementation. Test no-match, accept-zero and accept-all cases, proposer cost and actual committed tokens per target cycle. A low-acceptance panel cannot be discarded. Native n-gram integration is available, but its inspected speculator does not activate confidence-based adaptive verification merely because a config flag is set.
6. **Controller cost exceeds its decision benefit.** Test abrupt length/acceptance/load changes, expensive policy evaluation and rare shapes. Charge profiling, calibration, graph capture, warmup, cache memory and their amortization horizon. Freeze development and confirmation separately.
7. **Stochastic semantics change.** Greedy qualification does not cover stochastic output distributions. Identical random seeds alone are insufficient when batching changes random-number consumption. A stochastic extension needs request/position-stable RNG ownership and sampling/state tests, plus distributional validation appropriate to the algorithm. RNG means random-number generation.
8. **A gain is only a changed numerical mode.** If the scheme requires a new ordered reduction or slower invariant backend, compare both to optimized native deployment. Do not claim bitwise preservation of stock NCCL/cuBLAS after changing their arithmetic, or hide that overhead behind a slow reference.

## Corrections made after cross-checking

- The DSpark-only comment in `vllm/config/speculative.py` is stale relative to its general draft-model runtime and current adaptive-verification documentation. It was removed as a support restriction in this design.
- The selected normal GPU worker at this pin directly uses `v1/worker/gpu/model_runner.py`; the mapped integration is not assumed to require an old optional V2 switch.
- FlashAttention 2 accepts the split-count setting used by the inspected invariant path, but source compatibility still requires native qualification.
- Budget reserves and mathematical payload lower bounds are now separately labelled in the CPU tool.
- The initial root-bootstrap interval is explicitly conditional on shared worker rounds, not a claim about all session variability.
- N-gram/eager-mode engineering checks are not treated as representative evidence against mature learned-proposer and graph-enabled deployments.

## Attribution and claim rules

For fixed-policy lowering, the three-arm confirmation in PORTABLE_METHOD.md separates stock, common tuning and the incremental plan. If the joint controller track is selected, require four factorial cells on common tuning: native controller/native lowering, new controller/native lowering, native controller/new lowering, and new controller/new lowering. Keep stock native as a separate fifth arm. Ablate page geometry, legality and TP-cost features when claiming they explain the difference. A controller win with no independent lowering benefit is not a grouping win.

The five-arm version would require 11,520 measured +11,520 warm +360 primers = **23,400 requests in 180 workers**, before qualification and failures. Adding a separate no-speculation arm gives **28,080 requests in 216 workers**. These are alternative unlaunched designs, not additions silently covered by the 14,040-request three-arm estimate. Freeze the selected design and complete cost before execution.

For a statistical claim of more than 5% latency reduction, the upper confidence bound on the declared ratio estimand must be below 0.95, not merely its point estimate. Framework-specific >5% claims need framework-specific supporting intervals with prespecified multiplicity treatment. Predeclare workload weights, session treatment, acceptable regression criteria and how interactions limit the claim. Report every regression; do not discard cells because they fail a practical target. A point estimate that passes 5% with uncertainty crossing the threshold remains inconclusive for that target.

Batch-1 and concurrency-4 confirmation supports a low-concurrency domain. Saturation-serving generality requires the separate arrival/SLO study; different hardware families require additional hardware evidence. Representative support is a bounded claim, never a guarantee for all frameworks, models, loads and interconnects.
