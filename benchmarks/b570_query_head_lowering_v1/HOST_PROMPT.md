# B570 agent work order: independent query/head-lowering study

你推进的是一项新候选方法，不是恢复旧 NO-GO。目标始终是**有实质用处的创新与可迁移性**，不是把 QB 修到四题都过。只在本 PR 的新目录工作；PR109/111、RTX104/110、论文、arXiv、旧F0/模型/数值DLL/账本和自动化不改、不合并、不续跑。

## 立即开展：S0，CPU-only，最多一个工作日

1. 阅读 README、PROTOCOL、DESIGN、SOURCE_LOCK。先核验固定 PR111/109 资产及原始参考。基线q2 QB被拒绝是版本化后端能力事实，不是已经观测的CPU fallback或数值根因。
2. 运行当前 Python40项测试和C++48个descriptor-mock cases。它们是小型模型/描述符测试，不是实际GGML/GPU通过。不得把mock头文件带入真实构建；真正include指向恢复的冻结ggml.h。
3. 用提供的 `native/query_head.h` 接入独立真实GGML CPU harness。六表示 MQ/PQ/QB4/QH_C/QH_D/REPEAT4；q1必须真正调用原始链。QH r=hq+j，GQA floor(r/(qg))，mask r%q，最后恢复query/head顺序。Q不连续时显式cont；dense-mask和repeated-KV必须真实执行并计费。
4. 复用PR111独立地址/FP64 oracle，不把新候选本身当reference。检查真实buffer bounds、存储转换、stage与最终全向量；严格exact结构化控制，普通差异保留，没有事后容差。不能仅凭maxerror很小宣称原部署参考逐位相同。
5. 按plan.py的432fixture/2592图计算预算分开发与锁定后验证。现有本地toy测试已覆盖q3/4，诚实称“锁定后fixture输出验证”，不是从未考虑过的几何或未见自然任务。报告所有构建失败/第一次验证结果；最多两轮有明确范围的移植修订，不能无边界重写shader或搜特殊输入。
6. 检查actual完整后端supports_op及softmax mask条件需要哪些设备信息。S0只做源码/CPU，不初始化GPU。如果需要运行设备支持census，准备S1准确F0后请作者确认，不能偷偷当免费probe。
7. 接入真正序列化请求、executor、owned-PID监测与watchdog、独立raw解析和恢复。ledger.py只是append-only helper；evidence.py只是规范化记录算术，**不是这些接口已经完成**。不要重写所有旧工具，重用可靠的有限部件。
8. S0结果同时回答：是否只修了一个维度错误？是否有一类可复用表示条件？相比强PQ/物化广播多了哪些代价？没有潜在实际收益就NO-GO，不为章节数量继续。

## 准备并申请 S1，不自行启动

单独prospective F0绑定新代码、输入、原算术DLL、driver、真实命令/wire、计量与raw审计。预算161 operator-host attempts =1 capability-only +最多160数值图；3600owned秒、2GiB。无model requests、额外probe/warmup/retry。

capability-only census枚举全部可执行节点及全部预定16输入×5表示。必要条件≠完整supports_op；元数据view≠执行节点。按冻结规则先QH_C、否则QH_D、否则STOP；不能看输出/速度选择。保存census并绑定选择后再开始数值；实际placement也要观测，不能把fallback计算冒称全Vulkan。所有unsupported、失败、未启动坐标都保留。

若S1发现有效PQ/QH数值差异，保留它：这限制bitwise结论，但不自动否定full-decoder端点。q1共同路径不一致、语义/非有限/placement条件失败则停止。S1不输出端到端speedup。

## S2/S3 分别经过准确F0确认

S2是64次自然请求小试，R8→R_SHADOW8→六candidate counts24→diagnostic24；原始R不能被新shadow代替。所有candidate从prompt自然形成状态，保持k1、独立target/draft schedule、pending/bonus/reconciliation、phase/cache身份。

监测先验证实际角色合同：旧R检查点不是100ms周期。nominal period与actual gap分开，不宣称连续驻留。第一个R返回就审查，进入candidate前再次gate；hash正确不能掩盖语义错配。

只有真实参考/观察控制、C_R_PQ和C_R_QH完整四题资格、actual supported backend及绑定VERIFY的multirow证据齐全，才申请S3。其余有效candidate不一致是科学反例，不重试到通过。不能通过更换题目/模型/精度/掩码修门槛。

S3按固定24未见自然文本×7臂×3session，两日期块；504formal+504warmups，504processes，21600owned秒，6GiB。选择前完整review历史暴露，禁止根据答案/输出/速度选题；不足格就准备阶段停止。所有主/辅助比较、六分层、回退及完整总体成本都报告，不只报告成功子集。

## 输出与关闭

对话中直接给结构化结论；必要文件保留：RESULT.md、真实source/runtime/F0与plan、raw manifest、支持/实际placement记录、阶段数值或endpoint矩阵、完整成本/回退、恢复回执、剩余未知与GO/STOP。

主判据：是否扩大可用条件且胜过强PQ/保守reference？仅证明代数正确/一项supports条件通过不够。数据源必须真实，hardware handoff中没有的DRAM/cache/XMX/timestamps/DAG/residency保持null。不给新硬件写面积功耗或免费共享假设，不与另一个硬件工作流重复造模拟器。

新探索不阻塞本次arXiv。旧失败原封不动；没有明确增量就在一天CPU原型或有限gate处收尾。不要为了“创新”无限细化到某个特殊token。
