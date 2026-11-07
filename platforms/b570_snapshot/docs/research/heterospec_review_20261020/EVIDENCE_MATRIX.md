# HeteroSpec：主张、参考与成本窗口证据矩阵

审阅日期：2026-10-20。公开基线为 [arXiv v3][V3]（2026-10-15 修订）。最新 RTX 结果以 [PR124 综合表][RTX] 对 PR120–123 的固定科学提交为索引；B570 新证据来自 [PR128][B128] 与 [PR129][B129]。

## 1. 论文应保留的中心关系

**v3 已提供具体方法与自然请求收益；新增实验解释哪些优化机会能通过参考资格、软件基线和完整成本核算。** 新证据加强方法的适用边界，尚未形成加速器贡献。

每项主张绑定六项：参考行为 (R)、已测输入 (X)、运行时与设备 (E)、候选映射 (M)、成本窗口 (W)、比较基线 (B)。数学等价、局部张量对应、完整请求输出一致是不同层次；后端接受映射也不自动满足后三者。下表中的“合格”只覆盖对应输入及冻结环境。

## 2. 已公开的正结果：更新时应保留

| 证据 | 事实及参考/基线 | 窗口与范围 | 可用于论文的结论 | 不可外推 |
|---|---|---|---|---|
| v3：方法 | QB 配对变换 query/mask 视图、共享 KV，并将 phase/layout 纳入图复用 | 受支持的非 FlashAttention 路径 | 一个保留周围投影与 FFN 批处理的局部表示方法 | 不证明其他算子批量不变或所有后端支持 |
| v3：自然请求正收益 | 对显式逐 query attention（PQ），Qwen3/SmolLM2/Llama 请求延迟分别降低 **3.06%/6.17%/2.83%**；固定面板完整参考输出一致 | 两日期、六 session；完整推测请求 | QB 的表示选择具有已测系统收益 | 这些比例不是对普通非推测解码的加速，也不是对 B570 的收益 |
| v3：局部与状态边界 | 72 个 CUDA context 中，PQ/QB 在 QK、softmax、AV 逐位对应；Vulkan 状态干预显示相同端点不保证组件可互换 | 三个层位置、两个 phase、q=1–4；状态研究使用自身参考 | 局部对应与状态组合需要分别验证 | 72-context replay 不等于 CUDA Graph capture/replay，也不赋予后续微图完整请求资格 |

本轮不会用新的阴性微图结果否定上述自然请求正结果：它们比较的基线和问题不同。[V3]

## 3. RTX：强软件基线如何收缩“硬件机会”

| 固定证据 | 观察与参考/基线 | 实际窗口 | 保留的论文含义 | 范围限制 |
|---|---|---|---|---|
| PR121：正结果 | 双 QB 同实现对照；核心面板 **QB_A/QH_C=0.900826**，24 个 q2/q4 几何中 19 个支持 QB、5 个未决 | 常驻图到完成同步 | QB 是较强的软件基线，不能只与较慢候选比较 | 两 session、固定输入；A/A 包络不认证每个几何的 2% 分辨率 |
| PR121：策略阴性结果 | 留出 12/12 均值方向预测正确；加 lookup 的离线策略/固定 QB=**1.010298** | 实测分量的离线相位和 | 能预测方向不等于能实现净收益 | 不是集成 selector 或 decoder 成本 |
| PR122：执行模式干预 | 实际 CUDA Graph ON/OFF 下 QB 成本比 **0.615–0.849**；四个 permuted-q2 坐标的 QH−QB 差由 12.056–12.975 μs 缩至 0.735–1.627 μs | 匹配 clean 图完成窗口；profile 单独确认 capture/replay | 执行模式改变候选优化空间 | 不把总干预效应全部解释为 CPU launch 开销 |
| PR122/123：边界反例 | 1023/1024/1025 处出现 **8→3→8 kernels**。固定逻辑输入后，L1023→S1024 为 **0/4** 字节资格；L1023→S1025 为 **4/4**，但对两个 native QB 基线成本比约 **1.0148/1.0150** | 不合格路径止于首执行；仅合格路径有 clean 成本 | 可到达的快路径仍可能不满足指定参考；可合格的表示也可能无收益 | 不能给失败路径画加速柱；kernel 数不识别带宽、占用率或独立因果机制 |
| PR123：完整事务阴性结果 | q2/q4 的 compact QH/QB_A=**1.002216/1.001598**；对 QB_B=**1.008295/1.004167**，均未通过实用收益筛选 | 同一连续 copy/transpose→Q 上传→实际 replay/同步→完整 ordinary 读回 | 计入形成表示的成本后，保留固定 QB | KV/mask 常驻、目标预分配；不含自然 Q 生产与 KV 更新；未决不等于严格等价 |

来源：[RTX 综合证据与固定来源索引][RTX]。这些后续微图比较的参考是规定的完整 ordinary 输出；不得借用 v3 的模型请求资格。PR123 的 `SOURCE_LINK_UNKNOWN` 与其他历史失败继续保留。

## 4. B570：从后端准入到真实请求相关性

| 证据层次 | 事实及基线 | 窗口/覆盖 | 可说与不可外推 |
|---|---|---|---|
| PR128：准入正结果 | 原冻结 backend 拒绝沿第四维抬升的多查询 QB；窄修复利用现有 shader broadcast，使受测几何通过；无 KV REPEAT | Hq=Hkv=8、d=128、key=1023/1024/1025、q=1/2/4、F16/F32 | 原障碍是可修复的版本/几何准入缺口；**不是一般 GQA 支持** |
| PR128：常驻成本未决 | QH_C−双 QB=**−1.028 μs**，调整区间 **[−2.177,+0.067] μs** | compact Q 常驻图；三固定输入、三新进程 | 未建立实用 QH_C 优势；不能声称等效 |
| PR128：完整事务未决 | QB_A/B/QH_C 平均 **187.013/187.819/185.898 μs**；配对差 **−1.518 μs [−4.168,+0.916]**；比率 **0.992244 [0.979908,1.004691]**；A/A 阈值 **17.284 μs** | 共同 permuted host Q 起点；连续 copy/transpose、上传/同步、图/同步、完整读回；243 资格槽、43,740 技术重复 | 保留 QB、关闭这一受测 QH 优化分支；不含模型 Q 生产/KV 更新，不能外推端到端收益 |
| PR129：真实范围核对 | Qwen3-8B Q8_0，HumanEval/42，124 个 prompt ID、16-token cap；实际 **Hq/Hkv=32/8、q1、physical key256** | 一个暴露 prompt；11 成功进程、33 重复请求、528 组完整 logits，对**本轮首个 clean 参考**逐字节一致 | 接入了真实请求；context capacity1024不是执行 key1024。未运行 q2/q4 映射，不能移用微图资格或旧请求参考 |
| PR129：观察器修复与诊断 | serial logger 约 +12% 未过门槛；final concurrent logger补齐末组并过滤 inactive nodes。clean/profile/clean 为 **27.6675/29.6058/27.6794 ms** | 第三 context 的15个相关 decode 时延中位数；约 +7% 开销，通过预设10%粗筛 | 这是观察器扰动，**不是算法加速**；通过粗筛不证明逐算子无扰动 |
| PR129：受限成本归因 | QK/softmax/AV core 占 **2.8005%–2.8026%**；量化 matvec/fused groups占 **92.5152%** | 被观察、同步后的 GPU 小计，覆盖 prompt与continuation | 支持重新检查投影工作负载；core不含投影/RoPE/KV更新，量化组也不等于“仅FFN”。**不得代入 Amdahl，不能诊断物理带宽瓶颈** |

来源：[PR128 完整事务结果][B128]、[PR129 结果][B129]及[请求范围说明][BRIDGE]。

## 5. 论文、数据与执行状态的边界

RTX 与 B570 的运行时、GQA、输入表示、执行模式和观察器均不同。本文只比较证据关系，**不横向排列设备性能，不池化样本，不跨窗口相减成本**。RTX 的真实 CUDA Graph replay 不能成为 B570 的执行模式标签。

PR128 与 PR129 已分别以合并提交 `c9f018ff0ac5c8001deb36bcb062ff27408a673b`、`ec6b97518a2f230330d79f1b0ba2ca97bc70cd6a` 接纳为限定归档；表内仍引用原科学 head。合并不改变 CPU8 **0/8、无 F0**，也不把历史 NO_GO/HOLD 改成成功。

最新 B570 ledger 为 **246.8043431 / 300 秒，剩余 53.1956569 秒**，包含失败入口与全部后续费用；不得从 PR128 的旧余额重启。剩余额度不代表新实验需求或执行许可。

本次独立复算核对了 B570128 compact 元数据、统计、源码及 hash 见证；RTX 大 raw 和 B570 完整张量/logits仍保留在原机器。Git 小包可核验不等于全 raw 外部认证。论文应保留这一访问边界。

**更新后的章节任务：解释“有资格的映射能否在强软件基线与真实成本下兑现收益”。** 硬件继续 `SOFTWARE_FIRST/HOLD`；新请求关键路径、物理机制和 PPA 是后续待检验内容，不能由现有计数或诊断比例替代。

[V3]: https://arxiv.org/abs/2610.03228v3
[RTX]: https://github.com/leecdiang/HeteroSpec/blob/9b8cdba784b34a5aa3e8981073223c451bbaaf54/docs/research/rtx_evidence_synthesis_20261018/EVIDENCE_MATRIX.md
[B128]: https://github.com/leecdiang/HeteroSpec/blob/cf6c8bf43dc1ee4e9e8529bbe42300844e0165c9/benchmarks/b570_qb_batch_broadcast_v1/transaction_v1/RESULT.md
[B129]: https://github.com/leecdiang/HeteroSpec/blob/c541241ad62213a8d31006e539e4ce0623793040/benchmarks/b570_model_request_bridge_v1/RESULT.md
[BRIDGE]: https://github.com/leecdiang/HeteroSpec/blob/c541241ad62213a8d31006e539e4ce0623793040/benchmarks/b570_model_request_bridge_v1/PAPER_ADDENDUM.md
