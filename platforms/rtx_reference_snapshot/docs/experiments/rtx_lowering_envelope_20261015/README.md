# RTX 下一阶段：实际执行路径、参考兼容表示与未见输入边界

**DESIGN_WITH_CPU_HELPERS；不是现成 native runner、执行 F0 或 GPU 实验结果。**

作者要求分析最新 RTX PR，并在有依据时设计下一步。本设计读取 PR104 封存 `f997262d6b0accb126a1217c9356745cc8bbf708`、PR110 结果 `dae5aea9f9009a686196dd89981c0ae9699ae612`、独立 B570 PR112 设计 `7864716787fabb17cb613ed7125c180736c133ef`。基于固定 main `f5b7b8e9a6d02b228cb0e7b7b3932e89327cfb63`，不改这些分支、旧 F0 或历史结果。

## 审查结论

PR104 六会话 PQ/QB 成本与72上下文重放支持继续推进软件主线。直接从已核验 Git blob 的36条会话log contrasts复算六个比值，与报告舍入一致；36条均为正。实际最小会话间隔3608.866443秒，首末开始间隔24.450800709小时。该复算不是完整raw重审，也没有重算bootstrap区间。

PR110 的390格是26个输入×3资源场景×5个同策略标签。源代码只检查mapping名称，不以名称改变正式调度；因此1.000是同实现parity，不是五种架构的性能比较，也不是新硬件被普遍证伪。保留SOFTWARE_FIRST，不再扩大同类toy扫描，不直接进入RTL/PPA。

## 本轮真正增加什么

1. 用PR104的完整、未裁剪tensor，观察实际CUDA后端支持、执行归属、kernel/拷贝/图管理信息及有限完成时间；将干净timing与profile彻底分离。
2. 把PR112提出的query/head lowering作为一个RTX软件候选，与真实PQ、QB比较。`r=h*q+j`不改模型head/权重；Q packing、mask及输出恢复全部收费。不把它预称新颖或更快。
3. 在原量化reference下，用三家族独立未见自然输入、实际较长有效上下文和完整请求，检查可用域与成本。不是再重跑PR104曝光面板来证明泛化。

QB本身若已足够好、QH不支持或无收益，都是有效出口。B570 PR112独立推进，不接管、不等待其正结果；没有从冻结Vulkan软件缺口推出新硬件必要性。

## 入口

- [PROTOCOL.md](PROTOCOL.md)：候选、强基线、阶段预算、实际计量及退出条件。
- [HOST_PROMPT.md](HOST_PROMPT.md)：Windows GPT Work执行入口。
- [design_checks.py](design_checks.py)、[test_design.py](test_design.py)：仅CPU索引与计划辅助，非native launcher或完整raw审计器。
- [VALIDATION.json](VALIDATION.json)：18项本地CPU测试和旧报告复算的精确范围。

S0可先进行CPU/源码接入。S1/S2/S3均需实际F0与相应作者确认，不自动执行或借用旧预算。

| 阶段 | 内容 | 最高预算 |
|---|---|---|
| S0 | 固定源码、真实GGML图接入、CPU准入 | 0 GPU/model/device-query starts；3600 child秒；1GiB |
| S1 | 完整72快照数值重放、24固定上下文timing/profile | 1009 operator-host attempts；2808 graph computes含288 warmups；7200 owned秒；4GiB |
| S2 | 三家族每族两输入、六主臂及影子R的自然pilot | 84 requests/processes；无warmup；7200 owned秒；4GiB |
| S3 | 每族18个未见输入、六臂、三会话跨两日期块 | 972 measured+972 warmups=1944 requests /972 processes；43200 owned秒；8GiB |

这是各阶段上限，不是必须一次全部执行的配额。失败/已启动/未启动分开；没有新probe、隐式capture compute或科学retry。只能一项owned重任务；原R监测能力按实际语义登记，不承诺未实现的周期采样或连续驻留。

新实现与结果只写 `benchmarks/rtx_lowering_envelope_v1/`，本设计留在其目录。保留Draft，不merge、不改论文或发布、不创建后台自动化，不要求新硬件或付费云服务。当前RTX封存证据可以独立用于论文，不能由这轮可选延伸阻塞旧结果更新。

## 本次主源范围

- PR104 RESULT、E2_SESSION_CONTRASTS、E2_SESSION_TABLE：结果与表级复算。
- PR110 RESULT、H0、model.py：同策略parity及数据/资源范围审查；未重跑390格。
- PR112 DESIGN：读取QH_C/QH_D索引与mask设计；未宣称RTX/CUDA移植已完成。
- NVIDIA CUDA Graph性能说明：https://docs.nvidia.com/dl-cuda-graph/troubleshooting/performance-issues.html ，graph/node tracing开销区别。
- NVIDIA CUPTI：https://docs.nvidia.com/cupti/main/main.html ，CUDA graph/node相关活动接口；本机已有版本是否支持必须核验，不因官网最新版存在而升级冻结环境。
- NVIDIA CUDA events：https://docs.nvidia.com/cuda/archive/13.4.2/cuda-runtime-api/cuda_runtime_api/group__CUDART__EVENT.html ，完成与异步流计时限制；只作方法依据，不冒称本机版本13.4。
- FlashInfer：https://docs.flashinfer.ai/api/attention.html ，fixed_split_size等强软件近邻；未适配其融合attention，不能作为本量化non-flash参考的直接性能数据。

本次不是穷尽文献优先权审查。head/query packing、固定归约、图复用均非独有概念；新贡献必须来自实现、同参考强基线和新增适用域，而不是实验数量。
