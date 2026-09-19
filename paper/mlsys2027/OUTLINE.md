# MLSys 2027 paper outline — post-audit freeze

Working target: **10 pages main body, 2 columns, references excluded**.

Authoritative scientific source: `paper/mlsys2027/PAPER_FRAMEWORK_HANDOFF.md`.

## Working title candidates

1. **When Does Speculative Decoding Pay on Consumer Systems?**
2. **HeteroSpec: Correctness-Constrained Realized Costs of Speculative Decoding**
3. **Fast but Inadmissible: Speculative Decoding Across Consumer Runtimes**
4. **Correctness-Constrained Speculative Decoding on Consumer AI PCs**

Title wording is not scientifically frozen.

## Core paper question

> When does speculative decoding become profitable once the execution path is filtered by a strict greedy token-exact contract and the draft cost is measured through the actual runtime state interface?

The paper is not a hardware leaderboard and does not claim heterogeneous speculative decoding as a new algorithm.

## Frozen contribution structure

1. Auditable cross-platform characterization of profitable, exact-but-negative, correctness-blocked, and state-interface-bound regimes on four consumer systems.
2. Correctness-constrained realized-cost accounting that separates complete round cost from the target-forward microbenchmark proxy `V_k^micro`, and separates committed progress `C` from accepted draft tokens/round.
3. Within-platform evidence that correctness filtering can remove the physically cheapest target-verification path.
4. Direct 358H evidence that runtime state reconstruction can erase favorable isolated draft-device throughput.
5. A preregistered M4 code-conditioned positive regime retained alongside a representative negative workload.

## Page budget

### 1. Introduction — ~1.0 page

Lead with the empirical puzzle, not with “heterogeneous SD is new”:
- M4 HumanEval fixed-k2: 1.387x, exact and profitable;
- representative M4 24Q: 0.842x, exact and negative;
- RTX: near-one-step raw batched verification exists but fails exactness; exact serialized controls are negative;
- 358H CPU/NPU: exact, yet verification/state-interface costs dominate.

End with bounded contributions and the claim that runtime admissibility and realized state cost are first-class constraints.

### 2. Background and audited accounting model — ~1.25 pages

Explain draft, target block verification, accepted prefix, correction/bonus, and greedy token-exact reference equivalence.

Define:
- `T_b`: matched target-only baseline cost/token;
- `T_d(real)`: realized draft-subsystem cost/round;
- `T_target,round(real)`: complete realized target-side cost/round;
- `T_x`: residual;
- `C`: committed output tokens/round;
- `V_k^micro`: target-forward PPk/PP1 diagnostic proxy.

Main accounting identity:

`speedup = T_b*C / [T_d(real) + T_target,round(real) + T_x]`

Normalized:

`speedup = C / [D_real + R_target + X]`

Break-even:

`C > D_real + R_target + X`

Explicit warning: `V_k^micro` is not automatically `R_target`.

### 3. Methodology and evidence classes — ~1.5 pages

Platforms:
- MacBook Air M4 / llama.cpp Metal;
- Core Ultra 9 275HX + RTX 5070 Ti **Laptop** / CUDA;
- Core i5-13400 + Arc B570 / Vulkan;
- Core Ultra X7 358H + Arc B390 target + CPU/NPU OpenVINO draft.

Describe:
- frozen model/runtime/quantization per study;
- prompt selection and pairing;
- correctness contract;
- prompt-level estimators and bootstrap;
- raw / primary / mechanism / diagnostic evidence classes;
- energy sensor boundaries;
- preregistration, manifests, archive integrity.

Disclose:
- HumanEval code was not functionally executed;
- early M4 MLX-LM 4-bit path failed exactness and is distinct from final llama.cpp Q8_0 path;
- Windows raw per-run Git provenance is weaker than other final platforms;
- 358H upstream source identity is STRONGLY_SUPPORTED reconstruction, not recovered proof.

### 4. Correctness changes the usable verification path — ~1.25 pages

Central within-platform evidence:
- M4 Metal `V_2^micro` ≈ 1.02–1.08 on an exact qualified path;
- RTX batched `V_2^micro` ≈ 0.98–1.01 but frozen HumanEval exactness fails;
- RTX serialized exact control `V_2^micro` ≈ 2.14–2.43;
- B570 serialized `V_2^micro` ≈ 1.98–1.99 but full HumanEval exactness is only 60/90.

Key sentence: **serialization is an execution property, not an exactness guarantee.**

### 5. Results by regime — ~2.5 pages

#### 5.1 M4: workload-conditioned profitable regime
- representative 24Q: 0.842x [0.809,0.877], 72/72 exact;
- preregistered HumanEval fixed-k2: 1.387x [1.351,1.422], 90/90 exact;
- primary fixed-k2 energy is neutral within uncertainty;
- p_min=.9 energy improvement is secondary, not a replacement primary result.

#### 5.2 RTX 5070 Ti Laptop: fast raw path, exact expensive path
- CPU→RTX exact: 0.404x;
- RTX→RTX exact: 0.650x;
- stable batch-shape numerical argmax flip;
- transfer matters but is not the sole explanation.

#### 5.3 B570: no correctness-admissible optimization result
- fast path 45/90 exact;
- serialized fallback 60/90 exact;
- speed/energy values remain diagnostic;
- paper-facing term `V2_serialized`, never global `V2_exact`.

#### 5.4 358H: exact-but-negative realized-cost regimes
- CPU: 0.734x [0.693,0.771], verification 87.34%;
- NPU: 0.352x [0.333,0.369], full-prefix replay+proposal 58.35%;
- direct committed progress C ≈ 2.46;
- no end-to-end Phase3 energy claim.

### 6. Cross-platform regime map and system implications — ~1.25 pages

Organize around regimes, not hardware winners:
- profitable + exact;
- exact but unprofitable;
- fast but inadmissible;
- state-interface bound.

Discuss implications:
- correctness qualification before performance promotion;
- persistent draft state as future design target;
- workload-aware speculation;
- microbench opportunity versus realized round accounting.

Do not turn future designs into current contributions.

### 7. Related work — ~0.75 page

Must explicitly position against:
- classic speculative decoding / assisted generation;
- heterogeneous SD: Dovetail, DuoDecoding, Mirror-SD;
- systematic SD performance modeling/production studies;
- heterogeneous inference / AI-PC runtimes;
- numerical reproducibility and execution-shape sensitivity.

Do not claim first heterogeneous SD or first generic SD cost model.

### 8. Limitations and conclusion — ~0.5 page

Required limitations:
- four platforms / mostly one model family;
- cross-platform software/hardware confounding;
- token exactness is a chosen deterministic contract;
- no HumanEval pass@k;
- M4 session/thermal drift not captured by prompt bootstrap;
- energy boundaries differ;
- Windows raw per-run provenance gap;
- 358H reconstructed source provenance;
- no measured state-reuse intervention.

## Main figures

1. correctness-constrained realized-cost schematic;
2. cross-platform regime map with separate correctness encoding;
3. `V_2^micro` path/correctness figure;
4. 358H CPU/NPU cost decomposition;
5. M4 representative-vs-code-conditioned contrast.

Energy belongs in boundary-separated small multiples, preferably appendix.

## Appendix candidates

- full platform/runtime matrix;
- token-exact contract details;
- frozen prompt IDs;
- bootstrap estimators/seeds/order rules;
- verification microbenchmark commands;
- energy sensor boundaries;
- B570 mismatch prompts;
- CUDA divergence capture;
- 358H runner/provenance amendments;
- archive/manifest integrity.
