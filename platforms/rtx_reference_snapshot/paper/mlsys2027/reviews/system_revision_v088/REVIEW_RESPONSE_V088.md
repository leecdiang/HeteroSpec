# v0.8.8 审稿回应与修订记录

本轮按已完成的 v0.8.7 六份固定成品审稿修订。旧报告、评分、PDF/ZIP 和原始实验保持原身份；以下是新版本的作者回应及针对性核验，不是重投票。

## 统一主线

新标题：**Predicting Execution Paths and Bounding Optimization in Speculative Decoding**。摘要、引言、贡献、结果和结论统一为 B570 完整轨迹预测 → RTX 同集指定候选判别 → matched qualification/cost → 358H/M4 支持性约束。主文先呈现新增科学问题和它改变的诊断选择；原历史时序与硬件库存保留在附录。

| 审稿请求 | 修订与证据 | 最终位置 |
|---|---|---|
| R1 P0-C：相对资格否决新增什么 | 明写资格是部署判断，预冻结预测额外判别执行描述；列“基本门已经知道 / 新证据 / 允许选择 / 固定前提” | §1、§4、§7；system_decisions_v088；GLOBAL_SYSTEM_READOUT_V088.md |
| R1/R5/R6：贡献顺序与大局 | 按统一主线重排结果与运行时章节，系统展望讨论执行描述、优化预算和控制机会 | 摘要、§1、§4–7、结论 |
| R2/R4/R5：UB2 与 replay 输入合同 | 紧凑表列 prompt/weights/proposals、自己计算的 history/decisions、共享例程；明确 UB 是 capacity，不认证实际 forward-trace 等价 | §2.2、Table 1；Appendix M/Q |
| R4：51/57 的交叉关系 | 主表列 /15 两者错，/18 仅 reference 错，/25 仅 UB2 错；replay 全部相等 | §4.3；trajectory table；Q first-ID 表 |
| R1：V4 绝对延迟 | 既有 171 QPC 记录导出 19 prompt-median 的 min/quartile/median/max，保留全部 57 prompt-condition medians；独立原端点复算 | §5.1；absolute table；Appendix Q；CSV/JSON |
| R3：CI 条件推断对象 | 经验 prompt-row 重采样，条件于曝光队列、观测中位数和固定配置；排除选择/总体/新会话覆盖 | §3.2、§5.1、Appendix Q |
| R4/R5/R6：因果和 transfer 术语 | 改为 prospective path prediction / sampled intervention / specified-candidate discrimination；不称同一预测器移植成功 | §1、§2、§4、Appendix J/M |
| R4：score 与 margin 相邻 | 主文同段展示 score absolute delta 中位数/p95/max 与两分区 margin min/median；标为 marginal descriptors，不是近边界或全程 null | §4.2；Appendix P |
| R2：最近先行工作 | 表列 sensitivity、deterministic construction、synchronization/cost forensics 与本稿预冻结完整 native-path 问题的区别；复核四篇原始论文 | §8 nearest-work table；原 references 不改 |
| R1/R2/R5：历史 inventory 与重复限制 | 主文移除 11-study 大库存及旧头条时序，保留重点问题/结果；精确研究映射和旧 M4/RTX/B570 时序进 R | §3–7；Appendix R |
| R4/R5：P/R 独立性与字母冲突 | Separate P/R orchestration 就近声明 shared numerical routines；主文不再用 P 指 prediction equality | §2、§4.3；trajectory table |
| R5：浮动与 caption | 表引用放在完整段落后，旧 0.646+CI 用不可分组保持；null speedup/CI 明确只指 blocked batched 行；新增表使用 ragged-right 排版 | §4.3、§5.1；表和逐页 QA |
| R1/R2/R6：附录历史定位/入口 | A9 旧 RTX 标 earlier two-path cost (30 prompts)；旧绝对时长标题标 earlier 30 prompts；full H2 digest 指向 A13 准确交叉引用；V4 入口在 Q | Appendix K/N/O/P/Q |
| R3：证据能力 | 区分 compact CPU 复算、full capsule raw logs/state controls、reported chronology；projection booleans 不是原 KV/sampler bytes | §3.3、Appendix O/Q |
| 保护 Figure 3 | 原 tex、PDF asset、textwidth inclusion、caption 完全保留，移动到 Appendix F 背景；未重画或缩放 | Appendix F；source-invariant receipt |
| 保护既有结论 | 所有原数组、估计/CI/seed、负结果、V3 terminal 状态、host amendment、旧验证器/宏/style/tag 不变 | byte/source invariants、CPU replay、远端 tree diff |

P0-C 的重要性反对意见被正面回应，但不能宣称完全消失：有限栈、共享数值例程和有限区别任务仍然存在。新稿未获得六份新评分，不能继承旧的弱接收计票。

## 核验与边界

本轮新做：post-study plan 和描述量导出；从 171 原 QPC 记录的独立实现核对；新匿名包两次 clean CPU 验证；改变分位数或 prompt median 并重算 manifest 的两个损坏样本仍被拒绝；两次独立 clean ZIP 编译；PDF 字体/匿名性/引用/页数检查；所有最终页面视觉检查。最终 hashes、页数和精确 source mapping 见 FINAL_ARTIFACT_MANIFEST_V088.json、REVISION_V088_QA.json、VISUAL_QA_V088.json。

复用：原九胶囊 native-log/QPC audit 和历史数值/runtime 关闭回执。未重下载九胶囊、未执行 GPU/模型、未重跑全部历史套件。Compact 包不能验证遗漏二进制、原绝对时间或未保留状态字节。内部 hardware-only PDF 是章节移除/引用证明，不能投稿。

修订核验结论：**Share with caveats**，即所检查范围内的有限结论与材料可审阅；贡献重要性和最终投稿判断仍保留。B570 本轮不补实验；更强 single-block 因果主张需要独立有界设计。Merge、公开 release 和会议提交仍未执行。
