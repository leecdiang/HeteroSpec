# 下一阶段 RTX draft ubatch 研究：受限执行协议草案

**当前状态：NOT_READY_FOR_GPU。** 本文是未来设备实验的执行合同和分阶段计划，不是可直接运行的GPU runner；本次只读源码、CPU bridge结果与既有记录，没有使用用户设备、创建GPU任务、运行新模型或写PR。不要因九点验收时间而跳过门槛。

## 1. 当前真正具备的能力

已审读 #183 固定head `282e730f9befd59d07c53d2d8d419fdccfdbdbb8` 的[README](https://github.com/leecdiang/HeteroSpec/blob/282e730f9befd59d07c53d2d8d419fdccfdbdbb8/experiments/draft_ubatch_probe/README.md)、[stage.py](https://github.com/leecdiang/HeteroSpec/blob/282e730f9befd59d07c53d2d8d419fdccfdbdbb8/experiments/draft_ubatch_probe/stage.py)、[离线设计](https://github.com/leecdiang/HeteroSpec/blob/282e730f9befd59d07c53d2d8d419fdccfdbdbb8/experiments/draft_ubatch_probe/target_reference_replay/DESIGN.md)。stage.py只生成draft物理ubatch1/2/4派生source，保持draft output reserve1、target请求算法不变；Windows派生worker仍NOT_COMPILED。

本地真实native bridge位于 ` /workspace/scratch/14b58e5a88ca/heterospec-native-replay `，审读src/bridge.cpp、run_bridge.py、run_matrix.py、parse_state.py及evidence/SUMMARY.json。16case×3独立进程已完成，112 target vectors与40 active-target-state snapshots匹配；这是实测CPU native证据，不再只是人工bytes。但范围严格为：

- 两个未训练tiny synthetic模型，target与draft同模型、词表NONE/128 IDs、无自然tokenizer/EOG；7-token prompt、cap≤9。
- candidate target ubatch1/output reserve4；reference也output reserve4；不是旧R的output reserve1，不是QB target ubatch4。
- whole-prompt单caller/last-only，然后scalar；fresh进程、每条maximal reference path新context，无resident-reset复现。
- 请求n_ctx128被runtime实际取整至256，说明必须记录实际值。
- parser仅支持两层、256维、F16、seq0、连续positions，2048bytes/token。不是Qwen/Smol parser，也不涵盖inactive padding、完整draft state或hidden backend state。
- 16case不是model×branch×ubatch全交叉。native-draft自由proposal仅在ub4测试，其他宽度与控制分支有意混排；不能当ub1/2/4公平对照，更不能外推性能。
- 0.839秒进程总墙钟、1.65MB原始payload等只描述tiny CPU单轮instrumented工作，不提供GPU时长估计。

Bridge正在独立准备发布，其最新远端head由执行前重新核验；本文的本地源码pin另见SOURCE_SCOPE.json。历史失败/证据保留修复必须保留，不覆盖旧attempt。

## 2. 为什么不能直接套现有GPU命令

[冻结worker](https://github.com/leecdiang/HeteroSpec/blob/29511ed91eb9f3d9773cfdda53e3554b0f4ad08b/scripts/experiments/rtx_scope_transfer_v1/worker.cpp#L184-L280) 锁cap128、n_ctx1024、Qwen/Smol resident生命周期、旧study/slot身份；无论target-only与否都加载draft权重，并预置R/GS/PQ/QB四个context pool。其资源admission不等于本小实验的单arm资源admission。

旧[host.py](https://github.com/leecdiang/HeteroSpec/blob/29511ed91eb9f3d9773cfdda53e3554b0f4ad08b/scripts/experiments/rtx_scope_transfer_v1/host.py)、[prepare_host.py](https://github.com/leecdiang/HeteroSpec/blob/29511ed91eb9f3d9773cfdda53e3554b0f4ad08b/scripts/experiments/rtx_scope_transfer_v1/prepare_host.py)和[qualify.py](https://github.com/leecdiang/HeteroSpec/blob/29511ed91eb9f3d9773cfdda53e3554b0f4ad08b/scripts/experiments/rtx_scope_transfer_v1/qualify.py)绑定旧计划、日期、预算及98请求qualification单元。qualify.py主要比较PQ/QB相同路径与向量，不提供新proposal相对旧R的每prefix全向量/每commit activeKV资格。

不能改个--draft-ubatch或换JSON就运行本协议，不能把旧NUMERICALLY_QUALIFIED字符串当新合同通过。需要独立的新study ID、可审阅新host adapter及GPU capture/replay adapter，不改旧实验或把旧receipt装作新配置。短cap也需要显式派生并新绑定，不可静默绕过cap128检查。

缺失项（任一未完成即BLOCKED）：
1. 真正的Windows/GPU派生可执行文件与完整静态source/module/compiler/runtime绑定及测试；实际loaded-module/dispatch和峰值必须由G1-R原生阶段验证，不伪装成G0只读所得。
2. 实际Qwen/Smol tokenizer、EOG、模型pair和GPU sequence-state canonical extractor，未知dtype/layout拒绝。
3. 复现指定旧R的caller、output reserve、scope、prior-history/reset生命周期的reference adapter；新fresh R仅可作单独参考族。
4. target-only baseline的真实独立执行/捕获schema，不能把无draft记录伪装成k3 speculative trace。
5. 实际物理microbatch/dispatch观测。capacity4或ceil(tokens/4)不是GPU确实采用对应数值路线的证据。
6. bounded host controller：per-attempt fresh目录、预算、超时、逐request停机、owned-process清理、失败receipt不覆盖；原始数据不得自动上传。
7. 下节所有真实设备路径、身份、预算和baseline cache合同已填写并审核。

## 3. G0：零新GPU请求的冻结与只读预检

G0只准备身份、能力和预算，不执行数值bridge。旧R native identity/observer数值bridge与峰值resource admission另命名G1-R（即G0静态后的native阶段），必须有独立冻结的cap128旧binary及adapter请求/token/时间/证据预算；当前该预算未核定，故G1-R和后续阶段均不可启动。不能用“G0通过”表示旧R数值资格已通过。

先核最新PR head并保存changed files；用户设备未连接或未授权使用就停，不创建设备任务。输出本地检查报告即可。

冻结两个不同概念：
- **R_old具体部署**：归档source/exe/numerical DLL、模型+tokenizer、device/driver/CUDA/JIT、n_ctx/n_batch/physical ubatch1/output reserve1、prompt caller及mask、seq/positions、greedy tie-break/EOG、scope、初始化/reset及确定的prior-request历史。
- **参考生命周期**：R_old_resident_reset与R_fresh分别命名。旧Qwen/Smol先复用context、memory_clear(false)，不等于新建context。若旧完整producer无法重建，只能报告R_old_UNPROVEN；不能让新CPU bridge或旧endpoint记录替它背书。

短cap参考另命名 `R_adapter(old-numerical-identity, prefix-replay)`。旧binary只收cap128，绝不声称直接把它改参数跑cap8。短prefix adapter的source、进程/池布局和输出reserve须单独冻结，并先与未改旧R的对应前缀生产/可观察边界建立桥接；必要的完整cap128旧R执行单列预算，不能按8-token计费。若全state提取会改变旧生产路线且未证明observer桥接，维持R_OLD_UNPROVEN，不用旧endpoint-only记录补这个缺口。

新reference逐maximal路径要复现登记的R_old起点历史：例如先完成固定priming请求、reset(false)，再whole-prompt last-only及scalar延伸。可以在不同路径前重新构造该起点，不能把污染路径trim后宣称fresh。若想用新context省历史，必须先对本登记scope证明两族的全vector/activeKV边界桥接，仍不宣称全输入等价。

绑定内容：所有source和数值模块/模型/编译器/JIT摘要，实际loaded modules、GPU UUID、driver、KV dtype/layout、实际n_ctx/n_batch、target/draft输出reserve、caller IDs/positions/masks/实际dispatch、生命周期与priming序列。摘要只作身份/完整性，不替代数值或提取器证明。CPU bridge曾观察context取整，实际值必须与冻结允许值一致。

### 真实路径与输出合同

当前没有核验任何RTX设备的可写输出路径，**不编造C:/D:路径，不宣称本稿命令可执行**。未来执行者须从已连接设备的真实仓库和本地模型manifest只读解析绝对路径，写入LOCAL_PATHS.json：repo、old_R_exe、candidate_exes[1,2,4]、target_only_exes、target/draft模型、numerical_modules、已存在且获准的output_parent。核实存在/sha/权限后，为这次新study创建 `output_parent/rtx_draft_ubatch_<UTC>_<unique_id>/`，不得复用已有目录。

第一条设备报告必须给出**解析后的完整绝对run_root**，不是占位符。每个attempt保存完整command argv、配置、STARTED/COMPLETED/FAILED、PID与cleanup、原始captures、budget ledger和最终scope结果。原始prompt/token/派生摘要只留获准的设备输出目录；不得自动提交PR、同步云端或传给第三方。可公开的新fixture仅用人工/公开材料。

当前本稿的真实交付目录是 `/tmp/rtx-draft-ubatch-protocol-20261104/`，不是GPU输出目录。

## 4. 先定义强baseline，再看速度

五个arm足够，暂不加入overlap、persistent双KV、prefill重排、跳过EOG预填充、adaptive draft或新target算法：

- B_default：实际默认/常用的**target-only**实现，使用其合理最快配置；只加载target并拥有同等prefix-cache资格与资源预算。
- B_QB：target-only、与C相同的QB target配置。隔离draft的额外收益，不代替B_default。
- C1/C2/C4：普通draft物理ubatch1/2/4；draft output reserve均1，target QB与其余算法完全固定。

R_old是数值参考，不必是最快baseline。B_default/B_QB都要先接受同一个target-strict资格；default若不满足，明确列为不同合同的实际默认参照，不混入strict speedup。仍保留其速度，不能通过删除它营造部署优势。最快的合格target-only baseline按预登记pilot规则选择，并同时报告两者。

不要让target-only常驻无用draft或全部GS/PQ池，以免人为拖慢baseline；如果拿掉这些资源改变数值路线，就对真正target-only配置重新资格化，而不是强迫它承担speculation成本。

### cold/warm定义与小规模限制

主比较只选一个预登记cell，且其适用性必须与目标工作负载一致：**权重/进程warm，target与draft KV均empty，经登记的resident-reset历史**。这不是warm-prefix cache命中。weights_loaded、JIT cache、graph cache、context lifecycle/history、target/draft prefix-cache hit分别登记；H=0的首请求不能自动称steady-state graph-warm，必要时只标weights-resident/first-graph-use的受限cell。所有arm用相同前置系统warmup政策和请求边界，但target-only不付draft初始化。

另外两个cell分阶段考虑，不能全因子展开：
- process/model cold：完整进程启动、权重加载、context/graph准备、prefill、decode、teardown计入service/first-use latency。单独报告，不和warm service混平均。
- prefix warm：只有真实cache实现及state资格已具备时才允许。B_default/B_QB获得同样的target prefix reuse机会；C获得其target+draft两份缓存。cache构建/恢复/查找/容量和摊销次数均计费。target-only无需虚构第二份draft cache。

T-warm/D-cold只作为明确命名的非对称场景，与同T-warm target-only比较，不与T-cold baseline比。尚无candidate cache实现就将其prefix-warm标NOT_IMPLEMENTED，不用host成本相减模拟成实测。若默认target-only已经有prefix cache且目标工作负载实际会命中，必须让它正常使用cache，candidate没有实现就承担自己的真实miss/prefill成本；不能关闭baseline cache来替candidate制造优势。若本次只研究empty-KV cell，就明确不能据此宣称默认重复prefix部署胜出。当前不会要求一口气跑cold×warm×两模型×所有arm。

## 5. G1：先target-strict数值资格，非统计“近似不劣”

数值门槛是 **零完整字节差异、零丢失状态/位置/语义差异、零未解释失败**。没有epsilon、argmax-only、允许1%错误或p-value放行。性能non-inferiority是之后的独立问题。

先选定一个family，且在看新timing前冻结选择理由。历史Qwen净收益使它成为合理候选，Smol较高draft成本只说明需要更大改善，并不自动更值得扩大。实际资源/最强baseline未核定前，此选择保持UNBOUND，不自动跑两family。

最小G1建议：两个公开/人工文本输入，实际tokenizer长度约32、128，cap8；已完成旧R桥接的R_adapter各两次，B_default/B_QB/C1/C2/C4各一次，共14个自由生成请求。这14个请求不包括必要的旧binary cap128桥接运行；在G1前另登记其次数/时间/token预算，不能暗中添加。若该桥接未建，G1不得执行old-R-strict流程；若另做新参考族诊断，必须另命名、另定预算并获得明确授权，不能成为绕过G1-R的自动降级路线。另最多8个明确标注ORACLE_CONTROLLED_PROTOCOL_PROBE的initial/rejection0/1/2/allaccept/accepted-stop/bonus/stop诊断。它们不进入acceptance或性能统计。prior-history采用方案A：每个candidate、heavy/light run、reference maximal path、autonomous free R及stability run之前，都从同一冻结构造步骤重建H history，再reset；不在只prime一次后连续运行却声称起点相同。H包含0或1个完整登记请求，token/cap/caller/池布局固定；若重现旧binary的priming，它也必须按旧cap128执行，不能暗中用cap8代替。H若需要超过1个请求，本微型协议不覆盖，须另订预算。priming次数由实际setup数×H请求数导出，每次均计请求、tokens、时间、数据和资源，绝不免费。

每个C真实proposal tape都独立检查，draft bytes不要求等于C1：
1. initial及每次verify所有四行完整f32，包括首次拒绝后off-greedy行，与精确匹配prefix、prompt边界、caller/mask/lifecycle的scalar R比较。
2. 每commit完整active target K/V、positions、next_position、输出但未materialize尾token、next-loop pending与正确frontier logits。保留verification row accepted，不误用trim后的logits(-1)。包含initial stop。
3. forced replay消费整条所需prefix，即使含EOG；自由R是另一个进程，只接prompt/cap/EOG合同，不接candidate endpoint/tape。
4. 自由R endpoint及每行full vector另比。B_default/B_QB用真正ordinary target-only事件schema资格，不能借C schema假通过。
5. long→short/reset、丢弃tail后续接、至少一个真实tokenizer EOG边界、实际shape边界列覆盖状态。找不到自然EOG样本则标NOT_COVERED并限制cap-only范围，不能把synthetic stop叫EOG已验证。

每个参考路径只给required queries一个capture owner；所有路径仍从登记纯净起点执行。额外重复R观察全比较，冲突即停。所有提取均先同步并深拷贝，再允许suffix/下一轮覆盖缓冲。

G1建议硬上限：22自由/控制请求；256 reference jobs（包括离线forced paths及控制proposal调用的每一个内部oracle context，不能藏在8个probe请求内）；22 autonomous free-R runs与4 stability runs。最多304个重建起点，故H=1时priming上界304次（H=0则0），真实计划按每个case/path精确推导后冻结。另限制75,000 reference token evaluations（包括reference的H）；30分钟owned GPU进程墙钟；8GiB新增保留证据。达到任一上限就停并标INCOMPLETE，不把未跑部分算通过。具体时间预算只是待审批硬上限，不是完成时间预测。

## 6. G2：10个timed请求的微型成本筛选，先决定是否值得继续

仅G1零差异且所有必需coverage可解释后。先固定一个约128-token公开文本、cap16、5arms、2独立session，共10timed请求。先对这5个arm各做一次heavy full-state资格，覆盖新cap16；通过后才允许运行对应的provisional light计时。observer bridge依赖这次light本身：其tape/vector摘要/dispatch桥接完成后才可将该结果纳入性能claim，否则记OBSERVER_BRIDGE_UNPROVEN，保留但不报生产收益。这次provisional light已算在10个timed预算内，没有免费calibration。新prompt/cap/shape不能继承G1范围。每个light的actual tape/完整vector摘要/dispatch必须仍在该heavy覆盖下；若变化，先停止该计时claim，新增heavy资格也必须在原预算内，不能事后修补后忽略第一次变化。

每个run/path按上节独立重建H，不能把两session的priming混成一次。固定随机seed、平衡/交错arm顺序，禁止同一GPU并发与温度/后台负载失控下挑好结果。这里仅一个prompt，结果只用于淘汰明显无价值方向和提出下一阶段，不作泛化/统计结论。
Heavy资格与性能必须分开：
- heavy导出全部state，不作为生产latency。
- timed route保留必要实际proposal/decision/caller及已有host-visible完整向量摘要，所有额外logging/hash成本计入被测service。不可把oracle、state export或host拷贝偷偷移出timer再宣称生产加速。
- 同arm的heavy companion用相同登记起点、prompt、native draft，自由生成；比较actual tape、完整target-vector摘要及dispatch。若不同，observer bridge失败/范围未建，provisional latency保留但不纳入资格化性能结论，不让forced修补掩盖。
- light run没有逐commit完整KV导出，就不能说其每个未观察KV字节已被直接验证。finite heavy qualification、observer bridge与light timing是三种证据分别报告。无法建立可信observer bridge则只报告instrumented结果，不宣称无观察生产路径已target-strict。

唯一primary是同合同、同cache资格下完整warm service latency；TTFT为secondary/guardrail。计时必须实测：t0为登记的请求进入服务边界，t_first为首个token实际可见/发送完成，t_last为末token实际可见/发送完成，t_done为cleanup完成；分别报TTFT=t_first−t0、用户完成latency=t_last−t0、完整service=t_done−t0。GPU依赖在对应边界按协议同步，不把launch返回当完成。旧worker的service_seconds包含reset/context准备及teardown，request_seconds在reset之后开始，二者均不含更早的模型加载/pool provisioning；不能直接将任一个叫cold end-to-end或真实TTFT。旧worker在target prefill之后还会先做draft prefill才sample initial，必须保持当前策略并实测首输出，不能拿target prefill时间当TTFT。另记录模型setup/cold end-to-end、target/draft prefill、draft sync/propose、verification、acceptance/每cycle输出、实际call/dispatch、peak GPU/host RAM。默认target-only不付draft/pool费用。各arm的实际proposal/路径可能不同，所以变化是完整系统效果；旧host减法或“只改ub所以仅prefill改变”不能当因果分解。

pilot只作单prompt筛选，不把重复当独立样本：至少一个C2/C4须同时达到相对最快合格target-only的实用point改善门槛（建议≥3%）、相对C1无实质倒退，且TTFT不触发预登记退步guardrail（建议配对point回退不超过5%），才有理由提议确认阶段；否则NO_PRACTICAL_GAIN并停止扩大。仅胜C1却仍输最强target-only只能作为诊断发现，不自动推进；若收益仅在被削弱baseline、未计初始化/缓存构建或oracle免费时存在，也停止。几乎全部时间已不在draft prefill时，不再为极小可争取收益新建复杂cache/overlap实验。

G2建议上限：10timed+5heavy；128 forced-reference jobs；5 autonomous free-R与2 stability runs，共最多150个重建起点，H=1时最多150priming（具体按冻结计划导出）。限制75,000 reference token evaluations（含H）；30分钟owned GPU墙钟；8GiB新增证据。预算包括companion/replay/失败，不只成功timed结果。任一达到则INCOMPLETE。不要为通过而扩大cap/样本或切模型。

## 7. G3：只有明确机会时才申请小型确认阶段

这不是当前自动后续任务。只有G2值得继续、old-R范围和observer bridge都可接受，才冻结一个胜出C2或C4，以及B_default和B_QB，共最多3arms；只有两baseline配置/生命周期/缓存身份确实相同才可合并，不能仅凭pilot计时接近合并。12个**新**公开/人工prompt、cap32、2sessions，72timed请求，先完成最多36个arm×prompt heavy full-state资格；任何新cap32、input/shape须先heavy再provisional light，light桥接通过后才计入结果，其费用已在72timed预算内。第二session的实际轨迹若超出对应heavy覆盖就停止该claim。不再同时扫两模型或所有cache状态。cap128/长prompt/general-EOG或新family另列未验证范围。

G2在单prompt观察到的相对C1优化不被扩大为G3已确认结论。若研究问题还要求G3对C1的独立确认，须另核定第4arm预算，不能静默添加。保留两种baseline避免pilot选出的赢家在新panel上不再最快却仍被称“最强”；不使用逐prompt择最快的oracle baseline。

性能non-inferiority示例预登记为δ=3%：对每prompt先汇总session内primary warm-service配对log latency ratio，再按prompt聚类计算一侧95%上界，分别要求对B_default与B_QB的upper(C/B)≤1.03；实际采用还要求两者point ratio均≤0.97。若某default配置不能满足strict合同，明确分开其实际部署参照与合格baseline结果，不删除该参照，也不把跨合同速度混成strict收益。NI通过不等于加速成立；只有对两个预登记合格baseline的一侧上界都低于1才支持该有限panel的统计加速结论，point≤0.97但上界≥1只能称点估计机会/不确定。报告每prompt、分层长度、失败、峰值内存；不得用cycle或vocab元素扩大n。12个prompt的CI可能宽，结果INCONCLUSIVE则停止并诚实报告，不追加到显著为止。建议固定为按prompt重采样的10,000次cluster bootstrap（每prompt内部先汇总两session的paired log-ratio），一侧95% percentile上界，seed在正式测量前固定；小n覆盖率限制要披露，不能看结果改方法。正式TTFT guardrail同样预登记为ratio一侧上界≤1.05，不能只报平均throughput掩盖首token倒退。

G3预算需单独核定。初稿上限：72timed+36heavy、2,048 forced-reference jobs、36 autonomous free-R与12 stability runs；至多2,204个重建起点，H=1则priming最多2,204次（实际数须由已冻结完整history recipe推导，不能只列12次warmup）。另限制500,000 reference token evaluations（含H）、2小时owned GPU墙钟、12GiB新增证据。这些不是可完成保证，先由G2实测每token/setup/readout成本估算能否在预算内完成；不能就不启动。若默认target-only已快于C1和candidate，研究应报告负结果，而不是换弱baseline。

## 8. 所有阶段共用的资源与停止规则

12GB是设备级约束，不是可用VRAM。实测driver free/total，计target+draft权重、实际allocated n_ctx KV、workspace、graphs、allocator保留、capture staging和系统占用。建议预登记至少max(512MiB,总显存5%)的运行余量，且还须测峰值；它只是初始admission规则，不保证无OOM。每arm只保留自身必要资源（重建R_old时仍必须保留其登记池布局，不能偷换），reference与candidate不同时常驻第二套target。host RSS硬上限、磁盘最低剩余和单进程timeout也必须在LOCAL_PATHS/预算中填入具体字节/秒，不能留无限；应基于实际可用RAM/磁盘留出系统余量，未核验则BLOCKED。下一job的最坏remaining token/workspace/output/time bound必须能放进剩余预算才允许启动；含reference prior-history的所有调用均入账。先对最大登记prefill/verify/export形状测峰值再扩，旧256MiB post-provision余量不证明峰值安全。更改offload/dtype/context以避OOM是新部署，不自动重试。

资源兼容性必须在启动前证明，不能“先跑到预算再说”：例如L512/cap16逐次j0，一个Qwen candidate+R仅逐commit重复activeKV就约2.28GiB，尚未计raw serialization、canonical双份、logits与free/R repeats。现CPU bridge的写盘方式不能据此直接承诺大矩阵落在8/12GiB内。只有已实现且验证过的stream/chunk保留策略给出保守最坏上界，或按完整复制预算证明足够，才能启动；不假定去重率。若不相容，预检BLOCKED，先在CPU实现有界存储或重新审批更小scope/预算，不能静默降低证据等级。

完整KV每commit都读取比较；chunk去重可减保留字节，不能减去GPU→host或全读成本。摘要only、可重构完整bytes、hash-only三种证据分别标。先按短cap实测真实payload/host峰值，再决定扩大，不能拿名义144/192KiB每token当完整GPU内存预测。

立即停止并保留failure：任一full-vector/active-state mismatch、R重复冲突、caller/mask/实际dispatch身份漂移、自然EOG语义错误、超时/OOM/nonfinite、数据不全/提取器未知格式、已有目录被覆盖风险、native进程cleanup不明、预算耗尽、主机出现其他GPU负载。数值失败不得自动retry到PASS；技术重试必须新attempt并明确原因，限最多一次且不排除首次失败。时间/温度扰动重试也计预算，不删除bad block。

最终结果至少区分：PREPARED_NOT_RUN、BLOCKED_MISSING_ADAPTER、R_OLD_UNPROVEN、NUMERICAL_MISMATCH、FINITE_SCOPE_MATCH、OBSERVER_BRIDGE_UNPROVEN、TIMING_INCONCLUSIVE、NO_PRACTICAL_GAIN。不得单一“PASS”吞掉这些层次。现在的交付只到PREPARED_NOT_RUN/NOT_READY_FOR_GPU。
