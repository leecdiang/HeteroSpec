# Terminal journal semantics review of PR183

Reviewed fixed head: `2b6f0efc47de3efd7d739042065409e8bc21d526`. The published `test_native.cpp`, `frozen-worker.cpp`, and `stage.py` were retrieved from GitHub at that commit and exactly matched the local reviewed bytes.

## Finding

This is a misleading/underspecified journal field, not an observed loss of output tokens or live KV caused by the field. The fixture writes `cycles[].pending = done ? null : pending`; the frozen and generated Windows workers likewise write `cycles[].pending_after`. Those expressions describe whether another loop iteration will consume pending. They do not describe whether the last emitted token is materialized in KV.

At initial, correction, and bonus termination, the final emitted token remains in the output IDs and in the local pending variable but has not been decoded into retained KV. At accepted-token termination, the final emitted token is already in retained KV; the local pending variable may still contain the old seed. Replacing the null with that raw variable would introduce a false record.

The complete existing records retain enough output/branch/frontier information to derive the unmaterialized token. Initial stop has no cycle record, so any explicit clarification must also provide final-request metadata. These records are not complete resumable checkpoints: fresh contexts are destroyed, resident contexts are reset for the next request, and retained frontier logits need separate treatment.

## Native reproduction

The pinned published CPU fixture was instrumented only with read-only target/draft observations, terminal assertions, and fresh scalar diagnostic replay. It added no target/draft decode, trim, acceptance, or parameter changes. All 75 old result records, excluding the additional evidence and low-level assertion count, remained exactly equal to the previously retained stress-Q8 results.

The 75 terminal cases comprised 18 initial stops, 15 corrections, 15 bonuses, and 27 accepted-token stops. The first 48 retain one emitted but unmaterialized token; the other 27 retain all emitted tokens in KV.

Examples use draft ubatch 2, prompt length 7, and the pinned synthetic stress-Q8 model:

- Initial cap 1: emitted `[73]`, target KV maximum position 6. Token 73 is unmaterialized at position 7. There is no cycle pending field.
- Forced rejection 0, cap 2: emitted `[73,117]`, terminal correction, keep 8, KV maximum 7, legacy pending null. Token 117 is unmaterialized at position 8.
- Forced all-accept, cap 5: emitted `[73,117,24,24,24]`, terminal bonus, keep 11, KV maximum 10, legacy pending null. Final token 24 is unmaterialized at position 11.
- Forced all-accept, cap 2: emitted `[73,117]`, terminal accepted, keep 9, KV maximum 8. No output token remains unmaterialized. The raw local pending variable is still 73, the old seed.

At a speculative cycle with `accepted=a`, the logits at verification row `a` predict from the retained frontier. All 75 selected frontier rows, using the prefill last row for initial stop, matched a fresh scalar replay at the same retained prefix. The default last-output row did not match that prefix in 36 cases: 21 accepted stops and 15 corrections. This does not change the completed endpoint, but rules out treating default last logits as a generic continuation checkpoint. The journal can identify the correct row; that alone does not preserve its lifetime after cleanup/reset.

## Minimal non-runtime correction

Prefer an additive, read-only interpretation sidecar and explicit schema documentation. Preserve old records and the frozen source. Keep legacy pending semantics as `next_iteration_only`, and derive:

- `B = materialized prefix length`, checked against the final KV position / cycle keep.
- `P = prompt length`, `O = emitted output count`.
- `unmaterialized_count = P + O - B`, required to be exactly 0 or 1.
- If the count is one, record the final emitted token and its position B. If zero, record an empty list.
- Record the frontier prediction source separately: the final verification row `accepted`, or the final prefill row for initial stop.
- Retain `recovery_status = UNPROVEN`. Do not automatically decode the terminal token, reset KV, repair state, or claim a resume feature.

Handle ordinary no-draft worker requests separately: those can have many emitted tokens with an empty cycle list. Therefore `cycles.empty()` does not universally imply initial stop. Validate source/schema, emitted length, branch, keep, and actual KV bounds where available. Reject inconsistent counts, unknown branches, wrong pending-token interpretations, and incomplete evidence rather than manufacturing a checkpoint.

## Scope

Cloud CPU only. Same synthetic model for target and draft, target physical ubatch 1 / output reservation 4. No user computer, Windows worker execution, GPU route, frozen deployment-R qualification, failure recovery, complete hidden-state equivalence, or performance claim. A fresh scalar context is independent of the observed context's KV but uses the same runtime implementation.

## Reproduction

```
python3 make_terminal_probe.py --fixture /path/to/PR183/test_native.cpp --output /tmp/fresh-probe
python3 run_native.py --fixture /tmp/fresh-probe/terminal_probe.cpp \
  --source /path/to/candidate-runtime --library-dir /path/to/cpu-build/bin \
  --model /path/to/pinned-stress-q8.gguf --output /tmp/fresh-terminal-run \
  --expected-exit 0 --expected-status PASS
```

All output directories must be fresh. Only the test executable is UBSan-instrumented by this runner, not its linked runtime libraries. Exact hashes and summary are in SUMMARY.json; the full terminal evidence is in NATIVE_TERMINAL_RESULT.json.
