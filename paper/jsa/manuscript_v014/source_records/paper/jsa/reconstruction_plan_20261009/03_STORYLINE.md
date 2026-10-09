# 确认主线：执行约束在哪里，收益来自哪里

这是全文架构说明，不是完整英文稿。沿用#69的诊断→修复→成本骨架；主要改变是按设计决策组织证据，补齐重要反例，减少历史顺序和重复限定。

## 中心论点与贡献

给定必须复现的greedy参考，单看token前缀、接受率、验证调用数或预测命中率，都不能决定一个推测执行变换是否值得采用。需要分别建立：状态/当前路径的局部依赖、原生完整输出资格、普通与匹配基线下的真实成本。现有案例证明这些判断会给出不同答案。

三项可写贡献：

1. **执行边界的实证诊断。** 将自然保留状态与当前recipe交叉，结合own-path shams和单块干预，展示当前路径、状态、交互、即时null/后续变化等不同情况。新意落在具体native运行时的证据及其设计含义，不把状态干预本身当首创。
2. **目标阶段的有限实现与资格。** 具体解释RTX Qwen3非flash attention查询布局的图变换，保留projection/FFN批量计算；four-switch, 16-mask factorial确定有限家族内的目标prefill+continuation约束；随后冻结recipe验证24个project-unused输入。B570用另一种phase-binding实现建立对照，不能宣称同一算子跨后端迁移。
3. **合格运行点及其收益边界。** 通过R/M/C和qualified negative cases区分目标路径改进、推测增量、复杂控制收益与draft侧优化的上限。这是实测设计证据，不是一个自动优化器或由比率恒等式构成的新理论。

主张层级：观察到的有限行为 → 可执行的评估/设计方法建议 → 尚未建立的跨家族充分性。正文不得把第三层写成第一层。新家族即使成功，也仅扩展到其测试配置。

## 三个研究问题

| RQ | 要回答的设计问题 | 决定性证据 | 不应替代它的指标 |
|---|---|---|---|
| RQ1 | 输出偏差要求控制当前计算、状态形成，还是两者？ | 自然state×recipe，own-path shams，B570单块即时/下游区分 | 仅同token前缀、相同reason、logit margin或复现器命中率 |
| RQ2 | 在既定实现家族中，哪些阶段约束足以保留完整参考？ | 16 masks、native资格、冻结后RTX24、B570输入/宽度失败与修复 | 所选一步argmax相同，或把known answer回放当在线修复 |
| RQ3 | 合格修复应当部署、加宽或增加控制吗？ | 同panel R/M/C成本、fixed-UB宽度、B570强R、M4 guard/oracle、358H target-work floor | 更多accepted tokens、更少caller calls、比旧慢实现更快、孤立draft throughput |

## 正文章节蓝图

以下词数为作者写作预算，不是JSA规定；建议正文约6,500–8,000英文词（不含参考文献与补充），以论证密度决定。无需把现有24页单栏机械压回六页。

| 节 | 建议预算 | 内容与收束句职责 |
|---|---:|---|
| 1 Introduction | 650–850 | 从同参考下的软件执行变换切入；提前给出RTX正例与B570反例；提出3 RQ和具体贡献，避免先讲实验史 |
| 2 Runtime architecture and prior work | 750–950 | 执行事务、KV/pending/stop边界；模型和数值路径；最近工作对照，区分参考保持与logit determinism |
| 3 Study design and contracts | 850–1,050 | 配置/暴露/输出/计时矩阵；自然cross/sham；R/M/C；任务级估计；qualified速度门槛 |
| 4 Locating the consistency boundary (RQ1) | 950–1,150 | 以RTX repair/regression为问题，直接进入cross；B570单块反例与自然cross；旧prediction/bridge各用紧凑段落约束解释 |
| 5 Phase-scoped implementation and qualification (RQ2) | 850–1,050 | 从原图到query-batch布局的代码级解释；phase masks、原生资格、冻结RTX24、宽geometry失败；B570是不同recipe |
| 6 Does the qualified design pay? (RQ3) | 1,200–1,500 | RTX双基线主表与task variation；fixed-UB失败；B570合格但负收益；M4/358H作为控制和工作量边界，避免四篇独立故事 |
| 7 Design implications, limits and artifact | 650–850 | 三条证据支撑的操作建议；适用前提与失败分支；单家族与资料访问；未来家族只标pending |
| 8 Conclusion | 150–220 | 回答三个RQ，结束于已建立的有限设计证据，不重复全部数字与免责声明 |

摘要结构（≤250词）：问题与约束→本稿具体实现/实验方法→RTX generation与双request基线→一个决定性失败边界→贡献及范围。不要把全部历史study名称堆进摘要。不一定放M4/358H所有数值，正文和补充承担完整性。

## 全量利用与主文密度

必须主文出现：RTX /15 repair-/25 regression、自然cross；B570即时决策不变但下游变化；mask3有限范围；RTX24及双基线；宽度资格/成本两种失败；B57015 endpoint-qualified强R负收益；M4 Guard不胜固定策略；358H target-work必要预算。

应保留但压缩：H1/H2预测、ordinary U2 bridge、离线proxy选择。它们分别排除“预测就等于修复”“复杂复现器一定必要”“诊断自动变成有收益selector”。不能把这些否定结果删掉后又把论文卖成自动选择方法。

主要进S1：逐task数组/首差/分母、历次protocol和停止、FA-on pilot与各配置reference变化、旧M424Q/30Q及358H阈值分解、所有计时差异、原始能耗边界、#63旧长panel正例和新输入失败。正文给可读的证据角色索引，不逐PR讲述。

## 图表任务书（此PR不制作图）

| 图/表 | 要让读者看懂什么 | 数据/绘制限制 |
|---|---|---|
| F1 架构与约束位置 | 状态在哪形成、保存、使用；4 switches在哪里；R/M/C差何处 | 根据实际源码画vector；不能暗示当前C运行了未启用的state transplant |
| F2 交叉诊断与端点层级 | RTX path/interaction、B570 state/recipe；局部null与下游变化可并存 | token ID用等值类别着色，不以ID大小画连续热图；不同task不共享颜色数值含义 |
| F3 phase资格矩阵 | 16 masks、4 probes、passing3/7/11/15；有限最小mask3 | 如用图替代表则只留一个；注明k3/UB4，不能混旧UB2/UB1 probe结果 |
| F4 ordinary/matched/candidate | 总部署改动与推测增量的区别 | generation/request并列，统一baseline/candidate；不是堆叠组件耗时 |
| F5 成本边界 | fixed-UB更宽更慢、B570修复后仍慢、task差异 | 小面板或表更合适则不强画；不把跨timer平台画成共同硬件速度排行榜 |
| T1 study/config contract | target/draft、backend/runtime/quant、任务暴露、端点、timer、重复单位 | 将历史re-tokenized text与后期direct IDs明确分开 |
| T2 nearest-work delta | 已有原则 vs 本稿新增具体证据 vs 尚缺比较 | 不给没实现的方法编速度或支持矩阵 |
| T3 output/cost decisions | 输出失败、合格正收益、合格负收益各自对应的设计决定 | 展示真实失败与缺失；B570119/120不能改成120/120 |

## 比#69必须更清楚的五处

1. 模型家族：既有历史平台表显示final target均为Qwen3-8B；不能以“历史models不同”让读者误以为已有跨家族机制验证。
2. 局部实现：说明哪些tensor view/shape、graph复用条件、phase dispatch和state恢复/停止规则改了；引用实际实现路径与提交，不由散文猜kernel。
3. 证据层级：old prediction、same-state单块、natural-state cross、native完整输出、付费成本不互相替代。
4. 性能主张：1.742/1.683/1.035成组呈现；将局部图约束减少解释为资格范围，而非已有显著额外decode收益。
5. 结论形式：可以给离线工程评估流程，不能声称该流程已作为在线自动诊断/修复策略实现或跨模型验证。
