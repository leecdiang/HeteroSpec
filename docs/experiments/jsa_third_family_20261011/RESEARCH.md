# 选择模型与设计的依据

检索及静态检查日期：2026-10-11。模型元数据、公开转换文件前缀和已有结果均只读；没有加载模型做推理。全文区分已观察结果、静态事实与待验证解释。

## 已有结果告诉我们什么

[RTX PR #80](https://github.com/leecdiang/HeteroSpec/pull/80) 固定在 `92aeebe9bb422a754b1457e9e3572e7a57dd1d31`：Qwen 新确认集的普通 R/C3 为 1.642286，matched M3/C3 为 1.074120；同日独立 S 组 matched GM 1.057687。Smol 固定 C3 的 168 个实际完整原生输出都匹配 R，但整体冻结矩阵存在操作缺失，因此原正式 qualified speedup 仍为 null。

仅作已观察 CSV 的描述性分解，Smol 的 R/M3=1.524613、M3/C3=0.647699、R/C3=0.987490。这三个数不能升级成原研究的正式合格收益。在相同任务与聚合规则下，`R/C = (R/M) * (M/C)`：目标路径的改善可能被草稿及验证的额外成本抵消。这是值得新实验检验的解释，尚不是已证明的因果归因。

[B570 PR #82](https://github.com/leecdiang/HeteroSpec/pull/82) 固定在 `7e82fa0b8fc2c9d56e04512c47a0986171534b25`：Smol 的预定 endpoint 条件合格，R/C=0.546139，候选成本约 1.831 倍普通参考；原生 suffix 不完全匹配。N 已匹配 endpoint，不能宣称该家族在 B570 上证明了修复必要性。CUDA 完整数组与 Vulkan endpoint 合同分别报告。

这些结果约束下一轮的主张：保持 reference、目标路径优化、草稿带来的增量，是三个不同的问题。新增家族的正结果不会消除 Smol 反例。

## 为什么首选 Llama 8B/1B

[Meta 的 Llama 3.1 模型卡](https://huggingface.co/meta-llama/Llama-3.1-8B-Instruct) 和 [Llama 3.2 模型卡](https://huggingface.co/meta-llama/Llama-3.2-1B-Instruct) 提供模型家族背景。本机未获官方受限文件访问；本设计实际绑定的是公开发布者 [8B Q8_0 转换](https://huggingface.co/bartowski/Meta-Llama-3.1-8B-Instruct-GGUF/tree/bf5b95e96dac0462e2a09145ec66cae9a3f12067) 与 [1B Q8_0 转换](https://huggingface.co/bartowski/Llama-3.2-1B-Instruct-GGUF/tree/067b946cf014b7c697f3654f621d577a3e3afd1c)。模型身份的实测范围限于这些文件，不能冒称自行从已核验的官方原始权重转换。

实际 GGUF 元数据给出：目标 32 层、head_dim128，草稿 16 层、head_dim64，均为 dense Llama/GQA、8 个 KV heads。全部 tokenizer.ggml 组件相同；两个聊天模板不同，必须由目标模板生成一次 prompt IDs，再给同一 pair 的目标和草稿使用同一 IDs。不能分别套模板后假装相同前缀。发布者 SHA256 尚需执行端对完整下载文件独立核验。

目标 8B 接近已有 Qwen 8B，减少“只比较一个 8B 目标与一个 1.7B 目标”的规模差异。Smol 官方固定配置显示[目标 24 层](https://huggingface.co/HuggingFaceTB/SmolLM2-1.7B-Instruct/blob/31b70e2e869a7173562077fd711b654946d38674/config.json)、[135M 草稿 30 层](https://huggingface.co/HuggingFaceTB/SmolLM2-135M-Instruct/blob/12fd25f77366fa6b3b4b768ec3050bf629380bac/config.json)；Llama 1B 虽参数更多但只有 16 层。故参数量比不能作为草稿成本比的替代。词表、深度、架构、接受率和硬件都会影响成本；这一选择有可检验的理由，但不承诺正收益。

原 RTX PR #80 已有独立 dense Llama query-axis 分支，保留 role/phase 与 graph reuse key、未改变发布 CUDA 数值库。这降低移植成本。Smol 上运行过该分支，不等于 Llama 的不同 head_dim、层数、RoPE 或新 ctx 已被验证；仍须真实形状、作用域、capture 开关和原生输出资格检查。

## 其他家族为何暂不进入同轮

| 候选 | 静态检查 | 选择 |
|---|---|---|
| IBM Granite 3.3 8B/2B | 官方 tokenizer 完整组件相同，vocab49,159；独立 granite 架构，具有 embedding/attention/residual/logit scaling | 有价值的后续架构迁移对象；本轮不临时加新图移植 |
| Phi-3 small/mini | 官方 vocab 分别 100,352 与 32,064，model_type 也不同 | 不适合现有直接同 token-ID 草稿验证；不得关闭兼容性 guard |
| Gemma 3 4B/1B | 官方文件本机 HTTP401，现有绑定不足；不能假定现有 dense Llama patch 覆盖其架构 | 不进入本轮；没有静态失败就宣称其不支持 |

Granite 来源：[官方 8B](https://huggingface.co/ibm-granite/granite-3.3-8b-instruct/tree/51dd4bc2ade4059a6bd87649d68aa11e4fb2529b)、[官方 2B](https://huggingface.co/ibm-granite/granite-3.3-2b-instruct/tree/707f574c62054322f6b5b04b6d075f0a8f05e0f0)、[固定 upstream 的 Granite 图](https://github.com/ggml-org/llama.cpp/blob/0cae43063cf15170e91a2ff4d034da0ecef4a1b2/src/models/granite.cpp)。Phi 来源：[mini 配置](https://huggingface.co/microsoft/Phi-3-mini-4k-instruct/blob/f39ac1d28e925b323eae81227eaba4464caced4e/config.json)、[small 配置](https://huggingface.co/microsoft/Phi-3-small-8k-instruct/blob/188b876e997ee4055df01afe46274c14c400fe40/config.json)。

## 文献如何影响方案

[Fast Inference from Transformers via Speculative Decoding](https://arxiv.org/abs/2211.17192) 分析接受概率、草稿相对成本和草稿长度的关系；[Decoding Speculative Decoding](https://aclanthology.org/2025.naacl-long.328/) 实测强调草稿延迟，语言建模能力不能直接代替推测性能。本研究据此预先限定 k=1/2/3，测量实际 proposal/accept/verify 工作，避免固定一个 k 后把慢归因于家族，也避免在确认集上无限调参。

本轮**不**提出新在线控制器，不训练 drafter，不引入异词表 SD 或另一推理引擎。目标是区分固定 recipe 的迁移、预定 k 敏感性和硬件费用边界。

## 能支持的论文表述

- 新家族 C 完整匹配 R：有限配置/输入上的 reference-preserving transfer；不能说所有输入、所有 logits 或功能正确性均获证明。
- N 不匹配而 C 匹配：该 panel 上存在修复必要性与成功修复；没有 state cross 时不推出唯一算子因果结论。
- R/C 正而 M/C 不正：目标路径收益转移，不能宣称草稿增量普适。
- Llama 与 Qwen 固定 recipe 均通过资格及跨日费用规则：可增加这两个家族、该硬件与合同下的跨家族收益证据。Smol 反例仍在主表。
- 只有某个次要 k 正：这是预定配置敏感性结果，不能把它改称固定 k3 的成功；按协议对 k1/2 次检验使用保守区间。
- 三家族只覆盖 dense decoder 的相关实现路径；不能扩展为 MoE、滑窗、混合架构或全部四个平台的通用定理。
