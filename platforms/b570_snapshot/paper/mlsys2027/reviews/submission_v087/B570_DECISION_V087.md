# B570 决策：先完成现有材料修订，本轮不执行

**当前决定：不补 B570，不扩 dense all-block scan。** v0.8.7 已完成 RTX A+B 整合和六视角投稿级评审。全部报告均认为现有有限主张不需要新执行；R1 的弱拒绝针对系统重要性，其他五份弱接收也保留这一风险。补一个实验不能预设提高评分。

## 当前证据与尚未提出的强主张

- 原 H1：draft-free target-only UB1 预冻结预测在 24 个 reserved prompts × 3 上为 72/72；reference/live 60/72。这个结论是 tested-path/cohort predictive sufficiency，资格仍 blocked。
- 另一个 24-prompt fork cohort：scores 72/72 改变，raw top-1 和 sampled immediate decisions 0/72 改变；persistent UB128 continuation 的完整轨迹 18/72 改变，涉及 6 个提示。
- 论文已明确 persistent continuation 不只干预一个 block，不能把后续差异归因于该块，也不能借它解释原 H1 四个参考分歧提示。

因此 single-block/common-policy study 会回答一个**新且更强的问题**，不是现有有效性欠账。先完成贡献聚焦、交叉失败、绝对成本尺度与术语／入口修订，更直接回应本轮意见。

## 将来值得重新考虑的触发条件

只有作者明确希望提出下面的有限因果命题，且它能具体回应修改后仍存在的机制价值问题时，才准备新协议：

> 在固定 checkpoint，改变一个 verification block 的执行 partition 后，让两分支恢复同一后续策略，是否足以改变即时决定或后续完整轨迹？

这不是批准执行。需要独立的 PREPARE_ONLY 协议与工程证据，经审查后再执行。不要把它自动纳入当前 PR、重开旧 campaign 或改旧数组。

## 有界设计必须解决的语义

1. 固定可审核的 checkpoint/任务/分母/端点/重复数，说明这是既有曝光案例的 confirmatory intervention 还是新的 exposure-audited cohort；不把已见案例伪装成 unseen prediction。
2. 从同一个已检查的 prefix、KV、位置、proposal 和 sampler 状态分叉；同 partition R0 恢复控制必须先过工程门。
3. 只让指定 verification block 的 partition 不同，随后两分支使用同一明确的 execution policy。需要保留各自干预产生的状态；不要把 alternate state 覆盖成 primary state而抹掉效应。
4. common policy 不等于未来 proposals/输入字节被强制相同。若干预使历史变化，后续 live drafting 可以跟随各自历史；那属于这次干预的后果。不得同时改变下一块及以后 UB 设置。若要测试固定 tape，则另设具名、预定的控制，不能混称 native continuation。
5. 在结果前固定即时 ID／acceptance/correction/bonus／endpoint、首差位置和完整 trajectory 的判据；score、state bytes 和 discrete decisions 分开。opaque sampler state 无法序列化时明确源码／clone 控制的能力上限。
6. 结果分支预定：score change 但全程 ID 相同是 bounded null；即时差异是局部 witness；即时相同但 common-policy 后有差异只在 R0/恢复/状态控制成立时支持有限的后续因果效果。不能自动命名唯一 numerical cause。
7. 所有零效应、失败工程门和未完成状态保留；禁止按 outcome 加 checkpoints/prompts、搜索到正结果才停或改 continuation。

## 为什么不建议现在立即执行

该设计消除 persistent-policy 混杂，有独立科学价值；但可能得到全部 null，也可能只在少量既见任务得到 witness，均不能保证解决主轨的重要性争议。它也不会解除 B570 reference qualification、扩展 RTX target-only 排除范围或提供 production 性能证据。本轮审稿的具体 P1 请求全部可以使用已有材料处理。

建议保留其为一项可选择的后续科学目标。现阶段实验 CLOSED；本次没有新增 GPU/model inference。dense scan、更多 backend、358H persistence、M4 controller variants 继续不执行。
