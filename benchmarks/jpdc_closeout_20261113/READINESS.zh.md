# 零 GPU 收口决策与剩余事项

本次已经完成：方法保证与实际 guard/状态边界对应、固定版本登记、五个 8B/14B/Llama 面板统计复算、S3 分层推断、自由多轮负结果、删除后可得性、OASST 冲突的来源核对。论文没有被修改。

| 剩余事项 | 现有资料能否解决 | 本次处置／下一步 |
|---|---|---|
| 方法表述不要超出 guard | 能 | 对照 GUARANTEES 与固定源码；将“通用在线证明/无副作用回退”收窄为受支持配置和离线资格，作者在论文编辑时落实 |
| 强基线、负结果、分母、重复单位 | 能 | C/B 为 S3 主比较；固定 packing 与 LOCAL 分开；自由多轮无服务收益；所有原 root/轮次和差异案例保留，不因不利结果删样 |
| 版本与统计复算 | 能，已完成 | 本目录提供逐请求计时、冻结计划、全估计与区间、独立脚本；不混池、不升级原分析器 |
| 原始数据声明 | 能，需按权限准确措辞 | 公共统计与受限 raw 分开；同盘归档不是异地；S3 仅 3 个当前内容抽查；#221 raw 未定位 |
| #221 原始反例逐字节独立复核 | 目前不能 | 有公开源码/当时审阅与摘要，但原 CPU payload 不在已知可访问位置。应先联系原执行环境/现有归档；若找回，成本仅 MB 级读取，不需要 GPU。未恢复前将主张限定为历史诊断。没有确认“永久丢失” |
| OASST 标签冲突 | 能，已解决来源 | successor 勘误为冻结 Apache-2.0；不改旧结果，不把模型许可混为一谈 |
| JPDC 专属格式、长度、匿名要求等 | 本次无法完整核实 | 两个官方作者指南入口均返回 403，保留 EXTERNAL_ACCESS_BLOCKED；由作者通过可访问浏览器/编辑部最终确认，不能填造要求 |
| 通用出版数据与 AI 政策 | 能核实通用来源，需作者完成自身声明 | [Elsevier manuscript preparation](https://www.elsevier.com/en-gb/publishing/publish-in-a-journal/manuscript-preparation) 与 [generative AI policies](https://www.elsevier.com/about/policies-and-standards/generative-ai-policies-for-journals)。人类作者承担责任；适用 AI 辅助使用、方法和数据可得性声明应按真实情况完成。这里不代作者宣称已满足全部投稿义务 |

作者指南入口：

- https://www.sciencedirect.com/journal/journal-of-parallel-and-distributed-computing/publish/guide-for-authors
- https://www.elsevier.com/journals/journal-of-parallel-and-distributed-computing/0743-7315/guide-for-authors

## GPU 决策

**对本目录明确收窄后的论文主张，没有必须补做的 GPU 实验。** 5% 不是完成或投稿条件，不扩大自然会话面板、不启动 #238 八请求重放、不补齐表格。

以下若仍想保留为论文新主张，才可能需要另立小实验或更大研究：现代完整 backend 的公平服务比较、自然 EOG/更广生命周期资格、所有 packed descriptor 的 fail-closed admission、新的自然多轮 LOCAL 服务加速。最小本轮方案是排除这些未建立的主张，不声称本次解决了它们。

若希望 #221 的全部原始诊断也能当场重放，应先恢复已有 CPU 捕获；若确无可用副本，再决定是否批准一个单独身份的 CPU 实验。不能用新生成样本冒充旧原始记录。S3 约 62.5 GB 候选内容的全量 SHA 校验也是可选零 GPU 工作，不是本次统计/有限样本复核的必要条件。

停止状态：本轮不执行模型，不新增 GPU 预算，不修改论文或旧基线。剩余外部访问与 raw 定位缺口明确保留，没有以新增 mock、控制器或门控掩盖。
