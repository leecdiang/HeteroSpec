# B570 闭环诊断研究方案 — PREPARE_ONLY

日期：2026-10-03。状态：**研究方案已准备，运行资格未建立，未执行模型或 GPU。** 用户批准的是 v0.9.0 独立复评及按其结果准备后续研究。本方案不重开原 B570 campaign，也不修改原数组、分母、失败标记或作者冻结标签。若进入执行，应建立独立的新研究目录与协议版本。

## 1. 要补的知识

两位新评审均认可现有有限预测与成本结论，但仍缺一个具体证据：更简单的复现器是否能帮助区分执行原因，且它指导的改变是否在 native 路径上得到确认。目标不是为了增加样本数，也不预设一定修好、提速或得到接收。

首选任务：在 B570 四条已知 reference-divergent 轨迹上，检验一项明确的 target prefill 执行策略改变。先在无 draft 的复现器中形成可检验的输出预测，再在 native speculation 中核验。若两边对该改变的响应一致，且能区分 prefill 历史与后续 speculative orchestration 的解释，才获得比“复现成功”更强的诊断证据。

这是针对已曝光案例的诊断与干预研究，不是新的 unseen cohort。原 24 个任务的结果都已知；任何新预测只能指候选干预版本的数组在该版本 native 执行前冻结，不能改写旧案例的曝光身份。

## 2. 选择 prefill 的依据与边界

[PREPARE_SOURCE_AUDIT.json](PREPARE_SOURCE_AUDIT.json) 对三个原始源码文件做只读核对，Git blob 哈希与 v0.9.0 内容提交一致：

- H1 harness 在 `scripts/platform/b570_mechanism_v08/harness.cpp` 56–64 行经 `common_prompt_batch_decode` 输入 prompt；85–89 行为随后单 ID decode。其配置锁定 context1024、batch512、UB1/128、greedy seed123、cap128。
- 已留存的 instrumented native frontend 在 `scripts/platform/b570_partition_intervention_v1/generated_speculative.cpp` 203–205 行将 target prompt 分为前面全部 ID 和最后一个 ID 两次 caller-level decode。
- `scripts/platform/b570_partition_intervention_v1/observer.h` 34–60 行提供跨 context 的序列化/恢复与长度、内容、consumption 和 committed-history 检查起点。

这些是**源代码中的调用结构**。它们没有证明实际 backend occupied-forward 形状，也没有证明 prefill 导致了原四条差异。已有第64个输出之后的 fork 不能排除更早 prefill/KV 历史的影响。因此 prefill 是一个值得先检验的候选阶段，不是已定位的原因。

不假定存在动态 UB setter。若需在 prefill 后导出状态到不同 UB 的 context，必须新建工程资格检查，包括完整位置/KV、sampler、最后一行 logits 或 pending seed、accepted history 和序列所有权。不能凭旧 fork 恢复成功就宣称新的 phase-boundary transfer 也合格。

## 3. 有界范围

采用原 H1 的全部24个已曝光任务，不按新结果增减：

`/58, /156, /134, /42, /122, /114, /93, /115, /151, /63, /125, /133, /43, /139, /77, /35, /27, /34, /145, /82, /154, /78, /96, /138`。

四个主要诊断案例为 `/134, /42, /145, /138`；其余20个是原先 reference-compatible 的回归控制。每条件三次新运行仅检验重复稳定性，不能把24个任务改称72个独立样本。保留既有 greedy、inclusive-first-EOG/cap128、prompt tokenization、target/draft 模型与 numerical backend 约束；执行前必须填入并冻结实际资产字节身份。

不增加 GPU、模型、backend、dense checkpoint scan、M4 policy 或358H persistence。阶段归因只涉及本研究锁定的路径和状态转移；不命名唯一 kernel cause，不给全平台 losslessness 或性能保证。

## 4. 工程门 G0：先验证能否建立有效对照

G0 是准备与资格门，不进入正式结果分母。必须交付：

1. 新目录、协议、source/build/model/tokenized-prompt/backend/driver 清单及全部可得哈希；未知项保持 unknown，不能用旧清单替代实测身份。原文件只读。
2. 三个明确程序：target-only reference、target-only H1 reproducer、native speculation。基线分别与原完整 expected arrays 一致；若历史栈已无法忠实重建，标记 BLOCKED，不悄悄把新栈当旧栈。
3. 同 partition 的 prefill-boundary sham transfer 控制。至少固定四个诊断任务和 `/58` 三重复检查；后续正式基线也须在全部24个任务上通过旧数组回归。完整 KV/位置/sequence、sampler clone/accepted history、logits/pending seed 和恢复 consumption 的能力分别记录；缺失 opaque bytes 时不声称逐字节身份。
4. 新 instrumentation 的 output-equivalence 控制。记录实际 target forward 的 phase、输入 ID、positions、sequence IDs、occupied token counts、logits selection、KV mutation/reconciliation 和 sample/accept/correct/bonus 对应。UB capacity 与 caller batch length 保留为独立字段。backend 内部形状未观察到时写 unavailable，不能从这两个字段推造。
5. 明确 prefill policy 的实现：candidate native 与 baseline native 只改变 target prefill partition policy；logical caller grouping、后续 UB1 policy、draft 设置与 rollback/sampler 规则保持一致。两者若都需 transfer，则使用同一 sham-transfer 机制。复现器与 native 的 prefill 输入调用规则另行对齐并记录，避免把两个改动混称单一 micro-batch 因果效应。

如果G0无法建立单一改变和可信恢复，停止在工程 BLOCKED。不能以“获得正结果”为理由降低门槛。当前只读源码核对不足以令G0通过。

## 5. 正式候选条件与冻结顺序

以下是**候选条件设计**，只有G0通过、具体 policy 字节和资产清单冻结后，才成为可执行协议。每条件24任务×3，计划共360个完整数组；G0控制和pilot单列，不合并成额外正式样本。

| 条件 | 程序 | Target prefill | 后续 target execution | 用途 |
|---|---|---|---|---|
| R | 已定义 target-only reference | 原 reference policy | 原 reference UB128 | 明确参考契约并重建基线 |
| T0 | 无 draft reproducer | 原 UB1 policy；必要时同型 sham transfer | H1 UB1 | 对旧预测完整数组回归 |
| N0 | Native speculation | 原 UB1 policy；必要时同型 sham transfer | 原 native UB1 | 对旧 native 完整数组回归 |
| T1 | 无 draft reproducer | 候选 UB128 prefill policy，后转 UB1 context | H1 UB1 | 在 native 候选运行前冻结完整预测 |
| N1 | Native speculation | 与T1对应的候选 prefill policy，后转 UB1 context | 与N0相同 policy；draft follow own live history | 检验诊断预测是否回到 native 成立 |

R、T0、N0基线条件的归属和 caller-level规则以G0审查后的协议为准。不能用“UB128/UB1”标签替代实际输入和执行契约。R是参考比较对象，不自动称为唯一正确的数学输出。

顺序：先锁定任务/资产/实现/判据 → 完成G0与基线资格 → 冻结唯一候选T1/N1代码和所有假设 → 运行并封存全部T1完整数组 → 保存hash/remote acknowledgement及首个N1开始记录 → 执行N1 → 最后统一比较。N1不得导入T1未来ID；candidate选择阶段接触的输出如实标为探索/曝光。不得根据N1结果改候选、加任务或选checkpoint。若进一步探索其他改变，另开协议，不混入本正式测试。

## 6. 验收与结果分支

主要检验：每个任务的 `T0 == N0` 与 `T1 == N1` 完整数组及endpoint关系；四个诊断任务的 `N0 != R` 与 `N1 == R` 是分别报告的参考恢复结果。20个回归控制逐任务给出candidate/reference变化。不得仅用长度相同或首差相同代替完整匹配。

每个条件保留所有raw arrays、EOG/cap、第一次差异、actual trace、state检查、sampler/pending状态、退出码、失败及未达到记录。Score change、state change、即时ID/acceptance变化和完整trajectory变化分开，不从边际logit描述推造 near-tie causal witness。

| 结果 | 允许的解释 | 不能声称 |
|---|---|---|
| T1/N1完整匹配，四条差异均恢复参考，回归控制保持契约，G0/trace成立 | 简单复现器指导的一项prefill执行改变在native得到验证；支持这个阶段对这些案例的诊断价值与有限干预效果 | 唯一kernel原因、可移植普遍修复、提速或全分布losslessness |
| T1/N1匹配，但参考未恢复或只恢复部分 | 复现器对这项改变仍可预测；该候选不能完整解决既定差异。完整报告每个任务，允许有区分力的负结果 | 把部分恢复写成全cohort修复，按正例改主分母 |
| T1/N1不匹配 | 旧输入简化不能迁移到这项改变；新trace可能限定它失败的地方 | 旧72/72失效、所有target-only程序失败、proposal/history必需 |
| Scores/state变、IDs不变 | 在测试窗口和完整endpoint下的有限null | 没有数值敏感性或不存在其他checkpoint效应 |
| baseline/sham/state/instrumentation门失败 | 工程BLOCKED，主因不可识别 | 正式因果结论或绕过控制后继续追正结果 |

要构成论文里更强的闭环，不仅给数组相等：应展示一次可检查的“更少依赖的程序 → 已冻结的诊断候选 → native响应验证”过程，以及它排除了哪一个具体解释。没有计时对照就不声称节省调试时间；没有参考恢复就称诊断干预，不称bug fix。完整四案例与20控制表应进入新附录，主文给一个有完整条件和响应的实例。

## 7. 停止规则与稿件处理

只有一个候选prefill policy和固定任务集；完整保留positive、null、candidate failure与工程失败。工程门不通过即停止。正式结果出来后一次性评估是否增加了新知识，不重复修改实验直到模拟审稿给accept。

若结果不能区分prefill与后续state-history解释，保留这个限制；单块/common-continuation机制研究作为另一独立问题，不同时扩展。不得用persistent UB128 continuation解释单块因果。

v0.9.0仍为本轮固定复评对象。本方案、源码观察和未来可能结果均不写成v0.9.0既有证据。新的实验若最终成立，应进入后续版本，原数组与历史review保持原身份。当前B570/RTX/358H/M4旧campaign均为CLOSED。
