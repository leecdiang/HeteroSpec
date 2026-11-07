# Paper evidence handoff: ordinary scalar-reference gap closed

Status: **READY_FOR_BOUNDED_MANUSCRIPT_RECONSTRUCTION**. This means the specific PR62 B strong-baseline gap is closed with authenticated raw CPU analysis and the late-study evidence can enter a separate manuscript reconstruction. It does not mean the whole manuscript has been integrated, compiled, externally reviewed or accepted. Preserve explicit evidence limits.

## Same-panel cost result

|Baseline / candidate|Timer|Task-median GM|Descriptive95% interval|Faster/slower tasks|Round GM1/2/3/4|
|---|---|---:|---|---|---|
|scalar_reference / target_scopes|generation|1.170124448|[1.117013, 1.217681]|22/2|1.168805/1.173517/1.158128/1.173160|
|matched_target / target_scopes|generation|1.169237971|[1.117115, 1.217153]|22/2|1.169667/1.048849/1.175118/1.176428|
|scalar_reference / matched_target|generation|1.000758167|[0.995290, 1.007752]|11/13|0.999263/1.118862/0.985542/0.997222|
|scalar_reference / target_scopes|whole|1.741569262|[1.654608, 1.827079]|24/0|1.726493/1.736437/1.726798/1.736735|
|matched_target / target_scopes|whole|1.035071366|[1.004552, 1.063481]|17/7|1.028699/0.940220/1.051749/1.044236|
|scalar_reference / matched_target|whole|1.682559598|[1.589801, 1.766329]|24/0|1.678326/1.846841/1.641835/1.663163|

Speed is baseline_ms/candidate_ms; >1 means candidate faster.24 task clusters, four paid repeats per path; distinct balanced resident processes within the same campaign, not simultaneous same-process measurements. See RAW_COSTS, TASK_COST_PAIRS and ROUND_COST_PAIRS for all absolute costs and reversals. The 10000-draw seed20261008 linear-quantile intervals are descriptive; historical4000-draw seed20261005 intervals are separately reproduced, not replaced.

## English result paragraph

On an NVIDIA RTX 5070 Ti Laptop GPU with the frozen Qwen3-8B/0.6B Q8_0 CUDA configuration (greedy seed123, FA off, context4096, k3/UB4, cap128), the target-prefill-and-continuation attention constraint matched the complete saved scalar-reference response arrays and endpoints on all24 MBPP tasks in four repetitions. A post-hoc CPU reconstruction of the same384 measured requests, excluding16 warmups, found task-median geometric-mean speed ratios of 1.17012 for the original server generation timer and 1.74157 for resident whole-request latency against the measured ordinary UB1 scalar reference. Descriptive task-bootstrap95% intervals were [1.11701, 1.21768] and [1.65461, 1.82708], respectively; all four round geometric means were above one. Against the constrained draft-free matched target, the corresponding ratios were 1.16924 and 1.03507, with a whole-request reversal in round2 (0.94022). The draft-free constrained target itself achieved R/matched ratios of1.00076 generation and1.68256 whole request. Consequently, the larger scalar-baseline request improvement combines numerical-path/prefill differences with speculation and cannot be attributed entirely to speculative verification. The panel is now exposed; reference lengths were11–128 tokens, and the result is neither a population guarantee nor a comparison against every ordinary decoder. No new model execution was performed.

## What can be written

- Full saved response-array/endpoint qualification of allfour paths:96/96 requests per condition; stable reference24/24 tasks. No new recropping, functional-code claim or fuller unrecorded-stream certification.
- This measured constrained speculative path beats the measured ordinary UB1 reference on the frozen B panel in both timers, with allfour round directions positive.22/24 generation and24/24 whole-task median ratios are above1; the two generation slow tasks are retained.
- Matched-target speculative gain remains1.16924/1.03507. Generation is positive in allrounds; whole-request round2 is0.94022. Do not write every round/task gained against matched target.
- R/matched whole1.68256, generation1.00076 (descriptive interval straddles1). This prevents attributing the full1.74157 whole gain to speculation and prevents a unique component-cost explanation.
- RTX local qualification/scope ablation and C4's wider-k negative efficiency, and B570's scoped repair without ordinary-reference gain, remain evidence in their own contracts.

## What must be narrowed or excluded

The scalar comparison is appended post-hoc to already exposed records, not a new measurement or holdout. Ordinary R is the measured private qualified frontend with mask0/UB1/no draft, not globally optimal ordinary decode. Generation excludes first-sample/prompt time and some final bookkeeping; whole request excludes model load, warmup and shutdown. Single-client resident latency is not concurrency/throughput/energy. No universal losslessness, automatic constraint discovery, global minimal scope, unique kernel root cause, certified error bound, cross-model validity or calibrated publication probability follows.

## Claim mapping and manuscript order

CLAIM_EVIDENCE_MATRIX.csv binds exact commits, raw/derived scope, baselines, exposure and limits. Recommended order: problem and output contract → natural historical-state/current-path crosses → RTX local attention transformation and role/phase ablation → qualified cost against both ordinary R and matched target → width/history-state counterexamples → finite B570 transfer → M4/358H source-specific applicability boundaries. Put much of the early research history in the appendix.

The working empirical main line is: **historical numerical state and the current execution path jointly influence reference outputs; local numerical constraints alter the useful verification-parallelism space, whose value requires both output qualification and actual paid cost.** These are finite system findings, not a proven universal speculative algorithm. General acceleration from speculative decoding was already known; the new evidence concerns a qualified concrete constraint instance, natural-state diagnosis and measured operating boundaries.

## B570 and cross-platform scope

PR65 head8783cb1… is read at its frozen public source, not newly raw-audited here. Preserve its endpoint contract/raw-suffix distinction and strong-baseline negative result: R/candidate generation0.2825875535, whole0.2012895932 on15 complete paired tasks. E stays119/120 and PARTIAL_INFRASTRUCTURE_BUDGET_CLOSED, with the missing old-N1 slot not imputed; B570_GPU_NEXT_ACTION=STOP. CPU audit completion does not make its original E matrix COMPLETE. This RTX handoff closes the deferred RTX raw-cost item without editing PR65.

CUDA/Vulkan provide finite transfer of the diagnostic design, not the same repair implementation/parameters/reference. The late mechanism evidence still concentrates in one Qwen3 model family. M4/358H retain their original source-specific contracts/timers/qualification; no comparable late state-cross evidence is asserted merely because costs exist.

## C4 evidence boundaries

PR62 C4 diagnostics include warmup in calls/micrographs; drafted/accepted and timing belong to a separate formal session. Keep305→199 caller calls and305→397 micrograph observations in the diagnostic scope, and3528→5392 drafted/2772→3192 accepted with0.829442 generation/0.889868 whole k7-vs-k3 in the formal scope. No cross-session divisions or attribution of all latency to a single counter are valid.

## Next authorized boundary

Next stage is evidence integration, manuscript reconstruction, compilation and reviewer-oriented audit. This CPU task does not perform that rewrite and does not request another equivalent closeout or new GPU campaign. PR61 v0.11 at4f343596… remains a baseline missing the late evidence.
