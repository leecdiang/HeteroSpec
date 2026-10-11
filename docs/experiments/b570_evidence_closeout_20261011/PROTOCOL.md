# B570 最终驻留、修复代价与正式成本协议

状态：PROSPECTIVE_NOT_EXECUTED。base为#88固定head。本研究以明确新预算完成缺失证据，不重新打开#87已停止的确认账本。

## 1. 固定一个配置

仅Llama target Q6_K / draft Q4_K_M，hash/revision见ASSETS。greedy seed123、single seq、ctx1024、logical batch512、F16 KV、FAoff、threads10、draftUB1、prompt<=768、cap128。所有参考/匹配/候选都使用相同Q6目标文件，不与RTX Q8或旧B570 Q8合并。

固定五arms：R_stock普通UB128（output容量1），R_prod普通UB512（容量1），M_match修复target-only/prefill512/continuation物理UB1（容量4），N_k1未修复Q4 draft/k1/prefill512/continuation512（容量4），C_k1修复Q4 draft/k1/prefill512/continuation物理UB1（容量4）。保留#88实际容量4，即使k1也不缩成2以优化结果。R_prod是曝光#88已选择的固定配置，新的确认不能重选普通UB。C是已暴露诊断首选，负收益背景明确披露。

不增加模型/精度/k候选，不降低512MiB dedicated headroom，不CPU offload，不重试Q8负预算。RTX局部query-batch并行不是本Vulkan实现；不能把UB1模式名写成移植的并行算法。

## 2. 先解决可观测性；观测不到就结束

最多6个专用zero-forward加载/trace单元，trace工具诊断最多60分钟；均收费并记录完整worker生命周期。先实际恢复#88 CAS、source/binary/DLL/资产，不能凭旧报告声明恢复。重建仅观测/控制层时保留旧字节与新完整版本，未认证upstream来源继续NOT_CERTIFIED。

先运行只读trace_preflight.ps1盘点工具、profiles、权限与已有session。Windows GPUView/Log.cmd需要管理员会话；若当前无权限或工具不可用，记录阻断，不自动提权、关掉他人trace、改驱动/电源或循环安装工具。#88 WPR错误0xc5585011保留；不能靠把失败码/字段改成true通过。

新trace采集实现属于执行端，先读并绑定实际WPT/Log.cmd/provider/source。任何zero-forward加载前先封存F0P（probe/controller/source/binary、工具、固定load配置、预算、trace方法），commit/push并实际读回Git bytes；它不替代forward工程F0A。零forward加载需实测工具运行、B570 PCI8086:E20C/LUID与worker PID关联、模型权重/KV Vulkan分配到真实视频内存分配的关联。GPUView能显示GPU事件并不自动证明全部模型buffer驻留。

GPUView默认圆形trace建议短于一分钟。用于长block必须独立冻结并验证file-mode/足量buffer、event-loss及相关provider，不将默认短trace冒充全程覆盖。相关原始ETL、allocation映射、解码工具/版本与解析导出全部保留，尽量限定当前owned worker观察范围。

P0必须得到实际可用的事件覆盖与load allocation归因才能进入forward工程；缺permission、loss、无法关联模型分配或仍只有budget/PDH计数，状态RESIDENCY_PROOF_UNAVAILABLE，终止本研究GPU方向，不生成合格收益、不改为较弱合同。CPU证据整理仍完成。

可用观测后冻结F0A，工程跑真实prefill、proposal、verification、reject/rollback、reset、原生EOG、最长prompt及capture on/off。物理驻留资格需要观测窗口完整、events_lost=0、weights/KV allocation映射完整、仅dedicated segments、没有相关paging/eviction、不明allocation=0，实际same-PID dedicated budget-usage始终满足观测阈值512MiB。完整weight GPU-layer log、Vulkan0 buffer map与一个PDH点均不足。

任何已观测负预算/分配失败/offload、proof不完整则停止。证明范围仅绑定观测worker/区间，不推导整块B570普遍显存能力或未来不paging。代码residency_gate检查导出结构和摘要；它不解码ETL，执行端必须提供独立解析并核验原始证据，不能以手填receipt替代。

## 3. 有界工程与轻量正式通道

工程总256单元，包括前述zero-forward6、全部warmup/失败/辅助decode与修复；不借旧640预算、不重置。基本5arms×12曝光题×2重复=120；固定cap/capture/reset/最长边界和观測通道改造使用其余预算。

先完整绑定同一Q6 R_stock稳定参考，M/C需全部whole raw IDs、native EOG flags、length/terminal/stop一致。N允许分歧并保留其首分歧。若N这组题本已通过，不宣称新面板证明修复必要性；旧#88四自然任务证据保持其原范围。

#88逐decode memory采样、compute callbacks、KV readbacks等观察成本不能作为清洁部署数字。新正式worker关闭重型callbacks/完整状态readback，保留必要load身份、native CHECK/预算约束与原生结束语义。source差异必须限定并核验无算术/状态/模板变更。固定曝光题比较旧observer-on与新通道off的输出一致性；计时差只能解释观测费用，不用来重选k、草稿或R_prod。

用于物理证据的已冻结轻量ETW必须统一覆盖各formal worker加载与请求期间，其真实共同系统观测成本包含在wall request结果中，明确正式结果为该可观测合同下的费用。若无法在formal获得同范围证据，qualified resident ratios置null，不用工程驻留样本保证formal全部时期。event-loss、覆盖与allocation对应逐worker记录，不以预先true字段填充。

组件与工作量profiling按 [MECHANISM_PROTOCOL.md](MECHANISM_PROTOCOL.md)：6曝光输入×R_stock/R_prod/M_match/C_k1四arm×baseline/lite/heavy=最多72请求，计入256总预算，驻留与原生资格优先。三模式保留同一ETW；heavy不得校准正式费用，lite不能新增同步。不能将N/C输出不同的时间差当纯修复税。驻留未通过则仅整理已暴露计数/缺项，不为成本模型绕过P0启动forward。

## 4. 新确认与排程

#88工程题及#84全部工程/确认题加入最小排除；再审计完整可访问B570/RTX/PR/归档历史。采用与RTX相同的description标准化hash分池，B570奇数桶，RTX偶数桶；每域按固定hash排序取12题，合计24新题。训练未见不在主张内，未知主机历史明确披露。新确认集在任何对应forward前冻结，selector无权看它。

F0B包括五arm、输入及native IDs、完整code/model/DLL身份、observability/decoder、单PIDbudget、请求记录格式、排程和统计，commit/push实际Git blobs读回先于formal warmup/请求。唯一C固定，无正收益准入；已通过实现/输出/驻留门槛即完成确认，负工程收益不取消。

5arms×24题×5轮×2连续会话=1200正式+50 synthetic cap128 warmup。每block新resident进程，不自动warmup；一个warmup实际计费。五循环Latin行，session1逐行反转，各arm每session每位置一次。所有task顺序冻结，无RTX等待或跨日等待。

主timer从resident请求JSON/IDs准备到完整RESULT接收/JSON解析/native结束校验，全部prefill/draft/verify/rollback/sync和请求内memory活动均收费。native CHECK统一在主timer外；load/idle/warmup、ETL持久化及metadata另记。不把读取PERSISTED或hash操作偷偷放进某一arm而不计费/不披露。

每arm240slots。完整R_stock稳定，比较涉及arms全部whole raw/EOG/长度/terminal/stop通过且每实际worker物理证据合格，才有qualified ratio；N失败不抹去R/M/C完整比较。N/C或R/N不合格时null，原始完整费用仅作诊断。formal retry0；没有补槽、换题、换模式、删后缀或重选。

统计为每session/task/arm五轮绝对费用中位数，24题及各域等权log ratio，再两session平均。主R_prod/C_k1，另M_match/C、R_stock/C、R_prod/M；全task/session/domain与负例保留。两同日会话不报跨日CI。

总256工程+1200formal+50warm=1506单元，owned GPU-process8小时，outer7天。达到任何门槛/预算停止点则停止并交付，不运行另一量化补救。

## 5. 结果的论文用途

若C保参考但不胜R_prod/M，正式确认该UB1修复方案不适合latency；这已是完成主线的有效负边界。若N更快却偏离，展示输出资格与成本门槛分离。若C胜出，报告固定精度、实现、可观测窗口和双基线，不扩大为跨平台普适加速。

若物理证据始终不足，最终交付是经过有界补证仍未准入的边界，不产生formal数值。保留#82已完成正式负结果和#88曝光正确性/费用证据，不使它们消失。

新结果Draft PR接在本设计上，独立benchmarks/b570_evidence_closeout_v1。包含raw arrays、ETL/分配映射、全源码/binary、memory/slot ledger、费用/负例、停止原因与真实CPU/Git档案恢复。旧#86/#87/#88、主文、release只读。

官方观测参考：
- https://learn.microsoft.com/en-us/windows-hardware/drivers/display/generating-a-trace-for-gpuview
- https://learn.microsoft.com/en-us/windows-hardware/drivers/display/using-gpuview

