# HeteroSpec：收益预算、强基线与热路径成本审查

本文件只分析冻结仓库数据和源码。没有新增模型请求、GPU实验、生产源码修改、提交或推送。分析可用 Python 标准库复现，不依赖 GPU。

## 结论

独立四列组 packing 已证明在旧 graph-tile+concat 路线的部分输入上有收益，但尚未证明超越 backend-loop4。下一步应先建立真实强基线，再用净服务预算决定是否继续。不能把 23→2 次 kernel 发射直接翻译为加速比，也不能把 #177 的条件样本当作自然总体。

若目标是 5% 端到端节时，当前证据对不同生命周期给出完全不同的必要条件：

- #171 四个自然输入的 prefill-heavy 服务，若以已 packed 的 newWB 为起点，整个 prefill 占平均服务 65.23%。即使所有 prefill 都可优化，也至少需要再缩短 prefill 7.67%；若额外安全成本为服务时间的 1%，则至少需要 9.20%。真正 packing 可触达的算子只是 prefill 的子集，实际要求更高。
- #174 32-root 文件缓存命中服务，receipt→append 只占平均服务 20.99%，且已经包括文件/index/reset/lookup/import。即使将这一整个区间视为可优化，也需要缩短至少 23.83%；加 1% 服务开销后至少 28.59%。这只是宽松下界，不能从累计 import 时钟中推导纯 GPU append 成本。
- #177 条件池的 WB-rechunk，完整且已同步的 append 占平均服务 19.62%。要达到 5% 服务节时，整个 append 至少缩短 25.49%；加 1% 服务开销后至少 30.58%。如果新机制只触达 append 的一半，所需该部分缩短比例还要翻倍。

5% 只是可选工程目标，不是 TPDS 的通用接收标准。以上是必要条件/敏感性计算，不是承诺能实现。

## 1. 固定证据与复现

- PR171：`371223b696bb805030c29f04e39eb17b57fb2ebb`。
- PR174：`aa7ff4e64752be3de0d7974febbce453ae3a96c0`。
- PR177：`610fd3a364bec6e8a3881ef666bedacd2035679a`。
- PR179：重新检查最新 `8005cf01b9b7736d77e4e0c5dc3ecb2da2c29603`。其 `native_checkpoint.hpp` 与早先 `d694011...` 字节相同，Git blob 均为 `2358590d3ad3f9a61f897852075901e03b1d29c7`。

运行：`python analyze_payoff.py --out analysis.json`。

脚本校验 `sources.json` 所列文件 SHA256；读取原始 #171 的 36 个正式服务记录、16 个捕获算子描述符和单独的 profile；读取 #174 官方 phase summaries；读取 #177 的 48 个正式记录并逐条核对三个不重叠阶段之和等于服务时间。所有来源 URL、文件路径、冻结版本与摘要均在 source manifest。`data.json`是仅保留本分析所需字段的派生投影，不是新数据；`build_inputs.py`校验原始下载SHA256后可逐字节再生该投影。脚本不依赖头条均值手工抄录，也不做跨阶段几何均值相减。

主要来源：
- [#171 原始服务记录](https://github.com/leecdiang/HeteroSpec/blob/371223b696bb805030c29f04e39eb17b57fb2ebb/benchmarks/rtx_operator_frontier_v1/execution/evidence/service-cost.json.gz)
- [#171 算子重放记录](https://github.com/leecdiang/HeteroSpec/blob/371223b696bb805030c29f04e39eb17b57fb2ebb/benchmarks/rtx_operator_frontier_v1/execution/evidence/operands.json.gz)
- [#171 单独的 CUDA profile](https://github.com/leecdiang/HeteroSpec/blob/371223b696bb805030c29f04e39eb17b57fb2ebb/benchmarks/rtx_operator_frontier_v1/execution/evidence/operator-activities.json.gz)
- [#174 计时口径与汇总](https://github.com/leecdiang/HeteroSpec/blob/aa7ff4e64752be3de0d7974febbce453ae3a96c0/benchmarks/rtx_prefix_reuse_v1/execution/evidence/DETAILS.json)
- [#177 不重叠阶段原始记录](https://github.com/leecdiang/HeteroSpec/blob/610fd3a364bec6e8a3881ef666bedacd2035679a/benchmarks/rtx_rechunk_discrimination_v1/evidence/ANALYSIS.json)
- [#179 checkpoint 热路径](https://github.com/leecdiang/HeteroSpec/blob/8005cf01b9b7736d77e4e0c5dc3ecb2da2c29603/src/reference_batching/native_checkpoint.hpp)

## 2. 不能重复计算的旧收益

在 q32 整除、无 fusion 的已研究图形中：

1. graph tile：8 个 quantizer + 8 个四列 MMVQ + 7 个 concat，共 23 次发射。
2. backend-loop4：预期 1 个 wide quantizer + 8 个四列 MMVQ，直接写最终输出，共 9 次。此处是源码机制预期，尚不是实际 profile。
3. packed：1 个 quantizer + 1 个带 8 个独立四列组的 MMVQ，共 2 次，已在捕获描述符上观察。

因此与强基线比较的剩余问题主要是 8→1 个 MMVQ 的调度、资源使用、执行重叠和真实权重流量，不是再次领取已经由 loop4 消除的重复量化与 concat 收益。一个 grid.z 维度不证明每份权重只从 DRAM 读取一次，多个 CTA 仍可能重复读权重。需要 DRAM/L2 实测，而非从图形维度猜测。

#171 8B q32 独立算子干净重放，单位 μs：

| 算子 | tile | packed | 节时 |
|---|---:|---:|---:|
| Q | 172.4 | 150.2 | 12.88% |
| V | 67.1 | 67.5 | -0.60% |
| K | 68.4 | 45.9 | 32.89% |
| attention output | 173.7 | 148.2 | 14.68% |
| FFN gate | 745.3 | 681.7 | 8.53% |
| FFN up | 730.7 | 688.9 | 5.72% |
| FFN down | 759.1 | 735.4 | 3.12% |
| vocabulary output | 8864.1 | 8542.4 | 3.63% |

Q 的 q8 干净重放反而为 47.9→48.7 μs。每条只有三个 post-initial 样本，不能当稳定微基准分布。

独立 profile 中，q32 Q 的 tile kernel 总和分为：量化 7.455、MMVQ 145.569、concat 13.246 μs；packed 为量化 1.792、MMVQ 137.439 μs。这个旧对比的差额有相当部分来自 loop4 同样试图消除的工作。但不能以相减法预测 loop4 耗时：wide quantizer、输出布局、发射时序、cache 状态及 profile 干扰都改变了。

对 output.weight，profile 中 tile concat 本身为 561.468 μs；其去除不属于 packing 相对 loop4 的独占贡献。也不能把各算子的表格乘层数相加预测自然服务：真实输出行选择、宽度、层内 shape 和调度不同。

GPU kernel sum 与 CPU submit/sync 墙钟不相加；干净时间与 profile 时间保持分开。V 的 profile 总时长下降而干净墙钟没有下降，正是不能拿 kernel 数或 profile 单次记录代替端到端结果的例子。

## 3. Amdahl 预算与实际作用域

设同一个已合格强基线请求耗时 T，其中机制真正能触达的临界路径工作为 E。该部分缩短比例为 r；新增安全/绑定/物化成本为 G；一次性资格成本为 C；实际合法复用 N 次；故障概率 p，额外失败恢复成本 R。

净节省：`Δ = E*r - G - C/N - p*R`。

净服务节时率：`Δ/T`。若 phase fraction 为 f、机制只触达 phase 的比例 a，则 E/T=f*a。

要达到目标 δ，必要条件为：`r >= (δ + G/T + C/(N*T) + p*R/T)/(f*a)`。

若右侧≥1，该范围内机制即使清零可触达工作也不能达到目标。若每次扣除热路径和失败成本后的节省≤0，则无有限资格回本次数；否则 `N >= C/(E*r-G-p*R)`。不得沿用 #174 的 2038.78 s 校准成本作为尚未实现的新资格成本。

下表用算术总时长之比支持平均延迟预算，避免把阶段几何均值当作可相加分量。所有优化假设均乐观地将整个所列区间视为可优化。

| 冻结样本/起点 | 平均服务 s | 可优化区间的宽松上界 s | 占比 | 假设整个区间缩短20%时的服务节时上界 | 再扣1%服务开销 |
|---|---:|---:|---:|---:|---:|
| #171 newWB，整个 prefill | 3.426920 | 2.235228 | 65.23% | 13.05% | 12.05% |
| #174 WB-cut，receipt→append | 3.011222 | 0.631938 | 20.99% | 4.20% | 3.20% |
| #177 WB-rechunk，整个 append | 3.738973 | 0.733528 | 19.62% | 3.92% | 2.92% |

这些数字不表示 packing 能让整个阶段缩短20%。loop4 之后剩余 eligible kernel 的真实占比 a 尚未测得，不能赋值1作为预测。

按论文常用的逐根几何延迟比算，同样将 #177 每个记录的完整 append 人为缩短20%，对应几何服务节时仅 3.34%，不是上表的算术均值3.92%。脚本同时给出两种口径，不能互换。原始 #177 的实际 rechunk/QB 几何服务比0.994379和均值配对节时24.012 ms也不是这个新机制的效果。

#171 newQB 相比 oldQB：原始配对均值服务节省124.453 ms，prefill节省114.256 ms；原始几何服务比约0.959963（4.00%节时）。四个prompt长度为125/322/386/532，输出124或128。所有 k3 verify caller_rows均为4，packing门槛≥8，所以这不是 verify 加速证据。相对更强的已 packed newWB，新QB反而更慢。

#174：正文中的 import_s 是未额外同步的累计 receipt 时钟。worker仅在每次 decode后同步；不能从0.631938与0.463064相减宣布纯 append=0.168874 s。安全的当前预算是包含import的宽松上界。整个 receipt→append 清零的理论服务加速上限也仅1.2656×，真正 packing 上限更低。

#177：新加的 import-ready 和 append-done 都显式同步，三个 disjoint phase逐条相加等于service。WB-rechunk各root append占服务的比例按root均值为：37.50%、7.06%、8.22%、7.71%、12.65%、44.32%、5.59%、8.57%。长append405/521 tokens与短append34–90 tokens不是同一个收益机制窗口。特别是短append34的root，整个append仅5.59%；额外1%服务成本后，即使将完整append清零，也达不到5%服务节时。

## 4. Cache-hit、长短prompt与输出长度

需要按部署分布而非挑选最好样本来定义目标：

- miss/长prompt/短输出：prefill占比可能高，最值得先测，但#171不是完整生产分布。
- hit/短append/长生成：前缀计算已经被命中消除，剩余 q1 自回归生成和import可能主导；现有≥8列packing触达范围很小。
- hit/长append：仍有可打包新增tokens，但历史KV长度、q32尾部、图复用和边界切分分别影响成本。
- q≤4或k3 verify：当前packing没有路径收益；任何额外guard都是负担，除非另一个明确机制节约成本。
- KV granule/对齐：#174 granule1的623/9888个q32 calls跨边界；granule32的输出盲情景没有跨界，但它不是已测部署，不能据此改写原始结果。

对于同一部署、同一请求分布，可用：`E[T]=(1-h)*T_miss+h*T_hit` 和相同的节省混合式，h为实际hit概率。前提是miss/hit各自来自可比较的冻结测量；必要时再按append/output长度和residency分层。

禁止把#171的miss-like speculative服务与#174 target-only hit服务混成一条实测hit-rate曲线。#174 empty-cache控制只含原panel首8个prompt、另一生命周期，不能将3.803 s空缓存几何均值与32-root的3.002 s命中几何均值直接用于全流量估计。

#177有6,423paths/2,596roots；去除既有暴露后2,552个root代表中只有130个符合schedule差异条件，约5.09%。八个root是从这个条件池抽取。不能用八个条件root的均值替代2,552个root，更不能乘一个5.09%比例就宣称生产收益，因为总体请求权重、频率和其他root耗时未给出。它只诊断机制，不救回#174的AUTO null。

## 5. #179 的成本不是常数级guard

最新8005cf01的checkpoint owner仍执行：

1. append前 `serialize(context)`，同步、分配vector、导出完整state并比较。
2. 每个token `batch.logits[i]=true`；逐行读取并复制完整词表。
3. append后再次同步和完整state序列化。
4. `NativeCapsule next=current_`、`current_=next`和`checkpoint_=next`涉及拥有vector的值复制，不能当成指针换名。
5. 失败时先等待旧context，再创建fresh context、导入checkpoint、再次序列化readback验证。

vocab=151,936来自#171捕获描述符。q32全行logit payload为32×151936×4=19,447,808字节，即18.546875 MiB。这只是payload大小，不是实测PCIe流量、峰值内存或耗时。所有行还可能导致本来不需要的output projection；应实测而非用该payload反推GPU时间。

这里有两个不同合法合同，不能偷换：

- 若合同要求每个追加位置的完整logits可观察并与R逐位相同，所有行的输出工作不能悄悄删掉。对比基线也必须输出相同观察量，完整成本计入。
- 若最终服务只需要最后追加位置、并保留必需的speculative验证行，应在实验前明确注册这一较小服务观察量、适用证明和资格测试；不能事后用减少输出量冒充原full-logit合同下的加速。

#174/#177普通服务默认仅请求最后append行的logit，heavy资格才扩展输出。因此直接把#179 owner包在原服务上并沿用原时间，会改变实际workload。

冷路径资格与热路径binding分离、有界写集与plan caching可以作为待实现方向，但不能直接删除full-state验证就继续宣称原合同成立。prefix cache命中也不自动免除materialization/copy、layout/dtype核对、integrity、ownership/COW、generation与event依赖；这些成本必须实测。已有#179 cache接口修复不等同于已经实现GPU零拷贝或低开销恢复。

#179 CUDA enforcing路径仍拒绝CUDA split；没有实测GPU可用优化，因此当前不存在能从该实现测出的GPU净收益。

## 6. 最短实证路线与停止条件

A. 同源强基线。冻结scalar R，比较graph4+concat、backend-loop4、packed；相同原始operand、输出行、math mode、捕获/融合策略和合法graph reuse。q1/3/4/5/8/16/32及尾部；Q/K/V/output和FFN。先得到合法性与可触达工作占比，不能只测最顺手的Q projection。

B. 检查剩余机制。干净计时与profile分跑；记录CPU plan/bind/submit、同步wall、GPU event、实际quantizer/MMVQ/concat数、DRAM/L2和occupancy。packed若不稳定胜loop4，则停止把现packing包装成主性能贡献。可以保留有价值的负结果，或提出真正减少shared weight traffic/重复materialization的新机制，但不要靠改baseline制造收益。

C. 安全成本阶梯。no-guard、full-state owner、cached plan+dynamic binding、经证明合法的bounded-write transaction分开测。所有方案输出同一合同观察量；扫描历史长度H、新tokensq、cache residency；分别报告G、C、实际N、失败率p和恢复R。资格/完整logit审计可以冷运行，但其保证如何覆盖热路径必须明确。

D. 服务配对。相同root与session配对。WB-rechunk与QB公平获得所有有效底层优化；保留miss/hit/append/output的预定义分层及总体。报告平均、逐root/session几何比、p95、cold启动、失败恢复和总账。#177条件池始终单列。吞吐需要真实并发与内存压力实验，不能从单请求延迟倒算。

E. 决策。先设工程目标和信赖区间口径。若 `E*r <= G + C/N + p*R`，停止性能主张。若强WB获得相同收益而QB没有额外收益，论文应将贡献定位为共享底层reference-preserving执行机制，而非AUTO/QB优势。AUTO只有在存在跨session稳定互补的多条有效路径后才有理由重启。

目前能交付的是固定数据预算、可运行CPU分析、成本列表和明确实验判据。loop4 GPU资格、packing对loop4净收益、#179低开销安全实现、真实cache-hit分布、生产吞吐和跨硬件推广均未测得。
