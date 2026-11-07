# RTX 平台联合实验 Prompt：跨后端预测与 fresh 合格路径延迟

冻结日期：2026-09-30（北京时间）。仓库：`leecdiang/HeteroSpec`。核对时 `main=f8290281156f6b3de8fbc8b44fd10a4afa7bcd89`，论文修订 PR #40 为未合并 draft。正式执行时重新记录最新 main、worktree、代码和环境身份；main 如已前进，核对差异并写入冻结记录。

## 联合执行的科学边界

**可以在 RTX 平台一次性组织完成，但这是一个平台活动中的两项独立研究，不是一次推理同时产出两个结果。**同一 RTX 主机、模型资产与驱动检查可以共用；预测与延迟必须有不同提示词用途、条件、计时/预测端点、冻结检查点、原始运行及分析。预期的基础正式执行量为预测臂 `24×3×(reference+predictor+batched live)=216`、延迟臂 `30×3×(reference+serialized)=180`，合计 **396 次**；R0、暴露 discovery、候选提案生成及可能的技术重启另计，协议须给出完整日程。两个臂顺序运行，避免 GPU 资源与温度互相干扰。

已有 RTX v2 的 batched 75/90、serialized 90/90，以及历史 serialized 计时，只能用于设计和工程检查。它们不能填入任何一个新正式分母。若预测臂无法产生可冻结的候选，延迟臂仍可按原预注册完成；若延迟资格或 timer 失败，预测臂仍可按原预注册完成。两个结果独立解释。

## 可直接交付 RTX 主机执行者的 Prompt

你负责 HeteroSpec 新研究 `RTX_TRANSFER_AND_MATCHED_LATENCY_V1`，在 Windows 11 + RTX 5070 Ti Laptop + llama.cpp CUDA0 上完成**一个平台活动、两个独立实验臂**：A 为 prospective batched-path prediction，B 为 freshly qualified serialized-path matched latency。工作包括方案、实现、预注册、冻结、完整新执行、独立验证、归档和一个 draft PR。禁止改旧研究数值/证据或论文，不自动 merge；阳性结果不是交付条件。

### 0. 仓库和现有证据核对

递归检查仓库和主机可用归档，至少阅读：

- `benchmarks/rtx_direct_id_v2/{PREREGISTRATION.md,protocol_v2.json,FORMAL_REPORT.md,CLOSEOUT.md,NATIVE_CAPTURE_CONTRACT.md,build_manifest.json,runtime_freeze_manifest.json}`；
- `scripts/{rtx_direct_id_v2.py,verify_rtx_direct_id_v2.py,rtx_direct_id_v2_background.py}`；
- `benchmarks/b570_mechanism_v08/{DISCOVERY_PLAN.md,HARNESS_DESIGN.md,PREDICTION_FREEZE.md,CLOSEOUT.md}`；
- `reports/5070ti/HUMANEVAL_LLAMA_REPLICATION.md`、`scripts/windows_humaneval_llama_replication.py`；
- `docs/{experiment_protocol.md,data_policy.md,reproduction.md}` 与当前论文 `sections/{03_methodology.tex,05_diagnoses.tex,09_limitations.tex}`。

从最新 main 的干净独立 worktree 新建 `experiment/rtx-transfer-and-matched-latency-v1`。使用新研究目录 `benchmarks/rtx_transfer_latency_v1/`，其中 `prediction/` 与 `latency/` 分开；源码放 `scripts/platform/rtx_transfer_latency_v1/`，两臂 raw/归档分别放 `artifacts/rtx_predictive_transfer_v1/` 和 `artifacts/rtx_matched_latency_v1/`。旧 v2、旧 Windows 计时和论文只读。一个总 manifest 可共享主机、驱动、模型、数据与上游源码身份，但每个臂分别记录自己的 runner/timer 二进制、命令、数据、资格和 freeze SHA；不可假定两个臂使用完全相同的可执行文件。

沿用可用的 Qwen3-8B Q8_0 target、Qwen3-0.6B Q8_0 draft、llama.cpp b10839 / `0cae43063cf15170e91a2ff4d034da0ecef4a1b2`、greedy k=2、seed 123、FA off、完整 CUDA0 offload，语义端点为首 128 个已提交 generated ID 或更早且包含 EOG 的序列。target、draft、数据集、CLI/DLL/source/patch、GPU/驱动/CUDA、环境、确切命令和原始日志全部哈希/记录。若旧 v2 的模型或 driver 字节不同，明确冻结新的条件并重新资格，不能宣称精确重放。保持 native committed-ID 的无损字节抓取，排除 prompt IDs 与未提交 proposals；不以文本重 tokenize 判 exact。

### 1. 联合预注册与两臂共同 R0

在任何正式运行前提交机器可读 protocol、完整计划和源代码。将两臂的科学问题、不同分母、提示词用途、固定调度、失败规则、端点和禁止互借数据写在同一个总 protocol 的两个独立 arm 中。R0 检查设备、全层 offload、fresh process/context、EOG/128 cap、native ID 事件、lossless 日志读取、命令与环境身份。R0 数据不进入任一正式分母。

预先锁定执行顺序：A 的暴露 discovery 和预测器冻结 → A 的 reserved reference/predictor 与预测文件冻结 → A 的 reserved batched live → 主机空闲、按预设规则稳定时钟/温度并核对所有 hash → B 的新 180 次配对资格/计时。B 的 protocol 与 timer/R0 必须在 A 的第一个正式运行前冻结；A 的结果不得改变 B 的任务、条件、计时或估计量。若要调整顺序，必须在正式开始前改协议并重新冻结。两个臂不并发运行。

### 2. A 臂：RTX batched 路径的前瞻完整序列预测

**冻结目标。**在 RTX 上，先从已暴露 discovery 构造并冻结一个候选，然后在新 reserved live 结果出现前写死 72 条完整预测。主终点是 24 个不同 reserved 提示词 × 3 次的 predictor/`RTX_BATCHED_K2` live 完整 ID 数组相等，预设 72/72 为全中门槛；同时报告同一批 reference/live 相等、参考分歧的不同提示词数、分歧位置与 ID、任务级重复稳定性。只有至少一个后来实际参考分歧的 reserved 提示词被正确预测，才称全中结果有区分力；零分歧时标为 `NONDISCRIMINATING`。这测试预测程序跨 Vulkan→CUDA 后端，不预设 B570 的 UB1 机制直接迁移。

在任何新模型推理前审计仓库与所有可访问本机目录的任务暴露。旧 RTX v2 的 30 任务、历史 CUDA/106、旧 B570 reserved 24、任何其他已知结果或状态不明的任务，均不能作为 A 的 reserved 正式任务。对剩余未暴露 HumanEval ID 用协议预先固定的盐 + task ID 的 SHA-256 排序选恰好 24 个；冻结完整名单、可选池、排除理由、输入 hash。可读输入文本，但在假设冻结前不得对 reserved 作 target-only、proposal、logit、R0 或 live 推理。池不足时先停止并另行冻结可许可新任务来源和提示格式，不从已知有利任务补足。

A 的暴露 discovery 固定 12 个旧任务 × 3 次：batched 分歧 `/64,/106,/119,/128,/129`；参考相等控制 `/3,/10,/19,/20,/28,/32,/44`，均指 HumanEval ID。先证明 common target reference UB1 harness 对既有参考完整 ID 的 90/90 工程资格并通过日志/设备/预算检查；失败为 `HARNESS_NOT_QUALIFIED`，不得进入 reserved。预注册至多两个候选：H1 使用与 reference 同前端/输入/采样器的 target-only `n_ubatch=2`；H2 仅在 H1 discovery 失败、且能在 reserved live 前**独立生成** proposal tape 时，使用固定提案 target verification replay。target-only 的单 token decode 即使设置 UB2，也未必模拟 speculative 的批量验证，必须以实际发现和分组记录检验，不得按参数名称推定。H2 不得引用任何 reserved live proposal、输出或未来状态。H1 全部 36/36 discovery complete-ID 才入选；H1 失败才按冻结决策树检验 H2 36/36。两者失败或 H2 无法独立产生提案，交付 `MECHANISM_NOT_ISOLATED` 并停止 A 的 reserved；不得事后搜索 H3、换模型/k/ubatch 或挑任务。此停止不取消已独立冻结的 B。

候选入选后，在**任何 reserved 推理之前** commit + push 唯一 predictor 算法、源码/二进制/模型/数据 hash、24 ID、三次重复、预测/参考定义、72/72 规则及失败处理。之后只执行 A 的 reference 与 predictor `24×3×2=144` 次。重复不稳定或操作/设备异常则保存记录并在 live 前停止。把 72 条完整预测与对应参考数组、全 SHA-256、预先预测的相等分类和首分歧组成不可覆盖文件，记录文件 digest 并 **commit + push；此时间必须早于第一个 reserved batched live 结果**。之后执行 72 次新 `RTX_BATCHED_K2` live，错配也全部保存，不选择性补跑。旧 75/90 和五个旧分歧任务绝不进入新 72 的分子/分母。

### 3. B 臂：RTX serialized 的新鲜合格路径配对延迟

**冻结目标。**在与 A 分开的正式运行中，以原 RTX v2 固定的 30 HumanEval ID、每个 3 次、新运行的 `TARGET_REFERENCE_UB1` 与 `RTX_SERIALIZED_K2_UB1`，比较相同 prompt/template/model/runtime/driver/计时边界，合计 `30×3×2=180` 次。每个 task×rep 内两条件顺序按预先冻结种子随机化。只有这批新 serialized/reference 完整 generated-ID **90/90** 且 180 次 timer/设备资格完整，才估计 post-prefill 速度。每提示词取各条件三次延迟的中位数，算 `T_target/T_serialized`，再对 30 个比值取几何均值；大于 1 才表示 serialized 较快。报告绝对毫秒、逐提示词比值、10,000 次提示词 bootstrap 95% CI（固定 seed），重复不当作独立提示词。不得做能耗结论。

B 的计时从初始 prompt prefill 完成后的生成循环初始化/seed 和所有必要状态工作开始，到最后一个已提交 ID 完成。serialized 必须计入 draft 推理、target 验证、接受/纠正/bonus、同步、KV/状态清理、proposal 与调度；target-only 有相应一致边界。排除模型加载和初始 prefill。进程总 wall time 混入加载/prefill，不合格；未核实的 `--perf`/内部 `eval time` 可能漏 draft/集成，也不能直接当终点。B 的 R0 用事件边界和独立时间记录校验 timer，并在看正式性能前固定观测 hook 开销阈值。若为计时修改 CLI/runtime，预先提交 patch、逐文件重哈希、证明输出语义不变并重新执行 direct-ID 仪器资格；旧 v2 的 90/90 不能为新构建背书。计时端点无法核实时报告 `TIMING_INVALID`，不计算 speedup。

B 正式运行保留每次完整 ID、原始 timer 起止事件、输出长度/EOG、命令、环境、设备/热状态与 stdout/stderr。所有错配继续留存。新运行若 <90/90，B 为 `QUALIFICATION_BLOCKED`，对应计时仅可标为诊断，不以旧 serialized 0.650× 或 A 的 batched 结果修补。操作不完整为 `INCOMPLETE_OPERATIONAL_FAILURE`。A 无论成功失败都不能影响这些判断。

### 4. 独立验证、归档和 closeout

分别为 A、B 编写不导入各自主分析 comparator/aggregator 的独立验证器：A 重读 native events、重算新 72 对、reference 分类和首分歧，并核对预测文件 commit/push 早于 live；B 重算新 90 对、180 个 timer 区间、配对、中位数、几何均值和 bootstrap。验证 source/binary/model/command/device/任务/调度覆盖、前后 hash 与完整失败记录。为两臂分别生成可离线检查的内容寻址原始证据包；按仓库数据政策排除权重和二进制，但保留身份 hash 与可选本机重哈希入口。

一个 draft PR 可含两个分开的 arm 报告和一个总 closeout，明确列出：共同计划/source freeze、A 假设冻结、A 预测文件冻结、A 首个 live、B 首个计时、各自独立验证和归档的 commit SHA 与 UTC 顺序。报告每臂的正、负、无区分力、资格失败或操作失败，不合并分母、不叙述 batched BLOCKED 路径的性能，也不声称两臂是同一次推理。作者审阅后才决定各自是否进入论文；不自动 merge。
