# Q8 packing: current block mapping and a two-group reuse hypothesis

**Status: source analysis and an unimplemented, unmeasured candidate.** No new compilation, model run, native execution or GPU experiment was performed. The five-file guard-audit package remains unchanged.

## Source-backed conclusion

In current packed `[K,4,g]` execution, for each output-row tile, different arithmetic groups occupy different CUDA thread blocks along the grid’s channel dimension. Each group can span many row tiles along `grid.x`. The kernel does **not** explicitly reuse a loaded weight fragment across different groups inside one block. Compared with backend-loop4, its directly visible changes are consolidating multiple four-column MMVQ kernel launches into one grouped launch and allowing groups to occupy the grid together. Both paths already quantize the wide activation once. The source does not establish how much elapsed time comes from launch overhead, additional group concurrency, or hardware caches; it establishes no DRAM-byte reduction. [A1–A3]

| Step | Exact source behavior | Consequence |
|---|---|---|
| Graph mapping | `build_lora_mm` creates `[K,4,g]` and ordinary `ggml_mul_mat`; output is reshaped to logical column order. | Arithmetic width is 4; independent group count is a different dimension. [A1] |
| Host MMVQ descriptor | Without IDs, `ncols_dst=ne1=4`, `nchannels_dst=ne2=g`; the broadcast weight has `nchannels_x=ne02=1`. | The case-4 specialization remains selected if the generic dispatcher reaches MMVQ. [A2] |
| Launch geometry | `calc_launch_params` uses `block_nums=(ceil(M/rows_per_block), nchannels_dst, nsamples)` and `block_dims=(warp_size,nwarps,1)`. | Different groups occupy different `blockIdx.y` values, hence different blocks. [A2] |
| Kernel mapping | `channel_dst=blockIdx.y`; `channel_x=fastdiv(channel_dst,channel_ratio)` with `channel_ratio=g/1`; `channel_y=channel_dst`. | Every group reads the same weight channel 0 but its own activation channel. Same addresses are not cross-block register reuse. [A2] |
| Accumulation | Each block owns `tmp[4][rows_per_cuda_block]`; K-loop dot calls load weight and activation fragments. `tmp_shared` contains partial sums for that block’s reduction. | No loop over independent groups, shared weight tile, or cross-group register broadcast is present. Compiler reuse inside one four-column block is a separate issue. [A2, A4] |

The relevant source identities are the same public source ZIP as the guard audit, SHA-256 `57cbfbfe43ae1c4b4ed5ba3f5261412daa2b5c14b712e76d868da55f4f8a4101`. This conclusion is conditional on admission to the MMVQ path; the packed generic-dispatch scope gap remains as documented in G03.

## First candidate: exactly two independent four-column groups in one block

Start only with a captured, admitted Q8_0/F32 projection having **q=8, g=2, no tail, no IDs and no fused arithmetic**. Give the kernel a separate `groups_per_block=2` parameter while retaining `c_ncols_dst=4`. Each thread owns two independent sets of four-column accumulators and reuses its loaded weight fragment for both groups. This is a hypothesis about reusing data across independent output computations; it does not combine their reductions.

For each output, preserve the existing thread-to-K assignment, `kbx` start and step, `kqs`, row assignment, dot-product integer operation order, scale arithmetic, per-thread FP accumulation order, inter-warp sum order and final warp reduction. One conceptual iteration is:

```text
for each original K iteration assigned to this thread:
    obtain the original weight fragment for each original output row
    update accumulator[group 0][column 0..3][row] with the original dot arithmetic
    update accumulator[group 1][column 0..3][row] with the same weight fragment
reduce each group's accumulators separately using the original four-column recipe
```

The existing Q8 helper explicitly loads weight integer fragments and scale, then computes a `dp4a` chain and the scaled contribution. A prototype would have to expose reuse of those exact fragments while preserving each output’s operations. Merely rewriting the helper or keeping apparently identical C++ expressions is insufficient: compiler FMA contraction, instruction selection, scheduling and register spilling can alter the numerical behavior or cost. Bitwise own-path and cross-path replay is a prerequisite to any performance claim. [A4]

**Do not implement this by setting `ncols_dst=8`.** In the source’s generic NVIDIA parameter table, the four-column path uses 4 warps while the eight-column path uses 2. That changes the K partition and reduction organization. The proposed new dimension is the number of independent four-column groups sharing weight fragments; it must not change the native arithmetic width or its reduction parameters. [A2]

### Resource and scheduling risks

For the generic NVIDIA four-column configuration, the source gives 4 warps, 32 lanes per warp and 2 output rows per block. The explicit accumulator payload is therefore `4 × 2 = 8` floats per thread for one group, versus `2 × 4 × 2 = 16` for the candidate. This counts accumulator elements, **not compiled registers**. Weight fragments, activations, address state and compiler temporaries add to the true register footprint. [A2]

If each group retains a separate copy of the current inter-warp reduction buffer, its storage grows from `(4−1) × 4 × 2 × 32 × 4 = 3072` bytes to 6144 bytes per block. These are source-level buffer sizes, not measured occupancy. More live registers and shared memory can reduce resident blocks or trigger spills. With q=8, combining two groups also halves the number of blocks in the group dimension, which can reduce scheduling parallelism when the row grid is small. A slower kernel is a plausible outcome even if explicit weight loads decrease.

The narrow initial implementation should prefer a thread’s own register-resident weight fragment reused across its two accumulator sets. A shared-memory broadcast across different warp groups would add a separate communication/barrier design and is outside this first candidate. No DRAM or L2 saving follows automatically: current separate blocks may already receive repeated weights through cache. Reduced source loads must not be reported as measured memory-traffic reduction.

## Minimal three-arm operator experiment — design only

| Arm | Bound computation | What it isolates |
|---|---|---|
| A: backend-loop4 | One unchanged activation quantization; two old four-column MMVQ launches. | Strong control retaining the original arithmetic and backend loop. |
| B: current packed | One unchanged activation quantization; one kernel launch, grid channel count 2, one four-column group per block. | Existing launch consolidation and group-grid mapping. |
| C: proposed shared-weight pair | One unchanged activation quantization; one kernel launch, two independent four-column groups in each block. | Additional intra-block weight-fragment reuse and its resource cost. |

Use the same captured **real** weight and activation bytes, exact shape/stride/padding/placement descriptors, output layout, device, stream and frozen compilation flags. Start with a single admitted q=8 descriptor from a real projection; it proves only that case. Refuse any descriptor not covered by its preflight rather than silently substituting another kernel.

First reproduce each original four-column output and compare B and C bitwise to A. Check activation quantization bytes independently so differences cannot be hidden upstream. Inspect that C still uses the four-column lane/K/reduction organization. Only after these pass should the same three arms be timed in blocked paired order. A kernel-only diagnostic may reuse the same already-quantized activation for all arms; a separate complete-operator timing must include the identical quantizer and synchronization boundaries for all three. Do not mix those denominators.

Record, at minimum, kernel latency, compiler-reported registers per thread, spill loads/stores or spill bytes, static/dynamic shared memory, and achieved occupancy or active-warps/resident-block evidence when supported. If profiling access exists, also collect DRAM bytes and L2 traffic/hit metrics; otherwise label memory-traffic attribution unknown. A source-level operation count or same-address analysis cannot replace those counters. Report confidence intervals and control drift; a small positive point estimate alone does not establish a useful improvement.

Stop on a numerical mismatch or a loss against current packed that cannot be explained by a specific measurable resource cost. A successful operator result only motivates a fresh native full-request qualification against the original reference, including requested full vectors, active KV, accepted frontier and pending-token behavior. Then measure complete resident-service cost against the strong baseline and current packed path. q=8 gains do not apply automatically to current k3 verification, which never enters multi-group packing; the opportunity must be measured in actual wider prompt work or separately qualified k7 verification. A general 5% claim requires that final system evidence.

## Exact source references

| ID | Source member and symbols | SHA-256 |
|---|---|---|
| A1 | `native/cores/packed/src/llama-graph.cpp`, `llm_graph_context::build_lora_mm`, lines 1566–1605 | `3b1a6df5a5a7fc902642f42d9373a4d1ae6cf2013a50003698f30bbd3f0f522e` |
| A2 | `native/cores/packed/ggml/src/ggml-cuda/mmvq.cu`: parameter functions (410–554), `mul_mat_vec_q` (558–742), `calc_launch_params` (936–945), case-4 dispatch (1161–1168), host channel/stride setup (1442–1498) | `d9c69fafab943383b29e525417f5e2157a445c9b1afca97b7d9de23d20a2564a` |
| A3 | Same `mmvq.cu`, marked backend-loop4 quantization and loop, lines 1427–1491 | `d9c69fafab943383b29e525417f5e2157a445c9b1afca97b7d9de23d20a2564a` |
| A4 | `native/cores/packed/ggml/src/ggml-cuda/vecdotq.cuh`, `vec_dot_q8_0_q8_1_impl` (246–257), `vec_dot_q8_0_q8_1` (851–866) | `6607e651085e9ff6e653a6ad23666467d1e4aee23904fd0e3e5f1d90d17dd526` |

All cited files were read from or checked against the pinned release archive and its manifest. This addendum is independent of the frozen guard-audit files and adds no implemented optimization or experimental result.
