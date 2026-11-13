# CPU implementation and server handoff

## What now runs
`adapter.py` is an executable CPU adapter, not a native controller. It restores exact original R input tokens, selects a deterministic H candidate panel, materializes the **actual S3 worker JSON ABI**, and emits concrete argv inventories. It imports no backend, invokes no subprocess and does not manufacture a GPU reservation. Native performance/qualification remains NOT_RUN.

Public S3 source archive: commit `ab695a766d055f7d3c6b1fed0720c579c749bcdb`, `benchmarks/server_expansion_v1/strong_baseline_followup_20261110/S3_F2_20261110_RESOURCE02/S3_F2.tar.gz`. SHA256 `d8511c2d124655b99d0562750974d476bc4b75bed4810ac116f08ee6bb4ae6f2`, 4,802,349 bytes. Its original roots hash matches the historical report. Extract to a fresh folder with Python 3.12+ tarfile `filter='data'`; never overwrite the deployment. These are public text input/source/job records, not missing numerical captures.

```sh
# S3_ARCHIVE points to that extracted archive; P points to this PR directory.
cd "$P"
python adapter.py freeze --archive "$S3_ARCHIVE" --out /tmp/s3-followup-inputs
S3_ARCHIVE="$S3_ARCHIVE" python -m unittest -v test_adapter
S3_ARCHIVE="$S3_ARCHIVE" python -O -m unittest -v test_adapter
# Replace MODEL with the actual retained GGUF path. These commands only write JSON.
python adapter.py materialize --archive "$S3_ARCHIVE" --roots frozen_inputs/R_ROOTS.json --cohort R --day 1 --model "$MODEL" --out /tmp/s3-R-day1
python adapter.py materialize --archive "$S3_ARCHIVE" --roots frozen_inputs/R_ROOTS.json --cohort R --day 2 --model "$MODEL" --out /tmp/s3-R-day2
python adapter.py materialize --archive "$S3_ARCHIVE" --roots frozen_inputs/H_CANDIDATE_ROOTS.json --cohort H --day 1 --model "$MODEL" --out /tmp/s3-H-day1
python adapter.py commands --plan /tmp/s3-R-day1 --config /path/to/local-paths.json --out /tmp/s3-R-day1-argv.json
```

Local path config schema: `{"executables":{"R":"/absolute/transfer-worker","model":"/absolute/model-worker"},"gpu_uuid":"actual allocated UUID","output_root":"/new/successor/output"}`. The argv producer does not verify those paths exist and does not launch them. It records expected original ELF identities, so a rebuilt binary cannot silently become an identical-binary replication.

## Corrected qualification accounting
The initial design omitted clean bridge requests. The real `execution_s3_v1/verify.py::complete_bridge` requires **both heavy and clean**. Each first-date/root now uses R, repeated R, B-heavy+clean, C-heavy+clean: six requests in four processes. Second-date sentinel slots 0 and 6 use twelve requests in eight processes. No hidden free clean request.

| Panel | Qualification | Warm+measured | Planned requests | Request ceiling | Conservative row ceiling |
|---|---:|---:|---:|---:|---:|
| R day1+day2 |72+12|192|276|292|93,440|
| H |72|96|168|176|56,320|
| Total |156|288|444|468|149,760|

Actual fixed-input reserved rows: R day1 37,548; R day2 24,084; H 39,340; total100,972. Native actual work can be lower after EOG. Worker starts remain96+56+96=248 because heavy/clean share a qualification process. The 24 reserve requests are failure allowance, not automatic retry authorization. All ceilings remain proposals, not approved GPU spending.

## Real deployment compatibility checked on CPU
- R IDs and complete token arrays match byte-verified historical ROOTS.json.
- Every generated B/C job's non-input/non-path fields equals its real archived S3 template; this includes capability_request and scalar-loop vs independent-group selection.
- R entries keep original service names and all registered state positions; candidate heavy/clean names match the existing checker; formal names are exactly warm/measured.
- Tests exercise integer/vocabulary boundaries, duplicate inputs, cap/day/cohort input constraints, modified R rejection, no overwrite, request counts and command construction. 10 tests pass in ordinary Python and `-O`; no assert-only admission checks.
- H is fixed as a **candidate** using the archived exposure table, original12 exclusion, ID/token/normalized-description deduplication and input-only SHA rank. Later project exposure has NOT been reconciled; do not call it globally unexposed. No model output used in selection.

## Remaining native connection, explicitly not implemented here
No direct A5000 environment appeared in available environment inventory. No live server filesystem, ELF, model, current resource or lock state was inspected. Cloud CPU tests are not on-server native `--echo`, GPU qualification or timing.

1. On the server, locate retained R and S3 model binaries/model and original numerical readers. Run the model binary's documented **CPU `--echo JOB`** for generated B/C jobs after confirming loader behavior and dependencies; no ordinary `JOB OUT` invocation in this CPU preparation task.
2. Implement a small successor launcher around the existing native `JOB OUT` ABI and original `repeated_R`, `complete_bridge`, `clean`, `row` readers. Do not run old `run.py` or reuse its historical admission file/ledger. The S3-specific `host.py` supports S3/S3_QUAL but is tightly coupled to old certificates and budget; the earlier execution_v1 host is not the S3 host.
3. Original `model_entry.cpp` requires `complete_F0_readback`, `complete_F2_readback`, `prior_S1_qualified` and formal numerical/oracle flags. These must be backed by new evidence/reference to retained unchanged qualification, not filled true merely to make execution work. A minimal successor frontend admission shim may be cleaner; if rebuilt, explicitly label it and retain numerical objects/clock. Do not change arithmetic, old artifacts or historical approval.
4. Connect qualification before formal requests, record every reservation before launch, enforce panel/day budget together, and bind day2 to day1 same deployment and >=24h separation. Keep useful timeout/cooperative locking; no new hostwide sandbox/monitoring project.
5. Existing heavy capture reader writes sizeable raw states. One-root streaming/retention integration and its peak disk estimate are not yet implemented. The80GiB proposal is **not a proven sufficient bound**. Do not run all heavy jobs into80GiB and hope it fits. Preserve originals; any disposal covers only newly created scratch and needs its execution retention approval.
6. Refresh current GPU/RAM/disk/quiet window, reconcile H exposure, then request the corrected bounded native run. A JSON command inventory alone is not a ready-to-execute campaign.

The new reusable input/ABI work removes guesswork without presenting missing native integration as completed. No GPU call, new model forward, archive deletion, old STATE edit, merge or paper edit occurred.
