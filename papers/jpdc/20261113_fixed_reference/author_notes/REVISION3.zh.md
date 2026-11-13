# JPDC 第三版：作者审阅说明

## 一页决策摘要

**本轮保持第二版主线、章节顺序、题目和全部服务统计。** 修订集中于两个方法证据桥梁、三张补充机制表，以及 Discussion、Conclusion、现代算子段和图注的语言精修。没有新增 GPU 或模型实验。

论文仍回答同一问题：固定每组的数值路径后，怎样改变组间执行组织，同时交付消费者要求的完整输出与后继状态？第三版把“为什么必须这样做”的历史证据接到了构造之后。

| 本轮重点 | 作者应看到的变化 |
|---|---|
| 算术路径 | 16 个捕获 descriptor 中，native width 2/4 均匹配 scalar；8/16/32 均不匹配。四列内层加外层分组在三个宽度上均恢复完整算子输出一致。 |
| 两类条件 | Vulkan 投影修复后 endpoint 一致，但长输入的两种 speculative layout 各有 99/128 个 committed vectors 不同；联合 attention 修复消除差异，关闭修复恢复原轨迹。 |
| Producer 合同 | 补表覆盖八输入、两 producer、三 consumer。两个 speculative layout 彼此一致仍可能偏离固定 R；边界同时包含 KV 与初始 logits。 |
| 结果认识 | S3 节省集中在 prefill；Q8、k=3 的验证最多四行；local cuts 的服务价值取决于机会、保留的周边工作及新增成本。 |
| 表达与范围 | 用确切的 1.51% 替换“small but measurable”；正应用结果明确限定为三个 A5000 Q8 面板；现代 U 保留不同合同与完整 backend 未测。 |

**强对照不变：** A5000、Qwen3-32B、target-only、a=1、whole-call cuts；B 是共享 activation quantization 后的 backend scalar-loop。C/B=0.984864，按 root 等权降时 1.51%，95% 区间 1.23%–1.79%。它不是 Q8 loop4 或 LOCAL＋四列 packing 的组合增量。

当前供作者审阅的正文为 13 页，补充为 14 页。全部既有图的数值、矢量文件和统计输入保留；新增三张表由公开记录字段与 CPU 脚本生成。原 CAS 模板、字号与版芯没有改动。

**停在作者审阅：** 科学内容、作者信息、权限、数据存储和声明仍需作者确认。本轮没有合并、发布、更新 arXiv 或投稿。

<!--PAGEBREAK-->

## 引入了什么，为什么

**算术宽度证据进入 Method 和补表 A.1。** 同一捕获权重与 F32 activation 前缀分别送入 scalar、native-wide 和 grouped-four 路径。分母是两个模型各八种算子 descriptor，不是 16 个独立工作负载。捕获使用确定性的 32-token fixture。CUPTI 只覆盖 8B 的八种算子；width 4 与 8 使用相同 activation-quantizer 入口，却改变 reduction warps。width 16/32 转入 MMQ，七种算子另有 stream-K fixup。没有将不同 bit 的原因全部归给 quantizer。

**投影／attention 修复进入 Results 和补表 A.2。** 对原始逐行记录重新计数后，99 的准确含义是长输入上每个 speculative layout 的 99/128；两臂合计 198 个差异记录。完整审计共有 1,920 行，包含 R control，不能写成总计 99/1,920。combined repair 的相同坐标为零差异。attention-off 的数量由原报告记录的完整轨迹复现推得，表注明确区别于新做的逐行实验。修复联合改变 extent、contiguity 和 dispatch，没有声称单因素因果。

**Producer 证据只进补表 A.3。** 三种结果类别覆盖完整八输入／48 单元；没有只挑两个有利例子。表统一相对固定 R，未偷偷换成各 producer 自己的 C1。全部 16 个 input–producer pairs 内 PQ/QB 的 endpoint、cycles、full vectors 一致；KV 与 initial logits 在八输入上同时改变。它属于早期 B570、boundary-zero clean receiver、k=1，与当前 capacity-4096 自然多轮合同分开。

**另一个范围澄清：** 原来泛称的 Vulkan “microbatch 128”现限定到受控 SmolLM2 append：outer prompt call 最多 512、physical microbatch 128。新引入的 Llama stock-UB1 与 Qwen P1/P4T 不继承这个设置。

## 没有引入什么

- 没有把历史 23→2 kernels 搬进性能论证。该对照同时改变旧 tile/concat graph 的量化、launch 与拼接，不是共享量化后纯调度增量，更不是 S3 1.51% 的分解。
- 没有回填历史弱对照的较大服务百分比。三份历史记录在本版只承担数值机制和消费者合同的解释。
- 没有新增图形或重画已有科学图；紧凑、可编辑的机制表足以表达新证据。未测单元用破折号并解释，不画成零。
- 没有从有限 capture／digest／equality 记录推出跨设备或全输入的逐位证明，也没有重放受限原始张量。

## 文字精修

Conclusion 明确收束到组内算术与组间执行自由、输出／状态义务、强对照 1.51% 和机会—成本关系。Discussion 直接说明共享量化后的剩余机会，删除未测维护成本与生产 ROI 猜测。现代 U 主文直接写算子降时 38.7%，保留单输入、不同合同、完整 backend 未测；早期 oracle 失败仍在补充。图注说明比较与读法，删去“保留不利结果”等编辑行为描述。

删去跨节重复的开发场景和成本概括，使主文保持 13 页并消除单条参考文献孤页。没有通过缩小字体、改变官方版芯或删除科学限制压缩篇幅。

## 核查与复现范围

本轮完整阅读当前主文、补充及三份指定历史报告，直接核对相关公开 operand/dispatch 记录、committed-row JSON、repair controls、producer 全矩阵和历史源码。独立审阅分别检查机制、逐行统计及语言；集成后交叉复读，并实际编译、渲染检查正文与补充的每一页。

新增复现入口是 `paper/scripts/analyze_v3_history.py`。它从 `paper/data/v3/` 中的公开字段投影生成三张表和摘要；`sources.json` 逐项说明固定 URL、字段保留与省略。没有改动既有 52 个冻结科学输入，也没有改变原 bootstrap、root 单位或估计量。

本轮不是重新执行全仓审计或新一轮完整文献搜索。既有文献、原统计重建及投稿指南核验记录继续保留在早期审阅目录；当前稿没有新增外部文献或期刊政策主张。未复跑 native qualification、未取得全部原始公司受限数据，也未重新测量现代完整 backend。

## 作者仍需确认

优先确认三项历史机制解释和 producer 合同的表述，以及这些公开字段投影的最终出版许可。其次核实作者／单位完整地址、CRediT、资助、利益冲突、致谢、AI 历史使用及最终数据存储／受限访问安排。详细项目仍在独立 `DECLARATIONS_TO_CONFIRM.md`，没有移入科学正文，也没有代替作者签署。

## 固定来源

- [算术宽度与外层分组：371223b6，完整报告及同目录原始记录](https://github.com/leecdiang/HeteroSpec/blob/371223b696bb805030c29f04e39eb17b57fb2ebb/benchmarks/rtx_operator_frontier_v1/execution/RESULTS.md)
- [Vulkan 投影与 attention 联合修复：10a70566](https://github.com/leecdiang/HeteroSpec/blob/10a70566ce01ab707dbdcc57d8270c1434088f07/benchmarks/b570_llama_companion_v1/host_execution/RESULTS.md)
- [Producer × consumer：022babfa](https://github.com/leecdiang/HeteroSpec/blob/022babfabb3d1b6f4f2a2830dca04b2654d193f9/benchmarks/b570_producer_consumer_boundary_v1/RESULT.md)
- [SmolLM2 受控 append 的 producer 设置：62f2e334](https://github.com/leecdiang/HeteroSpec/blob/62f2e3345b25b59268cc2b3c131fd5ed8c7d5f88/platforms/b570_snapshot/benchmarks/tpds_phase1_v1/RESULT.md)
- [第二版审阅基准：c08b68b2](https://github.com/leecdiang/HeteroSpec/commit/c08b68b2c68a4b3a86f850eda368430fc8efeb3f)
