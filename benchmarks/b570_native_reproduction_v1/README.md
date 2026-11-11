# B570 native reproduction kit

Execution of [PR146](https://github.com/leecdiang/HeteroSpec/pull/146) on the Arc B570 host. See `RESULT.md` for measured completion, `RESUME.md` for the next action, and `PLAN.json` plus `TECHNICAL_AMENDMENT_A2.json` for the finite validation contract. File integrity, native numerical qualification and historical performance are separate checks.

## Source and build

The upstream is llama.cpp `0cae43063cf15170e91a2ff4d034da0ecef4a1b2` (b10839), authenticated against 3,545 source files. `SOURCE_INPUTS.json` contains every upstream file hash and the two complete historical overlays. `SOURCE_RECOVERY.json` binds the delivered overlays/header and PR134 inputs to exact Git source archives. `patches/01-admission-cumulative.patch` recovers the cumulative Vulkan predecessor, `02-av-preserve.patch` is PR132's unchanged patch, and `03-request-bridge.patch` supplies the request integration. `native/query_head.h` is the unchanged dependency. The complete overlays are used for deterministic preparation; these patches explain the lineage.

Build with Visual Studio 2022 C++ Build Tools, Windows SDK, CMake and Vulkan SDK (including SPIR-V headers and glslc). The tested versions and generated shader inventory are in `BUILD.json`. This is a **new runtime**, not an assertion of historical DLL byte identity. All numerical libraries, the shader generator and all 147 shader translation units are rebuilt. No old `.obj`, `.lib`, shader output directory or prebuilt numerical DLL is a build input.

From the repository root, use a new directory:

```powershell
$kit = (Resolve-Path benchmarks/b570_native_reproduction_v1).Path
$taskRoot = 'C:/hs/b570-reproduce-new'
New-Item -ItemType Directory -Path $taskRoot
Invoke-WebRequest 'https://codeload.github.com/ggml-org/llama.cpp/tar.gz/0cae43063cf15170e91a2ff4d034da0ecef4a1b2' -OutFile "$taskRoot/upstream.tar.gz"
$expected = (Get-Content "$kit/SOURCE_INPUTS.json" -Raw | ConvertFrom-Json).upstream_archive_sha256
if ((Get-FileHash "$taskRoot/upstream.tar.gz").Hash.ToLowerInvariant() -ne $expected) { throw 'Upstream archive changed' }
python -X utf8 "$kit/prepare_source.py" --archive "$taskRoot/upstream.tar.gz" --dest "$taskRoot/source"
cmake -S $kit -B "$taskRoot/build" -G 'Visual Studio 17 2022' -A x64 "-DLLAMA_SOURCE=$taskRoot/source/llama.cpp-0cae43063cf15170e91a2ff4d034da0ecef4a1b2" -DCMAKE_PREFIX_PATH=C:/VulkanSDK/1.4.357.0 -DGGML_NATIVE=ON -DLLAMA_BUILD_NUMBER=10839 -DLLAMA_BUILD_COMMIT=0cae43063
cmake --build "$taskRoot/build" --config Release --parallel 4
```

Stop if any command fails. Codeload transport encoding may change in the future; do not waive the hash check silently. The archived upstream tarball is part of the local delivery, and the full per-file inventory supplies the source identity independently.

## Native replay

`LOCAL_DELIVERY.json` identifies the persistent source/runtime/fixture/reference package and its hash inventory. Model bytes are deliberately excluded. Supply the two exact Qwen3 Q8_0 files from `MODEL_IDENTITY.json` in `$modelRoot`. PR134's request contract offloads **both target and draft to B570**, with context thread settings 8. This reproduces PR134; it does not change or rerun PR143's later CPU-draft QB/thread8 baseline.

Use `freeze.py` to hash the new runtime, scripts, fixed inputs and external models before requests. The supervisor launches its native worker suspended, places it in a kill-on-close Job, resumes it, records loaded modules and checks Job counts and cleanup. The one-active-process limit is not a claim of one cumulative lifetime process. Additional counted Job-process identities remain unknown and are explicitly reported.

```powershell
$modelRoot = 'D:/models/gguf'
python -X utf8 "$kit/freeze.py" --bin "$taskRoot/build/bin/Release" --model-root $modelRoot --out "$taskRoot/FREEZE.json"
python -X utf8 "$kit/run_native.py" --manifest "$taskRoot/FREEZE.json" --receipt "$taskRoot/capture.receipt.json" --capture "$taskRoot/fixture" --limit 240 "$taskRoot/build/bin/Release/formal.exe" "$taskRoot/capture" "$modelRoot/Qwen3-8B-Q8_0.gguf" "$modelRoot/Qwen3-0.6B-Q8_0.gguf" "$kit/INPUT_PANEL.json" qual 2 $taskRoot
python -X utf8 "$kit/audit_request.py" --actual "$taskRoot/capture" --reference "$referenceRoot/qual-2" --out "$taskRoot/capture-audit.json"
python -X utf8 "$kit/run_native.py" --manifest "$taskRoot/FREEZE.json" --receipt "$taskRoot/stage.receipt.json" --limit 30 "$taskRoot/build/bin/Release/stage_replay.exe" "$taskRoot/fixture" "$taskRoot/stage"
```

Set `$referenceRoot` to the delivered `references` directory before the audit. For ordinary smoke omit `--capture`, use a new output/receipt, and run indices 0,1,2,3 (HumanEval/38,65,115,127). Each native invocation executes one complete R/PQ/QB triplet. Audit against `references/qual-N` immediately after each triplet; stop dependent qualification on any mismatch. No timing mode is exposed by the delivered driver.

Stage replay accepts the real q2/key512 capture and compares QK, softmax, AV and final bytes for PQ/QB. Its q1 control uses the first query slice of that same real fixture; it is not an independently captured q1 request. No q4, key256-stage, other-layer stage or general shape qualification is claimed. Ordinary request verification does check all 36 target layers at the observed key256/key512 shapes.

Raw capture introduces synchronized readbacks. The ordinary HumanEval/115 triplet disables that hook in the same executable and provides the complete logits/state control. The first technically incomplete capture attempt is retained separately; it is not substituted for the complete fixture.

## Integrity and limits

The copied package is verified using `scripts/native_reproduction/bundle_manifest.py` and then replayed natively. This is a clean source build plus fresh-directory execution; it is not a second-machine test. The package includes source inputs and runtime binaries for local recovery, while Git retains source, small real fixture bytes, manifests and receipts. Bulk vectors and binary libraries stay in the indexed local package.

PR143 remains a limited negative practical-benefit result, including its historical helper-accounting deviation. This kit does not retime it, establish speedup, validate other model families, or alter the older Llama Q6_K failure.
