# 受限进程错误 2 的定位

当前 #230 head 为 `45a867d6ca9300bd4080291db370017953c1ec50`。e06 使用的 SECURITY_CAPABILITIES=0x20009、JOB_LIST=0x2000d 与冻结 Windows SDK WinBase.h 的定义一致。结构大小及普通 Job 路径已在本机 CPU 替身中成功使用。

新诊断保留同一原子 Job、零能力 AppContainer 和挂起创建：

| CPU 变体 | 结果 |
|---|---|
| 相同 cpu-probe，只使用限额 Job | 创建成功，active=1，未恢复，随后终止自有 Job |
| 相同 cpu-probe，加原 AppContainer | CreateProcessW 返回 2 |
| 相同 cpu-probe，cwd 换成 System32 | CreateProcessW 返回 2 |
| 改为 System32/cmd.exe，同一隔离及 System32 cwd | CreateProcessW 返回 2，未启动命令解释器 |

派生包 SID 成功，但 GetAppContainerFolderPath 返回 `0x80070002`、路径为空。官方启动流程要求创建每用户 profile，然后取得 SID；已有 profile 才使用派生 SID。当前代码只执行派生 SID，未建立 profile。多路径对照排除了仅由项目 EXE 拼写或工作目录造成错误的解释。尚未建立 profile 存在且就绪的前置证明，也未通过创建 profile 的对照实验断言错误 2 的唯一原因。派生 SID 成功不能证明 profile 已存在。[Microsoft 的 AppContainer 启动流程](https://learn.microsoft.com/en-us/windows/win32/secauthz/implementing-an-appcontainer) · [创建 profile 的副作用](https://learn.microsoft.com/en-us/windows/win32/api/userenv/nf-userenv-createappcontainerprofile)

静态读取 cpu-probe 和数值根 DLL 的现有 DACL，仅含用户、SYSTEM、Administrators，没有新包 SID 的读取 ACE。创建 profile 后，读取批准映像仍需用真实子 token 验证。模型目录 DACL 原样保留。

拟议修复是创建专用零能力 profile，并在全新的 staging-B1 中复制两个探针与十个 DLL，共 812,146,832 字节；只给该包 SID 此新树的读取和执行权限。无需变动源文件、旧依赖、模型目录、父目录或 System32 的 ACL。profile 自带专用存储，TEMP/TMP 指向其 Temp。用户尚未批准的配置变更不执行。

`diagnose_cpu.py` 与 `DIAGNOSIS_CPU.json` 包含实际挂起创建和回执。`prepare_staging.py` 默认只计算计划；`STAGING_PLAN.json` 绑定源文件身份。apply 会新建 profile 和 ACL，必须在取得明确批准后使用。所有新 profile、目录及部分失败记录都保留，待确认依赖进程和句柄结束后再按其身份处理。

本组诊断的数值 DLL 正常加载、CUDA 初始化、GPU context、模型和 kernel 均为 0。
