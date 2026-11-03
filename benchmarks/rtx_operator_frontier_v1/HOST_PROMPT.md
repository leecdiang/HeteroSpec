# RTX host handoff

继续本 PR 的 `benchmarks/rtx_operator_frontier_v1/PLAN.md`，基于冻结 PR168 独立推进，不改动正在运行的 B570。保留原面板 QB/WB 约 1% 且两轮反向的结果，不再重复计时追 3% 门槛。先用真实同操作数重放与源码/dispatch 核对，查清 Q8 projection/FFN 的统一四列分块哪些必要、哪些可放宽或减少 launch/concat 开销；有明确机制才实施结构驱动的局部改进，并把同样的算术改进公平应用到 WB-cut。再按计划完成 C1536 下 q8/q32、256/1024 边界的跨界/非跨界八个坐标，核对实际图调用、算子宽度、完整向量和固定配对成本，诊断结果不冒称自然负载平均加速。仅在实现实质变化时冻结候选并做小型新自然输入确认及一次成本面板；否则交付机制结论后与 B570 汇合。允许自主修复工程和已定位的结构问题，保持原 R、权重及 k3 合同，不复制 B570 的新 head 维度实验、不改旧结果、不自动合并。提交独立结果 PR，明确新增能力、收益来源或无收益边界。

The parent experiment is PR168 `9c79594f679ea4aad1956d8a385fdf6a7352d892`. This document authorizes host execution of the scoped plan; its existence is not evidence that the new native experiments have run.
