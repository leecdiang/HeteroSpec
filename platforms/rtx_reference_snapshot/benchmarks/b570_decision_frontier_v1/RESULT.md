# B570 decision-frontier v1 — incomplete native collection, completed CPU review

The new capture study stopped after its first counts attempt because the registered donor registry keyed KV by task|state and omitted recipient. The B entry overwrote A. The planned EMPTY B->A request imported B KV instead of A KV. This is an adapter integration failure, not a scientific EMPTY intervention result. No retry, registry repair, heavy request or subset-stage request was executed. The failure and all 167 unstarted slots are retained.

Fixed evidence: PR103 result b46415f2725d7c06e093a6cd2b2d261b61925dc6, registration dd33b24abebc335d39f3b63b4e7beff86bdcf934, PR101 baseline 26706c9fb4818ec3465e45acea029c4ab88a390f. New F0 644aa5c14686d88c913bce32f291c8c2ac6a0be5 was authenticated byte-for-byte before native launch. PR105 remains Draft. The frozen code and flawed DONORS body are unchanged.

## Raw audit and execution

A distinct fresh PR103 restore verified the final ZIP SHA256 2e6114e9a3019b71d7e7a1ac55dd483ee8191ce6fcb99310fcbeda588992b0b1 and all 2,561 members. Independent parsing tied REQUEST, RESULT, trace, restored input hashes, actual runtime identity, PID/lifecycle and ledger to every one of 192 outputs. PR101 endpoint references were recomputed from 40 actual P2 raw records, bound to the fixed Git indexes and archive manifest. The resolver mapping records actual fresh reads and rejects fallback to the original run.

32 historical controls pass. All 80 subset repeat coordinates agree across their two original processes. Among 160 subset requests: B=30, C=54, D=76; these are request counts, not independent input success rates. All 76 subset D requests changed bytes; structural subset nulls=0. Donor->recipient notation fixes recipient initial logits.

The /1248 B->A L0 quartet is EMPTY D / K_layer0 D / V_layer0 B / KV_layer0 D in both repeats, with changed bytes 0 / 113464 / 122089 / 235553. B is historical full-cross following; D matches recipient. No necessity/minimality follows.

New execution: 1 attempted slot, 1 process creation, 1 native request, 127 target decode calls / successful micrographs / rows, 128 native sampling calls, 0 target prefill calls, 12.438 cumulative owned seconds, 0 probes/warmups/retries. Native exit code=0; receipt status=FAILED because imported KV SHA aba498c2... differs from planned 80b83531.... Recipient initial logits SHA a8833600... remained fixed; t0=1271 is valid. The actual wrong-input output matches the historical full-cross reference. Minimum memory headroom was 2,269,863,936 bytes. Stop was the restore-input gate, not a budget limit; 168 / 21600 seconds / 4 GiB limits were not exhausted. Counts is validated as memory.json and aggregate counters, not full trace geometry.

The collision affects 28 planned cells, discovered by CPU forensic assertions. This exposes a missing prelaunch registry-to-plan consistency check in the adapter. Twenty-four prelaunch CPU tests passed but did not cover this assembly collision; those passes did not establish native qualification. The first failed CPU path-assumption attempt and the failed synthetic fixture attempt are also retained in development logs.

## F16 retained-state distances

K is token-major [N,8,128]; FA-off V is feature-major [1024,N], exposed logically as [N,8,128]. K byte strides are (2048,256,2), V strides (2,256*N,2*N). Source state_write_data/cpy_k/cpy_v and hash-bound native stderr establish this geometry. Immutable metadata is checked separately. Selected bytes and changed bytes are different quantities. V_layer0 selects 1/64 of all K/V value bytes, excluding metadata; this is neither an error-size fraction nor information/causal contribution.

Full-state comparison below is B donor vs A reference. FP64 calculations decode stored F16; all values are finite. Relative L2 divides by the actual recipient norm; zero reference norm gives N/A without epsilon. Both directions and all seven selectors, full ordered-ULP histograms, zero/sign changes and role/layer/position/head/channel profiles are in evidence/STATE_DISTANCE.json. Ordered ULP uses sign-aware ordering and reports signed zeros separately; it is not a causal-importance metric.

| Task | Changed bytes | Changed F16 elements | Max absolute | RMS absolute | L2 relative (A reference) | Ordered ULP max |
|---|---:|---:|---:|---:|---:|---:|
| 1248 | 11382660 | 10119591 | 0.255859375 | 0.008327455 | 0.006488689 | 23616 |
| 831 | 9587243 | 8428708 | 1.33258056640625 | 0.013095576 | 0.010452955 | 28484 |
| 1011 | 13535185 | 11929239 | 0.265625 | 0.008894085 | 0.006887112 | 23325 |
| 1249 | 11605004 | 10259709 | 0.24609375 | 0.008620512 | 0.006748138 | 23325 |

The /1011 and /1249 A/B state differences are nonzero and comparable in relative/RMS scale to /1248. Endpoint stability therefore does not establish state equality or uniquely small state error.

## Common prefixes, availability and score contrasts

Each panel frontier is computed from all four full native token sequences. All arms share [0,t*) and every compared logit snapshot is aligned to its actual naturally_committed_prefix_ids and consumed logical position. t0 is separately pinned recipient initial logits consumed by the native sampler, never a new forward or missing boundary_snapshot96(0). No post-divergence natural text is compared as the same input. No arm-specific frontier is substituted for the panel frontier.

| Task | Recipient | Panel | Frontier/status | Prespecified positions |
|---|---|---|---|---|
| 1248 | A | L0 | 47 | 1,46,47 |
| 1248 | A | POSITION | 47 | 1,46,47 |
| 831 | A | L0 | 40 | 1,39,40 |
| 831 | A | POSITION | 81 | 1,80,81 |
| 831 | B | L0 | 81 | 1,80,81 |
| 831 | B | POSITION | 81 | 1,80,81 |
| 1011 | A | L0 | 10 | 1,9,10 |
| 1011 | A | POSITION | 10 | 1,9,10 |
| 1249 | A | L0 | RIGHT_CENSORED_AT_128 | 1,31,63,95,127 |
| 1249 | A | POSITION | RIGHT_CENSORED_AT_128 | 1,31,63,95,127 |

/1248 recipient B also has t*=47 in both panels. /1011 recipient B also has t*=10 in both panels. /1249 recipient B also remains RIGHT_CENSORED_AT_128. Legacy KV_prefix128 covers positions [0,min(128,N)); legacy KV_tail128 covers its complement [min(128,N),N), not the last 128 tokens. This exact historical definition is retained; for /831 N=133 the tail contains five positions.

Old availability: 44/112 planned repeat-level four-cell comparisons are complete; 68 are incomplete. Full-vector gaps are 272 panel entries or 240 unique arm×repeat×position coordinates. phase96 top2/hash alone never substitutes for a full vector. /831 A L0 at t=39/40 and /1011 at t=9/10 remain missing; /1249 later positions 31/63/95/127 remain missing. New-batch complete four-cell comparisons=0. Historical and new repeats are not mixed.

Below are all available frontier contrasts plus /1011 and /1249 t=1 contrasts. L0 first/second=K/V; POSITION first/second=prefix/tail. For a differing panel, r/u is fixed from that panel's frontier and shared at earlier sampled positions; for /1249 r/u is EMPTY top1/top2 at t=1, stable ID tie-break. Both original repeats have the same displayed values. FP32 full vectors are promoted to FP64; no epsilon declares a residual zero. All 44 detailed comparisons, scores/ranks/argmax, hashes, certificate values and both repeats are in FRONTIER_ANALYSIS.json/csv; every FP64 vocabulary residual is preserved in the private archive.

| Task | Donor->recipient | Panel | t | delta first | delta second | I | Vector I Linf | EMPTY top1 margin |
|---|---|---|---:|---:|---:|---:|---:|---:|
| 1248 | B->A | L0 | 47 | 0.059743881 | 0.088148117 | -0.135864258 | 0.347980499 | 0.066514969 |
| 1248 | B->A | POSITION | 47 | 0.078002930 | 0.095777512 | -0.096559525 | 0.290860951 | 0.066514969 |
| 1248 | A->B | L0 | 47 | 0.025909424 | 0.033445358 | -0.019031525 | 0.236373663 | 0.010705948 |
| 1248 | A->B | POSITION | 47 | -0.018556595 | -0.000782013 | 0.096559525 | 0.290860951 | 0.010705948 |
| 831 | B->A | POSITION | 81 | -0.095176697 | -0.062551498 | 0.238718033 | 0.317362785 | 0.013084412 |
| 831 | A->B | L0 | 81 | 0.118263245 | 0.172574997 | -0.049446106 | 0.264456511 | 0.067905426 |
| 831 | A->B | POSITION | 81 | 0.143541336 | 0.176166534 | -0.238718033 | 0.317362785 | 0.067905426 |
| 1011 | B->A | L0 | 1 | -0.044275284 | 0.028943062 | -0.046950340 | 0.238487482 | 0.561777115 |
| 1011 | B->A | POSITION | 1 | 0.014308929 | 0.006087303 | -0.056207657 | 0.246789455 | 0.561777115 |
| 1011 | A->B | L0 | 1 | 0.005011559 | 0.022273064 | -0.008228302 | 0.257912874 | 0.549312592 |
| 1011 | A->B | POSITION | 1 | 0.041898727 | 0.050120354 | -0.056207657 | 0.246789455 | 0.549312592 |
| 1249 | B->A | L0 | 1 | -0.014455795 | -0.038658142 | 0.048860550 | 0.227325201 | 0.959617615 |
| 1249 | B->A | POSITION | 1 | -0.007623672 | -0.016855240 | 0.047288895 | 0.246829033 | 0.959617615 |
| 1249 | A->B | L0 | 1 | -0.048194885 | -0.079702377 | 0.110851288 | 0.251505136 | 0.936807632 |
| 1249 | A->B | POSITION | 1 | -0.039665222 | -0.030433655 | 0.047288895 | 0.246829033 | 0.936807632 |

All 22 available position×panel repeat pairs have bitwise equal full FP32 arm vectors. This only describes available historical captures. It makes no claim about uncollected new repeats. No population confidence interval is formed.

At /1248 B->A t=47, r=220/u=832, actual argmax across EMPTY/K/V/KV is 220/220/832/220; d is -0.066514969/-0.006771088/+0.021633148/-0.054487228. Thus a V-only crossing and joint noncrossing coexist with measured negative score residual. The POSITION argmax is 220/832/832/832. In A->B, L0 argmax is 832/220/220/220 while POSITION is 832/832/832/220. These are direction-specific observations. /831 B->A POSITION t=81 is 1521/1521/1521/1855; /831 A->B at t=81 has 1855/1521/1521/1521 in both panels. A residual is net score nonadditivity under this controlled quartet; it neither identifies one nonlinear operator nor estimates complete natural mediation. The synthetic additive-margin/nonmonotone-endpoint test demonstrates why endpoint labels alone are insufficient.

## /1011 versus /1249 and limits

/1011 historical full A/B cross is endpoint-stable, but mixed-subset arms first diverge at t=10 in both directions/panels. At t=1 all seven states choose token 11886. EMPTY top1 margins are 0.561777115 (A) / 0.549312592 (B); the maximum per-arm epsilon Linf is 0.207827211. Every observed t=1 quartet arm satisfies m>2*epsilon, an observed-position sufficient certificate. The pair used for d at t=1 remains the frozen t=10 pair 2860/3392; actual token 11886 is a third candidate and ranks/argmax are explicitly checked. Missing t=9/10 full logits prevent quantifying the eventual crossing or its score residual.

/1249 all seven arms share the cap128 endpoint in both directions; no claim of indefinite stability is made. At t=1 all choose 1505. EMPTY margins are 0.959617615 (A) / 0.936807632 (B); maximum per-arm epsilon is 0.194167793. Nonzero score effects and vector residuals coexist with all t=1 certificate passes. Missing later descriptive captures prevent a whole-sequence margin account. The converse of m>2*epsilon is false, and the certificate is not a runtime algorithm or new theorem.

Supported: PR103 sufficient manipulated retained-state subsets can be tied to exact native endpoints and, where available, actual full-vector same-prefix score changes. Direction-specific nonmonotonic endpoints can coexist with measured score nonadditivity. Stable endpoints need not imply state/logit equality. These increase the auditability and limited local evidence for “B570 reveals retained-state boundary limiting local repair transfer.”

Still indistinguishable: which downstream operations generate the residual; natural versus off-distribution hybrid paths; contribution of unmeasured positions/layers; complete projection mediation; necessary/minimal/unique state subset; V being globally most important; longer-horizon stability; general repair transfer or population success. The failed new collection leaves the registered frontier study incomplete. No paper, PR102/PR104, numerical runtime, model or historical archive was edited; no RTX control, release, merge or publication automation was performed.

## Zero-GPU upstream bridge and future hook feasibility

Twelve actual PR101 P1C heavy raw records (/1248,/831) and 100 K/V FP32 projection/reshape/RoPE payloads were read and hash-bound. V MUL_MAT [1024,W,1,1], nb=(4,4096,4096W,4096W), becomes [128,8,W,1], nb=(4,512,4096,4096W); corresponding FP32 captured payload hashes agree through reshape. K has distinct post-RoPE capture. These captures do not include actual SET_ROWS/F16 cache-write outputs and do not reveal the dispatch pipeline. /1011 and /1249 lack these operator captures. Therefore V0/K0 projection→serialized F16 provenance is NOT_ESTABLISHED; host cast similarity is not GPU byte lineage.

Real prospective source points (implementation/qualification not performed): llama-graph.cpp build_qkv separate V projection at 1717 and K at 1703, reshape at 1732–1734; models/llama.cpp 143–160 exposes returned K/V before K RoPE at 152. cpy_k at llama-kv-cache.cpp 1335/1350 flattens/stores K; cpy_v 1388–1406 reshapes or contiguates V and SET_ROWS writes scalar features via v_idxs. state_write_data 2303–2322 serializes F16 V feature-major. Vulkan source has multiple fusion patterns and F16 set_rows pipelines; the existing observer does not identify the actual chosen shader.

A future registered native-prefill intervention should replace the designated projection tensor with an explicit dependency-bearing node on the same backend, before reshape/consumer views for V and before RoPE for K. Identify by layer/op/tensor and caller position/IDs, not name alone (Kcur repeats at projection/reshape/RoPE). Capture and assert real dtype/ne/nb/view_offset, bind micrograph positions, prevent alias writes into another live tensor, and keep donor input/host storage alive until synchronized completion. A callback after execution is not by itself a safe replacement API; scheduler partitioning, fused consumers and graph allocation/alias lifetimes need qualification in a separately frozen future runtime. Backend uploads/copies and reads need explicit synchronization and completion proof.

Required future own-path sham uses recipient projection through the identical replacement/copy/sync path; observe-off controls keep observer behavior separate; direct boundary-0 KV patch holds other layers fixed, whereas upstream replacement lets attention and later-layer states recompute. Record all resulting KV layers and native initial/continuation logits. Preregister whether recomputed initial logits are natural or recipient-clamped as distinct estimands, without silently equating them. Do not call either a teacher-forced result. Even downstream-recomputed states are not automatically distributed like natural unmodified input. No hook was implemented or executed this round; “QB passed Vulkan” is not established.

Method boundaries only in this new review: [Zhang & Nanda v2](https://arxiv.org/html/2309.16042v2) motivates explicit metric/corruption/window choices; [Vaidyanathan et al. v1](https://arxiv.org/html/2606.27510v1) discusses mediator/bypass interactions and context-dependent estimands, not validation of our KV quartet as a full natural indirect effect; [Grant et al. v5](https://arxiv.org/html/2511.04638v5) shows why behaviorally successful interventions do not establish natural representational provenance. These papers do not verify B570 observations or warrant a first-interaction claim.

## Reproduction and delivery

Frozen prelaunch modules and new F0 remain intact. review_after_stop.py is explicitly post-stop CPU forensic/source review. Raw manifest, local archive and fresh-restore receipt are delivered separately; archive SHA/member verification and CPU reanalysis are local on this host. Remote raw delivery is REMOTE_PENDING; independent-machine recomputation is NOT_PERFORMED. No public raw upload was authorized or performed. The actual ZIP, full FP32 vectors from the separate PR103 ZIP, FP64 residuals and source-code hashes remain accessible through the local private package and explicit external dependencies.

CPU commands: use audit_raw.py --repo --baseline --archive --fresh --output [--restore], state_distance.py --fresh --output, plan_frontier.py --audit --fresh --output, analyze_frontier.py --plan --audit --fresh --out [--new-run], and review_after_stop.py --run --baseline --repo --output. reproduce.py verifies the new ZIP/member manifest, runs fresh-path CPU reanalysis and preserves the separation of the historical and failed new batch.
