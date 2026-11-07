# v0.14.4 实际验收记录

日期 2026-10-10。基线为最新 #74 HEAD `e6236d220a5123c691153f2558b8d4dc5d92b0c6`。本轮包括 Figure 2 标签修正／关系矩阵、Figure1C 间距、两 PDF 色彩语义统一、无损补充压缩、两张补充图、交叉审稿与 humanizer 全文复读；继续更新 #75，没有新模型请求、forward 或 warmup。

| 检查 | 当前记录 | 实际范围 |
|---|---|---|
| #74 基线 | `provenance/V0143_BASELINE_CONTENT.json` | 268 个源包成员与精确 HEAD Git blob 核对；记录原文／表／asset 对照 |
| 无损压缩 | `output/LOSSLESS_COMPRESSION_QA.json` | 七节、23 小节、30 导航目标；全部 16 张原表的 cells／caption／label／顺序，537 个 generated data cells 加 inline tables；26 claim rows／28 experiment entries 相同 |
| 全文语言 | `output/HUMANIZER_QA.json`, `HUMANIZER_REVIEW_ZH.md` | 固定 humanizer v3.1.0；19文件／17改写／63段；第二遍复读完成，编辑前源码可唯一精确恢复；数字／数学／引用绑定／inline tables／七 figure blocks／版式命令相同，科学范围另经人工阅读 |
| 受保护文件 | 同上 | 183 文件字节相同，含全部 133 来源、26 导出、16 历史副本、计算／验证、书目／声明／class/style；八个 protected 正文图资产按初始认证哈希重绘；compute AST 相同 |
| 数值 | `output/NUMERICAL_QA.json`, `SCIENTIFIC_QA.json` | RTX384 行、所有 12 比较与 source-specific interval、七 regressions／round reversal；B570119 行、15/14pairs、三个 timer 与 suffix；16masks、fixed-UB saved ratios、M4 等 CPU 复核 |
| 当前图表 | `output/ASSET_PRESERVATION_QA.json` | 22 个供给资产锁定；默认构建保留图表排版。七图科学输入对象与初始 #75 逐项相同；仅重新表达布局、关系和颜色角色 |
| 图值与边界 | `output/VISUAL_DATA_QA.json`, `FIGURE_INPUTS.json` | 原 48 task points／六 saved intervals／四 rounds／16 masks／12 geometry cells；Figure2 五矩阵、B570 recipe labels；S1 全119行／missing／suffix；S2 原 speeds／intervals／ceilings／budget；七 PDF vector bounds；实际 SVG glyph/link、20 IDs 与比例条，Figure1C 净距，48+4 绘图位置／形状／颜色和 R/M/C／M/C／conditional 颜色角色独立检查 |
| 编译 | `output/BUILD_QA.json` | 正文12页、补充13页；正常5p双栏；零 overfull／undefined／duplicate targets／missing glyphs／float too large；全字体嵌入，无 Type3 |
| 视觉 | `output/VISUAL_REVIEW_QA.json` | 全25页 contact sheets；全部七图独立放大；七个关键页面160dpi复看。不声称每页都单页高倍率检查 |
| 作者源包 | `output/SOURCE_PACKAGE_REBUILD_QA.json` | 最终 299 文件 ZIP 空目录完整 CPU 构建；sources、numerical／scientific core／lossless／figure／humanizer QA、22图表、PDF bytes/text 相同；同环境范围 |
| flat sources | `output/FLAT_SOURCE_REBUILD_QA.json` | 正文与补充分别解包编译；page counts/text 相同；每个 PDF 的 byte equality 单独报告，不假设差异原因 |
| JSA 版式 | `JSA_REQUIREMENTS_RECHECK.md` | 已读作者给出的官方指南快照第8／11–12页，允许 LaTeX 双栏且无补充单栏要求；实时官网403，门户未访问 |
| 审稿 | `CROSS_REVIEW_ZH.md` | 单审阅者五角度交叉核对；主要范围／统计风险仍开放，不是外部独立评审 |

页数由 27→13，减少 14 页（51.85%），并包含两张新图。正文仍为 12 页。压缩来自双栏、合页目录和 wide-table reflow；正常 class 字号／行距／页边距，未使用负间距或缩放表中文字。

原始 raw archives 未重新打开，fixed-UB 只复算保存的 task ratios，358H180-row original-host ceiling audit 仍继承。没有 live Overleaf／Editorial Manager 编译或上传；当前包是作者审阅和可复建的提交材料。作者事实、数据权限、AI声明和最终参考确认仍待作者处理。最终 SHA 在各 receipt 与 `SHA256SUMS.json` 中，继承记录在 `validation/INHERITED_*`。
