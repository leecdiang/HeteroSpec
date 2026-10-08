# HeteroSpec B570：机制辨别与单候选可行性验证 — 完整执行 Prompt v1

执行平台：**原来完成 PR #63 的 Windows + Intel Arc B570 本机，在有本地命令执行权限的 GPT Work / Codex 会话执行。**不要发给只有 GitHub 读取能力的云端会话，也不要在 RTX、358H 或其它 GPU 上替代执行。本机已有研究依赖应优先复用。

这是一轮新的、有限的研究，不是重新打开 #63 的截止窗口，也不是继续无界追求正结果。你需要从核查、实现、实验、独立复算一直完成到**新 Draft PR 和中文交付**。成功的机制结果、成功的候选、科学失败和实际能力不足都必须有可复核交付。不要只给方案、启动后台进程后结束，或以“可以继续”收尾。

## 1. 目标与授权

研究问题：**B570 上为什么某个 prefill 修复能恢复旧任务，却在另一个输入或 continuation 几何下失效/回归？能否据真实状态与当前计算的证据，形成一个固定、任务无关、比全局串行更有成本希望的局部执行配方？**

优先建立可解释且可反驳的机制证据；只有机制和成本共同支持时，才实现一个候选家族。不得预设 attention 是根因，不得保证有正向加速。

本 prompt 已授权：在隔离目录中修改私有研究前端、添加自然 checkpoint 和只读观测、编译新私有程序、执行下述有限 B570 原生请求、恢复并核验现有本地证据、创建新分支与 Draft PR。无需每个阶段重复请求确认。

继续遵守合并暂停：**不合并任何 PR，不修改论文，不覆盖 #63 或历史实验，不修改既有 tag/release。**不改系统驱动、电源策略、用户桌面程序或原模型/runtime；不关闭不属于本任务的进程。若环境变化，记录事实和适用范围，不编造因果。

## 2. 固定起点与必须保留的结论

仓库：`leecdiang/HeteroSpec`。

本 prompt 审阅的 PR #63 head：`66594b349955e66146702325559c26019ea16485`。

原目录：`benchmarks/b570_closeout_overnight_v1/`。

必读：

- `REPORT.md`、`PROTOCOL.json`、`DECISION.json`、`B_SUMMARY.json`、`C_SUMMARY.json`、`E_PLAN.json`、`E_DECISION.json`。
- `normative_audit_20261007/REVIEW_REPORT.md`、`SUPPLEMENT_VERIFICATION.json`、`MECHANISM_SUPPLEMENT_SCHEDULE.json` 及其冻结实现。
- `code/src/native.cpp`、`target.cpp`、`observer.h`、`runner.py`，以及当前资产、归档恢复与输入暴露账本。
- 作为比较依据读取 #59/#60；#62 的 `benchmarks/rtx_closeout_bcd/` 包含已完成的 RTX 宽度失败、真实状态交叉与 fixed-UB 负效率结果。不得重复把这些问题说成未做，也不在 B570 本机声称已独立扫描 RTX bulk raw。

先核对实际 PR head。若 #63 后来前进，读取增量并记录采用的确切科学 snapshot；不混用不同 head 的参考、程序或计时。原 snapshot 和所有负结果保持可追溯。

当前证据必须原样保留：

1. B570 原修复在共享24个 MBPP 上合格；原未用8个 MBPP 中，MBPP/72 的 matched T 和 N1 各四轮均偏离，首差异零基41。原“未用”队列现在已暴露，不能再次叫 holdout。
2. 共享 B 的 N0/N1 比值为 generation `0.9995218815660408`、whole `1.247058534284672`；T/N1 为 `0.8040229271596392` / `0.6935408122196928`；R/N1 为 `0.1885246521769912` / `0.17905546046949286`。比值大于1才表示候选更快。
3. C 的旧长3任务、k3/UB4、cap128 相对 matched T 为 `1.3457983005631404` / `1.048339053506626`，相对 ordinary R 仍慢；不得升级为全平台部署收益。
4. E 的五个 UB2 候选均资格失败，保留 NO_GO_PILOT；再扫 k、UB 或换任务不属于本 prompt。
5. /145 的 ordinary 同k1/UB2路径通过，而 prefill128 修复路径失败；/42 两种路径都失败。这些父路径不构成已经做过的同状态反事实。
6. 错误路径 /42、/145 的自然 top1/top2 margin 分别约 `0.346687`、`0.116642`。不能假设错误只发生在小 margin；不能据此发明已认证的 margin guard。
7. 原因仍为 NOT_CAUSALLY_IDENTIFIED；原生 mid-trajectory state cross 尚未实现。#63 的规范审核已补齐其有限任务；本轮不能冒充是在修补原核心遗漏。

## 3. 新研究的边界、预算和持久执行

新目录建议 `benchmarks/b570_mechanism_pilot_v1/`；原本机路径从现有记录读取，不猜用户名或磁盘路径。私有运行目录、源码历史、原始证据、公开派生目录分开，所有新增文件只属于这轮。

固定模型/后端：B570、Qwen3-8B/0.6B Q8_0、原发布 Vulkan/runtime、ctx1024、threads10/batch10、FA off、greedy seed123、单序列。原模型散列与资产散列按 #63 复核。实际设备不能只看 Vulkan 序号：每个会话枚举物理 B570，并从真实模型加载日志验证 target/draft device 和 offload。禁止重现被错枚举到 UHD730 却当 B570 的记录混用。

本阶段上限：**312 次非热身完整生成、24 次额外 target 验证 forward、48 次排除热身**。下述上限之内，失败/中断/无效尝试同样记账；不可把失败重跑次数藏在预算之外。无需用完预算。任何额外模型重算、参考生成、局部 forward、暖机均另列并计入对应上限。

先建立 `PROTOCOL.json`、`SOURCE_BINDINGS.json`、`ASSET_MANIFEST.json`、`UNIT_MANIFEST.json`、`STATUS.json`、`LEDGER.jsonl`、`BUDGET.json`、`RUNBOOK.md` 和 `resume` 入口。每阶段开始前提交其源码、binary hash、输入和判定规则；原始 attempts 追加，不覆盖。候选和新输入的冻结发生在相应输出之前。

用持久 worker 执行预先实现且已授权的单位；每单位原子写入结果、散列和进度，提供心跳和人工 STOP。轮询不长期阻塞交互；持续报告已完成分母和真实下一步。模型作业不能并行争用同一 GPU。

不要沿用 #63 已过期的 cutoff，也不要自行加一个“5小时后不交付就退出”的限制。先估计 ETA 并保存可续跑状态；若平台的硬额度/上下文限制真的中断，完整记录中断位置，恢复时仅执行尚未完成的单位。不得声称 prompt 能消除宿主硬限制。已完成且 hash 验证通过的单位不重复生成。

普通科学 mismatch 不是基础设施故障，**不重试以追成功**。基础设施无效也保留完整 attempt：仅在源冻结、明确修正平台/构建问题且预算允许时，执行最多一次可解释恢复；原记录不删除。只管理本任务所创建且 PID+creation identity 可验证的进程。

无论 GO、NO_GO、UNSUPPORTED 或 PARTIAL，都继续做已有证据的独立验证、归档、报告和 Draft PR。门槛失败是有结论的研究完成；实际未执行则明确未执行。

## 4. Stage 0 — CPU 可行性审计，零新模型请求

恢复 #63 原包及补充包，核对 SHA、CRC、对象映射与资产；复算66份导出 CSV 的744行成本，检查所有速度分母和输出资格。发现差异则保留并阻止依赖该数据的推断。

重点审查下面的执行区别：

- R 的 ordinary target caller 分组与 matched/native 的 `prompt[:-1]`、最后一个 prompt token 分组。
- prefill/continuation UB、实际 occupied query、输出槽 reservation、stride、mask、逻辑 KV位置、单序列 ownership。
- 首 pending token 在哪里采样；sampler 是否已经 accept prompt、是否 clone 于正确时刻；哪些 sampler history/penalty 对当前 greedy 合同实际有效。
- 状态构造与状态搬运：当前 `observer.move` 在 capture-off 仍读出 source、读回 restored 和 source-after，并进行往返校验；context 创建、host/device 传移和同步可能是前端成本。不能从这里直接推断全部慢速原因。
- 原 R 与 matched T 都在合格共享队列保持参考，却有很大的耗时差。查是否涉及 caller/图/输出槽路径；“配了相同 UB”不能替代实际相同执行证明。

输出 `FEASIBILITY.md`：区分“数值/状态问题”“研究前端见证成本”“未观测的后端成本”。已有精确累计时间能直接使用，只有调用计数的部分不能伪造算子耗时。内核 dispatch 缺少实际证据时保持 unknown。

新颖性审查使用原始来源：

- LLM-42：https://arxiv.org/html/2601.17768v2
- Vosti：https://arxiv.org/html/2609.38981v1
- Batch-invariant inference：https://thinkingmachines.ai/blog/defeating-nondeterminism-in-llm-inference/

写一个简短差异表：已有原则、我们已有证据、这次准备验证的未决预测。选择性确定性、KV一致、固定数值路径均不能重命名为首创。当前目标是实现可辨别干预并导出可迁移配方，不是用审计项目数量证明创新。

## 5. Stage A — 自然 checkpoint 实现与历史行为桥接

开发任务固定为：HumanEval/42、/145、/138、/134、/58、MBPP/72。它们全部已暴露；/134 是匹配控制，/58 保留其宽度边界，/72 是旧迁移失败。

在隔离的新私有前端加入 checkpoint 和只读日志，使用原公开 state API 及经过核对的 sampler clone。不得改变模型数值、采样、候选生成、accept/bonus/rollback、停止或 reference。

Checkpoint 只出现在真实运行的 target 验证调用前或明确的自然提交边界。保存：

- 真实 target/draft KV、各自位置与序列 ownership。
- 真实 committed prefix、pending、已经产生的当次 proposal、target/draft post-sample sampler 状态或有效 clone、loop/acceptance counters。
- 当前逻辑 caller IDs/positions/sequence/logits mask，prefill/continuation phase，以及实际数值几何参数。

不从空 KV 按已知答案重建 donor；不强制参考前缀；不拿未来 proposal tape 代替真实起草。Opaque sampler bytes 若 API 不提供，明确写 unavailable，并用 clone 元数据、行为 shams 和有效配置说明能力范围。

每任务桥接四个来源定义明确的旧条件：R_reference、N1_repaired、E_k1_ub2，以及 ordinary 控制。五个 HumanEval 的 ordinary 控制为 M_ordinary_same_k1_ub2；MBPP/72 的 ordinary 控制预先固定为原 B 的 N0_ordinary（k2、prefill1、UB1），以提供迁移失败的自然父轨迹。ordinary 条件的 prefill、handoff 和 reservation 按 #63 实际源配置复现，不靠名称猜测。6任务×4条件×2轮，共 **48 次完整请求**；热身另列。两轮分别采用 capture-on 和 capture-off，必须保持各自可获得的历史完整数组与端点，包括 N1 在 /72 的失败以及 E 的失败。历史没有该 task/条件完整参考时，明确记为本轮新父轨迹，只检验开关观测是否保留行为，不能冒称历史桥接。不能把失败修掉以后才叫桥接通过。

只捕获被冻结少数 checkpoint 的全分数/必要张量及状态，避免无目的保存每层每步巨量 tensors。桥接费用是诊断费用，不是正式加速样本。

桥接失败时，停止后续机制/候选 GPU 推断，交付 `BLOCKED_BRIDGE`，完成 CPU/归档/PR。不要在桥接中搜索新参数。

## 6. Stage B — 真实 donor × 当前验证路径的交叉

固定案例顺序：/145、/42、/72，最多三例、每例两轮。依据自然完整轨迹寻找首个可用对齐检查点；规则是最接近保留分歧、但尚未分歧且位于真实可恢复边界。不按 margin 或速度挑点。

两种 donor 来自 Stage A 这次真实父轨迹。只有 committed IDs、长度、pending 及当前逻辑位置/请求语义对齐时，才比较。/145、/42 用 N1 与 E1；/72 用 N1 与 ordinary N0。不得额外生成父轨迹或按结果更换案例。

当前路径对比的逻辑验证 batch 固定为某个明确父轨迹已在线生成的当次 batch，四个交叉 cell 使用完全相同的 IDs/positions/mask。它是有成本的局部诊断，不是投机整轨迹的新方法。确保没有把不同 proposal、history 或 logits row 混进“同状态”。

对于2个 donor和2种当前数值路径，做2×2交叉；最多 **3×2×4=24 次辅助 target forward**。保存全部 float32 decision logits、真实 top1/top2、指定参考/替代/EOG分数，以及操作前后 state/prefix身份。

每种 donor 的原路径 restore/continue sham 必须复现父轨迹完整输出且原 source 不变；最多 **3×2×2=12 次完整 sham 请求**。sham 保留该父轨迹原本的 batch 和全部逻辑参数；交叉的共同 batch 若与另一父轨迹原 batch 不同，不能把那个交叉 cell 当作同路径 sham，也不能要求它重现另一父轨迹的历史决策。两者的验证作用分开报告。如果 reserve slots、caller形状或其它参数无法保持一致，将当前干预定义为“完整路径配方”，不能把它叫纯 UB 单变量或唯一 kernel 因果。

归类为 STATE_EFFECT、CURRENT_PATH_EFFECT、INTERACTION、NO_DETECTED_EFFECT 或 UNALIGNED/UNSUPPORTED。至少两个独立任务具备通过 shams 的有效交叉，才给出跨案例的机制支持；同一任务重复 cap 不算独立案例。保持 logits variation、argmax翻转、完整输出恢复三个不同层次。

自然 checkpoint 不可恢复、logical prefix 不齐或 shim 改变原轨迹时，写出真实限制。可分析已取得的自然数据，但不能用 forced prefix 或 token哈希冒充同状态交叉，也不能宣布 causally identified。

## 7. Stage C — 是否值得实现一个候选

先写并提交 `CANDIDATE_DECISION.json`。候选必须由已完成的机制/路径证据导出，说明改哪里、为什么应同时修复 /72 和保留旧恢复、预计成本来自哪里。

最多 **一个任务无关的实现家族，一个预先固定的 k/UB 配方**。允许隔离的 frontend/graph布局/阶段绑定改造；已有 Vulkan shader、精度、权重保持不变。若须改私有图构造库，单独命名和隔离，保留旧发布库和桥接控制，不能覆盖旧 binary 或把新库当原资产。

不能直接假定把 RTX attention reshape 搬过来就足够。若数据支持具体局部 layout/operand 路径，才能提出它；若主问题是 prefill状态构造，配方必须覆盖它，而不是只限制当前调用。Source-level dispatch eligibility 不是实际 kernel 证明。

不要实现按task ID、已知参考、divergence位置、未来proposal或完整离线答案路由。没有可计算误差上界的“小 margin 回退”不构成安全 guard；在线额外 reference forward 若使用，全部计时且比较其成本，不能隐藏。

若机制仍不可辨别，或只有删去一次性见证/同步才能提升研究前端成本，则分别交付 `NO_GO_MECHANISM` 或 `HARNESS_OPTIMIZATION_ONLY`。后者可以有用，但不能宣称新数值修复/新投机算法。不要再另起第二家族、扫五种 k 或看结果后扩大范围。

有可信配方时，源码/config/输入身份先冻结；在6开发任务各2轮执行候选，最多 **12 次完整请求**，分别采用 capture-on 和 capture-off 并要求完整输出一致。以固定旧 R 完整数组离线评分，必须修复 /72 并保留另外5个参考。任何失败停止该候选后续测量，报告完整失败；不准修正后把同一开发集升级为独立确认。

## 8. Stage D — 原暴露面板的资格扩展

仅在开发资格通过后运行。将旧24个 HumanEval、共享24个 MBPP、旧8个 unused MBPP 合并为**56个已暴露任务**；任务来源和 prompt身份先核验。不得把旧8个仍叫 unused。

候选每任务2轮，共 **112 次完整请求**。参考使用原 immutable R 完整 IDs/EOG/cap128 exports，只用于离线评分；它们是已付费的保留参考，不作为新运行或新速度基线。旧参考和当前源/资产合同关联必须成立，Stage A 的 fresh R 桥接必须已经通过。

要求112/112全数组、长度、runtime EOG或cap端点一致及重复稳定；列每任务结果和首差异。任何 mismatch 导致 full-panel gate失败，停止 Stage E。保留已运行的完整矩阵，不补选任务、替换参考或将成功子集称全体。

本阶段只能支持这56个暴露输入、cap128和冻结合同，不能证明跨长度、模型或其它后端。

## 9. Stage E — 一个小型新输入/成本确认

只在 Stage D 通过后开始。先重新审计所有可访问历史，包括 #63 的32 MBPP、原8未用任务、开发输入、#62输入及已知其它平台记录。未知暴露不能当未用；不能假称重新扫描了不可访问 RTX历史。

从审计支持的 eligible MBPP 中以 `SHA256(task_id + "HeteroSpec-B570-mechanism-v1-confirm")` 排序取16个。只用静态输入条件确保 prompt+cap128 在ctx1024内；禁止依据生成长度、难度、margin或运行时间筛选。冻结 manifest、dataset/prompt/tokenizer哈希、候选code和先验判断，再生成任何新参考。

不足16个时，在新输出前明确缩减并保存 amendment；少于8个则标 `UNSUPPORTED_UNUSED_PANEL`，完成已有范围交付。审计范围有限时，准确称 accessible-project-unused，不称 model-training unseen。

四条件：ordinary R、候选同 target计算配方的 matched target-only、候选 speculation、旧 N1。每条件16任务×2轮，最多 **128 次完整请求**。第一轮条件顺序按固定排列，第二轮完全反转；任务顺序按固定 hash 轮换。每会话独立初始化，显式热身除账，每请求清KV/sampler/pending/history，无prompt-cache/多并发。

每轮 R 均作为付费原生请求，检查稳定；R输出不能作为候选在线输入，也不能反向修改候选。新输入首次 mismatch按预定门槛失败，所有其它已预定条件和费用按资源许可留存为诊断，不调候选。

性能分别报告 generation、whole request、真实host端到端。所有在线初始化、state读写/克隆/回滚、设备同步、draft/target与cleanup都不能漏账；disk证据落盘的边界保持明确。capture资格采用 A/C 已预算请求，E 两轮均为 capture-off 正式费用；不能从有观测计时中扣算无观测成本。若一种新增前端的 capture-on/off 桥接仍缺失，应在新输入输出前从128请求中预先扣出诊断额度、同比缩减完整的新输入矩阵，并保存 amendment；不能超预算补跑或减少单个条件以保留16任务的外观。

对照关系至少包括候选/R、候选/匹配target、候选/旧N1。引用比值统一 baseline/candidate：逐任务两轮中位数比后取任务GM，提供每任务绝对ms及每轮方向。

预先设定本阶段投资门槛：

- 全部候选与匹配target对付费R的完整输出和端点通过，重复稳定。
- 候选/R 的 generation GM≥1.05、whole GM≥1.03，两轮汇总方向均为快。
- 达标才给 `GO_LARGER_VALIDATION`；这只是小型pilot的后续投资门槛，不是可靠总体收益证明。两轮不足以宣称统计显著或生产效果。
- 若只胜过旧N1、仍慢于ordinary R，写 `SCOPED_REPAIR_WITHOUT_DEPLOYMENT_GAIN`；若只清理研究前端成本，写 `HARNESS_OPTIMIZATION_ONLY`。
- 新输入资格失败则 `NO_GO_TRANSFER`；性能失败则 `NO_GO_EFFICIENCY`。不得事后降低门槛或再补一轮直到通过。

本 prompt 不启动更大矩阵、第二模型或其它硬件；这些仅在 GO 后列为下一轮冻结方案。

## 10. 验证、成果和新 PR — 所有分支都必须完成

实现独立CPU parser/validator，不导入执行器的 endpoint、qualification 或比较函数。直接重读完整raw IDs、runtime EOG、实际 suffix、scalar参考、checkpoint/clone/对齐证据、cost端点、所有失败和source identities。至少检查：同路径sham、source不变、隐藏未来答案、计费单位、重复key、missing分母、无效设备、原科学失败保留与新输入暴露。

精确预算：Stage A48、B最多12完整sham+24辅助forward、C12、D112、E128；最大完整非热身 **312**。不能把辅助forward当作完整生成，不能把 repeats 当额外独立任务，也不能把已门控未执行阶段说成完成。

输出并验证：

- `REPORT.zh-CN.md`：先讲结果与含义，再讲证据和局限；明确机制贡献、候选贡献与研究前端优化的区别。
- `DECISION.json`、`CAUSAL_RESULTS.json`、`QUALIFICATION.json`、`COSTS.csv`、`WORK_ACCOUNTING.json`、`COUNTS.json`、`FAILURES.json`、`INDEPENDENT_VERIFICATION.json`。
- `RELATED_WORK.md`：与 LLM-42、Vosti、batch-invariant inference 的机制/假设/适用范围直接比较；哪些新颖性未成立。
- `NEXT_STAGE.md`：只在证据支持时推荐更大确认或第二合同；NO_GO也有明确收束建议。
- 冻结源码、精确构建身份、source/binary/model/runtime hashes、完整attempt ledger、暴露审计、manifests、相应复现命令。

按内容地址封存本轮 raw/state/必要logits、失败、源码历史和私有程序；保留外部模型/runtime依赖哈希。实际恢复并用独立CPU代码从恢复字节重新派生、核对CRC/SHA。不要仅检查ZIP存在就称可恢复。旧两个包不重写。

GitHub只提交本轮派生结果/代码/绑定/恢复说明，bulk state、模型和runtime不上传。新branch基于实际main，只增加新研究目录；#63 固定 snapshot作为明确外部证据依赖，不能把它整包合进当前PR。新 Draft PR说明base/head、完成/失败/门控计数、完整输出、强基线成本、真正新增证据与适用范围。

通过新的远端fetch/checkout和逐Git blob/hash回读验证实际交付，确保diff没有论文或旧实验改动。若GitHub暂不可写，完成本地commit、bundle及准确上传阻塞记录，不冒称创建PR。重试只针对传输，并不重跑模型。

最终中文汇报必须包括：新Draft PR链接、确切head、各阶段真实分母、是否建立有效交叉、是否修复/72且保留旧恢复、候选是否比ordinary R更快、是否值得下一轮、不可支持的主张。即使NO_GO也完成此交付，不以“建议继续”结束。

开始执行，直到这轮有限研究与交付全部完成。不要合并。
