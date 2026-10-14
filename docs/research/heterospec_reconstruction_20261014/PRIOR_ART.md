# 最近研究与创新边界

**截至2026-10-14的定向主源审查，不是穷尽检索或正式系统综述。** 比较的是方法、参考契约和证据职责；下表不做跨论文速度排名。全文阅读范围是相关方法/讨论段落，不把检索摘要当成完整实验复核。

## 1. 最需要改变定位的近邻

| ID / 主源 | 已覆盖的内容 | 对本次重构的约束与可保留差异 |
|---|---|---|
| P01 [CoRun: Padding is Simple and Efficient for Deterministic LLM Inference](https://arxiv.org/html/2608.14376v1), v1,2026-08-14 | isolated prefill、fixed-shape batched decode、位置不变性、采样状态、CUDA Graph；分阶段控制形状 | 不能以phase-specific shapes/保留既有kernel为独创。QB的区别须落在序列内部query/mask表示与既有量化参考，不是请求批次padding。未实测共同契约外部优势。 |
| P02 [LLM-42](https://arxiv.org/html/2601.17768v2), v2 | 固定形状verification、rollback和KV维护，复用现有kernel | QB没有额外数值恢复verifier，但正常speculative verification仍执行；没有直接比较不得说更快。 |
| P03 [Vosti](https://arxiv.org/html/2609.38981v1), v1 | 规定部署内kernel、engine与cache的联合确定性约束和形式化验证 | 不能将一般state invariant/归纳说明当新理论。本研究是已有部署参考的局部改写；其保证弱于正式验证，目标也不完全相同。 |
| P04 [MarginGate](https://arxiv.org/html/2605.30218v1), v1 | 决策margin触发的稀疏数值verification与状态维护 | m与误差的充分条件不是新算法。本研究完整向量诊断有参考成本，不能声称免费在线margin controller。 |
| P05 [Stage-Replay Divergence Follows the KV Cache](https://arxiv.org/html/2607.28495v1), v1 | 固定前缀、精度控制、双向整个KV移植与后缀效应 | 整份KV携带分歧已非新发现。增量是固定量化分段、有限子集、同前缀连续分数和组合性反例。 |
| P06 [Same Request, Different Answer](https://arxiv.org/abs/2609.04748), v2更新2026-10-12 | 摘要报告量化与cache历史下的分歧、恢复状态/反量化控制 | 基线bib使用v1；需关注v2变化。仅核实摘要/版本，v2 HTML获取失败，不能宣称逐节复核或全部差异已确认。 |

P01 是本轮新找到的强竞争邻项，不应把它隐藏在长相关工作末尾。P06的版本推进意味着旧引用列表不是持续有效的“最近研究已齐全”证明。原有LLM-42、Vosti、Stage-Replay、MarginGate不是此次才加入基线。

## 2. 机制解释的方法边界

| ID / 主源 | 可用的定位与限制 |
|---|---|
| P07 [The Curse of Multiple Mediators: Hidden Interaction Effects in Activation Patching](https://arxiv.org/html/2606.27510v1) | 多组件干预的交互和归因问题已有研究；有限四格净残差不等于自然间接效应或唯一中介。 |
| P08 [Towards Best Practices of Activation Patching in Language Models: Metrics and Methods](https://arxiv.org/html/2309.16042v2) | 指标和干预选择会改变定位解释；保存完整logits、真实argmax、同前缀与规则比只统计端点标签更有信息。 |
| P09 [Addressing divergent representations from causal interventions on neural networks](https://arxiv.org/html/2511.04638v5) | 内部干预的表示偏离问题；own-path与字节sham可验证重建正确，却不证明混合状态自然可达。 |
| P17 [Correctness Forensics for Batch Speculative Decoding: Diagnosing the Ragged Tensor Problem](https://arxiv.org/html/2510.22876v4) | ragged多序列位置/mask/KV不同步属于逻辑语义故障；要与语义索引正确时的有限精度几何问题分开。 |

POSITION规范化来自本项目实际互补状态/向量字节关系的审查。不要因两个方向都运行过就当成两个独立机制，也不要将该恒等式冒称新通用因果理论。

## 3. 数值与性能基础研究

| ID / 主源 | 与本研究的关系 |
|---|---|
| P10 [Defeating Nondeterminism in LLM Inference](https://thinkingmachines.ai/blog/defeating-nondeterminism-in-llm-inference/) | kernel层面的batch invariance已有工程方案；本研究不是首次发现浮点规约依赖形状。工程文章不等于同行评审对本文的验证。 |
| P11 [Understanding and Mitigating Numerical Sources of Nondeterminism in LLM Inference / LayerCast](https://arxiv.org/abs/2506.09501) | 保持低精度存储而提高算术精度的路线；不能把改精度后的输出直接当同一固定量化参考。这里只做abstract级定位。 |
| P12 [Deterministic Inference across Tensor Parallel Sizes That Eliminates Training-Inference Mismatch / TBIK](https://arxiv.org/abs/2511.17826) | 跨TP配置的归约设计；不是本文单GPU局部layout方案，不能把当前结果外推到TP。这里只做abstract级定位。 |
| P13 [Speculative Decoding: Performance or Illusion?](https://proceedings.mlsys.org/paper_files/paper/2026/hash/554e056fe2b6d9fd27ffcd3367ae1267-Abstract-Conference.html) | 现实运行栈、验证成本和benchmark选择的影响已有工作。本轮只核实官方摘要页；不能把一般“acceptance不等于speedup”当独有贡献。 |
| P14 [Lossless but Not Free](https://arxiv.org/html/2607.17283v1) | 消费硬件的实际验证执行与成本；逻辑并行不自动等于物理摊销。本文应强调同参考的修复组织对照，而非一般硬件成本警告。 |
| P15 [Fast Inference from Transformers via Speculative Decoding](https://proceedings.mlr.press/v202/leviathan23a.html) | speculative decoding基础；算法分布保持与某一部署recipe逐token保持是不同要求，不声称推翻原算法。 |
| P16 [Accelerating Large Language Model Decoding with Speculative Sampling](https://arxiv.org/abs/2302.01318) | 原文已有hardware numerics限定；新增数值边界应放在实现保证层，不包装成推翻理论。 |

## 4. 竞争结论

本次检索没有建立“无人在此前做过query-axis lifting”的穷尽性结论。最稳健的创新主张是**具体的完整实现对象、与最近本栈PQ比较的收益证据，以及状态组合性约束下的适用域分析**。若要宣称对已有确定性系统的实质性能超越，必须另做同参考适配与公平测量；目前没有这项结果。

不建议把CoRun、Vosti的强保证或吞吐数字与本研究的有限latency比值直接放在胜负榜。更适合一张能力矩阵：reference目标、改变哪个层级、是否额外verification、状态形成控制、已验证范围、计时契约。
