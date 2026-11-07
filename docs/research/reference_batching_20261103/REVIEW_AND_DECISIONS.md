# HeteroSpec：本轮判断与项目推进

2026-11-03。基于论文 PR154，以及 CUDA PR162、Vulkan PR163、Qwen 修复 PR159 和 producer–consumer PR152 的固定提交。

## 结论

这轮实验足以把物理前缀与算术路径修复放进论文核心。它们已经构成可解释、可干预、可移植的系统方法原型；当前证据还没有建立“由同一结构规则自动处理不同模型家族”的强普适性。下一步应完成这项正面能力。继续增加日志、重复通过的输入或者计时次数，不会替代它。

论文目标确定为：**在保持一个既定量化部署数值参考的条件下，从真实图、算子和缓存结构推导可以保留的 query 并行，并用已有批量执行路径实现它。** prompt 与 speculative verification 提供已知 query；普通 autoregressive continuation 仍逐 token 执行。

这一目标对已有参考有兼容要求的部署有价值。不能把任何数值差异都描述成模型正确性错误，也不能把“选择了更容易保持的参考”计作优化成功。论文需要同时交付方法、适用条件与实际代价；普适性来自规则的结构预测能力。

## 对所给审稿结论的取舍

| 判断 | 本轮处理 |
|---|---|
| 两平台完成定位、干预、修复、未见确认 | 同意，保留为核心证据。Vulkan 的独立精度因素与实际 dispatch 差别也保留。 |
| 同一个物理前缀分组原则跨后端落地 | 同意。两份 native 实现具有相同规则；当前新共享实现的 GPU 资格另行建立。 |
| 应做共享 runtime 和主动 Qwen 迁移 | 同意，并已交付共享前缀代码、接入候选与平台执行任务。 |
| 最少连续分组公式提升方法表达 | 保留为短结构性质。它是相邻等值段的基本下界，不承担主要理论创新。 |
| target-only 与 speculative 是两个应用出口 | 同意，但 M/R 的完整路径收益包含 prefill；不能解释为未知 AR token 被并行生成。 |
| 原 Qwen 回归支持跨家族迁移 | 需要分开：Vulkan 两新开关未启用；CUDA combined build 加载了前缀代码，但记录未证明实际 Qwen 边界拆分。 |
| 现阶段足以声称强普适的方法 | 尚不成立。共享 API、关闭开关的成功或未触发规则的回归都不能填补这个缺口。 |

这些区别改变研究任务和论文贡献表述，不需要在每个段落重复加入防御性限定。

## 真实的新颖性空间

“浮点数受 batch shape 影响”“固定归约可保持稳定”“状态与 kernel 契约共同决定确定性”已有充分先行工作。Thinking Machines 的讨论已经涵盖 attention 的 query length、KV 划分与固定 split-size；LLM-42 使用一致 verifier 并修复 KV；CoRun 采用固定形状执行；Vosti 定义状态与算子条件。不能把这些一般原则重新包装成首次发现。

本项目更有辨识度的问题是：**参考在优化之前已经确定，如何在不重写全部 kernel、不全面串行化、也不依赖额外在线 verifier 的条件下，利用现有批量算子保持它？**

已有结果提供了三个具体结构因素：

1. attention 的物理 KV 前缀影响 backend 求值组织，逻辑 mask 不足以恢复标量路径；
2. 相同 Q8 权重对应的标量与多行激活算术可以不同；
3. head normalization 的 row-dependent offload 偏好可以改变后续 RoPE 的执行位置。

物理前缀分组加上局部算术路径选择，是这个问题的一种有实现和因果证据的解法。它的最终学术含量取决于能否将因素变成可预测、可调用的结构规则，以及这些规则允许保留多少有效并行。共享代码是必要产物，但代码去重本身不构成新颖性。

Vosti 官方 kernel-contract 文档明确区分其 determinism 保证与对一个既有 reference implementation 的数值等价；这支持上述问题定位。它并不自动证明本实现已经给出一般等价保证。

## 实验结果的正确用法

本轮从每平台 144 个保存块、每块 6 个 service time 重建了全部 1,728 个正式耗时。聚合、A/A 门槛、反向块数与报告一致。该工作没有重新处理原机全部 raw 向量，也没有运行新 GPU 请求。

| 完整请求比值 | CUDA | Vulkan | 回答的问题 |
|---|---:|---:|---|
| speculative QB / 双 PQ 算术均值 | 0.975531 | 0.950549 | QB 局部表示增量 |
| target-only QB / target-only PQ | 1.004367 | 0.899300 | 普通生成路径中的布局增量，事后比较 |
| target-only QB / speculative QB | 0.973607 | 0.334255 | 同布局开启 draft 的价值，大于 1 才获益 |
| target-only QB / 原参考 R | 0.446871 | 0.544429 | 保持原参考的完整执行路径代价 |
| speculative QB / 原参考 R | 0.458985 | 1.628787 | 加上 draft 后的完整路径代价 |
| 原预设实用布局筛选 | 未通过 | 通过 | 工程筛选，非显著性检验 |

新增的有效观察是 Vulkan target-only QB 相对同候选 PQ 的约 10.07% 完整请求减少。它来自同一保存面板的事后配对重建。M 的多行容量主要用于 prefill，continuation 仍是单行；现有 service timer 未隔离各 phase，不能进一步分配这个收益。

这也说明下一轮应保留三类比较：原 R 的完整路径兼容代价、同运行时 PQ/QB 的局部增量、同布局 M/C 的 draft 价值。只有 R 对照不能排除收益主要来自串行参考较慢；只有 PQ/QB 又无法回答保持既定参考的完整价值。

新 Llama 的 draft value 在两平台均小于 1，应按实测选择 target-only。Qwen14B 的既有 repair study 同布局 draft value 为 1.4256，保留了正面的 speculative 应用。不同模型和 placement 的差异本来就是系统决策的一部分。

## 本轮已交付

### 论文

新稿：**HeteroSpec: Reference-Preserving Query Batching for Quantized Inference**，位于 [paper/reference_batching_20261103](../../../paper/reference_batching_20261103/README.md)。

新稿将“问题 → 机制 → 分组与 lowering → 数值路径 → 因果与迁移证据 → 完整成本”作为主线。它保留旧稿的有效 scope、Qwen placement 和 producer-state 结果，压缩项目历史与审计叙述。旧 32 页版本完整保留；新稿当前 10 页，含参考文献与附录。未来任务进入本文件和实验计划，结果章节只陈述已完成证据。

### 共享实现候选

[src/reference_batching](../../../src/reference_batching/README.md) 包含 C++17 前缀提取、最大相邻相容分组、策略身份和两平台原生源码接入脚本。脚本把原实现中的重复前缀逻辑换成共享调用，并让 graph reuse 显式区分相关策略。源树适配写入独立候选，保留原生支持范围。

已完成独立标量分配对照、穷举小规模分组对照、策略身份检查及源码接入检查。它们支持代码行为，不属于新 GPU 结果，也不能计为模型普适性。

当前原生调用仍只提供前缀需求。自动算术／dispatch 需求提取尚未接通；Vulkan 的 head/shape 约束仍在，CUDA 的 Q/K 归一化角色识别仍需从实际图结构抽取。这是明确的待实现部分。

新的图策略身份检查处理未来同 context 切换策略的情况。本轮没有复现旧实验使用错误图缓存的故障，不把这项改进反写成旧结果问题。

### 原机执行任务

[PLAN.md](../../../benchmarks/reference_batching_transfer_20261103/PLAN.md) 及两份平台 prompt 定义了可执行的下一步：

- [RTX_PROMPT.md](../../../benchmarks/reference_batching_transfer_20261103/RTX_PROMPT.md)：接入真实结构提取，预测并观察 Qwen8B/14B 的前缀边界和 normalization placement。保留原 Qwen14B 反例和原参考。
- [B570_PROMPT.md](../../../benchmarks/reference_batching_transfer_20261103/B570_PROMPT.md)：让新策略真正处理原 Qwen P1+PQ/QB 失败单元，并检查 producer 条件。已有 P4T 成功单元不能替代 P1 修复。Qwen 保留其原 all-GPU placement 和 k1 合同。

先完成结构预测与保留反例，再冻结实现；默认每平台 8 个自然未见输入，3 sessions × 8 inputs × 5 arms，共 120 个正式测量。RTX 两个 Qwen 配置各 4 个并分别汇总。这个面板验证主动迁移和描述代价，不用于估计广泛部署的失败概率，也不计时到某个有利门槛。

Llama 只保留原边界反例和一个普通控制。若共享变更没有扩展其数值执行范围，无需重跑旧 24 输入和 864 测量。需要解释 prefill/decode 占比时，另取小型诊断子集；不把探针放入正式计时路径。

## 完成标准与停止规则

这项研究推进的完成标准是：同一共享调用实际进入 native 路径；结构规则在输出之前给出预期行动；Qwen 原失败路径按规则修复；冻结后的小面板保持原参考；一次完整成本对照说明保留并行的实际价值。

如果 Qwen 暴露一个新的真实结构因素，可以用同状态或真实操作数干预识别并实现它。单纯增加一个开关或模型特判不会增加普适性。若新增条件没有共同结构解释，就应据实将方法定位为范围较窄的系统原型，而不是用更多通过样例扩大表述。

这些问题回答后停止可选补测。第三平台、任意新增模型、MoE／Strata、为了过门槛重跑计时均不属于本轮目标。RTX 远端交付回执可单独收尾，不阻塞方法工作；冻结材料和原参考保持原状。新稿作为 draft PR 提供作者审核，不自动合并或对外投稿。

## 来源

- [PR154 / 07bee1c5：当前论文](https://github.com/leecdiang/HeteroSpec/pull/154)
- [PR162 / e11d2b75：CUDA Llama](https://github.com/leecdiang/HeteroSpec/blob/e11d2b75d82422409ba2b701aa38c59f36acc50b/benchmarks/rtx_llama_repair_v1/host_execution/RESULTS.md)
- [PR163 / 10a70566：Vulkan Llama](https://github.com/leecdiang/HeteroSpec/blob/10a70566ce01ab707dbdcc57d8270c1434088f07/benchmarks/b570_llama_companion_v1/host_execution/RESULTS.md)
- [PR159：CUDA Qwen14B](https://github.com/leecdiang/HeteroSpec/pull/159)
- [PR152：Qwen producer–consumer](https://github.com/leecdiang/HeteroSpec/blob/022babfabb3d1b6f4f2a2830dca04b2654d193f9/benchmarks/b570_producer_consumer_boundary_v1/RESULT.md)
- [Thinking Machines：Defeating Nondeterminism in LLM Inference](https://thinkingmachines.ai/blog/defeating-nondeterminism-in-llm-inference/)
- [LLM-42 原论文](https://arxiv.org/html/2601.17768v2)
- [CoRun 原论文摘要](https://arxiv.org/abs/2608.14376)
- [Vosti 官方 kernel contracts](https://github.com/QDelta/Vosti/blob/main/docs/kernel-contracts.md)
- [LayerCast / NeurIPS 2025](https://proceedings.neurips.cc/paper_files/paper/2025/hash/f80094a824ba5912d4a2de169c404a40-Abstract-Conference.html)

完整逐项来源在 [EXPERIMENT_AUDIT.md](EXPERIMENT_AUDIT.md) 和新稿的 SOURCE_MANIFEST.json。开发性审阅使用 peer-review、scientific-critical-thinking 与 anti-defensive-writing-en 技能；技能辅助组织判断，不能替代源代码、原机结果和作者判断。相关 Scientific Agent Skills 引用已列入稿件的辅助工作声明。
