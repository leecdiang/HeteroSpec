# 固定实验方案与止损规则

## 1. 主问题与三条竞争解释

H1：只控制 continuation attention 不够；改变 prefill 状态形成方式后可恢复参考资格。
H2：局部 QB 不同于全局 microbatch=1；实际多 query micrograph 能保留物理摊销，但 draft/状态维护可吃掉收益。
H3：已暴露任务上的效果不能代表适用性；冻结后的方案应接受不同内容、长度的验证。

这些是假设，不是当前结果。主要终点是完整原生 token/EOG/length/stop/cap128 与**历史 R_stock**一致；答案正确率不属于本研究。主比较必须同模型/tokenizer/精度/采样/输入/输出窗口，不与别的系统论文速度直接排名。

## 2. 固定参考：绝不利用新结果选择参考

原机从 PR92 `82946adf...` 的完整归档恢复 R_stock 的**真实 binary、recipe、输入包装和模型身份**，作为 R。读取原始 F0/命令，而不是凭记忆把 R 简化成 UB128。若真实身份无法恢复，S0 STOP，不改以 PR101 A 或较容易匹配的端点为参考。

新 build 的 R_PORT 必须执行完全相同逻辑 recipe，S1 中与原始 R 比较；四个固定任务各两个新进程重复。历史端点仅用于外部绑定，不算本次启动数。桥接失败是实现/身份阻塞，不是候选方案的科学反例。

P128 指新 matched 容量下按 128 一段的 caller schedule，P512 指尽量一段（本轮 N<=512）。**P128 只叫“参考相近的形成策略”，未验证前不能叫 reference-exact state。** 两者配置共同的 UB512、容量4、非 flash、prefill MQ，最后绝对位置才索要 logits；不能将容量/phase QB 同时变动伪装成纯 producer 对照。实际初始 KV/logits 相等与否另行观察，不能由参数推出。

## 3. 十臂自然执行，不用 donor registry

| arm | producer | continuation | draft | 用途 |
|---|---|---|---|---|
| R | 归档中的 R_stock | 归档中的 reference | 无 | 固定资格/成本基准 |
| M128 | P128 | ordinary q1，容量4 | 无 | 同状态策略 target-only 对照 |
| M512 | P512 | ordinary q1，容量4 | 无 | 分段本身与容量影响 |
| C128_MQ / C512_MQ | P128 / P512 | 未局部修复的 MQ | 固定 k3 | 只有状态策略是否足够 |
| C128_PQ / C512_PQ | P128 / P512 | 显式逐 query attention | 固定 k3 | 最近局部实现对照 |
| C128_QB / C512_QB | P128 / P512 | query-to-batch attention | 固定 k3 | 新组合候选 |
| C128_SERIAL | P128 | 完整 target continuation microbatch1，容量仍4 | 固定 k3 | 同 producer、同 draft 的全局串行控制 |

除 SERIAL 的 continuation UB1 外，所有 C 臂 continuation UB4；最大 caller q4、输出预留4；实际 q1..4 由正常 proposal/EOG/cap 决定。draft 使用 PR92 已有兼容 Q4_K_M 文件和固定 producer/consumer recipe，不与 target 分段联动。不用答案、teacher forcing、固定后缀或 golden proposal 替代真实 draft。

M 的 q1 时 MQ/PQ/QB 应走共同路径，不重复贴三个标签冒充三项方法。这里是**consumer-only PQ/QB**加独立 producer 因子，不等于 CUDA mask3 的原版完整方案；不宣称直接复现“B570 原 QB”，因为历史 B570 只有全局 UB1 repair。

新增 C128_SERIAL 不改变 draft 或 caller，只有实际 target continuation U1，与局部 PQ/U4 区分。它不叫 CoRun 或 LLM-42 复现。

对照职责：C同producer的PQ/QB量化表示增量；P128/P512同consumer检验状态形成影响；M128/C128_QB与M512/C512_QB检验完整draft经济性；R/C检验总价值。某一项合格不能替代另一项。

## 4. S0：只补最短必要接入

使用独立源码树。恢复 PR92 的自然 speculative actor/acceptance/rollback 与已验证内存/计数设施；参考 PR101 的完整 caller schedule 实现；参考 PR98 的 PQ/QB graph 语义。PR101 专用 worker 在 `partition98` guard 禁止 draft、非 ordinary，不能直接修改几个请求键就把它当本研究完整执行器。

保持既有四个 GGML backend DLL 与 shader arithmetic 不变（实际来源/ABI须核对）。新 actor 与 graph 构造所在 llama library 若重编译，明确报告新 hash、source diff、compiler、graph/source lineage；**不要声称整个 numerical runtime 字节未变**。变化只允许 producer/consumer绑定、图表示、对应重用身份与记录，不改变权重、精度、采样算法或 backend 算术。

S0 最多一个工作日；最多两轮有明确根因的接入修订；如果需要重写 Vulkan shader、另换模型/后端或追逐许多特殊图路径，记录 STOP_SCOPE_EXPANSION，提交总结等待新的研究决定。不是“修到有正结果”。CPU代码修复可以正常开发；开始过的native条件不覆盖重跑。

S0 先选定完整输入池与24 holdout，outcome尚不可见。准备 F0 与所有将发送的请求（含warmup）。PLAN→recipe→实际序列化请求必须三方一致，测试合法hash但错cell也被拒绝。默认生产不允许restore，任何 donor、initial-logit外部注入或pending重构键均拒绝。

## 5. S1：小额可行性闸门

### 算子 smoke：48 次独立 operator starts

q=1,2,3,4 × key extent=128,384，共8合法形状。每形状 MQ/PQ/QB各两次，固定operand seed，真实GQA/head/dtype从已锁模型元数据获取；同一组固定FP32 Q/mask与F16 K/V，由所有labels消费。mask是同一query位置的causal mask；数据可用小幅非整数随机值，先冻结完整bytes。禁止视结果改seed或误差阈值。

CPU FP64逻辑oracle只用于本次冻结的小幅有界合成数据（元素绝对值<=0.25，至少包含正负抵消与因果mask）；数学索引检查阈值预设绝对1e-4＋相对1e-4，分别报告每阶段；它不是GPU逐位真值。比较实际QK/softmax/AV完整输出、within-arm重复、q1共同路径及PQ/QB逐位关系。数学/shape/NaN/重复异常是实现闸门；q1共同路径应逐位相同。q>1若PQ/QB不逐位相同，保留结果，记录NO_BITWISE_TRANSFER，不能继承CUDA的逐位机制结论，但数学/接口条件合格时仍可进入原定S2检验完整端点；tensor不等不自动等于token失败。不为某个seed微调。此smoke不是天然model context replay，不能冒称原模型机制证据。

只统计真实 graph dispatch 能力，不把 ne4>1 当 GPU 并行保证。没有对应backend支持或metadata容量，S1停，不通过隐形copy成q次图后仍称QB。

### 原参考桥接：16 次模型请求

固定四个已暴露task：GSM8K/test/{1248,831,1011,1249}，原生 R 与 R_PORT，各两次fresh过程、无warmup。source/runtime/模型/driver错、原reference不稳定或port端点不同均停。真实输入来自PR101/103且与R_stock tokenizer绑定核对，不能假设同名ID一定同prompt。

## 6. S2：四任务全矩阵，共120模型请求

四task×十arm×（counts两次＋heavy一次），各fresh进程，无warmup。S2 latency仅pilot，不并入最终性能估计。每个任务和观测重复的recipe、输入、cap固定；排序由plan确定。

所有候选正常完成但与R端点不同，是SCIENTIFIC_NONQUALIFIED，不是基础设施失败；它是本研究要观察的结果，继续完成预定S2矩阵。错输入、错route、内存越界、缺失完成、错误rollback或参考失败是EXECUTION_ERROR，立即停止，不送后续native请求。

heavy只采固定阶段/事务摘要、初始KV/logits和有限tensor provenance，不逐token保存全KV。producer必须从原始prompt**自然算起**，不恢复PR103 donor。各consumer在同producer下的初始数据和预期关闭的prefill layout应匹配；不匹配先审查factor污染。

S2结束才作Go/No-Go：
- C128_QB必须在全部四task两个counts重复上与R完整一致，且heavy端点一致。
- 在真实speculative C128_QB中至少观测到q>1的occupied target micrograph，且QK/softmax/AV图使用预定QB路径；否则输出NO_PHYSICAL_AMORTIZATION，并停止S3，而非降为q1后宣称成功。
- 不以pilot速度正负决定是否放行；有效但慢也允许固定S3产生负结果。
- 若C128_QB没有合格覆盖，不更换C512_QB当新“主方法”；本轮主候选不成立，停止扩展，并保留完整S2和全部其他arm结果。

这条闸门是节省资源的预注册阶段选择，不构成对H1的证实。C512_QB本来也通过时，仍可验证成本/普适性，但不能宣称C128扩大资格范围。

## 7. S3：真正的新输入验证，不再钻四个旧题

从锁定语料、相同prompt formatter/tokenizer中按ID/hash排序选取24个任务：MBPP/GSM8K各12个；每domain的合格未见池按原生token长度排序成三个等人数rank层，每层按固定hash选4个；长度同分用预定hash破同分。最终报告实际min/median/max及跨128比例，不能把rank层说成固定绝对长度区间。排除所有可恢复历史实验的task ID和完整prompt token hash，并记录exposure检查覆盖边界。这个“未见”指本项目未跑过，不是模型训练未见或数学总体随机样本。

不能带答案/单元测试进入推理输入。任一domain不足12个未见输入时，在任何新结果前报告并作前瞻修订；不能拼接、padding无意义token或选到出现分歧才收手。固定24个输入的所有十arm都运行，不按是否通过挑选报告。

三session；每session同24个task×十arm。每个测量都fresh worker：先一次同arm固定已暴露校准prompt warmup，reset target/draft/KV/sampler/counters，再一次正式请求。共720测量＋720明示warmup＝1440；720进程。sessions至少在前一个完成后相隔15分钟，主机空闲、电源/温度/driver/loaded module准入；不宣称三独立日期。

S3前将简单策略固定为“注册静态域内选择C128_QB，域外从请求开始选择R”。与always C512_QB（只靠静态合法）、always R及所有实际arm比较。不能看heldout输出选择每个task最快的合格arm，不能按taskID白名单决定；不做在线风险分类器。

请求开始前可拒绝/选择R，但开始执行后不能换回R kernel就假装状态被修好。本轮不实现中途恢复。领域外输入测试应在CPU验证路由拒绝即可，不追加未计费native probes。

## 8. 资格、性能、架构的报告分别写

完整输出资格：每task各session reference必须稳定；任一candidate与R不等则该arm全panel qualified ratio为null，不能只从成功任务求快。每个候选nonqualification仍逐task公开。对PQ/QB、同producer M/C额外要求两边各自符合R。

主成本：包括自然prefill、draft、verification、正常sync、acceptance/reconcile和策略选择的完整request wall；模型加载单列，720warmup时间从效果估计排除但计入资源预算。每session先算24任务参考总时间/候选总时间，再报告三个session与其等权log均值；另报任务中位数/回归、各domain/长度cell和尾部延迟。三session不够强时间泛化，不强行输出置信区间；禁止边跑边按显著性加样。

实际策略必须把选择器计时算进请求；study.py的arm成本可作策略基线，但它本身没有实现测量真实策略开销。不得把replay、heavy时间或CPU enqueue分项当作paid GPU kernel时间。

广泛实用性判据事前固定：若新组合只在少数旧题成功，而新的长短输入大批拒绝/不合格，或整体成本并无优势，不开发更细的逐题选择器挽救；报告本轮范围内缺乏系统价值。2%可作为实际改进参考线而非显著性检验：没有额外hardware结论，也不能用它覆盖输出失败。

## 9. 保留负结果且控制项目深度

- 无合法Vulkan QB：停止移植，不重写shader或扩新精度；输出可移植障碍与已测证据。
- 全部q>1最终串行：停止性能扩展；输出逻辑并行不等于物理摊销的架构限制。
- 参考状态策略仍不能保证续写：保留边界；不自动开启单层projection注入/全量logit搜索。
- 仅旧题有效：停止“更小子集”方向，不能把特化白名单变成普适贡献。
- 全部正确但慢：诚实报告成本边界，不追加更大k或更容易draft直到正收益。

一期只允许一个model pair、一个backend、q<=4、两种producer分段、三种局部consumer表示及一个全局串行控制、24新prompt。没有V head搜索、阈值调参、FPGA实现、通用调度器或外部系统完整复现。另一体系架构对话可读取本研究的中性trace，但不得改变本轮登记。物理micrograph同时处理多行是有摊销机会的必要观测，不是充分证明XMX并行度、共享缓存命中或DRAM减少；QB的attention query列为1、query-batch为q也不能误记为整个target被串行。

总上限核对：bridge16＋pilot120＋validation1440＝1576模型请求；独立算子48；native进程16＋120＋720＋48＝904；owned时间21600秒；新运行输出8GiB。耗尽任一上限停止，不因先前阶段省下请求而自动扩展后一阶段。warmup进程内仅有一次正式请求，统计以task/session报告，不将720进程当720独立输入。

源级k3控制需补：接受0/1/2/3个proposal、全接受bonus、首错correction、draft catchup、target/draft trim、pending只消费一次、早停与cap边界。现有worker只准k1，计数器也有w1/w2硬编码，必须全链路修改并测试。

脚本只给schema及CPU控制，不是native执行CLI；原机须实现具有真实字段来源的frontend和controller。记录`raw_request_path/raw_result_path/raw_timer_path/raw_identity_path`并逐字节校验，而不只是提供若干能通过hash的无关文件。读取时使用绝对run根和相对raw路径，禁止路径逃逸。
