# B570 native execution checkpoint

This is an unfinished research checkpoint for independent result PR163, based on PR161. The original Vulkan reference remains `oracle-01`; RTX PR160 has not been modified. No confirmation performance claim is available yet.

The original 54 Llama requests and 5916 full-vocabulary vectors were recovered and independently audited. The old B570 Q6 and Qwen evidence is retained separately. The same target/draft Q8 weights were admitted at target GPU / draft CPU placement after the all-GPU profile failed its pre-forward memory reserve. Both roles were admitted before the 36-request natural baseline.

Actual B570 state, cycle, scheduler and dispatch evidence identifies two mechanisms:

1. The first layer Q8 projection uses F32 activations for q1 but Q8_1 activation quantization for q4. Fixed real operands reproduce all 15 original Q/K/V paths; a factor intervention and the explicit F32 structural policy each reproduce the scalar projection vectors. This difference precedes RoPE.
2. After that repair, all three development endpoints agree, but the long input still differs in 99 committed full vectors beginning at output29. At actual cycle8/base765, q1 uses physical keys768 for its first three rows and q4 uses1024. Visible V, QK and probability prefixes are bitwise equal. Eleven native AV own-path/intervention calls establish that exchanging the physical reduction extent exchanges the native results. On Vulkan this changes physical contiguity and the actual nc/contiguous shader selection; an unchanged-pipeline loop-length cause is not asserted.

Five repaired same-state/probe controls preserve the complete natural trajectory. Sixteen real attention-chain replays cover q1/2/3/4, PQ/QB and keys768/1024, with 64 independently reconstructed stage comparisons. The original and Q8-repair libraries each pass all12 historical Qwen requests using the unchanged original auditor; the repair regression covers914 saved vectors.

The combined candidate adds maximal adjacent equal-prefix groups, with graph-reuse invalidation when physical prefix extents change. Its two policies are independently switchable for ablation. Native guard fixtures compile the actual patched KV method, including rejection of noncontiguous, sparse, multi-stream and sliding-window states. Existing CPU tests:59 passed. Full combined development, factor ablations and final-library old-path regression remain in progress.

All failed admissions, failed builds, original references, exposure records and cumulative ledger entries remain retained under `I:/HeteroSpec/b570-llama-20261102`. The natural candidate pool has been tokenized with the exact historical template and original GGUF vocabulary without creating contexts or running forwards. No unseen panel has been selected. Cross-platform exposure review, candidate freeze, unseen qualification, complete timing/cost, raw publication and fresh remote download verification are still required.
