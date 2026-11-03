# B570 Qwen shared-rule transfer

Both retained MATH P1 counterexamples now preserve the original scalar Qwen reference. P1 uses the historical one-token caller sequence in its UB4 producer. The final candidate restores the exact original P1 state and initial logits. Its resumed PQ and QB consumers reproduce every committed scalar vector, including on the inputs where P4T had already passed. On GSM1184 the repaired P4T producer itself produces the original P1 boundary.

In the frozen eight-input panel, QB took 8.50% less complete service time than PQ for ordinary greedy generation and 3.09% less for speculative generation. Speculative QB took 2.2432 times the original R service time. All 120 measurements and immediate warmups are included.

## Original contract and retained cases

The all-GPU Qwen3-8B and Qwen3-0.6B Q8 files, eight threads, F16 KV, non-flash attention, historical k1 transaction behavior, original inputs and cap128 are pinned. The reference input/recording adapter links PR152's original numerical DLLs. Each of its 384 retained scalar vectors and the three endpoints matched the historical records before unseen use. Both roles passed zero-forward admission. The initial failed host-memory admission remains in the cumulative evidence.

| Retained input | Historical first differing output (zero-based) | Final result against original R |
|---|---|---|
| MATH500 prealgebra 1865 | P1+PQ/QB at 4 | Same P1 boundary. Both resumed paths match all 128 committed vectors. |
| MATH500 prealgebra 1804 | P1+PQ/QB at 24 | Same P1 boundary. Both resumed paths match all 128 committed vectors. |
| GSM8K train 1184 | P1+PQ/QB and P4T+C1/PQ/QB at 29 | P1 and repaired P4T boundaries match historical P1. Both producers' ordinary and resumed paths match all 128 committed vectors. |

Matched PQ/QB transactions and all saved vectors, including conditional rejected rows and draft decisions, agree within each producer. The new P4T state on GSM1184 differs from its historical failing P4T state. Development controls use the original historical producer and caller sequences. Integrated confirmation and cost use one fixed P4T target prefill policy throughout.

## Predictions and native observations

| Condition | Prediction | Observed on B570 |
|---|---|---|
| P1 width-two verification, Q8_0 weights and F32 input | Scalar dispatch retains F32, native batch default would quantize. Keep F32 activations with batched work. | Native selector recorded scalar_quant=0, batch_quant=1, selected_quant=0 and mul_mat_vec_q8_0_f32_f32. MATH1865 and 1804 both preserve P1+PQ/QB. |
| GSM1184 P4T producer | Batch projection needs the same arithmetic preservation during prefill. | Target prefill selected the batched F32 path at widths four and two. Its boundary KV and initial logits equal historical P1. |
| Width two, physical head254, padding256 | Extents [256,256], one group | Native cache used=256, occupied_end=256. No split. Both full rows equal scalar teacher forcing. |
| Width two, physical head255, padding256 | Extents [256,512], groups 1+1 | Native cache used=257, occupied_end=257, capacity1024. Split observed. Both full rows equal scalar teacher forcing. |
| Stable versus changed same-shape policy | Reuse stable graph, reject prior graph on precision change | Real reuse counter increments at base259, stays unchanged on the switch at261, increments again once stable at265. |
| Precision-only reversal on original MATH1865 P1 | Default batched activation quantization and historical failure return | Same candidate binary selects mul_mat_vec_q8_0_q8_1_f32. All 205 saved vectors, complete transactions and endpoint match the historical failure. |
| PR163 Llama boundary and ordinary control | Base765 groups 3+1, no verification split on the ordinary input | All 32 layers use Vulkan0 at the 3+1 boundary. Both controls reproduce the historical trajectories and all 548 saved vectors. |

The retained MATH cases stay in one physical bucket. The independent boundary probe establishes the Qwen split under real native cache conditions. The F32 intervention explains the repaired P1 failures. The mapping uses tensor types, dimensions, strides, device dispatch predicates, cache occupancy and policy state without model names or input identity.

## Frozen confirmation

Source freeze was at commit 9848cce08b5b1eb872449aa03440352bef50ab4e. Selection and timing order were written after freeze and before any unseen model request. The authenticated PR163 exposure inventory and subsequent exposed inputs were applied to the pinned natural source pool. The exact Qwen tokenizer round-tripped all three historical prompts. The available near-boundary stratum contained 37 natural math inputs and zero code inputs. Four near-boundary math inputs and four ordinary inputs spanning code and math were selected.

All 8 original R, 32 heavy candidate and one clean observer-control request passed. The 6,316 saved full-vocabulary vectors passed raw digest and greedy reconstruction. Each of the 4,096 committed candidate vectors equals its original scalar vector byte-for-byte. All eight outputs reached the registered cap of 128. PQ/QB logical transactions and complete conditional vectors match, and the representative heavy/clean trajectories agree. Per-input cells are in QUALIFICATION.json.

## Complete fixed costs

Ratios are geometric means of 24 equally weighted session/input blocks. Each cell uses the complete measured service window. The five arms share the declared placement and exact inputs. R has its original scalar prefill, while the four integrated arms use P4T. M/R therefore includes the prefill policy difference.

| Numerator / denominator | All blocks | Session 1 | Session 2 | Session 3 | Blocks above / below 1 |
|---|---:|---:|---:|---:|---:|
| M_QB / M_PQ | 0.915047 | 0.916938 | 0.916287 | 0.911925 | 0 / 24 |
| C_QB / C_PQ | 0.969123 | 0.972818 | 0.965850 | 0.968712 | 0 / 24 |
| M_QB / C_QB | 0.269172 | 0.268659 | 0.269437 | 0.269421 | 0 / 24 |
| M_QB / original R | 0.603813 | 0.603678 | 0.603853 | 0.603908 | 0 / 24 |
| C_QB / original R | 2.243222 | 2.247004 | 2.241164 | 2.241504 | 24 / 0 |

Across the 120 model-loaded pairs, warmup service totaled 1,698.180 s and measured service 1,696.091 s. Model loading took 613.423 s, measured separately in the driver. Total native process time was 4,165.961 s, including 158.267 s outside model loading and service. Host-owned time for these pairs was 4,221.382 s. The 41 qualification requests used 826.345 host-owned seconds, of which 145.673 s were for the eight original reference requests, including 41.077 s loading their models.

The separate phase subset used the predeclared first input, MATH/prealgebra/train/54. Original R spent 6.301 s in target prefill and 3.519 s in ordinary decode. M_QB spent 2.350 s and 3.516 s in the same phases. C_QB spent 2.367 s in target prefill, 10.140 s in draft prefill, 3.861 s in draft synchronization decode, 3.824 s in proposal decode and 2.559 s in target verification. Both measured trim phases together were under 0.001 s. PHASES.json contains the separate service windows. These instrumented durations describe that input only. All formal timings used clean fresh contexts without heavy callbacks, phase clocks or trace writes.

## Evidence and scope

The complete run records 318 natural model requests, four separately identified teacher-forced sequences and one failed zero-forward admission. All native jobs have cleanup receipts. Full block reversals, raw seconds, phase clocks, predictions and original failures remain available. The standalone CPU auditor independently reconstructs the retained results, all eight unseen qualifications and all 120 cost pairs.

The tested domain is this B570/Vulkan runtime, frozen model pair, supported Qwen graph/cache shapes and finite natural panel. These descriptive comparisons supply no population confidence interval. The independent result PR contains no manuscript changes.
