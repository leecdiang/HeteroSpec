# 2026-10-20 仓库审阅与合并记录

## 结论与本次工作边界

本轮完成对最新 PR #128、#129 的源码、实验范围和可取得证据的审阅，并通过 GitHub 插件按依赖顺序合并。两条 PR 可以作为**范围受限的实验记录与修复方案归档**进入 main；这项判断不等于 B570 全工作负载资格、通用 Vulkan 移植资格、CPU8/F0 准入，或新硬件收益已获证明。

本次审阅由同一对话中的主 assistant 与并行 assistant 分工完成。源码审阅与 compact 证据复算相互补充，但这些分工不是外部独立认证，也不是 PR #127 所要求的正式 137 项源码复审。所有本地复算均为 CPU 操作；本轮没有启动新的 GPU、模型、native host、actor、RTL 或 CPU8 实验。

后续结论与论文设计 PR 仅新增研究文档，保持打开供审阅；没有将设计提案写成已完成的实验，也没有改写活动论文或公开 arXiv 版本。

## 1. 实际合并记录

仓库：[`leecdiang/HeteroSpec`](https://github.com/leecdiang/HeteroSpec)。本轮起始 main 为 [`9b8cdba784b34a5aa3e8981073223c451bbaaf54`](https://github.com/leecdiang/HeteroSpec/commit/9b8cdba784b34a5aa3e8981073223c451bbaaf54)。

| PR | 审阅与合并时锁定的 head | 合并操作 | GitHub 返回的 merge commit |
|---|---|---|---|
| [#128](https://github.com/leecdiang/HeteroSpec/pull/128) | `cf6c8bf43dc1ee4e9e8529bbe42300844e0165c9` | 先合并到 main | [`c9f018ff0ac5c8001deb36bcb062ff27408a673b`](https://github.com/leecdiang/HeteroSpec/commit/c9f018ff0ac5c8001deb36bcb062ff27408a673b) |
| [#129](https://github.com/leecdiang/HeteroSpec/pull/129) | `c541241ad62213a8d31006e539e4ce0623793040` | 将原来的 PR #128 分支 base 改为 main，核对后合并 | [`ec6b97518a2f230330d79f1b0ba2ca97bc70cd6a`](https://github.com/leecdiang/HeteroSpec/commit/ec6b97518a2f230330d79f1b0ba2ca97bc70cd6a) |

以上顺序保留 #128 → #129 的依赖。#129 调整 base 的目的是将已审阅的增量合并到 main；没有将其直接合入仍然独立的历史实验分支。合并请求使用已审阅的 head SHA，避免未经检查的后来提交混入此次操作。

作者在 2026-10-20 本次请求中明确要求“完成仓库以及最新 PR 的分析以及合并”。这一当前授权覆盖两条 PR 先前的 Draft / no-merge 文字；旧文字继续作为历史状态保留，不被解释成永久阻止作者新决定的规则。合并范围由具体审阅结论决定，没有因此批量合并所有旧草稿。

### 合并前的 GitHub 状态

主 assistant 通过 GitHub 插件核对：两条最新 head 的 checks、commit statuses、PR reviews 与 review threads 均为空；当时 main 未受分支保护。这表示这些 head **没有可报告的 CI 检查结果或 GitHub review 门槛**，不能称为“CI 全绿”或“外部审核通过”。合并依据是本轮记录的源码检查、证据复算与作者授权。

| 变更范围 | PR #128 | PR #129 |
|---|---:|---:|
| 新增文件 | 56 | 20 |
| 修改 / 删除已有活动文件 | 0 / 0 | 0 / 0 |
| 所在子树 | `benchmarks/b570_qb_batch_broadcast_v1/` | `benchmarks/b570_model_request_bridge_v1/` |
| backend 交付形式 | admission patch、实验程序和证据 | logger patch、源码快照、实验程序和证据 |

因此，合并并未把两个 patch 自动安装为仓库的活动 backend，也没有替换模型、DLL、shader 或论文。完整文件列表与审阅范围分别可在 [PR #128 的 Files changed](https://github.com/leecdiang/HeteroSpec/pull/128/files) 和 [PR #129 的 Files changed](https://github.com/leecdiang/HeteroSpec/pull/129/files) 核对。

## 2. PR #128：准入修复和两种成本窗口

### 已核对的源码事实

portable patch 为普通 `MUL_MAT` 的特定组合放行：连续 F16 A、F32 B、A 第四维为 1、B 第四维为 2 或 4、B 第二维为 1，并要求 A/B 第三维相等。源码路径支持这一区域所需的 batch broadcast；它没有建立一般 GQA 或所有 Vulkan QB 形状的准入结论。

从 PR #129 快照取得的 PR #128 candidate 源码完整 SHA256 与登记值 `c16de703ff610cb10d4f4b19b64a1f4bb2e36ad57047b1443b718725da939576` 相同。反向应用 portable patch 可以重建登记的 baseline SHA256 `04615c97998a76d2d0b15d2ebb93bf381eb3fb565492d7714d3fc9d1c333b98d`。固定的 `query_head.h` 依赖也与 manifest 哈希一致。147 个 shader object 沿用既有构建，不能称为新编译或完全自包含的跨机复现环境。

相关源码与实验定义见 [portable patch](https://github.com/leecdiang/HeteroSpec/blob/cf6c8bf43dc1ee4e9e8529bbe42300844e0165c9/benchmarks/b570_qb_batch_broadcast_v1/qb-batch-broadcast-portable.patch)、[transaction RESULT](https://github.com/leecdiang/HeteroSpec/blob/cf6c8bf43dc1ee4e9e8529bbe42300844e0165c9/benchmarks/b570_qb_batch_broadcast_v1/transaction_v1/RESULT.md)。

### 本轮完成的复算

并行 assistant 下载并解包 resident / transaction compact 数据，重新执行两个原有 `analyze.py`。与登记 JSON 相比，仅有两个浮点末位字段差异，最大绝对差 `1.1102230246251565e-16`；九个坐标与固定 panel 的决定全部维持 `UNRESOLVED`。

进一步核对了三次 transaction session 各自的 162 个成对 block 坐标、81 个成功资格 slot、15,633 次返回的 graph computation、正常清理，以及 compact transaction archive 中 17/17 项完整文件哈希。7,819 项 manifest 的 SHA256 与登记一致；resident 与 transaction 原机 CPU raw-check 记录中的 243 个 final witness 哈希对应一致。

| 固定等权 q2/q4 panel | Resident compact-Q graph | Common permuted-Q transaction |
|---|---:|---:|
| QH_C − 双 QB 对照，μs | −1.0277058 | −1.5180453 |
| 调整后的差值区间，μs | [−2.1765299, +0.0669518] | [−4.1677178, +0.9156414] |
| A/A 实用差异门槛，μs | 3.4447222 | 17.2838889 |
| 结论 | UNRESOLVED | UNRESOLVED |

两种窗口均没有建立超过该实验 A/A 噪声与实用门槛的 QH_C 优势。它们也没有证明两种映射严格等价、QB 普遍最优或其他真实请求上必然无收益。两种窗口改变了布局与成本范围，不能用两组绝对时间相减来推算一个独立的 transfer/packing 成本。数值来源见 [transaction ANALYSIS](https://github.com/leecdiang/HeteroSpec/blob/cf6c8bf43dc1ee4e9e8529bbe42300844e0165c9/benchmarks/b570_qb_batch_broadcast_v1/transaction_v1/ANALYSIS.json) 与 [paper integration](https://github.com/leecdiang/HeteroSpec/blob/cf6c8bf43dc1ee4e9e8529bbe42300844e0165c9/benchmarks/b570_qb_batch_broadcast_v1/transaction_v1/PAPER_INTEGRATION.md)。

### 原始数据边界

transaction 的 7,782 个 raw 文件、约 4.356 GB 数据仍留在原 Windows 主机。本轮验证 compact 数字、源码身份和记录之间的对应关系；没有取回或逐数组重新执行这些原始 tensor 的数值比较。引用上述 witness 一致时必须保持这一限定。

PR #128 当时的累计为 `53.7774511 / 300 s`。这是历史 head 的余额，#129 已继续计入费用，不得用 #128 的旧余额重新启动 launcher。

## 3. PR #129：真实请求范围与 logger 完整性

### 源码与证据复核

本轮独立工作目录中的 CPU 复算完成以下检查，结果记录于 [PR129_METADATA_REVIEW.json](reviews/PR129_METADATA_REVIEW.json)：

- compact ZIP 中 **122/122 个文件**的完整 bytes、大小和 SHA256 与 695 项 manifest 的对应条目匹配；manifest 自身 SHA256 为 `1edc027875c7e8ee14395650cb25794aef166d2770d0d15aef7ffad1b17c9fec`。
- 12 个 process receipts 连续计账；11 个成功进程、33 次重复请求、528 个 logits 元数据记录的 token、EOG、形状与登记哈希对应一致。
- 从保存的 stderr 重新解析三张最终上下文表，操作次数、各组时间与百分比均与登记分析相同。
- 对父源码仅作文本换行规范化后，`git apply --check` 通过；实际应用 logger patch 后与最终源码逐字一致。两个 Python 脚本 AST 解析通过。

logger 的两处改动是：补充最后一个时间区间的 terminal timestamp / graph-end index；按 executor 的空节点与 `COMPUTE` 判据过滤不活跃标签。旧 concurrent 表遗漏了最终输出投影；最终三张表各包含 16 次输出投影，并包含 QK、softmax、AV、CONT 各 5,004 次，即 `36 × (124 + 15)`，且没有 `n=0` matrix 标签。混合组仍作为整体统计。见 [logger patch](https://github.com/leecdiang/HeteroSpec/blob/c541241ad62213a8d31006e539e4ce0623793040/benchmarks/b570_model_request_bridge_v1/concurrent-logger.patch) 与 [ANALYSIS](https://github.com/leecdiang/HeteroSpec/blob/c541241ad62213a8d31006e539e4ce0623793040/benchmarks/b570_model_request_bridge_v1/ANALYSIS.json)。

### 科研结论的准确范围

本次模型请求为一个已暴露的 HumanEval/42 提示词：Qwen3-8B Q8_0，124 个 prompt tokens、16 个输出 tokens，36 层，Hq/Hkv=32/8，d=128，ubatch1。实际执行的 attention key extent 为 **256**、查询宽度为 **q1**；配置 context capacity=1024 不等于执行 key extent=1024。它与 #128 的 equal-head 8/8、key1023–1025、q2/q4 微图不同。

33 次请求来自这一提示词的重复和 observer 对照，不能算 33 个独立工作负载样本。528 份原始 `.f32` arrays 没有远端交付；本轮可读取的原始 tensor 文件为 **0**。本轮没有重新验证全部 logits 的实际 bytes，JSON 中明确记录 `raw_tensor_independent_validation=false`。原机的完整 byte-equality 结论以原机记录和哈希声明的身份保留。

最终同 DLL 的 clean/profile/clean 中位 decode 时间为 `27.6675 / 29.6058 / 27.6794 ms`，profile 相对两个 clean 分别增加 `7.0056926% / 6.9596884%`，通过不变的 ±10% 粗门槛。原串行 observer 约 12% 的开销拒绝结果被保留。每个中位数包含 15 个相关 decode 时间，这不是统计等价检验。

最终第三上下文的诊断 GPU subtotal 为 `3.490070 s`；QK/softmax/AV core 的占比边界为 `2.8004596%–2.8025652%`，量化 matvec / fused groups 为 `92.5152352%`。这些是有观测干扰的同步 GPU subtotal，不能作为自然请求关键路径占比代入 Amdahl 公式。core 没有包含 Q/K/V/O projections；量化组也不能全部归为 FFN，或仅凭名字判断带宽瓶颈。

这项结果支持结束当前已经测过的 attention-mapping 假设并保留基线，但没有排除其他长上下文、真实 speculative q2/q4 或 GQA 场景。它也没有建立新加速器的收益。完整范围与限制见 [RESULT](https://github.com/leecdiang/HeteroSpec/blob/c541241ad62213a8d31006e539e4ce0623793040/benchmarks/b570_model_request_bridge_v1/RESULT.md) 和 [PAPER_ADDENDUM](https://github.com/leecdiang/HeteroSpec/blob/c541241ad62213a8d31006e539e4ce0623793040/benchmarks/b570_model_request_bridge_v1/PAPER_ADDENDUM.md)。

### 累计预算

起始累计 `53.7774511 s`，#129 全部阶段新增 `193.0268920 s`，最终累计 **`246.8043431 / 300 s`**，余额 **`53.1956569 s`**。其中包含 `0.1694517 s` 的失败入口；所有失败、observer 拒绝和历史变体继续保存。旧 launcher 的初始余额是历史记录，不是再次执行的预算授权。

## 4. 没有合并的分支与不能替代的资格

### PR #127：源码 CI 与正式准入不同

PR #127 的候选仍为 `a793303c967567b6e07233596db8711eeb6a0a44`。本轮核对到 [源码 CI run 39373738635](https://github.com/leecdiang/HeteroSpec/actions/runs/39373738635) 成功、105 项测试通过，但其当前状态仍为 **`SOURCE_BLOCKED`**。本轮没有声称完成正式的 137 项完整源码复审，没有生成或继承 F0，也没有把 CPU8 从 **0/8** 改为已准入。

#128/#129 是各自已有授权范围的实验分支；合并其记录不能追认 #127 正式流程已经完成。#127 与相关旧 B570 草稿继续保留。

### PR #102：公开 v3 与旧准备稿不能直接同步

本轮没有合并 [PR #102](https://github.com/leecdiang/HeteroSpec/pull/102)。它是旧的 23 页准备稿，与当前公开 [arXiv v3](https://arxiv.org/abs/2610.03228v3) 的 17 页版本不同，且包含 license 改动。将它作为“最新公开版本”直接合并会混淆论文基线与许可变更；本轮未进行相应同步。

### 其他历史草稿

本轮对其他历史 PR 做进展与依赖核对，不等于重新完整审阅其全部源码。保留这些草稿既不表示每条都有 bug，也不表示每条已经通过合并审阅。各自的失败、停止原因、UUID、预算、原始输出和未启动项继续有效，没有因本次两条新证据 PR 合并而重置。

## 5. 可审阅的最终状态

- main 已包含 #128 的范围受限准入/成本记录，以及 #129 的真实请求范围检查与 logger 修复记录；对应终点是 `ec6b97518a2f230330d79f1b0ba2ca97bc70cd6a`。
- 两条合并均基于固定 head 与本轮实际可取得的证据；没有不存在的 CI 绿灯、外部认证或完整 raw-array 复验声明。
- 论文主线和后续实验方案在新的文档 PR 中供讨论；既有 arXiv v3、活动论文、原机运行状态、历史资格与预算不因该设计 PR 自动更新。

本记录应与同目录的研究结论和实验设计一起阅读：**合并的是已有证据及明确范围的实现记录，待做实验与论文更新仍由其自己的计划和准入条件界定。**
