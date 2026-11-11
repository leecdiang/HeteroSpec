# Runtime evidence supplement v0.4

This extends the immutable historical `MANUSCRIPT_EVIDENCE_LEDGER.md`; historical proposal-only status there is not the current manuscript status.

## M4 — primary prospective runtime result

Authority: `benchmarks/m4_runtime/{PREREGISTRATION.md,CALIBRATION_FREEZE.json,QUALIFICATION_REPORT.json,FORMAL_ANALYSIS.json,FORMAL_REPORT.md,M4_RUNTIME_CLOSEOUT.md,runtime_policy_protocol_v0.json}`; inventory and three split JSONs. All runtime source/data hashes are locked by `RUNTIME_BASELINE_V04.json` at base main `bbf0c555cc50242f85c086eac342c9deb5c2e945`.

Archive: `artifacts/m4_runtime/runtime-profitability-control-20260925/m4_runtime_complete_evidence.tar.gz`, SHA-256 `af73b8f0edeae5027357338a627d899b08db425884a1373162932a72f4f119ab`. The standard-library verifier independently extracts and checks every payload, reconstructs calibration selection, directly compares generated token arrays, reconstructs formal prompt medians, and replays all three 10,000-resample intervals and fallback. The paper's canonical runtime validator invokes it and checks the resulting receipt against the descriptor.

Policy E8_M000: initial decision after 8 rounds, margin 0, subsequent decisions after each completed speculative round; one-way fallback. Reference estimated only from calibration. Qualification: 48/48 exact for both conditions. Formal: 60 prompts × 3 repetitions × 3 conditions = 540 observations, 180/180 exact per speculative condition, zero mismatches. The primary estimator is prompt GM of ratios of per-condition median latency. Bootstrap uses Python Random seed 20260924 and linear-interpolated percentile endpoints; a single stream computes the three intervals in frozen order.

| Paper value | Frozen value | Evidence class |
|---|---|---|
| Target/Guard | 1.3114 [1.2487, 1.3787] | Primary prospective speedup |
| Target/Always-Spec | 1.3469 [1.2867, 1.4088] | Frozen formal comparator |
| Guard/offline oracle | 1.0278 [1.0137, 1.0446] | Descriptive hindsight regret |
| Fallback | 30.6% of Guard requests | Descriptive control trace |

`runtime_values.py` maps 23 TeX macros to exact JSON fields/derived protocol counts. `RUNTIME_QA_V04.json` records the full machine-readable mapping. Main uses: abstract, Section 7, Table 3, limitations. Appendix uses: estimator and recovery note. No raw empirical decimal is permitted in Section 7/Table 3; model identity `0.6` is the sole exception. Other protocol identities remain literal and trace to pinned source.

Performance is post-prefill generation with request-local initialization/control/state/transition costs charged; loading and shared prompt prefill excluded. The Guard does not beat the fixed-k=2 aggregate point estimate. The oracle is unavailable online, and no serving/concurrency, cross-model/platform generalization, stable small-stratum estimate, or runtime energy benefit is claimed.

## M4 provenance exception

Actual calibration freeze SHA: `3c179a35f046b57edb4ddc8772a1aba609b496878efc2b7849a66947c8b7830b`; erroneously recorded build-manifest SHA: `21592be38c0c477f63cea819b96b5b12cfea4529c131f6914b761a06ae5e518b`. Formal-start commit: `202109717754bc62f889d19b5fbb141bfc3cc529`.

Frozen `frozen()` returned the build-manifest path due to loop-variable shadowing. Independent recovery reconciled the actual freeze, clean formal-start source, qualification and complete attempts, then applied the original formulas. This is a metadata-recording defect, not a measurement mutation. Original observations, formal-start markers and STOPPED state are retained. The manuscript describes the exception in limitations and the appendix; it does not repair the experimental code or records.

## 358H — diagnostic qualification outcome

Exact pin: `12f387d117fb52cc0ecc688931b9925abb29e71e`, independently confirmed against the GitHub branch. `RUNTIME_358H_PIN_V04.json` identifies six byte-identical source snapshots and SHA-256 values under `runtime_v04/`; no experimental branch was merged. Key sources are `V03_CORRECTNESS_DIAGNOSTIC_REPORT.md`, `runtime_diagnostic_v0_3_evidence.json`, and `runtime_protocol_v0_3.json`.

The pin explicitly records `UB2_INTRINSICALLY_BLOCKED_IN_TESTED_STACK`, no v0.2 R2 execution, no formal performance data, and `r2_authorized=false`. Fresh same-prefix controls reproduce target UB1/UB2 divergence; isolated processes and execution-order controls reproduce it. Proposal playback excludes live NPU inference from the /48 diagnosis. History matters, and rejection-shape controls do not establish a rollback-boundary defect. No particular floating-point operation or line-level fix is proven. These findings are diagnostic and invalid for performance claims, scoped to Qwen3-8B Q8_0 / llama.cpp b10839 / Vulkan0 and the frozen execution contract.

The supplied task closeout provides the v0.2 small-gate pass/full-gate failure and CPU/NPU persistent-adapter disposition. The pinned transition note records CPU restore/reconcile unestablished and frozen dynamic-IR NPU compilation failure; architecture and protocol record the process-isolated implementation. Complete v0.2 R0/R1 raw outputs and v0.3 local raw traces are not present in this checkout. This audit verifies compact findings and hashes, not a fresh raw-trace reproduction of 358H. No additional exactness count or performance value is inferred. This is a remaining artifact-review limitation, disclosed in the appendix and integration report.

## Scientific boundaries retained

The hardware campaigns, estimators, negative M4 sample, positive separate HumanEval result, B570 formal stop/diagnostic status, exact negative 358H Phase 3, complete target cost versus micro proxy, replay-plus-proposal inseparability, reconstructed-source STRONGLY_SUPPORTED status, and separate energy domains remain unchanged. Cross-platform synthesis is retrospective; the runtime study is separately prospective. HumanEval token equality is not functional correctness.
