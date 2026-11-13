# CPU-only resource and manifest preparation

This successor does not grant or exercise native permission. `load_manifest()`
expands the frozen proposal, and `ResourcePolicy.check()` evaluates only supplied
evidence. Even an injected `PASS` returns `native_execution_authorized: false`.
The emitted manifest has `approval: null`, no allocated GPU identity, unresolved
worker identities and `mode: CPU_MOCK_ONLY`. No model, tokenizer, backend,
context, placement, forward, user unit or actual cgroup was created by these
resource tests.

## Frozen operation graph

Four full input SHA-256 pins precede JSON parsing. They bind the original native
job template, N1a proposal, resource review and required 261-check graph. Merely
preserving their operation counts is insufficient: changing any input byte
rejects manifest generation. The prior proposal, sources and ledgers are not
edited.

The exact 72 planned requests comprise 32 natural requests and 40 scripted
control requests. They run through resident R, repeat R, independently recomputed
cold canonical oracle, then strong whole-rechunk + loop4. Each role has separate
natural and control workers, for eight workers. Two separate no-forward probes
plus those eight workers consume at most ten each of backend initialization,
model load, context creation and placement. A pre-exec placement reservation is
required because a native-linked executable can initialize device libraries
before `main`; a worker verifies that reservation instead of charging it again.
The accounting reservation is not native permission.

Rows are reserved per original operation rather than estimated from a favorable
generated continuation:

| Component | Planned request count | Reserved decoded rows |
|---|---:|---:|
| Natural first turns: fixed prompt lengths 92, 63, 27, 108; cap 128; four paths | 16 | 3,192 |
| Natural second turns: capacity bound, original real R continuation still unresolved | 16 | 65,536 |
| Five two-turn scripted controls, four paths | 40 | 626 |
| Planned total | 72 | 69,354 |
| Failed-attempt allowance, not runnable retries | 4 | 16,384 |
| Global ceiling | 76 | 85,738 |

Cold natural `canonical_ids: null` remain null. The CPU calculation uses the
saved first-prompt length and a capacity bound for the continuation; it does not
construct or predict actual R-produced token IDs. A rejected capacity admission
does not execute rows, but the attempted request remains charged. The four
failed-request slots never create extra operation IDs, successor requests or an
automatic retry path.

Per-phase caps intersect request caps, worker caps and global counters. The
global metadata envelope is 380 MiB; “5 MiB per request” is its original average,
not an invalid universal per-request cap. A natural continuation with reset can
exceed that average. The generated caps count its actual phase inventory. An
owned-output BEFORE capture belongs to the still-active setup request; AFTER
belongs to the continuation. Each setup and continuation therefore owns one
event, rather than charging both to the latter.

## Exact disk ceiling

No additional disk allowance is introduced. The original ceiling remains
**553,094,505,923 bytes**. One full C4096 F16 active-KV upper bound is
603,979,776 bytes; one complete requested F32 vocabulary row is 607,744 bytes.
The raw request bound is three active-prefix snapshots plus 132 full rows,
1,892,161,536 bytes. Actual active prefixes may be shorter, but no smaller
observed capture is used to enlarge another quota.

| Pool | Bytes |
|---|---:|
| Raw captures: 76 × request upper bound | 143,804,276,736 |
| Capture metadata, including partial-marker reserve | 398,458,880 |
| Shared controller/broker journal | 536,870,912 |
| Raw capture + metadata + journal | 144,739,606,528 |
| Archive: ceiling of 102% of preceding pool + 16 MiB headers | 147,651,175,875 |
| Independent strict restore/readback | 144,739,606,528 |
| Build, controller state and text pool | 8,589,934,592 |
| Protected free disk | 107,374,182,400 |
| Required free disk | **553,094,505,923** |

The existing 8 GiB build/text pool is divided into 7 GiB retained build artifacts,
256 MiB worker logs, 256 MiB controller logs, and 512 MiB controller state and
indices. A selected source/build set must be measured and fit within 7 GiB;
unknown or larger sets block admission. This is not an assertion that every
historical build tree fits. Ten children have two bounded output streams each;
20 × 12 MiB = 240 MiB fits the worker-log allocation. Logs must be drained with a
bounded stream reservation or fixed bounded buffering, rather than making one
journal record per arbitrarily small pipe read.

The archive allows at most 4,096 entries and 16 MiB of headers; the known capture
inventory has 2,471 entries. Source selection and export must also respect that
entry ceiling. The journal is one shared 512 MiB pool, not separate controller
and broker pools. At most 250,100 records of at most 2,048 bytes consume
512,204,800 bytes. Snapshot indices and bounded logs are charged to the carved
8 GiB pool. The capture-open emergency marker is prepaid as 1,024 metadata bytes;
348 directories require 356,352 bytes within the existing 1 MiB marker reserve.

The policy conservatively requires the entire free-disk floor on every resource
check, including during work. As data accumulates it can stop earlier than a
precise remaining-reservation calculation would. It never weakens the protected
floor or deletes prior data to recover space.

## Source-based command bound

`static_rpc_bound()` retains the correlation between a first turn's fixed prompt
and cap and the next turn's retained head. It does not treat all 252 planned
state captures as full C4096 captures. The planned graph has 180 nonempty state
captures, 29,088 KV chunks and 4,217 state-vector rows. Adding four worst-case
failed attempts yields 268 state captures, 192 nonempty captures, 36,000 KV
chunks and 4,737 state-vector rows.

For a state with head `h`, the source-call bound is
`18 + 72*(h>0) + 2*(72*ceil(h/512) + requested_vector_rows)`.
The constants include capture-open, finite-read, tensor synchronization and
commit operations. Owned copies cost 16 commands each; bounded receipts cost
four each. Adding all row/decode calls, append starts, request trace/finish,
trim/reset, producer calls and startup allowance gives **199,196 native
accounting commands**, below the 250,000 command ceiling. It retains every
comparison, read and finite-value check. This is a static source upper bound,
not observed GPU work or a runtime performance estimate. The controller remains
responsible for its bounded extra journal records and a single outstanding
worker.

## RAM, device and time gates

Before launch, at least 48 GiB available RAM is required: a hard 24 GiB owned
worker cgroup limit plus 24 GiB protected system availability. During work,
available RAM must remain at least 24 GiB and sampled group RSS at most 24 GiB.
Polling RSS or setting `RLIMIT_RSS` does not supply hard enforcement. The source
supports a future fresh owned child in a delegated user-manager subtree; the
read-only capability finding does not mean that a group has been activated or
that the current SSH scope is delegated. These tests only wrote ordinary mock
files. `DelegatedCgroupPlan.activate_actual()` always rejects before writes.
Future activation and native membership require separate admission and review.

The exact allocated GPU identity, independent process/lock verification, an
external exclusive allocation covering work, and a measured no-forward
placement peak with at least 2 GiB VRAM margin are required. An idle snapshot is
not a continuous exclusive-window guarantee. Missing hard enforcement, missing
lease, unbound identities or unperformed placement tests are `BLOCKED`, even
when the arithmetic fits a read-only resource snapshot. This layer allocates
nothing and does not run those probes.

The maximum proposal window is 18,000 seconds using wall and monotonic clocks.
The last new worker start is offset 6,600 seconds; each worker has a 600-second
watchdog, and each probe 120 seconds. Native work is intended to be finished by
offset 7,200 seconds, leaving bounded export, archive and readback time. A
monotonic deadline cannot be extended by wall-clock rollback. These are stop
limits, not a claim that unexecuted GPU work will finish at a measured speed.

## CPU evidence and remaining admission

[CPU evidence](CPU_EVIDENCE/resources-01/RECEIPT.json) records 15/15 tests in
ordinary Python and 15/15 under `python3 -O`. They cover exact resource/operation
arithmetic, full input pins, the unresolved cold-ID regression, manifest hashes,
quota and disk failures, missing or expired leases, stale snapshots, ownership
conflicts, last-launch/deadline behavior, mock cgroup ownership/reentry and
permanent denial of actual activation. The preceding controller test failure
caused by `len(None)` remains in the parent evidence history; this correction
does not erase it. [The emitted manifest](CPU_EVIDENCE/resources-01/FROZEN_MANIFEST.json)
is a reproducible nonauthorizing template.

Run the resource tests from this directory with an absolute, nonexistent ordinary
output directory: `python3 test_resources.py --out FRESH_ABSOLUTE_DIRECTORY`.
The optimized-mode check uses a second fresh directory and `python3 -O`.
They do not import native libraries or touch the cgroup filesystem. The test
results establish CPU preparation only. Actual cgroup activation, exclusive GPU
allocation, loaded binary/model/tokenizer/template/producer identity, native
capture provenance, placement peak, reference repetition and all 261 native
checks remain unexecuted or unapproved. N1b, N2 and performance measurement are
outside this manifest.
