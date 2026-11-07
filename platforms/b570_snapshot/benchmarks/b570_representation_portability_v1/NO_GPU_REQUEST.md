# No new GPU request

Decision: **CLOSE_B570_PORT_WITH_REUSABLE_FINDINGS**.

The frozen `ggml_backend_vk_device_supports_op` rejects MUL_MAT when the two
sources have different `ne[3]` (ggml-vulkan.cpp:18976, SHA256 in
SOURCE_BINDINGS.json). Every admitted original q2 QB graph has K/V batch=1
and query/probability batch=2. Both QK and AV therefore fail that predicate,
independently of K=128/256 and of the two reviewed Q storage conditions.
This is a backend capability restriction, not a mathematical semantic bug or
evidence that hardware cannot implement the broadcast.

Consequently there are no four q2 original-QB fixtures in this reviewed family
that meet the premise of a same-backend MQ/PQ/QB GPU numerical comparison.
A 24-start run could merely encounter CPU fallback or reject a candidate;
neither outcome is a GPU numerical counterexample. It would not establish the
missing same-input GPU comparison. This follow-up supplies no semantic fix,
so there is no QB_FIXED arm and no 32-start proposal. Repeating full model
suffixes would leave H2/H4 entangled. No new GPU authorization is requested.

Do not bypass supports_op, repeat/copy K/V across batch, change precision or
construct a second optimization candidate under this plan. Such work changes
backend implementation/materialization costs and requires a separate question,
source review, frozen operands, budget and author approval.

If that prerequisite is independently addressed later, a new proposal would
need actual per-op backend assignment, input-before/after hashes, every output
dimension, finite execution lists and repeatability. Synthetic inputs remain
synthetic; they cannot replace missing native operand/state snapshots. No
operator result can retroqualify the original P1 NO-GO. The role-specific
monitor checker here is preparatory only; its example jitter/loss limits have
not been approved as an execution F0.
