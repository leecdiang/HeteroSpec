# B570 平台独立实验 Prompt：同状态 live 目标分区干预

冻结日期：2026-09-30（北京时间）。仓库：`leecdiang/HeteroSpec`。核对时 `main=f8290281156f6b3de8fbc8b44fd10a4afa7bcd89`，论文修订 PR #40 仍为未合并 draft。正式执行时记录最新 main、worktree、源码/二进制和环境身份；若有变化，核对后新冻结。

**为什么需要新运行：**既有 B570 研究在预先冻结后取得 target-only UB1 predictor/live 72/72、reference/live 60/72；这是路径预测，不是同一 KV/采样器状态下的 live 目标分区切换。旧 72 条数组不能充当本研究的新成对干预观测。已知四个分歧任务只能用于暴露的工程诊断；正式结论另取未暴露任务。阴性或技术不可行同样是合规结果。

## 可直接交付 B570 主机执行者的 Prompt

你负责 HeteroSpec 新研究 B570_LIVE_PARTITION_INTERVENTION_V1，独立完成方案、实现、执行、验证、归档和 draft PR。平台是 Windows 11 + Intel Arc B570 + llama.cpp Vulkan0。此研究要产生新的因果对照观测；不得把已有 72/72 target-only 预测改称 live-loop 干预，不自动 merge。

冻结的科学目标：在同一个 live speculative target-verification 决策点，以同一已提交前缀、同一已验证的目标 KV/采样器状态、同一预先记录的 draft proposal 序列与同一采样规则，成对比较 target UB1 与 UB128（或在工程资格阶段根据 pinned API 证实的等价物理分区）的目标 logits、top-1 ID 和实际提交决定。唯一有意改变的因素是目标执行分区。主终点是预定决策点的成对完整 ID/score 记录，以及每个提示词是否出现由该分区切换引起的首次不同决策；次终点是从分叉点继续的有序生成 ID 轨迹。不要预设 UB128 会恢复参考、产生 90/90 或证明某个 Vulkan kernel；零差异也是结果。

先阅读 benchmarks/b570_mechanism_v08/{HARNESS_DESIGN.md,DISCOVERY_PLAN.md,HYPOTHESIS_FREEZE.md,PREDICTION_FREEZE.md,VALIDATION_REPORT.md,CLOSEOUT.md}，scripts/platform/b570_mechanism_v08/{harness.cpp,study.py,verify.py}，benchmarks/b570_direct_id_v1/{PREREGISTRATION.md,protocol_v1.json,FORMAL_REPORT.md}，以及 docs/{experiment_protocol.md,data_policy.md}。既有 B570 参考 UB128、serialized UB1、target-only UB1 的 72/72，以及四个已知分歧任务 /134、/42、/145、/138，只可作为暴露的工程诊断和设计依据；不是新干预的正式观测。

1. 从最新 main 的干净独立 worktree/分支开始；新建 benchmarks/b570_partition_intervention_v1、scripts/platform/b570_partition_intervention_v1、artifacts/b570_partition_intervention_v1，旧 B570 v1/v0.8 及论文只读。冻结模型/数据/源码/构建/DLL、驱动与 Vulkan 版本、37/37 target 和 29/29 draft Vulkan0 offload、Qwen3-8B/0.6B Q8_0、llama.cpp b10839/0cae4306、greedy k=2、batch 512、context 1024、FA off、seed 123、128 个已提交 ID 或更早含 EOG 的端点。环境字节变化要新建资格与冻结，不能悄悄继承旧身份。

2. 首先解决“同状态”工程资格，而不是直接成对跑两个独立 CLI 进程。写出实际可执行的状态 fork/checkpoint 方案：两个分支在目标分区发生改变前必须持有相同的 token prefix、KV 状态、position、sampler 状态、proposal tape、接受/纠正规则和输出预算。记录每个分叉前的状态身份及能证明同一性的检查；如果 n_ubatch 是 context 构造时固定的，必须验证跨 context 恢复的状态等价，并说明分区切换发生在何处。两次从头运行 UB1/UB128，即便喂相同文本，也可能具有不同 prefill/历史，不能算通过。同 prefix 但 KV 无法核等，也只能算诊断。先在已暴露的四个分歧任务及参考相等控制任务做全新 R0，证明 instrumented runner 不改 committed ID 和 proposal 语义、fork 前状态确实一致、两个分支绑定 Vulkan0。若无法做到，把全部失败证据交付 INTERVENTION_NOT_FEASIBLE；不包装成因果结果，也不进入 reserved 正式测量。

3. 在任何正式新任务推理前完成仓库和主机归档暴露审计；已知旧 30 与旧 reserved 24、任何不明暴露均排除。以固定盐 + task ID hash 无结果选择 24 个新 reserved HumanEval 提示词，冻结输入及 ID、3 次重复、分叉规则、提案 tape 的无泄漏获取方式、所有要记录的验证事件、主终点的聚合和停机规则。主终点覆盖每次执行中按照已冻结规则遇到的所有合格验证决策点，不能仅挑出产生差异的点；如采用采样检查点，须在结果出现前锁定索引/规则。旧四任务可在独立“暴露诊断”表呈现，但不能混入 reserved 的 24×3 分母。新条件的 proposal 不能来自任一分支的未来 live 结果；它必须在该对照决策前固定且两分支完全相同。

4. 提交并 push 方案、技术资格报告和全部身份/端点/调度/分析代码的冻结 commit，然后在新 reserved 集执行真实 live-loop 配对分叉。对每一分叉记录原始 target logits（至少 top-2、margin、被提出 ID 的分数）、两分区的 target 决定、proposal、已提交前缀、KV/采样器状态验证、n_batch/n_ubatch 与实际物理验证分组、后续完整 committed-ID 数组。完全保留无差异、差异、失败；不做 ubatch/k/FA/模型/提示词搜索，不从旧 72 条序列复制任何正式结果。操作或状态资格失败立即停止正式解释并保留尝试，不选择性替换执行。

5. 独立验证器重算每个分叉的身份检查、条件覆盖、首次不同决策、序列端点、哈希和时间顺序；发表提示词级与分叉事件级计数，并明确相关事件不能当作独立提示词。若同状态资格通过且切换改变目标决定，可称“在这些已测状态上有目标分区干预效应”，仍不能命名唯一数值操作或推到 RTX。若仅有新 same-prefix target-only logits 对照而没有合格 live fork，结果标为 SAME_PREFIX_DIAGNOSTIC_ONLY；不得回答原定 live 因果问题。若完整新对照没有差异，报告 NO_EFFECT_DETECTED_ON_TESTED_STATES。生成可离线检查的内容寻址证据包、独立 draft PR、冻结/执行/closeout commit 链；旧证据与论文不改，不自动 merge。
