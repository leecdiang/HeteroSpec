# 固定证据与回归防线

审查日期：2026-11-10。设计基线为 [#216 固定 head](https://github.com/leecdiang/HeteroSpec/tree/41ef4ca6bbc382c02fb97ebea874651fbf9fd4ac)。新分支叠在此提交，仅新增本目录，避免把历史结果重写成新证据。

| 证据 | 固定版本 | 对本设计的约束 |
|---|---|---|
| [#210](https://github.com/leecdiang/HeteroSpec/pull/210) | `3268a63dcbde99d5d9f8dd461f34d56e9840d3a0` | 等工作量、完整输出、独立 32B 资格；不得把配置 guard 当数值证明。 |
| [#211](https://github.com/leecdiang/HeteroSpec/pull/211) | `ad9fb6846dd979c3a76d3c415c74fa9f86565f7d` | 显式顺序平衡、独立 R、负结果可结束。 |
| [#212](https://github.com/leecdiang/HeteroSpec/pull/212) | `398e79a177bc71d83db4d58cf78672554f552586` | 原冻结序列 199/196/278/197，并非全都支持位置 248/252 + 8；必须核验具体 fixture，不允许补零/静默延长 R。residual 不是可直接命名的 logging 开销。 |
| [#213](https://github.com/leecdiang/HeteroSpec/pull/213) | `ba5b4c8e01d50d4bfaab1ac3908f798347be063a` | RTX k7 更慢与等工作量 q8 更快可同时成立；不得把算子收益等同 live 收益。冻结/读者修复与间隙需保留。 |
| [#214](https://github.com/leecdiang/HeteroSpec/pull/214) | `fb1b55b8ac6d911881ffb24ae268563afe0d2568` | B 有进程首用与顺序混杂，C 的单次 follow-up 不构成稳态分布。8B 账本 1909/2048、3053954/8000000。 |
| [#215](https://github.com/leecdiang/HeteroSpec/pull/215) | `29a3751f3745668f287a8dcc3b2ad2c0d15bdc43` | 补证不抹掉旧全局冻结限制，不恢复未保存的历史 KV；公开 SHA 回读不等于 GPU 数值重验。 |
| [#216](https://github.com/leecdiang/HeteroSpec/pull/216) | `41ef4ca6bbc382c02fb97ebea874651fbf9fd4ac` | 32B 514/640、652026/2000000；4 暴露根、六臂、96 warm + 96 measured、graphs disabled。B2 仅准备，0 新 8B 请求。 |

## 必须阅读的具体文件

以下均位于上述 #216 固定提交，不能读取移动分支后假定版本相同：

- [`Q32_full_v1/build.py`](https://github.com/leecdiang/HeteroSpec/blob/41ef4ca6bbc382c02fb97ebea874651fbf9fd4ac/benchmarks/server_expansion_v1/Q32_full_v1/build.py)：图级 loop 为每列 `view → mul_mat → concat`；group 使用 `view_3d(ne11=1) → mul_mat → reshape`。只改图翻译单元，原 CUDA 对象保持。故旧比较同时改变图组织与通道组织，不能归因到新点积算法。
- [`Q32_full_v1/PLAN.md`](https://github.com/leecdiang/HeteroSpec/blob/41ef4ca6bbc382c02fb97ebea874651fbf9fd4ac/benchmarks/server_expansion_v1/Q32_full_v1/PLAN.md) 与 [`REBUILD.md`](https://github.com/leecdiang/HeteroSpec/blob/41ef4ca6bbc382c02fb97ebea874651fbf9fd4ac/benchmarks/server_expansion_v1/Q32_full_v1/REBUILD.md)：reserve8→32、长循环 observer、callback 返回值、重建闭包、完整预热与过期日期问题。
- [`REFERENCE_ADMISSION_PUBLIC.json`](https://github.com/leecdiang/HeteroSpec/blob/41ef4ca6bbc382c02fb97ebea874651fbf9fd4ac/benchmarks/server_expansion_v1/Q32_full_v1/REFERENCE_ADMISSION_PUBLIC.json)：独立标量 R 与 64 层、151936 维、原始四根的绑定。
- [`B2_controlled_v1/b2_controlled.py`](https://github.com/leecdiang/HeteroSpec/blob/41ef4ca6bbc382c02fb97ebea874651fbf9fd4ac/benchmarks/server_expansion_v1/B2_controlled_v1/b2_controlled.py)：16 进程、每进程四暖四测、33024 保守行；`STOP=2026-11-09T21:00:00Z` 已过期。
- [`B2_controlled_v1/SKIPPED_BEFORE_GPU.json`](https://github.com/leecdiang/HeteroSpec/blob/41ef4ca6bbc382c02fb97ebea874651fbf9fd4ac/benchmarks/server_expansion_v1/B2_controlled_v1/SKIPPED_BEFORE_GPU.json)：上次未执行，不能把 prepared 当新结果。

## 不再重复的错误

| 旧风险 | 新门禁 |
|---|---|
| 只冻一部分源码/脚本，运行后补读者 | 全部生成源码、host adapter、checker、exporter、统计、privacy transform 先用归档 fixture 测试并整体回读；冻结后更改新 epoch，不倒写“事前冻结”。 |
| 只检查 argmax、哈希或形状 | 数值资格用完整原始向量与解析 active KV/frontier；clean 哈希只是已资格路径的桥接。 |
| 同 R 名字但改变精度/归约 | R 二进制/依赖/策略/输出集合分别绑定；新输入扩展另建不可变 oracle 子集，不能覆盖旧 R。 |
| 用 graph 开关/timeout 解释全部性能 | 共同图政策先冻结；timeout 只证明该次未完成；计时只解释明确干预的实现包。 |
| 首用/预热不均、阶段间混池 | 每条完整同根 warm 紧接 measured，所有臂相同 reset；新 epoch 单独统计。 |
| 先看效果再选根/截短/换臂/加轮 | 只按输入筛选，明确排除历史暴露；冻结后不替换、不追正号。 |
| 旧 fixture 不够长或缺实际操作数 | CPU 先核验 token/state 长度与所有字节，缺失即阻断；新 oracle 生成逐项收费。 |
| 改目录清预算、重跑退款 | 原 ledger 前缀 SHA + 新阶段增量 + 累计总数；启动/失败/负例/参考/预热全部计费。 |
| 拿模型 hash/load 与输出序列化当 kernel time | 分清 service、operation、caller、GPU event、profiler；重叠时钟不相加，未知成本为 null。 |
| 只公开结果摘要，声称数值复验 | 完整公开字节/统计重算与私有数值捕获分别列明，绝不混称独立 GPU rerun。 |
