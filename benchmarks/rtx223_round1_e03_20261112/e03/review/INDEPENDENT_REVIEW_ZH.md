# e03 独立审查：INCONCLUSIVE，GPU 入口继续关闭

本审查只涵盖 e03 新增源码、CPU 计数器、实际数值 DLL 的编译链接与磁盘身份。没有正常加载数值 DLL、调用 CUDA、加载模型或执行 GPU 请求；没有重复 e01 的 41 项或 e02 的 18 项测试。CPU mock 的 4096 次计数不是 4096 次 GPU launch。

| 关口 | 独立审查结论 | 证据边界 |
|---|---|---|
| 旧材料保存 | PASS | 原 e02 764 个文件及原数值 core 3540 个文件重新计算 SHA256，均匹配；e03 的文档、打包入口可以另行修改 |
| 全局预算 CPU 语义 | PASS_CPU_ONLY | 独立执行 16 个新增 CPU mock 场景：共享 TU 状态、并发 4096 上限、继承 reservation、不退款、不重配、重入拒绝、opaque 拒绝、自己进程 failstop |
| 默认 native 入口 | BLOCKED，正确 | 最终 provider 非 CPU-test 构建固定返回 -6；frontend 在任何 LoadLibrary/模型初始化前无条件拒绝，外部 JSON 不能解除 |
| 数值 C backend 集成 | PASS_LINK_ONLY | 实际 DLL 已链接，145 个对象逐一重算；141 个复用对象与原成功编译记录一致，4 个新对象成功；最终 provider 恰好链接一次，旧 provider 对象排除 |
| 实际 DLL 磁盘身份 | PASS_PE_ONLY | AMD64 DLL，33,850,880 字节，SHA256 bcdb7642d32609c9242dc8aaecfadfb9f4e082ac8cfeccf5de6b7466546eb24b；独立 dumpbin 原始导入/导出/头记录保留 |
| Frontend 准备 | PASS_PREPARATION_ONLY | 14 个源码、两个 EXE、链接输入与 22 个 preflight 原始日志匹配；6 项 identity-reader 测试的普通/-O 收据和源码绑定匹配 |
| 实际数值 DLL 普通加载/metadata 调用 | NOT_RUN | 两次普通加载属于无 CUDA 的自有 mock DLL；数值 DLL 只有磁盘 PE 检查 |
| 完整模型物理 kernel 口径 | NOT_QUALIFIED | raw/库/graph 分支静态改写及 CPU mock 未证明真实模型路径上的全部 kernel 计费关系；当前保守 profile 也尚未证明能运行完整请求 |
| 原执行线程与正常宿主窗口 | BLOCKED | 原线程 API 不可用，缓存标题/时间没有终态时间线；5 个可见进程只代表受限命名空间，不能证明宿主空闲 |
| 66 项 native 资格、真实 q8 A/B/C、真实消费者链、完整服务成本 | NOT_RUN | 没有新量化字节/完整输出/状态/时延样本，不能作系统价值判断 |
| 第二轮 | DO_NOT_START | 没有相对 packed 的配对改善、真实请求覆盖或完整服务净收益证据 |

最终 provider 的一个实现状态由所有已链接 TU 共享，CAS 约束计数，TLS 只负责重入检测。这里的范围是一个已绑定 DLL 实例，不能推广为任意重复加载模块之间的自动全进程合并。真实 worker 额度仍必须来自原 family 的持久 reservation，e03 没有新授予 4096 次额度。

对当前静态 inventory 的 149 个 runtime API 位置，独立分类为：59 个查询/错误/属性读取，59 个 event/stream 同步和生命周期，11 个配置，8 个 host allocation/pinning，10 个 device allocation/free，以及 2 个已有 kernel 内的 PDL intrinsic。它们不是 149 个隐藏 kernel，也不能相加当作动态 kernel 数。具体需要避免漏计的是 cuBLAS/CUB 等库的实际提交、graph replay、多 kernel library work 和 cooperative/extended launch 路线；当前补丁拒绝未计费库和 replay 路线。memcpy/DMA 没有被偷偷加入 kernel 配额；当前拒绝 memcpy/memset 是保守 profile 限制，尚不能证明请求可运行。

C 的源码仍为明确 Q8_0/F32、q=8、g=2 子域：`tmp[2][4][2]` 两组独立 accumulator；每个 K/lane 分片先加载一次权重 `v` 与 `dw`，再供两组四列使用；每个输出沿原 case4 的 K 遍历、跨 warp 部分和 lane reduce 顺序。它没有把 native specialization 宽度改为 8。最终 stage-v4 补足 K/M 相等、contiguous stride、实际 buffer type/device、分配区间、默认 precision、无 IDs/fusion、SM120/warp32/case4 geometry 检查，并在原 quantizer 前拒绝不支持 descriptor。实际数值与 dispatch 尚未验证；C 子域以外的 packed 路线没有因此获得资格。

独立从最终 MMVQ 编译原始日志重算：case4 为每线程 63 registers/3072 bytes static shared memory，C 为 91/6144，二者报告 stack/spill 均为 0。occupancy、DRAM、L2、时延仍为 unknown/NOT_RUN。源码权重复用与编译资源增加都不是速度提升证据。

机制归因仍需分开：A→B 包含原有布局与 dispatch 合并；B→C 在原 packed 一次 kernel 中合并两组 CTA，改变 CTA 数、每 CTA 工作量、寄存器和 shared memory，并使权重片段跨两组复用。B→C 不是再少一次 kernel launch 的证据，也不能将未来全部差距都归于 DRAM 权重流量下降。kernel-only 与共同量化/同步后的 operator 以及请求关键路径目前均无测量。

必须保留的失败和限度包括：早期 C ABI void guard 抛异常导致 CPU v1 三个 opaque 场景损坏结果；v2 Windows `OPAQUE` 宏冲突编译失败；v3 aggregator 对预期非零 failstop 退出误判，原收据保留并离线纠正；完整数值编译的 MMVQ private-type 和 include-path 失败均保留。最终 C ABI 使用状态返回或显式终止自己进程，禁止宣称通用 owner 可恢复；只有 DLL 内 graph callback 的 C++ 错误边界返回 GGML_STATUS_FAILED。若 worker 突然结束、实际计数未知，应按 supervisor 的持久 reservation 保守计费，不能由缺失输出退款。

第一批源码有一个明确 provenance 例外：安全子任务在批次期间将最终 provider body 同步至隔离的 `.cu`；精确时刻未记录，09:09:38Z 只是 catalog 近似时间。旧 body SHA74e727d1… 已保留，最终 DLL 只使用新鲜编译的 canonical 07f4b162… 对象。283 成员 CUDA catalog 除此项外匹配；另独立重算完整原/现源树和 delta，非 catalog 的唯一原成员变化是 inactive HIP profile 的 vendors/hip.h，已由 delta 绑定。没有每次编译的完整 include/dependency 时间戳证明，因此不宣称所有 code-generating 依赖在整个批次中都有不可变见证；未来 fresh GPU 候选需在编译前冻结完整依赖树。

建议下一步仍属准备：取得原线程终态和正常宿主窗口证据，冻结完整依赖及一套 A/B/C/draft/reference 的 graph/PDL/VMM 政策，证明一个实际可运行且全部 kernel 可计费的窄 profile，再在原预算内逐阶段解除资格关口。普通 CUDA DLL 加载可能执行 CRT/fatbinary 注册，不能把“metadata 函数体没有 CUDA”当成加载无 CUDA。任何这样的 native 步骤都不由本审查自动准入。

复算入口为 `e03/review/verify_final_bindings.py`；它只读取磁盘并使用显式失败检查，不依赖 Python assert。其结果、独立 16 个 CPU 原始日志、编译资源重算、独立 PE 原始输出、静态 API 分类分别见同目录收据。已有 speculation 相对 target-only 的收益没有被计入新 C 机制；e03 没有性能增量结论。
