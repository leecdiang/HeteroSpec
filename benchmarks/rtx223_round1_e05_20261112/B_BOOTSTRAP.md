# 方案 B · 单次 DLL 加载与设备可见性探针（待批准）

**本轮状态为 NOT_RUN。** 建议单独验证三件事：指定数值 DLL 能否由 Windows loader 加载，实际解析的 CUDA runtime 是否只看到预期 UUID，指定的计量通道能否启动、关联调用并输出回执。这里的“加载”指 DLL 加载。模型加载可行性、ggml 模型放置、A/B/C dispatch 与正例 kernel 探测灵敏度留为未验证。即使三项通过，即结束本合同。

## 操作范围及其源码依据

e04 实际编译入口为 `e04/frontend/run-v4/source/entry.cpp:39`。普通路径在第 50–51 行要求 native release，第 65–76 行才会注册 backend、选唯一 GPU 并加载 target 和可选 draft。其 `e03_binding.hpp` 的 `require_native_release` 无条件抛错。现有 profile 在模型加载后的第 98 行才有 profiler 入口，且当前 job 明确禁止 profile。保留上述代码及拒绝。以下提案需要**单独编译、可审核的无模型探针**；本轮没有可启动的探针授权。

1. **一个独占 runner，一个数值进程。** 已运行的纯 CPU 父控制器持有本次 GPU 实验的排他锁和独立 B 账本。用户已确认三条对应原执行聊天截至本次核对没有遗留任务或 lease。此证据适用于该时点。将来在同一准入操作内刷新全宿主及调度状态，核实本窗口所有可能延后启动的入口受同一排他范围控制。若后来出现未结清或可绕开该范围的任务，B 拒绝启动。绑定合同摘要、一次性 nonce、设备 UUID、可执行文件/依赖清单、进程创建时间及 PID、Job handle、窗口及输出目录。父控先创建未命名的私有 Job，独占唯一不可继承的 Job 句柄，不复制/外送该句柄。先设置并读回 active-process limit=1、两个 breakaway 标志皆关闭、kill-on-job-close 及 2 GiB 进程 commit 上限。用 STARTUPINFOEX 的 `PROC_THREAD_ATTRIBUTE_JOB_LIST` 指定此 Job，在同一次 `CreateProcessW(EXTENDED_STARTUPINFO_PRESENT | CREATE_SUSPENDED)` 中完成创建和入组。恢复前按句柄复核 PID、创建时间、Job 成员关系及 active=1。禁止创建后再 Assign 的降级路径。此机制和父控在 CreateProcess 返回前后、Resume 前后崩溃时仅结束自有子进程的行为须在相同 Windows build 和嵌套 Job 环境以纯 CPU 替身验证。任一能力或故障试验未证实则拒绝。探针只允许固定文件和既有父进程授权的通道，无 helper、子进程、服务、调度器或远程委托入口。父进程不加载数值 DLL。本方案新增实验进程总数为 1。父控和探针合计 2 个参与进程。进程限额不限制 Windows/driver 自身线程。[创建进程时原子加入 Job](https://devblogs.microsoft.com/oldnewthing/20230209-00/?p=107812)
2. **计量先开。** 父控在创建探针前启动并检查系统模块加载/卸载与进程退出事件，记录基线。探针的 PE 启动导入须与数值栈解耦。计量库绝对路径普通加载至多 1 次。先验证 `cuptiGetVersion` 与随该 DLL 提供的 `cupti_version.h:114` 相符（API 28，CUDA 12.9 Update 1）。注册回调并启用与本机 ABI 匹配的 runtime/driver API、context、kernel 与 memcpy 活动，所有必需状态成功才准许下一步。记录计量准备完成的时刻；库可能已带入 driver 或初始化 context。设置目标 UUID 的可见性必须发生在创建进程之前。计量初始化即失败时，禁止继续加载数值 DLL。计量不可用、未获权限时直接结束。
3. **一次显式数值根加载。** 对绑定目录中的 `ggml-cuda.dll` 发起一次 `LoadLibraryExW`，限制依赖搜索为 DLL 目录及 System32。读取此次实际加载的模块与动态解析到的路径。根 DLL 本身导入 `ggml-base.dll`、cudart、cuBLAS 和 MSVC 运行时，依赖加载及 CRT、TLS、fatbinary 行为包含在 B 的风险范围内。根加载失败即终止。禁止扫描目录注册 backend，禁止调用选择器、budget configure 及数值运算导出。只允许数值根加载一次并不限制其隐式依赖加载次数。
4. **一次设备数，一次属性。** 通过本进程已匹配的 `cudart64_12.dll` 模块句柄解析并限次调用 `cudaGetDeviceCount`。只有结果为 1 时，调用一次 `cudaGetDeviceProperties_v2(&prop,0)`，比较 `prop.uuid` 的 16 个字节及设备名。冻结的 `cuda_runtime_api.h:172` 将属性查询映射到 v2，`driver_types.h:2428` 定义 UUID；须用同一冻结头文件的 ABI 编译。与 `runtime/source-v1/ggml/src/ggml-cuda/ggml-cuda.cu:225–301` 设备发现共用底层两种查询。直接进入 ggml 枚举还会初始化静态设备表、处理虚拟设备映射及可能触发 VMM 不透明调用，故本次只验证数值 DLL 所解析的 **runtime 可见路由**。不显式创建或 retain context，不调用 `cudaSetDevice`、分配、传输、同步、positive-control kernel 或 reset。运行时或计量库可能隐式激活 context，真实数目和物理工作无已证上界。[CUDA Runtime Device Management](https://docs.nvidia.com/cuda/archive/12.9.0/cuda-runtime-api/group__CUDART__DEVICE.html)
5. **退出和失败清理。** 释放本探针取得的根模块引用 1 次，在计量仍有效时尽量记录卸载；引用计数及进程级资源可能延迟真正 detach。数值侧停止新调用后结束活动采集，完成下述全局 flush、回调收尾及丢失检查，记录尾部边界，退出。系统事件记录保持到父控收到进程句柄 signaled、Job active=0 和事件尾部；只记录时间边界及安全预算，不产生性能数据。失败、超时、父控死亡时保留部分记录和未完成状态，禁止重试。只能通过已绑定的 Job 句柄停止自有进程；若清理未证实，在 B 账本保留未闭合 attempt 并阻断未来准入，不能据此认定设备端所有清理均结束。

## 固定设备和依赖身份

拟限定 Windows 宿主的一块 NVIDIA GeForce RTX 5070 Ti Laptop GPU，UUID `GPU-6dd57db3-9aac-ccc8-bd69-225a5ea2c4dd`。原 `RESOURCE_PLAN.json` 记物理 index 0、12,227 MiB、驱动 616.92；index 仅留作历史线索。执行前须核实唯一可用 NVIDIA 计算设备及物理 UUID、driver、版本与独占状态，创建探针前对子进程设置完整 `CUDA_VISIBLE_DEVICES=<UUID>`，清除外来 CUDA/ggml 设备覆盖、注入或 profiling 设置（包括 `GGML_CUDA_DEVICES` 和 P2P）；固定关闭 graph。若无法建立单卡宿主约束，拒绝入场。观察到第二设备、外来 context/worker 或 UUID 不符，停止后续步骤。能硬限制探针提交的 ordinal（只准 0），不能用环境变量证明所有闭源初始化阶段的 placement。

本轮以普通文件读取复核以下九个 SHA-256，与 e04 的 `frontend/expected-modules-v1/MODULE_CLOSURE_v3.json`（`9407bbbb3d7946373a15bafd969ee92a8f22e189ed9246ed611b44f18485789a`）逐项相符。合计 807,245,888 字节。**实际加载路径及身份本轮均为 NOT_RUN。**

|预期文件|SHA-256|
|---|---|
|ggml-cuda.dll|2307f64f1f1f4d0bb4aba42e6f6793a29579c2af031e4dbadac77811096ae8ad|
|ggml-base.dll|2b0c99093f256d913f8b63e2ff5aabb43db8d849c6e9b2b7899b4367b2465dfc|
|cudart64_12.dll|760c38928bbe5759f7b31ed6692599eb7ec83cedd5702e84c2b72028a89837e1|
|cublas64_12.dll|90052a83efd1b57a8e3616a6590b335855f81b814a4f16eecb7b5bf6d1b1d4eb|
|cublasLt64_12.dll|c3a05ea244c937314afec09f87b91f814c7e27977681f6c67eb51bb06ced3a4a|
|MSVCP140.dll|0fa7eb792d3fbcf2233e4ea47e9144b9b1309ba8ed5d4731a72fffa8f4f556d6|
|VCRUNTIME140.dll|80b039ca328f53ce4f468eda0e6d25a6e565eb4842b3690db1d1cf033a1f2aca|
|VCRUNTIME140_1.dll|99ad0c5380674e28f965dc76b7cdfb8688cc2175a6641e00ab524195c3eaa900|
|VCOMP140.dll|95d4ce4a6802d1e18b5e0e1722cc30ea72ca7e033f83828f05c0b7b993fe7cbf|

VCOMP 的字节只作为 B 的拟议依赖，原历史身份继续 UNKNOWN。另以磁盘读取记录 profiler 源码中给出的 `E:/rtx170/profiler/sdk/nvidia/cuda_cupti/bin/cupti64_2025.2.1.dll`（4,552,272 字节，`be1ecb387e14c1c0515b3b162b44c89b480c9a12f16c60f7b82eb8b1ebc35e74`）和 `C:/Windows/System32/nvcuda.dll`（4,790,504 字节，32.0.16.1692，`f2b550e83f56b7b819efe382d712d125ee180341f012bd0aba2288320609a45a`）。后者可能只是一层入口。未来应冻结探针/控制器可执行文件、对应源码及编译器/头文件、CUPTI 与驱动实际后端、系统/API-set 目标及其路径、版本、大小、文件 ID、哈希，纳入同一批准摘要。执行期间持有防替换的普通文件句柄。核对每阶段模块快照（含启动时预加载模块）和加载/卸载记录，以**句柄解析的最终路径及其文件身份**与预期匹配；路径文件哈希的适用范围是映射来源，不能认证运行时内存的每个字节。不得默认放过 driver-store 动态库或同名模块。发现未知模块立即停止并保留身份；观测到加载后才做的校验不能事前拦截构造器。

## 供批准的单次预算

以下数值是探针设计约束或人为设定的保守停止阈值。尚无本机 bootstrap 样本可用于推算隐式工作。

|量|拟议边界、性质和依据|
|---|---|
|时间|建议仅在 **2026-11-13 20:00–20:05（上海）** 的人工确认独占时段内操作，过期作废，不排队。安全墙钟自创建进程前起算，至多给 80 秒进行列出的操作，余下 10 秒用于退出；超过 90 秒触发父控终止自有 Job，窗口剩余不足 90 秒不启动。只包含一次库加载、两次查询和清理，超时直接计失败。可强制禁止新步骤，终止请求的调度、驱动侧收尾和设备工作时长没有同步硬上界。|
|请求、模型、数据行|硬限 target/draft/GGUF 加载 **0**、输入/输出/target/draft 行各 **0**、请求 **0**、forward、warmup、graph 构建/replay 各 **0**。独立最小可执行文件没有模型参数、llama 初始化、输入数据或 forward/graph 入口，拒绝所有额外参数，无模型目录读权限。加载 GGUF 对确认 DLL 实际身份、runtime UUID 和计量 API 链没有必要。|
|操作与进程|硬限本合同尝试 1、实验子进程 1、重试 0、显式根加载 1、显式设备数查询最多 1、ordinal 0 属性读取最多 1。一次性 attempt 在创建前写入 B 自有账本，失败消耗该次；每步调用前消费许可。显式设备分配、context 创建请求、主动 kernel、GPU 张量捕获字节皆为 0。DLL 内部隐式操作不填入这些应用层硬限。|
|主机内存、磁盘|Job process commit 提议硬限 2 GiB，和 GPU 显存分别记录。九 DLL 磁盘大小约 770 MiB 仅作量级依据，不能据此预测 commit。父控所有新增事件/回执/日志（含 stdout/stderr）预置固定总容量 64 MiB，使用预分配文件或受限写入器，预留终止回执空间，配额满即停，不覆盖旧记录。CUPTI 宿主缓冲区总计最多 16 MiB（沿用已有 profiler 的每块 4 MiB，最多四块）；任何丢弃或溢出即记录失败。执行前承载卷空闲至少 2 GiB，运行中低于 1 GiB 即停。在专用目录限定写入权限、禁用 CUDA 磁盘缓存并绑定 TEMP/TMP；系统/驱动及外部写入无整机磁盘硬限。只读使用既有 DLL，无需在窗口内再复制约 770 MiB。|
|显存|提议入场空闲显存至少 8 GiB；相对入场已用显存增长达到 1 GiB 或空闲跌破 7 GiB 即停。该卡历史容量约 12 GiB，本方案无权重/KV/工作负载主动分配，选择为其他工作保留至少数 GiB 余量。使用与 UUID 绑定的非 CUDA 宿主管理采样（同一父进程、每秒至少一次），失读、设备身份或独占状态变化即停。水位检查为准入条件和运行中观察，无法阻止驱动在两次采样之间超限。没有 WDDM 逐进程显存硬配额证明。|
|物理 launch 和 context|提议硬限的只有**主动发起**的 kernel、显式 context 创建、校准 kernel 均为 0。CUPTI、driver/runtime、DLL 注册、TLS/CRT、库内部、失败与退出均可能引入隐式活动；全生命周期物理 launch 和实际 context 上界记为 **null**。若发现 kernel 活动，停止后续操作，保留记录；硬上限 4096 不适用于这一独立提案。|

## 计量判读与停止

以本机 `E:/rtx170/profiler/sdk/nvidia/cuda_cupti/include/cupti_activity.h` 为 ABI 依据（SHA-256 `ef11d11e13f725455c84414855a1956550994c214ef8d2269bae63fc32124252`）。第 7320–7345、7417–7447、7508–7547 行分别规定丢失计数、完成回调和 flush 的语义。缓冲区为全局所有，完成回调的 context 为 NULL、streamId 为 0；从每条活动记录提取上下文/流信息。仅由单一串行收集者调用 `cuptiActivityGetNumDroppedRecords(NULL, 0, &n)`；每次读取都会复位该队列计数，保存每次调用状态、增量 n 和累计值（含第一次读取），末次读取在最终 flush 与回调排空后完成，不能只看末次的零。停收时检查各已启用活动的关闭结果与 `cuptiActivityFlushAll(CUPTI_ACTIVITY_FLAG_FLUSH_FORCED)` 返回值；记录 callback 与缓冲池交接，确认完成回调已返回、待解析/待写记录均清空且证据落盘。解析只使用 validSize。强制 flush 可以包含未完成的记录，不隐含 CUDA 同步；存在不完整记录、回调未排空、查询或 flush 失败，均标计量不通过，不追加设备同步或重试。[CUPTI Activity API](https://docs.nvidia.com/cupti/12.9/api/group__CUPTI__ACTIVITY__API.html)

父控用自有 ETW 会话从创建前记录进程、映像及退出事件。核对 provider 启用、事件顺序、消费端排空和会话关闭统计，记录 `EventsLost`、`LogBuffersLost`、`RealTimeBuffersLost`。丢失、缺少必需事件、占满配额或终态/计数未知，加载轨迹即不完整，B 不能通过。[Windows ETW 会话统计](https://learn.microsoft.com/en-us/windows/win32/api/evntrace/ns-evntrace-event_trace_properties)

设备侧记录从探针 CUPTI 注册/启用成功时开始，并在最后可确认的 flush 结束。对两次 API 的回调/活动与本进程、线程、设备信息和调用顺序作关联，分开记 context、kernel、memcpy、API 和丢失数。没有 kernel 正例时只可报告“API 关联及记录写出是否通过，观测区间内收到 0 条 kernel 记录，正例检测未验证”。空 trace、无查询 API 回执或丢失状态未知，不能视为计量通过。计量库自身初始化、启用前工作、不支持的活动种类、子/设备端或库内不可见工作、buffer 丢失、异常退出和最后 flush 之后的 TLS/driver 清理均可形成盲区。正常退出及零 dropped 也不提供逐 launch 阻断或回溯的全生命周期上界。

身份/锁/lease/窗口/资源任一不符，应用层操作超出清单，CUPTI 失败，时钟跳变或心跳丢失，均关闭后续步骤。能安全正常退出时先释放自有引用；超时时仅结束自有 Job。持久保存已完成阶段、首次失败点、计量有效起止、缺失记录、退出/强制终止及宿主观察，无证据的字段保持 UNKNOWN。无自动重试、退款或下一步资格操作。

**批准边界。** 在 B 探针及 runner 的源码/PE/运行依赖摘要、CPU 故障测试、排重证据和现场窗口可逐项复核后，用户须对该摘要、上述日期/设备、单次数值 DLL 与计量加载、两次 runtime 查询、0 模型和 0 主动 kernel、允许发生不可预定量的隐式 context/物理 launch、水位及终止条件作明确同意。本提案没有取得这项同意。若用户仍要求 4096 物理 launch 硬上限，此提案不能运行。B 自有账本不继承、不写入、不重置 e02 原额度。批准只针对本次 bootstrap；结果只生成加载、可见设备及观测可行性回执。66 格资格、模型加载、实际分派、正例校准、计时及第二轮须另立相应协议并单独授权。
