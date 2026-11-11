# 参考文献专项核对与遗漏工作检索

核对日期：2026年10月13日（Asia/Shanghai）。对象：v0.15.2 的全部22个书目条目，含未进入印刷文献表的 Qwen3；结果落实于 v0.15.3。

本轮补入5篇相关论文、1条直接工程诊断、1条独立审计来源，以及1篇经文件指纹确认的同项目早期报告。最终书目库30条，Qwen3仍为未引用的库条目；正文和补充分别生成实际引用列表。逐条元数据、版本、作者、日期、主源及检索限制见 `provenance/REFERENCE_AUDIT_V0153.json`。

## 已落实的主要修订

- LLM-42 改引 SOSP2026正式出版记录，补齐页码916–931及正式DOI；MLSys论文补页码1719–1741。
- PR91实验与PR94独立审计分开引用，补正SupplementS1源表。PR93审计及历史台账按可证实的GitHub账号YinnHuu署名，不推断该账号的真实姓名或论文作者身份。
- HumanEval和Qwen3补全最新主源的58/60人作者列表，印刷列表统一显示前6名后加et al.；MBPP/GSM8K/HumanEval/Qwen3明确版本。
- 网页、软件及伴随记录显示完整URL及实际访问日期。软件仍引实验使用的固定构建，不以最新软件替换实验版本。
- Vosti与同项目旧预印本的arXiv页面显示DOI待注册，但DataCite注册记录已是findable，标题作者匹配；保留DOI并记录差异。

## 22条既有文献逐项结论

| 键 | 主源 | 结论 |
|---|---|---|
| `leviathan2023` | [核对来源](https://proceedings.mlr.press/v202/leviathan23a.html) | ICML2023，PMLR202:19274–19286；保留正式版。 |
| `thinkingmachines` | [核对来源](https://thinkingmachines.ai/blog/defeating-nondeterminism-in-llm-inference/) | 官方Citation明确HoraceHe与ThinkingMachinesLab共同署名；保留。博客，不是同行评审论文。 |
| `mbpp` | [核对来源](https://arxiv.org/abs/2108.07732) | 作者/题名/2021年正确；最新v1，固定版本。 |
| `gsm8k` | [核对来源](https://arxiv.org/abs/2110.14168) | 作者/题名/2021年正确；最新v2，固定版本。 |
| `humaneval` | [核对来源](https://arxiv.org/abs/2107.03374) | 最新v2增加作者等信息；补全58名作者并固定版本。 |
| `qwen3` | [核对来源](https://arxiv.org/abs/2505.09388) | 最新v1；补全60名作者，未在正文或补充引用，不输出到印刷列表。 |
| `llm42` | [核对来源](https://arxiv.org/abs/2601.17768) | 更新为SOSP2026正式版，916–931，正式DOI。技术文字依据arXivv2；ACM全文403。 |
| `margingate` | [核对来源](https://arxiv.org/abs/2605.30218) | 最新v1，仍按预印本引用；未发现已核实的正式替代版。 |
| `vosti` | [核对来源](https://arxiv.org/abs/2609.38981) | 最新v1；DataCite已注册DOI。更具体承认chunking/query/cache等证明范围。 |
| `stagereplay` | [核对来源](https://arxiv.org/abs/2607.28495) | 最新v1；保留已有KV移植和共同后缀控制的归因。 |
| `illusion` | [核对来源](https://arxiv.org/abs/2601.11580) | 保留MLSys2026正式版，补1719–1741及publisher。 |
| `lossless` | [核对来源](https://arxiv.org/abs/2607.17283) | 最新v1，预印本；保持consumer-hardware语境。 |
| `aclheterospec` | [核对来源](https://arxiv.org/abs/2505.13254) | ACL2026正式版、页码/DOI正确；作者ZaneCao与最新正式版一致。 |
| `llamacpp` | [核对来源](https://github.com/ggml-org/llama.cpp) | b10839与官方tag相符；Vulkan上游谱系仍未认证，固定本地字节。 |
| `rtxconfirm` | [核对来源](https://github.com/leecdiang/HeteroSpec/blob/810407c9423cac925d38a976403e23c81bb1704b/benchmarks/rtx_evidence_closeout_v1/RESULTS.md) | 源仅支持PR91实验；将后来的PR94审计单列。 |
| `rtxrepair` | [核对来源](https://github.com/leecdiang/HeteroSpec/blob/3235d44c26edd92db33e574094c26af8e29d2452/benchmarks/rtx_querylayout_mechanism_v1/RESULTS.md) | PR98固定源、任务/session medians与21项比较仍成立。 |
| `bpartition` | [核对来源](https://github.com/leecdiang/HeteroSpec/blob/c0e16aff9f3eeb0e677a52fcdc092068c096bf5d/benchmarks/b570_prefill_partition_causality_v1/RESULTS.md) | PR99原始三臂/63请求来源保留；PR101作为后续扩展。 |
| `bfinal` | [核对来源](https://github.com/leecdiang/HeteroSpec/blob/26706c9fb4818ec3465e45acea029c4ab88a390f/benchmarks/b570_final_causal_closeout_v1/RESULTS.md) | PR101仍为同一head的Draft；不是已发表或已合并论文。 |
| `bcost` | [核对来源](https://github.com/leecdiang/HeteroSpec/blob/82946adf946491e6cf7fef761bcc1ec0772e914e/benchmarks/b570_evidence_closeout_v1/README.md) | PR92只支持原始stock gate及成本；不代替PR93/97后续证据。 |
| `bpostaudit` | [核对来源](https://github.com/leecdiang/HeteroSpec/blob/57da177c3b63a714d6e6b5e5d7a7dc1f1393e662/docs/experiments/b570_postaudit_20261012/AUDIT_SUMMARY.json) | PR93直接源支持240完整输出配对；账号署名改为YinnHuu。 |
| `bwork` | [核对来源](https://github.com/leecdiang/HeteroSpec/blob/5a66653bd0ce413d4eb9aef3a4501b93c138071b/benchmarks/b570_phasebinding_boundary_v1/RESULTS.md) | PR97直接源支持563物理验证周期及原始限制。 |
| `history` | [核对来源](https://github.com/leecdiang/HeteroSpec/blob/f5b7b8e9a6d02b228cb0e7b7b3932e89327cfb63/paper/jsa/manuscript_v0145/EXPERIMENT_DESTINATIONS.json) | 固定28组历史台账；文件引入者为YinnHuu，按账号归因。 |

## 补引与贡献边界

| 工作 | 加入位置 | 与本文关系 |
|---|---|---|
| [LayerCast](https://proceedings.neurips.cc/paper_files/paper/2025/hash/f80094a824ba5912d4a2de169c404a40-Abstract-Conference.html) | 正文7.1 | 已研究配置/精度敏感性并改用FP32计算；本文保持登记精度并改变局部图布局。 |
| [TBIK](https://proceedings.mlr.press/v306/zhang26ag.html) | 正文7.1 | 已统一GPU内外规约顺序；本文不主张跨张量并行规模的不变性。 |
| [Same Request, Different Answer](https://arxiv.org/abs/2609.04748v1) | 正文7.2 | 已有量化缓存状态分歧，且每条路径可各自复现；本文不把此现象列为首次发现。 |
| [Vulkan算子诊断](https://github.com/ggml-org/llama.cpp/issues/25618#issuecomment-5392171333) | 正文7.2 | frizikk的2026-08-24工程记录已有投影边界与局部修复限制；与同行评审论文区分。 |
| [The Illusion of Equivalence](https://arxiv.org/abs/2604.15409v1) | 补充S5.4 | 引用FP16/FP32下缓存与重计算的对照，不误称其已做双向KV移植。 |
| [Re-feeding Is Not Replaying](https://arxiv.org/abs/2606.15621v1) | 补充S5.4 | 引用留存decode-timeKV、重喂前缀及replica噪声对照，不误写成任意完整状态恢复。 |
| [同项目早期报告](https://arxiv.org/abs/2610.03228v1) | 补充S6 | 原始预测文件SHA256与公开附录J一致；历史证据关联，不算独立复现。 |

上述补充后，本文的具体增量仍限定为完整QB图布局/相位/复用设计、同参考修复成本比较，以及量化运行栈中实际分段、投影前沿和经过own-path sham准入的状态重建证据。无需为了回应这些引用再开展未经设计的大实验。

## 检索但未加入的条目

- Sequoia：硬件感知投机成本优化，与本文已承认的成本基础相符；当前句子由更直接的性能研究支持，保留于审计候选。
- ReproBLAS/TOMS：浮点可复现求和基础，与特定旧参考路径保持不同；记录背景关系，不扩展正文为通用数值计算综述。
- llama.cpp#28111：其他量化/硬件的批次敏感性工程观察，未与本文Q8_0样本混合。#16016仍Draft、#28108未合并，未当作已发布实现或保证。

## 适用范围

检索覆盖当前已有文献的正式页面、版本记录及相邻引文，辅以相关主题和官方项目记录；不保证不存在未索引、私有或刚发布的遗漏工作。未见更正/撤稿通知仅指访问过的主源。外部方法未复现，本文GPU实验及约675MB原始归档未重跑。JSA完整指南采用仓库保存的2026-10-09核实记录；2026-10-13实时页面仍无法访问，不能声称已排除之后的规则变动。
