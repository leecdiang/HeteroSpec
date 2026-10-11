# RTX 执行端交接提示词

在真实RTX 5070 Ti Laptop主机完成本设计，创建独立结果Draft PR；以本补全PR实际HEAD为执行来源，不回退到旧稿或覆盖#84。先读取README、ASSESSMENT、PROTOCOL、DESIGN、ASSETS、SOURCE_BINDINGS、MINIMUM_EXCLUSIONS、EVIDENCE_AUDIT和CPU_VALIDATION。此PR只提供CPU规划/复算工具，没有声称native已编译或开始GPU。

1. 实读当前HEAD及所有Git blob并记录bytes/hash，恢复#84完整作者源码/EXE/数值DLL，重新核验ASSETS。独立新study目录和single-writer ledger，源码/runtime身份全部绑定。新实现不得修改旧冻结runner。
2. 按协议实现controller adapter，将actual model/condition/phase/原生全输出/cap/EOG/费用等填入RECORD_SCHEMA.md。修改#84控制器的硬编码排程仅能在新目录，保留其numeric路径。
3. 完成全历史审计与12曝光工程题，封存/发布/实际remote读回F0A后才forward。每家族360 paid工程上限。用完整ordinary网格选择R_prod，不使用任何confirmation速度。
4. 以MINIMUM_EXCLUSIONS加完整历史排除、偶数description桶准备新24题；输入格式沿用#84的tasks/families字段并补history_audit。每题保留完整description、prompt与native IDs。
5. 用closeout.py select-ordinary和schedule生成选择与五条件五轮排程，独立验证顺序/slot/budget；冻结共同F0B并读回remote bytes。
6. 建立单独本地无人值守控制器，按实际冻结排程运行全部三家族；无需Codex/OpenAI API轮询，不因Smol负收益删除或停止其合格确认。正式请求不自动retry；metadata有限I/O重试不得重发推理。结果先独立唯一落盘，监视器不得干扰写入。
7. 工程重型capture关闭后运行3750 formal/warm请求预算（3600+150）；全部实际启动计费。沿用冻结host准入，按16h生命周期/7天停止线结束。
8. 原生record adapter必须保留raw tokens与结束语义；只转换字段名，不裁剪输出。closeout.py analyse核对完整比较，独立raw verifier再核对CPU结果。生成中文结果与全部负例。
9. 实际本地恢复及认证Git科学档案恢复/字节读回，提交独立结果Draft PR并更新其状态。不能合并、发布或修改paper/release。

执行命令模板（不会启动GPU）：
```bash
python scripts/platform/rtx_evidence_closeout_v1/closeout.py --design docs/experiments/rtx_evidence_closeout_20261011/DESIGN.json validate
python scripts/platform/rtx_evidence_closeout_v1/closeout.py --design docs/experiments/rtx_evidence_closeout_20261011/DESIGN.json select-ordinary --rows <exposed_ordinary_rows.json> --out <selected_ordinary.json>
python scripts/platform/rtx_evidence_closeout_v1/closeout.py --design docs/experiments/rtx_evidence_closeout_20261011/DESIGN.json schedule --inputs <new_confirmation_inputs.json> --ordinary <selected_ordinary.json> --out <new_formal_plan.json>
```
遇到无法恢复源码、预算或资格阻断，完成可恢复停止报告；不得临时替换为新模型/更大k/更低精度来追正结果。

