# 前瞻性协议：两个固定profile，独立参考，完整结果

## 1. 范围、资产与封存

研究ID `b570_llama_memory_followup_v1`，范围仅Llama；STANDARD_Q6为主，TIGHT_Q8为补充。[POLICY.json](POLICY.json) 与 [ASSETS.json](ASSETS.json) 是本方案新规则，不调用旧#85的Q8-only host/select工具批准新profile。继承#85关于全历史排除、原生提交、whole-request计时及实际Git恢复的要求，以下明确变更优先。

先读回本方案actual remote head及全部Git blobs，复核#86证据；恢复#82/#86真实源程序/程序/DLL。原数值模块commit仍未认证时明确保留 NOT_CERTIFIED。本轮输出使用新目录和独立账本；旧#85/#86所有状态、512门槛和消耗原样保留。本轮新640×2工程预算属于独立预登记研究，不能把旧研究消费抹去；综合成本另列旧11次加载和本轮全部消费。

共同固定 greedy seed123、单seq、ctx1024、logical batch512、F16 KV、FAoff、threads10、全GPU目标/草稿权重与KV、生成cap128。native prompt总长度最多768；工程最大长度768加cap128在ctx内。不自动缩短题、ctx、cap，不CPU offload，不换目标量化/模型或启用FA。普通路径UB网格32/128/512；R_stock固定UB128。一次target模板渲染和tokenize后的原生prompt IDs供同profile全部arms共用，跨profile可共享题目但不得假设输出相等。

准备同一套12个曝光工程题（MBPP6、GSM8K6），以及固定warmup/边界题。审计完整B570历史、旧工程题、RTX#84及#83所有已预留题，排除至少#85 BASE_EXCLUSIONS的89个IDs，并扩展实际历史。确认题只预留独立池，选择器此时不可读。共同F0A登记两profile全部资产、threshold、候选空间、模式和缓冲容量、源码/DLL、任务、预算、时间范围；commit/push并核验actual remote blobs先于本轮任何forward，包括warmup/辅助decode。零forward探测也必须有源程序证明无hidden warmup。

## 2. 同进程内存与工程门槛

STANDARD_Q6：目标Q6_K，草稿Q8_0/Q4_K_M，阈值536870912 bytes（512MiB）。TIGHT_Q8：目标Q8_0，仅Q4_K_M草稿，阈值134217728 bytes（128MiB）。阈值从显式profile参数进入native probe、resident worker、controller和analysis，拒绝未知profile/量化/阈值；不能仅修改日志/退出码。始终保留budget−usage为signed数，负值停止；不禁用底层分配/兼容性检查。

每profile最多12个专用零forward探测单元（ordinary各UB、实际两模式/草稿、匹配路径与必要复测），每单元保守占1个工程预算单位，并占完整owned-process lifetime。不得用多次重新启动挑一次较宽裕的预算；最多3个同配置复测且全部发布，任何一次预算不足的配置不能凭最佳样本获得内存资格。正式worker加载与warmup归入正式预算/生命周期，不属于独立探测重试。

选择设备真实PCI8086:E20C与已审计Vulkan backend一致。采样由持有模型的同一PID调用VK_EXT_memory_budget；验证该B570 dedicated heap，使用每个相关heap的signed budget−usage最小值，不加系统heap，不拿另一个PID估计usage。记录物理大小、budget/usage、device/heap、PID、timestamp、模型/程序hash以及生命周期。全GPU layers及KV是必要但不足证据。

必须加载各候选实际的target/draft上下文、输出容量与工作区。batched验证至少能容纳k_max+1个实际输出（k3至少4），同时检查n_outputs_max及per_seq和实际图；顺序native模式按审核源码登记所需容量，不将它的1-output样本继承到batched模式。TIGHT_Q8的target prefill UB固定32；STANDARD_Q6的candidate prefill UB取已选R_prod的UB。draft UB1。不同模式的M_match与C保持目标路径、prefill UB、容量和数值设置相同；R_stock/R_prod维持真实普通实现，不为了匹配而降低普通基线效率。

加载余量只允许进入有限工程。在实际最长prompt768、cap128、k3验证、拒绝/rollback、自然EOG、capture on/off与reset工程运行中测峰值；LOADED及整个已观测ENGINEERING_PEAK均须满足profile阈值，无实际allocation failure。内存记录须覆盖工程分配路径并声明采样分辨率；请求前后两点不等于覆盖峰值。工程trace关闭后再次核验无隐藏decode、输出与边界行为。

分开登记：全GPU执行、权重/KV分配映射、观察到的local/nonlocal/paging范围。host输出数组、CPU tokenizer/控制器及显式staging不计为CPU模型offload；系统heap上的权重/KV/目标计算不允许。未能独立核验驻留范围则 `RESIDENCY_UNKNOWN`，可继续收集受控的原始正确性/成本诊断，但不得给出qualified驻留GPU速度结论或作为“放宽后显存可行”的正式证据。原始负预算、分配失败或实际offload则停止该配置，不继续正式确认。该区别不能用人工true字段代替。

正式每worker加载和每请求前检查阈值，检查耗时在主请求计时外对各arm统一处理。ENGINEERING_PEAK合格不是未来预算保证。正式出现不足、分配失败或迁移/驻留证据违规，保留已付请求、记录准确失效点，停止该profile；不自动改成另一个量化，也不重跑formal。内存事件在主计时内发生的成本仍须计入请求。

## 3. 有界探索和选择：不以正收益筛掉确认

先完成ordinary网格：12题×2曝光轮×3UB=72 paid，加3 warmup。候选ordinary必须完整raw native committed IDs、length、terminal及stop与稳定R_stock一致；选择两轮等权GM耗时最低者为R_prod，tie取较小UB。R_stock不稳定/不合格则该profile停止，不能改普通参考掩盖问题。

候选空间：STANDARD_Q6的2草稿×2模式(native_greedy/vulkan_batched_repair)×k_max[1,2,3]=12；TIGHT_Q8的1草稿×2模式×3=6。模式沿用可恢复实现的含义，必须审计实际数值路径、scope与repair mask并冻结，不把模式名称当证明。unsupported/内存失败仍列入完整空间而不forward。k为最大proposal长度，保留真实accept/verify/rollback记录。两个M_match各跑同12题×2轮以及各1次warmup。

另保留N_diagnostic：固定Q4草稿、k3、candidate prefill设置，对未修复的原生推测路径做同12题×2轮+1 warmup（25次），纳入工程预算。完整提交ID、第一分歧位置及可得的target决策/repair scope日志与R逐题比较，记录TRIGGER_OBSERVED或NO_TRIGGER；路径不支持/内存失败则保留原因和未检验状态。N不参与候选性能排名，也不与正式四arm混成全矩阵资格门槛。若N完全相等，不能宣称这组题证明了修复必要性；若N有偏差而C一致，才可在实际观测范围内讨论修复作用。N的分歧不能事后裁剪为一致。

每个C最多12题×2曝光轮与1次warmup。预排序资格要求：完整raw输出等价、真实模式/容量/基础内存门槛已核验；不要求R_prod/C>1或M/C>1。score为两轮R_prod/C的较小值，tie依次较小k、较小已观测peak bytes、candidate_id字典序。选择器只看同profile曝光工程数据，不能比较两个profile谁更快来决定哪项获得确认。

唯一排名第一的候选执行完整工程边界：2个合成prompt×caps[1,2,3,4,31,32,128]×[R_stock,C_selected]×capture on/off=56请求+4 warm。另外最长prompt、所有模式的tiny验证/回滚、EOG、capture/reset、必要实现修复共用余下预算。完整峰值、原生cap/EOG提交、capture关闭输出、状态重置均通过才能确认；所选候选失败则profile停止，保留所有候选，不循环换第二名追正结果。实现修复可在剩余工程预算内进行，但保留每次版本/消耗，全部资格要重新核验；不得重置640预算。

STANDARD_Q6基础485+25个N诊断forward+最多12零forward单元=522单位；TIGHT_Q8基础335+25+12=372单位。各hard cap640包含每次forward/warmup/隐含startup/辅助decode/失败、12个以内加载单元。START先fsync，失败也计费。剩余118/268只用于上述工程核验/修复，不扩展模型、量化、k、题集或阈值。预算不足就报告不完整。

输出完整矩阵和选择理由，即使无收益也不撤销已合格候选的正式确认。状态分别为 MEMORY_BLOCKED、IMPLEMENTATION_BLOCKED、RESIDENCY_UNKNOWN_DIAGNOSTIC、QUALIFIED_CANDIDATE_SELECTED。不使用#85旧“>1.05才进入确认”门槛；旧工具的select/host不适用于本轮，需新profile-aware检查和独立负向验证。

## 4. 共同F0B与两个新会话

两个profile工程都结束后，同时冻结选择或明确停止。再生成全新24题（MBPP12、GSM8K12），与完整历史/工程/RTX预留池不重叠。同题可供两个已冻结profile使用；不能看完Q6确认后再调整Q8。R/M/C在各自profile独立实际支付，不跨量化复用R、raw outputs或timings。共同F0B封存题目bytes/prompt IDs、全部源码/DLL/资产、候选与参考、控制器/内存规则、计时、完整schedule及统计代码；remote blobs实读验证后才执行任何确认forward。

每个合格profile：2个连续新会话×4轮×4arms(R_stock,R_prod,M_match,C_selected)×24题=768正式，加32固定synthetic cap128 warmup，总800。每arm192请求；即使两个R配置相同也独立支付。每block新resident worker，加载后10秒固定idle、1个warmup、24题，完整PID生命周期记账。

四轮arm顺序依次[a,b,c,d]、[b,c,d,a]、[c,d,a,b]、[d,a,b,c]；session2将每轮顺序反转。a=R_stock,b=R_prod,c=M_match,d=C_selected。各arm在每session每位置出现一次，task顺序与hash提前冻结。不得按温度/结果动态择时；可连续同日运行，无需等待RTX或六个日期。

计时从resident请求的prompt/JSON准备开始，到完整响应收取、native提交IDs/stop解析核验结束；全部proposal/reject/verify/rollback/decode/末端同步包括其中。普通/匹配/候选使用相同轻量提交通道；详细profiling工程完成后关闭。磁盘hash/持久化放在计时后并另报总开销。加载、warmup、idle与工程时间单列，不删失败、不要仅报decode kernel时间。

每profile640工程+800正式=1440上限，owned GPU-process lifetime8小时；两profile总2880/16小时，outer7天停止线。预算不可互借；一个失败另一个仍可继续其已预登记独立范围。formal重试0；不补槽、不换题、不重选候选。所有load/unload/crash/timeout保留，wall时间按完整owned worker生命周期累加，不用采样区间冒充运行时长。

## 5. 判断、限制与交付

每session/task/arm取四轮whole-request耗时中位数，24题等权GM ratio；两个session log ratio等权平均。主比较R_prod/C，另报R_stock/C、M_match/C、每domain/session/task、proposal/accept/verify/sync、峰值和完整搜索成本。

每profile四arm必须各192个完整paid记录，普通输出跨八次稳定、全部arm逐题原生提交IDs/length/terminal/stop全等、边界/实现/内存范围均合格。任一缺失/分歧/内存资格未知或失败，该profile所有qualified ratios为null；原始计时只作明确标记的诊断，不裁剪后缀或把unsupported候选隐藏。

POSITIVE_DESCRIPTIVE仍要求主比较两个session均>1、整体≥1.05、matched两个session>1；小收益、持平和变慢均报完整数值。无需达到此阈值才交付确认结果。两同日session不做日期t-CI，不称跨日期稳健。Q6/Q8分行报告，不聚合跨精度收益，也不声称“Llama/Qwen/Smol全都加速”。

提交新的结果Draft PR和可恢复CAS/源码/日志/ledger/机器判断/中文报告。独立CPU复算+实际Git-hosted恢复/readback，明确旧门槛旧结论、本轮新门槛、已测与未测。不中断RTX、不merge、不改论文结论。静态审计PASS不等于native已正确或B570已经运行。
