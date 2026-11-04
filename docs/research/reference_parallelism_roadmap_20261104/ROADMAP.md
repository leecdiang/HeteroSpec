# 基于当前代码与数据的 2＋1＋3 研究路线
## 保留既有数值 reference 的并行优化，以及对 TPDS 投稿的实际帮助

**评审快照：2026-11-04。文档基线：main `41ff8fd61f1c1275cf2c36103af0fa0e889b908a`。**

本文件是分析与路径规划，不是新的实验结果、实施授权或投稿承诺。它只新增文档，不合并开放实验，不改历史数据、数值 reference、运行时代码或论文。证据来自不同未合并分支，因此下面使用固定提交链接；本文件位于 main 的新分支，不代表被引用的实现已经进入 main。

## 1. 决策摘要

**建议将路线 2 与路线 1 联合推进，将路线 3 保留为有门槛的扩展。**

- **路线 2：保留归约方式的独立输出组打包。** 已有实际实现、同 operand 反例与恢复、kernel 记录，以及约 4.00% 的有限面板完整服务耗时下降。它是当前最清晰的新增性能机制，但 QB 与 WB 都能使用。
- **路线 1：可检查的数值执行契约和安全回退。** 已有物理边界、图模式识别、后端查询与策略身份，尚缺完整的支持域传递、执行前拒绝与状态安全回退。它应当把路线 2 和既有规则提升为可复用方法，而不是先承诺任意浮点程序的自动等价判断。
- **路线 3：状态来源、兼容复用与恢复。** 真实探针表明当前图策略恢复一致后，历史状态仍可能保持偏离。问题成立的线索很强，但尚无完整的跨请求 KV admission/repair 系统及净收益证据。先做最小机制验证，再决定是否进入调度与共享缓存。

这条主线不要求“QB-local 普遍快于 WB”。新的核心问题可以是：

> 在忠实既有 scalar reference 的约束下，如何识别并利用仍然合法的硬件并行性，并让未知执行和状态安全退出优化路径？

这是研究方向，不是现已证明的通用结论。

## 2. 当前证据账本

| 证据 | 已有事实 | 对路线的作用 | 不能推出 |
|---|---|---|---|
| [#171 算子与自然服务结果](https://github.com/leecdiang/HeteroSpec/blob/371223b696bb805030c29f04e39eb17b57fb2ebb/benchmarks/rtx_operator_frontier_v1/execution/RESULTS.md) | 16 个捕获算子实例；普通宽度 8/16/32 偏离 scalar，packed 路径在这些实例上恢复逐位一致；四输入服务约降 4.00% | 路线 2 的正基础 | 所有层/输入/硬件的证明，或 QB 独有收益 |
| [#166 共享规则](https://github.com/leecdiang/HeteroSpec/blob/abd36bea639bf814159ad68ab015bc983c5338b1/src/reference_batching/reference_batching.hpp)、[CUDA 接入](https://github.com/leecdiang/HeteroSpec/blob/abd36bea639bf814159ad68ab015bc983c5338b1/src/reference_batching/activate_cuda_requirements.py) | 物理 extent、连续相等分组、图模式、placement 与复用身份 | 路线 1 已有可复用部件 | 从任意程序自动抽取数值语义 |
| [#165 Vulkan 映射](https://github.com/leecdiang/HeteroSpec/blob/5aae66e05b0f6e8a8b44dac719b2b05b8f84f34f/scripts/b570_qwen_transfer/map_vulkan.py) | 实际 dispatch/activation 路径查询与修正 | 路线 1 的另一后端实例 | CUDA、Vulkan 的差异都来自同一原因 |
| [#165 同 context 探针](https://github.com/leecdiang/HeteroSpec/blob/5aae66e05b0f6e8a8b44dac719b2b05b8f84f34f/benchmarks/reference_batching_transfer_20261103/b570_host/QWEN_NATIVE_PROBES.json) | precision 切回后两行仍偏离 scalar | 路线 3 的状态历史线索 | KV-only 因果结论，或已实现修复 |
| [#174 RTX 自然 prefix](https://github.com/leecdiang/HeteroSpec/blob/aa7ff4e64752be3de0d7974febbce453ae3a96c0/benchmarks/rtx_prefix_reuse_v1/execution/RESULTS.md) | 32 roots、四个同日 session；AUTO 常量 WB-cut，无注册服务收益 | 限制 selector 与 QB 普适主张 | 策略等价，或 AUTO 永远无用 |
| [#175 B570 自然 prefix](https://github.com/leecdiang/HeteroSpec/blob/cd5f542a851d192e21187bc00566de0f685e2383/benchmarks/b570_prefix_reuse_v1/RESULTS.md) | AUTO 常量 WB-rechunk；所有主区间跨 1；原生与交付复原已完成 | 双平台负结果与成本约束 | 线上命中率、SLA 或生产调度收益 |
| [#177 RTX 条件化 rechunk](https://github.com/leecdiang/HeteroSpec/blob/610fd3a364bec6e8a3881ef666bedacd2035679a/benchmarks/rtx_rechunk_discrimination_v1/RESULTS.md) | 8 个未暴露 root；WB-rechunk append 更快，完整服务 session 反向 | 强 target-only 对照必须保留 | 稳定服务收益或总体平均收益 |

**#175 最新状态修正。** 早先 `92f8a32` 快照中最终交付未确认；本文件使用新头 `cd5f542a851d192e21187bc00566de0f685e2383`。其 [DELIVERY_READBACK](https://github.com/leecdiang/HeteroSpec/blob/cd5f542a851d192e21187bc00566de0f685e2383/benchmarks/b570_prefix_reuse_v1/evidence/DELIVERY_READBACK.json) 记录 25,546 个逻辑文件复原、所有归档对象核验、same-host authenticated fresh download=true、external native replication=false。应当更新交付状态，但不能把它改称第三方 GPU 复现。

### 数值契约层次

目标分布保持、生成 token 相同、完整 binary32 logits 相同、committed KV/final state 相同是不同验收层。当前研究必须保留每项实验实际使用的层次，不能把 token pass 升格为完整状态 pass。性能比较也必须说明候选是否满足同一个 reference 合同。

## 3. 路线 2：把已有打包补丁发展成有边界的优化方法

### 3.1 实现是什么

[packed.patch](https://github.com/leecdiang/HeteroSpec/blob/371223b696bb805030c29f04e39eb17b57fb2ebb/benchmarks/rtx_operator_frontier_v1/execution/packed.patch) 在既有最多四列 matmul lowering 上增加：

1. 对连续 F32 输入，把前 `floor(q/4)*4` 列视为 `[K,4,groups]`；
2. 用同一未批处理 Q8 权重广播到独立组，调用一次现有 `ggml_mul_mat`；
3. reshape 输出；不足四列的尾巴保持旧的小块路径。

增加的是独立输出组的并行度，不是随意扩大每个输出的归约维度 K。没有新写一个任意宽度 CUDA GEMM。现有 q 范围是 `4<q<=32`，实际 packed 分支从 q>=8 开始，另有权重与输入高维、连续性限制。

### 3.2 为什么这个机制值得研究

[相同 operand replay](https://github.com/leecdiang/HeteroSpec/blob/371223b696bb805030c29f04e39eb17b57fb2ebb/benchmarks/rtx_operator_frontier_v1/execution/replay.inc) 和 [first-divergence](https://github.com/leecdiang/HeteroSpec/blob/371223b696bb805030c29f04e39eb17b57fb2ebb/benchmarks/rtx_operator_frontier_v1/execution/evidence/first-divergence.json) 将 scalar、tile、native-wide、packed 放在同一输入下比较。已保存的 16 描述符/288 路由记录支持报告中的等价模式。实例为两个 Qwen 模型、每个八类算子，不能误称所有网络层。

CUPTI 记录显示，q4 与 q8 可使用同一类 row-Q8_1 quantizer，但选择不同 MMVQ block 配置；q16/32 又进入其他计算路径。因此“同 dtype/同 quantizer”不足以判定数值合法。该证据同时给路线 1 一个可证伪的问题。临时量化 activation 的每一字节没有在这里单独隔离，因此不把 launch 配置变化当作已经排除所有其他因素的单一因果证明。

性能也必须逐项读：

| 8B q32 算子 | 旧 tile/concat，中位微秒 | packed，中位微秒 | 解释 |
|---|---:|---:|---|
| Q projection | 172.4 | 150.2 | 真实局部改善 |
| K projection | 68.4 | 45.9 | 真实局部改善 |
| V projection | 67.1 | 67.5 | kernel 23→2 仍不保证更快 |
| Final output | 8864.1 | 8542.4 | 大算子中收益比例较小 |

这些是三次 warmup 后同步非 profiler 计时的中位数；不要将 profiler kernel 时间之和混成服务耗时。

自然面板四输入、三 session、36 个服务记录：
- old QB：3.3562237304 s；
- packed QB：3.2218509798 s；
- packed WB：3.1985217597 s；
- old/new QB=1.0417066933×，即耗时下降约 4.00%，不是下降 4.17%；
- new WB/new QB=0.992759063；打包对照 11/12 配对块支持改善，WB 在三个 session 均略快。

主要收益在 prefill。k3 verification 只有四行，没有进入此 packed 分支。#174/#177 共享打包实现而没有旧/新算子消融，提供更多资格场景，却不是新的打包加速证据。

### 3.3 尚缺什么

- 实验 driver 固定 CUDA/all-GPU；通用图补丁本身缺完整的 backend/residency admission。
- q<=32、Q8_0/F32、连续布局之外尚未资格确认。不能把“输出独立”直接当作跨设备浮点逐位相同的证明。
- 尾组、非连续输入、其他量化格式、不同 build/driver/kernel dispatch 都可能改变条件。
- kernel 数不是目的。应优先保留实际减少 wall time、内存访问或 materialization 的变换。

**下一步产物：**明确适用谓词、原路径 fallback、尾部规则和后端身份的 reduction-preserving packing 模块；再以预先选择的未见实例测其覆盖与失败。先复用现成捕获和代码分析，不启动新的无边界模型扫测。

## 4. 路线 1：让优化资格成为可检查接口

### 4.1 已经做过的部分

[共享 header](https://github.com/leecdiang/HeteroSpec/blob/abd36bea639bf814159ad68ab015bc983c5338b1/src/reference_batching/reference_batching.hpp) 提取实际物理 head/occupancy/capacity/padding 下的 extent，处理不支持的 sparse/noncontiguous、sliding-window、多 stream 状态，按 requirement 相等分最大连续组。

[CUDA 识别](https://github.com/leecdiang/HeteroSpec/blob/abd36bea639bf814159ad68ab015bc983c5338b1/src/reference_batching/activate_cuda_requirements.py) 已通过图边识别 RMSNorm→MUL→RoPE 结构，并比较 scalar/batch placement；不是只凭 tensor 名。部分 README 旧描述落后于代码，复核应优先看实际实现。

[Vulkan mapper](https://github.com/leecdiang/HeteroSpec/blob/5aae66e05b0f6e8a8b44dac719b2b05b8f84f34f/scripts/b570_qwen_transfer/map_vulkan.py) 查询实际 `ggml_vk_should_use_mmvq` 等条件，比较 scalar/batch activation quantization。图复用已有 layout、prefix、precision、placement、implementation 身份。

这些不能再次列作“尚未实现的创新”。

### 4.2 真正的缺口

**描述符不足。** 同 ActivationPath 返回 unchanged 的规则不能概括 #171 同 quantizer、不同 reduction/dispatch 的反例。新契约需要表达具体 reduction/accumulation realization，而不是仅列类型。

**unsupported 没有贯穿执行。** [native integration](https://github.com/leecdiang/HeteroSpec/blob/abd36bea639bf814159ad68ab015bc983c5338b1/src/reference_batching/integrate_llama_cpp.py) 中某些 extractor 状态最终只传出 extents，不支持时走 legacy generic path；该路径未被宣称 reference-preserving。Vulkan 的 `ProjectionAction::unsupported` 也没有全部转成硬拒绝/原 scalar fallback。

**回退必须保护状态。** 在已修改状态后重新打开精度开关，并不等于恢复原 reference。执行前 admission 与执行后 checkpoint 恢复是不同操作。

### 4.3 限定域契约的建议设计

以下是提案，不是已存在 API：

- 操作数：dtype、shape、stride、alias/contiguity；
- 执行：backend/placement、quantizer、accumulator/reduction schedule、kernel/dispatch identity、build/runtime 身份；
- 状态：reference identity、producer recipe、已验证状态边界、physical extents；
- 规则：适用谓词、变换、拒绝理由、fallback、验证证据与版本；
- 输出：允许、拒绝或需恢复；未知情况不能获得 reference-preserving 标签。

首批只注册已有四类：physical prefix split、Vulkan F32-preserving batch、CUDA head-placement preservation、四列 packing。让同一接口解释这些实例，而不是为每个新模型继续添加不透明名字判断。

**验证问题：**契约能否在执行前正确预测已知反例的拒绝、合法组的接受，并且对未知/不支持输入安全回退？预测必须在结果前固定，不能见到输出不一致后改规则再算一次通过。

这能形成方法贡献，但 descriptor 完备性、backend 相对保证及证明范围必须明确。有限全向量测试不自动成为全输入形式证明。

## 5. 路线 3：把 graph identity 与 state lineage 分开

### 5.1 已有实现与尚未实现的系统

[CPU contract](https://github.com/leecdiang/HeteroSpec/blob/41ff8fd61f1c1275cf2c36103af0fa0e889b908a/src/query_layout/contract.py) 已包含 reference/state_recipe/role/phase/layout/signature；实际 native graph reuse 已有 policy identity；[#152 boundary](https://github.com/leecdiang/HeteroSpec/blob/022babfabb3d1b6f4f2a2830dca04b2654d193f9/benchmarks/b570_producer_consumer_boundary_v1/native/boundary.cpp) 还做过 state 和初始 logits 的导出、恢复、重新导出核对。它们分别是接口模型、图缓存安全和实验状态恢复，不能混称完整的共享 KV 服务。

当前缺少的是：跨请求历史来源传播、producer–consumer 兼容 admission、失效传播、部分恢复/重算与服务成本的统一系统。

### 5.2 最有价值的状态反例

[probe 结果](https://github.com/leecdiang/HeteroSpec/blob/5aae66e05b0f6e8a8b44dac719b2b05b8f84f34f/benchmarks/reference_batching_transfer_20261103/b570_host/QWEN_NATIVE_PROBES.json) 与 [执行代码](https://github.com/leecdiang/HeteroSpec/blob/5aae66e05b0f6e8a8b44dac719b2b05b8f84f34f/scripts/b570_qwen_transfer/probe.inc) 在固定 teacher-forced IDs、同一 context 下记录：

| base | precision | graph reuse delta | 两行是否等于 scalar |
|---|---|---:|---|
| 253–259 的该序列 | true | 随形状有重建/复用 | 都是 |
| 261 | false | 0 | 都否 |
| 263 | true | 0 | 都否 |
| 265 | true | 1 | 都否 |

切换之后并没有恢复历史 state。因此，它支持“当前图重新兼容不自动修复历史”的推论，但没有独立隔离 KV、initial logits 及其他状态的各自因果贡献，也没有验证新恢复方案。

[#152](https://github.com/leecdiang/HeteroSpec/blob/022babfabb3d1b6f4f2a2830dca04b2654d193f9/benchmarks/b570_producer_consumer_boundary_v1/RESULT.md) 两个固定-R producer 条件案例是重要背景；[#165](https://github.com/leecdiang/HeteroSpec/blob/5aae66e05b0f6e8a8b44dac719b2b05b8f84f34f/benchmarks/reference_batching_transfer_20261103/b570_host/RESULTS.md) 已修复它们，并用 precision-only reversal 复现旧失败。不能把已经修好的案例当仍未解决的线上故障。

普通 speculative rollback 删除未接受 suffix，保留 accepted-prefix/pending-token/bonus 语义。它不等于对已接受但数值不兼容的历史做 provenance rollback。

### 5.3 先问机制问题，再问调度

最小比较应包括：只更新 graph key、拒绝可疑状态、恢复干净 checkpoint、固定 canonical producer、完全隔离 producer recipe、全量重算。token-only 不安全复用可以作为反例，不宜作为唯一性能基线。

先验证：
1. 完整 vectors、committed state 和 token/position 是否恢复；
2. 哪些状态能被安全接受，哪些必须拒绝；
3. snapshot/checkpoint/metadata/import/recompute 的真实成本；
4. 是否确实存在多个兼容类及有价值的复用机会。

若所有 producer 已修成同一 reference，兼容分类可能退化为一个类别。若保守隔离损失的 hit 或重算成本超过收益，就不推进复杂 scheduler。若有明确价值，再扩展共享缓存、驱逐、分页、并发和服务 SLO；现有 [native contract](https://github.com/leecdiang/HeteroSpec/blob/801196166c8e2a02215003301d129e68504e6b72/benchmarks/tpds_prefix_reuse_v1/NATIVE_CONTRACT.md) 明确不覆盖 fragmented/sliding/multi-stream。

## 6. 为什么不继续把 AUTO 当核心赌注

[#174](https://github.com/leecdiang/HeteroSpec/blob/aa7ff4e64752be3de0d7974febbce453ae3a96c0/benchmarks/rtx_prefix_reuse_v1/execution/RESULTS.md)：32 roots×4 同日 session，AUTO 常量 WB-cut；AUTO 比最快 fixed 点估计慢 0.635%，主 family-adjusted 区间跨 1。校准成本约 2038.78 s。不是等价证明。

[#175](https://github.com/leecdiang/HeteroSpec/blob/cd5f542a851d192e21187bc00566de0f685e2383/benchmarks/b570_prefix_reuse_v1/RESULTS.md)：AUTO 常量 WB-rechunk；QB/AUTO=0.9997066，family95=[0.9978614,1.0016849]。对 WB-cut 的极小正平均 saving 对应约 104.7 万 cache hits 的点 break-even，但 saving 区间跨零，不能保证有限摊销。所有主请求按 replay 构造都是 hit，不是生产命中率。

两个平台的 12 calibration roots 都没有 crossing。自然全池 6423 paths 中，573 个 crossing、298 个 WB ordered schedule 不同、192 个 call count 不同；8.92%/4.64%/2.99% 是路径占比，不是时间加权收益上限。

[#177](https://github.com/leecdiang/HeteroSpec/blob/610fd3a364bec6e8a3881ef666bedacd2035679a/benchmarks/rtx_rechunk_discrimination_v1/RESULTS.md) 的 8-root 条件化测试给 WB-rechunk/QB append=0.960486，完整 service=0.994379，两个 service session 方向相反。只能表明此条件面板未建立 QB 优势，不能外推总体。

这不证明所有 AUTO 都无用，而是说明当前候选池、观测特征与校准预算没有支持它。先改变执行成本的候选空间，再谈选型更合理。

## 7. 与近邻工作的差别及新颖性检查

以下为文献定位，不作跨系统速度排名；近期预印本须在投稿前复核版本。

| 近邻 | 必须承认的已有思想 | 本路线仍需证明的差别 |
|---|---|---|
| [Thinking Machines batch invariance](https://thinkingmachines.ai/blog/defeating-nondeterminism-in-llm-inference/)、[vLLM](https://docs.vllm.ai/en/stable/features/batch_invariance/) | 固定数值路径、batch-independent reduction 已有工程实现 | 忠实既有 reference 的条件，而不只是选择一个新的 canonical |
| [Vosti](https://arxiv.org/html/2609.38981v1) | batching/chunking/KV 逐位关系和程序分析是直接近邻 | 已部署 reference 的变换资格、具体可用优化、状态历史边界；不能仅换术语 |
| [LLM-42](https://arxiv.org/html/2601.17768v2) | 固定 verifier、验证/回滚与 KV 修复已有先例 | 既有 reference 下的精确合同、低成本安全变换，不能把 verify+rollback 作为独有创新 |
| [Bit-exact inference verification](https://arxiv.org/html/2606.00279v1) | 记录/复现既有硬件行为是相关路线 | 我们主要优化合法执行，仍需比较其 replay/verification 契约 |
| [Hydragen](https://arxiv.org/abs/2402.05099)、[RelayAttention](https://aclanthology.org/2024.acl-long.270/) | 独立请求共享 prefix 的读取/计算已有方法 | 数学等价不等于旧实现逐位等价，需同合同比较 |
| [BatchLLM](https://arxiv.org/abs/2412.03594)、[Sarathi-Serve](https://arxiv.org/abs/2403.02310)、[FlashInfer](https://arxiv.org/abs/2501.01005) | 重填块、launch/尾块与全生命周期优化已有系统设计 | 与公平强 target-only 基线比较，而不是弱切块对照 |
| [FlashInfer Autotuner v2](https://flashinfer.ai/2026/09/22/autotuner-v2.html)、[Stream-K](https://arxiv.org/abs/2301.03598) | 独立 oracle、部署一致计时、稳健固定实现 | 净收益与候选池空间，不能把事后 oracle 当线上策略 |

文献审查应产出逐项 claim matrix：相同目标/不同合同/已有方法/新实现/未证明假设。不能仅以“我们要求更严格”作为新颖性；必须展示这种约束下有用且可推广的方法。

## 8. 阶段路线与明确决策条件

本节是未来实施建议；本 PR 不启动这些阶段，不预先分配 GPU 请求额度。

| 阶段 | 最小产物 | 继续条件 | 缩减或停止条件 |
|---|---|---|---|
| A：CPU/源码盘点 | 现有变换、guard、fallback、固定源身份与反例映射；可复用 replay 清单 | 存在明确未覆盖条件或可消除成本 | 只是重命名已做内容，则整理文档后结束 |
| B：2＋1 限定实现 | packing admission、tail/fallback、执行契约与拒绝理由；原 scalar 保持不变 | 同 operand 与状态测试通过，未知域安全退出 | 需要修改 reference 才通过，或 fallback 破坏历史，暂停该变换 |
| C：有限推广 | 预先定义的一组新 shape/operator/backend 条件，独立资格与计时 | 不依赖事后删失败，存在可解释覆盖与净成本改善 | 只剩单一特例，则降低一般性主张，避免无边界扩表 |
| D：完整服务确认 | 相同 arithmetic 的最强 WB-rechunk/fixed、QB 和必要消融；独立数据/测量 | 完整成本含调度/校准/状态操作后仍有稳定收益或清楚的适用规律 | kernel 收益不转化，保留负结果，不追逐旧 3% 门槛 |
| E：路线3最小机制 | graph-only、state rejection、checkpoint recovery、canonical replay 的对照 | 恢复正确且兼容类/复用机会有实际价值 | 所有安全路径同类，或 metadata/重算吃掉收益，停止扩张 |
| F：论文整合 | 主张-证据-限制一一对应，保留旧负结果与强基线 | 新主线足够独立且完成验证 | 未满足则按现有范围投稿或转向更匹配期刊，不用愿景替代数据 |

具体 native 预算、独立输入和成功条件应在代码候选明确后预注册。不要现在随意规定新的百分比或大量 GPU 扫测。每个后续实验应回答能改变路线选择的问题。

### 共同评测规则

- original scalar reference、输入选择、停止条件与 estimator 在输出前固定。
- 资格与速度分离；完整 logits/state、token/position/transaction 分别记录。
- 使用同样优化的 WB-rechunk、设备/模型 fixed 策略；AUTO 若保留，必须计算 dispatch、特征、校准和切换净成本。
- oracle/校准/测试独立；按 root/session/time 分组，不能把重复调用当独立样本。
- 保留所有失败、回退与成本；不只报告获胜实例。
- q、head、尾组和 cache boundary 的机制面板与自然服务面板分开；条件化结论不冒充自然平均。
- 同设备、跨日期、跨后端、跨设备是不同外推范围；源码可移植也不等于数值可移植。
- snapshot-backed replay 与真实 resident/online serving 明确区分。吞吐/SLA 需要实际服务实验支持。

## 9. 对投稿的帮助与现实判断

### 9.1 目前最容易被审稿人质疑的地方

1. “local grouping 比 whole-graph 更快”在强 WB 与自然 workload 下缺乏稳定支持。
2. 提供复杂审计和很多边界案例，不自动构成新的高效并行方法。
3. 四输入、单 RTX 的约 4% 结果不足以支撑广泛系统性能主张。
4. 新 canonical determinism、旧 reference preservation、有限测试与形式保证若混用，会使核心主张失去可信度。
5. 缓存实验若只是 replay，不能写成生产 prefix-cache scheduler。

### 9.2 2＋1 能补什么

- **方法贡献：**将人工修补变成有适用谓词、拒绝行为与可复用实现的变换族。
- **机制解释：**展示同数学算子/类型为何不足，以及保持 reduction descriptor 时仍能增加独立并行度。
- **并行系统价值：**不依赖 QB 赢，而是与任何满足合同的强 caller 组合，并报告完整服务成本。
- **一般性：**把扩展目标从“再多跑几条 prompt”改为明确的新算子/dispatch/布局条件。
- **可复现性：**固定实现、反例和失败域，使外部研究者能判断自己部署是否适用。

路线 3 若成立，可补状态生命周期的系统贡献；若不成立，不应为了论文规模而强行绑定到主线。

### 9.3 建议的论文叙事

1. 现实需求：复用既有数值 reference，而不是替换成新的 deterministic runtime。
2. 核心难点：shape/dispatch/producer history 改变可破坏该 reference。
3. 方法：受契约约束的优化空间、注册变换、状态安全退出。
4. 具体实例：归约保持的独立组 packing，以及已验证的后端规则。
5. 评测：同合同强 fixed/WB 基线、完整成本、适用规律和负结果。
6. 若路线3成熟，再加入共享状态 admission/recovery；否则作为有证据的边界问题。

这仍是候选结构，不在本 PR 中重写论文。

### 9.4 TPDS 的判断

**这条路线可以提高稿件的研究完成度和论证质量，但目前不能客观给出一个中稿概率百分比。** 缺少校准的投稿样本，且关键推广和系统结果尚未发生。仅创建路线文档不会改变录用可能性；真正有帮助的是后续可验证的贡献。

- 若 2＋1 能在有意义的不同条件下复用，明确守住原 reference，并在强基线下体现可解释的净收益，则更接近有说服力的并行系统论文。
- 若最终仍是一个特定 RTX 补丁加小面板收益，适合缩小主张；TPDS 的贡献规模与一般性仍是明显风险。
- 若 3 只增加元数据而没有兼容性或成本优势，不把它充作额外贡献。
- 如果性能普遍接近强 fixed，也可以保留数值关系与机制结果，但应重新评估论文类别与目标期刊，而不是包装成通用加速。
- JSA 也要求充分的方法和实证贡献，不是自动接收的退路。选刊应根据完成后的实际贡献，而不是期望值。

## 10. 本次审查与发布边界

此次分析读取固定提交下的源代码、patch、报告和 JSON/压缩记录；分别核算 #171 的 16 描述符/288 路由模式与 36 服务记录，#174/#175 的六个主几何估计，以及 #177 的 48 条测量与 phase 加和。此类核算是报告/记录级独立重算，不是本次重新运行 GPU，也不是重新下载和重放所有原始向量。

写入本文件前再次读取 #175 最新 RESULTS 与 DELIVERY_READBACK，更新了交付状态。文献定位来自同期相关工作审查；不是穷尽性或独立实验复现声明。

本 PR 的验收：
- 仅新增本路线文档；
- 所有仓库证据链接使用明确的完整提交号；
- 已实现、已观测、推论、未来建议分别标记；
- 不改历史失败、不替换原 reference、不合并开放实验；
- 后续代码或实验需要单独明确任务与预算，不能把路线文档当运行指令。
