# v0.14.4 修改记录

本轮叠加最新英文编辑 #74，精确基线 `e6236d220a5123c691153f2558b8d4dc5d92b0c6`；新增独立目录，不覆盖 #70–#74 的既有工作。完整审稿见 `CROSS_REVIEW_ZH.md`。

1. **Figure 2 小修。** C donor 写 N0；D/E donor 写 Alt.=`E_k1_ub2`；HumanEval 列写 UB1/r3 与 UB2/r2，图内及图注定义 output reservation r。消除 E 混指普通 donor／alternate recipe 的歧义。20 个 categorical cells、五矩阵和持续执行 0/72、18/72 不变。正文只更新相应图注和 donor 描述；其余四图不重绘。
2. **无损压缩。** 补充由 27 页改成与正文相同的 normal Elsevier 5p Times 双栏；目录紧接正文，宽表跨双栏、删去 longtable 重复表头／续页家具，原有内容不删。含两张新图后为 13 页，减少 51.85%。七节、23小节、30导航目标、12张补充表、所有原文／数值／精度／引用和 negative/missing findings 保留。
3. **必要补充绘图。** S1 解释 B570 同 context 的 phase binding、单次 pending sample、endpoint 与 raw paid suffix，以及119/120和15/14pairs；S2 用 measured实心圆与conditional空心菱形区分358H原速度／区间和成本天花板，展示达到parity必要的target-work预算。都绑定已有来源，不增测量、不做虚构 timing profile。
4. **视觉协调。** 沿用 ASV 参照的 serif、蓝／赭／绿、白底细线、灰色说明和 A/B/C 面板；所有图为 vector PDF＋editable SVG。新图、Figure2 和正文其他图共用原 `visual_figures.py` 样式。
5. **可追踪交付。** 可携带的 #74 基线 receipt、no-loss audit、22图表 asset lock、26claims／28groups原行保留；CPU构建、空目录ZIP和flat source编译验证。

额外文字只有补充 S1 的 R/M/C standalone key、两图的引用／图注，以及 S7 对当前构建方式的准确更新。正文 abstract 214 words、六 keywords、五 Highlights、18条书目保留。

五角度交叉审稿认为现有 finite-scope 工程论证可以成立，但单一模型家族、同合同外部方法比较缺口和跨会话统计稳定性仍是主要风险。本轮未运行新实验，也未把重排当作科学加强。作者身份／声明／访问决定／文献最终状态保留待核。
