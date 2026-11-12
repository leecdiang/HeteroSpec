# Windows RTX 5070 Ti · e06 无模型 bootstrap 交接

**B 的探针和独立 runner 已实现，真实执行为 NOT_RUN。当前宿主身份缺两项通过证据，执行门槛为 BLOCKED。** 父提交为 #223 的 `ba2b8734f60183c58b09c30163ea0eeb13fc009d`。只读回查了 e05 全部 16 个 Git blob 和 5 份旧账本。独立 B 账本尚未创建。e05 的旧会话排重保留其原时点结论。[父提交与旧账本回读](PARENT_READBACK.json)

### 实现与身份

最终探针源码在 [probe/v2](probe/v2)。无模型子进程先核对私有管道、Job 限制、固定 UUID 与截止，再逐步消费六个单次许可。先加载 CUPTI 并检查 API 28；再按绝对路径显式加载一次 `ggml-cuda.dll`，核对九个已加载模块，解析 cudart 中两个非转发导出。只调一次 `cudaGetDeviceCount`；结果必须为 1，才调一次 `cudaGetDeviceProperties_v2(..., 0)`，核对 16 字节 UUID 和设备名。最后释放数值根引用、关闭计量、flush 并核验。清理处理部分初始化和失败路径。入口没有模型参数、模型库、forward、显式 context 或主动 kernel。

[runner](runner/runner.py) 在指定解释器的隔离模式下工作。它核对外部批准摘要、合同、部署和文件身份，持有防替换句柄，在设备 UUID 互斥与专用 B 标记下用 CREATE_NEW 持久预留唯一 attempt。原锁只查，原账本只读。创建子进程时通过 JOB_LIST 同时完成挂起创建与入组，恢复前核验 PID、创建时间、成员数和受限 token。父进程独持不可继承的 Job 句柄，关闭即终止该 Job。在每个许可前校验观察状态、已加载模块和截止。没有自动重试、预算退款或恢复未闭合 attempt 的入口。[Windows Job 代码](runner/winjob.py)

| 产物 | SHA-256 |
|---|---|
| native-probe.exe，未运行 | `70fe177f4d7cdacbe25f73aaf27ef617f59f5832335708831185c5f76781b805` |
| cpu-probe.exe，只链接 main 与 fake | `8a5cc2607dfdf3e59902dbb359e09e20e4348aa736b7bd3fac788fa996f449cb` |
| observation.dll，仅父控 ETW | `a49b1a25555d9f31c04fe059d7d74a6df9605eb2c698671d0767943471d1b43d` |

两个探针的静态启动导入均只有 KERNEL32.dll。ETW 模块仅导入 ADVAPI32、KERNEL32 和 tdh。最终探针编译锁定 6,351 个输入，ETW 模块锁定 4,502 个输入；保留各次源码、命令、依赖及链接前对象摘要。runner 的三个 Python 文件、1,098 个解释器及标准库输入、候选数值栈和系统/驱动映像均绑定。12 个部署根包括九个项目依赖、CUPTI、nvcuda 与 NVML，另有 32 个精确路径的候选映像。静态非延迟名称解析缺项为 0；遇到意外动态或延迟加载的文件即停止。VCOMP 的历史参考身份仍未知。[冻结身份总表](build/REVIEW_IDENTITIES.json) · [运行候选清单](build/DEPLOYMENT.json)

### 预算与可观察范围

| 边界 | 实现与证据 |
|---|---|
| 进程和内存 | 一个新增数值子进程，Job active limit 1、禁止 breakaway、process commit 2 GiB。真实 CPU Job 测试中，超额提交返回 1455，创建第二进程返回 1816，退出后 active=0。[实测](observation/JOB_LIMITS_CPU.json) |
| 记录与存储 | runner 控制的日志/回执总计 64 MiB，保留 64 KiB 写终态。管道有帧长限制。应用供应给 CUPTI 的缓冲固定为 4×4 MiB。库内部缓冲、Windows 或 driver 自行产生的磁盘和内存活动只能按其各自边界解释。磁盘入场余量 2 GiB，运行低于 1 GiB 即停。 |
| 时间 | 从创建前的单调时钟起算。80 秒停止发放新的工作许可，子进程另查同一 tick 截止，清理可继续。90 秒触发终止自有 Job。OS 调度、正在进行的库调用、设备卡死和驱动清理均无可证明的即时完成保证。无法确认退出/日志尾部时保留 UNKNOWN 和已消费的 attempt。 |
| 显存与设备 | 父控使用非 CUDA 的 NVML 读取目标卡、驱动、显存和可见计算进程。入场空闲至少 8 GiB；低于 7 GiB、已用较基线增长至少 1 GiB、遇外来计算进程、采样失败或间隔超过 1 秒即停止。采样与 WDDM 可见范围无法给峰值显存、全部类型的 GPU 工作或隐式 placement 建立硬限。[观察器](runner/observation.py) |
| 物理工作 | CUPTI 在探针计量初始化成功后提供回调和活动记录，按两次 API 的关联号、PID/TID、顺序及返回值验证。全局丢失数读后复位，记录增量；强制 flush 未完成、缓冲未还、观察到 kernel、丢失或 ETW 尾部不明均不能通过。计量启用前和最后回调之后仍有盲区；零记录缺少 kernel 正例验证。隐式 context、全生命周期物理 launch 及设备清理时长上界均为 null。 |

### CPU 故障测试

真实 Windows 匿名管道上的 CPU 替身通过 31 项检查，包括迟到许可、顺序错误、EOF、设备数异常、错误 UUID、丢失记录和错误关联。最终 runner 套件通过 34 组，覆盖加载失败、映像替换、并发锁、父控在创建前/恢复前/恢复后死亡、观察器卡住、非零退出及日志尾部不明。真实短写注入只写入 9 字节，验证不再接受后续写入或补发许可，原 attempt 不能重放。测试中使用独立目录、测试锁和 CPU 替身。原始生产预算没有扣款。[31 项子进程测试](probe/tests/CPU_PROTOCOL_001.json) · [34 组 runner 测试](runner/cpu-checks/run-005/RESULT.json)

保留 run-004 的失败：当时把进程句柄已发信号和 Job active=0 视为同时可见。独立复现中第二进程已被 1816 拒绝，Job 的 active 读数稍后才降到 0。修复在剩余清理时间内等待并复查；仍不能确定时返回 UNKNOWN。显存水位与 ETW 终态策略另做 5 项 CPU 合成检查，普通与 -O 各通过一次。[失败记录](runner/cpu-checks/run-004/FAILURE.json) · [观察器测试](observation/CPU_POLICY_OPTIMIZED.log)

### 本机还缺的两项证据

1. **ETW。** 在拟用 Windows 身份上只启动父控 ETW 组件，启动链返回 Win32 5，未创建 CPU 子进程。收尾返回 4201，没有可认可的首尾事件或丢失统计。须在实际拟用的登录身份/启动环境中取得 CPU 子进程的创建、映像、退出和零丢失回执。当前零值字段没有观测区间。[ETW CPU 记录](observation/ETW_CPU_BOUND.json)
2. **受限子进程。** 同一 CPU 替身可以在普通受限额 Job 中运行。为它同时指定零能力 AppContainer 和原子 Job 后，CreateProcessW 返回 WinError 2，尚未获得子 token；无法证明批准映像可读及目标模型路径拒读。失败位置已定位，具体路径、配置或访问原因仍待确认。下一项验证仅需 CPU 替身。若现场需要调整权限或部署，先单独明确调整范围。[隔离 CPU 记录](runner/cpu-checks/acl-002/APPCONTAINER_CPU.json) · [宿主与信任边界](observation/SCOPE_ZH.md)

执行入口以通过且匹配当前身份/产物的 CPU 回执为前置条件。即使补足以上两项，还须在真正的准入操作内刷新全主机任务、调度来源、旧锁和 lease，核实直到窗口结束都由同一 runner 独占。e05 的用户确认无需重新追溯，无法约束未来重新派发。11 月 13 日 20:00–20:05（上海）仍仅为提案，未预约、未排队；过期须另提窗口、重新绑定并批准。

### 本轮使用量

模型加载及请求、输入和输出行、普通数值 DLL 加载、真实探针运行、CUDA 初始化、GPU context、物理 kernel launch 和原生 GPU 秒均为 **0**。这里记录本轮程序的行为，宿主上其他应用的 GPU 使用不在统计范围。66 格资格、模型闭环及性能计时均为 NOT_RUN。A 的原 4,096 硬合同仍未闭合，原生产入口继续拒绝；第二轮未开始。

[机器可读门槛](RESULT.json) · [单次操作批准摘要](APPROVAL_ZH.md) · [独立预算](CONTRACT.json) · [runner 与回执字段](runner/README_ZH.md) · [构建及冻结方法](build/BUILD_REVIEW_ZH.md)

本机交接目录为工作区下的 `rtx223-e06`。完整备份保留每次构建、自己编译的 PE、CPU 测试的原始日志与失败记录；vendor DLL、模型和工具链字节仍在原位置。Git 提交包含源码、清单和审查记录。解压到其他路径可能改变文件 ID；实际批准对象以原路径的冻结清单为准。
