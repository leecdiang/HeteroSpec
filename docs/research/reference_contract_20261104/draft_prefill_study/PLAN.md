# QB draft prefill：先做小实验，再决定是否值得继续

2026-11-04。状态：**研究设计与历史CPU重算，不是已启动的Qwen/Smol GPU实验。** 本目录不启用优化、不改变旧worker、旧R、已有原始记录或论文，不给出accept概率，也不把合理路线写成已证明的新颖性或加速。

## 结论与范围

建议先检查普通draft ubatch从1增到2/4的最小改动及CPU事务行为，再决定是否进行设备资格和性能试验。若应用只要求严格target参考行为，draft字节不必保持旧UB1一致；普通更大ubatch就是必须面对的简单竞争者。不要在它之前投入完整双缓存服务、并发调度器或自定义逐行严格算术内核。

本计划依据[224d928的draft研究](https://github.com/leecdiang/HeteroSpec/blob/224d92865c1f55988539453e02e0e25f1ad9cb2d/docs/research/reference_contract_20261104/draft_reuse_research/RESEARCH.md)与[9299459的更正重算](https://github.com/leecdiang/HeteroSpec/blob/9299459c1ab28d0ffa9783d81d290acbedd40a2e/docs/research/reference_contract_20261104/rtx_reanalysis/REPORT.md)。主结论限于#151的QB、两天、每模型12个已暴露输入和四个session。96个input/session块不是96个独立工作负载；新输入、新runtime、新缓存、长上下文和其他scope均须重新验证。GS/PQ反例不能被QB结果覆盖。

## 1. 独立读源得到的实际合同

[worker.cpp](https://github.com/leecdiang/HeteroSpec/blob/29511ed91eb9f3d9773cfdda53e3554b0f4ad08b/scripts/experiments/rtx_scope_transfer_v1/worker.cpp#L74-L164)明确显示：

- 每个请求清空target和draft KV，模型可以resident，但不是prefix warm。
- scoped target ubatch为4，draft在构造路径硬编码为1；context1024、F16 KV、非flash、greedy k=3。
- 每次decode后同步，再累计host phase；先target prefill，再draft prefill，之后才采样/提交首个target token。
- seed、proposal、correction/bonus、committed prefix与pending token不同。每轮同时trim两个模型至合法边界，pending可能还没有写入任何KV。

独立取回的worker Git blob为`b38275fb41c9baa732adc02e40f6c9529b1b2fa6`。早先分析副本只多一个文件末尾换行，代码相同。

[study.py 501–510](https://github.com/leecdiang/HeteroSpec/blob/29511ed91eb9f3d9773cfdda53e3554b0f4ad08b/scripts/experiments/rtx_scope_transfer_v1/study.py#L501-L510)对旧R做的是保留原始出处的endpoint检查；[585–593](https://github.com/leecdiang/HeteroSpec/blob/29511ed91eb9f3d9773cfdda53e3554b0f4ad08b/scripts/experiments/rtx_scope_transfer_v1/study.py#L585-L593)的完整决策向量字节比较在相应M或C内比较PQ与QB。不能把这升级成任意新draft轨迹对旧R完整数值行为的证明。

[NativeCheckpointOwner](https://github.com/leecdiang/HeteroSpec/blob/224d92865c1f55988539453e02e0e25f1ad9cb2d/src/reference_batching/native_checkpoint.hpp)在append前后同步、导出完整state、保存所请求logits，恢复时创建新context。它是单模型、单sequence的正确性基础，不是已测得低开销的双模型prefix serving cache。其成本不能沿用#151旧timing。

## 2. 必须分开的两种exactness

### T合同：严格target参考，允许draft改变

保持声明的target参考行为严格；普通draft更大ubatch可以改变draft logits、KV、proposal与接受轨迹。资格检查至少包括：

1. matched committed prefix上的target完整词表向量、输出、位置、终止和pending元数据；检查实际需要的target state合同。
2. 如果声称所有target verification row都满足数值参考，离线参考必须在候选实际proposal prefix上做forced-prefix验证，包括off-greedy分支。不能拿这些行直接与正常greedy轨迹的其他prefix比较。
3. 第0/1/2个proposal拒绝、全部接受后bonus、cycle中EOG/cap、reset、后续continuation。
4. 明确物理state序列化格式、未使用区域/metadata与逻辑KV比较的口径，不能只凭bounds相同就声称全部KV字节相同。

CPU tiny-model结果只证明对应CPU fixture/部署，不能自动证明Qwen/Smol CUDA、旧R完整数值参考或采样分布。历史worker只有greedy，不延伸成随机sampling算法保证。

### TD合同：target与旧UB1 draft均严格保持

在T之外，还要求draft logits/KV、proposal、接受轨迹和逻辑工作一致。逐行保留UB1算术的定制prefill属于这一研究线；普通宽ubatch不应冒充TD。

先说明应用为什么需要更强TD合同。若用户价值只依赖T，不能人为要求draft byte exact，再把普通宽draft排除。反过来，如果论文声称TD，就必须完整验证，不能以endpoint相同代替。

旧R保持不可变的科学参考角色；性能主对照使用同合同下最强合法实现，不以更慢旧R充当唯一竞争者。两模型族分别判定，不能以Qwen通过替Smol背书。

## 3. 新CPU sensitivity：足以阻止不值得做的实验

下面都是**固定其余分项的host accounting反事实**，不是因果估计、真正warm请求、实测并发或GPU kernel时间。比例s/f表示假设可删除的相位墙钟比例，既不是token LCP比例，也不是自然hit rate。

|QB，两天合计|Qwen|SmolLM2|
|---|---:|---:|
|原始C/M，总时间比|0.892232|1.280828|
|冷缓存、理想删除全部draft prefill后C/M|0.715534|0.879337|
|双方各删除50% target prefill，理想重叠余下prefill后的C/M|0.631205|1.051664|
|双方各删除100% target prefill，draft仍冷，理想prefill重叠后的C/M|0.799739|1.569481|

100% target删除时已无target prefill可隐藏draft启动。50%时，Smol即使完美、零竞争重叠仍慢5.17%。这并不否定真正双缓存也删除draft prefill的可能，而是说明冷缓存的完美重叠上限不能代替热target流量的证据。

冷Smol合计需要删除69.946%的draft prefill才打平；若选择3%完整service收益作为工程门槛，则需删除77.419%，四session范围74.218%–80.587%，均尚未加额外开销。3%是本计划建议的决策坐标，不是用户承诺、功效证明或新的显著性结论。Qwen原本已优于target-only，新增方法还需优于现有有用draft路径。

脚本同时保留h=0和每请求10ms的透明敏感性坐标。10ms不是测得实现开销。完整结果见`sensitivity.json`，不可将其标记为新的模型实验数据。

## 4. 公平竞争者，不做一次性大矩阵

依次考虑：

1. **最强合格target-only QB**：同样可用的target prefix、相同总内存预算；释放draft占用后target-only能容纳更多cache的机会也不能隐去。
2. 未改UB1 draft：同lifecycle的机制基线。
3. 普通更大ubatch draft：1/2/4是轻量可行性入口；若更大值仍有明显可能且资源允许，最后性能主张不能只战胜UB1就停止寻找更强普通基线。
4. 持久化独立target/draft KV：分开frontier、合法prefix、miss/catch-up/eviction。host快照导入和GPU常驻复用是不同部署，分开比较。
5. 重叠prefill：只在剩余冷启动机会足够、并发状态安全后考虑。
6. 定制TD prefill：只有简单方案留下足够收益且TD本身有明确价值才推进。

不得为候选关闭合法graph replay、已有合格target-only batching或缓存。历史ub4可保留为reproduction track，但部署决策须面对更强合格target-only；例如target batching变化不能无资格地继承旧参考，也不能被无理由忽略。

持久化双KV已有直接先例：[Meta §3.4 Persistent KV](https://arxiv.org/html/2508.08192v1)。通用并发、overlap与相关机制的既有工作已在[固定研究报告](https://github.com/leecdiang/HeteroSpec/blob/224d92865c1f55988539453e02e0e25f1ad9cb2d/docs/research/reference_contract_20261104/draft_reuse_research/RESEARCH.md)中列出。把它们作为竞争者，不宣称机制首次出现。若主张依赖代码重复，还应面对低内存suffix/ngram类draft，而不是只比冷神经draft。

## 5. 分阶段执行与预算

### A：当前允许的云端CPU工作

固定身份、重算、检查源、实现独立最小ubatch1/2/4适配与CPU事务测试。target geometry、k、cache lifecycle、首token顺序、admission均不同时改动。CPU实现应单独报告；本目录不把其他进行中的CPU工作算成已完成，更不宣称GPU已启动。

离线参考可用于qualification，但不能把预先算出的expected KV/logits当作未知请求的免费生产runtime oracle。需要在线参考重算的安全方案必须把成本计入service。

### B：以后另行安排的设备机制pilot

只有取得所需设备执行授权且通过身份/资源门后开始。每模型先选4个新root：code/math × short/long，各一。自然token长度可用128–384与512–768；不人为padding/truncation制造机会。cap32/128在同root上交叉，仍按root聚类。

先比target-only、UB1与预选普通宽draft，全部冷KV、两轮平衡配对顺序。这个小pilot用于机制/成本筛选，不作独立总体推断。先qualify再timing，保留失败/fallback与全部尝试成本，不挑幸存子集。

若普通宽draft已满足目标，或者删除它剩余全部draft prefill仍无法超过最强竞争者的工程门槛，就停止定制内核。新的实际timing出来后重新计算，而不是继续拿旧UB1的P做上限。

### C：仅对幸存方案做状态诊断

分开四格：target冷/draft冷；target热/draft冷；target冷/draft热；双热。warm指有效prefix状态，不是模型resident。target-only获得完全相同的合法target prefix。先每模型一短一长代表root，避免全panel乘以所有状态。

分开partial/exact hit；增加early-prefix edit、相同长度错误prefix、target-only轮次后draft落后、压力淘汰和cold unique请求。人工全hit只说明机制可行，不能估计真实流量命中率。

### D：值得才做新的盲测确认

冻结设置与admission规则，使用root-disjoint的新输入。24-root、每domain×length格6个可以作为小规模结构参考，但不是天然足够检出3%。正式样本数需从calibration方差和可接受预算预先确定；不能看test结果继续补样直到好看。

output budget是输入时已知的cap，实际结束长度和接受率是运行后结果。admission不得偷用本请求未来接受率、真实输出长度或实际完整成本。小样本不足时报告不确定，不硬推总体结论。

## 6. 两个KV的状态合同与12GB约束

target KV不能充当draft KV。两边权重、层/头数和位置配置不同，需分别保存：部署/模型/producer身份、精确token前缀、绝对位置、valid committed frontier、pending、tentative suffix与回滚边界。target-only轮次后draft可能落后，重新启用必须catch-up，不能按长度假设一致。

exact full-prefix hit还需正确恢复target输出logits；native state本身遗漏logits时，位置正确不等于首token可正确恢复。查找key应由请求前已知身份构成，完整检查digest碰撞、recipe、模型/tokenizer/RoPE/KV dtype、runtime与状态完整性。出错后恢复所有已承诺状态，不能只删除suffix就假设整个逻辑batch原子。

按官方config与F16 K/V，名义每token字节是`2 × layers × KV_heads × head_dim × 2`：

- [Qwen3-8B](https://huggingface.co/Qwen/Qwen3-8B/raw/main/config.json)144KiB + [0.6B](https://huggingface.co/Qwen/Qwen3-0.6B/raw/main/config.json)112KiB，pair每1024位置256MiB。
- [SmolLM2-1.7B](https://huggingface.co/HuggingFaceTB/SmolLM2-1.7B-Instruct/raw/main/config.json)192KiB + [135M](https://huggingface.co/HuggingFaceTB/SmolLM2-135M-Instruct/raw/main/config.json)22.5KiB，pair每1024位置214.5MiB。

这是结构计算，不能替代实际GGUF/runtime分配。它不含alignment、allocator metadata、graph、activation scratch、speculative slots和恢复时新旧context并存。官方main config只作结构来源，真正资格绑定历史模型hash/metadata。

历史RTX total为12,792,037,376字节；旧Qwen多个context pool建立后仅余1.795GiB，Smol余8.129GiB。这不是当前可用量或新服务容量承诺。建议资源门至少保留512MiB并实测最坏恢复/临时缓冲时peak；该reserve也不是不会OOM的证明。不得假设另一台B570的10GB可以相加，或将模型文件体积当作VRAM占用。

两个模型族分开执行、分析与结论；不默认两对模型一起resident。host spill可行性与导入/同步成本独立记录。

## 7. 完整成本与统计口径

主要指标是完整service和声明lifecycle/trace内总等待时间。计入lookup/key、first fill、catch-up、导入导出/copy、状态检查、同步、capture/rebuild、eviction、失败/fallback、恢复、cancel及变化后的proposal/target调用数。模型加载、构建、calibration等按部署窗口分别记账；不把重叠wall与process sums重复相加。

串行敏感性为`C_new=C-fP+h`。公平target重用的假设式为：

`M_new=M-sP_target_M+h_M`

`C_new=C-sP_target_C-fP_draft+h_C`

这里s相同只是两边删除相同比例target phase的灵敏度坐标，不是完整缓存干预。更大draft改变接受率/continuation后，旧分项不可固定，需实际service。完美overlap最多隐藏`min(remaining_target_prefill, remaining_draft_prefill)`，假设零竞争、零同步开销；实际并发直接测request wall，不再把重叠phase相加。

同合同最强竞争者为B，当前候选成本为C0、剩余可删除draft phase为P_rem时，定制prefill的理想收益上限是`[B-(C0-P_rem)]/B`。如果连这个上限都不越过工程门槛，无须做昂贵新内核；这是筛选，不是因果保证。

单列TTFT。原worker在draft prefill之后才采样首token；提前返回target首token可能改善TTFT而不改善completion latency，必须另立干预。cap1/初始EOG可以检验不必要draft启动，但不可偷偷混入ubatch消融。

root/conversation是样本单位；session与cap变体是相关重复。缓存trace按整段会话计first fill及全部turn，重采样整个root/trace，不重采样token或turn伪造样本量。同时报告sum(C)/sum(M)与等root几何比，注明不同estimand。两模型分别检验；主比较与多重性处理预先固定。小panel的p95/worst regression只能描述，不是SLA。

## 8. 失败门与可接受的负结论

- target所需数值合同失败：停止该合同下性能主张，不能降成只比endpoint后继续同名结论。
- prefix/recipe/state不一致、恢复不完整、使用未计费runtime oracle：拒绝路径。
- memory admission失败、未计费offload或不安全并发：不启动对应设备方案。
- 完整成本无法胜过最强同合同基线：停止或缩小适用范围。
- 最大剩余ROI不足，或收益仅在制造的全hit且没有真实reuse证据：不扩展成大研究。
- 只一个模型族通过：只报告该族；不包装成双模型普适。

可能的有用结论是：普通宽draft已解决冷启动；Smol在target热/draft冷时仍不适合启用；定制TD内核剩余价值不足。这样的明确边界比增加一个事后oracle或再次用慢R制造大倍数更有价值。

## 复现与未完成项

见[README.md](README.md)、[SOURCE_MANIFEST.json](SOURCE_MANIFEST.json)、[VALIDATION.json](VALIDATION.json)。本包完成的是历史验证、host sensitivity与方案；新的Qwen/Smol数值资格、设备timing、并发安全、真实cache命中分布、12GB峰值和生产收益仍未建立。未合并任何PR，未更新论文，未声明提高论文接收概率。
