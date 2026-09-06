# M4 Portability Audit

## Verdict

The M4 MacBook Air can be a bounded third-platform architecture control, but the existing execution engine is not a drop-in port. The low-cost path is to retain the experiment contract and analysis layer, add a thin MLX-LM runner, and use the runtime's native speculation. Porting the CUDA/OpenVINO custom harness would be a separate medium-to-high-cost systems project.

## Reuse map

| Area | Status | Evidence / action |
|---|---|---|
| Research questions, relative-speedup interpretation | Reuse | Compare each M4 mode with its own M4 baseline; do not rank hardware by absolute tok/s. |
| `root_cause_12q` prompt IDs and selection rule | Reuse | Keep the existing two-per-task split and prompt hashes. Benchmark text remains external under the repository data policy. |
| Result schema | Reuse with extension | `analysis/all_runs.csv` already carries TTFT, TPOT, ITL, acceptance, timing, power, memory, exactness and validity. Add Apple memory/thermal fields without renaming shared columns. |
| Analysis and figures | Reuse | `build_paper_dataset.py`, `build_break_even_and_figures.py`, `build_final_platform_figures.py`, and processed CSV conventions are platform-neutral once an adapter emits the shared schema. |
| Environment setup | Partial | `scripts/setup/macos/configure_env.sh`, `configs/platform_m4_mba.yaml`, and `requirements/macos-mlx.txt` are scaffolds, not frozen reproduction artifacts. |
| Target/draft execution | Replace | Phase 2--6 scripts call `torch.cuda`, CUDA synchronization/memory APIs, bitsandbytes, or OpenVINO. Add an MLX-LM-native runner; do not hide CPU fallback. |
| Custom speculative harness | Not portable directly | `phase3_*` couples an OpenVINO draft to a CUDA verifier and encodes Windows-derived cache/synchronization behavior. Preserve it as Platform A evidence. |
| NVIDIA telemetry | Replace | `check_nvml.py`, `phase2_target_baseline.py`, and power loggers use NVML/`nvidia-smi`. macOS needs a separate qualified logger. |
| Intel telemetry | Replace | Intel Unified Telemetry and OpenVINO device checks are Windows/Intel-only. |
| Windows controls | Not applicable | Power mode, MUX, WDDM, page-file and HYPERVISOR_ERROR mitigations must not be mapped mechanically to macOS. Record macOS power source, Low Power Mode, thermal pressure and swap instead. |

## Required macOS adapter boundary

Implement one platform runner that accepts prompt IDs, fixed `k`, output cap, greedy mode and repetition metadata, then emits the existing run schema plus raw token IDs and a separate per-token timing trace. Runtime-specific fields should include MLX/MLX-LM versions, model revisions, quantization, macOS build, M4 GPU-core count, active/peak MLX memory, system memory pressure and swap deltas.

The adapter must expose baseline and native-speculation modes through the same prompt preparation and timing boundary. It must not recreate the Windows custom verifier in the feasibility phase.

## Scope note

The supplied task attachment ends after the word “最多”. This audit uses the complete preceding constraint as authoritative: 12 questions, baseline plus native speculation, and a small fixed-`k` set only.

