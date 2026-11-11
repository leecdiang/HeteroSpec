# RTX: strongest operator control, then ordinary wide draft

## Scientific bases (do not silently combine them)

- Working host/result branch: PR177, `610fd3a364bec6e8a3881ef666bedacd2035679a`.
- Operator implementation: PR171 `371223b696bb805030c29f04e39eb17b57fb2ebb` and its original oracle/source kit. Strong-control stager: PR180 `7ac1b6bd91a69fe3a27819c81978c4a78fac5cbd`.
- Draft-only intervention: PR151 `29511ed91eb9f3d9773cfdda53e3554b0f4ad08b` historical library and context, with staged derivatives. PR183 is source/protocol background, not a replacement reference.

## Lane O: packing versus a real backend loop (highest priority)

Use the three source-staged variants from the same PR171 candidate: graph_tiles, backend_loop4, packed. Original R stays a fourth, separate **numerical oracle**, not a mandatory timing competitor. Retain native-fast only as an ineligible compatibility/cost reference if already measured; do not use it to qualify a method.

Start with saved real operands (Qwen3-8B and already available .6B) across Q/K/V/O, gate/up/down and vocabulary projection. Development widths: q1/4 controls, q5/7/8/9/16/31/32. Frozen matrix helper also supplies physical prefixes1/255/256/257/511 for selected whole-model tail/boundary probes; do not blindly run the entire operator×prefix×model Cartesian product as requests.

Check F32 activation bytes, original quantized intermediate bytes where accessible, each bounded MMVQ specialization, tails, output and continuation. Backend loop quantizes wide input once: this is a hypothesis to qualify, not an assumed equality. Obtain actual selected-kernel traces and clean timings separately. Failed numerical qualification is investigated with actual operands, not dismissed as a competitor being unsupported by definition.

Once numerically qualified, collect operator execution, quantization, launches, concat/copy, scheduling and synchronization. Runtime event sums are diagnostics, not additive wall time. Keep existing graph execution policies equal across the compared arms. The C++ exception/fallback path is not a new timing mode.

**Natural primary panel:** twelve fresh code/math input roots, six paired sessions, three arms =216 measurements +216 immediate warmups. Use PR171's C1536, all-GPU Qwen3-8B plus existing .6B draft, k3, cap128, resident-reset service. Keeping k3 unchanged isolates projection implementation; no packing gain is attributed to a four-row verification that does not enter the wider packing path. Use exactly the same caller/attention scope in all arms (QB as the direct old/new control). Equally optimized WB-rechunk remains available and its prior natural tie/win stays in the paper; do not add a fresh QB/WB rescue panel.

If matching the original C1536 service cannot be reconstructed, finish the operator mechanism/qualification first. A different target-only/C4096 experiment must be separately frozen and labeled, never substituted into the old 4% estimate.

**Paper decision:** packed must be compared with loop4, not only tiles. A tie/loss can close this lane and narrow the packing claim. Do not tune a new kernel on the held-out panel or append extra sessions to obtain significance.

## Lane D: T-compatible ordinary draft UB1/2/4

This is independent of Lane O. Do not wait for a new packing result to transplant numerical libraries into the old reference.

Use original PR151 Qwen3-8B/.6B C1024, original target scope (QB), k3, greedy cap128, NATIVE whole-prompt producer and resident-reset history. Four arms: equally optimized M_QB, D1 unchanged physical draft UB1, D2, D4. Draft output reserve remains1. Its prefill caller is unchanged (one whole prompt); subsequent DRAFT_SYNC and PROPOSE callers remain singleton. Actual proposals and target histories may change under T.

Run the minimal old-R/observer and trained-model forced-prefix bridge first. Do not widen old-R output reserve to make a four-output observer easier. Use the existing reserve1 scalar read path for forced reference and the candidate's already requested k+1 rows.

Four exposed development roots are enough to discover obvious capacity/compatibility or cost failure. If qualified, twelve new roots ×four arms ×four paired sessions =192 measurements +192 warmups. Report all arms, prefill actual speedup, complete request cost, acceptance/verify work and warmup/setup/qualification costs separately. Compare both against M and against D1; Qwen's pre-existing draft advantage is not a new improvement.

Llama is a **secondary, conditional** replication using its own prior fresh-context/k3 reference. It may begin only after Qwen has a surviving measured opportunity and its existing assets/admission fit; freeze a separate twelve-root panel. No cross-family pooling. Smol is a small negative-control/cost-screen option, not required to rescue the result; the unrecovered report's hypothetical speedup budget is not an experimental success gate.

## Exit and delivery

Complete every viable lane without waiting for B570. If a required original reference cannot be recovered or an arm remains numerically incompatible after local diagnosis, deliver a scoped negative/blocked result and the other lane's evidence. No universal transaction framework, MMA kernel, new GPU or paid rental in this PR. Preserve PR174/177 negative outcomes and publish a result PR, not an automatically merged manuscript change.
