# PR217 execution entry

This implementation is being prepared against design head
`c85b98636d5e0a7d9c367be8f3447b0799d12a78`. CPU compilation and fixture
success are separate from GPU numerical qualification and formal performance.
Read the parent protocol and the actual epoch's immutable F0 index, admission,
S1 certificate, F1 readback and final status before interpreting any result.

The scope is Qwen3-32B-Q4_K_M, whole target-only M, G/B/C on one allocated
A5000. **WHOLE retains the original W/SIMPLE physical-extent planner.** Its
crossing q4 caller at position255 executes physical widths1+3. This is separate
from the stateless S2 projection cells, which actually compute all4 or32 rows.
B uses a persistent private matmul marker, one batch quantization and repeated
original scalar-dot dispatch on the same stream. C retains independent channels
with ne11=1. No device dot expression or quantizer is rewritten. No graphs-on
probe, draft model, D4, second GPU or paper edit is part of this entry.

## Required fixed inputs and toolchain

Set `HS_ROOT` to the authorized Linux cache and study root. All new output
directories below must be fresh. The cache contains the original fixed Linux
source packet and completed source-build receipts from PR196/PR216:

- Pristine reference `0cae43063cf15170e91a2ff4d034da0ecef4a1b2`, its original
  independent `run-01/build-R-01` source/build/dependency receipts and scalar R.
- Candidate source `873d16712fbf3bc04f54e9b3753515c5dbebb60f`, original
  `run-01/build-loop4-01`, Q32 graph source/archive `q32-q4-full-build-04`, and
  fixed frontend `q32-q4-full-build-10`. Their full dependency bytes are checked.
  Reconstruct these inputs using the pinned PR216 REBUILD entry and the fixed
  Linux source packet; a moving upstream checkout or Windows DLL is invalid.
- Original Q32 synthetic capacity INPUT tokens, exposed native termination
  fixture, exposed root333 INPUT, state-writer profile and inherited ledger.
  Old candidate outputs and old operand gold are never used as the new oracle.
- Exact target GGUF:19,762,149,024 bytes,
  SHA256 `efd971561896866f0e910cce52761ca77b1b138090c7f15fe284676d57d1f689`.
  Obtain the licensed Qwen model using the original fixed acquisition manifest.
- Recorded CUDA12.5/NVCC, GCC11, sm86 and the existing locked Python/NumPy
  environment. No dependency upgrade, sudo, driver/power change or device reset.

This is a same-host continuation using an immutable, verified source-build
cache. A clean output directory does not mean an unprepared machine. Missing
cache/source/dependency inputs are errors; the entry does not silently download
different versions or treat transferred old outputs as qualification. Another
host/device requires its own source builds, repeated R and full qualification.

## CPU preparation, build and independent readback

Run from `execution_v1` with the recorded Python interpreter:

```sh
python -B reproduce.py build --root "$HS_ROOT" --work "$NEW_CPU_OUTPUT"
python -B reproduce.py freeze prepare --root "$HS_ROOT" --source "$PROTOCOL_SOURCE" \
  --cpu "$NEW_CPU_OUTPUT" --out "$PUBLIC_F0_DIRECTORY"
```

The finite CPU queue recompiles both changed CUDA translation units, the graph
unit and all new frontends/glue; verifies every archive member occurrence;
links scalar gold exclusively to pristine R numerical archives; checks all
new compiler dependencies and inherited closure; enumerates the complete job
manifest; runs design/execution fixtures in ordinary and `-O` modes; reads an
actual historical64-layer F16 state as a **reader fixture only**; and tests
native CPU echo, monotonic-clock compatibility and refusal without admission.
It starts zero model requests and has no automatic GPU transition.

Publish the complete reviewed F0 directory at an immutable commit, then:

```sh
python -B reproduce.py freeze verify --directory "$PUBLIC_F0_DIRECTORY" \
  --commit "$F0_COMMIT" --cache "$FRESH_DOWNLOADED_F0" --out "$F0_READBACK"
python -B reproduce.py admit --root "$HS_ROOT" --source "$PROTOCOL_SOURCE" \
  --cpu "$NEW_CPU_OUTPUT" --public "$PUBLIC_F0_DIRECTORY" --proof "$F0_READBACK" \
  --authority "$PRIVATE_USER_AUTHORITY" --out "$NEW_EXECUTION_DIRECTORY"
```

The private authority binds the actual assigned UUID and user-approved budget.
It contains no password/token. The original514-request history and640 ceiling
remain preserved; new requests are appended to one registered Q32 journal,
with both current cumulative requests and rows checked. The complete actual
manifest determines the expanded finite allowance. Per-column gold, audit
quantization, startup failures, expected rejects, warmups and closeout are
explicitly accounted. B2 has its independent8B ledger; S3 has a separate gate.

## GPU qualification and formal S2

```sh
python -B reproduce.py qualify --configuration "$ADMISSION_S1"
```

Run this command through a bounded server-side tmux/timeout wrapper after the
zero-GPU disconnect/reconnect heartbeat proof has passed. The server contains
all code, inputs, logs, locks and supervision; no SSH tunnel or Mac file is used.
The S1 queue first repeats pristine R, freezes its actual content, captures real
G scalar columns, generates independent per-column gold and quantized bytes,
then verifies all registered typed/width cells, all full151936 logits, all64
active K/V layers, frontiers, physical extents, capacity rejection, native
EOG/cap/reset and heavy/clean bridges. Actual G inputs are assembled in their
recorded column order; they are not replaced by synthetic/zero activation.

On the first unexpected failure, it preserves partial output and stops without
native retry. It terminates only its own positively identified process group
on resource conflict or timeout. It uses the original shared GPU allocation
lock, protects existing services, samples resources and preserves safety margins.

After all S1 gates pass, the server stops at
`S1_PASSED_WAITING_F1_PUBLIC_READBACK`. Publish and completely read back the
qualified sources, cells, all72 operations, graph policy, costs, caller-based
whole-panel admission and certificate. Only then provide the distinct S2
admission and run:

```sh
python -B reproduce.py run-s2 --configuration "$ADMISSION_S2"
python -B reproduce.py analyze --phase S2 --input "$S2_ROWS" --out "$REPLAY_ANALYSIS"
```

S2 consumes exactly36 fresh workers, each one same-input warmup immediately
followed by its measurement. Fixed parent-protocol order is checked against
actual host timestamps. All4/32 full vectors are caller-owned and fenced;
operation time includes quantization, launches and complete output copy. Restore,
startup/hash/load, warmup, serialization, caller and fixed gaps are retained.
The common clean-window lock excludes this study's build/download preparation.
Counters describe instrumented application calls; opaque library launches and
driver VMM allocation are unknown. GPU memory snapshots are not guaranteed peaks.

CPU preparation and admitted S1 continue after SSH disconnect. Public GitHub
publication/readback must actually occur before F1 can admit S2; lack of a
server-side authenticated publication mechanism is a safe checkpoint, not
permission to fabricate a successful freeze. Work may finish that publication
while online. No further user confirmation is needed for already approved steps.

## Archive and independent text replay

Use `reproduce.py archive create` with an explicit terminal reviewed public-text
selection, then `archive replay` into a new directory with the transport SHA.
The reader rejects links, traversal, duplicates, missing fragments, truncation
and overwrite. Keep original private vector/KV/weight/activation payloads. State
clearly whether a check is historical reuse, host numerical qualification,
public byte/statistical replay or an independent GPU replication. Public hashes
alone are not a public numeric rerun. Optional B2 and S3 require their own
complete registrations; neither may interrupt or consume the other's budget.

Safe stop: create `STOP_REQUESTED` in the active phase output directory. A
healthy active worker finishes; no new worker starts. To reconnect, read
`STATE.json`, `workers/*/HOST.json`, the canonical ledger and live launch PID/
start-ticks before doing anything. Never repeat a worker whose outcome is unknown.
