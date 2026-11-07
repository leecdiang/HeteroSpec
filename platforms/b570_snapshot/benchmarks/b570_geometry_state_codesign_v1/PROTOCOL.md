# 研究协议与决策门槛

## 1. 科学问题及预期增量

主问题：当数值组织和硬件批处理粒度相互耦合时，是否能用**参考兼容的状态形成计划＋局部 query-to-batch 图表示**，保留原参考并减少把整段目标计算串行化的代价？

这不是固定 prefill/decode 形状的首次提出；CoRun、LLM-42 已有相关路线。也不是首次发现 KV 敏感性。可主张的增量要来自：在同一量化参考下，自然执行的状态形成×局部表示对照，以及相对于 PQ、无状态约束 QB 和完整参考的可用性/成本。

三个主要假设与竞争解释：

| 假设 | 竞争解释 | 区分方式 |
|---|---|---|
| 固定 producer 组织可增加 QB 的完整请求资格 | 只修 prefill 不够，后续 verification 会重新形成不同状态 | 自然完整输出与提交后状态/位置；不靠 boundary0 输出推全程 |
| QB 保留外围真正的多行计算，并避免 PQ 显式逐 query 子图成本 | 只有逻辑 caller 变宽，实际仍为多个 width1 micrographs | actual occupied width histogram＋graph/row/dispatch 分层计量 |
| 效果能迁移到未见输入和多个长度区间 | 只是四个已暴露 GSM8K 的特殊现象 | 冻结后两任务域×三长度区间的 24 个未见 prompt |

## 2. 参考与干预的精确定义

### 不更换参考

主参考 R 是 PR92/97 原始 stock-compatible ordinary UB128 recipe，必须从原机完整制品核验目标权重、tokenizer、格式、runtime、capacity1、逻辑 batch512、ctx1024、threads10、FAoff、F16 KV、greedy、完整 EOG-or-cap128。未知字段不得从显卡型号猜测。

R 在 P1/P2 都直接调用原始参考 runtime，不用新编译版本替代。R_SHADOW 是新执行器关闭改写时的影子臂，仅用于 P1 接入控制；四个校准输入上的一致不被外推为未见输入一致。P2 每个未见输入、每个时间块都真正执行原始 R。

### Producer 两水平

- `reference128`：一次完整 caller 提交，内部 ub128，expected occupied widths `[128,...,remainder]`，只在完整 prompt 最后绝对位置请求 logits。
- `bulk512`：一次完整 caller 提交、ub512，prompt≤512，所以预定一个 n-token micrograph。

两者的**候选** output capacity 都固定4；reference shadow capacity1另列，不把这一差异隐藏。所有候选 prefill 的 attention 保持 MQ，这样 producer 因子不是同时改变布局。若现有图路径不能固定这些条件，则标 `FACTOR_NOT_ISOLATABLE` 并停止因子解释，不能改名成已控制。

`reference128` 名称仅指参考分段计划，**不预设形成的所有内部字节已等于原始 R**。诊断要检查逻辑 K/V、位置与初始 full logits；若只能证明端点一致，就保持该层级，不写成完整 state identity。

### Consumer 三水平

MQ、PQ、QB 在所有 speculative 臂中保持 k1、target continuation ub4、capacity4、完全相同的 draft、acceptance/bonus/rollback。query caller 最大2（pending＋1 proposal），并不预设实际微图宽度就是2。

PQ 只在 attention 中按 query 构图，**不能复用原先全 target UB1 串行化的路径并改名 PQ**。QB 将 query→第四维及对应 mask view，外围 projection/FFN 保持多行；shared KV、GQA、mask 和输出次序必须保持。

q1 共用原单query路径，作为实现负对照。草稿有独立 role/phase、独立 prefill schedule，禁止继承 target 的全局 schedule；不同长度的 draft prompt 不能照抄 target chunk list。

### 九臂

| 臂 | prefill | continuation | draft |
|---|---|---|---|
| R | 原参考分段及普通路径 | ordinary，capacity1 | 无 |
| M_B_QB | bulk512 | QB，capacity4 | 无 |
| M_R_QB | reference128 | QB，capacity4 | 无 |
| C_B_MQ / C_B_PQ / C_B_QB | bulk512 | 分别 MQ/PQ/QB | 固定 Q4_K_M，k1 |
| C_R_MQ / C_R_PQ / C_R_QB | reference128 | 分别 MQ/PQ/QB | 同上 |

这比只比较“改之前/改之后”多，但能分开：producer 作用、局部表示作用及两者组合；draft 收益用 M_p_QB/C_p_QB；QB 独有表示收益用 C_p_PQ/C_p_QB。

## 3. P0：不启动 GPU 的工程准入

恢复固定源码和参考制品；检验真实接口，完成独立 native 图层移植；模型和算术 backend 优先不变。新图层必然可能改变 llama DLL/worker SHA，必须记录新旧差分与 manifest，不能要求所有 DLL 字节相同又同时声称已加入新图变换。

严禁自动去掉 PR101 的 target-only guard 后就运行 speculative。以经过验证的 PR97 通用 speculative 事务为继承起点，单独接入 PR101 的自然 prefill 分段逻辑；保护独立 role/phase、pending consumption、rollback和output reservation。见 NATIVE_INTEGRATION。

P0 在最多两轮有明确变更范围的移植/集成修订后必须作 GO/NO-GO；不是要求只允许两次编译命令，也不是隐瞒编译错误。若需要重写 Vulkan 算术 kernel、改模型精度、变更 sampler、做 F16 cache-write 注入，停止本设计并报告，不能在此预算内扩展。

生成 `F0_EXECUTION.json`，包括准确输入、顺序、预算、代码/编译器/backend/driver/model、所有实际序列化请求、启动/关闭/异常/计量规则。远端完整 commit 字节回读后才能启动。不是给候选 F0 增加一个 true 字段。

## 4. P1：80 starts 的最小可行性研究

固定4个校准 sentinel：/1248、/831、/1011、/1249，全部是已暴露输入。

- 原参考 R：4×2 fresh-process counts =8。
- 新参考 R_SHADOW：4×(1 counts＋1 diagnostic)=8。
- 八个候选：4×8×(1 counts＋1 diagnostic)=64。
- 总80个fresh processes/requests；无隐式 warmup、probe、operator run、retry。

实际启动顺序已经在 planner 固定为：原始 R 的8次→R_SHADOW 的4counts＋4diagnostic→32个candidate counts→32个candidate diagnostic。`validate_plan`拒绝把候选提前到reference控制前；原机runner仍必须检查前阶段receipt才能进入下一阶段。

每次从prompt自然执行，清空KV/位置/pending/sampler；禁止使用旧donor。counts与diagnostic的完整endpoint应该相同。诊断只采必要的逻辑状态hash、完整初始logits、有限graph/dispatch汇总，不进行逐层巨量payload/API dump。

分类规则：

- wrong model/recipe/geometry/PID/actual request/source hash、观察改变输出、参考重建不一致、内存不够、counter conservation异常：**控制/基础设施停止**。
- 有效候选的完整输出不等于参考：**有效的 treatment counterexample**，不能拿其较短输出算“更快”；保留后继续预定安全臂，不为了让MQ失败而终止全部设计。
- counts与diagnostic各自有效但logits不同：保留数值观察变化；不能宣称bitwise稳定。若端点相同，数值因果解释需降级。

P1→P2的预定可行性门槛：原参考稳定、新参考shadow及观察对照合格；C_R_QB和C_R_PQ在4个sentinel完整合格；C_R_QB至少出现一个经过真实trace验证的occupied width>1 verification micrograph。这个门槛是选择值得研究的实现，不是未见输入验证。**不使用pilot速度或“正结果有几个”作自适应样本选择。**

若没有这个物理批处理杠杆，停止大面板；若语义/数值不合格，保留失败并报告尚未支持移植。不要再换head、找特殊prompt、扩大精度。

## 5. P2：真正的未见条件与性能研究（另行 GO）

### 输入

24个独立、此前未执行/未挑选的prompt：code / math 两域，各含64–127、128–255、256–512三个实际token长度区间，每格4个。保持自然文本、原模板和tokenizer，不截断或填充成合适长度，不根据答案质量/初步latency挑题。

先从来源绑定的数据导出纯 metadata＋direct IDs 的inventory；`select_holdout`按固定hash排名选择。排除所有历史PR的输入ID与prompt token hash，不止PR98/P2。历史暴露全集不完整时标 `EXPOSURE_NOT_ESTABLISHED`，不得叫blind/unseen。任一格不足4个，停止准备、在新执行前修订设计，而非运行后换题。

这覆盖两个任务域和三种prefill工作比例，不是第二模型、多GPU、超长上下文或任意服务负载的证明。本轮不买硬件、不上服务器、不加精度/模型搜索。待本轮确有广泛价值才考虑第二模型。

### 运行

24 inputs×9 arms×4 separated sessions=864正式请求，每个正式请求一个新process；同一process前有1个明确计账的warmup并清空状态（相同prompt、cache off），因此总1728starts、864processes。四个sessions分成两个日期块，s1距s0完成≥1h，s2距s0启动≥24h且不早于s1完成，s3距s2完成≥1h。这不是四个独立日期。

以task×session为block，九臂轮换/反序，顺序由固定seed产生。所有臂均运行，已知MQ不合格也不删除；若不安全则按停止规则保存未启动坐标。每轮R在所有任务上跨session稳定。

正式计时：模型已驻留，request reset、prefill、decode/verify、draft与reconciliation、必要的结束同步全部计入，最后token/EOG/cap一致。模型加载单列；不把诊断同步或GPU时间查询放进正式counts timer。以性能优势挑选任务或对照是禁止的。

### 预先定义的策略比较

`always_reference`、`shape_only→C_B_QB`、`producer_guarded→C_R_QB`；静态不支持或不是fresh_request时选择从prompt重新执行R，**不是沿未知KV继续R**。producer_guarded只在P1已通过后成为冻结候选；不读取validation output/logits/margin/latency选择路径。

策略评估报告优化覆盖、错误接受、unknown/拒绝及成本。当前源码只实现pure routing，不声称已测在线策略overhead。正式报告采用测到的直接recipe成本；要报告真实调度器总体速度，必须在原机将route调用置于同一计时窗口并保留计量证据，否则只标离线路由模拟成本。

## 6. 分析与判断

正式比较包括R/C_R_QB、C_R_PQ/C_R_QB、C_B_PQ/C_B_QB、C_B_QB/C_R_QB、M_R_QB/C_R_QB及M_B_QB/C_B_QB。任一成对比较只在完整预定面板输出都满足同参考时称qualified。错误/缺失不按0耗时、不缩短分母、不汇总成成功子集的胜利。

`analysis.py`已实现各arm vs R及10项直接成对比较、四时间块、两域×三长度格、回退/缺失/错误及warmup-measured进程对应。它只检查归一化record与可选raw hash；原机必须补独立raw字段重建与验证，不得把CPU合成记录算成native资格。统计时保留真实EOG和cap128端点。

统计单位：输入24；4时间块是执行重复；9arm不是9个独立数据集；draft acceptance按实际分母报告。主要给等权task-log平均、四session点估计、逐任务回归和总成本比；不在四cluster上制造很窄CI，不进行request-level bootstrap。所有中途aggregate保持withheld直到完整time gate。

实践意义不靠一个事后挑出的阈值：报告两域/三长度格覆盖及回退。只有C_R_QB在新输入恢复了原C_B_QB的不足，并相对R保留成本，才能说组合扩大了可用域。若原QB已经全部通过，新策略只是增加开销，就如实判为无新增状态策略价值。若只PQ/QB更快，则贡献仍是局部表示，而非状态约束。

## 7. 不钻牛角尖的退出机制

- P1没有稳定reference-compatible组合或真实batching杠杆：停止大实验，不改shader/math/量化救结果。
- P2效应只存在于历史四题、单一狭窄长度格或特定token：不得称普适；保留一次边界结论，不加第三轮同类搜索。
- producer约束的全请求成本全面吃掉收益：不做更复杂的online selector；优先结束此支线。
- 新硬件想法另处讨论。本PR输出可复用几何/状态/工作量摘要供其使用，不等待它、不擅自扩为RTL/PPA项目。
- PR105前沿缺口仍是未完成；不将本研究算成补齐其240 logits，亦不要求先跑完它才开始本研究P0。

## 8. 架构线协同（依据作者补充结论）

本研究不设计“提高草稿接受率的Tensor Core”，也不宣称发现B570 XMX缺陷。主要产物是：参考输出资格、正常执行成本、数值图表示与实际物理工作粒度的关系。接受率是次要工作量观测；固定参考/候选时不预设它必须上升。

另一个对话负责候选弹性验证单元的功能/周期/RTL研究，本任务提供有限、来源真实的geometry/work/tensor接口。不得将实际GPU opaque kernel当成已定义的算术DAG，不假设FP16输入+FP32累加足以描述舍入/规约。

若B570软件无法在不改算术backend的情况下获得multirow且参考兼容的执行，软件大面板停止，但其负结果可作为架构需求输入。这不证明新硬件不可行，也不是强行让新硬件“赢”的证据。architecture.py仅有显式假设的共享读下界和Amdahl敏感性，不是周期模型、PPA或实测流量。

没有“新增架构章节”指标。先验证是否存在强软件路径剩余的真实代价；若更好的融合/调度已能解决，贡献按软件—架构协同定位，不硬称新硬件。
