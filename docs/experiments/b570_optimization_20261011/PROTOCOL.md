# 自主核验、有限优化、独立确认

## 1. 平台与资产核验；无推理前封存 F0A

只在真实 B570 主机执行。实际读回本 PR/head，恢复 #82 native 源码/程序/DLL 及原始 hashes；所有新输出放在新目录。零 forward inventory 记录 Windows/CPU/RAM/driver、电源模式、B570 exact Vulkan device、显示路由、程序/DLL/source SHA 和模型完整 bytes/SHA。HF LFS metadata pin 不等于本地完整文件已核验。实际 runtime dump 检查目标和每种草稿的全部词表字节/类型、BOS/EOS、每个 EOG 标志及 suppression，保留原生 compatibility guard。提示模板只用 target，一次渲染的 native prompt IDs 供所有 arms 使用。

静态核验无需等待日期。准备自己的 12 个已曝光 discovery 题（6 MBPP/6 GSM8K）、合成边界题，绑定完整历史曝光账本及 RTX #84 已冻结的全部 24 题。确认题此时只预留独立池，不展示给优化选择器。F0A 冻结预算、完整探索空间、源程序、资产 pins、discovery 全题及历史排除集合；commit/push 并读取 actual remote Git blobs 核验。此后才能进行任何本轮 forward，包括 warmup、token compatibility 辅助 decode。

零 forward native load 关闭 hidden warmup；必须由实际 source/日志证明，没有隐含 decode。加载同一 family 最多 8 次（ordinary 与两种 draft 的必要上下文组合），计入 8 小时生命周期。预算在模型 worker 内测量；全 GPU layer counts、KV residency、dedicated budget/usage、无 spill 和工程 peak 都需要 native 证据。512 MiB 门槛未满足则停止该配置，不以 CPU offload 偷换范围。若只 Q4 可运行，明确是新的草稿配置，旧 Q8 pair 状态仍记录为 OOM/不足/未知。

## 2. 有界工程与选择

固定 greedy seed123、单 seq、ctx1024、batch512、F16 KV、FAoff、全 GPU、输出 cap128。普通 UB 网格 32/128/512，stock ordinary UB128 独立保留。12 个 discovery 题各两遍；选择所有题完整、与 stock 普通输出全一致且两遍几何均值耗时最低的 ordinary 作为 R_prod。stock 不合格则先解决实现，不能使用别的 ordinary 掩盖不稳定输出。

最多 12 个 C：2 草稿量化 × 2 已验证支持的模式 × k_max1/2/3；unsupported 不跑但保留原因。target prefill UB 取 R_prod，draft UB1。先用 tiny synthetic 确认 batched query/KV rollback 与原生 cap/EOG 提交，再在整套 discovery 比较。变长接受数必须记录，k 是最大 proposal 长度，不假装每步都接受 k。每次改实现都保留版本和已消费请求；空间和预算不得通过“新版本”重置。两个 mode 各配一套相同 target 路径的 M_match。

基础上限：ordinary 72+3 warm，C 288+12 warm，M 48+2 warm；最终候选与 stock ordinary 的 2 个合成边界题 × caps[1,2,3,4,31,32,128] × 2 arms × capture on/off =56 请求+4 warm，共 **485**。hard cap **640** 包含所有工程 forward/隐含 startup/warm/辅助 decode/失败尝试；余量 155 只做已列空间的修复和门槛，不增加候选、重选题集或扩大 k。开始前以 START fsync 记账，失败也占预算。边界 raw 提交数组必须在 native commit 时满足 cap/EOG，不能在 Python 比较时裁剪；proposal/verify 的未提交工作另外全部保存。

捕获状态只用于工程门槛。正式均关闭详细 trace；所有 arms 相同的轻量计数/完整提交 IDs 与 stop metadata 通道，持久化与 hash 放在主计时之后。修复 C 的单 token 文件写入、冗余同步、重复图构建时，同时验证 M/R 计时与数字路径；若更改 numerical backend，须额外核验 stock 与候选 target-only 等价。

先选择最快合格 ordinary，再对每个 C 使用完整 discovery 两遍的 paid 成本。要求 R_prod/C 每遍 >1.05、M_match/C 每遍 >1、原始输出全部等价、memory/边界/capture/reset 等门槛全通过。score 为两遍 R_prod/C 的较小值；并列依次取较小 k、较小实际峰值、固定 candidate_id 字典序。不按题挑赢家、不用确认题换配置。不达门槛则提交 FEASIBLE_NO_PROMISING_GAIN 和所有观察，正式不跑，不能把 native 是否可运行写成加速证明。

## 3. 提交可行方案；封存 F0B 后自动确认

核验结束必须创建新的 B570 可行方案 Draft PR，包含机器 inventory、受 hash 绑定证据、所有候选矩阵、搜索消耗、原始负结果、选中配置或阻塞、确定的运行指令和本地控制器。仅提交人工勾选的 true 字段不足以核验 native：同时绑定实际代码、二进制、日志和独立负向测试。CPU 工具的 SELFTEST_PASS 不是 B570 实验通过。

若候选有希望，选择器输出封存，再从排除历史/探索/当前 RTX 全题的池生成 **全新 24 题（12+12）**，实际题目 bytes、prompt IDs、slot schedule 及普通代码、候选实现/所有 DLL、计时/统计冻结到 F0B；actual remote readback 必须先于第一个确认 forward。确认题相同 family 各 arm 共用；Llama 若在看过 Qwen 确认后才选择，必须用另一套新题，且声明跨家族选择影响。两 family 不共享确认题。

每 family **2 个连续会话 × 4 轮 × 4 arms × 24 题 =768**正式、32 个 synthetic cap128 warmup，总 800；每 arm 192 个实际 paid 请求。即使 R_prod 恰好 UB128 也实际支付 R_stock 和 R_prod，不能把一条记录伪装成两个请求。每 block 新 resident worker，加载/卸载日志独立，10 秒固定 idle 后一个固定 warmup，再做 24 题；顺序用预封存 balanced Latin rotations，两 session 相反，并绑定完整 schedule/hash。温度可能不可读，固定时间规则不依赖温度阈值。新短等待规则只适用于本研究，不改变进行中的 RTX 冻结条件。

主计时所有 arms 一致：resident 全部 prompt/JSON 准备开始，到发送、完整 response 收取、native 提交 ID/stop metadata 解析核验完成；磁盘持久化/hash 不算主计时但记录总成本。整个 proposal、reject、verify、rollback、目标 decode 与末端同步均必须包含。进程加载、固定 warmup、idle、工程消耗另报实际总 wall/lifetime，不从对某配置有利的子区间替代 whole request。

本地控制器串行运行并前置预算检查，失败原位保存、不补跑 formal、不借用另一个 family 预算、不自动降精度/offload/换 prompt。边界/capture/全 GPU gate 若运行中失败，受影响比较 qualified speedup=null。主机重启可读取 ledger 保留已执行 slots，不能生成一个新的“完整”研究隐去失败。控制器无 AI/API 调用，简报在 block 之间按阶段或每 10 分钟写一次；无需持续聊天轮询。

## 4. 判断收益与交付

每个 session/task/arm 取四轮绝对请求耗时中位数，再算 24 题等权 GM ratio；两个 session 的 log ratio 等权平均。所有 baseline 必须实际完整、stock R 每题八次输出稳定，四 arms 同题原始提交 IDs、length、terminal、stop reason 全一致。每项比较必须包括 192 个完整且有效 paid records，少一项也不能发布该项 qualified ratio。

主比较 R_prod/C；同时报告 R_stock/C、M_match/C、两 domain、每题回归、每 session 比值、proposal/accept/verify/sync 成本、峰值显存、完整搜索成本。POSITIVE_DESCRIPTIVE 要求主比较每会话 >1、整体 ≥1.05、matched 每会话 >1，且全部实现/完整输出门槛通过。低于此门槛但有真实小收益照实报数值，不称实用正向。两 session 不输出日期 t-CI，不宣称跨日期稳健。

一 family 上限 640工程+800确认、8小时owned lifetime；两 family最多2880请求/16小时，outer7天仅作失联停止线，无日历等待。任何 stop 状态均生成可恢复结果包、账本、机器决定及中文报告；CPU 独立复算和 actual Git-hosted 恢复/readback 后更新结果 PR。不 merge，不改论文结论，不自动发布。
