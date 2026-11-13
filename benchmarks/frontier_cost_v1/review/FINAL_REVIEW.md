# 独立交叉审稿：发布范围与证据

**结论：APPROVE_SCOPED_DRAFT。** 本轮可以作为独立、可复现的研究实现提交 Draft PR。通过项是合成 F32 CPU 上的完整 worker 延后 draft 尾步集成和实验协议实现；改变 target 调用宽度的首个非平凡 CPU 候选没有通过完整向量与状态资格。本轮没有 GPU 性能结果，不能宣称已实现约 5% 加速或普适新方法，也不构成生产合并批准。

审稿者独立阅读了原始实现与新实现，重新哈希保存的输入、源码、库、二进制、日志和 captures，自行逐字节比较并重建请求逻辑。独立审计脚本没有导入实现作者的 comparator。本审稿者没有重新执行 native 模型或 GPU 请求。以下 PASS 表示所述有限范围内的实际复核结果。

## 结果判定

| 检查 | 判定 | 独立证据与边界 |
|---|---|---|
| 固定源码准备与 CPU 数值库身份 | PASS | 4 个支持文件、3,539 个 numerical-core 成员和实际生成的 4 个共享库重新验证大小与 SHA；candidate worker 与既有固定 SHA 一致。构建成功仍是 BUILT_NOT_QUALIFIED。 |
| 完整 worker eager/deferred 对照 | PASS_CPU_FIXTURE | 32 请求对、552 个完整 frontend-read 向量对、272 个 active sequence 对，逐字节比较每侧 76,633,984 B。所有 argmax、accept/correction/bonus/CAP/EOG/keep 和观察事件顺序独立重建一致。 |
| 首个宽度候选 q2 对 q1+q1 | FAIL_QUALIFICATION | p248 的起始 active sequence 与 native geometry 完全相同；实际宽度分别为 [2] 与 [1,1]。完整输出、末态和下一步输出出现差异，计划正确停在计时之前。 |
| 独立 q1-only 协议 smoke | PASS_PROTOCOL_ONLY | 50 个 capture 引用重新哈希、40 个 blob 对逐字节比较；独立算得 10 contexts、136 native calls、3,524 rows，与逐阶段预算一致。没有不同宽度候选，不推翻 q2 失败。 |
| 历史 GPU reference、生产模型、完整服务收益 | OPEN_NOT_RUN | 本轮新证据不提供上述资格，不提供 GPU 性能或 5% 结论。 |

## 完整 worker：观察覆盖与保留边界

两个模式 include 相同 candidate worker，仅改变显式 compile definition。wrapper 保存原始 native 函数指针并调用真实函数；其作用是观察真实被请求的全向量，以及真实 trim/reset 后的 active sequence。没有修改 EOG 判断、强制接受长度或替换采样 token。

独立复核采用完整事件流，而非事后按 phase 或数量筛选。每个请求的预期事件数为 target 向量 `1 + (k+1) × cycles`、draft 向量 `k × cycles`、native state `4 + 3 × cycles`；目录中的原始文件集合也必须恰好等于事件引用集合。eager 的末次 draft forward 会产生尚未消费的输出；该输出未被 frontend 请求，因此没有被 wrapper 捕获，后处理没有删除任何事件。

实际覆盖包括 4 个 initial CAP、4 个 initial EOG、8 个 all-accepted terminal cycle、12 个 partial-accepted terminal cycle、2 个 bonus terminal、17 个 correction cycle、28 个 resident reset 和 4 个 256-cell extent crossing。共省去 29 次未保留的 draft q1，恢复 19 次必须保留的末步，其中包含终止时全部接受的路径。实际 draft native-call 差值逐请求恰好等于省略数。

状态结论限定为 **active sequence bytes 和被原生 append guard 检查的 dense mapping、allocator head、extent**。序列序列化不是完整 context 内存镜像；没有声称 inactive KV、padding、全部后端私有状态或图缓存逐字节相同。两种模式的原始数值共享库相同，进程实际加载的 `libllama*` / `libggml*` 集合也在前后核验。原生产 CLI 的 `GPU required` 检查保留，实际 CPU 退出码为 2，且源码中该检查早于 model load。

完整 worker 使用具有原生 SPM/EOS 元数据的未训练 F32 合成模型和显式 token IDs。它验证实际 greedy/EOG 行为，不验证自然语言 tokenizer、训练模型质量、量化生产路径或跨模型泛化。旧 controlled-frontier probe 与本轮完整 worker fixture 的资格不可互相继承。

## 宽度候选：失败应保留，不能被 argmax 掩盖

独立读取 raw 得到如下差异：

| 项目 | q1+q1 与 q2 的比较 |
|---|---|
| 初态 | 510,952 B 完全相同；geometry 相同 |
| 两行完整输出 | 256 个 float word 中 242 个不同，335 个字节不同；最大绝对差 1.9937753677368164e-05 |
| 输出 argmax | 两行均相同，分别为 109、5 |
| 末态 active sequence | 515,072 B 中 43 B 不同 |
| 下一步完整输出 | 128 个 float word 中 127 个不同；最大绝对差 4.023313522338867e-06；argmax 均为 75 |
| 下一步 active sequence | 517,132 B 中 43 B 不同 |

这说明仅比较输出 token 会漏掉本轮要求的向量与状态不兼容。实际只执行 3 contexts、31 native calls、752 rows，`timing_started=false` 且 measurement 列表为空。没有用较小 ubatch 或较弱判据重新包装成通过。

该失败发生在既定 random F32 CPU fixture、原 M2 LOCAL、实际 `n_ubatch=32` 的新诊断 reference 下。算术原因尚未定位；它不证明另一模型、量化方式或 CUDA 后端的 q2 也不合格。完整 worker 的 PASS 保持原 target 形状，宽度 probe 则改变形状，两者没有矛盾。

## 成本测量与下一阶段限制

操作窗口包含 schedule/batch 构造、原 PhaseContext planning/counters、native 同步以及完整 requested vector 物化。新增预算的 reserve 在窗口前，JSON 计账在窗口后，不会额外按 call 数污染被测成本。prefix、state export、比较、文件写入、continuation、draft 与 sampling 不在操作窗口内。

初始 state export 会影响 cache，因此记录名称是 capture-conditioned operation。q1 smoke 中，`first_after_fresh_context` 和 `one_shape_warmup_then_reset` 的实际 operation 都是 `graphs_built=1, graphs_reused=0`；后一名称描述执行顺序，不意味着已达到热图或 steady state。warm reset/replay 的初态 bytes 和 geometry 等价由已绑定、已执行的源码强制检查；该 reset export 未另存为独立 raw 文件。

固定 LOCAL 切分上限为 32；prefix 的外部块不超过 32，候选 q 不超过 8，continuation 为 1，实际 ubatch 为 32。在这个范围内，预算中的每个 call 对应一次 `llama_decode` API 调用；不能解释为 GPU kernel 数。全宽 CPU 计划上限是 190 contexts、3,032 calls、68,048 rows，但失败后没有执行满预算。

q8 对 q4+q4 的成本差同时含形状、attention、图、同步和共享工作，不能直接命名为跨状态通用的固定 per-call A。draft sync 也不能与 target A 混计。旧 Windows RTX 完整服务 proxy 中的 4.498 ms 阈值依赖其特定假设，不能直接移植到 A5000。本轮没有测量一个可代入该阈值的 A。

下一阶段仍需以相同真实模型、硬件、source/binary 身份和既定 reference 逐项取得 GPU 数值资格，再比较共享工程修复后的完整服务 baseline 与因果控制器；记录首次使用成本、失败与回归。远程执行器的资源分配、deadline 和中止保留应按其发布时的 host admission 单独审查。本次 CPU 证据不替代远程运行验证。

## 最终 host wrapper 增补

完成 CPU smoke 后，wrapper 增加了公开原模型身份硬绑定、已提交的 public profile 检查和固定 1,800 秒 native deadline；C++ source 未改变。审稿者独立运行了两个有针对性的 host-only 检查：终止自身创建的 sleeping Python 子进程并保留输出/被截断的 RESULT，以及拒绝用调用者给出的另一个 SHA 覆盖固定原模型 SHA。两个检查通过，没有执行模型。该新 wrapper 尚未执行 native 模型，既有 CPU 结果继续绑定 `retained_protocol_snapshot` 中的实际旧 wrapper。

公开 archive 的完整 SHA 和 4 个提取 metadata 成员相对已认证 TEXT_INDEX 的身份重新验证；64 个 job 均声明同一 target GGUF SHA，metadata vocabulary 为 151,936。公开 p248/p255 inputs 也从已哈希 LIVE_RECORDS 独立重新选择并重建。整个 GGUF SHA 绑定 embedded tokenizer，metadata receipt SHA 不等于独立 vocabulary digest。新的超时路径仅 kill/reap 本 wrapper 所有的 native child，保留 absent/malformed partial result 的中断证据，不重试或重置 GPU。真实资源占用、放置和 CUDA 执行仍未验证。

## 发布终审：设备映射、文档与成本后处理

最终 wrapper SHA 为 `d10df8f66e5d2a31301445037b0bc8f3c5135e5086b29074e06cd38949299a8f`。我另外独立执行了三个 mock host 检查，覆盖固定环境、物理 GPU0/MIG/重复或缺失的 inventory 拒绝，以及实际可见设备 PCI/count 的接受与拒绝。没有调用 CUDA driver、native 模型或 GPU kernel。

最终映射逻辑先要求申请的物理 index 大于零，NVML inventory 的 index 和规范化 PCI 地址唯一，GPU0 与申请设备均可识别；选中设备的 MIG 为 enabled 或未知时拒绝。它固定 `CUDA_DEVICE_ORDER=PCI_BUS_ID`，从物理 inventory 得到相应 CUDA ordinal，再通过单可见 CUDA 设备的实际 PCI 地址确认对应关系。CUDA ordinal 可以与物理 index 不同，不能只看环境变量中的数字。选卡和身份查询均不采集 UUID；真实 CUDA admission 分支尚未执行。

`RESULTS.md`、`HOST_EXECUTION.md` 与 Draft PR 正文已完成只读终审，其 CPU 结果、失败资格和开放事项与证据一致。公开计划又经独立逐层枚举：资格 38 contexts / 444 calls / 9,789 rows；测量 152 / 2,588 / 58,658；合计 **190 / 3,032 / 68,447**。1,800 秒仅限制 native child，driver identity query 有单独的 15 秒 timeout；源码核验、文件哈希和编译在此前进行，文档没有把它称为整个流水线的总时限。

新增成本后处理先验证 raw 与资格，再按同一 case/mode/repeat 比较 q8、q4+q4、八次 q1；不跨 q 拟合 A，也不聚合为全服务收益。我在两份既有已审 raw 上实际运行该后处理：宽度失败返回 `NO_COST_ADMITTED_QUALIFICATION_OR_EXECUTION_FAILED`，q1 smoke 返回 `NO_Q8_PAIRS_Q1_PROTOCOL_SMOKE_ONLY`，均无成本对。没有以模拟或补填数值制造 q8 结果。终审仍只允许有限范围 Draft；实际 CUDA、真实模型和完整服务收益保持 OPEN。

## 可发布范围与证据索引

可以发布源码、输入规范、有限范围的 CPU 实现验证摘要，以及明确保留的 width qualification failure。模型、编译物、raw vectors/states、缓存与原始机器日志应留在独立 evidence package。旧研究目录、论文主张与 PR218 S3 均不由本审稿修改。

- [PREPARE_SOURCE_AUDIT.json](PREPARE_SOURCE_AUDIT.json)：准备源码与数值库身份。
- [MATCHED_BUDGET_AUDIT.json](MATCHED_BUDGET_AUDIT.json)：全宽 CPU 计划与 native-call 映射。
- [NATIVE_INTEGRATION_RAW_AUDIT.json](NATIVE_INTEGRATION_RAW_AUDIT.json)：完整 worker 原始字节及请求逻辑独立审计。
- [MATCHED_FAILURE_RAW_AUDIT.json](MATCHED_FAILURE_RAW_AUDIT.json)：q2 失败的原始字节独立复算。
- [MATCHED_Q1_SMOKE_AUDIT.json](MATCHED_Q1_SMOKE_AUDIT.json)：独立 q1 协议 smoke。
- [HOST_ADMISSION_AUDIT.json](HOST_ADMISSION_AUDIT.json)：前一冻结版 wrapper 的公开原模型绑定、deadline 与目标 host-only 检查。
- [TERMINAL_RELEASE_AUDIT.json](TERMINAL_RELEASE_AUDIT.json)：最后冻结的 PCI/MIG 映射、文档与成本后处理终审；记录新 wrapper 的 host-only 验证范围。

本次完整 workspace 审计脚本为 `audit_native_outputs.py`、`audit_matched_smoke.py`；两者显式拒绝 Python `-O`，且必须写入新的报告路径。它们会访问本次原始 source/build/model 绑定路径。搬迁后的 raw-only evidence package 可用模块提供的 `compare_integration.py`、`verify_run.py` 重放。审稿最终允许的是上述 **Draft 研究实现范围**，不是性能结论或生产合并。
