# e10：固定 few-row MMQ 的真实数值差异与停止决定

本轮取得了真实GPU数值证据，结论是：新上游路径可能成为现代性能参照，但不能替换旧逐位参考；本次独立资格未通过，因此没有U/B计时数据，也没有理由继续盲写一个通用权重复用C2。

## 已核对的原结果与本轮选择

PR230 head ba019f30522352c87cac2cc527082ecc6c73ed97、PR234 head304dcbff6d17461237774464c67ce8cb0ed60189均为Draft、未合并。e08 C/B投影1.147676、含量化1.126389；e09 C1/B分别1.022156、1.026132。二者各自慢于同期B；不是严格同会话C/C1对照。C1把两组顺序化，放弃跨组寄存器权重片段复用，因此不将两轮差异写成occupancy因果。旧原始数据、构建、失败记录和账本在前后均核对哈希。

只选择一个预注册诊断D：冻结旧B对照固定上游U，判断源代码推导的适用性和数值合同差别；仅两者各自资格通过后，才允许把U作为不同数值合同的性能参照计时。未开发/扫描另一批C候选。完整源码对照、门槛和资源见 [SOURCE_COMPARISON_ZH.md](SOURCE_COMPARISON_ZH.md)。

可证伪问题是：真实8行Q8_0输入能否使用上游few-row布局，并同时满足本轮独立U检查和旧逐位合同？机制是int8 MMA+每warp cp.async ring，区别于C/C1的DP4A复用。预期收益可能来自tile/MMA，而非“更低寄存器数”；代价是新量化布局、不同算术顺序和69KB共享区。可能失败于数值不等价、快速除法的量化半整数边界、资源限制或本机无收益。

## 输入和编译身份

使用e08已验证的真实8-token捕获，不是q32前8行替代。权重是Qwen3-8B-Q8_0的blk.0.attn_q.weight，K=M4096，F32 activation为[4096,8]。重新读完整GGUF SHA256并直接读其目标tensor文件偏移1350722848，确认17,825,792B与原weight.bin相同；producer exe、实验DLL、原activation、Q8_1、backend输出以及旧捕获回执身份均复核。模型没有加载到runtime；模型文件只用于只读哈希/原始tensor核对。

| 对象 | SHA256 |
|---|---|
| 模型文件 |408b955510e196121c1c375201744783b5c9a43c7956d73fc78df54c66e883d6|
| weight |822086ad0b394e3f032f5a95a0193df9a6f2f628f58cee4b2d2c44ba4bb26b5e|
| activation F32 |47009f80cddac6ccefd830bd4a2763c6f5fa1a6cf96fb40fb2b6d1555e0d2836|
| 旧Q8_1 |caaf90580faecb85103fb19d9f76f4d8210c3fd2ca72a7da1d28971537000901|
| 旧backend输出 |6f4c7a410b441c266a34f20f5a5c1c2bc67ef4a3ef5e622e4a005cadd42a0fd0|
| 本次operator-upstream.exe |bf0782998bafb9ec63215f9dcdef382fffb40271df113a0af7006da4253c0f4f|

build001与build002均保留，后者只完善失败结果输出，数值device定义未改。选用build002，冻结9862个输入，冻结清单SHA256=4dc2b7213e82b9c79fa28b9b0262c4088e70b8f673dc42416db6ba877af73a0e；编译/链接成功、实际依赖无漏项、全部输入前后不变。sm120a，-O3/-use_fast_math，旧B与新U分离TU/headers。没有换掉冻结B、后端或旧参考。

## 准入、尝试与真实结果

CPU预算/过期门限/溢出故障测试通过；量化fragment的36864字节映射独立验证全部覆盖；524288个权重scale与1024个activation block满足预注册误差界的有限值域。它们是CPU证据，不是GPU性能或正确性替代品。

第一次Windows管理员启动返回“用户取消”，没有创建controller、profile、预留或GPU工作；同一已批准冻结入口重发后成功。管理员控制器PID26588在北京时间10:25启动。只读全主机任务/服务/进程快照、canonical device lease与独占runner、NVML水位、固定UUID、同身份受限CPU子进程与ETW起止检查均通过。54个受保护模型路径拒绝访问。只沿用批准的同名零能力profile与staging继承权限，无新ACL、模型目录、Windhawk或安全设置变更。

| 阶段 | 结果 | 实际内容 |
|---|---|---|
| 原数据/源码/模型tensor身份 |PASS|只读完整哈希与字节核对|
| 固定上游10变更文件 |PASS|Git blob+SHA256|
| 编译、CPU预算与隔离准入 |PASS|无CPU阶段CUDA初始化|
| 新GPU资格001 |FAIL|10:25:51预留14；10:26:00 native退出2|
| B完整Q8_1+输出 |PASS|2次重放，全部36864B/131072B逐位相等|
| U独立CPU量化整数q |FAIL|10/32768值不等，每项差1|
| U独立scale检查 |PASS（子检查）|1024个float尺度均在8ULP内，最大2ULP|
| U完整量化dot误差界 |PASS（子检查）|32768输出均在gamma64界内，最大误差/界0.03830|
| U旧参考逐位保持 |FAIL/NON_EQUIVALENT|24个q不同、1024个scale不同、32766个输出float位模式不同|
| U第2次确定性重放 |NOT_RUN|第1次独立资格失败即停|
| 预热/配对计时/occupancy/流量采样 |NOT_RUN|无性能样本；实际occupancy/L2/DRAM均NOT_MEASURED|
| 模型/forward/服务/66格 |NOT_RUN|没有扩大|
| 结果保全、profile删除、控制器退出 |PASS|保留全部7个profile文件；删除HRESULT0；10:27:52 STOPPED|

U独立检查在CONTRACT.json及源码中提前规定：所有q等于CPU float32 RN除法量化器；1024个D4尺度有限正值≤1、距CPU尺度≤8ULP；每输出以实际、另行验证的U量化操作数计算独立double dot，满足gamma64×绝对block贡献之和+128×FLT_MIN；重复输出/量化逐位确定。最后一项没有运行，不能将部分PASS拼成资格PASS。

实际U结果：相对独立double量化dot最大绝对误差5.95757358e-8，界失败0；相对旧输出L2差0.0002370446208。完整逻辑q、尺度、32766个输出差异均逐项保存CSV，原始二进制保留本机。没有篡改参考或选择性删值。

离线CPU复核重现全部10个量化差异：都在或紧邻舍入半整数边界、差1。冻结生成PTX的量化入口包含 `div.approx.ftz.f32`、`rcp.approx.ftz.f32`及roundf lowering，见FAST_MATH_DIAGNOSIS.json。NVIDIA文档说明use_fast_math包含较低精度除法：[CUDA floating-point computation](https://docs.nvidia.com/cuda/cuda-programming-guide/05-appendices/mathematical-functions.html)。因此CPU RN精确除法oracle与编译后的U并不天然逐位等价。这里的推断是“独立oracle合同/快速数学兼容性问题”，不是已定位的上游kernel错误。没有修改编译器选项、改CPU标准或重试将本轮改成成功。

## 账本、执行边界与清理局限

新family与旧账本完全独立。启动前415分配为首次资格14、一次定位后资格修正14、计时355、余量32；原本资格最多8次，计时最多320次（预热8、投影120、完整算子192）。实际仅资格001：B量化/投影各2，U量化/投影各1，共6次显式提交前许可；永久预留14，未用预留8不退回，401未预留。没有资格重试、计时预留或未来排队。闭合本次控制器，不自动沿用余额。

每条作者显式dispatch在第一次可能提交前调用e10_reserve，检查额度不溢出和109秒单调时钟；native单进程、2GiB commit的kill-on-close Job原子纳入，native Job119秒、外控120秒。CPU门限测试验证exact14/refuse15/expired/overflow。源码调用点数只是检查辅助；真正限制来自每dispatch的执行前拒绝，不等于物理launch统计。

资格任务包括现场复核共8.984秒；native从grant至退出约0.23秒，未计真实GPU计时。分配了4个device buffer共18,124,800B。观测水位从约296.7MB到463.6MB设备使用量，41°C；这是全设备稀疏采样而非峰值证明。结束只读nvidia-smi无compute进程、0%利用率、38°C，memory.used报告0MiB，均仅时点观察。

失败发生在资格检查抛出异常，正常streamDestroy/cudaFree语句未执行，依靠自有进程退出与Job关闭；已确认子进程退出，不能保证设备异常时立即回收。ETW使用partial_close，loss计数[0,0,0]，未完成正常终态模块闭包验证；不能把loss为0称观测完整。NVML/ETW/watchdog均不证明隐式context或全生命周期physical launch上界；后者仍未知，原4096硬合同仍NOT_CLOSED。CUDA runtime/driver实际初始化存在，不能报告本轮context/launch全为0。模型加载、decode、新捕获和数值根DLL显式加载均0，作者显式应用kernel许可6。

结束后重新核对9862个构建输入、49项旧身份/账本/失败记录及新staging文件ID/哈希，全部不变。没有未知锁删除或无关进程终止。最终全主机相关worker/任务/服务为空、canonical锁和本轮runner lease不存在、controller已退出。快照不保证未来外部新建任务；PowerShell深层CIM元数据有Depth7警告，顶层任务/动作/状态/相关过滤保留私有原记录，公开只给摘要。

## 继续与论文判断

不立即开发C2。上游已实现广泛类型、2–24列门槛下的MMA和权重staging复用；再次提出“把四列组共用一次权重读取”不足以支持一般性kernel新颖性。也不能用C1降低寄存器的单例，或未测occupancy/内存流量，解释C的负结果。

现代强基线需要补测；本次没有资格通过的上游性能样本，不能说U更快或更慢。固定上游可以成为另一个数值合同的现代参照，但不满足旧逐位保持目标。本例还显示lowering表示决定是否命中few-row，值得优先分析“保留旧参考的调度”和“接受新版算术合同的最强实现”两条明确分开的路线。

更值得的下一步是先在CPU独立建立、证明并预注册GPU快速除法允许误差区间与量化半整数歧义集，再用完整U量化/输出的独立数值合同验证，不事后豁免这10项。或明确选择精确除法的新U变体，并承认它不是默认上游。之后另立合同，比较正式固定上游host/PDL配置及B，两条投影/含量化边界交替配对，保留全样本；不能把当前FAIL的U当性能合格。若要提出严格旧逐位新kernel，应先有不改变K/缩放/归约的具体机制和编译报告，而非参数扫描。

若未来单输入结果通过且显著，也仍需跨K/M/N、量化类型、真实token/前缀、resident/冷启动、设备和完整请求链验证。没有修改/提交论文、冻结基线或生产准入，没有合并PR，没有普适5%或服务/k3收益结论。
