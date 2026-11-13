# HeteroSpec 论文图示研究与实施建议

研究日期：2026-11-08。范围：参考图辨析、真实系统论文图例、现有图与证据审查、后续绘图规格和工具选择。

**建议升级图组，但无需把现有图全部推翻。** 最有价值的变化是让读者用五张主图看懂：参考为何失效、如何保留并行、何时有收益、完整服务是否获益、收益来自哪个因素。统一语义、可复核数据和明确的对照，比复杂装饰更接近优秀系统论文。

本文件只记录研究结论，不包含新实验、新性能图、正文改写、基线替换或发布操作。后续正式作图与论文整合应等待 #205/#206 的最终资格、正式性能及证据收口；未运行或未完成的格子必须保留其真实状态。以下数量和结论均属于所注明的冻结版本，不代表未来实验结果。

## 1 参考图片值得借鉴什么

三张参考图经原论文核对，分别对应 [LaVer 原文](https://arxiv.org/html/2512.06281v1) 的 Fig. 3、Fig. 1 和 Fig. 2。该版本是多模态学习论文预印本，不能仅凭图片外观把它当作 TPDS 的审稿标准。

- **图片一，Fig. 3：借鉴机制层次。** 总体框架、不同数据实体、训练状态和局部机制放大共同说明方法。HeteroSpec 可借鉴“同一个请求从逻辑位置到物理前缀，再到执行图”的连续示例；不应搬入无关的教师网络、雪花/火焰图标或训练模块。
- **图片二，Fig. 1：不建议照搬雷达图。** 图中不同基准的尺度不同，雷达面积不是可解释的统一收益。HeteroSpec 的耗时、内存、数值资格、接受率也不能放在同一面积里排名。按度量分面、配对点图和明确基线的森林图更可靠。
- **图片三，Fig. 2：借鉴多面板证据链。** 热图、局部表示和定量曲线回答互补问题。HeteroSpec 应使用真实误差、首次分歧和干预对照；t-SNE 的距离或簇分离不能证明 token、全词表向量或 KV 状态一致。

借鉴结构和信息组织，不复制原图的布局细节、图标、数据或配色组合。此次不把第三方图片加入仓库。

## 2 从真实系统论文中学习图的组织方式

下表是面向 HeteroSpec 的小规模原文案例研究，不是“所有顶刊图”的统计调查。SOSP、OSDI、ASPLOS 是系统顶会，NeurIPS 是机器学习会议；它们与 TPDS 期刊的类型明确分开。图号以链接版本为准。

| 原文实例 | 图中解决的问题 | HeteroSpec 可采用的方法 | 不应照搬 |
|---|---|---|---|
| [PipeMesh，TPDS 36(9)，2025，Fig. 1，PDF 第 2 页](https://hub.hku.hk/bitstream/10722/361925/1/content.pdf#page=2)，[DOI](https://doi.org/10.1109/TPDS.2025.3583983) | 同一布局并列三种调度；微批编号、计算/通信和 activation lifespan 都有语义 | 固定请求与相同输入，逐层比较 whole cuts 和 local cuts；用相同图元追踪状态生命周期 | 不把示意宽度当计时，不画本项目未测的流水重叠 |
| [FlashAttention，NeurIPS 2022，Fig. 1，PDF 第 2 页](https://proceedings.neurips.cc/paper_files/paper/2022/file/67d57c32e20fd0a7a302cb81d36e40d5-Paper-Conference.pdf#page=2) | 内存层级、张量分块与时间分解把优化原因联系到成本 | 让 KV 存储、query/mask view、物理 extent 与真实成本相互对应 | 不借用其 IO/复杂度结论，也不复制不适用的 HBM/SRAM 分层 |
| [vLLM/PagedAttention，SOSP 2023，Fig. 6，PDF 第 6 页](https://arxiv.org/pdf/2309.06180#page=6) | 用具体实例展示逻辑块、块表和物理块的关系 | 以 positions 765–768 的可追踪实例说明“逻辑遮罩相同，物理计算范围仍不同” | 不把 HeteroSpec 画成分页 KV 算法 |
| [SpecInfer，ASPLOS 2024，Fig. 2，PDF 第 4 页](https://arxiv.org/pdf/2305.09781#page=4) | 组织 token tree、验证和同步的完整闭环 | 总览图交代 draft、verify、commit/rollback 和 pending 的边界，局部放大 attention lowering | 本项目固定 k3/q4 路径不能画成已支持任意 token tree |
| [DistServe，OSDI 2024，Fig. 1，PDF 第 2 页](https://www.usenix.org/system/files/osdi24-zhong-yinmin.pdf#page=2) | 把两类延迟约束随负载变化的矛盾放在同一问题设定中 | 分开 resident service、first complete result 和资源成本，标明每项指标的定义 | 不把本地 request service 改称在线 goodput、QPS 或 TTFT |

这些图的共同优点是固定比较对象、清楚标注状态和度量、把机制与代价联系起来。原论文图形本身不证明作者用了哪个绘图软件；除非公开源文件确认，不应声称“顶刊都用某软件”。本文后面的工具是针对本仓库的实施建议。

补充案例：[Kistler 与 Alvisi，TPDS 16(9)，2005，Fig. 2–4、9–10](https://www.cs.cornell.edu/lorenzo/papers/kistlertpds.pdf#page=7) 从性能、覆盖率与等待时间走到消息量和字节开销，并保留退化工作负载。值得借鉴的是收益、机制、成本、边界的证据组织，而不是照搬老式密集纹理柱形。

## 3 仓库现状与版本边界

研究基准是 [main cfc9edf4582bb3c02885c9171a2ab2635bf19588](https://github.com/leecdiang/HeteroSpec/tree/cfc9edf4582bb3c02885c9171a2ab2635bf19588)。检查了实际目录、TeX 源、重建脚本入口和结果 JSON，而非只看旧 README。

### 3.1 已有图具备值得保留的基础

在该树的 [11 月 3 日候选稿](https://github.com/leecdiang/HeteroSpec/tree/cfc9edf4582bb3c02885c9171a2ab2635bf19588/paper/reference_batching_20261103) 中：

| 已有图 | 已经做对的事 | 下一步 |
|---|---|---|
| `figures/prefix.tex` | scalar / unsplit / compatible groups 并列，示例含 768/1024 extent | 扩展到逻辑位置、物理 extent、外层并行和局部 cut 的一张机制图 |
| `figures/layout_cost.tex` | CUDA/Vulkan 六个 session 点、聚合菱形、1.0 和各研究自己的实用阈值 | 保留；不要改成只有均值的柱图，不把旧阈值移植到新 R2 |
| `figures/scope_transfer.tex` | 三个日期、聚合和 scope interaction 分开；线段明确为 date range 而非 CI | 保留历史语义；如篇幅不足移到补充材料而非删除负结果 |
| `data/SOURCE_MANIFEST.json` 与 `scripts/reconstruct.py` | 已有数据来源与重建链 | 后续作图延续脚本生成，不手改图中的数值 |

[11 月 1 日视觉审查](https://github.com/leecdiang/HeteroSpec/blob/cfc9edf4582bb3c02885c9171a2ab2635bf19588/docs/research/visual_review_20261101/REVIEW.md) 也已强调完整失败格、灰度冗余、范围与 CI 区别。因此“简单”不能等同于“不严谨”。当前缺口主要是最新实验仍分散在多个结果分支，主图尚未统一讲清机制、比较对象和因素归因。

版本注意：#164 在本次查询中仍为 open，但上述目录实际存在于 main 的集成树中；旧导航中的“目录不在 main”等说法不能替代实际文件检查。本文不据此改动论文版本标识，也不推断已提交或已获作者定稿批准。

### 3.2 最新证据决定图应该诚实地讲什么

- **RTX #195：** 独立 16-root、4-session resident panel；D4 对四个固定 target-only M 的总服务比为约 0.693–0.709。它回答 D4 相对完整强基线是否获益，不自动证明 LOCAL 的独立收益。
- **B570 #194 保存快照：** 12 个指定 append 坐标，所有 crossing 格 LOCAL 较快，所有 inside 格略慢。它是机制诊断，不是自然请求总体平均加速。
- **Linux/A5000 #203：** 同四个固定 M 的比值约 0.816–0.828；旧 16 roots 已暴露，属于 deployment transfer。两个 D4 的约 2% 差别同时改变 cut 和 projection，且顺序有混杂。
- **Linux/A5000 #204 M1：** 平衡四 D4 因子实验把 packing 的约 1.56–1.64% 与 LOCAL 的约 0.13–0.21% 分开；packed 下 LOCAL 区间包含无收益。20/2224 逻辑 verification cycles 需要 SIMPLE rechunk，提供了小 cut 收益的实际工作解释。
- **#205/#206：** 在本次锁定版本中，仍有资格收口和/或正式性能尚未完成。不能把资格成功、容量准入或 pilot 填成正式服务收益。

## 4 推荐五张主图和两张补充图

以下是图的规格，不是已生成的结果。图号待论文结构最终确定。每图只承担一个主要论点。

### 主图 A 参考约束下的执行机制

**要回答：为什么仅保持 causal mask 还不够，LOCAL 到底保留了哪一部分并行？**

- (a) 用同一个 append 的 positions 765、766、767、768，标出原 scalar 所需 extent 768、768、768、1024。逻辑可见范围和物理 operand extent 分层展示，不用相同阴影混为一谈。
- (b) 对比普通 unsplit、whole-graph rechunk 和 LOCAL attention grouping。外层 projection/FFN 的宽度与 attention 的局部分组分别画清，避免把 LOCAL 画成整个图都串行。
- (c) 展示 paired Q/mask views、shared KV、按 query 顺序合并；底部小框标明 activation/placement policy 和 graph reuse key。
- 用箭头表示数据依赖，虚线表示约束/对应关系；共享 KV 用同一实体而不是多个看似复制的缓存。commit/rollback 与 pending 保留在执行边界处。
- **来源：** 候选稿 `02_mechanisms.tex`、`03_method.tex`、`figures/prefix.tex`，以及 #195/#194 的实际物理工作记录。
- **限制：** 765–768 是已观测案例；矩形长度不是运行时间。R、whole 和 LOCAL 的具体含义必须按各部署绑定，不能把不同阶段的历史实现拼成一个假想已测系统。
- **工具/成本：** 复用 TikZ 或使用可编辑 SVG，P1，中等工作量。数据验证和实验最终口径确定后再定版。

### 主图 B 数值修复的可观测证据

**要回答：何时出现内部差异，哪些干预真正消除了它？**

- (a) 时间/输出位置线上标注已记录的首次 full-vector 差异和首次 token 差异。已知 Llama CUDA 案例分别为输出 29 与 81，标清零基索引。
- (b) 干预矩阵展示原路径、仅 activation 修复、加 prefix 修复及逆向撤销；分别编码 token/EOG、请求的 full vectors、active KV/frontier，而不是一个笼统的绿色“correct”。
- (c) 只有存在足够逐位置原始记录时才画共享色标误差热图；没有的字段用 NA，不从两个已知事件点插值造曲线。
- 数值“bitwise equal”和“within tolerance”要用不同文字；完整 KV 与 frontier 也应分项。误差为零不能在 log 色标上任意加 epsilon 后伪装成精确测量。
- **来源：** 候选稿的机制章节、`data/SOURCE_MANIFEST.json` 指向的 #162/#163 原始报告，未来补入 #205 最终冻结的独立 Linux R 资格。
- **限制：** 不用 t-SNE、余弦相似度或 greedy token 匹配替代全向量/状态证据；形式资格范围不等于每次 formal clean request 都再次重放了内部状态。
- **工具/成本：** Matplotlib + 现有只读统计记录，P1，中到高，成本来自证据对齐而非画图。无新 GPU 需求的部分先做，缺记录就缩小图的声明。

### 主图 C 结构条件何时有收益

**要回答：跨边界、q、模型、capacity 对收益方向有什么影响？**

- RTX 与 B570 分成独立 panels；行列固定顺序包含所有 inside/crossing、q 和 capacity 格。
- 小型热图编码固定分子/分母的时间比值，以 1 为中性。建议使用 `log2(ratio)` 的对称发散色标，并在格内写实际 ratio；独立的绝对 ms 点图提供量级。
- 重复仅 2 次的 RTX 和 3 次的 B570 显示所有点或原始范围，不能制造总体 CI 或平滑的“性能地形”。
- RTX 的 cut 和 projection 两个因素分面，保留 Qwen packed regressions；B570 inside 的所有负收益都必须可见。
- **来源：** E2、E3，下节列出精确路径。
- **限制：** 这是选择过的结构坐标。不得把 12 格均值当自然 workload 加速，不从格子的数量估计自然 crossing 频率。
- **工具/成本：** Matplotlib，P1，低到中。从已冻结 JSON/完整 timing 记录生成，不重跑实验。

### 主图 D 对完整强基线的 resident service

**要回答：D4 相对每一个固定 target-only baseline 是否更快，差异有多大？**

- 按部署分面展示 ratio 森林图：四个固定 M 必须全部保留。每行一个聚合点与原研究区间，旁列绝对总服务秒、测量请求数。
- RTX R2 使用原四比较族的 98.75% percentile intervals；Linux #203 使用其五比较族的 99% intervals。不能为了视觉一致把区间改写成 95%。
- 分母和方向印在图内，例如 `D4 / fixed M (lower is better)`；画 1.0 参考线。R2 未核实存在实用阈值，因此不添加旧 Llama A/A screen。
- 主 panel 可放聚合结果，补充 panel 放所有 per-root 和 per-session 点；root-cluster bootstrap 的单位是 root，4 sessions 在 root 内一起保留，不把 64 requests 当 64 独立样本。
- **来源：** E1、E4。未来 #205/#206 只能在正式 panel 完成、比较族/基线冻结且报告审查后成为新 panel。
- **限制：** 不用事后最快 M；不混 Windows 与 Linux 时间，不把 transfer roots 称为 unseen confirmation。#203 两个 D4 的差别单列描述，不能标注“LOCAL causal gain”。
- **工具/成本：** Matplotlib 或 PGFPlots，P1，低到中。

### 主图 E 分离 LOCAL 与 packing 的因素归因

**要回答：整体变化究竟来自 cut、projection，还是二者交互？**

- (a) 2×2 矩阵明确 whole/local × loop4/packed，四个实测 D4 arms 对应四个角。标绝对 complete service，不用面积编码耗时。
- (b) 四个预注册直接 contrasts 的森林图，加一个独立 interaction 行，保留所有五个 99% 区间。
- (c) 旁列实际工作：20/2224 逻辑 cycles 发生 SIMPLE rechunk；q4 verification 没有 wide packing，packing 机会主要在 prefill。图中区分 logical cycles、physical calls、scheduled graph nodes 和 GPU kernel activities。
- **来源：** E5 的 `all_fixed_controls`、`interaction`、`totals`，及 README/physical census。interaction 是逐 root ratio 的 geometric mean，不是四个 pooled totals 的代数比。
- **限制：** 0.128% cut point estimate 的区间跨 1，不能隐藏；交互不支持有利协同。组合 1.7615% 仅描述，不冒充新增预注册显著性检验。该 panel 没有 target-only M，不能单凭它判断 speculation profitability。
- **工具/成本：** Matplotlib，P1，低到中。优先级很高，因为它直接防止论文误归因。

### 补充图 S1 完整成本与资源取舍

**要回答：resident gain 是否同时降低启动、整段工作时间和资源成本？**

- 分面展示 resident service、实际 test burst、first complete result、worker wall 和 memory，单位分别固定。
- 只有证明同一测量窗口内互斥且覆盖完整的 phase 才能堆叠；service、burst、worker、wrapper 等重叠窗口不能相加。
- `other_service_s` 若为算术 residual，要写明不是独立时钟；unmeasured 保留 null/NA，不填零。
- 采样 device-global memory 与 total-minus-free 的定义依部署分别标注，不伪装成 process peak；不要画未经量测的能耗/碳排。
- **来源：** E1 的 `actual_host_windows`、cost-coverage，E4/E5 的 clock/memory scope 文件。
- **限制：** #204 worker totals 近乎相同，不支持把 resident 的 packing gain 宣传为相同幅度的 cold-start gain；first complete result 不是 TTFT。
- **工具/成本：** Matplotlib，P2，中。若篇幅允许，应把最影响主结论的成本 panel 放主文，而不是把所有成本藏到附录。

### 补充图 S2 资格与适用边界矩阵

**要回答：在哪些部署和机制上，实际验证到了哪一步？**

- 行为 model × backend × context，列为 reference identity、requested vectors、active KV/frontier、transaction/EOG、clean/heavy bridge、formal service。
- 每格用文字与符号同时编码：PASS、MISMATCH、UNSUPPORTED、NOT_RUN、PENDING、NA；其中 NA 是不适用，NOT_RUN 是未执行，二者不能合并。
- 原始失败与最终修复分成版本行或清楚的脚注，不用最终绿色覆盖旧失败。资格通过和性能获益使用不同列。
- **来源：** 候选稿 coverage matrix、各平台 VALIDATION/RESULT，#205/#206 最终收口后增行。
- **限制：** 不把 helper tests、source rebuild、readback 或 clean endpoint checks 提升为全内部状态的独立复现。跨设备不主张 bit identity。
- **工具/成本：** 简单 LaTeX 表格或矢量矩阵足够，P2，低到中；若它决定论文适用范围，正文保留其压缩版。

## 5 可追溯的数据入口

这些是研究时实际检查的入口。后续绘图使用固定 commit，不使用漂移的分支名。表中路径均相对于对应 commit 的仓库根目录。

| ID | 冻结入口 | 已确认可用的字段/事实 | 用途 |
|---|---|---|---|
| E0 | [候选稿源码，main cfc9edf4](https://github.com/leecdiang/HeteroSpec/tree/cfc9edf4582bb3c02885c9171a2ab2635bf19588/paper/reference_batching_20261103) | prefix 例子、完整机制说明、source manifest、已有 timing 图 | A/B、保留旧图 |
| E1 | [RTX R2 RESULTS.json](https://github.com/leecdiang/HeteroSpec/blob/cfc9edf4582bb3c02885c9171a2ab2635bf19588/benchmarks/tpds_phase1_v1/host_evidence/R2/RESULTS.json) | `primary.contrasts[].total_ratio/adjusted_interval/per_root/per_session`、`primary.totals_s`、`actual_host_windows`；同目录 `MEASUREMENT-COST-COVERAGE.json` 有 coverage | D/S1 |
| E2 | [RTX R1-STRUCT RESULTS.json](https://github.com/leecdiang/HeteroSpec/blob/cfc9edf4582bb3c02885c9171a2ab2635bf19588/benchmarks/tpds_phase1_v1/host_evidence/R1-STRUCT/RESULTS.json) | `coordinates[].cell/times_s/paired_total_ratios`，2 repetitions；[完整结果](https://github.com/leecdiang/HeteroSpec/blob/cfc9edf4582bb3c02885c9171a2ab2635bf19588/benchmarks/tpds_phase1_v1/RESULT.md) | C |
| E3 | [B570 保存快照 RESULT.md](https://github.com/leecdiang/HeteroSpec/blob/cfc9edf4582bb3c02885c9171a2ab2635bf19588/platforms/b570_snapshot/benchmarks/tpds_phase1_v1/RESULT.md) | 12 coordinates 的全部均值、3 repetitions 定义、inside/crossing 方向、clock/输出-row 限制；原重复入口 `evidence/B570_FORMAL_RECORDS.json` 由报告给出 | C/S2 |
| E4 | [Linux #203，592abdfe，RESULTS.json](https://github.com/leecdiang/HeteroSpec/blob/592abdfe9267fd97ecbde18cd0ee9a1bfc319e20/benchmarks/linux_transfer_v1/results_ampere_20261107/RESULTS.json) | `contrasts[].total_ratio/adjusted_interval/per_root/per_session`、`totals_s`、`host_windows`；同目录 README 定义 fixed-order confound | D/S1 |
| E5 | [M1 #204，55f501e9，RESULTS.json](https://github.com/leecdiang/HeteroSpec/blob/55f501e9a93013a4b4d82cc4967e82b8d9054a81/benchmarks/server_expansion_v1/M/results_ampere_m1_20261107/RESULTS.json) | `all_fixed_controls[].total_ratio/interval/root_ratios/session_ratios`、`interaction`、`totals`；同目录 README 定义 20/2224、q4 负对照和 memory scope | E/S1 |
| E6 | [#205 锁定 254a4926](https://github.com/leecdiang/HeteroSpec/commit/254a4926d757b9477b92876c245d3c37c4e390f2)；[#206 锁定 6788af25](https://github.com/leecdiang/HeteroSpec/commit/6788af259f341844a546d977e663c6006b996aaf) | 当时资格/正式 panel 未收口；仅作为等待状态，不作为最终性能来源 | B/D/S2 待更新 |

特别注意 root 布局的 `benchmarks/tpds_phase1_v1` 是 RTX 版本，B570 应从 `platforms/b570_snapshot` 读。两平台的同名文件不能互相覆盖或混配。

**后续每图的数据契约：** 记录 source commit、输入文件 SHA256、study/model/backend/reference ID、arm 与 baseline、measurement window、unit、root/session/repeat、status、缺失原因、estimator、interval family/level。原始 field 名不同可由 adapter 统一，但不能改变定义。

建议后续作图 PR 同时交付源数据清单、只读导出器、绘图脚本、矢量 PDF、预览 PNG 与数值核对结果。本文没有把脚本样例冒充已经完成的工具。

## 6 科学可视化与版式规范

1. **一图一主要问题。** 标题指出比较，caption 给样本单位、分母、时间窗口、区间含义和最重要范围限制。不要在标题中预写尚未得到的“显著提升”。
2. **配色编码固定。** 同一 arm 在全篇保持一致；cut 可用颜色，projection 用 marker/线型，状态用符号与文字。避免同一绿色同时表示 LOCAL、PASS、速度最快三种意义。
3. **热图依据数据类型选色。** 非负误差用顺序色标；相对 1 的性能变化用发散色标或 log-ratio；同类 panels 用同一范围。避免 rainbow/jet。依据见 [Matplotlib 官方色标说明](https://matplotlib.org/stable/users/explain/colors/colormaps.html)。
4. **不通过裁剪制造优势。** 柱形长度通常从零起；森林图可局部放大但明确刻度和 1.0。不得把 0.1% 的增量画成大面积优势而隐藏绝对秒数。
5. **统计定义不因美观改变。** ratio of totals、mean ratio、geometric mean 是不同 estimands；保持原研究定义。observed range、SD、SE、bootstrap CI、practical screen 分别标注。
6. **负结果和未完成有独立编码。** 不删除回退格，不在 log 轴把失败/缺失填为零，不用“没有误差条”暗示没有不确定性。
7. **少样本不画虚假的分布细节。** 2–4 次重复不适合 violin/KDE；先显示所有原始点。ECDF 只有在需要呈现分布且所有数据可用时使用，重复结构仍要解释。
8. **优先矢量输出。** IEEE 接受 PDF/EPS/PS 等；嵌入字体。单/双栏参考宽度为 88.9/182 mm；成品字号约 9–10 pt，不是源画布字号。以投稿模板最终尺寸为准。[IEEE 格式](https://journals.ieeeauthorcenter.ieee.org/create-your-ieee-journal-article/create-graphics-for-your-article/file-formatting/)、[尺寸与分辨率](https://journals.ieeeauthorcenter.ieee.org/create-your-ieee-journal-article/create-graphics-for-your-article/resolution-and-size/)。
9. **栅格只用于需要栅格的内容。** IEEE 对非矢量彩色/灰度要求 >300 dpi、黑白线稿 >600 dpi；后期上采样不会补回细节。SVG 可作编辑源，提交时转受支持的 PDF 等格式。
10. **实际尺寸复核。** 检查单栏/双栏 100% 尺寸、灰度、色觉辨识、字体嵌入、caption 与 panels 的对应。不要用截图替代清晰的原生坐标和文字。

不优先采用：雷达图、3D 柱图、装饰性 Sankey、没有真实组成关系的堆叠图、无相关观测的 attention 热图、为体现“高级”而加入的 UMAP/t-SNE、没有完整公平样本的 Pareto frontier。

## 7 工具和 skill 的选择

### 7.1 默认采用仓库已经具备的数据驱动路线

- **Matplotlib + NumPy/pandas：** 用于森林图、paired dot、factorial、热图和共享尺度多面板。样式和 export 参数集中定义；保留可重建 CSV/JSON。当前研究环境实际 import 成功：Matplotlib 3.10.8、NumPy 2.3.5、pandas 2.2.3。Seaborn 0.13.2 也可 import，但默认统计聚合/CI 不应用来覆盖原研究 estimator。
- **TikZ/PGFPlots：** 适合复用现有 mechanism 图和与论文一致的字体、公式；[官方项目](https://ctan.org/pkg/pgfplots)支持从明确坐标生成图。当前环境有 pdflatex 命令，但真实编译检查失败，原因是缺少 `pdflatex.fmt`；设置可写缓存目录后仍缺格式。**不能宣称 TeX 编译链已就绪**。应在已有完整 TeX 环境或后续补齐依赖后验证。
- **Inkscape/SVG：** 适合机制图排版与手工微调，但不手改科学数值；由数据脚本生成的 panel 应当保持为可重建元素。Graphviz 适合初始依赖图，不能替代最终出版版式检查。
- **Poppler：** 用于后续 PDF 栅格复核和字体检查；命令可用不等于论文已成功编译。
- **收费软件无需作为前置条件。** 当前没有理由购买 Illustrator、Origin 或 BioRender 才能完成本项目的出版级图。可根据作者既有熟练度选择，但不能从成图推断原作者使用它们。

### 7.2 公共 skills 只作流程辅助

- **[K-Dense scientific-visualization](https://github.com/K-Dense-AI/scientific-agent-skills/blob/main/skills/scientific-visualization/SKILL.md)：** 已核对官方公开文档，适合图形选型、uncertainty/missingness、多面板、可访问性与导出检查。可以作为下一次作图的审查清单。**本次未安装、未运行该 skill**，不等于它的所有依赖已验证。
- **[K-Dense scientific-schematics](https://github.com/K-Dense-AI/scientific-agent-skills/blob/main/skills/scientific-schematics/SKILL.md)：** 已核对官方文档，依赖外部 OpenRouter API，输出 PNG 草图而非可编辑矢量。最多用于非定量布局灵感；不作为正式 tensor 图或统计图的首选。自动评分不能验证科学正确性；此次未安装、未运行、未调用外部生成。
- **本地工具冒烟检查：** 实际完成 Matplotlib→PDF→Poppler PNG、Inkscape SVG→PDF、Graphviz DOT→PDF 的最小样例。它们证明基础导出通路，不证明最终 HeteroSpec 图已完成。Matplotlib 可设置 `pdf.fonttype=42`，再用 `pdffonts` 检查；缓存目录设到可写位置。输出格式见 [Matplotlib 官方说明](https://matplotlib.org/stable/users/explain/figure/backends.html)。

任何 skill 都不代替数据 provenance、统计定义和原稿实际尺寸复核。此次不安装新 skill、不配置外部 API、不上传论文私有材料。

## 8 实施顺序与成本

以下是工程量级判断，不是承诺时限或计算预算；本任务不启动任何 GPU 实验。

| 阶段 | 工作 | 预计投入级别 | 开始条件 |
|---|---|---|---|
| P0 | 定稿论点、锁定各 study、核对五张主图的数据字段和 status | 约半天量级 | #205/#206 最终范围与收口状态明确；先可审查已冻结来源 |
| P1a | 主图 D/E，复用已保存 ratios/intervals；明确基线与因子 | 约半天至一天 | 每个来源通过独立数值核对 |
| P1b | 主图 A/B/C，原创机制设计与修复证据拼接 | 约一至两天 | 机制与最终资格范围确认，缺失数据不补造 |
| P2 | S1/S2、统一样式、caption、灰度和双栏检查 | 约半天至一天 | 主图冻结与完整 TeX/导出环境就绪 |

整个图组通常是数个人工作日量级，而不是先采购算力或绘图软件。若只做第一批，优先 **A + D + E**：机制、完整服务、因素归因。结构图 C 的已有数据重排成本低；修复图 B 的主要成本是逐项溯源。不能为了热图或更多采样点临时追加未经设计的新实验。

## 9 后续绘图 PR 的验收清单

- [ ] #205/#206 已明确终态，正式结果、pilot、资格和 NOT_RUN 没有混用。
- [ ] 每图的 source commit/文件 hash/字段和比较方向可追溯。
- [ ] RTX/B570 独立命名空间，Linux 独立 R，旧参考与新参考不混配。
- [ ] 所有固定 baselines、负结果、失败和缺失保留。
- [ ] 原 estimands、root clustering、multiple-comparison family、区间级别未改变。
- [ ] 时间窗互斥性/包含关系、memory 采样定义、NULL 成本经过检查。
- [ ] 可从固定输入一条命令生成 PDF/PNG，不手动改数值。
- [ ] 图中所有矩阵、曲线和示意都标明 measured / derived / schematic。
- [ ] 最终实际尺寸、灰度、字体嵌入、截断/重叠与 caption 完成复核。
- [ ] 原创机制布局；外部图只作为参考，引用原论文，不复制截图充当本研究结果。

本次验证范围：读取了三张用户参考图与其原文对应关系，核对系统论文实例、仓库实际图源码和上述主要结果/字段；检查了 Python 工具 import，并尝试现有 TeX 图的局部只读重建，后者因格式依赖缺失未成功。没有运行模型、改动实验、重新计算新的统计检验或宣称完成最终成图视觉验收。

