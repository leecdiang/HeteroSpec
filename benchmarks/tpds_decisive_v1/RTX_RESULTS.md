# RTX original-host results for PR184

This result branch continues local `f16c958c` from the exact design head
`db3793e2ca44514eaf155f2ecb671bf38c7bc17e`. It preserves the PR151 and PR171
references separately. It does not replace the PR174 AUTO null or PR177's
conditional rechunk result. B570, the manuscript and submitted arXiv are unchanged.

## Lane D: frozen confirmation invalidated

All sixteen exposed-root/arm full-state qualifications and sixteen exact
warmup/measurement priming checks passed on the original RTX. The independent
oracle retained the original scalar reserve1 path, complete prompt producer,
models, context capacity1024 and numerical modules. D1/D2/D4 changed only the
declared draft physical width; the target retained QB4. M retained the same
model/pool residency.

The complete twelve-root, four-arm, four-session schedule was published before
test outputs in commit `07b909f0acce5f6228225118cb501a525c2ac403`. All twelve
autonomous original test references and twelve independent forced final-state
references executed. The first eight main requests passed. Both warmup and
measurement of mandatory D1 at `APPS/train/65` (704 prompt tokens) then produced
the same greedy tokens but different target state:4,363,908 F16 KV elements and
all151,936 frontier values differed. The first KV difference was at token767,
layer1. Ten main requests completed;374 scheduled requests remained unstarted.
There is no full-panel performance aggregate and no selective retry.

A bounded three-trajectory GPU diagnosis reused the actual failed token head,
not a chosen offset. An independently computed scalar prefix imported into
physical cells0..766. The actual four-row call expanded attention key extent768
to1024 immediately and differed in all four complete vectors and final active
KV. A diagnostic1+3 split kept extent768 for the first row, then1024, and matched
all four vectors and final KV byte for byte. This supports a boundary-sensitive
numerical explanation; it is not a new arm, a main rerun, or a speed claim.
The unchanged mandatory D1 contract failed, so this lane is closed negative.

`host_evidence/host/D-LANE-CLOSURE.json` retains all384 planned outcomes.
`D-BOUNDARY-DIAGNOSIS.json` and `D-DELIVERABLE-RECONSTRUCTION.json` identify the
actual GPU diagnostic and its successful CPU reconstruction from delivered-format
bytes. Finite development qualification did not prove every natural test boundary.

## Lane O: original-host qualification

The same newly compiled CUDA/base modules are supplied to graph_tiles,
backend_loop4 and packed. The old PR171 oracle remains separate. All saved real
Q/K/V/O, gate/up/down and vocabulary operands for both8B and.6B models matched
the original scalar oracle at q1/4/5/7/8/9/16/31/32. Both models' thirteen selected
whole-model prefix/width cells matched full vectors, scalar continuation and
active target KV in all three arms.

Actual CUPTI traces are separate from clean timing. The loop4 route emitted one
quantize_q8_1 kernel and ceil(q/4) MMVQ kernels, including tails, on all144
model/projection/width cells. Temporary CUDA Q8_1 activation storage was not
exported; intermediate-byte equality is not claimed. The new CPU host-buffer
plugin was bridged with2592 additional real GPU operator executions while
preserving the CUDA/base/core/executable bytes. Total operator reservations are
7488, including the early failed attempts, below8192.

The natural-service qualification and formal-panel disposition are recorded in
the accompanying versioned O receipts. A build, parser test or readiness flag is
not a GPU qualification. Any invalidated main panel is reported without a
partial-subset performance estimate.

## Costs, failures and engineering

`host_evidence/UNIFIED_COSTS.json` joins all attempts to the durable SQLite ledger,
actual complete work, failed-work lower bounds, service records and host wall.
Reservations are never refunded. Model loading and pool setup are separate from
the declared resident-reset service clock and are nested in process wall; they
must not be added twice. `ENGINEERING_COSTS.json` retains separately measured
configure, compile, link and tokenizer costs. Missing failed-work measurements
remain unknown, not zero. Artifact/installation time without an independent
receipt is not presented as measured zero.

Every native launch uses finite request/row/operator reservations, an owned host
lock, time limit, live memory/disk polling and GPU reserve checks. Historical early
development telemetry limitations remain in the raw records; later checks are
not retroactively attributed to those runs. The overall ceilings remain8192
model trajectories,16,000,000 decoded rows and8192 isolated operator executions.

Retained failures include old adapter admission errors, CUDA build attempts,
the shared-DLL clock initialization crash, missing CPU host-buffer registration,
CPU-backend configure incompatibility, a controller finalization failure, and a
development disk-reserve interruption. These are distinguished from D's actual
numerical failure. The packed development request interrupted by disk reserve
was repeated in a fresh directory after storage repair; completed exactly-bound
GPU receipts were reused. No timing was retried to obtain a favorable result.

## Reproduction

The release index supplies each part's byte length and SHA256. The portable
bundle records original absolute paths as identifiers and stores deduplicated,
losslessly compressed chunks. Model GGUF files are not included; their complete
SHA256 identities are in the freezes and jobs. Saved projection operands,
original/candidate source, compiled workers/modules, reference payloads,
failures, build commands, exposure inputs and telemetry are included.

`restore_delivered_host.py` accepts either the ZIP or its `.parts.json` index.
The latter seeks across verified parts without creating another full-size ZIP.
It writes only under a fresh destination and shares duplicate payloads locally.
For example:

```powershell
python restore_delivered_host.py raw-evidence.zip.parts.json D:/rtx184-qualification/O-root0 restored-O-root0
python qualify.py restored-O-root0/graph_tiles/capture.json restored-O-root0/free/capture.json restored-O-root0/bank/capture.json replay-qualification.json
```

Repeat with the other arms/roots to independently recompute recorded finite
qualification. This is an offline check of actual GPU-produced bytes, not a new
native qualification. The compact `D-boundary-repro.zip` includes the actual
failed-head diagnostic, its profile and comparisons; it was restored and
independently rechecked before delivery.

For native reconstruction, restore the pinned source/build/runtime subtrees and
use the exact compiler/link commands in their receipts. The historical contexts,
caller flags, reserve sizes and numerical libraries must remain unchanged.
Source paths are original-host paths, not a claim of portable numerical equality
on another driver/compiler. Rebuilding is not permission to relabel a new binary
with an old qualification or resume an invalidated frozen panel.

Raw availability is explicit in the file/chunk manifests. Retired local payload
paths remain reconstructible; no failed capture was replaced with a success
flag. No hidden-padding equivalence, universal runtime attestation or endpoint-
only substitute for target-state equality is claimed.
