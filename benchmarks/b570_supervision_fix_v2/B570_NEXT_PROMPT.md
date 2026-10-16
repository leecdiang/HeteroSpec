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
