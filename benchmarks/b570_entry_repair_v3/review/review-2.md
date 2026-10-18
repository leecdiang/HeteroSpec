autoreview findings: 3
[P2] [P2] Write actual newline delimiters in smoke-test journals
benchmarks/b570_entry_repair_v3/source/test_entry_repairs.py:131
The fixture appends `'\\n'`, which writes literal backslash-n characters instead of newline delimiters. Consequently, every SmokeAuditTests case fails at `partial smoke journal`: the positive test cannot pass, and the negative tests never reach their expected validation errors. Use `'\n'` so these regressions exercise exit coverage and decision reconstruction.

[P2] [P2] Bind smoke decisions to the registered resource profile
benchmarks/b570_entry_repair_v3/source/check_observer_smoke.py:30
The checker compares decision limits only with the limits recorded in OBSERVER_START; it never compares either with `profile(kind, seconds)`. An observer mistakenly using an enlarged review limit can therefore produce internally consistent journals and receive OBSERVER_SMOKE_PASS. For example, a 33-process healthy run with a recorded live limit of 64 passes the healthy checks. Validate the start record against the canonical profile before reconstructing decisions.

[P2] [P2] Reconcile sampled Job identities with recorded exits
benchmarks/b570_entry_repair_v3/source/check_observer_smoke.py:26
Exit coverage is checked only for identities that received PROCESS_CREATE records. Identities present in resource census `members` are never reconciled with that set. In particular, the rejection branch can pass with 33 sampled processes but only one created-and-closed identity, provided cleanup reports an empty Job. This certifies the smoke despite missing actual exits for known sampled members—the gap that matters for nested-debugger descendants. Require every sampled `(pid, created_filetime)` identity to have matching lifecycle and OS exit evidence, and reject unresolved census coverage.

overall: patch is incorrect (0.96)
The supplied change contains a deterministic regression-test failure and two false-pass paths in the smoke validator. Assessment is based on the complete supplied source; project code and native Windows behavior were not executed. The excluded legacy CPU8 adapter was not assessed.
