# RTX223 e09 C1：资源目标达到，单例仍未超过 packed B

接续 PR #230 head `ba019f30522352c87cac2cc527082ecc6c73ed97`。本轮只做一版 C1，复用已验证真实 q8，不重新捕获或加载模型。2026-11-13 09:07 完成资格，09:08 完成计时（北京时间）。没有扩展服务、66 格或第二轮，没有改旧参考、账本或论文。

结论：C1 将编译器资源降至 **64 registers/线程、3072 B shared/CTA、0 spill**，理论驻留上限恢复到 B 的 8 CTA/SM。完整逐位数值通过。但本例 C1/B 配对几何平均耗时仍为 **1.022156（投影慢2.22%）**、**1.026132（含量化慢2.61%）**。投影12/12、完整算子11/12组慢于 B；当前不升级到模型请求链或服务。

## 先核对的旧证据

最新远程 head 与本机交付一致，#230 仍 Draft/未合并。重新读取原始计时和六次资格输出，独立比较全部字节；旧 C/B 配对比值确为1.147676、1.126389。保留 e07 B1、六次 e08 bootstrap、三次 e08捕获失败/成功记录及其解释，没有重跑旧 C、bootstrap 或 q8 producer。

复核 producer 可执行文件、独立根 DLL、模型、输入、Q8_1 activation、后端输出及其冻结身份；原 profile 已删除后的保全映射也逐文件核对。当前原 GGUF SHA256 仍为 `408b955510e196121c1c375201744783b5c9a43c7956d73fc78df54c66e883d6`。

额外做只读 GGUF v3 元数据解析：`blk.0.attn_q.weight` 为 Q8_0、4096x4096，数据起点5956384、tensor offset1344766464、绝对偏移1350722848；读出的17825792字节与捕获权重逐字节同一，SHA256 `822086ad0b394e3f032f5a95a0193df9a6f2f628f58cee4b2d2c44ba4bb26b5e`。这是文件读取，不是模型加载或数值 DLL 执行。

F32 activation、实际 Q8_1 与完整 oracle 的 SHA256 分别为：

- `47009f80cddac6ccefd830bd4a2763c6f5fa1a6cf96fb40fb2b6d1555e0d2836`
- `caaf90580faecb85103fb19d9f76f4d8210c3fd2ca72a7da1d28971537000901`
- `6f4c7a410b441c266a34f20f5a5c1c2bc67ef4a3ef5e622e4a005cadd42a0fd0`

其 lineage 仍是原 Qwen3 八 token 真正 q8 前缀，不是 q32 截行；原 producer 为 CPU embedding/RMS、首层 CUDA placement，不能外推成全 GPU 服务基线。当前模型和 producer 身份匹配不等于重新执行 producer，本轮捕获和模型操作预算均为0。

## 一版针对性修改

原 C 的 `tmp[2][4][2]` 同时保存16个 float 累加器/线程，而 case-4 为8个；`partial[2][3][4][2][32]` 的 group 维度直接将共享内存从3072增加至6144 B。跨组展开还改变权重、activation 和地址临时量的活跃区间。不能将63->91的28个物理寄存器全部归到新增8个源码累加器，更不能据此断言性能因果。

C1 采用不展开的外层 group 循环，同一128线程 CTA 顺序处理两组，重复使用 `tmp[4][2]` 和 `partial[3][4][2][32]`。保持每个输出的 lane/K 分区、K起点与步进、遍历顺序、dot primitive、跨warp相加顺序和warp reduce不变。所有warp都保留到第二组；组间加一道保护共享缓冲复用的 barrier。

这也意味着**放弃跨组寄存器权重片段复用、第二组重新加载权重、增加同步并改变调度**。所以它是资源降压诊断，不是只改变 occupancy 的因果对照。没有同时扫描变体、强行设置 maxregcount 或靠 spill 换寄存器。

| 来源/资源 | 原 A/B | 旧 C | C1 |
|---|---:|---:|---:|
| 同时活跃的源码 float 累加器/线程 | 8 | 16 | 8 |
| 编译器寄存器/线程 | 63 | 91 | 64 |
| 静态共享内存/CTA | 3072 B | 6144 B | 3072 B |
| 编译器 spill load/store | 0/0 | 0/0 | 0/0 |
| local bytes/线程 | 0 | 0 | 0 |
| occupancy API 理论 CTA/SM 上限 | 8 | 5 | 8 |
| 理论活跃 warps/SM 上限 | 32 | 20 | 32 |
| 实际 achieved occupancy | NOT_MEASURED | NOT_MEASURED | NOT_MEASURED |
| DRAM/L2实际流量 | NOT_MEASURED | NOT_MEASURED | NOT_MEASURED |

第一版即达到事前编译假设“<=64寄存器、3072共享、无spill”；性能假设“本例不慢于B”未达到。无额外性能 profiler，不用理论 occupancy 冒充实际采样。

## 资格和计时

设备为同一 UUID 的 **RTX5070 Ti Laptop GPU、12 GiB、46 SM、driver616.92**。A/B 的原始 MMVQ/quantizer header、算术与原 launch 形状保持不变，工具链与 `sm_120a`、`-use_fast_math` 设置一致。构建前冻结全部旧/新输入并持有读句柄，实际依赖闭包 PASS，构建后输入变化为0。

新程序 SHA256：`9928daecaffd91f9679a1fac4febc843015b41885a4196b7ac71299dbbe50db0`。

A/B/C1 各重放两次：每次36864个 Q8_1 字节、32768个 F32 输出全部逐位一致，并等于未改动的实际后端 oracle。父控独立核对六组原始文件，activation/output 差异字节均为0。资格只用14次显式提交前许可，无修正或重试。

计时只测 B/C1。每个边界12组，顺序 BC1、C1B 交替，各6组；每个 batch 四次调用。预热是一个固定 round，每臂两次完整算子调用（job保留旧 schema 的 `warmups=1` 表示这一固定round；实际 `warmup_calls_per_measured_arm=2`、执行回执4次算子调用及8次显式 kernel）。不将这个旧字段当成每臂一次调用。

| CUDA event 边界，微秒/算子 | B中位数 | C1中位数 | C1/B配对几何平均 | C1较慢组数 |
|---|---:|---:|---:|---:|
| 只投影，量化在 event 外 | 40.424 | 41.380 | 1.022156 | 12/12 |
| 量化+投影完整算子 | 44.572 | 45.648 | 1.026132 | 11/12 |

投影 B/C1 样本CV分别1.12%/0.73%；完整算子1.48%/1.64%。完整算子 B 的46.664、C1 的48.032微秒较高样本全部保留；没有剔除、选择重跑或筛选次序。所有48个batch在 event结束后做完整 Q8_1及输出逐位检查，48/48通过。

CUDA event包住四次调用后除以四，含设备排队和可能的主机提交间隙，不含分配、输入传输、资源查询及批后拷贝/比较。另存主机完成时间，它也不含后续批后比较。投影模式先做完再做完整算子模式；批后同步拷贝可能影响下一批时序，这是本协议的计量边界之一。

旧 C/B 的14.77%/12.64%与本轮2.22%/2.61%在方向上支持“资源降压版接近B”的观察，但两轮会话、三臂/两臂、每批重复数和批后检查协议不同，**不是 C 与 C1 的严格配对测量**。不能把差值写成纯粹 C1 加速或 occupancy 因果结论，也不是普适或服务结论。

## 独立415预算和现场保护

| 事前项目 | 可用/预留 | 实际显式提交前许可 |
|---|---:|---:|
| 模型加载、新捕获 | 0 | 0 |
| 初次A/B/C1资格 | 14 | 14 |
| 一次已定位修正后的资格余量 | 14，未使用 | 0 |
| 计时阶段总预留 | 355 | 320 |
| 其中共同预热 | 8 | 8 |
| 其中投影配对 | 120 | 120 |
| 其中含量化配对 | 192 | 192 |
| 计时预留内未用部分 | 35，不退款 | 0 |
| 独立失败余量 | 32，未使用 | 0 |

总上限415，实际永久预留 **369**，源码发出 **334** 次显式提交前许可；未预留46，已经预留未用的35不退回。预热/失败/重试均受同一新 family ledger 控制，没有借用 e08 剩余38或任何旧额度。模型加载/解码/数值根DLL显式加载为0；CUDA runtime/driver的真实初始化发生在两个原生阶段，隐式context数与整个生命周期物理 launch 数仍未知，不能报告GPU使用为0。

原4096全生命周期物理合同仍未闭合。源码计数仅覆盖显式应用 dispatch；加载、库/驱动内部工作及设备异常后的即时清理没有已证硬上界。ETW进程/映像、NVML水位和watchdog是有遗漏/延迟的观察或终止机制，不是物理硬上限。

09:06管理员控制器恢复后，先在同一身份做了新的受限CPU/ETW检查：六个CPU映像、start/stop各1、load/unload各6、loss0；没有CUDA初始化、NVML或数值DLL加载。未重复旧GPUbootstrap。当前全宿主进程、计划任务、服务、已知锁/lease及NVML独占检查在每阶段刷新；没有终止无关进程或移除未知锁。当前快照不能证明未来隐藏任务不会启动，NVML compute列表也不等同所有WDDM图形活动。

沿用同名零能力 AppContainer、原子加入 active-process=1 / kill-on-close / 2 GiB commit Job、父控outer最多2进程。新文件放在原已批准 staging 的独立子目录，只使用继承权限，没有修改ACL、原模型目录、Windhawk规则、服务、用户组或UAC设置。54个原模型路径实际访问拒绝。旧staging原有模型副本权限未变，本次程序不链接llama、没有GGUF加载路径，仅允许四个冻结操作数。

每段外控硬限120秒，内部110秒停止新的父控EXECUTE许可，119秒终止自有native Job；准入/执行水位与原已批准数值方案相同。native固定批次内部没有逐kernel的110秒时间检查，不能把父控阶段门限说成每个kernel的110秒硬门禁；本次资格和计时控制器墙钟分别8.813/9.016秒，未触及该边界。其墙钟包含主机预检与身份锁定，不是GPU忙碌时间。显存/温度采样峰值见RESULT；采样不到的瞬时峰值未知。

## 止损与下一步（不执行）

当前 C1 接近 B 但仍未胜出，本轮停止，不扩大到请求链、服务、66格或第二轮。资源改动之外的同步/权重重载可能抵消收益，这是**待检验的下一假设**，不是测得的原因。后续可先静态查看调度/访存指令，不自动产生新候选GPU sweep。

若先消除旧C/C1跨会话协议差异，可提案用同一现有输入、同一新二进制同时保留旧C和C1：A/B/C/C1各两次逐位资格18；B/C/C1六组平衡顺序、每批五次、两种边界计时及共同预热294；资格修正余量18、失败余量20，共**350次独立新显式预算**，不加载模型。这会提供当前缺失的严格C/C1配对证据，但仍不是只改变occupancy的因果实验。此提案NOT_RUN，不能挪用本轮余额。

若要检验跨输入稳定性，建议先固定两个新真实 q8 producer 提示：

1. `Explain why cache locality matters for matrix multiplication on GPUs.`
2. `A compiler schedules independent instructions to hide memory latency.`

保持同一未改GGUF、相同首层前缀placement及A/B/C1二进制算术合同，每个提示由原tokenizer产生实际前8 token；在未来执行前冻结token IDs、producer、原始权重/F32/Q8_1/oracle身份，不能用旧q32截行。每个输入捕获预留32、资格14、同协议计时预留355，两个输入802；另一次资格修正14与失败余量32，共 **848次独立新显式预算**，最多6段受控GPU运行、每段120秒。输出总量不超过128 MiB，不运行完整服务。必须另批合同、窗口和预算，不使用本轮剩余额度；这里仅为具体提案，全部NOT_RUN。

## 门槛与证据

| 门槛 | 结果 |
|---|---|
| 最新head/旧失败/真实捕获身份复用 | PASS |
| 源码/编译资源假设及依赖闭包 | PASS，单候选首版 |
| 当前CPU隔离/ETW/进程准入 | PASS |
| A/B/C1全部逐位资格 | PASS |
| B/C1全部配对与48批后数值检查 | PASS |
| C1本例不慢于B | FAIL |
| 实际occupancy、DRAM/L2流量 | NOT_MEASURED |
| 全生命周期4096 / 生产native准入 | 未闭合 / 仍拒绝 |
| 服务、66格、第二轮、论文与合并 | NOT_RUN |

[完整结果](RESULT.json) · [全部原始样本](ALL_SAMPLES.csv) · [六次独立逐位复核](BITWISE_QUALIFICATION.json) · [捕获复用与GGUF原始payload核对](PARENT_REUSE_VERIFIED.json) · [合同](CONTRACT.json) · [源码假设](RESOURCE_HYPOTHESIS.md) · [构建回执](build-001/BUILD.json) · [纯CPU预算故障测试](counter-cpu-001/RESULT.json)

完整本机 successor：`C:/Users/ASUS/Documents/ChatGPT/HeteroSpec/rtx223-e09-c1`，独立运行账：`D:/HeteroSpec-PC/rtx223-e09-c1`。原始结果字节已在删除专用profile前逐文件保全；旧资料和负结果不覆盖。profile已删除、控制器已退出、两种自有lease均已释放；最终只读快照无项目task/service/worker，e07/e08及五份旧账本哈希均不变。没有修改Windhawk配置。模型、操作数payload、EXE/DLL和全宿主命令行快照不上传仓库，公开文件与审计包提供源码、身份、原始样本和闭合回执。[最终清理与旧账核对](CLEANUP_FINAL.json)。
