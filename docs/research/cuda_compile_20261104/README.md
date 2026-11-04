# CUDA compile validation, 2026-11-04

**PR180 full CUDA backend and llama compile/link: PASS. PR179 changed CUDA units: PASS. GPU execution: NOT_RUN.**

This supersedes the earlier `CUDA compilation NOT_RUN` label only for the exact snapshots and build configuration below. Earlier CPU receipts remain historical records. No experimental PR was merged and no frozen reference was changed.

## Exact scope

- PR180 runtime/stager: `40934bf0f6dd5ab41e42e0f682f42aef0514e760`.
- PR179 contract/audit: `8005cf01b9b7736d77e4e0c5dc3ecb2da2c29603`.
- Native source kit SHA256: `b1926827029e0bb8e219861901f2ca3538b330a44f9c6093b5267157dbfcd1ac`.
- Each staged source was copied to an independent build workspace. Both complete source inventories were checked after building and remained unchanged. `SOURCE_IDENTITIES.json` records whole-tree digest algorithms and critical file hashes.
- No source fix was needed. No user computer, driver installation, system header patch, compiler compatibility override, remote runtime file edit, model download or paid compute purchase was involved.

PR180's complete Release `llama` target built and linked successfully. All **143 CUDA translation units** were compiled for both sm_89 and sm_120a. The linked CUDA library contains **143 cubins for each architecture**.

PR179's actual `ggml-cuda.cu` and `mmvq.cu` compiled successfully for both targets. Its complete library link was deferred after the long PR180 build. The sequential runner was prevented from starting that second full build by temporarily moving the intact focused-build directory. The resulting immediate directory-lookup error is retained in the raw log and explicitly classified as a scheduling deferral, not a source/compiler failure. The directory was restored and both passed objects are preserved.

## Official toolchain and host

CUDA Toolkit **13.2.2**, NVCC/ptxas/cuobjdump/nvdisasm **13.2.86**, cuBLAS **13.4.1.3**, GCC/G++ **14.2.0**, CMake **4.4.4**, Ninja **1.13.2.git.kitware.jobserver-pipe-1**, Debian 13/glibc 2.41, Linux x86_64. NVIDIA's [CUDA 13.2 installation table](https://docs.nvidia.com/cuda/archive/13.2.2/cuda-installation-guide-linux/index.html) includes this distribution/compiler/libc family; the cloud kernel is not the exact validated kernel shown in the table.

Official NVIDIA redistributable components were downloaded, checked against the [release manifest](https://developer.download.nvidia.com/compute/cuda/redist/redistrib_13.2.2.json) SHA256 values, and extracted without privilege into a workspace directory. `TOOLCHAIN.json` preserves URLs, versions, hashes and archive sizes. Download/use is governed by the [NVIDIA CUDA Toolkit license](https://docs.nvidia.com/cuda/eula/index.html); there was no separate explicit acceptance action.

An earlier CUDA 12.9.1 smoke compile failed because its `sinpi`/`cospi` exception specifications conflicted with glibc 2.41. This happened before HeteroSpec source compilation. The diagnostic is preserved in `logs/smoke.log`; no system/CUDA headers were modified to hide it.

## Configuration and commands

`BUILD_COMMANDS.json` preserves exact configure/build commands, return codes, elapsed time and log hashes. `CUDA_COMMANDS.json` contains exact compiler invocations for the changed units and hashes of the full generated compilation databases. `logs/` preserves the configuration, focused-build, full-build and cubin inventories.

Core configuration: `Release`, `GGML_CUDA=ON`, `GGML_NATIVE=OFF`, `CMAKE_CUDA_ARCHITECTURES=89-real;120a-real`, one build job, Vulkan off and optional NCCL off. The original source CUDA release flags, including `-use_fast_math`, were retained. No inference about a separately built reference's arithmetic follows from these flags.

The [NVIDIA GPU table](https://developer.nvidia.com/cuda/gpus) lists GeForce RTX 5070 Ti at compute capability 12.0, but does not separately spell out its Laptop suffix. The project's CMake selects the architecture-specific `120a` variant for Blackwell FP4 instructions. This is a compilation target, not a query or validation of the user's physical device. sm_89 provides a second, older architecture compile target.

A portable form of the full build is:

```sh
cmake -S "$STAGED_SOURCE" -B "$BUILD" -G Ninja \
  -DCUDAToolkit_ROOT="$CUDA" -DCMAKE_CUDA_COMPILER="$CUDA/bin/nvcc" \
  -DCMAKE_CUDA_HOST_COMPILER=/usr/bin/g++-14 \
  '-DCMAKE_CUDA_ARCHITECTURES=89-real;120a-real' \
  -DCMAKE_BUILD_TYPE=Release -DGGML_CUDA=ON -DGGML_NATIVE=OFF \
  -DGGML_VULKAN=OFF -DGGML_CUDA_NCCL=OFF -DGGML_CCACHE=OFF \
  -DLLAMA_BUILD_COMMON=OFF -DLLAMA_BUILD_TESTS=OFF \
  -DLLAMA_BUILD_TOOLS=OFF -DLLAMA_BUILD_EXAMPLES=OFF -DLLAMA_BUILD_SERVER=OFF
cmake --build "$BUILD" --target llama -j 1
```

Use the pinned stagers and source kit from the corresponding PR, not an unrelated latest llama.cpp checkout. Set `TMPDIR` to a workspace with enough space. NVIDIA's `lib/stubs` is a link-time stub directory, not a usable runtime driver.

## Results and costs

- PR180 focused units: 88.35 s. PR179 focused units: 103.03 s.
- PR180 full-build stage after those two objects: **3,987.93 s (66.47 min)**.
- Largest individual child RSS: **831,904 KiB (812.41 MiB)**. This is not aggregate-container peak memory.
- Archive downloads across both attempted toolchains and nvdisasm: **1,910,420,604 bytes**. Retained local audit/toolchains/build outputs occupied about **6.2 GiB**.
- PR180 full log: no compiler error or warning.
- PR179 has two nonfatal `-Wmissing-declarations` warnings for `hs_cuda_exchange_audit` and `hs_cuda_audit_mmvq`. Add consistent prior declarations before requiring warnings-as-errors; this audit did not change source to suppress them.
- CUDA library SHA256: `c5ac0a484ad7074737d9a55cea0d1bf8129456a848dd2a59fc1311541c7d91bb`.
- llama library SHA256: `72ea9218c32935c100380335a1ef40b6d2370e8376c7f6dae11d6c717c284515`.

`VALIDATION.json` includes artifact sizes/hashes and the final verification boundary. The binaries are Linux x86_64 libraries; their static dependency list still requires a real `libcuda.so.1` driver and CUDA 13 runtime/cuBLAS for loading.

## Not established

**No CUDA kernel or model was run.** PR179 full-library linkage, Windows DLL/compiler behavior, device/driver compatibility, original-reference equality, full-vector logits/KV/continuation correctness, quantization/launch counts, and end-to-end performance remain unverified. Successful compilation does not establish numerical equivalence, safe optimization admission, a speedup, or a paper-acceptance probability. Separate experimental kernel work is outside this receipt.
