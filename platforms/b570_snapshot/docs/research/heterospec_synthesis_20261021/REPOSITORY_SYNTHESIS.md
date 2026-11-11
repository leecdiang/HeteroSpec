# HeteroSpec：全项目证据回顾、叙事修订与 JSA 补强路径

2026-10-21。仓库读取基线：`50dbd0a931620168c6227d991851cd2dffb46fe8`（PR138 已合并）；稿件基线为对应的完整 v3 源码对齐稿。本文是作者授权的研究与编辑分析，不是新增实验结果或外部审稿决定。

## 1. 本轮究竟读取了什么

回顾覆盖了根目录与全部 benchmark 子目录索引、当前 25 条开放 PR 的元数据/研究状态、28 组历史实验的完整去向表及叙述、当前论文全部正文/补充材料、报告级数据与检查器，并重新读取了关键原始结果报告和 AV 修复补丁。M4、358H、早期 RTX/B570 失败、状态干预、数值重放、映射控制和最新服务面板均纳入研究判断。

这是一轮仓库级科学证据回顾，不是每个二进制、每行旧代码或完整多 GB 原始归档的逐字节审计。大型 raw logits、模型权重和原生运行时没有重新下载或执行。文件级覆盖记录见 `READ_COVERAGE.json`。停止/未执行记录不因新稿而改变；CPU8/F0 阻塞状态没有被解锁。

需要区别三个层次：原始数据中已经有的结论、这轮重新强调的综合判断、仍然需要新实验验证的假设。以下逐项标明。

## 2. 之前没有充分突出、现在值得作为论证中心的结论

### A. 数值修复的范围会改变 drafting 的盈亏，而不只是改变一个 kernel 的耗时

**性质：已有结果的重新组织，加上一项明确的事后代数汇总；不是新实验或新定理。** 旧稿 Equation (8) 和原始七臂数据已经蕴含交叉点，但主图只画了 QB 的 draft 增量。

令 `D_L = T(M_L)/T(C_L)`。同一输入、session 权重和请求计时窗口下：

| 模型 | 全局串行 GS | 局部逐 query PQ | 局部 query-to-batch QB |
|---|---:|---:|---:|
| Qwen3 | 0.710 | 1.125 | 1.144 |
| SmolLM2 | 0.592 | 0.616 | 0.634 |
| Llama | 0.724 | 1.107 | 1.117 |

大于 1 表示加 draft 更快。Qwen3/Llama 在 GS 下不划算，在两种局部修复下划算。**PQ 已经跨过盈亏线；QB 的独立贡献是进一步降低局部表示成本。** 因而不能把 GS→QB 的全部差额或 RTX 后续 41.8% 都归因于 QB。

本轮显式计算 `Gamma = D_QB/D_GS = (C_GS/C_QB)/(M_GS/M_QB)`，分别为 1.611544、1.070660、1.541572。它描述原面板中的 repair–draft interaction，不是 attention 占比、GPU 加速倍数或新确认试验。六位小数输入的舍入误差单独传播；这些区间不代表统计置信区间。

这条结论的工程含义是：不能先脱离修复实现判断某一 target/draft 模型对是否“值得推测”，再把数值一致性当成成本无关的补丁。应对同参考的完整实现共同选择修复范围和 draft 政策。

### B. QB 的价值并不依赖 draft 必须成功

**性质：原七臂表格已有正结果，本轮提高可见度。** 原面板 `R/M_QB` 为 1.334051、1.369890、1.426161，且每个任务都偏向修复后的 target-only 路径。SmolLM2 因而给出一个有用的分离例子：reference-preserving batching 有收益，而加 draft 不划算。

这并不等于击败现代最优 serving stack；R 是指定的串行数值参考。其价值是说明“有用的数值修复”和“有用的 speculative policy”是两个可独立成立的命题，而不是把 SmolLM2 的负 draft 结果解释成整个方法无效。

### C. 跨 query 的并行与单个 query 内的数值求值顺序，是不同的设计自由度

**性质：已有源码和对照支持的局部机制综合。** PR132 的关键不是换一套“更准确”的算术：它保留原有 nc AV shader、令 V batch stride 为零，保留 probability/output 的真实 stride，并扩大独立 query workgroup 的 dispatch。147 个既有编译对象复用，未修改 shader 算术。

对照很有解释力：packed AV 路线在 key512/q2 的 8,192 个值中有 7,160 个不一致；保留 nc 路线后，六个 key256/512 × q1/2/4 坐标各阶段完全一致，后续真实 q2 请求另行通过。

因此，值得带走的设计规则是**在 query 之间暴露并行，在 query 内保留已验证的求值路径**。这比“某 GPU 不支持 QB”或“数值一致性必然要求串行”更有信息量。该规则的实测域仍是记录的布局、类型和形状；它不是任意 backend 的浮点等价证明。

### D. 输出相同是一次部署的合格条件，不是缓存组件的通用替换接口

**性质：已知有限反例的系统化解释。** /1011 的两个完整自然状态输出相同，但 20 个 subset/direction 坐标中有 16 个混合后产生第三轨迹；/1249 则保持稳定。V0 有效而 K0+V0 无效的反例还否定了“约束更多组件必然更正确”的单调假设。

这让 phase/layout 进入图缓存 key 的实现与 KV producer provenance 联系起来：形状相同、端点相同、文件 hash 各自正确，都不能替代正确的 producer–receiver 绑定。论文不需要把它包装成新的程序等价理论；它已经能支持一个具体的迁移义务：记录 prefill recipe、位置、pending token 和恢复语义，再验证进入局部变换的状态。

### E. 更准确的预测、更高的接受率、更少的 API 调用，都可能不是正确的优化目标

**性质：跨历史项目的定性综合，不合并不同平台的计时数字。** M4 的 prospective guard 在 60 个 held-out prompts 上相对 target-only 有收益，但固定 k2 的 aggregate 更好。RTX selector 对 12 个 held-out synthetic 坐标的均值方向预测正确，计入 lookup 后仍比固定 QB 贵。358H 的 CPU/NPU draft 接受率都约 75%，完整服务却都慢；固定 UB4 扩大 k 的历史实验还出现调用减少、physical micrographs 增多和请求变慢。

共同教训不是“自适应都没用”，而是**预测目标应当是可执行、同参考、付费后的完整动作，而不是 acceptance、API 数或局部 winner 标签**。这也是为何不应再为了多一个新控制器而重开一个统计噪声很大的支线。

### F. B570 真正值得验证的候选是 submission granularity，而非已经证伪的线程参数叙事

**性质：待检验假设。** PR135 的 8→1 线程参数并没有证明实际 worker 数减少，GET_ROWS/SET_ROWS 本来可能只用一个 task。另一个 draft-prefill submission 变体已经做到一个 API 调用、physical q1、346 个原 logits 不变，但审阅提交没有完整干净计时。

这给出一个合理候选：把“合并 API 提交”与“改变数值 microbatch”解耦，减少主机交互而保留参考。只有新的同参考 balanced timing 才能证明它有收益。当前不写成论文性能结果，也不以它宣布 B570 baseline 已经最优。

## 3. 使用 anti-defensive-writing skill 后的具体改法

实际读取：`Adkid-Zephyr/anti-defensive-writing-Skill` 的英文 `SKILL.md`，Git blob `87a163642daa5674a7fed82eb9112ae703ee0e73`。这次采用的是按优势组织论证、去除实验日记结构、贡献先行和结论收束；没有删除会改变结论的失败、未完成数据或对照。

摘要和引言改为“部署问题→QB 方法→独立 PQ/QB 收益→修复范围与 draft 交互→迁移条件”。图4C展示 GS/PQ/QB 三种 draft value，而不是让读者自己从补充表重建。架构讨论改为三个设计规则，减少重复的 no-RTL/no-PPA/no-universal 句式。实验身份、统计单位和适用范围在相应定义及集中 scope 中保留；失败路径仍明确无合格成本。

主线没有转成广告口号。RTX 的 5.208% A/A、两个反向 session、SmolLM2 和 B570 的负 draft 经济性、80 格状态矩阵、44/112 向量覆盖、原始任务退化及未完成 prefill 计时均保留。

## 4. JSA：怎样真正提高录用机会

官方 scope 包含 system software 和偏软件的 HW/SW co-design，并明确要求案例贡献超出某一个软件设计。因此，本稿的机会在可复用图变换与迁移条件，而不是添加没有收益证据的 RTL。来源：https://shop.elsevier.com/journals/journal-of-systems-architecture/1383-7621 （2026-10-21核对）。

优先级如下：

1. **本轮能完成的 P0：** 把局部修复的设计选择和 matched counterfactual 讲透；让所有新数字可由保存表重算；提供 reviewer 可用、独立于私有 GitHub 权限的最小源码/数据包。不要以大量自检次数替代复现，也不要把旧实验混成新的总体样本。
2. **最可能改变审稿判断的 P1：** 对冻结实现做未见自然输入和真实 visible-key 长度验证。当前数值 replay 的 physical key extent=256 并不代表真实长上下文；跨日期重复旧输入也不补输入泛化。独立实验计划见 `docs/experiments/heldout_reference_transfer_v1/`，是设计而非已运行结果。
3. **基线补强：** 在同一参考契约下审查更强的 native/fused 或缓存优化路线。先证明可比，再报告速度；不允许为了比较方便把不同输出当作同一任务。若无法满足契约，记录拒绝原因和覆盖，而不是声称已经击败该系统。
4. **外部复核：** 请不参与本轮改写的研究者从干净目录构建、复算报告表，再抽查真实模型输入/输出；这比再增加几千次技术重复更能缓解 artifact 的可信度问题。模型和 raw archive 的公开方式、许可证及访问应由作者决定。

上一轮给出的 JSA 25–40% 是未经校准的主观估计，不会因本轮润色自动调高。现在改善的是读者能否识别真实贡献。P1 的结果若维持参考、获得非零覆盖并证明同契约成本收益，才会实质性改变对可迁移性的判断；负结果也必须进入结论。

## 5. 仓库与发布的实际问题

根 README、REPO_STATUS 仍主要指向 Oct10/v0145，而 paper/README 指向已合并稿件；CITATION.cff 仍称“论文出来后再引用”。这些过期入口会误导新读者，建议下一次仓库同步修正，并将旧内容原字节保留到 history。仓库是私有的，不能把私有路径当成审稿人已经可访问的 artifact；本次 arXiv 包包含报告级源数据、分析脚本和完整正文/补充材料，以减少该依赖。

arXiv 官方要求 ancillary 目录不包含 TeX。上一包两张被正文调用的表位于 `anc/closure/`；本轮移到 `tables/`，更新生成器和测试，并在不带 anc 的干净目录重编译。提交包不含旧审稿概率、私有编辑记录、编译日志、模型二进制、凭据或本机路径。日志与审阅意见另交作者保存。

## 6. 处置与来源

当前稿件可用于 arXiv 更新前人工检查；本轮没有提交 arXiv、修改许可、运行模型、合并旧 Draft 实验 PR 或复活已停止的研究。新实验设计仍须机器身份、输入清单、资源预算及作者执行授权，不能把一个计划 PR 当成执行通过。

关键读取来源（固定提交）：
- 主线、历史ledger、当前论文：`50dbd0a931620168c6227d991851cd2dffb46fe8`。
- 七臂：`benchmarks/rtx_querylayout_mechanism_v1/RESULTS.md` 与论文 `anc/rtx_repair_cost.csv`。
- M4：`benchmarks/m4_runtime/M4_RUNTIME_CLOSEOUT.md`；358H：`analysis/358h_phase3_summary.json`。
- 映射与生命周期：`benchmarks/rtx_reference_envelope_v2/RESULT.md`；架构同策略控制：`benchmarks/rtx_reference_packing_v1/RESULT.md`。
- GQA/AV补丁：`7e98e288b4137c998604a0809c7e956474967de1`，`benchmarks/b570_gqa_av_preserve_v1/{RESULT.md,av-preserve.patch}`。
- B570政策及未完成submission：`e44c4df04c895b55ef734ee7b0659189158f95ab`。
- RTX服务：`9868acfbb2ae2e4b753ad20b680c333d55289dc0`，`benchmarks/rtx_platform_closure_v1/execution_v2/RESULT.md`。
- 已有组合性/普适性综合（避免冒称首次发现）：`3bc3c2f018acd39ca81911c7725175d5c0be306a`，`docs/research/heterospec_reconstruction_20261014/GENERALIZATION.md`。
- arXiv文件规则：https://info.arxiv.org/help/ancillary_files.html 与 https://info.arxiv.org/help/submit_tex.html 。

## 7. 本轮仓库写入状态

本轮 GitHub 连接器的实际工具清单仅提供读取动作；写入工具发现没有返回 create_tree、分支、提交或 PR 创建动作。仓库本轮没有改变，也没有新 PR 编号。交付包附已在隔离目录通过 git apply 与编译验证的补丁、两份 PR 说明及实验设计，供具备写权限的执行环境同步。当前 main 仍为上述 PR138 合并基线。请勿把本地成稿或补丁当成已经推送的远端结果。
