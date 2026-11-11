# Related-Work Boundary Audit — v0.8.3 Phase 5

This calibration used only descriptions and citations already present in the Phase-4 manuscript and `references.bib`. No external literature search, new citation, or firstness claim was added. “Support” below means the bounded statement was already paired with a citation in the manuscript; it is not a fresh verification of the cited paper.

| Existing phrase or topic | Existing cited source(s) | Claim made by the Phase-4 wording | Current manuscript support sufficient? | Action | Revised phrase or boundary |
|---|---|---|---|---|---|
| Speculative decoding amortizes target work | `leviathan2023` | Algorithmic motivation and sampling preservation under assumptions | Yes for bounded background | Keep, shorten | Target amortization under algorithmic assumptions |
| Verification dominance, workload/batch effects | `illusion` | Effective verification parallelism can limit gains | Yes as existing cited description | Keep, shorten | Verification dominance and batch effects in vLLM |
| Conditional cost and runtime policy | `specllm` | Control and realized cost were studied before | Yes as existing cited description | Keep, shorten | Conditional execution cost and runtime control |
| Edge–cloud profitability | `distance` | Analytical profitability conditions predate this paper | Yes as existing cited description | Keep, shorten | Edge–cloud profitability conditions |
| Consumer Apple silicon gains/slowdowns; quantized Metal verification; agreement and batch-shape changes | `lossless` | Consumer slowdowns, correctness gating, and path sensitivity are close prior art | Yes for the already described bounded observations; no universal claim | Rewrite compactly | Five backend configurations with gains and slowdowns; one ineffective batch-parallel path; output agreement and target-only argmax changes |
| GPU/CPU and GPU/NPU placement | `dovetail`, `duodecoding`, `mirror` | Heterogeneous placement exists | Yes for the existing broad descriptions | Combine | Prior GPU/CPU or GPU/NPU paths; no claim of discovering placement |
| Analytical model and compiler partitioning | `compilerassisted` | Cost/performance modeling and CPU/GPU partitioning exist | Yes for the narrower retained claim | Weaken detail | Analytical cost model with compiler-oriented CPU/GPU partitioning |
| Joint draft/verification/CPU–NPU design | `lever` | Heterogeneous co-design exists | Yes for the existing cited description | Keep, shorten | Joint optimization for a smartphone target |
| Incremental draft KV reuse | `compactmemory` | State reuse exists as prior art | Yes for the cited bounded claim | Keep, shorten | Compressed draft KV memory; no claim that state reuse is new |
| Ragged-batch and numerical mismatch | `batchcorrect` | Prior correctness forensics distinguishes error types | Yes for the existing description | Keep, shorten | Ragged-batch synchronization versus residual mismatch |
| Numerical variation and deterministic inference | `numerics`, `llm42` | Numerical path dependence is established | Yes for the existing cited descriptions | Rewrite boundary | Numerical path dependence is not new here |
| Adaptive serving/configuration/context policies | `turbospec`, `banditspec`, `aclheterospec` | Adaptive control exists | Yes for the existing descriptions | Combine | Adaptive control is established; M4 Guard has no demonstrated incremental benefit |
| “Our distinction” scattered across five paragraphs | Existing manuscript results | Could read as several broad novelty claims | Yes for endpoints, but diffuse | Rewrite | Prospectively captured-ID path qualification; frozen reserved complete-trajectory prediction; one realized state-interface accounting result |

## Closest-work map

| Prior work owns, as already described in the manuscript | What this paper adds on its tested paths |
|---|---|
| *Lossless but Not Free*: consumer gains/slowdowns, ineffective verification in a quantized Metal configuration, output agreement, and target-only batch-shape change | Prospective RTX/B570 direct-ID path qualification separated from historical timing; a frozen B570 reserved complete-trajectory predictor |
| *Compiler-Assisted Speculative Sampling*: analytical cost modeling and compiler-oriented CPU/GPU partitioning | Direct generated-ID qualification and measured output-trajectory prediction, not a new analytical performance model |
| *Lever*: heterogeneous draft/verification/CPU–NPU co-design | One measured 358H combined state-interface cost boundary, not a general heterogeneous-placement law |
| ACL 2026 *HeteroSpec*: context-adaptive verification allocation | A frozen target-partition predictor for complete reserved serialized outputs, not an adaptive verification policy |
| Numerical reproducibility works: batch-shape/path sensitivity and deterministic inference | A path-specific admissibility gate and prediction protocol, not the discovery of numerical sensitivity |

The Introduction now places established background immediately before the three contributions. Its first-page order remains qualification → prediction → realized cost. Citation keys are unchanged; no `first` claim was introduced.
