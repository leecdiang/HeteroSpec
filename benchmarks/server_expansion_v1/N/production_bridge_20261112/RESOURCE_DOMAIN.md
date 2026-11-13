# Resource-domain preparation: CPU evidence only

The current resource domain is a fail-closed bridge component, not an activated
kernel domain or a GPU allocation. The only activation adapter writes fresh
ordinary files. `activate_actual()` unconditionally rejects before a system
write; a configuration boolean cannot override it. No native executable, model,
backend, GPU context, placement or forward is needed to exercise this component.

## Immutable identity and lifecycle

`DomainBinding.from_dict()` canonicalizes the complete owner, run, manifest,
worker, stage, device, lease and issuer identities; both launcher and worker
executable hashes; a supervisor PID/start/boot/UID identity; the exact delegated
parent path hash/device/inode/UID/mount/controller identity; and dual-clock start,
last-launch and deadline values. The resulting bytes are immutable and their
SHA-256 is the domain identity sent through the bridge. Nested caller objects
cannot mutate the binding. Missing, unresolved and unknown fields are rejected.

The supervisor is the existing Python controller, known before launch. Fresh
launcher and worker PIDs are bound later, so the domain SHA does not depend on
an as-yet nonexistent child. The bridge independently binds the frozen job,
sealed worker-image FD, actual peer identities and inherited cgroup membership.
The resource component additionally normalizes the bridge's four-field process
identity and reads `/proc` when it needs executable or ancestry enrichment.
Parent links are contiguous and end at the bound supervisor, with matching
UID and boot identity; a matching final ancestor alone is insufficient.

The lifecycle is explicit:

1. `before_launch()` validates current evidence without creating a domain.
2. `bind_child(childpeer,parentpeer)` checks a still-blocked child in the launcher
   image, validates ancestry, then rehearses `BINDING.json`, `memory.max`,
   `pids.max` and child membership writes using ordinary files. It enters
   `PREEXEC`. A planned worker hash does not falsely identify this image.
3. At the source-bound worker HELLO, `observe_postexec(peer)` checks the same
   PID/start/boot/UID with the actual worker image and enters `POSTEXEC`.
4. `assert_live()` checks the appropriate image, membership, limits, parent,
   lease, resource floors and deadlines. Errors poison the instance; presenting
   repaired evidence does not authorize a retry.
5. Only after the bridge independently observes its held child pidfd readable,
   `assert_after_exit(peer)` permits resource checks without a live child proc
   entry. This records no stage success and proves no GPU preemption or kernel
   completion. Source-bound supervisor reporting and launcher reap remain
   separate bridge obligations.
6. `close_result()` preserves the reason and any remaining owned PIDs. It sends
   no signals and always reports `resource_release_verified: false`. Empty
   caller-supplied PID lists are not turned into independent release proof.

The object accepts an injected observer and clock so the same guard methods can
be called at every bridge transition. Unknown locks, unverified owner or lease,
stale/future samples, changed parent/process identity, expired heartbeats,
short leases and clock limits all fail closed. The proposal requires external
lease validity through the fixed deadline, not merely an idle GPU at launch.
An old PID alone cannot establish ownership.

## Real reads and synthetic CPU evidence

`cpu_resource_fixture.cpu_domain_factory` attaches this component to the fixed
standard-library-only launcher/worker demonstration. Its observer actually
reads process identities and ancestry, executable bytes, inherited cgroup
membership, sampled RSS, host available RAM and disk space. It explicitly labels
GPU free space, the GPU lease, delegation flags and limit activation as
synthetic CPU fixture fields. The ordinary directory identity is not described
as an activated `/sys/fs/cgroup` domain.

The CPU chain inherits its existing cgroup; matching parent/child membership
does not enforce a new memory limit. The ordinary-file adapter proves validated
operation ordering, readback, identity checks and failure preservation only.
Its paths reject symlinks and nonordinary proc/sys/cgroup filesystems. Every
mock creation is fresh; partial files survive a failure, and reentry is denied.

Read-only host capability evidence can support a future owned child beneath a
delegated user-manager parent. Capability availability does not mean that such
a child exists, that the current SSH scope is delegated or that limits are
active. Real activation, membership verification and a resource-owning
supervisor must be separately admitted and reviewed before native work. An
external GPU lease cannot be replaced by this program's own assertion.

`KernelCgroupAdapter` also contains a concrete source-only future operation
body. Its activation method begins with an unconditional denial, and the current
`ResourceDomain` rejects it as an adapter. Behind that closed gate, the reviewed
sequence walks a held parent directory FD without symlinks, checks device,
inode, UID, mount ID and cgroup2 mount type, requires an empty direct parent and
already-enabled delegated memory/pids controllers, creates a fresh child, and
writes and reads back the same limits used by the ordinary mock. It never
enables system controllers, removes a prior child or resets a device.

The source body requires a separately reviewed atomic
`clone3(CLONE_INTO_CGROUP)` launcher using the held child-domain FD, followed by
owned pidfd, identity and exact member readback. A numeric `cgroup.procs` attach
is deliberately absent: before/after PID checks alone do not make attachment
atomic against exit and PID reuse. The future callback and kernel path are
**not executed or admitted here**. The ordinary mock exercises the shared
memory/pids operation specification and failure rules; it does not validate the
unexecuted cgroup2 mount/atomic-spawn/kernel actuation body.

## Bounds with bridge overhead

`resource_manifest()` recomputes the old **553,094,505,923-byte** ceiling without
increasing requests, rows, placements or storage. It remains an unapproved
proposal: 72 planned requests / 69,354 rows, at most 76 / 85,738 with failed
attempts, ten each of backend/model/context/placement actions, and at most
18,000 seconds. Failure slots are not executable retry IDs.

The raw, metadata, shared journal, archive and independent restore pools remain
unchanged. Bridge/domain overhead is carved from the existing 8 GiB build/text
pool:

| Subpool | Limit |
|---|---:|
| Prior and new retained builds/sources | 7 GiB |
| Worker logs | 256 MiB |
| Controller logs | 128 MiB |
| Bridge logs | 128 MiB |
| Resource-domain records | 16 MiB |
| Bridge receipts | 256 MiB |
| Controller indices | 240 MiB |
| Total | **8 GiB** |

There is no second 512 MiB journal. The common ceiling remains 250,100 bounded
2,048-byte records. Domain records have a separate carved 16 MiB cap: at most
4,096 records of 4,096 bytes, sufficient for a proposed five-second heartbeat
cadence over five hours plus bounded lifecycle records. Per-RPC observations
must not silently create an unbounded per-observation file or journal entry.
The archive keeps its 4,096-entry ceiling; bridge/domain entries are bounded at
512, in addition to the prior known 2,471 entries. Export must measure the final
source/artifact selection and stop if any byte or entry pool does not fit.
The 4,096 domain records belong in bounded streams, not 4,096 new archive files.
At most 128 immutable bridge records of 32,768 bytes consume 4 MiB, with compact
descriptors bounded separately inside the existing shared journal. Conservatively
adding 128 transitions to the old 199,196 source-command bound gives 199,324,
still below 250,000; no finite or comparison check is removed.

[The base execution manifest](EXECUTION_MANIFEST_NOT_ADMITTED.json) expands every
original request's rows, raw bytes, metadata and phase caps, the eight workers,
two probes and inaccessible four-failure allowance. It pins the complete prior
manifest bytes as well as its canonical identity. `resource_manifest.py` can
reproduce it without loading a model. The four original paths and all 261 check
IDs remain unchanged. It preserves the earlier unmeasured-build placeholder;
the [final enriched proposal](FINAL_EXECUTION_MANIFEST_NOT_ADMITTED.json) adds
the named final selected-file receipt without changing those execution limits.
The independently measured prior subset is
1,715,339,140 bytes: prior ELF pair 446,211,136; twelve numerical archives
452,090,090; six parser objects 13,657,192; and six resolved dynamic dependencies
803,380,722. The new pair, std-only pair and selected reconstructable sources
are included in the final named selection; an entire historical build tree is
not assumed to fit. The final set has 7,953 files, 2,631,178,832 logical bytes and
2,650,431,488 allocated bytes. Together with a bounded ancillary strict restore
inside the same 7 GiB artifact pool, it fits that pool without adding disk quota.
The [named partial measurement](review/SELECTED_EXISTING_ARTIFACTS_PARTIAL.json)
contains the 26 selected existing file identities; it is not a complete build
admission receipt.

The proposal retains 24 GiB domain memory, 128 processes, protected 24 GiB host
availability and 48 GiB before launch; at least 2 GiB device margin; a last-new-
worker start offset of 6,600 seconds and a 600-second worker watchdog. These are
stop conditions, not measured runtime estimates. Polling RSS is not a hard
memory limit; stopping a process is not an unconditional GPU hard-kill promise.

## Reproduction and limits of the evidence

From this directory, run `python3 tests/resource_tests.py --out
FRESH_ABSOLUTE_ORDINARY_DIRECTORY`; optimized mode needs a second fresh directory
and `python3 -O`. The current component suite passed **27/27** in each mode. It covers
immutable hashes, missing identities, stale/expired authority, resource caps,
contiguous ancestry, four-field peer enrichment, preexec/postexec and exit
phases, partial writes, tampered limits/inodes/symlinks, no retry and permanent
denial of actual activation, the explicitly synthetic fixture evidence labels,
and pinned manifest expansion. The source-bound
[current receipt and logs](CPU_EVIDENCE/resource-domain-04/RECEIPT.json) retain the exact
tested hashes and show zero model/backend/context/placement/forward operations
and zero actual cgroup changes.
The four-field post-exit regression also injects a failing process reader to
prove that no dead-child `/proc` inspection is needed after the bridge's held
pidfd observation. Earlier 22-test and 26-test epochs remain public; the
intermediate 25-test epoch is retained privately. Later source additions do not
rewrite their recorded hashes.

These component tests do not establish that the full bridge invokes every guard
in the required order. Full-chain standard-only CPU integration is reported
separately. Neither source inspection, a CPU integration pass nor synthetic
accounting validates any of the 261 native numerical checks or grants the
proposed N1a GPU budget. N1b, N2 and performance measurement remain outside this
resource proposal.
