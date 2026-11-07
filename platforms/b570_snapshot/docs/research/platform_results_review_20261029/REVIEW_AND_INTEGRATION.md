# Platform result review and manuscript integration memo — 2026-10-29

## Checkpoints and scope

Paper baseline: `914b820e00b33a0d428335637345454b8736959c` (PR145). B570 result: `022babfabb3d1b6f4f2a2830dca04b2654d193f9` (PR152). RTX qualification: `cefbd987df44dc74aae769eeb1b12ea43c276ecc` (PR151).

This is a source/compact-evidence review, not another native execution or an external peer review. It reads the B570 protocol, input-source amendment, implementation, native boundary driver, analyzer, complete compact matrix and state comparisons, audit summaries, delivery receipts and live release metadata. It also reads RTX qualification status, metadata-correction before/after receipts, and continuation instructions.

Two compact CSVs were materialized from connector-returned content and authenticated against their Git blob identities. A separately written standard-library script cross-checked all 48 coordinates and shared equality fields. The complete raw-vector auditor and all 6,826 archive members were NOT rerun/rehashed by this review. Full-package verification is attributed to the source-host receipts.

No PR was merged. No GPU request was launched. This memo does not alter manuscript TeX, numerical results, frozen experiment sources, calendars or budgets. The 28-page PDF at `914b820e` remains the last validated manuscript artifact.

## 1. B570 scientific conclusion

The result is suitable for the main text. Its strongest evidence is a fixed-reference producer-conditioned change in local eligibility, not merely unequal producer-state bytes.

For `MATH500/test/prealgebra/1865.json` and `.../1804.json`, denote the complete P1/P4T boundaries by S1/S4, including initial logits. Under the frozen boundary0 clean-receiver contract and capped/EOG endpoint window:

```
C1(S1) = C1(S4) = R
PQ(S1) = QB(S1) != R
PQ(S4) = QB(S4) = R
```

P1 local paths first diverge at outputs 5 and 25 respectively, one-based. PQ and QB agree in complete endpoints, cycles and captured full-vocabulary vectors on all 16 input–producer pairs. Their mutual agreement therefore does not establish preservation of the specified serial reference.

Independent compact cross-check:

| Producer | C1 = R | PQ = R | QB = R |
|---|---:|---:|---:|
| P1 | 8/8 | 5/8 | 5/8 |
| P4T | 7/8 | 7/8 | 7/8 |

Five inputs retain R in all six scientific cells despite changed producer-state bytes. Two have the fixed-reference eligibility switch above. `GSM8K/train/1184` changes its natural C1 and local endpoints with the producer; its local pair differs from its own C1 under both producers.

The 152 completed requests, 48 evidence-qualified scientific cells and 39 strict-R-equal scientific cells are different quantities. Do not translate evidence qualification into universal reference preservation. The 39/48 tally is descriptive fixed-panel accounting, not a population rate.

### Contribution and reporting

The paper should retain repair scope and drafting economics as its main direction, with this result strengthening the qualification step: qualify the producer–consumer execution combination against the chosen reference before comparing complete-request costs. The states here were produced by the two prefill recipes, rather than arbitrary mixtures of KV components; the resumed consumer nevertheless remains a clean receiver.

Preserve these distinctions:

- The intervention changes complete producer boundary state, including KV and initial logits. It does not isolate KV alone, identify a failing operator, prove general q4 qualification, or establish natural integrated P4T speculative-path behavior.
- The final panel is four short GSM8K and four longer MATH-500 inputs under documented pre-forward source amendments. It is all-math, not a domain-by-length factorial. Do not infer a length effect or a population failure rate.
- Observer-off retains common metadata instrumentation. The control establishes the defined full-logit-observer/restoration contract, not an entirely uninstrumented production path. Endpoint equality is limited to the captured cap/EOG window.
- The matrix supplies no formal performance result. In particular, P4T is not established as a generally superior repair policy.

No additional B570 model requests are recommended for this bounded paper claim. KV/logit decomposition and natural integrated P4T speculation would answer stronger, separate questions and require their own pre-execution plans. They are not prerequisites for reporting this result accurately.

## 2. Evidence checks

The source-host summaries report 152/152 requests, B0 qualified, 96 actual restored-boundary checks, 88 observer/own-path comparisons, 48 scientific cells, and no audit errors. Native source inspection confirms empty-receiver import, actual state re-export/readback, full initial-vector extent checking, and first-maximum sampling of the receiver-owned initial vector. `analyze.py` keeps strict-R equality separate from producer-conditioned C1 equality and evidence qualification.

The live published prerelease's eight asset IDs, sizes and server-reported SHA256 digests match `delivery/ROUNDTRIP.json`: six ZIPs plus the member manifest and package receipt. That receipt reports all 6,826 members verified; `delivery/CPU_READBACK.json` reports eight byte-identical reconstructed products. This review did not repeat the multi-gigabyte download or raw-payload replay.

Compact source identities independently checked:

| File | Git blob SHA1 | SHA256 |
|---|---|---|
| `execution/STATE_EFFECTS.csv` | `c59910d9888cd01d60e91ce40f6a16a82f88e264` | `b578e7a0311484a06447f99836b02beabbb90c7e964512b0d28b5c4dcafd38ac` |
| `execution/MATRIX.csv` | `e67b215eb5fe992d6de06ef37dd984f27505d5f2` | `de73abff0826ec8e0ad3c76ae19e6e6d6f24759f2464380dd229ef064ee6b699` |

## 3. Manuscript integration draft — not inserted or compiled

Place after “Preserving the AV path in a scoped GQA port” in `paper/arxiv_v4_candidate/sections/06_boundaries.tex`. This connects a successful local numerical port to its end-to-end eligibility conditions. Keep the older Llama state experiments separately attributed.

### Producer-conditioned eligibility after a successful port

A successful local port does not make reference eligibility independent of producer state. We test the Qwen3 GQA port on eight new mathematical inputs using a 152-request protocol: 32 historical restoration and observer controls, followed by 15 requests per new input. P1 submits prompt IDs individually; P4T submits groups of four, with a three-token tail split into two plus one. Each producer exports its complete sequence state and initial FP32 logits. Fresh C1, PQ and QB consumers then resume under the fixed boundary0 clean-receiver contract. Each input also has an independently executed strict serial reference R.

Changing the producer changes both KV serialization and initial logits on all eight inputs. PQ and QB nevertheless agree in endpoints, cycles and every captured full-vocabulary vector on all 16 input–producer pairs. Two inputs isolate a stronger boundary: C1 retains the same R under both producers, while PQ/QB depart from R after P1 and preserve R after P4T. Their first P1 local departures occur at outputs 5 and 25. Five inputs retain R in all six producer–consumer cells; the remaining input changes its C1 and local endpoints with the producer, and its local pair differs from its own C1 under both producers.

Thus, agreement between local implementations and equality of the producers' serial endpoints do not establish identical reference eligibility. Qualification must account for the producer–consumer combination. This intervention measures the total effect of the exported boundary state under the clean-receiver contract; it neither isolates KV alone nor measures natural integrated P4T service performance.

Retain the full eight-input table in supplementary material. The main text can show the two fixed-reference examples and summarize the other five-stable/one-changed-reference outcomes without discarding any inputs. RTX qualification must not be entered as a new performance estimate.

## 4. RTX status and continuation

The current runner is implemented; the old design-stage NATIVE_EXTENSION_REQUIRED description is obsolete for PR151's current checkpoint. Qwen and SmolLM2 each have 98 numerical qualification requests. Formal measurements, formal warmups, Llama diagnostics and technical retries are zero at the reviewed checkpoint.

The SmolLM2 metadata correction recovers a renamed query from an already captured `kq` operand under a pinned family/source condition. Before/after request hashes both equal `d94ad8a65cd95e85a61a0e76bcfd0b770b3aa810452c094143e96e4743bb917b`; attempt hashes both equal `cf44ded7bac952efd88c1f19cb716a4eba2f6791be903a52a78af612f21aaf60`. The original refusal is retained and the receipt reports zero added GPU requests. No numerical threshold should be relaxed.

This review environment is a Linux sandbox without an available execution route to the Windows RTX host. No live host lock/process inspection or formal request was performed. Continue only on the native host.

### Host handoff prompt

在 PR151 当前分支的 RTX 原机上继续：先读取 CONTINUE_HOST.md、CURRENT_SOURCE_BINDING.json、现有 bundle 的 FREEZE_COMMIT.json、ATTEMPTS.json 和两个 NUMERICALLY_QUALIFIED 回执，并核对锁及进程身份；仅在真实上海日期 2026-10-29 按顺序执行尚未启动的 d0 四个 formal unit，每个完成并核验回执后再启动下一个，不重建、不重跑资格、不删除锁、不重复已有 attempt、不花自动重试储备；保留所有失败，结束后提交实际计数与继续说明，不合并 PR。

For 2026-10-29 Asia/Shanghai, the existing order is:

1. `formal/d0/s0/Qwen`
2. `formal/d0/s0/SmolLM2`
3. `formal/d0/s1/Qwen`
4. `formal/d0/s1/SmolLM2`

Each unit has seven warmups and 84 measurements. A complete day is therefore 28 warmups plus 336 measurements, 364 planned requests; these are not executed counts.

The checkout is `C:\Users\ASUS\Documents\ChatGPT\HeteroSpec\repo`. Run one unit at a time after preflight:

```powershell
& D:\HeteroSpec-PC\python311\python.exe -B scripts\experiments\rtx_scope_transfer_v1\host.py --bundle work\scope-transfer-bundle-v1 --unit formal/d0/s0/Qwen
```

Preserve the frozen 2026-10-29/30/31 dates, existing family order, >=20-hour per-family/daily-first-session gates, 1,800-second pre-midnight allowance, and numerical no-retry rule. Do not substitute dates, reset existing attempts, or count qualification as formal collection. The 54 Llama diagnostics remain a separate stream. B570 outcomes must not change the RTX panel, runtime, comparator or thresholds. Retained temporary directories need not be deleted.

## Source links

[B570 result](https://github.com/leecdiang/HeteroSpec/blob/022babfabb3d1b6f4f2a2830dca04b2654d193f9/benchmarks/b570_producer_consumer_boundary_v1/RESULT.md) · [Matrix](https://github.com/leecdiang/HeteroSpec/blob/022babfabb3d1b6f4f2a2830dca04b2654d193f9/benchmarks/b570_producer_consumer_boundary_v1/execution/MATRIX.csv) · [State effects](https://github.com/leecdiang/HeteroSpec/blob/022babfabb3d1b6f4f2a2830dca04b2654d193f9/benchmarks/b570_producer_consumer_boundary_v1/execution/STATE_EFFECTS.csv) · [Delivery](https://github.com/leecdiang/HeteroSpec/blob/022babfabb3d1b6f4f2a2830dca04b2654d193f9/benchmarks/b570_producer_consumer_boundary_v1/delivery/README.md)

[RTX qualification](https://github.com/leecdiang/HeteroSpec/blob/cefbd987df44dc74aae769eeb1b12ea43c276ecc/benchmarks/rtx_scope_transfer_v1/host_execution/QUALIFICATION_STATUS.json) · [Continuation](https://github.com/leecdiang/HeteroSpec/blob/cefbd987df44dc74aae769eeb1b12ea43c276ecc/benchmarks/rtx_scope_transfer_v1/CONTINUE_HOST.md) · [Metadata correction](https://github.com/leecdiang/HeteroSpec/blob/cefbd987df44dc74aae769eeb1b12ea43c276ecc/benchmarks/rtx_scope_transfer_v1/AUDIT_METADATA_CORRECTION.md)
