# 删除后的证据可得性

本次没有删除、移动、恢复或重压缩实验数据。只依据清理执行记录、现存索引、有限样本和归档验证记录界定可复核范围。公开文件使用项目内逻辑路径；主机地址、账户、设备 UUID、凭据和公司绝对路径不发布。获准维护者可在原项目根目录解析相对路径。

## 实际清理，不把候选清单当作执行结果

| 已执行类别 | 路径数 | 已分配空间减少 | 恢复与损失 |
|---|---:|---:|---|
| 完整模型对应下载分段 | 3,283 | 54,235,521,024 B | 保留完整模型，经完整 SHA/字节数及分段区间比对，可精确切回；硬链接去重后少于原估算 |
| 已有完整副本的构建 `.o` | 18 | 137,965,568 B | 可恢复对应成员或按保留源码/库重建；最终二进制、库和失败日志保留 |
| 已验证 zstd 副本的原 tar | 3 | 18,897,506,304 B | 先完成整条解压 tar 字节与成员验证，再删除旧 tar；压缩件仍在 |
| 批准裁减的中间 `sequence.bin` | 17,181 | 786,188,636,160 B | 按精确文件名单执行；没有为该类别整体建立新副本。不是按目录删除；不等于每个内容都没有现存副本 |
| **合计** | **20,485** | **859,459,629,056 B** | 这是删除文件的 allocation 减少；新归档新增约 16.345 GB，不能把该数直接说成共享文件系统空闲差值 |

更激进的 MINIMAL 方案中另 250 个文件、11,595,653,120 B **未执行删除**；本机重复交付包 271,156,343 B 也还在。787 个受保护 anchor 全部保留，119,990 个剩余数值/receipt/result/STATE/账本文件的元数据检查未发现变更。清理后项目磁盘 allocation 记录为 667,339,358,208 B；保留数值与记录的逻辑长度合计 536,581,785,553 B。二者口径不同。

执行记录位于项目相对路径 `storage-review-20261113-01/cleanup-20261113-01/`；精确删除清单 SHA 为 `3f116d7591b841d43953ebf31a838e763e5b0980ef060da52f60bdceb0750971`。这些私有清单没有随公共 PR 发布。

## 按主张的复核能力

| 主张／材料 | 保留位置或直接来源 | 现在能复核 | 不能声称／其他副本 |
|---|---|---|---|
| #218 S3 完整服务强基线 | `strong-baseline-followup-20261110/`，原 job `sb217-s3-20261110T1842Z-01`；[公开冻结结果](https://github.com/leecdiang/HeteroSpec/tree/ab695a766d055f7d3c6b1fed0720c579c749bcdb/benchmarks/server_expansion_v1/strong_baseline_followup_20261110/RESULTS_S3_20261112)；本目录 `statistics/service/` | 逐请求统计、12 roots 分层区间、输入/配置/版本、资格证书与保留完整参考/边界样本 | 被删每一步不能直接从原路径读取；实际索引中删除的 S3 KV 是 **5,964** 个；见下方副本证据 |
| #203–#208 8B/14B/Llama | `run-01/`、`m1-run-01/`、`f-run-01/`、`d14-run-01/`、`d14-attribution-run-01/`；本目录 `statistics/pr20*/` 与 [固定来源](CLAIMS_AND_BASELINES.zh.md) | 五个面板全部计时估计与区间；#205/#206/#208 原 receipt 哈希、原冻结分析和独立实现；完整输出、主参考、分层样本保留 | 不把数学复算叫重做 GPU 资格；已裁减非参考逐步 KV 的全部原始字节不能统一承诺恢复 |
| #221 全向量、状态、消费者反例 | [公开源码、RESULT 与历史独立审阅](https://github.com/leecdiang/HeteroSpec/tree/af436df989570ad882db65bd8a4b265b9e8cfdae/benchmarks/frontier_cost_v1)；[本次定位状态](evidence/PR221_LOCATION.json) | 能核对方法、比较工具、当时计数/差异与预期 payload 哈希 | 实际 CPU tensor payload 未定位，不能重新逐字节验证；没有证据表明被本次 A5000 清理删除，也不能断言没有其他副本 |
| #232/#233/#236 生命周期与自由多轮 | 下述三份 zstd 包，以及原实验目录；#236 episode 统计复制到 `statistics/service/` | 这些包具有完整 tar/成员回读证据，保存原始向量/KV及失败；可以复算已执行八个 episode 的成本 | 保留包未再执行 GPU；两个 supplied/free 开发案例不代表全部自然会话，也不补足未覆盖 EOG/261 项 |
| #238/#239 机会与限制 | [#238](https://github.com/leecdiang/HeteroSpec/pull/238)、[#239](https://github.com/leecdiang/HeteroSpec/pull/239) 的源码、geometry、REPORT | CPU LCP/模板/调用差异与 No-Go 推理 | 8 请求机制重放没有执行，不能写成实测后端成本 |
| RTX #237/#240 | [#237 公共样本](https://github.com/leecdiang/HeteroSpec/tree/c8e5ea070ac393d7513903e0ec261dfce4554a49/benchmarks/rtx223_e11_u_contract_20261113)、[#240 状态](https://github.com/leecdiang/HeteroSpec/tree/d240c5b43a763d5b02b5a53169b07f8e8af71a6c/benchmarks/rtx223_e12_backend_closure_20261113) | 公共 CSV、数值合同、构建/静态检查和已执行范围 | 不假设 A5000 保存 RTX 私有 tensor；full backend NOT_RUN |

### S3 副本发现与验证限度

`retention/S3_COPY_MAP.csv.gz` 对照原 numeric index 与真实删除日志，逐项列出 5,964 个已删 logical ID → 当前存在的保留候选 ID、长度和历史 SHA。全部能匹配候选，合计逻辑数据 249,189,106,152 B；按候选内容去重约 62,524,973,064 B。**只有 3 个有界样本完成本次新内容 SHA 检查，均一致。** 其余为历史 SHA/size 相等且当前路径存在，不能升级成“全部已恢复/已验证”。

详见 [S3_COPY_COVERAGE.json](retention/S3_COPY_COVERAGE.json)。如需恢复每一步原始字节，最小额外工作是读取约 62.5 GB 唯一候选内容，对照所有 SHA，再按映射流式读取或恢复约 249.2 GB logical payload。此处没有执行；它无需 GPU，但会占共享 I/O，只有论文确需逐步全复核时才值得做。其他实验没有作这样的全候选映射，不从 S3 外推。

### 完整压缩包

项目相对目录 `storage-review-20261113-01/archives/`：

| 包 | 压缩 bytes | 覆盖 |
|---|---:|---|
| `PR231-pilot.tar.zst` | 765,885,840 | #232 的原 pilot，638 个成员 |
| `PR233-qualification.tar.zst` | 8,987,790,835 | #233 资格、9,060 个成员 |
| `PR236-free-service.tar.zst` | 6,319,882,859 | #236 自由多轮及相关记录、6,697 个成员 |
| `LOCAL-CLOSED-DELIVERIES.tar.gz` | 271,156,343 | 五个本机闭环交付目录的补充快照；不是整个实验盘 |

前三份总计 16,073,559,534 B，替代的旧 tar 合计 18,897,506,304 B。它们不覆盖旧 1.31 TB 的全部内容。归档在**同一物理存储**，不是异地备份；公共报告也不是私有原始 tensor 的副本。

公共数据足以复算本目录全部统计。公司原始捕获、机器路径和模型不在本 PR 中公开，不能承诺任意读者直接访问；需要另行协调获准访问、已有合规副本或按固定身份重新构建。数据声明应逐项区分公开统计、受限原始样本、被裁减中间量和未定位材料，不能笼统写“全部原始数据公开”。
