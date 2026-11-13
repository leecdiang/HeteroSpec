# #244 Windows完整部署R/M：已完成两面板，数值合同不同

## 结果与解释

**完成192次正式请求：P128、G64。两臂自己的集成资格均PASS。** 本实验在一台RTX5070 Ti Laptop GPU上、单个18.09分钟执行窗口内完成，含多个驻留session；不是原提取U/B单输入算子试验。

|预注册面板|root数/配对块|正式请求|等权root M/R耗时比|分层paired-root bootstrap95%|
|---|---|---:|---:|---|
|P：相同prompt与128个强制continuation token|16/4|128|0.678474|[0.663120,0.693858]|
|G：各自自主greedy、共同cap128|16/2|64|0.676136|[0.662307,0.690207]|

P主指标是在本面板、共同部署包络中，M完整模型的固定工作量执行成本比R低**32.15%**，条件区间对应约30.61%–33.69%。这不是保持旧参考结果的加速，也不是自由生成服务收益。64个P配对全部保留，单对M/R范围0.494911–0.900863；root等权主指标与按总时间加权的pooled比0.672400分列，不挑较有利的数字。

G仅作独立描述：M/R比0.676136，约32.39%时间差。本次两臂各4096 emitted tokens，64条response**全部在cap128终止**，没有自然EOG结束；20/32个配对token轨迹完全相同，12/32不同。等长不等于内容或质量等价，不能称非劣，也不能当自然完成回答的服务时延。全部文本、token、首次分歧、TTFT及decode-per-token保留于G_TRAJECTORY_DIFFERENCES.json、ALL_RECORDS.json及CSV。

所有区间按预注册root层级估计：每根先平均block的log(M/R)，16根等权，长度分层整根重采样20000次、seed244。block是重复session，不是64个独立任务；区间仅反映本窗口的root重采样，不覆盖跨日、跨设备、共享session漂移或生产负载。各块比值与全部样本一并给出，没有剔除慢根、异常比或重选面板。

## 输入范围的重大限定

原方案的<=128/256/512/768箱在实际native tokenizer过滤后，可用code/math数分别为56/260、68/36、14/10、**0/2**，无法填满最后一个箱。按加载前固定的确定性备用规则，在任何decode前改用切点60/74/78/768，每箱2code+2math、稳定ID最先合格者，共8 HumanEval和8 MATH-500。实际正式prompt长度只有**26–161**；这不是原长prompt覆盖，不能推广到513–768长度或完整C1024性能。764-token长输入仅用于资格，未作为性能样本。

选择发生在R reference部署的真实tokenizer导出后、任何推理输出/计时前。continuation取公开canonical_solution+tests或MATH solution的前128个真实token；不足者过滤，无repeat/padding，无快臂生成teacher。显式Qwen3 user/assistant no-thinking字符串格式固定，不称模型factory template。M独立reference逐项重新tokenize全部16根prompt/continuation并要求IDs相同。输入版本、稳定IDs与hash已冻结。旧A5000 S3记录的12根与本面板稳定ID无交集；未声称语义去重或训练未见。

## 数值资格与跨合同差异

每臂8次资格请求、3个新进程：独立native driver2请求；fresh adapter2请求；另一个fresh adapter先重复2请求，再reset/reuse2请求。短根为自主greedy并捕获完整请求词表行，长根为历史764前缀+固定128 continuation。比较所有实际请求行的完整F32向量、tokens、EOG、rows/calls、KV末位置及reset；driver独立实现batch/位置/greedy控制，不include adapter。每臂6次完整向量对比均逐位一致。

R还在原记录配置(batch1024/ubatch1/reserve1/24threads)重放历史764 frontier，607744字节精确相同，SHA256 **8b13e6e1554f15a78fdf5fb75c8c661e45cb3b52e60d3a8ad0a626fb2485691b**。adapter采用共同正式profile的batch32、2threads，保持R内部ubatch1/reserve1；与native driver所有请求向量仍一致。M reference和adapter均用自己的固定现代完整backend，未套用旧提取U CPU-RN oracle。

这是真实完整原生链的集成/稳定性/continuation资格，不是仅自身重复，更不是独立全输入数学正确性证明。R原静态核心与运行DLL逐字绑定，M完整固定源码构建；PR235旧FAIL、PR237独立U合同和全部旧记录均不改。

**M与R数值差异明显，不能视为微小舍入或兼容参考。** 同一长固定诊断全部152个请求行×151936词表=23094272值中，23094237个float位模式不同；最大绝对差7.820194，最差请求行(relative L2)0.478030，出现在位置287；argmax相同149/152也不替代完整差异。已核对模型hash、输入、位置、RoPE/RMS/head参数、F16KV、FAoff和放置，未发现adapter错接；差异具体机制未定位，不归咎于单kernel、舍入或上游bug。完整per-row统计和原始两组F32文件身份保留。

两臂实际日志EOG集合相同：[128247,151643,151645,151662,151663,151664]。G尊重EOG，未为凑长度抑制停止；本次恰好全部撞cap。未执行生成代码或质量scorer，质量等价/非劣为NOT_ESTABLISHED。P只比较同一逻辑token工作量，不能把输出兼容性或质量收益藏在速度数字里。

## 完整部署与计时边界

R恢复自原native-original-v4：libllama.a SHA **8fa2731e05cd064156ed4587b3a85d59498ef11b2b6d5f95fec1262a420db445**，等于历史R-Qwen BUILD；完整静态核心未改，运行DLL逐一匹配历史BUILD并复制。用原Zig Windows工具链链接最薄API adapter和独立driver。R CUDA沿用原冻结二进制，本轮没有声称从全部CUDA源码重新构建；其历史二进制来源限制保留。

M从pinned **0fb8f157702702f33f4e018de8701b2569a1bc28** 完整构建llama/ggml CPU/CUDA，MSVC14.44.35207、CUDA12.9.86、sm120a-real；CMake ABI设备探测被显式跳过，实际编译/链接另证。首次worker头路径缺失失败保留，重生成构建后通过。没有将现代DLL塞入旧frontend，也没有提取U移植进R。

共同模型Qwen3-8B-Q8_0 GGUF为8709518112字节，SHA **408b955510e196121c1c375201744783b5c9a43c7956d73fc78df54c66e883d6**；单序列、C1024、F16 K/V、Flash disabled、因果attention、2 CPU threads、请求batch32、单GPU n_gpu_layers999。每个真实运行日志确认**offloaded37/37层**；input embedding仍按两版本共同的stock放置落在CPU，不称所有算术都在GPU。

R内部ubatch1/reserve1是其固定参考策略；M内部ubatch32并保留graph/PDL默认允许行为。两臂资格日志均直接观察到CUDA graph reuse；正式session不加graph debug。M PDL为默认允许，是否逐kernel实际采用未单独监测；不声称所有op都走few-row。完整路径可能混用MMVQ/MMQ/few-row与其他库，未做逐operator或launch计数。Flash关闭是共同包络，不称所有factory defaults或现代最优配置。

两臂编译器、CUDA/BLAS运行库、批策略与优化实现不同，结果代表完整部署迁移总体取舍，不能把32.15%归因于few-row kernel或把它当固定参考约束的纯因果成本。阶段均值显示节省集中于含reset/输入交付/prefill的阶段，continuation均值没有同等改善；这是同一host timer的描述性分解，不是kernel消融。

P顺序RM/MR/MR/RM，G顺序RM/MR，块内相同循环根顺序、每块轮转4根。一次只驻留一个模型，每session一个冻结warmup+16正式请求，load/unload不入resident请求时间，process总时间另记。同步steady_clock边界含reset、batch构造/交付、decode/sync、轻量输出与token bookkeeping；文件解析、完整向量/文本detokenization与JSON落盘在计时外。没有网络/HTTP队列或draft/k3路径。

G为声明的state-complete response：最后一个emitted token也decode入KV，EOG只记录而不作为正文decode。它不等于默认CLI最后一token或网络服务的结束边界。

## 预算、资源、失败与退出

首次模型加载窗口：北京时间2026-11-13 **23:15:56至23:34:02**，约1085.38秒，低于6小时。共**220请求=16资格+12warmup+192正式**；实际processed rows **51370**，保守永久预留197120 rows；**18次模型驻留部署/18次显式llama_context构造**，达到部署上限，未再加载。8次请求余量未用，不追加轮次。每次先预扣、失败不退款，单自有Job进程/16GiB commit、600秒无完成进度/总6h停止、资源阈值均在执行器内实现；并未证明设备卡死后的即时清理。

开始前的零消耗停止保留：本地模型utility PID29020占有compute context，未创建R/M子进程、额度0。用户随后明确授权处理并保护本对话；仅用路径/命令类型/创建时间绑定的handle终止该OnDeviceModel utility，主进程PID28000只读保护且仍存活，不改设置或ACL，不终止其他任务。以原零预留账本前缀追加接续，没有重置账本或启动窗口。

实验采样温度39–74°C，最高观测总GPU使用8724254720字节(约8.13GiB，含系统)，仍有约4GiB空闲。只读clock/power快照另存，未锁频、未改变平衡电源/风扇配置；启动时AC接入，不能据此作跨天热稳态保证。证据约**1.285GiB**；包含新构建/依赖的整个工作目录约4.46GiB逻辑文件大小，均未触及10GiB证据上限。没有OOM、decode错误、推理重试或正式样本排除。

收尾所有18个自有worker退出0，Job结束、RTX lease释放、无GPU任务排队；主进程仍存活。模型/CUDA实际初始化非零；物理kernel launch及隐式GPU context数未计数、不设已证生命周期硬界。228请求合同独立于旧4096/500账本，旧默认拒绝与失败记录不变。

## 对论文的影响和未完成项

现在可以增加一个**完整模型、固定工作量、不同数值合同的迁移参照**，取代“只有提取算子现代参照”的空缺。本面板P约32.15%是直接实测，不由旧U/B约38.7%推算，两者不可拼接成同一结果。它支持讨论实现/参考策略的执行成本取舍，但不证明保持旧参考可获同样收益、HeteroSpec服务加速或普适5%。

尚未完成：原计划长prompt性能覆盖、自然EOG结束的长自由生成/质量评测、跨窗口/平台复现、HTTP服务或完整speculative链、差异机制与硬件计数器的因果分解。R完整原生链的历史CUDA二进制重建溯源限制也保留。未测项不以预测补齐，不将这些工作自动排队，不继续C2或调优。

完整源码、构建失败、资格/全部P/G原始记录、root/phase图、预算、退出与差异在同目录及RAW_RUN_AUDIT.zip。大体积全词表F32文件保留本机并逐个hash绑定，公开审计包不含模型、厂商DLL或未脱敏全主机命令行；不承诺全部私有二进制已公开。

本轮只更新Draft PR244，不合并、不改论文、不投稿或发布arXiv。
