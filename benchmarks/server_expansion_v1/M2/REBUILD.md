# M2 reconstruction and verification

This describes the source and verification workflow, not a declaration that a
pilot has completed. The result directory and its terminal status are authoritative.
Read the original Linux transfer README, ENVIRONMENT, PROTOCOL and HOST_ADAPTER,
then M/PLAN.md and M/RUNTIME_PIN.json. A new host needs its own approved single
GPU UUID, resource check and independent Linux R before candidate execution.

The actual qualified M1 parent is
55f501e9a93013a4b4d82cc4967e82b8d9054a81 (PR204). The Linux numerical predecessor
is592abdfe9267fd97ecbde18cd0ee9a1bfc319e20 (PR203); the M2 design head is
ba0a76482805e3062f76a07f1fa49f7d77bd2d19 (PR197). No moving upstream head,
Windows DLL/oracle, replacement weight file, driver upgrade or implicit precision
change is part of this reconstruction.

The source execution history is retained separately from connector-created public
commits, whose Git metadata differs. Native frontend source commit
61bcce0552b1a80e9345fa199238ebb7bc63e6ff produced both binaries and remains
unchanged through driver03. Driver01 is785e9173badb2b13308008e619e5b95fb20aaba0;
driver02 is49a90f90d4c1ce6f4fa1e656488d0478081ab6b1; actual driver03 is
ae287bce170f3af2c998bf9b2892703ff2257685. A thin source Git bundle requires the
published M1 parent. Verify its prerequisite before fetching; do not merge it.
The public source binding identifies staged tar and executable bytes.

## Fixed models and runtime

Target Qwen3-8B-Q8_0.gguf has SHA-256
408b955510e196121c1c375201744783b5c9a43c7956d73fc78df54c66e883d6.
Draft Qwen3-0.6B-Q8_0.gguf is639446688 bytes, SHA-256
9465e63a22add5354d9bb4b99e90117043c7124007664907259bd16d043bb031.
Use the original acquisition receipts for exact revisions, byte counts and
applicable licenses. q8 here means verification width8, not weight precision.

The deployment used Ubuntu22.04.5, GCC11.4, CMake3.31.6, CUDA12.5.40,
driver595.84, SM86/A5000, Python3.11.14 and NumPy2.3.5. All new arms use two
native threads on the same recorded CPU affinity, F16 KV, C1024, no flash
attention, target UB32/reserve8 and draft prefill UB4/reserve1. R remains
UB1/reserve1. Original k3/reserve4 timings are a separate configuration.
Changing the host/toolchain is a new deployment requiring numerical qualification.

## Native build and history

The original reference, loop4 and packed numerical archives were fully built
from the fixed Linux source packet. M2 verifies that full source/dependency
closure and relinks a new transaction/reservation/tape frontend against the
unchanged Linux CUDA archives. It does not borrow an old executable or Windows
library. The compile/link commands, generated frontend, dependencies, module
maps and all source epochs are included as text. Compiled binaries and weights
are not redistributed.

After reconstructing the qualified predecessor on an authorized host, the native
build entry point is:

```sh
python -B benchmarks/server_expansion_v1/M2/build_native.py \
  --baseline "$HS_WORK/run-01" --runtime "$HS_WORK/m1-runtime-01" \
  --out "$HS_WORK/m2-build-NEW"
```

Use a fresh output directory. Host paths in archived receipts are redacted;
they are evidence bindings rather than portable commands. On the retained host,
source03 verifies completed01/02 snapshots, exact payload/build/module identities
and every consumed old operand before reuse. An incomplete or failed native
run cannot be reused. There is no reservation refund or reset of old counters.

Source03 is the actual history-bound queue, not a turnkey launcher for an empty
machine. A fresh host must regenerate its own independent R/M1 operands and
initialize a new host adapter, epoch and cumulative ledger; it must not invent
old snapshot files or reuse redacted allocation identities. Rebuild the same
native source and keep the complete vector/KV/transaction/physical gates. The
archived token/forced-prefix jobs make the finite operands reproducible. Raw
vector/KV payloads remain retained on the original authorized host, with public
byte commitments; public hashes alone do not independently prove equivalence.

The qualifications and timing are automated by queue.py: reserve8 bridge,
all8 natural paths, actual256-token geometry, controlled transactions, native
negative cases, owned native draft tapes and their replay bridge, then a frozen
24-worker descriptive panel only if all gates, budget and time permit. The API
phase name `confirmation` reuses the predecessor's exact24-slot admission guard;
this M2 study is descriptive and never queues576 tests. Postprocess_v2.py reads
back every retained capture and sanitized text and replays fixed statistics
without a model call. Additional profile observers and any observer continuation
are separately recorded; they do not change the frozen native driver.

## Public byte and statistical replay

Download the exact result commit. Its PARTS.json lists every gzip part and SHA;
concatenate in manifest order and verify the complete gzip SHA/byte count. Keep
TEXT_INDEX, BINARY_CAPTURE_INDEX, EXPORT_SCOPE and LOCAL_READBACK alongside it.
The complete stream uses the original canonical public-text-bundle schema.
Large expanded archives must be streamed one record at a time.

```sh
python -B benchmarks/server_expansion_v1/M2/replay_public.py \
  --bundle /path/to/assembled-archive --out /path/to/FRESH-public-replay
```

The helper verifies the complete public stream/index chain, original raw receipt
commitments, all144 timed/primer request records, physical counters, endpoints,
clean APIs, graph reuse and sampled memory, then recomputes the fixed descriptive
results exactly. It does not rerun models, reconstruct monotonic host clocks or
requalify original private GPU allocation/numerical state. Incomplete panels do
not admit a complete-pilot statistical replay or performance claim.

Width_analysis.py adds the predeclared LP7/other-arm and fixed-cut/projection
k7/k3 tables. Its input is the complete panel plus the pre-timing declaration;
use --text-index for original byte commitments when input text was sanitized.
Compare replay and live separately. Read same-k/same-projection contrasts before
cross-k totals. Count producer work separately from free target replay and retain
all startup/hash/load/primer/request-string clocks. Clock categories overlap;
process wall is not GPU kernel time, and first completed request is not TTFT.

No native qualification is inferred from exit status alone. No public raw-capture,
population-confirmation, new blind sample, manuscript, merge or Release claim is
made by the byte/statistical checks.
