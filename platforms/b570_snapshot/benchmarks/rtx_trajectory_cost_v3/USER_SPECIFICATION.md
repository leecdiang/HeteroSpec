# RTX 联合研究完整 Prompt：V3 轨迹预测器比较 + 匹配资格与成本

日期：2026-10-01（北京时间）。R1：仓库状态与基线已在 #46 集成后更新，实验设计未变。仓库：`leecdiang/HeteroSpec`。平台：Windows + RTX 5070 Ti Laptop / CUDA0。

把本文件完整交给 RTX 平台执行代理。它覆盖协议准备、工程核验、冻结、A/B 正式执行、独立验证、归档和 Draft PR。两项研究在一台主机上顺序完成，分别报告；不要求 A 成功才能做 B。

**首次运行模式：`PREPARE_ONLY`。**按作者此前决定，先把两份协议和工程实现做成可审核的冻结交付；此阶段允许已曝光任务上的工程推理，禁止任何新 reserved 模型 forward。协议审核后，作者提供 `EXECUTE_FROZEN` 和所审核的完整 SHA，再继续本文件的正式执行部分。后续 F2 预测封存与 B 开始前复核由程序执行，无须每个 checkpoint 再请求一次确认。仅收到本文件不能自行认定已经获得 `EXECUTE_FROZEN` 指令。

## 1. 任务、授权和不可变边界

你负责活动 `RTX_TRAJECTORY_AND_MATCHED_COST_V3`，包含两项研究：

- **A：`RTX_TRAJECTORY_SUFFICIENCY_V3`。**在新的 reserved 集合上，前瞻比较固定 target-only UB2 候选与既有 H2/R_ONLY replay 候选对原生 batched live 完整轨迹的预测能力。
- **B：`RTX_MATCHED_QUALIFICATION_COST_V2`。**在同一冻结计时构建、工作负载和测量边界下，新执行 target-only reference、batched speculative、serialized speculative，联合判断 direct-ID 资格与实际成本。

请实际实现、构建、检查和交付，不能只写方案。阳性结果不是交付条件；候选错配和路径资格失败都是有效研究结果。工程能力不足、冻结失败或操作异常必须交付可审计的阻塞记录，不能填充或模拟实验结果。

允许新增本研究 runner、observer、timer、协议、verifier、分析和证据包，允许在新分支提交、推送和创建或更新本研究 Draft PR。不要自动 merge、创建 scientific tag、发布 release、投稿，或修改论文。B570、358H、M4 本轮均不新增执行。

旧模型输出、协议、归档、数值宏、图、稿件、旧成品和科学冻结 tag 保持原样。旧研究脚本采用只读复用或有来源说明的复制；需要改变行为时在新目录中实施。不要为满足旧 validator 修改历史材料，也不要把旧原始数据补进新正式分母。

## 2. 精确基线和必须阅读的入口

仓库状态已于 2026-10-01 完成 reconciliation。先阅读 `paper/mlsys2027/HANDOVER_CURRENT.md` 与 `REPO_STATUS.md`；旧 versioned author handover/stopping rule 的 Draft/unmerged 描述是交付当时的历史，不代表实时 main。

| 对象 | 核对后的身份和状态 |
|---|---|
| main 最近一次稿件集成锚点 | `361cb43a67f7fd9bfae95de4cdf7e816c46bbe90`，PR #46；已完整包含 v0.8.6；后续状态维护提交可在它之后 |
| PR #44 | delivery HEAD `dccbbb53e1f91d3239e2075336100795dd6daa1e`；原 main merge `30673fd8153b30681e959ea36a10b23ef89a990e` |
| PR #45 | delivery HEAD `494a5ca4fe62534b032b37d01652c3f88e0d16e1`；原 stacked merge `30635a680a93a2bd145361861b6c563f2f485fca`，现在也是 main 的祖先 |
| v0.8.6 TeX source/content | `da8d5739eb108de7f35d3a3cfbd954d42462f2e0`；原交付身份保持不变 |
| 科学 author-freeze tag | `mlsys2027-v0.8-author-freeze` 仍解析至 `1d3b556c93b477680788dfd1eb0737dfe9eee28c` |

集成锚点不等于永远不变的 main HEAD。执行前 fetch，解析实际 `origin/main`，确认上述 v0.8.6 集成锚点是其祖先，并检查后续差异。记录实际 starting/base SHA，而不是把此表中的锚点当作当前 checkout。

从最新 main 建立干净、独立 worktree，建议分支 `experiment/rtx-trajectory-and-matched-cost-v3`。确认既有 RTX V1、H2 V2 和 v0.8.6 都已存在；不需要再合入旧论文分支。保留精确只读交付 ref 作来源核对，不在实验分支修改稿件。记录原作者 checkout HEAD 与 dirty 状态，不在原 checkout 运行或覆盖研究产物。

至少阅读以下真实入口，记录文件 SHA 和阅读范围；目录中的状态字段与实际 closeout、receipt 分开理解：

- `benchmarks/rtx_transfer_latency_v1/`：`protocol.json`、`PREREGISTRATION.md`、`asset_identity.json`、`runtime_freeze.json`、`timer_build_manifest.json`、`timer.patch`、`prediction/REPORT.{json,md}`、`latency/REPORT.{json,md}`、`CLOSEOUT.{json,md}`、`REPRODUCTION.md`。
- `scripts/platform/rtx_transfer_latency_v1/`：`native.py`、`study.py`、`build_timer.py`、`audit.py`、`verify_common.py`、`verify_prediction.py`、`verify_latency.py`、`verify_provenance.py`、`archive.py`。
- `benchmarks/rtx_independent_proposal_replay_v2/`：`protocol.json`、`PREREGISTRATION.md`、`H2_DESIGN.md`、`INPUT_CONTRACT.json`、`EFFECTIVE_CONFIGURATION.json`、`COMMAND_TEMPLATES.json`、`BUILD_IDENTITY.json`、`ASSET_ENVIRONMENT_BEFORE.json`、`RESERVED_SET.json`、工程资格、`FORMAL_REPORT.{json,md}`、`CLOSEOUT.{json,md}`、`REPRODUCTION.md`、F0/F1/F2 manifests 和 remote receipts。
- `scripts/platform/rtx_independent_proposal_replay_v2/`：`worker.cpp`、`engine.py`、`phases.py`、`prepare.py`、`qualification.py`、`engineering_extra.py`、`freeze.py`、`identity.py`、`input_contract.py`、`verify.py`、`package.py`、`offline.py`、`reconstruct_parts.py`。
- 原 RTX direct-ID v2 的 capture contract、资产/构建身份、完整任务清单和正式报告；B570、M4、358H 的已执行任务、输出和 exposure inventories，以及相关归档成员。
- v0.8.6 正文 Section 5、limitations、Appendix M/N/P，只用于理解已有结论与边界。
- `docs/data_policy.md`、`docs/experiment_protocol.md`、`docs/reproduction.md` 与适用的 `AGENTS.md`；pinned llama.cpp 的 CLI/server、draft-simple、sampler、decode 和 KV rollback 源码。

建议新增以下目录，旧目录不改：

```text
benchmarks/rtx_trajectory_cost_v3/
    A_trajectory/
    B_matched_cost/
scripts/platform/rtx_trajectory_cost_v3/
artifacts/rtx_trajectory_sufficiency_v3/
artifacts/rtx_matched_qualification_cost_v2/
```

## 3. 历史事实及本研究能回答什么

保留以下历史事实，不能用本轮结果覆盖：

- RTX V1 的 target-only UB2 H1 discovery 为 **24/36**；`/64,/106,/119,/128` 四个任务各三次不匹配。没有选中 H1，H2 当时未执行，reserved **0 次**。
- RTX H2 V2：H2/live、R_ONLY/live、H2/R_ONLY 均 **72/72**，UB1 reference/live 为 **60/72**；程序分离，但共享 llama.cpp/GGML/CUDA 数值库。V2 reserved 集合没有 target-only UB2 competitor。
- 原 RTX 新计时研究：serialized/reference **90/90**、180 runs；`target/serialized = 0.6458157742698285`，原 CI `[0.629802205379344, 0.6598843928244866]`。它只有两个 matched conditions，本轮不能直接沿用其资格或数值。

A 不再采用“先筛选 H1，失败才选择 H2”的 discovery 决策树。两个候选都已由已有工作指定；**本轮直接比较两个固定候选，H1 错配不能阻止比较。**工程数据可证明实现和输入契约，但不重新挑选有利算法、任务或候选。禁止 H3 搜索。

A 的解释限于：这个 target-only UB2 候选和这个 proposal-conditioned replay 候选在冻结集合上的预测能力。UB2 失败、replay 成功，排除的是这个简单候选，不能证明 proposal/history 在所有可能算法中必要。UB2 成功也不能抹掉已知 H1 discovery 失败，不能宣称普遍跨 backend transfer、唯一数值原因或最小充分状态。

`n_ubatch=2` 是物理最大 micro-batch 容量；target-only 逐 token 生成不因此变成双 token speculative verification。它可能改变 prefill 和 KV 数值历史。本研究比较完整执行路径，不把 UB 参数差异解释为只改变某一个 verification block。

B 的 endpoint 是所冻结、含仪器和日志的 post-prefill request latency；不等于部署 throughput、全请求加载延迟或能耗。BLOCKED 路径的时间仅作诊断，不能形成 lossless speedup 结论。

## 4. 共同计算栈、输入和输出契约

优先保持已有 RTX 条件。路径位置从当前主机解析，不把旧绝对路径当作必然存在的文件。

| 项目 | 冻结要求 |
|---|---|
| GPU | RTX 5070 Ti Laptop，显式 CUDA0，记录型号、设备 ID、VRAM、驱动和功率模式 |
| 上游 | llama.cpp b10839 / `0cae43063cf15170e91a2ff4d034da0ecef4a1b2` |
| target | Qwen3-8B Q8_0；SHA256 `408b955510e196121c1c375201744783b5c9a43c7956d73fc78df54c66e883d6` |
| draft | Qwen3-0.6B Q8_0；SHA256 `9465e63a22add5354d9bb4b99e90117043c7124007664907259bd16d043bb031` |
| 数据 | 原 HumanEval 文件；SHA256 `b796127e635a67f93fb35c04f4cb03cf06f38c8072ee7cee8833d7bee06979ef` |
| target sampler | greedy；seed 123、temp 0、top-k 0、top-p 1、min-p 0；完整有效 sampler chain 另外冻结 |
| speculation | 原 draft-simple，max proposal width 2、min 0；冻结实际 draft sampler、p_min、rollback，不把 target seed 当 draft seed |
| context | ctx 4096、logical batch 2048、一个 sequence；有效线程数、K/V 类型、kv_unified 等取既有契约并显式记录 |
| attention/放置 | FA off，target 37/37、draft 29/29 层 CUDA0 offload，实际日志确认 |
| 状态 | 每次 fresh process/context；禁止跨运行 prompt、KV、sampler 或 proposal 缓存 |
| 输出端点 | 首 128 个原生已提交 generated IDs；更早 EOG 时包含第一个 EOG ID 并停止 |

沿用已有完整文本模板、Qwen3 no-tools formatting、`enable_thinking=false`、native CLI 对末尾一个 LF 的移除规则。冻结原输入字节、format 后实际字节、prompt token IDs 和各自 hashes。输入模板为：

```text
Complete the following Python function. Return only the completed Python code, without Markdown fences.

{HumanEval 原始 prompt}
```

输出 capture 必须直接读取 native committed-ID 事件，排除 prompt 与未提交 proposals。长度不同即不相等。不能用 detokenized 文本再 tokenize 判 exact，不能只保留 digest 或成功数量。

数组 digest 契约固定为 UTF-8 `json.dumps(ids, separators=(',', ':'))` 字节的 SHA256，文件 digest 独立记录。保存首分歧的零基位置、左右 ID（长度差用 null）、终止原因、输出长度。

记录 OS build、GPU driver/CUDA runtime、相关 DLL、compiler、构建选项、源/patch/executable/模型/数据 hash、所有有效环境覆盖变量和运行命令。主机设置、GHelper 模式、AC 供电、风扇/功率配置固定；不在正式执行间升级驱动或更改配置。环境变化意味着新条件，历史资格不能继承。

## 5. 曝光审计与 A/B 的固定工作负载

在本轮任何模型推理前完成新的 exposure audit；输入层检查和 tokenizer-only 不算模型 forward。审计整个仓库、相关 PR/分支、主机相关 checkout/work/run/archive 目录、分片重建后的逻辑成员，包括 target-only、draft、proposal、logit、replay 和 live 输出。不可访问的相关材料与扫描异常要列出，未知/模糊任务保守排除；不能为了凑数降低规则。

旧 V2 清单的 eligible pool 是 50 个，已经选走并执行 24 个；按那份旧清单只剩 26 个。**这不是当前仍有 26 个干净任务的保证。**后续推理和归档可能进一步减少。V1 的未执行 reserved 名单本身不构成输出曝光，但其中后来被别的研究执行过的任务必须排除。纯 universe/input 清单与真实输出分开分类，并保留理由。

A 从 HumanEval 164-task universe 的当前 eligible pool 选恰好 24 个。固定盐：

```text
RTX_TRAJECTORY_SUFFICIENCY_V3|reserved|20261001|
```

以 `SHA256((salt + full_task_id).encode('utf-8')).hexdigest()` 升序，hash 相同按 full task ID 排序，取前 24 个。不根据输入长短、旧匹配率或预期 divergence 挑题。冻结完整全集、排除理由、审计范围、可选池、排序键、24 IDs、输入 hashes；选择后不替换。

**正常模式：B 使用 A 所选的同一 24 IDs，各三次，但全部为另外的新运行。**B 的名单、随机顺序、条件和统计在 A 任何 reserved forward 前冻结，不能看 A 结果后改变。B 执行时这些输出已曝光；明确披露它是预先选定集合上的成本研究，不声称又获得一组未曝光预测样本。

**预先规定的准备期备用模式：**如果审计完整且 eligible pool 不足 24，A 为 `RESERVED_POOL_BLOCKED`、reserved 0；不要换数据集或减小 A 的分母。B 可继续准备为 B-only，使用既有 RTX direct-ID/V1 cost 固定 30 IDs（三次），从原协议读取并将全部 IDs 写入本轮协议。这个分支只由准备期池数量决定，在任何正式数据前冻结；不是根据 A 结果改变 B workload。如果审计不完整或存在不可消除的身份/数据风险，交付阻塞，不能擅自启用备用集合来掩盖它。

首次协议交付须明确显示最终是哪一种模式：`A24_B24` 或 `A_BLOCKED_B30`。作者审核的是这一确切模式与名单。已选定 24 个但 A 后来错配/操作失败时，B 仍使用这 24 个，不切到 30 个。

## 6. 工程阶段：复用已有实现，验证新增部分

仅使用已曝光任务和明确标记的非 HumanEval 合成输入。固定 exposed engineering 集为旧 12 IDs：`/64,/106,/119,/128,/129,/3,/10,/19,/20,/28,/32,/44`，每个三次；全部加 `HumanEval/` 前缀。另列出 EOG/cap/状态 fixtures；不得从剩余 eligible pool 取 discovery 数据。

优先复用 V2 的 `P.exe`、`R.exe`、`worker.cpp`、`engine.py`、输入契约、tape 和 capture。对兼容路径和新目录作适配，但不随意改数值逻辑。优先复用 V1 timer patch，在新目录扩展三条件支持。旧构建产物可以在主机读取和重哈希，不提交权重或二进制到 Git。

完成以下核验，原始记录与失败尝试均保留：

1. **A 原生输出与 reference 契约。**原 CLI UB1 与 R 的 reference UB1 在固定 12×3 上新执行，完整数组 36/36 相等；检查实际 prompt IDs、sampler、EOG/cap 和设备。旧数组只用于额外回归，不替代新核验。
2. **A P/R 与 replay 隔离。**P 只加载 draft；R/R_ONLY 只加载 target。R_ONLY 不启动 P，不读取 reference/prediction/live 数组，只顺序消费新 H2 生成的 tape。新 H2/R_ONLY 在固定 12×3 上 36/36 相等，检查 pending token、prefix、position、acceptance/correction/bonus、KV rollback 和终止。
3. **A 候选工程观察。**在固定曝光集合保留 target-only UB2、H2 和原生 live 的比较，用于查实现与记录能力。UB2/live 错配不构成资格失败；H2/live 错配也不能触发改候选/挑任务。发现明确实现缺陷可在准备期修复并保存差异；不能以“让预测全中”为准则反复搜索。
4. **B 三条件 timer 语义核验。**固定 12×3×3 个条件，每条件分别执行原始 CLI 和新增 timer CLI，基础 216 次工程执行；逐条件原始/timer 完整数组均 36/36 相等。batched 与 reference 不相等是合法的，不能把这种错配算作 timer 改变语义。保留 patch 和证明 sampler/生成规则未被改变的源码检查。确实无法保持语义，则报告 `TIMER_SEMANTICS_NOT_ESTABLISHED`，不进入 B 正式执行。
5. **实际 decode 观察。**沿用上游 `LLAMA_BATCH_DEBUG=1` 的原生 batch 记录与 V2 metadata-only graph callback；核对 on/off 观察器的输出语义。记录 prefill/generation、逻辑 decode token IDs/positions/sequence/logits mask、实际物理分组和图输出维度。未观测到的量标明缺失，不能从 UB2 名称推导。工程 observer 记录不能冒充正式运行的事件。
6. **端点与状态分支。**实际运行覆盖 inclusive EOG 和恰好 128 committed IDs 的 cap；检查 proposal 长度 0/1/2、rejection、correction、bonus、rollback。自然运行和构造 fixture 分开记录。不能只检查 cap 参数。
7. **独立 verifier 负例。**在临时证据副本注入至少：ID 改动、数组截断/漏 EOG、task/rep 交换、重复 run、tape hash/轮次损坏、未来答案字段、未达到 F2 提前启动 A live/B、timer 缺失或反向区间、错误统计方向、把 BLOCKED 写为 speedup。独立 verifier 必须拒绝；正式证据不被改动。

工程记录可在两项核验间引用同一真实运行，但须有准确 run ID 与条件身份；正式 A/B 观测绝不共享。没有重新选择预测器的 discovery 阶段，没有新增 36/36 H1 成功门槛。全部构建、调试、编译失败和工程重跑单独计数。

## 7. A 的五个执行条件和数据边界

| 条件 | 执行与允许输入 |
|---|---|
| `A_REFERENCE_UB1` | 原始 common CLI，target-only UB1；只读冻结 prompt |
| `A_TARGET_ONLY_UB2` | 同一原始 CLI，target-only，仅 target `n_ubatch` 从 1 改 2；没有 draft、tape 或 live 输入 |
| `A_H2_P_R` | V2 P→R 算法：P/R 用自己已产生的历史构造 proposal tape 和完整预测；在 live 前完成 |
| `A_R_ONLY` | fresh target-only R，顺序消费对应 H2 sealed tape，独立计算完整 committed IDs；不加载 draft |
| `A_NATIVE_BATCHED_LIVE` | 原始 CLI 自行执行 draft-simple，target/draft UB2；不导入 tape、预测或 proposer 状态 |

R_ONLY 成功不意味着预测生成是 draft-free：其 tape 由 H2 的 P/R 产生。本轮既比较完整 H2 predictor，也保留 R_ONLY 拆分核验；不能只列四个名字而漏算 H2 tape 生成的工作量。

每轮 P request/response 和固定 R request 在 R decode 前持久化，tape append-only、digest-linked。R 根据自己的 pending token/prefix 检查输入，而不是接收预期 committed 答案。未来 prefix、参考答案、预测数组置于单独审计目录，不是 R 的输入。共享数值 DLL 的事实与独立程序的边界继续披露。

正式原生路径完整命令从已有 V1/V2模板派生，不自行增加影响数值的默认参数。特别核对 draft UB、draft confidence/sampler、effective n_batch、缓存类型、threads、context 和 observer 环境。保留实际加载模块与完整命令。

## 8. B 的三条件与 matched timer

三条件都来自**同一个新冻结 timer executable**和相同数值 DLL，不把 A 的原始 CLI 时间拿来补 B：

| 条件 | 配置 | direct-ID comparator |
|---|---|---|
| `B_TARGET_REFERENCE_UB1` | target-only，target UB1 | B 内部参考 |
| `B_BATCHED_K2_UB2` | draft-simple，target UB2、draft UB2，max width 2 | 同 task×rep 的 B reference |
| `B_SERIALIZED_K2_UB1` | 同一 draft-simple，target UB1、draft UB1，max width 2 | 同 task×rep 的 B reference |

在 pinned 原生实现中，`common_base_params_to_speculative()` 复制主参数的 `n_ubatch` 给 draft，因此 `--ubatch-size=1/2` 同时影响 target/draft。这里明确沿用该原生配置，不虚设未提供的独立 draft UB 选项，也不新增分离参数的干预臂。它还作用于 prefill/数值历史，不能称“只干预 target verification”。serialized 的真实物理分组须记录；不要只按名称认定已序列化。其他模型、输入、端点、seed、有效 sampler、设备、线程、log/observer 配置和测量边界一致，条件特有工作如 draft 计算自然计入对应时间。

**主 timer：**原生 QueryPerformanceCounter，记录 start/end ticks 与 frequency。起点在 target 和存在的 draft 初始 prompt prefill 完成并同步后，位于 per-request sampler constructor/seed/reset/prompt acceptance 和生成状态初始化之前。终点在最后 committed ID、必要 target/draft 同步、response/log 工作和 slot release 完成后，model/context 进程销毁前。prefill 期间不可偷算第一 generated token而在 timer 后仅提交；用源码/事件明确首个输出的计算与采样归属。

包含 draft generation、target verification、acceptance/correction/bonus、调度、KV rollback、生成状态管理、必要同步和边界内日志/响应工作。排除模型加载、初始 prefill、进程/model teardown。统一 timer placement 与打印策略，不用 Python 进程 wall time或未审计 `--perf` eval time替代。

保留独立实现的 `std::chrono::steady_clock` 起止记录作为辅助检查；它与 QPC 在 Windows 上可能共享 oscillator，不声称独立硬件时钟。两记录差异阈值固定为 `max(0.020 ms, 0.001 × QPC interval)`。10,000 次空 clock-hook probe 的 p99 要 `<=10 μs`，且 `<1%` 最短合格工程 interval。该探针仅约束时钟调用，不代表完整 instrumentation/logging overhead，也不用于减去正式延迟。

工程期检查三个条件所有终止分支都恰好生成一个 timer record，count/terminal ID 与 native committed 数组一致；包括 EOG、128 cap和 speculation 终止分支。正式执行不另开一套 timing-only runs：**每个 B run 同时产生自己的 ID gate 数据和 timer。**分析时先计算 gate，再解释 timing。

默认主机稳定规则沿用已有研究：B 前至少 120 秒 idle；三次间隔 10 秒样本 GPU utilization <=5%、temperature <=55°C、温度跨度 <=2°C，最多等待 600 秒，未满足则操作阻塞。每次正式运行前固定 2 秒 idle，保留 pre/post device snapshots。工程期如该规则确实不可用，须在首次协议审核前给出理由和完整替代阈值；正式数据开始后不调整。调度不能根据输出、匹配率或耗时决定等待与重跑。

## 9. B 随机日程与统计定义

正常模式 N=24，每个 prompt 三次，形成 72 个 task×rep blocks；每 block 的三条件相邻、顺序随机。六种三条件排列各使用 12 次；将完整排列列表用 `random.Random(2026100103).shuffle()` 一次打乱，按 A selection rank、rep 1→3 分配。冻结整个 schedule.json，不在运行时重新抽签。

备用 B-only 模式 N=30，90 blocks；六排列各 15 次，同一 seed，按既有 30-task protocol 原始顺序、rep 1→3 分配。不得看结果后切换模式。

每个路径 c 对每个 prompt i：

```text
M_i,c = median(该 prompt 在该条件的 3 次原生 interval_ms)
r_i,c = M_i,target / M_i,c
S_c   = exp(mean_i(log(r_i,c)))
```

`S>1` 表示 speculative 条件更快，`S<1` 表示更慢。不能把 ratio direction 反过来，不能先取每 repetition ratio 中位数来替换 ratio of condition medians。

主估计分别为 qualified batched 与 qualified serialized 对 reference 的 S。95% CI 使用 10,000 次 distinct-prompt paired bootstrap，固定 seed `2026100104`，按冻结 prompt 顺序生成索引；两条路径采用同一套 resampling indices。每次抽 N 个 prompt 的整个配对行，重算 GM；2.5%/97.5% 分位用 `(n-1)p` 的线性插值。三次 repetitions 不是三个独立 prompts。

预先规定一个 secondary contrast：只有两条路径都 qualified 且完整 timer 有效时，报告 `GM_i(M_i,batched / M_i,serialized)`，同一 bootstrap；大于 1 表示 serialized 比 batched 快。它是本轮实测，不使用旧 cost ratio。另列三条件逐 prompt 中位 ms、GM、median、输出长度/EOG、candidate faster 的 prompt 数；总体绝对时间 summary 与 ratio estimator 分开。

batched/serialized 任一路径未过 gate，其主 speedup 与 CI 字段设为 null。可以列 raw ms、输出长度、首分歧与诊断说明，但不能对 blocked 路径给出 admissible lossless GM/CI，也不能只保留相等 prompts再称主结果。若另一路径 qualified，仍按完整冻结集合报告它的成本；不把两路径 gate 合成一个分母。

## 10. 首次交付：PREPARE_ONLY 到 F0

完成阅读、曝光审计、工程实现/核验、negative checks与 timer R0。生成 joint protocol、A/B各自 protocol、固定 cohort/schedules、资产/环境/源身份、调用与数据依赖图、有效配置、完整命令、endpoint contract、计数、统计、失败规则和独立 verifier。

F0 之前可以修复工程问题，保留全部变化与尝试；定稿后构建字节与源文件冻结。不要为获得有利结果改 H1/H2、model/k/UB或 prompt。把本文件原样保存为 `USER_SPECIFICATION.md`；解释各规范如何进入机器可读 protocol。

commit + push F0 内容，核对远端完整 SHA、tree/files 和可取回的内容 hashes，保存 remote acknowledgement 与 HTTP server Date（如可取得）。receipt 文件可在后续提交中记录其父内容 commit；不让 manifest/hash 自我循环。Git ancestry、hash 与服务器时间分别说明其证明能力，不能用本地 mtime 冒充独立时间。

提交一个 Draft PR，标题明确“protocol/engineering freeze; reserved not executed”，并交付 `PROTOCOL_REVIEW_PACKET.md`。此时必须有机器可读证明：A reserved model forwards=0、A reserved live=0、B formal runs=0；tokenizer-only、工程 forward 和 P/R 子调用分别计数。

**首次运行到此停止。**所有依赖审核的配置已具体完成，作者能审核精确协议、实现、工程证据和名单。不要停在需要作者猜测的 TODO/FILL 字段；真正阻塞的项目明示 BLOCKED，不编造。

## 11. EXECUTE_FROZEN：F1 与 A pre-live

收到作者对确切 F0 protocol/source SHA 的审核和 `EXECUTE_FROZEN` 指令后，记录审核依据，并逐文件验证执行源、参数、模型、DLL、timer、prompt、cohort/schedule 与所审核版本相同。若准备材料被改动，先重新冻结和审核，不能将授权移用到不同协议。审核不是对科学结果的预先认可。

F1 在任何 reserved 模型 forward 前形成并推送：绑定已审核 source/protocol SHA、实际资产重哈希、完整24名单、输入与 tokenization、四项 pre-live 条件、72/72判据、B已冻结内容、正式顺序和无 live记录。保留远端 acknowledgement。

按 task selection rank、rep 1→3，对每 task×rep 固定执行：

1. `A_REFERENCE_UB1`；
2. `A_TARGET_ONLY_UB2`；
3. `A_H2_P_R`，生成自己的新 tape/完整预测；
4. `A_R_ONLY`，fresh context 重放对应 tape。

共 **24×3×4=288 次完整 pre-live 条件执行**。不能使用旧 V2 tape、V1预测或 B 产生的 proposals。原生 live 进程和 B formal 入口均有 hard guard，F2 尚未有效时不可启动。

完成本阶段后，检查每条件三次重复稳定、输入/设备/端点/身份，以及 H2/R_ONLY 72/72 一致。UB2 与 reference 或 H2不相等是合法预测差异，不作为停机、改候选或换任务理由。

H2/R_ONLY 错配表示 replay component qualification 失败；任何 pre-live repetition instability、无效 capture、操作或身份异常按第14节处理。在已经完成的真实日程内保留所有记录；live尚未开始，不能以未知 live作为依据补修。科学性候选差异与工程完整性失败分开。

## 12. F2：完整预测封存和 A live

pre-live 资格通过后，生成不可覆盖的 `RESERVED_PREDICTIONS.json`，含72个 task×rep rows，每行四个条件的完整数组、数组hash、输入hash、run ID、tapehash、endpoint和预测的reference相等/首分歧。保存逐轮tapes、events及全部必要 raw records，并产生完整 manifest。

F2 内容 commit + push。大型 pre-live证据采用内容寻址分片，**首个 live 前**从远端完整取回所有必需内容，重新拼装并验hash；仅72条hash、空文件或本机未上传数组不构成封存。保存远端精确content SHA/tree、server acknowledgement、取回时间与文件hash。

`F2 remote acknowledgement < first A reserved live process launch`，且早于任何B formal进程。实现状态机/sentinel，日志记录attempt并拒绝违规启动。封存内容之后不能覆盖；后续结果另存。receipt及结果提交可以作为F2的后代，但核验受保护source/预测内容未变。

然后按selection rank、rep1→3执行 **72次** `A_NATIVE_BATCHED_LIVE`。fresh原生CLI自行drafting，不能导入H2 tape。即使UB2或H2错配，仍完成全部有效预定运行。操作失败保留真实前缀，不选择性替换、重启或补齐分母。

A正式基础执行量 **360次**：72 reference +72 target-only UB2 +72 H2 P/R +72 R_ONLY +72 native live。P/R轮内调用另外报告，不能当作新增独立样本。

## 13. A 比较、结果分类与 B 开始

独立计算并逐行公布：UB2/live、H2/live、R_ONLY/live、reference/live、H2/R_ONLY；均为同一72对，同时报告24个不同prompts和prompt级三次全部匹配数。完整数组逐元素比较，不只验hash；报告所有首分歧、长度与repeat stability。

先报告每个candidate自己的matching结果，再报告两者联合关系：

| UB2/live | H2与R_ONLY/live | 可支持的有限结果 |
|---|---|---|
| 72/72 | 两者均72/72 | 两个预定候选都预测成功；数据不能区分是否需要proposal-conditioned输入 |
| <72/72 | 两者均72/72 | 该target-only UB2候选失败，预定replay候选成功；不能推出history必要性 |
| 72/72 | replay未全中 | 该target-only候选全中，replay候选未全中；检查并如实报告replay各项差异 |
| <72/72 | replay未全中 | 两个预定候选都未达全中门槛；不搜索第三个候选 |

每个全中candidate另外区分：存在至少一个actual reference-divergent prompt且被完整预测，才标 `MATCH_DISCRIMINATING`；reference/live全部相等时标 `MATCH_NONDISCRIMINATING`。partial matches也报告其在所有reference-divergent prompts上的完整结果。即使有reference divergence，两candidate都全中也不能证明某个输入必要。零divergence后不得追加或换集合。

若live某条件重复不稳定，保留逐run counts并标明 `LIVE_REPEAT_INSTABILITY`；不能以集合中某个重复代替冻结的一对。有效稳定的360次完成才允许作预定完整有限结论；incomplete和invalid statuses见下一节。

B开始的条件是**曝光顺序安全且自己的工程/冻结有效**，不是A全中：

- 正常：A完成/封存，再idle与资产重哈希，推送B-start receipt，执行冻结的216次B正式运行。
- A在pre-live操作/完整性失败且未到F2：先写不可逆的A终止记录，关闭同集合A继续入口；此后B仍可使用已经冻结的24 IDs。不能B跑完后回头把同集合A补为prospective；新A须新study和新reserved。
- B-only准备期模式：A明确reserved0、不启动A；审核后执行B冻结的30IDs×3×3=270次。
- 共享模型/DLL/device身份异常：相关研究停在真实前缀；不能在变化后的stack继续凑数。

A outcome不改变B条件、schedule、统计或样本量。B scientific mismatch继续完成全部正式三条件。每路径gate分别为72/72（备用模式90/90），并要求对应完整timer/device/input/endpoint与reference repeat checks有效。reference若重复不稳定，B不报告qualified性能。B三条件正式日程完成且记录有效后，由第9节估计量报告qualified路径成本。

## 14. 固定停止、失败和修复规则

程序应分别记录执行完整性、候选matching、reference-compatibility、repeat stability和provenance；不要用一个PASS隐藏不同含义。

| 情形 | 处理 |
|---|---|
| A候选与reference不同 | 合法预测结果，按固定日程继续 |
| A候选与live错配 | 完成有效的预定A live，报告mismatch；B不受科学结果影响 |
| A H2/R_ONLY pre-live错配、repeat instability或capture失败 | 记录真实结果，A不能进入live；不得在reserved上修补候选 |
| B candidate/reference错配 | 全部B日程继续，受影响路径为BLOCKED，主speedup/CI=null |
| B某路径qualified、另一条BLOCKED | 分别报告；qualified路径按完整冻结集合估计成本 |
| identity/device/timer/进程失败或超时 | 停止受影响研究，保留failed/in-flight run及日程前缀；不选择性重跑 |
| 违反冻结/曝光顺序 | `PROVENANCE_INVALID`，不能称有效prospective预测；不删除违例 |
| 日程未完整 | `INCOMPLETE_OPERATIONAL_FAILURE`，不能把计划分母写成实际执行或准确率 |
| A池不足 | 准备期A blocked；仅按预先规定和审核的B-only模式继续 |

正式前锁定每次进程timeout，例如沿用已有runner的确切值并通过工程核验；写入protocol。发生技术失败不允许原地修复后覆盖正式attempt。需要新attempt时另立研究身份，保留旧attempt；已曝光任务不能继续作为新A reserved。此类新研究需要另行协议，不在本prompt中自动启动。

本轮不要求candidate匹配、batched阻塞、serialized合格或成本有利。所有科学分支均是交付结果；不得因未得理想结果扩dataset、增重复、删任务、改timer或追加分析终点。

## 15. 基础计数、运行ledger与独立验证

正常模式的基础正式计数：

| 阶段 | distinct prompts | repetitions | conditions | complete runs |
|---|---:|---:|---:|---:|
| A pre-live | 24 | 3 | 4 | 288 |
| A native live | 24 | 3 | 1 | 72 |
| A合计 | 24 | 3 | 5 | 360 |
| B matched IDs+timing | 24 | 3 | 3 | 216 |
| 联合合计 | 同一24 | 3 | 8个分别执行的条件 | **576** |

备用B-only为30×3×3=270；A reserved0。工程、R0、fixtures、observer on/off、构建失败、负例、P/R子调用单独计数。576不是独立样本数，更不能把多个72对相加称新的独立prompt数。

所有forward/进程进入统一append-only `EXECUTION_LEDGER.jsonl`，含phase、study、run/task/rep/condition、开始/结束UTC与monotonic时间、source/protocol/asset身份、实际command、PID、status、parent/subevent关联。一个run不可重复计入多个正式条件。计划、started、completed-valid、mismatch、failed、not-reached各自可复算。

独立verifier不得导入runner主comparison/aggregation函数。可共享wire schema和digest定义，但要从raw events/arrays/timer/tapes独立重算：

- A：全部数组和首分歧，72行匹配矩阵，24prompt结果，reference divergence，重复稳定，端点，tape顺序与allowed inputs，source/资产、F1/F2 chronology、remote content retrieval。
- B：精确日程/排列平衡、全部新gate pairs、原生timer interval/count/terminal ID、计时边界资格、逐prompt三次median、ratio、GM、bootstrap、qualified/blocked字段约束。
- 联合：A在F2前无live/B；异常A结束后B开始的状态不可逆；pre/post身份；旧受保护文件不变；工程和正式没有互借观测；所有失败记录存在。

## 16. 可移植证据和交付要求

按仓库data policy封存两项独立、内容寻址证据包，另有joint chronology/index。保留完整原生ID数组、stdout/stderr lossless bytes、events、tapes、timers、输入身份、设备快照、源patch、协议、manifest和失败记录。大包可分片，记录逻辑成员hash与完整重建命令。不要只提交汇总json或声称模型推理完成但缺raw。

不提交模型权重、一般build产品、credentials、HF/cache环境。二进制和数据不公开时保留身份与可选主机重哈希入口，明确离线核验能复算哪些结果、不能认证哪些省略资产。作者完整证据与匿名capsule分开；匿名版本保留A预测与B统计可复算内容，脱敏字段不能破坏逻辑关联。绝对路径是provenance，不是复现指令。

至少交付：

```text
USER_SPECIFICATION.md
JOINT_PROTOCOL.json
PROTOCOL_REVIEW_PACKET.md
READ_RECEIPTS.json
EXPOSURE_AUDIT.json + RESERVED_SET.json
INPUT_CONTRACT.json + EFFECTIVE_CONFIGURATION.json
ASSET_IDENTITY.json + ENVIRONMENT.json + BUILD_IDENTITY.json
COMMAND_TEMPLATES.json + EXECUTION_LEDGER.jsonl
ENGINEERING_REPORT.md/json + NEGATIVE_VALIDATION.json
F0/F1/F2_MANIFEST.json + REMOTE_RECEIPT.json（实际达到者）
A_trajectory/protocol.json + RESERVED_PREDICTIONS.json
A_trajectory/REPORT.md/json + INDEPENDENT_VALIDATION.json
B_matched_cost/protocol.json + schedule.json
B_matched_cost/REPORT.md/json + INDEPENDENT_VALIDATION.json
JOINT_CHRONOLOGY.json + CLOSEOUT.md/json
REPRODUCTION.md + PROTECTED_FILES_CHECK.json
ARTIFACT_MANIFEST.json + complete/anonymous archives
```

未达到阶段用NOT_REACHED并给实际计数，不创建假receipt。先在独立干净目录解压/重建证据、离线复算；不要把“已有verifier曾通过”当成本轮执行回执。足以核对结果的数组、tape和timer文件须可从提交内容或索引归档取得。

提供一个新的统一入口，例如 `scripts/platform/rtx_trajectory_cost_v3/study.py`，支持 `prepare`、`seal-protocol`、`A-pre-live`、`seal-predictions`、`A-live`、`B-formal`、`verify`、`archive`；这是本次要实现的接口，不是声称旧仓库已有的命令。入口执行状态检查和hash guards，给出Windows可直接运行的准确命令、目录、恢复/停止说明。不要把只能阅读的旧绝对路径或省略参数的伪命令当作交付。

## 17. 最终汇报与 Draft PR

PREPARE_ONLY先交付一份具体protocol/engineering Draft PR并停在第10节；正式授权后继续同一研究分支，完成时更新Draft PR为结果交付，保留协议提交及全部freeze祖先。PR针对实际main，只包含新研究范围；若base前进导致冲突，在独立checkout核对，不改封存source身份、旧论文或raw结果。

最终汇报须包含：starting/source/protocol/F1/F2/final/remote HEAD、branch、工作树状态、main与#45关系；模型/数据/runtime/timer身份；审核和remote chronology；实际cohort及排除数；计划与实际执行计数；所有stop/偏差；A五条件结果及reference-divergent prompts；B各路径gate与允许的成本结果、CI、绝对ms；独立验证/negative checks/重建记录；完整/匿名包hash和可获取路径。

解释严格按结果写。不要把H2 tape驱动的R_ONLY称为draft-free生成，不写proposal/history必要性，不把UB2容量称为已隔离的verification原因，不以72/72外推其他任务/设备，不把旧24/36失败消失，不给blocked路径lossless speedup，不根据空hook推断整个日志成本。不自动整合论文或merge。

**你的下一条执行动作：默认完成PREPARE_ONLY。**先检查精确代码与资产，落地新入口、协议和工程资格，完成F0远端冻结并提交可审核PR。作者审核确切版本后，通过同一完整prompt继续A+B；科学结果如何都按预定分支交付。

## 已核对的只读来源

- [v0.8.6 main 集成锚点](https://github.com/leecdiang/HeteroSpec/tree/361cb43a67f7fd9bfae95de4cdf7e816c46bbe90)
- [canonical handover](https://github.com/leecdiang/HeteroSpec/blob/main/paper/mlsys2027/HANDOVER_CURRENT.md)
- [PR #46](https://github.com/leecdiang/HeteroSpec/pull/46)
- [PR #44](https://github.com/leecdiang/HeteroSpec/pull/44)、[PR #45](https://github.com/leecdiang/HeteroSpec/pull/45)
- [H2设计](https://github.com/leecdiang/HeteroSpec/blob/494a5ca4fe62534b032b37d01652c3f88e0d16e1/benchmarks/rtx_independent_proposal_replay_v2/H2_DESIGN.md)
- [H2有效配置](https://github.com/leecdiang/HeteroSpec/blob/494a5ca4fe62534b032b37d01652c3f88e0d16e1/benchmarks/rtx_independent_proposal_replay_v2/EFFECTIVE_CONFIGURATION.json)
- [H2条件入口](https://github.com/leecdiang/HeteroSpec/blob/494a5ca4fe62534b032b37d01652c3f88e0d16e1/scripts/platform/rtx_independent_proposal_replay_v2/phases.py)
- [既有计时器构建](https://github.com/leecdiang/HeteroSpec/blob/494a5ca4fe62534b032b37d01652c3f88e0d16e1/scripts/platform/rtx_transfer_latency_v1/build_timer.py)
- [既有RTX协议](https://github.com/leecdiang/HeteroSpec/blob/494a5ca4fe62534b032b37d01652c3f88e0d16e1/benchmarks/rtx_transfer_latency_v1/protocol.json)
- [pinned draft参数继承](https://github.com/ggml-org/llama.cpp/blob/0cae43063cf15170e91a2ff4d034da0ecef4a1b2/common/speculative.cpp)
