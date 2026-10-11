# JSA_THIRD_FAMILY_V1：冻结执行协议

## 1. 范围和不可变边界

RTX/CUDA 主研究，新增 Llama 8B/1B，旧 Qwen 和 Smol 作共同对照。先分别资格，再报告每家族费用，不把三个家族当随机抽样或池化历史请求。PR #80/#82 全部结果只读。新 study ID、新目录、新 ledger、新冻结；不能补跑旧 Smol 矩阵后覆盖它的 INCOMPLETE。

固定 upstream 为 `0cae43063cf15170e91a2ff4d034da0ecef4a1b2`，恢复 PR #80 最终 F 原生 core/frontend 与数值库，而非旧 S executable 或普通 upstream binary。读取 SOURCE_BINDINGS 指定的 NATIVE_BUILD/PATCH、SOURCE_RUNTIME_CONTRACT、MODEL_CHOICE、REPRODUCE 和 author archive。公开 RAW_EVIDENCE 主要支持 CPU 再分析，完整私有原生源码/程序在单独 author archive，模型和发布数值 DLL 外置。必须先验证恢复物身份；不能把一份公开源码说成完整 CUDA 可重建交付。

三家族共用最终冻结 core、发布数值 DLL、HTTP 前端和有效设置。工程阶段允许为 runner、记录写入及已定义 dense Llama 形状作有来源的结构性补齐；所有版本保留，Qwen 分支保留，算法、dtype、数值库、mask 集合不得改变。新增数值栈或超出原 dense Llama patch 的算法/架构变更为 STACK_INCOMPATIBLE。不能换最新 llama.cpp 求快。

## 2. 零 forward 资产预检与 F0A

ASSETS 固定三个 pair，新增 Llama 不因速度、分歧、接受率或 OOM 后换家族、draft 或量化。公开转换来源及 license、revision、完整 bytes/SHA256、所有 GGUF tokenizer 字段、runtime 原生 token bytes/type/BOS/EOS/EOG/add flags、官方访问状态及无法认证的原始权重血缘分别记录。保留原生 compatibility guard；静态字段相等不能代替实际 guard 或输出资格。

固定 `ctx1024, logical_batch2048, FA off, F16 K/V, single seq, threads24, full GPU offload`。greedy、target request seed123、cap128、无跨请求 cache；家族自己的原生 EOG/suppression，不复制 Qwen 的 token 列表。实际 draft sampler 按 PR #80 构造行为审计；rank0 proposal、p_min0、minimum0、maximum k，不能把 target seed 当 draft constructor seed。

Llama 两文件共 9,861,858,848 B；ctx1024 的 F16 KV 预算目标 134,217,728 B、草稿 33,554,432 B。固定预估准入公式：文件 bytes 和 + KV + `max(512MiB,三次10秒间隔的最大 idle GPU used)` + 512MiB graph/workspace reserve + 512MiB safety <= 实际 total VRAM。idle 时关闭本任务先前服务。随后零 forward 加载，实际 full-offload 日志、分配/reservation和可用显存 >=512MiB 再核验；不能拿 GGUF 文件大小当实际 GPU 分配证明。reserve 是准入预算，真实 graph 分配与 workspace 仍在工程阶段检查。

未过准入为 MEMORY_OR_ASSET_BLOCKED；不允许偷偷 partial offload、改 ctx/precision 或以低精度新文件替代。某家族 blocked 不解锁第四家族，也不妨碍其他家族独立交付，但原三家族研究缺口明列。ctx1024 是本研究事前约束，与旧 ctx4096 费用不可拼接。没有声称官方受限资产已获本机授权或完整下载验证。

F0A 必须在本轮任何模型 forward（含 synthetic、warmup、旧 probe）之前 commit/push 并独立远端读回：资产选择、来源、模板、候选集合、输入审核及名单、日期与统计规则、预算、已读 design SHA。零 forward tokenizer/load 操作允许；有隐藏 warmup 的载入工具不是零 forward。若输入无法冻结，停在 INPUT_POOL_BLOCKED。

## 3. 新输入和统一模板

总共 24 个原始用户输入：12 MBPP coding、12 GSM8K math。每个家族用自己的**目标**模板渲染一次；同一 pair 的 target/draft 使用完全相同 prompt IDs。Llama 目标/草稿的 GGUF chat template 并不相同，不分别渲染。Qwen 禁用 thinking，其他家族不制造不存在的 thinking 参数。

MBPP 使用旧官方 sanitized revision `e49bbfe381c9c0e564b937f1c4e163a2273c65cc`，test IDs11..510；沿用 RTX 的 description-only 用户模板，不传答案、tests、canonical solution 或历史输出。GSM8K 使用作者仓库 `openai/grade-school-math` commit `3101c7d5072418e28b9008a6636bde82a006892c` 的 `grade_school_math/data/test.jsonl`，SHA256 `3730d312f6e3440559ace48831e51066acaca737f6eabec99bccb9e4b3c39d14`，1319 行；稳定 ID 为 `GSM8K/test/<zero-based-line-index>`。GSM 用户模板精确为 `Solve the following problem and explain your reasoning.\n\n` + 原 question。answer 字段离线隔离，runner 不可读取；不测功能准确率。

审计 main、相关分支/PR #79–#82、所有可访问 host run/archive 与已有 input/exposure ledgers，特别排除 RTX #80 与 B570 #82 的 24-task confirmation、所有 discovery 和当前其他研究的 reservation。任何既往 model forward/proposal/logit/replay 曝光、重复原文、身份含糊或跨 panel 重复都排除。列明不可访问历史和无法扫描范围；只声称在所审计范围内 held-out，不声称未出现在训练或未知私有材料中。

在本轮模型输出前，对三家族只做分词，若任一目标或草稿的真实格式化 prompt >768 IDs、空输入、template 不可用或 prompt 不一致，事前按静态理由排除。768+128 留给 pending/verify 的余量足以容纳 ctx1024；确认中不得截 prompt 或改 cap。按家族无关固定 salt `heterospec-jsa-third-family-20261011-v1|<domain>|<full_task_id>` 的 UTF8 SHA256 升序（ties按full ID）各取12。保存完整 eligible/exclusion 清单、分词、原始/渲染 bytes、IDs/hash、来源。任何领域不足12即 INPUT_POOL_BLOCKED，不用少分母替代。

三个家族共同使用这24个原始问题，在本研究中分别实付 R；不同家族不要求输出等于彼此，也不按 token/s 池化。输入是新 study 的确认 panel，不可用于预试、调参、抓 divergence 或 warmup。

## 4. 条件、有限工程与 F0B

| 名称 | mask | spec | target UB | 最大草稿 k |
|---|---:|---|---:|---:|
| R | 0 | off | 1 | 0 |
| N | 0 | on | 4 | 3 |
| M3 | 3 | off | 4 | 0 |
| C3_K3 | 3 | on | 4 | 3 |
| C3_K1 | 3 | on | 4 | 1 |
| C3_K2 | 3 | on | 4 | 2 |

mask3 始终只作用 target prefill 与 target continuation，draft mask bits 关闭。所有 speculative draft UB1。K1/K2 改变最大草稿长度，**不是** PR #80 的 mask1/mask2。M3 和三种 C 使用相同 target 图/作用域、UB capacity、数值栈与采样；query 数不同是推测方法本身的工作，不冒称逐调用相同。R/M 无 draft decode；草稿加载/residency及在线工作属于推测增量的真实费用。

每家族用原 RTX 12 个 exposed discovery 输入（HumanEval/15,/25,/18,/31 + B_INPUTS 原序前8 MBPP）对全部六条件做2轮，共 `3*12*6*2=432` 请求。同时用2个固定旧/synthetic probe 对每家族六条件做 capture-on/off 一对，共72额外请求；共504计划工程请求，工程硬上限640包含所有测试及工程 warmup。只在旧/exposed/synthetic 上有限修复，不搜索新 masks、UB、drafter、精度或任务。

检查 reset、无跨请求 cached tokens、prefill/continuation作用域、graph reuse key、目标和草稿实际分支/shape（Llama head_dim128/64）、proposal/bonus/correction/EOG/cap 边界以及原生数组。capture 开关和最小 counters 开关不得改变已观察原生输出。旧 partial-block writer 失败要在工程阶段排查：单一 writer、每请求唯一输出路径、完成记录不可变、monitor 只读已完成记录；测试元数据写入、退出和恢复。不能默认锁持有者或声称问题已解决。

预定 engineering capture 完成后，冻结最终原生源码/二进制/DLL、runner、模板、全部有效参数、完整 slot schedule、日期、timer/statistic代码、已知工程分歧与形状证据，生成 F0B 并远端读回。**科学性 divergence 或慢不删除任何一个已定义条件**；完整记录它并继续确认。实际实现/shape unsupported 则标记受影响条件 IMPLEMENTATION_BLOCKED，不能虚构计划请求已执行。确认开始后不改代码和任何规则。确认 k1/2 全部报告，不按工程或正式时间选一个赢家。

## 5. 六个独立日期与请求安排

F0A 事前列明 Asia/Shanghai 六个不同日历日期与窗口，相邻日期首窗口至少20小时，14个日历日内完成；不把24轮、三个family或数千请求当独立日期。每日期每家族一个会话，前一会话所有服务/contexts关闭，重新建服务和固定 synthetic warmup。模型载入/warmup另记，不进入 resident primary timer。

family 顺序为 `[Qwen,SmolLM2,Llama]`，第 d 日期循环左移 `d mod3`（d=0..5），每家族各占每个位置两次。四轮条件基序固定为 `[R,N,M3,C3_K3,C3_K1,C3_K2]`、其反序、该基序左移3位、左移3位后的反序；第 d 日期对这四行各自统一再左移 `d` 位。每家族每日期4轮、每轮6个条件 block；每个 block 新 resident server、1个固定 cap32 synthetic warmup、按同一 task 顺序执行24次 cap128请求。R、M3、C3_K3 在每日期的位置多重集完全相同，六日期总体每条件在每位置出现4次。N和k1的次检验不具有每日期的相同位置多重集，保留这一限制及顺序明细，不能从较好次检验改选主配置。

task 顺序按 `heterospec-jsa-third-family-20261011-v1|order|<d>|<r>|<full_task_id>` SHA256 排序（ties按ID），该日期/轮在三个family和全部条件相同。任务输入本身不变。

固定 AC、原功率策略、无其他 GPU 任务、无并行 build/audit 的资源竞争。每 block 前 idle120秒，随后3次10秒间隔观测：util<=5%、温度<=55C、三次温差<=2C，最多600秒；不根据已观察收益改变准入。缺失遥测及 host/power/driver变化显式记录，不能静默当通过。准入失败记 block 缺失，不补有利窗口。

正式 `3 families*24 tasks*6 conditions*4 rounds*6 dates=10,368`；warmups `3*6*4*6=432`；formal block/server 数432。每家族每条件计划576个实际请求。只计实际 started requests 及进程生命周期，不把分解/replay重复计为新的独立实验。预算为工程640完整请求、128辅助decode/8小时，自有正式进程24小时、14日；总 started 完整请求最多11,440，额外12,000是防错硬停止而非可用于补跑的额度。主机等待无服务时不算自有 GPU 进程寿命，服务 idle/warmup/loading均算。

## 6. 资格与缺失：事前按比较绑定

primary correctness 是 **全部 runtime-native committed output IDs** 与相同 family 的实际 ordinary R 完整数组相同，含实际 terminal、length、stop reason。运行 cap128、首 EOG 语义一并检查；原生记录存在 suffix 时全部保留并计费，不能在分析中截到 EOG/cap 来取得 primary 合格。另报告 endpoint/suffix 作为诊断，不以 endpoint pass 代替 raw pass。proposal/KV 中未提交的 token 与 committed 输出分列，不从文本重分词造数组。

每家族全部576个 R 必须完整且同一 task 跨轮/日期稳定；每条件全部576 slots完整、按所有 paid R检查、重复稳定才能获得 whole-panel 资格。任意 mismatch 就不合格，无 majority/reference替换、无通过子集速度。R不稳定使该family的所有reference比较不合格。

新研究**预先采用比较所需条件的完整性 gate**：M3/C3_K3 要求 R、M3、C3_K3 全部六日期完整并合格；N 或 C3_K1 的失败/缺失不会消除一个已完整的 R/M3/C3_K3 比较。R/C 只要求 R和该C；R/M只要求R/M。这与旧 PR #80 的 global-matrix freeze 不同，仅适用于本新研究；不得回填改判旧结果。每个失败或缺失条件仍在总表和完整 ledger 中。

操作 crash、timeout、metadata写入失败、准入失败：保留每个 STARTED/MISSING/FAILED slot与证据，不自动补跑正式请求、条件或日期。已付费但无法取到完整原生记录的请求不算成功。可以继续剩余独立 slots，不能修好程序后覆盖同一 study。任何受影响 pair 缺日期/请求时，qualified primary speedup和CI为 null；只描述已有绝对成本。修复后的研究另立协议/冻结，不借本预算恢复失败 slots。

## 7. 计时、主检验与解释

唯一主 timer：resident nonstreaming HTTP，client monotonic/perf_counter 从提交前至完整接收并解析 JSON 后，包含 uncached prefill、draft、verify、rollback/correction、sampling、同步及响应；加载/warmup另账。记录 server generation 时间仅在各条件代码边界一致时作 secondary；不可用两个不同 timer 之差推断 host费用。正式关闭 tensor/state/逐token诊断 trace，保留一致最小 native IDs、计数及记录。

每 family/date/task/condition，先取4轮**绝对时间中位数**；每个任务计算 baseline/candidate ratio。24个task的log ratio平均为 day effect z_d。六日期 GM=`exp(mean(z_d))`；95%CI=`exp(mean(z_d) +/- 2.570581835636314 * sample_sd(z_d)/sqrt(6))`，df5。唯一固定主检验是 **Llama M3/C3_K3**。同时列 R/C3_K3、R/M3，Qwen/Smol 对应结果、两个domain、每日期/任务的方向及绝对费用。六日期并不保证足够检验力，也不能外推到随机家族总体。

“有跨日稳定收益”的固定判定：完整资格、95%CI下界>1、至少5/6日期ratio>1。Llama matched成功而ordinary失败，不称普通请求加速；ordinary成功而matched失败，不称草稿加速。Qwen与Llama均在固定k3上通过ordinary和matched规则，才增加两家族的同合同、混合panel收益证据；两个domain各自的效果分别报告，不把混合成功说成两个domain都显著或每任务都受益。

k1/k2 为事前 secondary sensitivity，不能改 primary、从k1/2/3选最大确认GM。对于 `3family*2k*2comparators(R/C,M3/C)=12` 个 secondary comparisons，逐项使用 Bonferroni 99.583333333% 双侧区间（每tail alpha=0.05/24，t分位须由已冻结统计代码计算），report unadjusted95%CI仅作描述。显著正结果只能称该预定 k 的收益，不冒称固定k3迁移。N 不合格时涉及N的qualified ratios为null。

paired R/M/C 的相同聚合满足 R/C=(R/M)*(M/C)，用于费用分解。报告回归task、EOG vs cap分布、长度、acceptance counters及极值，不删除偏差输入或因输出较短重新平衡panel。

## 8. 成本机制、交付与跨平台边界

在exposed工程请求上记录 proposed/accepted/rejected draft IDs 数、bonus/correction数、实际target query-width分布、draft/target prefill/decode/verify/rollback次数、graphreuse及paid state/sync工作。接受率=`accepted draft /proposed draft`，bonus不计为接受draft；每cycle提交产出与prefill pending/最后partial block分开。phase timer若会增加同步，仅限工程报告，不能冒充无trace正式GPU耗时。实际计数/时序不充分时解释为待验证，不用参数比、反分词或微基准替代完整请求成本。

这可区分低接受、高草稿成本、验证形状损失和host调度等相关现象；没有自然 state cross 就不声称唯一算子因果机制。N完全匹配R则为 NO_REPAIR_TRIGGER_OBSERVED，仅说明该panel上不需要该修复，仍可检验费用。

执行端在新的 result draft PR 中先冻结远端并读回，用户已指派执行时随后按协议自动进行，无需额外 PREPARE_ONLY。结果含完整schedule/ledger、版本/assets/input hashes、原生数组、失败与suffix、每family/condition/comparison qualification、费用表/日期CI、计数和scope。提供可复算CPU包及独立恢复/远端读取校验；大源码/程序/日志按author archive保存，weights/数值DLL外置hash绑定。不得写论文中的新结论、升级release或自动merge。

B570不参与本轮RTX主矩阵，也不要求四个平台全跑。B570可以独立做资产、分词和内存预检；新的正式Llama验证需另立Vulkan合同/实现/冻结，不能直接执行CUDA图patch或混入RTX统计。其后复制是否受RTX结果筛选必须如实说明，不能拿条件性复制当无条件跨平台普适性。PR #82 的负结果始终保留。
