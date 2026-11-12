# e04 前端冻结构建

本目录交付 Windows 原生前端的可核对编译与链接证据。它不是 GPU 资格或性能结果。新前端 EXE、数值 DLL、模型与 CUDA 初始化均未执行。

最终编译结果位于 `recovery-v1/BUILD.json`，两个 EXE 位于 `run-v4/build/{loop4,packed}/bin/worker.exe`。`SOURCE_IDENTITY_v4.json` 绑定全部 14 个前端源码；相对 e03 的 source-v4，仅 `e03_binding.hpp` 中预算 epoch 字面量改为 e04。已有状态机、捕获、输出所有权、事务失效及 `require_native_release()` 的无条件拒绝保持原实现。

`run-v4/PREPARED_INPUTS.json` 与 `run-v4/FREEZE.json` 在 loop4 编译前绑定源码、完整私有 Zig exe/lib 树、观察到的外部头文件、nlohmann、固定 core/CRT/archive 二进制依赖、编译/链接命令、环境及实际生成工作流。私有输入使用 Win32 `GENERIC_READ + FILE_SHARE_READ` 句柄拒绝写入和删除。仅对自己的副本做过锁失效测试；旧材料未加锁或修改。

每臂实际 `-MD` 记录与同参数的最终 `-M` 预扫描严格比较，共 1,051 个文件；实际 `-v` 与预扫描 `-###` 中的 CPU 为 arrowlake-s，117 项特性逐项一致。依赖解析拒绝空、截断、多规则、变量、错误目标和错误源；CPU 解析拒绝缺失或多个真实 cc1 命令。最终生成的 object 在链接前另外锁定。

v4 的 loop4 编译和链接成功后，细粒度 archive member 解析保守拒绝了同名 COFF 成员歧义。保留完整 `BUILD_v4.log`、原 trace、map 和二进制。新的 `recovery-v1` 重新核对并锁定全部原输入和 loop4 产物，只编译尚未执行的 packed；不重复 loop4。两个臂的锁区间分开记录，不声称一个连续锁区间覆盖全部构建。

最终采用完整 archive 容器闭包：每臂 33 个 archive 的全部字节在链接前冻结，实际 LLD `/verbose` 的 archive 路径、直接 object、member 标签和 map 均落在该闭包中。`*-WHOLE_ARCHIVE_WITNESS.json` 为该范围的 PASS；精确的同名 member occurrence 为 **NOT_ATTESTED**。新的 `link_witness_v2.py` 只补充准确的弱别名证明，后续 C++ 解码名歧义仍保守拒绝，不冒充完整 member 证明。

`HOST_ARTIFACTS_v4.json` 从磁盘解析两份最终 PE，记录 EXE hash、imports、TLS 是否存在、完整输入清单 hash 及 C 卷标识。未发现直接 CUDA/数值模块 import。TLS/CRT 初始化未执行，Python 解释器/标准库和可变 Windows 系统 DLL 不属于冻结范围；本轮没有重编既有 core/CRT archive。

复核入口是 `recovery-v1/{PREPARED,FREEZE,POSTFREEZE,BUILD}.json`、原 `run-v4/RECIPE.json`、原始编译/链接日志与实际 `.d`/`.map`。确切执行命令保留在这些记录及 `PREPARE_v4.log`、`BUILD_v4.log`、`RECOVERY_*_v1.log`。重新构建应使用独立的新输出目录和新冻结；现有命令含绝对输入/输出路径，不能直接覆盖执行。

本目录新增冻结、真实 CPU trace 和容器闭包边界测试，普通 Python 与 `-O` 均通过。未重跑 e03 的旧资格测试套件。模型请求、target/draft rows、GPU launch、warmup、原生捕获和 GPU 时间均为 0；A/B/C native 资格、真实请求链及服务价值均为 **NOT_RUN**。数值 DLL 如有外部绑定，也只代表磁盘产物身份，不能解除 native 门禁。

`DEPLOYMENT_BINDING_v2.json` 现已从外部绑定最终新数值 DLL（SHA `2307f64f…96ae8ad`）、两个前端以及编译/链接冻结记录。数值 DLL 来自 145 个全新 v2 TU 和独立 link-v3；不声称连续的 compile/link 锁区间。`expected-modules-v1/MODULE_CLOSURE_v3.json` 绑定 9 份本机 DLL 磁盘副本及 248 项非系统 import/export 名称检查，所有 A/B/C 使用同一预期目录。base/CUDA 四项与三项 MSVC runtime 共七项，均与旧 audit 中 loop4 和 packed 两个角色的固定 expected pin 完全相同。`vcomp140.dll` 的旧运行身份未知，当前 System32 副本明确标为 **PROPOSED_NEW_MODULE_IDENTITY_NOT_NATIVE_QUALIFIED**。静态 PE 名称闭包、文件存在和 hash 不证明语义 ABI、数值兼容、动态 driver/API-set 解析或实际模块加载；这些均为 NOT_RUN。DLL 字节不进入公开交付归档。

本文件由 README_ZH.md 追加修订而来，修正此前关于三项 MSVC prior pin 缺失的保守描述；实际旧 audit 已存在这些 expected hash。旧文件与全部二进制保留不变。当前状态入口为 STATUS_v2.json。
