# B570 formal finite-panel result

**NO_ESTABLISHED_PRACTICAL_PANEL_BENEFIT**

This is a completed prospectively registered finite-panel experiment, not an unseen-input or cross-date confirmation. Preregistration/source freeze commit: `809851f26e7a8f8e230aa26ecba8e639b97e5728`, created before GPU execution. Parent scientific candidate: PR133 `34787ab56f0ae8b533d18fe02db2d37e8ebb63a4`.

## Reference admission

All four registered inputs pass complete native endpoint equivalence between R, PQ and QB: token IDs, EOG flags, length, terminal token and stop reason. All PQ/QB saved full logits vectors, including discarded verification rows and draft proposal vectors, match byte for byte. All complete PQ/QB cycle traces match. Qualification covers actual q2/GQA32:8 across36 target layers on B570.

| Existing input | Tokens / stop | Verify cycles | Accepted proposals | Full-logit pairs | Actual physical key |
|---|---:|---:|---:|---:|---|
| HumanEval/38 | 64 / CAP | 32 | 31 | 97 | 256 |
| HumanEval/65 | 53 / EOG | 28 | 25 | 85 | 256 |
| HumanEval/115 | 41 / EOG | 22 | 19 | 67 | 512 |
| HumanEval/127 | 64 / CAP | 32 | 31 | 97 | 512 |

The four explicit input-ID sequences come from the project's existing PROMPT_TOKENS archive. They are exposed inputs, selected before this experiment for short/long geometry, not chosen using their new outputs or timing. Their chat-formatted input identities differ from PR133's raw HumanEval/42 prompt. R_e is a prospective q1/64-token reference for these sequences; historical R and16-token qualification remain unchanged. The cap is64, not a forced64-token output: natural EOG is honored.

## Clean full costs

Four independent native processes execute four explicit warmups and16 measured requests each: **64 measured requests plus16 warmups**, after12 qualification requests. All measured endpoints match their registered R_e, and all speculative cycle traces match the qualification trace. PQ_A/PQ_B call exactly the same implementation.

| Input | QB reduction vs dual-PQ, service | QB / target-only service | PQ_A / PQ_B imbalance |
|---|---:|---:|---:|
| HumanEval/38 | +0.536% | 2.5978 | -0.047% |
| HumanEval/65 | +0.800% | 2.6520 | -0.230% |
| HumanEval/115 | +0.272% | 2.6198 | -0.012% |
| HumanEval/127 | +0.334% | 2.6097 | -0.754% |

Primary equal-input geometric-mean service ratio QB/dual-PQ: **0.99514398**, reduction **+0.4856%**.
Request-only secondary ratio: **0.99511565**.
QB/target-only service ratio (separate draft economics): **2.61976294**.
Largest aggregate per-input A/A imbalance: **0.7537%**.
Registered practical threshold: **2.0000%**.
Per-process paired panel ratios: `[0.9962425614489917, 0.9953125999997887, 0.9961198807297972, 0.9929044831913394]`.

The predeclared screen requires a reduction above both2% and A/A imbalance, and QB below dual-PQ in every process-level panel aggregate. This engineering screen is not a hypothesis test or equivalence test. All paired blocks are reported in TIMING_TABLE.csv; no outlier removal, favorable subset selection, population confidence interval or optional stopping is used. Repeated processes do not create additional independent workloads.

## Cost and implementation boundaries

Primary `service_seconds` includes fresh context creation/graph reservation, target and draft prefill as applicable, generation, sampling, state maintenance, synchronization and context destruction. Shared model loading is measured separately. Request-only time excludes context lifetime overhead. Host full-logit copying, finite checks and cycle-record construction are included; post-request comparisons and file output are excluded. No node observer or raw-vector file writes run in timed requests.

Each process warms every arm with the previously qualified16-token prompt, checking the complete reference and trace; warmup costs are retained separately. This separates registered warmup from measurement but does not claim machine cold boot or flushed driver caches. Processes execute sequentially on the user's B570; exclusive machine ownership/background-load control is not established.

The `steady` record category means measured after this registered warmup, not proof of fully warm caches for every shape. The warmup prompt observes key256; key512 qualification ran previously, but persistence of its pipeline/cache state across processes is not controlled. Every measured request intentionally creates a fresh context. Consequently this experiment estimates post-warmup fresh-context service under the declared sequence, and does not separately identify cold-boot or persistent-context steady-state performance.

Phase fields are synchronized host wall durations around existing decode calls, separated by role/phase. There is no additional GPU synchronization relative to the inherited host. Host/other residual is explicitly unassigned. These fields are neither GPU kernel active time nor a critical-path proof, and their ratios cannot establish a physical bandwidth bottleneck.

Descriptive arithmetic means from the registered phase fields help locate the cost boundary: PQ target verification takes1.009015s per request versus QB0.935009s (about7.33% lower within that phase). QB draft prefill alone takes9.229470s; all its draft decode/prefill calls total12.366798s. Mean target-only whole service is7.325388s, while QB whole service is19.168150s. These descriptive means are not the primary geometric-mean estimator. They show why a local verification improvement is insufficient under this execution policy; they do not identify why draft execution is expensive or attribute that expense to physical GPU resources.

The frozen q1 reference uses token-by-token prefill. Draft weights remain resident even for target-only R, but R creates no draft context. This is a reference-matched standalone request bridge, not an optimized production serving implementation or a proven software ceiling. The study evaluates layout and draft economics under this declared execution policy; it does not claim no faster software implementation can exist.

## Paper conclusion

The result extends the B570 evidence from a single16-token key256 bridge to four registered inputs with a64-token cap, natural EOG, and observed key256/512. It supports backend and stateful-request migration under the stated reference. Cost benefit is a separate outcome governed by the reported ratios and failed/passed screen; bytewise equality alone is not acceleration evidence.

Under PR130's paper structure, place this result in State Formation and Backend Transfer and Real-Request Scope/Mapping Costs. Retain the existing RTX E2 gains with their original population and scope; do not pool the B570 panel with them. Do not reopen QH micrographs or infer a new accelerator. A physical hardware opportunity still requires an optimized software baseline, a stable residual and causal resource evidence.

The useful next engineering experiment is reference-preserving draft/prefill software execution, with fixed inputs and complete costs, rather than more attention-layout microbenchmarks. This is a next-step inference from the phase costs, not a validated optimization. Any batching or schedule change must be re-admitted against the frozen R_e and cannot retroactively modify this study.

## Evidence and accounting

All8 native processes return normally with complete capture and no deadline kill. Whole-parent charge this study: **1416.5916577s**; prior **401.2123575s** remains unchanged; combined historical charge **1817.8040152s**. Charges include loading/cleanup and are not GPU-active seconds.

COMPACT_EVIDENCE.zip preserves all result/progress/geometry JSON, logs and receipts. RAW_LOGITS_MANIFEST.json enumerates full vectors by size/SHA256. Full vectors are additionally archived locally; LOCAL_ARCHIVE.json pins that archive and explicitly records that it is not hosted on GitHub. This is local execution plus CPU recheck, not independent external raw-data certification.

No actor, RTL, CPU8 expansion or PR merge.
