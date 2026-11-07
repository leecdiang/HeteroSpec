# 是否补第二模型家族：明确决策与有限设计

## 结论

**建议补真正的第二模型家族，作为正式投稿前的优先增强项；当前立即开始JSA重写，不等待新实验。** 这不是JSA指南规定的模型数量，也不是现有有界实验的逻辑有效性门槛。建议来自本稿想贡献可复用的运行时设计经验，而现有target为Qwen3-8B，RTX图变换也明确在Qwen3非flash图上实现。

新的Qwen参数规模、同家族新版或换量化位宽可检查别的维度，但不能计作这里要求的独立家族。M4/RTX/B570/358H四个硬件不能抵消这个限制。第二家族应改变实际model graph/architecture code path；其draft/target兼容性、tokenizer、量化、上下文、内存和算子支持先做工程检查。本PR不指定未经可用性核查的具体模型，不下载权重、不启动实验。

## 到底检验什么

将两种主张分开：

1. **固定实现的迁移**：将冻结的phase-scoped实现移植到第二家族的对应算子路径，在不看confirmation输出的前提下，完整参考资格和双基线成本能否成立？如果需要结构性新实现，记录为新recipe，不能叫原recipe零修改迁移。
2. **诊断方法的适用性**：若出现真实原生偏差，能否用自然state×current-recipe、own-path shams和有限phase family解释局部依赖，随后在新输入上验证提出的约束？没有偏差时，结果是该panel未触发修复需要，不是已验证所有因果模式。

这两项都比“第二模型也测一个吞吐数字”更贴近主线。不要预设它必须与Qwen3一样需要mask3，也不要挑选会复现预期失败的confirmation任务。

## 后续协议应具备的最小矩阵

以下是设计建议，不是已冻结的执行协议或事前功效保证；实际ID、样本数、重复轮次、预算及统计规则须在读取新输出前写入单独protocol并commit。

| 阶段 | 必须固定/测量 | 停止与解释 |
|---|---|---|
| 工程资格 | 权重/tokenizer/runtime/graph身份；target/draft兼容；无capture与有capture一致性；R重复稳定；EOG/cap/采样/状态接口 | 不支持的算子/家族记录为工程限制，不能算科学negative或悄悄换成Qwen |
| Discovery | 独立小panel；native ordinary speculative、ordinary R、matched M、候选C；若有偏差才做自然cross与sham | probe是exposed；保持真实prefix和pending状态，不teacher-force或输入未来proposal |
| Finite scope | 若要主张phase选择，预定义与原研究可解释对应的phase switches，并完整报告通过/失败 | 合格集合变化是有效边界，不能只挑原mask3；无偏差则报告无须修复而非“找到相同机制” |
| Freeze | 冻结唯一主候选/无修复分支、code/weights、参考合同、confirmation输入身份、计时、missing规则、停止预算 | 新家族的参考应预注册为该家族的ordinary参考，不能要求token ID等于Qwen或事后改参考 |
| Confirmation | 与discovery分离的输入panel；R/M/C，另保留未修复native条件以识别repair是否必要；四条件同任务实际付费、平衡顺序 | 若需一个小而可比的起点，可设计24–32个新输入、4轮；这是工程预算示例，不是样本充足性或高置信泛化证明 |
| Cost/session | 每任务绝对费用中位数再求ratio/GM；generation和resident request；失败、warmup、冷加载分账；控制session顺序 | 若要强调稳定微小request增量，至少增加独立session/day的预定重复；task bootstrap不替代session复制 |
| Boundary | 一个事前固定的宽度或长度挑战，若预算允许；报告实际生成长度 | 不能看结果后不断加任务/调k直到正结果；更大cap不等于更长实际trajectory |

## 结果分支预先写清

| 结果 | 论文可增加的内容 | 不能增加的内容 |
|---|---|---|
| 原生有偏差；固定recipe修复；R/M成本均正 | 第二家族下的有限资格与合格运行点 | 普适无损、跨所有家族的mask3定理 |
| 输出修复但M/C或R/C不胜 | 第二家族的合格成本失败；进一步支持两门槛独立 | 改删baseline、只报较好timer或改用旧慢实现当部署比较 |
| recipe失败或phase需求不同 | 真实迁移边界；限定原方法scope | 持续调参直到通过，再把新结果叫原冻结方案成功 |
| native没有偏差 | 在这个新panel下无需修复/无机制触发；仍可测额外约束成本 | 证明原机制不存在或已复现跨家族repair机制 |
| 工程不兼容/预算中断 | 明确incomplete、unsupported或missing | 算作完成的negative science，或插补输出/耗时 |

与最近方法的同合同实现比较是另一种增强，不能由第二家族替代。如果重写要声称优于某个方法，必须真的完成共同模型/任务/参考/后端/timer对照；当前应避免此类优越性主张，而不是为了转投自动开展昂贵的大比较。

## 未补时如何提交

保留一家族消费级runtime案例定位，标题/摘要不写cross-model generalization；清楚写graph特定实现和有限充分性。选择继续投稿可以是作者的理性取舍，但不能把已有四平台或更多重复当作家族缺口已解决。所有新实验由后续独立任务/协议执行，本PR不授权runner自行扩展。
