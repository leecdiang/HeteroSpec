# Bounded follow-up: query-local attention constraint

Freeze before prototype outcomes. This is a hypothesis motivated by the completed native state/current-call crossing, not a unique-operation attribution. /15 decisions follow the current call under both donors; /25 changes only for the N1 donor/current-UB1 combination. All tested donors have identical prompt K/V but different generated-prefix K/V. Logical K0/V0 remain equal in these pairs; later cache tensors differ. This makes the attention/cache subgraph a reasonable narrow candidate while leaving other explanations open.

Candidate: in the private Qwen3 non-flash graph only, split two query columns into one-query attention subgraphs (QK, softmax, weighted V) and concatenate their outputs. Keep projection/FFN/output matrix operations and caller token grouping batched. Apply the same fixed constraint to both prefill and continuation; no task ID, future answer, margin threshold, or known divergence index controls it. No new CUDA kernel, model or dependency. This is an engineering candidate, not established novelty over batch-invariant inference/LLM-42.

First cap8 fresh complete native trajectories: four original tasks /15,/25,/18,/31, each with original global-UB1 target-only reference and candidate native draft k2/global-UB2. Reuse original prompts, FA off, ctx4096, threads24, greedy seed123, inclusive EOG/cap128. The candidate must match the ORIGINAL reference; do not change the reference to match the patch. Record every mismatch. One repetition is an exposed qualification probe, not performance or holdout evidence.

If all four qualify, specify a separate repeat-stability and matched-cost gate before any speed claim. If any fails, record the failed constrained subgraph recipe; do not broaden to the deployment benchmark or report its timings as qualified speedup. Neither failure nor success uniquely proves that attention causes every numerical difference.

Preserve both previously qualified frontends before modifying the private generated graph. Inference freezes, exact modified-source hashes and unchanged CUDA hash remain separate for the original causal matrix and this prototype.
