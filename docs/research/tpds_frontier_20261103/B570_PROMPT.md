# B570 原机任务：TPDS 参考相容并行与真实服务代价

先读同目录 AUDIT.md 和 PLAN.md。从 PR165 `5aae66e05b0f6e8a8b44dac719b2b05b8f84f34f` 恢复已执行最终 source binding，新建候选 worktree；原 P1/R、权重、端点、失败记录与旧成本均保留。上一轮已经完成主动 Qwen 修复，不要再重跑旧8输入面板或重复证明它通过。

公共核心由RTX侧发布集成候选commit；你先并行完成下面的计时隔离，再在冻结结构实验前读取该共同修订，负责Vulkan mapping。公共接口确需修改时用commit协调，最终核对公共核心字节一致，不各自复制一套“同名”实现。

首先处理本轮发现的具体性能口径：build_driver.py 在每次 llama_decode 前调用 capacity_check()，transfer_scope.hpp 内同时查询显存和系统 RAM；该调用在 service timer 内、phase timer 外，clean=true 不会关闭它。保留零 forward admission、请求边界检查、外层资源/进程安全保护，把逐 decode 重查询移出生产热路径。在同二进制下，按 PLAN 用旧面板 token 最短/最长两个输入进行五arm×polling-on/off×三session固定小诊断（60正式测量+warmup）；比较完整服务和实际查询成本，不能靠从旧时间减估计值来“修正”结果。数值路径/端点保持不变。PQ/QB逻辑工作匹配使局部对照较受保护，但不能假定查询开销严格抵消。

将当前 Vulkan scalar/batch activation selector 与物理前缀映射接入共同核心，保留 ordered-append reuse 身份。共同核心要与 RTX 最终接口修订对齐；冻结前记录真实 hash，不使用“接口相同所以实现相同”的表述。用 MATH1865/1804 的原 P1 状态、GSM1184 producer 条件及两个 Llama 旧控制做必要回归；F32 precision reversal 已有因果证据，无关代码未改时不再重复整个诊断程序。

接着执行 PLAN 的并行扩展：Qwen8B all-GPU，q=1/2/4/8，C1024及预先容量准入的4096（无法保持原 placement 时按计划登记2048或unsupported）。Q8、F16KV等不为通过而替换。Vulkan q≤4与key extent支持必须通过真实 shader/stride/dispatch 实现扩展，不能只删guard。对不跨界/跨界提前预测组宽，并实测scalar、repaired PQ、局部QB、整target caller边界拆分。用已知query固定工作重放分开并行与draft接受率；caller8若执行4+4应明确报告。新增 C 对应独立预先冻结 R_C，不改原 R1024。

主文成本以普通 target-only 的prefill/完整服务价值为主，保留 speculative 作为另一出口。当前同一输入的诊断显示 draft prefill 之外还有显著同步/提议代价；本任务不要求“修好 draft 就一定获益”，也不把此轮 all-GPU Qwen 的损失归因于 CPU draft。为两种相容分组实现采集少量匹配的phase/graph/实际kernel诊断，正式计时关闭重探针。

结构阶段结束后冻结新12自然输入与六session四arm面板（288正式测量+warmup）；原先8输入已暴露，不叫未见。自然长度层/领域选择、计时顺序和估计量在输出前固定。保留全部输入、逆向块和负结果。MHA/head64仅在已有Vulkan lowering可实质扩展时做定点检查；做不到就列出真实边界，不追加第三平台或大量替代模型。

工程故障和有证据的新算术条件可自主修复并继续，不能按模型名/输入/答案特判或使用全模型串行 fallback充作扩展成功。交付独立结果 PR、共同源码身份、预测/触发表、强基线完整成本、原参考资格和现有格式的可复算材料。不自动合并或投稿。
