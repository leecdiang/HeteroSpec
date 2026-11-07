# JSA 双栏与补充材料核对 — 2026-10-10

本轮实际阅读了作者提供的 JSA 官方 Guide for Authors PDF，日期 2026-10-09，共18页。文件标题为 `Guide for authors - Journal of Systems Architecture - ISSN 1383-7621 | ScienceDirect.com by Elsevier.pdf`，SHA-256 `ddd6a4c762c85872af94a1dd97be9add87317a39a6d2ad4657bdf35560c602dc`。这是官方页面的保存版本；2026-10-10 [实时官方网址](https://www.sciencedirect.com/journal/journal-of-systems-architecture/publish/guide-for-authors) 仍返回403。

| 指南位置 | 读取到的要求 | 本轮决定 |
|---|---|---|
| 第8页，File format / LaTeX | Word 单栏；LaTeX 允许双栏，需可编辑源文件 | 补充使用与正文相同的 `final,5p,times,twocolumn` class，交付 editable TeX、PDF artwork 和 bibliography |
| 第11–12页，Supplementary material | 准确、相关、正文引用、随稿提交、每个补充文件有简洁说明 | 保留独立 supplement PDF，S1–S7/S图表编号与目录；正文已有 supplementary 引用，源包分开提供 |
| 第12页，Supplementary material | 补充文件按接收形式上线，不由production重排 | 在本轮直接完成 readable双栏和PDF视觉核验；保持正常class字号／行距／页边距 |

保存的指南未规定补充PDF必须单栏，也未给出本轮采用的27页上限。因此双栏是按官方LaTeX允许性做出的合理版式决定；13页是无损压缩结果，不声称是期刊强制目标或最终publisher typesetting。正常 5p class 与主文一致，没有负间距、降低class默认body size或图形缩放表格。

正文仍12页，abstract为214 words（当前构建词法检查），六keywords，五Highlights均不超过85字符，18参考条目均被引用。Highlights的建议性质、声明和作者事实沿用既有记录，不把所有提交字段视作已完成。

Structured author ZIP含代码／导出／来源绑定；flat主文与补充ZIP各含单独TeX入口及必要资源，供无子目录工作流使用。扁平文件命名／源码规则沿用先前Elsevier官方源审查，本轮只重新验证本地构建，没有重新核对每个在线帮助页面。

本轮没有访问登录后的Editorial Manager、检查attachment slots、上传或运行live Overleaf。最新投稿字段与最终门户接受情况仍须提交时实际核实。指南快照可支持当前双栏决定，不能证明在线投稿成功。作者身份、CRediT、资金／利益冲突、数据访问、AI声明、文献最终状态及其他附件见 `AUTHOR_TODO.md`。
