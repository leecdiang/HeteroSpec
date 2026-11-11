# B570 独立执行协议

数值设计在 [DESIGN.json](DESIGN.json)。本协议定义资格、冻结时点、失败处理和报告合同。只在新研究根目录执行，保留旧证据和数值资产身份。

## 1. 恢复与 Qwen 桥接

从本 PR exact head 建立新实验分支/目录，例如 `benchmarks/jsa_b570_validation_v1/`。从旧 CAS/source-history 恢复需要的资产并做独立 CPU 验证。不得直接启动旧自动执行器、复用旧槽位或补跑 E 缺失项。

核对原 GGML/Vulkan 数值运行库、shader、编译参数、driver。旧 driver 为 `32.0.101.9034`，实际值独立记录；无法恢复旧值则桥接属于新合同复测。禁止为寻找通过结果自动更新 driver 或数值栈。私有 candidate DLL 与原 DLL 分开存放，绑定实际加载模块路径/哈希；新 DLL 不能标为原资产。R/N 保留原普通/原 speculative 路径，M/C 只用既有 phase-binding 结构补丁；跨模型工程仅支持模型中立 IO、动态元数据及真实 KV schema，不改算子、精度、shader、采样和 accept/bonus/rollback。

执行前冻结 4 已暴露探针 × R/N/M/C × capture on/off，共32请求。每条路径核对自己的历史端点和 raw 数组，已知 N/R 差异和 C/R suffix 不算新增桥接失败；on/off 必须同路径等价，R 和 C 必须恢复各自历史端点。历史 raw 未完整留存写 UNKNOWN。任何历史身份或 observer 等价失败停止新家族 GPU 请求，保留失败凭证；不能把编译成功当数值资格。无法恢复原运行库交付 `UNSUPPORTED_PINNED_ASSETS`。

## 2. 第二家族资产、输入与 F0

唯一模型对是快照中的 SmolLM2-1.7B/135M Instruct Q8_0；不设输出后的模型备选。下载或复用相同文件并逐字节验 SHA256。重新核对 actual vocab 每个 ID 的 text/type、全部 added/special tokens、BOS/EOS/EOG 和 tokenizer flags，不能只比词表大小。保留 native compatibility 检查，不放宽断言。用 target 实际 chat template，冻结原始 user/formatted UTF-8、token IDs 和 hashes；R/N/M/C 共用完全相同 IDs。

F0 前记录本方案与 RTX #80 的最新相关 PR heads，保留 [COORDINATION_SNAPSHOT.json](COORDINATION_SNAPSHOT.json) 的初始 pinned 证据。增量审计主库、相关已关闭/开放 PR、B570 实际执行根目录、结果-bearing archives、失败 attempts 和 warmups。下载的全数据集和候选人口文件不等于全部执行；其他研究的selected/reserved、已观察、错误记录及歧义证据保守排除。本研究尚无forward的唯一自有预留以availability-only记录，不因预留本身排除自己；任何实际输出仍计暴露。按 task ID 与 description hash 双重核对，并排除 RTX 全部已计划/已执行确认任务。

初始24 ID 只是**暂定预留**。从快照 `remaining_ranked_candidates` 按固定顺序取首24个通过新增暴露审计的任务，保留每项排除证据。这个候选人口不能用于发现调试或 warmup。不足24则记录 `INCOMPLETE_EXPOSURE_AUDIT`，只继续已暴露的发现/诊断；不能把“B570 未跑过”称为“项目未用”。不可访问的私有主机明确列为未知，不能借 RTX 审计代替 B570 本机审计。

**任何 SmolLM2 forward 前**，冻结模型/tokenizer、12发现任务、24确认任务（或无法冻结原因）、源码/二进制/模块、设备/合同、计时边界、warmup/所有请求顺序和 budgets。创建结果 Draft PR、推送 F0并从 GitHub 核验 exact head。冻结后自动继续用户已授权的有限执行，不额外停在 PREPARE_ONLY；不能见过发现输出后再选确认队列。初始化自动 warmup 要关闭或逐次列为预算内请求/辅助 decode，禁止隐藏 forward。

每次 generation 前用唯一物理设备名和实际加载日志确认 Arc B570；目标/draft 全部层 offload，层数动态读取，不沿用37/37、29/29。ctx1024/batch512/threads10、FA off、greedy123、seq0、单请求；核对effective sampling无额外repeat/frequency/presence/dry惩罚、grammar、mirostat或reasoning控制（repeat penalty=1，其余禁用），与原greedy恢复范围一致；prompt+cap+k+原实现预留必须适配 context。OOM、partial offload或架构不支持记 UNSUPPORTED，不改量化、CPU fallback 或模型。

## 3. 四条件实现身份

| 条件 | target prefill / continuation | 路径 |
|---|---|---|
| R | UB128 / UB128 | 原普通 target-only，新模型付费参考；原 prompt/sampler/output-reservation construction |
| N | UB128 / UB1；draftUB1、k2 | PR63 old_N1 的最小模型中立移植，保留原 speculative 状态和接受规则 |
| M | UB128→UB1，同 context | PR64 matched target-only；candidate reservation512/per-seq1，保留 live sampler/pending 首 token |
| C | M 的构建与 phase binding；draftUB1、k2 | 唯一 PR64 CANONICAL_PREFILL_INPLACE_PHASE_BINDING speculative 候选 |

R 不是 RTX scalarUB1，也不是 M。N 不加入新修复后冒充原 native。M/C 在 ordinary prompt 构建、已采样 pending 首 token 后原位绑定；不重建目标context、转移/teacher-recompute KV或重采首token。保存 actual recipe，包括 output reservation；联动改变不能描述为纯 UB 干预。

旧 runner 的 Qwen 路径、151936/EOG、层数、prompt template、旧预算和 study-root 全部替换为本轮显式冻结元数据。仅在该源码版本尚无 Smol forward且不改变数值语义时进行 IO/动态元数据工程修复并重封F0；发现输出后不改数值实现。CPU输出解析修复只能重算原payload，记录前后hash，不重跑请求。原 `n_predict=127` 等须按caller首token语义审计；实际端点必须明确为首EOG/128，不能只看命令参数。

## 4. 有限发现与自然状态干预

12任务按 DESIGN 固定顺序，均曾在项目暴露；四条件两轮共96请求。保存端点/raw、稳定性、first divergence、长度和成本。C/N/M 与 R 的数值 mismatch 是有效结果，不换候选。R不稳定、payload缺失或capture改变输出属于工程资格失败。

另外每条件固定首4发现任务做 capture on/off 工程对照，共32请求；与96发现off输出核对。同一 arm 的 raw IDs/EOG/长度/停止语义必须相同。observer 改变输出则 `UNSUPPORTED_OBSERVER` 并停止确认，不挑其他恰好通过的探针。

若出现 R/N 或 R/C 端点差异，按锁定任务顺序取最先至多两个具有自然 N/C 对齐checkpoint的任务，每项最多两重复。用实际执行达到的、分叉前最近共同 committed-prefix checkpoint，窗口divergence前16至divergence，固定选择最近合法边界。所有考虑过的任务/未对齐理由保留；无共同边界记 `NO_ALIGNED_NATURAL_CHECKPOINT`，无分叉记 `NO_TRIGGER`。不强制参考prefix、不扫新任务、不使用确认队列。

比较两种真实 target KV数值状态 × 两种当前完整target recipe。logical query batch 来自一条实际donor路径并在四格相同，来源记录。先通过两个 donor 的完整 raw own-path continuation sham；逐字节验证 KV/位置/seq ownership、API restore roundtrip、source-after不变。冻结actual greedy sampler可恢复范围和pending/proposal/position；opaque sampler bytes无法恢复写UNAVAILABLE，不宣称一般随机采样恢复。按真实架构解析 KV和全部float32 vocab行，禁止Qwen宽度重解释。argmax、margin、分数差和非加性全保留，重复列/无argmax flip也报告。

主要cross最多2任务×2重复×4格=16辅助decode；其余控制/roundtrip共用64辅助上限。自然donor和完整sham计入256工程请求上限。机制恢复失败只使诊断支路UNSUPPORTED，不使已独立合格的输出/成本失效；不证明唯一operator根因或整条counterfactual修复。

## 5. 确认、资格与成本

确认工程门：资产/设备/Qwen桥接、固定R稳定性、四条件on/off等价、完整payload、付费计时、F0及暴露审计通过。**C/N/M的数值差异不取消矩阵**；384请求用于预注册正/负特征测量。确认输入一旦forward，禁止换任务、删失败、换模型/候选、增轮或改seed。

确认前只刷新相关PR的cohort/暴露元数据并记录heads/时间；不看RTX科学结果来调配方。最终24若与新预留/已执行集合冲突，或存在task-ID/description层面的暴露歧义，停止fresh-confirmation支路，记 `CONFIRMATION_RESERVATION_CONFLICT`；此时不在已见发现输出后换队列，其他支路仍可收尾。一般不可访问主机范围列为审计限制，不据此声称全项目所有主机已证明未用。

四轮四条件，每条件块新建ready resident process，完成后关闭，共**16独立进程会话**，不复用发现context。条件顺序为 R/N/C/M、N/M/R/C、M/C/N/R、C/R/M/N；每轮所有条件共用同一task顺序，冻结24列表按0/6/12/18旋转。每会话1次固定已暴露warmup（首发现任务），共16 warm另记。会话前确认无其他GPU作业，记录driver、设备、时间/温度/可读频率；不自动改电源配置或套RTX温度阈值。允许同日，记录实际日期和session身份。

独立 CPU parser 从 paid payload 读取全部 raw IDs/EOG，再取最早runtime EOG（含）或cap128为正式端点。验证 ID范围、flag与target实际EOG一致、length/stop reason。每arm各轮端点稳定，且24任务每轮端点与同轮paid R完全相同，才能称**冻结队列端点合格**。完整raw的重复稳定性和相等性另设字段；端点pass不提升raw lossless。所有额外suffix计算、拷贝、同步和文件读回收费。

资格按比较对判定：R/C需R和C的24×4矩阵完整且合格；M/C、N/C还分别要求M、N也与R同合同合格。N数值失败不抹去已经完整合格的R/C，但N/C的qualified speedup为null，只可保留明确标为不合格baseline的诊断耗时比。各比较不筛选“恰好通过”的任务子集。

主指标为相同wrapper的host整请求：进程ready后、发送前开始，到完整匹配payload与所需ID/EOG文件读回验证完成；包含reset/phase reserve/draft/verify/sampler/rollback/KV修改、sync和IPC。native whole/generation另审源码边界；旧native whole_end早于observer.finish，不能称完整host时间。cold模型/context创建、进程load/cleanup另记，online phase/context修改必须在付费timer内。instrumented checkpoint/全词表读回不进入性能矩阵；正式最小IDs/EOG记录与检查为四条件一致的付费路径。

每任务取四轮成本中位数，算baseline/C，再按24任务取GM；R/C主比较、M/C和N/C次比较。报告每轮GM、每任务/每轮方向、长度与suffix。某比较对缺失任一冻结请求，其全部24任务的qualified speedup为null；不补零、删任务或拿discovery代替，完整子集诊断显式分母。四条件总矩阵partial与已完整比较对分开报告。不作跨日期tCI，不将四轮当独立日期；小幅改善仅属有限探索性结果，不宣称生产稳健收益，不自动加测日期或轮次。

## 6. 预算、失败与交付

计数以START为准，包括失败/timeout：工程非warm256、正式384、warm64，共704完整请求；辅助target decode64，实际token/图数另记。工程活动GPU8h、确认8h、合计16h；活动时间按所有本研究自有GPU进程会话从创建至退出的墙钟累计，包含load、warmup、sync与会话内等待，不仅是kernel时间。纯CPU准备/下载且无自有GPU进程时不计此活动额度。首个自有GPU会话起7自然日；按最早耗尽项停止，空余不授权新候选。native启动内部warmup/compat试算必须数清或关闭；数不清就不执行。只终止属于本研究PID+creation identity的进程。

每请求追加START、exact epoch、输入/config/source/module hashes、session、完整payload和END/FAILURE。不自动重试已开始科学请求；已有完整payload但缺RESULT先CPU恢复，不重跑。预算或基础设施中断记PARTIAL，缺失显式保留；人工STOP即停止新请求。driver/backend/模型数值身份变更不能沿用旧F0。

结果Draft PR至少含F0/REMOTE_FREEZE_RECEIPT、MODEL_CHOICE、COORDINATION/EXPOSURE_AUDIT、INPUTS/TOKENIZATION、REQUEST_SCHEDULE/LEDGER、SESSION/MODULE/DEVICE/TIMER_BINDINGS、资格和成本全矩阵、自然诊断或未触发原因、DECISION/REPORT、独立CPU verifier与实际结果、CAS hash/index/真实fresh restore和远端readback。独立verifier不导入旧runner的endpoint/qualification/cost函数；验证missing、duplicate、EOG/suffix误资格、ratio反向、不合格成本五类拒绝。GitHub放轻量源码和派生证据，bulk沿用内容寻址交付；不自动merge、改冻结JSA论文或tag/release。最终回报结果PR、exacthead、完整/失败/缺失计数与科学边界。
