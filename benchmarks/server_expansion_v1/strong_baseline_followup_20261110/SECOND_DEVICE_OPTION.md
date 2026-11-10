# 可选：第二张A5000上的干净重建与配对复测

**OPTIONAL / DEFER / NOT_AUTHORIZED。** 本文件只是响应审稿建议的设计，不说明当前已分到第二张卡，不触发作业。最多另一张已授权A5000；不扩张到第三张、不租卡、不做tensor parallel、双卡draft或N/X全分支。它不是主论文必过门槛，不完成时主研究可以结题。

## 1. 明确价值与预先决定

检查隐藏工作目录依赖、构建差异、设备偶然性与最小复现入口的摩擦。只能称“相同GPU型号、第二物理设备的干净环境稳健性检查”，不称新架构、独立实验室或新工作负载总体证据。

**是否执行、源版本、构建方法、预定六根子集、政策、顺序、统计及预算在主S3新根任何模型输出前冻结**，不能看到主卡group差才上第二卡追正号。源版本/共同policy沿用F1冻结，子集选择规则在F0固定、实际IDs与主F2绑定；先前暴露开发根S2只作诊断，不据其方向挑第二卡输入。可在主卡完整交付后执行，但激活意向/清单已事前固定；晚决定的研究只能明确标成新post hoc研究，不混作本项事前复测。没有单独窗口/额度批准就继续DEFER。

## 2. 干净重建而非复制工作目录

从 `MINIMAL_REPRODUCTION.md` 单一入口，在第二设备新worktree/build/output目录获取固定源和已声明可获取依赖、模型身份及licenses。不复制主卡ELF、private绝对路径、缓存或历史oracle当作已合格。记录编译器/toolkit/driver/SM数/型号、完整source与对象闭包、ELF及实际模块、build耗时与失败。

可核验共用只读model bytes，但SHA/路径、I/O与访问许可明确；不能依赖未列出的私有wheel、临时header或历史working-directory import。不要求下载全部历史KV归档；由本设备自己的R和必要新捕获产生本项证据。

三臂G/B/C全在第二卡上运行，并保持主卡冻结的whole/M/共同graph政策/精度/参考语义/endpoint。各卡性能差异可存在，不允许G放卡1、B放卡2、C放卡3直接比较。CUDA/cuBLAS的一般复现说明不能替代此自定义量化路径的数值资格。

## 3. 自己的R与资格

第二设备重建独立pristine scalar R，不链接candidate patched对象。每根两次独立R请求，最低**12 R**；每根每臂完整heavy bridge最低**18**。真实typed operand逐列gold、batch activation量化字节、完整151936维输出、64层active KV/frontier、物理width/路径、输出所有权、容量/EOG/reset、heavy/clean及所选graphs状态按S1完整检查，额外请求明确计入。

这30个请求只是六根重复R+桥接的下限，**不保证覆盖全部第二设备资格**。共享实现源码不允许自动复用主设备数值资格；无法完整资格时停止，不缩减为argmax或跨卡hash比较。模型/题目输入可相同，R产物必须独立产生。若第二设备所选graph政策失败，记录稳健性限制，不临时换policy/参数再算成功。

## 4. 固定6根、三臂、三轮

主面板按输入排序冻结后，取code前3个root槽0/1/2，math前3个槽6/7/8；第二卡将其映射为replica_slot0–5。映射在主输出前固定，不按表现换根。无主S3实际输入冻结则本项不能自己另选六个“更好”的root。

6根 ×3臂 ×3轮 = **54 measured +54同根完整warm =108 logical requests，54 fresh workers/model loads**。每worker与主面板同合同：同根warm、完整reset、立即measured；reset、最后fence与owned outputs均按S3 service边界处理。每round根顺序旋转0/2/4；每root取主顺序表对应replica_slot行的前三列：

| replica_slot | 主root槽 | 三轮臂顺序 |
|---|---|---|
| 0 | 0 (code) | GBC / BCG / CGB |
| 1 | 1 (code) | BCG / CGB / GBC |
| 2 | 2 (code) | CGB / GBC / BCG |
| 3 | 6 (math) | GCB / CBG / BGC |
| 4 | 7 (math) | CBG / BGC / GCB |
| 5 | 8 (math) | BGC / GCB / CBG |

三轮共18root blocks：全局六排列各3、每臂各位置6、每个块内有向邻接6；每根每臂各位置恰一次。每域各位置平衡，但两个域采用互补orientation，域内邻接不全覆盖，不做域间机制归因；跨block/cross-worker carryover也不全平衡。CPU脚本实际枚举并输出矩阵，不能把global balance叫完全随机。

## 5. 报告、不池化、不追样本

每根三轮log配对C/B，展示全部六根、每次warm/measured、prefill/q1 decode、方向、几何均值、caller与所有成本。B/G、C/G作为描述性附表。样本小，以六根点估计/范围为主，不借重复测量提升独立N。

同时展示主设备同六根**全部四轮**的对应log配对，以及第二设备三轮的值与逐根差。不得选择主卡三轮来凑相等，不能把两卡计作12新根，也不池化制造更窄主CI。本项不作新的确认性显著/等价声明；设备间差异是该两个设备/窗口/构建组合下的描述，不是卡型号或架构因果。

若不一致，保留原结果、构建/环境差与不确定性，不按第二卡表现调参、挑轮次、追加第三卡。正确负结果有效；缺失/失败panel只报告partial，禁止选择性重跑成功臂。真正需要新调查时另提范围与授权，不在此项暗中扩张。

## 6. 新预算、独立安静窗口与收尾

建议**待批准**增量ceiling192请求：108panel +最低12R +18bridge +至少16失败/收尾 =154，最多38剩余额度供必要独立gold、额外资格、probe等。精确完整资格若需要更多就不准入，192不是“保证足够”。行数逐job公式；全局未明确批准更高row ceiling前仍受历史32B 2,000,000限制。

两层账本同时公布：本设备本阶段增量，以及包括主卡全部历史与新尝试的32B累计总数/row。继承最新ledger前缀，不能新卡目录从零后不报总成本。原514 +主阶段上限256 +S3上限384 +本项上限192 =**1346**只是所有上限全用的假设最大请求数，不是授权；B2仍独立8B账本，不借额度。

全阶段按自身R/heavy/full-model worker类别估计load/hash/warm完整caller，加保存/传输/重算与900s收尾余量；不得直接拿主卡轻operation成本填入。新的私有GPU UUID、CPU/RAM/disk/安全reserve、时间窗和主机共享资源协调需明确授权。保护GPU0和外部任务。

两张卡的**正式计时使用不重叠的安静窗口**；另一卡同时编译、全模型hash、模型加载、归档/压缩或重I/O会竞争CPU/内存/磁盘，不能只凭不同GPU宣称无干扰。可在获准范围并行零计时开发，但不得侵入任一clean window；记录host活动与全部间隙。无可用窗口就DEFER，不重排已经进行中的完整主panel。

交付包括最小入口从空目录的完整执行记录、source/build/环境差异、独立资格、108操作与54caller、两层账本、全部失败、字节/统计回读及锁/资源释放。主研究结题不等待这个可选项。
