# Shared reference-batching transfer

## Research question

Can one executable planner derive batching requirements from the actual model graph, cache state and backend arithmetic, then preserve an existing numerical reference across Llama and Qwen without model-name rules?

The result should be a reusable method and a predictive transfer result. The existing Llama evidence already establishes the physical-prefix mechanism on CUDA and Vulkan. This study turns that mechanism into a shared implementation and tests the missing cross-family behavior. It does not repeat the previous full Llama panels or seek a different answer from their timing results.

## Starting points

| Role | Frozen source/result |
|---|---|
| CUDA repaired Llama + combined Qwen regression | PR162, `e11d2b75d82422409ba2b701aa38c59f36acc50b` |
| CUDA Qwen14B causal head-normalization placement repair | PR159, `38b3d3d3929dc958e6a2a7e0bdc8abd61ff38ab1` |
| Vulkan repaired Llama | PR163, `10a70566ce01ab707dbdcc57d8270c1434088f07`; frozen candidate source `5d1272dcb2e53b73e3e72db4c403361fbef7d6c4` |
| Vulkan Qwen producer–consumer counterexamples | PR152, `022babfabb3d1b6f4f2a2830dca04b2654d193f9` |
| Shared candidate | `src/reference_batching/reference_batching.hpp` and `src/reference_batching/integrate_llama_cpp.py` in this PR |

Use new worktrees/build/output directories and the authenticated existing assets. Keep the old references, weights, historical inputs, reports and failure records intact. Ordinary build, adapter, observer and integration defects may be fixed autonomously; record the material source changes and continue. No permission round is required for these already-authorized tasks.

## Deliver the method first

The current shared header implements physical-prefix extraction, adjacent grouping and policy identity. The source integrator connects the prefix planner and graph-reuse checks to the two repaired source trees. The header's arithmetic/dispatch requirement fields and projection decision helper are interfaces; a zero-valued placeholder or an unused helper is not cross-family policy extraction.

Complete the native extraction and call sites on the hosts:

1. Read actual graph/operator roles, tensor shapes and strides, Q/K head structure, weight/input/activation types, scalar-reference placement or dispatch, cache occupancy, slot head and native padding. Derive requirements from these quantities, without selecting by model name, prompt ID, answer, output position or margin.
2. Invoke the shared planner with requirements actually derived from the native path. If arithmetic/dispatch IDs are used, construct them from explicit descriptors; do not leave default IDs and claim those conditions were inspected.
3. On Vulkan, use the observed scalar/batch activation paths to select the existing F32-activation batch projection when required. On CUDA, derive the scalar-compatible head-normalization placement from the actual graph and backend preference. Preserve the real operands and existing batched work where the condition permits it.
4. Bind the effective policy and per-row extent/requirements to graph reuse. Check a representative same-shape policy change and a boundary transition; no need for a second exhaustive archival audit.

The native backend's admitted domain remains explicit. For example, the current Vulkan layout has guards for head dimension 128, 32 Q heads, 8 KV heads, q2–4 and key extents 256–1024. Extend a guard only with implementation support and a corresponding native control. A general C++ planner alone does not expand a shader's supported shapes.

For unsupported shapes or states, report the reason and preserve safe existing behavior. Such a case is not counted as a successful transfer. A model-wide serial fallback is not the intended research result; a necessary local split retains the maximal supported groups.

## Predictive structural probes

Before running a new diagnostic case, record its expected groups or policy action from the extracted structure. Include boundaries and nearby non-boundaries. Use the existing native padding and the actual query widths reached by each harness; do not force every platform to the same k.

For the dense append condition, the shared rule predicts

`e_i = min(capacity, max(padding, ceil((head+i+1)/padding)*padding))`.

At head 765, width 4, padding 256 it predicts `[768,768,768,1024]` and groups 3+1. At head 764, width 4 it predicts one four-row group. Test the corresponding native cases that matter for Qwen, including a different query width or padding boundary when the existing adapter supports it. Teacher-forced or captured-state operator probes are acceptable diagnostics and are labelled as such; they do not replace natural unseen generation.

Save compact actual trigger records for these diagnostics:

- Request/checkpoint and phase; actual row positions and widths.
- Physical cache state, scalar extents and resulting groups.
- Structural arithmetic/dispatch descriptors and the selected action.
- Whether the relevant rule actually fired; if it did not, the reason.
- Effective graph-policy identity and whether reuse was accepted or invalidated.

These are native observations. Do not fill them from the desired case table or infer them from the fact that the final token is correct. Keep diagnostic collection off during formal timing.

## Division of work

### RTX / CUDA

Compile the shared candidate from the restored final PR162 source. Exercise Qwen3-8B and Qwen3-14B under the same structural policy, with real boundary triggers and the scalar-compatible normalization-placement rule. Existing Qwen regression success is useful but does not establish that a prefix split fired. Derive and log the real requirements, demonstrate the predicted grouping/placement, and verify the ordinary and speculative paths against the unchanged original references.

Retain the original Qwen14B failed development cases and a small Qwen8B control set. Recheck the known Llama boundary counterexample and one non-boundary control once after integration. Existing full-vector auditors and original reference records can be reused; do not rerun the old 24-input Llama panel or its 864 measurements.

### B570 / Vulkan

First apply the same extraction/planner approach to the original Qwen3-8B producer–consumer counterexamples:

| Input | Existing distinguishing result |
|---|---|
| `MATH500/test/prealgebra/1865.json` | P1+C1 and P4T+C1 preserve the same R; P1+PQ/QB fail, P4T+PQ/QB already pass |
| `MATH500/test/prealgebra/1804.json` | Same pattern |
| `GSM8K/train/1184` | P4T changes natural C1; both producer/consumer combinations contain divergences |

The first two require a repaired **P1+PQ/QB** path against the same original R. Switching to the already successful P4T cell is not a repair. The third tests whether the policy controls producer arithmetic/state as well as the consumer. Keep the exact original P1 construction, input IDs, cap, k and numerical reference when replaying these fixtures. The new rules must be actually enabled and their trigger state visible; the previous adapter only enabled layout.

The Qwen reference keeps its original all-GPU target/draft placement, 8 threads, F16 KV and k1 transaction contract; do not inherit Llama's GPU-target/CPU-draft admission choice. Use each retained fixture's recorded cap. The new integrated candidate's natural prefill policy may exploit its supported batching, but must be fixed for the model before confirmation and applied uniformly. It does not replace the required repair of the historical P1 cells, and it must not select P1/P4T from input identity or observed success.

If F32-activation preservation and prefix grouping do not resolve a retained counterexample, inspect the first relevant same-state/operand divergence and add the structural condition indicated by that evidence. Do not assume CUDA's Qwen placement mechanism applies to Vulkan. Use one focused factor reversal or same-state replay sufficient to distinguish the new condition; avoid restarting the entire Llama diagnostic program.

Recheck the known Llama boundary case and one non-boundary control after the common code changes. Broader Llama requalification is needed only if the native arithmetic domain actually changes.

## Freeze and small unseen confirmation

Freeze the shared implementation and each backend mapping after the structural probes and retained development cases are resolved. Then select natural inputs using the existing exposure indexes, source revisions and exact tokenizer. Do not rescan all historical archives when an authenticated complete exposure index already exists.

Default size:

- RTX: four unseen Qwen3-8B inputs and four unseen Qwen3-14B inputs.
- B570: eight unseen Qwen3-8B inputs.

Within each family, select both boundary-near and ordinary prompt lengths, and more than one source/domain where feasible. Prefer natural lengths that predict an early boundary crossing. Use no padding, truncation or hand-edited prompts to manufacture those cells. If the available pool lacks the desired natural lengths, use a documented nearby stratum before any output; the explicit native structural probes remain the primary boundary coverage. Keep the frozen selected panel even if a request ends before a predicted later boundary.

Run genuine greedy reference and M_PQ/M_QB/C_PQ/C_QB paths. Reuse the established observers/auditors. Compare complete endpoints and the committed full-vocabulary vectors against the unchanged numerical reference; compare matched PQ/QB transactions and conditional rejected rows when available. One representative heavy/off check per family/new instrumentation path is sufficient unless a concrete observer discrepancy requires more work. Formal timing supplies further uninstrumented endpoint checks.

For old native binaries with hard-coded input lists, an input/recording adapter may be added without changing the numerical reference's context settings, call sequence, libraries, model bytes or greedy rules. Preserve the original executable and first show the adapter reproduces its retained fixture vectors. State accurately that new inputs used an input adapter; do not claim the unchanged old executable accepted them. If the numerical path cannot be preserved, resolve that adapter issue rather than quietly redefining R.

A failed unseen input remains a reported counterexample. If it exposes a repairable new structural condition, retain the failed panel as development, revise the implementation, and select a new small confirmation panel after freezing. Do not keep changing inputs or opening new panels without a concrete new mechanism.

## Complete cost comparison

Use the successful new candidate's same runtime, placement, numerical assets and request contract for M_PQ/M_QB/C_PQ/C_QB. Retain the original numerical R as the baseline. The ordinary M arms execute natural greedy generation; their generated-token loop remains single-row. Their prefill capacity may be larger than R, so M/R is a whole-path comparison.

Default measurement budget is fixed **three sessions × eight inputs × five arms = 120 measurements per host**, with the usual immediate same-arm warmup. Fix the order before timing; rotate/randomize arm and input order using the existing harness. This small descriptive panel is not a population-power or perfect carryover-balance claim. If the existing reusable runner requires a different fixed session structure, document that choice before outputs and run it once.

Report these paired quantities separately:

- `M_QB/M_PQ`: ordinary-generation layout difference in the same candidate runtime.
- `C_QB/C_PQ`: speculative layout difference in the same candidate runtime.
- `M_QB/C_QB`: incremental value of drafting under QB.
- `M_QB/R` and `C_QB/R`: full-path cost relative to the original numerical reference.

Use all registered blocks and the same aggregation for all contrasts. Report each session and block reversals. There is no new timing-until-threshold rule: a neutral or unfavorable result completes the study as measured.

Service timing includes the chosen context lifecycle, prefill, generation/draft/verification, reconciliation, synchronization and teardown as applicable. Keep heavy observers, vector writes and probes outside formal timing. Report model loading and one-time reference/qualification preparation separately without pretending they are free. If phase attribution is needed, collect a small separate diagnostic subset with prefill/decode/verification/repair phase clocks; use it to explain work distribution, not to replace the clean primary timings or claim that the instrumented values are overhead-free.

## Completion and stopping

Successful completion requires actual shared native calls, observed structural triggers, retained-counterexample repair under the original references, the frozen small confirmation, and one complete cost panel. Submit a compact result PR with the source changes, reproducible entry commands, trigger table, confirmation table and cost table; reuse the existing evidence delivery format. Do not count archive size, request count or CPU checks as method novelty.

Stop optional experimentation once those questions are answered. Do not rerun timing for a better sign, expand to a third platform, add arbitrary models, or repeat old successful audits. If the remaining issue is a specific unsupported operator/state, report the smallest concrete counterexample and required implementation change. If resource/admission or missing original assets prevent execution, preserve the exact blocking evidence and finish the implementable work; do not substitute a new reference or quantization.

No manuscript merge, historical-result rewrite or arXiv/journal submission is part of these host tasks. The authoring PR integrates the source and later results separately.
