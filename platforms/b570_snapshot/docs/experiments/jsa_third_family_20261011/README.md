# 跨模型家族验证：Llama 新家族与三家族共同对照

**设计稿；没有新增模型 forward，也没有新增实验结果。** 主执行平台为 RTX/CUDA。该研究独立于 PR #80/#82，不改写它们的资格规则或负面结果。

新增对象固定为 Llama-3.1-8B-Instruct / Llama-3.2-1B-Instruct Q8_0；在同一批新输入上同时保留 Qwen3-8B/0.6B 和 SmolLM2-1.7B/135M。核心问题是：固定 target-phase mask3 能否保持各模型自己的 ordinary 输出，以及普通请求收益与纯推测增量分别能否迁移。

| 项目 | 冻结设计 |
|---|---|
| 模型 | 三个训练家族；Llama 是新增对象；各 pair 的实际转换文件分别绑定 |
| 输入 | 12 个历史审计后保留的 MBPP 输入 + 12 个 GSM8K 问题；三家族共用原始用户输入 |
| 条件 | R、N、M3、C3_K3、C3_K1、C3_K2；后三者都使用 mask3，名称中的 K 是草稿长度 |
| 固定主检验 | Llama 的 M3/C3_K3；普通参考 R/C3_K3 同时报告 |
| 次检验 | Qwen/Smol 固定配置；k=1、2 的预定敏感性检验；不从确认集选择赢家 |
| 独立复测 | 六个不同日期，每家族每天一个独立会话、四轮，日期是主统计单位 |
| 请求预算 | 正式 10,368；warmup 432；工程最多 640；合计最多 11,440，另设 12,000 硬停止线 |
| 时间预算 | 所有自有 GPU 进程生命周期最多 32 小时，14 个日历日内结束 |

已对两个公开 Llama GGUF 的固定 revision 进行零 forward 元数据读取：128,256 个 token、全部 token ID 对应文本、类型、merges、BOS/EOS、pre-tokenizer 标签相等；**聊天模板不同**。这允许进入主机预检，不等于 runtime 资格、数值一致性、完整文件哈希验证或加速证据。Meta 官方文件本机访问仍为 HTTP 401；公开转换的官方原始权重 revision 血缘未获认证。这些边界保留在 [ASSETS.json](ASSETS.json) 和 [STATIC_PREFLIGHT.json](STATIC_PREFLIGHT.json)。

阅读顺序：[研究依据](RESEARCH.md) → [执行协议](PROTOCOL.md) → [机器设计](DESIGN.json) → [RTX 执行提示词](EXECUTION_PROMPT.md)。[来源绑定](SOURCE_BINDINGS.json) 与 [静态核验](VALIDATION.json) 用于读取核对。

若输出保持和性能都成功，可以增加“在所测 Qwen/Llama 配置和输入上跨家族迁移”的证据。若只输出保持成功，只扩展输出合同的适用范围。Smol 的慢、所有分歧、操作缺失和不确定区间都保留；有限模型和输入不能证明所有模型均加速。
