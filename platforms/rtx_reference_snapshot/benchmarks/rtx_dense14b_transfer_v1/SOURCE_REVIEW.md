# Source review and host acceptance boundary

Reviewed 2026-11-01. This is a new dense-model experiment, not a restart of PR151.

## Reuse and actual changes

The previous worker, arm specification, build script and transaction auditor were read at commit `29511ed91eb9f3d9773cfdda53e3554b0f4ad08b`. Their exact Git blob IDs are executable guards in common.py. The native adapter reads those blobs using git show and creates a new staged directory. Missing or repeated patch anchors fail before source staging. Old source, executables, DLLs, outputs and reference records are never written.

The old source hardcodes full GPU loading and rejects CPU attention. The adaptation changes target offload only, keeps draft fully offloaded, records CPU/GPU operation placement, guards 14B geometry, removes the unused GS pool, uses a new study identity and exports sequence state after the request timer. The actual sampling, proposal, all verification rows, acceptance, bonus/correction, pending token and KV trimming loop is reused. The inherited build fully recompiles the new core/worker from its authenticated source capsule while retaining the 21-library numerical cohort.

## What was validated here

76 distinct standard-library tests passed in a Linux CPU container. They cover strict JSON/path/hash utilities; candidate selection and exposure exclusions; 40/120/576 slot counts; six-arm ordering; endpoints; actual-shape/device validation; primary and secondary estimators; A/A and session reversal cases; fail-closed source anchor guards; bounded GGUF parsing; ZIP reopening; and full-size synthetic 151,936-logit artifacts with missing/corrupt/mismatched data mutations. The internal-difference test deliberately permits endpoint-preserving non-top-logit differences and reports them separately.

The artifact fixture uses a small transaction-validation stub; it does not certify the historical native transaction auditor. Host execution loads that separately pinned auditor and applies it to actual rows. No synthetic fixture is a native result.

## Host work still required

Actual Windows Job Object behavior and cleanup, old-source capsule availability, native API signatures, C++ compilation/linking, target download/hash, correct tokenizer/template use, backend selection,40-layer mixed-placement geometry, peak working set and output reference must be tested on the existing RTX machine. No actual GPU or model was available in the authoring container. Build and feasibility status are therefore NOT_RUN, not PASS. Ordinary compatibility repairs are delegated in ENGINEERING_POLICY.md.

The runner already implements native subprocess/handshake execution and raw-record checks; it is not merely a normalized-data template. However, CPU tests cannot prove that a CUDA/CPU hybrid graph is numerically admissible. Technical errors may be fixed with retained receipts; true reference failures must not be relabelled as engineering errors.

## Specific review corrections

- R's native selector remains1 even though R has no local repair; it is not incorrectly assigned QB selector0.
- Half-resident configurations require actual QK device and GQA shape observations at all40 layers, not only accepting a CPU string.
- The draft remains loaded for every arm; unused GS pools are removed without changing the chosen comparisons.
- Complete-unit recovery re-audits retained raw records. Failed or incomplete units do not silently rerun.
- A surviving/unverified owned process keeps the GPU lock for actual host inspection.
- Heavy diagnostic full-logit writes stay inside diagnostic execution and their durations are not performance samples; clean timing has no such writes. Additional sequence-state export is after the clock.
- Source-code/asset freeze, raw qualification reconstruction and its seal are checked before formal sessions. All candidate endpoints share the newly defined14B R at the chosen placement.
- Four sessions do not create four independent dates, and the analyzer creates no population confidence interval.

## Primary external identity sources

Official architecture: https://huggingface.co/Qwen/Qwen3-14B/blob/main/config.json
Pinned official GGUF: https://huggingface.co/Qwen/Qwen3-14B-GGUF/blob/c75e7b2d0234068f674a1bacf548ea32e27ccd29/Qwen3-14B-Q8_0.gguf
Runtime ancestry: https://github.com/leecdiang/HeteroSpec/tree/29511ed91eb9f3d9773cfdda53e3554b0f4ad08b/scripts/experiments/rtx_scope_transfer_v1
The actual model hash and architecture metadata, not a mutable web page, govern host execution.
