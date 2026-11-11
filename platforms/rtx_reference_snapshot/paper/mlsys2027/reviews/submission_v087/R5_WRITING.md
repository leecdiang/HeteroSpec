# R5 独立审稿：叙事、清晰度、阅读成本与呈现

**稿件：HeteroSpec v0.8.7。评分：4/6（弱接收）；信心：4/5。**

本评分依据冻结稿件本身，未读取以往评分、其他审稿报告、作者 QA 或原始审计报告。把论文视为有限范围的实证系统测量与诊断研究；负结果可以构成贡献，不要求新解码算法、成功优化器或唯一数值根因。

## 阅读与检查范围

- 已完整阅读指定的 `REVIEW_RUBRIC.md`、`FIXED_PACKET.json`、`main.txt` 与 `appendix.txt`。
- 已逐页查看正文物理页 1–12、附录物理页 1–14 的全部 PNG，均来自指定 `input/render/`；正文第 11–12 页为参考文献。
- 对指定两份 PDF 读取页数并核对 SHA-256，均与冻结包一致。附录实际为 14 页；rubric 中旧的页数描述未用来限定阅读范围。
- 以下页码均为**物理 PDF 页码**，正文与附录分别计数。未执行证据包验证程序或模型，未对外部文献事实进行独立核验；文献判断仅依据论文的相关工作处理。
- 依冻结评审要求，已披露的主机／风扇策略修订不是阻断项或重跑理由，也不据此推断其物理影响已经被独立排除。

## 我理解的贡献与整体判断

论文最有价值的主张是把三个容易混淆的问题拆开：能否在 live 结果出现前预测完整输出、该输出是否兼容指定参照、兼容执行是否真的降低所测成本。

B570 的 draft-free UB1 候选在 discovery 后选定，再先冻结完整数组，最后预测 24 个保留提示的 72 次 live 序列。72/72 命中包括四个参照不一致的提示，而同集 UB128 参照仅 60/72 相等。因此，这不是事后给 mismatch 命名，也不只是复述参照输出：一个可被任意后续 token 推翻的执行路径候选在有限新样本上成功预测了非参照轨迹。它仍不能作为保持参照 ID 的优化路径。

RTX V4 增加了更直接的同集鉴别：相同 19 个提示上，target-only UB2 仅匹配 51/57，而两个 proposal-conditioned replay 程序匹配 57/57。随后 B 臂在相同提示上重新执行三种配置的 171 个成本观测，直接判定 batching 不兼容、serialization 兼容但在 instrumented post-prefill 边界内较慢。这将候选预测与可部署替换的资格／成本联系起来，是本版本最完整的一组证据。

358H 的固定进度／target work 条件上界，以及 M4 Guard 输给固定 speculation 的配对负结果，提供两个补充工程结论。其知识增量不大到足以消除主会场价值的争议，但足以让我倾向弱接收。当前最突出的问题是**论文按历史研究积累的顺序呈现过多材料，使最强结果到正文第 5–7 页才展开**，而非有限主张中已证明的科学错误。

## 主要优点

1. **第一页能找到实际结果和核心区别。** 标题准确反映 qualification 与 realized costs，未许诺新算法或普遍加速。摘要与引言（正文第 1 页）明确给出 B570 的预先冻结预测、RTX 同集鉴别和序列化负成本结果，并以 predictable / reference-compatible / profitable 三者的区别收束。读者无需猜作者把负结果当作什么贡献。
2. **关键端点定义很有用。** 第 2 页 §2.1 明确 H、Q、P 各自比较什么；完整数组包括长度和首个 EOG／cap，且不等于功能正确性。这些区别后续基本保持一致。
3. **新增 RTX A+B 的整合是实质性的。** 第 6 页 §5.3、表 3 解决同一保留集缺少 target-only 对照的问题；第 7 页 §5.4、表 4 解决 gate 与成本来自不同研究的问题。B 的观察是 fresh，A/B 共用提示而非独立 cohort，UB 配置同时作用于 draft 这一点也写明。没有把旧 90/90 gate 借给新计时。
4. **负结果的决策含义有足够约束。** 第 7 页 §5.5 的零 draft／residual 上界明确固定 progress、target work 和 baseline；第 9 页 §7.3 不把 fallback 活跃度等同于有益决策，并直接报告 Guard/Always 的次要配对分析。
5. **版面总体可读。** 正文全部页与附录全部页未见文字截断、表格越界、遮挡或不可辨识图例。表 3/4 的数字、列名与行关系清楚；图 4 直观地区分 isolated draft 机会与完整接口成本。

## 分级问题与精确修改请求

### P0-V：未发现

在本次限定的 PDF／文本检查中，未发现足以推翻书面中心有限结论的已证明错误。没有把 57 个重复观测当作 57 个独立提示、把预测一致当作参照资格、把 persistent UB128 continuation 当作单块因果效应，或把固定算术上界当作优化实验。匿名 PDF 不能独立认证原始绝对时间、共享数值例程不等于独立数值实现，这些均已披露，不能仅因披露而称为数据损坏。

### P0-C：我不设当前接收阻断项；意义判断仍有真实分歧

最强反对意见是：主要新知识局限于少数 consumer stack、四个 B570 与两个 RTX 的参照分歧提示；replay 使用相同数值库，qualification 和完整成本测量本身也不是新原则。第 9–10 页 §8 已承认相邻工作研究过数值路径敏感性、慢速和控制。这可以支撑以“新增可推广知识不足”为由的弱拒，而不是 P0-V。我的判断是 prospective whole-array discrimination 加上 RTX 同集 fresh cost，已超过单纯记录 slowdown；不把未测普遍机制、成功优化或生产负载作为隐含接收条件。

### P1-1：中心研究被历史研究和分母管理推迟，阅读成本高

**位置：** 正文第 3 页表 1、§3；第 4–5 页 §4、图 1、表 2；第 5–6 页 §5.1、图 3。

正文表 1 有 11 个研究行，先介绍历史 costs、独立 direct-ID gate、H1 discovery、V2、旧序列化 cost，读者要在接触 V4 设计前记住多套参照和分母。随后图 1／表 2 再占据显著版面，§5.1 又解释旧 proxy 与旧 fresh gate 不可配对。诚实保留历史的做法正确，但篇章中心因此像一份逐步累加的研究档案。相同的 60/90、78/90、60/72、51/57 分属不同问题，文中解释无错，读者仍需要反复追踪。

**请求：** 用现有材料按问题重排。将 B570 的 Figure 2 冻结流程与 RTX A/B 的最小设计放在主要方法／主要结果入口；紧接呈现 prospective prediction 和 matched qualification/cost，再给 358H 与 M4 支撑案例。将完整历史 timing/proxy inventory 移至附录或压缩为一个背景段／紧凑行组。主文保留“旧 text-path timing 不由新 direct-ID gate 追认”的显著说明、每个实际新研究的提示数与重复数、参照与边界；不应通过合并旧研究或删除失败记录来减轻负担。表 1 可改为“主张—同集对照—端点—工程决定”，历史 campaign 名称与完整分母另保留在附录。

### P1-2：摘要与贡献排序不统一，缩略语过密

**位置：** 正文第 1 页摘要、引言最后的贡献列表；第 2 页贡献续句。

摘要／引言最先并最充分强调 B570 prediction；贡献列表却先列 RTX qualification/cost。两者均是合理贡献，但优先级不一致，使读者不确定论文究竟主要是 trajectory prediction 论文，还是 consumer cost inventory。摘要在很短篇幅内引入 UB1、UB2、72/72、60/72、51/57、57/57、171、0.677×、358H、M4 Guard；分母正确，仍有明显记忆成本。摘要中 UB2、Guard 的直观含义不如正文清楚。

**请求：** 选定统一的中心顺序，并在摘要、贡献列表、结果节与结论中贯彻。保留 B570 非参照完整轨迹预测以及 RTX 同集预测／资格／成本这两组关键数值，把 fork、358H 和 Guard 合为一个补充结论句或移走其非核心细节。第一次出现 UB2 时说明是 target micro-batch capacity，而不是让读者把它当算法名称。标题当前可接受；不要求改成更宽或更强的标题。

### P1-3：主文方法基本足够，但应以紧凑输入流程替代 campaign 回顾

**位置：** 正文第 5 页 §5.2、Figure 2；第 6 页 §5.3；附录第 5–6 页 §J、7–10 页 §M／N.1、12–13 页 §Q.2–Q.4。

B570 的 selected hypothesis / prediction freeze / live 顺序已在主文出现，足以理解 strongest inference；RTX 也交代 separate P/R、sealed tape、native live 不导入 tape 和共享数值例程。完整 allowlist、prefix assertions、capture repair、process witnesses 放附录是合理的，不构成当前方法完全藏在附录。问题是读者先得到 V2/H1 历史和 H2/R_ONLY 代号，再拼装实际 V4 输入关系。

**请求：** 将已有主文／附录信息改写为一个很短的流程说明或小表：B570 predictor 仅接收 prompt；RTX H2 的 draft P 根据自身过去 feedback 产 proposals，target R 自行计算 acceptance/correction/bonus；fresh replay 仅顺序消费 sealed proposals；native live 自产 proposals；最终 predictions/tapes 在 live 前封存。明确 shared numerical routines 和不同 orchestration 的边界。保留现有工程 witness 与详细 RPC 字段在附录。无需新解码器伪代码，也无需把整套验证日志搬入主文。

### P1-4：重复的边界句压过了论证；“causal and transfer limits”应收紧

**位置：** 正文第 1–2 页引言贡献续句；第 5–7 页 §§5.2–6；第 10 页 §§8–10。

“不识别唯一数值原因”“不证明 history 必要”“不追认旧 timing”“不是 portable rule”在引言、结果、§6、相关工作、limitations、conclusion 多次近似复述。§6 目前大部分是结果／限制再说一遍，新增决策组织价值有限。语气有机械式声明感，但我不据此推断写作来源或 AI 作者身份；它主要来自过多防误读句，而非空洞宣传。

引言贡献续句的 “candidate test of its causal and transfer limits”（第 2 页）尤其容易扩大理解。B570 的 fork 是另一个 cohort 的抽样 intervention；RTX 是不同 stack、参照与指定 UB2 候选，不是完全相同 predictor 的严格迁移实验。后续正文已正确限定，不足以认定中心因果主张被推翻，但该短语比实际证据更宽。

**请求：** 将这个短语收紧到“separate sampled intervention and same-set candidate discrimination on RTX”所表达的层次。每个结果节保留与该推理直接相关的一条边界，统一限制集中于 §9；§6 则只陈述“证据—排除的工程选择—固定前提”，避免逐项重报数字。保留“UB2 失败不等于所有 target-only 假设失败”和“fork 后持续策略不等于单块影响”等关键限制，不能因删重复而扩大结论。

### P2：表格标注和浮动位置的小修

**位置：** 正文第 6 页表 3、第 7 页表 4，及第 6–7 页 §5.4 跨页处；附录第 10–11 页 §O／表 A13。

- **表 3：** 表本身可读，`Pairs / 57` 与 `Prompts / 19` 已明确分母；不是字号或列宽事故。但 `Independent P/R (H2)` 对跳读者可能意味着独立数值实现。改为“Separate P/R orchestration (H2)”或加一句共享 numerical routines 的表注；用“fresh target replay”替代只有代码味的 `R_ONLY` 标签，可将内部名留括号。
- **表 4：** 资格、成本方向、CI 清楚，blocked batching 没有伪装成 qualified speedup。caption 的 “no speedup or CI is formed”应明确仅指 blocked batched row；可改为“For the blocked batched path, speedup and CI are not formed.” 这样不会在扫读时与下一行 serialization 的 CI 相冲突。
- **浮动：** 表 3 插在“Table 3 contrasts the / predefined candidates”句中间；表 4 出现在上一页旧结果的 `0.646×` 与下一页 `[0.630, 0.660]` 之间。数值无误，阅读被打断。将句子与整组 estimate/CI 留在同一段，或把旧 cost 结果压成完整独立句放在 V4 后面。
- **附录入口：** §O 称 full filename digest “above”，但完整长文件名在下一物理页表 A13，宜直接交叉引用表 A13。长 digest／包路径虽能辨识，却不适合人工复制；表 A13 与 §Q.5 可将下载对象名、执行入口和 digest 分开，保留原字节身份。

## Rubric A–E

### A：最强结果超越事后观察的科学推断是什么？

B570 在 reserved live 之前冻结的是**整条** capped sequence，而非事后定位到的第一处差异。四个正确预测的非参照轨迹排除“只是输出标准参照”的简单解释，并支持这个指定 draft-free target partition 在有限 cohort 上的 predictive sufficiency。RTX V4 在相同提示上以预先指定候选形成可失败的鉴别：target-only UB2 不具完整同集充分性，proposal-conditioned replay 在所测输入／共享数值例程下充分。两者都不推出唯一 kernel 原因、history 的必要性或普遍传递规律。抽样 fork 支持 score 可变而 sampled immediate decisions 不变，later persistent continuation 另列为不同端点。

### B：有限范围内有什么具体决策？

| 所测证据 | 可据此作出的决定 | 必须保留的前提 |
|---|---|---|
| B570 prediction 72/72，reference/live 60/72 | 可用 UB1 候选预测此路径；不能把该 live 路径作为保持 UB128 参照的替换 | 所测 stack、24 提示、128-ID cap |
| RTX A 的 UB2 51/57、replay 57/57 | 拒绝这个 target-only UB2 候选的完整同集充分性；replay 可复现所测轨迹 | 不是所有 target-only 候选的否定，不是 history 必要性证明 |
| RTX B batching 51/57、serialization 57/57 且 0.677× | 阻止 batching 的全 cohort 参照兼容替换；不采用所测 serialization 作为该边界内的延迟优化 | instrumented post-prefill 边界；logging 成本未被排除 |
| 358H 的 C/Rtarget 上界低于 1 | 固定 measured progress 与 target work 时，单独消除 draft／residual 不能到 parity | 不是改变 target execution 或 proposals 后的上界 |
| M4 Guard/Always 1.0271，CI 全高于 1 | 这组 held-out aggregate 指标上采用已测固定 Always 比此 Guard 更合理 | 两个固定模式与此已冻结 rule；不能推广到全部 adaptive policies |

### C：对实际写出的主张，是否逻辑上必须增加新执行？

**没有。** 在本评审范围内，未识别出需要新 execution 才能修复的确切失败前提。当前不主张独立数值实现、proposal/history 必要性、唯一根因、生产性能、硬件排名或成功 persistence；因此这些没有被测量不构成已写结论的缺口。主机／风扇策略修订也不作为重跑前提。

若作者以后要宣称无 logging 的部署延迟、相同 predictor 的 portability、单块 intervention 导致 later divergence、或成功 state persistence，则分别需要对应的新执行／控制。但那属于更强的新主张，不是本稿接收的默认要求。

### D：现有材料修改能否足够？

**足以修复我识别出的全部写作／可审性问题。** 主线重排、将历史 inventory 留附录、给核心输入流程、收紧 transfer 词句、统一贡献排序、去重和修 float 均不需模型运行。它们会使增量知识更容易评估，不能凭编辑保证所有审稿人对 main-track 意义达成一致；有限结果的重要性仍是判断问题。

### E：本版本的阅读摩擦或不支持的措辞是什么？

主要摩擦是 campaign 名称和分母反复累积、主结果出场较晚、H1/H2 与 V2/V4 在主线前出现、范围句重复、表格插断完整句。局部需收紧的措辞是引言贡献中的 “causal and transfer limits” 和表 3 的单独 “Independent”。摘要 “M4 Guard loses to fixed speculation”在正文有 aggregate 配对证据，但建议摘要补“on the held-out aggregate comparison”，以免被理解为每个请求都输。没有发现必须靠扩大有限 scope 才能消除的叙事矛盾。

## 五个统一轴的评估

| 轴 | 本次判断 |
|---|---|
| 有限科学有效性 | 较强。cohort、参照、输入、endpoint、comparator 与 estimand 已区分；P/Q、即时／持续效应、算术总量／GM 没有明显混淆。 |
| 相对已知路径敏感性与完整成本测量的增量 | 中等。新增 prospective whole-array sufficiency/discrimination 与同集 qualification/cost 有可失败知识；共享例程和很少的分歧提示限制意义。 |
| 有限工程后果 | 中等偏强。对具体配置的采用／排除、draft-only 投资方向及此 Guard 的使用有明确结论。不是可移植优化规则。 |
| 可检查性 | PDF 层面较强，但有披露的能力上限。关键流程、数据角色和匿名入口可定位；本评审未运行 artifact，不能声称独立原始字节／chronology 审计。 |
| 整合后的连贯性与可读性 | 中等。第一页核心观点清楚，RTX A+B 提升逻辑完整性；历史先行和重复防误读句仍显著增加正文阅读成本。 |

## 向作者的具体问题

1. 哪一组结果是准备让读者作为第一贡献记住的：B570 非参照完整轨迹的预先预测，还是 RTX 同集 qualification/cost？请使摘要、贡献序号和章节顺序给出相同答案。
2. “causal and transfer limits”具体指哪一个已测对比？若仅指 separate fork 与 RTX 指定 UB2 候选，能否直接使用这两个准确名称？
3. 能否在表 3 附近用现有输入契约给一个紧凑说明，使跳读者立即知道 fresh replay 接收 proposals 而不接收未来 live IDs，且 numerical routines 与 live 共享？

以上均可用已有材料回答，不构成新实验清单。

## 必要与可选实验

**逻辑必要的新执行：无。** 接收前有用的动作是现有材料的编辑与图表修订，不是为追求正结果继续尝试。

**仅在追求更强结论时可选：** 减少／关闭 logging 的 fresh latency comparison、跨 stack 固定同一个 predictor 的迁移测试、立即还原原政策的单块 fork、跨模型／长度／session 扩展、成功 state persistence 测试。它们分别增加部署、迁移、因果定位或覆盖面的证据，不应因本稿是有限范围研究而全部升格为 blocker。新增独立数值实现或正面控制收益也不是论文类型的固有要求。

## 最强接收与拒绝理由，以及最终理由

**最强接收理由：** 该论文提供可被完整 live 序列推翻的前瞻预测，并实际预测了参照之外的轨迹；RTX V4 再以同集候选鉴别和 fresh 三路径 cost 将预测、qualification、profitability 分开。负结果导向具体配置决定，作者不将其包装成普遍根因或新优化算法。当前结构瑕疵可用已有证据修复。

**最强拒绝理由：** 科学增量可能仍被认为是若干特定实现的合规／成本测试：同库 replay 的充分性、极少分歧提示和有限 cap 不能给出可迁移机制，已知的路径敏感性与开销原则又覆盖许多工程结论。较长 historical inventory 和重复限定使新增洞见与既有常识的差别不够突出。这是成立的意义／表达判断，而非已证明的中央有效性错误。

**最终理由：4/6，信心 4/5。** 我倾向接收这组有限但可证伪的经验知识。新增 RTX A+B 已让论文形成闭合的“预测—资格—所测成本”主线；最需要改的是读者到达这条主线的路径。未认定 P0-V，也未设当前 P0-C 或逻辑必要新实验。评分没有依赖正收益、新算法或未写出的更强机制主张。
