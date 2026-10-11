# RTX 最终证据与基线补全协议

状态：PROSPECTIVE_NOT_EXECUTED。base为#84固定head；本文件与DESIGN.json共同定义新研究，不改变#83/#84冻结与结论。实际native/controller实现、工程资格和新GPU测量尚未执行。

## 1. 问题与固定范围

判断R/M的请求收益是否需要query-batch改造，及C3是否优于预定集合内更强的普通解码。三个固定家族Qwen/SmolLM2/Llama，target/draft Q8_0及六个完整hash继承#84。不增加家族、量化、FA、并发、k搜索或外部方法移植。旧自然状态/路径交叉、16-mask与宽度反例用于正文机制证据，不重做同义干预。

继承ctx1024、target greedy/seed123、draft rank0、F16 KV、FAoff、single seq、threads24、draftUB1、requested batch2048/effective1024。普通ub网格为1/4/32/128/512，均不超过有效容量。target模板仅渲染一次，原生prompt IDs供该家族全部arms共享；prompt<=768、cap128，不缩短题或根据输出调整上限。公开转换字节和revision已绑定，官方checkpoint转换血缘仍NOT_CERTIFIED。

实际恢复#84作者源码/EXE及原数值DLL；新controller以新目录实现。原生server非capture计时，新增计数不能改变数值路径。每worker日志包括实际UB、output容量、全部层及KV GPU映射、runtime/source/model hashes。普通arm不得装载draft。继承#84的AC/显示GPU/电源/冷却准入，以冻结host字段记录，不在结果后换策略。

## 2. 工程与普通基线选择

每家族复用12个已暴露工程输入，重新支付R。先运行5UB×12题×2重复=120个ordinary请求，完整token IDs、原生EOG/长度/停止边界等于稳定UB1 R方可参加选择。R自身不稳定则该家族停止。

选择完整合格者的两轮等权log费用最低配置；精确tie选较小UB。选择同时包含UB1/4，所谓R_prod只是此网格内最优，不声称全局最优。失败配置/费用/缺失全部保留。不得删失败任务或从确认数据选普通基线。

M0=ordinary/mask0/UB4；M3=target-only/mask3/UB4；C3=spec/mask3/UB4/k3。工程加N=ordinary speculation/mask0/UB4/k3，12题×2重复，验证本数值合同中实际分歧；N只作有界修复必要性诊断，不替代#84完整N结果。M3与C3同样各24次。无正收益准入门槛。

每家族360工程预算，包括全部load-only探针、warmup、forward、辅助decode、失败与实现修复；合计1080。ordinary120 + M3/C3/N72 + warmup及资格/profiling均占该预算。修复保留每版本，重新做受影响资格，不重置预算，不扩空间。

工程须核验actual图/phase/reset/graph reuse/capture开关、cap1/2/3/4/31/128、原生EOG、rollback和最长768 prompt。M0/R_prod可能不保参考，照样保留并完成其有限测量；未合格的普通路径不成为合格速度基线。固定C3实现不满足自身工程/内存条件则该家族按停止分支交付，不重选mask或k。

工作量归因与盈亏平衡必须按 [MECHANISM_PROTOCOL.md](MECHANISM_PROTOCOL.md) 做有界尝试：固定6个已暴露MBPP/GSM8K输入，R/R_prod/M3/C3四arm×baseline/lite/heavy=每家族72完整工程请求，均计入360预算。只用无新增同步的有效lite计时校准；heavy只验证计数/形状。正式冻结lite通道和工程校准模型，不从新任务重拟合或为Smol追正结果。

## 3. 新输入、共同冻结、排程

#84全部输入已暴露。新确认24题=12 MBPP+12 GSM8K，完整可访问历史按ID与描述排除，MINIMUM_EXCLUSIONS只是93个已绑定最小排除项，不能替代完整host/PR/归档审计。未知主机历史如实披露。

两个平台共用确定性分池：NFKC、casefold、压缩空白后的description，计算SHA256('heterospec-final-closeout-v1|'+domain+'|'+description)整数模2；RTX取0，B570取1，再按固定hash排序选每域12题。相同描述归同一平台，不以任务标签按结果分流。完整审计后无足够题即停止，不更换数据集/题域；同时排除任何新预留任务。

F0A在任何新forward/warmup前绑定完整设计、曝光题、native/controller、数值DLL、模型、计时、预算及逐条源码bytes；commit/push后实际Git blob读回。工程结束先冻结三个R_prod选择和停止状态，再生成/封存确认输入及完整F0B。F0B实际remote byte-readback先于任何formal，包括其warmup。结果后的计划文件改动禁止。

正式5条件R/M0/M3/R_prod/C3×24题×5轮×2会话×3家族=3600；每block新resident进程，一个固定synthetic cap128 warmup，共150次。条件重复即使配置相同也独立支付。

session0使用5个循环Latin行；session1逐行反转，每arm每session在每位置出现一次。同block任务顺序以冻结hash确定。家族会话顺序session0 Qwen/Smol/Llama，session1 Llama/Smol/Qwen；保留实际UTC，不等待新的日期。相关跨日期判断仍null。

## 4. 费用、资格与结论

主timer为完整resident请求提交到完整response/IDs/stop解析核验，计入JSON通道、prefill、proposal、verify、采样、KV/rollback/sync、响应；加载、warmup、冷却、磁盘hash/persistence分账。不引用仅target kernel或旧generation timer替代request费用。

每条件每家族240 planned槽，所有已启动slot只能完成一次，正式retry0；FAILED/STARTED/MISSING原样保留。必要R完整稳定、比较两arms全部完整并符合完整raw/EOG/cap合同，才有qualified ratio；无关失败arm不抹掉其他完整比较，失败/不完整比值null，完整费用另作diagnostic。不裁剪raw后缀、不多数票参考、不按passing子集报告收益。

统计按每session/task/arm五轮绝对费用中位数，域/24题log比平均，再两session等权平均；报告所有task/session/domain与退化任务。主部署R_prod/C3，matched M3/C3，归因M0/M3，另报R/C3、R/M0、R/M3、R_prod/M3。不根据主结果重选R_prod、k、mask或输入。

若M0本已保参考且同样快，R/M的较大收益不能全归attention改造。若M0失败而M3通过，可支持局部约束使该并行路径获得资格。若C3未胜R_prod，收缩该配置部署加速主张；若Smol仍负，保留并给出拒绝使用draft的有限决定。不将MBPP/GSM8K标签变成事后online routing规则。

总上限1080工程+3600formal+150warm=4830 paid单元；owned GPU-process lifetime16小时、外层7天。失败/加载/等待均记完整生命周期，不跨家族挪预算。达到停止线交付已有结果与缺项，不补跑。跨日、energy、多请求吞吐不属于最终必需证据。

## 5. 交付

独立结果目录benchmarks/rtx_evidence_closeout_v1与对应scripts；完整ledger、原生数组/停止边界、绝对费用、phase证据、runtime身份、全部ordinary候选和选择费用、负例与停止原因。独立CPU重算、真实本地和Git-hosted档案恢复；新Draft结果PR接在本补全设计上。旧#80/#84及paper/release只读。

