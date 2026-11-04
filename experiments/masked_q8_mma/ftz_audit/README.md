# Frozen-PTX FTZ recipe audit and explicitly FTZ-compiled variant

**No GPU execution, no frozen-R equivalence, no production qualification.** This is a separate build/audit of the unchanged PR181 experimental source, not a silent replacement of the frozen reference or an enabled runtime patch.

## Evidence that required the re-audit

The frozen DLL SHA256 is `8df3d5d6363dab0b221f143992e816d1366be4b076b47ce6b1612a148c0bc09c`. Directly extracted ordinary Q8_0 q1/q4 PTX has:

- half-to-float scale conversions without an FTZ modifier;
- two signed DP4A leaves, scale `mul.ftz.f32`, exact integer-to-float conversion, and `fma.rn.ftz.f32` update;
- `add.ftz.f32` for sequential cross-warp merge and the XOR butterfly.

The extracted quantizer additionally uses `div.approx.ftz.f32`. Frozen sm89 native SASS inspection independently shows FMUL.FTZ, FFMA.FTZ, FADD.FTZ and SHFL.BFLY. There is no frozen native sm120 SASS in this DLL; its driver-JIT result is a separate obligation.

PR181's original compilation did not specify FTZ and emitted non-FTZ explicit RN operations. Its unfused mode is also not the observed frozen FMA update. Thus that original build is **not an exact deployed opcode recipe match**. Its tests were already labeled as prequantized synthetic controls, not equality to R.

## Narrow domain: the FTZ difference does not itself refute the old CPU model

For finite binary16 scales, each half is an integer multiple of 2^-24. Their product is exact in binary32 (at most22 significant bits), and is an integer multiple of 2^-48. Each original dot8 is an exact integer of magnitude at most131072. Starting from zero and with no external bias/initial accumulator, every exact multiply/FMA/add input and every RN result stays on the 2^-48 lattice. Rounding to24 significant bits cannot create a fractional lattice unit. Hence every nonzero intermediate is at least2^-48, far above the smallest normal binary32 magnitude2^-126.

Overflow is also absent within this launcher's positive int K domain: half magnitudes are below2^16 and dot8 magnitude is at most2^17, so a term is below2^49. A lane chain has at most2^21 updates (one per1024 K elements). With binary32 unit roundoff2^-24 its accumulated absolute bound is below2^71; the four-warp/lane reduction remains conservatively below2^79. This is far below overflow. Cancellation cannot increase that absolute bound. Missing K blocks are skipped, not added as padded FP updates.

Therefore FTZ has no nonzero subnormal to flush in this **finite-half, integer-dot, zero-initial-accumulator, no-bias projection domain**. This is a conditional arithmetic argument, not a proof of CUDA memory accesses, compiled control/dataflow, quantizer outputs, NaN/Inf handling or full-model execution. Signed zeros collapse in the integer model, so it only proves absence of nonzero subnormal values; the argument relies on FTZ leaving already-zero operands unchanged and does not certify every other zero-sign transformation.

Actual quantizer-produced half scales can be nonfinite even when every F32 input is finite: amax=2^24 gives d approximately132104, which overflows binary16 to +Inf. A finite-F32 check therefore does not establish this domain; the actual half-scale exponent must differ from31, or an equivalent producer bound must be proved. A deployment cannot infer this domain merely from dtype, model name or a descriptor hash. Dynamic assumptions must be enforced or proved. The F32 activation quantizer's approximate division and FTZ behavior are **not modeled or replaced** here.

## Implemented separate variant

`kernels-original.cu` is byte-identical to reviewed PR181 source SHA256 `a8a465ac224ba8aa9613946edbe5cf7291a063f1a4c171f366a143aa82586bb9`. `audit_recipe.py` compiles it with both `-ftz=false` and `-ftz=true`, without enabling the unrelated transformations bundled by `--use_fast_math`. The explicit FTZ variant is also assembled for sm89 and sm120a and disassembled. Only its FMA modes are candidates for the observed update recipe; unfused modes remain negative controls.

The script checks that all emitted scalar add/mul/FMA operations have the requested FTZ flag, and pins the actual frozen q1/q4/quantizer entries. These checks align **operation flags only**; they do not prove entire instruction dependency graphs equivalent. CUDA13.2.2 and its targets remain different from the original build/driver-JIT combination. This is not permission to enable a fast path.

## CPU checks and negative controls

`check_domain.py` enumerates all63488 finite half encodings, checks253952 exact scale pairs, and tests524288 rounded lattice updates across explicit fused/unfused models. It uses arbitrary-precision integers, not approximate NumPy equality.

Two host FTZ-model counterexamples demonstrate why the assumption cannot be dropped:

- `fma(2^-126, 0.5, 0)` is binary32 bits0x00400000 without FTZ and zero under the modeled FTZ semantics. That scale cannot be produced by two finite half factors in this projection.
- An arbitrary initial accumulator2^-149 with a zero product remains bits0x00000001 without FTZ and becomes zero under modeled FTZ. This violates the zero-initial-accumulator premise.

These are **host-modeled, domain-external examples**, not GPU measurements and not discovered errors in the restricted half-scale operator. No FTZ counterexample inside the stated domain was found; the lattice argument explains why FTZ alone cannot provide one. **FMA contraction is different:** a valid in-domain witness below disproves substituting unfused arithmetic.

## Reproduce

    python check_domain.py
    python audit_recipe.py --cuda /path/to/cuda-13.2.2 --frozen-entries /path/to/extracted/ptx_entries --output /fresh/output

The frozen entries must come from the pinned authorized DLL extraction. The script does not download or execute that DLL or modify a GPU driver. It preserves the reference and emits a separate experimental object. Its witness executable attempts a GPU test only in the selected execution environment when a usable device exists; otherwise it exits77. The recorded cloud run had no usable device and launched no kernel. No user computer was accessed. Keep the source, frozen entry hashes, compiler command, resource reports and disassembly hashes with any later device experiment.

## In-domain FMA negative test

K=1056 places two nonzero dot8 leaves in blocks0 and32 of the same logical W4 lane. Block0 has scales1/1 and dot18897, represented by signed bytes W=[127,127,101,0,0,0,0,0], Y=[127,21,1,0,0,0,0,0]. Block32 has half-scale bits0x3be9/0x3f4d (0.98876953125 / 1.8251953125) and dot-13817, represented by W=[-127,-101,0,0,0,0,0,0], Y=[108,1,0,0,0,0,0,0]. All other leaves are zero.

The explicit host float test produces fused bits0xc5bcb40b versus unfused bits0xc5bcb40c. This witness is within the stated finite-half, zero-initial-accumulator domain; it is not an FTZ difference. The frozen DLL explicitly uses FMA, so **fused=true is necessary but not sufficient** for a candidate matching this recipe. The unfused variants must remain negative controls.

`test_fma_witness.cu` realizes those actual Q8_0/Q8_1 bytes, checks the expected W4 bits and compares every candidate layout in both modes. It builds with the explicit FTZ object for sm89/sm120a. In this environment it returns77 because there is no usable CUDA device; only the host witness has executed. `audit_recipe.py` records compilation and the honest GPU run status. Passing this finite fixture on a future device still would not establish full frozen-R equivalence.
