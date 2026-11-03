# RTX 原机任务：TPDS 参考相容并行扩展

先读同目录 AUDIT.md 和 PLAN.md。以 PR166 `abd36bea639bf814159ad68ab015bc983c5338b1` 的实际已执行源树为数值起点，在新 worktree 推进，不修改旧结果，也不重复执行 PR164 的旧8输入面板。目标是形成可复用方法与扩展证据，不是让某个百分比更漂亮。

由RTX侧负责公共核心的集成候选，先将可读取的commit发布给B570侧；B570可并行做计时隔离。两边最终冻结的公共核心字节应一致，backend mapping分别绑定。涉及公共接口的进一步修改先通过commit协调，不各自复制一套“同名”实现。

先完成共享集成：保留实际图 RMS_NORM→MUL→RoPE 识别和 scalar-placement 选择，纳入 PR165 `final_mapping.py` 的 ordered-append reuse 身份思想；不能误写成原 CUDA 没有 build guard。给出共同核心的 commit/hash，后端差异明确放在 mapping。只做已有 Qwen14B 反例、Llama 边界/普通点和必要的同形状策略切换控制。原 PR166 十个补齐 recipes 是同冻结二进制的追加覆盖，不需要据此重开未见面板。

离线整理旧计时：保留 ratio-of-session-sums 的原报告，另重算等 input/等 session 的 paired-log；把 timed R 标为经旧 oracle 资格的 candidate-runtime ordinary path，不能称原旧 exe 的速度。完成 PR166 自己的 raw/source 远端交付；不要拿 PR162 的已完成回执替代。检查正式热路径是否有逐 decode 的重资源查询，只在确有问题时做 PLAN 中的小型隔离。

实施 PLAN 的主问题：在真实 allocator 状态下提前预测 q=1/2/4/8、短/长 context、跨界/不跨界的分组，比较 scalar、repaired PQ、局部 QB 和整 target caller 边界拆分。当前 helper 的 rows≤4 必须按真实算术机制扩展，不能只改 guard；报告 caller width 与物理 microbatch/FFN/attention width，不能把8行内部拆成4+4称为8行并行。使用真实固定状态/操作数重放隔离工作量，保留未通过坐标和首个差异。C4096 的 R_C 是事先定义的新配置参考，不替换旧 R1024；容量不足的处理按 PLAN，在输出前声明。

主 cohort 为 Qwen8B all-GPU。Qwen14B partial-offload 只补必要的宽度/位置规则迁移，分开汇报，不作为模型规模效应。新规则冻结后，在已有 SmolLM2 MHA/head64 做一个小型主动迁移检查，不增加随机模型数量。完成结构阶段后再冻结自然12输入与6-session四arm成本面板；既有 speculative 结果保留，不强制新场景都开启 draft。

可自主修复 build、adapter、observer 和实际发现的结构问题，记录实质性改动后继续。不要按输入/答案特判、偷换原参考、删失败、选择成功子集或计时到达阈值。不要自动合并、投稿或重写冻结历史。交付独立结果 PR：共同实现、复现入口、结构预测/实际触发、完整向量资格、强基线比较、完整成本及少量必要诊断。上传/回读使用已有机制，不再开发一套归档框架。
