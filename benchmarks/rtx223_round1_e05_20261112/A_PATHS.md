# 方案 A · 全生命周期物理 launch 的覆盖矩阵

**判定：原合同未闭合。** 在 #223 `7ce00b3c72ecf72adcd6d3832d78c3d359dbb6ac` 对应的 Windows 构建上，第一个决定性缺口出现在正常 DLL 加载时。加载可以先运行依赖项的初始化代码，返回后前端才能取得预算导出地址。对这个区间没有绑定实际运行时身份的物理上界，也没有已证明的逐次提交否决点。即使后面的显式 kernel 全部有守卫，仅这一个缺口就足以拒绝执行。此判定适用于现有部署和证据，未推断任意未来驱动的能力。

## 计费起止与举证条件

原 e01 `RESOURCE_PLAN.json` SHA-256 为 `c801e0ae529a14e7911e678b02d018086be3eed5712b3bb16ece06c3b638bd63`。整个 family 共享 4,096 次：warmup 192、正确性 96、配对计时 3,456、失败余量 352。资格、热身、已失败尝试、target/draft、runtime 和 standalone 都计费。新 epoch 没有新额度。其余限额见原计划和 e02 `continuation/safety/BUDGET_BINDING.json`。

一个物理单位指一次设备 kernel grid 执行。一次调用的 grid 大小不改变这一个单位。DMA 字节、请求、行数、API 次数、采样记录数分别核算。合格的方案须在任何可能启动设备工作的进程或 DLL 启动前，在规范 family 账本中一次性保守覆盖正常执行和**最坏可达失败前缀及其清理**，且通过可信实现证明每条实际路径不会超出预留，或在下一次未覆盖物理提交之前强制拒绝。崩溃后的预留不退款。仅写入“预留 4096”无法限制未知操作实际消耗。

以下使用 e04 包内相对路径。前端文件在 `e04/frontend/run-v4/source/`，CUDA 文件在 `runtime/source-v1/ggml/src/ggml-cuda/`，llama 文件在 `runtime/source-v1/src/`。引用行号对应冻结文件的行号，源中诊断字符串内的行号可能较早。每行“预留位置”指最晚可行的控制边界，所有成本均须提前纳入 family 总预留。“未知”表示缺少上界证明，并未判定该 API 实际一定发出 kernel。

在 #223 Git 树中以 `benchmarks/rtx223_round1_e04_20261112/` 为根，审查入口、前端源码和已修改的 CUDA 文件可直接阅读。下表的 `runtime/build-v2/deps/059.d` 位于 e04 v2 ZIP 中（SHA-256 `72c8f772ba8bb602ea22f8e8cd8a5d39c5c74f32d1cdc9f94624aae071ede553`）。`sum.cu`、`llama.cpp`、`llama-model.cpp`、`llama-context.cpp` 的行号来自本机完整源码，哈希与 `runtime/SOURCE_RECEIPT.json` 中四项相符；可用已绑定 original packed source kit 加 66 个覆盖文件重建这些源码。紧凑 Git/ZIP 只带部分源码全文。[原提交的前端加载顺序](https://github.com/leecdiang/HeteroSpec/blob/7ce00b3c72ecf72adcd6d3832d78c3d359dbb6ac/benchmarks/rtx223_round1_e04_20261112/e04/frontend/run-v4/source/e03_binding.hpp#L60-L87) · [完整源码重建说明](https://github.com/leecdiang/HeteroSpec/blob/7ce00b3c72ecf72adcd6d3832d78c3d359dbb6ac/benchmarks/rtx223_round1_e04_20261112/runtime/README.md)

| 路径与责任所有者 | 事前物理上界 | 最早风险之前的预留位置 | 超限前可阻止的范围、证据与缺口 |
|---|---|---|---|
| 宿主离线检查、启动 worker；runner、Windows loader、CRT | 本轮纯文件/CPU 检查贡献 0；待运行 EXE 的启动区间未知 | 父 runner 在创建进程前绑定 EXE、DLL、设备、进程/lease 和全部阶段 | 父进程可不创建 worker。worker 的 `entry.cpp:39,49–51` 在 main 内拒绝业务入口，覆盖不到 main 之前的静态导入、TLS、初始化器。多实例、重入或另一旧任务必须由外部排重和 family 预留处理。 |
| 数值 DLL、依赖加载、注册、延迟解析；前端、Windows loader、各 DLL / 驱动 | 未知；磁盘 SHA 和 PE 导入名可确定，普通加载最多发生多少物理提交无证书 | 父 runner 在创建进程前，隔离前端在首次可能载入模块前 | `e03_binding.hpp:60,65–87` 先拒绝；若未来放开，先 LoadLibraryExW base/CUDA，后 GetProcAddress、再 configure。e04 独立 `review/frontend-final/pe-native/imports.txt:58,101–108,114–131` 列出 cudart、fatbinary/function/var 注册和 cuBLAS。TLS/CRT、隐式/延迟依赖、动态符号、driver 内部均无在途否决证明。 |
| CUDA runtime / driver 初始化，选择设备、上下文、首次模块加载与可能的 JIT；ggml、NVIDIA | 未知；设备数量、UUID 和 context 数无法换算成 kernel 数 | 首个可能进入 runtime 的操作之前，包括加载期间的隐式调用 | `ggml-cuda.cu:137,225–229,287–295,420` 有直接 cudaSetDevice / cudaGetDeviceCount 和部分显式拒绝的 driver 查询。没有统一支配首次 runtime 调用的物理提交守卫。CUDA 12 的设备选择可初始化 primary context。[CUDA 初始化](https://docs.nvidia.com/cuda/archive/12.9.1/cuda-c-programming-guide/index.html#initialization) |
| 库句柄、workspace、算法选择及内部 kernel；cuBLAS、CUB、运行时与回退实现 | 未知；已知 host 调用次数仍缺算法、尺寸、设备和失败分支对应的内部次数 | 加载前预留库成本；每次进入库之前拒绝未证明的算法或路径 | `common.cuh:1511–1520`、`ggml-cuda.cu:1554–1614` 可在部分 cuBLAS 调用前拒绝。另见 `sum.cu:11–17` 的 CUB 查询和执行，`common.cuh:112–114` 的编译条件，`runtime/build-v2/deps/059.d:908–909` 的 CUB 依赖。源中的该调用没有本地 hs 守卫；未证明它在每个模型中可达，也未证明排除或受控。 |
| target、draft 文件解析、权重驻留、显存分配/转换/传输；前端、llama、ggml、driver | 各模型入口次数可数，物理项未知 | 两个模型、失败的半加载清理均在进程创建前纳入预留，分别在 load 之前检查 | `entry.cpp:65–77` 的 devices 和 n_gpu_layers，`llama.cpp:369,438,465–469` 与 `llama-model.cpp:1402,1484–1489` 的张量加载、分配和失败释放。文件身份和 placement 参数不能证明每次实际加载路径的工作量。 |
| target/draft context、KV、stream/event、内存池、清零/复制；llama、ggml、runtime | 未知；应分别计首次、延迟、复用和分配失败 | 初次上下文、内存操作前；不能推迟至 decode 开始 | `entry.cpp:89–91`、`worker.cpp:93–95`、`ggml-cuda.cu:597–612,779–797`、`common.cuh:1499,1519`。有些 memcpy/memset/映射调用可在调用前拒绝。DMA 可单独记录；不能统一假定每次拷贝发 0 次或 1 次 kernel。 |
| direct、模板 wrapper、普通/扩展 launch、standalone quantizer/MMVQ；项目代码、CUDA 运行时 | 对经过守卫、已证明无子提交的单一直接 grid，单次显式提交可保守收 1；全族动态调用总数未知 | family 先预留；实际 direct 提交前原子消耗同一份余额，wrapper 展开后只对物理子提交计费 | `quantize.cu:590–598`、`common.cuh:1678–1683`、`hs_launch_budget.cu:42–94`。后者的计数器仅一个 DLL 实例，production configure 固定拒绝；已写守卫的站点可 fail-stop，其他 DLL/实例、同族其他 worker、driver 内部与 device-side 子工作没有覆盖证明。源码站点数不限制循环执行次数。 |
| warmup、target/draft prefill、proposal、verify、采样/回退、配对筛选与 66 格；前端、调度器、各 backend | 请求/行可预先限定；每条真实描述符及分支的物理成本未知 | 在任何 warmup/qualification 前，覆盖所有 arm、draft/reference、负例及失败成本 | `worker.cpp:109,227,235,245–251`、`llama-context.cpp:2525`、`entry.cpp:99–115,127–131`。前端能停止下一请求，但调度器的一次 graph compute 可进入多个算子及库。保留原 A/B/C、输入和比较协议，66 格均未运行。 |
| CUDA graph 捕获、构建、instantiation/upload/update、replay、child/conditional/device launch；ggml、库、driver/device | 当前冻结 CUDA TU 的自有 graph 路径编译关闭；其他所有者、替代构建的物理成本未知 | 编译时关闭并绑定身份；若将来启用，构图、更新和每次 replay 前均须有预留 | `ggml-cuda.cu:3–5` 禁止启用 GGML_CUDA_USE_GRAPHS，`common.cuh:1235–1237` 和 `e03_binding.hpp:65` 给出编译与运行侧策略。源中可选路径见 `ggml-cuda.cu:2670–2687,4402–4423,4500`。未证明供应商内部也全禁。将来任何可变图均需拒绝或重新冻结：展开 kernel/child、循环最大次数、replay 次数并另界定 upload/update；没有有限证明的 device launch、WHILE、host callback 及并发外部工作应事前拒绝。[CUDA Graphs](https://docs.nvidia.com/cuda/archive/12.9.1/cuda-c-programming-guide/index.html#cuda-graphs) |
| correction/bonus、trim、pending、capture/export 及真实继续；前端、llama KV 和 backend | 状态调用及捕获字节可计，伴随 kernel/同步/拷贝的物理数未知 | 进入真实请求前覆盖最坏可达分支和捕获、恢复、清理，逐次操作前校验 | `worker.cpp:130–131,248–261`、`entry.cpp:4–6,25,130–144`。现有 state/API 数和字节预留约束其本身，无法给底层数据处理限额。 |
| 正常 teardown、DLL 卸载；前端、backend、CRT、loader、驱动 | 未知；工作可延迟到 free、同步、detach 和驱动回收 | 首次启动之前给正常退出留足不可挪用的额度 | `entry.cpp:152` 在最终释放之前做模块快照，随后清空 context、释放模型/backend。`ggml-cuda.cu:710–746` 涉及 cuBLAS destroy、workspace 和 device buffer free。能拒绝某个显式 destroy，无法证明完整退出有界且成功。 |
| 错误、超时、部分初始化、异步在途工作和进程死亡后清理；worker、宿主、loader、驱动 | 未知，失败点和剩余工作因路径而异 | 预留与正常路径共同计算，例如最长可失败前缀加最坏清理；不得靠失败后补记 | `entry.cpp:153` 异常返回，`llama.cpp:438` 半加载释放，`hs_launch_budget.cu:28–38` fail-stop 终止本进程。watchdog 只能停止后续受控操作，不能撤销已提交工作；进程退出及日志落盘均缺少最后一次可能物理提交的覆盖。 |

## 哪些证据能改变判定

e04 的 `budget/lifecycle_budget.py:22–31,73–75,144–185,312–342,413–423` 要求 18 个阶段、统一 arm 策略和有限展开。native 表为空，lookup 直接拒绝，执行控制器只接受 CPU mock；`budget/NATIVE_PREFLIGHT.json` 在 worker bootstrap 返回 `NATIVE_PROOF_MISSING`、总 bound 为 null。该语义和 `hs_launch_budget.cu:42–49` 的 native -6 相符。e04 独立审查 `e04/review/INDEPENDENT_REVIEW_ZH.md`、`e04/review/lifecycle/PROOF_OBLIGATIONS.json` 支持这一边界。后验审计可区分重复 API/graph 节点、请求 owner 和实际设备，也须记录启用前、退出后、未启用的类别和丢包。CUPTI 的 dropped 计数只涵盖其定义的队列丢弃，强退前缓冲未交付时计数也可能不可得；读到零不足以证明全部区间有记录。该接口未给出覆盖所有所有者的逐物理提交否决。[CUPTI Activity API](https://docs.nvidia.com/cupti/12.9/api/group__CUPTI__ACTIVITY__API.html)

若要重审，需要能执行完整原剖面的独立证据，使每条必经路径满足下列条件之一：证明固定部署上最多产生有限的物理工作，并在其首次可能发生前按 family 总账预留；或证明不可绕过的低层强制点逐次拦住所有未预留提交，包括 driver/库、device-side 及退出后的工作。可选路径可用绑定构建身份的不可达证明排除。还须对绑定身份变化、并发/重试、异常退出和耗尽时的清理做真实覆盖审查。单次 bootstrap 的观测不能补齐这些条件。

**A 的可执行性证据门槛 FAIL；native 准入 BLOCKED；native 硬上界 null；资格与性能 NOT_RUN。** 当前可证明的原生执行策略只允许拒绝进入，本轮没有调用数值 DLL 导出或测试 GPU。4096 和失败余量原样保留。
