# JPDC重构证据摘要：现代基线竞争边界

用途是供用户重构稿件并审阅的证据索引，不是已经修改的论文或投稿材料。未提交期刊或arXiv。最终稿、作者及投稿信息须另行确认。

## 可以采用的已测结论

1. PR237在RTX5070 Ti Laptop GPU上，复用一个真实首层q8输入(K=M4096,N8)，比较旧packed B与固定上游0fb8f157的提取few-row device实现U。两臂resident、普通launch/PDL0等价、graph OFF。每边界12对交替顺序，每batch5次，全部48样本保留、48批完整回检通过。
2. 含量化配对U/B为0.612924，区间[0.607906,0.618665]，算子时间下降约38.7%；仅投影0.582391，区间[0.578649,0.585872]。两边界12/12对U更快。这是同一输入/短会话内的探索性数据，不是跨输入总体估计。
3. 原C和C1各自在不同会话慢于B，负结果保留；C1同时改变组调度与跨组寄存器复用，不能把C到C1差异归因于occupancy。PR237及C1实际occupancy/L2/DRAM均未测。
4. 本轮e12补充了完整上游产物、公共API符号及dispatcher/graph/PDL/计量边界的静态证据，公共API链接PASS，完整运行NOT_RUN。新增GPU调用0，不产生新的性能或数值结论。

## 必须并列呈现的数值合同

|合同|对象与结果|不能写成什么|
|---|---|---|
|旧参考保持|B完整Q8_1和全部输出逐位重放PASS；U不等价|不能写U在相同逐位合同下替代B|
|PR235原U CPU-RN合同|10个量化q不符，原资格FAIL，不计时|不能以新合同事后把旧FAIL改PASS；不是已证上游bug|
|PR237新独立U合同|固定PTX近似语义的joint inverse允许集合、完整q/scale及double输出界、两次raw确定性，GPU和独立CPU复核PASS|不是CPU RN天然等价GPU fast-math；900块多witness，不是唯一硬件inverse oracle|

U相对B：24个逻辑q、1024个scale和32766个输出float位模式不同；相对L2误差0.0002370446，最大绝对差6.5844506e-05。一般正确性测试、argmax一致或容差通过均不替代逐位合同。完整差异CSV在PR237运行审计包中。

## 现代基线表应如何分层

|层次|当前证据|稿件应标注的范围|
|---|---|---|
|旧参考保持的packed B/C/C1|已测算子及负结果|实现取舍与参考保持约束；不是现代最强默认后端|
|固定上游提取few-row U|PR237数值与配对PASS|不同数值合同的现代算子参照，限定PDL0/graph OFF、resident、单输入/会话|
|完整固定ggml-cuda backend/dispatcher|已有编译、现e12 API链接PASS，运行资格/计时NOT_RUN|未完成比较，不能填入38.7%作为默认后端收益|
|完整默认上游/模型服务|NOT_RUN|不能称端到端强基线已覆盖，不能外推请求、k3或普适5%|

上游已有cp.async权重staging、MMA tile和多列复用。一般权重复用不是足够的新颖性；本输入U明显更快意味着必须收窄“优化先进性/强基线”的主张。当前证据更适合陈述数值合同约束下的实现取舍、审计边界和负结果；能否支撑整篇稿件贡献仍需结合已有系统级数据审阅，不能靠这个单例补出系统收益。

完整现代默认比较缺口有具体位置：MUL_MAT内部D4量化buffer私有、完整graph的direct/capture/replay未接预算、公共event禁用计时且stream私有、新DLL/base未纳入旧stage身份。它们不是GPU不支持，也不是上游性能差；本轮按合理成本收尾，没有继续搭建新框架。

## 5%应如何处理

不再以追求5%为本轮目标。PR237的Amdahl公式只可作条件分析：若未来保持旧参考的实现达到r=0.612924，则new/old=1-f+fr+h；h=0时5%下降要求f≥12.9174%，h=1%要求约15.5008%。同请求f/h未测，U的不同合同速度也不保证可迁移到旧参考候选。不得把跨会话、不同平台或首层捕获prefix时间拼为实际成本栈。

## 未完成项与收尾决定

- 完整上游默认backend/dispatcher实际few-row选择、数值资格、graph/PDL配对时间：NOT_RUN。
- 完整同请求阶段成本、跨输入/平台代表性、实测服务改善：NOT_MEASURED/NOT_RUN。
- 实际occupancy、L2/DRAM、功耗/时钟：NOT_MEASURED。
- 原4096全生命周期物理launch硬合同：NOT_CLOSED；PR237的400及本轮500授权只涉及显式应用调用。
- 本轮不开发C2，不执行PR237候选，不扩展服务或大面板，不改旧基线。

推荐在重构的实验表中直接保留这些空缺和限定语；若稿件必须声称完整现代默认后端竞争性，该主张目前没有证据，应删去或明确列为未完成比较，而不是用提取算子替代。

原始结果入口：[PR235](https://github.com/leecdiang/HeteroSpec/pull/235)、[PR237固定结果目录](https://github.com/leecdiang/HeteroSpec/tree/c8e5ea070ac393d7513903e0ec261dfce4554a49/benchmarks/rtx223_e11_u_contract_20261113)。本轮数据仅为SOURCE_ARTIFACT_BINDING.json、REUSE_VERIFIED.json、link-only日志、只读现场摘要及0消耗BUDGET.json。
