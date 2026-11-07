# 给 RTX 平台的完整任务

在新的独立目录执行 `JSA_THIRD_FAMILY_V1`，阅读本目录 README、RESEARCH、PROTOCOL、DESIGN、ASSETS、STATIC_PREFLIGHT、SOURCE_BINDINGS，并解析你实际读取的 PR/head。不得覆盖 PR #80 或将它的 Smol INCOMPLETE 改判。该提示词在用户将本 PR 指派给 RTX 时授权按协议完成研究；本地设计 PR 本身没有启动远程 GPU，也没有发送其他聊天消息。

先恢复并核验 PR #80 最终 F native core、dense Llama patch 和发布数值DLL；完整私有源码/程序来自其author archive，Git CPU包不等于独立GPU重建包。三pair固定，Llama新pair必须使用ASSETS绑定的两个公开Q8_0文件，完整下载bytes/SHA256及实际runtime词表再检查。官方401和转换原始权重血缘不明照实写，不伪造官方tokenizer或授权状态，不关闭原生compatibility guard。

固定ctx1024、F16KV、FAoff、单seq、全GPU及三家族各自target模板/EOG/suppression。Llama两个模板不同，只用目标模板生成一次同pair共享IDs。先做零forward资产/内存预检、历史曝光审核、12MBPP+12GSM8K名单及六日期窗口冻结F0A，commit/push并独立读取远端确认后才能进行任何本轮forward。

按PROTOCOL在旧exposed/synthetic上完成六条件的有限工程：R,N,M3,C3_K3,C3_K1,C3_K2；K表示最大草稿长度，三C均mask3。不跑mask1、不换家族/量化/UB，不在新panel预试。完整检查scope/reuse/head_dim/capture/reset/EOG/cap与写入锁问题，保留版本和失败。F0B冻结所有实现、命令、source/binary hashes、输入、完整slots/timer/statistics，远端核验后自动进入正式阶段。

六独立日期，三家族各自每天一独立会话、四轮、六个条件，每block新resident server、固定synthetic warmup、24个真实paid请求。遵守顺序/冷却/完整数组和比较绑定gate。最大10,368正式、432warmup、640工程、128辅助decode，32小时自有GPU进程生命周期、14日；不以12,000硬停止线余量补跑正式slots。操作missing/divergence/慢均保留，受影响pair的qualified speedup为null。

唯一主检验Llama M3/C3_K3，同时ordinary R/C3_K3，六日期t区间；k1/k2次检验按冻结12比较的保守区间。报告三家族所有结果、Smol负结果、两domain、每日期/任务回归以及真实proposal/accept/verify成本计数。不要根据确认速度换主配置，不承诺普适加速。

创建新的结果draft PR并交付可复算、恢复和远端核验的证据。只做RTX研究，不发其他平台消息、不自动merge、改论文结论或发布。资源/恢复/架构/输入阻塞照实交付具体status与已有证据，其他独立家族可按已冻结计划推进。
