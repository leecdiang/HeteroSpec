# HeteroSpec 双平台迁移审阅与 TPDS 判断

2026-11-03 · 作者研究审阅，不是 IEEE 编辑决定。审阅冻结点：PR165 `5aae66e05b0f6e8a8b44dac719b2b05b8f84f34f`；PR166 `abd36bea639bf814159ad68ab015bc983c5338b1`；稿件/目标 PR164 `06c5780d1a3e3e37b780d50274b6ab3e07bc96dc`。

## 总体判断

**两平台的科学执行已完成，这一轮兑现了上一轮最重要的缺口：结构规则在 Qwen 原生路径中实际触发，并修复保留反例。** 现在是有跨模型主动迁移证据的参考保持 runtime 原型，而不是仅在新库中重跑旧配置的兼容测试。

TPDS 目标值得保留。目前更需要回答的是：方法如何扩展到更宽 query / 更长上下文，以及它相对“遇到边界就拆整段 target 计算”这种简单方法，究竟多保留多少有效并行。下一阶段应围绕这个系统问题建设方法，而非重复旧样本、追更好百分比或扩大归档程序。

本轮关键源码和报告审阅未发现推翻已测试数值修复的证据。发现的主要问题是 B570 热路径资源查询的成本解释、两平台成本聚合口径不同，以及分支集成时 graph-reuse 条件未统一。这些问题应分开处理，不能把它们扩大成“所有结果无效”。

## 已完成的实质贡献

### B570：原失败路径修复与 producer 条件消除

MATH1865、1804 保留历史 P1 KV/初始 logits，resumed PQ/QB 均逐字节恢复128个 committed scalar vectors。并没有改走原先已成功的 P4T。GSM1184 的新 P4T producer 本身形成历史 P1 的边界，两个 producer 的 ordinary/resumed 路径均保持原 R。

精度开关反转在同候选二进制上恢复 MATH1865 历史失败的全部205个保存向量、事务与端点。实际 Vulkan selector 从权重/输入类型、contiguity 和 device dispatch 谓词得到 scalar_quant=0、batch_quant=1，再选择 F32-activation 批量实现。

**因果归属要精确：两个旧 MATH 失败单元没有跨物理 bucket，修复它们的是激活算术要求。** Qwen 的物理前缀规则则由另外的 native cache probe 证明：width2/head254 不拆，head255 拆1+1，实际行向量对应 scalar teacher forcing。两种机制共同组成方法，但不能把所有成功都归给 prefix grouping。

八个冻结后自然输入通过；6316个保存向量由原机 auditor 重建，4096个 committed candidate vectors 对原 R 相同。8个输入均生成128个token，有限窗口保持不能写成任意长生成保证。来源：[B570 RESULTS](https://github.com/leecdiang/HeteroSpec/blob/5aae66e05b0f6e8a8b44dac719b2b05b8f84f34f/benchmarks/reference_batching_transfer_20261103/b570_host/RESULTS.md)、同目录 PRECISION_REVERSAL.json、INDEPENDENT.json。

### RTX：结构选择而非模型名称选择

Qwen8B 的真实 head510 跨512边界，预测/观察为2+2；Qwen14B head254 跨256边界同样为2+2。普通点保持一组，QK 观察覆盖36/40层。14B 的实际图 RMS_NORM→MUL→RoPE 链决定 scalar-placement 选择，8B没有相应 preference 分歧。8398是 selector preference 查询次数，不是8398次独立 kernel launch。

12个 PR159 旧失败 recipes 全部恢复原 R；其中10个是正式面板结束后、同一冻结二进制的追加覆盖。这不是冻结后调参，不要求据此重开未见面板。两配置各4个新输入全部通过。2540/2560的 committed-vector计数包含 candidate R 的资格格，不能把5100全称为非参考候选向量。

8B为 all-GPU，14B为 partial-offload；它们是两个模型配置，不是受控的纯模型规模实验，也不能算成三个模型家族。来源：[RTX RESULTS](https://github.com/leecdiang/HeteroSpec/blob/abd36bea639bf814159ad68ab015bc983c5338b1/benchmarks/reference_batching_transfer_20261103/rtx_execution/RESULTS.md)、evidence/FREEZE.json、PR159_RECIPE_AUDIT.json，以及 src/reference_batching/activate_cuda_requirements.py。

## 成本结果及复算

M=普通 target-only，C=speculative。所有比值均为分子时间/分母时间。以下保留各报告的原估计量，不混合输入或硬件排名。

| 配置 | M_QB/M_PQ | C_QB/C_PQ | M_QB/C_QB | M_QB/R | C_QB/R |
|---|---:|---:|---:|---:|---:|
| RTX Qwen8B | 1.016815 | 0.958175 | 1.194423 | 0.527884 | 0.441957 |
| RTX Qwen14B partial-offload | 0.983533 | 0.976817 | 1.658557 | 0.543050 | 0.327423 |
| B570 Qwen8B all-GPU | 0.915047 | 0.969123 | 0.269172 | 0.603813 | 2.243222 |

B570 的 M/C≈0.269意味着 speculative 耗时约为同布局 target-only 的3.715倍，不只是比R慢2.243倍。两组比较回答不同问题。RTX的局部 speculative QB 相对PQ降低4.18%/2.32%；B570普通路径和speculative路径分别降低8.50%/3.09%。RTX8B ordinary QB相对PQ增加1.68%，保留这个结果。

B570该轮是all-GPU Qwen，不允许沿用旧Llama的CPU-draft归因。预定的单输入phase诊断中，R的target prefill/ordinary为6.301/3.519秒，M_QB为2.350/3.516秒；真实改善主要出现在prefill，而非未知AR token并行。C_QB的draft prefill为10.140秒，但draft sync+proposal也达7.685秒。即使仅在这份诊断中假设draft prefill为零、其余phase不变，剩余阶段总和仍高于M_QB；不能承诺单独优化draft prefill就会盈利。来源：B570 PHASES.json（performance_eligible=false）。

### F1：B570逐decode资源查询进入正式service timer（重要解释问题）

scripts/b570_qwen_transfer/build_driver.py 注入 `DecodeScope scope(...); capacity_check();`，之后才开始phase计时并调用llama_decode。transfer_scope.hpp中的capacity_check调用ggml_backend_dev_memory和GlobalMemoryStatusEx。整个run_request被service timer包围；policy.clean与performance_eligible均不屏蔽该查询。

因此旧表是包含此安全查询的driver服务代价。查询次数随scalar prefill、batch prefill与speculative步骤变化，可能影响M/R与C/M解释。现有证据没有测出该项占比；不能将全部残差、全部gain或全部draft损失归给它。匹配工作量的PQ/QB局部比较更受保护，但不等于查询开销严格抵消。

行动：保留请求边界/外层安全保护，做一次小型同二进制polling-on/off隔离，新生产计时移除逐decode重查询；旧记录保持原样。详见PLAN A。来源：[build_driver.py](https://github.com/leecdiang/HeteroSpec/blob/5aae66e05b0f6e8a8b44dac719b2b05b8f84f34f/scripts/b570_qwen_transfer/build_driver.py)、[transfer_scope.hpp](https://github.com/leecdiang/HeteroSpec/blob/5aae66e05b0f6e8a8b44dac719b2b05b8f84f34f/scripts/b570_qwen_transfer/transfer_scope.hpp)。

### F2：RTX与B570的聚合口径不同（离线可解决）

RTX confirm.py 先对每个输入跨session累加时间后算ratio，再对输入取几何均值；B570对24个session/input配对块取等权几何均值。两者均可定义，但不是同一estimand。

本次复算RTX全部120个保存正式耗时，精确重现其原报告；统一成等输入等session paired-log 后：

| 配置 | M_QB/M_PQ | C_QB/C_PQ | M_QB/C_QB | M_QB/R | C_QB/R |
|---|---:|---:|---:|---:|---:|
| RTX8B | 1.017374 | 0.958029 | 1.193593 | 0.529363 | 0.443504 |
| RTX14B | 0.984046 | 0.976796 | 1.658206 | 0.543134 | 0.327543 |

方向均不变。每个RTX配置的ordinary比较均有4/12块QB更慢，speculative比较1/12块更慢；B570两个局部对比均24/24块QB更快。这是描述性结果，不是把块当独立样本的显著性判断。统一复算必须标为事后分析，不回写原报告或追认成预注册。

来源：[RTX confirm.py](https://github.com/leecdiang/HeteroSpec/blob/abd36bea639bf814159ad68ab015bc983c5338b1/benchmarks/reference_batching_transfer_20261103/rtx_execution/confirm.py)、两个evidence/*/COST.json、B570 COST.json。

### F3：数值oracle与被计时的R要分开

RTX旧exe提供资格oracle；正式timed R使用已通过完整向量对应的candidate-runtime ordinary路径。B570的reference adapter链接原数值DLL。这不推翻数值参考保持，但两个R的成本定义并非相同，也不能把RTX表写成旧exe本身被加速多少。来源：两平台RESULTS与RTX confirm.py。

### F4：共享集成要合并已有正确条件，而非重开审计工程

B570 final_mapping.py把logical ordered-append加入graph reuse身份。CUDA原prefix实现有build-time ordered判断，而当前共享integrator主要比prefix vector与policy；新head-placement key是另一条件，不能替代ordering。现有测试使用ordered工作负载，未观察到错误复用；这是一项扩展前应修正的集成缺口，不是已证实旧结果错误。

两个分支共享算法及接口，但不是已经交付了同一revision的双后端release。整合CUDA新helper和Vulkanreuse条件，做一个相关状态变化控制即可。来源：PR165 scripts/b570_qwen_transfer/final_mapping.py，PR166 src/reference_batching/integrate_llama_cpp.py / activate_cuda_requirements.py，以及PR162 prefix_extent.py。

### F5：科学完成、交付完成、论文集成是三个状态

PR165已完成远端回读与独立脚本恢复，仍是同host认证访问，不是第三方GPU复现。PR166为Draft，已读提交的RESULTS仅说明raw在E:/rtx164；没有找到本轮远端完整交付回执。旧PR162的交付已完成不能代替它。PR164的README/方法章节仍写共享候选只有CPU验证、自动选择未接通，现已落后于新结果。只需集成事实，不用再增加免责声明。

## 按TPDS目标的判断

| 问题 | 当前证据 | 下一步价值 |
|---|---|---|
| 原参考兼容是否真正修复 | 较强：原状态、完整向量、因果反转、冻结确认 | 不重复全面板 |
| 是否主动跨家族 | 已建立Llama→Qwen的实际结构触发；8B/14B配置有区别 | 统一native产物，增加一个真正不同head结构的点 |
| 是否有独特方法 | 既定数值参考下的选择性执行约束有辨识度 | 相容条件如何决定可利用的并行，而非把简单分段命题包装成理论创新 |
| 并行扩展与强替代方案 | 当前主域q≤4/context1024，尚缺完整frontier与整caller拆分对照 | 下一阶段最优先 |
| 成本解释 | 同布局比较可用；大R-relative改善含prefill，B570另有polling项 | 定点隔离+新面板的clean主计时 |
| 稿件状态 | 10页候选尚未吸收本轮新证据 | 改为方法与迁移/扩展主线，历史状态干预下沉 |

TPDS官方范围包含GPU/异构体系结构、runtime、数值并行算法及性能建模，不要求为投稿凭空增加多机或新硬件。[官方scope](https://www.computer.org/digital-library/journals/td/cfp-parallel-distributed-systems)。

与先行工作对比，batch-invariant归约、固定shape调度、verify/rollback和状态/kernel契约都已有直接工作；不要声称首次发现batch数值敏感性。HeteroSpec的研究定位仍是**兼容优化前已经确定的量化参考，利用局部结构约束保留既有批量执行**。下一实验应检验其效率与迁移，不制造与不同权重/precision/runtime的外部系统速度排名。

- Thinking Machines, Defeating Nondeterminism in LLM Inference (2025): https://thinkingmachines.ai/blog/defeating-nondeterminism-in-llm-inference/
- LLM-42, verified speculation: https://arxiv.org/abs/2601.17768
- CoRun, fixed-shape scheduling: https://arxiv.org/abs/2608.14376
- Vosti, state/kernel determinism specification and proof: https://arxiv.org/abs/2609.38981

## 审核范围与技能

使用peer-review、scientific-critical-thinking、statistical-analysis、scholar-evaluation和anti-defensive-writing-en五种视角。当前会话不能启动独立subagent；这不是五个独立审稿人。技能用于组织方法审查与贡献表达，不能替代源码、数据或授权作者判断；未使用隐藏不利结果的写作建议。

本次读取的是关键实现、冻结/结果/资格/诊断报告及计时/审计代码，不是仓库全部文件的逐字节复审。CPU复算输入为从连接器返回内容转录的保存数据：RTX120个正式耗时；B570首session40个正式耗时；另复算B570全部48个局部配对ratio。共160个保存时间值，不声称已重新解析全部240个native原始请求或全部raw向量。B570全量raw恢复由原机INDEPENDENT/REMOTE_RECONSTRUCTION报告支持，本次没有复制该全量复现。没有新GPU forward、修改旧实验、合并分支或投稿。

辅助方法来源：Kassis, Agarwal, He, Patel, Brueckner (2026), Scientific Agent Skills: A Library of Procedural Knowledge for Research Agents, https://arxiv.org/abs/2609.00065。相关技能已列入本审阅产物的来源，不要求把它们当成论文的科学贡献。
