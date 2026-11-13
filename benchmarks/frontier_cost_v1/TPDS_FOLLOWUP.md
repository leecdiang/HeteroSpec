# 对 PR222 审稿的响应：下一轮实验与论文证据闭环

## 固定稿件与公开状态

本轮已读取 [PR222](https://github.com/leecdiang/HeteroSpec/pull/222) 的固定 head
`e8a4981ef7db8f05cff7144fd4edc6e5a4109343`，包括方法、结果与评价设计。
它是新的 Draft 作者审阅稿，主题为 *Reference-Compatible Parallel Execution
for Quantized LLM Inference*。此处接受用户给出的逐页审稿作为设计输入；本轮
没有另做 PDF 视觉复核，不将其补充材料后两页写成已经审过。

本轮再次读取 [PR218](https://github.com/leecdiang/HeteroSpec/pull/218)，head 仍为
`4fe337a8ff349d547023f9dd60b8e114e5323207`，公开目录有 S1/S2、B2 的结果与
S3 的冻结准备资料，未见新的 S3 完成结果。旧 PR 正文中的“running”不是本轮
服务器仍在运行的证据。优先取得已注册 S3 的结局和完整 ledger，不另造一个
“完成”状态，也不把算子级 C/B=0.8528 转换为完整服务收益。

本轮对 PR222 head 的 GitHub Actions 查询返回 0 条 workflow run。这只表示
没有取得该 head 的 Actions 结果；作者包内本地测试记录不等于 GitHub CI。
本研究更新不修改 PR222 或既有 S3 的文件、计划和预算。

## 1. 强基线完整服务优先于继续扩模型

| 优先级 | 要回答的具体问题 | 需要的结果与判定 |
|---|---|---|
| P0：核实既有 S3 | 32B grouped 在 backend-internal loop 之上还有多少完整服务价值？ | 从已冻结 journal 核查独立 R、全部 bridge、退出状态、完整 planned coverage、资源/成本窗口和失败记录；只有资格通过且面板完整，才估计服务差值。若结果仍不可得，将 32B 定位为 typed transfer/feasibility。 |
| P1：同面板归因 | 1%–2% 是哪些阶段的变化？新控制或执行是否有独立贡献？ | 相同输入与交错顺序测 W-L4-D4、L-L4-D4、W-P-D4、L-P-D4；所有通用优化共享。逐请求记录不重叠的 prefill、verify、draft、state/output/host，核对 phase sum 与 resident total。应用 M 另保留同合同的固定对照。 |
| P2：真实请求正确性与 guard | 每个 recipe 的条件在哪里检查，失败如何处理？ | 完成下节表格的源代码定位、负例、完整请求与状态边界；不要只补一张没有可复算判据的概念表。 |
| P3：长前缀/长度分层 | 方法机会是否随自然前缀、crossing 频率或 prefill 占比改变？ | 在同模型、同后端、同固定容量内分层，再用相同前缀比较容量；同时保留 crossing 和 inside。容量与前缀不能一起改变后归因给单一因素。 |
| P4：同合同 runtime 对照 | 相对现代执行路径，收益是否仍存在？ | 先建立相同参考合同和观察窗口；无法保持旧数值参考的 serving 配置单独作为另一应用合同，不混入“保持 R 的加速”分母。 |
| P5：新 SD 路径 | 新前沿决策是否超越现有 short/lazy draft 和成本感知 adaptation？ | 原始参考下的合法 stage/outcome 成本、冻结因果策略与新 root 确认；controller × executor 消融以及所有 fallback/失败都保留。 |

S3 是已有 32B 强基线问题；本轮 8B cap16 请求诊断与 190-context 操作诊断
解决别的问题。三者不能互相继承资格或合并预算。长前缀、runtime 与确认集均
是后续设计，尚未编入本次两个固定可执行 profile。

### 同面板成本应怎样回答审稿

分别报告 packing 在 W、L 下的直接效应，cut 在 loop4、packed 下的直接效应，
以及预注册的交互项。主指标沿用 PR222 的 ratio-of-totals；root cluster 重采样
保留每个 root 的全部臂和重复。等 root 几何均值作为预声明的次指标，帮助检查
较长请求是否主导结论。不要把来自不同面板的 phase 平均值拼成一个成本分解。

对新前沿方法，基线必须已有 lazy-tail/cap 处理。若改变 drafter、graph policy
或 kernel，分别标成干预，不把所有差额归因于一个调度器。完整进程成本继续与
resident service 并列，初始化成本反转应保留。

## 2. Recipe / guard 表应交付什么

下表区分**当前稿件明确陈述的前提**与**下一步需定位/重放的证据**。它不是
所有 guard 已完成独立实现审计的证明。每行最终都应追加固定 source/符号、
执行 receipt 与未覆盖项，避免把有限测试写成任意 shape 的定理。

| 对象 | 当前稿件的前提 | 表中必须列出的具体 guard 与结果 | 必须保留的负例或边界 |
|---|---|---|---|
| CUDA Q8 projection | Q8_0 权重、F32 输入，保留四列 MMVQ 算术；分组 `[K,4,g]` | 哪些 tensor type/shape/stride/placement 可用；`q=4g` 的分组与 tail 路由；实际 dispatch 身份与输出布局 | q≤4、q8、多组/tail，非支持 stride/layout，不同 graph 条件；不能据当前 CPU q1 reference 推断所有 CUDA 合法性 |
| Mixed Q4_K/Q6_K projection | per-type scalar-column 算术，`[K,1,q]` channel grouping | 每类 tensor 的类型、量化器、dot/accumulation 与 layout guard；graph-level loop、backend loop、grouped 三条实现分别绑定 | Q4_K 与 Q6_K 分开；记录已见 mixed directions；算子与 full-model 资格分开 |
| Vulkan projection/attention | 受影响投影保留 F32 activation；phase-specific p021 QK/AV 路径 | phase/stride/dispatch、mask 物化与输出恢复的实际谓词；原 prompt producer 和 continuation recipe 分开 | 不支持的 stride、inside/crossing、q2/q4/q32；C1024 与 C4096 的实际分配分别验证 |
| 物理 KV 前缀 | 一条 dense、nonwrapping 活动序列；head 与逻辑前缀对应 | occupancy、position、sequence ownership、head、capacity、padding；extent 公式输入与生成 plan 对应 | holes、shifted head、wrap、capacity overflow、不同 extent 但同逻辑长度；非支持配置须在首次数值执行前拒绝 |
| 输出与状态所有权 | 原 requested-row mask 与同 resident owner；同步后在 scratch 复用前拥有向量 | output reserve 不等于 requested rows；initial/commit/terminal 的 vector 与 active KV；pending/correction/bonus、trim、reset | 首拒绝、全接受、CAP/EOG、p4 已验证但未物化、draft catch-up、同 token 不同完整向量、失败后不可继续复用半更新 owner |
| Graph/reuse 与回退 | key 含 recipe、逐行几何、phase policy 与外形 | key 构成及实际 build/reuse；unsupported-before-execution 与 failed-after-execution 分别规定 | shape 看似相同但 recipe/extent 变；reset 后重新 build；未执行前只可选另一个已获资格路径，执行失败后不能用原 owner 静默重试 |

结构上建议给每个 recipe 单列三列：**数学/组合前提、运行时检查、实际测试域**。
当前非 Flash、F16 KV、greedy、单序列、dense/nonwrapping 应写在支持域中。
Flash、量化 KV、paged/multi-sequence 等不能通过省略一个 guard 就获得原合同。

## 3. 长前缀与现代 runtime：按可解释的轴推进

先在一个已选定模型/后端建立新的固定容量资格，再比较真实短、中、长前缀。
例如 C4096 若获资格，可预注册 128–256、768–1024、2048–3072 token 区间；
这些只是拟议分层，当前 C1024 工具不接受覆盖参数来执行它们。固定输出上限、
同等完整 prompt producer 与实验顺序；不能通过重复 token 填充把人为 crossing
面板称作自然请求面板。将无法取得足够自然长输入的层保留为空，而非事后换任务。

先用开发层估计方差、合法计划差和 phase 覆盖，再按精度与资源目标固定新确认
root 数和全部 IDs。旧 16 roots、两条成本历史及本轮两个 APPS prompt 均已曝光。
每个请求记录真实 crossing 次数/类型、prefill/verification 占比、物理工作与
guard/fallback 次数；报告长度分层结果，不只给 pooled 5%。同一前缀的 C1024/
C4096 对照若可执行，则另回答容量效应，避免与前缀增长混杂。

“现代 runtime”至少区分两类比较：

- **同参考合同的执行比较：** 相同模型/词表、producer、数值路径、请求/状态
  边界和资源，比较强原生执行、短/lazy drafting、现有自适应控制与候选。
- **改变合同或 workload 的 serving 比较：** Flash、paged KV、batch/并发、量化
  KV 或不同采样路径若改变原 R，先明确新的参考与资格。它们可以回答部署价值，
  但不能替代第一类问题。吞吐与排队时延还需单独的负载/SLO 协议。

这一区分不是回避强基线。应明确哪些对照能保持原合同、哪些不能，以及这种
严格参考需求在哪些复现/回归验证或既有部署迁移场景中有实际价值。该应用价值
属于待论证的动机，不能仅由论文中的 numerical equality 自动推出。

## 4. 平台表、图与论文主张

平台表按每个测量部署分别固定 CPU/内存、GPU/VRAM、OS、driver/runtime、编译器
和 flags、source/binary/modules、模型/KV dtype、offload、attention、graph policy、
线程、context/output reserve，以及实际 power/clock policy。区分设置值、观测值
与 unavailable；不补写未采集的遥测，也不为本实验擅自改变功率或时钟。
小幅收益的重复应在相同资源状态下配对；记录可取得的时钟/温度/空闲显存与
并存进程状态，保留漂移与失败，不进行事后挑选。

图表优先改动清单：

1. 摘要/结果先给强对照下的独立组件收益，再给完整应用相对 M 的收益。
2. Fig. 5 补 W-L4-D4：先确认现有同面板第五个 contrast 的原始数据与区间；
   若已有合法数据，重绘无需新 GPU；若缺同面板分解，就将该部分列为待测。
3. Fig. 6 在图注直接写 Windows RTX，A5000 matched-history 另给身份与范围。
4. recipe/guard 表与平台表可以提升可复现性，但它们本身不是新的性能证据。
5. 补充材料后两页独立视觉检查仍开放；本轮未修改或重新排版稿件。

当前可支持的论文定位仍是“在指定参考语义下安全重组量化推理执行”的系统
方法。若要提升为约 5% 的新投机解码路径，必须另有强基线完整服务增量、合法
执行机制与未曝光配置上的证据。不能通过换标题、基线或分母完成这一步。
