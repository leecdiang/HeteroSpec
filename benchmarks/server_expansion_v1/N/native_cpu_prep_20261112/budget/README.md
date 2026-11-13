# CPU-only durable budget component

This component is preparatory mock code, not a GPU admission service. All native
context creation, placement, and model forward remain prohibited. `admit_native`
always rejects, regardless of an `approved=True` argument. There is no import of
CUDA, llama.cpp, a model library, or a subprocess launcher.

Source reviewed: PR #226 commit `87ea17971642f65468678cee8477505b9956611a`,
`benchmarks/server_expansion_v1/N/n1a_lifecycle_20261112/plan/manifest.js`.
The supplied `original_manifest.js` is an unmodified inspection copy, not a
replacement for or edit to the frozen source.

## Integration

Construct `MockBudget(new_directory, manifest)` with explicit `CPU_MOCK_ONLY`,
run ID, SHA-256 source binding, fixed deadline epoch, three explicit numeric
limits, and a `request_rows` map. A caller must reserve a request before accepting
it, and reserve the full known decode batch rows before simulating dispatch.
Reservations remain consumed if subsequent mock work fails. Unknown IDs,
duplicates, request caps, per-request row caps, aggregate caps, and timeout fail
closed. Each successful reservation is persisted before it returns. No refund or
automatic retry exists. Closing does not clear the ledger; reopening binds exact
manifest bytes and replays the prior expenditure.

Map the frozen proposal's `operations[].id/decoded_rows_max` to `request_rows`.
Do not manufacture IDs for the four unallocated failure slots. The proposal's
76 requests, 85,738 rows and 10 placements are **not authorization and not module
defaults**. This module must not be attached to a real adapter. A future execution
controller needs separately reviewed approval handling, per-phase gate receipts,
operation order checks, concrete placement IDs, and a shared native dispatch cap.

## Failure model and limitations

- Exclusive POSIX `flock` prevents simultaneous holders of one ledger. Different
  directories are separate mock sessions, not global resource exclusion.
- Every append first writes and fsyncs `UNCERTAIN`, then appends and fsyncs its
  event, then removes and syncs the marker. A crash or IO error in the critical
  interval blocks reopening. Manual reconciliation, not quota restoration, is
  required. Short writes are not retried. Error details should be retained by
  the integrating harness.
- The ledger is not an anti-tampering mechanism against an actor editing or
  deleting files. It requires local POSIX filesystem semantics; NFS/distributed
  locking and power-loss durability are not qualified here.
- Deadline is checked before each reservation, using both fixed wall time and
  a process-local monotonic deadline. It does not stop an already running native
  operation. Trusted wall-clock continuity across process restarts and an
  external supervisor would be needed for real execution.
- This ledger cannot establish that native launch accounting is complete,
  approval is genuine, GPU UUID is owned, state snapshots are truthful, or that
  PR #226's 261 raw comparisons passed. All tests use synthetic CPU events.

Run: `python test_budget.py` and `python -O test_budget.py`.
