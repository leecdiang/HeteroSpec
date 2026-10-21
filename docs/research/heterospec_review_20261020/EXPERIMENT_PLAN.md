# 后续实验：先补真实多查询请求，再决定体系结构投入

设计日期：2026-10-20。状态：**新研究提案，未执行**。本轮只完成源码/紧凑证据审阅与 PR 合并。下文新增矩阵须由执行端绑定具体输入、运行时、观察器与资源预算后形成新的执行清单；不重开历史 UUID，不继承旧 launcher 的初始余额。

## 1. 要回答的三个问题

1. **适用性**：真实 speculative verification 是否出现所研究的 q>1、GQA、key extent 与图组织？
2. **请求价值**：在保持登记参考、包含输入/状态维护成本且使用强软件基线时，布局选择是否影响完整请求？
3. **物理机制**：如果仍有可观残差，具体是哪种资源或依赖导致，硬件是否拥有强基线没有的可验证能力？

#128/#129 已完成的结果使“继续重跑相同 QB/QH 微图直到看到优势”失去必要性。RTX 已完成 E2 及 #120–123；B570 已完成有限域的表示事务与一个 q1 请求核对。新的实验要填补上面的问题，而不是增加相同结果的计数。[RTX][R128][R129]

## 2. 优先级与阶段出口

| 顺序 | 平台 / 工作 | 具体产出 | 通过后的动作 / 失败的解释 |
|---|---|---|---|
| E0 | 两平台，现有档案与源码的 CPU 核对 | reference/runtime/实际几何对照、GQA支持矩阵、可复用的已完成数据字段 | 缺的只有新字段时才收集；避免重复已完成实验 |
| E1 | RTX，真实多查询请求的最小桥接 | 真实q分布、阶段/请求成本、完整端点、clean与profile关系 | 有q>1且能对应端点与成本，才扩展新输入 |
| E2 | B570，GQA算子准入，然后真实请求桥接 | QK与AV分别支持/放置/数值结果；匹配请求对照 | 不通过则报告具体支持/状态边界，不强行重写整个后端 |
| E3 | 最有信息的平台，小规模预先冻结的新输入或更长实际key | 迁移边界或有限请求收益的确认 | 没有实用请求残差则结束当前优化方向 |
| E4 | 仅有真实残差时，物理机制与硬件可行性 | 依赖时间线、资源干预、校准模型、同资源强基线 | 有独特机制与系统收益空间后才考虑RTL/PPA |

E1 与 E2 的 CPU 准备可以并行。GPU执行是否同机、是否互相影响，由实际机器身份决定；不得从平台名推定独占资源。

## 3. E0：可直接交给原机 agent 的只读准备

恢复每项已有科学数据的固定源与 DLL 身份、model/tokenizer、输入 IDs、采样/EOG/cap、phase-mask、microbatch capacity、KV格式和 graph mode。输出一个小表，逐项标明 **KNOWN / MISSING / INCOMPATIBLE**，优先使用已保存的日志和张量。

### 必须保持两个参考层次

- **算子参考**：同输入、完整输出与约定阶段数值；不能自动资格化自然模型状态。
- **请求参考**：完整 native token IDs、EOG flags、长度、末 token、停止原因及登记的输出窗口。

旧 B570 R 的失败不被新 clean q1 reference 覆盖。若新 source/DLL/model 配置必须建立新的参考，先把它明确命名为新研究的 R_e，并保留与旧参考的对应是否已证实。#129 的16-token窗口不等于历史128-token窗口。跨设备分别对本平台登记参考资格化，不要求无依据的跨设备逐位等同。[R129]

### B570 重点核对

PR128 的允许域有 equal-head 与 contiguous A 条件；PR129 真正的 Qwen3 是 Hq/Hkv=32/8。先写出自然 QK 和 AV 的实际 shape、stride、head map、batch 广播与 output order，再判断朴素 query-to-batch 变换是否落入新谓词。不能把 supports=true 或某个 q1 成功当作 q2/q4 GQA 的通过证据。[PATCH128][R129]

### RTX 重点核对

优先复用 #104 已合格的原生 speculative 路径与 #116 的实际张量。#123 中 `SOURCE_LINK_UNKNOWN` 等身份限制保持原义；若要从执行路径提升到源码机制解释，必须补具体 source-to-binary 身份，不能事后修改旧数据资格。确认真实 CUDA Graph capture/replay 条件与拟用 clean path 匹配。[RTX]

E0 是数据与源码映射工作，不扩建 CPU8。旧 CPU8 资格线若单独继续，仍保留其自身 SOURCE_BLOCKED、0/8 与无 F0；它不是这里的自动前置条件。

## 4. E1：RTX 真实请求桥接的最小可执行设计

### 4.1 固定一个模型组合与四个已暴露输入

从已有合格研究选择一个 target/draft 组合，保留其权重、量化与采样规则。优先 Qwen3，但必须使用同一已有冻结文件；不要把 B570 Q8_0 或历史 Q6_K 的不同身份混成同一参考。

从既有已暴露面板预先选 **4 个输入**，覆盖较短/较长实际 prompt 与已有正收益/近持平情形。选择以既有登记信息为准，在本轮新计时之前冻结；这是机制探索面板，不叫未见输入或独立确认。

| arm | 作用 |
|---|---|
| M_QB | 无草拟的目标运行，提供 q1 continuation 和修复成本控制 |
| C_QB_k1 | 真实 k=1 speculative transaction |
| C_QB_k3 | 真实 k=3 speculative transaction，主观察对象 |
| C_PQ_k3 | 与 C_QB_k3 同 draft/状态协议的局部表示对照 |

k 是草拟配置；**实际 q 不预设为 k+1**。记录 proposal 数、caller 行数、实际 occupied micrograph q、query列/batch、输出预留及状态提交。capacity4 也不代表每次执行四行。

### 4.2 一个小面板，不冒充新的大样本收益确认

每个输入安排两个 clean block，每个 block 含上述4臂并均衡顺序；在中间单独采 C_QB_k3 与 C_PQ_k3 的稀疏 profile，再做两个显式参考 R_A/R_B 控制。合计 **4×(4+2+4+2)=48 个主请求槽位**。同 DLL 的 clean/profile/clean 对应保留。

这48个槽位只定义核心科学工作量。加载、编译/capture、warmup、observer calibration、失败入口及清理必须列成显式槽位并在开始前一起计账，不能视作免费请求；最终 native process 数由冻结宿主安排决定。**不能把48写成全部执行成本已经确定或已授权。** 若现有参考无法对应输入/运行时，先完成新的参考桥接，不能省略 R_A/R_B。

每个 clean 请求保留完整 endpoint 和原生实际工作量；失败输出保留，但该 arm 不得到 qualified speedup。重复进程和连续 decode 步不当独立任务；此阶段只报告每输入、每block及范围，不从两个 clean block制造很精确的总体置信区间。

### 4.3 必须给出的输出字段

| 层次 | 字段与解释 |
|---|---|
| 真实几何 | role、prefill/verification、实际q、visible keys、physical key extent、Hq/Hkv、dtype/stride、设备放置、图复用 |
| 完整请求 | 声明的开始与终止边界、native endpoint、wall time；loading/cold capture与steady request分开 |
| 草拟与状态 | proposed/accepted/corrected/bonus tokens、pending处理、reconciliation、实际KV更新 |
| 阶段解释 | target prefill、draft、target verification、accept/reconcile、sampling/host handling；保留混合与未分配区间 |
| 观察完整性 | output projection/terminal interval、effective op counts、profile扰动、是否引入额外同步 |

分阶段计时若存在重叠，不能把各段之和当请求时间。图内kernel duration求和也不是critical-path份额。实际成本以独立 clean 完整请求为主，profile只用于解释运行形状和机制。

### 4.4 阶段出口

- 全部实际 width1：得到“该配置不触发多查询机会”，不转用 micrograph 制造 q>1。
- q>1存在但 endpoint不合格：报告状态/接口/数值边界，定位第一处可比较分歧；不给速度收益。
- endpoint合格，布局局部差异存在但完整请求无实用收益：报告被其他阶段稀释的结果，关闭当前优化支线。
- endpoint合格且有稳定请求残差：进入E3，随后选择针对残差的E4干预。

## 5. E2：B570 先资格化真实 GQA，再做同一问题

### 5.1 算子级最小资格面板

保持真实 model 的 d、Hq/Hkv 与 mask 语义，先构造 q=1/2/4 的 QK/AV descriptor。优先使用现有实际输入作为起点；人为扩展的多query输入必须标成合成/派生，不叫自然 speculative state。

选择两个事前固定的 key/stride 情形：一个来自 #129 的实际执行域，另一个由拟测试真实多query图决定。这里是新 GQA 准入研究，不重复 near1024 的性能筛选。比较 serial/PQ参考与 scoped QB；保留完整输入readback、QK/softmax/AV输出、head/mask/address与恢复后的final。

对每个 q/输入情形，分别报告 QK 和 AV：后端支持、实际放置、同步/返回和规定参考比较。只有 q1 通过不能推进到一般多查询请求。若新增准入条件，需要新的冻结 build/patch 与正负控制；不改变旧 #128 支持域或旧资格记录。

一轮有具体源码依据的窄修复后仍不能满足语义与支持，或需要大规模 shader 重写/换量化/换模型，结束本轮移植并将问题明确写为边界。这个停止规则是研究取舍，不是对不同硬件能力下结论。

### 5.2 请求级桥接

通过GQA准入后，才尝试E1同类原生请求方案。继续使用已有 accept/correction/bonus/rollback/pending 状态流程，并检查 phase与graph cache，不引入一个临时actor替代真实执行。

B570 当前新系列累计 **246.8043431/300 s，余额53.1956569 s**。上述新矩阵不被认为已容纳在这53秒中；如果实施新研究，先为新增范围确定预算并保留旧累计，不能从历史脚本重新以0计账。[R129]

## 6. E3：只扩展能够改变结论的一个维度

E1/E2有信息后，优先在以下两项选一项并事前冻结，不立即做全模型×全长度×全k的大矩阵：

- **新输入迁移**：例如12个项目此前未运行输入，MBPP/GSM8K各6，按本tokenizer长度三层、每层2个；按全量历史输入清单去重。报告全部输入，不只呈现通过者。
- **更长真实key**：针对观测到的目标阶段选少数预先固定区间，实际测得的visible/physical key是自变量；不能只改context capacity。

若目标是新输入请求收益确认，可固定一个模型与 M_PQ/M_QB/C_PQ/C_QB 四臂，保持同一 k；12输入×4臂×6session=**288个正式请求**，跨至少2个日期，warmup与控制另列并预先预算。这是可选的后续确认设计，不能拿六session/单机推成多设备总体。重采样和比较按请求/配对block/session组织，保留q1与近持平结果，技术重复不扩大独立样本数。

主要效应在开始前确定为 C_QB/C_PQ 的完整请求比；草拟经济性单独以 C_QB/M_QB 报告。效果门槛应结合注册的最小实用收益与A/A噪声；若沿用2%作为工程筛选，必须明确它是选择标准，不是测量精度认证，也不能用扩大样本反复追正。任何整体不合格arm不发布qualified speedup。

这一步不能以重跑已完成 E2 为目的。新增输入或长度应实际补充v3已声明的局限。

## 7. E4：硬件研究的最小证据要求

当前没有足够证据直接定义一个有收益的新模块。若请求级残差已经成立，再选择可证伪干预：

- 提交/重放假设：正确重放开关和事件/依赖记录，结合请求成本，不能仅看API计数。
- 数据供给假设：真实流量与缓存/带宽计数器、复用范围干预；不能由“量化matvec”名称推出memory-bound。
- 算术与占用假设：对应kernel和资源数据、受控并行/资源变化；仍保持原数值契约。
- 状态维护假设：记录自然KV更新、reconcile与主机等待，区分状态正确性和执行开销。

若模型使用无重叠串行占比f和阶段加速s，系统上界可以写为 S=1/((1-f)+f/s)。前提必须由请求依赖证明；**不允许把#129的2.8% subtotal代入**。有重叠时使用实际依赖图和可被消除的路径长度。

同资源基线必须享有合理的query并行、权重/KV共享、缓存、packing与重放。候选需要明确额外能力、缓冲/端口/控制成本和数值求值；原PR110五标签同policy的parity不能当五种架构性能比较。[H0]

真正进入RTL前，先给出校准后的周期/流量模型以及它对未用于校准的实测场景的误差。之后再核查综合频率、面积/资源、功耗模型与片外传输。若强软件后已无实用请求空间，就完成论文边界章节，不以硬件名字代替结果。

## 8. 可转交执行端的短说明

> 先只读恢复最新合并的128/129及RTX124证据，保持历史R、失败、CPU8 0/8无F0和246.8043431s累计。优先输出实际reference/runtime/形状/字段缺口表；RTX用既有合格native路径设计真实k1/k3请求桥接，记录实际q而非假定k+1，clean请求计时与稀疏profile分开。B570先核对32/8 GQA的QK/AV是否落入128的equal-head准入域，逐项说明支持/放置/数值差距。不要重跑已关闭QH/1024微图、改参考追认旧结果或扩建CPU8。提交具体输入/arm/控制/预算清单和停止条件后，才按当前会话已获授权的范围开展新实验；此研究设计本身不启动GPU。

[RTX]: https://github.com/leecdiang/HeteroSpec/blob/9b8cdba784b34a5aa3e8981073223c451bbaaf54/docs/research/rtx_evidence_synthesis_20261018/EVIDENCE_MATRIX.md
[R128]: https://github.com/leecdiang/HeteroSpec/blob/cf6c8bf43dc1ee4e9e8529bbe42300844e0165c9/benchmarks/b570_qb_batch_broadcast_v1/transaction_v1/RESULT.md
[PATCH128]: https://github.com/leecdiang/HeteroSpec/blob/cf6c8bf43dc1ee4e9e8529bbe42300844e0165c9/benchmarks/b570_qb_batch_broadcast_v1/qb-batch-broadcast-portable.patch
[R129]: https://github.com/leecdiang/HeteroSpec/blob/c541241ad62213a8d31006e539e4ce0623793040/benchmarks/b570_model_request_bridge_v1/RESULT.md
[H0]: https://github.com/leecdiang/HeteroSpec/blob/9b8cdba784b34a5aa3e8981073223c451bbaaf54/benchmarks/rtx_reference_packing_v1/H0.md
