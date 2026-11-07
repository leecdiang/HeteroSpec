# PR120：RTX 参考约束、合格映射与成本边界

**结论：可信的重复执行已恢复；本次面板中 QB 仍是更强的软件成本基线，QH_C 没有总体成本优势。硬件方向保持 SOFTWARE_FIRST/HOLD。**

实验身份 `rtx-reference-envelope-v2`，执行 UUID `hs120-8a6bde3c-bc24-4f16-9e1e-9950965386d3`。PR118 的 r2 仍永久停止、0 个合格样本；其代码、审批、保护条件与原始证据未改写。

## 1. 哪些映射在什么条件下合格

D0 在三个原分配进程和三个回退进程中复现了同一故障：第一次 ordinary 正确，第二次 32/4096 个 float32 words 不同。实际地址及完整字节证明：K 的存储被 AV 复用，V 的存储被 ordinary 恢复节点复用。第一次输出低 16 位 `0x6000` 写进 V 后，作为 FP16 读取恰为 **512**，对应第二次异常值。每次重传可恢复全部输出，但设备输入仍被覆盖；采用独立持久输入存储后，3 个新进程各 34 次调用的输入与输出均精确保持。这个见证定位了本宿主的存储生命周期问题，并不是 QB 算术、CUDA kernel 或归约树故障的证据。见 [D0_FINDINGS.json](D0_FINDINGS.json)。

|阶段|实际 GPU 宿主|图调用|结果与范围|
|---|---:|---:|---|
|D0|12|216|全部干预、失败和回退保留；3 个持久输入宿主合格|
|N1|216|7,344|72/72 单元格；24 个旧暴露上下文 × 3 布局，各 3 个新进程、2 warmups + 32 次|
|T1|432|16,416|全部数值合格；8 warmups + 30 次；5/6 成本块有效|
|R1|672|15,504|240 串行参考宿主、288 资格宿主、144 成本宿主|
|M1|纯 CPU|0|1,008 个确定性模型点；原始较粗模型另存并撤回其强基线解释|

PQ、QB、QH_C 在所测持久输入生命周期下均保持完整 ordinary 参考字节。保留全部头、通道、key、mask、原 dtype/精度、必要 CONT/REPEAT/输出恢复，以及原 CUDA graph 禁用设置。每个宿主检查实际支持、CUDA buffer/device 归属、共享核心与 41 个插件导入、输入前后字节及完成同步。

N1 是 PR116 真实索引中的固定 24 个暴露上下文，覆盖三家族、两 phase、q1–q4 与原层选择规则；不是完整 72 上下文面板。原 tensor key extent=256 含 padding，真实可见 key 见 [CONTEXTS.csv](results/CONTEXTS.csv)。

R1 是预先固定的 12 development + 12 holdout 逻辑几何，各两个值实现，共 48 个合成输入：Hq=32，d=64/128，Hkv=1/8/32，选定坐标的真实可见长度最高 4096，并包含 compact/permuted Q、causal/irregular/single-visible mask。144 个映射单元格均经两个独立新进程 ×34 次合格；120 对独立单 query 参考逐位相同。4 个单可见 key 输入另有完整独立 CPU oracle，共 65,536 words。见 [R1_CONTEXTS.csv](results/R1_CONTEXTS.csv)。这是合成数组，不是未见自然 prompt；clean 图没有读取新 QK/softmax/AV 中间值，不能声称新几何四阶段均已对应。

## 2. 真实成本差异

比值大于 1 有利于分母。先对宿主内技术重复求均值，再按 context/block 配对，等 context、等 block 权重。无删尾、无逐调用 bootstrap。五个有效块来自同一机器会话，不是五个独立日期。完整六排列均已采集，但一块从成本估计中排除。

|q2–q4 成本视图|T_QB/T_QH_C|QB−QH_C μs|T_PQ/T_QB|PQ−QB μs|
|---|---:|---:|---:|---:|
|resident_graph|0.885627|-11.997|1.814620|80.721|
|resident_call|0.903634|-14.658|1.591796|86.365|
|input_inclusive_first_call_phase_sum|0.924892|-2021.999|1.050152|1249.038|

主要比较的描述性块 bootstrap 95% 区间为 **[0.8717449356194544,0.8950737248750243]**。QH_C 在 **73/90** 个有效 context/block 配对中退化；其余局部反转全部保留，见 [CONTRASTS.csv](results/CONTRASTS.csv)。五个块的 log contrast 为 [-0.116282617185456,-0.1193126672450239,-0.15272000587724285,-0.10881932954653362,-0.1101623367052592]；leave-one-block-out 比值为 [0.8844815853782447,0.8851518450813659,0.8925754441230765,0.8828328388694865,0.8831293013412441]。

q1 公共构图负对照：QB/QH_C=1.015293，平均差 0.971 μs，没有达到预设的 >1.02 且 >1 μs 联合阈值。其逐块变化也完整保留。单个 >1.02 点不能称为稳定加速。

|布局，q>1|有效宿主|宿主均值的均值 μs|宿主 median 的 median μs|宿主 p95 的 median μs|最大单调用 μs|
|---|---:|---:|---:|---:|---:|
|PQ|90|173.176|161.000|264.900|953.800|
|QB|90|92.455|82.175|141.400|337.700|
|QH_C|90|104.452|92.775|165.250|669.700|

resident_graph 包含 graph_compute 和全设备完成同步；resident_call 再包含必要 ordinary readback（包括本实现的 CPU 输出缓冲分配）。input-inclusive 是每宿主一次“CPU 完整物化 + upload/sync + 首次 warmup 的完成图及 readback”相位和，不是 30 次独立输入包含样本，也不是 decoder 请求墙钟。初始化、构图、分配、源文件读取和完整宿主命令墙钟另列，见 [COST_COMPONENTS.csv](results/COST_COMPONENTS.csv)。 其中 initialization 包含核心身份哈希/审计和 CUDA 初始化，不是纯 CUDA 初始化时间；main 之前的 loader 时间只在完整宿主墙钟中。

快照 mask/Q/K/V 的实际复制和上传已计量；从自然模型状态产生这些操作数的成本不在本工作负载中。QH 必需的 GPU packing、mask 视图/物化和输出恢复仍在真实图内付费。文件写入、检查、profiling 不进入图付费窗口，但后置观察可能影响下一次 replay/cache 状态。所有原始 QPC ticks、warmups、尾部均保留在本地归档；不把宿主墙钟或图节点数称为 kernel 时间或 launch 数。

## 3. 能否跨几何预测

R1 q>1 holdout 的 QB/QH_C=0.962451。总体仍偏向 QB，但局部次序会反转。冻结的 q-only selector 在任何 R1 输出产生前已决定 q1–q4 全选 QB；全部 24 个 holdout 值实现相对逐点 oracle 的平均比值为 1.039761，最大 1.289041，已加上实测 Python lookup 开销。它没有构成超越固定 QB 的新方法，也没有证明 q 足以预测更广几何的最优映射。

R1 成本只有两个值实现，布局采用固定 PQ→QB→QH_C 顺序，存在次序混杂，故只作描述性边界证据，不冒充六块确认。selector 成本是“选定映射实测均值 + CPU lookup”的相位和，不是已经集成并测过的 decoder selector。下一项最有信息量的成本实验是对预选边界/GQA/stride 坐标做独立平衡顺序重复，而不是挑本轮有利点补跑。

另有完整 FP64 数学 oracle：48 个合成输入、409,600 个输出 words，最大绝对差 0.000382292988，见 [FP64_ORACLE.csv](FP64_ORACLE.csv)。它使用完整头/通道/key、原 mask 和精确传入 scale；不是部署字节参考，没有据此改动容差、数值资格或候选。相同部署字节也不能被解释为更接近数学真值；差异的具体 backend 来源仍未知。该附加 CPU 诊断从 fresh CAS 重算，CSV 及每个 FP64 输出 hash 相同；输出位于归档旁的 CPU_FP64_ORACLE，未混入主 GPU raw 容器。

另外 48 个旧暴露上下文的输入已在 CPU 上核验可用，但本轮新资格仍为 UNSTARTED，未与旧 PR113 部分结果拼接。完整 36+36 合成设计尚余 48 个逻辑 fixture（每 split 24 个）未执行；原 R1 冻结计划的“每 split 剩 12 个”只是算术注释错误，原字节保留，实际矩阵/计数未变。新自然快照和 W1 未执行。

## 4. 强基线之后是否有硬件空间

**尚未知，保持 SOFTWARE_FIRST/HOLD。** M1 比较真实不同的静态、动态和缓存感知调度、消融及乐观下界，保留完整几何、有限 context/descriptor/cache/bank/queue、流式 AV、共享操作数复用、setup 摊销和三个资源区间。初版模型漏计 P/部分累加器 bank 读，并以整 key 维 V 操作数限制了强基线流式复用；其源码和全部结果保存在 M1/revision0。本轮唯一一次 CPU 模型替代修正了这些假设。

模型仍是 ABSTRACT_REFERENCE：bank 按 tile 保留、全驻留工作区等假设较粗，没有 RTX 数值 DAG、物理资源校准或独立 heldout 架构验证。其冷启动、完整数值 DAG 下界是条件性下界，不是 ordinary-only attention 的普适代数下界。模型网格点不是统计实验样本。不能从 baseline/ideal 差距直接推导硬件收益。

实际 kernel 身份、launch 数、物理流量、occupancy、Tensor Core 利用率、RTX 归约 DAG、面积/频率/PPA 和请求关键路径比例仍为 UNKNOWN。未找到合格 profiler，但这没有阻塞合格的主机完成计时。下一步需要物理 trace/竞争软件基线与参考资格，再决定微架构方向；自然请求还需独立 actor/shared-core/KV/rollback/phase 资格和 W1 授权。本轮没有 RTL/FPGA、actor/decoder、模型请求或新权重下载，也没有修改 B570、论文、main、发布和自动化。

## 失败、资源及复现

T1 的 attempt0559 在 native 已退出后，CPU 去重遇到 NTFS 最大硬链接数。全部 38 个输出、输入前后字节、支持/归属/导入及 exit0 均重新核验。真实 Windows 的 1,100 文件测试验证回退方式：达到上限就保留原普通文件。只继续从未启动的坐标，没有 GPU retry；在查看延迟之前，整个 block4 已从成本汇总排除，所有原始数据、原 freeze 和修复记录均保留。P0 的导入库路径修复、负测试与较早分析版本也保留。

实际 GPU 宿主 1332，图调用 39480，节点支持 API 查询 27336，就绪/环境设备查询 99；模型请求及 profiler 均为 0。宿主命令墙钟合计 1755.289 秒，不是 GPU busy/kernel 时间；native Job commit 峰值 625913856 bytes。D0/N1/T1 阶段耗时 {'D0': 22.203000000008615, 'N1': 342.9530000000086, 'T1': 951.3016514778137}；R1 耗时 1001.219 秒。没有完整全机工程进程账本，不把这些计数冒充全部 OS 生命周期。

任务使用一个 GPU worker、8 GiB RAM/新存储预算、8 小时总上限及最后 1 小时交付预留。存储按唯一文件内容/文件 ID 去重并另列逻辑发生字节数；所有发生记录仍可恢复。电源方案在 R1 期间观察到，T1 未连续记录 power scheme/固定时钟。空闲前后样本不保证期间持续独占设备。

原始位置：`D:\hs120-8a6bde3c-bc24-4f16-9e1e-9950965386d3`。归档：`D:\hs120-8a6bde3c-bc24-4f16-9e1e-9950965386d3-archive\raw.zip`。成员数 110693，逻辑发生字节 11603510909，唯一二进制 blob 898，容器 127743318 bytes。**RAW_LOCAL_ONLY**：遵守 CONTRIBUTING，不把 raw telemetry 提交 Git，没有远端 raw 认证或外部独立审查。

归档 SHA256：`ab94591015b609df057c1b3edc99784f0a066e8eb9bba56e266097b783e17c3d`。成员 manifest SHA256：`fb178beb74b1f373c7f0e87f6814645b059503229a207b7015ebdfa8f426b67b`。全部成员已 fresh restore 并逐项校验；新解释器复算的科学 CSV 字节一致。见 [RAW_LOCATION.json](RAW_LOCATION.json)。

命令见 [COMMANDS.md](COMMANDS.md)。CPU 恢复通过显式“原输入路径→恢复 CAS”映射读取相同字节，原 spec/job 不改写。历史 GPU 命令仅供审计，不是重新执行本 UUID 的许可。
