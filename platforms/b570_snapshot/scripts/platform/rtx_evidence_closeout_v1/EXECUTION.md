# RTX #89 本地执行

结果分支接在实际设计 HEAD e2d5dcbc224c086d1d6804de8ed925182bfa1404 上；旧 #84 数据只读。独立运行目录 D:/hsc89，单写者锁与不可覆盖请求账本。控制器不调用 Codex/OpenAI，也不根据收益改题、k、mask或家族。

准备入口依次为 prepare_run.py（完整作者档案真实恢复/独立旧CPU复算/六模型与数值DLL哈希）、build_run.py（只新增观测层的隔离静态core）、native_inputs.py（六份完整native词表及曝光输入 IDs）。它们没有新模型 forward。run_all.py 随后完成 F0A commit/push/实际认证Git blob读回、固定工程与profiling、完整历史审计及新偶数描述池、真实预算预估、F0B读回、3600formal/150warm、独立CPU分析和本地/认证Git档案恢复，再创建独立Draft结果PR。普通条件不加载draft。

本机执行使用 D:/HeteroSpec-PC/.venv-analysis/Scripts/python.exe。运行 run_all.py 后本地持续执行，不需要 AI 轮询。D:/hsc89/STATUS.json、controller.stdout.log、ledger/、runs/ 保存进度和完整证据。结束时 RESULT_PR.json 包含新结果PR链接；应在当前聊天使用 attach_artifact 附加这个实际新PR。不会合并或改论文/release。

核心工程每家族302计划单元，上限360；profiling每家族104计划单元（96请求+4load+4warm），上限128，互不借用。16小时 owned process与7天 outer上限连续记账；正式已启动槽不重复。Ctrl/C或主机睡眠/关机会影响未完成进程；已有槽保留，可在同一冻结预算内继续未启动槽，新worker仍收费及固定预热。AC/driver/power/loaded headroom与继承冷却门槛保持。冷却在worker之外，120秒后3次间隔10秒采样，最长600秒。

正式完整wall包含JSON提交、完整response/IDs/stop解析和endpoint校验；磁盘保存/哈希/模块认证在计时之外。counts只加轻量整数，所有arms相同。分项/重型观测仅限固定profiling面板；真实lite无法证明互斥完成wall跨度时，如实冻结 MODEL_TIMING_UNAVAILABLE，主资格与费用实验继续。完整raw IDs永不裁后缀，不扣除观测开销。

返回的工作量同时保留 llama_decode caller 和实际 process_ubatch graph_compute 行数，draft UB1标准调用按物理micrograph计数；不是硬件occupancy。proposal五种去向、输出来源、周期进展/位置、graph reuse、phase/reset/cap/EOG/rollback由轻量汇总及独立heavy重放核验。缺项与反例保留。
