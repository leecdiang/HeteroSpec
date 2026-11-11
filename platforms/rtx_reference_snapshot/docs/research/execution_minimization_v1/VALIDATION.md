# CPU 验证与执行状态

本 PR 在源 main `e87291d26df32f2cb9571e005ab173b1c7a6830b` 的同内容树上进行只读分析。原工作树 HEAD `7a464b00097f983a439e8d8c018fb918147624a1` 的完整 Git tree 与 main 同为 `a7b3edfb0e02a111ae08412edec7638392fa6d2c`。九个源文件以 immutable Git blob SHA、SHA256、字节数绑定。

在拥有对应Git对象的仓库根目录运行：

```powershell
python -B scripts/analysis/execution_minimization_v1/audit.py
python -B scripts/analysis/execution_minimization_v1/test_audit.py
```

`audit.py` 只读取源绑定的 Git blobs，生成本新增研究目录的 EVIDENCE_TABLE、TASK_CASES、AUDIT_RESULTS。它不读模型，不修改源blob、论文或历史报告。可以用 `--repo` 指定Git仓库，`--out` 和 `--bindings` 指定新增目录/绑定文件。

完成检查：

- 三个上下文的1005继承记录分别为285、360、360；任务单位分别19、24、24；保持每任务三次稳定观察和独立的cohort合同。
- 全部task/condition/repetition键恰好覆盖规定矩阵；inclusive EOG/cap128、完整长度/理由/terminal ID通过检查。
- ordinary U2未测上下文保留UNKNOWN与72单元分母，不插值或复制其他条件。
- 输出与参考效果、初始state见证和因果未知字段保持分离。
- 七项有意义的风险测试：重复记录、缺失重复、重复不等于独立任务、相同停止理由掩盖长度变化、UNKNOWN分母、错误端点/重复JSON字段、绑定源损坏拒绝。
- 相同输入重算的三项输出逐字节一致。

发布时使用完整 source base tree 增加本目录和新分析脚本；只允许新增文件。PR比较需确认没有论文/继承路径修改，完整根树需保留所有非docs/scripts条目，docs/scripts的原有子树需完整保留。

零新增模型运行、GPU forwards、模型下载和付费计算。阶段A/B/C、迁移与成本检验均未执行。新CPU分析不独立认证既有机器执行、绝对时间、 omitted weights/binaries或完整raw archive；既有资格和档案审计仍是继承证据。
