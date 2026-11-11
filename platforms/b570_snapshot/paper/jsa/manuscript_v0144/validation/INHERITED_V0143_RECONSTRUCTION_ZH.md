# v0.14.3 JSA 英文科学编辑说明

本轮基于当前视觉 PR #73 的最新 HEAD `f7d2a863265e6d619d3582d702e57cec1cfa9be2`，新建独立版本目录并接续该视觉分支。没有回退到 #72 或旧稿。主文由13页变为12页，补充仍27页，保留正常 Elsevier 5p 双栏与原有字号、行距、页边距和图尺寸。

正文现在围绕三个工程问题组织：固定 ordinary 输出的要求下，哪些路径／状态差异值得约束；哪些源码明确的有限约束取得资格；在 ordinary 与 matched 两个 paid baselines 下，合格方案是否值得部署。结果段先提出问题，再给主要观察、工程选择和就近限制。删除重复的版本、路径、验收流程叙述；复现和作者事项留在补充与作者文档。

| 位置 | 英文修改与保留边界 |
|---|---|
| 摘要、Introduction | 三个具体贡献：局部诊断、已实现的 phase/query-layout 约束、双 paid baseline 和负结果；不宣称普遍新理论或方法优越性 |
| Runtime、Related Work | 解释 target/draft 独立状态、提交与回滚、role/phase guard；明确已实现部分及没有进行的 same-contract 方法比较 |
| Methods | 区分 prediction、qualification、paid cost；先定义 R/M/C、任务中位数与 GM；不混用 timer 或把 bootstrap 当作独立 session 稳定性 |
| Figure1 与 §5.1 | 明确 query `(d,q,h,1)→(d,1,h,q)`、K/V broadcast 和 mask view；projection/FFN 保持 batched；不写全部 scalarized、全网络逐 token 重算或新 CUDA kernel |
| Figure2 与 §4 | 先教读矩阵，再解释 current-path／interaction／retained-state；ID 是类别，B570 HumanEval 为整体 recipe；72 forks 的0 immediate／18 downstream 与195内部 events 分母分开，后续 UB128持续 |
| Figure3 与 §5 | mask3 仅在四开关族中 inclusion-minimal，3/7/11/15全保留；joint k/UB geometry 与 fixed-UB4 widening 成本分开；/229、旧HE/18、11输入、两次重复、cap512和最大261均保留 |
| Figure4 与 §6.1 | R/C≈1.742、R/M≈1.683、M/C≈1.035；generation M/C≈1.169；部署收益与draft增量分别解释，不作组件耗时拆解或timer相减 |
| Figure5 与 §6.2 | 直接回答均匀性和跨轮一致性：22/24、17/24、round2≈0.940；不逐点复述48点，不把任务GM与round GM混用 |
| §6.3–6.5、Implications | 保留 qualified-but-slower、B570119/120与15/14 pairs、missing old-N1和endpoint/raw/suffix；M4独立策略启示、358H条件预算和单家族限制 |
| Conclusion | 给有限但可用的控制位置与基线选择；保留失败范围与实际成本，第二家族未跑不预写结果 |
| 补充 | S1移除过时版本叙事，S2.3标题与持续续写策略一致，S7集中复现和访问范围；其他科学正文和全部数据表保留 |

另有一项必须由绑定来源澄清的标签问题：Figure2 的 E 不是跨面板相同的后期 phase-binding candidate。C面板是 ordinary `N0_ordinary` donor，D/E面板是 `E_k1_ub2` donor。现有六case来源明确这一点，已在图注和邻近正文解释。图自身未重画，token ID、recipe、分母和结果没有改动。

五张 PDF、五张 SVG 和八张数据表共18资产与视觉基线逐字节相同；冻结数据、统计估计、比较对象、底层精度和所有失败结果保留。正文比率沿用图表显示精度。26个claim与28组实验去向保留，独立版本目录也保留所有旧稿。

验收包括完整CPU复算、图值回查、两PDF编译、39页contact sheets逐页查看、完整作者ZIP解包重建和两个flat源包重建。主文12页全部检查；补充27页也全部检查，而不只检查修改页面。不存在未定义引用、溢出、缺字或Type3字体。详细范围及当前记录见 VALIDATION_LOG.md；源码包测试不等于 live Overleaf／Editorial Manager验收，绑定导出复算不等于完整私有raw归档重审。

作者身份、CRediT、资助、冲突、永久访问链接、实际AI使用声明及文献待核项仍见 AUTHOR_TODO.md。第二模型家族和same-contract比较未补做；没有运行模型实验、合并、投稿或公开私有数据。
