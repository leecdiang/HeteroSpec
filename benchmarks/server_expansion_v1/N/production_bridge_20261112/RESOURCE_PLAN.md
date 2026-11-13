# Unapproved finite resource and export plan

This is a CPU-prepared proposal. It authorizes no GPU context, model execution,
placement action, activated cgroup, five-hour lease or numerical qualification.
The independent ledgers remain 72 planned / 76 maximum requests and 69,354 /
85,738 rows, with ten each of backend/model/context/placement actions. Four
failed-attempt slots do not supply automatic retries or new runnable IDs.

The original disk proposal stays **553,094,505,923 bytes**:

| Pool | Bytes |
|---|---:|
| Raw vectors and active KV | 143,804,276,736 |
| Capture metadata | 398,458,880 |
| One shared controller/broker journal | 536,870,912 |
| Raw + metadata + journal | 144,739,606,528 |
| Archive reserve | 147,651,175,875 |
| Independent raw/metadata/journal restore | 144,739,606,528 |
| Existing build/text pool | 8,589,934,592 |
| Protected free disk | 107,374,182,400 |
| Total | **553,094,505,923** |

The archive may additionally contain at most 1 GiB of the already-budgeted
bounded logs, state and records. Its input plus the existing 16 MiB header bound
is at most 145,830,125,568 bytes, below the same archive reserve. Strict readback
of that ancillary 1 GiB is charged inside the existing **7 GiB artifact pool**,
alongside retained builds and sources. The independent raw restore pool does
not quietly grow. The finalizer requires
`max(selected logical bytes, selected allocated bytes) + 1 GiB <= 7 GiB`.
The remaining original 1 GiB build/text carve holds original worker/controller/
bridge logs and controller/domain/bridge state. No extra restore allowance is
introduced.

The [named final retained set](review/MEASURED_SELECTION_FINAL02.json) contains
7,953 explicitly selected files: 2,631,178,832 logical bytes and 2,650,431,488
unique-inode allocated bytes, including the final launcher03 and protocol
source09 replacements. Adding the ancillary readback uses 3,724,173,312 of the
7,516,192,768 artifact-pool bytes and leaves 3,792,019,456 bytes in that pool.
The finalizer independently checks the denominator and byte sum and records the
receipt's full SHA-256. This is a measured selected-set bound, not admission or
a claim about all historical workspaces. The
[intermediate receipt](review/MEASURED_SELECTION_INTERMEDIATE01.json) and
[earlier subset](review/SELECTED_EXISTING_ARTIFACTS_PARTIAL.json) remain preserved.

Retained files are **not** the raw archive allowlist. They stay in the named
server build/source pool; source identities and pinned Git/rebuild references
provide reconstruction. The raw archive includes every required raw numerical
capture and required state/failure/ownership/transport receipt, one journal,
bounded logs and records, and source identities. It excludes retained ELFs,
objects, system/CUDA/NCCL libraries, weights, whole restored source/dependency
trees and unrelated history. No history is deleted or recursively repacked.

The raw export remains unfrozen because no native data have been generated.
Before any future export, an exact relative-path allowlist must cover all
required evidence and satisfy at most 4,096 entries, bounded relative paths and
16 MiB headers. The known 2,471 capture entries plus up to 512 bridge/domain
entries do not turn a 7,953-file retained set into an entry-cap pass. Required
evidence that does not fit produces a blocked or partial delivery; it is never
omitted to make the count pass.

The public CPU package is a separate allowlisted set of reviewed UTF-8 code,
configuration, logs, receipts and documentation, including only necessary
pinned old CPU code. It contains no ELF, object, library, model, credential or
unrelated internal path. Its frozen export receipt establishes its actual
denominator; retained-build measurements do not establish public export safety.

[RESOURCE_ARCHIVE_PLAN.json](RESOURCE_ARCHIVE_PLAN.json) is the machine-readable
policy. `finalize_resource_manifest.py --selection MEASURED_SELECTION.json --out
FRESH_OUTPUT.json` reproduces the
[enriched unapproved execution manifest](FINAL_EXECUTION_MANIFEST_NOT_ADMITTED.json) from the
pinned old request graph, selected-file receipt and archive plan. It validates
the selected denominator and byte sum, both logical/allocated bounds, shared
readback charge and unchanged archive limits. Pending replacements remain
blocked. Nine synthetic CPU finalizer tests passed in ordinary and optimized
Python; these tests neither execute nor independently measure selected files.

The [domain plan](RESOURCE_DOMAIN.md) details the 24 GiB / 128-process proposal,
dual-clock deadlines, immutable owner/device/stage/lease binding and still-closed
kernel operation body. Actual kernel limits, atomic domain process creation,
external GPU allocation, native memory/placement peak and all 261 native
numerical checks remain unexecuted or unapproved. CPU transport success is not
a substitute for any of them.
