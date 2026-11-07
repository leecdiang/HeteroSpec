# Actual execution and CPU reconstruction

Python: `C:/Users/ASUS/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe`.
Worktree `D:/hs122`, branch `research/rtx-mechanism-baselines-v1-20261018`.
Lane `benchmarks/rtx_mechanism_baselines_v1`.
New raw UUID `D:/hs122-5e483f69-dac1-41a4-a046-14401910e6e5`.

The commands below are actual history, **not permission to resume this UUID**.
Every stage has immutable STARTED/ENDED or FAILED plus owned lifecycle receipts.

1. Read pinned PR122 docs, PR121 result/collector/graphs, CONTRIBUTING; run
   `python -B -m unittest -v test_cpu` (15 tests).
2. `bootstrap.py` copied exact selected input bytes, no old ordinary outputs;
   `adapt_native.py`, `adapt_controller.py`, `prepare_rtx.py build/graphs`.
   CPU source/native graph checks, pre-CUDA rejection and Windows cleanup tests.
3. `capability_cpu.py`: three explicitly accounted SMI calls and one NVML session;
   installed profiler search. Official NVIDIA wheels downloaded by exact PyPI
   URL/hash under raw/tools. CUDA runtime DLL from wheel is **not** numerical
   runtime; it is never in PATH. Only headers used, and explicit CUPTI path/hash
   dynamically loaded in instrumented hosts. Build failures retained.
4. Implementation commit `378adc08`; `runner.py freeze`, `runner.py reference`:
   44 new serial hosts. Initial capability: two OFF alternating-value hosts pass;
   first ON host access violation before first graph, retained.
5. Tool callback field correction commit `2c77e50c`; `freeze_tool_repair.py`,
   `runner.py capability2`: two new ON hosts, actual capture/replay and alternating
   input bytes pass. Original OFF/reference receipts retain original identity.
6. `runner.py qualification`: 144 hosts, including21 instrumented qualification
   hosts. `export_measurements.py` and `trace_summary.py` before timing completed
   a full raw-byte audit. 24 total profile attempts include the initial failure.
7. `runner.py confirm0`, then separately started `runner.py confirm1`: eight
   balanced blocks,768 fresh hosts; each8warmups+30measurements. No CUPTI in clean.
8. P0 engineering commit `3c05febf`; `producer_rtx.py freeze` before P0 GPU outputs:
   distinct OFF plan/IDs, B0 dual identity untouched. `producer_rtx.py p0reference`,
   `p0qualification`, separately `p0confirm0` and `p0confirm1`.

CPU-only postprocessing (set `HETEROSPEC_RUN_ROOT` to the raw directory):

```text
python -B audit_rtx.py --cohort core --out <new-output-directory>
python -B audit_rtx.py --cohort p0 --out <new-output-directory>
python -B trace_summary.py --out <new-output-directory>
python -B cost_details.py --out <new-output-directory>
python -B identity_audit.py --out <new-output-file>
python -B verify_archival.py --out <new-output-file>
```

`close_rtx.py snapshot/package/restore/replay` is the local exact-member ZIP+CAS
retention and fresh CPU workflow. It neither launches a GPU nor uploads raw.
`report_rtx.py` generates compact public tables and RESULT from audited data.

All outputs are exclusive-create; use fresh CPU output names. Freeze JSONs bind
actual consumed bytes, including Windows line endings. Git source text may use
LF; consumed source/binaries are retained in raw SOURCE/SOURCE_REPAIR1 and the
public execution artifacts use per-file `-text` attributes. Never substitute
Git-normalized source bytes for an exact execution identity.
