# CLARITY_INITIAL — 首次独立 whole-paper 内部模拟评阅

本评阅仅针对 `review_packet_initial/` 的固定 v0.10.0 packet；未读取 packet 外的稿件、既有评阅、prompt、工作记录或其他评阅者意见。这是内部模拟判断，不是真实 MLSys 会议评阅，不是接受概率。阅读、渲染与证据重算均离线 CPU 完成，没有运行模型或增加实验。

## 固定对象、覆盖与验证边界

先读取 SHA256SUMS.json，实际重算四项 SHA-256 均匹配：

| 对象 | SHA-256 |
|---|---|
| manuscript-v0.10.0.pdf | c089271735661bce0ea8a89fcf206531c9dbb928d9cfe869f78a0677bc6bb8e8 |
| appendix-v0.10.0.pdf | bd143c90cf8dbe743db7717f13d81db8cbbb256875d4c3659d18d5f6e0486310 |
| INDEX.md | 8d9dbc7c885d8c2606bab34491f0f486e3a824410f4f35e8978b90a1d026207c |
| anonymous-intervention-evidence-v0.10.0.zip | b74629942f65677ce3a0e25f9fefbcde55ec3238cafb4b8917dce89eceb80427 |

文字覆盖：主稿全部 12 页（10 页正文、2 页参考文献）、附录全部 23 页，包含 Section T 与 A27/A28 全任务表。可视覆盖：所有页面的整页缩略渲染；另以较高分辨率检查主稿 p3、p5、p6、p7、p9（Figures 1–3、Tables 1–3/5）及附录 p11、p19。缩略浏览用于整体版式检查，不能等同于所有小字都逐像素放大核对。

读取 INDEX、ZIP 的 README/验证程序；在临时目录运行 `python -B verify_v010.py`，退出码 0，统一完整数组比较、历史包基础投影及 v090 扩展均 PASS。统一导出为 1005 arrays、67 task units：B570 24、RTX HumanEval 19、RTX MBPP 24，每任务三次、五条件；预测前后均匹配，paired transition 数与正文一致。验证程序的成功验证的是所交付数组/历史记录的算术与内部一致性。

未独立验证：原生模型推理，未交付 weights/binaries/driver 的实际字节，原始绝对实验时间，完整原始 intervention 日志与状态移交字节、源码到导出的全部映射，opaque sampler 字节一致性，功能性代码正确性，以及参考文献原文的真实性/优先权。packet 中所述 author-side raw audit 的 B570 PASS、RTX QUALIFIED_PASS 是作者报告；我没有把它当作自己已重做的 raw audit。为遵守封闭 packet 评阅未上网查询文献。

## 我理解的主张

论文研究的是：预先冻结的可执行执行路径描述，能否预测某个具体原生 speculative decoding 配置在受控改变前后的**完整 generated-ID 数组及 endpoint**。预测匹配 Pj=Nj、对指定 greedy reference 的兼容 Nj=R、以及路径实际成本是不同问题。这里的“完整”不意味着全部 logits、内部状态或执行事件，也不是 HumanEval pass@k。

两条 intervention 证据不是一个可跨硬件迁移的 predictor。B570 的 target-only、无 draft/proposal 描述，在已暴露的 24 任务上预测 baseline 及 target-prefill UB1→UB128 加 first-pending sample/state handoff 后的 native 路径；四个 diagnostic mismatch 全恢复，20 controls 无新偏离，reference match 从 20/24 到 24/24。RTX 描述使用自身 proposal/target workers、共享 pinned numerical routines，在 target-prefill/draft UB2 与 caller grouping 固定时改 target-continuation UB2→UB1；19 exposed HumanEval 与 24 exposure-audited MBPP 的前后输出均预测正确。但是 HumanEval /15 恢复、/25 新偏离、/18 持续偏离，MBPP /463、/304 持续偏离；reference 总匹配保持 39/43，不满足预定恢复且无新回归目标。/304 输出发生改变，因此“持续不匹配”不能当作输出 no-op。

独立历史成本证据说明：RTX qualified serialization 的 matched post-prefill speedup 为 0.677，358H 在固定 target work/progress 条件下去掉 draft/residual 的 prompt-GM ceilings 为 0.8372/0.8448，M4 Guard 虽胜 target-only，却比 Always-Spec 慢 2.71%。这些成本不是新 interventions 的性能结果。主张是有限配置下的 prospective intervention-prediction validation 及由此区分的工程决策；没有新 decoder、通用 repair、唯一 stage cause、生产性能收益或更优 adaptive policy。

## Strengths

1. **核心比较被正确拆开且贯穿全文。** Abstract、§2.1、Table 1、§4、§7、§9–10 对 prediction/native 与 native/reference 不混用；三重复也没有伪装成独立任务。RTX 恢复目标失败被保留为失败，没有以预测通过重定义 repair success。这种一致性是论文最扎实的优点。
2. **完整输出而非 first mismatch/common prefix 提供真实信息。** §4.3 与 Appendix T/A28 的 /304、/18、/463 区别清楚；Appendix S/A25 显示 target-only UB2 失败并不总等于整个后缀改变（/25 reconverges）。这比只报告 gate fail 更有诊断内容。匿名导出使这些有限比较可重算。
3. **Figure 2 是有效主图。** task-level match/mismatch 的符号和恢复/新偏离方向直接表达 paired cancellation，分开 HumanEval/MBPP，标出 task 与 array 分母；该图支持正文而没有把重复数组包装成样本量。
4. **成本论证守住测量边界。** §5.2/Eq.3 同时区分 pooled totals 与原 prompt estimator；Figure 3 明确 replay+proposal 不可分离。§6/Table 4 承认 Guard/Always 是 post-study secondary，并给出 fixed-mode oracle 的小机会空间。§9 集中说明成本不与新 interventions 混合。
5. **英文总体可理解，技术审慎。** 没有把可复现的 mismatch 说成模型功能错误，也不把数值敏感性升级为已定位 kernel bug。模型、cohort、cap/EOG 与 comparator 的界限有实质依据。

## Weaknesses：全文连贯、方法可读性与贡献强度

- **最大疑问是中心贡献能给研究者什么新的能力。** §1 将“冻结完整预测+受控 native 比较”列为贡献，§8/A26 承认数值路径变化、determinism、correctness gating 已有先例。B570 删除 draft 的 reproducer 是明确的简化；RTX 的 predictor 则保留 proposal feedback、target decision 和共享数值实现。前后 full-array 匹配值得验证，但主稿尚未说明这种重建相对直接运行 candidate 或现有 replay/forensics 工作，减少了什么搜索/实现负担，或排除了什么此前无法排除的描述。共享 routines 不自动使结果成为抄答案；我也不要求独立数值实现。但“不是抄答案”和“具有足够新的系统贡献”是两道判断。§7/Table 5 给出的不少决策（不兼容则拒绝、兼容但更慢则拒绝）依靠普通 gate/timer 本就能作出。
- **主稿先给结果，执行描述却很难操作性理解。** §2.2/§4.1 与 Table 1 给了输入边界，缺少一份紧凑算法/执行流程说明：B570 T1 如何生成 prefill 改变后的 target-only 序列；RTX workers 如何从自身反馈形成 proposals 并计算 correction/bonus/rollback；predictor 与 native 究竟哪些 orchestration 相同、哪些不同。关键本地计算/allowlist 示例在 Appendix N.1/S.3/A24，新的 intervention contract 又到 T。读者能复述结论，却不易仅凭主稿复述方法。术语“intervention-prediction closure”更像结果命名，未帮助解释为什么闭合有用。
- **篇幅围绕多个年代/目的不同的研究切换，冲淡标题承诺。** §4 约两页，§5–6 的 RTX/358H/M4 cost 与 guard 占据大量篇幅，但不是预测 interventions 的 measured consequence。§7 正确交代这点；科学上避免误混，叙事上却显得两篇内容连接在一起。§3 一开始就堆 OS build、审计、stop rules、timing estimator、energy boundaries，理解中心问题前就要求读者管理许多 campaign。历史细节可继续保留，但不必在第一遍阅读路径中如此突出。
- **campaign 指代与符号存在局部绊脚点。** §5.1 “V4 B uses A’s 19 tasks”在主稿此前没有直观定义 A/B；p5 的 G0/H arrays 未在附近定义，读者需要追到附录。历史 B570 H1、RTX H2 与新 P0/P1 的多种命名映射虽在 T 解释，却增加阅读成本。Appendix A22 的 study map 未包括两项当前主结果，而新的干预被置于附录末端 T，地图易被误读为当前论文的完整 map。
- **有一处明确图形排版错误。** 主稿 Figure 1（p3）下方左侧“Does the description forecast this path?”与中间“Restored, persistent or new deviation”文字横向重叠。它恰好是全篇决策逻辑图，应修正列宽/字体/换行。Figure 2/3 与 Table 1/5 可读，无需笼统重画全部图。
- **英文的问题主要是过密，而非语法。** Abstract 同时容纳两干预、三成本支线和多重免责边界；反复出现 complete/frozen/native/controlled/qualified 等定语。相同“不意味着”的限制出现在 §1、§3、§4、§7、§8、§9、§10。集中保留必要 caveats、在结果段优先写观察，会提升信息密度。p3/§3.3 的“offline review/author packet”叙述，以及 reviewer-requested、版本/repair 历史，让论文偶尔像证据交付说明。证据目录和 provenance audit 应有明确入口，而不必成为主稿的叙事主语。
- **可审计性不是完全原始可复现性。** current ZIP 强于仅给表格，但它并不让本评阅独立检查所有 handoff、occupancy、ordering 与 runtime source。正文已诚实限定；应再把“本 packet 可重算的证据”和“另有作者侧 raw 审计的证据”一目了然地分开，避免读者把 §3.1 的完整 raw review 当成现有小 ZIP 的功能。

## 影响接受的前三 blocker（按优先级）

| 优先级 | 分类 | Blocker 与具体依据 | 最有价值的解决方向 |
|---|---|---|---|
| 1 | **fundamental-novelty-impact** | §1/§7/§8 的中心增量尚未充分建立。B570 的 draft-free simplification 有明确价值；RTX 在共享 numerics 上复现较完整 native 决策过程，尚缺相对普通 replay、candidate run 与 gate 的具体收益/新知识。完整预测的可靠性不是该问题的自动答案。 | 用一个实际研究/调试任务说明“采用这个描述后能少做/区分什么”，并与最近工作逐项比较方法输出与能力。可先用已留存 records 建立具体差异；若主张节省工程时间/成本，则该新增主张需要新证据。扩 cohort 本身不解决贡献问题。 |
| 2 | **expression** | 主稿不足以操作性解释两个 frozen programs，方法核心散落于 N.1、S、T；Figure 1 重叠；A/B/G0/H 指代与缺干预项的 A22 study map 增加负担。读者看见结果但难以理解实验真正测试了哪个程序。 | 主稿加入紧凑算法或执行序列及一条本地 decision 示例；定义哪些 numerical routines 共享、哪些 API orchestration 独立；统一当前 study map/符号；修图并将旧名称留在附录映射。无需新模型实验。 |
| 3 | **existing-evidence-analysis** | §5–6 的丰富 negative cost results 与 §4 的 intervention 预测未形成足够紧密的共同分析。Table 5 各支线多是独立 gate/cost 决策，主稿大篇幅却没有证明“预测信息”在这些 cost 决策中实际增加什么。 | 重新按中心问题筛选现有证据，明确哪一项支持预测能力、哪一项仅支持独立成本边界。优先呈现 B570 简化与 RTX 具体被排除的简化，把详细 guard、historical cost/energy 与 estimator 历史压到附录；或明确将稿件定位为两类独立问题的经验研究，降低“统一方法”预期。 |

以上不是预设 stage factorial 要求，也不是把 unique-cause identification 当作当前主张必须满足的条件。我没有发现一个必须先补全所有 stage 组合才能评阅现有结果的问题。

## 评分与 confidence

**内部 3/5，borderline。** 有限结论可核、paired 行为有信息、失败呈现诚实，明显高于仅报告某些硬件慢/不一致的普通测量报告；但作为完整系统论文，方法的主稿解释、两类证据的凝聚及中心研究增量仍不足以使我给 weak accept。若只修英语与 Figure 1，评分不会自然升到 4；若能够利用现有 evidence 展示 concrete reproducer simplification/decision value，并显著压缩旁支，接受理由会更有力。无新 decoder/无生产修复不构成拒稿理由，贡献可来自经验验证；当前疑问是经验验证的新增能力是否足够清楚且重要。

**Confidence：4/5（对本文主张和内部证据一致性的判断）；对外部 novelty priority 为中等。** 我读完固定主稿/附录、可视检查关键图、运行了作者交付的离线 checker，能较可靠地区分它做了什么和没做什么；但没有运行原生 inference、重做 raw provenance audit 或核查参考文献原文。因此此 confidence 不应解释为完整外部复现或真实会议评分的确定性。

## 修改优先级与追加实验的价值

最先值得做的是把两个 predictor 讲成能执行、能比较的对象，并用一项现有具体案例说明减掉了什么或预测排除了什么；其次让 title/abstract/main study map 围绕同一贡献组织，降低 cost/guard 的主稿比重；再修 Figure 1、局部未定义符号和冗余 caveats。这些都是当前可立即处理的修订，不必先增加任务数。

若要追加证据，最能影响我判断的是**一个直接验证方法增量的预先固定使用场景**，例如与直接 native rerun/普通 replay 比较的可检验 reproduction/diagnostic 简化，或者清楚限定的工程收益；不能以增加数组总数代替该比较。如果稿件决定扩展为新 intervention 的 optimization claim，则需要对应 qualified native latency，但现有稿件没有作该性能主张，故不是目前的强制缺口。

下列追加通常不会改变我的判断：在已暴露任务上把三重复扩大到更多重复；多加几个仍共享相同实现、全部预测通过的任务但不解释能力差异；把 B570/RTX 结果汇成更大“成功率”；为 unchanged RTX aggregate 再加统计检验；再测 isolated draft throughput；盲目补齐所有 stage/factorial cells；增加 functional pass@k 但仍无法解释执行描述的增量。它们各可服务别的问题，却不能解决这里最重要的 novelty/impact 与全文组织问题。
