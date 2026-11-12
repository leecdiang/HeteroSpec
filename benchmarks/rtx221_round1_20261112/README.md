# Windows RTX 5070 Ti: first-round preparation

**INCONCLUSIVE. No new GPU/model execution.** Native work remains blocked until the original execution thread and the Windows execution adapter are verified. This is an additive, isolated continuation of #221 at `af436df989570ad882db65bd8a4b265b9e8cfdae`. It does not rerun #213/#215.

Read [REPORT_ZH.md](REPORT_ZH.md), [RESEARCH_QUESTION.md](RESEARCH_QUESTION.md), [RESULT.json](RESULT.json), [RESOURCE_PLAN.json](RESOURCE_PLAN.json), [qualification/README.md](qualification/README.md), [native/README.md](native/README.md), and [request/PROTOCOL.md](request/PROTOCOL.md).

The native prototype is build-only and execution-disabled. The host admission/ledger module is preparation code, not a qualified live launcher: it has no process-bound exclusive lock, global three-hour deadline or integrated worker monitoring. No JSON boolean releases the delivered operator executable's compile-time block. No native qualification or performance result is claimed.

Run host checks using an installed Python executable, not the WindowsApps alias:

```powershell
& 'D:/HeteroSpec-PC/.venv-analysis/Scripts/python.exe' -B -m unittest discover -s tests -v
& 'D:/HeteroSpec-PC/.venv-analysis/Scripts/python.exe' -O -B -m unittest discover -s tests -v
```

Rebuild the operator in a new output directory with `build_tools/build_operator.py --out build_tools/rebuild-review`. It reads the hash-bound private Windows source kit and installed CUDA/MSVC; it never runs the resulting probe. See native build findings/history for exact flags and preparation failures. The new request frontend's build status is separately recorded under request/build.

The compact delivery excludes model weights, recovered historical weight/activation binaries, copied old ledgers, toolchain copies and executable build products. Those remain at the bound local locations. It contains the sources, fixtures, build commands/logs, all prospective expectations, raw CPU records, source/module identities and independent checks. A fresh host must supply the pinned source kit/toolchain and models; this package is not a standalone model distribution.
