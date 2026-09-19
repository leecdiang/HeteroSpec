# HeteroSpec MLSys 2027 Paper Framework Handoff

> Role: scientific framework handoff / evidence ledger / paper architecture.
> This file is the single source of truth for MLSys 2027 paper claims. It is not manuscript prose.
> Scientific priority: frozen experiment definitions and repository evidence > audit workflow > presentation.

## 0. Handoff metadata

- Last updated: 2026-09-19
- Audited branch base: `main`
- Audited main HEAD: `8de9642b3d27830ec182f3571974069d5b88d405`
- Head meaning: merge commit for PR #12, `358H: close Phase-3 heterogeneous validation`
- Audit branch: `paper/audit-round1-20260918`
- Open audit PR: #13, `Paper: complete MLSys 2027 scientific audit (Rounds 1–12)`
- Auditor: ChatGPT / GPT-5.6 Sol using the connected GitHub repository tools
- Current phase: hardware experiments **CLOSED**; paper scientific-audit / handoff maintenance phase
- Historical audit scope completed on this branch: **Rounds 1–12 — FULL SCIENTIFIC AUDIT COMPLETE**
- Current bounded action: **Round 1 revalidation on 2026-09-19** after mandatory Skill/Plugin rediscovery
- Audit scope not yet authorized by this turn: manuscript prose, final figure production, or a new runtime/software experiment
- No new hardware experiment was designed or run.
- No preregistration, raw artifact, historical result report, or frozen experiment data was modified.

### 0.1 Tool / Skill / Plugin discovery record — Stage A revalidation (2026-09-19)

Discovery was repeated before the repository-wide revalidation, as required. The current environment is **not identical** to the earlier audit environment: the Data Analytics skill family is now exposed, including dedicated analysis-validation and data-quality workflows. This changes the audit tooling record but **does not change scientific authority**: frozen experiment definitions and repository evidence remain controlling.

#### All currently visible installed Skills and advertised descriptions

| Skill | URI / family | Advertised description / role |
|---|---|---|
| analyze-data-quality | `skills://plugins/data-analytics/analyze-data-quality` | Investigate freshness, grain, missingness, duplicates, broken joins, schema drift, and conflicting structured-data results. |
| build-dashboard | `skills://plugins/data-analytics/build-dashboard` | Build/update source-backed interactive dashboards. |
| build-report | `skills://plugins/data-analytics/build-report` | Build polished analytical reports supported by inspectable evidence. |
| convert-to-doc | `skills://plugins/data-analytics/convert-to-doc` | Convert an existing Data app into DOCX / Google Doc. |
| convert-to-slides | `skills://plugins/data-analytics/convert-to-slides` | Convert an existing Data app into PowerPoint / Google Slides. |
| create-data-context | `skills://plugins/data-analytics/create-data-context` | Create/update reusable analytical context, conventions, definitions, and preferences. |
| design-kpis | `skills://plugins/data-analytics/design-kpis` | Design KPI definitions, targets, guardrails, and measurement plans. |
| gather-business-context | `skills://plugins/data-analytics/gather-business-context` | Gather business context from connected/provided sources before analysis. |
| index | `skills://plugins/data-analytics/index` | Router/index for Data analysis, diagnostics, data quality, sizing, dashboards, reports, charts, notebooks, and reusable context. |
| jupyter-notebooks | `skills://plugins/data-analytics/jupyter-notebooks` | Create/edit/validate reproducible SQL/Python notebooks and audit trails. |
| kpi-reporting | `skills://plugins/data-analytics/kpi-reporting` | Prepare KPI readouts, scorecards, WBR/MBR/QBR summaries. |
| market-sizing | `skills://plugins/data-analytics/market-sizing` | Estimate TAM/SAM/SOM and opportunity size with transparent assumptions. |
| metric-diagnostics | `skills://plugins/data-analytics/metric-diagnostics` | Diagnose metric changes, anomalies, gaps, and discrepancies. |
| product-business-analysis | `skills://plugins/data-analytics/product-business-analysis` | Support product/business decisions with metric-backed evidence. |
| publish-artifact-to-sites | `skills://plugins/data-analytics/publish-artifact-to-sites` | Publish an existing Data report/dashboard to Sites. |
| report-to-pdf | `skills://plugins/data-analytics/report-to-pdf` | Create PDF from an existing Data report/dashboard. |
| schedule-refresh-jobs | `skills://plugins/data-analytics/schedule-refresh-jobs` | Schedule recurring refresh for existing Data artifacts. |
| share-artifact-summary | `skills://plugins/data-analytics/share-artifact-summary` | Share a concise summary of a Data report/dashboard/chart. |
| validate-data | `skills://plugins/data-analytics/validate-data` | Validate methodology, sources, calculations, visuals, conclusions, and supported repairs. |
| visualize-data | `skills://plugins/data-analytics/visualize-data` | Design/build/revise/verify quantitative charts and figures for durable artifacts. |
| Analytics Dashboard template | `skills://plugins/openai-templates/artifact-template-analytics-dashboard` | Spreadsheet template for acquisition, engagement, retention, revenue, and conversion KPIs. |
| Business Review template | `skills://plugins/openai-templates/artifact-template-business-review` | Presentation template for business performance, KPIs, priorities, and decisions. |
| Design Report template | `skills://plugins/openai-templates/artifact-template-design-report` | Document template for findings, implications, recommendations, and appendix. |
| Experiment Analysis template | `skills://plugins/openai-templates/artifact-template-experiment-analysis` | Document template for hypotheses, methodology, results, interpretation, limitations, next steps. |
| Financial Budget template | `skills://plugins/openai-templates/artifact-template-financial-budget` | Spreadsheet template for actuals, budget, scenarios, variances, and runway. |
| Investment Committee Memo template | `skills://plugins/openai-templates/artifact-template-investment-committee-memo` | Document template for investment thesis, analysis, risks, and recommendation. |
| Legal Memorandum template | `skills://plugins/openai-templates/artifact-template-legal-memorandum` | Document template for issue, answer, facts, analysis, conclusion. |
| Market Trends Report template | `skills://plugins/openai-templates/artifact-template-market-trends-report` | Presentation template for market/industry trends and supporting evidence. |
| Minimal Letterhead template | `skills://plugins/openai-templates/artifact-template-minimal-letterhead` | Document template for professional business letters. |
| Operating Calendar template | `skills://plugins/openai-templates/artifact-template-operating-calendar` | Spreadsheet template for milestones, campaigns, launches, deadlines. |
| Operating Review template | `skills://plugins/openai-templates/artifact-template-operating-review` | Presentation template for operating scorecards, risks, decisions, actions. |
| Project Kickoff template | `skills://plugins/openai-templates/artifact-template-project-kickoff` | Presentation template for goals, scope, roles, milestones, and risks. |
| Project Tracker template | `skills://plugins/openai-templates/artifact-template-project-tracker` | Spreadsheet template for workstreams, tasks, owners, dates, status, and Gantt. |
| Sales Pipeline template | `skills://plugins/openai-templates/artifact-template-sales-pipeline` | Spreadsheet template for opportunities, stages, probabilities, forecasts, risks. |
| Simple Dark Mode template | `skills://plugins/openai-templates/artifact-template-simple-dark-mode` | General dark-mode presentation template. |
| Simple Light Mode template | `skills://plugins/openai-templates/artifact-template-simple-light-mode` | General light-mode presentation template. |
| Strategy Memorandum template | `skills://plugins/openai-templates/artifact-template-strategy-memorandum` | Document template for strategic choices, rationale, risks, and milestones. |
| System Design template | `skills://plugins/openai-templates/artifact-template-system-design` | Document template for architecture, requirements, components, flows, APIs, and tradeoffs. |
| Team Alignment template | `skills://plugins/openai-templates/artifact-template-team-alignment` | Presentation template for goals, priorities, decisions, and action items. |
| Three-Statement Forecast template | `skills://plugins/openai-templates/artifact-template-three-statement-forecast` | Spreadsheet template for integrated income statement, balance sheet, cash flow. |
| Template Creator | `skills://plugins/template-creator/template-creator` | Create/update reusable artifact-template skills from reference artifacts. |
| Presentation router | `skills://plugins/presentations-router/presentation` | Route explicitly selected presentation tasks. |
| PDF router | `skills://plugins/pdf-router/pdf` | Route explicitly selected PDF tasks. |
| Document router | `skills://plugins/documents-router/document` | Route explicitly selected document tasks. |
| Plugin Management | `skills://plugins/plugin-management/plugin-management` | Discover/manage plugins, permissions, connections, and dependencies. |
| Spreadsheet router | `skills://plugins/spreadsheets-router/spreadsheet` | Route explicitly selected spreadsheet tasks. |

#### Candidate Skill instructions inspected for this Stage A revalidation

1. **validate-data**
   - URI: `skills://plugins/data-analytics/validate-data/skill.md`
   - Instructions read in full; deep-review reference also inspected.
   - Why applicable: this is an explicit scientific-analysis audit. The workflow requires recovering the question/evidence, checking methodology/data fitness, independently verifying consequential calculations when needed, separating causal mechanisms from supported associations, and reporting unresolved verification honestly.
   - Used for: **Round 1 revalidation workflow discipline only**. This round is status/staleness-focused, so no wholesale recomputation was repeated.
   - Cannot solve: Git provenance by itself, raw artifact SHA identity by itself, preregistration authority, cross-platform causal attribution, novelty, or scientific claims unsupported by repository evidence.
   - Boundary: it is an audit workflow aid, not a scientific authority that can override frozen definitions or repository evidence.

2. **analyze-data-quality**
   - URI: `skills://plugins/data-analytics/analyze-data-quality/skill.md`
   - Instructions read in full.
   - Why applicable: useful for targeted checks of source freshness, grain, completeness, duplicate/conflicting outputs, and lineage risks in processed/raw structured experiment data.
   - Used for: **scoped companion methodology**. No new broad raw-data profile was launched in Round 1 because the bounded task is repository final status/stale documents.
   - Cannot solve: claim admissibility, causal interpretation, Git commit provenance, paper novelty, or whether an execution path satisfies the frozen correctness contract without the underlying experiment evidence.

3. **Experiment Analysis template**
   - URI: `skills://plugins/openai-templates/artifact-template-experiment-analysis/skill.md`
   - Instructions read in full.
   - Why considered: its hypothesis/method/result/limitation structure is relevant to experiment organization.
   - Used for: **not invoked as an artifact template**. The task requires a repository Markdown scientific ledger, not a styled document.
   - Cannot solve: Git provenance, SHA/integrity validation, raw→analysis→report lineage, cross-platform causality, bootstrap correctness, novelty.

4. **System Design template**
   - URI: `skills://plugins/openai-templates/artifact-template-system-design/skill.md`
   - Instructions read in full.
   - Stage fit: Stage D runtime/software co-design only, after hardware evidence is frozen.
   - Used for Round 1: **not used for scientific conclusions**.
   - Cannot solve: retrospective scientific validity, experimental provenance, correctness-admissibility, causal attribution.

#### Plugin / repository / statistics / research capability discovery

- **GitHub connector:** installed, connected, and used directly for private repository read/write operations.
- Repository access: push and pull are available; `main` was not modified.
- Plugin directory search was repeated for scientific/reproducibility/statistics/academic-paper/figure capabilities.
- **Scite:** available in directory but not installed; potentially useful in Stage E for literature/citation-context checks. Not needed for Round 1 repository status.
- **Wolfram:** available in directory but not installed; potentially useful in Stage B for independent mathematical/statistical verification. Not needed for Round 1 status audit.
- **Hugging Face:** available in directory but not installed; potentially useful for model/dataset metadata checks if a future provenance question requires it.
- General Python statistical computation remains available for deterministic recomputation, but no Round-1 headline recomputation was necessary because this bounded pass verified repository status and living-document consistency.
- Document/report/figure skills are presentation aids and do not supersede repository evidence.

**Stage-A authority for scientific truth remains:** frozen experiment definitions + repository evidence + claim taxonomy + evidence ledger + explicit uncertainty/limitations.

### 0.2 Historical Stage C rediscovery — unified mechanism/formula

- Skill discovery was repeated before Round 6 in the prior audit sequence.
- The audit concluded that no template or plugin could establish a cost identity or measured-variable semantics independently of runtime evidence.
- Round-6 authority therefore remained frozen runtime semantics, measured decompositions, mechanism controls, and algebraic consistency with end-to-end observations.
- The key scientific correction from that round is preserved in Section 5: `V_k^micro` is a target-forward batching proxy and must not be silently substituted for complete realized target-side round cost.

### 0.3 Historical Stage B rediscovery — statistics / confidence intervals

- Skill discovery was repeated before Round 7 in the prior audit sequence.
- Statistical validation used repository analysis code plus independent deterministic recomputation of frozen prompt-level vectors.
- The current environment now exposes `validate-data` and `analyze-data-quality`, but this does **not** invalidate or alter the earlier numerical audit; those skills would be workflow aids if Round 7 were rerun.
- No preregistered estimator or historical report is changed by current tool availability.

### 0.4 Historical Stages D/E/F/G rediscovery

- Previous rediscovery before runtime-design, synthesis, figure-plan, and adversarial-review stages found no tool that superseded repository evidence.
- Stage D remained a bounded future-design audit; no implementation was added.
- Stage E synthesis used the evidence ledger plus literature review.
- Stage F figure planning was limited to audited quantities and avoids cross-platform hardware ranking.
- Stage G adversarial review used repository evidence, protocol deviations, provenance limitations, statistics, and related work rather than template-generated scoring.
- If any of Stages D/E/F/G are reopened, discovery must be repeated again because the environment has changed since those historical passes.

## 1. Project status

### Hardware study status

**CLOSED** under the frozen campaigns.

| Platform | Final status | Bounded interpretation |
|---|---|---|
| MacBook Air M4 / llama.cpp Metal | CLOSED | Representative frozen Spec-Bench 24Q negative; separately preregistered HumanEval30 fixed-k=2 exact profitable regime exists. Workload-conditioned, not general. |
| Core Ultra 9 275HX + RTX 5070 Ti Laptop / CUDA | CLOSED | CPU→RTX and exact same-GPU HumanEval controls are negative. Cheap batched raw verification exists but is not correctness-admissible under the frozen token-exact contract. |
| Core i5-13400 + Arc B570 / Vulkan | CLOSED | Fast path fails correctness; serialized fallback improves exactness but remains non-universal. No tested B570 path is a correctness-admissible optimization result. |
| Core Ultra X7 358H + Arc B390 target + CPU/NPU OpenVINO draft | CLOSED | CPU and NPU paths are token-exact but unprofitable; CPU is target-verification-bound, NPU is realized state/replay+proposal bound. |

### Software/runtime study status

- No new formal runtime/software contribution has been started.
- Runtime design opportunities are evidence-derived future work only.
- Persistent draft state, rollback/reuse, profitability controller, adaptive-k, correctness-aware path selection, and device selection are **not measured paper contributions** in the closed hardware study.

### Paper status

- The existing audit branch completed Rounds 1–12 and froze the scientific thesis/contribution ordering for drafting.
- This 2026-09-19 action is only a **Round 1 repository-status revalidation** and does not reopen or overturn later rounds.
- Final title remains unfrozen; wording may change without changing scientific claims.
- Manuscript prose has intentionally not been produced by this audit task.
- `main` still contains several stale pre-Phase3 paper-control documents; the audit branch already carries the synchronized replacements.

## 2. Research question candidates

Primary candidate:

> Under what correctness, verification-amortization, realized draft-state cost, and workload conditions does speculative decoding become profitable on consumer hardware?

Supporting questions:

- When does a physically fast target-verification path remain usable after the frozen correctness contract is applied?
- When does isolated draft-device throughput fail to predict realized end-to-end draft cost?
- How much committed work per speculative round is required to amortize realized draft + complete target-side + residual runtime cost?

Do not reduce the paper question to “does heterogeneous speculative decoding work?”. The evidence supports **regime characterization**, not a universal binary verdict.

## 3. Current leading / frozen scientific thesis

Frozen by the prior Round-12 audit; unchanged by the current Round-1 revalidation:

> On the tested consumer systems, speculative decoding is profitable only when a **correctness-admissible execution path** and the **realized stateful draft interface** keep total per-round cost below the progress actually committed by that round. Acceptance rate and isolated draft throughput are insufficient summaries because the usable verification path can change after exactness filtering, and runtime state reconstruction can dominate a nominally fast draft device.

Four observed regimes:

1. **Profitable + exact:** M4 / llama.cpp Metal, separately preregistered HumanEval code-conditioned fixed-k=2, 1.387x [1.351, 1.422], 90/90 exact.
2. **Exact but unprofitable:** M4 representative 24Q, RTX serialized HumanEval controls, 358H CPU/NPU.
3. **Physically fast but correctness-inadmissible:** RTX CUDA batched `ubatch=2`; B570 fast Vulkan path.
4. **State-interface bound:** 358H NPU, where full committed-prefix replay + proposal dominates realized draft cost despite favorable isolated NPU throughput.

The thesis is explicitly **not**:
- heterogeneous speculative decoding is new;
- acceptance is not enough as a standalone novelty claim;
- M4 wins because of unified memory;
- CUDA/Vulkan is broken;
- NPU hardware is unsuitable.

## 4. Candidate / frozen contributions

Contribution order frozen by the prior Round 12; current revalidation found no status evidence requiring a change.

1. **Auditable cross-platform characterization of speculative-decoding regimes on four consumer systems.**
   - positive, negative, correctness-blocked, and state-interface-bound outcomes are all retained;
   - mechanism triangulation, not a controlled hardware leaderboard.

2. **Correctness-constrained realized-cost accounting.**
   - distinguish complete realized round cost `D_real + R_target + X` from target-forward microbenchmark proxy `V_k^micro`;
   - distinguish committed progress `C` from accepted draft tokens/round;
   - treat as accounting/diagnostic discipline, not a universal new theory.

3. **Empirical evidence that correctness filtering changes the usable verification path.**
   - RTX: near-one-step batched verification is physically available but violates the frozen exactness contract; the tested exact control is near-serialized and negative;
   - B570: serialization itself does not guarantee global exactness.

4. **Empirical evidence that the realized state interface can erase isolated draft-device advantage.**
   - 358H NPU proposal calls reconstruct the complete committed prefix; replay+proposal is 58.35% of measured speculative time;
   - CPU remains target-verification dominated.

5. **A preregistered workload-conditioned positive regime retained alongside a representative negative result.**
   - M4 HumanEval fixed-k2 positive;
   - M4 representative 24Q negative;
   - supports selective/runtime-aware deployment rather than a platform-wide win claim.

Artifact/provenance quality is a supporting strength, not a standalone novelty claim.

## 5. Unified analytical framework

### 5.1 Realized round accounting

For one realized speculative round:

```text
S_round =
    T_b * C
    -------------------------------------------
    T_d(real) + T_target,round(real) + T_x
```

Normalize by matched baseline target-token cost `T_b`:

```text
S_round = C / [D_real + R_target + X]
```

Break-even:

```text
C > D_real + R_target + X
```

Definitions:

- `T_b`: matched target-only baseline cost per output token under the same timing boundary.
- `T_d(real)`: realized draft-subsystem cost through the actual state interface; may include replay/reconstruction when execution does so.
- `T_target,round(real)`: complete realized target-side cost per speculative round, including verification and any target correction/bonus behavior inside the measured runtime boundary.
- `T_x`: residual cost not already included above.
- `C`: all output tokens committed by the round, including correction/bonus behavior.
- `D_real=T_d(real)/T_b`, `R_target=T_target,round(real)/T_b`, `X=T_x/T_b`.

This is an accounting identity when components share a boundary; it does not imply every platform exposes every term independently.

### 5.2 Target-forward microbenchmark proxy

Separately:

```text
V_k^micro(n,e) =
    T_target_forward(k,n,e)
    -----------------------
    T_target_decode(1,n)
```

Interpretation:
- mechanism / batching-efficiency proxy;
- still subject to correctness filtering;
- **not** automatically equal to complete realized `R_target`;
- a physically fast path failing exactness is not an admissible optimization path.

Platform interpretation:
- M4: `V_2^micro≈1.02–1.08` demonstrates cheap exact width-two target-forward batching.
- RTX: batched `V_2^micro≈0.98–1.01` is cheap but correctness-blocked; serialized exact control `≈2.14–2.43`.
- B570: historical serialized `PP2/PP1≈1.98–1.99` is diagnostic and not globally exact on HumanEval30.
- 358H: Phase 3 directly measures the complete target-side interval and provides the cleanest realization of `R_target`.

358H aggregate accounting check:

| Path | `C` | `D_real` | `R_target` | `X` | `C/(D+R+X)` | Aggregate baseline/spec ratio |
|---|---:|---:|---:|---:|---:|---:|
| CPU draft | 2.4631 | 0.4304 | 2.9767 | 0.00124 | 0.7227 | 0.7227 |
| NPU draft | 2.4584 | 4.1251 | 2.9435 | 0.00130 | 0.3477 | 0.3477 |

These ratio-of-totals values are not expected to equal prompt-level geometric-mean headline speedups 0.734x/0.352x; aggregation level must be explicit.

### 5.3 Committed work versus accepted draft tokens

- 358H records `C` directly: 2.4631 CPU and 2.4584 NPU.
- Historical M4/RTX `accepted_per_round` fields count accepted **draft** tokens/round and are not `C`.
- M4 effective output progress reconstructed from runtime counters is descriptive only; do not promote it to the same measurement status as direct 358H `C`.
- High acceptance therefore cannot substitute for committed progress in the accounting model.

### 5.4 Formula complexity rule

Keep `T_d(real)` aggregated unless frozen evidence exposes a finer term without changing execution. Do not invent separately measured replay, rollback, reconstruction, transfer, or correction terms for platforms where they were not measured.

## 6. Platform regime map

### M4 / Metal

- Representative frozen Spec-Bench 24Q: **0.842x**, 95% CI **[0.809, 0.877]**, 72/72 exact, 1/24 prompts faster.
- Package efficiency ratio: 0.678x; baseline 1.206 vs k2 1.729 package J/output-token.
- Separately preregistered HumanEval30 fixed-k=2: **1.387x [1.351, 1.422]**, 30/30 faster, 90/90 exact, mean acceptance ≈90.1%, accepted draft tokens/round ≈1.798.
- HumanEval fixed-k2 package efficiency 1.013x [0.990, 1.034]: **energy-neutral within uncertainty**.
- Registered p_min=0.9 secondary package efficiency: 1.041x [1.018, 1.065].
- Safe interpretation: profitable exact **code-conditioned** regime exists; representative workload did not generalize it.
- Corrected synthetic ceiling from preregistration: **NOT EXECUTED**; older exploratory synthetic data cannot substitute.

### RTX 5070 Ti Laptop / CUDA

- Platform closed.
- 60Q pilot negative across k; 0–1/60 prompts faster depending on k.
- HumanEval exact serialized controls:
  - CPU→RTX: **0.404x [0.390, 0.418]**, 90/90 exact, 0/30 faster, 91.31% acceptance.
  - RTX→RTX: **0.650x [0.629, 0.673]**, 90/90 exact, 0/30 faster, 91.21% acceptance.
- Raw CUDA `ubatch=2` `V_2^micro≈0.983–1.009` but frozen exactness fails on a stable HumanEval/106 reproduction.
- Exact `ubatch=1` `V_2^micro≈2.137–2.431`.
- Stable logit ordering flip supports a batch-shape-dependent numerical argmax change, not a universal CUDA defect.
- Safe interpretation: transfer is not the sole cause; correctness filtering removes the fast verification path in this frozen configuration.

### Arc B570 / Vulkan

- Platform closed after one preregistered serialized fallback candidate.
- Fast path: 45/90 exact pairs; speedup 0.5383x diagnostic; V2(512)=1.2426, V2(2048)=1.6373.
- Serialized fallback: 60/90 exact pairs; 20/30 wholly exact prompts; speedup **0.3087x [0.2927, 0.3246]** diagnostic; 0/30 faster.
- Serialized verification proxy: 1.9827 at 512; 1.9917 at 2048.
- Board-energy efficiency ratio 0.3023x [0.2846, 0.3202]; Arc B570 board boundary only.
- Historical reports use `V2_exact`; paper-facing term is **serialized fallback verification factor / `V2_serialized`** unless an explicitly bounded exact subset is named.
- Safe interpretation: no tested B570 path qualifies as a correctness-admissible optimization result.

### Core Ultra X7 358H + Arc B390 target + CPU/NPU OpenVINO draft

- Phase 0–3 scientific execution complete and merged to `main`.
- Stage-A gate: CPU 18/18 exact; NPU 18/18 exact.
- HumanEval30:
  - CPU: **0.734x [0.693, 0.771]**, 90/90 exact, 0/30 faster.
  - NPU: **0.352x [0.333, 0.369]**, 90/90 exact, 0/30 faster.
- Acceptance / committed work:
  - CPU 75.31%, C=2.463.
  - NPU 75.13%, C=2.458.
- Decomposition:
  - CPU: replay+proposal 12.63%, target verification 87.34%, residual 0.04%.
  - NPU: replay+proposal 58.35%, target verification 41.63%, residual 0.02%.
- End-to-end energy is not claimed; NPU energy is not admissible.
- Reconstructed draft source identity remains **STRONGLY_SUPPORTED**, not proven exact upstream identity.
- Safe interpretation: current OpenVINO/state interface erases isolated NPU draft-throughput advantage through full-prefix replay+proposal; do not generalize to NPUs.

## 7. Claim taxonomy

| Claim ID | Candidate wording | Status | Platforms | Quantitative support | Limitation / reviewer risk | Paper placement |
|---|---|---|---|---|---|---|
| C-M4-01 | A preregistered exact profitable fixed-k=2 regime exists on M4 for the frozen HumanEval code-conditioned workload. | PRIMARY | M4 | 1.387x [1.351,1.422], 90/90 exact, 30/30 faster | workload-conditioned; no functional pass@k | Results |
| C-M4-02 | The representative frozen 24Q M4 study is negative. | PRIMARY | M4 | 0.842x [0.809,0.877], 72/72 exact | workload differs from HumanEval | Results / anti-cherry-pick context |
| C-XP-01 | Acceptance alone is insufficient to predict profitability. | MECHANISM_SUPPORTED | M4, RTX, 358H; B570 diagnostic | high acceptance coexists with positive/negative outcomes | cross-platform association; not single isolated cause | Intro / Discussion |
| C-RTX-01 | In the frozen llama.cpp/CUDA/Q8_0 configuration, the fast batched path can change greedy argmax and is not admissible under the token-exact contract. | MECHANISM_SUPPORTED | RTX | stable HumanEval/106 divergence + logit-order sign flip | bounded config/case | Results |
| C-RTX-02 | The tested exact CUDA fallback raises width-2 target-forward cost to roughly 2.14–2.43 target decodes. | MECHANISM_SUPPORTED | RTX | ubatch=1 controls | microbenchmark, not full round cost | Results / Framework |
| C-B570-01 | The single serialized B570 fallback is not universally token-exact on HumanEval30. | DIAGNOSTIC | B570 | 60/90 pairs; 20/30 prompts exact | post-gate diagnostic phase | Results / Limitation |
| C-B570-02 | B570 has no tested correctness-admissible optimization result. | SECONDARY | B570 | fast and serialized correctness failures | backend/config bounded | Results |
| C-358H-01 | CPU and NPU 358H paths are token-exact but unprofitable in frozen Phase 3. | PRIMARY | 358H | 0.734x / 0.352x; both 90/90 exact | post-prefill timing | Results |
| C-358H-02 | Realized stateful draft cost dominates the tested NPU path despite favorable isolated draft throughput. | MECHANISM_SUPPORTED | 358H NPU | replay+proposal 58.35% | replay/proposal inseparable; interface-specific | Framework / Discussion |
| C-XP-02 | Verification amortization must be correctness-filtered. | MECHANISM_SUPPORTED | M4, RTX, B570 | cheap exact vs cheap inadmissible paths | strict token-exact contract is a study choice | Framework |
| C-M4-CAUSE-UM | Unified memory is the cause of M4 profitability. | PLAUSIBLE_NOT_CAUSAL | M4 | compatible but not isolated | no causal control | Never causal wording |
| C-CUDA-BROKEN | CUDA is broken for speculative decoding. | FORBIDDEN_OVERCLAIM | RTX | not supported | single frozen stack/configuration | Never |
| C-NPU-SLOW | NPU compute is too slow for speculative decoding. | FORBIDDEN_OVERCLAIM | 358H | contradicted by isolated-throughput evidence | measured issue is realized state interface | Never |
| C-HE-FUNC | Token-exact HumanEval outputs establish functional HumanEval correctness/pass@k. | FORBIDDEN_OVERCLAIM | HumanEval studies | generated code not executed | invalid metric substitution | Never |
| C-ENERGY-RANK | Absolute J/token ranks all platforms directly. | FORBIDDEN_OVERCLAIM | all | sensor boundaries differ | incomparable domains | Never |
| C-M4-GENERAL | Speculative decoding generally works on M4. | FORBIDDEN_OVERCLAIM | M4 | representative 24Q negative | positive is workload-conditioned | Never |

## 8. Evidence ledger

Headline evidence has already been traced more deeply in historical Rounds 2–7. This table is the paper-facing compact ledger; source reports remain unchanged historical evidence.

| Evidence ID | Platform / experiment | Class | Metric / value | CI / repetitions | Correctness | Workload / runtime | Source report / evidence path | Energy boundary / caveat | Paper use |
|---|---|---|---|---|---|---|---|---|---|
| E-M4-24Q-01 | M4 representative confirmation | PRIMARY | speedup 0.842x | [0.809,0.877], 24 prompts ×3 | 72/72 exact | Spec-Bench 24Q; Qwen3-8B/0.6B Q8_0; Metal k=2 | `reports/m4/M4_CONFIRMATORY_VALIDATION.md`; indexed in `M4_EXPERIMENT_INDEX.md` | Silemetry package aggregate; separate DRAM excluded | representative negative |
| E-M4-HE30-01 | M4 HumanEval30 fixed-k2 | PRIMARY | 1.387x | [1.351,1.422], 30×3 | 90/90 exact | HumanEval30; same Q8_0 pair; Metal | `reports/m4/M4_HUMANEVAL_CODE_CONDITIONED.md`; authoritative archive `artifacts/m4_humaneval_code_conditioned/` | package efficiency 1.013x [0.990,1.034], neutral within uncertainty | conditioned positive regime |
| E-M4-HE30-02 | M4 p_min=.9 secondary | SECONDARY | package efficiency 1.041x | [1.018,1.065] | 90/90 exact | same | same prereg/report/archive | package only | secondary energy result |
| E-RTX-HE30-CPU-01 | CPU→RTX exact serialized | SECONDARY | 0.404x | [0.390,0.418], 30×3 | 90/90 exact | HumanEval30; llama.cpp CUDA ubatch=1 | `reports/5070ti/HUMANEVAL_LLAMA_REPLICATION.md`, final platform report | not primary energy evidence; raw per-run Git provenance weaker | exact negative control |
| E-RTX-HE30-GPU-01 | RTX→RTX exact serialized | SECONDARY | 0.650x | [0.629,0.673], 30×3 | 90/90 exact | same | same | not primary energy evidence | exact negative control |
| E-RTX-V2-RAW-01 | RTX raw CUDA verification | DIAGNOSTIC | 1.009@0; 0.983@256 | mechanism control | correctness-blocked | CUDA ubatch=2 | `reports/5070ti/WINDOWS_VERIFICATION_MECHANISM_CONTROLS.md` | n/a | raw-vs-admissible path |
| E-RTX-V2-ADM-01 | RTX serialized exact verification | MECHANISM_SUPPORTED | 2.431@0; 2.137@256 | mechanism control | exact control | CUDA ubatch=1 | same | n/a | admissible verification penalty |
| E-RTX-DIV-01 | RTX divergence min-repro | MECHANISM_SUPPORTED | margin +0.080948 → -0.126457; token 2790→2629 | 3/3 independent processes | demonstrates divergence | HumanEval/106 | `reports/5070ti/CUDA_DIVERGENCE_NUMERICAL_DIAGNOSIS.md` | bounded config/case | numerical mechanism |
| E-B570-FAST-01 | B570 fast path | DIAGNOSTIC | speedup 0.5383; V2 1.2426/1.6373 | 90 pairs | 45/90 exact | HumanEval30; Vulkan | `reports/b570/B570_FAST_VS_EXACT_FALLBACK.md` | board efficiency 0.6961; diagnostic | correctness-blocked |
| E-B570-SERIAL-01 | B570 serialized fallback | DIAGNOSTIC | 0.3087; V2 1.9827/1.9917 | [0.2927,0.3246] | 60/90 exact | HumanEval30; Vulkan n_ubatch=1 | `reports/b570/B570_EXACT_FALLBACK_VALIDATION.md` | board efficiency 0.3023 [0.2846,0.3202]; diagnostic | serialized fallback boundary |
| E-358H-P3-CPU-01 | 358H CPU draft | PRIMARY | 0.734x | [0.693,0.771], 30×3 | 90/90 exact; gate 18/18 | Vulkan0 target + OpenVINO CPU draft | `reports/358h/358H_PHASE3_END_TO_END_VALIDATION.md` | no end-to-end energy claim | exact negative CPU |
| E-358H-P3-NPU-01 | 358H NPU draft | PRIMARY | 0.352x | [0.333,0.369], 30×3 | 90/90 exact; gate 18/18 | Vulkan0 target + OpenVINO NPU draft | same | NPU energy NOT_ADMISSIBLE | exact negative NPU |
| E-358H-DECOMP-CPU-01 | 358H CPU decomposition | MECHANISM_SUPPORTED | replay+proposal 12.63%; verify 87.34%; residual 0.04% | arithmetic mean of 90 requests | exact | Phase3 | same + analysis outputs | n/a | verification-bound mechanism |
| E-358H-DECOMP-NPU-01 | 358H NPU decomposition | MECHANISM_SUPPORTED | replay+proposal 58.35%; verify 41.63%; residual 0.02% | arithmetic mean of 90 requests | exact | Phase3 | same + analysis outputs | n/a | state-interface mechanism |
| E-358H-ARCHIVE-01 | 358H archive integrity | SECONDARY | 34/34 manifest entries verified; zero failures | closeout archive | n/a | Phase3 archive | `reports/358h/358H_REPOSITORY_CLOSEOUT_AUDIT.md`; tar SHA256 `2fa619...8511` | n/a | reproducibility |

## 9. Cross-platform comparison table

| Regime | Correctness-admissible end-to-end result? | Profitability | Main supported bottleneck / enabling condition | Critical caveat |
|---|---|---|---|---|
| M4 24Q k=2 | Yes | No, 0.842x | workload/committed-progress insufficient despite cheap exact batching | not evidence M4 speculation never works |
| M4 HumanEval k=2 | Yes | Yes, 1.387x | cheap exact verification + favorable code-conditioned workload | no functional HumanEval execution |
| RTX CUDA HumanEval | Yes only via serialized controls | No, 0.404x / 0.650x | correctness-admissible verification near-serialized; draft/integration overhead remains | fast raw path exists but is correctness-blocked |
| B570 Vulkan | No universally exact tested path | No admissible optimization claim | correctness failure; serialization ~2× and still non-universal | timing/energy are diagnostic |
| 358H CPU | Yes | No, 0.734x | target verification 87.34% | post-prefill timing boundary |
| 358H NPU | Yes | No, 0.352x | realized prefix replay+proposal 58.35% | current OpenVINO/state interface; not universal NPU claim |

Cross-platform comparison is **mechanism comparison**, not a controlled hardware ranking. Hardware, runtime, backend, quantization/execution, memory organization, and scheduling differ.

## 10. Figure plan

No final figure is produced by this audit.

| Figure ID | Question answered | Source data | Structure | Platforms | Evidence class | Risk / caveat |
|---|---|---|---|---|---|---|
| F1 | What must be amortized for speculation to profit? | framework + 358H decomposition | cost blocks `D_real`, `R_target`, `X`, `C`; `V_k^micro` inset | all | framework | do not imply every term independently measured everywhere |
| F2 | What distinct regimes exist? | headline prompt-level results | categorical regime map, not leaderboard | all | mixed, visibly encoded | do not imply pure hardware comparison |
| F3 | How does raw target batching differ from admissible verification? | M4/RTX/B570 controls | `V_2^micro` by path + correctness marker | M4, RTX, B570 | mechanism/diagnostic | B570 serialized path not universally exact |
| F4 | Why is acceptance insufficient? | acceptance/C + speedup | relationship plot only where definitions match | M4, RTX, 358H | mixed | accepted-draft/round ≠ direct C |
| F5 | Why does isolated NPU draft speed not survive end to end? | 358H Phase1 + Phase3 | isolated vs realized draft/state cost | 358H | primary/mechanism | interface-specific, not NPU hardware verdict |
| F6 | What dominates 358H request time? | Phase3 decomposition | CPU vs NPU stacked costs | 358H | primary/mechanism | arithmetic means vs prompt-GM labeled |
| F7 | What do energy measurements say within each sensor boundary? | platform energy summaries | separate small multiples | M4/RTX/B570 | primary/diagnostic | never one absolute ranking |

## 11. Table plan

| Table ID | Purpose | Required provenance |
|---|---|---|
| T1 | Platform/runtime/model/correctness-contract matrix | frozen configs + final reports |
| T2 | Headline outcomes with evidence class and correctness status | evidence ledger + statistics audit |
| T3 | Mechanism quantities: raw/admissible V2, C/acceptance, realized draft/state cost, residual | mechanism reports/scripts; N/A when not comparable |
| T4 | Energy sensor boundaries and permitted claims | telemetry protocols/reports; never merge domains |

## 12. Runtime/software design opportunities

Future study only; not current contributions.

| Opportunity | Measured bottleneck addressed | Platform evidence | Expected benefit | Difficulty | New experiment required? | Scope risk | Needed for current scientific validity? |
|---|---|---|---|---|---|---|---|
| correctness-aware verification path selection | cheap raw path may fail exactness | RTX, B570 | choose cheapest path satisfying correctness | medium | yes | medium | no |
| persistent draft state / rollback / reuse | full-prefix replay dominates realized draft cost | 358H NPU | reduce `T_d(real)` | high | yes, separately preregistered | high | no |
| online profitability controller | workload-conditioned M4 result | M4 24Q vs HumanEval | disable speculation in negative regimes | medium | yes | medium | no |
| adaptive k | deeper k can hurt acceptance/verification | M4/RTX pilots | trade committed progress against cost | medium | yes | medium-high | no |
| CPU/NPU/iGPU draft selection | isolated fastest device may not minimize realized cost | RTX characterization + 358H | choose device by realized cost | high | yes | high | no |

## 13. Reviewer attack list

| Concern | Severity | Evidence available | Response | Extra experiment by default? | Explicit limitation? |
|---|---|---|---|---|---|
| Only four platforms; can this generalize? | HIGH | four distinct stacks show repeated accounting constraints | claim regimes/mechanisms, not universal hardware law | no | yes |
| Cross-platform stacks differ; causality confounded | HIGH | bounded language + within-platform controls | separate within-platform mechanism evidence from cross-platform synthesis | no | yes |
| M4 HumanEval looks cherry-picked after 24Q failed | HIGH | separate preregistration, frozen IDs, negative 24Q retained | present chronology and both outcomes | no | yes |
| Why HumanEval if code not executed? | HIGH | exact-token contract only | state HumanEval is a structured generation distribution here, not pass@k evidence | no | yes |
| Token-exact contract is too strict | MEDIUM-HIGH | frozen deterministic-greedy equivalence contract | motivate as study contract; looser quality contracts are different work | no | yes |
| CUDA divergence may be a near-tie edge case | HIGH | stable 3/3 capture + gate impact | claim only frozen configuration/path | no | yes |
| B570 fallback called exact despite 60/90 | HIGH | direct mismatch between historical label and full workload | use `V2_serialized`; historical wording remains provenance | no | yes |
| 358H replay is a bad adapter, not NPU weakness | HIGH | state-interface semantics measured directly | agree with bounded interpretation; do not generalize to NPU hardware | no | yes |
| Should state reuse be implemented? | MEDIUM-HIGH | measured NPU bottleneck gives a clear design requirement | optional future strengthening, not retroactive evidence | maybe later | yes |
| Energy boundaries are incomparable | HIGH | boundaries documented | no global J/token ranking | no | yes |
| Why not a production speculative runtime? | MEDIUM | native/control evidence exists but study is implementation-bounded | frame as mechanism/characterization study | no by default | yes |
| Models are mostly Qwen3 8B/0.6B | HIGH | model consistency helps mechanism comparison | bound generalization | no by default | yes |
| Is this only an engineering benchmark paper? | HIGH | accounting + correctness/state-interface mechanisms | sell systems principle + auditable evidence, not leaderboard | no | yes |
| 358H prediction vs observation discrepancy undermines model | MEDIUM | omitted realized replay/state cost explains gap | use as validation for measuring `T_d(real)` | no | yes |
| No new runtime optimization is implemented | HIGH for MLSys novelty | characterization is scientifically coherent | do not claim runtime invention; optional co-design can strengthen future version | not for validity | yes |
| 358H source provenance is reconstructed | MEDIUM | qualification/provenance amendment | retain `STRONGLY_SUPPORTED`; never proven exact identity | no | yes |

## 14. Known limitations

1. HumanEval generated code was not executed for functional pass@k; “exact” means generated token-ID equality.
2. Energy boundaries differ by platform and cannot be treated as one calibrated domain.
3. M4 unified memory is not isolated as a causal factor.
4. CUDA batch-shape argmax flip is a bounded frozen-configuration observation, not “CUDA is broken.”
5. B570 results are frozen backend/configuration results; serialized fallback is not universally exact.
6. 358H NPU result is an end-to-end result of the current OpenVINO/state interface, not a universal NPU verdict.
7. 358H reconstructed draft source is `STRONGLY_SUPPORTED`, not proven exact upstream source identity.
8. M4 preregistered corrected synthetic ceiling was not completed.
9. Cross-platform comparisons change hardware and software simultaneously; causal attribution must remain within-platform unless an isolated control exists.
10. 358H primary timing is post-prefill decode end-to-end time, not whole-request user-perceived latency.
11. RTX/NVIDIA and Intel CPU component energy domains are separate and are not summed as whole-system energy.
12. B570 board energy excludes CPU/wall/whole-system energy.
13. Windows HumanEval/mechanism headline values are recomputable from committed derived tables, but raw per-run Git provenance is weaker than M4/B570/358H because some authoritative run JSONs were documented as local/ignored.
14. Prompt-bootstrap CIs represent prompt-sampling uncertainty conditional on each frozen campaign; they do not capture all between-session/thermal/runtime-state uncertainty.

## 15. Forbidden / unsafe claims

Never publish the following without new evidence:

- “Heterogeneous speculative decoding is generally profitable on consumer hardware.”
- “Speculative decoding generally works on M4.”
- “Unified memory causes the M4 win.”
- “CUDA is broken.”
- “Vulkan cannot do exact speculative decoding.”
- “The B570 serialized fallback is globally exact.”
- “The NPU is too slow / lacks compute.”
- “NPUs are unsuitable for speculative decoding.”
- “HumanEval exactness means functional correctness.”
- “Energy efficiency can be ranked directly across M4, RTX, B570, and 358H from current J/token values.”
- “358H reconstructed source exactly equals the lost historical upstream source.”
- “The corrected M4 synthetic ceiling was completed.”
- “High acceptance guarantees speedup.”
- “Isolated draft tok/s is the system draft cost.”
- “`V_k^micro` is automatically the complete realized target-side cost.”

## 16. Open scientific questions

Questions remaining after the completed audit are paper-scope / future-study questions, not unresolved status of the closed hardware campaigns:

- Is the strongest MLSys novelty the combined correctness-constrained realized-cost regime characterization, or does a separately measured runtime intervention materially improve acceptance prospects?
- If runtime co-design is started later, can persistent draft state reduce 358H-like `T_d(real)` without altering correctness or moving bottlenecks elsewhere?
- Under a looser non-token-exact quality contract, would the physically fast RTX/B570 paths become admissible, and how should quality loss be measured? This is a different study and must not be retrofitted onto current results.
- How broadly do the observed regimes generalize beyond Qwen3 and the tested runtimes? No universal model-family or hardware law is claimed.
- How should future work define a cross-platform committed-progress quantity when old runtimes expose only accepted draft tokens rather than full round commits?

## 17. Missing evidence / inconsistencies

### 17.1 Living documents stale on `main` at the current Round-1 revalidation

1. `REPO_STATUS.md`
   - still says status is on the 358H closeout branch / merge pending;
   - contradicted by `main` HEAD `8de9642...` and merged PR #12.

2. `paper/mlsys2027/EVIDENCE_AUDIT_2026-09-18.md`
   - records old `main` head `7327495...`;
   - treats 358H Phase3 as provisional/not started.

3. `paper/mlsys2027/WRITING_STATUS.md`
   - keeps 358H results and cross-platform table on HOLD because Phase3 was pending.

4. `paper/mlsys2027/README.md`
   - instructs keeping 358H provisional until Phase3 completes/merges.

5. `paper/mlsys2027/OUTLINE.md`
   - contains pre-Phase3 placeholders and old model terminology.

**Current branch state:** PR #13 / `paper/audit-round1-20260918` already contains synchronized replacements for these living docs. This revalidation therefore does not create another competing repair branch.

### 17.2 Historical reports with now-outdated process statements — preserve

- `reports/358h/358H_REPOSITORY_CLOSEOUT_AUDIT.md` contains pre-merge process wording.
- `reports/358h/358H_PLATFORM_CLOSEOUT.md` says repository integration gates must pass before merge.

These statements were true at report time and are provenance. Do not rewrite historical reports merely because PR #12 later merged.

### 17.3 Scientific terminology inconsistency

- Historical B570 reports use `V2_exact` although the same fallback validates only 60/90 pairs across HumanEval30.
- Paper-facing term remains **`V2_serialized` / serialized fallback verification factor**.
- Historical report wording is preserved for provenance.

### 17.4 Tooling provenance inconsistency discovered 2026-09-19

- Old handoff wording said no dedicated scientific validation/data-quality Skill was exposed.
- Current environment exposes `validate-data` and `analyze-data-quality`.
- This is a **tooling metadata change only**. It does not retroactively change any numerical audit, preregistration, or claim status.

### 17.5 Evidence depth summary after historical Rounds 2–7

- **M4:** strongest provenance; raw HumanEval results, preregistration, manifest, analysis script, prompt summary, telemetry metadata, and representative 24Q raw JSON were audited; headline aggregates independently recomputed.
- **RTX 5070 Ti Laptop:** headline statistics independently recomputed from committed pair-level CSV; raw per-run JSON provenance is weaker because some logs remain local/ignored, while committed derived tables/manifests/mechanism captures support the headline claims.
- **B570:** complete serialized-fallback archive committed; formal stop rule and later diagnostic status audited; CI reproducibility restored bit-for-bit by replaying retained first-seen prompt order.
- **358H:** headline values independently recomputed from committed prompt summary; runner semantics inspected; 34-entry archive and recovery bundle integrity audited.

No deep audit found a numerical discrepancy that changes a headline platform conclusion.

## 18. Paper outline candidate

Do not treat prose or final title as frozen. Scientific order currently supported:

1. Empirical puzzle / research question.
2. Correctness contract and admissible execution paths.
3. Realized-cost accounting and `V_k^micro` distinction.
4. Methodology and evidence classes.
5. M4: representative negative + preregistered workload-conditioned positive.
6. RTX: raw-fast vs exact-expensive verification.
7. B570: serialization does not guarantee admissibility.
8. 358H: exact-but-negative verification/state-interface regimes.
9. Cross-platform regime map and system implications.
10. Limitations / related work / conclusion.

No manuscript prose is authorized by this Round-1 revalidation.

## 19. Decision log

### D-20260918-01 — 358H final status
- Old: 358H pending/provisional in the original paper workspace.
- New: Phase 0–3 scientific execution **CLOSED** and merged to `main`.
- Evidence: merged PR #12; main HEAD `8de9642...`; Phase3 validation and platform closeout.

### D-20260918-02 — B570 verification terminology
- Old: historical `V2_exact` label for serialized fallback.
- New: paper uses `V2_serialized` / serialized fallback verification factor unless an explicitly bounded exact subset is named.
- Reason: full validation is only 60/90 exact pairs.

### D-20260918-03 — realized draft cost
- Old risk: isolated draft throughput used as proxy for `T_d`.
- New: framework uses `T_d(real)` through actual state interface.
- Reason: 358H NPU isolated throughput advantage is erased by full-prefix replay+proposal, 58.35% of speculative time.

### D-20260918-04 — formula complexity
- Old candidate: split proposal/replay/rollback/reconstruction.
- New: keep aggregate `T_d(real)` unless measured evidence exposes finer terms.
- Reason: replay-only/proposal-only cannot be separated in frozen 358H execution without changing inference.

### D-20260918-05 — M4 primary energy wording
- Old risk: treat fixed-k2 package efficiency 1.013x as an energy win.
- New: **energy-neutral within uncertainty**.
- Reason: 95% CI [0.990, 1.034] crosses 1.

### D-20260918-06 — committed-work metric
- Old risk: use `accepted_per_round` as `C`.
- New: `C` means all output tokens committed per speculative round, including target correction/bonus behavior.
- Reason: 358H records both notions and they are definitionally distinct.

### D-20260918-07 — Windows raw provenance level
- Old: imply equal raw provenance across all platforms.
- New: Windows headline values remain supported/recomputable, but raw per-run Git provenance is one tier weaker than M4/B570/358H.

### D-20260918-08 — serialized does not imply exact
- Old risk: call a serialized path exact by construction.
- New: serialization is execution-path property; exactness is an empirical workload-level correctness property.
- Reason: B570 ubatch=1 fallback is 60/90 exact despite passing an earlier 18/18 six-prompt gate.

### D-20260918-09 — separate micro verification proxy from realized target-round cost
- Old: `V_k(admissible)*T_b` used directly as end-to-end target term.
- New: end-to-end equation uses `T_target,round(real)` / `R_target`; `V_k^micro` is a separate target-forward batching proxy.
- Reason: microbenchmarks do not necessarily include correction/bonus and other target-side round work.

### D-20260918-10 — aggregation level of cost identity
- Old risk: expect arithmetic decomposition to reproduce prompt-level geometric-mean speedup.
- New: accounting identity must be evaluated at the same aggregation level as inputs.

### D-20260918-11 — B570 CI input-order question resolved
- Provisional concern: numerically sorting prompts changed finite fixed-seed bootstrap endpoints slightly.
- Resolution: retained finalizer uses first-seen randomized execution order; replaying it reproduces archived speed and energy CIs bit-for-bit.
- Scientific impact: none.

### D-20260919-01 — Stage-A Skill discovery refresh
- Old: handoff stated no dedicated scientific validation/data-quality Skill was exposed.
- New: current environment exposes `validate-data` and `analyze-data-quality`; both were inspected and adopted as workflow aids.
- Reason: mandatory rediscovery shows the available capability set changed.
- Scientific effect: **none**. Skills do not override frozen experiments, Git provenance, preregistration, or repository evidence.
- Additional discovered but uninstalled plugins: Scite (Stage E candidate), Wolfram (Stage B candidate), Hugging Face (provenance candidate). None was required for this Round 1.

## 20. Audit log

### Round 1 — 2026-09-18 — repository-wide final-status audit

- Main HEAD: `8de9642b3d27830ec182f3571974069d5b88d405`.
- PR #12 verified merged: `358H: close Phase-3 heterogeneous validation`.
- Inspected root status/docs, paper workspace, paper notes, and final platform reports.
- Findings:
  - four hardware campaigns scientifically closed;
  - 358H merged, making several paper-control documents stale;
  - root README synchronized;
  - B570 `V2_exact` terminology too strong at workload scope;
  - candidate unified formula viable only if draft cost is realized stateful cost and verification is correctness constrained.
- Changed conclusions at that time:
  - 358H provisional → final closed evidence;
  - state-interface cost elevated to first-class mechanism;
  - B570 serialized factor renamed for paper use.

### Round 2 — 2026-09-18 — M4 deep evidence-chain audit

- Traced preregistration → frozen selection → raw results → analysis script → prompt summaries → report.
- Independently recomputed HumanEval and representative 24Q headline statistics.
- No headline discrepancy found.
- Tightened energy wording and bootstrap-resample reporting.
- Clarified `accepted_per_round` ≠ unified `C`.

### Round 3 — 2026-09-18 — RTX 5070 Ti Laptop deep audit

- Independently recomputed exact-control HumanEval statistics from committed pair-level data.
- Verified verification-cost controls and stable numerical argmax sign flip.
- No headline discrepancy found.
- Added raw-trace Git provenance limitation for local/ignored run JSON files.

### Round 4 — 2026-09-18 — Arc B570 deep audit

- Verified formal-v2 stop rule, diagnostic-only extension, serialized fallback preregistration, full processed result, archive.
- No headline discrepancy found.
- Confirmed `V2_exact` must not be inherited as a global paper label.
- Fallback timing/energy remains diagnostic because full-workload exactness is 60/90, not 90/90.

### Round 5 — 2026-09-18 — 358H deep audit

- Independently recomputed prompt-level performance, exactness, decomposition, and committed-work accounting.
- Inspected runner implementation: OpenVINO proposal call replays the entire committed prefix.
- Verified 34-entry manifest and recovery-bundle integrity metadata.
- No headline discrepancy found.
- Elevated direct `C` semantics and state-interface cost as measured evidence.

### Round 6 — 2026-09-18 — unified formula / mechanism audit

- Corrected conflation between target-forward `PPk/PP1` and complete realized target-side round cost.
- Final accounting uses `R_target`; `V_k^micro` is mechanism diagnosis.
- Revised identity verified exactly on 358H arithmetic totals.
- M4 effective progress reconstruction retained as descriptive only, not direct `C`.

### Round 7 — 2026-09-18 — statistics / CI / aggregation audit

- Independently reproduced headline point estimates and bootstrap CIs for M4 HumanEval, M4 24Q, Windows exact HumanEval controls, and 358H CPU/NPU.
- Prompt is the bootstrap unit after within-prompt repetition reduction; no headline pseudoreplication found.
- Within-prompt estimators and resample counts differ by frozen study and must remain explicit.
- B570 exact-fallback CIs reproduced bit-for-bit when retained first-seen prompt order is replayed.
- CIs primarily reflect prompt sampling conditional on each campaign, not full system-state uncertainty.
- No statistical finding changes any headline sign or correctness-admissibility class.

### Round 8 — 2026-09-18 — correctness-contract audit

- Common paper meaning: deterministic greedy generated-token equality under frozen normalization; prompt/prefix excluded; first genuine generated-token divergence fails the pair/path.
- M4 final llama.cpp Q8_0 path is exact in frozen studies; earlier MLX-LM 4-bit failure remains historical evidence, not a contradiction.
- RTX default batched path correctness-blocked; serialized controls exact.
- B570 fast 45/90; serialized 60/90; small gate exactness does not imply workload-global exactness.
- 358H CPU/NPU each 90/90 exact.
- Functional HumanEval correctness is not claimed.

### Round 9 — 2026-09-18 — energy-boundary audit

- M4: Silemetry CPU+GPU+ANE package aggregate; separate DRAM excluded.
- RTX: NVIDIA board and Intel CPU package are separate domains and are not summed as calibrated whole-system energy.
- B570: Arc B570 board only.
- 358H: no end-to-end energy claim.
- Energy is secondary/appendix material; no cross-platform absolute ranking.

### Round 10 — 2026-09-18/19 — cross-platform claim / novelty audit

- Surviving claims: correctness filtering can remove physically cheap verification; realized stateful draft cost can diverge from isolated throughput; acceptance alone does not determine profitability; distinct regimes exist under tested conditions.
- Related work already includes heterogeneous speculative decoding and performance modeling; heterogeneous SD itself and generic cost algebra are not safe novelty claims.
- Final framing: audited correctness-constrained realized-cost cross-platform characterization.

### Stage D — runtime/software co-design audit

- No implementation added.
- Evidence-derived opportunities: persistent draft state, correctness-aware verification selection, workload-aware profitability control, adaptive proposal budget, realized-cost device selection.
- None is required to make current evidence scientifically valid; measured intervention could strengthen future systems novelty.

### Stage F — figure-policy audit

- Main figures should show realized-cost accounting, regime map, verification-path admissibility, 358H decomposition, M4 workload contrast.
- Energy only as sensor-boundary-separated small multiples.
- Never mix accepted draft tokens/round with direct `C` on an unlabeled common axis.

### Round 11 — adversarial reviewer audit

- Highest risks: novelty, confounded cross-platform comparison, HumanEval interpretation/cherry-picking, exactness contract, B570 terminology, 358H adapter/interface confound, energy comparability, model/platform scope, no runtime intervention.
- Final adversarial verdict: scientifically coherent if claims stay bounded; novelty risk dominates result-validity risk.

### Round 12 — final thesis / contribution freeze

- Scientific story frozen as correctness-constrained realized-cost characterization of when speculative decoding pays on tested consumer systems.
- Evidence hierarchy frozen: primary M4 24Q + M4 HumanEval + RTX exact controls + 358H Phase3; mechanism-supported M4/RTX/358H controls; B570 and exploratory controls diagnostic where specified.
- Hardware campaigns closed; headline statistics reproduced; correctness/energy terminology frozen.
- Remaining work: manuscript/figures and optional separately scoped co-design, not unresolved interpretation of existing hardware data.

### Round 1 revalidation — 2026-09-19 — repository-wide final-status / stale-document re-audit

- Main HEAD rechecked: `8de9642b3d27830ec182f3571974069d5b88d405`; unchanged from the audited Phase3 merge.
- PR #12 rechecked: merged=true; 358H Phase3 is on `main`.
- Existing audit PR #13 discovered/rechecked:
  - head branch `paper/audit-round1-20260918`;
  - base `main` at `8de9642...`;
  - branch was 12 commits ahead / 0 behind before this update;
  - it already contained the synchronized living-doc repairs and Rounds 1–12 handoff.
- Repository/status files inspected in this bounded pass:
  - `README.md` on main;
  - `REPO_STATUS.md` on main and audit branch;
  - `paper/mlsys2027/` listing;
  - `paper/notes/` listing;
  - `paper/mlsys2027/PAPER_FRAMEWORK_HANDOFF.md` on audit branch;
  - main `EVIDENCE_AUDIT_2026-09-18.md`, `WRITING_STATUS.md`, `README.md`, `OUTLINE.md`;
  - audit-branch synchronized evidence/status docs;
  - `reports/m4/M4_EXPERIMENT_INDEX.md`;
  - `reports/5070ti/FINAL_5070TI_PLATFORM_REPORT.md`;
  - `reports/b570/B570_PLATFORM_CLOSEOUT.md`;
  - `reports/358h/358H_PLATFORM_CLOSEOUT.md`;
  - recent commits and PR #12/#13 metadata.
- Findings:
  - **no new headline result/status drift** across the four platforms;
  - root README remains synchronized with final platform states;
  - the stale living docs still present on `main` are already corrected in PR #13, so no duplicate repair branch was created;
  - historical closeout reports with pre-merge process statements remain intentionally untouched;
  - current Skill availability changed materially: Data Analytics now exposes `validate-data` and `analyze-data-quality`, so old “no dedicated validation skill” wording was stale.
- Scientific conclusion changes from this revalidation: **none**.
- Tooling/process change: Stage-A capability record refreshed; `validate-data` and `analyze-data-quality` are now recognized as audit workflow aids, subordinate to frozen definitions/repository evidence.
- No new raw-data sweep was performed because Round 1 is intentionally status/staleness-bounded and deep platform audits already exist on this branch.
- No new experiment, parameter search, preregistration edit, raw-data edit, or historical-report rewrite was performed.

## 21. Next audit / work queue

All originally requested audit rounds are complete on this branch. Current recommended sequence, only when explicitly requested:

1. Re-run Skill/Plugin discovery for the next major stage.
2. Use this handoff as the scientific authority for manuscript drafting.
3. Produce figures only under the Section 10/Stage-F comparability constraints.
4. If runtime/software co-design is pursued, create a new scoped branch and preregistration; do not extend the closed hardware campaigns post hoc.
5. Before final submission/release, perform one final reviewer/adversarial re-audit and repository/publication hygiene pass.

No additional hardware experiment is authorized by this handoff.

---

Scientific stop rule: if later repository evidence contradicts any frozen synthesis here, update the Evidence Ledger and Decision Log explicitly. Do not preserve a preferred paper story at the expense of evidence.
