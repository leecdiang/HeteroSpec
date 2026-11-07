# PR119 CPU8 integration — ENGINEERING_BLOCKED

锁定远端提交：`b59545aaff20eba93c82a21029c252104144f9fc`。独立任务 UUID：`6214e73d-2da5-455c-b133-b0d246beb6fd`。本地根：`C:/hs/b570-capability-v1/6214e73d-2da5-455c-b133-b0d246beb6fd`。保持 Draft。

## 停止原因与执行冻结

最后修订的 `source/stall_supervisor.py:3` 在达到暂停/停滞控制点之前抛出 `ModuleNotFoundError: No module named 'win'`。迁移入口遗漏了显式 runtime 导入路径；这是本次适配错误。真实 watchdog 没有被暂停，没有测得“身份/RSS仍可读但进度过期”的拒绝，也没有开始下一用例。该项为 **NOT_REACHED**，不能称为预期故障通过。

源码修订0/1/2已登记并用尽，按协议停止，没有第四修订、补跑或换根。停滞尝试的 harness/watchdog/supervisor 三个真实身份都取得OS退出；Job为空、句柄关闭，20秒救援没有触发。此清理事实不替代预定控制点。

**没有生成执行 CAPABILITY_FREEZE.json/F0，没有批准的正式入口。** SOURCE_SNAPSHOT.json仅为未准入候选的证据快照，不是执行冻结或独立批准。停止原因为 NATIVE_STALE_GATE_NOT_REACHED / SOURCE_REVISION_BUDGET_EXHAUSTED / ADAPTER_REVIEW_BLOCKED，不是6小时墙钟超限。

## 实际准入与门槛

|检查|实际状态与证据|
|---|---|
|远端来源/修复复审绑定|23份获取文件，19项受绑定摘要全部匹配；原修复 runtime 的 scoped-clean 有效，但不覆盖本轮新 bridge|
|真实环境|批准 Python3.12.10、Windows/AMD64；GetWindowsDirectoryW/GetSystemDirectoryW实际成功；仅记录环境键存在性|
|原30项便携回归|30/30通过；不是Windows八项资格|
|健康C1/C2/C3|3/3真实通过，5 actor实际闭合；修复版原始只读核验器返回 DEVELOPMENT_EVIDENCE_PASS|
|冻结替换原生门槛|4/4通过：source+manifest一同替换、子进程前替换、只改source、缺初始摘要，实际win.freeze_check对应拒绝|
|watchdog停滞|NOT_REACHED，入口导入失败；真实暂停、过期后首次tick、后续准入拒绝均未建立|
|新增预算/回执补充回归|UNSTARTED；原30项中的预算反例已通过，不能据此宣布完整新增门槛通过|
|bridge健康/日志失败D0 smoke|2项均UNSTARTED|
|七项原始副本bridge反例|UNSTARTED，源码保留为候选，未伪造PASS|
|最终完整独立复审|BLOCKED；第一次实际复审被观察器资源守卫中断，无最终结论；第二次未启动|
|正式八项|0启动，8项全部UNSTARTED|

## 正式八项矩阵

|次序|用例|状态|
|---|---|---|
|1|normal_single|UNSTARTED|
|2|normal_transition（8对A→B、16唯一槽位）|UNSTARTED|
|3|terminal_pending_completion|UNSTARTED|
|4|frozen_input|UNSTARTED|
|5|late_closed_slot_write|UNSTARTED|
|6|resource_read_failure|UNSTARTED|
|7|directory_read_timeout|UNSTARTED|
|8|journal_write_failure|UNSTARTED|

计划24个producer槽位，实际0；没有运行confirm.py、完整19项或57项确认。旧raw auditor返回57项确认缺失是未执行的计划状态，不是启动了确认。没有改变1秒内层判据，也没有用5秒外层能力资格替代它。

## 实际工程、编译、失败及审查

只在新根部署必要旧依赖。旧内层仅3个文件变化：common.BASE显式根绑定；raw_audit.ORIGINAL恢复地址映射；launch.ps1的根准入参数和独立compiled DLL位置。原watcher/controller/supervisor/C#捕获逻辑不变，100ms/1秒、sealed guard、pending completion、fault/detector判据未降低。新增15份source文件及44份最终运行源码/依赖的摘要、理由见ADAPTATIONS.json和SOURCE_SNAPSHOT.json。这些是**未通过门槛的候选**。

- 第一次CPU编译退出1（CS1504），保留完整实际参数/输出和编译器OS闭合。规范化Windows反斜杠路径后第二次编译成功，没有改C#计算/捕获源码。
- DLL为39424B，SHA256 `4994e1fb9f09a986fc9223819285cf6093a56bbd9d3c0f82df28f3b6c7e53955`；csc.exe SHA256 `eca02e6b15cde93009a59a3d129d5a77fb5008f2e1cf62cf573b6737c747ecc3`。仅为compiled证据，未完成launcher/八项执行验证。DLL未放入source-only导入树。
- 第一次独立实现复审通过真实Codex进程启动；其观察区间约15.2162041秒，未产出最终报告。观察器把审查辅助进程也套入8进程门槛，失败时列出10个尚未闭合身份；触发读取没有持久保存完整资源值，不能声称已分解全部触发因素或完整资源合格。
- 原失败观察保留为INCOMPLETE。后来对16个登记身份进行真实只读查询，全部返回NO_SUCH_PID；这证明查询时这些身份已不存在，**不补齐10个缺失的历史退出FILETIME**。
- 最后修订加入辅助/用例角色区分、异常路径debug事件清理、源码库存/预算与原始审计适配，语法检查34份Python通过。但未取得最终独立 scoped-clean；停滞入口仍失败，因此没有复审后放行或正式冻结。

## 预算与生命周期范围

第一次准备UTC为2026-10-18T07:00:10Z；最后原生失败观测UTC为07:30:13.269Z；收尾开始UTC为07:32:49.415Z。实际总墙钟与收尾截止前沿见最终计账，不能把进程寿命和当工程墙钟。

D0预约15/20，已保留7个原生CASE_BEGIN（健康3＋冻结4），另有1次已启动停滞harness在CASE_BEGIN前失败；保守实际尝试收费8。剩余预约保留未启动，不重新分配。三次源码修订用尽；1/2次独立复审尝试，没有最终clean，不隐瞒未完成。

去重后有31个独立观测身份、21个实际OS退出；已覆盖寿命和11.4289346秒。10个复审身份缺历史退出时间/寿命，保持null。外层observer/watchdog自身、命令shell、工具宿主及部分预检/审计根进程也无完整外部OS覆盖；全任务启动/寿命完整总账为UNKNOWN，不填0。已保存样本的聚合RSS峰值369922048B；它不能替代缺失触发样本或完整任务峰值。

旧raw_audit实际执行并完整保留：process_ledger_valid=false，原因为unclosed processes in published prefix；其25启动/15闭合、3.370283秒只是该前缀，不是全任务。收尾只读核验器逐项重建健康/冻结/停滞未到达、31/21身份及矩阵，并对未修改旧raw_audit重算逐字节等价JSON结果，均保持ENGINEERING_BLOCKED，没有把旧全账本失败改成PASS。

## 归档与最终交付

全部旧原始数据、失败、协议/审查获取字节、源码修订与候选、真实编译DLL、工具请求/完整结果、OS事件/资源流和未启动矩阵纳入本轮新归档；只读收尾核验器不加载DLL/原生插件。包和manifest建立在worker退出后的不可变前沿，后续打包/恢复/远端回执单列，防止自我哈希递归。

远端上传、实际下载到全新目录、逐成员认证、包内未修改核验器在-I/-S/-B隔离导入环境重算的实际结果由REMOTE_RESTORE.json和FINAL_DELIVERY.json记录；当前文档前沿不预填成功。没有旧归档重新打包，也没有恢复旧三小时运行。

GPU查询/初始化/插件、工作负载模型读取/请求、科学原生启动与图计算全部0。1次代码复审控制服务调用另列，不是工作负载模型实验。PR115/117、旧三小时UUID和历史PR119字节与结论不变；论文/main/RTX/release/自动化不动。最终状态为ENGINEERING_BLOCKED，不是CPU8_INTEGRATION_PASS、旧完整确认、ENGINEERING_READY或论文资格。任务收尾后不自动执行任何后续。

## 最终交付前沿与未闭合范围

根外不可变回执：`C:/hs/b570-capability-v1/tail-6214e73d-2da5-455c-b133-b0d246beb6fd/COMPLETION_RECEIPT.json`，SHA256 `ebae2a133ea62571b039f0e0fc6eeb1b82c756ae528a61e128cc27f448394d4f`。它绑定真实失败工具结束（exit1）、审计/恢复结束（exit0）、worker清单、源码快照及恢复报告摘要；execution_freeze_sha256明确为null，required_execution_gates_satisfied=false。它是**阻断结果的交付回执**，不填缺失执行F0，也不能授予PASS。

实际观察前沿 2026-10-18T07:44:33.311Z：总任务2663.311秒；从最后原生失败起的保守交付时间860.042秒。两个受控新根共5393185B逻辑数据、按实际4096B簇及逐文件/目录保留计账8624128B；连同256MiB证据/恢复预留为277059584B <1GiB。只有两份ZIP（原归档和真实下载），尾部采用独立JSON证据包。后续发布/回读开销继续由FINAL_DELIVERY_STATE.json记录；如最终超过6小时，必须改报预算阻断。

实际post-stop工具文件哈希、18次正式命令请求和所有原始结果另列尾部；缺失的外侧OS创建/退出仍为null，未用session或exit_code冒充。不会再启动开发用例、独立复审或任何实验。PR115/117与历史三小时字节保持不变，PR119保留Draft。
