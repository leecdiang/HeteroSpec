# B570: reference-compatible target parallelism and speculation economics

**Prospective design + tested CPU tools. Native integration and new GPU execution: NOT_RUN.**

Base: PR187 `b01040d3b303abfc31c5ce2dbcb100cac7490b27`.
This independent result-free branch does not alter PR188 or wait for RTX.

The question is not whether removing serialization alone can rescue speculation.
PR64 and PR82 already tested resident phase binding without ordinary-reference
profit. Reuse that mechanism, preserve the current target contract, and determine
whether useful target parallel work savings pay for the entire draft/lifecycle bill.

Read `PLAN.md`, `HISTORY.md`, `HOST_ADAPTER.md`, then `HOST_PROMPT.md`.

## Already implemented

- `costs.py`: reconstruct PR187 saved service/coarse windows from authenticated
  metrics; missing phase times remain null. Compute non-double-counted diagnostic
  partitions and the target-savings/draft/other cost identity.
- `stage_costs.py` + `native/cost_clock.hpp`: generate frontend-only mode0,
  host-envelope and synchronized-diagnostic builds. Cover BOTH observer wrappers
  and direct M prompt-decode begin/end. Preserve online transfer checks; time its
  three exports, import, context creation/destruction and comparisons separately.
- `stage_resident_core.py`: private source overlay reusing PR64's
  synchronize / phase-ubatch / scheduler-reserve mechanism. It does NOT copy
  PR64's enlarged output reservation or silently change numerical R.
- `native/phase_binding.hpp`: identity/position guard around a host-bound phase
  mutation. Not a KV-byte proof, graph-cache certificate or production fallback.
- `design.py`, `analyze.py`: outcome-free root selection, balanced schedules,
  explicit development decisions, complete-panel root-cluster comparisons.

## Run local helper checks

```sh
python -m unittest discover -s tests -v
python -O -m unittest discover -s tests -v
c++ -std=c++17 -Wall -Wextra -Werror -pedantic -fsanitize=undefined \
  -DB570_COST_MODE=2 tests/test_native.cpp -o /tmp/b570-econ-tests
/tmp/b570-econ-tests
```

These tests are synthetic/standalone only. Native Windows builds, original-R
bridges, phase-binding integration, Vulkan graph/dispatch observations and timing
must be completed on the original host. Do not stop at helper tests.

Use the existing PR187 supervisor, request reservations, full-vector/state and
free/forced reference tools. Adapt paths and reviewed ABI normally; do not start
another universal auditing framework. Package only the needed evidence once.
