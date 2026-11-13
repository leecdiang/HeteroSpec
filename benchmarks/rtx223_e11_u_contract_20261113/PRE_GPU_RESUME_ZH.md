# 接续e11，先现场Windows管理员启动

当前GPU尝试/预留/许可均0；旧e10永久预留14、实际6不变。不要重跑旧捕获、C/C1、e10失败或CPU构建。

1. 先核对最新PR head及e11当前文件身份。所选为build003、STAGING_V3、runner_v3。旧build001/002、旧CPU失败保留；它们不是待执行变体。
2. 当前控制器未启动，family.jsonl应不存在，CPU请求停放为admin-queue/001-cpu-admission-v3.not_run。先确认不存在活跃自有控制器/worker、未知锁或新冲突任务，不能删除未知记录。
3. 只有用户能现场操作时，移除**本轮创建且内容/合同SHA匹配**的ADMIN_STOP，恢复这个已哈希CPU请求为001-cpu-admission.json；再运行已冻结Launch-Controller.ps1触发Windows UAC。不要因聊天回复就假定启动成功，必须看到ADMIN_LAUNCH、READY及正确身份。当前冻结窗口至2026-11-13北京时间14:30；过期不启动，需要新版本窗口/控制器身份，仍受同一500累计上限约束。
4. CPU_SMOKE_PASS必须来自runner_v3、当前管理员身份、当前CPU受限子进程和完整ETW起止验证；旧回执不替代。失败先保全，不启动GPU。
5. CPU通过后，prepare_phase_v3.py qualification只排一次14预留任务。确认自有退出、完整ETW结束、native8次许可及A/U两次全量资格，再运行纯CPU independent_qualification_v3.py作独立验证。旧e10 FAIL仍不变。无合格结果则不计时。
6. 上述均通过后，prepare_phase_v3.py timing预留416，实际固定392。检查全部48样本、48次完整postbatch、operation counts74/122每臂及退出，随后analyze_v3.py保存全部样本/配对/敏感性。不删除失败、不退款、不执行新候选或完整上游默认后端。
7. 结束复制profile所有文件并校验哈希，再确认无自有进程/lease后删除本次创建的同名profile，停止控制器。预备快照PRE_GPU_RESULT、PREPARATION_LEDGER及.not_run历史留存；最终RESULT可更新，但这些准备与失败记录不能覆盖。

运行只包括固定UUID的同一首层8-token Q8_0操作数，不加载模型，不forward，不用新构建完整ggml-cuda.dll。生产默认拒绝和原4096未闭合状态不变。
