# Independent review of the next HeteroSpec study

## Decision and scope

**The new research evidence is ready for author review in PR #221. No blocking issue remains in the frozen diagnostic source, its observed result, the proposed service figure, or the static guard report. This does not qualify a production optimization or establish a general 5% gain.**

The most useful new finding is a conditional positive result: the bounded CPU fixture supports the predeclared q4-based macro and shortened-frontier contracts. It also supplies a concrete limit. At the fifth frontier, the extra fifth output differs between q4+q1 and trimmed q8 in both histories even though the four primary consumer vectors, materialized active state, native geometry and common continuation agree. The result must retain both facts.

This review independently inspected source and archived implementation bytes, reran six host-only checks, recomputed the service contrasts, viewed the complete proposed figure, and read every raw diagnostic blob. It did not execute a model, native probe or GPU job. The experiment owner executed one CPU child after the eight source files were published and checked at [commit ef276632](https://github.com/leecdiang/HeteroSpec/tree/ef2766327e7821fe188d1ad788b2c3b05531eb9a/benchmarks/frontier_cost_v1/next_study/q4_frontier). The pre-execution review and subsequent evidence review are separate receipts.

## 1. What the CPU result actually establishes

The fixed deployment is the existing untrained, two-layer, vocabulary-128 F32 model, with CPU execution, one thread, F16 KV, context 1024, microbatch limit 32, non-Flash attention and the reconstructed LOCAL frontend. Prefixes of length 248 and 252, all operation tokens, and the common continuation token are forced inputs. No natural speculative acceptance, EOG or output-cap event is sampled. The diagnostic reference is defined locally; it is not the paper's historical reference R. [Protocol and frozen source](../q4_frontier/README.md)

| Comparison, at each of the two histories | Primary operation vectors | State and continuation obligation | Observed result |
| --- | --- | --- | --- |
| q4+q4 repeat versus its own first capture | All 8 complete vocabulary rows | Initial and final active-state bytes/geometry; common q1 continuation vector/state/geometry | Equal |
| q8 versus q4+q4 | All 8 complete vocabulary rows | Same obligation at P+8 | Equal |
| q8 trimmed to P+4 versus q4 | First 4 complete vocabulary rows | Same active frontier at P+4 and common q1 continuation | Equal |
| q8 trimmed to P+5 versus q4+q1 materialization | First 4 complete vocabulary rows | Same materialized active frontier at P+5 and common q1 continuation | Equal |

These are eight comparison records, including two own-path repeats, with 64 primary comparison fields. They are not 64 independent statistical observations. The six remaining contexts are explicitly labeled reference captures.

The independent audit read all **30 content-addressed raw blobs, totaling 7,385,976 bytes**, without importing the experiment's verifier. It recomputed each byte comparison, each expected geometry, every prefix/operation/continuation stage and the physical-width histograms. The complete work is **14 contexts, 146 decode API calls, 146 observed physical calls, 3,612 target rows, four trim calls and one model load**. All 42 stages are present. The observed run stayed inside the predeclared limits and used one native child with no retry. Source, build, binary, model, job, logs and loaded-module identities agree with the frozen receipts. [Independent raw audit](q4_evidence_review.json), [offline audit implementation](audit_q4_raw.py), [pre-execution review](q4_preexecution_review.json)

### The fifth-output difference is part of the result

The q1 materialization physically requests and copies a fifth logit vector through the unchanged frontend. The protocol saved that vector but excluded it from the four-consumer equality obligation before execution. The wide path also saved its generated extras. Their equality and finite status are diagnostic observations, not hidden additional primary consumers.

| History length | Different fifth-vector float bit patterns | Maximum absolute difference | Reference / wide argmax |
| ---: | ---: | ---: | ---: |
| 248 | 117 of 128 | 3.5762786865234375e-7 | 13 / 13 |
| 252 | 128 of 128 | 3.889203071594238e-6 | 14 / 14 |

Both fifth vectors are finite. Equal argmax does not make the vectors equal, and this review does not use a numerical tolerance to promote them to equality. The macro q8-versus-q4+q4 comparison, by contrast, includes all eight outputs and passes exactly. [Raw fifth-vector statistics](q4_evidence_review.json)

The distinction matters operationally. A future path may use this restricted frontier contract only if its real consumer graph has the same obligations. If the fifth output is consumed, this diagnostic is not a qualification for that use. The existing worker consumes all requested k+1 rows; its production contract cannot be relaxed by citing a projected four-row comparison. No historical-R qualification or production full-mask equivalence follows from this pass.

The result shows that the earlier q1-reference rejection does not exhaust the possible q4-based paths on this fixture. It does not supply stage costs, a service speedup, a trained-model result, a quantized CUDA recipe result, an acceptance probability, or evidence of broad transfer. The production cost admission remains unresolved. If a future diagnostic fails before a later branch, that branch must remain `NOT_RUN`; this completed panel has no such omitted branches.

The final algorithm note correctly connects this boundary to the real worker. `L_4`, the fifth operation vector, is produced after the fourth proposal and judges the fifth proposal. A k7 rejection there leaves four accepted proposals, trims to `B+5`, and carries the correction as an emitted but unmaterialized pending token. A k3 all-accept bonus instead comes from `L_3` and leaves target KV at `B+4`. The diagnostic's fifth input was forced, not established as either real pending token. Its fixed-token continuation clears the prior output owner and never reads the unequal `L_4`. The proposed four-step real-request closure therefore remains a separate, versioned protocol; the k3-to-k7 chain requires a new qualified request loop and does not alter an existing frozen S3 or production panel. [Algorithm implications](../guard_audit/ALGORITHM_IMPLICATIONS.md), [final interpretation review](interpretation_review.json)

### Geometry is a separate obligation

The native geometry check requires dense sequence-0 occupancy, positions, extent and a successful native append guard. That guard includes physical head == next. A rejection would be a failure of this precise dense-append contract, not automatically a numerical error or proof that every possible continuation is wrong. The added failure observation reports accessible cache metadata and explicitly does not claim to read the hidden head value. No geometry rejection occurred in this run. Active sequence export excludes dead KV cells; the state comparison is not a demand that all unused allocation bytes match. [Frozen source](../q4_frontier/frontier_probe.cpp), [pre-execution review](q4_preexecution_review.json)

## 2. The recovered service contrast is valid and narrower than the overall speculative gain

The proposed Fig. 5 restores `L_P_D4 / W_L4_D4`, which is already in the original five-comparison family. Independent recomputation confirms all 15 ratios of totals, the root-level geometric summaries, all 220 displayed root points and the strong-control percentages. The published adjusted intervals are retained and transformed; this review does not claim to regenerate their bootstrap from absolute root times. [Independent arithmetic](five_contrasts_review.json), [figure and scope review](figure_review.json), [proposed figure explanation](../paper_audit/README.md)

| A5000 deployment | Same-panel D4 time reduction | Published adjusted interval as time reduction |
| --- | ---: | ---: |
| Qwen3-8B | 2.0116% | 1.4441%–2.4411% |
| Qwen3-14B | 1.0807% | 0.8310%–1.2824% |
| Llama-8B | 1.5641% | 1.1548%–1.8320% |

This contrast changes both projection and cut scope. It is not a pure packing effect or pure cut effect. The five-member family is explicit in the pinned manuscript evaluation, and the Qwen14/Llama original summaries also record family size five. Adding the fifth display row does not introduce a newly selected unadjusted test.

The full PNG was visually inspected. The 1.0 reference line, Llama root-level slowdowns, A5000 label, joint-effect explanation and Qwen8 order-confounding note are visible. No meaningful clipping or label overlap was found. All 220 roots remain in the figure. Qwen8 and Qwen14 share root identities; 44 displayed root instances are not 44 independent new tasks. The fixed relative ordering of the Qwen8 D4 arms remains a limitation of causal attribution. [Figure review](figure_review.json)

The paper addition correctly leaves the requested same-panel phase decomposition open. It does not construct that decomposition by subtracting unrelated heavy or factorial timings. Its worker-lifecycle values use a different denominator and are not presented as TTFT or resident request latency. Defining the goal as 5% lower resident-service time gives additional reductions of 3.0498%, 3.9622% and 3.4905% relative to the current candidates, through `1 - 0.95/current_ratio`. These are conditional algebraic requirements, not forecasts or additive percentage points. [Paper addition](../paper_audit/README.md)

## 3. The guard findings are source-backed scope gaps

The static matrix's **20 source identities, 10 guard rows and 35 exact source regions** were independently checked against the original release ZIP and the separately identified reconstructed frontend. Four source-region end lines originally extended beyond the file's true end; those references were corrected and both verifiers now enforce region bounds. [Binding review](guard_bindings_review.json), [guard matrix](../guard_audit/GUARD_MATRIX.json)

Three distinctions must survive manuscript editing:

1. The packed graph creates an unmarked grouped matmul and uses the ordinary CUDA dispatcher. The loop4 path marks its node and then applies dedicated shape, stride, actual-buffer/device, warp and old-tile-MMVQ rejection checks. Sharing the backend source file does not transfer those predicates to the packed node.
2. Clean execution disables the placement observer. A reset `bad=false` followed by `need(!bad)` is not an independent clean placement observation. The original RTX name filter and the later reconstructed M2 MUL_MAT observer have different coverage.
3. Target-group exceptions poison `PhaseContext`; trim, draft and sample errors rely partly on CLI process termination. That is a valid termination boundary for the audited worker, but it is not a general recoverable service-object API contract.

The audit does not establish wrong arithmetic, a triggered bad fallback, or misplaced operators in the frozen measured deployment. Conversely, it does not certify every descriptor accepted by the packed branch. The suspected shape-only graph-reuse problem is not supported: actual reuse compares prefix and policy information as well as existing graph settings. The documentation should name those live predicates rather than an unused helper. The 22 proposed positive, negative and failure cases are all design-only `NOT_RUN`. [Source audit](../guard_audit/SOURCE_AUDIT.md), [qualification design](../guard_audit/PACKED_QUALIFICATION_DESIGN.json)

## 4. The architecture candidate is actionable but unimplemented

Independent source inspection confirms that, for each output-row tile, current packed groups occupy different CUDA blocks along grid.y. The current case-4 kernel has no explicit cross-group register reuse of weight fragments. Repeated reads of the same weight address do not establish a DRAM-traffic saving. The proposed first change is specifically to give one block two independent four-column groups while preserving each output's original K assignment and reduction order. [Architecture hypothesis](../guard_audit/ARCHITECTURE_HYPOTHESIS.md)

The warning against simply changing native column width to eight is justified: the generic NVIDIA table changes from four warps at width four to two at width eight. The proposed source-level accumulator count of 8 to 16 floats per thread and reduction-buffer size of 3,072 to 6,144 bytes are correct arithmetic, not measured registers, occupancy or latency. A three-arm comparison—backend-loop4, current packed, proposed within-block reuse—can separate the new hypothesis from the existing launch consolidation. It must use real captured operands and pass exact replay before timing. [Architecture review](architecture_review.json)

This is a kernel and scheduling hypothesis, not an already implemented new speculative-decoding method. Current k3 verification does not enter multi-group packing; any benefit must be located in measured prompt work or a separately qualified wider verification path. Successful operator evidence would still need original-reference full-request qualification and complete service timing against the strong baseline.

## Publication and remaining work

The review resolves the concrete source/citation/accounting issues found in this continuation. It does not reopen broad testing after the frozen CPU panel passed. The useful next production experiment is to bind the real consumer contract and original reference, collect admitted stage costs on the intended deployment, and evaluate the architecture candidate only after exact operator qualification. The same-panel phase decomposition, the stronger 32B service result, and general 5% evidence remain separate requirements.

The publication allowlist separates these review receipts from the retained build, log and raw evidence. Raw blobs, native binaries, build logs and working source snapshots remain in the retained evidence package rather than being represented as new public performance data. The pre-execution receipt describes its own earlier `NOT_RUN` state; the final raw-evidence receipt records the one subsequent completed CPU experiment.
