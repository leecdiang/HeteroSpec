# Reproduce the B570 phase-one review-v2 result

This result starts at PR193 head `eed20261b5820ea4f778fb5a1012cb07e98dfea4`.
The execution-source commit is recorded in `RUN_SOURCE_COMMIT.json`. The original
R and prior releases remain separate immutable dependencies. No model weights
are included. No RTX or speculation-profit panel is part of this result.

## Evidence reconstruction, without a GPU or models

Use Python 3.12 and NumPy. Download every archive part and `INDEX.json`,
`MEMBERS.json`, `object_archive.py`, `recompute.py`, `README.md` from
[the dedicated evidence release](https://github.com/leecdiang/HeteroSpec/releases/tag/b570-phase1-review-v2-evidence-20261107)
into a fresh DOWNLOAD directory. Repository access is required. The result PR's
`evidence/B570_DELIVERY_READBACK.json` records the authenticated download check;
it is same-host verification, not external native replication.

```powershell
python DOWNLOAD/object_archive.py verify --root DOWNLOAD
python DOWNLOAD/object_archive.py restore --root DOWNLOAD --out RESTORED
python -B RESTORED/delivery/recompute.py RESTORED RESTORED_CHECK.json
```

The last command refuses model-weight access and process launches. It verifies
every token object, reconstructs every distinct complete serialized KV state in
memory, and checks its original raw SHA256 and parser round trip. It rechecks the
original-R bridge, required complete vocabulary vectors, full active KV,
frontiers, reset/EOG/cap/pending controls, all 216 slots, actual module identities,
ledger reservations and cost coverage. Raw `.bin` files are represented by
lossless `.bin.pack.json` recipes plus `state-token-cas`; they can be reconstructed
with the delivered `state_codec.encode`. The original flat files remain on the
experiment host. Compare the result with `AUDIT.json`; the restored report adds
an explicit `state_storage` verification section.

## Native build from a fresh directory

Use Windows x64, the recorded Visual Studio 2022 MSVC 14.44.35207 toolchain,
Windows SDK 10.0.26100.0, CMake/Ninja and Vulkan SDK 1.4.357.0. The actual compiler
dependency reports, compile/link argv, response files, linker library searches,
environment and tool/runtime hashes are in `BUILD_INPUTS.json`,
`COMPILER_DEPENDENCIES.json` and `BUILD_FREEZE.json`. Installed SDK/compiler/system
DLL bytes are external prerequisites; their hashes are retained, not redistributed.

The source entry is `native02/CMakeLists.txt`, with relative source/header/generated
and library dependencies in `native02/inputs`. The original common static and
ggml import libraries are explicitly pinned ABI dependencies. They are not
presented as freshly rebuilt shaders. The original and PR169 Vulkan backend
implementations, licenses and binding receipts are retained in `repro`; the final
F32/p021 backend is the already admitted PR169/191 implementation.

In an x64 Visual Studio developer command prompt, from RESTORED:

```bat
set PHASE1_DEPS=%CD%\fresh-dependencies
set VULKAN_SDK=YOUR_INSTALLED_VULKAN_SDK
cmake -S native02 -B fresh-build -G Ninja -DCMAKE_BUILD_TYPE=Release -DPYTHON=python.exe
cmake --build fresh-build -- -j 4 -d keeprsp
```

The compiler launcher creates real per-unit MSVC source-dependency reports.
Fresh `llama.dll` outputs go to `fresh-build/bin/R` and `fresh-build/bin/LS`.
Copy the corresponding authenticated common/ggml runtime dependencies from the
delivered frozen profiles to those directories, keeping the fresh `llama.dll`.
ORIGINAL additionally uses the unchanged original `llama.dll`. The R/ORIGINAL
Vulkan backend is `a9bcbe815d0fc1b9a7914fceb55b7275750169ec58dc8c4a09691ea0ea12f92c`;
LS uses F32/p021 `059163952ce66e26722dde75eb9dba30b4dfba59a428b3d9577b9b0d637c186e`.
They are distinct declared dependencies. `CLEAN_BUILD_QUALIFIED.json` records the
actual fresh-directory build and native four-row bridge at both capacities.

## Models, licensed inputs and requests

Use the already held Q8_0 files, with F16 KV and no Flash Attention. Matched idle
Smol135M weights/context stay resident at **both** capacities. Hashes:

- Target SmolLM2-1.7B: `0c6e8955788b1253f418c354a4bdc4cf507b8cfe49c48bb10c7c58ae713cfa2a`.
- Idle draft SmolLM2-135M: `40f7094960b6ede829145d102ca79451b364b27d9d8694d4406e002024cff357`.

Publisher revisions and model-card/license references are in
`repro/MODEL_PROVENANCE.json`: target
[bartowski revision 1f034647](https://huggingface.co/bartowski/SmolLM2-1.7B-Instruct-GGUF/tree/1f03464768bfcc0319fc50da8ff5fb20b6417ba2)
and draft
[lmstudio-community revision 04f7f8a0](https://huggingface.co/lmstudio-community/SmolLM2-135M-Instruct-GGUF/tree/04f7f8a05a8e4bc208e88d11e8c9122be36c2f9b).
Publisher conversion lineage is not independently certified. This round did not
download or redistribute weights. `TOKEN_TAPE.json` contains the deterministic
known-token diagnostic tape from the already licensed OASST pool and its source
hash/ID, selected before candidate outputs.

For a bounded qualification, the worker takes target path, idle-draft path,
capacity, method (`R`, `S`, `L`) and output reserve (`0` for R, `4` for S/L), then
reads the delivered JSONL request schema. ORIGINAL/R keep the original reserve.
q2/q4 request all rows; q32 requests only the last row. SIMPLE sets
`HS_ECON_WHOLE=1`; LOCAL uses the same LS binary without that flag. Do not replay
old absolute output paths: use fresh paths. Use the delivered supervisor and
reservation ledger with the documented resource floors before native launch.

The original-host adapter intentionally binds the host's recovered paths. A new
host must establish independent resource, numerical and module qualification and
its own freeze, not reuse the B570 performance receipts as new measurements.

## Timing and accounting scope

Native append begins immediately before resident phase binding with an assembled
query batch. It includes native reserve/planning/graph work or reuse, execution,
synchronization and requested row ownership copies. It ends after the required
sync/copies. Prefix establishment/import/reset and full owned-process costs are
retained separately. Caller batch assembly/release and response-file I/O are
included in the broader process/service envelopes but have no separate subclock;
those subcosts remain null. `service_ms` ends at receipt assembly and is not called
complete per-request response latency. The owned worker clock includes result
write/close and process termination; inclusive clocks are never added together.

The twelve fixed inside/crossing coordinates are structural diagnostics. All
three repeats and immediate same-arm warmups remain. They provide no natural
crossing frequency, population confidence interval, global service-speed average
or new Smol/k1 profitability claim.
