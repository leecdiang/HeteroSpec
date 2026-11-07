# 交给B570执行端

在真实Intel Arc B570主机读取并核验本PR actual head和新目录所有Git blobs。执行 `docs/experiments/b570_memory_followup_20261011/PROTOCOL.md` 与 POLICY/ASSETS；这是#86零forward边界后的新研究。不要修改#85/#86原来的512MiB门槛/失败记录，不把旧209MiB加载观察标成已能推理。

优先STANDARD_Q6（8B Q6_K目标、1B Q8/Q4草稿、512MiB），TIGHT_Q8为独立补充（8B Q8目标、1B Q4草稿、128MiB）。两profile一起F0A登记；完整下载Q6并核验bytes/SHA、运行时全词表/EOG/guard；元数据前缀核验不是完整模型hash。各profile都用自己的同文件普通推理参考。两profile预算640工程+800确认、8GPU生命周期小时各自独立，总2880/16小时，不互借，不自动降精度/offload/门槛/题目。

核验并改造实际native加载器、worker、controller及分析器，使显式profile决定正确阈值；拒绝未知profile/不匹配量化，保留signed负预算、真实分配失败及原生兼容性保护。旧#86加载器有硬编码512；旧#85 plan.py的host/assets/select也有Q8-only和正向筛选规则，不能直接拿其PASS为本轮背书。新审计工具只用于历史复算和静态检查，不能作为推理批准器。

实际同PID、确切B570 dedicated heap测预算，真实生成图/工作区完整分配；batched k3用至少4输出容量，不借用旧out1日志。记录全GPU权重/KV与实际内存驻留证据；UNKNOWN只可给诊断，不称GPU驻留资格通过。所有工程峰值/边界/capture-reset/native提交先通过。优先处理能完成Llama家族证据的Q6配置，不再运行新Qwen优化研究。

两profile均用曝光工程题选择唯一候选；不要只让正收益候选获得独立确认。工程保留25次未修复N诊断，原生首次分歧和repair scope如实记录，NO_TRIGGER不能声称修复必要性；N不加入正式四arm的全矩阵资格门槛。两个profile工程都结束/选择冻结后，才共同F0B封存新24题、全部程序/资产/计时/平衡顺序/统计，并实读remote blobs。随后用无AI/API调用的串行控制器运行两个连续新会话；同日可行，无需等RTX，但题目须排除RTX完整预留池。正式不补跑，失败原位保存并给所有qualified ratios=null。

本轮native worker/controller在本设计PR中尚未实现或编译核验。由执行端依据恢复的实际源程序完成实现、负向测试和两次封存后自动推进已授权范围；不需要每阶段等待聊天批准。创建新的结果Draft PR，保留每个候选、负结果、旧新研究总消费、完整可恢复证据；独立复算与实际Git恢复验证后更新该PR。若停止也提交具体MEMORY/IMPLEMENTATION/RESIDENCY状态，不能把静态PASS写成实验PASS。不merge、不改论文。
