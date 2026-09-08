# Repository audit

- Top-level entries: .git, .gitignore, CITATION.cff, CONTRIBUTING.md, FIRST_COMMIT_FILELIST.txt, LICENSE_PLACEHOLDER.md, README.md, REPO_STATUS.md, analysis, artifacts, benchmarks, configs, docs, logs, paper, pyproject.toml, repo_audit.md, reports, requirements, schemas, scripts, src, work
- File count: 289
- Total size: 0.01 GiB

## Large files

| Path | MiB | >50 MiB | >100 MiB |
|---|---:|---:|---:|

## File classes

| Class | Count |
|---|---:|
| `.safetensors` | 0 |
| `.gguf` | 0 |
| `.onnx` | 0 |
| `.bin` | 0 |
| `.pt` | 0 |
| `.pth` | 0 |
| `.npy` | 0 |
| `.npz` | 0 |
| `.jsonl` | 0 |
| `.csv` | 28 |
| Virtual environments | 0 files |
| Hugging Face cache | 0 files |
| Model store | 0 files |
| Tracked raw telemetry | 1 files |

## Absolute-path audit

- Files containing a macOS/Linux user path, original project root, or Windows user path: 15.
- Findings in authoritative or historical records may be retained for provenance, but must be reviewed for privacy before public release.
  - `artifacts/m4_humaneval_code_conditioned/results.json`
  - `work/m4/llama_q503_extraction_smoke.json`
  - `work/m4/q469_8bit_k2.json`
  - `work/m4/q395_k4_postreboot_timed.json`
  - `work/m4/q469_k2_correctness_recheck.json`
  - `work/m4/llama_confirmatory_24q.json`
  - `work/m4/llama_metal_q8_12q_formal.json`
  - `work/m4/llama_metal_q8_395_469_k6.json`
  - `work/m4/qwen3_8b_8bit_load_smoke.json`
  - `work/m4/m4_mlx_12q_pilot.json`
  - `work/m4/llama_k2_decomposition.json`
  - `work/m4/llama_metal_q8_395_469_k4.json`
  - `work/m4/llama_metal_q8_395_469_k2.json`
  - `work/m4/qwen3_8b_bf16_load_smoke.json`
  - `work/m4/q395_8bit_k2_recheck.json`

## Protection decision

- No source data was deleted.
- Models, caches, virtual environments, runs, archives, raw logs, general raw telemetry, and machine profiles are excluded through `.gitignore`.
- The tracked M4 HumanEval `telemetry.csv` is the documented authoritative raw-data exception.
- Processed analysis CSVs, reports, figures, portable scripts, configs, and provenance IDs are candidates for Git.
