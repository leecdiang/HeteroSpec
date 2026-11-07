# JSA v0.14.0 全文重构说明

论文现已按“在哪里约束执行一致性，以及修复后是否值得付费”组织为完整英文系统设计研究：运行事务与状态接口 → RQ1 局部诊断 → RQ2 实现与阶段资格 → RQ3 普通/匹配成本 → 工程决策与边界。独立 S1 补充材料保存详细协议、全部主要配对结果、历史合同、失败和缺失；S2 提供作者源包、图表代码与复算记录。

## 贡献如何改变

贡献不再是首次发现 numerical sensitivity、KV consistency、固定形状验证或回滚，也不把诊断包装成新在线算法。正文承认这些已有基础，落在三件实际工作：自然 state×current-recipe 与 own-path shams 的受控局部证据；实际 Qwen3 non-flash attention query-layout 改造及 phase dispatch/graph-reuse 接口；恢复资格后，以付费 R/M/C 对照改变工程选择。RTX、B570 的不同修复也不被写成一个跨平台通用实现。

RTX 实现把 query 列放到 batch 维，K/V 广播，mask 布局同步改变；投影、FFN、输出层保留批量计算。源码断言、支持宽度、捕获旁路、phase guard 和图复用标记均已在正文解释。四开关全部16个 mask 的资格矩阵显示 passing3/7/11/15；mask3 的“最小”限定为已测试家族中的包含关系，不是最少阶段的普遍定理。mask3 相对mask15 的1.003569×额外 generation 收益未过1.03门槛，仍完整报告。

## 补回和保留的证据

- RTX /15修复与/25回归、MBPP/304持续失败但输出改变，解释为什么 aggregate 相同不能说全体 no-op。
- B570 同状态单块即时72次/195事件均不改变决策，但冻结继续策略下18次/6任务下游改变；明确后续UB128块持续，不将其写成只扰动一块随后恢复路径的因果证据。
- RTX 与B570的自然交叉及shams；B570 /72两列相同是state control，HumanEval两列同时改变UB与reservation。
- 冻结后24个project-unused MBPP输入、384个正式请求，四条件各96合格；计时不混淆generation与resident request。
- 宽geometry输出失败，以及固定UB4更宽draft合格却更慢的反例；caller减少不等于micrograph或kernel工作减少。
- B570原closeout的1,456记录完成、局部正例、/72新输入失败和UB2候选失败；后来的phase-binding成本119/120及raw suffix全额费用。
- H1失败/后来的H2与replay闭环、ordinary U2 bridge、offline selector、pilot、V3终止/V4完成与host amendment、M4 metadata recovery、M4 Guard/oracle及358H target-work floor，各有明确去向。旧研究已完成的修复/closeout不再写成尚未完成。

## 收窄或澄清的主张

RTX resident-request为1.741569× ordinary、1.035071× matched；匹配无draft目标路径自身已有1.682560×收益。因此前者是完整部署改变，后者才是该目标路径上加入draft的增量。七个matched request任务回归和第二轮0.940220×反向保留。R是实际付费且合格的参考，不声称最快普通解码器。比率乘法恒等式不是attention/KV/同步/host成本分解。

RTX full-response equality、B570 first-EOG/cap128 endpoint equality与历史re-tokenized-text agreement分开。B570不改119/120：R/M/C各15完整配对，old-N1只有14；缺失payload、中断费用和unknown raw comparisons保持unknown。新CPU检查是export级复算；不能冒充完整私有归档审计。

M4固定策略与Guard分别约1.346894×、1.311387×，paired secondary Guard/Always latency为1.027076；不因“自适应”而宣称收益。两动作oracle的factor和实际latency reduction分别写清，不能升级为所有控制器的上界。358H prompt与pooled估计量、固定progress条件预算与实际成本分别报告，不宣称NPU或异构推理不可能。

## 还缺什么

作者真实身份、单位、通讯信息、CRediT、资助、冲突、简介/照片、declarations tool文件、正式数据与软件可访问位置、权限及最终AI声明必须由作者确认。所有作者最终科学/文献/语言核验尚未由本稿代为宣布完成。Editorial Manager实际附件槽与问卷未操作；没有投稿、合并或发布数据。

第二模型家族由后续独立任务补充。本轮已经完成当前证据下全文，并在阶段资格之后、付费成本之前安排自然插入位置；不等待它，也不写预期结果。当前限制仍是一家族、有限输入、指定图路径与计时环境；没有同合同最近方法实现对照、普适无损、stochastic sampling、并发吞吐或新的能耗结果。

验收记录分别说明133份实际读源的字节绑定、26份冻结证据与16份历史副本不变、数值复算、图件来源、干净构建、源包解包重建和最终逐页视觉检查。它们属于作者侧验证，不称外部同行评审或商业查重。
