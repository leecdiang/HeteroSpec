# M4 Experiment Index

This index distinguishes authoritative raw evidence from derived summaries.
Unless stated otherwise, the platform is a 24 GB MacBook Air M4. Model weights,
virtual environments, downloaded datasets, caches, and local build products are
not archived.

| Experiment | Commit | Input/config | Authoritative output | Report | Core conclusion |
|---|---|---|---|---|---|
| Portability, memory, telemetry qualification | `db572c8` | `configs/platform_m4_mba.yaml`, macOS setup scripts | bounded qualification records under `work/m4/` | `M4_FEASIBILITY_SUMMARY.md`, `M4_MEMORY_FEASIBILITY.md`, `M4_TELEMETRY_FEASIBILITY.md` | Infrastructure and composite memory/telemetry gates passed. |
| MLX 4-bit and 8-bit correctness | `a2c0efb` | frozen Q395/Q469, MLX runners | `work/m4/q395_k4_postreboot_timed.json`, `work/m4/q469_k2_correctness_recheck.json`, `work/m4/q395_8bit_k2_recheck.json`, `work/m4/q469_8bit_k2.json` | `M4_CORRECTNESS_CHECK.md` | Both precision paths fail strict exactness; deterministic divergence persists. |
| llama.cpp Metal correctness gate | `45fe981` | Q395/Q469, `k=2/4/6`, official Q8_0 pair | `work/m4/llama_metal_q8_395_469_k2.json`, `...k4.json`, `...k6.json` | `M4_CORRECTNESS_CHECK.md` | Exact at all six prompt/configuration cells. |
| llama.cpp 12Q decision matrix | `4c1ba09` | `benchmarks/root_cause_12q/selection.json`, randomized four-condition order | `work/m4/llama_metal_q8_12q_formal.json`, `work/m4/silemetry_llama_q8_12q_formal.csv` | `M4_LLAMA_12Q_DECISION_EXPERIMENT.md` | Initial `k=2` positive signal: 1.350x; deeper drafts negative. |
| Mechanism diagnosis | `78cd468` | verification microbench, residency control, exploratory synthetic control, paired recheck | `work/m4/llama_verify_q8_synced.csv`, `work/m4/llama_draft_residency_control.json`, `work/m4/llama_synthetic_crossover.json`, `work/m4/llama_k2_repro_check.json` | `M4_SPECULATION_MECHANISM_DIAGNOSIS.md` | Cheap width-two verification and structured acceptance govern profitability. The synthetic control is exploratory (seed 20260903, 3 reps), predates the later preregistration, and its parameter interpretation is superseded by the corrected preregistered design. |
| Representative 24Q confirmation | selection `b556f42`; result `365cc50` | `benchmarks/m4_confirmatory_24q/selection.json`, 3 paired repetitions | `work/m4/llama_confirmatory_24q.json`, `work/m4/silemetry_confirmatory_24q.csv` | `M4_CONFIRMATORY_VALIDATION.md` | Representative signal did not generalize: 0.842x, 72/72 exact. |
| HumanEval 30Q code-conditioned confirmation | preregistration `1646c56`; runner `1ca9dcd`; archive `60fc8e4` | `benchmarks/m4_code_conditioned_30q/preregistration.json`, 30 frozen prompts, 3 repetitions | `artifacts/m4_humaneval_code_conditioned/results.json`, `telemetry.csv` | `M4_HUMANEVAL_CODE_CONDITIONED.md` | Code-conditioned regime confirmed: fixed `k=2` 1.387x, CI [1.351, 1.422], 90/90 exact. |
| Preregistered corrected synthetic ceiling | preregistration `1646c56` | conditional probabilities 0.6/0.7/0.8/0.9/0.95/1.0 mapped to `p,p^2`, 5 reps/level, 5 baseline reps, 128 output tokens, seed 20260911 | **NOT EXECUTED**; no matching result artifact | preregistration status/deviation noted in repository closeout docs | This preregistered secondary item remains incomplete and must not be reconstructed from the earlier exploratory synthetic diagnostic. |

## Authoritative files

For HumanEval, `results.json` is the authoritative performance, schedule,
correctness, memory, acceptance, and per-run energy record; `telemetry.csv` is
the authoritative raw power stream. Files in `analysis/` and figures are
deterministic derivatives produced by `scripts/summarize_m4_humaneval.py`.
`artifacts/m4_humaneval_code_conditioned/manifest.json` records checksums,
software versions, sanitized system metadata, model hashes, and exclusions.

Historical raw M4 files remain under `work/m4/` to preserve their original
paths and bytes. The two local executables in that directory are deliberately
excluded; their source and build scripts are tracked under `scripts/setup/macos/`.
