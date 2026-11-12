# B1 父控制器与 CPU 故障证据

**默认拒绝。** 本目录没有 GPU 启动许可。本轮只运行 `test_runner.py` 的固定 CPU 替身、Windows 包容性测试和磁盘身份复核。真实探针、NVML 设备查询、CUPTI、数值 DLL 加载均未执行。原 e02 native 门禁和生产账本保持原样。

## Windows 控制边界

父控仅接受固定解释器 `D:/HeteroSpec-PC/python311/python.exe`，使用 `-I -S -B`，脚本为 `runner.py`。入口需要外部明确批准回执的路径和从批准渠道取得的 SHA-256。省略任一项即退出。此处的信任边界为持有该 Windows 账户、控制调度窗口并转交用户授权的操作人；任何知道字段格式的人都可以计算文件摘要，该摘要本身不认证人。没有实现远端签名服务。不得把“没有旧任务”或批准 CPU 准备的答复填写为 B 授权。

批准回执采用 `heterospec.e06.owner-approval.v1`。它绑定源码固定的 `consent`、用户的 `owner_confirmation`、`nonce`、`attempts=1`、完整 `device_uuid`、合同中两个带时区的 `window` 端点及 `release`、`contract`、`etw_smoke`、`appcontainer_smoke` 四份文件的绝对路径和 SHA-256。回执必须来自已批准唯一操作及风险的操作人，合同与 release 中实际文件全部须能复核。**当前没有这样的回执。**

即便将来有批准，仍须在窗口内持目标设备 UUID 的全局 mutex 和独立 `D:/HeteroSpec-PC/rtx223-bootstrap-b1/B1.lock`，先后检查旧 marker。旧 `RTX_EXPERIMENT.lock` 仅读取。操作人隔离所有可能的派发源后，将 60 秒内的窗口观察留在固定状态目录中的 `dispatch-clearance.json`。其中 `nonce` 与批准一致，`observed_utc`、`device_uuid`、`source_chats=["221","223-interrupted","223-successor"]`、空 `pending` 和 `other_leases`、合同结束的 `fenced_through`、实际的 `dispatcher_ownership` 和摘要绑定的 `host_snapshot` 均须齐全。宿主快照涵盖 Windows 进程、计划任务、服务，字段沿用 e05 公共摘要。父控持锁后再做当前主机进程枚举及规范账本/sidecar 检查。新 mutex 只约束参加该协议的 runner；有可绕开的提交者时没有独占权。

独立 B 状态目录拒绝重解析点并持有祖先句柄。父控以 CREATE_NEW 建立 `attempt.jsonl`，先落盘 RESERVED，再创建单一子进程；进程创建、阶段许可和终态均需持续写入并刷盘。已有文件一律拒绝，进程号不用于回收不明进程。短写时将实际写入的前缀计入限额并封存文件，不拼接伪造的完整行；重开保持 UNKNOWN 并禁止重试。账户拥有者须保护这份永久记录免被手工删除或回滚。

独占 Job 不继承、kill-on-close、active limit 1、process commit limit 2 GiB；原子 CreateProcess 同时携带 Job 列表和 pipe handle 白名单。生产探针另带无 capability 的专用 AppContainer SID。暂停状态下复核成员、PID/创建时间、包 SID 与零能力，通过模拟该实际子 token 打开模型目录/模型文件（仅请求读取权限，不读取模型字节），必须获得 ACCESS_DENIED，并测试批准的 DLL 根能被读取。实际数值二进制没有接收模型、外部参数或创建其他工作负载的协议。没有自动修改包配置或 ACL。父控的状态和证据目录应由上述操作人控制，子进程无额外写入授权。

批准摘要涵盖解释器及其 1,098 项磁盘输入，运行入口复核 Python 搜索路径、覆盖文件的缺席和成员清单；所有准许映像及候选路径须能以防写/防删除句柄固定。本轮文件测试在同一进程内固定了 1,143 个输入。Python 及 Windows 已在入口前启动，因此还需操作人在可信运行环境中从已审查的解释器启动；文件检查不能重构预先执行的代码或进程内存。

80 秒停止新工作和 90 秒终止自有 Job 是停止触发条件。工作线程卡在 IPC、观察器或系统调用时，独立 watchdog 仍请求终止本 Job；收尾仍卡住时退出父控，最后 Job 句柄关闭，单次 reservation 保留为 UNKNOWN。Windows 调度延迟、驱动清理及设备物理工作仍没有可证明的硬时长或 launch 上限。

## CPU 结果

| 检查 | 结果与范围 |
|---|---|
| 正常替身、六阶段故障、错误 UUID/设备数、丢失/不完整/无归因/迟到活动等 | [34 组最终 CPU 检查](cpu-checks/run-005/RESULT.json) 通过。正常替身 SHA-256 为 `8a5cc2607dfdf3e59902dbb359e09e20e4348aa736b7bd3fac788fa996f449cb` |
| 真进程与故障边界 | 父控在创建前、恢复前后退出，核对自有进程消失。挂死观察器由独立 watchdog 处理；第二 CPU 进程收到 ERROR_NOT_ENOUGH_QUOTA (1816)。短写实际留下 9 字节，首个许可前短写的最后完整探针行是 READY。畸形/缺 END/尾随/非零退出/静默超时均拒绝 |
| Job 计数延迟 | [原失败](cpu-checks/run-004/FAILURE.json) 保留。进程句柄已 signaled 而 Job 的 active 计数仍可暂为 1；后续在预算内等到 active=0。不能核实则记 UNKNOWN |
| AppContainer 真 CPU 替身 | [同一 Windows/控制器身份采样](cpu-checks/acl-002/APPCONTAINER_CPU.json) 在原子创建时得到 WinError 2。测得保护范围 54 个路径，尚未执行子 token 的实际读拒绝及 DLL 读取检查。未据错误码推断唯一原因 |
| 普通文件身份及句柄 | [离线文件实验](cpu-checks/FILE_PINS_001.json) 固定 1,098 项 Python 输入、12 个根映像、32 个额外候选及 API-set schema。没有普通加载这些映像 |

在实际控制器 Windows 身份、同一系统启动和嵌套 Job 范围内，需要分别取得 ETW 与 AppContainer 的正向 CPU 凭据。runner 验证各自的文件摘要、时间、runner 上下文摘要、目标二进制身份和结果字段，然后在真正执行时再次检查实时状态。当前 AppContainer 和 ETW 结果均不能满足启动门槛。没有资格实验、性能计时或自动升级。
