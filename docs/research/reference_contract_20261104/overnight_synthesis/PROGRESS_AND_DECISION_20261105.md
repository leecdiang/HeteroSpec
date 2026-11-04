# HeteroSpec：研究进展、证据边界与下一步决策

状态快照：2026-11-05 01:38（UTC+8）。这是持续更新的交叉审查候选稿，不是“九点前全部完成”的终稿。仅云端源码检查、历史数据分析、CPU验证与CUDA编译；没有新增GPU数值/性能实验，没有使用用户设备，没有合并开放实验，也没有修改已冻结论文或历史数据。

## 一页结论

**最重要的进展是把“为什么不快”和“下一步怎样最便宜地证伪”拆清楚了，而不是已经做出普适加速。**

1. 历史QB确有值得挽救的continuation收益。#151的56个完整请求亏损块全部仍有正非prefill收益；#162的144个QB配对全部有正decode收益，却有93个完整service亏损。模型已驻留、但本次无prefix复用的draft prefill（KV冷）是明确的会计成本来源；这不是模型加载冷启动。但这不是全scope结论：#151 GS的96个配对全部decode净节省为负，其中86个完整service亏损，不能靠“统一优化prefill”解释所有失败。
2. 先检查普通draft ubatch1→2/4，才有理由开发更复杂的双缓存、并发或严格draft内核。若只需要target严格，draft本身无需逐位沿用旧UB1。普通宽draft是必须正面比较的简单竞争者。
3. 普通宽draft仍不能直接启动GPU实验。#183已从纸面设计推进到真实native CPU捕获、独立forced-prefix回放及第三进程自由参考；但仍是微型合成模型，尚未桥接历史R、实际Qwen/Smol、目标GPU及观察开关。当前明确为 **NOT_READY_FOR_GPU**。
4. 性能主线必须面对#180 backend-loop4。#171的packing胜过旧图切片，并不证明胜过一次量化、直接输出的强基线。#180已真实完成固定源快照的143个CUDA单元与llama链接；没有GPU运行，不能宣布数值合格或更快。
5. #181 masked MMA能编译，实际旧DLL的FTZ/FMA/JIT风险已被定位；但masked k8/k16有直接前作，资源占用也不轻，不能先把它定为新颖性核心。#182是永远拒绝执行的诊断工具，不是已完成的低成本安全快路径。
6. AUTO目前不是值得继续堆规则的主攻点。44个题根的探索性LORO中，Qwen/Llama相对最强固定策略仅省1.61%/1.57%，Smol反而慢0.38%；其中Llama会错误启用draft并造成单root约13.1%回退。不存在已经证实的普适路由收益。

**推荐顺序：明确旧参考的实际价值与合同 → 补参考/观察桥接 → 检验普通宽draft → 比较loop4/packed/强DP4A → 仅为有净收益的路径实现低开销资格与状态管理 → 新盲面板确认。** 不应同时把AUTO、MMA、双缓存、事务框架都作为论文主贡献。

## 1. 阅读入口与固定版本

本次直接查询远端，#178–183均为draft、未合并。以下是本报告审查时的head；后续变化须增加新快照，不覆盖历史结论。

| PR | 固定head | 应如何理解 |
|---|---|---|
| [#178](https://github.com/leecdiang/HeteroSpec/pull/178) | `4bbd322de1411be9f7998def4042dafabb4df669` | 路线假说，不是最终实验结论 |
| [#179](https://github.com/leecdiang/HeteroSpec/pull/179) | `b065d5450ce0160caca75e0c18c2af2a4aa28cf7` | 合同原型与后续重算/研究汇总 |
| [#180](https://github.com/leecdiang/HeteroSpec/pull/180) | `7ac1b6bd91a69fe3a27819c81978c4a78fac5cbd` | 强loop4对照与CUDA构建证据 |
| [#181](https://github.com/leecdiang/HeteroSpec/pull/181) | `44625c8d53b8a7cc694d9c25a197858424d63197` | 独立Q8 MMA/DP4A、冻结DLL与FTZ审计 |
| [#182](https://github.com/leecdiang/HeteroSpec/pull/182) | `08c66ac2aee56d937d0f94d07c8bbadc9d47466b` | all-split计划检查，armed时全拒绝 |
| [#183](https://github.com/leecdiang/HeteroSpec/pull/183) | `895c20513bd086d389ea52a60d0cd52a89bec73d` | draft ubatch、回放链、未来GPU协议 |

它们是不同时间点叠加的分支，不是同一最终系统的六个可直接拼装模块。#180基于#179较早快照；#181基于#180较早快照；#182/#183也各有冻结父版本。发布文档head不等于所有源文件都在该head重新构建过。未来集成要重新检查源差、编译、ABI和行为，不能将分支测试数量相加称作整体测试通过。

建议先读[QB重算与范围更正](https://github.com/leecdiang/HeteroSpec/blob/b065d5450ce0160caca75e0c18c2af2a4aa28cf7/docs/research/reference_contract_20261104/rtx_reanalysis/REPORT.md)、[Llama原生phase重算](https://github.com/leecdiang/HeteroSpec/blob/b065d5450ce0160caca75e0c18c2af2a4aa28cf7/docs/research/reference_contract_20261104/llama_reanalysis/REPORT.md)、[路由重算](https://github.com/leecdiang/HeteroSpec/blob/b065d5450ce0160caca75e0c18c2af2a4aa28cf7/docs/research/reference_contract_20261104/routing_reanalysis/REPORT.md)，再读[成本预算](https://github.com/leecdiang/HeteroSpec/blob/b065d5450ce0160caca75e0c18c2af2a4aa28cf7/docs/research/reference_contract_20261104/payoff/REPORT.md)和[最小draft方案](https://github.com/leecdiang/HeteroSpec/blob/b065d5450ce0160caca75e0c18c2af2a4aa28cf7/docs/research/reference_contract_20261104/draft_prefill_study/PLAN.md)。不要只读早期PR正文。

## 2. 旧数据里真正改变路线的信息

### 2.1 不再把所有慢归因为“普适性不足”

#151的QB：Qwen16个、Smol40个亏损块，共56/56非prefill净残差为正；保留实际target prefill差异、理想删除draft prefill后，这56块都能转正。这只是固定其余测量的会计反事实，不是已经实现的缓存收益，也不保证优化draft后proposal轨迹不变。

反例同样重要：GS的86个完整亏损块全部非prefill decode不利；PQ56个亏损块中仍有一个非prefill反例。GS全96配对decode不利，与“86个亏损块不利”不矛盾：分母不同。报告必须明确“QB”，不可再写“全部draft亏损都只在prefill”。

#162提供独立的Llama phase证据，而不只是把#151机制外推过去。QB144配对中93个完整service亏损；所有144个decode净节省为正。长数学draft prefill均值1.898s，非prefill净节省1.133s；长代码对应1.775s、1.000s。数学长短接受率约73.0%与75.6%，没有接受率崩溃。完整服务仍亏，说明“接受率高”不是充分的启动条件。

这两个研究不能拼成一条无差别总均值：#151是resident但每次清KV，#162是fresh context且service含setup/teardown。两者phase计时都是同步host decode elapsed，不是GPU kernel时间。DRAFT_SYNC实际执行seed decode，不能把它当纯等待直接扣掉。

当前单输入只有一个cap/EOG输出长度。`C−M = F + n*b − (L−1)*a + H`是可逐条验证的会计恒等式；用当前平均速率算“break-even输出长度”只是外推。不能为了摊薄成本强迫自然EOG继续，也不能把外推点当合法上下文容量内的预测。

### 2.2 先修成本，不先扩大路由搜索

路由分析包含44个不同题目ID、48个model-root单元、240个QB重复请求配对。它没有把同一题的session分入训练和测试，也没有用最终acceptance/输出长度作特征。root分组不证明统计独立、自然随机抽样或跨数据集语义去重。但仍是看过历史面板后设计的策略族，并非前瞻确认。

尤其，LORO只隔离root、不隔离日期：某较早请求的训练可以用后日其他root的标签。逆向day2→day1仅是稳定性诊断。Qwen当前12个OOF动作恰好等于该面板root oracle，使固定预测bootstrap天然不能产生负收益；这不是未来分类错误被证明为零。

相对同模型最强固定策略，Qwen省1.610%，Llama省1.572%，Smol慢0.383%。Llama条件区间包含零；9个启用draft的root里4个亏。只在当前M/C两个arm上，事后root oracle额外空间约为1.61%/3.17%/0.89%，不是改变draft prefill后的新系统上限。旧Llama“384长度阈值省2.36%”是exposed策略，不能替换成新的泛化结论。

决策：保留该流程为负面/风险基线，停止在同一面板上继续寻找看起来更好的阈值。新路径成本改变后，再判断是否产生足够大的、跨session稳定的互补区间。

### 2.3 B570与RTX的结果都要求强WB基线

[B570独立复算](https://github.com/leecdiang/HeteroSpec/blob/b065d5450ce0160caca75e0c18c2af2a4aa28cf7/docs/research/reference_contract_20261104/b570_reanalysis/REPORT.md)保留了关键反例：#169的129个crossing配对中48个QB调用更少却更慢。#175的4个crossing root的微小优势，移除head205/append84即翻转；cut/rechunk所有32个root调用总数都相同。因此不能用“少调用”给它解释因果。

#174 AUTO实际恒定WB-cut；#175恒定WB-rechunk。名字叫AUTO不代表学到了有效自适应。#177刻意选择8个有schedule差异的新root，rechunk/QB append比0.960486，但完整service比0.994379且两session方向相反；它是条件机制研究，不替代#174的代表性null。

#177以WB-rechunk为起点，同步append仅占平均服务19.62%。即使整个append缩短20%，算术完整服务节省上限也只有3.92%，还未扣新guard；若希望5%净节时并容许1%服务安全成本，需要整个append缩短约30.58%。这不是5%接收门槛，只是防止投入与收益脱节的预算。

## 3. 我们究竟保证哪一种“严格”

应将历史结果与新合同分开命名：

- endpoint相同：完整输出IDs、EOG、长度、stop reason、terminal ID相同。
- matched-prefix完整logits相同：同一个逻辑token前缀上的完整词表F32字节相同，包含实际proposal的off-greedy验证分支。
- committed active KV与位置/前沿相同：所声明活跃状态逐位相同，并保存正确frontier logits和未materialize尾token。
- 可安全恢复：还需捕获足够的隐藏状态、所有权、事件、错误状态和恢复行为。前三级有限比对并不自动给出第四级。

#152“strict_reference_equal”的39/48是endpoint比较；局部PQ/QB有另行更强的向量检查。旧论文中已有明确endpoint定义，不能仅因缩写含strict就判定历史论文造假或错误。正确做法是保留旧定义，并在新主张前明确升级后的证据尚缺什么。#165已经修复的激活精度反例也不能继续当作当前未修复失败。

对于draft，建议先坚持T合同：target行为按声明参考保持，draft可改变。只有证明应用必须保留旧draft logits/proposal路径，才提出更强TD合同。否则人为要求draft逐位不变会排除普通宽ubatch，制造不公平基线。

#183发现了真实的审计盲点：terminal pending=null意为没有下一轮，不保证所有已输出token都在KV里；75个fixture中48个末尾有未materialize输出。trim后默认last logits有36/75不对应保留前缀，必须取正确verification row。CPU桥接已显式记录这些内容，但仍不授权恢复。

## 4. 今晚代码推进到哪里，哪些不能混说

### #179：真实合同/状态原型，但还很昂贵

直接读[NativeCheckpointOwner](https://github.com/leecdiang/HeteroSpec/blob/b065d5450ce0160caca75e0c18c2af2a4aa28cf7/src/reference_batching/native_checkpoint.hpp)可见：append前后同步并序列化完整state，每行请求完整logits，多次复制持有vector的capsule，失败后创建fresh context并readback。它不是常数级guard，也不是GPU零拷贝缓存。捕获模式还改变fusion/graph reuse路径，不能把instrumented成功当未观察路径资格。

CUDA enforcing目前拒绝整个split，没有合格allow路径。[runtime资格研究](https://github.com/leecdiang/HeteroSpec/blob/b065d5450ce0160caca75e0c18c2af2a4aa28cf7/docs/research/reference_contract_20261104/runtime_qualification/RUNTIME_QUALIFICATION_AND_COMMITTED_STATE_20261104.md)提出的逐层KV提交、zero-tail、reader lease等仍有明确假设；Python有限模型检查不是原生CUDA事务证明。

### #180：强基线已经编译，快不快还不知道

[loop4实现](https://github.com/leecdiang/HeteroSpec/blob/7ac1b6bd91a69fe3a27819c81978c4a78fac5cbd/docs/research/backend_loop4/README.md)在backend内一次量化、按原≤4列specialization循环并直接写最终输出。必须验证宽量化与分块量化是否相同，不能只看MMVQ helper名。

[真实完整CUDA/llama构建记录](https://github.com/leecdiang/HeteroSpec/blob/7ac1b6bd91a69fe3a27819c81978c4a78fac5cbd/docs/research/cuda_compile_20261104/README.md)针对#180源快照`40934bf0f6dd5ab41e42e0f682f42aef0514e760`，143个CUDA单元、sm89/sm120a各143 cubin，约66.47分钟；工具链CUDA13.2.2/NVCC13.2.86。#179源`8005cf01...`仅修改的两个CUDA单元编译通过，完整链接未做。没有任何GPU执行。

#171 q32 Q投影旧图23kernel→packed2kernel，干净墙钟172.4→150.2μs；V却67.1→67.5μs。loop4预期9kernel是源码推断，尚未profile。packing相对loop4不能再领取“去掉重复量化和concat”的全部旧收益。

### #181：编译了候选，也发现了参考数学的真实风险

[masked MMA实验](https://github.com/leecdiang/HeteroSpec/blob/44625c8d53b8a7cc694d9c25a197858424d63197/experiments/masked_q8_mma/README.md)目前只覆盖预量化Q8、窄shape、有限half scale；不含F32量化器及完整模型。24个kernel/architecture组合编译成功，并成功链接测试程序，GPU测试无设备退出77，不能写成通过GPU测试。

原冻结Windows DLL只有sm86/sm89原生cubin，无sm120；实际Blackwell部署需要JIT，而最终JIT SASS未被观测。原PTX存在FTZ乘法/FMA/reduction，不能拿新Linux源码默认数学假设替代旧binary。

FTZ差异不自动证明候选错：在有限half scale、整数dot、零起始累加、无bias等限定条件下，中间值落在2^-48格点，不产生非零FP32 subnormal；这不单独证明signed-zero语义也完全相等。FMA则存在可达signed-byte反例，K1056可相差1 ULP。`fused=true`必要而不充分；还缺量化、完整数据流、JIT和实际GPU验证。有限F32输入也可量化出half Inf，不能只检查输入finite。

MMA寄存器压力架构相关，sm89为168而sm120a为108；DP4A布局也各有代价。零spill不是更快证明。下一步必须与同布局DP4A、logical-W4及宽DP4A、loop4/packed公平比较，不能只挑弱DP控制。

### #182：有效的诊断基础，不是性能成果

[计划检查器](https://github.com/leecdiang/HeteroSpec/blob/08c66ac2aee56d937d0f94d07c8bbadc9d47466b/experiments/scheduler_plan_probe/README.md)在真实CPU多split/transfer上验证了stale-plan等拒绝，三个ggml CPU库及harness的ASan/UBSan已运行（CUDA关闭），不涵盖全部llama/model代码。但armed时所有请求都veto，根本不存在allow分支；hook前llama memory_update/mctx.apply可能已改变状态。其保证是没有新的split copy/compute，不是完整请求无副作用/原子性。LSan曾尝试但因ptrace限制失败，随后关闭LSan的ASan/UBSan重跑通过，不应概称所有sanitizer通过。

### #183：已打通真实CPU证据链，但尚无真实模型资格

[原生桥接](https://github.com/leecdiang/HeteroSpec/blob/895c20513bd086d389ea52a60d0cd52a89bec73d/experiments/draft_ubatch_probe/native_replay_bridge/README.md)以两个未训练tiny dense-Llama模型、seq0/F16 KV、独立进程对齐candidate、forced prefix和free R。独立审查18个case/54进程、178个完整向量使用与58个commit状态匹配；还另开34个前缀进程检查reference共享路径。它们是有限CPU诊断，不是18个真实任务性能实验。

新bridge target为ubatch1/output4、fresh context，同模型充当draft，vocab NONE无真实tokenizer/EOG。历史#151旧R是target ubatch1/output1、whole-prompt last-only、resident-reset/cap128；历史C的scoped target则是ubatch4/output4。不能混淆二者，也不能认为新bridge的caller/pool/output reserve自动兼容它们。Windows worker仍未编译。完整native capture归档仅在本地验证，未上传；仓库提供源、摘要、hash与重新生成方法，不能仅凭链接声称全部原始native bytes已交付。

[未来设备协议](https://github.com/leecdiang/HeteroSpec/blob/895c20513bd086d389ea52a60d0cd52a89bec73d/experiments/draft_ubatch_probe/rtx_gpu_protocol/PROTOCOL.md)明确NOT_READY_FOR_GPU，先G0身份/预算、G1旧R/native/观察/状态/资源桥接。旧binary固定cap128与output reserve1，不能暗中改cap8或换fresh R后沿用旧名字。重审计与干净timing必须分开，后者只有观察桥接合格才有意义。

## 5. 与已有工作的关系：可借鉴，不能冒领

- [Taming Bitwise Behavior](https://arxiv.org/html/2609.11356v1)已有reduction描述、编译后等价检查与布局优化，Appendix E明确讨论masked k8/k16。masking思想有前作；其浮点MMA/FP32累加实例并不直接等于我们的signed-byte leaf/W4/Q8实现。具体量化叶顺序和部署兼容的区别仍需逐项证明，不能宣称发明masking，也不能把读PTX/SASS摘录称为完整形式验证。
- [llama_reproducible固定patch](https://github.com/amiller/llama_reproducible/blob/f0dafdbd9dba40bd0e596f74f3da5f592900fca4/patches/0001-all-deterministic-parity.patch)已有四列backend loop。这正是强baseline来源；其整套模式还改其他数学，不能整包导入后仍说保持原R。
- [Vosti](https://arxiv.org/html/2609.38981v1)已有系统级确定性、KV前缀不变量和关系式kernel合同。通用“状态合同+调度检查”本身不足以作为新颖性。
- [draft-reuse专题调研](https://github.com/leecdiang/HeteroSpec/blob/b065d5450ce0160caca75e0c18c2af2a4aa28cf7/docs/research/reference_contract_20261104/draft_reuse_research/RESEARCH.md)覆盖持久化双KV、overlap、history-free/目标特征draft等。它们应成为分类明确的竞争者；不是所有论文都可直接替换现有Qwen/Smol草稿，也不能说双缓存或重叠首次提出。

更值得验证的潜在差异是：**在不可任意重定义的既有量化部署参考上，找出可执行、可拒绝、成本合算的并行域，并把kernel等价约束与真实提交状态衔接起来。** 这仍是研究假说。需要真实旧artifact兼容/回放/回归价值，而不是为了制造问题凭空添加更强合同。

## 6. 依赖排序的技术决策树

### 门0：论文到底解决谁的问题？现在可在云端完成

交付一页合同与用户价值：旧R为何不可换、必须观察哪些logits/状态、可容忍哪些draft变化、谁会使用兼容性。拆分T与TD；冻结最强合法baseline候选和主成本口径。

若找不到需要旧数值参考的应用，不继续以“旧R严格兼容”为中心构造大系统。可另立新参考/新数值合同的研究假说，重新检验近邻差异与强基线，保留已有工具和负结果，但不能继承旧R资格或速度。若只需target严格，优先普通宽draft，不开发TD专用内核。

### 门1：把参考桥接做到能否决实验，而不是先跑大面板

先离线补全真实source/runtime/模型/设备身份、caller/mask/lifecycle、输出cap与历史状态复建。CPU可审查解析器、失败注入与预算，但不能替代设备桥接。实际GPU需要另有合适且已授权的执行环境，本报告不触发用户机器或租赁。

进入设备阶段后，先一模型族、两个短输入、小cap的机制诊断；旧cap128桥接及priming额外成本必须单独登记。任一完整所需向量/active KV/frontier差异即停止该合同的性能主张；不降成只比较endpoint继续报同名成功。free R必须独立于candidate答案；forced参考必须覆盖实际proposal前缀，包括首次拒绝后行。

### 门2A：用最便宜的改动检查draft启动

比较同lifecycle的B_default、B_QB、旧draftUB1和普通UB2/4，保持target、k、输出保留与缓存策略不变。先资格后timing，不同时叠cache/overlap/early-EOG优化。1/2/4只是可行性入口，不保证已找到最强普通宽draft。

若普通宽draft已解决问题，优先采用简单路径；论文是否仍有独立技术贡献另判。若候选加上剩余全部draft prefill都省不出有意义的净收益，停止定制prefill。只有留下足够成本空间，再分别测target冷/draft冷、target热/draft冷、target冷/draft热、双热，并公平给target-only缓存及总显存资格。

固定其余测量、且无新增开销的会计反事实下，Smol历史模型已驻留、KV冷的请求要删约70%的draft prefill才能总体打平，3%工程节时需约77%；target热/draft冷时成本更差。不能拿理想冷overlap替代真实热target分布。双KV内存、catch-up、eviction、恢复临时副本均须计费。

### 门2B：并行域内核只做有决策价值的比较

先同源R、图切片、backend-loop4、packed；资格合格才计时。覆盖Q/K/V/output/FFN及q1/3/4/5/8/16/32和尾部，记录fallback而非丢弃。干净墙钟与profile分跑，实际量化/MMVQ/concat数和资源/流量证据支撑机制。

若packed只胜图切片不胜loop4，停止把现packing作为主要新性能贡献。MMA仅在预量化资格和预算成立后加入，必须打败强DP4A族；不靠缩窄输入到最有利Q投影救结论。#171 k3 verify只有4行、packing门槛≥8，旧收益主要在prefill，不能包装为verify加速。

### 门3：只为幸存路径实现低成本安全机制

当前完整state owner可做昂贵正确性对照。新路径必须说明哪些资格在冷路径、哪些动态事实每请求绑定，何时失效，读者lease何时释放，错误是否可恢复。先实现一个明确allow域，保留保守拒绝；不从#182全拒绝直接推出低开销。

成本账：`净节省 = 可触达临界路径缩短 − 热路径安全成本 − 冷资格成本/实际复用次数 − 失败概率×恢复成本`。逐项测，不把未来oracle/cache命中免费化。若不为正，无有限的“多跑几次就回本”。改变输出行数、关闭baseline合法graph reuse或给候选独占缓存都不算公平收益。

### 门4：新盲数据与论文决定

只给幸存机制注册新root-disjoint面板。先固定规则、主要对比、预算与停止条件；用calibration方差决定样本量，不用“24题”假装功效足够。session、cap变体和同会话turn是相关重复，按root/trace聚类。保留失败、fallback、首填、尾部回退、峰值显存与完整服务，而非只报GPU核。

若只有窄模型/宽度通过，论文明确缩小范围；若强WB获得同样收益但QB无额外收益，转为共享底层执行机制，不再主张AUTO/QB优势。若全成本没有胜最强同合同baseline，交付诚实负结果，不继续堆模块掩盖。

## 7. 为什么现在不能说“TPDS中稿概率已超过50%”

当前没有一个可校准到这篇稿件的概率模型，也没有完整新稿、真实新GPU结果和审稿人评议。数字50%不会因为更多PR、更多CPU断言或更长调研自动成立。反过来，也不能凭历史null直接断言没有投稿价值。

最实在的风险仍是四个：
1. 与Taming/Vosti/llama_reproducible的区别可能不足；
2. 最强loop4/宽draft基线尚未实际比完；
3. 原生CUDA参考与低开销状态allow路径尚未闭合；
4. 当前自然服务收益小且不稳定，有限面板不足以支持普适性。

改善投稿质量的可检验里程碑应是：一个明确未被近邻解决的问题；一个能被反例击败的主张；实际合格且胜强基线的机制；包含零收益与失败域的完整系统评价；可重现artifact。达成后再找领域研究者审读完整稿件、评估TPDS定位。若最后仅剩窄内核编译/数值贡献，应重评论文结构与合适渠道，而不是靠增加系统名词硬凑TPDS。

## 8. 已发现的过时表述与下一次更新规则

首次审查发现PR179/180正文的CUDA未编译说明、PR183正文的能力摘要落后于新增证据。三条PR正文已于2026-11-04 17:33 UTC作最小更新并读回，head未改变；旧receipt继续保留为历史记录。CUDA构建仍只覆盖已注明源快照，不能扩大为最新所有代码或GPU执行通过。

rtx_mechanism报告第5节/结尾仍说#162 phase待取得；现在llama_reanalysis已独立完成，前者只应作为当时分析范围，不可继续当当前阻塞。所谓“672记录、24输入”是24个model-input，Qwen/Smol共享4个题，题ID并集20；和路由44root总数不冲突。应避免将模型面板数写成独立原题数。

合成fixture的75case、独立bridge的18case、几千geometry断言、历史几百重复测量、143 CUDA编译单元是五种不同证据；任何总报告不得把它们相加称为实验规模。仓库当前为私有，不把内部PR/结果叫作公开可下载证据。

下一次更新应记录新的head、真正执行的步骤、失败与未做项，并逐条检查它们改变了上述哪个门的结论。尚无新GPU结果时，保持“研究推进与可执行计划”，不升级成“路线已验证”或“接收率提升”。
