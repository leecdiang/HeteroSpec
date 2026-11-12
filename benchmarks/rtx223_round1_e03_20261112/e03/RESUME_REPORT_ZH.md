# RTX 5070 Ti 第一轮 e03 续作

结论：**INCONCLUSIVE**。本轮完成 C 数值 DLL 的真实链接、前端绑定准备及共享预算计数器的 CPU 验证；可信排重和完整模型物理 launch 预算仍未通过，因此没有初始化数值 DLL、运行模型或启动 GPU。资格与性能结论均未产生，不建议进入第二轮。

起点为 PR #223 `8f2585f90c40c81bca726c50647af650fd866e3f`，#221 为 `af436df989570ad882db65bd8a4b265b9e8cfdae`。当前交付位于独立 e03 目录。e01/e02、原源码、参考、失败记录和规范账本未覆盖。已读取原第一轮研究问题、协议、22 项预期、e02 续作与独立复核；仍匹配的 41 项 CPU 测试、Windows 监督器普通/优化模式各 18 项和 v7 前端准备未重复执行。

| 门槛 | 状态 | 证据与边界 |
| --- | --- | --- |
| 旧材料与预算继承 | PASS | `PARENT_BINDING.json`、`BUDGET_CONTINUITY.json`；独立复核原 e02 764 文件和原 core 3540 文件无变化 |
| 原 #221/#223 线程与全主机排重 | BLOCKED | 线程 API -32000；候选线程无可信终态；进程枚举仅见沙箱范围 |
| Windows 监督器机制 | PASS（继承的 CPU 范围） | 原 18×2 检查仍有效；不是全主机独占证明 |
| 显式源码路径的共享预留计数器 | PASS（CPU/源码范围） | 16 场景通过，独立重跑通过；边界、并发、跨 TU、失败不退额、重入、opaque 拒绝与自身 failstop |
| 完整生命周期 4096 物理 launch 强制上限 | BLOCKED | 未证明运行时/库内部活动完整覆盖；native configure 固定返回 -6，无 JSON 开关放行 |
| C 数值 DLL 编译与链接 | PASS | 实际 numerical backend，145 个链接对象，其中 141 复用、4 新编译，单一计数器 provider |
| 前端严格 profile、身份和 C ABI 绑定准备 | PASS（CPU） | loop4/packed 编译链接，22 个新 schema/gate fixture、6×2 reader 检查、4 个 CPU loader 场景通过 |
| 数值 DLL 正常加载、实际 A/B/C CUDA 分派 | NOT_RUN | 仅离线 PE/磁盘身份核验；CPU stand-in 加载单列，不冒充数值 DLL |
| 原路径重放、完整 activation/output/state、22×3 资格 | NOT_RUN | 66 格均保留冻结预期，见 `NATIVE_QUALIFICATION.json` |
| kernel/operator 配对计时与真实请求闭环 | NOT_RUN | 无真实 q8 捕获、自然 L4 消费或延迟样本 |
| 完整 resident-service 与强固定基线比较 | NOT_RUN | 无净收益、误差范围或机制增量估计 |

## 研究与合同

部署仍是单张 Windows RTX 5070 Ti Laptop、固定 Q8_0 参考、完整 requested logits 与 target/draft 活动状态的 resident 服务。原模型、词表、KV、producer、源码和 DLL 身份沿用原身份记录；本次没有实际加载模型，不能把磁盘记录称为已加载模块观测。主对照仍为 A backend-loop4、B 当前 packed、C 同 CTA 两组独立四列 accumulator，以及开发阶段冻结的最强合格固定策略。真实 target-only/runtime 只作应用背景，不同数值语义不得混入主比较。

假设是重复读取权重片段与调度成本可能限制 eligible q8 projection。A→B 反映 grid/launch 组织变化；B→C 才考察新增的同 CTA 复用及其寄存器、共享内存和并行度代价。原有 speculation 相对 target-only 的约 11%–25% 不是 C 的增量收益。最终指标仍是相同请求的完整服务墙钟时间，包含 reset、prefill、draft、verify、同步、planning/guard、controller、state、reconciliation 和 fallback；不得加总重叠阶段或拼接面板。

## 排重证据与所缺范围

本轮记录了 UTC 时间、两候选线程目录、线程 API 错误、受限进程枚举、已知锁、账本及 GPU 快照。当前 API 不能给出原线程内容绑定的终态；本地目录的 null async 状态和零终态事件不能证明已结束。NtQuerySystemInformation/Toolhelp 的可见范围只有沙箱，已知锁缺失和 GPU 空闲也不能补足全主机证据。没有删除锁、终止进程或改动其他任务。

需要主机所有者提供的最小补证见 `dedup/OWNER_STEPS_ZH.md`：在本机正常 PowerShell 粘贴只读 `Collect-HeteroSpecHostReadOnly.ps1` 内容并回传 JSON；打开两原会话，记录检查时间、是否仍执行、最后一项相关任务及结果；若存在 worker/lease，提供 PID、创建时间、可执行文件、当前持有者和排队状态。脚本不要求管理员或修改执行策略，不采集命令行/密钥、不启动模型。候选会话若并非原执行会话，还需要正确会话标识。这些证据到齐也不会自动绕过其他准入条件。

## 全模型预算：已实现部分与未解决部分

新 provider 使用跨 TU 共享原子状态，在提交前预留，约束继承已用额与该 worker 预留额合计不超过 4096；禁止重复配置、重入、超限和失败退款。void 路径拒绝时只终止自身进程，避免 C ABI/GNU-MSVC 异常传播；监督器须保留预留额和 unknown-actual 记录。不能给每个 worker 重新发放 4096，也不能让同一请求加载多个未绑定 DLL 实例分摊计数。

静态检查覆盖 168 个 raw launch 位置和 1 个 launch API 位置，并在 85 个 opaque、13 个 driver 位置加拒绝。149 个其余 runtime 调用已分类：它们包含查询、同步、配置、内存等，**不等于 149 个隐藏 kernel**。上述数字是源码位置数，不是全模型动态 launch 次数，也不是可运行请求的上界证明。

Graph capture/replay、cuBLAS、CUB 等不计作一个普通 launch：当前一致禁用/拒绝相应入口。运行前没有一个已证明可用的完整模型路径及全生命周期物理 launch 上界；内部 runtime 活动和保守 memcpy 等拒绝也可能使模型加载不可用。因此本轮保留 **all-physical coverage NOT_QUALIFIED / usable profile BLOCKED**，数值 configure 固定拒绝。没有 GPU 试跑来探测边界，没有将 standalone 局部计数替代全模型约束。后续准备需证明一个明确可执行的有限路径及所有初始化/传输/库/graph 活动的预算口径；若做不到，应继续阻塞而不是扩大预算。

## C runtime 与复建

新的 `runtime/build-v3/bin/ggml-cuda.dll` 为实际数值 DLL，33850880 字节，SHA-256：

`bcdb7642d32609c9242dc8aaecfadfb9f4e082ac8cfeccf5de6b7466546eb24b`

导出单次 A/B/C selector、身份及共享预算 ABI；C 已接入 packed dispatcher，限定 Q8_0/F32、q=8/g=2、[K,4,2]、K%512=0、偶数 M、同设备连续合法 span 等子域。C 保持每组原四列的 K/lane/归约顺序。A 仍要求 loop4 core，B/C 使用 packed core。域外旧 packed 路径不是新获得资格的 fallback。分派计数表示 guard 前 branch attempt，不能当作 kernel 完成计数。

正常加载涉及生成 CUDA 注册代码；当前只做 PE 离线核验，实际数值 DLL 的正常 LoadLibrary、导出调用、设备选择和执行均为 NOT_RUN。编译资源记录是 sm120a 编译器输出：原 case4 为 63 registers/thread、3072 B static shared；C 为 91、6144 B；两者报告 0 spill。occupancy、DRAM、L2、延迟均 unknown，不能据此声称 DRAM 流量下降。

复建见 `runtime/README.md`、`materialize_final_source.py`、`delta-v2/ORIGIN_MANIFEST.json` 和 `build_runtime.py`。固定原源码包加 66 项 delta 可恢复完整 3546 文件，已在新目录逐文件验证。保留 MAX_PATH 失败和修复 helper。实际链接复用了 141 个已成功对象；初批构建期间 provider 源码发生一次有记录的同步，准确时刻未知，旧对象未进入最终链接，新 provider 重新编译。独立审计核对最终 145 对象与命令/源码/链接身份。没有逐次编译时的完整 include 依赖快照，因此不声称全批次所有依赖始终冻结，也不保证跨环境 DLL 字节一致。

## 资源、失败与停止

规范账本仍为原 e02 `continuation/safety/runtime/family-ledger.sqlite`；本次只有明确标记的只读快照，不建立新规范账本。原第一轮限额保持 256 请求、1000000 target+draft rows、10800 秒原生 GPU 窗口、4096 全 kernel launch、2 GiB 捕获；warmup 和失败余量仍计入原分配。窗口未启动，不因新 epoch 延长或重置。授权与窗口需在未来实际准入时重新核对，不能将当前阻塞期间当作已获独占时段。

**e03 与同族累计原生使用均为：模型请求 0、target/draft rows 0、CUDA contexts 0、GPU launch 0、GPU 秒 0、GPU 捕获 0。** CPU fixture 计数不进入这些实际数。编译及 CPU 工程耗时不是 GPU/服务耗时；总工程墙钟未作为性能测量，未给出估计值。

完整保留构建 v1/v2 失败、counter prototype 的失败/修正、线程 API 失败、源码同步例外与首轮路径重建失败，见 `PREPARATION_FAILURES.json`。没有重跑 #213/#215，没有改旧 STATE、功耗、风扇或驱动，没有多卡、B570/Metal、PR 合并、Release 或论文修改。

下一步仍属于第一轮：补可信原线程/主机证据，完成可证明的完整模型预算 profile，再通过实际数值 DLL 绑定和原冻结资格。只有资格、相对 packed 的可解释配对改善、真实消费者覆盖及完整服务净收益空间全部成立，才有下一轮建议的依据。当前没有这些证据，不扩大样本、不启动第二轮。
