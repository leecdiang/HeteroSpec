# HeteroSpec P0：独立代理统计与证据审查

日期：2026-10-27  
审查基线：PR145 原稿 `85b3f2d6e43ea7d19fb4b0f6827cbd7f492f6fdb`（本地 `paper_current`）。  
审查对象：最终 P0 源稿 `paper_revision`；关键文件 SHA256 见同目录 `independent_stats_final_snapshot.json`。  
审查角色：未参与被审正文与两个新分析脚本编写的独立审查代理。这里的独立性指任务内的作者/复核职责分离；这不是外部人类同行评审、期刊审稿或编辑决定。作者仍负责最后的科学判断和提交。

## 结论

**P0 在现有科学范围内构成实质增强，可作为增强稿更新 PR145。未发现阻断问题或尚需修复的重大统计/证据错误。** 审查中发现的一个 EOG 来源表述问题已修正并复核。此结论不以“必须通过”为预设，也不把复现脚本的 PASS 当作论文价值判断。

增强有三个明确来源：

1. 从原始 E2 请求独立重算了此前未直接报告的 draft-on/off 对比，在正确的六会话层面描述了固定面板上的政策方向与不确定性。
2. 原七臂结论现在具有可逐条追溯的原始响应审计，并明确区分相同逻辑工作与处理政策有意改变的物理图工作。
3. 叙述把历史 M3/C3 资格证据、具名 GS/PQ/QB 比较、E2 事后分析和后续服务实验分开；策略选择改为候选组合的观测成本比较，避免把条件效应假定成可分离的顺序最优化。

这轮增强**没有增加原生执行、独立主机、输入覆盖或独立日期**，也没有独立重复完整的 GS/local × draft 交互。正文、摘要和补充材料已保留这些边界。

## 1. 审查范围与方法

实际读取并应用了本地 `statistical-analysis.md`、`scientific-critical-thinking.md` 和 `peer-review.md` 及相关伦理、统计可重复性说明。具体采用其估计目标与抽样单位优先、逐项分母追踪、假设与设计分开评估、探索性/预注册区分、声明—证据对应和可行修复原则。未将医学试验指南或自动检查分数机械套用到系统实验。

本任务是作者授权的内部修订审查，非外部期刊受邀审稿，未宣称完成某个期刊的 AI 或保密政策审查。稿件和数据只在授权工作区内读取；唯一的公开网页查询用于核对所用审查技能的书目，不含稿件内容。无远程写入，无原生 GPU/模型执行，无论文源文件编辑。

审查覆盖：

- 基线与改稿全部共有源文件差异，包括摘要、引言、方法、设计、评估、选择规则、结论、S2/S3、README、证据地图与 `anc/check.py`。
- 两个新生成器、三个新表、E2 派生 JSON/CSV，以及七臂的字段投影、原始索引、计划、语义、源码/构建记录与版本路由。
- 独立计算而非仅调用作者生成器；随后运行两项作者 `--check` 作实现一致性复核。
- 最后精简正文和措辞修正后，重新检查关键源文件与两个生成器的结果。PDF 的版面/分页验收由主任务负责，本报告不把源稿检查描述为 PDF 全页视觉验收。

计算环境：Python 3.12.14，标准库 `csv`、`math`、`statistics`、`collections`、`json`、`hashlib`、`gzip`、`zipfile`；独立重算未导入两个被审生成器。

## 2. E2：独立数值复核

### 2.1 来源、分母与估计量

直接读取 `anc/rtx104/E2_REQUEST_LATENCIES.csv`。其 SHA256 为：

`f29eba027022a1fb704bc1fb58ce3fe535d4387cdbec564f8086ac4bfdc08194`

我独立得到 1,620 行，其中 324 个标记 warmup、432 个非 warmup 串行参考请求、864 个非 warmup 本地布局请求。后者正好组成 `3 families × 6 sessions × 12 inputs = 216` 个完整四元组，每个含一条 M_PQ、M_QB、C_PQ、C_QB；无重复或缺失的被分析布局记录。

对每个输入/会话先计算 `log(T_M/T_C)`，每会话均值含 12 个输入，然后对六个会话均值等权平均并取指数。Gamma 由同一四元组内的 `D_QB/D_PQ` 计算，再用同样权重汇总。该估计方式与论文 Equation `eq:ratio` 一致；在完整平衡面板上也与直接对相应 72 个任务/会话 log 比求均值一致。

置信限按 `exp(mean(z) ± t(0.975,5) × sample_sd(z)/sqrt(6))` 独立重算。为避免照抄作者常量，我反解 df=5 的 Student CDF：令 `a=atan(t/sqrt(5))`，则 `F(t)=1/2+[a+(2/3)sin(2a)+(1/12)sin(4a)]/pi`，得到临界值 **2.5705818356363146**。

### 2.2 全部九个独立结果

| 家族 | 对比 | 独立点估计 | 独立 pointwise 95% t5 区间 | 六会话 >1 / <1 |
|---|---|---:|---:|---:|
| Qwen3 | D_PQ | 1.072057666 | [1.058882365, 1.085396904] | 6 / 0 |
| Qwen3 | D_QB | 1.083665770 | [1.059328094, 1.108562596] | 6 / 0 |
| Qwen3 | Gamma | 1.010827873 | [0.996110937, 1.025762242] | 4 / 2 |
| SmolLM2 | D_PQ | 0.575628513 | [0.563960658, 0.587537766] | 0 / 6 |
| SmolLM2 | D_QB | 0.596931351 | [0.582287946, 0.611943008] | 0 / 6 |
| SmolLM2 | Gamma | 1.037007961 | [1.027961795, 1.046133734] | 6 / 0 |
| Llama | D_PQ | 1.090530327 | [1.069862389, 1.111597535] | 6 / 0 |
| Llama | D_QB | 1.105048445 | [1.096790200, 1.113368870] | 6 / 0 |
| Llama | Gamma | 1.013312897 | [0.994813982, 1.032155806] | 5 / 1 |

表格与新增 `tables/e2_draft_profitability.tex`、`tables/e2_draft_profitability_details.tex` 在显示精度上全部一致。正文 QB 的 7.72%、9.51% 降低及 SmolLM2 的 67.52% 增加，使用 `1-1/D` 或 `1/D-1`，也正确；没有把 speed ratio 的百分比与 latency reduction 混用。

QB 六会话任务聚合中，Qwen3 有 10/12、SmolLM2 有 0/12、Llama 有 11/12 输入支持 drafting；与 S3 一致。PQ 对应为 9/12、0/12、11/12。

### 2.3 抽样单位、块序与有限敏感性

**没有将 864 请求、216 四元组或 72 任务/会话格伪作独立统计样本。** 新区间使用六个会话 log 均值，并在设计与表注中声明 independent/approximately normal 假设。六次会话在一台主机、两个日期上运行：六会话统计不能自动升级成六个独立日期或多主机总体推断。正态性或独立性也不能由一个小样本诊断的“未拒绝”来认证。本轮不据此增加无必要的正态检验或事后功效。

独立读取 block 编号得到 M-before-C 的会话数分别为 Qwen3 4/6、SmolLM2 3/6、Llama 4/6，其余均 C-before-M，与新增文字一致。四元组是匹配分析格，不是四臂紧邻随机交叉执行。新主文和 S3 明确说明其配对不能消除会话内漂移，这是必要而充分的当前范围限制。

作为针对该风险的有限诊断，我另外检查了两种块序分组和六次 leave-one-session-out 点估计，未作新显著性声明：

| 家族 | QB：M-before-C 聚合 | QB：C-before-M 聚合 | QB：逐一剔除会话后估计范围 |
|---|---:|---:|---:|
| Qwen3 | 1.080798438 | 1.089423276 | [1.077494639, 1.088952030] |
| SmolLM2 | 0.604560194 | 0.589398774 | [0.593935445, 0.601883106] |
| Llama | 1.103283855 | 1.108586095 | [1.102938992, 1.106785008] |

这些描述性检查说明当前方向并非由单次会话或仅一种块序决定；它们不能估计或消除未记录的时间漂移。详细六会话值保存在 `independent_e2_recalculation.json`。

### 2.4 事后性与推断范围

新区间全部明确为 retrospective/exploratory/pointwise、无 multiplicity adjustment。两项本地 drafting 值与 Gamma 均完整呈现，没有隐藏 Gamma 跨 1 的 Qwen3/Llama 结果。SmolLM2 的 Gamma 大于 1 但 D_QB 小于 1 的反例保留，正确区分“QB 改善 drafting 的相对价值”和“drafting 本身盈利”。

E2 没有 GS；因此它支持固定暴露面板中本地 draft 决策的跨会话方向一致性，不是 GS→local crossover 的独立重复，也不是未见输入上的政策验证。最终摘要已加入 `on the same exposed panel`，主文与 S3 保留无 GS、无新增执行和块序限制。原 registered PQ/QB percentile bootstrap 结果未改。对目前这样的探索性估计报告，不需要为满足形式而强制补一套多重检验显著性程序；若日后把九个对比用作正式联合决策，则必须预先定义推断族与决策规则。

## 3. 七臂：原记录、版本路线与工作量审计

### 3.1 独立原字节复核范围

我直接从 `p0_counters/extracted/local/runs/formal/` 重开 **2,058** 个原始 `RECORD.json`，逐个与原 `INDEX.json` 的长度及 SHA256 比对。结果包含 **2,016 formal + 42 warmup**；去除 warmup 后，恰为 **288 个匹配七臂审计组**，键为 family/task/session/round，每组七臂具有相同 input hash。实际执行采用 42 个 family/session/arm workers，每个 worker 执行 48 个 formal 请求；第二会话反转各家族的 arm 顺序。288 组是跨这些 workers 按任务与重复编号重建的匹配集合，并非相邻、随机排列的七臂执行时间块。它们不能作为 288 个独立随机执行块，记录工作量匹配也不能消除 worker 间时间漂移。

进一步独立核对全部 2,016 formal 记录：

- `output.ids == response.tokens`；
- 归一化 `workload == response.hs_closeout.workload`；
- 输出长度与 `tokens_predicted`、原生 tokens 数一致；
- 归一化 stop reason 对应原生 `stop_type`；
- prompt-cache count 对应 `response.timings.cache_n`；
- `truncated` 与原响应一致。

我还从原归档的 `MODEL_CONTRACT.json` 读取每家的 EOG ID 集合，以原生 token ID 逐个重算 EOG flags，**2,016/2,016 组一致**。该 model contract 的原始 SHA256 为 `7fe5ad4dfff880b9da0394c1448eb6c3fb5cd733769e20319cf1fac1a9dc986d`。因此完整 endpoint 一致性不是仅比较长度、末 token 或一个端点 hash。

所有 **1,728 non-R→paired-R** 的完整 normalized output 对象逐字段相同。M、C 各自有 288 个 GS/PQ/QB triples，共 576 triples；每个 triple 三种两两对比，合计 1,728 comparisons。它们是可审计的配对计数，不是新增的独立统计样本。

### 3.2 逻辑工作与物理执行严格分开

直接比较每个原记录的所有 workload 字段，得到：

| 比较 | 配对数 | 出现差异的字段；每项差异均为 288/288 |
|---|---:|---|
| M_GS / M_PQ | 288 | physical_micrograph_calls、graphs_reused、target_prefill_physical_calls、target_physical_width_hist |
| M_GS / M_QB | 288 | 同上 |
| C_GS / C_PQ | 288 | 上述四项，另有 target_continuation_physical_width_hist |
| C_GS / C_QB | 288 | 同上 |
| M_PQ / M_QB | 288 | 无，全部 exported workload 字段相等 |
| C_PQ / C_QB | 288 | 无，全部 exported workload 字段相等 |

这些结果支持稿件的新表述：逻辑 proposals、acceptance、rows、rollback、caller histograms 相同，GS 改变物理批处理。draft physical fields 也保持相同。它们没有把 GS 的物理图变化误判成逻辑 workload 不匹配。

计数语义明示 physical rows 为提交给 graph_compute 的 native token rows，不是 GPU hardware occupancy；graph reuse 也不是 CUDA Graph replay 事件计数。新文不把这些字段变成硬件 launch 证明、不把汇总计数提升为逐周期轨迹/bitwise KV 证明，也不从 ratio 产品推断 projection/FFN/attention 的耗时份额。目标-only 的收益明确包含 prefill，没有声称单 token decode 因 QB 获得同样速度提升。

### 3.3 来源链与修正版本

独立重算本地 parts 001/007/009 的 SHA256 与 Git blob SHA1，均与固定原 manifest/取回记录一致；原 manifest 的 Git blob 也重算为 `2ab06e9edac7752592e36570127291d57f2554d9`。本审查没有再次从远程取得这些 commit 对象，也没有下载其余六片或重算整个九片 ZIP 的 SHA256。正文正确说明了这一级别，而未把局部归档复核写成全包复核。

原始 index → record hash → compact projection 的路径可复核；作者生成器的 `--raw-root` 模式实际重开 2,016 formal originals 并逐条精确重现投影，结果全部通过。默认 `--check` 仅验证附带字段投影的范围，也在文档中说明，没有隐瞒缺少完整 raw bytes 时的能力边界。

我还核查 42 份原 `COMMAND.json` 的 hash、其 family/session/condition 与 2,016 条记录的 runtime identity 绑定，得到：

- 96 个初始 freeze 记录均为 Qwen session 0 的 R/M_QB；其余 1,920 个携带 v02 标记。
- **实际原 executable 使用 1,632 次；metadata4 executable 使用 384 次**，后者仅为 SmolLM2/Llama 的 M_PQ/C_PQ。
- 两份 native source inventories 唯一变化为 `src/llama-context.cpp`；原 correction patch 将 PQ 的 metadata reservation 设为 `4 × res`。
- 21 个 numerical DLL hashes 全部相同；counter definition、export、observer 源 hash 相同。

所以 v02 freeze 不能等同于 1,920 次请求都换用了 corrected executable。新 S2 已准确区分二者；GS/QB 同 executable 的归因基础较清楚，PQ 比较则保留其真实 metadata-capacity route。只凭相同 DLL 不能声称所有宿主代码/资源成本完全相同，稿件没有这么做。

## 4. 问题分级及处置

### 阻断问题

**0 项。** 未发现源测量被修改、抽样单位错误、数值重算失败、缺失被分析四元组、端点不匹配或新文把 E2 当作完整 GS/local 重复的情况。

### 重大必修问题

**0 项。** 剩余限制是原实验范围与识别能力的限制，最终稿已披露；不需要为了本次受限结论而补做新实验后才更新 PR145。未来更强的跨平台、因果机制或泛化表述需要相应新证据，见下一节。

### 轻微问题 M1：EOG 来源命名——已解决

- **位置：** `sections/05_evaluation.tex` 新七臂审计段、S2 `supp:sevenarmwork`、`tables/seven_arm_work_audit.tex` 表注、对应生成器、README 和 source receipt。
- **观察：** 初稿把 token 与 EOG flag 数组统称为 “native token and EOG arrays”。原 HTTP response 直接返回 tokens；EOG flags 位于 normalized output 中，并由 EOG token contract解释。
- **依据：** 原 RECORD 的 response 字段不含原生 EOG flag 数组；完整 flags 的一致性确实存在，且我依据原 token IDs 和 model contract 独立重算通过。
- **最小修复：** 使用 “native token IDs and recorded EOG flags”；receipt 明确直接对原生响应重新核查的是 tokens。
- **最终复核：** root 已在正文、补充、生成器、表和文档一致修正。记录投影 SHA256 仍为 `b0ac6e8a7216aa2f1bf9f544239df2a362b8e415d7b231a1e0112725b351c7be`；原数据未改；修改后两个生成器的 check 均再次通过。**关闭。**

## 5. 哪些是现在增强、哪些仍需实验

### 当前可成立的增强

- 七臂跨越盈利边界的叙述现在直接以具名的 GS/PQ/QB 数据起步，历史 M3/C3 不再容易被误读成有确定 PQ/QB 身份的实验。
- E2 新分析回答了有用而原本遗漏的问题：同一组本地布局下，draft-on/off 的方向是否在六次已有会话中一致。结果确实一致，且不确定性、任务例外、块序和事后性均可审查。
- “工作相同”具体收缩到可以核对的逻辑 counters/histograms，物理图与归档来源单列，避免机制结论超出观测。
- `argmin` 使用最终稿中的 **observed** `widehat T`，其候选域限定为已评估并通过 reference qualification 的组合。它不暗示已知真实全局最优，不保证顺序选择最优，也不新增 online correctness verifier。
- 原 negative results、SmolLM2 draft 成本、Llama transfer failure、k=1 practical screen 未被删掉；历史完整资格表移到 S2 后仍在，E1 72-context 结果只是重排。

### 要支持更强主张时必须补的实验

| 更强主张 | 所需的最小新增证据 | 与本次 PR145 更新的关系 |
|---|---|---|
| “完整 GS/local × draft interaction 已被独立重复” | 新的预先固定六臂或七臂 factorial；同 input/session 内短块随机化或严格均衡交叉顺序；预先确定 interaction estimand、完整请求 timer、有效单元和异常处置；GS/PQ/QB × M/C 都保留 | E2 缺 GS，任何额外 CSV 重算都补不上；当前稿只作受限描述，不阻断 |
| “B570/Vulkan 上也具有同样 draft-profitability 转换” | 在该 backend 上独立建立 full-endpoint qualification 后，运行实际 draft-on/off × repair/layout 对比；保留不支持或失败的配置，不用 RTX 效果外推 | 双平台实验 PR 可纳入这一前置条件；当前 Vulkan 结果不能替代完整经济性实验 |
| “某个特定算子或 CUDA Graph replay 是已量化收益来源” | 有 A/A/观察开销控制的分阶段计时或受控机制开关；真实 capture/replay/fallback 事件与请求计时绑定；处理重叠/异步，不能直接把 API span 相加为互斥 wall time | 现稿没有该强结论，未做此实验不阻断 |
| “策略对未见输入/长上下文或其他机器成立” | 预先冻结的新输入与范围，独立机器/日期，完整参考与 stop 语义验证；按正确层级形成不确定性 | 现稿固定 exposed panel 结论不能自动延伸，需明确增加范围 |

对 RTX 后续实验，优先使用一个可容纳 PQ metadata 的共同 executable/configuration 并记录 binary/source/loaded-module identities，避免把 build route 和 treatment 混在一起；如果因机制需要不同路径，应显式把它定义为 implementation contrast，并保留共同路径控制。对 B570，先完成与部署参考一致的 producer-state/continuation qualification，再注册 cost screen；失败配置应直接报告，不能为得到正性能结果在执行后调整准入条件。

### 可选、按目标决定的扩展

更多 draft length、prompt length、output cap、task domain、冷/热生命周期和真正独立主机可扩大适用域；若文章维持当前范围，它们不是本次 P0 的必修任务。逐周期完整轨迹或 bitwise KV/logit 证据仅在要声称对应的强同一性时必需，当前聚合工作量审计无须为此膨胀成全状态证明。

## 6. 测量不变、复核命令与交付判断

逐字节比较发现：原稿共有 189 个文件中 174 个不变、15 个变化；原有 129 个 `anc/` 文件中 **128 个不变，唯一改动是接入新验证的 `anc/check.py`**。没有删除原测量文件；已有 E2 CSV、原统计值与已有测量来源均未变。`main.bbl` 的变化仅是重新生成后的大小写/换行，不是替换参考证据。新七臂投影也在最终措辞修改中保持原字节。

复核过的作者命令：

```text
python3 scripts/generate_e2_draft_profitability.py --check
python3 scripts/generate_seven_arm_work_audit.py --check --raw-root /workspace/scratch/f7c1c9dbc8e4/p0_counters/extracted
```

它们分别返回 E2 216 cells / 864 measurements 与七臂 2,016 records / 288 matched audit groups（生成器字段仍名为 `seven_arm_blocks`） / 1,728 logical matches / 1,728 endpoint matches；后者另外返回 **2,016 original-byte projection exact matches**。这些运行是原数据重分析和审计复现，不能称为重新运行模型或独立硬件复现。

独立重算与最终快照附在：

- `independent_e2_recalculation.json`：九个对比的独立估计、区间、六会话值、块序与有限敏感性。
- `independent_seven_arm_recalculation.json`：原记录 hash、endpoint、workload、命令路由、EOG 独立重算覆盖。
- `independent_stats_final_snapshot.json`：最终审查源文件 SHA256 与 Python 版本。

**最终判断：可提交为已增强 P0 稿。** 这是对证据一致性和当前表述边界的判断；剩余工作应进入明确定义的新实验，而不把未来实验结果预写为已有证据。更新 PR145 时应继续把这份文件称为内部独立代理审查报告或计算/证据审计，不能称为外部人类同行评审。

## 最终版本状态：匹配审计组与执行 workers 的澄清

2026-10-27 在上述审查完成后，对最后五处源稿变更完成轻量终检：`sections/05_evaluation.tex`、`sections/04_design.tex`、`supplement/02_cuda_cost.tex`、`scripts/generate_seven_arm_work_audit.py`、`tables/seven_arm_work_audit.tex`。变更将 288 个集合明确命名为 matched audit groups，并说明实际 42 个 arm-specific workers、每个 48 个 formal 请求、第二会话反转顺序以及 worker 间漂移限制。

独立读取冻结原计划，确认三家族 session 1 的七臂顺序分别都是 session 0 的完整逆序，计划共 42 workers，每个恰有 48 formal slots。生成器与原 P0 交付实现的 AST 对比确认：除 `table_bytes` 外计算代码完全相同；该函数变化仅涉及表头/表注。表内全部数值保持 96、288、576/576 与 1728/1728 等原值，未改估计或记录。无需为这次说明性修改重跑完整数值与测试套件。

已刷新 `independent_stats_final_snapshot.json` 的这五个文件 SHA256；其余被记录文件的 hash 均未变化。本报告第 3.1 节及相关措辞同步采用“匹配审计组”。**最终判断保持：P0 实质增强，可更新 PR145；无新增阻断或重大必修问题。**

## 审查流程参考

本报告使用的程序性审查技能来源，已按当前公开记录核对作者、年份与版本：Kassis, T., Agarwal, V., He, Y., Patel, D., & Brueckner, A. M. (2026). *Scientific Agent Skills: A Library of Procedural Knowledge for Research Agents*. arXiv:2609.00065（当前记录 v2，2026-09-02）. https://doi.org/10.48550/arXiv.2609.00065 。该引用说明流程来源，不是 HeteroSpec 科学结论的证据。
