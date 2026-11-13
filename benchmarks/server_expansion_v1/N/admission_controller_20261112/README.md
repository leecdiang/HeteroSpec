# N1a controller and admission preparation — CPU only

Independent successor of Draft PR228, frozen at
f9a10b9cba9ae29b331ade43c0e92d67afd4c27c. The PR thread had no new comments.
No applicable AGENTS.md was found in the checkout or its ancestors. Only this
new directory changes; old reference, STATE, data, source, logs, failures and
budgets remain intact.

**CPU controller implementation is delivered; native execution remains No-Go.**
No model, including vocabulary-only, backend initialization, model/GPU context,
placement or forward was executed. No N1a/N1b/N2 or timing was started.
Both new native ELFs and the closed launcher artifact were compiled/linked and
inspected only, never invoked even for help or their denial path.

## What is implemented

The stage state machine follows resident R → independent repeat R → aligned cold
canonical oracle → strong whole-rechunk+loop4. Two fixed workers per stage retain
the original natural/control partition and request order. Worker close ACK leaves
WAIT_EXIT; the next worker is blocked until owned-process exit0 and complete,
bounded output evidence agree. Bare waitpid0 does not supply that evidence.

The controller binds run, manifest, source identity, PID/start/boot/UID, one worker
lease and an actual kernel FLOCK owner. It rejects unknown/replaced/lost locks,
changed STATE or manifest, caller alias changes, concurrent entries, reused worker
processes, expired clocks, partial accounting and uncertain failures. One compact
hash-chained ledger reserves requests, actual decode rows, deployments and each
classified raw/metadata write before mutation. Recovery is read-only and cannot
resume an existing STATE, refund failed consumption or create replacement jobs.

The new pure-Python staged verifier consumes the exact frozen261 graph:
27 R self checks,81 repeat checks,72 cold checks and81 strong checks.
It validates staged inventory, complete F32 vectors, every active F16 K/V scalar,
pending/frontier/EOG/cap, actual retained-prefix strides, ownership transitions
and empty reset. Hashes establish transport only; raw bits and finiteness decide
numeric comparison. Previous file seals are re-read before subsequent workers.
A first difference or semantic conflict is retained and blocks the next stage.

After R's self checks, an immutable18-input certificate binds actual provided
canonical IDs and retained heads to snapshot descriptors. Cold jobs replay those
inputs independently; repeat/strong jobs assert expected IDs while retaining
their own producer. This R certificate is not cold equivalence or GPU permission.
Every prepared job still has execution_authorized=false and unresolved native
owner, lease, allocation and loaded-identity fields.

The source-derived native worker uses a new owner-bound C++ client. HELLOv2 binds
the controller peer and worker lease. Actual backend/model/context/request/decode
hooks reach the stage broker; all normal capture/receipt writes and syncs go
through bounded controller I/O. Failure-marker credit is reserved before capture
creation. The original numerical archives, R arithmetic, producer and KV adapter
remain unchanged. The final concrete ProductionGate still rejects before native
object construction and launch.

A standard-library-only C++ supervisor implements owned pidfd/timerfd monitoring,
parent-death checks, bounded stdout/stderr drains and failure stop. It avoids a
process-wide file-size limit that would break large KV captures. CPU tests can
prove host-side stop delivery to owned mock children; they cannot prove that an
uninterruptible GPU/device task quiesces by a deadline.

## Evidence and limits

audit/ contains current actual-host read-only identity/resource checks.
CPU_EVIDENCE/ and review material preserve source-bound tests, ordinary-file
cgroup rehearsals, failed epochs, raw/sanitized log identities and compile/link
receipts. The std-only C++ probe also communicates with the actual Python broker
using a real owned CPU process; its eight row/request events are synthetic
accounting, not model work or a complete R stage.

Artificial tensor fixtures exercise staged consumers; they are deliberately
marked synthetic and contain no model output. Python results are cross-checked
against the unchanged Node raw comparator. These tests do not turn any of the
261 native checks into PASS. The native mapping remains261 NOT_RUN.

The minimum proposal is still72 planned/76 maximum requests,
69,354 planned/85,738 maximum rows and10 deployments. The total space requirement
stays553,094,505,923 bytes. No allowance was added or borrowed; controller logs
and state are carved from the existing8GiB build/text pool. The static RPC bound
and compact journal proof are in RESOURCE_PLAN.md. Five hours is a stop watchdog,
not measured completion time. Failure reserve is not automatic retry permission.

## Remaining admission

The native production connector is review-only, as documented in NATIVE_ADAPTER.md.
Its launch-owner/BINDCHILD/close-before-worker and complete supervisor result
bridge must be reviewed and connected before activation; the current entry stays
closed. An idle snapshot, JSON PASS receipt, this prompt or an accounting ACK
cannot activate it.

Separate finite device/budget/window approval, real owned-cgroup activation and
membership, external quiet/exclusive allocation, no-forward placement peak,
actual loaded identities, native supervisor/device behavior and all strict
numerical qualifications remain BLOCKED or NOT_RUN. Delegation availability is
not an activated hard limit. No real reference-repeat/cold equivalence, native
KV lifecycle, LOCAL opportunity, four-arm qualification or speed claim follows.

Stop after this CPU delivery for independent review. Do not merge, alter the
paper or old baseline, publish a Release, enlarge quotas, delete data or launch
native work.
