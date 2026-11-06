# Resident reference-derived phase-plan experiment

**Original-host execution:** `host.py` and `native/resident_context.hpp` now bind
the resident executor to compiled llama/CUDA workers. `host_evidence/` contains
actual Qwen original-R/observer bridges, boundary and six-arm qualifications,
CUDA traces, retained failures and costs. `SHARED_RULE_FREEZE.json` records the
exact candidate bytes before the Smol transfer. The design description below
records the original PR188 authoring boundary; it is not a GPU completion claim.

Read PLAN.md, B570_COST_SCAN.md, and HOST_PROMPT.md. This is an additive package
based on PR186. The old D failure and the completed operator panel stay unchanged.

The positive goal is a small, reusable native execution plan across phases and
model structures, keeping fixed R without copying full KV to enforce each phase
transition. It is not a new AUTO or generic all-reject guard framework.

Implemented in this delivery:
- C++17 typed dense-prefix model, actual-requirement contiguous planner, structural
  graph identity, original-output-mask-preserving byte collector and grouped
  execution interface with poisoned-context failure handling.
- Read-only B570 source-work/cost calculator plus archived-slot metric scanner.
- Python and C++ tests, including dynamic extents and failure/row ownership.

Not implemented/verified here:
- Original-host native metadata/dispatch extraction and binding of the callback
  executor to llama, the same-R single-context candidate, or any new GPU result.
  The executor must build these using the existing PR186/PR171 code. Helper test
  success is not GPU qualification. Do not treat a type/shape key as a proof.
- Full B570 per-slot phase aggregation: the private release's raw metadata was
  not restored in this authoring workspace. Per-operation migration timers do
  not exist in the reviewed source. The scan does not invent their values.

CPU checks:
```
python -m unittest discover -s tests -v
python -O -m unittest discover -s tests -v
c++ -std=c++17 -O2 -Wall -Wextra -Werror -fsanitize=undefined tests/test_plan.cpp -o test-plan
./test-plan
python analysis/b570_online_scan.py --output /fresh/scan.json
```

Do not install a new numerical library over an old reference. Source-staged
candidates and independent original references must be separately identified.
Offline observation and online production work have different clocks. No merge,
arXiv edit, model download or paid GPU rental is authorized by this package.
