# Build, execution, analysis and recovery

Windows Python 3.12, Visual Studio 2022 BuildTools, CMake; no new dependencies.

Build in this worktree:

```powershell
python scripts/platform/b570_prefill_diagnostic_v1/generate_sources.py
cmake -S scripts/platform/b570_prefill_diagnostic_v1 -B C:/hs/b570-prefill-build -G "Visual Studio 17 2022" -A x64
cmake --build C:/hs/b570-prefill-build --config Release --parallel 2
Copy-Item C:/hs/b570-direct-id-v1-build/bin/Release/*.dll C:/hs/b570-prefill-build/Release
```

Do not rebuild a frozen version and resume it. Its source/binary hashes must
remain fixed. Exact new target/native sources and observer.h are retained.
generate_sources.py asserts replacement anchors against read-only source.

Entry points: controller.py prepare/run/status/pilot, fixture.py,
independent_verify.py. Prepare already completed; do not repeat. Pilot is an
engineering entry point and is never used for N1. Detached full pipeline:

```powershell
$studyPython = 'C:\Users\DIANG\AppData\Local\Programs\Python\Python312\python.exe'
$studyController = 'C:\hs\b570-prefill-v1\scripts\platform\b570_prefill_diagnostic_v1\controller.py'
$studyProcess = Start-Process -FilePath $studyPython -ArgumentList $studyController,'run' -WindowStyle Hidden -PassThru -RedirectStandardOutput 'C:\hs\b570-prefill-v1\artifacts\b570_prefill_diagnostic_v1\controller.stdout.txt' -RedirectStandardError 'C:\hs\b570-prefill-v1\artifacts\b570_prefill_diagnostic_v1\controller.stderr.txt'
$studyProcess.Id
```

Before launch or recovery read artifacts/b570_prefill_diagnostic_v1/RESUME.md,
STATE.json, STATUS.json and LOCK.json. Compare PID creation identity, not just
PID. An active matching controller means status read only. Stale locks are
retained with a unique suffix; completed valid results are hash-checked and
reused. Every attempted unit has its own attempt directory and raw logs.

The controller is independent of the model turn. The no-GPU fixture validated
continued output after the launching tool returned. This is a tested local
execution mechanism, not an automatic model wake-up or survival guarantee.

Final audit reopens raw captures directly with a separate endpoint implementation
and never imports the collector. It checks all 360 raw arrays, endpoints,
baseline regressions, transfers, input and file hashes, and seal/N1 order.
Clean extracted archive is audited with that same independent checker.

No draft PR, manuscript change, main/tag update, merge, release or submission
is performed. Final reports may be read without running inference again.
