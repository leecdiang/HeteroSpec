# v0.14.3 图文对应与保留的视觉语言

本轮不重画图。以下画布、颜色和面板组织均继承当前视觉PR #73；五PDF、五SVG和八数据表由 `provenance/LOCKED_VISUAL_ASSETS.json` 锁定。英文编辑修改图注、面板引用与邻近论证，未更改图值或布局。

参考作者提供的 ASV 论文：白底、衬线字、细线、低饱和蓝／赭／绿、按论证功能组织 A/B/C 面板，机制示意与实测证据配对。没有复制 ASV 的科学内容，也没有把参考 PDF 加入仓库。所有定量图由冻结导出数据和绑定报告生成，不使用生成式图像。

统一画布宽 7.2 in，按正常 `\textwidth` 跨双栏插入。主字号约 9 pt，面板标题 10 pt，辅助标注最小 8 pt。PDF 为嵌入字体矢量图，SVG 保留可编辑文本。低于／高于 1 的方向用形状冗余编码，不能只靠颜色判断。图 4 的两种 timer 使用不同且明确标注的横轴范围；图 5 A/B 共用范围和任务顺序。

| 图与画布 | 要回答的问题 | 实际输入 | 科学边界 |
|---|---|---|---|
| 1，7.2×4.2 in | 状态由谁持有，代码改了哪里，何时启用约束？ | `source_records/benchmarks/rtx_consistency_contract_v1/query_batch_patch.py`；`rtx_consistency_phase2/scope_patch.py` | 正确 view 为 `(d,q,h,1)→(d,1,h,q)`；数字 tiles 是示意，不是测量；目标／draft 状态分别持有。图复用条件不能读作普遍充分条件。 |
| 2，7.2×4.15 in | 当前路径、保留状态与交互如何区分，局部检查能否代表续写？ | `evidence/RTX_NATURAL_CROSSES.json`；`evidence/b57065/CAUSAL_RECHECK.json`；绑定 `b570_partition_intervention_v1/DELIVERY_REPORT.md` | 保留五个 2×2 token-ID 矩阵；ID 是类别，不作差。B570 HumanEval 改的是完整 recipe；MBPP/72 两列相同。F 的 0/72 与 18/72 不是孤立单 block 因果效应，后续替代块继续 UB128。 |
| 3，7.2×3.85 in | 哪个 phase 子集足够，扩大 geometry 后是否仍成立？ | `evidence/RTX_PHASE_FACTORIAL.csv`；绑定 `rtx_closeout_bcd/REPORT.md` 的12行表格 | 16 masks 全保留；mask 3 仅在测试的四开关族中 inclusion-minimal。右侧 joint k/UB 变化与固定 UB4 成本实验不同；11输入、两次重复、cap 非实际长度，旧 /18 失败在另一面板。 |
| 4，7.2×3.7 in | 部署收益中多少在无 draft 的路径已经存在？ | `evidence/rtx66/COST_SUMMARY.json`；`RAW_COSTS.csv` | R/C、R/M、M/C 和六个保存区间全部保留；1.742≈1.683×1.035 为比率恒等式，不是组件耗时瀑布图；区间为 descriptive task bootstrap。 |
| 5，7.2×4.65 in | 小幅 request 收益是否均匀、跨轮次一致？ | `evidence/rtx66/RAW_COSTS.csv`；`COST_SUMMARY.json` | 全24任务、48点、四轮全部保留；gen 22/24、request 17/24；round 2 约0.940。任务中位数 GM 与轮次 GM 不混用；不构造 session CI。 |

`output/FIGURE_INPUTS.json` 保存绘图数据、顺序和新增报告来源哈希；`output/VISUAL_DATA_QA.json` 将48点、六个区间和四轮回查冻结数据，并检查 PDF 字体、画布范围和无栅格图像。表3和表4仅显示精度由六位改为三位；计算与六张其余生成表不变。

图注与正文现在先给面板读法，再给主要观察与工程边界。Figure2的E donor已按绑定来源明确：C是ordinary N0，D/E是alternate cross recipe `E_k1_ub2`，两者均非后期phase-binding candidate。该澄清不改变保留的矩阵。原视觉prompt已完成并归档；本轮文字修改见 `RECONSTRUCTION_ZH.md`。
