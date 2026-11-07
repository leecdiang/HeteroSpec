# v0.14.4 修改记录

本轮叠加最新英文编辑 #74，精确基线 `e6236d220a5123c691153f2558b8d4dc5d92b0c6`；新增独立目录，不覆盖 #70–#74 的既有工作。完整审稿见 `CROSS_REVIEW_ZH.md`。本次继续更新当前 Draft #75（初始 HEAD `92349e897de8fe66f282dd0121a5ec5d367b7000`），保持同一个 v0144 目录。

1. **Figure 2 小修。** C donor 写 N0；D/E donor 写 Alt.=`E_k1_ub2`；HumanEval 列写 UB1/r3 与 UB2/r2，图内及图注定义 output reservation r。消除 E 混指普通 donor／alternate recipe 的歧义。20 个 categorical cells、五矩阵和持续执行 0/72、18/72 不变。新版改为填色节点与无向相等／不同连接，直接呈现 current-path、retained-state 和 interaction 的不同结构；F 用汇总比例条显示持续执行观察，不构造时间曲线。图注对应更新。
2. **无损压缩。** 补充由 27 页改成与正文相同的 normal Elsevier 5p Times 双栏；目录紧接正文，宽表跨双栏、删去 longtable 重复表头／续页家具，原有内容不删。含两张新图后为 13 页，减少 51.85%。七节、23小节、30导航目标、12张补充表、原有科学信息／数值／精度／引用和 negative/missing findings 保留，编辑前文字可精确恢复。
3. **必要补充绘图。** S1 解释 B570 同 context 的 phase binding、单次 pending sample、endpoint 与 raw paid suffix，以及119/120和15/14pairs；S2 用 measured实心圆与conditional空心菱形区分358H原速度／区间和成本天花板，展示达到parity必要的target-work预算。都绑定已有来源，不增测量、不做虚构 timing profile。
4. **视觉协调。** 沿用 ASV 参照的 serif、蓝／赭／绿、白底细线、灰色说明和 A/B/C 面板；所有图为 vector PDF＋editable SVG。全部七图共用保留的 `visual_figures.py` 样式。Figure1C 四框横向净距 18.22 pt、纵向净距 15.79 pt；括线汇集四开关，箭头与后续节点净距至少 7 pt（原图画布尺度）。蓝色沿用目标／参考或 case 内类别锚点；赭色沿用 draft／speculation／alternate 与偏离；绿色沿用约束／资格／条件边界。Figure4/S1 的 R/M/C 角色一致，Figure5 两 timer 与 S2 的 measured M/C 比较同为赭色；速度方向继续由形状表示。两 PDF 不增加单独的全局颜色说明。
5. **全文语言优化。** 按作者指定 humanizer v3.1.0 的固定提交做两遍全文阅读；19 文件审阅，17 文件／63 段改写，清理机械过渡与重复收束。技术对比、条件范围和负面／缺失结果保留；数字、数学、引用／绑定命令、全部 inline table／figure blocks 与版式命令相同。声明和 Highlights 阅读后保留。见 `HUMANIZER_REVIEW_ZH.md` 与可唯一逆转的完整 edit receipt。
6. **可追踪交付。** 可携带的 #74 基线 receipt、no-loss audit、22图表 asset lock、26claims／28groups原行保留；CPU构建、空目录ZIP和flat source编译验证。初始七图科学输入对象逐项完全相等，183 个 protected 文件仍字节相同，八个 protected 图形资产按明确 receipt 重绘。默认构建锁定当前供给资产，不自动重绘。

新增内容为补充 S1 的 R/M/C standalone key、两图的引用／图注和 S7 当前构建说明；其余语言修改逐项记录，不增加科学结果。正文 abstract 220 words、六 keywords、五 Highlights、18条书目。

五角度交叉审稿认为现有 finite-scope 工程论证可以成立，但单一模型家族、同合同外部方法比较缺口和跨会话统计稳定性仍是主要风险。本轮未运行新实验，也未把重排当作科学加强。作者身份／声明／访问决定／文献最终状态保留待核。
