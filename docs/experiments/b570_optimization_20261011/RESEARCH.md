# 从已知成本推导优化方向

B570 #82 的 SmolLM2 target 很小；草稿、验证、同步与路径差异的开销超过省掉的普通 decode。新方案优先探索更大的 Qwen target，而不是继续证明这个已知慢配置。RTX Qwen 第一会话提供有限支持：C 比相同目标路径 M 快约 10%，但 R/C 的约 56% 包含 R 到 M 的路径差异，且 RTX ordinary UB1 与 B570 #82 ordinary UB128 不同。因此新 B570 研究同时报告 stock ordinary、最快合格 ordinary 和 matched target-only。

草稿 Q4_K_M 可减少草稿权重和带宽需求，可能改善接受率与草稿成本的平衡，也可能变差。目标权重及目标采样保持固定，必须用实际 native 词表、EOG 标志和提交输出核验。不同家族各自独立选择，不合并成普适结论。

Vulkan 优化须通过本机实际实现验证：批量验证的 query shape、KV 写入和 rollback、图复用与同步次数。在 bounded engineering 中可以修复 UB1 串行验证、每 token 同步或 tracing 的开销。不得把 CUDA patch 的支持推断到 Vulkan；未支持的模式标为 UNSUPPORTED，保留诊断和预算消耗。

## 显存测量必须属于模型进程

[`VK_EXT_memory_budget` 官方定义](https://docs.vulkan.org/refpages/latest/refpages/source/VkPhysicalDeviceMemoryBudgetPropertiesEXT.html)中，heapUsage 是**当前进程**的分配估计，heapBudget 是该进程可用预算的指导值。独立运行 vulkaninfo 或另一个探针后，用它的 usage 推断模型进程剩余显存是错误的。模型加载与工程运行时，必须在拥有模型的 worker PID 内查询，并绑定 PID、时间、物理设备、source/binary hashes、日志及 native allocator 峰值。提供的 native header 是待 B570 编译验证的接入模板，不是已有加载证明。

仅统计 B570 的 dedicated device-local heap；共享系统内存、WMI AdapterRAM 和另一块核显的预算不算 B570 余量。要求实际所有 target/draft 层与 KV 全 GPU，至少 512 MiB dedicated headroom，工程峰值持续符合该门槛。静态 file+KV+reserve 超额可阻止保守路径，但不能被写成已观察到的 OOM；通过实际测量才可修订其假设。

## 当前证据的边界

旧 B570 使用 driver 32.0.101.9034；本轮记录实际 driver 并冻结，不能假定未更新。旧温度/频率读数不可用，新轮如仍不可用照实标记。独显直连关闭不会改变协议的输出契约，但设备路由与背景显示占用必须记录。

旧 b10839 源码来自发布目录，未认证为某 upstream Git commit。恢复 #82 的完整私有源码、build manifests、数值 DLL 与 actual Git-hosted CAS 并逐项 hash 核验；不要凭版本名编造 commit。新 native 前端改动与任何数值 backend 改动都逐版本保留、重做等价门槛，并在 F0B 固定。无需升级整个 backend 来追逐最新版本。

两会话支持预声明配置在本轮题集上的描述性收益；日期 CI、跨日期稳健性和所有模型通用加速保持 null/UNTESTED。后续独立研究可以加强这些结论，不替代本轮负结果。
