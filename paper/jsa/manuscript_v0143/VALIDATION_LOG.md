# v0.14.3 实际验收范围

本轮是英文科学编辑和已有导出的 CPU 验证。基线为当前视觉 PR #73 的 `f7d2a863265e6d619d3582d702e57cec1cfa9be2`。没有模型请求、forward、warmup或硬件实验。

| 检查 | 当前记录 | 实际范围 |
|---|---|---|
| 当前基线 | `provenance/EDITORIAL_BASELINE.json` | 282个v0.14.2文件与最新HEAD Git blob核对；不以旧源包代替当前基线 |
| 编辑继承 | `output/EDITORIAL_QA.json` | evidence、historical_sources、source_records、文献、class/style、18图表资产和compute AST与视觉稿比较；26claim／28实验ID和原规划事实来源保留 |
| 数值 | `output/NUMERICAL_QA.json`、`SCIENTIFIC_QA.json` | 133源绑定、26导出、16历史；RTX384行资格／时间、B570119行与15/14完整pairs、phase16masks、M4及已有区间等CPU复算 |
| 不重画 | `output/ASSET_PRESERVATION_QA.json` | 五PDF、五SVG、八TeX数据表逐字节一致；默认build只复算，不重生成图表 |
| 图值 | `output/VISUAL_DATA_QA.json`、`FIGURE_INPUTS.json` | 48任务点、六比率及区间、四request轮次、16masks、12geometry格；五PDF字体／画布／矢量检查 |
| 科学文字 | `SCIENTIFIC_AUDIT.md` | 通读主文、全部补充和五图，核对源码query/mask/phase、local crosses、持续UB128、geometry和timer定义；Figure2 E donor按实际来源澄清 |
| 编译 | `output/BUILD_QA.json` | 主文12页、补充27页，正常5p双栏；无Overfull、未定义／重复引用、缺字、过大float；字体全嵌入，无Type3 |
| 页面视觉 | `output/VISUAL_REVIEW_QA.json` | 最终主文12页与补充27页均经渲染contact sheets逐页检查；未发现裁切、遮挡、缺页或图文重叠。此记录不声称每页额外做单页高倍率检查 |
| 作者ZIP | `output/SOURCE_PACKAGE_REBUILD_QA.json` | 最终ZIP到空目录完整CPU重建，源文件、数值、独立audit核心、18资产、PDF字节及提取文本一致；当前环境范围 |
| flat ZIP | `output/FLAT_SOURCE_REBUILD_QA.json` | 主文／补充分别解包编译，页数与提取文本一致；字节是否相同逐项报告，差异不自行解释为仅元数据 |

旧版科学／视觉叙述归档在 `validation/INHERITED_*`，不是本轮执行证据。新旧稿对照的正文词数使用去除图表、标题、引文命令和数学后的英语token近似计数，明确不等于TeXcount或投稿系统统计。

完整私有raw归档没有重新打开。源绑定认证不等于重新逐行审查每个源文件；fixed-UB保留任务比率复算范围，358H180行original-host审计仍为继承证据。没有live Overleaf／Editorial Manager、期刊字段复查、外部同行评审或acceptance概率评估。作者声明与参考文献待核问题保持待确认。
