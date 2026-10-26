# B570 existing-material external delivery result

This completes the B570 packaging/access request in PR145 at `bc5157c46a2999b5716e9968cc5b5571e4e6e930`, using PR148 `41cb7504ece1f78109fde6895b10ffc56dff8ef1`. The new result is stacked on PR148. There were **zero new GPU requests, native executions, builds, or performance experiments**. CPU checks inspect existing evidence only.

## Delivered and verified

The two assets are published at the [private repository release](https://github.com/leecdiang/HeteroSpec/releases/tag/b570-native-source-reference-v1-20261026). Repository collaborators need read access and GitHub authentication. This is a persistent controlled access entry, not anonymous public hosting. [ACCESS.json](ACCESS.json) contains observed asset IDs, API/download URLs, sizes, SHA256 values and member-manifest identities. [README.md](README.md) provides the shortest download/unpack/CPU-check commands and the optional later source-build/native instructions.

| Asset | Compressed bytes | ZIP file members | SHA256 |
|---|---:|---:|---|
| B570_MINIMAL_SOURCE_REQUEST_V1.zip | 232,568,531 | 551 | `774c1ce5351fa7b1b9b60d7eb801361d3268d0f6398c6d386b22e66dd65c59ea` |
| B570_FOUR_INPUT_REFERENCES_V1.zip | 497,867,884 | 1,162 | `a0c0ab0e4f962e8be84cc8cca9b4adc518707a01f87561f40f57e657346bf95e` |

The minimal package retains 542 original members: full upstream source archive, source preparation/build kit, real stage fixture, complete HumanEval/115 R/PQ/QB reference and captured request evidence, stage evidence, original auditors and expected receipts. The references package retains 1,156 original members and makes all four fixed inputs' complete references available. Each ZIP adds provenance and delivery instructions/tools plus its root manifest. [MANIFEST_MINIMAL.json](MANIFEST_MINIMAL.json) and [MANIFEST_FOUR_INPUT_REFERENCES.json](MANIFEST_FOUR_INPUT_REFERENCES.json) are byte copies of those root manifests; their file counts exclude the manifest itself.

Both uploaded assets were **fully downloaded from the GitHub asset API into new directories**, SHA256-checked, safely extracted and CPU-audited. Downloads used the current authorized repository account while the release was staged; it was then published for repository readers. A separate collaborator account and a second hardware host were not tested. Publication preserves the verified asset IDs and hashes; the published tag/asset API state was checked separately.

| CPU verification of downloaded bytes | Result | New receipt |
|---|---|---|
| Minimal package identity/source lineage | All 550 listed files and 542 original-member bindings pass; 551 ZIP files including manifest | [Round trip](receipts/ROUNDTRIP_MINIMAL.json) |
| Existing natural request capture vs historical reference | 175 full vectors; R41/PQ67/QB67, endpoint/state fields match; historical audit fields equal except relocated paths | [Request audit](receipts/MINIMAL_REQUEST.json) |
| Existing real stage evidence | 16 comparisons pass, visible keys `[350, 351]`; historical audit fields equal except relocated paths | [Stage audit](receipts/MINIMAL_STAGE.json) |
| Four-input reference identity and internal consistency | All 1,161 listed files and 1,156 original-member bindings pass; 914 stored vectors across HumanEval/38,65,115,127 | [Round trip](receipts/ROUNDTRIP_FOUR_INPUT_REFERENCES.json) |
| Pinned source preparation from downloaded tarball | All 3,545 upstream files and overlays authenticated and recovered in a new directory; no compilation | [Source preparation](receipts/DOWNLOADED_SOURCE_PREPARATION.json) |

The four-input check invokes the pinned auditor with each authenticated reference as both arguments, checking internal R/PQ/QB relationships, input binding and historical endpoints. It is not a new model-output comparison. Per-input receipts are `receipts/REFERENCE_0.json` through `REFERENCE_3.json`; vector counts are 258/223/175/258. The minimal request check separately compares preserved capture bytes against preserved reference bytes.

Ten integrity tests pass, including same-size tampering, missing/extra members, duplicate/aliased paths, unsafe paths, altered provenance and attempted in-tree/overwrite output. Six documented PowerShell blocks pass syntax parsing. The packages contain no target/draft model tensors or EXE/DLL runtime payloads. The unchanged upstream source tarball retains 19 vocabulary-only GGUF test files, each with zero tensors; these are distinct from the external model weights ([payload inventory](receipts/PAYLOAD_BOUNDARY.json)). Git stores documentation, tools, inventories and small receipts, not these large ZIPs.

The new entry point defines `referenceRoot` before request audits, supplies the stage audit command and uses relocatable package paths. It explicitly reproduces **PR134's target and draft both on B570/Vulkan**, not PR143's later CPU-draft timing study. Historical `collect_results.py` remains source-host-specific; the new CPU verifier handles relocated packages without rewriting old scripts or evidence.

## Local custody only

The original `B570_NATIVE_DELIVERY.zip` remains unchanged at its recorded source-host custody path: 1,367,643,308 bytes, SHA256 `78abc364729fed7ba0f8b92cf3594eed2511df181714e9f53b19ede2a4465973`. [The final rehash receipt](receipts/ORIGINAL_ARCHIVE_UNCHANGED.json) confirms this identity. It is **not** externally hosted by this delivery. It retains the larger historical evidence, failed-attempt raw materials and original binaries. No local filesystem path is presented as an external download.

Original kit manifests, README/RESULT/RESUME files, failed-attempt records and scientific data retain their bytes. New packaging and path guidance live only in this new delivery directory; inherited package members retain their original paths and hashes.

## External dependencies still required

The two exact model weights remain external dependencies. [MODEL_SOURCES.json](MODEL_SOURCES.json) pins official public GGUF repository revisions, direct URLs, byte sizes, LFS SHA256 values and Apache-2.0 licence references. The metadata matches the historical model identity; no model payload was downloaded in this task. The direct GGUFs require no conversion or separate tokenizer.

[DEPENDENCIES.md](DEPENDENCIES.md) provides official Windows/MSVC/Vulkan/driver/runtime acquisition entries and source licence notices. Exact original installer hashes are not established; in particular, no fixed official download of historical Intel driver `32.0.101.9034` was verified. This source-build route does not redistribute vendor runtimes or promise bit-identical historical DLLs. A rebuilt runtime and any changed host/driver need separate native qualification. That future execution is outside this packaging task.

No required minimal source/fixture/request/reference bytes remain local-only. Hardware execution on another machine, exact installer archival and performance measurements are not claimed by this delivery.
