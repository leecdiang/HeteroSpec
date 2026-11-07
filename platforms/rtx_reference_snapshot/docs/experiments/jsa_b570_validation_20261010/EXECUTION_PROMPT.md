# 交给 B570 平台的执行指令

请从本 PR exact head 读取 [README.md](README.md)、[PROTOCOL.md](PROTOCOL.md)、[DESIGN.json](DESIGN.json)、[COORDINATION_SNAPSHOT.json](COORDINATION_SNAPSHOT.json) 和 [SOURCE_BINDINGS.json](SOURCE_BINDINGS.json)，执行 **B570独立SmolLM2第二家族验证**。本方案内有限准备、冻结和实验已获用户授权；不用等RTX完成，也不用额外停在PREPARE_ONLY。

1. 新建study root，恢复原Qwen数值资产与PR64私有phase-binding源码/DLL，执行预先冻结的32请求桥接。验证actual设备、模块、动态offload和capture等价；不补跑旧E缺槽。
2. 固定快照中SmolLM2-1.7B/135M Instruct Q8_0的相同GGUF哈希，重验actual全词表/EOG/tokenizer。R=普通UB128；N=原old_N1/k2；M=matched target；C=唯一canonical-prefill原位UB128→UB1/k2候选。保留ctx1024/threads10/Vulkan，不移植RTX mask3。
3. 任何Smolforward前审计本机和可访问项目/PR/归档、RTX预留任务；固定排序取首24可验证未暴露任务，与12已暴露发现任务隔离。暂定预留不等于host资格；不够24就明确exposure边界。冻结所有资产/源码/队列/timer/warm/完整顺序，创建结果Draft PR、推送F0并验证远端head后自行继续。
4. 执行12×4×2=96发现请求和固定capture对照。数值失败保留，禁止改候选/模型。有自然分叉且能真实恢复时最多2任务×2重复做完整own-path sham和状态×整路径四格，辅助decode上限64；无触发/不支持恢复也交付，不扩大找例。
5. 确认前刷新cohort预留元数据；新冲突停止fresh-confirmation，不在看到发现输出后换队列。工程/exposure资格通过后执行24×R/N/M/C×4=384正式请求、16新进程会话、16已暴露warmup，按DESIGN固定顺序。方法数值mismatch仍收集冻结负结果矩阵；基础设施资格失败则partial收尾。
6. 正式输出合同为首runtime EOG含或cap128；raw数组/suffix独立核对并全收费。主指标为共同wrapper的host整请求，native whole/generation另审边界。ratio=baseline/C，不合格/缺失cohort qualified speedup=null，不混RTX参考或不同timer/session。
7. 工程256非warm+正式384+warm64=704 started请求、64辅助decode、工程8h/确认8h/总16活动GPU小时、7自然日为硬上限。记录隐式forward，不自动重试、加轮、搜索候选或补旧实验。
8. 独立CPU verifier直接读原payload/KV/float arrays，保留全部负例/缺失及实际CAS恢复、fresh远端readback。完成独立结果Draft PR并回报链接、exacthead、计数与结论；不merge、改稿、发布release或用RTX新结果选择B570方案。

RTX #79是设计背景，#80为在推进的执行，本轮没有其结果依赖。同日独立进程会话不构成跨日期复测。固定路径不迁移，或端点合格而仍慢，均是应保留的完成结果。
