# B570 有限闭环实验报告

预算档：**NIGHT**。当前状态：**MEASURED_CORE_COMPLETE_PENDING_DELIVERY**。最终交付状态以 `DELIVERY_VERIFIED.json` 为准。

本批次独立追加 PR #63，未改论文、旧实验、驱动或系统设置。驱动差异按用户指示记录；旧参考仍通过本轮实际生成核对。原预算和中断记录保留，恢复窗口见 `RECOVERY_AMENDMENT.json`。

## 1. 旧修复与两个输入队列

旧24个 HumanEval 的 R/N0/N1 各两次及五个诊断/控制的 matched bridge 完成。新共享24个 MBPP 与项目审计范围内未执行的 8 个 MBPP 独立计数。共享输入已被 RTX 使用，不称项目未执行。

| 队列 | R | matched T | ordinary native | 原修复 native |
|---|---:|---:|---:|---:|
| shared | PASS | PASS | PASS | PASS |
| unused | PASS | FAIL | PASS | FAIL |

旧 G0 中 ordinary native 的四个历史任务失败按原合同保留；G0 PASS 表示正确复现历史参考、原失败与修复，不把 N0 全部称为合格。费用对照的 matched continuation 输出槽修订及新 33 请求/9 热身资格另见 MATCHED_RESERVATION_AMENDMENT.json 与 G0_TARGET_FINAL.json。

本轮使用现有 Windows 桌面环境。旧任务工程探针期间曾观察到动态壁纸视频解码占用；临时暂停操作被自动审批拒绝，未执行，未绕过，未结束用户程序。ENVIRONMENT_OBSERVATIONS.json 保留快照范围。正式费用是该实际桌面条件下的平衡重复结果；没有把 shared-memory 计数解释成分页证明，也没有把耗时变化归因于壁纸、温度或频率。

完整 IDs、首 runtime EOG、长度和 cap 契约逐项比较；native 原始 overshoot 保留并计入实际工作与费用，不以输出文本或重分词代替直接 IDs。失败任务和首次差异见 `B_SUMMARY.json`。暴露审计依据可访问历史及固定 RTX 收据；未取得的 RTX 巨型历史没有假称独立扫描。

## 2. 宽度与实际长度

| k / continuation UB | cap | 共享 matched/native | 旧长 matched/native |
|---|---|---|

设备枚举修复：第四轮 B 与部分长锚点实际使用 UHD730，共190条完整请求（含12条热身）列为 INFRA_REJECTED_PLATFORM，原字节和计时保留；它们不构成 B570 科学结果。恢复只重做平台身份不合格的请求，完成的 B570 科学结果复用。原截止时刻保留；超时缺失仍为 PARTIAL。详见 DEVICE_RECOVERY_AMENDMENT/FREEZE 与独立核验。

原 k2 / target prefill128 → continuation1 长锚点：84/84 正式请求完成，cap256、512 的 ordinary R / matched T / N1 全部保留参考。任务仍为冻结4个共享输入和3个旧长输入，没有据输出更换队列。实际普通参考终点如下：

| cap | task | reference tokens | endpoint |
|---|---|---:|---|
| 256 | HumanEval/31 | 175 | EOG |
| 256 | HumanEval/49 | 139 | EOG |
| 256 | HumanEval/81 | 256 | CAP |
| 256 | MBPP/124 | 19 | EOG |
| 256 | MBPP/234 | 14 | EOG |
| 256 | MBPP/415 | 142 | EOG |
| 256 | MBPP/439 | 27 | EOG |
| 512 | HumanEval/31 | 175 | EOG |
| 512 | HumanEval/49 | 139 | EOG |
| 512 | HumanEval/81 | 261 | EOG |
| 512 | MBPP/124 | 19 | EOG |
| 512 | MBPP/234 | 14 | EOG |
| 512 | MBPP/415 | 142 | EOG |
| 512 | MBPP/439 | 27 | EOG |

长输出通过不等于完整长驻 reset 面板通过。

用户在上一截止后明确授权继续完成平台闭环；续跑时窗另存 CONTINUATION_AMENDMENT.json，原 PARTIAL 报告/截止/失败保留在 engineering-continuation-v1。原输入、配置与数值程序未重选，已完成有效科学输出不重复生成。一个截止时已完整写出的请求经 CPU 核对回收，见 CPU_PAYLOAD_RECOVERY.json；host 延迟为包含停机清理的上界，C++ 计时原样保留。

用户明确暂停后于晚间授权恢复，并报告已关闭屏保。暂停位置和原结果保留；另有一个暂停时已经写完的请求经 CPU 核对回收，避免重复。环境变化仅按用户描述记录，不宣称动态壁纸已完全退出或性能变化的因果来源。B/部分D属于较早环境，后续C/E属于续跑时段，各自队列/阶段费用分别解释。见 PAUSE_RESUME_AMENDMENT.json 与 CPU_PAYLOAD_RECOVERY_PAUSE.json。

旧任务工程宽度 proof 另保留 4 条完整 native 参考偏离，详见 G0_WIDTH.json。它们位于原 C/E 队列之外的旧控制输入；C/E 在自身固定队列通过也不能抹去这些反例或扩张为原24任务的普适资格。

| k / continuation UB | cap | 共享 matched/native | 旧长 matched/native |
|---|---|---|---|
| 1 / 2 | 128 | PASS/PASS | PASS/PASS |
| 1 / 2 | 256 | PASS/PASS | PASS/PASS |
| 1 / 2 | 512 | PASS/PASS | PASS/PASS |
| 3 / 4 | 128 | PASS/PASS | PASS/PASS |
| 3 / 4 | 256 | PASS/PASS | PASS/PASS |
| 3 / 4 | 512 | PASS/PASS | PASS/PASS |
| 5 / 6 | 128 | PASS/PASS | PASS/PASS |
| 5 / 6 | 256 | PASS/PASS | PASS/PASS |
| 5 / 6 | 512 | PASS/PASS | PASS/PASS |
| 7 / 8 | 128 | PASS/PASS | PASS/PASS |
| 7 / 8 | 256 | PASS/PASS | PASS/PASS |
| 7 / 8 | 512 | PASS/PASS | PASS/PASS |

所有宽度均固定 target prefill128、draft prefill/continuation1。ctx1024，threads10，FA off，greedy seed123。每个 cap 自然 EOG 或上限结束；实际长度、suffix 和首次差异见 C 明细。容量与实际 query 数不同；旧任务扩展 proof、D/E capture 的实际图观察单独保留，未捕获的逐任务 micrograph 范围记 missing，不猜测 kernel 启动数。

## 3. 原锚点的长驻状态

- D_RESET: COMPLETED_PASS，96/96 请求，6 热身。
- D_TIMING: COMPLETED_PASS，96/96 请求，4 热身。

每请求清两模型 KV、采样器、pending 和历史；模型每会话只加载一次、无 prompt/KV cache、单请求串行服务。capture-on 资格与 capture-off 费用分开，不能称多并发吞吐。

## 4. 真实效率与额外收益

| 阶段 / 队列 | 基线 → 候选 | 输出资格 | 生成比 | 整请求比 |
|---|---|---|---:|---:|
| B / project_unused_within_accessible_audit | T_matched → N1_repaired | 失败，仅诊断费用 | 0.8001 | 0.7023 |
| B / project_unused_within_accessible_audit | R_reference → N1_repaired | 失败，仅诊断费用 | 0.2455 | 0.2285 |
| B / project_unused_within_accessible_audit | N0_ordinary → N1_repaired | 失败，仅诊断费用 | 1.0100 | 1.2282 |
| B / project_unused_within_accessible_audit | R_reference → N0_ordinary | 合格 | 0.2430 | 0.1861 |
| B / cross_platform_shared_project_exposed | T_matched → N1_repaired | 合格 | 0.8040 | 0.6935 |
| B / cross_platform_shared_project_exposed | R_reference → N1_repaired | 合格 | 0.1885 | 0.1791 |
| B / cross_platform_shared_project_exposed | N0_ordinary → N1_repaired | 合格 | 0.9995 | 1.2471 |
| B / cross_platform_shared_project_exposed | R_reference → N0_ordinary | 合格 | 0.1886 | 0.1436 |
| D_TIMING / cross_platform_shared_project_exposed | T_matched → N1_repaired | 合格 | 0.8279 | 0.7278 |

比值为基线耗时/候选耗时：每任务取重复中位数，再求任务几何平均。绝对 ms 与每任务分布见 derived CSV。生成计时包括 sampler/batch 初始化、pending 源采样、真实状态序列化/载入/往返校验、草稿、验证、rollback、最终设备同步；整请求另含 prefill/reset/cleanup。证据文件落盘在 C++ 计时外，真实 host 延迟另保留。模型/上下文冷加载和热身单独列账。失败输出费用不称无损加速。

E 决定：**NO_GO_PILOT**。E 的实际计划、pilot、选择、独立确认仅以已经生成的对应文件为依据；缺少对应文件的阶段为未执行，不称新增收益。布局原型本批次 `NOT_IMPLEMENTED`，未改变发布 Vulkan shader 算术。

## 5. 状态证据与 RTX 迁移边界

局部机制状态：**NOT_CAUSALLY_IDENTIFIED**。

真实 prefill 状态往返、source 不变、pending 首样本及克隆 sampler 的链/history/seed均有证据。机制诊断的实际执行及自然父轨迹以 MECHANISM.json 和原始 MECHANISM 请求为依据；C 全矩阵没有失败配置时，本次诊断按冻结 C 选择规则为 GATED_BY_QUALIFICATION；这不抹去 B_unused /72 的失败。因果状态仍为 NOT_CAUSALLY_IDENTIFIED。已有 prefill 证据来自 G0、资格控制和实际完成的请求。生成没有使用参考 ID、强制前缀或未来 proposal tape。当前前端缺少自然中途的完整 donor+draft+post-sample sampler checkpoint，未执行 2×2 状态反事实，不称过去状态或当前布局是唯一原因。top1/top2 margin 与指定参考 EOS/替代 token margin 分开，后者未取得完整 logits 时明确 missing。opaque sampler 字节和唯一 Vulkan kernel 身份未认证。

RTX 的局部布局资格和增加 k 可能变慢的经验用作设计依据；RTX k3/UB4、CUDA、global UB1参考不作为 B570 答案。共享24个输入的逐任务平台行见 `RTX_B570_COMPARISON.csv`；两平台参考、ctx、threads、后端及原始 suffix 契约不同，不作直接 token 等同或单变量硬件因果结论。

## 6. 投入决定与可恢复证据

当前选择：`NO_GO_PILOT`；核心完整性：`True`。合格但更慢就是无额外效率收益；无法完成的阶段保持 PARTIAL。本轮核心完成1456/1456个正式请求；剩余分母逐阶段见下表。核心未完成时，即使归档/回读通过仍为 PARTIAL；只有原合同所有核心测量或科学资格门控以及独立核验、实际恢复和远端回读通过才支持有限范围闭环。

| 阶段 | 状态 | planned | complete | unexecuted | warm |
|---|---|---:|---:|---:|---:|
| G0 | COMPLETED_PASS | 144 | 144 | 0 | 7 |
| G0_BRIDGE | COMPLETED_PASS | 20 | 20 | 0 | 4 |
| B | COMPLETED_SCIENTIFIC_FAIL | 512 | 512 | 0 | 16 |
| C | COMPLETED_PASS | 504 | 504 | 0 | 72 |
| C_ANCHOR_LONG | COMPLETED_PASS | 84 | 84 | 0 | 12 |
| D_RESET | COMPLETED_PASS | 96 | 96 | 0 | 6 |
| D_TIMING | COMPLETED_PASS | 96 | 96 | 0 | 4 |
| G0_REBUILT | COMPLETED_PASS | 30 | 30 | 0 | 6 |
| G0_SHAM | COMPLETED_PASS | 20 | 20 | 0 | 4 |
| G0_WIDTH | COMPLETED_SCIENTIFIC_FAIL | 16 | 16 | 0 | 8 |
| G0_TARGET_FINAL | COMPLETED_PASS | 33 | 33 | 0 | 9 |
| G0_ETA | COMPLETED_PASS | 22 | 22 | 0 | 11 |
| G0_ETA_N0 | COMPLETED_PASS | 2 | 2 | 0 | 1 |
| G0_DEVICE_REQUALIFICATION | COMPLETED_PASS | 30 | 30 | 0 | 6 |
| G0_CONTINUATION_QUAL | COMPLETED_PASS | 15 | 15 | 0 | 3 |
| E_CAPTURE | COMPLETED_PASS | 6 | 6 | 0 | 6 |
| E_PILOT | COMPLETED_SCIENTIFIC_FAIL | 144 | 144 | 0 | 12 |
| E_CONFIRM | GATED_BY_QUALIFICATION | 512 | 0 | 512 | 0 |
| E_LONG | GATED_BY_QUALIFICATION | 84 | 0 | 84 | 0 |
| E_D_RESET | GATED_BY_QUALIFICATION | 96 | 0 | 96 | 0 |
| E_D_TIMING | GATED_BY_QUALIFICATION | 96 | 0 | 96 | 0 |
| MECHANISM | GATED_BY_QUALIFICATION | 0 | 0 | 0 | 0 |

## C 的独立匹配成本

| 队列 | k / UB | cap | 基线 → 候选 | 输出资格 | 生成比 | 整请求比 |
|---|---|---|---|---|---:|---:|
| cross_platform_shared_project_exposed | 5 / 6 | 512 | T_matched → N_candidate | 合格 | 0.9297 | 0.8527 |
| cross_platform_shared_project_exposed | 5 / 6 | 512 | R_reference → N_candidate | 合格 | 0.1460 | 0.1471 |
| cross_platform_shared_project_exposed | 1 / 2 | 128 | T_matched → N_candidate | 合格 | 0.9208 | 0.8318 |
| cross_platform_shared_project_exposed | 1 / 2 | 128 | R_reference → N_candidate | 合格 | 0.1684 | 0.1666 |
| cross_platform_shared_project_exposed | 5 / 6 | 128 | T_matched → N_candidate | 合格 | 0.9481 | 0.8706 |
| cross_platform_shared_project_exposed | 5 / 6 | 128 | R_reference → N_candidate | 合格 | 0.1417 | 0.1431 |
| exposed_long_supplement | 3 / 4 | 128 | T_matched → N_candidate | 合格 | 1.3458 | 1.0483 |
| exposed_long_supplement | 3 / 4 | 128 | R_reference → N_candidate | 合格 | 0.4576 | 0.3711 |
| exposed_long_supplement | 5 / 6 | 256 | T_matched → N_candidate | 合格 | 1.0681 | 0.8653 |
| exposed_long_supplement | 5 / 6 | 256 | R_reference → N_candidate | 合格 | 0.5698 | 0.4732 |
| cross_platform_shared_project_exposed | 1 / 2 | 512 | T_matched → N_candidate | 合格 | 0.9887 | 0.8867 |
| cross_platform_shared_project_exposed | 1 / 2 | 512 | R_reference → N_candidate | 合格 | 0.1800 | 0.1769 |
| cross_platform_shared_project_exposed | 7 / 8 | 256 | T_matched → N_candidate | 合格 | 0.8836 | 0.8166 |
| cross_platform_shared_project_exposed | 7 / 8 | 256 | R_reference → N_candidate | 合格 | 0.1354 | 0.1375 |
| cross_platform_shared_project_exposed | 7 / 8 | 128 | T_matched → N_candidate | 合格 | 0.9145 | 0.8416 |
| cross_platform_shared_project_exposed | 7 / 8 | 128 | R_reference → N_candidate | 合格 | 0.1381 | 0.1397 |
| cross_platform_shared_project_exposed | 5 / 6 | 256 | T_matched → N_candidate | 合格 | 0.8951 | 0.8215 |
| cross_platform_shared_project_exposed | 5 / 6 | 256 | R_reference → N_candidate | 合格 | 0.1452 | 0.1463 |
| cross_platform_shared_project_exposed | 7 / 8 | 512 | T_matched → N_candidate | 合格 | 0.9213 | 0.8485 |
| cross_platform_shared_project_exposed | 7 / 8 | 512 | R_reference → N_candidate | 合格 | 0.1420 | 0.1436 |
| exposed_long_supplement | 1 / 2 | 512 | T_matched → N_candidate | 合格 | 0.8506 | 0.7057 |
| exposed_long_supplement | 1 / 2 | 512 | R_reference → N_candidate | 合格 | 0.5166 | 0.4373 |
| exposed_long_supplement | 1 / 2 | 128 | T_matched → N_candidate | 合格 | 0.9261 | 0.7240 |
| exposed_long_supplement | 1 / 2 | 128 | R_reference → N_candidate | 合格 | 0.4708 | 0.3797 |
| cross_platform_shared_project_exposed | 3 / 4 | 128 | T_matched → N_candidate | 合格 | 0.9886 | 0.9052 |
| cross_platform_shared_project_exposed | 3 / 4 | 128 | R_reference → N_candidate | 合格 | 0.1387 | 0.1402 |
| exposed_long_supplement | 7 / 8 | 128 | T_matched → N_candidate | 合格 | 1.0300 | 0.8068 |
| exposed_long_supplement | 7 / 8 | 128 | R_reference → N_candidate | 合格 | 0.4608 | 0.3740 |
| exposed_long_supplement | 3 / 4 | 256 | T_matched → N_candidate | 合格 | 1.0346 | 0.8428 |
| exposed_long_supplement | 3 / 4 | 256 | R_reference → N_candidate | 合格 | 0.5472 | 0.4573 |
| cross_platform_shared_project_exposed | 3 / 4 | 512 | T_matched → N_candidate | 合格 | 0.9655 | 0.8848 |
| cross_platform_shared_project_exposed | 3 / 4 | 512 | R_reference → N_candidate | 合格 | 0.1536 | 0.1545 |
| exposed_long_supplement | 5 / 6 | 128 | T_matched → N_candidate | 合格 | 1.0853 | 0.8389 |
| exposed_long_supplement | 5 / 6 | 128 | R_reference → N_candidate | 合格 | 0.4803 | 0.3851 |
| exposed_long_supplement | 7 / 8 | 256 | T_matched → N_candidate | 合格 | 1.1434 | 0.9132 |
| exposed_long_supplement | 7 / 8 | 256 | R_reference → N_candidate | 合格 | 0.6029 | 0.4940 |
| cross_platform_shared_project_exposed | 1 / 2 | 256 | T_matched → N_candidate | 合格 | 0.9206 | 0.8336 |
| cross_platform_shared_project_exposed | 1 / 2 | 256 | R_reference → N_candidate | 合格 | 0.1674 | 0.1660 |
| exposed_long_supplement | 3 / 4 | 512 | T_matched → N_candidate | 合格 | 1.0294 | 0.8400 |
| exposed_long_supplement | 3 / 4 | 512 | R_reference → N_candidate | 合格 | 0.5674 | 0.4753 |
| exposed_long_supplement | 1 / 2 | 256 | T_matched → N_candidate | 合格 | 0.8900 | 0.7317 |
| exposed_long_supplement | 1 / 2 | 256 | R_reference → N_candidate | 合格 | 0.5391 | 0.4524 |
| exposed_long_supplement | 5 / 6 | 512 | T_matched → N_candidate | 合格 | 1.1109 | 0.8943 |
| exposed_long_supplement | 5 / 6 | 512 | R_reference → N_candidate | 合格 | 0.5916 | 0.4882 |
| cross_platform_shared_project_exposed | 3 / 4 | 256 | T_matched → N_candidate | 合格 | 0.8701 | 0.8013 |
| cross_platform_shared_project_exposed | 3 / 4 | 256 | R_reference → N_candidate | 合格 | 0.1408 | 0.1423 |
| exposed_long_supplement | 7 / 8 | 512 | T_matched → N_candidate | 合格 | 1.1345 | 0.9164 |
| exposed_long_supplement | 7 / 8 | 512 | R_reference → N_candidate | 合格 | 0.6021 | 0.4989 |

## 固定 UB 的完整效率 pilot

以下均为已暴露选择队列上的探索费用，独立确认未完成时不能作新增收益或部署结论。每配置24请求、两轮；共享8任务与旧4诊断任务分别核算。

| 配置 | 全 pilot 参考 | 进入确认门槛 | 全队列生成/整请求比 | 共享生成/整请求比 | 旧诊断生成/整请求比 |
|---|---|---|---|---|---|
| E_k1_ub2 | False | False | 1.1786/1.1567 | 1.1252/1.1115 | 1.2933/1.2526 |
| N1_repaired | True | False | 1.0000/1.0000 | 1.0000/1.0000 | 1.0000/1.0000 |
| E_k2_ub2 | False | False | 1.0713/1.0644 | 1.0464/1.0420 | 1.1227/1.1106 |
| E_k3_ub2 | False | False | 1.1356/1.1202 | 1.1123/1.0997 | 1.1837/1.1624 |
| E_k5_ub2 | False | False | 1.0386/1.0358 | 1.0312/1.0276 | 1.0536/1.0524 |
| E_k7_ub2 | False | False | 0.9731/0.9772 | 0.9765/0.9782 | 0.9664/0.9751 |

独立 CPU 验证：PASS，363698 项检查，1961 条完整记录，零模型 forward。失败 attempts 和此前工程记录全部归档。外部权重/运行库及旧 capsule 是独立哈希依赖，不进入 PR 或新包 payload。

本报告不推断 HumanEval 功能正确率、能耗收益、普适最小范围定理或唯一内核原因。

## 实际工作量与缺失观察

逐请求 caller 次数/输入数量、草稿与接受数量/比例、真实 prefill 状态转移次数及 capture 中的 micrograph 观察见 WORK_ACCOUNTING.json / CSV；已在干净恢复的同一原始字节上独立重算一致。capture-off 没有图数量，统一记 missing。观察器未逐项记录 synchronization 次数，不能从源码估计或把 KV mutation 当同步；完整同步费用仍包含在冻结 C++ 计时中。图观察与 API 调用均不称 kernel 启动数。

| 阶段 | 条件 | 请求 | target calls | draft calls | drafted | accepted | accepted/drafted |
|---|---|---:|---:|---:|---:|---:|---:|
| D_TIMING | N1_repaired | 48 | 628 | 1692 | 1064 | 844 | 0.7932 |
| D_TIMING | T_matched | 48 | 1436 | 0 | 0 | 0 | N/A |
| E_PILOT | E_k1_ub2 | 24 | 920 | 1792 | 872 | 722 | 0.8280 |
| E_PILOT | E_k2_ub2 | 24 | 680 | 1944 | 1264 | 966 | 0.7642 |
| E_PILOT | E_k3_ub2 | 24 | 564 | 2112 | 1548 | 1086 | 0.7016 |
| E_PILOT | E_k5_ub2 | 24 | 452 | 2472 | 2020 | 1204 | 0.5960 |
| E_PILOT | E_k7_ub2 | 24 | 414 | 2976 | 2562 | 1248 | 0.4871 |
| E_PILOT | N1_repaired | 24 | 678 | 1938 | 1260 | 968 | 0.7683 |
