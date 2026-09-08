# Reproduction

## Evidence levels

1. **Audit existing evidence:** requires only the clone. Read machine-readable summaries, reports, manifests, preregistrations, and the M4 HumanEval authoritative archive.
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

The preregistered corrected synthetic ceiling is **not reproduced by a matching tracked result**. `work/m4/llama_synthetic_crossover.json` is an earlier, differently parameterized mechanism diagnostic. Do not relabel it as the preregistered ceiling.

## Windows evidence

The platform-level result and the matched HumanEval follow-up are summarized in `reports/5070ti/FINAL_5070TI_PLATFORM_REPORT.md` and `reports/5070ti/HUMANEVAL_LLAMA_REPLICATION.md`. Exact-verification ratios and the numerical divergence capture are tracked under `reports/5070ti/`; machine-local raw replication logs remain excluded as declared in those reports.

## Interpretation constraints

- Preserve frozen prompt sets, seeds, model revisions, quantization, `k`, runtime flags, pairing, and stop rules.
- Apply correctness gates before reading a timing as performance evidence.
- Treat “exact” as paired token equality, not functional correctness of generated code.
- Do not compare energy domains as though they were the same sensor boundary.
- Do not fill missing evidence from prose, a different experiment, or a platform with similar hardware.

