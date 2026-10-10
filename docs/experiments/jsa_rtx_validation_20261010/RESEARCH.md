# 第一手检索与方案决策

检索日期：2026-10-10。只用作者论文、官方实现、模型发布页和统计方法原始/权威来源。以下是方案判断，不是新的实测兼容性证明。

## 1. 研究问题决定平台范围

当前 `paper/jsa/manuscript_v0145/sections/03_methods.tex` 将 RTX 修复、B570 whole-recipe binding、M4 Guard、358H target-work 边界分别处理。需要补的约 3.5% matched request 增量属于 RTX；其他平台没有承担同一收益主张。应在产生该主张的固定 RTX 配置上复测，而不是扩大为四平台排名。

第二家族检验模型图路径，跨日期检验运行环境重复性，外部方法检验共同合同下的资格/成本。三者不能互相替代。新增第二后端可以进一步增强跨后端适用性，但本轮不将其作为 RTX 交付的前置条件。

## 2. 外部方法选择

| 第一手来源 | 检索所得与决策 |
|---|---|
| [LLM-42 v2](https://arxiv.org/html/2601.17768v2)，§4、§5；[官方实现](https://github.com/microsoft/llm-42) | 固定形状验证、回滚和 verifier KV 替换与本稿的状态/路径问题最接近；因此选作主外部方法。官方实现基于 SGLang，论文环境与当前 Q8_0 GGML RTX 不同。采用有映射说明的同栈移植，不混用论文速度数字。 |
| [Thinking Machines 原文](https://thinkingmachines.ai/blog/defeating-nondeterminism-in-llm-inference/)，[官方 batch_invariant_ops](https://github.com/thinking-machines-lab/batch_invariant_ops) | 算子批不变性是相关方法，但现成 PyTorch/Triton 算子不能直接当作当前 GGML Q8_0 的对照。将其列入兼容性说明；本轮不启动另一个 FP16/BF16 栈来制造“同合同”速度比较。 |
| [SGLang 确定性实现说明](https://www.lmsys.org/blog/2025-09-22-sglang-deterministic/) | 确定性依赖 GEMM、attention、采样与调度设置；一个开关或固定种子不能替代完整输出资格。只作为实现检查来源，不新增第三种运行栈。 |
| [MarginGate v1](https://arxiv.org/html/2605.30218v1)，§3 | 稀疏 margin 触发、局部 KV 修复依赖校准及 verifier 合同；不预设其状态假设适用于本稿 Q8_0 路径。本轮不增加阈值搜索；保留为相关工作及后续独立问题。 |
| [Vosti v1](https://arxiv.org/html/2609.38981v1)，§2、§4–6 | 区分系统/内核层的确定性，覆盖更多执行变化。其验证栈不是现有 RTX 前端的可替换模块；本轮不重写整个服务引擎，也不把 token 一致写成 logits 位一致或形式化证明。 |

**关键合同差异：**LLM-42 的 verifier 可以产生自己的规范输出；它的重复性不自动意味着等于本稿固定 ordinary UB1 参考。因此本轮不承诺外部方法必定通过该合同。输出先行，合格后才比较速度；不匹配时保留重复稳定性、完整偏差和诊断成本。若只有 adaptation 完成，稿件只能称“同栈、同合同的外部方法移植评估”，完整原系统对照的限制仍需保留。

不选择 n-gram/EAGLE/MTP 作为唯一外部对照：它们更换 proposal 机制，不能直接回答“参考保持修复”的相对成本；也不把旧 serialized speculation 改名为新的外部对照。

## 3. 第二家族的选择与尚待核验的事实

优先 pair 的来源：[Llama-3.1-8B-Instruct](https://huggingface.co/meta-llama/Llama-3.1-8B-Instruct)、[Llama-3.2-1B-Instruct](https://huggingface.co/meta-llama/Llama-3.2-1B-Instruct)。其模型系列、规模来自官方 model cards。当前会话未取得 gated config/tokenizer 文件，公开下载返回 401；因此**没有确认词表兼容或具体 GGUF 身份**。RTX 若已有授权资产可直接核验，不需要再次要求用户批准已授权工作；若需要作者尚未拥有的访问资格，记录资产阻塞。

输出前的预定备用为 [SmolLM2-1.7B-Instruct](https://huggingface.co/HuggingFaceTB/SmolLM2-1.7B-Instruct) / [SmolLM2-135M-Instruct](https://huggingface.co/HuggingFaceTB/SmolLM2-135M-Instruct)。本次成功读取官方 config/tokenizer_config：两者 `model_type=llama`、`vocab_size=49152`，tokenizer_class 均 GPT2Tokenizer；这仅支持候选筛选，不能替代完整 token-to-ID、special tokens、GGUF 与 runtime 检查。

随后按官方repo固定revision读取完整tokenizer.json，确认model词表/merges、added_tokens、normalizer、pre_tokenizer、post_processor、decoder六组件均相同。目标revision为`31b70e2e869a7173562077fd711b654946d38674`，draft为`12fd25f77366fa6b3b4b768ec3050bf629380bac`；三份官方元数据文件的URL/bytes/SHA见SOURCE_BINDINGS。这增强了备用pair的静态依据，仍未验证转换后GGUF或绑定RTX前端；新转换应使用这些revision。

绑定 [llama.cpp 源码](https://github.com/ggml-org/llama.cpp/blob/0cae43063cf15170e91a2ff4d034da0ecef4a1b2/common/speculative.cpp) 的 `common_speculative_are_compatible` 检查词表类型、特殊 token 设置等；相同 vocab_size 不是兼容性证明。RTX 必须同时记录官方检查结果及额外的实际 token 映射检查。不得修改 token ID、关闭检查或沿用 Qwen EOG 常量来强行通过。

两个候选均改变现有 Qwen3 图路径。备用规模不同，成本只在各模型内比较，不将两家族速度相互排名。家族确认结果可能是迁移成功、需要新 recipe、原生无偏差或工程不支持；无偏差不等于复现了修复机制。

## 4. 会话设计及统计决策

[Kalibera 与 Jones 的原始方法记录](https://kar.kent.ac.uk/33611/)讨论不同层次的基准重复与不确定性；本轮据此保留 request、round、session、day 四层，不能把所有请求当独立会话。六日期/十二会话是本方案的固定有限预算，**不是来源要求，也不是事前功效保证**。

主分析对每日期的平均 log speed ratio 使用 [NIST 均值 t 区间](https://www.itl.nist.gov/div898/handbook/eda/section3/eda352.htm)再指数变换；day 是最高聚合单位，df=5。其有效性依赖日期间近似独立、day log effect 分布的近似条件。报告六个原始 day effects、leave-one-day-out 和日期趋势，不用少量 cluster 的 bootstrap 窄区间掩盖这些假设。该区间针对固定任务面板及观察到的环境重复，不是未知任务、平台或未来部署的保证。

预定收益判定见 PROTOCOL.md。区间跨 1 时结论为未能确认稳定正增量，不能持续加会话直到显著。结果的解释优先级是完整输出资格、执行完整性、效果及波动，而不是阳性结果。
