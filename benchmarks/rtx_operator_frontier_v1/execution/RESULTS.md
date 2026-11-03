# RTX operator frontier

Packing independent four-column reductions cut geometric mean complete service time from 3.3562 s to 3.2219 s on the four frozen natural inputs. Equally optimized WB took 3.1985 s. The local-cut advantage appeared in deliberately boundary-active appends, while WB was slightly faster in the natural panel.

Sixteen captured model/operator pairs passed own-path replay. On identical weight and F32 activation bytes, all eight Q8 operator classes in both models matched scalar outputs at native widths 2 and 4 and diverged at 8, 16 and 32. A single broadcast matmul over independent four-column groups matched the scalar output at 8, 16 and 32 for every captured descriptor. These are finite observations on this CUDA cohort.

## Operator evidence

The first graph-ordered relevant operation was the layer-zero Q projection. For each model the live scalar input columns concatenated byte-for-byte to the live native-wide input, the weights were identical, and scalar operator replay reproduced the live scalar outputs. Direct width-eight Q reproduced its corresponding replay. All eight rows in the retained 0.6B scoped wide-projection witness differ from its scalar oracle. In the new C1536 observer run only two of eight final rows equaled the earlier C1024 unscoped native witness. Operator conclusions use own-path replay within each run.

CUPTI recorded the same row-Q8_1 activation quantizer at native widths four and eight. The MMVQ launch block changed from 32 × 4 threads to 32 × 2. The CUDA source uses four reduction warps through width four and two at width eight. At 16 and 32 the trace switched to MMQ quantization, matrix multiplication and stream-K fixup. These observations localize width-eight divergence without assuming a change from F32 to Q8 activation arithmetic. Internal temporary quantized bytes were not separately captured.

The candidate represents complete groups as [K,4,g], broadcasts the original Q8 weight, and reshapes the result as a view. A remainder uses the existing bounded tile and one join. The activation must be contiguous, with a dense, unbatched weight and at least eight columns. The runtime study admits fully GPU-offloaded Qwen3-8B on this RTX backend. CPU and hybrid execution of this candidate are unqualified. Both local and whole-graph cuts use the same linked operator core.

Isolated Qwen8B width-32 replay below uses the same observed CUDA0 operands. Times are median synchronized graph execution over the three post-warm repeats in the unprofiled replay. GPU kernel sums come from a separate CUPTI pass. The tile concatenation bytes count logical output writes.

| Class | Descriptor K × output | Tile / pack kernels | Tile / pack execution µs | Tile / pack GPU kernel µs | Tile concat MiB |
|---|---:|---:|---:|---:|---:|
| blk.0.attn_q.weight | 4096 × 4096 | 23 / 2 | 172.4 / 150.2 | 166.3 / 139.2 | 2.19 |
| blk.0.attn_v.weight | 4096 × 1024 | 23 / 2 | 67.1 / 67.5 | 92.3 / 58.9 | 0.55 |
| blk.0.attn_k.weight | 4096 × 1024 | 23 / 2 | 68.4 / 45.9 | 92.9 / 37.3 | 0.55 |
| blk.0.attn_output.weight | 4096 × 4096 | 23 / 2 | 173.7 / 148.2 | 181.8 / 139.2 | 2.19 |
| blk.0.ffn_gate.weight | 4096 × 12288 | 23 / 2 | 745.3 / 681.7 | 773.4 / 716.0 | 6.56 |
| blk.0.ffn_up.weight | 4096 × 12288 | 23 / 2 | 730.7 / 688.9 | 777.0 / 729.1 | 6.56 |
| blk.0.ffn_down.weight | 12288 × 4096 | 23 / 2 | 759.1 / 735.4 | 781.0 / 749.2 | 2.19 |
| output.weight | 4096 × 151936 | 23 / 2 | 8864.1 / 8542.4 | 14446.2 / 13752.8 | 81.14 |

At q32 the old Q projection issued eight four-column matmuls with seven joins. The packed projection issued one four-column, eight-group matmul. Trace records include kernel names, launch grids, block dimensions and durations. The profiler and clean measurements used separate binaries. CPU graph-definition time, submission and synchronization wait are separate fields in the replay receipts. GPU kernel times can overlap CPU submission and must not be added to the wall interval.

### Diagnostic attribution at 32 columns

All entries are microseconds. CPU definition includes creating the graph arena and nodes. Submit/wait are medians after the initial run, without CUPTI. The kernel sum is from the separate trace and excludes transfer activities.

| Operator | Implementation | CPU graph definition | Host submit | Synchronization wait | GPU kernel sum |
|---|---|---:|---:|---:|---:|
| blk.0.attn_q.weight | tile | 13.6 | 6.9 | 165.5 | 166.3 |
| blk.0.attn_q.weight | packed | 13.0 | 8.4 | 141.8 | 139.2 |
| blk.0.ffn_down.weight | tile | 16.4 | 17.9 | 741.2 | 781.0 |
| blk.0.ffn_down.weight | packed | 12.7 | 26.6 | 712.3 | 749.2 |
| output.weight | tile | 20.2 | 35.9 | 8854.0 | 14446.2 |
| output.weight | packed | 15.3 | 26.6 | 8516.1 | 13752.8 |

## Active KV boundaries

Each cell restores a scalar R prefix from the same serialized state. P was measured as 256. Five paths matched all 800 appended vocabulary vectors and 40 subsequent continuation vectors. The append clock includes splitting, graph work, materialization, compute and synchronization. All 120 measured appends have an immediate same-arm warmup from identical state. The table gives geometric means in milliseconds over three paired blocks.

| Boundary | Head | q | Cross | S1 | QB4 | WB4 | New QB | New WB | New WB / QB |
|---:|---:|---:|:---:|---:|---:|---:|---:|---:|---:|
| 256 | 248 | 8 | no | 140.02 | 49.06 | 48.75 | 38.32 | 37.61 | 0.981 |
| 256 | 253 | 8 | yes | 125.57 | 46.76 | 62.88 | 41.98 | 62.75 | 1.495 |
| 256 | 224 | 32 | no | 448.43 | 165.81 | 165.57 | 135.44 | 135.47 | 1.000 |
| 256 | 253 | 32 | yes | 468.85 | 182.15 | 197.86 | 150.56 | 171.65 | 1.140 |
| 1024 | 1016 | 8 | no | 119.58 | 44.54 | 45.21 | 39.69 | 39.96 | 1.007 |
| 1024 | 1021 | 8 | yes | 125.39 | 46.82 | 63.35 | 41.79 | 62.91 | 1.505 |
| 1024 | 992 | 32 | no | 457.04 | 173.39 | 174.04 | 143.85 | 144.72 | 1.006 |
| 1024 | 1021 | 32 | yes | 465.91 | 179.69 | 194.70 | 147.59 | 167.91 | 1.138 |

New WB time / new QB time is 0.999× for noncrossing cells and 1.307× for crossing cells. When q8 crosses, WB splits into three and five rows, so neither subgraph can use an eight-column packed operator. When q32 crosses, its 29-row second graph still packs 28 columns. The coordinates have deliberately balanced cut density. Their average has no deployment-frequency interpretation.

Every QK and AV row group agreed with the registered geometry. At B1024/H1021, q32 uses extents 1024 then 1280 with QK/AV groups 3+4+4+4+4+4+4+4+1. Local submits [32], whereas WB submits [3,29]. Local Q projection uses one [output,4,8] matmul. WB restarts at the boundary and uses three columns in the first graph, then seven four-column groups and a one-column tail. Counts, bytes and physical graph-build/reuse observations for every cell are in coordinates.json.

### Prediction and profiler check

QK and AV groups matched in every cell. Counts are CUDA kernels in a separate append trace. Concat MiB are logical writes to concat outputs seen by the scheduler. They differ from CUPTI memcpy bytes.

| H / q | QB predicted → observed calls | WB predicted → observed calls | Actual QK/AV rows | Old QB / new QB kernels | Old WB / new WB kernels | QB concat MiB old / new |
|---|---|---|---|---:|---:|---:|
| 248 / 8 | [8] → [8] | [8] → [8] | [4, 4] | 1808 / 1049 | 1808 / 1049 | 51.9 / 4.5 |
| 253 / 8 | [8] → [8] | [3, 5] → [3, 5] | [3, 4, 1] | 1952 / 1193 | 2713 / 2713 | 55.8 / 8.4 |
| 224 / 32 | [32] → [32] | [32] → [32] | [4, 4, 4, 4, 4, 4, 4, 4] | 7226 / 1913 | 7226 / 1913 | 908.0 / 78.8 |
| 253 / 32 | [32] → [32] | [3, 29] → [3, 29] | [3, 4, 4, 4, 4, 4, 4, 4, 1] | 7370 / 2057 | 8131 / 3577 | 922.1 / 92.8 |
| 1016 / 8 | [8] → [8] | [8] → [8] | [4, 4] | 1808 / 1049 | 1808 / 1049 | 51.9 / 4.5 |
| 1021 / 8 | [8] → [8] | [3, 5] → [3, 5] | [3, 4, 1] | 1952 / 1193 | 2713 / 2713 | 55.8 / 8.4 |
| 992 / 32 | [32] → [32] | [32] → [32] | [4, 4, 4, 4, 4, 4, 4, 4] | 7226 / 1913 | 7226 / 1913 | 908.0 / 78.8 |
| 1021 / 32 | [32] → [32] | [3, 29] → [3, 29] | [3, 4, 4, 4, 4, 4, 4, 4, 1] | 7370 / 2057 | 8131 / 3577 | 922.1 / 92.8 |

The six distinct scalar prefixes took 65.3 s to generate. The 120 append-pair processes spent 442.8 s loading the model and 104.5 s reading and restoring prefix state across both roles. Context initialization and all three of those costs are outside the append interval. Per-pair process wall time remains in the evidence.

## Unseen natural confirmation and service cost

The fixed panel used four fresh inputs, C1536, k3 and cap128. Old QB4, new QB and new WB matched 1524 committed-vector comparisons against immutable R and 1836 branch-vector comparisons against scalar k3, including uncommitted positions. The sets overlap. Endpoints and complete cycle transactions matched. Timed R was not an arm in this panel.

| Arm | Complete service s | Prefill wall s | Target verify s | Continuation wall s |
|---|---:|---:|---:|---:|
| oldQB | 3.3562 | 2.0814 | 0.7848 | 1.1957 |
| newQB | 3.2219 | 1.9420 | 0.7759 | 1.1856 |
| newWB | 3.1985 | 1.9228 | 0.7753 | 1.1839 |

Old QB / new QB was **1.0417×**. New WB / new QB was **0.9928×**. The first ratio isolates the operator change with local grouping fixed. The second compares group organization with identical operator lowering. Per-session WB/QB ratios were 0.9864, 0.9936, 0.9983.

The 36 service measurements and 36 immediate warmups used 125.4 and 117.2 service seconds. Model loading, pool provisioning and process wall are recorded separately in the raw receipts. Resident service includes reset, target and draft prefill, the inherited verify/rollback/sampling loop and synchronization.

The old/new QB session ratios were 1.0446, 1.0390, 1.0415. Packed QB won 11/12 matched blocks. Prefill accounts for most of the change. The k3 verification call stays at four rows and cannot enter the new packing path. The small verification-time difference is descriptive.

The 36 matched service processes spent 431.7 s wall time, including 148.0 s of model loading and 1.0 s of pool setup.

## Contribution boundary

The supported mechanism is parallel execution of independent compatible reductions using an existing CUDA dispatch. It removes repeated launch and concat work without relaxing the original numerical reference. The operator benefit applies to WB and QB alike. Local grouping and operator packing are separate contributions. Their estimates must stay separate. The aligned PR168 pilot and its mixed session directions remain historical evidence. Four natural inputs on one RTX system do not establish population speedup. This result is ready for comparison with the independent B570 work.
