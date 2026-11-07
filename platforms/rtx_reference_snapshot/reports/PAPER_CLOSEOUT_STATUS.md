# HeteroSpec-PC 主平台论文数据收口状态

**PRIMARY PLATFORM = CLOSED (2026-09-07)**

## 范围冻结

本阶段只补充论文所需数据，不重新寻找“能赢”的配置。继续禁止：420 holdout、20B target、14B RTX 双模型同驻、更多 `k`、复杂 speculative algorithm，以及任何突破显存安全边界的配置。

## 工作包状态

| 工作包 | 状态 | 说明 |
|---|---|---|
| 已有日志统一数据集 | IN PROGRESS | 先保留全部真实字段；不存在的 TTFT/ITL/Intel energy 不事后伪造 |
| A 功耗与能量 | PENDING MEASUREMENT | 固定既有 12 题；需联合 NVML + Intel telemetry |
| A 噪声估计 | PENDING MEASUREMENT | 固定 6 题、每配置 5 次 |
| B empirical break-even | IN PROGRESS | 基于 60Q round-level 数据拟合并 bootstrap |
| C 第二模型家族 | PENDING FEASIBILITY | 先检查 tokenizer/license/export/VRAM，再决定 Gemma 2 或替代 pair |
| D context sensitivity | PENDING | 512/2048/8192，8k 先过 memory canary |
| E sustained thermal | PENDING | 10 min、各 2 次、ABBA/BAAB |
| 论文图表 | IN PROGRESS | 先生成已有数据支持的图；功耗图等待 A |

## 数据纪律

- 14B 的 4/12 exact mismatch 全部保留并标记 invalid，不筛除。
- NVML、CUDA 与 Intel power domain 分开报告。
- 缺失字段为空值，不使用推算值冒充传感器或逐 token 测量。
- 新测量使用唯一 run ID、1 s 对齐遥测和冻结的模型 revision。
- 第二模型若兼容性成本过高，记录为 feasibility failure，不更换研究问题或扩大工程范围。

最终关闭条件仍为全部收口工作完成后写入：`PRIMARY PLATFORM = CLOSED`。当前尚未关闭。
