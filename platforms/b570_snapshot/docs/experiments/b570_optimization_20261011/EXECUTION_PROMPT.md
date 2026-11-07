# 交给 B570 执行端的完整任务

请接手本 PR 的 `B570_OPTIMIZATION_V1`。用户授权你在真实 Intel Arc B570 10 GB 主机自行完成核验、提交 B570 可行方案 Draft PR，并在本协议的有界工程和独立确认范围内自动推进。目标是尽可能找到真实的正向收益；允许优化和探索选择，必须保留所有负结果。不要复写 #82，也不要更改正在进行的 RTX #84。

实际读取本 PR/head 和 README、RESEARCH、PROTOCOL、POLICY、ASSETS、SOURCE_BINDINGS、RTX_INTERIM_CONTEXT。先恢复 #82 原始 native 私有源码/程序和完整 CAS，逐项核验旧 source/build/module hashes。不要虚构 b10839 upstream commit；你可以在新分支修改实现并记录 lineage，但不能把新 backend 当作旧已认证结果。

先运行 CPU selftest 与静态 plan 命令。收集真实 inventory 和 hash-bound native 证据，不填示例值。补齐本机工程所需的 runner/controller：恢复旧 stdin resident frontend，接入同 PID 的 Vulkan memory 查询（工具目录提供模板），禁用 hidden warmup，验证 raw cap/EOG commit、全词表与目标 prompt IDs。独立探针 usage 不能认证模型 VRAM。若 header/SDK 不支持就在核验报告保留具体阻塞，不假装编译通过。

Qwen 优先：目标保持 Q8，草稿试 Q8/Q4_K_M 和已声明 k1/2/3、native/batched 两模式。Llama 作为另一独立研究，仅实际全 GPU 加载/峰值余量通过时推进。保留 stock ordinary UB128，并用 UB32/128/512 完整 discovery 找到最快合格 ordinary。C 必须胜过它且胜过 matched target-only，不能用 UB1 普通推理制造收益。

F0A commit/push/actual remote readback 必须先于任何新 forward。按协议预算探索，所有 startup/warmup/辅助 decode/失败都预记 START 并计入640。需要代码修复就保留版本/失败及 hash，不重置预算、不碰独立确认题。探索无收益也提交所有证据。

核验和有限探索结束，先新建 B570 可行方案 Draft PR：明确 VERIFIED_FEASIBLE、FEASIBLE_NO_PROMISING_GAIN 或具体 BLOCKED/UNKNOWN，给出可执行指令、预算、证据、候选选择及预计用时依据。PR 不是只有勾选布尔值。若有合格候选，封存选择后选全新确认题，排除 #80/#82、所有本轮探索题、RTX #84 全 panel 和任何已看过的确认题，做完整历史曝光审核。F0B actual remote readback 后控制器自动运行两个连续会话，不等六个日期。

四 arms/24题/四轮/两会话，768正式+32 warm，完整输出等价及192 paid records/arm才发布 qualified speedup。formal不能补跑或根据速度换配置。局部收益、回归、失败、额外实现成本都报告；日期CI=null。Qwen/Llama独立输出，无证据不宣称普适正向。

本地脚本自主到完成/边界停止，无 AI/API 持续监控；简报每10分钟且只在block间更新，仅异常、工程决定、封存和最终交付需要 AI。结果创建/更新 Draft PR，并附实际 Git-hosted 可恢复包与独立复算/readback。若有 Codex attach_artifact 工具，创建 PR 后立即关联。不得自动 merge、改论文或发布。实际 B570 状态未知就报告 UNKNOWN；CPU fixture/selftest 不能写成 GPU 核验结果。
