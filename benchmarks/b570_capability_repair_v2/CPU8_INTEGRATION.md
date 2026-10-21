# PR119 原八项 CPU 验证接入方案

状态：修复源码独立复审 scoped-clean 后设计的执行方案；不是已实现、
已验证的八项入口。当前 runtime 的 measured 模式仍执行三小时能力实验，
不能用改 actor 参数或伪造 SUMMARY 的办法当作八项入口。
B570 可在下面明确授权的 D0 阶段实现和审查适配，冻结后不再改动。

## 目标与结果边界

只回答原 PR119 的八项 CPU 工程行为是否成立。保存历史 UUID 的源码、
原始归档、失败、结果与限制；不升级其资格，不改 PR115/117，不扩展论文。
GPU 查询/初始化/插件加载、工作负载模型读取/请求、科学原生启动、图计算均为零。
不运行 confirm.py、完整 19-case 开发套件或 57 项确认。

本轮成功名称为 CPU8_INTEGRATION_PASS，明确是八项用例和其任务内监督
的限定结果。它不是 CAPABILITY_ENDURANCE_PASS、旧完整确认通过、
全任务生命周期总账、ENGINEERING_READY 或论文证据。
若旧 raw_audit 的全任务总账要求仍未满足，必须保留该项 FAIL/UNKNOWN，
不得把受限八项状态写成旧 SMALL_WINDOWS_VALIDATION_PASS。

## 两层监督及必要适配

在新的 C:/hs/b570-capability-v1/<新 UUID>/ 下工作，外层监督在根内，
旧用例部署在 legacy/。不复用旧根，不调用旧 startCold，不依赖前序账本。
已存在但无测量的根也不能复用。通过正式 exec_command/write_stdin 启动，
真实查询系统路径/解释器身份，不依赖空 nodeRepl.env，不补造环境值。

D0 仅允许新增 task-local bridge、根路径参数化、真实生命周期到旧 schema
的转换、观测/核验接口及针对性测试。新副本不得覆盖旧 PR 源码。
需要改旧逻辑判据时停止；不允许降低 detector、控制点、1 秒覆盖或关闭要求。

1. 新外层以修复版 guards 与 Win32 primitives 为基础，在恢复 round/launcher
   前绑定实际 PID、创建 FILETIME、命令、句柄、Job 和冻结摘要；独立记录
   正常退出、超时、后代终止与句柄关闭。任务内产生的编译/测试/适配/审查/
   恢复进程也登记可实际观测的字段，未覆盖部分单列，禁止用 exit_code
   或 session_id 伪造 OS 时间。不能把通用旧 launcher 直接塞进 C1/C2/C3：
   原 capability verifier 的角色数和用例格式不适用于旧八项。
2. 旧 watcher/controller/launcher 内层保留原 100ms 名义周期、1 秒有效空窗、
   pending completion、sealed guard、真实故障注入与生产 detector。
   新外层 5 秒进度守卫只保证外层存活，不能替代内层 1 秒判据。
3. 将 common.BASE、raw_audit.ORIGINAL、配置/prepare/storage/恢复路径及所有
   硬编码根显式参数化为同一个绑定的 legacy 根；逐个列出改动位置。
   不做盲目全局字符串替换、不符号链接旧根、不临时改共享服务。
4. bridge 的 ledger 输出逐字段关联原始 OS 事件文件、序号、SHA256，
   每个 PID+创建时间唯一；缺字段输出 UNKNOWN 并拒绝依赖它的资格。
   保留新外层日志和旧原始日志两套来源，不将一个 PASS 布尔值翻译成另一个。
   旧 raw_audit 输出原样保留；新增八项判决器只汇总可重建的用例条件，
   单独保留原任务级全账本判决，不删失败项。
5. 冻结 bridge、原用例副本、C# 源码与真实编译产物、所有解释器/依赖、配置、
   新旧核验器、冻结规则和独立复审输入。编译 DLL 放独立 compiled 证据目录；
   source-only 恢复导入树不能混入 DLL/pyc/额外模块。
   启动 intent 必须在启动前登记冻结摘要；实际 OS 命令携带同一摘要。

## 有限开发与原生门槛

总墙钟从本轮第一次准备计起 6 小时，含下载、编译、两次以内独立复审、
恢复和交付。D0 最多 90 分钟、源码修订 0/1/2、20 个实际用例尝试；每次
启动前预约，逐次扣额，失败也计数，原始 CASE_BEGIN 重算。单次独立审查
最多 900 秒，两次合计最多 1,800 秒，均计入 D0。不能通过改 revision ID、
换 run、重启服务或开新 UUID 清零本轮额度。超过额度收尾。

D0 同时完成最小 bridge 与以下原生门槛，不再启动三小时重复 soak：

- 健康路径：修复 runtime 的 development 入口真实完成 C1/C2/C3，保留
  正常退出、超时和后代清理；这三项仍计入 20 次，不当成正式八项。
- watchdog 停滞：在真实 watchdog 已发布进度后，用有登记、独立截止和
  必然恢复/终止机制的 CPU harness 暂停它，确保它仍是原 PID/创建身份且
  RSS 可读。冻结 harness 应提供两用例之间持续 tick 超过5秒的受控等待，
  避免健康三用例过早结束而根本没测到停滞；不放宽原用例时限。supervisor 必须在旧进度超过 5 秒后的第一次 tick 拒绝，
  不再创建新用例，现存 actor 走真实清理；保留检测延迟、实际退出与
  所有 harness 进程的清理。独立救援上限 20 秒；救援代为关闭不追认
  supervisor 清理成功。不要对共享服务或无关进程注入。
- 冻结替换：隔离的牺牲根中调用实际 win.freeze_check 并保留初始摘要，
  修改 actor 以及相匹配的冻结清单，再检查；必须拒绝。另测子进程启动前
  已替换清单、只改源码、缺初始摘要。不能修改正式测量根做此反例。
- 预算与回执：在合成证据副本中运行真实 guards/verifier 路径，拒绝
  22,000 秒前置用时、D0>5,400秒、第四修订、重复登记、实际次数超过预约、
  全任务>21,600秒、交付>1,800秒、缺失/非有限时间或没有完成恢复的收尾。
  正常边界能通过；不得为了测试真的等待六小时。
- bridge 负例回归：缺控制点、提前被其他 detector 拒绝、缺 OS 退出、
  时间/身份错配、缺 pending completion、缺独立日志失败证据，都必须拒绝。
  健康 CPU bridge smoke（可用 normal_single）计为 D0，不能顶替正式用例。

为故障门槛创建专用 harness；禁止直接运行 runtime measured 然后在三小时
前中止并称为通过。harness/bridge 最终版本独立复审达到 P0–P2 scoped-clean，
其源码哈希和报告随后一起冻结。复审后改动必须重新审查，受上述额度约束；
没有有效独立报告就停止于 ADAPTER_REVIEW_BLOCKED。

## 正式八项：一次冻结、每项最多一次

每项运行前预注册 run ID、目标、故障 ID、预期 detector 和预算。
按表顺序串行，原始审计通过才允许下一项。不得扩为三轮或整套确认。

| 次序 / 用例 | 必须重建的证据 |
|---|---|
| 1 normal_single | 实际工作完成、stdout/stderr 与活动输出合法；退出后审计延迟不扩大运行覆盖窗口 |
| 2 normal_transition | 原定义 8 对 A→B、16 个唯一槽位；A 封存后 guard 连续，B 正常活动，无未解释提前拒绝，pending I/O 闭合 |
| 3 terminal_pending_completion | 关闭/取消期间确有目标封存写完成通知；记录成功且 bytes>0 的 pending completion 和对应实际句柄关闭，不能用 cancel 请求代替 |
| 4 frozen_input | 指定冻结输入实际被写，目标、故障 ID、原始通知及 SEALED_WRITE_REJECTED 相符 |
| 5 late_closed_slot_write | A 已封存、B 活动时 A 实际被写；持续保护及正确拒绝，不能忽略旧槽位 |
| 6 resource_read_failure | 生产资源读取实际失败，故障前采样有效、真实控制点和 RESOURCE_READ_REJECTED 对应；目录覆盖仍有效 |
| 7 directory_read_timeout | 生产活动目录读取实际阻塞超过 1 秒，故障前覆盖有效、独立 COVERAGE_GAP_REJECTED；资源覆盖仍有效 |
| 8 journal_write_failure | 生产 RESOURCE 日志真实写失败；独立 launcher/stderr/外层回执绑定失败路径，拒绝后不再 GO，实际进程与 I/O 收尾 |

单例保留旧 90 秒上限、transition 180 秒、清理 30 秒；不能因外层更宽而放宽。
正式八项额外至多 8 个 case ID，其中 transition 仍包含 16 槽位；两种计数都报。
任何非预期失败、提前拒绝、未达控制点、守卫过期、漂移、超额、退出或 I/O
未证实，立即停止后续，保留 FAIL/BLOCKED/UNSTARTED，不重试、不修补冻结。

资源采用两个适用限额中较严格者：同一时刻一组用例；新外层每个 supervisor/
watchdog RSS≤512MiB，actor≤256MiB，合计≤1.5GiB、live actors≤8。
全部新任务子进程启动≤3000、已覆盖寿命和≤21600秒；缺失部分不得当0。
新派生存储≤1GiB，至少256MiB证据/恢复预留，磁盘剩余≥10GiB，最多两份归档。
旧内层更具体的日志/监测/句柄限制全部保留。若启动前资源不可满足，停止而非提额。

## 收尾与可接受结论

交付保留30分钟；启动正式阶段前必须留足八项最坏用例+清理+审计+交付余量。
记录第一次准备 UTC、冻结 UTC、真实启动 UTC、单调计时区间、全部修订和
预约/实际次数。复用修复版预算规则时不得把 bridge 的 run 假装成原
CAPABILITY_ENDURANCE 格式；新增八项审计器要独立复算同样的时长门槛。

原始包与清单远端上传后实际下载到新目录，逐成员认证，再用包内未改核验器
在隔离导入树重算；外部绝对路径工具绑定独立核验。最终尾部回执绑定冻结、
清单、正式工具请求/结束、恢复报告摘要及观测时点。旧归档不重新打包。
有限前缀 PASS 与最终交付分开；最终工作超过六小时不得报任务 PASS。

八项全部控制点、检测、清理、覆盖和恢复通过，才可报 CPU8_INTEGRATION_PASS；
否则 ENGINEERING_BLOCKED，并明确具体门槛和未启动数。
外层自身/shell/工具宿主生命周期缺口仍单列；若发现缺口落到八项必要证据内，
该用例不能通过。保留全账本缺口，绝不宣称 ENGINEERING_READY。
全部结果回推 PR119 新 UUID 结果目录，保持 Draft，不合并，不自动开始后续。
