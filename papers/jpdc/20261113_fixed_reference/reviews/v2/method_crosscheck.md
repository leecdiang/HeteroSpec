# V2 方法、首图与实验桥接交叉检查

日期：2026-11-13。审阅基准：Draft PR #243，`1382b2295aa9525a99ddb8f24026390ea11e95c4`；本记录检查其独立 V2 工作区中的修订文件。用途是作者内部交叉检查，不是期刊正式同行评审。

## 结论

在本次实际读取的范围内，未发现需要阻塞整合的方法—图示冲突。新版首图、方法、实现和补充使用同一四查询例子；八查询图明确是已知 prefill 输入，未冒充四输出 verifier 的八行调用。32B 的 `a=1` scalar-loop 强基线、Q8 的 `a=4` factorial，以及自然两轮 pilot 的 C4096/loop4/no-draft 配置已正确分开。

本次没有修改他人负责的正文、图或数据。下表记录已经核实的对应关系，避免将“看过图”写成对全部实现和实验的全面认证。

## 首图与方法逐项检查

| 检查项 | 图中表示 | 代码/正文对应 | 判断 |
|---|---|---|---|
| 四个已知查询 | seed@765、d1@766、d2@767、d3@768 | padding 256 的 scalar-reference extents 为 768/768/768/1024；直接宽调用为全部 1024 | 一致；图将改变的前三个物理范围直接标出 |
| whole/local cut | Simple 两个外层框，3+1；Local 一个外层框，attention 3+1 | `resident_context.hpp` 按 extent 切 whole calls；local graph 在 attention 内用受限视图再拼回 | 一致 |
| 四查询算术组 | Local 一个四列组；Simple 三列 tail 加一列 | Q8 `a=4`；q=4 不进入 q≥8 的跨组 packed 分支 | 一致；没有把四列画成两个四列组 |
| tail 数值义务 | 图注说明所有使用的 1–4 列路径都须保持参考 | 方法和补充明确 width、quantizer、reduction、descriptor 均属 backend 条件 | 没有由 reshape 或相同 extent 推导无条件等价 |
| 输出所有权 | z0、z1、z2、z3 按行存储 | all-row verification 输出在 native buffer 复用前复制；consumer 不在看到差异后再排除输出 | 一致 |
| 接受前沿 | d1/d2 接受；z2 选择 correction c | 输入 z2 对应 position 767，预测位置 768 的 token | 索引正确 |
| 状态提交 | KV 保留至 767；d3@768 被 trim；c@768 pending | 初始 materialized length b=765，accepted r=2，keep=b+1+r=768；c 下一次 decode 才 materialize | 索引、长度与 pending 语义一致 |
| 八行 prefill | positions 761–768，last output requested | 前七行 extent 768、最后一行 1024；只需 last-row 输出，不触及原 all-row reserve=4 限制 | 一致；这是构造示意，不是新增实测 workload |
| 八行两种分组 | physical 7+1；attention 4+3+1；arithmetic 4+4 | local attention max4 tile；eligible projection `[K,4,2]` 保留内层四列路径 | 一致；未画出未经支持的任意并行 decoder calls |

`03_method.tex` 中数学输出集合 O 与实际 frontend all-row/last-row 模式有直接对应；`supp_contract.tex` 进一步给出两种集合及 Q8/S3 reserve 的差别。planner 结构不变量、backend 算术条件、有限实验检查分为三项。packed 不继承 loop4 全部在线 marker guard、CLI 失败退出不等于服务事务恢复，这两个边界在实现/补充保留。

## 与 Evaluation / Results 的桥接检查

完整读取本次工作区中的 `05_evaluation.tex`、`06_results.tex`，并回看原始 S3、自然多轮及 history-reconstruction 公开记录和 Q8 factorial 计划。

| 实验 | 当前稿件表述 | 直接来源和本次复核 | 判断 |
|---|---|---|---|
| S3 | mixed Q4_K/Q6_K，a=1、whole cuts、target-only；B 共享量化后 backend scalar loop；C 独立 scalar channels | S3 原 README、F0 graph/MMVQ diff；另从 288 行 CSV 排除 144 warm，独立重算 144 measured / 48 配对 / 12 roots | 与实现一致；未写成 Q8 backend-loop4 或 Local+packing 组合增量 |
| S3 估计量 | root 等权 C/B=0.984864；95% interval；phase sums 独立标注 | 本次重算 C/B=0.984863742851，降时 1.513625714888%；pooled=0.983809466031；48/48 paired rounds 较快 | 数字和统计单位一致；此次没有再抽 bootstrap，区间与原冻结结果核对 |
| S3 phase account | prefill 143.927→137.984 s；decode 216.663→216.690 s；主估计仍为 root 等权 | 原 S3 same-panel cost account 给出未舍入值及差额；5.942 s saving 使用未舍入数计算 | 正确；phase totals 没有被当成独立重复或拆成未测 kernel 因果 |
| Q8 factorial | a=4，whole/local × loop4/packed，k=3，q≤4 verification，packing 在 wider prefill | 两模型 PLAN 均为同 16 roots、4 sessions、4 arms；packed code 的 q≥8 条件与验证宽度一致 | 与 S3 分开；小分量、跨一的区间和 interaction 保留 |
| 自然两轮 pilot | C4096，original loop4 固定，target-only/no draft；2 conversations × 2 rounds × 2 arms | 原 README 明确以上配置、no FA/graphs；原 STATISTICS 内四对值独立做除法 | 1.0997048、1.0024302、1.0886215、0.9887654；pooled 1.042196240392 与正文四舍五入一致 |
| history 根因 | four-token empty-think suffix 与 next canonical history 不同；128 个 body IDs 保留；共同 trim/recompute | 原 history README 的两实际 free-response 轨迹、位置和 token 说明 | 没有写成 trim/parse/BPE 错误；旧 canonical history 的潜在复用没有归给 Local |
| opportunity 与成本 | 20/2,224 与 B570 受控 timing 分面；89-row counts 标作 source-derived | 文本、caption 和现有 figure-source mapping 分开频率、append 时钟、逻辑张量/节点计数 | 没有合成跨平台预测，没有把 calls/tiles 当 GPU traffic/latency |
| 完整应用与宽度 | draft application、same-D4 增量、固定顺序 8B 与 balanced factorial 分开；q8 equal-work 和 k7 live-work 分开 | 读取全文及方法调用条件；本次未另行复算这些完整应用统计 | 表述未混淆归因；原数据的完整 CPU 复算由统计/整合工作承担 |
| RTX 现代比较 | U 与 legacy B 不同合同、单输入提取算子；full backend 未运行；两 legacy candidates 是 separate sessions | 读取本文段落；方法无从此结果推导服务/跨平台优势 | 范围表述正确；本次没有重做此面板的统计或 upstream 源码审查 |

## 有据问题及处理

本次未提出需要修改他人文件的实质问题。首图的 native 条件在图注和方法中可见；不建议为追求“证明感”再向图中添加 guard/qualification 盒子，以免破坏当前的执行主线。

图的实际整页排版尚未在此次检查中确认：本次只实际显示了 `fig01_overview.png`，并读取其 LaTeX caption。最终 CAS PDF 中的跨栏尺寸、图注分页和相邻正文仍须渲染后检查，不计作已通过。

## 固定来源与复核范围

- [native phase source archive](https://github.com/leecdiang/HeteroSpec/releases/download/tpds-phase1-rtx-review-v2-evidence-20261107/rtx-phase1-source.zip)，archive SHA256 `57cbfbfe43ae1c4b4ed5ba3f5261412daa2b5c14b712e76d868da55f4f8a4101`。本轮方法修订已直接读 planner、resident frontend、worker acceptance loop、packed projection/local attention 构造和 native append metadata；逐文件范围与 SHA 在 `method_read_scope.json`。
- [S3 原结果](https://github.com/leecdiang/HeteroSpec/blob/ab695a766d055f7d3c6b1fed0720c579c749bcdb/benchmarks/server_expansion_v1/strong_baseline_followup_20261110/RESULTS_S3_20261112/README.md)；[同面板 phase account](https://github.com/leecdiang/HeteroSpec/blob/ab695a766d055f7d3c6b1fed0720c579c749bcdb/benchmarks/server_expansion_v1/strong_baseline_followup_20261110/RESULTS_S3_20261112/COST_AUDIT.json)。本次使用未改动的 `paper/data/closeout/service/S3_TIMINGS.csv` 重算主点估计，不重抽或替换预先定义区间。
- [Q8 8B factorial plan](https://github.com/leecdiang/HeteroSpec/blob/10fc03ed59e260a290a8ca8d6670d30d50f08118/benchmarks/jpdc_closeout_20261113/statistics/pr204/PLAN.json)；[14B factorial plan](https://github.com/leecdiang/HeteroSpec/blob/10fc03ed59e260a290a8ca8d6670d30d50f08118/benchmarks/jpdc_closeout_20261113/statistics/pr208/PLAN.json)。本次直接读两完整计划，未把共享 roots 视为模型间新独立样本。
- [自然两轮原 README](https://github.com/leecdiang/HeteroSpec/blob/6597489d01d0fa1fb17dce8bf6cade2c53e3a463/benchmarks/server_expansion_v1/N/free_service_retry_20261113/README.md)；同版本 `EVIDENCE/STATISTICS.json`。本次直接读完整公开 README、statistics 并重算四个配对比和 pooled ratio；未接触受限 tensor bytes。
- [canonical-history 原分析](https://github.com/leecdiang/HeteroSpec/blob/ef1b6427b7f3b6b7d62c4249933b33b8f810d89f/benchmarks/server_expansion_v1/N/resident_opportunity_20261113/README.md)，本次完整读取其 source/observation/inference 区分；未重新运行 tokenizer 或模型。
- [首图沿用的四查询 extent 来源](https://github.com/leecdiang/HeteroSpec/blob/e8a4981ef7db8f05cff7144fd4edc6e5a4109343/papers/reference_compatible/20261111_tpds_mainline_rewrite/data_added/rewrite_figure_sources.json)，与本次 native 源码核对；新首图没有新增实测观测。

未核查：最终 PDF 排版（待编译）、未公开 tensor bytes 的重新数值验证、全部 native kernel 的全输入等价、本文其他面板的完整独立统计重跑、实际服务事务恢复。没有 GPU、模型、tokenizer 或 native inference 执行；没有变更旧数据或 baseline。
