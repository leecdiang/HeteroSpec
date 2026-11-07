# Scientific protocol

## 1. Decision, rivals and scope

H1: on actual reusable prefixes, local grouping saves work that cannot be recovered by a reference-compatible whole-graph caller.
H2: the old comparison overstates local value because a caller can restart full-width chunks after a boundary.
H3: apparent nonalignment is a logical-prefix artifact; effective cache-granule rounding removes it.
H4: append improvements exist but cache handling, remaining decode or calibration prevents a useful total-service improvement.

These are prospective candidate explanations. Old q8/q32 results motivate them, but do not count as new evidence. A negative result is a completed experiment, not a reason to change widths, examples or references until a win appears.

Primary scope: single-stream, dense causal append with known input tokens, all-GPU Qwen3-8B Q8_0 target only, F16 KV, non-flash attention, qmax=32, ordinary greedy continuation with cap128/native EOG. The exact target, tokenizer, native renderer, scalar oracle libraries, placement and stop rule are frozen before candidate outputs. This is conversational trace replay, not live production telemetry, task-accuracy evaluation or closed-loop agent evaluation. Historical assistant messages are known replay inputs, not falsely attributed to this target model.

## 2. Zero-forward preparation and opportunity census

Recover exact source/runtime assets from the platform pins in `study.json`; preserve old references, failures and ledgers. Capacity admission tries C4096, C2048, C1024 in this order, at most two zero-forward probes per rung if an identified engineering error requires one corrected build. No prompt/output/speed selects a capacity. Prefer the largest configuration admitted on both hosts. If there is no common admitted deployment, report separate deployments and do not pool their timing or call it a controlled hardware comparison. No hidden precision reduction, CPU weight offload or draft-loading fallback.

Download the pinned OASST1 revision and freeze its files and native tokenizer/template bytes. Use English, nondeleted, nonsynthetic, complete alternating conversation paths ending in a prompter/user message, with at least one prior assistant turn. Retain all candidate paths and exclusion reasons. Build the cached history from the same path through the preceding assistant message; render both histories using the exact serving template and tokenize each complete string natively. Compute the token-level longest common prefix. Do not join independently tokenized snippets, add synthetic padding, truncate prompts to fit, or select offset bands after timing. Exclude requests whose full prompt plus output allowance cannot fit the selected deployment; report their number and length distribution.

For every path, distinguish:
- logical common-prefix length;
- the cache manager's **effective reusable length**, granularity and reason for any rounding;
- actual dense physical append head and allocator padding;
- appended token count, q32 caller sequence, required attention groups and predicted WB calls;
- prefix-lookup/materialization mode and source-message/root identity.

A full-block prefix cache can round the reusable length. In particular, a reusable head aligned to q32 with P=256 produces no internal crossing for q32 chunks. This implication is checked from descriptors; it is not an assumption about all engines. The primary implementation may support exact-token persistent snapshots, but must label that deployment explicitly. Alongside it, compute an output-free sensitivity census for cache granularities 1, 16, 32 and 64. These are declared cache-policy scenarios, not measured vLLM/SGLang performance or claims about their defaults. Report full-pool rates and sampled-panel rates separately.

If the actual admitted reuse policy has zero active crossings, preserve that result. Complete only the bounded aligned control and compatibility work needed for the negative conclusion; do not replace it with fabricated offsets. A token-granular deployment can be studied as a separately named application only if it is genuinely implemented, not relabeled as the original cache policy.

## 3. Cohorts, exposure and freeze order

Before any target or candidate output on new inputs, hash-rank eligible conversation roots with the fixed seed in `study.json`. Choose one eligible terminal path per root by a second hash, without inspecting outputs, timing, crossing status or target quality. Use 12 disjoint calibration roots and 32 held-out roots. This primary estimand weights roots equally; it is not the message-frequency distribution of the full dataset. Report the metadata census so this distinction is visible.

Audit exclusions against all known prior HeteroSpec task IDs/text/token hashes. Shared roots never occur in both calibration and test. A pre-output shortfall is reported as insufficient eligible coverage; no silent downsampling or output-driven source replacement. Native tokenizer and renderer identities must match across hosts to call the panel shared. Different renderings require explicitly separate panels, not a fabricated paired hardware contrast.

Both host implementations can develop concurrently on old/synthetic/calibration inputs. Each sends a source/deployment/calibration-policy freeze receipt. No platform starts the common held-out outputs before both freezes exist. If one host cannot finish, the other may complete an independent panel under a prospectively recorded fork, but it cannot later call exposed transfer blind dual-platform confirmation.

## 4. Strong baselines and selector

All arms use the same qualified arithmetic core within a backend: packed Q8 CUDA projection/FFN where admitted; Vulkan's scalar-compatible activation and attention paths. All use identical prefix state and input tokens within a paired request.

**QB:** retain fixed q32 outer caller chunks and cut attention locally using the scalar physical requirements.

**WB-cut:** the inherited comparator. Keep the original q32 outer-chunk origin; divide each chunk at required physical boundaries. For example H253 and a q32 call becomes 3+29, then the original next q32 chunk begins at 285.

**WB-rechunk:** an alignment-aware whole-graph caller. At each step use min(remaining,32,distance to the next required physical boundary), then restart the next full chunk from the new head. H253 begins with 3, then full32 chunks begin at256,288,... . Its final remainder is charged. It changes caller partitioning, not tokens, reference, dtype or numerical core. Generalize from the native requirement extractor, not an assumed logical-index formula outside dense append. If code inspection establishes that an inherited implementation already behaves identically, mark an alias and remove the duplicate arm prospectively before freeze, with corresponding schedule/statistics/budget amendment.

**AUTO:** choose one of the three whole-request append policies once, using only deployment identity and pre-output structural descriptors. No selection by model name, task ID, text semantics, output margins, held-out latency or trialing all policies online. Leave ordinary q1 continuation unchanged. A mid-request switch is outside the primary design because state/graph identity needs separate proof.

Calibration uses all 12 calibration roots, three fixed policies, two sessions, matched immediate warmups and a deterministic position-balanced order across roots. It is not a full within-root three-arm Williams crossover. Fit at most a three-entry lookup by the predeclared old-WB extra-call density (zero, positive <=1/8, >1/8). An entry needs >=4 calibration roots; otherwise use the all-root best fixed policy. Within an entry, select a different policy only when its geometric-mean time is at least 2% lower than the global winner; ties fall back to WB-rechunk, then WB-cut, then QB. Fix the selector and source before held-out qualification. This small empirical policy has no claimed optimality. A constant selector is valid and its lookup overhead remains charged. The host measures calibration cost rather than treating offline tuning as free.

## 5. Reference, state and numerical qualification

Each deployment obtains an independent original scalar reference before candidate qualification. Two original runs per main input check repeat stability. Changing capacity/residency creates a separately named deployment and a new prospectively fixed reference; it never changes old R to erase a failure.

Prefix snapshots must come from a reference-compatible producer. First authenticate shared-state restores and own-path roundtrips, including positions, pending-token ownership, initial logits where required and output flags. A final KV hash alone does not certify complete context restoration. For the main deployment, cache lookup and actual state materialization/import are part of service. Rebuilding a canonical prefix solely for qualification does not become a hidden runtime repair. Record prefix-construction time separately and charge it in the observed trace total.

For each candidate input check heavy/off complete endpoints and every committed full-vocabulary binary32 vector with exactly the same requested output-row flags as clean service. Separately probe known appended rows against scalar replay of the same tokens. Requesting all append logits can change graph shape, especially the output projection: those probes are a separately labeled diagnostic, not a substitute for qualification of the actual service output flags. An observer must capture owned buffers before reuse and pass its own same-path control. Also check ordered append plans, actual heads and widths, no double consumption, EOG/cap, cache mutation isolation, and final continuation. Appended known-token logits do not imply that the target would have generated the historical transcript. Same-path capture/no-capture controls must match. Before main timing, confirm all four arms on all32 inputs. One numerical failure withholds that arm's whole-panel qualified performance claim; retain diagnostic times and every failed input. Do not select a passing subset.

The new primary study has no draft. RTX k3 and B570's historical k1/capacity behavior remain separate. No new B570 speculative gain is inferred from target-only success.

## 6. Time windows and execution

Primary: synchronized complete cache-hit service from receipt of the fixed token request through prefix-key lookup, actual state materialization/import or binding, policy lookup, append, greedy generation, synchronization and state/response commit. Include actual context creation/destruction if that is the chosen serving lifecycle. Declare one lifecycle before calibration and use it in all arms. Shared resident model loading is outside and separately reported. No per-token memory polling is added to one arm only; the same safe monitoring policy is retained and its overhead is not subtracted.

Secondary: time-to-first-output/append interval; lookup/import, producer and decode diagnostics in separate observed runs; total trace cost including all actual cache creations and misses. Calibrated phase subtotals are not a substitute for measured complete service. No timing with heavy vector dumps or profiler callbacks. Each formal measurement has one immediate same-input/arm warmup, with restored/reset state, not a warmup allowed to mutate the measured starting state.

Main timing: 32 roots x4 arms x4 independently loaded sessions =512 measurements +512 warmups. A four-period Williams order gives each arm each position and each ordered predecessor once per root. Hash-randomize root order within session. Separate sessions across two dates where practicable; if all occur on one date, report that fact and do not claim cross-date inference. The sampling unit remains the root, conditional on these measured sessions.

Aligned negative control: the same unmodified full prompts of the first eight held-out roots, from an empty cache (no prefix content removed), three fixed arms, two sessions,96 timed/warm slots plus64 R/candidate heavy/off qualification slots. This is a different lifecycle workload, not part of the primary cache-hit estimator. No invented padding.

## 7. Analysis and stopping

Primary log contrast for fixed arm b and AUTO, per root i, is the mean over all four matched session log times log(T_b/T_AUTO). Equal-root geometric means are reported for QB, WB-cut and WB-rechunk. To claim AUTO improves upon the best fixed choice, all three relevant complete contrasts must pass; do not compare only with the slowest baseline. Retain WB-rechunk/QB and WB-cut/QB as descriptive fixed-policy contrasts.

Bootstrap roots, carrying their complete four-session arm vectors together, seed20261104,10000 draws. Use two-sided 98.333% intervals per each of three AUTO comparisons (Bonferroni family95%). Report unadjusted95% intervals only as secondary, explicitly labeled. Three hosted systems are not independent samples for a GPU-population confidence interval. No cross-platform pooled estimate. No p-value as acceptance probability, no request-level bootstrap of128 repeated rows, and no formal equivalence claim from an interval crossing1.

Predeclared engineering success requires (i) full qualification and complete panel, (ii) family intervals above1 for AUTO against all three fixed arms, (iii) >=3% point time reduction against the fastest fixed arm, and (iv) each session direction reported, including reversals. The 3% threshold is a usefulness screen, not a power guarantee. A local TTFT gain with no service benefit is reported as such. A winning fixed QB or WB policy can still be the substantive conclusion; do not force AUTO to win.

Report all roots, worst regressions, medians and a descriptive p95 without an SLA claim from32roots. Report actual cache-hit fraction, cache build cost, import traffic, native graph reuse, dispatch classes and mask/join costs where traced. Calibration break-even is C_cal / observed mean service saving only when the saving is positive; include uncertainty and actual observed reuse counts. Do not assume unlimited future reuse or arbitrary fanout.

No outcome-dependent extra rounds. A resource or technical failure remains in its original slot and ledger. Resume unstarted slots after ordinary connection interruptions. A code correction before freeze starts a source-bound engineering epoch. A post-freeze numerical repair requires a new prospective unseen panel and carried-over costs, not a silently rewritten confirmation. The host may repair ordinary build/path/API integration without asking at every step; it may not relax the scientific contract.

## 8. Initial work reservation (per platform)

| Stage | Maximum planned model requests |
|---|---:|
| Development, history and instrumentation controls |192|
| Calibration references24 + qualification72 + timed/warm144 |240|
| Main references64 + candidate heavy/off256 |320|
| Main formal measurements512 + warmups512 |1024|
| Aligned controls: qualification64 + timed/warm96 |160|
| **Planned total** |**1936**|
| Engineering reserve in initial2048-request tranche |112|

At most6 zero-forward admissions and64 standalone operator/trace graph submissions are separately reserved and reported. Profile requests count against the192development slots, not in addition. Mandatory reference-prefix creation within a counted request is included; any separate native seed-building requests count against development/reserve. Before native launch the host must bind finite per-worker timeouts, available disk/RAM/VRAM reserve, native source hashes and process cleanup. This package does not invent those runtime readings. A reasoned prospective budget extension is allowed for genuine engineering or a separately named experiment, never to erase costs or chase an aggregate. No arbitrary overnight deadline is a scientific stop rule.

## 9. Deliverables and claim disposition

Deliver a separate result PR, exact code/runtime/model/input pins, original and all successor source identities, untouched old evidence, census, fixed policy, complete slots and failures, full vectors or authenticated access, CPU reconstruction and restored-download verification. Record packaging verification separately from third-party native replication. Update neither manuscript results nor main automatically. A shared compact source/fixture kit that another machine can build is a required publication deliverable, not merely a source-host path.

Classify the final result as: application benefit over strongest fixed baseline; useful fixed policy but no selector benefit; TTFT-only benefit; compatibility boundary; natural-opportunity absent; or resource/implementation blocked. Each can close the protocol. Only new evidence, not a rewritten headline, changes TPDS prospects.
