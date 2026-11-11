# HeteroSpec：从 1%–2% 到约 5% 的研究判决与方法候选

## 研究结论

当前证据支持继续研究“在既有数值参考约束下选择投机执行前沿”，但尚不支持
“已经找到普适 5% 加速的新解码方法”。值得投入的残余问题是：同一候选工作图上，
能否利用合法分段、执行批量和状态收敛的联合决策，降低强工程基线之后仍存在的
完整请求成本。方法的独立收益必须在这些共用优化都到位之后计算。

本次不改论文、不替换历史 reference、不把尚未确认完成的 S3 记作完成。后续实验必须
有新的提交、独立预算和明确配置。GPU 实测未在当前会话执行。

## 当前论文主线与这轮优化的关系

本轮先核对 PR220，随后收到作者对 PR222 的审稿，并重新读取最新固定稿
`e8a4981ef7db8f05cff7144fd4edc6e5a4109343` 的
[方法](https://github.com/leecdiang/HeteroSpec/blob/e8a4981ef7db8f05cff7144fd4edc6e5a4109343/papers/reference_compatible/20261111_tpds_mainline_rewrite/sections/03_method.tex)、
[结果](https://github.com/leecdiang/HeteroSpec/blob/e8a4981ef7db8f05cff7144fd4edc6e5a4109343/papers/reference_compatible/20261111_tpds_mainline_rewrite/sections/05_results.tex) 和
[评价设计](https://github.com/leecdiang/HeteroSpec/blob/e8a4981ef7db8f05cff7144fd4edc6e5a4109343/papers/reference_compatible/20261111_tpds_mainline_rewrite/sections/04_evaluation.tex)。
当前论文主线是 **Reference-Compatible Parallel Execution for Quantized LLM
Inference**：先确定保持数值参考的算术 recipe，
再依物理 KV 前缀与 extent 划分兼容组，在整个图切分或只在 attention 内切分，
并由同一个 state owner 管理各阶段的输出、提交、trim 和 pending token。

用户关心的独立 1%–2% 与“应用相对 target-only”不是同一个对照。当前草稿
报告三个 Linux 部署相对最快已测固定 M 的服务下降为 17.21%、25.54%、11.52%；
但在固定 draft policy 与宽度的公平分解中，8B packing 增量为 1.64%（W）和
1.56%（L），14B 为 0.99% 和 0.80%。这说明要增加约 5% 的独立方法收益，
必须越过已经很强的 backend-loop4 与现有共享工程优化。

| 当前主线发现 | 对下一轮方向的直接约束 |
|---|---|
| 8B factorial 中 2,224 个 verification cycles 只有 20 个需要额外 whole-graph boundary split，约 0.899% | 自然轨迹里局部切分机会稀少；不能从刻意 crossing 小窗口推导普遍服务收益。 |
| Q8 算术组宽度为四；k3 最多请求四行，不进入更宽 packing 路径 | 当前 k3 的 packing 主要作用在 prefill；只有把验证工作组织得更好，宽执行能力才可能贡献新的 verification 收益。 |
| q8 的同工作量效率与 k7 的 live workload 是两个实验；后者付出更多 rows 与 draft 工作 | 不能直接把宽操作的单位效率搬成更长草稿的服务收益。 |
| 32B mixed-Q4 普通生成中已有约 5.6% 的 grouped 增量，但对照为 graph-level scalar-column，grouped D4 又慢于最快 M | 这是特定 recipe/对照下的执行层结果；不能充当普适新投机控制方法的 5%。backend-internal loop 与 target-only 仍要保留为强对照。 |
| Vulkan 的 crossing append 有明显局部收益，但自然 AUTO 与完整 speculative pilot 未建立相应服务优势 | 支持域、物理几何发生率和 draft 成本必须进入评价，不能只展示有利边界。 |

因此候选研究应在现有 phase executor **之上**选择真正可达的验证/继续前沿，
同时保留原数值与状态合同。它不会仅因加入“frontier”名称就变成新的方法。
如果后续只有执行 recipe 在有限域改善，应按这个实质写成体系结构贡献；若
因果前沿选择在共同 recipe 上仍有独立收益，才有依据建立新的解码路径叙事。

## 一、为什么现有收益容易停在 1%–2%

### 1. 更便宜的局部操作未必覆盖足够多的服务时间

公开 PR213 的 Windows RTX、16 roots、8 repeated blocks、cap96 面板中，
最快观察到的固定臂为 LOCAL-loop4-k3，总服务时间 183.035577 s。其中 target
prefill 为 65.1487578 s，target verify 为 72.1597334 s，draft proposal 为
25.2019812 s。它们分别占 35.59%、39.42%、13.77%。这些是原面板的 host phase
时间，不是 CUDA kernel profiler 分解，也不能移植为 A5000 的相同占比。

若只改变 verify，完整服务减少 5% 要求该阶段减少约 12.68%；若只改变 proposal，
则要求减少约 36.31%。因此单个小算子下降几个百分点通常不足以支撑服务目标。

证据：[公开结果](https://github.com/leecdiang/HeteroSpec/blob/ba5b4c8e01d50d4bfaab1ac3908f798347be063a/benchmarks/rtx_q8_transfer_20261109/results_20261109/LIVE_RESULTS.json)、
[完整成本说明](https://github.com/leecdiang/HeteroSpec/blob/ba5b4c8e01d50d4bfaab1ac3908f798347be063a/benchmarks/rtx_q8_transfer_20261109/results_20261109/cost-rechecked/COMPLETE_COSTS.json)。
逐请求 phase 重算使用该公开 archive 内 `records/LIVE_RECORDS.json`，SHA256
`53d76c43d4b2fa378855b90f76d9bcb60e509d4086fddd630e3c0f51f6197487`。

### 2. 尾部延迟修复是必要的共同基线

已完成的真实 M2 request CPU 对照有 32 对请求、552 对完整前端读取向量、
272 对活跃序列状态，逐字节一致。候选省去 29 次不需要的尾部 draft 调用，
同时恢复 19 次必须保留的调用。该观察证明的是当前合成 F32 fixture 的请求
实现正确性，未测生产 GPU 收益。见 [上一提交的结果](https://github.com/leecdiang/HeteroSpec/blob/d6053addcd973e503ebeaae495b3326d6bf99bd4/benchmarks/frontier_cost_v1/RESULTS.md)。

在旧公开记录上，用每个请求自身的 proposal phase 均值估算，尾部修复对应
约 1.56%–1.58% 的原服务时间。这是 proxy，包含均匀单调用成本等假设。不能将
它与另一个算法相对未修复基线的比例相加，也不能把旧时序估算改称新测量。

### 3. 普通两段验证没有在该面板上减少 target 调用

旧 k7 轨迹中 2,296 个 cycle 有 1,224 个需要第二段。直接 q4→q4 reveal
因此需要 3,520 次 target q4，强 k3 臂需要 3,504 次。给双方相同的 cap-aware
目标行数上界后，二者为 13,960 与 13,944 rows。长草稿方案还先支付了更多
串行 proposal 工作。这否定了“普通两段切分已经通过少调用取胜”的解释；
这些工作量并不是对所有新策略或硬件时延的上界证明。

同样，逐 root 从旧固定 k3/k7 臂事后挑选，不能得到优于同方法 k3 的结果。
允许在请求内部换动作是更大的问题，但必须重新取得对应数值和状态资格。

### 4. 调用数的剩余空间尚未变成可实现的收益

旧记录的删失前缀分析保留首次拒绝之前的真实信息，隐藏之后无法观测的草稿。
在 16 个独立 root 上，一个使用未来结果选路的已知边路线可使 target calls
从 438 减为 287、rows 从 1,752 减为 1,479；q4 投影组仍为 438。
它是 hindsight 机会诊断，不能当在线控制器。

给双方共同尾部修复后，16 roots 的单 block 计数对应如下展示性模型：

\[
\text{saved}=151A+151S+24D-H.
\]

其中 A 是未测的可移除 target 外层调用成本，S 与 D 分别为 draft sync 和
proposal 成本，H 是该 block 的新策略、形状切换、恢复等总成本；没有减少
投影组的 G 项。使用各旧请求自身 phase 均值汇总到原 8 blocks 后，调用系数
为 1,208A，相应 H 也按 8 blocks 汇总；A=H=0 的额外节省 proxy 约 1.98%。
达到 5% 需要 A 约大于 4.498 ms/被移除调用；H 会继续提高门槛。该数值只用于解释
旧面板的机会条件，不可把新的 q8−q4 差额当作 A，也不可套用到另一 GPU。

### 5. 静态 kernel 指标已暴露基线混杂

之前的 Rows2 原型没有在公平控制下显示更少核心 load/arithmetic 指令。
共同使用 `launch_bounds(128,1)` 时，原生 dense q4 与 Rows2 都占 64 registers；
共同去掉注解后，分别为 48 与 53。初始寄存器优势来自比较配置不一致。
这些是 SM86 编译观察，没有动态 occupancy、带宽或时延结论。
因此当前不把 Rows2 放在首要正向路线，也不给静态代码减少写性能百分比。

### 6. B2 已有局部超过 5% 的点估计，完整服务仍需覆盖率

本轮重新按每个 worker 的两次 q8、两次 q4pair 测量计算均值比，再对四个
进程取几何均值，复现了原 B2 的四个结果。没有新增 GPU 调用。

| B2 core / boundary | q8 相对 q4pair 的局部时间下降 | 假设该比例可代表所有替换窗口时，服务下降 5% 所需覆盖率 |
|---|---:|---:|
| loop4 / 248 | 0.956% | 523.26% |
| loop4 / 252 | 2.193% | 227.95% |
| packed / 248 | 6.301% | 79.35% |
| packed / 252 | 5.243% | 95.36% |

最后一列仅为 `0.05 / 局部下降比例`：它假设被替换操作数量不变、比例能代表
所有相应窗口、其它工作不变且无新增开销。超过 100% 表示在这些假设下，仅靠
该替换达不到目标；不能外推为其它控制策略不可能获益。两个 packed 点说明局部
5% 并不缺乏先例，同时说明仍需要测量这类工作在完整请求中的实际覆盖率。

B2 只有已暴露 root、两个 boundary 和有限进程重复，不能据此宣称模型泛化。
更不能将它与上面另一部署的 RTX phase 占比相乘。
[原始公开 B2 重算](https://github.com/leecdiang/HeteroSpec/blob/4fe337a8ff349d547023f9dd60b8e114e5323207/benchmarks/server_expansion_v1/strong_baseline_followup_20261110/RESULTS_B2_20261110/INDEPENDENT_PUBLIC_STATS_01.json)
及本轮 [可复算结果](research/EXPOSED_PANEL_ECONOMICS.json) 保留了身份与限制；
脚本为 [economic_review.py](research/economic_review.py)。这些历史摘要不进入
当前控制器的成本目录。

### 7. 一个真正因果的接受预测回放，暂未胜过更简单对照

本轮在已公开 LOCAL-loop4-k7 的 session0、16 roots、287 个真实 logged cycles
上，按原文件顺序逐次“先预测、后观察”。按位置的 Beta 估计只更新真实匹配
前缀与首个拒绝，共使用 1,301 次有效 prefix trials。first4 匹配标签有 153
个真、128 个假，另 6 个在四行之前终止而删失。

在相同 281 个可观察标签上，位置条件概率乘积的 Brier 为 **0.25757**，仅用
过去 first4 成败频率的 Beta 对照为 **0.25185**（越低越好）。这次固定回放
没有显示位置模型更优；没有置信区间，也不是两者总体差异的显著性判定。
初始化、有限样本和顺序均会影响结果，不能据此证明更强预测器没有价值。

这个标签只预测“前四个候选是否匹配”，并不等于“经过 CAP/EOG 后还会继续”。
该诊断没有执行反事实动作、没有重建替代请求轨迹、没有估计时延，也没有将
已暴露 roots 当作新确认集。它补上的是从 hindsight 机会到在线算法之间的一项
实际检查；目前还没有理由声称可用因果信号已经足够取得那条 oracle 路线。
可复算入口见 [trace_diagnostic.py](controller/trace_diagnostic.py)，具体固定摘要
与独立重算见 [控制器说明](controller/README.md) 和本轮独立审稿。

## 二、建议保留的研究问题

工作题目可以先写为 **Reference-Compatible Frontier Scheduling for Speculative
Decoding**。这是待验证的研究描述，不是已经确立的新方法名称或首创声明。

### 状态与动作

在 greedy、固定模型与数值参考的当前范围内，用状态 s 表示已提交前缀、已经
计算并已观察的 draft/target 前沿、待处理 token、活跃 KV 范围、已知 cap、
graph/shape 条件及资源配置。策略只能使用这个时刻的信息集。

一个完整动作不只是“选择 k”：它还要说明追加多少 draft、验证哪一段、采用
哪种合法 lowering，以及各接受/拒绝/终止结果如何 materialize、trim、catch up
到下一状态。已有完整草稿的成本是沉没成本；在验证前截短不能退还它。

记合法动作集合为 A_R(s)。其中的 R 必须先声明，动作资格必须覆盖输出向量、
状态及后续 continuation。相同 token 不足以合并状态：本次 CPU q2 对 q1+q1
的反例恰好保留 argmax，却改变了完整向量及活跃状态。

本次 q1…q8 probe 的 q1 参考只是已声明的诊断参考，尚未桥接为历史 R。
它在 q2 停止，不能推出 q4↔q8 等其它候选之间不存在合法变换。真正的阶段
资格应从原 R 已知可部署的路径出发逐动作确认；不能把通过整个 q1 面板当成
所有研究路径唯一的入口。

完整问题的一个表述为：

\[
V(s)=\min_{a\in A_R(s)}\left[C(s,a)+\sum_o P(o\mid\mathcal F_t,a)
V(F(s,a,o))\right].
\]

这里 C 必须包含执行及状态收敛成本，F 必须给出真实的下一状态。这个表达式
本身是标准决策建模，不构成新颖性。本次最小实现使用有限块 surrogate，不能
把其最优解改称整个请求的最优解。单步“期望 token/期望时间”同样没有这一保证。
该合成模型还假设到达相同前沿的后继已收敛为同一个成本相关状态；当前实现
不认证这种物理等价。若不同路径留下不同 graph/cache 条件，实际决策状态必须
保留这些区别，不能只按逻辑前沿合并。真实运行接口仍保持 abstain。

### 与体系结构的实质联系

| 体系结构因素 | 策略需要认识的事实 | 必须测量或证明的量 |
|---|---|---|
| 量化算术分组 | 宽度变化可能改变量化、归约与路径 | 合法 q/recipe 集合，完整向量与 KV |
| 权重重读与共享执行 | 少 rows 可能多一次完整 target pass | 同历史、同状态的实际阶段成本 |
| KV extent / 分配几何 | 逻辑前缀相同不代表物理状态相同 | head、extent、dense、active bytes、后续状态 |
| GPU graph / shape | first-use 与 reset 后执行不等于热图 | 实际 build/reuse，编译和失效成本 |
| CPU 与 GPU 同步 | 小动作的决策、复制、同步会侵蚀节省 | 控制器耗时、完整请求时间及恢复代价 |

新方法若能成立，贡献应来自一个能减少完整服务成本的、既有强基线没有的合法
执行变换，或这种变换对应的可利用问题结构。字段更多、状态命名更复杂和更严格
审计都只是实现条件。

## 三、新颖性边界

| 已有工作 | 已经覆盖的关键内容 | 本项目必须进一步证明什么 |
|---|---|---|
| [TurboSpec v3](https://arxiv.org/abs/2406.14066v3) | 环境 profiling、反馈式 speculation 控制、goodput | 在同等控制与工程基线上，固定数值参考带来什么额外可执行优化 |
| [PEARL v3](https://arxiv.org/abs/2408.11850v3) | 首 token pre-verify 与验证期间继续 drafting | 分段边界和状态处理有何非平凡增量，完整计入串行草稿成本 |
| [PACER](https://arxiv.org/abs/2602.01274) | 可训练层进行 blockwise pre-verification，动态停止 draft | 不能仅把“分块+自适应长度”作为新方法；需要不同机制及对照 |
| [EVICT v2](https://arxiv.org/abs/2605.00342v2) | drafter 信号结合离线成本，截取 MoE draft tree | 当前精确状态/恢复条件能否改变可实现决策及收益，而非重述成本感知截短 |

上述近期复核基于各论文 primary abstract；前一轮的更深入源码/论文检查已经
覆盖 native adaptive、lazy tail、tree 与异质 allocation。这里不据摘要断言
某论文没有一个隐藏的细节，也不把不同输出合同下的速度数字移作本项目证据。

## 四、下一轮实验应该决定什么

完整方案见 [STUDY_DESIGN.md](STUDY_DESIGN.md)。按信息价值依次执行：

针对最新 PR222 审稿，另有 [TPDS_FOLLOWUP.md](TPDS_FOLLOWUP.md)：优先核实
既有 S3 的强基线完整服务结局，再补同面板 phase 分解、recipe/guard 证据表、
长前缀分层与同合同 runtime。这里列出的新控制器诊断不能替代那些论文缺口。

1. **生产请求桥。** 先验证真实模型和 GPU 上的 eager/deferred 请求行为、完整
   capture 与状态收敛。短 cap 的有限诊断只回答实现问题。干净计时与带 capture
   资格之间还需有明确桥，不能凭 token 一致授予正式性能资格。
2. **同历史成本表。** 执行原固定 target-operation profile。出现资格失败就
   保留失败；合格的整段 q8 / q4+q4 / q1×8 成本只用于相应宏动作，不能自动
   充当看到首段结果后再决策的阶段成本。
3. **必要的 outcome 成本。** 对候选策略实际会调用的阶段，补齐继续、拒绝、
   cap、已观察 EOG、materialization 和 draft catch-up 成本。缺任一分支便
   不能让策略把它当零成本。先检验净收益余量，再扩大请求面板。
4. **冻结因果策略。** 用独立开发输入选择参数；已暴露的两个历史及旧 16 roots
   均不能冒充新确认集。决策接口不接收未来真实接受长度或未来 EOG。
5. **完整服务与跨配置确认。** 在同等工程基线下实施 controller×executor
   交叉消融，再分别检验不同模型、长度、硬件/软件配置及不利样本。

若实测可合法省下的成本，在计入策略及恢复之后连 5% 的必要条件都不满足，
应停止扩大该单请求路线。不同 proposer、多请求异质 allocation 和新的 kernel
分别属于另一个干预；应建立新的对照，不能补进本路线的分子来凑比例。

## 五、本轮新增工作与开放项

独立审稿已用原 q1 记录副本复现旧诊断工具的五类准入缺口：JOB token 漂移、
RUN 超时/失败状态、model 身份漂移、不完整 repeat 面板、缺失实际模块记录。
旧工具的 raw 重放成功不代表这些记录可以进入控制器成本表。原 CPU 数据及其
独立逐字节审计结论保留；新接口专门收紧这次权限提升。

本轮最小控制器和生产实验入口的最终范围、实际测试及仍缺的桥，以新增模块
README 和本轮独立审稿为准。当前没有真实阶段成本目录，策略应拒绝从缺失数据
作性能决策。合成测试用于验证决策与拒绝路径，不作为解码收益。

**最终判定标准：** 约 5% 应当是对冻结强基线的完整服务独立增量；普适性应
落在明确声明并实际测试的支持域；新颖性应落在可复现的算法/执行机制。三个
问题都需要各自证据，不能用其中一个替代另两个。
