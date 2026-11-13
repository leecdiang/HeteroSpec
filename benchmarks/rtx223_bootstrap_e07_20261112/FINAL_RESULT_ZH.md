# e07 · 已获准的单次 B1 结果

**B1 已执行一次并失败停止，额度已消耗，没有重试。当前没有 C 的原生数值或性能证据。**

两个 CPU 准入问题已经实际解决并取得同一管理员登录身份的正向回执。ETW 进程起止各1条、映像加载和卸载各31条，零丢失且创建时间匹配。新建的零能力 AppContainer 下，CPU 替身成功原子进入单进程 Job，54个模型路径有效拒读，12个批准DLL路径可读。用户明确批准了专用profile、新副本目录RX和本次提权范围，并现场确认UAC。原有模型、原文件与系统ACL没有修改。

## 单次尝试的直接结果

上海时间 **2026-11-12 23:43:15**，最终runner绑定了今晚23:40–23:59:59窗口与原B1操作限额。现场快照有364进程，未见专用竞争worker、项目计划任务或服务。runner取得UUID互斥及B专用marker，原账本无变化；NVML入场读数为0个计算进程、空闲12524191744字节、已用296747008字节。这些是现场可见范围，WDDM图形活动仍可能存在。

独立账本先登记唯一RESERVED，再创建挂起探针，核验PID/创建时间、单进程Job和54个模型拒读。探针仅报告READY。发放第一个METER许可前，观察器发现启动过程映射了未绑定文件 **C:/Windows/System32/apphelp.dll**，当场拒绝后续操作。该映像的本机磁盘SHA-256为055a5f86aae369ab44d0deebac7cc2104b4ab328718f3c028625bd63984cba32。本轮没有将它补入allowlist，也未再次执行。

退出记录明确为FAILED、自有子进程退出已确认、retry=false。ETW部分收尾状态0、丢失计数[0,0,0]；因提前失败，没有完整成功的进程/映像终态认证。没有任何stage_permit_consumed，故CUPTI加载、数值根加载、cudaGetDeviceCount和UUID查询均未发生。独立账本SHA-256为93511edae7577341b36fc30d50c72dae7363d64476e368634dff05013eab7e60，原路径与只读回抄逐字节一致。[账本](B1_ATTEMPT_READBACK.jsonl) · [退出](B1_LAUNCH_RESULT.json) · [入口输出](B1.stdout.log) · [准入现场](HOST_PRE_B1.json)

| 实际消耗或状态 | 数值 |
|---|---|
| 独立B1 attempt / 真实无模型探针进程 | 1 / 1 |
| 父控NVML普通加载 | 1 |
| CUPTI / 数值根DLL普通加载 | 0 / 0 |
| CUDA runtime API、显式context、主动kernel | 均为0 |
| 模型加载、forward、请求和数据行 | 均为0 |
| 全生命周期隐式context和物理launch | 未知；CUPTI尚未启动，不能由应用调用数推导为0 |
| 正确性、66格资格、GPU计时、模型闭环 | NOT_RUN |

## 保留与清理

确认launcher结束、无探针存活且B marker释放后，按用户批准删除了本次新建profile，DeleteAppContainerProfile返回0。新staging树约775MiB及其包SID的RX记录、源文件、所有失败日志和B账本保留。没有修改旧额度、旧参考或论文。[profile清理](acl/PROFILE_CLEANUP.json)

首次提权CPU入口因LF/CRLF摘要不一致在ETW启动前拒绝，保留旧脚本并按落盘字节修复。首次B launcher又因PowerShell UTC/本地日期比较在账本预留和所有GPU相关调用前退出；改为明确UTC后，本地ValidateOnly通过，再经用户确认UAC进入上述唯一尝试。两项启动准备错误均保留，未计作第二次B执行。release_v3已经生成并全部绑定，随后辅助审阅摘要的独占创建因旧摘要存在而报错；没有改写release，实际入口重新校验其SHA及所列全部文件。

## 下一步决策

本轮的失败揭示了Windows启动映像闭包缺项。要再运行B，需要先独立检查apphelp.dll的来源及可达依赖，把实际需要的身份纳入新的冻结候选，完成同一受限进程启动的CPU映像闭包试验，再提出**新的单次额度和明确授权**。不得重开本次账本或把未执行的数值调用退回额度。

[后续A/B/C提案](NEXT_ABC_PROPOSAL_ZH.md)给出Q8_0/F32、q8、K=M=4096的单描述符全字节门槛及最多567次显式应用kernel、120秒进程墙钟的独立提案。它尚未获准，也仍缺合格的真实q8捕获；现有q32前八行派生输入不能填补原要求。既有原生预算或本次bootstrap批准均未授权该阶段。原4096全生命周期硬合同继续未闭合，第二轮未开始，PR未合并。
