# Evidence required by the repaired implementation

EvidenceReader validates the entire unique manifest and authenticates every
subsequent consumed input, including source captures, stdout, ACKs, directory
fixtures, launcher receipts and process records. Inputs outside the manifest,
aliases, partial records and changed bytes fail. An empty manifest is not valid.

The watcher emits WATCH_ARMED, IO_ARMED, IO_COMPLETION, WATCH_CLOSE_BEGIN,
CANCEL_ISSUED and WATCH_CLOSED. A cancellation request is not completion.
SEALED and FAILED slot transitions both require overlapping guards and actual
completion before closing the old handle. Parent guards preserve metadata
notifications for the registered directory itself; out-of-scope sibling events
remain explicit and must be independently checked against the registered roots.

ROUND, WATCH, per-case RESOURCE/DIRECTORY journals and launcher receipts are
separate evidence sources. A real production journal failure stops admission
and writes an emergency record to stderr, independently captured by the C#
launcher. The auditor verifies captured bytes against the launcher's receipt;
an `outer_record=true` assertion cannot replace that evidence.

All GO/CONTINUE writes and rejection state changes share one lock. Journal
failure latches admission before diagnostic persistence. New case admission
requires the previous case to have closed without an unexplained failure;
events outside cases are fatal and cannot be reassigned to a previous fault.

BOOTSTRAP_REGISTRY.json must prospectively identify each task-owned outer
process and the task start boundary. BOOTSTRAP_CLOSED.json must contain
actual OS exit evidence for precisely those identities and the task end
boundary. The old PR117 missing fields cannot satisfy this schema retrospectively.

Portable tests use synthetic evidence and OS-independent functions. Their PASS
does not produce ENGINEERING_READY, a Windows qualification or paper evidence.

Live admission requires this registry to include the executing broker. It charges
registered outer processes conservatively through the current monotonic time, even
if an outer process exited early; final accounting uses actual OS exit times. This
may stop early, but cannot spend a hidden outer lifetime allowance.

Restoration validates every packaged frozen source file, including imported audit
dependencies, against the current reviewed freeze before executing the auditor.

Development recovery may explicitly select the committed SOURCE_REVIEW_FREEZE.json
with --source-freeze, relative to the task root. This source-only review binding
does not assert a confirmation run or satisfy the final ENGINEERING_READY gate.
The closing ledger must extend the exact authenticated raw-audit ledger prefix;
readiness also verifies the final ledger bytes and actual budget fields.

For development, snapshot.py --source-only retains LauncherCapture.dll under
the snapshot's compiled evidence directory with byte/hash/source identity, while
excluding that DLL from the packaged source-only import tree. Runtime source caps
and build logs remain authenticated members. Full confirmation snapshots keep
the separately frozen DLL in their ordinary source set.

Cold bootstrap uses one new PROCESS_LEDGER.jsonl and no predecessor. The existing
Node tool service loads the hash-pinned CPU Win32 bridge, creates Python suspended,
records actual PID/creation FILETIME before resuming, and retains its OS handle
through exit. It observes zero remaining outer-job processes, closes handles, then
persists closure. Failed/missing receipts never qualify closure. The pre-existing
shared service is identified separately; its historical lifetime is not charged
as a new task process. Preparation elapsed time is included in task wall time.
FILETIME fields cross Node as decimal strings without floating-point rounding.

The public tool performance clock supplies elapsed preparation duration only, not
a QPC timestamp. The observer samples QPC first, then the same captured public
clock; subtracting the rounded-up duration conservatively includes the bridge
interval. Clock origins are never compared. A reversed/nonfinite clock fails before
process creation. Environment comes from an explicit public allowlist, not process.
