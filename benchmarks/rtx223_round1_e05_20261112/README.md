# Windows RTX 5070 Ti · 第一轮 e05

**原 4,096 次全生命周期物理 launch 合同未闭合。第一轮仍为 INCONCLUSIVE。** 本目录接续 [e04](../rtx223_round1_e04_20261112/e04/RESUME_REPORT_ZH.md)，审查起点为 #223 的 `7ce00b3c72ecf72adcd6d3832d78c3d359dbb6ac`。本轮没有启动数值进程、普通加载数值 DLL 或进入 CUDA。模型加载、模型请求、输入/输出行、GPU context、物理 kernel launch、原生 GPU 秒及 GPU 捕获字节均为 0。这个零来自执行范围，未启动 GPU 观测器。

| 门槛 | 状态 | 证据与边界 |
|---|---|---|
| 原执行轮次与旧任务排重 | PASS，限答复时点 | #221 有完成回复；#223 原聊天的 e01–e03 均有结束回复。该聊天最新 e04 项只有用户消息，列表 idle、详情 systemError。另一个接续聊天的完成回复绑定 e04 提交。约 20:50（上海）所有者确认三处均没有遗留、排队或延迟的 GPU 任务和 lease。[会话与队列取证](THREAD_EVIDENCE.json) |
| 宿主只读取证 | PASS，限采样范围 | 367 个进程、204 个计划任务、313 项服务；177 个进程命令行不可读。未见专用 worker；已知文件锁及 UUID mutex 缺席。e01、e02 账本 attempts 各为 0。实际窗口仍须保证所有提交者遵守单一 runner/lease。[宿主取证](DEDUP_HOST.md) |
| 源码、构建与磁盘依赖身份 | PASS，限磁盘字节 | 从钉住的 Git tree 校验报告与清单，重新读取 3,546 个源码、12,706 个受控构建输入、145 个对象及其依赖文件/日志、两个前端、链接 DLL、九个部署 DLL 及五份旧账本。未重新编译；VCOMP 的历史身份仍未知。[逐类复核](DISK_AUDIT.json) |
| 原控制器 CPU 故障测试与 native 默认拒绝 | PASS，限 CPU | 原 26 项测试在普通 Python 与 -O 各通过一次，覆盖边界、身份、重入、未知成本、失败清理和不退款。重新执行纯 CPU preflight，首个 worker bootstrap 即拒绝，可信 proof 表为 0。[普通记录](CPU_normal.log) · [优化模式记录](CPU_optimized.log) · [拒绝结果](NATIVE_REFUSAL.json) |
| 方案 A 可执行硬上界 | FAIL；native 准入 BLOCKED | 父控能拒绝整个进程。若允许加载，预算导出只有在 LoadLibraryExW 返回后才可调用，缺少加载期间的受信物理上界；闭源库内部、延迟初始化、异常退出与 driver 回收也缺覆盖。总上界为 null。自有 graph 编译关闭和局部 direct 守卫只约束各自路径。[12 类路径覆盖矩阵](A_PATHS.md) |
| 方案 B 的磁盘入口与预算设计 | PASS，限提案与静态入口 | 只读解析预期 cudart 的两个设备查询与 CUPTI 的十个导出，核对 SHA、非转发及有效 RVA。实际加载身份、ABI、计量、设备可见路由、探针与 runner 的实施、真实独占均为 NOT_RUN。执行授权 BLOCKED。[入口记录](BOOTSTRAP_EXPORTS.json) · [独立预算](B_BOOTSTRAP.md) |
| 第一轮资格、真实请求与性能 | NOT_RUN | 22×3 共 66 格均未执行。没有 q8 原生正确性、配对计时、真实消费者链、完整服务收益或 5% 结论；第二轮未启动。 |

### 独立预算的适用范围

方案 B 提议在单一已确认独占窗口使用一个无模型探针加载一次数值 DLL，查询一次可见设备数；仅在结果为 1 时查询 ordinal 0 的 UUID。设备固定为原 RTX 5070 Ti Laptop GPU。模型、forward、显式 context 创建及主动 kernel 均为 0。目标是取得实际加载与设备身份、检查计量通道能否关联两次 API。零 kernel 记录仍缺正例验证。即使观测与退出都成功，也不能据此签发方案 A 的证明。

拟议窗口为 2026-11-13 20:00–20:05（上海），尚未预约或排队。80 秒后停止新操作，90 秒触发自有 Job 的终止处理；设备侧清理时长和隐式 launch 数未知。Job 提交内存、日志容量及显存采样停止线详见提案。实施前还需固定无模型探针和 runner 字节、核对系统/驱动实际依赖候选，在同一 Windows 环境用无 CUDA 子进程验证 Job、失败清理和计量回执处理。实际运行前须取得用户对定稿身份、操作、窗口、独立预算及隐式工作风险的明确批准。此处没有启动入口、B 账本或预订。

原 family 仍沿用 256 请求、合计 1,000,000 target/draft rows、10,800 原生 GPU 秒、4,096 物理 launch、2 GiB 捕获和原分项/失败余量。e02 规范账本仍是唯一原账本。旧预算、参考、失败记录和论文无写入。B 完成即停，任何资格、计时或第二轮需另立协议并授权。

### CPU 复核

本机以 Python 3.11 从含 e01/e02/e04 完整交付与 Git 仓库 `repo/` 的原工作区复核。下列操作仅做摘要、磁盘 PE 解析和既有 CPU 故障测试。Git 中的精简交付与本机完整构建包的区别见路径矩阵。

```powershell
$e04 = 'rtx223-round1-resume-20261112-e04'
$e05 = 'rtx223-e05-authoring'
py -3.11 -I -B -S "$e05/audit_inputs.py" .
py -3.11 -I -B -S "$e05/inspect_bootstrap_exports.py" $e04 'E:/rtx170/profiler/sdk/nvidia/cuda_cupti/bin/cupti64_2025.2.1.dll'
py -3.11 -I -B -S -m unittest discover -s "$e04/e04/budget" -p test_lifecycle_budget.py -v
py -3.11 -I -B -S -O -m unittest discover -s "$e04/e04/budget" -p test_lifecycle_budget.py -v
```

[机器可读结论](RESULT.json) · [独立内容复核](REVIEW.md)
