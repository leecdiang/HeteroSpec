# v0.14.5 收尾审阅

基线：PR #75，`92b08a0ffab2ca08c835b411d9d7478ccd57603b`。本轮完成标题、摘要与主线收束，以及单份 arXiv 合并稿准备。

| 位置 | 收尾决定 | 证据边界 |
|---|---|---|
| 标题 | Paid Cost 改为 Measured Cost；两份 PDF 的标题和元数据对应 | 保留 reference-preserving、consumer systems、diagnosis、repair scope |
| 摘要 | 220 → 204 词，聚焦诊断、约束、资格确认和成本 | 保留 24 项有限资格确认、三个请求对照、七项回退、一轮反向、qualified-but-slower 和 Qwen3 范围 |
| 引言贡献段 | RTX 为实施/成本主证据；B570 为机制和较慢反例；M4/358H 为辅助边界 | 不把不同输出合同或计时域合并成硬件排名 |
| 结论 | 总结相同主线，明确保留三个证据缺口 | 不宣称跨家族修复、外部方法优势或独立会话稳定性 |
| 补充材料 | 同步标题、版本，仍为 13 页正常双栏 | 内容、表格、图、来源绑定保持原样 |
| arXiv | 正文加补充形成 24 页单份 PDF，并提供对应源码 | 沿用已发表 v1 署名；公开稿保留真实 AI 辅助及访问边界说明 |

三项请求比值有不同分母：1.742 是 speculative 相对 ordinary 的速度；1.683 是 draft-free matched 相对 ordinary；1.035 是 speculative 相对 matched。它们近似满足乘法关系，不能相加；1.035 不是跨任务、跨会话的稳定保证。摘要省略的 generation 1.170/1.169 在 §6 与表格中完整保留。

按用户指定的 [humanizer v3.1.0](https://github.com/blader/humanizer/blob/225a6f39ac85f76ee48dbad772ea4abe4ed6c9d8/SKILL.md) 对收尾草稿进行第二次对照阅读。保留必要的技术区分及限定语，减少罗列。原 19 文件、17 修改文件、63 段 humanizer 记录完整保留；本轮另记四个 TeX 文件的逐段前后文本。自动检查先恢复精确 v0.14.4 文本，再执行原 humanizer 与科学检查。

第二次阅读核对了 ordinary greedy reference 的定义、局部 cross 与完整输出资格确认的差别、RTX full-response 与 B570 endpoint 的合同差别、四开关族内最小性、project-unused 的有限含义、比值分母、task/round 反向、宽 draft 负面结果和历史辅助案例。没有新增定理或实验数据。

Figure 1C、Figure 2 和补充图继续使用 #75 最新资产。七图 PDF/SVG 与八张生成表共 22 个文件逐字节继承，不会退回旧图。蓝/赭/绿的 target/reference、draft/alternate、constraint/qualification/conditional-bound 角色保持统一。

三项后续研究均保留在正文限制和结论中：第二家族、同合同外部方法比较、独立会话稳定性。本轮是同一审阅者的逐项交叉检查，不冒充多位独立审稿人的共识。署名和声明的交接见 `ARXIV_UPDATE_ZH.md`。
