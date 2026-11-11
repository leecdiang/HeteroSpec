# RTX普通参考成本闭环：CPU复算报告

本轮完成普通参考强基线缺口。固定target_scopes候选相对普通标量R，生成**1.170124448×**、整请求**1.741569262×**；四轮GM方向均更快。相对matched target仍为1.169237971×／1.035071366×，整请求第二轮0.940220031×明确保留。这是有限面板正向结果，不能把1.7416×全部解释为投机验证贡献。

新增模型请求、target/draft forward、warmup均为**0**。没有启动native程序、runner、服务器、profiling或runtime恢复，没有修改模型/运行库/驱动/论文或旧PR。此次只读取原归档与已恢复B记录，编写并执行CPU分析。

## 证据与资格

原ZIP122395102bytes，SHA25688ff7d52da4815dee11d7232e36b292fd77fe18a414e01aca41e860cdd4cade5；全ZIP CRC通过。10151logical files/6542objects身份符合。B_RECORDS SHA256a6e562625f229fd38eed31a9492bb04db269f78355391ab41cf31c6d2dce6bd4。读取并核验498个B及计时来源相关文件，未重新审计C/D raw。打包源码250058d…、B运行源码7b8c6fb…、公共PR62头8dfa60a…分别保留。Phase2依赖ZIP的身份与所读计时源码匹配。

384/384正式请求，16/16原warmup排除；四条件每个96/96完整保存数组及endpoint资格通过，24/24参考跨四轮稳定。每条独立raw与RECORDS聚合一致、唯一键和轮转顺序一致；输入/程序/source身份、cache_n=0、无truncation及参数一致。参考实际11–128token，23EOS/1cap；完整response数组不代表未记录的内部样本流。原bridge16请求/4warmup未混入成本。

## 主要成本比较

|Baseline / candidate|Timer|Task-median GM|Descriptive95% interval|Faster/slower tasks|Round GM1/2/3/4|
|---|---|---:|---|---|---|
|scalar_reference / target_scopes|generation|1.170124448|[1.117013, 1.217681]|22/2|1.168805/1.173517/1.158128/1.173160|
|matched_target / target_scopes|generation|1.169237971|[1.117115, 1.217153]|22/2|1.169667/1.048849/1.175118/1.176428|
|scalar_reference / matched_target|generation|1.000758167|[0.995290, 1.007752]|11/13|0.999263/1.118862/0.985542/0.997222|
|scalar_reference / target_scopes|whole|1.741569262|[1.654608, 1.827079]|24/0|1.726493/1.736437/1.726798/1.736735|
|matched_target / target_scopes|whole|1.035071366|[1.004552, 1.063481]|17/7|1.028699/0.940220/1.051749/1.044236|
|scalar_reference / matched_target|whole|1.682559598|[1.589801, 1.766329]|24/0|1.678326/1.846841/1.641835/1.663163|

全部比值为baseline/candidate，>1候选更快；先每题每条件四个绝对ms取中位数，再比值，再24题等权几何平均。相对普通R的生成慢任务为MBPP/124, MBPP/393，保留不删；其余22更快，整请求24均更快。matched目标整请求17更快/7更慢且有第二轮反向。绝对费用见下表，表中跨任务中位数用于描述，不是比值GM的分子分母。

|Condition|Median across24 task medians: generation ms|Whole ms|
|---|---:|---:|
|scalar_reference|443.335000|1190.082875|
|matched_target|443.713250|689.247100|
|target_scopes|390.874000|675.346025|
|all_scopes|411.536250|701.377575|

主候选固定为target_scopes，未按新结果切换mask。历史practical_decode_gain规则（generation≥1.03、whole≥1、至少3/4轮generation>1）在R及matched两比较通过；该历史门槛不把事后追加的R比较变成前瞻实验，也不是部署保证。

## 解释范围

R/matched整请求1.68256×而生成1.00076×（描述区间跨1）。R使用全局UB1，matched使用mask3/UB4；其prefill等执行路径也不同。因此总整请求改善包含路径改变与投机，不能由GM差推导attention、draft、KV或同步的费用比例。逐题48项与两个GM乘法恒等式均通过，它们只是算术核查。

generation采用原predicted_ms，首样本/预填充及部分末尾记账不在此字段；whole采用收到并解析resident HTTP响应的host wall_ms，模型加载/热身/退出另属边界。B未启用条件式hs::move状态移植；相关代码存在不等于本次承担其费用。详见SOURCE_TIMER_AUDIT。四轮各四个独立resident进程，不是同一进程同时测四模式。未认证环境完全平稳或生产并发性能。

## 描述统计与独立验证

固定20261008、PCG64、10000次任务聚类bootstrap、linear/type7分位数；先合并重复再重采样24题。这是已暴露面板的描述区间，不是跨模型/任务总体保证。旧20261005/4000/sorted99与3899规则另算，旧三组比较的点值、各轮与区间均复现。新parser不导入旧runner或资格/成本函数；第二复算器直接从raw重建数组、键、绝对费用、配对与分位数。16591项检查通过，六负例（缺重复、重复键、倒置比值、错单位、不合格输出、非有限成本）全部拒绝。前期CPU实现错误完整保留在ANALYSIS_REPAIRS，未改变原数据或删除失败。

## 论文交接

结论分支：**FINITE_PANEL_GAIN_AGAINST_ORDINARY_AND_MATCHED**，同时保留matched整请求轮次混合与计时限制。可写RTX具体局部方案的完整参考合格加速、自然状态/当前路径有限诊断，以及数值资格与实际工作量需要共同验证。不能写普适无损、全局最优、唯一kernel原因、功能正确率或跨平台普遍加速。

PR65的B570 E119/120、强R负结果与GPU_NEXT_ACTION=STOP保持原样，本轮只是补齐其deferred RTX raw item。C4更宽k的成本负结果保持各自会话分母。接下来可以进入全稿证据整合、重构、编译与审稿，**本任务没有改写论文**。PAPER_HANDOFF含英文段落、主张映射与全稿顺序。

## 次要比较（全部保留）

|Baseline / candidate|Timer|Task-median GM|Descriptive95% interval|Faster/slower tasks|Round GM1/2/3/4|
|---|---|---:|---|---|---|
|scalar_reference / target_scopes|generation|1.170124448|[1.117013, 1.217681]|22/2|1.168805/1.173517/1.158128/1.173160|
|matched_target / target_scopes|generation|1.169237971|[1.117115, 1.217153]|22/2|1.169667/1.048849/1.175118/1.176428|
|scalar_reference / matched_target|generation|1.000758167|[0.995290, 1.007752]|11/13|0.999263/1.118862/0.985542/0.997222|
|scalar_reference / all_scopes|generation|1.152348388|[1.099880, 1.199192]|22/2|1.156386/1.150881/1.135925/1.142547|
|matched_target / all_scopes|generation|1.151475377|[1.099968, 1.198554]|22/2|1.157239/1.028617/1.152590/1.145730|
|all_scopes / target_scopes|generation|1.015425943|[1.007525, 1.024253]|20/4|1.010740/1.019668/1.019546/1.026794|
|scalar_reference / target_scopes|whole|1.741569262|[1.654608, 1.827079]|24/0|1.726493/1.736437/1.726798/1.736735|
|matched_target / target_scopes|whole|1.035071366|[1.004552, 1.063481]|17/7|1.028699/0.940220/1.051749/1.044236|
|scalar_reference / matched_target|whole|1.682559598|[1.589801, 1.766329]|24/0|1.678326/1.846841/1.641835/1.663163|
|scalar_reference / all_scopes|whole|1.690201646|[1.610916, 1.768226]|24/0|1.702378/1.685808/1.650840/1.675488|
|matched_target / all_scopes|whole|1.004541918|[0.975846, 1.031662]|12/12|1.014331/0.912806/1.005485/1.007411|
|all_scopes / target_scopes|whole|1.030391412|[1.022464, 1.038939]|23/1|1.014165/1.030032/1.046012/1.036555|

原科学输入/归档的post-audit通过，图表SVG/PDF另提供PNG查看。所有新分析源码、小型派生表与交接仅添加独立研究目录，Draft PR不合并。交付身份由后续DELIVERY_RECEIPT记录。
