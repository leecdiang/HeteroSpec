# 方法与实现稿：源代码核查及作者交接

## 已交付

- `paper/sections/03_method.tex`：以具体四查询例子介绍物理组与算术组，定义部署级参考、输出/状态合同，给出物理范围公式、`[K,a,g]` 组织及四步构造，最后给出条件化组合论证。
- `paper/sections/04_implementation.tex`：解释 Q8 与 Q4/Q6 的不同内层算术、强控制、resident 执行、真实 reuse 键，以及在线检查、capture、离线资格与失败边界。
- `paper/sections/supp_contract.tex`：集中记录支持域、实际 guard、输出请求范围、状态观察范围和两类 CPU 消费者诊断。

主文方法与实现约 1800 词；补充约 1000 词。只需标准 LaTeX 数学和 `enumerate`，无新增宏依赖。引用键为 `records` 与 `loop4code`；方法图使用 `fig:overview`。主稿应以固定版本来源表补足 `records` 对实验和实现的索引。

## 本次直接核读的证据

1. 原论文 #222 的参考、方法与补充章节；最新主线报告中路线 A/B/C、方法步骤、叙事诊断、反证与证据边界。
2. #241 `GUARANTEES.zh.md`、`GUARD_SOURCE_AUDIT.json` 的全部主要结论和相关 G01–G10 条目。
3. 当前 main 的 `src/reference_batching/reference_batching.hpp`：dense state、`scalar_prefix_requirements`、相邻分组、projection requirement 和 graph identity。
4. 固定源码资产中的 `phase_plan.hpp`、`resident_context.hpp`、`worker.cpp`；`llama-graph.cpp` 的 packed projection、local attention、reuse/placement；`llama-kv-cache.cpp` 的 live append；CUDA dispatcher 与 MMVQ 的 marked loop4 路径。方法写法来自具体控制流，不把辅助结构存在视为实际接入。
5. #218 S3 的 `llama-graph.cpp.diff`、`mmvq.cu.diff`：B 的共享 quantizer 后逐列 scalar backend loop，C 的 `[K,1,q]` channel 组织。
6. 原生物理范围干预固定版本 `701079f265c0ff8fd05d43fbc2d8d5054a711e1b` 的 `RESULTS.md` 全文。确认两种外层消费者都把该 AV 算子降低为 q=1；q1/q4 是外层消费者身份，768/1024 才是该干预实际改变的算子范围。没有把源码推测的 reduction launch geometry 写成 profiler 结果。
7. CPU 宽度失败与 frontier 公共结果，并直接读 `frontier_probe.cpp`。frontier5 实际参考为 `{4,1}`，候选为 `{8}` 后 trim 到5；必须区别于 full-width `{4,4}` 参考。额外向量被捕获，但共享消费者只要求前4行，不能改写为原生产 verifier 已合格。

没有执行原生模型、GPU、服务计时或重新资格。这里的代码重读不会改变历史资格范围。

## 已修正的关键风险

| 风险 | 稿件处理 |
|---|---|
| 把 scalar reference 等同跨设备参考 | 明确定义 $R_d$ 是具体部署；另一设备/后端是另一参考。 |
| 仅 mask 一样便声称执行一样 | 从真实物理 extent 干预解释差异，并将分组范围与算术路径分别处理。 |
| 把 `[K,a,g]` packing 或 loop4 自称原创 | 贡献写成两类约束、局部切分和消费者义务的组合；引用已有 small-column 实现。 |
| 把 S3 B 错称 loop4 | 正文明确 B 是共享量化后的 scalar-loop；Q4/Q6 $a=1$，Q8 $a=4$。 |
| k3 verification 被画成多组 Q8 packing | 实现明确三 proposals 只有四个 verify rows，真正多组 packing 发生在较宽 prompt 工作。 |
| 把 planner arithmetic tag 当完整数值 recipe | 明确它只编码 K/V 类型；其他选择由部署绑定与 backend 分析承担。 |
| 把 frontend Identity helper 当 live reuse key | 正文描述真实 policy/prefix/head-placement/topology 检查，附录说明 helper 未接入。 |
| packed 自动继承 loop4 的 guards | 正文和附录准确区分 marked control 与普通 dispatcher。 |
| clean observer 等同每次执行证明 | capture-only 观察与 clean service 分开。 |
| CLI 退出等同服务事务恢复 | 正文说 target-group poison；trim/draft/sample/reset 等依赖进程退出。 |
| token/argmax 一样等同全输出状态一样 | 方法合同完整；附录保留 242/256 与 127/128 的 CPU 反例。 |
| frontier5 宽度诊断被扩大为通用 verifier 资格 | 明确预设下游合同、固定 token37、q4+1 对照、额外第五向量不属于共享合同、非自然 acceptance。 |

## 语言与科学编辑

将原来“recipe / phase plan / frontier / guard”同时引入的方式改为：先让读者看到哪里必须切，再定义参考和两种组。正文采用明确动作，如 derive、partition、retain、copy、commit，不以 `only/may/however/we do not claim` 串联段落。必要限制分别放在合同定义、实现边界和补充细节，不重复使用防御性形容词。

独立于语言简化保留的科学条件：物理范围公式仅属于 dense nonwrapping profile；[K,a,g] 形状不是数值证明；条件组合不是全输入证明；已请求向量不得事后丢弃；有限离线观察不能升格为 always-on guard。

## 实际使用的 skill

固定来源：`K-Dense-AI/scientific-agent-skills@2d2065fb4520fa3f3f2bcf61cff26ec8b7eba4b5`。

- `scientific-writing`：已阅读全文，采用证据先行、明确科学问题与贡献、区分方法/实现/结果、引用可核验来源。没有安装其可选软件。
- `peer-review`：已阅读全文及 `references/ethical_review_practice.md`；用于作者授权的内部审稿，检查核心主张、替代解释、适用范围和复现边界。没有将它冒充编辑部委派的匿名同行评审。

语言审阅由本轮独立编辑流程继续完成；本文件不声称已调用不存在的 humanizer 软件。根代理负责全稿所需的技能记录、AI 声明与作者最终核实。

## 尚需整稿时核对

1. `records` 的补充来源表必须列清固定源码资产哈希、S3 diff、物理范围干预、消费者诊断，不让通用仓库 URL 承担所有复核定位。
2. 旧正文若保留重复的“Why batching changes results”节，应避免再次全文复述 768/1024 例和合同定义。方法开头可与引言呼应，但无需第三次定义术语。
3. 数值合同图中分别画 physical attention extent 与 arithmetic group；S3 不画成 a=4。图中的组表示合法组织，不保证所有组同时驻留或并行执行。
4. 后文结果不能将完整投机收益归给此方法，不能把跨合同 modern operator 比较当作方法服务收益。
5. 若进一步承诺任意后端、自动准入、故障后复用或正式在线证明，需要额外实现及资格，不能靠润色本稿获得。

本次已完成与图表代理交叉核对：`fig:overview` 与 `fig:extent` 标签一致，AV 干预明确 q=1、pad P + 对应宽 V，不称为 V 补零或 full-state 干预。
