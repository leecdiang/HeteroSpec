# PR104 interim execution checkpoint — sessions 0–4

**Partial E2; final session 5 pending. E1 has not started.**

Five sessions completed: 1,350 native request starts and completed records, including 270 excluded warmups, from 270 fresh workers. Measured requests comprise 720 PQ/QB comparisons and 360 serial references. Zero scientific request failures, output mismatches, invalid output contracts, workload errors or heavy-observer flags were found. Closed native owned time: 4,149.036 seconds of the unchanged 43,200-second cap.

| Session | Started, China time | Completed, China time | Requests |
|---:|---|---|---:|
| 0 | October 14 12:27:07 | October 14 12:56:45 | 270 |
| 1 | October 14 13:56:54 | October 14 14:26:52 | 270 |
| 2 | October 14 15:27:01 | October 14 15:57:05 | 270 |
| 3 | October 14 16:57:15 | October 14 17:27:27 | 270 |
| 4 | October 14 18:53:55 | October 14 19:23:23 | 270 |
| 5 | Not started; earliest October 15 12:27:07 | Pending | 0 |

The first session-4 controller launch failed during authenticated GitHub freeze readback with network EOF before a session receipt, native load or scientific slot existed. That launch, original supervisor failure and stop analysis are retained in full. A separate prospective transport supplement was committed and authenticated before invoking the untouched session. Scientific retries: zero. The original Phase 0 failure at ccfbc2e is also retained unchanged.

The original E2 freeze remains 49b992b2ed1cabd05fad6e234cad2d3418c2b65a, with transport supplement e06dc8df53622eddd3f9306addbeaf428cdb3548. Tasks, token IDs, arms, AB/BA schedule, six sessions, budgets, timers, models, DLLs and family-specific binaries are unchanged. Session 5 retains the >=24-hour first-to-last rule and >=one-hour previous-completion rule. Automatic attendance remains active.

Every aggregate PQ/QB estimate is withheld because all six sessions and the final time-block gate are required. PARTIAL_ANALYSIS.json retains all available task/session contrasts and missing session-5 coordinates; this checkpoint makes no practical-improvement or equivalence claim. E1 numerical values, ULP and first divergence are unavailable because E1 is gated on complete E2. This checkpoint neither confirms nor refutes the paper's QB economics claim. It does not establish blind/new-input, cross-device or universal equivalence, kernel identity or reduction-tree identity.

RAW_E2_S0_S4.zip contains all current ledgers, block exports, raw request/worker records, cooldowns, environment/module/PID receipts, failed control attempts, freeze/readback records, the two selected native executables and analysis sources. Model weights and numerical DLL bytes are excluded; their hashes and loaded-module verification receipts remain. RAW_ARCHIVE_MANIFEST.json binds every member. ARCHIVE_RESTORE.json confirms a fresh-directory byte restoration and a separate-interpreter CPU recomputation matching the partial analysis byte-for-byte, on the same host; this is not an external auditor.

This is an immutable interim checkpoint, not the final scientific delivery. Historical RTX results, main and PR102 were not modified. PR104 remains Draft.
