# HeteroSpec v0.9.0 独立复评与下一步决定

2026-10-03。**本轮独立复评为两份 weak reject；不能报告为高把握 accept。** 现有有限结论经新的独立算术检查保持成立，决定性缺口仍是系统贡献的分量和实际诊断价值。本轮完成复评、只读源码核对和一项后续研究方案，没有修改、重新编译稿件或执行模型/GPU实验。

## 1. 新评审结论

| 独立视角 | 推荐 | 置信度 | 决定性理由 |
|---|---|---|---|
| 系统意义与近邻差异 | 3/6，weak reject | 4/5 | 完整前瞻复现有价值，但尚未展示诊断问题被解决、可复用的原因区分或更广的执行规则。 |
| 证据、推断与比较对象 | 3/6，weak reject | 4/5 | 数组、门禁和条件预算成立；失败的RTX容量级候选没有匹配实际forward/state历史，成功replay共享数值例程；有限结果的可迁移知识与实用影响仍偏弱。 |

两位评审均阅读完整主稿12页和附录17页文本，分别检查7页和8页关键渲染，并直接计算留存数组/成本记录。它们未读旧分数、旧review/meta-review、作者回复或对方意见；任务从独立上下文启动，中立rubric没有预设推荐。相同模型体系、相同材料和只有两份意见意味着这不是两个独立机构的评审，更不是委员会投票或接收概率。

v0.8.9的旧内部视角为系统3/6、证据4/6；本轮v0.9.0为3/6、3/6。**没有分数层面的改善证据。** 新旧不是同一评审人的配对打分，不能据此计算改稿的因果效果或真实接收率升降。v0.9.0的具体性、估计量对齐和叙事确有改善；新的读者仍认为这些改进不足以跨越研究意义门槛。

## 2. 哪些理由被缓解，哪些仍然决定接收

| 问题 | v0.9.0已有证据 | 本轮状态 |
|---|---|---|
| 完整预测不易理解其价值 | B570四条非参考后缀155个位置；RTX持续差异与单点再汇合；输入/移除依赖明确 | 有效缓解表达与评估问题。 |
| 358H指标和预算不同单位 | 原prompt-median→GM上界与16.28%/15.52%条件预算，保留独立pooled界 | 新算术检查一致；不是当前拒稿原因。 |
| M4控制活跃不等于收益 | Guard/Always为1.027076，双固定模式机会仅0.06915% | 正确、有用的负结果；没有新增policy优势。 |
| 复现器是否改变真实诊断任务 | 更少依赖及完整expected arrays已成立 | 尚无一次诊断定位、干预响应验证或修复回到native的闭环。 |
| RTX比较是否隔离必要执行信息 | 同cohort候选失败分布与replay成功 | 实际forward/state历史未匹配；无法排除更强target-only描述，不能推导history必要。 |
| 近邻之外的新系统认识 | 前瞻完整native输出预测 | 仍是有限同栈程序到输出的对应，冻结程序的严谨性不能单独承担贡献影响。 |

主审接受两份报告共同指出的核心缺口：需要一个有区分力的诊断任务，把“简化描述够用”推进到“它帮助判定了哪个执行因素，且在native上验证”。无需强求一个更快decoder或唯一kernel原因；但当前的用途描述还不能代替这个结果。

## 3. 有效性与覆盖边界

两份新实现均核对B570完整数组与fork、RTX A/B、358H处理记录和M4成本输入。关键结果一致：B570 72/72预测、60/72参考，155/151位置；RTX UB1/UB2 51/57、replay57/57、serialized GM0.677351且0/19更快；358H prompt-GM界0.837219/0.844840；M4 Guard/Always1.027076、Always/two-mode oracle1.000692。新结果不是新的样本或新置信区间。

两位均未发现新的material arithmetic/denominator错误或当前有限主张中的未支持因果/必要性断言。这个结论是已检查范围内的观察，不是完整科学原始记录审计。M4/358H direct-ID资格不能从cost-only记录重新认证；投影state-check booleans不是raw KV/sampler字节。原绝对时序、omitted资产、独立数值实现和logging-free性能没有新增认证。

M4 freeze-hash记录错误、RTX V3 endpoint-parser失败和V4 host-policy amendment仍保留披露及限制。证据评审建议在主文§3.1更直接写出V4物理host条件的例外。主文目前指向附录Q，附录Q.2已有实质披露；这是一项透明性改进，不是本轮新发现的致命有效性问题。

**下一版本可直接采用的范围句（Proposed，未修改冻结v0.9.0）：**

> The reported V4 completion used a disclosed pre-live fan-policy amendment after predictor capture; numerical candidates and output endpoints remained unchanged (Appendix Q.2).

该句应与下一次实质修订一起编译验收，不把加一句限制描述当成解决系统意义问题。不得将host amendment说成物理无影响已被证明。

## 4. 下一步选择：一个闭环诊断任务

推荐先准备B570上的**prefill阶段执行策略干预，经简单复现器预测后回到native确认**。理由不是已经发现prefill是原因，而是源码显示prefill调用结构与后续decode需要分别检查，现有第64个输出后的fork不能排除更早的历史影响。三个源文件已在固定内容提交逐字节核对；实际backend形状及新的phase-boundary state-transfer资格仍未知。

[DIAGNOSTIC_STUDY_PREPARE_ONLY.md](DIAGNOSTIC_STUDY_PREPARE_ONLY.md)给出：

- 固定四个已曝光差异案例及原24-task cohort中的20个回归控制，保留三重复的稳定性身份。
- 先核对资产、基线、same-partition sham transfer、sampler/pending/logits/KV与instrumentation输出资格；门失败则工程BLOCKED。
- 候选的R、T0、N0、T1、N1五条件，G0成立后计划360个完整数组；不把G0/pilot加入主分母。
- 唯一candidate在结果前冻结；先封存全部T1预测，再运行不导入未来ID的N1。实际target prefill改变与后续policy、caller规则、state-transfer机制的对照分别明确。
- 正结果、部分恢复、null、复现关系不迁移、工程失败均预先保留。没有参考恢复不称bug fix，没有计时对照不称节省调试时间。

**方案状态为PREPARE_ONLY，尚非执行就绪或新增实证。** 不假定动态UB setter可用，也不以旧恢复控制替代新的资格。下一阶段首先是G0工程准备；能否真正改变系统贡献判断取决于可识别的诊断结果及native验证，不能预设正结果或accept。当前实验保持CLOSED。

若该候选不能区分解释，应如实保留负结果；真正trace/state-matched RTX描述或single-block/common-continuation是另外的新问题，不同时启动多个扩展，不进行dense scan。应以一次新的、可检验的知识闭环判断收益，而不是继续收集模拟分数。

## 5. 冻结对象、来源与交付

内容提交 `01682f3b992a11b36b309fbd6c9e9950f1dc5d89`；tree `dee99576b4b346e383f8a482d0c0797441f21c4d`。四个审阅成品、reviewer实际读取的中立rubric/manifest、coverage与计算身份见 [FIXED_PACKET.json](FIXED_PACKET.json)、[REVIEW_COVERAGE_QA.json](REVIEW_COVERAGE_QA.json)。主稿10页正文+2页参考，附录17页；没有生成新PDF。

主审额外检查主稿p.3/4/9/10的原最终渲染、报告主张与留存计算一致性、三份源文件以及以下近邻/官方材料。两位的primary-literature覆盖分别写在报告，不冒称完整穷尽检索。旧全页build/font/anonymity/visual收据只在对象哈希一致时保留其历史身份；本轮是全文审稿与抽样视觉检查。

- [MLSys 2027 CFP](https://mlsys.org/Conferences/2027/CallForResearchPapers)：研究标准为novelty、quality、interest、impact；testing/debugging在范围内，正文10页、评审不必读附录。
- [Lossless but Not Free](https://arxiv.org/html/2607.17283v1)：consumer-runtime成本与batch-shape数值现象已有研究；本稿增量需由完整前瞻复现与新的诊断知识承担。
- [Correctness Forensics](https://arxiv.org/html/2510.22876v4)与[LLM-42](https://arxiv.org/html/2601.17768v2)：针对近邻的correctness/state/shape方法核对；不将诊断流程或shape-consistent运行本身认作首次发现。

两份原意见保持原文：[系统视角](SYSTEMS_ACCEPTANCE_REVIEW.md)、[证据视角](EVIDENCE_ACCEPTANCE_REVIEW.md)。原v0.8.9审稿、v0.9.0成果和科学冻结标签均保持原身份。现有Draft PR #51仅增加复评与方案及更新living status，不merge、release或conference submission。
