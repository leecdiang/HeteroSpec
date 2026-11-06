# Resident reference-derived phase plans — RTX results

Original-host native execution is complete. Read [RESULTS.md](RESULTS.md) for the
full six-arm results, qualification scope, setup/warmup costs and retained
failures; [REPRODUCE.md](REPRODUCE.md) describes the authenticated raw evidence.
`PLAN.md` and `HOST_PROMPT.md` remain the original prospective PR188 protocol.

`native/resident_context.hpp` is the small native interface: obtain real supported
cache/graph/backend requirements, form immutable groups, execute on the same
target/KV, and own only the originally requested output rows. SIMPLE uses maximal
compatible whole-graph groups and loop4; LOCAL uses local prefix attention and
wide packed projection. Both preserve masks, frontier, pending and stopping
semantics. The adapter and each native core are actually built and exercised on
the RTX GPU against an independent unchanged original reference.

Final candidate bytes pass all48 boundary/width cells and all six M/D1/D4
qualification arms on Qwen and Smol. The common rule was published before Smol
outputs; the real GQA/head128 and MHA/head64 structures use identical candidate
executables. Full requested vectors and active KV/frontiers are observed in
finite development qualification at declared boundaries. Clean confirmation
checks endpoints and producer/pending/termination traces, without full-KV dumps
or online numerical reference replay. No helper or readiness field substitutes
for the saved GPU evidence.

The new outcome-unexposed panel completes576 measurements and576 immediate
warmups, eight roots/family and six Williams sessions. LOCAL-D4/SIMPLE-D4 total
service is0.991096 on Qwen (adjusted interval crosses1) and0.961556 on Smol.
Smol LOCAL-M remains faster than LOCAL-D4. All six controls,15 contrasts,
regressions, failed reservations, reference/teacher work and complete observed
costs remain available. No extra sessions or new AUTO are fitted. RTX model work
is stopped; no B570/arXiv change, rental or merge is performed.

The inherited B570 source/cost scan and CPU/C++ helpers are retained unchanged.
They do not provide new B570 measurements or RTX GPU qualification. Same-context
execution and inherited loop4/packed kernels alone are not claimed novel; see
[RELATED_WORK.md](RELATED_WORK.md) for the narrower composition claim and limits.
