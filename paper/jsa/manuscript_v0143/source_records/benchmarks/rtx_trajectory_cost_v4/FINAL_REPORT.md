# RTX V4 完整实验结果

本轮完成了全部 456 个条件：保留并复用原有 228 次数值有效预测，新增 57 次真实解码和 171 次计时，未重跑或改写原预测。430 次工程验证也是此前已完成的本轮验证。

完成口径为用户明确授权的补充协议。下表统计数值与采集完整性；原环境一致性停止及协议补充的详细记录见[审计附录](HOST_POLICY_AUDIT_APPENDIX.md)。

| 阶段 | 计划 | 数值有效记录 | 运行采集失败 | 未到达 |
|---|---:|---:|---:|---:|
| A pre-live | 228 | 228 | 0 | 0 |
| A native live | 57 | 57 | 0 | 0 |
| B matched cost | 171 | 171 | 0 | 0 |
| 正式合计 | 456 | 456 | 0 | 0 |

这 19 个任务在 V4 首次选择时是曝光审计后剩余的完整未曝光集合：145 个任务被保守排除，其中包括旧 V3 实際曝光的 7 个任务。继续阶段复用已观察的预测，不构成新的未曝光队列。三次重复与多个条件不是额外独立样本；A/B 使用同一组题目，所有 B 运行均重新执行。

修复依据：pinned b10839 在第 128 个 committed token 为 EOG 时，先报告 limit，再报告 EOS。新采集器和独立核验器严格接受此完整边界，同时拒绝缺失、重复、反序与矛盾标记。实际 vocab-only API 查询得到全部六个 EOG ID，未创建 context 或推理。模型、数值 worker、runtime 和计时程序保持原字节。

新工程五项门槛各 36/36；修复专项五项门槛各 3/3，含 21 次真实同时 EOS/cap；20 个 observer pairs、20 次真实端点条件、15 个原始/统计负例及 14 份端点损坏 fixture 均独立核验。旧失败日志只作回归，不改写旧状态。

| A：对原生 batched live 的完整数组比较 | 精确 pairs | 全部三重复精确的题目 |
|---|---:|---:|
| Target-only UB2 | 51/57 | 17/19 |
| 独立 per-round P/R | 57/57 | 19/19 |
| Fresh R-only replay | 57/57 | 19/19 |
| UB1 reference | 51/57 | 17/19 |

Reference-divergent 题目数：2/19。H2/R-only gate：57/57。全部 A 条件重复稳定：True。候选状态和所有 first divergences 见 A_trajectory/REPORT.json。

| B 路径 | 完整数组 gate | 状态 | 加速比 reference/candidate | 95% CI |
|---|---:|---|---:|---|
| B_BATCHED_K2_UB2 | 51/57 | BLOCKED | null | null |
| B_SERIALIZED_K2_UB1 | 57/57 | QUALIFIED | 0.677351 | [0.661653, 0.691812] |

实测成本结论：B_SERIALIZED_K2_UB1 通过完整输出等值门槛，但其配对几何平均耗时约为参考的 1.476 倍，增加 47.6%。该合格路径未获得加速；未合格路径保留诊断计时，不报告无损加速比。

只有完整 57/57 gate 且 reference 重复稳定的路径，才报告三重复中位数之比的几何均值和 10,000 次 prompt-paired bootstrap 区间。失败路径的速度与 CI 为 null，保留计时仅供诊断。

论文边界：这是 19 个曝光条件化题目的有限集合验证，不能推广为随机代表性样本；候选的完整匹配仅支持该集合上的经验充分性，不证明必要性、唯一性、最小性或跨 backend 普适性。主计时是含日志、响应与同步的 instrumented post-prefill request latency，排除加载、初始 prefill 和 teardown，不支持吞吐、能耗或未插桩部署的声明。

可直接审阅的英文论文段落和结果表位于 PAPER_EVIDENCE_DRAFT.md；旧封存论文没有自动修改。

冻结与实际顺序：
- F0：06562c920046360bd1243a6d845408e9a371f3a1；完整远端取回确认 2026-10-02T08:38:06.152842+00:00。
- F1：d02f55c5d136b9043c5dd208db53511c15443f4b；完整远端取回确认 2026-10-02T08:39:31.845740+00:00。
- F2：f9b88dcdc5541297a32faa0437b2bad2b93ffafc；完整远端取回确认 2026-10-02T10:45:12.158717+00:00。
- B_START：d0a1238580f3daff0d8011fb07b4c5c63640828e；完整远端取回确认 2026-10-02T10:58:56.765736+00:00。

模型进程：工程 476、A reserved 342（其中 live 57）、B 171。worker logical forwards 21549；operation calls 18252。tokenizer-only 3 次，0 forward。原生 allocator metadata 不足以辨认独立 decode-call 分母，A reserved distinct forward 数保留 null；完整 ledger 已归档。

| 最终完整证据包 | 版本 | 压缩字节 | SHA-256 | 离线核验 |
|---|---|---:|---|---|
| A | 匿名 | 89274896 | befd156992138902624406a2c8c6f8854494caad7c7c00df3c4cf3de5bd6f6c7 | PASS |
| A | 作者 | 664483316 | d8f49929bddf5bb9da2cc685c384556892391fdb97793fdf06cde617e0644c8a | PASS |
| B | 匿名 | 116890414 | 7be6bd011a2f3741d6788f19768a1f2f5e40deceebb394ec9dd631a951fe2157 | PASS |
| B | 作者 | 692065302 | 8c8d60a5bfc4d8eb88b77c3a4b0de084092bb6e113ba0b4711edd922021f7183 | PASS |

总索引 COMPLETE_ARTIFACT_MANIFEST.json 包含四份工程包、一份 F2 pre-live 作者包及四份最终完整包，共九包。每份均从实际分片在新目录重建，并由独立 verifier 重新计算；作者版验证 Git 对象归属和冻结顺序。F0 的初始 ARTIFACT_MANIFEST.json 字节不变。

离线复核不需要 GPU 或网络，但不直接认证未打包的模型、runtime、驱动和硬件。匿名版本替换身份与时间信息，不认证原始远端时间或外部资产；Git 内容证明和服务器响应时间不等于独立可信时间戳。原始证据和数值实现没有在 F0 后修改。

用户授权原话保存在 NEW_STUDY_AUTHORIZATION.json；operator 将已核验 F0 SHA 绑定执行模式，不声称用户逐字输入 EXECUTE_FROZEN 或亲自审阅后来生成的 SHA。所有改动限于四个新增研究目录；旧论文、旧数据、主分支和作者冻结标签保持不变。Draft PR：https://github.com/leecdiang/HeteroSpec/pull/49。


方法与审计：数值实现、候选、完整输出 gate、日程、计时边界和 thermal/idle 规则保持冻结。原停止记录保留在审计附件中，不作新的未曝光独立样本或原无偏差环境协议通过的声明。
