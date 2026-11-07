# B570 native resident and target-parallel economics

Executed on the original Arc B570 host from PR189 actual head `03bc44b6f382919e08a8c1aaa198c2dd723b5c8f`, on the independent `codex/b570-economics-results-20261106` branch. The unchanged original Smol R, strong H1/D1, D4 and caller-only controls are retained. All fixed exposed inputs and warmups remain in the result.

This is a finite development result on four already exposed roots, not a new unseen natural confirmation. The clean complete-service pilot determines the continuation decision; separately instrumented, synchronized and heavy mechanism requests do not replace it. No performance slot was dropped, replaced or extended.

The fastest speculative arm is **S_D4**, with 14.588283s measured total versus **L_M** at 9.202151s: **1.585312 times M service**. It loses on every fixed root. Actual compatible target parallelism works, but its observed savings do not pay the draft and all additional online costs. The prescribed development exit is CLOSE_SPECULATION_AND_REPORT; no new natural panel was launched.

## Complete clean service

Each row has eight measured requests and eight immediate same-arm warmups: four fixed exposed roots, two counterbalanced blocks. R below denotes the resident old-width candidate, not the independent original reference producer. SIMPLE and LOCAL use the same repaired binaries and graph reuse policy; their target-only M controls retain original UB128 prefill and ordinary singleton continuation. M keeps the same unused draft weights/context resident and charges its reset.

| Stage | Arm | Measured total s | Warm total s | Total / best M | Proposed | Accepted |
|---|---|---|---|---|---|---|
| resident | R_M | 9.183679 | 8.977247 | 1.000000 | 0 | 0 |
| resident | R_H1 | 19.159790 | 18.979951 | 2.086287 | 578 | 416 |
| resident | R_C4U4 | 16.989755 | 16.703042 | 1.849994 | 578 | 416 |
| resident | R_C4U1 | 19.174658 | 18.946326 | 2.087906 | 578 | 416 |
| parallel | S_M | 9.224182 | 9.056726 | 1.002394 | 0 | 0 |
| parallel | S_H1 | 17.811756 | 17.744267 | 1.935608 | 578 | 416 |
| parallel | S_C4U4 | 14.588283 | 14.565661 | 1.585312 | 578 | 416 |
| parallel | L_M | 9.202151 | 9.091748 | 1.000000 | 0 | 0 |
| parallel | L_H1 | 17.858775 | 17.792458 | 1.940717 | 578 | 416 |
| parallel | L_C4U4 | 14.598564 | 14.530955 | 1.586430 | 578 | 416 |
| parallel | S_C4U1 | 17.810699 | 17.867876 | 1.935493 | 578 | 416 |
| parallel | L_C4U1 | 17.849096 | 17.789559 | 1.939666 | 578 | 416 |

| Draft control, eight method/root checks | Equal resident same-arm frontier | Different from resident H1 frontier | Maximum absolute F32 difference from H1 |
|---|---|---|---|
| H1 | 8 | 0 | 0.00000000 |
| C4U1 | 8 | 0 | 0.00000000 |
| C4U4 | 8 | 8 | 0.56567955 |

Service includes reset and synchronization, original prefill, sampling, draft/verify/trim, phase binding/reservation, state maintenance and response-file close. Fresh process/library/backend/model/context provisioning is outside service and separately charged. Heavy KV capture, physical tracing and reference replay are absent from these clean requests. The resident and parallel pilots are separate stage windows; their cross-stage differences are descriptive, not a randomized lifecycle/parallel causal estimate.

## Exposed gate

| Candidate | Best fixed M / D total | Equal-root geometric ratio | Roots favoring D | Decision |
|---|---|---|---|---|
| S_D1 | 0.516634 | 0.533855 | 0 | CLOSE_SPECULATION_AND_REPORT |
| S_D4 | 0.630791 | 0.642721 | 0 | CLOSE_SPECULATION_AND_REPORT |
| L_D1 | 0.515273 | 0.532848 | 0 | CLOSE_SPECULATION_AND_REPORT |
| L_D4 | 0.630346 | 0.642250 | 0 | CLOSE_SPECULATION_AND_REPORT |
| S_C4U1 | 0.516664 | 0.533930 | 0 | CLOSE_SPECULATION_AND_REPORT |
| L_C4U1 | 0.515553 | 0.532540 | 0 | CLOSE_SPECULATION_AND_REPORT |

All root-specific totals and directions are retained in `evidence/DEVELOPMENT_GATE.json`. This gate is not a significance test. If no candidate has a complete-service opportunity, the protocol closes D-PROFIT without adding roots, sessions or a new k/width/cache/overlap sweep. A fresh target-only S_M/L_M panel would exercise unchanged original prefill and singleton ordinary continuation here; the known q2/q4/q32 mechanism evidence alone is not a new natural target-only capability beyond the earlier target work. No blind output or natural-panel performance sample was started.

## All exposed comparisons

Numerator service / denominator service; above one favors the denominator. These are all 28 comparisons of eight retained development arms, including the caller-only controls. Four exposed roots do not support an unseen-population claim. No confirmation intervals are attached to this development gate.

| Numerator / denominator | Total ratio | Equal-root geometric ratio | Mean paired difference s |
|---|---|---|---|
| S_M / S_D1 | 0.517870 | 0.535141 | -1.073447 |
| S_M / S_D4 | 0.632301 | 0.644269 | -0.670513 |
| S_M / L_M | 1.002394 | 1.002409 | 0.002754 |
| S_M / L_D1 | 0.516507 | 0.534132 | -1.079324 |
| S_M / L_D4 | 0.631855 | 0.643798 | -0.671798 |
| S_M / S_C4U1 | 0.517901 | 0.535216 | -1.073315 |
| S_M / L_C4U1 | 0.516787 | 0.533823 | -1.078114 |
| S_D1 / S_D4 | 1.220963 | 1.203925 | 0.402934 |
| S_D1 / L_M | 1.935608 | 1.873169 | 1.076201 |
| S_D1 / L_D1 | 0.997367 | 0.998115 | -0.005877 |
| S_D1 / L_D4 | 1.220103 | 1.203044 | 0.401649 |
| S_D1 / S_C4U1 | 1.000059 | 1.000141 | 0.000132 |
| S_D1 / L_C4U1 | 0.997908 | 0.997537 | -0.004668 |
| S_D4 / L_M | 1.585312 | 1.555886 | 0.673266 |
| S_D4 / L_D1 | 0.816869 | 0.829051 | -0.408812 |
| S_D4 / L_D4 | 0.999296 | 0.999268 | -0.001285 |
| S_D4 / S_C4U1 | 0.819074 | 0.830734 | -0.402802 |
| S_D4 / L_C4U1 | 0.817312 | 0.828571 | -0.407602 |
| L_M / L_D1 | 0.515273 | 0.532848 | -1.082078 |
| L_M / L_D4 | 0.630346 | 0.642250 | -0.674552 |
| L_M / S_C4U1 | 0.516664 | 0.533930 | -1.076068 |
| L_M / L_C4U1 | 0.515553 | 0.532540 | -1.080868 |
| L_D1 / L_D4 | 1.223324 | 1.205316 | 0.407526 |
| L_D1 / S_C4U1 | 1.002699 | 1.002031 | 0.006010 |
| L_D1 / L_C4U1 | 1.000542 | 0.999422 | 0.001210 |
| L_D4 / S_C4U1 | 0.819651 | 0.831342 | -0.401517 |
| L_D4 / L_C4U1 | 0.817888 | 0.829178 | -0.406316 |
| S_C4U1 / L_C4U1 | 0.997849 | 0.997396 | -0.004800 |

## Missing online costs and timer perturbation

A0 rechecks all 864 PR187 slots and metric hashes with zero model forwards; original totals are unchanged. Old generation clocks include transition and are not relabelled decoder time. Missing historical fine-grained clocks remain null.

| A1 arm | Mode0 total s, n=8 | Mode1 total s, n=8 | Mode1 / mode0 | Mode2 / matched mode0 |
|---|---|---|---|---|
| M | 9.106493 | 9.128010 | 1.002363 | 1.010673 |
| H1 | 90.064830 | 90.074184 | 1.000104 | 1.002475 |
| C4U4 | 87.760821 | 87.666933 | 0.998930 | 1.003963 |

A1 completes the prespecified 108 requests: 54 measurements and 54 warmups, with qualification charged separately. Mode1 preserves the ordering with small observed aggregate perturbation; no timer-overhead subtraction or extra timing was used. Mode2 adds boundary drains and has only the two fixed diagnostic roots. Host envelopes, including blocking envelopes, are not measured device-kernel times. Draft continuation is one actual combined native call; its separate sync/proposal times remain null.

| A1 mode1 exclusive phase s, n=8 | M | H1 | D4 |
|---|---|---|---|
| target_prefill | 0.748799 | 0.539541 | 0.537767 |
| target_ordinary | 0.721613 | 0.000000 | 0.000000 |
| target_verify | 0.000000 | 5.448305 | 5.446049 |
| draft_prefill | 0.000000 | 6.121858 | 3.803451 |
| draft_continuation_unsplit | 0.000000 | 0.987616 | 1.010417 |
| export_source | 0.000000 | 23.626684 | 23.548727 |
| export_destination | 0.000000 | 23.576270 | 23.531498 |
| export_source_after | 0.000000 | 23.523135 | 23.499578 |
| import_state | 0.000000 | 0.129177 | 0.130921 |
| context_create | 0.000000 | 0.158432 | 0.161040 |
| context_destroy | 0.000000 | 0.016997 | 0.015114 |
| state_checks | 0.000000 | 0.186235 | 0.196216 |
| sampler_clone | 0.000000 | 0.000563 | 0.000533 |
| transition | 0.000000 | 0.061197 | 0.060610 |
| phase_bind | 0.000000 | 0.000000 | 0.000000 |

The transition row is its self time, not the inclusive parent added again. Every speculative mode1/2 request observes three exports, one import, one context creation/destruction, one full-comparison span and one sampler clone. Resident and parallel diagnostics observe zero calls for these migration operations; no cost is removed by an estimated byte/PCIe subtraction. This reuse of in-place phase binding follows PR64/82 and is not a new discovery or profit guarantee.

## Physical target work and complete cost identity

Each physical-work row below contains its separate warm and measured mechanism request. A micrograph is counted once after successful process_ubatch graph_compute. Layer embedding callbacks and logical verification counts are not treated as physical forwards. Head, occupied rows, extent, output rows, successful graph reuse/rebuild and actual target trim events are preserved in the raw logs and decision receipt.

| Stage | Arm | Logical verifies | Occupied continuation graphs | Continuation rows | Width: count | Reused target graphs, all phases | Trim span reductions |
|---|---|---|---|---|---|---|---|
| resident | R_M | 0 | 992 | 992 | {"1": 992} | 984 | 0 |
| resident | R_H1 | 578 | 1156 | 1156 | {"1": 1156} | 1148 | 0 |
| resident | R_C4U4 | 578 | 1156 | 1156 | {"1": 1156} | 1148 | 0 |
| resident | R_C4U1 | 578 | 1156 | 1156 | {"1": 1156} | 1148 | 0 |
| parallel | S_M | 0 | 992 | 992 | {"1": 992} | 984 | 0 |
| parallel | S_H1 | 578 | 582 | 1156 | {"1": 8, "2": 574} | 566 | 0 |
| parallel | S_C4U4 | 578 | 582 | 1156 | {"1": 8, "2": 574} | 566 | 0 |
| parallel | S_C4U1 | 578 | 582 | 1156 | {"1": 8, "2": 574} | 566 | 0 |
| parallel | L_M | 0 | 992 | 992 | {"1": 992} | 984 | 0 |
| parallel | L_H1 | 578 | 578 | 1156 | {"2": 578} | 566 | 0 |
| parallel | L_C4U4 | 578 | 578 | 1156 | {"2": 578} | 566 | 0 |
| parallel | L_C4U1 | 578 | 578 | 1156 | {"2": 578} | 566 | 0 |

SIMPLE splits the whole graph at the actual dense physical 256-token extent boundary inside one logical decode, preserving every requested output row. LOCAL retains wide compatible projection/FFN work and splits the incompatible attention groups locally. Both preserve original phase0 UB128 producer arithmetic; continuation enables the existing PR169 F32 activation/p021 mapping only where that reference phase and geometry require it. No model-name/input-ID rule or global LOCAL prefill cap4 is introduced. Dispatch logs describe actual selected paths/command recording, not an invented count of every executed device dispatch.

The following diagnostic identity is descriptive: M_service − D_service = target_saved − draft_added − other_added. Mode1 and mode2 have different execution windows and are shown separately. Other includes uninstrumented work/waits, phase and state maintenance, sampling and response completion; it is not discarded.

| Mode | Arm | Fixed roots | Target saved s | Draft added s | Other added s | Full service saved s |
|---|---|---|---|---|---|---|
| 1 | S_H1 | 4 | -0.310793 | 4.572332 | -0.623512 | -4.259613 |
| 1 | S_C4U4 | 4 | -0.322726 | 2.968241 | -0.620265 | -2.670702 |
| 1 | S_C4U1 | 4 | -0.325239 | 4.554729 | -0.623067 | -4.256900 |
| 1 | L_H1 | 4 | -0.334579 | 4.592878 | -0.602466 | -4.324990 |
| 1 | L_C4U4 | 4 | -0.332200 | 3.014778 | -0.615118 | -2.731861 |
| 1 | L_C4U1 | 4 | -0.332138 | 4.593604 | -0.637814 | -4.287928 |
| 2 | S_H1 | 2 | 0.486019 | 2.905831 | 0.200134 | -2.619946 |
| 2 | S_C4U4 | 2 | 0.466681 | 1.923330 | 0.210582 | -1.667231 |
| 2 | L_H1 | 2 | 0.461518 | 2.901607 | 0.212367 | -2.652456 |
| 2 | L_C4U4 | 2 | 0.452655 | 1.904810 | 0.208687 | -1.660842 |

## Native contract and mechanisms

The read-only reconstruction rechecks 13046 complete 49,152-element F32 conditional vectors and 7575 committed active KV/frontier states against the independent original R. These repeated checks are not independent performance samples. All target vectors, including actual off-greedy proposal prefixes, committed emitted prefixes, positioned pending suffixes, endpoints and heavy/off final states match. Original R is unchanged: whole prompt/512 outer chunks with UB128 first, scalar forced continuation only after that producer. Candidate values are never supplied to R.

All 32 SIMPLE/LOCAL natural-development qualification cells and 16 resident cells pass, alongside the 36 A1 arm/mode cells. The four fixed prompts have 234, 147, 833 and 508 tokens; the last retains native EOG at 116 output tokens while the other three reach cap128. No padding, truncation or alignment-based input selection is used.

Twenty-six separately labelled known-token cases cover q2/q4/q32 at actual head254/255/256, q32+tail1/2/3 and rollback followed by a two-row replay. All required vectors and active KV/frontiers match R. Twelve cap1 arm/method cases exercise the real ending loop. Separate k3 protocol requests exercise first and later rejection, rollback and post-rollback continuation; their timing is not used as k1 economic evidence. Reset, accept-all bonus, natural EOG and cap128 remain covered by the fixed natural-development trajectories.

The used known-probe02 immutable source reports initial known tokens but omits the two post-rollback replay rows from that one metadata field. Actual caller_rows, requests, occupied micrographs and conservative reservations include both replay rows. The report derives the complete count from those actual counters. A separately retained known-probe03 build adds explicit replay/decoded-row metadata; it was not used to retime or replace any probe.

## Costs, retained failures and limits

The new immutable ledger reserves 1058 requests / 1114516 row upper bounds / 0 operator replays against 3072 / 4,000,000 / 2048 ceilings. The old 1706-request / 1,804,796-row ledger is unchanged. Reservations include warmups, failures and independent forced R; no refunds are taken. New native charged wall is 7708.624s and owned-worker wall is 7961.834s. These clocks overlap and are not added.

| Stage | Reserved requests | Reserved rows | Native s | Owned-worker s | Provisioning-to-ready s |
|---|---|---|---|---|---|
| A1-qualification | 168 | 185052 | 2513.703 | 2553.662 | 123.887; 0 unmetered |
| A1-timing | 108 | 121022 | 937.969 | 961.186 | 78.037; 0 unmetered |
| cap1-contract | 48 | 39624 | 205.230 | 216.084 | 34.950; 0 unmetered |
| original-R-forced | 30 | 8970 | 65.137 | 78.142 | 37.465; 0 unmetered |
| known-mechanism | 52 | 18824 | 461.047 | 472.904 | 38.395; 0 unmetered |
| parallel-caller | 32 | 43936 | 99.750 | 106.703 | 23.657; 0 unmetered |
| parallel-diagnostic | 64 | 74840 | 175.107 | 189.345 | 47.014; 0 unmetered |
| parallel-mechanism02 | 64 | 74840 | 290.670 | 305.311 | 46.775; 0 unmetered |
| parallel-pilot | 96 | 105744 | 251.267 | 272.328 | 70.893; 0 unmetered |
| parallel-qual | 128 | 149680 | 1351.591 | 1381.922 | 94.468; 0 unmetered |
| parallel-synchronized | 24 | 30556 | 68.112 | 73.566 | 18.610; 0 unmetered |
| k3-protocol | 8 | 11936 | 112.249 | 114.110 | 5.859; 0 unmetered |
| resident-caller | 16 | 21968 | 52.204 | 55.732 | 11.687; 0 unmetered |
| resident-diagnostic | 34 | 38144 | 91.998 | 99.123 | 23.218; 1 unmetered |
| resident-mechanism02 | 32 | 37420 | 144.031 | 151.484 | 23.095; 0 unmetered |
| resident-pilot | 48 | 52872 | 132.298 | 142.887 | 34.875; 0 unmetered |
| resident-qual | 64 | 74840 | 654.341 | 669.225 | 46.265; 0 unmetered |
| resident-synchronized | 12 | 15278 | 34.906 | 37.486 | 8.719; 0 unmetered |
| original-R-resource-observer | 30 | 8970 | 67.014 | 80.634 | 40.692; 0 unmetered |

Provisioning includes process/DLL/backend/model/context setup observed at 100ms resolution, not pure weight loading. Full driver CPU/wall, build/configure/validation and streamed-storage receipts are retained separately. Driver clocks include child and offline checks; storage overlaps diagnostic native work. Some initial unmetered engineering CPU preparation has no complete wall estimate and remains null. These inclusive costs are not added to native service a second time.

Every native worker retains 900s wall / 180s request-progress bounds, 16GiB Job memory, 20GiB disk and 2GiB RAM floors. Candidate/frozen-control workers observe the actual signed device reserve of at least 128MiB. Loaded numerical/common DLL hashes and suspended-before-Job assignment are verified. Real parent-failure and timeout descendant-cleanup tests leave zero active processes. No system-wide process killing is used.

The initial A0 source-anchor failure, unused engineering build epochs and the prelaunch environment allow-list failure remain retained. The latter reserved two requests, started zero native forwards, and keeps that reservation. The private supervisor adapter admits only four explicit economics flags with value1; base supervisor and resource/cleanup behavior are pinned and unchanged. The repaired mechanism jobs use distinct names. No new native numerical failure was erased. Earlier PR187 numerical/capture failures and all five Qwen zero-forward capacity failures remain unchanged.

The first portable build proof stopped on an overbroad old-path guard after both private cores had compiled. The guard mistook a valid new output directory below the evidence root for the old fixed library path. A distinct frontend attempt repairs only that path check and reuses completed core compiles after source, log and library hash checks. The failed script/logs and all build costs remain retained; this repair adds zero model requests and replaces no timing.

The first full CPU reconstruction passed the vector/state checks and then stopped on an aggregation assertion: sequential float += and Python 3.12 builtin sum differed by 1.78e-15 seconds on two totals. The reader now uses the same builtin summation as the recorded decision. Raw per-request values and hashes are unchanged, the failed reconstruction and its cost are retained, and a separately named full reconstruction verifies the correction. That reader-only correction adds no model request or performance session.

The next CPU audit exposed missing signed-budget logs in the unchanged original forced R. Those 30 original observations remain null. A separate resource-only observer copy adds the existing signed capacity checks after original initialization and after each original forced request; removing those insertions recovers the original producer text exactly under universal-newline decoding. Replaying every same token tape observes at least 7673688064 bytes of signed device reserve and byte-matches all 1980 original conditional vectors and 0 requested states. The original R executable, numerical DLLs, producer and old observations remain unchanged. These separately charged reference-qualification requests add no performance session or input. The first observer build's Windows min-macro conflict and the following count-guard failure are also retained as zero-model engineering failures.

Optional Qwen transfer was not attempted in this bounded Smol economics result. It is not admitted by the Smol result or by deleting a duplicate context in a capacity estimate. Any later Qwen attempt still requires its own original PR165 R and actual signed capacity admission; the historical negative remaining budget remains a failure. No RTX/arXiv change, merge, model download or rental is performed.

## Reproduction

See `REPRODUCE.md` for the authenticated new evidence release, the explicit immutable PR187 dependency, read-only restoration, portable source rebuild and exact native request/runtime identities. No model weights are needed to reconstruct these tables and contract checks. Exact pinned GGUF files remain separate inputs for native reruns. Fresh authenticated download verification is same-host evidence, not external native replication.
