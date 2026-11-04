# Frozen PR174 CUDA binary inspection

Inspected on 2026-11-04 in the cloud. No user device, GPU, model, kernel execution, or source recompilation was used. No production code or frozen reference was modified.

## Result

The actual frozen runtime is available and has been acquired and verified. Its ordinary Q8_0 MMVQ q=1 and q=4 paths explicitly use scale-first **fused** FP32 accumulation with **flush-to-zero (FTZ)**. This is direct embedded-code evidence, not a conclusion inferred from C++ or a new compiler build.

The DLL contains no native sm_120 cubin. Its native cubins target only sm_86 and sm_89, with forward-compatible PTX targets up through sm_90. Therefore the archived sm_89 SASS is not the RTX5070 Ti deployment's final SASS. Given the recorded sm_120 device, a successful original execution requires a compatible PTX/JIT path; that deployed driver's selected module and generated code have not been observed here. NVIDIA documents cubin compatibility within a compute-capability major version and PTX forward compatibility: <https://docs.nvidia.com/cuda/blackwell-compatibility-guide/index.html>.

## Identity and acquisition

- Release: <https://github.com/leecdiang/HeteroSpec/releases/tag/rtx-prefix-reuse-v1-20261104>
- Repository manifest: <https://github.com/leecdiang/HeteroSpec/blob/aa7ff4e64752be3de0d7974febbce453ae3a96c0/benchmarks/rtx_prefix_reuse_v1/execution/evidence/RUNTIME_KIT.json>
- Frozen runtime ZIP: 717,461,138 bytes, SHA256 `24d647dbf7bedb1003e766363d24cad04d55094290f1b06d6e17a342cb328d12`.
- `modules/ggml-cuda.dll`: 547,318,272 bytes, SHA256 `8df3d5d6363dab0b221f143992e816d1366be4b076b47ce6b1612a148c0bc09c`.
- `.nv_fatb`: exactly 532,213,320 bytes at PE file offset `0xe66400`, SHA256 `c5f1d0057fe2859da82daa8a806e7592d7c5fe74eccf562b651c349dba43c4a6`.
- Both archived oracle and candidate binding manifests pin the same CUDA DLL hash.
- The giant 7,763,135,840-byte raw-evidence archive was not downloaded.

The ZIP and selected members were independently hash-checked before inspection. Linux cuobjdump did not recognize CUDA code directly in the Windows PE container; the reproducer therefore reads the PE section table and extracts the original `.nv_fatb` bytes without modifying the DLL. A clean streaming extraction and selected-module disassembly were then rerun successfully. No downloaded executable or library was loaded.

## Code inventory

- 286 native ELF objects: 143 sm_86 and 143 sm_89.
- 858 PTX objects: 143 each for sm_50, sm_61, sm_70, sm_75, sm_80, and sm_90.
- Embedded PTX ISA version 8.4, Windows host, 64-bit compile size.
- Ordinary q=1 and q=4 Q8_0 MMVQ are in PTX object 228 (sm_90), native object 76 (sm_89).
- Activation quantization is in PTX object 288 (sm_90).
- Inspection tool: cuobjdump 13.2, V13.2.86, build `cuda_13.2.r13.2/compiler.37953736_0`. Using a newer disassembler does not change the archived instructions.

## Direct Q8 MMVQ evidence

See `ptx/q8_mmvq_q1.sm90.ptx`, `ptx/q8_mmvq_q4.sm90.ptx`, and `sass/q8_mmvq_q1_q4.original_sm89.sass`.

The entry names are:

```
_Z13mul_mat_vec_qIL9ggml_type8ELi1ELb0ELb0ELb0EEvPKvS2_PKi31ggml_cuda_mm_fusion_args_devicePfj5uint3jjjS7_jjjS7_jjjj
_Z13mul_mat_vec_qIL9ggml_type8ELi4ELb0ELb0ELb0EEvPKvS2_PKi31ggml_cuda_mm_fusion_args_devicePfj5uint3jjjS7_jjjS7_jjjj
```

For q=1, normalized snippet lines 126 and 137 explicitly use weight-block stride 34 bytes and activation-block stride 36 bytes. Lines 152-164 load the weight half and activation's low half, then `cvt.f32.f16` without an FTZ modifier. Lines 169-176 contain:

```
dp4a.s32.s32 %r76, %r77, %r78, %r79;
dp4a.s32.s32 %r80, %r81, %r82, %r76;
mul.ftz.f32 %f15, %f13, %f14;
cvt.rn.f32.s32 %f16, %r80;
fma.rn.ftz.f32 %f55, %f15, %f16, %f55;
```

Thus the two four-byte signed integer dots are combined exactly, the two scales are multiplied first, and the integer-to-float result participates in explicit RN fused accumulation. q=1 cross-warp merge at lines 394-398 uses `add.ftz.f32`; the XOR reduction at lines 403-424 uses butterfly offsets 16, 8, 4, 2, 1 and `add.ftz.f32`. q=4 has the corresponding scale-first fused paths and FTZ merge/reduction. Static instruction-site counts are not execution counts: q=1 has 5 FMA sites because of a remainder loop plus an unrolled group of four; q=4 has 8 FMA sites. The ordinary q=1/q=4 PTX variants inspected at all six embedded targets use FTZ arithmetic.

The archived sm_89 SASS independently confirms `FMUL.FTZ`, `FFMA.FTZ`, `FADD.FTZ`, and `SHFL.BFLY`. It is corroborating archived code, not deployed sm_120 code.

## Direct activation-quantizer evidence

See `ptx/quantize_q8_1.sm90.ptx`, entry `_Z13quantize_q8_1PKfPvxxxxxj5uint3`.

- Absolute-value and warp-maximum path use `abs.ftz.f32` and `max.ftz.f32`.
- Warp sum uses the same 16/8/4/2/1 butterfly order and `add.ftz.f32`.
- The float scale is `div.approx.ftz.f32 amax, 127.0f`.
- The quantized ratio is a second `div.approx.ftz.f32 xi, scale`.
- Nonzero case forms sign(x/scale) times 0.5 from the sign bit, uses `add.rz.ftz.f32`, then `cvt.rzi.f32.f32` and `cvt.rzi.ftz.s32.f32`, before storing a byte. Zero amax has an explicit branch.
- The saved scale and sum use `cvt.rn.f16.f32` and a paired half store.

An arbitrary FP32 host quantizer or correctly-rounded division is not established as bit-equivalent by these instructions. NVIDIA defines the `.ftz` and approximate-divide semantics in the PTX ISA: <https://docs.nvidia.com/cuda/parallel-thread-execution/>.

## Toolchain provenance and limits

The pinned bundled `cudart64_12.dll` identifies itself as **NVIDIA CUDA Runtime 12.4.127**, original filename `CUDART64_124_127.DLL`; SHA256 `d28e42265da7462162a54da6b7a99ea4fa2caf8139d862bb500db875d0b32dfc`. This is runtime-library identity, not proof of the exact nvcc compiler build. The CUDA DLL's PE linker version is 14.44. Its embedded source paths are consistent with an upstream llama.cpp CI build, but paths alone are not a provenance proof.

The release's Zig 0.16.0 record describes Windows host worker/core commands. The archived historical CMake configuration says `GGML_CUDA=OFF` and dynamically loads backends. These commands do not establish the CUDA DLL's compiler revision or complete CUDA flags. PTX 8.4 and the runtime identity are compatible with a CUDA12.4-era build, but exact nvcc version/flags are not independently established.

## Consequences for PR181

1. An ordinary source expression or CUDA13.2 recompilation must not be labeled the frozen reference binary. The new reference evidence is the pinned DLL and its embedded PTX/SASS.
2. The frozen scale-first FMA choice is now evidenced directly. Separate multiply-plus-add is not its instruction contract.
3. The frozen arithmetic includes FTZ. A non-FTZ candidate requires either matching lowering or a proof that FTZ cannot affect the stated supported domain. Opcode difference alone is not a demonstrated output mismatch. For actual finite half scales (not merely finite pre-quantization FP32 inputs), each scale is an integer multiple of 2^-24. Assume RN rounding, +0 initial accumulators, no bias or external initial accumulator, and no overflow. Their exact product is an integer multiple of 2^-48 and fits FP32 (at most 22 significand bits); multiplying by an integer dot and RN rounding remains on that lattice. Starting from +0, RN FMA and addition preserve the lattice. A finite nonzero intermediate is therefore at least 2^-48 in magnitude, far above the FP32 subnormal range. Under these narrow prequantized-domain assumptions, FTZ is dormant in these projection operations. This excludes only FTZ-caused differences, not differences between fused and unfused arithmetic. This argument does not establish arbitrary-FP32 quantizer equivalence, cover nonfinite half scales/NaN payloads, or prove that candidate lane/address/reduction mappings match the frozen kernel.
4. Preserve the exact per-lane accumulation, cross-warp merge, XOR tree, and activation quantizer if claiming reference-preserving execution. q=4 merge instructions can reverse the operand order relative to a q=1-style abstract left fold; finite addition is commutative, but NaN-payload claims would need the actual instruction order rather than that abstraction.
5. Driver identity, JIT choices/final sm_120 SASS, actual runtime routing, end-to-end bit comparisons, and performance remain unverified. No native replication, speedup, successful launch, or correctness claim is made by this inspection.

## Reproduce

Download only `frozen-runtime.zip` from the linked release to an authorized cloud workspace, then run:

```
python reproduce.py /path/to/frozen-runtime.zip /path/to/cuobjdump --output reproduced
python verify.py --reproduced reproduced
```

Use Python 3.11+ (standard library) and the recorded cuobjdump version for byte-identical disassembly text. The script checks the ZIP, DLL and fatbin hashes, extracts selected original PTX/cubins, emits the q=1/q=4 archived sm_89 SASS, and records commands/hashes. It has been run successfully here. The snippets are LF-normalized inspection excerpts with original source line ranges in `VERIFICATION.json`; they are not standalone PTX modules because shared declarations may occur elsewhere. Full original selected PTX modules and cubins are regenerated under `reproduced/`, which is ignored by Git. `verify.py` checks every committed text file against `MANIFEST.json` and optionally compares fresh extraction with the committed PTX/SASS. No assertion-based checks are used, so Python `-O` does not disable validation.

Only text evidence is committed here. The runtime ZIP, DLLs, fatbin, full PTX modules, cubins, model weights, credentials and temporary download addresses are excluded. The authorized release is the sole acquisition entry point; the reproducer makes no network requests. `IDENTITY.json` records source identities and architecture counts; `VERIFICATION.json` records portable command receipts and the distinction between inspection-tool and frozen-runtime versions. This audit does not modify the frozen reference or register a new deployed implementation.
