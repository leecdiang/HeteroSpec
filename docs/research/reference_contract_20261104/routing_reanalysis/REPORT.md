# Draft-use admission：严格按原题隔离的探索性重算

2026-11-04。只读CPU历史分析，不是实测online路由，不是新的盲面板。脚本为本次探索新写，策略族受到此前已知结果启发，外层隔离不能消除研究者已经见过整面板的选择偏差。不得把这里的区间当确认性显著性证据。

## 结论

按完整请求成本比较最强不分流固定策略后，剩余可争取空间很小，且低复杂度路由不普适：

- Qwen：最强固定是始终draft。nested外层LOO省1.610%，恰好达到该12root面板的root均值oracle；阈值536–556tokens。12/12动作逐root一致，并非四舍五入巧合：两者成本均48.25503405s，而alwaysC为49.044748775s。不可将12个已知题上的完美分类当作可迁移保证。
- Llama：最强固定是始终target-only。nested省1.572%，而root oracle仅省3.167%。24root中路由选9个draft，其中4个反而亏；最大root均值损失339.9ms、相对target-only慢13.12%。
- SmolLM2：最强固定是target-only。nested反而慢0.383%，选draft的两个root全部亏；两个真实有利root都未选中。oracle可争取空间也只有0.885%。

这些结果不支持“只加一个prompt长度阈值就能普适挽回draft成本”；当前nested学习/选择流程在Smol上失效，但并未排除所有长度策略族或其他分布。模型已知但阈值不能直接跨模型照搬，prompt token数量也受tokenizer与模型结构影响。

## 样本与隔离

#151用day1/day2的QB96 measured配对：Qwen和Smol各12题，每model-root各4session，但仅4个题ID交叠（CodeContests/valid/108、/66，GSM8K/test/70、/806），并集20root。#162用QB144配对：另24root各6session。共44个题目ID、48 model-root单元、240重复请求配对。不能把重复session当新增独立任务。

每model-root先对全部重复session M/C秒数取均值，评价每root等权期望成本。outer留出一个完整root，同root其他session以及另一模型版本都先排除；训练再按部署时已知model过滤。每模型独立拟合，不借另模型的标签。内层同样按root留一，比较固定M/C与单方向stump（prompt≤阈值用C）。所有阈值只由内层/外层训练root的相邻prompt中点及始终M/C候选确定，最小化训练总成本；并列优先更简单策略/更保守阈值。

外层LORO仅隔离题根，不隔离日期：root均值及训练标签使用全部两天/全部session，因此不是按时间可部署的滚动回测，某早期请求的拟合可能用到后日其他题标签。此处评价的是历史面板内的新题隔离，不是时间前瞻预测。

唯一决策特征是部署model与prompt token数。未读输出长度、真实acceptance、EOG、phase或事后收益作为特征。cap均为128，没有给定预算变化，无法估计预算策略。模型和prompt长度是请求前已知，但tokenization/加载/维护等实际部署成本未测。

## 基线与oracle

- alwaysM/alwaysC是真正无训练的零选择成本规则。
- train_fixed是在每个外层train内选M或C，三个模型均与全样本事后最强固定一致。
- 最强固定分母是每模型完整评价面板上较低总成本的一种固定策略，不是较弱的always-draft；它使用测试标签选择分母，是刻意更苛刻的回顾性参照，不应宣称可事先知道。
- root_oracle按每root全部重复的均值选低成本arm，是事后有先知标签的上限参照，不是可执行策略，也不是按每次timing噪声翻转arm的session oracle。这个空间只限当前选定QB M/C两arm及样本均值；不是完整系统理论上限、未来分布保证或改变prefill成本后新arm的上限。
- exposed384_reference是#162原分层边界384的事后使用：虽然分层边界先于输出选择，拿它做draft路由已看过收益，不能称预注册策略。Llama省2.359%（旧事后route），高于nested的1.572%；搬到Qwen/Smol则比其最强固定慢1.949%/5.669%。

## 不确定性与实际开销

10000次按模型成员结构分层的root簇bootstrap：8个Qwen-only、8个Smol-only、4个shared、24个Llama各自簇抽样，保持每模型12/24root有效样本量；#151共享4root两模型同步抽取，随机种子817301。保持外层OOF决策固定，重采样完整root，得到相对最强固定省时的条件性95%百分位区间：Qwen[0.360%,2.898%]，Llama[−0.500%,4.122%]，Smol[−1.090%,0%]。

这些区间仅反映有限当前root的重加权，不重训阈值，不含训练不确定性、模型/研究者选择或公开面板筛选偏差，不是未来任务总体保证。尤其Llama包含零。Qwen当前OOF逐root都不差于alwaysC，所以固定预测的重采样天然不能产生负收益；Smol当前OOF逐root都不优于M，区间自然不为正。这不是训练后未来预测误差被证明有符号。当前44题也不是自然业务随机样本。

在假定每请求固定额外成本h的敏感性模型下，nested相对最强固定的均值余量只有Qwen65.81ms、Llama71.85ms；Smol已经负4.49ms，无正开销空间。脚本给1/10/50/100ms敏感性。这些只是会计允许预算，不是已测router开销。加载draft、状态检查、cache lookup/import、编译、内存压力及fallback都可能不是常量，不能因为CPU比较几乎免费便忽略完整部署成本。

## 跨日与跨模型反例

#151 day1训练阈值在day2测试，以及反向，仍是各模型相同12题，仅测时序稳定性；day2→day1是逆时诊断，不是未来预测：Qwen阈值548.5两方向省约1.52–1.71%；Smol分别阈值214/76，约省0.39–0.53%。Smol同题跨日看似有利却新root LOO失败，说明这种切分不足以证明泛化。

跨模型直接搬全源模型拟合阈值，Qwen548.5到Llama仅省0.784%，到Smol反而慢8.145%；Llama319.5到Qwen慢1.949%、Smol慢0.528%；Smol76到Llama完全不启用draft，到Qwen慢7.220%。#151模型互迁仅4/12目标题共享root，是部分重叠的跨模型测试，不能称完全新题验证；#151↔#162则换模型、数据集、tokenizer、fresh/resident口径等多项，不能把差异归因单一因素。

## 下一步与投稿用途

当前结果适合把具体单方向长度阈值流程列为经过检验、在Smol未改善的基线，支持必须报告强固定baseline与风险尾部，而非给auto直接背书。不要事后追加更多规则直到本面板好看。

若继续，新盲root要在看输出前固定：模型分组、阈值/规则族、训练数据、是否包含fallback以及完整开销；不按EOG/acceptance筛选。旧#162事后route保持exposed-only标识。将每root最坏额外成本、错误启用率、总成本与校准分布漂移一起评价。没有新数据前不能宣称真实accept率、online速度或投稿概率提高。

## 复现

在本目录运行 python -O analyze.py，只用标准库。scalars.json只含240个QB配对的完整成本、prompt计数、模型/日期/session、公开root ID及whole-source member hash，不含题目、token序列或其内容摘要。SOURCE_MANIFEST.json记录来源与投影完整性校验。

results.json在本地生成，预期hash和字节见GENERATED_OUTPUTS.json；包含48个外层预测、全部阈值、内层损失、逐模型强固定/训练固定/oracle、开销、跨日与跨模型结果。只复算投影上的路由，不重验原始完整endpoint/KV。原始源审计见相邻rtx_mechanism和llama_reanalysis目录。
