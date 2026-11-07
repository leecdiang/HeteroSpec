# Mechanism figure scientific validation v0.5

**Ready within reviewed scope. A and B pass. B is the selected PUBLICATION-CANDIDATE.** No experiments were rerun; no new estimator, CI, theoretical model or runtime intervention was introduced.

Source commit: `974e84540b5193b416e20920629260ff320f759d`. All 32 used source files are locked by Git blob SHA-1 and SHA256 in [source_lock.json](mechanism_v05/data/source_lock.json); their Git hashes were checked against the exact base tree. Original files are unchanged. [evidence.json](mechanism_v05/data/evidence.json) retains full precision and status; [quality.json](mechanism_v05/data/quality.json) records source-grain checks and exclusions.

## Available skills and review discipline

Discovery inspected the current orchestrator and executor catalogs, including all continuation pages. `visualize-data`, `analyze-data-quality`, `validate-data`, and `pdf` were available and their full instructions were read, with relevant shared instructions. System Design was absent, so stages, gates, and boundaries were reviewed manually. `jupyter-notebooks` was present but optional and not used: two small tracked Python scripts provide the extraction and independent audit without a new analysis notebook. No skill was used as scientific authority. Validation uses the scoped authoring workflow, not a reopened experiment audit.

## Evidence re-audit

| Anchor | Independently checked result | Authoritative evidence and meaning |
|---|---|---|
| M4 representative 24Q | 0.8419651017595143×; 95% CI [0.8086934553836356, 0.8767650352539212]; 72/72 exact | `analysis/m4_confirmatory_summary.json` and prompt summary CSV. Prompt GM reproduced from 24 prompt values; original CI retained. Primary, exact negative. |
| M4 HumanEval30 fixed-k2 | 1.3873523375548336×; [1.3505744794957149, 1.421625385088532]; 90/90 exact | `analysis/m4_humaneval_summary.json`, prompt summary CSV, and `benchmarks/m4_code_conditioned_30q/preregistration.json`. Prompt GM reproduced over 30 prompts. Primary, exact profitable, separately preregistered. |
| M4 micro proxy | 1.022181855, 1.076125610, 1.032263523 at contexts 512/2048/8192 | `work/m4/llama_verify_q8_synced.csv`: 84 rows, unique context/width/repetition; each relevant cell has 7 repetitions. Ratio of medians corroborates the target-forward opportunity; not used as a mechanism assignment for M4. |
| RTX batched | 0.9831479829424705–1.0090304299186035 | Raw `artifacts/windows_verification_mechanism/windows-exact-verification-microbench.json` and `reports/5070ti/WINDOWS_EXACT_VERIFICATION_COST.csv`: ratio of medians, 20 samples per operation/cell, depths 0 and 256. Range, not CI. Correctness-blocked under frozen contract. |
| RTX serialized | 2.137011311768208–2.43099575218514; two 90/90 exact secondary controls | Same raw micro file; `HUMANEVAL_LLAMA_REPLICATION.csv`. Qualified serialized secondary controls exist. The schematic must not imply all RTX paths are blocked. |
| RTX divergence | Stable frozen HumanEval/106 mismatch; later same-commit numerical diagnostic corroborates batch-shape-dependent argmax change | `WINDOWS_VERIFICATION_MECHANISM_CONTROLS.md` and `CUDA_DIVERGENCE_NUMERICAL_DIAGNOSIS.md`. A narrow configuration/path result, not a universal CUDA defect or kernel attribution. No divergence number added to artwork. |
| B570 fast diagnostic | 45/90 exact; global qualification fails | `artifacts/b570_backend_control/diagnostic-v1-20260912-170834/raw/diagnostic_summary.json`, including original FAIL and diagnostic labels. |
| B570 serialized diagnostic | 60/90 exact; `global_admissible=false` | `analysis/b570_exact_fallback_summary.json`; `reports/b570/B570_VERIFICATION_MECHANISM.md`. Legacy `V2_exact` fields are preserved in source, never promoted as a path status. |
| 358H isolated drafting, context 8192 | CPU 30.80706214904785; NPU 48.08302688598633 tok/s | `analysis/358h_draft_device_summary.csv` and JSON, final Phase 1 telemetry-OFF medians. Original 95% CIs: CPU [30.343034744262695,31.361581802368164], NPU [47.103416442871094,48.4038200378418]. |
| 358H CPU Phase 3 | 90/90 exact; prompt GM 0.7339145857381156×; complete target-side 87.3364614301828% | `analysis/358h_phase3_prompt_summary.csv` and summary JSON. Prompt GM replayed from per-prompt medians of three matched time ratios; fraction recomputed as ratio of arithmetic totals. Optional artwork anchor omitted for space. |
| 358H NPU Phase 3 | 90/90 exact; prompt GM 0.35166323938180594×; replay+proposal 58.3474076350763% | Same final Phase-3 sources. Original 95% speedup CI [0.33259483634282594,0.36894872997722167] is retained in A's caption. |
| 358H interface and timing | One synchronous OpenVINO call receives the full committed prefix and returns proposals; initial prefill is outside primary timing | `reports/358h/358H_PHASE3_END_TO_END_VALIDATION.md`, `358H_RUNNER_SEMANTICS_MAPPING.md`, and `scripts/platform/358h/phase3_heterogeneous_runner.py`. The last file is a qualification/dry-run implementation, not a new claim that reconstructed source equals the lost historical formal source. The existing STRONGLY_SUPPORTED qualification remains. |

Statistical bounds were read and matched to authoritative summaries, not recomputed or homogenized. The independent verifier recomputes consequential point ratios and percentages using a separate implementation; it imports neither extraction nor rendering helpers. This is not a fresh full bootstrap audit. Prompt CIs remain conditional on each frozen campaign and do not capture all between-session variation.

## Data-quality controls

Seven relevant tables passed expected row count, unique grain and required-field checks. M4 prompt data have 24/30 rows; the synchronized micro file has 84; RTX micro summaries have 4 rows and raw cells have 20 samples per operation; serialized controls have 180 paired rows; Phase-1 summaries have 6 device/context rows; final Phase 3 has 180 request-level rows (90 per device, 30 prompts × 3 repetitions).

The misleading `analysis/358h_phase3_prompt_level.csv` is confirmed header-only and excluded. The final `prompt_summary.csv` is treated as request-level despite its filename. B570 formal V2 remains NOT RUN after the formal gate failure; subsequent fast and serialized observations remain diagnostic. Contaminated early serialized values are not used. Historical labels and reports are reconciled with frozen raw/processed evidence and the handoff, not selected for a cleaner story. No new conflicting numerical result was found.

## Phrase and boundary review

| Figure statement or visual choice | Validation / allowed inference |
|---|---|
| Local opportunity → qualification → stateful realization → outcome | An ordering of evaluation/measurement boundaries. Caption explicitly says arrows do not guarantee gain. It is not a new algorithm or an exhaustive theory. |
| Solid filled continuation; dashed open blocked endpoint | Only admissible execution continues to a qualified outcome. No blocked path is assigned a qualified speedup. |
| `V_k^micro` separated from `R_target` | Artwork explicitly says the micro proxy is not complete target work. RTX context range is not a CI; contexts are not presented as matched across platforms. |
| Acceptance separated from `C` | Artwork says acceptance is not `C`. Caption defines all committed output, including correction/bonus tokens; `C` sits below a rule separating progress from cost terms. |
| B570 60/90 exact count | A labels the bounded pair count, immediately followed by globally inadmissible. B's caption says serialization does not qualify the full workload. Neither calls the path exact. |
| 358H isolated advantage lost at measured interface | Supported by Phase-1 throughput, Phase-3 matched outcomes/timed regions and runtime semantics. No intrinsic NPU weakness, replay-only duration, state-persistent intervention or complete causal attribution is claimed. |
| 358H percentages versus headline speedup | The NPU percentage is share of speculative post-prefill time from arithmetic totals; headline speedup is prompt GM. A's caption preserves this distinction and uncertainty. No accounting equation is used to derive the headline GM. |
| M4 opposite observed outcomes | Two independent frozen studies on the same tested Metal stack. Workload/session conditions differ; no workload-only causality or paired between-workload inference. Not assigned to either diagnosis. |
| Profitable / exact but negative | Explicitly labeled observed regimes, not the only possible outcomes in general. These are qualified outcomes, not hardware categories. |
| Configuration-scoped and non-exhaustive | Printed in both figures and captions. No universal claim about correctness, state management, CUDA, Vulkan, or NPUs. |
| Post-prefill decode | Printed at the outcome stage and stated in captions. Excludes loading and initial prompt prefill; not whole-request user-perceived latency. |

## Numerical and visual acceptance

[validate.py](mechanism_v05/scripts/validate.py) checks original-source invariants, original CI values, numeric bindings in compiled A text and caption, qualitative phrases in both compiled figures, path encodings, and output geometry. All figure numbers are independently matched to sources. A has no implied common numeric axis; B has no decimal numerical evidence anchors. Automated phrase checks support but do not replace the manual claim review above.

Final PDF checks: vector-only, all font programs embedded, exact nominal double-column width, and all text bounds inside the page. SVGs contain no raster image nodes and use vector glyph outlines; both were independently rendered with MuPDF and inspected. `pdffonts` corroborated embedded Type-1 font subsets. No overfull TeX boxes. Minimum ordinary label is 8 TeX pt; mathematical scripts are approximately 5.98 PDF pt, inspected at native size.

Both final candidates were inspected in color and grayscale at 96 and 180 dpi, with 6.75-in native geometry (648 px and 1215 px wide). Same-width captioned proofs were also inspected. Filled/solid versus open/dashed/text status remains understandable without blue. Alignment, arrow weight, whitespace, math, and callout hierarchy pass; no clipped or overlapping text remains. The answer to “systems-paper schematic or infographic?” is **systems-paper schematic** for both, with B more economical.

No physical printer test or final manuscript pagination is claimed. Print at 100%, without fit-to-page scaling. Results and final output SHA256 values are in [validation.json](mechanism_v05/qa/validation.json) and [MECHANISM_MANIFEST.json](mechanism_v05/MECHANISM_MANIFEST.json).
