# 主张、强基线与负结果

所有 head 见 [VERSIONS.json](evidence/VERSIONS.json)，以下均链接不可变提交。不同工作负载、量化、参考或平台的结果不拼接为一份实测成本栈。

| 可保留主张 | 直接证据／最强相关对照 | 必须同时说明的限制 |
|---|---|---|
| 32B mixed-Q4/Q6 固定部署上 independent-channel group 有小幅完整服务增量 | [#218 S3 原记录与每 root 结果](https://github.com/leecdiang/HeteroSpec/tree/ab695a766d055f7d3c6b1fed0720c579c749bcdb/benchmarks/server_expansion_v1/strong_baseline_followup_20261110/RESULTS_S3_20261112)；[本次复算](evidence/SERVICE_RECOMPUTATION.json)：C/B root 几何比 0.984863743，95% [0.982147937,0.987720995] | G=graph REF1、B=backend REF1、C=group。主比较是更强的 B；不是 live speculative、RTX 新 kernel、并发服务或长上下文实验；约 1.51% 而非 5% |
| G/B/C 强基线层次可以分别核对 | S3 B/G、C/G 使用 97.5% CI；B/G=0.956854868，C/G=0.942371667；C/B ratio-of-totals=0.983809466 | root 几何平均与 ratio-of-totals 分母不同，不能互换；S2 算子收益不能代替 S3 服务结果 |
| 8B 六臂迁移中整套方案有收益 | [#203 REQUESTS](https://github.com/leecdiang/HeteroSpec/tree/592abdfe9267fd97ecbde18cd0ee9a1bfc319e20/benchmarks/linux_transfer_v1/results_ampere_20261107)；[384 条复算](evidence/TRANSFER_RECOMPUTATION.json) | 旧暴露输入是部署迁移，不是新盲样；D4 同时改变投机与组织；顺序与热历史限制保留，不能归因于 LOCAL 单因素 |
| 8B、14B 的组织与 packing 可分开归因 | [#204 四臂](https://github.com/leecdiang/HeteroSpec/tree/55f501e9a93013a4b4d82cc4967e82b8d9054a81/benchmarks/server_expansion_v1/M/results_ampere_m1_20261107)、[#208 四臂](https://github.com/leecdiang/HeteroSpec/tree/ca6caee2cb1cd21dbcfcf1312e500a8fbb3729a8/benchmarks/server_expansion_v1/D14/results_attribution_20261108)；本目录独立复算 | LOCAL 增量小，fixed-packed 的区间可跨 1；不能将 packing 贡献全部归于 LOCAL。#208 是单独运行批次，不与主面板混池 |
| Linux/A5000 资格与模型家族迁移有有限证据 | [#205 Llama](https://github.com/leecdiang/HeteroSpec/tree/ca2c769c87d9b072eb050373e571abfd616ec1fa/benchmarks/server_expansion_v1/F/results_confirmation_20261108)、[#206 14B](https://github.com/leecdiang/HeteroSpec/tree/dbca51e565ca90242ef7a39c5a6df98c1db2ba76/benchmarks/server_expansion_v1/D14/results_complete_20261108)；[928 条原冻结重放](statistics/REPLAY_SUMMARY.json) | #205 是 Llama，#206 是 14B；heavy 资格与 clean 性能深度分开，本次只重放计时 receipt |
| 自由多轮可完成严格状态接续的有限资格 | [#232](https://github.com/leecdiang/HeteroSpec/pull/232)、[#233](https://github.com/leecdiang/HeteroSpec/pull/233)、[#236 实际 producer 链](https://github.com/leecdiang/HeteroSpec/tree/6597489d01d0fa1fb17dce8bf6cade2c53e3a463/benchmarks/server_expansion_v1/N/free_service_retry_20261113) | #232/#233 为 supplied-history；#236 是两个自生成开发案例，均 cap128；没有自然 EOG 覆盖，不是全部 261 项 |
| 当前自然多轮未建立 LOCAL 服务加速 | #236 八个 episode：strong=36.385331460s、LOCAL=37.920655653s；[#238 首差与几何](https://github.com/leecdiang/HeteroSpec/pull/238)、[#239 成本 No-Go](https://github.com/leecdiang/HeteroSpec/tree/750346a149da58aa94a0d16016f5c451221008f7/benchmarks/server_expansion_v1/N/local_cost_decision_20261113) | empty-think 的 4 token stub 在 canonical 历史中省略，首差位于 assistant 内容前；最新 assistant KV 无法保留。较早 canonical KV 是双方共同收益。只少一次外层 decode、rows 相同；机制重放 8 请求未执行，不能当作遗漏的正结果 |
| 完整数值与消费者覆盖有必要 | [#221 CPU 反例和 q4 frontier 诊断](https://github.com/leecdiang/HeteroSpec/tree/af436df989570ad882db65bd8a4b265b9e8cfdae/benchmarks/frontier_cost_v1) | 小型未训练 CPU/F32 反例不是 A5000 量化 GPU 反例；本次未定位其原始 payload，只能复查公开汇总、源码与历史独立审阅 |
| RTX 的新算子结果必须按自身合同引用 | [#237 全样本与数值合同](https://github.com/leecdiang/HeteroSpec/tree/c8e5ea070ac393d7513903e0ec261dfce4554a49/benchmarks/rtx223_e11_u_contract_20261113)、[#240 后端收口](https://github.com/leecdiang/HeteroSpec/tree/d240c5b43a763d5b02b5a53169b07f8e8af71a6c/benchmarks/rtx223_e12_backend_closure_20261113) | 公开算子材料可读；不假定私有 RTX 数据在 A5000。现代完整 backend NOT_RUN；独立 U oracle、旧参考与历史部署合同不得混称 |

组件到服务的解释仅限同面板：S3 receipt 可分辨已记录服务与组件计时，但没有被分别测量的阶段仍为未知，重叠计时不能相加；本次不构造跨实验成本栈。#236 的 response 与 reset 是不重叠区间，可核对相加；内部 phase 可能重叠。warm 记录不并入 measured 主统计。

5% 是历史项目目标，不是 JPDC/TPDS 的审稿阈值。将 LOCAL 保留为限定条件下、参考保持的执行组织机制；目前不应作为自然多轮普适服务加速主线。
