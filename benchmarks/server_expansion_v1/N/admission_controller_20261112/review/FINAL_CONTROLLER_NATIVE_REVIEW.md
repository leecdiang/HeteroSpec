# Independent controller/native-boundary review

CPU preparation is reviewable; native execution remains No-Go. This review read
the root controller, late-bound R handoff and C++/Python interoperability sources
independently from their author. All four complete reviewed files match the
actual source epoch05 archive used for the final CPU tests. Their exact sizes and
SHA256 values are in FINAL_CONTROLLER_NATIVE_REVIEW.json. No native binary,
model, backend, GPU/model context, placement or forward was run for this review.

Four material issues were found and corrected before the final source freeze:

| Finding | Final correction and relevant fault coverage |
| --- | --- |
| A second-open flock conflict did not identify the holder after loss of the original lock. | /proc/locks must show the exact kernel FLOCK device/inode and controller PID. Unknown competitors with unchanged LOCK contents are rejected; no automatic reacquisition. |
| Recovery compared only counts/chain/owner, so status-only STATE tampering could appear complete. | Published STATE inode/bytes and in-memory canonical state are bound; recovery compares the complete replay-derived state. Complete requires all four stages/eight workers. Status-only and internal-state tampering are tested. |
| Runtime indices referenced caller-owned manifest dictionaries outside the frozen copy. | Worker/deployment policy derives only from the controller's deep copy. Mutation of the original caller input cannot rewrite policy. |
| The public state property exposed live counters/stage fields to mutation. | Public state is a deep copy; canonical state bindings catch internal changes. Entry/event RLocks serialize competing reservations. |

Final CPU controller tests pass37 normally and37 with Python -O, including these
faults, out-of-order/parallel workers, lost identity/lease, partial journal/write,
fsync/disk/row/byte/quota/time failure, crash inspection, strict cold first
difference, R certificate tampering and strong-not-started controls. The actual
std-only C++ probe↔Python broker test passes8 synthetic request/row reservations
and184 metadata bytes. It does not run a stage checkpoint or a model.

The reviewed stage path requires R, independent repeat, semantically aligned cold
and then strong. A checkpoint calls the internal strict provided-byte verifier,
requires the exact frozen check IDs and preserves first differences. An accounting
close ACK keeps the worker occupied in WAIT_EXIT. Bare waitpid0 is blocked;
advancement also requires a source-bound owned exit, successful supervisor result
and complete bounded logs. The durable eighteen-input R handoff binds actual
provided snapshots; cold uses its canonical IDs/head, while repeat/strong keep
their own producer and use expected IDs only as assertions. No JSON PASS receipt
can directly advance a stage or grant native execution.

The generated full native worker and real compiled R/loop4 client/IO wiring are
separately source-bound. Their two ELF files were compiled/linked and inspected,
never executed. The final gate remains permanent denial before native object
construction or launcher fork/exec. Fixed CPU child tests establish the host
pidfd/timerfd/parent-death and bounded log behavior; they do not prove GPU
quiescence or numerical state. The live BINDCHILD/production CLI connector and
actual resource-domain admission remain explicitly BLOCKED.

No unresolved material source bug was found in this final four-file snapshot.
All261 native checks, loaded-runtime truth, actual active-KV/full-vector lifecycle
and resident/cold equivalence remain NOT_RUN. Source/hash/synthetic evidence is
not native qualification, a device allocation, a quiet window or budget approval.
No N1a/N2 or performance conclusion is supported by this review.
