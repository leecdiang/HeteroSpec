# P0 独立论证、贡献与补实验审查

日期：2026-10-27。性质：作者授权的内部发展性审查工作底稿；审查代理未参与本文正文或新增分析代码编写。本报告不是外部人工同行评审，不代替作者的最终科学判断，也不保证编辑决定。

比较对象：PR145 baseline `85b3f2d6e43ea7d19fb4b0f6827cbd7f492f6fdb` 的本地 `paper_current/`，与本次 `paper_revision/`。报告只写入 `p0_review/`，没有修改正文或远程内容。

## 1. 裁决

**P0 相对 baseline 有实质增强，可以作为已增强的作者修订稿提交当前版本；不应把未执行的双平台实验设为这次修订的强制前置条件。** 增强来自证据约束和科学论证，而不是新增 GPU 实验或新方法。新增七臂原始响应审计，使原来的 repair-scope 成本比较有了更可靠的“记录到的逻辑工作相同”依据；新增 E2 草稿开关分析，使 local draft 决策得到另一执行安排下六个 session 的支持。两者都没有扩大输入人群、提供完整 GS 交互的独立复现，或建立对任意新请求的正确性保证。

这个裁决有两个不同层次：

- 对**当前有限声明**，改稿已比 baseline 更有根据，修订中发现的少量措辞问题可以局部解决，不需要无穷补 benchmark。
- 对**下一步希望扩大的声明**，最有价值的新增实验是 RTX 的独立面板 repair-scope × draft 交互，以及成功 Qwen Vulkan 路径上的 producer-conditioned consumer 检验。它们应作为结果尚空的独立实验 PR，而不能提前写成当前论文的结果。

后续实验的明确取舍如下。

| 工作 | 裁决 | 能改变的结论 |
|---|---|---|
| RTX：PR144 Qwen/Smol 固定 transfer panel，GS/PQ/QB × draft，三日期 | **保留；这是中心经济学论点最值得补的前瞻性实验** | 交互是否能迁移到原主实验以外的输入，以及相邻分臂 worker 的时间安排是否影响原方向 |
| RTX：已知 Llama 反例 CPU 定位和有限 producer/consumer 干预 | **保留，并与性能阶段解耦** | 把“互相一致但均不匹配 R”的存在性反例，推进到有边界的 producer 或 consumer 解释；允许仍未定位 |
| B570：Qwen P1/P4T × C1/PQ/QB，完整状态恢复 | **保留；先补 consumer-specific 恢复资格** | 成功 port 的局部 consumer 是否仍受 producer 状态条件约束；不要求出现正例或加速 |
| RTX 重复原主 12 例、再加 k/lifecycle 全因子 | **删除默认项** | 主要重复已完成证据，不能替代 GS × draft 的跨面板问题 |
| B570 旧 Llama KV 子集移植大全、再次 delivery、速度模型 | **删除本轮默认项** | 旧因果存在性与材料交付已有证据；新速度模型需要另一套干净服务契约 |
| 八个全新 domain × length 正交 RTX 输入 | **从当前实验 PR 移除，保留为后续另立设计** | 当前候选池无法自然填满四格；不应为“新”引入截短、拼接或结果后选择 |

提交当前改稿不是声称一般化问题已解决。提交前仍由负责数值复算和构建的任务确认实际统计结果与最终 PDF；本报告不把自己的论证审查冒充完整数值复算或原生重跑。

## 2. 实际审查范围与技能应用

实际比较了 abstract、introduction、reference contract、method、experimental design、evaluation、architecture/selection、conclusion 的基线与改稿；阅读了 new-input transfer、state/backend boundaries、related work、matched native deployment、S2/S3、`CLAIM_EVIDENCE.md` 以及新增表。还读取了七臂 `COUNTER_SEMANTICS.md`、`METHOD_CONDITIONS.md`、压缩的实际 `formal_plan.json.gz`，以及双平台工作包和与设计直接相关的 native source 入口。

没有阅读上一轮审查结论来决定本轮判断，没有编辑新增分析代码，没有独立打开全部 2,016 个原始归档 member，也没有运行新 GPU 请求。E2 的全数复算、归档身份及字段投影的完整核验由另一独立统计审查任务负责；本报告把这些结果视为待其独立确认的数值基础，重点检查结论是否由这种证据支持。

本地技能的实际应用如下，而非仅引用名称：

- `peer-review.md` 及其 ethical-review guidance：把每个实质意见绑定到位置、理由和最小补救；新实验请求必须与中心主张成比例。这里是作者自己工作区内授权的内部审查，不冒充受某期刊委任的审稿人，也未把未公开稿件传给搜索服务。
- `scholar-evaluation.md` 与 evaluation framework：分别判断 soundness 和 contribution，不用综合分数掩盖“论证更强，但创新增量有限”的差别。
- `scientific-writing.md` 与 writing principles：区分 retrospective/registered、同面板/新输入、计数相同/完整 trace 相同、时间估计/机制归因，以及自然路径/恢复干预。
- `anti-defensive-writing-en.md`：只采用围绕最强证据组织叙事、避免工程日志式正文的原则。没有采用其可能导致隐藏关键负结果的读法；Llama 失败、Smol 草稿成本和 k1 屏幕失败直接界定贡献，必须保留。

只对最近邻公开 primary work 做了定向核对：Thinking Machines 的 batch-invariant 工作、CoRun、LLM-42 和 FlashAttention-2；没有进行无目标文献扩张。公开来源见第 9 节。

## 3. 与 baseline 相比，哪些是真正增强

| 改动 | baseline 的状况 | P0 增量与为什么有用 | 不能据此推出什么 |
|---|---|---|---|
| 七臂原始响应工作审计 | 有完整输出资格、原成本表和 ratio-of-ratios，但工作匹配的直接支撑较弱 | `sections/05_evaluation.tex` 的审计段、S2 `Original-response audit of logical work` 和新增表把 2,016 formal records 匹配为 288 audit groups；检查 GS/PQ/QB 的逻辑计数、proposal/acceptance/width histograms，另列物理图差异 | 不是 per-cycle trace 或 bitwise state 证明；不消除 worker/time drift；不分解 projection/attention/FFN 时间 |
| E2 local draft-on/off 再分析 | E2 在主线中主要支持 PQ/QB representation cost；草稿开关依赖原两会话面板 | `sections/05_evaluation.tex` 的 `Draft decisions across the six E2 sessions`，及 S3 `Retrospective draft-on/off analysis`，利用现存 864 measurements 构成 216 quartets；三个家族在两种 local layout 下的六个 session 决策方向一致 | 无 GS，因此不是 full repair-scope interaction 的独立复现；同一 exposed panel、同一 host、约一天跨度；不是新输入或新 GPU 实验 |
| 历史 M3/C3 与正式 PQ/QB 身份分开 | 主文先展示较大的历史资格表，易被读者当成后续 QB 的更大面板证明 | 历史表移到 S2；S2 明确 archived `query_batch` label 不足以把 M3/C3 追认成 PQ 或 QB。主文从显式七臂证据进入贡献 | 没有凭表移动增加方法适用域；这是防止错误证据继承的实质澄清 |
| 联合策略选择 | baseline 的三项 ordered choices 容易暗示逐维贪心选择足以最优 | `sections/07_architecture.tex` 3–8 行改为在 evaluated qualified combinations 内比较同一观察成本估计，并说明各维效应不必可分离 | 不是新优化算法、在线控制器、总体最优策略或跨输入预测器 |
| target-only 收益解释 | R/M_QB 容易被理解为加速了单 token decode | `sections/05_evaluation.tex` target-only 段明确完整请求包含 prefill，continuation 是共同 q1 路径 | 不等于 single-token decoding speedup，也不等于量化了 prefill 占比 |
| graph-cache 身份 | “每 process 固定实现”已不能覆盖后来的 matched native bridge | `sections/03_method.tex` 54 行区分历史 process 固定与后续 context 固定 | 不表示同一 cached context 内的动态 PQ/QB 切换已经验证 |

上述前两项是证据增强，第三至第六项是论证有效性与可解释性增强。单纯把段落重排、缩短重复数值、把边界集中到 contract，并不单独算科学贡献；它们使真正新增的证据更容易被正确理解。

## 4. 目前最有说服力的贡献与其边界

### 4.1 最强主线应继续是 repair-scope economics

最有分量的问题不是“能否把 query 维改成 batch 维”，而是：**当保留指定数值 reference 成为约束时，修复范围怎样改变 drafting 的净价值，以及怎样以更低 graph/runtime 成本实现局部修复。** 原七臂数据把 scope effect 与 PQ/QB representation effect 分开；两种 local repair 都使 Qwen/Llama 跨过草稿盈利边界，Smol 则保留 target-only。QB 的额外价值应继续用 PQ-relative 的独立小幅收益表达，不把 GS→local 的全部收益归给 QB。

现稿在 `sections/05_evaluation.tex` 17–30 行和图注中做到了这一点。新 E2 分析支持三个 local 决策的执行稳定性，但不会让原 GS 交互变成独立确认。这个区别在主文和 S3 明说，值得保留。

原七臂 schedule 还揭示一个应明确而非夸大的边界。我直接读取了冻结 plan：它有 42 个 family/session/arm worker blocks，每个 48 个 formal slots；每个家族第二 session 对应逆序。288 是按 family/input/session/repetition 重建的跨臂审计配对组。逆序降低了单一固定顺序的疑虑，但这些组不是原生相邻随机时间块。工作审计加强了“算了多少逻辑工作”的控制，不能替代更好的时间安排。这是新增 RTX 同输入七臂时间块最明确的科学理由。

### 4.2 方法贡献是 graph/runtime 集成，不是新的 attention 数学

`sections/03_method.tex` 14–44 行的地址、mask、GQA 和输出重排证明清楚说明了一项必要语义性质；它是支持实现正确性的 proof obligation，不是新的 attention 运算定理。Q 独立、K/V 共享和 query-axis parallelism 已是成熟结构，论文已经在 introduction 与 related work 中承认。[P1–P4]

实际差异在于使用已有 non-flash operators 的 view lowering，并把 head/mask/index 语义与 phase binding、graph reuse、native speculative reconciliation 联合落实。Vulkan 的 AV-preserving 修改说明“只是改几个 shape”不能替代 backend admission 与数值路径检查。现有材料支持这项集成贡献，但不支持“首次使用 query parallelism”“不改变 kernels 即可普遍移植”或强于所有 deterministic-inference 系统的结论。

### 4.3 指定 deployed reference 是目标差异，不自动是优势证明

Thinking Machines 着重让运算对 batching/slicing 不变；CoRun 控制 prefill/decode 的执行形状；LLM-42 使用固定形状验证与 KV 修复。[P1–P3] 现稿对这些 control points 的描述与 primary source 一致。QB 的有限面板 qualification 与 LLM-42 的在线 verify–rollback 契约也确实不同。

但是“它们不以本文的已部署量化 reference 为目标”只能说明评估目标不同，不能代替同目标性能优势证据。现稿没有提出这种未经测试的 superiority 主张，也没有必要为了消除这个不存在的主张而把所有系统移植进同一 benchmark。最小要求是继续用 GS/PQ 的同 runtime 直接比较支撑自己的收益，并保持表中的目标差异。

### 4.4 当前泛化范围是有限、可重放 workload

`sections/02_problem.tex` 13–16 行的 admitted/validated/use domain 区分是关键。`sections/10_input_transfer.tex` 9 行的 Llama 反例说明 source guard 与 PQ/QB 互相一致不能认证任意新输入。三模型、多 phase、多 layer 的覆盖有价值，但并未解除 q≤4、非 flash、单 sequence、Q8_0/F16、ctx1024 和特定 numerical stack 的边界；E1 的真实 visible contexts 也比 physical key extent 小得多。

`sections/08_related_limits.tex` 40–45 行已保留这些事实。因此当前标题和主张只能按“经指定 reference 检查的 workload 上 reference-preserving”阅读。若未来把成果包装成任意新请求的安全加速器，必须另有在线保障或明确验证域；本次 P0 不能提供那个承诺。无需把这一点在每一节重复，但 contract、transfer counterexample 和 scope section 不能被叙事精简删除。

## 5. 发现的问题、严重度与最小修复

严重度约定：P0 为会使本次核心结论失效的阻断；P1 为可能导致错误科学解释、需要先修正的设计/主张问题；P2 为精度或叙事问题。这里的等级不是整篇论文评分。

| ID | 严重度 / 状态 | 位置 | 观察与最小修复 |
|---|---|---|---|
| A1 | P2，已修 | `abstract.tex` E2 新句 | 原新句容易被读成新输入复现。已改成 `on the same exposed panel`，保留 retrospective 与两日期范围。无需增加新实验来解决这个措辞问题。 |
| A2 | P2，已修 | `sections/07_architecture.tex` 3–8 行 | argmin 原来未显式区分观察成本与未知真实成本。已用 `widehat T` 并定义 observed estimate；比较集合也明确限于 evaluated qualified combinations。 |
| A3 | P1 级解释风险，已修并回读确认 | `sections/05_evaluation.tex` 审计段；S2 审计段；新增表 caption；实际 `formal_plan.json.gz` | “288 seven-arm blocks”可能让读者误认为原 schedule 具有 288 个近邻实验时间块。现已改称 matched seven-arm audit groups，S2 98行明确原 42 个分臂 worker、逆序 session，以及工作相等不能消除 between-worker temporal drift。现有 descriptive crossover 不因此被推翻。 |
| A4 | P2，已修；发现者为独立统计审查 | S2 与工作审计表的 endpoint 描述 | EOG flags 来源是保存的 normalized record，不应统称 native arrays。改为 complete native token IDs and recorded EOG flags。本人没有把该来源精度问题冒称为自己的全数原始复算发现。 |
| E1 | P1，设计已修并回读；执行前必须通过 | `B570_WORK_PACKAGE.md` B0/结果模式；`DATA_CONTRACT.md` restoration 条款 | 仅 C1 的 natural/resumed sham 不能直接排除新 speculative receiver bridge 的错误。已增加两个已有 controls 的 P1×PQ/QB×natural/resumed×off/on 共 16 请求；比较完整 producer state、endpoint、decision vectors 和 cycle。B0 由16变32，总主预算由136变152。设计纳入不等于实际sham已通过。 |
| E2 | P1，设计解释边界已纳入；不增加默认矩阵 | B570 P4T 解释；RTX A2 checkpoint 分支 | 缺少同布局 natural/resumed sham 时，把 PQ=QB≠C1 直接称为自然生产 consumer 根因会过强。设计已限定 clean-receiver contract；RTX 优先复用 A1 natural 与 A2 resumed 并保存 prefill boundary 做 same-state/sham 比较，不能拿旧 B570 sham 自动认证 CUDA。 |
| E3 | P1，既有设计已覆盖，执行时需保留 | RTX A2；B570 严格 R 行 | UB4/output4 下物理 q1 不自动等于严格 UB1/output1 R。P1+C1 必须逐输入核对 R；若不同，记录 context/configuration 边界，不把 R 换成方便通过的候选。 |

没有发现 P0 新增了一项必须通过大规模新 GPU 实验才能纠正的中心过度主张。上述 A1–A4 已用很小的精确修订解决并回读确认。E1–E3 是后续尚未实施设计的资格与解释条件，不是对当前已完成稿件的新增结果要求；已回读最终工作包中的152请求预算、speculation-sham条款和RTX的同状态绑定。

一个可选而非阻断的旧措辞改进：`sections/07_architecture.tex` 最后段的 hardware-design requirement 可写成“实现本文 evaluation contract 的硬件设计目标”。现有有限 endpoint 测试并未证明所有保留 reference 的硬件都必须采用同一 per-query 算术组织。该段已经明确未测 hardware performance，故不应把这个措辞点升级为要求做硬件实验。

## 6. RTX：保留什么，矩阵为何足够

### 6.1 主性能实验：接受当前固定方案

接受 `RTX_WORK_PACKAGE.md` 的 Qwen3 + SmolLM2、PR144 各自固定12输入、R + 3 scopes × draft on/off、k3、resident、3实际日期×2独立加载 session。两个家族在既有结果中分别提供 drafting 有利和不利的对照，足以回答有限的交互迁移问题；它们不是对“三模型总体”的随机抽样。PR144 面板现在已暴露，应称独立于原主实验的 panel transfer，不能称本次 unseen 或 blind test。

该设计增加的是三种原来没有同时具备的控制：原主面板之外的任务；同一输入下靠近执行的全部策略；实际不同日期。各家族所有臂使用同一个 executable/core，顺便消除了历史 PQ metadata-capacity 路由差异在新比较中的解释负担。不要把这些优点压缩成“请求数更多”。

| 层次 | 最小数量 | 用途 |
|---|---:|---|
| 主要科学 cells | 2 families ×12 inputs ×6 policy cells ×6 sessions =864 | 3 scopes × draft 的完整条件比较 |
| 同块严格 R | 2×12×6=144 | 实时 reference 控制和单独 R-relative 服务基准 |
| formal 合计 | 1,008 | 不把这些当作1,008个独立统计样本 |
| 固定 warmups | 84 | 每 family/session/arm 一个预定 warmup |
| 新 binary qualification | 196 | 168 capture-on 全格，28 capture-off 哨兵；与正式计时分开 |

严格说，主 `log D_QB − log D_GS` 只需要四臂；检验两种 local repair 并分离 layout effect 需要六臂。R 是 reference/部署基准，不是 scope×draft 的第七个因子。保留每块 R 是合理的小幅预算，能得到同契约的净部署基准；不应再加 A/A 重复臂、两个 lifecycle 或多个 k，把本设计扩成已做过的部署研究。

主要判断必须分别报告 `D_QB`、`D_GS` 以及交互。交互为正不表示 drafting 在 QB 下有利，Smol 恰好说明这种逻辑差别。三个日期也只能提供有限的方向复查：报告全部日期和 session 点；日期 t 区间自由度2是弱敏感性，不是可靠的人群推断或 power 证明。既定边界内的反号日期、失配输入和无触发结果必须完整保留。

PR144 中短 math 与长 code 混杂不妨碍这个固定面板交互，但不允许解释为独立 length effect 或 domain effect。没有必要为了这个未声称的因果问题把本次 panel 再换掉。全部旧主12例追加复现，以及八新正交输入，都从默认矩阵删除。

### 6.2 Llama：先定位，允许有限失败结题

接受 A0 的零 GPU 原始 decision/cycle 重建；只有共同自然前缀上的可比行才能用于首次字节差、top1差和endpoint差判断。首次 logit 字节差不是根因，且原 observer 没有逐层 Q/K/V 数据，这个限制不能被代码推测补齐。

接受 A1 的1失败+2通过控制、R/PQ/QB、observer off/on 共18请求。若同一 reference 已稳定而旧反例在新 driver 消失，结论应是 runtime-dependent counterexample，不能未经识别改动就称“修复”。

接受 A2 的2 producer×3 consumer×3输入×off/on 共36请求，以及最多12个 C1自然/恢复 sham。若采用 checkpoint 方法，应把 A1 的 prefill 全状态与 A2 donor 绑定，并在同状态条件下复用其 natural/resumed PQ/QB 对照。若无法建立该绑定，先收窄归因，不无条件扩大成新网格。P1+C1 的 UB4/output4 配置必须独立匹配严格 R。

只有 A2 留下明确问题时才启用有上限的真实算子 capture/replay；每个 replay 先过 native own-path sham。最多一次可解释 source fix 合理，但“修到通过”不是完成标准。Llama 不进入默认正式 timing cohort；不许删掉失败输入、悄悄回到原12例，或阻塞两个已资格家族的独立复现。

## 7. B570：以成功 port 的 producer 边界为终点

### 7.1 研究问题有增量，但不是当前稿件的逻辑欠债

旧 Llama Q6_K 研究已经证明，在其被测输入与恢复契约下，上游状态能够决定后续差异。再做一次同样的 whole-KV/initial-logit 交叉，不会填补当前最有价值的空白。新问题是成功移植的 Qwen GQA/AV-preserving 路径是否具有同样的条件边界；这把“成功 port”与“producer 必须资格”连接在同一个实现中。

这值得做，却不能说当前论文没有它就不成立：现稿已经把 Qwen 成功范围和 Llama 失败范围分开。其必要性取决于是否要扩大“成功 port 在 producer 改变后仍可使用”的主张。

### 7.2 接受 P1/P4T × C1/PQ/QB；按修正后的152请求实施

P4T 的尾长3固定拆成2+1，是一项新冻结 caller recipe，不能写成任意 UB4 自然分块的代表。producer固定PQ、target UB4/output4，draft producer固定serial；consumer在clean contexts内保持自己的layout，导入完整sequence KV/positions和initial logits，并正确重建第一次采样与pending语义。这使估计对象成为完整 producer numerical state 的总效应，而非未经额外交叉证明的“KV唯一原因”。

八个新自然输入按CPU属性与历史曝光排除冻结，两长度带各4，满足 key extent 上限即可。domain×length 正交不是这个机制问题的必要条件。若静态候选不足，必须在首次forward前决定缩为四例；不能在无触发后追加或换题。

| 阶段 | 数量 | 说明 |
|---|---:|---|
| B0 C1 恢复与 observer controls | 16 | 两个旧controls×2producer×natural/resumed×off/on |
| B0 新增 spec consumer own-path controls | 16 | 两个旧controls×PQ/QB×natural/resumed(P1)×off/on |
| B1 严格 R | 8 | UB1/output1，不把 q1 的 UB4候选当R |
| B1 自然 producer+C1 | 32 | 8×2producer×off/on |
| B1 每个 donor 自身 resumed C1 sham | 16 | 每个新输入自己通过状态及endpoint检查 |
| B1 local consumers | 64 | 8×2producer×PQ/QB×off/on |
| **默认合计** | **152** | 8个新输入的有限机制实验；重复不构成152个独立输入 |

新增16请求不是重做全部 delivery，而是排除本实验新引入的恢复/speculation桥错误。P1自然PQ/QB的prefill state应与其恢复donor一致，并对照PR148历史完整reference和对应cycle/vector。若不一致，先修复或停止恢复方法资格，不能把它报告为新输入上的方法失败。

P4T 条件下，在没有layout-specific自然sham时，所有结论限定于 boundary0 clean-receiver contract。若同donor下PQ=QB≠C1，可以报告恢复契约内的reference失败；不能直接宣称未经测试的完整自然生产路径也会如此。真正需要自然路径归因时，再做与该具体反例相配的有限验证，而非默认扩展整个矩阵。

### 7.3 保留负结果，删除不必要扩展

以下结果都能完成本实验：producer state不同但所有endpoint相同；consumer忠实保持不同producer各自的C1轨迹；同donor下局部consumer不匹配C1；或恢复契约失败而只能保留自然观测。第一个结果只是有限no-trigger，不是一般不变性；最后一个结果是恢复方法边界，不是GPU方法性能失败。

默认关闭额外 KV×initial-logits 2×2、q4 operator grid、partition sweep、第三模型、CPU/Vulkan draft placement对照和性能预测模型。只有需要改变已写的具体主张时才另立设计。恢复型请求外置了producer并添加readback/import，不能把它的时间当完整生产服务收益，也不能与PR143的不同CPU-draft契约混合拟合。

## 8. 最终交付建议

当前稿件应按“局部repair改变草稿经济性；QB降低实现成本；reference资格由完整请求与producer条件共同约束”这一顺序提交增强版本。新增E2表和七臂audit保留在主线/补充的现位置；历史M3身份、关键失败与scope继续保留。无需把所有材料认证流程搬进主文。

两平台实验PR可以现在提交可审查设计与实现，但result字段必须保持未执行。RTX以固定PR144 panel和实际日期slots执行；B570按新增consumer恢复gate后的152请求矩阵执行。任何负结果或未完成状态都依冻结规则报告，不要求每个平台交付新的加速正例。

**最终科学判断：P0已增强论证可靠性和中心结果的可解释性，创新主张应维持原有集成方法与repair–draft实证的范围；没有依据把它升级为普遍确定性方法或跨平台通用加速结论。当前增强稿可以推进，有限补实验继续独立完成。**

## 9. 定向核对的公开 primary sources 与方法归属

- [P1] Horace He and Thinking Machines Lab, *Defeating Nondeterminism in LLM Inference* (2025), sections “Batch-invariant matrix multiplication” and “Batch-invariant attention”：https://thinkingmachines.ai/blog/defeating-nondeterminism-in-llm-inference/ 。核对点为固定 reduction/tiling、KV布局与固定split-size；不是对本文速度的外部验证。
- [P2] Raja Gond, Aditya K Kamath, Ramachandran Ramjee, Ashish Panwar, *LLM-42: Enabling Determinism in LLM Inference with Verified Speculation*, arXiv:2601.17768v2：https://arxiv.org/html/2601.17768v2 。核对点为fixed-shape verifier、verify–rollback和已验证window的KV替换，尤其“Making KV cache consistent”。
- [P3] Shiju Zhao et al., *CoRun: Padding is Simple and Efficient for Deterministic LLM Inference*, arXiv:2608.14376v1：https://arxiv.org/html/2608.14376v1 。核对点为IV-A/IV-B的determinism contract、isolated prefill、fixed-shape decode、decode Split-KV与collective约束。
- [P4] Tri Dao, *FlashAttention-2: Faster Attention with Better Parallelism and Work Partitioning*, arXiv:2307.08691：https://arxiv.org/html/2307.08691v1 。核对点为query-axis work partition与GQA共享K/V语义；不据此否定不同runtime约束下的QB集成贡献。
- 本报告程序性使用了本地Scientific Agent Skills审稿/科学写作指导；依其归属要求注明：Timothy Kassis, Vinayak Agarwal, Yuhuan He, Darshil Patel, Aubrey M. Brueckner (2026), *Scientific Agent Skills: A Library of Procedural Knowledge for Research Agents*, https://doi.org/10.48550/arXiv.2609.00065 。作者与年份已从官方记录核对。这是程序来源，不是论文结论正确性的证据，也未加入论文正文参考文献。

