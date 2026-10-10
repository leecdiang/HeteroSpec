# HeteroSpec v0.14.4 交叉审稿与处理记录

日期：2026-10-10。审稿基线为最新 Draft PR [#74](https://github.com/leecdiang/HeteroSpec/pull/74)，HEAD `e6236d220a5123c691153f2558b8d4dc5d92b0c6`。本记录由同一审阅者从贡献、因果、统计、实现和复现五个角度交叉检查；不冒充独立审稿人投票，也不估计录用概率。检查覆盖完整正文、S1–S7、26 条 claim、28 组实验去向、绑定实现与导出，以及全部渲染页面。

## 结论

目前最成立的论证是：在消费级系统上的一个模型家族中，用可执行的参考输出合同区分路径、状态与局部交互，再限定修复范围，并用已经支付的普通／匹配／候选成本评估收益。正文把诊断、实施和成本连接起来，也保留了反例、缺失和有限资格边界。

本轮可直接解决的问题是 Figure 2 的符号歧义、补充材料的排版长度，以及 B570 状态／计费合同与 358H 条件预算的阅读负担。主要科学风险仍是单一模型家族、缺少同合同的外部方法比较，以及小幅 RTX 匹配请求收益的独立会话稳定性。排版优化和现有导出的 CPU 重算不能消除这些风险。现有标题、摘要和 §7 保留有限范围；此次没有新增模型运行或扩大结论。

## 最近 PR 的交叉核对

| PR | 核对的角色 | 对本轮的约束 |
|---|---|---|
| [#70](https://github.com/leecdiang/HeteroSpec/pull/70), `00ea8f7` | JSA 重构计划、实验清单、模型家族门槛 | 28 组实验不能因视觉压缩失去去向；第二家族尚无本轮结果 |
| [#71](https://github.com/leecdiang/HeteroSpec/pull/71), `c1f1126` | 正文故事与证据重构 | 不把本地诊断升级成全轨迹保证；保留输出、估计器与历史研究边界 |
| [#72](https://github.com/leecdiang/HeteroSpec/pull/72), `a686af6` | 正文 Elsevier 5p 双栏 | 正常正文字号、栏宽和页边距作为补充版式的参照 |
| [#73](https://github.com/leecdiang/HeteroSpec/pull/73), `f7d2a86` | ASV 参照下的五图视觉重构 | 继承衬线字、蓝／赭／绿、白底细线、A/B/C 分面及图内范围说明 |
| [#74](https://github.com/leecdiang/HeteroSpec/pull/74), `e6236d2` | 科学英文编辑后的最新论证 | 以其完整正文与 27 页补充为唯一修改基线；继承四张正文图及全部原始表格数据 |

以上 PR 均为分层提交；本轮新目录 `paper/jsa/manuscript_v0144/` 叠加在 #74，旧目录和既有证据保留。#73/#74 的已取回评论没有提供额外 Figure 2 修正指令，所以下述修改依据实际 donor/recipe 记录。

## 五个角度的审稿与裁决

| 角度与位置 | 发现及其含义 | 严重程度／本轮处理 |
|---|---|---|
| 贡献与相关工作；§1、§7，C01/C10/C26 | Batch invariance、固定形状执行与推理确定性已有相关工作。本文的可守贡献是消费系统上参考合同、自然交叉、有限修复和付费比较的连接；不能据此宣称新的普适 lossless 算法或内核优势。 | 主要科学风险仍开放；原有限定保留。当前引用能说明关系，但不能替代同合同基准。 |
| Figure 2C 与 D/E；§4.4，C06 | 原图用 E 同时表示 MBPP/72 的普通 N0 donor 和 HumanEval 的 `E_k1_ub2` donor，容易把 donor、recipe 与后来候选混为一谈。HumanEval 的 UB 与 output reservation 同时变化。 | 局部呈现问题已修：C 用 N0；D/E 用 Alt.；列写 UB1/r3 与 UB2/r2，释义 r。20 个 categorical cells、重复次数和 0/72→18/72 完全保留。 |
| 因果解释；§4.2–§4.4、S2，C04–C06 | 自然交叉只识别选定前缀处的当前路径、保留状态或局部交互。MBPP/72 是相同当前列的状态控制；HumanEval 是 whole-recipe 因子。Tensor 等值不能指认唯一内核，opaque sampler/RNG bytes 未被完整恢复核对。 | 重要范围限制已保留；图和文字一致。继续避免 UB 单因素归因或随机状态普适保证。 |
| 局部与持续输出；§4.3、S2.3，C05 | 72 个 fork 的即时决策均不变，但 18 个持续执行后来分歧。后续 alternate blocks 仍采用 UB128；72/195 是执行／内部事件，不是独立任务数。 | 重要因果边界已保留；不是“一个块改动后恢复”的后效应证明。 |
| 付费比较；§6.1、S4.1，C14 | RTX request 的 R/C≈1.742，由 R/M≈1.683 与 M/C≈1.035 的比值恒等式连接；generation 的 M/C≈1.169。较大普通参考增益不能全部算作 speculative 增量。R 是执行过的参考，不是最快实现证明。 | 现有正文和 Figure 4 表述成立。三个比较和两个计时域、全部 12 比较保留；恒等式不解释组件成本。 |
| 不确定性；§6.2、Figure 5、S4.1，C15 | 七个 task-median 匹配 request 回归，round 2 GM≈0.940220。Task bootstrap 描述所选任务，未覆盖独立会话／日期变化；聚合的小幅正收益不能承诺部署稳定性。 | 主要统计风险仍开放。保留全部 24 task medians、四轮结果和明确的 descriptive intervals。 |
| RTX 实现；§5.1–§5.4、S3，C10–C12/C16 | Query 从列维转为批维，沿用 head stride；KV broadcast、batched projection/FFN/recombination 仍在。通过 masks 3/7/11/15 是四开关家族内 inclusion-minimal 结论；更宽 UB 失败限制外推。 | 图 1/3 与实现说明一致；不声称重写全部算子、全局最小修复或独立 CUDA 内核优越性。原实现文件和计算函数不改。 |
| B570 实现、缺失与成本；§5.5/§6.4、S5，C19–C22 | 同一 target context 保留 KV/live sampler，pending token 只取样／接受一次；capture-off 不读 witness。Endpoint equality 与 raw-array equality 分离；26 suffix IDs 仍付费。119/120 包含 old-N1 /400 round 1 缺失；old N1 仅 14 个完整 pair，R/M/C 各 15 个。 | 新 Figure S1 把三项合同放在同一图中。缺失不补零、不补测，不删除 /400 其他比较；仍无独立成本组件归因。候选对强基线失败的结果保留。 |
| 历史比较与 358H；§6.5、S6，C23–C25 | 历史 text/ID、energy domain 和估计器不可池化。358H prompt ceiling 为 CPU≈0.837219、NPU≈0.844840；固定 baseline/progress、删除其他非负工作后，达到 parity 仍需 target-work 至少降 16.28%/15.52%。Pooled accounting 是另一估计器。 | 新 Figure S2 区分 measured circle 与 conditional open diamond，无 ceiling CI；不把必要预算说成实现收益或 NPU 不可能性。180-row 原主机 ceiling 审计仍是继承证据。 |
| 补充材料／复现；S1–S7 | 27 页的主要长度来自单栏、独立目录分页及宽表处理。双栏保留独立 S 编号、目录与完整 table rows 可显著压缩；单靠 PDF 字符统计不足以证明信息不丢失。 | 27→13 页，减少 51.85%。逐段规范化比对、所有 16 个原始表格（正文 4＋补充 12）单元格／标题／标签比对、证据字节比对和 clean rebuild 均用于核验。 |

## 与相近工作的复核

本轮打开了以下一手来源，复核的是当前定位而非新增优越性结论：

- [LLM-42, arXiv 2601.17768v2](https://arxiv.org/abs/2601.17768v2)：固定形状复用与经验证的 fast path/rollback 已有关联，因此本文应聚焦实际合同、诊断和付费结果。
- [Vosti, arXiv 2609.38981v1](https://arxiv.org/abs/2609.38981v1)：形式化 bitwise logit determinism 与 kernel/state/KV 条件，和本文 finite response-ID qualification 的证据层级不同。DOI 链接在 arXiv 页面上可见；本轮未成功完成 resolver/注册状态验证，保留作者待核事项。
- [StageReplay, arXiv 2607.28495](https://arxiv.org/abs/2607.28495)：同一前缀下 construction/precision 交叉与 KV 承载关系已有讨论；本文不能把“相同前缀不等于相同数值状态”单独作为新发现。
- [Thinking Machines, Defeating Nondeterminism in LLM Inference](https://thinkingmachines.ai/blog/defeating-nondeterminism-in-llm-inference/)：batch-invariant inference 是相关已有路线。当前源码审计可界定本文的 graph control；不能取代与该路线相同输出合同下的实测比较。

以上关系来自原始论文／技术说明；“需要收窄贡献”和“还缺同合同比较”是本审稿的判断。18 条原参考文献保持不变，未把相关工作的不同实验条件或不同确定性定义作为直接速度对照。

## 双栏允许性与视觉裁决

检查了作者提供、日期为 2026-10-09 的 JSA 官方 Guide for Authors PDF：第 8 页允许 LaTeX 双栏；第 11–12 页要求补充文件准确、相关、被引用、随正文提交并附说明，且按收到的形式发布。未见补充 PDF 必须单栏的条款，因此本轮采用与正文相同的 `final,5p,times,twocolumn`。2026-10-10 实时官网仍返回 403；这项判断明确基于保存的官方指南，不表示投稿门户已接受。完整来源与哈希见 `JSA_REQUIREMENTS_RECHECK.md`。

视觉参照是作者 ASV `40.pdf` 第 7–8 页，SHA-256 `85b1c624a0d500dbd7ded7d9b36af2b5db8aed3fc5317d50b6fb2bcc2c00c776`。新图与正文沿用 STIX/Times 衬线、蓝 `#426b8b`／赭 `#b07b43`／绿 `#3e725e`、白底细线和灰色说明。颜色在同一角色中沿用；shape、实心／空心、文字同时表达区别，避免仅靠颜色。Figure S2 的实心圆表示 measured estimates、空心菱形表示 conditional ceilings，不能互换。两张新增图只重新表达已存在的信息，图内注明范围，不制作虚构 timing trace。

## 本轮验证及剩余事项

`LOSSLESS_COMPRESSION_QA.json` 逐项保存了允许的三处文字更新、七节原内容、30 个导航目标、537 个 generated data cells、六个 inline tables、26 claims 和 28 groups 的核对结果。191 个受保护文件字节相同，覆盖 133 个绑定来源、26 个冻结导出、16 个历史副本、原计算逻辑／格式类／声明／书目，以及四张未改正文图的八个资产。最新来源包的 268 个基线源文件先逐一与 #74 Git blob 核对，再形成可随 ZIP 独立检查的基线记录。

CPU 重算、标准库科学核对、七张 vector figure 的数据／边界检查、pdfLaTeX 编译、源包空目录重建和 flat-source 重建均记录当前哈希。全部 25 页以联系表检查，Figure 2 和两张新图独立放大检查，关键宽表页面复看。当前检查不重新打开私有 raw archives、不重新执行模型，也不验证缺失二进制／驱动或在线投稿系统。

作者事实、CRediT、资金／利益冲突、公开访问方案、AI 使用声明、最终文献状态以及实际门户附件仍由作者核实。科学加强若继续开展，应优先提供新的家族／方法／独立会话证据；本轮保留这些空白和限制，不填入预期结果。
