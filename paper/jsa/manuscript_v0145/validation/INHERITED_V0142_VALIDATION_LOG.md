# v0.14.2 实际验收范围

本轮执行已有导出的 CPU 复算、图表重构、有限文字调整、编译与渲染。没有模型请求、forward、warmup 或新硬件实验。

| 检查 | 当前记录 | 范围 |
|---|---|---|
| 基线 | `output/INHERITANCE_QA.json` | #72的a686af6基线源包；原evidence、historical_sources、source_records逐文件相同；compute AST与六张补充生成表相同 |
| 数值 | `output/NUMERICAL_QA.json`、`SCIENTIFIC_QA.json` | 133源绑定、26导出、16历史；RTX384rows和B570119rows等既有复算；不重新打开私有raw |
| 图值与矢量 | `output/VISUAL_DATA_QA.json`、`FIGURE_INPUTS.json` | 48任务点、六比率及保存区间、四request轮次、完整16masks、12geometry格；五PDF无Type3、无栅格图像、文字不越画布 |
| 编译 | `output/BUILD_QA.json` | 主文13页、补充27页；无Overfull、undefined、重复引用、缺字；全部嵌字且无Type3 |
| 视觉 | `output/VISUAL_REVIEW_QA.json` | 五图独立渲染；40页contact sheets查看；补充仅版本／继承说明变动后重查相应页。图文无裁切遮挡；末页参考文献留白保留，下一轮文字编辑后再平衡 |
| 作者源包 | `output/SOURCE_PACKAGE_REBUILD_QA.json` | 最终ZIP解包到空目录，完整CPU重建并比较源文件、图表、数值、PDF字节和提取文本；以此当前机器记录为准 |
| flat源包 | `output/FLAT_SOURCE_REBUILD_QA.json` | 两文档分别解包编译；页数／提取文本相等；PDF字节是否一致逐项报告，不把不同字节自行称为仅元数据差异 |

首轮本地编译发现 Computer Modern Typewriter 缺少矢量映射，改为嵌入 Latin Modern Typewriter 后通过。首轮部分 PNG 渲染文件截断，改用 JPEG 重新生成全部页面；损坏预览不是交付资产。

保存的历史检查位于 `validation/INHERITED_V0141_*`，不当作本轮执行证据。没有 live Overleaf / Editorial Manager 上传或期刊格式验收，没有第二模型家族、完整私有raw审计或外部同行评审。作者声明与文献待核事项仍由作者确认。
