# PR104 之后的 CPU 研究协议

**设计协议，不是执行 F0、已实现模型或硬件正确性证书。** 本轮仅 H0–H3，额外 model/GPU/operator starts=0。旧 RTX E2/E1 不属于本轮新预算，也不能转移剩余额度。主研究对象是固定参考约束下的资源重组，而非改变 draft 模型或提高接受率。

## 0. 必须先结束已有 RTX 闭环

读取 PR104 最新分支与原机账本，对照本次已读快照 `50e64c7c8a2ac69fd59fd4b80310687754deb071`。当前仓库记录 E2 s0–s4 共 1,350 starts/270 workers 已完成，s5 和 E1 尚待；这不是保证接手时仍未完成。

先核对原 supervisor/锁/owned PID/SESSION receipts。已运行或完成的坐标不重复；不能为方便再次调用 prepare 创建第二份同名试验。未启动的 s5 使用已经认证的科学 F0 与 transport 补充规则。前序 session 完成后至少 1 小时、最后一组距第一组开始至少 24 小时；已记录 s5 最早北京时间 2026-10-15 12:27:07，实际准入取全部原门槛的最大值。晚开机可更晚，不伪造或压缩时间。E2 全上限 324 workers/1,620 requests，包含 324 warmups，owned 43,200 秒；已花费不可重置。E2 不得插入 Nsight、GPU queries、额外同步、新 kernel、驱动升级或高负载 CPU 模型。

六组结束后按原分析保留 1.02 practical ratio、全部任务/会话退化、完整原 R 资格、缺失和小 cluster 不确定性。不提前汇总、不挑快/相同的子集。若终止或协议失败，原样封存；不能追认合规或补跑已启动槽。E2 不能合法完成时，E1 依原协议保持 BLOCKED，不擅自解锁。

E2 完整结束且原准入满足后，完成 E1 的独立源码接入、CPU 负测试和前瞻 F0，沿原有授权执行：三家族×首/中/末层×prefill/continuation×q1..4=72 contexts；q2/4 的 min-key=128，q1/3=0，非完整 key-length factorial。上限 216 native requests（包括 warmups）、432 standalone operator starts、owned 21,600 秒。冻结原规定的输入选择，不换题寻找正结果；缺失 geometry 为 NOT_OBSERVED，own-path失败为 NOT_ADMITTED。HS_E1_LAYER/PHASE/Q/MIN_KEY 要通过真实 sanitizer/serializer，不仅存在于 shell。隔离构建，不替换 E2 runtime。实际数值/输出/输入生命周期必须逐项核验，kernel/DAG 不可猜测。

最后在 PR104 原分支交付 E2/E1 各自结果、全部成本、raw manifest、全新恢复与独立 CPU 复算。只有真实执行的检查才能写通过。旧任务的负结果或合规停止均可封存，不等于科学成功；封存之后才开始本研究重任务。不以是否正加速或 PR 是否 merge 作为新 CPU 研究前提。

## 1. H0：来源与剩余代价，一轮有界审查

恢复已经存在的 RTX PR98、完成后的 PR104 源码/数据。PR108硬件说明与PR109 B570结果只作边界输入，不等待、不接管B570。PR109记录的F0采样承诺与原R checkpoint行为不符，说明应核验承诺的实际语义；本轮不能将检查点伪称连续监测，也不能把它迁移成RTX必有同一故障。其C_R_QB反例不是RTX结论。

一份表包含：现有最佳同参考软件路径、作用范围、已测量、由源代码确定、仅是假设、UNKNOWN；区分启动/图管理、重复数据供给、算术依赖限制、状态生产/维护四种解释。PQ/QB请求比值不等于任何kernel份额；连续物理驻留、XMX/SM利用率或DRAM流量缺失就保持未知。

强软件审查最少覆盖：当前PQ/QB实现、合法的固定分块/固定归约、ragged query packing、KV multicast/共享、图复用/融合机会。官方FlashInfer fixed_split_size与Thinking Machines batch-invariant工作是近邻机制，不是已经在本量化runtime适配的baseline。不在本轮安装另一推理栈跑GPU或把公开速度直接抄作基线。

H0给出具体假说：例如同一数值分块约束下，独立query/输出上下文的细粒度资源绑定是否比现有粗粒度映射更省等待。必须说明所提能力不能由强基线同样合法实现的原因；若不知道，只能登记为待检验架构假设，不能写成RTX已证实缺陷。

H0允许进入一个有成本上限的探索性CPU模型，不要求先识别全部专有算术。但不得为使模型启动把UNKNOWN改为已测。若所有拟议能力都与强基线等效，给SOFTWARE_FIRST并以最小同能力parity测试收尾；不人为削弱基线制造差距。

## 2. H1：明确数值契约，实际实现一个原语

首版只研究 AV 型加权归约 `O[j,c]=sum_t P[j,t]*V[t,c]` 的上下文/数据供给。P是已有softmax结果或显式合成输入；不改变softmax、不声称整层融合attention/端到端模型已实现。不跳过被mask后为零的项来改变既定算术图，除非契约明确允许且有证明。

两个目标分别记录，不能混用：

A. DEPLOYED_REFERENCE：只在实际已识别的对应语义和同输入证据范围内比较既有RTX结果；有限PQ/QB相等不是完整归约树识别。
B. DECLARED_ARCHITECTURE_REFERENCE：没有A的语义时，直接定义新原语的明确有限精度参考。默认F32数据（F16 V先按声明方式转换），乘法RN-even到F32，再加法RN-even到F32，按t递增执行，不隐式FMA；转换、次正规数、signed zero、overflow与非有限输入处理必须写入合同。B上的正确性/性能不称为恢复RTX旧参考。

对每个(j,c)，算术DAG/步序/舍入点固定；不同上下文间可交错或换执行lane，不能重新括号化同一依赖链。独立顺序reference interpreter与候选scheduler trace checker分开实现，检查算术输出、微操作依赖、一次发出/完成、不可读旧epoch、资源守恒、无重复提交和回压下的进展。不能两边只调用同一段待测scheduler然后宣布独立验证。

标量舍入用经过测试的明确实现（例如合法可复用的SoftFloat，或独立整数位级参考）；不能直接用宿主float64求和并最后cast冒充逐步F32。至少包括不同关联导致差异、FMA/非FMA区分、舍入tie、次正规数、signed zero、非法输入与输入不变性测试。若只实现有限域，预先声明拒绝域，不能运行后删失败输入。

实际输入：从已存在且own-path/生命周期合格的E1快照按(family,phase,q)分组，每组在0/middle/last层的固定顺序取第一个合格上下文，最多24个。准入只依赖输入来源与own-path，不按PQ/QB是否相等或速度选择；相等失败也保留。缺组列NOT_AVAILABLE，不另跑GPU补齐。大型张量需缩小CPU范围时，在看候选结果前固定head/channel/key子视图规则、地址映射和裁剪标识；裁剪只是native operand subview，不是原完整算子replay。

合成输入与实际operand分别标记，数据由固定seed产生。未取得任何实际payload也可完成B类合成机制测试，但结果必须是SYNTHETIC_ONLY / NATIVE_VALIDATION_MISSING，不能声明普适、实际接受率或LLM端到端收益。

## 3. H2：同资源周期/事件模型，不只是图数公式

H1数值与控制检查通过后，真正实现离散事件或逐周期模型，输出可复算事件trace和每类等待。不得把Python自身运行时间作为芯片时延。CPU_F0在正式比较前冻结所有workload、资源表、mapping、种子、指标和比较方向，允许工程测试先修软件bug，但保留记录，正式结果不据此扩大扫描。

首版至少包含：计算lane数量/延迟/issue rate、上下文容量与读写带宽、KV缓冲容量与bank端口、广播带宽、队列深度/credits、回压、输入输出和部分结果流量、映射/切换代价。数据fetch不只按q乘tile字节，算清缓存可保留范围与真实模型层级。不能免费给candidate额外MAC、带宽、无限广播、零冲突或无穷context。

五个预先声明的映射：

- B0_FIXED_SHARED：固定数值分块与合法固定调度，允许KV共享和合理流水；不是所有query全串行的唯一baseline。
- B1_PACKED_MULTICAST：相同数值契约下的强软件/固定硬件映射，允许ragged packing、KV multicast、固定次序合并和相同可用缓冲；不能无理由禁止它的合法优化。
- A_CONTEXT：在B0基础上只引入候选上下文绑定能力，不新增供给能力。
- A_SUPPLY：在B0基础上只引入候选供给组织，不新增上下文能力。
- C_JOINT：两种候选能力组合。

若两候选能力中的一种本来就在B1，写清楚，不重复计为创新。C_JOINT与B1具相同合法schedule集合时应得到同能力parity，差异可能只是调度策略而非新硬件。候选真正多出的粒度/连接/上下文功能必须有具体模型实现与代价；对基线的限制没有真实来源时只可称抽象架构情景。用小图穷举或独立下界检查baseline调度质量，防止故意选差顺序。相同总buffer预算时计入tag/accumulator/context占用；同字节预算不等于已证明同硅面积或同频率。

正式模拟总cell attempts≤1024，重复和失败均计入。先冻结一个完整小网格，推荐q∈{1,2,3,4}、key∈{64,128,256,512}，覆盖带宽充足、带宽受限、bank冲突三类明确数值资源情景；其余维度固定或用预定小面板，不暗中全因子扩张。每个workload/resource点五种映射全运行；若硬预算不足，在任何正式结果前缩小整组参数并记录理由，不能只删慢/错误candidate。合成资源值是抽象输入，不填写猜测的RTX频率/带宽。

每个cell保留：数值资格、总周期、计算/访存/上下文/回压等待、供给字节及所在模型层级、资源峰值、输入/输出/trace绑定。cycle模型有未知参数时给范围与敏感性。确定性仿真grid不是随机样本，不做虚假统计显著性。模型误差不能由与自己相同的实现互比得出。

强制负对照：q1；baseline与candidate拥有相同能力/供给时的parity；给candidate新增开销可消掉收益；收紧带宽/端口后不会出现超过资源上限的吞吐；对依赖图重新关联的非法优化被拒绝；相同KV地址但不同ownership/epoch不能共享；stale/重复/缺失事件被独立checker拒绝；buffer溢出表现为背压或明确非法，不静默免费spill。

## 4. 端到端推断与停止边界

本轮默认只报告原语/条件周期模型，不给新的实测RTX端到端speedup。若沿用原生输出轨迹，数值和接受/rollback决策不能被模型悄悄改变。完整endpoint一样也不能推定中间trace相同。改变数值决策后需要重新生成对应functional trace；本轮没有运行完整模型，不虚构它。

可报告标准条件关系 S=1/(1-f+f/s+h)，注明f为非重叠基线关键路径份额、s为该部分速度假设、h为新增串行开销份额。获益条件h<f(1-1/s)只是代数解释，不是新定理。缺少可靠f时只给情景，不用micrograph数推kernel占比，不从E2 wall拟合。模拟器无法校准到真实RTX时称抽象模型，不能因模型没有实物便放弃有界设计研究，也不能假称精确GPU模拟。

H0–H3本轮子进程累计运行上限14400秒、单进程RSS≤8GiB、一个重任务并发、派生输出≤2GiB，所有正式cell attempts≤1024。测试、失败和恢复成本记录，既有raw只读。超过上限、需要新GPU采集/完整runtime替换/RTL/PPA、或需要第三轮结果驱动架构搜索时停止扩展，交付现有结果及下一阶段建议；不购买云资源/硬件。

## 5. H3：一次闭环与下一步

输出一份RESULT和必要CSV/JSON、代码与测试，不制造多套重复报告。给出：

- PR104终态及独立复算，哪些旧结论supported/refuted/unresolved；不得改写原阈值和实验历史。
- 本轮数值契约属于A还是B，实际payload覆盖/合成范围、H1功能checker通过与反例。
- 对B1的增量究竟来自哪个新增能力，是否只是软件调度，是否被资源/开销/误差覆盖。
- 所有负结果、缺失、停止与预算，不仅是最优网格点。
- 一个结论：SOFTWARE_FIRST、HOLD_MISSING_EVIDENCE、或CONDITIONAL_MODEL_SUPPORT。最后一项只允许提出下一项小规模验证，不自动开GPU/RTL。

论文只交付claim/evidence表与章节建议，不修改PR102正文或代填模拟数据。B570提供独立边界，不要求其通过才证明RTX结果；不声称跨GPU统一逐位参考或新硬件提高模型准确率。
