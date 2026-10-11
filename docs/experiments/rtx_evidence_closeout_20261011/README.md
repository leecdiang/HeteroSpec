# RTX 最终证据补全方案

**执行入口：用户说“完成 PR89”即按 [EXECUTION_PROMPT.md](EXECUTION_PROMPT.md) 在本平台实现、运行、复算并创建独立结果 Draft PR。请读取最新 HEAD 和 [FINAL_REVIEW.md](FINAL_REVIEW.md)，不要只审查或合并设计。**

本PR给出最新#84正式结果之后的最后证据计划及CPU复算。GPU/trace/native新实验尚未执行。

入口：[整体判断](ASSESSMENT.md)、[主张与证据](CLAIM_EVIDENCE.md)、[执行协议](PROTOCOL.md)、[工作量与盈亏模型](MECHANISM_PROTOCOL.md)、[执行端交接](EXECUTION_PROMPT.md)、[机器设计](DESIGN.json)、[资产](ASSETS.json)、[源码绑定](SOURCE_BINDINGS.json)、[最小排除](MINIMUM_EXCLUSIONS.json)、[现有证据CPU复算](EVIDENCE_AUDIT.json)、[记录接口](RECORD_SCHEMA.md)、[CPU验证](CPU_VALIDATION.json)。

接在 RTX #84 的实际结果分支上。保留三家族和k3，补同UB普通M0、预定网格R_prod及收益归因；正式五条件、五轮、两会话。

所有旧结果与冻结、论文和release保持原有状态。结果必须新建独立目录/账本和Draft PR；设计准备阶段未启动GPU；执行端已获授权在协议范围运行，设计PR不合并，不预先宣称新加速。代码位于scripts/platform/rtx_evidence_closeout_v1，仅CPU plan/select/analyse及审计。

CPU验证命令：
```bash
python scripts/platform/rtx_evidence_closeout_v1/closeout.py --design docs/experiments/rtx_evidence_closeout_20261011/DESIGN.json validate
python -m unittest discover -s scripts/platform/rtx_evidence_closeout_v1 -p 'test_*.py'
python scripts/platform/rtx_evidence_closeout_v1/audit_previous.py --root . --platform RTX --out <scratch_audit.json>
```

静态PASS只代表设计/CPU边界检查通过，不代表native编译、原始档案再验证或物理驻留证明。


本次扩展明确检验Acceptance、实际draft/target work、长度/停止分布与冻结成本模型。模型失败也是结果；历史Qwen1.035与新1.106不构成实现优化A/B。

工作量工具：mechanism.py calibrate / analyse；必须保留真实校准/原始证据并事前封存。它不实现native计数hook或GPU timer，CPU测试不证明计时正确。

已有数据再分析：[原生计数/长度](PRIOR_WORKLOAD_AUDIT.md)、[机器复算](PRIOR_WORKLOAD_AUDIT.json)。
