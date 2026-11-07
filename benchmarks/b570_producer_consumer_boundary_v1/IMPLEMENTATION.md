# Native implementation and execution entry points

The 2026-10-28 extension adds `native/boundary.cpp`, `CMakeLists.txt`,
`prepare_panel.py`, `execute.py`, `run_native.py`, and `analyze.py`.
The protocol and its original CPU validator remain byte unchanged. The original
`plan.json` is retained as the design-stage draft; actual execution requires a
separate bound `FROZEN_PLAN.json` and its byte-checked launch manifests.

## Build and numerical custody

The new CMake project compiles only `boundary.exe`. It imports the PR148/150
qualified `llama`, `ggml`, and `ggml-base` import libraries; it does not rebuild
numerical libraries. Copy the five qualified DLLs beside the executable. The
freeze checks those copies against the qualified runtime, hashes the models and
driver sources, and records the actual new executable identity. The supervisor
records loaded module hashes; a missing/substituted numerical module prevents
qualification.

```powershell
cmake -S benchmarks/b570_producer_consumer_boundary_v1 -B $build -A x64 -DLLAMA_SOURCE=$preparedSource -DQUALIFIED_BUILD=$qualifiedBuild
cmake --build $build --config Release --target boundary
python benchmarks/b570_producer_consumer_boundary_v1/execute.py freeze --bin $bin --models $models --qualified-runtime $qualifiedRuntime --selection $selection --out $freeze
python benchmarks/b570_producer_consumer_boundary_v1/execute.py run --freeze $freeze --references $references --out $newRun
python benchmarks/b570_producer_consumer_boundary_v1/analyze.py --plan "$freeze/FROZEN_PLAN.json" --records "$newRun/REQUESTS.jsonl" --payload-root "$newRun/raw" --reference-root $references --out $newAnalysis
```

All output directories must be new. A source change requires a new freeze. A
failed native attempt remains in the ledger; this entry point has no retry flag.
The native argument list is `boundary OUTPUT TARGET DRAFT PANEL SLOTS`.

## Observation and state contract

Both observation arms retain metadata-only attention descriptors, actual caller
IDs/positions, and real boundary exports. The `heavy` arm additionally persists
every complete trajectory vector. Metadata callbacks return false and do not
read tensor contents or request an additional graph execution. Verification
descriptors use the unchanged PR148 observer implementation and ordering; new
producer and ordinary descriptors are stored separately. A physical micrograph
histogram is explicitly unknown. The off/on comparison therefore tests the
additional full-logit observer, with common metadata instrumentation present.
This operational definition is recorded before native forwards in `FREEZE.json`.

Restoration starts with a fresh target context whose layout stays fixed. The
sequence API imports the donor bytes, exports an actual receiver readback, and
compares the full serialization and positions. A separate receiver-owned FP32
initial vector is persisted and consumed once by the same first-maximum rule.
No target forward recreates the boundary. Draft prefill remains serial P1.

Content-addressed storage deduplicates only bytes already read from the native
producer/receiver or full logit array. Existing content is byte-compared before
reuse. The 8 GiB unique-payload cap is enforced on every new payload write.
The supervisor retains the original suspended-process Windows Job containment,
module inventory, cleanup receipts and single active worker policy, with the
protocol's 900-second per-input limit. Individual requests have the frozen
180-second soft deadline. Owned model-worker time is summed across inputs.

## Qualification and interpretation

Each worker runs one input in frozen slot order. Native own-path or observer
mismatches stop that worker immediately. The host independently audits original
historical payloads after each control input. All 32 B0 slots must qualify before
any B1 worker can start. A historical failure is retained as REFERENCE_MISMATCH;
any already-executed dependent record retains its output but cannot qualify.
Remaining coordinates receive explicit NOT_RUN_DEPENDENCY or NOT_RUN_BUDGET.

`analyze.py` recomputes both audits before producing all 48 scientific cells,
including missing/failed/unrun cells. It keeps strict-R and producer-conditioned
comparisons distinct. P4T conclusions remain limited to the boundary0 clean
receiver contract. No new performance inference is produced.

Compilation and synthetic CPU tests alone are not native qualification. Actual
execution status and evidence receipts must be read from the run's audit files.
