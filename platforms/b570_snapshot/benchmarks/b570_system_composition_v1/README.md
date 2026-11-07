# B570：状态形成 × 局部执行组织的系统级验证

**独立 Draft；设计＋可运行 CPU 工具，不是已完成的 Vulkan 移植或 GPU 结果。**

## 研究目标

检验：自然执行中，用参考相近的 prefill 形成方式配合局部 Query-to-Batch（QB）continuation，能否扩大既有参考的可用优化范围，而不是全部回退到全局逐 token 执行。

工作单位是完整请求、prefill 分段、verification 批处理和跨阶段状态；不是继续搜索“某题某层某 head 的神奇字节”。一期固定现有 8B target / 已有 draft / 单 B570；迁移性通过 24 个未参与本项目实验的新输入、2 个领域、3 个长度层及真实自然执行检验，而不是以硬件数量代替泛化。此范围不覆盖任意模型、FlashAttention、多 GPU 或无限输出长度。

**通过首先意味着方法可检验；不保证获得正收益，不保证达到论文录用或独有创新。**

## 立即入口

将 [HOST_PROMPT.md](HOST_PROMPT.md) 交给 B570 agent。先完成静态源码/运行时接入，再在新 F0 后按阶段执行。无需等待 RTX E2/E1 或 PR105 的缺失 full-logit 采集；但同一 B570 不得与 PR105 并发。本 PR 不启动、不取消、不修改 PR105，未使用其剩余预算；RTX PR104、论文 PR102、分析 PR106 均不改。

- [PROTOCOL.md](PROTOCOL.md)：问题、固定对照、选题、预算、阶段放行、成功/负结果/止损。
- [NATIVE_CONTRACT.md](NATIVE_CONTRACT.md)：真实代码缺口与原机接线义务，尤其旧 target-only actor 禁止 draft、reference 不能重锚、counts-off 图切换。
- [ARCHITECTURE.md](ARCHITECTURE.md)：与体系架构的连接、可测计数、资源和物理摊销，明确哪些不能推断。
- `study.py`：标准库 CPU 选题/排程/请求语义校验/完整端点比较/有限性能汇总/工作量核对。
- `test_study.py`：41 项合成正负控制；不是原机资格。
- `architecture.py`：导出物理工作量与逻辑 K/V 供给场景；不输出虚假的 XMX 利用率、DRAM 实测或硬件加速预测。
- [SOURCES.md](SOURCES.md)：固定内部来源与近期外部近邻。

```bash
cd benchmarks/b570_system_composition_v1
python -B -m unittest -v test_study
python -B study.py plan --inputs HOST_INPUTS.json --output NEW_PLAN.json
python -B study.py analyze --plan NEW_PLAN.json --records RECORDS.json \
  --raw-root NEW_RUN --runtime-fingerprint SHA256 --output NEW_ANALYSIS.json
```

`HOST_INPUTS.json` 需要原机从固定 corpus/tokenizer 及全项目 exposure 清单形成。测试 fixture 只在测试里生成，绝不能当正式 prompt 池。命令不覆盖输出。没有自动 native execute 命令，也没有暗藏模型下载、加载、warmup 或后台任务。

## 有界预算：阶段不到就不花

| 阶段 | 新模型请求上限 | 独立算子启动 | native 进程上限 |
|---|---:|---:|---:|
| S0 静态接入与 CPU 测试 | 0 | 0 | 0 |
| S1 算子能力＋原参考桥接 | 16 | 48 | 64 |
| S2 四个已暴露输入，十臂自然执行 | 120 | 0 | 120 |
| S3 24 新输入 × 十臂 × 三 session，每测量前显式 warmup | 1,440（720 测量＋720 warmup） | 0 | 720 |
| **总上限** | **1,576** | **48** | **904** |

总 native 启动单位最多 1,624（模型请求＋独立算子，不能把一个请求当一个 forward），累计 owned native-process 时间 **21,600 秒**，新运行输出 **8 GiB**。S3 条件放行，非默认强跑；没有另加的 probe/smoke/warmup/retry。单项预算不足则停止并报告 incomplete，不更换模型、降精度、扩 q、缩短输出或偷偷扩预算。

用户此次已同意方向并要求按新 PR 推进；本轮助手仅创建方案与 CPU 工具。原机仍须在任何新 native 启动前提交实际 source/runtime/model/driver/inputs/request/F0 并认证回读，不能将本 README 当完成的运行时准入。上述新预算与 PR105 v1 已花 1 请求/127 decodes/12.438 秒和 PR105 v2 待定 168 次分开计账，不重置历史。

## 当前完成度与新增 k3 边界

已完成：可复现 CPU 计划器、语义检查、离线分析、合成测试和 host 协议。
待原机完成：Vulkan PQ/QB 图移植、reference-port bridge、实际请求协议、原生进程/时限/磁盘控制、真实 raw 适配与独立核验、F0、全部 GPU 运行。

不要写“已证明 B570 QB 可用”，不要把 native 补接看成只需改几个路径。若已支持的固定 backend 不具备所需广播/多 query 执行能力，先止损，而不是开启无限 shader 调优项目。

**k3 是本新研究的有意扩展，不是 PR92 的 k1 配置。** 必须实现并验证完整 k3 acceptance/rollback/bonus/EOG/cap 的控制逻辑；只改旧 worker 的 `k!=1` guard 不算完成。所有新 C 臂使用相同 k3，绝不拿历史 k1 请求时间直接当新对照。当前 S0 仍有真实 native 接入工作。
