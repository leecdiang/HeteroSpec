# Arc B570 Backend-Control Platform Closeout

## Final disposition

- formal run: `formal-v2-20260912-122930`
- overall status: `COMPLETE_STOP_RULE`
- correctness: `FAIL`
- V2 exact 512: `NOT RUN`
- V2 exact 2048: `NOT RUN`
- classification: **UNCLASSIFIED (V2 prohibited after correctness failure)**
- HumanEval30: **NOT_RUN_BY_PREREGISTRATION_V2_SEPARATE_LATER_PHASE**

The B570 was added as a Vulkan backend-generalization control for the Intel Core i5-13400 / Arc B570 / DDR4-3200 / Windows 11 25H2 platform. Runtime was llama.cpp b10839 (`0cae43063`), Vulkan0, frozen Qwen3-8B and Qwen3-0.6B Q8_0 hashes, full offload, greedy decoding, k=2, ctx 1024, batch 512, ubatch 128, and a 128-generated-token contract.

## Preregistration history and stop rule

Qualification commit `385f3fc590e4b37d27d7ae6db9211aa7803c84ba` preceded replacement preregistration commit `59185f24793eb2b852be0821295d13c44ad97636`, which preceded this result. The v1 attempt failed because batch/context capacity and CLI token-boundary semantics made it invalid; it remains retained as **INVALID / CONFIGURATION-BLOCKED**, not a Vulkan numerical failure.

Preregistration v2 is controlling. Its stop rule permits only the six-prompt correctness gate followed, on exact PASS, by V2. It explicitly describes HumanEval30 as a separate later proposal and declares power measurement false. Therefore this unattended closeout did not run HumanEval30, even if the prompt's later-stage gate would otherwise allow it. PresentMon Card Power was collected per the newer operational request, but is classified as supporting telemetry rather than preregistered formal energy evidence.

## Energy boundary and limitations

The sensor boundary is Intel Arc B570 **GPU board energy**, `PM_METRIC_GPU_CARD_POWER` at 100 ms, integrated over exact QPC workload bounds. CPU package energy was unavailable, so no result is whole-system energy. Level Zero B570 energy was unsupported. Correctness-run supporting median J/token was `6.292920` baseline and `5.449823` speculative; these are not promoted to a preregistered energy comparison.

No CUDA/Vulkan/Metal causal equivalence is claimed. Results characterize only the tested runtime, models, driver, device and frozen settings. The B570 platform is **CLOSED** unless a later paper-review protocol explicitly reopens it.

## Post-gate diagnostic extension (diagnostic-v1-20260912-170834)

The original formal correctness result remains **FAIL** and unchanged. A later explicitly post-hoc diagnostic extension measured frozen HumanEval30 prevalence and raw mechanisms; it cannot rescue or replace the gate. See `B570_DIAGNOSTIC_EXTENSION.md`.

## Exact fallback final validation (exact-fallback-v1-20260912-222617)

- correctness: 60/90 exact pairs
- V2_exact: 512=1.9827, 2048=1.9917
- speedup GM: 0.3087
- Arc B570 board-energy efficiency ratio: 0.3023
- platform status: CLOSED
