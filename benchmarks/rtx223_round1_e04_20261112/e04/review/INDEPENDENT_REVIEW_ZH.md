# e04 独立审查：INCONCLUSIVE，继续关闭原生入口

本轮完成了可复核的 CPU、源码冻结和实际数值 DLL 构建准备。它没有建立新的数值资格、完整模型 kernel 预算证明或系统收益证据，不能启动第二轮。原生请求、CUDA 初始化、数值 DLL 正常加载与导出调用、模型加载和 GPU launch 均未执行；旧 41/18 项及此前 counter 套件没有重跑。

| 关口 | 独立结论 | 证据范围 |
|---|---|---|
| 旧材料保存 | PASS | 原 e03 1749 个文件核对 bytes/SHA256/Git blob；原 core 3540 个文件、e03 完整源码 3546 个文件、5 份旧账本重新计算哈希均匹配；规范账本仍为 1 family、0 attempts |
| 生命周期预算 planner | PASS_CPU_MOCK_ONLY | 26 项新测试在普通 Python 与 -O 下独立通过；直接读取 52 个测试目录中的 SQLite/哨兵记录，4097 超额持久化并阻止后续租约，未知实际成本不退款 |
| 编译前完整输入冻结 | PASS_PREPARATION_ONLY | 12706 个输入、3028201393 字节；完整 3546 文件源码、复制工具链/SDK、生成脚本、命令和环境固定；实际依赖与源字节独立复算 |
| 新数值 DLL | PASS_COMPILE_LINK_ONLY | 145 个 e04-v2 新编译对象，143 CUDA + 2 HOST；全部原始依赖、日志和对象哈希通过。另一次 link-v3 冻结 12861 个输入后链接，不复用 e03 或失败 v1 对象 |
| 新 frontend | PASS_CPU_BUILD_WHOLE_ARCHIVE_CLOSURE_ONLY | 两臂各 1051 个原始 -M/-MD 依赖及 117 项 CPU features 匹配；33 个完整 archive 容器已绑定。17 组同名不同 payload 的精确成员选择仍 NOT_ATTESTED |
| 磁盘 PE 身份 | PASS_OFFLINE_ONLY | 两个 EXE 与新数值 DLL 的独立 dumpbin 记录通过；未执行 EXE 或正常加载目标 DLL |
| 部署模块绑定 | PROPOSAL_ONLY | 只核对磁盘路径/字节。旧入口磁盘相等与旧审计合同 pin 必须分开；缺少旧 pin 的组件保持 UNKNOWN，不能声称实际 runtime 已绑定 |
| 完整生命周期物理 4096 约束 | BLOCKED | trusted native proof registry 为 0、完整 bound 为 null；在 worker bootstrap 前拒绝。CPU 公式和零工作拒绝路径不能证明可运行 profile |
| 原线程/正常宿主窗口 | BLOCKED | 原任务终态、排队 worker/lease 仍待确认；先前完整宿主快照只是瞬时证据 |
| 66 项 native 资格、真实 q8 A/B/C、请求链和完整服务成本 | NOT_RUN | 没有新量化 activation/完整输出/状态/时延样本，无相对 packed 的配对改善 |

新 DLL 为 `runtime/link-v3/bin/ggml-cuda.dll`，33851904 字节，SHA256 `2307f64f1f1f4d0bb4aba42e6f6793a29579c2af031e4dbadac77811096ae8ad`。29 个导出包含全部 13 个 runtime/budget 名称，CPU-only reentry 导出不存在；仍可见 CUDA/cuBLAS 导入和 fatbinary 注册入口。磁盘导出名不能替代函数执行、实际模块解析或数值资格。

e04-v2 编译与 link-v3 是两次明确的锁会话。145 个对象在完整冻结下新生成；原链接因受控环境遗漏 TEMP/TMP 而在 C:/Windows 临时文件处失败，随后对同一批新对象、相同 source/toolchain/library 和新链接环境重新冻结再链接。没有因为链接临时目录问题重复生成数值代码，也没有宣称连续持锁。Frontend 的恢复阶段同样明确区分锁会话；完整 archive 容器涵盖所有候选成员，因此精确成员歧义不等于存在未绑定的代码输入。

冻结覆盖编译源码、工具资源、SDK 和实际 include 依赖；保留原始响应文件、依赖、link trace/map 与失败记录。它不是所有 OS 文件打开行为、进程内存、Windows runtime DLL、driver、hardware 或完整 Python runtime/stdlib 的不可变证明。生成的中间文件属于编译输出，不能倒称为编译前已有输入。此前 e03 的 provider 中途同步及缺少逐次完整依赖时间见证仍保留，本轮没有追溯改写旧历史。

C 的完整源码与 e03 uniform tree 相同，仍是 Q8_0/F32、q8/g2 两组独立四列 accumulator 的窄实现。已有 case4 的 K/lane/reduction 顺序与权重片段跨组复用是源码结论；本轮未执行 quantizer、dispatch 或输出比较。A→B 的布局/dispatch 合并与 B→C 的 CTA 数、资源和权重复用影响必须分别测量。新构建的 registers、spill、shared memory、occupancy、DRAM、L2 与时延保持 UNKNOWN/NOT_RUN，不移植旧 epoch 的数值，也不把 speculation 的整体 11%–25% 收益计入 C。

完整 kernel 口径覆盖原 family 的 target、draft、runtime 和 standalone kernel；DMA/API 调用数不机械加入 kernel 配额，静态调用点不等于物理 kernel 数。只观察 dispatcher、standalone 或拒绝所有工作都不能填补 DLL 构造、初始化、加载、库内部、graph、fallback、真实消费者及 teardown 的完整成本证据。Native provider 仍固定返回 -6，frontend/registry 在数值 DLL 加载前拒绝；JSON 自声明不能开闸。

保留的准备失败包括初版依赖/CPU 解析缺陷、CPU mock 账本隔离/未闭合租约/策略摘要缺陷、缺少 VC/Auxiliary/Build 支持文件的 nvcc OS 识别失败、真实 nvcc 双 source 依赖格式、TEMP/TMP 链接失败、frontend 准备与 CPU 元数据比较失败，以及精确 archive 成员见证的歧义。修复使用新版本和新冻结；这些失败不是 GPU 性能负样本。

下一步仍属第一轮：补原线程与 worker/lease 证据，在真正准入时重核宿主窗口；建立实际可运行且从 DLL/bootstrap 到 teardown 都具有可信 kernel bound 的 profile；完成实际模块绑定和 66 项资格，再做真实 A/B/C、bonus→seed→L4→correction/trim/pending 继续链与完整服务成本。仅补外部确认不足以解除技术门禁。原额度不变，复制工具/源码约 3.03 GB 属 CPU 准备磁盘量，GPU 捕获与真实预算使用仍为 0。

独立复算入口和哈希绑定见同目录 `FINAL_REVIEW.json`、`NATIVE_FINAL_RECHECK.json`、`frontend-final/` 与 `lifecycle/final-independent-v1/`。结论为 INCONCLUSIVE，第二轮 DO_NOT_START。
