# 发给 Windows / RTX GPT Work

你负责HeteroSpec的RTX下一阶段，不接管B570。先核对原机状态和仓库最新head。PR104已封存于f997262d6b0accb126a1217c9356745cc8bbf708，PR110本轮结果为dae5aea9f9009a686196dd89981c0ae9699ae612。若原机确已完成，验证receipt后直接进入本新设计，不重新启动六会话、E1或390个parity cells。

完整阅读本目录README.md、PROTOCOL.md、design_checks.py、test_design.py、VALIDATION.json。新工作在隔离分支/worktree，只新增benchmarks/rtx_lowering_envelope_v1/；原始设计保留前瞻版本。不要改旧F0、历史输出、PR102/main、发布、B570或自动化，不merge，不购买硬件/云服务。

本轮目标不是继续扩大PR110的同策略模拟，而是：用实际完整native张量和CUDA执行观察解释PQ/QB成本；测试从固定PR112 DESIGN迁移的query/head lowering；在原量化部署参考和真实较长有效上下文下检验新输入及费用。PR112只是设计输入，不能把B570运行时或producer方案复制到RTX。

一、先实际完成S0，零GPU/model/device query

恢复PR98/104完整native源码、数值DLL、72个E1快照和原参考。核对当前family×arm实际binary路由、编译器/driver/model及源差分。运行本目录18项CPU测试；它们不是native准入。另完成真实GGML图builder、q1原路径、q1..4/D64与128、mask/GQA/stride/output重组和实际serializer的CPU测试。

实现QH_C、QH_D的真实不同图：r=h*q+j，保持原K/V对象与floor(r/(q*g))映射。permuted Q需要真实packing；compact/dense mask、输出恢复全部计费。保持RTX原target mask3与k3、模型精度及draft事务，不引入B570的prefill-MQ/reference128/bulk512。

建立完整backend支持registry及真实placement检查；只通过batch维度必要条件不得标full support。schema里的布尔值不能代替实际CUDA支持查询/执行归属。实际独立GPU census只能在S1授权后进行。

实现runner、独立raw审计、before-start账本、owned PID/watchdog和加载模块记录；对原R与新actor按真实能力登记监测合同，不能再假称所有进程均100ms采样或持续驻留。只在已有安装与ABI允许时准备profile路径，不为取符号改旧CUDA环境。S0上限3600 child秒、1GiB、两轮有范围修订；不是两次编译命令限制，也不允许无限搜索。

二、逐阶段F0与授权，不能自动一口气跑全部预算

S0形成实际F0/支持registry/输入/顺序/工具版本/预算/原机安全阈值并提交认证回读。已有准确有效阶段授权不重复询问；缺少相应F0确认时停在该节点。不把本设计或CPU_PASS当成GPU授权，不借旧未用预算。

S1：1个零compute支持census；按完整、输出前census固定选择QH_C，否则QH_D，否则停止。72完整E1快照×MQ/PQ/QB/QH_C/QH_D×2重放，最多720个单次graph hosts；不得使用PR110的64-key/2-channel裁剪数据。继承MQ own-path、PQ/QB、q1、输入不变和实际placement控制必须通过。QH的有限q>1差异保留，不以结果换variant；它只限制bitwise主张，不自动等于完整endpoint失败。

S1 timing/profile：按profile_coordinates固定24个完整上下文，覆盖三家族/两phase/q1..4并轮换首中末层。真实PQ/QB/固定QH各3个clean timing hosts及1个trace host。clean每host1warmup+8measured，trace每host1warmup+1diagnostic。阶段总上限1009 operator-host attempts、2808 graph computes含288warmups、7200owned秒、4GiB；没有隐式capture-time compute或profile内部replay。

干净时间窗口包含Q/mask物化和输出恢复以及合法完成同步，不放profile或阶段readback。输入/setup/build单列。技术重复不当独立样本。profile输出与clean严格分开、不扣开销拟合速度；观察CUDA活动/拷贝/后端归属时说明来源。无法识别kernel、跨流完成或成本份额就UNKNOWN，不能用CPU enqueue、图数或memcpy量冒充GPU时间/DRAM流量。无profile不阻塞已具其他实际placement证据的软件研究，但硬件解释保持HOLD。

S2另批准：三家族每族1旧曝光输入+1新自然长输入，共6坐标；原R、R_SHADOW、M_QB、M_QH、C_PQ、C_QB、C_QH，共84 fresh requests/processes，无warmups，7200owned秒/4GiB。先原R12counts，再shadow12，再候选60。原R不替换runtime；shadow只作接入控制。完整自然请求、reference端点和实际多行VERIFY必须检查。新pilot输入计入暴露历史；不根据pilot速度挑题/门槛。失败按协议分类与收尾，不为正结果改shader、dtype、q或model。

S3另批准且S2通过：每族18个未见自然输入，code/math×64–127、128–255、256–768三个实际token长度层×每层3；排除项目历史ID/token hash及pilot，先metadata固定hash选择，不截断或填充。所有输入须在继承ctx内容纳cap128与lookahead。六固定主臂、三家族、三会话：972measured+972warmups=1944starts/972processes，43200owned秒/8GiB。会话1距0结束≥1h，会话2距0开始≥24h且距1结束≥1h。仅两日期块不宣称三独立日期。

S3完整原R资格与全部预定坐标通过后才给相应family的qualified ratio，失败/缺失不变成快速成功子集。保留所有任务/长度/家族退化、实际visible-key范围及padding范围。不从tensor extent=256推长上下文，不把prototype图reshape当普适方法。没有>512实际有效上下文就不声称该范围。完整time gate前不汇总；不使用request级bootstrap或按结果扩样本。原生graph/row计数不等于kernel或算术DAG。

三、结论与交付

对话里直接回答：实际完成阶段和准入；模型/算子/graph/warmup启动、失败、未启动、时间和空间账本；PQ/QB/QH各自的合法性、实际后端、数值与完整请求资格；所有成本、退化与新输入范围；剩余代价是什么、是否只是软件问题、哪项硬件假说真正值得继续。

保留必要源码、原始records/tensors/trace、manifest、完整分析和独立fresh-restore重建。不只再写一份计划，不造新硬件通过或5标签消融。若QH不支持/无收益就保留结论，不能偷删QB强基线。R与M/C比较各自含义按协议分开，不把全部R/C改进归给投机或attention硬件。

实现/結果提交到本新分支或从此设计固定head分出的单独Draft结果PR，回链本设计；不重复创建设计、不merge。不改当前论文；给可用于论文的claim/evidence表即可。硬件只能提出下一步具体机制与预算，不能自动做RTL、新模拟器或新GPU实验。
