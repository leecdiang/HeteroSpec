# M4 workload-conditioned preregistration

This directory freezes a separate code-workload hypothesis test. It does not
replace, reopen, or pool with the representative 24-prompt Spec-Bench result.

The HumanEval IDs were selected uniformly from the canonical 164-task ID
space before downloading or reading prompt contents. The primary test is
baseline versus fixed `k=2`. Confidence gating is secondary and cannot be used
to relabel a failed primary test as a successful confirmation.

Generated code is not executed in this throughput study. "Exact" means that
the baseline and speculative paths emit identical token IDs under greedy
decoding; it is not a HumanEval functional-correctness claim.
