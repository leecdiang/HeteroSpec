# Repository status

Status as of 2026-09-18 on `main` at `8de9642b3d27830ec182f3571974069d5b88d405`, after merge of PR #12 (`358H: close Phase-3 heterogeneous validation`).

The authoritative MLSys 2027 scientific framework handoff is `paper/mlsys2027/PAPER_FRAMEWORK_HANDOFF.md`.

## Completed and merged

- Windows Core Ultra 9 275HX + **RTX 5070 Ti Laptop** platform closure, including the 60Q pilot, root-cause controls, target-size/capacity work, component power study, matched HumanEval replication, exact-verification microbenchmark, CUDA divergence diagnosis, and paper-critical raw provenance.
- MacBook Air M4 platform closure, including portability/correctness gates, the 12Q decision study, mechanism controls, the frozen 24Q representative confirmation, and the preregistered 30-prompt HumanEval code-conditioned study.
- Arc B570 Vulkan backend-control closure, including formal correctness failure, HumanEval30 diagnostics, the single serialized fallback validation, verification measurements, board-energy data, and paper-critical provenance.
- Core Ultra X7 358H Phase 0–3 closure, including source/provenance qualification, explicit CPU/GPU/NPU binding, isolated CPU/NPU draft characterization, Phase-2 threshold prediction, and Phase-3 end-to-end HumanEval30 validation.
- Publication-sized evidence archives for M4 HumanEval, Windows HumanEval/verification/divergence, B570 backend-control evidence, and the byte-complete 358H Phase-3 recovery bundle.
- Repository-wide documentation consolidation, including the verification-amortization framework and cross-platform mechanism interpretation.

## Final platform classes

### MacBook Air M4 / Metal

- Representative frozen Spec-Bench 24Q: 0.842x [0.809, 0.877], 72/72 exact.
- Separately preregistered HumanEval30 fixed-k=2: 1.387x [1.351, 1.422], 90/90 exact, 30/30 prompts faster.
- Final interpretation: workload-conditioned exact profitable regime exists; representative workload did not generalize it.

### Core Ultra 9 275HX + RTX 5070 Ti Laptop / CUDA

- Exact HumanEval controls: CPU→RTX 0.404x [0.390, 0.418], RTX→RTX 0.650x [0.629, 0.673], both 90/90 exact.
- Fast batched CUDA verification is near one target decode but is correctness-blocked in the frozen replication; exact serialized verification costs roughly 2.14–2.43 target decodes.
- Final interpretation: correctness-admissible tested paths are negative.

### Core i5-13400 + Arc B570 / Vulkan

- Fast path: correctness-blocked, 45/90 exact pairs.
- Serialized fallback: 60/90 exact pairs, 20/30 exact prompts; not universally exact; diagnostic speedup 0.3087x.
- Final interpretation: no tested B570 path qualifies as a correctness-admissible optimization result.
- Paper-facing terminology should avoid treating the serialized verification proxy as globally exact.

### Core Ultra X7 358H + Arc B390 target + CPU/NPU OpenVINO draft

- CPU: 0.734x [0.693, 0.771], 90/90 exact, 0/30 faster.
- NPU: 0.352x [0.333, 0.369], 90/90 exact, 0/30 faster.
- CPU time is dominated by target verification; NPU time is dominated by full-prefix replay plus proposal in the current state interface.
- End-to-end energy is not claimed.
- Final class: **CORRECTNESS-ADMISSIBLE / NOT PROFITABLE — SCIENTIFIC EXECUTION CLOSED**.

## Pending or deliberately incomplete

- The M4 HumanEval preregistration's **corrected synthetic ceiling** has no completion artifact matching its frozen design. The earlier exploratory synthetic crossover is not a substitute.
- HumanEval generated code was not functionally executed; “exact” means paired greedy token-ID equality.
- Final paper thesis/title/contribution ordering remains under audit.
- Runtime/software co-design is future work unless separately scoped and preregistered.

## Data and interpretation boundaries

- Energy sensor boundaries differ by platform and must not be treated as one common calibrated domain.
- M4 unified memory is not isolated as a causal factor.
- The frozen CUDA divergence evidence is not a universal CUDA failure claim.
- B570 conclusions are backend/configuration bounded.
- The 358H NPU result characterizes the current OpenVINO/state interface; it is not evidence that NPUs are generally unsuitable.
- The 358H reconstructed source remains `STRONGLY_SUPPORTED`, not proven exact historical source identity.

## Remaining before public release

- Choose and install a real license; `LICENSE_PLACEHOLDER.md` is not a release license.
- Finalize authors and identifiers in `CITATION.cff`.
- Decide whether local-path provenance fields need redaction or documented acceptance for the public archive.
- Run security, large-file, link, and generated-artifact checks again on the exact release candidate.
- Add paper/arXiv, DOI, and archival-release metadata only when they exist.

## Remote and branch policy

Private GitHub repository: `https://github.com/leecdiang/HeteroSpec`.

The four completed hardware campaigns are merged to `main`. Any follow-up optimization/runtime study must use a new branch and new preregistration rather than extending a closed campaign.
