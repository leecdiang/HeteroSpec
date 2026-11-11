# Native request integration and matched-history cost qualification

This experiment advances the 2026-11-11 HeteroSpec review from helper tests and
trace arithmetic to executable request-layer integration and target-operation
qualification. It adds a new, isolated directory; historical source, results,
paper snapshots, and the PR218 S3 job remain separate.

## What changed

The deferred draft tail now has a test that invokes the actual reconstructed
M2 `provision/request` code. Greedy decisions, cap/EOG handling, correction and
bonus emission, and resident reset run through that worker. The independent CPU
driver records the vectors the frontend actually reads and native sequence
state. Both compile modes use the same unmodified numerical library.

The cost probe invokes the original M2 `PhaseContext` with `LOCAL`, fixed
`n_ubatch=32`, and eight output slots. At each fixed token history it compares a
wide call with q1 calls and, where distinct, q4 chunks. It checks full vectors,
active sequence bytes, geometry, and the next continuation before allowing any
timing. New context and one-shape-warmup/reset conditions are reported separately.

**This is a CPU-validated research implementation, not a new GPU speedup.** The
synthetic request fixtures are untrained; the operation reference is newly
established for the exact backend/model/configuration. It is not the historical
paper R. Any GPU or production-model use needs its own qualification and source,
model, resource, and budget bindings.

## Results and exact evidence

The final summaries and independent audits are indexed in `RESULTS.md`.
Request-level equality and operation-width qualification are different tests:
the tail repair preserves the original target call shapes; changing q does not.
A rejected q2 operation must not be admitted merely because its argmax matches.

The fixed full operation plan has at most two input histories, q=1..8, two
measurement orders, and two explicitly named cache conditions. Qualification
failure stops the plan before timing. A separate q1-only implementation smoke
checks the measurement/reset/accounting branches; it does not rehabilitate a
rejected width or provide width-speedup evidence.

Only source, generated input specifications, and reviewable summaries belong in
Git. Raw captures, compiled binaries, model fixtures, and machine telemetry are
kept in the author evidence package. No private GPU capture or model weight is
introduced into this repository.

## Reproduce the CPU integration

Run from `benchmarks/frontier_cost_v1` in a checkout. Python 3.10+, NumPy, a GNU
C++17 compiler, and CMake are needed. The recorded implementation checks used
Python 3.12, GCC 14.2, and CMake 3.31.6 on Linux. Build and run outputs should be
outside the checkout, in a fresh directory for each attempt.

```bash
python prepare.py --work /absolute/fresh/hs-prepared --backend cpu --jobs 2
```

This acquires the whole-file-hashed public 39 MB source ZIP, verifies all 3,547
selected source/frontend members, reconstructs the pinned Linux M2 frontend,
applies the explicit deferred-tail compile switch, and builds the unchanged
`llama` numerical target. It does not load a model. An already downloaded exact
ZIP can be supplied with `--archive`; use `--cmake /absolute/path/to/cmake` if
CMake is not on PATH. A successful build is `BUILT_NOT_QUALIFIED`.

The output `PREPARED.json` provides the actual `core`, `lib_dir`, and
`candidate_frontend` paths. Use them explicitly:

```bash
python native_integration/build_integration.py \
  --core /absolute/fresh/hs-prepared/sourcekit/native/cores/loop4 \
  --lib-dir /absolute/fresh/hs-prepared/numerical_build/bin \
  --frontend /absolute/fresh/hs-prepared/frontend/candidate_frontend \
  --out /absolute/fresh/hs-integration-build

python native_integration/make_integration_fixture.py \
  --gguf-python /absolute/fresh/hs-prepared/sourcekit/native/cores/loop4/gguf-py \
  --out /absolute/fresh/hs-fixture

python native_integration/run_integration.py \
  --build /absolute/fresh/hs-integration-build \
  --fixture /absolute/fresh/hs-fixture \
  --lib-dir /absolute/fresh/hs-prepared/numerical_build/bin \
  --out /absolute/fresh/hs-request-run

python native_integration/compare_integration.py /absolute/fresh/hs-request-run \
  --out /absolute/fresh/hs-request-comparison.json
```

The synthetic vocabulary supplies native EOS metadata and requests use explicit
token IDs. This tests actual greedy vector decisions and native EOG handling;
it does not test natural-language text tokenization or model quality. The original
guarded production entry retains its GPU requirement. Its expected CPU refusal
is recorded separately, without pretending that the production CLI ran a model.

## Reproduce the operation qualification

```bash
python matched_cost/run_probe.py \
  --core /absolute/fresh/hs-prepared/sourcekit/native/cores/loop4 \
  --frontend /absolute/fresh/hs-prepared/frontend/candidate_frontend \
  --lib-dir /absolute/fresh/hs-prepared/numerical_build/bin \
  --model /absolute/path/to/bound-model.gguf \
  --inputs matched_cost/inputs_cpu.json \
  --output /absolute/fresh/hs-operation-run --backend cpu
```

The supplied CPU input manifest requires the declared 128-token untrained
fixture family. Bind the actual model digest in the receipt. A different fixture
is a different run, even if its vocabulary length is the same. See the
`matched_cost/README.md` for the exact fixture used in the recorded check, the
separate q1 smoke, input-source identities, native-call/row budgets, and the
current CUDA interface.

The operation timing window includes schedule/batch construction, original
planning/counters, decode synchronization, and owned full-logit materialization.
Prefix construction, state export, comparison, file output, and next-continuation
checks are outside and separately accounted. State export conditions the cache
before measurement: these are instrumented operation diagnostics, not clean
resident-request or steady-state times.

## What the next GPU experiment should decide

Use a committed source snapshot on one assigned, idle non-GPU0 device. Preserve
existing workloads and PR218's independent S3 accounting. Follow
`HOST_EXECUTION.md`; do not borrow unused slots from a historical experiment.

The useful output is a table of actually qualified actions and their observed
costs at the same histories, configuration, and hardware. A q8 versus q4+q4
difference includes graph, attention, shape, synchronization, and sharing effects;
it is not automatically a transferable fixed per-call cost A. The prior 4.498 ms
threshold came from a particular Windows RTX complete-service panel and explicit
proxy assumptions. It cannot be inserted unchanged into an A5000 measurement.

Even a favorable operation table must be followed by the complete-service
baseline on the same deployment and a causal controller comparison. Both arms
receive common tail/cap/backend improvements. Whole-request costs, failed
qualifications, first-use effects, and regressions remain visible. No 5% or
generality claim is established by this preparation.
