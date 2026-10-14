# 体系架构结合点：两个粒度，而不是往软件论文中硬塞一块 RTL

## 1. 面向可迁移机制的问题

本研究将 `logical verification width`、`physical target micrograph width`、`attention numerical grouping` 和 `state-producer partition` 分开。

传统的“为一致性把所有token串行化”把数值分组和硬件工作粒度捆在一起。候选目标是让attention维持单query数值组织，外围projection/FFN继续多行执行，并在必要时约束形成状态的prefill分段。这是一个编译图/运行时与加速器执行组织的协同问题。

B570上历史caller2→两个width1 graphs意味着高acceptance没有自动变成实际graph摊销。新实验必须观察是否改变这一物理工作组织，而不是再写一次“接受率不是速度”。

## 2. 可以测什么，测不到什么

| 等级 | 证据 | 可以解释 | 不可以推断 |
|---|---|---|---|
| L0：自然完整请求 | reference endpoint、resident request wall、draft成本、归档失败 | 实际用户可见收益及资格 | kernel占比、HBM/GDDR流量 |
| L1：native工作组织 | caller rows、实际micrograph widths、rows/graphs、accepted/committed、rollback、graph构建/复用计数 | 是否真的multirow、图碎片化/重复工作 | micrograph=shader launch；减少图数必然加速 |
| L2：backend汇总（可选） | 实際dispatch计数、pipeline身份/工作组形状、已完成Vulkan timestamps | dispatch粒度/调度开销的有限证据 | XMX利用率、L2命中率、真实DRAM带宽，除非另有真实计数 |
| L3：新硬件架构（本PR不做） | 明确ISA/RTL/周期模型及对照；资源/频率/面积/功耗 | 新architecture/PPA结论 | 用Python图数模型或CPU enqueue时间冒充RTL结果 |

先完成L0/L1已经足够形成有硬件意识的运行时研究。L2只做一次有明确边界的可行性检查；不可用就保留UNKNOWN，不把两周投入到某个driver符号。

## 3. 预定指标

- `occupied_rows_per_graph = target_continuation_rows / target_continuation_graphs`。
- `graphs_per_visible_postfirst_token = continuation_graphs / (output_length-1)`。
- `rows_per_visible_postfirst_token`：包括pending seed、proposal、可能回滚的行，不当成纯无效FLOPs。
- draft proposal/catchup rows、rollback次数、实际每轮committed token数及接受分母。
- phase切换/graph rebuild/cache reuse次数、必要的同步调用；计数不是已完成耗时。
- 可选dispatch计数必须从真实backend收集，不能用graph数乘一个估计kernel数代替。

主结论看qualified request cost。即使实际width2出现且graphs/output变少，也可能被draft、memory访问、launch或state formation成本吃掉。这种负结果仍可回答“物理批处理杠杆是否足够”，不能硬归因给其中一项。

## 4. 有限硬件计量，不开另一个大项目

P1 diagnostic可在少数固定位置保存graph和dispatch汇总，但禁止全量Vulkan API文本dump。历史API-dump已出现scope/输出体积失败，不重新踩相同路径。

P3最多24个standalone operator starts：从P1预定两个sentinel的首次可用q2 MQ快照提取同输入Q/K/V/mask，q1只取合法的首query子视图。2contexts×q1/2×MQ/PQ/QB×2repeats。原MQ q2 replay必须对自身captured output；q1是派生单query负对照，不冒称原native q1捕获。snapshot不存在则NOT_OBSERVED，不换输入直到找到想要的数值。

若已有backend能取得时间查询：检查queue的timestampValidBits、timestampPeriod、query availability、wrap-around、写入stage、buffer lifetime，异步回读在诊断结束后完成。不得把CPU vkCmdDispatch调用间隔当GPU执行时间；不得将重叠stage wall相加为独占分解。该观测本身的输出一致性另验，正式counts不启用queries。

P3从输入至输出不改算术kernel，仅变图表示。若无法获得合格时间，保留counts/形状，最多24starts上限不变，取消不可实现的时间字段。真实DRAM/缓存/XMX数据不可用时不画实测Roofline、不拟合假memory-bandwidth系数。

## 5. 与另一个硬件研究对话的接口

仅输出一个只读、来源固定的 `GEOMETRY_WORK_SUMMARY.json/csv`：q、key extent、dtype、GQA、layout、每请求/事务rows/graphs/dispatch、状态大小、qualification、真实时间以及UNKNOWN项。

该摘要可帮助另一个研究探索“reference-compatible formation”和“numerical grouping”是否应成为调度/图指令的显式属性，但这是后续假设。本PR不创设指令、不承诺面积功耗节省、不阻塞它、不修改其设计。

## 6. 广度退出标准

若只能解释/修好某四题或某一token，不把它包装成体系架构创新。若相同机制在未见代码/数学请求和多个prefill比例上成立，并能测到工作组织与实际收益的联系，才把它作为可迁移协同设计证据。仍如实注明单模型、k1/q≤2、固定precision/backend/ctx，不宣称全部LLM服务。

## 主源依据（检索于2026-10-15）

- Khronos Vulkan Queries：https://docs.vulkan.org/spec/latest/chapters/queries.html 。异步query、timestampValidBits、可用性与stage语义；本PR只读相关规范，不声称本机已实现查询。
- CoRun：https://arxiv.org/abs/2608.14376 。phase-specific形状控制已有近邻，不能列为独有大概念。
- LLM-42：https://arxiv.org/abs/2601.17768 。verify/rollback确定性路线，不与本文不同硬件速度直接排名。
- PR97 B570 physical-work报告：固定commit/source见SOURCE_LOCK。它是本项目原始实验，不是跨硬件普遍规律。

## 7. 对接“参考算术图保持的弹性验证单元”

三种宽度不能混为一谈：逻辑验证caller宽度；GPU实际micrograph/执行资源分配宽度；每个输出的算术依赖/舍入组织。QB现有证据在有限上下文说明数值对应，不能据此声明某种Tensor Core/XMX内部顺序已被识别。

后续硬件模型的可变因素可以是query发射次序、计算单元分配、KV tile预取与共享、backpressure；但固定的算术DAG边、舍入节点、mask、softmax和状态输入必须明确。串行依赖链不能靠调度被删除。该功能模型由另一工作流负责，本任务不预先声称真实B570的DAG就是某个理想FP模型。

### 对接数据对象

- 原始部署参考ID、model/runtime/source pins、输入和状态来源ID；
- 实际logical q、micrograph width、key extent、GQA/head维度、stride/mask与有效行；
- native事务的pending、accepted/correction/bonus/rollback和真实提交计数；
- 有对应证据时才附完整Q/K/V/mask payload及输出；数据未获得则缺失，不生成替代随机数据冒充；
- 计时通道、完成范围、观察污染边界；数据流量/利用率未知保持null。

初始接口`architecture_record`输出request-level原生工作摘要；逐算子tensor补充接口需要在P0/P3实际接入后另绑定，不声称已包含当前数据。

### 强基线与消融

本轮真实平台用MQ/PQ/QB、相同producer与相同reference；硬件线至少要加同MAC资源/同SRAM容量端口/同带宽下允许合理KV共享的固定调度基线。不能将“每个query都从外存再读完整KV”的弱基线当唯一比较。可以拆开独立query上下文、共享供给、保持DAG的弹性调度，以找到收益来自何处。

`reuse_opportunity`故意同时输出强shared baseline：若两者都能只取一次tile，就不会用q倍重复读的弱基线宣称q倍硬件收益。它不包含bank conflicts/广播/读端口/上下文缓存/外存实际事务，因此只作假设下界。

### 不能从本研究直接推出的结论

- 新架构提高模型准确率或草稿固有接受概率；
- PQ/QB费用差等于Tensor Core/XMX利用率差；
- 一个logical micrograph就是一个shader kernel；
- XMX或DRAM瓶颈占总请求的某个比例；
- 固定trace下快了等于数值改变后端到端也快了；
- 只综合控制器就得到了整加速器面积/功耗。

### 已核查的近邻与来源深度

- SPECTRA，arXiv:2609.24847：本轮核实主源摘要，runtime-reconfigurable tiled speculative pipeline与GEMV/GEMM适配已有工作，不把phase-aware tiles作为独创。
- SpecPIM，DOI:10.1145/3620666.3651352：本轮核实ACM条目/摘要，架构—数据流协同已有近邻，未做全篇或数值复现。
- Hawkeye，arXiv:2603.20421：本轮核实主源摘要；其CPU数值复现需要针对设备识别，不能直接当B570或RTX5070Ti的精确模型。
- NVIDIA PTX当前规范，https://docs.nvidia.com/cuda/parallel-thread-execution/index.html ：特定mma/wmma类型的累加/舍入细节可能未规定；dtype标签不足以定义参考算术。此规范不是Intel XMX规格。
- Khronos Vulkan Queries，同上：queries异步与结果availability，必须验证本机路径；不从接口存在推定已经取得合格测量。

这些是主源边界定位，不是完整related-work优先权证明，也不支持不同论文硬件speedup直接排名。
