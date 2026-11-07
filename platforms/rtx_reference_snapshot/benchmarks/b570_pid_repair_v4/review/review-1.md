autoreview findings: 2
[P1] [P1] Normalize retained handles before using them as dictionary keys
benchmarks/b570_pid_repair_v4/source/process_registry.py:17
`win.retain()` returns a `W.HANDLE` instance (`ctypes.c_void_p`), which is unhashable under [CPython 3.12](https://github.com/python/cpython/blob/3.12/Modules/_ctypes/_ctypes.c#L2683-L2690). Consequently, the first native CREATE_PROCESS event raises `TypeError` at `self.orphans[h]`, before identity registration. Every observer smoke, churn run, and observed review therefore fails. The duplicated handle also escapes cleanup tracking because insertion never succeeds. Normalize the retained handle to its integer `.value`, or store it without hashing the ctypes object, and cover the actual ctypes return type in the portable regression fixture; its current integer handles conceal this blocker.

[P2] [P2] Reconcile the receipt's root exit code with the recorded OS exit
benchmarks/b570_pid_repair_v4/source/audit_identity_stream.py:45
The auditor requires `receipt['root_exit_code'] == 0` but never compares it with `exits[root]` or `closed[root]['exit_code']`. A stream whose root EXIT_OBSERVED and PROCESS_CLOSED both record exit code 7 still receives IDENTITY_STREAM_PASS when the receipt claims zero and the other totals match. This defeats the independent reconstruction of successful command completion required for churn and full review. Require the root's paired exit records to agree with the receipt and record zero.

overall: patch is incorrect (0.99)
Reviewed all supplied source and the execution protocol. Native observation is blocked by unhashable retained handles, and the identity auditor can accept contradictory root-exit evidence. No project code was executed. Windows behavior and the unavailable legacy deployment layers were not certified; missing context was not treated as a defect.
