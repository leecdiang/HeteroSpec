# 投稿适配：基线与持续研究分开判断

核验日期：2026-10-05。以下是根据官方范围与审稿标准作出的适配判断，不是接受概率或投稿承诺。v0.11.0 只整合 #53–56；#59/#60 的迁移验证可能改变优先级。

| 去向 | 官方范围/标准 | 当前基线适配与缺口 | 条件性建议 |
|---|---|---|---|
| MLSys 2027 research track | 原创性、技术质量、意义与影响；10页正文，参考和附录另计 | 技术审计更扎实，独立新颖性和迁移仍弱 | 若新方法形成可迁移的范围选择与净收益，再复评；本基线不作为强接收候选 |
| Journal of Systems Architecture | 系统软件/体系结构，嵌入式方向；欢迎超出特定设计的案例研究 | 端侧异构执行、数值合同与系统成本有关联；需提炼架构规律 | 研究若收束为系统实证案例，值得优先调查；不要只交某工具调参说明 |
| IEEE Access | 技术正确、原创并推进既有知识；不要求同等程度的高新颖性 | 完整实验和可核算证据较契合；仍需真实新增贡献与明确范围 | 是较现实的完整实证论文备选，不能称为保证接受 |
| ACM TECS | 嵌入式系统的分析、设计、行为、验证，覆盖 edge AI | 358H/M4/消费端硬件只有在嵌入式约束是论文问题中心时才有价值 | 条件性去向；若主文只剩通用 RTX 软件 patch，范围优势会减弱 |

官方来源：[MLSys call](https://mlsys.org/Conferences/2027/CallForResearchPapers)、[Elsevier JSA scope](https://shop.elsevier.com/journals/journal-of-systems-architecture/1383-7621)、[IEEE Access reviewer guidelines](https://ieeeaccess.ieee.org/reviewers/reviewer-guidelines/)、[ACM SIGPLAN 的 TECS 官方征集说明](https://www.sigplan.org/announce/2025-10-16-tecs-eic/)。

读取限制：JSA 作者细则和 ACM DL 作者页面在本次检索中受访问限制；没有核验它们的现行模板、页数、费用或周转时间。TECS 范围使用2025年的官方征集说明，提交前应再核验现行作者说明。没有据此给出费用或日期建议。

当前建议是保留格式完整的 MLSys 工作稿作为基线，先完成新方法最有信息量的验证。若只获得有限配置案例，考虑 JSA/IEEE Access 的实际范围；若得到固定配方跨合同迁移和对最接近工作的明确优势，再决定是否保持更高创新门槛的投递目标。工业 track 也不应作为创新性不足的绕路：官方强调实际生产部署和大规模证据，当前实验没有建立这种条件。

证据审计、artifact evaluation 与论文 novelty 是不同判断。可复核性可以加强可信度，不能单独替代方法贡献；官方 AE 也不能当作接收概率加分的承诺。
