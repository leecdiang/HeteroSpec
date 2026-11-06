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

Implemented and exercised on the original RTX host:
- The native extractor/planner/executor in `native/resident_context.hpp`, with
  immutable per-call groups and owned requested output rows on one target KV.
- Separate rebuilt SIMPLE/LOCAL native workers and their original-R observer
  adapters, actual metadata/dispatch bindings, finite vector/KV/frontier checks,
  resource-bounded launch accounting and separate CUDA activity traces.
- A pre-Smol common-rule publication, followed by transfer to different native
  head mapping/dimensions. See `RESULTS.md` and the exact receipts for scope.

The inherited B570 source-work calculator and helper tests remain unchanged.
They supply neither RTX qualification nor B570 measurements. Raw metadata for
its old per-slot aggregation was not restored here, and no missing timer is
invented. This result does not execute or modify B570.

The commands below are inherited helper checks; actual GPU qualification is in
`host_evidence/`, never inferred from these tests. Reproduction is documented in
`REPRODUCE.md`.

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
