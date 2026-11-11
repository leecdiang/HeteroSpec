# RTX true-q8 experiment handoff

**Design only. No GPU experiment was run by this PR.** Read [PLAN.md](PLAN.md) for the full frozen protocol, stage limits and stop conditions. The executor must publish concrete source/input/job manifests before new outputs. This branch inherits #209 only to retain reconstruction materials; the new study is a native Windows RTX epoch, not a Linux runtime transplant. It can begin without waiting for #210 execution.

Expected main panel:16 roots x8 arms x8 balanced order blocks =1024 measured requests, plus128 primers. Qualification and equal-work diagnosis come first. New request ceiling2048; existing cumulative RTX request/row limits remain and must be reconciled. This is not a promise that the whole study fits before actual admission.

## 中文执行 prompt

请在我的 RTX 5070 Ti Laptop 原生 Windows 环境推进 HeteroSpec 的 true-q8 实验。先读取这个设计分支的 benchmarks/rtx_q8_transfer_20261109/PLAN.md，按完整方案执行，不需要等 A5000 的 #210；我希望回答清楚平台差异和宽度收益边界，不需要追求 k7 一定获胜。

1. 先确认实际连接的是 RTX 笔记本，不是 A5000 或其他机器。核对 #195 的 Windows 原始 R、真实加载的 DLL/模型/源码哈希，并结合 #209 的完整生成源码和 #62 的历史失败，完成零 GPU 审查。这里 q8 指物理验证宽度8，不是权重量化；k7 的调用宽度8但内部仍拆成 q4，不能算 true q8。

2. 使用独立的新结果分支和目录。保持 Qwen3-8B/0.6B Q8_0、C1024、F16 KV、noFA 和已资格验证的 Windows 数值后端。k3/k7 都用 reserve8，原 scalar R 不改，旧 reserve4 数据不混入。先落实真实宽度8的容量、完整 logits 所有权、切分、状态和生命周期，再通过全向量、KV/frontier、拒绝/全接受/bonus、cap/EOG、reset 及负例资格检查。不能通过就保留失败并停，不放宽标准。

3. 按 PLAN 做等工作量诊断：相同初始状态、相同8个 token、全部8行完整输出，对比两次 q4 与一次真 q8；分别固定 loop4/packed、真实 extent 内/跨界。4个固定开发来源、8个格子、4次配对重复，共128正式诊断和32预热。恢复成本双方都放在主计时外单列，输出物化成本双方都计入。profiling 单独计费，不混入正式性能数据。

4. 资格通过后，完成八臂 live 面板：whole/LOCAL × loop4/packed × k3/k7。预先冻结16个符合 PLAN 的新输入、cap96、prompt≤192 token、8个完整 Williams 顺序块，共1024正式请求+128预热。不要只测 LOCAL-packed，不按好坏挑输入，也不要观察结果后改 cap、换实现或删臂。原始任务池若不足，先报告并修改预注册，不能偷偷替换。独立 R 的新参考生成也收费。

5. 执行前核对本机最新累计预算。#195 的904/3072请求、557528/4000000保守行数只是历史快照。本轮最多2048请求，按 PLAN 分阶段，所有参考、预热、失败和profiling都算；总行数继续受原4M上限约束。先发布精确 job/row manifest、可用时段、实际资源预留和超时策略。不要搬用 A5000 的222请求余量或已经过去的周日/周一截止时间。资源不足就明确停在相应阶段，不牺牲正确性门槛。

6. GPU 正式任务串行，保留 AC/功耗模式、温度、其他进程和完整计时记录；不擅自改系统设置，不打断其他任务。按 PLAN 的四个主要 k7/k3 对比及独立次要机制对比，保留所有结果和配对根级区间；完整发布物理行数、接受率、尾部未消费提案、prefill/draft/verify/residual、加载预热和内存限制。cap96 面板不能直接当成 A5000 不同 horizon 的精确复现，不能用旧 M 数据宣称新的相对 M 加速。

7. 实现/资格与结果均保留完整 source bindings、原始记录、累计账本和失败版本，完成归档回读及离线重算后汇报：真正完成了什么、证据支持哪条论文结论、限制是什么、是否还有必要补实验。允许负结果结题。不要合并 PR、发布 Release、删除数据、改历史基线、改论文或顺带启动32B/B570。

## Validation of this design PR

The schedule and request/row arithmetic are checked offline. No native build, GPU qualification, memory admission or runtime result is claimed. Public readback of these documents verifies delivery only.
