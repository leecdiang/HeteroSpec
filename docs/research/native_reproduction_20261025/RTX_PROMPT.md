在这台 RTX 主机继续 HeteroSpec。先读取本 PR 的 `docs/research/native_reproduction_20261025/RTX_PLAN.md`、同目录 `EXECUTION_POLICY.md` 和现有交接/运行时索引，记录当前提交；创建独立 RTX 工作分支，保留已有结果。现在授权你恢复材料、修复必要工程问题、构建并运行原生复现及其后的受控实验。PR140/142 的长自然输入计划仍保留原阻塞状态；本次是既有12输入的新桥接 campaign，不继承其长输入分层门槛，也不声称已解决未见输入验证。

先恢复 E2 原始源码/二进制和 metadata4 路由、数值 DLL 与模型身份，交付一个真实多查询 stage replay fixture 和一个完整 R/PQ/QB 请求 fixture，从新目录验证能运行。已有 archive 优先使用；顺手能从源码确认历史 M3/C3 身份就补证据，确认不了不要猜，也别阻塞其他工作。

桥接自身资格通过后，按同一 stack/reference/既有12个 Qwen3输入，做 k=1/3 × resident/fresh 的 PQ_A/PQ_B/QB 桥接，计完整服务时间并记录 A/A。先做小型可行性和观察开销检查，依据本机资源确定有限正式预算、warmup和排序，再提交冻结配置；不要机械照搬8会话或逐请求warmup。正式结果不因显著性追加。Graph 计数能可靠记录就记录；缺少可选工具时继续 clean timing，单列未观测机制。

路径、依赖、构建和 adapter 小问题自行修复并记 amendment，不要频繁停下来询问。维护原子 checkpoint 和唯一 slot/attempt ID，恢复时核对已完成项，再继续 pending；中断配对块按冻结的技术重试规则用新 attempt 重跑，原记录保留，不能覆盖或当成功。数值失败停止对应单元的 qualified timing，继续其他独立任务；只清理自己启动的进程。源码/reference/timer 等科学合同改变时另开 cohort，不混合旧结果。

最终给出可复现材料、完整结果/失败表、分析脚本、结论和仍缺的证据，并创建 RTX 结果 PR。不要直接合并、投稿或覆盖论文数据。
