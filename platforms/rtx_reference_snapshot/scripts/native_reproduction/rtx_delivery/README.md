# RTX native delivery (PR147 result bytes)

This kit fulfills the RTX part of PR145's `NATIVE_DELIVERY_PROMPT.md` at
`bc5157c46a2999b5716e9968cc5b5571e4e6e930`. Result baseline is PR147 commit
`3429e2c49626c30e4a406a517a3e8a030aea9c7f`. Packaging and verification start
**zero native/GPU processes**. Historical measurements, failures and freezes
are unchanged. B570's separate PR148 archive is not held or delivered by this RTX kit.

## What is delivered

The private HeteroSpec Git repository is the authorized durable storage. Its
`benchmarks/rtx_native_delivery_20261026/` directory contains ordered 40-MiB
parts, `PARTS.json` (part/whole SHA256 and sizes), and `MEMBERS.json` (every
member's size, SHA256 and source). Use the immutable commit linked by that
directory's `ACCESS.json`. Repository read access is sufficient; no draft
release maintainer permission is needed. Local drive paths are not download URLs.

The package includes the original historical source/executable capsule, the
real E1 Qwen3 layer0/q3 fixture and own-arm expected stage bytes, six complete
historical/rebuilt HTTP smoke responses, and full R/PQ/QB qualification records
for GSM8K/test/443. The latter are `qual-0187`, `qual-0192`, `qual-0193`:
target-only R and captured k3/fresh PQ/QB, with **704 complete vocabulary
vectors**, including rejected/unexamined rows. The input is the already-used
stage/smoke coordinate; it was not selected by timing. All 936 formal requests
remain in the original compact records, also included unchanged.

The source capsule is the Qwen original, SHA256
`62086688fc095be2654ae25aad2c7780c94db8617db5a6a9f71504f49897bf7e`.
Metadata4 was used for other model families and is not substituted here.
Its separate archive remains available at commit
`3235d44c26edd92db33e574094c26af8e29d2452`, directory
`benchmarks/rtx_querylayout_mechanism_v1`, SHA256
`36be0d738ad5d29579b75825f68337003eb127405cc5418abc566cb07718a4d8`.

Other inputs' heavy vectors, full build products and the interrupted v1 attempt
remain **only on the source host**, indexed by PR147 `RAW_FILES.json.gz` and
`RAW_ACCESS.json`. This subset does not claim external delivery of those 26.9 GB.

## CPU-only restore and audit

Use Python 3.11+ and Git/GitHub CLI authenticated for the private repository.
From a checkout of the pinned delivery commit, in PowerShell:

```powershell
python scripts/native_reproduction/rtx_delivery/delivery.py restore benchmarks/rtx_native_delivery_20261026/PARTS.json C:/repro/rtx-delivery
$kit = 'C:/repro/rtx-delivery/kit'
python "$kit/tools/delivery.py" audit $kit
```

Use a new output directory. Restore authenticates every part, the assembled ZIP,
every extracted member and the nested compact-record archive. It checks the
preserved R/PQ/QB endpoints against the E2 reference, full speculative state,
288 PQ/QB vector pairs, recorded layout/placement, MQ own-path and PQ/QB stage
identity, all six HTTP endpoints/stops, and the existing qualification/audit
receipts. Expected audit: PASS, 3 full requests, 704 vectors, 288 equal PQ/QB
vectors, 12 recorded stage replays, 780 recorded qualification checks, 936
compact formal requests, **0 newly started native processes**. This is CPU
validation of preserved evidence, not a new GPU replay or second-host result.

## Obtain exact external dependencies

Weights and numerical DLLs are not redistributed. `DEPENDENCIES.json` pins
upstream URLs, release asset IDs/revisions, sizes and SHA256. Obtain the runtime
archives directly from [llama.cpp b10839](https://github.com/ggml-org/llama.cpp/releases/tag/b10839),
subject to their upstream notices/licenses:

```powershell
gh release download b10839 --repo ggml-org/llama.cpp --pattern 'llama-b10839-bin-win-cuda-12.4-x64.zip' --pattern 'cudart-llama-bin-win-cuda-12.4-x64.zip' --dir C:/repro/downloads
python "$kit/tools/delivery.py" dependencies $kit C:/repro/downloads C:/repro/exact-dlls
```

Both whole archives and **all 21 DLL hashes** must match. Only those exact DLLs
are extracted; the upstream unmodified llama server is not used as the
HeteroSpec executable. Newer CUDA/BLAS/ggml releases are not interchangeable.
The source-host delivery check freshly downloaded both archives and checked
all 21 hashes. This provides an upstream acquisition path without republishing
third-party numerical libraries.

The Q8_0 files are the exact published GGUFs from
[Qwen3-8B-GGUF](https://huggingface.co/Qwen/Qwen3-8B-GGUF/tree/7c41481f57cb95916b40956ab2f0b139b296d974)
and [Qwen3-0.6B-GGUF](https://huggingface.co/Qwen/Qwen3-0.6B-GGUF/tree/23749fefcc72300e3a2ad315e1317431b06b590a).
**No conversion/quantization step is needed.** Download using the revision URLs
in the dependency manifest and retain the upstream model license. No base
checkpoint lineage beyond the identified published GGUF is claimed.

```powershell
$deps = Get-Content "$kit/DEPENDENCIES.json" -Raw | ConvertFrom-Json
New-Item -ItemType Directory C:/repro/models
curl.exe -fL --retry 3 -o "C:/repro/models/$($deps.models.target.filename)" $deps.models.target.url
curl.exe -fL --retry 3 -o "C:/repro/models/$($deps.models.draft.filename)" $deps.models.draft.url
$runtime = 'C:/repro/rtx-runtime'
python "$kit/tools/delivery.py" prepare $kit $runtime --dll-dir C:/repro/exact-dlls --target C:/repro/models/Qwen3-8B-Q8_0.gguf --draft C:/repro/models/Qwen3-0.6B-Q8_0.gguf
```

Preparation is CPU-only: hash weights/DLLs, check/extract all 3542 original
capsule members, and write a new runtime tree with local model paths. It never
edits archival JSON. Historical absolute paths in receipts remain provenance;
active paths derive from `$kit`, `$runtime`, explicit model/DLL arguments and
explicit build-tool arguments. The original `rtx_recover.py` is included as
an unchanged helper for `sha/read/save`; do not invoke its old host-specific main.
The extractor supports deep Windows source paths using extended paths. Keep
the native build root short (such as `C:/repro/rtx-runtime`) because external
compiler/linker path limits are separate from the archive extractor.

## Optional native reproduction on another RTX host

The following commands are **not part of this packaging task and were not run
for this delivery**. They require a compatible Windows RTX/CUDA driver/device
and the dependencies above. They write a new reproduction, never extend PR147's
finite timing campaign. Do not interpret their incidental timings as new
performance evidence. Python, Zig 0.16.0, CMake 4.4.3 and Ninja 1.13.2 were used
in the original core/frontend build; their original hashes are in the preserved
build receipts. Supply local tool paths explicitly; no D: mapping is required.

```powershell
$zig = 'C:/tools/zig/zig.exe'
$cmake = 'C:/tools/cmake/bin/cmake.exe'
$ninja = 'C:/tools/ninja/ninja.exe'
python "$kit/tools/build.py" $runtime --zig $zig --cmake $cmake --ninja $ninja
python "$kit/tools/stage.py" $runtime
python "$kit/tools/request.py" $runtime
```

`build.py` rebuilds core/frontend objects only and retains the fixed external
numerical DLLs. It does not rebuild CUDA kernels/NVIDIA libraries and does not
claim byte-identical executables. `stage.py` checks original/rebuilt × MQ/PQ/QB
× two repeats against shipped expected bytes. `request.py` preserves and checks
six original/rebuilt R/PQ/QB HTTP responses against the historical E2 endpoint.

For the complete captured natural-request comparison:

```powershell
python "$kit/tools/bridge_build.py" $runtime --zig $zig
python "$kit/tools/bridge_run.py" $runtime "$runtime/DELIVERY_SLOTS.json" request-replay --timeout 600
python "$kit/tools/delivery.py" audit-request $kit "$runtime/request-replay"
```

The unchanged v2 worker runs only the three delivered slots. CPU `audit-request`
requires exact endpoints, stop conditions, speculative state and all 704 vectors,
including rows not selected for output. It ignores elapsed time. A mismatch is
a failed reproduction, not permission to replace reference bytes. Preserve the
new output and its own executable/driver identity. No formal schedule or
campaign script is needed for this minimum reproduction.
