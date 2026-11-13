# 方法与实现保证的对应

本表是对已有实现的静态审查和历史资格的界定，不是新的 native 资格。直接来源为 [#221 冻结 guard 审查](https://github.com/leecdiang/HeteroSpec/tree/af436df989570ad882db65bd8a4b265b9e8cfdae/benchmarks/frontier_cost_v1/next_study/guard_audit)，本目录 [GUARD_SOURCE_AUDIT.json](evidence/GUARD_SOURCE_AUDIT.json) 保留其每个符号、行号、完整成员 SHA 和缺失资格。

本次从用户审阅包独立重读并核对 8 个完整源码成员，SHA 全部匹配；其余 12 项仅继承冻结审查身份，其中 5 项明确是重构 frontend，不代表历史执行二进制。详见 [SOURCE_MEMBER_CHECK.json](evidence/SOURCE_MEMBER_CHECK.json)。服务器旧下载位置的 ZIP 不完整且不可读取，未拿它冒充发布资产。未下载大包或重新编译执行。

| ID／义务 | 实际可运行源码保证 | 不能推出的保证／论文处理 |
|---|---|---|
| G01 dense cache 与追加位置 | `PhaseContext`、`phase_append_requirements` 检查 dense、非环绕、F16、head/position、单流、非 SWA 等前置条件 | 不是 token/KV 字节 oracle，也不证明任意外部修改后的全局独占；仅声明受支持配置 |
| G02 whole/LOCAL 计划 | 相邻相同 extent／arithmetic class 形成有序组，组宽有界；LOCAL chunk 依赖实际 attention 切分 | arithmetic class 不是完整 backend recipe ID；调用数不等于 kernel 数，不能据此声称少做 token rows |
| G03 packed admission | Q8_0/F32、q 与形状限制；q≥8 且布局满足时按 `[K,4,g]` 分组，尾部走 ≤4 列路径 | packed 未标记节点仍走普通 CUDA dispatcher；不能借用 loop4 的 same-device、warp32、padding 与 MMVQ 保证；形状回退不等于已资格的普适参考回退 |
| G04 marked loop4 | 明确的 NVIDIA、同设备、warp32、padding、MMVQ/old-tile、整数 offset 检查 | 一些检查位于 decode/operator 内部，之前的工作可能已经改变状态；不是全阶段无副作用的预检 |
| G05 attention 与物理视图 | 源码绑定实际 KV 视图、extent、offset、stride 等 | 不是所有隐藏 dispatch/reduction、设备与 workspace 的完整 recipe 证书 |
| G06 graph reuse | 真实前缀向量、reference policy、placement 等参与重用判断，超出仅形状比较 | 抽象 `state_recipe` 或分析 helper 的键不能代替 native 全覆盖证明 |
| G07 输出所有权 | 同步后复制所请求完整 vocab 输出，检查 append 后 head 与有限值 | 没有在线逐请求比较独立 R 的全向量字节；有限值、token 或 argmax 相同都不足 |
| G08 pending／提交／失败 | 正常 decode 有 pending/commit 规则，捕获的 decode 异常会 poison context | trim/draft/sample/reset 的全部异常不都被同一事务 catch 覆盖；CLI 退出不是通用嵌入式可恢复事务保证 |
| G09 placement 观测 | capture 配置开启时回调观测实际执行节点 | clean 模式可关闭，名称筛选不天然包含 `frontier_packed`；不能说所有正式计时都取得完整物理执行证书 |
| G10 全向量／状态证据 | 资格 capture 导出完整输出、native sequence/frontier；另有 active-KV 抽取与离线比较 | 不是所有隐藏内存，clean 性能不重复 heavy 捕获；不能以 trim 前后 head 相同替代 retained KV 原始字节比较 |

处理方式：保留历史正确性结果的固定输入、模型、二进制、布局和被比较状态边界；不把外推义务写成已有在线 guard。若未来补 admission/fallback 或异常所有权实现，必须重新资格，不能用本次 CPU 审查为变更背书。

#221 的第五输出向量诊断也不能简化为“未被选中的向量都可丢弃”：其固定 token 37 消费者没有读取该向量，只说明该消费者的覆盖边界。所有请求要求的向量仍需完整保留。该 PR 的 22 项拟议 native 资格，以及后续完整 N1a 的 261 项，均没有因本次文档核对升级为 PASS。
