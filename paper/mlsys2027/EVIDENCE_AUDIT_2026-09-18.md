# Evidence audit for MLSys 2027 drafting

Audit date: **2026-09-18**.

This file is a compact status audit for the paper workspace. The detailed scientific ledger and decision log are now maintained in `PAPER_FRAMEWORK_HANDOFF.md`, which is authoritative if this file and the handoff ever diverge.

## Repository state checked

Current `main` head:

`8de9642b3d27830ec182f3571974069d5b88d405`

This is the merge commit for PR #12, `358H: close Phase-3 heterogeneous validation`.

The four hardware campaigns are now scientifically closed and merged.

## Completed-platform evidence suitable for drafting

### M4 / llama.cpp Metal

Safe established evidence includes:
- exact tested llama.cpp/Metal verification cells;
- representative frozen Spec-Bench 24Q: 0.842x [0.809, 0.877], 72/72 exact;
- preregistered HumanEval30 fixed-k=2: 1.387x [1.351, 1.422], 30/30 prompts faster, 90/90 exact;
- fixed-k=2 package energy neutral within uncertainty;
- workload dependence must remain explicit.

Primary sources:
- `reports/m4/M4_HUMANEVAL_CODE_CONDITIONED.md`
- `reports/m4/M4_CONFIRMATORY_VALIDATION.md`
- `reports/m4/M4_SPECULATION_MECHANISM_DIAGNOSIS.md`
- `reports/m4/M4_EXPERIMENT_INDEX.md`

### Windows / Core Ultra 9 275HX + RTX 5070 Ti Laptop

Safe established evidence includes:
- exact serialized HumanEval controls are negative: CPU→RTX 0.404x [0.390, 0.418], RTX→RTX 0.650x [0.629, 0.673];
- fast CUDA two-token target batching is near one target-decode cost but is correctness-blocked in the frozen replication;
- serialized `ubatch=1` restores exactness in the tested control and raises verification cost to roughly 2.14–2.43 target decodes;
- component energy domains are separate and are not whole-system energy;
- always preserve the **RTX 5070 Ti Laptop** designation.

Primary sources:
- `reports/5070ti/FINAL_5070TI_PLATFORM_REPORT.md`
- `reports/5070ti/HUMANEVAL_LLAMA_REPLICATION.md`
- `reports/5070ti/WINDOWS_VERIFICATION_MECHANISM_CONTROLS.md`
- `reports/5070ti/CUDA_DIVERGENCE_NUMERICAL_DIAGNOSIS.md`

### Arc B570 / Vulkan

Safe established evidence includes:
- fast path is correctness-blocked: 45/90 exact pairs;
- serialized fallback improves exactness but remains non-universal: 60/90 exact pairs, 20/30 exact prompts;
- serialized verification factor is approximately 1.98–1.99;
- serialized timing is diagnostic only: 0.3087x [0.2927, 0.3246], 0/30 faster;
- board-energy efficiency is worse than baseline;
- no tested B570 path is a correctness-admissible optimization result.

Terminology rule:
- do not use historical `V2_exact` wording as a global paper claim for the serialized fallback;
- prefer `V2_serialized` / serialized fallback verification factor unless a bounded exact subset is explicitly named.

Primary sources:
- `reports/b570/B570_EXACT_FALLBACK_VALIDATION.md`
- `reports/b570/B570_FAST_VS_EXACT_FALLBACK.md`
- `reports/b570/B570_PLATFORM_CLOSEOUT.md`

### Core Ultra X7 358H

Phase 3 is now final and merged.

Safe established evidence includes:
- Stage-A gate: CPU 18/18 exact; NPU 18/18 exact;
- HumanEval30: CPU 0.734x [0.693, 0.771], 90/90 exact, 0/30 faster;
- HumanEval30: NPU 0.352x [0.333, 0.369], 90/90 exact, 0/30 faster;
- CPU acceptance 75.31%, C=2.463; NPU acceptance 75.13%, C=2.458;
- CPU time dominated by target verification (87.34%);
- NPU time dominated by synchronous full-prefix replay plus proposal (58.35%);
- residual Python/orchestration is ~0.02–0.04%, not the primary mechanism;
- end-to-end energy is not claimed;
- reconstructed source remains `STRONGLY_SUPPORTED`, not proven exact historical identity;
- 34/34 archive manifest entries were verified before merge.

Primary sources:
- `reports/358h/358H_PHASE3_END_TO_END_VALIDATION.md`
- `reports/358h/358H_PLATFORM_CLOSEOUT.md`
- `reports/358h/358H_PROVENANCE_AMENDMENT.md`
- `reports/358h/358H_REPOSITORY_CLOSEOUT_AUDIT.md`

## Evidence gaps that must remain visible

1. M4 corrected synthetic ceiling was not completed under the preregistered design.
2. HumanEval generated code was not functionally executed.
3. Energy boundaries differ across platforms.
4. Cross-platform causal attribution is limited because hardware and software stacks change together.
5. 358H source reconstruction has a documented provenance limitation.
6. Report-level traceability is established, but platform-specific rounds must still audit processed analysis, scripts, preregistration, and raw artifacts for headline claims.

## Drafting readiness

Scientifically draftable now:
- Introduction framing;
- correctness contract;
- minimal profitability model;
- methodology;
- all four platform result sections;
- cross-platform regime table;
- limitations.

Still not frozen:
- final title;
- abstract;
- final contribution order/count;
- final discussion emphasis;
- conclusion;
- whether a new runtime/software contribution is necessary.

Do not copy numbers from chat history into the manuscript without checking repository evidence and the handoff ledger.
