# Decisive reference-compatible experiments (2026-11-05)

**Original-host RTX execution:** see [RTX_RESULTS.md](RTX_RESULTS.md) and `host_evidence/` for native builds, independent GPU state qualifications, retained failures, costs and panel disposition. The design/tooling description below records the original PR184 boundary; it is not the current execution status.

Read `protocols/DECISION.md`, `protocols/COMMON.md`, then the platform plan. These are independent experiments on copies of frozen sources, not a merge of PR179–183. Do not install the always-veto diagnostic path into a performance executable. Do not modify the submitted arXiv replacement or historical R.

## What is implemented here

| File | Executable work |
|---|---|
| `stage_sources.py` | Export the pinned PR180 baseline stager/dependencies; materialize graph_tiles/loop4/packed. Create RTX draft UB1/2/4 derivatives and heavy-only state observers. Create B570 C1U1/C4U1/C4U2/C4U4 derivatives, separating caller geometry from physical microbatch. |
| `native/draft_prefill.hpp` | Bounded scalar/q4 caller schedules, with original final-output policy handled by the inherited prefill routine. |
| `native/target_capture.hpp` | Copy an already requested frontier row and native sequence bytes; no extra logits masks/reserves or reference arithmetic. |
| `native/replay_path.hpp` | Independent forced continuation using explicitly supplied historical prompt caller lengths **and output flags**, on a caller-owned historical context. |
| `active_kv.py` | Profile-bound dense seq0/F16 active KV extraction including transposed V. Real trained-model/writer profiles are NOT preapproved. |
| `trace.py`, `qualify.py` | Reconstruct greedy endpoints/committed prefixes independently; compare every captured target vector, active KV and retained-prefix frontier against separate reference captures. |
| `normalize.py`, `merge_references.py` | Normalize existing original-host captures, construct token-only independent reference jobs, and merge actual reference paths with duplicate-prefix stability checks. |
| `design.py` | Outcome-free root selection and counterbalanced complete schedules. |
| `runner.py` | Durable work reservation, logical-session adapter invocation, owned-process timeout cleanup and retained failures. |
| `readiness.py` | Independent per-lane gates, without a cross-platform waiting barrier. |
| `analyze.py` | Full-panel paired estimates, all fixed contrasts, root-cluster uncertainty, total-service and geometric views. |

These tools check consistency and recorded bytes. A hash, a native-origin flag or a matching descriptor is not remote attestation or a proof of numerical equivalence.

## Original design boundary

Use the existing original-host runners, not a new speculative algorithm. Bind actual paths/compiler/libraries; compile the generated derivatives; connect native records to the capture/session formats; verify the actual old serializer/model profile; build separate autonomous and forced-reference job entry points; implement observed module/resource receipts and uninstrumented timing. `HOST_ADAPTER.md` is the explicit remaining boundary. The authoring environment did **not** compile these Windows workers or run restored trained models.

This is substantive staging/comparison/analysis code, not a claim that a universal native driver has already been completed. A local build or adapter issue is work to solve during development, not a reason to return after running only Python tests.

## Local CPU checks

```sh
cd benchmarks/tpds_decisive_v1
python -m unittest discover -s tests -v
python -O -m unittest discover -s tests -v
g++ -std=c++17 -O2 -Wall -Wextra -pedantic tests/test_native_helpers.cpp -o /tmp/tpds-helpers
/tmp/tpds-helpers
```

Windows may use the available C++17 compiler rather than copying the command literally. These are synthetic/data-structure tests, not GPU or trained-model evidence.

## Pinned source staging (on an authorized existing checkout)

```sh
# The commits must already exist locally; otherwise fetch their PR refs first.
python stage_sources.py rtx-loop4 --repo /path/to/HeteroSpec \
  --candidate /verified/PR171/source-kit/candidate --out /fresh/loop-arms
python stage_sources.py rtx-draft --repo /path/to/HeteroSpec --out /fresh/draft-arms
python stage_sources.py b570-draft --worker /verified/PR165/generated/boundary.cpp \
  --expected-sha256 SHA_FROM_VERIFIED_HISTORICAL_SOURCE_MANIFEST --out /fresh/vulkan-draft-arms
```

The last SHA is a host-resolved source identity, not permission to self-approve an arbitrary file. The supplied B570 source must include the qualified PR165 adaptations; obtain it from the authenticated native source kit/old build, not the unadapted PR152 worker.

## Publication

The enclosing delivery includes `publish_prs.py` and separate PR bodies. It uses an existing authenticated `gh` session on the host, a fresh git worktree, exact base commits, a non-force push and `gh pr create --draft`. It does not run GPU work. No PR is claimed created until that command returns and reads back the actual URL/head.
