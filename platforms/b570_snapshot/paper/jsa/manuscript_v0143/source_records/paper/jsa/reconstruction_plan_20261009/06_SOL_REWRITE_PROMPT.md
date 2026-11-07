# 交给6.1sol：依本PR重写JSA全文

你要完成的是正式的英文全文重写与稿件交付，不是继续产生空泛建议。作者已选择JSA方向；本目录提供主线、交叉审稿和完整证据去向。先读取本目录全部Markdown、VALIDATION.json和SOURCE_INDEX.json，再读取当前源码和它们引用的实际证据。不要将历史报告的“待执行”句子当作当前状态。

## 1. 基线和操作范围

- 从包含本目录的新Draft PR的精确head创建独立重写分支。其父基线是PR #69 head `21aa7b29142a1e3b7130b8e4a6a252777a91af80`；main科学稿为v0.12.1，`f3fd2aecc6288c661033ee83d5216db6481dac3f`。
- 开始前核对main、#69及本PR是否变化；保留新科学合并，避免拿旧快照覆盖后续工作。此PR当前stacked目标是 `paper/jsa-v013-20261009`。若父PR状态变化，按真实Git祖先关系选base，不静默合并或force push。
- 以 `paper/jsa/manuscript_v013/` 为源码与证据起点，新建 `paper/jsa/manuscript_v014/`（若该目录已存在，先核实而非覆盖），保留所有旧稿、旧图、实验、manifest及冻结标签。必要的JSA当前入口更新放在新PR，避免把旧版本记录改写成新结论。
- 本轮仅使用已有证据重写、做CPU核查和需要的可复算图表。禁止新模型推理、GPU实验、warmup、结果导向调参、补造counterfactual/耗时/作者信息。第二家族仍pending；预留自然插入位置但不伪造预期结果、不在正文留“待填数值”作为完成稿。
- 输出新Draft PR；不自动合并、不投稿、不改变仓库可见性、不对外发布数据或创建DOI。

## 2. 固定写作方向

按 `03_STORYLINE.md` 的三个RQ完成论文：在哪里控制状态与路径；哪些阶段约束足够；合格方案是否值得推测。推荐标题为 Reference-Preserving Speculative Decoding on Consumer Systems: Diagnosis, Repair Scope, and Paid Cost，可在保留范围的前提下精简。

贡献写具体实现和具体证据，不用“我们提出一个框架”掩盖未实现的算法。避免按PR、日期或版本顺序讲故事。将严谨性限制放在首次定义和对应实验边界，不在每段重复同一套免责声明。正文以系统架构读者理解为标准，定义UB、k、natural donor、pending state、endpoint及R/M/C，不能假设读者读过仓库。

必须新增或加强的内容：

1. 实际runtime transaction与控制位置示意；从源码解释query-batch图变换、保留的batched operators、phase开关及graph reuse/状态边界。先核验源码再写，不能把操作调用数叫kernel launches。
2. 把B570 single-block结果补入RQ1：即时不变、下游变化；保留RTX state/path effect与B570whole-recipe、duplicate-column限制。
3. 用16-mask完整pattern支持有限scope；区分qualification-selected和speed-selected；mask3相对mask15额外decode收益未过门槛。
4. 将RTX24与付费R/M/C作为主成本结果，1.742×请求必须同时解释1.683×无draft路径与1.035×增量；保留7/24回归、第二轮反向、timer细节。
5. 将fixed-UB width与B570强R负结果用于阻止不成立的设计结论；M4和358H为控制与draft优化边界。具体写清哪些工程决策因此改变。
6. 使用 `04_EVIDENCE_LEDGER.md` 把每组实验映射到主文、S1或明确历史记录；保留#58/#63局部正例、H1失败、H2/replay、bridge、selection、V3终止和raw suffix/missing，不因叙事便利抹掉。
7. 最近工作比较表，承认LLM-42、Stage-Replay、Vosti、batch-invariant和consumer-cost分析已有贡献；核验原文和发表状态后界定本稿增量，不能声称未经测量的优势。

## 3. 不可越过的科学口径

- 一家族不是多家族；四平台不是统一机制的四次复制。晚期graph为Qwen3非flash、greedy、single-slot等实际合同。
- 当前离散decision、完整response、endpoint、raw suffix、logits、KV全同是不同主张。
- 原有完整数组通过不证明功能正确率或普适无损；B570 first-EOG/cap128不提升成raw-array equality。
- 新输入是accessible-project-unused，在测过后变成exposed；不是训练未见。不能将后来追加的ordinary-R CPU分析写成事前固定的主要比较。
- R是已付费合格ordinary参考，不是已证全局最优；比率identity不提供组件成本归因。当前C未启用state-transfer分支，不得给它虚构相关成本。
- B570正式119/120缺失原样保留；R/M/C各15完整task pairs，oldN1只14。旧实现改进不等于胜过ordinary。
- 所有历史primary估计、CI、random seed与timer保留；如新做CPU重析，明确命名和来源，不替换旧统计。
- 不把全文重写称为已完成的外部peer review、商业查重或硬件复现实验。

## 4. 期刊准备与视觉

遵循 `01_JSA_REQUIREMENTS.md` 及实际官方指南；elsarticle单栏审阅格式、≤250词摘要、1–7关键词；准备3–5条≤85字符highlights。图表必须正文明确引用；图为独立矢量PDF，表/公式可编辑。具体视觉优化可按作者后续要求完成，但本轮产物应达到清晰可读、无截断/重叠。

每张图只回答一个关键问题。F1结构、F2cross、F3phase与F4R/M/C优先；不为了图多而制造重复。准确保留成本比率方向，不将独立study放一张可误读的硬件排名图。数据图使用代码和真实导出，不使用生成式位图代替科学数据。

完善软件/预印本/正式会议文献、网页访问日期与引用双向对应。不能机械凑25篇或追求没有来源的近五年比例。作者姓名/单位/贡献/资助/冲突/数据发布位置由作者确认；用清楚的作者待办记录承接，不编事实。AI辅助声明如实准备，未得到作者实际审阅不能写成已获最终批准。

## 5. 实际交付与验证

交付：新英文main.tex及章节、独立补充S1、references、highlights、主文PDF、补充PDF、干净重建的Overleaf作者包；中文重写说明、claim→source精确映射、作者投稿待办和QA报告。若打包正式EM源包，先核对当前通用LaTeX/EM路径要求；不要把作者工作ZIP直接宣称提交无障碍。

核查应解决具体风险：

1. 验证所有继承证据字节与base一致；按需要运行已有CPU核查。先确认函数行为，避免不必要的图重生或改写旧文件。
2. 从保存绝对耗时重算关键比率与资格join；验证missing、任务/重复单位、mask集合和图表输入。脚本PASS不等于private raw认证。
3. clean compile及源码ZIP解包重建；无未定义引用、溢出、未嵌字/Type3问题。读取并逐页检查最终PDF，特别是新表和补充引用。
4. 对新增正文做主张审计：每个贡献、数字、因果词、泛化词有明确证据级别。保留第二家族缺口和最近工作重叠；不以版式优化换取夸张结论。
5. 检查最终PR diff只改获授权的JSA稿件/说明，新实验和所有历史文件保持不变；记录base/head与交付哈希。

完成后报告：标题与论证结构改了什么；核心证据怎样进入全文；验证范围；还需作者提供什么。提交新的Draft PR供作者审阅，不因没有第二家族而停止现有稿件的完整重写。
