# 固定上游 few-row MMQ 与 B/C/C1：源码对照

固定参考是 [llama.cpp PR31533](https://github.com/ggml-org/llama.cpp/pull/31533) 的合并版本 [0fb8f157702702f33f4e018de8701b2569a1bc28](https://github.com/ggml-org/llama.cpp/commit/0fb8f157702702f33f4e018de8701b2569a1bc28)，不是随时间移动的 master。PR 于2026-11-02公开、11-12合并；不能用合并日期冒充创新首次出现日期。下载归档 SHA256 为908f9cf777977a12b345146ff2b228ed4940450ec948b3f5e1c20251a44d870b；10个变更文件逐一对照 GitHub Git blob 身份，见 UPSTREAM_BLOBS_VERIFIED.json。本项目 PR234 的304dcbff与PR230的ba019f30均未改动。

## 调度门槛与本例的表示差异

[mmq-few.cu L814](https://github.com/ggml-org/llama.cpp/blob/0fb8f157702702f33f4e018de8701b2569a1bc28/ggml/src/ggml-cuda/mmq-few.cu#L814) 的 gate 需要 CUDA/NVIDIA、编译可用的 Ampere MMA、CC低于Rubin1300，排除 FORCE_CUBLAS。HIP/MUSA 不支持。DGX Spark1210还要求对应编译架构，否则没有其必需的 L2 prefetch。仅8种权重：Q8_0、Q3_K、Q4_K、Q5_K、Q6_K、IQ3_S、IQ4_NL、IQ4_XS。

K至少2048，并且必须是所选 ring stage 长度的倍数；不是只要求256整除。最多24个src1列。非Spark最小列数：Q3_K/Q5_K=3，Q4_K/Q6_K/IQ4_NL=4，Q8_0/IQ3_S=5，IQ4_XS=6；Spark为2，IQ4_XS/IQ4_NL为8。src0按stage和类型需16或4/2字节对齐，src1需16字节。正式host路径还断言src1/dst F32、连续K维、批维可广播。

| 本例表示 | K/M | src1 ne | Q8列数 gate | 本轮意义 |
|---|---|---|---|---|
| 原始真实8行捕获 |4096/4096|[4096,8,1,1]|通过；ncg=1,nmt=1，stage512|适用U的独立输入表示|
| 冻结 packed B |4096/4096|[4096,4,2,1]|不通过：ne1=4<5|不能假定后端升级即启用U|

冻结前端 `runtime/source-v1/src/llama-graph.cpp` L1570–1584 明确将前8列 view 成 `[K,4,2]`，输出再reshape；独立B探针保留该四列归约描述及批次stride。该文件实际位于旧e04目录，未修改。U必须以同一F32数据的原始8列表示进行比较，不能把两种host分流混为一谈。

[ggml-cuda.cu L2492](https://github.com/ggml-org/llama.cpp/blob/0fb8f157702702f33f4e018de8701b2569a1bc28/ggml/src/ggml-cuda/ggml-cuda.cu#L2492) 先计算use_mmq_few；它为真时跳过MMVQ并选few-row，再考虑一般MMQ。更早仍有浮点专用路径。融合入口也有few-row条件；MUL_MAT_ID不是本次适用路径。这里是固定源码及形状推导，未运行完整新版后端调度器。

## 内核机制逐项对照

| 项目 | 冻结 B | 原 C | C1 | 固定上游 U，当前Q8/8列实例 |
|---|---|---|---|---|
| grid/CTA |2048×2，128线程|2048，128线程|2048，128线程|256，128线程，16权重行/CTA|
| 权重 staging |各四列组经MMVQ/DP4A读取|每个K片段的寄存器权重跨两组共用|外层顺序处理两组，重新读权重|原始量化权重经cp.async进入每warp私有双ring，再解码供int8 MMA复用|
| activation |旧连续block_q8_1|同B|同B|MMA fragment布局；Q8权重用D4 float尺度|
| 工作集 |每线程4列×2权重行累加|两组同时存活，累加器翻倍|一组存活，复用累加器/共享区|yf每unit含4个int4 qs与4个int4 ds；两unit fragment和16×8 MMA输出映射|
| K遍历 |lane/warp分割Q8_0 block与子片段|每个输出保持B的lane/K划分与FP累加顺序|每组保持上述顺序，组间串行|warp从2×warp_id个256-value unit开始，每次前进8unit，逐stage内2unit、每unit8个32-value block|
| 归约 |缩放部分DP4A整数dot→lane float累加；warp0按固定warp序合并后warp_reduce_sum|同B每输出归约；同时两组|同B每输出归约；先完成组0再组1|每32-value整数MMA dot后缩放；warp内输出fragment逐K累加，最终warp0依次加另外3warp，无旧lane shuffle树|
| 同步 |尾部block barrier|尾部block barrier|两组各barrier，复用前再barrier|K循环cp.async commit/wait+syncwarp；wait_all后尾部2个block barrier|
| 跨组权重复用 |组内四列，组间不承诺片段复用|保留|明确放弃|一般化MMA列组复用，ncg1覆盖8列，最多3组24列|

U的stage在本例是512values=16个Q8_0 block，即每权重行544B。4warp×2ring×16row×544=69,632B动态共享内存。Q8_0禁止32-row tall tile；Q6_K三ring，其他本例两ring。Spark L2预取不在本机CC1200路径上。固定源码 [L487](https://github.com/ggml-org/llama.cpp/blob/0fb8f157702702f33f4e018de8701b2569a1bc28/ggml/src/ggml-cuda/mmq-few.cu#L487) 可核对ring、K迭代及尾部归约。常量权重可在PDL wait前开始copy；本例权重静态。没有stream-K fixup kernel。

## 数值合同不能由一般正确性测试代替

旧量化器取 `d=amax/127`、`roundf(x/d)`，存half(d)和half(原F32输入之和)。U每8线程处理一个32值block，各持4值，取 `d_inv=127/amax`、`roundf(x*d_inv)`、`d=1/d_inv`。Q8_0的D4布局存float尺度，不存旧half sum。其他Q4_K/Q5_K使用DS4；不能概括为所有上游类型都D4。

相同36,864B不代表相同布局或数值：U每256×8组144个int4=2304B。逻辑q字节、尺度、输出必须分别比较。最新版上游普通quantize_q8_1还与冻结版本有sum语义差别，这属于整个新版依赖的差异，不能未经单独历史定位就全部归因于PR31533。为此B与U用各自旧/新headers分离编译，未让U头文件悄悄改变B。

即使把U的float尺度舍成half或重排q，也不能自动恢复B：整数dot聚合粒度、缩放时点、K划分、FP归约树都不同。本轮实测U与旧参考有24个逻辑q、全部1024尺度、32766个输出float的位模式不同。U相对旧输出L2差为0.0002370446208。这是直接的非等价证据；不证明U一般数值错误，更不证明服务质量损失。

## 资源数据及边界

| 路径 | registers/线程 | static shared | dynamic shared | spill | 理论CTA/SM |
|---|---:|---:|---:|---|---:|
| B |63|3072B|0|0|8|
| C，旧会话 |91|6144B|0|0|5|
| C1，旧会话 |64|3072B|0|0|8|
| U，本次 |244|0|69632B|0|1|

表中是投影资源；量化器B24/U22寄存器，分别256/128线程。资源来自冻结编译日志；本次cudaFuncGetAttributes/occupancy API也返回B63/U244及理论8/1。理论上限不是实际occupancy；B/C/C1/U实际occupancy、L2/DRAM流量均NOT_MEASURED。U更低的理论并发并不能预测它慢：MMA、tile复用及cp.async改变了每CTA工作量与算术吞吐。没有计时则没有本机U/B性能结论。C→C1同时改变两组并行、权重重读、同步和工作集，跨会话差异也不能证明occupancy因果。

独立U诊断逐字提取device定义和量化器，未修改数学、K循环、布局。host固定Q8_0,ncg1,nmt1及正确stride，采用两臂相同的普通launch（PDL0等价），保持device PDL helper原样。它不是完整上游host/backend、默认PDL1或请求链性能基准。即使下轮计时成功，也需另测正式新版后端与PDL策略后才能称最强端到端参照。
