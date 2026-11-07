# Actual RTX commands — dispatch complete; do not rerun GPU

Worktree `D:/hs121`; Python is the frozen executable in RUN_SPEC.json.
Run from this directory with `-B` (no old entrypoints):

```powershell
$py='C:/Users/ASUS/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe'
& $py -B -m unittest -v test_cpu
& $py -B prepare_rtx.py prepare
& $py -B prepare_rtx.py build
& $py -B test_rtx.py
# Commit correctness-critical sources, then freeze once:
& $py -B collect.py freeze
& $py -B collect.py reference
& $py -B collect.py qualification
& $py -B collect.py aa_pilot
# METHOD_DECISION.json must be frozen from A/A only before these:
& $py -B collect.py confirm0
& $py -B collect.py confirm1
```

New root is recorded in local ignored LOCAL_RUN.json or explicit HETEROSPEC_RUN_ROOT.
Every stage/task creates exclusive STARTED records; never invoke an old UUID again.
The logical optional holdout is NOT dispatched by these commands. No profiler,
actor, decoder, W1 or model request is part of these entrypoints.

H1 pays CUDA packing/materialization/restoration inside the graph. Its completed
call includes direct readback into a preallocated per-call buffer. Initialization,
input-copy/upload and output-buffer allocation are reported separately. QPC and
numerical comparisons remain observers and can affect subsequent replay.

## Completed CPU delivery

After all GPU tasks ended, the actual CPU-only commands were:

```powershell
& $py -B cpu_preparation.py
& $py -B export_rtx.py --out '<UUID>/analysis_final' --draws 4000
& $py -B factor_review.py --plan '<UUID>/plan.json' --analysis '<UUID>/analysis_final/ANALYSIS.json' --out '<UUID>/analysis_final/FACTOR_REVIEW.csv'
& $py -B cost_views.py --plan '<UUID>/plan.json' --hosts '<UUID>/analysis_final/HOSTS.csv' --out '<UUID>/analysis_final/OTHER_COST_VIEWS.json'
& $py -B cpu_prepare_audit.py --out '<UUID>/cpu_preparation_analysis'
& $py -B seal_rtx.py sources
& $py -B seal_rtx.py package
& $py -B seal_rtx.py restore
& $py -B seal_rtx.py replay
& $py -B report_rtx.py
& $py -B format_result.py
```

The archive/restore commands already ran once and require fresh destinations. Do
not delete prior directories or run GPU tasks to repair transport/formatting.

CPU-only new reanalysis can use the retained fresh restore with a NEW output:

```powershell
$env:HETEROSPEC_RUN_ROOT='D:/hs121-0cd72634-266d-4b57-9b00-1d7df2327735-fresh/raw'
& $py -B "$env:HETEROSPEC_RUN_ROOT/source_runtime/export_rtx.py" --out '<new CPU output directory>' --draws 4000
& $py -B "$env:HETEROSPEC_RUN_ROOT/source_runtime/cpu_prepare_audit.py" --out '<new CPU preparation output directory>'
```

The adapter remaps case/serial paths in memory only and checks original exact
source/input/reference bytes; it does not edit raw specs or recapture references.
Actual independent-process logs and every QPC/input/output occurrence are local.
The separate AUX_FRESH_RECOMPUTE.json records factor/cost/prediction table replay.
