# e11最终：现代few-row存在算子空间，旧参考保持与服务收益仍待验证

本轮完成同一真实首层q8输入上的B重放、独立U数值资格及完整配对计时。U在两个预注册边界均有探索性优势，值得申请一次有明确旧参考合同的候选验证；不据此扩展到模型服务。U仍不逐位保持旧B，PR235的原CPU-RN资格FAIL永久保留。本文中的A/B/C指三种合同；旧候选C/C1另行命名。

## 实测结论与所有样本

固定RTX5070 Ti **Laptop GPU**、12GiB、46SM、driver616.92、UUID GPU-6dd57db3-9aac-ccc8-bd69-225a5ea2c4dd。同一K=M4096、N8真实首层操作数，resident输入，两臂普通launch、PDL0等价、graph OFF。不是完整上游默认后端、请求链或服务计时。

每边界12对，BU/UB交替，各顺序6对；每batch5次，计时前每臂预热2次完整算子。全部48个batch样本、24对均保留，无筛选、无补跑。每batch后量化及完整输出与该臂独立资格字节逐位一致，48/48通过。均值为每算子微秒；配对比值取12对几何均值，不能用两个均值相除代替。

|边界|B均值µs|U均值µs|配对U/B|配对bootstrap 95%区间|U较快对数|
|---|---:|---:|---:|---|---|
|仅投影|39.9680|23.2768|0.582391|[0.578649, 0.585872]|12/12|
|含activation量化|44.1771|27.0779|0.612924|[0.607906, 0.618665]|12/12|

仅投影B范围38.7328–40.5312µs、U22.8160–23.6160µs，样本CV分别1.162%/1.087%；含量化B43.5968–44.7424µs、U26.7264–27.5904µs，CV0.793%/1.084%。仅投影BU/UB几何比0.583024/0.581758；含量化0.612548/0.613301。两边界均满足事前条件：几何比<1、整对bootstrap区间上界<1、至少10/12对更快、两种顺序分层均<1。10000次整对重采样、固定seed20261113；这是同一短会话内探索区间，不覆盖跨输入/会话/平台不确定性。

[全部原始样本](ALL_SAMPLES.csv)、[全部配对](ALL_PAIRS.csv)、[完整统计](ANALYSIS.json)、[原始native计时结果](TIMING_NATIVE_RESULT.json)。event区间排除分配/拷贝/验证，可能包含host提交间隙；投影前单次量化在event外，完整算子量化在event内。不得把两个独立边界相减当作独立测得量化成本。功耗/时钟/实际occupancy/L2/DRAM均NOT_MEASURED。

## 三种合同与完整数值结果

**A：原参考保持，PASS（B）；U不满足。** B两次完整36864B Q8_1和32768个F32输出与e08捕获逐位相同。U相对旧B有24个逻辑q、1024个scale、32766个输出float位模式不同；相对L2误差0.0002370446，最大绝对差6.5844506e-05。不以argmax替代完整比较。全部差异CSV及原始字节身份保留。

**B：新的独立U数值合同，PASS。** 在GPU前注册，固定上游源码、编译器、sm120a、实际PTX8.8 div.approx.ftz/rcp.approx.ftz语义。对1024块/32768量化值/完整布局，要求每32值块存在同一个inverse解释全部q和scale：inverse为独立RN(127/amax)前后2个F32邻居，scale为该inverse的RN倒数前后1邻居；独立RN乘法、FTZ、ties-away整数化，域外拒绝。范围依据[NVIDIA CUDA12.9 PTX规范](https://docs.nvidia.com/cuda/archive/12.9.0/parallel-thread-execution/index.html)，未从旧10处差异拟合。

两次U的joint block失败0、最少witness1，但900块有多个witness，因此这是受限允许集合验证，不是唯一预测隐藏硬件inverse。对实际且独立验证的q/d，CPU intdot32+double数学参考检查全部32768输出，gamma64×sum_abs+128×FLT_MIN界失败0，最坏误差5.9575736e-08，为界的0.03830倍。两次raw量化/输出完全一致，并由另一个CPU-only可执行验证器重新检查。旧CPU-RN仍有10个q不同，作为诊断保留；不把旧合同改写为PASS。

**C：提取算子性能合同，PASS。** 上述统计只覆盖固定device实现和显式host路径。完整固定上游ggml-cuda虽161步成功编译链接，尚未加载；默认dispatcher、PDL、graph及pool的运行计数和依赖闭包未准入，RUNTIME NOT_RUN。详见[数值预注册](NUMERICAL_CONTRACTS_ZH.md)、[后端边界与复现](BACKEND_BOUNDARIES_ZH.md)。

## 身份、调用与源码比较

PR230 ba019f30522352c87cac2cc527082ecc6c73ed97；PR234 304dcbff6d17461237774464c67ce8cb0ed60189；PR235 01a4cf847bfc8340321564c66132680d4131bf0d，交付前再次核对，均Draft未合并。旧C/B投影1.147676、完整1.126389；旧C1/B1.022156/1.026132，原样保留。不同会话且C1串行化两组、放弃跨组寄存器复用，不能把C→C1解释为occupancy因果。

捕获来自Qwen3-8B-Q8_0 blk.0.attn_q.weight，真实8token，非q32前8行；本轮无新捕获。GGUF完整哈希、原始tensor绝对偏移1350722848/17,825,792B、producer及全部activation/量化/后端输出身份重新核验。结果后再次核对118条旧证据、9863个native构建输入和7个stage文件，均未变。

|对象|SHA256|
|---|---|
|模型GGUF|408b955510e196121c1c375201744783b5c9a43c7956d73fc78df54c66e883d6|
|weight|822086ad0b394e3f032f5a95a0193df9a6f2f628f58cee4b2d2c44ba4bb26b5e|
|F32 activation|47009f80cddac6ccefd830bd4a2763c6f5fa1a6cf96fb40fb2b6d1555e0d2836|
|旧Q8_1|caaf90580faecb85103fb19d9f76f4d8210c3fd2ca72a7da1d28971537000901|
|旧完整输出|6f4c7a410b441c266a34f20f5a5c1c2bc67ef4a3ef5e622e4a005cadd42a0fd0|
|U新量化|a3824e6bbc5b82dc0fb9e65cae9905899da047289929eb85f449f4eee3de1d8e|
|U新输出|e7e78637b1a3af945c0ae233ffc4b93d949947ff5fa1312790fee88f5667bb83|
|唯一GPU探针build003|de350801047138acfd22454d31b2186d02dfba981ed1ed84ae115a7fb5f725b0|
|native FREEZE|ece9bc339e4d884da64ac0137bc9ccbdbb87a60584553a47383f705ecec3be3c|

固定上游[0fb8f157](https://github.com/ggml-org/llama.cpp/commit/0fb8f157702702f33f4e018de8701b2569a1bc28)来自已合并PR31533。few-row CUDA gate为Ampere+且低于Rubin1300、支持列举8类量化、K≥2048且满足stage、N≤24；非Spark Q8至少5列。原始[4096,8,1,1]通过，旧packed[4096,4,2,1]的ne1=4不适用。不能仅按总token数认为dispatcher会选同一路径。

|路径|本例布局/并行|权重使用、K与算术|资源|
|---|---|---|---|
|B|128线程，2048×2CTA，4列×两组|旧DP4A、half2(d,sum)、旧K/lane与FP归约|63reg，3072B静态shared，0spill|
|旧C|同线程同时累积两组|跨组寄存器权重片段复用，旧参考通过|91reg，共享内存翻倍，原负结果保留|
|C1|两组顺序化|放弃跨组寄存器复用；不是单独occupancy干预|原编译报告/负结果不变；实际occupancy未测|
|U|128线程，256CTA，16输出行tile|cp.async私有warp双ring原始weight；Kstage512；int8 MMA32dot、D4 float scale、不同FP归约|244reg，69632B动态shared，0spill|

U量化采用127/amax近似inverse、x×inverse整数化、1/inverse的float尺度，不保留旧half sum字段。U与B既有映射也有数值合同差别，当前优势无法归因于单一权重复用或occupancy。理论B8CTA/32warp与U1CTA/4warp每SM只是资源可驻留上界，不是实测占用率。一般权重staging/复用已在现代上游存在，不能当作本项目新颖性。

## 准入、失败、预算和退出

同一管理员身份的受限CPU/ETW检查通过，54条模型路径实际拒绝；既有package SID/staging RX不变，无ACL或系统安全变更。原profile首次清理后，在同一个已批准零能力profile下复建做本次准入，输出全部保存后再次删除，DeleteAppContainerProfile返回0。没有终止无关进程或改ToDesk设置。

|阶段/尝试|结果|显式实际|说明|
|---|---|---:|---|
|CPU counter故障、预算边界与oracle域测试|PASS（保留先前FAIL）|0|no-throw C ABI；500/501、392/393、过期/溢出/无dispatch；CPU不加载数值DLL或初始化CUDA|
|qualification-001，12:16|PASS|8|B/U各量化2+投影2；两次全量检查|
|timing-001，12:17|FAIL准入|0|foreign compute context；native未创建，原PID未记录|
|timing-002，12:40|FAIL准入|0|观察PID39736；约5秒前快照为ToDesk视频worker，非同时生命周期绑定，不能断言绝对身份|
|008 CPU入口，13:21|FAIL|0|旧profile回执路径拼接错误；profile/受限worker/CUDA均未创建；原源码保留|
|010 CPU修正，13:22|PASS|0|新版本只修正读取不可变e07原回执；CPU slot旧文件名带cleanup但用途明确为准入修复|
|idle只读检查，13:22:21–31|PASS|0|无compute PID/ToDesk视频worker，GPU util0%，连续10.078秒；最多90秒等待|
|timing-003，13:22:31–39|PASS|392|warm8+projection144+complete240；受控任务7.297秒；退出0，自有Job为空|
|收尾，13:23以后|PASS|0|profile输出保存、profile删除、控制器退出、lease均无遗留|

原500分配14资格+14已定位修正+416计时+56余量不变。全局永久预留430=14+416；实际400=8+392；已预留未用30不退款，未预留70未用。两次计时准入失败均在native创建和PERMIT前，接续引用同一416逻辑预留、额外预留0，未重置/挪用旧账。全部新旧family前缀逐字保留，失败回执不覆盖。[最终账](LEDGER_INTERPRETATION_FINAL.json)、[全局原始日志](FAMILY_FINAL.jsonl)。

探针每个四类作者dispatch前核准显式许可及109秒新步骤截止；inner Job单子进程/2GiB/kill-on-close/119秒，外控2进程/120秒。输出16MiB上限，device数组18,124,800B；GPU内存/磁盘/温度采样可触发停止但不是瞬时资源硬界。资格及计时各观察进程start/end1/1、映像load/unload55/55、ETW loss0；NVML短采样可能漏过短kernel，util0不表示未执行GPU。实际观察温度39–40°C；只读收尾无compute PID。设备挂死时即时清理无保证。

本轮模型加载0、新捕获0、forward0、完整数值根DLL显式加载0；实际GPU native进程2，CUDA runtime/driver初始化非零。隐式context数与全生命周期physical launch数UNKNOWN；400只数显式应用dispatch，不声称原4096物理launch硬合同闭合。完整默认后端、实际occupancy、L2/DRAM及服务均NOT_RUN/NOT_MEASURED。生产默认拒绝不变。

## 服务5%和唯一下一候选

本轮含量化r=0.612924意味着**该不同合同算子时间下降38.7076%**。条件公式new/old=1-f+fr+h；若某个未来旧参考保持候选能达到此r，5%服务下降要求f≥(0.05+h)/(1-r)。h=0时至少12.9174%受益覆盖；按本次区间为12.7520%–13.1118%；h=0.5%/1%时点要求约14.2091%/15.5008%。例如同请求受益部分仅10%，即便完全达到U的r且无额外成本，也只有3.8708%的条件下降。

f和h均NOT_MEASURED。捕获在首层typed stop退出，并非完整请求；禁止拼接旧面板/跨会话/A5000的成本来冒充同请求栈。U更快说明现代强参照有空间，不说明保持旧参考也能达到，更不说明服务达5%。[完整敏感性](AMDAHL.json)。

只提出一个[八warp双组共享原始权重stage候选](NEXT_SINGLE_CANDIDATE_ZH.md)：256线程CTA分两套独立4warp，各保持B每输出的K/lane、DP4A、half缩放及FP归约；共享两行×32个Q8_0 block的2176B原始字节stage，4stage，预计partial+raw payload约8320B。保留跨组shared原始权重复用，放弃C的跨组寄存器片段复用；与U的MMA/D4不同。

这是一项可证伪映射假设：合并调度并减少同CTA重复原始取数能否抵消256线程、barrier和shared成本，仍未知。B可能已充分命中缓存；寄存器/实际occupancy/流量未知，不能预言瓶颈或收益。候选未实现/编译/GPU运行，本轮不执行。

下一步仅申请独立最小资格+固定配对协议：先编译证明旧K/归约映射并核对资源，两次全量旧B activation/输出逐位资格，通过后才计时；任何位差即停。完整算子paired95%上界≥1或仅投影有利则停止扩展。若有利，先跨输入再核对同请求成本f/h；完整默认上游需要另建dispatcher/PDL/graph预算与依赖准入。一般权重复用不作为新颖性；论文需要明确旧参考可保持的独特约束和强基线差异，当前不修改或提交论文。

## 交付状态

旧e01–e10、原参考、B1失败及全部旧账本保留。准备阶段报告和0消耗快照以PRE_GPU前缀保存；两次拒绝后的中间快照以TWO_REFUSALS前缀保存；旧TIMING_NOT_RUN仅是当时状态，由本文与当前RESULT取代。初始审计zip不变，新运行审计zip另加；源码、失败、编译、CPU、资格、原始样本和账本均可审查。模型/权重/activation原始二进制只保留本机，公开交付身份和全部数值差异CSV。

Draft PR独立续作；不合并、不升级基线、不运行新候选/跨输入/服务，不提交论文，不宣称普适5%。所有管理员控制器已退出，GPU队列关闭。
