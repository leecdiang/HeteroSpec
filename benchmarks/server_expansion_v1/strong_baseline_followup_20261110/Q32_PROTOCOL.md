# 32B：强简单基线、机制诊断及条件性新根确认

## 0. 状态、问题与预定结论边界

**设计完成不等于运行准入。** 本 PR 仅设计。执行器、后端 loop、实际 operand/root 清单、当前服务器授权窗口均未就绪，`ADMISSION.template.json` 保持不可准入。不能运行旧日期 coordinator，也不能沿用旧分配锁当作新授权。

旧结果回答“当前两个部署实现谁更快”，没有单独识别 group 的增量。新研究只回答：

1. 在相同真实 Q4_K/Q6_K 输入、原始标量点积、完整输出与共同优化政策下，图级逐列循环搬到后端后，原 group 优势保留多少？
2. 若三路径可正确实现，whole target-only 上是否有值得报告的新根部署差别？

固定 **whole lowering + M（target-only）**。不加入 LOCAL、D4、k7、模型家族、其他 GPU 或租卡。M 的多列收益主要可能来自 prefill；decode 的 q1 是负对照，必须拆报。此设计不能提供新 D4 收益、投机接受率、kernel 算术创新或 GPU 架构因果结论。若将来研究 D4，需另注册三 projection × 同一 D4 语义的完整三臂，不拿旧六臂拼接。

## 1. 三条实现及可归因范围

| 标识 | 实现合同 | 允许解释 |
|---|---|---|
| G：graph REF1-loop | 同固定图源码，每列 view、原标量 mul_mat、拼接输出。原执行作为强度待检验的对照，不能故意降低性能。 | 旧 graph 组织包。 |
| B：backend REF1-loop | 一个显式、受 guard 约束的后端入口，在同 stream 内按列调用原始单列量化/标量点积派发，直接写入预分配输出列。循环在 host backend 内，不是再次生成逐列 ggml 图。 | 相比 G 的图节点、concat、buffer/dispatch 组织包。 |
| C：REF1-group | 保持原独立通道 `ne11=1` group 路径；列独立，保持原 per-type scalar-MMVQ 的计算顺序。 | 相比 B 的后端分组执行包。 |

三者均使用原 `vec_dot_q4_K_q8_1` / `vec_dot_q6_K_q8_1`，原 `quantize_row_q8_1_cuda`、block/padding/type 参数、原 FP32 accumulate/归约顺序、原 FP16 KV。禁止把 Q4_K 重解码成另一精度、改 TF32/fast-math/规约树、转到旧 Q8 四列 arithmetic、隐藏 CPU fallback、只算 argmax 或部分输出。共同合法优化（容量复用、无用临时对象、静态元数据缓存）必须对所有可适用臂开放，并先冻结差异表。

**不先假定 B 可行。** S0 检查 pinned 后端单列 dispatch 的可调用边界、activation 量化缓存生命周期、量化 padding、stride/offset、输出所有权、capture 约束及错误传播。后端循环若仍逐列量化，这是实际工作的一部分，必须计时并记录，不得只报 dot。若复用共同量化能严格证明每列量化字节等价且可公平用于三臂，在同一候选 epoch 中统一采用；不能仅给 C 或 B 偷换工作量。

B 禁止“一个融合 kernel 内重新实现整套点积”冒充简单 loop。若确实只能修改算术 kernel，先标记方案不可用/需要新协议，而非把不同算术塞进本研究。实现不支持某合法 descriptor 时 fail closed，不能静默回退到 G 或 C。B 被证实不可行时公布具体 API/stride/capture/语义阻碍、尝试与成本，停止三臂性能确认，不删掉其存在、改称 group 已击败最强简单实现。

G→B 与 B→C 均是可审计实现包的对照。即使数值完全一致，也不能仅由计时将差额全命名为图开销或 kernel 算术优化。需辅助图节点/concat/kernel launch/quantization/copy 次数及独立 profiler 证据；未解释 residual 保持 `unassigned`。

## 2. 不变条件、共同 CUDA Graphs 政策

- 目标保持 19,762,149,024 字节 Qwen3-32B-Q4_K_M.gguf，SHA256 `efd971561896866f0e910cce52761ca77b1b138090c7f15fe284676d57d1f689`；385 Q4_K、65 Q6_K、257 F32。逐 tensor 的 type/shape/stride/归属重新核验，不把这个计数当数值资格。
- R 是 #216 同主机原 pristine Linux scalar R，UB1/reserve1、C1024、F16 KV、noFA、原图政策。旧 R 文件与容差均不改；不从候选产出 oracle。新输入需要用同 R 扩展新不可变 oracle 分区，完整记录新增请求。跨主机/driver/依赖变化不能继承输出或资格，需该平台自身的重复 R。
- 三候选保持 C1024、UB32、reserve32、F16 KV、noFA、whole、相同 greedy/EOG/cap/reset/tokenizer/template/线程与 offload。输入 embedding 的标准 CPU 映射必须如实记录；不写“全部 tensor GPU”。无 draft 模型加载。
- **本设计主政策固定 `cuda_graphs=false`，与 #216 候选一致。** 三臂均在 backend 初始化前用固定后端支持的 switch 设置，记录解析配置、实际 capture/replay 状态与 absence/presence 计数。不能只看环境变量字符串。
- graphs-on 不是允许在 timing 中临时切换的备用档。若希望研究更强共同部署政策，必须在本轮任何 clean 性能输出前，为三臂完成明确的共同可行性与数值门禁，在新协议修订中说明选用依据并重新冻结全套源码/资格/fixture/预算；不能看速度后选胜者政策，也不能拿旧 graph-off 一臂对新 graph-on 一臂。无共同 on 支持时保留 off 的范围限制，不将 timeout 解释成 on 不可能。
- 原 R 自身政策不用改成候选政策来“凑同配置”。要求的是同一独立 oracle、候选间共同政策和对 oracle 的数值证明。

## 3. 阶段与冻结顺序

### S0：零 GPU 静态审计及实现准备

不初始化 CUDA、不做 allocation probe、不调用模型。读取 pinned 源包、编译与依赖清单，核验 G/C 生成源码；实际查看 `.agents/skills` 与 checkout 指南。B 在新目录实现并编译，所有改动数值 TU 都实际重编，不通过仅更名 archive 成员蒙混。保存 compiler/CUDA/flags、源码 diff、每一 archive 成员、ELF/map、完整传递依赖和实际加载模块承诺，原目录只读。

产物：`SOURCE_LOCK`、三臂差异表、B 可行性报告、descriptor inventory、逐阶段精确 job manifest、固定统计/验证/导出代码、失败与停止状态机测试。静态 build 不等于数值合格。

先用历史归档 raw fixture 和人工负例在 CPU 上走通 reader、ledger、export、privacy transform、clock parser；至少包括 reserve8/32 混写、缺 token、模块清单 string/object、reference/candidate receipt 字段不同、callback 假返回、旧 primer 计费残留、退出前导出、文件名碰撞/路径遍历。检查器不能在性能已产生后才第一次试运行。

### F0：参考与资格整批冻结

在**任何本轮模型输出**前，固定所有 S1 原始 R 输入/分支、候选资格输入、完整检查器、负例、资源与预算规则、源码/模块和预定调度。公共发布后逐字节全文回读，保存 immutable commit 和每个文件 SHA。不能只冻结 first job，后面随结果补资格。按合同必须依 R 输出构造的 oracle 字节/状态，先冻结构造函数与所有请求分支，再在 R 完成后固定产物，候选尚未运行。

### S1：独立 R 与三臂完整资格

先验证原 R 的字节承诺；每个新原始输入在独立 native process 中运行 R 两次，检验有限性、完整向量及解析 active state 的一致性。不能通过重复候选得出参考。需要更多 teacher/branch replay 的，每条分支都列入 manifest 并收费。记录合法 EOG 不得填充至 cap。

1. **真实 typed operands**：先 inventory 全模型实际出现的 `(weight type, dimensions, strides, padding, output layout, q)` 描述符。覆盖 Q4_K 与 Q6_K 的所有实现分支/不同形状类别、q1/4/32、合法尾列以及实际边界。性能代表 cell 可以少，数值 guard 覆盖不得缩水。引用已有捕获仅在 raw 字节、源/环境和完整 oracle 关联都可核验时合法；缺失就登记新 capture/reference 任务，不用随机/零值假装真实输入。
2. **独立逐列 gold、算术与完整所有权**：每个冻结真实 `(weight, x)` 输入，必须由未修改且未链接任何候选 patched 数值对象的原始 scalar R 逐列 q1 生成完整 gold，固定 R 的源码/对象/依赖与量化 activation 字节。G/B/C 各自直接对这个 gold 全输出逐元素比较；三者互相比对只是附加诊断，不能使共享错误通过。要求原严格 bitwise 合同（完整 F32 字节、NaN/Inf 先拒绝）；column order、padding、stride、输出 alias/生命周期逐项检验。任何 mismatch 停止，无临时 epsilon 放宽或只比 argmax。输出由 caller 独立持有，下一次调用覆盖 scratch 后仍完整一致。逐列 R/gold 操作均明确计入参考预算，不藏在一次worker中。
3. **全模型 M 桥接**：三个 whole 路径都对同 R 检验完整 151936 维所请求 logits，全部 64 层 active K/V、frontier、active length/position 与 token 生命周期。prefill 中所有请求输出，以及每个生成 step 和关键 reset/EOG/cap/capacity 边界完整检查。不能仅做局部 projection 数值就上 live 服务图。
4. **边界覆盖**：使用明确命名的输入/状态测试 q1、q4、q32、partial last chunk、物理 extent 之前/跨越/之后、C1024 容量边界与非法溢出、空/非法 descriptor、错类型/stride/output mask、EOG one-before/at-cap、立即停止及 reset 后再生成。合成容量 stress 明标 synthetic，只作正确性；自然 EOG fixture 不得用时间选样。缺自然 fixture 时注册 R 搜索成本，不伪造覆盖。
5. **实际物理执行**：记录 graph nodes、真实 q、original scalar-dot dispatch、每层类型、buffer device、输出列、kernel/quantization/copy 次数、reserve32、active extent 与 no silent fallback。确认 B 实际进入后端 loop，不是只改名字。q1 三路径应退化为同一合法单列语义，不通过重复输出制造 q4/q32。
6. **heavy/clean bridge**：同生成源码、算术 archives、参数及输入，区别仅已登记的观察 instrumentation。独立检查 complete vectors/state、physical contract 与输出生命周期；clean output、终点 state commitments 和每步 semantic tape 联结至 heavy 资格。heavy observer 的回调必须继续正确 graph 计算，不能复制后 `return false` 提前截断。clean 不运行 per-node device-property 查询、JSON 构造、重型 hash/export 或 profiler。

本轮 M 没有 draft accept/reject/bonus，不能把它们写成“已覆盖”；旧 D4 证书保持旧范围。target 的容量/reset/stop 则不能省略。编译更换、数学源码/ABI、graph 策略、oracle 或 guard 变化使相应资格失效。纯读者修复可离线重检已完整保存字节，不需自动 GPU 重跑，但保留旧失败与新 epoch，公开其时间，禁止宣称全源一次性冻结。

### F1：诊断整批冻结

S1 全通过后，发布精确四个性能 operand cell、三臂二进制/模块、全部 72 操作顺序、计时边界、固定分析、完整费用与 latest-start 计算。远端全文回读后才开始第一个 warmup。用已暴露开发根捕获，不打开新确认根的候选输出或速度。

### S2：72 操作的有界真实操作数诊断

四 cell 固定为 Q4_K/q4、Q4_K/q32、Q6_K/q4、Q6_K/q32。每种 type 选 inventory 中**预先规则选出的第一个合法 tensor**（按 layer index、tensor name、原 capture 顺序排序）对应真实输入；不能根据效果挑 tensor。需要尺寸不同时允许逐 cell 绑定自己的实际 shape，但同 cell 三臂完全相同。若缺 q4 或 q32 真输入，先在 F0 中登记有依据的新 R/capture；无法完成则停止，不降格为 synthetic 性能结果。

每 cell 三个独立 repetition block。每 block 按机器生成的三臂顺序启动三 fresh workers，每 worker 仅运行该 cell 的 **1 次完整 warmup + 1 次 measured**，同进程、同状态/参数、重新恢复固定输入，所有 q 行输出拷贝到 caller-owned memory；warm 不计入 estimate，但计入预算/总成本。总计：4×3×3×2 = **72 logical operations，36 warm + 36 measured，36 workers**。q1 的正确性负对照属于 S1，不暗加免费 timing。

偶数 cell 用 GBC/BCG/CGB，奇数 cell 用 GCB/CBG/BGC，三 repetition 各一行。每 cell 每臂在每位置出现一次；全局每个有向邻接各四次。这不产生独立根样本，也不平衡跨 cell/block 的首尾 carryover。fresh process、固定 worker 间 policy 与 timestamp/频率记录限制但不消除后者。

每 worker 的权重/operand 在暖态时驻留；state/input restore 对三臂一致并单独计时。这里只测**同路径一次完整预热后的第二次调用**，一次warm不证明稳态。worker间固定等待policy及telemetry cadence须在F1写明；不能看到速度/频率后临时补warm、延长等待或挑较稳定区段，任何新增模型调用都收费并需要新登记。主诊断 operation 时间从合法 ready state 开始，到全部输出已同步可用结束，包含其 activation quantization、全部 launch、完整 output materialization/copy 和必要 sync。另报 restore、startup/load/hash、warm、receipt/serialization、worker/caller。CUDA events 必须覆盖正确 stream、先后有已定义 fence；若事件只覆盖 device region，标明 device interval，不能冒称完整 operation。

主operation计时使用host单调时钟，结束点必须晚于最后device fence和全部owned-output复制完成，不能把异步enqueue返回当结束。device event仅作另列嵌套指标。仪器化 profiler 在独立预注册任务中执行并收费，不能混入36 clean measurements。所有臂有共同最小预分配physical counters；若无法消除观察者随图节点数放大的开销，结果需明确“instrumented implementation”，不能归因到无观察者production。不得猜测residual。

报告四 cell 全部单次值、warm 值、三 block 配对 log-ratio、算术总量与几何比、全部失败和冷启动。样本少且 operands 已暴露，**描述性结果，不做 population inference、不报 kernel 优化因果、不将 36 操作当 36 独立根**。S2 不能重算或替换 #216 的约 5.62%。

## 4. S3 条件性新根服务确认

### 4.1 是否值得做

S3 仅在 B 与其他两臂完整合格、S2 无未解释错误、资源允许且稿件仍需要“三实现的新输入部署比较”时登记。决定文件在新根任何模型输出前发布，写明为何已有诊断不足。B 更快、C 更快或方向不确定均可进入，**不能以正号或显著性为准入条件**。如果只保留局部机制证据、不再提出新根性能主张，S3 直接不做。S2 看不出差异不等于等价；不做 S3 时清楚写“尚无新根确认”。

本协议选择 **12 根**，不是运行后从 12 加至 16。12 比 16 更省资源且便于全局完整排列平衡；16 只能在尚未打开新根输出前另注册完整预算/顺序/统计修订，不能用于可选停止或扩样追显著。

### 4.2 新根选择与 oracle

固定公开且已有访问权的 code/math 数据快照，6 code + 6 math。F0 登记数据版本/license、完整 universe 与选择函数、去重规则、tokenizer/template SHA、输入条件；F2 前输出最终 roots.json。只按输入元数据筛选：自然 prompt 1–192 tokens、C1024 可容纳 prompt+cap128、不截断、canonical problem ID 与 prompt 规范化 SHA 去重。按 `SHA256("heterospec-q32-strong-v1:" + canonical_id)` 排序，每域取前 6。不能根据 EOG、生成正确率、接受率、速度或答案选根。

排除历史全部开发/资格/计时/失败使用的 code/math 根、其变体及相同文本；包括 #216 四 MATH 根 333/313/315/654、#211–#215 和所有较早可恢复 manifests 中的根。输出可追溯 exposure exclusion table。无法完整恢复暴露记录时，只能称“在可恢复清单中未暴露”，不能承诺严格盲样本；若独立新根是目的，就阻断并补齐记录。

输入短不能自动宣称代表所有 code/math。目标是此预定义可行输入集合的有限 panel。cap128 固定，原生 EOG 提前结束照实保留、不补 token、不替换根；报告每根实际长度。不得强迫所有根生成128再叫自然服务。

每根同 pristine R 两次独立请求，至少 **24 reference requests**，完整新 oracle 字节在任何候选请求前冻结；每根每臂至少一条完整 heavy 桥接 **36 candidate requests**。复杂边界/额外 oracle 分支另算；不能宣称这 60 已经包含全部 S1 资格。新 roots 对三臂 greedy 完整序列一致才有配对服务比较。

### 4.3 F2 与服务顺序

全套实际 12 roots、24+ reference 任务、36+ bridge、三臂配置、144 fresh worker、288 requests 的 IDs、顺序、源码、统计、结果 schema 与费用**一次性**冻结。依次做重复 R → oracle 内容冻结 → heavy 资格 → 最终准入复查 → clean panel。F2 规则和 jobs 在新根 R 输出前已发布，只有预声明 oracle SHA 字段在 R 后填入；所有 candidate/timing 输入不得借此更改。

12 根 × 3 projection × 4 轮 = **144 measured + 144 matched full warmups = 288 requests**。最简单无隐藏常驻状态实现：每个 root×round block 连续三个 fresh native workers，每 worker 对同一根/同一 cap/同一 M 路径 warm 一次、完整 reset、立即 measured 一次。因三路径可能独立 ELF，本设计不假定 runtime 可在同进程安全切换。共 144 worker/model loads，全部进预算和窗口；若成本不容纳，跳过整个 S3，不运行后改成异步常驻池。

顺序由 `design_checks.py` 固定：每 round 根槽位旋转 0/3/6/9；`root_slot mod 6` 对应四轮臂顺序为：

| slot mod 6 | round0 | round1 | round2 | round3 |
|---|---|---|---|---|
| 0 | GBC | BCG | CGB | GCB |
| 1 | BCG | CGB | GBC | CBG |
| 2 | CGB | GBC | BCG | BGC |
| 3 | GCB | CBG | BGC | GBC |
| 4 | CBG | BGC | GCB | BCG |
| 5 | BGC | GCB | CBG | CGB |

每 round 六排列各两次，四轮合计每排列八次；每臂全局各位置 **16次**（一个位置三臂合计48），每个有向臂邻接16次。6 code/6 math 槽分别占0–5/6–11，每域同样平衡，每臂各位置8次。

**单根四轮不可能覆盖六排列；并不声称单根或所有跨 block/跨 worker 邻接全平衡。** 各根获得四个不同排列；每臂位置频数为1或2，有向邻接不完全平衡。输出每根 position/carryover 明细和全局/域级矩阵。root 在 round 的宏观位置有确定性轮转但不完全覆盖12个位置。记录所有间隙、温度/频率、干扰与时序；不把 deterministic schedule 当完全随机试验。不得将全局平衡替换成“每根完美平衡”。

### 4.4 时间、成本与统计

主 endpoint 是每 measured request 的 resident complete service time：同tokenizer后输入就绪、开始该请求的完整context reset之前起表，至合法终止、全部owned outputs ready与最后必需device fence完成止表；**三臂都把请求初始reset算入service**，prefill+decode+必要内存操作也都包含。上一warm的收尾不得转移本次reset成本，且reset后active state必须符合空请求合同。边界函数名称/代码行必须F2固定，不把执行后observer写盘悄悄移入移出。另拆prefill、decode、stop/reset、输出copy、unassigned residual；elapsed与嵌套时钟不相加。模型load/文件SHA/启动/完整warmups/序列化/退出/所有失败的caller总成本另报。该新边界不追溯改写旧#216的service定义。

主比较预定 **C/B**：对根 i 四轮算 `d_i = mean_r(log(T_Cir/T_Bir))`，报告 `exp(mean_i d_i)` 和 percent change。每根等权，12 根为推断单位。95% percentile bootstrap，20,000 次，固定 seed 20261110；在6 code与6 math层内分别重抽根，每次连同该根全部轮次，最终两域等权。CI 是有限新根 sampling 的近似，不覆盖所有硬件/题型/上下文。轮次不是48独立根。

次比较B/G、C/G为独立标注的同一secondary family，用每个97.5%区间（Bonferroni控制家族95%）。展示全部根/域/轮次、总服务时间之比（工作量加权描述量）及中位数，不能用pooled total ratio替代主根等权estimand。固定实际重要性阈值1%：C/B的95%区间全部低于0.99才称“C在该panel上至少1%更快”；仅低于1可称统计方向证据；跨1为不确定，不能称相同。B至少1%更快须B/C区间上界<0.99，等价地C/B区间下界>1/0.99，不能用>1.01代替。有限等价仅在预定C/B的同一95%区间完全落入[0.99,1.01]时作保守、明确以B为分母的范围表述。

不做效果导向可选停止、删慢点、事后换主比较、补根、选择最佳round。若设备干扰、失败或资格错误破坏任一完整 root block，停止面板并保留全量；没有成功 arm 的选择性 native 重跑。未完成面板仅做明确标注的部分描述，不能作完整确认。若确需重启，另开新 epoch、完整新登记与预算，旧尝试始终计费。

没有可靠既往新根方差可给出准确 power，故不承诺12根足以证明1%效应。CI 宽也是合法结论。复用旧已暴露4根统计不能声称 power-based 新样本保证。

## 5. 预算、资源、窗口与停机

旧 32B 起点必须逐字节核验为 **514 requests，652026 conservative rows**，原 ceiling640/2000000，余126 requests /1347974 rows。旧8B与RTX账本完全分开。启动时发现新历史消耗则更新继承值，不能仍硬写514。

这里提出**有待授权的阶段上限**，不是新增授权或已经证明足够：

| 阶段 | 计划增量上限/刚性保留 | 准入条件 |
|---|---|---|
| S0 | 0 GPU requests | build/CPU成本另报。 |
| S1+S2 | 先请求最多256个新增32B logical requests，其中72为S2、16为非选择性失败/收尾，余最多168用于参考/资格/必要诊断 | 精确清单足够才申请并冻结；不是把旧剩余126换目录重置。若全用，累计770，比原640明确增加130。 |
| S3 | 再请求最多384新增 requests：288 warm/measurement，至少24 R+36 bridge，余最多36用于额外必要分支/失败/收尾，其中至少16保留到正式准入 | 精确资格需要超过可用20个额外槽即停/重新登记，不能削掉门禁。S1+S2与S3若各用满，累计1154。 |

实际阶段 ceiling 可在**任何本轮模型输出前**根据完整 manifest 下调，不能在效果出来后追加样本。预算增加必须显式批准并保留原640 ceiling历史；本 PR 不修改旧注册。S3 若不激活就没有这384额度。若 S1 全部资格无法装入168或 S3额外20，报告缺口，等待新范围/额度决定。

行数不用 request 数粗略推断。每项列出 replay/prefill/teacher/生成/真实验证行、边界/negative 的零forward依据、完整 formula 与最大 cap；采用更保守的实际可证明界限。F0/F2 汇总 `historical_rows + Σ reserved_rows <= prospective_row_ceiling`，未明确修订前2,000,000仍有效。一个 worker 内多个 operation 逐个计为logical request，不能藏在一次 launch。模型加载、空输入expected-reject、启动后fail、R repeat、warm、profiling都计；reservation/失败无退款，取消但未启动另列状态与保守承诺，不倒删 ledger。

资源仅用新的明确分配：单 GPU、私有 UUID绑定、GPU0/外部任务保护、原 minimum 1GiB GPU reserve与原RAM限值、磁盘至少100GiB **且**大于精确保存量+余量。旧捕获近159.6GB，因此100GiB不是足够容量证明。先核算所需raw/state/archive/临时重复存储；空间不足停止，不删旧数据。沿用授权CPU核心/线程需要再核对；禁止未经允许更改功耗/时钟/VPN/driver、sudo、reset、杀其他作业、租卡。清洁计时无并行build/download/profiler。

新 `allocation_start/end_utc`、`last_new_worker_utc`、`delivery_deadline_utc` 均需填写，旧05:00/08:00已经过期。whole-stage admission 按job类别求和：`Σ类别(剩余该类worker数 × 已观察同配置完整caller最大成本 × 1.25)`，明确区分S2 projection micro-worker、scalar R重复/逐列gold、heavy全模型桥接、S3 full-model warm+measured等；每类包括其load/hash/warm，不能拿轻量projection成本估计32B模型加载。再加未包含的固定worker等待、导出/压缩/传输/全文回读实测预算及至少900s收尾余量。无同类同配置成本时，登记有预算的开发pilot，不能用service代替caller估算。不要重复计入已包含warm/primer。单worker timeout合理预先确定，距截止至少timeout+60s才启动。

窗口/余量/资源不够，整阶段不准入。已授权健康worker不为插入新任务中断；资源安全触发时安全停own任务并保留取消记录。暂停后不跳到余下有利臂，恢复需要新完整性与窗口决定。GPU lock、guard、native workers退出与释放必须可验证。

## 6. 全局事故策略与交付验收

F0/F1/F2 各阶段必须有 complete-file remote readback，而不只是commit hash。注册hash链绑定到首个实际request时间；变更任何执行/统计/检查source都开新epoch。发现freeze后错误先停止，不悄悄覆盖。完整raw仍可支持纯离线修复时复算全部，明确“post hoc reader correction”；不让failed输出消失，不把archive replay称GPU复验。

每次attempt保留：job ID/parent/phase/ordinal、source/build/model/oracle/fixture/config SHA、开始/结束/时区/单调clock、资源样本、全部stdout/stderr/exit/timeout、native与caller成本、reservation与consumption、完整输出/状态承诺、错误与决定。有效负结果不算失败；校验不一致不是统计outlier。

交付包括：

- 冻结计划/清单/源码依赖、资格完整表及raw位置承诺、拒绝/失败/未启动清单。
- 所有warm与measured receipts、单根/单cell/单round数据、固定脚本、统计结果、全部历史+新阶段账本。
- 原raw保留只读；sanitized public text包不含权重、账号、allocation UUID或不相关主机信息。原始数值载荷可受存储/授权限制，缺公开payload需明示。
- 在新空目录逐文件字节/SHA恢复，再仅用下载public bytes复算所有表与计数；防绝对路径/`..`、覆盖与归档chunk误解。
- 单列资格复用、host本地数值验证、公开字节复算、独立跨GPU重验四个不同层级，逐项标记 `passed / failed / not-run / unavailable`。
- 完整 limitations、残留观察者开销、非全平衡邻接、旧与新graph政策分离、有限样本与未做D4。报告 GPU/lock释放。

只在以上通过后提交结果PR。没有自动merge、Release、论文替换或后续D/E。设计也不能保证不再出错；它要求错误被前置检测、如实保留并使执行停止，而不是事后装饰成无误实验。
