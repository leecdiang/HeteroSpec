# 下一轮实验：准入、因果效果与约 5% 的判定

本文件规定研究顺序与判定含义，不启动新的 GPU 工作。当前两个执行 profile
分别是有限生产请求诊断和固定 target-operation 诊断；后续确认面板必须在模型、
平台、输入、预算均固定后另行提交。保留既有 S3 的计划与预算；本轮未确认其完成。

最新稿件锚点为 PR222 的 `e8a4981ef7db8f05cff7144fd4edc6e5a4109343`。
对作者四项审稿意见的逐项响应、S3 状态、recipe/guard 表设计、长前缀与相同
合同 runtime 的优先顺序见 [TPDS_FOLLOWUP.md](TPDS_FOLLOWUP.md)。这些研究
设计没有扩大下述两个有限执行 profile，也不把增加相似模型作为第一优先项。

## 1. 预先定义目标

主指标沿用 PR222 的 ratio-of-totals 和 5% 完整服务耗时下降口径。令 T_c、
T_b 为同一输入、同一配置下候选与冻结强基线的完整 resident-request 时间。
同时预注册逐 root 比值与等 root 几何均值，后者用于看平均结果是否掩盖迁移
差异。这项指标选择在本轮新服务实验开始之前固定；不改任何历史估计。

\[
\rho=\frac{\sum_{i,b}T_{c,i,b}}{\sum_{i,b}T_{b,i,b}},\qquad
R_i=\frac{\sum_bT_{c,i,b}}{\sum_bT_{b,i,b}},\qquad
R_{\mathrm{equal}}=\exp\left(\frac1n\sum_i\log R_i\right).
\]

同时报告每 root 结果、尾部时延及失败数，不能看结果后切换主指标。
\(\rho=0.95\) 是时间下降 5%；等工作吞吐对应 1/0.95，约 1.0526
倍。5% 吞吐增长与 5% 时间下降不是同一个数字。

### 结论分级

- 点估计 ρ≤0.95：达到预定的约 5% 点目标。
- 点估计达到目标且预注册区间上界<1：有该确认集上的正向收益证据。
- 区间上界≤0.95：才支持在该区间方法与采样假设下至少 5% 的更强陈述。
- 不同配置的平均收益不能遮蔽负例。普适性结论限于声明过的模型、长度、
  quantization、后端与 graph 条件；两张同型卡不是两个独立架构族。

所有阶段都保留 fallback 的实际开销。原始失败、超时和未通过资格的输入不能
从分母静默删除，部分完成只报告为部分完成。

## 2. G0：完成来源与动作准入

成本目录必须关联外部固定的 run 身份、实际成功状态、完整计划覆盖、输入 IDs、
模型/词表、源码/二进制/实际加载库、backend placement、计时口径和起末状态。
从待审文件内部读出一个自报 SHA，再拿它核自己，不构成外部来源认证。

旧 `matched_cost/verify_run.py` 与 `summarize_cost.py` 继续用于相应 raw 的诊断
复算；控制器使用本轮的严格准入接口。当前 CPU q2 失败和 q1-only smoke 不能
变成可部署的宽动作成本目录。即使未来 GPU 宏动作全部通过，也不能由此推导
分段中途的条件成本。

## 3. G1：真实请求 eager/deferred 的有限桥接

生产诊断使用两个从原始 job 预先确定的完整 prompt、k7、短 cap16。它关注
真实模型下的 full vectors、活跃状态、终止和必要尾部恢复；不是旧 cap96
确认面板，也不是新性能确认集。具体模型 SHA、进程/调用/行数/raw 上限和
构建命令以 `production_compare` 的固定计划为准。

必须区分三个时钟：

1. 原 worker 的 service_seconds：按其源码定义的完整 request 内部窗口。
2. model/pool 初始化和进程 wall：另行报告，不能与重叠窗口相加。
3. capture 观察、状态导出与落盘：可能改变缓存与同步，因此资格执行不能
   自动变成无 capture 的性能证据。

如果无 capture 路径只暴露 token、cycle 和 bounds，它仍缺完整向量/状态桥。
本轮准备工具不得凭这些字段声明 5% 或历史 R 兼容。该缺口要作为真实实验
结论保留，而不是扩大 PASS 的含义。

## 4. G2：同历史的 target-operation 诊断

PR221 的公开固定 profile 最大为 190 contexts、3,032 次 native decode API
调用、68,447 target rows；raw blobs 上限 2 GiB，native child 上限 1,800 s。
计时包含 schedule/batch 构造、原 planning、同步和完整 logits materialization，
排除 prefix 构造、状态导出/比较/落盘和 next continuation。它属于受 capture
影响的操作诊断。

保留 `first_after_fresh_context` 与 `one_shape_warmup_then_reset` 标签以及实际
graph build/reuse。后者在已有 CPU smoke 中仍是 build1/reuse0，不能称热图。

**改变研究判断的观测：**

- 宽动作不能保持所声明参考：该 deployment 中该动作不进入后续策略。
- 宽动作全部合格但价格差小于相应额外同步/恢复/策略成本：停止该分段假设。
- 出现足够大的、可重复且与 phase/shape 对应的成本差：进入 G3；不能立即
  将 q8 与 q4+q4 的差当成固定调用开销 A。

本 profile 的 q1 是诊断参考，尚未证明等于历史 R。q2 失败只排除该次比较，
不能否定 q4 与 q8 之间的所有合法变换。G3 应从明确的原 R 已部署路径逐动作
资格验证；本次保留固定 profile，不将其扩展为所有研究路线唯一的准入门槛。

## 5. G3：补足条件分支与强简单对照

在相同已生成候选图上比较整段验证、分段验证，以及短 draft→verify→需要时
再继续 draft。串行 proposer 与并行 block proposer 分别研究；替换 proposer
是独立干预，不能把它的收益记为前沿调度收益。

每个阶段的成本应按 outcome 绑定到收敛状态，至少覆盖首次拒绝、全部接受、
cap 终止、已观察 EOG、需要继续以及状态修复。尤其首 q4 输入
`[seed,p1,p2,p3]` 的末行可以验证 p4，但没有物化 p4 的 KV；相应 terminal
路径的补调用仍须计费。零 draft 选择后的下一轮 catch-up 也不能免费。

开发阶段先固定有限候选目录和成本口径。对拟用的 stage/outcome 有缺口时，
控制器返回不可决策状态并使用已声明的 fallback，不以宏动作均值补成零成本。

## 6. G4：冻结因果策略与确认输入

控制器只能读取当时可得的状态和过去已经完成的动作结果。首次拒绝之后的
proposal 结果属于删失数据，不按“都拒绝”更新；bonus 也不能当成已观察 draft
预测。未来接受长度、未来 EOG 和看过确认结果之后调整的阈值均不得进入决策。

本轮有限块 Bellman surrogate 是实现原型，不是已证明的完整请求最优算法。
STOP 的状态收敛必须有单独资格与完整成本。策略自身耗时必须计费。

旧公开 16 roots、两条成本历史和 cap16 诊断输入已被研究使用。确认集采用另行
固定的新输入，先固定全部 IDs 与 tokenization 后开始；不能仅换随机 seed 将
相同 roots 当作新确认样本。开发数据与确认数据在 root 级去重。

## 7. G5：controller × executor 的交叉消融

| | 既有合格执行路径 | 新合格执行路径 |
|---|---|---|
| 强 native/adaptive 控制 | B00 | B01 |
| 新前沿策略 | B10 | B11 |

四格共享尾部修复、cap 规则、同等 graph 支持及其它通用 kernel 调优。主比较
预先固定为 B11 对最强的、开发阶段已选择的可部署基线，不能事后给不同输入
挑不同弱对照。B10/B00 衡量控制变化，B01/B00 衡量执行变化。

另做 same-plan lowering intervention：固定相同输入、已选择动作及必要输出，
仅改变 executor，以识别执行路径效应。在线控制器与执行器同时变化时，不能
把整个差值都归因于 kernel。跨不同 GPU、OS、模型和 cohort 的数据也不能作为
单独体系结构因素的因果比较。

确认面板规模须在 G1–G3 完成后根据固定时长/精度目标注册。本文件不凭当前
合成 fixture 推断方差或声称足够统计功效。可沿用旧设计的 paired order blocks
与 root cluster 思路；重复同 root 不增加独立 root 数。bootstrap seed、draws、
区间方法、主要对照族和多重比较规则应在看到确认结果之前固定。禁止“达到
5% 就停”的事后停止规则。

## 8. G6：泛化与止损

先在一个精确部署验证收益，再扩展至少两种模型族、短/长 context 和两个
实际可取得资格的硬件/后端配置。每个新增配置独立绑定模型、source 和 R；
当前硬绑定 Qwen3-8B 的 profile 不能靠覆盖一个 caller 参数用于另一个模型。

当前算法原型明确限定 greedy。若要扩展到随机投机采样，需要另行证明自适应
停止规则仍保持目标分布，并固定 request/position 级 RNG 所有权。相同 seed 或
相同 logits 不能替代这项证明：当 p=q=Bernoulli(1/2)，只保留预采样为 1 的
草稿，否则重新从 target 采样时，最终 P(1)=1/2+(1/2)(1/2)=3/4。这个选择偏差
反例属于此前已审的算法边界，本轮不把 greedy 资格推广成 stochastic 保证。

报告各配置的收益、反例、fallback 比例和资格失败。仅有总体平均 5% 不支持
普适性；某配置不合格也不能改写成“零成本 fallback”。若 kernel/shape 的
机会集中于特定宽度，应把支持域明确写入方法，而非要求所有请求享有相同收益。

满足以下任一条件时，应降级或停止当前单请求路线：合法动作集合退化、实测
净收益上界不足、优于共同优化之后的强基线的效果消失、策略依赖未来信息、
或收益只能靠换 proposer/graph policy/比较器取得。届时可准确报告一个工程
修复或有限域机制结论；它们不自动成为新投机方法的普适 5% 增量。
