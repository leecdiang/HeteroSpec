# B570：成本差距与实际工作量

所有速度比均为 baseline_ms / candidate_ms，>1 表示 candidate 更快。每任务先取两轮绝对费用中位数，再相除，最后取任务几何平均。原始费用和端点见 COSTS_RECOMPUTED.csv，任务配对和单轮配对分别见 COST_TASK_PAIRS.csv、COST_ROUND_PAIRS.csv。绝不缩短 suffix 的已付时间。

| 比较 | 任务数 | generation | whole | host |
|---|---:|---:|---:|---:|
| ordinary R / candidate |15|0.28258755350958753|0.2012895931787418|0.2018837104115267|
| matched target / candidate |15|0.28576136794192253|0.2057042276473282|0.20624276201591446|
| old N1 / candidate |14|3.9930912531266287|2.6339404210545703|2.6333865472136693|
| ordinary R / matched target |15|0.9888934797058363|0.9785389220285977|0.9788644626275350|

候选在全部15任务的中位数和全部30个单轮上均慢于 R/matched，三个 timer 均如此。old N1 的14个任务中位数均更慢；generation 的28轮均更慢，但 whole/host 各有一个反向轮：MBPP/245 round2，old N1/candidate = 0.8735823147094709 / 0.8736026835705244。该例外保留，未选择性重跑。

候选相对 R 的整请求耗时倍率约4.968，而 matched 相对 R 约1.022。后者直接反驳“参考保持目标路径本身约慢5倍”的解释。matched→candidate 加入完整投机循环后的整体差、old N1→candidate 改换研究前端的整体差，都不是隔离的单组件 duration。不能从 GM 相减求 draft 百分比。

## 正式30份 candidate 记录中的工作

日志实际总计：prompt 1416 tokens、端点1150 tokens、raw1176 tokens，其中26个 suffix 仍全额收费；drafted888、accepted702，合并计数接受率702/888 = 0.7905405405405406。它不是30个请求接受率的简单均值，也不是未观测 proposal token 数组的等价证明。

target caller：474 calls / 2748 tokens；draft caller：1392 calls / 2778 tokens。扣除两个模型各一次 prompt 工作后，target verification 为444 caller calls / 1332 caller tokens，draft proposal888单token calls，draft catchup474单token calls。target continuation/端点 = 1.1582608695652175；draft continuation/端点 = 1.1843478260869564。R/matched 每个输出后的单token续算在末端前停止，正式 matched 共1120 continuation caller tokens；candidate 比这多212个 target continuation caller tokens（包括验证未提交位置与末端多余工作）。这些是实际 caller 工作，不是 GPU kernel dispatch。

每请求令 P 为实际 prompt 长度，L 为完整 raw 长度，A/D 为 accepted/drafted，Tcall/Ttok 与 Dcall/Dtok 为记录的角色总计。此次 P<512，单序列、k2、draftUB1；冻结源码与全部30份正式计数支持：

```
V = Tcall - ceil(P/512)
target continuation tokens = Ttok - P = 3V
proposal calls/tokens = D = 2V
catchup calls/tokens = Dcall - 1 - D = Dtok - P - D = L - A = V + 1
raw commits = A + V + 1
```

公式在已有6份 C capture-on开发记录中与 decode、KV mutation、commit 数组逐项核对；4份 matched桥接 capture-on另核对其 target caller 总计。这些记录均为开发/桥接证据，不计入正式 E 速度，也不称新独立确认。

UB1 使冻结 runtime 的 microbatch 容量至多一个 token，k2 的三token target caller batch不能在同一多token microbatch内验证。因此本实现缺少该种批量摊销机会；3V是 caller token 总计，不是3V次 GPU重算、kernel或graph的实测次数。完整形式上的派发与内核 duration 均 unknown。不能据此证明 B570 所有实现不可能投机加速。

## 源码支持而非隔离计时的操作

source anchors：candidate-front/native.cpp:184–229（请求重置、两个角色 prompt）、250–274（sampler/batch构造与phase binding）、463–534（commit、KV keep/cp/rm、catchup、clone）、563–676（proposal分布构造/向量拷贝、draft与target caller）、695–722（同步/清理与计时）；candidate-front/phase.h；candidate-src/llama-context.cpp:4332–4346；candidate-front/observer.h:36–60（capture-off仍记录总caller计数）。源码均与原CAS绑定，未运行任何前端。

按单序列循环和计数可确定：target KV mutation调用2340、draft1896、sampler clone444、proposal distribution vector copy888。这里是源分支调用公式，操作可能是no-op；不是抹掉/复制的真实KV字节量。catchup位于终止判定前，末次依旧收费。Formal capture-off不保留逐步commit/rollback；accepted总数已测，bonus与correct的单独总数、每次rollback删除的实际条目/字节、distribution每次实际数组宽度均 unknown。capture-on展示的是已记录开发轨迹，不填补正式缺失。

source可见请求前后两个角色同步、两次phase同步/图reserve资格更新、sampler候选分布构造与拷贝、KV元数据操作和host调度；完整独立组件毫秒和占比 unknown。一个更窄的已有 timer 可以访问：stderr 的 target `common_perf_print sampling time` 来自每请求新sampler的 `t_total_us`。按账本会话顺序关联、核对每块raw_count后，30正式请求共851.52ms，单请求9.79–94.05ms，打印精度0.01ms；其中sampler-chain子时间不能与父时间相加。该timer不含进入sampling前同步、不含draft sampler、distribution vector拷贝、clone/KV/host，不能代替完整sampling或GPU成本分解。SAMPLER_TIMER_AUDIT.csv与LOG_TIMER_AUDIT给出逐请求字节来源及范围。

同一stderr的load/prompt eval/eval/total属于未重置的context累计计数（eval还显示0），不能当互斥的逐请求GPU组件，或把unaccounted解释成单一host/rollback费用。prefill_ms记录候选联合prefill实际经过时间，不是 draft-only duration。generation timer还覆盖sampler初始化/phase操作与末端同步；whole timer覆盖重置、prefill、循环、清理，不含会话冷加载；capture JSON写出属于host边界。旧A/B主机时钟颗粒15.625ms只用于诊断，不提供正式细粒度收益。

同context/live sampler已去除旧第二target context、序列化handoff及三次状态读回，正式capture-off没有phase KV见证读回。old N1整体改善支持工程进展；R/matched依旧远快于candidate，削弱“这些旧状态传输开销就是全部差距”的假设。剩余差距未通过单独中介实验归因到draft、sampler、UB1或任何唯一组件。

## 决定

B570_GPU_NEXT_ACTION=STOP。此次没有区别于固定数值路径/KV原则、能够在线删去真实paid工作且保持参考的新机制假设。进一步前端清理属于 HARNESS_OPTIMIZATION_ONLY；不实现新候选、不增跑模型。

若未来另外授权，用符号条件 `T_R > T_prefill + T_verify + T_draft + T_sample + T_KV + T_sync + T_host` 组织测量，右边所有未独立测量duration保持unknown；相互重叠时须定义互斥边界。不可假设零draft、零rollback或全接受，不从现有GM推出通用上界。新确认输入须重新审计暴露并预冻结，现E15已是开发数据。
