# 交给 Windows / RTX 平台 GPT Work 的执行 Prompt

你负责用户的 RTX 5070 Ti Laptop / Windows HeteroSpec 工作。B570由另一平台独立推进；本任务不是接管或重跑B570。

仓库：https://github.com/leecdiang/HeteroSpec
当前闭环PR：https://github.com/leecdiang/HeteroSpec/pull/104
后续设计分支：design/rtx-reference-packing-after104-20261015
后续设计目录：docs/experiments/rtx_reference_packing_20261015/
新代码/结果目录：benchmarks/rtx_reference_packing_v1/

**按顺序实际推进，不只写计划：核对原机状态 → PR104 E2跨日期收尾 → 原PR E1 → 原始证据恢复/复算和封存 → 后续PR H0 → 有条件H1/H2 → H3结论。先完成跨日期任务，再按新PR继续。**

## A. 接手时先看事实，不从旧PR简介推断未运行

1. 读取PR104最新head、comments、原机worktree、F0、ledger、SESSION receipts、supervisor/锁/owned PID。设计者本次读取PR104的head是50e64c7c8a2ac69fd59fd4b80310687754deb071，但原机可能已前进。
2. 保护未提交文件，不reset/clean/force-push，不替换原runtime。原机如果不是目标RTX平台或身份不符，停止原机执行并报告。
3. 已开始/完成的slot绝不重跑。已有合法supervisor还在运行时，不启动第二个。锁和receipt不能为了恢复而删除，先核对生命周期。
4. PR104 README开头等历史说明可能滞后；以固定协议、准入补充和实际账本交叉核对，不把旧“zero GPU”文案当成当前状态。
5. 读PR104的README.md、RUNTIME_ADAPTER_AMENDMENT.md、E2_TRANSPORT_AMENDMENT.md、registration/E2_F0.json、registration/E2_TRANSPORT_F0.json及实际driver。保留family×arm的15条真实binary/source路由，不用一个统一binary替换。

## B. 先完成E2跨日期任务

仓库上次记录s0–s4已完成1350 requests/270 workers；若原机未前进，剩余s5是270 requests/54 workers，而不是重跑六组。真实剩余额度由账本确定。

s5已记录最早为北京时间2026-10-15 12:27:07，同时必须满足距上一session结束≥1小时、距第一session开始≥24小时及其余原始条件。计算真实UTC/本地时间对应，晚开机可以更晚，不改系统时钟、不伪造时间、不压缩间隔。未到时间就保持原已授权机制或封存为WAITING，不先运行新模型或重负载来占空档。

全E2预算固定：1620 requests（含324 warmups）、324 workers、owned43200秒，已消耗不重置。保持相同面板、顺序、模型、DLL、sampler、timer和1.02阈值。正式counts禁止Nsight、GPU queries、额外同步、重捕获、新kernel/driver/电源调优。系统更新或其他漂移触发原门槛时如实停止，不假称环境未变。

只有符合原transport补充的“科学slot完全未启动”传输恢复才可重试传输；错字节、已有receipt或科学启动后的错误不能被改名成网络重试。只处理owned进程。

六组完成后按原脚本和独立复算输出全部family×M/C对照、参考资格、每session和每task比值、退化、实际意义阈值和六cluster不确定性。缺失/失败/输出不一致按原规则withhold，不挑成功子集，不为了显著性扩样本。

若E2已失败/停止，保留F0、失败、所有成本及未启动坐标并封存。不要为了进入后续PR绕过原E1门槛。E2无正收益本身不是失败，更不是停止研究的理由；合法负结果照常收尾。

## C. 再完成原PR104的E1，不把后续任务塞进E1预算

E2完整闭环且原准入满足后，依原授权完成E1独立native接入与真正F0；已有明确有效授权不重复索要，确有缺失的授权节点再停。

72 contexts：三家族×首/中/末层×prefill/continuation×q1..4。保持原key条件和最长继承prompt选择规则；不根据数值或速度换题。HS_E1_LAYER/PHASE/Q/MIN_KEY必须真实通过sanitizer与serializer。隔离构建，只改已准许诊断部分，不覆盖E2二进制，不变数值DLL和模型。

上限216 model requests（含warmups）、432 standalone operator starts、owned21600秒；所有失败/启动计账，无额外probe/smoke/retry。保留input bytes/shape/stride/mask/GQA、生命周期、capture-on/off完整endpoint、MQ own-path、各arm重复；缺context标NOT_OBSERVED，own-path失败标NOT_ADMITTED，真实PQ/QB差异保留为反例。未知kernel/reduction tree不猜。

若原E1被控制/实现问题或E2终态阻塞，记录合法BLOCKED/NOT_IMPLEMENTABLE及证据，不假称72项已完成，也不擅自扩大范围。只能使用合格历史证据继续后续CPU探索。

在PR104原分支交付准确E2/E1结果和raw manifest、恢复/独立复算、实际source/runtime/F0/账本；更新滞后状态但不改旧失败文件。旧链所有owned任务结束且状态已封存后，再进入后续设计PR。不要为了进新PR先merge任何PR。

## D. 按后续设计PR真正推进CPU研究

完整读取本目录README.md、PROTOCOL.md、WORK_ORDER.json、SOURCE_LOCK.json。隔离worktree，在后续设计分支添加benchmarks/rtx_reference_packing_v1/；不复制或覆盖旧冻结实验。B570的PR108/109及其后续只读参考，不等待其正结果，也不续跑其31个旧未启动槽。

这条任务允许在前置封存后推进限定H0–H3 CPU工作；不为每个已明确CPU步骤再问作者。新增GPU/model/operator预算=0；不买硬件/云服务，不创建新的后台自动化，不改论文/main/release/Zenodo/arXiv。

H0：给出强同参考软件baseline后的剩余代价表，区分启动/图管理、数据供给、数值依赖、状态形成。结合实际源码、PR98/E1输入、E2合格请求费用；不得从总wall推kernel占比。审查固定分块、batch-invariant、ragged packing、KV multicast与可行融合，不仅拿GS作弱基线。

H1：按PROTOCOL实际实现一个小型AV加权归约的reference interpreter、上下文scheduler和独立trace/numeric checker。保持数值分块/舍入不变，只改变独立上下文资源绑定和供给。不改变softmax，不免费引入online算法。

若专有RTX算术未知，明确用DECLARED_ARCHITECTURE_REFERENCE开展合成/真实operand子视图研究，不将它称为旧RTX逐位复现。缺实际payload单列NATIVE_VALIDATION_MISSING，不伪造随机native输入。输入选择、合法裁剪、转换和拒绝域事先固定。

H2：H1通过后真正实现周期/事件模型，冻结CPU_F0和完整小网格再比较。五映射按PROTOCOL：B0_FIXED_SHARED、B1_PACKED_MULTICAST、A_CONTEXT、A_SUPPLY、C_JOINT。强基线也允许同样可行的共享/packing；相同资源、依赖、缓冲、广播与回压计费；候选多出的能力必须具体且有代价。同能力应parity，不靠削弱baseline制造硬件优越性。

上限：累计子进程运行14400秒、单进程RSS8GiB、一个重任务并发、派生输出2GiB、正式模拟cell attempts≤1024（失败/重复计入）。最多两轮有记录的实现修订，不做结果驱动无限架构搜索。原始证据只读，CPU_F0前检查实际主机余量。无证据的RTX时钟/带宽/DRAM/利用率不填默认值。

如果H0发现候选与强基线完全相同，用最小parity检验后给SOFTWARE_FIRST；若参考/输入/模型实现不足，给HOLD并列最小缺口。不要只通过文档检查便声称硬件通过，也不要因无法精确模拟专有GPU而停止所有可明确标注的有限域CPU研究。

H3：直接给技术结论，指出新机制是否成立、收益在哪些条件被开销抵消、是否只是软件组织。结果是条件原语模型，不是实测RTX端到端speedup。确有价值时提出一个下一阶段小验证方案及新预算/F0，不能自动执行GPU或RTL。

## E. 最终交付

在对话中直接输出，不只给报告链接：
1. PR104 E2/E1准确终态、总/新增成本、全部失败与未启动坐标、实际commit/F0。
2. 六session完整分析与E1数值资格分别报告；原始证据的恢复和独立复算实际做了什么。
3. 新PR的H0证据、H1/H2实现/测试/运行到哪一步，实际输入与合成输入分开。
4. 同B1强基线的全部对照、模型假设/未知量、否证/退化及资源预算。
5. SOFTWARE_FIRST / HOLD_MISSING_EVIDENCE / CONDITIONAL_MODEL_SUPPORT，附具体理由，不许只填布尔PASS。
6. 实际push的commit/Draft PR、必要源码与结果、未解决阻塞和下一步；不merge或修改论文。

请从原机现状核对开始，先完成跨日期任务，再完成原E1，最后按新设计推进。不要重跑已经完成的实验，也不要用“已写好计划”代替闭环。
