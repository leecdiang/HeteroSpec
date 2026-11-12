# Request-side preparation

The request-side result is **INCONCLUSIVE for native service value**. No model
or GPU was run. The source-only dynamic schedule, independent constructed
state-machine fixture and host cost reader are ready for review; full native
request qualification and timing integration remain open.

The current 19 CPU tests pass in ordinary Python and `python -O`. Raw fixture
records, test logs and a structural scan of the eight old #215 receipts are
retained in `cpu_result_v2/`. The scan confirms natural ingredients in separate
fixed-k requests and explicitly leaves the combined chain uncovered. The
initial 17-test `cpu_result/` is retained; review then tightened endpoint-cost
admission and added missing-reset and missing-guard cases.

Recreate the checks into a fresh output directory (the script refuses to
overwrite `cpu_result`), or rerun just the tests:

```powershell
& 'D:/HeteroSpec-PC/.venv-analysis/Scripts/python.exe' -B -m unittest discover -s tests -p 'test_request*.py' -v
& 'D:/HeteroSpec-PC/.venv-analysis/Scripts/python.exe' -B -O -m unittest discover -s tests -p 'test_request*.py' -v
```

Prepare a fresh source-only frontend from the exact historical input:

```powershell
& 'D:/HeteroSpec-PC/.venv-analysis/Scripts/python.exe' -B request/prepare_native.py D:/rtx211-q8-20261109/frontend-v2 request/prepared_frontend_new
```

The adapter changes `worker.cpp` only. It preserves old files and does not
load models or run a worker. `prepared_frontend_PREPARATION.json` binds every
copied source, identifies the old worker and lists unresolved native gates.
See `PROTOCOL.md` for controls, endpoint, natural/constructed scope and all
unresolved requirements.

`build_frontend.py` reuses the old recorded compiler/link arguments and
unchanged static cores, writing solely to a fresh new build directory. It
does not launch its output. Build status and exact commands, failures and
before/after read-only input hashes are kept with the build, not inferred from
CPU fixture success. Runtime DLL inventories cannot be claimed from a link.

Both compile attempts failed and remain retained. `build/FAILED.json` records
Zig installation-directory discovery failure. After byte-identical workspace
staging of Zig and its library, `build_v2/FAILED.json` records
`entry.cpp:1:1: error: Unexpected`. A separate header compile returned the same
tool error; its verbose log is retained. No object, linked executable or
native request was produced. Do not interpret source preparation as a
successful native build or qualification. `STATUS.json` binds these results.
