# Initial MLSys 2027 paper outline

Working target: **10 pages main body, 2 columns, references excluded**.

The allocation below is a planning budget, not a formatting override.

## Working title candidates

1. **When Is Speculative Decoding Profitable on Consumer Hardware?**
2. **Correctness-Constrained Speculative Decoding on Consumer AI PCs**
3. **The Hidden Cost of Exact Verification in Speculative Decoding**
4. **HeteroSpec: Correctness-Constrained Speculative Decoding Across Consumer Hardware**

Do not freeze the title until 358H Phase 3 closes.

## Core paper question

Why do superficially similar speculative-decoding configurations with high draft acceptance produce opposite performance outcomes across consumer platforms?

## Proposed contribution structure

1. A correctness-constrained cost model that separates draft cost, target verification amortization, runtime/state overhead, and committed work per round.
2. Cross-platform evidence that cheap **raw** target batching is not sufficient when the fast path violates the chosen token-exact contract.
3. Workload-conditioned evidence that an exact profitable regime exists on M4/Metal, while exact CUDA controls and tested B570/Vulkan paths are negative.
4. 358H threshold validation: whether faster CPU/NPU drafting survives verification and state/runtime overhead end to end. Final wording waits for Phase 3.

## Page budget

### 1. Introduction — ~1.0 page

Motivation:
- speculative decoding promises latency reduction by converting autoregressive serial work into block verification;
- consumer systems contain heterogeneous spare compute;
- the intuitive predictor "high acceptance + fast draft" is incomplete.

Lead with the empirical puzzle:
- M4 HumanEval fixed k=2: exact and profitable;
- Windows exact controls: similarly high acceptance but negative;
- fast CUDA batching is physically cheap but correctness-blocked.

End with contributions and bounded claims.

### 2. Background and cost model — ~1.25 pages

Explain:
- draft sequential proposal generation;
- causal block verification;
- accepted-prefix / correction / bonus behavior;
- strict greedy token-exact contract.

Define:
- `T_b`
- `T_d(k)`
- `T_v(k,e)`
- `T_x(e)`
- committed tokens `C`
- `V_k = T_v(k)/T_b`
- correctness-constrained `V_k^exact`

Main equation:

`T_spec/token = [T_d(k) + T_v(k,e) + T_x(e)] / C`

Break-even:

`C > T_d(k)/T_b + V_k(e) + T_x(e)/T_b`

### 3. Methodology — ~1.5 pages

Platforms:
- M4 / Metal
- 275HX + RTX 5070 Ti Laptop / CUDA
- i5-13400 + Arc B570 / Vulkan
- 358H + B390 target + CPU/NPU draft, pending final Phase 3

Describe:
- model pair / quantization per matched studies;
- batch-1 greedy setting;
- HumanEval30 selection and pairing;
- exactness gate;
- verification microbenchmarks;
- timing and bootstrap aggregation;
- energy boundaries;
- preregistration / frozen configs;
- archive/manifests.

Explicitly say platform comparisons are mechanism comparisons, not hardware-only controlled benchmarks.

### 4. Why acceptance is not enough — ~1.25 pages

Use the M4 vs RTX contrast:
- both high-acceptance HumanEval regimes;
- M4 exact V2 near one;
- CUDA raw V2 near one but fast path can flip greedy argmax;
- exact CUDA fallback V2 > 2;
- same workload, opposite end-to-end outcome.

This is likely the central figure/table.

### 5. Cross-platform results — ~2.5 pages

#### 5.1 M4: profitable exact code-conditioned regime
- representative 24Q remains negative;
- HumanEval30 fixed k=2 positive;
- correctness and energy qualification;
- workload dependence.

#### 5.2 RTX 5070 Ti Laptop: fast raw verification, expensive exact verification
- CPU-to-RTX and same-GPU exact controls;
- native/custom integration evidence;
- divergence mechanism as batch-shape numerical argmax flip;
- avoid universal CUDA claims.

#### 5.3 B570: serialization improves but does not guarantee exactness
- fast path correctness failure;
- serialized fallback exactness improves but remains incomplete;
- V2 ~2 and strongly negative diagnostic performance/energy;
- do not call serialized path `V2_exact` if full-workload exactness is not established.

#### 5.4 358H: predictive draft-cost threshold validation
- reserve final wording;
- show isolated CPU/NPU draft trend and Phase-2 prediction only if final paper narrative benefits;
- final end-to-end result must come from Phase 3.

### 6. System implications / discussion — ~1.25 pages

Potential lessons:
- verification amortization must be correctness-filtered;
- acceptance is necessary but not sufficient;
- state reuse and runtime integration can dominate;
- faster heterogeneous draft compute can fail to translate to system speedup;
- energy follows time-to-solution, not instantaneous watts alone.

Limit causal claims:
- unified memory is not isolated;
- one CUDA numerical capture does not identify a universal kernel defect;
- Vulkan/B570 result is backend/configuration bounded;
- NPU conclusions must remain tied to the tested OpenVINO state-management path.

### 7. Related work — ~0.75 page

Organize by:
- speculative decoding algorithms;
- assisted generation/runtime implementations;
- heterogeneous inference / AI-PC accelerators;
- inference performance and energy measurement;
- numerical reproducibility / exactness in ML systems.

### 8. Limitations and conclusion — ~0.5 page

Keep limitations explicit rather than burying them.

## Appendix candidates — separate upload

Reviewers are not required to read appendices, so no central claim may depend on them.

Possible appendix content:
- full platform/runtime table;
- exact-token contract details;
- complete HumanEval prompt IDs;
- verification microbenchmark commands;
- bootstrap procedure;
- power-sensor boundaries;
- B570 mismatch prompt list;
- CUDA divergence logit-capture details;
- 358H provenance amendment / runner-state qualification;
- archive integrity manifests.
