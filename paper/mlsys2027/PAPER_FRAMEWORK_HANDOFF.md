# HeteroSpec MLSys 2027 Paper Framework Handoff

> Role: scientific framework handoff / evidence ledger / paper architecture.  
> This file is the single source of truth for MLSys 2027 paper claims. It is not manuscript prose.  
> Scientific priority: **frozen experiment definitions and repository evidence > audit workflow > presentation quality**.

## 0. Handoff metadata

- Last updated: **2026-09-19**
- Target venue: **MLSys 2027 Research Track**
- Audited baseline: `main`
- Audited `main` HEAD: `5c8cc30284de2345d2056199cdeeffcad3da5599`
- Head meaning: merge of PR #13, `Paper: complete MLSys 2027 scientific audit (Rounds 1–12)`
- 358H closeout merge already contained in baseline: PR #12 / `8de9642b3d27830ec182f3571974069d5b88d405`
- Terminal audit branch: `paper/final-audit-20260919`
- Auditor: ChatGPT / GPT-5.6 Sol with connected GitHub repository tools, Data Analytics validation skills, direct statistical recomputation, and current public-literature search
- Hardware experiment phase: **CLOSED**
- Rounds 1–12 scientific audit: **COMPLETE and merged**
- Terminal revalidation scope: repository status, independent headline spot-recomputation, methodology/statistics consistency, correctness, energy, formula semantics, living-document drift, current novelty/related-work positioning, figure policy, and adversarial reviewer audit
- No new hardware experiment was designed or run.
- No raw experiment data, preregistration, failed run, or historical result report was rewritten to fit the paper story.
- Exact paper title wording remains **unfrozen**.

### 0.1 Current Skill / Plugin / tool discovery

Discovery was repeated at the requested major stages. The visible installed Skill catalog was stable during the terminal audit.

#### Visible Skills and advertised roles

| Skill | URI / family | Advertised role |
|---|---|---|
| analyze-data-quality | `skills://plugins/data-analytics/analyze-data-quality` | Structured-data trust: freshness, grain, missingness, duplicates, joins, schema drift, conflicting results. |
| build-dashboard | `skills://plugins/data-analytics/build-dashboard` | Source-backed interactive dashboards. |
| build-report | `skills://plugins/data-analytics/build-report` | Durable analytical reports backed by inspectable evidence. |
| convert-to-doc | `skills://plugins/data-analytics/convert-to-doc` | Convert a Data app to DOCX / Google Doc. |
| convert-to-slides | `skills://plugins/data-analytics/convert-to-slides` | Convert a Data app to PowerPoint / Google Slides. |
| create-data-context | `skills://plugins/data-analytics/create-data-context` | Reusable analysis context, conventions, definitions. |
| design-kpis | `skills://plugins/data-analytics/design-kpis` | KPI definitions, targets, guardrails, measurement plans. |
| gather-business-context | `skills://plugins/data-analytics/gather-business-context` | Gather connected/provided context before analysis. |
| index | `skills://plugins/data-analytics/index` | Router/index for Data analytical workflows. |
| jupyter-notebooks | `skills://plugins/data-analytics/jupyter-notebooks` | Reproducible Python/SQL notebooks and audit trails. |
| kpi-reporting | `skills://plugins/data-analytics/kpi-reporting` | KPI readouts / scorecards. |
| market-sizing | `skills://plugins/data-analytics/market-sizing` | Transparent TAM/SAM/SOM and opportunity sizing. |
| metric-diagnostics | `skills://plugins/data-analytics/metric-diagnostics` | Diagnose metric changes/anomalies/discrepancies. |
| product-business-analysis | `skills://plugins/data-analytics/product-business-analysis` | Metric-backed product/business decisions. |
| publish-artifact-to-sites | `skills://plugins/data-analytics/publish-artifact-to-sites` | Publish Data artifacts. |
| report-to-pdf | `skills://plugins/data-analytics/report-to-pdf` | PDF export for Data artifacts. |
| schedule-refresh-jobs | `skills://plugins/data-analytics/schedule-refresh-jobs` | Recurring Data refreshes. |
| share-artifact-summary | `skills://plugins/data-analytics/share-artifact-summary` | Summarize/share Data artifacts. |
| validate-data | `skills://plugins/data-analytics/validate-data` | Validate methodology, sources, calculations, visuals, conclusions, supported repairs. |
| visualize-data | `skills://plugins/data-analytics/visualize-data` | Design/revise/verify quantitative figures in durable artifacts. |
| Analytics Dashboard template | `skills://plugins/openai-templates/artifact-template-analytics-dashboard` | Analytics spreadsheet template. |
| Business Review template | `skills://plugins/openai-templates/artifact-template-business-review` | Business-review presentation template. |
| Design Report template | `skills://plugins/openai-templates/artifact-template-design-report` | Design-report document template. |
| Experiment Analysis template | `skills://plugins/openai-templates/artifact-template-experiment-analysis` | Experiment document template: hypothesis/method/results/limitations. |
| Financial Budget template | `skills://plugins/openai-templates/artifact-template-financial-budget` | Financial-budget spreadsheet template. |
| Investment Committee Memo template | `skills://plugins/openai-templates/artifact-template-investment-committee-memo` | Investment memo template. |
| Legal Memorandum template | `skills://plugins/openai-templates/artifact-template-legal-memorandum` | Legal memo template. |
| Market Trends Report template | `skills://plugins/openai-templates/artifact-template-market-trends-report` | Market-trends presentation template. |
| Minimal Letterhead template | `skills://plugins/openai-templates/artifact-template-minimal-letterhead` | Letter template. |
| Operating Calendar template | `skills://plugins/openai-templates/artifact-template-operating-calendar` | Operating-calendar spreadsheet template. |
| Operating Review template | `skills://plugins/openai-templates/artifact-template-operating-review` | Operating-review presentation template. |
| Project Kickoff template | `skills://plugins/openai-templates/artifact-template-project-kickoff` | Project-kickoff presentation template. |
| Project Tracker template | `skills://plugins/openai-templates/artifact-template-project-tracker` | Project-tracker spreadsheet template. |
| Sales Pipeline template | `skills://plugins/openai-templates/artifact-template-sales-pipeline` | Sales-pipeline spreadsheet template. |
| Simple Dark Mode template | `skills://plugins/openai-templates/artifact-template-simple-dark-mode` | Presentation template. |
| Simple Light Mode template | `skills://plugins/openai-templates/artifact-template-simple-light-mode` | Presentation template. |
| Strategy Memorandum template | `skills://plugins/openai-templates/artifact-template-strategy-memorandum` | Strategy memo template. |
| System Design template | `skills://plugins/openai-templates/artifact-template-system-design` | Architecture / API / tradeoff document template. |
| Team Alignment template | `skills://plugins/openai-templates/artifact-template-team-alignment` | Team-alignment presentation template. |
| Three-Statement Forecast template | `skills://plugins/openai-templates/artifact-template-three-statement-forecast` | Financial forecast spreadsheet template. |
| Template Creator | `skills://plugins/template-creator/template-creator` | Create/update reusable artifact templates. |
| Presentation router | `skills://plugins/presentations-router/presentation` | Explicit presentation routing only. |
| PDF router | `skills://plugins/pdf-router/pdf` | Explicit PDF routing only. |
| Document router | `skills://plugins/documents-router/document` | Explicit document routing only. |
| Plugin Management | `skills://plugins/plugin-management/plugin-management` | Discover/manage plugins and connections. |
| Spreadsheet router | `skills://plugins/spreadsheets-router/spreadsheet` | Explicit spreadsheet routing only. |

#### Relevant Skills inspected and audit boundary

| Skill | Full instructions inspected? | Used where | What it helps with | What it cannot establish |
|---|---|---|---|---|
| `validate-data` | Yes, including deep-review reference | Stage A / final validation | methodology/source/calculation/conclusion checks; evidence-vs-claim discipline | Git provenance, SHA identity, preregistration authority, novelty, unsupported causal claims |
| `analyze-data-quality` | Yes | Stage A / data-hygiene checks | stale/empty derivative detection, grain/source conflicts, lineage risks | claim admissibility, causal attribution, exactness without experiment evidence |
| `jupyter-notebooks` | Yes | Stage B/statistical workflow guidance | reproducible recomputation/audit trails | scientific authority beyond selected inputs and code |
| `visualize-data` | Yes | Stage F figure planning | quantitative figure truthfulness and design constraints | does not decide scientific novelty or evidence class |
| Experiment Analysis template | Yes | evaluated only | experiment-structure template | not a provenance/statistics/causal audit authority |
| System Design template | Yes | Stage D future-work framing only | runtime architecture/design organization | cannot retroactively validate closed experiments |

#### Plugin / repository capabilities

- GitHub connector: **installed and connected**, with read/write access to `leecdiang/HeteroSpec`.
- General Python computation: available and used for independent arithmetic/bootstrap spot-recomputation in the audit workflow.
- Plugin-directory candidates discovered but not required for the terminal audit:
  - Scite — literature/citation-context support; not installed.
  - Wolfram — mathematical/statistical computation; not installed.
  - Hugging Face — model/dataset metadata; not installed.
- Public literature was checked with current web sources where novelty/current publication status mattered.

#### Stage rediscovery log

- **Stage A — repository-wide final audit:** full current catalog checked; `validate-data` / `analyze-data-quality` used as workflow aids.
- **Stage B — statistics/CI:** catalog rechecked; no Skill superseded direct replay of frozen estimators/scripts.
- **Stage C — unified formula/mechanism:** catalog rechecked; no performance-model Skill superseded measured runtime semantics.
- **Stage D — runtime/software co-design:** system-design capability remains a future-design aid only.
- **Stage E — paper synthesis/novelty:** catalog rechecked; public literature search remained necessary because novelty depends on current publications.
- **Stage F — publication figures:** catalog rechecked; `visualize-data` constraints informed figure policy, but no final figures were generated.
- **Stage G — adversarial review:** catalog rechecked; no dedicated peer-review authority superseded evidence + current literature.

**Scientific authority remains:** frozen protocol/preregistration + repository evidence + independent recomputation + explicit uncertainty > Skill workflow > presentation.

## 1. Project status

### 1.1 Hardware study

**CLOSED.** No new hardware experiment is required to make the existing measurements scientifically interpretable.

| Platform | Final class | Terminal-audit interpretation |
|---|---|---|
| MacBook Air M4 / llama.cpp Metal | mixed workload regimes; closed | representative 24Q negative; separately preregistered HumanEval fixed-k2 exact and profitable |
| Core Ultra 9 275HX + RTX 5070 Ti Laptop / CUDA | correctness-admissible controls negative; closed | cheap raw batching exists but frozen exactness excludes it; serialized exact controls negative |
| Core i5-13400 + Arc B570 / Vulkan | no globally admissible tested optimization path; closed | fast path fails correctness; serialized fallback remains only 60/90 exact |
| Core Ultra X7 358H + Arc B390 target + CPU/NPU OpenVINO draft | exact but unprofitable; closed | CPU target-side bound; NPU realized state-interface/replay+proposal bound |

### 1.2 Software/runtime study

- No measured runtime intervention is part of the current contribution.
- Persistent draft state, correctness-aware path selection, online profitability control, adaptive `k`, and device selection remain future study opportunities.
- Any future intervention must be separately scoped/preregistered; it must not alter or reinterpret the closed hardware campaigns post hoc.

### 1.3 Paper status

- Rounds 1–12: complete and merged.
- Terminal revalidation: complete on `paper/final-audit-20260919` after the repairs logged below.
- Scientific thesis: **frozen for drafting**.
- Contribution ordering: **frozen for drafting**.
- Exact title wording: **not frozen**.
- Main novelty risk: **positioning**, not headline measurement validity.
- Manuscript prose / final figures: not produced by this audit.

## 2. Research question candidates

### Primary research question

> **When the execution path is filtered by a strict greedy token-equivalence contract, how do realized verification and state-interface costs determine whether speculative decoding pays on tested consumer systems?**

This is narrower and more defensible than “When is speculative decoding profitable?” in the abstract, because current literature already contains broad systematic SD performance studies and generic commit/cost decompositions.

### Supporting questions

- Can the physically fastest target-forward path be excluded by the frozen correctness contract?
- Can isolated draft-device throughput fail to predict realized end-to-end draft cost because the runtime reconstructs state?
- Which observed regimes remain after correctness and realized-state costs are made explicit?
- Which quantities are directly comparable across platforms, and which are only mechanism-specific diagnostics?

### Questions this paper does not answer

- Is strict token equality the only valid quality contract for speculative decoding? No; it is the frozen contract of this study.
- Which hardware architecture is intrinsically best for SD? Cross-platform hardware/software factors are confounded.
- Are NPUs, CUDA, Vulkan, Metal, or unified memory universally good/bad for SD? No.

## 3. Current leading thesis and title direction

### 3.1 Frozen scientific thesis

> **On the tested consumer systems, the profitable speculative-decoding path is determined by the execution path that remains admissible after the frozen correctness contract and by the costs realized through the actual state interface. Physically cheap target batching, high acceptance, or favorable isolated draft throughput can each fail to translate into end-to-end gains when correctness filtering changes the usable path or state reconstruction dominates the realized draft subsystem.**

This thesis is supported by four observed regimes:

1. **Profitable + exact:** M4 / llama.cpp Metal, separately preregistered HumanEval code-conditioned fixed-k2: 1.387x [1.351, 1.422], 90/90 exact.
2. **Exact but unprofitable:** M4 representative 24Q; RTX serialized HumanEval controls; 358H CPU/NPU.
3. **Physically fast but correctness-inadmissible:** RTX CUDA batched `ubatch=2`; B570 fast Vulkan path.
4. **State-interface bound:** 358H NPU, where full committed-prefix replay+proposal dominates realized draft cost despite favorable isolated NPU throughput.

### 3.2 Novelty boundary after current literature audit

Current literature materially constrains broad novelty claims:

- **Dovetail (arXiv:2412.18934, 2024):** heterogeneous CPU/GPU speculative decoding already exists.
- **DuoDecoding (arXiv:2503.00784, 2025):** hardware-aware heterogeneous CPU/GPU SD already exists.
- **Mirror Speculative Decoding (arXiv:2510.13161, 2025):** explicitly maps speculative work across GPU/NPU.
- **Speculative Decoding: Performance or Illusion? (MLSys 2026):** production-grade systematic SD study; verification dominance, workload variation, and theoretical upper bounds are already same-venue prior work.
- **Runtime-Controlled Evaluation of Speculative Decoding Methods (Electronics 2026):** explicitly decomposes speedup as `S = τ / c`, where `τ` is committed tokens/step and `c` is conditional execution cost. Therefore a generic commit/cost accounting identity is not novel.
- **Batch Speculative Decoding Done Right (arXiv:2510.22876, 2025):** correctness/output-equivalence failures and correctness-first batch SD are existing topics.
- **LLM-42 (arXiv:2601.17768, 2026)** and related numerical-reproducibility work: batch-size/dynamic-execution floating-point nondeterminism is not newly discovered here.
- **Give Me FP32 or Give Me Death? (arXiv:2506.09501, 2025):** system configuration/batch/GPU can alter greedy outputs through finite-precision non-associativity.
- **Speculation at a Distance (arXiv:2606.25091, 2026):** closed-form profitability conditions already exist for distributed speculative decoding.
- Recent draft-memory/KV-cache work further means that “state reuse” itself is not a novel idea; HeteroSpec's evidence is the measured state-interface failure mode on a consumer NPU path.

Therefore the paper must **not** claim novelty for:
- heterogeneous speculative decoding itself;
- the generic fact that acceptance alone is insufficient;
- generic verification-cost bottlenecks;
- the algebraic form of commit/cost accounting;
- batch-shape floating-point nondeterminism itself;
- persistent draft state / KV reuse as an idea.

The strongest differentiated contribution is:

> **cross-runtime empirical evidence that a strict correctness contract can change the usable execution path, combined with direct realized state-interface measurements showing how a nominally fast heterogeneous draft device can lose its isolated advantage end to end on consumer systems.**

### 3.3 Title candidates after novelty tightening

| Candidate | Evidence coverage | Novelty/positioning | MLSys fit | Main risk | Software contribution required? |
|---|---|---|---|---|---|
| A. *When Does Speculative Decoding Pay on Consumer Systems?* | high | weak-medium | good | overlaps strongly with MLSys 2026 broad performance study | no, but novelty attack is high |
| B. *Correctness-Constrained Speculative Decoding on Consumer AI PCs* | high | medium | good | “AI PCs” is awkward for M4; still broad | no |
| C. *Verification and State Reuse as the Hidden Bottlenecks of Speculative Decoding* | medium | weak-medium | medium | overstates “hidden”; state reuse is not implemented and prior work exists | likely yes to defend title |
| D. *HeteroSpec: A Cross-Platform Study of Correctness-Constrained Speculative Decoding* | high | medium | good | sounds benchmark/characterization-heavy | no |
| E. *HeteroSpec: Correctness-Admissible Paths and Realized Costs in Consumer Speculative Decoding* | **highest** | **strongest current direction** | **good** | phrase is less catchy; still must explain cross-stack confounding | no for scientific validity |

**Decision:** freeze the **title direction** around correctness-admissible paths + realized costs, but do not freeze exact wording before manuscript/figure integration.

## 4. Candidate contributions — frozen ordering

1. **Auditable cross-runtime characterization of correctness-admissible speculative-decoding regimes on four consumer systems.**
   - Positive, exact-negative, correctness-blocked, and state-interface-bound outcomes are preserved rather than filtered into one favorable story.
   - This is mechanism triangulation across heterogeneous stacks, not a controlled hardware leaderboard.

2. **Correctness-constrained realized-cost accounting discipline.**
   - Distinguishes complete realized round costs `D_real + R_target + X` from target-forward microbenchmark `V_k^micro`.
   - Distinguishes committed progress `C` from accepted draft tokens/round.
   - **Not claimed as novel algebra**; its contribution is disciplined use in this evidence chain.

3. **Within-platform evidence that correctness filtering can remove the physically cheapest verification path.**
   - RTX: near-one-step batched target-forward path exists but violates frozen token equivalence; exact serialized controls are negative.
   - B570: serialization itself does not guarantee global exactness.
   - This is not a claim that batch nondeterminism or correctness-first SD is newly discovered in general.

4. **Direct evidence that the realized state interface can erase isolated draft-device advantage.**
   - 358H NPU proposal calls reconstruct the complete committed prefix; replay+proposal is 58.35% of measured speculative time.
   - CPU remains target-side dominated.
   - The claim is interface-specific, not a verdict on NPU compute capability.

5. **A separately preregistered workload-conditioned profitable regime retained beside a representative negative result.**
   - M4 HumanEval fixed-k2 positive.
   - M4 representative 24Q negative.
   - This is evidence for regime dependence and selective deployment, not “M4 generally wins.”

Artifact/provenance quality is a supporting strength, not a standalone scientific novelty claim.

## 5. Unified analytical framework

### 5.1 Final realized-round accounting

For one speculative round under a consistent measurement boundary:

```text
S_round =
    T_b * C
    -------------------------------------------
    T_d(real) + T_target,round(real) + T_x
```

Normalized by one matched baseline target-token cost `T_b`:

```text
S_round = C / [D_real + R_target + X]
```

Break-even:

```text
C > D_real + R_target + X
```

Definitions:

- `T_b`: matched target-only baseline cost per output token under the same timing boundary.
- `T_d(real)`: realized draft-subsystem cost through the actual runtime state interface. It includes replay/reconstruction when the actual execution performs it.
- `T_target,round(real)`: **complete realized target-side work per speculative round**, including proposal verification and target correction/bonus behavior inside that runtime's measured round semantics.
- `T_x`: residual cost not already included above.
- `C`: all output tokens committed by the round, including correction/bonus behavior.
- `D_real = T_d(real)/T_b`.
- `R_target = T_target,round(real)/T_b`.
- `X = T_x/T_b`.

This is an accounting identity at a specified aggregation level. It is not claimed as a new theoretical model, and it does not imply every platform exposes every component directly.

### 5.2 Target-forward microbenchmark proxy

Separately define:

```text
V_k^micro(n,e) =
    T_target_forward(k,n,e)
    -----------------------
    T_target_decode(1,n)
```

where `n` is context/depth and `e` is an execution path.

`V_k^micro` is a **batching opportunity / mechanism proxy**. It answers whether a target backend can process a width-`k` causal block near the cost of one target decode. It must not be silently substituted for complete `R_target` unless the measurement boundary proves that it includes all realized target-side round work.

Correctness acts as a gate on path admissibility:
- a physically fast path that fails the frozen token-equivalence contract is not an admissible optimization path for this study;
- serialization is not synonymous with exactness;
- if no tested path is globally exact for the frozen workload, no globally correctness-admissible performance claim exists.

### 5.3 Why the distinction is required by repository evidence

| Platform/path | `V_2^micro` evidence | Correctness meaning | End-to-end accounting meaning |
|---|---|---|---|
| M4 Metal | ≈1.02–1.08 | final tested llama.cpp path exact in frozen cells | cheap target-forward opportunity; complete `R_target` not directly exposed by historical microbench |
| RTX CUDA batched ub2 | ≈0.98–1.01 | correctness-blocked | physically cheap but inadmissible path |
| RTX CUDA serialized ub1 | ≈2.14–2.43 | exact control | expensive target-forward control; not automatically complete `R_target` |
| B570 Vulkan serialized ub1 | ≈1.98–1.99 | only 60/90 exact | diagnostic serialized proxy only; no globally admissible result |
| 358H CPU/NPU | do not substitute isolated Phase-2 V2 for Phase-3 `R_target` | both 90/90 exact | Phase 3 directly times complete target-side region and realized draft-state interface |

### 5.4 358H direct realized accounting

Using Phase-3 arithmetic totals:

| Path | `C` | `D_real` | `R_target` | `X` | `C/(D+R+X)` | Aggregate baseline/spec ratio |
|---|---:|---:|---:|---:|---:|---:|
| CPU draft | 2.4631 | 0.4304 | 2.9767 | 0.00124 | 0.7227 | 0.7227 |
| NPU draft | 2.4584 | 4.1251 | 2.9435 | 0.00130 | 0.3477 | 0.3477 |

The identity reproduces ratio-of-total-times exactly at the same aggregation level. It is **not expected** to equal the preregistered prompt-level geometric-mean speedups 0.734x and 0.352x.

Runner inspection additionally establishes:
- OpenVINO proposal generation receives the entire committed prefix every round;
- replay/reconstruction plus proposal is therefore genuinely inside `T_d(real)`;
- target timing includes proposal evaluation, invalid-suffix rollback when required, and correction/bonus target decode.

### 5.5 Committed progress versus accepted draft tokens

- 358H directly records `C`: 2.4631 CPU and 2.4584 NPU.
- Historical M4/RTX `accepted_per_round` counts accepted **draft** tokens and is not `C`.
- M4 allows only a boundary-affected reconstructed effective progress from runtime counters; it remains descriptive and is not promoted to the same evidence class as direct 358H round traces.
- Do not plot direct `C` and historical accepted-draft-tokens/round as one unlabeled common metric.

### 5.6 Phase-2 versus Phase-3 358H interpretation

Phase 2 used a favorable predictive eligibility model with isolated draft cost, target-forward verification proxy, and `T_x=0` to classify CPU/NPU context points as BORDERLINE under central `C=2` and optimistic `C=3` scenarios.

Phase 3 observed `C≈2.46` but remained negative because the **realized stateful draft call** and **complete target-side round cost** are materially larger than the Phase-2 proxies assumed.

Safe interpretation:
- Phase 2 was an entry/eligibility screen, not a validated end-to-end speed predictor;
- the Phase2→Phase3 gap supports the need to measure `T_d(real)` and complete `R_target`;
- do not present the gap as a failed preregistered prediction or as proof that the accounting identity is wrong.

### 5.7 Formula complexity decision

Keep `T_d(real)` aggregated in the unified framework. Do not invent separate replay, reconstruction, rollback, transfer, or correction variables where frozen execution did not measure them independently.

## 6. Platform regime map

### 6.1 M4 / llama.cpp Metal

- Representative frozen Spec-Bench 24Q:
  - speedup **0.841965x**;
  - 95% prompt-bootstrap CI **[0.808693, 0.876765]**;
  - 72/72 exact;
  - 1/24 prompts faster;
  - package-efficiency ratio **0.677507x** (worse than baseline because ratio is baseline/speculative J/token).
- Separately preregistered HumanEval30 fixed-k2:
  - speedup **1.387352x**;
  - 95% CI **[1.350574, 1.421625]**;
  - 90/90 exact;
  - 30/30 prompts faster;
  - mean acceptance ≈0.90070;
  - accepted draft tokens/round ≈1.79833.
- Fixed-k2 HumanEval package-efficiency ratio:
  - point estimate **1.012951x**;
  - 95% CI **[0.989567, 1.034071]**;
  - interpretation: **energy-neutral within uncertainty**.
- Registered secondary `p_min=0.9`:
  - speedup ≈1.395596x;
  - package-efficiency ratio ≈1.041018x [1.018006, 1.064502].
- Corrected synthetic ceiling: **NOT EXECUTED** under the preregistered design.

Safe claim: an exact profitable **code-conditioned** regime exists; representative 24Q did not generalize it. Do not claim general M4 profitability or unified-memory causality.

### 6.2 RTX 5070 Ti Laptop / llama.cpp CUDA

- Exact serialized HumanEval controls:
  - CPU→RTX: **0.403937x [0.390402, 0.417988]**, 90/90 exact, 0/30 faster, acceptance ≈0.91307.
  - RTX→RTX: **0.650079x [0.628958, 0.673417]**, 90/90 exact, 0/30 faster, acceptance ≈0.91207.
- Target-forward mechanism:
  - batched `ubatch=2`: `V_2^micro≈1.0090` at depth 0, `≈0.9831` at 256; correctness-blocked.
  - serialized `ubatch=1`: `≈2.4310` and `≈2.1370`; exact control.
- Stable divergence capture:
  - HumanEval/106 first divergence repeats 3/3 at the same captured position;
  - baseline/serialized token 2790 vs batched token 2629;
  - score margin +0.080948 → -0.126457.
- Same-GPU placement improves performance relative to CPU→RTX but remains <1, so transfer/synchronization is material but not the sole explanation.
- HumanEval serialized follow-up does not provide an admissible formal energy comparison.
- Raw per-run Git provenance is weaker than other platforms because some authoritative run JSONs were historically local/ignored; committed derived tables/mechanism captures remain sufficient for headline recomputation.

Safe claim: in the frozen llama.cpp/CUDA/Q8_0 stack, the cheap batched path can change greedy argmax and is inadmissible under the token-exact contract; tested exact controls are decisively negative. Do not identify a universal CUDA defect or a specific kernel cause.

### 6.3 Arc B570 / llama.cpp Vulkan

- Formal v2 correctness gate: FAIL; preregistered stop rule prohibits promoting a formal V2/performance result from that run.
- Later diagnostic fast path: 45/90 exact pairs.
- Unique frozen serialized fallback:
  - 60/90 exact pairs;
  - 20/30 wholly exact prompts;
  - global admissible=false;
  - diagnostic speedup **0.308682x [0.292690, 0.324604]**;
  - 0/30 prompts faster;
  - exact-subset descriptive GM ≈0.302574x;
  - serialized `V_2^micro≈1.982668 / 1.991707` at context 512/2048;
  - Arc-board efficiency ratio **0.302276x [0.284553, 0.320160]**;
  - baseline mean ≈5.602 vs fallback ≈18.850 board J/token.

Safe claim: no tested B570 path is a globally correctness-admissible optimization result. Historical `V2_exact` field names remain provenance; paper-facing term is `V2_serialized` / serialized `V_2^micro`.

### 6.4 Core Ultra X7 358H + Arc B390 Vulkan target + OpenVINO CPU/NPU draft

- Stage-A gate: CPU 18/18 exact; NPU 18/18 exact.
- HumanEval30:
  - CPU **0.733915x [0.692920, 0.771090]**, 90/90 exact, 0/30 faster.
  - NPU **0.351663x [0.332595, 0.368949]**, 90/90 exact, 0/30 faster.
- Acceptance / committed progress:
  - CPU weighted acceptance 0.753054; `C=2.463117`.
  - NPU weighted acceptance 0.751319; `C=2.458387`.
- Decomposition:
  - CPU: replay+proposal 12.627%; target-side 87.336%; residual 0.036%.
  - NPU: replay+proposal 58.347%; target-side 41.634%; residual 0.018%.
- Isolated draft characterization includes contexts where NPU steady-state throughput is competitive with or above CPU, yet the realized NPU proposal call is much more expensive because the complete prefix is replayed through the current state interface.
- End-to-end Phase-3 energy: CPU **NOT CLAIMED**; NPU **NOT ADMISSIBLE**.
- Reconstructed source identity: `STRONGLY_SUPPORTED`, never proven exact historical upstream identity.

Safe claim: the current OpenVINO/state interface erases the isolated NPU draft-throughput advantage through full-prefix replay+proposal. Do not generalize to NPU hardware.

## 7. Claim taxonomy

| Claim ID | Candidate wording | Status | Platforms | Supporting evidence | Limitations / reviewer risk | Paper placement |
|---|---|---|---|---|---|---|
| C-M4-01 | A separately preregistered exact profitable fixed-k2 regime exists on M4 for the frozen HumanEval code-conditioned workload. | PRIMARY | M4 | 1.387x [1.351,1.422], 90/90 exact, 30/30 faster | workload-conditioned; no pass@k | Results |
| C-M4-02 | The representative frozen 24Q M4 study is negative. | PRIMARY | M4 | 0.842x [0.809,0.877], 72/72 exact | workload mix differs from HumanEval | Results / anti-cherry-pick evidence |
| C-M4-ENERGY-01 | Fixed-k2 HumanEval package energy is neutral within uncertainty. | SECONDARY | M4 | efficiency 1.013x [0.990,1.034] | sensor is package aggregate; gate used point estimate | Results/Limitations |
| C-RTX-01 | In the frozen llama.cpp/CUDA/Q8_0 stack, the fast batched target-forward path can change greedy argmax and is inadmissible under the token-exact contract. | MECHANISM_SUPPORTED | RTX | stable HumanEval/106 divergence + margin sign flip | bounded path/config/case; not new generic nondeterminism | Results |
| C-RTX-02 | The tested serialized exact-control target-forward proxy is ≈2.14–2.43 baseline target decodes. | MECHANISM_SUPPORTED | RTX | `WINDOWS_EXACT_VERIFICATION_COST.csv` | `V_2^micro`, not complete `R_target` | Mechanism |
| C-RTX-03 | Exact CPU→RTX and RTX→RTX HumanEval controls are unprofitable. | SECONDARY | RTX | 0.404x / 0.650x, both 90/90 | controls are serialized and implementation-bounded | Results |
| C-B570-01 | Fast and serialized B570 paths both fail workload-global token equivalence. | DIAGNOSTIC | B570 | 45/90 and 60/90 | post-gate diagnostics; frozen backend/config | Results/Limitations |
| C-B570-02 | No tested B570 path supports a correctness-admissible optimization claim. | SECONDARY | B570 | formal stop + diagnostic fallback | does not imply Vulkan universally fails | Results |
| C-358H-01 | CPU and NPU 358H paths are exact but unprofitable in frozen Phase 3. | PRIMARY | 358H | 0.734x / 0.352x; each 90/90 exact | post-prefill timing boundary | Results |
| C-358H-02 | Realized full-prefix replay+proposal dominates the tested NPU draft subsystem. | MECHANISM_SUPPORTED | 358H NPU | 58.35% of speculative time; runner passes full prefix | interface-specific; replay/proposal inseparable | Results/Discussion |
| C-358H-03 | CPU Phase3 is target-side dominated. | MECHANISM_SUPPORTED | 358H CPU | target-side region 87.34% | complete runner boundary; not micro V2 | Results |
| C-XP-01 | A strict correctness contract can change which physically available verification path is admissible. | MECHANISM_SUPPORTED | RTX, B570; M4 contrast | cheap inadmissible vs exact/serialized paths | related work has correctness-first SD; novelty is evidence/context, not concept firstness | Intro/Discussion |
| C-XP-02 | Isolated draft throughput is not sufficient to represent realized draft subsystem cost under a state-reconstructing interface. | MECHANISM_SUPPORTED | 358H | isolated NPU vs Phase3 realized call | bounded OpenVINO adapter | Intro/Discussion |
| C-XP-03 | Tested consumer systems occupy multiple correctness/cost regimes rather than one platform-wide outcome. | MECHANISM_SUPPORTED | all | cross-platform regime map | mechanism triangulation, not hardware causality | Intro/Discussion |
| C-ACC-NEW | “Acceptance is insufficient” is a novel contribution. | NOT_SUPPORTED | all | prior literature already establishes related cost/acceptance interactions | novelty overlap | Never as novelty |
| C-FORMULA-NOVEL | The `C/cost` accounting identity is a novel theory. | NOT_SUPPORTED | all | SpecLLM uses `S=τ/c`; other analytical work exists | high novelty overlap | Never as novelty |
| C-M4-CAUSE-UM | Unified memory causes the M4 profitable regime. | PLAUSIBLE_NOT_CAUSAL | M4 | compatible with implementation | no isolated control | Never causal |
| C-CUDA-BROKEN | CUDA is broken for speculative decoding. | FORBIDDEN_OVERCLAIM | RTX | contradicted by bounded evidence scope | universal/backend-loaded claim | Never |
| C-VULKAN-BROKEN | Vulkan cannot do exact speculative decoding. | FORBIDDEN_OVERCLAIM | B570 | one frozen stack only | universal backend claim | Never |
| C-NPU-SLOW | NPU compute is too slow / NPUs are unsuitable for SD. | FORBIDDEN_OVERCLAIM | 358H | isolated throughput contradicts framing | measured issue is state interface | Never |
| C-HE-FUNC | HumanEval token exactness establishes functional correctness/pass@k. | FORBIDDEN_OVERCLAIM | HumanEval studies | code not executed | metric substitution | Never |
| C-ENERGY-RANK | Current J/token values rank platforms on energy efficiency. | FORBIDDEN_OVERCLAIM | all | sensor domains differ | invalid boundary comparison | Never |
| C-M4-GENERAL | Speculative decoding generally works on M4. | FORBIDDEN_OVERCLAIM | M4 | representative 24Q is negative | workload-conditioned positive only | Never |
| C-B570-EXACT | The B570 serialized fallback is globally exact. | FORBIDDEN_OVERCLAIM | B570 | only 60/90 pairs exact | historical field name is misleading at global scope | Never |
| C-SYNTH-DONE | The M4 corrected synthetic ceiling was completed. | FORBIDDEN_OVERCLAIM | M4 | no matching artifact | prereg deviation | Never |

## 8. Evidence ledger

### 8.1 Headline evidence

| Evidence ID | Platform / experiment | Class | Metric / value | CI / reps | Correctness | Workload/runtime | Primary source(s) | Provenance / caveat | Paper use |
|---|---|---|---|---|---|---|---|---|---|
| E-M4-24Q-01 | M4 representative 24Q | PRIMARY | 0.841965x | [0.808693,0.876765], 24×3 | 72/72 exact | Spec-Bench 24Q; Q8_0; Metal k2 | `reports/m4/M4_CONFIRMATORY_VALIDATION.md`; `analysis/m4_confirmatory_*` | independently recomputed | representative negative |
| E-M4-HE30-01 | M4 HumanEval fixed-k2 | PRIMARY | 1.387352x | [1.350574,1.421625], 30×3 | 90/90 exact | HumanEval30; Q8_0; Metal | `reports/m4/M4_HUMANEVAL_CODE_CONDITIONED.md`; authoritative archive | independently replayed 100k bootstrap | conditioned positive |
| E-M4-HE30-ENERGY-01 | M4 HE fixed-k2 package energy | SECONDARY | 1.012951x efficiency | [0.989567,1.034071] | exact path | same | M4 HE summary/raw telemetry | neutral within uncertainty; package boundary | energy wording |
| E-M4-PMIN09-ENERGY-01 | M4 p_min=.9 energy | SECONDARY | 1.041018x | [1.018006,1.064502] | 90/90 exact | registered secondary | same | not replacement for primary fixed-k2 | secondary |
| E-RTX-HE30-CPU-01 | CPU→RTX serialized exact control | SECONDARY | 0.403937x | [0.390402,0.417988], 30×3 | 90/90 exact | HumanEval30; CUDA ub1 | `reports/5070ti/windows_humaneval_summary.json` | derived table committed; some raw JSON local/ignored | exact negative |
| E-RTX-HE30-GPU-01 | RTX→RTX serialized exact control | SECONDARY | 0.650079x | [0.628958,0.673417], 30×3 | 90/90 exact | same | same | same provenance limitation | exact negative |
| E-RTX-V2-RAW-01 | CUDA batched target-forward | DIAGNOSTIC | 1.0090@0; 0.9831@256 | 20 reps/cell | correctness-blocked | ubatch2 | `WINDOWS_EXACT_VERIFICATION_COST.csv` | `V_2^micro` only | fastest physical path |
| E-RTX-V2-SER-01 | CUDA serialized target-forward | MECHANISM_SUPPORTED | 2.4310@0; 2.1370@256 | 20 reps/cell | exact control | ubatch1 | same | `V_2^micro`, not complete round | correctness cost |
| E-RTX-DIV-01 | CUDA divergence capture | MECHANISM_SUPPORTED | margin +0.080948 → -0.126457; 2790→2629 | 3/3 | demonstrates divergence | HumanEval/106 | `CUDA_DIVERGENCE_*` | one stable config/case; mechanism bounded | numerical evidence |
| E-B570-FAST-01 | B570 fast path | DIAGNOSTIC | 0.5383x; V2 1.2426/1.6373 | diagnostic workload | 45/90 exact | Vulkan | B570 diagnostic reports | correctness-blocked | mechanism only |
| E-B570-SERIAL-01 | B570 serialized fallback | DIAGNOSTIC | 0.308682x; V2 1.982668/1.991707 | [0.292690,0.324604] | 60/90 exact | Vulkan ubatch1 | `B570_EXACT_FALLBACK_VALIDATION.md`; `analysis/b570_exact_fallback_*` | global admissible=false; archive complete | serialized boundary |
| E-B570-ENERGY-01 | B570 fallback board energy | DIAGNOSTIC | efficiency 0.302276x | [0.284553,0.320160] | non-admissible path | Arc board | same | board only, diagnostic | appendix only |
| E-358H-P3-CPU-01 | 358H CPU Phase3 | PRIMARY | 0.733915x | [0.692920,0.771090], 30×3 | 90/90 exact; gate18/18 | Vulkan0 + OpenVINO CPU | `358H_PHASE3_END_TO_END_VALIDATION.md`; `analysis/358h_phase3_summary.json` | post-prefill; archive 34/34 | exact negative |
| E-358H-P3-NPU-01 | 358H NPU Phase3 | PRIMARY | 0.351663x | [0.332595,0.368949], 30×3 | 90/90 exact; gate18/18 | Vulkan0 + OpenVINO NPU | same | post-prefill; no admissible energy | exact negative |
| E-358H-DECOMP-CPU-01 | CPU decomposition | MECHANISM_SUPPORTED | draft12.63%, target87.34%, residual0.04% | 90 requests | exact | Phase3 | `analysis/358h_phase3_decomposition.csv` | arithmetic ratio-of-totals | target-side bound |
| E-358H-DECOMP-NPU-01 | NPU decomposition | MECHANISM_SUPPORTED | draft58.35%, target41.63%, residual0.02% | 90 requests | exact | Phase3 | same + runner | full-prefix proposal semantics | state-interface bound |
| E-358H-C-01 | committed progress | MECHANISM_SUPPORTED | CPU2.463117; NPU2.458387 | all formal rounds | exact | Phase3 | summary + rounds CSV | direct C, not accepted/round | accounting |
| E-358H-ARCHIVE-01 | archive integrity | SECONDARY | 34/34 entries, zero failures | closeout | n/a | Phase3 | repository closeout audit | recovery tar SHA256 retained | reproducibility |

### 8.2 Statistical audit ledger

| Study | Within-prompt estimator | Bootstrap unit | Resamples / seed | Terminal verdict |
|---|---|---|---|---|
| M4 HumanEval | GM of 3 paired ratios | prompt | 100,000 / 20260910 | point/CI reproduced exactly |
| M4 24Q | GM of 3 paired ratios | prompt | 10,000 / 20260907 | point/CI reproduced exactly |
| RTX HumanEval | GM of 3 paired ratios | prompt | 10,000 / 20260910 | prior independent recomputation retained; data unchanged |
| B570 fallback | prompt GM from pair data | prompt | 10,000 / 20260910 | point estimates rechecked; prior bit-level CI replay depends on retained input order |
| 358H Phase3 | median of 3 paired ratios | prompt | 10,000 NumPy / 20260919 | summary/script semantics rechecked; primary vector unchanged |

No headline pseudoreplication was found. Do not post-hoc homogenize estimators or bootstrap implementations. CIs primarily represent prompt-sampling uncertainty conditional on each frozen campaign, not complete session/thermal/runtime uncertainty.

## 9. Cross-platform comparison table

| Regime | Correctness-admissible end-to-end result? | Profitability | Main evidence-supported mechanism | Critical caveat |
|---|---|---|---|---|
| M4 24Q k2 | Yes | No, 0.842x | cheap exact target-forward path exists, but this workload remains negative | not evidence M4 never works |
| M4 HumanEval k2 | Yes | Yes, 1.387x | exact cheap batching opportunity + favorable workload/runtime regime | no functional pass@k; do not claim causal predictability |
| RTX CUDA batched | No | no admissible speed claim | cheap target-forward batching physically exists but changes greedy argmax on frozen case | config/path bounded |
| RTX serialized exact controls | Yes | No, 0.404x / 0.650x | admissible target-forward control near-serialized; draft/integration costs remain | `V_2^micro` not complete `R_target` |
| B570 Vulkan fast | No | diagnostic only | correctness failure | 45/90 exact |
| B570 serialized fallback | No globally | diagnostic 0.309x | serialization costs ~2× and still does not guarantee exactness | 60/90 exact; board-energy diagnostic only |
| 358H CPU | Yes | No, 0.734x | complete target-side work 87.34% | post-prefill boundary |
| 358H NPU | Yes | No, 0.352x | realized full-prefix replay+proposal 58.35% | current state interface, not universal NPU claim |

Cross-platform comparison is a **regime/mechanism comparison**, not a controlled hardware ranking.

## 10. Figure plan

### Main-paper priority

| Figure ID | Question answered | Source data | Structure | Evidence class | Main risk / rule |
|---|---|---|---|---|---|
| F1 | What must be measured after correctness filtering? | framework + 358H realized decomposition | schematic showing correctness gate, `D_real`, complete `R_target`, `X`, `C`; `V_k^micro` as diagnostic inset | framework/mechanism | label accounting identity, not new theory |
| F2 | Is the M4 positive result representative? | M4 24Q + HumanEval prompt summaries | two-condition workload contrast with CIs and exactness | PRIMARY | show chronology/preregistration; never hide 24Q negative |
| F3 | How can correctness change the usable target-forward path? | M4/RTX/B570 mechanism controls | path-specific `V_2^micro` with correctness/admissibility markers | MECHANISM/DIAGNOSTIC | contexts/stacks differ; not a hardware leaderboard; B570 serialized not exact |
| F4 | Why does isolated NPU draft speed not survive end to end? | 358H Phase1 draft summary + Phase3 decomposition | 2-panel isolated draft throughput vs realized draft/target/residual cost | PRIMARY/MECHANISM | different measurement boundaries clearly labeled; interface-specific |
| F5 | What regimes exist across the study? | headline ledger | categorical regime map/table, not a quantitative ranking | mixed | encode evidence/correctness class explicitly |

### De-prioritized from main paper

- Generic acceptance-vs-speedup cross-platform scatter: **do not use as a central figure**. Definitions differ (`C` vs accepted draft tokens), and current literature already establishes that commit/acceptance alone does not determine speedup.
- Global absolute energy chart: **forbidden** because sensor boundaries differ.

### Appendix-only figure policy

- Energy small multiples, each with explicit sensor boundary.
- B570 mismatch/diagnostic distributions.
- CUDA divergence detail.
- Statistical/provenance supplemental plots if space is useful.

## 11. Table plan

| Table ID | Purpose | Required provenance / rule |
|---|---|---|
| T1 | Platform/runtime/model/timing/correctness-contract matrix | frozen configs + final reports; always `RTX 5070 Ti Laptop` |
| T2 | Headline outcomes with evidence class and exactness/admissibility | evidence ledger; B570 diagnostic status visible |
| T3 | Mechanism quantities (`V_k^micro`, direct `C`, realized state cost, residual) | leave N/A rather than force incomparable definitions |
| T4 | Statistical estimator/bootstrap policy by campaign | script/preregistration; explicitly show differences |
| T5 | Energy boundary and allowed interpretation | never merge package/board/component/no-boundary measurements |

## 12. Runtime/software design opportunities

These are future design requirements derived from measured bottlenecks, not current contributions.

| Opportunity | Measured bottleneck addressed | Platform evidence | Expected benefit | Difficulty | Experimental requirement | Scope risk | Needed for current validity? |
|---|---|---|---|---|---|---|---|
| correctness-qualified verification-path selection | fastest physical path may violate exactness | RTX, B570 | select cheapest path satisfying chosen contract | medium | new implementation + preregistered validation | medium | no |
| persistent draft state / KV reuse / rollback | full-prefix replay dominates realized NPU draft cost | 358H NPU | reduce `T_d(real)` | high | separate co-design study | high | no |
| online profitability controller | workload-conditioned M4 result | M4 24Q vs HumanEval | avoid speculation in negative regimes | medium | new prospective study | medium | no |
| adaptive `k` | deeper proposal can increase cost/reduce acceptance | M4/RTX pilot/mechanism | adapt progress/cost tradeoff | medium | new study | medium-high | no |
| realized-cost device selection | isolated fastest device may not minimize end-to-end cost | RTX draft characterization + 358H | select CPU/NPU/iGPU by realized stateful cost | high | new study | high | no |

Novelty warning: state reuse, adaptive proposal control, and hardware-aware SD already have substantial prior art. A future software contribution would need a measured differentiator, not merely implementation of a known idea.

## 13. Reviewer attack list

| Concern | Severity | Evidence available | Response direction | Extra experiment needed by default? | Explicit limitation? |
|---|---|---|---|---|---|
| MLSys 2026 already has a systematic SD performance study. | **CRITICAL novelty** | current literature audit | do not claim first systematic profitability study; emphasize correctness-admissible path changes + consumer heterogeneous state-interface evidence | no for validity; software intervention could strengthen novelty | yes |
| `S=τ/c` / commit-vs-cost decomposition already exists. | **HIGH novelty** | 2026 runtime-controlled evaluation | present our equation as audited accounting discipline with direct component measurement where available, not new algebra | no | yes |
| Correctness-first/batch output-equivalence work already exists. | HIGH novelty | Batch SD Done Right; deterministic inference work | claim concrete impact on tested speculative path, not first correctness concern | no | yes |
| Batch shape / finite precision nondeterminism is already known. | HIGH novelty | LLM-42; FP32/reproducibility work | our contribution is frozen path consequence + exact verification-control evidence, not phenomenon firstness | no | yes |
| Heterogeneous SD already exists. | HIGH novelty | Dovetail, DuoDecoding, Mirror-SD | explicitly agree; no algorithmic-firstness claim | no | yes |
| Four platforms / narrow model family cannot generalize. | HIGH | four closed stacks | claim observed regimes and requirements, not universal hardware/model law | no | yes |
| Cross-platform stacks are confounded. | HIGH | within-platform controls + bounded synthesis | mechanism triangulation only; causal claims remain within platform | no | yes |
| M4 HumanEval is cherry-picked after 24Q failed. | HIGH | separate preregistration/frozen IDs; 24Q retained | show chronology and both results prominently; existence/workload-conditioned claim only | no | yes |
| HumanEval code was never functionally executed. | HIGH | explicit protocol | describe HumanEval as structured generation workload; exactness is token equality, not pass@k | no | yes |
| Strict token equality is an arbitrary/too-strong contract. | MEDIUM-HIGH | frozen deterministic contract | motivate as deterministic reference equivalence for this study; looser quality contracts are valid future work | no | yes |
| M4 primary prereg energy gate uses point estimate but CI crosses 1. | MEDIUM-HIGH | prereg + 100k bootstrap | state gate criterion honestly; call primary energy neutral within uncertainty, not a robust win | no | yes |
| CUDA divergence is one near-tie edge case. | HIGH | 3/3 stable capture + primary gate impact | bound claim to frozen stack; do not infer universal backend/kernel defect | no | yes |
| B570 six-prompt serialized gate passed but full workload failed. | HIGH if hidden | 18/18 gate then 60/90 full | use as evidence that small gates cannot establish workload-global exactness; never call serialized path exact by construction | no | yes |
| 358H NPU loss is just a poor adapter. | HIGH | runner semantics + decomposition | agree with bounded interpretation: this is the measured state-interface result | no | yes |
| Why not implement persistent state reuse and show a win? | HIGH for systems novelty | direct NPU bottleneck identified | scientifically not required to validate current characterization; may strengthen acceptance if separately implemented/preregistered | optional future | yes |
| Phase2 predicted borderline/optimistic opportunity but Phase3 lost badly. | MEDIUM-HIGH | Phase2 summary + Phase3 direct accounting | Phase2 was an eligibility/favorable-bound screen using proxies; Phase3 demonstrates why realized costs matter | no | yes |
| Energy numbers are incomparable. | HIGH | boundary audit | no absolute cross-platform ranking; appendix small multiples only | no | yes |
| Windows raw run logs are not fully in Git. | MEDIUM | committed pair tables/manifests/mechanism captures | disclose evidence tier; headline recomputed from committed derived data | no | yes |
| Prompt bootstrap ignores full session/thermal/system-state uncertainty. | MEDIUM-HIGH | repetition drift / protocol review | state CI estimand; do not overstate general system variance coverage | no | yes |
| No production serving engine / batch-load study. | MEDIUM-HIGH | scope is batch1 consumer characterization | contrast with MLSys 2026/SpecLLM; do not compete on production-serving coverage | no | yes |
| This is “only a benchmark paper.” | **HIGH acceptance risk** | mechanisms + prereg + direct state/correctness evidence | center paper on two measured systems mechanisms and bounded design requirements; avoid leaderboard structure | optional software contribution can strengthen | yes |

### Adversarial verdict

**Measurement validity:** strong within the stated boundaries.  
**Scientific coherence:** strong after the `V_k^micro` / `R_target` correction and explicit evidence classes.  
**Primary acceptance risk:** novelty/positioning and lack of a measured software intervention, not a discovered headline numerical error.

## 14. Known limitations

1. HumanEval generated code was not executed for functional pass@k; “exact” means generated token-ID equality.
2. Energy boundaries differ by platform and cannot be compared as one calibrated domain.
3. M4 unified memory is not isolated as a causal factor.
4. CUDA batch-shape argmax flip is a bounded frozen-stack observation, not “CUDA is broken.”
5. B570 results are backend/configuration bounded; serialized fallback is not universally exact.
6. 358H NPU result is an end-to-end result of the current OpenVINO/state interface, not a universal NPU verdict.
7. 358H reconstructed draft source is `STRONGLY_SUPPORTED`, not proven exact historical upstream identity.
8. M4 preregistered corrected synthetic ceiling was not completed.
9. Cross-platform comparisons change hardware and software simultaneously; hardware causality is not isolated.
10. 358H primary timing is post-prefill decode end-to-end time, not whole-request user-perceived latency.
11. RTX NVIDIA-board and Intel CPU-package energy domains are separate and are not summed as whole-system energy.
12. B570 board energy excludes CPU/wall/whole-system energy and is diagnostic because the path is not globally admissible.
13. Windows raw per-run Git provenance is one tier weaker than M4/B570/358H for the HumanEval/mechanism follow-up.
14. Prompt-bootstrap CIs mainly represent prompt sampling conditional on each frozen campaign; they do not cover full between-session/thermal/runtime-state uncertainty.
15. Frozen statistical estimators/bootstraps differ across campaigns and must not be silently homogenized.
16. Only four consumer systems and a narrow model family/runtime set are studied.
17. The strict token-exact contract is deliberately stronger than approximate-quality contracts used in some deployment settings.
18. No measured runtime optimization/state-reuse intervention is part of the current paper evidence.
19. `analysis/358h_phase3_prompt_level.csv` is a historical blocked-preflight header-only scaffold and must not be mistaken for final data.
20. The B570 historical finalizer/report field `V2_exact` is legacy terminology and must not leak into paper-facing global-exact claims.

## 15. Forbidden / unsafe claims

Do not publish the following without genuinely new evidence:

- “Heterogeneous speculative decoding is new.”
- “Heterogeneous speculative decoding is generally profitable/unprofitable on consumer hardware.”
- “This is the first systematic study of speculative-decoding performance.”
- “The `C/cost` or `τ/c` accounting equation is a new speculative-decoding theory.”
- “Acceptance is insufficient” as a standalone novelty claim.
- “Verification is the hidden bottleneck” as a universal/new discovery.
- “Batch-shape nondeterminism is newly discovered here.”
- “Speculative decoding generally works on M4.”
- “Unified memory causes the M4 win.”
- “CUDA is broken.”
- “Vulkan cannot do exact speculative decoding.”
- “The B570 serialized fallback is globally exact.”
- “The NPU is too slow / lacks compute.”
- “NPUs are unsuitable for speculative decoding.”
- “HumanEval token exactness means functional correctness/pass@k.”
- “Energy efficiency can be ranked directly across M4, RTX, B570, and 358H from current J/token values.”
- “358H reconstructed source exactly equals the lost historical upstream source.”
- “The corrected M4 synthetic ceiling was completed.”
- “High acceptance guarantees speedup.”
- “Isolated draft tok/s is the system draft cost.”
- “`V_k^micro` is automatically the complete realized target-side round cost.”
- “Phase 2 accurately predicted the Phase-3 358H end-to-end speedup.”
- “Persistent state reuse is itself a novel contribution of the current paper.”

## 16. Open scientific questions

These are future-paper/future-study questions, not unresolved validity of the closed hardware experiments:

- Would a measured persistent-draft-state intervention materially strengthen MLSys novelty enough to justify a separate co-design study?
- Under a looser approximate-quality contract, would physically fast RTX/B570 paths become admissible, and how should output quality be defined/measured? This requires a separate study.
- How broadly do the observed regimes generalize beyond Qwen3 and the tested consumer runtimes?
- Can future runtimes expose direct committed progress and complete target-round cost consistently enough to make cross-platform `C`/`R_target` comparisons less heterogeneous?
- Can correctness qualification be performed cheaply online without allowing a small gate (as on B570) to overgeneralize to a broader workload?
- Which runtime intervention gives the strongest *measured* incremental contribution: state persistence, correctness-aware path selection, or workload-aware speculation gating?

## 17. Missing evidence / inconsistencies

### 17.1 Repaired in terminal audit

1. **Post-merge status drift**
   - Old living docs still referenced `8de9642...` / PR #12 as current and described thesis/contribution ordering as under audit.
   - Repaired `REPO_STATUS.md`, paper workspace README, and compact evidence audit to the PR #13 merged baseline.

2. **Cross-platform mechanism note used pre-Round6 V2 semantics**
   - Old note used `V_2` / `V_2^exact` in prose that could be read as complete target-side round cost.
   - Repaired `paper/notes/CROSS_PLATFORM_MECHANISM.md` to use `V_k^micro`, keep `R_target` separate, add B570, and bound M4 mechanism language.

3. **358H misleading empty derivative filename**
   - `analysis/358h_phase3_prompt_level.csv` is header-only and originated from a blocked preflight.
   - It is now explicitly documented in `analysis/README.md` as historical/non-authoritative; final data sources are `358h_phase3_prompt_summary.csv`, rounds, decomposition, and summary JSON.

4. **RTX hardware identity in B570 living cross-platform summary**
   - `reports/b570/B570_CROSS_PLATFORM_SUMMARY.md` wrote `RTX 5070 Ti`.
   - Repaired to **RTX 5070 Ti Laptop** and changed cross-platform V2 language to micro/serialized terminology.

5. **Windows generated cross-platform descriptor drift**
   - Cross-platform CSV used `CPU/GPU unified-memory fixed k=2` as an M4 condition label, which risks causal over-reading.
   - Repaired to `llama.cpp Metal fixed k=2`.
   - `scripts/summarize_windows_humaneval_replication.py` was synchronized so regeneration preserves current archive provenance and neutral labeling.

### 17.2 Intentionally preserved historical inconsistencies

- Historical B570 result objects/reports contain a field/label `V2_exact`. Preserve as experiment provenance; paper-facing terminology supersedes it.
- Historical 358H closeout reports may describe pre-merge repository state. Preserve because they were true when written.
- Historical local paths/usernames embedded in provenance records may remain until release-time privacy review; do not alter scientific source files merely for aesthetic consistency.
- The historical B570 finalizer contains old cross-platform display wording. It is a closeout-era script, not the current paper authority; do not rerun it to regenerate paper-facing summaries without applying the handoff terminology/identity rules.

### 17.3 Evidence completeness by platform

- **M4:** strongest raw→analysis→report provenance; headline values independently recomputed again in terminal audit.
- **RTX 5070 Ti Laptop:** committed derived tables/mechanism captures support headline recomputation; raw per-run Git completeness weaker.
- **B570:** formal stop rule and complete serialized-fallback archive retained; prompt-level point estimates rechecked; prior audit reproduced finite bootstrap CIs bit-for-bit with retained input order.
- **358H:** direct processed summaries, runner semantics, round traces, decomposition, and 34-entry evidence bundle support the primary claims.

No terminal revalidation found a numerical discrepancy that changes a headline platform class or reverses the frozen thesis.

## 18. Paper outline candidate

Scientific order recommended for manuscript drafting:

1. **Empirical puzzle and research question** — same nominal SD idea spans profitable, exact-negative, inadmissible-fast, and state-interface-bound regimes.
2. **Correctness contract + realized-cost accounting** — define admissibility, `C`, `D_real`, complete `R_target`, `X`; explicitly separate `V_k^micro`.
3. **Methodology and evidence classes** — platforms, model/runtime scope, frozen estimators, statistical/energy boundaries, preregistration/provenance.
4. **Correctness changes the usable verification path** — M4/RTX/B570 path evidence; serialization ≠ exactness.
5. **M4 workload contrast** — representative 24Q negative + separately preregistered HumanEval positive.
6. **RTX exact controls and numerical path change** — raw-fast vs exact-expensive; bounded divergence evidence.
7. **B570 correctness-blocked control** — formal stop rule + diagnostic serialized fallback.
8. **358H realized state-interface result** — Phase2 eligibility vs Phase3 direct accounting; CPU target-bound, NPU state-interface-bound.
9. **Cross-platform regime map / design requirements** — mechanism synthesis, not hardware ranking.
10. **Related work / limitations / conclusion** — explicitly position against MLSys 2026 systematic SD study, runtime-controlled `τ/c` evaluation, heterogeneous SD, correctness-first SD, numerical determinism work.

Do not turn future runtime-design opportunities into current contributions.

## 19. Decision log

### D-20260918-01 — 358H final status
- Old: pending/provisional in original paper workspace.
- New: Phase 0–3 CLOSED and merged.
- Evidence: PR #12, Phase3 validation/closeout.

### D-20260918-02 — B570 verification terminology
- Old: historical global-looking `V2_exact` label.
- New: paper-facing `V2_serialized` / serialized `V_2^micro` unless an explicitly bounded exact subset is named.
- Reason: full workload only 60/90 exact.

### D-20260918-03 — realized draft cost
- Old risk: use isolated draft throughput as `T_d`.
- New: use `T_d(real)` through the actual state interface.
- Evidence: 358H NPU replay+proposal 58.35% despite favorable isolated throughput.

### D-20260918-04 — formula complexity
- Old candidate: split replay/proposal/rollback/reconstruction everywhere.
- New: keep aggregate `T_d(real)` unless independently measured without changing execution.

### D-20260918-05 — M4 primary energy wording
- Old risk: call 1.013x fixed-k2 package efficiency an energy win.
- New: **energy-neutral within uncertainty** because CI [0.990,1.034] crosses 1.

### D-20260918-06 — committed-work metric
- Old risk: use historical `accepted_per_round` as `C`.
- New: `C` means all committed output tokens/round including correction/bonus behavior.

### D-20260918-07 — Windows raw provenance level
- Old: imply all platform raw evidence chains are equally complete.
- New: Windows headlines are supported/recomputable from committed derived tables, but raw per-run Git provenance is one tier weaker.

### D-20260918-08 — serialized does not imply exact
- Old risk: serialized fallback called exact by construction.
- New: serialization is execution property; exactness is empirical workload property.

### D-20260918-09 — separate micro V2 from complete target-round cost
- Old: use `V_k*T_b` directly as end-to-end target term.
- New: use complete `R_target`; reserve `V_k^micro` for target-forward mechanism diagnosis.

### D-20260918-10 — aggregation level
- Old risk: expect arithmetic decomposition to equal prompt-GM speedup.
- New: accounting identity evaluated at same aggregation level as inputs.

### D-20260918-11 — B570 CI input order
- Provisional concern: sorted prompt order changed finite fixed-seed CI endpoints.
- Resolution: retained finalizer/raw pair order reproduces archived CIs bit-for-bit; no statistical error.

### D-20260919-01 — Skill discovery refresh
- Current environment exposes Data Analytics validation/data-quality skills.
- They are workflow aids, not authorities over frozen repository evidence.

### D-20260919-FINAL-01 — audit baseline advanced after PR #13 merge
- Old metadata: PR #13 open / audited baseline `8de9642...`.
- New: PR #13 merged; audited main baseline `5c8cc30284de2345d2056199cdeeffcad3da5599`.
- Evidence: GitHub branch/commit/PR history.

### D-20260919-FINAL-02 — cross-platform mechanism note superseded old V2 semantics
- Old: living note used `V_2` / `V_2^exact` as if directly interpretable as verification cost.
- New: all target-forward values named `V_k^micro`; complete end-to-end target-side term remains `R_target`.
- Reason: Round6 accounting audit + 358H direct runner semantics.

### D-20260919-FINAL-03 — 358H prompt-level scaffold classified non-authoritative
- Old risk: `analysis/358h_phase3_prompt_level.csv` filename could be mistaken for final data despite being header-only.
- New: explicitly historical blocked-preflight scaffold; final authority is prompt_summary/rounds/decomposition/summary JSON.
- Evidence: file content + commit `89fb760...` history.

### D-20260919-FINAL-04 — reproducibility/document identity repairs
- Repaired B570 living cross-platform summary to `RTX 5070 Ti Laptop` and micro/serialized terminology.
- Repaired Windows cross-platform M4 label/provenance and synchronized its generator.
- Scientific effect: **none on measurements**.

### D-20260919-FINAL-05 — novelty tightened after current literature audit
- Old broad risk: frame generic profitability accounting / acceptance / verification as novelty.
- New: generic commit/cost accounting, heterogeneous SD, correctness concerns, verification bottlenecks, and batch-shape nondeterminism are prior art.
- Strongest current novelty direction: correctness-admissible execution-path consequences + direct realized state-interface evidence on heterogeneous consumer systems.
- Scientific effect: **claim narrowing, not result change**.

### D-20260919-FINAL-06 — figure priority changed
- Old plan included a generic acceptance-vs-speedup main figure.
- New: de-prioritize it due nonuniform metric definitions and strong prior-art overlap; prioritize M4 workload contrast, verification-path admissibility, and 358H isolated-vs-realized state cost.

## 20. Audit log

### Round 1 — repository-wide status / stale-document audit
- Confirmed 358H Phase3 merge and four closed campaigns.
- Found stale paper-control docs and B570 terminology risk.
- Established initial handoff/evidence ledger.

### Round 2 — M4 deep audit
- Traced preregistration → frozen selection → raw result → analysis → report.
- Independently recomputed HumanEval/24Q headline values.
- No headline discrepancy; tightened energy wording.

### Round 3 — RTX 5070 Ti Laptop deep audit
- Recomputed exact HumanEval controls from committed pair-level data.
- Verified target-forward controls and stable numerical divergence.
- Added raw-provenance limitation.

### Round 4 — B570 deep audit
- Verified formal stop rule, later diagnostic status, unique serialized fallback, archive, and CI provenance.
- No headline discrepancy; enforced serialized≠exact terminology.

### Round 5 — 358H deep audit
- Recomputed performance/correctness/decomposition/C.
- Inspected runner full-prefix replay semantics and archive integrity.
- Elevated state-interface cost as measured mechanism.

### Round 6 — formula/mechanism audit
- Corrected conflation of target-forward PPk/PP1 with complete target-side round cost.
- Introduced final `R_target` vs `V_k^micro` distinction.
- Verified accounting identity on 358H aggregate totals.

### Round 7 — statistics/CI/aggregation audit
- Reproduced headline point estimates/CIs; no headline pseudoreplication.
- Preserved study-specific estimators/seeds/resample counts.
- Resolved B570 deterministic input-order requirement.

### Round 8 — correctness-contract audit
- Frozen common generated-token equality meaning.
- Qualified every exact/inexact claim by runtime/path/workload.
- Confirmed HumanEval pass@k is not claimed.

### Round 9 — energy-boundary audit
- Preserved M4 package, RTX separate component, B570 board-only, and no-358H-end-to-end boundaries.
- Prohibited global energy ranking.

### Round 10 — cross-platform / novelty audit
- Removed heterogeneous-SD firstness and generic cost-model novelty claims.
- Framed cross-platform result as mechanism triangulation.

### Stage D — runtime/software design audit
- Derived future requirements from measured bottlenecks.
- Did not implement or backfill a software contribution.

### Stage F — figure-plan audit
- Shifted from leaderboard/acceptance-centric plots to evidence-specific mechanism figures.

### Round 11 — adversarial reviewer audit
- Main risks: novelty, cross-stack confounding, HumanEval interpretation, correctness contract, NPU adapter confound, energy boundaries, model scope, no software intervention.

### Round 12 — thesis/contribution freeze
- Frozen scientific story and contribution ordering for drafting.
- Left exact title wording unfrozen.

### Terminal revalidation — 2026-09-19

Repository/integrity:
- Confirmed PR #13 merged; current audited `main` = `5c8cc30284de2345d2056199cdeeffcad3da5599`.
- Compared current main against the 358H merge point `8de9642...`: paper audit changed only seven paper/status docs; frozen experiment data/prereg/raw artifacts were unchanged.

Independent/targeted recomputation:
- M4 HumanEval fixed-k2 100k bootstrap replay reproduced speed and energy point estimates/CIs exactly.
- M4 representative 24Q 10k bootstrap replay reproduced speed CI and energy ratio exactly.
- B570 prompt-summary recomputation reproduced global GM, exact-prompt count, exact-subset GM, and board-energy ratio.
- RTX verification-cost cells and divergence capture rechecked directly; exact HumanEval summary remains unchanged from prior independent recomputation.
- 358H summary/runner/decomposition rechecked; ratio-of-total-times accounting reconstructed exactly for CPU/NPU.

New findings:
- post-merge status metadata stale in multiple living paper docs;
- cross-platform mechanism note retained pre-Round6 V2 semantics;
- 358H header-only preflight CSV could be mistaken for final data;
- B570 living summary dropped `Laptop` from RTX device identity and retained ambiguous V2 labeling;
- Windows cross-platform generator carried stale M4 provenance/“unified-memory” descriptor;
- current literature further tightens novelty: generic SD performance characterization, `τ/c` accounting, correctness-first batching, and batch-shape nondeterminism all have clear prior art.

Repairs performed on `paper/final-audit-20260919`:
- refreshed `REPO_STATUS.md`;
- refreshed compact evidence audit;
- refreshed paper workspace README;
- updated `analysis/README.md` authority note;
- rewrote living cross-platform mechanism note to final `V_k^micro` / `R_target` semantics;
- corrected B570 living cross-platform summary hardware identity/terminology;
- neutralized M4 condition label in Windows cross-platform CSV and synchronized its generator;
- updated this authoritative handoff.

Terminal scientific verdict:
- **No new numerical discrepancy changes any platform class or headline result.**
- **No new evidence reverses the frozen scientific thesis.**
- **Novelty framing is narrower than before and must stay narrow.**
- The paper is scientifically ready for manuscript/figure production, with novelty/positioning as the dominant remaining risk.

## 21. Next workflow

The hardware scientific audit is complete. The next work, only when requested, is paper production:

1. draft the manuscript from this handoff + `OUTLINE.md`;
2. produce main figures under Section 10 constraints;
3. build related work explicitly around the novelty boundaries above;
4. run final source/citation/anonymization/page-limit/adversarial review on the exact submission PDF;
5. optionally design a **separately preregistered** runtime co-design study if the team decides the expected MLSys novelty gain justifies the scope.

No additional hardware experiment is authorized by this handoff, and no post-hoc parameter search should be used to make the current story more favorable.

---

Scientific stop rule: if later evidence contradicts this synthesis, update the Evidence Ledger and Decision Log explicitly. Do not preserve a preferred narrative at the expense of repository evidence.
