# Repository status

Status revalidated **2026-09-19** against `main` at `5c8cc30284de2345d2056199cdeeffcad3da5599`, the merge of PR #13 (`Paper: complete MLSys 2027 scientific audit (Rounds 1–12)`).

The authoritative MLSys 2027 scientific framework handoff is `paper/mlsys2027/PAPER_FRAMEWORK_HANDOFF.md`.

## Completed and merged

- Windows Core Ultra 9 275HX + **RTX 5070 Ti Laptop** platform closure, including the 60Q pilot, root-cause controls, target-size/capacity work, component-power study, matched HumanEval replication, exact-verification microbenchmark, CUDA divergence diagnosis, and paper-critical evidence.
- MacBook Air M4 platform closure, including portability/correctness gates, the 12Q decision study, mechanism controls, frozen 24Q representative confirmation, and preregistered 30-prompt HumanEval code-conditioned study.
- Arc B570 Vulkan backend-control closure, including formal correctness failure, HumanEval30 diagnostics, the single serialized fallback validation, verification measurements, board-energy data, and paper-critical provenance.
- Core Ultra X7 358H Phase 0–3 closure, including source/provenance qualification, explicit CPU/GPU/NPU binding, isolated CPU/NPU draft characterization, Phase-2 eligibility analysis, and Phase-3 end-to-end HumanEval30 validation.
- Publication-sized evidence archives for M4 HumanEval, Windows HumanEval/verification/divergence, B570 backend-control evidence, and the byte-complete 358H Phase-3 recovery bundle.
- MLSys 2027 scientific audit Rounds 1–12, including independent headline recomputation, statistics/CI review, correctness-contract audit, energy-boundary audit, unified accounting correction, related-work positioning, and adversarial-review audit.

No experiment data, preregistration, failed run, or historical result report was changed by the paper audit.

## Final platform classes

### MacBook Air M4 / llama.cpp Metal

- Representative frozen Spec-Bench 24Q: **0.842x [0.809, 0.877]**, 72/72 exact.
- Separately preregistered HumanEval30 fixed-k=2: **1.387x [1.351, 1.422]**, 90/90 exact, 30/30 prompts faster.
- Fixed-k2 HumanEval package energy is **neutral within uncertainty**: efficiency ratio 1.013x [0.990, 1.034].
- Final interpretation: a workload-conditioned exact profitable regime exists; the representative workload did not generalize it.

### Core Ultra 9 275HX + RTX 5070 Ti Laptop / CUDA

- Exact serialized HumanEval controls: CPU→RTX **0.404x [0.390, 0.418]**, RTX→RTX **0.650x [0.629, 0.673]**, both 90/90 exact and 0/30 prompts faster.
- Batched `ubatch=2` target-forward `V_2^micro` is approximately 0.98–1.01 but is correctness-blocked in the frozen replication.
- Serialized `ubatch=1` exact-control `V_2^micro` is approximately 2.14–2.43.
- Final interpretation: correctness-admissible tested paths are negative; the numerical divergence is configuration/path bounded, not a universal CUDA claim.

### Core i5-13400 + Arc B570 / Vulkan

- Fast path: correctness-blocked, 45/90 exact pairs.
- Serialized fallback: 60/90 exact pairs, 20/30 exact prompts; not universally exact; diagnostic speedup **0.3087x [0.2927, 0.3246]**.
- Serialized target-forward proxy is approximately 1.98–1.99.
- Final interpretation: no tested B570 path qualifies as a correctness-admissible optimization result.
- Paper-facing terminology: `V2_serialized` / serialized `V_2^micro`, not global `V2_exact`.

### Core Ultra X7 358H + Arc B390 target + CPU/NPU OpenVINO draft

- CPU: **0.734x [0.693, 0.771]**, 90/90 exact, 0/30 faster.
- NPU: **0.352x [0.333, 0.369]**, 90/90 exact, 0/30 faster.
- CPU time is dominated by complete target-side verification work (87.34%).
- NPU time is dominated by synchronous full-prefix replay plus proposal in the current state interface (58.35%).
- End-to-end Phase-3 energy is not claimed.
- Final class: **CORRECTNESS-ADMISSIBLE / NOT PROFITABLE — SCIENTIFIC EXECUTION CLOSED**.

## Paper scientific status

- Hardware study: **CLOSED**.
- Scientific audit Rounds 1–12: **COMPLETE and merged**.
- Final scientific thesis and contribution ordering: **FROZEN for drafting**, subject only to explicit revision if later evidence contradicts the ledger.
- Exact paper title: **not frozen**.
- Runtime/software co-design: future work unless separately scoped and preregistered; no runtime intervention is a current measured contribution.
- Manuscript/figure production: next paper-production phase, governed by `PAPER_FRAMEWORK_HANDOFF.md`.

Current thesis direction:

> The tested systems become profitable only when the execution path that survives the correctness contract and the realized stateful runtime costs fit within the committed progress of a speculative round. The paper contribution is a correctness-admissible, realized-cost cross-runtime characterization—not a generic claim that high acceptance, heterogeneous hardware, or one backend determines success.

## Deliberately incomplete / non-claims

- The M4 HumanEval preregistration's corrected synthetic ceiling has no completion artifact matching its frozen design. The earlier exploratory synthetic crossover is not a substitute.
- HumanEval generated code was not functionally executed; “exact” means paired greedy generated-token ID equality.
- Energy sensor boundaries differ materially across platforms and are not one common calibrated domain.
- M4 unified memory is not isolated as a causal factor.
- The CUDA batch-shape argmax flip is not a universal CUDA failure claim.
- B570 conclusions are frozen backend/configuration results.
- The 358H NPU result characterizes the current OpenVINO/state interface; it is not evidence that NPUs are generally unsuitable.
- The 358H reconstructed source remains `STRONGLY_SUPPORTED`, not proven exact historical source identity.

## Reproducibility notes

- M4 has the strongest raw-to-report provenance among the headline studies.
- Windows HumanEval/mechanism headline values are reproducible from committed derived pair tables and mechanism captures, but some authoritative per-run JSON logs were historically local/ignored; raw Git provenance is therefore weaker than M4/B570/358H.
- B570 exact-fallback bootstrap CIs reproduce bit-for-bit only when the retained first-seen execution order is replayed; sorting the exported prompt CSV changes finite fixed-seed bootstrap endpoints slightly.
- `analysis/358h_phase3_prompt_level.csv` is a historical blocked-preflight, header-only scaffold. It is **not** the final Phase-3 dataset. Use `analysis/358h_phase3_prompt_summary.csv`, `analysis/358h_phase3_rounds.csv`, `analysis/358h_phase3_decomposition.csv`, and `analysis/358h_phase3_summary.json` for final Phase-3 analysis.

## Remaining before public release / submission

- Choose and install a real license; `LICENSE_PLACEHOLDER.md` is not a release license.
- Finalize authors and identifiers in `CITATION.cff`.
- Decide whether local-path provenance fields need redaction or documented acceptance for a public artifact.
- Use the official MLSys format and perform final double-blind/privacy review on the exact submission candidate.
- Re-run security, large-file, link, generated-artifact, and source-consistency checks on the exact release candidate.
- Add paper/arXiv, DOI, and archival-release metadata only when they exist.

## Branch policy

The four completed hardware campaigns and the Rounds 1–12 audit are merged to `main`. The 2026-09-19 terminal revalidation is maintained on `paper/final-audit-20260919` until reviewed. Any future optimization/runtime study must use a new branch and a new preregistration rather than extending a closed campaign post hoc.
