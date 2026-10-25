# 发给 B570 执行端

你在 B570 主机继续 HeteroSpec。请读取当前协调分支的 `docs/research/native_reproduction_20261025/B570_PLAN.md` 和同目录 `EXECUTION_POLICY.md`，以本地实际目录为准，立即完成可行部分，并将结果提交独立分支、创建结果 PR，不合并。

目标是把已通过的 Qwen Q8_0 GQA / AV-preserving Vulkan 路径交付成可干净构建、真实 stage 回放、完整请求核对的原生复现包。恢复 PR131 前置 admission/query_head、PR132 AV patch、request bridge 和 PR134 源码与参考；解决旧 shader 对象目录的隐式构建依赖。先清点与 CPU/只读审计，再构建、提取真实 Q/K/V/mask 和请求 fixture，最后在 B570 做有限 smoke。没有旧归档时区分“新捕获”与“历史复现”，继续其他独立任务。

PR143 已完成 prefill 全面板，未建立达到预设门槛的实际收益，保留 QB/thread8；不要重跑它，也不要写“缺 timing”。B570 默认不复制 RTX resident/fresh 因子实验；只有本机缺有效 fresh-service 对照或出现明确新部署问题，才补最小配对控制。旧 Llama Q6_K 失败与新 Qwen 成功路径分开报告。

请自主调整路径、工具链、构建和采集脚本，保留变更与新 runtime 身份；不要因旧 CPU8 gate 或历史 wrapper 停掉所有工作。参考、输入、算法和计时边界不能悄悄改变。数值失败就停止该候选的性能解释，保存证据并继续其他交付项。设置合理资源预算，保存 checkpoint、失败槽位和重试记录。结果 PR 给出源码/依赖/hash、复现命令、可访问 fixture、实测 receipts 和具体未完成项；单次 smoke 不报 speedup。
