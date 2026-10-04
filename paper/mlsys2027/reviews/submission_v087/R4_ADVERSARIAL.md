# R4：对抗性主张审计与替代解释（HeteroSpec v0.8.7）

**评分：4/6（弱接收）。置信度：4/5。**

**问题等级：未发现 P0-V；没有本报告认定的 P0-C 阻断项；3 项 P1、2 项 P2。当前已写主张不需要新增模型执行。** 这是对有限范围的实证系统测量与诊断论文的判断，不以新算法、成功优化器、唯一数值机制或跨平台定律为接收前提。

## 阅读与核查范围

通读主文全部 12 个物理 PDF 页（10 页正文、2 页参考文献）和附录全部 14 页。实际视觉检查：主文物理页 **1、5、6、7、10**，附录物理页 **12、13、14**。主文、附录和匿名 CPU ZIP 的字节数及 SHA-256 均与 `FIXED_PACKET.json` 一致。没有阅读其他审稿、早期分数、作者 QA 或源稿，也没有编辑文稿。

另检查了允许的 `anonymous-evidence-index-v0.8.7.zip`：其 `python3 -B verify.py` 通过；并直接从导出的数组与计时字段另写计算，重算了 B570 H1 比较、fork 的实际决策字段、RTX V4 A/B 比较与 paired-prompt bootstrap、M4 Guard/Always 比值及 358H 条件成本上界。这里的独立性指我另算了匿名数据，不是独立 GPU 复现、原始绝对时间认证或遗漏二进制的核验。未取得、审计或运行正文所列完整 GPU 胶囊；不把附录第 14 页所述作者侧审计当作本人的工作。相关工作判断限于论文自己的处理，没有外部文献事实核验。

## 我理解的贡献

最有信息量的结果是 B570 上先选择、后冻结完整数组的 target-only UB1 预测：24 个保留提示的 72 次执行全部匹配 live，其中 4 个提示的 12 次执行偏离指定 UB128 参考。它把“这个数值路径曾出现分歧”推进为“这个已选路径假设可以在尚未看到 live 结果时预测全部 capped 输出”。RTX V4 则在同一组 19 个剩余、经 exposure 审计的提示上区分了预定候选：UB2 target-only 失败，proposal-conditioned replay 全匹配。

论文同时证明这类预测成功不等于严格参考资格，更不等于盈利：新的 RTX 三路径研究把 direct-ID gate 与自己的计时配对；serialization 合格但在记录的 instrumented post-prefill 边界内更慢。358H 给出固定进度与 target work 下的条件算术界；M4 对一个合格 Guard 的实验发现其没有超过固定 speculation 的 aggregate latency。这些结果组成有限且可检查的工程拒绝理由，而不是一套新解码算法。

## 主要优点

- **真正可失败的完整输出预测。** 主文第 5 页 §5.2、Figure 2，附录第 5–7 页 §J、Tables A6–A7 区分 hypothesis freeze 和 full-array freeze。四个非参考预测排除了只复制参考答案这一解释。72 次重复仍只有 24 个提示，论文没有把它们当成 72 个独立样本。
- **候选区分与工程 gate 没有混用。** 主文第 6 页 §5.3/Table 3 的预测比较，与第 7 页 §5.4/Table 4 的 reference qualification 是不同端点。RTX B 从自己的 fresh arrays 取得 gate，没有借历史 Figure 3 的资格来解释新计时。
- **负结果没有被包装为成功机制或优化。** 主文第 6–7 页明确约束 persistent fork、whole-path microbatch、logging 和固定成本界；第 9 页 Table 5 将 Guard/Always 标为 post-study secondary；第 10 页 §§9–10 没有推广到所有 target-only 程序、所有硬件或生产服务。

## 对抗性主张审计

| 被审计的有限主张及锚点 | 最强替代解释或反例方向 | 当前判断 |
|---|---|---|
| B570 UB1 在保留集预测 72/72，参考 60/72（主文 p5 §5.2；附录 p5–7 §J） | 共享 target 数值代码和一致的逐步执行可能足以解释成功；这不需要发现新数值机制。 | 解释成功来源的替代说法成立，但不反驳已经冻结的完整数组匹配。我重算得到 72/72、60/72。它只支持该路径/队列的经验充分性。 |
| RTX H2、fresh R_ONLY 为 57/57（主文 p6 §5.3；附录 p12–13 §§Q.2–Q.3） | 两套编排共享 llama.cpp/GGML/CUDA 数值例程；H2 tape 由 draft 和自己的历史反馈生成。 | 不能称独立数值实现或 draft-free 预测。论文已明确区分 application/API 编排独立与数值共享；共享内核本身不是当前主张的失效。匿名数组不能单独证明无输入泄漏，完整源代码/allowlist 是另一证据层。 |
| UB2 为 51/57，所以指定候选不足（主文 p6 §5.3；附录 p13 Table A18） | 未比较的 target-only 重分块、状态重建或其他执行策略仍可能匹配；history 也未被证明必要、最小或唯一。 | 这是对一个预定候选的有限反例，不能上升为 target-only 不可能性。摘要、§5.3、§6 和局限均遵守了这个界限。 |
| UB1 与 UB2 同为 51/57（同上） | 相同 aggregate 值可能掩盖不同失败提示，误导为两者预测相同。 | 不是相同预测器；正文已说明，数组核查也确认。应在 Table 3 更直接显示失败任务，属于 P1 可读性修复。 |
| B570 scores 改变，sampled immediate decisions 不变，later trajectories 18/72 不同（主文 p5–6 §5.2；附录 p6–7 §L、p10–11 §P.1） | 中位 margin 很大，数值变化未必触及决策边界；后续分支持续采用 UB128，而且 proposals 随分支历史变化。 | 我重算 216 score rows、195 reachable events 的 committed ID/acceptance/EOG 决策变化为 0；完整 continuation 18/72，涉及 6 个提示。后续差异不能归因于一次 fork，也不能解释旧 H1 四个提示；文稿已明确这一点。 |
| RTX serialization 57/57 合格但 0.677×（主文 p7 §5.4/Table 4；附录 p13 §Q.4） | instrumentation、condition-dependent logging 和整体 UB 配置可能决定计时；UB 也传播到 draft。 | 有效的结论是记录的完整配置在记录的 instrumented 边界内更慢，不能推出 target microbatch 的纯因果效应或无日志部署速度。我重算 GM=0.6773510334393157，CI≈[0.6616533074169813, 0.6918118724220993]，0/19 更快；这些限制正文已披露。 |
| 358H 零 draft/residual 仍不能 parity（主文 p7 §5.5；附录 p11–12 §P.3） | 更换 draft/proposals 或 target execution 可能改变 committed progress、rounds 和 target work。 | 当前主张固定这些量，代数界成立。我从 processed times 重算 CPU B/T=0.8274529834、NPU=0.8351858524。它不是 prompt-GM 界，也不是所有 draft 改进都不可能的结论。 |
| M4 Guard 没有超过 Always-Spec（主文 p9 §7.3/Table 5；附录 p10–11 §P.2） | 只在 2/60 提示上 target-only 更快，使这两个固定模式之间的 hindsight 机会很小；别的 switching policy 可能不同。 | 我重算 Guard/Always GM=1.027076，24 个 Guard 更快、36 个 Always 更快。该 post-study 比较不能证明任何控制策略都无用；论文只否定被测 Guard 的 aggregate 增益。 |

RTX 最关键的交叉关系可以用现有数组直接展示：

| 提示 | UB1 reference 对 live | Target-only UB2 对 live | H2 / R_ONLY 对 live |
|---|---|---|---|
| /15 | 不等，index 15：4199→9147 | 不等，index 15：4199→9147 | 均全等 |
| /18 | 不等，index 29：1191→3007 | 全等 | 均全等 |
| /25 | 全等 | 不等，index 4：271→1406 | 均全等 |
| 其余 16 个提示 | 全等 | 全等 | 均全等 |

三次重复中的结果一致。这个交叉关系比两个 51/57 数字更准确地传达 discriminator 的实际增量。

**披露不等于效度失败。** Exposure-conditioned selection、相关重复、匿名导出不能认证原始时间、原始二进制缺失、持续 continuation、共享数值内核和 instrumented timer 都是真实限制。但它们已经进入当前 estimand 或证据能力边界；本次没有找到它们与已经写下的有限中央结论冲突的实例。风扇/host policy amendment 也不作为腐败、接收阻断或重跑理由：附录 p13 §Q.2 保留了原 strict-host stop、预测记录及之后的 amendment，且没有声称已独立证明物理无影响。

## 具体问题与请求修改

**P1-1：增量知识的表达仍容易被“复现同一数值程序”解释吞没。** 主文 p1 贡献段、p7 §6、p10 §8 和附录 p5–6 §J/Table A6 使用 prediction、mechanism-validation、causal limits 等术语。最强替代解释是：预测器在同一数值栈上重建足够相近的执行路径，所以 full-array equality 本来就有希望成功。论文已经不声称唯一机制，但应把增量更明确地写成“预先选定并封存的路径假设在保留提示上受到逐 ID 检验；RTX 的某个看似对应 UB 配置却没有同样充分性”。建议将 §J/Table A6 的 mechanism-validation endpoint 改称 prospective path-prediction endpoint，并在贡献段直接点明这一可失败的差别。可用现有材料完成，不需要独立数值实现或新增解码器。其是否足够重要仍是主会门槛判断，不能靠改名解决。

**P1-2：B570 的 score 变化缺少同页的决策尺度。** 主文 p6 §5.2 给出 median absolute top-one delta 0.0695，而 raw margins 只在附录 p11 Table A14：UB1/UB128 中位约 17.5021/17.5128，最小约 0.2291/0.2003。这不是归一化概率，也不证明干预到了困难决策边界。建议在主文该段并列放入 margin 中位数/最小值，并将信息价值说清为“抽样状态的数值敏感性与即时决策稳定性”。当前没有宣称 near-boundary 强因果 null，因此是呈现修复，不是新增实验要求。

**P1-3：Table 3 仅显示 aggregate counts，最关键交叉差异要靠跨段阅读。** 主文 p6 Table 3 与附录 p13 Table A18。建议为 Table 3 增加失败提示列：UB2=/15,/25；reference=/15,/18；或加入上面的三提示交叉表。保留 Q/P 的比较器区分，不把 A 的 prediction gate 写成 B 的 qualification。这项修改只需要已经存在的结果。

**P2-1：记号和研究身份的阅读成本较高。** 主文 p2 §2.1 用 P 表示 prediction，而 p6 §5.3/附录 p7 §M 的 P 是 draft process；H1/H2、V2/V4、R_ONLY、Q/P 和多组 60/72、51/57 并存。建议统一用“P worker”或“draft worker”指进程，并在 Table 1 的研究行保留完整 comparator 名称。不要为了简短删掉现有有限范围。

**P2-2：amendment 可更具体，但不升级其后果。** 附录 p13 §Q.2 的“host-policy amendment”可直称风扇/host 运行策略 amendment，并保持原 strict-host stop 与 amendment 的区分。该建议仅帮助复现理解；不要求宣称物理无影响，不以此要求新预测、重跑或拒稿。

## Rubric A–E

**A．最强结果比回顾性观察多推断了什么？** B570 的 hypothesis 和 72 个完整输出数组先于 reserved live，任何一个后续 ID 错误都可以失败；成功且包含四个非参考提示，使结果不是“事后看见 mismatch”或“只预测参考”。RTX V4 进一步对同一集的预定竞争候选作有限区分。它们增加的是路径假设的经验预测充分性/不充分性，不是 history necessity、唯一原因或普适可迁移模型。

**B．有限范围内可以作哪些具体决定？** 不以能预测 B570 live 为由批准其严格参考替换；不把 RTX target-only UB2 当作这 19 个提示的完整预测器；RTX batching 不能作为该 reference 下的工作负载全局 lossless 替换，serialization 也不能作为被测边界内的 latency 优化；358H 只改 draft/residual、保持测得进度和 target work 时不能达到总时间 parity；在这次 M4 matched aggregate 中没有支持为增益加入被测 Guard 的证据。这些不是硬件采购建议或 production 结论。

**C．对已经写下的主张，是否有逻辑上必须的新执行？** **没有。** 没有发现当前有限结论依赖一个已经被反证、却仍被作者当成成立的前提。需要独立数值实现才能主张数值实现独立、需要新 target-only 候选才能扩大排除范围、需要 single-block restoration 才能归因单次 fork；论文没有写这些强主张。现有匿名材料不能认证绝对 chronology 是审查能力限制，不能被伪装成已证明的时间造假。

**D．能否只改现有材料？重要性还是否属于判断？** 能。上述 P1 的 endpoint 改称、score/margin 并列、失败任务交叉表，以及 P2 的记号与 amendment 澄清均不需要新数据。它们能使有限增量更容易被审查，但不能自动把本来很窄的经验增量变成更大的发现；主会重要性依然是实质判断。我认为 prospective full-trajectory discrimination 与同研究 qualification/cost 闭环的组合刚好超过弱接收门槛。

**E．本版本的阅读摩擦或无支持措辞？** 主要是重复的研究身份、同数不同 cohort/comparator、P 的双重角色，以及 mechanism-validation 容易被读成 mechanism identification。核心段落已经反复限制唯一原因与必要性，我没有发现需要 P0-V 定性的泛化措辞。所检查页面没有截断、遮挡或公式错误；附录 p13 的 GM 公式确实含 1/19，文本提取漏掉分母不能算论文错误。

## 问题与实验必要性

非阻断的作者问题：

1. 是否同意把主贡献中的“机制”表述收敛为“可失败的执行路径预测与候选区分”，并说明其对研究者的用途，而不把共享栈上的复现成功称为新的数值规律？
2. 能否将当前 Figure/Table 的结果交叉关系与 margin 尺度直接放入主文，使读者不需要从附录重新拼接才能评估 discriminator 和 sampled null 的力度？
3. 完整 replay capsule 中，哪一个已存在的源码入口/allowlist 检查最直接支持“未来答案不进入 R inputs”？建议在 §Q.2 或 INDEX 的能力说明中指向它；不要求用数组相等证明输入隔离。

**必须的新增实验：无。**

可选的更强主张实验，均不作为本次接收条件：

- 若以后要声称 history 必要，增加预先定义的 target-only 执行/状态候选和消融；本次 UB2 失败不够排除所有这类程序。
- 若以后要归因 sampled block 的后续因果作用，做干预后恢复共同 UB 策略的 single-block 设计，并可取更多决策位置；当前 persistent continuation 已正确限定。
- 若以后要提供 deployment latency 或跨 session 结论，再测对应无日志/部署边界和独立 session。当前 instrumented 0.677× 不依赖这类扩展实验。

## 最强接收与拒稿理由

**最强接收理由：** 这不是单纯列举 slowdown 或 argmax sensitivity。它给出预先封存的完整 trajectory 预测、能否替换参考的独立 gate、同 cohort 的竞争候选区分，以及自己的 qualified cost 结果。B570 的四个非参考预测与 RTX UB2 的两个失败提示都是具体可证伪知识；负结果对限定实现提供了可执行的停止/选择理由。共享数值内核、persistent continuation 和 instrumented timing 不被隐藏，结论没有越过这些能力。

**最强拒稿理由：** 按论文自己的相关工作处理，batch-shape 数值敏感性、完整成本核算、correctness gating 和 adaptive control 已存在。新的主要经验结果仍可以由同栈程序的数值路径相似性解释；它没有揭示可跨实现操作的 causal mechanism，没有提供快且合格的 RTX 路径，也没有控制收益。有效独立提示数小且 exposure-conditioned，很多辅证只是保护解释边界。若主会要求更可迁移的新知识，这可能仍是扎实但增量不足的案例集。这个拒稿理由是 **significance**，不是把未声称的 necessity、生产速度或新算法硬塞成效度前提。

**最终理由：** 我给弱接收而非强接收。现有 finite predictive discrimination 与 matched qualification/cost 组合有足够系统研究价值，且没有发现中央有限主张的实际反例。三项 P1 应以现有证据完成；如果委员会对这种有界经验增量的主会价值持更高门槛，拒稿也应明确落在重要性判断，而不是要求重跑风扇 amendment、唯一内核解释或独立数值实现来修复一个并不存在的已写主张。
