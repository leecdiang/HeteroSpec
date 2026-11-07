# 全量实验去向与证据边界

所有路径相对仓库根，读取基线固定为 `21aa7b29142a1e3b7130b8e4a6a252777a91af80`。原研究报告中的“下一步”“未合并”等是当时状态，必须结合后续closeout理解。这里不重新执行private raw，不声称逐项验证所有历史测量真实性。

主文=承担核心论证；S1=补充中的完整可查记录；历史=保留原文件/引用，不再拿来建立新headline。后期CPU closeout修正解释时，以修正为准，同时保留原失败和原报告。

| 实验/材料 | 关键事实及允许结论 | 去向与作用 | 第一手仓库入口 |
|---|---|---|---|
| 早期四平台概览、M4代表24Q/独立HumanEval30 | 不同backend/OS/runtime一起变化；历史M4/RTX/B570是re-tokenized text，358H direct IDs | S1；说明项目起点与历史合同，不作统一硬件排名 | `paper/jsa/manuscript_v013/historical_sources/tables/01_platforms_v05.tex`；`historical_sources/appendix.tex`；`benchmarks/m4_confirmatory_24q/`；`m4_code_conditioned_30q/` |
| 早期RTX/B570/358H对照与阈值 | isolated draft优势不保证stateful收益；能耗域和timer不统一 | S1；保留成本分解/能耗范围，不转写为晚期repair能效 | `benchmarks/root_cause_12q/`；`windows_humaneval_replication_30q/`；`b570_backend_control/`；`358h_threshold_validation/`；历史appendix |
| M4正式runtime | 60 tasks×3 conditions×3 reps=540；fixed/guard各180/180；1.346894×/1.311387×；guard慢2.71% | 主文RQ3紧凑案例，完整表S1；反驳未经支持的controller收益 | `benchmarks/m4_runtime/FORMAL_REPORT.md`、`GUARD_ALWAYS_SECONDARY_REPORT.md`；v013 `evidence/M4_FORMAL_ANALYSIS.json` |
| M4 hindsight二动作oracle与分组 | fixed相对oracle仅1.000692；HE30与SpecBench30收益不同 | 主文简述、S1分组；不是任何intra-request policy的上界 | 同上；v013 `tables/workload_strata.tex` |
| B570 direct-ID资格 | 更强输出gate必须单独建立，不给旧timing追授资格 | S1合同演进 | `benchmarks/b570_direct_id_v1/FORMAL_REPORT.md`；历史 `tables/direct_id_values.tex` |
| B570 prospective predictor | discovery36/36；reserved72/72 predictor/live，reference60/72，24 tasks×3 | RQ1背景压缩/S1完整；预测native偏差≠恢复参考 | `benchmarks/b570_mechanism_v08/`；历史 `sections/05_diagnoses.tex` |
| B570同状态单块干预 | 72 runs/24 tasks；score均变，立即decision不变；18 runs/6 tasks下游变 | **主文RQ1必须补回**；局部离散null不能代替trajectory验证 | `benchmarks/b570_partition_intervention_v1/DELIVERY_REPORT.md`、`STUDY_PROTOCOL.md` |
| RTX H1迁移失败 | H1 24/36未过36/36门槛；reserved inference=0，H2此study未实现 | S1＋RQ1一句；不是整个项目“复现失败” | `benchmarks/rtx_transfer_latency_v1/prediction/REPORT.md` |
| RTX独立proposal replay v2 | H2/live及R-only/live72/72，reference60/72；24 tasks | S1预测层证据；不把输出replay等同cheap online repair | `benchmarks/rtx_independent_proposal_replay_v2/FORMAL_REPORT.md` |
| RTX初期direct-ID与独立latency arm | 各自gate/端点与测时；不能把不同campaign拼成配对 | S1原报告，历史数字按原表保留 | `benchmarks/rtx_direct_id_v1/`、`rtx_direct_id_v2/`、`rtx_transfer_latency_v1/latency/REPORT.md` |
| RTX V3停止 | 126有效formal前缀、2失败、448未到达；无完整正式速度结论 | S1失败/审计账本，不池化进入V4 | `benchmarks/rtx_trajectory_cost_v3/FINAL_REPORT.md` |
| RTX V4预测与串行成本 | 19任务；P/R和R-only57/57；batched51/57被blocked；global serial57/57但0.677351× | 主文RQ3一项合格负例，S1协议/host amendment；不与后期timer构成优化曲线 | `benchmarks/rtx_trajectory_cost_v4/FINAL_REPORT.md` |
| B570 prefill干预 | T0/N0、T1/N1各72/72；reference60/72→72/72，4修复20控制；含pending/state handoff | 主文RQ1短对照/S1全部；非纯KV或纯prefill单算子原因 | `benchmarks/b570_prefill_diagnostic_v1/STUDY_REPORT.md`、`DECISIONS.md` |
| RTX continuation干预 | 43 tasks×3；两条件预测各129/129；reference均117/129；HE /15修复、/25回归；MBPP/304仍失败但index33改变 | 主文RQ1动机；aggregate unchanged不能写成全体no-op | `benchmarks/rtx_target_verification_intervention_v1/STUDY_REPORT.md` |
| ordinary U2 bridge | 19 exposed×3 conditions×3=171；U2=N1 57/57严格边界；非state equivalence | 主文简述/S1详表；复杂复现器的必要性受简单baseline约束 | `benchmarks/rtx_target_only_bridge_v1/STUDY_REPORT.md` |
| 离线selector feasibility | RTX enumeration/proxy都114且abstain；B570 direct72/proxy144；未知counterfactual保持unknown | 主文一段或discussion，S1完整；不得重新包装成已实现的有效selector | `benchmarks/diagnostic_selection_feasibility_v1/FEASIBILITY_REPORT.md` |
| RTX效率pilot #58 | FA-on/UB512四probe k4合格1.492×请求，但扩大面板小模型18/24、片段21/24、混合15/24；各配置reference会变 | S1；说明既有方法确有收益但不能免除全panelgate；不借其3.9×合成case撑当前headline | `benchmarks/rtx_efficiency_pilot_v1/REPORT.md` |
| RTX自然cross与局部图 #59 | 24 donor/48 forks/24 sham；/15 path、/25 interaction、两局部null；70/72 generated K/V不同 | 主文RQ1核心；token不同/张量不同不唯一定位kernel | `benchmarks/rtx_consistency_contract_v1/REPORT_ZH.md`；v013 `evidence/RTX_NATURAL_CROSSES.json` |
| RTX实现版本成本 #59 | 串行/逐query/并行query各有负正结果；strict matched19任务1.256×生成/1.077×请求 | RQ2解释实现；详细成本S1，不能拿插桩版本比率当同条件最终增益 | 同上及其source、qualification、cost导出 |
| phase消融 #60 | 16 masks×4×2；passing3/7/11/15；scope-cost19×3×6；mask3/15额外生成仅1.003569未过1.03门槛 | **主文RQ2核心**；最小资格范围≠显著额外速度 | `benchmarks/rtx_consistency_phase2/RESULTS.zh-CN.md`；v013 `evidence/RTX_PHASE_FACTORIAL.csv` |
| 冻结RTX新输入 #62＋CPU强R #66 | 24 MBPP×4条件×4=384，各96合格；R/C gen1.170124、request1.741569；M/C1.169238/1.035071；R/M request1.682560 | **主文RQ2/3 headline**；7请求回归、round2反转；普通R比较是事后CPU重析已有付费数据 | `benchmarks/rtx_closeout_bcd/REPORT.md`；`benchmarks/rtx_pr62_cpu_reference_closeout_v1/REPORT.zh-CN.md`、`SOURCE_TIMER_AUDIT.md`；v013 rtx66 CSV |
| RTX宽geometry/长cap #62 | /229在k5/UB6与k7/UB8失败；两cap是同task；最大实际长度261 | 主文RQ2失败边界；不是512token全程已验证 | `benchmarks/rtx_closeout_bcd/results/C_BOUNDARY_SUMMARY.json`及REPORT |
| RTX固定UB4宽draft #62 | k3/5/7均qualify；k7相对k3 0.829442/0.889868；相对matched0.997404/0.950353 | 主文RQ3关键反例；calls和micrographs来自不同粒度，不能伪造kernel剖面 | v013 `evidence/RTX_FIXED_UB_RESULTS.json`；`benchmarks/rtx_closeout_bcd/results/C4_RESULTS.json` |
| RTX resident reset #62 D | 有限顺序循环，matched约1.181×/1.039× | S1；不称并发或生产throughput | `benchmarks/rtx_closeout_bcd/results/D_PUBLIC_RESULTS.json` |
| B570原closeout及规范补齐 #63 | 原core1456完成；新输入/72失败；五UB2候选失败；旧长局部positive保留；当时无natural state cross | 主文失败一段/S1完整；后续#64才有真实cross，不能回填旧study | `benchmarks/b570_closeout_overnight_v1/REPORT.md`；`normative_audit_20261007/REVIEW_REPORT.md` |
| B570自然cross/phase-binding #64＋CPU #65 | 3tasks×2 contexts；12shams；/145 /42 interactions，/72 state effect且列相同；C12、D112 endpoint资格；E119/120 | 主文RQ1与3；raw suffix及unknown不删；state×whole recipe，非纯UB | `benchmarks/b570_mechanism_pilot_v1/REPORT.zh-CN.md`；`benchmarks/b570_pr64_cpu_closeout_v2/REPORT.zh-CN.md` |
| B57015正式成本 | candidate/R/matched各30完整；oldN1仅14完整task pairs；R/C0.282588/0.201290；M/C0.285761/0.205704；oldN1/C3.993/2.634 | **主文RQ3强反例**；赢旧实现不代表部署收益；suffix全额计费 | v013 `evidence/b57065/COSTS_RECOMPUTED.csv`、qualification和work breakdown |
| 358H stateful边界 | CPU/NPU实际0.73392/0.35166；prompt target-floor ceilings0.8372/0.8448，至少16.28%/15.52% target-work削减预算 | 主文RQ3紧凑边界/S1全分解；不是NPU/异构推理不可能 | v013 `historical_sources/sections/03_methodology.tex`、`05_diagnoses.tex`、`tables/followup_values_v085.tex`及历史appendix |

## 数字使用规则

- 独立任务、重复运行、condition、fork、内部decision event分别报告，禁止相加得到“数千独立样本”。
- RTX本次full response与B570 first-EOG/cap128 endpoint不同；historical text equality更弱。完整raw suffix比较缺失则写unknown。
- 每条speed给baseline/candidate、timer、任务集、重复合并方式；358H的median-of-paired-ratios不偷换为ratio-of-medians。
- #63局部正结果也保留，不能为了B570 negative narrative抹掉。反过来不能用它替换失败的全panel或#64/65强R比较。
- S1必须提供表中各组详细结果或明确指向对应可访问材料。不要只说“见GitHub”，也不要求把所有大归档塞进PDF。
- 本轮新执行的是已有CPU verifier重跑，范围在VALIDATION；其余为报告/源码/导出审阅。未重复完整GPU实验，未核查所有私有payload。
