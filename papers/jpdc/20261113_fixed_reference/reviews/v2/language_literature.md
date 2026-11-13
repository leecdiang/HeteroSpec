# 第二版：科学语言与相关工作复核

日期：2026-11-13。审阅基准为 Draft PR #243 的 `1382b2295aa9525a99ddb8f24026390ea11e95c4`；本记录描述第二版的文字与文献工作，不替代数据、代码或排版审阅。

## 实际修改

- 重写 `paper/abstract.tex`，现为 196 个空白分隔词。顺序为问题、构造、S3 强对照发现、机会与成本的解释。明确 S3 是一列算术组与 whole-call cuts，避免把 1.51% 归给 LOCAL 与四列 packing 的组合。CAS 主文件的内联摘要由整稿负责人同步。
- 重写引言：用四个已知查询引出物理范围和量化路径，再说明已有参考为何值得保留、相邻工作的差别、两类分组与状态交付。固定参考的开发场景作为用途说明，没有写成已验证的生产需求。
- 首图图注与设计者核对：四查询仅含一个完整的四列算术组；八查询是独立的已知 prefill 示例。图注明示所有实际使用的一至四列路径都需要 backend 条件。接受两提案后的 KV 边界和 pending correction 与方法节一致。
- 相关工作按研究问题组织。将算术与调度分离、固定归约、数值相关的 KV 边界、四列执行与通用 packing 放回已有工作；本文贡献落在 query-specific 物理范围、算术组、局部切分和消费者输出／状态义务的组合。
- 删除重复的否定式自辩和泛化结语；保留条件论证、已测实例与现有实现范围。未新增性能结论、实验或引用条目。`references.bib` 的已核版本与元数据保持不变。

## 关键核查与修订依据

1. 实际读取方法和实现第二版全文，检查已知查询、四查询／八 prefill、`O` 的数学定义与 all-row／last-row frontend、scalar 与 Q8 实例、online admission／capture／离线 qualification 的区别。反馈了缓存符号与内积维度重名、末尾贡献重复两点；方法负责人已修正。
2. 对照 `paper/data/closeout/service/S3_TIMINGS.csv`、`paper/data/pr218/PER_ROOT.csv` 和现有统计脚本，实际运行了 CPU 命令 `python paper/scripts/recompute_service.py --data paper/data/closeout/service`。结果为 C/B = 0.9848637428511184，95% 比值区间 [0.9821479373132749, 0.98772099465029]。摘要和引言使用对应的 1.51% 降时及 1.23%–1.79% 区间。12 roots、每 root 四轮及分层 bootstrap 口径未变；没有用 pooled ratio 替代主估计。
3. 读取同面板 `paper/data/v2/s3_cost_audit.json`，确认阶段合计与 service 主估计具有不同统计用途。我的摘要没有将 phase sums 写成新的独立样本。
4. 将引言最后一个实验解释明确写成 width experiments：等工作验证变快与更深推测增加 target／draft 工作可以并存；避免把它误写成完整 speculative application 在各面板总体变慢。

## 本轮直接读过的原始文献与代码

这里记录本轮确实重读的范围。前一版更广的元数据核验仍在 `reviews/literature_verification.json`；本轮没有声称把每篇全文或所有源码重新审了一遍。

| 来源与固定版本 | 本轮直接阅读范围 | 用于正文的判断及限制 |
|---|---|---|
| [Yang et al., Taming, arXiv:2609.11356v1](https://arxiv.org/abs/2609.11356v1) | 原始 PDF 第 1、4–6 页；标题、作者、descriptor、调度自由度及 §3.3 | 算术结构与执行调度的分离已有先例；attention 在该版本中是理论处理。当前 abs 链接返回 DisabledError，未重新核实后续版本历史。原始 PDF SHA256：`e4c5e276cde39c96d2f2a77cccbfbe713f282168a22e633c85cd22647e9ce95c`。 |
| [CoRun, arXiv:2608.14376v1](https://arxiv.org/abs/2608.14376v1) | 原始 PDF 第 1、5–7 页 | 核对 prefill、固定形状 decode、位置不变性与状态归纳的适用条件。当前 abs 链接返回 DisabledError，未重新核实后续版本历史。PDF SHA256：`7f76c92ccad53bb312acab1a511b1bbb69caf142c4bcdbf526c110c4890ce90d`。 |
| [Vosti, arXiv:2609.38981v1](https://arxiv.org/abs/2609.38981v1) | 原始 PDF 第 1、4–6 页及官方 abs 元数据 | 核对 engine／kernel 合同层次、live 和 retained KV 的含义；未执行证明工具或审计全部 kernel。 |
| [LLM-42, arXiv:2601.17768v2](https://arxiv.org/html/2601.17768v2) | 原始 HTML §4.1–4.3 与 §4.4 相关段落 | 核对 fixed-shape verification 和成功验 token 后仍覆盖 KV 的机制；未复现实验或代码证明。 |
| [He and Thinking Machines Lab, 2025-09-10](https://thinkingmachines.ai/blog/defeating-nondeterminism-in-llm-inference/) | 原始文章中 batch-invariant normalization、matmul、attention 与 cached／new KV 分界段落 | 核对既有 batch-invariance 方法和边界导致归约分组变化的例子。网页不是固定代码发布。 |
| [llama_reproducible, f0dafdbd9dba40bd0e596f74f3da5f592900fca4](https://github.com/amiller/llama_reproducible/tree/f0dafdbd9dba40bd0e596f74f3da5f592900fca4) | 该版本完整 README；与已有实现阅读记录交叉核对 | 四列路径与确定性量化属于继承组件。README 的测试设置不能扩展为任意硬件保证。 |
| [llama.cpp mmq-few.cu, 0fb8f157702702f33f4e018de8701b2569a1bc28](https://github.com/ggml-org/llama.cpp/blob/0fb8f157702702f33f4e018de8701b2569a1bc28/ggml/src/ggml-cuda/mmq-few.cu) | 重新直接获取源码，读取声明、integer MMA、column-group 数据流、异步复制／归约、量化调用和 dispatch 条件 | 现代路径已有这些优化；不据此推导实测 occupancy、流量或完整服务性能。 |
| [FlashAttention, arXiv:2205.14135v2](https://arxiv.org/abs/2205.14135v2) | 官方标题、作者、版本历史及摘要 | 仅使用 IO-aware tiling 的窄主张；本轮未通读全文。 |
| [FlashInfer, arXiv:2501.01005v2](https://arxiv.org/abs/2501.01005v2) | 官方标题、作者、版本历史及摘要 | 仅使用 KV layout 与 load balancing 的窄主张；本轮未通读全文。 |
| [Leviathan et al., PMLR 202 (2023)](https://proceedings.mlr.press/v202/leviathan23a.html) | 官方 proceedings 元数据与摘要 | 核对目标分布与并行验证的表述；没有重新独立验证算法证明。 |
| [Chen et al., arXiv:2302.01318v1](https://arxiv.org/abs/2302.01318v1) | 官方元数据与摘要 | 保留 within-hardware-numerics 范围，不转写成完整输出及 KV 逐位保证。 |
| [Liu et al., ACL 2026, 12930–12947](https://aclanthology.org/2026.acl-long.589/) | 官方题目、作者、DOI 与摘要 | 本轮使用 uncertainty-adaptive verification 的窄主张。该名称仍仅作为他人工作的引用；本稿标题不使用项目名。 |

本轮没有重新核验模型和数据集论文的全文，其 bibliographic 元数据沿用前一版已记录的官方核查。没有替这些论文添加性能数字，也没有把模型论文当作实验模型文件版本的证据。

## 实际采用的编辑指南

- [scientific-writing 2.3](https://github.com/K-Dense-AI/scientific-agent-skills/blob/2d2065fb4520fa3f3f2bcf61cff26ec8b7eba4b5/skills/scientific-writing/SKILL.md)：全文读取；用于保留证据、区分机制论证与实测结论、避免添加没有来源的需求或承诺。
- [literature-review 1.11](https://github.com/K-Dense-AI/scientific-agent-skills/blob/2d2065fb4520fa3f3f2bcf61cff26ec8b7eba4b5/skills/literature-review/SKILL.md)：全文读取；用于主题比较、原始来源核对及透明的阅读范围。这里不是 systematic review。
- [humanizer 4.0.0](https://github.com/blader/humanizer/blob/b48c832f0f809c1b5658edbb838c2521b72f2413/SKILL.md)：全文读取后编辑；去除套话、重复转折、否定式自辩和无根据的强调，保留数字、术语、条件与引文。没有生成 detector 分数或声称通过某种识别器。

未安装新的软件或 skill。技术术语和数学结构按论文含义保留，没有为了模仿个人口吻添加经历或研究结果。

## 跨分工交叉读

在其余部分仍在修订时，已完整阅读当时的评价设计、结果、讨论、结论与声明。反馈包括自然多轮 caption 应写 projection organization 固定、强对照新图应区分 phase 合计与 root 推断、8B 同 D4 图注补固定顺序，以及把 author 待确认清单移出科学正文。这是源文件交叉读，不代表最终 PDF 已完成视觉验收。

独立查看了第二版首图的实际 PNG。四面板与正文例子、caption、两类分组、输出行归属和 pending-token 提交相符。反馈将图中的 `O / FFN` 展开为 `Output proj. / FFN`，避免与请求输出集合 $O$ 重名。最终排版可读性仍须在编译页上检查。

## 范围边界与待整稿检查

- 后续整稿源文件、全部 PDF 页和修订页的独立交叉检查已完成，结果及确切 PDF 哈希见 `final_text_crosscheck.md`；以下条目保留本次初稿编辑结束时的范围。
- 此记录完成时，已读并修改摘要／引言／相关工作，已读方法和实现，并做了上述其他正文源文件的初步交叉读。补充与最终 PDF 的整稿检查须在它们稳定后完成。
- 这次文字编辑没有运行模型、GPU、外部文献实验或形式化证明。CPU 计算仅复算已有公开计时表。
- 首图 caption 已按设计方案核对；最终可读性、panel 排布和图文一致性仍以实际编译图为准，由整稿视觉检查完成。
- 所有 author information、数据分享权限、利益冲突和 AI 使用范围仍由作者最终确认；这些确认不能由语言编辑推定。
