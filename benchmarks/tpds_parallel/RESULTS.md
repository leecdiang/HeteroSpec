# RTX reference-preserving execution pilot

On the fixed 8B panel, the fastest reference-compatible competitor to QB-local was WB-cut. Its geometric mean service time divided by QB-local’s was **1.0104×**. QB-local was faster in 5 of eight input/context/session blocks. The frozen pilot criterion was missed.

## Numerical results and native lowering

The four methods and timed R matched all 2,560 committed full-vocabulary vectors across two unseen inputs at context capacities 1024 and 1536. The three grouped methods also matched 1,896 speculative decision vectors against S1, including uncommitted branches. All k3 cycle records matched. The 1024 oracle ran the original executable. The 1536 oracle used an independently linked, unmodified PR166 core. Timed R ran on the candidate runtime.

The inputs were MATH/algebra/train/687 (255 prompt tokens) and APPS/train/920 (593). Each speculative cycle used the inherited k3 verification and rollback. Widths above four were target prefill or teacher-input mechanism probes.

| Probe | Predicted whole-graph calls | Observed layer-zero QK rows | Executing backend |
|---|---:|---|---|
| cross256, QB-local | [32] | [3, 4, 4, 4, 4, 4, 4, 4, 1] | CUDA0 |
| cross256, WB-cut | [3, 29] | [3, 4, 4, 4, 4, 4, 4, 4, 1] | CUDA0 |
| cross512, QB-local | [16] | [2, 4, 4, 4, 2] | CUDA0 |
| cross512, WB-cut | [2, 14] | [2, 4, 4, 4, 2] | CUDA0 |
| eight, QB-local | [32] | [3, 4, 4, 4, 4, 4, 4, 4, 1] | CUDA0 |
| eight, WB-cut | [3, 29] | [3, 4, 4, 4, 4, 4, 4, 4, 1] | CUDA0 |
| fourteen, QB-local | [8] | [4, 4] | CPU |
| fourteen, WB-cut | [8] | [4, 4] | CPU |

The 8B crossing at position 253 produced one 32-row graph for QB and two whole-graph calls of widths 3 and 29 for WB. Their attention tiles read extents 256 and 512. At position 510 the extents were 512 and 768. Wide graph callers retain parallel four-column Q8 matmuls for Q/K/V, output, FFN and vocabulary projection. The 32-row graph therefore does not imply a 32-row elementary matmul or attention group.

Qwen3-0.6B has 16 query and 8 KV heads, versus 32/8 on 8B and 40/8 on 14B. At layer zero the fully offloaded 0.6B and 8B graphs placed both rotary head scales on CUDA. On the partially offloaded 14B graph Q scale ran on CUDA and K scale ran on CPU at width eight. The same structural rule selected these placements. All three models use head dimension 128. Scheduler records identify the executing backend and op shape. No kernel-level profiler was used.

The early wide implementation hit invalid tensor views and exhausted the graph arena on scalar-attention lowering. After the view offset was fixed, retaining wide projection dispatch still changed all eight logits rows in the first 0.6B QB probe. Four-column projection lowering and row-sized graph storage restored the fixed reference in the measured wide cells. The failure attempts and their observed rows remain in the mechanism evidence.

## Complete service and phase costs

Seconds are geometric means across eight matched measurements per arm. Service includes resident reset, both prefills where applicable, generation, rollback, sampling and synchronization. Prefill wall ends at the first committed token. Continuation wall covers the rest of generation. Verify is synchronized target decode time within continuation. The means of components need not sum to the geometric mean of the service time.

| Arm | Service s | Prefill wall s | Target verify s | Continuation wall s | Arm / QB time |
|---|---:|---:|---:|---:|---:|
| R | 8.574 | 6.104 | — | 2.290 | 2.0722 |
| S1 | 11.265 | 7.684 | 2.782 | 3.222 | 2.7225 |
| PQ-ext | 4.397 | 2.867 | 0.945 | 1.390 | 1.0626 |
| QB-local | 4.138 | 2.739 | 0.822 | 1.258 | 1.0000 |
| WB-cut | 4.181 | 2.770 | 0.840 | 1.278 | 1.0104 |
| native32 | 2.340 | 1.073 | 0.732 | 1.180 | 0.5654 |
| native-full | 2.100 | 0.860 | 0.717 | 1.163 | 0.5076 |
| native-ordinary | 2.419 | 0.112 | — | 2.290 | 0.5845 |

The WB-cut/QB ratios in sessions one and two were 0.9844 and 1.0371. The fastest tested stock arm was native-full at 2.100 s. It differed from the numerical oracle on 512 committed positions and matched 0 of four endpoints. Stock candidates used the retained F16 KV, non-flash backend with the registered batch widths. This comparison does not characterize other flash-attention settings.

The four timing processes consumed 670.0 s wall time, including 16.5 s of model loading and 1.2 s of pool setup. The 64 warmups consumed 320.9 service seconds and the 64 measured requests consumed 325.6. Process startup, pool release, output and remaining host costs are included in the process wall receipts.

## Graph reuse during qualification

Counts below sum the four natural input/context observations per method. The reuse counter spans target and draft contexts. Physical histograms refer to target ubatches only. Capture observations and timed service are reported separately.

| Method | Reused graphs | Prefill physical widths (width × calls) | Verify physical widths (width × calls) |
|---|---:|---|---|
| R | 2190 | 1 × 1696 | — |
| S1 | 4632 | 1 × 1696 | 1 × 632 |
| PQ-ext | 2508 | 17 × 2, 31 × 2, 32 × 50 | 4 × 158 |
| QB-local | 2508 | 17 × 2, 31 × 2, 32 × 50 | 4 × 158 |
| WB-cut | 2508 | 17 × 2, 31 × 2, 32 × 50 | 1 × 2, 3 × 2, 4 × 156 |

## TPDS contribution judgment

The evidence establishes a placement-sensitive execution mechanism and a bitwise comparison against two strong alternatives on this RTX worker. The incremental local-cut advantage over WB-cut was +1.04% in throughput-equivalent terms on this panel. It falls short of a consistent 3% pilot advantage; the evidence supports a mechanism result, with a narrower performance claim.

Relative to per-row attention, QB-local delivered 1.063× end-to-end speedup. Target verification fell from 0.945 s to 0.822 s. Compared with WB-cut, the frozen width-32 prompt chunks aligned with the 256-cell boundaries and both methods used the same physical prefill widths. WB made additional whole-graph cuts on only two of 158 verification calls across the four observations. The large savings over timed R and S1 are shared by WB as well.

The numerical transfer spans three Q/KV mappings, while complete service timing is confined to one GPU and one target/draft pair. The two inputs recur across both contexts and sessions, so the eight paired blocks are not eight independent workloads. A claim of general superiority for TPDS exceeds these data.

The evidence directory includes per-block reversals, original reference digests, raw timing receipts, executed tensor shapes, source pins and the saved panel. The README gives native and offline reproduction instructions.
