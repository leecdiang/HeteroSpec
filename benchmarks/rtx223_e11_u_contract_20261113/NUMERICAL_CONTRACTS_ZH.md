# e11预注册：三个独立合同

A保持旧B不变：两次完整Q8_1全部36864字节及32768个F32输出逐位相等原捕获，不能改变参考来通过。e10原CPU-RN合同及FAIL永久保留。

B是新的、受限域内的上游独立数值合同，不等同于A，也不是e10合同的更正：固定0fb8f157源码、固定编译器/-use_fast_math、sm120a AOT与实际PTX primitive。验证器独立于GPU实现，不复制GPU量化器作oracle，不使用观测输出拟合容差。

对每个32值block，CPU根据F32输入独立求amax，并求RN(127/amax)。枚举其前后2个F32邻居共5个inverse；要求存在**同一个**inverse，能够同时解释全部32个q以及该block的float尺度。q由RN乘法、FTZ、ties-away roundf生成；尺度必须属于RN(1/inverse)及其前后1个F32邻居。这里允许集合的宽度来自固定PTX div.approx/rcp.approx的公布精度，不是从e10的10项差异估计；不得逐元素各挑一个不一致inverse。每块报告witness数，集合验证不能声称唯一重建了硬件近似值。

依据：[NVIDIA PTX ISA div/rcp](https://docs.nvidia.com/cuda/parallel-thread-execution/)，近似div在分母正常范围为2ULP，近似rcp为1ULP。它们的具体位结果不是跨设备的RN保证。CUDA数学指南另说明部分精度数字来自有限测试；本合同是明确有限域、固定编译产物下的可检验数值准入，不把公布精度当作所有硬件/生命周期的安全证明。编译后必须直接核对PTX操作及布局，若编译改变到不受此模型覆盖的操作则拒绝。

限定有限F32输入，非零值为normal，block amax>0、在2^-126到2^126之间，inverse和scale正常有限、scale≤1，q范围[-127,127]。当前真实捕获须逐项验证这些条件；任何域外值拒绝而不是推测处理。CPU采用RN模式和严格浮点，乘法强制存回F32；两个F32的乘积可由CPU double独立复核。roundf lowering在本域与ties-away整数化一致，不能使用可能把半整数邻居推过边界的F32加0.5近似替代。

完整输出对实际、已经独立验证的U量化q/d，独立CPU逐32值算整数dot，按double精确表示的q/dw/dy贡献计算数学参考。每个32768输出要求 abs(actual-reference)≤gamma64×sum_abs(block_contributions)+128×FLT_MIN，u=2^-24，gamma64=64u/(1-64u)。要求权重half尺度有限且abs≤1。32值intdot精确且小于2^24；每warp32个block贡献及缩放、最终3warp加法的舍入深度小于64。FTZ绝对项单独覆盖，拒绝溢出/非有限结果。报告所有错误计数及最坏误差，不用argmax替代。

两次B和两次U重放；U每次均做上述完整验证，并要求两次raw量化全部字节和全部输出逐位确定。全部旧B/U逻辑q、尺度、输出位模式及误差另列；U可以满足B合同而不满足A合同，但不得写成旧参考保持成功。

C为性能诊断：**提取device实现、固定host参数、两臂普通launch（PDL0等价）、graph禁用、resident同一操作数**。B使用旧packed四列×两组；U使用同一F32的原始8列和上游D4量化。仅投影边界排除量化；完整算子边界包含量化+投影。分配/拷贝/校验在event外，所以不是请求延迟/完整上游后端速度。正式上游host默认PDL、dispatcher、graph及内存池另审查，未经预算计数闭合不运行。

资格通过后12组交替BU/UB，每batch5次，两条边界固定顺序。各臂预热2次完整算子（共8次显式kernel）；投影24batch×(一次边界外量化+5投影)=144；完整算子24batch×5×2=240，共392。每batch后raw量化/完整输出与该臂已独立资格的oracle逐位相等，不计时校验。全部48样本保留，禁止按结果筛选。报告配对几何比、全部顺序、范围/CV、方向一致性和固定种子paired bootstrap区间；不按单个有利样本判断5%。

资格初次14预留、一次已定位工程修正14、计时416、失败余量56，总500；预留不退。资格实际最多8、计时实际392。所有失败、预热、修正计入；每次作者dispatch前强制拒绝额度与109秒新步骤截止；native Job119秒、外控120秒。模型/捕获/新候选/服务预算0。隐式context、库/驱动物理launch及设备挂死后即时清理上界未知；原4096仍未闭合。
