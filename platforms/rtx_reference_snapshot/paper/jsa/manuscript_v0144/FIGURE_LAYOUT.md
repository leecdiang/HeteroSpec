# v0.14.4 图形与版式说明

视觉参照为作者提供的 ASV `40.pdf` 第 7–8 页，SHA-256 `85b1c624a0d500dbd7ded7d9b36af2b5db8aed3fc5317d50b6fb2bcc2c00c776`。使用其白底、衬线、细线、蓝／赭／绿及按证据功能组织 A/B/C 面板的惯例；参考 PDF 没有加入仓库。所有科学图为可复算的代码矢量图。

统一画布宽 7.2 in，跨双栏插入；面板标题约 10 pt，图内主要文字约 9 pt、辅助文字至少 8 pt。图使用 STIXGeneral 衬线，正文及补充使用相同 Times class 设置。蓝 `#426b8b`、赭 `#b07b43`、绿 `#3e725e`，配灰色辅助线、白底及少量浅色填充。颜色跟随跨图角色：蓝为目标／ordinary reference／case 内类别锚点；赭为 draft／speculation／alternate 与相对锚点的偏离；绿为约束／资格／条件边界；灰为连接、汇总比较和未知历史单元。R/M/C 分别为蓝／绿／赭，M/C 比较在不同 timer 和系统中保持赭色，conditional ceiling／必要预算保持绿色；不按硬件、timer 或速度正负改色。实心／空心、圈／菱形／叉及文字冗余表达差异。

| 图 | 读法与输入 | 保留的范围 |
|---|---|---|
| Figure 1，7.2×4.2 in | 目标／draft 状态所有权，query view `(d,q,h,1)→(d,1,h,q)`，role/phase graph controls；输入来自绑定 query/mask patches | projection/FFN 保持 batched；仅受支持的 Qwen3 non-flash、stream/shape；C 四框净距增大，括线汇集四开关，后续箭头两端留白 |
| Figure 2，7.2×4.15 in | 五个 categorical 2×2 关系矩阵：填色 tiles＋无向 =／≠ 连接；汇总比例条表示持续执行观察；RTX Natural Crosses、B570 CAUSAL_RECHECK 和 delivery report | 保留全部原数据；C donor=N0，两列都 UB1/r3；D/E donor=Alt.=`E_k1_ub2`，列 UB1/r3 与 UB2/r2。UB 与 reservation 同变；不是唯一内核原因；F 继续 UB128，并非隔离单块后效应 |
| Figure 3，7.2×3.85 in | 16 mask 全矩阵及 12 geometry cells | masks 3/7/11/15 通过，mask 3 仅 family 内 inclusion-minimal；joint k/UB panel 与 fixed UB 成本分开；实际最长 261；科学输入对象完全相同 |
| Figure 4，7.2×3.7 in | R/M/C paid paths 与六个保存 ratio/interval | generation/request 横轴范围明确；ratio identity 不是组件瀑布；task-bootstrap 为 descriptive；科学输入对象完全相同 |
| Figure 5，7.2×4.65 in | 全 24 tasks、48 points、四 request rounds | 相同任务顺序与 scale；七 request regressions、round 2 reversal 全保留；不创建 session CI；科学输入对象完全相同 |
| Figure S1，7.2×3.7 in | 同 target context 的 prefill→pending sample→bind→native loop；endpoint 1,150＋suffix 26＝paid raw 1,176；119/120 与 15/14 pairs | 原实现与 B570 COSTS_RECOMPUTED 绑定；不是 timing profile。missing old-N1 /400 round 1 不补零。共 30 formal candidate responses 的计数 |
| Figure S2，7.2×2.7 in | 实心圆／bar 为 saved measured estimates／intervals；空心菱形为 conditional zero-other-work ceiling；target-cut 预算 | 原 358H summary 与 full-precision historical appendix 绑定。固定 baseline/progress，conditional ceilings 无 CI。必要削减不是 achieved savings；180-row raw audit 仍继承 |

Figure 2 categorical cells 保留：

| 面板 | 第一 donor 行 | 第二 donor 行 |
|---|---|---|
| A，RTX HE/15 | 9147, 4199 | 9147, 4199 |
| B，RTX HE/25 | 1406, 1406 | 1406, 271 |
| C，B570 MBPP/72 | 320, 320 | 308, 308 |
| D，B570 HE/145 | 71465, 279 | 279, 279 |
| E，B570 HE/42 | 432, 1817 | 1817, 1817 |

Figure2 的蓝色选定首格 ID 为 case 内比较锚点，赭色表示不同 ID；相等连接为灰、不同连接为赭。四条无向连接仅表示相邻格相等／不同，不表示时间、因果箭头或 ID 距离。各 case 的锚点不被声称为 ordinary native reference。图 2C 的 N0 与 D/E 的 Alt. 均非后期 phase-binding candidate。绘制时对六个 B570 case 的 donor、当前 recipe、reservation 与导出矩阵逐项核对。

`provenance/FIGURE_INPUTS_V0144.json` 保存源哈希和绘图数据，`LOCKED_REVISION_ASSETS.json` 锁定 14 个 PDF/SVG 加八个 TeX 表。`revision_qa.py` 从独立读取的导出检查新图值及无损继承；`check_visuals.py` 同时检查原 48 点、六保存区间、四轮、16 masks、12 geometry cells 和全部七张 PDF 的画布／矢量文本边界。新增检查实际导出的 SVG 节点／关系／glyph、比例条、phase marker 颜色、48+4 点的位置与方向形状，以及 PDF 中 Figure1C 框／箭头净距和 R/M/C、speculative/conditional 数值的颜色。`SEMANTIC_VISUAL_REVISION.json` 保存初始／当前图哈希，`INITIAL_V0144_FIGURE_INPUTS.json` 保留七图科学输入对象作精确比较。具体页面视觉核验在 `output/VISUAL_REVIEW_QA.json`。humanizer 全文复读后重新编译并核验页面；该语言 pass 的七个 figure blocks 与图注保持完全相同。

补充材料采用与正文一致的双栏 serif 版式。12 个原表保留所有行、精度、标题和标签；宽表跨双栏，紧凑的 proxy lookup 保留单栏。目录不单独占页，S 编号独立且 30 个导航目标保留。正文页边距、字号与行距不变，补充使用相同 class 默认值。
