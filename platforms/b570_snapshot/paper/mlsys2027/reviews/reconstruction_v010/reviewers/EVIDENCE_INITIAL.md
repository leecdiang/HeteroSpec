# EVIDENCE_INITIAL — 首次独立 whole-paper 内部模拟评阅

这是内部模拟评阅，不是 MLSys 会议判断，也不表示接收概率。本次首次独立阅读，没有读取其他评阅意见、目录外 prompt、作者工作记录或原始审计报告。评阅立场是 evidence / causal reasoning，综合评价整篇论文，而非为某种预定 stage/factorial 实验设计验收。

## 范围、身份与实际核验

唯一输入是 `review_packet_initial/` 中固定 packet。阅读主文全部 12 页、appendix 全部 23 页、INDEX、匿名 intervention ZIP 的 README/manifest/数组/派生比较，以及其内嵌 historical-v0.9.0 ZIP 中相关证据与 CPU 算术代码。额外目视检查了主文 Figure 2 所在页。没有执行新模型或新实验，没有联网，也没有读取 packet 之外的科学记录。

| 对象 | 实际 SHA-256 |
|---|---|
| manuscript-v0.10.0.pdf | `c089271735661bce0ea8a89fcf206531c9dbb928d9cfe869f78a0677bc6bb8e8` |
| appendix-v0.10.0.pdf | `bd143c90cf8dbe743db7717f13d81db8cbbb256875d4c3659d18d5f6e0486310` |
| INDEX.md | `8d9dbc7c885d8c2606bab34491f0f486e3a824410f4f35e8978b90a1d026207c` |
| anonymous-intervention-evidence-v0.10.0.zip | `b74629942f65677ce3a0e25f9fefbcde55ec3238cafb4b8917dce89eceb80427` |

四项均与 packet 的 SHA256SUMS.json 一致。另核验 intervention ZIP 内五项 manifest，及 historical ZIP 的原 manifest 29 项、V090 manifest 35 项，均通过。

为遵守仅写此评阅文件的范围，我在内存读取 ZIP：运行了 supplied verify_v010.py 的 compute()，与 DERIVED.json 全量一致；另用自行编写的比较代码重算 1005 个数组、67 个 task unit、五条件、三重复的完整 ID/endpoint equality、稳定性、reference transitions 和所有 native before/after 变化。没有调用会临时解包/写文件的 verify_v010.main()，也没有宣称执行了完整 historical base verifier。另运行 historical verify_v4.validate()，独立重算 358H 两种 ceiling 及 M4 Guard/Always GM、secondary CI 和 fixed-mode oracle。以下证据结论有上述 CPU 复算支持。

| cohort | task 数 | 每条件数组数 | P0=N0 / P1=N1 | reference task match before→after | N0=N1 task 数 |
|---|---:|---:|---:|---:|---:|
| B570 exposed24 | 24 | 72 | 72/72；72/72 | 20→24 | 20 |
| RTX old19 | 19 | 57 | 57/57；57/57 | 17→17 | 17 |
| RTX new24 MBPP | 24 | 72 | 72/72；72/72 | 22→22 | 23 |

所有五条件均三次 repeat-stable。600 个 EOS 数组最后 ID 均为 151645，之前无 packet 所列 EOG；其余 405 数组均为 128 IDs，endpoint 为 CAP128 或 limit。所有 export 的 overshoot 字段为 0。这能确认该 export 的边界一致性，不能确认未提供 raw stop-marker/overshoot 日志的完整保留。

B570 四个变化是 /134 index88、/138 index93、/145 index103、/42 index73，分别 40、35、25、55 个对齐位置变化；RTX /15 为 25→28 IDs、index15 起 10 个对齐位置变化及 3 个附加 ID，/25 为同长度75仅 index4 变化，MBPP/304 为同长度47仅 index33 变化。/18 与 /463 的 complete native output 确实不变，/304 虽 persistent reference mismatch 却不是 output no-op。旧19个 RTX task 的全部57个 exported N0 数组也与 historical V4 live 数组一致；这说明数值一致性，不证明新的运行来源或线程设置。

成本复算：RTX V4 qualified serialization GM=0.6773510334，CI=[0.6616533074,0.6918118724]，0/19 prompts 更快；batched 51/57 被 gate 阻止。358H prompt-GM ceilings 为 CPU 0.8372192092、NPU 0.8448401086；pooled ceilings 为 0.8274529834、0.8351858524。M4 Guard/Always=1.0270760220，独立 secondary CI=[1.0129560055,1.0435592654]；Always/two-fixed-mode oracle=1.0006919671，target faster 为2/60。没有发现这些核心数值与主文不一致。

## 我理解的贡献

论文提出并测试的是冻结的可执行 execution-path description，而非学习预测器、新解码算法或数值正确性证明。它把 complete native-output prediction、对特定 greedy reference 的兼容、paired intervention outcome 和 realized cost 分开。

B570 使用无 draft/proposals 的 target-only description，在 target prefill UB1→UB128、保留 continuation/draft UB1 并作首次 pending sample/state handoff 的条件下，预测并恢复已曝光24任务中四个已知 deviation，20 controls 不新偏离。RTX 使用有自身 feedback/proposals 的 P/R orchestration，数值例程与 native 共享，预测 target continuation UB2→UB1 前后43任务的完整 outputs；但旧19任务的一恢复与一新偏离相抵，MBPP两个 mismatch 保留，因此 predefined recovery/no-new-regression target 失败。不同描述和不同干预的两组有限成功 prediction，不能合成跨硬件统一预测器或修复规律。

独立的成本研究说明 qualified serialization 仍更慢、358H 在固定 measured target work/progress 前提下去掉其他开销仍不达 parity、M4 Guard 虽胜 target-only 却劣于 Always-Spec。它们不是新干预的性能数据。论文的真实新增点是有限、前瞻的 full-output 干预验证，以及保留失败修复结果；aggregate cancellation、成本恒等式和正确性 gating 本身不是新贡献。

## Strengths

1. **主要结论与完整数组相符。** §2.1、§4、Figure 2、Appendix T/A27–A28 没有把 prefix equality 当 complete equality，也不把三次重复当独立任务。/15 的长度变化与 /25 的 reconvergence、/304 的 persistent-but-changed 输出，使配对比较比单一 gate count 更有解释力。
2. **失败候选没有被重新定义成成功修复。** RTX 的 prediction closure 与 restoration failure 同时报告，且 old19/new24 分开；§4.3 不从 total agreement 不变推导 intervention 无效或无输出变化。这个负结果可信且有用。
3. **B570 存在实际 description simplification。** 早期 draft-free predictor 在 reserved tasks 上的完整非reference suffix 预测，随后在 exposed cohort 的 controlled restoration，强于仅找到一个首错 token 的 retrospective reproducer。它仍不证明 draft 在 native 中因果无关，论文对此限制正确。
4. **对因果边界的措辞相当克制。** §4.2 明示 prefill+sample/state handoff；§4.3 区分全局 UB1 历史路径和当前 continuation-only intervention；Appendix L/P/S 把一次 sampled block 的数值变化、immediate decisions 不变与 persistent continuation 下 delayed divergence 分开。没有把 graph capacity 当 occupied shape 或把跨平台差异当硬件原因。
5. **成本证据自洽且估计对象清楚。** §3.2、§5、§6 区分 prompt-GM 与 pooled accounting、instrumented post-prefill 与部署 latency、primary 与 post-study analyses。bootstrap 单位是 prompt；M4 hindsight oracle 只比较两种 fixed mode。这些限制没有被图形或结论抹去。
6. **可独立重算的中性数组和历史计时投影是实质资产。** 此 packet 足以发现许多 array/endpoint/count/estimator 错误，实际复算通过。失败 attempts、host-policy amendment、metadata defect 和 effective thread correction 被承认，也优于隐藏这些研究历史。

## Weaknesses 与证据边界

**A. 核心新方法的增量价值仍不够清晰（§1、§2.2、§4.1、§7、§8、Appendix A26）。** B570 target-only simplification 是有意义的；RTX richer description 则再次执行同一 pinned numerical routines 下的 proposal-conditioned target computation。允许 shared numerics 是合理的，不使结论无效，但“描述预测”与“把 native 计算重新编排并预先跑一遍”之间，尚未给出读者可复用的抽象或选择程序。Table 1 说明输入，却没有解释如何从 path specification 构造 P1、它省掉哪些 native 复杂性，以及成功或失败 prediction 提供什么不能由先跑该 candidate native+reference gate 获得的工程收益。论文承认没有 debugging-time saving 或 performance benefit；那么剩余 research impact 必须更具体地证明，不能只靠更严谨的术语与 sealing。这是价值/新颖性疑问，不是要求一个唯一 stage cause。

**B. 新 intervention 的最关键 controls 在本 packet 中不可独立重查（§3.1/3.3、Table 1、Appendix T）。** FORMAL_ARRAYS/DERIVED 包含 R/P0/P1/N0/N1 和结果，未包含本次 intervention 的 predictor/native source、sealed tape内容、freeze/readback receipts、same-boundary sham逐项输出、KV/logits/sample handoff records、graph-occupancy traces、完整 attempt manifest 或字段映射。historical ZIP 的 `B570_live_intervention.json` 是较早的 sampled fork研究，不是本次新的 prefill intervention。INDEX 和正文引用的 author-side raw audit PASS/QUALIFIED_PASS 是作者报告，本次无法据此确认。这不反驳数组结果，却使 central prospective/control/input-separation claims 的核验强度低于 arithmetic claims。应把现有 retained evidence 的匿名关键投影提供到同一 packet，而非要求新GPU运行或独立可信绝对时钟。

**C. 冻结与独立性的结论需要分层阅读（§3.1、§4.1、Appendix J/M/Q/T）。** 前瞻性是 reported implementation/prediction-before-native ordering，不是独立 preregistration 或 blind model selection。B570本次24任务已曝光；RTX旧19已曝光，新MBPP24是 audited project records 中无已知 prior execution exposure，并非训练未见或随机代表样本。P/R与native的 application/API分离不等于 independent numerical implementation；hash验证内容不验证绝对时刻。主文通常已准确说明，但 §3.1 “offline intervention review restores … raw/trace records” 与 §3.3 “anonymous index recomputes …” 容易让当前 packet 读者误以为自己能重做那份 raw audit。请明确作者侧审计与本文提供给读者的可验证对象。

**D. 对干预效应的有限因果推断合理，外延较弱（§4.2–4.3、§9）。** Same-boundary sham如果按描述成立，可以控制 transfer程序本身；首次sample/state handoff仍属于treated path，不必分解成“pure prefill KV”。B570结果可支持该 combined intervention 在此 cohort 的 path-level restoration。RTX continuation-only candidate 失败，既不证明其他stage必要，也不排除该stage对部分任务有效；/15本身恢复。old global UB、draft、prefill、thread defaults 与当前 configuration 变化阻止历史对比作necessity/interaction归因。论文没有越界，但它能支持的修复/可迁移洞见也因此很有限。

**E. 成本章节正确但与主贡献松散（§5–§7、Table 5）。** 三个平台的 cost案例不是 controlled intervention路径的成本，不能解释新干预是否有可部署价值。RTX condition-dependent logging cost没有被clock-call probe界定；358H replay/proposal不可分且ceiling固定 measured target work/progress；M4 post-study fixed-mode oracle不能解释 within-request control机会。正文承认这些，故我不把结果判为错误；问题是多个正确而窄的诊断被汇总成“framework”，没有足够说明其相对于已有 gating/profitability work 的新增系统决策能力。

## 按优先级的前三项 acceptance blockers

| 优先级 | 类型 | 阻碍 | 最有价值的解决路径 |
|---|---|---|---|
| 1 | fundamental-novelty-impact | 有限 prospective numerical reexecution 与已有 reproducer/forensics/gating 工作的新增系统价值尚未充分建立，尤其RTX共享例程的rich description。 | 给出明确可操作的方法：description怎样选择/构造、怎样预测一个变化、删去或隔离了哪些native结构、怎样改变真实研究/工程决策。现有B570 draft-free简化应成为具体例子；若可提供已记录的工作量或被成功区分的竞争解释则最好。单纯重新命名closure或再强调配对抵消不能解决。 |
| 2 | existing-evidence-analysis | 本packet支持export arithmetic，但无法独立审核新干预的sealing、input allowlist、sham、handoff、occupied shape与complete-attempt选取。 | 将已经保留的匿名source片段、依赖/输入合同、freeze roles/readback顺序、sham denominators和逐项结果、handoff/shape摘要及original→export字段绑定放入packet并可CPU检查；把作者侧raw audit与reader verification能力分别标注。无需新模型运行，也不需要绝对时间认证。 |
| 3 | new-evidence（如要提升外延/影响力）；有限结论本身无逻辑缺口 | B570恢复只在已知exposed24上；RTX的新MBPP cohort增加了prediction evidence，却没有显示恢复或统一方法迁移。当前可发表影响力很依赖两个局部案例。 | 最具判别力的是一次预先冻结、未曝光B570 intervention cohort，或在一个具体独立configuration上无结果驱动改写地应用已选description，或一项明确的实际诊断收益验证。选择一种与贡献相符的目标即可；不是默认要求所有stage的factorial，也不是强制广泛model/hardware sweep。 |

第3项是对研究广度/影响力的接收门槛判断，不表示作者目前有限的 “these tested descriptions match these outputs” 结论需要该新数据才能成立。若将论文定位为精确案例研究而非通用方法，其权重可以降低，但第1项仍需令人信服的case-study洞见。

## 高价值修改与无效追加

最优先的无新运行修改是：把新intervention实现/信息合同写成紧凑可执行流程，呈现关键sham与handoff观测的denominators及允许验证的字节；增设一张reader-checkable、author-audited-only、omitted的证据能力表；围绕B570简化与RTX candidate rejection讲清具体新增用途。Figure 2可在persistent组旁注明 /304 changed、/463 unchanged，避免只有reference状态时读者把两者看成同一种路径反应。历史H/Q/cost臂的身份保持，主文可减少重复limitations语句，腾出篇幅解释description的构造。

不值得默认追加：在同一exposed task上再增加重复次数；把1005 arrays当1005独立样本做显著性分析；仅采更多raw logit perturbations却不对应竞争解释；不冻结新描述的post-hoc stage search；只提高isolated draft throughput来暗示端到端收益；仅增加clock-call probes来证明logging-free cost；无明确问题的大规模hardware/model列表。一个predefined competing explanation的targeted test可以有价值，但当前论文的bounded prediction主张不以unique-stage identification或完整factorial为前提。

## 内部评分与 confidence

**内部总评分：3/5（borderline）。** 数组、完整endpoint、paired effects与主要成本算术可信，且论文并未把成功prediction冒充成功修复。对于有限empirical claims，我倾向认可。阻止我给4/5的主要原因是增量方法/系统影响力偏弱，以及新干预的controls/source/freeze证据在本packet中尚不能独立重查；并非没有做某一套指定stage实验。若关键retained证据可匿名公开且method用途阐明，现有结果有可能支撑更正面的判断；纯表达压缩未必足以跨越impact问题。

**Confidence：3/5（中等）。** 全部PDF覆盖、manifest和full-array/cost复算使我对表中有限数值与推断边界较有把握；但没有模型复现、原始intervention source/log审计，且按唯一packet限制未外查引用文献与priority，所以不能高度确信novelty或raw provenance。INDEX中的B570 PASS / RTX QUALIFIED_PASS只按作者侧报告记录，未当作我的独立审计结论。

无法验证项明确包括：原始prediction/native运行的真实外部时间、作者机器全部历史exposure、MBPP selection与freeze的底层记录、权重/omitted runtime/compiler/driver字节、opaque sampler状态字节相等、sham/handoff/graph traces原始内容、原始attempt的选取完整性、无未披露future-answer channel，以及作者侧原始审计报告的全部结论。这些局限不推导出造假或错误，也不能由export equality本身排除。功能HumanEval/MBPP正确率、生产性能、能耗、新干预成本、population failure rate或unique floating-point cause均没有在本评阅中验证，论文也不应据此宣称。
