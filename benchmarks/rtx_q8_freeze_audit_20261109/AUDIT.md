# PR #213：分阶段冻结的独立离线审计

审计对象：#211设计提交`ad9fb6846dd979c3a76d3c415c74fa9f86565f7d`；#213结果提交`ba5b4c8e01d50d4bfaab1ac3908f798347be063a`。北京时间2026-11-09。本审计使用新读取器和新统计实现，不导入旧资格验证器，不执行worker、分词器、模型或GPU。原结果、基线、账本和论文均未修改。它是对现存材料的独立复核实现，不是另一团队/另一设备的独立实验。

## 判断

**总体判为第二档：存在尚不能排除的风险。** 全局“任何新输出前全部冻结”确实没有遵守，不能改称全程事前冻结。现存原始数值与固定正式面板的复核未发现实质数值错误、删臂/换输入或结果导向的分析变更。局部数值证据和已记录服务时间结果仍可有条件使用；未记录的尝试、历史发布时间和中断环境影响不能靠“未发现”证明不存在。

| 档位 | 本次判断与适用范围 | 直接证据 |
| --- | --- | --- |
| 不影响现有结论（有限条件） | 已捕获输入上的严格数值相等、同工作量算子结果、冻结八臂点估计及区间均复核一致；没有发现冻结偏离改变这些现存数据的证据。 | [数值复核](evidence/NUMERIC_RECHECK.json)、[面板复算](evidence/PANEL_RECHECK.json) |
| 存在尚不能排除的风险（总体） | 资格对先前路径/R输出的依赖；全局冻结违例；正式自然跨界拒绝的旧KV未捕获；312秒修复间隙可改变运行环境。不能声称严格独立事前资格或零影响。 | [完整时间线](evidence/TIMELINE_FINAL.json)、[联合覆盖缺口](evidence/BOUNDARY_COVERAGE_GAP.json)、[修复复核](evidence/READER_REPAIR_RECHECK.json) |
| 发现实质结果问题（本次未检出） | 未检出数值不等、正式数据选择/篡改或分析变更；程序违例已确认。若声称“全部输入/源码/分析在任何输出前已冻结”，该表述与证据冲突，不能用于论文。未检出不证明一切影响不存在。 | [PLAN.md](https://github.com/leecdiang/HeteroSpec/blob/ad9fb6846dd979c3a76d3c415c74fa9f86565f7d/benchmarks/rtx_q8_transfer_20261109/PLAN.md#L31)、[LIMITATIONS.md](https://github.com/leecdiang/HeteroSpec/blob/ba5b4c8e01d50d4bfaab1ac3908f798347be063a/benchmarks/rtx_q8_transfer_20261109/LIMITATIONS.md) |

这里的“有限条件”以现存执行记录真实完整为前提。哈希承诺支持材料一致性，不能独立证明历史进程未被干预或不存在未记录的筛选。

## 1. 实际冻结与输出时间线

全部时间为2026-11-09北京时间。下表“首次Git出现”是本地Git提交作者时间，并由本地远端ref推送reflog交叉支持；数值首输出为原始文件mtime。它们不是独立服务器时间公证。各个工作单元的精确路径、开始/结束、首输出、首次提交和本地mtime均列于[TIMELINE_FINAL.json](evidence/TIMELINE_FINAL.json)。不能用多个清单继承的同一个`utc`字段代替实际冻结时点。

| 组别/逻辑请求 | 输入生成规则 | 具体清单首次Git出现 | 该组首数值输出 | 执行开始～结束 |
| --- | --- | --- | --- | --- |
| V1几何20 | 既有rtx184强制token带；q4/q8的extent内与平衡跨界；先R后8候选。 | [`bbe05b35`](https://github.com/leecdiang/HeteroSpec/commit/bbe05b35ce228a30ec7db28fecaf9d6a08140831) 14:39:32 | 14:40:06.334536 | 14:39:49.988238～14:43:44.082019 |
| V2自然84 | 原rtx188四个暴露根；cap128/32/32/32＋cap1，全部8臂重/轻；4新R。 | [`bc650e04`](https://github.com/leecdiang/HeteroSpec/commit/bc650e04b419329aedbff87e034aff107f664de5) 14:50:48 | 14:51:07.900527 | 14:50:55.606266～15:15:11.401887 |
| 动态R90 | 39份展开清单；从实际候选已请求路径和提交前缀补齐R，覆盖未有参考的所有行/状态。 | [`14859fc4`](https://github.com/leecdiang/HeteroSpec/commit/14859fc4364132865dee4ec18d7d79559809b132) 15:16:43、[`5ef7d0f6`](https://github.com/leecdiang/HeteroSpec/commit/5ef7d0f6bfed36adcd18be166a2e19b2ed02dcee) 15:36:44、[`147db0d0`](https://github.com/leecdiang/HeteroSpec/commit/147db0d0d32217275c75df0098289a26e4afaf15) 15:41:45 | 14:53:51.099120 | 14:53:38.445572～15:37:58.169648 |
| 标量延续3 | 原四根不替换；按ceil(prompt/256)确定E=256或768，补至cross头之后8 token。 | [`14859fc4`](https://github.com/leecdiang/HeteroSpec/commit/14859fc4364132865dee4ec18d7d79559809b132) 15:16:43 | 15:17:06.781669 | 15:16:48.682254～15:17:45.364163 |
| EOG/控制/负例134 | 借用已注册EOG提示；R贪婪带构造所有拒绝位次、接受cap、bonus及续转；5负例。 | [`14859fc4`](https://github.com/leecdiang/HeteroSpec/commit/14859fc4364132865dee4ec18d7d79559809b132) 15:16:43 | 15:18:38.287158 | 15:18:28.945687～15:32:37.849077 |
| 正式R16 | 14:39已提交的16输入，cap96，原scalar R一次生成端点；不是性能M。 | [`14859fc4`](https://github.com/leecdiang/HeteroSpec/commit/14859fc4364132865dee4ec18d7d79559809b132) 15:16:43 | 15:32:51.671836 | 15:32:37.858053～15:33:42.264498 |
| producer5 | 固定4开发根＋EOG；以独立R延续为位置索引，native draft单独生成7提案及全向量hash。 | [`5ef7d0f6`](https://github.com/leecdiang/HeteroSpec/commit/5ef7d0f6bfed36adcd18be166a2e19b2ed02dcee) 15:36:44 | 15:37:08.594035 | 15:36:49.886866～15:37:13.092813 |
| tape重放/负例35 | 绑定producer结果后展开；r0 cap16和EOG cap128，全部8臂重/轻＋3负例。 | [`147db0d0`](https://github.com/leecdiang/HeteroSpec/commit/147db0d0d32217275c75df0098289a26e4afaf15) 15:41:45 | 15:37:34.288327 | 15:37:17.405819～15:41:42.360831 |
| V2几何36 | 保留V1内/跨界；长根既有R带增加255/767处1+k；4新R＋32候选。 | [`5ef7d0f6`](https://github.com/leecdiang/HeteroSpec/commit/5ef7d0f6bfed36adcd18be166a2e19b2ed02dcee) 15:36:44 | 15:42:06.856912 | 15:41:50.819610～15:47:51.371528 |
| 同工作量资格40 | 4根×内/跨界的同8 token；8 R case＋32重捕获候选。 | [`147db0d0`](https://github.com/leecdiang/HeteroSpec/commit/147db0d0d32217275c75df0098289a26e4afaf15) 15:41:45 | 15:49:37.831368 | 15:49:21.874628～15:53:59.521585 |
| 干净诊断160 | 固定128测量＋32预热，AB/BA/BA/AB，两个投影与几何互补反转。 | [`2a884e28`](https://github.com/leecdiang/HeteroSpec/commit/2a884e28e3c31c2cb20eebf853c48e03698364fe) 15:56:13 | 15:59:14.679538 | 15:58:56.755937～16:12:12.316278 |
| 正式面板1152 | 16根×8臂×8顺序块1024测量＋128预热，64串行worker。 | [`2a884e28`](https://github.com/leecdiang/HeteroSpec/commit/2a884e28e3c31c2cb20eebf853c48e03698364fe) 15:56:13 | 16:16:44.003333 | 16:16:26.423872～17:09:34.289962 |

**50个资格工作单元、125次请求的具体清单在其执行后才进入Git**：39个动态R工作单元共90请求，及8个tape重放与3个负例工作单元共35请求。其生成规则先在阶段清单中声明，具体文件的原始mtime大多早于本次reserve；有1份仅相差约0.24微秒，不能在该时钟精度下判定先后。写入后再调用执行器的源码支持逐工作单元顺序，但这不能补成全局事前冻结或逐任务事前公开。

V2前端在V1几何输出之后才实现/构建，并在`bc650e04`14:50:48提交；旧数值核心与R未改。完整C/D具体清单与分析代码在`2a884e28`15:56:13提交，推送reflog15:56:18，执行者全文件远端回读记录15:58:35；首干净诊断reserve15:58:56，首live reserve16:16:26。正式R输出早于完整分析文件，但#211的四主比较、根级bootstrap/seed/区间、八臂与cap96此前已经写定。[PUBLIC_FREEZE_READBACK.json](https://github.com/leecdiang/HeteroSpec/blob/ba5b4c8e01d50d4bfaab1ac3908f798347be063a/benchmarks/rtx_q8_transfer_20261109/results_20261109/PUBLIC_FREEZE_READBACK.json)。

`COHORT_ADMISSION`与排序程序在`bbe05b35`14:39:32提交，早于本轮首次模型reserve14:39:49。最终命名的`COHORT_FREEZE`到`5ef7d0f6`15:36:44才提交，晚于正式R输出；本审计逐字段确认两者16项完全相同，不把这个晚文件当成首次冻结。#62完整39份暴露JSON现已重读并通过身份排除；该审查与词表token验证不是模型正确性资格。

### 正式16输入逐项

已从16,000条原始授权任务、来源/历史排除文件哈希、seed20261109的domain/ID哈希序和长度≤192规则重新构造；没有重新运行native分词器，只读取冻结的词表token记录。首次实际prompt文本/token字节均见[COHORT_ADMISSION.json](https://github.com/leecdiang/HeteroSpec/blob/bbe05b35ce228a30ec7db28fecaf9d6a08140831/benchmarks/rtx_q8_transfer_20261109/results_20261109/cohort/COHORT_ADMISSION.json)；下表共用此前瞻输入提交，每项cap96。R单个worker执行15:32:37.858～15:33:42.264，逐项时间为receipt文件mtime，非单独进程开始。

| 输入 | prompt token | 首次R输出 | 首次live输出（保留原首worker） |
| --- | --- | --- | --- |
| APPS/train/199 | 117 | 15:32:51.671836 | 16:16:53.077293 |
| APPS/train/169 | 151 | 15:32:55.583838 | 16:17:01.615798 |
| APPS/train/417 | 134 | 15:32:59.198169 | 16:17:09.402310 |
| APPS/train/254 | 140 | 15:33:02.314003 | 16:16:54.499338 |
| APPS/train/296 | 173 | 15:33:06.388386 | 16:16:47.216202 |
| APPS/train/603 | 178 | 15:33:10.675577 | 16:17:03.759391 |
| APPS/train/305 | 171 | 15:33:14.854568 | 16:16:51.642606 |
| APPS/train/979 | 179 | 15:33:18.161644 | 16:17:05.155835 |
| MATH/geometry/train/200 | 48 | 15:33:20.490411 | 16:16:57.177608 |
| MATH/intermediate_algebra/train/799 | 72 | 15:33:23.175623 | 16:17:07.589066 |
| MATH/intermediate_algebra/train/911 | 96 | 15:33:26.223740 | 16:16:55.968524 |
| MATH/intermediate_algebra/train/805 | 99 | 15:33:29.319804 | 16:16:58.639261 |
| MATH/number_theory/train/237 | 42 | 15:33:31.552258 | 16:16:49.768915 |
| MATH/counting_and_probability/train/599 | 59 | 15:33:34.045524 | 16:17:06.357594 |
| MATH/algebra/train/408 | 63 | 15:33:36.600887 | 16:16:59.887525 |
| MATH/intermediate_algebra/train/532 | 78 | 15:33:39.379483 | 16:16:48.539931 |

### 明确偏离的条款

- #211 §2/L31要求ANY输出前全部源码/fixture/队列/分析冻结：不满足。V1→V2、动态oracle、控制/tape/诊断具体操作数和完整统计文件均分期形成。不能把“每次调用前有本地JSON”和“正式计时前冻结”替代该条款。
- §1要求实现前读完固定资料：#210补读记录为15:16:42，已经晚于V1几何和V2自然资格，早于全部干净计时。它是已确认审查顺序偏离。
- §3允许R作为独立正确性参考、§5明确干净计时不逐请求导出全KV：这些本身没有违反；输入已受先前路径影响的资格必须按自适应/有限资格披露。
- 未发现偏离§5/6的正式16输入、cap96、8臂、8个Williams块、四主比较或既定统计。完整清单晚于正式R输出，早于C/D输出，时间边界必须同时报告。

## 2. 输出依赖、失败保留与参考独立性

| 资格根 | prompt token | 本轮自然cap | 本轮根/规则首次提交 | 新R首次完整logits | 首候选heavy首次logits |
| --- | --- | --- | --- | --- | --- |
| GSM8K/test/806 | 99 | 128＋cap1 | bc650e04 / 14:50:48 | 14:51:07.900527 | 14:52:40.616241 |
| GSM8K/test/70 | 75 | 32 | bc650e04 / 14:50:48 | 14:51:25.341830 | 14:53:03.758545 |
| GSM8K/test/986 | 92 | 32 | bc650e04 / 14:50:48 | 14:51:39.421857 | 14:53:10.392812 |
| APPS/train/65 | 704 | 32 | bc650e04 / 14:50:48 | 14:52:17.058851 | 14:53:24.067209 |
| M2/Qwen8B/termination-fixture-v1 | 20 | 128 | 14859fc4 / 15:16:43 | 15:18:38.287158 | 15:18:59.105001 |

同工作量操作数保持上述前四根；短根E256对应within头248/cross头252，长根E768对应760/764，均追加8个独立R token。没有挑选更快的延续。EOG提示是父#209已暴露的终止fixture，其Linux8B结果此前已知；本轮仍用原Windows8B R独立生成结果，不把它称作新盲根或借用Linux数值参考。[QUALIFICATION_TASKS.json](https://github.com/leecdiang/HeteroSpec/blob/ba5b4c8e01d50d4bfaab1ac3908f798347be063a/benchmarks/rtx_q8_transfer_20261109/results_20261109/QUALIFICATION_TASKS.json)、[EOG_FIXTURE_SOURCE_209.json](https://github.com/leecdiang/HeteroSpec/blob/ba5b4c8e01d50d4bfaab1ac3908f798347be063a/benchmarks/rtx_q8_transfer_20261109/results_20261109/EOG_FIXTURE_SOURCE_209.json)、[DIAGNOSTIC_OPERANDS.json](https://github.com/leecdiang/HeteroSpec/blob/ba5b4c8e01d50d4bfaab1ac3908f798347be063a/benchmarks/rtx_q8_transfer_20261109/results_20261109/DIAGNOSTIC_OPERANDS.json)。

后续资格输入**确实依赖先前输出**，不能写成完全独立挑选。动态R用实际候选的token路径定位所有待比较logits/已提交状态；控制fixture用原始R贪婪token并在指定拒绝位次改一个token；诊断延续用既有R长度/EOG和实测cache extent确定是否能构造；tape重放在producer输出后绑定具体七提案。资格最大service/token还用于完整面板时间准入估计，未改变已定cap/输入/臂/样本量。

本审计重新构造全部112个控制用例，并从候选全轨迹逐行查找独立R参考，没有依据旧通过标记跳过缺失行。52个R工作单元均绑定原可执行文件SHA256`73113940…603e249`；R输入只含模型身份、token ID、位置/观察选择，没有候选浮点值或expected-vector路径。R在反事实提案路径上强制计算是条件数值oracle，输入不是独立随机样本；但期望浮点由原R独立计算。当前完整向量、argmax/端点及active-KV相等证据未出现循环使用候选浮点作参考的迹象。

四开发根与既有rtx188清单相同，APPS/train/65的704-token长失败根保留在所有8臂自然重/轻、native producer和长边界几何；没有全局排除它。128/32/32/32 horizon及短根/EOG两个tape子门槛也可在父#209源码中找到，早于本轮对应自然输出，不能把它们当作新出现失败后缩短/删根的证据。它们仍只提供有限覆盖；#62 MBPP等其他历史失败并未在本轮全部重新执行。[qualify.py](https://github.com/leecdiang/HeteroSpec/blob/ba5b4c8e01d50d4bfaab1ac3908f798347be063a/benchmarks/rtx_q8_transfer_20261109/results_20261109/pinned_sources/benchmarks/server_expansion_v1/M2/qualify.py#L33)、[panel.py](https://github.com/leecdiang/HeteroSpec/blob/ba5b4c8e01d50d4bfaab1ac3908f798347be063a/benchmarks/rtx_q8_transfer_20261109/results_20261109/pinned_sources/benchmarks/server_expansion_v1/M2/panel.py#L55)。

183个工作目录与账本逐项对应，175 COMPLETE＋8预定拒绝，无已记录的非预期native失败槽被替换。固定诊断中不利的GSM8K/test/70／loop4／cross格子仍保留（其聚合q8更慢约6.36%），没有从四来源合计删除。没有在已存记录里发现有利筛选、容差变更或失败后换输入；不能据此证明别处从未尝试/丢弃过未记录输入。

## 3. 实际离线复核与边界

| 材料/检查 | 本次实际操作 | 结果与限制 |
| --- | --- | --- |
| 完整F32 target向量 | 6,232次全151936维比较；重读字节、有限性、argmax及完整SHA256，与独立R前缀匹配。 | 0不一致；不是只读旧passed字段。 |
| active target KV/frontier | 1,224次状态比较；新解析器从序列头、dense位置、36层F16 K/V布局提取全部active字节。frontier另作完整向量比较。 | 0不一致；只排除合同原本不要求的inactive padding，无数值容差；token身份由冻结调用轨迹绑定。 |
| 事务及覆盖 | 176个heavy请求、1216个clean请求重新推导pending/接受/拒绝/bonus/trim/cap/EOG，核对物理宽度/输出mask及clean API；48个几何case。 | 全部吻合；k3拒绝rank0..2、k7 rank0..6及所有已注册cap/续转被实际检查。 |
| 同工作量 | 32 heavy资格＋160 clean算子请求的8行输出、初/末active KV/frontier、实际{4:2}/{8:1}及零draft重新检查。 | 均吻合；全部4来源/8格/ABBA原记录保留。 |
| heavy/clean桥接 | 64对请求逐字段重核相同输入、端点、cycles、KV bounds、执行切分与计数。 | 全部吻合；clean内部未保存的KV仍不能逐字节重算。 |
| proposal ownership | 1,832个live草稿完整向量文件重新哈希，与producer记录hash/seed/proposals逐项绑定。 | producer侧5根只导出hash，未导出独立F32文件；该侧不能称为重新读取原向量比较。 |
| 负例与实际dispatch | 重读8个原生failure.json、预定错误类别、退出码及已记录GPU图形状/物理计数；不是只读EXPECTED_REJECT标记。 | 错误类别与资格一致；没有重执行native guard或GPU dispatch。 |
| 源码/版本/DLL | 重哈希1126项源/工具/链接文件，V2前端及各worker exe；重核实际模块记录和当前数值DLL字节。 | 两套V2：loop4 fb6cbf2a…、packed 3c8968fa…；同一套对应全部heavy资格、C和D。V1只作早期几何，未用其passed代替V2。 |
| 不可读取/未捕获 | 本次数值读取没有丢失/无法打开的所需已有文件；原始材料8102个路径、约53.69GB读取量。 | 正式clean没有全向量/KV捕获、producer侧没有原F32字节；这些是未生成的材料，不能用通过标记补齐。 |

新解析器不导入旧`active_kv.parse`或`trace_from_row`；采用另一种K层后V层的规范化字节序再比较完整hash。每个重读二进制还核对既有归档索引的大小/SHA256，索引本身与固定结果提交中的承诺绑定。原GPU向量/KV采用零容差全字节hash相等；统计独立实现仅对求和重排产生的浮点舍入使用1e-12一致性阈值，二者不能混同。实际逐文件证据见[RAW_FILES_READ](evidence/RAW_FILES_READ.json)、[来源/运行时](evidence/SOURCE_RUNTIME_RECHECK.json)。

旧QUALIFICATION、NATURAL_COMPLETE、EXTRA_COMPLETE、GEOMETRY_V2_COMPLETE、TAPES_COMPLETE和SAME_WORK_QUALIFICATION_COMPLETE这六个汇总文件另列为[仅读声明/标记](evidence/LEGACY_MARKERS_READ_ONLY.json)，不把其passed布尔值当成本次数值复核。本审计没有重新执行原GPU资格程序；新逐字节复核、原运行记录重核、仅读标记和未生成材料是四类不同证据。

### 一个真实的联合覆盖缺口

已有176个重捕获自然/控制/tape事务中，VERIFY跨真实extent的次数为0；强制几何和同工作量测试另行覆盖256/768跨界，其原始字节均通过。正式面板在3个根（APPS/train/296、305、603）上有288个跨界cycle，其中128个发生拒绝。APPS/train/603在k7 base251/254/255等处具有跨界拒绝/回退，但旧clean对应KV字节不存在，不能离线证明这些旧时刻全部active KV与R逐位相同。

这不是发现原始数值不相等，也不是§5要求把1024条正式计时全部重捕获：[PLAN.md](https://github.com/leecdiang/HeteroSpec/blob/ad9fb6846dd979c3a76d3c415c74fa9f86565f7d/benchmarks/rtx_q8_transfer_20261109/PLAN.md#L79)明确将重捕获与干净计时分开。它是将分离的几何/自然资格推广到“自然跨界＋拒绝回退”的证据强度边界，必须保留，尤其历史上端点一致并不保证active-KV一致。

## 4. 正式分析与首worker修复

本审计从64个原始worker的1152个receipt重新构造8×16服务时间矩阵，逐字节哈希核对汇总记录，验证每arm/root恰有8次正式测量，全部输入、cap、root permutation、8×8 Williams位置/56对块内有向相邻均与`2a884e28`相同。以整数cluster重数矩阵实现独立bootstrap，复算10000次抽样及两族区间，与旧实现只差统计舍入。分析源码从事前清单提交至最终提交未变化；没有发现看C/D结果后改主比较、删臂或换分析的记录。

| 主比较 | 复算变化 | 98.75%调整区间 |
| --- | --- | --- |
| arm1/arm0 | +13.835% | [+8.400%, +21.121%] |
| arm3/arm2 | +13.818% | [+8.566%, +20.163%] |
| arm5/arm4 | +14.588% | [+9.240%, +21.362%] |
| arm7/arm6 | +13.578% | [+8.898%, +19.800%] |

首live worker执行16:16:26.423872～16:17:12.120805，原生18请求已完成；错误记录16:19:52，修复提交`da569cf8`16:22:19，第二worker16:22:24开始。间隙**312.135秒**。本审计重哈希该worker全部30个修复封存文件；仍是同一个已收费attempt，完整job/源码/receipt与计时未被重写，0 GPU重跑。

独立重现旧读者错误：真实3+1切分中的`requested_rows`已经是caller-global `[0,1,2]`和`[3]`；旧读者再次加3，得到`[0,1,2,6]`，修复后为`[0,1,2,3]`。源码差分还增加原始R primer端点核对、封存worker复用和同值标记幂等检查；本审计核实这些变化，不能把修复简写成只有一行。原生前端、可执行文件、输入/顺序和统计源码均未因此变化。[READER_REPAIR_ADMISSION.json](https://github.com/leecdiang/HeteroSpec/blob/ba5b4c8e01d50d4bfaab1ac3908f798347be063a/benchmarks/rtx_q8_transfer_20261109/results_20261109/READER_REPAIR_ADMISSION.json)。

修复不可能追溯改变已写入的native服务时钟，但312秒停顿可能改变后续热/缓存环境，所以不能断言“计时完全不受影响”。所有8块保留。作为明确事后描述性检查，整块排除session0后的四变化分别为+14.286%、+13.729%、+14.349%、+13.595%；全部8块的单块方向也均为k7更慢。这削弱“结论仅由首块间隙造成”的解释，没有估计出停顿的因果效应；该敏感性不替换预注册主结果。

## 5. 论文使用与最小补证

可保留：测试过的V2物理宽度/全输出/active-KV有限资格；相同状态/8 token/8行输出的四来源算子描述；此16根、cap96、单Windows GPU配置下四个k7/k3服务比和根级区间，以及完整不利结果。表述应为“采用披露偏离的分阶段资格，并在正式计时前冻结完整八臂清单后，本机面板观察到k7耗时增加13.6%～14.6%”。

必须限定/不可使用：全资格全部事前冻结、对任何输入普遍无损、全部正式natural跨界回退KV已严格验证、独立盲资格、M优越性、GPU架构因果、kernel归因或次要区间跨零即等价。未独立重算词表分词；未重做native guards、producer侧F32或历史进程内存；未核实任何材料以外的尝试。

**首先采用的最小补证是本次已完成的零GPU审计**：保留本报告、逐项时间线、原始字节复核与完整统计复算，并收窄上述表述；无需因冻结程序偏离重跑1024条。过去的全局冻结违例不能通过事后重跑抹去。

若论文要把“自然跨界拒绝回退也经过full-vector/active-KV验证”作为更强的主证据，现有旧clean材料确有缺口，建议先审阅[可选补证草案](evidence/OPTIONAL_SUPPLEMENT_DRAFT.json)：按原输入顺序选第一个在k3/k7均实际跨界且拒绝的根APPS/train/603（只按覆盖选，不按速度），8臂各1个heavy资格请求；从已有clean完整token轨迹预先生成全部29个独立R强制参考case。全部token/位置/参考队列可以在任何补证新输出之前一次冻结。它是事后针对性补证，不是新的盲性能确认。

29个R case是现有单一路径原生接口下，合并共享前缀后留下的29个最大叶路径，覆盖64条已知完整trial路径及所需提交状态；37请求是这份固定“8臂＋完整现存轨迹复核”方案的精确预算，不宣称所有可能实现中的理论最小值。新准入仍需单独确认资源与时间，不将16×900秒超时上限当实际运行预测。

| 补证资源 | 明确预算/门槛 |
| --- | --- |
| 本次实际新增GPU | 0请求、0行；旧账本字节未改。 |
| 可选、尚未执行 | 29个R case＋8个heavy候选＝37逻辑请求，16 native worker，18543保守行；无正式计时、无新预热/profiling。 |
| 成功后资格累计 | 463＋37＝500/512，尚留12请求；不得借用其他阶段。 |
| 成功后RTX累计 | 2716/3072请求、2872841/4000000行；新tranche1812/2048。执行前需重新核对最新账本。 |
| 原始捕获存储 | 按既有轨迹估计约12.29GiB＋日志/余量；使用新C盘目录，保留10GiB底线及D盘20GiB底线，不删除旧材料。 |
| 停止条件 | 原始trace改变、任何完整向量/状态不等、guard/资源/预算失败即保留并停；不临时扩参考、换根、降标准或重跑正式面板。 |

补证不是自动批准或自动任务，本仓库只保存输入草案，没有执行器。若只保留上述有条件的有限观察结论，可不启动GPU补证；若需要更强联合状态断言，这37请求是针对当前真实缺口的有限方案。即便通过，也不能恢复旧clean未导出的KV或消除过去冻结偏离。

## 6. 审计边界与交付

未修改#213已有数据、通过标记、失败记录、基线或论文；未合并、发布Release或提交论文。未启动GPU、32B/B570、分词native程序、计时重跑或新模型。原ledger哈希在[RUNTIME_TIMING_SCOPE](evidence/RUNTIME_TIMING_SCOPE.json)再次核对。审计生成物、读取器、逐路径hash、完整比较明细与37请求草案均置于本新目录；旧路径保留原样。

