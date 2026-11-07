# 待执行方案：状态构造与当前目标调用路径的辨别

**状态：PLAN_ONLY。**当前只有封存输出的 CPU 分析完成。下列代码扩展、模型运行、实验冻结和迁移检验尚未进行。本文件是可审查方案；不能作为实验完成记录或既有论文主张。

## 1. 固定目标和竞争解释

目标是缩小忠实复现原生输出所需的执行，保留已有参考不一致行为也有价值。不以改变参考、自动修复或提高功能 pass@1 为目标。

G1：普通 target-only 在某一规定区域已经足够，复杂描述没有额外用途。

G2：从同一真实状态出发，当前目标 verification 的数值调用路径足以改变决定；此前 draft 历史不必作为 live 子系统保留，但输入合同仍可能需要记录的 proposals。

G3：即使固定当前目标 verification 输入和路径，进入该调用的续算状态也会改变决定；删除 draft 的配方必须保留相应状态构造。

G2/G3 可以同时存在。仅有 top-two margin 小、UB 参数不同或两条输出相同，不能排除任何解释。此处没有新 kernel 精确性定理或 stage 唯一因果主张。

## 2. 阶段 A：实现可行性和资格检查

复用已存在的 Windows RTX 5070 Ti Laptop GPU、Qwen3-8B/0.6B Q8_0、固定 b10839 数值库和现有 native observer/worker。源码已有同步、全 context serialization、恢复、sampler clone、caller tokens/positions/masks、图维度记录。它们只在初始 handoff 被验证，**不能直接继承为任意后续边界的资格证明**。

新增 hook 必须在目标 KV cleanup 后、下一次 verification forward 前导出：真实 committed prefix、未解码 pending ID、post-accept sampler clone/history、seq/positions、全目标 context state、调用 tokens/positions/sequence IDs/logits mask。报告缓存中仍有的任何 uncommitted suffix。保存当前 logits 时标明其是否会被调用读取，不假定 state API 自动保存有效 logits。

必须完成：

1. 观测开/关完整输出与 endpoint 相同；hook 不增加模型 forward。
2. 导出前后源 state 不变；同配置恢复后 contract state/positions 和行为 sham 相同。
3. UB2/UB1 跨 context 恢复满足规定兼容性；sampler 只 clone，不重复 accept 或 sample pending token。opaque sampler bytes 不可得，按历史/seed/行为限定资格。
4. 恢复到 CUDA0 且加载相同资产/数值库；四个反事实 context 顺序执行，避免同时驻留多份8B模型/缓存。
5. state 文件是全 context serialized state，不能因扩展名为 `.kv` 就称其为纯 KV tensor。不同 serialized hash 不能单独证明 KV 数值不同；需要逐层/位置逻辑 KV 导出才能做该主张。

工程完整运行最多12次；运行失败也计入上限，不按输出重新运行。若一轮限定实现审查后无法实现真实状态对齐、无扰动与可靠恢复，停止阶段 B，不用 fresh-prefill 冒充 live state。

## 3. 阶段 B：已暴露4任务的最小对照

固定诊断任务：HumanEval/15、/25、/18、/31。前两者发生方向相反的变化；后两者提供持续不变偏差和匹配控制。选择依赖已知结果，明确是诊断样本，不是 holdout。

每任务 N0/N1 各3次 fresh-process donor capture，共24次完整运行；输出合同为已有 inclusive EOG/cap128，不覆盖额外 raw suffix。记录所有 donor 输出，不以必须重现旧值为筛选成功样本的条件。

对 /15、/25，从两份 donor 轨迹中选择已知 first divergence 之前最后一个**自然出现、完全对齐**的 round-start checkpoint。必须具有相同完整 committed IDs、pending ID、seq/positions、sampler history，以及相同 verification tokens/positions/sequence IDs/logits mask。对 /18、/31 用生成位置不超过4的最后一个此类 checkpoint。若没有合格共同 checkpoint，该任务记录 UNSUPPORTED，不替换任务，不补造状态。

不得靠裁剪、补 token 或 fresh prefill 把两条 native 路径改造成共同前缀。前缀相等也不能替代 live state 的导出和恢复。

每任务/重复的固定矩阵：

| 实际 donor state | 当前 verification UB2 | 当前 verification UB1 |
|---|---|---|
| 从 N0 原生执行取得 S0 | S0,C2 | S0,C1 |
| 从 N1 原生执行取得 S1 | S1,C2 | S1,C1 |

四格使用完全相同的已冻结 pending-plus-proposal 调用合同；保持 proposals、位置、mask、采样合同，唯独改变 state donor 和当前 verification micro-batch capacity。记录实际图占用，不把 UB 参数当作实际 shape 或 kernel dispatch。

本轮 proposals 来自已经付费取得的 donor capture。**这是带输入记录的机制诊断，不能称为不依赖 proposal 的前瞻预测，也不能称为免费删除 drafting。**如果两 donor 的该调用合同不同，则矩阵不成立，不把它解释成纯状态效应。

每格恢复自己独立的未变 snapshot，执行一次规定 verification call。主指标是按同一 greedy acceptance/correction 规则实际到达的决定与必要 logits；拒绝后的无效 proposal 行不作为真实生成 token。辅助指标是在这次合法 commit/correction 后，以相同 UB1 target-only 单 token 路径续算最多32个 generated IDs，遇 inclusive EOG 提前停止；另报长度/端点。它是短反事实，不是完整原生 trajectory 复现，也不与 cap128 结果混用。

共4任务 × 2donor × 2当前路径 × 3重复 = **最多48个 fork 单元**。每个单元一次规定 verification call + 最多32次单 token 续算；工程失败和重试包含在预算中。需单列新完整运行、fork单元、prefill/target/draft token work、导出字节量，不能把所有单元混作独立任务。

S0,C2 vs S0,C1、S1,C2 vs S1,C1 检验该固定真实状态上的当前调用效应；S0,C2 vs S1,C2、S0,C1 vs S1,C1 检验固定调用上的 donor-state 效应。交互或没有可辨别差异均完整报告。恢复改变的是全 context state 时，只称 state effect，不称唯一 KV 或唯一 kernel 原因。

**第一轮硬上限：12工程 + 24donor = 36次完整运行，另48次短fork。**本 PR 实际消耗均为零。不得为获得有利结果改 checkpoint、样本或上限。

## 4. 进入阶段 C 的条件

必须同时满足：

- 阶段 A 资格通过；至少两个发生行为变化的案例有有效辨别结果，而不是全由不变控制支撑。
- 得到可执行的简化配方；它的输入在规定操作阶段可获得，不读取 future target outputs、已知分歧位置或任务 remedy 标签。
- 能说明配方相对 ordinary U2、完整 native replay、已有 H 和 recorded-proposal target replay 新增什么。若仍需录制 proposals，就明确降级为诊断重放；没有可迁移配方时不进前瞻等价验证。
- 增量超出 LLM-42 的固定形状验证或 Stage-Replay 的 cache-donor sufficiency。只重复它们的已知现象即 STOP_REDUNDANT_MECHANISM，保留有限栈确认结果。

若为了拟合成功而需要一条任务专用规则，停止，不按平台名/任务名选择动作。不要把“遇到不确定就完整执行原生”包装成新能力。

## 5. 阶段 C：一个冻结迁移检验

仅在阶段 B 达标后制定最终可执行协议。**本文件尚未冻结最终配方或选出新任务，不能称为预注册已完成。**

优先选择同一既有模型/量化/机器的 k=3 配置，改变 verification 宽度这一维度，不额外下载模型。此前 k=2 仪器资格不自动覆盖 k=3，需要新完整验收。若冻结前的资产/配置检查表明 k=3 不支持，停止该阶段；替代配置需另行显式协议版本，不能混入同一验证。

从完整项目 exposure inventory 中排除所有已看过输出的任务，不仅排除本4任务和RTX19。按固定任务源版本及预先固定排序选择8个可运行 HumanEval任务；先记录 inventory、任务ID/输入哈希、全部排除理由，再运行任何新增输出。实现 canary 仍用旧任务。未找到8个合格任务则保持 NOT_EXECUTED，不使用已暴露 MBPP24 充当 holdout。

最终 protocol/implementation commit 在新增输出前冻结，并明确 N0/N1/U2 及配方的输入、输出预测和 UNKNOWN规则。最低正式比较是8任务 × N0/N1/U2 × 3次 = 72次完整运行；资格最多6次，总上限78次。若配方需要额外生成路径，必须先修订并审查预算，不能把它隐藏在72次中。

primary 比较使用完整 committed IDs + (长度, EOG/limit, terminal ID)，同已有 cap128 合同。报告每任务三次重复和所有失败。改变 config 不等于跨模型/跨硬件迁移，更不等于普遍规律。

若没有发生 N0/N1 行为变化的新案例，最多得到“不变路径上的有限确认”；不给强预测分量，也不继续搜到变化样本为止。若配方只能输出 UNKNOWN，也报告其覆盖率，不能称等价预测成功。

## 6. 用途与成本验收、退出

完整原生重执行、ordinary U2、既有 H、recorded-proposal target replay 是明确基线。前者能忠实产生 N0，U2已有失败案例，recorded proposals是可付费重用的诊断输入。分别比较：可复现条件覆盖、删除的进程/状态依赖、目标与draft实际数值工作、错误定位所排除的竞争解释。

若主张时间收益，另测相同边界的完整总成本，含donor capture、准备、状态读取/导出、重放和验证；同样允许基线缓存与有效复用。冷启动和多次复现分开，不能用历史 RTX/M4/358H 时间代替新测量。本计划没有授权或执行时间收益测量，也没有把 CPU 解析时间当GPU节约。

退出分级：

- 技术资格失败：STOP_INSTRUMENTATION，不作机制结论。
- 只有既知 cache/shape 现象或没有可迁移配方：STOP_NEW_METHOD，增强有限实证叙述。
- 有配方但迁移失败：保留反例并缩小适用域，不调规则后继续使用同一holdout。
- 有配方和有限迁移，但无成本优势：可以讨论机制/复现范围，不能称优化。
- 只有明确增量成立，才考虑扩大到第二模型或backend，并重新评估投稿价值。
