# e12收尾：完整上游API可链接，运行比较仍未准入

接续PR237最新head **c8e5ea070ac393d7513903e0ec261dfce4554a49**，未重复GPU资格或计时。现有固定上游完整后端确实已构建，公共API的编译/链接验证通过；但要求的完整few-row实际路径证明、内部量化资格、投影计时和默认graph预算尚未具备。本轮依照“较大改造则结束”的条件止于审计，**新增GPU运行NOT_RUN、500独立额度预留0/实际0**。不将其描述成上游不能运行或数学上不可能控制；这是当前产物及已验证执行链的缺口。

## 已有证据与本轮最小核验

PR237仍Draft/未合并。只复核10份直接使用的已发表结果、合同、全部原始样本及账本的精确身份，不再遍历所有历史文件或重读GGUF。原48样本/24对和48次逐批完整回检记录相符，旧e11实际400/500、预留430不变。PR235原CPU-RN资格FAIL和PR237新独立U合同均不改。

同一真实Qwen3-8B-Q8_0首层输入，K=M4096、N8，RTX5070 Ti **Laptop GPU**，同一短会话。PR237提取device实现、resident输入、PDL0等价、graph OFF：

|边界|B均值µs|U均值µs|配对U/B几何比|paired bootstrap 95%|
|---|---:|---:|---:|---|
|仅投影|39.9680|23.2768|0.582391|[0.578649,0.585872]|
|含activation量化|44.1771|27.0779|0.612924|[0.607906,0.618665]|

每边界12对BU/UB交替、每batch5次，12/12对U更快，未丢样或挑选单个数字。含量化时间下降约38.7%只属于这个不同数值合同的提取算子边界，不是完整后端、默认dispatcher/PDL/graph或端到端服务收益。

[原始48样本](https://github.com/leecdiang/HeteroSpec/blob/c8e5ea070ac393d7513903e0ec261dfce4554a49/benchmarks/rtx223_e11_u_contract_20261113/ALL_SAMPLES.csv)、[原始24对](https://github.com/leecdiang/HeteroSpec/blob/c8e5ea070ac393d7513903e0ec261dfce4554a49/benchmarks/rtx223_e11_u_contract_20261113/ALL_PAIRS.csv)、[native资格/计时及全部差异审计目录](https://github.com/leecdiang/HeteroSpec/tree/c8e5ea070ac393d7513903e0ec261dfce4554a49/benchmarks/rtx223_e11_u_contract_20261113)。本轮没有新增性能样本，也不制造空白或模拟数据作为GPU结果。

## 现有完整产物与实际完成的链接验证

固定llama.cpp **0fb8f157702702f33f4e018de8701b2569a1bc28**，CUDA12.9.86、MSVC14.44.35207、sm120a-real。旧full-backend-002已经161步完整构建，ggml-cuda.dll为38,267,392B、SHA256 **3839d8c7c50bc88da6b00314a5b83b12374cc51bba1a85286981890331bfdded**。本轮仅核对9个直接相关源码/头文件与当时构建INPUTS一致、检查PE导入/导出及链接库；不重建后端。

`backend_api_link_only.cpp`的15个API地址引用经实际cl/link成功解析到ggml-cuda.lib和ggml-base.lib，生成**无entry的NOLOAD链接证明DLL**，没有可执行GPU工作负载。dumpbin只读解析PE文件，没有LoadLibrary或运行该DLL。全部编译/链接/PE日志和实际头依赖见link-only/，编译及检查约0.234秒，不能将CPU链接成功当作运行或正确性证明。

公共调用路径确实存在：ggml_backend_cuda_init(0)、独立WEIGHTS buffer的Q8_0[4096,4096]、CUDA COMPUTE buffer的F32[4096,8]和输出、ggml_mul_mat、ggml_build_forward_expand、ggml_backend_alloc_ctx_tensors、tensor_set、backend_graph_compute、synchronize及tensor_get。这里只证明符号可链接，**未实际调用这些数值API**。最小复现和完整停止点见[API与准入边界](API_AND_GATE_ZH.md)。

现代DLL的ggml-base.dll是702,976B/SHA e62a10e72e2c416a7b5a09f997630466d17662148beb69058023d9cd94d30566；旧staging白名单绑定的677,888B ggml-base及33,853,440B旧ggml-cuda均是不同身份，不能直接沿用。PE还列出cudart64_12、cublas64_12、cublasLt64_12、nvcuda及CRT依赖；PE列表不是实际运行时全部加载映像闭包。没有为通过而替换原文件、改白名单或ACL。

## few-row选择：静态适用，尚非实际运行证据

[ggml-cuda.cu L2447–2502](https://github.com/ggml-org/llama.cpp/blob/0fb8f157702702f33f4e018de8701b2569a1bc28/ggml/src/ggml-cuda/ggml-cuda.cu#L2447)先处理FWHT、padding/类型回退、MMVF/MMF，再在L2492计算few-row谓词；只有use_mmq_few为真才在L2498调用ggml_cuda_mul_mat_q_few。

对固定设备和原始q8形状，Q8_0、F32输入/输出、Ampere到Blackwell、N8在非Spark Q8阈值5至24内、K4096满足512 stage整数倍，16B对齐及单设备无view的WEIGHTS placement可使其静态适用。旧packed[4096,4,2,1]的ne1=4不满足此门槛。完整实际的设备属性、buffer usage、flags、stride、指针对齐和dispatcher分支必须在新受控进程中直接记录，现标**STATIC_ELIGIBLE / RUNTIME NOT_RUN**，不能写“已经确认进入few-row”。

本例静态对应Q8_0/ncg1/nmt1、256 CTA、128线程、69632B动态shared。该函数在ctx.pool私有临时buffer中量化，然后投影；WEIGHTS usage且非PARAM使x_is_constant为真，与PR237提取U传入的true一致。完整dispatcher仍可能因实际布局/placement不同而走其他路径，参数推导不替代实际证据。

## 比较边界及停止原因

|项|现有完整后端证据|当前缺口与判断|
|---|---|---|
|默认graph|cache GGML_CUDA_GRAPHS=ON；graph.cuh L65读取DISABLE_GRAPHS的**存在性**；稳定属性后由direct warmup进入capture，再replay|不能把一次graph compute或一次cudaGraphLaunch算作一个kernel；capture提交与每次replay的kernel节点必须有预留/拒绝及记录。当前graph launch两条路径均无e11许可回调|
|PDL|默认环境允许；common.cuh L1534按loaded-kernel属性选择cudaLaunchKernelEx，否则普通launch|实际选择未测。ptxVersion是cudaFuncAttributes字段，不等同PTX ISA8.8。设置PDL=0/禁用graph可形成另一个后端配置，但不能标成完整默认路径，且不消除下面的量化/计时缺口|
|量化资格|mmq-few.cu的src1_q是函数内pool临时分配；完整MUL_MAT包含D4量化及投影|公开tensor_get和scheduler逐node callback只能看到图tensor，不能取得这个内部临时q/d。不能直接把PR237捕获的q/d当作新完整DLL实际q/d；需新只读导出/快照hook再套用原注册oracle|
|投影计时|公共graph_compute边界包含量化；ctx.stream是私有nonblocking stream|公共CUDA后端event_new明确使用cudaEventDisableTiming（ggml-cuda.cu L6732）；未公开投影独立入口/stream getter，registry get_proc_address也没有。需内部事件hook并处理graph边界，不能用外部default stream事件冒充|
|含量化计时|可以设计同步前后host墙钟包住graph_compute，但它包含CPU调度/同步|与PR237 resident CUDA-event边界不同；若这样测必须重建两臂同墙钟协议，不能直接拼接旧B GPU时间|
|预算|PR237四个作者dispatch在调用前e11_reserve；完整DLL未导入/调用它|只限制host API次数或事后profiler不构成已验证的显式调用控制；单node图或可另建保守上界，但当前没有这一运行证明和故障拒绝链|
|准入|旧Job/lease/ETW方案存在、旧实验已关闭|新DLL/base、启动依赖、内部计量及结果写出须独立绑定并以CPU受限替身复验；不能只替换旧stage中的文件|

源码已有graph节点枚举用于cluster兼容性检查，但这不是预算控制；cluster检查之后的两处graph launch仍无本实验的预留/拒绝。这里不要求证明库/驱动物理launch上界，也不声称只有逐launch hook才可能控制作者提交；**缺的是当前完整路径的具体可审查合同与实现**。

因此，满足用户要求至少涉及新的后端量化快照/路径回执、stream内分界计时、direct/capture/replay计数及新DLL身份准入。这已经超出只写公共API调用器的改动。按本轮合理成本和不再堆框架的指令，未实现这些改造，也不以试运行探路消耗GPU额度。完整后端资格/配对计时均NOT_RUN，属于未完成比较，既非上游性能负结果，也非隔离失败或硬件不支持。

## 当前任务、资源与退出

2026-11-13北京时间13:36主机只读快照：358进程、204计划任务；未见相关worker、HeteroSpec计划任务或服务；D:/HeteroSpec-PC中*.lock/*.lease/*lease.json只读枚举无结果，两个已知lease不存在。13:43的固定UUID NVML快照无compute PID、util0%、37°C、约11.66GiB free。近期50聊天库存中，本机active仅本聊天；另一个active聊天“检查 munic int1 运行任务”在远端主机。没有向任何其他任务发送消息或停止任务。

这些是当时快照，不能排除未来外部任务或所有graphics工作，也未据此宣称取得运行独占许可。由于本轮不启动GPU，不另建锁/profile、管理员控制器或GPU队列；不制造旧会话历史缺口。

本轮模型、forward、普通数值DLL加载、CUDA runtime/driver初始化、所建GPU context和显式应用kernel调用均**0**；NVML只是固定管理库只读观测。独立500预算未预留、未消耗，旧e11账本430预留/400实际、旧失败不变。没有ACL/系统安全变更、无关进程终止、未知锁删除、旧基线/模型修改或论文投稿。

## 给论文重构的结论

保留PR237作为**固定现代device实现的受限算子参照**，明确不同数值合同、同一首层q8输入/单会话、PDL0/graph OFF/resident CUDA-event边界。它证明旧packed B并非该案例中最强算子实现，不证明完整现代默认后端、端到端竞争性或服务5%。现代上游已有一般权重staging/复用，不能仅凭这类机制主张新颖性。

JPDC重构证据摘要单列于[JPDC_EVIDENCE_ZH.md](JPDC_EVIDENCE_ZH.md)。本轮关闭，不推进PR237的候选、新C2、跨平台面板或服务加速项目。未修改论文文件；正式投稿/arXiv发布均未授权，必须先重构、由用户审阅最终稿并确认作者和投稿信息。
