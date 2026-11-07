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

The recorded dispatch is now complete. Do not re-execute its GPU commands.
R1 used `boundary.py prepare`, CPU `test_boundary_cpu.py`, then `boundary.py run`.
The post-exit retention repair used `resume_retention.py` to continue only
never-started T1 coordinates; it is not a general retry entrypoint.

Actual CPU closure commands were:

```powershell
$env:HETEROSPEC_RUN_ROOT = 'D:/hs120-8a6bde3c-bc24-4f16-9e1e-9950965386d3'
& $py -B "$lane/final_analysis.py" --root $env:HETEROSPEC_RUN_ROOT --out '<new CPU output directory>'
# Initial archive/restore commands already executed once:
& $py -B "$lane/seal.py" sources
& $py -B "$lane/seal.py" package
& $py -B "$lane/seal.py" restore
& $py -B "$lane/seal.py" replay
# Do not delete prior directories to repeat these commands.
```

For new CPU reanalysis of the retained restore, use a fresh `--out` directory,
`--root D:/hs120-8a6bde3c-bc24-4f16-9e1e-9950965386d3-fresh/raw`, and
`--source-map D:/hs120-8a6bde3c-bc24-4f16-9e1e-9950965386d3-fresh/SOURCE_MAP.json`.
The retained runtime source is under that restore's `raw/source_runtime/`.

Executed stages create immutable STARTED/FREEZE/ENDED records; these commands
are not permission to restart an existing phase. Historical entrypoints are never
called. `cpu` builds actual graphs and loads shared CPU core only; no CUDA plugin
or graph computation. `time` accepts only independently qualified N1 cells.
