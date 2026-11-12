# PR223 第一轮续作：INCONCLUSIVE

本次修通了 Windows 前端的编译/链接，补齐并测试了所属 worker 的监督、锁和账本机制；**没有放行 GPU，也没有完成原生数值资格**。原线程当前终态和主机任务视图仍无法可靠核实，全模型 launch 上限也尚未落实。第一轮结论保持 INCONCLUSIVE，不进入第二轮。

新 epoch 为 `rtx223-round1-20261112-e02`，延续 e01 的同一资源族。开工时 #223 head 为 `bc78721363f01ae8f36dd7b1d32c89b8c9e26cea`，#221 为 `af436df989570ad882db65bd8a4b265b9e8cfdae`。核对了165份父版本清单文件、最新 ZIP、报告、独立复核与原 Prompt 1。远端根 AGENTS.md 仍返回404；遵循本会话提供的项目指令及适用的私有核心说明。

| 门槛 | 状态 | 本次证据与边界 |
| --- | --- | --- |
| 原材料/预算连续性 | PASS | 父源文件与交付一致，旧三账本主哈希相同；e01为0 attempts；新 canonical family ledger同样0 attempts，窗口未启动 |
| 原线程与主机排重 | FAIL：阻塞 | 直接API返回-32000；本地CLI历史只到11月9日；新应用目录找到两个候选线程，但无当前终态记录；Toolhelp与NT查询均只暴露沙箱进程 |
| Windows 监督器机制 | PASS，仅CPU OS验证 | 进程持有锁、CREATE_NEW未知锁拒绝、Job内所属子树、崩溃/心跳/超时、全局截止和费用保留；不等于全主机排重或GPU安全资格 |
| 动态前端构建/链接 | PASS | loop4/packed两臂使用原GNU/libc++ ABI参数及缓存CRT完成链接；两臂早期selftest通过，未初始化backend/model/CUDA |
| 新捕获/失效/计时源码 | PASS，编译/host检查范围 | 接入完整requested rows、target/draft的untrimmed/committed导出、几何、事务失效、state与服务端点hooks及捕获上限；实际native输出与端点未验 |
| Q8_1/dispatch导出补丁 | PASS，仅TU编译 | 原MMVQ后量化导出及逐case4提交前观察已编译；未链接新数值DLL、未加载或执行；不是clean dispatch保证 |
| 全模型4096-launch预算约束 | NOT_RUN/未实现 | standalone计数不能约束模型内直接launch、wrapper与graph replay；静态位置数不是动态次数或最低开销 |
| 22×3 native资格 | NOT_RUN | 66格未执行；没有把CPU拒绝、编译或selftest记为GPU资格 |
| A/B/C配对、真实请求链、服务净收益 | NOT_RUN | 原始配对为空，成本和误差区间为null；没有性能正负结论 |

构建故障通过对照隔离：`timeline.hpp` 的内容、UTF8编码和头文件路径正常，同样的最小C++程序在本机的 `zig c++` 驱动路径也报Unexpected；同一二进制的 `zig clang` 可以编译。改用直接Clang编译和原有缓存CRT/libc++的lld链接后，两臂完整前端成功。这里报告的是本环境中的驱动路径差异，不推断所有Zig安装都有同一故障，也不把链接成功升级为原生ABI或数值资格。

原41项普通/-O测试的源码身份仍有效，未重跑。新监督器的18项真实Windows OS测试在普通/-O下通过，并获独立复核；另有6项无CUDA的C++ launch账本检查，以及两臂早期host selftest。新增诊断成本读者覆盖state类别，但始终拒绝据此生成clean性能主张。各项精确命令、源码与产物哈希见各目录回执和最终独立复核。

独立审查推动修复了超额/未知费用被错误当作完成、退出与截止竞态、子进程Job绑定前失败清理、失败后的launch与捕获字节错误记零，以及fresh生命周期中事务指针失效等问题。早期失败与最终结果分别保留。OS测试使用唯一CPU-TEST锁及所属dummy子进程；其中合成的kernel计数字段不属于真实GPU用量。

本次实际模型请求 **0**、target/draft rows **0**、CUDA context **0**、kernel launch **0**、原生GPU耗时 **0秒**、GPU捕获 **0字节**。CPU编译、测试和独立审查的时间保留在各自原始回执；未将重叠耗时相加，也未把它们填进服务成本。原上限保持256请求、100万rows、10800秒单一窗口、4096个所有kernel launch、2 GiB捕获，warmup和失败余量在内；没有新预算、借用或重置窗口。

排重的剩余证据非常具体：与执行内容绑定的 #221/#223 当前终态或有效租约，以及可信的主机worker/监督器视图。本地找到的「合并关闭PR并审阅」与「第一轮结论汇总」候选行只有标题/更新时间，没有终态事件；空active表和GPU空闲都未被用于放行。另须落实全模型kernel的提交前上限，再链接、绑定和资格验证新backend导出路径。新mutex不会让旧的非合作客户端自动参与。

这些条件满足后，继续原第一轮的实际q8捕获、原路径/量化字节/全输出与状态资格；通过后才计时。当前C仍为独立算子候选，尚未作为已资格runtime路径部署，最强固定策略也未选择。没有可报告的C-over-packed差值、置信区间或服务净收益，更没有把既有投机收益计入新机制。未重跑#213 live或#215补证，未合并PR、改论文、发布Release或启动第二轮。
