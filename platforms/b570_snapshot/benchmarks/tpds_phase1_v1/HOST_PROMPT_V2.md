# 原机增量交接 v2

继续当前 PR 的原机适配，先读 `REVIEW_V2.md` 并检查本机是否已有正式
freeze 或 timing 槽位。已冻结/开始的面板保持旧 commit、臂和计时口径；
本修复另建版本与输出目录，不中途拼接。原始 R 与历史记录不变。

**RTX #192：**新 R2 冻结前审查 W_L4/W_P/L_L4/L_P，覆盖全部合法不等价
的 target-only 组合（最多四个），保留 matched M 与 D4。遗漏混合臂须有
同参考、源码、真实 trace 和开销路径等价证明，或明确原生不适用证据；
不能依据测试集速度删臂。使用 baseline-review v2 生成 4–6 臂、四轮的
请求串并报告所有固定 M 对照。R1/R2 独立推进，不等待 B570。

**B570 #193：**先完成真实 C4096 context/KV/scheduler/output 分配及原 R
桥接，核实 clean observer 全调用链。结构计时必须是已准备有效状态后的
native append_ms，包含 phase bind/sync/请求输出复制，不回填 prefill 或
完整 service。q32 保持 last-only，actual observer counters 不能默认填0。
C4096 真正受限时保留记录并继续 C1024/干净构建，不等待 RTX。

**双方共同：**先保存完整 compiler transitive dependencies、头/生成文件、
配置/response files、编译链接 argv、工具与库及实际加载模块，在资格后、
正式 timing 前冻结并复查。未测 draft phase 为 null；部分覆盖只报告
observed_sum 与覆盖数。正常编译、路径、ABI、源码定位和 observer 适配
自主修复并重新资格，不停在工具测试。复用现有 supervisor/ledger，不增加
通用审计框架，不降低安全余量，不租卡、不合并、不改论文。完成适用分支
后提交独立结果 PR，区分旧版本、新资格、干净 timing 与只读重算。
