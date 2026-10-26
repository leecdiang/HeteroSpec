# B570 external dependencies and model acquisition

This delivery uses a source-build-only route. It distributes source, fixed inputs, existing evidence and integrity checks; it does not distribute model weights, EXE/DLL runtime files, driver files, SDKs or Microsoft redistributables. The retained runtime hashes and loaded-module inventories identify historical executions. They are not files to copy from the original machine.

The delivery work on 2026-10-26 checks packaging, access and bytes on the CPU. It does not run GPU qualification, model inference or performance experiments. A recipient's rebuilt runtime or new host must receive its own native qualification before it can inherit any numerical claim. Integrity checks alone do not supply that qualification.

## Exact models

[MODEL_SOURCES.json](MODEL_SOURCES.json) records the two fixed official Hugging Face revisions, direct file URLs, licences and metadata endpoints. On 2026-10-26, the official revision APIs returned these exact LFS SHA-256 values and sizes; both repositories were public and ungated. Only metadata and licence text were fetched during this delivery check.

| Role | Original filename | Bytes | SHA-256 |
| --- | --- | ---: | --- |
| Target | `Qwen3-8B-Q8_0.gguf` | 8,709,518,112 | `408b955510e196121c1c375201744783b5c9a43c7956d73fc78df54c66e883d6` |
| Draft | `Qwen3-0.6B-Q8_0.gguf` | 639,446,688 | `9465e63a22add5354d9bb4b99e90117043c7124007664907259bd16d043bb031` |

Download the [target GGUF at revision 7c41481f](https://huggingface.co/Qwen/Qwen3-8B-GGUF/resolve/7c41481f57cb95916b40956ab2f0b139b296d974/Qwen3-8B-Q8_0.gguf) and [draft GGUF at revision 23749fef](https://huggingface.co/Qwen/Qwen3-0.6B-GGUF/resolve/23749fefcc72300e3a2ad315e1317431b06b590a/Qwen3-0.6B-Q8_0.gguf) without renaming or conversion. Both already contain the required quantized weights and tokenizer. No Transformers conversion, new quantization or separate tokenizer download is needed. The exact historical Transformers source revision and converter version for the draft were not recorded; the fixed official GGUF bytes are the reproducible input.

The repositories supply Apache-2.0 licences: [target licence](https://huggingface.co/Qwen/Qwen3-8B-GGUF/raw/7c41481f57cb95916b40956ab2f0b139b296d974/LICENSE) and [draft licence](https://huggingface.co/Qwen/Qwen3-0.6B-GGUF/raw/23749fefcc72300e3a2ad315e1317431b06b590a/LICENSE). Recipients obtain the weights directly from those publishers and retain the applicable licence and notices if redistributing them.

Run this PowerShell block from the directory containing this document and `MODEL_SOURCES.json`. Choose a new destination with room for both files. The commands fetch the pinned official URLs, check every byte's SHA-256 and the size, then install each file under its original name. They do not run inference. A failed download or check stops before the file is accepted.

```powershell
$ErrorActionPreference = 'Stop'
$modelRoot = 'C:/hs/b570-external-models' # Choose a fresh destination.
if (Test-Path -LiteralPath $modelRoot) { throw 'Use a new model destination' }
New-Item -ItemType Directory -Path $modelRoot | Out-Null
$spec = Get-Content -LiteralPath './MODEL_SOURCES.json' -Raw | ConvertFrom-Json
foreach ($model in $spec.models) {
    $partial = Join-Path $modelRoot ($model.filename + '.part')
    curl.exe --fail --location --retry 3 --output $partial $model.download_url
    if ($LASTEXITCODE -ne 0) { throw ('Download failed: ' + $model.filename) }
    $bytes = (Get-Item -LiteralPath $partial).Length
    $hash = (Get-FileHash -LiteralPath $partial -Algorithm SHA256).Hash.ToLowerInvariant()
    if ($bytes -ne $model.bytes -or $hash -ne $model.sha256) {
        throw ('Model identity mismatch: ' + $model.filename)
    }
    Move-Item -LiteralPath $partial -Destination (Join-Path $modelRoot $model.filename)
    Write-Output ('Verified ' + $model.filename + ' ' + $hash)
}
```

For weights already present, hash them in place instead of downloading or changing them:

```powershell
$ErrorActionPreference = 'Stop'
$modelRoot = 'D:/models/gguf' # Existing model directory.
$spec = Get-Content -LiteralPath './MODEL_SOURCES.json' -Raw | ConvertFrom-Json
foreach ($model in $spec.models) {
    $file = Join-Path $modelRoot $model.filename
    $hash = (Get-FileHash -LiteralPath $file -Algorithm SHA256).Hash.ToLowerInvariant()
    if ((Get-Item -LiteralPath $file).Length -ne $model.bytes -or $hash -ne $model.sha256) {
        throw ('Model identity mismatch: ' + $model.filename)
    }
    Write-Output ('Verified ' + $model.filename + ' ' + $hash)
}
```

## Source, tools and drivers

The native source is llama.cpp commit `0cae43063cf15170e91a2ff4d034da0ecef4a1b2` with the recorded HeteroSpec overlays. Use the delivered upstream archive and per-file source inventory with `prepare_source.py`, following the delivery README. Do not substitute an unpinned llama.cpp checkout or a prebuilt numerical library. Build commands and historical tool hashes are recorded in the reproduction kit's `README.md` and `BUILD.json`; `RUNTIME_A2.json` identifies the final historical runtime.

| Dependency | Recorded environment or use | Official acquisition entry |
| --- | --- | --- |
| Python | Use Python 3.12+ for source preparation and CPU integrity/audit scripts; those scripts use the standard library. | [Python Windows releases](https://www.python.org/downloads/windows/) |
| Visual Studio C++ Build Tools | Visual Studio 2022; compiler `19.44.35228.0`, toolset directory `14.44.35207`; x64 C++ tools. | [Visual Studio 2022 release history](https://learn.microsoft.com/en-us/visualstudio/releases/2022/release-history), [Microsoft downloads](https://visualstudio.microsoft.com/downloads/) |
| Windows SDK | `10.0.26100.0` recorded by the build. | [Windows SDK downloads and archive](https://learn.microsoft.com/en-us/windows/apps/windows-sdk/downloads) |
| CMake | `4.4.3` recorded by the build. | [CMake downloads](https://cmake.org/download/) |
| Vulkan SDK | `1.4.357.0`, including `glslc` and SPIR-V headers. | [Official 1.4.357.0 release announcement](https://www.lunarg.com/lunarg-releases-vulkan-sdk-1-4-357-0/), [LunarG SDK downloads](https://vulkan.lunarg.com/sdk/home#windows) |
| VC++/OpenMP runtime | Historical loaded modules include `MSVCP140.dll`, `VCRUNTIME140.dll`, `VCRUNTIME140_1.dll` and `VCOMP140.DLL`. Obtain the runtime through Microsoft's installer. | [Microsoft runtime guidance](https://learn.microsoft.com/en-us/cpp/windows/latest-supported-vc-redist?view=msvc-170), [official x64 redistributable](https://aka.ms/vc14/vc_redist.x64.exe) |
| Intel Arc driver and Vulkan runtime | The delivered native qualification records Arc B570 driver `32.0.101.9034`. The Vulkan loader/ICD comes from the host's official driver/runtime installation. | [Intel Arc Windows driver](https://www.intel.com/content/www/us/en/download/785597/intel-arc-graphics-windows.html), [Intel historical drivers](https://www.intel.com/content/www/us/en/download/857252/historical-intel-arc-graphics-drivers.html) |

These official pages are acquisition entry points, not a frozen installer bundle. The exact original installer hashes for MSVC, Windows SDK, Vulkan SDK, CMake, Microsoft runtime and the Intel driver have not been established in this delivery. Historical `cl.exe`, `glslc.exe` and `cmake.exe` hashes in `BUILD.json` are installed-tool hashes, not installer hashes. Select the recorded components when they remain available and record what is actually installed.

At the 2026-10-26 check, Intel's main page offered `32.0.101.9150` and its historical page displayed `32.0.101.8826`; neither is a verified fixed download for the recorded `32.0.101.9034`. The Microsoft x64 redistributable link also tracks a changing release. Microsoft requires a runtime at least as recent as the build tools. Any available replacement version changes the recipient environment; it does not establish identity with the original runtime or transfer the original qualification. This delivery does not install those replacements.

## Licence and module boundaries

Preserve the original source licences and copyright notices when extracting, modifying or redistributing source. Relevant locations are:

| Component | Licence evidence in the supplied sources |
| --- | --- |
| HeteroSpec harness and delivery code | `delivery/LICENSE`, copied from the repository root `LICENSE` (MIT, Chengzhan Li). |
| llama.cpp / ggml | Upstream archive root `LICENSE`; reproduction kit `native/UPSTREAM_LICENSE` (MIT, ggml authors). |
| nlohmann JSON | Upstream `licenses/LICENSE-jsonhpp` and `vendor/nlohmann/json.hpp` (MIT, Niels Lohmann). |
| llamafile CPU matrix kernel | Full MIT notice at the start of upstream `ggml/src/ggml-cpu/llamafile/sgemm.cpp` (Mozilla Foundation). |

Other bundled upstream source notices remain in the original archive and must be retained. Microsoft build tools/runtime and Intel drivers remain subject to their vendor installation/licence terms. Download them through the official entries above; no third-party runtime or driver binaries are redistributed in this package.

The historical receipt `receipts/smoke-0-a1.receipt.json` includes GamePPSdk's `GPP_VKLayer64.dll` and Windhawk-related modules in its loaded-module inventory. Those entries describe the original host and are **not delivery dependencies**. Do not install them merely to match the inventory. The historical module list is retained as evidence; a new host must record its own modules and complete separate qualification. Neither retaining that inventory nor checking this package executes the GPU.

Repository evidence: `benchmarks/b570_native_reproduction_v1/{MODEL_IDENTITY.json,BUILD.json,RUNTIME_A2.json}`, `reports/b570/B570_ENVIRONMENT_QUALIFICATION.md`, `reports/358h/358H_CANONICAL_DRAFT_RESOLUTION.md`, and `reports/358h/358H_PROVENANCE_AMENDMENT.md`. Paths in this paragraph are repository-relative. The three identity/build JSON files are also under `kit/` in the minimal package; the research reports remain available in the repository.
