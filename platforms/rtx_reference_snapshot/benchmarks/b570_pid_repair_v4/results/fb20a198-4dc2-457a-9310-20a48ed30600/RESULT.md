# PR119 B570 CPU8 — ENGINEERING_BLOCKED

本轮 UUID：fb20a198-4dc2-457a-9310-20a48ed30600。设计/来源锁：b28740c3bad06c743c28c74afe6ee0e50101fe9b。实际新增实现提交：6673ba89b188878275c7b536a5c1570c0c8604bc。保持 Draft；没有执行冻结，没有启动正式八项。

## 实际结论与停止边界

根据作者最新直接指令“注意，遇到阻碍自行修复，目标是完成实验”，在新根内修复接入阻碍，保留所有中间源码、失败与工具回执。没有沿用附件中禁止现场修复的停止规则。原 CPU8 的90分钟D0、20次原生尝试、两次独立复审各900秒/合计1800秒、6小时总任务和30分钟交付边界继续保留，解释前瞻登记在 development/AUTHORIZATION_VARIANCE.json。0/1/2是登记批次标签，不能据此声称只有三个不同源码哈希。

第一次完整独立实现复审正常完成，发现4项P2：D0只信摘要、外层采样证据可空、工具回执未绑定真实watchdog命令、漏登记D0启动可漏账。均已修复并完成生产路径CPU回归。

第二次完整复审正常完成，确认四项修复，但仍有2项P2：
1. source/verify_cpu8.py:18 只验证清单所列文件，没有要求与完整证据树及消费输入逐项一致，可能漏交历史失败。
2. source/verify_cpu8.py:47 未将独立 WATCHDOG_RECEIPT.json 与原始 WATCHDOG_END.receipt 及生命周期边界一致核对，改变 end_ns 可能错误缩短交付时长。

两次复审额度已用尽，不能形成准入所需的最终 P0–P2 scoped-clean。停止于 ADAPTER_REVIEW_BLOCKED；未生成 CAPABILITY_FREEZE.json，不启动八项，不把源码建议当成实际 Windows 验收。两份报告与全部原始审查进程流保留；第二候选清单SHA256为3251aaa6a7b0bd10f153441d01ae229878f7df3f9d1bba42d6d3a6d072eb478c。

## 原生门槛和实际失败

|项目|实际结果|证据/边界|
|---|---|---|
|来源/工具身份|通过|162份精确来源条目，34项交付源码绑定；独立Python3.12.10、Windows系统目录、PowerShell、C#编译器和审查CLI真实身份|
|四入口Windows隔离启动预检|通过|实际新进程，模块来源逐项比对；当前源码清单ed7f285d86c7028758e08ac5ccd7fda4e7652e7036718187c78f97582cb3bd12|
|observer正常/两个资源限额负例|原始审计通过|分别21/21、21/21、65/65已识别身份实际关闭；两个限额负例由live_process_count正确拒绝，不当成普通成功|
|初次200-worker churn|失败并保留|worker108超时；217个身份关闭，14为额外PID身份数；不得将未完成200轮称为通过|
|修复后200-worker churn|通过|真实200个worker、201个总身份关闭；2个额外复用PID身份；仅修复console创建方式，不改每子进程5秒边界|
|真实应用断点负例|通过|到达APPLICATION_BREAKPOINT_BEGIN，NOT_HANDLED，非零实际退出；没有SWALLOWED|
|健康C1/C2/C3|3/3通过|5个actor，正常退出、超时、后代清理原始证据；不顶替正式八项|
|实际冻结替换负例|4/4通过|源码+清单、子进程前清单、源码单改、缺初始pin，均到达对应拒绝|
|真实watchdog停滞|通过|原PID/FILETIME和RSS仍可读；5,015,408,300ns进度年龄处拒绝下一用例；20秒独立救援未触发，实际退出/空Job|
|bridge首次D0正常|失败并计账|GBK读取UTF8 ACCEPTANCE失败，CASE_BEGIN前；仍收费1次|
|bridge第二D0正常|失败并计账|DETACHED PowerShell退出0但controller/工作未到达；原审计EVIDENCE_MISSING，不以退出0放行|
|bridge独立新ID正常/日志失败|D0限定通过|改为CREATE_NO_WINDOW后，真实控制点、目标操作、原始detector、OS退出和I/O闭合成立；不是正式CPU8资格|

C#真实编译成功，compiler PID39212、3个观察身份关闭。LauncherCapture.dll为39424B，SHA256 1999a1c78c26e88c30a0ea9c3a8d604acba20dccec74a979af5104af39cd769e。仅保留compiled证据及实际CPU launcher使用，不混入source-only导入树。错误的首次DLL快照序列化字节单独保留并纠正，未重编译或覆盖历史证据。

D0预约19/20，独立从原始启动重算实际18，包括两次CASE_BEGIN前/控制点前失败。停滞组第二项预约未用；没有用换根、重置额度或漏登记获得通过。全部失败还包括只读审计导入/现有清单冲突、旧fixture未登记新检测到的freeze事件等；原始工具stderr和失败摘要均保留，未重跑已成功原生case来掩盖审计错误。

## CPU回归与适配范围

原92项交付回归：14 registry、11 identity、31 entry、30 capability、6 exception。另有11项预算、5项生产exception/身份集成、7项bridge反事实回归。首轮复审修复后新增21项生产路径反例；与31项入口回归合并的最终52项运行全部通过。中间出现1项旧测试fixture登记错误，失败保留，隔离fixture后重跑52项通过。上述是不同时间/源码绑定的具体测试记录，不将重复测试相加声称独立新增样本。

本轮修改14个task-local文件，详见 development/FINAL_ADAPTATION_DIFFS.json：
- bridge.py：UTF8输入读取、CPU PowerShell控制台创建方式。
- churn_helpers.py：200-worker观察器门槛的console创建方式。
- cpu8_audit.py：真实异常继续策略及PID+创建FILETIME身份重建。
- cpu8_supervisor.py：未知actor总账字段保持null。
- source_guard.py：独立枚举原始启动并核对前瞻预约、漏账和上限。
- integration_gates.py：封存D0快照的完整成员认证、原raw_audit和实际qualify重算。
- cpu8_monitor.py / tool_binding.py / verify_cpu8.py：非空外层资源流、有效间隔、真实命令与终端回执关联。
- freeze_cpu8.py及四个测试文件：相应绑定/故障测试。

冻结科学数值后端和旧内层watcher/controller/launcher的detector、100ms标称周期、1秒有效覆盖、封存、pending completion、GO和清理判据均未改。新外层5秒守卫不替代内层1秒。本轮健康外层两个采样流最大有效空窗分别1,010,370,900ns和1,010,252,900ns，只按其5秒外层标准记录，不能报告为一秒以内。

## 正式八项

|次序|case|状态|实际producer槽位|
|---|---|---|---|
|1|normal_single|UNSTARTED|0|
|2|normal_transition（原定义8对A→B、16唯一槽位）|UNSTARTED|0|
|3|terminal_pending_completion|UNSTARTED|0|
|4|frozen_input|UNSTARTED|0|
|5|late_closed_slot_write|UNSTARTED|0|
|6|resource_read_failure|UNSTARTED|0|
|7|directory_read_timeout|UNSTARTED|0|
|8|journal_write_failure|UNSTARTED|0|

全部因最终独立clean缺失而未准入。D0输出没有填充本表。没有执行confirm.py、完整19项、57项、measured三小时或其他测量。

## 实际成本和缺失

从第一次准备2026-10-18T13:24:09.005Z到记录停止，4020.011秒，未超过D0的5400秒。两次完整独立复审墙钟629.7793706和497.5158338秒，合计1127.2952044秒；分别174和110个身份全部关闭，工具会话实际退出0，但报告均为findings。

可独立从命令观察器重建的834个去重身份全部有实际OS退出，已覆盖寿命和9423.0304473秒。它们是有限观测前缀，不是整机或全任务进程总数。原生actor/监督器有各自独立流；外层observer/watchdog自身、shell/工具宿主、早期预检/便携测试及交付工具的部分OS生命周期仍UNKNOWN，不能用工具退出码填0。两次代码复审服务使用单列，不属于工作负载模型请求。

资源峰值见 delivery/OBSERVED_RESOURCE_PEAKS.json。第二次复审观察到的聚合RSS峰631590912B，observer峰25919488B；各故障限额smoke单独标记。实际派生存储、归档、恢复和尾部工具成本见REMOTE_RESTORE.json、TAIL_EVIDENCE.json及FINAL_DELIVERY_STATE.json，不把早期前缀当作最终预算。至少256MiB证据/恢复预留，另有导出保守预留；不删除历史数据。

## 原始重建、恢复与认证

LEGACY_RAW_AUDIT.json保留原始输出：normal/journal两个D0的NOT_REACHED（正式源码/构建绑定未准入）以及此前退出0但无controller的EVIDENCE_MISSING。旧原始审计所覆盖进程前缀valid=true不等于全任务总账成立，也不提升正式资格。

RECONSTRUCTED.json由原始通知、控制点、OS事件、资源与预算重建；delivery/RECONSTRUCT.py仅为阻断态只读交付驱动，调用包内原raw_audit及原生门槛/身份审计器。它没有把部分结果转成CPU8 PASS。远端原始ZIP实际下载到全新目录，每个清单成员验哈希，使用包内未修改审计器在-I/-S/-B隔离环境重算并逐字节比对。精确归档和恢复结果由尾部认证文件给出；只有实际完成恢复后才发布对应回执。

源码提交的116个文本文件和39424B DLL已远端回读一致。后续证据提交、归档SHA、实际恢复成员数、重算SHA、最终工具结束和总墙钟由最终交付状态绑定，不能回填更早批准时间。

PR115保持d04b41e03b1fcd747851edb6aed3b4c40c544a5d；PR117保持08ec85f4a2c58e53a6dde4a230d686930dc7e600。三小时UUID、6214e73d与14a37e28的全部失败、缺失退出和历史文件字节不变。本轮只增加新UUID实现/结果目录。

GPU查询、GPU初始化、GPU插件、工作负载模型读取/请求、科学原生启动和图计算均为0。没有论文/main/RTX/release/自动化改动，不合并，不自动开始后续。结果不是CPU8_INTEGRATION_PASS、ENGINEERING_READY、旧完整确认或论文证据。
