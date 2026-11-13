# Native wiring and bounded host supervisor evidence

All native/backend/model/GPU-context/placement/forward operations are zero.
Two source-bound numerical worker ELF files were compiled/linked and inspected,
never executed. Their original reference/loop4 numerical archives and27 ancestor
compile inputs match the frozen PR228 identities. The generated worker's six
explicit IO/client substitutions retain original numerical/lifecycle code and
the unchanged permanent ProductionGate. See native/DERIVATION.json and
native_link_01/BUILD.json.

Final native worker identities:

| Role | Bytes | SHA256 |
| --- | ---: | --- |
| R | 222813032 | a4982697eddf162730e50cdac8ed748bbaa19025b580520fa05eb3bcdac305c4 |
| loop4 | 223398104 | 78ffffc3f3e3fa23b35b871a46d826297acf5bd28069b6aa6936e95514b6df10 |

The numerical worker build took44.368 seconds. Complete original symbol logs
remain private; selected real native/client symbols are public together with the
original log sizes and hashes. Nonfatal compiler warnings are retained.

client_01 contains19 normal and19 NDEBUG std-only client groups,6.863 seconds.
Both mock binaries passed the standard-library dynamic-dependency whitelist
before the first mock ran. Tests include owner PID/start/boot, lease and socket
identity, ACK/partial/timeout, local reentry, classified pre-write accounting,
short write, ENOSPC, fsync, capture-root replacement and outside/unknown paths.
These mocks issue synthetic hook events only; there is no model/backend API.

launcher_02 contains18 normal and18 NDEBUG std-only supervisor groups,9.744
seconds. Tests use fixed compiled CPU child actions, not arbitrary executables.
They cover pidfd/timerfd deadlines, zombie-owner loss, kernel parent-death,
bounded stdout/stderr, overflow, partial/ENOSPC writes, fsync after child exit0,
reused/same-inode/sparse-offset guards and the12MiB per-stream cap. Log completion,
partial state and copied byte counters are tested explicitly. The separate
closed native-launcher entry compiled with real execve/timerfd/guard symbols;
that artifact was not executed. Its production CLI and live controller adapter
remain BLOCKED. CPU PID termination tests prove host signaling of their owned
children, not CUDA/device quiescence or hardware numerical correctness.

The earlier launcher_01 test/source epoch is preserved privately with all four
original source byte hashes verified. It preceded the explicit per-stream
completion/partial/byte-result fields; it is historical evidence, not the current
header certificate. The first upload attempt also failed before compilation
because the fresh server successor directory did not yet exist; its source
archive was retained and a new empty0700 directory was then created. Old study
directories, STATE, locks and data were untouched.

interop_probe_01 records the separately compiled std-only C++ interoperability
probe identity and inspected dependencies. That receipt deliberately does not
claim execution; the parent controller's interop result records its actual CPU
execution separately. Its logical backend/model/context/placement hooks are mock
accounting events. It has no native/model library dependency.

RAW_LOG_INDEX.json binds unredacted original raw evidence and public copies.
Only private source/build/mock-root path prefixes were substituted. Complete raw
outputs and synthetic partial/crash files remain in independent private task
directories. No copied packet contains numerical model captures or weights.
