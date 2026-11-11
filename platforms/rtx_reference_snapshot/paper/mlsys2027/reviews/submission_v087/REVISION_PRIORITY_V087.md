# v0.8.7 审稿修订优先级

本表是审稿交付，不是已落实到冻结 PDF 的修改。所有请求先使用现有材料；不增加 GPU/model 执行，不改原始分母、数值、CI、失败状态、Figure 3 或作者冻结 tag。物理页码分别以主文／附录计数。

| 优先级 | 定位／报告 | 具体修改 | 是否新增实验 |
|---|---|---|---|
| P0-C 判断项 | 主文 p1–2、§6；R1，其他报告承认风险 | 讲清前瞻预测和同集判别相对资格失败本身新增哪些诊断约束；保留“主轨意义仍可能不足”的分歧 | 否；不能保证靠编辑消除分歧 |
| P1 | 摘要、贡献、§5–6；R1/R5/R6 | 统一顺序：B570 全轨迹预测 → RTX 指定候选判别 → matched qualification/cost；358H/M4 作为支持性约束 | 否 |
| P1 | §5.3、Table 3；R2/R4/R5 | 说明 UB2 是参数级候选而非实际逐 forward shape 完全匹配；用现有代码／记录列输入和状态经历，缺字段标未知 | 否 |
| P1 | Table 3、A18；R4 | 展示 /15 两者错、/18 仅 reference 错、/25 仅 UB2 错，replay 全等；不能用两个 51/57 代替交叉比较 | 否 |
| P1 | §5.4、Table 4、Appendix Q；R1 | 从现有 V4 B QPC 记录导出 19 个 prompt 条件中位时长的 min/quartile/median/max；精确标 V4，保持原 GM/CI | 否，只作 post-study 描述 |
| P1 | §3.2、Q.4；R3 | 明说 bootstrap 的 empirical prompt-row resampling 对象，条件于选定 cohort、观测中位数和固定配置；排除总体／会话保证 | 否 |
| P1 | 引言、Appendix J/A6；R4/R5/R6 | 将宽的 causal/transfer/mechanism 概括收紧为 prospective path prediction、sampled intervention 和 specified-candidate discrimination | 否 |
| P1 | §5.2、A14；R4 | score delta 与 retained raw margin 尺度邻近呈现，解释 sampled numerical sensitivity + immediate stability，不能称 near-boundary 或 whole-generation null | 否 |
| P1 | §8；R2 | 用最接近原始工作的小表区分观察敏感性、构造确定性、本稿预冻结轨迹判别与资格成本闭环；不宣称首次数值敏感性 | 否 |
| P1 | Table 1、§4–6；R1/R2/R5 | 压缩历史 inventory，保留入口／失败；将新研究成组呈现，§6 重点写结果改变的选择和固定前提 | 否 |
| P2 | Table 3；R4/R5 | Independent P/R 改为 separate P/R orchestration 并就近注明 shared numerical routines；区分 prediction P 与 draft P worker | 否 |
| P2 | §5.3–5.4、Table 3–4；R5 | 调整 float 位置，保持完整句及旧 0.646＋CI 在一起；caption 的 null speedup/CI 明确仅指 blocked batched row | 否 |
| P2 | Appendix A9、O/A13；R1/R2/R6 | A9 旧 RTX matched cost 标成 earlier two-path cost (30 prompts)；O 指向 A13 的准确包入口 | 否 |
| P2 | §3.3、O/Q.5；R3 | 表示 compact 直接复算／full capsule 原记录／reported chronology 的不同能力，布尔投影不是原始状态字节 | 否 |

不自动修订冻结稿件以掩盖这些意见。若落实上述修改，生成新的版本与 artifact hashes，按变化运行数值／source/LaTeX/视觉检查。没有新的失败或实质科学改变时，不重复完整历史测试和六人投票。不能把旧审稿分数转贴到新 PDF。
