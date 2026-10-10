# JSA_RTX_VALIDATION_V1 执行协议

此文件固定设计规则。执行端须将实际资产、日期、任务、构建和命令解析为独立 manifest 后冻结；本设计不伪造未知的主机身份或 confirmation ID。没有新增实验结果。

## 1. 三个独立研究与范围

| Arm | 问题 | 主工作负载 |
|---|---|---|
| S：session replication | 现有 Qwen matched request 小幅增量是否跨独立会话/日期保持？ | 原 B_INPUTS 的 24 个 exposed MBPP、原四条件、4 rounds、12 sessions/6 dates |
| F：second family | 固定目标阶段修复能否移植；诊断流程在第二图路径上的适用性如何？ | 固定 exposed discovery 与 24 个新的 project-unused confirmation 输入 |
| E：external method | 同栈 LLM-42 adaptation 是否满足 ordinary 输出合同，若满足费用如何？ | 与 F 共用事前锁定的 24 个输入；Qwen 与选定第二家族分别执行 |

F/E 可共用同一 model/task/round 的实际 R/M/C 测量，但每个 record 只能计费一次，报告共享的确切 run IDs；不得把两个报告的计数相加称独立样本。S 与 F/E 的测量、任务身份和估计分开，不池化历史或本轮数据。

## 2. 工程恢复和资产合同

阅读 SOURCE_BINDINGS.json 中的入口，特别是 `benchmarks/rtx_closeout_bcd/{PROTOCOL.md,README.md,RESTORE_WINDOWS.md,SOURCE_BINDINGS.json,B_MANIFEST.json,B_INPUTS.json,close_server.py,run_b.py}` 及 Phase1/Phase2。完整 rehydrate.py 在记录 ZIP 根目录，**不在公开 closeout 目录**。由实际主机定位 CAS archive 与其 Phase1/Phase2 依赖，核对 INDEX/对象 hashes，在新的短路径目录恢复。旧源码里的绝对路径是来源，不是新配置。

S 必须使用原四条件绑定前端、Qwen 权重、33 个发布 DLL、请求模板和有效设置。不能用当前最新 llama.cpp 重新跑后称原配置复测。若原前端或模型无法恢复，S 为 `ASSET_BLOCKED`；可以独立推进 F/E，不用另一套运行栈冒名复测。公开源码不是独立可重建 CUDA 交付。

S 工程桥接使用旧四个 HumanEval probes及四条件，至少16个完整实际请求并离线对照原数组；capture-on/off与reset检查仅用旧输入或synthetic。S 工程上限96完整请求、64辅助decode、4小时active GPU，另计warmups；桥接失败不调修复方案，S为`ORIGINAL_CONFIGURATION_NOT_REPRODUCED`，保留记录。

S 原资产锚点：upstream `0cae43063cf15170e91a2ff4d034da0ecef4a1b2`；target SHA256 `408b955510e196121c1c375201744783b5c9a43c7956d73fc78df54c66e883d6`；draft SHA256 `9465e63a22add5354d9bb4b99e90117043c7124007664907259bd16d043bb031`。具体前端/runner/library 身份从 B 的实际冻结记录解析，不能拿早期 BUILD_NOT_QUALIFIED 的字段当最终程序。

记录实际 GPU 型号/VRAM、Windows build、驱动、运行库、编译器、环境覆盖、AC/功率/风扇策略、线程、K/V 类型、graph reuse、tokenizer、target/draft placement 与实际 offload。保存每文件 hash、构建日志、有效命令、资产来源 revision。新 runner 在新目录；旧研究、归档和论文只读。

F/E 均优先沿用同一 upstream/发布 CUDA 栈；若移植必须更换数值库或后端，终止本轮同栈主对照，记录 `STACK_INCOMPATIBLE`，不能将不同栈数字补入主表。新前端结构性变化允许，但必须列出 patch 和行为映射，R/M/C/E 在同一冻结数值库下实际执行。

## 3. 模型及输入的输出前冻结

F 的 pair 选择顺序固定为 Llama-3.1-8B-Instruct / Llama-3.2-1B-Instruct Q8_0，然后 SmolLM2-1.7B-Instruct / SmolLM2-135M-Instruct Q8_0。输出前检查授权资产存在、完整词表/special tokens、runtime 架构支持、预估全部 GPU offload/ctx4096 内存；按顺序选第一对通过者，立即 commit 模型选择。第二家族任何 forward 后不再换 pair，即使偏差、资格或速度不理想。两者都不能满足时 F 为 `ASSET_OR_COMPATIBILITY_BLOCKED`，不将 Qwen 新规模计作第二家族。

不以关闭 runtime 兼容性检查、修改 tokenizer ID 或越过显式架构 guard 解决不支持。需补 Llama graph 的真实实现，而不是重命名 Qwen 分支。输出后发现工程问题可以在 exposed discovery 上有限修复并保留版本史；confirmation 一旦开始，禁止修复后覆盖原研究。

Discovery 固定 12 个 exposed 输入：HumanEval/15、/25、/18、/31，加旧 B_INPUTS 原序前八个 MBPP。prompt 内容保持既有 description-only 模板，不传入答案、测试、记录 proposal 或未来 reference。各家族用自己的官方 chat template；冻结原字节、格式化字节、prompt IDs、BOS/EOG、hash。各模型的 ordinary R 是其自己的参考，不要求 Llama/Smol 输出等于 Qwen。

Confirmation 使用旧研究同一官方 sanitized MBPP revision `e49bbfe381c9c0e564b937f1c4e163a2273c65cc` 的 test-ID 范围 11..510。新审计覆盖当前 main、相关分支/PR、主机 checkout、run、archive 逻辑成员：任何模型 forward、proposal、logit 或 replay 曝光、重复描述、身份含糊都排除；纯输入/分词不算 forward。不可访问材料和扫描异常明列，无法判断者保守排除。

对完整 eligible pool 按 `SHA256(UTF8("JSA_RTX_VALIDATION_V1|confirmation|20261010|" + full_task_id))` 升序排序，hash 相同按 full ID，选前 24。先锁定 pool/排除理由/任务/输入 hashes，再做任何 F/E confirmation forward。eligible 不足 24 或审计无法完成时 F/E confirmation 为 `INPUT_POOL_BLOCKED`；不减分母、不用 S 的旧输入代替“新输入”，可交付 discovery 和 S。

所有确认输入在 discovery 前锁定。锁定名单本身不算曝光；任何后续 forward 都进入 exposure ledger。确认结果只读，不能成为配置选择依据。

## 4. 完整输出资格

通用配置：greedy，seed123；ctx4096、logical batch2048、FA off、single sequence、无 prompt/KV/result cache、全 GPU offload、threads24；target/draft sampler chain 和实际 draft seed/p_min 从有效实现解析并冻结。跨模型不盲目复制 Qwen token 抑制列表或其 EOG 集。

需要保留同一请求内的live KV，禁止的是跨请求的prompt/result缓存。E自带fast/verifier contexts及其合法KV复制是方法付费工作，不受“只一个context”的假限制；每context只有一个sequence，权重可共享并记录内存。UB按方法条件固定：R1，N/M/C4，E fast4、verifier32。不能让verifier仍用UB4分块后声称实际固定32-query调用。

完整 committed IDs 直到首 EOG（包含）或 cap128，检查数组、长度、terminal ID、stop reason、有效 prompt 和 cached-token=0。只有 runtime 原生 IDs 可用于 exact；不能由文本再分词。原生响应含更长 suffix 时全存，不能截短来通过。数组 digest 为 UTF8 compact JSON integers 的 SHA256；文件 digest 另存。记录首分歧零基位置、两侧 ID（缺失为 null）、长度和终止类型。

每 task/round 的 R 都实际付费生成，跨 rounds/sessions 稳定性独立检查。R 不稳定时该 arm 没有固定参考资格，不用多数票或最常见参考。每候选必须在整个预定 panel/所有重复通过；任意 mismatch 就不合格。不删除问题任务或只分析 passing 子集的“无损”速度。

记录/捕获改动须在 discovery/旧 probes 上验证开关一致；计时关闭 observer/tensor/logit trace，仍保留最小原生输出与统一响应记录。仅有 repeat-stability 不等于 ordinary-reference equality，也不等于 functional correctness、全部 logits 相同或所有输入无损。

## 5. S：六日期、十二独立会话

严格采用旧 B_MANIFEST 的四条件：R=`mask0/spec off/UB1/k0`；M=`mask3/off/UB4/k0`；C3=`mask3/on/UB4/k3`；C15=`mask15/on/UB4/k3`。24 IDs 与输入 bytes/hash 逐项复用原 B_INPUTS，不重新选择。所有历史数组只作离线核验，不能供在线 runner 读取。

在第一次 S formal forward 前列明六个 Asia/Shanghai 日历日期及每日期两个时间窗口（同日开始时间间隔至少 4 小时），不同日期的第一个窗口开始时间至少间隔 20 小时；计划 14 日内完成。每次会话关闭前一会话全部服务/contexts，重新建服务、warmup、独立 GPU/host 状态记录。不是把一次持续会话切成十二份。

每 session 4 rounds；每 round 每条件起一个新 resident server，支付 1 次固定 synthetic warmup（cap32，模板按对应模型冻结），再执行全部 24 tasks。四条件 cyclic orders 使每条件每 session 占每个位置一次；每 session 的初始循环偏移按 session_index mod4，task 顺序按固定 salt `JSA_RTX_VALIDATION_V1|S|session|round|` 加 full ID 哈希排序，各条件同 round 使用同序。清单含精确顺序与 hash。

每条件 block 进入前固定无模型 idle120秒，随后 3 次10秒间隔观察，utilization<=5%、温度<=55C、三次温差<=2C，最大等待600秒；这是主机准入规则，不根据速度/输出延长等待。固定 AC、功率/风扇策略、无其他 GPU 工作；不改驱动、库、model/runner。记录采样值及 unavailable 字段，遥测在请求计时外，不删“看起来热”的正式请求。准入失败该 block 为缺失，保留已跑数据，不补一个有利会话。

总正式请求 `24*4*4*12=4608`，排除但计数 warmups `4*4*12=192`。这复测原 B 的 fresh-server-per-condition/round 模式；不与旧 D 的长期 resident cycles 拼接。S 无输出择优、无参数搜索、无新 family/E 条件。

## 6. F：固定迁移与有限诊断

先在 12 discovery 输入上实际运行重复 R、未修复 native N=`mask0/on/UB4/k3`、固定移植 C3 与 matched M3，每项两次。实现必须维护角色/phase 和 graph reuse key，证明对应分支实际执行。C3 为原目标阶段 recipe 的移植；结构变化详细记录，不能叫零改动迁移。

完整测试 16 个 role/phase masks，各输入两次；非 R 的 native speculative mask0 可与 discovery 已支付 N 共享，明列 run IDs。所有 masks 的结果都报告，有限集合不等于全局最小。

同时测试四种target-only matched controls（目标mask bits为0/1/2/3，UB4、spec off），各输入两次；草稿bits在target-only下不能制造新condition。可以与已支付M3共用确切records。一个mask进入候选合格集合需它及对应target-only control均通过discovery的稳定R；两者资格分列，不能由spec通过反推matched target通过。

输出选择规则只看 discovery 资格：优先保留 C3 为固定迁移主候选；另外从全部通过的 masks 中按 enabled_bit_count、integer_mask 选择一个，若不等于3则作为 Csel，并加入对应 target-only Msel。原 C3 即使失败也保留进确认，不被新候选替换；若没有通过者，不搜索新掩码/宽度，确认仍评价 R/N/M3/C3 的失败边界。选择完全不看费用。

若 discovery 存在 N/R 分歧，对最多两个输入做真实 state × current-path crosses：按 discovery 固定顺序选择首两个；用最后一个自然共同 committed prefix 的可支持 checkpoint；记录两种 donor 的 KV、pending token、positions、mask/phase/call state。两条 own-path shams 必须通过后才解释 cross。不能对齐时交付 `ALIGNMENT_UNSUPPORTED`，不 teacher-force future proposal 或把 token 同前缀等同 KV 同状态。这是局部诊断，不推出唯一 kernel 原因。

Discovery 工程+诊断最多 1,024 次完整请求、2,048 次辅助 decode 和 16 小时 active GPU 时间。仅允许该有限图迁移/16-mask 集合；不得无界调 k、UB、cap 或挑偏差任务。

F/E joint confirmation：第二家族至少 R/N/M3/C3/E32 五条件；有不同 Csel 时另加 Msel/Csel，共七条件。每条件使用相同输入、cap、采样/停止和冻结栈。rounds=condition_count（5 或7），cyclic orders 精确平衡位置；每 round 每条件新 server、一次 cap32 warmup、24 requests。完整矩阵 600 或1,176 正式请求；25 或49 warmups。R actual paid，输出失败不阻止其他条件的资格评估，但所有不合格成本只能作为诊断。

若 E 无法工程实现，F 仍按 R/N/M3/C3 加可选 Msel/Csel 执行；rounds=condition_count（4或6），请求384或864，warmups16或36。这种降级只能在确认首个 forward 前写入独立冻结，不能声称外部缺口已补齐。

## 7. E：LLM42_DVR_GGML_W32

先固定外部官方 repo revision 和所读文件 hashes，制作 `METHOD_MAPPING.md`：列出原方法的 decode、fixed-shape verify、padding、correction/bonus、rollback、verifier-KV 替换，以及本移植对应代码、不同处、缺少的原系统能力。主窗口 W=32、单 request 验证，不调窗口求更好速度；该 W 是本方案选择，不冒称论文唯一默认。

Fast path 是同一个 target 模型的 ordinary greedy decode，不是小 draft 模型，也不是读取离线 R。Verifier 在自己的 consistent state 上采用固定32个有效/填充 query slots；所有末尾短块、EOG、cap均按冻结的 causal padding 规则处理。只提交验证通过的前缀与合法 correction/bonus，拒绝部分 rollback；已验证区域的 continuation KV 来自 verifier，禁止保留 optimistic KV 冒称一致。记录实际 query shapes、KV provenance 和末尾路径。它不使用 HeteroSpec mask3 修复；否则对照变成组合方法，应另命名且不能替代 E。

具体固定W语义：E以自己固定、无inter-request batching的prefill得到首个consistent pending token T0（需检查重复性，不假定与R位一致）；fast path最多生成31个候选。Verifier输入T0及这31个候选，短块用预先固定的有效dummy ID填充到32，真实positions/causal关系保持，填充不得影响更早真实query。首个候选不匹配时，接受之前通过的候选和其前一输入row产生的correction，截断KV到最后一个已正确处理的输入；全部候选通过时，可以接受末row产生的bonus，但不得越过首EOG/cap。dummy对应输出与KV不得提交，padding/correction/bonus endpoint规则须有真实fixtures。下一块从verifier的已验证KV及pending token继续；fast speculative KV丢弃，复制/同步的实际成本计入。该展开是本方案的单request GGML映射，METHOD_MAPPING必须保留与原实现的区别。

需先验证 prefix/causality、padding 不改变真实 query、accept/correction/bonus、每种 rollback、EOG 在首/中/末位置、cap 截止、request reset、graph reuse；若不能保证固定形状/一致状态的实际实现，E 为 `IMPLEMENTATION_BLOCKED`，不能把仅记录“verified”的伪实现算外部方法。

每模型的 external engineering 最多128完整请求、256辅助 decode；总 engineering cap256完整/512辅助、16小时 active GPU。仅使用 discovery/已曝光或明确非数据集 synthetic fixtures。预算耗尽停止 E，F/S 可独立完成。不克隆庞大引擎、安装新系统环境后替代同栈评估。

Qwen E confirmation 共 R/N/M3/C3/E32 五条件，24 inputs、5 balanced rounds=600正式/25warmups。第二家族的 E 与 F joint matrix 共享对应实际记录。若只 Qwen 支持 E，明确缺失家族，不能宣称两家族完成外部对照。

每模型先报告 E repeat-stability 和 E/R complete equality，再报告 qualified cost。如果 E 输出稳定但不等于 R，状态为 `COMPLETE_CONTRACT_MISMATCH`；保留完整分歧和计时，qualified speedup/CI 为 null，不更改参考去让它通过。结果表同时列 HeteroSpec C3 的同一 gate，不能以移植的不合格证明原外部系统错误或全面劣于本方法。

成本计入额外 target decode、verify、padding、KV replacement/rollback、sampling和host调度/同步。不得免费缓存 reference/KV，或以离线预生成 proposal 去掉 decode 成本。加载及 warmup 分账，resident request 的统一 client boundary 必须覆盖 E 的全部付费工作。

## 8. 计时与统计

Primary timer 是非流式 resident HTTP request：client monotonic/perf_counter 在提交请求前开始，完整响应接收并解析后结束；包括未缓存 prefill、生成和响应，不包括冷加载/teardown/规定 warmup。记录 server 原 predicted_ms 作为 secondary，但不同代码路径只有在 SOURCE_TIMER_AUDIT 证实同一边界时才作 generation ratio。否则 generation comparison=null，仍可比较统一 request timer；不能把两计时差相减当 host 成本。

S 从每 session/task/condition 四轮的**绝对时间中位数**算 baseline/candidate ratio；24 task log ratios 平均为 session log effect。每日期两个 session log effects 平均为 day effect z_d。主效应 `exp(mean(z_d))`；六个完整日期的95%区间 `exp(mean(z_d) ± t(0.975,5)*sd(z_d)/sqrt(6))`，t critical=2.570581835636314。所有六日期/十二会话必须完整且该 pair 全部 output-qualified 才产生主区间。两个 sessions 不当作两个独立日期；4,608 requests不当作4,608独立样本。

S 唯一 primary comparison 为 M/C3 request；R/C3、R/M、C15/C3 和 generation 为 secondary，不转成新 primary。稳定正增量的预定判定：完整资格及矩阵，主区间下界>1，且至少5/6 day effects>0。GM>1但区间跨1为 `INCONCLUSIVE_POSITIVE_INCREMENT`；未通过方向/资格则分别报告，不许挑较好 timer。另报 day/session ratios、绝对时间、每任务回归、round方向、leave-one-day-out，以及日期趋势；小样本/独立日期假设限制保留。

S主比较要求R稳定且M/C3各完整通过；C15的独立输出失败保留并阻断涉及C15的合格比较，不将其失败自动转成M/C3失败。任何slot操作缺失仍使完整S主矩阵不成立。

F/E 在各模型/矩阵内对每 task/condition 的绝对时间跨 rounds 取中位数，形成 ratios、24-task GM，分别报 R/C、M/C、R/M、R/E，外部 E 与 C 只有二者及相关 matched control 合格时才比较。10,000 task bootstrap，NumPy PCG64 seed20261010，paired task整行同索引、type7 quantile，仅 descriptive，不能替代 S 日期间隔或外推。

若 F/E candidate fail，speedup=null，保留绝对成本及 mismatch；任务因操作异常缺失，不做成功子集主 ratio、不插补。功能准确率、能耗和并发 throughput 本轮不测。

## 9. 冻结、失败与交付

按 arm 建立 F0 manifests，包含 design/head SHA、实际 starting SHA、assets/build/code/inputs/日期/完整 schedule/timer/statistic/missing/stopping identities；commit并push，独立读取远端 SHA确认后自动进入相应执行。F 的资产/confirmation-input名单在 discovery前冻结，候选与实现及joint schedule在confirmation前另冻结。S 不等待 E 成功，E 不由 F 成功解锁；不可变文件漂移只阻断受影响 arm。

首个 confirmation 输出后不修改该 arm 的实现、参考、名单、矩阵或分析规则。崩溃、超时、host准入失败保留 run slot及日志，**本研究不自动补跑正式请求/会话**；余下独立 slots可继续，完成的但不完整 arm仅描述，不升级为完整收益验证。参考不稳定或输出 mismatch是科学结果，不当作可静默重试的操作错误。任何修复后研究用新protocol和新研究标识，原结果保留；不在当前研究无限扩展。

工程阶段无法实现的graph/recipe与有效实现产生的输出不匹配分开：前者为unsupported/blocked，后者才是所测试recipe的资格阴性。不能强行越过guard跑出错误结果后将其称为科学迁移失败。

总 formal budget 上限7,000完整请求（S4,608 + Qwen E600 + family最大1,176，剩余不用于搜索）；formal active GPU上限48小时，14日calendar窗口不含首次工程准备。各 arm分别列计划、完成、失败、未到达、warmup、辅助decode、实际时间。预算中断为 incomplete，不造数据补满。

交付新实验目录 `benchmarks/jsa_rtx_validation_v1/` 和新实现 `scripts/platform/jsa_rtx_validation_v1/`。至少包含：READ_RECEIPTS、ASSET_CHECK、EXPOSURE_AUDIT、MODEL_CHOICE、DISCOVERY、各F0/远端receipt、METHOD_MAPPING、命令/构建/日程、完整slot账本、逐任务/会话/日期CSV、QUALIFICATION、REPORT、独立CPU verifier、hash manifest和REPRODUCE。完整原始 arrays、trace、source/build可复核 archive 内容寻址保存并按docs/data_policy管理，不能只有digest或口头说“原始数据在本地”。给出作者可访问位置、完整SHA及重建方法，不把权重/凭证/大目录提交Git。

独立CPU verifier不得仅调用runner的统计函数；从原始逐条数组、timer和slot ledger重算资格/成本/汇总。汇总区别三个缺口的完成度。创建/更新本研究 Draft result PR；不merge、不写论文阳性结论、不发布/投稿。无论正负都完成可审核交付。
