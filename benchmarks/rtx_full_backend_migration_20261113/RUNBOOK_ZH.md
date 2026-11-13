# #244本机执行已收尾

已按用户独立授权完成两臂资格、P128/G64正式请求。实际220请求、51370rows、18模型部署，GPU窗口约18.09分钟。完整报告见[windows_20261113/RESULT_REPORT_ZH.md](windows_20261113/RESULT_REPORT_ZH.md)。原设计/CPU-only runbook与全部9个原文件以PR939b0ee51的精确版本保留在审计包。

本机执行源快照、编译日志、失败、账本、所有正式request/输出、完整资格对比与图均在windows_20261113/。大体积全词表F32留在本机，公开RAW_F32_LOCAL_INDEX绑定16个原始文件；不包含模型/厂商DLL/全主机私人命令行。

不要重跑现场campaign入口：18次部署已耗尽，8次请求余额并不授权追加模型加载或重复面板。现场脚本是本机路径与旧资产绑定的实际快照，不是通用自动安装器。复现需映射原始R资产、固定M源码和模型，在新独立合同/授权下使用。不要用run_session.py新建空账绕开本累计ledger。

R薄port保留原完整libllama.a与所有原CUDA/CPU DLL，内部ubatch1/reserve1；M完整build固定0fb8f157、ubatch32、graph/PDL允许，FA关闭/F16KV/ctx1024/2threads共同包络，GGML_NATIVE=OFF已声明。不是全部factory defaults或最优现代配置。恢复步骤/计时边界见IMPLEMENTATION_PROTOCOL_ZH.md和构建脚本。

P约32.15%降时是不同数值合同的完整模型固定工作成本；G全部cap128且仅20/32跨臂token轨迹相同，不称质量非劣。R/M完整诊断差异很大，原始数值保留；未定位差异机制。正式输入仅26–161token，长输入性能未测。21CPU测试普通和-O通过，Windows真实编译链接及两臂原生资格通过；CPU mocks不是GPU正确性证据。

无待处理GPU队列或管理员控制器，已释放RTX锁。用户授权仅终止过绑定的OnDeviceModel utility PID29020，保护本对话主进程PID28000；无设置/ACL更改。旧实验额度、失败、数据不改，不合并、不改论文或投稿。
