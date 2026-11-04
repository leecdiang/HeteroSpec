# RTX natural prefix reuse: No registered useful AUTO service benefit

All 32 held-out roots and all 4 arms passed native qualification. All 512 formal measurements and 512 immediate warmups completed once across four independently loaded sessions. The registered engineering screen is **NOT MET**. AUTO was frozen to `WB-cut` for every structural bin. Against the fastest fixed arm (`WB-cut`), its point service-time reduction is -0.6350%; the baseline/AUTO family-adjusted interval is [0.974813, 1.012617].

This is one exact-token file-backed replay deployment on the original RTX 5070 Ti Laptop host. It is not a production throughput, task-quality, GPU-population or cross-platform pooled estimate. A non-passing usefulness screen is not an equivalence result.

## Execution and frozen identity

- Design PR172 actual starting head: `801196166c8e2a02215003301d129e68504e6b72`; result branch: `codex/rtx-prefix-reuse-results`.
- Scientific ancestor PR171: `371223b696bb805030c29f04e39eb17b57fb2ebb`. Original scalar reference libraries and the unchanged packed CUDA arithmetic shared by all candidate arms remain authenticated.
- RTX source/policy freeze: `efd92438a08a4e9c37a422731ddd6850d8907f1b`; B570 actual freeze: `6517c79b59ad3d813a35fa087d15751b825dad34`.
- Joint gate released at `2026-11-04T04:46:22.131137+00:00` after independent 44-row identity/token/physical-head verification, before local held-out outputs. See [gate](evidence/COMMON_BLIND_GATE.json).
- Qwen3-8B Q8_0 SHA256 `408b955510e196121c1c375201744783b5c9a43c7956d73fc78df54c66e883d6`; C4096, F16 KV, non-flash, qmax32, target-only, all GPU, greedy cap128/native EOG.
- Native tokenizer identity `cc2cca16f808de7d17ae597b6f70563c006ff70d9a0dfae84ab5ccbd518e96ee`; template `57f1fd00f0013a2be96aa79b857391f27e23df5b5f847072b524c897e24d0361`.

A model and context stay resident within each session. Complete service includes snapshot file read, prefix-index materialization, reset, lookup/import, one policy lookup, append, greedy continuation, synchronization and owned response commit. Shared model/context startup and evidence serialization are outside service and retained in process accounting. B570 uses host-memory snapshots, so matched inputs do not justify a pure hardware timing contrast.

## Natural opportunity and fixed cohorts

The pinned OASST1 leaf pool has 6,423 eligible paths from 2,596 roots. Complete history and request strings were rendered and tokenized natively; token-level LCP, real allocator metadata and actual restored dense heads were checked. No synthetic padding, offset selection or prompt truncation was used. The earlier broader-path interpretation and its costs/reference bytes remain as engineering evidence; it contributed no exposed root to the common held-out panel.

| Granule | Eligible paths | Lost reuse | Crossed paths | Crossed q32 calls / total | Test crossed / eligible |
|---:|---:|---:|---:|---:|---:|
| 1 | 6423 | 0 | 573 | 623 / 9888 | 4 / 32 |
| 16 | 6422 | 1 | 346 | 375 / 11486 | 2 / 32 |
| 32 | 6242 | 181 | 0 | 0 / 12903 | 0 / 31 |
| 64 | 5564 | 859 | 0 | 0 / 14175 | 0 / 30 |

Granule 1 is the implemented deployment. Granules 16/32/64 are predeclared output-free floor-LCP scenarios from the original descriptors, not measured engine configurations. They use the same fixed panel without re-ranking. q32-aligned heads remove internal crossings; this does not establish that every serving engine uses those heads. The actual deployment retains 573 crossed paths (623/9,888 q32 calls, 6.30%); the 12 calibration roots contain zero crossings and the 32 held-out roots contain four.

## Native qualification

- Original scalar reference: two independent runs for each of 32 held-out roots.
- Main qualification: all 160 original-repeat/candidate comparisons passed complete binary32 vocabulary vectors, endpoints, positions and final sequence-state bytes; all 256 candidate heavy/off slots completed. Actual plans and physical heads matched the declared policies.
- Separate continuous-scalar/restore and own-prefix candidate diagnostics matched 75 full vectors and final state per comparison. Extra known-append rows use separate output flags and do not replace real-service qualification.
- Empty-cache control: first 8 unchanged full prompts; all 32 reference-repeat/fixed-arm comparisons passed, with 64 qualification and 96 timed/warm slots.
- All 1024 main service outputs and positions were checked against immutable original references during reconstruction. No passing subset was selected.

See [main proof](evidence/MAIN_QUALIFICATION.json), [aligned proof](evidence/ALIGNED_QUALIFICATION.json), and [raw archive verification](evidence/raw-evidence.zip.RESTORED_DOWNLOAD.json).

## Complete-service results

Ratios are fixed baseline time / AUTO time; values above 1 favor AUTO. Roots are equally weighted, retaining all four paired session vectors. Intervals use 10,000 root-bootstrap draws, seed 20261104; each primary interval is two-sided 98.333% (Bonferroni family 95% across three comparisons).

| Baseline | Baseline / AUTO | AUTO reduction % | Family-adjusted interval | Session ratios 1–4 |
|---|---:|---:|---|---|
| QB | 0.995384 | -0.4637 | [0.977198, 1.012918] | 1.003154, 0.986802, 0.995264, 0.996384 |
| WB-cut | 0.993690 | -0.6350 | [0.974813, 1.012617] | 0.991548, 0.998086, 0.993975, 0.991167 |
| WB-rechunk | 0.993964 | -0.6073 | [0.978640, 1.009058] | 0.987606, 0.996171, 0.987772, 1.004403 |

The engineering criterion requires every family interval above 1 and at least 3% reduction versus the fastest fixed arm. All four sessions occurred on 2026-11-04; there is no cross-date inference. Secondary unadjusted intervals, all root contrasts and worst regressions remain in [analysis](evidence/analysis.json).

| Arm | Geometric service s | Mean service s | Median s | Descriptive p95 s |
|---|---:|---:|---:|---:|
| QB | 3.007364 | 3.016579 | 3.000563 | 3.404085 |
| WB-cut | 3.002246 | 3.011222 | 2.987967 | 3.370909 |
| WB-rechunk | 3.003073 | 3.010709 | 2.973117 | 3.352206 |
| AUTO | 3.021310 | 3.029067 | 3.021203 | 3.322063 |

These percentiles describe 128 measurements per arm conditional on 32 roots and four sessions; they are not an SLA estimate.

Descriptive fixed-policy comparisons (no additional hypothesis tests):

- WB-cut / QB: 0.998298; session ratios 0.988431, 1.011435, 0.998704, 0.994764.
- WB-rechunk / QB: 0.998573; session ratios 0.984502, 1.009494, 0.992472, 1.008048.

## Append, imports and aligned control

| Arm | Geometric receipt-to-append s | Mean cumulative import s | Mean snapshot bytes | Empty-cache geometric service s |
|---|---:|---:|---:|---:|
| QB | 0.622190 | 0.464198 | 43706716 | 3.814175 |
| WB-cut | 0.623004 | 0.463064 | 43706716 | 3.803054 |
| WB-rechunk | 0.629014 | 0.469285 | 43706716 | 3.793374 |
| AUTO | 0.631300 | 0.469265 | 43706716 | not scheduled |

Append interval includes request receipt, file read/index/reset/lookup/import and append. Import interval is cumulative from receipt, not an additive isolated phase. No phase subtraction or kernel-cost attribution.
The empty-cache control uses another workload lifecycle and is not pooled with cache-hit service. Existing CUDA graph reuse log events are retained by process; no complete hit-rate denominator or per-arm kernel mask/join attribution is claimed.

## Complete costs and retained failures

- Calibration campaign elapsed: **2038.781179s**, including earlier repair/cohort epochs and idle coordination inside the recorded calibration window. The window starts with the first original calibration request; initial setup/build time before it is outside this explicitly named calibration window.
- Conservative request reservations: **2026 / 2048**; completed native request receipts: **1957**; reserved units without a completed receipt: **69**. Interrupted batches retain their entire reservation.
- Zero-forward launches: **2**; completed native process wall sum: **7288.123934s** (separate from, not added to, overlapping calibration wall time).
- Main measured service sum: **1544.649764s**; immediate-warmup service sum: **1539.268555s**.
- Main observed cache-hit fraction: 100%; serialized snapshot bytes supplied to the import API totaled **44755677696 bytes** across 1024 main slots. These are serialized API input bytes, not measured PCIe traffic. The planned replay hit fraction is not a production traffic estimate.
- Across all completed engineering/calibration/main/control requests, recorded service windows sum to **6021.082215s**; disjoint positive-head prefix production adds **438.733440s**. Heavy-observer I/O is included where actually used. Model-load windows sum to **451.653362s** and remain separately reported.
- The pre-freeze epoch omitting file/index costs was interrupted and invalidated for service claims. A later batch was interrupted for output-blind leaf-cohort reconciliation. Both batches, incomplete slots, original references, source epochs and cumulative costs remain in the raw archive and ledger; no favorable rerun was selected.

The full slot-by-slot disposition and process exits are in [details](evidence/DETAILS.json) and [accounting](evidence/FINAL_ACCOUNTING.json). Compile command outcomes/logs and old historical evidence remain separately pinned; no old R is replaced.

AUTO arithmetic mean service saving versus `WB-cut` is -0.017844841s/request; the secondary descriptive paired-root95% interval is [-0.065013513, 0.029399517]. This is a post-selection descriptive calculation, not another primary significance test.
No positive point saving exists, so no finite point calibration break-even is reported.
The saving interval includes nonpositive values, so a finite uncertainty-bounded break-even is not established.
Only 128 AUTO measurements were observed, four per root. No unlimited reuse/fanout is assumed.

## Reproduction and delivery

Release: [rtx-prefix-reuse-v1-20261104](https://github.com/leecdiang/HeteroSpec/releases/tag/rtx-prefix-reuse-v1-20261104). It contains the frozen runtime, complete native source kit, pre-test calibration archive and final raw evidence parts with whole/part SHA256 manifests. Model weights are excluded and must match the pinned hash.

Follow [execution README](README.md). `download_parts.py` downloads to a fresh directory, authenticates and joins parts, and reconstructs raw qualification and bootstrap results. `reproduce.py --prepare-only` checks the delivered runtime/model and rebases immutable snapshot paths without adding native measurements. Actual replay is a new run and must be charged separately. The worker deliberately requires an NVIDIA device description containing 5070; another deployment needs new qualification.

Actual restored-download verification is documented separately from local packaging checks. Neither is third-party native replication. No result was merged and no manuscript was changed.

## Delivered verification

All 58 final raw parts were downloaded from GitHub, authenticated and rejoined. The downloaded archive reconstructed all qualification evidence, 144 calibration slots, 1024 main slots, 96 aligned slots, separate restore diagnostics and the exact bootstrap result. It retains 56,588 original paths and 8,988 unique content blobs. Whole-archive SHA256: `5850cd9e839f099c6105ae54ce144494d32ee6e058b32cb3701e8f2272de5570`.

Prepare-only replay also passed against the downloaded runtime/raw archives and exact model, materializing 32 authenticated snapshots for the original main-session manifest. It added zero model requests. [Delivery receipt](evidence/DELIVERY.json) retains transfer retries and verification scope; this is not third-party native replication.

## All held-out root contrasts

| Input ID | QB / AUTO | WB-cut / AUTO | WB-rechunk / AUTO |
|---|---:|---:|---:|
| 8f6cbe7e-68df-4f96-9db3-594349dace43 | 0.929138 | 0.996222 | 1.055964 |
| a907849a-47a2-4e99-b5c9-787c5e93b52c | 0.989826 | 1.012101 | 0.991351 |
| 5c6415d4-4ba2-4ae0-a8e8-94694c61beac | 0.981056 | 0.996804 | 1.040417 |
| a3da83e3-e7ee-4051-bb64-98b4ad5561b1 | 1.018022 | 1.031499 | 0.953889 |
| 3f6424db-28af-41e2-bf0d-5427e226fbde | 1.068793 | 1.062436 | 1.024832 |
| 45074e6e-c5c6-43a0-8219-5aabbe1cb91b | 1.034577 | 0.986664 | 0.982717 |
| 8c38fcad-3134-48c9-a7c7-1a1e61126f5b | 0.966055 | 1.023693 | 0.956936 |
| 49d7e5b4-ffad-45f7-ae43-a8a91628ee13 | 0.974588 | 1.007617 | 0.958952 |
| 7a09054a-d17a-4880-82db-1598a0986533 | 1.047638 | 1.012674 | 1.045180 |
| b4e71c50-6af7-4a38-8663-e52b687f4605 | 0.971920 | 0.978988 | 0.988425 |
| e203db32-e885-4190-b1b2-b601c0d422b4 | 1.032562 | 0.956446 | 1.023274 |
| 0f1551f9-a09b-4b4b-9d1c-fa4e73703064 | 0.983282 | 0.966081 | 1.038770 |
| 6f42d232-d4e5-48f4-87ec-11987da35301 | 0.957593 | 0.969810 | 0.971782 |
| d80047a7-b5a4-408b-bb61-a9bc3fc30588 | 1.036966 | 1.003558 | 0.969845 |
| 0c77ef1d-f948-46e2-85a4-afd9d547f9e0 | 0.997803 | 1.048286 | 1.035633 |
| 9b70cc99-29c5-43bb-a590-213b5f0aee4d | 1.047881 | 1.036520 | 0.972124 |
| 00e60d6a-1b9e-4caf-a41c-2851b8829d96 | 1.043030 | 1.098598 | 0.991245 |
| 51bef404-cab9-41db-bb10-ead11ff45a3c | 1.033404 | 0.998803 | 0.997037 |
| aff49381-45fa-4d8b-8473-03da470f7286 | 0.951827 | 0.901470 | 0.909931 |
| b12101a2-c02a-48f8-a540-9ad91e56c61b | 0.954312 | 0.956954 | 0.988083 |
| 2362e4d3-00d0-4f58-a582-adbdd368b2aa | 0.979519 | 0.957854 | 1.015060 |
| 3cea8e47-8031-4173-a7ae-16bbad0a4ba3 | 0.980311 | 0.936643 | 0.964973 |
| f3f8ff92-0304-4234-ade2-a89538315a34 | 0.879303 | 0.937130 | 0.922365 |
| e1e672fd-8925-4629-a1be-fd7e760c68f8 | 1.023509 | 0.973119 | 0.984527 |
| 069bc63b-6c4d-4904-80e4-680770d5997c | 0.923898 | 0.914001 | 0.954952 |
| 6e0ae277-4ca6-47b9-a95b-750bafd8ecbd | 1.038293 | 1.077870 | 1.060501 |
| d9313683-4472-4333-a1c9-a1e48035e70e | 1.005192 | 0.991514 | 0.970798 |
| 554215b3-25a7-41c2-96ed-8ec7d4f6b64a | 0.994919 | 0.954659 | 0.994648 |
| 399e61a5-2d6b-43e7-8261-ed23ade2ab96 | 0.976009 | 1.042377 | 1.016765 |
| 5f09e449-9116-4e98-b536-df1fc54100c2 | 1.032485 | 1.001637 | 1.001190 |
| 874c03f7-0abc-4b95-a4bb-1d106f153c3b | 0.984407 | 0.994150 | 1.003121 |
| 53161481-6975-4d6d-8633-6afc9af423eb | 1.043470 | 1.003187 | 1.043419 |
