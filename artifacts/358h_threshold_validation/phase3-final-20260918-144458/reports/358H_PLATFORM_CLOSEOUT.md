# 358H platform closeout

## Final class

**CORRECTNESS-ADMISSIBLE / NOT PROFITABLE — CLOSED**

The Core Ultra X7 358H Phase-0 environment, Phase-1 isolated draft characterization, Phase-2 threshold analysis, and Phase-3 heterogeneous end-to-end validation are complete. The platform is closed under the frozen protocol; no parameter sweep, runtime tuning, model substitution, or follow-up timing campaign was performed after formal data began.

## Final finding

Both CPU and NPU use the same frozen OpenVINO Qwen3-0.6B INT4 draft semantics and generated token-exact output against the explicit Vulkan0 Qwen3-8B Q8_0 baseline for all 90 HumanEval30 pairs each. Yet their end-to-end geometric-mean speedups were 0.734x (CPU, 95% CI [0.693, 0.771]) and 0.352x (NPU, [0.333, 0.369]). Neither path was faster on any of the 30 prompts.

Acceptance was high (CPU 75.31%; NPU 75.13%) and committed work was about 2.46 output tokens per speculative round. That did not reach the Phase-2 optimistic C=3 regime. CPU is dominated by target verification; NPU is dominated by full committed-prefix replay plus proposal. Therefore isolated NPU throughput does not survive the currently qualified end-to-end system path.

## Boundaries and limitations

- Target placement: explicit Vulkan0, 37/37 model layers and 36/36 KV layers; CPU/NPU draft binding is explicitly evidenced per session.
- Full-prefix replay is part of the real system cost and remains included in the primary metric.
- OpenVINO's full-prefix generation call cannot separate replay time from proposal time without altering the measured execution; only their combined cost is reported.
- End-to-end energy: CPU **NOT CLAIMED**; NPU **NOT ADMISSIBLE**.
- The historical upstream Transformers revision of the canonical draft GGUF remains a documented provenance limitation. The frozen IR uses the previously qualified STRONGLY_SUPPORTED reconstructed source; this was not changed for Phase 3.

## Future work

A future state-reuse or idealized-replay control could test whether the NPU result is limited by this OpenVINO/adapter state interface. It is not part of this closed study and must be separately preregistered before any data collection.

