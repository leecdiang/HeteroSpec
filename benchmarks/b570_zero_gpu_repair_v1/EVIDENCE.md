# 验收证据契约

## 原始证据要求

每个 case 保留固定代码/配置/环境哈希、槽位注册状态及转换、原始 watcher buffer 和逐条 decision、三条监督时间序列、注入器操作回执与副作用（写入内容/文件前后哈希/FRAME与ACK等）、子进程握手与 GO、stdout/stderr、完整进程树台账、清理回执。接收单调时钟属于同一宿主；墙钟仅定位，不与单调时钟互减。

使用 typed reason code；字符串搜索、`FAILED` 或“有一条 rejected notification”不能证明命中预定故障。注入操作区间与 detector 匹配同一 fault ID、目标对象和槽位。以 path 判断时使用规范化路径和实际文件身份，覆盖大小写/别名；不能只凭 basename。事件序号、hash manifest、独立副作用使规范化回执可追溯，但不是防恶意伪造的密码学保证。

外层进程台账至少包含 task/run/case/role、PID、创建时间、父身份、命令或命令哈希、单调 launch/exit-observed、OS创建/退出时间、退出码、终止原因、子树结束、stdout/stderr路径；失败启动与未启动分开。长期外层控制器按整个寿命计一次；不要每case重复收费。独立审计检查未知/未闭合进程、预算、时钟缺口、错误路径拒绝及完整矩阵。

## 规范化回执与工具边界

`check_receipts.py RECEIPTS.json` 要求全部3轮、固定顺序、每case恰好一次、同一freeze哈希。它拒绝无触发、错误拒绝原因、路径不符、提前失败及证据链接缺失，输出 PASS/NOT_REACHED/WRONG_FAILURE/EVIDENCE_MISSING。

回执结构见测试中的构造器。字段 `evidence` 是 raw 相对路径与 SHA256 的引用字典；`verified` 是**独立 raw auditor**完成对应检查后填入的布尔值。工具本身不访问 Windows、不读取raw、不验证这些布尔值的真实性，也不发放 ENGINEERING_READY。host 需实现并审查 raw auditor：重建每个字段、检查SHA/副作用/顺序，拒绝手工声明替代证据。不得用测试构造器生成真实结果。

必需证据键：fixture、lifecycle、cleanup、watch、coverage；负例额外 injection、detector；每个检查项有 raw 引用。`early_failure` 不能被最终正确错误码覆盖。若指定故障根本未发生，NOT_REACHED；发生但拒绝原因/对象不符，WRONG_FAILURE；缺完整证据则 EVIDENCE_MISSING。

每个正例额外 raw 审计正常工作、监督持续覆盖。normal_transition 需8对转换全部检查，normal_late_panel 需8000文件、活动扫描边界及历史保护。负例注入造成的预期监督缺口不应冒充正常覆盖通过：`coverage_checked` 表示 raw auditor 证明该缺口触发正确拒绝和停止；其他无关缺口仍失败。

## 总体验收（不是单一脚本返回码）

全部19 case ×3轮=57个case回执，正常转换另含48个唯一槽位；确认开发计数分开。三轮源代码/工具链/冻结一致。真实受控故障仍保留原始FAILED状态，case PASS只是验收该控制有效。

除了57项PASS，还必须具备：
1. 实际实现独立审查最终结论与最终代码覆盖；无未处置的实质缺陷。
2. 可独立重算的三条监督流、完整任务子进程台账与预算，禁用项计数均0。
3. 前瞻冻结与远端认证，无已开始确认项重试。
4. 完整远端下载/全新恢复/逐成员哈希/包内未修改auditor重算一致。
5. PR115 head、Draft、结论保持原样；论文与其他目录无diff。

交付 `RESULT.md`、`ENGINEERING_EVIDENCE.md`（明确无论文数值/成本证据）、`DESIGN_DECISION.md`、`REVIEW_STATUS.json`、`CONFIRMATION_FREEZE.json`（若已准入）、`RECEIPTS.json`、`RAW_AUDIT.json`、`PROCESS_LEDGER`、`BUDGET_ACTUAL.json`、`RAW_MANIFEST.json`、归档与 `REMOTE_RESTORE.json`。未准入项不能伪造对应文件/哈希；使用状态表说明缺失。封存未闭环、计账或review缺失均 BLOCKED，归档恢复成功不能补齐。
