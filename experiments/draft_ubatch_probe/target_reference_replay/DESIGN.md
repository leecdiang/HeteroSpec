# #183 后续严格 target-reference qualification：可执行设计与资源门槛

状态：**设计 + CPU 离线证据工具原型；没有启动 GPU 实验，没有使用用户设备，没有修改或发布现有 PR。**

结论：可以先在云端完成查询规划、完整性检查、字节证据比较、成本估算与反例测试。不能仅凭这些工具或 #183 的 CPU PASS 声称 Qwen/Smol 的 GPU target 已经严格等于旧 R。下一步是一个有明确部署绑定的小型 native capture / replay bridge，而不是直接扩大全 GPU 矩阵。

## 1. 本次独立审读到的事实

初始冻结审读 #183 head `2b6f0efc47de3efd7d739042065409e8bc21d526`，特别是 [test_native.cpp](https://github.com/leecdiang/HeteroSpec/blob/2b6f0efc47de3efd7d739042065409e8bc21d526/experiments/draft_ubatch_probe/test_native.cpp)、[README](https://github.com/leecdiang/HeteroSpec/blob/2b6f0efc47de3efd7d739042065409e8bc21d526/experiments/draft_ubatch_probe/README.md) 和 [stress-q8 receipt](https://github.com/leecdiang/HeteroSpec/blob/2b6f0efc47de3efd7d739042065409e8bc21d526/experiments/draft_ubatch_probe/evidence/stress-q8-RECEIPT.json)。

15:51 UTC 再次核验PR已追加至head `8aebc64d2075ef7fca62e352b926ff6be201c06d`，仍是open draft、未合并。重新读取test_native.cpp的Git blob仍为`3494d5a0ad465e8bfea0ed77042ebf88b54ca3e7`，原实现不变；并读了新增的[ORACLE_SCOPE.md](https://github.com/leecdiang/HeteroSpec/blob/8aebc64d2075ef7fca62e352b926ff6be201c06d/experiments/draft_ubatch_probe/journal_boundary/ORACLE_SCOPE.md)，其prompt producer澄清与本设计一致。本次不改动该PR。

- test_native.cpp:17–37 的 reference 是 fresh CPU context、物理 ubatch1，每个 prompt token 分别调用 decode。candidate target 是普通未 scoped 的 ubatch1/output reserve4；不是 #151 scoped QB target ubatch4。draft 变动为 ubatch1/2/4、output reserve 仍为1。
- :55–58 对四个 target verification rows 都做完整 f32 向量比较，包括第一次 rejection 后不会提交的 proposal 前缀。这个覆盖方向正确。
- :79–94 的自由 greedy endpoint 和最终 retained KV 有独立检查；最终 KV 的 expected prefix 来自输出与终止分支，避免只相信可一起改错的 history。它不是每次 commit 的原始 KV 证据包。
- :106–107 的 `initial_logits_equal_scalar` 是 **draft prefill** 检查。严格 target qualification 需要独立的 **target initial logits** gate，不能用同名近义字段代替。
- 当前 journals 主要保存 IDs、分支、计数与布尔结果，没有给独立 GPU 审计器提供每行完整 logits、每次 commit 的 canonical KV、逐 caller 生产记录和原始部署证明。
- 强化 norm 的 synthetic fixture 改善了通用 history probe，但文档保留了一个 continuation logits 看不出 discarded-state、serialized sequence 能检出的反例。只测一个后续 token 或只测 endpoint 不能替代状态比较。

本工具只重新读取这些已发布 CPU journals 并生成计划，没有重跑模型。每种模型 75 cases、114 cycles，可导出 531 个 target-vector 使用点（含75 initial）、189个 commit、126条 maximal fresh paths。朴素独立查询需5673次 scalar token evaluation；前缀链方案需1518次。这些是根据实际记录的 token/分支计算的**未来回放计划计数**，不是已经执行的 replay。四个模型并不提供300个独立业务样本；相同设计的75场景重复在不同模型字节上。本地native.stdout的原F32/Q8 JSON哈希相同，stress两者也相同；发布的attempts.jsonl另有独立源哈希，因为这些日志没有保存原始向量。

## 2. 先定义“等于谁”，否则无法资格化

目标合同为：在登记的有限部署、请求和生命周期范围内，candidate **target** 的每个实际 proposed prefix 的全部目标 logits、每次 committed active KV、逻辑 positions 与输出 frontier，对匹配参考产生相同位模式及语义。draft 的 logits/KV/proposals 不必等于 ubatch1；但每个改变后的实际 proposal tape 都需要新的 target 覆盖。这里没有证明随机采样分布等价，也没有证明任意输入或任意设备上的数学恒等。

必须把四种对象分开：

1. 归档的旧 R endpoint 记录：只能保持原证据范围。
2. 重新执行的、完全绑定的旧 R 部署与完整 producer/lifecycle：需要精确源、模块、模型、runtime/device 等身份。
3. 新建 fresh-context scalar R 参考族：适用于纯净前缀回放，不能自动等同 resident-reset 旧 R。
4. #183 CPU scalar fixture：只支持它记录的 synthetic CPU 场景。

[冻结 #151 worker](https://github.com/leecdiang/HeteroSpec/blob/29511ed91eb9f3d9773cfdda53e3554b0f4ad08b/scripts/experiments/rtx_scope_transfer_v1/worker.cpp#L74-L93) 的 ubatch1 **不表示 prompt 每个 token 单独 caller**。:136–137 区分 P1 tokenwise 与一般的 whole-prompt caller，后者只请求最后一行 logits。#183 oracle 改为每个 prompt token 独立 caller并请求 logits。物理 ubatch、caller宽度、output mask/reserve、graph 分配都必须登记。工具中的 `historical_prefill_then_scalar` 名称仅指这一个 prompt 调用形状，不声称完整旧 R 身份。

另外 #151 :124–129 resident 路径复用 context 后 `memory_clear(false)`，其 prior requests、dirty tail、allocator/graph 历史和 fresh allocation 不同。若原承诺覆盖 resident R，应分别登记该生命周期及预置历史，并证明与所用 fresh R 之间的桥接关系；否则准确命名为 fresh R 范围，不偷换 old-R。旧 endpoint equality 不能被“source 看起来没变”升级成 full-vector/KV equality。

部署 manifest 至少冻结：target/draft GGUF与tokenizer/EOG映射、源及所有数值模块/依赖/可执行文件、构建选项和编译器、driver/CUDA/cuBLAS/JIT/cache身份、GPU与计算能力、线程、offload/placement、KV dtype/layout、n_ctx/n_batch/n_ubatch、output reservations、scope/layout selector、flash/matmul相关开关、greedy tie-break、caller分割和每caller logits mask、sequence/position、reset/fresh/历史契约、observer版本。候选和reference身份分开，摘要不能代替可读manifest及原始证据。

## 3. 分开两条轨迹，不让 oracle 帮 candidate 做事

### A. candidate 的真实自由运行

先由各 draft ubatch 的真实模型产生 proposals，按原 target accept/correction/bonus/trim 算法执行。捕获所有尝试，包括失败/中止。不得把 oracle 的正确 token 输回 candidate、用 reference KV 修复 candidate、或只重跑有利输出。

每次 target call 捕获 caller IDs、positions、sequence IDs、logits mask、logical/captured row index、实际物理切分、scope/shape/placement证据。完整拷贝 initial + verification四行 f32，不能只保存 argmax、margin、被接受行或第一拒绝前的行。字节必须在底层输出缓冲区下一次被复用前完成同步与独立深拷贝。

每次 commit（包括没有cycle的initial stop）捕获下节定义的active state和frontier。按照完成记录产生 canonical query keys：完整参考部署、prompt边界、prompt/continuation生产recipe、目标模型/tokenizer、context size、完整 tokens/positions/sequence。相同 token串但不同 prompt边界、mask、部署或生命周期不能混成同一查询。

### B. forced-prefix scalar R 回放

每个 candidate实际行对应 `retained_history + [seed] + proposals[:row]` 的准确前缀。即使该proposal在首个拒绝点后偏离自由 greedy路径，也必须被强制送入 R 并读取完整向量。用自由 R 生成的单一路径代替这些 off-greedy 查询会漏掉最重要的路径。forced replay必须消费请求的全部prefix，即使其中有EOG token，也不能套用自由生成的提前停止规则；candidate可能已经一次验证了这些后续行。原生decode对此的合法性与实际mask必须明确验证。

无需对每个中间前缀都创建新context：将查询组成前缀树。每条 maximal root-to-leaf 路径从空的fresh R开始，按同一固定scalar recipe连续解码；沿途深拷贝分配给该路径的完整查询。证据中的fresh_context/start_empty表示这条轨迹的起点，而不是说每个中间query都重新创建context。固定 n_ctx、output reserve、分配策略，不得按leaf长度预配不同图/内存。绝不从candidate导入KV，也不在走错分支后trim回溯并称其fresh。fresh context也不证明process全局scope/JIT/allocator历史清洁；可用独立reference进程隔离candidate全局状态，在其内部固定模型加载、context初始化与运行顺序，或显式绑定并验证等价的process历史。每path新context不必每path重载权重，实际setup成本仍要计。能共享的是**同一纯净前向路径上的中间结果**，不是污染过的context或未经资格化的checkpoint。

本工具把每个required query确定性指派给一条覆盖它的fresh路径，所有queries必须恰好被指派一次。其他路径经过相同前缀时不必重复host readout，**scalar caller及logits mask仍不变**。若额外记录了重复观察，必须验证其执行元数据和完整bytes，不能用后一个覆盖前一个。单独预登记R repeat/stability sentinel，任何重复冲突失败。这只是有限样本的稳定性检查，不能证明整个R数学确定。

### C. 自由 scalar R 输出检验

另起 fresh R，让它按自己的greedy logits选择每个token，不接收candidate完整答案作为forced tape。保存真实caller/positions/masks、输出和原生EOG、cap/stop_reason；比较每一个自由行的完整向量与同前缀forced R，并比较endpoint。forced replay正确不能替代自由生成正确。synthetic stop-index只用于控制流诊断，不替代真实tokenizer EOG。

受控 forced-proposal rejection0/1/2、allaccept、initial/accepted/correction/bonus终止仍有用，但必须标为协议探针。不能将其acceptance、速度或通过率混入真实draft自由运行数据。

## 4. 每次 commit 的状态合同

逻辑状态包含：materialized tokens及positions、sequence ID、next position、active K/V 的原始位模式、已输出但未materialize的最后token（若有）、下一轮pending语义、终止类型、以及**保留前缀对应的正确frontier logits**。

独立重建规则：`materialized_output_count = next_position - prompt_length`，`unmaterialized_count = emitted_count - materialized_output_count`，必须是0或1；materialized prefix必须等于prompt加输出的前缀。不能只相信worker的可变history。

- initial/correction/bonus stop：通常最后已输出token还没入KV，不能因为没有下一轮就把它在完整状态中抹掉。
- accepted stop：最后输出已经materialize；raw local pending可能仍是旧seed，不能简单去掉 `done ? null : pending` 来修复。
- 原 `pending_after=null` 可继续表示“没有下一轮pending”。另设 `unmaterialized_output_token/position`、`materialized_output_count`、`terminal_kind` 和覆盖initial stop的final记录。
- trim只改retainedKV，不保证 `logits(-1)` 就是保留前缀的logits。应保存此次verification的 **row accepted**，不能总保存row3。initial用initial row。row accepted在发生accepted-stop时也可能与最后输出是否已入KV不同于pending直觉。

状态比较必须逐层、逐active位置、K/V头和分量提取原始dtype bits；不得通过float转换“规范化”后声称原始bit equality。metadata按明确定义的canonical顺序单独比较。只有证明两边serializer同格式、同layout和同覆盖范围后，raw serialized byte equality才可直接用；格式不同首先是UNPROVEN，不宜自动解释为数值失败。

#183使用的 `llama_state_seq_*` serializer保存所选active cells及positions等，不覆盖全部未使用padding、旧allocator或所有hidden backend state。对应source receipt中 `src/llama-kv-cache.cpp` SHA256为`5d53edebfae0722b8da464fb2407a8b8aa6e83d4e976da7e44a7c1733f96530f`。active KV精确相等不能被扩大成全部物理内存相等。另做历史污染探针：长→短复用、reject后不同续接、重置后同prompt、交错session、context边界、真实EOG。恢复/迁移/持久化resume单独资格化；新增journal字段不等于已经实现checkpoint。

## 5. 验证本身会干扰执行

heavy capture不计入生产速度，不能从heavy曲线推断收益。完整KV导出、额外同步、host拷贝、reference并行常驻和额外logit请求可能改变分配、图捕获、调度和数值路线。

- 生产candidate不增加target oracle调用；reference phase在candidate结束后单独运行。避免在12GB GPU上同时放候选两模型和第二套target weights/context。
- logits mask/output reserve保持生产原值。#151 VERIFY本来请求所有四行，可以读取它们；不能为验证而悄悄切换不同output reserve。
- 使用同一冻结binary的observer开关时，仍需检查heavy与minimal-observation运行的实际proposal tape、每目标行hash/能捕获的字节、dispatch/shape/placement，以及终止state摘要，而非只看endpoint。提取器若需要新内核或改变计算图，必须单独桥接并保留UNPROVEN状态。
- “minimum observation”也不是绝对无干扰。报告哪些原生结果在无额外观察下不可见；不能凭有限一致性证明所有生产执行必然相同。
- native adapter失败、中断、数据缺失、格式不兼容、metadata不完整都不得报PASS。保留STARTED及失败日志，不做静默修补/删除/重试。

## 6. 资源计数：上界情景不是实际测量，也不是强制保存策略

以下只是指定无EOG轨迹的算术，L=512、最终输出N=128、k=3。cycle数C为32（allaccept）或127（每次j0reject）。所有verify四行都计算，即使cap在其中终止。

- target向量使用数 `1 + 4C`：129 或509。
- 朴素reference成本 `sum(各查询prefix长度)`：74,304 或293,882 scalar token evaluations。
- maximal fresh paths：1条、640 token evaluations；或127条、73,533 token evaluations。不是wall-clock加速估计，未含模型/context初始化、自由R、重复R、提取、磁盘等成本。该N128情景的独立自由R还需639 token evaluations。
- 若每条路径都重复host捕获所有共同祖先，j0情景将产生8,636个R向量观察，而非509个。默认查询指派避免这种不必要重复；它不减少被承诺的每query比较，只省沿途重复readout。R仍从fresh root解码完整路径。

使用官方config结构做名义F16 active-KV估计：[Qwen3-8B](https://huggingface.co/Qwen/Qwen3-8B/raw/main/config.json) 为每token144KiB、vocab151936；[SmolLM2-1.7B](https://huggingface.co/HuggingFaceTB/SmolLM2-1.7B-Instruct/raw/main/config.json) 为192KiB、vocab49152。公式为 layers × KVheads × head_dim × 2(K/V) × 2bytes。实际使用的GGUF、运行时padding/分配/weights/workspace必须另行绑定和测量，不能拿config取代12GB admission。

成对candidate+一个规范R副本的全向量存储：Qwen149.53/590.02MiB，Smol48.38/190.88MiB（allaccept/j0）。若每commit把两个完整activeKV都重复写盘，会得到Qwen5.22/20.23GiB、Smol6.96/26.98GiB。这是**刻意朴素的重复保留方案**，不是GPU内存需求，也不是严格验证的必要磁盘占用。未计自由/重复R、metadata、失败证据和隐藏状态。

12GB admission必须单独计算并实测：target+draft权重、两份已分配KV容量（通常按n_ctx而非当前active长度）、compute/graph workspace、allocator保留、GPU capture staging以及系统占用与登记的安全余量。使用driver报告的实际可用字节，不把商品12GB标签当可分配上限。candidate采完后释放它的contexts/必要权重再跑R；验证并不要求额外一份target同时驻留。CPU offload、减context、改KV dtype如果改变部署必须另登记，不能OOM后静默降级。

### 不降低逐commit承诺的存储方案

每个commit仍读取、比较**全部active位置**，不能仅看新append，否则漏掉旧prefix被改坏。按固定layer/position范围分块，在线对C/R对应块做直接byte比较，再写content-addressed chunk store；每个checkpoint保存有序chunk引用、位置/类型/长度和根摘要。相同C/R及不同checkpoint的相同chunk只保留一份。失败保留两侧payload、首差异offset、dtype、周边块和完整attempt。

若所有旧committed chunks确实不变，append链KV可仅保存一条完整最终历史：本情景Qwen约90MiB，Smol约120MiB，加manifest；这是条件性理想dedup数，不是实际测量、不可变性假设或所有布局的硬上限。小chunk/固定边界减少重复，但要计metadata。重复读取和GPU→host带宽成本仍存在，不能用磁盘dedup数当采集成本。

证据分级应明确：

- **可重构完整字节包**：保存所有必要logits和canonicalKV chunk，独立审计者可重建每次snapshot并直接memcmp。hash用于寻址/完整性，不是数值数学证明。
- **完整在线比较、摘要保留包**：在线确实比较全部bytes，但之后只留hash、逐块比较receipt及失败witness。能审计流程与加密承诺，不能重新独立检查已丢弃的成功payload；复现需重跑完全绑定的部署。不能称与上一档相同的artifact可重构性。
- **只比较hash**：还额外依赖碰撞假设和提取器正确性；不得把hash相同写成浮点定理。未提取/未比较区域绝不能用hash语言遮盖。

先做小上下文/短cap（8/16）全字节pilot，覆盖所有控制分支与native自由轨迹，失败立即停止该合同的推广。通过后才考虑更长上下文与cap，仍逐required query/commit验证，扩大范围另列。业务样本单位为独立prompt/session/lifecycle，行数、logit个数、checks计数不是独立样本。相同prompt的重复用于稳定性而非虚增业务n。

## 7. 云端已经实现什么，什么还没有

`replay_audit.py` 是stdlib离线原型：重建transaction与terminal frontier、列出off-greedy全部query、规划fresh maximal paths、验证每个required row/state与执行字段、比较raw f32/KV、核查自由R与forcedR、拒绝缺失/额外/矛盾记录。reference及candidate caller tokens/positions/masks/row索引和物理切分必须吻合登记的v1 recipe。成功只叫 `RECORDED_EVIDENCE_MATCH`，永远返回 `gpu_qualification_established:false`。

该v1原型限定k3、单sequence0、连续positions、whole-prompt-last-only candidate prefill、target物理ub1或4、由trusted manifest绑定的固定每token长度opaque canonicalKV格式。格式字符串和bytes-per-token本身不证明dtype/layout；提取器和manifest要先独立资格化。它不实现chunk store、SWA/混合dtype复杂KV、用户设备、native/GPU采集器、数值模型、old-R桥接或生产admission。未知recipe/格式必须新版本明确支持，而非把任意JSON当生产身份。

附带测试的“KV”是人工token整数bytes，logits也是人工函数，不是神经网络。它们验证证据管道能抓到非argmax位差、offpath漏行、错误pending/row、缺失/污染R、mask/caller错误、state丢失、路径逃逸、forced伪装freeR等反例，不能证明神经计算正确。部署manifest的自报真假、提取器正确性、observer干扰及隐藏backend state仍属外部资格门槛。

值得继续的小步：实现只读native capture adapter和canonical extractor，先用云端CPU真实fixture验证其绑定与mutation rejection；GPU阶段须另有明确设备/预算授权。不要把审计器PASS、旧endpoint-only、#183CPU、未来GPU参考合同写成同一个PASS。

实现内存提示：原型会保留每个query的一份raw向量，并临时展开一行Python float tuple做finite/argmax检查；不再为每个row保留Python float对象。Python对象、JSON、临时KV双缓冲都增加host RAM，4-byte原始向量预算不是本Python审计器的完整RAM预算。大模型应使用流式原生提取/比较器和受控chunk缓存；先测host峰值再扩大。
