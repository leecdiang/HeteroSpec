# B570 PR185 native result and separate Smol confirmation

The original-interface tail3 repair and original-host builds are complete. The Qwen C1024 mandatory-control capacity failure remains a failure. In the separate SmolLM2-1.7B/135M Q8 deployment, all4 development and12 test roots passed all6 native arms, the fixed24-measurement/24-warmup pilot completed, and the frozen432-measurement/432-warmup panel completed without a failed or replaced timing slot.

The best fixed method by total measured service is **M**. The fastest speculative arm is **C4U4**, using **9.354691 times M service**. Physical draft width4 helps relative to the speculative controls here, while complete speculative service remains much slower than M. This finite deployment result does not establish general equivalence or impossibility.

## Complete service

Each arm has72 measurements and72 immediate same-arm warmups. Service includes reset/sync, prefill, sampling/propose/verify/trim, original required transfer/restore/checks, continuation-context destruction and response-file close. Fresh worker/model provisioning is outside service and charged separately. Heavy qualification capture is absent from clean timing. M retains the same unused draft weights/context resident and charges its reset.

| Arm | Measured total (s) | Mean request (s) | Total / M | Warmup total (s) |
|---|---:|---:|---:|---:|
| M | 86.478166 | 1.201086 | 1.000000 | 84.496826 |
| H1 | 832.191137 | 11.558210 | 9.623136 | 834.857056 |
| C1U1 | 832.632691 | 11.564343 | 9.628242 | 834.434006 |
| C4U1 | 831.493408 | 11.548520 | 9.615068 | 835.520573 |
| C4U2 | 839.122671 | 11.654482 | 9.703289 | 843.099760 |
| C4U4 | 808.976532 | 11.235785 | 9.354691 | 811.505224 |

## All15 fixed comparisons

Ratios are numerator service / denominator service; a ratio above1 favors the denominator. Primary intervals use the frozen10000-draw root bootstrap with all6 paired sessions retained and Bonferroni adjustment across15 contrasts. Equal-root geometric ratios are the prespecified sensitivity. Absolute paired differences are seconds per request. Full root/session ratios and individual absolute-difference intervals remain in `evidence/recovery/MAIN_ANALYSIS.json`.

| Numerator / denominator | Total ratio | Primary family95 interval | Equal-root geometric ratio | Mean seconds numerator minus denominator |
|---|---:|---|---:|---:|
| M / H1 | 0.103916 | [0.100850, 0.106052] | 0.103823 | -10.357125 |
| M / C1U1 | 0.103861 | [0.100750, 0.106091] | 0.103770 | -10.363257 |
| M / C4U1 | 0.104003 | [0.101067, 0.106084] | 0.103917 | -10.347434 |
| M / C4U2 | 0.103058 | [0.100450, 0.104810] | 0.103024 | -10.453396 |
| M / C4U4 | 0.106898 | [0.103717, 0.109620] | 0.106771 | -10.034700 |
| H1 / C1U1 | 0.999470 | [0.996859, 1.002293] | 0.999486 | -0.006133 |
| H1 / C4U1 | 1.000839 | [0.998249, 1.003290] | 1.000908 | 0.009691 |
| H1 / C4U2 | 0.991740 | [0.979730, 0.999977] | 0.992300 | -0.096271 |
| H1 / C4U4 | 1.028696 | [1.020728, 1.035037] | 1.028391 | 0.322425 |
| C1U1 / C4U1 | 1.001370 | [0.998531, 1.004221] | 1.001424 | 0.015823 |
| C1U1 / C4U2 | 0.992266 | [0.980608, 1.000819] | 0.992811 | -0.090139 |
| C1U1 / C4U4 | 1.029242 | [1.021808, 1.035898] | 1.028920 | 0.328558 |
| C4U1 / C4U2 | 0.990908 | [0.980141, 0.998090] | 0.991400 | -0.105962 |
| C4U1 / C4U4 | 1.027834 | [1.018693, 1.035109] | 1.027457 | 0.312734 |
| C4U2 / C4U4 | 1.037265 | [1.021711, 1.055326] | 1.036370 | 0.418696 |

Intervals covering1 do not establish equivalence. The statistical sample is12 independent test roots, not the count of vectors, states, tokens, sessions or requests. No new AUTO was fitted and PR175 AUTO null results remain unchanged.

## Actual trained-model qualification

All target values use unchanged original numerical DLLs. Autonomous unchanged original R is repeated and stable on each root. An independently produced scalar original-R forced-prefix bank supplies complete49152-element F32 vectors and active KV/frontier at actual candidate prefixes. Candidate values are never supplied to R. Heavy/clean final state agrees; every committed state is an emitted greedy prefix, including correctly positioned terminal tokens still unmaterialized in KV. Historical full KV is not retroactively claimed.

| Test index | Original prompt tokens | Output tokens | Natural stop | Full vector comparisons across6 arms | Committed-state comparisons across6 arms |
|---:|---:|---:|---|---:|---:|
| 0 | 154 | 128 | CAP128 | 923 | 528 |
| 1 | 833 | 128 | CAP128 | 813 | 473 |
| 2 | 555 | 128 | CAP128 | 823 | 478 |
| 3 | 331 | 128 | CAP128 | 853 | 493 |
| 4 | 346 | 128 | CAP128 | 843 | 488 |
| 5 | 446 | 128 | CAP128 | 883 | 508 |
| 6 | 748 | 128 | CAP128 | 933 | 533 |
| 7 | 188 | 128 | CAP128 | 839 | 486 |
| 8 | 508 | 116 | EOG | 811 | 466 |
| 9 | 276 | 128 | CAP128 | 923 | 528 |
| 10 | 484 | 128 | CAP128 | 933 | 533 |
| 11 | 531 | 128 | CAP128 | 863 | 498 |

All10440 test conditional vectors and6012 committed states match. These are repeated finite checks across six methods, not additional independent roots. Long inputs, natural EOG and tails congruent to3 modulo4 were retained without truncation, padding, input replacement or outcome filtering.

The original prefill interface is exercised by8192 verbatim-interface cases, alongside8199 helper checks; the original width3 rejection is reproduced and q4 tails now use2+1. All77 Python tests pass normally and under `-O`; native execution/auditing itself rejects optimized Python. The historical Smol bridge separately checks25 full vectors/13 states, with the original target R executable unchanged. The old native score mismatch and heavy-capture deadline failure remain failures.

## Physical intervention

H1 retains the stronger inherited whole-prompt draft caller with original512 outer chunks and physical UB1. C1U1 uses caller1; C4U1/2/4 use caller up to4, tail3 as2+1, and actual physical UB1/2/4. Only the final prompt output is requested. Subsequent draft sync/propose remains singleton. Scheduler embedding columns are actual graph-shape observations and make no new kernel-identity claim.

| Draft arm | Observed caller widths | Observed embedding columns | Roots with draft F32 frontier different from H1 | Maximum absolute draft difference |
|---|---|---|---:|---:|
| H1 | 19,43,154,188,236,276,321,331,346,446,484,508,512 | 1 | 0/12 | 0 |
| C1U1 | 1 | 1 | 0/12 | 0 |
| C4U1 | 1,2,4 | 1 | 0/12 | 0 |
| C4U2 | 1,2,4 | 1,2 | 12/12 | 0.50850296 |
| C4U4 | 1,2,4 | 1,2,4 | 12/12 | 0.50850296 |

Ordinary physical width may alter draft logits, proposals and acceptance. The target trajectory is independently qualified. This is a separate historically referenced Smol runtime, not Qwen admission or a CUDA/Vulkan speed ranking.

## Complete native costs and limits

The cumulative immutable ledger reserves1706 model requests,1804796 decoded rows and0 operator replays against unchanged ceilings6144/12000000/2048. These reservations include failed, warm, teacher-forced and measured requests; the ledger was never reset. All5 Qwen zero-forward failures remain retained. Total native charged wall is18399.352s; owned-worker wall is18926.340s. These clocks overlap and are not added.

| Stage | Reserved requests | Reserved rows | Native charged (s) | Owned worker (s) | Observed provisioning-to-ready (s) |
|---|---:|---:|---:|---:|---:|
| qwen-zero-forward | 0 | 0 | 42.358 | 45.045 | 0.000; 5 units unmetered |
| offline-development-qualification | 211 | 139430 | 2339.138 | 2417.322 | 129.239; 65 units unmetered |
| confirmation | 864 | 1099872 | 9289.498 | 9505.890 | 676.041 |
| pilot | 48 | 47178 | 507.170 | 519.187 | 37.372 |
| offline-test-qualification | 583 | 518316 | 6221.188 | 6438.896 | 608.023 |

Provisioning observations include process/library/backend/model/context setup with100ms polling resolution; they are not pure weight-load measurements. Older units lacking a separate ready clock are counted explicitly in `COSTS.json`. Each native worker has900s wall,180s request-progress,16GiB Job memory,20GiB disk reserve,2GiB RAM reserve and128MiB signed device reserve. Suspended-before-Job assignment, kill-on-close and zero-active-process cleanup are verified, including real parent-failure/timeout descendants.

Inclusive coordinator/phase clocks and streamed-storage clocks overlap native work and are disclosed without adding them a second time. Initial v1 delivery and every failed epoch remain retained. Some CPU preparation, early packing and final mechanism/boundary aggregation were not separately wall-metered; no complete engineering-time total is claimed. Later delivery actions have separate actual wall receipts.

## Provenance and reconstruction

The branch starts at PR185 actual head `8befecc2484d749085ed95fca064b6acc42e7b1d`. Execution source `6e348b07162f3c3e9da4f8a749c4f46f5778e167` was frozen and published/read back before any test output. Frozen data include all6423 natural source paths, native tokenization/rendering, exact exposure exclusions and the unchanged sixteen selected roots. Full-population reconstruction passes; supplementary prior-exposure repair changed no selected identity or ordering.

A no-model post-panel check found execution sources, binaries and inputs still identical to the published freeze after all864 slots. Later edits only concern read-only reconstruction, cost-stage labels, documentation and transport. Original source snapshots, raw failed partial files, old R, full vectors and byte-exact reconstructible F16 sequence state are retained. Original Qwen F32-activation/p021 libraries and PR169 capacity failures are not relabeled as successful.

The separate v2 raw release contains actual binaries, portable frontend inputs, arguments, manifests and all included raw bytes, without GGUF weights. The immutable initial v1 release remains unchanged. Restore the objects and run `python -B RESTORED/delivery-v2/recompute.py RESTORED` with the pinned host requirements. Fresh-download restoration is recorded in `evidence/recovery/DELIVERY_READBACK.json` when delivery completes. Verification is authenticated on the same B570 host; it does not claim external native replication or anonymous access.

No merge, paper edit, new model download, rental or cross-platform pooling.
