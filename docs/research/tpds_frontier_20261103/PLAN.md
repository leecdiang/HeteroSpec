# TPDS 下一阶段：参考相容并行的扩展与强基线

2026-11-03 · 设计稿，尚未执行。配套 RTX_PROMPT.md / B570_PROMPT.md 可交给原机代理。原机可自主修复工程问题和据真实机制完善实现；新增参考配置、输入、对照和正式计时次序必须在相应输出前确定。不要把本文中的预期写成实验结果。

## 目标与依赖

本轮已经证明共享规则在 Qwen 原生执行中实际触发。下一项研究问题是：**在保持事先指定的数值参考时，局部相容分组能否比整段计算拆批保留更多有效并行，并在更宽 query 和更长上下文中保持价值？**

固定起点：PR164 `06c5780d1a3e3e37b780d50274b6ab3e07bc96dc`；B570 PR165 `5aae66e05b0f6e8a8b44dac719b2b05b8f84f34f`；RTX PR166 `abd36bea639bf814159ad68ab015bc983c5338b1`。另保留 PR162/163 的 Llama 数值结果与 PR159 的原 Qwen14B 失败单元。

用独立候选 worktree。两平台从同一共享实现修订出发，后端 mapping 分别绑定。不要修改旧参考、输入、失败记录、计时或关闭/合并旧 PR。此计划不授权 arXiv/期刊投稿。

## A. 一次集成与计时清理

将 PR166 的真实 RMS_NORM→MUL→RoPE 结构识别与 scalar placement 选择、PR165 的 Vulkan scalar/batch activation dispatch 选择接入统一候选。将 B570 的 ordered-append graph-reuse 身份检查带到共享集成；CUDA 原来已有 build-time 顺序 guard，但没有同等的 reuse-key 绑定。用一个同形状顺序/非顺序状态切换和原边界用例检查，不重跑所有历史面板。明确区分“输入结构可识别”“lowering 已支持”“数值对应已验证”；不要把 ProjectionAction::unsupported 或空 extent 向量默认为成功的参考保持路径。

B570 每次 decode 前的 capacity_check() 当前会查询设备显存和系统 RAM；它在 service timer 内、phase timer 外，且 clean=true 不会关闭它。保留零 forward admission、请求边界检查与外层进程/资源保护，将逐 decode 查询移出生产计时热路径。不要撤掉资源安全措施，也不要从总时间中减去估算的查询时间。

先做一个固定的 polling-on/off 诊断：从已暴露面板按 prompt token 长度选择最短和最长输入（并列按 ID 排序），五个旧 arms × 两种 polling 模式 × 三个 session，共 **60 次正式测量**，均有同 arm warmup。使用同一二进制/数值路径，只改变查询位置；参考保持检查不变。旧结果不覆盖。它回答安全查询造成多少实际负担，不用于重选最漂亮的旧结果。RTX 先检查同类查询是否进入热路径，仅在确有同类问题时做对应小诊断。

RTX 旧成本的 input-wise ratio-of-session-sums 与等权 paired-log 口径分别保留，后者作为事后统一复算；无需重跑模型。新实验一律用等 input、等 session 的 paired-log 估计。PR166 的原始材料远端交付可并行收尾，但不能用 PR162 的已完成交付替代。

## B. 主实验：结构与并行扩展

### B1. 预先声明的几何

主配置是各平台现有 Qwen3-8B Q8 部署。起始 caller widths 为 **1、2、4、8**；q=8 是需真实实现和验证的扩展，不是改一个 guard 后宣称支持。CUDA 的 head-preference helper 与 Vulkan 原生形状条件目前都有 q≤4 限制。记录实际物理 microbatch、projection/FFN width、attention group width；caller q=8 被内部拆成两个 q=4，不能当成真正八行并行。

上下文配置为现有 C=1024 和新 C=4096。先做零 forward 容量与真实 shape admission；4096 无法保持既定权重/placement/安全余量时，预先登记 C=2048，或者将不可运行项保留为 unsupported。禁止为了通过而换量化、挪动层、删长输入或更换参考。

**新容量意味着新部署配置。** 对新 C，用保留的原数值实现事先冻结该配置的串行参考 R_C；旧 R_1024 和旧反例不变。先验证新输入 adapter 未改变相应 scalar recipe，不能把 R_4096 冒称成原 R_1024 的逐字节相同执行。需要变更数值库才能支持新 C 时，单列新的研究配置，不能混入原参考兼容结果。

在 C1024 使用物理边界 256、768；在 C4096 使用 1536、3072（C2048 则为1024、1536）。这些是预定的物理 slot 值，不等同于 nominal prompt length。每个 q 检验不跨界 head=B−q；q>1 时再检验跨界 head=B−floor(q/2)。提前由真实 allocator 状态计算 e_i 和组宽，保存预测，再运行 native 观察。q1 的四个 common-path 控制加上其余三个宽度的两种对齐，在四个边界上共 **28 个结构坐标/主配置**。

使用真实状态/操作数的 teacher-forced fixed-work replay，固定各 arm 消费的 tokens、cache 初态与已知 query。每个坐标比较完整输出向量；代表性首层与中层捕获用于解释派发，不能用抽查层代替端到端向量检查。每个坐标三次 fresh-process 固定配对块，不采用追阈值重复；所有不支持或不一致的坐标保留。微基准单位与自然请求数分别报告。

### B2. 必须回答的替代方案

| 路径 | 实施方式 | 作用 |
|---|---|---|
| Scalar | 全 target 按参考逐行执行 | 数值锚点和串行代价 |
| Repaired PQ | 同精度/放置规则，attention 逐 query 子图 | 已有强局部表示基线 |
| Local QB | 全 q 的 projection/FFN，attention 按相容组 lowering | 被评估的方法 |
| Caller-split QB | 在相同物理前缀变化处拆整个 target caller，各子调用内 QB | 最直接、更简单的相容调度替代方案 |

所有路径使用同一候选运行时与显式算术规则，scalar 的数值结果先对原 R_C 资格。Caller-split 保留相同逻辑 token、输出 reservation、mask、pending/KV 与 commit 语义；输入已知时不得重新采样造成工作差异。它若不保持原参考，报告首个真实执行差异，不伪造为合格强基线；此结果可解释局部与全图拆分为何不等价。原生默认 fast path 可作为兼容/成本背景，但不保持 R 时不进入“合格方法最快”的排名。

主比较不是 Local QB 是否赢 Scalar，而是 **Local QB 与 Repaired PQ、Caller-split 的区别何时出现、来自哪里**。记录 group 数/宽度、完整 target 时间、实际 graph 调用、可观测 kernel 数、mask 连续化开销、planner/graph-build/reuse 成本。q/G 只是平均组宽，不是实际 GPU 利用率或加速比。重探针不进入正式计时。

可用分解 T = T_dense(q) + sum_g T_attention(e_g,w_g) + T_planning/views/graph 组织解释；先在短上下文坐标上估计开销趋势，再检验预留长上下文/另一对齐的预测。报告预测误差与失效原因，不把同一数据拟合后再称“预测”。这不要求额外训练一个路由模型。

### B3. 一个结构性迁移点，不扩散成模型跑分集

规则确定后，在已有 SmolLM2 的 MHA、head-dim64 结构上做小型主动启用验证，优先 RTX。该模型以前运行过，不能称为全项目未见模型；这里检验的是未参与新规则调整的结构迁移。固定四个开发外输入和一个真实边界，读取实际模型结构。已有 Vulkan 128/32/8 guard 不得直接删掉；只有实现了对应 head/stride lowering 才能称 Vulkan 支持。不能实现时如实保留边界，不自动寻找第三个平台或多个替代模型。

## C. 一次自然请求成本研究

B阶段完成后冻结候选及每种部署配置。每平台主 Qwen8B 选 **12个自然新输入**：代码/数学 × 短/中/长三个长度层 × 每层两个。长度定义和候选池先于输出；使用已有 exposure index，不重复归档扫描。不通过截断、填充或改题制造“自然”边界。无法满足某层时先登记具体缺项；保留所有选中输入，包括 EOG 早于预计边界的请求。

主终点是 ordinary target-only 的参考相容 prefill/完整请求价值；生成 continuation 仍逐 token 执行。原有 speculative 证据作为另一应用保留，不为让 B570 draft 盈利另开优化战线。

四个 arms 为上表 Scalar/Repaired PQ/Local QB/Caller-split QB，采用同模型加载策略、相同 context 生命周期、原参考 sampler/stopping 和固定已资格的 prefill 宽度。数值资格先于可比成本报告。每平台 **6 sessions × 12 inputs × 4 arms = 288个预定正式测量slot**，有各自同 arm warmup。不合格的arm保留失败记录，不放入“参考保持的合法加速比”；必要时保留空slot及原因，不能通过改R强行凑满成功计数。部署时可选模式不得利用评测输入的原参考答案或个例最快结果。

建议四 arm 的 Williams 顺序为 [0,1,3,2]、[1,2,0,3]、[2,3,1,0]、[3,0,2,1]；每 session12个 input 块各顺序3次，input 顺序固定 seed 打乱。测量前写出 manifest，保持配对块相邻。六个 session 不是六个独立硬件平台，也不能把 token/vector 数当样本量。

主报告给出全部 session 点、输入级差异、方向反转和等权几何比值。若报告区间，使用事先指定的 session-level 对比及其小样本假设，保留原始点；不筛块、不改变效应口径、不以达到显著性或门槛为停止条件。模型加载、资格/参考准备单列。安全保护在请求边界或外层运行，逐 decode 重查询、完整向量写盘与重观察不进入生产服务计时。

RTX Qwen14B 的 partial-offload 数据独立展示；只做必要的宽度/长上下文迁移控制，不与8B合并成模型规模曲线。新 speculative widths 仅作为真正支持后的小型附加出口，不要求两平台都赢。

## 完成条件

交付一个共同可调用的核心、两种实际 backend mapping、28坐标的预测/观测与性能表、一个简单强替代基线以及一次自然面板。接受中性或负性能结果；它们应给出采用范围，而不是引发新一轮追测。若出现新的具体算术机制，可保留失败后定点诊断并修复；工程问题可自主解决，不必每次请求许可。不得靠模型名/输入ID/输出/阈值特判或全模型退回串行伪造扩展成功。

主文据此围绕“参考约束怎样决定并行组织”展开；旧项目历史、归档数量和逐项审计进入附录/产物。先集成真实结果，不因目标是 TPDS 就凭空扩大保证。无第三平台、MoE、强制多机或全新形式化证明任务。
