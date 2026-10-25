# RTX 原生复现与部署桥接执行方案

状态：**READY FOR PLATFORM EXECUTION；尚未运行新的 RTX 实验。** 本方案供 RTX 5070 Ti Laptop 主机执行。稿件底稿为 PR #145，运行时来源以下列固定提交为准；执行开始时另记实际工作分支和工具链身份。

## 目标与完成顺序

RTX 承担两个任务：交付可实际重建/运行的最小原生材料；在同一套运行时内解释 resident k=3 的正向结果与 fresh k=1 的未建立增益结果。先完成小规模恢复与资格验证，再安排成本实验。B570 不需要镜像重复这套 2×2 因子实验。

本实验独立于 PR #140/#142 的长自然输入/flash-attention 计划。PR #142（检查时 head 为 `500b6a86d135e3ad85845ffc3a24eba5a477fb97`）记录：所查 MBPP/GSM8K 池在 256–448、640–832 两层均无输入，状态为 `S0_BLOCKED_MISSING_COVERAGE`，模型请求为零，并指出 864 与 852 的 worker 预算冲突。本方案直接研究既有暴露输入上的部署因素，另立 campaign/冻结文件，既不继承其未见长输入声称，也不改写那些失败记录。PR #142 已恢复的模型、两条可执行文件及 21 个 DLL 的身份材料可复用；那份 census 不算本实验的原生结果。若日后继续 PR #140，仍需单独修订其自然输入来源与预算。

| 阶段 | 本轮应交付 | 完成判据 |
|---|---|---|
| A：材料恢复 | 源码、补丁顺序、构建命令、依赖和模型身份；真实 stage/request fixture | 能从新目录重建，或精确说明历史二进制恢复与源码重建各自完成到哪一步 |
| B：原生复现 | 一个多查询 stage replay、一个完整 R/PQ/QB 请求；完整日志和比较脚本 | PQ/QB 的注册 stage bytes、完整输出/停止状态符合各自 reference，观察路径与自然请求对应 |
| C：受控桥接 | 同 stack 下 k=1/3 × resident/fresh 的 PQ_A/PQ_B/QB 完整请求成本 | 所有预登记单元有结果或明确失败状态；估计量、区间、A/A 与日期/会话敏感性齐全 |

阶段可独立交付。某个历史 archive 暂时缺失，不应阻止已有完整来源的构建、fixture 封装或新桥接可行性工作；新运行时的结果必须另立身份，不能冒充历史复现。

## A. 恢复真正使用过的材料

优先从本机既有已验证归档恢复；目录失效时搜索同名 capsule 和哈希，不依赖历史绝对路径。以下身份来自稿件的 `anc/runtime_reproduction/PROVENANCE.json`：

- 原始 repair/source：`3235d44c26edd92db33e574094c26af8e29d2452`，`SOURCE_RUNTIME.part001/.part002`；source inventory SHA256 为 `f974589db02a64fedcfdb0c76448bcf393a246e0f0a76d68e3b2e27837b05cdb`。
- PQ metadata4 修正：同提交的 `SOURCE_RUNTIME_V02.part001`；archive SHA256 为 `36be0d738ad5d29579b75825f68337003eb127405cc5418abc566cb07718a4d8`；source inventory 为 `720ba3522829572f63ad7c50974673d6488349eaaadab9e53371fb512609e84f`。
- E1/E2 封存：`f997262d6b0accb126a1217c9356745cc8bbf708`，入口 `benchmarks/rtx_qb_confirmation_v1/final_20261015`。按其索引恢复 capture、replay、model contract、build manifest 和原始请求记录。
- 后期 RTX fresh service：`9868acfbb2ae2e4b753ad20b680c333d55289dc0`，入口 `benchmarks/rtx_platform_closure_v1/execution_v2`。这是另一运行时合同，不能替代 E2 source。

**历史路由必须保留：** 全部 Qwen3 臂和所有 R/QB 臂使用原始可执行文件；仅 SmolLM2/Llama 的 M_PQ、C_PQ 使用 metadata4 版本。原始与 metadata4 的 21 个数值 DLL 哈希一致。稿件中附带的后期 `hs_scope.h` 是 service 实现示例，不能替换 E2 的环境选择器。

在新目录重建，列出实际编译器、构建参数、源文件差异、加载模块和 driver。历史工具链不可用时允许修复构建脚本或制作新工具链移植；原始恢复结果与移植结果分栏报告。先保留现有可运行路径，不为追求“完全干净”删除唯一工作副本。

最小 fixture 从真实归档选择，不自行生成替代输入：

1. 一个已准入的多查询 Qwen3 attention capture，优先 q=2 或 q=3，保留 Q/K/V/mask 原始跨度、shape/stride、head map、参数和 MQ/PQ/QB stage 输出。选哪个已存在的层/阶段由实际 archive 决定，选择规则和身份写入 manifest。
2. 一个完整原生请求，保留模板后输入 bytes/token IDs、模型/tokenizer 身份、R 输出 IDs/EOG/stop、PQ/QB 配置、必要的 state/work trace 和运行命令。GSM8K/443 可作为优先候选，缺失时从同一已冻结面板选资料齐全的一项并记录原因。
3. `README`、一条重建命令、一条 stage replay 命令、一条 request smoke 命令、机器可读 PASS/FAIL、SHA256 清单。大文件留在现有受控 artifact 路径，仓库保存代码、索引和可校验获取方式；不提交模型权重或完整 raw telemetry。

若 M3/C3 的原源码也在手边，沿实际 graph builder 分支确认历史 `query_batch` 是哪种实现，记录文件/行号及源码哈希；标签不足时保留未解决，继续其他任务。

## B. 原生检查应证明什么

先跑已有 CPU 合同和来源校验，再执行最小 GPU replay 与完整请求。stage 检查包括输入前后身份、重复执行、MQ own-path 和 PQ/QB stage bytes；完整请求按原合同比较完整输出及停止状态。需要 heavy capture 时，将其与 clean request timing 分开，验证观察开启/关闭没有改变资格。

这一步的完成是“真实 fixture 可复现”，不是重新获得 72-context 或六会话证据。若需要改源码才能通过，保存原失败，再以新构建身份复核。numerical mismatch 只使对应运行不合格，不能用其时间报告 qualified speedup。

## C. 同条件部署桥接

第一轮只用现有 Qwen3-8B/0.6B Q8_0 与既有 12 输入（MBPP 123/140/255/401/413/418；GSM8K 111/120/1308/141/322/443）。共同参考为 target-only R；共同配置起点为 ctx1024、target caller UB4、draft UB1、F16 KV、non-flash、greedy、native EOG 或 cap128、禁用 prompt-cache reuse。线程和电源策略在本机可行性阶段核实后统一冻结。

| 因子单元 | k | 生命周期 | 比较臂 |
|---|---:|---|---|
| A | 1 | resident | PQ_A、PQ_B、QB |
| B | 3 | resident | PQ_A、PQ_B、QB |
| C | 1 | fresh | PQ_A、PQ_B、QB |
| D | 3 | fresh | PQ_A、PQ_B、QB |

PQ_A/PQ_B 是相同实现的重复控制。优先让全部因子单元和臂共用同一二进制。若确需两个构建，每个构建分别覆盖完整因子单元和臂并单独分析，或增加能单独识别构建效应的交叉对照；不得将构建与 k、生命周期或布局绑定后作因果归因。数值资格通过和 DLL 哈希一致不能证明两个构建性能相同；无法拆分时直接报告构建与部署效应未分离。两种生命周期共用输入准备、prefill、生成、采样和结果构造代码。resident 保留 context/graph cache、每请求清理状态；fresh 每请求创建/reserve 并在 timer 内销毁。模型权重在两者均驻留，且不得跨请求复用 KV/prompt 前缀。

主指标为完整请求服务时间，包含各生命周期应承担的 reset/create/reserve、prefill、generation、采样、状态更新、同步、结果构造及 destroy；reference 比较和文件输出在 timer 外。另记共同的 prefill+generation 窗口和生命周期区间。原始秒数、毫秒差、比值与完整请求数都交付，不从 profile 扣出所谓 clean cost。

相同 k 的不同臂/生命周期应保持完整端点及匹配的 acceptance/correction/bonus、KV trimming 和逻辑工作。能无干扰取得 full logits 时保留拒绝行；若 heavy readback 会破坏自然图，采用独立资格运行，不将其时长混入主计时。实际 q、key extent 和布局以运行记录为准。

### Graph 观察是分层证据，不是全局开关

优先记录实际 capture/instantiate/replay/eager/fallback、cache reuse/invalidations 和 shape 身份。先做相同 PQ 的 counter-on/off 小型校准；不要假定缓冲计数免费。若观察器改变图选择或开销无法控制，clean timing 关闭它，另做同身份诊断。缺少可用 Nsight/CUPTI 或某项 counter 不阻塞总成本实验，缺项写 `unobserved`，禁止把“编译启用”当作实际 replay。

只有后续还要声称 Graph 是因果机制，才增加同合格单元的受控 ON/OFF 干预。当前 2×2 结果首先回答 k/lifecycle 如何改变 QB 的总成本效应。

### 可行性可调整，正式统计不能追结果

先做少量工程输入、相同 PQ 的噪声/观察开销检查，估计运行时间，再冻结正式预算。此前的“8 会话、逐请求 warmup”只是初稿预算，可在可行性阶段改成更适合此运行时的有限方案；说明选择依据。建议以 6–8 个新进程会话、跨多个日期为起点，不预先宣称功效。warmup 使用明确、统一且有物理意义的规则，全部另记成本，不强制为每个测量都做一个完整重复请求。

正式开始前提交 `FREEZE.json` 和执行顺序：stack/reference/panel、四单元与三臂、timer、warmup、排序种子、会话/日期/资源上限、失败/重试处置、估计量和区间方法。正式预算不按 QB 效应或显著性追加。在输入/会话的匹配块内，随机化并平衡四单元顺序及 PQ_A/PQ_B/QB 臂顺序；各臂遵循同一预热规则，记录 cache 状态，避免顺序固定造成热状态混杂。

每个输入/会话/单元取 `r = T_QB / mean(T_PQ_A,T_PQ_B)`，按输入再按会话等权平均 log ratio。保留四单元估计及配对 k、lifecycle、交互对比；预登记同时区间或清楚区分主/次对比。不确定性以独立进程会话为聚类单位，并保留块内四单元配对；日期有额外共变时按日期处理或报告敏感性。12 个输入是固定的已暴露面板，不当成 12 个独立运行时会话，也不外推未见输入总体。实际收益门槛为 2% 服务时间下降（r<0.98），同时报告 A/A、会话/日期敏感性和逐输入回归。原先 1.02 的 PQ/QB 门槛不与此混用。样本量不足或区间跨阈值时报告不确定性，不能解释为无效或等价。

## 持续推进与恢复规则

- 路径、依赖发现、构建命令、日志写出和 adapter 的工程修复可自行处理，写 amendment 并复核受影响资格；不要为了一个旧路径或可选工具反复等待用户。
- 程序只管理自己启动且身份已验证的进程；使用已有清理工具或 `try/finally`，退出时回收 owned workers。不要全局杀死 Python、模型服务或清理未知目录。
- 以 campaign/session/input/cell/arm 组成唯一 slot ID。记录 pending、running、complete、failed、blocked、interrupted；文件原子落盘。重新启动先核对已完成结果的身份与哈希，只执行 pending 槽位。
- 已开始但结果不明确的槽位标为 interrupted，不冒充“未开始”。需要技术重试时，按冻结规则建立整个配对块的新 attempt，保留原 attempt 的所有已完成/中断行，不能跨 attempt 补成一对；诊断重试不覆盖正式测量。某单元失败时继续不依赖它的复现/分析，不把局部阻塞升级成全部暂停。
- formal 中改动源码、reference、timer 或观察模式会生成新的确认性 cohort；旧 cohort 保留，不同版本分别报告确认性结果；跨版本的探索性综合须单列，不能替代冻结对照。

最终交付 `RESULT.md`、可校验材料清单、build/native 检查回执、完整槽位表/计时表、分析脚本和 source/host 身份；清楚分开 **历史恢复、原生复现、新桥接结果、未完成项**。执行结果开独立 RTX PR，不覆盖稿件 PR #145，也不直接改写论文数字。
