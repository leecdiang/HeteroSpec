# E0 decision, before development execution

Fixed design: 8b8c78f8fc63195369e276c83216075b8475a352. PR115 remains read-only d04b41e03b1fcd747851edb6aed3b4c40c544a5d.

## Observation and scope

One natural A-close/B-start pair, using the hash-verified old CPU supervisor ported to the new task root, completed A and B. Status: **NOT_REPRODUCED**. Full original buffers, lifecycle, cancel/completion and close instrumentation are in e0/external. Notification writer PID and operation time remain null. This does not refute PR115's records or establish its unique writer/cause.

The candidate is a containment design, to be validated, not ROOT_CAUSE_CONFIRMED. No fixed wait or action/path filtering is used to make old events pass.

## Registered topology and responsibility

Each round uses one new shared protected root, slots catalog, sacrificial inputs/results, and (when requested) 8000 newly created history files. Every slot and file baseline is prepared before arming. External journals and PowerShell controller logs are outside all protected roots. The real new implementation directory is also protected during a round. All new physical storage, including sparse Git objects, fixtures, logs and restoration, counts against 1GiB, with 256MiB reserved.

A persistent catalog watcher monitors FILE_NAME/DIR_NAME/SECURITY without treating child-directory writeback metadata as content writes. Separate recursive content handles cover every registered slot, input, result and history root, including LAST_WRITE, SIZE, ATTRIBUTES, NAME and SECURITY. Thus no file action=3 is omitted, no sealed slot is unguarded, and a slot rename/removal is still a violation at the namespace guard. Resolved paths, volume/file identity and actual raw buffers bind decisions. Reparse/hardlink fixtures are rejected.

## Slot and I/O state machine

PREPARED → ACTIVE → CLOSING → SEALED; failures go to FAILED and cannot restart. A unique slot ID is never reused. ACTIVE permits only that slot's contents. Other slots and immutable roots remain protected.

The producer exits; duplicate OS handle identity and times remain in the outer debugger ledger. Pipes drain/close and observers finish. Post-exit complete output audit is separate from live coverage. Before CLOSING, final file hashes are recorded. During CLOSING only notifications for those unchanged final files and the explicitly registered controller fence are eligible. The fence is synchronously written/flushed/closed and its real notification is observed. A new deny-all sealed content guard is armed before the previous content guard is cancelled. CancelIoEx is only a request: the final GetOverlappedResult result and any successful payload are processed, then directory/event close results are recorded. Only after completion and overlapping handoff is SEALED committed. Unknown events still reject; a new guard event cannot be waived as old noise. Shared namespace guards persist throughout.

This combines writer termination, flushed streams, final content audit, explicit ownership fence, overlapping protection and final I/O completion. Merely draining/reopening is not a seal proof. An explicit pending-close negative coordinates a real completed sealed write with CancelIoEx and checks final payload processing. A separate persistent guard protects the same sealed object during that probe.

## Faults, supervision and process boundary

Fault injection is task-specific and explicit. Filesystem mutations affect only newly created sacrificial CPU fixtures, from a real injector process. Identity/journal faults occur before GO; post-handshake faults occur at WORKING while the producer is gated, except frame/exit/deadline tests that need execution. A case may pass only if its raw operation, side effect, control point, typed detector/object and complete cleanup all match. Wrong or earlier failures remain wrong failures.

Resource, active-directory and watcher streams are independent and durable at nominal 100ms. Conservative read durations, first/next/last effective intervals remain ≤1,000,000,000ns; exact boundary tests are separate. Post-exit audit delay never becomes a resource sample. Watch/reader/journal failures fail closed with independent outer receipts where possible.

Outer task broker was armed before checkout/build/test/review commands. DEBUG_PROCESS creation events provide OS parent/command identity for descendants, including quick-exit processes; duplicated handles survive debug continuation and supply real exit FILETIMEs. Existing Codex/tool services, initial protocol reads, one read-only commit check, and the first broker bootstrap command are explicitly excluded and externally receipted. They are not fabricated child lifetimes. The broker's own full lifetime is counted once at closure. All later task commands, Git, review, archive and restore are submitted through it. The debugger adds real CPU overhead; no performance claim is made.

Development is limited to six prospectively hashed states, two suites/24 targeted cases each. Final implementation review, remote freeze authentication and three fixed-order confirmation rounds are separate gates; none has yet passed at this decision point.

## Revision 1: notifications belong to registered objects, not the current case

Revision 0 preserved a real deferred action=3 for the terminal-pending fixture after that negative case closed. It incorrectly charged the following log-overflow case, which was NOT_REACHED. The pending negative itself was observed and rejected; no unique writer or operation time is inferred.

Revision 1 routes every rejected file notification to its prospectively registered sacrificial fault owner. A closed negative owner can retain additional rejections only while its actual injector receipt exists and canonical path, file ID, final mtime and full content SHA still match the recorded mutation. Its domain remains failed, with no later GO. All such notifications remain raw, disallowed DETECTOR records, explicitly marked observed_in_case and owner_remains_failed; they are never allowed or dropped. A different identity/content/mtime, positive-slot mutation, unknown path, or root change still stops the current round. This isolates already-rejected negative domains while preserving their ongoing protection. It establishes object ownership only, not the kernel notification's unique writer or event time. Final review must assess this boundary.

## Revision 2: failed producers must also finish the seal protocol

Revision 1 reached real FRAME/ACK log overflow, but late DATA/ACK notifications from the killed producer were charged to the next resource-fault case. That next fault was not reached. The failed producer had been marked FAILED without completing the same fence/overlapping handle closure used by successful producers. Revision 2 closes every producer through CLOSING, final file hashes, observed file fence and completed overlapping handoff, then commits FAILED or SEALED. No failure becomes admitted, and no notification is ignored. The auditor additionally decodes raw Windows buffers independently instead of trusting decision text. A Windows path-key portability error in the first revision-1 audit is retained; input keys are now canonicalized.

## Revision 3: final qualification and prospective-freeze integration

Revision 2 completed all 19 real CPU cases and the independent reconstruction passed each row, including nonempty FRAME ACK retention and all deliberately invalid monitoring cases. Revision 3 keeps the runtime repair, adds globally unique slot IDs, startup path rejection, final-review/remote-freeze gates, fixed confirmation entry and raw-auditor adversarial tests. The raw auditor now checks original notification buffers, exact confirmation order, downloaded freeze/source bytes and unrelated monitoring gaps. No confirmation has started.

## Revision 4: task-queue integration and final delivery source

After revision 3 completed all 19 native CPU controls, a queue request parse failed before launching the next snapshot. The original broker stopped, and four queued tool commands were not started; all 270 already observed task children had closed. The actual bytes read during that parse and the first broker's OS exit FILETIME were not retained. The external exit receipt and complete old ledger are preserved; no missing identity is fabricated.

Development rebootstrap generation 2 retains the old ledger and pending requests, carries forward starts/lifetimes/global task clock, and uses a separate queue. The publisher exclusively stages, fsyncs/closes and atomically renames a complete request; it refuses a second publication until the previous result is fully parseable. This also prevents publication from racing between-command capacity inventory. A real incomplete .partial file remained present while a CPU control completed, then was completed/flushed/renamed and executed once. Concurrent publication was actually rejected. No old request or experiment slot was resumed.

Every journal now includes real native thread IDs/names. Final raw reconstruction requires independent watchdog thread evidence; earlier development records lacking that field remain identifiable and are not substituted for confirmation. Archive, exact remote download/restoration and final-tail auditors are part of the reviewed host source before final confirmation. The final tail uses the existing tool service after all local task children close, so no recursive unobserved child is created merely to close its own ledger. Bootstrap/rebootstrap missing OS fields remain outside the debug-child scope and separately costed, not silently called complete.
