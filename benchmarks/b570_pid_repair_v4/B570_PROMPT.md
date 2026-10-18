# 发给 B570 的完整执行 prompt：PR119 PID 身份修复验证

继续 PR119 的 CPU 工程接入。本次使用 benchmarks/b570_pid_repair_v4/ 的
修复交付；先读取 README、RESULT、REVIEW_BINDING 及独立复审原始报告，
锁定远端 SHA 并核验全部绑定文件。历史 4cb0e0f（14a37e28 UUID）、3cf5612 的 ENGINEERING_BLOCKED、
6214e73d UUID、三小时 c475bcaf UUID、PR115/117 和论文全部保持原样。
不追补历史缺失退出，不覆写旧失败，不把此次新尝试记成旧任务重试。

范围：真实启动预检、review 观察器原生检查、停滞门槛、完整 CPU8 候选独立
复审；所有必要门槛确实通过后，按既有 CPU8_INTEGRATION.md 冻结并顺序执行
原八项。不要重跑三小时 soak，不运行完整19项/57项，不做 GPU 查询、初始化、
插件加载、模型读取/请求、科学原生执行或图计算，不扩展论文。

本次修复代码已交付，不授权现场编写替代入口或放宽判据。允许填写真实路径、
新 UUID、时间、注册/清单/审查回执和编译产物这些数据；遇到还需源码适配、
缺依赖、原生失败或独立审查 findings，完整保留后停止，回 PR 修复。
不要为了“持续几小时”故意循环、等待或重复失败。

## 1. 新任务部署和预算

使用全新 C:/hs/b570-capability-v1/<UUID>/，已有根一律不复用。
记录本轮首次准备 UTC，全部准备/下载/编译/审查/恢复/交付计入6小时；
D0至正式冻结最多90分钟，交付预留30分钟、至少256MiB。
总新存储≤1GiB、磁盘剩余≥10GiB；其他限制沿用 CPU8_INTEGRATION.md。
本轮运行一个已交付源码版本，不消耗0/1/2去现场猜入口；所有原生门槛、
smoke和失败仍前瞻预约并计入最多20个开发用例，子进程另行计账。
review profile 的专用资源例外仅适用于审查/合成辅助树，绝不改变 actor 限制。

按精确远端字节部署，不用历史结果目录作为运行根：
- 获取锁定提交中的 benchmarks/b570_supervision_fix_v2/ 源码/依赖文件，
  放到新根 legacy/repo/benchmarks/b570_supervision_fix_v2/；包含其根级
  check_receipts.py、ACCEPTANCE.json、BUDGET.json 和 host/，不能只复制host。
  不复制旧results、run、冻结、日志或可执行编译产物。
- 以 3cf5612 的 implementations/6214e73d... 中 source/、src/rev2/、
  legacy/repo/.../host/ 的精确字节覆盖对应新副本。
- 再以本提交 b570_pid_repair_v4/source/ 和 src/rev2/ 覆盖新副本。
  这是确定的文件覆盖次序，不改文件内容。保存每层来源/摘要/最终清单。
- acquisition/repair/ 保存 b59545a 设计交付中的 CPU8_INTEGRATION.md、
  B570_PROMPT.md、REVIEW_BINDING.json、review/review-2.json、
  review/review-2-status.json 等原协议输入；它们是来源证据，不是新adapter批准。
  新修复的协议/报告另存 acquisition/entry_repair/。
- 新建真实 ACQUISITION.json、CONFIG.json、CPU8_PLAN.json、TASK_START.json、
  legacy/ROOT_BINDING.json；沿用既有结构，task_root/legacy_root、UUID和时间
  必须是本轮真实值。只可把历史 CONFIG/CPU8_PLAN 当计划模板，不复制旧
  注册、PASS、freeze、审查批准或receipt。
- 使用已批准 Python 的实际绝对路径；通过正式 exec_command/write_stdin，
  不依赖共享 Node process/env，不伪造SystemRoot。不使用裸命令等待时间
  充当进程硬截止。

## 2. 真实入口预检先行

先运行 source/test_process_registry.py、source/test_identity_audit.py、
source/test_entry_repairs.py 的全部回归与 src/rev2/test_repairs.py
的30项回归及 test_exception_policy.py 的异常策略回归。它们不等于 Windows 验收。

对部署后 source/、src/rev2/ 所有文件生成 ENTRY_SOURCE_MANIFEST.json
（files: 相对路径到SHA256映射，禁止pyc/额外模块）；先登记清单SHA256、
命令及工具身份，再执行下列脚本。所有命令参数应为实际绝对路径：

python.exe -I -B <root>/source/startup_preflight.py
  --root <root> --manifest <root>/ENTRY_SOURCE_MANIFEST.json
  --manifest-sha256 <已登记摘要> --output <root>/preflight/STARTUP.json

它会真的从不同工作目录启动 observe、outer_watchdog、stall_supervisor、
stall_harness，加载当前Win32/runtime及入口所需依赖，核验实际模块路径、
退出码并再次验清单。必须取得 STARTUP_PREFLIGHT_PASS。
仅语法编译、--help、fixture通过或单独能import win不算。
任何模块缺失、路径错配或入口失败都停止在 STARTUP_PREFLIGHT_BLOCKED；
不得在原生控制点后才发现入口不能导入。

## 3. 原生观察器检查：直接使用交付的 helper_tree.py

先确认主机资源能容纳有限review配置：最多32个Job成员、每进程2GiB、
合计4GiB、观察器512MiB。每次≤900秒；本节smoke设30秒。
actor case配置仍是8个、每个256MiB、合计1.5GiB。
辅助进程不是actor，不能默认使用case profile；也不能去掉观察器。

每个smoke预登记独立ID、原始命令、目标profile、预期结果；串行执行：

A. review-smoke-ok：
python.exe -I -B <root>/source/review_entry.py --root <root>
  --id review-smoke-ok --seconds 30 --
  <python.exe> -I -B <root>/source/helper_tree.py
  --folder <root>/development/helpers-ok --children 10
期望正常退出。用 check_observer_smoke.py --folder
<root>/processes/review-smoke-ok --kind review 重建，必须证明至少11个实际身份、
至少11个并发Job成员、真实退出和空Job。

B. case-smoke-limit：
使用 observe.py --root <root> --id case-smoke-limit --seconds 30 --kind case --
运行同一 helper_tree.py，换新folder，--children 10。
期望观察器非零退出，LIMIT_DECISION 命中 live_process_count。
核验器 --folder <root>/processes/case-smoke-limit --kind case --expect-rejection
必须确认原始超额与实际清理；不能把非零退出本身算通过。

C. review-smoke-limit：
使用 review_entry.py，独立ID review-smoke-limit、30秒、新folder，
helper_tree.py --children 32（含父进程超过32）。
用核验器 --kind review --expect-rejection，验证review配置自身仍有硬上限
及真实退出。超额但缺退出/空Job证据算失败，不能继续真实审查。

资源统计必须来自Job成员，包括嵌套调试器管理的子进程；调试事件的生命周期
覆盖另列。保留 READ_OBSERVATION、LIMIT_DECISION、OS_EVENTS 和全部
stdout/stderr。无法解释的资源读取失败不是预期超额通过。
以上smoke不产生任何scoped-clean审查结论。

### 3D. 连续短命进程门槛（新增，不要求操作系统必然复用 PID）

前瞻预约一个 kind=observed_command 用例，ID review-churn，run=processes/review-churn。
使用 review_entry.py --root <root> --id review-churn --seconds 180 --
<python.exe> -I -B <root>/source/churn_helpers.py --children 200。
必须一次完成200个子进程，stdout恰有200条index=0..199的结果和最后
CHURN_COMPLETE/children=200；所有子PID均在该次OS_EVENTS的创建记录出现。
本串行用例使用专用身份核验器：
python.exe -I -B <root>/source/audit_identity_stream.py --folder <root>/processes/review-churn --churn。
必须 IDENTITY_STREAM_PASS，至少201个实际身份，全部退出、句柄闭合及空Job。
将stdout的每个子PID与OS创建记录关联，报告实际不同创建身份和reused_pids。
没有观察到PID复用可通过原生短命压力项，但不得宣称真实PID复用复现；
同PID不同创建时间由本轮确定性Registry回归覆盖，二者分开报告。
存在未知身份、未匹配退出、重复活跃PID或核验错误即阻断。

### 3E. 应用断点异常反例（新增）

预约一个 kind=observed_command，ID review-breakpoint，run=processes/review-breakpoint。
通过 review_entry.py --root <root> --id review-breakpoint --seconds 30 --
<python.exe> -I -B <root>/source/breakpoint_helper.py 运行一次。
预期命令及观察器非零，实际根进程非零退出；必须到达
APPLICATION_BREAKPOINT_BEGIN，不能出现 APPLICATION_BREAKPOINT_SWALLOWED。
用 audit_identity_stream.py --folder <root>/processes/review-breakpoint --breakpoint
核验完整退出和非零根退出、应用断点被NOT_HANDLED转交。只有该完整反例通过才继续。
这不是完整审查的非零退出豁免；完整审查仍要求成功完成和clean报告。

## 4. 原生门槛与完整复审

前瞻登记本轮开发额度及各run；复用接口要求的 healthy-r0-a1、
stall-r2-a1、stall_harness_r2、freeze-r1 是新根内的标签，不代表重用旧结果。
本轮源码仍只有一个版本，登记revision=0；与history所需的REVISION_*.json
及D0_RESERVATIONS.json保持一致。REVISION_*.json 是watchdog/冻结actor历史登记，
只放这两类；冻结登记必须含 kind=in_process_freeze，健康/停滞用 kind=watchdog。
三个observer smoke及review-churn、review-breakpoint在全量D0_RESERVATIONS中用 kind=observed_command，
run为processes/<对应ID>，由OS_EVENTS的真实OBSERVER_START重算，不伪装成watchdog。
legacy bridge smoke仍由原ROUND日志重算；所有类别都保留预约额度。
健康预约3项，停滞预约2项（第二项必须
未启动），冻结预约4项，三个observer smoke另计3项，新增review-churn、review-breakpoint各计1项，其余bridge smoke
同样前瞻预约，总和不得超过20。

真实完成健康C1/C2/C3和冻结反例，然后执行：
python.exe -I -B <root>/source/stall_harness.py <root>

暂停前必须实际完成首个C1并到达STALL_READY；暂停后watchdog身份/RSS仍可读，
以暂停后的最终progress为基准，5秒过期后拒绝下一用例；MUST_NOT_START
不得出现。保留监督器真实退出、watchdog恢复/退出、空Job和句柄关闭。
20秒救援只能救援，触发救援不能取得停滞门槛PASS。
用 native_gate_audit.check(root) 及原始日志重建，任意提前退出都标NOT_REACHED，
不能称为正确拒绝。

按既有CPU8协议完成必要C#真实编译、bridge针对性回归和D0 smoke，保留
所有失败。禁止复用历史DLL当作本轮编译成功。此阶段若源码缺陷暴露，不现场
改源码，不推进正式八项。

完整候选独立复审必须覆盖最终 source/、src/rev2/、legacy源码与依赖、
launcher源码/构建身份、新旧审计器及协议。新修复的scoped-clean不能替代
这项完整adapter复审。复制不可变候选、生成输入清单、保存精确哈希。
通过 source/review_entry.py --root <root> --id full-review --seconds 900 --
调用现有正式独立审查入口，显式要求P0–P2完整审查、只读、不执行项目代码、
不委派、不超过2个并发读取助手。不要绕过工具自身隔离。
正式工具允许继续轮询至观察器收尾；不能用yield_time_ms当900秒硬截止，
也不能给更外层工具设置早于观察器+清理的截止。

真实审查必须最终完成，报告有明确scope、findings和scoped-clean，
输入字节仍匹配，命令/观察器真实结束且已覆盖进程退出闭合。
此外对 processes/full-review 运行 audit_identity_stream.py，必须取得
IDENTITY_STREAM_PASS；它只核验观察器覆盖内的身份，不替代独立审查结论，
不补足观察器自身、外层shell或其他未覆盖生命周期。
stdout有文字、退出0、观察器正常结束或review smoke通过，都不能替代报告。
资源守卫、超时、工具异常、incomplete、findings均不得追认clean。
保存精确触发样本及缺失；本轮至多一次完整复审，不为好看而重试。

## 5. 只有全部前提通过才接原八项

只有原生门槛、bridge开发判据、完整独立复审和预算全部通过，才按既有接口
生成FINAL_REVIEW_BINDING和前瞻执行冻结。新增回执只能是证据，不改运行源码。
在冻结前对最终source inventory重新生成入口清单并再做真实启动预检，
说明与首次清单的差异仅是已登记证据文件。不能复用早期清单掩盖变更。

随后串行一次执行：
normal_single；normal_transition（8对A→B、16槽位）；
terminal_pending_completion；frozen_input；late_closed_slot_write；
resource_read_failure；directory_read_timeout；journal_write_failure。

每项原始审计通过再启动下一项。保留原内层100ms/1秒、真实控制点/目标
detector/pending completion/实际收尾判据，外层5秒绝不替代。
正常/transition/清理上限90/180/30秒。冻结后不改、不重试。
提前被其他错误挡住、未到控制点、缺实际退出或I/O完成，都不是负例通过。
任一非预期失败立即停止，后续UNSTARTED。

## 6. 收尾

保留本轮全部原始数据，上传后实际远端下载到新目录、逐成员验哈希，
包内未修改核验器隔离重算；有限前缀、最后审查/恢复/发布尾部时间分别记录，
最终必要交付超过6小时不得沿用早期PASS。历史十个缺失退出仍为null。
结果写到PR119新UUID目录，保持Draft、不合并、不自动启动后续。

逐项报告：入口预检、PID确定性回归、原生review-churn及实际复用数、三个observer smoke、健康/冻结/停滞门槛、完整复审、
F0是否生成、原八项矩阵、控制点、实际进程/寿命/墙钟/存储和未覆盖项、
恢复证据、GPU/模型/科学执行零计数。
八项及其必要证据全通过才报CPU8_INTEGRATION_PASS；
否则ENGINEERING_BLOCKED并给出第一个阻断及UNSTARTED。
即使限定八项通过，也不是完整总账、旧57项确认、ENGINEERING_READY或论文结果。
