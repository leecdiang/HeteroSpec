# 原机执行：先做有界资格与成本诊断

目标是判断同一历史下哪些验证动作合法、各自实际成本是多少。本轮只运行
这里固定的 target-operation profile，不自动扩展为全服务面板。CPU 的
q2 失败与 q1 smoke 都不能代替这次 GPU 资格。

## 1. 接续条件

- 在原机读取本 Draft PR 的固定 commit，记录完整 HEAD。实验子树必须已
  提交且无修改；输出放在 checkout 之外的新目录。runner 会检查这些身份。
- 先只读清点服务器、现有任务和显存。使用已分配的一张空闲非 GPU0 卡；
  保留现有服务和 PR218 S3。没有执行通道或明确分配时，完成只读清点与构建，
  记录资源缺口，不启动模型。不要 sudo、升级驱动、reset GPU 或杀其他任务。
- 记录实际 GPU 型号、driver、compiler/CUDA 与库身份。保持 GPU UUID
  采集关闭。A5000 使用 SM86；不要把默认编译目标用于不同架构。
- 这是独立实验 epoch，不挪用 PR218、B2 或其他旧实验剩余预算、reference
  或成功状态，也不修改正在运行的 S3 文件和 journal。

## 2. 模型与公开输入已固定

使用已有 `Qwen3-8B-Q8_0.gguf`，whole-file SHA256 必须为：

```
408b955510e196121c1c375201744783b5c9a43c7956d73fc78df54c66e883d6
```

该身份来自经完整 archive/member 哈希验证的 PR213 job manifest，64 个
jobs 一致。它同时绑定 GGUF 内置词表。另附 tokenizer metadata receipt
身份和 vocab=151936；receipt 的摘要不冒充独立词表内容摘要。

`matched_cost/inputs_public.json` 固定两个已暴露历史：p248 与 p255。它们按
原始记录的 root/cycle 字典顺序选取，没有按性能选择。它们是操作诊断输入，
不是新确认集、自然在线控制器或原 GPU reference captures。不得替换模型、
重分词、改 token IDs，或把候选随后产生的新输入混进本轮。

## 3. 新路径构建

从 `benchmarks/frontier_cost_v1` 运行。以下路径都由原机 agent 填成真实的
独立目录，避免覆盖任何旧结果。

```bash
python prepare.py --work /absolute/fresh/hs-cuda-prepared \
  --backend cuda --cuda-arch 86 --jobs 2
```

这一步只获取与编译源码，不加载模型。可用 `--archive` 指向已存在且哈希
完全相同的 source ZIP。任何编译失败都保留日志；不能为通过而改旧数值源码。
CUDA 全库构建尚未在本次无 GPU 环境中验证，原机应如实记录结果。

读取生成的 `PREPARED.json`，记录新数值库、frontend、构建参数和实际路径。
成功编译仍是 `BUILT_NOT_QUALIFIED`。新库不能直接继承旧 ELF 的数值资格。

## 4. 先生成计划，再执行固定 profile

无模型计划命令：

```bash
python matched_cost/run_probe.py \
  --inputs matched_cost/inputs_public.json \
  --output /absolute/fresh/hs-public-plan --plan-only
```

完整通过时的硬上限为：

| 阶段 | Contexts | Native decode API calls | Target rows |
|---|---:|---:|---:|
| 数值 / 状态资格 | 38 | 444 | 9,789 |
| 后续两个顺序、两种状态的测量 | 152 | 2,588 | 58,658 |
| 总计 | 190 | 3,032 | 68,447 |

这些计数包括 prefix、warmup、reset 后重放和 continuation。API 调用数
不等于 CUDA kernel 数。raw blob 上限 2 GiB，native 子进程限时 1,800 秒；
超时仅终止并回收这个 runner 启动的 child，保留已有结果，不自动重试。
1,800 秒不包含前面的源码核验、哈希计算和编译，不是整个流水线的总时限。

在确认设备已分配、无已有 compute process、模型哈希正确后执行：

```bash
python matched_cost/run_probe.py \
  --core /absolute/fresh/hs-cuda-prepared/sourcekit/native/cores/loop4 \
  --frontend /absolute/fresh/hs-cuda-prepared/frontend/candidate_frontend \
  --lib-dir /absolute/fresh/hs-cuda-prepared/numerical_build/bin \
  --model /absolute/existing/Qwen3-8B-Q8_0.gguf \
  --inputs matched_cost/inputs_public.json \
  --output /absolute/fresh/hs-public-operation \
  --backend cuda --gpu-index "$HETEROSPEC_GPU_INDEX"
```

`HETEROSPEC_GPU_INDEX` 必须由原机实际分配结果设置，不能照抄为任意空闲卡。
runner 在模型调用前检查来源、模型、单卡可见性、已存在进程及预载显存。
物理 GPU 编号须与实际 CUDA 设备的 PCI 地址对应；MIG、映射歧义或落到
物理 GPU0 都拒绝执行，不能仅凭 `CUDA_VISIBLE_DEVICES` 的数字推断选卡正确。
预载显存门槛不等于连续峰值证明。实际模型层放置和已装载模块也会记录。

任何向量或活跃序列不一致立即停止本 profile，不进入测量；保留失败和
完整双方原始数据。不改 ubatch 去伪装请求的物理宽度，不换 fixture，不删除
不利输入，不追加 sweep。原模型哈希、source、binding 或预算不符也停止。

## 5. 如何解释并交回结果

完整请求里的 draft、sampling、prefill 等并不都包含在本操作计时窗内。
state export 还会影响测量前的 cache 状态。请保留这两个状态标签：
`first_after_fresh_context` 与 `one_shape_warmup_then_reset`，同时报告实际
graph build/reuse；不能改称稳态或默认已有热图。

若全部资格通过，交回逐动作成本表及全部计数。q8 与 q4+q4 的差值包括
shape、attention、graph 与共享执行等因素，不能直接当作普适常数 A。
前一轮 4.498 ms 门槛来自特定 Windows RTX 完整窗口；在 A5000 上须结合
同硬件、同身份的完整服务基线重新评估，不能直接套数。

把 code commit、库和模型身份、RUN/RESULT/验证摘要及独立 raw manifest
放入结果说明；原始向量、状态、模型、二进制和机器 telemetry 保留在私有
证据包中，不提交到 Git。提交新的 Draft 结果更新供审阅，不自动合并、
改论文、租卡或启动后续大面板。

原 M2 production entry 的 eager/deferred 两臂可以用构建器生成，但其真实
模型、GPU reference、完整服务资格是下一阶段。此 target-operation probe
不替代那项资格，也不宣称已经达到独立 5%。
