# 观察器的实际边界

ETW 父控模块订阅本机 Microsoft-Windows-Kernel-Process 的进程与映像事件。子进程创建前开始订阅，得到挂起子进程 PID 后筛选之前暂存的事件，再以创建 FILETIME 核对进程起止身份。程序检查实际映像路径、阶段快照、丢失计数与事件尾部。固定缓冲区或队列溢出、解析失败、意外身份都会使准入或结果失败。这些检查能发现已观察到的加载，无法在任意 DLL 构造器开始前拒绝其中的物理提交。

CPU ETW 试验使用编译后确认仅导入系统 DLL 的 observation.dll，未调用 NVML、CUPTI 或数值 DLL。普通回执和绑定 Windows/登录身份的回执都记录了启动链返回 5；未创建子进程。收尾状态 4201，随后按固定名称只读查询未发现该收集会话。当前身份的 Performance Log Users 组已启用，Administrators 组标为仅用于拒绝。仅凭组名不能断定 provider 已可用，也未定位到具体是哪条 Windows 权限或 provider 策略造成错误。强退后可能得不到最后的 ETW/CUPTI 记录；将来若固定名称仍被占用，拒绝重新使用，按已核实的会话归属处理。

零能力 AppContainer 的 CPU 试验记录 CreateProcessW 返回 2。普通 Job 以同一 CPU 替身执行成功；复核时该文件仍存在。按包名派生 SID 后只读检查，当前用户的 AppContainer Mappings 下未发现该 SID 的注册项。这是排查线索；尚未用对照试验证实错误 2 的原因。本轮未注册 profile、提升权限、放宽模型目录 ACL 或运行真实探针。

执行时使用的冻结文件以实际落盘路径和文件 ID 为准。模块哈希针对文件字节，参考部署、宿主内核和可信操作者构成信任前提。隔离进程的受限 token、Job 和匿名管道用于限制经冻结 runner 发起的一次运行。它们不认证任意同用户重建的父进程，也不能阻止有权限的其他程序自行调用驱动。Python 的启动及既有模块缓存同样需要可信入口，进程内的文件复核不能倒推认证此前的内存内容。

[磁盘输入绑定](../build/REVIEW_IDENTITIES.json) · [Windows ETW 会话](https://learn.microsoft.com/en-us/windows/win32/etw/configuring-and-starting-an-event-tracing-session) · [NVML 设备查询](https://docs.nvidia.com/deploy/nvml-api/group__nvmlDeviceQueries.html)
