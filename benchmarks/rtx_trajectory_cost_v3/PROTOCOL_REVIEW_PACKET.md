# Protocol / engineering review packet

This is PREPARE_ONLY. The exact F0 content commit is `a48381567f7f40330a589e33d285650c9e91f209`. Push, full remote retrieval and independent offline Git-object membership verification all passed. Remote acknowledgement: 2026-10-01T19:10:24.451062+00:00. No F1/F2 receipt is fabricated.

Mode: A24_B24. Exposure audit covers 93,176 classified file/member entries, published scientific branch heads and conservative historical inventories. There are 26 eligible and 138 excluded HumanEval tasks. Selection is the fixed SHA-256 salt order in RESERVED_SET.json; no candidate performance selects or replaces tasks.

The 24 selected IDs, in rank order: 2, 161, 86, 157, 16, 158, 59, 40, 31, 99, 49, 25, 141, 76, 142, 109, 15, 66, 81, 136, 148, 18, 143, 87 (each prefixed HumanEval/).

A plans 288 pre-live runs followed by 72 original native live runs. The four pre-live conditions are original reference UB1, original target-only UB2, H2 independent P/R, and fresh R-only replay. H2/R-only must pass 72/72 with four-condition repeat stability before F2. F2 contains every full array and own proposal tape, and is pushed and fully retrieved before any live/B launch. No H1 success gate or H3 is introduced. Scientific candidate mismatch is retained and classified without tuning.

B plans 216 fresh runs on the same frozen 24 prompts, three repetitions and three conditions. A observations are not reused. All conditions use the same newly qualified timer executable: target-only UB1, batched K2 with both model contexts UB2, serialized K2 with both UB1. The 72 blocks balance all six condition permutations 12 times, shuffled with seed 2026100103. Each path gates all 72 new complete-ID pairs independently; blocked speedup/CI remain null. The estimator uses prompt-level three-run medians, reference/candidate ratios, geometric mean and 10,000 paired bootstrap draws with seed 2026100104 and fixed linear percentiles.

Actual engineering: 360 fixed exposed-task runs plus 20 observer-off and 20 real EOG/cap runs, 400 complete conditions. Five mandatory gates each pass 36/36. All 20 observer pairs match. Constructed state coverage uses three additional model contexts, five R branches and P widths 0/1/2; these are not natural predictions. All 15 independent corruptions are rejected. Clock-call p99 is 0.6 microseconds, below 10 microseconds and 1% of the shortest 48.382 ms engineering interval. No logging overhead is subtracted or bounded.

Actual V3 model processes: 443 (including P/R sub-processes and three constructed contexts). Worker logical forwards: 11,778. Worker operation calls: 10,308. Tokenizer-only processes: 1, forwards: 0. Native allocator metadata records: 144,908; logical and physical records are reconstructed separately, and this number is not a distinct forward denominator. Observer-off native internal forwards are not individually exposed. Native target/draft role and exact per-decode host endpoints remain unobserved; process envelopes and source/native clocks are preserved.

**A reserved model forwards = 0; A reserved live runs = 0; B formal runs = 0.** Formal scientific reports are NOT_REACHED. The 576 scheduled conditions are not measured results or independent samples.

One real engineering metadata replacement failed after 338 valid runs. The blocked snapshot/stdout remains in engineering-attempt1/io-recovery. A finite I/O-only replace retry was added. The exact valid prefix was independently checked; only the 22 unstarted conditions ran afterward, with zero model reruns and unchanged numerical worker/timer bytes. The first extra waiter stopped before launching a model. A read-only verifier was optimized without changing its parsed output, retaining its interrupted and completed logs.

Target/draft/dataset, released DLL, P/R/T/Q/timer and observed driver identities are explicit. Initial/final scientific asset bytes, Windows/GPU identity, GHelper configuration and AC state agree. Original author checkout remains at a95ba4874668174bfa261578b23c3e036ea841b5 with no tracked changes. All old scientific paths and the author-freeze tag remain unchanged.

Two separate author archives and two derived anonymous archives each passed actual fresh-directory extraction, strict member hashes, independent arrays/tapes/timers/schedule/statistics and all 15 negative cases. The shared engineering run IDs are disclosed, not new independent A/B samples. Omitted external weights/runtime/driver bytes cannot be authenticated offline. Anonymous capsules redact host/account/PIDs and encode UTC ordinal order; original digests may retain linkage and do not prove unlinkability.

Review JOINT_PROTOCOL, PROTOCOL_MAPPING, EFFECTIVE_CONFIGURATION, INPUT_CONTRACT, COMMAND_TEMPLATES, BUILD_IDENTITY, ASSET_IDENTITY, ENGINEERING_REPORT, ENGINEERING_ATTEMPTS, NEGATIVE_VALIDATION and ARTIFACT_MANIFEST. REPRODUCTION gives all eight modes, exact Windows commands and no-retry formal stop rules. Author/full and anonymous verification results are recorded separately.

Required stop: USER_SPECIFICATION section 10 says “首次运行到此停止”. Resume only with the literal EXECUTE_FROZEN and the reviewed complete F0 SHA. No authorization is inferred from “continue”, and the original shutdown request is deferred until the full formal experiment actually finishes.

F0 publishing representation: GitHub rejected a 313.23 MiB plain ledger. Complete original 328,445,023-byte / 167,303-event engineering ledger, SHA-256 af8a427a60e5b6c4ab8c458a3443f251600a86ce5cbf920bf88d86fadc4c6d59, is preserved exactly in both author archive members `metadata/EXECUTION_LEDGER.jsonl`; ENGINEERING_LEDGER_ARCHIVE_INDEX.json binds these bytes. The local append-only ledger subsequently adds only the F0 acknowledgement (167,304 events). No model rerun, source math change or truncation occurred. Unpublished candidate commits and failed attempts are preserved locally; PUBLICATION_ATTEMPTS records them.

Four archive SHA-256 values (two parts each, fully reconstructed from GitHub before acknowledgement):

- `artifacts/rtx_trajectory_sufficiency_v3/engineering-a4500d44ee85c60856d07c6461681ca9013d00e008cbb9b4628a02a50dbcc938.parts.json`: `a4500d44ee85c60856d07c6461681ca9013d00e008cbb9b4628a02a50dbcc938` (89510514 bytes), offline PASS.
- `artifacts/rtx_matched_qualification_cost_v2/engineering-b6b0835073c30d47390289beac996978684fb5e0a92b9ad56f5674b1ae4d1980.parts.json`: `b6b0835073c30d47390289beac996978684fb5e0a92b9ad56f5674b1ae4d1980` (89510514 bytes), offline PASS.
- `artifacts/rtx_trajectory_sufficiency_v3/engineering-anonymous-f33da6e95191ec34213c7e0bd8f5b5eb05ac114db593ee7f9d2f9232f45a05c3.parts.json`: `f33da6e95191ec34213c7e0bd8f5b5eb05ac114db593ee7f9d2f9232f45a05c3` (71907638 bytes), offline PASS.
- `artifacts/rtx_matched_qualification_cost_v2/engineering-anonymous-3f838c31bd74b627b57a23af81e040912830b1c8c362a281577bb7c0ac196a07.parts.json`: `3f838c31bd74b627b57a23af81e040912830b1c8c362a281577bb7c0ac196a07` (71907638 bytes), offline PASS.

Resume instruction after review: `EXECUTE_FROZEN a48381567f7f40330a589e33d285650c9e91f209`.
