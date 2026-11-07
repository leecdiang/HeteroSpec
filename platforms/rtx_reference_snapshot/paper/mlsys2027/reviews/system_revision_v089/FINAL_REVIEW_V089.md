# v0.8.9 修后复核与审稿意见闭环

本次为主代理的作者修订复核，依据固定 v0.8.7 审稿请求及 v0.8.8 成品逐项核对。它不是六名独立评审的新投票，也不继承旧版本分数。

## 复核结论

当前稿件最有价值的增量是预冻结完整非参考轨迹的可证伪预测，以及 RTX 同集指定候选的实际否证。资格判断和成本研究随后约束可采用的系统选择。358H 与 M4 提供固定前提下的优化预算及控制机会，不能累加为跨硬件普遍因果规律。

有限主张与现有材料相符；本次未识别到推翻中央结论的有效性错误。R1 的重要性反对意见仍成立为判断分歧：真正区分的任务少、数值例程共享、仪器化成本的部署外推有限。论证清楚和材料严密不保证跨过主轨门槛。

建议：交作者做最终科学判断和投稿材料确认。现有材料修订已完成；不为获得更好分数重复六人投票，不因“继续推进”自动合并、发布或提交。

## 本次发现并落实的遗漏

1. v0.8.8 正文与附录 J prose 已收紧措辞，但 A6 使用的旧版本表仍称 `primary mechanism-validation endpoint`。这是 R4 P1-1、R6-1 的具体遗漏。本次创建 `b570_prediction_commitment_v089.tex`，改为 `primary prospective path-prediction endpoint`。原 v083 表、完整 ledger、digest、时间和所有数值保持原字节；主文 scientific prose 不改。
2. A9 已标 earlier two-path 30-prompt cost，但表注还缺 R6-3 请求的 V4 就近入口。本次在新 `appendix_followups_v089.tex` 中指向 Section Q；其 A13 文档源码入口同时更新为实际 v0.8.9 ZIP。匿名 evidence 仍指向未改动的 v0.8.8 包。
3. 当前构建说明将 2027 规则称为 unpublished。现已查到官方 2027 CFP，明确沿用 2025 格式。更新当前说明，保留原 style bytes 和历史文档。见 [官方格式核对](VENUE_PRECHECK_20261003.md)。

## 旧审稿请求的最终落点

以下是主代理的落实判断，不代表原评审同意或重新评分。P0-C 的“已回应”不等于重要性争议已解决。

| 请求组 | 当前落点 | 复核判断 |
|---|---|---|
| R1 P0-C；R1 P1-1；R6-2 | §1、§4、§7；Table 6 将新增观察、允许决策、固定前提分开 | 已正面回应；主轨意义仍有分歧 |
| R1/R5/R6 贡献顺序 | 摘要、引言、结果、系统展望、结论均为 B570 → RTX 判别 → qualification/cost → 支持约束 | 已落实 |
| R2 P1-2；R4/R5 输入与 UB 假说 | §2.2、Table 1；UB capacity 与 actual forward history 区分，本地决策与 shared routines 并列 | 已落实；未保留的 trace 等价仍未知 |
| R4 P1-3 交叉失败 | Table 2 与 Appendix Q：/15 两者错、/18 仅 reference、/25 仅 UB2 | 已落实 |
| R1 P1-2 V4 绝对成本 | §5.1、Table 4、Q.5；171 原 QPC、19 prompt medians、57 条件 medians | 已落实；观测分布不是 CI |
| R3 P1 条件 bootstrap | §3.2、§5.1、Q.4：经验 prompt rows、已选 cohort/medians/config；排除总体与新会话保证 | 已落实；原估计、seed、CI 不变 |
| R4 P1-1；R6-1 因果/transfer/端点术语 | 正文已限定；v089 补齐 A6 的 prospective path-prediction endpoint | 遗漏已修复 |
| R4 P1-2 score/margin 尺度 | §4.2 同段列 delta 与 raw margin，明确 marginal descriptors、无 near-tie witness | 已落实 |
| R2 P1-1 最近先行工作 | §8、Table 7 区分敏感性、确定性构造、forensics、前瞻完整轨迹问题 | 已落实；仍不认证全球首次 |
| R1/R2/R5 历史库存和重复限制 | 核心结果在 §4–6；原 Figure 3 保留字节/geometry 并移 F，研究映射与旧时序在 R | 已落实 |
| R4 P2-1；R5 P/R 记号 | prediction equality 用文字；P 只指 draft worker，separate orchestration 与 shared routines 同处 | 已落实 |
| R5 P2 浮动/成本 caption | 引用置完整段后；旧 0.646 与 CI 不拆；null 明确仅指 blocked batching | 已落实；普通跨页/column continuation 不作错误 |
| R6-3 A9 研究身份与入口 | Earlier RTX two-path cost (30 prompts)；v089 caption 就近指向 Q | 补齐入口 |
| R2 P1-4；R5/R6-4 H2 入口 | O 明确指 A13 full capsule entry；A13 文档源码为 v089、科学 evidence 为 v088 | 已落实 |
| R3 P2 证据能力 | §3.3、O/Q 与 A13 区分 compact recomputation、full retained records、reported chronology | 已落实；projection 非原 KV/sampler bytes |
| R4 P2-2 host amendment | Q.2 明写 fan/host amendment，保留原 stop 与披露，不认证物理无影响 | 已落实，非重跑理由 |

## 数据与实验决定

本次没有新计算研究结果、变更样本、修改主要估计或运行模型。全局数据分析继续使用 [v0.8.8 全局读出](../system_revision_v088/GLOBAL_SYSTEM_READOUT_V088.md)。其 171 原 QPC 的独立描述量复算、两次 evidence CPU 验证和坏数据拒绝属于上轮已完成回执，本次核对其哈希后复用，不冒充重执行。

B570 保持 CLOSED。现有稿件没有将 persistent-UB128 continuation 的后续差异归因于一个 block，因此 single-block/common-policy 对照仍不是维持当前主张的必要项。只有作者明确改为追求更强单块因果贡献，才另设有界协议；不做 dense scan，不预设正结果。RTX/358H/M4 同样不重开。

## 成品与核验身份

新 main/appendix/internal proof/source ZIP 为 v0.8.9；实际科学 evidence 为原 v0.8.8 匿名包。原 v0.8.7/v0.8.8 PDF、ZIP、审稿报告、分析/验证器及科学 freeze tag 保留。

新检查和复用检查以 [FINAL_ARTIFACT_MANIFEST_V089.json](../../evidence/FINAL_ARTIFACT_MANIFEST_V089.json)、[REVIEW_CLOSEOUT_V089_QA.json](../../evidence/REVIEW_CLOSEOUT_V089_QA.json)、[VISUAL_QA_V089.json](../../evidence/VISUAL_QA_V089.json) 为准。只在当前源码 ZIP 重新编译和 final-hash 视觉核对通过后交付。精确远端身份见 [DELIVERY_V089.md](../../evidence/DELIVERY_V089.md)。
