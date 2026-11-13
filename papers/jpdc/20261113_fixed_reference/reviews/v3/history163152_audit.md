# V3 historical mechanism review: Vulkan arithmetic/attention and producer state

## Scope actually reviewed

Read the two complete frozen result reports, current V2 method and results sections, and relevant supplement passages. Retrieved the public committed-vector audit JSONs and endpoint/ablation summaries for the Llama study; retrieved the full 48-cell matrix, eight-row state effects, and protocol for the producer study. Counts below are CPU counts of those public records, not a replay of native tensors or a new GPU experiment. No private evidence archives were opened or republished.

The current V2 already explains that producer state matters, that Vulkan attention extent changes can alter dispatch, and that matching argmax is insufficient. It does not yet present the concrete projection-only 99-vector counterexample or the historical producer matrix. The new material can replace part of the repeated CPU-counterexample explanation in Results rather than adding a new research branch.

## 1. Llama Q8: projection repair does not finish the reference obligation

Frozen directory: [`10a70566ce01ab707dbdcc57d8270c1434088f07`, host_execution](https://github.com/leecdiang/HeteroSpec/tree/10a70566ce01ab707dbdcc57d8270c1434088f07/benchmarks/b570_llama_companion_v1/host_execution).

Contract: Arc B570 / Vulkan, Meta-Llama-3.1-8B-Instruct-Q8_0 target, Llama-3.2-1B-Instruct-Q8_0 draft, target on GPU and draft on CPU, context 1024, F16 KV, flash attention disabled, k=3, cap=128, eight threads. Reference is the frozen stock UB1 oracle built from upstream `0cae43063cf15170e91a2ff4d034da0ecef4a1b2`; final candidate source is `5d1272dcb2e53b73e3e72db4c403361fbef7d6c4`. This is distinct from the CUDA width study, S3, and the later C4096 natural multi-turn pilot.

### Critical scope correction to the shorthand “99 vectors”

The full public [`COMMITTED_REFERENCE_AUDIT-00.json`](https://github.com/leecdiang/HeteroSpec/blob/10a70566ce01ab707dbdcc57d8270c1434088f07/benchmarks/b570_llama_companion_v1/host_execution/COMMITTED_REFERENCE_AUDIT-00.json) has three inputs × five audited arms (including R) × 128 committed rows = **1,920 rows**. The long input `CodeContests/valid/108` has **99 differing rows in C_PQ and 99 in C_QB**, both at zero-based output indices 29–127. Thus there are 198 discrepant records across both layouts, representing the same 99 affected output positions in each layout. The other 13 input–arm cells have no discrepant committed row. Do not write “99/1,920” or imply 99 is the total over both arms.

The corresponding [`COMBINED_COMMITTED_AUDIT-03.json`](https://github.com/leecdiang/HeteroSpec/blob/10a70566ce01ab707dbdcc57d8270c1434088f07/benchmarks/b570_llama_companion_v1/host_execution/COMBINED_COMMITTED_AUDIT-03.json) has the same 1,920 coordinates and **zero** discrepancies. The independent summary also reports the complete three-input, 36-request development matrix, 3,152 saved vectors and 1,920 committed candidate vectors; these counts overlap by design and are not independent samples. See [`COMBINED_INDEPENDENT_DEVELOPMENT-00.json`](https://github.com/leecdiang/HeteroSpec/blob/10a70566ce01ab707dbdcc57d8270c1434088f07/benchmarks/b570_llama_companion_v1/host_execution/COMBINED_INDEPENDENT_DEVELOPMENT-00.json).

All 15 endpoint cells in [`Q8_REPAIR_BASELINE_AUDIT.json`](https://github.com/leecdiang/HeteroSpec/blob/10a70566ce01ab707dbdcc57d8270c1434088f07/benchmarks/b570_llama_companion_v1/host_execution/Q8_REPAIR_BASELINE_AUDIT.json) report reference equality and observer stability. Its `QUALIFIED` status and PQ/QB full-vector correspondence **do not mean every committed vector equals the stock scalar reference**: the separate committed audit exposes the 99-per-layout failures. This distinction is precisely the useful scientific finding.

[`COMBINED_NO_PREFIX_BASELINE_AUDIT.json`](https://github.com/leecdiang/HeteroSpec/blob/10a70566ce01ab707dbdcc57d8270c1434088f07/benchmarks/b570_llama_companion_v1/host_execution/COMBINED_NO_PREFIX_BASELINE_AUDIT.json) again retains endpoint equality. [`PREFIX_FACTOR_REVERSAL-00.json`](https://github.com/leecdiang/HeteroSpec/blob/10a70566ce01ab707dbdcc57d8270c1434088f07/benchmarks/b570_llama_companion_v1/host_execution/PREFIX_FACTOR_REVERSAL-00.json) records complete equality of the 36-request / 3,152-saved-vector prefix-off trajectory to the projection-only trajectory. The report identifies this as a same-binary prefix-off control. Accordingly it restores the same 99 differing committed rows in each speculative layout. Removing the Q8 projection repair instead restores endpoint failures in [`COMBINED_NO_Q8_BASELINE_AUDIT.json`](https://github.com/leecdiang/HeteroSpec/blob/10a70566ce01ab707dbdcc57d8270c1434088f07/benchmarks/b570_llama_companion_v1/host_execution/COMBINED_NO_Q8_BASELINE_AUDIT.json).

### Suggested compact supplement table

| Configuration | Development endpoints equal reference | Differing committed rows on long input, per speculative layout | Across all 1,920 audited committed rows |
|---|---|---:|---:|
| Projection repair only | Yes | 99 / 128 | 198 |
| Projection + attention repair | Yes | 0 / 128 | 0 |
| Combined binary, attention repair disabled | Yes | 99 / 128, restored trajectory | 198, restored trajectory |

Caption should define the three inputs, the five audited arms R/M_PQ/M_QB/C_PQ/C_QB, and the 128 committed decisions per cell; the 99 affected positions are counted once in each of C_PQ and C_QB. The third row follows full trajectory reversal, not a new independently retrieved committed-vector audit. A short adjacent sentence can state that disabling projection repair reintroduces endpoint failures. No timing or historical large gain is needed in this mechanism table.

### Mechanism and attribution

The projection intervention is real: scalar Q8 projection uses F32 activations while q4 ordinarily selects Q8_1. Scoped F32 policy restores scalar projections. The final width audit has 21 real-operand Q/K/V calls at q=1,2,3,4: [`FINAL_PROJECTION_WIDTHS_AUDIT-00.json`](https://github.com/leecdiang/HeteroSpec/blob/10a70566ce01ab707dbdcc57d8270c1434088f07/benchmarks/b570_llama_companion_v1/host_execution/FINAL_PROJECTION_WIDTHS_AUDIT-00.json).

The attention intervention jointly changes physical extent, contiguity and dispatch. At cycle 8/base 765, the first three scalar rows use extent 768 and the last uses 1024; the ordinary q4 path uses 1024 throughout. The public eleven-call [`AV_EXTENT_AUDIT-00.json`](https://github.com/leecdiang/HeteroSpec/blob/10a70566ce01ab707dbdcc57d8270c1434088f07/benchmarks/b570_llama_companion_v1/host_execution/AV_EXTENT_AUDIT-00.json) shows the 768-entry cases dispatching `mul_mat_vec_nc_f16_f32`, while 1024-entry cases dispatch `mul_mat_vec_f16_f32_f32`. Cropped results reproduce scalar row hashes. This supports the joint attention-path requirement; it does not isolate an unchanged-pipeline loop-length cause.

Suggested main-text bridge:

> The Vulkan Llama case separates the two obligations. Restoring the scalar projection arithmetic makes the development endpoints agree, yet 99 of 128 committed vocabulary vectors still differ in each speculative layout on the long input. Grouping attention by the reference path removes these discrepancies, and disabling that repair restores them. This intervention changes extent, contiguity and dispatch together. Matching tokens and repaired projections therefore leave an attention-path obligation that full-vector comparisons can expose.

Use one source citation plus a supplement table pointer. Exact qualification is finite and already bounded in Methods; no extra generic disclaimer is necessary here.

## 2. Producer × consumer: a compact historical illustration

Frozen study: [`022babfabb3d1b6f4f2a2830dca04b2654d193f9`](https://github.com/leecdiang/HeteroSpec/tree/022babfabb3d1b6f4f2a2830dca04b2654d193f9/benchmarks/b570_producer_consumer_boundary_v1).

The [`PROTOCOL.md`](https://github.com/leecdiang/HeteroSpec/blob/022babfabb3d1b6f4f2a2830dca04b2654d193f9/benchmarks/b570_producer_consumer_boundary_v1/PROTOCOL.md) fixes Qwen3-8B-Q8_0 and Qwen3-0.6B-Q8_0 on B570 Vulkan, F16 KV, flash attention off, eight threads. This is a **boundary0 clean-receiver** experiment with **k=1** speculative consumers (target verification q=2), cap 128. P1 produces the prompt one ID per call. P4T produces four IDs per call; tails 1/2 are direct and tail 3 is 2+1. Both use the PQ producer and request only the final prompt output. The factor changes the target producer state, while the draft producer remains serial. Consumers import the serialized sequence state and the complete initial FP32 logits into a clean target context. C1 is target-only; PQ and QB are the two speculative attention layouts.

The full [`execution/MATRIX.csv`](https://github.com/leecdiang/HeteroSpec/blob/022babfabb3d1b6f4f2a2830dca04b2654d193f9/benchmarks/b570_producer_consumer_boundary_v1/execution/MATRIX.csv) contains **48 cells = 8 inputs × 2 producers × 3 consumers**. [`STATE_EFFECTS.csv`](https://github.com/leecdiang/HeteroSpec/blob/022babfabb3d1b6f4f2a2830dca04b2654d193f9/benchmarks/b570_producer_consumer_boundary_v1/execution/STATE_EFFECTS.csv) confirms changed KV serialization **and** changed initial logits on all eight inputs. Within each producer, PQ and QB agree on endpoint, cycles, and full vectors, including discarded verification rows, for all **16 input–producer pairs**.

### Suggested supplement table (three outcome classes preserve all eight inputs)

| Input class | n | P1 C1 = R | P4T C1 = R | P1 PQ/QB = R | P4T PQ/QB = R |
|---|---:|---|---|---|---|
| Five unchanged-endpoint inputs | 5 | Yes | Yes | Yes | Yes |
| MATH500 prealgebra 1865 and 1804 | 2 | Yes | Yes | No | Yes |
| GSM8K train 1184 | 1 | Yes | No | No | No |

The five-input class contains GSM8K/train/582, /4140, /2279 and MATH500/test/geometry/846.json, /465.json. The two prealgebra cases first differ from R at one-based outputs 5 and 25 under P1 PQ/QB. These are the clearest fixed-reference examples: C1 keeps the same R under both producers while speculative consumers change eligibility. In the GSM8K case, P4T also changes C1's endpoint, first at output 30. Therefore the table must compare against fixed R, not silently replace R by each producer's own C1. The original source table additionally gives the producer-conditioned comparisons.

Suggested short prose:

> A historical B570 clean-receiver test makes the producer requirement concrete. Across eight inputs, two speculative layouts agree with one another under both prompt producers. On two inputs, changing the producer changes whether both layouts preserve the fixed reference, even though the ordinary consumer retains the same reference endpoint. The changed boundary includes both KV and initial logits. These k=1 results precede the later repairs and describe that historical boundary contract, rather than the C4096 multi-turn implementation.

This study adds a concrete reason to bind producer state; it does not isolate KV alone, prove production demand, qualify arbitrary q4 operators, or measure service benefit. Keep it in the supplement. The full eight-row CSV already suffices for readers who want individual coordinates.

## 3. Files prepared for the parent editor

- `history163_committed_rows_projection.json`: all 3,840 committed-row records from the two public audits, retaining input ID, arm, output index and equality flag without filtering. Source URLs and projection descriptions are included.
- `history163_controls_projection.json`: all endpoint cells, full prefix reversal slot counts and independent combined qualification summary; workstation paths and receipt hashes are omitted.
- `history152_MATRIX.csv`, `history152_STATE_EFFECTS.csv`, `history152_STATE_SUMMARY.json`: verbatim public tabular/summary files.

No manuscript files were changed. No native experiment was run. The source reports' broad evidence archive verification was not independently repeated here. The shorthand 99-vector issue is resolved by explicit per-layout counting; it does not invalidate the mechanism finding.
