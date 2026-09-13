# HeteroSpec-PC

Characterizing correctness-constrained heterogeneous speculative decoding across consumer AI PCs.

## Research question

Can spare CPU, integrated-GPU, or NPU compute accelerate single-user, batch-1 LLM decoding on a discrete GPU? The project studies traditional draft-target speculative decoding, including correctness, verification amortization, runtime integration, energy, and memory-capacity constraints.

## Current results

Three completed platforms establish a cross-platform mechanism result rather than a universal yes/no answer:

- **Windows / Core Ultra 9 275HX + RTX 5070 Ti Laptop — closed.** CPU-assisted drafting did not outperform RTX-only decoding in the tested Qwen3-8B/14B configurations. In the matched HumanEval follow-up, exact serialized `k=2` controls reached 0.404x (CPU to RTX) and 0.650x (RTX to RTX). The fast CUDA two-token verification path costs approximately one target decode but can change the greedy argmax; the exact path costs 2.14--2.43 target decodes.
- **macOS / MacBook Air M4, 24 GB — closed.** The representative frozen Spec-Bench 24Q confirmation was negative at 0.842x, while the separately preregistered 30-prompt HumanEval code-conditioned study confirmed a profitable fixed-`k=2` regime at **1.387x** (95% CI [1.351, 1.422]), with 30/30 prompts faster and 90/90 token-exact pairs. Fixed `k=2` was package-energy neutral within uncertainty; the registered `p_min=0.9` secondary condition improved package energy.
- **Windows / Core i5-13400 + Arc B570 — closed.** The Vulkan fast path was correctness-blocked: 45/90 frozen HumanEval30 pairs were token-exact, with a diagnostic 0.538x geometric-mean speedup and 0.696x Arc-board energy-efficiency ratio. The single preregistered serialized fallback (`n_ubatch=1`) passed its six-prompt gate but was not universally exact on the full selection (60/90 pairs; 20/30 prompts). Its clean V2 ratios were 1.983 and 1.992 at contexts 512 and 2048; its overall diagnostic speedup was 0.309x, with 0/30 prompts faster and a 0.302x board-energy-efficiency ratio. Both energy-efficiency ratios are baseline board J/token divided by speculative board J/token, so values below one favor the baseline. No B570 path qualifies as a correctness-admissible optimization result.
- **Windows / Core Ultra X7 358H — pending.** No result is claimed.

The joint interpretation is that high acceptance is necessary but not sufficient. Profitability depends on a correctness-preserving execution path that batches target verification cheaply, retains target/draft state, and keeps draft plus orchestration cost below the target work avoided. Unified memory may enable the M4 implementation, but the repository does not isolate it as the sole cause.

See [`paper/notes/VERIFICATION_AMORTIZATION_FRAMEWORK.md`](paper/notes/VERIFICATION_AMORTIZATION_FRAMEWORK.md), [`paper/notes/CROSS_PLATFORM_MECHANISM.md`](paper/notes/CROSS_PLATFORM_MECHANISM.md), and [`reports/b570/B570_EXACT_FALLBACK_VALIDATION.md`](reports/b570/B570_EXACT_FALLBACK_VALIDATION.md) for the unified model and evidence chain.

## Repository layout

- `scripts/`: experiment, telemetry, correctness, and analysis programs; legacy paths are retained to preserve imports.
- `analysis/`: processed datasets used by reports and figures.
- `artifacts/`: publication-sized authoritative archives explicitly listed by the data policy.
- `reports/`: platform reports, mechanism controls, and generated figures.
- `configs/`: portable platform and experiment configuration.
- `benchmarks/`: frozen selections, preregistrations, and upstream dataset provenance; benchmark datasets are not redistributed.
- `docs/`: protocol, reproduction, hardware, data policy, and publication checks.
- `requirements/`: per-platform dependency specifications.

## Reproduction status

- 275HX + RTX 5070 Ti: processed data, reports, manifests, and runners available; local raw run logs are excluded.
- M4: the HumanEval archive includes frozen prompts, the authoritative `results.json`, raw `telemetry.csv`, checksums, processed summaries, reports, and runners. Historical M4 evidence is indexed in `reports/m4/M4_EXPERIMENT_INDEX.md`.
- i5-13400 + Arc B570: qualification, formal correctness, post-gate diagnostics, clean exact-fallback validation, PresentMon board telemetry, processed summaries, and manifests are available under [`reports/b570/`](reports/b570/) and [`artifacts/b570_backend_control/`](artifacts/b570_backend_control/). B570 paper-critical artifacts are stored with Git text conversion disabled; all 1,843 manifest entries were audited against the committed Git object bytes.
- 358H: pending; do not infer a result from configuration files alone.

Set `HETEROSPEC_ROOT`, `HETEROSPEC_MODEL_ROOT`, `HETEROSPEC_DATA_ROOT`, and `HETEROSPEC_CACHE_ROOT` when local assets live outside the clone. Model weights, downloaded datasets, caches, virtual environments, and most machine-local raw runs are intentionally absent. See `docs/reproduction.md` for evidence tiers and supported regeneration paths.

## Publication status

The repository is private and the three completed platform conclusions are consolidated. Public release remains blocked on choosing a license, finalizing author metadata in `CITATION.cff`, and completing a final release-time privacy and secret review. No paper, DOI, or archival release is claimed yet.

