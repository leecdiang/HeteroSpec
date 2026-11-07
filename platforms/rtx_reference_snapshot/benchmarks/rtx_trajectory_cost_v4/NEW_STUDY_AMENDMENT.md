# V4 修复与独立新研究协议

用户在 V3 失败终止与完整证据交付后，直接授权“自行修复后完成实验……完善论文……得到同样有价值的结论，也可以继续”。这份新协议落实该后续授权。旧 V3 的两个失败 attempt、72/54 有效前缀、F0/F1/B_START/COMPLETE 和 Draft PR #48 全部保留，不改写、不补为 prospective、不复用为新正式样本。

修复的范围是原生 committed-ID 采集及独立核验：实际 pinned b10839 源码先检测 budget，再检测 EOG，所以 inclusive EOG 恰为第 128 个 token 时会同时记录 limit 与 EOS。新采集器保存两条观测，将终止原因规范为 EOS。缺失、重复、反序、非 EOG 的双标记及提前出现的 EOG 均拒绝。实际 vocab-only API 查询确认 EOG IDs 为 128247、151643、151645、151662、151663、151664；不创建 context 或进行模型推理。两份原失败日志只是只读回归输入，旧状态保持 OPERATIONAL_FAILURE。

曝光审计继承 V3 已完整核验的 93,176 项清单和 138 个保守排除，再扫描既有原始进程记录，包括 failed/in-flight。V3 新曝光 2、161、86、157、16、158、59，共 7 个任务，必须排除。新的 19 个样本是全部剩余未曝光任务；按新固定 salt RTX_TRAJECTORY_SUFFICIENCY_V4|reserved|20261002| 排序，不依据模型结果选取或替换。顺序为 143、31、25、81、15、141、142、18、136、99、148、140、87、76、26、49、40、109、66。模式 A19_B19；总排除 145。

A 仍比较两个预定候选：target-only UB2 与 per-round 独立 P/R、fresh R-only replay。19×3×4=228 次 pre-live；完整稳定且 H2/R-only 57/57 后，封存全部数组和 tape，发布并完整取回 F2，再执行 19×3=57 次原生 batched live。合计 A 285 个条件。A 候选错配不是改候选或停掉有利对照的理由；完整有限集合结论、reference-divergent 分类和 first divergences 均保留。

B 使用同一冻结 19 IDs，但执行 171 次新的计时条件，不共享 A 观测。57 个 block 由六种 permutation 各 9 次，再加预定三种 cyclic rotation 构成；每个条件在三个位置各出现 19 次，permutation 各 9 或 10 次。固定打乱 seed 2026100203。每条候选路径分别 gate 全部 57 个新 reference/candidate ID pairs；只有 qualified 路径允许 speedup/CI。仍用每 prompt 三重复中位数、reference/candidate 比值的几何均值和 10,000 次 prompt-paired bootstrap，固定 seed 2026100204。ratio >1 表示候选更快。失败路径速度/CI 为 null；不做有利子集。加载/初始 prefill/teardown 不在主计时区间，日志、响应、同步与释放仍包含，不宣称吞吐或能耗。

正式计划共 456 个条件，来自 19 个独立 prompt，不等于 456 个独立样本。样本量与旧 24-task 方案的差异必须在报告和论文解释中披露，不能把旧 attempt 与新 cohort 合并成更大的 prospective 分母。

工程先做 30 次 fresh HumanEval/59 exposed-only 修复资格（3 重复×10 条件），保留 reference/replay 和三类原版/计时版逐数组 gate，并要求至少 12 次真实同时 EOS/cap。再重新执行原 360 次 base engineering、40 次 observer/endpoint 检查和 3 个 constructed contexts；五个 mandatory gate 各 36/36、20 个 observer pairs、15 类原始/统计负例与另行 EOS/cap 损坏回归都需要实际通过。工程条件总数 430；旧工程只作为回归依据，不冒充本次 fresh 条件。

模型、数据、释放版 numeric DLL、P/R worker.cpp、计时 patch 与 executable、sampler、KV、UB 配置、observer、计时定义和 thermal/idle 规则保持相同字节或定义。旧构建产物按全量 SHA-256 复用到独立未提交工作目录，fresh engineering 重新资格验证，不宣称重新编译数值 backend。tokenizer 的唯一新增项是 vocab-only EOG 身份输出。归档长路径、标准 tar hardlink 与一次 gzip 传输解压在本次 F0 前作为冻结实现纳入核验，逻辑成员字节不变。

F0/F1/F2/B_START 均保留精确 Git 内容提交、整文件远端取回、分片与整包重建、Git membership 证明和实际 UTC/monotonic 顺序。用户此次明确授权修复和推进，故不重复要求后来才生成的 SHA 或 EXECUTE_FROZEN 字面输入；operator 将实际 F0 SHA 绑定 AUTHORIZATION.json，保存用户原话及“并非用户逐字指令/逐字审阅 SHA”的范围。首次 reserved forward 必须在 F1 的真实远端确认之后；live 必须在 F2 完整取回之后。

本研究正式阶段仍在冻结版本上保留每次实际 attempt；科学错配完成预定日程，操作/身份异常保留真实前缀、关闭受影响研究。修复不覆盖此前正式尝试。若后续还需新 study，继续保持研究身份、曝光清单和分母的可追溯边界。不会自动将新数据写入旧封存 artifacts 或旧论文；完成后先提供可审阅的论文修改建议与证据链接。用户的“完成后关机”请求继续保留，当前未启动关机。
