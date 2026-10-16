# B570 supervision repair v2

Independent implementation candidate based on PR117 commit
`08ec85f4a2c58e53a6dde4a230d686930dc7e600`. PR115 and PR117 remain closed-out
engineering-blocked evidence; no historical result is upgraded.

This PR fixes rejection/GO synchronization, lexical alias checks, unconditional
CLOSING immutability, actual critical-journal failure injection with an independent
stderr signal, watcher lifetime reconstruction, authenticated auditor inputs, and
final report/recovery/source bindings. Missing bootstrap observations fail the tail
audit rather than being replaced with fixed allowances. Live child process charges
include a monotonic lifetime estimate while they are still running.

## Validation and limits

Portable tests: `python3 -m unittest discover -s tests` and
`node --test tests/test_bootstrap.mjs tests/test_gates.mjs`. The fixtures include valid inputs as well as
counterexamples; synthetic READY is a gate unit test, never a machine result.
No Windows integration, GPU queries, model reads or scientific experiments are
performed by this PR preparation. The natural Windows A→B problem has not been
reproduced or demonstrated repaired. Conservative notification rejection may still
block legitimate asynchronous Windows delivery and requires measurement.

An independent code review is required before this candidate can be sent for a
small Windows validation. Its actual result is reported in the PR, not inferred
from unit tests. The inherited ACCEPTANCE/BUDGET files describe the old full
confirmation format only; they do not authorize another 57-case execution.

## Next Windows validation, after review

Use a fresh isolated root, exact source bytes and prospectively observed outer
process identities. First run the normal single slot and natural A→B handoff with
raw notification timing. Then exercise reject-before-GO, pending-close handoff,
metadata/path replacement, and real resource-journal failure, one targeted case at
a time. Every negative must reach its intended control point; an earlier unrelated
rejection is a failure. Require successful launcher/controller closure, complete
watcher I/O lifetimes and all process/accounting receipts. Stop at the first
unexplained discrepancy and report it. Do not reinterpret a developer test as a
Windows pass or run the full matrix automatically.

No paper claim, performance target, model or GPU work is added here.

## Cold-bootstrap follow-up

The original BOOTSTRAP_BLOCKED results/RESULT.md is preserved unchanged. Invoke
host/bootstrap_cold.mjs inside the existing Windows x64 Node tool service. It loads
a pinned CPU Win32 bridge without installer/helper processes, creates the broker
suspended, registers it, resumes it, and observes actual OS exit. One fresh queue
and ledger replace predecessor dependencies; retired entrypoints refuse execution.
See B570_NEXT_PROMPT.md for the complete dispatch. Requires Node-API 8+ and access
to the pinned npm archive. Windows qualification remains outstanding.
