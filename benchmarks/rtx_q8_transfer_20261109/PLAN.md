# RTX true-q8 transfer and width-economics protocol

Status: DESIGN ONLY / NOT RUN. A new Windows RTX experiment, not a new performance result. Changes in this PR are additive protocol documents only. No old baseline, source, result, manuscript or device setting is changed.

## 1. Question and frozen evidence

Does the wider verification path have the same cost/benefit on RTX 5070 Ti Laptop as on Linux A5000, and which part is physical execution versus extra speculative work?

Here q8 is eight physical verification rows, not Q8_0 weight precision. k3 = seed plus three proposals (q4); k7 = seed plus seven proposals (q8). D4 names draft prefill geometry, not proposal count.

Read these pinned sources before implementation:
- [#209](https://github.com/leecdiang/HeteroSpec/pull/209), head `2d076402b4ddc29c92549d360cd974af40d3f0a4`: complete M2 build/reconstruction, finite gates, descriptive four-root A5000 pilot and all failures. LOCAL-packed k7/k3 service is +14.057%; replay +10.610%. These are not population claims.
- [#210](https://github.com/leecdiang/HeteroSpec/pull/210), head `3268a63dcbde99d5d9f8dd461f34d56e9840d3a0`: source/cost audit and equal-work diagnosis. This RTX study does not wait for its A5000 execution and does not borrow its budget.
- [#195](https://github.com/leecdiang/HeteroSpec/pull/195), head `873d16712fbf3bc04f54e9b3753515c5dbebb60f`, `benchmarks/tpds_phase1_v1/RESULT.md` and `REPRODUCE_RTX.md`: original Windows reference, native recipes, source/runtime closure and RTX geometry. Qwen whole q8 packed cost was 46.113 versus loop4 40.598 ms inside, and 73.481 versus 59.483 ms crossing. Do not assume packed or LOCAL-packed wins. Smol is a different model, not a replacement for Qwen.
- [#62](https://github.com/leecdiang/HeteroSpec/pull/62), head `8dfa60a2492e0639a0774f7bac842273485ca26a`, `benchmarks/rtx_closeout_bcd/REPORT.md`: original wide-query reference failures and fixed-UB4 repair. Its caller-eight path used physical microqueries <=4. It is NOT proof of true q8.

The paper contribution sought is a defensible platform-dependent operating envelope and cost explanation, not a universal k7 win, new decoding algorithm, or an opportunistic best-arm chart. A negative result is useful. No 32B, B570, new model family, precision sweep or automatic optimization campaign is included.

## 2. Stage A: zero-GPU reconstruction and pre-registration

Use the RTX laptop's original native Windows backend and independent scalar R. Do not execute the Linux binary, rename the Linux reference, change old reference arithmetic, or reuse A5000 qualification as a Windows proof.

Inventory device UUID/name and VRAM, driver, OS, CPU/RAM, loaded module hashes, compiler/toolchain, build flags, exact model/tokenizer hashes, source commits and generated source. Identify the full #209 transform/build chain and actual compiled worker; bridge only the width-aware frontend into the pinned RTX numerical implementation. Bind real loaded DLLs, not merely files on PATH. Keep original reference source/binary immutable.

Use Qwen3-8B Q8_0 target and Qwen3-0.6B Q8_0 draft, C1024, F16 KV, noFA and the original RTX CPU/thread/GPU placement settings where qualified. Target UB32 and candidate output reserve8 require explicit Windows qualification. Both k values use reserve8. Keep old reserve4 data separate and qualify the bridge; original scalar R remains UB1 and its original output policy. If any required model/build differs, stop and publish the difference instead of calling it the same comparison.

Check 12GB memory on the actual host before admitting jobs; preserve the existing resource reserve rules. Do not change quantization, offload, context, FA or numerical tolerances to make it fit. Record sampled memory as sampled, not guaranteed peak. No global power, driver or security changes. AC power and the already selected fixed performance mode must be documented; if conditions are unsuitable, wait rather than alter settings without approval.

Archive a source audit covering full-vocabulary vector ownership/lifetime, copies outside phase timers, allocation, synchronized decode, pending/frontier bookkeeping, rollback, tail proposals, JSON/materialization and reset. A residual is not evidence of logging cost; a host decode clock is not GPU kernel time. Retain old epochs and failures. No optimization is necessary to run the baseline transfer. A proposed optimization is a separate amendment/epoch, never spliced into the panel.

Before ANY new outputs, freeze: the exact executable/source/model manifest, all fixtures, cohort IDs/prompt bytes/token IDs, cap, order, timers, acceptance criteria, analysis and job/row ledger. Perform no-model schedule and accounting tests first.

## 3. Stage B: finite qualification, before clean timing

Ceiling 512 logical requests, including every new reference, bridge, fixture, rejected attempt and warmup. Enumerate exact jobs; this ceiling is not permission to drop required checks.

Port the relevant #209 natural, geometry, controlled rejection/all-accept/bonus, cap/EOG, reset, negative-test and proposal-tape ownership gates to the frozen Windows epoch. Reuse old proof only with exact code/data dependency bindings for unchanged paths. Check all requested full vocabulary vectors and active target KV/frontier against unchanged Windows R, plus target/draft pending/correction and final stopping semantics. Preserve existing tolerances. Expected rejects and accidental failures both count.

Explicitly exercise k7 actual occupied width8 under LOCAL and whole cuts, loop4/packed eligibility, within/cross native KV extent, all requested output rows and the second q4 call ownership. Log actual physical query widths, split coordinates, output masks, dimensions and device. Caller width8 with hidden UB4 decomposition is not q8. Never bypass a guard without implementing and qualifying storage, capacity, masks and ownership.

Use at least four exposed development roots (not the formal cohort), including a historical failing/cap-sensitive case where available. Qualifications must contain early rejection, full acceptance, bonus, short tail, EOG and context reset. Failure at a required gate stops the eight-arm panel; publish the failing case, not a silently smaller favorable panel.

Formal roots obtain independent full Windows R endpoints before timing, outside the timing set but charged to this budget. Development/qualification cost, including oracle regeneration, remains in complete accounting. A passing finite suite is not universal losslessness or task-answer correctness.

## 4. Stage C: equal-work target diagnosis

This isolates physical width cost from differing accepted work. No draft calls inside this diagnostic and no live-speedup claim.

Eight cells: fixed LOCAL cut x two projections (loop4/packed) x two executions (two sequential physical q4 calls / one physical q8 call) x two geometries (within/cross extent). Use four predeclared development origins with exact scalar continuations; do not select using timings.

Inspect the actual native extent E and absolute positions. If E=256, eight appended tokens at 248..255 are within, 252..259 cross; otherwise derive analogous verified positions before measurement. Frozen prefix/state/tokens must exist and fit C1024; a fixture that cannot be constructed is a reported blocker, not a synthetic claim of crossing.

Both executions start from identical target KV/frontier, consume the same eight known tokens, own all eight full vocabulary outputs beyond call return, and end at identical state. Second q4 consumes the state committed by the first. Compare every vector and active final KV/frontier to independent R. Restore and setup are outside BOTH primary timers, recorded separately. Primary operation time includes required vector materialization for BOTH. No last-row-only shortcut.

Four origins x eight cells x four paired repetitions =128 measured requests; one primer per origin/cell =32 primers. Total160. Four repetitions use AB, BA, BA, AB for q4pair/q8 within matched projection/geometry; reverse projection/geometry blocks in complementary rounds. These are paired diagnostic repetitions, not independent roots or a live confirmation. Qualification/oracle work is in Stage B.

Record all physical calls/rows, packed eligible/executed counts and dimensions. q4pair counts as one logical diagnostic request but two physical calls and all rows. Time and report per origin/cell and aggregate, with no significance hunting.

Optional profiling ceiling32 requests (all primers included), selected cells frozen before profile output. Profiler runs never enter clean timing. If profiling is unavailable, report missing attribution and continue only already-qualified clean stages; do not infer kernel behavior from host clocks.

## 5. Stage D: eight-arm live panel

The primary panel tests the current frozen, qualified RTX implementation, not an optimized replacement chosen because it wins.

Eight arms:
0 W-loop4-k3; 1 W-loop4-k7; 2 W-packed-k3; 3 W-packed-k7;
4 LOCAL-loop4-k3; 5 LOCAL-loop4-k7; 6 LOCAL-packed-k3; 7 LOCAL-packed-k7.

All use the same reserve8, model/backend/configuration, resident lifecycle and output contract. Independent R is the correctness oracle, not a timed target-only control. Therefore this panel does NOT establish speculation-versus-M superiority. Do not pool old #195 M timings with this new cohort.

Select 16 prospectively frozen roots: eight code and eight math from existing authorized benchmark pools. Selection uses a published deterministic seed20261109 and only task ID/domain and prompt-token length (<=192) criteria, never model output or speed. Exclude prior #195 formal roots, #209 exposed roots and qualification roots. Check overlap with #62 and disclose remaining prior exposure; if there are not enough eligible new roots, publish the shortage and amend BEFORE any formal outputs. Do not call benchmark tasks training-unseen. Freeze actual IDs/bytes/hashes, not merely the sampling procedure.

New panel cap =96 generated tokens; context C1024. This bounded horizon is intentional to retain meaningful replication within the historical row envelope, not chosen using outcome. Retain short/EOG-censored roots. It does not directly reproduce A5000's different horizon. Record tail-unconsumed proposals separately from rejected incorrect proposals and report cap-hit counts. No post-output cap or root changes.

Eight sessions/order blocks x eight arms x16 roots =1024 measured requests. Each arm/session is one resident worker: load once, two distinct exposed primers, then16 isolated requests with qualified resets. 64 workers,128 primers;1152 total live requests. All64 workers use identical frozen epoch/configuration. Do not run timed GPU workers concurrently.

Full eight-treatment Williams schedule: first row [0,1,7,2,6,3,5,4]; row s adds s modulo8 for s=0..7. Verify each arm occurs once at each position, and all56 ordered unequal adjacent pairs occur once over these eight rows. Freeze a separate deterministic per-session root permutation, shared by all arms in that session. Keep every session and root. These are order blocks, not eight independent hardware platforms or eight days.

Qualification must bridge clean timing to heavy capture with identical arithmetic/state/output policies. Clean timers retain endpoint/reference/trace/physical-counter/module checks and graph reuse checks, but do not insert full heavy KV capture into each timed request. Save complete process/load/first-result/primers/burst/worker/wrapper times and reset costs; inclusive clocks overlap and cannot be summed.

## 6. Estimands and analysis frozen before data

Primary family (four): total clean service k7/k3 at each fixed cut/projection. Sum over all roots/sessions, not average per-request ratios. Positive percentage means slower. Publish all four irrespective of sign. Resample the16 root clusters with replacement10000 times, keeping all paired arms/sessions of each selected root together, seed20261109. Report point estimates and two-sided98.75% percentile intervals (Bonferroni four-contrast family); explain finite sample/conditional configuration limitations.

Secondary mechanism family (four, separately labelled): packed/loop4 at fixed k7 for each cut; LOCAL/W at fixed k7 for each projection. Same paired-root method and separate98.75% intervals. Do not select the fastest arm then report its unadjusted interval. Provide session-specific and code/math descriptive sensitivity, cap-hit/tail accounting, without treating repeated cycles as independent samples.

Publish the full eight-arm table, per-root paired results, cycle/proposal/acceptance/unconsumed counts, target/draft/VERIFY physical rows, phase clocks, residual, complete overhead and sampled memory/power/temperature. Acceptance fractions alone do not prove speedup. Profile-derived attribution and equal-work diagnostics remain separate from live causal contrasts.

Cross-platform comparison is qualitative replication of direction and cost mechanisms under documented differences (GPU, OS, CPU, drivers, cohort, horizon), not a causal estimate of GPU architecture or pooled RTX+A5000 confidence interval. Only a later matched-input/horizon/build study could support that narrower attribution.

## 7. Finite resource admission and failure policy

Use the actual RTX cumulative ledger, NOT PR197's A5000 remainder. #195 snapshot:904/3072 requests and557528/4000000 reserved rows. Reconcile any later RTX work before admission. Never reset counters by creating a folder.

New tranche ceiling2048 logical requests:
- qualification/oracles/bridges512;
- equal-work clean diagnostics160;
- optional profiling32;
- live panel1152;
- failure/reconstruction/closure reserve192.
Total2048; with the published904 snapshot,2952/3072, leaving120 requests. These are ceilings, not mandatory spend or guaranteed sufficiency. No automatic borrowing between categories.

The original4M conservative reserved-row ceiling also remains. Snapshot row remainder3442472. For the live panel, if the inherited audited bound2*p+16*cap applies, p<=192/cap96 gives1920 rows/request, hence1152*1920=2211840. This leaves1230632 snapshot rows for all other work. Verify the bound against the actual code including references, reset, retries and special fixtures before using it; do not assume this arithmetic qualifies a worker. Enumerate all jobs and charge actual conservative bounds at admission. If any gate cannot fit the exact remainder, stop and ask for an explicit budget amendment; never weaken the gate or silently shrink the fixed panel.

Use the host's existing authorization window; do not inherit expired A5000 Sunday/Monday deadlines. Before execution publish start/end timezone, per-worker timeout, worst-case total wall estimate from qualification, source/job manifest and archive margin. Preserve900s worker timeout unless a separately justified amendment is approved. Do not pre-allocate64*900s as a runtime prediction. Admit each worker only if its bound fits time/rows/requests and leaves closure margin. A disconnected UI is not evidence that a job stopped.

Read-only check competing jobs and take the existing experiment mutex. Never kill foreign processes or interfere with the user's work. If interrupted or power/thermal conditions violate preregistered admissibility, preserve partial data and mark the panel incomplete; do not refill only adverse slots. Any rerun needs a new fully identified epoch with all attempts retained. No optional stopping on a favorable confidence interval. Completion is all planned slots or an explicit stopped-stage report.

## 8. Deliverables and decision

Use a new result branch/directory. Publish PLAN_FREEZE, SOURCE_BINDINGS, JOB_MANIFEST, QUALIFICATION, SAME_WORK, LIVE_RESULTS, COMPLETE_COSTS, CUMULATIVE_LEDGER and LIMITATIONS with raw/derived hashes; names may match existing schemas but must be documented. Preserve failed versions, original Windows R, all prior artifacts and source-only reconstruction. Verify public readback and recompute summaries from archived records. No weights, credentials or unrelated host data in GitHub.

Terminal outcomes:
1. Real q8 cannot qualify on this RTX epoch: locate the finite failure and stop live timing.
2. Equal-work q8 is efficient but live k7 loses: proposal/work economics, not batching alone, limits width.
3. Equal-work q8 is expensive: physical implementation/platform evidence explains part of the loss; no universal kernel diagnosis without profiler proof.
4. Live k7 helps within one or more predeclared conditions: retain all adverse cells and quantify limited scope.
5. No meaningful width difference or insufficient resources: publish the complete bounds/partial status without inventing a win.

This protocol strengthens the existing hardware-aware execution and evidence story. It does not require q8 winning, a new algorithm label, or32B before paper reconstruction. No merge, Release, data deletion, baseline rewrite, manuscript submission, extra model sweep or experiment launch is authorized merely by creating this design PR.
