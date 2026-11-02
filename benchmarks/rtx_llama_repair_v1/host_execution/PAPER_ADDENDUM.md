# Llama repair evidence addendum

This is a separate experimental addendum, not an edit to the manuscript. Final confirmation and delivery receipts are reported in RESULTS.md and the accompanying machine-readable records.

## Mechanism and scope

The immutable PR151 records contain 54 diagnostic requests and 5,916 complete decision vectors. The observed CodeContests/valid/108 output mismatch at index 81 maps to cycle 21, row 2. The earliest saved common-prefix vector difference occurs at output index 29, cycle 8, row 0, where the four consumed positions cross a physical KV padding boundary.

Same-state q1/q4 consumers, both execution orders, their own-path replay and observer controls locate an earlier difference. Captured valid Q/K/V and probability values agree, including a zero masked probability suffix. Repeated native operator replay with crossed physical extents reproduces the captured C_PQ attention-output difference: changing the reduction extent from 768 to 1,024 changes floating-point results even with identical visible values. This is evidence about the captured operation and supported execution path, not a proof about every attention kernel or model. The later cycle-21 same-state consumers already agree on the wrong original-reference decision because the state difference has propagated.

The structural repair groups adjacent rows by their scalar-equivalent physical KV prefix extent, preserves actual cache and padding semantics, materializes shortened masks when needed, and binds graph reuse to the extent vector. It applies under explicit dense contiguous single-stream causal non-flash guards. It contains no input ID, answer, output-position or margin exception. Ablating the intervention restores both historical C-arm failures. The separate Qwen head-normalization policy remains part of the combined candidate; it is not asserted to cause the Llama failure.

## Interpretation of validation and costs

Development inputs and Qwen regression inputs are previously exposed and do not establish unseen-input generalization. Unseen confirmation uses the registered balanced 24-input panel, immutable old-R executions, complete endpoint and available state/vector checks. A finite pass supports only the measured models, numerical assets, hardware and execution contract.

The prospective cost comparison retains all six Williams sessions and both warmups and measured requests. It uses arithmetic dual-PQ means within blocks and geometric means of paired ratios. Practical layout benefit requires improvement beyond both 2% and the largest symmetric input-aggregate A/A imbalance, with all six sessions favorable. Correctness and practical performance are distinct conclusions; an unfavorable result is retained without extending timing to change its sign.

All failed observers, candidate builds, partial executions and original-worker schema corrections remain in the cumulative ledger and source archive. Same-host independent reconstruction and fresh remote download/member checks are reproducibility and delivery checks, not third-party scientific replication. No population confidence interval is inferred by treating individual requests as independent experimental units.
