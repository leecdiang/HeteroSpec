# Rebuild and continuation boundaries

Use the fixed Linux source packet, compiler/CUDA and original complete numerical
source build described by PR196 and its delivered successor. Upstream reference
is `0cae43063cf15170e91a2ff4d034da0ecef4a1b2`; candidate source is
`873d16712fbf3bc04f54e9b3753515c5dbebb60f`. No moving branch or Windows DLL.
The full compiled CUDA dependency receipts remain mandatory, not just libraries.

Before CUDA initialize, use the explicitly allocated single UUID in private host
config, retain protected GPU0 and all resource reserves, and use two CPU tasks.
Check all model bytes/SHA/licenses. The model inventory and plan specify the
exact32B mixed-Q4 and0.6B Q8_0 files. Output reserve32 is a new32B candidate
contract; the pristine32B scalar R uses UB1/reserve1 and remains independent.

In a fresh installation with the same recorded root layout:

```sh
python -B prepare_host.py --work "$HS_ROOT/q32-q4-full-20261109-01"
python -B build.py --root "$HS_ROOT" --out "$HS_ROOT/q32-q4-full-build-01"
python -B seed_epoch.py --from-build "$HS_ROOT/q32-q4-full-build-01" --out "$HS_ROOT/q32-q4-full-build-04"
python -B build_frontend.py --root "$HS_ROOT" --builds "$HS_ROOT/q32-q4-full-build-04"
python -B build_operands.py --root "$HS_ROOT" --builds "$HS_ROOT/q32-q4-full-build-04" --out "$HS_ROOT/q32-q4-full-operands-build-04"
```

`build.py` actually compiles the modified graph translation unit and proves all
other archive members unchanged. The seed copies this exact new numerical core
for a fresh frontend epoch, then verifies its compiled dependency/source binding.
The operand observer/verifier are separate offline executables. A clean timing
worker never captures intermediate operands or exports states within service.

Reference preparation and execution are separate commands in `reference.py`.
The controller requires its own repeated32B R freeze before candidate forwards,
and charges exact job payloads, all reference branches and expected failures.
The source01 long-geometry timeout and partial short-case pass remain retained.
Source02 is an unused reserve32 build epoch. Source03 adds exact descriptor
dedup before JSON allocation, with every-invocation placement validation and all
original per-call physical execution records. No numerical tolerance is added.

The detached `coordinator.py` launches `qualification.py`, `finish.py`, then a
terminal-only `archive.py` reader. It is bound to this study's recorded paths,
dates, predecessor and ledger; it is not a generic command to replay over an
existing run. A new deployment must use fresh paths and an explicitly registered
schedule/allocation, and may not copy this study's reference outputs as its oracle.

Remaining gates include all full vectors,64-layer active KV/frontier, clean/heavy
bridge, all six controls, real typed operands, native EOG/cap, pending/rollback,
actual width/packing, capacity and native invalid-contract rejection. Only a
complete eligible192-request descriptive panel is analyzed. Never automatically
launch a larger confirmation panel, merge, Release, modify a manuscript or delete
raw artifacts. Public text replay is distinct from private numerical comparison.

Source04 applies the same explicit `cuda_graphs:false` to every new32B arm,
using the fixed backend original `GGML_CUDA_DISABLE_GRAPHS` switch before backend
initialization. Kernel fusion and numerical CUDA objects stay unchanged. The
scalar R and earlier completed deployments retain their original configuration.
Two graph-enabled long-loop qualification attempts timed out; both remain charged
and retained. This switch is a candidate policy to requalify, not an attributed
optimization or a performance result.

The actual latest controller sources are preserved verbatim in
`epochs/cached_recording_v1/`. Before any timing, the common frontend successor
adds complete binary PREFILL descriptors, the same full native SHA through the
pinned system libcrypto DSO, and the per-request immutable device-type cache.
`build_recording_successor.py --root "$HS_ROOT" --original
"$HS_ROOT/q32-q4-full-build-04" --out "$HS_ROOT/q32-q4-full-build-10"`
compiles both new frontends against the exact unchanged numerical archives.
Use the updated `build_operands.py` for its separate offline observer/verifier.
Record all commands, compiler, original/current archive members, full dependencies,
actual modules and ELF SHA. A rebuild never authorizes reuse of numerical results.

`prepare_recording_epoch.py` preserves all six original checks and reconstructs
complete binary descriptors offline. `prepare_cached_epoch.py` then generates
the latest common cache-policy capability, corrects every remaining direct
reserve8 constructor, and specializes the host clock records for interleaved
exact-root warmups. It copies the existing host adapter into a fresh runtime;
old host adapters, compiled baselines and result directories remain unchanged.
Review generated scripts and `ADAPTER_BINDING.json` before launching the detached
`cached_coordinator.py`. These dated controllers intentionally fail closed after
their registered deadline; a later reproduction needs a new prospective plan.

The two profiled diagnostics use unchanged native numerical ELFs and retain
complete model/dependency SHA, allocation/lock/budget checks. The first attempt
failed because Nsight starts its application in a new process group; it remains
charged. The successor admits only the exact expected native argv/UID/ELF when
proven a descendant of the own profiler launcher; all other GPU processes still
fail the original conflict check. `sample_own_cpu.c` collects only this process's
signal-context instruction pointer, without stack unwinding or external attach.
No diagnostic profiler/sampler is present in qualification or clean timing.

`prepare_batched_geometry.py` generates the later untimed batching controller
from the cached recording epoch. The exact generated sources are in
`epochs/batched_geometry_v1/`. Its compiled ELF and all original checks/inputs
remain unchanged; at most three independently reset new geometry cases share
a model-loaded worker. `batched_geometry_coordinator.py` finishes the active
request before handoff, rechecks complete identical predecessors, and detaches
the full all-six qualification, remaining gates, panel and terminal exporter.

After terminal export, `postprocess_delivery.py` runs `delivery_audit.py` without
starting any native request. It inventories all preserved errors and costs,
recomputes the192-request panel from original receipts, checks each exact-root
warmup/measurement pair and compares its96 measured rows with the independent
archive analysis. Caller/native totals include startup and ALL warmups; resident
service comparisons remain separate. Full sanitized public byte readback must
follow upload and is not inferred from local export or numerical qualification.
