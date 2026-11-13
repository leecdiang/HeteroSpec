# Native transport and host-launch boundary

All code in this successor remains CPU preparation. The original final
ProductionGate is unchanged and permanently denies before native worker JSON,
IPC, model/backend construction or native fork/exec. A JSON lease, a controller
ACK, a mock PASS or this task does not grant GPU execution. Neither native worker
ELF nor the closed native launcher artifact is executed in these checks.

## Implemented and compiled worker wiring

make_worker_descendant.py hashes the complete PR228 worker
d92280465ec60d52a24d6f8742117e2b7541e92ed411e3a70cbf3ea6fd4f54fa,
then applies six exact single-match substitutions: include the controller client,
bind the controller peer/lease, route the two StreamCapture IO objects and root
receipt IO, and route the receipt directory fsync. The generated complete source
is in native/worker.cpp with its derivation receipt. Numerical, lifecycle,
producer, active-KV and strict comparison code are unchanged. Old files are not
modified. build_descendant.py verifies all27 old compile inputs and the complete
original builder, then compiles/links against the same original numerical and
parser-only dependencies. nm/readelf inspect the real bodies; no binary runs.

ControlledNativeClient uses one AF_UNIX connection with bounded frames. It binds
controller PID, /proc start ticks, boot ID, kernel UID/PID credentials, socket
device/inode and a frozen owner-lease digest. The actual controller must bind the
reverse worker PID/start/boot/source identity. HELLO version2 contains run,
manifest, worker and lease identities. Each command remains sequence-numbered;
missing, partial, wrong or timed-out ACK poisons without reconnect/retry.

All existing backend/model/context/placement/request/actual-decode/mutation and
terminal hooks route to this client. Writer IO additionally reserves exact bytes
before every regular file write, using separate raw and metadata axes. The
actual FD must be owned, write-only, and inside the same frozen capture-root
inode with an exact allowed receipt/tensor/metadata path. Short writes or fsync
failures poison immediately, preserving the complete attempted reservation.

The unchanged StreamCapture failure cleanup writes a bounded UNCERTAIN marker
after poison. Therefore capture_open additionally pre-reserves1KiB metadata
before any capture filesystem side effect. At most348 capture directories need
356352 bytes, within the existing1MiB failure-marker allowance. Its fixed source
failure strings are below1KiB. Emergency owned marker cleanup is not a new model
request, retry, qualification or permission. No successful marker refund occurs.

## Host supervision implemented and CPU-tested

bounded_launcher.hpp provides a typed guarded native launch entry. Its concrete
gate rejects before executable hashing, accounting, fork or exec. The separately
tested internal host primitive launches only compiled fixed CPU child actions.
It validates finite absolute wall and monotonic deadlines at most5h, binds the
controller process identity including zombie rejection, arms an absolute timerfd,
and acquires the owned child pidfd before a pre-exec barrier permit.

The child installs PR_SET_PDEATHSIG(SIGKILL), then checks its actual parent
PID/start/boot before reading that barrier. This closes the fork-to-prctl parent
death race. The parent monitors the timer, controller identity and owned child;
it signals only that pidfd. There is no arbitrary PID/group kill fallback. An
unconfirmed exit remains explicitly BLOCKED rather than waiting forever or
claiming completion. Hardware/device quiescence under a stuck kernel cannot be
proved by these CPU tests and remains NOT_RUN/BLOCKED for native admission.

stdout/stderr are independently drained through parent-owned bounded pipes to
two fresh distinct regular files. Each stream is capped at12MiB, so20 proposed
streams fit240MiB within the existing256MiB worker-log allowance. A quota,
partial write, ENOSPC or fsync failure preserves the prefix and fails closed.
The supervisor result separately records completion flags, exact copied bytes,
partial state and exit status. Child exit0 is insufficient after a parent log
failure. RLIMIT_FSIZE is deliberately not used for log caps: it would also cap
large active-KV tensor files in the worker. Core dumps are disabled only inside
the unreachable native child setup, not by changing a host policy.

## Review-only production adapter design — NOT_RUN/BLOCKED

The typed native supervision entry is compiled, but no production job CLI or
controller-to-native launcher activation is admitted. The following bridge is
prospective; it must not be represented as a completed native path:

1. The controller acquires its owner lock and freezes run, stage, worker, sources,
   model, executable, requested bounds and finite resource/window identities.
   A separate approved production gate is still required; this build cannot
   supply one. Reserve deployment placement and log bytes durably before exec.
2. Register a source-bound CPU launcher as LAUNCH_ONLY. It validates the root
   controller identity and verifies the same pre-exec placement reservation,
   without charging it a second time. Accounting does not grant execution.
3. Fork the owned child behind a blocked pre-exec barrier. A future BINDCHILD
   handshake must register actual child PID/start/boot, parent identity, frozen
   executable/job SHA and the successor WORKER lease. The controller independently
   checks /proc ownership and resource-domain membership. No model ELF can start
   before this durable binding and all actual resource/approval gates.
4. Finish/close the launcher accounting session before the child WORKER HELLO,
   avoiding a blocked single-client broker. Publish any late-bound immutable job
   with O_EXCL while the child is still held. Never overwrite frozen inputs.
   Only then could a separately admitted native pre-exec permit be released.
5. The native child HELLO must match that precise bound PID/lease and expected
   current stage. The supervisor independently watches parent death, deadline,
   bounded logs and child exit. Failed/unknown ownership or a lost lock stops.
6. After worker accounting close, keep the stage occupied until the controller
   confirms owned exit, supervisor status OWNED_CHILD_EXITED, both logs complete,
   normal exit0 and strict stage evidence. Repeat/cold first difference blocks
   strong. Unknown supervisor status or bare waitpid0 does not advance anything.

BINDCHILD/production CLI/resource-domain activation are not implemented or tested
as a native bridge here. Default native launch remains denied. Native model
placement, actual loaded identity, GPU memory peaks, active state and all261
qualification checks remain NOT_RUN. The std-only client_probe tests transport
interoperability only; its accounting events do not initialize a backend or model.
