# B570 PR146 native reproduction closeout

The scoped Qwen3 GQA/AV-preserving path now has a clean source build, a real request-derived stage fixture, historical complete-request replay, and successful execution from a freshly copied directory on B570. This closes the B570 native-delivery work requested by PR146. It adds no performance result and leaves PR143's QB/thread8 baseline and negative practical-benefit screen unchanged.

| Deliverable | Observed result | Evidence |
|---|---|---|
| Upstream/source recovery | All 3,545 upstream files authenticated at `0cae43063cf15170e91a2ff4d034da0ecef4a1b2`; PR131 header, PR132 Vulkan source and PR133 bridge match exact Git archives | `SOURCE_INPUTS.json`, `SOURCE_RECOVERY.json`, `UPSTREAM_COMPARISON.json` |
| Clean native build | All numerical DLLs and 147 shader translation units built from source; no old object/library dependencies | `BUILD.json`, `RUNTIME_A2.json` |
| Real stage fixture | HumanEval/115, first QB VERIFY, layer0, key512/q2, 32/8 GQA; raw Q/K/V/mask spans and QK/softmax/AV/final readbacks | `REAL_STAGE_FIXTURE.zip`, `receipts/STAGE_AUDIT.json` |
| Stage replay | 16 exact stage comparisons: q2 PQ/QB and first-query q1 PQ/QB controls; causal mask exposes 350/351 keys | `receipts/STAGE_AUDIT.json` |
| Four-input ordinary smoke | All 12 R/PQ/QB requests match PR134; all 914 corresponding logits vectors, endpoint/stopping fields, cycle traces and per-decode descriptors match exactly | `receipts/SMOKE_0_AUDIT.json` through `SMOKE_3_AUDIT.json` |
| Capture control | HumanEval/115 with raw capture enabled/disabled: all 175 logits vectors and complete endpoint/state match | `SUMMARY.json` |
| Fresh-directory execution | 1,207 copied files hash-verified; copied runtime passes stage replay and a three-request HumanEval/115 replay (175 vectors) using copied references | `receipts/FRESH_COPY_INTEGRITY.json`, `FRESH_STAGE_AUDIT.json`, `FRESH_REQUEST_AUDIT.json` |
| Historical prefill audit | PR143 read-only audit passes with its declared limitations; all 156 old requests reconciled, no rerun | `PR143_READ_ONLY_AUDIT.json` |

The ordinary panel is HumanEval/38,65,115,127, with output lengths 64,53,41,64 and stops CAP,EOG,EOG,CAP. PQ and QB expose the natural q2 geometry in all 36 target layers. There are 346 paired PQ/QB complete vectors, plus the separate R vectors; comparing all three arms to their respective historical files gives 914 vector comparisons. Matching endpoints does not imply HumanEval functional correctness.

## Identity and execution scope

The source/plan froze at `bcfea0627d335c9db5992e1e309bde53d5685cdc`. The diagnostic correction froze at `3377b236` before its retry. This is newly compiled runtime qualification, not a claim that historical DLL bytes were rebuilt identically. The correction changed only the capture harness/supervisor; all five numerical DLL hashes remained unchanged. Actual loaded numerical module paths/hashes were checked for every worker, including the fresh directory. Complete loaded-module inventories retain the system Vulkan loader, Intel driver and loaded third-party Vulkan layer identities.

The request contract is exactly PR134's Qwen3-8B/0.6B Q8_0, F16 KV, greedy k=1, ctx1024, physical q1 prefill, max64/natural EOG, target ubatch1 for R and4 for PQ/QB, draft ubatch1, and context thread settings8. **Both PR134 models are offloaded to B570.** This request reproduction must not be described as a rerun of PR143's later CPU-draft service experiment.

The real fixture is a **new capture**, not PR132's historical synthetic operator fixture. q1 is the first-query slice of the natural q2 capture. Stage qualification covers this layer0/key512 sample, not q4, key256 stages, every layer, arbitrary shapes or other models. The four complete requests separately exercise observed key256/key512 geometries across all target layers. Fresh-directory validation took place on the same machine and driver.

## Preserved technical failure and accounting

`capture-a1` completed all three native requests and matched 175 historical vectors, but its wrapper failed a mistaken cumulative-process assertion, and the fixture missed final output because the caller renamed the tensor to `kqv_out-0`. Neither was a numerical failure. All original bytes, runtime and source snapshots are retained. `TECHNICAL_AMENDMENT_A2.json` records the correction; a single whole-triplet technical retry captured all four stages. No reference, input, model or numerical library was changed.

Total execution was **21 model requests in7 model workers, plus2 stage workers/8 graph computations**, within the24-request reservation. All9 native workers returned exit0 and empty Jobs. The initial wrapper failure remains in the ledger. The cumulative Job count was18, including9 additional counted processes whose identities/lifetimes were not captured. The active-process limit of1 is not a total-lifetime count. Build/tool helper processes are outside this native-worker accounting; no whole-task process-compliance claim is made. Summed supervised native-worker time was419.641 seconds, a diagnostic charge rather than a speed measurement.

All seven request triplets together supply1,439 exact historical full-vector comparisons; the four-input ordinary panel remains the914-vector primary smoke result. No numerical failure, replacement input, interim performance estimate or effect-dependent retry occurred.

## Delivery and remaining scope

`README.md` provides source/build and native commands. `LOCAL_DELIVERY.json` identifies the persistent model-free source/runtime/reference/raw-evidence package; `ARCHIVE_RECEIPT.json` supplies its completed full-byte verification and checksum. Git includes the small real stage fixture and receipts. Large full logits, historical reference bytes and binary libraries remain in the indexed local archive; there is no claim that Git alone contains them or that another machine has independently reproduced the result.

Completed: all PR146 B570 native-delivery requirements within the stated scope. Failed and retained: first capture wrapper/fixture attempt. Not planned or run: a new prefill timing panel, RTX-style lifecycle factorial, other-family repair, speedup claim, merge or manuscript submission. PR143's earlier helper-accounting deviation remains unchanged. `RESUME.md` gives offline verification and optional reproduction commands.
