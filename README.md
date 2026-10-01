# HeteroSpec

Execution-path qualification, prospective trajectory prediction and realized cost in speculative decoding on consumer systems.

**Start with [HANDOVER_CURRENT.md](paper/mlsys2027/HANDOVER_CURRENT.md)** for the current paper, evidence ledger and authorized work. [REPO_STATUS.md](REPO_STATUS.md) summarizes repository state. Older platform reports and versioned handovers retain their original campaign context.

## Current paper and main

Main contains manuscript v0.8.6 through [PR #46](https://github.com/leecdiang/HeteroSpec/pull/46), integration anchor `361cb43a67f7fd9bfae95de4cdf7e816c46bbe90`. This resolves #45's stacked merge into the v0.8.5 branch. Later documentation commits can follow the anchor; resolve the actual remote HEAD before starting work.

The current paper's central observation is a draft-free target-only UB1 predictor, frozen before reserved B570 live outcomes, matching **72/72 complete generated-ID trajectories on 24 prompts × three repetitions**. Reference/live is only **60/72**, so successful prediction does not make that path lossless-compatible.

Supporting evidence remains separate:

- **B570 same-state fork:** scores change at 72/72 sampled forks, while immediate raw top-1 and actual decisions change at 0/72. Persistent UB128 continuation changes 18/72 later trajectories on six prompts; it does not isolate a single-block downstream cause.
- **RTX:** earlier target-only UB2 H1 fails discovery at 24/36, reserved 0. Independent H2/R_ONLY program replay matches live 72/72 on a new cohort while reference/live remains blocked at 60/72. Programs share numerical libraries and H2 constructs its tape using draft computation.
- **RTX qualified cost:** a separate freshly qualified serialized path has target/serialized ratio **0.646× [0.630, 0.660]**, with 0/30 prompts faster, within an instrumented post-prefill CLI boundary.
- **358H:** the measured CPU/NPU paths are unprofitable; conditional zero-draft/residual bounds remain below parity at fixed measured progress and target work. The runtime attempt stopped at qualification.
- **M4 runtime:** Guard beats target-only but loses to fixed speculation; the hindsight two-fixed-mode oracle leaves little additional opportunity. This is a measured negative incremental-control result.

The paper makes finite, tested-path claims, without a unique numerical cause, universal transfer, general NPU weakness or adaptive-policy win. Exact IDs mean paired greedy output equality, not HumanEval functional pass@k. Existing campaigns are closed.

## Read and reproduce v0.8.6

- [Main PDF](paper/mlsys2027/manuscript/output/manuscript-v0.8.6.pdf): 10 body + 2 reference pages.
- [Separate appendix](paper/mlsys2027/manuscript/output/appendix-v0.8.6.pdf): 12 pages.
- [Source ZIP](paper/mlsys2027/manuscript/output/overleaf-convergence-v0.8.6.zip) and [anonymous evidence index](paper/mlsys2027/manuscript/output/anonymous-evidence-index-v0.8.6.zip).
- [Build/replay instructions](paper/mlsys2027/manuscript/README.md) and [exact artifact manifest](paper/mlsys2027/evidence/FINAL_ARTIFACT_MANIFEST_V086.json).

The hardware-only proof is an internal section-removal check, not a submission manuscript. Source/array/archive identities and access limits are disclosed in the versioned evidence records. Model weights, downloaded datasets, caches and most machine-local logs are absent by policy. Set HETEROSPEC_ROOT, HETEROSPEC_MODEL_ROOT, HETEROSPEC_DATA_ROOT and HETEROSPEC_CACHE_ROOT as needed; see [reproduction](docs/reproduction.md) and [data policy](docs/data_policy.md).

## Next work

The author selected RTX A+B as optional strengthening studies: a fresh same-set predictor comparison and a matched target/batched/serialized qualification–cost study. Use [the complete RTX prompt](docs/experiments/RTX_A_B_V3_EXECUTION_PROMPT.md), initially **PREPARE_ONLY**. Reserved execution follows review of the exact frozen protocol/source. Neither a positive result nor A success is required to report B.

Do not start B570 dense scanning, extra backends, 358H persistence or M4 variants from a limitation paragraph. Current guardrails and stopping rules are in the handover. Public release, arXiv and conference submission are separate decisions; no DOI or submission is claimed here.

## Repository layout

- scripts/: runners, telemetry, analysis and verifiers; legacy paths remain for provenance/imports.
- benchmarks/: protocols, frozen cohorts, evidence reports and build/runtime identities.
- artifacts/: indexed paper-critical archives under the data policy.
- analysis/ and reports/: processed data and historical platform reports.
- paper/mlsys2027/: current manuscript, evidence and versioned review records.
- docs/: reproduction, data policy, history and the next RTX execution prompt.
- configs/ and requirements/: portable configuration and platform dependencies.
