# 第二版整稿交叉审阅：语言、数值与呈现

审阅日期：2026-11-13。范围是作者审阅稿第二版；未运行模型或 GPU，也未改变原始数据、基线和主要估计量。

## 阅读范围

完整读取第二版评价设计、结果、讨论、结论、数据／AI 声明、`supp_experiments.tex` 和 `supp_sources.tex`，并阅读它们引用的生成表格。摘要、引言、相关工作和方法／实现的前序交叉审阅见 `language_literature.md`。本轮还逐页查看了正文 13 页和补充 12 页的实际渲染图，包括完整合同补充。

重点对照了 S3 同面板阶段记录、原始 S3 measured rows、post-hoc LOO 脚本与输出、自然历史重构的实际 free cases 与独立 supplied-history 字段、89-row source-derived 字段，以及 RTX C/C1 原始公开报告和 U 的编译资源记录。完整 native tensor 或公司受限记录没有在本轮重放。

## 找到并已在源文件修正的问题

| 问题 | 依据 | 修订 |
|---|---|---|
| AI 声明末句可被读成历史上 AI 从未协助产生任何实验测量 | 声明同一段同时包括本轮编辑与较早的研究代码工作；这个广泛否定没有完整历史依据 | 改为明确限定本次 revision：没有新增 model／GPU measurements，原实验数据保持不变 |
| “只分发计时，不分发 conversation text”与新输入内容不符 | `data/v2/history_REPORT.json` 包含短 `initial_prompt_tail` 和 `body_start` 诊断文字 | 补充和数据说明现在准确承认短 token／text excerpts，说明未打包完整语料 |
| 数据 README 沿用第一版 47 个源文件的说明，漏列本轮新增输入 | `generated/figure_sources_v2.json` 列出五个固定版本文件 | 补充 47 baseline + 5 revision-2 的区别和正确 manifest 路径；不存在的 `figure_sources.json` 链接已修正 |
| 旧 32B 图注的 “all six paths include slower speculative generation”易误读为六臂均为 speculative | 图和 Table D.5 实际有四条 M 与两条 D4 | 改为 “all six paths are shown, including the slower speculative arms” |
| 第一轮编译出现末页单条参考文献 | 正文最初为 14 页，最后一页仅一条文献 | 引言删去 34 词、相关工作删去 48 词的重复表达，未删引用或必要条件；正文现为 13 页，没有改版芯或缩小正文 |

## 新解释性材料核对

- **S3 phase account。** 直接字段给出 prefill B/C = 143.926569367 / 137.984134692 s，decode = 216.663232421 / 216.689812818 s，service = 364.831679008 / 358.924859316 s。差值分别为 −5.942434675、+0.026580397、−5.906819692 s，正文和表格舍入一致。图注明确为每臂同一 48 requests 的描述性总和；未将它们变成新的独立样本，也未拆出未计时的 kernel／量化／launch 因果份额。
- **LOO。** 从 unchanged measured CSV 另行用标准库 `math.fsum` 重算，最小值为删除 `CodeContests/train/99` 后的 0.984245573564021；最大值为删除 `CodeContests/train/173` 后的 0.9855610197231932。补充准确写成 11 个剩余 roots 等权的事后 point-estimate sensitivity，没有新 CI，也没有替换主结果。
- **History timeline。** 两个 actual free cases 的初始长度 92/27、materialized head 219/154、pending position 219/154、LCP 88/23、trim 131、next input 250/551 均与源字段一致。正文和表格正确区分“token IDs 相同”与“位置／conditioning 相同”。331/1,127 被明确限定为 supplied-history 的 CPU 条件预测。
- **89-row 构造。** 两臂各保留 23 个有序 projection tiles 与 23 个 attention tiles；4→3 calls、mask 157,696→182,272 bytes、concat 19→20，以及六个额外 mask-copy nodes 均来自 source-derived 记录。正文、图注和补充未将这些逻辑量写成实测 launches、DRAM 流量或 GPU 时长。
- **宽度工作量。** 直接查看原始 `LIVE_RESULTS.json` 的 `all_eight_arms`：每臂 128 measured requests、11,472 emitted tokens；同一 k 下四方法共享给出的 cycles／proposals／verified-row counts。当前主图 caption 与补充正确写成 per-arm，不把四方法合起来冒充更大样本。98.75% 区间仍属于 16-root 配对重采样。
- **RTX 变体。** C/C1 原始公开报告支持 91/64 registers、6/3 KiB static shared 及其各自旧合同资格。U 的固定编译资源记录支持 244 registers 与 69,632 bytes dynamic shared，即 68 KiB。表格保留 separate sessions，未把资源差别写成 achieved occupancy／带宽原因。38.7% 仍属于不同合同的单输入完整提取算子；完整现代 backend 没有测量点。

主要直接来源均在 `generated/figure_sources_v2.json` 和补充 source index 中固定。此处重新检查的新增记录包括：

- [S3 COST_AUDIT，ab695a766d055f7d3c6b1fed0720c579c749bcdb](https://github.com/leecdiang/HeteroSpec/blob/ab695a766d055f7d3c6b1fed0720c579c749bcdb/benchmarks/server_expansion_v1/strong_baseline_followup_20261110/RESULTS_S3_20261112/COST_AUDIT.json)
- [实际 history 与独立预测，ef1b6427b7f3b6b7d62c4249933b33b8f810d89f](https://github.com/leecdiang/HeteroSpec/blob/ef1b6427b7f3b6b7d62c4249933b33b8f810d89f/benchmarks/server_expansion_v1/N/resident_opportunity_20261113/RESULTS/REPORT.json)
- [source-derived local cost，750346a149da58aa94a0d16016f5c451221008f7](https://github.com/leecdiang/HeteroSpec/blob/750346a149da58aa94a0d16016f5c451221008f7/benchmarks/server_expansion_v1/N/local_cost_decision_20261113/RESULTS/REPORT.json)
- [live-width all-arm 原始结果，ba5b4c8e01d50d4bfaab1ac3908f798347be063a](https://github.com/leecdiang/HeteroSpec/blob/ba5b4c8e01d50d4bfaab1ac3908f798347be063a/benchmarks/rtx_q8_transfer_20261109/results_20261109/LIVE_RESULTS.json)
- [U 编译资源，a6a92fb08678696fdaefa4904f942237b4d3c84f](https://github.com/leecdiang/HeteroSpec/blob/a6a92fb08678696fdaefa4904f942237b4d3c84f/benchmarks/rtx223_e11_u_contract_20261113/COMPILER_RESOURCES.json)

## 实际 PDF 检查

采用本轮完整读取的 PDF skill 进行只读渲染。对以下快照全部页面逐页检查了图文、公式、引用、图注、表头和边界：

- 正文 13 页，SHA-256 `9dd2de42cc281230dab793cb569ebf73e089776975294e9f08538ab8e45b9795`。
- 补充 12 页的首轮全页快照，SHA-256 `acb944a5e87b915f15a714dc2c6fbf3ee7e2fa67c3c7e544589fdf3444f39512`；修订后版本为 `fb64f3a19db23e50c53f3cd7cd61dc1f4ead09d7c28291b6c1e4e6f1172d6b49`。

图中文字在实际全文宽度可读。未见图形裁切、文字覆盖、未解析引用或丢失数值。首图 `Output proj. / FFN` 已消除与请求输出集合 O 的歧义；phase panel、history table 和 RTX table 均与本次读取的正文一致。补充更新后，逐页字词及其位置比较只在第 6、8、10 页发现变化；已重新渲染并实际查看这三页，确认 D.2 六臂措辞、F.1 per-arm counts 图注和 G.1 资源栏格式均已修正且没有溢出。

## 尚未由本轮解决的外部范围

这些检查没有扩展原来实验的统计总体，也没有证明全部 native kernels、未测输入或跨设备逐位一致。没有运行新的 GPU、tokenizer、native qualification 或原始外部论文实验。历史 AI 工具使用细节、作者信息、最终数据分享／归档权限和投稿声明仍需作者确认。当前读取范围内未发现需新增实验才能修复的主文矛盾；研究外推的边界保留在方法、评价设计和讨论中。

## 封版版面复核

整稿负责人最后在 Related work 前设置了九行 `Needspace`，保留节标题与首段；此次没有修改科学文字。已再次实际查看刷新后的正文第 10–13 页：第 10 页结束结果，第 11 页在 Figure 6 及图注后完整开始 Related work，第 12 页继续相关工作、讨论与结论，第 13 页包含数据／AI 声明和完整参考文献。没有新增孤页、悬挂节标题、覆盖或裁切。本轮复核没有再编辑正文。

封版正文为 **679,537 bytes、13 页**，SHA-256：`546514a17e11cedf7fd1790c62a0df5fd70aa4d6f114740fa1025e2905e67a69`。

补充保持 **519,139 bytes、12 页**，SHA-256：`fb64f3a19db23e50c53f3cd7cd61dc1f4ead09d7c28291b6c1e4e6f1172d6b49`。
