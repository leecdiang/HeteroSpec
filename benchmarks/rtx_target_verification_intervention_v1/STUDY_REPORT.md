# RTX 完整实验报告

状态：VERIFIED_COMPLETE。645/645正式单元有效，失败尝试0；独立raw重算及干净归档恢复均通过。

本机GPU：NVIDIA GeForce RTX 5070 Ti Laptop GPU, 12227 MiB, 616.92, 00000000:02:00.0；Windows 10.0.26300；Python3.11.9；CUDA0，target37/37及draft29/29层offload。固定base `6a3a7e2483d5b13a24518d27b8c1ff3eafaac08f`；implementation `3b0044ed7fb3ce86fc97b8a822eea198a31ed5c2`。模型、数据与54个原runtime文件SHA256匹配V4。原CLI默认12线程与旧文档24线程不一致，本轮显式24线程重新资格；早期记录保留。

G0覆盖120条完整数组、30对plain/sham；其中45条H资格复用同一未改变H路径的实际记录，75条native在显式24线程下另行执行。此前默认线程资格120条及2条pilot单独保留。6个MBPP工程任务的30条输出不纳入正式分母。负例、恢复及启动工具返回后后台生存fixture均通过，不能据此承诺注销或重启生存。

| 分组 | H0/N0 | H1/N1 | N0/R | N1/R | 恢复任务 | 新增回归 |
|---|---:|---:|---:|---:|---:|---:|
| 旧19 | 57/57 | 57/57 | 51/57 | 51/57 | 1 | 1 |
| 新24 | 72/72 | 72/72 | 66/72 | 66/72 | 0 | 0 |

结论：完整预测闭环成立；主候选没有满足指定参考恢复及无新增回归的目标。

已知案例：HumanEval/15: restored；HumanEval/18: remaining_deviation；HumanEval/25: new_regression。restored表示本轮三次重复均完整恢复指定参考；remaining_deviation表示没有完整恢复。

| 实际图观察路径 | caller token数集合 | occupied token数集合 | logits输出数集合 |
|---|---|---|---|
| H0/draft/continuation | [1, 3] | [1, 2] | [0, 1] |
| H0/draft/prefill | [40, 41, 42, 44, 45, 46, 47, 48, 49, 51, 52, 54, 55, 56, 59, 91, 107, 111, 129, 139, 143, 151, 161, 165, 172, 182, 187, 194, 234, 237, 282, 293, 322] | [1, 2] | [0, 1] |
| H0/target/continuation | [1, 3] | [1, 2] | [1, 2] |
| H0/target/prefill | [40, 41, 42, 44, 45, 46, 47, 48, 49, 51, 52, 54, 55, 56, 59, 91, 107, 111, 129, 139, 143, 151, 161, 165, 172, 182, 187, 194, 234, 237, 282, 293, 322] | [1, 2] | [0, 1] |
| H1/draft/continuation | [1, 3] | [1, 2] | [0, 1] |
| H1/draft/prefill | [40, 41, 42, 44, 45, 46, 47, 48, 49, 51, 52, 54, 55, 56, 59, 91, 107, 111, 129, 139, 143, 151, 161, 165, 172, 182, 187, 194, 234, 237, 282, 293, 322] | [1, 2] | [0, 1] |
| H1/target/continuation | [1, 3] | [1] | [1] |
| H1/target/prefill | [40, 41, 42, 44, 45, 46, 47, 48, 49, 51, 52, 54, 55, 56, 59, 91, 107, 111, 129, 139, 143, 151, 161, 165, 172, 182, 187, 194, 234, 237, 282, 293, 322] | [1, 2] | [0, 1] |
| N0/draft/continuation | [1, 3] | [1, 2] | [0, 1] |
| N0/draft/prefill | [40, 41, 42, 44, 45, 46, 47, 48, 49, 51, 52, 54, 55, 56, 59, 91, 107, 111, 129, 139, 143, 151, 161, 165, 172, 182, 187, 194, 234, 237, 282, 293, 322] | [1, 2] | [0, 1] |
| N0/target/continuation | [1, 3] | [1, 2] | [1, 2] |
| N0/target/prefill | [40, 41, 42, 44, 45, 46, 47, 48, 49, 51, 52, 54, 55, 56, 59, 91, 107, 111, 129, 139, 143, 151, 161, 165, 172, 182, 187, 194, 234, 237, 282, 293, 322] | [1, 2] | [0, 1] |
| N1/draft/continuation | [1, 3] | [1, 2] | [0, 1] |
| N1/draft/prefill | [40, 41, 42, 44, 45, 46, 47, 48, 49, 51, 52, 54, 55, 56, 59, 91, 107, 111, 129, 139, 143, 151, 161, 165, 172, 182, 187, 194, 234, 237, 282, 293, 322] | [1, 2] | [0, 1] |
| N1/target/continuation | [1, 3] | [1] | [1] |
| N1/target/prefill | [40, 41, 42, 44, 45, 46, 47, 48, 49, 51, 52, 54, 55, 56, 59, 91, 107, 111, 129, 139, 143, 151, 161, 165, 172, 182, 187, 194, 234, 237, 282, 293, 322] | [1, 2] | [0, 1] |

原版R正式路径未增加图回调；其caller日志及G0观察版控制独立保留。表中只列实际捕获的图，未用容量值推算occupied值。

| 任务 | H0/N0 | H1/N1 | N0/R | N1/R | 重复稳定 | 参考变化 |
|---|---:|---:|---:|---:|---|---|
| HumanEval/143 | 3/3 | 3/3 | 3/3 | 3/3 | True | unchanged_match |
| HumanEval/31 | 3/3 | 3/3 | 3/3 | 3/3 | True | unchanged_match |
| HumanEval/25 | 3/3 | 3/3 | 3/3 | 0/3 | True | new_regression |
| HumanEval/81 | 3/3 | 3/3 | 3/3 | 3/3 | True | unchanged_match |
| HumanEval/15 | 3/3 | 3/3 | 0/3 | 3/3 | True | restored |
| HumanEval/141 | 3/3 | 3/3 | 3/3 | 3/3 | True | unchanged_match |
| HumanEval/142 | 3/3 | 3/3 | 3/3 | 3/3 | True | unchanged_match |
| HumanEval/18 | 3/3 | 3/3 | 0/3 | 0/3 | True | remaining_deviation |
| HumanEval/136 | 3/3 | 3/3 | 3/3 | 3/3 | True | unchanged_match |
| HumanEval/99 | 3/3 | 3/3 | 3/3 | 3/3 | True | unchanged_match |
| HumanEval/148 | 3/3 | 3/3 | 3/3 | 3/3 | True | unchanged_match |
| HumanEval/140 | 3/3 | 3/3 | 3/3 | 3/3 | True | unchanged_match |
| HumanEval/87 | 3/3 | 3/3 | 3/3 | 3/3 | True | unchanged_match |
| HumanEval/76 | 3/3 | 3/3 | 3/3 | 3/3 | True | unchanged_match |
| HumanEval/26 | 3/3 | 3/3 | 3/3 | 3/3 | True | unchanged_match |
| HumanEval/49 | 3/3 | 3/3 | 3/3 | 3/3 | True | unchanged_match |
| HumanEval/40 | 3/3 | 3/3 | 3/3 | 3/3 | True | unchanged_match |
| HumanEval/109 | 3/3 | 3/3 | 3/3 | 3/3 | True | unchanged_match |
| HumanEval/66 | 3/3 | 3/3 | 3/3 | 3/3 | True | unchanged_match |
| MBPP/310 | 3/3 | 3/3 | 3/3 | 3/3 | True | unchanged_match |
| MBPP/91 | 3/3 | 3/3 | 3/3 | 3/3 | True | unchanged_match |
| MBPP/267 | 3/3 | 3/3 | 3/3 | 3/3 | True | unchanged_match |
| MBPP/273 | 3/3 | 3/3 | 3/3 | 3/3 | True | unchanged_match |
| MBPP/438 | 3/3 | 3/3 | 3/3 | 3/3 | True | unchanged_match |
| MBPP/257 | 3/3 | 3/3 | 3/3 | 3/3 | True | unchanged_match |
| MBPP/444 | 3/3 | 3/3 | 3/3 | 3/3 | True | unchanged_match |
| MBPP/89 | 3/3 | 3/3 | 3/3 | 3/3 | True | unchanged_match |
| MBPP/68 | 3/3 | 3/3 | 3/3 | 3/3 | True | unchanged_match |
| MBPP/463 | 3/3 | 3/3 | 0/3 | 0/3 | True | remaining_deviation |
| MBPP/304 | 3/3 | 3/3 | 0/3 | 0/3 | True | remaining_deviation |
| MBPP/65 | 3/3 | 3/3 | 3/3 | 3/3 | True | unchanged_match |
| MBPP/456 | 3/3 | 3/3 | 3/3 | 3/3 | True | unchanged_match |
| MBPP/17 | 3/3 | 3/3 | 3/3 | 3/3 | True | unchanged_match |
| MBPP/266 | 3/3 | 3/3 | 3/3 | 3/3 | True | unchanged_match |
| MBPP/224 | 3/3 | 3/3 | 3/3 | 3/3 | True | unchanged_match |
| MBPP/394 | 3/3 | 3/3 | 3/3 | 3/3 | True | unchanged_match |
| MBPP/283 | 3/3 | 3/3 | 3/3 | 3/3 | True | unchanged_match |
| MBPP/86 | 3/3 | 3/3 | 3/3 | 3/3 | True | unchanged_match |
| MBPP/305 | 3/3 | 3/3 | 3/3 | 3/3 | True | unchanged_match |
| MBPP/246 | 3/3 | 3/3 | 3/3 | 3/3 | True | unchanged_match |
| MBPP/268 | 3/3 | 3/3 | 3/3 | 3/3 | True | unchanged_match |
| MBPP/164 | 3/3 | 3/3 | 3/3 | 3/3 | True | unchanged_match |
| MBPP/419 | 3/3 | 3/3 | 3/3 | 3/3 | True | unchanged_match |

旧R/H0/N0全部171条历史数组及endpoint比较通过。新24题来自固定官方sanitized MBPP commit e49bbfe381c9c0e564b937f1c4e163a2273c65cc，数据SHA256 ca95deaa9a01ef0a6f439f88bcf0dd3db3563d22f22aad6cae04ebb9a8d8c8e9；静态曝光排除及排序在新题forward前完成。新仅表示审计范围内无已知本项目执行曝光。

H及native保持各自caller grouping。Prefill和draft UB2固定，target continuation候选UB1。图回调保留实际caller tokens、positions、logits mask和occupied graph维度，容量不等于实际token数。首个pending在source采样并accept一次；完整KV、pending logits、source-before/source-after/destination字节及clone行为控制保留。Opaque sampler无法序列化，不宣称其字节相等。

258条H0/H1预测和各自产生的proposal tapes封存后，native才开始。封存模式：REMOTE_BEFORE_NATIVE。原生接收prompt、资产和固定参数，使用自己的live draft，未输入H tapes或未来答案。本机append-only hash ledger及Git内容归属支持顺序，不认证独立绝对实验时间。

独立parser直接重读raw，未导入研究比较helpers。归档15192个逻辑文件，SHA256 `ee545bda11c9c0622d589024e4805fb1f1d3f3f0cbcd9c5551aeb22258733482`，1205757106字节；CAS逐文件还原并重算科学字段一致。省略权重及外部/新runtime二进制，离线哈希清单不能认证省略字节。

贡献范围：固定单模型对、RTX/CUDA、旧19及新24任务上的预测干预native闭环和有限参考恢复计数。不推断功能正确率、生产lossless、唯一kernel、必要/最小性、速度或能耗。具体是否成功以H1/N1完整匹配与/15、/18参考恢复共同判断。未改论文、旧实验状态或作者tag。
