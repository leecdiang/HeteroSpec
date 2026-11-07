# HeteroSpec：基于 arXiv v3 的论文更新设计

日期：2026-10-20。状态：论文设计与证据整合方案；尚未更新 LaTeX、生成新稿或提交 arXiv。本文件不修改 `paper/`。公开基线是 [arXiv 2610.03228v3](https://arxiv.org/html/2610.03228v3)，旧 PR #102 的候选源码不能代替这一基线。

## 1. 主线与标题

**保留标题：Phase-Scoped Query Layouts for Reference-Preserving Speculative Decoding。**

论文仍以具体 QB 方法为中心：通过 query/mask views、共享 K/V、phase binding 和 graph-cache consistency，在限定运行域内保持指定参考，同时保留 attention 之外的批处理。更新后的问题是：这一局部方法的收益已经得到验证后，它在其他后端和执行模式中何时可用，完整表示成本是否保留收益，哪些机会实际出现在模型请求中？

“后端支持、局部参考对应、状态/请求对应、完整成本收益”用于组织经验资格与结果边界，不是一个新增算法，也不是适用于所有输入的证明。写作顺序应为**方法—可靠请求收益—状态与后端迁移—映射成本—体系结构启示**。[公开 v3 §§2–8](https://arxiv.org/html/2610.03228v3)

## 2. 相对 v3 的真实增量

v3 已包含六个 session 的 PQ/QB 请求比较、72-context CUDA replay、状态组成反例、冻结 Vulkan 支持谓词的限制，以及 software-first 的体系结构讨论；也已比较 CoRun、LLM-42、Vosti、SPECTRA。上述内容继续作为论文基础，不再写成新发现。三家族 3.06%、6.17%、2.83% 的 speculative request latency reduction 属于既有 E2 结果。[v3 §§5–8](https://arxiv.org/html/2610.03228v3)、[E2/E1 固定结果](https://github.com/leecdiang/HeteroSpec/blob/f997262d6b0accb126a1217c9356745cc8bbf708/benchmarks/rtx_qb_confirmation_v1/final_20261015/RESULT.md)

新增内容应集中为三点：

1. **强软件执行模式改变表面优化空间。** 实际 CUDA Graph capture/replay 后，选定几何的 QB ON/OFF 完成图成本比为 0.615–0.849；原有部分 QH−QB 差距明显缩小。固定逻辑长度的 padding 干预进一步表明，到达便宜路径不等于保持指定参考：L1023→S1024 不通过原参考资格，合格的 L1023→S1025 仍为八个 kernel，约贵 1.5%。[RTX 执行模式结果](https://github.com/leecdiang/HeteroSpec/blob/a1f15bfc8222054aa7b94b40f41af0dd0492ddab/benchmarks/rtx_mechanism_baselines_v1/RESULT.md)、[padding 干预结果](https://github.com/leecdiang/HeteroSpec/blob/f38ed240d904db09e121bf50158cd207e829a12f/benchmarks/rtx_dispatch_intervention_v1/RESULT.md)
2. **后端拒绝可以在明确域内由软件解除，解除后仍需证明收益。** B570 准入补丁在已测 Hq=Hkv=8、F16 K/V、F32 Q、q=1/2/4、key=1023/1024/1025 范围运行成功。完整 Q 表示事务中，QH_C−dual-QB 为 −1.518 μs，调整区间 [−4.168,+0.916] μs，未建立实用优势。旧后端拒绝与新后端限定域成功应并列保留。[准入与数值范围](https://github.com/leecdiang/HeteroSpec/blob/cf6c8bf43dc1ee4e9e8529bbe42300844e0165c9/benchmarks/b570_qb_batch_broadcast_v1/RESULT.md)、[完整事务结果](https://github.com/leecdiang/HeteroSpec/blob/cf6c8bf43dc1ee4e9e8529bbe42300844e0165c9/benchmarks/b570_qb_batch_broadcast_v1/transaction_v1/RESULT.md)
3. **真实请求检查限定微图结论的用途。** 一条暴露的 Qwen3 请求实际为 q1、physical key256、Hq/Hkv=32/8，没有执行等头数 near1024 微图的多查询机会。修正 terminal interval 与 inactive labels 后，设备计时仍有约 7% median observer overhead，得到的是诊断 subtotal。[真实请求与 observer 结果](https://github.com/leecdiang/HeteroSpec/blob/c541241ad62213a8d31006e539e4ce0623793040/benchmarks/b570_model_request_bridge_v1/RESULT.md)

这些结果使原有方法具备更完整的实施与成本边界；没有增加已验证的新加速器、选择器或 B570 端到端加速方法。章节应继承 [PR124 CHAPTER_DRAFT](https://github.com/leecdiang/HeteroSpec/blob/ca3b8b0dba84b6668a1713f23cfbf95aa99dd50e/docs/research/rtx_evidence_synthesis_20261018/CHAPTER_DRAFT.md) 和 [EVIDENCE_MATRIX](https://github.com/leecdiang/HeteroSpec/blob/ca3b8b0dba84b6668a1713f23cfbf95aa99dd50e/docs/research/rtx_evidence_synthesis_20261018/EVIDENCE_MATRIX.md)，再纳入 B570 的独立证据。

## 3. 建议的三项贡献

1. **具体实现贡献：** 给出 phase-scoped QB 的 query/mask 地址变换、K/V 共享、GQA 与输出顺序要求，以及跨 phase 和图复用的实现约束。贡献主体沿用 v3，不以“四项条件”替代方法细节。
2. **请求与数值证据：** 在固定量化运行时和三家族面板上，联合报告完整端点、72-context 局部数值对应、PQ/QB 独立实现成本、局部/全局修复与 draft 净收益；区分重复输入、暴露诊断与新输入验证。
3. **新增成本与迁移刻画：** 用 CUDA 与 Vulkan 的独立研究，展示参考资格、软件执行模式、表示准备和真实请求范围如何约束映射选择。新增贡献是受控干预及其测量结果，不是测量规范、padding、CUDA Graph 或状态组合概念本身。

前两项对应 [v3 方法及评估](https://arxiv.org/html/2610.03228v3)；第三项以本文件第 2 节的固定结果及 [B570 论文补充](https://github.com/leecdiang/HeteroSpec/blob/c541241ad62213a8d31006e539e4ce0623793040/benchmarks/b570_model_request_bridge_v1/PAPER_ADDENDUM.md) 为证据。

可沿用 PR124 的经验可用集合表达：固定参考 R、输入面板 X 和环境 e，仅在每个必需输入都通过输出与执行控制时，将映射 m 纳入 A_R(X,e)。成本写作 T_W(m,x,e)，窗口 W 必须显式给出。这是被测集合上的定义，不推导所有输入等价性。尤其不能由“局部完整 ordinary 相等”直接推出“带状态更新的完整请求相等”；新增 B570 结果应同时注明 FP64 容差检查、跨 arm 字节对应和最终参考连续性各自回答的问题。

跨设备也只比较研究结论，不比较未经配平的绝对性能。RTX 与 B570 的 head ratio、key extent、实际执行模式、输入来源和时间窗不同；两平台都未建立 QH 的实用优势，可以作为两个限定案例，不能合成为通用最优性结论。统计未决、未执行和已观察的数值失败分开展示，不把前两者画成“与基线相同”。上述口径与 [PR124 资格定义](https://github.com/leecdiang/HeteroSpec/blob/ca3b8b0dba84b6668a1713f23cfbf95aa99dd50e/docs/research/rtx_evidence_synthesis_20261018/CHAPTER_DRAFT.md)、[B570 事务限制](https://github.com/leecdiang/HeteroSpec/blob/cf6c8bf43dc1ee4e9e8529bbe42300844e0165c9/benchmarks/b570_qb_batch_broadcast_v1/transaction_v1/RESULT.md) 保持一致。

## 4. 完整章节安排

| 章节 | 论证任务与修改重点 |
|---|---|
| 1 Introduction | 从量化 speculative verification 改变执行几何切入；QB 为具体解法，新增结果解释部署边界；贡献保持三项。 |
| 2 Reference Contract and Execution Model | 保留端点、状态事务和经验资格定义；分开局部 ordinary 字节与请求端点，不把算子通过写成模型通过。 |
| 3 Phase-Scoped Query Layouts | 保留视图公式、mask、GQA、输出恢复、phase guard 和 cache key；维持方法篇幅。 |
| 4 Experimental Design | 增加后续研究范围表；每项绑定参考、输入、设备/运行时、比较基线、成本窗口和统计单位。 |
| 5 Numerical Correspondence and Request Cost | 保留 E1/E2 与 draft economics，明确所有请求收益属于原面板，后续微图没有追加模型加速数字。 |
| 6 State Formation and Backend Transfer | 保留最有解释力的状态反例；补“旧 Vulkan 拒绝→新运行时有限准入”，不覆盖历史失败。 |
| 7 Reference-Constrained Mapping Costs | 主新增章：强 QB 基线、A/A、真实 replay、固定逻辑长度干预、完整 Q 事务；按研究问题写，不按 PR 编号写。 |
| 8 Real-Request Scope and Architectural Implications | 接入 B570 q1/GQA 范围检查；将观测完整性作为结果解释条件；给出硬件机会仍缺什么。 |
| 9 Related Work and Limitations | 沿用 v3 对照，补充新增实验的合同差异、不同成本窗口和本地 raw 限制。 |
| 10 Conclusion | QB 是已实证的方法；新证据界定可用优化空间；后续优先真实 q>1 请求桥接。 |

现有结构来自 [v3](https://arxiv.org/html/2610.03228v3)，新增章内部组织继承 [PR124 草稿](https://github.com/leecdiang/HeteroSpec/blob/ca3b8b0dba84b6668a1713f23cfbf95aa99dd50e/docs/research/rtx_evidence_synthesis_20261018/CHAPTER_DRAFT.md)。工程故障账本、CPU8 审查过程、预算、UUID、归档与完整坐标留在仓库或补充材料。正文保留与结论有关的失败，但压缩重复资格说明。

## 5. 英文候选摘要

> Speculative verification changes a target model's execution geometry and can alter a quantized deployment's generated tokens. We present phase-scoped query-to-batch (QB) views that preserve query and mask semantics, share K/V storage, and retain batched computation outside attention. In a six-session experiment across three model families, QB reduces speculative request latency relative to explicit per-query attention by 3.06%, 6.17%, and 2.83%, with complete reference-output agreement on the fixed panel. A separate 72-context CUDA replay finds bitwise PQ/QB correspondence at QK, softmax, and AV. We then examine the constraints on transferring and further optimizing this representation. State interventions expose limits to component substitution, while a scoped Vulkan admission repair enables the evaluated equal-head QB geometries. Controlled CUDA experiments show that verified graph replay changes mapping costs and that padding into a cheaper execution path can fail the original numerical reference. Balanced mapping comparisons and charged Q-representation transactions do not establish a practical QH advantage over QB in their tested domains. A real Qwen3 request check further identifies a q1, grouped-query geometry distinct from the multiquery micrographs; its corrected profiling results remain diagnostic subtotals. Together, these results establish a concrete local implementation benefit and characterize the state, backend, and cost boundaries that constrain reference-preserving deployment and architectural optimization.

摘要仅整合本文件第 2 节的已有结果。QH 未建立优势不表示统计等价；micrograph 成本、原 E2 request 收益和 B570 单请求 observer 控制保持三个独立证据域。

## 6. 图表：新增两张复合图、一张资格表

| 图表 | 面板设计 | 取数与必须保留的边界 |
|---|---|---|
| 新图 A：执行模式与参考可行性 | A1：选定坐标的 OFF/ON 下 QH−QB 绝对差；A2：固定 logical L 的 padding 资格、实测路径和合格路径成本。 | 使用 [replay 结果](https://github.com/leecdiang/HeteroSpec/blob/a1f15bfc8222054aa7b94b40f41af0dd0492ddab/benchmarks/rtx_mechanism_baselines_v1/RESULT.md) 与 [padding 结果](https://github.com/leecdiang/HeteroSpec/blob/f38ed240d904db09e121bf50158cd207e829a12f/benchmarks/rtx_dispatch_intervention_v1/RESULT.md)。不合格路径不给性能柱；kernel 数不能单独证明带宽或因果机制。 |
| 新图 B：完整表示成本与请求范围 | B1：RTX ON 完整 Q 事务相对双 QB 的配对比值；B2：B570 完整事务的调整区间；B3：micrograph 与真实 Qwen3 的 q/key/head 范围对照。 | 使用上述 RTX padding 结果、[B570 transaction](https://github.com/leecdiang/HeteroSpec/blob/cf6c8bf43dc1ee4e9e8529bbe42300844e0165c9/benchmarks/b570_qb_batch_broadcast_v1/transaction_v1/RESULT.md) 和 [request bridge](https://github.com/leecdiang/HeteroSpec/blob/c541241ad62213a8d31006e539e4ce0623793040/benchmarks/b570_model_request_bridge_v1/RESULT.md)。平台分别绘制；区间定义各自标注，不合并总体或比较绝对设备性能。 |
| 新表：资格与主张范围 | 行含 E2、E1、RTX 映射/干预、B570 准入/事务、真实请求检查；列含参考、输入几何、实际放置、输出层级、成本窗口、剩余未知。 | 以 [PR124 证据矩阵](https://github.com/leecdiang/HeteroSpec/blob/ca3b8b0dba84b6668a1713f23cfbf95aa99dd50e/docs/research/rtx_evidence_synthesis_20261018/EVIDENCE_MATRIX.md) 为底稿，加入 B570 新行。只合并展示格式，不池化样本。 |

原有方法图与请求收益图继续承担主叙事。B570 的 2.8005–2.8026% 只覆盖 QK/softmax/AV core；92.5152% quantized groups 同时含 attention projections 与 FFN。若使用这些数字，只能放在明确标注的 observer 补充图，不将其代入 Amdahl 请求上界。[范围定义](https://github.com/leecdiang/HeteroSpec/blob/c541241ad62213a8d31006e539e4ce0623793040/benchmarks/b570_model_request_bridge_v1/PAPER_ADDENDUM.md)

## 7. 相关工作与体系结构定位

现有比较继续保留：[batch-invariant kernels](https://thinkingmachines.ai/blog/defeating-nondeterminism-in-llm-inference/) 控制数值求值；[CoRun](https://arxiv.org/html/2608.14376v1) 使用独立 prefill 和固定形状 decode；[LLM-42](https://arxiv.org/html/2601.17768v2) 增加固定形状验证与 rollback；[Vosti](https://arxiv.org/abs/2609.38981) 讨论系统/内核形式化确定性；[SPECTRA](https://arxiv.org/abs/2609.24847) 研究 speculative execution 的可重构硬件。v3 已有这些来源和区别；本次不追加“首次/首创”断言。

QB 的定位是固定量化部署中的具体局部视图变换与同参考成本证据。未在共同模型、运行时和参考契约上比较这些外部系统，不能将其论文加速数字直接作为本项目 baseline。体系结构章提供实证设计约束；硬件性能仍需额外机制、强软件后残差、真实关键路径和物理资源校准。原 CPU AV 研究的五个标签共用 policy、周期比 1.000 是控制结果。[强基线 H0 审查](https://github.com/leecdiang/HeteroSpec/blob/dae5aea9f9009a686196dd89981c0ae9699ae612/benchmarks/rtx_reference_packing_v1/H0.md)

数据可用性一节应区分公开稿内的 reported data、源码与输入身份索引、可取得的紧凑实验元数据，以及仍保存在原机的完整 raw。后续 RTX 与 B570 研究的本地恢复复算、Git 紧凑文件远端核验，不能写成完整张量已被外部独立复现。图表应从固定生成表导出；整理排版不得增加新的置信区间、改变样本单位或删去逆向结果。未完成的自然请求、GQA 移植和物理机制仍列为未知，不能用重复进程数充当 workload 覆盖。[RTX 可复现性边界](https://github.com/leecdiang/HeteroSpec/blob/f38ed240d904db09e121bf50158cd207e829a12f/benchmarks/rtx_dispatch_intervention_v1/RESULT.md)、[B570 交付范围](https://github.com/leecdiang/HeteroSpec/blob/c541241ad62213a8d31006e539e4ce0623793040/benchmarks/b570_model_request_bridge_v1/RESULT.md)

## 8. v4 发布路线与最短增强实验

**现有证据即可开始写 v4**：以公开 v3 对应源码为基础，整合上述章节和固定结果，复核每个图表的分母、输出资格与成本窗口，完成排版、引用及全文交叉检查后再提交。无需等待已完成的 E2，也不以旧 PR #102 代替公开稿。

若希望进一步增强，优先补真实 q>1 的 speculative request 桥接：RTX 使用既有合格 native 路径，小面板观察 k=1/3 的实际 q，分开 prefill、draft、target verification、accept/reconcile 与 sampling/同步；clean 完整请求计时与稀疏诊断分开。B570 先核对真实 32/8 GQA 的支持和映射，再决定能否开展同类桥接。当前 q1/key256 请求不能认证这些新域。[B570 范围与后续边界](https://github.com/leecdiang/HeteroSpec/blob/c541241ad62213a8d31006e539e4ce0623793040/benchmarks/b570_model_request_bridge_v1/PAPER_ADDENDUM.md)

原历史 R 不得被新 clean q1 reference 替代。若新模型/后端需要新参考，应前瞻登记新的 R_e 与输入/输出窗口，只用于新面板；16-token 控制不能追认为历史完整端点资格。旧 CPU8 不是这条研究的自动先决条件，历史失败、UUID、预算和 F0 状态保持原身份。关闭既测 QH 微小优势和 padding 支线；只有真实请求中出现可定位的强软件残差，才进入新的物理瓶颈与硬件研究。[RTX 支线关闭](https://github.com/leecdiang/HeteroSpec/blob/f38ed240d904db09e121bf50158cd207e829a12f/benchmarks/rtx_dispatch_intervention_v1/RESULT.md)、[B570 支线及预算](https://github.com/leecdiang/HeteroSpec/blob/c541241ad62213a8d31006e539e4ce0623793040/benchmarks/b570_model_request_bridge_v1/RESULT.md)
