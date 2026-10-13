# JSA 投稿前 RTX 补强方案

日期：2026-10-10。研究标识：`JSA_RTX_VALIDATION_V1`。本文档是执行设计，**没有新增模型实验结果**。

方案确认：本轮只在 RTX 上执行，分别补充独立日期/会话复测、第二模型家族和外部方法的同合同评估。B570、M4、358H 不扩展。四个平台的全组合不是当前有界主张的必要条件，也不是 JSA 的固定要求。

将本 PR 的准确 URL 和完整 head SHA 交给 RTX 执行端，并让它首先阅读 [EXECUTION_PROMPT.md](EXECUTION_PROMPT.md)。执行端负责工程实现、资产核验、冻结、实际运行、独立复核和结果 PR；本 PR 不包含可直接启动 CUDA 的新 runner。

| 文件 | 用途 |
|---|---|
| [RESEARCH.md](RESEARCH.md) | 第一手检索、方法选择及不能忽略的合同差异 |
| [PROTOCOL.md](PROTOCOL.md) | 工作负载、条件、冻结、计时、统计和停止规则 |
| [EXECUTION_PROMPT.md](EXECUTION_PROMPT.md) | 给 RTX 执行端的完整任务与授权范围 |
| [DESIGN.json](DESIGN.json) | 与协议对应的机器可读设计；主机字段待执行端解析 |
| [SOURCE_BINDINGS.json](SOURCE_BINDINGS.json) | 当前仓库入口的完整文件身份及外部来源 |
| [VALIDATION.json](VALIDATION.json) | 设计的CPU核验范围、计数和结果 |

优先复测现有 Qwen 配置：原 24 个 MBPP 任务、四条件、四轮，在六个预定日期各执行两个独立会话，共 4,608 次正式请求。旧面板明确是 exposed，检验固定工作负载的跨会话稳定性，不冒称新的泛化样本。

第二家族优先选择 Llama-3.1-8B-Instruct / Llama-3.2-1B-Instruct，均 Q8_0；若在任何第二家族 forward 前不能满足资产访问、词表或内存检查，使用预定备用 SmolLM2-1.7B-Instruct / SmolLM2-135M-Instruct Q8_0。两对都需要实机资格，尚未确认与绑定 RTX 前端兼容。选择只允许依据输出前的工程条件，不允许根据是否出现偏差或速度换家族。

外部主对照选择 LLM-42 的 decode–verify–rollback 方法，在当前 GGML/CUDA 栈实现并标记为 **`LLM42_DVR_GGML_W32` adaptation**。先检验完整输出是否等于各自 ordinary target-only 参考。稳定但不等于该参考是合同不匹配，不代表原论文的确定性主张错误。移植结果不能写成对原 SGLang/H100 系统的直接复现或性能排名。

三项研究独立交付。家族无法支持、外部实现未完成、参考不匹配、微小收益不能稳定复现，都必须明确记录；不得用另一项成功宣称三个缺口均已解决。
