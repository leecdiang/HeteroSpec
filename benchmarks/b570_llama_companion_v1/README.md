# B570 / Vulkan Llama companion to RTX PR160

**Design and executable source kit; no B570 native build, model forward or numerical qualification has been performed by the authoring environment.** Do not label the proposed expanded Vulkan domain as previously qualified.

Base: B570 PR152 `022babfabb3d1b6f4f2a2830dca04b2654d193f9`. RTX PR160 `aff1d029966a20adebfad6b664a36f32ed04bf9c` is already executing independently. This branch adds only two new directories; it does not merge, edit or wait on the RTX branch. Read HISTORY_AND_PROTOCOL.md and HOST_PROMPT.md first.

## What is implemented

Code: `scripts/experiments/b570_llama_companion_v1/` (Python standard library; C++17 + llama.cpp + Vulkan).

- `history.py`: recover exact original Llama models, token IDs and diagnostic history; optionally authenticate all54 historical records and5916 full vectors and map real cycle/row decisions.
- `source.py`, `build.py`: separate pristine-upstream oracle and candidate builds. Recover pinned B570 overlays, preserve AV shader arithmetic, source-bound candidate admission extension to q2/3/4 and key256/512/768/1024. Default no speculative root-cause repair is enabled.
- `worker.cpp`, `cycle.hpp`: natural R/M_PQ/M_QB/C_PQ/C_QB k3 execution; full decisions including rejected rows, pending ownership, correction/bonus and KV trimming; fresh contexts, fixed greedy/EOG/cap128. A new native integration, not a claim that the old k1 formal.exe can run it.
- Actual same-state q1 versus multiquery probes before a selected verification cycle, actual readback and positions, own-path multiquery replay and unchanged live-state checks. Rejected suffix rows are explicitly conditional, not natural R.
- Scheduler-node assignment and opt-in output tensor/stride/position capture; no inference from weight/buffer location and no fabricated Vulkan shader/pipeline identity.
- `host.py`, `capacity.py`: source/asset-bound epochs, zero-forward placement admission, tested ancestor Windows suspended-Job supervisor, exclusive GPU lock, loaded-runtime checking, renewable hash-chained resource ledger and retained partial failures.
- `audit.py`, `triage.py`, `trace_compare.py`: complete-vector greedy reconstruction, actual output-to-cycle mapping, explicit strided row comparisons, separate local-reference and implementation-correspondence findings.
- `panel.py`, `design.py`: post-freeze natural-input selection with both-platform exposure exclusion, heavy/off qualification, six-period Williams paired costs, dual PQ controls.
- `archive.py`: lossless partitioning and exact archive/member readback. Upload and a fresh authorized remote download must follow; local readback is not remote delivery or scientific replication.

## Hardware and reference decisions

Use the **exact RTX Q8 Llama target and draft bytes**, not the older B570 Q6_K target. The two files total 9,861,858,848 bytes before KV/context/compute/driver allocations. All-GPU feasibility is unproven on B570. Admission tries `(target GPU layers,draft GPU layers)` in this output-blind order: `(999,999)`, `(999,0)`, `(28,0)`, `(24,0)`. Both models stay Q8. The first allocation profile meeting declared headroom is selected before any scientific output. CPU draft or partial target placement is disclosed, not mislabeled a hardware-only comparison. Unknown failures are inspected, not automatically called OOM.

The new Vulkan oracle is a separately built, frozen stock UB1 execution with this selected target placement. It is **not** CUDA R and **not** the old Q6 reference. Keep the oracle executable and all its libraries separate from every evolving candidate. Candidate R must match this oracle's complete endpoints and saved full decision vectors. Do not force CUDA and Vulkan R to agree, or import opaque CUDA KV into Vulkan.

## Commands on the B570 host

Use a fresh worktree on this PR and a new work root, with the original authenticated upstream tarball. No old object files, shaders, models, references or runtimes are overwritten.

```powershell
$code = 'scripts/experiments/b570_llama_companion_v1'
python -B -m unittest discover -s "$code/tests" -v
python -B "$code/history.py" --repo . --out C:/hs/b570-llama/history
# Restore authenticated PR151 logical paths from the private evidence release first:
python -B "$code/history.py" --repo . --raw-root <restored-PR151-diagnostic-root> --out C:/hs/b570-llama/HISTORICAL_RAW_AUDIT.json
python -B "$code/build.py" --config C:/hs/b570-llama/build.json --mode oracle --out C:/hs/b570-llama/oracle
python -B "$code/build.py" --config C:/hs/b570-llama/build.json --mode candidate --out C:/hs/b570-llama/candidate-00
python -B "$code/capacity.py" --config C:/hs/b570-llama/host.json --out C:/hs/b570-llama/capacity-00
# SELECTED.json gives the selected epoch. Baseline executes6 oracle +30 candidate requests:
python -B "$code/host.py" baseline --epoch <selected-epoch>
```

The examples contain local placeholders deliberately; fill paths/tools/driver/resource fields from actual discovery. A missing Windows SDK or ABI adjustment is an engineering task, not a scientific result. `build.py` supports a pinned optional candidate source-extension script for the eventual evidence-led repair. It never applies it to the oracle.

### Development

A baseline reference mismatch is reported, not treated as the end of research. `triage.py` locates the relevant **local** Vulkan cycle; do not reuse CUDA's cycle number merely because the input is the same.

```powershell
python -B "$code/triage.py" --reference <local-oracle-heavy.json> --candidate <local-C-heavy.json> --out <new-triage.json>
python -B "$code/host.py" run --epoch <epoch> --attempt diagnostic-01 --slots <explicit-diagnostic-slots.json>
python -B "$code/host.py" budget --root <research-root> --credits 16384 --seconds 604800 --reason 'Specific next mechanism/control/replay work; cumulative old evidence retained'
```

Diagnostic slots extend an existing natural slot with `stage="diagnostic"`, `probe_cycle=<observed cycle>`, `observer="heavy"`, optional `trace=true` and `trace_pattern`. Start checkpoint/probe without tensor tracing; require unchanged natural trajectory, actual state readback, live-state nonmutation and own-path replay. Then add a trace/no-trace pair. The probe uses fresh receivers sequentially to reduce peak memory. If capacity still fails, redesign shadow residency explicitly and validate its own controls; do not silently change the frozen scientific placement.

New source/runtime/policy requires a successor epoch and retained old receipts. CPU-only auditor fixes should re-audit existing raw before considering any native rerun. There is no small per-candidate retry cap. Unsettled live processes/locks must be reconciled with evidence before another unit starts.

### Freeze and confirmation

Write the evidence-backed REVIEW.json. It pins an actual complete exposure audit for both platforms. For a no-trigger platform, use NONTRIGGER_PORT_VALIDATION, not EVIDENCED_REPAIR. If RTX's mechanism is later transferred, run a separately pinned transfer/ablation epoch.

```powershell
python -B "$code/host.py" freeze --epoch <epoch> --review <review.json>
python -B "$code/panel.py" --pool <tokenized-natural-pool.json> --exposure <both-platform-exposure.json> --freeze <epoch>/FREEZE.json --out <new-panel.json> --count 24
python -B "$code/host.py" confirm --epoch <epoch> --panel <new-panel.json>
```

`confirm` re-audits previous completed units on resume. Default24 gives48 oracle references,240 candidate qualification and864 measurements+864 warmups. R timing uses the original local oracle executable; all paths use the same selected model placement and fresh-context lifecycle. Candidate failures block timing, not continued development in a new epoch. Exposed panels are never silently recycled as unseen. A justified12-input panel can be chosen only before output exposure; it is not a failure-dependent reduction.

## Explicit remaining native work

Actual MSVC/Vulkan build and capacity validation; validate the new q3/long-key request port using real operands and own-path controls; inspect real Vulkan pipeline/shader choice if needed; implement the mechanism indicated by evidence; integrate old Qwen B570 regressions with semantic scope activation (old HS_REQUEST_LAYOUT alone no longer activates the new setter); compile/run old and new natural controls; tokenize and audit the confirmation pool; independently rebuild raw results; upload then freshly download and verify every member. No finished repair or GPU qualification is claimed by CPU tests.
