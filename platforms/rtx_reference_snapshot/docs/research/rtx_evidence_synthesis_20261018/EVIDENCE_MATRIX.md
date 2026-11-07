# RTX PR120–123：统一证据表与主张边界

整理日期：2026-10-18。状态：结果综合，不是新实验；硬件 SOFTWARE_FIRST/HOLD。
本文引用固定科学提交，后续合并不改变证据身份。所有旧运行 UUID 保持关闭。

## 1. 阅读约定与共同契约

PQ、QB、QH_C 是仓库已有映射实现名称；本表不把不同名称当作独立硬件架构。
除专门标注外，“合格”要求完整 ordinary 输出与规定参考逐字节相同，
并满足输入前后字节、CUDA 放置/支持、共享运行时、计算返回和完成同步检查。
独立 serial-q1 参考是指定实现的数值行为，不是实数数学真值。
完整 ordinary 相等不证明所有中间值、归约树、kernel 或自然 decoder 状态相同。

一个主张必须同时绑定：
**参考契约 R、实际输入集合 X、运行时/设备 E、候选映射 M、成本窗口 W、比较基线 B。**
改变任意一项，就不能直接移用原资格或性能结论。
运行证据以冻结 manifest 为准；跨 PR 不因同一设备而视为同一随机实验。

## 2. 核心主张—证据矩阵

| ID | 可用于论文的主张 | 契约与比较基线 | 成本边界 | 核心证据 | 适用范围与禁止外推 |
|---|---|---|---|---|---|
| C01 | 独立持久输入存储恢复了所测图的可信重复执行 | 原分配、每次重传、持久分配及回退；完整输入/ordinary 字节 | 生命周期诊断，非性能优化结论 | PR120 D0：地址/字节见证 K 被 AV、V 被 ordinary 复用；3 个持久输入新宿主各34调用保持字节 | 定位本宿主生命周期问题；不指认 QB 算术或 CUDA 归约故障 |
| C02 | PQ/QB/QH_C 在固定暴露上下文与已测合成输入中保持规定参考输出 | 原 dtype、mask、所有头/通道、输出恢复；规定参考与持久输入 | 数值资格不等于成本资格 | PR120 N1：24上下文×3布局×3宿主=216；R1：144映射单元格通过 | 固定24不是完整72；合成输入不是自然 prompt；新图未采四阶段中间值 |
| C03 | 原执行设置下，QB 是比 QH_C 更强的面板成本基线 | PR120 合格 PQ/QB/QH_C；q2–q4、同 context/block 配对 | resident_graph：图入口至全设备完成 | QB/QH_C=0.885627；PQ/QB=1.814620；QH_C在73/90配对中更贵；5/6成本块有效 | 同机同会话，未均衡的 R1 仅描述性；不能宣称请求加速或新输入通用最优 |
| C04 | A/A控制和均衡重复后，核心面板仍支持QB，但小差异仍有未决区 | PR121 QB_A/QB_B相同实现；候选PQ/QH_C；固定两值、两session | H1 resident_graph；30调用为宿主内技术重复 | QB_A/QH_C=0.900826，替代QB=0.901081；平均差−7.499µs；24个q2/q4几何19支持QB、5未决 | 2.762%为pilot包络中位尺度，不是逐几何2%精度认证；未决不等于等价 |
| C05 | 冻结预测规则未产生优于固定QB的选择策略 | PR121 新seed q3/GQA留出；固定QB为决策基线 | 选定图成本+实测CPU lookup的离线相位和 | 12/12均值方向正确但高估差距；QB/QH_C=0.962421；含lookup策略/固定QB=1.010298 | 方向预测不是有效优化；不是集成selector或decoder实验，不外推到未测分布 |
| C06 | 实际CUDA Graph重放显著改变映射相对成本 | PR122 同输入/布局 OFF vs 经实际capture/instantiate/replay证明的ON；双QB对照 | clean完成图成本；捕获/冷启动另列 | QB_A ON/OFF=0.615–0.849；四个permuted-q2坐标QH−QB差从12.056–12.975µs缩至0.735–1.627µs | 这是执行模式干预总效应；不是精确CPU launch分解，也不是端到端收益 |
| C07 | 1024邻界伴随实际后端路径变化，且成本断崖在ON仍存在 | PR122 q2/d128/Hq32/Hkv8；邻界三点与原mask | clean成本与独立profile分开 | QB实际kernel数8→3→8；ON QB成本113.085→50.439→114.618µs | 原邻界同时改变逻辑长度和causal frontier；kernel数不是因果机制、带宽或占用率 |
| C08 | compact Q减少所测QH路径的重复复制，但不能据此宣称最佳方案更快 | PR122 q2-k256 QH permuted vs compact；QB仍是强基线 | 实际trace；OFF完整Q事务另作描述性 | QH kernel数5→4；OFF QH compact/permuted=0.965833(q2)、0.947658(q4) | OFF面板无相同实现重复arm；不是ON转换结论；改善QH自身不等于优于QB |
| C09 | 固定逻辑输入的补齐可以改变执行路径，但跨越该边界不保持指定参考字节 | PR123 L固定、mask原列不变、新列屏蔽；必须对同一未补齐serial参考 | 不合格路径没有clean性能估计 | L1023→S1024：0/4资格，value0首次执行3 kernels；L1024→S1025/S1026均0/4 | 失败路径只有首次执行，不能称已证明稳态重放收益；不等于padding数学错误或模型质量下降 |
| C10 | 唯一合格补齐未带来成本收益 | PR123 L1023→S1025，对native_A和native_B；两值×八块 | ON resident_graph；补齐准备/初始KV上传另列 | 4/4资格；仍8 kernels；比值1.014783与1.014974，平均增加1.690/1.709µs | 该合格表示无收益；不证明所有补齐方法或硬件优化都无效 |
| C11 | 在实际ON完整Q事务中，compact QH未建立超越QB的实用收益 | PR123 q2/q4、k256；QB_A/QB_B相同实现，QH两表示；完整ordinary | 同一段copy/transpose→Q上传完成→重放/同步→ordinary读回 | QHcompact/QB_A=1.002216(q2)、1.001598(q4)；对QB_B=1.008295/1.004167；均未通过预定筛选 | 固定合成输入、KV/mask常驻、目标预分配；无自然Q生成/KV更新；不是严格等价证明 |
| C12 | 当前证据支持软件基线与硬件研究的准入边界，不支持加速器收益 | 最佳合格软件基线优先；PR120抽象CPU模型只作假设探索 | 无经校准物理模型、系统关键路径或PPA窗口 | PR120–123均保持SOFTWARE_FIRST/HOLD；PR123 SOURCE_LINK_UNKNOWN | 不宣称硬件加速、能效、面积、频率、流量、Tensor Core瓶颈或跨设备普适最优 |

逐项来源：[PR120][R120]、[PR121][R121]、[PR122][R122]、[PR123][R123]。
上述比值保留原分析口径；配对log比值的汇总一般不等于展示均值之比。

## 3. 成本窗口字典：论文不得混用

| 窗口 | 包含 | 不包含或需要另列 | 可回答的问题 |
|---|---|---|---|
| resident_graph / completed graph | graph_compute入口到全设备同步返回；图内必要packing、mask处理与ordinary恢复 | ordinary主机读回、初始输入准备/上传、分配/捕获、自然模型Q生成 | 常驻操作数下整张图的完成成本 |
| resident_call | 完成图再加完整ordinary读回；缓冲策略依各PR实现 | 初始输入形成/上传及模型请求其他阶段 | 带观测读回的完整调用成本 |
| PR120/121 input-inclusive phase sum | 一次物化、上传/同步、首次warmup完成call的分量和 | 不是30次独立输入包含事务；冷成本另列 | 描述性成本核算，不能称稳态请求延迟 |
| PR121 common-producer phase sum | 独立CPU准备测量与GPU分量组合 | 未在连续同一事务执行；共享CPU分量不增加统计独立样本 | 准备成本敏感性分析 |
| PR122 P0 OFF / PR123 T0 ON | 同一实际区间copy/transpose→Q上传/完成→图/同步→ordinary读回 | KV/mask常驻、目标预分配；原始模型Q生成、KV更新、首次全KV上传另列或UNKNOWN | 所测共同起点下的转换收益能否兑现 |
| profile timeline | 被观察宿主的真实API/kernel/copy事件 | 不替代clean计时；kernel duration和不是busy-time并集 | 路径身份、事件计数与重放证据 |
| decoder request / token throughput | 本组PR120–123未测 | 不能从上述窗口拼成自然请求加速 | 需独立系统资格与关键路径实验 |

PR120与PR121的观察方式不同；PR122与PR123的面板/事务也不同。
不得把跨PR绝对延迟相减解释为优化量。模式对比使用PR122内部匹配实验；
ON完整事务判断使用PR123内部匹配实验。

## 4. 资格、缺失与计数

| PR | 原生GPU宿主 / 显式图调用 | 资格/成本覆盖 | 必须保留的限制 |
|---|---|---|---|
| 120 | 1,332 / 39,480 | N1 216宿主；T1 432数值合格，5/6成本块有效；R1 144映射单元格资格 | D0故障/回退；退出后NTFS硬链接故障导致整块预先排除；R1固定布局顺序 |
| 121 | 3,008 / 99,088 | 核心1,664、留出384、pilot192宿主；全部计划GPU任务完成 | 非独立日期；时钟UNKNOWN；旧/新observer不可当同一测量条件 |
| 122 | 1,137 / 40,124 | 核心768计时宿主；P0 128；实际双模式资格和trace | 1次首图前CUPTI失败；P0因profile预算事前改为独立OFF；clean模式为签名绑定而非每宿主直接trace |
| 123 | 302 / 9,228 | 208/256 clean槽位；12资格宿主首调用失配；48槽位未启动 | 6个额外交替输入能力宿主；session0短暂CPU审计重叠；SOURCE_LINK_UNKNOWN |

PR123账目：344−48+6=302宿主；
11,400−48×38−12×33+6×8=9,228调用。
这只是执行记账，不能把不同PR宿主合并为性能样本或独立输入数。

## 5. 统计解释与反例

- 以宿主均值为输入，按注册的input/context与block配对；重复调用不当独立样本。
- PR121–123按实际session分层重采整块，保留arm和值之间的配对。
- A/A是相同实现的观察噪声参照，不是严格等价检验；2%/1µs是预设实用筛选。
- PR123 T0 q2 A/A绝对尺度2.346µs，q4为0.939µs；QHcompact对QB_A差为
  +0.194/+0.190µs。既无实用优势，也不能从跨1区间得出严格零差异。
- PR123补齐失败在两个fresh宿主重复出现；L1023→S1024的两个值模式分别
  8,188/8,192和8,191/8,192输出词不同，max abs约0.000253/0.00646。
  不描述为“只差最后一位”。大signed-ULP值不能单独作为模型质量指标。
- 这些适应性连续研究不是四次独立盲复现。PR121留出仍是有限合成几何；
  PR122/123选择的边界已经暴露。没有多设备总体推断或自然请求资格。
- 图重放后差距缩小不证明全部差距来自CPU提交；padding同时改变工作量、
  实际算术路径和存储表示，不能把成本变化全部归因于kernel数。

## 6. 复现与访问层次

| PR | 固定科学提交 | raw成员 | raw ZIP SHA256 |
|---|---|---:|---|
| 120 | c6eb66368bc876332afe82f9df5ea51fe0b4b5ec | 110,693 | ab94591015b609df057c1b3edc99784f0a066e8eb9bba56e266097b783e17c3d |
| 121 | d82ec4097adfa032886040e075e71e41cfeb5855 | 81,711 | 0a6d714a1f094307da77ee583a45fdb35571b82bbdcce6b9fa6100ac5da89693 |
| 122 | a1f15bfc8222054aa7b94b40f41af0dd0492ddab | 26,545 | 4b4ec876ee83d527899603a96625b97efc63a46a52e7b007fdba50cd035f325d |
| 123 | f38ed240d904db09e121bf50158cd207e829a12f | 7,860 | 2e69ad5cc8a32944781a1da643ea2116f11575aee14fc12c25eff997f22dcfd3 |

四轮raw均为原RTX机器本地保留，报告了fresh restore与新解释器CPU复算。
Git紧凑证据的远端字节核验不等于大raw远端认证，不等于第三方独立审查。
本次综合审查读取固定Git报告/表与证据说明，没有访问D盘raw、重跑GPU或重新认证这些归档。
原始源代码/DLL绑定、环境端点与资源统计以各冻结文件为准；异常时钟不作频率归一化。

## 7. 前序证据与合并语义

PR104的自然模型固定面板和PR116四阶段对应为前序证据，不能将其范围移植给PR120–123。
PR110抽象CPU模型结果不提供RTX物理校准。PR113部分完成、PR114零启动、
PR118工程准备/终止状态永久保留；后续成功不是对旧失败的覆盖。
合并只接纳实验记录和实现进仓库，不把历史NO_GO改成GO，不重启旧UUID。

[R120]: https://github.com/leecdiang/HeteroSpec/blob/c6eb66368bc876332afe82f9df5ea51fe0b4b5ec/benchmarks/rtx_reference_envelope_v2/RESULT.md
[R121]: https://github.com/leecdiang/HeteroSpec/blob/d82ec4097adfa032886040e075e71e41cfeb5855/benchmarks/rtx_boundary_confirmation_v1/RESULT.md
[R122]: https://github.com/leecdiang/HeteroSpec/blob/a1f15bfc8222054aa7b94b40f41af0dd0492ddab/benchmarks/rtx_mechanism_baselines_v1/RESULT.md
[R123]: https://github.com/leecdiang/HeteroSpec/blob/f38ed240d904db09e121bf50158cd207e829a12f/benchmarks/rtx_dispatch_intervention_v1/RESULT.md
