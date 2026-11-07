# v0.14.1 科学口径与全实验去向验收

本轮沿用 PR #71 的 v0.14.0（`c1f11267cdb4016c9b8ecf2514b0cec3ad7809dd`），不重新选题、不运行模型或硬件实验。新执行工作是保留源文件身份认证、已有导出数据的 CPU 复算，以及主文／补充／证据去向之间的编辑核对。原实验主机的私有 raw 审计仍是继承记录。

## 本轮实际执行的范围

1. 在 v0.14.1 目录执行 `scripts/reconstruct.py` 的 `compute()`：重新认证 **133 份** Git blob／SHA-256 绑定源副本，核对 **26 份** evidence 导出和 **16 份** historical 副本；结果保存于 `output/SCIENTIFIC_RECOMPUTATION_QA.json`。这一步不生成图、不修改 evidence、不打开历史 runtime。
2. 执行新增的 `scripts/audit_v0141.py`：不导入原 verifier，仅用 Python 标准库从 committed CSV／JSON 另行重建核心成本算术和全实验账本；结果为 `output/SCIENTIFIC_QA.json`。它还逐份比较上述 **42 份**导出／历史副本与本工作树保留的 v0.14.0 副本，并保存本轮实际核对文件的哈希。源码包中若没有旧稿相邻目录，则仍核对源绑定，报告相邻目录比较数量为 0，不能冒称再做了 42 份旧稿比较。
3. `scripts/build_ledgers.py` 重建 28 组实验的 Markdown／JSON 与 26 项主张 CSV；独立脚本逐字核对原规划账本的组名、事实、原去向与原来源路径。分类结果为 **9 组主文核心、12 组主文简述／补充详述、7 组补充边界／历史／复现**，无未分配项。分类不会改变样本分母、缺失状态或历史结果。
4. 独立通读摘要、主文各节、声明和补充的合同／实现／成本／条件推导，完成 **20 项**科学文字核对；`output/SCIENTIFIC_TEXT_REVIEW_QA.json` 保存所读 **22 份**稿件／映射／作者事项文件的源快照哈希。它与最终 PDF 的构建／视觉哈希分别记录，不把源快照当作最终逐页验收。核对促成两处精确澄清：B570 candidate 的 pending token 实际时序为 sample→phase bind→consume/accept；358H 主文保留统一比例（uniform）target-work reduction 的条件。

这些文件数量来自本轮实际遍历和执行，不继承旧的仓库总文件数，也不等于“重新阅读所有私有 raw 文件”。本记录不承担构建、逐页视觉或源码包解包验收；那些活动由各自本轮记录说明。

## 复算后的关键口径

| 对象 | 本轮 CPU 核对 | 保留的解释边界 |
|---|---|---|
| RTX 冻结扩展 | 384 个唯一 formal keys，24×4×4；各条件 96 份合格；12 组 GM、48 组 round GM | project-unused 是项目可见历史未执行，不是未训练；完整 response 资格不是数值等价 |
| RTX ordinary／matched／candidate | request R/C=1.741569262、M/C=1.035071366、R/M=1.682559598；generation R/C=1.170124448、M/C=1.169237971 | 大部分 request 改善来自 draft-free target path；50 个比率恒等式核对不是组件耗时分解 |
| RTX 任务与轮次 | 七个 matched-request 回归：MBPP/439、124、458、437、115、454、393；round 2=0.940220× | 任务 bootstrap 不能消除轮次反转或替代独立 session/day 重复 |
| phase family | 16 masks、128 requests；passing 3/7/11/15 | mask 3 仅在已测试四开关族中 inclusion-minimal；移除 draft 约束的额外 generation gate 仍失败 |
| 固定 UB4 更宽 draft | 重算所有保存 task ratios 的 GM 与分组 | 合格却更慢的反例保留；这是导出 task-ratio 重算，不是 raw timing 重解析 |
| B570 formal | 119/120；R/M/C 15 个完整 two-round task pairs，old-N1 14 个 | MBPP/400 的 old-N1 round 1 payload／中断费用仍缺失，不插补或零计费 |
| B570 强基线 | 12 个三计时 GM；R/M 在所有完整任务／轮次／计时均比 C 快 | 赢 old N1 不能作为部署收益；MBPP/245 old-N1 round 2 whole／host 反转保留 |
| B570 endpoint／raw | candidate endpoint=1,150、raw=1,176、paid suffix=26；drafted/accepted=888/702 | first-EOG/cap128 endpoint 与 RTX full response、历史 re-tokenized text 分开；raw unknown 不补齐 |
| M4 | 60 个任务绝对时间中位数，Guard/Always secondary=1.027076022，区间 [1.012956006,1.043559265]；two-action oracle factor=1.000691967 | secondary fresh stream 与 primary continued stream 分开；M4 是独立控制启示，不是 RTX repair 跨平台复现 |
| 358H | 核对 source-defined accounting 与 estimator 的正文／补充表述 | 完整 180-row original-host floor 审计仍继承；fixed-progress budget 不表示已实现优化或 NPU 不可能 |

完整复算还保留了两套 RTX interval 约定、natural-cross 矩阵、B570 299 qualification rows 与 caller-token 计数；详情见 `output/SCIENTIFIC_RECOMPUTATION_QA.json`。本轮模型请求、forward 和 warmup 均为 **0**。

## 导航与作者事项

`CLAIM_EVIDENCE.md/.csv` 保留 C01–C26，并增加本轮三类证据角色和详细补充去向；`EXPERIMENT_DESTINATIONS.md/.json` 保留 E01–E28 全量规划事实。补充去向使用 S2.1 等节号、稳定 TeX table label 和实际源码路径，避免图表页数变化使旧 Table S 编号误导读者。

M4 的策略细节、随机流、metadata recovery 和 oracle 分组在 S6.6；358H 的完整条件预算／分解／失败 candidate 在 S6.7；V3／V4 与 host amendment 在 S6.4。RTX 未通过的更宽 geometry 在 S4.2，qualified-but-slower 固定 UB4 在 S4.3。B570 旧 closeout 的局部正例及失败在 S5.1，119/120、raw unknown 和各计时在 S5.3／S5.4。主文必须仍就近给出决定工程选择的失败和条件，不能仅靠此账本替代主要论证。

v0.14.0 的“第二模型家族以后插在哪一节”写作计划移至 `AUTHOR_TODO.md`；正文保留一家族限制，没有预期结果。作者姓名／机构、CRediT、资助、冲突、数据访问权限、最终 AI 声明仍待真实作者确认。当前 JSA 官网 HTTP 403、期刊当前匿名化／字段未全部重新核实，以及 Editorial Manager 未上传／未验收的限制也已记录。没有合并、投稿或公开发布数据。
