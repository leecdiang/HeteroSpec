# B570 existing-material external delivery

This delivery implements PR145's `bc5157c46a2999b5716e9968cc5b5571e4e6e930` native-material prompt using PR148 `41cb7504ece1f78109fde6895b10ffc56dff8ef1`. It packages existing bytes only. No model inference, GPU replay, native rebuild, timing or performance experiment is part of this delivery task.

Use this document as the current entry point. `kit/README.md`, `RESULT.md`, `RESUME.md`, manifests and receipts are preserved historical material; their original machine paths are provenance. They are not relocation commands. The original full archive is preserved unchanged.

## Access and contents

`ACCESS.json` in this result PR supplies the authenticated GitHub Releases entry, exact asset IDs, download URLs, sizes and SHA256 values. The repository is private: a collaborator needs read access and a GitHub login/token that can read the repository. This is controlled external access, not an anonymous public release.

| Asset | Contents | Expected CPU result |
|---|---|---|
| `B570_MINIMAL_SOURCE_REQUEST_V1.zip` | Complete pinned upstream source tarball, historical build kit/overlays, real Q/K/V/mask and four stage outputs, full HumanEval/115 R/PQ/QB historical reference and captured request evidence, stage replay evidence | All selected files and source lineage match; 175 full request vectors and 16 stage comparisons pass |
| `B570_FOUR_INPUT_REFERENCES_V1.zip` | All four PR134 historical request reference directories, input identities and CPU auditor | All selected files and source lineage match; 914 vectors and all four R/PQ/QB endpoint/state relationships pass |

No model weight, executable or numerical DLL is redistributed by either new package. The source package rebuilds all numerical libraries and shaders. `DEPENDENCIES.md` and `MODEL_SOURCES.json` give the exact model bytes and official acquisition paths. Historical binary identities remain recorded in the preserved kit; a rebuild on another host is a new runtime requiring qualification.

## Download, unpack and verify without a GPU

Python 3.12 or later is recommended. Authenticate GitHub using Git Credential Manager, or set `GH_TOKEN` / `GITHUB_TOKEN` in the local process environment. Never put a token in a command argument or commit it. The downloader sends credentials only to the GitHub API and removes them from signed-storage redirects.

From the result PR checkout, choose a new short directory:

```powershell
$delivery = (Resolve-Path benchmarks/b570_native_delivery_v1).Path
$work = 'C:/b570-delivery-review-new'
New-Item -ItemType Directory -Path $work -ErrorAction Stop
python -B -X utf8 "$delivery/download.py" --access "$delivery/ACCESS.json" --asset minimal --dest "$work/B570_MINIMAL_SOURCE_REQUEST_V1.zip"
if ($LASTEXITCODE -ne 0) { throw 'Download failed' }
Expand-Archive -LiteralPath "$work/B570_MINIMAL_SOURCE_REQUEST_V1.zip" -DestinationPath "$work/minimal" -ErrorAction Stop
$bundleRoot = (Resolve-Path "$work/minimal").Path
$kit = Join-Path $bundleRoot 'kit'
$referenceRoot = Join-Path $bundleRoot 'references'
python -B -X utf8 "$bundleRoot/delivery/verify_package.py" --root $bundleRoot --out "$work/audit-minimal"
if ($LASTEXITCODE -ne 0) { throw 'Integrity or CPU audit failed' }

python -B -X utf8 "$delivery/download.py" --access "$delivery/ACCESS.json" --asset four_input_references --dest "$work/B570_FOUR_INPUT_REFERENCES_V1.zip"
if ($LASTEXITCODE -ne 0) { throw 'Download failed' }
Expand-Archive -LiteralPath "$work/B570_FOUR_INPUT_REFERENCES_V1.zip" -DestinationPath "$work/four-input-references" -ErrorAction Stop
python -B -X utf8 "$work/four-input-references/delivery/verify_package.py" --root "$work/four-input-references" --out "$work/audit-four-input-references"
if ($LASTEXITCODE -ne 0) { throw 'Reference audit failed' }
```

The verifier rejects missing, extra, changed, duplicate or escaping members, binds inherited bytes to the original archive's member manifest, then runs the existing CPU audits. New receipts go outside the extracted tree and cannot overwrite earlier receipts. The minimal audit checks the archived request/stage results against their historical receipt fields, excluding only relocated path fields. No native executable is launched.

For separate CPU inspection, define all paths before either command and use fresh output files:

```powershell
$bundleRoot = (Resolve-Path "$work/minimal").Path
$kit = Join-Path $bundleRoot 'kit'
$referenceRoot = Join-Path $bundleRoot 'references'
python -B -X utf8 "$kit/audit_request.py" --actual "$bundleRoot/evidence/capture-a2" --reference "$referenceRoot/qual-2" --out "$work/request-independent.json"
python -B -X utf8 "$kit/audit_stage.py" --fixture "$bundleRoot/fixture" --request "$bundleRoot/evidence/capture-a2" --replay "$bundleRoot/evidence/stage-a1" --out "$work/stage-independent.json"
```

Expected request status: `HISTORICAL_REQUEST_REPLAY_PASS`, 175 vectors (R41/PQ67/QB67), 41 output tokens, EOG. Expected stage status: `REAL_STAGE_REPLAY_AUDIT_PASS`, 16 comparisons, visible keys `[350, 351]`. These inspect prior native results; CPU checks do not themselves establish new native qualification.

Do not run the historical `collect_results.py` against this relocated layout. It expects the source host's live run directory and loaded-module paths. Its preserved summary is historical evidence, while the new verifier provides the portable package audit.

## Prepare a runtime on another B570 host

The commands below are for a later hardware reproduction by the recipient; they were not executed in this packaging task. Install the official Windows/MSVC/Vulkan dependencies described in `DEPENDENCIES.md`. Obtain both exact model files from `MODEL_SOURCES.json`. The bundled upstream tarball avoids a moving download dependency.

```powershell
$bundleRoot = (Resolve-Path "$work/minimal").Path
$kit = Join-Path $bundleRoot 'kit'
$referenceRoot = Join-Path $bundleRoot 'references'
$nativeRoot = Join-Path $work 'new-native-runtime'
$modelRoot = 'D:/models/gguf' # Replace with the actual externally supplied model directory.
$vulkanSdk = 'C:/VulkanSDK/1.4.357.0' # Replace with the actual installed SDK directory.
New-Item -ItemType Directory -Path $nativeRoot -ErrorAction Stop
$expected = (Get-Content "$kit/SOURCE_INPUTS.json" -Raw | ConvertFrom-Json).upstream_archive_sha256
if ((Get-FileHash "$bundleRoot/upstream.tar.gz").Hash.ToLowerInvariant() -ne $expected) { throw 'Upstream source archive mismatch' }
python -B -X utf8 "$kit/prepare_source.py" --archive "$bundleRoot/upstream.tar.gz" --dest "$nativeRoot/source"
if ($LASTEXITCODE -ne 0) { throw 'Source preparation failed' }
cmake -S $kit -B "$nativeRoot/build" -G 'Visual Studio 17 2022' -A x64 "-DLLAMA_SOURCE=$nativeRoot/source/llama.cpp-0cae43063cf15170e91a2ff4d034da0ecef4a1b2" "-DCMAKE_PREFIX_PATH=$vulkanSdk" -DGGML_NATIVE=ON -DLLAMA_BUILD_NUMBER=10839 -DLLAMA_BUILD_COMMIT=0cae43063
if ($LASTEXITCODE -ne 0) { throw 'Configure failed' }
cmake --build "$nativeRoot/build" --config Release --parallel 4
if ($LASTEXITCODE -ne 0) { throw 'Build failed' }
python -B -X utf8 "$kit/freeze.py" --bin "$nativeRoot/build/bin/Release" --model-root $modelRoot --out "$nativeRoot/FREEZE.json"
if ($LASTEXITCODE -ne 0) { throw 'Runtime/model freeze failed' }
```

Only after source/model verification, a recipient can perform the bounded stage and natural-request checks:

```powershell
python -B -X utf8 "$kit/run_native.py" --manifest "$nativeRoot/FREEZE.json" --receipt "$nativeRoot/stage.receipt.json" --limit 30 "$nativeRoot/build/bin/Release/stage_replay.exe" "$bundleRoot/fixture" "$nativeRoot/stage"
if ($LASTEXITCODE -ne 0) { throw 'Stage replay failed' }
python -B -X utf8 "$kit/audit_stage.py" --fixture "$bundleRoot/fixture" --request "$bundleRoot/evidence/capture-a2" --replay "$nativeRoot/stage" --out "$nativeRoot/stage-audit.json"
if ($LASTEXITCODE -ne 0) { throw 'Stage audit failed' }
python -B -X utf8 "$kit/run_native.py" --manifest "$nativeRoot/FREEZE.json" --receipt "$nativeRoot/request.receipt.json" --limit 240 "$nativeRoot/build/bin/Release/formal.exe" "$nativeRoot/request" "$modelRoot/Qwen3-8B-Q8_0.gguf" "$modelRoot/Qwen3-0.6B-Q8_0.gguf" "$kit/INPUT_PANEL.json" qual 2 $nativeRoot
if ($LASTEXITCODE -ne 0) { throw 'Request replay failed' }
python -B -X utf8 "$kit/audit_request.py" --actual "$nativeRoot/request" --reference "$referenceRoot/qual-2" --out "$nativeRoot/request-audit.json"
if ($LASTEXITCODE -ne 0) { throw 'Historical request mismatch' }
```

This reproduces **PR134's target and draft both on B570/Vulkan**, Qwen3-8B/0.6B Q8_0, F16 KV, k=1, physical q1 prefill and context thread settings8. It does not reproduce PR143's later CPU-draft QB/thread8 timing study. The delivered stage is the first layer0 q2/key512 verification of HumanEval/115; its q1 control is a first-query slice. No broader model, shape, driver or performance claim follows.

## Custody and provenance

Each package contains a new `manifest.json`, the unchanged original member manifest and original archive identity. Every inherited member retains its bytes and source path. New instructions and tools are under `delivery/`; no historical README, result or failed attempt is rewritten.

The original `B570_NATIVE_DELIVERY.zip` SHA256 `78abc364729fed7ba0f8b92cf3594eed2511df181714e9f53b19ede2a4465973` remains in source-host custody. It contains the complete earlier evidence, including failed attempts and historical binaries. That local path is not advertised as external access. The two new assets provide the minimal complete source/request replay and all four historical references externally. Neither CPU revalidation nor publication of these bytes changes historical results.
