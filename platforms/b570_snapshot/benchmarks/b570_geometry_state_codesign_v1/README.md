# B570：状态形成与物理执行粒度的受约束协同

**状态：DESIGN_AND_CPU_TOOLKIT；native runner 未接入、未编译验证，新增 native process/request/forward 均为 0。**

这不是另一轮 KV 子集搜索。本研究检验：**能否将保持参考所需的数值组织，与获得硬件摊销所需的物理批处理粒度分离；在自然完整请求中同时获得参考资格和有用成本。** B570 是试验平台，不是创新点本身。

## 先读什么

- [PROTOCOL.md](PROTOCOL.md)：九臂对照、先小后大、未见输入与停止规则。
- [NATIVE_INTEGRATION.md](NATIVE_INTEGRATION.md)：已发现的实际源码阻塞、必须补的执行路径、前置准入与冻结。
- [ARCHITECTURE.md](ARCHITECTURE.md)：体系架构问题、计量等级、可以说与不能说的结论。
- [AGENT_HANDOFF.md](AGENT_HANDOFF.md)：交给 B570 agent 的完整工作指令。
- [SOURCE_LOCK.json](SOURCE_LOCK.json)：固定历史来源、当前读到的 PR 状态、主源文献。

## 核心选择

1. **参考不换**：主参考为原 stock-compatible ordinary UB128、capacity1、Q6_K/F16 KV、greedy/cap128 的完整 recipe；从 PR92/97 原始制品恢复其身份。A=UB512 不是为了让新候选通过而选的新参考。
2. **自然形成，不移植**：新候选从完整 prompt 开始，禁止 donor restore、投影注入、teacher forcing 和带着不合格 KV 中途换 reference kernel。
3. **两种 producer × 三种 consumer**：reference128 / bulk512 的 prefill 分段；MQ / PQ / QB 的 continuation 表示。另加两个 draft-free 匹配臂与完整参考，共九个臂。
4. **小试先行**：80 requests 可行性面板，不以“速度正不正”决定删样本。成功只允许申请下一阶段；没有实际 multirow batching 或合格组合，就停止移植，不追逐某个 shader。
5. **泛化必须新输入**：确认面板 24 个未见 prompt，2 类任务×3 个长度区间×4；四个已暴露 GSM8K 只做校准，不作为泛化成绩。
6. **不同实验职责隔离**：不改 PR104 的 RTX 计划；不恢复 PR105 待批准的 168 次采集；不新增其余层/head/token 搜索；不影响另一个对话的硬件研究。

## 已实现的 CPU 工具

```bash
python -B -m unittest -v test_toolkit
python -B protocol.py select --inventory INPUT_INVENTORY.json --exposure EXPOSURE.json --out HOLDOUT_SELECTION.json
# 输入只包括来源绑定与 direct IDs，不包括答案、logits、耗时。
# 将选择结果中的 panel 数组单独写入经审核的 HOLDOUT_PANEL.json 后：
python -B protocol.py plan --panel HOLDOUT_PANEL.json --selection HOLDOUT_SELECTION.json --phase confirm --out PLAN_CONFIRM.json
python -B protocol.py plan --panel SENTINEL_PANEL.json --phase pilot --out PLAN_PILOT.json
```

`protocol.py` 生成输入选择及请求计划；`contracts.py` 校验规范化输出、实际分段和计数守恒；`analysis.py` 保留不合格结果并禁止只对快速成功子集汇总；`policy.py` 给出冻结的、请求前选定的简单 recipe 路由。它们**不是 native launcher，也不能替代独立 raw audit**。归一化证据必须由经过源码绑定的原机适配器生成，并与原始 REQUEST/RESULT/identity/lifecycle 对照。P2的R在全部未见输入上使用原始runtime，不以四题通过的新reference shadow代替。

`examples/` 只有待填的接口/准入说明，`test_toolkit.py` 的输入全部是合成测试；没有将假 prompt 或假性能混作实验。

## 执行级别与预算

| 阶段 | 原机工作 | 上限 | 当前状态 |
|---|---|---:|---|
| P0 | 来源审查、隔离移植、CPU 测试、执行 F0 | 0 native starts | 可先开展 |
| P1 | 原始参考8次＋影子8次＋八候选64次 | 80 requests /80 processes；7200s；4GiB；无暖机/重试 | 原机集成及执行 F0 审核后 |
| P2 | 24 未见输入×9 臂×4 时间块 | 864 正式＋864 暖机=1728 requests /864 processes；43200s；8GiB | P1 合格且作者 GO 后另注册 |
| P3（可选） | 两个已捕获输入×q1/2×MQ/PQ/QB×2 重复 | 24 operator starts；1800s；1GiB | 单独批准；不阻塞 P2 |

这些是不同的先验预算，不自动全部执行。若全部获准并完成，**本新研究最多 1808 个模型请求＋24 个 operator starts**；旧 PR105 的 1 个失败请求、127 decodes、12.438s 另外保留，不重置、不充当本研究 control。请求数不等于 forward 数。

## 什么样的结果才值得继续

我们需要端到端、未见条件的证据，不是另一个仅对 /1248 有效的技巧。若新组合在 P1 不能保持参考，或没有真实 multirow 工作组织，不进入大面板。若 P2 的效应只留在已暴露输入、只有极窄长度区间，或加入状态约束后的总成本全面劣化，报告边界并停止，不追加掩码/题目搜索挽救故事。

本研究可提供 architecture-aware runtime / 硬件—运行时协同证据。没有 RTL/PPA/周期精确模型时，**不称新硬件架构或新 ASIC**。也不把 24 新输入、单模型、q≤2、ctx1024 说成普适 LLM 服务。

## 架构研究的接口，不是新硬件结果

作者补充的弹性验证单元方向已纳入ARCHITECTURE.md。本任务输出真实工作粒度与状态来源，另一个研究负责明确的参考算术DAG、上下文/共享buffer/合并控制、周期或RTL。两者使用同一来源边界，但无需互等。

`architecture.py`区分正常请求成本、原生micrograph、未知dispatch/DRAM/XMX、假设下界。未知字段保持null，禁止由图数或logical tile字节估计冒充实测硬件参数；固定轨迹模拟不能直接代表会改变接受决策的新数值实现。

**交付级别**：这是一套设计＋CPU规划/分析工具，不是已编译的B570 QB执行器。P0的native移植、真实serializer、raw auditor、executor/F0是原机agent的主要工作。不得原地移除PR101 target-only guard假装完成。
