# Launch adapter and ownership contract

This is a CPU preparation layer over the exact #229 chain, not a replacement
reference. Source/binary provenance is in `review/HOST_READONLY_AUDIT.json` and
build receipts. The old five complete-source gates and original numerical
library identities are mandatory. Missing or changed identities stop the
corresponding chain; excerpts and a modern producer are not substitutes.

## Bound identities

Each v3 HELLO has exactly10 tab-delimited fields: `HELLO`, version3, hex run,
manifest SHA, hex client role/worker, lease SHA, actual job-file SHA, resource
domain SHA, device-UUID SHA, and fixed stage. IPC frames remain capped64KiB and
strictly sequenced. Unix `SO_PEERCRED` supplies the actual peer; JSON PID values
do not authenticate a session. The protected socket's inode/UID and controller
PID/start/boot are checked by the C++ client before and after each command.

`launch/<worker>` and `supervise/<worker>` must be the same controller-owned launcher
PID/start/boot/UID and frozen executable. The worker must be its bound descendant
with the planned image. A pre-exec child still has the launcher image; the
resource adapter records that fact separately from the sealed future worker
FD. Worker HELLO performs the explicit post-exec image transition before the
normal resource guard. It never labels the launcher's image as the worker.

`BINDCHILD` has child and parent identity, worker-image SHA, sealed image FD and
held job FD. Before ACK, the controller checks ancestry, inherited cgroup,
regular immutable image/full hash, bounded job/full hash and obtains a pidfd
with a second process-identity check. The C++ parent closes its launcher session
and receives a durable ACK before releasing its child barrier. The job pathname,
held file identity and full bytes are rechecked around release and after exec.

The CPU launcher's and worker's exact compiled SHAs are pinned in the reviewed
runner. Callers cannot substitute an arbitrary std-linked ELF by supplying its
SHA. Both launcher and worker execute sealed images, closing a pathname-swap
window between checking and exec. The worker gets a fixed minimal environment
with empty GPU visibility; no arbitrary command, arguments or loader variables
come from a job. These safeguards are CPU fixture evidence only.

## Slot, budget and stage gates

One controller owner holds the exact kernel FLOCK. Existing, unknown, changed or
lost locks are never removed. A durable placement reservation precedes launch;
the worker's placement hook verifies that reservation rather than charging it
twice. Request, physical rows and classified writer bytes are still reserved
before work. Partial journal/fsync failure preserves the conservative upper
charge and poisons the run. New bridge records fit the old journal/state pools;
they do not add model requests or expand the proposal.

The legacy unbound start/claim path is refused by the v3 controller. Worker
closure is not exit proof and does not release its slot. Later stage inputs
remain bound to R's verified input certificate and sealed captures. The strict
comparison consumer is inherited unchanged; first differences persist before
the next stage is refused. A repeat R self-check does not establish cold
equivalence. All261 actual native checks are `NOT_RUN` here.

## Supervisor result

The bound parent drains two capped pipes to separate fresh single-link regular
files, writes exact lengths and fsyncs before its result. Controller-readable
FDs and launcher write-only FDs refer to the same frozen inode; a duplicate of an
O_RDWR FD is not a write-only descriptor. Each live result binds child PID, raw
wait status, exit confirmation, signal/partial flags and both log descriptors.
The controller re-reads and hashes those actual files and checks its held child
pidfd. It then requires a clean closed supervisor session and reaps its own
launcher before releasing the worker. Submitted saved receipts and bare
`waitpid` success cannot substitute for this chain.

The resource lease/domain stays reserved through failure or uncertainty. A
pidfd-confirmed dead child permits only post-exit resource inspection, not a
success result or GPU-completion claim. Unknown results, missing EOF, overflow,
short writes, ENOSPC, fsync failure, owner loss, identity changes and deadline
expiry stop before subsequent workers. The source-bound supervisor can signal
only its owned child through a pidfd; there is no unknown PID/group fallback.
An uninterruptible kernel/device operation can outlast a host deadline.
Regular-file writes and `fsync` can also block inside the kernel. The prepared
supervisor checks the deadline before and after these calls; the controller's
absolute IPC deadlines then refuse further work and can signal its owned
launcher. This does not prove that an uninterruptible call returns or that GPU
resources are released within five hours. Hard completion/release remains
unproved and must not be promoted by the four CPU boundary tests.

## Closed production boundary

No route in this successor turns a CPU JSON receipt into GPU permission. The
native launcher and full native worker gate before argument parsing, job open,
fork/exec, backend init, model creation or placement. Compile/link and static
symbol evidence do not prove this chain's native output/state correctness.
The concrete kernel-domain activation and external quiet lease requirements are
listed separately in `RESOURCE_DOMAIN.md` and `STATUS.json`; blocked guarantees
must be resolved before any future separately reviewed activation change.
