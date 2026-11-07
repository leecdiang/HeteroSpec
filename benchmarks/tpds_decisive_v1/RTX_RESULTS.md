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

## Lane O: complete qualified panel, limited strongest-control gain

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

All twelve arm/root natural-service qualifications, their old-R/observer bridges,
heavy/off checks and exact priming checks passed. The complete runtime, including
the CPU host-buffer plugin and actually loaded external OpenMP module, is bound
to the receipts. The twelve-root, three-arm, six-session panel was published in
`5e1120fd37da94ed1c05e725dc8869ec571020a0` and read back before test outputs.
All216 measurements and216 immediate warmups completed with identical autonomous
outputs, active target KV and final frontier. There were no main retries.

Ratios below are numerator service time / denominator service time; values above1
favor the denominator. Intervals are the frozen10,000-draw root-cluster,
family-adjusted95% intervals across the three contrasts. Repetitions are not
independent roots.

| Numerator / denominator | Primary paired geometric ratio | Primary family95 | Total-service ratio | Total family95 |
|---|---:|---|---:|---|
| graph_tiles / backend_loop4 | 1.039120 | [1.013766, 1.065643] | 1.037981 | [1.014886, 1.061901] |
| graph_tiles / packed | 1.055686 | [1.027305, 1.087877] | 1.053897 | [1.028870, 1.083232] |
| backend_loop4 / packed | 1.015942 | **[0.999886, 1.029652]** | 1.015334 | [1.002420, 1.028274] |

The prespecified primary interval for packed versus the strong loop4 control
includes1. The secondary total-service interval excludes1. Thus there is a small
favorable point estimate and a positive secondary signal, but no stable primary
superiority conclusion. Two roots (`MATH/counting_and_probability/train/390` and
`MATH/algebra/train/464`) and two sessions favor loop4; all remain included.
This is not an equivalence claim. Loop4 explains much of the larger tiles gap;
the result does not justify presenting that whole gap as a unique packing gain.
No gain is attributed to four-row verification, which does not enter wide packing.

| Arm (72 measurements each) | Total service s | Mean service s | Total prefill s | Descriptive p95 service s |
|---|---:|---:|---:|---:|
| graph_tiles | 169.270079 | 2.350973 | 89.274269 | 5.439914 |
| backend_loop4 | 163.076223 | 2.264948 | 83.899717 | 5.145627 |
| packed | 160.613421 | 2.230742 | 81.468936 | 5.149208 |

The p95 is descriptive over the fixed repeated-root panel, not an SLA claim.
`O-MAIN-RECORDS.json` retains every planned slot. The original analysis is retained;
`O-MAIN-ANALYSIS-WITH-COSTS.json` independently recomputes exactly the same frozen
statistics while attaching full costs. No statistical result changes during that
accounting step. RTX GPU work stopped after this complete panel.

## Costs, failures and engineering

`host_evidence/UNIFIED_COSTS.json` joins all attempts to the durable SQLite ledger,
actual complete work, failed-work lower bounds, service records and host wall.
Reservations are never refunded. Model loading and pool setup are separate from
the declared resident-reset service clock and are nested in process wall; they
must not be added twice. `ENGINEERING_COSTS.json` retains separately measured
configure, compile, link and tokenizer costs. Missing failed-work measurements
remain unknown, not zero. Artifact/installation time without an independent
receipt is not presented as measured zero.

The complete ledger reserves992 model trajectories,5,170,326 decoded rows and7488
operator executions. Confirmed complete work is972 trajectories,400,479 decoded
rows and6912 operator executions; including completed slots inside the interrupted
attempt raises the documented lower bounds to974 trajectories and401,451 rows.
The remaining failed work is unresolved, explicitly bounded by retained
reservations, and is not reported as zero. Known complete-plus-failed-slot service
cost is3033.091091s; summed recorded host-attempt wall is10051.711872s.
One recovered controller-finalization wall uses its documented upper bound;
it is not silently presented as an exact native duration.

For O's432 main slots, actual decoded work is276,984 rows. Measurements cost
492.959722s and immediate warmups455.594342s. The216 version-worker loads cost
888.509955s, pool setup5.764572s and post-service state diagnostics200.740996s;
these components are nested in3569.577s of main-attempt wall. Independent test
references and outer state checks bring the full O confirmation calendar span to
4057.176s. O natural-service qualification, including CPU comparison, archival,
priming and storage repair, spans2975.732s. These spans must not be added to their
nested components. `ELAPSED_STAGE_SPANS.json` also retains D and operator
engineering spans, including intervening pauses instead of silently excluding them.

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

Artifacts: [RTX decisive evidence release](https://github.com/leecdiang/HeteroSpec/releases/tag/rtx-decisive-v1-evidence-20261105).
The compact `D-boundary-repro.zip` can be inspected without the full campaign
bundle; the full bundle is `raw-evidence.zip.partNNN` plus its parts index.

The release is published within the repository's existing **private** access
scope; repository visibility was not changed. Download using an authorized
GitHub session, for example:

```powershell
gh release download rtx-decisive-v1-evidence-20261105 --repo leecdiang/HeteroSpec --pattern 'raw-evidence.zip.part*' --pattern restore_delivered_host.py --dir evidence
```

The complete ZIP stream has 77 parts and 20,522,078,183 bytes (about 19.1 GiB),
representing 76,167 logical files and 409,899,607,100 logical bytes before duplicate
sharing. Choose only the required restoration subtree and allow its disk space.
`ARTIFACT_DELIVERY_PUBLISHED.json` records all server SHA256/size checks; an
authenticated index download was independently checked against its local hash.
Stream construction, chunk checks and part uploads took 4284.234s; publication
and metadata checks took 24.844s. These are separate CPU/delivery clocks, not
model-service or GPU time. Subsequent access/document checks are not included
in those two measurements. The full remote bundle was not downloaded again.

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
