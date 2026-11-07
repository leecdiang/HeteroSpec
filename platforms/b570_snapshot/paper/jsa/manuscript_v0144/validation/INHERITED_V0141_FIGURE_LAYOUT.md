# v0.14.1 双栏图表布局记录

日期：2026-10-09。五张主文图按正常 Elsevier `elsarticle` 5p 跨栏阅读尺寸重新组织，采用精确 7.2 in（182.88 mm）画布，不使用 `bbox_inches='tight'` 裁切后再放大。主文宜以 `figure*` 和 `width=\textwidth` 插入；5p 正常正文宽为 522 TeX pt（约 183.46 mm），仅需约 1.003 倍的等比调整。本配置是作者双栏稿，不能据此宣称与 JSA 最终出版版式完全相同。

| 图 | 画布（in） | 画布（mm） | 图内正文最小字号（pt） | 布局与证据保留 |
|---|---:|---:|---:|---|
| 1 架构与 query-layout | 7.2 × 3.0 | 182.88 × 76.20 | 9.5 | 左侧 target/draft prefill 汇入 retained state，右侧展示 proposal、verify、commit/rollback；保留四个 phase bit、状态回环、实际 query view、K/V 与 mask 条件及仍为 batched 的操作。 |
| 2 Natural crosses | 7.2 × 3.4 | 182.88 × 86.36 | 9.5 | 保留全部五个 2×2 诊断与所有 token ID；采用两行三列面板，空面板说明 donor/recipe、task-local 颜色与 own-path shams。B570 recipe 标签断成两行，语义不变。 |
| 3 Phase qualification | 7.2 × 3.6 | 182.88 × 91.44 | 9.5 | 保留完整 16 mask、四开关、四个 full-response probe，以及 3/7/11/15 的 PASS 标记；bit 与资格区分组。普通格中文字 10 pt。 |
| 4 Paid cost | 7.2 × 2.6 | 182.88 × 66.04 | 10.0 | generation 和 resident-request 两面板；保留 R/C、M/C、R/M 三种比较、saved descriptive intervals 与全部点估计。 |
| 5 Task variation | 7.2 × 4.5 | 182.88 × 114.30 | 9.5 | 保留 24 个 MBPP task 在两个 timer 下的全部 48 点；两个面板共用按 request 排序的任务轴。24 行中心间距约 10.18 pt；任务字号 9.5 pt。1× 线、各 timer 的 GM、回归颜色与 faster 分母均保留。 |

PDF 字体检查对**直立字符**读取实际字号；旋转的 y 轴标签在 PDF 文本提取器中会被报告为单字形宽度，因此其 `size` 不能当作旋转文本字号。旋转轴标签在绘图代码中为正常 10 pt。五个 PDF 的所有可提取字符均处于各自页面边界内。PDF 保留嵌入的矢量字形，SVG 保留可编辑文本；没有栅格化定量观察值。

## 主文成本表

| 表 | 列结构 | 实测 tabular 宽（TeX pt） | 使用方式 |
|---|---|---:|---|
| RTX paid cost | Ratio / Timer / Speed / 95% interval；六行 | 155.759 | 单栏 `table`，正常 `\small`（5p 主文为 9 pt）；24 task medians、四 repeats、generation 与 resident request、mask 3 说明保留在图注。 |
| B570 paid cost | Ratio / n / Gen. / Request / Host；四行 | 169.656 | 单栏 `table`，正常 `\small`；保留三个计时边界、15/14 complete two-round task-pair 分母、缺失 old-N1 不插补和 raw suffix work paid 条件。 |

表宽由独立正常 5p 文档的 TeX box 测量，均小于正常单栏约 251 pt。两表不使用 `resizebox`、缩字体、负间距或非模板页边距。数值仍保留原六位精度，RTX descriptive interval 仍保留原三位展示精度；行列重排没有改变数值。

## 实际验证范围

- 使用 `/usr/bin/python3` 3.9.6、NumPy 2.0.2、Matplotlib 3.9.4，调用既有 `compute()` 对 frozen exports 作 CPU 验证后生成图表；没有模型请求、warmup 或新硬件实验。
- `compute()` 的 AST 与 v0.14.0 完全一致；两张成本表数值体的多重集合与 v0.14.0 完全一致。
- 五图返回的 semantic input 字典与 v0.14.0 `output/FIGURE_INPUTS.json` 完全相同。
- 六张其余生成表（补充长表及辅助表）在本轮重新生成前后 SHA-256 完全相同；补充长表布局未修改。
- 五个当前 PDF 图与独立成本表测试文档已用 Poppler 渲染并逐图查看，未见裁切、重叠或缺字。该检查只覆盖图和表资产；主文及补充全文页级检查另见最终视觉验收记录。

代码改动限于 `scripts/reconstruct.py` 的 `table_file()`、`make_tables()`、`make_figures()`，以及对应 `figures/` 的五个 PDF/SVG 和 `tables/` 的两张成本表。冻结数据、计算函数、主文、补充文字和构建流程未由本图表任务修改。
