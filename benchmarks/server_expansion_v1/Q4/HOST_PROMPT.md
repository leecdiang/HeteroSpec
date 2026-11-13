# 远程执行 prompt

从本 PR 的实际最新 head 新建独立结果分支，先读本目录 PLAN.md、study.json 及 ../shared/COORDINATION.md、ADAPTER.md；使用 models.json 固定的官方 Qwen3-8B-Q4_K_M，draft仍为原0.6B Q8。先运行只读GGUF类型清点，查真实混合tensor类型、量化和dispatch，不依据文件名推断全部Q4，也不放开Q8保护当作支持。固定独立Q4 R，做真实操作数重放和通用typed recipe后接入最终阶段计划；先保留四种合法target-only组合，推测路径具备资格与新问题时才用六臂替代目标端面板。遇到未支持类型应做有依据的实现或明确支持边界，不冒充原Q8部署。 自主完成正常构建、ABI、源码和记录适配以及有机制依据的通用修复，保留失败、版本和重新资格，不停在 helper 测试；不得替换 R、按输入特判或删除不利对照。保护正在运行的 PR196 与公司服务，使用已授权 UUID 和协调后的安静计时窗口；交付独立结果 PR，不自动合并、不改论文、不租卡。
