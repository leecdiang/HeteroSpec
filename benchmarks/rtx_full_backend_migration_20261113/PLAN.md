# RTX 5070 Ti: full-backend numerical-migration comparison
Status: EXECUTED on Windows. See windows_20261113/RESULT_REPORT_ZH.md and IMPLEMENTATION_PROTOCOL_ZH.md. The design/proposed-budget text below is preserved as the preregistration, not current authorization/status.
Date: 2026-11-13. Target: RTX 5070 Ti Laptop GPU, 12 GiB, one owned device.

## Question and contribution
How much complete-model inference time changes when the existing fixed-reference deployment is replaced by a pinned modern upstream backend, and what numerical/behavioral changes accompany it?
This is an engineering migration comparison, not a new fixed-reference speedup or a quality-equivalence claim. A faster result can strengthen the paper's discussion of the cost of retaining a reference; a tie or regression is equally publishable. No 5% success threshold and no tuning to obtain a positive result.

R = restored legacy **complete deployment** used for the paper's RTX fixed-reference path.
M = **complete upstream llama.cpp deployment**, initially commit `0fb8f157702702f33f4e018de8701b2569a1bc28` identified in #240.
R/M deliberately differ from historical extracted-operator B/U. Never infer full-backend speed from U/B=0.612924.

## Read these existing sources
- [#230 e08 real operand / C result](https://github.com/leecdiang/HeteroSpec/pull/230).
- [#237 e11 extracted U](https://github.com/leecdiang/HeteroSpec/blob/c8e5ea070ac393d7513903e0ec261dfce4554a49/benchmarks/rtx223_e11_u_contract_20261113/REPORT_ZH.md).
- [#240 full-backend boundary](https://github.com/leecdiang/HeteroSpec/blob/d240c5b43a763d5b02b5a53169b07f8e8af71a6c/benchmarks/rtx223_e12_backend_closure_20261113/API_AND_GATE_ZH.md).
- [Pinned modern sources / prior build](https://github.com/leecdiang/HeteroSpec/blob/d240c5b43a763d5b02b5a53169b07f8e8af71a6c/benchmarks/rtx223_e12_backend_closure_20261113/SOURCE_ARTIFACT_BINDING.json).
- [Paper review baseline](https://github.com/leecdiang/HeteroSpec/tree/c08b68b2c68a4b3a86f850eda368430fc8efeb3f/papers/jpdc/20261113_fixed_reference).

#240 established build/link feasibility, not runtime qualification. Its private quantizer buffers, private streams and old kernel-count gate need not be reconstructed to measure complete-model synchronized host time. The old 4096 physical-launch contract remains unsatisfied and unchanged. This is a **new proposed request/row/time budget**, requiring execution approval; it does not borrow an old allocation.

## Two panels, two meanings
### P: primary, equal-work full-model replay
16 roots × 4 paired blocks × R/M = 128 formal requests.
Use identical frozen prompt token IDs and a frozen 128-token continuation per root, forcing each continuation token in both arms. Obtain continuations from the already available public input/reference corpus where possible, or choose dataset continuation text before GPU execution. Do not generate them using whichever arm later looks fastest. Include the BOS/format choice in the frozen manifest.

Run a complete target model, not a first-layer prefix or extracted MUL_MAT. Each request resets its own sequence, prefills and evaluates exactly the common continuation, requesting the same output rows. No draft or acceptance logic. Primary end-to-end replay timer includes reset, host input delivery, decode calls, synchronization, common lightweight output handling and token bookkeeping. Full output dumping is outside clean timing. CPU forced-token selection is common. It is **not autonomous generated-response latency**.

Both arms use a common deployment envelope: identical Qwen3-8B Q8_0 GGUF, tokenizer and pre-rendered token IDs; single sequence; C1024; F16 K/V; non-Flash causal attention; max batch/ubatch32; fixed CPU thread count2; full GPU offload; all prompt/continuation positions fit within896. Keep M's upstream graph/PDL behavior unmodified within that envelope, record what actually activates. R retains its own fixed-reference numerical policy. Do not call this "all factory defaults" because deployment parameters are specified. Internal batching/splitting may differ and is part of the deployment comparison; record API-call/row counts. Do not force M to use R's internal kernel widths.

### G: secondary, autonomous greedy resident service
Same16 prompts × 2 paired blocks × R/M =64 formal requests.
Same tokenizer/rendering, sampler greedy, penalties disabled, cap128, same EOS/EOG definition. Each arm owns its own KV and emits its own tokens. Preserve EOS stopping; never suppress it just to equalize runtime. Report paired total response time, emitted-token count, stopping reason, time to first token and decode time/token separately. Do not interpret a short/different response as equal-work acceleration.

Report first divergent token, exact token agreement, response lengths and representative retained complete outputs. An independent task scorer can assess existing code/math labels only if available and valid, without another model or fabricated quality judgments. With16 prompts, no claim of equal task quality or universal semantics preservation. Fixed-work P is the primary performance result; G explains what migration means for actual generation.

## Inputs and selection before timing
16 task roots in four prompt-length bins (<=128,129–256,257–512,513–768 tokens),4 per bin. Within each bin use2 code +2 math where the existing public corpus supports this without truncating questions. Deterministic first eligible unused IDs from a pinned dataset/version, ordered by stable ID. Record prior project exposure; "new selection" does not guarantee unseen training data. If bins cannot be filled, resolve and freeze a different balanced panel before any timing; do not choose on observed speed. Do not pad with synthetic prose merely to fill a bin. Keep this new panel distinct from the old single captured operand and A5000 S3 roots.

## Implementation, deliberately small
Build two separate complete llama/model API workers against their respective source trees, with a thin common JSONL request/receipt adapter. Do not mix modern ggml DLLs into an old llama frontend or splice an extracted U kernel into R. Prefer existing complete frontend source and public model API over a new inference engine. Adapter needs reset, prefill, forced continuation, greedy generation, synchronization and output copying. Test JSONL parsing, stop accounting, schedule, missing replies and analysis on CPU mocks.

Freeze an execution manifest once containing the actual R source/binary identity, M pinned source, model identity, compiler flags, parameters and host power mode. R's exact complete runtime must be located from the existing local handover, not guessed from the e11 operator DLL. This design has not verified local files or VRAM. If R cannot be restored without substantive changes, stop and propose a new comparison; do not label a reconstruction as the historical deployment.

Do not build a new ETW/AppContainer/kernel interception framework. Use an ordinary owned process with a wall-time watchdog, result ledger and clean exit. A local permission/security-setting change still needs its own approval. Never kill unrelated GPU processes.

## Qualification: each arm against its own reference
No cross-arm bitwise requirement: R and M intentionally define different numerical contracts.
Before timing, two fixed diagnostic roots (short, near-boundary) per arm,4 requests each =16 requests total:
1. Fresh native deployment run through an independently exercised native driver/API sequence.
2. Fresh adapter run with the same tokens, scheduling and output requests.
3. Repeat fresh adapter run.
4. Reset/reuse adapter run then same fixed continuation.
Compare complete requested vectors and generated-token/stopping behavior for identical within-arm schedules; verify position/sequence accounting, finite values, no context truncation and correct cleanup. Use existing active-state export if available; lack of a public M KV serialization API does not justify inventing cross-version byte equivalence. If available, state comparisons are **within arm** and normalized for that arm.

These are integration, stability and continuation checks, not an independent all-input numerical proof. R additionally checks the available historical reference fixture under its actual recorded configuration. If its fixture cannot be reproduced, resolve before using the name "legacy fixed-reference". M is not required to pass the abandoned extracted-U CPU-RN oracle. Preserve its historic failure as a separate question.

A repeat discrepancy is investigated before timing. It may be real nondeterminism rather than an adapter bug. Do not silently loosen tolerance; either demonstrate a benign integration explanation or amend the protocol and claim before running P/G. Do not time a known broken adapter. No full-vocabulary dumps during formal timing.

## Session ordering and clocks
Use one model resident at a time (both do not fit12GiB reliably). P blocks ordered RM,MR,MR,RM; G blocks RM,MR. In each block run all16 roots per arm with one deterministic cyclic root order shared by the paired arm; rotate by4 roots per block. Same16 roots provide paired workload clusters. This balances arm order but does not eliminate thermal drift.
Each arm-session loads once, runs one frozen warmup request, then the16 formal requests; unloading lies outside resident time. Eight P + four G sessions =12 model loads and12 warmups. Record actual graph warmup/capture versus steady state rather than assuming them absent.
Record process total time separately including model load, initial context and warmup, with the same session request count. Do not compare worker time for unequal workloads.
Use monotonic host clock with backend completion synchronization around the whole request. No CUDA-event/extracted operator comparisons. Log coarse temperature, clocks/power and foreign GPU usage before/after sessions using existing tools if permitted; no privileged instrumentation required. Use AC power and unchanged declared laptop performance/fan settings. Do not silently change system settings. Interference/thermal errors are recorded with all samples; predeclare operational invalidation before looking at timing and report exclusion counts.

## Analysis and success/negative outcomes
Primary rho_P = exp(mean_root(mean_block(log(t_M/t_R)))) over the128 formal replay requests. Retain all valid planned pairs. Report all16 root estimates, length-bin descriptive estimates, geometric primary reduction100*(1-rho), and20,000-draw stratified paired-root bootstrap95% CI (resample roots within length bins, keep all blocks/arms). Blocks are repeated sessions, not64 independent tasks. Six blocks do not establish cross-day generality.
G has a separate equal-root log-ratio estimate using2 blocks; report it beside token counts and agreement, not as same-work acceleration. CIs are exploratory secondary and not a quality test. Report pooled times as a separately labelled estimand.
No optional stopping for significance, no outlier removal based on speed, no replacement of slower roots. Finish planned blocks or label incomplete with reasons; no added rounds after seeing a near-miss.
- M faster in P: complete-model equal-work migration opportunity under this envelope, not a compatible-reference win.
- M faster only in G with shorter/different answers: no evidence of equal-work speedup.
- M slower/tied: extracted operator gain did not translate here; no claim all modern backends are worse.
- M unstable/adapter qualification fails: integration/qualification result only, not performance comparison.
- R/M token divergence: expected possible consequence; measure rather than erase it.
No occupancy/DRAM causal explanation without actual profiling. No universal5% target.

## Proposed execution budget (not approved, not consumed)
- Formal requests: P128 + G64 =192.
- Diagnostic qualification:16; warmups12; failure/retry reserve8.
- Hard total request cap228; maximum896 processed token rows/request =>204,288 rows including failures/warmups. Decode rows, not emitted tokens, debit the row counter.
- Model load/context deployment cap18: qualification4 + timing12 + retry reserve2. Count failed loads; do not refund.
- Active execution window6 hours from first model load, with per-request10-minute abort and controlled stop between requests. These are stop bounds, not time estimates or a guarantee of driver-hang recovery. No automatic overnight resumption.
- New evidence output <=10GiB (excluding already existing model/build files). Save complete diagnostic vectors, all request timing/token receipts, selected state evidence and error logs; avoid TB-scale per-step KV export.
- GPU memory must fit the exact same full-offload model/profile in both arms. Probe the approved diagnostic request, not a separate open-ended model sweep. If either arm OOMs, stop this comparison; a common reduced-offload or smaller-model successor needs a declared new profile, not a silent fallback.
- Physical kernel launches and implicit contexts are NOT bounded by the old4096 contract. No claim of zero implicit GPU work during model/backend initialization.
The owner must approve this independent operation and its budget after host preflight and concrete runtime identities are supplied. This PR authorizes neither GPU execution nor security changes.

## Recovery without needless stoppages
Ordinary CPU build/path/JSON/schema bugs may be fixed and retested before approval; record concise change notes. During an approved run, a transient failure may consume the8-request/2-load reserve only after confirming the owned worker exited and identifying a non-scientific cause. Retry the complete affected pair, retain failed receipts, and never expand caps or alter model, numerical path, sampler, workload, timer or outcome-dependent exclusion. Driver reset, unknown active worker, repeat numeric discrepancy, unknown placement, or changed comparison contract needs a stop and decision. A harmless additional signed Windows system DLL is not itself a scientific failure; do not resurrect an exhaustive image-allowlist gate unless required by the actual approved execution environment.

## Deliverables
PLAN, frozen manifest and input IDs, build/adapter changes, CPU tests, within-arm qualification results, all P/G rows, analysis script with mock tests, compact per-root/phase figures, report interpreting negative as well as positive outcomes. Update this PR; keep #230/#237/#240, old ledgers and paper unchanged. No merge, release, arXiv or journal submission.

## Historical status at design head (superseded by execution closeout)
Design source review complete. Modern source fixed from public #240. Actual R restoration, M complete model build, adapter implementation, local resources, runtime qualification and all performance panels: NOT_RUN. No result or timing forecast is implied by this plan.


## Execution closeout
User approved this campaign in the execution chat. Both panels completed:192formal,220totalrequests,51370actualrows,18deployments,1085.38seconds model window. Qualifier uses6deployments(total18) for independent native+two fresh adapter processes/reset. Original long bin was unfillable; predeclared deterministic fallback froze26..161-token formal prompts before inference. P ratio .678474 is full-model equal-work execution cost;G .676136 is separately reported with different trajectories. Large cross-contract vector differences remain;no quality/reference equivalence claim. See the complete report,source,rawrecords and scope limits in windows_20261113/. No new GPU work is queued.
