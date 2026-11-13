# 提取诊断与固定完整后端的边界

固定源码仍为0fb8f157702702f33f4e018de8701b2569a1bc28。旧B保持旧headers、量化器与四列MMVQ，完整输出参照e08真实首层捕获。U提取原样device定义及D4量化，使用新headers；没有让新版普通量化器或算术顺序改写旧B。

形状为同一个K=M4096、8-token F32输入。完整上游Q8_0 few-row gate要求非Spark ne1≥5、≤24、K≥2048并整除所选stage512、满足对齐；原始[4096,8,1,1]适用，旧packed[4096,4,2,1]不适用。完整上游dispatcher在few-row适用时跳过MMVQ，随后选few-row，不能根据逻辑“8行”推断packed也选U。

本轮探针的两臂是普通<<<>>> launch、相同非阻塞stream、无graph API。U为Q8_0/ncg1/nmt1，256个CTA、128线程、69632B动态shared。B为2048×2个CTA、128线程，旧packed stride。相同F32/权重，但量化表示与归约合同不同。投影event外量化一次，event内5次投影；完整算子event内5次量化+投影。分配、输入拷贝和全部验证在event外；event可能包含host提交间隙，不能把它称为纯硬件指令吞吐或服务延迟。

完整上游默认并非该探针：`common.cuh` L1495–1546通过`ggml_cuda_kernel_launch`选择cudaLaunchKernelEx的programmatic-stream属性；`ggml-cuda.cu` L844起默认允许PDL，除非GGML_CUDA_PDL=0，并用加载kernel的cudaFuncAttributes.ptxVersion≥90判断是否支持（这里不要混淆成PTX ISA9.0）。本轮提取host没有调用该PDL selector，称为PDL0等价；device PDL helper保持原样。

llama.cpp根CMakeLists L171默认将GGML_CUDA_GRAPHS打开；ggml子项目单独配置的默认值不同。正式graph compute还有capture/update/chunks/replay和pool等行为。不能用无graph、PDL0的提取算子数据替代完整上游默认后端或默认服务结果。

## 完整后端的实际构建

在独立full-backend-002/src副本，以官方portable CMake3.31.8、Ninja1.13.1、冻结MSVC14.44.35207和CUDA12.9.86构建ggml-cuda目标。CMake/Ninja包分别核对官方SHA清单/官方release asset digest，未做系统安装或配置修改。目标sm120a-real、GGML_NATIVE=OFF，GPU数学/PDL/graph默认选项保留；cache确认GGML_CUDA_GRAPHS=ON。CUDA compiler identity成功，161步完整编译/链接成功，约815秒，生成38,267,392B DLL，SHA256见FULL_BACKEND_BUILD_IDENTITY.json。未加载该DLL。

full-backend-001保留首次配置失败：Windows反斜杠路径在CUDA host compiler参数中被吃掉；v2改为正斜杠路径后配置成功。OpenSSL/Git缺失只影响HTTPS/嵌入build-info，未影响本CUDA目标；外部固定commit和源码blob记录提供身份，不假称DLL内嵌Git版本可用。

CMake3.31会在CUDA ABI成功后调用设备探测二进制，即使指定非native架构。本次显式CMAKE_CUDA_COMPILER_FORCED=TRUE跳过该执行步骤，编译能力由实际nvcc编译/链接另证。没有改变隔离或Windows安全设置，也未把CUDA设备探测混入CPU阶段。构建日志和源码前后哈希保留；完整后端是COMPILE_PASS、RUNTIME_NOT_RUN，并非已完成默认后端实验准入。

最小复现是full_backend_build_v2.py内固定命令：官方CMake、Ninja、冻结compiler/toolkit，-DGGML_CUDA=ON -DCMAKE_CUDA_ARCHITECTURES=120a-real -DCMAKE_CUDA_COMPILER_FORCED=TRUE，接着`cmake --build … --target ggml-cuda --parallel 2`。不要省略FORCED或改native后再称CPU-only配置。两次构建目录和失败均保留，未覆盖e10或任何旧基线。

本轮完整后端不运行的缺口是执行控制：尚未将dispatcher、初始化、graph capture/replay中作者显式调用逐一纳入可在提交前拒绝的计数，也未将这个新DLL及其全部实际加载依赖纳入受限执行闭包。成功链接不消除这些缺口。500次预算仅覆盖已证明的提取两臂四个调用点，不把编译成功当作完整默认后端性能证据。

上游源码：[mmq-few](https://github.com/ggml-org/llama.cpp/blob/0fb8f157702702f33f4e018de8701b2569a1bc28/ggml/src/ggml-cuda/mmq-few.cu)、[PDL/launch wrapper](https://github.com/ggml-org/llama.cpp/blob/0fb8f157702702f33f4e018de8701b2569a1bc28/ggml/src/ggml-cuda/common.cuh)、[dispatcher/PDL/graph](https://github.com/ggml-org/llama.cpp/blob/0fb8f157702702f33f4e018de8701b2569a1bc28/ggml/src/ggml-cuda/ggml-cuda.cu)。当前编译生成PTX8.8，近似primitive依据也可固定到[CUDA12.9 PTX8.8](https://docs.nvidia.com/cuda/archive/12.9.0/parallel-thread-execution/index.html)，与新合同2ULP/1ULP规则相符。
