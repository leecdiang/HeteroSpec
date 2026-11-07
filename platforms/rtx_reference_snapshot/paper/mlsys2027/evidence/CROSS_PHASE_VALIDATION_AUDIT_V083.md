# Cross-Phase Validation Semantics — Phase 6A

## Problem

Phase 4 required Related Work to remain unchanged relative to its input commit. Phase 5 later explicitly authorized Related Work revision. Applying that Phase-4 scope assertion to Phase-5 HEAD produces a false failure: the check answers whether Phase 4 stayed within its edit perimeter, not whether the current science regressed.

## Resolution

`VALIDATOR_SCOPE_CLASSIFICATION_V083.md` separates checkpoint-local scope checks from continuing scientific invariants. The original Phase-4 validator remains unchanged. `validate_current_scientific_invariants_v083.py` checks the live scientific claims; `validate_prior_phases_v083.py` authenticates the historical Phase-4 PASS receipt and runs current validators for the other phases and Figure 3.

## Phase-4 checkpoint verification

Input `3b6d7eee8888f96c71835b0b15eb1c7cb074a038` and output `d3ae7067fc5ff285d87238f8c48a7104ebfb349d` exist locally and are consecutive in this revision chain. A temporary detached worktree at the output commit ran the original committed `validate_claim_calibration_v083.py` (SHA-256 `e35019f84850a4807903d5c66f295f2bbb77b4d9e712c8fa7967ced333f0affc`) with the archived local Phase-4 preview (SHA-256 `5adb32808883717a8f59a339d8268c6de2ca45b49d0d268d054ed2c89e6b5f68`). Result: **PASS**, including Related Work unchanged. The worktree was removed.

## Phase-5 authorized evolution

Git diff confirms Related Work was unchanged from Phase-4 input to output and changed from Phase-4 output to Phase-5 output `0f0d2a8ab84271f0f7a08d8b9051cf85ef113c55`. The Phase-5 manuscript diff contains only `main.tex`, Introduction, Diagnoses, Runtime Co-design, Related Work, and Conclusion; these correspond to the declared CR-10, CR-11, and CR-12 edits. No hidden manuscript paths changed. The Phase-5 novelty/secondary-boundary validator: **PASS**. The authorized Related Work change is an expected evolution, not a scientific regression.

## Current state

The new current-state validator passes Phase-4 scientific claims (B570 72/72 complete-ID prediction, tested-path sufficiency, no unique numerical cause, three ordered contributions) and Phase-5 boundaries (prior-work acknowledgment, Guard's adverse fixed-speculation comparison, inseparable 358H call, no later performance endpoint). It also checks historical text-path versus fresh direct-ID labels, B570 reference/live 60/72 BLOCKED, and anonymous Phase-2 ledger integration. Earlier detailed validators remain independent.

## Integrity

No old check was deleted retroactively. No scientific requirement was weakened. Phase 6A changed no manuscript file, closed evidence, `benchmarks/`, or `artifacts/`; it ran no experiment or inference. Its files are validator infrastructure, scope classification, and validation receipts only.

## Phase-6 readiness

**READY** after `validate_prior_phases_v083.py` reports `PRIOR PHASES: PASS`. Use that script as the cross-phase preflight gate; keep the Phase-4 original validator as a historical checkpoint check. Run it with Python dependencies `pypdf` and `pymupdf` available. In the current workspace, the passing command was `PYTHONPATH=/tmp/heterospec-phase3-pydeps python3 paper/mlsys2027/scripts/validate_prior_phases_v083.py`.
