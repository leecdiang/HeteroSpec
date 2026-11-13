# e07 现场诊断与一次 B1 授权

父 head 为 #230 的 45a867d6ca9300bd4080291db370017953c1ec50。用户本轮明确授权今晚单次 B1，无模型、无 forward、无主动 kernel，接受独立合同的隐式工作及异常清理上界未知。原 4096 合同继续未闭合。旧 release 的 42 个绑定文件复查无差异。尚未创建 B1 attempt。

两个错误已并行定位。ETW 的 StartTrace/OpenTrace 成功，拒绝发生在 EnableTraceEx2(process/image provider)。新版本调整失败收尾顺序，自有会话能以状态0停止；当前身份的 provider 启用仍为5。受限进程使用的 Windows 属性常量正确，同一CPU镜像普通Job成功，AppContainer下换用System32工作目录和cmd.exe仍为2；GetAppContainerFolderPath返回0x80070002，专用profile未注册。项目可执行文件也未授予该包的读取权限。

必须由用户确认的两项现场变更已经提交确认请求，尚未执行：

- 创建专用零能力 AppContainer profile，在全新 staging-B1 目录复制12份冻结文件（812146832字节），仅向该包SID授予新树RX；原文件、模型目录及系统/原父目录ACL不改。先做CPU启动、实际映像读取及54个模型路径拒读检查。失败即停。结束后核实自有进程/句柄消失才删除本次新profile。
- 一次UAC提权运行固定、已冻结的ETW CPU检查；若通过，在同一拟用身份下重验CPU Job/隔离，并有条件使用用户已授权的一次B1。没有持久用户组、provider ACL或服务修改。

23:17（上海）的只读宿主视图含354进程、204注册任务及313服务，未见专用worker或直接项目任务/服务；173进程命令行不可读。已知旧marker和B1账本/锁缺席。WDDM采样显示三个3D engine各约3%，此样本不证明GPU独占。线程列表只显示本次Codex任务活动。正式运行前须重新核对现场，当前未宣称取得独占窗口。

全部本轮程序均为CPU诊断和静态/构建活动。NVML、CUPTI、数值DLL、CUDA初始化、模型、GPU context及物理kernel launch均未运行。B1为NOT_RUN。资格、配对GPU计时和模型闭环也为NOT_RUN。只有用户对必要安全配置步骤确认且两个准入条件通过，才可继续单次B1。下阶段A/B/C方案仅供另行批准。

[ETW直接证据](etw/ETW_DIAGNOSIS_ZH.md) · [受限进程证据](acl/DIAGNOSIS_ZH.md) · [现场快照](HOST_READONLY.json) · [任务配置复核](TASK_QUEUE_RECHECK.json) · [下一步A/B/C提案](NEXT_ABC_PROPOSAL_ZH.md)
