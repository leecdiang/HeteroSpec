# Qwen3-14B dense transfer — executable host scaffolding

**Host closeout: REFERENCE_COUNTEREXAMPLE, 2026-11-01.** Native compilation and24-layer-parameter capacity admission passed; all40 pilot requests completed, but two inputs failed the shared-R gate. Qualification and timing were not started. See [actual results](host_execution/RESULTS.md), [independent reconstruction](host_execution/INDEPENDENT_RECOMPUTE.json) and [proposed addendum](host_execution/PAPER_ADDENDUM.md). Do not rerun the commands below for this closed cohort.

The implementation and original preparation commands below are retained as history. This work branches from completed PR151 and does not merge it or alter PR154's paper.

Start with `HOST_PROMPT.md`, `PROTOCOL.md`, then `ENGINEERING_POLICY.md`. The user has already authorized preparation and automatic gated progression. The experiment agent may repair ordinary engineering problems and continue; model/reference/panel/estimator changes are not silent repairs.

## Implemented

- `model_inspect.py`: bounded GGUF metadata reader,40-layer/40-head/8-KV-head/Q8 target checks.
- `acquire_target.py`: resumable single pinned official target download and SHA256/size check; no model loading.
- `native.py`: exact-blob-guarded adaptation of the already executed PR151 worker. Retains its native speculative loop, introduces fixed partial target offload, admits/records CPU and GPU geometry, reduces unused pools, and exports final sequence state after the clock.
- `design.py`: deterministic unexposed 2-domain ×2-length selection, native slot schema, four-session balanced six-arm schedule, complete endpoint/vector/state artifact audit, layered qualification and paired analysis.
- `run.py`: real Windows subprocess driver with Job Object kill-on-close, serialized native handshake, lock/identity/resource checks, retained failure receipts, complete-unit recovery and automatic admission→pilot→qualification→timing progression.
- `archive.py`: bounded ZIP sharding with every member reopened and SHA checked. It does not claim remote uploading.
- CPU tests include full-size synthetic vocabulary-vector artifacts and qualification mutation cases, not just schema tests.

These are substantial reusable code, **not proof that a14B CUDA/CPU request already ran**. Windows Job behavior, native APIs, actual layer geometry, resource peaks and numerical reference require host validation. A human/agent host still recovers local assets, source capsule, exact tokenizer/rendered inputs, exposure inventory and budget.

## Commands (from repository root, Python3.11+)

```powershell
$Code = 'scripts/experiments/rtx_dense14b_transfer_v1'
python -B -m unittest discover -s $Code -p 'test_*.py' -v
python -B "$Code/run.py" probe
python -B "$Code/acquire_target.py" --out 'C:/HeteroSpecModels/Qwen3-14B-Q8_0.gguf'
python -B "$Code/model_inspect.py" 'C:/HeteroSpecModels/Qwen3-14B-Q8_0.gguf' --target --hash
python -B "$Code/native.py" --repo . --out 'C:/HeteroSpecRuns/dense14b/build_source'
```

Run `build_native.py --help` in that **new staged directory**. Use `--variant original`, the original authenticated source ZIP and21-DLL manifest, known Zig/CMake/Ninja paths, and a fresh `--out`. This actually rebuilds core and worker; it never reuses an old8B executable. The inherited executable basename remains `rtx-scope-transfer.exe` inside the NEW build/bin directory. Check ADAPTATION.json and BUILD.json.

Prepare `candidates.json` and a complete `exposure.json`; see INPUT_SCHEMA.md. The native worker consumes exact token IDs, not free-form text. Use the established tokenizer path with no model generation and save rendering provenance. All12 formal tasks must be natural, unseen and selected without model outputs.

```powershell
python -B "$Code/design.py" --candidates candidates.json --exposure exposure.json --out selected_panel.json
# Fill LOCAL_CONFIG.example.json with real paths/receipts/budgets, not invented hashes.
python -B "$Code/run.py" prepare --config local_config.json --pilot calibration.json --panel selected_panel.json --out 'C:/HeteroSpecRuns/dense14b/epoch01'
python -B "$Code/run.py" advance --bundle 'C:/HeteroSpecRuns/dense14b/epoch01'
python -B "$Code/archive.py" --bundle 'C:/HeteroSpecRuns/dense14b/epoch01' --out 'C:/HeteroSpecRuns/dense14b/archive01'
```

`advance` runs all remaining allowed stages when gates pass. Do not run it under another model process. It preserves completed stages across normal interruptions; a failed/incomplete attempt is retained for explicit engineering diagnosis, not silently rerun. If cleanup cannot be certified, the lock remains for host inspection.

The four sessions can be scheduled around host availability; no three-day wait is imposed. Actual dates are recorded. This is one larger-model, partially offloaded deployment, not a pure model-size or GPU-only scaling test. R, target-only local repair and speculative PQ/QB answer different questions; keep their denominators separate.
