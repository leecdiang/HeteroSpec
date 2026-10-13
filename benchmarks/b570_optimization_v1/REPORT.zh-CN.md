# B570 PR85 后续研究：平台门槛停止

本轮状态为 `BOUNDARY_STOP_ZERO_FORWARD`。按 PR85 exact head `840ef5fef96068e0e40eee434d89d07bbad6a592` 在真实 B570 主机完成固定资产、SDK、旧证据恢复和同进程加载核验；两个家族均没有达到协议要求的512MiB dedicated headroom，因此没有准入生成、候选性能探索或新题确认。

| 家族／配置 | 实测加载余量 | 决定 |
|---|---:|---|
| Qwen Q8 target / Q8 draft，UB128四输出 | 301.41MiB | 不准入 |
| Qwen Q8 target / Q4 draft，UB32单输出，最接近门槛的观测 | 503.47MiB | 不准入；要求512MiB |
| Llama Q8 target / Q4 draft，UB32单输出 | 209.27MiB | 不准入 |
| Llama Q8 target / Q8 draft，日志修复后的独立加载记录 | draft weights阶段预算减usage为−218,660,902 bytes | 预算超额，尚未创建draft context即停止 |

完整8次Qwen和3次Llama加载、每个时间点的heap预算/usage、原始日志及失败版本均保留。其中Llama Q8的一次追加加载只修复异常数值未写出的日志问题，不是生成实验重试；原先缺数值的异常记录仍保留。加载尝试另按工程预算保守收费：Qwen8/640、Llama3/640；生成请求、warmup、正式请求及辅助decode均为0。

显存查询在拥有模型的worker PID内执行，绑定实际Intel Arc B570／PCI8086:E20C／Vulkan物理设备，只计算device-local heap。系统heap不加到余量中。实际日志独立核验完整layer offload及Vulkan KV；加载余量不代表工程峰值或无spill证明。此次显卡驱动32.0.101.9034、B570显示路由2560×1440；未更改主机配置。

六个固定GGUF文件均完整哈希核验；Qwen全151,936词表、Llama全128,256词表与两种草稿的token bytes/type/score、BOS/EOS及EOG标记一致。SDK接入模板实际编译，数值DLL与重新恢复的#82原始bytes一致；307份恢复源码及15个固定Git blob核验通过，不编造b10839 upstream commit。

独立CPU核验通过561,324项检查，主要为完整词表逐项比较，同时复算显存预算、时间记账、核验6个完整模型SHA，并拒绝7个显存／来源错误样例。原设计的19项CPU防错测试通过。这些检查不表示运行了token生成或性能试验。

没有选出R_prod或C，没有发布任何qualified speedup。raw cap/EOG提交、capture/reset、batched verify/rollback支持与工程峰值均为NOT_TESTED；没有新确认题、F0B或日期CI。F0A需要先于新token forward，本轮没有任何token forward。原始asset pin中的pending/false字段保留其设计时含义，实际资产与词表核验由独立执行收据证明。

初次时长汇总误将无时间戳FINAL标记回退到开始时间，旧汇总和CPU源码保留。已改用最后一条实际带时间的卸载／异常记录，并增加独立复算检查；预算一直按整个串行研究elapsed wall保守取上界。没有修改原始显存数据或停止决定。

新可恢复包包含全部负加载数据、词表、实际执行二进制版本／数值DLL、源码、原始Git blob和预算账本。六个完整模型与已核验#82历史CAS仍是外部hash-bound依赖。交付恢复／远端回读收据单列；旧#82/#84、论文和历史实验数据均保留，结果PR保持Draft。
