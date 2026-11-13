# RTX 完整 backend 实验：本轮实现与现场接续

**本轮没有加载模型、CUDA 或 GPU。** 已实现工具，不等于两条原生链已经通过资格；PLAN.md 科学问题与总预算不变。

## 已实现
- `experiment.py prepare`：从真实 token 候选按长度×code/math 选择 16 根，生成 12 个 resident session、192 次正式请求和 12 次 warmup；配对顺序 P=RM/MR/MR/RM，G=RM/MR。
- `native_worker.cpp`：完整 model/context/decode API，不是提取算子。单模型驻留，C1024、batch/ubatch32、F16 KV、2 CPU threads、FA disabled、单 GPU 全层 offload 请求。实际 placement 仍需从原生日志核实。
- P 固定 prompt+128 continuation token，每次调用只请求末行 logits，逐个 decode continuation。G 使用共同的 lowest-ID tie-break greedy，EOG 不作为正文 decode；每个实际内容 token（包括最后一个）均 decode 入状态，故命名 **state-complete response**，不是 CLI 默认响应延迟的替代品。
- 同步 host timer 包括 reset、prefill、decode、同步及轻量 token 处理；不含文件解析、JSON 落盘或模型加载。另报 worker 总耗时、phase、TTFT、rows/calls、tokens、末 KV 位置。
- Q 保存每个实际请求输出行的完整 float32 词表向量，即每个 prefill chunk 和每个后续 decode 的末行。它不是全 prefill 行捕获或 KV 字节证明。Q 计时含捕获开销，不得作性能样本。
- `run_session.py` 默认仅预览命令；显式执行才创建一个自有进程、保留 stderr、预扣账本，10 分钟无进度/总 6 小时触发终止。无 ETW、系统权限变更或后台服务，不承诺驱动挂死后的清理时长。只支持串行、没有自动重试。
- P/G 分析分开；16 根等权 log-ratio、长度分层 root bootstrap 20,000 次。缺失、失败、重复、不同工作量不会被悄悄删掉后凑出完整推断。

## CPU-only 操作
真实候选 JSONL 每行包含 `root`（稳定唯一字符串）、`domain`（code/math）、`source`（固定版本来源）、`tokenizer_identity`、`prompt_ids`（1..768 个非负整数）、`continuation_ids`（恰好 128 个真实 token）。同一真实 tokenizer 语义还需由导出程序证明，整数检查不能代替它。不以 padding 或测试样本填正式面板。

```powershell
python -m unittest -v
python -O -m unittest -v
python experiment.py prepare candidates.jsonl prepared
```

以上不加载模型或运行 native。已有输出目录不会被覆盖。

## 原生编译，但不执行
M 使用完整 llama.cpp commit `0fb8f157702702f33f4e018de8701b2569a1bc28`。在配置好 MSVC/CUDA 的开发 PowerShell 内：

```powershell
cmake -S . -B build-M -DLLAMA_SOURCE_DIR=C:/path/to/pinned-modern-llama -DGGML_CUDA=ON
cmake --build build-M --config Release --target rtx244_worker -j 4
```

不要为确认构建而启动 worker/ctest。DLL 必须来自该完整 build，不能将现代 DLL 塞入旧 frontend。云端用该 commit 的真实公开 llama/ggml headers 做 C++17 **syntax-only** 检查已通过；未进行 MSVC/CUDA 编译链接。

R 必须定位论文使用的完整 legacy 源码与运行配置。当前没有取得本机源码，**尚无已验证的 R port**。若旧 API 不同，只做最薄 memory clear/参数兼容 port，保留数学路径并用历史 fixture 核验。不能把现代 worker 的重复构建冒充 R；如必须实质改 R，先重新定义比较。

## 仍需完成
1. 绑定真实 R 源码、两臂运行库、同 GGUF/tokenizer、显存/磁盘与执行窗口；核实全 offload。当前没有主机资源证据。
2. 导出真实候选 token 面板，冻结模型/源码/配置/输入/编译器/计时合同的一份简洁 manifest。
3. 每臂绑定**独立 native reference driver**。Q 只是 adapter 捕获，不是独立参考；按 PLAN 的 2 根×4 请求×2 臂=16 次，核对 driver/adapter/repeat/reset-reuse 的实际输出行完整向量和状态边界。若选择全 prefill 输出，标为资格变体，不能混入正式计时。
4. 资格、失败和重试同样必须进一个累计账本。执行器支持相同 schema 的 Q session，但还未实现独立 driver 的资格流程，不能略过这 16 次或开新账本绕额度。
5. 现场资源和执行摘要齐全后取得 GPU 授权。此 PR 与 CPU 编码不代表运行批准。

命令预览：
```powershell
python run_session.py prepared/00_P_R.json --exe C:/path/to/R/rtx244_worker.exe --model C:/path/to/model.gguf
# 原生资格与授权完成后，才给命令加 --execute；按 00..11 顺序选 R/M executable。
python experiment.py analyze prepared --mode P > primary.json
python experiment.py analyze prepared --mode G > greedy.json
```

不要直接运行 worker 绕账本，不要并行。执行器从账本首次尝试起计 6 小时，每 session 预扣全部请求，失败不返还；重试保留失败目录并复制累计账本，不能用空账本重置。总计 228 请求/204,288 rows/18 deployments 仍是待批准提案。Q 所用独立 driver 也须纳入同一预算。

## 验证事实
21 项 Python 标准库测试在普通及 `-O` 各通过一次，含输入/排程/统计异常和真实 CPU 子进程成功、失败、缺回执、超时。C++ 对真实 pinned headers syntax-only 通过。Windows build/link、R port、真实 panel、独立 native 资格均未完成；无性能结果。

下一步是现场接线和资格，不是重建监控系统。旧 4096 物理 launch 合同仍未闭合，也不适用于宣称本新预算已获批准。
