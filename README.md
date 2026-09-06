# HeteroSpec-PC

Characterizing heterogeneous speculative decoding across consumer AI PCs.

## Research question

Can spare CPU, integrated-GPU, or NPU compute accelerate single-user, batch-1 LLM decoding on a discrete GPU? The project studies traditional draft-target speculative decoding, including correctness, runtime integration, energy, and memory-capacity constraints.

## Platforms

- **Platform A — closed:** Intel Core Ultra 9 275HX, 48 GB RAM, RTX 5070 Ti Laptop 12 GB, Intel iGPU/NPU, Windows 11.
- **Platform B — pending:** Intel Core Ultra X7 358H, 32 GB RAM, Intel Arc B390/Xe3-class iGPU, 50-TOPS NPU, Windows 11.
- **Platform C — pending architecture control:** MacBook Air M4, 24 GB unified memory, macOS.

## Current headline result

On the primary 275HX + RTX 5070 Ti Laptop platform, CPU-assisted draft-model speculative decoding did not outperform RTX-only decoding in the tested Qwen3-8B/14B configurations. Root-cause analysis points to verification cost, KV/state reuse, runtime integration, and memory-capacity constraints rather than cross-device copy alone.

## Repository layout

- `scripts/`: experiment, telemetry, correctness, and analysis programs. Legacy scripts remain in place to preserve imports.
- `analysis/`: small processed datasets used by the paper figures.
- `reports/`: platform reports and generated figures.
- `configs/`: portable platform and experiment configuration.
- `benchmarks/`: split IDs and upstream dataset provenance, not redistributed benchmark content.
- `docs/`: protocol, reproduction, hardware, and data policy.
- `requirements/`: frozen or provisional per-platform dependencies.

## Reproduction status

- 275HX + RTX 5070 Ti: processed data and scripts available; platform closed.
- 358H: pending.
- M4: pending.

Set `HETEROSPEC_ROOT`, `HETEROSPEC_MODEL_ROOT`, `HETEROSPEC_DATA_ROOT`, and `HETEROSPEC_CACHE_ROOT` when local assets live outside the clone. Model weights, raw telemetry, and virtual environments are intentionally absent.

## Data policy

Git contains processed data and figure inputs. Model weights, caches, raw traces, and local run directories stay outside Git. A future data release may use Zenodo or a Hugging Face Dataset after licensing and privacy review.

## License

License pending before public release.

