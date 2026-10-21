# 来源与创新边界（方案版本 2026-10-15）

## 本项目固定来源

仓库：[leecdiang/HeteroSpec](https://github.com/leecdiang/HeteroSpec)。所有资产恢复均使用完整commit，不以分支最新文件覆盖历史。

| 用途 | 固定版本/路径 | 本轮实际读取 |
|---|---|---|
| 原参考、自然speculative actor、成本边界 | [PR92](https://github.com/leecdiang/HeteroSpec/pull/92)，`82946adf946491e6cf7fef761bcc1ec0772e914e`，`benchmarks/b570_evidence_closeout_v1/README.md`、CAS | PR元数据、README、engineering-plan前段与目录；完整CAS未在本环境恢复 |
| 原生schedule与target-only限制 | [PR101](https://github.com/leecdiang/HeteroSpec/pull/101)，`26706c9fb4818ec3465e45acea029c4ab88a390f`，`native/worker.cpp` | decode/prefill/counter/主循环/restore guard源段；ASSET_PREFLIGHT |
| PQ/QB图表示 | [PR98](https://github.com/leecdiang/HeteroSpec/pull/98)，`3235d44c26edd92db33e574094c26af8e29d2452`，`scripts/platform/rtx_querylayout_mechanism_v1/replay95.cpp`、`build95.py` | 完整两个文件；不是Vulkan编译或端到端验证 |
| 当前B570修复 | [PR105](https://github.com/leecdiang/HeteroSpec/pull/105)，`a90bf8533fd4062834378c608bbd40305995d341` | 最新元数据及此前审查；CPU候选不能当native执行器 |
| 重构与普适性目标 | [PR106](https://github.com/leecdiang/HeteroSpec/pull/106)，`3bc3c2f018acd39ca81911c7725175d5c0be306a` | 已有完整研究设计与当前状态；新PR不修改它 |
| RTX隔离边界 | [PR104](https://github.com/leecdiang/HeteroSpec/pull/104)，`50e64c7c8a2ac69fd59fd4b80310687754deb071` | 最新元数据；不提前声称s5或E1完成，不改变原时间表 |

## 外部主源，本轮核实的适用部分

- [SPECTRA](https://arxiv.org/abs/2609.24847)：阶段变化、GEMV/GEMM与tile/dataflow调整已有硬件研究；本次读到主源相关介绍/方法，不复算其FPGA结果。本研究不能仅以“阶段感知阵列”宣称创新。
- [CoRun](https://arxiv.org/abs/2608.14376)：isolated prefill与固定形状decode已有方案；本次核实主源摘要。我们的producer组合需通过固定量化reference实测证明增量，不以换名称回避近邻。
- [NVIDIA PTX ISA](https://docs.nvidia.com/cuda/parallel-thread-execution/)：若干mma/wmma语义未完整规定累加顺序；不能仅凭dtype推导Tensor Core数值图。当前B570工作更不能据此定位RTX Tensor Core内部缺陷。
- [Vulkan timestamp queries](https://docs.vulkan.org/spec/latest/chapters/queries.html)：API timestamp支持与所用队列valid bits/完成性有关；存在API能力不等于已取得本研究的组件时间。

用户提供的另一对话研究结论是有用的设计输入，不是其每篇引用已由本轮独立全量核查。SpecPIM、Hawkeye、SPEQ等后续若成为实际对照再核实和适配，不在本PR制造虚构的性能比较。本PR不声称新微架构优于这些系统。

## 本轮验证范围

本地实际执行了Python标准库CPU测试；结果见CPU_TESTS.log及VALIDATION.json。没有加载模型、编译Vulkan native、运行operator或GPU请求；没有得到新的模型输出/性能数据。纯工具的通过不意味着native接口已经实现。

本PR故意不复制完整历史raw，也不新建一套归档框架。只承载协议、CPU计划/准入/分析、架构trace接口和原机任务；实测证据由host在同一新分支按冻结规则提交。
