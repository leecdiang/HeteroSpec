# Independent B570 second-family validation

Result Draft PR #82 executes PR #81 at exact plan head `0a95a64805536323b0e8ae11784eaab150f91dcf`.

All560 requests completed:32 Qwen bridge,128 SmolLM2 discovery/capture controls,384 formal and16 warmups. Zero failures/missing/retries. All four arms qualified at the first-runtime-EOG-inclusive-or128 endpoint on the full24-task/four-round panel. N and C have raw suffix differences, so endpoint qualification is not complete raw equality.

Qualified host-request GM baseline/C: R/C **0.546138908**, M/C **0.561561946**, N/C **12.905834161**. C is about1.83 times the ordinary R cost; all24 tasks in all4 rounds were slower than R. Natural-state diagnostics were **NO_TRIGGER**. No cross-date or production-robustness claim.

[Chinese report](REPORT.zh-CN.md), [decision](DECISION.json), [complete matrix and per-task costs](D_VERIFICATION.json), [counts](COUNTS.json), [independent verification](INDEPENDENT_VERIFICATION.json), [full KV/F32 check](STATE_FLOAT_VERIFICATION.json), [negative guards](NEGATIVE_CONTRACT_TESTS.json).

[F0](F0.json) and [remote freeze receipt](REMOTE_FREEZE_RECEIPT.json) precede every Smol forward. Confirmation [reservation recheck](CONFIRMATION_RESERVATION_RECHECK.json) retained the frozen panel. [Ledger](LEDGER.jsonl) contains every START/COMPLETE; actual [sessions](SESSION_BINDINGS.json), [modules](MODULE_BINDINGS.json), [devices](DEVICE_BINDINGS.json) and [timers](TIMER_BINDINGS.json) are bound. [Preparation deviations](PREPARATION_DEVIATIONS.json) retain rejected static transport/CPU assumptions without scientific reruns.

[CAS index](CAS_INDEX.json) maps8 Git-hosted SHA256 parts to a392608205-byte ZIP and3319 logical files. [Local fresh restore](LOCAL_CAS_RESTORE.json) rederived every result identically. Final remote restoration/readback is reported separately in REMOTE_READBACK.json and DELIVERY_REPORT.md; DECISION.json was sealed before transport. No automatic merge/manuscript edits/release.
