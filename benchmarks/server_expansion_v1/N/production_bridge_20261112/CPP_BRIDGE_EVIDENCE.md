# C++ bridge preparation: CPU evidence and native limits

The current artifact selection is frozen in
[`CPU_EVIDENCE/cpp-bridge-final-03/CURRENT_SELECTION.json`](CPU_EVIDENCE/cpp-bridge-final-03/CURRENT_SELECTION.json).
The two genuine numerical workers and the genuine native launcher were compiled
and inspected, **never executed**. All 261 native qualification checks remain
`NOT_RUN`. Model creation, backend/GPU context creation, placement and forward
execution are all zero for this work.

## What is connected

`cpp_bridge_launcher.cpp` contains the actual three-party path used by the
reviewed, fixed std-only CPU fixture and prepared behind the native deny gate:

1. The controller binds the known launcher process before its stdin barrier is
   released. The launcher verifies the externally supplied whole-job SHA.
2. `BridgeJob` parses the exact bytes it hashed, keeps the original source file
   bound, and places the verified bytes in a sealed memfd. The executable is
   separately copied to a sealed memfd from its frozen image identity.
3. The child is forked behind a pre-exec barrier. The launcher authenticates to
   the v3 broker, sends `bind_child` with child/parent kernel identities and both
   sealed FDs, waits for the durable bind ACK, and then waits for the launcher
   session's durable close ACK. Only then is the child permit sent.
4. The fixed CPU worker opens its separate authenticated v3 session. Every
   request, row, writer byte and sync still passes through the controller's
   accounting gate. These fixture hook events are mock events, not native
   backend/model/context/placement calls.
5. The launcher owns the child's pidfd, bounded stdout/stderr pipes, deadline,
   and `waitpid`. It drains and syncs both logs and checks deadline and controller
   ownership again before reporting successful exit. The authenticated
   supervisor result includes the frozen log inode/size/SHA descriptors.
6. The Python controller independently checks the live identity and log records,
   then reaps its owned launcher before permitting stage completion. The root
   integration evidence is reported separately from these compile records.

The worker and launcher sessions use the same run, manifest, lease, job, resource
domain, device and stage bindings. A JSON receipt is not GPU authority. The
unchanged concrete `ProductionGate` is checked before native argument parsing,
job loading, IPC or native fork, and always denies.

## Source and binary continuity

The complete old native worker SHA
`4ef88dc28b9765eb8f6d3e01706ca885c64f6fef88c1c6fe05a017599ca95538`
is transformed by explicit counted replacements to
`0ca2eadcbdc9ac3c92b49f5f89eca6259c4d13976ec6fa794907e0d8ac386848`.
The derivative retains the frozen numerical/lifecycle implementation and deny
gate; it changes the verified job binding, v3 client and three real writer I/O
entry points. [`native/DERIVATION.json`](native/DERIVATION.json) records the
replacements. The full derived worker is checked in.

`BRIDGE_BUILD.json` preserves the five original deployment source gates, the
27-input verification, parser objects, original reference and loop4 numerical
archives, build commands, object hashes and the two new native ELF identities.
Those workers do not include the supervisor and needed no rebuild for its later
deadline fix. `STATIC_IDENTITY_03.json` records static symbols for the current
five selected artifacts; complete symbol logs remain private and hash-bound.

The std-only fixture builder checks its dependency allowlist before either CPU
artifact can be used in integration. The native artifacts are inspected with
`readelf`/`nm`, never by invoking their loader or selftests. The native launcher
is built without the CPU fixture macro and pins the two genuine native worker
SHA values. The CPU launcher pins only the one reviewed fixed CPU worker SHA.

## Supervisor boundary correction and failure retention

Review found that the previous inherited supervisor could accept exit plus EOF
before checking expiry, or finish `fsync` after expiry without another check.
The current supervisor checks expiry and controller ownership before successful
completion and again after log sync. The final CPU launcher and native launcher
were rebuilt; the numerical workers and fixed CPU worker were unchanged.

Four fixed std-only CPU tests passed:

| Control | Expected and observed result |
| --- | --- |
| Normal owned child exits before expiry | Complete |
| Log sync crosses the deadline | Reject, partial, no completion |
| Controller owner dies during log sync | Reject, partial, no completion |
| Pre-exec bind callback outlasts the lease | Reject before child action |

The first boundary-test invocation supplied a relative fixture path. It was
rejected before creating or executing a fixture. The same inspected test binary
then passed using a fresh absolute fixture path. Both logs are retained; no
native program was started. `finalize_launcher_epoch.py` only validates retained
hashes/logs and writes the receipt; it does not compile or execute anything.

Historical build receipts retain their historical launcher identities. The
current selection combines the fixed worker from CPU build02, the numerical
workers from native build01, and both launchers from build03. No old result or
failed epoch was overwritten or deleted. Public evidence replaces task-specific
paths with placeholders; `SANITIZATION_INDEX.json` binds the unchanged private
and public copies separately.

## Still blocked or not run

CPU pipe supervision does not establish a hardware resource domain or authorize
GPU execution. Atomic placement into a kernel-enforced domain, actual device
assignment/isolation, runtime resource enforcement and quiet-window evidence
must satisfy the separate resource gate. Numeric-PID attachment cannot be
treated as proof against PID reuse. No actual cgroup activation or hardware
admission was performed here.

The three-party CPU fixture proves only the exercised host bridge, durable
ordering, process ownership and failure behavior. It proves no native numerical
equivalence, active-KV correctness, producer semantics, cold/reference alignment
or performance result. N1a and N2 remain unexecuted and unauthorized by these
receipts.
