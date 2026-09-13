# 358H platform scripts

Status: **SCAFFOLD ONLY — NO FORMAL RUNNER YET**

This directory is intentionally documentation-only until Phase 0 qualification freezes the exact Intel/OpenVINO commands, device names, model representations, and telemetry interfaces for the Core Ultra X7 358H machine.

Do not copy B570 scripts blindly: B570 is a discrete Vulkan backend-control platform, while 358H is a CPU/iGPU/NPU draft-device threshold study.

When qualification is complete, scripts added here should minimally provide:

- explicit CPU / GPU / NPU device discovery and binding;
- model hash verification;
- warm-up and steady-state draft-latency measurement;
- no-fallback validation;
- machine-readable run manifests;
- paired baseline/speculative execution for Phase 3 if a path passes the threshold gate;
- telemetry capture only for validated sensor domains.

All formal scripts must consume the frozen settings in `benchmarks/358h_threshold_validation/preregistration_v1.json` rather than inventing parameters at runtime.
