# Cold-start amendment: follow this before the eight-case prompt below

The original results/RESULT.md is immutable BOOTSTRAP_BLOCKED history. Write the
new outcome to results/TOOL_INTERFACE_RESULT.md; preserve existing COLD_START_RESULT.md as well. This amendment replaces the old
unspecified bootstrap setup below. No Windows execution is claimed by source tests.

1. In the ALREADY RUNNING Windows x64 Node tool service, capture
   `globalThis.b570ToolClock = {beginMs: performance.now(), now: () => performance.now()}` before task preparation.
   Do not start shell, Git, Python, npm, compiler, or a new observer to prepare.
   Use built-in network/fs APIs to fetch the locked remote commit. Exclusively
   create `C:/hs/b570-supervision-fix-v2-20261016`; if it exists, stop without
   cleaning or reusing it. Materialize this directory at
   `BASE/repo/benchmarks/b570_supervision_fix_v2`, excluding historical results,
   caches and binaries. Validate remote Git blob identities, every source-review
   binding, and independent review report identity before importing any code.
   Record the existing service capability probe and Python executable identity without
   spawning a version query. Do not read a process global or import node:process;
   use only public performance, nodeRepl.env and node:os interfaces. Native loading
   must be permitted by the service; stop on any denial, without an indirect bypass. Do not fabricate previous ledgers or success marks.
2. Use an explicit existing Python absolute path as `pythonAbsolutePath`.
   In that same service:

   ```javascript
   const {startCold} = await import('file:///C:/hs/b570-supervision-fix-v2-20261016/repo/benchmarks/b570_supervision_fix_v2/host/bootstrap_cold.mjs');
   globalThis.b570 = await startCold({python: pythonAbsolutePath, toolClock: globalThis.b570ToolClock, environment: nodeRepl.env});
   ```

   The pinned bridge requires Node-API 8+; native loading itself must succeed.
   Do not obtain process.versions through require, a VM or another module. The adapter downloads and authenticates the fixed CPU
   native bridge in BOOTSTRAP_DEPENDENCY.json, without npm/install scripts/helper
   children. This CPU Win32 binding is not a GPU plugin. If unavailable, stop
   admission; do not adapt tools on the machine. Keep this Node session and b570
   object alive through closure; never reset it. The adapter creates the broker
   suspended, registers its OS identity, then resumes it. No predecessor required.
3. Poll `await b570.ready()` for at most 10 seconds in the existing service.
   On failure stop and preserve startup receipts/stdout/stderr. Before any tests,
   submit exactly one smoke request:

   ```javascript
   await b570.submit('bootstrap-smoke', [pythonAbsolutePath,'-I','-S','-B','-c',"print('BOOTSTRAP_OK')"], {role:'bootstrap-smoke',timeout:10});
   ```

   Wait for `await b570.result('bootstrap-smoke')`; require real exit zero,
   correct output, actual creation/exit ledger records and no open descendants.
   This is additional startup validation, not one of the eight cases. Failure
   stops subsequent work. Every later new process must use b570.submit with a
   unique ID and wait for its complete result before submitting the next request.
4. If no known standalone Node executable is available, stop admission before
   startup and report that missing prerequisite; do not launch a discovery helper.
   Through that broker run Python tests (`-B -m unittest discover -s <tests>`) and
   an explicitly known existing Node executable (do not discover it through process.execPath) (`--test <tests>/test_bootstrap.mjs
   <tests>/test_gates.mjs <tests>/test_tool_capabilities.mjs`). Run `python -B <host>/compile_launcher.py --compiler <existing-csc.exe>`
   through the broker to CPU-compile LauncherCapture.cs to host/LauncherCapture.dll
   and create results/BUILD_RECORD.json using the existing Windows compiler and preserve exact command, executable
   identity, stdout/stderr, exit status and DLL hash. No version-query helper may
   bypass the broker. Continue with exactly the eight cases below, once each,
   serially using `run_dev.py --id <unique-id> --revision 0 --cases <exact-case>`;
   stop at the first failure/control-point miss. Do not run confirm.py.
5. Run every snapshot, raw audit, archive and download/restore child through the
   same broker BEFORE stop. Development snapshots require --source-only. Authenticate
   the package source against this commit's SOURCE_REVIEW_FREEZE, and retain the
   last raw audit's exact ledger prefix. No old freeze or results may be reused.
6. In the SAME existing Node service run `const closed = await b570.stop()`.
   Require actual OS exit, zero remaining job descendants, closed handles and
   persisted BOOTSTRAP_CLOSED.json. Load host/closure_audit.mjs in this same service
   and call `await auditClosure(BASE, closed, finalRawAuditRelativePath)` with that
   actual returned receipt and the final raw audit to verify the tail. Do not
   substitute a manually constructed exit-code object.
   Sending STOP alone is not closure. After stop, upload/read back/write results
   using existing-service APIs only; do not start Git/auditor/helper processes.
   On any failure, still attempt stop and preserve evidence. Missing observation
   remains missing; never launch a replacement observer to invent closure.

Acceptance: frozen reviewed source; real cold smoke; all eight cases reach their
registered control points and satisfy raw evidence; complete process/OS closure,
budgets, remote recovery and exact audit reproduction. Only then report
SMALL_WINDOWS_VALIDATION_PASS. Otherwise ENGINEERING_BLOCKED (or BOOTSTRAP_BLOCKED
when no case can be admitted), remaining cases UNSTARTED. No ENGINEERING_READY,
scientific performance result or paper claim. Preserve PR115/117 and old PR119
result; remain Draft. The operator must report source/bridge identities and the
pre-existing observer separately from task-owned processes.

---

# B570 小规模 Windows 验证执行 prompt

本文件供负责人确认本 PR 最终独立审查通过后，手动发给 B570 执行。它不是本次本地修复已运行 Windows 的记录，也不自动启动任务。

---

请验证 `codex/b570-supervision-fix-v2-20261016` 分支中
`benchmarks/b570_supervision_fix_v2/` 的实际 Windows CPU 监督行为。先读取 PR 正文、README、PROTOCOL、EVIDENCE 和 VALIDATION，确认最终独立审查状态为 scoped-clean，锁定并回报实际提交 SHA。若 PR 后续有未审查源码改动，先停止准入。

本任务仅做小规模工程验证，不扩展论文主线。PR115 和 PR117 保持原提交、Draft 和 ENGINEERING_BLOCKED 收尾。禁止 GPU 查询/初始化/插件加载、模型文件读取、模型请求、科学原生启动和图计算；所有这些计数必须为 0。禁止运行 confirm.py、完整 19-case 开发套件或 57 项确认。任何结果都不得写成 ENGINEERING_READY 或论文科学证据。

使用固定且全新的 `C:/hs/b570-supervision-fix-v2-20261016` 根目录；若已存在任务材料，停止并报告，不能清理或覆盖。按精确字节取得新目录源码；不复用旧 PR 的编译产物、冻结、收据或成功标记。先在已有工具服务中安排前瞻外层进程登记与收尾观测，使首次新任务进程、编译、Git、审查、broker、后代、恢复与交付均可计账。BOOTSTRAP_REGISTRY 必须包含实际执行 broker 的 PID/创建时间及单调时钟任务起点；不要补造已错过的记录。若无法做到，停止于 BOOTSTRAP_BLOCKED，列出缺失，而非继续再产生一份不完整总账。实时预算和最终总账都须覆盖登记的外层进程。

本次仅允许 1 个冻结源码版本、8 个指定用例，每个用例最多运行 1 次，串行执行、各用独立注册 run ID。不得现场修改源码、重试失败用例、自动升级到全矩阵。沿用 BUDGET 中的单用例、进程、内存、存储与总时间硬上限，同时保留证据和恢复预留；记录实际累计值。若源码或工具适配需要修改，保留证据并停止，交回本 PR 修复。

先运行便携回归测试，并对 LauncherCapture.cs 做真实 CPU 编译，记录编译器身份、命令、退出码、DLL 精确哈希和所用源码集合；不能把编译或单测 PASS 算成 Windows 验收。经已登记 broker 执行 run_dev.py，每次显式传 `--cases`，禁止省略该参数：

1. normal_single
2. normal_transition（保留原定义的 8 对 A→B，不更改判据）
3. terminal_pending_completion
4. frozen_input
5. late_closed_slot_write
6. resource_read_failure
7. directory_read_timeout
8. journal_write_failure

每个用例结束后先检查原始证据再继续。任何非预期提前拒绝、未到控制点、进程未闭合、watcher I/O 未完成、真实资源超额、日志失败未取得独立外层证据、源码漂移或审计异常，都立即停止后续用例。后续标 UNSTARTED；不得把提前挡住算作负例通过。预期负例须满足其注册目标、故障 ID、真实操作和独立 detector，不能只看某个 PASS 字段。

重点检查：
- 正常 A→B 是否自然成功；保留所有原始通知，区分收到通知时间和未知的实际写入时间，不猜测唯一原因。
- GO/CONTINUE 在拒绝后是否确实不发送；临时 pending probe 正常关闭且永久 guard 始终保留；取消请求不能代替实际 I/O completion。
- ACTIVE 目录元数据在 namespace/rootmeta 重叠 guard 下判据一致，CLOSING/SEALED 不按内容相同放行替换。
- resource/directory 故障前的完整采样与含故障采样分别重建；实际 RESOURCE 日志写失败须有 launcher 捕获的独立 stderr 证据。
- controller、launcher、round 和所有任务进程真实收尾。不能用固定时长、布尔闭合字段或开发 PASS 补足缺失证据。

生成 manifest-bound 原始审计。开发快照必须给 snapshot.py 传 --source-only：保留编译 DLL 的实际字节、哈希、源码身份及构建证据，但将归档内该 DLL 放在快照的 compiled 证据目录，不能混入源码专用恢复导入树；不要删除运行时 DLL 或其 source_caps。恢复时必须先认证当前独立审查覆盖的完整源码与依赖集合，拒绝额外导入模块和字节码，再用包内未改审计器在隔离导入环境重算。开发阶段恢复须显式传入本 PR 的 SOURCE_REVIEW_FREEZE.json 作为 --source-freeze（使用相对于任务根的路径），先核验它来自锁定远端提交；它只绑定已审查源码，不是 CONFIRMATION_FREEZE，也不授予确认资格。上传与下载恢复仅更新本新 PR 的独立结果目录，保持 Draft，不合并。

最后交付 RESULT：锁定提交、实际启动/未启动的 8 项矩阵、原始失败与控制点、实际进程/寿命/墙钟/存储总账和缺失、远端证据与恢复状态、所有禁止操作的零计数。全部完成只能称 SMALL_WINDOWS_VALIDATION_PASS；其余称 ENGINEERING_BLOCKED，并给出首个阻断证据。不得宣称完整确认通过、B570 科学性能改善或论文结论推进。
