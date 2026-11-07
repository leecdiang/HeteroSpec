# Prospective protocol: support the existing paper on B570

## Question and fixed scope

Primary hypothesis: a supported QH_C lowering of independent attention queries matches strong PQ under real model operands and preserves the registered ordinary reference in natural decoding. Secondary hypothesis: its full speculative request cost is lower than PQ after all layout/copy costs. Both are falsifiable; improving the paper means obtaining valid evidence, not guaranteeing acceleration.

Keep Llama-3.1-8B-Instruct Q6_K target, inherited Llama-3.2-1B Q4_K_M draft, exact original model/tokenizer/template bytes, F16 KV, non-flash, greedy, one sequence, ctx1024, cap128, inherited 10-thread host configuration, k1/q<=2. Verify actual identities from SOURCE_LOCK rather than names. No altered shader arithmetic, dtype, precision flags, sampler, reference tokens, donor-state restore, answer-dependent routing, AV-only method, k3/q4 actor, new model or hardware work. Numerical DLLs and driver remain pinned; new actor/graph-library builds get new truthful identities. Preserve third-party source notices.

QH_C is fixed before outputs. No performance/numerical selection between QH_C/QH_D/REPEAT4. If compact-mask QH_C cannot meet backend semantics, stop this protocol. PQ must be a legal supported strong baseline with shared KV and reasonable graph reuse. Original rejected QB4 is historical support evidence, not a timed straw comparator. True packing, mask alignment, transfers, graph construction/reuse and recovery costs are charged.

## Execution authority and freezes

The author-facing HOST_PROMPT authorizes the complete bounded program once sent to the host. It replaces per-stage manual approval for THIS NEW study only. The host must still recover fixed sources, review native changes, save complete prospective manifests and verify remote bytes BEFORE scientific starts. Do not ask for human approval at each successful internal gate. If the host cannot establish required facts or needs a scope/budget/reference change, stop and report the concrete blocker.

Separate scientific stages use immutable start ledgers; no restart of a started slot or terminal failed stage. A completed S3 session may be followed later by its originally unstarted next session after identity rechecks. Inactive scheduling gaps do not consume native lifetime; they do count against the four-day calendar ceiling. Persist WAITING_FOR_SESSION with earliest eligible time, not COMPLETE. Do not launch duplicate agents/controllers or background automations without separate instruction.

Each F0 binds the adopted design commit, complete source/compiler/executable/runtime/model hashes, real native request wire bytes, environmental identity, exact slots/order, monitors, independent auditor, output roots, budgets and stop rules. Bind generated wrappers and transitive imports too. A frozen hash alone does not certify semantic correctness. The host reviews the execution order and confirms monitored intervals match actual roles. CPU tests and design JSON are never GPU acceptance.

## S0: production-path engineering, no device activity

Within BUDGET limits and at most two integration revisions, restore the old source/runtime and the existing QH candidate; implement the narrow changes in NATIVE_HANDOFF and SUPERVISION. Use real GGML metadata/address checks and original CPU oracles where useful. Do not rerun the 432-fixture search or broaden shapes. Validate only the admitted k1/q<=2 domain and actual layouts to be used.

Required CPU evidence: actual compile/link; graph guards and output ordering; graph-cache phase/role/layout/capacity identity; pending-token/accept/correction/bonus/rollback/EOG/cap cases; active resource ownership; production-equivalent filesystem notifications; negative controls that reject source mutation, missing evidence, invalid placement labels and retry attempts. No native model/compute process, device initialization or readiness query in S0. Test doubles are clearly CPU children, never asserted to be GPU proof.

Gate: repaired production-path supervision demonstrated, native implementation compiled, reference-bridge contract recoverable, independent audit runnable, all plan/accounting checks pass, complete stage F0 authenticated. Otherwise close as ENGINEERING_BLOCKED. After scientific data begins, only byte-preserving delivery repair is allowed; a scientific implementation change ends this study and needs a new prospective amendment, not an automatic second attempt.

## S1: actual operands and finite numerical correspondence

S1a uses four old sentinels, each in one fresh model process: one counts warmup, one heavy capture and one counts observer control, with full independent resets and prompt-cache reuse disabled. All three are charged: 12 model requests /4 model processes. Use the naturally executing reference128 producer and k1 MQ consumer. Do not force a future token. The two counts endpoints and heavy endpoint must match each other; MQ need not match ordinary R for this diagnostic. Any capture-induced output difference blocks transfer of its operands.

Capture the FIRST naturally occurring q2 target VERIFY at target layers 0 and L-1. Fixed selection before outcomes: 4 tasks x2 layers =8 native contexts. Save exact Q/K/V/mask bytes, strides, roots, positions, parameters and actual MQ output stages before in-place consumers overwrite operands. MQ native/replay correspondence is mandatory. If a natural q2 context is absent (e.g. early EOG), record missing and stop; do not choose a later or alternate task.

For each native q2 context create a q1 control using its first query and matching mask column, preserving K/V and logical positions. These eight q1 contexts are derived controls, NOT eight more native snapshots or independent prompts. Freeze all 16 exact input/output-control descriptors and operand hashes before S1b. This two-step freeze is necessary: the capture selection rule is prospective, while future tensor bytes cannot be known at S0.

S1b: one charged native support-census host, zero graph computes; enumerate EVERY executable node of all MQ/PQ/QH_C graphs, including CONT/copy/concat/softmax. Record actual device alignment and node support. Views are metadata. All required graphs must be supported. One boolean fourth-axis condition is not sufficient.

Then 16 contexts x3 layouts x2 independent processes =96 standalone graph computes. q1 executes the original chain for every label. Verify actual backend execution/ownership of every executable node, input immutability, full four-stage vectors, finite values and repeats. No CPU fallback or synthetic CPU output supplies a GPU sample. Mathematical address/structured checks and FP64 errors are separate from bitwise relation to PQ. QH/PQ disagreement is a retained finite numerical result, not proof of a broken algorithm; it closes THIS conservative paper-support gate without output-dependent tuning. Native q2 MQ replay must reproduce its captured stages; derived q1 only needs common-path agreement, not equality with a q2 result slice.

Gate to S2: all required controls and placement valid, full planned panel completed, PQ/QH_C bitwise equal at QK/softmax/AV/final on all 16 contexts and both repeats. Report q1 separately. Timings here are diagnostic, not endpoint speedups.

## S2: natural decoding pilot

Producer is fixed to the inherited reference128 recipe (MQ prefill, original final-position logits policy). It is called reference128 as a recipe, not assumed identical state. Remove the old bulk512 factor: no new producer factorial. Reference R is the original executable/recipe, not a rebuilt replacement.

Six arms, four sentinels, two independent counts processes per cell: 48 requests/processes, no warmups. R and R_SHADOW controls run before candidates. Candidate order is frozen/counterbalanced by plan. Additional heavy diagnostic: four tasks x C_R_PQ/C_R_QH =8 fresh requests/processes. S2 total56. Pilot latency is descriptive only; it cannot select progression.

| Arm | Meaning |
|---|---|
| R | Original ordinary UB128 reference, original capacity/phase behavior |
| R_SHADOW | Rebuilt original reference semantics, capacity1, untransformed attention |
| M_R | Candidate actor, natural reference128 prefill, capacity4/continuation UB4, no draft; actual continuation q1 |
| C_R_MQ | Same candidate state/transaction with k1 and original attention |
| C_R_PQ | Same with supported per-query attention |
| C_R_QH | Same with fixed QH_C |

Target/draft ownership and draft's inherited schedule remain separate. Candidate prefill is MQ; local PQ/QH applies only where the inherited target continuation guard enables it. Do not casually copy CUDA mask3 to this actor. Preserve and test graph cache identity even with observation disabled.

Check complete registered endpoints: native IDs, EOG flags, length, terminal token and stop reason for the entire cap128 window. Compare to actual R, not expected text or argmax of saved reference logits. Diagnostics establish before/after phase binding does not alter state, and observe actual ordered multirow VERIFY (not just caller width histograms), q-dependent graph identity and backend placement. Compare recorded acceptance/rollback/commit work across PQ/QH without claiming complete trace identity from counters alone.

Control/monitor/identity/capture errors stop immediately. Valid candidate endpoint mismatch is a scientific outcome: finish the remaining already planned S2 arms safely so the complete matrix is retained, then stop progression. Do not patch while running or time a shorter divergent output as a qualified speedup.

Gate to S3: R repeats stable; R_SHADOW and M_R all match R; C_R_PQ/C_R_QH both match R on every counts and heavy endpoint; genuine multirow VERIFY, actual supported GPU placement and observer controls pass. C_R_MQ may diverge and is not a gate. No speed gate. If only target-wide serialization could repair the failure, report a local-method boundary and close rather than changing the method.

## S3: independent-input confirmation

Select 24 texts before candidate outcomes: MBPP/GSM8K x target-token bins64-127/128-255/256-512 x4. Use exact pinned tokenization/template and the deterministic selector. No truncation or padding to fill bins. Audit all accessible project exposure identities, including alternate IDs with the same prompt hash; bind the inventory and disclose its coverage. Call inputs project-unused relative to that inventory, not universally unseen. Missing stratum or unknown tokenization stops preparation. No replacement after a scientific attempt.

Freeze full prompts/token bytes and 24 references-to-run before first S3 start; no oracle-output screening. The panel uses 6 blocks of4 tasks: block = domain x token stratum. Arms R, M_R, C_R_PQ, C_R_QH. Three sessions, each with all6 blocks and4 arms. Each block-arm has one fresh native process, one registered same-panel warmup (the fixed first task of that block), then two complete measured passes over its4 tasks; reset before EVERY request. Thus72 processes x(1+8) =648 requests, 576 measured and72 warmups. All warmup endpoints are retained and qualified too.

Order rotates/reverses arms within short blocks and task order between passes, using study.py's deterministic schedule. It is balanced scheduling, not a claim of perfect four-arm position balance in three sessions. Keep counts instrumentation identical in qualified comparisons and prompt caching off. First measure includes any graph setup not paid by the registered warmup; no guessed overhead subtraction.

Session1 starts >=1h after session0 ends; session2 >=1h after session1 ends and >=24h after session0 starts. Freeze timer definitions and actual session timestamps. These are three sessions, not three independent dates. Restarting the host to begin an unstarted planned session requires source/model/runtime/environment checks and immutable completed-session receipts, not rerunning old slots.

Primary ratio is geometric mean T_PQ/T_QH with equal task/session weights, median of two measured repeats within task/session. Secondary M_R/C_R_QH measures draft value; R/C_R_QH is whole-recipe comparison. Paid timer includes reset, natural prefill, drafting, verify, reconciliation, output recovery, required completion and endpoint return consistently across original and new actors. Include all mandatory packing/copies; loading is separate. Bind actual timer boundary differences; if harmonization cannot be established, withhold cross-actor cost claims.

Complete-reference qualification precedes speed claims. Keep failures, task regressions, domain/length strata, sessions, missing data and cumulative costs. Any required non-R arm mismatch withholds that arm's whole-panel qualified speedup; no successful-subset aggregate. R instability invalidates reference-based comparisons. No significance-dependent stopping, outcome selection, request-level bootstrap, or narrow population CI from3 sessions. See ANALYSIS.md for thresholds and conclusion rules.

## Readiness, ceilings and closeout

Before the capture stage, replay stage, pilot and each confirmation session (six windows), an OPTIONAL metadata-only device-readiness check may wait up to120s with at most5 queries30s apart, maximum30 queries total. Choose/query fields and thresholds prospectively from supported APIs in F0, not after failure. Queries have no model/graph work and are charged. No extra query inside a scientific slot or post-failure retry. Source identity checks and owned-process inventory are mandatory. If the window expires, end that stage, preserving all unstarted work.

Every native start reserves its entire per-attempt timeout plus cleanup against remaining stage wall/native budgets. Monitors and audits are charged separately, including overlap; never multiply wall by an arbitrary constant and call it measured lifetime. Control-child starts/lifetimes use actual PID/create/exit accounting; compiler/Git/OS delivery work has a declared separate scope. Supervise one compute child at a time. Reserve output and archive space before capture. Do not let archive growth consume scientific budget invisibly or erase old history to make room.

Close with RESULT.md, every planned slot/status, stage/context/task/session tables, full raw manifests and restorable archives, original/fresh independent audit comparisons, resource/missingness records, and PAPER_EVIDENCE.md. Recompute from an actually downloaded fresh archive with the unchanged independent analyzer. If transport fails, immutable-byte retransmission within delivery budget is allowed; no scientific rerun. Preserve raw before summaries. Keep PR Draft; no manuscript, main, release, arXiv, Zenodo or automation changes.
