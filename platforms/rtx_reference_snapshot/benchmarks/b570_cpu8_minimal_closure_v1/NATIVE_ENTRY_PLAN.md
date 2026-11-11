# B：最小原生入口方案（只做设计，尚未运行）

前置条件：A 在完整 119 文件组合及新的任务映射上取得真正完整、预算合格的独立 SOURCE_REVIEW_PASS。当前不满足，也没有 B 的执行授权。

## 收窄启动链

源码审查服务留在 A；B/C 的工作负载树不运行 Codex，不启动 CUA/REPL、插件发现、reviewer 或 debug 辅助读取进程。所选工作负载入口是固定 Python 解释器和现有 guard/observe/watchdog；保留产生原生身份和 DLL 事件的 DEBUG_PROCESS。`--ignore-user-config` 不进入准入假设，也不靠插件配置引号来证明服务消失。

期望树（仅源代码推导，P 仍 UNKNOWN）：

```
平台现有执行提供方 [成本/OS 覆盖 UNKNOWN，必须先解决]
  已登记的单个 PowerShell 请求包装 [必须被硬边界覆盖或有独立上界]
    Python operation_guard
      Python outer_watchdog
        Python cpu8_supervisor
          Python observe [DEBUG_PROCESS]
            Python bridge
              PowerShell launch.ps1 [同进程加载已有 C# DLL]
                Python controller
                  规定的 CPU injector/producer
```

不能删除功能必需的 PowerShell/C# launcher 来减少一个数字，它承担原 detector、pending I/O 与资源监督。若平台已有原生 argv 执行 API，可以消除最外层 shell，但必须原样捕获 request/session/terminal 并单独适配 `guarded_request`；当前源码仅支持显式 PowerShell 请求，不能声称已实现无 shell 提供方。

挂起子进程采用源码候选的 NO_WINDOW 标志，清楚记录标准句柄和实际 flags。不使用 DETACHED_PROCESS/NEW_CONSOLE/BREAKAWAY 叠加。所有必需后代仍逐个证明 Job 成员身份；若系统自行增加 console/helper，同样计入而非忽略。Debug CREATE 事件、Job 原生 census/累计 starts、保留句柄退出三者须一致，不能以采样漏掉短命进程来降低账目。

## 候选 CLI：用于逐项审查，当前不得执行

以下为 argv 数组，`${ROOT}`/`${UUID}`/`${HASH}` 是未赋值的设计参数，不是一个可复制运行的已批准命令：

```
[PINNED_PYTHON, "-I", "-S", "-B", "${ROOT}/source/operation_guard.py",
 "--intent", "${ROOT}/tools/${OP}.operation.json", "--intent-sha256", "${HASH}"]
```

guard 的 prospective intent 内只允许预先审查的 workload argv。正式 C 入口仍为：

```
[PINNED_PYTHON, "-I", "-S", "-B", "${ROOT}/source/outer_watchdog.py",
 "--root", "${ROOT}", "--run", "formal/${UUID}", "--mode", "cpu8",
 "--phase-limit", "${DERIVED_SECONDS}", "--freeze-sha256", "${F0_HASH}",
 "--supervisor-script", "${ROOT}/source/cpu8_supervisor.py"]
```

现有 `tool_binding.py` 固定 1120/1125 秒与 cap10；现有 guard 仍固定加二估价；现有 freeze/gate 生成器绑定旧操作编号。最终 A 需要用实际选定树的明示映射与边界替换这些字段，再重新审查和固定完整组合。上述数组是契约草案，不能调用旧生成器来“填好”它们。

## 前置硬边界与四行验证

在第一个 native 创建前，平台必须提供执行提供方/包装根可强制的启动数、并发、墙钟及清理上界，并保存机制和读回。Job ActiveProcessLimit 可作为一层机制，但单独不足以证明 039 反例下的聚合界；若无法覆盖外层，须有独立有限 U 和 starts 上界，否则连 B 的首行也不得启动。不得先运行无边界探索，再把观察到的最大值当作预约依据。

| 固定项（各一次；无正式槽位） | 必须证明 | 失败即停 |
|---|---|---|
| B01 正常最小启动/退出 | 原生根和全部后代 PID+创建/退出，debug/Job/累计 starts 对账，无额外服务；实际终态与字节 | 不在预测受控树内的成员、身份/退出缺失 |
| B02 cap 负例 | 在已批准硬边界下尝试一个超额创建；在创建/准入时拒绝，原生错误和所有既有成员清理 | 先成功创建到超限再由 Python 发现，不算通过 |
| B03 timeout | 精确单调截止、实际 TerminateJobObject、全部退出 FILETIME、原生 Job 空 | 超时后任一存活或未知退出 |
| B04 强制清理 | 控制点后模拟拥有者/命令异常，独立所有者仍完成有界 cleanup，最后退出由外侧真实观测 | receipt 自证退出、残留成员、外侧生命周期缺口 |

这些行将启动 CPU 原生帮助进程；当前没有执行权限。B 自身需要预先可强制的保守 envelope，B 的测量只可用于后续 C 校准，不能给 B 自身追认预算。

每行前瞻登记 `P,T,L,U,E,starts,storage,capture/export`；预留完整矩阵及收尾。执行时保存 exact argv/flags、机器/OS、解释器与 DLL identity、原生限制设置/读回、真实 request/response/session/terminal、原始日志、三个视角的身份清单、所有句柄关闭和外层最终退出。stable provider ID 未公开则 UNKNOWN，不用 chunk ID 替代。B 的最高结果是 ENTRY_ADMITTED，不计任何 CPU8 PASS。

## 不扩展的范围

不解释所有 Windows 控制台豁免机理，不为通用 reviewer 树制造更多 observer 嵌套，不重复完整旧 19/57 项或三小时 soak。仍须保留已有 native gates（原入口导入、observer/身份/断点/冻结/停滞/D0）到新的明确 gate mapping，不能用这四行替代原 CPU8 内层资格。只运行 A 最终 gate mapping 明确要求、且另获授权的项目。

## Post-A native qualification details (prospective only)

**Pre-execution source contract is now different from native proof.** The guard tracks the `CreateProcessW(CREATE_SUSPENDED)` root handle and a separately acknowledged `AssignProcessToJobObject` outcome. If assignment fails, it requests direct `TerminateProcess` on that exact retained root process, then waits for real exit FILETIME and closes the thread/process handles; `TerminateJobObject` alone is NOT enough. Before accepting B, price and execute one bounded B00 fault-injected assignment-failure cleanup negative with an outside-owner exit witness, including a deliberately failed direct-termination/exit-query counterexample. This B00 negative has nonzero starts, wall, storage and provider reserve; the old B01–B04 1200-process-second target DOES NOT cover it automatically.

B02/B03/B04 use frozen success/failure-specific contracts, not a generic allow-failure flag. B's outside owner must authenticate exact guard PowerShell request/terminal, true guard PID+creation+native parent, child image/argv/parent PID+creation and the outside owner's own distinct identity; the candidate witness JSON itself is only consistency evidence, not external authenticity. Count every short-lived Job start independently of 100ms polling; native cumulative starts that cannot be matched to preserved identities remain ENTRY_BLOCKED.

C's post-F0 runtime operation is materialized only after A/B approval and a separately authorized C freeze. Its actual bytes must equal the F0-pinned pre-freeze template with exactly one F0-hash substitution. B01–B04 and C remain **NOT_RUN** under this design.

## Fixed B00 assignment-failure qualification — prospective addition, not executed

**A source-only prerequisite.** The guard's `except` branch only calls `TerminateJobObject` after acknowledged `AssignProcessToJobObject` success. If the Job assignment fails, the retained `CREATE_SUSPENDED` root must instead be terminated through its own live process handle in `finally`, followed by an actual wait, exit FILETIME and handle-close witness. Independent outside-owner failure cleanup remains required when the guard itself cannot complete. Source-only checks of this routing do not certify native behavior.

Before separately authorizing any B entry launch, quote **both** fixed B00 controls independently:

| Control | Frozen trigger | Mandatory evidence | Fail/stop |
| --- | --- | --- | --- |
| B00a | Intentionally deny root-to-Job assignment after suspended creation, without resuming the child | Exact root PID/creation identity, Job assignment OS failure, direct TerminateProcess request and actual process exit FILETIME, Job accounting 0, external owner terminal and handle closure | Job-only termination, resumed unassigned root, no native exit/cleanup |
| B00b | Inject direct-termination or wait failure in an outer-owned bounded negative fixture | Failure classified and retained, independent outside owner performs mandatory final cleanup and proves no live root; negative must NOT be promoted to ENTRY_ADMITTED | Child survives, missing external cleanup authority or unknown cost |

**Per-operation quotation, not a new price assumption:** `E_B00k = ceil(P_k * (T_k + L_k) + U_k)` with separately justified starts, disk/export, exit/cleanup and service overhead. The previous B01–B04 1200-process-second target excluded B00; therefore **do not add B00 and keep the old B budget unchanged**. If provider/outer root hard bounds or price U remain UNKNOWN, do not run even B00a. Execute once per authorized fixed control, preserve failures and stop at first unqualified outcome. B00 is engineering entry qualification, never a formal CPU8 case or B570 scientific result.
