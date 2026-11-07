# B570 prefill 诊断研究：封存与上传交付报告

状态：**COMPLETE / UPLOADED_AND_REMOTE_RESTORE_VERIFIED**。正式计划 360 条，合格完整记录 360 条，失败 0 条，额外尝试 0 次。封存和上传期间没有新增模型推理、补跑或改动冻结执行源码。

## 远端保存与恢复验证

已上传至现有私有仓库 `leecdiang/HeteroSpec` 的独立分支 `codex/b570-prefill-diagnostic-v1`。30 个归档分块分四批保存，每批均核对远端提交。内容检查点为 `5983e17d6ec62dc9878c30d92d30948520ea893f`；其后的最终交付提交只补充收据、恢复说明和本报告。

从 GitHub 新建隔离的浅克隆并通过网络取回全部分块，没有借用本机研究仓库的 Git 对象。对取回的数据重建 4,073 个清单文件并逐项核对 SHA256，随后重新直接读取 360 条正式 raw：独立核对 **182,736 项全部通过**；另行重算 120 条 G0 数组和 30 对 sham trace/decision/score 控制，均通过。冻结执行源码字节一致，所有研究汇总结果与原封存值一致。详见 `REMOTE_DELIVERY.json`、`UPLOAD_RECEIPT.json`。

首次取回时，Windows 的全局自动换行设置把工作副本中的 JSON 从 LF 转为 CRLF，导致工作副本哈希失败；GitHub 中保存的 Git blob 字节和全部 30 个分块一直与封存值一致。失败记录保留在 `REMOTE_READBACK_ATTEMPTS.json` 与 `delivery-logs/`。已增加封存文件的字节保留属性，并从网络取回的 Git blob 原样生成两份封存 JSON 后完成最终核对。此修复只涉及交付工具和工作副本元数据。

## 两份归档及封存范围

远端可恢复证据包共 **1,473,070,703 字节**，30 个按 SHA256 命名的分块，包含 4,073 个可重建文件。索引和逐文件清单位于 `artifacts/b570_prefill_diagnostic_v1/ARCHIVE.json`、`REMOTE_MANIFEST.json`。

```text
远端证据包 SHA256
29ff8282a2751342c834d5a81c27c76daedab611205889a5a7c6ee8ec4ee45d8
```

本机原始完整 capsule 保留在 `C:/hs/b570-prefill-v1/artifacts/b570_prefill_diagnostic_v1/capsule/raw-capsule-v1.tar.gz`，18,950,381,810 字节，SHA256 `4ce6f65211c2847088ca4318746d47da369ea7596a88469be11c0e6aaecc5896`。原研究 Git bundle 与最终交付 Git bundle 保存在同一 `capsule/` 目录；最终本机 `FINAL_DELIVERY_SEAL.json` 绑定最终远端提交、交付 bundle 和收据。

远端证据包对重复内容去重，恢复为各自独立的普通文件，完整保存数组、endpoint、trace、attempt ledger、KV/pending-logit 证据及必要源码。按仓库数据规则未上传模型权重和可重建运行库二进制；它们的身份哈希仍保留，但离线恢复不能认证未包含的字节。原本机 capsule 不受此次压缩和去重影响。

`DELIVERY_SEAL.json` 是事后交付封存清单，绑定原冻结、预测封存、原始 ledger 和归档。原 `SUMMARY.json`、`ARCHIVE_RECEIPT.json` 和该交付 seal 的待上传字段保留当时快照，不覆盖历史；当前远端状态以 `REMOTE_DELIVERY.json`、`UPLOAD_RECEIPT.json` 及本报告为准。

## 原研究资格与结果

G0 和全部正式基线回归通过。72 条 T1 预测先完成本机封存，之后才启动 N1；本机事件记录支持顺序，未独立认证绝对时间。本次 GitHub 上传发生在研究完成之后，不能当作原预测的前瞻远端时间戳。

| 比较 | 完整数组及 endpoint 匹配 |
|---|---:|
| T0 / N0 | 72 / 72 |
| T1 / N1 | 72 / 72 |
| N0 / R | 60 / 72 |
| N1 / R | 72 / 72 |

四个诊断案例 HumanEval/134、42、145、138 均恢复参考完整输出；20 个控制任务零新增回归。24 个任务三重复均稳定，重复用于稳定性核对，任务样本数仍为 24。

结果支持：在这套固定 B570/Vulkan 配置及已接触的任务中，简化复现器指导的目标 prefill 干预迁移到原生 speculation，并恢复四个案例的参考输出。它不支持唯一 backend kernel 或硬件根因、跨平台规律、功能正确率、速度或能耗提升。详见原 `STUDY_REPORT.md`、`DECISIONS.md` 和逐任务表。

## 恢复入口与下一步

在包含全部 30 个分块的仓库工作副本中执行：

```powershell
python scripts/platform/b570_prefill_delivery_v1/restore.py --archive artifacts/b570_prefill_diagnostic_v1/ARCHIVE.json --dest C:/hs/prefill-restored-new --receipt restore-receipt.json
```

目标目录必须为空；恢复程序只做离线重建和验证，不启动 GPU 实验。现有研究冻结不变。此次没有修改 main、tag、PR #51、旧稿件，也没有 merge、release 或投稿。后续稿件整合或新研究另行授权。
