# RTX PR91 独立 CPU 交叉审计

审计结论：**PASS**。没有发现本次核查范围内的原始记录、输出资格、工作量守恒或请求费用重算不一致。此结论是归档证据审计，不是独立硬件复现实验，也不是普遍无损性证明。

## 固定来源与复现

- 实验：[PR91](https://github.com/leecdiang/HeteroSpec/pull/91)，固定提交 `810407c9423cac925d38a976403e23c81bb1704b`。
- 审计脚本与五个合成检查的执行提交：`98d8c58de3f5071870570e631d8fb13a7d070bcd`。
- [成功的 CPU 审计运行](https://github.com/leecdiang/HeteroSpec/actions/runs/38239233290)，job `114777434702`。
- 输入完整 ZIP：114,451,224 bytes，SHA256 `6cef4902fb2983024b4eb0c4b9a8a6c97ffed770d18495141f94144e11bc7232`。
- Actions 结果 ZIP：artifact `11741971021`，SHA256 `7f783c34fe20a7ba98583397945d8c620377189d9181184b11b603d176b225d3`。
- [RTX_CROSSAUDIT.json](RTX_CROSSAUDIT.json) 是从该结果 ZIP 提取的完整文件，持久保留全部逐任务费用、会话结果、不一致位置和工作量分母。
- 审计代码：`scripts/audit/rtx_pr91_crossaudit.py`；检查：`scripts/audit/test_rtx_pr91_crossaudit.py`。仅 Python 标准库，使用只读仓库 token 下载固定 Git 对象；未导入或执行归档代码。

```bash
python3 -m unittest discover -s scripts/audit -p 'test_rtx_pr91_crossaudit.py'
python3 -B scripts/audit/rtx_pr91_crossaudit.py --output audit-output
```

第二条命令需要通过运行环境提供只读 `GH_TOKEN`。新增 GPU/模型前向为零，外部 GGUF 和 DLL 的实际字节未在审计环境重新取得或认证。

## 实际核查

1. 两个分片的大小、SHA256、Git blob SHA；拼接 ZIP 的大小和 SHA256；INDEX 中 21,794 个文件；嵌套 SOURCE_RUNTIME 中 6,890 个文件。关键公开记录和源码包还与固定提交的 Git blob 交叉绑定。
2. 冻结设计、输入、计划和模型摘要；150 个正式 block、3,600 个唯一槽；账本 3,600 次正式请求和 150 次预热；冻结读回在正式记录之前；累计 owned lifetime 为 10,541.8209658 秒，paid units 为 4,970。
3. 每条正规化记录与独立路径下的原生 RECORD 完整比对；REQUEST_STARTED 输入 IDs、cap128、温度0、seed123；COMPLETED 摘要；原生响应的完整 IDs、EOG flags、长度、terminal ID、stop reason、无截断和 prompt cache_n=0。
4. 每条 wall_ms 与原生请求起止纳秒重算一致；正式通道为 counts，未启用 phase timer、heavy、ETW 或 added sync。工作量与原生 hs_closeout 字段完全相符。
5. Proposal 五种去向、输出来源、接受前缀和周期进展直方图、draft proposal/catchup、caller 与物理 micrograph 行数/调用计数守恒。
6. 五臂全配对比较：每家族十对，共三十对；每任务每臂十次重复稳定性；完整输出比较覆盖后缀，不能用首分歧位置相同推断两个输出相同。原报告二十一项比较的聚合费用、会话费用和退化任务重算一致。

合成检查覆盖缺失/重复坐标、相同首分歧之后仍不同的后缀、错误 EOG/裁剪、输入或 observer 漂移及费用比方向。它们不计为实验样本。

## 完整输出与请求费用

R 为 UB1 参考目标路径；M0 为普通 UB4 目标路径；M3 为 mask3 修复后的匹配目标路径；C3 在匹配目标路径上加入 k=3 draft；R_prod 为先在工程题上冻结选择的普通部署 UB。三个家族共享修复 scope 与 k，没有根据本次确认结果逐家族重选。

**三个家族均有 R=M3=C3，逐家族 240/240 完整请求配对一致。** M3 与 C3 各自相对 R 合计 720/720 一致。样本结构是 24 个任务 × 3 个家族 × 2 个会话 × 5 轮；不能写成 720 个独立任务。所有五臂在各自任务的十次重复中稳定。

| 家族 | R/M3 | M3/C3 | MBPP M3/C3 | GSM8K M3/C3 | 两会话 M3/C3 | M3/C3 退化任务 |
|---|---:|---:|---:|---:|---|---:|
| Qwen | 1.383332 | 1.134924 | 1.100373 | 1.170560 | 1.141932 / 1.127959 | 0/24 |
| SmolLM2 | 1.444173 | 0.607389 | 0.626978 | 0.588411 | 0.605004 / 0.609783 | 24/24 |
| Llama | 1.501051 | 1.072227 | 1.036570 | 1.109111 | 1.060561 / 1.084022 | 4/24 |

比值为分子路径的完整请求时间 / 分母路径时间；大于1表示分母更快。每任务、每会话先取五轮中位数，再对两个会话和24个任务等权取几何平均。每域12题；本表没有跨日期置信区间，也不将重复次数当成独立任务数。

- M0 对 R 的完整输出不一致任务：Qwen 5/24，SmolLM2 14/24，Llama 9/24。
- R_prod 对 R：Qwen 0/24，SmolLM2 14/24，Llama 8/24。不一致不等于任务质量更差，但这些比较不支持参考输出保持的速度主张。
- Qwen 的 R_prod/C3=1.569566 合格。SmolLM2 和 Llama 的诊断比值分别为0.512333和0.842790，输出不匹配，保留在完整 JSON 中，不升级为无损部署比较。
- Llama 的 M3/C3 退化题：MBPP/418、MBPP/476、MBPP/79、MBPP/99。SmolLM2 的24题全部退化；Qwen无退化题。
- R/M3 的1.383–1.501倍同时包含 UB1→UB4 的 prefill/path 变化；不能全部归因于 attention 修复。M0 输出不一致，也不能把 M0/M3 费用相减当成隔离的修复开销。

## Acceptance、draft、target 与长度

以下为每个家族/域120次 C3 请求的合并总数之比，**不是逐任务比值的中位数**。Acceptance 分母是实际 verified proposals；rows 与 micrographs 的分母是完整输出 ID 数（含终止 EOG）。Draft rows 包含 proposal 和 catchup，排除另行记录的 draft prefill。Target graphs 为 continuation 物理 micrograph 数，排除 prefill；target verification rows 包含验证 seed 行。

| 家族/域 | Acceptance | Draft rows/output | 其中 proposal / catchup | Target graphs/output | Verify rows/output | Prompt / output 中位数 | CAP/120 |
|---|---:|---:|---|---:|---:|---|---:|
| Qwen/MBPP | 73.98% | 2.1485 | 0.9208 / 1.2277 | 0.3069 | 1.2277 | 47.5 / 34 | 0 |
| Qwen/GSM8K | 74.46% | 2.1429 | 0.9161 / 1.2267 | 0.3106 | 1.2235 | 85.5 / 128 | 110 |
| SmolLM2/MBPP | 75.87% | 2.0977 | 0.8980 / 1.1997 | 0.3017 | 1.1983 | 68.5 / 36 | 10 |
| SmolLM2/GSM8K | 63.36% | 2.3906 | 1.0234 / 1.3672 | 0.3438 | 1.3665 | 109 / 128 | 120 |
| Llama/MBPP | 81.90% | 2.0057 | 0.8583 / 1.1474 | 0.2891 | 1.1463 | 70.5 / 77 | 40 |
| Llama/GSM8K | 76.56% | 2.1029 | 0.8997 / 1.2031 | 0.3034 | 1.2018 | 106 / 128 | 120 |

1. RTX 的 M3 continuation 物理图约为0.97–0.99/output，而 C3 为0.29–0.34/output，确实减少了图执行次数。C3 的 target verification rows 仍为1.15–1.37/output；图调用变少不等于算术行数变少，也不是 GPU occupancy 证明。
2. Draft continuation 为2.01–2.39 rows/output。Catchup 约占这些行的57%；只数 P_all 会遗漏真实 draft 工作。这不证明 catchup 可全部消除，也不识别其 wall 占比。
3. SmolLM2 的 MBPP acceptance 高于 Qwen，draft 行数略少、target 图数也接近，但速度方向相反。因此 acceptance 加工作计数仍不足以定量解释跨家族费用；需要单位工作成本及重叠信息。SmolLM2 的 GSM8K acceptance 下降且工作增加，与更差费用方向一致，但这是描述性机制证据。
4. GSM8K 的输出几乎全部到 cap128，MBPP 的停止分布明显不同。域比较混合了长度、prompt 和内容，不能当成长度的随机干预，也不能直接据此部署域选择器。CAP 处输出相等不推断未生成的完整解答相等。

## 模型缺口和两平台联系

`MODEL_TIMING_UNAVAILABLE` 保持成立。已有72个 lite 请求只能提供 enqueue 与自然 sampling-ready 标记；未建立完成后的互斥阶段 wall 分解。当前证据没有有效的阶段系数、预测误差或验证过的 break-even 阈值，不能用正式确认费用回填拟合来声称预测验证。

B570 的独立审计见 [PR93](https://github.com/leecdiang/HeteroSpec/pull/93)，固定审计 head `57da177c3b63a714d6e6b5e5d7a7dc1f1393e662`。其 R_prod=M_match=C_k1 在240次完整配对上相同，M/C=0.727927，24/24题退化。B570 C_k1 的 continuation 物理宽度为1，target verification rows/output 为1.0442（MBPP）和1.0612（GSM8K），另有 draft 工作；高 acceptance 未换来 target 图数摊薄。该事实与 RTX 的图数摊薄形成机制对照。

两平台 k、量化、面板与实现不同，不能把差异归因于 GPU 品牌，也不能将它们合并成同一个算法的硬件 A/B。B570 的全配对结论是保留原 R_stock 资格结果之后的事后完整配对审计，没有追溯替换原参考。

当前轮可以完成证据收尾。是否额外进行针对性实验，应由要保留的创新主张决定；详见 [论文判断与下一步](PAPER_ASSESSMENT.md)。本 PR 不改论文、release、原实验数据，不发起新硬件实验。
