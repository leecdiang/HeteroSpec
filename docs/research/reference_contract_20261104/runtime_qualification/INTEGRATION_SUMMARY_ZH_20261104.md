# 经独立复审补充后的条件性方案摘要

2026-11-04；本目录仅新增研究文档和 CPU 抽象测试，不修改 native runtime；无 GPU 执行或正式证明。

## 方案应进一步收窄

可以定义一个比“所有 KV 先写好，再凭 mask 忽略未来槽”更容易证明的首版：保留既有 scalar attention 的完整物理输入。每层先对有真实资格证据的纯投影做打包，随后按 query 顺序执行“写当前 K/V -> 原 scalar attention -> 写下一 query 的 K/V”。依赖图必须保留 attention 对下一写入的反依赖，因为 padding 中的未来槽也可能实际被读取。不能凭 causal mask 就抹去 NaN/Inf/有符号零等数值责任。

该层序重排仍有严格前提：独立 layer KV、无跨层共享可变状态、同一 frozen reference 的算子/融合路线，且所有改动的纯算子均有输入/输出和写集关系证据。原 R 的 RMSNorm/RoPE/SET_ROWS fusion 要原样保留，或单独证明替换；关闭 fusion、换 FA 或换 KV layout 不是免费保持 R。

源码 KV 初始化会清零。对独占、dense append-only、无删除/shift/import 的 context，可建立“已提交前缀匹配 R，所有空槽字节为零”不变量。这样成功调用不必完整 snapshot 或 hash KV；只有已确认非致命且所有写完成的失败，才清零精确新写集并丢弃 shadow metadata/output。转置 V 要按实际 stride 矩形清理，不能用大包围区间清零。未知写范围、异步未完成、fatal CUDA failure 必须 poison；不能原 context 直接 scalar 重试。

## 必须新增的 native 接口

- decode 预处理前取得 owner lease，纯检查 pending update；不能只在 graph_compute 外包一层。
- scheduler 分配后、任何候选持久写入前，prepare 全部 CPU/GPU splits、复制、融合和实际 launch 路线。当前 CUDA split 拒绝不等于整个请求未执行。
- prepare 还须包含 MMVQ 内部 Q8_1 scratch 分配、量化和 padding memset；scheduler tensor 表不是完整写集。
- PlanTemplate 缓存结构，PlanBinding 每次检查 epoch、实际地址/分配 generation、positions/indices、n_kv、stream/event、输出生命周期。CapturedExecutable 另有实例 generation；不能拿 first-node pointer/graph UID 当数值资格。
- 完成屏障覆盖每个设备、辅助 stream、失败前已提交工作和 output copy。PDL 可使同一 stream 上 kernels 重叠，须检查实际 dependency wait/trigger 和 capture edge 属性。
- in-place KV 的读者也要遵守完整事务 lease，GPU 读者直到完成才释放。只原子替换 immutable descriptor 不够，旧 descriptor 仍能读到正在改变的 padded KV。
- Native CUDA_CHECK 最终走 GGML_ABORT，普通 C++ catch 不构成通用 CUDA 错误恢复。
- 逻辑 ubatch>1 会选择 n_threads_batch/threadpool_batch；scalar-shaped CPU node 也须绑定原 scalar 执行设置。
- callback_eval 返回 false 可以跳过剩余节点而 scheduler 最后仍返回 success，首版必须拒绝此路径，不能用 success code 替代完整执行覆盖证明。
- fallback 也不是免费安全：prelaunch 拒绝只保证候选未改 committed state，随后普通 llama_decode 仍可能部分失败或破坏零尾。fallback 必须在同一 owner/completion/恢复协议内，否则撤销 fast clean capability，重建不变量后才能重入。

## 定理应该怎样写

限定为条件性的 committed-state simulation：初态满足零尾和 committed-state 关系，所有 kernel 关系/物理写集/调度顺序/资源生命周期/完成判定/observer 排他均正确，则成功提交等价于指定 R 的 q 个 transition；可恢复 abort 是 numerical state stutter；poison 不签发 clean token、不进 cache。对成功 commit 次数归纳，得到输出和历史 KV 的位级轨迹一致。

必须先指定 reference transition schedule。仅固定模型/二进制而 R 本身 chunk-dependent 时，token prefix 并不定义唯一 KV。要么 canonical producer 明确为 frozen scalar recurrence并证明其他 producer 等价，要么 cache key 含 producer recipe/trajectory。这个方案也不能直接声称等价于 cold-prefill。

Vosti 已有 kernel contract + engine/cache invariant + induction；Taming 已有 reference-equivalence classes 和受限调优。因此新意不能写成“首次契约/归约签名/状态归纳”，只能在旧 R 兼容的实际量化 runtime 路径、低开销提交/恢复、强基线下净收益中寻找。当前还没有实际 kernel certificate 和 full native fast path，仍应拒绝生产资格。

## 当前证据和限度

主文：`RUNTIME_QUALIFICATION_AND_COMMITTED_STATE_20261104.md`，包括逐行源码证据、数据结构、伪代码、定理/责任清单、缓存/taint/overflow/atomicity和对抗测试。

`check_transaction_model.py` 与 `transaction_model_results.json`：54 组完整状态等价、648 个故障回滚点、648 个 guard 拒绝、5 个已复现反例。模型假设 projection 等价、无并发 observer 和已知同步完成；不是 CUDA 语义模型、不是 native/GPU 测试、不是正式证明。原空清单漏洞和 observer 边界已按独立复审修正/明示；独立复审文件与独立测试分别列在 README 中。

`source_manifest.json` 记录 source kit 与全部检查文件 SHA256，行号绑定 staged source。

性能也只能作为待验证假设：顺序 attention/额外 KV launch 或 mask 成本可能吞掉 projection 收益。必须对比同一 R 内的后端四列循环强基线，报告合格命中率和完整请求/会话时间；当前 packing widths 8-32 并不自动改善四行 verify。若 speculative acceptance 只保留 m<q，还须把拒绝后缀清零和 RNG/acceptance 提交成本计入成功路径。
