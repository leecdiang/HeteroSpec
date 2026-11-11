按用户明确授权，完成#213冻结审计提出的37请求补证：29个原Windows标量R case、八臂各1个heavy请求。已暴露APPS/train/603（prompt178/cap96）上，全部自然跨extent拒绝/回退、完整向量、active target KV/frontier及与旧clean的语义桥接通过。原1024次正式测量及其统计保持原样。

- 独立R库：257个完整151936维F32向量、40个active状态前缀。
- 新候选：1936次完整向量比较、296次active target KV比较，全部全字节SHA256相等；检查1352个完整draft提案向量的有限性/argmax。八臂共20个跨界cycle、16次跨界拒绝。
- root603原8块的64条clean轨迹离线关联一致；这不等于恢复旧clean缺失的KV。
- 全部37逻辑请求、16 native worker完成；18543保守行，实际12687行。RTX最新2716/3072请求、2872841/4000000行；资格500/512、余12，无阶段借用或退款。
- 初始源/输入/数值验证器和精确29+8清单在任何本轮模型输出前发布并完整回读。首R worker已完成4case后，模块清单路径字符串被读成对象而触发Python错误；原FAILED/STOPPED/source和成本保留，离线重核后原样复用，0 native重跑。仅模块读者适配器公开修补并回读后继续余33请求，未改native、输入、判据、顺序或容差；不将整个执行器描述为一次性全源事前冻结。
- 4478个逻辑文件完整归档并逐字节恢复；用归档源与raw重新执行全部独立向量/KV/轨迹比较一致。远端24分片/12279828字节/549条文字记录全部下载核对。数值二进制完整留在本地CAS；公开文字回读不是远端GPU复验。

[完整补证结果](https://github.com/leecdiang/HeteroSpec/blob/8ed93ff57c8536ff0dd1c717a4b9c884de90a905/benchmarks/rtx_q8_correction_draft_20261109/RESULT.md) · [冻结方案](https://github.com/leecdiang/HeteroSpec/blob/b1a41dc0fe60012a331552510dd6156d58391ba5/benchmarks/rtx_q8_correction_draft_20261109/PROTOCOL.md) · [最新RTX账本链](https://github.com/leecdiang/HeteroSpec/blob/8ed93ff57c8536ff0dd1c717a4b9c884de90a905/benchmarks/rtx_q8_correction_draft_20261109/results/CUMULATIVE_LEDGER.json)。

本补证只加强一个事后按覆盖选定根的有限状态证据；不抹去原全局冻结违例、312秒间隙或未记录尝试风险，不恢复旧KV，不是独立盲样本/新速度确认。没有kernel/架构因果或M优越性新主张。旧审计、数据、历史基线和论文未修改；未合并、发布Release、提交论文或启动32B/B570。
