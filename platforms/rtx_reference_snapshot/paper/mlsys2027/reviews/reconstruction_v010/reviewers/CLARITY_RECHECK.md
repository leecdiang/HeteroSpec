# CLARITY_RECHECK — 唯一一轮修订复核

本次仅复核 `review_packet_final/` 中固定修订稿是否解决我的首次问题。`CLARITY_INITIAL.md` 保持不变；不重新评分，保留首次内部 3/5 borderline 判断。未读取其他评阅者意见或 packet 外工作记录。以下不是真实会议评阅或接受概率。

结论：**主要可修的图形与方法表达问题已经解决；贡献价值的界限讲得更准确，但实质 novelty/impact 疑问仍然存在。** 历史成本与当前 intervention 的关系从易误读的“预测增益”明确成独立决策证据，全文一致性有所提高。局部 study map/符号尚未完全整理。

## Exact packet 与实际覆盖

先读取 SHA256SUMS.json，重算其中全部 manifest entries，均匹配。核心对象精确哈希：

| 对象 | SHA-256 |
|---|---|
| manuscript-v0.10.0.pdf | d4c0ffeefd60b4d0b3b0b3c480157a3f298f7045410720a4a4a2ded3846df1a9 |
| appendix-v0.10.0.pdf | 2f3c0743eff79f0531954a9a129f3e6b4518e4138f2380b601b03f8b8527dc1f |
| INDEX.md | 455d7762d93136665437f8459db811ac3a6a93660a7f811fe807441887a64600 |
| anonymous-intervention-evidence-v0.10.0.zip | ff9f4cfd873225a71afceae4a5fa8c01f385f4d7377296393e98912e77ad8ffe |

文字阅读覆盖：新主稿全部 12 页、新附录全部 24 页，含全部 A27/A28。可视覆盖：两 PDF 每页的整页缩略图，另用 Poppler 较高分辨率检查主稿 p3 Figure 1、附录 p19–20 的新 T.1/T.2。主 Figures 2–3、Tables 1–5 和附录长表均在整页渲染中检查；未对每个细字作逐像素放大。

读取 final INDEX、匿名 ZIP README/verify_v010.py 与 raw-array schema；临时解包运行 `python -B verify_v010.py`，退出 0，统一数组与历史算术均 PASS。确认 1005 endpoint-bounded arrays、67 task units；B570 144 untruncated captures 的 prefix/contract IDs、endpoint、overshoot 数与 formal export 一致，N0/N1 post-cap totals 分别 60/63。所有 formal prediction/reference transitions 与正文一致。

此次对 `author-controls/` 所做的是 manifest 字节哈希检查，**没有**另行重做其 selected raw capture、源码、seal、handoff/sham 解析。也没有重做整个 15192-file archive 或 645 RTX units 的远程审计。因此我不能报告该完整 raw audit 已由本评阅独立复现。未运行模型、未验证遗漏 weights/binaries/driver 的实际字节、trusted absolute time、opaque sampler byte equality 或文献原文。额外交付提高了可检查性，不会自动扩大我的实际验证覆盖。

## 对首次问题的逐项复核

| 首次问题 | 本轮状态 | 依据与判断 |
|---|---|---|
| Figure 1 下方左/中说明文字重叠 | **已解决** | 新 p3 的三组决策说明缩短并换行；Poppler 放大图中分栏清楚，没有原先横向覆盖。Figures 2–3 的重要结果及解释仍保留。 |
| 主稿看得见结果、难以解释预测程序如何工作 | **主要解决** | §2.2 现在写出 B570 prefill→first sample/state carry→target-only continuation，以及 RTX proposal→pending-plus-proposal verification→commit correction/bonus→suffix reconciliation。明确 manually constructed、study-specific，非自动 extraction。T.1 补足各 worker/coordinator/native 的角色与共享数值计算限制，读者能够复述实际测试的程序。 |
| 缺一个当前 intervention 的具体预测例子 | **已解决** | T.1 的 MBPP/304 给出 baseline/intervention index33 的 488/481、完整 47-ID EOS prediction/native equality、两者均不等 reference。这说明新增信息是轨迹预测，而非只给 gate pass/fail；与 §4.3、A27/A28 一致。 |
| B570 simplification 与 RTX replay 被含混地赋予相同价值 | **表达上已解决；实质价值问题保留** | §7、T.1 明确 B570 删除 draft；RTX 保留 proposal feedback 和 numerical execution，不声称 execution compression、debugging saving 或独立数值实现。没有以“不是抄答案”替代全部价值论证。 |
| Table 5/正文暗示普通 gate 无法作同样 reject 决策 | **已解决** | §7 和 T.1 明说 ordinary reference gate already suffices to reject，description 额外提供 complete forecast 与 testable reproduction contract。Table 5 列名由 beyond-basic-gate 变为 evidence used for decision，RTX cost 被标明 historical。 |
| cost/guard 方法占据中心篇幅、削弱 intervention 主线 | **部分改善** | §6.1 简化，完整 guard construction/timer boundary 放到 T.2；Table 4 的主要比例、CI、direct-ID 分母，§6.2 estimator 与 secondary/hindsight 边界都在。没有通过删掉 Guard 负结果或成本估计量简化叙事。不过 §5–6 仍是较长独立支线，未成为当前预测方法的实测使用收益。 |
| V4 A/B、G0 等局部名称没有及时解释 | **部分解决** | §5.1 改为 historical V4 cost arm 与 prediction arm，主稿不再要求先知道 A/B。§4.3 解释 G0 是 effective baseline/sham qualification。但“45 unchanged H arrays reused”仍没有局部说明 H 在这里是何种 prediction 条件；§2.1 已将 H 定义为 historical text-path agreement，存在多义风险。Table 1 的 “H tapes”也可直接写 prediction proposal tapes。 |
| study map 未涵盖当前 intervention | **尚未解决** | 精确 final PDF 附录 p17 Table A22 仍只有 B570 H1/forks、RTX V4 A/B、358H、M4 六项，标题仍为 studies supporting the main argument；未列当前 B570/RTX intervention cohorts。T 在后面说明当前 studies，但不能等同于 A22 已更新。此为局部导航欠账，不是新的科学缺口。 |
| CAP128 与 raw overshoot 容易混淆 | **已解决核心边界** | §3.1、T.1、A27/A28 新 captions 明确 equality 在 specified endpoint 内，post-cap suffixes 单独保留、不进入 equality/no-op。新增 144 raw arrays 与 verifier 可核 prefix 和 60/63 totals。Figure 2 caption 仍说 raw overshoot retained，结合明确的 endpoint contract 不再构成我认为的实质矛盾；直接写 separately retained 会更快读懂。 |
| anonymous arithmetic 与完整 raw provenance review 的能力范围不清 | **明显改善，审计限度保留** | T.1 明确匿名包直接验证 exported arrays，source/handoff/sham/seal 是 separate author provenance packet 与 stated coverage 的角色；INDEX 也区分本地 selected captures 和 remote full audit。正文 §3.1 的 offline review 仍须理解为所报告审计，不能把它套用为本次 reviewer 亲自完成的工作。 |

## 剩余实质 blockers

1. **fundamental-novelty-impact：仍是优先级最高。** 新文已更准确地回答“额外信息是什么”：完整改变后轨迹及其 reproduction contract，B570 还有 draft-free 简化。我不再把这一贡献视为没有被说清楚。然而，RTX 需要手写保留 feedback 与 shared numerics 的重执行程序；matching complete arrays 本身尚未充分建立相对已有 replay/forensics/candidate execution 的显著新增研究能力。MBPP/304 让有限主张具体化，不能独自证明普遍方法价值或工程收益。论文可以作为严格经验研究成立，接受理由仍需要说明这种有限验证为何足够重要。它无需先证明唯一 stage cause，也无需改成独立 numerical implementation 才可有价值。

2. **existing-evidence-analysis / 全文凝聚：由误导风险降低为贡献组织问题。** 独立成本证据现在与 interventions 的边界准确；普通 gate 能 reject 也得到承认。因此我不再保留“文章把 cost decision 当成 prediction 增益”的同等强度批评。剩余问题是 RTX historical cost、358H bound、M4 Guard 给出了三个独立的工程负结果，仍占很大主稿空间，但没有显示 trajectory description 实际参与并改善了这些决策。可用准确的经验研究定位支持多支线，也可进一步压缩支线；这属于是否形成足够凝聚且重要系统贡献的判断，不是数组算术或数据缺失。

3. **expression：主要 blocker 已解除，只剩局部编辑。** 当前操作性描述足以读懂两个 programs；不再要求补一整套伪代码/更多 stage combinations 才能理解主张。Table A22 缺当前 studies、H 多义与若干 reviewer/version/provenance 用语尚值得整理，严重度低于首次方法问题。英文仍密集、abstract 仍同时概括两个预测与三个 cost 结果，但不妨碍准确识别主张。

## 保留的判断与不需追加的工作

首次评分保持不变，本轮不生成新分数或新的 confidence。修订显著改善了方法可读性和主张诚实程度；我的保留已经更集中于贡献增量与篇幅凝聚，而不是“作者没说明在测什么”。

补齐 study map/解歧 H、把 raw suffix caption 的 separately 一词写明属于低成本编辑。若以后继续建立更强 impact，最有价值的是直接检验一种具体 reproduction/diagnostic 能力的增量，而非把现有 repeat/cohort 数继续放大。更多已暴露任务重复、更多 isolated draft throughput、盲目 factorial、为 unchanged aggregate 添加检验或新 functional pass@k，仍不会解决上述首要判断。当前稿件并未声称新 interventions 有 optimization gain，因此我不把 intervention latency 作为必须追加的证据。

## 最终 closeout delta receipt（仅两项编辑与版式）

随后仅对 `review_packet_closeout/` 作范围受限的最终 delta 核验，不重开论文评阅、不更改首次报告或评分，也不替换上文 d4c0/2f3c 对象的复核记录。closeout manifest entries 实际 SHA-256 重算匹配；PDF 身份如下：

| closeout PDF | SHA-256 | 页数 |
|---|---|---|
| manuscript-v0.10.0.pdf | 5433df69f8f091c41b604f9f02714c435672a06e0379a63d2dcb96db30500185 | 12 |
| appendix-v0.10.0.pdf | ff1a69b1d425bf01108a59d7fb4de6d27e7e74b1b25d7849c33fd3d33715ac28 | 24 |

此次文字/视觉覆盖限于主稿 p5 的 §4.3 与附录 p17 的 Table A22，均重新用 Poppler 放大渲染查看。

- **§4.3 的 H 解歧已落稿。** 现为 “45 unchanged prediction-worker (H) arrays reused”，并保留 75 fresh native / 45 reused 的原计数和 G0 baseline/sham 说明。这解决上文所指出该句 H 未局部定义的遗漏；未将它改写成 120 个新 native outputs。
- **A22 当前干预两行已落稿。** 新增 B570 prefill intervention（T0/T1 vs N0/N1，Exposed24 × 3，CAP128，no timing）与 RTX continuation intervention（H0/H1 vs N0/N1，19 × 3; 24 × 3，EOG/cap128，no timing）；原六项仍保留。上文“尚未解决”的 current-study-map 状态仅适用于 d4c0/2f3c packet，对此 closeout 已解决。
- **这两页版式检查通过。** A22 新增行在页内正常换行，表头、分栏、表底线与下方 A23/正文不重叠或裁切；§4.3 新 H 说明正常排版，Tables 1/2 与正文间距可读。未借本次两页核验宣称已重新检查 closeout 全部页面或编译日志。

本 delta 不重跑模型、不追加科学实验，也不重跑未改变的 numerical evidence verifier。上文对于 raw/source/omitted-binary/absolute-time 的实际覆盖限制仍成立，novelty/impact 与成本支线凝聚的残余实质判断保持不变。Table 1 仍使用 “H tapes” 的小项表达建议不影响本次两项修正通过。
