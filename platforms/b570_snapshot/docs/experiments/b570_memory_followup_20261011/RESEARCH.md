# 事实、推断与范围

## #86 实际测到什么

以下来自 #86 固定 head `9f5e566e4fa843b7a47690552bfaa7f5ebaa8912` 的实际模型进程日志；[SOURCE_BINDINGS.json](SOURCE_BINDINGS.json) 绑定原始路径、SHA256 与源码。本目录复制的三份历史stdout逐byte保留，包括Windows CRLF；专用.gitattributes防止checkout换行转换。选取 LOADED 样本，不能取模型卸载后的 UNLOADED 样本。

| 配置（目标 / 草稿） | 实际采样点 | signed budget−usage | MiB | 含义 |
|---|---|---:|---:|---|
| Qwen 8B Q8 / 0.6B Q4，UB32，输出容量1 | LOADED | 527,925,248 | 503.46875 | 比原512门槛少8.53125 MiB |
| Llama 8B Q8 / 1B Q4，UB32，输出容量1 | LOADED | 219,439,104 | 209.2734375 | 可提出128门槛的新预检；尚未执行生成 |
| Llama 8B Q8 / 1B Q8，UB32 | DRAFT_WEIGHTS | −218,660,902 | −208.5312862 | 预算已超出；未达到双模型完整加载 |

#86 的全部过程没有 token forward，不构成输出错误、推测加速失败或所有 Llama 配置均不可运行的证据。Q8/Q8 的负预算也不等于一次已观测的生成 OOM；它说明仅降低正余量门槛不能使该加载记录满足预算条件。

加载器把 536870912 写在 MEMORY 判定、FINAL 状态和退出码中。单改 JSON、删检查或把旧日志的 false 改 true 均无效。新 worker、probe、controller、分析器要显式绑定同一 profile 阈值；保留底层真实分配失败和负预算保护。旧源码未执行生成，不能作为新推理驱动已通过的证明。

## 为什么不把209 MiB当作可用推理空间

[Vulkan 官方预算结构说明](https://docs.vulkan.org/refpages/latest/refpages/source/VkPhysicalDeviceMemoryBudgetPropertiesEXT.html) 把 heapBudget 定义为分配前的指导值，可能随其他程序活动变化；heapUsage 是当前进程分配的估计。[Windows 的应用显存预算说明](https://learn.microsoft.com/en-us/windows/win32/api/dxgi1_4/ns-dxgi1_4-dxgi_query_video_memory_info) 说明应用超过预算会有性能代价。总物理大小、广告10GB、另一个进程的usage、17GB系统heap均不能替代模型进程的 dedicated budget−usage。

生成还需要真实图、临时工作区、提交/回滚及验证输出缓冲。旧最佳样本 target `n_outputs_max=1`，并不证明 batched k=3 验证可分配4个输出。顺序单 token 路径是否只需1个输出，也要审核实际实现；不能用容量1的加载记录为容量4的路径背书。新预检必须使用各模式实际完整上下文和缓冲，再运行边界与最长输入工程题。

[WDDM GPU 虚拟内存文档](https://learn.microsoft.com/en-us/windows-hardware/drivers/display/gpu-virtual-memory-in-wddm-2-0) 说明 GPU 虚拟地址和物理驻留不是同一事实。全 GPU layer 日志、device-local heap 标志和正预算都不能单独证明没有系统内存驻留或迁移。须另报 native 分配映射和可获得的进程 local/nonlocal/paging 证据；不可观察时标 UNKNOWN，并限制结论范围。

## Q6主路线的证据强度

固定发布者版本的 [Q6_K 文件](https://huggingface.co/bartowski/Meta-Llama-3.1-8B-Instruct-GGUF/blob/bf5b95e96dac0462e2a09145ec66cae9a3f12067/Meta-Llama-3.1-8B-Instruct-Q6_K.gguf) 为6,596,011,424 bytes。实际读取8MiB前缀，完整解析7,823,572 bytes的GGUF元数据；tokenizer组件和chat template与已固定的8B Q8目标一致，见 [Q6_STATIC_PREFLIGHT.json](Q6_STATIC_PREFLIGHT.json)。这里没有加载模型，也没有核验6.6GB完整文件；发布者的LFS SHA必须在B570下载后独立复算。

量化文件仍声明相同的Llama架构、32层、4096隐藏维度、8个KV头和128256词表，但这不证明与原始Meta权重的完整数值谱系。保留 publisher-GGUF 来源层级，原始checkpoint转换 provenance 为 NOT_CERTIFIED。运行时还要复核完整词表字节/类型、所有EOG标志及原生compatibility guard。

Q6对普通输出的影响被同文件的普通参考吸收；这种实验检验的是相对该部署参考的保持能力和实际成本。Q6结果与RTX Q8、B570 Q8分开列出，不聚合为一个跨精度速度值。128门槛的Q8补充若成功，只支持该紧预算配置；Q6成功也不能宣称512门槛可以全面取消。
