# PR223 first-round continuation, e03

**Current result: INCONCLUSIVE; actual GPU/model usage remains zero.** Read [e03/RESUME_REPORT_ZH.md](e03/RESUME_REPORT_ZH.md), [e03/RESULT.json](e03/RESULT.json), [e03/dedup/DEDUP_E03_RESULT.json](e03/dedup/DEDUP_E03_RESULT.json) and [e03/review/FINAL_REVIEW.json](e03/review/FINAL_REVIEW.json). This isolated continuation starts at PR223 head `8f2585f90c40c81bca726c50647af650fd866e3f`.

The actual numerical CUDA DLL now links with C dispatcher and one shared prelaunch budget provider. Normal numerical DLL initialization, real A/B/C routing and all 66 native cells remain **NOT_RUN**. Full-host/original-thread clearance and usable full-model physical-launch coverage remain **BLOCKED**; native configure deliberately returns -6. CPU tests and compiler resource reports are preparation evidence only.

The archive explicitly includes the new numerical DLL and a read-only canonical-ledger snapshot, plus source deltas, build commands and retained failure logs. No old DLL is replaced. Reconstruct the uniform source with `runtime/materialize_final_source.py` using the pinned original source kit and `runtime/delta-v2`; see [runtime/README.md](runtime/README.md). A fresh reconstruction verified all 3546 files. Git records large-text/binary hash commitments; the archive supplies those bytes. Private thread caches, unchanged pinned core files, tools, weights and unlisted executable products are excluded.

Budget remains the original family: 256 requests, 1,000,000 rows, 10,800 native GPU seconds, 4096 all-kernel launches and 2 GiB capture. No window has started, no allowance was added. No round two is recommended or started. Minimal normal-host read-only evidence collection is in [e03/dedup/OWNER_STEPS_ZH.md](e03/dedup/OWNER_STEPS_ZH.md).

Everything below is inherited e02/e01 history, retained with its original scope.

## Inherited e02 entry

**Current result: INCONCLUSIVE, zero GPU/model work.** Read [continuation/RESUME_REPORT_ZH.md](continuation/RESUME_REPORT_ZH.md), [continuation/RESULT.json](continuation/RESULT.json), [continuation/review/V7_FINAL_RECHECK.json](continuation/review/V7_FINAL_RECHECK.json), and [continuation/NEXT_NATIVE_ENTRY.md](continuation/NEXT_NATIVE_ENTRY.md).

Windows supervision and frontend build/link are now CPU-tested. The final frontend is `continuation/frontend/hooked_frontend_v7`, built in `hooked-build-v5`, including actual binary JSON byte checks. Native thread/host clearance, full-model prelaunch counting, all 66 native cells, real request closure and complete service timing remain unqualified. Do not start round two.

The original family budget is unchanged. Use the canonical family ledger named in `continuation/safety/BUDGET_BINDING.json`; a new epoch does not add allowance or restart the window. No native window has started.

The delivery archive includes complete selected failure/build logs and own CPU raw ledgers. Git contains source/receipts and hash commitments; text files over512KiB and CPU SQLite bytes are archive-only. Private unrelated thread databases, copied old ledgers, model weights, tools and executable products are excluded. Critical inherited 41-test sources remain unchanged and were not rerun.

The following text and root `RESULT.json`/`REPORT_ZH.md` are **inherited e01 evidence**, retained for comparison. Current results are under `continuation/`.

## Inherited e01 entry

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
