# RTX 执行交接

请执行本目录 PROTOCOL.md 的新实验，保持 Draft。先阅读仓库 CONTRIBUTING.md、
PROTOCOL.md、plan.py 和 PLAN.json。父证据固定在 PR122 提交
`a1f15bfc8222054aa7b94b40f41af0dd0492ddab`；旧 UUID 已关闭，禁止恢复。
本 PR 交付实验设计与 CPU 排程工具，尚未实现新的 Windows 原生适配器，也没有 GPU 结果。

目标只有两个：
1. B0：相同逻辑输入与 causal frontier 下，改变物理存储长度能否保留参考字节、
   改变实际执行路径，并消除 1024 邻界成本断崖。
2. T0：真实 ON 的完整 Q 转换事务中，QH compact 是否优于原有 QB permuted。
   两个相同 QB 对照必须保留，不追逐亚微秒赢家。

按顺序推进：
- CPU 检查现有运行时、构建来源和 dispatch 源码；找不到对应源码可保留 UNKNOWN。
  运行 `python -m unittest discover -s benchmarks/rtx_dispatch_intervention_v1 -v`。
- 在新目录实现新的 adapter/collector/分析与证据导出。参考 PR122 的 runner.py、
  collector.cpp、graph_base.h、cupti_observer.h、producer_rtx.py 和审计工具。
  不要直接拿旧 collector 执行补齐；其运行身份和输入物理 span 检查需要适配。
- 必须用实际 strides 审核 K/V 补齐与 mask；逻辑 token 不重排、不丢弃；
  新 K/V 为有限零，新增 mask 为负无穷，原 mask 字节不变。
- 先提交实现与首次冻结，再采新 serial 参考及资格。补齐路径必须匹配原未补齐参考，
  不是只匹配自己的 padded 参考。失败保留，禁止改容差或换 seed 追求通过。
- 用 CUPTI 证明实际 ON；profile 与 clean 分离。资格后冻结 admission，
  然后按 PLAN.json 的两个 session、八块、平衡顺序完成合格路径。
- 所有原始输出、失败、超时和未启动坐标保留。汇总按 PROTOCOL.md 的统计口径，
  做 fresh restore 和新解释器复算，关闭 UUID，推送结果与摘要，保持 Draft。

自由度：路径、编译命令、工具接入、日志格式、CPU 实现细节可自行调整并记入修订。
允许在固定预算内修正首图前工具故障并新冻结；不允许科学重跑。
可因资格失败/ON 不可用/时间或资源上限省略对应臂，明确 INFEASIBLE、UNKNOWN、
UNSUPPORTED 或 INCOMPLETE，不要因为可选 trace 或来源查询阻塞全部交付。
正式采集后不得更改输入、模式、计时边界、warmup、重复数、排除规则或基线。
如确需改变科学设计，结束原 cohort，提交后续方案，不在本轮悄悄替换。

默认 344 个 GPU 宿主、11,400 次显式图调用；含额外能力/诊断的总上限
358 宿主、11,732 次。最多 24 次 profile 尝试（含失败），一个 GPU worker，
总六小时且最后 45 分钟交付。细节以 PROTOCOL.md 为准。

不启动 actor、自然 decoder、RTL/FPGA；不修改 B570、论文或 main，不合并。
硬件保持 SOFTWARE_FIRST/HOLD。阴性结果和不可行映射也是完成结果。
最终在对话直接给出主要科学结论、局限、预算、归档位置、提交 SHA 与 PR 链接。
