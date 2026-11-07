# RTX Llama causal-prefix repair

Execution is in progress. This record separates completed mechanism evidence from the confirmation and delivery gates, which are not yet complete.

The starting protocol is PR160 at `aff1d029966a20adebfad6b664a36f32ed04bf9c`, based on PR159 at `38b3d3d3929dc958e6a2a7e0bdc8abd61ff38ab1`. This is a separate results branch. The original R executable, model files, tokenizer, metadata4 source archive and numerical DLL cohort remain unchanged. Earlier PRs and their ledgers remain intact.

## Historical reconstruction and default baseline

`history.py` authenticated all 54 PR151 Llama diagnostic requests and all 5,916 complete 128,256-element F32 decision vectors. The request manifest digest is `2e52aee27acb551f3f3556a566ec5f83b123aa0d50a9c01da3666ac33a2fa4b9`. The default roles=0 build had no numerical extension and no Qwen normalization patch. It passed native capacity admission and completed the registered 36-request matrix.

All nine heavy R/C_PQ/C_QB cells across the original failure and two controls reproduced their historical endpoints and every saved vector. Thus the baseline reproduced the failure rather than replacing its reference. CPU test success was recorded separately and was not used as native validation.

For CodeContests/valid/108, the first output mismatch at output index 81 maps to actual cycle 21, row 2, base 815 and input position 817: old R selects token 16, whereas both baseline C arms select token 15. The earliest saved common-prefix vector difference is output index 29 at cycle 8, row 0, base 765. These mappings come from the actual recorded cycles, not division by the draft length.

## Mechanism evidence

At cycle 8 the four consumed positions are 765–768. Single-row consumption uses a physical KV extent of 768 for the first three rows and 1,024 for the fourth. A natural four-row verification uses 1,024 for every row. On exactly the same candidate KV and pending state, the baseline q1 and q4 consumers differ in complete vectors, while the q1 vectors match the old R vectors at this point. At cycle 21 the same-state consumers agree, including the wrong decision: the earlier state divergence has already propagated.

The q4 own-path replay matches natural execution. Both shadow orders, trace/no-trace controls, live-state invariance and unchanged natural outputs were checked. Captured layer-zero Q, visible K, visible V, visible QK and valid probability values agree bitwise, and the masked probability suffix is exactly zero.

Twenty-two standalone native CUDA operator executions include repeated own-path reconstructions and crossed-extent interventions. The operator experiment uses the first query of actual C_PQ execution at the captured checkpoint. Both consumers lower this attention operation per query, so the captured query width is one on both sides; their physical KV extents differ. Padding the q1-consumer probabilities with zeros and using the 1,024-wide V operand reproduces that query's q4-consumer V×probability output. Cropping the q4-consumer probabilities and V operand to the 768-wide scalar extent reproduces its q1-consumer output. Softmax crop/pad controls preserve the visible probability bits. This isolates physical reduction extent as the causal variable in this captured attention operation. C_QB transfer is validated by its separate same-state and natural matrix controls. The Llama cause is not attributed to Qwen RoPE.

Scheduler evidence places these operations on CUDA0. Source inspection is consistent with a reduction launch geometry change; an exact profiled kernel launch is not claimed.

## Structural intervention and retained failures

The repair groups maximal adjacent query rows that have equal scalar-equivalent physical KV prefix extent. Extents are computed from actual cache occupancy, slot head and native padding, rather than from a task, model name, answer, output index, layer or margin. The rule is guarded to dense contiguous single-stream append, ordered single-sequence causal non-flash attention. It crops Q/K/V/mask views for each group, materializes a shortened mask when necessary, concatenates the attention outputs, and includes the prefix extent vector in graph reuse checks. Other paths retain the original behavior.

The combined candidate retains PR159's separately established Q/K head-normalization offload policy for Qwen regressions. Llama 3 has no such head-normalization nodes; that policy is not asserted to explain this Llama failure.

The first operand observer rejected a legitimate scheduler mask copy; its failed unit and reservation remain. The observer was repaired by checking the exact scheduler-copy naming, operation, storage disjointness and source-bound scheduler behavior. The first structural candidate failed the native contiguous-mask assertion after 10 of its 36 reserved requests. Its source, build, partial raw and all 36 reserved credits remain. The successor explicitly materializes noncontiguous masks. A related build containing the known faulty mask policy was retained without native execution.

The repaired candidate completes all 36 development requests with original-reference and observer equality. All 18 heavy cells' committed decision vectors equal the corresponding original R vectors. Eight repaired same-state pairs across both arms, both orders and trace/no-trace have equal complete q1/q4 vectors and pass own-path controls. A fresh ablation process with the structural repair disabled restores both original failures, including their vectors and states.

## Frozen confirmation and independent reconstruction

The final host-schema successor, epoch07, uses the unchanged config06 native candidate. Its repeated 36-request development matrix passes. The complete pinned historical exposure union excludes IDs, text hashes and token hashes across all reviewed project history. The selected 24-input code/math × short/long panel remained unchanged through the pre-output host-schema correction and was frozen before any reference or candidate output.

All 48 immutable old-R reference requests and all 240 candidate qualification requests complete. Independent reconstruction checks 23,080 complete decision vectors and 168 candidate final-state artifacts, all endpoints/transactions/observer pairs, original-R vector preservation and layer/backend coverage. New Qwen8B/14B regressions pass 144/192 requests; the additional 24/32 successful original-R controls preserve complete R vectors. These Qwen inputs are development inputs, not unseen confirmation.

All six timing sessions complete: 864 measured requests and 864 immediately preceding warmups, with no captures, shadow consumers or concurrent archives/profiling. Independent recomputation matches the production report and retains every block. The geometric mean C_QB / arithmetic-dual-C_PQ service ratio is **0.975530833**. The largest symmetric input-aggregate A/A imbalance is **2.983157%**; the prospective improvement threshold is **2.983157%**. The practical layout-gain screen **did not pass**. Session ratios are 0.973614561, 0.961260205, 0.977617954, 0.981693410, 0.978961967, 0.980182884. An unfavorable performance result is not repaired by extending or selecting timing blocks.

| Service ratio | Geometric mean |
|---|---:|
| layout | 0.975530833 |
| D_QB | 0.973607050 |
| D_PQ | 0.945654464 |
| CQB_R | 0.458984574 |
| MQB_R | 0.446870617 |
| MPQ_R | 0.444927825 |
| CPQ_R | 0.470497250 |
| AA | 0.998819659 |

`layout` is C_QB / dual-C_PQ; `D_QB` and `D_PQ` are same-layout M/C ratios. The `_R` columns divide each arm's service time by R. Service includes fresh context setup, prefill/decode, state transfer/reconciliation, synchronization and teardown. Model load is reported separately: 26.557655 seconds across six sessions. All measured and warmup service totals and component totals are in INDEPENDENT_COST.json. These ratios are paired finite-panel summaries, without a population confidence interval.

## Complete accounting and retained failures

The append-only new study ledger reserves **2862 work credits**, including 846 development credits. It records 2573 audited complete model requests, 22 standalone operator replays and 130 extra shadow decodes. Supervised wall time is 24003.562 seconds, including host auditing and protocol waits. Reservations and actual calls are different quantities. Failed processes may have additional partial work; missing telemetry is not treated as zero. Historical PR151/PR156/PR159 records remain separately retained and are not reset or credited back.

FINAL_EXECUTION_SUMMARY.json additionally indexes every retained pre-transport preparation, build, test, audit and supervisor operation receipt with its elapsed time and exit code. Nested/overlapping operations are not summed into a misleading wall total. Archive/upload/download costs are preserved in the separate delivery metadata produced after scientific timing finishes.

There are 6 failed native execution units. Complete per-slot dispositions distinguish audited completion, worker completion rejected by host audit, possible partial starts, and unstarted slots. The baseline numerical failures, build-only candidates, host freeze/schema corrections and failed preparation/transport operations are also preserved even where they did not create a failed native unit. See LEDGER_AUDIT.json, ENGINEERING_CHANGES.jsonl, operation receipts and all source versions.

## Delivery

Independent draft result PR: https://github.com/leecdiang/HeteroSpec/pull/162. [Complete evidence release](https://github.com/leecdiang/HeteroSpec/releases/tag/rtx-llama-repair-v1-evidence-20261102) is published in the unchanged private repository. All **259 shards and 123,210 members** passed local readback and fresh authenticated remote download with exact archive/member inventory, byte counts and SHA-256 checks. Separate transport metadata and its final receipt were also uploaded, freshly downloaded and verified.

[RAW_ACCESS.json](https://github.com/leecdiang/HeteroSpec/releases/download/rtx-llama-repair-v1-evidence-20261102/RAW_ACCESS.json) SHA-256: `ba4999f8d8a526aa209a181ab7a0d96dd5a7cc5bd9c4e9e048e12d5dc1089f86`. Compressed raw/source archive size: **107,273,440,845 bytes**. [REMOTE_READBACK.json](https://github.com/leecdiang/HeteroSpec/releases/download/rtx-llama-repair-v1-evidence-20261102/REMOTE_READBACK.json), [delivery metadata readback](https://github.com/leecdiang/HeteroSpec/releases/download/rtx-llama-repair-v1-evidence-20261102/DELIVERY_METADATA_READBACK.json), FINAL_DELIVERY.json and delivery_final/ provide the final attestations. RESTORE.md gives independent reconstruction commands. No model weights are redistributed.

The sealed scientific snapshot remains `70086c63af202cd844a3062eff3929218152f73c`; its raw index binds actual executed source bytes. The later Git byte-fidelity commit `e11d2b75d82422409ba2b701aa38c59f36acc50b` disables EOL conversion and restores three tokenizer evidence receipts hidden by the pre-existing token* ignore rule. All 202 scientific receipts and staged study source bytes were checked. This changed no working numerical source, frozen candidate, original reference, panel, raw capsule or scientific result. Earlier commits, failed delivery checks and network attempts remain retained in the transport metadata and delivery records.

FINAL_EXECUTION_SUMMARY.json remains an immutable creation-time scientific report; FINAL_DELIVERY.json supersedes its then-pending delivery field. Same-host upload/download checks establish byte delivery, not third-party scientific replication. No merge or manuscript edit is performed. PAPER_ADDENDUM.md retains the supported scope and limitations, including the failed practical performance screen.
