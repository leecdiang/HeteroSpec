# 远程执行 prompt

从本 PR 的实际最新 head 新建独立结果分支，先读本目录 PLAN.md、study.json 及 ../shared/COORDINATION.md、ADAPTER.md；按 models.json 找回历史 Llama8B/1B Q8 精确权重、许可、tokenizer和模板，不用猜测的新GGUF替换。先冻结Qwen/Smol最终规则，再创建独立Linux Llama R，先尝试原规则迁移，使用旧CodeContests反例和有限边界/尾部/终止控制；实际观察graph、norm/RoPE及算术要求。若需通用新规则，保留首次迁移失败、另建扩展版本并回归Qwen/Smol，不把修改后的成功称零修改泛化。保留四个M与两个D4强控制，普通生成胜出不否定家族能力；不引入第四家族、MoE或新draft训练。 自主完成正常构建、ABI、源码和记录适配以及有机制依据的通用修复，保留失败、版本和重新资格，不停在 helper 测试；不得替换 R、按输入特判或删除不利对照。保护正在运行的 PR196 与公司服务，使用已授权 UUID 和协调后的安静计时窗口；交付独立结果 PR，不自动合并、不改论文、不租卡。
