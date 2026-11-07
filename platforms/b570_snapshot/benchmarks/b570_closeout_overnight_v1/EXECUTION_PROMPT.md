# HeteroSpec B570：通宵自动值守、跨平台对应验证与有限闭环执行 Prompt

版本：v1，2026-10-06（北京时间）。状态：**待 B570 本机预检与执行，不是已完成实验或已通过测试的程序**。

## 0. 你的任务与授权

你是运行在 Intel Arc B570 本机、能够访问 HeteroSpec 仓库和已有模型/工具的执行代理。用户授权你在今晚连续工作、必要时跑通宵，完成 B570 的这一轮有限实验闭环。请直接实施，不要只给计划、等待论文合并或反复询问常规实现选择。

必须建立在原论文、B570 已封存研究和 RTX 新研究上。目标是回答：**原 B570 数值修复能否迁移到对应输入，在长度/宽度及长驻请求下保留自身参考；是否存在经过独立验证的真实效率提升；哪些过去状态与执行形状构成其适用边界。**不能重新从零证明“投机解码通常能加速”。

本 prompt 授权的是一个**新研究批次**。历史文档里的 CLOSED / PREPARE_ONLY 指其历史批次，不阻止本次明确授权，也不允许覆盖旧研究。可创建隔离 checkout、实现和编译私有前端、使用已有 Vulkan 运行库、写冻结清单、执行模型、修正常规工程问题，并将新代码与派生证据追加到载有本 prompt 的草稿 PR 分支。不要修改本 prompt v1；后续变更另存带时间和理由的 amendment。不要 merge、release、提交会议、修改用户正在整合的论文，或更新驱动/系统、重启、改变永久功耗/超频设置。

“闭环”允许严谨的负结果：核心问题及预定适用边界有完整证据、资格与成本清楚、失败保留、归档可恢复。它不要求制造正加速，不等于普适无损。如果核心阶段因时间、资产或基础设施未完成，必须明确写 **PARTIAL / BLOCKED**，不能用“通宵已结束”代替闭环。

## 1. 固定起点：先读这些实际材料

仓库：`leecdiang/HeteroSpec`。先记录当前 main、当前 prompt PR 的 head/base 和本机工作状态。原论文整合可能继续推进；以下冻结证据不得被移动的 main 替代。

| 材料 | 冻结版本 / 入口 | 用途 |
|---|---|---|
| 本次编写时 main | `e87291d26df32f2cb9571e005ab173b1c7a6830b` | 论文、旧 B570 来源、贡献与数据规则 |
| 已独立审阅 B570 prefill 研究 | `196ed563b36d0e16a3cdb667b6996a4afd98da1d` | 原 native 修复、完整参考、状态转移与 sham |
| RTX 原生状态/局部约束研究 | PR [#59](https://github.com/leecdiang/HeteroSpec/pull/59)，head `b0dfa0fdd5672f55e658fc2265540af778c8f786` | 实际状态交叉、保留批处理的约束、匹配成本 |
| RTX 范围消融 | PR [#60](https://github.com/leecdiang/HeteroSpec/pull/60)，head `ba7f0ae228894ede329e895a6cba396b4cbebaff` | 角色/阶段范围与前瞻合同 |
| RTX 本轮闭环 | PR [#62](https://github.com/leecdiang/HeteroSpec/pull/62)，head `8dfa60a2492e0639a0774f7bac842273485ca26a` | 对应 B/C/D、共享24输入、失败边界、C4效率拒绝 |

必读文件：

- main / B570 冻结版本的 `benchmarks/b570_prefill_diagnostic_v1/{PROTOCOL.json,FREEZE.json,ASSET_MANIFEST.json,STUDY_REPORT.md,DELIVERY_REPORT.md}`；`scripts/platform/b570_prefill_diagnostic_v1/{controller.py,native.cpp,target.cpp,observer.h,generate_sources.py,independent_verify.py}`。
- main 的 `paper/mlsys2027/reviews/b570_prefill_review_20261004/REVIEW_REPORT.md`、当前论文实际源文件、`CONTRIBUTING.md`、`docs/data_policy.md` 和适用的本机 `AGENTS.md`。
- RTX #62 的 `benchmarks/rtx_closeout_bcd/{README.md,REPORT.md,PROTOCOL.md,B_INPUTS.json,C_MANIFEST.json,C4_PREOUTPUT_PLAN.json}` 及 `results/{CLOSEOUT_SUMMARY.json,C_BOUNDARY_SUMMARY.json,C_LOGIT_WITNESSES.json,C4_RESULTS.json,C4_WORK_COUNTS.json,POST_AUDIT.json}`。
- 需要原型时再读 #59/#60 的实际 ggml/llama 图变换实现；不要仅根据报告的 mask 名称实现它。

优先使用 B570 本机已有工作与封存原始记录。旧路径 `C:/hs/b570-prefill-v1`、`C:/hs/b570-prefill-build/Release`、原 `C:/Users/DIANG/Documents/ChatGPT/HeteroSpec` 只是定位线索，不保证存在；将实际路径写入可配置的 `HETEROSPEC_*` 绑定。缺本地原始证据时按 B570 `DELIVERY_REPORT.md` 的固定版本恢复入口恢复；不要重复下载已有且哈希相符的巨型包。

## 2. 已知事实：带入经验，不带入答案

**B570 旧事实**：固定 B570/Vulkan、Qwen3-8B/0.6B Q8_0、greedy seed123 下，原 k2 native 的 N0/R 为60/72；目标预填充 UB1→UB128，在源上下文采样首个 pending token，携带真实 KV、克隆的 post-sample sampler 转入 UB1 继续生成的 N1/R 为72/72。修复 HumanEval/134、42、145、138，20个控制无回归。草稿仍为 UB1。24个任务均已暴露；旧研究没有合格速度结论。

该动作不是“把草稿 prefill 改成128”。旧 R 是 B570 自己的 ordinary CLI/reference 契约，不能改成 RTX 的 global-UB1 参考。原 H1/target 与 native 的 prefill caller grouping 不同，native 为 `prompt[:-1]` 后 `prompt[-1]`；预测迁移通过不证明 caller 完全相同。opaque sampler 字节认证、唯一 Vulkan kernel 根因尚未由旧研究证明。

**RTX 新事实**：目标 prefill+continuation 的局部约束在24个锁定 MBPP 任务通过；k3/UB4 的生成/整请求速度相对匹配目标为1.1692x/1.0351x，长驻为1.1812x/1.0385x。相对全范围方案额外生成收益1.0154x，未达3%门槛。原 C 同时变 k 和 UB；UB6/8 在 MBPP/229 失败，旧 /18 连 target-alone 也失败。约束更多不保证更正确。

RTX 的自然状态交叉在 /229、47个已提交token处显示：换过去状态改变局部 EOS 决策，切当前查询布局不能在该位置修复；当前布局仍改变浮点分数。两个 cap 命中同一任务/边界，不能算两个独立案例。随后固定 UB4，k3/5/7 都通过参考，但 k7/k3 生成0.8294x、整请求0.8899x，四轮都更慢。逻辑调用减少，实际草稿及微图工作却增加。

带入的设计原则是：**记录过去状态来源、当前实际形状和决策裕量；分别检验数值资格与成本；把算法草稿上限 k 与角色/阶段微批容量拆开。**RTX mask3、UB4、k3、参考 token 和速度不能当作 B570 答案。两个平台模型文件确实相同，但后端、初始参考和 caller 契约不同；方法迁移与单变量硬件因果结论要分开。

## 3. 执行边界、时间预算和自动值守

首次启动记录 UTC、北京时间、单调时钟、截止时刻。用户指定截止时刻时优先遵循；没有明确时刻时默认启动后 **10小时**，其中至少 **75分钟**留给验证、归档、恢复、PR回读和最终报告。完成必要工作即可提前结束，不需要耗满通宵。

先用已暴露旧任务做小规模工程资格/耗时估算，禁止用待选新任务输出估算或筛选。估计须包括驻留请求、上下文重置/转移、长输出、编译和归档，不把旧 cold-process 总时间当作 resident decode 延迟。正式新任务执行前一次性冻结预算档：

| 档位 | B共享 / B项目未执行 | C共享主队列 / 旧长输出 | C正式请求 | C原锚点长确认 |
|---|---:|---:|---:|---:|
| FULL（优先） |24 /12|8 /3|792|132|
| NIGHT（ETA需要时） |24 /8|4 /3|504|84|

两档 B 都为4条件×4重复；C 都为4宽度×3上限×3条件×2重复；D 都为24共享任务×2条件×2周期，分别做资格与计时。NIGHT 缩的是预先锁定的队列，不能跑完失败任务后再删样本，也不能写成 RTX 完全相同的8任务 C 队列。若连 NIGHT 核心也无法在预算内完成，冻结诚实的缩减/未完成合同，优先保护核心参考、原锚点、B和D，报告 PARTIAL；不要许诺已闭环。

G0两组164条、B、C、原锚点长确认及D合计：FULL1856 / NIGHT1456条非热身完整请求，另计工程桥接、capture proof、机制辅助、热身和可能的E。依据本机已暴露任务的实测估计每阶段ETA，长输出要单独估计；阶段结束更新预测，到达预留归档线就停止新实验。不能用“还剩很多小时”替代完整候选确认的成本预算。

建立真正可恢复的本地 controller/watchdog：单控制器锁、PID+创建身份、阶段状态机、追加 ledger、每条请求唯一ID、源/参数/输入/资产哈希、原子写入、心跳、硬截止和停止标志。可以在隐藏后台进程中运行，不开可见窗口。默认仅一个 B570 GPU 作业；不要同时编译重负载或运行其他 GPU 任务污染正式计时。

区分 LLM 会话和本地计算进程。不能依靠“之后会自动醒来”的假设；续跑命令、锁核验、阶段恢复必须真实可用。恢复只读取完整且验过哈希的结果，半文件或失联请求不是完成。到时停止新实验、结束自己拥有的子进程，释放临时防睡眠请求，完成部分归档。不要结束用户其它进程。合法但不同的 token 输出是科学失败，**零自动重试**；确实未产生有效科学结果的基础设施失败最多两次、原 attempts 全保留；确定性 crash/OOM 不盲目重复。

## 4. G0：平台资产、原参考、旧动作与新执行器资格

在新隔离研究目录工作；旧模型、原生程序、源码、raw、论文及旧 archives 做前后身份核验。确认实际设备是 Intel Arc B570、后端是现有 Vulkan，完整 offload 没有悄悄转 CPU/其它GPU。记录真实 driver/OS/runtime/编译器/设备及未知项，不用 RTX/CUDA 命令替代 Vulkan 观察。

固定模型身份：

```text
Qwen3-8B-Q8_0.gguf
SHA256 408b955510e196121c1c375201744783b5c9a43c7956d73fc78df54c66e883d6
Qwen3-0.6B-Q8_0.gguf
SHA256 9465e63a22add5354d9bb4b99e90117043c7124007664907259bd16d043bb031
```

不同模型或量化不能悄悄替换。默认沿用旧 B570 的 ctx1024、batch512、FA off、greedy seed123、单请求执行和已验证线程设置；记录线程具体值。ctx4096 和 RTX threads24 不是默认要求：只有资源与资格通过才作为独立扩展，不能因此 OOM 后暗中改变主合同。共享比较明确写出 context、线程、参考和后端仍存在的差异。

先在旧24任务、原模板上新付费生成 R、N0、N1，各两次：144条请求。核对旧 R 契约及稳定性；N0 保留原4失败，N1保持原修复与20控制。再在四诊断任务及 /58 上，对 native caller grouping 的 matched-target T_N1 与 N1 作两次桥接：20条请求。每个实际驻留会话有一条排除热身，另外计数；这些 G0 记录不是正式速度样本。

原 N1 必须正确处理 pending首样本：先从源 logits 采样一次，克隆 post-sample sampler，状态载入目标上下文后消费 pending，不能从没有当前 logits 的新上下文重采样。检查实际序列位置、状态往返、source未变、sampler链/seed/history及其未知认证范围。保留 UB1→UB1 的 plain/sham 控制；已有控制字节可继承的条件是实现与环境身份相符，新 correctness-critical 改动必须补做资格。

新执行器优先在原 native/target 前端上增加驻留模型的逐请求接口、清状态和参数化，不换成另一个“看起来相同”的解码算法。模型加载一次、一次会话热身排除；每个请求都实际重置 KV/sampler/pending/draft/history。状态转移、上下文创建/重置、草稿、验证、rollback、同步及必要cleanup 都进入相应请求费用。普通参考与 matched target 的 grouping差异分别保留；matched target 要与 candidate 有相同目标预填充/转移策略，去掉草稿而非改写为重执行答案。

旧程序硬编码 k2、cap128、ctx1024；支持 k/cap 的新副本需检查完整循环/边界，不得仅删断言。扩展前后做旧参数 bridge，保存 exact diff、build flags、ABI和所有私有执行文件身份。重用绑定 Vulkan 库；不要为了赶进度重写 shader、改精度或绕过多序列/形状限制。

若 G0 失败，先保留失败，在旧任务上最多两个有记录的工程修订解决读写/状态/计时问题。驱动/环境漂移导致历史参考不能复现时写明 `BLOCKED_REFERENCE`；不得取新输出替换历史 R 再宣称修复。G0通过才启动新输入正式生成。

## 5. 输入、暴露审计与封存：两个 B 队列要分开

**B_shared：24个 RTX 对应 MBPP 输入。**从 #62 冻结 head 的 `B_INPUTS.json` 直接读取描述、formatted_prompt及其哈希，核对纯词表 tokenization，不读 RTX 输出当作 B570答案。顺序为：

```text
MBPP/439,415,124,234,441,229,12,458,299,443,18,93,
437,230,253,436,115,133,448,274,454,393,242,397
```

前缀 `MBPP/` 适用于每个编号。这些输入已被 RTX 执行，属于**跨平台共享、项目已暴露输入**；即使首次在B570运行，也不能称为全项目未执行任务。

**B_unused：独立项目未执行 MBPP 队列。**使用与 RTX 相同的官方 sanitized MBPP 固定版本 `e49bbfe381c9c0e564b937f1c4e163a2273c65cc`，文件 SHA256 `ca95deaa9a01ef0a6f439f88bcf0dd3db3563d22f22aad6cae04ebb9a8d8c8e9`。只使用描述，沿用 RTX raw/聊天包装；答案和测试只允许离线来源核验，不能输入模型。

审计本机旧 B570、其它可取得平台历史、当前论文与已合并/未合并相关研究，显式排除 B_shared24、旧 RTX MBPP、旧 B570执行、任务ID/描述命中、重复与含糊记录。不能复用 RTX 当时224候选池而不排除后来已运行的24。下载和明确零前向分词不算生成暴露；缺失可访问历史必须披露，不能宣称审计了不可取得的文件。

在任何这批任务 reference/candidate 前向前，按 SHA256 UTF-8 `(task_id + "HeteroSpec-B570-Closeout-Unused-v1")`、再按ID排序，锁定 FULL12/NIGHT8。保存完整候选/排除及理由、审计范围、输入哈希、词表分词证明、ctx+512预算。合格池不足时使用全体合格候选并标注降级，不能补入已暴露任务冒充 unused。

C主队列取 B_shared 固定顺序首8（FULL）或首4（NIGHT），不依 B 输出选择。C旧长补充优先使用 RTX /49、/81、/31 的**可取得、字节/包装哈希已认证输入**，参考必须在B570另付费生成。如果无法认证这三个输入，在所有新输入生成前，按旧B570 R记录中cap128-limited任务，以 SHA256 UTF-8 `(task_id + "HeteroSpec-B570-Closeout-Long-v1")`、再按ID排序锁定3个本平台旧任务；不足3个则依旧参考实际长度降序、同一哈希破同分补足。标记 `exposed_long_supplement`，不与unused混为一谈，不将 RTX 参考复制过来。

commit源代码与 `PROTOCOL/FREEZE/INPUTS/EXPOSURE/ASSET_MANIFEST`。写精确阶段单位表与 source commit，冻结预算档、结束时刻、长任务、资格/成本选择规则及失败条件；可将源和封存身份推送本PR提供远端检查点，但不得将事后推送时间误写为原前瞻时间证据。

## 6. B：参考恢复迁移与匹配成本

默认固定历史 N1 锚点 **k2、target prefill128、target continuation UB1、draft prefill/continuation UB1**。不要为了与RTX参数表相同直接改k3。两个队列各自检查、各自汇总；4条件为：

| 条件 | 含义 |
|---|---|
| R_reference | B570普通参考路径，独立实际生成；延续原UB128参考的真实prefill/serial-query行为 |
| T_matched | 与N1相同native目标caller、prefill128、pending/状态转入continuation UB1，无草稿 |
| N0_ordinary | 原ordinary native k2，target prefill1→continuation1，同样的sham框架，draft1 |
| N1_repaired | 原修复native k2，target prefill128→continuation1，draft1 |

cap128，4轮循环平衡条件顺序，每轮轮转任务顺序，4×4×(24+n_unused)完整请求；FULL576、NIGHT512，16次排除热身（若为各cohort独立会话则实际warm更多，必须提前写清）。每轮 R独立付费，不从 T/N 输出构造 reference。两队列的稳定性与资格必须分别报告，不能用重复数充当独立任务数。

资格检查完整**声明契约数组**与长度、reason、末ID、首runtime-EOG/cap，并保留原始全数组、全后缀及实际费用。旧B570 native存在128–130个原始ID的overshoot；不能静默删除。共同评分为inclusive-first-runtime-EOG或cap的完整契约，报告raw suffix数量/工作。RTX原生服务没有同样的suffix契约，不能声称两平台完整进程输出完全相同。`n_predict` 与cap的映射要在改动前冻结；禁止按候选结果临时归一化。

N0失败是被保留的科学结果，其成本仅诊断。N1必须与重复稳定的R一致，T也必须通过，才报告合格 N1/T速度；另外报告 N1/R，披露caller/状态框架差异。B_unused若N1失败，不更换任务/参考，不在该队列调参；继续可执行的固定边界与诊断，关闭“新任务全体无损”的成功结论。

## 7. C：角色/阶段分开，实际长度与宽度资格

将参数显式拆成 `target_prefill_ub`、`target_continuation_ub`、`draft_prefill_ub`、`draft_continuation_ub`、`k`；没有角色/阶段控制时先在私有副本实现并资格验证。不能把全局UB或RTX mask名假装成阶段分离。

主矩阵保持 **target prefill128、draft两阶段1**，检查 continuation `(k,UB)=(1,2),(3,4),(5,6),(7,8)`；cap128/256/512，R/T_matched/N_candidate三条件、2轮。FULL 11任务×4×3×3×2=792；NIGHT7任务=504。R每个宽度/cap/轮都实际重新生成；标量/单查询参考需跨宽度标签一致。matched T使用相同候选目标prefill与转移UB，caller grouping固定。

这是与 RTX C 对应的宽度/长度验证，但 B570固定prefill128，避免再次把prefill和continuation容量一起混杂。仍同时变了逻辑k与continuation UB，不能仅凭主矩阵把失败归因于k；E将固定微批做隔离。另保持原 k2/continuation1 的长锚点：原C队列×cap256/512×R/T/N1×2轮，FULL132、NIGHT84；cap128资格来自B，不把更宽失败误当成原锚点失败。

对每个支持宽度观察真实 target/draft、prefill/continuation、caller tokens/positions/seq/logits mask、occupied microquery、图节点和请求重置。cap128桥接到B已支付参考；编译支持、declared capacity、存在某shader源路径均不等于真实执行图或kernel dispatch。capture与必要强同步只用于资格，关闭后另取正式费用。

宽度前端扩展应在正式C前冻结，并在原配置桥接后使用。后台API不支持状态格式/形状时报告UNSUPPORTED及依据，不删除断言伪造支持。每个合法但偏离参考的完整输出保留；失败配置费用不作为无损提速。EOS自然结束，cap512不是“实际跑满512”，逐任务报告参考实际长度与endpoint。

## 8. D：原锚点的长驻请求、清状态与实际速度

使用B共享队列24任务与原k2/continuation1锚点，只在B_shared及C原锚点资格通过时运行。B_unused的科学失败不阻止已合格共享队列的D，但D结论仅覆盖共享队列。两种固定哈希任务排列采用 `(task_id + "HeteroSpec-B570-Closeout-D-v1-cycleN")`、N=1/2。

T_matched / N1两模式、24任务、2周期：先96条capture-enabled资格+4warm，验证每请求目标prefill从位置0、角色/阶段reset、pending无串入、完整参考；再相同96条capture-disabled计时+4warm。每模式/周期一个resident服务，禁用prompt/KV缓存，每请求独立重置；主计时不混入observer同步和巨型状态dump。

记录首末半会话与环境边界观察，但任务差异不能证明热漂移因果。单请求串行resident不是多并发吞吐。原锚点失败则状态写 `GATED_BY_ANCHOR_FAILURE` 并保留失败诊断，不用新的配置冒充原D通过。

## 9. 有限机制诊断：自然状态与当前调用交叉

最多2个失败task/configuration pair，按已冻结的宽度、cap、任务顺序选择。记录是否同任务、同自然切点；重复cap不是新独立案例。先每pair实际跑 R、T、失败native、原修复anchor、普通同配置（必要时去重并记清）。只选择自然到达且共前缀/同caller tokens/positions/seq/logits mask的边界，不强制参考前缀、不送入参考ID或未来proposal tape。

如果真实状态格式可支持，在隔离副本中交叉2个实际donor状态×2个当前路径/微批布局。必须有 source不变、精确状态载入/往返、同一 sampler状态/采样规则、pending/current logits语义、同路径sham复现自然native决策、每次辅助decode计数。维持当次自然proposal和caller；未用旧logits不能被错误消费。异构caller或不对齐前缀不得“对齐后”声称自然反事实。

状态交叉实现不支持时，记录trace/state/logit证据并写 **NOT_CAUSALLY_IDENTIFIED**；不要为了闭环编造机制。已有B570 pending-sample转移控制可以继承合格部分，但opaque sampler字节和driver源码缺失不能写成认证通过。

记录首次分歧处真正top1/top2与指定参考EOS/替代token的logit差，区分这两类margin。当前路径数值改变而离散决策不变，不是“数值无效应”。这些是局部实测证据，不自动成为可部署的误差上界/在线guard/唯一kernel根因。诊断、完整父轨迹、热身和辅助forward费用均单独入账。

## 10. E：基于RTX经验的效率探索，允许一次受控原型

核心B/C/D优先。仅剩余预算足够完成**整个**候选资格、独立成本、长确认和必要长驻检查时启动E正式确认；不能把pilot最优时间当作最终收益。

第一条路径：从C中选择**最小**的 >1 continuation UB，其对应配置在两C队列、所有cap/重复、matched T和native全通过；没有则保持UB1。只用输出/支持资格选择这个UB，不看速度。此UB是候选数值微批，不代表其中每个k已合格。

固定该UB、target prefill128、draft1，试 k∈{1,2,3,5,7}，同时保留原 k2/UB1作原锚点；完全重复配置合并，最多6条件。在固定首8个共享任务和四旧B570诊断任务上作2轮相反顺序pilot，最多144请求+12warm，参考来自已付费稳定R，不能在线输入参考。另做小规模 capture proof确认实际microquery和scope；它的时间不进入pilot成本。

这次允许**输出资格+成本**选择：只在全pilot参考通过的配置中，选 generation task-median GM最高、whole-request≥1、两轮方向都更快且generation≥1.03的非原锚点；再以wall GM、较小k、较小UB破同分。明确它是已暴露选择队列上的探索，不是前瞻速度结论。全部k试验及失败保留。不要重蹈RTX“最高合格k就是最优效率”的错误。

第二条路径（可选、至多一个原型，不与无限扫描并行）：如果宽continuation失败/无有效收益，且本机已有构建链和证据支持局部布局实验，可移植RTX的**目标continuation逐查询注意力布局、保留projection/FFN批处理**思想，target prefill仍保留B570128，draft不变。它是待验证的Vulkan图原型，不是直接复制CUDA内核或mask3。默认guard为已认证模型、FA off、支持宽度、正确KV/序列形状；不对不支持的multi-stream绕断言。

只允许一个数值原型族、至多两个有记录的工程修订，不换精度/模型/采样/输出参考、不调整Vulkan shader算术。新私有核心与原发布Vulkan算子/ABI能安全配合且old-profile bridge通过时才跑。先在同一pilot队列进行自然轨迹、sham、图/状态与完整参考资格，再做独立capture-offpilot成本。原型配置列表须在任何该原型输出前写amendment；如改了算术或前向模型规则则不能继续称为相同语义布局约束。无法在有限时间内实现就明确NOT_IMPLEMENTED，不牺牲核心归档。

两条路径最多选一个候选进入确认；原型与参数pilot均未达门槛时，E=`NO_GO_PILOT`，保留原锚点并停止探索。不根据失败不断加k、重选任务或再造第三个方案。

**独立E确认**：全B队列、4模式（原锚点native、候选native、候选matched T、普通同k/UB配置）、4轮完整循环平衡，FULL576/NIGHT512请求+16warm。pilot共享首8及旧4要与剩余16共享任务、B_unused分组报告；后两者没有该候选调参输出，但之前已在其它配置执行，不能再次称为全项目未执行任务。所有模式均要求自己的参考资格；普通模式失败费用只诊断。

这里“普通同k/UB”必须在E前写明实际实现：默认原ordinary native设置target全局UB为候选continuation UB、draft1、相同k，没有修复性prefill转移或局部图约束；它的target prefill容量因此与候选128不同，必须在对照表披露，不能称为仅切换一个开关的消融。若原前端无法支持该组合，记UNSUPPORTED；候选matched T仍是主要成本控制。原型确认同时保留原锚点私有前端的old-profile bridge，防止核心/ABI改动冒充候选收益。

合格候选再做原C队列 cap256/512 的 R/T/候选、2轮，FULL132/NIGHT84+6warm。若要推荐替代原锚点作resident方案，再按D对24共享任务完整执行候选T/native的96capture+96timing+8warm，不继承原锚点的D资格。剩余预算不足时只称CONFIGURATION_PILOT，不能宣布部署资格。

只有完整参考、长确认、适用范围通过，generation≥1.03x、whole-request≥1x、至少3/4独立确认轮方向更快，才写“比原已验证方案有额外解码收益”。同时报告对候选matched T和普通reference的实际比值。如果输出相同但慢，清楚写无效率收益；如果只prefill/wall快而decode慢，不能包装为decode加速。若普通同配置也合格，给出它这个强基线；若新方案优势只是已知投机收益，要明确新增贡献究竟是什么。

## 11. 所有成本、功耗和统计共同规则

主要速度比为基线耗时/候选耗时；逐任务取重复中位数后求比，再取任务几何平均。共享、项目未执行、旧长补充分开；不能合并相同任务不同cap为独立样本。报告绝对ms、完整请求及生成阶段、每轮方向、每任务分布、草稿/接受数量及比例、目标caller/micrograph/同步/状态转移次数。图观察不是kernel启动数。

generation计时边界在运行前冻结并由实际程序标记，包含生成所需草稿、验证、rollback、首样本转移及同步，不能漏掉原N1 `move()`费用。whole-request包含每请求的prefill、重置/创建/转移、生成与cleanup；模型加载/卸载和热身另账。序列化/反序列化若仍是candidate在线工作必须计时，不能离线免费付掉。推理结束要同步真实设备工作再停止计时。

模型每服务加载一次的resident费用与cold-start总费用分别报告；若resident实现做不出来，只能报告cold边界的费用和限制，不能称RTX相同的resident速度验证。格式化解析开销可分解，但请求实际承担部分不能丢弃。不可用计时字段写missing，不能从有instrumentation的时间“扣出”无instrumentation时间。

固定seed4000次任务重采样可给描述区间，注明选择后/有限面板，不称普适迁移置信区间。真实错误输出没有有效无损速度。能耗仅在已有、可认证且不重叠域的测量支持时报告；Intel package/其它域不能冒充整机/B570板卡功耗，没有可用板卡指标就不报告能耗改进。

## 12. 原始证据、独立验证、交付和闭环状态

每阶段freeze source/head/build、清晰命名所有输入与执行units；保存commands、env白名单、actualdevice、prompt/词表/EOG身份、实际全token输出及suffix、日志、timings、trace/state/logit证据、每attempt、所有失败、热身和辅助调用。新增CPU verifier尽量不导入执行器的比较逻辑，逐项重新算完整数组/endpoint/重复/唯一键/资格/分母/成本。比较controller输出和原始记录，不能只验一行PASS。

后审计模型、旧程序/源码/档案与发布库身份；original资产不变，当前driver/OS变化实记。检查cache为零、prompt准确、无truncation、合法长度/stop、无隐藏oracle、实际role/phase及sourcecommit正确。执行器/数值代码正式修改前commit并重新资格；离线汇总修复记录零模型执行与前后hash，不静默覆盖旧证据。

交付到本prompt PR的独立研究目录：代码、最终协议与amendments、source bindings、exposure summary、derived JSON/CSV、阶段与失败表、共享RTX/B570对应表、中文REPORT、REPRODUCE、DECISION、RESUME/STOP状态及证据manifest。不要改论文或旧PR。不上传权重、运行库二进制、凭据、bulk raw telemetry。完整raw/state/native源码/私有可执行程序放新本地不可变证据包，旧包做单独哈希依赖；远端大块上传仅遵循已有明确仓库交付规则，不以“已有一次例外”自行开新例外。

逐对象SHA/CRC及干净目标恢复必须通过；Windows短研究根目录或扩展路径处理深层源码，Git LF/CRLF不能破坏封存字节。保留新冻结Git history/bundle、原始素材来源及外部资产排除清单。恢复至少验证完整manifest、raw派生再计算、bound private程序和已安装runtime身份；无模型版本检查不能被写成新模型资格。GitHub所有新blob回读核对，diff仅本研究目录，PR保留draft，不merge。

生成 `RTX_B570_COMPARISON`：每行含平台、模型hash、backend/runtime、输入包装/任务hash、reference定义、ctx/threads、k、四role/phase UB与布局、实际query范围、past-state/pending来源、endpoint/suffix契约、队列暴露状态、完整资格、实际长度、速度/计时边界、阶段reset、局部机制证据及未知项。共享24任务提供并列结果与每任务比较；不要把两平台各自不同参考做直接token相等或把归一化速度当绝对硬件因果。

最终每一项标成 `COMPLETED_PASS`、`COMPLETED_SCIENTIFIC_FAIL`、`GATED_BY_QUALIFICATION`、`UNSUPPORTED`、`NOT_RUN_TIME`、`INFRA_BLOCKED`，实际planned/completed/failed/unexecuted/warm/auxiliary分母完整。核心B/C/原锚点D和审计/恢复全部完成，或有原合同规定的科学资格负结果解释相关跳过，才能给对应范围的有限闭环结论；非科学超时/基础设施遗漏仍是PARTIAL。

最终报告必须直接回答：

1. 旧B570 prefill动作是否在本轮保留参考；共享输入和项目未执行输入分别怎样？
2. 哪些k/角色阶段UB/实际长度范围通过，哪些失败或未执行？
3. 原锚点及任何推荐候选是否长驻reset通过？
4. 是否有比原修复native、匹配target及普通reference更好的真实效率，包含全部在线代价？
5. 状态/当前调用证据支持什么，不支持什么；RTX经验哪些迁移、哪些不迁移？
6. 今晚的投入决定是保留旧方案、采用独立合格新候选、拒绝额外速度方向，还是核心未完成？

不要输出录用概率、功能HumanEval正确率、唯一kernel原因或普适最小范围定理。成功与负结果都可闭环，只有真实完成且可恢复的证据才支持宣布本平台该部分闭环。

## 13. 现在开始的顺序

先定位旧B570资产和冻结证据，记录本机/当前PR、开始与截止时间 → 建新隔离工作区和可恢复控制器 → G0/少量已暴露计时资格 → 冻结预算档、两B队列、C长队列和代码 → B → C及原锚点长确认 → D → 按条件做有限诊断/E → independent verify / 后审计 → 不可变打包与实际恢复 → 追加本草稿PR、回读验证 → 输出自包含结论与剩余事项。

当一个门槛失败，执行本合同对应的保留/跳过/诊断分支，继续不依赖它的工作。遇到单纯工程问题先在隔离副本解决。不要为了等人工回复把整晚停在第一条失败日志，也不要为交付漂亮结果改变资格标准。现在开始执行。
