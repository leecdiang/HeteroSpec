# PR119 B570 CPU8 continuation v5 — ENGINEERING_BLOCKED

锁定来源：`d9b8a2cd0ac6f460781611dc45d31bc33b632a07`。独立UUID：`647fc68d-b3ad-43da-82e2-74037e7f2f35`。原始包及本轮实现提交：`8fe549988fe550c11dd37bb55f6e3d22f8e867ec`。保持Draft。

**未完成正式八项，0/8启动；没有执行F0，没有最终完整scoped-clean。** 已自主修复开发阻碍并保留失败；第三轮复审超时后，累计进程寿命余量不足以安排下一次完整复审、正式八项与收尾，因此停止开发。工程墙钟没有耗尽；没有按旧“两次复审”计数规则停止。

## 实际接入与门槛

|项目|实际结果与范围|
|---|---|
|来源与四入口|141份远端输入认证；真实Python/PowerShell/C#及reviewer身份核验；四入口Windows隔离启动预检通过|
|观察器smoke|正常21/21身份关闭；case限额负例21/21、review限额负例65/65；预定live_process_count原因及空Job由原始审计核对|
|churn / 断点|200-worker churn共201身份，8个额外PID复用身份；应用断点负例实际未被吞掉|
|C1/C2/C3|3/3，5个actor；属于能力门槛，不替代CPU8内层一秒资格|
|冻结替换|4个实际隔离反例按指定原因拒绝|
|watchdog停滞|实际暂停后身份/RSS仍可读；进度年龄5,019,809,500ns时拒绝下一用例；20秒救援未触发；所控Job空|
|D0 bridge|独立normal与journal_write_failure两个限定D0控制点完成；原raw_audit的NOT_REACHED、审批缺失及总账限制原样保留；不转成正式PASS|
|CPU回归|基础92、新v5的28、适用审计/桥接等回归实际运行；最新组合53/53。不同运行有重叠，不相加声称独立总数|
|CPU构建|实际本轮C#编译；39424B DLL，SHA256 `c15dd72cb30bcd8dbb614bef08e826f5b3bac96058ef0e4aa14ea050a074a948`。保留compiled证据；未变更数值后端|

外层能力门槛采样最大有效间隔约1.010秒，适用外层5秒条件；**没有把它当成CPU8内层1秒通过。** CPU8正式三流监督及8对转换资格均未建立。

## 适配、失败与独立复审

实现候选加入：Windows junction别名夹具；精确封存树及根外归档；硬链接拒绝；累计PID+创建时间、工具上界收费与统一存储预留；只读恢复与完整字节重算。没有改变原内层detector、100ms/1秒、pending I/O或科学判据。

|记录|实际情况|
|---|---|
|003 / 004|隔离测试入口导入错误；随后两个Windows symlink夹具因WinError1314失败。修正调用并用真实junction反例后通过；原失败保留|
|020 / 024|部分旧回归的继承console输出未完整捕获；在新ID下捕获预算/身份实际输出，原缺失不补写|
|review1|完整结束，4项发现：1 P1、3 P2。实际观察器墙钟682.651s，158/158身份退出；不是clean|
|027 / 028|新增预算夹具的合成FILETIME过早，45/46；保留后修正夹具，46/46|
|030|缺少churn回执API观察UTC，保守收费持续增长，触发CAMPAIGN_LIFETIME_LIMIT；回归尚未进入即被拒绝|
|review2 / 031 / 032|按预算守卫停止；首个定向清理出现WinError5，未完整记录该次拒绝的唯一目标，不能断言唯一竞态原因。后续保留身份清理及原观察器证实168/168退出、Job空；根退出125，无最终审查报告|
|收费证据修复|原churn回执实际exit0及session8022不变；新记录仅使用真实NTFS持久化时间加保守预留作为收费上界。原API观察UTC和外层OS退出仍null/UNKNOWN|
|033 / 034|真实恢复配置路径、外部工具预算、下载字节/完整argv及元数据上界反例；最后53/53通过|
|review3|240秒硬截止，实际240.099754s；96/96退出、Job空、根退出124。没有最终JSON verdict，不能放行|
|交付失败|停止重构器首次误判原资源负例的结束格式，保留失败后仅修正归档重构器；服务对象JSON读取格式错误、批量tree HTTP500均保留，改用认证blob运输；没有重做原生实验|
|跨语言核对|首次JS Number解析损失大整数FILETIME精度，错误地多计2身份；原输出标记REJECTED并保留。无损整数重建与包内Python结果一致|

第三轮**部分意见**仍指出两处资格风险，不能当成完整最终报告：原根使用`--relocated`可能跳过当前预算检查；下载/隔离执行声明未在正式资格检查中充分关联实际工具返回。这些问题未获得最终独立clean。当前实现为未准入候选，请勿把归档恢复成功当成执行批准。

## 正式八项

|顺序|用例|正式状态|实际正式控制点 / detector|
|---:|---|---|---|
|1|normal_single|UNSTARTED|缺失|
|2|normal_transition（8对/16唯一槽位）|UNSTARTED|缺失|
|3|terminal_pending_completion|UNSTARTED|缺失|
|4|frozen_input|UNSTARTED|缺失|
|5|late_closed_slot_write|UNSTARTED|缺失|
|6|resource_read_failure|UNSTARTED|缺失|
|7|directory_read_timeout|UNSTARTED|缺失|
|8|journal_write_failure|UNSTARTED|缺失；限定D0不计入正式槽位|

正式PASS/FAIL均为0，8项UNSTARTED。没有复用旧运行根、恢复旧槽位或拼接历史PASS。

## 进程、墙钟与空间

停止前缀由包内只读审计器从原始OS事件重建：**809个唯一PID+创建FILETIME，809个实际退出，覆盖寿命14226.4939618秒**。实际下载包核验器另1身份，实际寿命5.3404004秒、退出0、Job空；无损独立重建合计**810已识别并退出，14231.8343622秒**。

登记的工具命令根与观察器自身等有生命周期缺口。预算另用保守收费，不能把收费单位称为完整OS进程总数。最后CPU计账前沿：
- 工程墙钟 **5299.239954秒**，含300秒引导上界；之后仅既有服务的元数据、Git和交付I/O，实际尾部时点见FINAL_DELIVERY_STATE。
- 收费启动 **899单位**；累计寿命收费 **20795.8175958秒**。另留360进程秒给最后命令/回调，上界 **21155.8175958 <21600秒**；其实际API回调在计账捕获后0.062秒结束。
- 当前分配上界229273600B；含256MiB收尾及64MiB导出预留的收费 **564817920B <1GiB**；两份完整ZIP。随后新增尾部文档单列并处于导出预留内。
- 全任务真实启动总数/总寿命、外层自身OS退出及全任务峰值RSS仍**UNKNOWN**。普通工具exit0没有被包装成完整OS生命周期。
- CPU已有监督记录按各自角色保留；没有取消ReadDirectoryChangesW或放宽内层1,000,000,000ns。

## 实际远端恢复与未修改核验器

[原始ZIP](RAW_EVIDENCE.zip)：**11884291B**，SHA256 `f0f45f4fb167db1f4bb47208ac61f2ab2e622f723f0e22f1c01dd46129961fed`，Git blob `2639eebba5116d3feabe4c4082019f43c06369d1`。ZIP共5439成员，其中5438个数据成员；清单只排除自身，SHA256 `75d0f3f6f283ded46bcd3e5aa53f9318e561cbfcb429062494b033c87a7ce739`。

实际从提交`8fe549988fe550c11dd37bb55f6e3d22f8e867ec`通过GitHub连接器取回20个认证Base64分块，到全新目录重建第二份ZIP。逐块字节/Git身份、完整ZIP、5438成员和清单自身均认证。125份实际发布源码/配置/编译产物完整回读一致。

包内未修改`source/reconstruct_stopped.py`，SHA256 `a4853c726f9f36803a7192c7379d94f90de50d86e80ce3fb21a35cf45d4af391`，在`-I -S -B`隔离环境实际运行，保留真实PID、创建/退出FILETIME、完整argv、stdout/stderr、Job及句柄关闭。**20070B重算逐字节一致**，SHA256 `41e81ace67b6a8b53c6cb29719bce27731cfed6895b1bb4d66ac794199ede477`。

[恢复原始回执](REMOTE_RESTORE.json)、[重构结果](RECONSTRUCTED.json)、[最终CPU计账](FINAL_CPU_ACCOUNTING.json)、[完整未启动矩阵](CPU8_MATRIX.json)、[实际源码回读](SOURCE_REMOTE_AUTH.json)。原始失败、未完成审查和所有缺失继续存在；恢复仅认证停止结果，不修复资格缺口。

## 范围与历史

GPU查询/初始化/插件、工作负载模型读取/请求、科学原生/图计算均**0**。独立代码复审3次另列。没有三小时soak、confirm.py、19/57项、论文、RTX、main、release、自动化或后续科学执行。

PR115保持`d04b41e03b1fcd747851edb6aed3b4c40c544a5d`，PR117保持`08ec85f4a2c58e53a6dde4a230d686930dc7e600`。所有旧UUID、三小时证据、旧缺失退出和失败不改写。新目录独立提交，PR119保持Draft。

最终结论：**ENGINEERING_BLOCKED；不是CPU8_INTEGRATION_PASS、ENGINEERING_READY、旧完整确认或论文证据。**
