# Systems / novelty whole-paper 独立首次内部模拟评阅

本评阅仅针对 `review_packet_initial` 中固定的 v0.10.0 新稿。未阅读 packet 外的旧评阅、提示、工作记录、其他评阅者意见或作者原始审计报告。没有执行模型、GPU 推理或任何新的科学实验。

## 阅读与核验范围

先核对 `SHA256SUMS.json`，四项全部通过，PDF 实际页数为主稿 12 页、附录 23 页。阅读全文，包括主稿 §§1–10、参考文献，以及附录 A–T、全部比较表和参考文献。另渲染检查主稿第 3、5、6、7 页和附录第 19 页，主要用于核查 Figure 1–3、Table 1 和邻近工作比较的实际版面。

| 对象 | 本次实际读取的 SHA-256 |
| --- | --- |
| `manuscript-v0.10.0.pdf` | `c089271735661bce0ea8a89fcf206531c9dbb928d9cfe869f78a0677bc6bb8e8` |
| `appendix-v0.10.0.pdf` | `bd143c90cf8dbe743db7717f13d81db8cbbb256875d4c3659d18d5f6e0486310` |
| `INDEX.md` | `8d9dbc7c885d8c2606bab34491f0f486e3a824410f4f35e8978b90a1d026207c` |
| `anonymous-intervention-evidence-v0.10.0.zip` | `b74629942f65677ce3a0e25f9fefbcde55ec3238cafb4b8917dce89eceb80427` |

读取匿名 ZIP 的 README、完整数组、派生比较、manifest 和 verifier，并按其 CPU-only 入口运行 `python -B verify_v010.py`，结果 PASS。入口同时重算其内嵌历史 v0.9.0 的不可变 base projection 和 v090 扩展，均通过。另用独立短程序直接从完整数组重新配对核算五类比较，确认 1005 个唯一条件记录、67 个 task units、三次重复稳定及下述核心计数；核查 /15、/18、/25、MBPP/304、/463 的完整长度、endpoint 和差异位置。全部 1005 条导出记录的 overshoot 字段为 0；EOS 记录末尾都是 ID 151645。这是数组层面的观察，不是对原始停止解析器的独立验证。

匿名 compact packet 没有新干预的全部原始 trace、运行源码、KV bytes、原始 remote readback 或权重/二进制实体。因而我不能独立核验无未来答案输入、graph occupancy、实际线程配置、handoff/sham 的所有原始见证、原始封存时间，或重新鉴定模型/运行时资产。主稿和附录所述 raw audit 的 PASS / QUALIFIED_PASS 是作者提供的报告摘要；本次并未复做它们。哈希核验与导出算术 PASS 不能填补这些边界。

另做了有限的 primary literature lookup，只查公开原论文：Chordiya arXiv:2607.17283v1、LLM-42 arXiv:2601.17768v2、Vosti arXiv:2609.38981v1、Correctness Forensics arXiv:2510.22876v4。阅读相关方法、主张和限制段落，用于检查近邻关系；未做穷尽文献调查，也未读取任何本项目外部评阅。

## 主张和贡献的准确概括

论文的问题是：一个 native speculative path 不匹配指定 greedy reference 后，能否用事先冻结、输入契约明确的可执行描述，算出它完整的后续 ID 和 endpoint，并在受控改变执行路径后继续预测其输出？这里的“预测器”运行真实数值推理，是执行描述，不是学习模型，也不声称不运行推理就能预测。

1. B570/Vulkan 的 target-only、draft-free 描述，在 24 个已暴露任务上，对原始 target prefill/continuation UB1 路径及 prefill 改为 UB128 的 native 路径都匹配 72/72 完整数组和 endpoint。干预包含第一次 pending sample/state handoff，continuation 和 draft 仍为 UB1。四个诊断任务恢复 reference 匹配，20 个控制任务没有新偏离：60/72 → 72/72。它证明这组任务上的恢复，未证明唯一 prefill KV 原因或生产修复。
2. RTX/CUDA 用独立应用/API 编排的 proposal worker 和 target worker，保留共享 pinned numerical routines，预测 target continuation UB2 → UB1 前后的 native 路径。19 个已暴露 HumanEval 和 24 个 exposure-audited MBPP 任务的每个条件都完整匹配，分别 57/57 与 72/72。RTX 的修复目标却失败：HE/15 恢复、HE/25 新偏离、HE/18 持续偏离；MBPP/463 与 /304 持续偏离，其中 /304 的输出发生改变。不能把 persistent deviation 当作 output no-op。两种条件总体 reference agreement 同为 117/129，但不表示干预无效或实现了修复。
3. 论文把这些预测比较、reference compatibility 和独立成本决策分开。独立 RTX V4 三路径研究中，serialized 路径通过 57/57 ID gate，但 instrumented post-prefill speedup 为 0.677；358H CPU/NPU 完整成本中的 overhead-only prompt-GM ceilings 是 0.8372/0.8448；M4 held-out Guard 通过 ID gate，但比 Always-Spec 多 2.71% GM latency。这些分别支持拒绝某个优化候选、改变成本优化前提、优先选择被测固定 speculation，而不是一个统一跨设备修复器或新自适应策略。

## Strengths

- **核心有限观察具体、可证伪，而且保留失败。** §4、Table 1、Figure 2 与附录 T 的完整比较支持论文实际声明。RTX 没有将 failed restoration target 改名为成功；这比只报 prediction/native 100% 或只报聚合 agreement 更有科学价值。MBPP/304 的一处 token 改变也避免了以“仍不匹配”掩盖行为差异。
- **B570 的简化确实有实质内容。** 附录 J/S.1 的原始 target-only 描述移除了 draft loading、proposal generation 和 speculative outer loop，却预测了 reference 之外的完整后缀；这不是只记录第一处分叉。旧 reserved cohort 的四条非 reference 轨迹包含 155 个不同位置，虽不能视为独立样本，仍显示再现范围。新干预进一步检验了该简化能否描述恢复后的 native path。
- **数值路径与输出协议的区分认真。** §2.1、§3、附录 Q/T 明确 UB 是容量而非已占用 graph shape；也保留 inclusive EOG、cap、完整数组与 endpoint、失败尝试及固定比较器。论文没有把 functional HumanEval correctness、跨硬件 bitwise determinism 与特定 reference equality 混为一谈。
- **成本否定结论有可用的工程意义。** §5.2 和附录 P.4/P.5 的界限在明确固定 baseline/target work/progress 的前提下成立，并与原 prompt estimator 对齐。对于被测 358H interface，它足以阻止把全部研发押在消除 replay/proposal overhead 上。RTX Table 2 与 M4 Table 4 同样展示“通过 gate”与“值得优化”是不同决定。
- **统计和研究历史的透明度高。** 三次重复被当作稳定性观察；bootstrap 单位是 prompt；exposed、held-out、post-study、不同计时边界及 M4 freeze metadata defect 均明确保留。我没有发现本次重算的核心计数或成本数值与报告不一致。

## Weaknesses 与系统知识增量

**最主要问题是“可执行描述成功预测”究竟贡献多少新的系统知识。** RTX 描述保留 proposal generation、target sampling、accept/correct/bonus、KV reconciliation 和共享数值库，基本执行完整 speculative 语义。它与 native outer loop/API 编排不同，且没有输入 future native answers，因此我不把它称为答案复制或逻辑循环。但数值计算和关键状态转移都保留以后，完整输出相同较接近一项重要的实现等价性验证。§4/§7 没有展示这种表示使工程师解决了哪项普通 deterministic replay、直接 ID gate 或源码跟踪难以解决的问题。冻结和完整后缀扩大了证据可信度，并不自动扩大方法的知识增量。

B570 的 draft-free 再现比 RTX 更有辨别力，但论文尚未把两者合成为一种可复用的执行描述构建方法。§2.2 只定义描述的形式，§4.1 主要列契约与数值；描述如何从原 native path 导出、什么信息可以删掉、什么条件应改变描述，而不是观察输出后选择描述，主要散布在附录 J/M/Q/S/T。其旧 H1/H2、V2/V4 与新 P0/P1 名称也增加了审阅负担。读者得到一套很详细的审计历史，仍缺少一页能用于新 runtime 的方法。

**邻近工作区别存在，但当前主要是问题范围的区别。** [Chordiya §6.1](https://arxiv.org/html/2607.17283v1) 已测量 quantized Metal 中 target-only batch-dependent argmax changes，也把 correctness gate 和完整成本分开；[Correctness Forensics](https://arxiv.org/html/2510.22876v4) 提供状态同步 invariants 并区分 numerical mismatch 与实现同步错误；[LLM-42 §§4.1–4.2](https://arxiv.org/html/2601.17768v2) 构造固定形状验证、rollback 和 KV repair；[Vosti](https://arxiv.org/html/2609.38981v1) 给出固定部署下更强的 bitwise-logit specification 和 engine/kernel 验证。本文不是这些工作的劣化版本：准确预测一种仍 reference-incompatible 的 native path，确实是不同目的。可是 Table A26 主要说明“我们不承诺其保证而做 finite prospective prediction”，尚未充分说明为什么这个较窄目标产生足以支撑 whole-paper 的新 insight、工具能力或节约。

**正面干预结果的范围很窄，独立新任务上的有意义干预信息较少。** B570 §4.2 是此前四个已知诊断 mismatch 与 20 控制的恢复；此前 original H1 的 reserved 验证不能当作新 intervention 的 held-out 验证。RTX 新 MBPP cohort 是有价值的 exposure-audited 外推，但 24 个任务中 23 个 N0/N1 完全不变，仅 /304 发生一处改变而仍偏离 reference。因此“两个条件预测全对”对改变路径之后的 predictive capability 的实际压力，并不等于在大量新增、改变输出的测试上预测正确。论文已承认有限范围，问题是 impact，而不是其计数不成立。

**成本章节支持局部工程拒绝，未形成核心干预的成本/价值闭环。** Table 1 明确没有两项新干预的性能或能耗结果；§5 的 RTX global UB1 serialization 同时改变更多阶段，不是 §4 RTX candidate，不能量化预测所验证候选的系统 tradeoff。§5.2 的 target-work ceiling 有用，但优化目标仍停留在“必须改变 target work/progress”；现有成本分解未给出哪种可执行改变最有希望、与输出描述如何相接。§6 的 Guard 实证是诚实的负面结果，却也展示固定 Always 已经接近所定义的两固定模式 oracle；这对评估控制机会有价值，对论文标题下的 intervention prediction 贡献联系较弱。负面结果本身不是缺点，当前缺的是这些局部结果产生共同、可迁移设计结论的论证。

**成本的实测边界限制优化结论的用途。** §5.1/附录 Q 的 RTX instrumented CLI latency 包含 condition-dependent debug logging，clock-call probes 不能界定其全部成本；因此 0.677 是被测记录路径的结果，不是 logging-free deployment ratio。M4 不包含部分 setup 和 prefill，并且 oracle 只在两个已测 fixed modes 中选择。这些限定写得准确；不能靠更多 prompt bootstrap 缩小 interval 来变成部署结论。对于本文已限定的局部结论，我不据此判定测量失效。

**展示有一处实际版面缺陷。** 主稿第 3 页 Figure 1 下方的“Does the description forecast this path?”与中列说明相互覆盖，使论文最核心三种判断的区别难读。Figure 2 的配对展示清楚；Figure 3 的成本域标签清楚。Figure 1 应缩短说明或重新排版。§3/§9 大量 provenance 限制很有必要，但正文重复防御性界定挤压了方法解释空间。

## 接受判断前三 blocker（按优先级）

| 优先级 | Blocker | 分类 | 为什么影响判断 / 需要什么 |
| --- | --- | --- | --- |
| 1 | 预测闭合的新增系统知识与用途尚不足，尤其 RTX 描述接近完整机制的再执行 | **fundamental-novelty-impact** | Prospective seal 与配对核算增加可信度，却不是独立的算法/系统 novelty。需明确一个从 gate/replay 之外获得的新能力或可迁移发现，并展示完整描述在实现复杂度、资源、故障缩小或候选选择上产生实质差别。单纯改写贡献措辞不能完全解决。 |
| 2 | 方法核心尚未从审计记录中提炼出来，无法充分判断描述是如何选择与修改的 | **existing-evidence-analysis** | 用既有源码/调用见证给出简洁构建规则、before/after pseudocode 与 native 对照：共享什么、删去什么、状态边界在哪里、怎样从旧描述得到新描述；用至少一条发生改变的轨迹说明预测如何得出。许多材料似已存在，优先分析而非另跑模型。若只能给出两个特例，也应直接说明其设计原则尚未形成。 |
| 3 | 支撑有意义路径改变的外推证据不足，正面恢复仍局限于已知 B570 诊断集合 | **new-evidence** | 我不要求唯一 stage cause、特定 factorial、普遍修复或所有 RTX 任务恢复。需要一个针对核心用途、预先冻结的独立检验，使描述面对新的实际行为改变，并展示它能帮助选择/拒绝候选。可是在一个有理由预计偏离的新配置上验证，或在新的未用诊断 cohort 上验证 B570 描述；关键是新信息，不是扩大旧稳定任务的重复数。 |

第一项是实质接受障碍；第二项可能用现有证据显著改善评估；第三项是在承认 finite case-study 定位后，仍影响系统研究分量的证据缺口。Figure 1 版面问题属于 **expression**，不是前三实质 blocker。

## 内部评分与理由

内部量表：**1 reject，2 weak reject，3 borderline，4 weak accept，5 accept**。这是本次模拟阅读的内部判断，不是正式会议评阅、接收概率或对任何会议结果的预测。

**总体：2/5（weak reject）。Confidence：3/5（中等）。** 我相信此次供给的 finite comparisons 和主要条件成本算术；不认为 RTX failed recovery 会否定其预测主张，也不把缺少唯一 stage 归因当成必须补齐的逻辑漏洞。偏拒绝来自系统知识与实用方法的分量：B570 提供有趣的简化和恢复例子，RTX 提供完整预测与修复分离的例子，但 whole-paper 尚未展示比严谨复现/验证流程更明显的可迁移系统贡献。成本研究的局部否定结论增加价值，但与新的预测/干预方法联系不足。

Confidence 没有更高，是因为 compact evidence 只能复核导出和历史算术，不能让我直接审阅所有新干预源码及 raw handoff/proposal/graph witnesses；文献核查也限于上述近邻段落。若既有源码能够显示目前正文没有说明的重要结构简化或实际候选筛选能力，判断可向 borderline 移动。若只是再次证明现有数组相等，判断基本不变。

## 最有价值的修改

先围绕一个具体系统用途重写方法与贡献，而不是继续增加 audit chronology。把 B570 的“删除 draft 仍重现非 reference 后缀”和 RTX 的“容量标签不足、保留哪些状态/数值执行才能重现 changed path”写成可审查的描述构建过程；用原始已有记录给出程序结构、调用/状态迁移、与 native 的结构差别及复现代价。说明工程师拿到 mismatch 后，依靠这套方法比直接 gate 和 native replay 多知道什么，哪一步减少了候选空间或复现负担。新的模型实验应在这项用途清楚后，以一个预先冻结、能产生新行为改变的检验验证它。

其次，把 §5–6 保留为证据明确的工程决策，而不让它们替核心干预补出未测量的优化收益。358H 的 conditional ceilings 是这里最有价值的可复算优化预算，值得强调；M4 结果可以简化为“held-out qualified Guard 未超过固定 speculation，需先评估固定模式机会”。同时修复 Figure 1、压缩重复限制说明，把原始 study 名称与新 P0/P1 的映射集中一次列清。

## 不会改变当前判断的追加实验

- 在相同四个 B570 诊断任务或相同 RTX cohorts 上增加很多稳定重复；它主要加强重复稳定性，不能提供新方法或新外推信息。
- 没有具体竞争解释就补一个大而全的 stage/factorial matrix；更多组合本身不会证明描述的知识增量。若某个对照直接区分已有 competing explanations，才有价值。
- 仅扩大被测模型/设备数量并报告 mismatch rate，而不事先冻结与检验输出描述；这会成为另一份 sensitivity inventory。
- 继续展示 isolated draft throughput、提高 acceptance rate，或更精细地计算已经成立的 conditional ceilings；不能代替完整 qualified execution 的成本与用途。
- 只增测历史 serialized 路径的能耗，或重新调 Guard 得到一个更好的 workload GM，而不与主问题建立联系；这些不会解决当前最重要的 novelty/impact 顾虑。

本次没有发现能用纯算术修正翻转结论的错误。最有效的方向是将已经较可靠的观察，提炼为一个明确、可用、能在新情形下经受检验的系统方法。
