# RTX223 e08：真实 q8 数值通过，当前 C 慢于 packed B

接续 PR #230 的 `ee999060ea342e96014827f6c14ff8d5118b3d18`，北京时间 2026-11-13 01:03 完成第一批 A/B/C 配对数据，01:07 结束管理员控制器。PR 保持 Draft，不合并，不改论文、原参考或旧账本。

主要决策：当前 C 的逐位数值结果正确，但在本次真实 q8 操作数上，投影耗时比 B 高 **14.77%**，包含量化的完整算子耗时高 **12.64%**；两种边界各六组配对全部慢于 B。当前 C 不宜直接扩大到模型服务实验。这里只得到一个输入实例、一次计时会话的结果，不能外推普适收益或服务/k3 性能。

## 数值与配对结果

硬件实测为 **RTX 5070 Ti Laptop GPU，12 GiB，46 SM，compute capability 12.0**，UUID `GPU-6dd57db3-9aac-ccc8-bd69-225a5ea2c4dd`，驱动 616.92。不能将结果标成桌面版 5070 Ti。

输入为未改动 Qwen3-8B-Q8_0 的真正八 token 模型解码前缀，不是 q32 前八行。冻结的 tokenizer 输入为 `The quick brown fox jumps over the lazy dog and explains matrix multiplication.`；只送入其实际前八个 token。目标为 `blk.0.attn_q.weight`，K=M=4096、q=8、g=2、无 IDs/融合、连续 F32 输入与输出。

保留原始 17,825,792 字节 Q8_0 权重、131,072 字节 F32 activation、36,864 字节实际后端 Q8_1 activation、131,072 字节完整后端输出。A 为原 backend-loop4 的两次 case-4；B 为原 packed 的一次两组 grid；C 为同 CTA 的两组权重片段复用。C 源码与 e04 `hs_pair4_q8.cuh` 字节相同。A/B 算术源来自已冻结原 MMVQ，编译使用相同冻结 CUDA 工具链及 `sm_120a`、`-use_fast_math`。

每个候选重复两次：六次重放的 **全部 Q8_1 字节和全部 32,768 个 F32 输出值逐位一致**，并与捕获后端 oracle、其他候选一致。父控又独立比较原始文件，差异字节数均为 0。没有调整参考或容差。

| CUDA event 边界，微秒/算子 | A 中位数 | B 中位数 | C 中位数 | C/B 配对几何平均耗时变化 |
|---|---:|---:|---:|---:|
| 投影，量化在计时外 | 43.914 | 40.211 | 45.853 | +14.77% |
| 完整算子，含量化 | 49.286 | 44.291 | 50.045 | +12.64% |

六组固定平衡顺序：ABC、BCA、CAB、CBA、BAC、ACB。每组每臂五次，三臂各一次共同预热。先完成全部投影模式，再做完整算子模式。共 36 个 batch 样本、180 次受测算子调用，另有 3 次预热调用。CUDA event 包住整批，除以五；不含模型加载、分配、输入传输、资格检查和资源查询，包含设备排队及可能的主机提交间隙。另存主机完成墙钟，不将它等同纯 GPU 时间。

A 的完整算子第 2/3 号 block 为 55.763/55.923 微秒，其他四组约 48–50 微秒；全数保留。A 的该模式样本 CV 为 7.11%，B 为 0.46%、C 为 0.77%。C/A 的完整算子配对几何平均看似快 2.15%，中位数反而慢，不能据此给 C 正收益结论。C/B 的负结果在所有配对中方向相同，但仍不是跨运行稳定性证明。

| 资源 | A/B | C |
|---|---:|---:|
| 寄存器/线程 | 63 | 91 |
| 静态共享内存/CTA | 3,072 B | 6,144 B |
| local memory/线程 | 0 | 0 |
| 编译器 spill load/store | 0/0 B | 0/0 B |
| occupancy API 理论最多 CTA/SM | 8 | 5 |
| 理论活跃 warps/SM 上限 | 32 | 20 |

实际 achieved occupancy、L2/DRAM 流量未测。较高寄存器、较低理论 occupancy 是下一步检查线索，不能当作已证性能因果。

## 所有真实尝试与停止

e07 B1 仍为失败，唯一额度仍已消耗，旧记录不改。本轮先按原 3 次新 bootstrap 额度执行；用户随后明确要求放宽额度、继续取数，本轮将新 bootstrap 总限额**显式记为 6**，保留原 3 次合同和修订。此为对用户宽松授权的有限实施，不称用户给出了精确的数字 6，也没有改原 B1 或旧实验预算。

| 新 bootstrap 尝试 | 实际获准阶段 | 结果 |
|---|---|---|
| 001 | METER | FAIL：未绑定 IMM32，根 DLL 未加载 |
| 002 | METER | FAIL：未绑定 msasn1，根 DLL 未加载 |
| 003 | METER | FAIL：未绑定 WINTRUST，根 DLL 未加载 |
| 004 | METER/LOAD/COUNT | FAIL：未绑定 System32 nvapi64，UUID 未调用 |
| 005 | METER/LOAD/COUNT | FAIL：未绑定 windows.storage，UUID 未调用 |
| 006 | METER/LOAD/COUNT/UUID/CLOSE/FLUSH | PASS：一次根加载、一次 count、一次 UUID，正常退出 |

每次后都确认自有进程退出并定位新依赖再启动下次。新增系统/驱动映像经实际观察、静态依赖、精确路径/哈希及 Microsoft/WHQL 有效签名核对；未按目录或文件名泛化信任。apphelp 为启动兼容性依赖。Windhawk 引擎及未签名 Explorer 模组始终未准入；经用户批准的任务路径临时排除、用户手动退出后，2 秒 CPU 停留复测仅见六个正常映像。bootstrap 006 的 CUPTI 记录为两个不同 API correlation、kernel records=0、drop=0，ETW start/stop 各 1、映像 load/unload 各 64、丢失 0。CUPTI 区间不等同整个物理生命周期。

| 数值阶段 | 预留显式调用 | 实际提交前许可 | 结果/控制器墙钟 |
|---|---:|---:|---|
| capture-001 | 64 | 0 | FAIL，12.547 s：8,042,336,256 B cudaMalloc 拒绝；未 decode |
| capture-002 | 64 | 64 | FAIL，14.844 s：入口漏接已有 heavy 标志，回调被关闭；第 65 次提交前硬拒绝 |
| capture-003 | 32 | 4 | PASS，13.625 s：真实 q8 捕获、完整调度停止、清理退出 |
| qualification-001 | 14 | 14 | PASS，11.906 s：六次完整逐位检查 |
| timing-001 | 355 | 355 | PASS，11.766 s：全部配对样本完成 |
| 合计 | **529/567** | **437** | 38 未预留；92 已预留未用部分不退回 |

437 表示源码控制器发出的显式提交前许可，不是整个生命周期物理 kernel 完成数。成功捕获/资格/计时阶段各自同步和正常退出；失败阶段不能伪称完整成功。

首个失败后保留 2 GiB 进程提交限制，将捕获 producer 改为 mmap 同一完整 GGUF、`n_gpu_layers=0`，只用 `^blk[.]0[.].*` 精确 buffer override 将首层权重放到 CUDA；原模型目录、模型文件、算术参考和全 GPU 基线均未改。捕获要求目标权重、输入和输出均 GPU 驻留。这是独立输入 producer 的 placement，**不证明它与原全 GPU 请求基线等价**。

第二次失败后，读取冻结 `llama-context.cpp:1400` 确认 hsc heavy/context 绑定要求，接入原 `hsc::begin` / `decode_begin` 后，才进入原 eval callback。在目标投影已同步并写全文件后，通过仅穿过 GNU 调度调用栈的私有 typed stop 终止整个剩余调度，然后正常释放 context/model。没有让异常穿过 MSVC CUDA 后端帧。源码修订和旧二进制、失败输入均保留。

在第一次计时前将每批重复数从六改为五，重写未使用部分的事前分配：已用捕获预留 128 + 新捕获 32 + 资格 14 + 预热 7 + 投影计时 138 + 完整算子计时 210 + 失败余量 38 = 567。未从旧账本借用或退回任何预留。没有基于计时结果修改样本协议。

全轮模型加载调用 3 次，其中 2 次成功加载部分 GPU placement 的模型；decode 调用 2 次、每次 8 行，第一次被预算截断，第二次取得唯一完整捕获。没有生成/采样请求闭环；不能报告全轮模型或 GPU 使用为 0。原第一轮账本仍为其原数值。

## 身份、保护与观测范围

最终捕获程序：`e8f016e3a55c31602ac40ab3a638704de56c597a061818ed0fb3b96cc4015e96`。

算子程序：`b0d79aebbbb5faf996592d0b9252a01db0e1cbd770bf2888c1a6bd3add15d09b`。

独立 application-only CUDA 根 DLL：`ccd4d3f8f8d1f2001984fe3dea0e94fce014edc507904622d636682b939fc545`。

未改动模型：`408b955510e196121c1c375201744783b5c9a43c7956d73fc78df54c66e883d6`。

新根 DLL 复用 144 个经哈希核对的 e04 对象，仅新编译一个独立预算 host 对象；不是全新 145 对象重建。GPU 算术对象未改。CPU 未配置、重复配置、恰好耗尽和第四次拒绝测试通过；源码审计的 168 个直接 dispatch 位点及通用 cudaLaunchKernelEx 均有事前 guard，编译关闭 graphs，单实例计数无 reset/refund。独立算子所有显式 dispatch 只经单线程预留路径调用。源码位点数本身不是物理 launch 上限证明。

所有执行输入在执行前按路径、大小、哈希和文件身份锁定；编译前冻结工具链、源码、复用对象、生成器、命令和依赖，编译后无输入变化。完整清单、失败日志和来源见审计归档及本机冻结目录。旧生产根 DLL `2307f64f...`、原 native allowlist 空集和拒绝策略保持不变。

每阶段刷新全宿主进程、Task Scheduler、服务、已知锁/lease、NVML UUID 和占用；持有全局 UUID mutex 与排他 CREATE_NEW lease。历史用户确认只作当时结束证据，未重造历史缺口。当前快照和 lease 能排除所见冲突，不证明未来不合作的隐藏任务不会启动；NVML 的 compute 列表也不等同所有 WDDM/图形活动。

单零能力 AppContainer 原子纳入 active-process=1、kill-on-close、2 GiB 进程提交 Job；父控 outer Job 最多两个进程。每次控制器硬限 120 s，内部 110 s 停新阶段，终止只针对自有 Job。未修改 UAC、用户组、系统 provider ACL、模型目录 ACL 或其他进程。新增 staging 文件沿用已批准目录的继承权限。设备异常后的即时清理时间仍无硬保证。

数值阶段先看至少 10 GiB 空闲，执行中采样阈值为空闲 2 GiB、温度 85 C、磁盘 1 GiB、0.2 s 采样/1 s 陈旧拒绝。显存水位、温度、watchdog 是有遗漏与延迟的观察/终止机制，不是分配前硬上限。数值阶段采样最高 40 C；完整占用与峰值见 ANALYSIS，采样峰值不是瞬时硬峰值。未开数值 CUPTI/性能 profiler；ETW 只观察进程/映像，磁盘 hash 不等同内存映像证明。

**原 4096 全生命周期物理 launch 合同仍未闭合**。驱动、runtime、库内部及隐式 context/physical launch 数仍未知；本轮采用独立显式应用调用合同，不将 watchdog、CUPTI、源码计数或 wrapper 计数升级成原合同证明。

## 清理、门槛与下一步

原始操作数与六次完整输出已逐文件哈希复制到 `numeric-v1/evidence`，再删除本次专用 profile；失败数据同样保留。Windhawk Exclude 已恢复为空原值，保持用户手动退出状态，未重启后台。管理员控制器已 STOPPED。最终只读快照无候选 worker、项目排队任务/服务或 canonical lease；五份旧账本哈希全部不变。

| 门槛 | 状态 |
|---|---|
| 签名/映像闭包、CPU 隔离/ETW | PASS，保留每次失败及构建失败 |
| 独立 bootstrap | PASS，仅 attempt006 |
| 真正 q8、A/B/C 完整逐位正确性 | PASS，一个固定实例 |
| 配对计时 | PASS，一次会话；当前 C 对 B 的收益门槛 FAIL |
| 全生命周期 4096 / 生产准入 | 未闭合 / BLOCKED，未放宽 |
| 真实请求链、66 格、第二轮 | NOT_RUN |
| 稳定跨运行收益、实际 occupancy/L2 流量 | NOT_RUN |
| 合并、论文修改、旧基线修改 | NOT_RUN |

建议保留 B 作为当前算子选择，当前 C 暂停扩大实验。先做 CPU 编译与寄存器生命周期分析，检查在不改 case-4 每输出累加顺序的前提下能否降低 91 registers/线程；不能把降低寄存器当作已证明收益。

如要验证新的 C1，最小新 GPU 提案为：复用本轮已冻结真实操作数和不变 A/B oracle，不再加载模型；14 次逐位资格 + 355 次同协议预热/计时 + 14 次仅用于已定位代码修复的资格重试 + 32 次失败余量 = **415 次独立新显式预算**。仍为单任务、同 UUID、每运行 120 s、现有 Job/隔离/资源阈值，输出不超过 32 MiB。新候选、编译身份、时间窗口和新账本须先得到批准；本轮剩余 38 不自动挪用，也不继续执行。

真实请求链尚未完成相同 placement、producer、请求/回滚/输出合同及显式计数证明，原全 GPU 模型分配也失败；需要另外的具体内存与请求预算方案，不能将算子数值或本次计时外推到服务/k3。

## 直接证据

- [全部配对样本](numeric-v1/TIMING_SAMPLES.csv)、[计算与资源账](numeric-v1/ANALYSIS.json)、[独立逐位复核](numeric-v1/BITWISE_INDEPENDENT.json)
- [原始计时回执](numeric-v1/evidence/timing-001/result.json)、[原始资格回执](numeric-v1/evidence/qualification-001/result.json)
- [最终合同](numeric-v1/CONTRACT-v3.json)、[初始合同](numeric-v1/CONTRACT.json)、[中间修订](numeric-v1/CONTRACT-v2.json)
- [producer/操作数冻结](numeric-v1/OPERANDS_FROZEN.json)、[最终程序身份](numeric-v1/FINAL_IDENTITIES.json)、[profile 数据保全](numeric-v1/PROFILE_DATA_PRESERVED.json)
- [源码覆盖审计](numeric-v1/APPLICATION_PATH_AUDIT.json)、[CPU 预算故障测试](numeric-v1/counter-cpu-001/RESULT.json)
- [旧账本核对](OLD_LEDGERS_RECHECK.json)、[最终清理](CLEANUP_FINAL.json)、[管理员停止账](ADMIN_EVENTS.jsonl)

原始 GGUF、权重/activation/output 二进制、数值 DLL 和全宿主命令行快照只保留本机，不上传仓库。公开审计归档保留自身源码、所有尝试账与冻结身份；本机完整目录为 `C:/Users/ASUS/Documents/ChatGPT/HeteroSpec/rtx223-e08`，独立运行账为 `D:/HeteroSpec-PC/rtx223-e08`。

公开归档中的五份编译环境视图仅保留编译所需字段，去除无关账号、会话和访问路由标识；完整原始冻结文件仍留在本机，未被改写。[公开说明](PUBLIC_REDACTION.json) 同时保留原始文件与公开视图的哈希，二者不宣称字节相同。
