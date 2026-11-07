# v0.14.5 arXiv 合并稿交接

本次对应 [arXiv:2610.03228](https://arxiv.org/abs/2610.03228)，由作者自行更新。以 [v1 PDF](https://arxiv.org/pdf/2610.03228v1) 为正式署名和文档结构依据：Chengzhan Li；University of Electronic Science and Technology of China；chengzhan.li@std.uestc.edu.cn。v1 为 23 页，正文与参考文献之后接补充材料，页码连续。

为给左侧 arXiv 自动添加的竖排标识留出间距，合并版左右页边距统一为 **20 mm**。保留字体大小、栏间距和正文高度；行宽变化使此前 24 页重新分页为 26 页。期刊正文和单独补充的原有页边距保留。

本轮生成 **26 页单份 PDF**：`output/arxiv-combined-v0.14.5.pdf`。正文和参考文献占前 13 页，补充材料自第 14 页开始。延续连续页码，保留 S1–S7 的章节、图表标识及 30 个补充导航条目。使用目前统一的 Elsevier 双栏视觉样式。省去第二份完整标题页式 frontmatter 和五条重复参考文献，不删实验文字、图表或证据。

## 更新文件

- `output/arxiv-source-v0.14.5.zip`：**arXiv 上传请使用此包**：37 文件精简源码包，单一入口 `arxiv.tex`，七张矢量图、一份包含全部 18 条参考文献的 `arxiv.bbl`。`00README.json` 指定 pdfLaTeX 和这个入口。
- `output/arxiv-title-v0.14.5.txt`、`output/arxiv-abstract-v0.14.5.txt`、`output/arxiv-comments-v0.14.5.txt`：从本轮稿件提取的提交元数据；comments 为 “26 pages, 7 figures; expanded diagnosis, phase-scoped qualification and cost comparisons; includes supplementary material”。这里的 expanded 是相对于公开 v1，不表示此次 CPU 收尾新增了模型实验。
- `output/overleaf-author-source-v0.14.5.zip`：完整作者工作包，保留复现、来源绑定及作者审阅记录，不作为精简 arXiv 上传包。

单一 TeX 编译共享引用编号，避免拼接两份独立 PDF 后的重复目标和失效链接。补充材料引用的五条文献均在正文 18 条参考文献中。正文与补充科学内容的 input 顺序保持一致；所有七图与生成表逐字节继承。S7 只调整公开包与完整作者包的编译/访问说明，数字、公式及引用保持不变。

## 公开稿与作者审阅稿

arXiv 合并稿沿用 v1 已发表的正式署名、单位及邮箱；未将 GitHub 用户或 ASV 作者信息混入。将作者工作稿中尚待填写的 CRediT、funding/interests 表单和确认提示留在单独的 JSA 审阅稿中。公开稿保留实际 AI 辅助和 CPU 复现边界说明，不代填未经提供的 funding、competing interests 或公开数据地址，不宣称完成了私有原始档案重审。

精简源码包只含论文编译依赖；S7 清楚区分它与完整作者工作包，未声称全部证据导出已经公开。正式作者应在更新前通读新稿并确认公开声明符合实际情况。

## 已验证及最终提交动作

从空目录解压精简源码，运行 pdfLaTeX；检查连续页码、书签、有效链接、无 overfull/未定义/重复目标、嵌入字体及重复编译字节一致。对 26 页合并稿另做逐页视觉检查。具体结果在 `output/ARXIV_SOURCE_QA.json` 和 `VALIDATION_LOG.md`。

使用 arXiv 的已有条目更新流程，更新标题、摘要和 comments；上传上述精简源码包，选 pdfLaTeX，检查平台生成的单份 PDF，再由作者提交。内部 v0.14.5 是仓库版本号。本轮没有登录、上传或替作者提交。

依据（2026-10-10 核对）：[TeX submission](https://info.arxiv.org/help/submit_tex.html) 的编译依赖与 `.bbl` 要求；[00README JSON](https://info.arxiv.org/help/00README.html) 的入口配置。已发表 v1 的链接由作者提供，已核对公开 HTML 和 PDF；不再依赖此前未定位的仓库初版。

第二模型家族、同合同外部方法比较、独立会话稳定性仍为后续三项研究，限制在摘要、§7 和结论中保留。

## 新论文额度与版本更新

2026-10-10 核对的 [arXiv moderation policy](https://info.arxiv.org/help/moderation/index.html) 将每位作者每个自然月最多两篇 **new submissions** 与 **replacements** 分开规定；后者在版本 5 之后限制为每周一次。[Replace 指南](https://info.arxiv.org/help/replace.html) 说明已公布条目通过作者主页的 Replace 更新，并建议不要每周更新多次。因此更新 `2610.03228` 通常不消耗剩余的新论文名额；这里未查看账号是否收到单独限制。

这份有明确研究边界的稿件可以先更新为 v2。下一轮研究优先评估 1.035 倍 matched 请求收益跨独立会话的稳定性，再对第二模型家族完成输出资格与普通／matched／speculative 成本比较，随后补同合同外部方法比较。第二家族扩大证据范围，但本身不解决其余两个缺口。
