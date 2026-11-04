# RTX 历史证据重算：draft 预填充摊销，而不只是 QB/WB

2026-11-04。只读CPU重算；未启动GPU、未碰用户设备、未改PR。固定提交见 refs.json。不是新实验、因果结论、总体推断或投稿概率估计。

## 最有用的新增发现

1. **旧数据里已经存在“decode有价值，但draft启动成本吃光收益”的明确会计证据。** #151 day1/day2 的672条原生记录被独立解码；96个 input/session ×7arm，五个公开log对比重算最大差3.89e-16。全部56个draft亏损块在扣除target/draft prefill后的会计残差仍有正收益。不能把“整个请求不划算”解读为“verify没有价值”。
2. **#162本来就有拆开领域与长度的24输入面板。** 这比#151的数学短/代码长完全混杂更有用。Llama短数学draft收益M_QB/C_QB=1.1450，长数学0.8933；短代码1.0018，长代码0.8769。两种领域的长输入都不划算，不能用“数学开、代码关”的领域标签代替成本模型。
3. **并非所有负结果都能靠一点优化救活。** #151四个Smol session要消除总draft prefill的66.7%–73.2%，即使假设没有任何额外开销，才让该session总耗时打平。把prefill砍半仍比同scope target-only慢6.7%–9.3%。个别亏损块需消除97.4%，理想无开销同前缀分摊也需超过38次，远非“加个cache就好了”。
4. **历史强对照仍约束路线。** #122真实Graph replay将QH相对QB的12–13µs差额压至约0.7–1.6µs；#123真实producer→upload→compute→readback事务中，compact QH仍约1.0016–1.0022×QB。不能把重新减少launch的收益重复算成layout独立贡献。

## #151：原始相位会计

完整三日期公开input/session对比中的draft收益（M/C，大于1有利）为：Qwen代码1.018×、数学1.620×；Smol代码0.724×、数学0.994×。但数学对应短prompt、代码对应中长prompt，不能分离领域与长度。

本轮实际下载并校验了day1/day2两个小包，共672条formal native off.json；day0使用公开对比表，未重新下载原始计时。以下是两天的算术均值，不要与三天几何均值混用：

| 模型/组 | 块数 | 非prefill净节省残差 | draft prefill | target prefill C−M | 完整请求M−C |
|---|---:|---:|---:|---:|---:|
| Qwen代码 |32|1.289919s|1.125670s|+0.018456s|+0.145792s|
| Qwen数学 |16|1.356654s|0.176863s|−0.009589s|+1.189380s|
| Smol代码 |32|0.137637s|0.648966s|−0.008287s|−0.503043s|
| Smol数学 |16|0.127945s|0.115159s|−0.004894s|+0.017680s|

定义残差为(M−M_target_prefill)−(C−C_target_prefill−C_draft_prefill)。严格恒等式：M−C = 残差−draft_prefill−(C_target_prefill−M_target_prefill)。它包含非prefill的host逻辑、同步、上下文管理等，**不是排他的GPU decode收益，不是干预后的因果预测**。

原worker固定源第84行每次reset清空KV，第93行decode返回后llama_synchronize再累加phase，第137–138行先target prefill再draft prefill。因此这些是顺序host墙钟而非异步kernel duration。672个service减所有target/draft phase和都非负，范围3.20–33.91ms，均值12.36ms，未发现phase和大于service的明显重叠错误。

两天Qwen总M=219.874420s、总C=196.178995s、净节省23.695425s，四session分别节省6.166295/5.953378/5.636118/5.939634s，公式一致。四session的C/M总耗时比0.88808/0.89326/0.89603/0.89161，与等输入几何比约0.819不同，因为长请求权重不同。应同时报告两种estimand，不能把几何18%减少写成总等待时间减少18%。

Qwen组内平均接受率：代码0.7645、数学0.7979；Smol0.6620、0.6701。两组非prefill残差相近而draft prefill差很大，说明只用接受率判断收益遗漏了显著启动成本。但接受率是运行后得到的结果，不能当作admission时已知特征。

## 每input/session的摊销阈值

完整96行见 amortization_per_block.csv；模型×date×session汇总见 amortization_recomputed.json。

令C为实测draft-on完整成本，M为同scope target-only，P为实测draft prefill；候选方案实际可避免P的比例f，额外总开销h。仅作敏感性算式：

C_new = C − fP + h；严格有利要求 f > (C−M+h)/P。

f必须包含真正可复用的比例、实际命中率、实际减少计算量，不能用“缓存命中”自动设置f=1。h需要同时包含lookup、状态检验、导入/复制、同步、维护/淘汰、内存压力，以及对原decode路径的干扰。

仅在假设相同合法状态跨n次均摊完整P、无其他路径变化时，C_new=C−P+P/n+h，需要 n>P/[P−(C−M)−h] 且分母为正。此公式不是自然多轮对话的性能预测。

- Qwen16个亏损块：无开销阈值2.43%–66.78%，中位10.69%。理想n临界1.025–3.010。它不是所有Qwen请求的收益空间，原本数学请求已明显获益。
- Smol40个亏损块：阈值18.69%–97.39%，中位76.96%。理想n临界1.230–38.343。只有部分输入可能值得改造；全局盲开draft没有证据。
- CSV也给出额外10ms时的阈值。常数10ms只是透明的敏感性坐标，不是测得cache实现开销；真实开销可能随state大小改变。
- 每模型仅两天、每天两session，重复同12输入。阈值范围是观察范围，不是置信区间，更不是独立96样本总体概率。

## 为什么不能据此直接启用prefix缓存

原#151明确prompt_reuse=false、每次清空状态，因此本轮**零条自然cache命中证据**。跨请求复用还需要逐项满足：

- target和draft是各自模型与KV，不能拿target snapshot充当draft state；准确绑定模型/权重、tokenizer和prompt token序列、位置/RoPE、KV dtype、runtime/reduction策略、上下文/stream生命周期。
- 可共享的必须是相同合法前缀，不是相似文本、同dataset、同长度；实际多轮前缀增长会产生append新工作。
- 每个分支有各自pending token、accepted/rejected proposals、correction/bonus、回滚和committed KV。只匹配最终文本或长度不够。
- 存储cache的空间会挤占显存，可能触发CPU offload、allocator变化、同步与内存移动，且改变参考算术分派。固定资格不能从旧run继承。
- reset/复用/并发隔离必须完整验证，observer或capture不能偷藏在计时外再宣称零成本。引用多轮收益须同时给冷未命中、热命中、部分前缀和淘汰轨迹。

先测真实命中分布、P中可复用部分和h，再代入上述阈值。另一条候选是reference-preserving draft prefill实现，而不是缓存；这仍需重新验证draft全过程参考、相同proposal/逻辑工作以及完整请求，不可假设把UB1变宽自然合法。

## #162：独立交叉面板验证假说的价值

固定PR162头0f2bb3a...，HELDOUT.json含24条预输出SHA选出的自然输入，代码/数学×短128–384/长512–768各6条；6session、144块。FINAL_COST中每块包含6arm原始service_seconds。本轮从秒数复算layout、draft收益与基线，并核对公开汇总。

|预注册输入格|M_QB/C_QB|C_QB/dual C_PQ|draft有利块|
|---|---:|---:|---:|
|短代码|1.001790|0.981727|15/36|
|长代码|0.876872|0.974858|0/36|
|短数学|1.145035|0.964187|35/36|
|长数学|0.893313|0.981455|1/36|

所有Llama总体draft收益仅0.973607，layout为0.975531且未过原practical screen。不能把相对慢参考R约2.18×的优势称作draft带来的优势，因为同scope target-only已经更快。

**暴露面板上的选择空间敏感性**：事后采用“短开draft、长target-only”，几何时间比为常开draft的0.940773、常关draft的0.966276；按总耗时为0.923991、0.976408。六session均同方向。这里长度带是预先固定，但开关规则是看过结果后选择，未计policy开销，**绝非新盲测、自动方法实现或可发表的泛化性能**。它只说明值得把下一实验做成真正按输入分割、固定启发式的mixed-path对照，而不是在已暴露输入ID上学习oracle。

反例：#159新修复面板12input×4session，48/48块draft有利，总体D_QB=1.42555；#166两个模型各12块，Qwen8B D_QB=1.19359，Qwen14B=1.65821。长度不是跨模型通用关闭规则，模型、目标/草稿相对成本和服务窗口必须进入资格/成本边界。

## 历史范围与自洽检查

- #120–123：下载50个CSV。本轮从host表重算#12090对、#121core384对+holdout96对、#122768clean host及#123208qualified timed host。#120最初用eligible会误纳入block4，它表示数值资格，正确cost筛选必须额外timing_eligible；脚本已修正并再现0.885627 QB/QH、−11.997µs。是本轮分析排错，不是原仓库结果错误。
- #121 QB/QH0.900826、holdout0.962421，复现公开报告；不使用原不可信SM clock归一化。
- #122 q2 key1023/1024/1025，OFF QH−QB约12.741/12.165/12.056µs，ON约1.295/0.735/1.627µs。selected geometry，并非自然工作负载。
- #12312个padding资格失败，48个slot依规则不执行；不能删掉失败拿幸存样本给快路径效益。完整事务compact QH/QB q2=1.002216、q4=1.001598。
- #137下载旧E0失败和修复后的时钟记录，保留“不足原始历史logits”的边界；未把旧R endpoint等同完整参考。
- #144两个合格模型各48块重算：Qwenlayout0.967781、QB/R0.560577；Smollayout0.930056、QB/R1.007007。Llama未合格无成本，未纳入。
- #147864measurement记录重算k1/k3×fresh/resident全部四格，匹配公开几何比和所有reversal。fresh setup+teardown约17.4–17.6ms，resident约0.04ms；它们不是模型加载时间。service与分项和有最高75.8µs余量，未假称精确可加计时。k3布局收益成立不意味着draft开关或所有新runtime仍然有收益。
- #151公开三日期144个input-session logs代数核对；原始重算只覆盖day1/day2、672请求。
- #15948块分析级成本；#162144块含每arm秒数；#166两模型各12块秒数。
- #168已取complete-cost/cost JSON，但不是本报告新结论来源。#124–136多数为B570/文稿/计划；#140–146分段结果以#144/#147完结数据为准。**不是宣称120–170每个PR都逐文件复核，也没有重验所有原始logits/张量字节。**

## 最小下一实验建议

冻结模型、原始数值参考、scope、k、context和服务窗口后，用全新输入做交叉domain×prompt length×output budget。固定cost-only先验、常开draft、常关draft、冻结mixed规则，并用配对完整service比较。prefill、draft prefill、continuation分别记录，完整service为主指标；资格失败、miss/eviction/fallback和所有policy开销留在主分析。盲测不得使用该请求未来接受率/输出长度/实际完整成本作admission特征。先证明一个保守可解释规则能赢**两个constant基线**，再考虑学复杂AUTO。

这是给路线新增一个可被推翻的机制假说与预算边界，不是再堆一个“总能选最快”的事后oracle。

## 复现

python recompute.py
python raw_scope.py
python amortization.py

只用Python标准库。此目录为最小可复现投影：raw_scope.py直接读取data/pr151-native-projection.json，不需要下载ZIP；projection逐条绑定源archive/member SHA并只保留计时、相位及accepted/proposal_count，未包含完整logits/KV。两个ZIP曾实地下载、SHA与所有CRC验证；投影重算不能代替重新下载原始证据。SOURCE_MANIFEST.json给出此包各源的固定Git路径和本地文本SHA；refs.json记录PR固定头。文本工具可能规范化换行，因此本地SHA不冒充Git源字节SHA。输出JSON、CSV都是确定性分析产物。
