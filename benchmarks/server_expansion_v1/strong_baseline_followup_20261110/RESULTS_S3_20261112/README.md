# Recovered S3: complete, no new GPU requests

Original run **sb217-s3-20261110T1842Z-01** completed 2026-11-11 00:31:46 UTC (08:31:46 Beijing). Controller closed normally five seconds later; the GPU/coordinator/lifecycle/activity flocks used by qualification and formal phases are released. The server subsequently rebooted. Original PIDs and the historical PR title are not evidence of a live process. Recovery on 2026-11-12 only reads existing results and computes saved-data checks; it does not restart the runner, request a GPU, repeat S1/S2/B2 or create a successor experiment. The original STATE remains unchanged.

## What was compared

One A5000, Qwen3-32B-Q4_K_M mixed Q4_K/Q6_K weights; target-only greedy, k=0, no draft, WHOLE/SIMPLE, n_ctx1024, n_ubatch32, reserve32, two native CPU threads, F16 KV, common CUDA graphs off and flash attention off. G is graph-level REF1 loop; B is backend-internal REF1 loop with shared batch quantization; C is independent-channel group. B keeps the original per-column scalar-dot arithmetic. The primary question is C versus stronger B. This is not the RTX dual-four-column kernel's cross-GPU replication, live speculation, concurrent-request throughput or long-context evidence. A legacy proposal_mode=live field is inert with draft=false/k=0; no proposal tape/draft was executed. Native receipt arm=phase is a legacy name: actual arms are verified from WORKER/JOB plus native capability/selection.

Inputs were prospectively selected before new model outputs: six code and six math roots, prompt lengths39–187, cap128, frozen template and token IDs. All12 naturally reached CAP128; none had a natural early EOG. No root was replaced, truncated after observation, padded or added for precision. These inputs are new relative to the registered exposure audit, not claimed unseen in model training or universally semantically unexposed. Fixed prescribed orders and all unfavorable smaller effects are retained. A single matched warmup per fresh process is not proof of general steady state.

## Complete panel and statistics

144 fresh formal processes each execute one full warm, reset and measured request:144 warm +144 measured. From all288 original receipts, an independent Node implementation rebuilds rows before reading saved converted rows/analysis, verifies exact jobs/order/outputs/clocks/physical work, then cross-checks the frozen Python analysis. Twelve root units, not48 independent round units: average four log ratios within root, then equal-weight roots. Bootstrap resamples whole roots separately within6 code and6 math,20,000 replicates, seed20261110, linear R7 percentiles. C/B uses95%; B/G and C/G use97.5% each.

| Comparison / denominator | Equal-root time ratio | Frozen interval | Ratio of measured totals | Numerator / denominator seconds |
|---|---:|---:|---:|---:|
| C/B, primary, denominator B | 0.984863743 | 95% [0.982147937,0.987720995] | 0.983809466 | 358.924859316 /364.831679008 |
| B/G, denominator G | 0.956854868 | 97.5% [0.949633995,0.964364397] | 0.954322329 | 364.831679008 /382.293977613 |
| C/G, denominator G | 0.942371667 | 97.5% [0.932367729,0.952869302] | 0.938871341 | 358.924859316 /382.293977613 |

C reduces service time versus B by **1.514%**,95% interval corresponding to1.228–1.785%. This meets the protocol's finite-panel1% threshold; it does **not** meet the project's5% goal. Neither5% nor1% is a TPDS acceptance threshold. C/G's5.763% cannot substitute for C/B. All48 observed C/B round pairs favor C; the narrow finite-sample interval does not establish a universal hardware/model/population effect.

| Root | Prompt tokens | C/B | B/G | C/G |
|---|---:|---:|---:|---:|
| CodeContests/train/161 | 137 | 0.980810 | 0.947102 | 0.928927 |
| CodeContests/train/240 | 102 | 0.982682 | 0.954164 | 0.937640 |
| CodeContests/train/173 | 185 | 0.977226 | 0.939482 | 0.918087 |
| CodeContests/train/279 | 187 | 0.977239 | 0.938973 | 0.917601 |
| CodeContests/train/99 | 41 | 0.991689 | 0.971713 | 0.963637 |
| CodeContests/train/93 | 39 | 0.991617 | 0.973171 | 0.965013 |
| MATH/algebra/train/27 | 45 | 0.990890 | 0.970290 | 0.961451 |
| MATH/algebra/train/20 | 61 | 0.987859 | 0.961563 | 0.949889 |
| MATH/algebra/train/4 | 93 | 0.984027 | 0.953019 | 0.937797 |
| MATH/algebra/train/0 | 126 | 0.980482 | 0.946720 | 0.928242 |
| MATH/algebra/train/25 | 51 | 0.989042 | 0.967772 | 0.957167 |
| MATH/algebra/train/46 | 79 | 0.984959 | 0.959154 | 0.944728 |

PER_ROOT.csv and INDEPENDENT_REPORT.json include every root and all four paired rounds; no root below1% benefit is suppressed.

## Numerical evidence and its depth

Qualification completed66 fresh processes/135 requests:24 independent R requests (two/root),36 old six-boundary G/B/C heavy+clean requests,75 new-root bridge/calibration requests. All24 R runs froze oracles before a candidate ran. Original checks compared every generated-step full151936-dimensional finite F32 frontier and all64 layers' active F16 K/V plus frontiers/state lifecycle using strict bytes, not only argmax or final tokens. G/B/C heavy bridges use those complete readers. Old fixtures cover EOG/cap/reset, pending, capacity and physical extent behavior; the inherited S1 certificate covers the registered descriptor/geometry/overflow/crossing requirements.

Clean/formal requests verify exact input, complete generated tokens/EOG flags, qualified semantic trajectory, actual per-call widths/positions/extents/requested-output masks, reserve32, no draft or online reference/state/context/capture work, plus **terminal full frontier and all64 active KV** after the timed service. The final emitted token remains pending (not yet materialized in KV). They do not recompare every intermediate vector/KV byte on every timed request. Native code materializes and scans all required full output vectors. Recovery verifies all423 original receipts,210 exits/launch identities,66 comparison-file hashes,12 repeated-R check hashes and certificate/oracle hashes; it is not a new GPU qualification.

All20,946 private numerical payloads (352,859,196,146 bytes) remain readable and match their original SHA-256/size inventory. Full model and3,432 compiled closure files also match;89 frozen source and220 other frozen files match. The recovery integrity scan took469.671s at low CPU/I/O priority. It does not rerun the original numerical reader comparisons. The public9,892,511-byte text archive has8,364 payloads and exact numeric inventories, but does not distribute raw numerical captures. Public text/statistical replay is not independent GPU reproduction or an independent repeat of all heavy bytes. The report field unavailable_numeric_payloads=20946 means withheld from the public archive, not missing on the original host.

## Costs from this same panel

The primary native interval starts before full context reset, includes prefill/decode, all required owned outputs and final synchronization, and ends before post-service terminal-state export/semantic-tape/receipt serialization. Model loading/context provisioning are outside this resident-request interval. It is not cold process startup latency.

| Arm,48 measured requests | Service s | Prefill s | Decode s |
|---|---:|---:|---:|
| G |382.293978|161.324593|216.714533|
| B |364.831679|143.926569|216.663232|
| C |358.924859|137.984135|216.689813|

C minus B is−5.906820s service,−5.942435s prefill and+0.026580s decode. B prefill is39.45% of service; its4.13% prefill reduction is diluted to1.619% pooled service reduction (a different weighting from the1.514% primary estimate). This supports descriptive transmission mainly through prefill. It does not isolate quantization, dot or launch time. Same-panel application counters show B/C have equal quantized rows and quant calls; C has fewer scalar-dot dispatch and application launch calls. Counters are not isolated timings; opaque library internal launches remain unknown.

Actual source audit establishes reset/planning/prefill/decode/owned host-copy as sibling subintervals here. first_call_plan is already inside planning. Prefill/decode include llama_decode, batch-free, synchronization and backend work/output movement. output_copy is a later **host-logit to caller-owned-vector** copy, not total D2H. Stop/argmax/finite scan/commit/batch allocation/bookkeeping/final gaps are not individually timed; stop_separate_s=null. No S2 or other experiment timings are spliced into this cost accounting. COST_AUDIT.json records the residual and exclusions.

Qualification full-worker callers sum8058.630s; formal callers9385.567s;210-worker sum17444.197s. Entire controller phase wall is20938.934s (~5h49m), including checks/gaps; these are enclosing intervals, not additive components. Formal model-load totals492.627s and pool-setup7.316s are nested inside worker callers, outside service. launch_to_exit_observation includes post-exit module/budget validation and polling, not exact process lifetime; measured phase1_main_to_result is cumulative since native main, including warm and prior exports. Fixed3s gaps occur after callers; total210 gaps630s. Archive-export timing was not separately recorded; do not invent it.

All5,245 original resource samples record actual NVML free. Sampled minimum free5,421,137,920 bytes, maximum used19,865,272,320 bytes; these are not continuous peak measurements. Original run launch/completion times fit its registered allocation. Current free VRAM and that old window do not authorize another request; latest recovery permission explicitly excludes one.

## Full ledger, failures and identity

Same canonical32B journal hash8283a7977c020987a2b1153c901674f19960ea9087d114226c283b836b4dad09 has3,846 events, verified lifecycle/approval prefix/hash chain. **1,796 cumulative requests /771,465 reserved rows** = original514 +859 S1/S2 (including four charged startup-failure slots) +423 S3. S3 adds93,753 rows; all135 qualification +288 formal are COMPLETE. Its439-slot ceiling leaves16 unused failure slots, never treated as retry permission; no S3 failure/native retry occurred. No8B quota transfer or new ledger was used.

The original514 is fully recovered, not just trusted as a scalar:512 requests/651,898 rows in the original356-event ledger plus2 requests/128 rows in the prior diagnostic ledger. All178 reservations in the512 ledger have terminal outcomes:169 COMPLETE and9 FAILED worker outcomes covering15 reserved requests, including five named negative probes. Those FAILED labels are not all unexpected model failures. Both complete sanitized ledgers and inheritance receipt are included; no reservation is refunded. The four later S1 startup-failure slots remain in the main journal. All original records and prior results stay intact.

Design head c85b98636d5e0a7d9c367be8f3447b0799d12a78; public recovery began at4fe337a8ff349d547023f9dd60b8e114e5323207. Actual prospective S3 source/core freeze is commitfd727140e07e942d09e715e7cca14abe86588873, RESOURCE02. Pristine R source0cae43063cf15170e91a2ff4d034da0ecef4a1b2, R ELF SHA2565c23a74ffaeec433f9dbc37ce1e014f374839b84da0eb19e4cd36146cc7d5199. Shared G/B/C S3 ELF fc2190a8fee10869f1f98a061bf6d1d1484b115fe3800d3aee6020229b135a58; unchanged numerical objects, common opportunity. Exact GGUF19,762,149,024 bytes, SHA256efd971561896866f0e910cce52761ca77b1b138090c7f15fe284676d57d1f689. Manifest649f452a20e3070f2a1eb9800419eb8c9c6062b85b7353cf1f3b781deb139b7b; rootsa2ab60ee871fac53ec36c8bbae08fd0cb06e3efe046083b34d3351783288c771. Full identities and loaded module receipts are retained. See the existing source-reconstruction archive and735-step recipe for source material; its preflight is not completed cold compilation or another qualified ELF.

## Claim–evidence–limit

| Claim | Evidence | Limit |
|---|---|---|
| C retains a small service increment over stronger B here |12-root paired primary1.514%,95% interval; full prescribed panel|One A5000, one mixed-Q4/Q6 deployment, short prompts/C1024/CAP128, common graphs off; no5% claim|
| Strong B explains much of G→C gain |B/G0.956855 versus C/G0.942372, same complete services|Do not report weak-G effect as C/B; no isolated causal kernel timing|
| Original numerical/state qualification passed |Repeated independent R and complete heavy vectors/active KV; clean bridges and certificate|Timed requests have shallower intermediate checking; public bytes do not repeat GPU qualification|
| Same-panel gain mainly appears in prefill |Prefill−5.942s, decode+0.027s|Backend substage times unmeasured; no imported S2 cost stack|
| Broader RTX/live/concurrent/long-context claims are not established |Those conditions absent from this panel|No claim of new RTX kernel cross-GPU reproduction or live-k7 speedup|

## Saved-data reproduction

Strictly replay RESULT_S3_TEXT.tar.gz with the parent execution_s3_v1/deliver.py replay entry and transport SHA53c9a894f9c99dda7a483870f3f2835311ee273a63ae19ae8344443169c91989 into a fresh directory. No CUDA/model execution occurs. Then run the accompanying independent_receipts.js on restored text and a fresh report directory; optional original study root enables original path-sensitive SHA checks in memory. Public transport/member hashes and all raw receipt statistics are checkable without that private path. Public-delivery closure is established only by the separately added PUBLIC_REPLAY_PASS.json for actual anonymous immutable download/readback and independent public replay, not by the local replay. No merges, Release, paper edits, second device or new measurements are part of this delivery.

Actual anonymous closure passed for all28 files at immutable commit64a3d1d0a35b2b81903e915746e5f40957e8b968. The downloaded archive passed the original strict Python member/ledger/288-operation analysis replay and the independent Node receipt reconstruction/root bootstrap/history audit. The public-only mode explicitly cannot repeat788 path-sensitive original hashes without the private study-root substitution; those checks passed separately in the host recovery. It still verifies all8,364 anonymized member bytes and the complete public journal hash chain. An initial history-reader layout lookup failed before any report; a read-only view to the restored public archive supplied its documented ORIGINAL_TEXT layout. No experiment or numerical data were changed.

With the public result files in `$PUBLIC`, restore directly to its required fresh ORIGINAL_TEXT subdirectory and use fresh output paths:

```sh
python -B "$PROTOCOL/execution_s3_v1/deliver.py" replay \
  --archive "$PUBLIC/RESULT_S3_TEXT.tar.gz" \
  --sha256 53c9a894f9c99dda7a483870f3f2835311ee273a63ae19ae8344443169c91989 \
  --out "$PUBLIC/ORIGINAL_TEXT" --report "$NEW_PYTHON_REPORT"
node "$PUBLIC/independent_receipts.js" "$PUBLIC/ORIGINAL_TEXT" "$NEW_NODE_REPORT_DIRECTORY"
node "$PUBLIC/independent_history.js" "$PUBLIC" "$NEW_HISTORY_REPORT"
node "$PUBLIC/recompute_costs.js" "$PUBLIC/ORIGINAL_TEXT" "$NEW_COST_REPORT"
```

`PROTOCOL` is the parent strong_baseline_followup_20261110 directory from this PR. These are saved-data CPU entries only. The original runner remains closed and its STATE is preserved; any further measurement needs a separately authorized successor protocol.
