# JSA 要求核实记录 — 2026-10-09

针对 PR #69 的 v0.13.0 作者审阅稿。核查内容来自 JSA 官方 Guide for Authors 的检索索引，以及可完整读取的 Elsevier LaTeX/data 指南。JSA 全页直读仍返回 403；本地 HTTP 得到的 195 字节“Site Unavailable”页面也不是指南。此记录只认证已取得明确官方文本的条目，不声称完成全量投稿审核。

## 已确认与稿件状态

| 项目 | 核实规则 | v0.13.0 状态 |
|---|---|---|
| 审稿 | 单匿名 | 正式稿需补真实作者/单位/通讯信息，现仍为占位 |
| 栏数 | Word 单栏；LaTeX 可双栏 | 当前单栏可以保留 |
| 摘要/关键词 | ≤250 词；1–7 个英文关键词 | 161 词、6 个 |
| 文内引用 | 方括号编号 | 使用 elsarticle-num |
| Highlights | 鼓励；3–5 条，每条≤85 字符（含空格） | 5 条，长度 71/77/71/67/75 |
| 源文件 | 需提供可编辑源文件 | 已有 LaTeX/表格/图，但工作包须另作提交打包 |
| 研究数据 | Option C | 持久材料位置和正式可用性声明未完成 |
| EM 目录 | 不处理源码子目录 | Overleaf 工作 ZIP 有子目录，不能直接作为 EM 源码包 |

JSA 规则来源：[官方作者指南](https://www.sciencedirect.com/journal/journal-of-systems-architecture/publish/guide-for-authors)。EM 打包来源：[Elsevier LaTeX instructions](https://www.elsevier.com/researcher/author/policies-and-guidelines/latex-instructions)。Option C 的完整解释来源：[Elsevier research data guidelines](https://www.elsevier.com/researcher/author/tools-and-resources/research-data/data-guidelines)：存放、引用并链接数据；若无法分享则解释原因。不能把“尚未提供位置”写成已经履行数据要求，也不能编造限制理由。

## 对当前论文的判断

当前单栏、编号引用、摘要与关键词无需因本次核实而修改。`12pt/preprint` 是本稿的审阅格式选择，不是本次已核实的 JSA 强制选项。尚未确认专属 class、指定 3p/5p/CAS、字号、行距、行号、graphical abstract 的强制性，以及正文长度/页数上限；不从检索未命中推导“没有上限”。24 页单栏不能换算为已获得许可的任意长度，也没有证据要求压回旧稿六页。

已确认的投稿准备缺口是作者信息、材料访问方案和源码打包。作者需确定哪些保存数据、计算脚本和运行环境说明可以向读者/审稿人提供，明确无法提供的材料及真实原因。当前 private repository 和作者工作 ZIP 不应被描述为已实现独立公开硬件复现。此记录没有发布数据、创建材料 DOI、上传期刊或更改仓库可见性。

正式 EM 源包应从稿件所需文件生成一个平坦目录，同步改写 input/figure 路径并验证重建；分析证据与独立补充材料按其用途另行组织。现有 Overleaf ZIP 是已验证的作者工作包，仍保持原发布哈希；本次文档核实不重新生成论文 PDF 或源包。

其余提交项以文章类型和投稿入口的最终清单为准。作者、资助、利益冲突、材料访问及 AI 声明需要真实信息与作者确认。不要拿旧会议 CFP 页数、2018 年指南镜像或第三方模板的泛化内容代替现行 JSA 规则。

## 记录范围

对应 `JSA_REQUIREMENTS_VERIFIED_20261009.json` 的数值与状态；原 manuscript_v013/JSA_REQUIREMENTS_AND_DEPENDENCIES.json 是上一轮核实快照，本记录提供后续确认。核查本身不代表编辑部已批准本稿版式、数据方案或投稿适配。
