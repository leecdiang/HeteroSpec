# Hardware platforms

See `configs/platform_*.yaml` for portable configuration and the platform reports for measured facts. A configuration file is not evidence that a platform was run.

| Platform | Role | Status | Evidence boundary |
|---|---|---|---|
| Intel Core Ultra 9 275HX, 48 GB, RTX 5070 Ti Laptop 12 GB, Intel iGPU/NPU, Windows 11 | Primary heterogeneous AI-PC platform | **Closed** | CPU/iGPU/NPU draft qualification; Qwen3-8B/14B experiments; power; HumanEval replication; verification/correctness controls. Independent Intel iGPU/NPU power domains were unavailable. |
| MacBook Air M4, 24 GB unified memory, macOS | Architecture/backend control | **Closed** | MLX correctness diagnostics and llama.cpp/Metal correctness, mechanism, Spec-Bench, energy, and HumanEval evidence. Composite package telemetry is host/build-specific. |
| Intel Core i5-13400 + Intel Arc B570, Windows 11 | Discrete-GPU backend/correctness control | **Closed** | Vulkan qualification; formal correctness gate; HumanEval30 post-gate diagnostic; serialized fallback validation; Arc-board power/energy; publication-sized raw provenance. |
| Intel Core Ultra X7 358H, 32 GB, Arc B390/Xe3-class iGPU, ~50-TOPS NPU, Windows 11 | Predictive draft-cost threshold validation | **Scientifically closed** | Explicit CPU/GPU/NPU qualification; CPU/NPU isolated draft characterization; formal Vulkan0-target HumanEval30 validation. CPU 0.734x and NPU 0.352x, 90/90 token-exact pairs each, 0/30 prompts faster. Post-prefill decode timing only; no end-to-end energy or HumanEval pass@k claim. |

The completed Windows, M4, B570, and 358H studies are not hardware-only controlled comparisons. They differ in runtime, GPU architecture, quantization path, scheduling, and memory organization. Unified memory is therefore an enabling hypothesis, not an isolated causal result.

The 358H study is intentionally different from the B570 backend-control study: it tested whether a stronger consumer NPU could reduce **isolated draft cost** enough to approach the speculative-decoding break-even boundary. Isolated NPU throughput was competitive, but the qualified end-to-end adapter rebuilt the committed prefix for every proposal call; replay plus proposal dominated NPU speculative time and the realized path was decisively negative. The runbook remains the reproduction entry point, not authorization to extend the closed campaign.

Platform-specific environments must remain separate. Do not silently fall back between CPU, iGPU, NPU, CUDA, Vulkan, Metal, or MLX devices, and record runtime/build identifiers with any future evidence.
