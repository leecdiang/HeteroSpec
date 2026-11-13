# Source review and implementation limits

This is a new repair branch, not a change to PR156's closed result. The prior original R remains the executable oracle. The code restores PR156's adapter via Git at its exact commit, checks the archived worker SHA256 (`e1c1d779…`), and then applies count-checked edits. It never guesses a source anchor or edits an old build in place.

## Actual checks performed during authoring

- Reconstructed the original PR151 worker byte-for-byte: Git blob `b38275fb41c9baa732adc02e40f6c9529b1b2fa6`.
- Applied the PR155 adapter and verified the archived PR156 worker SHA256 `e1c1d77994ae1ec9b403f7699013ce17f00344621f85cbceb0b917abc256a533`.
- Applied the new worker transformation locally against that exact text. Compiled Python and ran the unit suite.
- Compiled `reference_rows.h` against an explicitly synthetic C++ graph API and checked row order, family/reference/q1 bypasses, descriptor rejection and caller precision propagation. This is not a real ggml kernel or CUDA compile.
- Read the pinned llama-context API and backend declarations. `llama_context::get_sched()` exists in the pinned core. The native build checks its actual authenticated extraction again.

## Review findings fixed before delivery

The original weight-to-QK and buffer-owner-to-QK interpretations are not reused. The observer queries scheduler assignment and reports buffer ownership separately. Post-compute callbacks return true to continue; diagnostic tensor reads are never timed samples. Captured outputs have explicit logical-prefix IDs, while row alignment still requires a source review.

A row-lowered projection returns a concat graph instead of a MUL_MAT node. Callers may subsequently set accumulation precision, so the helper forwards that setting to the actual leaf MUL_MATs; silently applying the old setter to a concat node would be wrong. Existing numerical libraries and R/draft paths remain unchanged, but the rebuilt R must still match the old executable in actual qualification.

A restored sequence state does not supply the initial sampler decision by itself. The producer's full initial logits are copied separately and sampled once. Optional checkpoint records include pending ownership and actual consumed IDs. RSEED's prefill, state/logit transfer and readback all remain within the request clock. SELF restore shams precede interpretation of producer crossings.

Initial EOG is retained as an input outcome. It cannot be counted as observed consumer multiquery execution; the auditor distinguishes seed-only execution and requires a real speculative verification witness elsewhere in the panel.

Candidate sealing rereads complete raw records instead of trusting a detached PASS JSON. Development and confirmation use different gates. Code changes produce new epochs but share the request ledger. A confirmation failure exposes the panel and blocks timing; it is not permission to silently reuse the same held-out set after tuning.

## Still native-host work

The entire worker, real core patch, state import format, numerical-library loading, scheduler callbacks and actual model outputs have **not** been executed in this authoring container. The archive's exact projection builder may require a small source-anchor adaptation after inspection. The supplied row families cover dense Qwen projections only and do not repair normalization, nonlinearities, fused attention or arbitrary model architectures by theorem.

A selected post-compute tensor may be a strided or aliased view. Only its captured output bytes at that event are described; late source-operand snapshots are not used. The strided comparator supports F32/F16 only and refuses inferred token axes. For a true operator causality claim, capture operands before mutation, validate own-path replay, and make a controlled intervention. Those additional replay adapters remain the host agent's responsibility if needed.

Serialization byte equality is a deliberately strong initial check. If harmless serialized metadata prevents it, inspect the format and implement a source-reviewed effective-state comparison with native shams and original-R checks; do not simply bypass the gate. No fixed-input performance success or universal determinism claim is made here.

## Primary source pointers

- HeteroSpec PR156: https://github.com/leecdiang/HeteroSpec/pull/156
- Original worker/build: `29511ed91eb9f3d9773cfdda53e3554b0f4ad08b:scripts/experiments/rtx_scope_transfer_v1/`
- Exact model core: https://github.com/ggml-org/llama.cpp/blob/0cae43063cf15170e91a2ff4d034da0ecef4a1b2/src/llama-context.h
- Backend API: https://github.com/ggml-org/llama.cpp/blob/0cae43063cf15170e91a2ff4d034da0ecef4a1b2/ggml/include/ggml-backend.h

All reviews here are source/test passes by the same assistant, not independent subagents, native replication or formal verification.
