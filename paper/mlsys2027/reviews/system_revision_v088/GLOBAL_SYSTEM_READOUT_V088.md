# v0.8.8 全局系统分析

结论：本稿最强的信息增量是对执行描述的前瞻判别，而不是再次发现数值敏感性、再次设置正确性门或报告硬件快慢。工程资格失败已经能够否决部署；新增预测结果回答的是“哪种描述能够在 live 之前预报这个失败路径的全部输出”。成本和策略结果随后约束哪些优化方向还有根据。

## 信息增量与决策边界

| 问题 | 已有门或基线已经说明 | 本稿额外说明 | 能作出的选择 | 不能推出 |
|---|---|---|---|---|
| B570 执行描述 | UB128 reference/live 60/72，路径不能作严格替代 | 预冻结 target-only UB1 无 draft/proposal 输入仍预测 72/72 完整 128-ID 轨迹，包含四个非参考提示 | 保留该 target-only 程序作为此路径上经验充分的描述；不改变部署否决 | native drafting 因果无关、唯一 kernel 原因、所有路径只需 UB1 |
| B570 状态干预 | 数值路径可能影响输出 | 新队列 72/72 score 变、0/72 即时变化，后续 18/72 变化发生在持续 UB128 策略下 | 将 sampled numerical sensitivity 与即时稳定分开；维持有限预测贡献 | 单块造成延迟变化、近边界 witness、解释原 H1 四提示 |
| RTX 候选判别 | reference/live 51/57，native batching 不兼容 | UB2/live 51/57 的失败任务不同；H2/R_ONLY 57/57 | 否证这个指定容量级 UB2 程序，保留成功的更丰富 replay 描述 | 所有 target-only 程序失败、proposal/history 必要或最小、独立数值实现 |
| RTX 资格和成本 | 跨研究门与历史时延不能形成 tradeoff | 同组提示、171 新测量内 batching blocked，serialization qualified 但慢 | 排除被测 instrumented serialization 作为延迟优化；不为 batching 作合格速度估计 | 无日志生产部署慢、能源或吞吐结论、旧 0.646 到新 0.677 的趋势 |
| 358H 优化预算 | CPU/NPU 两合格接口都慢于 target | 固定 progress/target work/baseline 下，即便 draft+residual 为零，上界只有 0.8275/0.8352 | 单改 draft 或 replay 无法达到该前提下的 parity；需改变前提并重过资格 | 任意新 target/proposal 配置的上界、一般 NPU 弱、已测得 persistence 收益 |
| M4 控制机会 | Guard 与 Always 均 180/180 exact、均快于 target | Guard/Always 1.0271 [1.0130,1.0436]；Always/两模式 oracle 1.0007 | 此测量中 fixed speculation 更好；fallback 活跃不能证明收益 | 所有切换策略不能改进、oracle 可在线达到、策略普遍不必要 |

这里新增的是诊断选择与设计约束，不是新的部署许可。B570 说明一个简化描述可成功；RTX 指定简化描述被同集反例否证；两者不能读成同一预测器跨 backend 转移。严格资格、有效描述与可获成本收益均须单独建立。

## 本轮既有记录分析

V4 B 原来的 171 条 QPC 端点，先按 19 个 prompt × 3 个 condition 各取三次中位数，再按这 19 个中位数计算线性分位数。单位秒；这些是观测分布，不是 CI：

| 条件 | min | Q25 | median | Q75 | max |
|---|---:|---:|---:|---:|---:|
| Target UB1 | 0.532 | 1.441 | 1.607 | 2.396 | 2.920 |
| Batched UB2（blocked，诊断） | 0.641 | 1.730 | 1.910 | 2.953 | 3.248 |
| Serialized UB1 | 0.843 | 2.074 | 2.332 | 3.611 | 4.102 |

配对 prompt-median GM 仍是 0.6773510334393157，原 CI [0.6616533074169813,0.6918118724220992]、10,000 次、seed 2026100204、任务顺序全部保留。不能用上表中位数相除替换这个估计；blocked batching 的速度/CI 仍为空。独立 NumPy 实现从原 B start/end QPC 端点计算，15 个描述量差异为零。

RTX 交叉失败：/15 两者均失败；/18 仅 UB1 reference 失败；/25 仅 UB2 失败。两种 replay 全部匹配。这将同为 51/57 的两个结果区分开，而非只重复分母。

Bootstrap 重采样的是已选曝光队列中经验 prompt rows，条件于已观测各条件中位数和冻结配置。它不建模曝光选择过程，也不是 HumanEval 总体、全会话或新温度状态保证。A/B 同组提示，不构成两份独立推广证据。

## 更高层次展望

后续系统研究应先明确有效执行描述及输出参考，再识别允许改变的成本前提，而不是从设备标签、UB 参数名或高 isolated draft throughput 直接推断可优化性。成功 replay 是一种复现描述；共享数值例程限制其独立性。358H 的负结果约束的是固定 target/progress 下的优化预算，M4 的负结果约束的是已测两种模式中的控制机会。它们提示架构和研究问题的优先级，但没有测得新的实现收益。

本轮通过全局重构回应贡献意见；有限模型、少量真正区分任务、共享例程和条件化队列仍限制主轨意义。编辑和数据复算不能证明会议接收，也不能把原 5 份弱接收视角改写成新版本共识。

## 实验决定

本轮不增加 B570 或其他模型执行。现有主张不把持续策略下的后续差异归因于单块，故 single-block/common-policy 对照不是维持当前结论的必要项。只有将目标明确改成更强的单块因果贡献时，才需另定有界协议；不能预设 positive witness，更不做 dense scan。RTX/358H/M4 保持 CLOSED。
