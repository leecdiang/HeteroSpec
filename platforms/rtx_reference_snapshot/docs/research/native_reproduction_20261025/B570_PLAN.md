# B570 原生复现交付与最小验证

本轮把已通过的 Qwen GQA / AV-preserving Vulkan 路径交付成可从干净目录构建、运行和核对的材料。B570 不需要复制 RTX 的 resident/fresh 因子实验；只有发现 B570 自身尚未回答的部署差异，才另立受控比较。

协调基线：`main@805864b1e370c4d17defa58bed4fac43c1cfb75e`。本文件是执行方案，尚无本轮 GPU 实测结果。旧文档的 B570 “Closed” 属于旧 campaign，不是全平台禁令；保留旧 Llama Q6_K 失败试验与后续 Qwen Q8_0 成功移植的区别。

## 先使用现有结论

- PR134 已有 Qwen3-8B / 0.6B Q8_0、F16 KV、k=1、自然 EOG、最多 64 输出 token 的正式请求证据：HumanEval/38、65、115、127；自然 q2、32/8 GQA、36 层目标模型，PQ/QB 对齐 346 个完整 logits 向量和周期轨迹。其计时面板与后续 PR143 是不同实验，不混用比值。
- PR143 已完成全部 156 请求、9 个模型进程，包括 64 次测量与 64 次匹配 warmup。`SUBMIT/dual-BASE=0.999161301690`，A/A=0.3689%，未达到实际收益门槛，保留 QB/thread8。**不重跑该 prefill 负面实验，不再写“缺少完整 timing”。**
- PR143 的 helper 后代进程未完整计数，`fully_protocol_resource_compliant=false`。保留这一资源记账偏差；不得事后补造合规记录，也不把它改写成数值验证失败。

## 原生依赖与恢复入口

| 来源 | 固定身份与用途 |
| --- | --- |
| 当前 `src/query_layout` | CPU 地址/状态契约及原生源码摘录；不能单独冒充完整 runtime。 |
| PR131 admission | `b5370cab7ce853d4b284e42e5515ffa50f1e8ce7`；恢复 `benchmarks/b570_gqa_admission_v1/` 的源码和前置 admission 修改，并带上 `benchmarks/b570_query_head_lowering_v1/native/query_head.h`。该候选本身在 key512/q2 的 AV 精确比较失败。 |
| PR132 AV-preserving | `7e98e288b4137c998604a0809c7e956474967de1`；`benchmarks/b570_gqa_av_preserve_v1/` 的源码快照、构建清单、`av-preserve.patch` 与真实 stage 输入/回读。它承接 PR131，不是任意最新版 llama.cpp 上的独立补丁。 |
| Request bridge | `34787ab56f0ae8b533d18fe02db2d37e8ebb63a4`；`benchmarks/b570_spec_request_bridge_v1/` 的源码快照、`runtime-integration.patch`、`spec_bridge.cpp`、模型与输入身份。 |
| PR134 正式服务 | `51febaddcf49bb18565e568cf964a6e5c78876c9`；`benchmarks/b570_formal_request_v1/` 的请求协议与参考结果。 |
| PR143 已完成 closeout | 原结果 `60b7d6a9301557c9a26c7d89acbe1b9d122bb53d`；当前 main 的 `docs/experiments/b570_prefill_closeout_v1/CLOSEOUT.md` 与 `reports/b570/prefill_closeout_review_v1/`。 |

先在 B570 主机恢复这些本地归档，核对 manifest，再获取确实缺失的文件。历史路径 `C:/hs/llama-b10839`、`C:/hs/b570-direct-id-v1-build` 只作查找线索。PR132 构建清单依赖既存 shader 对象目录；交付时必须提供这些对象的可追溯构建输入和生成命令，不能保留隐式依赖。`query_head.h` 的历史 SHA256 为 `2cf9dbc2efe7dcb6d9e4b122ed6b5040ca7d908ed6aacb1e569777ad5c340785`；AV patch 为 `0032fd2b65d98f3274d1ee121d0179b1ac9581c10537655f6f1d354d3e3a7d4e`。以完整源码清单确定真正的上游 commit，不把目录名当版本证明。

## 执行顺序

1. **资产与只读审计。** 记录 GPU、驱动、Vulkan SDK、编译器、CMake、上游/补丁 commit、模型 hash、数值 DLL hash 和路径映射。运行当前 CPU 契约检查。复核 PR143 时使用 `read_only_audit.py`，指定新的输出文件；旧 `audit.py` 会改写派生文件，旧 `verify_delivery.py` 也会写入记录的 worktree，不作为只读入口。缺少某份历史归档只阻塞对应历史复核，继续源码整理、构建和其他已具备资产的任务。

   ```powershell
   python -B reports/b570/prefill_closeout_review_v1/read_only_audit.py --repo . --native-root C:/hs/b570-prefill-closeout-20261021 --out C:/hs/b570-native-handoff-audit-new.json
   ```

   按实际路径调整参数，输出路径必须未存在。该命令不发起模型推理。

2. **最小可构建交付。** 在独立目录整理上游身份、完整补丁依赖顺序、`query_head.h`、shader 生成步骤、原生 stage 驱动、请求驱动、依赖清单和构建命令。干净构建不得读取未列入清单的旧 build 产物。把历史二进制复核与重新编译验证分列；工具链变化产生新的 runtime 身份，不能宣称同一历史二进制已复现。

3. **真实 fixture。** 从归档提取至少一组已通过的自然 q2 GQA fixture，包含 Q/K/V/mask 原始字节、形状、stride、span、key 容量、PQ/QB 选择及 QK→softmax→AV→最终输出参考。优先纳入 key512/q2，保留 q1 控制；声称覆盖 q4 或 key256 时一并交付对应参考。另给出完整请求 fixture：原始输入与 token IDs、模型身份、R/PQ/QB 配置、输出 token IDs、停止原因、完整同前缀 logits、接受/拒绝与状态轨迹。CPU 地址枚举、合成输入或只比较最终文本都不能替代这些材料。

4. **B570 原生 smoke。** 先回放 stage fixture，再以新构建跑 PR134 四个固定输入的 R/PQ/QB 请求，使用原协议的数值比较标准。建议先做一个输入，合格后完成其余三个；这是最多 12 个正式 smoke 请求的初始规模，不重复 64 次计时面板。逐层验证布局与 stage，核对全部参考 logits、输出、停止原因及状态轨迹，特别检查自然 q2 的 36 层目标调用。capture/普通运行存在不同构建或路径时，补一个对应控制并记账。若归档已缺失，先保留可运行路径和新捕获，再把历史对齐明确标为待完成；不得把新捕获当成旧参考。

5. **仅在存在新问题时补受控验证。** 干净构建 smoke 和有效 fresh-service 记录已经覆盖本轮交付时，结束 GPU 工作。若新构建/部署缺少有效 fresh-service 对照，先固定一个明确问题、同一模型/输入/线程/状态/计时边界和小规模配对表，再运行必要的 PQ/QB 控制。性能比较必须包含 A/A 和跨会话重复；单次 smoke 耗时只用于检查运行，不形成 speedup 结论。默认不扩展 CPU1/CPU8、prefill policy 或 resident/fresh 全因子面板。

## 执行弹性与完成标准

允许自主修复路径、依赖发现、编译脚本、日志和采集适配，并记录变更；数值算法、参考、模型、输入或比较边界发生变化时，分配新协议/runtime 身份并重新资格验证。数值失败停止该候选的性能解释，保留失败证据，继续不依赖它的交付任务。旧 CPU8 gate、过大的历史 wrapper、旧 campaign 的一次修复额度不作为本轮所有工作的总开关。

运行前依据实际空闲资源设定有限请求量、时限和磁盘预算，记录主进程及后代；无需套用已知失真的旧 helper 上限。保存每一步 checkpoint、失败/未完成槽位与重试身份，不覆盖结果、不静默补跑。遇到真实设备、权限或资源障碍就标明具体阻塞项，交付其余已完成内容。

结果 PR 应包含可从干净目录执行的 README/命令、源码与构建依赖清单、fixture 清单和可访问位置、hash、CPU/native/只读审计 receipts，以及逐项完成状态。大模型与大型 raw 包按仓库规则留在受控存储，Git 内保留获取说明和 hash。论文据此分别写清 CPU 契约、B570 原生回放、完整请求和历史性能证据；未完成的项目准确列出，不扩大失败或成功的适用范围。
