# Native q8 capability and descriptive M2 pilot on Linux/A5000

All finite qualification gates passed, followed by24/24 frozen workers:64 live measurements +32 primers, and a separate32 target-replay measurements +16 primers. Native execution ended2026-11-08 18:49:01 UTC (2026-11-09 02:49:01 Asia/Shanghai). There were no timed worker failures, selected native retries, extra rounds or576-test confirmation.

The actual k7/q8 path works and enables packing at the intended boundary, but these four exposed inputs do not show a profitable width increase. Read same-k/same-projection before cross-k totals: at k7, LOCAL saves0.171% with loop4 and0.367% with packed; packed saves1.633% in W and1.826% in LOCAL. At k3, corresponding LOCAL savings are0.350%/0.156%, and packing savings1.176%/0.984%. These small differences are descriptive, without confidence intervals or a population claim. k3 VERIFY is a negative control with wide packing inactive; packing can still act during prefill.

At fixed cut/projection, every live k7 arm is14.06–15.04% slower than its common-reserve8 k3 counterpart. LOCAL-packed goes11.878694s →13.548505s (+14.057%). On the separate common-tape target replay it goes4.100639s →4.535729s (+10.610%). All observed live proposal operands match the independently produced position-indexed tape, including primers. This is finite observed fidelity, not a guarantee for new inputs. Free replay has zero draft calls and retains both resident models/contexts; producer cost is separate.

|Arm|Live service total,8 measurements (s)|Replay service total,4 measurements (s)|Live native process sum,2 workers (s)|
|---|---:|---:|---:|
|W_L4_K3|12.038851|4.171876|124.682|
|W_P_K3|11.897263|4.118381|124.294|
|L_L4_K3|11.996725|4.156610|125.012|
|L_P_K3|11.878694|4.100639|124.466|
|W_L4_K7|13.824167|4.667288|127.974|
|W_P_K7|13.598468|4.565221|128.573|
|L_L4_K7|13.800486|4.640929|127.761|
|L_P_K7|13.548505|4.535729|127.040|

Each live arm emits1024 tokens across8 requests. k7 reduces verification cycles288 →172, but target physical rows increase1868 →2092 (+11.99%), as do live draft rows. VERIFY rows alone increase1152 →1376 (+19.44%). Accepted/proposed changes736/864 (85.19%) →852/1204 (70.76%); proposals not accepted increase128 →352, including unconsumed near-cap work rather than only incorrect proposals. Fewer cycles or more accepted proposals alone therefore do not establish profitability.

## What actually executed

k and all acceptance/correction/bonus/trim indexes are native parameters. Actual target reservation is8, with real row buffers and masks. Both k3 and k7 share it; original k3/reserve4 and scalar UB1/reserve1 R remain unchanged. Both models stay the exact original Qwen3-8B/0.6B Q8_0, with F16 KV/C1024/noFA, target UB32, draft prefill UB4 and two threads on the same approved single GPU. Here q8 is verification width, not weight quantization. No global q8→q4 decomposition occurs.

Live LOCAL-k7 physically executes172 width8 VERIFY calls. SIMPLE-k7 executes170 width8 calls plus2 width2 and2 width6 calls (two genuine2+6 boundary splits). LOCAL-k3 executes288 width4 calls; SIMPLE-k3 has286 width4 and4 width2 calls. Replay has exactly half these two-round counts. Every originally requested row remains owned and checked.

Fixed cache source and native evidence establish256-token extent padding. The separate geometry cases at positions255/767 require SIMPLE1+7 while LOCAL keeps8; at these crossings W-packed has no packed nodes and LOCAL-packed has253 per case. Eligible packed nodes have ne1=4/ne2=2, Q8_0 weights/F32 activations and actual GPU buffers. Both projection cores preserve all requested vectors and active target KV/frontier against R. These are scheduled graph/device descriptors and physical counters, not CUDA kernel-symbol profiling.

## Qualification and scope

QUALIFICATION_SUMMARY.json binds all original proofs: four k3-reserve8 bridges;40 natural root jobs including a genuine newly evaluated8B EOG,48 heavy/clean natural pairs including per-arm cap1;72 candidate geometry cases against18 independent scalar-R cases;96 controlled replay heavy/clean fixture pairs covering every rejection rank, accepted-suffix caps, bonus and cap1; five specific native negative checks; and16 owned-tape replay heavy/clean pairs. All passed their unchanged full-vector/active-target-state criteria, frontier/pending/commit/rollback checks and clean endpoint/trace/API/physical bridge. Live draft rollback bounds are checked; no independent full draft-KV numerical oracle is claimed.

Natural scope includes CAP128 on the first short root, fixed CAP32 short/long/tail roots and a genuine EOG diagnostic. Exhaustive rejection ranks are controlled replay fixtures; live observed branch coverage is reported separately. This is finite qualification, not every possible input/context boundary. Every timed request checks R endpoints, independently reconstructed trace, actual work, clean APIs, graph reuse and fixed module/capability bindings; it does not redo full internal-state comparisons inside each timer.

Four roots are the first four in immutable M1 order, with two distinct old primers: exposed deployment-transfer inputs, not new blind samples. The two live order rows reverse all arm precedences/complement positions and reverse the request order; they are not a full eight-row Williams/neighbor balance. Replay has one descriptive round. No new target-only M arm is in this pilot, so it makes no new speculation-versus-M claim. No reserve4 historical timing is pooled.

## Complete costs, failures and reconstruction

All M2 epochs01/02/03 retain122 reserved workers (117 complete, five expected native rejects),587 logical requests and578884 conservative reserved rows. The PR197 cumulative envelope, including original8B/M1 and failures, is1826/2048 requests and3021131/8000000 reserved rows. Reserved bounds are not actual work. Direct M2 counters report100776 target rows and52915 draft rows; unchanged scalar-R materialized-token/UB1 metadata derives8301 rows separately. Failed negatives without completed row receipts are unknown, not observed zero.

Known native-worker walls sum13437.936s (3.733h), including native integrity/hash/load/observers/requests; this is not GPU kernel time. Compile/link phases total25.491s, with build-inclusive staging time unknown. Timed live native-process/adapter sums are1009.802/1185.911s; replay476.532/564.910s. These clocks overlap and cannot be added. Cold worker strings include two primers and all requests, with warm OS file cache. First completed request is not TTFT. Per-worker setup/model-load/first-result/burst/request strings and sampled memory remain in the complete archive. Memory is selected-GPU total-minus-free at2s sampling, including driver/reserved bytes, not exact per-process peak.

Retained non-numerical failures include driver01's mistaken q4 wide-marker reviewer gate (corrected structurally without changing tolerances/binaries), the deliberate between-job mutex handoff before source03's true256-boundary probes (no active worker interrupted), and an auxiliary post-observer declaration launch race (continued with an explicit wait, zero native work). Post-panel cost-schema adaptation and a privacy-scanner placeholder false positive also remain recorded; both were data-only and caused no GPU rerun. Expected native rejects verify unsupported k, insufficient reserve, unknown fields, ignored context and transient capacity with their specific reasons. All charges remain; no failed version is overwritten.

The archive contains2963 sanitized text records (1842968603 expanded bytes), all source/build/module/config/job/receipt/state-comparison/failed-version records, plus raw/derived SHA commitments.7656 private vector/KV captures total32581556480 bytes and passed two complete byte reads. Raw numerical payloads, weights, full vocabulary, compiled binaries and unrelated company inventory are not redistributed. Historical R operands were reverified at use against the published predecessor indices; the new private-capture count covers the M2 epoch folders, not a new complete byte read of every predecessor file.

Reconstruct archive/scientific-records.json.gz in PARTS.json order, verify part and joined SHAs, then run ../replay_public.py with a fresh output directory. The public helper verifies the whole stream and exactly recomputes all144 timed/primer receipt statistics/memory from the fixed archived analyzer; it makes no new GPU allocation/numerical qualification claim. ../width_analysis.py reproduces the predeclared cross-width tables using TEXT_INDEX raw commitments for sanitized job sizes. See ../REBUILD.md and ../rebuild_materials_20261108 for exact source epochs, thin Git history and prerequisite. Historical M1-labelled construction statuses/console prefixes remain unchanged; later native proof/freeze and terminal status establish qualification.

LOCAL_READBACK and LOCAL_TRANSPORT_STREAM_CHECKED bind full server and transferred text reads. Public readback/statistical proofs are added separately against immutable artifact commit(s), without rewriting archive bytes. Main PR205/206/208 stay complete, read back and unchanged. The separate Q32 result in ../../Q32/results_admission_20261108 records exact model download/hash and C1024 allocation/short-forward smoke only, with no Q4 numerical qualification or performance panel. No manuscript, merge, Release, rental or data deletion.

Public closure passed: [PUBLIC_VALIDATION.json](PUBLIC_VALIDATION.json) binds immutable artifact commit128047ee0c3228771f81127dbc615a03bb6a5860. All104 public files and2963 expanded records match complete byte commitments; all144 timed/primer receipt statistics reproduce byte-identically. The predeclared width tables and complete cost addendum also reproduce byte-identically from the public derived archive. [PUBLIC_READBACK.json](PUBLIC_READBACK.json), [PUBLIC_STREAM_CHECKED.json](PUBLIC_STREAM_CHECKED.json), [PUBLIC_STATISTICS_REPLAY_CHECKED.json](PUBLIC_STATISTICS_REPLAY_CHECKED.json) and [PUBLIC_ADDITIVE_REPLAY_CHECKED.json](PUBLIC_ADDITIVE_REPLAY_CHECKED.json) preserve those checks. These are data-only checks, not new GPU/raw-state qualification.

For additive replay, use ../replay_additive_reports.py --archive /path/to/archive --m2-source /path/to/published/M2 --expected-dir /path/to/published/results_pilot_20261108 --out /path/to/FRESH-additive-replay. It verifies the complete public stream, binds only redacted workspace paths and raw/derived SHA identities, and leaves numeric fields and fixed analyzers unchanged.
