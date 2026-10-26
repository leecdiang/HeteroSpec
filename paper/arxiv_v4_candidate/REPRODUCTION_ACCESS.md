# Native reproduction access

Updated 2026-10-27. The minimum source, real-fixture and full-request reference materials are delivered for both platforms. Access requires permission to the private HeteroSpec repository and GitHub authentication. Source-host fresh-download CPU checks validate preserved evidence; the editorial audit checked pinned records, live asset metadata and integrity tests without downloading large payloads or running native inference.

## Reported-data reconstruction

The manuscript package contains source-pinned compact inputs and CPU scripts for reconstructing estimates, tables and figures. This route needs no model weights or GPU. `anc/native_delivery/SOURCE_INDEX.json` pins the compact delivery records to exact Git blobs.

## RTX

Result baseline: PR147 `3429e2c49626c30e4a406a517a3e8a030aea9c7f`. Delivery records: PR149 `9149b6f5f5a4dcde1b6124c654dc0ba1241ca509`. Fixed package material: `3999a95dd8f7fd29ae68b04ca46b8e95107c246c`.

- [Delivery guide and commands](https://github.com/leecdiang/HeteroSpec/blob/9149b6f5f5a4dcde1b6124c654dc0ba1241ca509/scripts/native_reproduction/rtx_delivery/README.md)
- [Access, ordered parts and archive identity](https://github.com/leecdiang/HeteroSpec/blob/9149b6f5f5a4dcde1b6124c654dc0ba1241ca509/benchmarks/rtx_native_delivery_20261026/ACCESS.json)
- [Fixed material directory](https://github.com/leecdiang/HeteroSpec/tree/3999a95dd8f7fd29ae68b04ca46b8e95107c246c/benchmarks/rtx_native_delivery_20261026)
- [Exact model and numerical-DLL acquisition](https://github.com/leecdiang/HeteroSpec/blob/9149b6f5f5a4dcde1b6124c654dc0ba1241ca509/benchmarks/rtx_native_delivery_20261026/DEPENDENCIES.json)
- [Fresh-download CPU verification](https://github.com/leecdiang/HeteroSpec/blob/9149b6f5f5a4dcde1b6124c654dc0ba1241ca509/benchmarks/rtx_native_delivery_20261026/REMOTE_VERIFICATION.json)

The 12-part archive is 473,187,187 bytes, SHA256 `1b3aa913be73db8be50d7cc28f6e733ad5b4b1a52862a3838920933ea70978a0`. It contains 785 indexed payload files plus its member manifest: original source/executable capsule, real q3 stage fixture, complete R/PQ/QB records for GSM8K/test/443, six historical HTTP responses, and 936 formal request records.

The recorded new HTTPS checkout verifies the parts, archive, indexed members, 3,542 restored source members, 704 preserved full-vocabulary vectors and all 288 PQ/QB vector pairs. New wrappers take explicit model, DLL, toolchain and output paths. Preparation obtained and hash-verified 21 exact numerical DLLs from the two official llama.cpp b10839 CUDA 12.4 archives.

Native reconstruction rebuilds core/frontend objects while retaining pinned CUDA/BLAS/ggml numerical DLLs. Other inputs' heavy logits, full build trees and interrupted-attempt evidence remain in original source-host custody.

## B570

Native result baseline: PR148 `41cb7504ece1f78109fde6895b10ffc56dff8ef1`. Delivery records: PR150 `9f03bead68462326497b03edb0d2d80f8f2fd4c3`.

- [Delivery guide, source preparation and audit commands](https://github.com/leecdiang/HeteroSpec/blob/9f03bead68462326497b03edb0d2d80f8f2fd4c3/benchmarks/b570_native_delivery_v1/README.md)
- [Published private-repository release](https://github.com/leecdiang/HeteroSpec/releases/tag/b570-native-source-reference-v1-20261026)
- [Asset identities and authenticated download routes](https://github.com/leecdiang/HeteroSpec/blob/9f03bead68462326497b03edb0d2d80f8f2fd4c3/benchmarks/b570_native_delivery_v1/ACCESS.json)
- [Delivery results and verification receipts](https://github.com/leecdiang/HeteroSpec/blob/9f03bead68462326497b03edb0d2d80f8f2fd4c3/benchmarks/b570_native_delivery_v1/RESULT.md)
- [Exact model sources](https://github.com/leecdiang/HeteroSpec/blob/9f03bead68462326497b03edb0d2d80f8f2fd4c3/benchmarks/b570_native_delivery_v1/MODEL_SOURCES.json) and [runtime/toolchain dependencies](https://github.com/leecdiang/HeteroSpec/blob/9f03bead68462326497b03edb0d2d80f8f2fd4c3/benchmarks/b570_native_delivery_v1/DEPENDENCIES.md)

| Asset | Bytes | SHA256 |
|---|---:|---|
| B570_MINIMAL_SOURCE_REQUEST_V1.zip | 232,568,531 | `774c1ce5351fa7b1b9b60d7eb801361d3268d0f6398c6d386b22e66dd65c59ea` |
| B570_FOUR_INPUT_REFERENCES_V1.zip | 497,867,884 | `a0c0ab0e4f962e8be84cc8cca9b4adc518707a01f87561f40f57e657346bf95e` |

Release ID `424397460`; asset IDs `678515311` (minimal) and `678524302` (four references). Live GitHub asset sizes and digests matched the access manifest in the editorial audit. The minimal ZIP has 550 indexed files plus its manifest; the four-input ZIP has 1,161 indexed files plus its manifest.

Both assets were downloaded and member-hashed in new source-host directories. The minimal package compares 175 preserved capture/reference vectors and 16 stage results. The four-input check authenticates 914 stored vectors and their internal R/PQ/QB relationships by supplying the references themselves to the auditor; it is distinct from a fresh model-output comparison. The new guide defines referenceRoot before request auditing and includes the stage command. Its source route rebuilds the numerical libraries/shaders and reproduces PR134's dual-model Vulkan contract, separate from PR143's later CPU-draft policy.

The original 1,367,643,308-byte archive remains locally held, SHA256 `78abc364729fed7ba0f8b92cf3594eed2511df181714e9f53b19ede2a4465973`. Delivered subsets contain the required minimum source, stage, request and all four reference inputs. The historical Intel driver is `32.0.101.9034`; an exact installer/hash is not supplied. A rebuilt runtime or changed driver needs native qualification on the receiving host.

## External dependencies and execution scope

Both kits pin public GGUF publisher revisions, direct URLs, sizes and SHA256. Target Qwen3-8B-Q8_0: `408b955510e196121c1c375201744783b5c9a43c7956d73fc78df54c66e883d6`; draft Qwen3-0.6B-Q8_0: `9465e63a22add5354d9bb4b99e90117043c7124007664907259bd16d043bb031`. These exact files require no conversion or separate tokenizer. Model weights remain external; the delivery checks matched existing local model bytes and publisher metadata rather than re-downloading model payloads.

Minimum controlled-access material delivery is complete. Source-host fresh-directory CPU checks establish transport and preserved-evidence integrity. They do not establish independently provisioned hardware execution or anonymous public distribution. No new timing campaign is required for the current manuscript claims.
