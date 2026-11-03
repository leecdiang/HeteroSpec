# HeteroSpec 投稿定位：IEEE TPDS（2026-11-03）

**首要投稿目标：IEEE Transactions on Parallel and Distributed Systems (TPDS)。**
备选：Journal of Systems Architecture (JSA)。如最终贡献更偏编译/代码优化或体系结构，再分别评估 ACM TACO、IEEE TC。目标是研究完成度与领域契合，不是为了期刊评级反向塑造数据或声称结果已达 TPDS 标准。

## 核心研究问题

**Reference-preserving parallel execution**：给定预先指定、不可事后修改的量化部署数值参考，如何从真实模型图、KV/序列状态与后端数值执行条件推导相容的 query 分组，并保留参考允许的最大有效批处理，而非全部串行化、按输入特判或只优化一个已知反例？

当前方法候选由三层组成：

1. **Reference-requirement extraction**：从真实图、tensor shape/stride、cache occupancy、物理 KV extent、算术精度及实际 backend dispatch/placement 生成执行要求；不能用模型名称、输入 ID 或输出差异决定策略。
2. **Compatibility-aware grouping and lowering**：在已知约束下，对相邻相容 query 建组，QB 维持既有批量 projection/FFN 与合适 attention 路径。最少连续分组公式是局部性质，不等于全系统最优，也不是论文最主要创新。
3. **Backend mapping and stateful integration**：将后端算术与图复用身份、prefill/verification/rollback 状态联系起来；不把逻辑 mask 等价自动当成 bitwise 参考等价。

**主张的最终强度由实际转移结果决定。** 在预测尚未由 Qwen 原机实验验证前，称其为“共享 runtime 候选与已验证的 Llama 机制”，不声称已实现跨家族自动保证。

## TPDS 导向的论文核心贡献（需要有实证）

- **机制与方法，而非补丁集**：解释物理 KV extent、投影激活算术、算子放置怎样约束既定数值参考；用一套可调用策略从结构生成实际执行选择。
- **跨后端与跨家族的预测性迁移**：CUDA、Vulkan 两套实现引用相同分组原则；Llama 已完成的因果证据保持冻结。新增 Qwen 必须看到策略真实启用，并修复预先保留的失败路径；Vulkan 不得通过改走原本已成功的 P4T 单元代替 P1 修复。
- **并行收益与完整成本**：比较同候选 runtime 中 PQ/QB、target-only/speculative 以及既定 R；分离 prefill 与后续单 token 自回归 continuation 的解释，报告 query 宽度、边界触发、实际组数、并行损失/开销和每次请求的收益或退化。M/R 不是纯 QB 或 decode 并行增益。
- **可复现的研究产物**：共享 planner、backend mapping、结构决策实例、对照表和精简复算入口。全文主线应是问题→结构机制→方法→跨结构验证→成本/适用性，而非项目沿革与档案量。

## 与正在执行的双平台任务的关系

**RTX_PROMPT.md 和 B570_PROMPT.md 已由作者发送给两平台原机代理，并已开始实验。** 本文档不改动原 prompt、冻结 reference、已注册面板、实验日程、参数、判断门槛或两端工作树。GPU 实验继续原协议，结果通过独立 PR 交付并复核，再视真实发现更新论文与目标判断。

- RTX：结构驱动的 Qwen8B/14B 实际路径选择，保留 normalization placement 与前缀边界，验证不依赖模型名的前置预测。
- B570：主动启用规则，处理原 Qwen P1+PQ/QB 失败单元；保留原 P1、strict R、固定 k/placement 及 producer 状态比较。
- 双平台默认的少量未见输入与固定完整成本面板维持原计划，不为 TPDS 改成更大的测试或追求更好点估计。
- RTX PR162 的远端证据收口、Vulkan PR163 的既有证据分别独立于新增方法资格；不要把旧原机数据归给新的共享候选。

## 写作与项目验收标准

TPDS 的核心问题不是“能否通过所有审计”，而是**什么并行自由度被允许、为什么、如何自动识别，以及实际保留了多少收益**。下一稿至少用一个统一图展示 reference requirement→compatibility planner→backend lowering；用一个真实 Llama 边界和一个 **Qwen 预测并触发的迁移实例**解释方法。成本结果在主文展示完整请求和有代表性的 block/phase 信息；审计程序、失败历史与 delivery 放补充材料。

本轮工作完成后按成果判断：
- 如果共享规则在真实 Qwen 结构上主动解决保留反例，并有可解释的并行/成本收益：**按 TPDS reviewer 的要求重新审稿，准备首投**。
- 如果只证明老 Llama 修复、Qwen 新规则未触发或继续按模型名补丁：缩窄主张，不为了维持 TPDS 目标反复追测，重新考虑 JSA。
- 如果研究发现新的实质性跨结构约束：先做针对性的机制确认，再纳入共享方法；不把不相关的审计和样本扩张当作创新。

**投稿状态：目标已确定，尚未投稿，也不代表 TPDS 接收机会获得保证。**

## 当前依据

- [PR164：共享候选与新稿](https://github.com/leecdiang/HeteroSpec/pull/164)
- [实验计划与两平台 prompt](../../../benchmarks/reference_batching_transfer_20261103/PLAN.md)
- [研究判断与证据使用口径](REVIEW_AND_DECISIONS.md)
- [CUDA Llama PR162](https://github.com/leecdiang/HeteroSpec/pull/162)
- [Vulkan Llama PR163](https://github.com/leecdiang/HeteroSpec/pull/163)
