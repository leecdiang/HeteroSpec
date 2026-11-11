# Complete staged experiment — no automatic continuation of a closed study

## 0. Questions, endpoints and common invariants

Primary questions: (1) does query/head lowering express the original attention, (2) can the frozen backend actually execute it without a hidden backend change, (3) does it preserve the given complete-decoder reference, and (4) is it useful against strong PQ after charging packing and state formation? Success at one level is not success at the next.

No old result/F0 is rewritten. PR109 remains 49 starts/48 complete/1 interrupted/31 unstarted, 8110 callers, monitoring violation and14 endpoint counterexamples. PR111 remains a closed CPU/source investigation with no new model execution. This new experiment has its own plan, branch, outputs, runtime manifests and attempt ledger.

Preserve target Llama-3.1-8B Q6_K, draft Llama-3.2-1B Q4_K_M, exact old GGUF/tokenizer/template bytes, F16 KV, native greedy, cap128, FA off, one request/stream, ctx1024. Exact source references must be recovered, not inferred from filenames. New graph code means new actor/graph-library hashes; record that honestly. Keep numerical backend DLLs byte-identical. Shader arithmetic/precision changes, new models or modified speculative rules are outside this study.

Candidate natural decoding stays k1/q<=2. q3/4 are bounded operator/CPU tests, NOT authority to change the inherited native transaction. No sampler tuning, head/layer/token search, donor restoration, teacher forcing, lost-output retries or live-KV reference switching.

## 1. S0 — bounded CPU realization, one working day

### Deliverables

Read fixed PR111 source bindings, old native attention builder and actual GGML API. Build `native/query_head.h` against the real recovered source; use only ggml-base/cpu for this stage. The local descriptor mock is not the real backend. Adapt the old independent integer-address/FP64 harness to expose actual QK/softmax/AV and output for six layouts: MQ, PQ, QB4, QH_C, QH_D, REPEAT4. Q1 delegates to the original actual chain.

Reuse trusted tooling instead of creating another large archive framework. The implementation supports compact/model-permuted Q only; explicit legal source offsets and actual buffer bounds are checked independently. Mask heads follow r modulo q. Dense mask/repeated KV controls must be true graph operations and their temporary allocations recorded. Do not CPU precompute the final answer and insert it as an operator result.

### Frozen numerical matrix

`plan.cpu_cells()` defines **72 geometries ×3 masks ×2 data patterns =432 fixtures**:

- d=dv=128; q1/2/3/4; key extents63/128/257;
- query/KV heads(4,4),(8,1),(16,4);
- compact and model-permuted Q, legal32-byte base offset;
- causal, single-valid-key and hole masks; structured and dyadic patterns.

216 q1/2 fixtures are development;216 q3/4 fixtures are evaluated after the implementation/rules lock, without changing arithmetic source or harness. This is a held-out *fixture-output* phase, not previously unknown geometry: this package already has small scalar and descriptor tests at q3/4. Do not call it unseen natural-input generalization. The generator algorithm and seed are fixed before results. A change after seeing held results creates a new version, not a requalified old holdout.

Each fixture uses six layout computations: ceiling2592 actual CPU graph computes. Local toy fsum checks are separately labeled and not added to this host numerical count. Structured addresses and exact one-hot/single-key expectations are strict; general FP64 abs/relative/ULP errors and all nonfinite outputs are retained without posthoc tolerance. Same-input PQ/QH bitwise relation is a separate observation. CPU math.fsum is not a model of actual Vulkan reductions.

### Exit

Within at most one working day /14,400 CPU-child seconds, 8GiB RSS/job, one heavy job, 2GiB output: deliver an actual compiled candidate or stop. At most two evidence-scoped integration revisions; build failures remain recorded. No expansion into shader repair, ABI archaeology or repeatedly tuned shape exceptions. New code should solve a class of layouts, not four task IDs. S0 may gather source-level support conditions but initializes no device.

## 2. S1 — same-input operator feasibility

Requires prospective exact execution F0 and author approval. The F0 binds graph code, real harness, compiler/source, numerical DLLs, driver/device identity, generated inputs, controls, all slot ordering, monitoring and the independent raw auditor. No native approval is inferred from this document or Python booleans.

### Budget and input

**At most161 owned operator-host process attempts:** first one capability-only device-support census, then160 planned graph attempts. No model process/request, warmup or retry. The capability-only start initializes the requested backend and asks the full supports_op predicate, but performs zero numerical graph computations. It is explicitly charged, not called a free probe. Ceiling3600 cumulative owned seconds and2GiB output.

16 generated fixed-operand contexts: q1/2/3/4 ×n63/257 ×heads(8,8)/(8,2); d=dv128; model-permuted Q; causal masks; fixed dyadic data. These are synthetic operator inputs, not native model snapshots. Each is planned for MQ/PQ/QH_C/QH_D/REPEAT4 with two independent process repeats:160. Original QB4 is a source/CPU rejection control; it is not executed as supported GPU work. Fewer actual starts if a gate closes; preserve all unstarted slots.

### Capability decision before any numerical output

Enumerate every executable graph node, including pack/repeat/contiguous/softmax work, against the real frozen backend. Views/reshapes are metadata and are distinguished from executable operations. Save original API results and descriptors; one source batch-equality check is not the full predicate. Freeze the census and deterministic choice:

1. QH_C if all16 input descriptors' full graphs are supported;
2. otherwise QH_D if all16 are supported;
3. otherwise STOP_NO_SUPPORTED_CANDIDATE.

MQ/PQ must also be supported. REPEAT4 failure remains a rejected baseline, not a reason to fabricate an implementation. Unsupported nonprimary arms are SKIPPED_UNSUPPORTED; no CPU fallback is timed as GPU. Selection uses no outputs, error metrics, times or favorable task labels. One version/graph fingerprint binds the selected candidate for S2/S3.

### Actual numerical execution and placement

Use direct backend graph execution or a source-audited scheduler. For each admitted attempt, verify placement of every executable node and source/output ownership. Capture actual backend handles and copies where available. A complete model endpoint or weight placement alone cannot prove attention placement. If actual placement cannot be established, mark numerical comparison NOT_ADMITTED and do not call it a Vulkan result.

Before/after every compute verify identical input bytes, metadata, mask, state ownership and output recovery. Record QK, softmax, AV and full final vectors, q1 original-path control, repeat identity, complete nonfinite cases and bitwise/finite abs/ULP metrics. Four structured fault controls stay CPU-only; do not intentionally run unsafe GPU descriptors.

The same input can have a valid PQ/QH numerical mismatch. It falsifies a bitwise claim for that context, not automatically a whole-decoder endpoint hypothesis. Thus S2 may be proposed after valid finite/repeatable computations and placement even if some PQ/QH pairs differ, but the mismatch must stay explicit; no domain trimming or tolerance retuning. q1/common-path disagreement, invalid structured semantics, nonfinite result or unresolved placement blocks progression.

Timing is descriptive full operator-chain wall time with necessary packing/repeats/readiness included. It is not the paid request interval and cannot yield end-to-end speedup. No profiler or implicit replay. Allocator high-water and explicitly observed copy operations may be reported; no invented DRAM/utilization.

## 3. S2 — natural request bridge and sentinel pilot

Separate F0/author approval. No operator budget is transferred. **64 fresh model processes/requests**,7200 owned seconds,4GiB output; no warmup/retry/probe. Original reference is actually run, not a newly built shadow replacing it.

| Phase order | Cells | Starts |
|---|---|---:|
| Original R counts |4 sentinel inputs ×2 independent processes|8|
| New R_SHADOW |4 ×counts/diagnostic|8|
| Six candidate arms |4 ×6 ×counts/diagnostic|48|

Four sentinel IDs remain /1248,/831,/1011,/1249 and are all exposed. Candidate arms: M_R,M_B,C_R_PQ,C_B_PQ,C_R_QH,C_B_QH. R/B denote reference128/bulk512 producer recipes from natural prompt execution; all candidate prefill uses MQ, candidate output capacity4 and continuation UB4. The QH arm uses the support-selected variant from S1, not a post-output winner. Draft has its independent inherited reference-prefill recipe/UB1; no copying target schedules.

Reference128 names a planned producer recipe, not proof of reference-identical state. State formation and consumer lowering are distinct factors; if actual runtime cannot isolate them, report whole-recipe comparison rather than a causal factorial. Graph-cache identity includes role/phase/q/layout/mask variant/output capacity. All pending/bonus/reconciliation semantics are inherited from the audited k1 transaction, not re-created casually.

### Monitoring correction learned from the old NO-GO

Declare actual per-role contracts: old-R internal data are checkpoints, new actor may be periodic, with nominal periods and tolerated real gaps separate. One identically configured external owned-PID safety observer may be used for both; bind its available measurements and costs. Do not assert that external sampled data prove continuous GPU residency. Audit monitoring semantics after the first old-R return and **before any candidate**, not after a full campaign. Hash correctness alone does not certify cadence. Never rewrite the old F0.

Control/identity/monitoring/observer errors stop; valid candidate endpoint mismatch is a retained scientific result and safe remaining planned arms continue. Candidate counts/diagnostic equality is necessary for observer qualification. R repeats and R_SHADOW must match the complete original endpoint (IDs, EOG, length, terminal and cap/stop). No shorter divergent completion counts as faster.

S2→S3 requires complete valid controls, C_R_PQ and C_R_QH full matching endpoints on all four, actual phase-bound multirow VERIFY evidence, and actual backend execution for the selected layout. Do not substitute overall histograms. Do not select by pilot speed. Bulk-producer failures remain informative and do not invalidate a correctly qualified reference-producer candidate. If this gate fails, close the new pilot; no third round of token/head tuning.

## 4. S3 — frozen unseen natural-input evaluation

Separate author GO/F0; this is the stage that tests empirical transfer beyond the four old inputs. Keep current B570 target/model family and k1; do not purchase hardware or change precision to populate a success table.

Use24 previously unexecuted natural texts:code/math ×actual target-token bins64–127/128–255/256–512 ×4. Exclude all exposed IDs and prompt hashes across project branches, using a reviewed inventory. `select_panel` uses only source-bound IDs/tokens/metadata and fixed hashing. No answer/logit/latency selection, no padding/truncation. If a stratum is unfilled or exposure is incomplete, stop preparation; a changed selection needs a prospective amendment, not a convenient replacement after failure.

Seven arms: R, M_R, M_B, C_R_PQ, C_B_PQ, C_R_QH, C_B_QH. Three separated sessions: s1 starts at least1h after s0 completes; s2 starts at least24h after s0 starts and after s1 completes. It is three sessions across at least two date blocks, not three independent dates. Counterbalanced arm order comes from the fixed planner.

24×7×3=504 measured requests. Each owns a fresh process with exactly one charged same-prompt warmup followed by measured request, each independently reset with prompt caching off. Thus **1008 requests /504 processes**, ceiling21,600 owned seconds/6GiB. Failed loads count as process attempts; an unstarted model request is not invented. All new stages together cap at1072 model requests and161 operator-host attempts; actual forward/dispatch counts stay separately observed.

Original R is run for every input/session, and must be stable across repeats. Endpoints and full panel come first. The paid window includes request reset, natural prefill, draft, verification, reconciliation and necessary completion synchronization; model load separately stated. Q pack, expanded mask, repeat, state formation and reusable graph setup used during requests are not subtracted. Report one-time/calibration cost separately. Use identical host timing semantics, and retain actor differences rather than subtracting guessed instrumentation overhead.

### Analysis and claims

Primary direct contrast C_R_PQ/C_R_QH; secondary R/C_R_QH, matched M_R/C_R_QH, bulk analogues and producer effect. Retain all task/session returns, regressions, missing and unqualified arms. No aggregate qualified speedup over only successful tasks. Report per-session equal-task log ratios, complete-panel total request costs, code/math ×length strata and all invalidities. Three sessions do not support a narrow population/date-cluster interval; no request bootstrap. `evidence.summarize` supplies normalized-record arithmetic; the host must add independent raw reconstruction; the supplied calculation retains all six strata, not treat its schema as a native audit.

Any routing/coverage analysis must be prospective. Current candidate choice is a fixed backend-support decision, not a learned risk predictor. Full data are not used to select a faster method per task. Never say rejection-all is universal safety or claim new-architecture reference equals original B570/RTX.

## 5. Information-gain stop rules and publication boundary

This study should improve a class of representations, or stop. Keep strong PQ; do not defeat an unsupported QB straw baseline. If a candidate passes but is consistently more expensive or only works on old/very narrow conditions, publish bounded engineering/negative evidence rather than another full experimental expansion. An unsupported comparator is not zero performance. Positive synthetic semantics do not supply model generality; one B570 model plus old RTX families is not a controlled multi-backend replica of the new lowering.

No arXiv/manuscript/release modifications during execution and no merge. Current arXiv waits only for its existing RTX evidence, not this new program. Hardware analysis receives real mapping/copy/resource requirements; it neither waits on all stages nor obtains a fabricated hardware speedup from the prototype. Zero new automations.
