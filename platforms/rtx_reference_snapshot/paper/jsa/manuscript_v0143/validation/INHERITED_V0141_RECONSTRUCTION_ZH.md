# v0.14.1 中文修订说明

本轮继承 #71 v0.14.0 与 #70 已确定的科学主线：运行事务/状态接口 → 状态与当前路径诊断 → 阶段约束及原生输出资格 → ordinary/matched 实际成本 → 工程选择与边界。main=`f3fd2ae…`、#70=`00ea8f7…`、#71=`c1f11267…`；两PR均未合并，#71仍为已核验latest。main是#71祖先，#70是#71的merge base，#71比规划多两个提交。独立分支接#71，仅在新manuscript_v0141交付，所有旧版本/证据保留。

## 实测篇幅和词数

| 版本 | 主文 | 补充 | 本轮依据 |
|---|---:|---:|---|
| v0.14.0单栏 | 30页 | 25页 | 读取基线PDF；没有把单栏页数当作超长证据 |
| 内容不变双栏 | 14页 | 25页 | 本轮编译；仅class/font兼容及跨栏浮动体调整，文字、结果、引用不变 |
| 最终v0.14.1 | **12页** | **27页** | 本轮干净构建与39页逐页渲染/检查 |

12–15页是作者编辑目标，不是JSA规定。采用官方elsarticle `final,5p,times,twocolumn`双栏作者稿；类文件、正常字号、行距和页边距保持正常，没有负间距堆积，也不声称精确模拟最终出版版式。补充保留正常12pt单栏；新增两页目录及必要推导，不设人为页数上限。

词数为TeXcount3.1.1 `-inc -sum main.tex` 的 text 项：Sections1–8正文 **6,394→5,908**；包含frontmatter/declarations的text **6,829→6,344**。最终headers207、captions/浮动体说明375，分别记录。排除文献、公式、数值表单元、嵌图文字及独立补充；加权Sum count包含数学计数，不冒充自然语言词数。摘要仍为既有词法口径218词。没有机械删减百分比。

## 主要删移及准确位置

| 编辑 | 原位置 | 新位置与作用 |
|---|---|---|
| 合并重复范围/非普适性说明 | Introduction/runtime/Methods/Discussion | 首次定义和关键结果仍就近限定，其余集中主文§3、§7.3 |
| 移完整参数/作者核验说明 | §3.1/3.4 | Supplement S1、S5.2、S7；主文仍保留合同、单位、资格、估计量、计时边界 |
| 缩短M4分层数值/oracle细节 | §6.5 | S6.6、Table S11；主文保留540请求、180/180、Guard更慢和两固定行动oracle限制 |
| 移358H条件公式/完整预算推导 | §6.5旧eq:floor | S6.7、Equation S1、Table S12；主文保留90请求、负收益和fixed-progress下uniform target-work必要削减预算 |
| 合并重复的工程决策总结 | §7.1–7.3 | §7保留行动和限制，对应方法/关键失败/主要比较仍在§4–6 |
| 移第二家族章节插入计划 | §7.3 | AUTHOR_TODO；正文仍明确单一Qwen3家族，不虚构新结果 |
| 澄清两处源码描述 | S5.2/S3.1 | sample pending→bindUB1→native loop consume/accept；mask是view而非新materialization，不变结果 |
| 清理旧S1/S2附件简称 | main/supplement/llama.cpp note | 独立supplement与author source package明确区分内部S节号 |

主文仍独立支撑三个RQ。C01–C26、E01–E28完整保留，去向分类为9核心、12主文简述/补充详述、7补充历史/边界/复现；原规划事实和源路径逐字保留。具体位置含稳定label和源码路径，不依赖浮动体页号。

## 图表和科学口径

五图按跨栏阅读宽度重新组织，图内最小正常文字9.5pt；保留全部16 masks和24任务×2timer点。相关工作/合同表跨栏，两核心成本表正常small=9pt单栏，不缩放表格。任务图由双栏对照的参考文献后孤立第14页回到结果第10页。正文图注说明对象/单位/限定；全部图表显式引用。

RTX request保留R/C=1.741569、M/C=1.035071、R/M=1.682560，generation单列，比率恒等式不是组件成本分解。七个matched-request回归、round2=0.940220、state×recipe/own-shams、repair/regression/local-null、phase有限最小性、24project-unused资格与width失败均可见。固定UB4下更宽draft合格却更慢、B570修复后输给两强基线仍为主文反例。B570119/120、15/14配对、first-EOG/cap128与full-response区别、26paid suffix不变；历史re-tokenized-text不升级。M4/358H不称RTX跨平台修复复现。

## 验收与重建

新执行CPU复算及标准库独立审计：RTX384行、12比较、48轮次、50恒等式、qualification digest joins、phase/crosses/fixedUB；B570119行、三个timer、15/14配对、suffix与旧路径轮次反转；M4secondary/oracle。358H原180-row floor审计仍标为继承。认证133源绑定、26导出、16历史副本；42份副本与v0.14.0字节一致。另检查本轮实际5683个基线Git blob身份，不复用旧5427计数。未重开完整private raw、重哈希遗漏模型/驱动或运行模型实验。

主/补干净编译无undefined/missing bibliography/duplicate labels或链接目标/overfull/missing glyph；字体全嵌入，无Type3。39页本轮全部重新渲染/查看；补充30目录项与目标页一致。结构化Overleaf ZIP与两件flat ZIP分别解包重建。同环境Overleaf两PDF字节一致；flat supplement也字节一致。flat main仅5个嵌入图的PTEX.FileName元数据随路径改写而变：实际比较485个逻辑PDF对象（含415压缩对象）、decoded streams、文本和12页RGB像素；不是假设的timestamp解释。哈希/工具链/文件数见JSON。

Overleaf重建不代表Editorial Manager验收；官方Elsevier要求源文件同级，另交付经过构建验证的main/supplement flat包。未登录、未上传、未投稿。图像页PNG为可重建scratch，验证记录保存其哈希。

## 仍待作者确认

作者/单位/通讯、CRediT、资助/利益冲突、永久数据/软件访问和权限、最终AI声明、人工科学/语言/引用复核仍待确认；Vosti DOI与另一文献publisher最终页码仍待重查。当前JSA Guide在线403，其最新匿名化/附件字段未完整核实，继承官方指南记录与本轮通用源包规则核查分开。第二家族没有新结果，本轮不执行/安排；不自动合并Draft PR。
