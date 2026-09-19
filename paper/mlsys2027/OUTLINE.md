# MLSys 2027 paper outline — terminal-audit freeze

Working target: **10 pages main body, 2 columns, references excluded**.

Authoritative scientific source: `paper/mlsys2027/PAPER_FRAMEWORK_HANDOFF.md`.

This is a paper-architecture outline, not manuscript prose. Scientific ordering is stable; exact title wording and prose are not frozen.

## Working title direction

Preferred direction after the 2026-09-19 novelty audit:

1. **HeteroSpec: Correctness-Admissible Paths and Realized Costs in Consumer Speculative Decoding**
2. **HeteroSpec: Correctness-Constrained Speculative Decoding Across Consumer Runtimes**
3. **A Cross-Platform Study of Correctness-Admissible Speculative Decoding on Consumer Systems**

De-prioritized because of current prior-art overlap:
- **When Does Speculative Decoding Pay on Consumer Systems?** — too close to broad systematic performance/profitability work already published at MLSys 2026.
- **Verification and State Reuse as the Hidden Bottlenecks...** — overclaims novelty and implies a measured state-reuse contribution that does not exist.

Do not freeze the exact title until the manuscript and main figures demonstrate which wording is most faithful.

## Core paper question

> When the execution path is filtered by a strict greedy token-equivalence contract, how do realized verification and state-interface costs determine whether speculative decoding pays on the tested consumer systems?

The paper is not a hardware leaderboard, does not claim heterogeneous speculative decoding as a new algorithm, and does not claim the accounting identity as a new theoretical model.

## Frozen contribution structure

1. Auditable cross-runtime characterization of profitable, exact-but-negative, correctness-blocked, and state-interface-bound regimes on four consumer systems.
2. Correctness-constrained realized-cost accounting discipline that separates complete round cost from target-forward microbenchmark `V_k^micro`, and separates committed progress `C` from accepted draft tokens/round.
3. Within-platform evidence that correctness filtering can remove the physically cheapest target-forward path; serialization itself does not guarantee exactness.
4. Direct 358H evidence that runtime state reconstruction can erase favorable isolated draft-device throughput.
5. A separately preregistered M4 code-conditioned positive regime retained beside a representative negative workload.

Novelty must come from the empirical mechanism combination and evidence discipline, **not** from generic claims that acceptance is insufficient, verification is expensive, batch shape affects numerics, or heterogeneous SD exists.

## Page budget

### 1. Introduction — ~1.0 page

Lead with the empirical puzzle:
- M4 HumanEval fixed-k2: 1.387x [1.351,1.422], exact and profitable;
- representative M4 24Q: 0.842x [0.809,0.877], exact and negative;
- RTX 5070 Ti Laptop: near-one-step raw target batching exists but is correctness-inadmissible; exact serialized controls are negative;
- B570: serialization improves exactness but still reaches only 60/90 exact pairs;
- 358H CPU/NPU: both exact, yet complete target-side work / realized state reconstruction dominate.

Motivating question:
- the relevant system is not merely “draft + verification”; it is the **cheapest execution path that survives the chosen correctness contract**, plus the state costs actually realized by that runtime.

End with bounded contributions. Explicitly avoid:
- heterogeneous-SD firstness;
- generic profitability-model firstness;
- universal backend/hardware claims.

### 2. Correctness contract and audited realized-cost accounting — ~1.25 pages

Explain:
- draft proposal;
- target block evaluation;
- accepted prefix;
- correction / bonus token;
- state rollback/reuse;
- deterministic greedy generated-token reference equivalence.

Define:
- `T_b`: matched target-only baseline cost/token;
- `T_d(real)`: realized draft-subsystem cost/round;
- `T_target,round(real)`: complete realized target-side cost/round;
- `T_x`: residual;
- `C`: all committed output tokens/round;
- `D_real`, `R_target`, `X` normalized by `T_b`;
- `V_k^micro`: target-forward `PPk/PP1` diagnostic proxy.

Accounting identity:

```text
speedup = T_b*C /
          [T_d(real) + T_target,round(real) + T_x]
        = C / [D_real + R_target + X]
```

Break-even:

```text
C > D_real + R_target + X
```

Critical warning:
- `V_k^micro` is **not automatically** `R_target`;
- accepted draft tokens/round are **not automatically** `C`;
- the equation is an accounting discipline, not a novelty claim.

### 3. Methodology and evidence classes — ~1.5 pages

Platforms:
- MacBook Air M4 / llama.cpp Metal;
- Core Ultra 9 275HX + **RTX 5070 Ti Laptop** / llama.cpp CUDA;
- Core i5-13400 + Arc B570 / llama.cpp Vulkan;
- Core Ultra X7 358H + Arc B390 Vulkan target + CPU/NPU OpenVINO draft.

Describe:
- model pair / quantization / execution path per study;
- batch-1 greedy generation setting;
- prompt selection and pairing;
- correctness gate;
- primary / secondary / mechanism / diagnostic evidence classes;
- target-forward microbenchmarks;
- direct realized decomposition where available;
- preregistration and frozen configs;
- archive/manifests and evidence tiers.

Statistical disclosure:
- M4 HumanEval: within-prompt GM, 100k prompt bootstrap, seed 20260910;
- M4 24Q: within-prompt GM, 10k, seed 20260907;
- RTX: within-prompt GM, 10k, seed 20260910;
- B570: prompt GM, 10k, seed 20260910, deterministic input order required for bit-level finite-bootstrap reproduction;
- 358H: within-prompt median, prompt GM, 10k NumPy bootstrap, seed 20260919.

Do not homogenize frozen estimators post hoc. Explain that these intervals mainly quantify prompt-sampling uncertainty conditional on each campaign.

Explicit boundaries:
- HumanEval code was not functionally executed;
- early M4 MLX-LM precision failures are distinct from final llama.cpp Q8_0 path;
- Windows raw per-run Git provenance is weaker than other final platforms;
- energy sensor boundaries differ;
- 358H source reconstruction is `STRONGLY_SUPPORTED`, not proven historical identity;
- cross-platform comparisons are mechanism comparisons, not hardware-only controlled benchmarks.

### 4. Correctness changes the usable execution path — ~1.25 pages

This is the central mechanism section.

M4:
- exact qualified Metal path;
- `V_2^micro≈1.02–1.08` on tested target-forward cells.

RTX 5070 Ti Laptop:
- batched `ubatch=2`: `V_2^micro≈0.98–1.01`, but frozen HumanEval exactness fails;
- serialized `ubatch=1`: exact control, `V_2^micro≈2.14–2.43`;
- HumanEval/106 first-divergence token ordering flip repeats 3/3;
- do not identify a universal CUDA/kernel defect.

B570:
- fast path 45/90 exact;
- serialized fallback 60/90 exact;
- serialized `V_2^micro≈1.98–1.99` remains diagnostic;
- **serialization is an execution property, not an exactness guarantee**.

Key interpretation:
- a physically cheap target-forward path does not count toward a strict-equivalence optimization claim if it fails the frozen correctness contract.
- prior work already studies output equivalence/nondeterminism; contribution here is the measured consequence for usable paths across these consumer runtimes.

### 5. Results by regime — ~2.5 pages

#### 5.1 M4: representative negative + separately preregistered positive

- 24Q: 0.842x [0.809,0.877], 72/72 exact, 1/24 faster;
- HumanEval fixed-k2: 1.387x [1.351,1.422], 90/90 exact, 30/30 faster;
- fixed-k2 package-energy ratio 1.013x [0.990,1.034] = neutral within uncertainty;
- registered `p_min=.9` energy improvement is secondary;
- corrected synthetic ceiling remains unexecuted.

Message:
- exact profitable **workload-conditioned** regime exists;
- do not claim representative M4 profitability or unified-memory causality.

#### 5.2 RTX 5070 Ti Laptop: fast raw path, exact expensive control

- CPU→RTX exact: 0.404x [0.390,0.418];
- RTX→RTX exact: 0.650x [0.629,0.673];
- both 90/90 exact, 0/30 faster;
- transfer matters, but same-GPU remains negative;
- raw batched path is physically cheap but inadmissible under frozen exactness.

Message:
- correctness filtering changes the usable path;
- integration/state/transfer costs remain after that path change.

#### 5.3 B570: no globally correctness-admissible optimization result

- formal v2 gate fails and stop rule remains controlling;
- later diagnostics do not rescue the formal result;
- fast 45/90 exact;
- serialized fallback 60/90 exact, diagnostic speedup 0.3087x [0.2927,0.3246];
- paper-facing term `V2_serialized` / serialized `V_2^micro`, never global `V2_exact`.

Message:
- small correctness gates can fail to generalize;
- serialization alone does not establish exactness.

#### 5.4 358H: exact but negative realized-cost regimes

- CPU: 0.734x [0.693,0.771], 90/90 exact;
- NPU: 0.352x [0.333,0.369], 90/90 exact;
- direct committed progress `C≈2.46` on both;
- CPU complete target-side work = 87.34% of speculative time;
- NPU full-prefix replay+proposal = 58.35%;
- residual Python/orchestration ≈0.02–0.04%, not the main mechanism;
- every OpenVINO proposal call reconstructs the full committed prefix;
- no end-to-end Phase3 energy claim.

Phase2/Phase3 message:
- Phase2 was an eligibility/favorable-bound screen using isolated/micro proxies;
- Phase3 demonstrates why realized state cost and complete target-side work must be measured.

### 6. Cross-platform regime map and system implications — ~1.0 page

Organize by regimes, not hardware winners:
- profitable + exact;
- exact but unprofitable;
- fast but inadmissible;
- state-interface bound.

System requirements derived from evidence:
- correctness qualification before promoting performance;
- measure realized state interface, not isolated draft tok/s;
- expose direct committed progress where possible;
- persistent state reuse and correctness-qualified path selection are future design targets;
- workload-aware speculation is suggested by M4 workload contrast.

Do not turn future design targets into current contributions.

### 7. Related work — ~0.9 page

Organize explicitly around overlap, not a generic bibliography dump.

#### 7.1 Speculative decoding and performance characterization
- classic speculative decoding / assisted generation;
- **Speculative Decoding: Performance or Illusion? (MLSys 2026)** — systematic production-engine characterization, verification dominance, workload/batch effects, upper bounds;
- **Runtime-Controlled Evaluation of Speculative Decoding Methods (2026)** — `S=τ/c` commit-length/conditional-cost decomposition under controlled runtime.

Consequence for our claims:
- no “first systematic performance study”;
- no generic commit/cost accounting novelty;
- no generic “high acceptance is insufficient” novelty.

#### 7.2 Heterogeneous speculative decoding
- Dovetail;
- DuoDecoding;
- Mirror Speculative Decoding;
- distributed/edge-cloud work such as Speculation at a Distance.

Consequence:
- no heterogeneous-SD algorithmic firstness.

#### 7.3 Correctness and numerical reproducibility
- Batch Speculative Decoding Done Right;
- LLM-42 / deterministic-inference work;
- finite-precision/batch-shape reproducibility studies such as Give Me FP32 or Give Me Death?.

Consequence:
- no firstness claim for output-equivalence concerns or batch-shape nondeterminism;
- HeteroSpec contributes a concrete correctness-admissibility consequence in tested consumer speculative paths.

#### 7.4 State / KV management and runtime integration
- persistent/cache-aware speculative-decoding work and long-context draft-memory work.

Consequence:
- state reuse itself is not a new idea;
- our evidence is the direct measured state-interface failure mode on the qualified 358H path.

### 8. Limitations and conclusion — ~0.55 page

Required limitations:
- four consumer systems / narrow model family;
- hardware and software stacks co-vary across platforms;
- token equality is a deliberately strict study contract;
- no HumanEval pass@k;
- campaign-specific estimators/bootstraps differ;
- prompt CIs do not cover full system-state uncertainty;
- M4 session/thermal drift not fully captured by prompt bootstrap;
- energy boundaries differ;
- Windows raw per-run provenance is weaker;
- 358H reconstructed-source limitation;
- no measured state-reuse/runtime intervention.

Conclusion should restate the bounded mechanism:
- the cheapest physical path is not necessarily the cheapest **admissible** path;
- isolated accelerator throughput is not necessarily realized stateful subsystem cost.

## Main figures — final priority

1. **Correctness-constrained realized-cost schematic** — correctness gate → `D_real`, complete `R_target`, `X`, `C`; `V_k^micro` shown separately as a microbenchmark proxy.
2. **M4 workload contrast** — representative 24Q negative vs separately preregistered HumanEval positive, with CIs/exactness.
3. **Verification-path admissibility** — M4/RTX/B570 path-specific `V_2^micro` with correctness/admissibility markers; explicitly not a hardware ranking.
4. **358H isolated-vs-realized/state decomposition** — show isolated CPU/NPU draft throughput separately from Phase3 realized cost shares.
5. **Cross-platform regime map** — categorical regime/evidence-class summary, not a quantitative leaderboard.

De-prioritize a generic cross-platform acceptance-vs-speedup plot: accepted-token metrics are not uniformly defined and the generic point is already well represented in prior work.

Energy belongs in boundary-separated small multiples, preferably appendix.

## Appendix candidates

- full platform/runtime/model matrix;
- token-exact contract details;
- frozen prompt IDs;
- bootstrap estimators/seeds/order rules;
- verification microbenchmark commands;
- energy sensor boundaries;
- B570 mismatch prompts / formal stop rule;
- CUDA divergence capture;
- 358H runner/provenance amendments and aggregate accounting reconstruction;
- archive/manifest integrity;
- protocol deviations, including the unexecuted M4 corrected synthetic ceiling.
