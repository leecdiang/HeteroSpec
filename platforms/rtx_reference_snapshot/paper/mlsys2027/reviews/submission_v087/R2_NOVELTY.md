# R2：新颖性、最近先行工作与 MLSys 主研究轨意义

**版本：v0.8.7。总分：4/6（Weak Accept）；置信度：4/5。**

我的判断是边界性的弱接收。论文增加了可证伪的有限系统知识：B570 上，一个不执行 draft 的具体 target-only 路径，事先预测了保留提示的完整 speculative 输出，连参考不相容的续写也正确；RTX 上，原先跨队列的比较被同集候选区分取代，指定 UB2 候选失败而两个 proposal-conditioned replay 成功；同集的新三条件成本实验随后证明，参考相容性并没有提供合格的加速路径。这些不是一个新的浮点现象，也不是新控制算法，但合起来略过了我对实证测量/诊断论文的主轨接收门槛。最接近先行工作的重叠很大，文章需要把增量的有限性与实际价值讲得更集中。

## 阅读范围与独立性

完整阅读固定输入的 `main.txt` 与 `appendix.txt`，包括主文全部 12 个物理页（10 页正文、2 页参考文献）和附录全部 14 个物理页。实际 PDF 的页数和内容优先于 rubric 顶部遗留的“v0.8.6 / 附录12页”描述。阅读了 `REVIEW_RUBRIC.md` 与 `FIXED_PACKET.json`，没有读取旧评分、作者 QA/handover、其他评审、论文源码或非指定科学包；没有改动论文，也没有运行模型或离线科学验证器。

实际目视检查的现有渲染图像：主文物理页 **5、6、7、9、10**；附录物理页 **6、11、13、14**。因此我检查了 Figure 2/3、Table 3/4/5、B570 冻结记录、RTX V4 区分与成本定义以及证据入口的实际排版，而没有宣称逐页目视检查全部图像。

外部检索仅依据下列原始论文页面，不把搜索结果中的媒体、社交网页或作者主页用作科学依据。检索日期为 2026-10-02。初次直接打开部分 arXiv abstract 地址失败，随后用检索得到的 arXiv HTML 成功读取；并非据失败页面推测论文内容。

| 原始来源与 URL | 本评审实际检索/阅读范围 | 对本稿新颖性的作用 |
|---|---|---|
| Chordiya, *Lossless but Not Free*, arXiv:2607.17283v1，[原始HTML](https://arxiv.org/html/2607.17283v1) | HTML 第55–98行、123–283行中工具返回的连续正文：摘要/引言、§3.2、§4、§5、§6.1–6.5、§7开头；未阅读论文全部参考文献或运行其代码 | 最近的消费者硬件实证先行工作，直接核查本稿对其测量、门控与 batch-shape argmax 现象的表述 |
| Gond 等，*LLM-42*, arXiv:2601.17768v2，[原始HTML](https://arxiv.org/html/2601.17768v2) | abstract 页面；HTML 第43–231行中工具返回的正文：摘要、§1–4.4、§5开头；未全面审计§5评测 | 核查既有的 shape-consistent 数值执行、固定形状 replay/rollback 与 KV 修复思想 |
| Yuan 等，*Understanding and Mitigating Numerical Sources of Nondeterminism in LLM Inference*, arXiv:2506.09501v2，[原始HTML](https://arxiv.org/html/2506.09501v2) | HTML 第45–96行：摘要、§1、§2.1–2.2开头；未全面审计后续实验/LayerCast实现 | 确认配置/精度变化导致 greedy 输出与长续写变化已是先行知识 |
| Zhang 等，*Correctness Forensics for Batch Speculative Decoding*, arXiv:2510.22876v4，[原始HTML](https://arxiv.org/html/2510.22876v4) | HTML 第67–109行、第121–125行、第228–276行以及工具 find 返回的少量附录段落：摘要/引言、架构边界、§4.2数值control/部分§4.3；未全面审计证明或全部附录 | 核查同步错误与剩余数值不相容、严格输出对照和成本诊断的先行工作 |

没有对本稿所有异构/自适应参考文献进行外部事实验证，也不据此宣称穷尽先行工作或证明“全球首次”。下文对未单独检索的参考文献仅评价本稿§8的处理。

## 我理解的贡献与五个评审轴

| 固定评审轴 | 评价 |
|---|---|
| 1. 有限科学有效性：队列、参考、输入、终点、比较器、estimand | 较强。主文页2§2.1区分 H/Q/P；页3 Table 1与§3明确队列、首个inclusive EOG/cap128和prompt统计单位；页5–7把 prediction、qualification、cost分开。未发现推翻当前中心有限结论的已证实错误。 |
| 2. 超越既有数值路径敏感性与完整成本测量的增量 | 中等且窄。新增的是预先冻结的完整非参考轨迹预测、同集候选失败/成功区分、同条件qualification/cost闭环；不是数值敏感性、门控、成本恒等式或adaptive control本身。 |
| 3. 有界工程后果 | 明确。对指定参考阻止不相容替换；对测量边界拒绝较慢串行实现；358H固定progress/target work下不能只节约draft；M4此规则不优于固定speculation。 |
| 4. 可检查性与前瞻顺序 | PDF提供清楚的冻结角色、输入契约、完整终点和匿名入口。它报告了顺序，却不能独立认证原绝对时间或缺失的二进制；本文明确承认这一点。我未运行artifact，因此不把作者侧audit当成本评审复现。 |
| 5. 整体连贯性与可读性 | 改善空间较大。结果边界通常写得准确，但历史campaign、H1/V2/V4、fork、成本与两种runtime研究相互穿插，重复免责声明占据很多主文空间。核心证据可以更早、更集中。 |

## 最近先行工作：重叠与真正增量

本稿主文页9–10§8对 Chordiya 的描述与我所读原文相符：该工作已经测量消费者 Apple silicon 多种backend组合的获益与减速，分解成本，诊断小验证批次未有效并行；§6.1还在没有speculative machinery的 target-only 计算中观察到 batch shape 改变logits并翻转argmax。故“消费者硬件会减速”“greedy exactness不能从算法保证直接继承”“验证并行性必须实际量测”不能成为本稿独有贡献。原始依据：[Lossless but Not Free §5–6.5](https://arxiv.org/html/2607.17283v1)。

Yuan 的已读部分已把precision、batch size、GPU配置与greedy响应/续写变化联系起来；Zhang 的已读部分把输出检查、同步错误与剩余数值偏差分开。本稿承认这些背景，而没有把所有reference mismatch都指控成decoder bug，这一点是恰当的。原始依据：[Yuan 摘要/§1–2](https://arxiv.org/html/2506.09501v2)、[Correctness Forensics §1/4.2](https://arxiv.org/html/2510.22876v4)。

LLM-42更接近“执行路径与完整状态”的思想邻域：已读§3–4利用形状一致的执行和验证/回滚，并强调只修token而不修KV可能留下后续不一致。它是在构造确定性输出；本稿是在预测/诊断指定native speculative路径，成功预测的路径仍可能不满足冻结reference。两者目标不同，但本稿应更具体交代这层关系，不能只用“verified speculation”一语带过。原始依据：[LLM-42 §3–4](https://arxiv.org/html/2601.17768v2)。

真正增加的知识是“一个已从discovery选定的具体路径，是否能在live未知时预测每一个后续ID”，而非“两个已知序列是否不同”。B570的UB1 predictor不含draft/proposal输入；旧观察本身并不推出它会重现extra verification、rollback及长期续写之后的全部native输出。主文页5 Figure 2、§5.2与附录页5–7§J/Table A6–A7记录了这个可失败测试。共享runtime并不抹除实证预测增量，但会限制其实现独立性和适用范围。

RTX V4的增量进一步是一个同集、预定义候选的反例：UB2 target-only在/25和/15失败，而UB1 reference在/15和/18失败；两个replay成功，不能把相同51/57总数当成同一预测。主文页6 Table 3/§5.3、附录页13 Table A18/§Q.3对此写得清楚。不过仅相同“UB2”选项不保证target-only的每次实际forward shape与speculative验证调用相同。因此这是对所指定粗粒度候选的有价值否证，尚不是执行历史一般必要性的发现。本稿当前没有犯后一种推断错误。

## 强项

1. **最强结果确实具有前瞻可证伪性。** B570先用12个暴露discovery提示选择H1，然后冻结保留任务与72个完整预测，再执行live。四个参考分歧提示的12个重复都被正确预测，排除了仅照抄reference的解释。有效任务数为24，并非72个独立提示；结果为cap128内完整数组，不是无限生成保证。（主文页1、5 Figure 2/§5.2；附录页5–7§J/Table A6–A7。）
2. **RTX区分了指定解释，并修复了原先同集比较缺位。** V4全用剩余19个暴露审计合格提示，UB2/live 51/57、H2/live及R_ONLY/live 57/57；参考不同的两条轨迹也成功预测。proposal tape依赖H2自己的既往feedback，fresh replay自行作决定，native live不导入tape。应用/API编排独立与共享数值库的边界没有混淆。（主文页6§5.3；附录页7–10§M/§N.1、页12–13§Q。）
3. **新成本闭环没有借用旧qualification。** 相同19提示的新171次三条件执行共享timer、endpoint及平衡顺序；batched直接ID被阻止，serialized直接ID合格却只有0.677×[0.662,0.692]速度比，0/19提示更快。该结论为instrumented post-prefill边界，日志开销未独立去除，当前措辞没有把它升级为deployment或throughput结论。（主文页7 Table 4/§5.4；附录页13§Q.4。）
4. **负结果产生可操作约束。** 358H在固定进度/target work条件下给出0.8275/0.8352的零draft/residual总时间上界；M4 Guard的合格正target-relative结果与负Always-relative结果并列。它们不是新理论，但比只报告“draft快/acceptance高”更能约束实现选择。（主文页7§5.5、页9 Table 5/§7.3；附录页11–12§P.2–P.3。）
5. **因果节制较好。** B570同状态fork的scores全部改变却0/72即时决策改变；持续UB128续写的18/72差异不被归因于单个采样block，也不用于解释原四个H1提示。RTX失败也只否决UB2候选。（主文页5–6§5.2、页10§9；附录页6–8§L、页10–11§P.1。）

## 问题、优先级与具体修改

**P0-V：未发现。** 没有在已读固定材料中找到一个已经失败、却被中心结论依赖的前提。host-policy/fan amendment按用户指定不作为有效性阻断或重跑理由；附录页13§Q.2保留原stop与修订、说明native live之前授权和封存。我的结论不假定该host改变的物理影响已被证明为零。

**P0-C：主轨重要性处在边界，属于判断，不是数据损坏。** 最强预测结果只有一个B570 stack的24个提示，其中真正区分reference的提示为4个；RTX新同集有19提示、2个UB2失败，且replay共享数值例程。工程决策主要服务这套指定Qwen3/llama.cpp实现。相较最近消费者硬件论文和数值路径工作，读者可能认为这仍是细致验证已有思路而非足够重要的新系统知识。我的投票认为“非参考全轨迹事前预测 + 相同队列候选失败 + 合格成本闭环”已经略足够；另一位评审以同样有限结果投弱拒绝也有合理的显著性理由。没有理由把此争议改写成必须发明算法、定位唯一kernel或证明普遍因果。

**P1-1：把最近先行工作的增量变成一个可扫读比较。** 在主文页9–10§8或页2贡献段，用小表列出最近的Lossless、数值配置工作、LLM-42、本稿各自问的是观察敏感性、构造确定性、事前整轨迹预测还是同集qualification/cost；标明本稿最强支持规模及共享数值routine。保留“数值路径依赖不是新现象”的承认，明确全轨迹冻结协议是证据增量而非算法创新。完全可从现有材料和引用完成。

**P1-2：更具体解释UB2候选为何是有意义但有限的比较器。** 主文页6§5.3目前给出参数和结果，却较少解释候选对应的实际执行假说。用现有代码/已有trace说明target-only UB2与proposal-conditioned UB2的调用输入、实际分组与状态经历何处对应、何处不同；没有已留存记录的字段可以明确标为未知。不要用这个建议要求新模型执行。紧贴Table 3说明“parameter-level候选不足”，防止读者将结果读成history必要性的机制证明。

**P1-3：集中呈现核心结果，压缩历史campaign与重复限定。** 主文页4–7§4–5保留很多旧成本、旧资格、旧V2和新V4数字；页6 Figure 3仍占较大版面，虽caption清楚，但它是明确不匹配的两幅panel，容易分散对Table 3/4的注意。可把V4的同集预测/资格/成本先成组呈现，历史proxy和失败历史移到紧凑背景或附录。保留H/Q/P与计时边界，不必每段重复全部禁止推论。

**P1-4：术语与证据入口修整。** 主文页5§5.2和页7§6的“this B570 stack / path sufficiency”虽被上下文限制，宜改成“this tested cohort and frozen path”；“independent”首次出现即同时写出应用编排独立、数值例程共享。附录页10§O称H2摘要“full filename digest above”，但可见前文不是就近提供完整文件名；真正入口在页11 Table A13。用明确交叉引用消除检索摩擦。rubric的旧页数是评审包元数据问题，不是论文科学错误。

**P2：可选加强。** 跨模型/更长cap、第二session、更多候选shape、无日志部署计时、分离replay/proposal成本或新policy都能增加外部意义，却不是当前有限结论的逻辑前提。新的单block恢复实验可支持更强因果问题；当前持续policy结果没有声称回答该问题。

## 固定 rubric A–E

**A. 最强结果比回顾观察增加了什么科学推论？**

增加“已指定target-only路径在保留输入上足以预测native speculative的完整capped轨迹”的经验支持。它不仅预测是否分歧和首差位置，还预测四个非reference提示的后续所有ID。任何后续ID错误都能失败，且预测已在live之前固定。因此它超越“某些logits/argmax会变”。但这种有限经验充分性不等于底层机制必要性、独立数值实现、未来输入保证或reference资格。

**B. 有界范围内有什么具体决策？**

| 结果 | 支持的具体决策 | 不支持的升级 |
|---|---|---|
| B570预测成功，reference/live 60/72 | 可以用此固定UB1路径重现/预测所测native轨迹；不能将该路径用作冻结UB128 reference的lossless替代 | 无全硬件/未来输入保证，无唯一数值原因 |
| RTX UB2 51/57、replay 57/57 | 拒绝所指定target-only UB2候选在该队列的全轨迹充分性；保留proposal-conditioned replay作为该路径复现工具 | 无history必要性、最小性或任意target-only候选不可能性 |
| RTX三条件cost | batched不能以当前严格reference合同入选；合格serialized在该仪器边界不值得作为latency优化 | 无production、无日志latency、throughput或energy结论 |
| 358H条件上界 | 固定progress/target work时只削减draft/residual仍不够，须改变这些固定量才可能达parity | 无改变target/proposals后上界，无NPU不能持久化的一般结论 |
| M4 Guard比Always慢，Always/oracle≈1.0007 | 对这组已测固定模式，Guard无aggregate增量价值，不宜以fallback活动证明收益 | 无所有switching policy失败或迁移风险降低结论 |

**C. 当前书面主张是否逻辑上必须有新执行？**

否。未识别需要新执行补齐的已失败中心前提。V4已有同集指定竞争者和fresh三路径cost；B570已有前瞻完整数组；即时fork与持久续写分开；成本和上界的条件公开。缺少普遍因果或生产bench只限制更强主张。fan-policy修订不产生本评审要求的rerun。若作者将结论升级为无日志部署速度、跨栈规则、history必要性或单block因果恢复，才需要对应的新证据；当前并未这样写。

**D. 现有材料修改能否够用？重要性仍是判断吗？**

可以。P1的先行工作比较、候选执行假说解释、结果次序与准确交叉引用都不依赖新执行。它们会让现有有限增量更易审查，但不能改变样本/实现范围；主轨重要性仍是评审判断，而不是再堆任务就可自动解决。我目前接受该有限增量。

**E. 本版本的阅读摩擦或无支持措辞？**

主要摩擦是多campaign和证据角色的编排、反复重复边界、页6大图的两幅不匹配证据相邻以及附录§O入口远距。主文整体已经避免了核心无支持的history必要性、唯一kernel、hardware排名和production加速措辞。最需要预防的是“path sufficiency / independent”被抽离上下文后的过强阅读；这是P1表述修整，而非P0-V。

## 必要与可选实验、澄清问题

**接收现有有限主张所必需的新实验：无。** 也不要求以fan-policy为由重跑。现有数据/代码说明与论文重组足以落实上述修改。

可选优先级：若作者希望提高一般意义，可先在另一模型或新session重复冻结prediction协议；若希望解释RTX为何需要更多输入，可测试更细的实际shape/state匹配候选，但结果只能逐一排除候选；若希望推荐部署，才测无日志路径/production latency。不要同时把这些全部当成接收条件。

给作者的问题均可优先用现有材料回答：

1. RTX target-only UB2候选对应怎样的实际forward分组/状态轨迹假说？与H2/native的差别已有多少代码或trace可以直接展示？
2. 除此论文实验之外，读者复用B570预测器或RTX replay诊断时，最小需要固定哪些输入、reference及runtime字段？可否给一份现有记录支持的简短执行清单？
3. 是否同意将新V4预测与cost作为一个主文证据组，并把不匹配的历史proxy图降为背景，从而使论文的增量不被旧观察淹没？

## 最强接收与拒绝论据、最终理由

**最强接收论据：** 论文把常见的“数值会变、测全成本”转化为几个真正可失败的系统判断：事前预测非reference完整轨迹、用同集候选明确失败边界、在同一cost研究内联合门控与计时、用条件上界和固定模式oracle约束无效优化方向。它认真保存负结果，当前主要陈述没有逃出证据边界。对实证系统研究而言，不需要正面算法胜利也能贡献有用知识。

**最强拒绝论据：** 最近先行工作已覆盖消费者backend减速、数值shape敏感性、output gate和cost decomposition；LLM-42也把shape/state与验证联系起来。本稿独特部分仍是单模型家族、极少真正区分案例、共享数值实现中的候选验证；具体工程决策可能只对指定集成有价值。评审可以据此认为增量不足以占MLSys主轨篇幅。这是**P0-C显著性判断**，不能冒充错误数据或缺失普遍机制。

我最终给 **4/6、置信4/5**。理由是完整事前轨迹预测与RTX同集区分/成本闭环相加，达到有限但真实的新系统知识；我不会以缺少新decoder、唯一数值根因或跨栈规律拒绝该类型论文。重要性在边界、写作需集中，但当前无需新模型执行来维护其实际书面中心结论。
