# Experiment protocol

Use batch-1 greedy decoding, fixed seeds and explicit device selection. Record the Git commit, model revision, prompt IDs, decoding configuration, correctness result, performance, memory, and available component telemetry for every formal run. `AUTO` and `MULTI` are forbidden for single-device OpenVINO claims.

For the Core Ultra X7 358H study, follow `docs/358H_RUNBOOK.md`. Complete and commit every `FILL_*` field in `benchmarks/358h_threshold_validation/preregistration_v1.json` before collecting formal measurements. The 358H sequence is qualification -> CPU/iGPU/NPU draft characterization -> predictive break-even gate -> end-to-end validation only for paths classified BORDERLINE or GO.
