# #223 第一轮 e04：e03 的独立续作

**结论：INCONCLUSIVE。GPU 准入继续 BLOCKED。** 本轮完成了新的生命周期 CPU 门禁、完整受控构建输入冻结、数值 DLL 全量重新编译及前端磁盘身份绑定提案。完整模型生命周期的 4096 物理 launch 强制仍未实现，原执行轮次终态及待启动 worker/lease 仍待用户提供。因此没有启动模型或 GPU，没有 native 正确性、筛选或性能结论，也没有进入第二轮。

起点为 #223 `7a4f2ca75923066c6eaac02a5e9ae885a846d688`。开工核对最新 RESULT、独立审查和 OWNER_STEPS；新工作位于独立 e04 目录。原 e01/e02/e03、旧源码、数据、失败记录和规范账本均保留。原测试套件没有重跑；新增测试仅针对本轮实现与暴露的风险。

| 门槛 | 结论 | 证据与限制 |
| --- | --- | --- |
| 旧材料、账本与预算继承 | PASS | 原 2678 项清单文件和五份旧账本哈希一致；规范账本 attempts=0 |
| 原执行轮次终态、排队 worker 与 lease 归属 | BLOCKED | 两次原会话 API 均 -32000；等待用户补证 |
| 此前全主机无 worker/已知锁快照 | 瞬时证据 | 按用户提供记录；不认定原会话结束，也不认定未来没有排队任务 |
| 生命周期事前上界与模拟提交前约束 | PASS，限 CPU mock | 26 项新检查在普通 Python/-O 下通过并独立复算 |
| 可运行的完整模型 4096 物理 launch 强制 | BLOCKED / NOT_IMPLEMENTED | native 证明表为空，完整物理上界为 null；真实拦截与初始化/库/清理覆盖未闭合 |
| 完整源码及受控代码生成输入冻结 | PASS，限记录范围 | 3546 个源码、12706 个编译输入；实际依赖及前后哈希、文件成员关系核验 |
| 新数值 DLL 构建 | PASS，限构建身份 | 143 CUDA＋2 host 全新对象；独立冻结链接成功，无 e03/失败 v1 对象复用 |
| 新前端两臂构建 | PASS，分开会话 | 每臂 1051 实际依赖、117 CPU 特征、33 个完整静态库容器；两 EXE 未运行 |
| 精确 archive 同名成员选择 | NOT_ATTESTED | 保守绑定完整容器字节；不把成员级歧义伪装成精确追踪成功 |
| 预期模块的磁盘 PE 名称闭包 | PASS_DISK_ONLY | 9 个 DLL 副本、产出端 248 项名称检查；系统/API-set/动态解析及 ABI/数值兼容未执行 |
| 历史 VCOMP 身份继承 | UNKNOWN | 新副本为明确标注的未资格提案，不能冒充旧参考已核实身份 |
| 实际加载 DLL、A/B/C 分派及 22×3 native 资格 | NOT_RUN | 66 格全部 NOT_RUN；保留每格原冻结预期 |
| 配对算子、真实消费者链与完整服务成本 | NOT_RUN | 无样本、收益值或误差区间 |

## 4096 约束具体做到了什么

新 `budget/lifecycle_budget.py` 是可执行的条件证明规划器和 CPU 模拟控制器。它要求 18 个生命周期阶段显式闭合：worker/DLL bootstrap、context/library 初始化、target/draft 模型与 KV、传输、warmup、prefill、draft/verify、reconciliation、capture、失败清理和 teardown。即使某阶段声称零工作，也必须有与产物、阶段和策略绑定的证明。

它在任何模拟入口前保守预留完整生命周期费用；同族上限为 4096，新 epoch 不能重新发放额度。未闭合 lease、失败、重入、重复步骤、身份变化和不明路径都拒绝。静态嵌套 graph/replay 按有限节点展开，不能把一次 replay 计作一次 kernel；循环、动态/device launch、host callback 和未知工作拒绝。后验统计只作为注释，不退款、不产生准入权。模拟出现 4097 的独立故障记录会保留超额、停止同族后续工作；它不是一次真实 GPU 超额。

这些检查**没有提供真实 driver/runtime 内核拦截**。`NATIVE_PREFLIGHT.json` 的生产证明表为 0，完整上界为 null，在 bootstrap/正常数值 DLL 加载前即拒绝。新 DLL 中的预算配置仍是静态拒绝策略，预期返回 -6；实际导出没有调用。没有用源码调用点、standalone119、API 次数或 CUPTI 后验统计替代全模型证明。DMA 或 API 调用本身不作为一个 kernel；本轮没有改变原内核计费口径。

缺口明确列于 `budget/NATIVE_CLOSURE_REQUIREMENTS.md`：初始化和 CRT/TLS/fatbinary/deferred work、库内部及传输侧工作、两个模型及所有动态路径、graph 与错误/driver 清理，都需要可信有限包络和提交前拒绝机制。缺少任一项，当前原预算口径就不能准入。CPU mock 通过和拒绝所有 native 工作，不等于已有可运行模型策略。

## 新构建证据与保留的失败

e04 数值源码与 e03 的统一最终源码 3546 文件逐字节一致，包含 297 个 `.h`。编译前复制并冻结源码、生成器、CUDA/MSVC/SDK、命令和相关环境，保留只读句柄拒绝写入/删除；编译前后检查输入成员关系及哈希。实际 nvcc `-MD`/MSVC 依赖记录须落入冻结输入或严格声明的生成输出。新产生的 145 个对象和响应文件在链接前再次冻结。

首个批次的 143 个 CUDA 编译因缺失 MSVC 探测布局失败，两个 host 编译通过，原批次保留。受控最小实验将原因定位到漏复制的原 `VC/Auxiliary/Build` 支持文件；恢复两个原文件和目录布局后编译通过，源码未修改。第二批 145 个对象全部全新编译、依赖闭包通过，但链接因 `TEMP/TMP` 缺失报 LNK1104。随后单独冻结相同新对象和链接输入，以自有临时目录完成 link-v3。明确记录两个锁定会话，没有声称全编译与链接始终共用一个不中断的冻结会话。

最终 DLL：`runtime/link-v3/bin/ggml-cuda.dll`，33851904 字节，SHA-256：

`2307f64f1f1f4d0bb4aba42e6f6793a29579c2af031e4dbadac77811096ae8ad`

loop4 与 packed 新前端也分别冻结重建。保留依赖解析、CPU 特征序列化、cc1 诊断识别和窄 archive 成员追踪的早期失败。完整静态库已冻结，因此采用保守的容器级输入闭包；无法核实的精确成员 occurrence 单列。loop4 编译未为追踪粒度再次重跑，packed 使用另外的锁定会话。部署绑定是外部磁盘清单，DLL 哈希没有循环嵌入前端。最新元数据见 `frontend/LATEST.json`：七项 base/CUDA/MSVC 依赖均有原 loop4/packed 双臂 pin；VCOMP 旧身份仍未知。独立复核核对了磁盘提案及身份，248 项名称检查标为产出端记录，没有冒充独立完整重跑或真实 loader 资格。

冻结范围是记录的受控代码生成输入，不是完整 Windows 系统映像；操作系统 loader/runtime、管理员控制和 Python runtime/stdlib 未全系统封存。不承诺跨环境 DLL 位同，也不以编译、链接或 PE 名称相容证明 CUDA 数值正确。

e03 的 provider 同步准确时间不明记录仍保留。e04 新冻结不能追溯修正旧批次。新 DLL 的寄存器、spill、共享内存、occupancy、DRAM/L2 和延迟未取得，不移植 e03 编译器数值作本轮观测，也不从源码或 launch 数推断流量下降。

## 资格顺序、资源与解除步骤

`qualification/` 保存原 22×3 预期和停止规则，没有新 GPU runner 放行。顺序保持：真实 q8 捕获及原路径重放 → 完整量化 activation/output/state 与 66 格资格 → 小规模原定配对 → 真 bonus 成为 seed、第五 proposal 拒绝读取 L4、correction/trim/pending 后继续 → 相同请求的完整 resident-service 与强固定策略。任何关键资格失败即停止性能阶段；自然覆盖缺失如实标记，构造 fixture 不冒充真实消费者。

A backend-loop4、B 当前 packed、C 双组四列及合格固定策略仍是主对照。共同 lazy-tail/cap/缓冲优化须公平适用；完整端点须含 controller、planning/guard、state/reconciliation 等实际开销。既有 speculation 相对 target-only 的收益与新机制增量分开，不同语义 runtime 仅作背景。当前没有相对 packed 的配对改善或完整服务净收益证据。

同族原限额保持：256 模型请求、1000000 target/draft rows、10800 原生 GPU 秒、4096 全 kernel launch、2 GiB GPU 捕获；原 warmup/失败分配不增加。规范账本仍为 e02 原路径，只读快照不是新账本。**本轮及同族原生实际量均为 0 请求、0 rows、0 context、0 launch、0 GPU 秒、0 GPU 捕获。** 数值编译输入约 3.028 GB、前端冻结输入约 575 MB 属于 CPU 准备，不计作 GPU 捕获。v2 阶段墙钟约 743.922 秒，含编译、依赖/哈希检查和失败链接；独立链接阶段墙钟约 10.312 秒，含锁定/哈希工作。它们不是纯编译器耗时或服务性能。

最小解除步骤：用户提供原 #221/#223 先前执行轮次的结束状态/最后结束回复、是否仍有排队旧 worker 及 lease 归属，见 `dedup/OWNER_STEPS_ZH.md`。当前无需重复既有主机快照；未来所有门槛就绪且原授权仍有效时，才在实际准入前刷新可信主机状态。另须完成真实全生命周期预算包络与提交前强制，核实模块身份及新提案的合同资格，然后才可运行原冻结资格。补会话证据本身不会自动放行 GPU。

交付包含可重建源码增量、生成/构建脚本、完整哈希清单、原始依赖/日志/map、270 项明确列出的新产物与只读/CPU mock 数据。专有工具链/SDK和 vendor DLL 字节、模型、私有会话缓存不进入公开包；保留本机隔离副本及其来源/哈希。Git 发布源码与审查摘要，原始大清单、日志、依赖和 SQLite 字节由完整压缩包提供。没有改旧参考/STATE、功耗/风扇/驱动，没有终止不明进程或删锁，没有合并、Release 或论文修改。第一轮 Go 条件未满足，不建议或自动启动第二轮。
