# B570 最终证据补全方案

本PR给出最新#84正式结果之后的最后证据计划及CPU复算。GPU/trace/native新实验尚未执行。

入口：[整体判断](ASSESSMENT.md)、[主张与证据](CLAIM_EVIDENCE.md)、[执行协议](PROTOCOL.md)、[执行端交接](EXECUTION_PROMPT.md)、[机器设计](DESIGN.json)、[资产](ASSETS.json)、[源码绑定](SOURCE_BINDINGS.json)、[最小排除](MINIMUM_EXCLUSIONS.json)、[现有证据CPU复算](EVIDENCE_AUDIT.json)、[记录接口](RECORD_SCHEMA.md)、[CPU验证](CPU_VALIDATION.json)。

接在 B570 #88 实际结果分支上。固定Q6/Q4 k1，先有界补物理驻留观测，准入后完成五条件正式成本；准入失败亦作为最终证据收尾。

所有旧结果与冻结、论文和release保持原有状态。结果必须新建独立目录/账本和Draft PR；该设计PR不合并、不启动GPU、不宣称新加速。代码位于scripts/platform/b570_evidence_closeout_v1，仅CPU plan/select/analyse及审计。

CPU验证命令：
```bash
python scripts/platform/b570_evidence_closeout_v1/closeout.py --design docs/experiments/b570_evidence_closeout_20261011/DESIGN.json validate
python -m unittest discover -s scripts/platform/b570_evidence_closeout_v1 -p 'test_*.py'
python scripts/platform/b570_evidence_closeout_v1/audit_previous.py --root . --platform B570 --out <scratch_audit.json>
```

静态PASS只代表设计/CPU边界检查通过，不代表native编译、原始档案再验证或物理驻留证明。

