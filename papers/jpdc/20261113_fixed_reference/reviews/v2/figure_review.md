# 第二版图表修订与独立图稿审阅

## 已完成的图表工作

主文采用六个论证任务：方法构造、物理范围干预、强基线增量及阶段定位、Q8 两因素、机会与静态成本、固定工作效率与实际服务工作量。共交付十二组 PDF / SVG / PNG；旧完整应用图移至补充。绘图源为 `paper/scripts/build_figures.py`，逐图版本、直接来源和输出哈希见 `paper/generated/figure_manifest.json`，完整图注建议见 `paper/generated/figure_captions.tex`。

| 文件 | 修订与目的 | 源尺寸 |
|---|---|---|
| `fig01_overview` | 四个查询贯穿 extent、whole/local、一个四列算术组、输出所有权、接受后的 KV 和 pending correction；另用明确标记的八行 prefill 展示跨组 packing。 | 7 × 5.20 in |
| `fig02_extent` | 保留双向 extent 干预及四个完整 AV 输出归属。 | 7 × 2.15 in |
| `fig03_strong_baseline` | 保留十二 root、四轮配对、C/B 主估计和 G 次级对照；新增独立描述性 phase 合计面板。 | 7 × 4.40 in |
| `fig04_factorial` | 保留全部 root、原 99% 区间、两项跨 1 的 LOCAL-with-packing 结果和 interaction。 | 7 × 3.35 in |
| `fig06_geometry` | B570 的 controlled crossing/inside 与 A5000 机会密度、89 行源码构造分别分面。 | 7 × 4.00 in |
| `fig07_work_cost` | 新三联图：固定八 token 的操作比值；每 arm 的工作量变化；十六 root 的真实服务比值和原区间。 | 7 × 3.30 in |
| `fig05_application` | 移补充，保留全部 88 个 root 对照点、完整应用与同 D4 的不同基线；升高源字号。 | 7 × 2.80 in |
| 原五张 `supp*` 图 | 保留相位正负贡献、历史反例、未测单元、生命周期反转和不同合同 RTX 算子结果。 | 沿用并复核 |

统一使用 P052 / Palatino 系字体、蓝与赭色、直接标记、位置和形状冗余编码。没有三维或面积编码，没有用生成式图像制作数值图。机制图由可编辑程序构造，AI 对图表代码与设计的辅助使用应在投稿声明中如实保留。

## 关键数值与口径

- S3 的 B 为共享激活量化后的 backend scalar-loop；a=1、whole cuts。C/B 的原等 root 几何估计和原 95% 区间不变。新增 phase 面板显示相同每 arm 48 次 measured requests 的合计：prefill 143.926569367→137.984134692 s，decode 216.663232421→216.689812818 s；其他与 residual 4.241877220→4.250911806 s；服务总和差 −5.906819692 s。这些合计没有误差条，不作为独立样本，也不替代主估计。
- S3 `COST_AUDIT.json` 来自固定 commit `ab695a766d055f7d3c6b1fed0720c579c749bcdb`、Git blob `8574ebf0e4532defa0077ebea92e1f891844c059`。另外直接用同 commit 的原 `RECONSTRUCTED_ROWS.json`（blob `bec82ee09ddbe3b62571517f94aa925632ca5bbd`）复核 B/C 各 48 次的 phase 求和。交付包不复制含 token 的完整 rows。
- B570 图保留十二格、每格三个配对值及 min–max；它们不是总体置信区间。20/2,224 是另一平台的验证周期计数。89 行 4→3 calls、23→23 projection tiles、154→178 KiB logical masks、19→20 concat nodes 是源码推导；没有标作流量或 GPU 时间。
- 图 7 的四个 fixed-work 单元各有四个 origin-level 聚合点；live 每种方法有十六个 root，原 98.75% paired-root 区间不变。四种方法在相同 k 下拥有相同的 **每 arm** 工作计数；每 arm 128 次 measured requests，来自十六 root × 八次 repeated order blocks。11,472 emitted tokens、3,504→2,296 cycles、14,016→18,368 verified rows、10,512→16,072 proposals 均是每 arm 合计，不能再跨四种方法相加。
- 该计数口径是在交叉审阅中发现并纠正的一处实际错误：最初把压缩 `work_by_k` 误读为按四方法合计。随后直接读取原 `LIVE_RESULTS.json` 的八个 arm，并新增其字节保持副本及对应复算约束；数值本身从未更改。原文件固定于 `ba5b4c8e01d50d4bfaab1ac3908f798347be063a`，Git blob `e515a920bec3929d80616cce04acf06d3a504539`，32291 字节。
- 完整应用图注保留 8B 同 D4 对照的固定顺序。RTX 图仍分开 C、C1、U 的 session、合同和事件计时；未测现代完整 backend 没有画成 0。

直接新增来源：

- [S3 phase accounting](https://github.com/leecdiang/HeteroSpec/blob/ab695a766d055f7d3c6b1fed0720c579c749bcdb/benchmarks/server_expansion_v1/strong_baseline_followup_20261110/RESULTS_S3_20261112/COST_AUDIT.json)
- [89-row source-derived construction](https://github.com/leecdiang/HeteroSpec/blob/750346a149da58aa94a0d16016f5c451221008f7/benchmarks/server_expansion_v1/N/local_cost_decision_20261113/RESULTS/REPORT.json)
- [Original RTX live per-arm counts](https://github.com/leecdiang/HeteroSpec/blob/ba5b4c8e01d50d4bfaab1ac3908f798347be063a/benchmarks/rtx_q8_transfer_20261109/results_20261109/LIVE_RESULTS.json)

## 已做的验证及其意义

1. CPU 全量生成成功。52 个来源身份检查包括原有 47 个文件和新增 5 个公开来源；原 47 个输入及冻结统计脚本均未改动。138 个 reconciliation 条目检查源哈希、从已有计时重算的图中点、root 比值、相位求和和新增每 arm 计数映射；**这不是 138 项新实验，也不是 backend 正确性或统计推广性的证明**。
2. 所有十二张独立图在彩色和灰度渲染中实际查看。修正了机制图最底部组标签相挤、强基线与 geometry 图的 xlabel/legend 重叠、图 7 的相邻方法标签重叠。将容易与数学输出集合 O 混淆的 `O / FFN` 改为 `Output proj. / FFN`。
3. 独立 PDF 检查：十二张均为矢量图，无嵌入栅格面板、无 Type 3 字体，文本字体均嵌入。源字号下限为主文 8.2 pt（extent 图 8.3 pt）、补充 8.6 pt；按主文 6.84 in 和补充 6.53 in 宽放置后最小值分别为 **8.0126 pt** 和 **8.0226 pt**。实际编译成稿的缩放另行复核，不能用这个预估代替最终版面。
4. 生成器检查页边之外的文字、坐标轴之外的观测点；未隐藏个体、置信区间跨 1、负结果、负相位贡献和未测格。该检查不替代实际人工看图。
5. 方法与语言审阅者分别查看首图并核对正文：四查询只有一个 a=4 组，八行 prefill 使用 last-only 输出，z2→correction，保留至 767 的 KV 与 768 的 pending token 一致。

应用的科研图形技能为 `scientific-visualization` 及其 publication-guidelines 参考材料，固定版本 [2d2065fb4520fa3f3f2bcf61cff26ec8b7eba4b5](https://github.com/K-Dense-AI/scientific-agent-skills/tree/2d2065fb4520fa3f3f2bcf61cff26ec8b7eba4b5/skills/scientific-visualization)。它提供设计与检查方法，不提供数据或实验结论。

## 完整稿件 PDF 复核与未做范围

未启动 GPU、未执行 native kernel、未重建全部原始二进制观测、未新增总体统计区间、未做色觉受试者或打印机测试。灰度冗余依靠形状、线型、位置及文字检查；不宣称完成了实际色盲用户研究。方法实现的完整审阅由方法分工负责，本报告只陈述图示的逐项交叉核对。

已用 Poppler 渲染并实际逐页审阅正文 13 页、补充 12 页。最终正文第 10–13 页和补充第 3、6、8、10 页在末轮修改后重新渲染并查看；其他页与此前逐页审阅的图像逐像素一致。页 2 的方法开头有足够正文，旧参考文献孤页已消除，Related work 现在从图 6 下方连贯开始，RTX 表头 Path 的 0.6738 pt 溢出已通过轻微调整表内列宽消除；没有改官方版芯。补充日志无 overfull box；正文日志仍报告 `\maketitle` 处 123.62721 pt 的空盒 overfull。实际标题页和页面边界检查没有发现相应可见越界；此模板标题阶段警告保留记录，不声称构建日志零警告。实际成稿中主图最小文字为 8.0157 pt、补图为 8.0294 pt；未发现图内裁切、点遗漏、图注越界、异常字形或遗留悬挂标题。图 5 的静态标签为 “Tiles / projection”，23 的单位是每个 fully consumed projection。图 6 和补充 F.1 的累计工作均明确为每 arm 128 次测量、同 k 四方法共享的计数。检查限于本报告记录的最终 PDF 字节版本，不能代替作者确认科学主张、作者信息和投稿声明。

| 最终文件 | 页数 / 字节 | SHA-256 |
|---|---|---|
| `paper/main.pdf` | 13 / 679537 | `546514a17e11cedf7fd1790c62a0df5fd70aa4d6f114740fa1025e2905e67a69` |
| `paper/supplement.pdf` | 12 / 519139 | `fb64f3a19db23e50c53f3cd7cd61dc1f4ead09d7c28291b6c1e4e6f1172d6b49` |

逐页字符边界、实际图内字号和哈希记录见 `reviews/v2/main_final_page_check.json` 与 `reviews/v2/supplement_final_page_check.json`。PDF skill 用于对最终成稿的只读渲染检查；图形生产仍由可复现的 Matplotlib / SVG 代码完成。
