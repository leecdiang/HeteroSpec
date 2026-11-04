# Strong baseline discrimination experiment proposal

Status: planning only, 2026-11-04. This is a proposed preregistration, not a registered or executed experiment. Source and binary hashes, input manifests, device availability, execution authorization, and the final stage budget remain to be filled before any native launch. No RTX or B570 work was performed for this document. Publication adds planning and offline-recalculation files only; it is not authorization to execute on any device. Historical experiment data, runtime code and PR state are unchanged.

## Decision and scope

First determine whether independent four-column packing improves upon a strong backend four-column MMVQ implementation under the same frozen arithmetic. Begin with a small real-operand qualification, not another complete corpus campaign. Only proceed to a separate exploratory service pilot after that gate. Use the pilot to assess variance, bottlenecks, preparation cost, and failure risk before committing a disjoint confirmation panel.

A 32-root allocation is a budget option, not a power proof. The earlier suggestion of 736 requests covered a particular 32-root, three-arm main study plus reserves; it did not include a separate pilot. This document replaces that shorthand with cumulative budgets.

The proposed useful effect of 3% complete-service reduction is a project planning screen inherited from earlier studies, not a journal acceptance standard. Detecting a true 3% improvement over zero is different from proving that improvement exceeds 3%. No acceptance probability or guaranteed speedup is asserted.

## Evidence that constrains the design

The implementation limits below were rechecked against the independent audit at fixed head 7f564ee3badb50d540d7dbc04031a03c32feae90. Publication starts from b392f3119e2e800790b363743b332693f1438e8b, which adds the research route document. The earlier d694011 snapshot is historical, not the current audit status.

The later audit already repaired C++ and Python failed-callback CLEAN resurrection, added executable per-request structural-assumption predicates, and separated known-identity prefix lookup from stored-state integrity with conflicting-state quarantine. Its reported 61 Python tests, 652 primary plus 72 independent C++ checks, 47 native tiny-Q8 CPU checks, 16 tensor checks, 19 mocked CUDA-audit ABI checks, and eight upstream state cases are acknowledged. They are distinct CPU/fixture scopes, not new GPU experiments. None of those repaired issues is presented here as an outstanding bug. CUDA/Windows/Qwen GPU qualification and low-overhead native write-set recovery remain separate open tasks.

1. PR171 compared a graph-level four-column tile/concat path with independent-group packing. Its q32 Q-projection kernel count was 23 versus 2, but a backend loop over already quantized columns removes repeated graph quantization and concat. The new comparison must not reuse 23 versus 2 as evidence against that stronger baseline.
2. At public comparator commit f0dafdbd9dba40bd0e596f74f3da5f592900fca4, the MMVQ loop advances the already quantized vy pointer in groups of at most four. Only this mechanism informs B4. Importing the comparator's other CPU/GPU parity changes would change the reference contract and invalidate the controlled comparison.
3. PR171's measured oldQB/newQB complete-service ratio was 1.0417 on four natural inputs. Most benefit was prefill. k3 verification uses four rows and cannot enter the packing path that requires at least eight columns.
4. PR174 and PR175 found no registered AUTO service benefit. PR177 found a 3.951% append point reduction for WB-rechunk relative to QB, but a 0.562% service point reduction with opposite session directions. These results remain negative evidence; this proposal does not retune AUTO or rescue QB by selecting favorable roots.
5. At the rechecked 7f564ee audit revision, PR179 still has no CUDA compilation or execution qualification. Enforcing mode rejects an entire CUDA split. Its current state owner performs full state synchronization/export before and after execution, copies logits, disables bound graph reuse, and uses fresh-context restoration. Metadata collection and CPU tests do not establish GPU numerical qualification or net service benefit.

## Arms and immutable controls

- R: unchanged original scalar numerical reference and its authenticated assets.
- B4: backend four-column MMVQ split in the same frozen source/arithmetic cohort, with one outer activation quantization and direct output writes. No graph concat.
- P4: PR171 independent four-column group packing.
- L4: historical graph tile/concat path, optional mechanism diagnostic only.
- G4: P4 plus a genuinely implemented and qualified native admission/checkpoint/recovery path. This arm is absent until it can execute correctly on the target GPU. Collect-only instrumentation is not G4.
- Native wide/stock: optional incompatible numerical-path speed context, never an eligible exact-reference baseline unless it independently qualifies.

B4 and P4 share quantization, per-output K reduction, QK/AV rules, head placement, model, KV precision, compiler options, runtime modules, and caller. Use the same fixed WB-rechunk caller in service to isolate operator lowering. Do not transplant other changes from the public comparator. Retain unsupported cases as unsupported rather than changing R to admit them.

Pin source, compiler and flags, executable, loaded DLLs, runtime, driver, physical device, model, tokenizer, graph configuration, and output flags. A new binary does not inherit the old binary's empirical qualification. Record actual post-packing strides, channels, samples, launch parameters and quantizer. A descriptor match is not a floating-point proof.

## Stage 0 Cloud preparation and admission plan

Permitted preparation without occupying user devices:
- Review the B4 patch against the frozen source and verify that only the intended dispatch/lowering changes.
- Build and run available cloud-only host/CPU tests without promoting them to GPU evidence.
- Prepare manifest validation, immutable output directories, accounting, offline reconstruction and analysis scripts.
- Verify saved capture identities and available operand dimensions.
- Freeze the smoke cases and their order before new GPU output.

Preparation gate before any user-device execution:
- Explicit authorization for device and bounded stage.
- Confirm that the device is idle using the approved host mechanism and shared experiment lock. Do not infer idle status from an earlier report.
- Validate actual toolchain availability, including CUDA/Windows ABI prerequisites. No installed toolkit is assumed.
- Check model availability, loaded module identities, free RAM/disk/VRAM, temperature/power policy, and other GPU users.
- Run zero-forward admission and record startup/peak resource readings.
- Recheck admission for added state copies. Old successful admission does not cover G4.
- Stop and report a blocker if these conditions fail. Do not migrate to a rental or another user device without authorization.

Planning reserve: up to two engineer-hours of build/integration investigation before a fresh decision. This is an effort cap, not a promise of CUDA readiness. Record failed builds and preparation time separately from scientific requests.

## Stage 1A Minimum real operand smoke

Use authenticated real 8B operands for four classes: Q projection, V projection, FFN down, and vocabulary output. Including V preserves an existing non-speedup counterexample. Use q = 4, 5, 8, 32, for 16 cases. q4 is the unchanged-path control, q5 tests the tail, q8 tests the dispatch boundary, and q32 tests maximum admitted grouping.

For each case:
- Replay R, B4 and P4 on exactly the same weight and F32 activation bytes.
- Compare every binary32 output byte, finite status and output geometry.
- Check actual selected dispatch and quantizer. Do not infer them only from the graph description.
- If an existing capture cannot supply a case, report the missing case before launch. Do not synthesize operands and continue calling them real captures.
- First complete correctness for all cases; only then time B4 and P4.

Budget:
- 16 case evaluations per route. A scalar R evaluation may require q separate graph submissions.
- Assuming scalar-column replay, the R count is 4 operators times (4+5+8+32) = 196 graph submissions; B4/P4 qualification adds 32.
- Two independently loaded clean sessions, each with one immediate warmup and ten timed repeats per case/optimized arm: 16 times 2 times 2 times 11 = 704 graph submissions.
- Optional separate q32 profiling of all four classes and both optimized arms: 8 submissions.
- Planned total 940 operator graph submissions; hard allowance 1024 including explicitly logged engineering attempts. No automatic retries or extra repeats after viewing signs.
- This is zero end-to-end service requests, but it is real GPU work and still requires device authorization.
- Provisional native wall allowance: 30 minutes excluding build and model transfer. The executable must stop at a safe unit boundary if the authorized allowance is exhausted. Actual timing may require a revised budget; there is no promise all cases fit.

Clean and profiled binaries are distinct. Report synchronized graph wall, graph-definition time, host submit/wait, kernel count and temporary/output-write bytes. Kernel duration and CPU wall are overlapping scopes, not additive components.

Go: exact qualification passes and a repeatable improvement remains in relevant work after B4 removes the weak-baseline overhead. No fixed percentage is required at this small operator stage.

Stop or narrow: any required exact-reference mismatch; invalid launch/residency assumptions; B4 matches or beats P4 on the useful descriptors; or the plausible service saving is smaller than measured added execution-policy costs. An inconclusive small timing difference does not prove equivalence, but can justify not purchasing a larger study.

The mechanism prediction to test is approximately one quantizer plus eight MMVQ launches for B4 versus one quantizer plus one grouped MMVQ at q32, without concat on either side. This is a prediction, not an observed result.

## Stage 1B Broader qualification only after the smoke

Optional expansion covers the 16 captured model/operator descriptors from Qwen3-0.6B and 8B, at q = 1, 4, 5, 8, 16, 31, 32: 112 operand cases. Keep missing descriptors and all counterexamples.

For scalar-column R, the planned reference submissions are 16 times 97 = 1552; B4/P4 add 224, for 1776 qualification submissions. A proposed cap of 2048 covers logged engineering attempts, not an unconstrained timing sweep. Load models serially. Do not add L4 timing or multiple profiler repeats without updating the registered budget before output.

This stage is finite empirical coverage. It does not prove arbitrary quantization, layout, architecture, hardware or concurrent execution equivalence. No natural-service performance conclusion follows from passing it.

## Stage 2 Separate exploratory service pilot

Use eight output-blind hash-selected natural roots not used to tune B4/P4. This pilot is explicitly exploratory, not the confirmatory paper panel.

Fixed RTX deployment:
- Original RTX 5070 Ti Laptop, after current authorization and idle check.
- Qwen3-8B Q8_0, fixed model SHA256 408b955510e196121c1c375201744783b5c9a43c7956d73fc78df54c66e883d6.
- C4096, F16 KV, non-flash, all-GPU target-only, qmax32, greedy cap128/native EOG.
- Identical WB-rechunk caller and snapshot lifecycle for B4/P4.
- Two separately loaded sessions, balanced pre-generated arm orders. Sessions are not assumed to be independent days.

Per root, run R twice and each candidate once with heavy output capture and once observer-off. This is six qualification requests per root, 48 total. Timings use two arms, two sessions, and an immediate same-arm warmup for every measurement: 64 requests including 32 measurements and 32 warmups. Total pilot budget is 112 service requests.

Keep reference creation, failures, setup, loads and snapshots in cumulative cost. Two predeclared sessions are not extended after inspecting results. Provisional original-host native wall allowance is one hour, excluding builds, artifact transfer and unavailable-device waiting; this is a planning limit, not a runtime forecast.

Pilot questions:
- What are the root-level paired log variance and session reversals?
- Is most time outside the changed operators?
- Does B4 already eliminate the useful gain?
- Are readback/checkpoint/graph-rebuild costs large enough to make G4 unpromising?
- Do qualification, preparation, memory headroom, or restore failures prevent safe completion?

Do not pool these eight roots into the later confirmation estimator. Their outcomes may inform the decision whether to continue. Once the later sample size and input rule are frozen, do not extend the confirmation panel in response to its results.

## Historical variance and sample size sensitivity

The supplied historical JSONs are exact parsed copies of the public PR174/175 analysis files. The companion script recomputes sample SD across the 32 root-level log contrasts. Those root contrasts already average four old sessions.

Selected SD estimates:
- RTX QB/AUTO: 0.043776.
- RTX WB-cut/AUTO: 0.045041.
- RTX WB-rechunk/AUTO: 0.037716.
- RTX WB-rechunk/QB: 0.044722.
- B570 WB-rechunk/QB: 0.004362.
- B570 WB-cut/QB: 0.006828.

These are not variance estimates for the new B4/P4 treatment. They mix old treatment heterogeneity and execution noise, use different arms, and are averaged over four rather than two sessions. B570 has a different lifecycle and cannot supply RTX power. Its apparently very small SD must not be converted into absurd one-root designs.

For planning only, a single two-sided 5% comparison with a desired 80% normal-approximation power has log-scale detectable effect approximately 2.8016 times sigma divided by sqrt(n). A corresponding service-time reduction is 1-exp(-effect). Detecting a true 3% reduction over zero uses delta = -log(0.97), not 0.03 exactly.

| Assumed root log SD | Approximate MDE at 16 roots | At 32 roots | At 64 roots | Normal approximate n for 3% |
|---|---:|---:|---:|---:|
| 0.0450, historical RTX scale | 3.10% | 2.20% | 1.56% | 18 |
| 0.06364, sqrt(2) sensitivity | 4.36% | 3.10% | 2.20% | 35 |
| 0.0675, 1.5x sensitivity | 4.62% | 3.29% | 2.34% | 39 |
| 0.0900, 2x sensitivity | 6.11% | 4.36% | 3.10% | 69 |

The sqrt(2) row describes a scenario in which reducing four averaged sessions to two increases independent session-noise variance; it is not a valid bound under drift or correlated sessions. The other multipliers are transparent sensitivity assumptions, not empirical estimates or confidence limits. Normal approximation ignores small-sample t corrections, heavy tails, root mixtures, hardware drift, qualification selection and multiple primary tests.

At sigma 0.045, detecting a 1% service reduction would need approximately 158 roots under that optimistic approximation; at sigma 0.06364 it would need approximately 315. A residual sub-percent win over B4 is not credibly established by declaring 32 roots enough.

Use the pilot to update planning, not to claim guaranteed power. Before confirmation, publish the observed pilot SD, the historical sensitivity comparison, the chosen effect of interest, the chosen allocation, the funding/device cap and the residual power uncertainty. A fixed budget may justify a pilot-sized result or a stop instead of an underpowered positive narrative. If demonstrating a lower confidence bound above 3% is required, plan for a true effect larger than 3% and use the gap to that threshold; the table above does not do that.

## Stage 3 Optional disjoint confirmation

Choose the confirmation allocation only after the separate pilot, then freeze it before confirmation output. Suggested budget options are 16, 32, 48, or 64 new roots. They are allocation choices, not asserted power guarantees. If variance and the expected effect make the available allocation uninformative, stop or seek a different authorized budget rather than promise success.

Primary sample:
- Output-blind hash-ranked eligible natural roots, disjoint from tuning, pilot and known prior exposure.
- No padding, offset selection, favorable-output filtering or replacement roots.
- Freeze source/binary hashes, full token inputs, physical heads, eligibility rule, arm order, warmups, sessions, timeouts and analysis seed.
- Keep known-exposed historical panels as regression tests only, not newly unseen data.

Two-arm scientific request count is 14n: 6n qualification plus 4n measurements plus 4n immediate warmups.
Three-arm count is 20n: 8n qualification plus 6n measurements plus 6n warmups.

| Main roots | Two-arm main requests | Three-arm main requests |
|---|---:|---:|
| 16 | 224 | 320 |
| 32 | 448 | 640 |
| 48 | 672 | 960 |
| 64 | 896 | 1280 |

Cumulative examples:
- Eight-root two-arm pilot plus 32-root two-arm main: 112+448 = 560 scientific service requests. Adding an optional 32-case recovery allowance and 64 engineering requests gives 656.
- The same pilot plus 32-root three-arm main: 112+640 = 752 scientific service requests; the same reserves give 848, not 736.
- If the pilot also has three arms, its own count is 160 and must replace 112 in that total.
- Operator graph submissions, build/admission processes and service requests are separate denominators. Report all; do not call zero service requests zero GPU use.
- A recovery case is a bounded native test transaction, not a free operation. Its actual constituent decode/restore calls and wall time must be recorded. Any additional reference/control transactions consume the reserve.

If G4 is absent, the primary contrast is P4 against B4 and the conclusion is explicitly about the unguarded compatible lowering. If G4 is included, make G4 against B4 the single primary system contrast; P4 describes the idealized lowering and safety cost. Do not select the headline between these after seeing results. An equally guarded B4 ablation can explain the safety mechanism but cannot replace G4 versus the strongest fixed deployment and hide absolute safety overhead.

Conditional strata are descriptive and fixed from input/geometry before output:
- Crossing versus noncrossing physical KV boundary.
- Requests with columns large enough to pack versus q<=4-only negative controls.
- Operator descriptor and width for the operator panel.
- Cache-hit service versus separately specified empty-cache control.

Do not guarantee adequate counts in a rare natural stratum. Report observed counts. An enriched diagnostic panel is a separate conditional population and cannot be pooled into the natural estimator.

## Endpoints and analysis

Main endpoint: native ready-token request entry to synchronized response/state commit, with the same lifecycle in both arms. Include all actual file reads or declared preload amortization, lookup/index/reset/import, admission/registry access, append, continuation, checkpoint export/readback, logits copies, graph rebuild, rejection/fallback, restore, synchronization and response commit.

Report model load, context provisioning, scalar prefix production, compile, calibration, cache preload, evidence I/O, failures and transport separately in cumulative resource accounting. State which costs are inside service. Do not add overlapping phase windows. Keep heavy-observer qualification out of clean timing, while retaining its actual campaign cost.

For each root, average session log ratios log(T_B/T_C); then average roots equally and exponentiate. Resample roots with all paired sessions and arms intact, using 10,000 bootstrap draws and a frozen seed. Report paired absolute milliseconds and every root/session result as well. The independent sampling unit is a root, not a repeated measurement, generated token or kernel.

A possible project success screen is:
- All required numerical/state qualifications pass.
- Primary interval supports positive service benefit.
- Point reduction reaches the predeclared 3% useful-effect screen.
- Both recorded sessions have the same direction.
This screen does not prove that the true reduction exceeds 3%. A stricter claim requires the appropriate lower confidence bound above that threshold.

An interval crossing no effect is inconclusive, not equivalence. An upper confidence limit below the useful-effect threshold can rule out that threshold only within the stated estimator and sampling scope. p95 from this panel is descriptive, not an SLA estimate. No population GPU or cross-date claim follows from two loaded sessions on one host/date.

## Native recovery evidence before any G4 performance claim

Qualify the actual GPU host and ABI, not a mocked context:
- Successful full-state checkpoint round trip, including independent logits, pending token and positions.
- Late rejection after slot allocation, synchronization of prior asynchronous work, and continuation matching untouched R.
- Import failure and readback mismatch on a fresh context.
- Unsupported layout/stride/residency/q and mismatched device/runtime identity.
- Cache metadata mismatch and retained last-good checkpoint isolation.
- Tainted state remains unavailable until full recovery succeeds.

Reserve up to 32 initial cases, with a complete generated case manifest before output; freeze their internal call counts and native budgets. The number 32 is an engineering coverage allowance, not a statistical failure-rate bound. Do not advertise universal device-loss, process-crash or concurrency recovery from these tests.

## Retention and stop rules

Keep every scheduled root, arm, warmup, measurement, timeout, OOM, mismatch, rejected descriptor, fallback, partial receipt, build failure and interrupted job. Reserve a unit before starting it. Incomplete reservations remain accounted for. Never replace a failing or slow root, discard warmups after comparing them, retune policy, or append rounds based on favorable signs.

- Correctness or state contamination: stop the affected path immediately and preserve failure evidence.
- Resource/authorization/idle check failure: no launch; report the exact blocker.
- A required baseline that cannot qualify: no controlled speedup claim; do not drop it to revive L4 as sole primary.
- Unpromising B4/P4 operator outcome: stop expansion, or retain a narrowly described negative result.
- Safety costs larger than plausible saving: do not run a full positive-system campaign just to search for lucky roots.
- Exhausted stage budget: stop at a safe boundary and report incomplete coverage. No automatic extra tranche.
- Repairs create a new source epoch. Preserve old outcomes and preregister a new evaluation stage; do not silently restart the old panel.

The independent confirmation panel remains valid as a confirmation of a pilot-selected decision only if the primary claim is tied to its own fixed test and new roots. Do not pool pilot and confirmation p-values or rebrand the full adaptive sequence as a single fixed experiment.

## Platform and resource constraints

RTX first: it directly tests the implemented B4/P4 distinction. Original deployment evidence identifies an RTX 5070 Ti Laptop with driver 616.92, but current loaded-driver/device facts must be rechecked. Do not assume a device is free, compiler-ready or thermally comparable now.

B570 is optional, separately authorized follow-on work:
- Retain its Vulkan F32 activation/p021 reference.
- CUDA MMVQ loops do not exist as a drop-in Vulkan baseline.
- PR179 currently has no qualified Vulkan admission/instrumentation path.
- Existing target-only C4096 admission does not repair historical failed dual-model k1 admission.
- Original B570 records show 37/37 layers on Vulkan, 576 MiB KV, and 630.59 MiB CPU_Mapped model buffer.
- Existing RTX service uses resident context/file-backed snapshot, while B570 uses host-memory snapshot/fresh context. Their absolute service times are not a hardware comparison.
- Establish a Vulkan-specific unchanged-reduction transformation and matched lifecycle before claiming portability or cross-device speed differences.

Historical runtime is context, not a forecast: PR174 recorded 7288.124 seconds of completed native-process wall across 1957 completed receipts and retained incomplete reservations; PR175 recorded 16562.891 seconds for its broader 1842-completed-request campaign. Build repair, scalar qualification, state I/O and orchestration can dominate. Do not divide these totals by requests and promise a completion time for the new implementation.

Storage planning: 32 roots times 128 output rows times 151936 vocabulary entries times four bytes times four heavy/reference trajectories is 9,957,277,696 bytes, approximately 9.27 GiB, before states, logs and temporary copies. Reserve and verify at least 20 GiB for that two-arm main-study evidence plan; larger or three-arm plans require a recomputed budget. Compression savings are not admission evidence.

Measure host/device peak allocations with full checkpoint copying and fresh-context restore. The old RTX 512 MiB and B570 128 MiB free-device reserves are historical policies, not proof the expanded path fits. Retain real model/context setup costs, serialized snapshot bytes and measured transfer traffic as different quantities. No new hardware purchase, rental, simultaneous model loading or device reservation is implied.

## Low cost alternatives and final outcomes

1. Cloud-only result: completed B4 source/host tests, verified case manifests, statistical plan and explicit GPU NOT_RUN status.
2. Authorized operator-only result: the 16-case smoke can falsify remaining packed merit without hundreds of service requests.
3. Authorized pilot-only result: 112 service requests can expose cost dominance and noisy estimates; report exploratory effect ranges without journal-level population claims.
4. Historical-data-only result: stronger baseline design plus reproduction of old negative findings, with no new performance assertion.
5. Full confirmation only after the prior gates, an informative budget and device authorization.

The research remains useful if the strong baseline eliminates the apparent benefit. Preserve that result and narrow the claim. Do not convert more protocol code, a larger test count, or a smaller p-value into a promise of TPDS acceptance.

## Sources

- [PR171 operator and service results](https://github.com/leecdiang/HeteroSpec/blob/371223b696bb805030c29f04e39eb17b57fb2ebb/benchmarks/rtx_operator_frontier_v1/execution/RESULTS.md)
- [PR171 bindings](https://github.com/leecdiang/HeteroSpec/blob/371223b696bb805030c29f04e39eb17b57fb2ebb/benchmarks/rtx_operator_frontier_v1/execution/evidence/bindings.json)
- [PR174 results](https://github.com/leecdiang/HeteroSpec/blob/aa7ff4e64752be3de0d7974febbce453ae3a96c0/benchmarks/rtx_prefix_reuse_v1/execution/RESULTS.md)
- [PR174 root contrasts](https://github.com/leecdiang/HeteroSpec/blob/aa7ff4e64752be3de0d7974febbce453ae3a96c0/benchmarks/rtx_prefix_reuse_v1/execution/evidence/analysis.json)
- [PR175 results](https://github.com/leecdiang/HeteroSpec/blob/cd5f542a851d192e21187bc00566de0f685e2383/benchmarks/b570_prefix_reuse_v1/RESULTS.md)
- [PR175 root contrasts](https://github.com/leecdiang/HeteroSpec/blob/cd5f542a851d192e21187bc00566de0f685e2383/benchmarks/b570_prefix_reuse_v1/evidence/analysis.json)
- [PR177](https://github.com/leecdiang/HeteroSpec/pull/177)
- [PR179 implementation limits and costs](https://github.com/leecdiang/HeteroSpec/blob/7f564ee3badb50d540d7dbc04031a03c32feae90/docs/research/reference_contract_20261104/IMPLEMENTATION.md)
- [PR179 independent audit and completed repairs](https://github.com/leecdiang/HeteroSpec/blob/7f564ee3badb50d540d7dbc04031a03c32feae90/docs/research/reference_contract_20261104/INDEPENDENT_AUDIT.md)
- [Comparator fixed patch](https://github.com/amiller/llama_reproducible/blob/f0dafdbd9dba40bd0e596f74f3da5f592900fca4/patches/0001-all-deterministic-parity.patch)

