# RTX H2/V2 完整执行 Prompt：独立提案与固定提案验证的前瞻复现

日期：2026-10-01（北京时间）。仓库：`leecdiang/HeteroSpec`。

用途：将本文件整体交给 RTX 5070 Ti Laptop / Windows 平台上的执行代理。先完成本研究及审核，再整合论文。本文件授权方案落地、实现、构建、资格检查、新执行、验证、归档和创建 draft PR；不授权修改论文或自动合并。

## 可直接复制的执行指令

你负责新研究 `RTX_INDEPENDENT_PROPOSAL_REPLAY_V2`。请完整阅读本 prompt，并在 `leecdiang/HeteroSpec` 上实施，而不是只交付计划。你的工作是补上 V1 未实施的 H2：通过独立 draft 提案生成器与 target-only 固定提案验证器，在未运行 reserved live 之前生成并封存完整轨迹预测，再与独立执行的原生 RTX batched live 路径比较。

工程阶段允许在已暴露输入上调试与修复，并保存全部尝试；进入冻结 discovery 和 reserved 后严格遵循停止规则。阳性结果不是交付条件。不得以“现有 CLI 没有 tape 接口”为由跳过实现：新增接口和独立前端正是本任务的工程内容。确实无法满足独立性或资格时，交付可审计的阻塞原因及已有工作。

### 1. 已完成的研究及本次边界

截至制定本 prompt：

| 来源 | 固定身份 | 已知结果／作用 |
|---|---|---|
| main | `f8290281156f6b3de8fbc8b44fd10a4afa7bcd89` | 当前基线；执行前重新读取最新 main |
| PR #42 | `3d60ac010523bbb0bf5c9db879d221159473bf0e` | RTX V1：H1 discovery 24/36，H2 未执行，reserved 0 次；独立延迟臂已完成 |
| PR #41 | `61a1eb104d9bd1f6220a066d797dcc10dfed268d` | B570 新干预：24 个新 reserved 提示词的输出已曝光 |
| PR #40 | `df7953365fbc33757c1aac772bbe915d9f407919` | 编辑修订；本次不修改论文 |

PR 页面：<https://github.com/leecdiang/HeteroSpec/pull/42>、<https://github.com/leecdiang/HeteroSpec/pull/41>。

V1 的 H1 不匹配来自 `/64,/106,/119,/128` 四个任务，各三次均不匹配且重复稳定。V1 H1、RTX 延迟和 B570 干预结果均继续封存。本次不重新筛选 H1、不补填 V1 的 reserved 分母，也不重做已完成的延迟实验。

**研究问题：**在所冻结 RTX/CUDA 栈上，由独立生成的提案驱动固定提案 target verification，能否在原生 batched live 运行之前，正确预测完整 generated-token-ID 轨迹，包括与 UB1 reference 不同的轨迹？

**解释边界：**H2 的预测生成阶段会使用 draft 模型和 target 计算。这与 B570 的 target-only UB1 预测器不同。成功可以支持“独立提案／验证程序在 RTX 上的前瞻路径复现”，不能直接支持 B570 的 draft-free 机制已经迁移到 CUDA、唯一数值原因、模型或 GPU 范围的一般规律。复用相同低层数学内核是允许的，程序拆分的意义和仍共享的实现必须披露。

### 2. 仓库、依赖和只读证据

从最新 main 建立干净、独立 worktree，分支建议为 `experiment/rtx-independent-proposal-replay-v2`。记录 starting HEAD、main、分支、工作区状态和全部依赖 SHA。若 main 尚不含 PR #41/#42，以只读 detached checkout 或 GitHub PR refs 获取其精确 head，不需要先 merge，也不得把大归档无目的地重复复制入新研究。

至少阅读：

- `benchmarks/rtx_transfer_latency_v1/` 下的 `PREREGISTRATION.md`、`protocol.json`、`asset_identity.json`、`runtime_freeze.json`、`RESERVED_SET.json`、`prediction/REPORT.{md,json}`、`CLOSEOUT.{md,json}` 与 `REPRODUCTION.md`。
- `scripts/platform/rtx_transfer_latency_v1/{native.py,study.py,audit.py,verify_common.py,verify_prediction.py,verify_provenance.py}`。
- `benchmarks/rtx_direct_id_v2/` 下的 protocol、capture contract、build/runtime manifest、formal report，以及相应 runner/verifier。
- PR #41 的 `RESERVED_SET.json`、`FORMAL_EXECUTION.json`、`ENDPOINT_ANALYSIS.json`；此前 B570 prediction、M4、358H、RTX 的已执行任务清单与暴露记录。
- `docs/{data_policy.md,experiment_protocol.md,reproduction.md}` 及适用的 `AGENTS.md`。
- pinned llama.cpp 的 CLI/server 生成循环、draft-simple 实现、采样器、tokenizer/chat template、target decode 与 KV rollback 源码。

新增目录：

```text
benchmarks/rtx_independent_proposal_replay_v2/
scripts/platform/rtx_independent_proposal_replay_v2/
artifacts/rtx_independent_proposal_replay_v2/
```

在新目录保留本 prompt、机器可读协议、源码、patch、身份、冻结收据和结果。旧研究源码、结果、数值和论文保持只读。确有需要的 `.gitattributes` / `.gitignore` 调整只能追加新目录的规则。

### 3. 冻结计算栈和输出契约

优先沿用 V1 prediction 臂的原始 CLI／DLL，不使用延迟臂的 timer executable 作为 live oracle。

| 项目 | 要求 |
|---|---|
| GPU | NVIDIA GeForce RTX 5070 Ti Laptop，显式 CUDA0 |
| 上游 | llama.cpp b10839，`0cae43063cf15170e91a2ff4d034da0ecef4a1b2` |
| target | Qwen3-8B Q8_0；SHA256 `408b955510e196121c1c375201744783b5c9a43c7956d73fc78df54c66e883d6` |
| draft | Qwen3-0.6B Q8_0；SHA256 `9465e63a22add5354d9bb4b99e90117043c7124007664907259bd16d043bb031` |
| HumanEval 数据 | SHA256 `b796127e635a67f93fb35c04f4cb03cf06f38c8072ee7cee8833d7bee06979ef` |
| 采样 | greedy，seed 123，temp 0，top-k 0，top-p 1，min-p 0；其余实际 sampler 参数完整冻结 |
| live | `draft-simple`，最大 draft 宽度 2，最小宽度 0，target `n_ubatch=2` |
| reference | 原始 common CLI target-only，target `n_ubatch=1` |
| FA／放置 | flash attention off；target 37/37、draft 29/29 层 CUDA0 offload |
| context | 每次 fresh process/context，ctx 4096，禁止跨运行 prompt/KV 缓存 |
| 端点 | 首 128 个原生已提交 generated ID；更早 EOG 时包含首个 EOG，并立即截止 |

从 V1 的确切命令和 pinned 源码获得完整有效配置。不要将 B570 的 batch 512、ctx 1024 或 speculative-example 前端搬进 RTX CLI 研究。RTX `n_batch`、draft context/ubatch、draft 阈值、tokenizer/chat template、BOS/special-token、所有默认值都须解析为显式有效配置，并核对实际日志。`k_max=2` 不表示每轮一定有两条 proposal；允许原生规则产生 0、1、2 条，必须记录实际长度及端点附近的预算行为。

输入文本使用 V1 完整模板：

```text
Complete the following Python function. Return only the completed Python code, without Markdown fences.

{HumanEval 原始 prompt}
```

模板占位符替换规则、UTF-8/LF 字节、native chat formatting、`enable_thinking=false`、实际 prompt token IDs 必须一致。冻结完整输入字节 hash 和实际 tokenized-prompt hash；不能把日志中的显示文本当作实际 prompt tokenization。

逐文件记录并前后重哈希 target/draft/data、原始 CLI、H2 新前端、低层 DLL、patch 和源代码。记录 OS build、GPU/PCI ID、驱动版本及相关 driver DLL 字节、CUDA runtime、编译器和环境覆盖变量。V1 OS build 26300；历史 26200 不是同一条件。环境变化应定义为新资格条件，不能仅凭版本字符串宣称字节复现。

本研究没有性能／能耗主终点，工程计时不构成速度结论。

### 4. H2 必须落地为可分开的 P、R 和 live

实现三个角色，其中 H2 由独立 orchestration 连接 P 和 R：

**P — 独立 draft proposer。**只加载 draft 权重；从输入和 H2 自己已产生的 committed prefix、自己的 draft KV／sampler 状态生成本轮 proposals。只能消费当前／过去状态，不读取 target logits、参考完整答案、原生 speculative live 输出或其 tape。保持 pinned draft-simple 的初始 prefill、draft partition、sampler reset/accept、缓存和回滚顺序。不得未经验证改为每轮整段 prefix 重算，因为这会改变 draft 数值历史。

**R — target-only fixed-proposal replayer。**只加载 target 权重；对显式传入的本轮 token IDs、positions、sequence IDs、logits mask 执行 target verification，并独立实现 greedy acceptance、首次 rejection/correction、全部 acceptance 后 bonus、KV suffix 删除和下轮 pending-token 状态。R 不加载 draft 模型，也不自行生成 proposals。prefill、输出 logits 索引、attention/position、采样链、target 状态历史必须依据 pinned CLI 实现，而不是凭 UB2 参数推定等价。

**L — 独立原生 batched live。**使用被冻结的原始 CLI 自行执行 draft-simple，不能导入 H2 tape、预测数组或 proposer 状态。优先完全不改原始 CLI；如需额外原生 proposal／graph 观察器，先在暴露任务上证明观察器输出语义一致，其补充数据不能替代原始 CLI 的正式 live oracle。

P 可复用经审计的低层 draft 函数，R 可复用 tokenizer、sampler 和 llama C API。不得将整段原生 speculative CLI/server 生成循环当作 predictor 再换文件名；不得调用 `llama-cli --spec-type draft-simple` 得到一份输出，然后把它改称“独立 tape”或“预测”。提交模块依赖／调用图和逐项对照表，明确哪些代码共享、哪些状态转换独立实现。

优先使用与原始栈兼容的 native C++ 前端，保留实际 backend bytes；也可采用有完整状态及事件记录的 orchestration。独立性指有明确输入边界的执行组件及无 live 数据依赖，不要求重新实现 CUDA 算子。

#### 4.1 允许的因果顺序

```text
输入与本研究自己的状态
→ P 生成第 r 轮 proposal，先追加写入并封存该轮请求
→ R 仅验证本轮固定 proposals，产生本轮 committed IDs
→ 用这些已产生 IDs 更新 P/R 自己的状态，进入第 r+1 轮
→ 完整 H2 预测及整条 tape 封存
→ 独立启动原生 L
```

允许在 H2 预测阶段自适应构造整条 tape：后轮 proposer 可以依赖 H2 自己先前产生的 committed IDs。不能要求一次无 target 反馈的 draft 自回归 tape 天然等于 live proposal 流；两者不是同一过程。正式 live 从始至终在完整预测文件封存后执行。

#### 4.2 tape 和事件契约

实现 append-only tape；每轮至少包含 run/task/rep、round index、之前已提交 ID 数及 prefix hash、pending token、proposal IDs、positions、sequence IDs、logits mask、有效 target/draft 配置、previous-event hash、生成及验证事件序号。P request／response 的 hash 必须在 R 本轮 decode 前产生。

R 根据自己计算出的 pending token 和 prefix 验证 tape 的对应字段；不能以 tape 中的“预期 committed ID”代替采样。未来轮的完整 prefix、预测答案和 reference 数组放在单独审计文件，不能作为 R 的计算输入。严格按轮顺序读 tape，禁止未来状态 look-ahead。

保留每次 target decode 的逻辑输入、实际物理分组／graph 输出维度、logits 索引、采样后的 target ID、proposal acceptance、correction/bonus、KV 操作、终止条件及 native committed IDs。三 token 验证块在 UB2 下可能分为 `[2,1]`；须记录实际图与输出 mask，不能把这一分组写成所有轮的假设。

同时保存 logits 的完整字节 hash、raw top-1/top-2 及 proposal score、sampler 选中 ID、sampler 配置与历史摘要。原始分数和实际采样决定分开。若不公开全部 logits，明确可复算内容及其限制。

在 `R_ONLY` 模式中使用 fresh target context，仅从已封存 tape 重放，不加载 draft、不启动 P、不读取预测／reference／live 答案。该模式必须产生自己的完整 committed-ID 数组，作为真实的拆分资格检查。

### 5. 新 reserved 暴露审计与固定选样

在任何 V2 模型推理前完成全仓库、上述未合并 PR、主机相关目录和归档成员的暴露审计。包括旧 RTX30、历史 CUDA/106、旧 B570 prediction reserved、M4/358H 执行结果、PR #41 的全部新 B570 reserved，以及所有已生成 target-only/proposal/logit/live 输出。状态不明的任务保守排除。

**不能直接沿用 V1 的 24-task reserved 名单。**目前已知 V1 名单中的 `/36,/74,/83,/84,/153` 已在 PR #41 被曝光。PR #41 还使 V1 的 61-task eligible pool 中共 11 个任务曝光；仅扣除此项后暂为 50 个，完整重新审计可能进一步减少。PR 未合并不意味着其输出未曝光。

不要机械复制 V1 audit 的目录跳过规则：V2 必须审计 V1 的已执行 discovery、工程和延迟记录，以及分片归档的逻辑成员。纯输入清单、eligible universe、明确标记 `NOT_REACHED` 且确无模型输出的 V1 reserved 列表本身不算结果曝光。对每种分类保留机器可读理由；不能为了凑够 24 个降低排除规则。

从 HumanEval 164-task universe 中的合格池选恰好 24 个。固定盐：

```text
RTX_INDEPENDENT_PROPOSAL_REPLAY_V2|reserved|20261001|
```

以 `SHA256((salt + full_task_id).encode('utf-8')).hexdigest()` 升序选择前 24 个，hash 相同以完整 task ID 排序。冻结全集、排除理由、扫描范围／异常、可选池、排序键、24 ID、完整输入 hash。可读取输入和做 tokenizer-only 检查，不得提前对 reserved 做模型 forward、target-only、draft/proposal、logit、R0 或 live。

池不足 24 或关键证据不可审计时为 `RESERVED_POOL_BLOCKED`。先保留已做工程工作并报告；不得按结果挑题、从已知有利任务补足或悄悄换数据集。

### 6. 暴露工程阶段：实现和资格

先提交工程计划与首次源码，然后在已暴露任务和明确标记的非 HumanEval 合成输入上完成构建与调试。全部编译失败、运行异常和修复记录保留，不混入正式分母。

至少完成：

1. **原生 reference 前端等价。**在旧 RTX 固定 30 个任务上各三次，分别新执行原始 CLI UB1 reference 和 R 的 target-only UB1 reference 模式，合计 180 次工程执行；完整数组必须 90/90 相等。旧参考数组可用于额外回归比较，但不能替代这两个新执行条件。此检查验证 H2 新前端的输入、tokenization、prefill 和采样契约，不要求 H2 batched 轨迹等于 reference。
2. **P/R 因果隔离。**源码审计加进程／文件访问记录，证明 P 没有 target 模型／答案输入，R_ONLY 没有 draft 模型／未来 committed 答案输入；预测阶段没有启动原生 L。冻结数据 allowlist、命令模板和输出目录规则。
3. **状态及数值路径。**在暴露任务上检查原始与新前端的实际 prompt IDs、第一 target token、draft proposal、target batch／图分组、logits 行和 KV rollback。必要时做暴露输入的诊断 observer，但保持正式 L 独立。不能靠文本相等或 UB 名称替代这一步。
4. **真实端点覆盖。**用固定合成输入真实触发包含 EOG 的提前终止和恰好 128 已提交 ID 的 cap；对 CLI reference、CLI live、H2、R_ONLY 都保留实际执行。初始探针不触发时只能在工程阶段记录并修订，最终探针和通过记录必须先于 discovery freeze。不得把只有 cap 参数但未触发 cap 当作已覆盖。
5. **分支覆盖。**工程 fixtures 覆盖实际 proposal 长度 0/1/2、首次拒绝、接受后纠正、全部接受后 bonus、接近 cap、EOG、无效 suffix 删除。fixture 只能用暴露输入与新生成的工程状态，并明确区分自然运行与人为构造测试。
6. **负例验证。**在独立临时副本破坏 tape hash/轮次、输入／任务关联、committed-ID 事件、future-prefix 或不允许的文件依赖；独立 verifier 必须拒绝，且不修改正式证据。

工程阶段允许修复，但所有修订透明。完成资格后锁定唯一 H2；本研究没有 H3，也不在 formal 后更换 model、k、ubatch、采样、prompt template 或状态策略。

### 7. 冻结 discovery，重新执行 H2 筛选

固定 discovery 仍为 12 个已暴露任务：

```text
HumanEval/64, /106, /119, /128, /129,
HumanEval/3, /10, /19, /20, /28, /32, /44
```

每个三次，每次分别新执行：

1. H2 的 P→R 预测，生成独立 tape 和完整数组；
2. fresh R_ONLY，重放该次 tape，得到自己的完整数组；
3. 原始 CLI 的 RTX_BATCHED_K2 live。

共 `12×3×3=108` 次完整工程／discovery 条件执行，P 的每轮调用另外计数。不得用 V1 的 36 条 live 数组填入新 discovery 的比较；它们只可用于事后工程回归。

在执行这批固定筛选前，commit + push discovery protocol、唯一 H2 源码／二进制／资产 manifest、工程资格、顺序、36/36 门槛和失败规则，保留 remote acknowledgement。

入选条件：H2/live **36/36** 完整 ID 相等；H2/R_ONLY **36/36** 完整 ID 相等；三个条件在任务内重复稳定；所有设备、输入、状态和事件资格有效。分别报告两个 36 对，不合并成“72 个独立样本”。

科学错配继续完成全部 discovery 108 次并报告首分歧；操作失败立即保留并停止，不替换运行。门槛未通过为 `DISCOVERY_NOT_QUALIFIED`，reserved 0 次。筛选之后不调参修补 V2；后续修改须新研究编号、保留本次失败，并在任何新 reserved forward 前重新协议化。

### 8. 三个远程冻结检查点与正式执行

只有 discovery 全部通过才能进入以下阶段。每次 checkpoint 都需完整 Git SHA、UTC、remote ref acknowledgement、文件 SHA256；仅有本机 mtime、commit message 或自报时间不够。Git ancestry 证明内容关系，不等于独立服务器时间证明，报告二者的界限。

**F0：discovery 冻结。**对应第 7 节，在固定筛选前。

**F1：假设和 reserved 冻结。**在任何 reserved 模型推理前，commit + push 唯一 H2 算法、源／二进制／资产／环境 manifest、重新审计所得 24 ID、完整 prompt/tokenizer 契约、三次重复、正式日程、端点、统计、失败规则及 independent verifier。对全部 24 输入做输入层 hash 验证，不做模型 forward。

F1 后按 task selection rank、repetition 1→3 固定顺序，每个 task×rep 执行：

- `REFERENCE_UB1`：原始 CLI target-only，一次新运行；
- `H2_P_R`：一次新 P→R 完整预测及 tape 生成；
- `R_ONLY`：一次 fresh target-only tape replay。

合计 `24×3×3=216` 次 pre-live 完整条件执行。其中 reference 与 H2 是未来主比较的输入，R_ONLY 是拆分资格，不是另一组独立提示词。P 的逐轮调用和失败另行完整计数。

比较 H2/R_ONLY 完整数组；核对同一条件的三次重复稳定、端点及全部身份。任何 H2/R_ONLY 错配为 `REPLAY_QUALIFICATION_FAILED`，重复不稳定为 `REPEAT_INSTABILITY`，操作／身份异常为 `OPERATIONAL_FAILURE`；保存全记录，在 live 前停止。reference/predictor 不相等是合法预测结果，不能作为换任务理由。

**F2：完整预测文件和 tape 冻结。**216 次成功完成后，生成不可覆盖的 72-row prediction 文件。每行包括 task/rep、输入与资产身份、完整 reference/H2/R_ONLY 数组及各数组 hash、tape hash、各运行 ID、预测的 reference 相等分类和首分歧。统一数组 digest 为 UTF-8 编码的 `json.dumps(ids,separators=(',',':'))` 字节 SHA256；明确文件 digest 与数组 digest 不同。

封存全部 tape、native events 和审计日志；提交完整 manifest、prediction 文件及足以复算预测的内容，commit + push 并核对远程精确内容和 acknowledgement。预测必须只包含已有 pre-live 输出；不能只提交空文件、72 条 hash 而不保存数组，或在 live 后补数组内容。大型文件采用内容寻址分片，并在首个 live 前确认所有被引用预测内容已可取回和验 hash。

**F2 的 remote acknowledgement 必须早于首个 reserved L 进程启动。**以一个显式状态机／sentinel 阻止提前启动 live；任何违例为 `PROVENANCE_INVALID`，不得称 prospective。

F2 后执行 72 次新原生 `RTX_BATCHED_K2`：24 tasks × 3。每次 fresh process/context，从冻结输入自行生成 proposals，不导入 H2 tape。科学错配继续完成全部 72 次；操作失败停在真实日程前缀，保存所有已完成、失败及在途记录，无选择性替换、重启或挑选最匹配重复。

**基础正式条件执行总量为 288 次**：72 reference + 72 H2 P/R + 72 R_ONLY + 72 live。两个阶段之间不能共享进程／KV；H2 内的逐轮 P/R 调用属于该次执行的子事件，不重复计算为额外正式样本。另有 reference 工程 180 次、discovery 108 次及全部 R0/调试/负例；分别计数，不与正式结果混合。

### 9. 主终点、分歧性与结果分类

主终点是 **72 个 H2/live 完整 generated-ID 数组比较**，同时报告 24 个不同提示词。逐 token 比较直到 inclusive EOG/128 cap；长度不同即不相等。记录全部首分歧的零基位置和两侧 ID，不以文本、checksum 单独相等或部分前缀代替完整数组比较。

报告：H2/live、R_ONLY/live、reference/live、H2/R_ONLY，均分别为同一组 72 对；每项同时给 prompt-level counts、repeat stability、参考分歧提示词数及其三次结果。重复和轮内事件不能当作独立提示词。

| 状态 | 判定 |
|---|---|
| `PROSPECTIVE_REPLAY_MATCH_DISCRIMINATING` | 72/72 H2/live，拆分和身份资格全部通过，且至少一个 actual reference-divergent 的不同 reserved 提示词被正确预测 |
| `PROSPECTIVE_REPLAY_MATCH_NONDISCRIMINATING` | 72/72 H2/live，但全部 actual live 轨迹与 reference 相等 |
| `PROSPECTIVE_REPLAY_MISMATCH` | 全部正式 live 有效完成，但 H2/live <72/72；完整披露错误 |
| `DISCOVERY_NOT_QUALIFIED` | discovery 未达到预先固定门槛；reserved 0 次 |
| `INDEPENDENCE_NOT_ESTABLISHED` | 无法满足 P/R/L 的输入、执行和数据依赖隔离；不进入 reserved |
| `HARNESS_NOT_QUALIFIED` | 工程前端或原生输出契约未过资格 |
| `REPLAY_QUALIFICATION_FAILED` / `REPEAT_INSTABILITY` | pre-live 资格失败，停止在 live 前 |
| `RESERVED_POOL_BLOCKED` | 未曝光任务或审计资格不足 |
| `INCOMPLETE_OPERATIONAL_FAILURE` / `PROVENANCE_INVALID` | 正式执行不完整、身份异常或冻结顺序失效；不报告有效 reserved accuracy |

72/72 是所选有限样本的全中门槛，不是分布层面的普适性证明。零 reference 分歧的结果不能通过追加新任务变成有区分力结果。

即使 all-match，也只能写该独立程序在所测 RTX 栈上的 prospective replication；不能写 target-only sufficiency、B570/CUDA 共因、唯一 kernel、架构内在失效或 batched 性能收益。若 P/R 分离程序重现了原生算法的大部分状态机，须明确这一点，不能将软件复现升级为独立数值机制发现。

### 10. 独立验证与完整证据包

在 F1 前冻结独立 verifier。它不导入执行 runner 的 comparator、aggregator 或状态机来宣布相等；自行读取原始 native commit events、tape 和 manifests。

至少验证：

- 输入 hash、tokenization 记录、模型/源码/二进制/命令、实际 CUDA0 与全层 offload、fresh context、inclusive EOG/cap、连续 commit indices、任务／重复／条件覆盖和所有 attempts。
- 全部 tape hash-chain、P 响应早于对应 R decode、prefix/positions 与过去状态一致；P/R_ONLY 的模型加载／文件访问隔离；不把声明性标签本身当作独立性证据。
- H2/R_ONLY 的完整输出与接受／纠正／bonus 事件；可复算 sampler decision，明确缺少完整 logits 时的限制。
- F0/F1/F2 远程收据、源文件在冻结 commit 的实际 Git membership、预测及 tape 在 F2 的精确字节、首个 live 启动时间、各次 source head 和无重叠的执行区间。
- 主结果所有数组逐元素比较、首分歧、reference 分歧、repeat stability 和严格结果分类。不得把 stop 情况打印成 72/72 或科学“成功”。

独立负例包括：改一条 committed ID、删除 native event、改 task/rep、改 tape proposal/hash-chain、伪造提前 live、把 reference/live 答案混入 R 输入。验证器必须拒绝，fixture 与正式目录分离。

构造内容寻址归档、完整每文件长度/SHA256 manifest 和 frozen source；按仓库政策排除权重、runtime 二进制、缓存及凭据，保留其身份和本机可选重哈希接口。省略字节只能在原主机验 hash，离线验证不能宣称已认证这些省略内容。

**交付前必须在全新目录完整重建并离线验证归档**，不需要 GPU。若使用分片，验证每片、顺序、合并后 SHA256、全部文件及 verifier；不得只验归档 index。用 `python -B` 或其他方式禁止 bytecode cache 污染严格 inventory，保留复建报告。内容 head、归档 head、最终 closeout head 分开记录，避免自引用 digest。

额外提供匿名审核子包，包含输入/任务的可审计映射、完整数组、必要 tape／事件、冻结 digest 及标准库复算入口。匿名化时去除主机用户名、个人路径、Git 作者和非必要精确时间；不要覆盖原始封存。若匿名化去除了外部冻结时间证明，清楚说明匿名包可以复算内容而不能独立证明原始 remote chronology。

### 11. 最终交付与 draft PR

完成并推送一个新的 draft PR，标题围绕最终实际结果，而不是预设“成功迁移”。不要修改／自动 merge #40/#41/#42，不修改论文；论文整合等待作者审阅本研究。

至少包含：

```text
PREREGISTRATION.md + protocol.json
EXPOSURE_AUDIT.json + RESERVED_SET.json
H2_DESIGN.md + 独立性/共享实现对照 + 源码/patch/构建入口
BUILD_IDENTITY.json + R0/HARNESS_QUALIFICATION 记录
DISCOVERY_REPORT.md/json + 全部新 discovery 记录
F0/F1/F2 冻结 manifest 与 remote 收据
RESERVED_PREDICTIONS.json + 全部 tape（如到达 F2）
FORMAL_REPORT.md/json + 逐任务比较（如到达 live）
独立 verifier + 负例结果 + REPRODUCTION.md
完整原始内容寻址归档 + 干净目录离线复建验证结果
匿名复算子包 + 明确的匿名化限制
CLOSEOUT.md/json + 手工审查用下一步建议
```

stop 时只生成真实到达的检查点，后续标 `NOT_REACHED`；不伪造缺失文件或时间。不要因失败删除有信息的执行记录。

最终向作者用中文报告：starting/final HEAD、branch/PR、H2 架构与共享代码范围、暴露池与重选24任务、资格及两个 discovery 36 对、正式四条件各次计数、72/72 是否达到、reference-divergent 不同提示词数、错配首位置／ID、三个 freeze 与 first live 的 SHA/UTC 顺序、独立验证／负例／完整验包、状态分类、保留限制，以及是否已具备稿件整合条件。

本次交付的结束条件是完整、可审核的 V2 结果或严格记录的停止原因；不要求阳性，也不以再次重跑 V1 H1 代替新增 H2 实现。

