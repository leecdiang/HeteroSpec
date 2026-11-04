# Experimental Q8 masked INT8 MMA, isolated compilation prototype

No production dispatch, runtime hook, automatic qualification, performance claim, or frozen-R equivalence. Inputs are already quantized serialized Q8_0 (34 bytes) and Q8_1 (36 bytes), not F32 activations. The quantizer and stateful model are outside this experiment.

## Experimental controls

- Mode 0: masked `m16n8k16.s32.s8.s8.s32`, 8 output rows by 8 columns, four reduction warps.
- Mode 1: signed DP4A leaves with **the same physical accumulator layout** as mode 0. This isolates integer leaf replacement. It is not the stronger wide-DP4A scheduling design and should not be advertised as its performance representative.
- Mode 2: independently written logical-lane W4 control, two rows/four columns, four reduction warps. This is a modeled reference, not the actual frozen binary.

- Modes 3/4/5: logical-lane four-warp M2N32 / M4N16 / M8N8 register-blocked DP4A controls. Weight words are explicitly loaded once outside the column loop. Mode3 requires N32, mode4 requires N16 or32, mode5 supports all admitted N. These are additional candidates, not a claim of optimal DP4A scheduling.

Both explicit FMA and unfused multiply/add variants compile; no assumption is made about which matches the frozen deployment. Scale multiplication, accumulation, sequential cross-warp merge, and XOR additions use explicit round-to-nearest intrinsics. Masked MMA C is always integer zero. Quant payloads use two 16-bit global loads for Q8_0 and one 32-bit global load for Q8_1, matching their guaranteed alignment. The caller must supply W aligned to2 bytes and Y/output aligned to4 bytes; the launcher rejects violations. Each original lane's K sequence is retained; incomplete K groups skip updates rather than performing padded zero FMAs.

Scope: positive K divisible by 32; positive M divisible by 8; N in {8,16,24,32}; dense contiguous buffers and finite half scales. SM80 is only the ISA/source minimum: the supplied fatbinary contains **sm89 and sm120a only**, not a universal SM80+ executable. Other devices require a suitable separately compiled and qualified target; the minimum-major launcher check alone does not establish binary compatibility. Other output rectangles are rejected. There is intentionally no newly invented tail fallback; later integration must route these through a verified original path. Partial groups of 32 **K blocks** are handled.

The low-level launcher does not validate buffer extents, residency, aliasing, half finiteness, or deployment identity. Architecture and pointer alignment are checked; allocation and semantic properties are explicit caller obligations and the function is **not an admission/safety API**. The provided test owns allocations, uses finite scales, synchronizes every launch, compares complete output bytes, and reports the first mismatch. It includes missing K blocks, signed-zero scales, subnormal-half scales, maximum finite-half scales, and signed integer extrema. It does not qualify NaN payload semantics or an F32 quantization producer.

## Reproduction

    python validate.py --cuda /path/to/cuda-13.2.2 --output /fresh/output

Requires g++-14, NVCC, and CUDA runtime development files. Builds sm89 and sm120a cubins, with PTX for compute89 and ptxas resource logs. This compiler/flags are an experimental build, **not the actual R toolchain pin**. Return code77 from the comparison executable means no GPU test ran. Build success is separate from numerical success. Run compute-sanitizer on a suitable GPU before treating any execution as memory/synchronization evidence.

The final source compiled and linked successfully with CUDA13.2.2 for both sm89 and sm120a. The executable returned77: no usable CUDA driver/device. PTX and SASS dumps are retained under validation-v3, with exact source/artifact hashes in receipt.json. SASS presence alone is not a formal equivalence proof.

RESOURCES.json contains all24 ptxas reports. All variants report zero stack and spill bytes. Masked MMA uses168 registers/thread on sm89 and108 on sm120a, with24KiB shared memory. The logical M2N32 DP control uses219/231 registers (unfused/fused) on sm89 but128 on sm120a; M4N16 uses96/104 and147/151 respectively. These toolchain-dependent differences are a warning against predicting winners from source-level accumulator counts. cuobjdump --dump-resource-usage reports an additional1024 bytes SHARED for sm120a (25600 bytes for the 24KiB-user kernels and4096 bytes for W4); do not budget occupancy from source/user-shared alone. The exact cubin resource dump is retained with its hash in CUBIN_RESOURCES.json. None is a timing, occupancy, or numerical-equivalence result.

## Prior art and research limits

The mapping derives from the separate CPU model in `heterospec-q8-mapping`: exact eight-product leaves, preserved four-warp K stream and ordered floating-point graph. [Taming Numerical Variation, Appendix E](https://arxiv.org/html/2609.11356v1) already describes embedding k8 groups in masked k16 MMA. No algorithmic novelty is claimed.

Before qualification, independently check fragment operand mapping, actual machine instructions and contraction, full prequantized vectors against the frozen kernel, original F32-to-Q8_1 bytes, all admitted device/model descriptors, and full model continuation/state. Benchmark against original graph tiles, backend-loop4, packed, and separately optimized wide-DP4A. The same-layout DP4A control cannot replace the logical-lane wide DP4A competitors; all three geometric controls are now implemented, but their scheduling is not claimed optimal. This source is deliberately not included in PR180 or a production registry.
