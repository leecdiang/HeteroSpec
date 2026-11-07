# 方法、验证与范围

## 本次是什么

作者授权的主线重构分析，不是期刊正式审稿，不作录用概率估计。现有论文已具备完整方法；本次对比其已陈述贡献和新增证据，生成多个候选主线，按最近研究和证据可承担程度作取舍。没有生成可直接替换的摘要、Introduction、Methods正文。

六份Skill来自公开 `K-Dense-AI/scientific-agent-skills`，实际读取范围和blob见SOURCE_LOCK。这是同一模型的六种方法参照，不是六个独立专家意见；未安装/执行其付费agent、统计库环境或图像接口。医学GRADE/临床审查模板不生搬到软件实验。

| Skill | 实际应用 |
|---|---|
| scientific-critical-thinking | 逐claim标明观测单位、反例、缺失与可承担解释；CPU准入不等于native资格 |
| hypothesis-generation | 候选解释、竞争解释、未见域预测分离；数据知情预测不称原始预注册 |
| scientific-brainstorming | 比较实现only、机制only、条件统一三路线，记录为何不选前两条独占主线 |
| statistical-analysis | 保留request/process/session/task/backend层级；不提前合并E2五session或新建CI |
| peer-review | 针对reshape优化、强近邻、两平台拼接、因果过度归因逐项反驳/补救 |
| literature-review | 定向检索及版本核对，尤其CoRun和cache-paper v2；全文获取失败明确披露 |

## 检索边界

检索日期2026-10-14；使用公开web检索和arXiv、PMLR、MLSys、作者工程文章等主源。未向搜索引擎或第三方模型发送私人实验数据。主要查询：

- `"LLM-42" deterministic speculative decoding`; `"Vosti" deterministic inference`; `"Stage-Replay" language model`; `"batch invariant" inference query length attention 2026`
- `site:arxiv.org "speculative" "deterministic" "2026" "layout"`; `site:arxiv.org "LayerCast"`; `site:arxiv.org "MarginGate"`; `site:arxiv.org "Tree-Based Invariant Kernels"`
- `"LayerCast" "LLM"`; `"Stage-Replay" "KV"`; `"The Curse of Multiple Mediators"`; `"Correctness Forensics" "Ragged"`

在候选路线形成后复查近邻，并因CoRun重新收紧泛化贡献。没有双人盲筛、完整多数据库导出或PRISMA计数，故不称systematic review；没有用引用总数证明创新。P06仅摘要与版本核实，v2 HTML获取失败；P11/12/13/15/16主要使用摘要/正式landing page作范围定位。其余阅读相关HTML方法与讨论段落，并非重新复算他人实验。论文年份/接收状态不超过所查主源。

## 证据获取与重算

GitHub插件读取固定提交的论文和实验文件；主线不依据本机推测路径。RTX原始ZIP获取未成功：当前container不能解析外部主机，下载工具也未准入connector签名链接。因此本轮没有完整raw restoration，不能把作者原机回执说成本轮异机复验。B57054向量私有子包也没有在本环境获得。

`inputs/rtx_repair_cost.csv`从完整工具文本重建，恢复CRLF后Git blob为 `e883410f6f97c65455b8fe00710478eb9051ce88`，与源文件相同。`reported_observations.json`是已提交session/scalar/count的人工转录，不是raw archive。重算只包含：

1. PR98完成面板的三类D=M/C，及舍入传播区间（不是CI）；
2. PR104每session exp(log ratio)及已报告回归数；不产生5session合并估计；
3. B570报告值的可加预测与残差精确算术；
4. canonical逻辑条件的计数依赖；
5. 四输入范数单阈值反例。

## CPU验证

最终 `python -B -m unittest -v test_reanalysis` **20项通过**，原日志见CPU_TESTS.log。测试覆盖CSV身份、21对照与panel假设、成本恒等式、舍入方向、缺失/额外/非有限数据拒绝、未完成E2禁提前结论、binary64标量重算、pair规范化、阈值反例和重复计数。

编写本地分析代码过程中第一轮测试曾发现把打印的最短十进制直接作为精确实数Fraction会与原binary64字段语义不同。已改为先按JSON binary64读取再 `Fraction.from_float`；最终数值与所给二进制浮点记录一致。没有修改任何原实验或源报告。这是本地分析代码测试修正，不是新的GPU科学失败。

20项通过只验证本PR的CPU算术与guard，不证明论文正确、完整raw已复验、E1已完成或任何未见输入泛化。最关键的未完成资格在ledger中保持PENDING。

## 发布范围

新独立Draft PR仅新增 `docs/research/heterospec_reconstruction_20261014/`。不修改paper、main、旧分支或运行时；不执行native/probe/warmup/operator；不改RTX等候时间或启动B570；不创建后台任务，不恢复Zenodo/arXiv发布。图表只写职责建议，未生成论文章节或伪造数据图。
