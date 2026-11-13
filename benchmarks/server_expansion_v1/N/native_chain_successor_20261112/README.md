# N1a original-source native-chain preparation: CPU only

Successor of PR227 at d1b4f909fdb33c732b951489c123237c4f057850 and
PR226 at 87ea17971642f65468678cee8477505b9956611a. Both heads were re-read
from GitHub and are unchanged. This directory adds preparation; it does not edit
the old reference, results, STATE, failures, ledgers, paper or experiment baseline.

The missing original source has now been recovered on the actual A5000 host.
All five complete source-gate SHA-256 values match. The original reference,
loop4 and packed source trees and recorded dependency closures were checked as
whole files; seven historical worker binaries match their build records.
See PUBLIC_READONLY_AUDIT.json and ACTIVE_KV_SOURCE_AND_RESOURCE.md. Neither a
source excerpt nor the CPU producer's numerical library substitutes for R.

Two new C4096 native frontends compiled and linked against the exact original
reference and loop4 numerical archives. Static nm/readelf checks retain and find
the actual decode/context/active-KV/producer/worker symbols. No resulting native
executable was started, including help, selftest or its denial path: GPU-linked
ELF initializers may run before main. BUILD_EVIDENCE records the exact source,
archive, object, executable and shared-library file identities and failure epochs.
These are file/link identities; actual loaded modules remain NOT_RUN.

Implemented preparation includes resident/repeat/cold/strong caller roles,
the original finite greedy rule, LCP trim/pending/final-token replay/reset,
caller-owned complete outputs, real source-specific active F16 K/V extraction,
and streamed F32/F16 immutable captures. The native producer uses an existing
model only, the pinned actual parser/template/task/final-response chain, and
preserves the complete actual serialization receipt before decode. No model,
including vocabulary-only, was created in this task.

A single durable accounting broker is wired into native worker calls, with
pre-exec placement reservation, request and actual-decode row pre-reservation.
It is tested only using CPU mocks. A final concrete ProductionGate rejects
every native entry before native object construction or an exec callback.
The mock broker's ACK is accounting, never admission. There is no authorized
native launcher, queued N1a run, model request or automatic continuation.

CPU fault tests cover short writes, quotas, partial work, failed trim, crash,
uncertain ACKs and reentry. Their receipts bind current source hashes.
The single-compiler CPU replay passed52+52 component checks,17+17 IPC groups,
8 independent budget groups,12 lifecycle groups,5 raw-prefix groups and194
host-layout checks in35.43 seconds. The file-only assembler passed10 tests;
independent static mapping passed9,958 assertions. Nonfatal native compile
warnings and prior failed build epochs are retained, not removed.
The 261-row map keeps every native check NOT_RUN; matching tokens, hashes,
heads or synthetic captures cannot upgrade that status. assemble_checks.js
rejects absent/partial native capture sets and uses the unchanged strict
PR226 full-byte comparison contract only on complete future evidence.

The minimal future proposal remains 72 planned / 76 maximum requests,
69,354 planned / 85,738 maximum rows, and ten deployment placements, with all
setup/oracle/control/failure consumption explicit. These numbers are not
approved. The revised storage proposal is 553,094,505,923 bytes, not the old
551 GB estimate. Five hours is a stop watchdog, not a measured completion time.
See NATIVE_PLAN.md, review/RESOURCE_PROPOSAL_REVIEW.json and STATUS.json.

**GPU No-Go.** A separate finite authorization, refreshed UUID/quiet-window
admission, resource enforcement, reviewed stage controller and successful
strict native qualification are still required. CPU preparation ends here.
No N1a/N1b/N2, timing, old panel rerun, Release, merge or paper change occurred.

Public reproducibility is limited to source, file identities, CPU mock tests,
job preparation, strict comparator/assembler tests and saved evidence. The
original host build trees, binaries and model remain private; complete original
backend rebuild dependencies are bound to their existing immutable materials.
No native raw numerical captures exist from this task.
