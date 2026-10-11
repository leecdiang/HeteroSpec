# 工作量归因与 Break-Even Cost Model

本扩展为 prospective 解释检验，不重新解释旧冻结为新优化。主成本资格仍由 PROTOCOL/closeout.py 定义；计数或模型缺失单独报告，不能删除已支付请求、抹去合格负成本，或补跑正式槽。

## 1. 两个问题分开

R/M 的大收益可能来自 prefill 微批量、目标端路径或两者。用 R、强普通 R_prod、匹配 M 的原生 prompt/output 长度、prefill 与 continuation 成本区分它们；RTX 再保留 M0。同参考的 M/C 才回答加 draft 是否划算。不能用接受率单独预测请求净收益，也不能把 model bytes/参数比例当实际每步费用。

## 2. 计数合同

对每个计划请求保留原生 prompt ID 数、完整输出 ID 数（含原生 EOG）、cap、stop、实际 context/UB/capacity。新增轻量计数须在独立新 worker 实现，核验代码、raw 输出和计数；数值代码、模板、采样及 KV 路径不可为性能调参改变。

- P_all：实际生成的 proposal ID 数；P_verified：实际送给 target 验证的 proposal ID 数；A：接受并提交到完整输出的 draft ID 数。另报 A/P_all 和 A/P_verified，分母零时 null。原生旧 draft_n/accepted 先保留原名并审计映射，不偷偷改定义。
- 每个 proposal 的互斥最终去向：accepted_committed、first_mismatch_rejected、unexamined_after_mismatch、terminal_discarded、unverified_before_verify；五项之和必须等于 P_all。接受但被 cap/EOG 阻止提交者归 terminal_discarded。不能把 P_all-A 全叫拒绝。
- 输出守恒：L = initial_target_committed + A + bonus_committed + correction_committed + fallback_committed。每周期进展与接受前缀长度直方图、各位置被尝试/接受数、零接受周期、尾部缩短都记录；不得假设 prefix 独立同分布。
- Draft work：prefill 的 IDs/调用；continuation 实际调用与行数，拆 proposal 和 catch-up/sync。P_all 不是所有 draft decode work。
- Target work：prefill 的 IDs/调用；continuation caller 宽度直方图及实际行数，分 verification/replay/fallback；实际物理 UB、micrograph/occupied query 行数独立记录。k+1 或逻辑 caller 宽度不是实际并行度。
- Sampling/commit、phase binding、KV trim/rollback、同步/调度、request channel 计时分别保留。GPU event 有则报告，无则 null；CPU enqueue span 不能当完成的 GPU 工作费用。

原始周期 trace 与计数可在 heavy 工程中记录；正式 lite 通道只保留汇总计数和必要的低成本时间戳，全部 arms 一致启用。source/计数语义/观测开关绑定在 F0A/F0B；缺失或不一致保留具体原因，不填估计值。输出长度/终止仍由原始数组独立检查。

## 3. 固定校准面板与观测扰动

每家族六个已经暴露的任务，3 MBPP + 3 GSM8K。来源/选法/ID 在 DESIGN.json 固定；按 SHA256('heterospec-break-even-v1|'+task_id) 排序取每域前三，不看速度、接受率或输出长度挑题。RTX 从 #84 的旧确认面板取，因此它们明确转为曝光工程题；B570 从 #88 的12个曝光工程题取。两平台正式新面板仍按原来的偶/奇 description 分池。

四 arms × 六题 × baseline/lite/heavy 三种观测模式 = 每家族最多72个完整工程请求，替换原先宽泛 profiling 配额；均计入原有工程总预算，不增加360/256或正式预算。三种模式按六题固定循环顺序平衡，不能用最快模式选择配置。

baseline = 继承的必要原生计数；lite = 新汇总 work 计数与可验证的低成本 elapsed hooks、无重型 capture/状态 readback；heavy = 独立周期/形状证据，可有同步开销。所有三模式完整 raw IDs/EOG/stop/cap 比较及原生计数映射必须核对，lite 对 baseline 的 wall 扰动单独报告。B570 三模式均保留同一强制 ETW/预算合同，不关闭驻留证据来获取快数字。

正式采用冻结 lite 通道；其费用包含计数/时钟/强制观测开销，不能称完全未观测的部署费用。只用 lite 的有效 elapsed span 校准。heavy 为形状/计数证据，其强制同步时间禁止拟合干净通道。若 lite 只能提供 enqueue 时间或无法形成同一 request 时钟下的互斥完成跨度，模型状态 MODEL_TIMING_UNAVAILABLE；已有合格成本仍按协议收尾，不加同步、不扩预算追模型成功。

## 4. 预先冻结的一阶模型

按 family、arm 独立校准实际非负单位费用，不跨硬件、量化、运行时搬系数，不按 MBPP/GSM8K 分别拟合。basis 固定为 target/draft prefill IDs、draft continuation rows、target continuation calls(width)、reconcile/output IDs、rollback calls、request channel(一次)。每一 component 的系数 = 六个 lite 校准请求中完整互斥 wall span 总和 / 对应 work 总和；没有出现过的宽度系数为 null，不当零成本。

互斥 wall partition 必须绑定实际边界/时钟与 retained trace，包含 native 执行和 caller 提交/结果解析；嵌套 GPU/CPU 时间及等待不能重复相加。分项之和与完整 wall 的残差在冻结精度内核验。同步只用原路径本来存在的等待，不能为校准新增同步。该模型是一阶工程假设，context 非线性、缓存与异步行为可使它失败，残差必须展示。

\(\widehat T_a(x)=\sum_b n_{a,b}(x)\,c_{a,b}\)。匹配盈亏为 \(\widehat G_M=\widehat T_M-\widehat T_C\)，部署盈亏另报 \(\widehat G_{prod}=\widehat T_{R\_prod}-\widehat T_C\)。拆为目标端节省减去 draft prefill/continuation、verification/replay 与 reconciliation/rollback/channel 差额；只有 G>0 才预测请求净收益。共同 target prefill 在实际相等时才抵消。

测得每周期进展与每周期完整费用后可画 break-even 曲线；不能直接套 g=1+k*acceptance。可补充固定已观察 target work/进展、把 draft 两个非负分项设零的条件性预测，但它不是改接受率/重训后仍成立的普适上界。

模型输入包含执行后测得的进展/接受/work，是条件性解释模型，**不是执行前速度预测器、online guard 或自动 routing**。输出长度也不能由这次模型预先知道。原论文的 ideal wall 模型要求足够长生成、近似独立接受及不增加 wall 的并行验证；这里保留有限长度、实测验证费用与修复成本，不直接移植其系数或保证。

方法参考：Leviathan et al., ICML 2023, sections 3.3 and A.3: https://proceedings.mlr.press/v202/leviathan23a/leviathan23a.pdf 。

## 5. 新任务上的模型检验

先完成曝光校准，再封存 MODEL_CALIBRATION.json / BREAK_EVEN_MODEL.json、参数、calibration task/source hashes、计数 adapter、basis 与所有失败；F0B 实际 remote readback 必须包括模型字节，先于新确认 warmup/forward。校准缺失时也冻结失败状态，不从新确认拟合，不因预测负收益改变 arms 或停止已准入确认。

只使用新24题的 work 计数与冻结系数预测每次完整费用；真实确认 wall 只作检验目标。按既有五轮中位数、task/session、两会话等权处理预测和实测，不把所有重复当独立题。报告每家族/每域两会话的完整表、MAE、MAPE、signed residual、预测/实测费用及 matched/prod gap；不输出通过子集的验证结论。

预定描述性检验：每家族/域所有96个 task-session/arm 值完整时，MAPE<=20%；matched 和 prod 的方向准确率各>=80%，仅在实测 |gap|>5% 基线费用的案例中评价方向，其余 NEAR_BREAK_EVEN 全部列出。每个方向检验至少6个 informative task-session，否则 INSUFFICIENT_DIRECTION_CASES。不支持的宽度、缺计数或失败全部计入覆盖分母，模型检验为 INCOMPLETE，不能补系数或删题修成通过。这些阈值是冻结的工程校验约定，不是统计显著性或新因果证据。

长度描述按 prompt <=64/128/256/768 与 output 1–32/33–64/65–127/128 固定桶，同时单列 EOG 与 CAP。MBPP/GSM8K只是离线解释分层，不按域新增拟合或在线选择器。cap128数据说明有限生成窗口内请求成本，不能改称完整解题/无限长回答速度。

## 6. 历史比较限制与交付

新的 Qwen M/C=1.106097 与历史约1.035分别属于各自冻结的面板、runtime、会话/重复和计时口径；只能并列描述，不能计算“优化提升”或把差额归因于代码。列出 source PR/head、模型、模板、ctx/UB/FA、计时与观测、task IDs、轮次/会话及统计设计。缺历史精确绑定时明确 SOURCE_NOT_RESTORED。不新增旧/新实现共同面板 A/B，避免本收尾扩展；如将来主张优化提升，再独立预注册共同任务与运行时的实现 A/B。

交付 WORKLOAD_RECORDS.json、MODEL_CALIBRATION.json、BREAK_EVEN_MODEL.json、MODEL_VALIDATION.json、MECHANISM_REPORT.md、固定 bins/域/负例表及预测–实测散点和 request 费用分解图。GPU计时缺失、未覆盖形状、时间闭合失败、near-boundary或模型否证都原样写入报告。结果仍创建独立 Draft PR 接在本设计上，旧结果和稿件不改。
