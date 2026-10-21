# 体系架构连接：实证接口，不抢做新Tensor Core

## 本PR的硬件问题

**可否把数值组织约束和物理验证粒度分开，并保留数据复用机会？** 状态形成是该边界的输入条件。研究单位是完整request、query/head、micrograph及共享K/V，不是特定题目某层的字节。

用户提供的硬件分析作为研究建议；本PR只承担真实trace与有限结构证据，不设计/综合新处理器，不以“提高接受率”为成功条件。功能参考保持、吞吐、接受长度分别报告。固定p/q时纯加速不必改变接受概率；新数值路径也可能增加错误接受，不能只数减少了多少拒绝。

## 必须拆开的五种“宽度”

1. 最大proposal k（本研究新k3）；
2. 实际verification caller的token行数；
3. 实际target micrograph occupied rows；
4. attention Q的query-column维度和query-batch维度；
5. 实际shader/XMX阵列的并发宽度。

QB中第4项可能是column=1、batch=q，而第3项仍应允许q>1。反过来caller=4而四个width1 micrograph不是并行验证成功。第5项没有硬件事件时UNKNOWN；不得用4或1直接填入XMX利用率。

## 从S2已有heavy请求输出一个中性trace

每个逻辑attention layer/event记录：slot、producer recipe、role/phase、caller ID、graph ID、occupied rows、Q/K/V/mask shape+stride+dtype、KV heads/query heads、key extent、logical positions、buffer/view ownership和有效生命周期；有限合法operand payload按内容去重。最多只存预先选定的早/中/晚层与第一组符合条件的verify，不搜索“最有差异”的层。capture生命周期未验证则只记录shape而不导出过期alias内容。

保存实际normal verification/acceptance/catchup/rollback的计数；不要为了生成trace强制候选、强制prefix或改实际分支。普通counts保留aggregate物理width hist；诊断trace耗时不进入request成本。没有新GPU独立trace预算，来自S2的40个已规划heavy请求。

`architecture.py`在规范化真实事件上核对逻辑与物理行数、GQA及有限KV供给场景。它假设每条event代表一层完整attention，而不是将PQ的每个子图误当独立整层；PQ子图需先按原始graph ID有据聚合。`source_kind=SYNTHETIC_TEST`的示例永不混入native统计。

## 能说什么，不能说什么

| 量 | 证据与允许解释 |
|---|---|
| micrographs/output、rows/micrograph、proposal/committed | 原生计数，描述物理工作组织；不等于shader launch数 |
| unique K/V value footprint | 从shape/dtype计算的逻辑payload，不是实测DRAM流量 |
| 一次供给与逐query供给场景 | 两种假设性逻辑字节需求；缓存、重取、bank冲突可能不同，不能叫实际上下界 |
| graph nodes、主机enqueue spans | 可定位软件图组织，不是已完成GPU组件时间 |
| shader名称、实际指令与归约序 | 未取得合格trace时UNKNOWN；FP16输入/FP32累加不能独自定义真实硬件算术 |
| occupancy、bandwidth、能耗、周期 | 本PR不测则NULL，不用总request wall倒推 |

Vulkan timestamps在API层可用，不代表现有runtime已经暴露正确、完成且可归属的timeline。本PR不为一个章节引入大型profiling改动；需要时另开隔离计划，不能混入正式计时。

## 架构研究的两个交接闸门

**必要性**：先比较PQ/QB和同k、同producer的SERIAL。若剩余代价主要可由软件fusion/调度消除，不强行提出新硬件。若全部路径仍width1，记录具体runtime/接口约束，不把它归咎为B570 XMX微架构固有缺陷。

**可证伪机制**：后续架构需明确独立query上下文、数据供给/共享、归约结果合并的具体实现，以及同计算/SRAM/带宽预算的强基线。不能把QB画成框图就称新架构，也不能把参考换成更高精度却说保持旧部署。

本trace只能支持固定已观测轨迹的资源分析。若候选架构改变数值和接受结果，原trace不再自动描述新控制流。没有实测组件占比，不代入Amdahl得到“全模型预测加速”；只可做明确假设的敏感性分析。

## 广度与止损

一期不买板卡，不依赖FPGA、Accel-Sim完整移植或黑盒Tensor Core逆向。不搜索逐层/head保护规则，不专门优化四个历史输入。24个未运行输入、2领域、3长度层检验是否存在跨内容的有用效果；这仍是一个model pair/backend的有限域，不是通用保证。

若只留下几个特定旧题的技巧、或者正确且全面变慢，结论应为本路线暂未展示系统价值。之后是否转做独立硬件研究由中性证据决定，不自动把负结果升级成新项目。
