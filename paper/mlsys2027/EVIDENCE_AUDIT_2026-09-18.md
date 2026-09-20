# Evidence audit for MLSys 2027 drafting

Original audit date: **2026-09-18**.  
Terminal revalidation: **2026-09-19**.

This file is a compact status audit. The authoritative scientific ledger, claim taxonomy, decision log, reviewer-risk register, and final audit log are maintained in `PAPER_FRAMEWORK_HANDOFF.md`; that handoff controls if this compact note ever diverges.

## Repository state checked

Current audited `main` baseline:

`5c8cc30284de2345d2056199cdeeffcad3da5599`

This is the merge of PR #13, `Paper: complete MLSys 2027 scientific audit (Rounds 1–12)`. PR #12, `358H: close Phase-3 heterogeneous validation`, is already contained in this history.

A compare from the 358H merge (`8de9642b3d27830ec182f3571974069d5b88d405`) to the current baseline shows that the paper audit changed only paper/status documentation; experiment data, analysis inputs, scripts used by the frozen experiments, preregistrations, and raw artifacts were not changed to fit the paper story.

The four hardware campaigns are scientifically closed.

## Completed-platform evidence suitable for drafting

### M4 / llama.cpp Metal

Safe evidence:
- representative frozen Spec-Bench 24Q: **0.842x [0.809, 0.877]**, 72/72 exact, 1/24 prompts faster;
- separately preregistered HumanEval30 fixed-k=2: **1.387x [1.351, 1.422]**, 30/30 prompts faster, 90/90 exact;
- HumanEval fixed-k2 package-efficiency point estimate 1.013x with CI [0.990, 1.034]: **energy-neutral within uncertainty**;
- registered `p_min=0.9` secondary energy efficiency 1.041x [1.018, 1.065];
- workload dependence must remain explicit;
- corrected synthetic ceiling remains unexecuted.

Primary sources:
- `reports/m4/M4_HUMANEVAL_CODE_CONDITIONED.md`
- `reports/m4/M4_CONFIRMATORY_VALIDATION.md`
- `reports/m4/M4_SPECULATION_MECHANISM_DIAGNOSIS.md`
- `reports/m4/M4_EXPERIMENT_INDEX.md`
- `analysis/m4_humaneval_summary.json`
- `analysis/m4_humaneval_prompt_summary.csv`
- `analysis/m4_confirmatory_summary.json`
- `analysis/m4_confirmatory_prompt_summary.csv`

Terminal revalidation independently replayed the frozen prompt-bootstrap implementations and reproduced the headline M4 point estimates and CIs.

### Windows / Core Ultra 9 275HX + RTX 5070 Ti Laptop

Safe evidence:
- exact serialized HumanEval controls are negative: CPU→RTX **0.404x [0.390, 0.418]**, RTX→RTX **0.650x [0.629, 0.673]**;
- both exact controls are 90/90 token-exact and 0/30 prompts faster;
- fast CUDA `ubatch=2` target-forward `V_2^micro` is approximately **1.009 at depth 0** and **0.983 at depth 256**, but the path is correctness-blocked in the frozen HumanEval replication;
- serialized `ubatch=1` exact-control `V_2^micro` is approximately **2.431** and **2.137** at the same depths;
- HumanEval/106 reproduces the same first divergence in 3/3 runs; baseline/serialized choose token 2790 while batched execution chooses token 2629;
- at the shared prefix, `score(2790)-score(2629)` flips from +0.080948 to -0.126457 under the batched path;
- component energy domains are separate and are not whole-system energy;
- always preserve the **RTX 5070 Ti Laptop** designation.

Primary sources:
- `reports/5070ti/FINAL_5070TI_PLATFORM_REPORT.md`
- `reports/5070ti/HUMANEVAL_LLAMA_REPLICATION.md`
- `reports/5070ti/windows_humaneval_summary.json`
- `reports/5070ti/WINDOWS_EXACT_VERIFICATION_COST.csv`
- `reports/5070ti/WINDOWS_CUDA_DIVERGENCE_MINREPRO.csv`
- `reports/5070ti/CUDA_DIVERGENCE_LOGITS.csv`

Raw-provenance limitation: some authoritative per-run HumanEval/mechanism JSON logs were historically local/ignored. The committed pair table, summary, manifests, verification-cost controls, and numerical capture support headline recomputation, but raw Git provenance is weaker than M4/B570/358H.

### Arc B570 / Vulkan

Safe evidence:
- formal fast path fails correctness;
- later diagnostic fast path: **45/90 exact pairs**;
- serialized fallback: **60/90 exact pairs**, 20/30 wholly exact prompts; not universally exact;
- serialized target-forward `V_2^micro`: approximately **1.983 / 1.992** at contexts 512 / 2048;
- serialized timing remains diagnostic: **0.3087x [0.2927, 0.3246]**, 0/30 prompts faster;
- Arc-board efficiency ratio: **0.3023x [0.2846, 0.3202]**; board boundary only;
- no tested B570 path is a correctness-admissible optimization result.

Terminology rule:
- historical files may retain the field name `V2_exact` as provenance;
- paper-facing text uses **serialized `V_2^micro` / `V2_serialized`**, because serialization is not a correctness proof.

Primary sources:
- `reports/b570/B570_EXACT_FALLBACK_VALIDATION.md`
- `reports/b570/B570_FAST_VS_EXACT_FALLBACK.md`
- `reports/b570/B570_PLATFORM_CLOSEOUT.md`
- `analysis/b570_exact_fallback_summary.json`
- `analysis/b570_exact_fallback_prompt_summary.csv`

Terminal revalidation independently reproduced the global prompt GM, exact-prompt count, exact-subset GM, and board-energy ratio from the prompt summary. The prior statistical audit reproduced the archived finite-bootstrap CIs bit-for-bit using the retained first-seen execution order.

### Core Ultra X7 358H + Arc B390 target + CPU/NPU OpenVINO draft

Safe evidence:
- Stage-A gate: CPU 18/18 exact; NPU 18/18 exact;
- HumanEval30 CPU: **0.734x [0.693, 0.771]**, 90/90 exact, 0/30 faster;
- HumanEval30 NPU: **0.352x [0.333, 0.369]**, 90/90 exact, 0/30 faster;
- CPU acceptance 75.31%, direct committed progress `C=2.463`;
- NPU acceptance 75.13%, direct committed progress `C=2.458`;
- CPU measured speculative time: 12.63% replay+proposal, 87.34% target-side work, ~0.04% residual;
- NPU measured speculative time: 58.35% replay+proposal, 41.63% target-side work, ~0.02% residual;
- each OpenVINO proposal call receives the complete committed prefix, so replay/reconstruction plus proposal is genuinely part of realized `T_d(real)`;
- replay-only and proposal-only are not separable without changing the frozen execution;
- end-to-end Phase-3 energy is not claimed;
- reconstructed draft source remains `STRONGLY_SUPPORTED`, not proven exact historical identity;
- 34/34 archive manifest entries were validated before the Phase-3 merge.

Primary sources:
- `reports/358h/358H_PHASE3_END_TO_END_VALIDATION.md`
- `reports/358h/358H_PLATFORM_CLOSEOUT.md`
- `reports/358h/358H_PROVENANCE_AMENDMENT.md`
- `reports/358h/358H_REPOSITORY_CLOSEOUT_AUDIT.md`
- `analysis/358h_phase3_summary.json`
- `analysis/358h_phase3_prompt_summary.csv`
- `analysis/358h_phase3_rounds.csv`
- `analysis/358h_phase3_decomposition.csv`
- `scripts/platform/358h/analyze_phase3_campaign.py`
- `scripts/platform/358h/phase3_heterogeneous_runner.py`

Important non-authoritative file: `analysis/358h_phase3_prompt_level.csv` is a historical blocked-preflight, header-only scaffold created before the successful Phase-3 campaign. It is not the final analysis source and must not be used for paper figures/tables.

## Unified accounting status

The original candidate model was tightened during the audit. The final paper must distinguish complete realized target-side round cost from a target-forward batching microbenchmark:

```text
S_round = T_b*C / [T_d(real) + T_target,round(real) + T_x]
        = C / [D_real + R_target + X]
```

with break-even:

```text
C > D_real + R_target + X
```

Separately:

```text
V_k^micro(n,e) = T_target_forward(k,n,e) / T_target_decode(1,n)
```

`V_k^micro` is a mechanism proxy. It is not automatically the complete `R_target` of an end-to-end speculative round.

358H directly validates the realized accounting at the ratio-of-total-times level:
- CPU: `C/(D_real+R_target+X) = 0.7227`, equal to aggregate baseline/speculative total-time ratio;
- NPU: `0.3477`, likewise equal to the aggregate ratio.

These aggregate ratios intentionally differ from the preregistered prompt-level geometric-mean headline speedups 0.734x / 0.352x because the estimands differ.

## Statistical boundaries

No headline pseudoreplication was found. Prompt is the bootstrap unit after reducing paired repetitions within prompt, but frozen estimators differ:

- M4 HumanEval: within-prompt geometric mean; 100,000 Python bootstrap resamples, seed 20260910.
- M4 24Q: within-prompt geometric mean; 10,000 Python bootstrap resamples, seed 20260907.
- RTX HumanEval: within-prompt geometric mean; 10,000 Python bootstrap resamples, seed 20260910.
- B570 fallback: prompt geometric mean; 10,000 Python bootstrap resamples, seed 20260910; deterministic input order is required for bit-level finite-bootstrap reproduction.
- 358H Phase3: within-prompt median paired speedup, then prompt geometric mean; 10,000 NumPy bootstrap resamples, seed 20260919.

Do not homogenize these frozen estimators post hoc. The reported CIs primarily reflect prompt-sampling uncertainty conditional on each campaign, not full between-session/thermal/runtime-state uncertainty.

## Evidence gaps / limitations that must remain visible

1. M4 corrected synthetic ceiling was not completed under the preregistered design.
2. HumanEval generated code was not functionally executed.
3. Energy boundaries differ across platforms.
4. Cross-platform causal attribution is limited because hardware and software stacks change together.
5. 358H source reconstruction has a documented provenance limitation.
6. Windows raw per-run Git provenance is incomplete relative to M4/B570/358H.
7. The strict token-exact contract is a deliberate study contract; approximate-quality speculative decoding is a different research question.
8. Only four consumer systems and a narrow model/runtime family are covered; no universal hardware/model law is claimed.

## Drafting readiness after terminal revalidation

Scientifically ready for drafting:
- Introduction framing;
- correctness contract;
- realized-cost accounting and `V_k^micro` distinction;
- methodology;
- all four platform result sections;
- cross-platform regime table;
- related-work positioning;
- limitations;
- discussion/conclusion consistent with the frozen thesis.

Frozen:
- scientific thesis;
- contribution ordering;
- evidence classes;
- correctness terminology;
- energy boundaries;
- statistical headline values.

Not frozen:
- exact paper title wording;
- prose style;
- final visual design and panel layout;
- any future runtime/software intervention.

Do not copy a number from chat history into the manuscript without checking the tracked source and `PAPER_FRAMEWORK_HANDOFF.md`.
