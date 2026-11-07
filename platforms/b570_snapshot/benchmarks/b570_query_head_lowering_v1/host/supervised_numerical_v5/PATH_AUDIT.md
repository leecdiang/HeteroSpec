# 启动与写入路径审查

审查基点：a2494a83cd77c18a7fbbb5df40cd7e6ed715a123。v4的 LAUNCH_CONTEXT.json、RESULT.md、storage.py、supervisor.py、execute.py 和 POLICY.md 均已读取。v4直接路径证据是：外层 Start-Process 把控制器 stdout/stderr 重定向到源码根 `supervised_numerical_v4/results/`；production watcher 随后拒绝该目录变化。原记录未保留 action/writer/通知时间，不声称唯一还原每一次写入。v4失败根、F0、回执及3.156秒计账保持原样。

v5两个保护根：

- 源码/登记：`C:/hs/b570-query-head-lowering/benchmarks/b570_query_head_lowering_v1/host/supervised_numerical_v5`
- 所有本轮构建、CPU测试及数值宿主输出：`C:/hs/b570-query-head-lowering/benchmarks/b570_query_head_lowering_v1/host_outputs/supervised_numerical_v5`

唯一独立日志区域：`C:/hs/b570-launch-logs/b570-supervised-numerical-v5-20261016-01`。它不在两个保护根内。准备阶段不创建该run日志目录；未来已批准启动器独占创建，已存在即停止。拥有者为冻结 INITIAL.cpu_modules 测试回执所记录的当前Windows SID（实际值绑定进F0），运行前核对SID及祖先无reparse路径。

|写入类别|位置|允许阶段及边界|
|---|---|---|
|源码、F0、完整wire、分析器、参考清单、构建二进制、CPU测试回执|v5源码根、OUT/build、OUT/CPU_TESTS|全部在GPU授权前准备完成。数值控制器活着时不得修改，也不运行构建/CPU测试/交付工具。|
|外层控制器stdout/stderr|独立日志区的CONTROLLER.stdout.log、CONTROLLER.stderr.log|仅拥有它们的PowerShell启动器通过实际重定向管道写。禁止写源码/results、非活动槽位、OUT根其他位置。外层PowerShell自身若stdout/stderr是指向保护根的磁盘句柄，在控制器启动前拒绝。|
|授权、预检查与所有权|独立日志区INITIAL.json；数值RUN/AUTHORIZATION.json、PREFLIGHT.json|INITIAL记录实际启动时间、调用参数中精确批准SHA、Windows SID、PID、句柄容量及模块身份。RUN回执由冻结控制器在首个Lease前写完；不预填历史批准时间，不改变旧F0状态。外部交付工具不在运行期间追加源码/results。|
|每槽登记/运行状态|RUN/NNN-ATTEMPT.json；当前活动槽位STATE.jsonl等|登记文件由控制器在该槽watch启动前写完；活动期间只允许当前槽位。下一槽必须等上一槽watch完全关闭后再登记。|
|原生宿主、monitor、auditor输出与进程生命周期|RUN/当前slot下的raw、stdout/stderr、MONITOR、AUDITOR、LIFECYCLE、接收回执等|原监督器实际创建/追加，watcher完整保护其他路径。退出观察、后置审计、生命周期回执与独立FILETIME保持原边界；失败缺失不补造。|
|目录变更通知日志|当前slot/WATCH_*.jsonl|仍由字节不变的production watcher生成，不把results加入白名单，不删未知写入/通知溢出/清理失败检查。|
|临时文件|准备阶段CMake构建树及编译器工作区；运行期仅匿名有界管道及内存JIT|C#捕获DLL提前编译，运行期Add-Type只加载已哈希DLL，不启动编译器。Python禁写pycache。没有批准运行期通用临时文件目录；新增外部日志文件名或目录属于失败。系统编译器临时工作是准备成本，不宣称枚举所有OS临时文件。|
|外部日志审计与封存|控制器退出后，v5源码/results/launcher|独立纯CPU审计工具核验关闭、大小、哈希和全部命名成员，再复制/归档。旧结果和其他封存目录从不写入。|
|原始归档、CPU重构、Git、远端认证、PR交付|控制器退出后新增results/及独立CPU工具|运行期间禁止这些工具向受保护根写入。所有源/原始数据只读；复制、压缩包及外部原件均计账。|

外部区域前瞻容量：每流软阈值1MiB，硬预留2MiB，日志事件文件硬上限8MiB，INITIAL及CLOSED各128KiB，整体16MiB，连完整外部导出预留共32MiB。两个原始重定向管道是有背压的操作系统管道；每流最多一个4096B已读块，实际输入/输出管道容量和须已取得且<=65536B，否则GO前HOLD。跨软阈值先停止整个拥有的Windows Job，再排空所有管道尾部，不能通过截断日志来通过。上限、实际创建/追加计数、关闭、PID、容量、SHA256及归档认证都保留。

匿名管道不是无限磁盘日志：进程组终止前不继续消费新数据，已进入管道的数据量受实测容量约束；2MiB硬预留大于1MiB软阈值+4096B在途块+65536B管道上限。CPU超限测试逐帧记录已完成flush的生产者ack，核对这些已产生的完整帧均存在于关闭日志；最后未完成ack不冒充完整记录。磁盘IO/API失败、读者未EOF、未知外部文件或无法取得容量均使日志资格失败，原文件不删除。

Windows Job在控制器等待LAUNCH_GO时接管其后代，避免身份/管道设置完成前启动数值代码。控制器退出后，job进程记账允许最多3秒有界清理等待，记录仍可见的PID/名字；已退出进程的名字无法获取时保留PID及null，不猜测名字，也不凭名字白名单放行仍活着的进程。仍有成员即失败并结束整组。此为退出后清理，不更改任何一秒运行期采样资格。
