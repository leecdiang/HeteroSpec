# RTX boundary confirmation v1 — measured results

Status: **COMPLETE_CORE_AND_PROSPECTIVE_HOLDOUT; SOFTWARE_FIRST/HOLD**.

Read [RESULT.md](RESULT.md) for the actual scientific conclusions and limits.
The native Windows/CUDA collector is implemented and the dispatched UUID is closed.
**Do not resume or rerun any GPU entrypoint for this UUID.**

- 3,008 actual GPU hosts / 99,088 graph calls; all numerical/placement/input/module
  checks passed, zero failed/unstarted planned GPU tasks and zero scientific retries.
- H1 full numerical qualification; H0 anchor qualification; 192-host A/A pilot.
  Buffered H1 selected using same-QB evidence only. Per-anchor A/A envelope median
  changed from16.054% to2.762%; this does not certify2% resolution.
- Full52-input core, four arms and eight blocks in two separately started sessions.
  Both QB labels execute exactly the same QB graph implementation. Completed-graph
  QB_A/QH_C=0.900826; alternateQB=0.901081.
  Nineteen of24q2/q4geometries clear the descriptive controls; five remain unresolved.
- Frozen new-seed q3/GQA holdout, all12inputs and eight blocks complete.
  QB_A/QH_C=0.962421. The rule gets12/12mean directions right but overpredicts
  margins; charging its measured lookup does not improve fixedQB. No holdout retuning.
- 128 pureCPU hosts separately measure common-Q packing/fullKV copy/mask creation.
  Their phase-sum accounting is not an integrated decoder/request measurement.

**Clock telemetry validity is NOT ESTABLISHED.** RawSM reports include0 and63915;
retain them as reported, without conversion or causal explanation. The frozen
eligibility gate did not use that channel. No frequency-normalized/kernel/hardware
claim is established; endpoint telemetry does not prove continuous exclusivity.

## Evidence and implementation

[Generated results](results/) · [Raw location/recovery](RAW_LOCATION.json) ·
[Exact artifacts](EXACT_ARTIFACTS.json) · [Actual commands](COMMANDS.md) ·
[Implementation amendments](AMENDMENTS.md).

- `collector.cpp`: unchanged inherited arithmetic/shared numerical stack, owned
  persistent input storage, H0 legacy-style and H1 buffered observation.
- `collect.py`: new single-worker execution entry, strict actual source/input
  identity, independently captured serial references, repeated qualification,
  A/A and balanced acquisition. Historical runs are never dispatched.
- `prepare_rtx.py`, `test_rtx.py`, `test_evidence.py`: full logical-index recipe,
  actualGGML CPU graph/address tests, Windows cleanup and raw-evidence negatives.
- `export_rtx.py`: independent CPU byte audit, real-order checks and compact export.
  `analyze.py` remains the original declared block-level statistical implementation.
- `prediction_rtx.py` / `holdout_rtx.py`: one frozen rule and gated prospective
  new-seed extension. No actor/model request or architecture simulation is included.
- `cpu_preparation.cpp` / `cpu_prepare_audit.py`: actualCPU prepare/readback bytes,
  disjoint timing and separately labeled complete-input phase sums.
- `seal_rtx.py`: exact local archival/restore and new-interpreter byte recomputation.

Raw archive: 81711members / 226521598bytes,
SHA256 `0a6d714a1f094307da77ee583a45fdb35571b82bbdcce6b9fa6100ac5da89693`. RAW_LOCAL_ONLY underCONTRIBUTING; no remote raw
upload or external independent review. Exact numeric runtime DLLs remain pinned
in their existing author-approved directory; they are not bundled wholesale.

## Original declared design

The following files preserve the original CPU-ready design and research contract;
its initial “execution pending” prose describes that initial delivery, not the
current status: [PROTOCOL.md](PROTOCOL.md), [DATA_AND_RECEIPTS.md](DATA_AND_RECEIPTS.md),
[RTX_PROMPT.md](RTX_PROMPT.md), [initial validation](VALIDATION.md).

The core has24q2/q4geometries plus twoq1controls, each with two synthetic value
patterns, all32heads/fullchannels/keys/masks. Holdout is sixq3/GQAgeometries, two
newseeds. These are not naturalprompts or independent population draws. A changed
runtime/observer/decoder requires its own scope and qualification. B570, paper,
main, release and automations remain untouched. This DraftPR is not merged.
