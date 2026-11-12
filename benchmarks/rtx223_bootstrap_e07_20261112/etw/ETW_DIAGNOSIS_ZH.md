# ETW 错误 5 的定位与待批准步骤

以 PR #230 的 `45a867d6ca9300bd4080291db370017953c1ec50` 为起点，保留 e06。两次新构建均冻结 4,502 个输入和实际头文件/链接对象，没有启动数值 DLL、NVML、CUPTI 或 CUDA。诊断 DLL 只普通导入系统 DLL。

在当前 Windows 登录身份，带阶段回执的第一版证明 StartTraceW、OpenTraceW 及消费线程创建都成功，错误 5 出自 `EnableTraceEx2` 启用 Microsoft-Windows-Kernel-Process（GUID `22fb2cd6-0e7b-422b-a0c7-2fad1fd0e716`，process/image keywords `0x50`）。只读的 `EventAccessQuery` 查询该 provider 的权限描述同样返回 5，未取得可分析的 ACL。当前 token 的管理员组为仅用于拒绝，Performance Log Users 已启用；未提升 token 或修改任何权限。

第二版先启用 provider，再打开 consumer。它仍在同一 EnableTraceEx2 返回 5，但失败时能够用自有会话句柄停止采集，ControlTraceW 返回 0；未打开 consumer。随后只读按固定名称查询未见会话。该代码修正了错误路径的收尾顺序，没有让当前身份取得 provider 的访问权。两次失败分别见 `DIAG_001.json`、`DIAG_002.json`，权限读取见 `PROVIDER_ACL_READONLY.json`。

当前最小下一步为**一次需用户确认的提权 CPU-only 检查**，运行固定的 `Request-Elevated-EtwCpuSmoke.ps1`。它发起隐藏窗口的 UAC 请求，执行固定的 `Elevated-EtwCpuSmoke.ps1`；后者核对解释器、CPU smoke 源码及 DLL 摘要，加载仅 ETW 的观察器，再创建一个受控 Python CPU 子进程并核对进程起止、映像及丢失记录。输出写入新文件，已存在就拒绝覆盖。没有数值 DLL、GPU、模型入口，也没有 group、ACL、registry 或 service 写入。是否成功仍待实测。

提权检查通过后，其身份摘要与当前普通 token 不同。同一批准运行入口的其他 CPU 隔离、Job 和文件访问测试必须在拟使用身份上核对；CPU ETW 成功本身不会放行 B。用户另行确认提权范围之前，两个脚本均未启动。

新版观察器 SHA-256 为 `e9e8a5f0a375f7d793104ce489a68db28ebcc3eae7c7a3b43b64f7b2e69366f2`，源码和命令绑定见 `build-002/BUILD.json`、`RECIPE.json`、`FROZEN_INPUTS.json`。smoke.py SHA-256 为 `b1e367f3acc79f62a87693ca7abf70858476896424625279b283570654ba2656`。真实启动入口仍须绑定新的完整 release，不能沿用 e06 旧 observation.dll 的摘要。

微软说明跨进程 provider 启用受到 ETW 权限约束，支持管理员及获授相应权限的 Performance Log Users 等身份。现有证据定位到了拒绝发生的 API，尚未证明具体 provider ACL 内容或提权后结果。[EnableTraceEx2](https://learn.microsoft.com/en-us/windows/win32/api/evntrace/nf-evntrace-enabletraceex2) · [StartTraceW](https://learn.microsoft.com/en-us/windows/win32/api/evntrace/nf-evntrace-starttracew)
