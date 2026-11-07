# Native reproduction access

Updated 2026-10-26. Repository links below require access to the private HeteroSpec repository. Archive checksums and sizes are taken from pinned manifests; this editorial revision did not download or rehash the native archives.


### Reconstructing reported results

The manuscript package includes the source-pinned compact inputs and scripts needed to reconstruct the reported estimates, tables and figures on a CPU. This route does not require model weights or GPU execution. It is separate from rebuilding the native runtime or comparing full request vectors.

### Native implementation and replay materials

| Platform | Versioned material and scope | External material still needed |
|---|---|---|
| RTX | Pinned source/build/replay scripts; historical source capsules; a real Qwen3 layer0/q3 attention fixture; compact native records and complete formal bridge timing records. The recorded clean build rebuilds core/frontend objects while retaining the pinned CUDA/BLAS/ggml numerical DLLs. | The exact numerical DLLs and externally supplied model bytes. Full qualification logits and interrupted-attempt evidence remain in the source-host raw archive. The recovery wrapper currently uses original-host paths and needs a documented relocation mapping or parameterized inputs. |
| B570 | Pinned upstream-source inventory, complete overlays/patches, build/audit scripts, a real HumanEval/115 layer0/q2/key512 fixture and receipts. The recorded build rebuilds all five numerical libraries and 147 shader translation units. | Exact model bytes; the historical request-reference vectors needed for full request comparison are in the source-host delivery archive. The full archive also contains newly recorded evidence and runtime binaries. |

RTX entry points at result commit `3429e2c49626c30e4a406a517a3e8a030aea9c7f`:

- [Build and replay guide](https://github.com/leecdiang/HeteroSpec/blob/3429e2c49626c30e4a406a517a3e8a030aea9c7f/scripts/native_reproduction/rtx_bridge/README.md)
- [Access and checksum manifest](https://github.com/leecdiang/HeteroSpec/blob/3429e2c49626c30e4a406a517a3e8a030aea9c7f/benchmarks/rtx_native_bridge_20261026/results/RAW_ACCESS.json)
- [Real native fixtures](https://github.com/leecdiang/HeteroSpec/blob/3429e2c49626c30e4a406a517a3e8a030aea9c7f/benchmarks/rtx_native_bridge_20261026/results/NATIVE_FIXTURES.zip): 1,345,558 bytes, SHA256 `3512e4aed7330dfcbdff37dbb858d576e6a8166bfedd55879926c014317ae0ae`.
- [Compact native records](https://github.com/leecdiang/HeteroSpec/blob/3429e2c49626c30e4a406a517a3e8a030aea9c7f/benchmarks/rtx_native_bridge_20261026/results/NATIVE_RECORDS.zip): 5,133,204 bytes, SHA256 `a516e8e4d4274c17ba11476fcb8296f3ebb0b281c7dbdb325dfd339c1a6d5c3c`.
- Historical source-capsule fragments and their manifests are [versioned at commit 3235d44c](https://github.com/leecdiang/HeteroSpec/tree/3235d44c26edd92db33e574094c26af8e29d2452/benchmarks/rtx_querylayout_mechanism_v1). Assemble the ordered fragments and verify the manifests before extraction. Expected complete ZIP hashes: original `62086688fc095be2654ae25aad2c7780c94db8617db5a6a9f71504f49897bf7e`; metadata4 `36be0d738ad5d29579b75825f68337003eb127405cc5418abc566cb07718a4d8`.

B570 entry points at result commit `41cb7504ece1f78109fde6895b10ffc56dff8ef1`:

- [Source/build/native guide and kit](https://github.com/leecdiang/HeteroSpec/tree/41cb7504ece1f78109fde6895b10ffc56dff8ef1/benchmarks/b570_native_reproduction_v1)
- [Real stage fixture](https://github.com/leecdiang/HeteroSpec/blob/41cb7504ece1f78109fde6895b10ffc56dff8ef1/benchmarks/b570_native_reproduction_v1/REAL_STAGE_FIXTURE.zip)
- [Local delivery manifest](https://github.com/leecdiang/HeteroSpec/blob/41cb7504ece1f78109fde6895b10ffc56dff8ef1/benchmarks/b570_native_reproduction_v1/LOCAL_DELIVERY.json) and [archive checksum receipt](https://github.com/leecdiang/HeteroSpec/blob/41cb7504ece1f78109fde6895b10ffc56dff8ef1/benchmarks/b570_native_reproduction_v1/ARCHIVE_RECEIPT.json).
- The model-free `B570_NATIVE_DELIVERY.zip` is 1,367,643,308 bytes, SHA256 `78abc364729fed7ba0f8b92cf3594eed2511df181714e9f53b19ede2a4465973`. The manifest records remote publication as not performed. Its `references/qual-0` through `qual-3` contain the historical full-request comparison bytes. A stable download entry for this archive or a complete minimal reference bundle is still required for external full-request reproduction.

Both platforms use externally supplied Qwen3 model files: target Qwen3-8B-Q8_0, SHA256 `408b955510e196121c1c375201744783b5c9a43c7956d73fc78df54c66e883d6`; draft Qwen3-0.6B-Q8_0, SHA256 `9465e63a22add5354d9bb4b99e90117043c7124007664907259bd16d043bb031`. A filename or model family alone does not establish this byte identity. The native kits retain full model identity manifests.

The recorded native checks are source-host rebuilds and fresh-directory replay. They do not constitute an independently provisioned second-machine reproduction. External access completion is a packaging task: expose the required existing bytes, dependency acquisition instructions and relocatable commands, then verify a fresh download. No additional timing campaign is needed to support the present manuscript results.

