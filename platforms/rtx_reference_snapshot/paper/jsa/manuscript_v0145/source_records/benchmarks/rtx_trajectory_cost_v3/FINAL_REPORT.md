# RTX V3 实验终止与证据交付报告

本轮已完成协议要求的失败终止、原始证据封存和独立核验，但正式实验未完成全部计划。工程阶段 400 次有效运行完成；正式 A、B 均在首个 capture 操作失败处不可逆停止。没有补跑、替换记录、修改冻结候选或启动新研究。

| 阶段 | 计划条件数 | 有效完成 | 失败 | 未到达 |
|---|---:|---:|---:|---:|
| A pre-live | 288 | 72 | 1 | 215 |
| A native live | 72 | 0 | 0 | 72 |
| B matched cost | 216 | 54 | 1 | 161 |
| 合计 | 576 | 126 | 2 | 448 |

这 576 个条件来自冻结的 24 个不同任务及重复/条件组合，不能视为 576 个独立样本。正式 A/B 观测没有共享；工程记录的共享引用明确保留相同 run ID。

失败原因：HumanEval-59 的 A_REFERENCE_UB1 与 B_SERIALIZED_K2_UB1 均由原生程序正常退出（exit code 0），原始日志记录连续 128 个 committed token，末 token 151645 为 EOG；同时出现 limit 和 EOS 两条停止标记。冻结的 native capture parser 只接受一条停止标记，故记录为 INCOMPLETE_OPERATIONAL_FAILURE。只读诊断不将失败改为有效，不据此扩充分母。原始 stdout/stderr、native logs、失败状态、事件和计时均已保留。

A pre-live 停止后，已先写不可逆 A 终止记录，再按同一冻结 24 IDs 进入 B；B 达到独立停止分支。A live 未运行，F2 未到达，完整 A 预测准确率不可报告；正式 B speedup 与置信区间均为 null，不能用已完成前缀代替预定全量统计。

冻结与顺序：
- F0：a48381567f7f40330a589e33d285650c9e91f209；工程与协议先发布并完整取回核验。
- F1：68a1c1deb8a9e0204428cc605ed2320dd8a4215a；远端确认 2026-10-02T04:54:57.895325+00:00 在第一条 reserved 执行前。
- A 终止：2026-10-02T05:04:36.681352+00:00；同集合 A 继续入口关闭。
- B_START：85c51a6f1ebb64bf0fbf112df0cfc2c8c32de5e5；A 终止后、B 执行前发布并完整取回。
- B 停止：2026-10-02T05:22:22.031295+00:00。
- COMPLETE 仅为终止后的证据交付检查点，不替代未到达的 F2，也不认证完整正式实验成功。

授权形式偏差已显式记录：用户在两次呈现具体 F0 完整 SHA 与 Draft PR 后回复“继续”，据此执行该版本；用户没有逐字输入 EXECUTE_FROZEN 或重新输入完整 SHA。AUTHORIZATION.json 保留原话与解释，未伪装为用户逐字指令。

固定输入与工程资格：曝光审计保守排除 138 个任务，26 个可选任务中按固定 salt 选定 24 IDs：2,161,86,157,16,158,59,40,31,99,49,25,141,76,142,109,15,66,81,136,148,18,143,87。五类 mandatory gates 各 36/36；20 个 observer on/off 成对记录、400 次完整工程运行、15 类真实原始数据损坏负例拒绝及 3 个 mocked failure-path 检查均保留。工程资格未覆盖同时 EOS/cap 的采集分支，此限制已由正式失败显现。

实际调用计数：工程模型进程 443，A reserved 子进程 91，A live 0，B 55；合计 589 模型进程。worker logical forwards 13452，worker operation calls 11658，tokenizer-only 2 个进程且 0 forward。A reserved 原生 distinct logical forward 数无法从失败记录严格确定，保留 null；allocator records 不作为独立 forward 数。完整 append-only ledger 已封存于作者版包内。

四份最终前缀证据包均在新的目录中真实解压，并由冻结的独立 offline verifier 验证逻辑成员哈希、400 次工程运行、15 类负例、正式有效/失败前缀；作者版另外验证 F0/F1/B_START 的便携 Git 对象归属证明。下列 complete 是证据包类型名，表示保存全部实际到达记录，不表示完成全部正式计划。

| 部分 | 版本 | 压缩字节 | SHA-256 | 离线核验 |
|---|---|---:|---|---|
| A | 匿名 | 60082374 | 929b33d9c267c641ac22fb639aa78d3a9cfe97deb9057d74b7ce7329b1efdd4f | PASS |
| A | 作者 | 378789940 | 9653cdd8601effb962dd2f7f1e7f98bf6e21318bb84cd8a7ddb5cec0fd07d58a | PASS |
| B | 匿名 | 64754800 | c2e059e454d4aeac276db8ea1b27d37386f3c327e09923107021045328324670 | PASS |
| B | 作者 | 383505864 | 7f801ca7b9a14ad81474cb4d5c84c221d7a847babba89857dc9a82849041919f | PASS |

每份包按 48 MiB 分片，索引含分片字节数、SHA-256、逻辑成员目录及完整重建说明。COMPLETE_ARTIFACT_MANIFEST.json 是最终八包总索引（四份工程包加四份最终前缀包）；原 F0 绑定的 ARTIFACT_MANIFEST.json 字节不变。归档阶段使用 Windows 长路径名和标准 tar 内部 hardlink 存储相同字节；只对传输先解压 gzip 一次，没有修改冻结数值实现、原始证据、计时或验收规则。所有归档操作失败与恢复均记录于 ARCHIVE_ATTEMPTS.json。

可移植验证不需要 GPU 或网络，但外部模型、原生 DLL 和硬件身份仅通过清单哈希引用，未打包也不能由离线包直接认证；匿名版省略身份与 Git 来源证明，UTC 改为顺序信息，不能认证远端冻结或外部资产。Git 内容/祖先证明与服务器响应 Date 均不等于独立可信时间戳。历史缺失原始档案保持缺失说明，未补造旧记录。

固定 target 8B Q8 SHA-256：408b955510e196121c1c375201744783b5c9a43c7956d73fc78df54c66e883d6。draft 0.6B：9465e63a22add5354d9bb4b99e90117043c7124007664907259bd16d043bb031。数据集 gzip：b796127e635a67f93fb35c04f4cb03cf06f38c8072ee7cee8833d7bee06979ef。RTX 5070 Ti Laptop、原 runtime 与 GHelper 配置的执行前后身份复核通过。

改动严格位于四个新增研究目录。旧论文、旧实验数据、主分支和 mlsys2027-v0.8-author-freeze 标签未修改，作者目录 D:/HeteroSpec-PC 保持只读。Draft PR：https://github.com/leecdiang/HeteroSpec/pull/48；没有合并或自动整合论文。后续若要修复采集器并研究，需要独立新 study 与新的未曝光集合，本 prompt 不自动授权启动。
