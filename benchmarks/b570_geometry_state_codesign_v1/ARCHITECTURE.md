# 硬件第一阶段审查：强软件基线之后，还剩什么值得硬件化？

审查基点：PR108 `584db4a5adb933383af7cbf037eb995336c4a47c`。本修订只调整硬件交接与CPU导出；不修改软件协议、原始数据、九臂、输入选择、计时、P1/P2准入或原机预算。

**当前是审查方案与数据接口，不是硬件可行性实证通过。** 目标不是提高模型准确率或草稿固有接受概率，而是识别：在同一参考契约下，是否存在强软件执行组织尚未消除、且具体硬件机制可能降低的成本。

## 1. 本PR能回答什么

自然producer形成状态，MQ/PQ/QB改变局部表示，外围projection/FFN是否保留多行执行，必须分别核验。`reference128`是分段方案名，不证明所有KV字节等于原R。自然完整请求、实际工作组织与完整请求费用，是三个不同证据对象。

P1/P2可以提供跨输入的工作量、资格与费用比较，但**不能仅由PQ/QB费用差推出Tensor Core/XMX瓶颈，也不能证明需要新硬件**。本研究运行在B570/Vulkan；它为后续RTX或抽象加速器提供工作负载与边界，不提供跨设备的算术、性能或利用率校准。

第一阶段不要求完整GPU仿真、RTL、FPGA或芯片PPA；也不要求为取得某个driver符号无限扩展诊断。记录UNKNOWN可以是有效结论，但UNKNOWN不是硬件GO。

## 2. 五个层次，不合并成一种“物理宽度”

| 层次 | 含义 | 不能替代的量 |
|---|---|---|
| 逻辑proposal/caller | pending、proposal与有效query；声明最大q不等于每次实际q | 成功执行的micrograph行数 |
| native micrograph | 实际occupied rows、图划分与复用 | shader dispatch、阵列并发或利用率 |
| backend dispatch | source-bound pipeline、workgroup和实际指令调度信息 | 仅凭dispatch数量仍不能推XMX占用或DRAM流量 |
| 计算资源映射 | tile/执行单元分配、端口竞争、带宽、发射与完成 | 每个输出的算术依赖关系 |
| 数值与状态契约 | operand、归约分组、舍入/转换、mask、softmax、KV生产和提交边界 | 完整端点相同不证明中间状态或上述算术图相同 |

请求级直方图不能重建逐事务时序，也不能独自证明某个width2图属于VERIFY。需要原协议的source-bound VERIFY witness；缺少时保持缺失，不能按直方图编造事件。

## 3. 先区分四种竞争解释

| 假设 | 最少需要的证据或条件分析 | 会使该解释降级的情形 |
|---|---|---|
| H-L：启动/图管理成本 | 已有构图/复用/同步计数；有资格时才用已完成计时 | 仅凭图数无法定量；现有图复用、融合或软件调度已足够，则优先软件 |
| H-M：重复数据供给 | 相同KV所有权/有效tile、dtype、shape/stride和重用范围；按内存层级列情景 | 强基线也能共享/驻留，或没有实际流量，不能宣称q倍DRAM收益 |
| H-A：保持参考算术限制并行度 | 明确参考DAG或明确命名的新算术契约；依赖与同资源映射比较 | DAG未知、已有固定分块/有序合并可实现，或收益来自悄悄改变归约 |
| H-S：状态生产/维护成本 | 相同producer的消费者对照；不同producer的自然完整输出；必要状态与提交工作 | 收益仅来自prefill、draft或状态重新计算，不能归给attention单元 |

先用现有归档、软件源码和已批准诊断做这张表，不增加新的native请求。H-L/M/A/S可以同时成立；未能分离时写成联合因素，不能拟合四个无依据的独占耗时系数。

## 4. 强基线与候选机制的最小范围

真实平台保持协议原有MQ/PQ/QB与同producer、同原R比较。后续硬件研究还需要同MAC数量、同频率假设、同SRAM容量/端口、同外部带宽的**合理共享固定调度基线**。不能只比较“每个query都从DRAM重读全部KV”。既有batch-invariant软件、固定形状/固定归约分块、图复用和可行融合，应作为竞争解释或可适配基线；不可适配者说明契约差异，不伪造native比较。

第一版最多研究一个小型执行单元：独立query累加上下文＋共享KV供给＋遵循参考依赖的发射/合并。拆开“仅共享”“仅弹性调度”“二者结合”，同时保留无额外硬件的强基线。为保持数值而新增的上下文、缓冲、广播、bank conflict、端口和回压成本必须计入。不能删除串行依赖；也不能把软件可实现的有序调度本身称为新ISA。

两类目标必须分别命名：

- **保留部署参考**：使用实际operand和已确认的实现语义；只在相应已验证域声称对应。B570证据不确定RTX内部算术。
- **新架构自定义参考**：可以先明确一个新的有限精度DAG，比较该架构上的单步与投机；这不是已恢复B570/RTX原部署输出。稳定、高精度或使用可复现累加器，也不自动满足旧参考。

第一阶段不得把q>2、第二模型、随机采样、多stream、多GPU或新precision继承为本PR的实证范围。CPU探索中的额外形状只能标为合成设计空间，不是新增native验证。

## 5. 现有预算内的观测边界

P1仍是80个model requests/processes，P2仍是1728 starts/864 processes（含864 warmups）；各自授权、owned时间和输出预算全部以PROTOCOL为准。本硬件修订不增加额外probe、warmup、重试或原机自动化，不要求先完成P3才能进入软件P2。

P1 diagnostic只使用已登记的有限捕获；不进行全量Vulkan API dump。可选P3仍最多24个独立operator starts，并另行批准：2个预定sentinel的首次可用q2 MQ快照 × q1/2 × MQ/PQ/QB × 2 repeats。q1是合法首query派生视图，不是伪称捕获的native q1；q2 MQ需对自身输出作sham。不存在快照则NOT_OBSERVED，不换题寻找有利结果。

如果现有路径支持GPU时间查询，核验timestampValidBits、timestampPeriod、availability、wrap-around、写入stage和buffer lifetime，异步回读，并验证观察影响。CPU enqueue或vkCmdDispatch间隔不是GPU执行时间；重叠区间不可相加为独占分解。正式counts不打开queries。不可取得合格计时就取消时间字段，保持原预算；不能用请求wall回归出假kernel时间、假DRAM带宽或实测Roofline。

模型加载不计入协议请求计时；这不等于已经证明整个请求持续物理驻留。导出保留原timer contract，但物理驻留资格单列UNKNOWN。

## 6. Schema 2：请求摘要不是模拟器trace

`architecture.py`现在要求源plan、外部提供的runtime manifest hash、原始文件root，并调用已有plan/record校验。它检查实际归一化request与冻结slot、完整endpoint、工作守恒、观察标志、timer、生命周期、raw路径/大小/hash。只有record自身两个格式正确的hash不再足以导出。

可选原R记录必须来自**同一plan、task与session的非warmup原R**，R_SHADOW不能代替。输出`MATCH / MISMATCH / NOT_CHECKED`；有效反例保留原始费用和工作，不删除、不视为合格加速。单个MATCH既不是全panel资格，也不是observer一致或状态相等的证明。完整费用资格继续由原分析与独立原始字段审计负责；本导出不汇总速度、不提前打开time gate。

格式明确区分：声明最大q、已观察micrograph直方图、未获得的实际caller/attention宽度、VERIFY事务witness、tensor/key extent/GQA/stride/mask、计算资源宽度和数值DAG。未获得的量保持null/UNKNOWN；prompt长度不充当算子key extent，F16 KV不充当所有operand/累加dtype。计时分为pilot描述、diagnostic、warmup排除和等待panel资格的confirm counts，删除易被误读为合格费用的旧`paid`标签。

**hash核验不是独立raw语义重建，更不是native来源认证。** 导出会明确保留`independent_raw_semantics_verified=false`与F0认证未由本工具执行；原机仍需独立解析REQUEST/RESULT/trace并绑定字段来源。临时合成文件即使hash正确、甚至被错误标成NATIVE，也不能因为此工具通过就升级成实验证据。

从本目录执行（新接口有意拒绝无plan/raw的旧调用）：

```bash
python architecture.py --record REQUEST_RECORD.json --plan PLAN.json \
  --runtime-hash FROZEN_RUNTIME_MANIFEST_SHA256 --raw-root RAW_ROOT \
  --reference-record MATCHING_ORIGINAL_R_RECORD.json --out GEOMETRY_WORK_SUMMARY.json
python -m unittest -v test_toolkit test_architecture
```

`--reference-record`可省略，但资格必须为NOT_CHECKED。失败/未完成/非法记录由原ledger保留，不由此导出伪装成完整观察。输入与输出均只读/新建，不覆盖历史文件。旧VALIDATION与CPU_TESTS日志仍描述初始版本，新增测试不把旧记录改写为当前测试。

### 后续逐事务/算子sidecar的最小信息（接口要求，尚未实现）

只有现有获批捕获真实提供时，才附：source文件hash及记录位置、request/transaction/phase/caller/micrograph/op身份、逻辑token位置与KV有效范围、state epoch与ownership、pending/proposed/accepted/correction/bonus/rollback/committed计数、Q/K/V/mask/output payload绑定及shape/stride/GQA/dtype、已完成事件与依赖。每项注明declared、observed、derived或unknown。

必须以实际cap/EOG/rollback规则检查守恒，不能把全部target rows当作有用token。只有counter histogram时，交付摘要和缺口，不重建一条想象的执行顺序。最终端点相同仍可能有不同接受/拒绝轨迹；数值或控制决策改变后需要功能模型生成新trace，不能冻结旧接受率/旧KV状态来预测新架构的端到端速度。

## 7. 条件成本分析，而不是硬件性能预测

`reuse_opportunity`是明确假设下的tile供给情景：独立读取、每组共享、强基线跨组共享。相同有效tile/KV所有权、组间能否保留和内存层级需先声明。`ceil(q/contexts)`不是无条件访存下界；强基线和候选都可读一次时没有由此得到的硬件收益。字段不代表实测DRAM事务。

`amdahl_sensitivity(f,s,h)`仅计算 `1 / (1-f+f/s+h)`。f是基线非重叠关键路径份额，s为该部分加速假设，h为新增串行成本占基线的比例；工作量/控制流不变。未知f不能用micrograph比例替代，也不从当前完整请求费用拟合。报告假设范围、来源和开销敏感性；没有可靠占比时只能给情景，不能给“预测RTX加速倍数”。若模型误差足以覆盖收益，则结论为证据不足。精确PPA不是这一阶段GO前提。

## 8. 第一阶段的完成物与三种出口

完成一份source-bound审查表即可，不强制新增大报告。它必须包含：参考目标及证据层级；上面四种解释；最佳同参考软件基线；候选模块改变什么、哪些依赖不能改变；一组含开销的条件上限/敏感性或明确缺口；适用范围与反例；一个可证伪的下一步CPU实验。

| 出口 | 依据 | 允许下一步 |
|---|---|---|
| GO_BOUNDED_CPU_MODEL | 有具体未消除的成本假说；已认真比较软件替代；明确数值契约；同资源对照和含开销情景值得证伪 | 仅一个小型功能/周期模型；不是硬件优越性通过，不自动准入GPU/RTL/P2 |
| SOFTWARE_FIRST | 有证据表明当前代价可由软件处理，或当前候选在同资源强基线下没有额外机制 | 保留软件贡献，不硬加“新硬件”章节；不声称所有未来硬件都无价值 |
| HOLD_MISSING_EVIDENCE | 尚无法区分剩余代价、参考语义、数据/关键路径或强基线 | 列最小缺口；不得默认pass，也不得擅自扩GPU预算 |

这里的三态是需要来源和理由的研究判断，**不是把几个手填布尔值变成科学准入的程序**。当前exporter固定输出`NOT_DECIDED_BY_EXPORTER`。P1/P2软件GO与硬件GO彼此独立；一次有效NO-GO或HOLD也能完成第一阶段审查。不能把“软件效果已经很好”本身推成任何硬件都不必要；必须针对所提模块说明剩余代价为何存在或不存在。

准入CPU模型前先冻结工作负载来源、对照、参数范围、数值判据、实际意义标准与模型误差处理；这些只约束后续硬件模型，不追溯改变本PR的native样本、顺序或费用判据。

## 9. 最需要对照的主源与阅读深度

本次硬件修订于2026-10-15重新读取以下主源；仅做相关机制审查，不声称穷尽优先权检索或复现实验：

- [Thinking Machines：Defeating Nondeterminism in LLM Inference](https://thinkingmachines.ai/blog/defeating-nondeterminism-in-llm-inference/)，阅读batch-invariant matmul/attention与fixed split-size段落。固定每输出归约、固定分块和并行度折衷已有直接先例；不能把“数值组织与资源调度分开”本身当独创。
- [ReproBLAS](https://bebop.cs.berkeley.edu/reproblas/)，阅读目标、累加器与tiling说明。调度无关的可复现归约已有基础；其参考数值语义不自动等于本项目量化部署参考。
- [NVIDIA PTX ISA](https://docs.nvidia.com/cuda/parallel-thread-execution/index.html)，阅读wmma/mma相关precision/rounding条款。若干浮点形式未规定完整累加顺序、舍入或subnormal处理；不可泛化为所有类型都未规定，更不可充当Intel XMX规格。
- [SPECTRA，arXiv:2609.24847v1](https://arxiv.org/abs/2609.24847v1)，核实主源摘要和ICCAD 2026接受说明，未复核全文/原型。GEMV/GEMM切换、tile和通信重配置已有近邻；只加phase-aware tiles不足以构成创新。

原版还列有[Khronos Queries](https://docs.vulkan.org/spec/latest/chapters/queries.html)、[CoRun](https://arxiv.org/abs/2608.14376)、[LLM-42](https://arxiv.org/abs/2601.17768)、[SpecPIM](https://doi.org/10.1145/3620666.3651352)、[Hawkeye](https://arxiv.org/abs/2603.20421)以及SOURCE_LOCK中的PR97。保留为继承的规范/近邻线索，不把本次未重新全文核查的条目升级成已完成全文审稿。不同参考、不同硬件的公开speedup不直接排名。

**最终定位：本PR可以供给硬件第一阶段的真实问题、数据和否证条件；只有明确的剩余代价、机制和公平对照，才值得进入架构实现。章节增加不是创新性证据。**
