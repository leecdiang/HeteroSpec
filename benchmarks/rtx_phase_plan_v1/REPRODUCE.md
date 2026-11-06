# Reproducing the native phase-plan result

Use this result PR's final commit. The immutable design input is PR188 head
`de96c18ced307b480f360d4d88a85792fc71fd6c`. `host_evidence/host/SHARED_RULE_FREEZE.json`
and `SHARED_RULE_PUBLISHED.json` bind the actual clean executables, rebuilt native
cores and loaded numerical modules before any new Smol output. Host-only storage,
resumption, analysis and delivery code added later does not change those bytes.

## Obtain and inspect actual evidence

The private repository's authenticated prerelease is
[`rtx-resident-phase-v1-evidence-20261106`](https://github.com/leecdiang/HeteroSpec/releases/tag/rtx-resident-phase-v1-evidence-20261106).
Repository access is required; an unauthenticated404 does not indicate missing
evidence. Model weights and credentials are excluded. For example:

```powershell
gh release download rtx-resident-phase-v1-evidence-20261106 --repo leecdiang/HeteroSpec --pattern 'raw-evidence.zip*' --dir X:/phase-evidence
python benchmarks/rtx_phase_plan_v1/restore_delivered_host.py X:/phase-evidence/raw-evidence.zip.parts.json D:/rtx188 X:/fresh-native-evidence
```

Use a fresh destination with ample space. The restore tool verifies every part,
chunk and complete payload and seeks over parts without concatenating a second
large ZIP. Windows absolute paths in `FILES.json` are identifiers; restoration
cannot write to those original paths. Repeated payloads are restored as hardlinks
where supported. Select other original-path subtrees with the same command.

The bundle includes new D/E native runs, failed and partial attempts, source and
compiled candidate/reference workers, numerical modules, native core archives,
build commands, model hashes, ledger, CUDA activities and cold-storage manifests.
All retired raw states remain reconstructible. It also includes the82 inherited
original-R payload files actually consumed by the Qwen replay bank, their bank
metadata and inherited cost receipts. It does not pool their old performance
samples into the new result. Compiler cache/object/debug intermediates are
rebuildable and are not required to inspect qualification.

`host_evidence/UNIFIED_COSTS.json` lists every attempt and observed component.
`ENGINEERING_COSTS.json` records build and lossless-storage work. Full host wall
contains model setup, qualification, teacher replay and failed work; service and
phase clocks are nested components, not additional wall time. An absent component
clock is unknown. Failed reservations are never refunded.

Publication is bound by `host_evidence/host/ARTIFACT_DELIVERY_PUBLISHED.json`;
`ARTIFACT_READBACK.json` records a fresh authenticated download and recomparison
of the retained head767/q4 boundary's saved original-R, SIMPLE and LOCAL frontier
vectors and complete active KV at prefix771. Its six restored files are a
selected transport/readback check, not a full-bundle fresh download or a new
runtime qualification. `ENGINEERING_COSTS.json` keeps publication and readback
clocks separate from native service. `TOOLCHAIN_IDENTITY.json` pins Python3.11.9,
Zig0.16.0, CMake4.4.3 and Ninja1.13.2, including actual executable hashes and the
retained initial version-query failure.

## Replay comparisons without new GPU work

`develop.compare_cases` compares full originally requested vectors and committed
active KV for each registered boundary/width cell. `qualification.py` independently
reconstructs speculative traces, selects initial/first-commit/terminal states,
checks pending and stopping semantics, and compares every originally requested
target vector, including rejected branches, with separate original-R captures.
These routines use original-path bindings. On a different machine, remap the
explicit host roots to restored subtrees and keep their pinned bytes unchanged.
`storage.read_bytes` also reads a cold state's verified chunks when the original
logical path has been retired. A CPU comparison rechecks recorded GPU evidence;
it does not qualify a newly compiled runtime.

The failed Smol SIMPLE-D1 attempt owns the first three complete clean measurements
and the fourth root's complete heavy capture. `resume_storage.py` uses receipt
existence alone, reconstructs its prior input/reset/decode history in a separately
charged job, and supplies only the missing fourth-root warmup and measurement.
The composite view records both sources; it is not a native successful attempt.
All recovery clocks remain in costs and are excluded from performance samples.

## Rebuild or execute on the RTX host

The original reference is not rebuilt or replaced by candidate code. Its original
executable/core/module hashes and the independent observer bridge are retained
for each family. Use the existing four pinned GGUF assets, whose exact hashes
are in `host.py` and the raw job files. The build receipts contain the actual
Windows Zig/CMake commands and include paths. Candidate source staging uses the
saved PR171/186 source kits; the bundle contains the staged source itself.
`host.py` binds the extractor, rebuilds each native core and links the worker;
it reuses the identical qualified CUDA/CPU/base numerical modules. No upgraded
library is installed over original R.

Development actions are `develop.py matrix --family Smol`, `develop.py exact-matrix`,
`develop.py natural --family FAMILY --arm ARM`, `qualification.py FAMILY ARM`, and
`kernel_profile.py run METHOD --family FAMILY`. These commands are documented
for fresh, explicitly named output roots: current run names deliberately refuse
implicit retry. Review and create a fresh budget/owner context before reproducing
GPU work; the delivered experiment has stopped. A readiness field, helper test
or build success cannot replace the separate original-R bridge and GPU checks.

The finite support is dense single-sequence append/reset/trim, C1024, F16 K/V,
the admitted no-FA backend/arithmetic profile and unchanged original output
reservation/masks. Holes, shifts, wrapping, sliding windows and different
arithmetic/placement need separate support and qualification. Do not generalize
these results to paged or multi-sequence caches.
