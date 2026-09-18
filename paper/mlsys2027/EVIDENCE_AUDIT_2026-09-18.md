# Evidence audit for MLSys 2027 drafting

Audit date: **2026-09-18**.

This audit distinguishes the repository's merged `main` state from later 358H work that exists on an unmerged experiment branch. It is a writing-control document, not a new scientific result.

## Repository state checked

### `main`

Observed head at audit time:

`7327495d181c91844cf7d031cfcb7384433b2089`

The head is the merge of the 358H experiment-environment preparation PR. The merged repository contains completed M4, RTX 5070 Ti Laptop, and Arc B570 evidence, plus 358H environment qualification. The root README and `REPO_STATUS.md` still describe 358H as pending because later Phase-1/2/runner work has not yet been merged.

### Active 358H experiment branch

Branch:

`codex/358h-phase1-results`

Observed head at audit time:

`0ff44e06ec517da63541f1d2230c56029a9cb5a2`

Relative to current `main`, this branch is ahead and contains the later 358H Phase-1/2 evidence, Phase-3 protocol/freeze material, runner qualification, analysis outputs, and run artifacts.

Important writing rule:

> Treat 358H results from this branch as **provisional evidence during drafting** until the formal Phase-3 campaign closes and the authoritative result is merged/reviewed.

## Completed-platform evidence already suitable for drafting

### M4 / llama.cpp Metal

Safe established evidence includes:
- exact `k=2` verification near one target decode at tested prefix lengths;
- representative frozen Spec-Bench 24Q result: negative overall;
- preregistered HumanEval30 fixed-`k=2`: 1.387x geometric-mean speedup, 95% CI [1.351, 1.422], 30/30 prompts faster, 90/90 exact pairs;
- fixed-`k=2` package-energy result is neutral within uncertainty;
- workload dependence must remain explicit.

Primary writing sources:
- `reports/m4/M4_HUMANEVAL_CODE_CONDITIONED.md`
- `reports/m4/M4_CONFIRMATORY_VALIDATION.md`
- `reports/m4/M4_SPECULATION_MECHANISM_DIAGNOSIS.md`
- `paper/notes/VERIFICATION_AMORTIZATION_FRAMEWORK.md`

### Windows / Core Ultra 9 275HX + RTX 5070 Ti Laptop

Safe established evidence includes:
- CPU-assisted and exact same-GPU controls are negative on the frozen HumanEval follow-up;
- fast CUDA two-token target batching is near one target-decode cost but is correctness-blocked on a stable frozen case;
- serialized `ubatch=1` restores exactness on the tested CUDA control but raises verification cost to roughly 2.14--2.43 single-token decodes;
- HumanEval exact controls: CPU-to-RTX 0.404x, RTX-to-RTX 0.650x;
- power/energy measurements use separate NVIDIA board and Intel CPU-package domains and must not be summed as whole-system energy;
- the GPU is **RTX 5070 Ti Laptop**, not a desktop RTX 5070 Ti.

Primary writing sources:
- `reports/5070ti/FINAL_5070TI_PLATFORM_REPORT.md`
- `reports/5070ti/HUMANEVAL_LLAMA_REPLICATION.md`
- `reports/5070ti/WINDOWS_VERIFICATION_MECHANISM_CONTROLS.md`
- `reports/5070ti/CUDA_DIVERGENCE_NUMERICAL_DIAGNOSIS.md`

### Arc B570 / Vulkan

Safe established evidence includes:
- fast Vulkan speculative path is not universally token-exact on the frozen HumanEval30 set;
- fast diagnostic path: 45/90 exact pairs and 15/30 wholly exact prompts;
- serialized fallback improves exactness but remains non-universal on the full set: 60/90 exact pairs and 20/30 wholly exact prompts;
- serialized verification factor is approximately 1.98--1.99;
- overall serialized timing is diagnostic only, about 0.309x geometric-mean speedup with 0/30 prompts faster;
- Arc-board energy efficiency is worse than baseline;
- B570 archive repair was completed and the platform is closed.

Primary writing sources:
- `reports/b570/B570_EXACT_FALLBACK_VALIDATION.md`
- `reports/b570/B570_FAST_VS_EXACT_FALLBACK.md`
- `reports/b570/B570_CROSS_PLATFORM_SUMMARY.md`
- `reports/b570/B570_PLATFORM_CLOSEOUT.md`

## 358H evidence currently available but not yet final

### Merged environment qualification

`reports/358h/358H_ENVIRONMENT_QUALIFICATION.md` on `main` establishes:
- explicit CPU/GPU/NPU OpenVINO execution qualification;
- frozen Qwen3-0.6B OpenVINO representation and provenance limitation;
- explicit B390/NPU driver/runtime metadata;
- no formal Phase-1 result in that merged qualification document.

### Later branch evidence

The active 358H branch records:
- Phase 1 CPU/NPU draft characterization complete;
- Phase 2 target baseline / exact verification / threshold analysis complete;
- CPU and NPU classified BORDERLINE;
- custom heterogeneous runner qualified;
- runner records end-to-end timing, draft/replay aggregate time, target verification, residual, proposals, accepted tokens, committed work `C`, token IDs, and per-round state positions;
- runner uses full committed-prefix replay for the OpenVINO draft path;
- formal Phase-3 HumanEval data had not started at the checked branch head.

The qualified-runner report states:
- target: llama.cpp b10839, Vulkan0, persistent target KV;
- draft: same frozen OpenVINO INT4 IR on explicit CPU or NPU;
- full committed-prefix replay remains inside `draft_time`;
- semantics/reference/state tests pass;
- `formal_phase3_data_seen_before_runner_freeze = false`.

The frozen campaign-driver record specifies:
- small gate tasks: 6 tasks x 3 repetitions;
- full HumanEval30 set: 30 tasks x 3 repetitions;
- conditions: target baseline, CPU draft k=2, NPU draft k=2;
- output cap 128;
- k=2;
- no runner instrumentation amendment because replay-only vs proposal-only timing cannot be separated without changing inference; end-to-end timing remains authoritative.

## Evidence gaps that must remain visible in the paper

1. **358H Phase 3 is not final yet.**
   Do not write a final end-to-end CPU/NPU conclusion until the formal campaign completes.

2. **M4 corrected synthetic ceiling was not completed under the preregistered design.**
   The older exploratory synthetic run must not be relabeled as that preregistered experiment.

3. **HumanEval generated code was not functionally executed in the existing cross-platform exactness studies.**
   "Exact" means token-ID equality, not task correctness.

4. **Energy boundaries differ across platforms.**
   M4 package, NVIDIA board, Intel CPU package, and Arc-board measurements are not one calibrated common power domain.

5. **Cross-platform causal attribution is limited.**
   Runtime, backend, hardware architecture, memory organization, quantization/execution details, and scheduling differ. Do not claim unified memory, CUDA, Vulkan, or any one kernel is the sole cause.

6. **358H model-source provenance has a documented reconstruction limitation.**
   Preserve the repository's `STRONGLY_SUPPORTED` wording; do not upgrade it to exact proven source identity.

## Drafting readiness

Ready now:
- Introduction
- Background / speculative decoding mechanics
- Correctness contract
- Verification-amortization model
- Experimental methodology
- M4 results
- RTX 5070 Ti Laptop results
- B570 results
- Most related discussion on correctness-constrained execution paths

Wait for 358H Phase 3 before freezing:
- final title
- abstract
- 358H results subsection
- cross-platform final table
- discussion emphasis
- conclusion
- headline contribution count/order
