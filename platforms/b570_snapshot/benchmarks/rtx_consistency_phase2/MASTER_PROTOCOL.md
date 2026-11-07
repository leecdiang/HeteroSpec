# RTX consistency contracts, Phase 2: frozen master protocol

Version 1. Evidence basis: manuscript v0.10/main e87291d and PR #59/head b0dfa0f. This is a private HeteroSpec study, with no submission to upstream llama.cpp. The completed Phase 1 artifacts and binaries remain immutable. All source/configuration changes must be committed before the relevant inference; failed and incomplete attempts are retained, without automatic inference retries. Raw telemetry, states, weights and runtimes stay outside GitHub.

## What is closed, and what remains open

Phase 1 closed a finite evidence chain on this numerical stack: reproduce the original native intervention; cross actual state/current call at four natural checkpoints; construct a local attention candidate; qualify its complete outputs; measure incremental speculation against the same constrained prefill. On 19 exposed tasks/four repetitions, the primary candidate matched 76/76 original ID/EOG-cap128 arrays and achieved task-median geometric-mean ratios 1.2564486597042208 for generation and 1.0774505180761593 for full requests. Earlier k2 negative results and the ordinary-k3 failures remain evidence. This is not universal losslessness, a minimum constraint, an operator-root-cause proof, or a production/cross-platform conclusion.

Phase 2 asks a connected question: which parts of the existing constraint are necessary, when do they remain sufficient, and how much efficiency does relaxing unnecessary parts recover? It does not search generic draft models or replace the original scalar reference with a new convenient output.

## Invariants and four questions

Keep Qwen3-8B/0.6B Q8_0, released b10839 CUDA DLLs, RTX 5070 Ti Laptop, FA off, ctx4096, one request/slot, threads24, greedy seed123, original chat wrapper and inclusive EOG. Stage A keeps k3/globalUB4/cap128. Complete original reference IDs/endpoints are immutable. No reference answer, proposal tape, divergence position, task-specific router, extra reference pass or repaired prefix is passed to the candidate.

1. **Necessary scope:** must the constraint cover target and draft, prefill and continuation, or only a subset?
2. **Prospective transfer:** does the frozen recipe pass tasks unused by our previous experiments?
3. **Boundary:** what happens when output length, cache geometry and verification width increase?
4. **Persistent execution:** are phase transitions, graph reuse and repeated uncached requests stable?

Stages depend on one another. A failed output gate cannot be redeemed by a faster timer. A recipe failure is retained and need not terminate unrelated planned recipes; a reference/instrumentation/build-bridge failure stops dependent interpretation. Unexpected failures get at most a separately frozen diagnostic extension, never an unreported repair or a restarted run with discarded outcomes.

## Stage 0: infrastructure bridge before ablation

Use a new private source/build directory copied from Phase 1, with the released backend unchanged. A process-fixed mask selects four scope flags: bit1 target-prefill (TP), bit2 target-continuation (TC), bit4 draft-prefill (DP), bit8 draft-continuation (DC). All 16 masks are predeclared. The model role comes from actual target/draft decode call sites, not model size or task ID. Each new request resets phase to prefill; the original first-pending handoff marks continuation after prompt processing for both models.

The constraint is a graph-topology choice. Its value must be snapshotted in graph parameters AND checked in graph-reuse eligibility. Reading only a mutable flag in the graph builder can silently reuse the wrong topology across phases. Capture-enabled diagnostic traces must verify actual query-batch nodes for multi-token micrographs in the selected role/phase. Scalar query calls are mathematically unchanged and are not counted as evidence that a multi-query lowering occurred. Cost capture is disabled and skips metadata/synchronization, as in the primary Phase 1 panel.

Engineering budget: 8 complete CLI trajectories (old Phase 1 and new all-on mask15 on /15,/25,/18,/31), plus 8 resident capture-enabled requests (/31 twice each with masks3,12,5,10) and4 excluded warmups. Masks3/12 distinguish model role; masks5/10 distinguish phase. Old/new all-on outputs must equal original R. Selective traces need not equal R; they must prove correct scope application, request-phase reset, and repeat-stable arrays/endpoints. Role/phase coverage must include multi-token graphs or explicitly report unsupported coverage. Any bridge failure stops Stage A. The expanded coverage was frozen during implementation review, before any Phase 2 model execution.

## Stage A1: complete scope factorial on the original diagnostic cases

16 masks x4 exposed cases (/15,/25,/18,/31) x2 repetitions =128 measured resident qualification requests, plus32 excluded warmups (one per process-fixed recipe session). Fresh service per recipe; reverse recipe order in repetition2 and rotate task order. These timings are diagnostic only, not formal speed claims. All masks, including ordinary mask0 and all-on mask15, are retained. Two all-on repeats on every case must reproduce R, or stop dependent stages. Score full arrays/EOG-cap128 and record draft/accepted counts; do not select by acceptance or speed.

Construct the observed passing set without assuming monotonicity: adding a constraint may change draft proposals or state construction. Compute all inclusion-minimal masks within this finite four-case/two-repeat passing set. This is not proof of global minimality or unique attention causation.

## Stage A2: full original 19-task gate

Freeze the A1 passing frontier before seeing the other 15 tasks in this new experiment. Test all-on mask15 and at most4 inclusion-minimal masks, ordered by (number of enabled flags, integer mask). If the frontier has more than4 masks, the remaining masks are recorded as not tested, not implicitly rejected. Add target-only controls for every distinct target scope (mask &3). All original 19 tasks are already exposed; this is an expanded qualification gate, not a holdout.

Two repetitions for each condition, full reference comparison; at most9 conditions x19 x2 =342 requests plus18 warmups. Target controls that drift from R block the corresponding incremental-speculation cost claim, even if the speculative candidate happens to match. All-on and its target must qualify. Select the cost challenger among full-cohort-qualified frontier masks by the same (flag count, integer mask) order, never by observed timing. If none qualifies, retain all-on as the existing result and do not search more recipes.

## Stage A3: output-qualified incremental cost

Compare the selected challenger, all-on speculation, and their same-target-scope target-only controls. With common target scope there are3 conditions; otherwise4. Use twice the number of conditions as fresh-process repetitions:6 or8, with two complete cyclic condition-order blocks.19 tasks, rotated order;342 or608 measured requests, plus18 or32 excluded warmups. Capture/state export/forks are off. Log GPU metadata before/after sessions, outside request timers. No concurrent GPU jobs.

Primary question: challenger vs all-on generation time, with complete output equivalence. Secondary: each speculative mode vs its own matched target-only generation and whole-request time. Use per-task repetition medians, geometric mean of ratios, every task and every repetition, plus fixed-seed task-resampling intervals labeled descriptive for this exposed cohort. Task resampling does not establish population representativeness. Also report paired per-repetition ratios to expose order/thermal sensitivity.

A practical efficiency advance requires no output mismatch, generation geometric-mean ratio challenger/all-on at least1.03, whole-request ratio at least1.00, and a consistent direction in at least4/6 or6/8 repetition summaries. Otherwise record a scope-sufficiency result or a speed-negative result; no new acceleration claim. A reduced-scope recipe may be informative even if not faster. The original all-on result is not erased.

## Stage B: locked unused-task evaluation

Only after A freezes a candidate or confirms all-on, audit all available historical run/manifests and previous paper/platform experiments. Distinguish downloaded corpus prompts (available only) from executed/inspected outputs and unknown exposure. Exclude executed/inspected and unknown tasks. HumanEval0..7 from the old pilot cannot be silently treated as unused. Missing history is not proof of non-exposure.

If at least24 eligible HumanEval and24 eligible MBPP tasks exist, select24 of each by SHA256(task ID + fixed seed `HeteroSpec-RTX-Phase2-B-v1`) and publish the manifest/dataset hashes BEFORE generating references or candidates. Otherwise reduce the declared panel with an explicit amendment before any new outputs, or mark unused-task evaluation unsupported. Do not invent clean task provenance.

Freeze recipe/code and run four repetitions of scalar reference, matched target-only, and speculation: up to48 tasks x3 conditions x4 =576 complete requests plus12 warmups. Generate references as paid runs; offline references cannot guide recipe changes. Any candidate mismatch fails the full-panel equivalence claim, with all timing retained as diagnostic. Do not tune on B and call a retest the same holdout. Functionality/pass@1 is a separate evaluation requiring a separately frozen code extraction/testing contract; ID agreement is not functional correctness.

## Stage C: length/width/cache boundary

After B qualification, select8 B tasks by the same hash order before outcomes. Predeclare caps128/256/512 and (draft k,global UB) pairs(1,2),(3,4),(5,6),(7,8). The original k3/UB4 remains the anchor. A wider Qwen3/FA-off graph guard needs its own bridge; projections/FFN may change their numerical path beyond width4, so attention alone must not be assumed sufficient.

With three modes (scalar reference, matched target, speculative), two repetitions, at most8 x3 caps x4 widths x3 modes x2 =576 complete requests plus24 warmups if sessions group caps/tasks by mode/width/repetition. Report capped outputs and actual EOG separately; cap512 does not imply every task reached EOG. Keep mismatches and all widths. No result-selected best-k headline. A failing width receives no qualified speedup; do not automatically add global serialization/repair and relabel it the same recipe.

If a boundary fails, freeze a diagnostic extension on at most2 deterministically selected failing task/configuration pairs: earliest predeclared width/cap, then task hash order. Reuse paid real-state crossing where native prefixes naturally align; otherwise report unsupported alignment. Operator operand/logical KV probes are paid diagnostics, not online predictors. Source-level eligible CUDA dispatch is not proof of actual kernel dispatch; unavailable tracing capability is reported honestly. This extension tests why the existing constraint boundary failed, not a new generic acceleration project.

## Stage D: persistent execution and implementation delivery

Only for a B/C-qualified fixed recipe, run two predeclared shuffled cycles of24 B tasks for matched target and speculation (96 requests plus4 warmups), uncached, in the same resident service per mode/cycle. Score complete references and record phase resets, failures and duration trends; resource observations remain outside timed requests. Compare request-order permutations. Multi-slot/throughput testing is a new numerical contract: the current one-KV-stream view/broadcast guard does not support it, and must not be bypassed for benchmarking.

Deliver per-stage frozen manifests, complete-output and cost summaries, every negative result, source/binary/model/runtime hashes, an exposure ledger, and a content-addressed local raw archive. Add results under a separate Phase 2 directory/PR; no manuscript edits until conclusions are mature. Report exactly which stages ran and which remain planned. No claim of venue acceptance, first/unique novelty, universal losslessness, or transfer beyond measured contracts.

## This execution tranche

Start with Stage0 and A1 after this plan and the implementation are frozen. Continue A2/A3 only when their explicit gates qualify, with a separate selection manifest committed before execution. B/C/D are designed here to coordinate later expansion; they require exposure/configuration manifests that are not yet prepared and must not start speculatively. This separation prevents large ungated sweeps and preserves the interpretation of the current paper.
