# B570 本轮执行边界

本研究为 PR #63 prompt v1 的新执行批次。prompt 原文保持不变；本目录记录新代码、预算冻结、失败与派生结果。历史研究和正在整合的论文不作为写入目标。

两个新队列分别报告：24 个 RTX/B570 共享 MBPP 输入是项目已暴露输入；项目未执行队列按可访问历史与固定 RTX 审计收据排除后排序。后者不涉及训练数据，且不声称独立扫描了 RTX 机器上不可访问的 bulk raw。

普通 B570 参考保留原 common caller grouping 和 UB128 的普通目标路径；matched target 使用 native 的 prompt[:-1] 与最后一 token 分组、源 logits 首样本、post-sample sampler clone、真实状态载入到 continuation 上下文。native 的原 rollback、draft proposal 和 cap overshoot 循环保留。目标 prefill 与 continuation 以及 draft 阶段参数分别记录。

新驻留前端每请求清空目标及草稿 KV，重置 sampler、pending、history 和所有 native 循环局部状态。模型只在会话启动时加载。正式 generation 时间包含首样本、在线状态传移、草稿、验证、rollback 及终端设备同步；whole 时间从请求解析和重置到 generation 与 cleanup。资格 observer 的强同步、state dump 及文件归档成本独立记录，不从有 observer 的耗时中扣除。端到端本机记录延迟另存，不能与模型加载费用混同。

数值失败的完整有效输出不自动重试。编译、CLI 和观测器工程修订均发生于新任务前；其完整和中断记录均保留，不进入正式速度样本。采样、模型精度、Vulkan shader 算术和 reference 不随输出变化。

driver 版本作为真实环境字段保留。用户在 2026-10-06 明确指示继续执行并不以该稳定性更新作为阻断；本研究仍按实测输出检查旧参考资格。

本轮 closure 只覆盖冻结配置、真实长度、单序列和这些任务。失败的路径只有诊断费用。没有可靠 B570 板卡能耗域，因此不产生能耗改进结论。没有 opaque sampler 字节认证或唯一 Vulkan kernel 因果结论。
