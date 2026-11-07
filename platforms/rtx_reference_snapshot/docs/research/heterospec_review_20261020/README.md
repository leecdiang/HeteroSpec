# HeteroSpec：v3 之后的研究审阅与下一步决策

日期：2026-10-20（Asia/Shanghai）。本次按作者要求使用 GitHub 插件审阅仓库，完成最新 PR 合并，并提出论文与实验设计。这里的研究建议尚未执行；本目录不更改论文源码或实验准入状态。

## 1. 结论

**HeteroSpec 已有扎实的 QB 软件方法与有限域系统收益证据。10 月 18–20 日的新进展进一步说明：一个表示优化必须同时保持指定参考、得到后端实际支持，并在强软件基线及完整成本窗口中有收益。现有证据足以加强论文的体系结构分析章节，尚不足以支撑一个已实现的新加速器贡献。**

本轮最新结果支持保留 QB，结束已经测过的 compact-QH 优化支线。最值得补的证据是：**真实推测请求的 q>1 验证阶段是否出现所研究的几何与成本，且其残余开销是否影响请求关键路径。** B570 还必须先解决已测 equal-head 域与真实 GQA 域之间的差距。[RTX 综合][RTX] [B570 映射][B128] [真实请求][B129]

这是一项有明确方法主体的系统研究。创新性应继续落在 query/mask 变换、phase 与 graph-cache 约束、对应的收益和可迁移边界；“四项检查”“更严格的测量”及“更多 PR”本身不构成新的算法贡献。论文适合围绕同一主问题深化，避免被工程审查流程和分散的硬件构想取代。[公开 v3][V3]

## 2. 此次实际完成的合并

| PR | 审阅的科学提交 | main 合并提交 | 接纳的内容 |
|---|---|---|---|
| [#128](https://github.com/leecdiang/HeteroSpec/pull/128) | `cf6c8bf43dc1ee4e9e8529bbe42300844e0165c9` | `c9f018ff0ac5c8001deb36bcb062ff27408a673b` | B570 窄域准入补丁、均衡映射对照和完整 Q 表示事务归档 |
| [#129](https://github.com/leecdiang/HeteroSpec/pull/129) | `c541241ad62213a8d31006e539e4ce0623793040` | `ec6b97518a2f230330d79f1b0ba2ca97bc70cd6a` | 单个真实请求的几何核对、Vulkan logger 修复和计时归因归档 |

初始 main 为 `9b8cdba784b34a5aa3e8981073223c451bbaaf54`，其中 RTX #104、#110、#113、#114、#116、#118、#120–124 已在 10 月 18 日合并。#129 在 #128 合并后改为以 main 为基线；两次均使用审阅过的 expected head SHA 合并，保留完整历史。两个新 PR 只新增独立 benchmark 子树，活动后端修复以 patch/源码快照归档。[原 RTX 合并记录][RTXMERGE]

本次核对了全部 19 条开放 PR 的状态和相互关系，重点完整审阅最新 #128/#129 的变更、关键源码及紧凑证据。其他历史草稿没有被宣称完成同等级的全文审计。具体合并证据、未合并分支原因及验证范围见 [MERGE_AUDIT.md](MERGE_AUDIT.md)；19条初始开放 PR 的固定身份和处理状态见 [REVIEW_SNAPSHOT.json](REVIEW_SNAPSHOT.json)。

## 3. 相比公开 v3，究竟增加了什么

公开版本是 **2026-10-15 的 arXiv:2610.03228v3，17 页、8 图**，标题为 *Phase-Scoped Query Layouts for Reference-Preserving Speculative Decoding*。它已经包含六 session、三模型家族的请求收益，72-context 数值 replay，状态组合边界以及 software-first 的硬件讨论；这些不能在 v4 中再次包装成新发现。[版本页][V3ABS]

| 研究部分 | v3 / 原有证据 | v3 之后的实质推进 |
|---|---|---|
| QB 方法与系统收益 | 相对显式逐 query attention，Qwen3/SmolLM2/Llama 的 speculative request 延迟下降 3.06%/6.17%/2.83%；固定面板完整输出一致 | 保留为论文主结果；新微图结果不能代替或扩大这些自然请求结论 |
| RTX 执行与成本 | 已有局部对应及请求成本 | #120–123 增加持久输入控制、A/A 基线、实际 CUDA Graph 干预、1024 边界资格反例和完整转换事务 |
| Vulkan 准入 | 指定旧 source/DLL 的必要支持条件拒绝 lifted QB | #128 在新候选中以窄补丁支持已测 equal-head F16/F32 域；旧拒绝仍成立，通用 GQA 尚未证明 |
| B570 映射成本 | 未有这组均衡、全表示成本闭合 | #128 保留 QB；QH_C 的两个成本窗口均未建立实用优势 |
| 模型中的实际形状 | 尚未完成新微图与真实请求的对应 | #129 发现该真实请求实际是 q1、key256、GQA32/8，未触发 equal-head q2/q4 near1024 的研究对象 |
| 观察工具 | 旧诊断能力存在限制 | #129 补回最终时间段并排除不执行的标签；仍是约 7% 干扰的诊断 subtotal |

详细数值、参考口径与可用主张见 [EVIDENCE_MATRIX.md](EVIDENCE_MATRIX.md)。

### RTX：强软件执行模式改变了原先看起来可优化的空间

真实 CUDA Graph ON/OFF 比较中，QB 完成图成本比为 **0.615–0.849**；一些 QH−QB 差距从约 12–13 µs 缩到约 0.7–1.6 µs。该干预说明执行模式显著影响相对成本，不能据此把全部差异归因于 CPU launch。[RTX]

1023/1024/1025 邻界有实测 8/3/8 kernel 路径变化。固定逻辑输入后，1023→物理1024 的补齐能到达三 kernel 路径，却不保持规定参考；保持参考的 1023→1025 仍为八 kernel 且约贵 1.5%。这直接展示了“后端可达路径”和“可采用的参考保持优化”之间的区别。[RTX]

计入实际 ON 表示事务后，compact-QH/QB_A 为 **1.002216（q2）/1.001598（q4）**，没有建立优势。因此，论文应解释为什么强软件基线、数值资格和完整成本共同约束优化，而不是继续寻找一个事后最快坐标。[RTX]

### B570：软件准入问题可在限定域修复，性能收益仍需单独证明

#128 的新支持域是等头数、contiguous F16 A/F32 B、单列与 batch 1→2/4；实验 Hq/Hkv=8/8。完整事务含共同起点 Q 的 copy/transpose、上传与完成、图计算与同步、完整结果读回；K/V/mask 常驻，目标预分配，未含自然模型 Q 生产或 KV 更新。[B128]

固定 q2/q4 面板 QH_C−双 QB 为 **−1.518 µs，调整区间 [−4.168,+0.916] µs**；比率 **0.992244 [0.979908,1.004691]**。三个 fresh process 位于同一设备/日期，43,740 次事务属于技术重复。它支持“本范围内未建立实用优势”，不能写成“严格等价”或“QB 普适最优”。[B128]

### 真实请求：不能把 q1 的小核心占比当作多查询验证的硬件上限

#129 是同一个已暴露 HumanEval/42 输入的 observer 控制，Qwen3-8B Q8_0、124 prompt tokens、16-token cap；实际 **Hq/Hkv=32/8、q1、physical key256**。配置容量1024不是实际执行 key1024。11 成功进程、33 重复请求不是 33 个独立任务，新 clean 参考也不是对旧 B570 R 的追认。[B129]

最终同 DLL clean/profile/clean 中位 decode 为 **27.6675/29.6058/27.6794 ms**。修复后 QK/softmax/AV core 为 instrumented GPU subtotal 的 **2.8005–2.8026%**，量化 matvec/fused groups 为 **92.5152%**。前者不含 Q/K/V/O 投影，后者同时含 attention 投影和 FFN；这些份额合并了 prefill 与 continuation，也不是请求关键路径。因此不能代入 Amdahl 公式、宣称 attention 全部仅2.8%，或从名称判定带宽瓶颈。[B129]

## 4. 体系结构章节的价值与落地条件

**现在可落地的是实证性的体系结构分析章节。** 它能给读者一个具体答案：保持指定量化实现的参考行为时，哪些软件映射可用、执行模式改变了多少优化空间、表示成本在哪里抵消收益，以及微图机会是否真的出现在工作负载中。

**当前不能写成一个已验证的新加速器。** 原 companion AV 模型给强基线同样的共享与调度能力后，五个名字使用同一 policy 并达到 parity；它是功能和资源一致性控制。它没有给出 RTX 的真实归约 DAG、物理瓶颈或 PPA 优势。[H0]

若继续做体系结构，值得保留的假设是：在真实多查询验证中，能否保持每个输出的数值求值与状态语义，同时跨 query 共享权重/KV 搬运或改善有限缓冲与端口调度。它需要先证明强软件之后仍有可定位的请求开销。共享、并行和缓存能力必须同样给比较基线；不能把候选独享的理想能力当成贡献。

建议采用下列推进条件：

1. 新候选在目标真实 q/GQA/key 域得到实际支持，完整请求保持登记参考。
2. 在最强已可用软件基线、正确重放模式、自然输入与状态维护成本下仍有稳定残差。
3. 依赖时间线和独立干预说明该残差影响请求完成时间，设备计数器支持具体物理解释。
4. 才建立可校准的周期/流量模型，给出同资源基线，并讨论 RTL、综合、频率、面积、能耗与片外传输代价。

本次证据只覆盖其中的部分前提，因此保持 `SOFTWARE_FIRST/HOLD`。这是当前研究投入判断，不是断言所有硬件优化均无价值。

## 5. 论文与实验决策

推荐继续沿用标题和 QB 主体。主线是：**在保留指定部署参考的约束下，用 phase-scoped QB 保留 attention 外的批处理；通过数值、状态、后端与完整成本实验，界定该局部优化能够兑现收益的条件。**

- 论文设计和英文候选摘要：[PAPER_PLAN.md](PAPER_PLAN.md)。
- 按优先级、输入/arm、测量与停止条件组织的后续路线：[EXPERIMENT_PLAN.md](EXPERIMENT_PLAN.md)。
- 不必再等待已经完成的 RTX E2；现有证据已能形成 v4 的实质性章节增补。
- 如果期望更强的论文升级，优先等待真实 q>1 request 桥接；不要为等待一个尚无机制的新加速器而无限延长主论文。
- #102 为旧准备稿，尚未与公开 v3 源包对齐。本目录是设计，不是已经修改、编译或上传的 v4。

## 6. 保留的工程与证据边界

#127 当前为 `a793303c967567b6e07233596db8711eeb6a0a44`。源代码 CI [39373738635](https://github.com/leecdiang/HeteroSpec/actions/runs/39373738635) 成功，记录105项源测试、111 AST及137项输入核验，但六项候选修复之后仍缺新的完整独立审查，A 为 `SOURCE_BLOCKED`、B 为 `ENTRY_BLOCKED/NOT_EXECUTED`、C 为 **0/8、无 F0**。[#127 最新说明][P127]

这条旧工程资格线与 #128/#129 的实际新科学记录并存。不能说整个 B570 仍“零 GPU 数据”，也不能用新实验反向放行 CPU8。旧 CPU8 不是本次新研究的自动先决条件。

当前 B570 新研究累计计账为 **246.8043431/300 s，剩余53.1956569 s**；全部失败与先前收费保留。余额不是必须消费的实验配额，本次没有启动任何 GPU、native 模型、actor、RTL、CPU8 或自动化。[B129]

本次审阅通过 GitHub 取回源码、patch、compact 日志与元数据，并执行纯 CPU 复算。#128 完整 raw tensors 与 #129 的528份完整 logits 仍在实验机，本次未独立重读其数据字节。完整审阅记录见 [PR128](reviews/PR128_REVIEW.md) 与 [PR129](reviews/PR129_METADATA_REVIEW.json)。这些是本对话分工完成的源码/紧凑证据审阅，不是原 PR127 要求的外部认证全量复审。

[V3]: https://arxiv.org/html/2610.03228v3
[V3ABS]: https://arxiv.org/abs/2610.03228v3
[RTX]: https://github.com/leecdiang/HeteroSpec/blob/9b8cdba784b34a5aa3e8981073223c451bbaaf54/docs/research/rtx_evidence_synthesis_20261018/EVIDENCE_MATRIX.md
[RTXMERGE]: https://github.com/leecdiang/HeteroSpec/blob/9b8cdba784b34a5aa3e8981073223c451bbaaf54/docs/research/rtx_evidence_synthesis_20261018/MERGE_LEDGER.md
[B128]: https://github.com/leecdiang/HeteroSpec/blob/cf6c8bf43dc1ee4e9e8529bbe42300844e0165c9/benchmarks/b570_qb_batch_broadcast_v1/transaction_v1/RESULT.md
[B129]: https://github.com/leecdiang/HeteroSpec/blob/c541241ad62213a8d31006e539e4ce0623793040/benchmarks/b570_model_request_bridge_v1/RESULT.md
[H0]: https://github.com/leecdiang/HeteroSpec/blob/9b8cdba784b34a5aa3e8981073223c451bbaaf54/benchmarks/rtx_reference_packing_v1/H0.md
[P127]: https://github.com/leecdiang/HeteroSpec/pull/127#issuecomment-6283966676
