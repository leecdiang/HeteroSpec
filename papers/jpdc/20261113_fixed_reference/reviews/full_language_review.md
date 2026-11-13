# 全文独立语言、创新归因与声明审阅

审阅日期：2026-11-13。逐节通读 `main.tex`、摘要及正文全部十个输入文件，并扫描全文引用。实际文件及其 SHA-256 见 `literature_full_review_snapshot.json`。本轮是完整源码文本审阅；没有将其称为 PDF 视觉验收、全仓库再次代码审计或第二次原始数据复算。相关文献原文和官方代码的已读范围见 `literature_verification.json`。

## 总体判断

主线现在可以顺着读：直观合批反例 → 两类分组 → 消费者合同 → 实现边界 → 因果干预 → 强控制增量 → 两因素归因 → 边界机会与反例 → 完整应用 → 改变数值合同的替代路径。核心结果没有被写成普适加速，也没有把完整投机收益归给 LOCAL。最大的语言问题已从术语堆叠转为若干重复说明：同一 768/1024 例子出现两次，兼容用例出现三次，部分段尾仍像作者自审笔记。可以收紧这些重复，同时保留真正改变结论的限制。

## 必须修正的具体问题

### M1：分组形状公式原先丢失尾部列——已修正并复读

位置：`03_method.tex`，算术分组公式，标签 `eq:arithmetic-groups`。

初读时，`X[K,q] → X[K,a,g]` 与 `q=ag+r` 同时出现；当 `r>0` 时，该映射未表示尾部，形状不守恒。方法审阅者已改成先分离 `X_full[K,ag]` 和 `X_tail[K,r]`，再对完整部分取 `[K,a,g]` 视图。本轮重新读取后确认该数学表述已修复。保留现在的公式。

### M2：factorial 被写成隔离 draft quality——已在自己负责的 related work 修正

位置：`07_related.tex` 最后一段。

原句把 draft quality、verification grouping、implementation improvements 都放在 factorial 可区分的效应之列，超过实验设计。四臂实验固定 draft policy，只隔离 packing、cut 及其 interaction；完整应用对照包含投机整体，不能继续分解其中 draft 质量的贡献。

经主审授权，已改为：

> We report complete speculative-application comparisons separately from four-arm experiments that hold the draft policy fixed and isolate packing, local cuts, and their interaction.

其他根稿文件未由本审阅者直接修改。

### M3：有限资格被概括成部署整体性质——请主审修改

位置：`03_method.tex`，分组公式后的末句：

> Those properties are established for each implementation and deployment covered by the experiments.

前文的 properties 包含激活量化、内部归约、strides、placement。单看这句，会以为这些条件已由完整在线检查或普遍证明覆盖。实现节随后明确 packed 没有继承 loop4 全部检查，且存在 capture 与 clean 的区别，因此这里应与证据等级保持一致。

建议直接替换：

> Each deployment binds these choices to a fixed implementation; qualification checks the resulting outputs and state for the reported cases.

这句仍肯定实现与实测结果，不额外堆一个免责段。

## 建议修订：优先改善阅读，不改变结论

### S1：引言保留短故事，把具体位置与完整干预留给方法、结果

位置：`01_introduction.tex` 第一段；`03_method.tex` 第一小节。

现在两个位置都完整讲一遍四查询、768/1024、零概率、归约变化。引言应只建立读者的疑问，方法用 `765–768` 和 `[768,768,768,1024]` 教会构造，结果再提供干预证据。建议引言首段替换为：

> Suppose a decoder is about to evaluate four known token positions. Processing them together can reuse weights and expose more GPU work. Yet crossing a KV-cache padding boundary can enlarge the physical attention range seen by earlier queries, even when the causal mask hides the same future tokens. The resulting kernel can produce different output bytes. A quantized projection can introduce another difference when query width selects a different quantizer or dot-product specialization.

方法首段保留具体位置、padding unit、extent 向量和解释。其捕获结果句可以压缩为一次结果指向：

> Section~\ref{sec:range-result} tests this mechanism by changing the physical range while retaining the visible operands.

如果主审选择保留方法中的简要观测而不使用交叉引用，也合理；重点是避免引言、方法、结果三次完整复述同一干预。

### S2：兼容用例用条件语气说明一次，不重复声明“没有生产采用证据”

位置：引言第二段；方法的 Reference and consumer contract 第一段；讨论第一小节。

引言列 regression、exact replay、component migration 足够建立价值。`may` 的条件语气已经说明这些是可信使用场景；紧接 `rather than evidence of a measured production demand` 会打断问题叙事。建议引言第二段为：

> Such differences matter when an optimization must retain the result of an existing deployment. For example, a regression workflow may compare full output vectors, an exact replay may resume from a stored cache, and a component migration may exchange states with an unchanged consumer. These scenarios motivate our question: \emph{what parallel execution remains available when the numerical reference is fixed?}

方法段保留 `R_d` 的组成和“更换 device/backend 定义不同参考”，删除其末尾再次列三个用例及 production-adoption 限定的句子。讨论保留实际价值判断：1.51% 证明限定部署的执行增量，尚未测量维护成本、能源或生产投资回报。这样不是删除边界，而是让边界出现在需要作决策的位置。

### S3：引言的继承归因可以正面写

位置：引言 `The construction uses established building blocks` 段。

`are not individual novelty claims` 诚实，但更像回应审稿意见。建议把前两句合成：

> The construction combines established four-column kernels, weight broadcasting, packing, and fixed reduction orders around two distinct grouping constraints.

随后保留“cuts 的位置及 consumer obligations 是方法贡献”和局部切分成本命题。Related work 已给直接来源，方法末尾也保留上游引用，无需每处再次说哪些东西不是创新。

### S4：解释资格覆盖时避免读者误以为每个面板都完成全部情形

位置：`05_evaluation.tex`，Qualification and clocks。

`The checks cover the tested prefill, continuation, boundary, rejection, trim, pending-token, terminal and reset cases.` 其中 `tested` 有限域是必要的，建议保留；若补充矩阵表明这些来自不同 campaign，最好改成：

> Across the qualification campaigns, the checked cases include prefill, continuation, boundary crossing, rejection, trim, pending tokens, termination, and reset; the supplement identifies the coverage of each implementation.

不要删掉随后 clean endpoint 检查不等于重新做全状态比较的说明。那是证据等级的实质区别。

### S5：结果段尾去掉“本报告如何防止误读”的自我说明

位置：`06_results.tex` 最后一段末句。

> Keeping these outcomes together prevents a kernel result, a compatibility result and a service result from being treated as one speedup claim.

前文已经清楚给出 operator、numerical contract 和 NOT_RUN 边界，该句可以直接删除，段落结束在两个 legacy-compatible candidate 的完整算子比值。若需要概括，建议事实句：

> The available measurements therefore compare operator choices; they leave the complete-backend service comparison open.

二者选一即可，不同时保留。

### S6：worker 总时的比较对象再明确一个名词

位置：`06_results.tex`，Initialization can change the decision。

`The 14B worker total ... falls from ... to ... for the compared burst` 未在同句点明 from/to 对象。建议补出对应的固定 M 控制及 `Local-packed D4`，沿用补充材料中的真实 arm 名称；不要为了可读性另造 baseline。后一句 Llama 已写明 fastest M 与 Local-packed D4，结构更清楚。

### S7：讨论复述方法四步可缩短，保留迁移条件

位置：`08_discussion.tex`，What transfers beyond this implementation 第一段。

该段与方法四步枚举重复。建议缩为：

> The transferable object is the construction procedure: derive the physical and arithmetic constraints of a chosen reference, place the required cuts at the operations that depend on them, and check the consumer's outputs and successor state.

随后保留下一段对 paged/sliding cache、mixed-device、Flash attention、并发与随机采样的适用限制。它说明实现推广需要什么，比再次复述执行步骤更有价值。

## 可以保留，不应在 humanizer 清理中误删

1. **摘要的结果顺序。** 先说明机制与条件组合，再给 32B 强控制增量，继而 factorial、负结果、完整应用与现代路径。216 个空白分词的当前源码计数低于 250 词上限；最终仍以抽取正文计数再检一次。摘要没有把 1.51% 写为 LOCAL 效果或完整投机收益。
2. **输出集合 O 的预先定义。** `omitted from O ... before execution` 限制不可删除；否则会让读者以为可事后丢弃不一致向量。现有文字避免了这种扩大。
3. **forced-prefix 与 autonomous reference 的区分。** 这不是术语赘述，而是说明投机分支与生成端点由不同检查回答。
4. **B 的真实身份。** 文稿区分 Q8 backend-loop4 与 mixed-Q4/Q6 scalar-loop B，且 32B 主图使用 C/B。应保留准确 arm 名称，不为迎合旧概括把 B 再叫 loop4；实现审阅负责其固定版本代码追溯。
5. **统计分母。** S3 的 equal-root geometric ratio 和 pooled ratio、12 roots 与 48 pairs 的区别必须保留。Q8 ratio-of-totals、99% family intervals、structural repeat range 和两 episode 无 population CI 也不能揉成一种“error bar”。
6. **自然多轮负结果。** 两个 episode、四个配对值及 pooled ratio 已给足证据，同时拒绝人口层面排名。无需再追加“普遍更慢/更快”的语言。
7. **现代路径。** U/B 的 38.7%、32,766/32,768 bit-pattern 差异、旧 oracle 资格失败及完整 backend 未计时各回答不同问题。当前叙述允许迁移更快，不把 U 写成本文服务收益。
8. **packed 与 marked loop4 的检查不同。** 实现节这是必须展示的差别。CLI 退出与持久服务事务恢复的界限同样应保留；不要把语言精简变成提高保证等级。
9. **related work 的状态义务。** Vosti canonical KV、LLM-42 在 token 成功时也修复 KV 已准确表述。没有首次声称固定归约、KV 边界、调度/算术分离或复用机制。

## 引用与版本检查

正文引用扫描结果：19 个不同 key，全部存在于 bibliography；无重复 BibTeX key；没有虚构引用 key。20 条 bibliography 中，`gsm8k` 尚未在主文引用。主审已确认它将在补充的 width 实验出处中引用，因此无需为了主文未用而删除，也不应为了消灭 unused key 强塞进不相关正文。

当前直接来源核验覆盖 Taming、TML、CoRun、Vosti、LLM-42、upstream few-row 源码、`llama_reproducible`、两篇投机基础论文、Liu 等的正式 ACL 文献以及模型/数据出处。部分文献只核 metadata 和支持该窄陈述的原始摘要，未冒充全文审计；Taming/CoRun 使用固定原 PDF，未在本次重新核其最新 arXiv history。完整范围与每条限制已单列。

引用为作者顺序 key 的自动化检查不能替代渲染后编号顺序检查。`unsrtnat` 配 numeric `natbib` 符合本次所用出现顺序方案；还需由构建负责人确认 PDF 无未解析编号、链接断裂或 bibliography 溢出。

## AI 与其他作者声明

图 1 caption、Methods 中分析/绘图代码说明及文末独立 AI declaration 分工正确，符合本次核验的 Elsevier 图像与研究代码条款。没有 graphical abstract。主稿明确处于 author-review 阶段，没有虚称作者已经完成最终核验或同意投稿。

最终稿应将 `ChatGPT/Codex` 这一合并工具名拆成确实使用的工具及用途，并由作者确认可核实的模型标识、版本和历史研究代码协助。不能为了“完整”补造工具版本；也不能把当前 assistant 对历史项目记录的阅读写成作者已确认的历史声明。本轮文本中 pending 状态是可留的草稿标记。

Data and code availability 区分公开绘图输入、受限 native records、已裁减 intermediates 和待确认存储库，且没有承诺全部原始 tensor 可取得。这个边界应保留。作者身份细节、资金、利益冲突及 CRediT 未确认项放在 author-review 草稿中是合适的；正式提交前应转为作者确认后的真实陈述。

## 本审阅没有解决的事项

这次检查没有复跑 GPU qualification，也没有替代数据审阅者对所有 figure inputs 的逐项回算。没有查看本次最终渲染 PDF，因此不把行宽、图中文字、跨页、裁切与 reference overflow 判为已通过。主审和视觉审阅者应在完成上述内容修改后完成实际大小的逐页验收。
