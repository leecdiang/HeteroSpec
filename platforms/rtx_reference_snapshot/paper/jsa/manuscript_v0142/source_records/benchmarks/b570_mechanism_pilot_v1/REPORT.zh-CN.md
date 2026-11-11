# B570 真实状态机制交叉与单候选 pilot

本轮科学决定为 **PARTIAL_INFRASTRUCTURE_BUDGET_CLOSED**。E矩阵保留一项预算内中断，实际119/120，不能宣布完整科学矩阵。三个独立任务的自然状态交叉都有效；/145 与 /42 显示历史状态和当前完整路径的交互，/72 在相同当前续写配方下显示状态效应。候选开发阶段12/12合格，在六个已暴露任务上恢复/72并保留五个旧参考；完整原始数组的观测开关稳定。 完整平台外推和实际加速必须分别由后续门槛判定。

这是 PR63 规范审核完成之后的一轮新有限研究。外部科学 snapshot 固定为 `66594b349955e66146702325559c26019ea16485`，新公开分支基于实际 main `e87291d26df32f2cb9571e005ab173b1c7a6830b`；没有合并任何 PR，也没有修改论文、旧研究、原模型、发布 runtime、驱动、电源或桌面程序。

## 实际单位与门控

| 阶段 | 完成 / 预定上限 | 判定 |
|---|---:|---|
| 0 | 1993历史记录、66 CSV /744成本行、153资产 | PASS；零模型请求 |
| A | 48/48完整生成 | PASS；已取得历史完整数组及端点保留；历史缺失的父轨迹明确标为本轮新父 |
| B | 12/12完整sham；24/24辅助target调用 | PASS；三个独立任务、两轮有效交叉 |
| C | 12/12完整生成 | PASS |
| D | 112/112完整生成 | PASS；全部56输入已暴露 |
| E | 127/128预算内完整生成 | PARTIAL_INFRASTRUCTURE_BUDGET_CLOSED；若运行，8诊断桥接+15任务×4条件×2轮 |

非热身开始/完成：312/311，上限312；排除但计费热身：37/37，上限48；辅助 target 调用：24/24，上限24。失败和中断同样计入开始数，没有科学重跑。每个请求保留完整原始 IDs、EOG、cap端点及越界 suffix；所有生成后截断的 suffix 仍占原始费用，未隐藏费用或选择成功子集。

## 中断及闭环范围

E预定120个正式位置，实际119份完整记录；另有1次old_N1第一轮MBPP/400在落盘前中断且原进程已消失，原因未知。保留原attempt与失败记录，开始数仍计入312上限。仅继续60个尚未开始的第二轮单位，没有重跑、删任务、改配方或插补耗时。候选/ordinary R/matched target各30/30均完整，可在全部15任务上比较；旧N1只有14任务具备两轮完整费用，必须单独标明，不能冒称15任务完整矩阵。实验矩阵状态为PARTIAL，投资决定不准标GO；证据封存和远端交付可闭环。中断请求和原进程销毁耗时不可得，WORK_ACCOUNTING的累计秒数为已测量费用小计。

## 真正新增的机制证据

自然 checkpoint 位于真实 target verification 前，真实 proposal 已在线产生。target/draft KV、逻辑位置与序列0、committed prefix、pending语义、实际batch、有效greedy sampler history及clone、loop counters一起保存。恢复通过公开 state API，不从空KV按参考重建，不强制参考前缀，不导入未来 proposal。

同路径sham保留每个donor自身的实际caller，并自然生成所有后续proposal；12/12完整原始 IDs和EOG复现父轨迹，source文件不变。四个cross cell另用同一个明确父轨迹已生成的逻辑batch，其作用与sham分开。下面矩阵的行是两个donor，列是两个当前完整配方；/72两列是相同UB1/reservation3的控制。只在预冻结、最接近原分歧的实际batch行归类，其他行完整报告。

| 案例 | 轮次 | 已提交长度 | 局部argmax归类 | 2×2真实greedy token IDs |
|---|---:|---:|---|---|
| HumanEval/145 | 1 | 56 | INTERACTION | `[[71465, 279], [279, 279]]` |
| HumanEval/145 | 2 | 56 | INTERACTION | `[[71465, 279], [279, 279]]` |
| HumanEval/42 | 1 | 73 | INTERACTION | `[[432, 1817], [1817, 1817]]` |
| HumanEval/42 | 2 | 73 | INTERACTION | `[[432, 1817], [1817, 1817]]` |
| MBPP/72 | 1 | 40 | STATE_EFFECT | `[[320, 320], [308, 308]]` |
| MBPP/72 | 2 | 40 | STATE_EFFECT | `[[320, 320], [308, 308]]` |

104个自然checkpoint独立二进制解析；完整float32词表分数、真实top1/top2、参考/替代/EOG分数、state/path差值及所有行决策见 CAUSAL_RESULTS.json。DONOR_STATE_COMPARISON.json 进一步直接比较真实F16 KV：三个任务的差异元素约399万、522万、607万；六个选定batch前缀均与对应参考语义对齐。分数改变、argmax翻转、完整轨迹恢复是三个不同端点；局部cross本身不证明反事实完整轨迹被修好。

UB与output reservation/caller几何一起改变，因此HumanEval干预定义为**当前完整配方**，不能宣称纯UB单变量或唯一kernel因果。Opaque sampler bytes/RNG cursor不可序列化；支持限制在冻结temp0、identity penalties、空grammar/unlimited reasoning的有效greedy合同，依据真实clone元数据与完整行为sham，不认证通用随机采样恢复。

## 单候选与资格边界

CANDIDATE_DECISION 在实现之前提交于私有source commit `415a503e4a378e596f970695ec2234d40745097b`。仅一个任务无关家族：ordinary-R完整prompt caller/512 output reservation与per-sequence1构造target状态，在同一context、同一live sampler内先采样pending，再通过独立私有API绑定continuation UB1；固定k2，draft UB1。调用原speculation accept/bonus/rollback逻辑。不存在task/reference/divergence/margin/future routing或在线额外reference forward。

私有 `llama-b570-pilot.dll` 只增加阶段绑定和scheduler重新reservation，数学、模型、GGML/Vulkan shaders与精度保持原路径。capture-on直接验证阶段绑定前后完整序列化KV相等；off不作KV见证读回。省去旧三次序列化读回、第二target context及host/device handoff是成本假设，phase reserve/reset/sync/draft/rollback仍全部在线计时。不是新的投机采样算法，也没有证明全部旧慢速来自见证。

旧普通路径与新私有库完全隔离。实际加载模块只含新llama私有DLL及原GGML/Vulkan DLL；原R与旧N1正式对照使用原binary及原发布DLL，输出写到新研究目录。D的旧R仅离线评分，不能当新的速度样本。

## 强基线成本

比值统一为 baseline/candidate，>1 才表示候选更快。每任务分别取两轮绝对费用中位数，相除后再取任务几何均值；全部绝对 ms 与每轮方向见 E_COSTS.csv。

| 对照 / 指标 | 完整配对任务 | GM | 第一轮 GM | 第二轮 GM | 全部输出合格 |
|---|---:|---:|---:|---:|---|
| ordinary_R / generation_ms | 15 | 0.282588 | 0.295294 | 0.268578 | True |
| ordinary_R / whole_request_ms | 15 | 0.201290 | 0.209943 | 0.191167 | True |
| ordinary_R / host_end_to_end_ms | 15 | 0.201884 | 0.210574 | 0.191732 | True |
| matched_target / generation_ms | 15 | 0.285761 | 0.298620 | 0.271581 | True |
| matched_target / whole_request_ms | 15 | 0.205704 | 0.216063 | 0.193915 | True |
| matched_target / host_end_to_end_ms | 15 | 0.206243 | 0.216522 | 0.194524 | True |
| old_N1 / generation_ms | 14 | 3.993091 | 5.249546 | 2.594062 | True |
| old_N1 / whole_request_ms | 14 | 2.633940 | 3.534477 | 1.641159 | True |
| old_N1 / host_end_to_end_ms | 14 | 2.633387 | 3.533623 | 1.640933 | True |


E的两轮条件顺序反转，每会话独立初始化并显式暖机，每请求清KV/sampler/history/pending，没有prompt-cache或多GPU并行。generation、whole request及高精度真实host E2E对完整请求全量保留；中断请求的实际时长不可得并明确披露。冷会话初始化、销毁与热身另记 WORK_ACCOUNTING，已测量部分逐项记录，中断部分不伪造费用。C/D是资格或诊断计时。A/B主机时钟是Python3.12 GetTickCount64，分辨率15.625ms，独立测得15–16ms步长；原值未修改，嵌套校验仅容许16ms量化，绝不从其推正式速度。C/D/E使用QueryPerformanceCounter。

投资门槛预定为完整资格、generation GM≥1.05、whole GM≥1.03、两轮均快；没有第三轮，没有事后降低门槛。旧N1不合格时相应费用仅为失败诊断。第二轮在次日恢复，不能假定两轮之间环境完全不变；条件反序减轻固定顺序偏差，但两轮有限pilot不能声明统计显著、一般总体或生产部署收益。

完整对照的观测性判定为 **SCOPED_REPAIR_WITHOUT_DEPLOYMENT_GAIN**；它是已完成配对数据的局部描述。正式研究状态保留 **PARTIAL_INFRASTRUCTURE_BUDGET_CLOSED**，不以14任务旧N1配对冒充15任务完整矩阵。

## 暴露、旧负结果和相关工作

旧共享24 MBPP、旧8个unused及24个HumanEval全部已暴露；/72原N1与matched T四轮失败、原UB2五候选资格失败均保留。旧共享R/N1 generation/whole比值0.1885246521769912/0.17905546046949286，T/N1为0.8040229271596392/0.6935408122196928，N0/N1为0.9995218815660408/1.247058534284672；不能改写为部署正收益。旧k3/UB4长三任务只支持原有限条件。

若E运行，其新输入严格按预定SHA256(task_id + "HeteroSpec-B570-mechanism-v1-confirm")排序、仅静态ctx安全选择；8次新matched前端桥接额度在任何新参考输出之前扣除，四条件面板等比例减到15任务。E_EXPOSURE_AUDIT/CATALOG说明最新可访问历史、保守排除及实际限制。原始数据集/显式零forward词表/机械可用性账本是可用性，未混成生成输出；所有其它实际或含糊description/ID命中保守排除。所谓unused仅是accessible-project-unused，不是model-training unseen；RTX bulk不可访问，未声称独立重扫。

RELATED_WORK对照LLM-42、Vosti与batch-invariant inference的原始来源。选择性确定性、KV一致和固定数值路径不是本轮首创；本轮增量是B570/Q8/Vulkan的可恢复自然状态交叉及一个被资格门槛实际检验的固定前端配方。#62已有RTX真实cross与fixed-UB负效率，不能冒充那些问题尚未做。

## 审计、修正与复现

独立CPU代码不导入执行器的endpoint/qualification比较函数。Stage0 68645项、A 1437项、B 63798项；最终综合检查见 INDEPENDENT_VERIFICATION。检查完整raw/EOG/端点/suffix、sampler/clone、sham、source不变、输入身份、重复keys、计费上限、实载B570与37/37 target、29/29 draft offload，保留所有失败。

预输出构建及离线解析修正均显式留证：A/B unused cross观察扩展分阶段绑定；C最初loader失败发生于任何模型加载/请求之前，dumpbin证明旧common.lib是DLL import，因而单独静态重编同一common源、只绑定新私有llama；原冻结与失败保留。D第一条完整raw、EOG和长度已一致，仅旧CAP128/新CAP端点字面值不同；CPU规范化保留所有原标签、未更改任何参考数组或候选。已完成D单位复用，不重新生成，额外session暖机照常计费。普通科学mismatch不会这样修复或追成功。

模型权重及原runtime/source散列、真实设备与驱动32.0.101.9034均记录。源distribution不是Git checkout，不编造SHA；实际编译binary、私有源码历史及阶段冻结分别绑定。驱动稳定性版本差异按用户授权记录，所有本轮桥接/正式对照依同一实际环境；屏保关闭不能推出完全无外部GPU干扰。

内容地址包封存完整raw/state/logits、attempts/失败、私有程序与源码Git历史；旧两个包不重写，外部模型/runtime依赖逐字节绑定。实际clean restore重新核对CRC、objects/file SHA、私有program/history及独立CPU派生；封存结果以 ARCHIVE_RESTORE.json 为准。公开只增加本轮目录，bulk state/模型/runtime不上传；最终新远端fetch/checkout及逐Git blob/SHA回读以 REMOTE_READBACK.json 为准。报告本身不替代这两个实际交付门槛。

不启动更大性能矩阵，不启动第二候选或其它模型/硬件。保留本轮可恢复状态交叉与资格边界。只有独立的新机制或成本假设及新的预冻结合同，才值得重新投入；本轮不继续参数搜索。
