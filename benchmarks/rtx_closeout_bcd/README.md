# RTX B/C/D finite closeout

Widening native speculative calls can change the past state and lose the original scalar reference even when a matched target control passes. This study continues the manuscript and Phase 1/2 diagnosis with prospective task validation, width/length qualification, natural-state crossings, persistent requests, and a bounded fixed-microbatch amendment. The final result is a finite configuration boundary with measured costs.

## Results

- **B:** all 24 locked, previously unused sanitized MBPP tasks match repeated paid scalar references under all four conditions (384 requests + 16 warmups). Target scopes / matched target: 1.1692x generation / 1.0351x whole request. Target scopes / all scopes: 1.0154x generation / 1.0304x whole request, below the predeclared 3% extra-generation gate.
- **C:** k1/UB2 and k3/UB4 qualify at all three requested caps (128/256/512). MBPP/229 fails under k5/UB6 and k7/UB8 in every cap/repetition; all failures and costs remain. The topology probe HumanEval/18 also fails its original reference under UB6/8 in target-alone and speculative modes. Actual long reference lengths reach 261, not 512 tokens.
- **Natural state crossing:** at 47 committed tokens of MBPP/229, two genuine donor states are crossed with two current UB6 query layouts. Both same-path shams per boundary pass. Swapping state changes the local EOS decision; swapping the current layout changes floating-point scores without changing that decision. This is local state evidence, not a unique operator or full-continuation proof.
- **D:** the original k3/UB4 profile matches all 24 task references in two resident cycles in both capture-enabled reset qualification and separate timing runs. 1.1812x generation / 1.0385x whole request. D does not test higher k.
- **Original optional C2/C3:** skipped by their frozen output gates. More constrained scopes failed to repair both selected wider cases. No failed outputs were replaced.

## Final parameter isolation

Original C changes k and UB together. C4 was declared after primary B/C/D and before all C4 forwards: fix numerical UB=4 and target scopes, test k3/5/7 on all 24 B tasks plus four old probes, two repeats. All three profiles pass complete-array/EOS qualification; actual k7 caller batches reach 8 while occupied microqueries remain 1–4 and constrained multiquery paths stay active. Capture costs are excluded.

Highest output-qualified k=7 was frozen before 448 independent balanced cost requests and 16 warmups. The same 28 pilot tasks are reused; no held-out or new unused-task claim.

| Comparison | Costs | Full-reference qualified |
|---|---|---|
| wider_speculation / anchor_speculation | 0.8294x generation / 0.8899x whole request | True |
| wider_speculation / matched_target | 0.9974x generation / 0.9504x whole request | True |
| anchor_speculation / matched_target | 1.2025x generation / 1.0680x whole request | True |
| wider_speculation / ordinary_wider | 0.9833x generation / 0.9577x whole request | False |

Predeclared extra-generation gate versus k3 (full reference, >=1.03x generation, >=1x whole request, >=3/4 faster repetitions): **FAIL**.

Final independent 11-task long validation pays scalar, matched target, and selected speculation at caps 256/512 with two repeats (132 + 6 warmups).

- cap256: qualification {'scalar_reference': True, 'matched_target': True, 'wider_speculation': True}; 1.0001x generation / 0.9649x whole request; cost qualified True.
- cap512: qualification {'scalar_reference': True, 'matched_target': True, 'wider_speculation': True}; 0.9715x generation / 0.9340x whole request; cost qualified True.

No further RTX profile search follows this bounded amendment. Failed qualifications and failed speed gates are retained.

## Evidence and reproducibility

Post-audit PASS: 2318 complete generations (2212 nonwarm + 106 warmups), plus 8 paid auxiliary target decodes. The two bound models, 33 published DLLs, prior private/native sources and binaries, and exact request-runner identities remain verified. One offline C summary key-set error was corrected without any model rerun; its record is retained.

Initial protocol/inputs were frozen before new B inference in private commit 7b8c6fb. C4 is explicitly a later bounded amendment, never a replacement of original C negatives. Public pre-output commits: 4c34dfc (C4 pilot) and 0ba7912 (selected C4 main/long manifest). Protocol, inputs and source identities retain their original hashes.

This PR adds only `benchmarks/rtx_closeout_bcd/` and leaves the manuscript and previous studies to the ongoing integration. `results/` and `tables/` contain derived summaries; the local full archive contains raw outputs, traces, exact private native source/binaries, corpus identity, frozen references and Git history. No weights, runtime binaries, raw telemetry, native token arrays or float dumps are committed here. Public B_INPUTS contains descriptions/prompts and zero-forward vocabulary tokenization, never solutions/tests.

Review artifacts: [Chinese report](REPORT.md), [closeout summary](results/CLOSEOUT_SUMMARY.json), [width/length](figures/width-length.svg), [qualified costs](figures/costs.svg), [state crossing](figures/state-crossing.svg).

Rehydrate the delivered CAS ZIP into a **new** directory using the included `rehydrate.py`; verify dependencies separately. Configure `HETEROSPEC_PHASE1_ROOT`, `HETEROSPEC_PHASE2_ROOT`, `HETEROSPEC_ASSET_ROOT`, and `HETEROSPEC_RTX_STUDY_ROOT`. `restore_runtime.py` checks and places the bound private executables and installed published DLLs. Python 3.11 is used; NumPy/Matplotlib are needed only for score analysis/figures. Models, the exact bound released runtime, and previous Phase 1/2 archives must already be available. The public code alone is not a portable CUDA rebuild.

Archived experiment runners intentionally refuse to overwrite run directories and require frozen clean Git heads. Evidence review/rehydration is separate from new model reruns: create a new checkout from `generated/FROZEN_HISTORY.bundle`, configure its dependencies, and preregister new output destinations before inference. Do not rerun exposure selection after these tasks have been executed.

The RTX closeout is scoped to this GPU, model pair, runtime, greedy seed, FA-off, single sequence, and finite tasks/configurations. It does not claim functional task correctness, universal losslessness, globally optimal k/scopes, unique operator causality, production throughput or cross-platform speed. B570 is the next separate platform study; its paid native reference and required scopes must be identified independently.
