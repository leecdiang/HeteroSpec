# S0 host freeze, revision 0

Parent PR112: 7864716787fabb17cb613ed7125c180736c133ef. Old PR111 source:
9fafc4ba49119f1c52e1606d295bd0b9a55a06d1; PR109 assets:
039a24bf61374042e0dc9f3a3619ea40b218a5ad. Read-only reuse, no old-run restart.

The exact 432 cells come from plan.cpu_cells, six actual GGML computations per
cell: MQ/PQ/QB4/QH_C/QH_D/REPEAT4. q1/q2 development (216), followed by a code
lock commit, then q3/q4 fixture outputs (216). q3/q4 were already considered in
the delivered toy tests; this is not unseen geometry or natural-input evidence.
Maximum 2592 CPU graph computations, 14400 child seconds, 8GiB RSS, 2GiB output,
one heavy job. No numerical retry or hidden warmup; retain first failure.

Inputs use oracle.fixture exactly: structured/dyadic and causal/single/holes.
F32 Q and F32 masks; K/V converted to F16 by Python's explicit storage format.
Both Q storage conditions use a 32-byte legal base offset. Scale is the stored
F32 representation of 1/sqrt(128), used identically by FP64 oracle and GGML.
No change to dtype, backend arithmetic, model, sampler or shader.

The independent PR111 FP64 scalar oracle is adapted only for scale; logical
query/head arrays do not use candidate helpers. Exact integer source addresses,
actual buffer bounds, pack/repeat identity, GQA, masks and output restoration
are checked. QK structured one-hot and structured single-key softmax/AV/final
are exact controls. General abs/relative/ULP distributions are retained without
a new tolerance. All actual stage/final vectors are saved for independent
full-vector PQ/QH comparisons; inputs are hashed before/after computation.

Actual modules recorded before/after; only ggml-base plus explicitly loaded
ggml-cpu. The descriptor mock is compiled separately and never enters the
real harness include paths. No S0 GPU module, device/capability query, model
process/request, GPU forward/operator, probe or warmup. S1 requires its own
concrete F0 and separate author approval before even its charged census.
