# 全稿科学交叉审阅

日期：2026-11-13。对象：本次 author-review draft 的 `main.tex`、摘要和全部主文章节，以及方法合同补充。审阅关注方法成立条件、因果指称、比较合同、统计单位和数据一致性；不替代独立的语言、参考文献元数据及最终 PDF 排版审阅。

## 总体判断

当前稿可以作为**有限部署内的固定参考执行构造论文**供作者审阅。主线已从优化名称和资格账本转为“固定数值行为仍留下怎样的并行空间”，与直接证据基本一致。最强干净增量由 S3 相对共享量化 backend scalar-loop 的比较承担；局部切分、完整投机应用以及现代不同合同算子分别回答不同问题，没有合并为一个统一速度结论。

本次数据复核没有发现需要更换核心结论的数值错误。发现并处理了一个公式错误和若干重要范围表述：完整组/tail 维度必须守恒；S3 bootstrap 必须注明 code/math 分层；自然 pilot 必须称两对话而非仅两次请求；S3 的 fresh-worker 暖后请求与长期常驻服务不能混淆。历史 Linux Qwen/Smol 的精确资格计数未找到本轮可直接复核的 summary，建议移出主文精确证据。

保留该主线不等于已有充分的普适系统优势。主要科研风险仍是审稿人认为构造来自专用实现的组合，且应用收益大部分不是新机制贡献。当前稿应正面展示两个算术组实例、局部切分规则和明确的状态义务，以这些可复用规则承担贡献，而不是用 1.5% 的统计显著性替代方法价值。

## 本次实际完成的检查

1. 完整读主稿所有段落、公式、表格和图注，及所负责的补充合同。
2. 从公开原行独立聚合五个 Q8 panel 的 **1568 条正式计时**：384、256、288、384、256 行；逐一检查每个 root/session/arm 键不重复、各主效应点估计及两个 interaction 一致。
3. 实际运行固定 #241 的 CPU 服务复算脚本，重得 S3 的三个估计及分层 bootstrap 区间，并重得自然服务总和。结果：`full_science_service_check.json`。
4. 实际运行固定 #241 的 Q8 复算脚本，重得四个后续 panel 的全部点估计、区间与 interaction（1184 行）。结果：`full_science_q8_intervals.json`。
5. 从 RTX 原始 `event_ms / batch_repetitions` 独立重算两个 U/B 几何比，检查原 analysis 的 12 个 paired blocks。没有把每 batch 内的 5 次执行当作 5 个独立样本。结果：`full_science_numeric_checks.json`。
6. 直接重读 S3 原始 README 与成本材料、自然 episode 行、静态机会与成本报告、现代合同/资格/未运行状态。方法部分另已直接核读 planner、resident executor、worker、packed/local graph、cache append、CUDA dispatcher/MMVQ 及 S3 diffs。

没有运行新模型、GPU、native 资格或服务 benchmark；没有改动历史实验数据、基线和源码。公开数值复算不能代表本轮重新比较了受限原始 KV/输出字节。

## 需要处理或已处理的具体问题

| ID | 问题与重要性 | 处理 |
|---|---|---|
| S01 | 原方法公式直接写 `X[K,q] → X[K,a,g]`，当 `r>0` 会丢失尾部元素。 | 已直接修正所负责 `03_method.tex`：先拆 `X_full[K,ag]` 与 `X_tail[K,r]`，仅完整部分取 `[K,a,g]` view；保留尾部处理。 |
| S02 | 原句称数值属性在各 implementation/deployment 已 established，容易超出实际有限资格。 | 已改为部署绑定固定实现，资格检查 reported cases 的输出和状态。 |
| S03 | S3 不是从全部12个 root 混合抽样，而是六 code、六 math 分别抽样。 | 原始 README、`recompute_service.py` 与实际复算一致；已通知主编代理，由其修正文及图注。点估计与当前数值区间无需修改。 |
| S04 | S3 144 个 formal requests 各来自 fresh worker，先同 root 完整 warmup，再 reset+measured；resident 指计时窗口。 | 建议设置段明确 fresh-worker 生命周期，避免理解为144请求连续运行的长期服务。主编代理已接受。 |
| S05 | 摘要 `two-request multi-turn pilot` 容易误读为只执行两次请求；实际是两段发展对话，各有多轮，每臂两轮计时。 | 建议 `two-conversation multi-turn pilot`。表内2×2和八 timed episodes正确。 |
| S06 | RTX B 是提取的 legacy packed Q8 算子，S3 B 是 scalar-loop backend control，字母相同而含义不同。 | 建议首次出现 RTX B 时明确 `extracted legacy packed Q8 operator`。不能把两个B或两个C作跨实验对照。 |
| S07 | 89-row 例子属于 proposed supplied-history append 的 source-derived 分析，不是自然 pilot 内已计时的 append。 | 建议明确 `source-derived proposed 89-row supplied-history append`。4→3 calls与23 projection tiles正确，但不是实际 GPU launch 或单项成本测量。 |
| S08 | “These observations explain” 若指自然 pilot 的全部 slowdown，会超过小样本和静态分析的因果能力。 | 可以说它们说明减少外层调用不一定减少主要算术工作；不要把测得的所有服务差异唯一归给 views/concat。实际 per-component costs 尚未知。 |
| S09 | `Q8 service and factorial ...99% intervals` 应限定 A5000 主 panel，避免覆盖附录的 Windows 四比较 family（98.75%）。 | 建议加 `A5000`；现有主文数字本身正确。 |
| S10 | “old CPU-round-to-nearest oracle” 容易与 legacy B 的旧参考混淆。e10是对新上游路径的独立严格CPU-RN合同，之后另声明受限U合同。 | 建议称 `the earlier strict CPU-round-to-nearest oracle for the upstream path`。保留失败、未在该合同下计时及新合同是不同选择。 |
| S11 | 主文6740向量/4784状态仅在当前可读 #222 正文/supp重复出现，本轮未定位其直接 qualification summary。 | 有限搜索 #222 来源清单、fixed source table、现存 Linux/phase1 材料后停止。建议主文不保留这两个精确计数，使用直接可核 S3 的资格深度；历史 Qwen/Smol 结果明示为 reported、未本轮重比原native bytes。 |
| S12 | 独立 supplement 对主稿 Eq. label 的引用会未定义。 | 已直接改为 `the reference relation in the main paper`。 |
| S13 | 补充原称后来profiles扩大capture点，可能把重构frontend当历史已执行资格。 | 已改为逐profile依其自身capture implementation和qualification record判定，未新增任何资格事实。 |

除所负责的 `03_method.tex` 与 `supp_contract.tex` 外，没有直接改动主编代理的稿件文件，避免并发覆盖。主编代理负责在整稿修订记录中确认其余修改是否已采纳。

## 核心数值和统计口径

| 结果 | 本次核查结果 | 必须保留的解释 |
|---|---|---|
| S3 C/B | 0.9848637428511184；95% [0.9821479373132749, 0.98772099465029] | 12 roots，root内四round平均log比，再等root；code/math分层 bootstrap20,000次。1.514%降时，不是完整投机。 |
| S3 B/G、C/G | 0.9568548680833465、0.9423716667458778；各97.5%区间匹配 | 不能用较弱G分母替代主要C/B。 |
| S3 pooled ratio | 0.9838094660308528 | B总364.831679008 s、C总358.924859316 s；与equal-root估计不同，当前稿明确区分。 |
| Q8 8B packing | W固定时1.63525%，L固定时1.55601% | 四臂平衡panel；强loop4已共享activation quantization。 |
| Q8 14B packing | W固定时0.98703%，L固定时0.79590% | 不把所有模型当独立工作负载；与8B共享16 roots。 |
| Q8 local cuts | 固定loop4：0.20873%、0.30431%；固定packed：0.12835%、0.11186% | 后两区间包含零降时；现稿保留。 |
| Factor interactions | 1.000696007210281、1.0017028256372917 | equal-root几何interaction；不同于四个direct effect的ratio-of-totals。 |
| 完整应用 vs fastest measured M | 17.2078%、25.5392%、11.5221% | 固定五比较family仍完整保留；fastest M是描述性选择，不替换所有固定controls。 |
| 同D4方法组合增量 | 2.01157%、1.08066%、1.56412% | 与完整投机收益分别描述；8B早期D4 pair存在固定顺序，factorial提供更干净归因。 |
| 自然服务 | W=36.38533145998372 s；L=37.92065565302619 s；L/W=1.0421962403923957 | 两对话development pilot，描述性，无population CI。 |
| 自然逐配对 | C0：1.0997048、1.0024302；C1：1.0886215、0.9887654 | 当前表round和case映射正确；不能说所有单次都更慢。 |
| RTX U完整算子 | 0.6129241707091678，95% [0.6079060430068594, 0.6186649050504166] | 单捕获输入，12 paired blocks，不同数值合同，非服务收益。 |
| RTX U纯projection边界 | 0.5823907655654196 | 与包含quantization的38.7%分开，不能混用计时边界。 |
| U与legacy输出 | 32766/32768 float bit patterns不同 | 来自独立差异绑定；新合同通过不消除旧严格合同失败。 |
| 完整现代默认backend | qualification及paired timing均NOT_RUN | 构建/链接与静态shape资格不能写成运行成功。 |

现代CSV中的 `per_operator_ms` 是经过单精度舍入的方便列；原分析以 `event_ms/5` 计算。直接使用方便列可得到约 $10^{-8}$ 的比值差，本轮已定位其原因。绘图脚本使用正确的原始event列，无需修改数据或报告数字。

## 因果机制、正确性与外推

### 有直接机制支撑的部分

768/1024 CUDA干预在同一实际捕获的 AV 算子上保持 q=1。visible Q/K/V/QK/probability prefixes一致，增加的probabilities为零；crop wide P/V到768复现scalar结果；reference P补零并使用相应1024-wide V复现wide结果。主文准确限制在完整AV输出，没有宣称这一干预同时证明完整KV状态等价。Vulkan伴随改变contiguity/dispatch，图注明示joint repair，归因范围正确。

物理组与算术组不同、局部attention cuts以及输出所有权可从实际源码识别。S3使用a=1、Q8使用a=4，避免将特定四列例子包装为所有量化类型的规则。图表也不把外组绘成能够提前生成未知因果token。

### 条件论证与实现范围

归纳论证的前提包括兼容producer、每个采用的operator organization保持其数值/状态效果、consumer收到所需输出并按同样规则commit。它对如何组合局部结果有解释力，但并非证明这些原生kernel对任意输入都满足前提。方法正文与实现guard/capture/资格的区分能够维持这一边界。

代码直接支持：row-owned完整向量copy发生于同步后；append endpoint检查；实际prefix/policy/head-placement重用判断；target decode失败poison。代码不支持：packed继承loop4全部guards、clean observer始终证明placement、所有异常可恢复、自动发现任意backend合同或自动reference fallback。当前稿没有越过这些边界。

### 负结果与性能归因

自然factorial机会率20/2224与pilot两对话小收益限制并存，说明“会跨padding边界”不足以推出显著服务收益。B570 1+(q−1)的受控cells、早期16+16反转和inside负值都得到保留。live k7较k3服务更慢，尽管equal-work q8较两个q4更便宜；新增target rows和draft proposals解释了为什么这两类比较不能互换。

这些结果支持有限配置中的工程选择，不支持通用收益预测器，也没有证明保留旧参考永远优于采用现代后端。讨论对合理回归/重放场景的表述没有虚构外部采用或用户研究。

## 主要固定来源

- [S3原始结果与统计定义，ab695a76](https://github.com/leecdiang/HeteroSpec/blob/ab695a766d055f7d3c6b1fed0720c579c749bcdb/benchmarks/server_expansion_v1/strong_baseline_followup_20261110/RESULTS_S3_20261112/README.md)
- [公开统计行及复算，10fc03ed](https://github.com/leecdiang/HeteroSpec/tree/10fc03ed59e260a290a8ca8d6670d30d50f08118/benchmarks/jpdc_closeout_20261113/)
- [直接保证范围，10fc03ed](https://github.com/leecdiang/HeteroSpec/blob/10fc03ed59e260a290a8ca8d6670d30d50f08118/benchmarks/jpdc_closeout_20261113/GUARANTEES.zh.md)
- [AV物理范围原始干预，701079f2](https://github.com/leecdiang/HeteroSpec/blob/701079f265c0ff8fd05d43fbc2d8d5054a711e1b/platforms/rtx_reference_snapshot/benchmarks/rtx_llama_repair_v1/host_execution/RESULTS.md)
- [自然multi-turn原始episode，92c47c1a](https://github.com/leecdiang/HeteroSpec/blob/92c47c1a49243fdb871036ff39ac33babddec04b/benchmarks/server_expansion_v1/N/free_service_retry_20261113/EVIDENCE/EPISODES.json)
- [实际自然工作量与源推导机会，01d1c980](https://github.com/leecdiang/HeteroSpec/blob/01d1c98001126ff15fae9fcb49185fe8be20ab76/benchmarks/server_expansion_v1/N/resident_opportunity_20261113/RESULTS/REPORT.json)
- [89-row静态成本分析，750346a1](https://github.com/leecdiang/HeteroSpec/blob/750346a149da58aa94a0d16016f5c451221008f7/benchmarks/server_expansion_v1/N/local_cost_decision_20261113/RESULTS/REPORT.json)
- [现代算子不同合同，a6a92fb0](https://github.com/leecdiang/HeteroSpec/blob/a6a92fb08678696fdaefa4904f942237b4d3c84f/benchmarks/rtx223_e11_u_contract_20261113/NUMERICAL_CONTRACTS_ZH.md)
- [现代算子原始计时，a6a92fb0](https://github.com/leecdiang/HeteroSpec/blob/a6a92fb08678696fdaefa4904f942237b4d3c84f/benchmarks/rtx223_e11_u_contract_20261113/ALL_SAMPLES.csv)
- [完整默认backend未运行，d240c5b4](https://github.com/leecdiang/HeteroSpec/blob/d240c5b43a763d5b02b5a53169b07f8e8af71a6c/benchmarks/rtx223_e12_backend_closure_20261113/RESULT.json)

## 未审或未重新执行的范围

本轮没有重新读取全部大型原始张量档案、执行所有历史native reader、验证全部binary module，或审完所有未发布分支。外部文献的逐项DOI和最新版本由独立文献代理承担；本次仅检查主稿中比较逻辑与已知研究边界是否一致。所见源码是具体冻结实现及selected functions，不是所有backends的全树形式审计。图像实际印刷大小、排版与色盲/灰阶检查由图表和编译审阅流程承担。

在这些范围内，没有发现必须新增GPU实验才能修复的核心缺口。对未直接核实的历史精确计数及超出实际实现的承诺，收窄正文即可；不应为了保留它们而扩大本轮实验或访问范围。
