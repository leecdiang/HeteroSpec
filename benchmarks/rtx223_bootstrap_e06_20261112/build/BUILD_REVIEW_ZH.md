# e06 构建及磁盘身份证据

正式探针和 CPU 替身使用同一份 `main.obj`，分别链接 `native.obj` 和 `fake.obj`。父控使用的 ETW 观测 DLL 单独编译。三个目标均为 x64；数值库、CUPTI 和 NVML 都没有被列入链接输入。正式探针通过运行时解析的代码仍保留在 `native.cpp`，须由获准的 runner 在独立窗口按合同驱动。构建和 PE 审查只读取文件。

| 本机保留的批次 | 可复查的证据 |
|---|---|
| `observer-attempt-001/` | `observer.cpp` 与真实头文件依赖共 199 项。产物普通导入为 ADVAPI32、KERNEL32、tdh，导出 5 个 `hs_trace_*` 符号。 |
| `probes-attempt-001/` | 首个冻结探针和替身的源码、命令、日志、产物与 PE 回执。本版本保留供比较。 |
| `probes-attempt-002/` | 本轮选定的 v2，增加子进程阶段时间检查、记录丢失读数是否有效、回调收尾及错误原因。真实后端和替身只普通导入 KERNEL32。 |

每个批次在空目录开始，`RECIPE.json` 记录编译、链接和环境。编译前持只读且拒绝写入/删除的 Windows 文件句柄，再为受控输入计算 SHA-256；`FROZEN_INPUTS.json` 与源码副本、编译器、头文件搜索根、工具和库参与同一持锁会话。编译后检查每个翻译单元的 `/sourceDependencies`，新对象在链接前另行锁住并登记。检查链接器报告的实际检索库、PE 的直接及延迟导入、构建前后成员关系和哈希。拒绝复用批次目录。此证据覆盖记录的代码生成输入，未封存 Windows 系统映像、运行进程内存或硬件。

`DEPLOYMENT.json` 固定 e05 的九个模块、CUPTI、System32 的 nvcuda 与 nvml。匹配 System32 loader 字节定位本机 DriverStore 包，并登记特定 x64 入口及其依赖。目录内其他 DLL 不因位于该目录而获得准入。只读解析普通 PE 导入及 ordinal/命名转发，并以本机 `apisetschema.dll` 的 v6 表定位候选 host。额外记录延迟导入边；仅有导入名不能证明实际加载路径。`DEPLOYMENT.edges.json` 保留磁盘解析边。将来若实际映射到清单外文件，runner 必须拒绝后续工作。

`PYTHON_INPUTS.json` 绑定指定基础解释器、安装根文件、DLLs 和标准库，包括既存字节码；命令是 `python.exe -I -S -B`，site-packages 不在导入路径。B 的入口依赖可信宿主创建该指定解释器。进程开始后的校验能检测磁盘身份差异，不能追溯认证进程启动前的内存状态。

`RELEASE_INPUTS.json` 锁定本轮交付的完整本机路径、文件 ID 及哈希。`REVIEW_IDENTITIES.json` 提供适合 PR 审阅的摘要，包括原始冻结表的 SHA、各构建产物和部署身份。两份回执只界定待审批对象；缺失的现场证据、失败的前置测试和用户批准各自独立。实际 CUDA 路由、数值正确性及性能保持 NOT_RUN。
