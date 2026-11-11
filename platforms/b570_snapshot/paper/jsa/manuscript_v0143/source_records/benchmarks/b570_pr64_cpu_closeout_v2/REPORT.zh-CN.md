# B570 PR64 CPU科学收尾v2

结论：原始字节支持有限端点修复与自然状态/完整配方的局部效应，同时保留相对普通 R 的强负效率。CPU审计与论文证据交接独立闭环；原E仍119/120，PARTIAL_INFRASTRUCTURE_BUDGET_CLOSED。B570_GPU_NEXT_ACTION=STOP。RTX原始强基线成本待移交，不冒称本机已复算。

## 原始访问与计数

复用PR64实际恢复目录，按原CAS的INDEX逐个核对所需文件hash，未重复恢复2GB。原CAS `6840d4d6f179564b57ef7c5b994da62c6b2e1d51b606f8a9cfbb8f91c26646fb`，2246085019bytes/3225files/2392objects。INPUT_BINDINGS列本轮实际读取的raw、source和冻结依赖；D_REFERENCE_BINDINGS还列经已恢复PR63 CAS index绑定的32MBPP×4轮旧R原始记录。

账本独立重建：非warm312starts/311complete、warm37/37、辅助target24/24。A48、B12完整own-path shams和24cross cells、C12、D112/56任务、E8桥接+119formal。唯一缺失 `E/FORMAL/1/old_N1/MBPP/400` 的原attempt、infra失败事件和分母保留；原因和中断耗时unknown，无重跑/插补。完整请求与aux host小计6541.859837599979秒，含warm；不含会话加载/清理和未知中断费用，不称总campaign费用。

A48/48表示继承桥接、输入/计数与重复稳定核查通过，不能写成48份都符合R：其中32份R端点一致，其余为保留的诊断负例。C12/12、D112/112、E127/127已有完成记录均为参考端点一致。候选/ordinary R/matched target正式各30/30，oldN1仅14任务具备两轮配对。

## 端点与完整raw分开

按runtime EOG集合或128token先到者取端点，保留并全额收费raw suffix。C12份中仅4份完整raw等于历史R，8份不等；D112份中，32MBPP的64份可对照旧raw（16相等、48不等），24HumanEval的48份只绑定完整cap128端点导出，历史完整raw比较标unknown。E127份含桥接，80raw相等/47不等；这些记录都端点一致。C/D/E相同任务/同配置的可用双轮raw重复稳定；缺失oldN1对应的单轮不能称双轮稳定。表见QUALIFICATION_RECOMPUTED.csv。

D56全部已暴露，24HE关联三轮不变参考导出，32MBPP关联四轮旧R真实raw。E15在原冻结时为accessible-project-unused；如今全部已暴露，不称新holdout，不等同训练未见。核对原预输出审计和冻结输入，无独立重扫RTX bulk。

## 真实机制范围

六交叉全部从fullfloat logits复算每行top1/top2、margin、参考/替代/EOG分数；24target/draft donor KV解析完整字节，F16布局、连续位置、sequence0 ownership与真实cross-before字节相等。12完整own-path sham、source不变及有效greedy历史/clone合同核对通过。sampler opaque bytes/RNG cursor不可得，只支持这套有效greedy配置。

| task | 两轮focus二维argmax表 | 判断 |
|---|---|---|
| HE145，prefix56，row0 | [[71465,279],[279,279]] | INTERACTION |
| HE42，prefix73，row0 | [[432,1817],[1817,1817]] | INTERACTION |
| MBPP72，prefix40，row1 | [[320,320],[308,308]] | STATE_EFFECT；两列相同当前配方 |

两种状态的target F16元素分别有3987448/5218133/6072820处不同。全行浮点score非加性另列，不能同argmax分类或完整候选资格混成普适因果证明。干预是历史target数值状态×完整当前配方（UB/输出reservation等共同改变），不能锁定唯一attention/kernel，也不证明反事实完整轨迹已修复。

## 成本结果与解释

比值为baseline_ms/candidate_ms，>1候选更快；每任务两轮绝对耗时中位数之比，再取任务GM。

| baseline / candidate | N | generation | whole | host |
|---|---:|---:|---:|---:|
| R / candidate |15|0.28258755350958753|0.2012895931787418|0.2018837104115267|
| matched / candidate |15|0.28576136794192253|0.2057042276473282|0.20624276201591446|
| oldN1 / candidate |14|3.9930912531266287|2.6339404210545703|2.6333865472136693|
| R / matched |15|0.9888934797058363|0.9785389220285977|0.9788644626275350|

R/matched对candidate在全部15任务和30单轮、全部三个timer均更快。oldN1任务中位数全部慢，但MBPP/245第二轮whole/host反向，oldN1/candidate为0.8735823147094709/0.8736026835705244。不能从GM声称每轮同方向。

完整candidate整请求约是R的4.968倍；matched目标路径仅约1.022倍，因此约5倍不能全归因于参考保持目标路径。candidate正式总drafted888、accepted702；target续算1332caller tokens、draft续算1362，分别约1.1583/1.1843倍端点1150token；额外suffix26token全额收费。公式及capture-on开发/桥接核对、KV操作/clone/分布拷贝见WORK_BREAKDOWN和COST_EXPLANATION。调用数、source分支操作不等于kernel派发或duration。所有未隔离的draft/verify/sampler/rollback/sync/host耗时与比例unknown。

额外核对已有stderr：有窄范围target common-sampling timer，30正式请求合计851.52ms、每请求9.79–94.05ms；排除前置同步且不含draft/拷贝/clone/KV/完整host，不能当完整sampling分解。context eval/prompt/total为累计未重置计数，不作单请求组件归因。

同context/live sampler128→1已删除旧第二target context和三次KV见证读回；oldN1整体改善是真实工程进展，尚不构成相对R的部署收益。未提出足以区别已有固定路径/KV原则的新在线机制假设，停止此路线新增GPU投入；仅可将研究前端清理视为HARNESS_OPTIMIZATION_ONLY。

## 论文与跨平台交接

PAPER_HANDOFF提供英文B570段落、分平台证据强度、三条经验贡献候选及反证、可用/待补/应删主张和后续文章顺序。CLAIM_EVIDENCE_MATRIX逐条绑定exact source、任务/配置/长度、控制与外推边界。RELATED_WORK比较实际读取的七项primary source，Performance or Illusion明确仅abstract。已有验证、固定数值路径/KV一致与回放原则不重新命名为新算法。

RTX PR59/60局部约束合格加速、mask3有限最小性、PR62真实状态cross和C4扩大k后的负效率均保留；不能将全部平台写成失败，也不能称四个平台均有相等强度状态cross。RTX#62 B相对matched的1.1692379705generation/1.0350713662whole不升级成胜过ordinary R。本机无身份绑定完整RTX B raw，CROSS_PLATFORM_GAPS明确同会话scalar-R配对、四重复中位数/GM/bootstrap/各轮方向和验证需求，状态DEFERRED_RTX_RAW_ACCESS。

## 验证和交付

新parser不导入旧执行器endpoint/qualification/cost函数。第三次CPU验证直接读取原始cost/IDs/fullfloat，再核对表、分母、图数据和旧bytes，拒绝missing、duplicate、ratio inversion、suffix misqualification、unqualified cost五类负例。INDEPENDENT_VERIFICATION给实际结果；两类精确SVG/PDF经Poppler渲染并查看，FIGURE_VISUAL_QA绑定最终PDF。

有限CPU阶段、失败履历、source/input hashes和resume入口保留。封存本轮轻量CPU产物，引用原CAS而不上传bulk/KV/模型。新branch基于实际main，只增benchmarks/b570_pr64_cpu_closeout_v2；新Draft PR与fresh远端readback见独立交付receipt/PR说明。零新模型请求/forward/warmup，原论文、PR63/64、数据/归档、runtime/driver、模型、tag/release不改，不合并。
