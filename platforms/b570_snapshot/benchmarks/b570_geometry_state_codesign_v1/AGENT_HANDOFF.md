# 发给 B570 agent 的执行任务

你负责本独立研究：`benchmarks/b570_geometry_state_codesign_v1/`。

## 目标

检验自然请求中“参考分段状态形成＋局部QB消费”能否保留原stock参考，并比全局保守路径保留更多物理批处理和请求收益。不要继续head/layer/token掩码搜索；不要做projection injection、teacher forcing、旧donor state restore。更不要为了搭体系架构而声称未测的cache/XMX/DRAM/PPA。

先读README、PROTOCOL、NATIVE_INTEGRATION、ARCHITECTURE及SOURCE_LOCK。核对远端原始来源。本包是设计与CPU工具，不是已能直接调用的native执行器。

## Git操作与分支

如外层包尚未发布，可在已登录GitHub CLI的机器执行外层 `python publish_pr.py` 离线预览，核对后执行 `python publish_pr.py --execute` 创建新独立Draft PR。只有真实返回URL和head SHA后才报告已创建。不要假设PR号107或覆盖同名分支。

新PR基于固定main，只新增本benchmark目录。PR104 RTX和PR105前沿预算完全不动；不要merge、重启其任务、执行其旧slots或恢复Zenodo/arXiv。

## P0：现在可做，零native

1. 恢复PR92/97的原始stock reference、generic speculative事务和PR101的自然prefill分段来源，准确pin所有源码、模型、runtime和driver。
2. 运行CPU toolkit tests，核对它们只是synthetic/schema测试，不代表native通过。
3. 在隔离源码/新native目录中最小实现producer recipe及MQ/PQ/QB consumer。先做QB非Flash、q1/2、单stream、原Llama图；其他能力不需要加。
4. PR101 target-only guard绝不能原地删掉；全局schedule不能跨target/draft复用。参考影子、capacity4匹配、phase/graph reuse、真实all-output位置、pending与rollback都要测试。
5. 做真实serializer准入测试：对全部九臂及80 pilot slots检查arm→wire→binary/phase/caller/actual geometry，发送同一已验证对象，禁止第二lookup。
6. 实现真正executor、before-start账本、raw输出/状态、超时/内存/磁盘gate、owned PID清理、独立raw normalizer与CPU分析桥。`analysis.py`已有R对各臂和10项paired contrasts；需要接入真正的raw evidence桥，而不是重写统计指标或把非法输出变成收益。
7. 最多两轮有明确范围的移植/集成修订后汇报可行性。若需要改shader算术/精度/模型/强行恢复状态，停止并报告NO-GO，不扩大设计。
8. 生成执行版F0，提交完整代码/plan/wire/source/budget和真实holdout暴露范围，远端逐字节回读。不要把CPU候选当执行授权。

## P1：原机80starts小试

收到作者对执行F0/本阶段预算的确认后执行，不额外probe/warmup/smoke。

必须先：8个原R counts →4个R_SHADOW counts＋4个R_SHADOW diagnostic →其余预定候选counts/diagnostic。整个80starts上限包含原机启动失败；实际forward计数另记，不用request冒充forward。

预算7200 cumulative owned-process seconds、4GiB新增output。记录所有已开始/未开始slot；科学失败不自动retry。错误身份/请求/参考/观察/计量安全条件触发停止；有效候选与参考不一致是正常反例，不删、不报speedup。

结束后严格用预定pilot gate：R与controls合格；C_R_QB和C_R_PQ四sentinel完整reference合格；QB存在实际multirow verification witness。没有就停止大面板；不要调k、换题或搜mask救结果。

## P2：另行作者GO，不自动启动

满足pilot gate后，提交24个未见prompt候选面板和独立执行F0，申请1728starts（864正式＋864暖机）、864processes、四时间块/两日期、43200s、8GiB。

输入2任务域×3token长度格×4个，固定hash选择，完整排除历史ID和prompt hash。不填充/截断凑长度，不参考答案/latency/新输出挑题。所有9臂照计划跑；所有失败、拒绝、unknown、任务回退保留。

冻结producer_guarded、shape_only和always_reference决策，不用validation输出反选recipe。正式timer包含从resident reset至自然prefill/verify/reconciliation/结束同步的全部请求成本；模型load与校准成本分开报告。无ref资格不汇总speedup。

## 结果输出

在对话里直接给结构化完整结论，文件只保留必要证据：

- RESULT.md：阶段、实际process/request/forward数、输出资格、multirow是否存在、scope、失败和GO/NO-GO。
- 真实raw manifest、原始REQUEST/RESULT/identity/lifecycle与独立恢复回执。
- GEOMETRY_WORK_SUMMARY：分层graph/rows/dispatch和UNKNOWN；不猜硬件计数。
- ANALYSIS.json/csv：四session、两域/三长度、全部比较、全部回退，缺失和不合格不藏。
- state-compatible形成＋QB相对原QB/PQ/R究竟增加了什么？未见输入支持了多少？端到端收益是否仍存在？

不得写“QB已经跨Vulkan普适”“state相同必然证明后续所有token相同”“graph就是kernel”“已测硬件PPA”“一定提高录用率”。若结果表明收益很窄，结束支线而不是继续缩小问题范围。

## 和架构研究并行的特别约束

不要开发另一个Tensor Core模拟器，不改FP数值语义，也不在此PR写RTL；只在预定diagnostic中提取真实来源的graph/work数据，供另一个对话选择是否值得硬件化。没有可用dispatch/GPU completed time/DRAM/XMX计数就填UNKNOWN，不能拟合伪参数。

将“保持原B570部署参考”和“另一研究定义的新算术单元参考”分开，所有仿真结果注明来源和假设。只承认已采集且通过对应的tensor，未知归约树不逆向猜测。

作者不希望越做越窄：禁止为让四个sentinel通过而继续head/layer/token搜索；P1失败按本阶段NO-GO收尾、P2必须未见自然输入；贡献若只存在极窄条件，不投入第三轮搜索。P105尚未补齐的前沿仍标pending，本研究不自动续跑它，也无需等它才做P0。
