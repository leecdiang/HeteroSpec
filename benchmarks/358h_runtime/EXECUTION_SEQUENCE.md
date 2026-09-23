# 358H Runtime Study — Deterministic Execution Sequence

This is the short operational companion to `WORK_HANDOFF.md`.

## Phase 0: local-only repair window

1. Checkout `runtime/358h-codesign-v0.1`.
2. Run `python -m compileall scripts/platform/358h_runtime`.
3. Run `probe_openvino_state.py` on CPU and NPU.
4. Run `runtime_state_tests.py` on CPU and NPU.
5. Repair only API/environment compatibility needed by the frozen model and explicit device paths.
6. Rerun steps 2–4 after every repair.
7. Commit the final R0 implementation. Do not collect R1 data before this commit.

R0 timings are invalid for performance claims.

## Phase 1: freeze source/environment

With a clean tracked worktree:

```powershell
python scripts/platform/358h_runtime/create_runtime_freeze.py `
  --r0-capability "$R/r0_capability.json" `
  --r0-state-tests "$R/r0_state_tests.json" `
  --output "$R/runtime_freeze_manifest.json"
```

After this succeeds, do not change HEAD, frozen runtime files, frozen packages, Python, model artifacts, or HumanEval through R2.

## Phase 2: derive R1 candidates automatically

```powershell
python scripts/platform/358h_runtime/plan_runtime_qualification.py `
  --r0-capability "$R/r0_capability.json" `
  --r0-state-tests "$R/r0_state_tests.json" `
  --output "$R/r1_plan.json"
```

Use **exactly** the path groups emitted in `r1_plan.json`. Do not manually add paths. Candidate planning consumes no timing.

For each non-empty group, run the R1 small gate in a separate process:

```powershell
python scripts/platform/358h_runtime/run_runtime_qualification.py `
  --stage small `
  --freeze-manifest "$R/runtime_freeze_manifest.json" `
  --paths <EXACT_PATH_LIST_FROM_ONE_R1_PLAN_GROUP> `
  --output-dir "$R/r1_small_<group>"
```

A non-zero return caused by an exactness failure does not erase surviving paths; preserve the summary and determine survivors solely from `qualification_summary.json`.

## Phase 3: R1 full exactness

For each group, pass only its small-gate `QUALIFIED` paths to a new full-gate process:

```powershell
python scripts/platform/358h_runtime/run_runtime_qualification.py `
  --stage full `
  --freeze-manifest "$R/runtime_freeze_manifest.json" `
  --paths <SMALL_GATE_QUALIFIED_PATHS_ONLY> `
  --output-dir "$R/r1_full_<group>"
```

The full gate is 90/90 token-ID equality. R1 timings remain diagnostic only.

## Phase 4: deterministic R2 registry

Feed every completed small/full summary pair to `freeze_runtime_registry.py` together with the frozen R0 artifacts.

The registry itself determines the minimal R2 condition set. It keeps only controls needed to identify a qualified intervention:

- `TARGET_UB1` always;
- for a qualified persistent device path: its same-frontend replay control, persistent path, and qualified legacy bridge if available;
- NPU UB2: qualified persistent UB1/UB2 pair first; otherwise predeclared legacy UB1/UB2 fallback; otherwise no UB2 timing condition.

No timing is read when producing this registry.

## Phase 5: R2 formal campaign

```powershell
python scripts/platform/358h_runtime/run_runtime_campaign.py `
  --registry "$R/runtime_qualification_registry.json" `
  --freeze-manifest "$R/runtime_freeze_manifest.json" `
  --output-dir "$R/r2_formal"
```

Do not alter conditions, affinity, k, workload, output cap, model artifacts, or order seed.

## Phase 6: deterministic analysis

```powershell
python scripts/platform/358h_runtime/analyze_runtime_campaign.py `
  --campaign-dir "$R/r2_formal" `
  --output-dir "$R/r2_analysis"
```

Review correctness before speed. Then classify separately:

1. complete system speedup vs `TARGET_UB1`;
2. state-reuse component effect vs same-frontend replay;
3. same-policy NPU UB1/UB2 target-verification effect, if promoted.

Only after this review should the manuscript be edited.
