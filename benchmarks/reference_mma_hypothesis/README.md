# Frozen-R Q8_0 data reuse and masked integer MMA

Status: **CPU model only. No CUDA compilation, CUDA execution, GPU timing, or full-model qualification.** 2026-11-04.

## Finding

There is a concrete arithmetic-preserving candidate beyond independently launching four-column groups: reuse the operands of several outputs while retaining the frozen output's exact floating-point dependency graph. A minimal higher-risk realization uses INT8 tensor cores only for the original eight-product integer leaves, never for the floating-point reduction. The host prototype below passes its bounded indexing, integer, symbolic-DAG, and numerical tests. It does not establish a faster kernel.

A simpler and necessary competing control is a wider DP4A kernel with the original four reduction warps. At width 32 it can offer substantially more weight reuse than the 8-by-8 masked-MMA prototype. Do not present tensor cores as the inevitable winner.

There is **no algorithmic novelty claim**. The potential increment is a specific Q8_0 implementation under this frozen R and measured evidence against strong controls.

## Frozen evidence and exact scope

The source ZIP was verified as SHA-256 `b1926827029e0bb8e219861901f2ca3538b330a44f9c6093b5267157dbfcd1ac`. All source line references below address `candidate/` inside that ZIP, not today's upstream branch.

| File | SHA-256 | Relevant lines |
|---|---|---|
| ggml/src/ggml-cuda/mmvq.cu | 49a8f1d60c06a3c4b7b95fcc6aa0406338a4afc94fdf7fc2d30d94f3670aa525 | 409-425, 536-554, 570-583, 665-739, 1437-1472 |
| ggml/src/ggml-cuda/vecdotq.cuh | 6607e651085e9ff6e653a6ad23666467d1e4aee23904fd0e3e5f1d90d17dd526 | 243-257, 851-865 |
| ggml/src/ggml-cuda/common.cuh | 2a521c64e4fe8ba743770fa5d76fa2fb455679326be905f84639997c4007f337 | 462-468, 711-748 |
| ggml/src/ggml-cuda/quantize.cu | 12ab0782e5e9cf273dcc584edc7413729b18609dc20b4bc6c7a53efd5656c48f | 54-100, 558-572 |

The target is the arithmetic of the frozen compatible width-four path used by [PR171 packing](https://github.com/leecdiang/HeteroSpec/blob/371223b696bb805030c29f04e39eb17b57fb2ebb/benchmarks/rtx_operator_frontier_v1/execution/packed.patch), and by the independent backend-loop4 control. An eight-column candidate means two independent reference width-four calls with shared operands. It does **not** mean reproducing the native width-eight path, which uses two reduction warps in the generic table and already differs in the retained evidence. [PR171 results and limitations](https://github.com/leecdiang/HeteroSpec/blob/371223b696bb805030c29f04e39eb17b57fb2ebb/benchmarks/rtx_operator_frontier_v1/execution/RESULTS.md).

Initial admission should be narrow: NVIDIA, a validated four-warp reference specialization, Q8_0 dense unbatched weights, dense F32 activation, ordinary non-fused MUL_MAT, no IDs, no split-device execution, supported strides and allocation extents, and 8 through 32 independent columns. Widths below eight, remainder rectangles, unsupported descriptors, and unqualified devices use the unchanged reference backend. Qwen descriptor applicability is not a substitute for testing actual captured operands.

## The immutable arithmetic

Let B=K/32 be the number of Q8 blocks, w in 0..3 the reduction warp, and l in 0..31 the original lane. Write l=4u+v, with u in 0..7 and v in 0..3. The frozen lane visits:

    k = 8*w + u + 32*s, for increasing s and k < B.

For weight row r and activation column j, its integer leaf is:

    I[r,j,k,v] = sum(t=0..7) Wq[r,k,8*v+t] * Yq[j,k,8*v+t].

`VDR_Q8_0_Q8_1_MMVQ=2` means two signed DP4A calls produce this eight-product leaf. The source then computes a product of half scales converted to float and the float-converted integer leaf. Each lane has a separate increasing-s accumulation chain. After those chains, the reference first combines warps in the ordered chain `((a0+a1)+a2)+a3`, then performs lane XOR additions in order **16, 8, 4, 2, 1**. For the two-row width-four kernel, row offset i is stored by original lane i.

For finite half scales, their product is exactly representable in binary32: each has at most 11 significand bits, the product needs at most 22, and its exponent range is safely within binary32. Each eight-product signed-int8 sum is bounded in magnitude by 131072 and also converts to binary32 exactly. These facts permit exact replacement of the integer leaf. They do **not** permit merging four leaves before their scale/float updates, reassociating the warp chain, changing the lane tree, or moving an update across its previous accumulator.

The final multiply and accumulator addition may be fused. The ZIP's CUDA CMake file sets `-use_fast_math` at line 195. NVCC documents that this enables FMA contraction and flush-to-zero, among other settings. The actual loaded binary's instructions, not the spelling of the C++ expression, must decide the contract. The prototype separately verifies an FMA DAG and an unfused multiply-plus-add DAG; it does not assert which is the frozen binary. [NVCC option reference](https://docs.nvidia.com/cuda/cuda-compiler-driver-nvcc/index.html#use-fast-math-use-fast-math).

On the modeled finite-half-scale domain, the product lattice has minimum quantum 2^-48, well above the binary32 subnormal range, so FP32 FTZ is not the expected source of a projection difference. It remains relevant to auditing the untouched F32 activation producer and does not resolve FMA contraction, NaNs, or instruction lowering. The host helper keeps the source's accumulator-first order in the unfused addition, but no host NaN behavior is promoted to a CUDA guarantee.

The original row quantizer must remain intact. It performs the same 32-lane reductions, division, roundf, and conversion to half at `quantize.cu:84-100`. Its row-local indexing is a useful source argument for column independence, but full quantized temporary bytes and all final output bytes still need hardware comparison. This prototype starts from quantized bytes and does not qualify that producer.

## One concrete candidate: 8 weight rows by 8 columns

Use one CTA of four physical warps. Each warp w keeps the same original K partition. In its outer s loop, visit u=0..7, hence k=32*s+8*w+u. For each Q8 block k, issue two independent `mma.sync.aligned.m16n8k16.row.col.s32.s8.s8.s32` operations, each with a zero INT32 accumulator. Half h=0 or 1 selects bytes 16h through 16h+15.

Construct A with 16 rows and 16 columns. For weight row r in 0..7 and subhalf v' in {0,1}:

    A[2*r+v', t] = Wq[r,k,16*h+t] if floor(t/8)==v', otherwise 0.
    B[t,j] = Yq[j,k,16*h+t].

Then D[2r+v',j] is exactly I[r,j,k,2h+v']. There are only eight nonzero products, no INT32 overflow, and no floating-point work in this replacement. Each instruction uses 50% of its nominal product slots. This uses dense INT8 MMA, not structured-sparse MMA; the mask is not a 2:4 sparsity pattern.

For physical lane p, define g=floor(p/4), t=p mod 4. Its four D registers z=0..3 map to:

    r = floor((g + 8*floor(z/2))/2)
    j = 2*t + (z mod 2)
    v = 2*h + (g mod 2).

Store one float accumulator `a[u][h][z]` for each combination. Thus the simultaneous-eight-u schedule holds 8*2*4=64 float accumulators per lane. The mapping is a bijection onto all 8*8*8*4 logical (u,r,j,v) states in each warp. The documented INT8 fragment layout and SM80 minimum are the ISA basis; the specific masked embedding and state mapping above are the prototype's derived construction. [Archived fragment specification](https://docs.nvidia.com/cuda/archive/11.4.1/parallel-thread-execution/index.html#warp-level-matrix-fragment-mma-16816-i8), [current integer-MMA semantics and target requirements](https://docs.nvidia.com/cuda/parallel-thread-execution/index.html#warp-level-matrix-instructions-mma).

After the K loop, combine same-register values from physical warps in exactly the frozen order. Only then translate the lane butterfly:

| Frozen operation | New physical operation |
|---|---|
| original lane XOR16 | register u XOR4 |
| original lane XOR8 | register u XOR2 |
| original lane XOR4 | register u XOR1 |
| original lane XOR2 | register h XOR1 |
| original lane XOR1 | physical lane p XOR4 |

For row r and column j, select u=0, h=0, `p=4*(2*(r mod 4)+(r mod 2))+floor(j/2)`, and `z=2*floor(r/4)+(j mod 2)`. This selects the reference writer's ordered tree, rather than relying on addition's commutativity. The symbolic checker treats addition as an ordered node and verifies this selection.

One can eliminate calculations that do not reach the chosen writer, but must retain that writer's ordered dependency tree. The host model intentionally computes the complete butterfly to make checking simpler.

## Resource and layout costs

- The specified simultaneous-eight-u schedule needs **64 float accumulator registers per thread**, before addresses, four INT32 MMA outputs, A/B fragments, scales, and staging. That is 8192 32-bit accumulator registers per CTA. It is a schedule-specific resource requirement, not a lower bound on every implementation. Serializing u to completion could use fewer registers while changing access locality.
- Cross-warp scratch is `3*32*64*4 = 24576` bytes, or 24 KiB, for a simple one-barrier implementation. No full integer intermediate matrix is written to global memory. Shared-memory physical indexing should make lane p contiguous at fixed u/h/z; naïve `[warp][p][u][h][z]` layout has an unfavorable lane stride.
- Actual register count, spills, shared-memory bank conflicts, active warps, instruction issue pressure, and instruction latency are unknown until compilation and profiling. Loop indices u/h/z should be statically unrolled; dynamic local-array indexing can spill.
- Q8_0 blocks occupy 34 bytes and their quant payload is only 2-byte aligned at some addresses. Use the frozen `get_int_b2` style of safe word assembly. A cast to an aligned int pointer or a naïve ldmatrix load is not justified. Q8_1 blocks occupy 36 bytes; preserve their layout too. Repacking weights would add state, storage, and amortization obligations and is not part of this minimal candidate.
- With full 8x8 output tiles, one Q8 block entails 512 scalar DP4A calls in the original leaf arithmetic, or 16 warp-wide DP4A instruction equivalents. The embedding uses two warp-wide INT8 MMA instructions. This is an instruction-count comparison only: it is **not** an 8x performance prediction. Float conversion, scale, accumulation, operand load, and final-reduction work remain.
- The reference processes eight K blocks across lane subgroups concurrently; the candidate visits those eight u positions as MMA work. The change can expose serial latency even though it gains operand reuse and integer throughput.

## Theoretical reuse, not measured traffic

Let M be output rows and N be activation columns, both divisible by eight for this accounting. Count unique serialized operand bytes needed by each CTA, assuming useful reuse within that CTA. This excludes output, padding, cache-sector effects, alignment, spills, and repeated scale loads.

| Quantity | loop4 / packed with M2,N4 CTAs | masked MMA M8,N8 CTAs |
|---|---|---|
| Weight bytes | (N/4) * M*K*34/32 | (N/8) * M*K*34/32 |
| Quantized activation bytes | (M/2) * N*K*36/32 | (M/8) * N*K*36/32 |

Thus the theoretical CTA-local reuse factors are **2x for W** and **4x for Y**. At N=32, the two terms sum to 26.5*M*K bytes in the baseline and 8.75*M*K bytes in this candidate, a 3.03x ratio of these logical counts. That ratio must not be described as DRAM traffic or speedup. Y can be strongly cache-resident, W can sometimes be cache-resident, and actual transactions need profiling.

For the retained 8B output descriptor M=151936,K=4096,N=32, the serialized weight is 630.59375 MiB. Ideal per-group weight reads are 5044.75 MiB for eight width-four groups and 2522.375 MiB for four width-eight candidate tiles. This saves at most 2522.375 MiB in that logical weight term. The whole quantized Y is only 0.140625 MiB, illustrating why the large logical repeated-Y count does not predict external-memory traffic.

### Why wide DP4A is an important competing control

Retain four reduction warps, two rows per CTA, exact same k sequence, scales, contraction, warp merge, and XOR tree; increase independent column accumulators to Ntile=8,16,32 and explicitly reuse each weight word/scale across them. This is ordinary register blocking under a fixed arithmetic contract.

Ntile=8 uses 16 float accumulators per thread and 6 KiB reduction scratch; Ntile=16 uses 32 and 12 KiB; Ntile=32 uses 64 and 24 KiB. Their ideal weight reuse relative to width four is 2x,4x,8x. A width-32 DP4A candidate has the same accumulator/scratch counts as this M8,N8 MMA schedule but potentially only one weight pass instead of four. The activation-reuse tradeoff goes the other way. The large output projection could favor this simpler kernel. There is no evidence yet to rank these candidates.

## Tails and negative cases

Start with the complete `floor(M/8)*8` by `floor(N/8)*8` rectangle. Process remaining columns on those rows with existing <=4 calls, and remaining rows across all columns with the reference path. This makes width 8/16/24/32 the best candidates and width 9/17/25 proportionately less attractive. Do not duplicate the bottom-right rectangle. The planner test checks exact-once coverage for 1120 M/N/K combinations.

For a final incomplete group of 32 Q8 blocks, all lanes in a warp must agree whether a given k is valid before executing MMA. Missing reference updates are skipped entirely. Do not add an FMA with zero merely because a tile is padded. A signed zero, a NaN, or compiler behavior can distinguish an extra operation. K must remain divisible by 32. The numerical tests include nonmultiples of 32 Q8 blocks and the model dimensions K=4096 and K=12288.

Reject or fall back for the wrong reduction descriptor, quantizer, architecture, dtype, fusion, layout, aliasing, output extent, stride, or device split. Do not silently change R to native width eight, native MMQ, a new batch-invariant global mode, a higher-precision sum, or an exactly rounded sum. Widths below eight have no fast rectangle. Small M, cache-resident weights, insufficient grid parallelism, poor MMA instruction support, spills, or a high fraction of tails can make the candidate slower.

## Executable CPU falsification

Run from this directory:

    python3 check_mapping.py --output-dir /tmp/heterospec-q8-mapping-reproduced

Requirements: Python, NumPy, and g++. The script builds only a host helper with `-ffp-contract=off`; its fused branch explicitly uses `std::fma`. Results and hashes are written to `results.json` in the chosen output directory, leaving the retained receipt untouched. Without the option, output goes to an ignored `reproduced/` subdirectory. The source files are `check_mapping.py` and `fp_update.cpp`.

The completed run checked:

- 1,218,048 exact integer fragment values, including the signed-int8 extremum 131072.
- 5,632 host output bit patterns for separately specified fused/unfused modes, including zero quants, negative zero scale, minimum subnormal half scales, maximum finite half scales, and irregular K tails.
- 640 ordered symbolic output DAGs across B=1,17,33,128,384 blocks and both contraction modes.
- 1120 tail-coverage plans for M in {1,2,7,8,9,16,17}, N=1..32, and five K values.

Negative controls demonstrably fail: two rather than four reduction warps, balanced instead of sequential cross-warp merging, reversed XOR order, changed FMA contraction, and one 32-product scaled integer leaf instead of four eight-product leaves. For one seed at K=4096, the respective unfused mismatch counts are 37/64,16/64,40/64,19/64. These are synthetic host witnesses, not model-output statistics.

A reproducible dot32 counterexample uses half-scale encodings 0x2744 and 0x07ec and four integer subdots [-4252,-22275,31614,-24783]. The frozen leaf tree produces float bits 0xbd8a6292, while scaling their combined dot32 produces 0xbd8a6290. Full signed-byte operands are recorded in `results.json`.

Scale-first grouping is another independent guard. Finite half values a=0.91748046875 and b=1.5615234375 with dot8=12209 give `float(float(a*b)*dot8)` bits 0x4688a6de, but `float(a*float(b*dot8))` gives 0x4688a6df. Merely retaining the fused-versus-split choice is insufficient. The symbolic DAG retains scale-first grouping; the two numerical modes do not enumerate every possible compiler transformation.

The symbolic equality is conditional on the modeled FP nodes. It is not a proof of the compiled CUDA binary, memory accesses, instruction lowering, synchronization, quantizer outputs, NaN payload behavior, or full-model execution. The host numerical mode does not claim to emulate every CUDA fast-math/FTZ detail.

## Existing work and contribution boundary

- [amiller/llama_reproducible at f0dafdb](https://github.com/amiller/llama_reproducible/blob/f0dafdbd9dba40bd0e596f74f3da5f592900fca4/patches/0001-all-deterministic-parity.patch) already contains DET_MAX_BATCH=4 looping over offsets into a quantized activation buffer. That is direct prior art for backend loop4; its other global deterministic changes are not admissible here.
- [Thinking Machines, 2025](https://thinkingmachines.ai/blog/defeating-nondeterminism-in-llm-inference/) explains batch invariance through fixed reduction choices and independent-output parallelism, including the small-batch cost of padded tensor-core tiles. That establishes the general principle, not equivalence to this pre-existing R.
- [Yang et al., 2026 preprint](https://arxiv.org/html/2609.11356v1), sections 5-6 and Appendix E, is direct prior art for preserving a reduction descriptor while changing scheduling/layout and checking compiled arithmetic. Appendix E explicitly describes KPD=8 groups masked within k16 work. Therefore neither masking small groups into MMA nor arithmetic-preserving retiling should be claimed as new here. Its studied FP GEMM reconstruction is not automatically a proof for this Q8_0 kernel.
- [NVIDIA CCCL determinism](https://nvidia.github.io/cccl/unstable/cccl/determinism.html) distinguishes stable arithmetic policies and toolchain scope. Reproducible accumulators or new deterministic trees do not necessarily reproduce an already frozen binary's result, so they are not replacements for this contract.

## Explicit decision and falsification gates

1. **Compilation gate, before hardware timing.** Compile the new kernel with the same actual CUDA toolkit/options/target as R. Save PTX/SASS and resource reports. Check signedness, zero-initialized MMA C, safe Q8 loads, converted scales, exact FMA/rounding/FTZ sequence, ordered per-u K chain, sequential cross-warp merge, and the mapped butterfly. Any mismatch stops the candidate. A compile failure or spilling is a result to retain, not a reason to describe it as qualified.
2. **Numerical gate.** Reuse identical captured W and F32 Y bytes for all eight operator classes in both models. Capture and compare the temporary Q8_1 bytes, every output bit, and all tails with loop4 and packed. Include all widths 1..32 and adversarial integer/scale/zero cases. One difference disqualifies that descriptor. Then run the original full-vector, continuation, and state/transaction checks against immutable R. No approximate tolerance or argmax-only pass.
3. **Strong timing controls.** Compare unchanged packed, backend-loop4 with one quantization and direct output offsets, fixed-four-warp wide DP4A at 8/16/32, and masked MMA. Keep graph cuts and all other runtime components identical. Report quantization, projection, launch, graph construction, capture/reuse, tail, and synchronized total costs. The backend-loop4 and packed arms are not interchangeable; either could win a descriptor.
4. **Predeclared superiority test.** For each predeclared descriptor/width, compare paired unprofiled time ratios candidate/loop4 and candidate/packed separately, with session/root as the independent unit. To call a useful operator win, require both upper confidence limits below 1 minus a preregistered useful threshold, and no equality failure. Choose that threshold and sample plan before GPU results. An interval crossing one is inconclusive. Against wide DP4A, report whether the masked MMA increment remains at all.
5. **Mechanism falsification.** Profile separately from timing. The proposed mechanism predicts fewer per-output weight/activation load requests and integer tensor instructions replacing DP4A leaves. If measured traffic/issue work does not decrease, if spills/local-memory traffic erase the benefit, or if cache effects make the alleged saved bytes irrelevant, reject the claimed mechanism even if an isolated timing is favorable. Kernel speed does not by itself establish service speed.
6. **End-to-end gate.** Retain original natural-input and KV-boundary panels and include all overhead in synchronized service time. A faster projection without a service gain supports an operator result only. If the strongest simpler wide-DP4A arm wins, prefer it and report the masked-MMA negative result.

**Recommendation:** retain the proven-on-CPU mapping as a falsifiable implementation candidate. First compare against the simple fixed-four-warp wide-DP4A control. There is a plausible route to beating backend loop4 without redefining R, but no current GPU evidence that either candidate does so.
