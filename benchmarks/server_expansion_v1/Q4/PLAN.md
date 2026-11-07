# Q4 — extend a real arithmetic domain, not a filename whitelist

## Question and assets

Can reference-derived phase rules preserve an independently fixed mixed-Q4
quantized deployment while retaining useful parallelism? This tests numerical
domain breadth, not whether Q4 reproduces Q8 logits or has equivalent model quality.

Fixed target: official Qwen3-8B-Q4_K_M.gguf at
Qwen/Qwen3-8B-GGUF revision6a569868d07d3bd59e8b97fb001bf8c0b254bb20,
5,027,783,488 bytes; SHA256
d98cdcbd03e17ce47681435b5150e34c1417f50b5c0019dd560e4882c5745785.
Keep existing Qwen3-0.6B Q8 draft when speculation is tested. Do not also quantize
or change the draft and attribute the resulting trajectory to target batching.

## Implementation sequence

1. Run shared/gguf_inventory.py on the exact file. Save every actual tensor's
   name,type,shape and mixed-type coverage. Q4_K_M is not a promise that every
   tensor is Q4_K. Metadata is not kernel execution evidence.
2. Freeze independent pristine Linux R_Q4_C1024 before candidate outputs, with
   declared producer, requested rows, F16KV/noFA and greedy cap. Never change R
   after seeing a troublesome candidate. The Q8 deployment remains immutable.
3. Recover the Q8 rule/dispatch requirements from the qualified Linux successor.
   Replay real operands for observed projection/FFN/head types at q1/4/8/32 and
   tails. Own-path reproduction comes before crossed interventions. Keep weights,
   activation input arithmetic, scale handling, accumulation and output ownership
   explicit. Include every actually encountered type or report support holes.
4. Implement **typed** loop/small-reduction and independent-group packing recipes
   only where justified. Reuse existing backend kernels when suitable. Do not
   widen a Q8 guard, reinterpret storage, dequantize to a different operation, or
   silently use CPU/fully serial fallback and call it unchanged parallelism.
   A fallback can be a valid supported route only if declared and fully costed;
   it is not evidence for the unsupported fast recipe.
5. Give whole/local paths exactly the same validated recipe set and graph reuse.
   Qualify producer/full requested vectors/active state/frontier/termination and
   counterexamples on a small exposed development set. Freeze the shared rule
   implementation before new natural roots. `recipe_inventory.py` helps enumerate
   missing recipes but never certifies numerical behavior.

## Natural comparison is capability-driven

Primary supported result can be target-only: four real W_L4/W_P/L_L4/L_P controls,
16 roots/four sessions (256 tests +32 primers). This is enough to test a target
method even if drafting is uneconomic. If both D4 mappings are already qualified
and have a concrete application question, prospectively choose the six-arm panel
instead (384 tests +48 primers); do not run both to multiply observations.

All contrasts are within the same fixed Q4 deployment. Same inputs across Q8/Q4
support paired descriptive comparisons, not byte-equivalence or a new independent
sample count. Q4-vs-Q8 model-quality assessment is outside this paper's experiment.
Preserve known Qwen tokenization/template, cap and all distinct lawful M baselines.
Do not select tensors/roots based on success or speed. Inapplicable mappings remain
visible; normal engineering or mechanism repair continues before a new freeze.

## Review outcome

A real typed rule extension plus full-model transfer is useful. Merely loading a
Q4 model, enumerating its types, compiling code or matching final text is not the
planned contribution. Packing may lose to a loop/control; record that and choose
appropriate implementation rather than collecting more rounds. Initial envelope
2048 requests/8M rows, including references/warmups/failed attempts. No MMA, router,
new model family or full quantization sweep. Preserve PR196 and deliver a separate
results PR with source-level recipes, all controls and complete service costs.
