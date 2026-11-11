# M4 Portability Audit

## Verdict

The experiment contract and processed-analysis layer are portable; the Windows execution and telemetry layers are not. The bounded Mac path should use a thin MLX-LM runner and native speculation rather than porting the CUDA/OpenVINO verifier.

| Area | Classification | Evidence / required action |
|---|---|---|
| Research question and within-platform relative speedup | Platform-independent | Reuse unchanged; do not compare Mac and Windows absolute tok/s as equivalent configurations. |
| `benchmarks/root_cause_12q/selection.json` | Direct reuse | All 12 frozen IDs exist in upstream Spec-Bench; prompt content stays in ignored `datasets/`. |
| Processed CSV analysis and figure builders | Reuse with schema adapter | Analysis code is mostly platform-neutral once the runner emits the shared columns. |
| Run schema | Reuse with extension | Add Apple runtime memory, swap, pressure, thermal state and observed power domains. |
| Phase 1 Intel qualification | OpenVINO-only | Scripts import OpenVINO/OpenVINO GenAI and explicitly select Intel devices. Do not port for this phase. |
| Phase 2--6 target/speculative runners | CUDA/NVML/OpenVINO-only | They call `torch.cuda`, CUDA synchronization/allocator APIs, bitsandbytes, NVML, and/or OpenVINO. Replace with the MLX adapter. |
| Windows setup | PowerShell-only | `scripts/setup/windows/configure_env.ps1` remains Windows-specific and unchanged. |
| NVIDIA telemetry | NVML-only | `check_nvml.py`, `nvidia-smi`, and in-process loggers cannot be reused on macOS. |
| macOS scaffolding | Reusable | `scripts/setup/macos/` now performs system, MLX, MPS and memory gates without personal paths. |

## Hard-coded paths

One tracked metadata field remains Windows-specific: `benchmarks/specbench/pilot_60q_ids.json` records the provenance path `D:\\HeteroSpec-PC\\...`. `scripts/migrate_repo_paths.py` intentionally contains old Windows paths as migration search patterns. These do not affect the M4 runner. No new Mac file contains a hard-coded `/Users/<name>` path.

## Adapter boundary

`scripts/m4_mlx_smoke.py` accepts a target, draft, dataset, prompt ID, output cap and fixed `k`; it uses the same prompt preparation for baseline and native speculation, records raw token IDs/hashes, TTFT, completion time, throughput, accepted-output markers, MLX peak memory and swap snapshots. It does not modify Platform A results or reproduce the Windows custom verifier.

The analysis adapter for a later 12Q pilot should map those records into the existing run schema. That adapter is intentionally deferred until the smoke correctness gate passes.
