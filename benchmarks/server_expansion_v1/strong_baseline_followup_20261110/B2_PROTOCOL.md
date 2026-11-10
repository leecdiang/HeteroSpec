# B2：可选的 A5000 暖态等工作量宽度补证

## 1. 必要性与本次状态

**默认 DEFER，不因本PR存在而执行。** #214 的数值资格可支持此实现的宽执行能力，RTX 同工作量结果也已存在。只有稿件需要额外说清“A5000固定四cell在统一warm与过程顺序下的q8/q4pair时序”时才激活B2；否则在论文中删除/限制这项速度主张，保留旧B/C及其混杂说明即可。B2不阻塞32B、主稿或其他已有效结果，不触发D/E或576请求确认。

上次 B2 prepared 后因窗口不足在GPU前跳过，当前没有新B2测量。原脚本 STOP 是 **2026-11-09T21:00:00Z**，窗口已经失效。不得执行旧waiter、改一行日期后直接跑，或把上次allocation/lock视为当前权限。

## 2. 严格复用条件

继承固定 #216 中 `B2_controlled_v1` 的设计与 #214 的B数值资格，但仅当以下全部通过CPU/file核验：

1. 精确原B loop4/packed ELF、完整编译/链接依赖、实际加载module、backend/context、graph政策、driver/CUDA适配合同与硬件绑定保持一致。文件可执行不等于支持同资格；跨机器/环境变更不能自动复用。
2. 32个原资格cell确实全部通过；重读可访问的原始完整捕获（原准备代码检查的1728 heavy capture文件）及完整向量、initial/final active KV/frontier检查，不只相信公开SHA或 `passed:true`。
3. 原 independent R、derived oracle freeze、checkpoint state/frontier、所有8个token和所请求8行输出均逐字节匹配。用已补足260 token的暴露origin0，positions248/252；不误用此前199/196/197的短流。每个位置必须满足 `position+8 <= len(stream)`，独立核验初始state正好在该prefix。
4. 不引入32B recorder ABI、设备cache修补或算术变更。需要改host路径/日期/模块读者时，在新目录建立纯调度epoch，证明native ELF/参数/clock边界均未变，事前冻结并完整回读。旧源码、failed和未执行状态保留。
5. 新clean的全8行output hash、physical q4+q4或q8、input state/restore、目标终点/真实调用数量与已资格合同连接。若原clean receipt不足以核验所需边界，不能悄悄加instrumentation后仍声称原资格直接覆盖，须登记新bridge。

任一条件缺失则 **NOT_ADMITTED**。需要新的GPU复资格/启动probe都须从剩余11请求中逐项预留，无法完整装入时停止并申请新阶段预算，不压缩资格、不从32B借额度。公开text replay不能替代不可访问的private KV数值payload验证。

## 3. 固定128操作及进程顺序

唯一合法B2大小是 **64 warm + 64 measured =128 logical operations**。与Q32的72操作诊断没有共享额度或样本。

四cell：loop4/packed projection × p248（within）/p252（cross）。physical extent/实际width需以原状态与receipt再次验证，而不是凭名字认定。每cell四个fresh native processes，共16；每进程8个operation，每个operation前恢复完全相同初始state与frontier，输入同8个token。

- A = 两次真实q4调用，第二次承接第一次的合法state，一共8行输出。
- B = 一次真实q8调用，一共8行输出。
- 两者都完成所有8个owned full vectors，不能比较只复制最后一行或输出mask不同的变体。

四round的cell顺序仍为 `(0,1,3,2), (1,2,0,3), (2,3,1,0), (3,0,2,1)`，每cell各位置一次，每个有向cell邻接一次。

| round | 四warm操作 | 四measured操作 |
|---|---|---|
| 0 | ABBA | ABBA |
| 1 | BAAB | ABBA |
| 2 | ABBA | BAAB |
| 3 | BAAB | BAAB |

每进程各路径恰有两次warm与两次measured；warm顺序×measured顺序在每cell形成完整2×2组合。先所有四次warm，再四次measured，绝不能出现原B第二轮fresh process的q8未同样预热。每cell每路径8个measured、每路径总32measured。顺序固定，保留首次cold warm和所有后续记录，不选择较快的一半。

ABBA/BAAB使每路径平均measured ordinal匹配并对称覆盖A→B/B→A，但并不证明长期热平衡，也没有完全消除更长历史/跨process热效应。两次warm是统一预处理，不叫“已证明稳态”。若要收敛测试，另注册其请求数与停止准则，不能吃掉11余量后仍照搬128准入。

## 4. 计时与统计

保持原B `operation_s` 的实际计时代码边界，并在冻结文件中引用函数/源码SHA，逐项说明是否包含restore、sync、完整copy、hash。主B2 endpoint是**这个已定义等工作量operation boundary**，不能重新命名为GPU kernel time或完整live service。

每个operation额外保留完整host/caller clocks；restore、disk/SHA、model/load、四次warm、完整output copy/hash、serialization、退出均另报，重叠clock不相加。第一marker含启动/模型加载，与后续marker不直接当作同边界样本。profiler不混在这64个measurement；若需要另登记并收费。

每cell/process求 `r_j = (sum of two measured B operation_s)/(sum of two measured A operation_s)`。报告四个process ratios、`exp(mean(log r_j))`、min/max、全部单次值、按ordinal的敏感性。四process/cell为正确聚类单位，不把16 operation/cell当独立样本；四cell是同一暴露root的不同条件，不等于四个root。

预定主呈现为描述性区间。可附log-ratio的t区间（df=3，明确其小样本/正态假设与脆弱性），四cell同时呈现时用98.75%区间做Bonferroni family95%；无p值胜者筛选。不得以宽区间跨1称“等价”。过程bootstrap只有4cluster，若展示仅作敏感性，不包装成高精度总体推断。冻结脚本先对人工数据验证方向、单位、sum-vs-mean与聚类。

仅支持“此暴露root、两边界、两projection、固定暖态历史的描述性结果”。不声称所有A5000稳态、模型总体、live k7/k3、M优越、32B可迁移或GPU架构原因。B2是新epoch，与原B/C分开展示，不合池抹掉旧混杂。

## 5. 预算与完整panel准入

起点原8B账本：**1909/2048 requests，3053954/8000000 conservative rows**。先读取所有原ledger并核验不可变前缀，发现新增请求就重算，不能用此快照覆盖现实。

- 固定B2：128 requests /33024 conservative rows。
- 无其他消耗时终点：**2037/2048 requests，3086978/8000000 rows**。
- 仅余**11 requests**，它们不是免费的重跑额度。所有新reference/bridge/negative/profiler/启动失败与retry都计入；不得使完整panel之后剩余为负。
- 新激活前固定 `q_requalification + q_setup + q_failure_reserve <= 11`，且所有必要job与failure-reserve的具体数量/理由写明。默认保留至少8个失败/收尾槽，因此GPU额外资格/启动最多3个；需要更多就不在旧2048 envelope里启动。预留不是授权重跑成功臂。
- 预算公式同时核验requests和rows。每个process内部8 operation逐个计费；warmup与错误尝试不能省略。一旦启动发生uncertain outcome先查native receipts/ledger，不重复调用。

本PR不提升2048 ceiling、不重置账本、不承诺现余11一定足够。窗口新登记必须涵盖16fresh loads、全部128操作、freeze/复核、归档/全文读回和至少900s收尾余量。原 `16*max(old caller)*1.35+120` 只是旧估算，需说明新环境成本适用性和新增传输容量，不能直接复制已过期04:19:17 admission。必要pilot也要占预算，且不能先跑再决定怎么记。

必须重新确认单GPU分配、私有UUID、保护GPU0、CPU集合、GPU/RAM/disk余量与当前无冲突；沿用Q32保护规则并按实际B2捕获大小检查磁盘。无窗口则继续DEFER，不启动等待循环，不租卡。B2只能在核心32B阶段和交付不受干扰时安排，不能抢其时间。

## 6. 失败、冻结与交付

执行前一次冻结16jobs、全部128ordered operations、原资格复用证据、ELF/module/state/input SHA、host adapter/exporter/checker、时钟/统计、budget/window及failure policy，远端全文回读。旧归档fixture走完CPU测试之后才准入。

任何数值/physical/资源/预算失败即停止，保留全部已完成slots、日志、时钟与成本，不自动native retry、不选择性重跑慢操作。完整16process未完成时只能报告partial，不发布完整B2估计。重启整panel需新窗口与新预算，原消耗不退款。

交付新独立结果目录，原B/C/准备/skip记录不动。包含128逐操作记录、16完整caller、32资格复用证明、全部错误/预算链、独立public字节与统计重算、不可公开数值payload限制、GPU与lock退出。明确列出没有做D/E、没有新live结果。默认不merge、不改论文。
