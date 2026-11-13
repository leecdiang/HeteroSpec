# 最小复现与准入边界

固定源码和DLL身份见SOURCE_ARTIFACT_BINDING.json。编译入口build_link_only.py只调用MSVC cl/link/dumpbin，不执行CUDA、数值DLL、CMake设备探测或测试二进制。

1. 从已有e11/build-003/COMMANDS.json取冻结compiler环境；使用固定源码ggml/include。
2. 编译backend_api_link_only.cpp，定义GGML_SHARED/GGML_BACKEND_SHARED。它只返回15个API地址，没有任何后端函数调用。
3. link /DLL /NOENTRY连接既有ggml-cuda.lib和ggml-base.lib。
4. dumpbin /DEPENDENTS /IMPORTS /EXPORTS只读检查两个完整DLL及NOLOAD链接证明DLL；所有日志保留。**不可加载NOLOAD DLL**，其导入表仍会触发数值依赖加载。

这证明现有环境能够解析公共API，不证明运行时DLL闭包、GPU初始化成功、dispatcher实际选择或数值正确。没有生成可运行的GPU harness。

若仅考虑一张单node MUL_MAT图，最小公共API数据流应为：

```text
fixed CUDA device0, verify physical UUID under controlled admission
weight context: Q8_0[4096,4096], dedicated CUDA buffer usage=WEIGHTS, no PARAM/view
compute context: F32[4096,8], MUL_MAT output F32[4096,8], dedicated CUDA buffer
build forward graph, assert one computed MUL_MAT node
copy frozen weight/F32 operand bytes to these buffers
backend_graph_compute -> backend_synchronize -> tensor_get(full output)
free buffers/backend/contexts, preserve complete terminal receipts
```

该流程是静态设计，未在本轮执行。对于完整默认后端，还须记录实际graph/PDL、真实few-row分支、内部q/d、完整输出，并在任何潜在显式提交前确保该次预算可覆盖；图capture/replay不能仅按host函数调用次数计量。

可能的future实现可以为严格限定单node图证明保守每调用上界，或对direct及每次graph replay预先按kernel节点收费；本轮没有选择或验证实现，不把“只有两个源码launch点”当成已经闭合的执行合同。默认graph暖机、capture路径与replay路径需分别计入；内部quantizer/property变更、回退或不完整结果必须拒绝并保留回执。500/120不是物理生命周期硬界。

计时与验证有独立缺口：公开接口无法读取src1_q临时buffer、仅投影入口或私有stream；registry也不提供这些扩展。调度器callback对应图tensor，内部q8量化不对应单独ggml tensor/node。backend event_new禁用timing。只测graph_compute host墙钟可以作为不同边界，但不能与旧B CUDA-event数字作公平配对，也不能交付用户要求的完整量化检查与投影分界。

现有graph/PDL可通过环境关闭，这是单独的配置实验，不是默认上游。关闭它们不能自动弥补量化/计时/身份准入缺口，本轮也没有改环境启动任何工作。

这些缺口可工程实现，但需要新仪器化DLL、重新编译、冻结和受限准入；依照收尾范围停止，不把方案转为新的实现任务或排队项。
