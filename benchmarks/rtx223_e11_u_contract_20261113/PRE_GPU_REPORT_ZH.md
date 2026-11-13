# e11：独立U合同与配对探索已准备，GPU等待Windows准入

**本轮尚不能判断现代few-row相对packed B的性能空间。** 已完成三个PR、真实q8操作数、失败与账本核验，建立新的独立U允许集合oracle、修复预算回调、完成提取探针和完整固定上游CUDA后端编译。Windows管理员启动返回取消，当前进程非管理员；相同管理员身份的受限CPU/ETW准入未运行，因此新GPU资格、预热、计时均NOT_RUN。没有把旧FAIL改成PASS或降低隔离要求来运行。

## 原证据与本轮身份

当前PR230=ba019f30522352c87cac2cc527082ecc6c73ed97，PR234=304dcbff6d17461237774464c67ce8cb0ed60189，PR235=01a4cf847bfc8340321564c66132680d4131bf0d，均Draft/未合并。旧C/B投影1.147676、含量化1.126389；旧C1/B分别1.022156、1.026132，原始pair重新计算相同。不同会话、C1顺序化两组并放弃跨组寄存器权重复用，不能把C→C1当occupancy因果。实际occupancy和L2/DRAM仍未测。

PR235的旧U资格仍为FAIL：6次显式许可、永久预留14，10个q不符原CPU-RN合同。其24个逻辑q、1024个scale、32766个旧输出位模式差异与原始二进制均保留。新e11合同不是旧合同的事后修订。

同一首层q8输入：Qwen3-8B-Q8_0，blk.0.attn_q.weight，K=M4096、8个真实token的F32 activation。完整GGUF SHA256重新核对，并直接读文件偏移1350722848的17,825,792B原始tensor，与weight.bin完全一致。producer exe、DLL、activation、旧Q8_1、旧完整输出和全部捕获终态链均核对。模型未加载到runtime；只读哈希与GGUF字节解析不构成模型forward。

| 对象 | SHA256 |
|---|---|
| 模型 |408b955510e196121c1c375201744783b5c9a43c7956d73fc78df54c66e883d6|
| weight |822086ad0b394e3f032f5a95a0193df9a6f2f628f58cee4b2d2c44ba4bb26b5e|
| F32 activation |47009f80cddac6ccefd830bd4a2763c6f5fa1a6cf96fb40fb2b6d1555e0d2836|
| 旧Q8_1 |caaf90580faecb85103fb19d9f76f4d8210c3fd2ca72a7da1d28971537000901|
| 旧完整输出 |6f4c7a410b441c266a34f20f5a5c1c2bc67ef4a3ef5e622e4a005cadd42a0fd0|
| 选定提取探针build003 |de350801047138acfd22454d31b2186d02dfba981ed1ed84ae115a7fb5f725b0|

新探针freeze SHA256=ece9bc339e4d884da64ac0137bc9ccbdbb87a60584553a47383f705ecec3be3c，实际依赖无未冻结项、输入无变化。固定上游仍为0fb8f157702702f33f4e018de8701b2569a1bc28，10个变更文件Git blob逐一相符。设备固定GPU-6dd57db3-9aac-ccc8-bd69-225a5ea2c4dd，已知为RTX5070 Ti Laptop GPU/12GiB/46SM，正式运行仍需现场重验UUID及独占。

## A、B、C三个合同

**A：旧参考保持。** 旧B源码、headers、量化与输出oracle不变；新运行必须两次全部36864B Q8_1和32768个F32输出逐位相同。当前仅历史结果核验PASS，新GPU重放NOT_RUN。

**B：新的上游独立数值合同。** 详见[预注册](NUMERICAL_CONTRACTS_ZH.md)与u_oracle.hpp。每32值块必须存在一个共同inverse，属于CPU RN(127/amax)前后2个F32邻居，能同时解释全部32个q及尺度；尺度须在该inverse的RN reciprocal前后1个F32邻居内。q的乘法、FTZ及ties-away舍入按固定PTX primitive独立建模，不逐元素各选互不相容的inverse。

误差宽度来自[CUDA12.9 PTX8.8 div/rcp定义](https://docs.nvidia.com/cuda/archive/12.9.0/parallel-thread-execution/index.html)，不是从旧10项差异拟合。编译生成PTX8.8、sm120a，直接核对div.approx.ftz与rcp.approx.ftz。有限/normal/非零block等域条件逐项检查；域外拒绝。CPU严格RN编译，完整输出另以独立整数dot+double量化数学参考和源码推导gamma64界验证。全部32768个输出、1024个尺度和32768个q都检查，另要求两次U原始字节逐位确定。

这个oracle是**允许集合oracle，不是唯一逐位预测硬件近似值**。CPU对旧U数据的离线检查符合新集合：1024块全部通过，其中900块存在多个inverse解释，不能声称还原了唯一中间值；32768输出误差界全部通过，最大误差/界0.03830。它只证明新CPU检查的可执行性，不替代新GPU资格，更不改变e10 FAIL。新独立GPU资格仍NOT_RUN。

**C：提取device算子探索。** 两臂resident相同原始操作数、普通launch/PDL0等价、graph禁用。仅投影与含activation量化的完整算子分开；分配/拷贝/验证在event外，可能含host提交间隙，不是服务端到端。正式上游默认PDL、graph、dispatcher与本探针不同。[后端边界与实际构建](BACKEND_BOUNDARIES_ZH.md)列出调用选择、形状、PDL、graph及最小复现。

真实原始[4096,8,1,1]适用上游Q8 few-row；旧packed[4096,4,2,1]因ne1=4不满足最小5列，不能假定升级后端即启用U。完整固定上游ggml-cuda目标已在新目录完成161步编译/链接，38,267,392B DLL SHA256=3839d8c7c50bc88da6b00314a5b83b12374cc51bba1a85286981890331bfdded；未加载运行。Root默认GGML_CUDA_GRAPHS=ON、PDL selector按环境与加载kernel属性决定；初始化、graph/replay、依赖身份和显式调用计数未闭合为本轮执行合同，因此不将完整后端计为已测。

## 实际门槛与失败

| 项目 | 本轮状态 |
|---|---|
| 三个PR、旧原始数据、producer、模型tensor、账本 |PASS|
| 新U独立CPU oracle及损坏q/scale/共享inverse/输出等故障检查 |PASS|
| 首版预算异常返回测试 |FAIL，保留0xc0000409|
| no-throw C接口修复后，三TU超额/过期/溢出/未知操作拒绝 |PASS|
| 提取build001/002/003编译 |PASS；001/002仅保留，003选定，全部未执行|
| 完整上游首次配置 |FAIL，路径问题保留|
| 完整上游v2配置及编译链接 |PASS，未加载|
| 同管理员身份受限CPU/ETW准入 |NOT_RUN，Windows启动取消|
| 本轮A/U重复数值资格 |NOT_RUN|
| 预热、全部48配对batch、实际occupancy/L2/DRAM |NOT_RUN / NOT_MEASURED|
| 新候选、模型forward、服务、66格 |NOT_RUN|

预算回调失败源于/EHsc下extern-C异常传播假设；相同CPU源改/EHs复现退出0，正式修复保留/EHsc，改为noexcept bool/cudaError返回，C++层处理拒绝。500/refuse501、392/refuse393、过期不计数、不dispatch、unsigned溢出、零/未知操作全部通过。v3进一步消除U特有的重复错误查询，两臂每dispatch检查一次，避免控制开销不对称。device数学、量化、归约与合同均未改。详见[保留的工程失败](ENGINEERING_FAILURES_ZH.md)。

## 独立预算与尚未执行的具体操作

500总上限分配：资格14、一次已定位工程修正14、计时416、余量56。首次资格实际最多8；成功后预热8、仅投影144、含量化240，共392，计划成功总实际400。所有失败/重试/预热均计入，预留不退款，不借旧账本。

配对协议和判据在GPU前冻结：12组BU/UB交替、每batch5次，两条边界共48batch，每batch后全部量化与输出与该臂独立合格结果逐位相同。保存全部样本，不剔除慢值。预注册几何比、整对bootstrap区间、顺序分层与至少10/12方向一致性，详见PERFORMANCE_DECISION.json；仅单输入、单会话探索，不证明普适稳定收益。

当前GPU账本尚未开启，**预留0，显式许可0，GPU尝试0**。PREPARATION_LEDGER.jsonl只记CPU准备和取消，不伪装成已运行GPU账本。相同受控启动为一个native子进程、原子纳入kill-on-close Job、2GiB commit，预计4个device buffer合计18,124,800B，32MiB结果水位；每dispatch前额度和109秒门限，native119秒、外控120秒。实际温度/显存/磁盘准入及观察须在正式运行重新获取，不把预计buffer字节当显存硬上界。

已批准500次与复用原受限方案不缺授权；缺的是Windows现场管理员启动，当前IsUserAnAdmin=false，之前UAC返回取消。不能复用旧管理员CPU回执或放弃ETW/隔离来绕过。新profile未创建，管理员控制器未建立，CPU请求已停放为.not_run并设置自有ADMIN_STOP；没有GPU请求排队或可能自动晚启动的实验。

本轮模型加载/新捕获/forward/数值DLL普通加载/实验CUDA初始化/实验GPU context/作者应用kernel许可均0。全主机物理launch未计，原4096全生命周期硬合同仍未闭合，生产native默认拒绝。未改ACL、安全设置、Windhawk、旧基线或论文，没有终止无关进程或删除未知锁。

## 服务5%的定量结论与唯一候选

没有本轮可信U/B计时，所以r未知；捕获在目标tensor后typed stop，不是完整同请求成本栈，f/h也未知。因此当前服务5%可行性为**UNDETERMINED**，不能据CPU检查、完整DLL链接成功或旧会话时间推断性能空间。

[Amdahl方法及完整敏感性表](AMDAHL_METHOD_ZH.md)：若严格旧参考方案达到算子比值r、覆盖同请求成本f、增加开销h，则服务下降5%要求f≥(0.05+h)/(1-r)。h=0时，r=.5需f≥10%；r=.8需25%；r=.9需50%；r=.95需100%；r=.98则即使全部服务受益也不足。没有挑一个有利数字，也不把不同合同的U速度自动记成HeteroSpec收益。

只保留[一个条件性设计提案](NEXT_SINGLE_CANDIDATE_ZH.md)：八warp CTA内两套独立四warp组共享原始权重stage，保持旧B的量化、DP4A部分dot及K/归约顺序，避免C每线程双组累加器和C1串行重读的组合。它保留shared原始权重跨组复用，不保留跨组寄存器片段复用。同步/CTA耦合、缓存已复用及寄存器增长都可能使其失败；目前没有性能证据支持启动它。未实现、未编译、未运行，不能声称新颖性或5%收益。

恢复入口与严格先后门槛见[RESUME_ZH.md](RESUME_ZH.md)。补一次现场Windows确认后，可接续同一未用500次协议；若当前窗口已过，必须重新绑定有效窗口及同一累计预算，不能借机重置旧额度。完整后端默认路径、新候选、跨输入、服务或论文均不会自动升级。
