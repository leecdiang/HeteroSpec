# Verification and delivery

**PASS.** The independent CPU parser reconstructed all 171 fresh formal records from raw selected logs/traces and verified 1,596 per-run file bindings. It imports no controller capture/comparison helper and does not use its PASS flags. All exact keys, prompt bytes/prefill IDs, settings, full committed arrays, endpoints, transcript bytes, native handoffs, repetition stability, historical bridges and comparison tables pass.

Engineering was separately audited (12 runs). Seven negative tests passed: truncated capture, duplicate keys, mixed attempts, early EOS and cap/marker risks. A separate strict-JSON settings audit covers 183 engineering/formal records and 122 native handoffs; it checks F16 KV, non-unified contexts, greedy settings, exact queue/order, draft k=2 and 24/24 thread flags, and the first-sample/pending/transfer sequence. U2 has one loaded target/context and no draft argument/load/speculative initialization or transfer. No arbitrary internal function-call tracing is claimed.

All 80 local model/data/runtime/native/tokenizer bindings match after execution. GPU UUID, driver and OS match preparation. The unchanged qualified instrumentation is reused with the documented local four-task smoke coverage; the old 120-array/30-sham campaign was not rerun. The historical lead reparses 114 restored native logs and uses the pinned old U2/reference array export, with its 12-thread caveat.

The frozen reason-only endpoint metric remains explicit. The supplementary full boundary is (length, EOS/limit reason, terminal ID): U2/N1 57/57; U2/N0 and N0/N1 54/57. Joint array/boundary agreement remains 57/57, 51/57 and 51/57. /15's different lengths are visible; /25 differs in IDs with the same boundary. All 60 recorded uncommitted target samples are retained outside committed-array equality.

## Actual archive/readback coverage

All **11** new Git-backed parts, the index and manifest were downloaded from the authenticated repository at `1903ade3507b6a9df8390f44ca88fe83f922ce42`. Every length/hash matches. Joined archive: **523,758,950 bytes**, SHA256 `26995b3a07789fd6311141e074c49909811a333c642504bbd5b1a3a655e81427`. Clean restoration checked every CAS blob and all **2,276 logical files**.

The frozen verifier was executed from the restored source against the restored evidence and again passed all 171 records. SUMMARY, ARRAYS, WITNESSES, COMPARISONS, RETROSPECTIVE_LEAD, task CSV, supplementary settings and strict-boundary outputs are byte-identical to the original independent audit. The settings checker only adds an external output-path option to avoid rewriting restored hardlinks; its predicates are unchanged. Supplementary boundary code/tables and later final reports/receipts are separate Git objects; the raw snapshot contains the earlier explicitly labelled reason-only table. No frozen execution code, argv, selected outcome or denominator changed.

Transport failures were retained: three gh raw API attempts returned `transform: short source buffer` and only two bytes; an identity-header diagnostic also failed. A binary-safe reader of the same authorized API succeeded. Credentials stayed in memory and were never written. Failure bodies/logs are in delivery_failures/ and READBACK_FAILURES.json. No GPU run was repeated to repair transport.

Git-backed parts avoid temporary Actions-artifact expiry, but require repository access and continued repository availability. Hash consistency/Git membership do not independently authenticate omitted weights/runtime binaries, the physical execution or absolute experiment clock. Opaque sampler bytes, later live-prefix KV and U2 internal state remain unavailable. No performance/energy/VRAM or universal equivalence claim follows.
