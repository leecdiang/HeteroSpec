# 第二版方法与实现修订记录

审阅基准：`1382b2295aa9525a99ddb8f24026390ea11e95c4`。本轮按作者授权修订方法说明，未新增 native 推理、GPU 实验或修改历史数据。不是正式期刊审稿决定。最终作者责任及声明仍由作者确认。

## 已修改

- `paper/sections/03_method.tex`：按“保留组内数值路径、改变组间组织”重写贯穿例子、构造和条件论证；增加有输入、两类分组、逐层执行、owned 输出和状态提交的七步伪代码。
- `paper/sections/04_implementation.tex`：明确 Q8 的 a=4 与 S3 mixed Q4/Q6 的 a=1 是两个方法实例；S3 保持 whole-graph cuts，B 是共享量化后的 backend scalar loop。删除重复的失败流程细节，保留实际失败边界并指向补充。
- `paper/sections/supp_contract.tex`：精确说明输出模式、reserve、完整组与 tails、accept/trim/pending 的源码行为，保留原有 capture/guard 差异和两个 CPU 消费者反例。

## 图与方法使用同一组例子

| 项目 | 四查询主例 | 八查询 packing inset |
|---|---|---|
| 已知位置 | 765–768 | 761–768 |
| 标量参考物理 extent | 768, 768, 768, 1024 | 前七行 768，最后一行 1024 |
| 物理 runs | 3+1 | 7+1 |
| LOCAL attention tiles（最大4） | 3+1 | 4+3+1 |
| LOCAL Q8 projections | 一个完整 a=4 组 | 两个完整 a=4 组 |
| frontend 用途 | seed + 三个 proposal 的四输出 verifier 可采用此构造 | 已知 prompt rows、last-row 输出；示意构造，不是新测量，也不是默认八输出 verifier |

Whole-call 四查询的投影会形成三列和一列 tail。正文要求 backend 对使用到的 1–4 列路径及其 quantization、reduction、descriptor 等条件承担数值义务，没有以四列 reshape 推导这些路径自动等价。

接受例固定为 accept d1,d2、reject d3：输入 seed 位于765，保留 target KV 0–767（长度768），correction 位于768、已输出但 pending；下一轮才 materialize。四个输出在接受决定前就属于请求集合，均须以原逻辑索引保存。此例与 `worker.cpp` 的 `keep=base+1+accepted` 对应。

## 三层义务与实际实现

1. **结构**：planner 根据元数据保持连续行序和不重叠完整分区；executor 在 native 输出复用前保存行归属，并按 consumer 决定提交状态。
2. **算术**：backend 要保持每个实际 group/tail 的操作数、量化、归约、stride、placement 及 descriptor。相同 extent 不代表 head geometry/V layout 相同；相同形状不决定 quantizer 或 reduction。
3. **检查**：实验对限定输入、边界的完整输出和活动状态提供资格证据；online、capture 与离线比较的覆盖保持分开。条件组合论证没有升级为所有 native kernels 的无条件证明。

主文中的输出集合 O 明确映射为 evaluated frontend 的 all-row 或 last-row 模式。原 Q8 profile 的 all-row reserve=4；32B S3 有独立 reserve=32。planner header 的一般 flags 并不提供任意 sparse-output 用户 API。

缓存状态符号改为 `mathcal K`，避免与投影内积维 K 重义。算法输入的已知行写作 `mathcal Q`，避免与 attention Q tensor 混淆。

## 直接核查与边界

逐文件读域与 SHA 在 `method_read_scope.json`；固定公开链接和 release source archive SHA 沿用 `reviews/method_sources.json`。本轮直接读取：

- 完整 `phase_plan.hpp`、`resident_context.hpp`；`worker.cpp` 的 reserve/decode/sample 定义和完整 request/accept/trim 循环。
- packed graph 的投影分组和 cached-attention grouping/view 代码；dense append requirements。
- S3 graph 与 MMVQ 的完整补丁。
- CPU width failure 的完整公开结果，以及 frontier probe 的完整源码和结果。

CPU 两行对一加一：242/256 output float bit patterns、43 serialized state bytes、后续127/128 float bit patterns 的差异均来自直接结果。第二例在运行前声明只消费四个输出，并以 q4+q1 为五行状态参考；没有在看到第五行差异后改合同。此轮仅重读源码和报告，未重新运行这些 native 诊断或读取受限 tensor blobs。

未重审全部 native 源树、全部未公开分支，也没有取得 all-input kernel proof、跨设备等价或通用服务事务恢复证据。当前限定主张可以通过这些文字修订说明清楚；若坚持上述更强主张，仍需要另行实现或实验证据。

## 写作与独立核对

实际重读 `scientific-writing` 2.3、`peer-review` 2.4 及 ethical review guidance（K-Dense commit `2d2065fb4520fa3f3f2bcf61cff26ec8b7eba4b5`），使用其证据绑定、条件区分和比例适当的修订原则。未安装软件、未新增一套审计门控。用户已授权稿件协作修订；不把此内部交叉阅读冒充正式期刊外审或最终人类作者认可。

语言审阅者交叉通读03/04后提出 K 重义与重复贡献段，均已修正。方法图的 token indices、extent、tile widths、outputs 和 pending transition 已与图表作者逐项对齐。实际编译和图形排版由整稿阶段复核；本记录不把尚未看到的最终 PDF 写成已通过。
