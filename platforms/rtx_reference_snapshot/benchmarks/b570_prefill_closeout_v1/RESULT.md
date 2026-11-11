# B570 final draft-prefill submission closeout

**NO_ESTABLISHED_PRACTICAL_PANEL_BENEFIT**

On the four exposed PR134 inputs, the complete fresh-context service ratio SUBMIT / mean(BASE_A, BASE_B) is **0.99916130**, a **+0.0839% service reduction**. The registered practical screen **does not pass**. SUBMIT / contemporary R is **1.20367799**; dual BASE / R is **1.20468836**. SUBMIT remains slower than contemporary target-only R.

## Frozen intervention and execution

Study UUID `87f1b888-efb4-4723-86f2-453333ebd9f5`. PR141 design head `03cc11662f0ff21514efd40e9a09d4c7e1d2c672`; source/manifest checkpoint `93ab8d62c24ed7bf60333b8ee196893d1991d868`; first-native registration freeze `a173f09c24e1af815257db350c1d64df87f09c15`; qualification-containing timing freeze `501ee5d46bbc386ca7a0462826126f1d356c5562`. Each process receipt identifies its actual freeze. All commits precede their respective native stages.

Only draft-prefill submission changes: one logical llama_decode instead of one call/synchronization per prompt token. Physical ubatch1, threads8, target QB, original numerical DLLs, models/tokenizer, final-token output flags, positions, KV/pending state and cap64/natural EOG are retained. BASE_A/B invoke exactly the same branch. Both weights remain resident for R. There is no target-prefill change or CPU1 combination. Source and observer changes are separated in SOURCE_AUDIT.md and request_observer_diff.patch.

All **156 registered requests /9 model processes** completed: 4 E0 calibration, 24 E1 qualification, 64 matched warmups and 64 measured requests. Every warmup matches its own input and arm and immediately precedes its measurement. All process exits and normal cleanup were observed. No failed slot, automatic retry, replacement run, outlier deletion, interim subset estimate or success-dependent extension occurred.

## Numerical, observer and physical geometry gates

The original PR134 manifests authenticate 914 historical vectors, including 346 original QB vectors. PR135 attempt2's 346 QB vectors and endpoints/cycles were recovered and rechecked before execution. Original endpoints remain /38 64/CAP, /65 53/EOG, /115 41/EOG, /127 64/CAP.

Fresh E0 compares 62 full vectors with the original /42 bridge. Fresh E1 independently rechecks **914 vectors**: 222 R, 346 BASE and 346 SUBMIT, including rejected verification rows. Capture/count native endpoints and complete cycles match. BASE/SUBMIT's ordered prefill QK and mask/key metadata sequences match, with one observed physical q1 per layer/ubatch and exactly prompt_length *28 draft-layer QK and mask observations in each capture. Consecutive positions, final-token flags and prefill KV endpoints are checked. All timed IDs/EOG/length/terminal/stop and speculative cycles match their original references. Callbacks are absent from all timed requests.

The geometry evidence is shape/source metadata plus complete finite-path full-logit and state equality; actual GPU mask values are not independently read back. Physical microbatch observations occur outside timing. Caller-count reduction is not a measured reduction in GPU operations or a GPU critical-path fraction.

## Complete-service panel

| Input | SUBMIT / dual BASE service | Service reduction | SUBMIT / R | dual BASE / R | A/A imbalance |
|---|---:|---:|---:|---:|---:|
| HumanEval/38 | 0.99753141 | +0.2469% | 1.158866 | 1.161734 | -0.2882% |
| HumanEval/65 | 0.99722051 | +0.2779% | 1.153750 | 1.156966 | +0.3689% |
| HumanEval/115 | 0.99918494 | +0.0815% | 1.280041 | 1.281086 | -0.0297% |
| HumanEval/127 | 1.00271787 | -0.2718% | 1.226513 | 1.223189 | -0.0295% |

Equal-weight geometric mean over all 16 input/session blocks: `0.999161301690`. Per-session ratios: `[1.0005918808834429, 0.9988269373238996, 0.9994477598680488, 0.997780703564486]`. Largest input-aggregate absolute A/A imbalance: **0.3689%**. Frozen required reduction: **2.0000%**, together with SUBMIT faster in every session aggregate. Request-only ratio, a secondary window: `0.998792623549`.

The primary timer begins before fresh target/draft context creation and graph reservation and ends after context destruction. It includes prefill, generation, native logits/sampling, inherited host/state work, synchronization and teardown. Model loading is separate. Reference comparisons and output-file writes follow the timer. No per-request Python execution or observer is inserted. The outer Python process only supervises the whole native worker and enforces fixed safety reservations. Secondary phase fields sum the inherited decode/synchronize spans; batch construction and loop overhead remain in complete service rather than those sums. No independent whole-prefill interval or GPU critical-path time is inferred. COST_WINDOW_DEFINITIONS.json gives the exact overlapping boundaries.

This is a descriptive, fixed finite panel on one B570/driver/model/runtime configuration. Four exposed inputs support no new-input or length-generalization claim, population confidence interval, equivalence result or fully optimized software ceiling. Machine background exclusivity and cold-driver cache behavior are not established.

## Historical records and cost accounting

PR135 attempt1's failed observer run, CPU-thread negative study and original ledgers are unchanged. The recovered attempt2 time-0 has 3 warmups +6 measured records and a complete 163.5546413-second parent receipt. Time-1 has 3 warmups +2 measured records but no exit/process receipt, with 81.3101785 seconds of recorded service windows. Its full parent cost/exit/cleanup is unknown. Time-2 is absent. These observations remain historical and are never pooled into this study or used to complete its old UUID.

Receipt-backed earlier cumulative cost is 3435.1001972 seconds, with the additional unreceipted process explicitly unknown. New worker wall, model loading, complete service, request-only, synchronized phase windows, wrapper/preflight and conservative owned host wall remain separate in ALL_COST_WINDOWS.csv and CLOSEOUT.json; overlapping windows must not be summed. Preparation/compiler/auditor work is included in conservative owned wall rather than invented isolated active CPU/GPU time. Packaging and final integrity audit costs have separate receipts.

## Disposition and evidence

Retain the original QB/thread8 baseline; this screen does not establish a practical improvement. The small observed effect remains unresolved and does not establish equivalence. This final bounded study closes the software-policy branch. No additional width sweep, target prefill, persistent-context policy, new shader, k tuning, CPU8, QH, M4/358H, hardware or RTL run follows automatically. No historical paper/reference edit or arXiv submission is performed.

The result PR contains native result JSON, all process receipts, complete slot disposition, phase/cost tables, frozen source/order/asset hashes, raw manifests, independent raw-to-normalized reconstruction and the original PR141 estimator result. COMPACT_EVIDENCE.zip retains detailed native geometry/progress/log files. HISTORICAL_COMPACT.zip preserves recovered prior records. LOCAL_RAW_ARCHIVE.json locates and hashes the complete new raw-vector archive on this machine; original PR134 raw vectors remain separately available at their recorded paths. This is local full-byte authentication and independent computation, not third-party or external raw-data certification. See REPRODUCTION.md and PAPER_ADDENDUM.md.

Only the nine native model workers have individual process receipts. Compiler/control/auditor/coordination costs use conservative owned wall and command-level evidence; individual helper descendants were not separately counted. The 128-other-process reservation is not independently reconciled. RESOURCE_RECEIPT.json records this limit on the full resource-accounting claim; the complete scientific panel and native safety/accounting checks remain separately reported.
