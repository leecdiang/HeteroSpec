# JPDC 投稿稿件：作者审阅说明

**题目：Parallelizing Quantized LLM Inference Under a Fixed Numerical Reference**

本稿供作者审阅。写作、图表和 CPU 复算已经完成；最终作者信息、声明、数据存储与投稿决定尚未由作者确认。本轮没有运行新的模型或 GPU 实验，没有改动历史实验、基线或数据。

## 一页决策摘要

**论文现在讲什么。** 固定已有数值参考时，查询仍可以并行组织。方法把物理 KV 范围与投影的算术分组分开：在真正依赖范围的位置局部切分，保留其他宽图计算，并向消费者交付其预先要求的完整输出和后继状态。方法价值是这一构造及适用条件，不是把 packing、loop4、权重复用或固定归约分别声称为原创。

**证据支持什么。** A5000、Qwen3-32B、target-only 的强同合同对照给出 1.51% 服务降时，95% 分层配对 root 区间为 1.23–1.79%。Q8 factorial 将 packing 的 0.80–1.64% 增量与很小的 LOCAL 增量分开。控制边界跨越显示明显机会，自然多轮两对话没有观察到 LOCAL 服务改善，扩大投机宽度会因额外工作使完整生成更慢。现代上游单输入提取算子在另一数值合同下快 38.7%，完整现代默认 backend 未运行。

**当前稿件的定位。** 这是固定参考条件下的并行执行方法与系统机制论文。JPDC 适配点是并行工作组织、实现条件和公平的系统性能解释；它不以“达到 5%”作为门槛，也不以较弱控制的大数字支撑主要方法增量。最强审稿风险仍是：可复用构造是否足够超越特定 llama.cpp 路径的工程组合，以及有限工作负载是否足以支持所选结论。正文主动给出构造、条件组合论证和反证，不能消除这些研究判断上的风险。

**作者下一步。** 可以审阅这份完整重构稿，优先确认方法新颖性的定位和结果解释。正式投稿前必须完成真实作者/资助/利益冲突/CRediT/AI 历史声明，决定适当的数据存储与受限访问条款，并复查投稿系统的最新要求。当前限定主张不要求为了追数字新增 GPU 面板。若希望声称完整现代后端优势、通用在线正确性保证或跨设备逐位一致，则需要新的实现与证据，当前稿件没有这些主张。

<!--PAGEBREAK-->

## 1. 叙事选择与原稿的关键变化

采用已经选定的“兼容并行执行方法”主线。机制分析解释方法为什么成立；成本与反例解释何时值得使用。题目按作者确定版本保留。HeteroSpec 只出现在既有仓库 URL 和真实相关文献题名中，不作为本文名称或新缩写。

引言先用四个已知查询的直观情境提出问题，再介绍两种分组。具体位置 765–768、物理范围 [768,768,768,1024] 及其构造留在方法节。结果节按“物理范围干预 → 强控制增量 → factorial 归因 → 几何机会和自然负结果 → 完整应用 → 更换合同的替代路径”展开。旧稿中以资格、阶段名和结果包为中心的叙事被移出正文。

方法定义消费者要求的输出集合、完整词表向量、canonical active KV 和逻辑状态。被排除的输出必须在运行前由消费者合同排除，不能发现不一致后再删除。组合论证明确依赖所用算子的数值义务；实现节区分在线检查、capture 观察、离线资格与条件论证，避免把有限实测扩大成一般证明。

### 与旧稿相比最重要的修正

| 原稿或早期表述风险 | 本稿处理 | 科学意义 |
|---|---|---|
| 32B 以 graph scalar-loop 的约 5.6% 为主要结果 | 主结果采用 C/B 的 1.51%；旧六臂面板保留在补充 | 显示共享量化之后的真正执行增量 |
| 将 S3 的 B 通称为 backend-loop4 | 明确为 backend scalar-loop，a=1；Q8 loop4 是 a=4 | 不把不同算术组织混成一个基线 |
| 完整投机收益与 packing/LOCAL 增量相邻但易混淆 | 主图分面显示 same-D4 增量和完整应用；补充保留全部 15 个固定对照 | draft 及投机机制不被归给单一组件 |
| LOCAL 的控制单元优势容易掩盖自然请求结果 | 同时显示 inside 负结果、低 crossing 频率、自然两对话及历史反转 | 解释机会频率与成本，而非挑选正例 |
| packed 被读成继承 loop4 的完整 guard | 明确普通 dispatcher、部署资格与 marked loop4 检查的差异 | 不制造不存在的在线安全证书 |
| CLI 退出被扩大成事务恢复 | 区分 target poison 和进程退出；持久服务恢复列为实现缺口 | 保留真实失败边界 |
| 旧稿 6740/4784 精确资格总数缺少本轮直接 summary 追溯 | 主文撤出这两个精确计数；保留直接可核的 S3 资格深度和历史 reported 范围 | 不把旧正文数字冒充独立重比的原始证据 |
| 现代路径 38.7% 易被混作方法或服务收益 | 指明不同合同、单输入提取算子；完整 backend 明确未运行 | 允许数值迁移是更快的合理选择 |

固定参考的回归、重放和状态兼容用途以可信场景提出。没有虚构生产采用、客户需求或用户研究。其实际维护收益、能耗收益与迁移成本也没有被测量。

## 2. 核心主张、直接来源与边界

| 主张 | 支持层级与直接证据 | 必须保留的限制或反证 |
|---|---|---|
| 物理范围可改变 attention–value 的完整输出 | 固定 q=1 的 crop/pad 双向干预，源 [RANGE] | 这是 AV 输出，不是该干预下完整 KV/状态的等价证明；Vulkan 是范围、layout 和 dispatch 联合修复 |
| 两种分组及局部切分可组成可复用构造 | planner、native graph、F0 三臂源码、消费者所有权；源 [CODE]、[STRONG]、[GUARD] | 算子义务是部署条件；没有自动发现等价 kernel 或跨输入证明 |
| 32B 执行组织比强同合同 B 降时 1.51% | 12 roots × 4 rounds；六 coding/六 math 分层 bootstrap；源 [STRONG]、[ROWS] | target-only、固定 A5000 部署；144 fresh workers 各 warmup 后计时；不是常驻长生命周期并发服务 |
| Q8 packing 与 LOCAL 的贡献不同 | 两模型四臂平衡 factorial；所有 root 和 family 区间；源 [ROWS]、[Q8F] | 共用 16 roots；LOCAL/packed 的区间跨 1；k3 verification 至多四行，多组 packing 在 prefill |
| 自然多轮未观察到 LOCAL 服务改善 | 两对话、两轮、四对、八个 episode；pooled L/W=1.042196；源 [NATURAL] | 描述性结果，不给总体置信区间；不能推广为普遍更慢或更快 |
| 完整投机应用可改善 resident 计时 | 8B/14B/Llama 的所有固定 M 对照；源 [ROWS] | Llama worker 排名反转；32B 与 B570 的投机负结果保留；8B earlier D4 顺序固定 |
| 宽调用更便宜不意味着宽投机更快 | equal-work q8 与 live k7/k3 分开；源 [WIDTH] | 已知 token 操作与改变 proposal 工作量不是同一实验 |
| 现代 U 算子更快 | 事件时间/重复次数重算 U/B=0.612924；源 [MODERN] | 不同合同、单张捕获输入；32766/32768 输出 bit patterns 不同；完整默认 backend [BACKEND] 未运行 |

S3 的主估计是每个 root 内平均 paired log ratio，再对 12 roots 等权几何平均，结果 0.9848637428511184。95% 区间 [0.9821479373132749,0.98772099465029]。pooled total ratio 为 0.9838094660308528，是不同 estimand。正文、图、摘要保持这一差别。

Q8 application/factorial 的点估计是 ratio of totals，使用 99% paired-root family intervals；interaction 是等权 root 的 ratio-of-ratios 几何均值。Windows live-width 用 98.75% intervals；B570 三配对用 observed range；自然 pilot 不造 CI。不同统计单位没有拼成一条统一曲线。

## 3. 图表设计：每张图承担一个论证任务

正文采用同一 P052 字体系统、蓝/赭/灰配色，颜色同时由形状、空实心、纹理或位置编码。PDF/SVG 是矢量，数值图直接从公开输入生成；PNG 只用于预览。主要图形文字按最终双栏尺寸检查。强控制、误差及负方向点没有被坐标轴裁掉。

| 图或表 | 设计意图 | 相对旧稿的变化与限制 |
|---|---|---|
| 主图 1：机制总览 | 三面板依次解释直接合批改变范围、两类分组、局部 attention 与输出/状态连接 | 新画；以具体行和分界替代工程术语框图。是正文机制图，不是 graphical abstract |
| 主图 2：范围干预 | 四格直接比较两参考与 crop/pad 的输出身份 | 重画；显式 q=1 AV consumer、768/1024，避免把完整状态资格画成干预结果 |
| 主图 3：32B 强基线 | 12 roots 的重复点、root summary、95% C/B；旁列弱 G 的两次级对照 | 新增 S3；绝不让较大的 C/G 替代方法增量 |
| 主图 4：factorial | 两模型小倍图，四个主效应与 interaction；灰点保留异质性 | 重画；明确 interaction 的不同 estimand，跨 1 区间保留 |
| 主图 5：几何机会 | B570 crossing/inside 三配对及 A5000 机会频率分开显示 | 修改；不同量不共用“加速”轴，负 inside controls 和三点范围都可见 |
| 主图 6：应用与增量 | 分面比较 same-D4 与完整应用，使用各自合适的轴 | 重画；完整 15 个固定对照在补充可编辑表，不靠选择最快 M 代替预定 family |
| 正文自然 pilot 表 | 两对话 × 两轮并排列出，pooled ratio 独立一行 | 新增；没有把重复测量变成四个独立任务，也没有把未测范围画成零 |
| 补图 D.1 / D.2：宽度与成本 | equal-work、live-width、工作量，以及分阶段差额 | 重画；说明更少 cycles 为什么伴随更多 verified/draft rows |
| 补图 E.1：历史几何 | 保留早期 16+16 等反转及未测格 | 重画；未测格明确留空，不补数 |
| 补图 C.1：早期 32B 与生命周期 | 保留旧六臂面板和 Llama 初始化反转 | 重画；旧弱 baseline 仍可查，但不再占据主结果 |
| 补图 E.2：RTX 合同取舍 | C/C1/U 各会话独立显示，保留更慢旧合同候选 | 新增；旧 oracle 失败和未运行 backend 没有时间点 |

实际编号以最终 PDF 为准。每张图的固定源 URL、完整 commit、输入 SHA-256、图尺寸、输出 SHA-256、统计口径与脚本入口在 `paper/generated/figure_manifest.json`。编辑图形应改 `build_figures.py` 后重建，不手工移动数据点。

## 4. 独立审阅、修正与复算

写作与实现、文献/语言、图表/数据分别分工，之后交叉审阅整稿。主编直接阅读稿件和关键证据，没有把子任务总结当作原始数据。保留了审阅快照与逐项反馈，供作者检查发生了什么改动。

已落实的实质修正包括：算术分组先拆 full/tail 再 reshape，修复 r>0 的维度表达；“每部署已经证明”改成固定实现绑定及 reported-case 资格；factorial 不再暗示隔离 draft quality；S3 写明分层 bootstrap、fresh-worker 暖后计时；自然 pilot 从 two-request 改成 two-conversation；RTX B 明确为 extracted legacy packed Q8 operator；89-row 示例标明 proposed source-derived plan，不当作实测 launch 或自然 pilot 变慢的唯一原因。

CPU 复算重建 1568 条 Q8 服务/factorial timing rows、S3 288 行 warm/measured 记录和自然多轮八行；另外独立 NumPy 实现核对新公开的 928 行。所有对应点估计、区间和 interaction 与固定分析一致。绘图脚本执行 133 项数值断言并检查完整 root、配对和显示范围。它没有运行模型、native 资格或 GPU。

现代 RTX CSV 的 `per_operator_ms` 方便列存在约 1e-8 的比值舍入差异。图脚本使用同 CSV 的原事件时间除以批次重复数，准确重现公布结果。没有“修正”任何原始计时数据。

实际读取并应用的能力包括 `scientific-writing`、`peer-review`、`literature-review`、`scientific-visualization`、`statistical-analysis`，以及 `blader/humanizer` 4.0.0。科研 skill 固定到 K-Dense commit `2d2065fb4520fa3f3f2bcf61cff26ec8b7eba4b5`；humanizer 固定到 `b48c832f0f809c1b5658edbb838c2521b72f2413`。环境自带 PDF 能力用于排版与实际渲染检查。未为凑数量安装软件，也未把不存在的技能列为使用记录。

### 审阅范围与未审范围

完整读取了现有论文源及补充、最新写作指南、当前重构稿和补充；核对了 main、#222、#241、#242 及相关结果 head 的关系。关键 planner、ownership、native graph lowering、loop4/packed dispatch、S3 diff 与 CPU consumer diagnostics 直接读源。现代上游重点核对 few-row、量化与 dispatch 路径；不是对全部 llama.cpp 的源码审计。主要文献按支持相应陈述的原始论文与官方源码阅读；文献清单记录了全文/局部/仅 metadata 的具体范围。

没有重新比较全部历史 native tensor bytes，没有重跑 GPU，没有审完整套形式证明或全部上游实现。部分历史资格总数只能回到旧论文，已撤出主文精确主张。公开 numeric projection 与原始 receipt 的区别在补充、数据 README 和来源 manifest 中说明。

## 5. JPDC 格式、构建和政策

投稿方向为 JPDC Regular，优先 subscription/non-OA；本轮没有选择 OA、购买选项或进行投稿。期刊范围与本研究的并行执行、性能评估和系统实现主题相符，但方法新颖性和证据充分性仍是审稿判断，不能据此承诺录用。

采用 [GUIDE] 中作者提供的官方摘录作为摘要、关键词、highlights 和页数约束：摘要不超过 250 词，关键词 1–7 个，独立 highlights 3–5 条、每条不超过 85 字符；双栏总页数按 16 页规划。当前摘要为 216 个空白分词，六个关键词，五条 highlights，字符数分别 82、84、84、77、85。完整在线 Guide 页面本轮再次访问返回 403；没有声称独立读到了其全部最新内容，正式提交前应复查。

官方 CAS ZIP 已从 Elsevier 官方 CDN 实际下载，SHA-256 为 `36d97da01c6bbd134f315bff6c3de553735e2550444a6ddd4f869ddc67a20757`，与 #242 完全相同。官方 `cas-dc.cls` 与 `cas-common.sty` 保持原字节。环境问题是 TeX 文件数据库/format/font map 缺失，已用本地 cache 修复并实际编译。使用 numeric natbib + unsrtnat，按出现顺序编号；CAS 原 bst 按作者排序，因此没有误用它。

正文采用可编辑双栏 CAS，补充独立编号 A–F，highlights 独立可编辑。自定义前导配置把模板默认“submitted to Elsevier”页脚替换为作者审阅稿，避免暗示已经投稿；未提供 ORCID 时不印空身份字段。官方模板类文件没有被改写。

官方 [LATEX] 指出 Editorial Manager 不处理含子目录的 LaTeX 源。交付同时保留便于维护的分目录源码和单层 submission source ZIP，并实际编译单层版本。它仍是供作者准备上传的文件，未自动上传投稿系统。

官方 [AI] 区分解释图、真实数据可复算图和 graphical abstract：本稿的机制图在图注说明 AI 辅助，数值分析/绘图在 Methods 说明，文末另有 AI declaration。当前环境报告的工具身份是 ChatGPT、OpenAI、GPT-6 Astra Pro；历史研究代码的完整 AI 工具、模型版本、用途和作者监督仍须作者核实。AI 声明没有声称作者已完成最终审查。

## 6. 最可能的审稿质疑与正面回应

**为什么不直接换现代 backend？** 如果允许改变数值合同，应当比较现代实现。稿件明确给出现代 U 的算子优势；研究问题是保留既有数值接口时如何组织工作。完整默认 backend 尚未测量，因此两者完整服务优劣是开放问题。这个回应保住问题定义，不证明每个部署都有保留旧参考的需求。

**1.5% 为什么值得发表？** 数值本身不能承担全部论文价值。它证明强同合同控制之后仍有可测增量；方法价值还来自两类分组、局部切分与消费者义务的构造，以及正负结果对机会和成本的解释。若审稿人认为组合仍过于特定实现，这个风险真实存在，不能靠弱基线的大数字解决。

**是否只是补丁集合？** 稿件提供输入条件、构造步骤、完整消费者关系和条件组合论证，并在 Q8 a=4、mixed-Q4/Q6 a=1 和 Vulkan 中给出不同实例。但没有自动准入、任意布局支持或通用数值证明。方法能否推广的判断仍需要读者评估；对更强推广主张应另做针对性实现与资格，而不是措辞升级。

**正确性是否可靠且可复核？** 全向量、active KV、逻辑前沿和消费者请求分别定义；CPU 反例说明 argmax 不足。公开计时可复算，关键源码可查。部分原始 native 数据受限或已裁减，当前没有完全开放的重执行承诺，这会影响可复现性评价。数据声明必须保持真实。

**统计是否靠重复次数撑起来？** S3 以 12 roots 分层推断，Q8 按 roots 聚类；显式标注复用 roots、固定顺序、置信区间 family、少样本范围和不同 estimand。没有把 48 pairs、1024 requests 或三次结构重复当作相同数量的独立任务。

## 7. 投稿前真正剩下什么

### 必做：无需新增 GPU

作者逐节确认科学判断、方法定位与局限；补齐真实单位/地址、通讯信息、CRediT、资助、利益冲突、致谢和最终 AI 声明。确认公开数据许可及公司限制的准确范围，决定满足 JPDC 数据要求的适当存储库和可合法提供的材料；已裁减材料不能承诺获取。复查最新完整 Guide、Regular 页数解释和投稿系统生成的 PDF。完成最终人为审阅并明确同意投稿后，才能去掉作者审阅草稿标记。

### 仅坚持更强主张时才需要

若要声称更快的完整现代 backend，需要同部署、完整计时边界且各自数值合同合格的比较；当前算子结果不足。如果要声称通用在线兼容或持久服务恢复，需要补齐 packed 实际 dispatch/placement guards 与全事务失效边界，再做针对性资格。如果要声称 LOCAL 对自然多轮普遍有效，需要独立代表性工作负载与机制可预测的机会分布；目前不建议为了追求百分比启动大面板。

### 可不做

无需为了达到 5% 扩大模型或平台规模；无需给每个旧结果重画一张主图；无需把所有历史工程日志塞进正文；无需改仓库名称来完成这篇无品牌标题的论文。旧仓库 URL 是来源，不是论文品牌。

## 直接来源

- [RANGE] [固定 q=1 AV 物理范围干预](https://github.com/leecdiang/HeteroSpec/blob/701079f265c0ff8fd05d43fbc2d8d5054a711e1b/platforms/rtx_reference_snapshot/benchmarks/rtx_llama_repair_v1/host_execution/RESULTS.md)。
- [CODE] [当前 planner 固定源](https://github.com/leecdiang/HeteroSpec/blob/ad16a13d2510363bb6f7c7b99241fe9ef1b54bb0/src/reference_batching/reference_batching.hpp)；native source snapshot 的完整成员 SHA 在方法来源表。
- [STRONG] [32B 三臂代码与 S3 结果](https://github.com/leecdiang/HeteroSpec/tree/ab695a766d055f7d3c6b1fed0720c579c749bcdb/benchmarks/server_expansion_v1/strong_baseline_followup_20261110)。
- [ROWS] [公开原行、固定计划与复算程序](https://github.com/leecdiang/HeteroSpec/tree/10fc03ed59e260a290a8ca8d6670d30d50f08118/benchmarks/jpdc_closeout_20261113)。
- [Q8F] [8B factorial](https://github.com/leecdiang/HeteroSpec/tree/55f501e9a93013a4b4d82cc4967e82b8d9054a81/benchmarks/server_expansion_v1/M/results_ampere_m1_20261107)；[14B factorial](https://github.com/leecdiang/HeteroSpec/tree/ca6caee2cb1cd21dbcfcf1312e500a8fbb3729a8/benchmarks/server_expansion_v1/D14/results_attribution_20261108)。
- [GUARD] [实现保证与观测边界](https://github.com/leecdiang/HeteroSpec/blob/10fc03ed59e260a290a8ca8d6670d30d50f08118/benchmarks/jpdc_closeout_20261113/GUARANTEES.zh.md)。
- [NATURAL] [自然多轮全部 episode](https://github.com/leecdiang/HeteroSpec/blob/92c47c1a49243fdb871036ff39ac33babddec04b/benchmarks/server_expansion_v1/N/free_service_retry_20261113/EVIDENCE/EPISODES.json)。
- [WIDTH] [宽度完整结果固定版本](https://github.com/leecdiang/HeteroSpec/tree/ba5b4c8e01d50d4bfaab1ac3908f798347be063a)。
- [MODERN] [现代 U 合同与全部算子原样本](https://github.com/leecdiang/HeteroSpec/tree/a6a92fb08678696fdaefa4904f942237b4d3c84f/benchmarks/rtx223_e11_u_contract_20261113)。
- [BACKEND] [完整默认 backend 状态](https://github.com/leecdiang/HeteroSpec/blob/d240c5b43a763d5b02b5a53169b07f8e8af71a6c/benchmarks/rtx223_e12_backend_closure_20261113/RESULT.json)。
- [GUIDE] [#242 写作指南与官方模板固定 head](https://github.com/leecdiang/HeteroSpec/tree/b0c2391426f60185a4a70b7fd286b39220ca4cc0/docs/jpdc-authoring-kit)；[JPDC Guide for Authors](https://www.sciencedirect.com/journal/journal-of-parallel-and-distributed-computing/publish/guide-for-authors)。
- [LATEX] [Elsevier LaTeX instructions](https://www.elsevier.com/researcher/author/policies-and-guidelines/latex-instructions)。
- [AI] [Elsevier generative AI policies for journals](https://www.elsevier.com/about/policies-and-standards/generative-ai-policies-for-journals)。

完整文献条目与固定版本在 `paper/references.bib`；实现、数据与文献的实际阅读范围在随附审阅记录中。正式稿的责任、真实作者声明和投稿选择留在作者决策点。
