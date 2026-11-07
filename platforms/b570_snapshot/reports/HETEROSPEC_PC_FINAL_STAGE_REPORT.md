# HeteroSpec-PC 最终阶段封存报告

**封存日期：2026-09-06**  
**平台：Windows 11 / Intel Core Ultra 9 275HX / Intel Graphics / Intel AI Boost / NVIDIA GeForce RTX 5070 Ti Laptop GPU 12 GB**  
**研究分支状态：停止继续扩大传统 draft-model speculative decoding 实验**

## 结论摘要

本阶段回答了一个明确的系统问题：在 12 GB 消费级 AI PC 上，把闲置的 Intel CPU/iGPU/NPU 用作 draft、把 RTX 5070 Ti Laptop 用作 target，能否为 8B 至 14B 模型带来可靠的推测解码加速？

当前实现和已测试的成熟框架路径均未得到可推广的正加速。8B 上，60 题正式 pilot 的全部 `k` 都为负；12 题根因控制说明跨设备传输并非唯一原因，自研 harness 的重复 prefill、跨 runtime 调度和 KV/控制开销确实很大，但成熟的 RTX 原生 assisted generation 也只达到近似 break-even。把 target 扩至 14B 后，target token latency 增加 47.4%，理论筛选比值 `r` 从 0.179 降至 0.122，但 CPU-assisted 路径仍只有 0.718x，且 4/12 输出不完全一致；同时 12 GB 显存已成为决定性约束。

因此不再打开 420 题 holdout，不尝试约 20B target，也不继续用更多 benchmark 为这一分支“续命”。

> **Stop criterion reached.**

## 决策路径

```text
HeteroSpec-PC
│
├── Device qualification
│     ├── OpenVINO CPU / GPU.0 / NPU 均通过显式 runtime gate
│     └── CPU 是最快的 Intel draft 设备
│
├── 60Q k sweep
│     ├── k = 1 / 2 / 4 / 6 / 8
│     ├── 60/60 题、360 个配置块、420 个生成 turn，exact failure = 0
│     └── 所有 k 均为负，最佳 k=1 仍只有 0.51x 几何平均加速比
│
├── 12Q root-cause
│     ├── CPU/OpenVINO → RTX 自研路径：0.733x
│     ├── RTX → RTX 同一自研 harness：0.611x
│     ├── 跨设备并非唯一原因，自研 harness 开销得到确认
│     └── Transformers 原生 RTX speculation：1.015x，约等于 break-even
│
└── 8B → 14B crossover
      ├── target latency +47.4%
      ├── r：0.179 → 0.122
      ├── CPU-assisted：0.718x，0/12 题更快
      ├── exact output：8/12，不能作为正确性合格 benchmark
      └── 12 GB VRAM 成为限制，不再测试 RTX 双模型同驻或 20B
```

## 1. 平台与 Gate 0

Gate 0 结果为 **PASS WITH TELEMETRY LIMITATION**。

- PyTorch 2.11.0+cu128 显式识别 RTX 5070 Ti Laptop；CUDA 可用，显存为 12 GB 等级。
- OpenVINO 显式识别并成功编译/运行 `CPU`、`GPU.0` 和 `NPU`。Intel 单设备实验禁止使用 `AUTO`/`MULTI`。
- NVML 的 1 Hz 功率记录通过。
- Intel Unified Telemetry 可记录 CPU package power，并可观察 Intel GPU/NPU 活动；该 OEM/驱动组合未提供独立 iGPU/NPU power domain，因此各 power domain 不作相加，也不声称为整机功耗。
- Windows 电源模式与 OEM 模式固定为用户接受的 Balanced；MUX 为 Hybrid，Intel 与 NVIDIA 设备同时可用；AC 已连接；page file 为系统管理。

完整平台清单见 `system_profile.json` 与 `reports/GATE0_REPORT.md`。

## 2. Intel draft device qualification

使用相同的 Qwen3-0.6B 对称 INT4、小上下文、低 batch 自回归条件测得：

| k | CPU | Intel iGPU | NPU |
|---:|---:|---:|---:|
| 1 | 10.78 ms | 14.87 ms | 140.33 ms |
| 2 | 21.15 ms | 30.29 ms | 168.98 ms |
| 4 | 42.76 ms | 59.34 ms | 224.54 ms |
| 8 | 84.82 ms | 121.51 ms | 330.69 ms |

结论：CPU 是本机最快的 Intel draft 设备，故进入主实验；iGPU 不是低 batch token-by-token 推理的“降维优势”，其并行单元、驱动调度与共享内存开销在这一工作负载下未被充分摊薄。NPU 完成 qualification，但当前 OpenVINO 路径的延迟远高于 CPU，不进入正式主链路。

## 3. 60 题 k sweep

正式 pilot 使用 Qwen3-8B NF4 target、CPU/OpenVINO Qwen3-0.6B draft、128-token 输出上限，对 60 道 Spec-Bench 题测试 `k=1/2/4/6/8`。60/60 题完成，360 个配置块与 420 个生成 turn 均无 exact-output failure。

| k | 几何平均 speedup | 算术平均 | 中位数 | 更快题数 | acceptance |
|---:|---:|---:|---:|---:|---:|
| 1 | 0.51x | 0.53x | 0.53x | 0/60 | 67.2% |
| 2 | 0.46x | 0.50x | 0.47x | 0/60 | 56.3% |
| 4 | 0.35x | 0.40x | 0.36x | 1/60 | 40.7% |
| 6 | 0.30x | 0.34x | 0.29x | 0/60 | 31.5% |
| 8 | 0.25x | 0.29x | 0.24x | 1/60 | 25.4% |

最佳 `k=1` 仍约慢 49%，且增大 `k` 时 acceptance 与性能同步恶化。因此没有统计理由直接扩大到 420 题；应先做根因控制。

## 4. 12 题根因控制

从六个官方任务组中按输入长度预先选取每组最短的两题，固定 64-token cap 与 `k=1`：

| 配置 | 实现 | 几何平均 speedup | 更快题数 | exact output |
|---|---|---:|---:|---:|
| RTX 8B baseline | 配对基线 | 1.000x | — | reference |
| CPU 0.6B → RTX 8B | OpenVINO + 自研 verifier | 0.733x | 1/12 | 12/12 |
| RTX 0.6B → RTX 8B | 同一自研 harness | 0.611x | 0/12 | 12/12 |
| RTX 0.6B → RTX 8B | Transformers native assisted | 1.015x | 5/12 | 12/12 |

这一控制组排除了“只要移除 CPU→CUDA 传输就会变快”的简单解释。同一个低效 harness 把 draft 放回 RTX 后，因为 GPU contention 反而更慢。自研路径的重复完整前缀 draft、跨 runtime 编排、verification/correction、Python/KV bookkeeping 均贡献开销；成熟框架通过集成 assistant KV cache 与调度消除了其中的大部分损失。

但消除实现损失后，8B 原生 speculation 的几何平均仅 1.015x、总时间比 1.031x、中位数 0.973x，方向随题目变化。这是“小样本诊断中的近似 break-even”，不是稳定的生产加速。

## 5. 8B → 14B target-size crossover

14B feasibility 使用与 8B 成对一致的内存可行协议：NF4 linear、FP32 quantized compute、BF16 非量化层、eager attention、128-token prompt、256-token output、3 次重复、CUDA 进程上限为物理显存 85%，无 CPU offload 或 silent fallback。

| Target | TTFT | decode latency | sustained | CUDA peak | NVML peak |
|---|---:|---:|---:|---:|---:|
| Qwen3-8B | 229.48 ms | 60.16 ms/token | 16.62 tok/s | 5.905 GiB | 6694.1 MB |
| Qwen3-14B | 423.87 ms | 88.69 ms/token | 11.27 tok/s | 9.678 GiB | 10646.1 MB |

14B 的稳态 target latency 是 8B 的 1.474 倍。以合格 CPU draft 的 10.78 ms/token 作为初筛：

- 8B：`r = 10.78 / 60.16 = 0.179`
- 14B：`r = 10.78 / 88.69 = 0.122`

分母变大确实改善了理论空间，但并未产生端到端 crossover。Transformers native CPU-assisted 14B、同一 12 题、`k=1`、64-token cap 的结果为：几何平均 0.718x、中位数 0.717x、总时间比 0.708x、0/12 更快；输出只在 8/12 题完全一致。该结果正式标记为 **FAIL_CORRECTNESS**，其时序只保留为诊断证据，不能晋升为正确性合格的 benchmark。

全 FP32 非量化层的 14B 无法安全装入：85% 上限下在实际分配前即因请求 10.71 GiB 失败；91% 上限下加载至约 75%、已分配 10.49 GiB 后，追加 340 MiB 时安全 OOM，NVML 峰值 11,550.1 MB。内存可行的 14B target 单独已使用约 9.68 GiB CUDA / 10.65 GB NVML，因此未冒险进行 14B target + RTX draft 双模型同驻，也未尝试 20B。

## 6. 稳定性事件与安全边界

实验期间曾在接近满显存区域反复出现 Windows `HYPERVISOR_ERROR (0x20001)` 黑屏/崩溃；在恢复默认显存频率后仍能复现，游戏与双烤稳定，因此不能归因于显存超频。事件与模型加载/推理时接近显存容量高度相关，但现有证据不足以证明唯一的内核级根因。

后续采用显存配额、减小输出 cap、先做 canary、记录 NVML peak 与安全 OOM 的方式控制风险。60 题 run 曾达到 12,204.1 MB 而未崩溃，这并不证明近满显存运行安全；它只说明崩溃不是由一个绝对、可重复的单一阈值决定。底层 hypervisor/驱动稳定性问题未被宣称为已修复。

## 7. 停止判据

本分支在以下证据同时出现时停止：

1. 8B 的完整 60 题、五个 `k` 均无总体加速，最佳仅 0.51x。
2. 12 题控制证明自研 harness 是重要开销来源，但成熟 RTX 原生 speculation 在 8B 也仅近似 break-even。
3. 14B 把理论 `r` 改善到 0.122 后，成熟 CPU-assisted 路径仍为 0.718x，且存在 4/12 exact mismatch。
4. 14B target 已逼近 12 GB 显存安全边界；RTX 双模型同驻和 20B 会显著增加 OOM/系统崩溃风险。
5. 因此 420 题无法解决当前机制性阻塞，只会放大时间、能耗和平台风险。

**Stop criterion reached.**

这不证明所有硬件、所有 target 尺寸或一个未来的持久化 OpenVINO KV-cache 实现都必然失败；它证明的是：在本机、当前可用的正确性合格路径和安全内存范围内，继续扩大传统 draft-model speculative decoding 没有实验依据。

## 8. 有效性边界

- 60 题 pilot 为显存安全把原计划较长输出改为 128-token cap；结论适用于该冻结条件。
- 420 题 holdout 从未打开，因此不存在用 holdout 反复调参的问题。
- 12 题 root-cause 是高信息密度控制实验，不是最终总体性能估计；1.015x 不应被宣传为稳定收益。
- 14B 的全 FP32 配置无法装入，8B/14B crossover 使用成对 BF16 非量化层配置；它与早期 8B 结果不可直接混成一个绝对性能表。
- 14B CPU-assisted 的 4/12 mismatch 使其不具备正式 benchmark 资格。
- 自研分解未独立测得纯 CPU→CUDA copy 时间，故不把所有 residual 都归因于跨设备传输。
- Intel 独立 GPU/NPU power counter 不可用；CPU package、GPU/NPU activity 和 NVIDIA board power 分域报告，不相加为整机功耗。

## 9. 后续研究方向（新问题，不延续本分支）

若继续利用 iGPU/NPU，应建立新的研究问题：让 Intel 设备承担 embedding、reranking、speech、vision 或其他可与 RTX target 并行的工作，而不是与 target 每个 token 强同步。

本阶段数据支持的系统设计启示是：

> “闲置算力”不等于“免费算力”。这台机器应避免 fine-grained heterogeneous synchronization；更有希望的是 coarse-grained、可异步、状态耦合弱的异构协作。

新方向应使用独立的研究假设、数据集、正确性指标与 Gate，不应把结果并入本 speculative decoding 分支。

## 10. 证据索引

| 内容 | 主要证据 |
|---|---|
| 平台与 Gate 0 | `system_profile.json`; `reports/GATE0_REPORT.md`; `logs/check_nvidia.txt`; `logs/check_openvino_devices.txt` |
| Intel telemetry | `reports/intel_telemetry_capabilities.md`; `telemetry/intel_idle_30s/` |
| Draft qualification | `reports/QWEN_DRAFT_QUALIFICATION.md`; `reports/DRAFT_MICRO_LATENCY.md`; `reports/qwen_draft_qualification_runs.csv` |
| 稳定性事件 | `reports/PHASE2_HYPERVISOR_INCIDENT.md` |
| Cached/exact correctness | `reports/PHASE3_CACHED_CORRECTNESS.md`; `reports/PHASE3_SPECULATIVE_CORRECTNESS.md` |
| 60Q k sweep | `logs/phase4-specbench-pilot-cap128-formal-20260906.json` |
| 12Q root cause | `reports/ROOT_CAUSE_SPECULATION_12Q.md`; `logs/phase5-*-20260906.json` |
| 8B/14B crossover | `reports/TARGET_SIZE_CROSSOVER_8B_14B.md`; `logs/phase6-*-20260906.json`; `env/qwen3-14b-manifest.json` |

模型权重、虚拟环境和超大型 Intel trace 不复制进轻量封存 ZIP；模型由带 revision/hash 的 manifest 引用，Python 环境由 pip freeze 复现，大型原始 trace 保留在原路径并由外部资产清单记录。
