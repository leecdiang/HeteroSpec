# B570 实验 PR 工作包
状态：设计/CPU工作包；新 GPU 请求为 0。native extension未实现、未编译、未native验证。
建议目录：`benchmarks/b570_producer_consumer_boundary_v1/`。
建议 base：PR150 的 `codex/b570-native-delivery-20261026`，起点 `9f03bead68462326497b03edb0d2d80f8f2fd4c3`。

## 1. 目标与严格必要性

最值得新增的问题是：在已经有干净源码重建和真实请求资格的 Qwen3 路径上，**producer 改变后的完整数值状态，是否改变局部 consumer 能保持的 reference**？

旧 Llama Q6_K 的4个暴露自然输入已经完成 whole-KV × 初始logits 因果交叉；再次复现AA/AB/BA/BB不会显著增加论文新颖性。新实验应该换成已成功移植的Qwen3 GQA/AV-preserving实现，并用按输入属性冻结的新自然输入，连接“成功port”和“producer-state边界”。

不要求新增B570速度正例。当前正式复现formal.exe只有qual模式，且PR134/148是target+draft都在Vulkan；PR143的性能结论是不同的CPU-draft/thread8路径。把它们混在一起拟合速度模型会引入比所解释现象更多的契约差异。

## 2. 实际可复用资产

全部来自PR150 head所继承的 `benchmarks/b570_native_reproduction_v1/`：

| 文件 | 实际能力 | 本实验需要的差异 |
|---|---|---|
| `native/formal.cpp` | R/PQ/QB完整k1请求；prefill逐ID；ctx1024/batch512/8threads/F16KV；全部36层几何检查；full logits/cycle | 新ArmSpec、显式prefill schedule、boundary0 export/import、consumer-only resumed request |
| `native/query_head.h` | shared-KV PQ/QB图构造，q≤4一般检查 | 数值代码保持原字节；不把prototype一般检查当request层全shape资格 |
| `patches/03-request-bridge.patch` | native接入仅q2/4、key256/512、Qwen3(32Q/8KV heads, d128) | 原条件保持；新producer schedule严格落在1/2/4，记录实际路径 |
| `native/raw_capture.h` | QB首次VERIFY层0的Q/K/V/mask与QK/softmax/AV/final | 当前不捕获producer；新producer checkpoint使用sequence state，不伪称此hook已有q4 producer stage数据 |
| `native/stage_replay.cpp` | 固定真实q2/key512 fixture及其q1切片 | 本实验默认不扩大到q4算子网格；仅有具体归因需要时另加真实fixture |
| `run_native.py`, `freeze.py`, `audit_request.py` | bounded Job监督、module/hash、完整端点/向量核对 | 扩展新输出schema；不重新执行整个旧delivery协议 |
| `CMakeLists.txt`, `prepare_source.py` | 源码重建入口 | 新target链接同一已经资格的数值库；记录driver新身份 |

固定upstream `0cae43063cf15170e91a2ff4d034da0ecef4a1b2`；原PR131/132/134 overlays及所有数值DLL按PR148 manifest。模型使用 `MODEL_IDENTITY.json` 中的Qwen3-8B-Q8_0和Qwen3-0.6B-Q8_0；两模型仍Vulkan、8threads、FAoff、F16KV。不暗中换CPU draft。

状态恢复的**代码模式**参考PR145可读的 `benchmarks/b570_final_causal_closeout_v1/native/worker.cpp` 和 `code/prepare100.py`：
`llama_state_seq_get_size/get_data/set_data`，clean receiver，完整initial FP32 logits，位置核对，greedy first-token ownership。旧worker依赖10threads/Q6_K/额外私有symbols，不能直接拿旧EXE跑新Qwen，也不能把旧sham资格继承过来。

## 3. 明确两个实验因子

### Producer

固定producer实现为PQ，target context UB4/output4；draft不参与producer因子。

- P1：按native IDs逐个caller提交，除全prompt最后一个位置以外全部logits=false。
- P4T：固定每次提交4个IDs；尾长1/2直接提交；尾长3固定分成2+1。只在全prompt最后一个位置请求logits。这个尾块规则在freeze前写入每个input的完整 `caller_lengths`。
- 两者token IDs、绝对positions、mask语义、Qwen权重、线程和所有context参数相同；唯一主动变动是完整producer caller recipe。
- 选择P4T是因为现接入只含q2/4；不能称其与任意UB4内部分块相同。每个实际图的occupied width和fallback状态要记录。

完成prefill后同步，保存完整sequence KV序列化bytes（全部层+位置）和完整initial FP32 logits。producer结束前继续其自然C1生成，得到自然基准。此时尚未选择/强制任何参考后缀。

### Consumer

所有consumer从clean target context开始，context参数相同，载入所指定producer的完整sequence state；initial logits通过与native formal.cpp相同的finite-first-max规则只采样一次，然后遵循原pending-token规则。每个consumer固定自己的layout，不能在同context中途切换。

- C1：target-only，每次消费一个pending token；无需draft。
- C_PQ：原k1 speculation，target verify q2，PQ attention。
- C_QB：原k1 speculation，target verify q2，QB attention。
- draft在每次spec consumer中从同一prompt做原逐ID prefill、同一模型/UB1，独立重建；producer因子只改变target state，不能顺便改变draft producer。

三consumer都必须保存complete IDs/EOG/terminal/stop和全部cycle reconciliation。所有时间是diagnostic，不从此恢复型请求提取服务速度，因为producer已被外置且snapshot/import并非生产服务路径。

## 4. 输入冻结与最小矩阵

### 静态选择

目标8个此前未用于当前实现实验的新自然输入，按source revision、task ID、规范化文本排除历史，使用固定hash排序；任何新输出都不能用于选例。

两长度带每带4个，建议64–192与256–352个formatted native IDs；cap128，硬约束N+128+2<512。长度census必须在forward前证实可填满。尽量让两域都出现，但本研究不是domain×length因果估计；若当前候选池不能正交，明确报告。不能通过截断或拼接制造自然长math或短code。

本PR固定8例与152primary slots。如静态候选不足，停止在forward前，另作可审查的设计修订；本PR工具不会自动缩成4例或改变矩阵。不能运行后因为无触发追加例子。最终PANEL.json必须含exact native IDs、模板/来源/长度、selection_hash、完整P1/P4T schedule及曝光排除结果。输入不匹配shape/extent的处理是预先排除，不是查看输出后的剔除。

### B0：新增driver的恢复与speculation能力对照，32请求

固定已有HumanEval/38（181 IDs）与HumanEval/115（349 IDs），沿用原cap64（不是主矩阵的cap128，也不是新结果中的盲例）：
2inputs ×2producers × natural C1/resumed C1 ×observer off/on = **16完整请求**。

自然轨迹中捕获prefill donor；resumed C1必须重新读回全部KV字节、位置、initial FP32并逐项等于donor，再重现自然完整endpoint。所有resumed（含off）需保存实际post-import restored_boundary KV/initial payload；CPU必须重哈希原donor与实际readback，不能只收restore_roundtrip布尔或donor摘要。heavy initial_logits还必须匹配真正消费的target_initial向量。至少capture-on/off完整输出相同。P1的自然R端点还应复现PR148既有reference。P4T为新producer，不要求与P1相同。

再追加同两个历史controls的P1 producer ×PQ/QB consumer ×natural/resumed ×off/on = **16请求**。自然PQ/QB各自保持layout不变，保存其producer bytes；必须与相应P1 donor逐字节相同。每个layout的resumed轨迹匹配自己的natural完整endpoint、全部cycle/state及full logits；自然路径同时复现PR148的原reference。B0合计32请求。此门槛专门排除新增speculation/resume bridge的实现缺陷，不能只凭C1恢复sham替代。

若任何恢复/consumer-specific sham失败，停止受影响donor/consumer交叉；可保留自然producer研究，明确“未建立恢复契约”。不能直接继续KV因果结论或把新driver缺陷归为局部修复不足。

### B1：8输入的主矩阵，120请求

| 部分 | 数量 | 目的 |
|---|---:|---|
| 每input的独立严格R（UB1/output1、逐ID prefill与continuation），一次 | 8 | 验证UB4的P1+C1确实保持所指定R；不能仅凭物理q1假设context容量无影响 |
| 每input的P1/P4T自然C1，off/on各1 | 8×2×2=32 | 自然producer基准、observer guard、16个captured donor |
| 每个donor的fresh resumed C1，一次 | 8×2=16 | 每个新输入自己通过endpoint/state own-path sham |
| 每个donor的C_PQ/C_QB，off/on各1 | 8×2×2×2=64 | producer × local-consumer交叉，PQ/QB全向量与cycle比较 |
| **主矩阵总计** | **120** | 6个自然/consumer科学格各有off/on轨迹，另加16个恢复sham和8个严格R |

含B0总上限 **152完整model请求**；两个重复是observer guard/稳定性检查，不是152个独立任务。严格R是UB1/output1；P1+C1的UB4/output4必须逐输入匹配R，否则该input不具备指定reference资格，但自然差异保留。consumer每个fresh target上下文，可在同worker中复用已加载模型；每input做一个fresh model-worker便于内存/故障隔离。自然producer状态导出后清理producer context再启动consumer，避免无必要地同时保留所有context。

不需要新operator replay，也不需要完整十几个caller partition sweep。本PR固定152primary slots，不包含自动缩减或追加。

## 5. 什么结果有信息

定义Y(p,c)为完整输出，S(p)为完整producer checkpoint，L(p)为initial full logits。指定reference为独立严格R（UB1/output1），要求P1+C1与之逐输入相等；不动态挑参考。producer条件比较同时以各自自然C1为基准，明确它与严格R是两个不同判断。

| 结果模式 | 可以支持的论断 |
|---|---|
| S(P1)≠S(P4T)，但对所有c完整Y相同 | 数值producer变化没有在该有限panel转为输出差；不是普遍无影响，也不追着新正例加样本 |
| Y(P1,C1)≠Y(P4T,C1)，且每个producer内C_PQ=C_QB=C1 | producer决定了可保持的reference；局部consumer忠实保留各自producer，无法把错误producer恢复为指定reference |
| 相同producer下PQ=QB≠C1 | PQ/QB一致不足以建立serial-reference资格；局部修复范围不足，即使实现间bitwise一致 |
| 仅某producer下PQ或QB失效 | producer与consumer有适用条件交互；报告具体状态/shape，不把失败归为泛“Vulkan不支持” |
| 相同producer下PQ≠QB | 端到端布局转换反例；冻结最小坐标，停止该scope性能推论 |
| donor恢复sham失败 | 不能作producer-state移植因果论断；自然轨迹结果仍可单独报告 |

所有P4T交叉终点限定于**boundary0 clean-receiver contract**。没有该producer/layout自己的natural-vs-resumed sham时，负结果不能直接宣称自然生产路径失效。P1的consumer-specific历史controls提供driver资格；P4T只证明此明确重构契约内的producer-state总效应。

这测试的是**完整producer数值状态（KV+初始logits等必要边界状态）的总效应**，不能直接等同“KV是唯一原因”。只有需要区分KV和initial logits，才可增加固定少量2×2 cross：按冻结ID顺序取前两个自然端点不同的输入，KV∈P1/P4T ×initial logits∈P1/P4T，在共同C1下运行两repeat=16请求；这是结果条件化的解释性跟进，不是发生率样本，预算在首次forward前登记。默认此项关闭，独立复审决定是否纳入。

q4 producer的“实际走PQ”和“已经保持串行reference”是不同结论；后者必须由完整请求结果支持。当前真实stage fixture仍仅q2/key512，不把P4T矩阵自动称为所有q4算子资格。若要定位具体q4操作，后续捕获必须来自本次真实producer，先做native own-path replay再比较PQ/QB；旧fixture拼接或q1切片不能代替。

## 6. 具体代码接口

建议新增driver沿用formal.cpp类结构，不修改旧formal.cpp：

- `ProducerSpec {layout=PQ, caller_lengths, final_only_logits=true}`。
- `BoundaryState export_boundary(Context&, prompt_ids)`：synchronize；记录KV min/max；保存sequence bytes与完整initial logits；所有bytes内容地址命名；提供metadata版本和context/source identity。
- `Context::restore_boundary(BoundaryState)`：只在刚初始化的空context调用；verify model/token IDs/positions；seq_set_data返回长度必须全匹配；seq_get_data roundtrip逐字节相同；不能调用额外model forward去“补状态”。
- `sample_initial(saved_logits)`：同formal.cpp的first finite maximum；所有vocab项检查finite；记录tie rule/top2；第一次pending状态跟自然路径一致。
- `run_consumer(ConsumerSpec, BoundaryState, prompt, cap)`：原generation循环；draft serial prefill独立；target不再次prefill；完整记录accept/reject/trim/kept position；cap/EOG严格原样。k1非终止accept必须提交bonus，只有proposal本身达到cap/EOG才可省略；每cycle的target_kv_max/draft_kv_max须为keep-1，终止后不能多执行cycle。
- `run_natural(ProducerSpec,C1)`：prefill后可capture，继续原单步完整输出，形成每个donor的own-path endpoint。
- `audit.py`：独立CPU，解析结果和payload而不导入driver，分别验证自然/恢复相等、PQ/QB state/logits相等、serial-reference资格和失配坐标。
- `analyze.py`：输出8input×2producer×3consumer表，所有false/null/NOT_RUN都保留。

新的CLI建议为 `boundary.exe OUTPUT TARGET DRAFT PANEL SLOTS`。这不是当前formal.exe的已存在接口；实施PR必须提供该新target和README。旧现有接口依然是 `formal OUTPUT TARGET DRAFT PANEL qual INDEX STUDY_ROOT`，只接受INDEX0..3，不得声称当前runner已能执行此计划。

## 7. 执行与停止条件

Host动作顺序：

1. 切到新实验branch，读取既有PR150 ACCESS及已验证本地runtime路径。复用包，不重新运行全部旧delivery。核对fixed source/runtime/models，记录当前driver。
2. CPU-only冻结candidate census/排除/8-input panel和caller schedules。
3. 编译新增native driver；五数值DLL保持PR148版本，若实际重编则记录新身份并先资格，不声称字节未变。
4. 冻结PLAN/SLOTS/BUILD/MODEL/observer/source；每个driver失败尝试有独立identity和日志。
5. B0的32请求先完成且CPU审计通过；再按固定顺序运行B1，每input independent worker，所有raw result立即落盘。
6. 独立CPU重建matrix、sham、vector inventory、geometry、budget；用既有manifest系统交付必要payload和auditor；在结果PR报告所有失败和未运行项。

立即停止受影响scope：wrong model/runtime/tokenization、非finite、actual q/key不在声明域、GPU placement错误、driver请求超过cap、restore roundtrip不符、own-path sham不符、observer改变自然endpoint。数值失败不重试；本152-slot freeze没有自动技术retry。需要技术重跑时另记录amendment与新attempt inventory，原始152条不得覆盖；不能因无差异/负结果扩panel。

资源预算不是科学结果：152请求的总owned上限建议3小时、单请求180秒、必要恢复payload上限8GiB，在host静态检查后冻结；超过任一上限记录未完成，不动态翻倍。并行GPU workers=1。主数据没有新性能claim，不使用host wall timer来宣称GPU专属阶段成本。

## 8. 为何不把“可预测成本”与本PR捆绑

有判别力的成本模型需要一个前瞻性预测：只用独立calibration的producer/consumer成本和已固定逻辑工作，预测未测panel中M/C或GS/QB的方向，再在干净完整服务窗口验证。当前B570 source可恢复数值状态，但没有这样一条同契约干净计时runner；引入它相当于再做一个实验。

本轮可先提取已有PR143与新矩阵的call/row counts，检查成本解释是否具备可识别性，不从有readback/import的诊断时间拟合。若论文确需可预测成本作为第二主贡献，再新立固定预算的target/draft placement、计时和held-out预测验证；不把后验分解已知总时间称为预测成功。



## 可执行CPU工具与原生状态

实际CPU入口、152-slot生成/审核和raw记录格式见README.md与HOST_HANDOFF.md。work_package.py已实现CPU规划与验证；上述native boundary.exe函数是host实现规范，并未由本PR提供已编译实现。计划的status保持DRAFT_UNBOUND，所有new结果为null。
