# Portable method and representative validation

## The intended result

The goal is a reusable integration that improves **actual end-to-end speculative inference by more than 5% across a representative supported domain in mainstream frameworks**. It is not satisfied by a fast isolated kernel, one favorable shape, a larger proposal length, a weaker baseline, or a single selected A5000 configuration.

Tensor parallelism (TP), key/value (KV) cache, bfloat16 (BF16), and streaming-multiprocessor architecture (SM) retain the definitions in the other design files. End-to-end latency here means the complete resident request from admission to terminal state, including drafting, target verification, sampling, cache reconciliation, scheduler work, communication and synchronization. Queueing and full process lifetime are additional separately reported boundaries.

The 944-request protocol is an **initial engineering and finite scale-transition panel**. It is not the final evidence for the broader goal. No experiment in this PR has run. A fixed narrow panel is useful to detect bugs and attribute mechanisms, but a general claim requires the independent confirmation layer below.

## Proposed reusable interface

The candidate is a phase-aware verification-plan interface and backend lowering, provisionally described as a **native verification plan**. This is a design name, not a completed algorithm or established novelty claim. It carries query ownership, valid cache visibility, numerical policy and collective schedule explicitly from the framework's proposer through verification and state commit.

The common layer defines semantics and test cases; a small engine adapter extracts real request/cache metadata; a backend-specific lowerer chooses a measured, reference-compatible schedule. It does not replace the engine's proposer, scheduler or optimized kernels by default. vLLM and SGLang require independently tested adapters. A CPU schema or a n-gram plugin is insufficient to claim that either integration exists.

A useful scheme should reduce repeated work while preserving the framework's actual deployed numerical and state contract. The exact mechanism must be established by traces. Candidate opportunities are:

1. **Shape-aware arithmetic-preserving execution.** Group only independent verification rows with compatible arithmetic/state requirements, and use efficient row/channel schedules without changing their reduction. A useful grouping must beat the native compatible batched path, not only a per-row loop.
2. **Reusable request/phase plans.** Reuse validated descriptors and graph metadata when the complete cache/phase/epoch key allows it; avoid redundant CPU/device transitions and intermediate metadata reconstruction. Prove that the selected engine actually repeats this work before claiming it as a gap. A stale plan, changed block table, rollback or request reuse invalidates the relevant entry.
3. **Collective-aware lowering.** Co-schedule independent verification rows while preserving rank-order arithmetic and collective participation. Measure reduction in actual communication/submission overhead. Native speculative execution already batches many rows, so this opportunity may be absent.

These are hypotheses with an explicit no-op outcome: if native kernels/scheduling already implement the useful transformation, reuse them and report no additional method benefit. A new interface by itself is not evidence of a new acceleration algorithm. The novelty comparison must include the pinned frameworks' batch-invariance, speculative scheduling, graph caching and collective capabilities.

## Separate controller research track

If fixed-policy execution optimization has insufficient measured opportunity, investigate a separate joint horizon/plan controller rather than increasing proposal length globally. The possible distinction is to include numerical-legality groups, actual page geometry and tensor-parallel critical-path cost in a request-level decision. This distinction is a research hypothesis requiring a related-work and native-feature comparison.

Ordinary adaptive speculation is already present. The pinned vLLM configuration includes `num_speculative_tokens_per_batch_size` and `enable_adaptive_verification`. Its adaptive-verification documentation covers model-based proposers and suffix, including online calibration, slot survival ranking and startup shape-cost profiling. A DSpark-only field docstring in `speculative.py` is stale relative to the broader runtime implementation; it is not a DSpark-only guard. Ordinary n-gram has no corresponding confidence/adaptive-enable attributes in the inspected speculator, so this does not imply adaptive n-gram support. Dynamic horizon selection or generic cost-aware budgeting alone is not new. A candidate controller must be compared with the strongest eligible native adaptive policy, not only a fixed-k baseline.

At a decision boundary, select proposal horizon k and legal verification plan g to maximize predicted **actually committed output tokens divided by complete cycle time**, subject to memory, numerical/state legality and latency constraints. Estimate committed output from the actual acceptance/EOS/cap/pending-token semantics, not proposal count. Model measured critical-path time, including overlap, rather than blindly adding overlapping draft, target and communication intervals. Count the controller's own CPU/GPU time and synchronization.

Use only a development trace to fit a small bounded policy and its uncertainty. Freeze policy, search budget and fallback before held-out tests. When confidence is low or predicted benefit is below overhead, use the native policy. Test deliberately adverse conditions: low acceptance, short outputs, page boundaries, changing load, cache pressure and slow communication. Record policy switches, decisions and costs; do not remove low-acceptance inputs.

Use a 2×2 ablation with the same proposer/model/resource envelope: native versus new controller, crossed with native versus candidate execution adapter. The controller's generic gain, the adapter's gain and their interaction are different effects. This track is a new registered research epoch; it does not change the fixed-k=3 first panel after results. A positive joint-system result cannot be attributed wholly to HeteroSpec grouping.

## Separate collective engineering track

If TP4/8 needs a newly declared ordered reference, compare full all-gather plus rank-order sum with a reduce-scatter-then-all-gather decomposition that preserves each element's rank-order FP32 sum and final cast. The existing `reduce_scatter_batch_invariant` helper is a source starting point, not a two-line validated replacement.

For P ranks and N bytes of per-rank input, ideal useful received payload per rank changes from `(P-1)*N` for all-gather of all contributions to `2*(P-1)*N/P` for a balanced reduce-scatter/all-gather decomposition. This ignores transport/protocol overhead and is not a latency prediction. Two collectives can be slower than one for small q and small messages. The existing fixed-order sum is already one Triton kernel, so there is no assumed Python per-rank sum loop to eliminate.

The current helper partitions rows; q=4 with TP8 can leave ranks owning no row. A real all-reduce implementation must define element-level or variable-count partitioning, zero-owner participation, exact reconstruction, dtype/rounding and capture behavior. It must prove equality to the declared ordered reference, not claim equality to stock NCCL. Give this generic optimization equally to all compatible native and candidate arms; otherwise it artificially inflates the method's increment.

## Concrete SM86 kernel opportunity and its attribution limit

At vLLM `75be5c3919b6a82fa1885c0d0a2250adba477413`, [batch_invariant_configs.py](https://github.com/vllm-project/vllm/blob/75be5c3919b6a82fa1885c0d0a2250adba477413/vllm/model_executor/determinism/batch_invariant_configs.py) has tuned architecture families for SM89, SM90, SM100 and SM120, not SM80/86. The [Ampere fallback](https://github.com/vllm-project/vllm/blob/75be5c3919b6a82fa1885c0d0a2250adba477413/vllm/model_executor/determinism/batch_invariant.py) uses a default BF16 128×128×64 tile with eight warps and three stages. Small verification row counts can therefore be a concrete tuning target.

A bounded development experiment can test smaller row/column tiles and launch schedules for **actual TP-sharded model shapes**, while preserving the original K reduction tile, accumulation order, casts and epilogue. Keeping K fixed is a starting constraint, not a proof: compiler transformations and tiling can still change numerical results, so full operand and model-state gates remain mandatory.

Generic SM86 tuning must be given to the strong baseline too. Compare stock native speculation, native speculation plus common tuning, and common tuning plus the candidate plan. Report generic backend improvement separately from the plan's incremental gain. If the gain is entirely common tuning, call it an Ampere backend optimization, not evidence that HeteroSpec's grouping caused it. It may still be useful engineering and suitable for an upstream contribution, but it is a different scientific claim.

Use a separate development corpus and fixed candidate-search budget. Freeze the winning configuration and rationale before held-out confirmation. Never increase verification width solely to reach a favorable matrix shape. Longer drafting changes accepted work, rejection frequency and draft cost; any adaptive proposal algorithm requires its own comparison against mature native adaptation.

## Objective and falsification

For each matched scenario, let T_base be complete request time for the strongest native speculative baseline under the same model, hardware allocation, proposal configuration and supported numerical contract. Let T_new be time with the candidate. Define ratio r=T_new/T_base, latency reduction 1-r, and speedup 1/r. The practical goal is r<0.95, not merely a kernel ratio below 0.95.

If f is the baseline fraction affected by the optimization, s its measured local speedup, and h added overhead as a fraction of baseline request time, then the planning approximation is `savings=f*(1-1/s)-h`. It is useful only after profiling this actual framework/model/topology. Existing Q4 single-card ratios and vendor SM100 benchmarks cannot fill f or s.

Fail the broad hypothesis if the apparent benefit disappears against the commonly tuned native baseline, violates the declared output/state contract, comes only from a tiny selected workload subset, or is offset by communication/scheduling/state overhead. For fixed-policy lowering, changing proposals also invalidates its isolated-effect claim. The separate controller track may change proposed/verified work under the frozen common proposer and valid output/state contract; its gain requires the 2×2 attribution rather than a same-proposal claim. Preserve the result and narrow the claim if appropriate. The >5% target never permits deleting negative cells, moving failed runs out of the ledger, extending a sample until positive, or weakening numerical requirements.

## Independent representative confirmation

After the engineering gates succeed, freeze a new confirmation registration with all final models, source revisions, workload identities, serving settings and budgets. Proposed coverage:

- **Frameworks:** vLLM and SGLang, with independently qualified adapters and each framework's strongest eligible native speculative configuration. If only one works, the claim is single-framework.
- **Models:** R1-Distill-Qwen-14B and 32B for size transfer, plus an independently qualified dense architecture such as Mistral-7B-v0.3. The third model is a candidate, not yet a frozen/loaded checkpoint. Two Qwen sizes alone do not demonstrate architecture independence.
- **Proposers and production settings:** n-gram is the initial integration smoke, not a sufficient proxy for all mature speculative decoding. Confirmation must include a supported learned proposer family such as an actually available EAGLE/DFlash/draft-model pair, with checkpoint/tokenizer and engine support verified before freeze. Select the strongest eligible native proposer/settings using independent development inputs, not confirmation outcomes. At least two proposer families must be represented across the final cells; otherwise narrow the claim to the tested family. The counts below assume one frozen proposer policy per model/framework cell, not a hidden extra proposer factor. Preserve supported CUDA graphs, native scheduling, common tuning and fusion opportunities in both controls and candidate. If the candidate needs graphs off or a more expensive numerical mode, compare its full cost with the optimized native deployment rather than disabling baseline features to equalize it artificially.
- **Inputs:** 64 held-out roots, eight in each of four application families × two length bands. Families: code completion, mathematical reasoning, factual/document question answering and multi-turn text conversation. Bands: approximately 128–512 and 2048–4096 input tokens, checked after each model's tokenizer/template. Freeze assignments and actual token counts; do not force different semantics to match lengths.
- **Output:** freeze task-appropriate caps before timing, with a total allocation that holds prompt, output and lookahead. Use an 8192-token allocation if the long-input/long-output panel requires it; requalify memory and state. Report truncation and task completion. Latency to a truncated answer is not successful-task latency.
- **Load:** batch-1 latency and fixed four-request concurrency as distinct regimes. Add an open-loop, near-saturation/SLO study only after its separate arrival trace and adequate request count are frozen. SLO means service-level objective; do not infer reliable tail latency from a tiny request panel.
- **Sessions:** three independently restarted sessions with balanced arm order and frozen request/arrival order. State reuse and warmup policy must match each load regime; concurrent panels need a complete warm phase rather than interspersed serialized warmups that change their offered load.
- **Arms:** stock native speculation, native speculation with every common backend optimization, and that same commonly optimized baseline plus the candidate. The stock/common difference isolates ordinary tuning; the common/candidate difference is the method's incremental effect.

The prospective 64 roots ×3 models ×2 frameworks ×2 load regimes ×3 sessions ×3 arms yields **6912 measured requests**. With a full equal-size warm phase per arm/session and two primer requests per worker, this would require 6912 warm requests +216 primers = **14,040 total requests in 108 workers**, before all qualification, failed attempts and optional SLO work. This count is not an instruction to launch now. First estimate complete wall time, GPU-hours, memory and disk from receipts, then reserve sufficient resources. The model/runtime/adapter availability gates may stop or reduce the supported scope; such reductions must be recorded before confirmation, not selected from its results.

Keep batch-1 request latency and concurrent throughput/makespan as separate endpoints; do not average unlike metrics into a single >5% number. Predefine application weights from an intended use distribution or use equally weighted scenario families explicitly. Report aggregate and per-framework/model/length/load effects, individual roots, uncertainty and worst regressions. A favorable average hiding substantial regressions is not a universal acceleration claim.

Use root resampling with all repeated conditions for a root kept together and session-aware analysis/diagnostics. Three sessions remain limited evidence of deployment variability; show session contrasts and do not overstate asymptotic tail confidence. Freeze multiplicity treatment and the exact primary estimands before runs. A broad claim should be supported by representative aggregate improvement and consistent evidence across the declared frameworks, with every exception visible; a single selected cell exceeding 5% only supports that cell.

## Development sequence

1. Establish unchanged mainstream execution, resource inventory and real bottleneck fractions.
2. Build the smallest adapter that preserves native ownership/state and exposes a measured opportunity.
3. Implement common SM86 tuning or collective support separately, with identical availability to controls.
4. Complete finite numerical and 2→4→8 scale gates. Use their results for diagnosis, not final generalization.
5. Freeze the method and independent confirmation corpus; run the representative study without outcome-driven changes.
6. Deliver rebuildable adapters, qualification tests, all positive/negative results, applicability conditions and complete costs.

This roadmap remains implementation work. The present PR supplies source-grounded design, a testable CPU preflight and explicit falsification criteria, not a completed portable accelerator or a measured >5% result.
