# HeteroSpec：参考语义保持的低开销并行执行路线

研究与实施草案，2026-11-04。本文不是已实现能力、GPU实验结果或接收概率预测。

## 1. 结论

主线收敛为：固定既有 reference R，寻找真正有收益的等价并行变换，以可缓存执行计划和有界写集事务组合到服务。先证明比强基线有用，再扩展自动选择或跨recipe缓存。测试数量、审计功能和四列分组本身不是论文创新。

原“2→1→3”建议修订为：①算子/计划先击败后端四列循环；②低开销组合与恢复；③存在多个互补有效路径后才做AUTO/跨recipe复用。不能承诺TPDS接收率超过50%；应逐项消除弱基线、样本冒充证明、开销漏算和系统收益不稳。

## 2. 固定证据

审查版本是PR178 `4bbd322de1411be9f7998def4042dafabb4df669`和PR179 `d694011de1065701b25840f30e25cc532c27f52d`。后续修复需重新核验，不能自动归于本版本。

- [PR178路线](https://github.com/leecdiang/HeteroSpec/blob/4bbd322de1411be9f7998def4042dafabb4df669/docs/research/reference_parallelism_roadmap_20261104/ROADMAP.md)
- [PR179实现说明](https://github.com/leecdiang/HeteroSpec/blob/d694011de1065701b25840f30e25cc532c27f52d/docs/research/reference_contract_20261104/IMPLEMENTATION.md)
- [PR171算子实验](https://github.com/leecdiang/HeteroSpec/blob/371223b696bb805030c29f04e39eb17b57fb2ebb/benchmarks/rtx_operator_frontier_v1/execution/RESULTS.md)：16个捕获描述符packed匹配标量，不是任意输入证明。q32 Q projection从23到2 kernels、172.4到150.2μs，但V从67.1到67.5μs。自然输入完整路径3.3562到3.2219秒，约4%节时，packed WB 3.1985秒仍略快。主要改善prefill，k3 verify四行不走此packing。
- PR174校准2038.78秒、AUTO固定WB-cut；PR175主区间跨1、微小均值收益需约104.7万次命中回本；PR177条件池8个未见root complete比0.994379且跨session翻转。不能再拿弱WB、挑选root或均值微差推广总体。
- PR179是审计恢复基础设施。CUDA staged代码未编译/运行，enforce拒绝CUDA split；CPU/mock测试不构成GPU资格。

## 3. 最强近邻与主张边界

以下一手链接已于2026-11-04打开核验。论文以arXiv预印本描述，未据此宣称任何会议接收。

### amiller/llama_reproducible

[项目](https://github.com/amiller/llama_reproducible)；[固定补丁](https://github.com/amiller/llama_reproducible/blob/f0dafdbd9dba40bd0e596f74f3da5f592900fca4/patches/0001-all-deterministic-parity.patch#L2966-L2995)。CUDA switch在ncols>4时按四列循环分发，量化位于循环外。这可能消除graph tile+concat的重复量化及concat。必须把该机制移植到同一冻结HeteroSpec runtime再比较；不能直接将其修改超越函数/CPU语义的整个runtime当作同一R。四列保序及CPU复制GPU归约已有先例，不应声称首次提出。独立CTA可能重复读取权重，第三维广播不证明只读取一次。

### Taming Bitwise Behavior

[Yang等，arXiv:2609.11356](https://arxiv.org/abs/2609.11356)。该工作覆盖GEMM归约描述、受约束编译和位等价检查。它直接限制“保序并行/等价类调优”的广义新颖性。我们的差异只能落在真实旧R兼容、量化runtime集成、历史状态安全及净系统收益，而不是复述归约签名。未实现静态证明不能声称同等级保证。

### Vosti

[Qin等，arXiv:2609.38981](https://arxiv.org/abs/2609.38981)。固定配置确定性覆盖批处理与前缀KV等变化，分层处理引擎与kernel保证，与“kernel契约+状态归纳”强重叠。潜在区别是保持既有部署R的位级轨迹，而不只是建立新的确定性实现。必须证明此需求真实有价值；不能把较窄保证包装成更强验证。

以上摘要性比较不是artifact复现。后续登记其版本、模型/硬件/精度支持及可运行条件，区分机制比较与跨系统吞吐，不制造不公平排行榜。

## 4. 真实KV生命周期

原生源码来自[PR174 source kit](https://github.com/leecdiang/HeteroSpec/blob/aa7ff4e64752be3de0d7974febbce453ae3a96c0/benchmarks/rtx_prefix_reuse_v1/execution/evidence/native-source-kit.zip)，SHA256 `b1926827029e0bb8e219861901f2ca3538b330a44f9c6093b5267157dbfcd1ac`。以下行号是解压后candidate，不是最新上游。

| 阶段 | 源码 | 结论 |
|---|---|---|
| decode预处理 | llama-context.cpp约1750 | init_batch之前memory_update(false)；prepare失败可能memory_update(true)。事务要在此前拦截shift/copy，不能只包graph_compute。 |
| placement | llama-kv-cache.cpp:748–826 prepare | 保存heads和目标cell元数据，暂apply各ubatch再逆序恢复。是shadow规划先例，不是KV字节快照。 |
| apply | llama-context.cpp:1336；kv-cache.cpp:2729 | mctx->apply早于build/alloc_graph，cells/head/n_kv已修改。图分配失败不等于零状态变化。 |
| overwrite | kv-cache.cpp:1098–1190 | occupied slot触发rm，还可能purge更早位置。只备份目标槽不能覆盖副作用。 |
| KV真实写 | kv-cache.cpp:1332–1420 cpy_k/cpy_v | SET_ROWS；非转置V按row，转置V是标量索引scatter且可能pad。写集要按实际地址/dtype block边界推导。 |
| async | process_ubatch graph_compute | 返回不能等同device完成。abort/输入复用/rollback均需事件依赖或同步。 |
| 原失败清理 | decode约1810后 | seq_rm仅移除失败ubatch，早期成功ubatch、输出及sampler不是整个逻辑batch原子回滚。 |
| full snapshot | context.cpp:2591；kv-cache.cpp:2067,2250 | host writer析构逐tensor_get；扫描cells/层并搬运真实KV，不是O(1)校验。 |

ON_DEVICE sequence state可作中间开销基线，但同seq再次get使旧快照失效，且依赖原context mem_storage，不能直接fresh-context恢复。需要owner/lifetime设计。

## 5. Reference与可执行谓词

R至少固定模型/tokenizer哈希、source/binary/编译选项、math mode、device/driver范围、kernel路线、KV精度/布局、positions和sampler约束。“同R逐位相同”与“不同R质量接近”分开。

PR179 collect关闭fusion/capture，记录的是改变后策略。只能选择：①观察不改变原策略，并验证观察对照；②明确把collect配置命名为另一个R。不能给原部署签发collect轨迹资格。

资格检查必须返回typed reason，未知一律拒绝，而非检查描述字符串非空：
- ID和版本匹配：model/binary/device/policy/qualification。
- shape/type/stride/align/contiguous/tail位于已支持域，尺寸计算无溢出。
- alias/view解析到buffer+byte范围；kernel具体template、K分工、accumulator dtype、FMA/cast/rounding/reduction树满足reference关系。这需要可信证明或明确经验等级，不是标签。
- SET_ROWS索引在预留写集，无重复冲突、block/向量写越界；转置V独立规则。
- committed KV读集与允许写集不相交；没有未支持shift、copy、SWA覆盖、defrag、shared-owner mutation、recurrent memory、adapter修改。
- weights只读，scratch/output生命周期覆盖async完成，position/sequence/mask符合契约；未知split/fusion/capture节点拒绝。

首版限定单context独占、单sequence、dense transformer、append-only、新空槽、无pending update、无backend sampler/embedding/辅助输出、明确KV dtype/layout。每次扩域新增谓词和测试，不靠放开总开关。

## 6. 三层计划及图复用

1. KernelQualification：冷路径的静态语义证据、代码身份与域；finite replay只能标empirical，不得升格proved。
2. PlanTemplate：图拓扑、实际backend split/kernel族、alias约束与动态范围。scheduler alloc完成后、第一次launch前核准所有split。若后端到launch才选kernel，须先重构route选择为纯计划阶段，不能声称已有prelaunch保证。
3. PlanBinding：本次slot/position/n_kv、buffer generation、地址、events和写集，每次检查动态条件。开销可能随新增tokens/节点增长，不承诺O(1)。

不能把物理地址和n_kv全写死后称每步可复用。graph reuse/capture复用已核准template，但动态binding必须更新。检查到后续split失败时，前面split不能已修改KV。

失效事件包含model/LoRA/control vector、buffer relocation、dtype/stride、n_kv引起kernel门槛、device/compiler、fusion/capture、KV移动/seq操作、allocator generation、并发模式、资格撤销。裸指针重用不是身份，使用generation。检查和launch之间需独占或等价同步防TOCTOU。

热路径不做scalar rerun、全logits导出、完整KV重新hash或fresh-context重建。必要结果输出仍计成本。全字节审计移到冷路径的前提是已有适用证明，不能单纯删检查后继续宣称安全。

## 7. 有界写集事务

状态机：Idle→Reserved→Planned→Submitted→Completed→Committed；失败明确进入Rejected/Aborted/Poisoned。

事务单位是完整逻辑batch，覆盖全部ubatch。首版若仅支持单ubatch，predicate显式拒绝多ubatch。外部只在commit后看到新logits、cache和sampling结果。

- Reserved：独占context，检查pending updates；在shadow cells预留全部新槽；记录旧heads/cells/output metadata/generation。禁止原生自动优化重试。
- Planned：用shadow memory view构图，解析真实读写和路线。过渡实现可在独占context内暂改metadata并完整记日志，但必须保证不可被observer看到，并拒绝occupied slots以避免未覆盖purge。
- Submitted：只写未发布新槽，旧KV不可变，输出进入transaction-owned buffer，记录completion事件。
- Completed：所有设备写完成且检查错误，才可commit metadata、输出并推进generation。
- Aborted：等待或隔离in-flight工作，再丢弃新metadata与输出。新槽脏字节可不还原的前提是它们不会被未来任何计算读取。
- Poisoned：非法地址、设备故障、未知写集或无法确认完成，隔离context。不在可能损坏的context上scalar重试；从事前可信checkpoint或token replay重建并计恢复成本。

### 容易遗漏的padding责任

attention可能触达padding；mask不自动证明NaN/Inf不会进入中间运算。须证明masked load和有效n_kv排除脏槽，或恢复/清零必要区域，并验证清零不改变R。状态观察量明确为committed KV+metadata；若契约要求整个allocation字节一致，就必须恢复，不能事后改定义通过测试。

### 回退分界

- launch前：零committed变更，返回原R，只计规划/拒绝开销。
- launch后但合法新槽写：同步完成后弃tentative状态，再从旧state运行R；测失败率和p95。
- 可能写旧KV/不可证明写集：完整checkpoint慢路径或禁优化；seq_rm不构成等价恢复。
- 致命设备错误：可能无法导出，不能失败后才抓快照；必须预存可信状态或可重放token历史。

## 8. 证明责任与缺口

| 责任 | 必须建立 | 当前可做/缺口 |
|---|---|---|
| P1算术 | 量化/归约/FMA/cast与R等价 | replay有限；需要结构证明、静态检查与binary绑定 |
| P2映射 | packed不串列、越界，tail正确 | CPU index性质测试；实际GPU待测 |
| P3组合 | 所有node读同一逻辑输入且split完整 | plan DAG/alias检查，未知拒绝 |
| P4历史 | committed bytes/prefix不变 | append写集证明，shift/overwrite拒绝 |
| P5回滚 | abort对外等价于未执行 | metadata、outputs、sampler和async都覆盖 |
| P6缓存 | 命中是合法producer状态 | identity/integrity分离、COW及owner/version |
| P7时效 | 检查至commit不失效 | generation/独占/events和race测试 |
| P8实际执行 | 二进制执行核准路线 | dispatch绑定；collect改变策略尚不能签发 |
| P9信任边界 | compiler/device/checker假设明确 | 不能称端到端形式验证 |

logits相同不自动证明全部KV相同，KV相同不证明sampler状态相同。每项结论精确到观察量与适用域。

## 9. Cache修复

审查版本ExactRecipeCache.get要求expected完整KV+logits，适合审计/去重而不是未计算prefix lookup。后续即使修复，保留回归测试。

接口拆分：lookup(known_identity)、admit(identity,payload,evidence)、validate_integrity(entry)、materialize(entry,destination)。已知identity包括reference/model、token prefix/positions、recipe资格、parent lineage、格式和owner；integrity校验存储损坏，不要求caller先计算目标KV。materialize检查layout、precision、residency、ownership并COW。先strict recipe，跨recipe须具体producer-equivalence关系。未知资格是miss，不把全模型比较藏进“cache hit”。

## 10. 实施任务与可验证边界

A. execution_contract：typed predicate、拒绝码、证据等级和版本/域。CPU可验证fail-closed组合。
B. plan_template/binding：纯route选择、完整split、失效、graph reuse绑定。CPU/mock可测逻辑，不能证明GPU覆盖。
C. kv_write_plan：shadow prepare、K与两种V byte writes、overflow/alias/duplicate检查；禁shift/SWA/copy。随机小域穷举/property测试。
D. append_transaction：独占、日志、输出暂存、completion/commit/abort/poison，逐阶段故障注入。多ubatch先拒绝再扩展。
E. 强基线：同runtime backend4 loop，量化次数与concat实测；保持其他policy相同。
F. profile后选一项主优化：共享weight load、quantize复用、materialization消除或plan replay。不要同时叠加无法归因的变换。
G. 服务：WB-rechunk与QB共同获得最佳合法低层优化，完整成本和负结果都保留。

无GPU能交付CPU单元/property测试、mock events、failure injection、tiny native CPU集成、测量脚本与NOT_RUN manifest。不能交付CUDA资格、GPU性能或B570泛化结论。

## 11. 分阶段实验与止损

E0：冻结source/binary/model、硬件/驱动、policy、功耗/时钟条件与数据划分。正确性和计时分离，cold/hot明确，逐root逐session留原始结果。

E1最先做：scalar、graph4+concat、backend4-loop、packed、各自合法graph reuse，同一operands及自然分布。覆盖Q/K/V/out、q=1/3/4/5/8/16/32和tail、两模型、边界stride。测wall、GPU events、launch/quantize/concat、DRAM/L2、occupancy；profile另跑避免污染计时。packed若不能胜backend4-loop，停止把packing当主贡献。

E2开销：无guard、每次full plan、cached template+binding、full-state owner、合法写集transaction；扫描历史长和新增tokens。快照随历史KV增长，写集预期随新增KV增长，但metadata、padding、events及恢复都计入。回本N=cold_cost/每次净节省；净节省≤0不存在回本点。

E3破坏安全边界：reserve/build/alloc/每个split/SET_ROWS/async/commit前后故障；污染padding、buffer relocation、n_kv门槛、过期资格、重复索引、SWA覆盖、同指针新generation、多ubatch第二个失败。核对旧KV/metadata/output/sampler及后续R轨迹。未解释差异即撤销该域，不用容差掩盖。

E4完整服务：强WB-rechunk、fixedQB、候选AUTO平等优化。分开prefill/verify/append/recovery/qualification及端到端/p95。预定义总体roots，条件池单列诊断。多独立session，最好跨日期/设备；配对root/session区间，不把同root重复当独立样本。

功耗若可测，说明GPU/整机边界、采样率和idle处理，报告J/request和J/token；GPU功耗不能称整机节能。RTX/B570分别固定R，不据此声称跨设备逐位相同。

止损门槛要预注册，可选实际最小收益δ（端到端5%仅作候选预算，并非论文通用标准）。需要区间、绝对延迟和cold/failure债务共同支持。若强WB抹平收益，转窄域机制或补技术，不用AUTO故事包装。

## 12. TPDS主张矩阵及反方

| 拟主张 | 必需证据 | 当前结论 |
|---|---|---|
| 保持旧R | 固定R与真实迁移/复验需求、完整观察量 | 目标可定义，未全面实现 |
| 比四列loop快 | 同runtime强基线和因果profile | 未验证 |
| 历史状态安全 | P1–P9适用证明、GPU与故障实测 | #179仅基础设施 |
| 热路径足够便宜 | cold/hot/failure完整成本 | 未验证 |
| AUTO必要 | 多互补有效路径与跨session收益 | 现有实验不支持 |
| 跨硬件 | 两设备各自有效域与结果 | 不由RTX捕获推广 |
| 可复现 | 固定环境、脚本、负结果与NOT_RUN | 可建设，不代替新颖性 |

反方问“为何不选择新而快的确定性语义”：需真实旧R兼容价值，否则研究动机减弱。问“grouped GEMM加checkpoint有什么新”：四列与事务本身不新，需非平凡变换/低成本组合及净收益。问“Vosti/Taming已做”：明确较窄旧R量化部署问题，诚实比较保证。问“算子快4%，检查更慢”：完整成本净负即撤性能主张。问“只在样本相同”：经验资格不等于结构证明。问“人为关闭优化制造优势”：基线也得获得相同graph reuse/policy。

投稿前最低可信组合：一个超越强近邻的机制、明确有限保证、强基线下稳定净收益、可核验artifact。缺少这些时延后TPDS/改变定位，比主观50%承诺更务实。

## 13. 相对此前方案的变化

保留reference-first和先机制后调度。新增后端4列强基线；collect不得签发原策略；full-state迁出热路径；事务覆盖实际SET_ROWS、padding、async和outputs；cache从expected-state比较拆为已知身份lookup。“计划+写集”明确是待实现，不包装成PR179已完成。每项都设失败测试与退出条件。
