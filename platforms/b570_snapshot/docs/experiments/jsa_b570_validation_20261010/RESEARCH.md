# 来源、判断与范围

设计依据是 B570 原协议/公开源码、独立 CPU 原始证据复核，以及 RTX 新执行端发布的**静态模型、暴露审计与输入预留元数据**。未读取 RTX 新性能或科学结果来选择 B570 方法。来源身份见 [SOURCE_BINDINGS.json](SOURCE_BINDINGS.json) 和 [COORDINATION_SNAPSHOT.json](COORDINATION_SNAPSHOT.json)。

## 已有 B570 证据

- [原协议](../../../benchmarks/b570_mechanism_pilot_v1/PROTOCOL.json)：Vulkan，ctx1024/batch512/threads10，FA off，greedy seed123，cap128。
- [固定候选](../../../benchmarks/b570_mechanism_pilot_v1/CANDIDATE_DECISION.json) 与 [E 原矩阵](../../../benchmarks/b570_mechanism_pilot_v1/E_MANIFEST.json)：ordinary prompt construction、保留同一 context/live sampler 的原位 UB128→UB1 phase binding，既有 k2/draftUB1。普通 R 为 UB128，matched target 为 UB1；M 不是 R。
- [CPU 复核](../../../benchmarks/b570_pr64_cpu_closeout_v2/REPORT.zh-CN.md) 和 [论文交接](../../../benchmarks/b570_pr64_cpu_closeout_v2/PAPER_HANDOFF.md)：E119/120；候选/R 整请求比 0.20128959，所有已配对 R 轮次均慢。端点恢复不等于全部 raw 数组相等。旧路线停止追加 GPU 投入；新家族迁移不能被解释成旧结果的重新胜出。
- [恢复协议](../../../benchmarks/b570_mechanism_pilot_v1/RESTORE.md)：CAS 含私有 phase-binding DLL、候选/状态程序与源码历史；模型和原运行库为外部哈希绑定依赖。b10839 是源码分发包，不可凭空赋予它 Git commit。恢复旧证据不授权重跑旧请求；本方案仅授权新独立研究。

## 第二家族与资产选择

[RTX 执行 PR80](https://github.com/leecdiang/HeteroSpec/pull/80) 的固定头 `3deff21dfbcba927f05828bd2f9fd4570e2e3e4c` 已用预定工程备选选中 SmolLM2，原因是 Llama 正式资产访问受限，选择记录为 STATIC_QUALIFIED_NO_FORWARD。本方案据此锁定同一模型对和 GGUF 字节，不根据 RTX 好坏改选。模型族从 Qwen3 扩展为 SmolLM2；这不自动证明任意架构、量化或模型可迁移。

官方 [1.7B config](https://huggingface.co/HuggingFaceTB/SmolLM2-1.7B-Instruct/blob/31b70e2e869a7173562077fd711b654946d38674/config.json) 和 [135M config](https://huggingface.co/HuggingFaceTB/SmolLM2-135M-Instruct/blob/12fd25f77366fa6b3b4b768ec3050bf629380bac/config.json) 将实现标为 LlamaForCausalLM。已核对官方 tokenizer 完整映射/合并及 special-token 配置；RTX 静态收据还绑定 actual GGUF 49152 词表和 EOG/BOS/EOS 标记。B570 必须独立重验 actual GGUF 和 native compatibility；CUDA 构建成功不证明 Vulkan 正确运行。

GGUF 来自快照固定的 bartowski 与 lmstudio-community 发布者。可证的是文件哈希和转换发布版本；发布者没有认证对应的官方原始权重 revision，因此不称“从指定官方 checkpoint 重新转换”。actual vocab、层数、KV 形状动态读取，不能沿用 Qwen 的 151936、37/37、29/29、EOG 或 prompt IDs。

## 外部方法的范围

[LLM-42 官方实现](https://github.com/microsoft/llm-42) 使用其 SGLang/CUDA 系统。B570 的原数值合同是 GGML/Vulkan；另行实现 Vulkan 批不变算子会增加新工程与数值合同，不能称为原系统的同合同复现。本轮只有 R/N/M/C。外部方法适配由 [RTX 设计 PR79](https://github.com/leecdiang/HeteroSpec/pull/79) 的执行分支承担，其资格仍须实际验证。

## 为什么可以并行

模型字节与合同在输出前冻结即可独立执行，无需 RTX 完成结果。两端采用独立确认任务：B570 的暂定 24 个预留 ID 与 RTX 当前已预留 24 ID 无交集。B570 仍需审计自己的执行历史、CAS 和开放 PR。这里的“项目未用”只指可访问证据下未执行/未观测，绝不指训练未见；不可访问主机的范围明确保留为未知。

逐字移植 RTX 输出后选出的新候选，需要等待该候选冻结并另定协议；当前固定 B570 候选验证不依赖此步骤。四轮新进程只是有限独立会话复核，不产生独立日期样本；报告整请求付费和各轮方向，不能据此宣称小幅生产收益稳健。
