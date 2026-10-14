# HeteroSpec：主线重构与创新性增量审查

**研究决策稿｜2026-10-14｜只分析，不是论文正文。**

基线为 PR102 `8a93f3c`（v0.15.3）；证据截止 RTX PR104 `50e64c7` 与 B570 PR105 `a90bf85`。不读取或预测尚未发生的 RTX session 5，不把 E1 或 B570 v2 候选采集当成完成。完整提交与来源见 [SOURCE_LOCK.json](SOURCE_LOCK.json)。

## 决策

**保留 QB 作为实现核心；将论文的问题从“一个局部布局更快”提升为“保留既有部署参考时，局部执行几何修复何时足够、何时必须约束状态形成，以及它是否保留投机经济性”。**

这不是将 QB 改名成通用确定性系统。PR102 已经提出局部修复、参考契约和 Vulkan 边界；本次明确区分：已有方法、已经增加的证据、新的分析，以及仍需前瞻验证的可迁移性方案。不能把增加术语或重新画图当成新算法。

### 相对 PR102 的实质增量

| 层次 | 此次可推进的内容 | 当前证据状态 |
|---|---|---|
| 方法价值 | 让 PQ/QB 成为核心实现对照，以独立进程/时间块而非原两个相邻 session 检查小效应 | RTX 五个 session 已提交；最终聚合仍锁定 |
| 解释深度 | 从整份 KV cross 下沉到有限子集、共同前缀分数、实际 argmax，并消除 POSITION 坐标重复 | PR103/105 既有 raw 的再分析；不是新的 GPU 复现 |
| 系统结论 | 明确 repair organization × draft 的净收益方向；小扰动范数不足以单独解释固定面板的端点差异 | 前者是此前已有派生结论；后者是本轮报告值排序推导 |
| 普适性 | 给出与 GPU 名称分离的适用条件、完整状态边界和校准/未见输入验证路线 | 分析方案；尚无通用选择器或新后端成功结果 |
| 外部创新边界 | 新补 CoRun；核实 cache-induced divergence 论文已更新 v2 | 主源检索；未做外部系统性能复现 |

## 阅读入口

1. [RECONSTRUCTION.md](RECONSTRUCTION.md)：推荐主线、三条候选路线、相对基线的增量、章节/图表职责和反方审稿。
2. [GENERALIZATION.md](GENERALIZATION.md)：可迁移接口、条件性论证、状态形成与决策前沿、未来验证与结果分支。
3. [PRIOR_ART.md](PRIOR_ART.md)：按竞争维度比较近期主源，包含新增 CoRun 和 cache-paper v2；不以检索不到证明首次。
4. [EVIDENCE_LEDGER.csv](EVIDENCE_LEDGER.csv)：逐条结论的证据、状态、反例和下一步；[METHODS_AND_VALIDATION.md](METHODS_AND_VALIDATION.md) 记录六项 Skill 的实际使用与本轮边界。
5. [REANALYSIS.json](REANALYSIS.json)：CPU 重算结果；[reanalysis.py](reanalysis.py)、[test_reanalysis.py](test_reanalysis.py) 可独立运行。

```bash
# 从本目录运行；Python >=3.11，仅标准库，无网络/模型/GPU。
python -B -m unittest -v test_reanalysis
python -B reanalysis.py
# 可写到一个尚不存在的新文件；已有文件会拒绝覆盖。
python -B reanalysis.py --output /path/to/new-result.json
```

## 本 PR 不做什么

不修改 `paper/`、PR102、PR103/104/105、main、旧实验或原始档案；不启动 native 请求、operator replay、probe、warmup；不批准 B570 的新预算；不改变 RTX 的时间/停止规则；不创建或恢复自动化；不上传 arXiv/Zenodo。不撰写摘要、Introduction 或替换论文章节。

当前研究决策是：完成已有 E2/E1 与已经设计的 B570 前沿工作后，再决定是否追加“前瞻适用域验证”或“上游干预”。不是根据中途好坏结果改任务、阈值或对照。此前失败和负结果保留。
