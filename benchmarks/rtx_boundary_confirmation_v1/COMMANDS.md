# Actual RTX entrypoints

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
