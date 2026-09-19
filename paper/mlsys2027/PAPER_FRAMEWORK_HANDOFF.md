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
- Auditor: ChatGPT / GPT-5.6 Sol using the connected GitHub repository tools
- Current phase: hardware experiments CLOSED; paper scientific-audit phase
- Audit scope completed: Rounds 1–7 — repository/platform evidence-chain audits, unified formula/mechanism audit, and statistics/CI audit
- Audit scope not yet completed: correctness-contract audit, energy-boundary audit, cross-platform claim audit, adversarial reviewer audit, final thesis/contribution freeze
- No new hardware experiment was designed or run in this round.
- No preregistration, raw artifact, historical result report, or experiment data was modified.

### 0.1 Tool / Skill / Plugin discovery record — Stage A

Discovery was repeated at Stage A as required.

#### Available Skills and advertised descriptions

| Skill | Advertised description |
|---|---|
| Analytics Dashboard | Spreadsheet template for acquisition, engagement, retention, revenue, conversion funnel KPIs. |
| Business Review | Presentation template for business performance, KPIs, segments, priorities, decisions, outlook. |
| Design Report | Document template for executive summary, findings, implications, recommendations, appendix. |
| Experiment Analysis | Document template for hypotheses, methodology, results, interpretation, limitations, next steps. |
| Financial Budget | Spreadsheet template for actuals, budget, forecasts, variances, runway, departmental plans. |
| Investment Committee Memo | Document template for investment thesis, transaction details, financial analysis, risks, recommendation. |
| Legal Memorandum | Document template for issue, brief answer, facts, analysis, conclusion. |
| Market Trends Report | Presentation template for market/industry trends, evidence, implications, responses. |
| Minimal Letterhead | Document template for professional business letters. |
| Operating Calendar | Spreadsheet template for annual/monthly operating milestones, launches, deadlines, recurring events. |
| Operating Review | Presentation template for weekly scorecards, functional updates, risks, decisions, actions. |
| Project Kickoff | Presentation template for goals, scope, roles, milestones, risks, working model. |
| Project Tracker | Spreadsheet template for workstreams, tasks, owners, status, priority, dates, Gantt. |
| Sales Pipeline | Spreadsheet template for opportunities, stages, owners, deal sizes, probabilities, forecasts, next steps, risks. |
| Simple Dark Mode | General dark-mode presentation template. |
| Simple Light Mode | General light-mode presentation template. |
| Strategy Memorandum | Document template for strategic context, choices, rationale, risks, milestones, recommendation. |
| System Design | Document template for architecture, requirements, components, data flows, APIs, tradeoffs, operations. |
| Team Alignment | Presentation template for offsites/planning, goals, priorities, decisions, actions. |
| Three-Statement Forecast | Spreadsheet template for integrated income statement, balance sheet, cash flow forecast. |
| Template Creator | Create/update reusable artifact-template skills from reference artifacts. |
| Presentation router | Routes explicitly selected presentation artifact requests to the preinstalled presentation capability. |
| PDF router | Routes explicitly selected PDF artifact requests to the preinstalled PDF capability. |
| Document router | Routes explicitly selected document artifact requests to the preinstalled document capability. |
| Plugin Management | Inspect/manage plugin permissions, dependencies, connections/removal. |
| Spreadsheet router | Routes explicitly selected spreadsheet artifact requests to the preinstalled spreadsheet capability. |

#### Candidate Skill inspection

1. **Experiment Analysis**
   - URI: `skills://plugins/openai-templates/artifact-template-experiment-analysis/skill.md`
   - Full instructions inspected in Round 1.
   - Relevant idea: hypothesis/method/result/interpretation/limitation structure.
   - Round use: **evaluated but not invoked as a template**. The Skill is an artifact-generation workflow, not a scientific-audit engine, and this task requires a repository Markdown ledger.
   - Cannot solve: Git provenance, SHA/integrity validation, raw→analysis→report lineage, cross-platform causality, bootstrap correctness, novelty.

2. **System Design**
   - URI: `skills://plugins/openai-templates/artifact-template-system-design/skill.md`
   - Full instructions inspected in Round 1.
   - Stage fit: reserve for Stage D runtime/software co-design after the hardware audit is scientifically frozen.
   - Round use: **not used for Stage A conclusions**.
   - Cannot solve: retrospective scientific validity, correctness-admissibility, experimental provenance, causal attribution.

3. **Design Report**
   - URI: `skills://plugins/openai-templates/artifact-template-design-report/skill.md`
   - Full instructions inspected in Round 1.
   - Stage fit: possible later reporting/layout aid only.
   - Round use: **not invoked**.
   - Cannot solve: experiment validation, evidence authority, statistical correctness, provenance.

#### Plugin / tool capability status

- GitHub connector: **available and connected** to private repository `leecdiang/HeteroSpec`; read and write permissions confirmed.
- Repository tools used in Round 1: repo metadata, commit search, PR inspection, branch creation, file read/write.
- Dedicated statistics/CI/bootstrap Skill or plugin: **none exposed in the current environment**.
- General Python statistical computation is available, but no recomputation was required in Round 1; Stage B/Round 7 must rediscover tools before use.
- Dedicated scientific reproducibility/evidence-audit Skill: **none exposed**.
- Document/research capabilities exist, but none supersede repository evidence.
- Stage-A authority therefore remains: frozen definitions + repository evidence + evidence ledger + claim taxonomy.

### 0.2 Tool / Skill rediscovery — Stage C (unified mechanism/formula)

Rediscovery was repeated before Round 6.

- Available Skill catalog was re-listed; no new scientific-analysis Skill appeared.
- Full instructions were re-read for **Experiment Analysis** and **System Design**.
- Both remain artifact-template workflows. They can structure later documentation but cannot establish a cost identity, determine which variables are actually measured, or justify causal/mechanistic claims.
- No dedicated mechanism-model or performance-model plugin was exposed.
- Round-6 authority therefore remained the frozen runtime semantics, measured decompositions, mechanism controls, and algebraic consistency with end-to-end observations.

### 0.3 Tool / Skill rediscovery — Stage B (statistics / confidence intervals)

Rediscovery was repeated before Round 7.

- Available Skills were re-listed; relevant candidates remained **Experiment Analysis** and **Analytics Dashboard**, both presentation/artifact aids rather than statistical authorities.
- Full Experiment Analysis instructions were re-read.
- No dedicated bootstrap/CI/statistical-validation Skill or plugin was exposed.
- Statistical audit therefore used direct inspection of repository analysis code plus independent deterministic recomputation of the frozen prompt-level vectors.
- This rediscovery did not authorize changing any preregistered estimator or historical report.

## 1. Project status

### Hardware study status

**CLOSED** under the currently frozen hardware campaigns.

| Platform | Final status | Round-1 bounded interpretation |
|---|---|---|
| MacBook Air M4 / Metal | CLOSED | Representative 24Q negative; separately preregistered HumanEval30 fixed-k=2 exact profitable regime exists. Workload-conditioned, not general. |
| Core Ultra 9 275HX + RTX 5070 Ti Laptop / CUDA | CLOSED | Heterogeneous and exact same-GPU HumanEval controls are negative. Cheap batched raw verification exists but is not correctness-admissible under the frozen token-exact contract. |
| Core i5-13400 + Arc B570 / Vulkan | CLOSED | Fast path fails correctness; serialized fallback improves exactness but remains non-universal. No tested B570 path is a correctness-admissible optimization result. |
| Core Ultra X7 358H + Arc B390 target + CPU/NPU OpenVINO draft | CLOSED | CPU and NPU paths are token-exact but unprofitable; CPU is verification-bound, NPU is realized state/replay+proposal bound. |

### Software/runtime study status

- Not started as a new formal contribution.
- Runtime design opportunities are recorded only as evidence-derived future work.
- No state-reuse implementation, profitability controller, adaptive-k controller, or correctness-aware path selector is currently a measured paper contribution.

### Paper status

- Scientific framework audit in progress.
- Final title: **not frozen**.
- Final contribution count/order: **not frozen**.
- Manuscript prose: intentionally not produced by this audit.
- The previous paper workspace was created before 358H Phase 3 merged and contains stale provisional language; living status docs are being synchronized separately on this audit branch.

## 2. Research question candidates

Primary candidate:

> Under what correctness, verification-amortization, realized draft-state cost, and workload conditions does speculative decoding become profitable on consumer hardware?

Secondary decompositions:

- When does a physically fast target-verification path remain usable after the frozen correctness contract is applied?
- When does isolated draft-device throughput fail to predict realized end-to-end draft cost?
- How much committed work per speculative round is needed to amortize draft + admissible verification + residual runtime cost?

Do **not** reduce the paper question to “does heterogeneous speculative decoding work?” The repository supports regime analysis, not a universal binary verdict.

## 3. Current leading thesis

**Tentative; not frozen.**

A correctness-constrained speculative path is profitable only when the realized committed work per round is large enough to amortize **all** of:

1. the actual stateful draft-subsystem cost,
2. the target-verification cost of an execution path that satisfies the frozen correctness contract,
3. residual transfer/synchronization/runtime cost.

The four completed platforms expose different failure/success regimes:

- M4 HumanEval: admissible verification is near-one-target-step and workload predictability produces enough committed work → profitable exact regime.
- RTX 5070 Ti Laptop: a cheap raw batched verification path exists but fails the token-exact gate; the tested exact route becomes near-serialized → negative.
- B570: serialization increases verification cost and still does not establish universal exactness → no admissible optimization result.
- 358H CPU: exact but target-verification dominated → negative.
- 358H NPU: exact but the realized draft subsystem reconstructs/replays committed prefix inside the proposal call → isolated NPU throughput does not translate to end-to-end profitability.

This thesis is stronger than “high acceptance is not enough,” but must remain bounded to the tested runtimes/configurations.

## 4. Candidate contributions

Status is provisional until the platform-deep and statistics audits finish.

1. **Cross-platform correctness-constrained profitability study.**
   - Evidence: four closed consumer platforms, frozen/archived studies.
   - Risk: platform/software stacks are heterogeneous; this is mechanism triangulation, not a controlled hardware-only causal comparison.

2. **Minimal break-even framework using realized draft cost, correctness-admissible verification, residual cost, and committed work.**
   - Evidence: existing verification-amortization note + 358H decomposition.
   - Risk: must not introduce unmeasured latent variables merely for elegance.

3. **Empirical separation of raw verification speed from correctness-admissible verification.**
   - Evidence: RTX CUDA; complementary B570 behavior.
   - Risk: B570 serialized path is not universally exact and must not be labeled globally exact.

4. **Empirical separation of isolated draft throughput from realized stateful draft-subsystem cost.**
   - Evidence: 358H NPU.
   - Risk: current evidence identifies the tested OpenVINO/adapter state interface, not NPUs in general.

5. **Workload-conditioned positive regime rather than cherry-picked universal success.**
   - Evidence: M4 representative 24Q negative coexists with preregistered HumanEval30 positive.
   - Risk: reviewer may challenge HumanEval functional relevance because generated code was not executed.

## 5. Unified analytical framework

### 5.1 Final accounting distinction after Round 6

Round 6 found that the earlier draft of this handoff used one symbol too broadly. A target-forward microbenchmark such as `PP2/PP1` does **not** necessarily include all target-side work performed by a complete speculative round. In particular, correction/bonus decoding and state actions may occur outside the measured proposal-verification block.

The paper must therefore separate **realized round accounting** from a **microbenchmark batching proxy**.

#### End-to-end realized accounting

For one realized speculative round:

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

with break-even:

```text
C > D_real + R_target + X
```

Definitions:

- `T_b`: matched target-only baseline cost per output token within the same timing boundary.
- `T_d(real)`: realized draft-subsystem cost per speculative round through the actual state interface. It can include replay/reconstruction when the runtime performs it.
- `T_target,round(real)`: **complete realized target-side cost per speculative round**, including the target work actually executed for proposal verification and any correction/bonus behavior included by that runtime.
- `T_x`: measured/derived residual not already included above.
- `C`: all output tokens committed by the round, including target correction/bonus behavior.
- `D_real=T_d(real)/T_b`, `R_target=T_target,round(real)/T_b`, and `X=T_x/T_b`.

This is an accounting identity when all components are measured under the same boundary. It is not a claim that every platform exposes every term directly.

#### Target-forward microbenchmark proxy

Separately define:

```text
V_k^micro(n,e) =
    T_target_forward(k,n,e)
    -----------------------
    T_target_decode(1,n)
```

This is a **batching-efficiency / verification-opportunity proxy**. It is useful for diagnosing whether a backend can evaluate a width-`k` causal block for near one target step.

Correctness filtering still applies:

- a fast execution path that fails the frozen token-exact gate is not an admissible optimization path;
- if no tested path passes the workload-level correctness contract, there is no correctness-admissible end-to-end optimization result.

However, `V_k^micro` must **not** be substituted for `R_target` unless the measured microbenchmark is shown to include all target work in the realized round.

### 5.2 Why the distinction is necessary

- **M4 / Metal:** `V_2^micro≈1.02–1.08` demonstrates cheap exact width-two target-forward batching, but it does not by itself measure the entire speculative target-side round.
- **RTX / CUDA:** batched `V_2^micro≈0.98–1.01` is physically cheap but correctness-blocked; serialized `V_2^micro≈2.14–2.43` is an exact control. These values diagnose the verification-path change; they are not complete end-to-end round accounting.
- **B570 / Vulkan:** the historical serialized `PP2/PP1≈1.98–1.99` is a diagnostic microbenchmark and the path is not globally token-exact on HumanEval30.
- **358H:** Phase 3 directly measures the complete target-side interval and therefore provides the cleanest realization of `R_target`.

Using arithmetic totals for the 358H campaign:

| Path | `C` | `D_real` | `R_target` | `X` | `C/(D+R+X)` | Aggregate baseline/spec ratio |
|---|---:|---:|---:|---:|---:|---:|
| CPU draft | 2.4631 | 0.4304 | 2.9767 | 0.00124 | 0.7227 | 0.7227 |
| NPU draft | 2.4584 | 4.1251 | 2.9435 | 0.00130 | 0.3477 | 0.3477 |

These aggregate identities use arithmetic totals/means and therefore are **not expected to equal** the paper's prompt-level geometric-mean speedups (0.734x and 0.352x). Aggregation level must always be stated.

### 5.3 Committed work versus accepted draft tokens

Round 6 strengthens the distinction between acceptance and committed progress.

- 358H records `C` directly from round traces: 2.4631 CPU and 2.4584 NPU.
- Historical M4/RTX fields named `accepted_per_round` count accepted **draft** tokens/round and are not `C`.
- M4 raw HumanEval records allow a boundary-affected reconstructed quantity `output_tokens_runtime / verification_rounds`:
  - fixed k2 weighted ≈2.8264 output tokens/reported verification round;
  - p_min=.8 ≈2.6764;
  - p_min=.9 ≈2.6059.
- Because initial/final runtime effects make `output_tokens - accepted_tokens - rounds` vary by 0–2, these M4 values are **reconstructed effective progress**, not promoted to the same direct-measurement status as 358H `C`.
- The fact that p_min conditions have higher acceptance but lower reconstructed effective progress is additional evidence that acceptance rate alone cannot stand in for committed progress.

### 5.4 Formula complexity decision

Keep `T_d(real)` aggregated. Do not invent separately measured replay, reconstruction, rollback, transfer, or correction terms where the frozen runtime did not expose them.

The unified contribution is therefore an **accounting discipline**:
1. measure realized draft-state cost,
2. measure the complete realized target-side round cost when available,
3. use microbenchmark `V_k^micro` only as a mechanism proxy,
4. enforce correctness before admitting a path,
5. compare cost against realized committed progress `C`.

## 6. Platform regime map

### M4 / Metal

- Frozen representative Spec-Bench 24Q: 0.842x, 95% CI [0.809, 0.877], 72/72 exact, 1/24 prompts faster.
- Package energy ratio 0.678x; baseline 1.206 vs k2 1.729 package J/output-token.
- Separate preregistered HumanEval30 primary fixed-k=2: 1.387x [1.351, 1.422], 30/30 faster, 90/90 exact, 90.1% mean acceptance, 1.798 accepted draft tokens/round.
- HumanEval fixed-k=2 package efficiency 1.013x [0.990, 1.034]: energy-neutral within uncertainty.
- Registered p_min=0.9 secondary package efficiency 1.041x [1.018, 1.065].
- Safe interpretation: profitable exact **code-conditioned** regime exists; representative workload did not generalize it.
- Corrected synthetic ceiling from preregistration: NOT EXECUTED; older exploratory synthetic data cannot substitute.

### RTX 5070 Ti Laptop / CUDA

- Platform closed.
- 60Q pilot negative across k; 0–1/60 prompts faster depending on k.
- HumanEval exact serialized controls:
  - CPU→RTX: 0.404x [0.390, 0.418], 90/90 exact, 0/30 faster, 91.31% acceptance.
  - RTX→RTX: 0.650x [0.629, 0.673], 90/90 exact, 0/30 faster, 91.21% acceptance.
- Raw CUDA ubatch=2 V2 ≈ 0.983–1.009 but fails frozen exactness on stable HumanEval/106 reproduction.
- Exact ubatch=1 V2 ≈ 2.137–2.431.
- Logit ordering flip reproduced at the first divergence; this supports batch-shape-dependent numerical argmax change, not a universal CUDA defect.
- Safe interpretation: transfer matters but does not solely explain the negative result; correctness filtering removes the fast verification path in this frozen configuration.

### Arc B570 / Vulkan

- Platform closed after one preregistered serialized fallback candidate.
- Fast path: 45/90 exact pairs; speedup 0.5383x diagnostic; V2(512)=1.2426, V2(2048)=1.6373.
- Serialized fallback: 60/90 exact pairs; 20/30 wholly exact prompts; speedup 0.3087x [0.2927, 0.3246] diagnostic; 0/30 faster.
- Serialized verification proxy: 1.9827 at 512 and 1.9917 at 2048.
- Board-energy efficiency ratio 0.3023x [0.2846, 0.3202]; boundary is Arc B570 adapter board only.
- **Terminology warning:** historical reports label the serialized proxy `V2_exact`, but full-workload correctness is not universal. Paper-facing terminology should be `V2_serialized` / serialized fallback verification factor unless a later correctness audit justifies a narrower exact qualifier.
- Safe interpretation: no tested B570 path qualifies as a correctness-admissible optimization result.

### 358H CPU / NPU + B390 Vulkan target

- Phase 0–3 scientific execution complete and merged to main.
- Stage-A gate: CPU 18/18 exact; NPU 18/18 exact.
- HumanEval30:
  - CPU: 0.734x [0.693, 0.771], 90/90 exact, 0/30 faster.
  - NPU: 0.352x [0.333, 0.369], 90/90 exact, 0/30 faster.
- Acceptance / committed work:
  - CPU 75.31%, C=2.463.
  - NPU 75.13%, C=2.458.
- Decomposition:
  - CPU: replay+proposal 12.63%, target verification 87.34%, residual 0.04%.
  - NPU: replay+proposal 58.35%, target verification 41.63%, residual 0.02%.
- End-to-end energy is not claimed; NPU is not admissible.
- Reconstructed draft source identity remains STRONGLY_SUPPORTED, not proven exact upstream identity.
- Safe interpretation: current OpenVINO/state interface erases isolated NPU draft-throughput advantage through full-prefix replay+proposal; do not generalize to NPUs.

## 7. Claim taxonomy

| Claim ID | Candidate wording | Status | Platforms | Key evidence | Limitation / reviewer risk | Suggested paper placement |
|---|---|---|---|---|---|---|
| C-M4-01 | A preregistered exact profitable fixed-k=2 regime exists on M4 for the frozen HumanEval code-conditioned workload. | PRIMARY | M4 | 1.387x [1.351,1.422], 90/90 exact, 30/30 faster | workload-conditioned; no functional pass@k | Results |
| C-M4-02 | The representative frozen 24Q M4 study is negative. | PRIMARY | M4 | 0.842x [0.809,0.877], 72/72 exact | workload mix differs from HumanEval | Results / limitation against cherry-picking |
| C-XP-01 | Acceptance alone is insufficient to predict profitability. | MECHANISM_SUPPORTED | M4, RTX, 358H; B570 diagnostic | high acceptance coexists with positive and negative outcomes | observational cross-platform evidence, not isolated causal proof | Intro / Discussion |
| C-RTX-01 | In the frozen llama.cpp/CUDA/Q8_0 configuration, the fast batched path can change greedy argmax and therefore is not admissible under the token-exact contract. | MECHANISM_SUPPORTED | RTX | stable HumanEval/106 divergence + logit-order sign flip | one stable case/configuration; do not generalize to CUDA | Results |
| C-RTX-02 | The tested exact CUDA fallback raises width-2 verification cost to roughly 2.14–2.43 target decodes. | MECHANISM_SUPPORTED | RTX | ubatch=1 V2 controls | microbenchmark depths differ from M4 | Results / framework |
| C-B570-01 | The single serialized B570 fallback is not universally token-exact on HumanEval30. | DIAGNOSTIC | B570 | 60/90 pairs, 20/30 prompts | later post-gate phase | Results / limitation |
| C-B570-02 | B570 has no tested correctness-admissible optimization result. | SECONDARY | B570 | fast + serialized correctness failures | backend/config bounded | Results |
| C-358H-01 | CPU and NPU 358H paths are token-exact but unprofitable in the frozen Phase-3 workload. | PRIMARY | 358H | CPU 0.734x; NPU 0.352x; both 90/90 exact | post-prefill timing, not whole-request latency | Results |
| C-358H-02 | Realized stateful draft cost, not isolated draft throughput, dominates the tested NPU path. | MECHANISM_SUPPORTED | 358H NPU | replay+proposal 58.35% | replay/proposal not separable; implementation-specific | Framework / Discussion |
| C-XP-02 | Verification amortization must be correctness-filtered. | MECHANISM_SUPPORTED | M4, RTX, B570 | cheap exact vs cheap inadmissible paths | strict token-exact contract may be challenged as strong | Framework |
| C-M4-CAUSE-UM | Unified memory is the cause of M4 profitability. | PLAUSIBLE_NOT_CAUSAL | M4 | compatible with system behavior | no isolated control | Do not state causally |
| C-CUDA-BROKEN | CUDA is broken for speculative decoding. | FORBIDDEN_OVERCLAIM | RTX | not supported | frozen single config/case evidence only | Never |
| C-NPU-SLOW | NPU compute is too slow for speculative decoding. | FORBIDDEN_OVERCLAIM | 358H | contradicted by isolated-throughput framing | measured issue is stateful interface cost | Never |
| C-HE-FUNC | Token-exact HumanEval outputs establish functional HumanEval correctness/pass@k. | FORBIDDEN_OVERCLAIM | all HumanEval studies | generated code not executed | invalid metric substitution | Never |
| C-ENERGY-RANK | Absolute J/token can rank all platforms directly. | FORBIDDEN_OVERCLAIM | all | sensor boundaries differ | incomparable energy domains | Never |
| C-M4-GENERAL | Speculative decoding generally works on M4. | FORBIDDEN_OVERCLAIM | M4 | 24Q is negative | workload-conditioned positive only | Never |

## 8. Evidence ledger

Round-1 level is deliberately headline/report-level. Rows marked **TRACE-PENDING** require analysis-script/prereg/raw validation in platform-specific rounds.

| Evidence ID | Platform / experiment | Class | Metric / value | CI / reps | Correctness | Workload / model / runtime | Source report | Analysis / script / prereg / raw status | Energy boundary | Paper use |
|---|---|---|---|---|---|---|---|---|---|---|
| E-M4-24Q-01 | M4 representative confirmatory | PRIMARY | speedup 0.842x | CI [0.809,0.877], 24 prompts ×3 | 72/72 exact | Spec-Bench 24Q; Qwen3-8B/0.6B Q8_0; llama.cpp Metal k=2 | `reports/m4/M4_CONFIRMATORY_VALIDATION.md` | index traces selection/result commits; deeper raw audit Round 2 | Silemetry package aggregate excludes separate DRAM | representative negative |
| E-M4-HE30-01 | M4 HumanEval30 | PRIMARY | speedup 1.387x | CI [1.351,1.422], 30×3 | 90/90 exact | HumanEval30; same Q8_0 pair; Metal k=2 | `reports/m4/M4_HUMANEVAL_CODE_CONDITIONED.md` | analysis `m4_humaneval_summary.json`; script and prereg/raw paths explicitly listed; verify Round 2/7 | package efficiency 1.013x [0.990,1.034] | positive conditioned regime |
| E-M4-HE30-02 | M4 HumanEval p_min=.9 secondary | SECONDARY | package efficiency 1.041x | CI [1.018,1.065] | 90/90 exact | same workload | same report | prereg listed; verify Round 2/7 | package | secondary energy result |
| E-RTX-HE30-CPU-01 | RTX HumanEval CPU→RTX exact control | SECONDARY | 0.404x | CI [0.390,0.418], 30×3 | 90/90 exact | HumanEval30; Q8_0; llama.cpp CUDA ubatch=1 | `reports/5070ti/FINAL_5070TI_PLATFORM_REPORT.md` + replication report | TRACE-PENDING Round 3 | not primary energy result | exact negative control |
| E-RTX-HE30-GPU-01 | RTX HumanEval RTX→RTX exact control | SECONDARY | 0.650x | CI [0.629,0.673], 30×3 | 90/90 exact | same | same | TRACE-PENDING Round 3 | not primary energy result | exact negative control |
| E-RTX-V2-RAW-01 | RTX raw CUDA verification | DIAGNOSTIC | V2 1.009@0, 0.983@256 | mechanism control | correctness-blocked | llama.cpp/CUDA ubatch=2 | `reports/5070ti/WINDOWS_VERIFICATION_MECHANISM_CONTROLS.md` via final report | TRACE-PENDING Round 3 | n/a | raw vs admissible |
| E-RTX-V2-ADM-01 | RTX serialized exact verification | MECHANISM_SUPPORTED | V2 2.431@0, 2.137@256 | mechanism control | exact control | llama.cpp/CUDA ubatch=1 | same + final report | TRACE-PENDING Round 3 | n/a | admissible verification penalty |
| E-RTX-DIV-01 | RTX divergence min-repro | MECHANISM_SUPPORTED | score margin +0.080948 → -0.126457; token 2790→2629 | 3/3 independent processes | shows divergence | HumanEval/106 frozen capture | `reports/5070ti/CUDA_DIVERGENCE_NUMERICAL_DIAGNOSIS.md` via final report | TRACE-PENDING Round 3 | n/a | numerical mechanism |
| E-B570-FAST-01 | B570 fast path | DIAGNOSTIC | speedup 0.5383; V2 1.2426/1.6373 | full diagnostic 90 pairs | 45/90 exact | HumanEval30; Vulkan | `reports/b570/B570_FAST_VS_EXACT_FALLBACK.md` | deeper prereg/raw audit Round 4 | board efficiency 0.6961 | correctness-blocked diagnostic |
| E-B570-SERIAL-01 | B570 serialized fallback | DIAGNOSTIC | speedup 0.3087; verification 1.9827/1.9917 | CI [0.2927,0.3246] | 60/90 exact; not universal | HumanEval30; Vulkan n_ubatch=1 | `reports/b570/B570_EXACT_FALLBACK_VALIDATION.md` | deeper prereg/raw audit Round 4 | board J/token 5.602→18.850; efficiency 0.3023 [0.2846,0.3202] | serialized fallback boundary |
| E-358H-P3-CPU-01 | 358H Phase3 CPU draft | PRIMARY | 0.734x | CI [0.693,0.771], 30×3 | 90/90 exact; gate 18/18 | HumanEval30; Vulkan0 target + OpenVINO CPU draft | `reports/358h/358H_PHASE3_END_TO_END_VALIDATION.md` | processed paths listed; raw archive 34-entry bundle; deep audit Round 5/7 | no end-to-end energy claim | exact negative CPU |
| E-358H-P3-NPU-01 | 358H Phase3 NPU draft | PRIMARY | 0.352x | CI [0.333,0.369], 30×3 | 90/90 exact; gate 18/18 | same target + OpenVINO NPU draft | same | processed/raw paths listed; deep audit Round 5/7 | NPU energy NOT_ADMISSIBLE | exact negative NPU |
| E-358H-DECOMP-CPU-01 | 358H CPU decomposition | MECHANISM_SUPPORTED | replay+proposal 12.63%; verify 87.34%; residual 0.04% | arithmetic mean of 90 requests | exact path | Phase3 | same | analysis path listed; recompute Round 5 | n/a | verification-bound mechanism |
| E-358H-DECOMP-NPU-01 | 358H NPU decomposition | MECHANISM_SUPPORTED | replay+proposal 58.35%; verify 41.63%; residual 0.02% | arithmetic mean of 90 requests | exact path | Phase3 | same | analysis path listed; recompute Round 5 | n/a | state-interface mechanism |
| E-358H-ARCHIVE-01 | 358H archive integrity | SECONDARY | 34/34 manifest entries verified, zero failures | one closeout archive | n/a | Phase3 archive | `reports/358h/358H_REPOSITORY_CLOSEOUT_AUDIT.md` | compressed bundle SHA256 `2fa619...8511`; direct Git objects verified before merge | n/a | reproducibility |

## 9. Cross-platform comparison table

| Platform regime | Correctness-admissible end-to-end result? | Profitability | Main bottleneck supported by evidence | Important caveat |
|---|---|---|---|---|
| M4 24Q k=2 | Yes | No, 0.842x | insufficient committed work / workload dependence despite cheap exact V2 | not evidence that M4 speculation never works |
| M4 HumanEval k=2 | Yes | Yes, 1.387x | successful regime: cheap exact verification + predictable workload | no functional HumanEval execution |
| RTX CUDA HumanEval | Yes only via serialized control | No, 0.404x / 0.650x | admissible verification near-serialized; draft/integration overhead remains | fast raw path exists but is correctness-blocked |
| B570 Vulkan | No universally exact tested path | No admissible optimization claim | correctness failure; serialization costs ~2× and still non-universal | timing/energy are diagnostic |
| 358H CPU | Yes | No, 0.734x | target verification 87.34% | post-prefill boundary |
| 358H NPU | Yes | No, 0.352x | realized prefix replay+proposal 58.35% | current OpenVINO/state interface, not NPU universal |

Cross-platform comparison is **mechanism comparison**, not a controlled hardware ranking. Runtime, backend, quantization/execution, memory organization, and scheduling differ.

## 10. Figure plan

No final figures produced in Round 1.

| Figure ID | Question answered | Source data | Axes / structure | Platforms | Evidence class | Section | Risk |
|---|---|---|---|---|---|---|---|
| F1 | What must be amortized for speculation to profit? | framework + measured decomposition | conceptual equation / cost blocks | all | framework | Background/model | avoid implying every term independently measured everywhere |
| F2 | What regimes exist across platforms? | headline prompt-level results | categorical regime map, not leaderboard | all | mixed primary/diagnostic clearly encoded | Results overview | do not rank incompatible configs as pure hardware comparison |
| F3 | How does raw V2 differ from admissible verification? | M4/RTX/B570 mechanism controls | V2 by path + correctness marker | M4, RTX, B570 | mechanism/diagnostic | Mechanism | B570 serialized not universal exact |
| F4 | Why is high acceptance insufficient? | HumanEval acceptance/C + speedup | acceptance or C vs speedup | M4, RTX, 358H | mixed | Mechanism | only plot matched definitions; accepted/round ≠ C |
| F5 | Why does NPU isolated speed not survive end to end? | 358H Phase1 + Phase3 decomposition | isolated draft vs realized replay+proposal/system share | 358H | primary/mechanism | 358H | avoid causal claim beyond state interface |
| F6 | What dominates request time on 358H? | Phase3 summary | stacked decomposition CPU/NPU | 358H | primary/mechanism | Results | arithmetic means vs prompt GM must be labeled |
| F7 | What do energy results say within each sensor boundary? | platform energy summaries | small multiples by platform | M4/RTX/B570 only if clearly separated | primary/diagnostic | Appendix/limitations | never make one absolute cross-platform energy ranking |

## 11. Table plan

| Table ID | Purpose | Required provenance |
|---|---|---|
| T1 | Platform/runtime/model/correctness-contract matrix | frozen configs + final reports |
| T2 | Cross-platform headline outcomes with explicit evidence class and correctness status | Evidence ledger rows + prompt-level CI audit |
| T3 | Mechanism quantities: raw/admissible V2, C/acceptance, realized draft/state cost, residual | mechanism reports + scripts; leave N/A where not comparable |
| T4 | Energy sensor boundaries and permitted claims | telemetry protocols/reports; never merge domains |

## 12. Runtime/software design opportunities

These are **future study opportunities**, not current contributions.

| Opportunity | Measured bottleneck addressed | Platform evidence | Expected benefit | Difficulty | New experiment required? | Scope risk | Needed for current MLSys claim? |
|---|---|---|---|---|---|---|---|
| correctness-aware verification path selection | cheap raw path may fail exactness | RTX, B570 | avoid counting inadmissible speed; select cheapest verified path | medium | yes for implementation claim | medium | no |
| persistent draft state / rollback / reuse | full-prefix replay dominates realized draft cost | 358H NPU | reduce `T_d(real)` | high | yes, separately preregistered | high | no; could strengthen future systems contribution |
| online profitability controller | M4 workload dependence | M4 24Q vs HumanEval | avoid speculation on negative prompts/regimes | medium | yes | medium | no |
| adaptive k | deeper k can hurt verification/acceptance | M4/RTX pilot/mechanism | trade C vs verification/draft cost | medium | yes | medium-high | no |
| CPU/NPU/iGPU draft selection | isolated fastest device may differ by workload/state interface | RTX draft characterization + 358H | choose realized-cost-minimizing device | high | yes | high | no |

## 13. Reviewer attack list

| Concern | Severity | Evidence available now | Response direction | Extra experiment needed by default? | Must state limitation? |
|---|---|---|---|---|---|
| Only four platforms; can this generalize? | HIGH | four distinct stacks expose repeated accounting constraints | claim mechanism/regimes, not universal hardware law | no | yes |
| Cross-platform stacks differ; causality confounded | HIGH | explicit bounded wording and mechanism-specific controls | separate within-platform evidence from cross-platform synthesis | no | yes |
| M4 HumanEval looks cherry-picked after 24Q failed | HIGH | separate preregistration, frozen 30 IDs, 24Q retained negative | present both results and chronology; workload-conditioned claim | no | yes |
| Why HumanEval if code was not executed? | HIGH | exact-token contract only | state that workload is a structured generation distribution, not functional benchmark result | no | yes |
| Token-exact contract may be unnecessarily strict | MEDIUM-HIGH | contract is frozen and makes path admissibility explicit | motivate deterministic greedy equivalence; discuss looser contracts as future work | no | yes |
| CUDA divergence may be one near-tie edge case | HIGH | stable 3/3 capture plus HumanEval gate impact | claim only frozen configuration; do not universalize | no | yes |
| B570 fallback called exact despite 60/90 | HIGH | direct contradiction in terminology vs correctness count | rename paper-facing factor `V2_serialized`; preserve historical report | no | yes |
| 358H replay may be an inefficient adapter, not NPU limitation | HIGH | report explicitly measures current state interface | agree; paper claim is state-interface cost, not NPU hardware weakness | no | yes |
| Should state reuse be implemented before publication? | MEDIUM-HIGH | negative result identifies a concrete requirement | depends on final paper contribution target; current study can stand as characterization if claims remain bounded | maybe, but not automatic | yes |
| Energy domains differ | HIGH | boundaries documented per platform | no absolute cross-platform J/token ranking | no | yes |
| Why not a production speculative runtime? | MEDIUM | native/control paths exist on RTX; platform study is implementation-bounded | frame as correctness/runtime mechanism study | possibly related-work discussion | yes |
| Models are small / mostly Qwen3 | HIGH | model pair consistency helps mechanism comparison | bound generalization; do not claim model-family universality | no by default | yes |
| Is this only an engineering benchmark paper? | HIGH | formula + repeated bottleneck regimes + correctness/state-interface mechanisms | contribution must be systems principle + auditable evidence, not leaderboard | no | yes |
| 358H prediction vs observation discrepancy undermines model | MEDIUM | discrepancy is explained by omitted realized replay/state cost | use it as validation of `T_d(real)` requirement | no | yes |

## 14. Known limitations

1. HumanEval generated code was not executed for functional pass@k; “exact” means generated token-ID equality.
2. Energy boundaries differ by platform and cannot be compared as one calibrated domain.
3. M4 unified memory is not isolated as a causal factor.
4. CUDA batch-shape argmax flip is a bounded frozen-configuration observation, not “CUDA is broken.”
5. B570 results are frozen backend/configuration results; serialized fallback is not universally exact.
6. 358H NPU result is an end-to-end result of the current OpenVINO/state interface, not a universal NPU verdict.
7. 358H reconstructed draft source is STRONGLY_SUPPORTED, not proven exact upstream source identity.
8. M4 preregistered corrected synthetic ceiling was not completed.
9. Cross-platform comparisons change hardware and software simultaneously; causal attribution must remain within-platform unless an isolated control exists.
10. 358H primary timing is post-prefill decode end-to-end time, not whole-request user-perceived latency.
11. RTX/NVIDIA and Intel CPU component energy domains are separate and are not summed as whole-system energy.
12. B570 board energy excludes CPU/wall/whole-system energy.

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
- “Energy efficiency can be ranked directly across M4, RTX, B570, and 358H from the current J/token values.”
- “358H reconstructed source exactly equals the lost historical upstream source.”
- “The corrected M4 synthetic ceiling was completed.”
- “High acceptance guarantees speedup.”
- “Isolated draft tok/s is the system draft cost.”

## 16. Open scientific questions

- Does the minimal formula remain quantitatively consistent after independent recomputation of all headline aggregations?
- What is the most defensible common definition of `V_k(admissible)` when correctness is prompt-dependent rather than universal (B570)?
- Can M4's realized draft cost be decomposed enough to compare state handling with 358H without inventing unavailable instrumentation?
- How should `C` be reported cross-platform when some historical reports emphasize accepted draft tokens/round rather than committed tokens?
- Is the central novelty strongest as profitability accounting, correctness-constrained verification, state-interface cost, or the combined regime map?
- Does final MLSys framing require a new runtime co-design implementation, or is the evidence-backed characterization sufficiently systems-oriented?
- Which prior speculative-decoding/runtime papers already formalize equivalent break-even terms? Literature audit not yet performed.
- Are all prompt-bootstrap implementations consistent in unit-of-analysis, geometric aggregation, and paired resampling? Round 7.

## 17. Missing evidence / inconsistencies

### Living docs that were stale at Round-1 start

1. `REPO_STATUS.md`
   - says status is on the 358H closeout branch and merge is pending;
   - says 358H result remains on dedicated branch pending review;
   - contradicted by main HEAD `8de9642...` and merged PR #12.

2. `paper/mlsys2027/EVIDENCE_AUDIT_2026-09-18.md`
   - records old main head `7327495...`;
   - treats 358H Phase3 as provisional/not started.

3. `paper/mlsys2027/WRITING_STATUS.md`
   - keeps 358H results HOLD and cross-platform table HOLD because Phase3 was pending.

4. `paper/mlsys2027/README.md`
   - instructs keeping 358H provisional until Phase3 completes/merges.

5. `paper/mlsys2027/OUTLINE.md`
   - contains multiple “358H pending final Phase3” placeholders.
   - Round-1 decision: flag but do not substantially rewrite the outline yet; final structure belongs after thesis/contribution audit.

### Historical reports with now-outdated process statements — preserve, do not rewrite

- `reports/358h/358H_REPOSITORY_CLOSEOUT_AUDIT.md` says PR #12 was READY FOR REVIEW and not auto-merged.
- `reports/358h/358H_PLATFORM_CLOSEOUT.md` says repository integration gates must pass before merge.

These were true at report time and form provenance. They should not be rewritten merely because the PR later merged.

### Scientific terminology inconsistency

- `reports/b570/B570_EXACT_FALLBACK_VALIDATION.md` and `B570_PLATFORM_CLOSEOUT.md` use `V2_exact` while the same validation reports only 60/90 exact pairs.
- Paper-facing terminology must not inherit that label uncritically.
- Current handoff term: **serialized fallback verification factor / `V2_serialized`**.
- Revisit in Round 4 and Round 8.

### Trace depth after Rounds 2–5

Platform-deep tracing is now complete for the headline claims.

- **M4:** strongest provenance. HumanEval raw `results.json`, preregistration, manifest, analysis script, prompt summary, telemetry hash metadata, and representative 24Q raw JSON were all inspected. Headline aggregations were independently recomputed from raw records.
- **RTX 5070 Ti Laptop:** headline HumanEval statistics were independently recomputed from the committed pair-level CSV and match the summary exactly. Important limitation: the authoritative ubatch=1 and aborted ubatch=2 run JSON files are documented as local/ignored; the repository retains their derived pair table, summary, manifest, mechanism CSVs, and numerical diagnosis. Raw-trace Git completeness is therefore weaker than M4/B570/358H.
- **B570:** the complete serialized-fallback archive is committed, including preflight, manifests, HumanEval30 raw/processed records, V2 records, telemetry, stdout/stderr, and remote-disconnect checks. Processed headline values match the reviewer-facing final status.
- **358H:** headline values were independently recomputed from the committed 180-row prompt summary. The 34-entry archive manifest reports 34/34 validated entries and zero size/SHA failures; an independently validated recovery tarball is retained.

No platform-deep audit found a numerical discrepancy that changes a headline platform conclusion. The substantive corrections are terminology, evidence strength, and metric semantics rather than headline values.

## 18. Paper outline candidate

Do not treat the existing `OUTLINE.md` as frozen.

Candidate scientific order:

1. Research question / empirical puzzle.
2. Correctness contract and admissible execution path.
3. Minimal profitability model.
4. Experimental methodology and evidence classes.
5. M4: workload-conditioned positive and representative negative.
6. RTX: raw-fast vs exact-expensive verification.
7. B570: serialization does not guarantee admissibility.
8. 358H: exact-but-negative verification/state-interface regimes.
9. Cross-platform regime map and system implications.
10. Limitations / related work / conclusion.

Do not write prose from this outline until Round 12 thesis/contribution freeze.

## 19. Decision log

### D-20260918-01 — 358H final status
- Old: 358H pending/provisional in paper workspace.
- New: Phase 0–3 scientific execution CLOSED and merged to main.
- Reason: PR #12 merged; main HEAD `8de9642...`; Phase3 report and platform closeout present on main.
- Evidence: PR #12, root README, `358H_PHASE3_END_TO_END_VALIDATION.md`, `358H_PLATFORM_CLOSEOUT.md`.

### D-20260918-02 — B570 verification terminology
- Old: historical report label `V2_exact` for serialized fallback.
- New: paper framework uses `V2_serialized` / serialized fallback verification factor unless a bounded exact subset is explicitly named.
- Reason: full validation is only 60/90 exact pairs; global performance admissible=false.
- Evidence: `B570_EXACT_FALLBACK_VALIDATION.md`, `B570_FAST_VS_EXACT_FALLBACK.md`.
- Historical reports are not rewritten.

### D-20260918-03 — realized draft cost
- Old risk: use isolated draft throughput as proxy for `T_d`.
- New: unified framework uses `T_d(real)`, measured through the actual end-to-end state interface.
- Reason: 358H NPU isolated throughput advantage is erased by full-prefix replay+proposal, 58.35% of measured speculative time.
- Evidence: `358H_PHASE3_END_TO_END_VALIDATION.md`, verification-amortization framework.

### D-20260918-04 — formula complexity
- Old candidate: possibly split `T_d(real)` into proposal/replay/rollback/reconstruction.
- New: keep a minimal aggregate `T_d(real)` for now.
- Reason: 358H replay-only and proposal-only cannot be separated without changing execution; extra variables would exceed measured evidence.
- Revisit: Round 6.

## 19A. Stage-A deep-audit addendum — Rounds 2–5

### M4 deep audit

**Verdict: SUPPORT, with metric/energy wording tightened.**

- HumanEval30 raw archive contains 360 runs: 90 each for baseline, fixed-k2, p_min=0.8, and p_min=0.9.
- The preregistration object embedded in the authoritative result is JSON-identical to `benchmarks/m4_code_conditioned_30q/preregistration.json`; the frozen HumanEval IDs independently reproduce from `random.Random(20260908).sample(range(164), 30)`.
- Independent raw recomputation:
  - fixed k2: 1.387352x, 30/30 prompts faster, 90/90 exact, mean acceptance 0.90070, accepted draft tokens/round 1.79833;
  - p_min=0.8: 1.362377x, 90/90 exact;
  - p_min=0.9: 1.395596x, 90/90 exact.
- Fixed-k2 package-energy efficiency ratio is 1.01295x, but the reported CI [0.98957, 1.03407] crosses 1.0. The preregistered energy gate is a point-estimate gate, so this is not a protocol failure; paper wording must be **energy-neutral within uncertainty**, not a significant energy win.
- HumanEval summary script uses **100,000** prompt-bootstrap resamples with seed 20260910. This differs from the 10,000 resamples used by the representative 24Q study.
- Representative 24Q raw recomputation: 72/72 exact; prompt GM 0.841965x; median 0.846050x; 1/24 faster; package-efficiency ratio 0.677507x; mean package J/token 1.206251 baseline vs 1.729272 k2.
- Representative repetition-level GMs are 0.909834 / 0.818999 / 0.801008, so session drift exists, but the prompt-level estimator and CI remain decisively below 1.
- The representative summarizer correctly reduces three paired repetitions within prompt before bootstrapping prompts; no repetition-level pseudoreplication was found.
- Corrected synthetic ceiling was preregistered but not executed. Older exploratory synthetic data remain diagnostic only.
- Exactness is generated token-ID equality; HumanEval functions were not executed.

### RTX 5070 Ti Laptop deep audit

**Verdict: SUPPORT, with a raw-provenance limitation.**

- Exact serialized HumanEval pair table independently recomputes to:
  - CPU→RTX: 0.403937x, median 0.399304x, 90/90 exact, 0/30 faster, weighted acceptance 0.913067, accepted-draft-tokens/round 1.821156;
  - RTX→RTX: 0.650079x, median 0.637317x, 90/90 exact, 0/30 faster, weighted acceptance 0.912070, accepted-draft-tokens/round 1.819172.
- Statistics use prompt as unit, three repetition-paired ratios per prompt, then 10,000 prompt bootstrap resamples with seed 20260910.
- Fast CUDA `ubatch=2` verification proxy is 1.0090x at context depth 0 and 0.9831x at 256; exact `ubatch=1` proxy is 2.4310x and 2.1370x.
- HumanEval/106 divergence reproduces 3/3 at captured index 190; baseline/serialized choose token 2790 while batched chooses 2629.
- Same-commit diagnostic score difference `score(2790)-score(2629)` is +0.080948 baseline/serialized and -0.126457 batched, identical across three independent processes. This supports a batch-shape-dependent numerical argmax flip, not a kernel-specific or universal CUDA claim.
- **Repository limitation:** `logs/windows-humaneval-replication-30q-ub1.json`, the aborted primary JSON, and some mechanism raw logs are documented as local/ignored. The committed pair CSV/summary/manifest and mechanism CSVs allow headline recomputation, but raw per-run Git provenance is incomplete relative to M4/B570/358H.
- HumanEval follow-up has no admissible energy ratio; 1 Hz process-window telemetry includes model loading and lacks the required decode-window/CPU-package boundary.

### B570 deep audit

**Verdict: SUPPORT the negative/correctness-blocked conclusion; strengthen terminology correction.**

- Formal v2 preregistration correctly stops after the six-prompt correctness failure. No formal V2 or HumanEval30 performance result is admissible from that run.
- A later diagnostic extension was explicitly frozen as post-gate diagnostic-only and did not alter the formal failure.
- Fast-path diagnostic: 45/90 exact pairs, 15/30 wholly exact prompts, 0.5383x raw speedup, 0/30 faster, V2_raw=1.2426/1.6373 at 512/2048.
- The unique serialized fallback candidate was frozen before its full validation; global performance was preregistered as admissible only if all 90 pairs were exact.
- Full fallback result: 60/90 exact pairs, 20/30 wholly exact prompts, global admissible=false; diagnostic speedup 0.308682x, CI [0.292690, 0.324604], 0/30 faster; exact-subset descriptive speedup 0.302574x.
- Arc-board energy efficiency ratio 0.302276x, CI [0.284553, 0.320160]; baseline mean 5.601993 vs fallback 18.849895 board J/token. Boundary is Arc B570 board only.
- Historical field/report name `V2_exact`=1.982668/1.991707 is scientifically misleading at full-workload scope. Paper-facing name remains **`V2_serialized` / serialized ubatch=1 verification proxy**.
- Complete committed archive exists for `exact-fallback-v1-20260912-222617`, including raw HumanEval30 records, V2 data, telemetry, stdout/stderr, manifests, and remote-disconnect evidence.
- Principle frozen for paper: **serialized is an execution property; exactness is an empirical workload-level correctness property.**

### 358H deep audit

**Verdict: SUPPORT, and directly strengthen the unified accounting semantics.**

- Independent recomputation from the 180-row committed prompt summary:
  - CPU draft: 0.7339146x, median 0.771737x, 90/90 exact, 0/30 faster;
  - NPU draft: 0.3516632x, median 0.367999x, 90/90 exact, 0/30 faster.
- The estimator is median of three paired speedups within each HumanEval prompt, then geometric mean across 30 prompt medians; CI uses 10,000 prompt bootstrap resamples, seed 20260919.
- CPU arithmetic-mean decomposition over 90 requests independently recomputes to 13253.126 ms total = 1673.507 ms draft replay+proposal + 11574.811 ms target verification + 4.808 ms residual.
- NPU recomputes to 27543.780 ms total = 16071.082 ms draft replay+proposal + 11467.641 ms verification + 5.057 ms residual.
- Runner inspection confirms each OpenVINO proposal call invokes `LLMPipeline.generate` on the **entire committed prefix**; replay and proposal are therefore truly combined in the measured draft interval and cannot be separated retrospectively without changing execution.
- 358H provides the cleanest direct `C`: committed output tokens / speculative rounds, including correction/bonus behavior:
  - CPU C=2.463117 from 11,520 committed tokens / 4,677 rounds;
  - NPU C=2.458387 from 11,520 / 4,686.
- This is **not the same metric** as historical M4/RTX `accepted_per_round`, which counts accepted draft tokens/round.
- Phase-3 archive manifest records 34 entries; recovery bundle validation reports 34/34 entries validated and zero failures. Recovery tarball: 694239 bytes, SHA256 `2fa6197864b1c6fc7af1c6da31f24ccf224e3dc0933bc1534840117eaee08511`.
- Formal-execution amendment discloses brief interactive monitoring and a retrospectively documented host-state snapshot. Repetition stability and baseline chronology show no discontinuity capable of moving either CI across 1; this remains a disclosed protocol limitation rather than grounds for sample removal.
- Historical Transformers source commit is unrecoverable. Reconstructed source remains STRONGLY_SUPPORTED, never PROVEN exact historical identity.


### D-20260918-05 — M4 primary energy wording
- Old risk: treat fixed-k2 package efficiency 1.013x as an energy win.
- New: describe fixed-k2 as **energy-neutral within uncertainty**; only the point estimate is favorable.
- Reason: package-efficiency 95% CI [0.990, 1.034] crosses 1.0.
- The preregistered gate used the point estimate, so this is a wording/statistical-strength correction, not a protocol failure.

### D-20260918-06 — cross-platform committed-work metric
- Old risk: use historical `accepted_per_round` as `C`.
- New: `C` means all committed output tokens per speculative round, including target correction/bonus behavior. M4/RTX accepted-draft-tokens/round remain separately named proxies/descriptors unless committed progress can be reconstructed.
- Reason: 358H directly records both quantities and demonstrates they are definitionally distinct.

### D-20260918-07 — Windows raw provenance level
- Old: treat all platform evidence chains as equally complete.
- New: Windows HumanEval/mechanism headline values remain supported and recomputable from committed derived tables, but raw per-run Git provenance is one tier weaker because authoritative JSON logs are documented as local/ignored.
- Reason: repository inspection.

### D-20260918-08 — serialized does not imply exact
- Old risk: call a serialized fallback “exact” by construction.
- New: serialization is an execution-path property; exactness is established only by the frozen workload correctness gate.
- Reason: B570 ubatch=1 fallback is only 60/90 exact despite prior 18/18 six-prompt gate.
- Consequence: paper-facing `V2_serialized` terminology is mandatory.


### D-20260918-09 — separate micro verification proxy from realized target-round cost
- Old: the framework wrote `V_k(admissible)*T_b` directly as the target term in the end-to-end break-even equation.
- New: the end-to-end equation uses `T_target,round(real)` / `R_target`; `V_k^micro=PPk/PP1` is a separate target-forward batching proxy.
- Reason: target-forward microbenchmarks do not necessarily include correction/bonus and other target-side work. 358H directly demonstrates a complete target-side per-round cost near three baseline-token equivalents.
- Consequence: M4/RTX/B570 V2 values remain valuable mechanism evidence but are not silently substituted into the accounting identity.

### D-20260918-10 — aggregation level of the cost identity
- Old risk: expect arithmetic decomposition plugged into the formula to reproduce the prompt-level geometric-mean speedup.
- New: realized cost accounting is evaluated at the same aggregation level as its inputs. For 358H, arithmetic totals exactly reproduce the aggregate baseline/speculative time ratio; prompt-GM remains the preregistered headline estimator.
- Reason: ratio-of-totals and geometric mean of per-prompt paired ratios are different estimands.

### D-20260918-11 — B570 historical CI reproducibility — SUPERSEDED DURING ROUND 7
- Provisional observation: re-bootstrapping the numerically sorted prompt CSV gave a slightly different finite-sample CI.
- Resolution: this was **not** a historical-analysis error. Commit `15e3bd19...` retains `scripts/platform/b570/finalize_b570_exact_fallback.py`, which builds prompt dictionaries in first-seen randomized execution order and then applies Python `random.Random(20260910)` for 10,000 resamples.
- Replaying that exact retained input order reproduces the archived speed CI **[0.2926903625835106, 0.3246036952205638]** and energy CI **[0.28455311861341115, 0.3201604335732349]** bit-for-bit.
- Lesson: a finite fixed-seed bootstrap is numerically sensitive to input ordering even though the underlying empirical prompt distribution is the same. The raw pair archive preserves the required order, so B570 CI provenance is complete.
- Scientific impact: none; the final Round-7 verdict is full reproduction, not a reproducibility gap.

## 20. Audit log

### Round 1 — 2026-09-18 — repository-wide final-status audit

- main HEAD: `8de9642b3d27830ec182f3571974069d5b88d405`
- Recent merge verified: PR #12 `358H: close Phase-3 heterogeneous validation`, merged=true.
- Files/directories inspected:
  - `README.md`
  - `REPO_STATUS.md`
  - `paper/mlsys2027/` listing
  - `paper/notes/` listing
  - `paper/mlsys2027/EVIDENCE_AUDIT_2026-09-18.md`
  - `paper/mlsys2027/WRITING_STATUS.md`
  - `paper/mlsys2027/OUTLINE.md`
  - `paper/mlsys2027/README.md`
  - `paper/notes/CROSS_PLATFORM_MECHANISM.md`
  - `paper/notes/VERIFICATION_AMORTIZATION_FRAMEWORK.md`
  - `reports/m4/M4_EXPERIMENT_INDEX.md`
  - `reports/m4/M4_HUMANEVAL_CODE_CONDITIONED.md`
  - `reports/m4/M4_CONFIRMATORY_VALIDATION.md`
  - `reports/5070ti/FINAL_5070TI_PLATFORM_REPORT.md`
  - `reports/b570/B570_PLATFORM_CLOSEOUT.md`
  - `reports/b570/B570_EXACT_FALLBACK_VALIDATION.md`
  - `reports/b570/B570_FAST_VS_EXACT_FALLBACK.md`
  - `reports/358h/` listing
  - `reports/358h/358H_PHASE3_END_TO_END_VALIDATION.md`
  - `reports/358h/358H_PLATFORM_CLOSEOUT.md`
  - `reports/358h/358H_PROVENANCE_AMENDMENT.md`
  - `reports/358h/358H_REPOSITORY_CLOSEOUT_AUDIT.md`
- Findings:
  - four platform campaigns are scientifically closed;
  - 358H is merged, making several living paper/status docs stale;
  - root README is already synchronized;
  - B570 `V2_exact` terminology is too strong for 60/90 full-workload exactness;
  - candidate unified formula remains viable if `T_d` means realized stateful subsystem cost and `V_k` is correctness-filtered.
- Changed conclusions:
  - 358H moved from provisional to final closed evidence;
  - state-interface cost becomes a first-class measured mechanism;
  - B570 serialized factor must be renamed in paper-facing material.
- Unresolved:
  - platform-deep raw/provenance checks;
  - aggregation/CI consistency;
  - exact common meaning of admissible V2 in partially exact B570 case;
  - novelty/literature positioning;
  - whether runtime co-design is necessary for the final contribution.

### Round 2 — 2026-09-18 — M4 deep evidence-chain audit

- Traced preregistration → frozen selection → raw results → analysis script → prompt summaries → report.
- Independently recomputed HumanEval and representative 24Q headline statistics.
- No headline discrepancy found.
- Tightened energy wording and bootstrap-resample count.
- Clarified that `accepted_per_round` is not the unified `C`.

### Round 3 — 2026-09-18 — RTX 5070 Ti Laptop deep audit

- Independently recomputed exact-control HumanEval statistics from the committed pair-level CSV.
- Verified verification-cost controls and stable numerical sign flip.
- No headline discrepancy found.
- Added raw-trace Git provenance limitation for local/ignored run JSON files.

### Round 4 — 2026-09-18 — Arc B570 deep audit

- Verified formal-v2 stop rule, post-gate diagnostic status, one-candidate fallback preregistration, full fallback processed result, and archive contents.
- No headline discrepancy found.
- Confirmed that `V2_exact` must not be inherited as a paper-facing global-exact label.
- Confirmed all fallback timing/energy remains diagnostic because 60/90, not 90/90, pairs are exact.

### Round 5 — 2026-09-18 — 358H deep audit

- Independently recomputed prompt-level performance, exactness, decomposition, and committed-work accounting.
- Inspected runner implementation to verify whole-prefix OpenVINO replay semantics.
- Verified 34-entry manifest and recovery-bundle integrity metadata.
- No headline discrepancy found.
- Elevated direct `C` semantics and state-interface cost as measured evidence for the unified framework.


### Round 6 — 2026-09-18 — unified formula / mechanism audit

- Re-discovered Stage-C Skills/tools; no scientific modeling plugin superseded repository evidence.
- Audited the verification-amortization note against M4/RTX/B570 microbenchmarks and the 358H realized decomposition.
- Found and corrected a symbol-level conflation between target-forward `PPk/PP1` and complete realized target-side round cost.
- The minimal accounting thesis survives, but the paper must use `R_target` for end-to-end cost and reserve `V_k^micro` for mechanism diagnosis.
- Verified the revised identity exactly on 358H arithmetic totals.
- Reconstructed M4 effective output progress per reported verification round as a diagnostic only; did not promote it to direct `C`.

### Round 7 — 2026-09-18 — statistics / CI / aggregation audit

- Re-discovered Stage-B Skills/tools; no dedicated statistical-validation plugin was available.
- Independently reproduced headline point estimates and bootstrap CIs for:
  - M4 HumanEval fixed k2 / p_min conditions;
  - M4 representative 24Q;
  - Windows CPU→RTX and RTX→RTX exact controls;
  - 358H CPU and NPU Phase3.
- Verified all headline studies use HumanEval/Spec-Bench prompt as the bootstrap unit after reducing repetitions within prompt; no headline pseudoreplication was found.
- Protocol-specific within-prompt estimators differ (geometric mean for M4/RTX, median for 358H) and must not be silently homogenized.
- Bootstrap implementations/resample counts also differ by frozen study; this is acceptable when reported, but the manuscript should make the differences explicit.
- B570 exact-fallback point estimates **and CIs** reproduce exactly after replaying the retained finalizer's first-seen prompt order. The finalizer script is preserved in commit `15e3bd19...`; no B570 CI reproducibility gap remains.
- Statistical CIs primarily reflect prompt-sampling uncertainty conditional on each campaign. They do not capture full between-session/thermal/runtime-state uncertainty; M4 representative repetition drift makes this limitation particularly important.
- No statistical finding changes the sign or correctness-admissibility of any headline platform result.
- B570 audit lesson: report the bootstrap unit, seed, resample count, estimator, **and deterministic input ordering** when bit-level CI reproducibility matters.

## 21. Next audit queue

Bounded order:

Completed: Rounds 1–7.

Remaining bounded order:

1. **Round 8 — correctness-contract audit.**
2. **Round 9 — energy-boundary audit.**
3. **Round 10 — cross-platform claim audit.**
4. **Round 11 — reviewer/adversarial audit.**
5. **Round 12 — final thesis + contribution freeze.**

Before every major stage, repeat Skill/Plugin/tool discovery and record any newly available relevant capability here.

---

Scientific stop rule for this handoff: if later evidence contradicts this Round-1 synthesis, update the ledger and Decision log. Do not preserve a preferred paper story at the expense of repository evidence.
