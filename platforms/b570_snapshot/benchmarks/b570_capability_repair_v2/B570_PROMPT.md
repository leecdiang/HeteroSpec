# 发给 B570 的完整执行 prompt

请继续 PR119（leecdiang/HeteroSpec，分支
codex/b570-supervision-fix-v2-20261016），执行本轮“修复门槛 + 原八项 CPU 接入”。
本任务已授权在有限 D0 内实现必要适配、测试、独立复审、冻结以及通过门槛后
连续执行八项，无须每一步再询问；不以达到某个积极结果为目标，不隐藏失败。

先读取本提交的 benchmarks/b570_capability_repair_v2/README.md、
CPU8_INTEGRATION.md、REVIEW_BINDING.json、review/ 中的独立复审记录、
runtime/ 全部实现与回归。CPU8_INTEGRATION.md 是本轮完整执行协议，与本
prompt 一起生效。锁定实际远端提交，逐文件验证 REVIEW_BINDING 中的修复
源码摘要及 scoped-clean 复审状态。存在未审查运行时代码漂移时停止，不凭
旧 PASS 放行。保留 PR115/117 和 PR119 历史三小时 UUID 的全部字节与结论。

范围严格限 CPU 工程；GPU 查询/初始化/插件、工作负载模型读取/请求、
科学原生启动和图计算均为0。不改论文，不运行 confirm.py、完整19项或57项。
当前修复 runtime 的 measured 模式仍会跑三小时；本轮不要调用它来假装
短检查，也不要重复三小时 soak。目标是八项接入，不是继续堆运行时长。

使用全新 C:/hs/b570-capability-v1/<UUID>/，正式 exec_command/write_stdin；
不复用已有根、不调用旧 startCold、不依赖共享 Node 的 process/env、不补造
SystemRoot。真实取得解释器、系统目录和工具身份，保留请求、完整输出、
会话结束与实际 OS 观测。能力层外侧的生命周期缺失单列，不填0或伪造退出。

按 CPU8_INTEGRATION.md 执行：
1. D0 最多90分钟、3个源码修订、20个实际用例尝试；每次前瞻预约并逐次扣额，
   失败保留且计数。总任务6小时含编译、审查、恢复和交付；交付预留30分钟。
   两次以内独立复审，每次≤900秒、合计≤1800秒，计入D0。不得换根清零额度。
2. 在新副本实现小型 bridge/harness：参数化旧根，保留旧 watcher/controller/
   launcher 的判据；外层使用已修复的进度、冻结和预算守卫。不能简单改 C1
   的命令运行旧用例，因为角色和证据格式不同。列出全部适配文件/理由。
   允许路径、入口、真实证据转换和核验接口适配，不允许放宽科学/工程判据。
3. 运行30项便携回归，并完成协议规定的原生门槛：真实健康 C1/C2/C3；
   watchdog 已停滞但身份/RSS仍可读时，supervisor 拒绝下一用例并清理；
   初始摘要固定后源码+清单一起替换仍被拒绝；真实预算检查拒绝超时、
   第四修订、少报预约、缺失/非有限时间等反例。故障只注入隔离牺牲根和
   任务进程；暂停 watchdog 的 harness 必须有独立20秒救援，救援不冒充
   supervisor 自行清理成功。全部尝试计账。
4. 对完整最终 bridge/harness/核验器及所用依赖独立复审至 P0–P2 scoped-clean。
   通过后冻结源码、配置、真实 C# 编译产物、工具身份与审查报告。在正式
   tool intent 中预登记冻结 SHA256，实际入口携带同一摘要，进程内固定。
   冻结后不得修改、重试或重启测量。审查/开发额度耗尽则保留阻断并收尾。
5. 正式阶段只按顺序运行一次：
   normal_single；
   normal_transition（原定义8对A→B、16唯一槽位）；
   terminal_pending_completion；
   frozen_input；
   late_closed_slot_write；
   resource_read_failure；
   directory_read_timeout；
   journal_write_failure。
   每项原始审计通过再启动下一项；每项先注册独立run ID、目标、故障ID及
   detector。正常/transition/清理分别保留90/180/30秒上限。
6. 严格应用 CPU8_INTEGRATION.md 表中的验收标准。尤其不能用外层5秒代替
   内层1秒；负例必须确实到达预定控制点、发生目标操作并由正确 detector
   拒绝。提前被旧槽位通知挡住、缺pending completion、只有cancel请求、
   只有布尔PASS、退出码或session ID，都不能算通过。日志写失败必须有
   独立外层原始回执，拒绝后没有GO，实际进程及I/O闭合。
7. 首个非预期失败、漂移、超额或清理未知即停后续，标明UNSTARTED，不现场
   修补冻结。预期故障被正确检测且原始审计完整才算该负例通过。旧原始
   raw_audit 输出完整保留；新桥接不得删除全账本失败或合成缺失OS字段。
8. 归档、远端实际下载到新目录、逐成员验哈希，再使用包内未修改核验器在
   隔离导入环境重算。编译DLL保留为compiled证据，不混入source-only导入树。
   尾部回执绑定冻结、清单、工具结束、恢复报告摘要和实际观测时点；
   返回PENDING_DELIVERY不算最终PASS。核验时点后的尾部成本继续报告，
   最终所需交付超过6小时则任务BUDGET_EXCEEDED，不沿用早期前缀PASS。

不要为“持续数小时”刻意等待、循环、重跑或自动进入下一阶段；门槛通过就
顺序推进，八项做完即收尾。发生协议明确阻断时停下是正确结果。

最终回推 PR119 的新独立结果目录，保持 Draft、不合并。交付 RESULT.md：
锁定提交与最终冻结、适配/审查版本、全部D0失败、原生门槛结果、正式八项
PASS/FAIL/BLOCKED/UNSTARTED矩阵、控制点与detector、进程/墙钟/存储实测和
缺失、恢复证据、禁止操作零计数。全部八项及必要证据通过才能报
CPU8_INTEGRATION_PASS，否则ENGINEERING_BLOCKED或具体预算阻断。
限定结果不等于旧完整确认、全任务总账、ENGINEERING_READY或论文结论。
不修改历史三小时证据，不自动启动GPU、科学实验或其他后续任务。
