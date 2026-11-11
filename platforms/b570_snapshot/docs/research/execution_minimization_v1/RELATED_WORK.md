# 最近工作与增量门槛

这是窄范围机制比较，不是完整新颖性搜索，也不构成 first/unique 证明。2026-10-05 重新读取 LLM-42 v2 和 Stage-Replay v1 的公开全文；MarginGate/Integer Alibi 的机制比较继承 #56 的已绑定全文检查。作者报告的结果未由本 PR 独立复现。

| Primary work | 已有能力 | 本路线必须额外回答 |
|---|---|---|
| [LLM-42 v2](https://arxiv.org/html/2601.17768v2) | 固定形状验证、回滚和状态修复以建立规定的推理确定性 | 能否删除live draft并保留一个已有原生数值路径，包括非参考输出？改变UB后与普通U2相等不是独立贡献。 |
| [Stage-Replay v1](https://arxiv.org/html/2607.28495v1) | 区分token重放/live state；通过对齐控制和双向整缓存交换检验donor对后续轨迹的充分性 | speculative verification调用、接受/回退与状态构造的关系，是否产生新的执行简化边界？重复“KV决定后续输出”不足。 |
| [MarginGate v1](https://arxiv.org/html/2605.30218v1) | 基于已付费当前margin的触发验证和KV修复，报告验证成本收益 | 此路线不提出新的margin门控或参考修复器。事后低margin不能作为免费预测特征。 |
| [Integer Alibi v2](https://arxiv.org/html/2608.13756v2) | 在规定W8A8相同操作数及累加界下排除一种误差源，并作缩放/重放控制 | 不把该整数精确性结论移植到Q8_0；本路线未记录对应runtime operands/dispatch。 |

还必须与本项目已有 RTX H 程序比较：H 已另行编排proposal与target，但保留live draft和共享数值执行。换接口、重做冻结或加完整数组比较不会自动增加能力。

合理的增量是：一种比已有H更小、输入合同明确的复现执行，在预先冻结的新配置上保留有意义的原生行为；或用受控反事实识别它为何只能在特定区域成立。成本优势和production修复是额外主张，不能由过程简化直接推导。

只观察“形状敏感”“前缀相同但状态不同”“参考一致率抵消”时，应把它们作为已知问题在本栈的实证结果，不据此继续投入新方法论文。
