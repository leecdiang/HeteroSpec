# Reproduction

## Evidence levels

1. **Audit existing evidence:** requires only the clone. Read machine-readable summaries, reports, manifests, preregistrations, and the tracked paper-critical raw archives.
2. **Regenerate derived summaries/figures:** use the tracked analysis scripts and their documented inputs. This should not invoke model inference.
3. **Re-run experiments:** requires the original class of physical platform, independently obtained model weights and benchmark data, matching runtime/build details, and platform telemetry. Re-running is outside repository consolidation.

## Common setup

1. Clone the repository and create an isolated Python 3.11 environment.
2. Install the applicable file under `requirements/`; do not combine the Windows and macOS freezes.
3. Obtain model weights and upstream benchmark data independently.
4. Set `HETEROSPEC_ROOT`, `HETEROSPEC_MODEL_ROOT`, `HETEROSPEC_DATA_ROOT`, and `HETEROSPEC_CACHE_ROOT` when assets live outside the clone.
5. Run device and memory gates before inference. A requested unavailable device is an error; do not silently fall back.

## M4 evidence

The formal HumanEval archive is self-contained for result auditing:

- preregistration: `benchmarks/m4_code_conditioned_30q/preregistration.json`
- frozen prompts and authoritative records: `artifacts/m4_humaneval_code_conditioned/`
- summarizer: `scripts/summarize_m4_humaneval.py`
- processed summary: `analysis/m4_humaneval_summary.json`
- report: `reports/m4/M4_HUMANEVAL_CODE_CONDITIONED.md`
- full historical evidence map: `reports/m4/M4_EXPERIMENT_INDEX.md`

The preregistered corrected synthetic ceiling is **not reproduced by a matching tracked result**. `work/m4/llama_synthetic_crossover.json` is an earlier, differently parameterized exploratory mechanism diagnostic and must not be relabeled as the preregistered ceiling.

## Windows RTX evidence

The platform-level result and matched HumanEval follow-up are summarized in `reports/5070ti/FINAL_5070TI_PLATFORM_REPORT.md` and `reports/5070ti/HUMANEVAL_LLAMA_REPLICATION.md`. The paper-critical raw provenance tracked in Git is split into three archives:

- `artifacts/windows_humaneval_replication/` — exact `ubatch=1` replication, correctness-aborted `ubatch=2` attempt, and supporting NVML telemetry.
- `artifacts/windows_verification_mechanism/` — raw 20-repetition verification microbenchmark supporting the exact-verification ratios.
- `artifacts/windows_cuda_divergence/` — raw divergence minimum reproduction, authoritative logit-capture payload, and supporting telemetry.

Each archive contains a `manifest.json` with size/SHA-256 integrity, runtime metadata, classification, derived outputs, and exclusions.

## Arc B570 evidence

B570 is closed. Qualification, the formal correctness gate, the full post-gate diagnostic, and the unique serialized fallback validation are documented under `reports/b570/` and archived under `artifacts/b570_backend_control/`.

The B570 archive uses Git text conversion disabled for paper-critical files. The closeout audit verified committed Git-object bytes against manifest size/SHA256 entries. The serialized fallback remained non-universal on the full HumanEval30 selection, so its overall timing is diagnostic only.

## 358H evidence

The 358H Phase 0–3 scientific campaign is complete. Audit entry points are:

- environment/provenance qualification: `reports/358h/358H_ENVIRONMENT_QUALIFICATION.md`
- frozen preregistration and execution addendum: `benchmarks/358h_threshold_validation/`
- Phase-3 result and mechanism decomposition: `reports/358h/358H_PHASE3_END_TO_END_VALIDATION.md`
- formal execution disclosure: `reports/358h/358H_FORMAL_EXECUTION_AMENDMENT.md`
- repository transport audit: `reports/358h/358H_REPOSITORY_CLOSEOUT_AUDIT.md`
- byte-complete evidence bundle: `artifacts/358h_threshold_validation/phase3-final-20260918-144458/358h_phase3_complete_evidence.tar.gz`

The bundle is gzip-compressed tar, 694239 bytes, SHA256 `2fa6197864b1c6fc7af1c6da31f24ccf224e3dc0933bc1534840117eaee08511`. Extract it and validate the 34 files against the enclosed `manifest.json`. The separately visible approximately-80-KiB copies of the largest JSON/CSV files were truncated by the initial Git transport and are non-authoritative previews.

Re-running requires the independently obtained frozen model artifacts, the recorded llama.cpp/OpenVINO builds, explicit Vulkan0 target binding, explicit CPU/NPU draft binding, and a newly frozen formal host-state record. The primary Phase-3 metric excludes prompt prefill. Do not interpret token exactness as HumanEval functional correctness or package telemetry as NPU energy.

## Interpretation constraints

- Preserve frozen prompt sets, seeds, model revisions, quantization/precision, `k`, runtime flags, pairing, and stop rules.
- Apply correctness gates before reading a timing as performance evidence.
- Treat “exact” as paired token equality, not functional correctness of generated code.
- Do not compare energy domains as though they were the same sensor boundary.
- Do not fill missing evidence from prose, a different experiment, or a platform with similar hardware.
- For 358H single-device claims, explicit CPU/GPU/NPU binding is mandatory; OpenVINO `AUTO` and `MULTI` are not admissible substitutes.
