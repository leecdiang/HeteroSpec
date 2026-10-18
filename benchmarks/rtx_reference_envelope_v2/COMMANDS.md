# Actual entrypoints

Worktree: `D:/hs120`. Set `HETEROSPEC_RUN_ROOT` to the UUID directory in
`INVENTORY.json` when replaying outside this workstation. Python is the actual
interpreter recorded there. Build imports/includes are recorded in `BUILD.json`.

```powershell
$py = 'C:/Users/ASUS/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe'
$lane = 'D:/hs120/benchmarks/rtx_reference_envelope_v2'
& $py -B "$lane/build.py"
& $py -B "$lane/test_cpu.py"
& $py -B "$lane/run.py" cpu
& $py -B "$lane/run.py" diagnose
# Commit stable implementation before formal qualification:
& $py -B "$lane/run.py" qualify
& $py -B "$lane/run.py" time
& $py -B "$lane/analyze.py" --root '<UUID raw root>' --out '<fresh summary directory>'
```

Executed stages create immutable STARTED/FREEZE/ENDED records; these commands
are not permission to restart an existing phase. Historical entrypoints are never
called. `cpu` builds actual graphs and loads shared CPU core only; no CUDA plugin
or graph computation. `time` accepts only independently qualified N1 cells.
