# 给 6.1sol 的下一轮文字衔接 prompt

请基于 HeteroSpec 当前 v0.14.2 视觉重构稿完成一轮 JSA 英文科学编辑。先读取本文件所在分支的最新 HEAD、`paper/jsa/manuscript_v0142/README.md`、`FIGURE_LAYOUT.md`、`SCIENTIFIC_AUDIT.md`、`CLAIM_EVIDENCE.md`、`EXPERIMENT_DESTINATIONS.md` 和 `AUTHOR_TODO.md`，然后通读主文、补充以及五张图。当前基线接在 #72 上；以实际所在分支／PR 为准，不回退到旧稿。创建独立分支和新的 Draft PR 接在当前视觉 PR 上，不合并。

本轮目标是让英文论证与五图一致，维持正常 Elsevier 5p 双栏主文约12–15页（含图表和参考文献）。当前主文13页、补充27页。不要重画图，不要改变冻结数据、比较对象、统计估计、分母或结果方向。允许修改图注和面板引用；如发现科学错误，先回到绑定来源核对，给出具体更正，不以措辞掩盖。

主线：在需要复现固定 ordinary target 输出的消费级系统中，speculation 会改变有状态执行。局部 natural crosses 用于诊断；源码明确的 query-layout／phase 约束在有限族中取得资格；ordinary 与 matched 两个 paid baselines 区分部署收益和 draft 的增量；geometry 失败、qualified-but-slower、B570 强基线失败、M4/358H 控制与成本边界共同限定工程结论。突出实际 runtime 设计和工程选择，避免把论文写成日志、审计报告或普遍新理论。

逐图写作任务：

1. Figure1：解释独立 target/draft 状态、query view `(d,q,h,1)→(d,1,h,q)`、K/V broadcast／mask view 和 role/phase graph guard；projection/FFN 保留 batched。不能写成全部 scalarized、逐 token 全网络重算、全模型适用或新 CUDA kernel。
2. Figure2：先给读矩阵方法，再讲 current-path、interaction、retained-state 三种局部观察。token ID 是类别；B570 HE 的当前列是整体 recipe，不是单一 UB 因子；MBPP/72 两列相同。F：72 forks 中 immediate changes 为0、downstream changes 为18；后续 alternate blocks 继续UB128，不能写成 isolated single-block-then-restored 的因果效应，也不把195 decision events当195独立任务。
3. Figure3：mask3是测试的四开关族中的 inclusion-minimal，而不是所有输入／所有实现的最小必要条件。3/7/11/15通过。geometry右图是k与UB共同变化、11输入、两次重复；UB6/8的MBPP/229失败，cap512不是512个实际生成位置，最大观察长度261。旧HE/18属于另一面板，不能隐去。与固定UB4而只扩draft宽度的成本反例分开。
4. Figure4：先定义R=ordinary，M=matched repaired target-only，C=speculation；request R/C≈1.742、R/M≈1.683、M/C≈1.035，generation M/C≈1.169。比率乘法不是组件耗时拆解。不能把generation与request相减解释host成本，也不能用1.742宣称draft贡献。
5. Figure5：全24任务，generation22/24、request17/24更快；四轮中round2≈0.940反转。任务中位数GM与round GM不混用，descriptive task bootstrap不等于session稳定性。段落应直接回答均匀性和稳定性，而非复述48个点。

必须保留：B570119/120、old-N1缺失不补齐、15与14完整task pairs、endpoint/raw/suffix区分，B570对强基线更慢；RTX wider fixed-UB qualified-but-slower；M4独立策略启示并非RTX repair复现；358H条件预算而非已实现加速或NPU不可能；one-model-family限制，第二家族未跑不得预写结果。现有完整28实验去向与26claim映射继续可追踪。

英语编辑要求：每个结果段按问题→主要观察→工程含义→关键边界组织。删除重复的版本、文件路径、验证流程或防御性套话，把复现细节放补充／作者文档；关键限制要就近保留。Introduction突出3项具体贡献，Related Work明确已实现部分和没有做的same-contract对比，Conclusion给有限但可用的设计结论。不要增加无来源state-of-the-art、first、universal、causal、significant或acceptance措辞。正文展示三位有效小数已足够处与表图统一，底层数值不改。

不要为页数缩字号、行距、页边距或使用负间距；不要删失败结果、缩成不可读图，也不要把同一家族说成跨家族。作者身份、CRediT、资助、冲突、永久数据链接、AI声明和文献待核项继续标记待确认。若补充新相关工作，逐篇读一手来源，不能仅凭标题添加引用。

完成后：重建两PDF、数值复算、图值校验、源码包解包重建，检查全部主文页面和发生变化的补充页面。报告正文文字变化、页数、图表／证据保持情况、实际检查范围与未解决问题。提交主文PDF、补充PDF、Overleaf源码包、中文修改说明和可审阅的Draft PR。不得运行模型实验、合并、投稿或公开私有数据。
