# B570 最终驻留、修复代价与正式成本协议

状态：PROSPECTIVE_NOT_EXECUTED。base为#88固定head。本研究以明确新预算完成缺失证据，不重新打开#87已停止的确认账本。

## 1. 固定一个配置

仅Llama target Q6_K / draft Q4_K_M，hash/revision见ASSETS。greedy seed123、single seq、ctx1024、logical batch512、F16 KV、FAoff、threads10、draftUB1、prompt<=768、cap128。所有参考/匹配/候选都使用相同Q6目标文件，不与RTX Q8或旧B570 Q8合并。

固定五arms：R_stock普通UB128（output容量1），R_prod普通UB512（容量1），M_match修复target-only/prefill512/continuation物理UB1（容量4），N_k1未修复Q4 draft/k1/prefill512/continuation512（容量4），C_k1修复Q4 draft/k1/prefill512/continuation物理UB1（容量4）。保留#88实际容量4，即使k1也不缩成2以优化结果。R_prod是曝光#88已选择的固定配置，新的确认不能重选普通UB。C是已暴露诊断首选，负收益背景明确披露。

不增加模型/精度/k候选，不降低512MiB dedicated headroom，不CPU offload，不重试Q8负预算。RTX局部query-batch并行不是本Vulkan实现；不能把UB1模式名写成移植的并行算法。

## 2. 有界驻留补证；与实际费用研究分开

最多6个专用zero-forward加载/trace单元，trace工具诊断最多60分钟；均收费并记录完整worker生命周期。先实际恢复#88 CAS、source/binary/DLL/资产，不能凭旧报告声明恢复。重建仅观测/控制层时保留旧字节与新完整版本，未认证upstream来源继续NOT_CERTIFIED。

先运行只读trace_preflight.ps1盘点工具、profiles、权限与已有session。Windows GPUView/Log.cmd需要管理员会话；若当前无权限或工具不可用，记录阻断，不自动提权、关掉他人trace、改驱动/电源或循环安装工具。#88 WPR错误0xc5585011保留；不能靠把失败码/字段改成true通过。

新trace采集实现属于执行端，先读并绑定实际WPT/Log.cmd/provider/source。任何zero-forward加载前先封存F0P（probe/controller/source/binary、工具、固定load配置、预算、trace方法），commit/push并实际读回Git bytes；它不替代forward工程F0A。零forward加载需实测工具运行、B570 PCI8086:E20C/LUID与worker PID关联、模型权重/KV Vulkan分配到真实视频内存分配的关联。GPUView能显示GPU事件并不自动证明全部模型buffer驻留。

GPUView默认圆形trace建议短于一分钟。用于长block必须独立冻结并验证file-mode/足量buffer、event-loss及相关provider，不将默认短trace冒充全程覆盖。相关原始ETL、allocation映射、解码工具/版本与解析导出全部保留，尽量限定当前owned worker观察范围。

P0有界尝试取得真实事件覆盖和load allocation归因。缺permission、loss、无法关联模型分配或只有budget/PDH计数时记RESIDENCY_PROOF_UNAVAILABLE，停止继续追trace；它不禁止进入输出/实际请求费用工程。这里事前定义两个独立证据问题，不能把UNKNOWN写成物理驻留通过，也不提升#88旧结果。继续forward前仍需实际运行门槛：same-worker signed headroom>=512MiB、全部weights/KV GPU放置日志、没有已知分配失败/offload或相关paging/eviction；实际失败停止，不能通过换量化或降阈值补救。

运行门槛通过后冻结F0A，工程跑真实prefill、proposal、verification、reject/rollback、reset、原生EOG、最长prompt及capture on/off。物理驻留资格需要观测窗口完整、events_lost=0、weights/KV allocation映射完整、仅dedicated segments、没有相关paging/eviction、不明allocation=0，实际same-PID dedicated budget-usage始终满足观测阈值512MiB。完整weight GPU-layer log、Vulkan0 buffer map与一个PDH点均不足。

任何已观测预算低于512MiB/分配失败/offload/相关paging或eviction则停止；proof不完整仅使物理结论UNKNOWN。实际预算检查点的最小值不能写成两个检查点之间连续物理驻留证明。证明范围仅绑定观测worker/区间，不推导整块B570普遍显存能力或未来不paging。代码residency_gate检查导出结构和摘要；它不解码ETL，执行端必须提供独立解析并核验原始证据，不能以手填receipt替代。

## 3. 有界工程与轻量正式通道

核心工程256单元，包括前述最多6个zero-forward probes、全部核心warmup/失败/辅助decode与修复；不借旧640预算、不重置。基本5arms×12曝光题×2重复=120，资格边界使用核心剩余额度。机制另列profiling128（96测量槽+32加载/预热/失败余量），总工程384；两类不借用，模型缺项不挤掉主确认。

先完整绑定同一Q6 R_stock稳定参考，M/C需全部whole raw IDs、native EOG flags、length/terminal/stop一致。N允许分歧并保留其首分歧。若N这组题本已通过，不宣称新面板证明修复必要性；旧#88四自然任务证据保持其原范围。

#88逐decode memory采样、compute callbacks、KV readbacks等观察成本不能作为清洁部署数字。新正式worker关闭重型callbacks/完整状态readback，保留必要load身份、native CHECK/预算约束与原生结束语义。source差异必须限定并核验无算术/状态/模板变更。固定曝光题比较旧observer-on与新通道off的输出一致性；计时差只能解释观测费用，不用来重选k、草稿或R_prod。

正式统一counts通道，关闭实验ETW、分项elapsed hooks、heavy callbacks/状态readback与新增同步，保留实际运行必要检查和轻量整数计数。主费用不扣减估算的观测开销。ETW限独立工程heavy观察，逐worker保存event-loss/覆盖/allocation证据；它只能证明该观察区间。正式无同范围物理证明，严格resident qualified_ratio必须null，但完整输出/运行门槛通过的request_qualified_ratio可以报告实际费用。不能称后者为fully-resident或纯GPU硬件速度。

组件与工作量profiling按 [MECHANISM_PROTOCOL.md](MECHANISM_PROTOCOL.md)：6曝光输入×R_stock/R_prod/M_match/C_k1四arm×baseline/counts/lite/heavy=96测量槽，计入独立128 profiling预算。baseline/counts/lite关闭实验ETW，heavy可采集驻留/形状；四模式均保持运行门槛。heavy不得校准正式费用，lite不能新增同步，分别报告counts-baseline和lite-counts扰动。不将不同输出的N/C差当纯修复税；模型失败不取消已合格的主费用确认。

## 4. 新确认与排程

#88工程题及#84全部工程/确认题加入最小排除；再审计完整可访问B570/RTX/PR/归档历史。采用与RTX相同的description标准化hash分池，B570奇数桶，RTX偶数桶；每域按固定hash排序取12题，合计24新题。训练未见不在主张内，未知主机历史明确披露。新确认集在任何对应forward前冻结，selector无权看它。

F0B包括五arm、输入及native IDs、完整code/model/DLL身份、observability/decoder、单PIDbudget、请求记录格式、排程和统计，commit/push实际Git blobs读回先于formal warmup/请求。唯一C固定，无正收益准入；已通过实现/输出/实际运行内存门槛即完成确认，负工程收益不取消。

5arms×24题×5轮×2连续会话=1200正式+50 synthetic cap128 warmup。每block新resident进程，不自动warmup；一个warmup实际计费。五循环Latin行，session1逐行反转，各arm每session每位置一次。所有task顺序冻结，无RTX等待或跨日等待。

主timer从resident请求JSON/IDs准备到完整RESULT接收/JSON解析/native结束校验，全部prefill/draft/verify/rollback/sync和请求内memory活动均收费。native CHECK统一在主timer外；load/idle/warmup、ETL持久化及metadata另记。不把读取PERSISTED或hash操作偷偷放进某一arm而不计费/不披露。

每arm240slots。完整R_stock稳定，比较涉及arms全部whole raw/EOG/长度/terminal/stop、完整费用与运行门槛通过，才有request_qualified_ratio。严格qualified_ratio另外要求相应正式worker的物理证据；缺少即null。N失败不抹去R/M/C完整比较。N/C或R/N不合格时null，原始完整费用仅作诊断。formal retry0；没有补槽、换题、换模式、删后缀或重选。

统计为每session/task/arm五轮绝对费用中位数，24题及各域等权log ratio，再两session平均。主R_prod/C_k1，另M_match/C、R_stock/C、R_prod/M；全task/session/domain与负例保留。两同日会话不报跨日CI。

总384工程+1200formal+50warm=1634单元，owned GPU-process8小时，outer7天。F0B前以工程真实耗时预估完整确认并预留余量；模型/trace缺项不阻断主确认。达到实际资源/预算停止点则交付，不运行另一量化补救。未启动槽可在原冻结计划和预算内恢复，已启动槽不可重跑。

## 5. 结果的论文用途

若C保参考但不胜R_prod/M，正式确认该UB1修复方案不适合latency；这已是完成主线的有效负边界。若N更快却偏离，展示输出资格与成本门槛分离。若C胜出，报告固定精度、实现、counts测量通道和双基线，不扩大为跨平台普适加速；物理驻留主张限独立trace实际范围。

若物理证据始终不足，交付UNKNOWN及有界补证记录；只要运行和输出资格满足，仍完成formal实际费用确认，严格resident比值保持null。保留#82已完成正式负结果和#88曝光正确性/费用证据，不使它们消失。

新结果Draft PR接在本设计上，独立benchmarks/b570_evidence_closeout_v1。包含raw arrays、ETL/分配映射、全源码/binary、memory/slot ledger、费用/负例、停止原因与真实CPU/Git档案恢复。旧#86/#87/#88、主文、release只读。

官方观测参考：
- https://learn.microsoft.com/en-us/windows-hardware/drivers/display/generating-a-trace-for-gpuview
- https://learn.microsoft.com/en-us/windows-hardware/drivers/display/using-gpuview

