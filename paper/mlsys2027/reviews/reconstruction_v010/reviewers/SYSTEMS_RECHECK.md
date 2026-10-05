# Systems / novelty 实质修订复核

本次仅检查指定 `review_packet_final` 的唯一一轮修订，确认首评中可由现有证据和表达修复的问题，以及仍未解决的系统 novelty / impact。`SYSTEMS_INITIAL.md` 原样保留；不做新评分，原内部评级与 confidence 保留。未阅读其他评阅者意见、目录外工作记录或新提示材料，未执行模型或 GPU 推理。使用 PDF skill 的只读提取与渲染流程。

## Exact packet、哈希与覆盖

`SHA256SUMS.json` 所列 **25 个文件全部哈希匹配**；manifest 自身 SHA-256 为 `43e2e87b40bd99e78d61fecd282c80671009028304a195d499d595e14f89ee73`。实读 PDF 页数是主稿 12 页、附录 24 页。

| 对象 | 实际读取的 SHA-256 |
| --- | --- |
| `manuscript-v0.10.0.pdf` | `d4c0ffeefd60b4d0b3b0b3c480157a3f298f7045410720a4a4a2ded3846df1a9` |
| `appendix-v0.10.0.pdf` | `2f3c0743eff79f0531954a9a129f3e6b4518e4138f2380b601b03f8b8527dc1f` |
| `INDEX.md` | `455d7762d93136665437f8459db811ac3a6a93660a7f811fe807441887a64600` |
| `anonymous-intervention-evidence-v0.10.0.zip` | `ff9f4cfd873225a71afceae4a5fa8c01f385f4d7377296393e98912e77ad8ffe` |

重新阅读主稿 §§1–10 及附录 A–T 的正文与表格，重点核查 §2.2、§3.1、§4、§6–7、Table 5、附录 T.1/T.2 与 Tables A27/A28。渲染检查主稿第 2、3、9 页、附录第 19、20 页，核查修订方法说明、Figure 1、工程用途表与新增 endpoint 说明。

CPU-only `python -B verify_v010.py` 再次 PASS，包括完整正式比较、新增 B570 raw captures 和保留的历史重算。另将 final 与先前授权阅读的 initial 匿名 ZIP 直接比较：**1005 条正式记录的 task/condition/rep 键、IDs 和 endpoint 完全相同；DERIVED.json 与 historical-v0.9.0.zip 字节不变**。这支持此次是说明与证据导出的修订，不是改变正式科学结果。

对新增 `author-controls` 做有限只读核查：检查 COVERAGE 与 raw/source manifest，静态阅读 RTX `execution.py` 和 `worker.cpp` 的 round orchestration、allowlist、prefill/pending handoff 与 target decision 片段。选定 RTX tar 的 **262 个文件**和 capture manifest 的 exact file set、SHA-256、bytes 全部一致；**25 个 first-rep result**与正式 neutral arrays/endpoint 一致。其中 **10 个 H 条件**从 R-wire response 的 committed IDs 重建一致，**10 个 N 条件**从 first_pending + verify_decision sampled IDs、按第一个 inclusive EOS 选择重建一致；其余 **5 个 R 条件只检查 result 对正式数组**，未重做 reference raw-log parser。selected native continuation 的 attn_norm occupancy 观察为 N0 `{1,2}`、N1 `{1}`，与附录的限定叙述相符。

此范围不是全 15,192-file archive 或全 645 RTX units 的独立重建。packet 的完整远端 audit coverage 是所供审计记录，本人没有执行那个完整审计。静态源码、selected captures 与哈希增加可审查性，不证明 omitted weights/runtime binaries 的真实字节、adversarial file isolation、opaque sampler byte equality 或独立可信绝对时间。没有把 selected subset 的通过外推成完整 raw-audit 再执行，也没有为复核再次检索文献。

## 可由现有证据修复的问题：复核结果

| 首评问题 | 修订中的对应内容 | 本次判断 |
| --- | --- | --- |
| 描述的操作方法隐藏在 provenance/history 中，B570 与 RTX 的“预测”容易混读 | 主稿 §2.2 增加 prefill/first sample/state、round proposal/verification/commit/reconcile；附录 T.1 说明两个程序的构建与 changed-context boundary；明确 manually constructed study-specific programs | **基本解决其可审查性和表达部分。** 现在能理解共享什么、删除什么、在哪个边界改变配置，以及 target decision 如何本地生成。无需为补一个通用 automatic extraction 方法继续要求实验，因为稿件明确没有这项主张。 |
| B570 的结构简化与 RTX 的完整数值再执行未清楚区分 | T.1 和 §7 明确 B570 删除 draft，RTX 保留 live proposal feedback 与 shared numerical routines，且不声称 numerical independence/execution compression 或 debugging savings | **解决过宽工程解释的风险。** B570 的 draft-free reproducer 是真实结构简化；RTX 是另行编排的数值再执行等价性检验。较窄定位更准确，是否足够新颖仍是独立实质问题。 |
| gate 与完整轨迹信息对拒绝候选的作用混杂 | §7、T.1 明确 ordinary reference gate 已足以 reject RTX recovery candidate；描述额外给出完整 changed trajectory 与 reproduction contract | **解决。** 新稿不再需要把“预测完整数组”说成拒绝错误候选的必要条件。它实际新增的描述信息也更清楚。 |
| 缺少发生行为改变的具体预测例子 | T.1 用 MBPP/304：index 33 baseline 488、intervention 481，两个 47-ID EOS 数组均完整匹配 native，同时都偏离 reference | **解决例子展示问题。** 正式数组及该 first-rep 原始 subset 均支持例子。这展示 prospective trajectory forecast，未新增 held-out 行为改变样本或工程节约证据。 |
| 成本章节可能被当作新干预的成本闭环 | §5.1、§7 与 Table 5 标识 RTX historical cost，明确 timing studies 不测量新 intervention；M4/358H 保留各自成本边界 | **解决证据归属和措辞问题。** 各局部优化拒绝结论仍有意义；这些结果不应被拿来支持新 predictor 的性能收益。 |
| 正文细节挤压核心方法，M4 控制与主线联系较弱 | §6.1 压缩构建说明，附录 T.2 保留完整 construction/timer boundary；主稿 §6.2/Table 4 保留 split、gate、held-out protocol、prompt-median estimator、bootstrap、结果和 oracle 限制 | **排布有改善，未发现借移动文本删去失败或更换估计量。** M4 与 intervention prediction 的实质联系仍较弱，但现在更明确是独立工程决策证据。 |
| Figure 1 底部列说明实际重叠 | 主稿第 3 页新渲染 | **已修复。** 三种判断分列可读，未再发生原重叠。 |

首评前三 blocker 中第 2 项 `existing-evidence-analysis`，在“程序做什么、怎样变成条件对应描述、结构 simplification 与 numerical reexecution 如何区分”的核心阅读障碍上，可视为**基本解决**。当前 T.1 是详细步骤叙述而非独立伪代码，但已有足够操作信息支持这轮 limited recheck；我不再将“没有单独伪代码框”作为接受障碍。没有形成一般描述提取方法，是修订后明确的贡献边界，其影响归入 novelty / impact。

## CAP128 与 raw suffix 的专项确认

§3.1、附录 T.1、Tables A27/A28 现在清楚区分：正式 equality 比较 **合同规定的完整 128 IDs + CAP128 endpoint**；native final round 中额外 committed post-cap IDs 独立保留，不参与正式 equality 或 output no-op。本文的“complete”应按这个 endpoint contract 阅读，不能理解为所有 raw committed native IDs 也与 predictor 相同。

直接重算新增的 144 条 B570 untruncated native units，唯一 task/condition/repetition 键完整；每条前 128 IDs 等于正式 contract array，原始长度 128–130，差值与 raw_overshoot 一致。

| 条件 | raw len 128 的记录数 | raw len 129 的记录数 | raw len 130 的记录数 | post-cap ID 总数 |
| --- | ---: | ---: | ---: | ---: |
| N0 | 33 | 18 | 21 | 60 |
| N1 | 33 | 15 | 24 | 63 |

所以首评中“1005 条导出 overshoot 字段为 0”的观察仅描述 initial endpoint-bounded export，不能被解释为 native 没有 overshoot；本复核保留首次报告，同时补充此准确边界。此次澄清没有改变 72/72 prediction/native equality、60/72 → 72/72 reference equality 或 20 个控制任务在指定 endpoint 内的 output no-op。新增 raw 后缀不能被当作预测额外成功的 IDs，也无需为已冻结的 128-ID contract 改写正式分母。

## 剩余 substantive blockers

1. **fundamental-novelty-impact：仍保留，为最主要障碍。** 修订现在更坦诚地将 RTX 定位为保留共享 numerical execution 的候选 description validation。其 complete trajectory 信息确实超出 binary gate，但稿件仍没有展示这项较昂贵的再执行，相对于直接 native replay、gate 或状态跟踪，产生了多大的新可迁移系统知识或实用能力。B570 的 draft-free 简化与 exposed-cohort restoration 更有辨别力，但两个手工程序还没有组成可用于新 runtime 的方法或原则。修订成功说明了贡献“是什么”，尚未提供更多证据说明其 whole-paper 分量“为什么足够”。这是 impact 判断，不是认为 RTX 正确预测逻辑循环、复制 future answer 或其 failed repair 否定预测主张。
2. **new-evidence：新的有意义路径改变上的外推仍有限。** B570 正面恢复仍是已暴露的四个诊断任务与 20 个控制；旧 reserved predictor 验证不能变成新 intervention 的 held-out 验证。RTX 新 MBPP cohort 中仅 /304 的 N0/N1 array 改变，且只是一个位置；追加的 worked example 与 raw subset增强可检查性，没有增加新的行为改变案例。若要扩大系统贡献，仍需要针对具体用途的独立、事先冻结检验，而非增加旧任务重复。此要求不包含特定 stage/factorial、唯一 numerical cause、跨设备统一修复器或保证所有任务恢复。
3. **whole-paper coherence / engineering value：改善但仍是 impact 限制。** RTX historical cost、358H budgets、M4 Guard 负结果各自支持限定工程决定。稿件已清楚标为独立证据，因此没有“拿旧成本冒充新干预收益”的未解决问题；但它们也仍不能为 prediction description 增加已测量的资源压缩、调试节约或候选选择优势。358H 的 conditional ceilings 依然是最有用的可复算优化预算；它们的价值不等于核心描述方法已经实现优化或获得通用因果解释。

不再保留 Figure 1 overlap、gate 作用混淆、CAP128/raw capture 含糊、B570 与 RTX 执行缩减混读，或方法 round 的基本操作不清，作为未解决问题。额外源码和 selected raw captures也实质减少了首评的可检查范围缺口；仍不可独立认证的 omitted assets/absolute time 属于已披露边界，不自动形成新拒绝理由。

## 本轮结论

这是有效的实质修订：现有 evidence 能修复的主要方法说明、证据归属、endpoint 和版面问题已得到处理，正式结果保持不变。原内部评级保留，不新增分数。剩余主要顾虑集中在 **novelty / impact 及有意义新路径改变的外推**，不会靠更完整的审计措辞、更多稳定重复或继续压缩同一组数据的 confidence interval 自动解决。


## Closeout hash / delta receipt（仅补记）

核对范围严格限于 `review_packet_closeout/` 的哈希、页数、两处遗漏修正和对应未变计数；没有重新开展 whole-paper review、重新评价 novelty / impact 或新增评分。`SHA256SUMS.json` 列出的三个文件全部 SHA256 验证通过：

| 文件 | 实测 SHA256 | 页数 |
|---|---|---:|
| manuscript-v0.10.0.pdf | `5433df69f8f091c41b604f9f02714c435672a06e0379a63d2dcb96db30500185` | 12 |
| appendix-v0.10.0.pdf | `ff1a69b1d425bf01108a59d7fb4de6d27e7e74b1b25d7849c33fd3d33715ac28` | 24 |
| DELTA.md | `28f6f8dbe017dd036a54bb360ebc31578db132e4e6eb5f8806440d2204810a2a` | — |

逐项核对 PDF 提取文本，并渲染检查主文物理第 5 页与 appendix 物理第 17 页：

- **Table A22 两项当前 intervention 已补列。** B570 prefill 列明 own reference、T0/T1 predictions 对 N0/N1 native、exposed 24×3、CAP128、paired outcomes、no timing；RTX continuation 列明 own reference、H0/H1 predictions 对 N0/N1 native、19×3 与 24×3、EOG/cap128、paired outcomes、no timing。旧 historical entries 保留。两行使研究概览与当前主线一致，不增加新实验或新性能结论。
- **§4.3 reused H 的身份已明确。** G0 说明是 75 个在 24 threads 新检查的 native arrays，加 45 个未变而复用的 **prediction-worker (H) arrays**，不是 120 个新 24-thread outputs。这消除了此处 H 与 historical text-path H 的潜在歧义；不改变原计数或因果归属边界。
- **相关结果计数保持原值。** 同页 Table 1 中 B570 两条件预测各 72/72，native/reference 为 60/72→72/72；RTX 旧 cohort 两条件预测各 57/57、新 cohort 各 72/72，native/reference 分别为 51/57→51/57、66/72→66/72。G0 75+45 的组成在本次仅澄清标签，未增加 observations。

Closeout 目录不另附 evidence ZIP；其 DELTA 声明沿用 `review_packet_final/` 的证据。我重新核对该目录的 `anonymous-intervention-evidence-v0.10.0.zip`，SHA256 仍为 `ff9f4cfd873225a71afceae4a5fa8c01f385f4d7377296393e98912e77ad8ffe`，与本报告此前审计版本一致。未重复解包或重跑 evidence verifier，未运行模型。本次确认两项遗漏修正和相关版面、哈希及计数一致；**以上 recheck 结论、remaining blockers 与原内部评级全部保留，不产生新评级。**
