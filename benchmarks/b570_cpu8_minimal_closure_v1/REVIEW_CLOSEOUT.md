# 源码审查与最小闭环交付：仍未准入

本次权限仅为源码审查、方案设计及 GitHub 修改。没有启动 B570、GPU、工作负载模型、actor、RTL、原生门槛或正式 CPU8；没有合并 PR。执行冻结 F0 不存在，正式八项仍为 0/8。

| 任务 | 本次产物 | 资格状态 |
|---|---|---|
| A | 六份源码覆盖文件、完整组合哈希、可读补丁、29 项源码反例检查 | `SOURCE_BLOCKED`：没有完整独立 scoped-clean，入口硬边界未证明，部署映射待修订 |
| B | 复用现有监督器的精简入口设计、固定原生验证矩阵、停止条件 | `ENTRY_BLOCKED / NOT_EXECUTED`，没有启动资格测试 |
| C | 八项顺序、detector、预算推导表和交付清单 | `NOT_AUTHORIZED / UNSTARTED`，只有条件方案 |

## 核对的不可变来源

- PR126 协议两份均完整阅读；两次提交为 `dba3677d5571800f04e83800e5b149cb381e83a6`、`faecb04484a0c45f7c55564ab50399243bca9b12`。本修订基于后者。
- PR125 head `c86ed78a8c6b8093205c34c1ab66b7f1bfcdc0ae`：RESULT、FOLLOWUP、JOB_CAP_DIAGNOSIS_REPORT、CLOSEOUT_SOURCE_MANIFEST、修复前后源码，以及原始 ZIP 中实际源码、037/039 的 argv、请求、终态、OS 与资源事件。
- PR119 head `aa7d64b5e4c198699a2f1fcc52c8ff2e31103fa7`：最终 RESULT、源码继承关系及 PR 历史正文。未重新执行其旧测试或原生审计器；旧 PASS 不转成新资格。
- 三个 PR 的讨论读取均返回空列表。没有把不存在的独立审查报告当成通过。

本地只读重建 PR125 的 36 个归档分块，逐块长度/SHA256、完整 ZIP 长度/SHA256 均核对。ZIP 为 6,958,084 字节、3,718 成员，SHA256 `f9ff6c8299847e11b2f8574b35225d3164bcb116bedb2fe1b246f3df5bb25a54`；封存清单的 3,717 数据成员均逐字节哈希核对，清单自身 SHA256 `558ac556d9dafa5c0cc2416a57c70c64bbc322a63fb684064979e0bbc6c7060e`。这是本次实际做过的静态输入核验，未执行包内原生代码，也没有声称重做旧的 Windows 接受或旧 48,742 字节报告重算。

PR125 声明的历史恢复成功、缺失的上传/下载返回、未知提交服务结果、未公开 provider 稳定调用 ID，以及发布尾部超出原 1,800 秒预测的 117.236 秒，全部继续保留。第二份交付 tar.xz 未在本次重新恢复；不把阅读旧回执写成新的独立恢复。

## 本次实际源码修复

文件位于 `source_candidate/`，仅在新的只读审查副本中覆盖相同相对路径。历史目录和归档不修改。

1. `source/verify_cpu8.py`：原根不论请求 live 或稳定 reconstruct，都先执行原生根身份、当前进程、当前存储和受保护预算检查；原根不得声称 relocated。真正搬迁根只允许显式 reconstruction，且绝无完整 PASS 权限。先检查原始路径再 resolve，保留别名拒绝。
2. `source/delivery_binding_v6.py`：将冻结操作哈希、固定允许的守卫请求格式、实际守卫命令与父子身份、顺序/时间、会话终态及提供方实际摘要输出关联。完整退出清单和 Job 总启动数必须一致，不能仅凭 Job 空或 receipt 布尔字段通过。分别核对孩子报告字节与守卫终态摘要；二者不是同一输出流。拒绝同时替换 intent 与捕获请求、孤立 exit0、缺失退出、错会话与非前瞻登记。`chunk_id` 改名为 `provider_chunk_ids`，稳定调用 ID 明示 `UNKNOWN_NOT_EXPOSED`。
3. `source/recompute_cpu8.py`：显式指定 reconstruct。该脚本只用于真实搬迁恢复根；原根稳定前缀使用 audit 的 reconstruct 且 relocated=False，仍须先过实时门槛。
4. `source/observe.py`：候选创建标志从 `0x0000000d` 改为 `0x08000005`，保留 DEBUG_PROCESS 与 CREATE_SUSPENDED，用 CREATE_NO_WINDOW 替换 DETACHED_PROCESS。
5. `src/rev2/win.py`：普通挂起子进程标志从 `0x0000000c` 改为 `0x08000004`。依然先挂起、分配 Job 再恢复。

6. `source/budget_v6.py`：修复负区间可减少累计收费的路径；结算前要求带时区、前瞻登记、单调捕获次序、稳定真实会话和整数终态。失败操作仍按向上取整区间收费。此修复不把原 cap+2 假设升级为硬资源证明。

第 4/5 项是待原生准入的源代码候选，不能据此声称额外 conhost 已消失。未去掉 DEBUG_PROCESS、未放宽 detector 或内层 100ms/1 秒规则，也没有把 cap4 改成 cap5。

Microsoft 的 [进程创建标志](https://learn.microsoft.com/en-us/windows/win32/procthread/process-creation-flags)说明 CREATE_NO_WINDOW 与 DETACHED_PROCESS 同时设置时前者会被忽略，因此这里是替换而非叠加。该文档不证明所选 B570 启动树的实际上界；[Job 文档](https://learn.microsoft.com/en-us/windows/win32/procthread/job-objects)也不能取代 039 的真实反例。

`SOURCE_COMPOSITION.json` 列出 119 个源码/导入组合文件及各自来源：113 个取自已核对的停止归档，6 个为新覆盖文件。另列历史配置和独立 compiled 引用。它不是 scoped-clean 清单或执行冻结。`SOURCE_DELTA.patch` 可逐项复审差异。

## 测试与仍然开放的发现

29 项测试在普通本地源码审查环境运行，所有进程/提供方夹具明确标为 SYNTHETIC，原生函数用拒绝/哨兵替代。未导入 Win32 执行模块、未执行原生入口、未启动任何 actor。完整组合中的 107 个 Python 文件仅做 AST 语法解析。这些结果只能证明相应源码判据，不能证明 Windows 行为或完整部署合格。

| 优先级 | 位置/证据 | 发现与处置 |
|---|---|---|
| P1 | 原 `verify_cpu8.py:10–29` | 原根 reconstruct 跳过实时限制。新覆盖文件关闭此路径；新资格仍未取得。 |
| P1 | 原 `delivery_binding_v6.py:35–61` | 声明请求、输出与闭合证据绑定不足。新覆盖文件加固；不能补造旧的缺失 provider 返回。 |
| P1，开放 | `operation_guard.py:13,18,61`、037/039 原始记录 | `(cap+2)*(T+5)` 未证明是启动树/外部服务的硬上界。后验检查与结算不能修复前瞻预约。未以新字段或伪证书掩盖。 |
| P2，开放 | `engineering_gates_v6.py:14,29`；`finalize_review_v6.py:12,23,31` | 固定旧操作 036/026/compile-v6-2/038-final-startup 等，不能原样作为新任务的部署与证据映射。须在 A 的最终完整组合中用明确、预先登记的新任务映射替换，并独立审查。 |
| P2，开放 | 037 的 134 文件清单 | 之后 budget_v6、operation_guard 又改过，旧清单不是当前最终候选。此次已重列 119 文件组合，但尚未完整独立复审。 |

更严格的绑定会拒绝部分旧夹具/旧 receipt。这是预期的资格收紧，不改写旧 raw、旧失败或旧结论；旧原始读取器仍在历史归档中。不能为了让新源码接受旧证据而去修改旧记录。

## 为什么没有启动一次“完整独立复审”

本协议明确要求在真正可强制的预算内完成一次完整审查，否则停止 A。本次现有连接器/审查服务没有提供可验证的 worker 数、完整服务寿命、硬截止和清理保证；原生机器上的该证明又未获当前权限。直接再起 Codex/CUA/REPL 或独立子代理不能解决这个缺口。因此没有启动新独立审查，也不生成 scoped-clean、SOURCE_REVIEW_PASS、ENTRY_ADMITTED 或 F0。

这是协议的预算停止条件，不是一次自动审批拒绝。当前源码设计工作本身不冒充受控的 B570 A campaign：没有编造其 OS 总账、精确起点、峰值或费用上界；本地 shell/读取/哈希/测试 helper 与连接器服务成本覆盖仍 UNKNOWN。`VALIDATION.json` 只记录实际源码检查和实际工具返回，不证明全任务资源帽。

## 历史预算与下一步

旧开发 3,613、余额 787、收尾 96、正式预留使用 0，均留在旧 UUID；不转入新任务。原 3,030 复审估计依赖已被推翻的 cap4。旧正式 13,600 也不是八个单项测量价。[预算与八项方案](CPU8_ACCEPTANCE_PLAN.md)给出可复审的推导，所有缺失 P/U/starts/storage 都保持 UNKNOWN，未生成“可执行总预算”。

最短推进顺序：完成一个真正受限的源码审查入口和明确的新任务映射 → 完整独立审查一次 → 获授权后只做 [四行原生入口矩阵](NATIVE_ENTRY_PLAN.md) → 由实际边界填满八项价格表 → 单独授权 C。没有新三小时 soak，没有为各工具服务再造一套通用证明框架。

长期科研顺序保持：参考语义约束 → 合格映射 → 强软件基线 → 完整成本边界 → 剩余硬件机会。CPU8 闭环本身不产生 B570 数值/性能或 RTL 价值结论。

## 2026-10-20 additive A2 scope split and source-candidate revision (not new qualification)

This section supersedes the **next-step recommendations** above, not the recorded b4cd53d3 source-only evidence, tests or failures. A remains `SOURCE_BLOCKED`; B remains `ENTRY_BLOCKED / NOT_EXECUTED`; C remains **formal 0/8 with no F0**.

- A is now prospectively separate from the Windows native reviewer Job. The reviewer-service internal PID/worker cost remains UNKNOWN and separately recorded, not zero or charged as invented Windows process-seconds. A's source-only finalizer checks exact full review coverage, byte drift, P0–P2 and reviewer attribution, but its maximum result is **SOURCE_REVIEW_EVIDENCE_CONSISTENT** until actual independent provenance is verified. No independent review has been run by this revision.
- In PR126 `source_candidate/`, 17 source overlays (13 replacements, four new helpers) make the 123-file source/import composition reviewable; includes newly staged original-v6 source and prospective replacements for `finalize_review_v6`, `integration_gates`, `native_gate_audit`, `engineering_gates_v6`, `tool_binding`, `operation_guard`, `budget_v6`, `freeze_cpu8`, `verify_cpu8` and frozen Python identity. Historical PR125 bytes are unchanged. `SOURCE_COMPOSITION.json` records per-file SHA256 and 12 auxiliary config/test/review input hashes. This is a proposed input inventory, not a completed deployed manifest or independent approval.
- The budget no longer assumes two unobserved root starts: explicit cumulative Job start allowance, outer owned starts and nonzero provider reserve must be quoted, with the native monotonic interval checked at settlement. This is a conservative arithmetic candidate, **not proof of B's hard provider boundary**. The actual 039 cap4→6 counterexample and UNKNOWN service lifetime remain binding negative evidence.
- Success delivery `invocation()` still requires exit 0/CLOSED. Separate `b_negative_binding_v7.py` requires a fixed B02/B03/B04 failure role, real provider exit, native detector and outside-owner cleanup witness. The source-only code is not yet qualified against real Windows event emission; special failure detectors and external capture authorization remain integration tasks.
- The prior 29 counterfactual checks belonged to `b4cd53d3`. New `tests/test_a2_contract.py` contains additional **synthetic** regression definitions but has **NOT BEEN RUN** in this GitHub-only revision. No new Python/Win32 runtime, compiler, helper, B570 GPU/model/actor/RTL or formal CPU8 was started.
- Canonical short handoff: [README.md](README.md), [A_SCOPE_V2.md](A_SCOPE_V2.md), [SOURCE_COMPOSITION.json](SOURCE_COMPOSITION.json), [PLATFORM_HANDOFF.md](PLATFORM_HANDOFF.md). Read `A_SCOPE_V2` before any earlier report-only prompt. Full source-only P0–P2 review, provider record authentication, B's pre-admission envelope, native B01–B04 and C's complete price remain **not done / unauthorized**.

Do not interpret this addendum, a hash-matched candidate, or passing future synthetic tests as SOURCE_REVIEW_PASS, ENTRY_ADMITTED, F0 or CPU8_INTEGRATION_PASS. PR remains Draft; old PR115/117/119/125, UUIDs, budgets and raw failures retain their terminal status.
