# 主张到证据映射

历史表路径均在 `paper/mlsys2027/manuscript/tables/` 下。基线 commit：`e87291d26df32f2cb9571e005ab173b1c7a6830b`。以下仓库路径都相对该固定 commit；新 #57–60 未整合进匿名稿。复核范围：exports/计算器/封装与既有审计回执；没有把来源审计描述为本轮重新执行。

| 论文主张 | 固定证据路径 | 稿件位置 | 必须保留的边界 |
|---|---|---|---|
| B570 四任务恢复，20控制保留，360单元 | `benchmarks/b570_prefill_diagnostic_v1/{DELIVERY_REPORT.md,STUDY_REPORT.md}`；`paper/mlsys2027/reviews/reconstruction_v010/b570/` | Outcomes；干预附录 | 24暴露任务、三次稳定重复；无该干预速度/能耗结论 |
| RTX 预测全匹配，但恢复/回归使参考总数不变，645单元 | `benchmarks/rtx_target_verification_intervention_v1/STUDY_REPORT.md`；`paper/mlsys2027/reviews/reconstruction_v010/rtx/` | Outcomes；干预任务表/完整witness | 19 HE +24 MBPP；129/129预测不等于129/129参考修复 |
| 普通 U2=N1，171新原生运行 | `benchmarks/rtx_target_only_bridge_v1/{STUDY_REPORT.md,RESULTS.json,VERIFICATION_REPORT.md}` | `05_bridge_v011.tex`；bridge图/表；附录U | 三轮57/57完整ID+边界；17/19参考一致；24线程旧默认12线程并非因果对照 |
| selector 未证明优于直接验证 | `benchmarks/diagnostic_selection_feasibility_v1/{FEASIBILITY_REPORT.md,REPLAY_RESULTS.json,INPUT_SNAPSHOT_BINDING.json}`；`scripts/analysis/diagnostic_selection_feasibility_v1/` | `06_selection_v011.tex`；表；附录V | 1005是重组分析记录；无新原生运行；MBPP U2未知；只否定两指定候选的现有证据 |
| RTX qualified serialization GM .677351 | 既有 `rtx_v4_values_v087.tex` 与匿名包保留 historical calculators/source exports | Diagnoses；RTX V4附录 | 19历史任务、post-prefill、instrumented边界；不能给新bridge定价 |
| 358H prompt-GM 零额外开销上界 .837219/.844840 | `derived_values_v086.tex`、`direct_id_values.tex`及历史匿名计算器 | Diagnoses；derived附录 | 条件性上界，非实测加速，也非体系结构不可能性 |
| M4 Guard/Always 1.027076，固定模式机会 .06915% | `runtime_values.tex`、`07_runtime.tex`及保留 historical calculators | Runtime；附录T.2 | Guard慢于Always；fixed-mode opportunity不代表动态oracle |

本文两个不同的1005记录数不应相加或互换：干预单元360+645；离线分析重组285+360+360，包含旧 reference、预测与重复使用的已有数据。bridge 171 单独计数。严格边界包括长度+终端ID；只按停止类别的57/57不能替代 strict boundary 的54/57。

匿名包包含保留 v0.10.0 evidence ZIP 的确切字节、新 wrapper 和原 selector source/inputs/recomputed outputs。内层 manifests 及外层 artifact manifest 各自绑定内容。它不能认证未包含模型/runtime的 bytes，也不能证明绝对实验时间。
