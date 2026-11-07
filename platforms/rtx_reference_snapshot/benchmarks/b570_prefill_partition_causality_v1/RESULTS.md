# B570 Prefill Partition Causality — native result

At fixed target-only UB512, externally partitioning prefill into128 + remainder reproduces the historical UB128 complete outputs for both affected tasks. A differs from B at the original delayed output indices47 and81; B matches C over every native ID, EOG/cap boundary, length and terminal ID. B and C have **bitwise-identical full FP32 logits and source-defined serialized sequence KV at prefill completion**. This supports the sufficiency of this concrete external Prefill partition intervention on these exposed cases.

This updates PR97's unresolved prefill-only question with a narrower admitted intervention. It does not turn the earlier failed whole-recipe factorial into a clean experiment, claim isolated Vulkan kernel geometry, prove state-to-output mediation/necessity, validate state transplantation, change stock qualification or certify physical residency.

## Actual intervention and physical work

A: context UB512/capacity1, full prompt in one caller.
B: **same UB512/capacity1**, caller128 + remainder.
C: UB128/capacity1, one caller internally split by native runtime.
All other target-only model/context/precision/greedy/stop/continuation rules fixed; no continuation binding, speculative code modification, warmup, retry or forced token.

For all arms, the complete prompt's final absolute position is the **only** requested prefill logits row. B's intermediate caller requests zero logits. Trace-derived contiguous KV positions, natural pending-token consumption, native successful physical widths and graph/row conservation were independently checked.
For161 IDs: A has caller161 and physical graph161; B has callers128+33 and physical graphs128,33; C has caller161 and physical graphs128,33. For133 IDs the remainder is5; stable long controls use128+62 and128+35. Continuation submits one consumed pending token and executes occupied width1 on all paths.

Caller segmentation inherently includes per-call queue/scheduler handling. Graph counters represent successful native micrographs and occupied rows, **not** Vulkan dispatch counts or exclusive GPU stage fees. Capture-heavy mode adds completion waits/readback per caller; a separate capture-off repeat produces identical complete outputs in every arm.

## Complete trajectories and numerical state

| Fixed input | Prompt IDs | First A/B difference, zero-based | Full B=C | Prefill B/C FP32+KV bitwise equal | Prefill A/B FP32 equal | Prefill A/B KV equal |
|---|---:|---:|---|---|---|---|
| GSM8K/test/1248 | 161 | 47 | True | True | False | False |
| GSM8K/test/831 | 133 | 81 | True | True | False | False |
| GSM8K/test/1011 | 190 | None | True | True | False | False |
| GSM8K/test/1249 | 163 | None | True | True | False | False |
| FIXED_PREFIX_1248/127 | 127 | None | True | True | True | True |
| FIXED_PREFIX_1248/128 | 128 | None | True | True | True | True |
| FIXED_PREFIX_1248/129 | 129 | 57 | True | True | False | False |

Each task/arm has3 independently loaded worker repeats, with rotated arm/task order: counts capture-off, heavy capture-on, heavy capture-on. Every complete endpoint is stable across all3 repeats; both captured repeats have stable numerical hashes. All7 inputs also have B/C-identical logits/KV hashes at the3 registered natural output cuts. Full FP32 vectors are archived at all cuts; complete sequence-KV bytes are archived at prefill completion. Later KV hashes have no archived payload and are explicitly bounded live diagnostics.

The two historical stable >128 controls were selected prospectively by ascending integer ID from the old stable long-prompt set; both have A/B prefill numerical differences but identical complete output. The127/128 fixed-prefix inputs are invariant; the129 fixed-prefix input changes output at57 and matches C. Thus exceeding128 does not imply inevitable token-output divergence. These fixed-prefix inputs are truncated synthetic ID sequences; no benchmark-answer correctness claim is made.

A reproduces all10 original R_prod endpoints and C all10 original R_stock endpoints on each of the4 historical tasks. Original160 selected native records are archived and checked against the immutable formal record index. The129 case's first difference57 was **not** an added capture cut: its registered cuts remain0/1/47.

## Execution, source and independent validation

63 starts / 63 complete;1 zero-forward load probe;64 charged units;0 warmups/retries/forks;10 native lifetimes;805.234s owned lifetime. Minimum sampled same-PID dedicated headroom 2,097,594,368 bytes. Actual Intel8086:E20C/B570 native Vulkan weight/KV placement and numerical DLL identity passed. Continuous residency UNKNOWN.

The original numerical DLL bytes and Q6_K GGUF hash are unchanged. Frozen PR97 parent:5a66653bd0ce413d4eb9aef3a4501b93c138071b.
Prospective actor seal:f35e63076287caf213106b683e888a3674a07d73 was published and authenticated from55 actual GitHub file bodies before the first new forward. The39-part source transport is recorded in F0A_CAPSULE.json/F0A_AUTHENTICATED.json; no metadata-only source verification. Preparatory failures are recorded and no scientific request failed.

code/verify98.py is stdlib-only, imports no controller and performs no native execution. It independently validates all63 coordinates, all raw FIFO endpoints, source/model/module pins, exact historical outputs, final-only logits, KV positions, graph conservation, full FP32 payloads/top2, and source-defined64 K/V tensors in each prefill payload. Twelve rejection tests cover malformed coordinate/payload/geometry/stop/PID/headroom evidence.

See INDEPENDENT_VERIFICATION.json, SYNTHETIC_REJECTION.json and full CAS descriptor/manifest. Fresh local and authenticated remote restoration receipts are published separately to avoid circular archive hashes; each recomputes all5 analysis artifacts from restored raw bytes and fully rehashes the target GGUF.

## Qualification and cost boundary

Original PR92 R_stock-relative qualification failures and all null qualified ratios are retained in baseline/PR92_QUALIFICATION.json with the exact original bytes and in QUALIFICATION.json. This study is an exposed target-only intervention, not a new blind stock qualification trial. All new elapsed fields are diagnostic only; no new paid request economics, speedup ratio, GPU timing coefficients or break-even fit. The earlier actual request-cost and physical verification-work conclusions remain the separate PR92/93/97 evidence. MODEL_TIMING_UNAVAILABLE, donor-state causality UNRESOLVED, no state restore/clone claims.

Legacy phase96.*.logits_scope wording in the inherited frontend says hash-only. For this frozen follow-up, the additional partition98.full_payloads pointers are authoritative: raw FP32 vectors and prefill sequence KV bytes are saved and independently rehashed. Serialized state excludes dynamic output buffers, frontend pending/sampler/scheduler ownership, as documented in the retained source scope.

Only a new benchmark subtree is added. Main, paper, docs, old result files and existing PRs are not changed or merged.
