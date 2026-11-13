# JPDC 第二版：作者审阅说明

**Parallelizing Quantized LLM Inference Under a Fixed Numerical Reference**

## 一页修改摘要

**本版完成的是论证与表达的成熟化。** 主线保持为“保留每组的数值路径，改变组间执行组织”。四查询的范围、whole/local 切分、输出行和 pending 状态现在贯穿同一个例子；独立八行 prefill 小图才展示两个四列算术组。增加七步构造，明确 planner、backend 和有限实验分别负责什么。

**主要结果没有改变。** S3 仍为 A5000、Qwen3-32B、target-only、a=1、whole cuts：C/B=0.984864，root 等权降时 1.51%，95% 区间 1.23%–1.79%。B 是共享量化的 backend scalar-loop。新增同面板 phase 解释表明节省集中在 prefill；合计时长不替代 root 主估计。Q8 的 a=4 factorial、完整应用和自然 LOCAL 负结果仍单独呈现。

**新的视觉主线是“机制 → 干预 → 强基线解释 → 两机制归因 → 机会与成本 → 更宽调用的工作代价”。** 正文六张图统一字体、蓝/赭/灰、形状与空实心编码；完整应用分布移到补充。不同平台、合同、统计单位和计时边界没有合成一条收益曲线。

**实质纠正与保留。** 自然两轮设置纠正为 C4096、backend-loop4、无 draft。empty-think stub 导致 canonical 历史从更早位置重算；它不是 trim 错误，较早历史复用由两方法共享。89-row 案例的 calls 4→3 不改变每个完整消费投影的 23 tiles；其 mask/concat 数量是源码推导。现代 U 仍是不同合同的单输入算子结果，完整现代默认 backend 未运行。

**仍停在作者审阅。** 本轮没有新增 GPU 或 native inference，没有改动原始输入、基线和冻结统计方案。限定后的主张可直接审稿，不需要为了追求 5% 新增面板。新颖性是否足以超越实现组合、有限工作负载的外部效度、受限/已裁减记录的数据存储安排仍是实质问题。作者信息、声明和正式投稿必须由作者决定。

<!--PAGEBREAK-->

## 1. 相对第一版的逐项修改

审阅基准为 [#243 commit 1382b229](https://github.com/leecdiang/HeteroSpec/commit/1382b2295aa9525a99ddb8f24026390ea11e95c4)。开始工作时核对其 head，未发现后续提交；修订在独立工作副本进行，保存前再次检查远端。

| 要求 | 第二版处理 |
|---|---|
| 同一例子解释完整方法 | 四查询 765–768 的范围为 768/768/768/1024；whole 切成 3+1，local 保留一个四列投影组并在 attention 内切 3+1。独立八 prefill 行采用 7+1 物理 runs、4+3+1 attention tiles、4+4 arithmetic groups。 |
| 输出与状态不能停留在口号 | z2 选择 correction；保留 KV 至 767，correction 在 768 pending。全部预先请求的输出先复制到行所有存储。数学 O 对应 frontend 的 all-row/last-row 模式，不暗示任意 sparse-output API。 |
| 讲清为什么成立 | 七步构造涵盖两分组、调用、输出重排和消费者提交；结构不变量、backend 算术义务与实测资格分开。相同 extent 不代表完整 descriptor 相同，相同 shape 不固定量化/归约路径。 |
| 方法实例和实验桥 | 设计表逐面板标出 a、切分、基线、问题、统计单位和计时边界；S3 不再可能被读成 LOCAL＋四列 packing 的组合收益。 |
| 用数据解释 1.51% | 同 48 请求/arm 的 prefill 143.927→137.984 s，decode 216.663→216.690 s；服务合计节省 5.907 s。主估计保持 12 roots 等权，pooled ratio 另列。 |
| 负结果形成机制解释 | 20/2,224 的自然机会频率，与 B570 受控 20.34%–44.68% 降时分面；source-derived 89 rows 展示 calls 和剩余算术/assembly 成本。 |
| 自然历史根因 | 新增两实际对话的 token/state 时间线；331/1,127 单列为 supplied-history CPU 预测。没有把它当自由生成频率或 GPU 收益。 |
| wider-work 反转 | 新主图同时显示同八 token 操作、每 arm 的工作计数、16 roots 的 live-service 分布及原 98.75% 区间。每 arm 128 次请求，四方法相同 k 共享计数。 |
| 完整应用公平性 | 原全部控制、root 分布与区间移至补充；正文保留应用结论。8B same-D4 的固定顺序在正文和补图 caption 各交代一次，不当作平衡 factorial。 |
| 现代替代方案 | 补充 B/C/C1/U 的执行改变、合同、编译资源和计时边界；跨会话不当配对，静态资源不解释成实测 occupancy/流量。 |
| 自信而准确 | 摘要按问题—构造—强基线—机会成本展开；引言直接区分参考固定、batch invariance、固定调度和验证修复。详细失败流程留补充，内部待确认事项移出正文。 |

## 2. 六张主图各自承担的论证

| 最终主图 | 论证任务 | 关键限制 |
|---|---|---|
| 1：机制总览 | 将范围、切分、算术组、输出所有权、accepted prefix 与 pending 放进同一故事。 | 四查询不是两个四列组；八行 inset 是已知 prefill；图为概念示意，不是新实验。 |
| 2：物理范围干预 | crop/pad 双向干预使 AV 完整结果跟随物理范围。 | 单查询、捕获案例、AV 输出；不能扩大成全部状态的干预证明。 |
| 3：强基线和 phase | 同时显示 12 roots、48 pairs、主区间与 prefill/decode 来源。 | phase 是合计时长，非独立样本；G 次级对照不替代 B。 |
| 4：Q8 factorial | 分离 packing、local cut 和 interaction，并保留 root 异质性及跨 1 区间。 | 两模型共用 16 roots；interaction 的等权几何口径与主效应不同。 |
| 5：机会和剩余工作 | 展示受控事件收益、自然频率及 89-row 构造的成本竞争。 | 三部分来源/平台/单位分开，不跨平台相乘，不把逻辑 mask 字节当 DRAM 流量。 |
| 6：宽调用与 live 工作 | 更快的同工作调用可与更慢的完整服务并存，原因是验证和 draft 工作增加。 | operation 和 service 是独立实验；不拟合未存在的性能预测。 |

补充保留完整应用、早期 32B、Llama 生命周期反转、宽度 phase 差额、历史 16+16 几何反转和 RTX 合同取舍。S3 phase 表由代码生成。所有图保留 SVG/PDF/PNG，数据输入、固定 commit、Git blob 与 SHA-256 在 `paper/generated/figure_manifest.json`、`figure_sources_v2.json` 中，绘图逻辑在 `paper/scripts/build_figures.py`。

## 3. 本轮新增解释的直接来源

| 内容 | 固定直接入口 | 重建与边界 |
|---|---|---|
| S3 phase 与强基线 | [ab695a76 RESULTS_S3](https://github.com/leecdiang/HeteroSpec/tree/ab695a766d055f7d3c6b1fed0720c579c749bcdb/benchmarks/server_expansion_v1/strong_baseline_followup_20261110/RESULTS_S3_20261112) | COST_AUDIT 与同面板 measured receipts 对齐；CI/estimand 不变。 |
| 自然真实两轮 | [92c47c1a EPISODES](https://github.com/leecdiang/HeteroSpec/blob/92c47c1a49243fdb871036ff39ac33babddec04b/benchmarks/server_expansion_v1/N/free_service_retry_20261113/EVIDENCE/EPISODES.json) | 两对话×两轮；四比值/pooled 描述性结果，不补 CI。 |
| 历史对齐 | [ef1b6427 REPORT](https://github.com/leecdiang/HeteroSpec/blob/ef1b6427b7f3b6b7d62c4249933b33b8f810d89f/benchmarks/server_expansion_v1/N/resident_opportunity_20261113/RESULTS/REPORT.json) | 实际 free cases 与 supplied-history 预测分字段；新增副本含公开诊断的少量 token/text 摘录。 |
| 89-row 及成本 | [750346a1 REPORT](https://github.com/leecdiang/HeteroSpec/blob/750346a149da58aa94a0d16016f5c451221008f7/benchmarks/server_expansion_v1/N/local_cost_decision_20261113/RESULTS/REPORT.json) | 核查完整 ordered tile 列表相同；无新计时。 |
| live-width 每 arm 计数 | [ba5b4c8e LIVE_RESULTS](https://github.com/leecdiang/HeteroSpec/blob/ba5b4c8e01d50d4bfaab1ac3908f798347be063a/benchmarks/rtx_q8_transfer_20261109/results_20261109/LIVE_RESULTS.json) | 8 arms×128=1,024；11,472 输出及 work counts 是每 arm。 |
| RTX U | [a6a92fb0](https://github.com/leecdiang/HeteroSpec/tree/a6a92fb08678696fdaefa4904f942237b4d3c84f/benchmarks/rtx223_e11_u_contract_20261113) | U/B=0.612924、不同数值合同；C/C1 各有固定来源，完整 backend 未运行。 |

新增 leave-one-root-out 是明确的事后探索：删去一 root 后对余下 11 roots 等权，范围 0.984246–0.985561。它没有替换主估计、没有新 CI，也没有预注册主张。脚本 `analyze_v2.py` 和逐项 CSV 可复算。

## 4. 交叉审阅和真实完成范围

方法、语言/文献、图表三条独立分工交叉核对；主编直接阅读最终方法、结果、补充和关键数据。已落实的交叉纠错包括：自然 C4096 设置、图 5 tile 单位、图 6 每 arm 计数、AI 声明的本轮范围，以及诊断文件含短文本摘录的数据说明。审阅记录按实际读到的版本和范围保留在 `reviews/v2/`。

本轮重新读取主要相邻工作的原始论文相关段落和固定源码：Taming 的算术/调度分离、CoRun 的固定形状、Thinking Machines 的 batch invariance、Vosti 的 engine/kernel 条件，以及 LLM-42 的 KV 修复。Taming/CoRun 的实时版本页访问受限，沿用已取得的固定 v1 原文，没有声称核查最新版本历史。没有宣称发明已有 packing、loop4、固定归约、量化 kernel 或一般投机解码。

完成的是 CPU 重建、代码/文献阅读、图文修订和实际 PDF 编译/渲染。没有重新验证公司受限的 tensor 原始字节，没有复跑历史 native/GPU 资格，没有完成全部上游代码或形式证明审计。公开投影支持的统计复算不等于所有原始 native 记录可获得。具体构建页数、字体和最终 PDF 身份在 `validation/v2/` 与 `paper/generated/manuscript_checks.json`。

## 5. 作者仍需决定的事项

最有可能的审稿问题是：该构造是否充分超越已有算术/调度分离和特定实现组合；1.51% 是否值得维护固定参考路径；为何不采用现代后端；有限且有重用的 roots 能支持怎样的泛化。稿件正面回答问题、给出强对照和迁移替代，但不以文字消除证据缺口。

当前收窄主张不依赖额外 GPU 实验。若作者坚持完整现代后端服务优势、跨设备/全部输入的逐位保证、广泛生产采用或持久服务事务恢复，则需要另行授权的新证据或实现。它们没有被写成已经完成。

作者需核实姓名/机构/通信信息、CRediT、资助、利益冲突、致谢许可、完整历史 AI 工具和实际监督、公司约束及最终数据存储/访问机制。正文不再放“作者待确认”工作项；事实性数据声明和本轮 AI 使用仍保留。逐项入口为 `author_notes/DECLARATIONS_TO_CONFIRM.md`。本稿没有替作者签署最终责任声明。

JPDC 格式沿用 [#242 固定写作指南](https://github.com/leecdiang/HeteroSpec/tree/b0c2391426f60185a4a70b7fd286b39220ca4cc0)，官方 CAS 类/样式未改。摘要 196 词，六关键词，五条独立 highlights；字符与页数由脚本复核。官方完整 Guide 的实时访问仍受限制；最终提交应核对 [JPDC Guide](https://www.sciencedirect.com/journal/journal-of-parallel-and-distributed-computing/publish/guide-for-authors)、[Elsevier AI policy](https://www.elsevier.com/about/policies-and-standards/generative-ai-policies-for-journals) 和 [LaTeX instructions](https://www.elsevier.com/researcher/author/policies-and-guidelines/latex-instructions)。优先订阅制/非 OA；本轮没有选择付费路线、合并、发布、更新 arXiv 或正式投稿。
