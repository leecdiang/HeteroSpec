# RTX QB mechanism and independent-block confirmation

**Implementation Draft — zero new GPU experiments in this PR.** Includes an E2 cost-study planner/executor/analyzer, an E1 diagnostic source-patch generator and tensor comparator, and 20 locally passing synthetic test methods. Windows adapter integration has not been tested in the authoring environment. **E1 native compilation and capture/replay orchestration still require host integration before its execution freeze.** This is not a claim that both experiments are already turnkey or completed.

Baseline: PR98 commit `3235d44c26edd92db33e574094c26af8e29d2452`. QB means **Query-to-Batch**, PQ the per-query local implementation, M target-only and C speculative. Do not replace the tested quantized models, numerical DLLs or reference contract. Keep this PR independent of B570 and paper PR102.

## E2: does the small PQ/QB cost difference reproduce?

Use the three inherited families, twelve tasks per family, M_PQ/M_QB and C_PQ/C_QB, and the serial R reference. All comparisons retain the direct native IDs, EOG-or-cap128 endpoint and inclusive resident request timer. No cache reuse, phase timers, heavy capture, added synchronization, Nsight or ETW in the paid comparison.

The default reuses the **exposed PR98 panel** and measures new execution blocks, not new-input generalization. `prepare --holdout FILE.json` instead admits twelve direct-ID tasks per family only if IDs and token sequences are disjoint from the old P2 panel. That check alone does not certify absence from every earlier experiment: the host agent must document the full exposure history before calling inputs blind. Panel choice must precede timing and cannot change after registration.

### Prespecified schedule and budget

Six sessions. Within each family/session, run R before and after the comparison panel in separate processes. Split the twelve shuffled tasks into four triplets. For each M/C triplet, run PQ and QB consecutively in fresh processes; alternate AB/BA so each session contains two pairs of each ordering. Each process receives one excluded warmup, then its assigned measured requests. Family, path and task order are deterministic from seed 20261014. There are **324 fresh worker processes, 864 PQ/QB requests, 432 reference requests and 324 warmups: 1,620 native request starts total**.

Adjacent sessions start at least one hour after the previous session completes. The last starts at least 24 hours after the first. This gives separate time blocks spanning dates, **not six independent dates**. CPU preparation and native-process lifetime are separate; the E2 owned-process limit is 12 hours. There is no significance-based stopping, speed-based exclusion, scientific retry or automatic sample-size extension. Missing/failed blocks remain visible and withhold the affected confirmatory estimate. An underpowered result is inconclusive, not permission to tune until positive.

Temperature, utilization, AC state, GPU/driver/memory identity and power scheme are admitted before each process. Clock/power observations are recorded outside the paid request timer. These are endpoint samples, not continuous thermodynamic tracing or proof of physical residency. The inherited resident worker verifies loaded numerical modules and full offload. The watchdog only targets its own child process.

### Analysis

For each family and M/C separately, all 12 tasks must match both local R endpoints, and references must remain stable across all six sessions. A single output mismatch, failed/missing coordinate or heavy observer condition withholds the aggregate qualified estimate; do not select only fast/equal tasks. Compute each session's equally weighted mean of task log(latency_PQ/latency_QB), then equally weight the six session values. Report the geometric speed ratio, QB latency reduction, every session and task ratio, regressions, and the prespecified practical ratio threshold 1.02.

The script provides an approximate percentile bootstrap **over the six session contrasts**, not over individual requests. Six clusters are a small sample; this interval is conditional on the fixed tasks and one host and does not establish cross-device or strong cross-date generalization. Do not describe six family/path intervals as a familywise-controlled significance test. Preserve sign reversals and results below the practical threshold.

### E2 host commands

Use a new worktree and new run directory. The legacy directory must contain the fixed `resident.py`, `run_common.py` and their original helper modules. `--runtime` is the admitted PR98 binary directory, historically `D:/hsc95/native/build/bin`; `--results` is the PR98 benchmark result directory. Models are rehashed at their recorded local paths. Python >=3.11; use `-B` to avoid writing bytecode into inherited directories, and never use `-O`.

```powershell
cd benchmarks/rtx_qb_confirmation_v1
python -B -m unittest -v
python -B experiment.py prepare --results "D:/path/to/PR98/benchmarks/rtx_querylayout_mechanism_v1" --legacy "D:/path/to/PR98/scripts/platform/rtx_evidence_closeout_v1" --runtime "D:/hsc95/native/build/bin" --out "D:/hs-qb-confirmation-v1"
```

Before execution, inspect the complete generated PLAN/FREEZE, source bindings, inherited helper integration, native module identities, host telemetry and the intended input exposure. Resolve any integration defect by an explicit amendment **before** starting its affected scientific slots. Commit the exact generated `FREEZE.json` to `benchmarks/rtx_qb_confirmation_v1/registration/E2_F0.json` on this branch, push, and use that full commit in every session. The executor checks both local Git and authenticated GitHub registration bytes. No credentials or model weights belong in the registration.

```powershell
# Replace COMMIT and the worktree path with the actual registered values.
python -B experiment.py run-session --out "D:/hs-qb-confirmation-v1" --repo "D:/path/to/new-worktree" --freeze-commit COMMIT --registration "benchmarks/rtx_qb_confirmation_v1/registration/E2_F0.json" --session 0
# Invoke sessions 1..5 only at their admitted separated times, with the same freeze.
python -B experiment.py analyze --out "D:/hs-qb-confirmation-v1"
```

The commands do not create a scheduler or background service. Do not overwrite failed receipts or rerun an interrupted started coordinate. Diagnose stale locks and process lifetime before any deliberate recovery. The raw record/export and endpoint checks here are not a new full independent audit of every historical provenance claim.

## E1: broader finite numerical correspondence, not a universal theorem

The source generator accepts only the exact PR98 `capture95.h` and `replay95.cpp` Git blobs. It emits replacements into a **new** directory, never patches E2 binaries. Capture gains a selected layer, prefill/continuation, exact q=1..4 and minimum observed key extent. Replay admits q=1 and deliberately uses the common single-query path for all labels at that negative-control width. Existing dtype, GQA and mask restrictions remain; no unsupported geometry is silently relaxed.

```powershell
python -B experiment.py patch-e1 --capture "D:/path/to/PR98/scripts/platform/rtx_querylayout_mechanism_v1/capture95.h" --replay "D:/path/to/PR98/scripts/platform/rtx_querylayout_mechanism_v1/replay95.cpp" --out "D:/hs-qb-e1-patch-v1"
```

**Host integration gate, not yet implemented as a complete capture runner in this PR:** make an isolated copy of the byte-pinned native source; replace only its diagnostic `common/capture95.h` and `replay95.cpp`; use the inherited build recipe with the same numerical DLLs. Bind generated-source, full driver-body, compiler and executable hashes. Review and test the capture adapter before registration. The historical environment sanitizer removes `HS_*` variables: the host adapter must explicitly pass the four E1 selectors below, rather than assume shell variables survive. Do not edit the historical adapter in place or relabel a failed build as a scientific null.

Prospective bounded matrix: three families × first/middle/last target layer (derive L from pinned model metadata; indices 0, floor(L/2), L-1) × prefill/continuation × q=1..4 = **72 contexts**. q=1/3 use minimum key extent 0; q=2/4 use 128. This is a deliberately sparse design, **not a full key-length factorial**. Freeze exact selected tasks and token IDs before any new forward; select the longest inherited P2 prompt per family with lexical ID tie-break, not by observed numerical difference. A missing exact q/key context is NOT_OBSERVED; no post-hoc replacement task or forced suffix.

Selector environment: `HS_E1_LAYER`, `HS_E1_PHASE` (0 prefill, 1 continuation), `HS_E1_Q`, `HS_E1_MIN_KEY`. Use a native unrepaired MQ capture condition at that physical width; q=1 uses ordinary decoding, q>1 may use the inherited speculative native route with maximum proposal width q-1, subject to actual topology admission. Keep the condition identical for capture-on/off controls.

Per context: one counts-mode warmup, one heavy capture and one counts-mode full-endpoint observer control in an isolated owned process. Maximum **216 native request starts**, including warmups, and **432 standalone operator starts** (MQ/PQ/QB × two repeats × 72), with an E1 combined owned-process limit of six hours. The host orchestration must enforce and persist these budgets; the current `patch-e1`/`compare-e1` CPU utilities do not enforce a global GPU budget by themselves. No scientific retry. Authenticate the complete E1 runtime/driver/plan freeze before these starts.

The host adapter must retain real native tensor bytes, shape, stride, mask, GQA, source lifetime and raw decode trace. Preserve snapshot input hashes before/after each replay, exact executable/module identities, commands, output-on/off equality and all attempt logs. Use output folders `MQ-r0`, `PQ-r0`, `QB-r0`, `MQ-r1`, `PQ-r1`, `QB-r1` for the native replay executable; rotate execution order. Then:

```powershell
python -B experiment.py compare-e1 --snapshot "D:/path/to/captured/context" --replays "D:/path/to/that/context/replays"
```

The comparator checks native MQ own-path tensors and within-arm repeatability before reporting PQ/QB equality. It is a component of the audit, not a replacement for the host observer/input/source gates. A same-input counterexample narrows the method's admitted scope; a failed own-path replay is NOT_ADMITTED. Actual GPU kernel symbols, reduction trees and counts-off launch scheduling remain UNKNOWN unless separately captured and qualified. Captured runtime graph nodes alone do not prove them. This study neither claims QB support on Vulkan nor attributes GS's larger gains solely to QB.

## Agent handoff and completion

Keep this PR in Draft. Finish the stated host integration, freeze complete source/driver/runtime/input plans prospectively, then execute only the admitted bounded experiments. Do not tune to recover an expected advantage. Report E1 numerical qualification and E2 request-cost qualification separately; archive positive, null, reversal, regression, failure and missing-context outcomes. Seal new raw logs/manifests, restore them in a fresh directory and independently rerun the CPU analyses before calling the new evidence archived.

Modify only this new benchmark directory and branch. No edits/merges to main, old experiments, PR102 manuscript, arXiv, Zenodo, releases or licenses. Existing empirical numbers stay unchanged until a separately authorized paper revision. The current 20 synthetic tests exercise scheduling, estimator algebra, failure withholding, source-anchor rejection, stride handling and freeze rejection; they are not native Windows, CUDA, E1 compilation or whole-archive acceptance tests.
