# B570: connecting micrographs to the reference request

This follow-up addresses the gap between the PR128 synthetic mapping experiment and the paper's real model workload. The user authorized necessary follow-up and repairs after the model-free study. It does not retrospectively change that study's scope or any CPU8 qualification.

## What the real request establishes

The existing, hash-verified Qwen3-8B Q8_0 model processes the unchanged 124-token HumanEval/42 prompt from the previously exposed development set. The new run uses the serialized ubatch=1 reference configuration, context 1024, F16 KV, FlashAttention disabled and a 16-token greedy cap. Three fresh contexts share a loaded model in each process. The middle context records metadata but always declines per-node evaluation; the other two have no evaluation callback.

Actual metadata shows Hq/Hkv=32/8, d=128 and 36 layers. QK, softmax, AV and final recombination are placed on B570. The physical attention-key extent is 256 and q=1 in this request. The context capacity of 1024 must not be mistaken for an executed key extent of 1024. The runtime reports 37/37 layers offloaded; CPU-mapped model storage remains present, so this is not a claim that every operation or all storage reside on the GPU.

The prior micrograph used Hq/Hkv=8/8 and keys 1023–1025. Its q2/q4 conclusions do not transfer directly to this real request. Under the tested q1 reference path, the QB and QH graph prototype uses the same original chain. No multiquery model mapping was enabled.

## Measurement failures and repairs

The initial host tried a dynamic-plugin loader against a backend already registered by the pinned linked DLLs. It failed before loading the model. Removing the unsupported loader calls repaired the host; the failed process and its charge remain in the ledger.

The backend's serial performance logger adds per-operation synchronization. It failed the predeclared observer screen: median decode cost increased by about 12%, while its clean controls differed by less than 1%. Its per-operation fractions are retained as perturbed diagnostics.

Concurrent logging reduced the perturbation, but source and counter inspection exposed an omitted terminal interval. The final output projection was absent from all three context tables. A terminal timestamp and graph-end index restore that interval. A further attribution repair filters empty and non-compute nodes with the same predicate used by the executor, preventing zero-length inactive operations from appearing in group labels.

These changes affect the diagnostic logger only. They do not alter arithmetic shaders, Q/K/V tensors, model graph construction, model weights or sampling. All earlier logger outputs remain available; they are not relabeled as complete.

## How to use the final evidence

Use the final same-DLL clean/profile/clean results in `ANALYSIS.json` and `RESULT.md`. All three context tables must account for 16 positive-width output projections and 5,004 effective QK, softmax, AV and recombination operations each: 36 layers × (124 prompt positions + 15 continuation decodes). Mixed timestamp groups are never divided among their members by assumption.

The 10% median-decode gate is an exploratory necessary observer check, not a proof of per-operator noninterference or statistical equivalence. The final profile still measures a synchronized, instrumented GPU subtotal over the prompt and continuation. It does not measure a natural-request critical-path fraction. Do not insert these fractions into an Amdahl speedup formula.

The small QK/softmax/AV core excludes Q/K/V and output projections, RoPE, cache updates, and other work commonly included in a broader definition of “attention.” Quantized matrix-vector groups include both FFN and attention projections and sometimes fused additions. They must not be described as “FFN only” or used to diagnose DRAM bandwidth from operation names alone.

## Manuscript placement and bounded contribution

Place this follow-up immediately after the B570 micrograph cost comparison, before hardware implications. A suitable claim is:

> A real-request scope check prevents extrapolation from an exposed micrograph to an unmeasured workload. On the tested serialized Qwen3-8B request, the actual attention geometry is GQA with q=1 and a physical key extent of 256, rather than the equal-head, near-1024 micrograph. Observer calibration and execution-count checks additionally reveal that seemingly detailed profiler output can both perturb execution and omit its terminal interval. After repairing the logger, the resulting group costs remain diagnostic GPU subtotals. They support prioritizing investigation of the measured quantized projection groups over an unestablished multiquery attention-mapping opportunity, without establishing a new hardware bottleneck or end-to-end gain.

The scientific progression is therefore:

1. Preserve the prescribed implementation reference and full output evidence.
2. Establish the mapping's finite-input admissibility.
3. Compare against a strong fixed baseline with A/A controls.
4. Charge the input representation transaction.
5. Check that the proposed opportunity occurs in the real reference request.
6. Calibrate and validate the observer before interpreting its cost attribution.

This strengthens the paper's evidence discipline and closes the immediate B570 attention-mapping branch. It is not a new accelerator contribution.

## What remains unestablished

Only one previously exposed prompt and one device/date are covered; repeated contexts and processes are not independent workload samples. The short cap does not qualify the full HumanEval workload or transfer historical token-level passes. Cross-process complete-logit equality is relative to the new clean reference for this fixed request.

A physical bottleneck diagnosis still needs calibrated hardware counters, traffic/occupancy evidence and interventions. Larger-scale model optimization also requires a distinct admissible candidate and representative workload qualification. There is no evidence here to justify actor/RTL work or to revive the CPU8 framework as a prerequisite for this research result.

Keep CPU8/PR127 status and all old failures unchanged. Preserve the remaining budget rather than spending it on another repetition of a closed hypothesis. The final cumulative balance is recorded in `RESULT.md` and `BUDGET_LEDGER.json`; never restart a historical launcher with its old starting charge.
