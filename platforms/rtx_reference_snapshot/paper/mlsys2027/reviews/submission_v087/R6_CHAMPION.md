# R6 独立审稿：最强公平接受理由及其压力测试

**版本：v0.8.7。评分：4/6（弱接收）。置信度：4/5。**

本评审将论文视为有明确边界的实证系统测量与诊断论文。结论不是“已知数值敏感性再次发生”，而是：在固定路径上，什么执行描述足以预先预测完整输出；预测成功是否满足指定参考的兼容性；兼容路径是否在同一研究的完整计时边界内有利可图。这三个问题的有限答案有科学与工程增量。我支持弱接收，但不把严密的协议记录本身当作足够的新颖性，也不把程序复现当成独立数值实现。

## 阅读范围与独立性

- 完整阅读主文 12 个物理 PDF 页（正文 1–10，参考文献 11–12）和附录 14 个物理 PDF 页，以及提供的文字阅读辅助；对辅助文本末尾遗漏的末句，以原 PDF 提取文本和渲染页补齐。
- 实际查看的主文渲染页：1、3、4、5、6、7、8、9、10、12。覆盖 Table 1–5、Figure 1–4、摘要及结论。
- 实际查看的附录渲染页：2、3、4、5、6、7、8、9、10、11、12、13、14。覆盖 Table A1–A18、B570 冻结记录、fork 控制、RTX proposal/replay 输入描述、V3 失败及 V4 计时与修订记录。
- 两份 PDF 的 SHA-256 与 FIXED_PACKET.json 一致。未阅读旧版本审稿、既有分数、作者交接报告、其他评审或输入目录之外的科学材料；未编辑论文；未运行模型、离线证据包或外部文献核验。下文的文献增量判断只依据主文 §8 的处理，不声称已独立验证相关文献事实。
- REVIEW_RUBRIC.md 的标题和附录页数仍写 v0.8.6 / 12 页；本次按固定包指定的 v0.8.7 原 PDF、实际 14 页附录评审，不把这项包说明差异算作论文科学缺陷。

## 我理解的贡献与最强接受理由

**最强科学结果是 B570 的前瞻完整轨迹预测，RTX 同集合反例使其边界更有信息。** B570 在暴露的发现集上选择无 draft 的 target-only UB1，然后分别冻结假设与 72 条完整预测数组，再执行 24 个保留 prompt 的三次 live 重复。预测与 live 为 72/72，UB128 参考与同一 live 为 60/72；四个参考分歧 prompt 的 12 次运行及后续整条 capped 序列均被正确预测（主文 p5 §5.2、Figure 2；附录 p5–7 §J、Table A6–A7）。这不只是看见某个 argmax 变了再解释：任何保留数组中更晚的一个错误 ID 都会否定冻结预测。四条非参考轨迹也排除了“只复制参考结果”的解释。

这个结果没有发现新的数值现象，也不证明 UB1 是唯一或最小描述；它给出了一个实测充分性命题：在这一 B570 路径和保留集合上，无须 live draft/proposal 输入的 target-only UB1 程序足以预测 capped live 输出。该命题可能因为 proposal-conditioned 计算、历史状态、rollback 或采样实现差异而失败，故不是仅凭贪心算法定义即可得到的无条件恒等式。共享数值代码降低了机制独立性，但并不取消预先固定完整数组的可证伪性。

RTX V4 在同一 19 个剩余、经过暴露审计的 prompt 上比较指定候选：target-only UB2 为 51/57，H2 与 fresh R ONLY 各为 57/57；参考 UB1 也是 51/57，但失败 prompt 不同（主文 p6 §5.3、Table 3；附录 p13 §Q.3、Table A18）。这使“只用 target micro-batch 描述就足够”不再是从 B570 向其他路径顺推的故事：该指定 UB2 候选在 RTX 的完整集合上被实际否定。replay 的成功是 proposal-conditioned 执行的有限经验充分性，不能推出 proposal/history 对所有 target-only 描述都必要。

**最强系统结果是同研究内把资格与成本联合判断。** RTX V4 B 在同一 19 个 prompt 上新执行三路径的 171 次运行，用同一 timer executable 和平衡顺序：batching 51/57 不满足参考 ID 合同；serialization 57/57 满足合同，但 target/serialized 为 0.677 [0.662, 0.692]、0/19 prompt 更快（主文 p7 §5.4、Table 4；附录 p13 §Q.4）。这不借用历史资格授权另一批 timing，因此能支持两个不同的实际筛选决定。358H 的固定进度、固定 target work 上界，以及 M4 Guard 相对固定 speculation 的负结果，进一步说明改善局部环节或增加控制活动不自动产生可接受的收益（主文 p7–9 §5.5、§7；附录 p11 §P.2–P.3）。

## 对接受理由的压力测试

1. **B570 的发现可能是对同路径常识的严格验证，而不是深层解释。** UB1 predictor 与 serialized live 共享 target 数值例程，且只有 24 个独立 prompt、四个参考分歧例子；三次重复不能将有效多样性扩成 72 个独立任务。其增量在预先给出完整轨迹且成功预测非参考后续，而不在数值敏感性本身。若评审认为这一有限描述的确认仍不足主会重要性，可以合理弱拒；不能据此称 72/72 的有限结果无效。
2. **RTX replay 与 live 很接近。** H2 使用 draft 构造自身反馈依赖的 tape，R ONLY 用共享 llama.cpp/GGML/CUDA 例程逐项计算；它没有得到未来 live 输出，但它不是独立数值求解器（主文 p6 §5.3；附录 p7–10 §M、§N.1，p12 §Q.2）。这支持编排和状态输入层面的重现，不证明一个新的不可约历史机制。V4 的实际增量主要来自同集合 UB2 反例，而不来自将 57/57 包装成机制唯一性。
3. **计时的外推能力有限。** RTX timer 包含相关 logging/response，condition-dependent logging 未被证明抵消；空 clock-hook 检查只测 clock-call 开销（主文 p7 §5.4；附录 p9 §N，p12 §P.4，p13 §Q.4）。因此 0.677 有效地描述记录中的 instrumented post-prefill request，不能判定 logging-free 部署也一定较慢。它仍能否定“这个已测、已合格实现就是延迟优化”，但工程意义比生产优化结论窄。
4. **其他平台主要是支持性约束，不能累加成普遍法则。** 358H 的零 draft 上界是已知 accounting identity 的有用实例化，M4 Guard 的失败是一个固定策略、固定工作负载的结果；历史 M4/RTX/B570 text-path timing 不被后来的 direct-ID gate 追认。不同 reference、backend、OS、量化与 timer 边界妨碍平台因果排名（主文 p3 §3.1–3.3，p5 Table 2，p10 §9）。接受的理由应是有限预测区分和资格/成本决策，不是“四个平台”数量本身。
5. **前瞻顺序的证据有审查边界。** PDF 提供冻结角色、摘要和 reported host/server ordering；摘要 digest 能绑定内容，不能自行证明外部绝对时间。匿名数组可供检查，但我未执行其 verifier，也不能据 PDF 宣称已证明原始进程 chronology 或不存在所有未记录暴露（主文 p3 §3.3；附录 p6 §J，p8 §M，p11 Table A13，p13–14 §Q）。论文已经承认这些限制，没有发现当前顺序叙述与所示材料冲突的证据。

这些压力把我从“接收”限制为“弱接收”，但没有使我要求新算法、唯一 kernel 原因、跨栈成功迁移或生产 benchmark 才能接受当前论文类型。

## 五个共同评价轴

| 评价轴 | 判断 | 关键证据与边界 |
|---|---|---|
| 1. 有限科学有效性 | 良好；未发现 P0-V | H/P/Q 比较对象、inclusive EOG/cap128、prompt 与重复单位、冻结候选均明确。B570 24 prompt 与 RTX V4 19 prompt 支持各自有限命题，不是总体成功率。fork 即时与持续后续政策分别报告。主文 p2 §2.1、p3 §3、p5–7 §5；附录 §J、§L、§Q。 |
| 2. 已知敏感性与完整成本之外的增量 | 有、但中等 | B570 的冻结非参考完整轨迹与 RTX 同集合指定候选反例超出回顾性 mismatch。既有理论 accounting、重复 slowdown 和 control 本身不是新贡献。主文 p5–7 §5–6，p9–10 §8。 |
| 3. 具体有界工程后果 | 明确，但不广泛外推 | P 成功仍不能批准 Q 失败路径；RTX batching 排除于指定参考替代，serialization 排除于已测 instrumented 延迟优化；358H draft-only 优化不足；M4 无理由以实测 Guard 替代 Always。主文 p7 §6、p9 §7.3。 |
| 4. 证据、输入、控制、顺序可检查性 | PDF 层面较好；未独立 artifact 认证 | 完整数组/endpoint 角色、tape allowlist、own-state 检查、R0/KV/clone、失败记录和 exact entries 有实质说明。共享例程、匿名 chronology、外部 binaries 与旧 raw trace 缺失的能力边界明确。附录 p6–10、p11 Table A13、p12–14 §Q。 |
| 5. 整合与可读性 | 可读，但研究命名与贡献聚焦仍可改善 | Table 1 非常有帮助；Figure 3 明确禁止 proxy/gate 配对。但 H1/H2、V2/V3/V4、两次 RTX cost 与多种 reference 使主线成本较高。下述现有材料修订能改善。 |

## 问题分级与具体请求

**P0-V：0。** 未发现已经演示、足以推翻当前中心有限主张的错误。

**P0-C：0（本评审不设接收阻断项）。** 重要性依然可合理争论；我将共享数值实现、少量条件化 prompt 和 instrumented timing 作为评分限制，而不是把它们误报为数据损坏或未完成既定实验。

| 编号 | 级别与定位 | 问题 | 精确请求 |
|---|---|---|---|
| R6-1 | P1；主文物理 p1 §1 “intervention and transfer”、p2 贡献列表 “causal and transfer limits”；附录 p5 §J、p6 Table A6 的 “mechanism-validation” | 概括词比实际最强推论宽。B570 fork 是另一集合的一处即时对照加持续后续政策；RTX 改换 UB、live 路径和参考，并未执行同一冻结 predictor 的成功跨栈迁移。“mechanism-validation”也容易让读者高估 predictor 成功的因果含义。详细正文已作限制，因此是概括修订，不是 P0-V。 | 将主文概括改成“sampled intervention and cross-stack candidate discrimination”之类准确描述；将附录相应 endpoint 命名为“prospective full-trajectory prediction/path-sufficiency validation”。保留 sampled checkpoint、persistent continuation、共享例程与非唯一性限制。无需识别 kernel。 |
| R6-2 | P1；主文物理 p1–2 贡献列表，p5–7 §5，p7 §6；p9–10 §8 | 新颖性最强处与实验协议细节竞争。读者需要从数处拼出：B570 成功是 descriptor sufficiency，RTX 失败是 specified candidate rejection，cost 决策另有 reference。多次重复“没有建立”的限定也压缩了这三个正面有限结论的空间。 | 用现有 Figure 2、Table 3–4 和 §6 内容，形成一个简短主线摘要：“冻结命题—可否定事件—观察—允许决策”。将完整轨迹前瞻预测和同集合反例作为科学增量，将资格/完整成本作为系统增量；历史四平台结果按支持性角色介绍。无需新增实验或扩大 scope。 |
| R6-3 | P2；附录物理 p8 Table A9 的 “RTX matched cost” 行，与主文 p7 §5.4、附录 p13 §Q.4 | Table A9 的泛称在 v0.8.7 中容易被读成新的三路径 V4；实际上该行是较早 30-prompt、两路径、90/90 成本研究。两者 sample/gate 不可混用。正文说明是正确的。 | 将该行标成 “Earlier RTX two-path cost (30 prompts)”；表注直接指向 V4 的 §Q.2/§Q.4。只修改研究身份标签。 |
| R6-4 | P2；附录物理 p10 §O 首段、p11 Table A13 | “H2 capsule’s SHA256 is its full filename digest above” 的位置指示不清，完整 filename 的明确表项实际在后页 Table A13；长 digest 与脚本路径断行也提高入口查找成本。 | 使用准确的 “Table A13 RTX full anonymous capsule entry” 交叉引用；将精确可复制入口集中于一处并保留 capability/limit 列。无需补成 PDF 内所有 raw arrays。 |

## Rubric A–E 的直接回答

**A. 最强结果比回顾性观察多了什么科学推论？**

它把“改变执行路径可能导致差异”推进为一个可以在保留输出到来之前失败的具体预测命题：B570 target-only UB1 对该路径的完整 capped 输出经验上充分，甚至对参考不一致的四个 prompt 也正确；RTX 同集合则否定预定义 target-only UB2 的全集合充分性。后者不是对全部 target-only 假设的反证，前者不是唯一因果说明。贡献是有限可预测性的实证区分，而不是新的数值敏感性事实（主文 p5–7 §5.2–§6；附录 p5–7 §J、p13 §Q.3）。

**B. 当前边界内能作哪些具体决定？**

- B570：不能以该 live 路径无损替代 UB128 参考；预测对了不改变 60/72 的资格失败。若需要诊断这个路径的 capped IDs，UB1 可以作本研究范围内验证过的 draft-free predictor。
- RTX：不能用这个 target-only UB2 候选替代完整 cohort 的 live 轨迹预测；不能将 batched 路径当作 UB1 参考兼容替代。合格 serialization 的已测 instrumented post-prefill latency 更高，没有这个已测实现的延迟优化理由；logging-free 部署另需测量。
- 358H：固定当前进度与 target work 时，仅降低 draft/replay 接口或 residual 不足达到总时间 parity；必须改变 bound 的固定量才可能越过它。未测 persistence 收益不从 bound 自动产生。
- M4：此 workload 上 Always 优于 Guard 的 aggregate latency；fallback 活动不是有益决定比例，离线两固定模式 oracle 几乎无选择空间也不等于所有动态策略无空间。

这些都是针对明确候选与参考的工程筛选，不是硬件排名、总体失败率或普遍调参法则（主文 p7 §6、p9 §7.3；附录 p11 §P.2–P.3、p13 §Q.4）。

**C. 对实际写下的主张，是否有逻辑上必要的新执行？**

**没有。** 未找到当前中心命题缺失的必要前提。它们分别诉诸保留完整数组 equality、指定候选 finite-cohort failure、同研究的 direct-ID gate 与 instrumented latency、固定 totals 的 accounting bound、M4 固定策略比较。论文已经明确排除 history necessity、单 block 延迟因果、独立数值实现、portable mechanism 和部署收益。不能把这些已排除的强命题反过来作为本版本必须新执行的要求。

遵循固定包的指示，风扇/host-policy 修订不作为否决理由或重跑依据。附录物理 p13 §Q.2 的原 stop 与 amendment 披露应保留；我没有独立证明其物理影响为零，也不作这种宣称。

**D. 能否仅靠现有材料修订满足请求？重要性是否仍需判断？**

可以。R6-1–4 都是术语、主线和入口修订；已有数组摘要、Table A18、输入流说明、资格/成本表足以支持当前推论。将它们整理好能让有限新知识更直接，但不会增加 prompt 多样性、独立数值例程或 logging-free timing，因此重要性仍是主会判断，不应由“完成全部审计”机械推出接受。

**E. 本版有哪些阅读摩擦或支持不足的措辞？**

主要是主文概括的 “transfer/causal limits”、附录 “mechanism-validation” 可能被读成更强推论；以及 Table A9 的 generic cost 名称和 §O 的入口指向。H1/H2、V2/V3/V4 和旧/新 qualification、旧/新 timing 的叙述负担较高。Figure 2、Figure 3、Table 1 与 §9 有效防止实质混淆；我没有发现从 P 推 Q、从 fork 后续推即时因果、从 zero-draft bound 推已测 persistence、从 57/57 replay 推必要性，或从 0.677 推生产 throughput 的中心越界。

## 实验必要性与可选扩展

| 项目 | 本版是否必要 | 若以后执行，支持何种更强结论 |
|---|---|---|
| 重跑 B570/RTX 当前研究 | 否；没有识别出必须通过重跑修补的中心失效前提 | 独立会话/主机执行可增加重复性证据，不能自动提供 universal mechanism。 |
| 消除或测量 logging 的 RTX 延迟影响 | 对当前 instrumented-boundary 主张否 | 对 uninstrumented deployment latency 的外推需要新的匹配测量或充分开销界；不能由 clock-call probe 替代。 |
| 同一 checkpoint 单 block 改变后恢复原后续政策 | 否 | 将即时 block 对更晚输出的效果与持续 UB128 政策分开，才可支持单 block 延迟因果解释。 |
| 系统性消融 proposal/history 或设计其他 target-only predictors | 否 | 有助于识别更小 sufficient state；单个 UB2 失败本身不能证明 history 必要。 |
| 新模型、backend、独立数值实现或更多 prompt | 否 | 改善外推、独立机制验证与重要性；是扩展当前有限结果，不是补齐其已写下的证明义务。 |
| 新 Guard、persistence 性能/energy、production throughput | 否 | 检验新的优化主张；本版没有宣称这些正面收益。 |

## 最强接受与拒绝立场

**最强接受立场。** 论文提供一条完整且可被失败推翻的实证链：前瞻预测可以正确覆盖非参考完整轨迹；在另一明确路径上，一个预定义 target-only 描述被同集合 replay 对照否定；预测性、参考资格和收益互不蕴含，且 matched RTX cost 将最后两者联合测试。负结果改变了实际候选选择，358H 与 M4 进一步给出固定假设内的优化优先级与反例。有限经验知识不必须以新算法或唯一机制形式出现；这个组合足以达到边缘主会贡献。

**最强拒绝立场。** 即使所有有限结果有效，主要 predictor/replay 仍是共享例程上非常接近 live 路径的实现；新知识集中在一个 Qwen 配对和 24/19 个条件化代码 prompt。相关工作按本文描述已经覆盖数值路径变化、完整成本、slowdown 和自适应控制，剩下的精细候选确认与否定可能不足主会重要性。instrumented cost 的部署意义有限，四平台叙述也没有共同因果模型。如果据此弱拒，理由应是增量与影响不足，而不是要求论文必须有 optimizer，或将披露限制称为已证无效。

**最终判断。** 我选择 **4/6 弱接收，置信度 4/5**。B570 的非参考完整轨迹前瞻预测和 RTX V4 同集合指定候选反例，提供了超出回顾性 path sensitivity 的可证伪知识；同研究的资格/成本决策为它增加了系统意义。我认为这刚好跨过接受门槛。强接受需要更大增量或更宽实证基础，但这些不能被误列成当前有限主张逻辑上必要的补实验。现有材料修订可完成我提出的请求；未发现 P0-V，也没有本评审所采用的 P0-C。
