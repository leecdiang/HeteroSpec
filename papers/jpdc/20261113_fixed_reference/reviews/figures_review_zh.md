# 科学图表与数据复核记录

## 已完成的工作

已完成 6 张正文图、5 张补图，以及“全部 15 个固定应用对照”和“4 对自然多轮 episode”的可编辑 LaTeX 表。全部图提供矢量 PDF、保留可编辑文字的 SVG 和预览 PNG；生成入口为 `paper/scripts/build_figures.py`。没有执行 GPU、模型推理、远程写入或修改既有实验数据。

本轮实际读取了固定版本的原论文图表计划、公开数值文件、#241 公开逐行计时及其计划/原统计结果。主审/方法审阅者另直接核对了 AV 干预原报告与方法代码。图表任务中使用了 `scientific-visualization` 和 `statistical-analysis` 两项固定版本技能及其出版/期刊要求参考文件；它们是工作清单，不是数据来源。

## 视觉系统和每图意图

1. **总览图**：先让读者看见位置 765–768 对应的物理范围差异，再把物理分组与算术分组并排，最后落到 attention 局部切分与下游输出/状态。八列分组明确是示意；没有画成所有组都可任意并发。
2. **AV 干预图**：四格呈现 scalar/wide capture 与 768/1024 replay 的交叉结果；将双向因果干预放在“完整 AV 输出”这一可核范围内。没有画 KV 状态验证，也没有把 V 错画成补零。
3. **强基线图**：48 轮配对观测留在 12 个 root 内；主 C/B 与弱 G 对照在旁边，读者能直接看到换基线后剩余约 1.51% 的增量。B 明确是共享量化后的 backend scalar loop。
4. **factorial 图**：8 个直接效应与 2 个 interaction 均有 root 观测，保留 LOCAL/packing 的跨 1 区间。直接效应是 ratio of totals，interaction 是 equal-root geometric ratio of ratios，不能统一称同一个统计量。
5. **应用图**：左为同 D4 组合增量，右为完整应用相对最快固定 M，分面使用不同控制与刻度。Llama 中两个更慢 root 没有删除。
6. **几何图**：所有 12 个 B570 cell、36 个配对观测均保留；跨界和 inside 方向相反可见。3 个点的 min–max 是描述范围，不是置信区间。A5000 的 20/2224 机会数只作分离注释，没有与 B570 拼曲线。
7. **宽度补图**：equal-work q8 和 live k7 的方向相反，并列显示工作量计数，防止把减少 launch 当成应用收益。
8. **有符号成本补图**：保留所有 phase 的正负项、很小的 setup/teardown 项，以及未归因 residual，准确相加到完整 service。
9. **历史几何补图**：保留 q16/q32 逆转和未测 Smol q4，未测格写明 Not measured。
10. **旧 32B/生命周期补图**：旧弱基线大数字和 D4 负结果同时出现；Llama 四个固定 M 在 resident/worker 时钟下的排序逆转并列，避免只保留热服务优势。
11. **RTX 合同补图**：C、C1、U 分三面板；前两个同旧合同候选没有改善，U 更快但改变数值合同。完整现代默认后端未运行，不画成 0。

全套采用与稿件协调的 P052 字体、蓝/赭/灰和形状/填充/纹理冗余编码。主色文字对白色背景对比度超过 5:1；附带灰度实际 PDF 检查页。图内保留短面板标题，没有使用封面式巨型标题。

## 数值与文件检查

- 47 个公开源文件的 SHA-256 全部匹配；24 个 #222 输入另校验了 Git blob。未修改任何源文件。
- 图表生成完成 **133 项断言**：包括 S3 的全部 root 与三对比、Q8 全部 point estimates 与 root 数、所有 108 个 B570 时间的比例、旧 32B 96 行总量、宽度 phase 余额、15 个应用控制和自然多轮总量。
- 重要舍入细节：#237 CSV 的 `per_operator_ms` 便利列与公布分析相差约 1e-8。改为从同 CSV 的原始 `event_ms / batch_repetitions` 重算，精确重现 kernel 0.5823907655654195、complete 0.6129241707091678；没有“修正”原数据。
- 所有散点都在显示范围内；没有为了刻度裁掉 root 或 adverse pair。
- 11 个最终 PDF 均为单页、固定 7 英寸宽、无嵌入栅格图，无 Type 3 字体；字体已嵌入。实际 PDF 渲染已逐图检查，另检查灰度总览。
- 第一轮发现轴标签/脚注重叠，已增加下边距修复。S3 主估计文字与横轴标签原冲突也已修复。

## 正文交叉审阅中发现并反馈的问题

1. factorial 图注不可将 interaction 也称 ratio of totals；应单独注明 equal-root geometric interaction。
2. 几何图用 triangle/circle 和填充区分，range 线型相同；图注应写 marker shape/fill，而非不同 line patterns。
3. 应用图顺序为 (a) 同 D4、(b) 完整应用相对最快固定 M，图注需明确。
4. 摘要的 two-request multi-turn pilot 统计单位不准确，反馈改 two-conversation 或 two-episode；实际为 2 cases × 2 rounds × 2 arms 的 8 个计时 episode。

正文评价/结果中的主要数值已与直接行和 source results 对照：S3 等 root 与 pooled estimator 分开，prefill/decode、factorial、同 D4/完整应用、自然与 RTX 数值一致。

## 仍需作者与主审处理

图表 CPU 复核不能替代重新执行正确性资格，不能使不公开的大型 tensor/KV 变成公开数据。原 99%/98.75% 等区间在此按来源保留；主审已另执行公开统计复算。完整现代默认 backend 仍未计时，图中保持这一空缺。

主稿最终页大小、图浮动、图注、补图顺序和作者 AI/数据可得性声明须由主审整稿检查与作者确认。源数据可得性应区分此处公开标量/聚合记录与另行持有或受限的 native payload。没有为了获得更大加速建议或执行新实验。
