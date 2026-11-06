# TPDS phase one: attribution, practical service and sparse scale transfer

Status: framework/source-staging work; **new native builds and GPU results NOT_RUN**.
User-approved scope: the 2026-11-06 next-stage design. This directory is added to
separate RTX PR190 and B570 PR191 descendants. Neither historical branch is edited.
Read `PLATFORM.json`, the corresponding `RTX.md`/`B570.md`, then `EXECUTION.md`
and `HOST_ADAPTER.md`. Execute independently; do not wait for the other platform.

## Implemented here

- `design.py`: exact sparse matrices, outcome-free input selection, four-arm
  Williams confirmation schedules, and sixteen genuine persistent-worker bursts.
- `stage_native.py`: verified-source staging of two existing CUDA arithmetic cores
  and one common frontend. Runtime cut scope is independent of the core choice.
  The entry overlay supports real target-only loading and result-ready markers.
- `stage_b570_probe.py`: actual-capacity guard, q32 last-only output mask and
  append timing overlay for the existing known-token probe. Native allocation
  remains host-bound; the old reserve32 probe is not silently inherited.
- `analyze.py`: complete-panel checks, four direct factorial contrasts plus a
  root-log interaction, clustered bootstrap with multiplicity, sparse descriptive
  comparisons, and persistent-burst service/host-window reporting.
- `receipts.py`: saved PR190 phase costs, normalized trace signatures, independent
  branch decisions, and explicit source-only portable packaging.
- `native/burst_clock.hpp`: optional host-only interval helper, no GPU sync or model.
- Tests use synthetic data/source fixtures. They never establish native equality.

Native numerical qualification, historical ledger/supervisor and actual backend
tracing are reused from the parent, not replaced by a new audit framework.
Original-host ABI/build binding remains executing-agent work. The files include
ordinary engineering freedom; a source anchor error is an integration task, not
permission to stop the campaign at CPU tests.

## Start without a GPU

```sh
cd benchmarks/tpds_phase1_v1
python3 -m unittest discover -s tests -v
python3 -O -m unittest discover -s tests -v
python3 design.py rtx-struct --out NEW/rtx_structure.json
python3 design.py b570-struct --out NEW/b570_structure.json
```

`python` is also suitable on a host where it resolves to Python 3.11 or newer.
The native model runner must consume the generated plan through the existing
owned-process supervisor and cumulative reservation ledger. These commands only
write schedules. Analysis needs NumPy; stage/design/receipt tools use the standard
library. Do not install a new GPU driver/OS, rent compute or download models here.

## Binding and execution

RTX input to `stage_native.py` is a JSON with `base_commit`, `cores`, `frontends`.
Each of `cores` and `frontends` has `loop4` and `packed`; each item contains a local
`root` and explicit `{relative_path: sha256}` `files`. Recover these from final
PR190 source/runtime manifests, not from guessed example hashes. The five required
frontend sources are entry.cpp, worker.cpp, resident_context.hpp, phase_plan.hpp,
target_capture.hpp. Both frontend snapshots must match before adding common
residency support. Core source manifests include transitive build inputs.

```sh
python3 stage_native.py HOST_BINDING.json NEW/candidates
# If the R2 entry overlay needs adaptation, R1 can proceed independently:
python3 stage_native.py HOST_BINDING.json NEW/r1_only --factorial-only
python3 receipts.py saved-costs PARENT_RESULTS.json NEW/saved_costs.json
python3 design.py natural --inputs FROZEN_COHORTS.json --out NEW/r1.json
python3 design.py burst --inputs FROZEN_COHORTS.json --primers EXPOSED_A EXPOSED_B --out NEW/r2_workers.json
python3 analyze.py natural NEW/r1.json NORMALIZED_RECORDS.json NEW/r1_analysis.json
python3 analyze.py structural NEW/rtx_structure.json STRUCTURAL_RECORDS.json NEW/structural_analysis.json
python3 analyze.py burst NEW/r2_workers.json BURST_RECORDS.json NEW/r2_analysis.json
```

Only generate/execute the natural schedule after the scientific question and
qualification decision. Do not fill budgets for their own sake. All qualification,
failed forwards, references and warmups consume the platform's existing ledger.
R1 natural may close as redundant while R2 and portable build work continue.
B570 C4096 may be unavailable while C1024 qualification and clean rebuild continue.

## Canonical observations

Flat schedule record: `slot_id`, `status`, `qualified`, `reference_id`,
`service_s`; preserve native receipt hash, source identity and full raw receipt
beside it. Only a real independent numerical check may set `qualified=true`.
A boolean supplied to a normalization function is not that check.

Burst record: `worker_id`, `status`, `process_count=1`, `provision_count=1`,
ordered 2-primer +16-measurement `requests`; each request has root/kind/status/
qualified/reference_id/service_s. Add measured launch-to-first-result,
launch-to-first-test-result, test-burst wall, worker wall, model setup and peak
active device bytes. Host observer timestamps the flushed native marker; never
substitute native-main time or setup/N for process-launch latency. Worker clocks
and native service are nested and must not be added twice.

Completion means native code, qualification, measured applicable work and a result
PR, or a scientifically supported branch closure plus all other applicable work.
It does not mean every hypothesis wins, nor simply that these helper tests pass.
