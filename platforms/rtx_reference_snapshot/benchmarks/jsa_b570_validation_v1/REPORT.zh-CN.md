# B570 第二模型家族独立验证

状态：`COMPLETE_FIXED_CANDIDATE_ENDPOINT_TRANSFER_WITHOUT_ORDINARY_GAIN`。数值/成本矩阵已封闭；归档恢复与远端回读状态见单独交付收据。

按 PR #81 固定头执行，原桥接 32/32；SmolLM2 发现及观测资格 128/128；正式 384/384；16 次已暴露 warmup。共 560 次完整请求，失败 0，缺失 0，科学重试 0。

整请求付费时间包括 reset、状态/phase 修改、draft/verify/sampling/rollback/sync、完整 payload 与 IDs/EOG 读回校验。原生 whole/generation 另列，不代替 host timer。

| 条件 | 端点与 R 全队列相等且稳定 | 完整 raw 与 R 相等 | raw 四轮稳定 |
|---|---|---|---|
| R | True | True | True |
| N | True | False | True |
| M | True | True | True |
| C | True | False | True |

| 比较 | qualified host GM（baseline/C） | 诊断 host GM |
|---|---|---|
| R/C | 0.5461389078917818 | 0.5461389078917818 |
| M/C | 0.5615619463653193 | 0.5615619463653193 |
| N/C | 12.90583416102916 | 12.90583416102916 |

每任务取四轮成本中位数，再对全部 24 任务取几何均值；逐轮方向、全部逐任务比和完整负例见 D_VERIFICATION.json。资格失败时保留诊断耗时，qualified speedup 为 null。没有筛选通过任务。

自然状态支路：`NO_TRIGGER`；首两个触发和所有考虑任务列于 NATURAL_DIAGNOSTIC.json。未提交自然 KV 状态×路径因果证据。

本研究自有 GPU 会话累计 0.567 小时；包含 load、warmup、同步及会话等待，工程/正式预算分别核对。未读到固定温度/频率接口的会话明确标为 unavailable。

原生成 EXE/DLL 未改动；target 实际全 offload 25 层、draft 31 层，完整 49152 词表与 EOG/tokenizer 元数据独立核对。所有确认输入在任何第二家族 forward 前冻结，F0 与远端 head 收据已发布。

暴露审计覆盖约 6.7 万可访问文本，以 ID 和描述双重排除，与 RTX 计划确认名单分离；不可访问私有主机仍为未知，不称训练未见或全项目所有主机均已证明未用。

结论仅限固定队列端点和有限会话成本；完整 raw 后缀另核对并收费，不证明功能正确、跨日期稳健性或唯一算子根因。未合并 PR、改稿或追加旧 Qwen 优化。
